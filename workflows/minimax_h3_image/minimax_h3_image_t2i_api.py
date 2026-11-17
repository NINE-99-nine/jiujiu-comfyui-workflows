# -*- coding: utf-8 -*-
# ============ minimax_h3_image_t2i_api.py · MiniMax H3 Image 文生图引子 v1.0 ============
# 与 minimax_h3_image_t2i_api.json 同 basename → 自动配对。
# 链路：102 UNet → 170 LoRA(尘星 0.8，固定不暴露) → 120 KSampler(6 步 / cfg 1 / lcm / sgm_uniform)
#       ← 108 MiniMaxH3ImageConditioning(105 提示词 + 138 分辨率)
#       → 123 VAEDecode → 124 ImageScaleToTotalPixels(出图缩放) → 127 SaveImage
#
# 用法：
#   python minimax_h3_image_t2i_api.py --prompt "…" [--ratio 21:9 --mp 8 --out-mp 2.5 --name 名字 --seed -1]
#   python minimax_h3_image_t2i_api.py --prompt-file 词.txt [同上]
#   python minimax_h3_image_t2i_api.py --prompt-file 词.txt --dry-run     # 只打印将要改的节点与预计尺寸
# 只输出一行 JSON：{"kind":"image","prompt_id":…,"file":…,"size":…}
#
# ⚠️ 关键事实（2026-11-17 实测）：
#   1) 提示词写 105.value。108.prompt 已被 105 连线占用，写它无效。
#   2) 尺寸只走 138 ResolutionSelector（108 的 width/height 被 138[0]/[1] 占线，直接写无效）。
#      138.multiple 模板=32 → 宽高自动对齐 32 倍数；模型要求 32 倍数（节点 width/height step=32）。
#   3) 出图缩放是 124 ImageScaleToTotalPixels：按总像素缩放、保持长宽比；模板 2.5 < 生成 8，
#      即成品是**降采样**。要更清晰就把 --out-mp 提到 ≥8（上限 16）。
#   4) 122 "Enable PE?" 在本模板里没有任何节点引用（悬空残留），引子不碰。
#   5) 170 LoRA 固定尘星 0.8，按作者要求不暴露成参数。

import argparse, datetime, json, math, random, re, sys
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_suffix(".json")

# ---- 节点号（v1 模板，14 节点）----
P_PROMPT  = "105"   # PrimitiveStringMultiline.value：提示词（唯一入口）
P_COND    = "108"   # MiniMaxH3ImageConditioning：width/height 由 138 供线，不直接写
P_RES     = "138"   # ResolutionSelector：aspect_ratio / megapixels / multiple
P_SAMPLER = "120"   # KSampler：seed（steps/cfg/sampler 固定不暴露）
P_SCALE   = "124"   # ImageScaleToTotalPixels：megapixels = 出图总像素
P_SAVE    = "127"   # SaveImage：filename_prefix

MULTIPLE = 32                       # 模型硬要求：宽高必须是 32 的倍数
MP_MIN, MP_MAX = 0.1, 16.0          # 138.megapixels 的合法区间（节点定义）
OUT_MP_MIN, OUT_MP_MAX = 0.01, 16.0 # 124.megapixels 的合法区间（节点定义）

# 比例枚举（与本机 ResolutionSelector 的 aspect_ratio 下拉完全一致；短名/全名都收）
RATIOS = {
    "1:1":  "1:1 (Square)",
    "2:3":  "2:3 (Portrait Photo)",
    "3:2":  "3:2 (Photo)",
    "3:4":  "3:4 (Portrait Standard)",
    "4:3":  "4:3 (Standard)",
    "9:16": "9:16 (Portrait Widescreen)",
    "16:9": "16:9 (Widescreen)",
    "21:9": "21:9 (Ultrawide)",
}


def _ratio_key(ratio):
    """'21:9' / '21:9 (Ultrawide)' → '21:9'；不认识就报错并列出合法值。"""
    key = (ratio or "").split("(")[0].strip()
    if key not in RATIOS:
        raise SystemExit(f"[minimax-h3-t2i] --ratio 不认识：{ratio}\n合法值：{' / '.join(RATIOS)}（或全名）")
    return key


def _snap(v):
    """对齐到最接近的 32 倍数（与 138.multiple=32 同规则），用来预估实际出图宽高。"""
    return max(MULTIPLE, int(math.floor(v / MULTIPLE + 0.5)) * MULTIPLE)


def calc_size(ratio_key, megapixels):
    """按比例 + 像素预算预估生成宽高（对齐 32）。真正生效的是 138 节点，这里只用于打印与自检。"""
    rw, rh = (int(x) for x in ratio_key.split(":"))
    px = float(megapixels) * 1_000_000
    w = math.sqrt(px * rw / rh)
    h = px / w
    return _snap(w), _snap(h)


def calc_out_size(w, h, out_mp):
    """出图缩放后的宽高预估：按总像素等比缩放，并对齐 32（保持长宽比）。"""
    scale = math.sqrt((float(out_mp) * 1_000_000) / (w * h))
    return _snap(w * scale), _snap(h * scale)


def build(prompt, ratio=None, mp=None, out_mp=None, name="output", seed=-1, dry=False):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    # ① 提示词 → 105.value
    wf[P_PROMPT]["inputs"]["value"] = prompt

    # ② 尺寸 → 138 ResolutionSelector（不传＝沿用模板 21:9 / 8MP / multiple 32）
    res = wf[P_RES]["inputs"]
    if ratio:
        res["aspect_ratio"] = RATIOS[_ratio_key(ratio)]
    if mp is not None:
        if not (MP_MIN <= float(mp) <= MP_MAX):
            raise SystemExit(f"[minimax-h3-t2i] --mp 超出范围：{mp}（合法 {MP_MIN}~{MP_MAX} MP）")
        res["megapixels"] = float(mp)

    # ③ 出图缩放 → 124 ImageScaleToTotalPixels.megapixels
    if out_mp is not None:
        if not (OUT_MP_MIN <= float(out_mp) <= OUT_MP_MAX):
            raise SystemExit(f"[minimax-h3-t2i] --out-mp 超出范围：{out_mp}（合法 {OUT_MP_MIN}~{OUT_MP_MAX} MP）")
        wf[P_SCALE]["inputs"]["megapixels"] = float(out_mp)

    # ④ seed → 120 KSampler（comfy_submit 只处理 class_type 以 Seed 开头的节点，这里必须自己写）
    seed_val = random.randint(1, 10 ** 15) if seed == -1 else int(seed)
    wf[P_SAMPLER]["inputs"]["seed"] = seed_val

    # ⑤ 输出前缀：日期/成品名
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[P_SAVE]["inputs"]["filename_prefix"] = f"{today}/{safe}"

    # ⑥ 自检：生成宽高必须是 32 的倍数（预估与节点同规则）
    ratio_key = _ratio_key(res["aspect_ratio"])
    gw, gh = calc_size(ratio_key, res["megapixels"])
    ow, oh = calc_out_size(gw, gh, wf[P_SCALE]["inputs"]["megapixels"])
    info = {
        "ratio": res["aspect_ratio"],
        "gen_mp": res["megapixels"],
        "gen_size~": f"{gw}x{gh}",
        "out_mp": wf[P_SCALE]["inputs"]["megapixels"],
        "out_size~": f"{ow}x{oh}",
        "seed": seed_val,
        "prefix": wf[P_SAVE]["inputs"]["filename_prefix"],
        "lora": f"{wf['170']['inputs']['lora_name']} @ {wf['170']['inputs']['strength_model']}",
        "steps": wf[P_SAMPLER]["inputs"]["steps"],
        "cfg": wf[P_SAMPLER]["inputs"]["cfg"],
    }
    if dry:
        info["nodes_touched"] = [P_PROMPT, P_RES, P_SCALE, P_SAMPLER, P_SAVE]
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print("[minimax-h3-t2i] " + json.dumps(info, ensure_ascii=False), file=sys.stderr)
    return wf


def load_prompt(args):
    """提示词来源：--prompt 直传（短）或 --prompt-file 读文件（长/多段/含引号），二者互斥。"""
    if args.prompt_file:
        path = Path(args.prompt_file).expanduser()
        if not path.is_file():
            print(f"[minimax-h3-t2i] 提示词文件不存在或不是文件：{path}", file=sys.stderr)
            sys.exit(2)
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            print(f"[minimax-h3-t2i] 提示词文件为空：{path}", file=sys.stderr)
            sys.exit(2)
        return text
    text = (args.prompt or "").strip()
    if not text:
        print("[minimax-h3-t2i] --prompt 内容为空", file=sys.stderr)
        sys.exit(2)
    return text


def main():
    p = argparse.ArgumentParser(
        description="MiniMax H3 Image 文生图（6 步 / cfg 1 / lcm · 8MP 起 · 32 倍数自动对齐）")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt", help="提示词（短稿直传；长文/多段/含引号一律用 --prompt-file）")
    src.add_argument("--prompt-file", dest="prompt_file",
                     help="提示词文件路径（UTF-8；长文/含引号一律用这个，避免 shell 截断）")
    p.add_argument("--ratio", "-r", default=None,
                   help="画面比例：不传＝沿用模板 21:9。合法值 "
                        "1:1 / 2:3 / 3:2 / 3:4 / 4:3 / 9:16 / 16:9 / 21:9（短名或全名都行）")
    p.add_argument("--mp", type=float, default=None,
                   help="生成总像素（MP）：不传＝沿用模板 8。合法 0.1~16。"
                        "⚠️ 这模型吃大尺寸：低于 8MP 容易糊，2~4MP 会明显低质；最大 16")
    p.add_argument("--out-mp", dest="out_mp", type=float, default=None,
                   help="出图缩放后的总像素（MP）：不传＝沿用模板 2.5（=从 8MP 降采样）"
                        "；要原尺寸清晰成品就给 8 或更高（上限 16）")
    p.add_argument("--name", default="output", help="成品名（自动加 日期/ 目录）")
    p.add_argument("--seed", type=int, default=-1, help="-1 随机 / 具体值固定（写入 120 KSampler）")
    p.add_argument("--dry-run", dest="dry_run", action="store_true",
                   help="只打印将要改的节点与预计生成/出图尺寸，不提交")
    args = p.parse_args()

    wf = build(load_prompt(args), args.ratio, args.mp, args.out_mp, args.name,
               args.seed, dry=args.dry_run)
    if args.dry_run:
        return
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
