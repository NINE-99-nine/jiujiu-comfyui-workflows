# -*- coding: utf-8 -*-
# ============ minimax_h3_image_edit_api.py · MiniMax H3 Image 图像编辑引子 v1.0 ============
# 与 minimax_h3_image_edit_api.json 同 basename → 自动配对。
#
# 链路：
#   90 底图 → 91 缩到 12MP(area) → 92 对齐32 →┬→ 164 取尺寸 → 32.width/height
#                                              └→ 171 输入前缩放 1.2MP → 32.images.image_0
#   图2..图11（93/96/99/139/149/145/146/147/148/150）→ 172..181 输入前缩放 1.5MP → 32.images.image_N
#   43 提示词 → 32；32 → CONDITIONING(38.positive) / LATENT(mode=base 时的画布)
#   162 数字 → 165 比例选择器 → 168 空Latent ─┐
#   169 开关（base=底图 / custom=自定义）────┴→ 38.latent_image
#   38 KSampler(6步/cfg1/lcm) → 42 解码 → 63 缩到 --out-mp → 9 存图
#
# 用法：
#   python minimax_h3_image_edit_api.py --img1 底图.png --prompt-file 词.txt
#   python minimax_h3_image_edit_api.py --img1 底图.png --ref 图2.png --ref 图3.png --prompt "…"
#   python minimax_h3_image_edit_api.py --img1 底图.png --prompt "…" --ratio 3:4 --mp 8   # 自定义分辨率
#   python minimax_h3_image_edit_api.py --img1 底图.png --prompt "…" --dry-run
# 只输出一行 JSON：{"kind":"image","prompt_id":…,"file":…,"size":…}
#
# ⚠️ 关键事实（2026-11-17 实测）：
#   1) 提示词写 43.value。
#   2) 两种分辨率模式就是 169 开关：base=用 32 吐出的底图 latent（12MP、32 对齐）；
#      custom=用 165+168。custom 时本引子会把 32.width/height 也从 164 切到 165，
#      保证「条件说的尺寸」与「画布尺寸」永远一致（作者 2026-11-17 拍板）。
#   3) custom 的像素数写 162.value（PrimitiveFloat），不是 165.megapixels——后者已被 [162,0] 占线。
#   4) 多图一律挂「输入前缩放」节点（171..181），绝不直接连 LoadImage（原图太大爆显存）。
#      `32.images` 是 AUTOGROW 输入，键名 images.image_0…；**image_0 = 提示词里的「图1」= 底图**（0 基键名）。
#   5) 模型天然支持最多 16 张输入；本模板只有 11 个槽位（1 底图 + 10 参考），A770 实际 2 张就很吃力。
#   6) 61 "Enable PE?" 悬空残留，引子不碰；LoRA 尘星 0.8 固定不暴露。

import argparse, datetime, json, math, os, random, re, sys, urllib.request
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit
from execution import env

TEMPLATE = _here.with_suffix(".json")
COMFY = env.COMFY_URL

# ---- 节点号（v1 模板，36 节点）----
P_PROMPT   = "43"    # PrimitiveStringMultiline.value：提示词入口
P_COND     = "32"    # MiniMaxH3ImageConditioning：prompt / width / height / images.image_N
P_KS       = "38"    # KSampler：seed
P_OUTSCALE = "63"    # ImageScaleToTotalPixels：出图总像素
P_SAVE     = "9"     # SaveImage：filename_prefix
P_SIZE     = "164"   # GetImageSize(92)：底图实际宽高
P_MPF      = "162"   # PrimitiveFloat：custom 模式的像素数
P_RATIO    = "165"   # ResolutionSelector：custom 模式的比例
P_EMPTY    = "168"   # EmptyLatentImage：custom 模式的画布
P_SWITCH   = "169"   # ComfySwitchNode：false=底图 / true=自定义

# 槽位：(提示词里的图号, LoadImage 节点, 输入前缩放节点, 预缩放 MP)
SLOTS = [
    (1,  "90",  "171", 1.2),   # 底图（必传）
    (2,  "93",  "172", 1.5),
    (3,  "96",  "173", 1.5),
    (4,  "99",  "174", 1.5),
    (5,  "139", "175", 1.5),
    (6,  "149", "176", 1.5),
    (7,  "145", "177", 1.5),
    (8,  "146", "178", 1.5),
    (9,  "147", "179", 1.5),
    (10, "148", "180", 1.5),
    (11, "150", "181", 1.5),
]
MAX_REF = len(SLOTS) - 1          # 本模板最多 10 张参考
MODEL_MAX_IMG = 16                # 模型本身支持的上限（作者 2026-11-17）

MULTIPLE = 32
MP_MIN, MP_MAX = 0.1, 16.0
OUT_MP_MIN, OUT_MP_MAX = 0.01, 16.0

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
    key = (ratio or "").split("(")[0].strip()
    if key not in RATIOS:
        raise SystemExit(f"[minimax-h3-edit] --ratio 不认识：{ratio}\n合法值：{' / '.join(RATIOS)}（或全名）")
    return key


def _snap(v):
    return max(MULTIPLE, int(math.floor(v / MULTIPLE + 0.5)) * MULTIPLE)


def calc_size(ratio_key, megapixels):
    rw, rh = (int(x) for x in ratio_key.split(":"))
    px = float(megapixels) * 1_000_000
    w = math.sqrt(px * rw / rh)
    return _snap(w), _snap(px / w)


def calc_out_size(w, h, out_mp):
    scale = math.sqrt((float(out_mp) * 1_000_000) / (w * h))
    return _snap(w * scale), _snap(h * scale)


def _upload_image(path):
    """把本地图上传到 ComfyUI 的 input 目录，返回可喂给 LoadImage 的名字。"""
    path = str(path)
    if not os.path.isfile(path):
        raise SystemExit("[minimax-h3-edit] 图片不存在：%s" % path)
    fname = os.path.basename(path)
    ext = os.path.splitext(fname)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        raise SystemExit("[minimax-h3-edit] 不支持的图片格式: %s" % ext)
    with open(path, "rb") as f:
        data = f.read()
    boundary = "----hermesmmh3" + str(os.getpid())
    parts = [
        ('--%s\r\nContent-Disposition: form-data; name="image"; filename="%s"\r\n'
         'Content-Type: application/octet-stream\r\n\r\n' % (boundary, fname)).encode(),
        data + b"\r\n",
        ('--%s\r\nContent-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n' % boundary).encode(),
        ("--%s--\r\n" % boundary).encode(),
    ]
    req = urllib.request.Request(COMFY + "/upload/image", data=b"".join(parts),
                                 headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary},
                                 method="POST")
    r = json.loads(urllib.request.urlopen(req, timeout=120).read().decode("utf-8"))
    name = r.get("name")
    sub = r.get("subfolder", "")
    return name if not sub else "%s/%s" % (sub, name)


def build(prompt, base_name, ref_names, mode, ratio, mp, out_mp, name="output", seed=-1, dry=False):
    """base_name = 已可喂 LoadImage 的底图名；ref_names = 图2、图3… 依次。"""
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    ref_names = list(ref_names or [])
    if len(ref_names) > MAX_REF:
        raise SystemExit(f"[minimax-h3-edit] 参考图太多：{len(ref_names)} 张（本模板最多 {MAX_REF} 张；"
                         f"模型本身支持 {MODEL_MAX_IMG} 张，但模板只有 {len(SLOTS)} 个槽位）")

    # ① 提示词 → 43.value
    wf[P_PROMPT]["inputs"]["value"] = prompt

    # ② 图片：底图 → 90（其缩放 171 已在模板里接到 images.image_0）
    wf[SLOTS[0][1]]["inputs"]["image"] = base_name
    wf[P_COND]["inputs"]["images.image_0"] = [SLOTS[0][2], 0]
    #    参考图 i-1 → LoadImage 槽位 + 挂到 images.image_{i-1}（指向输入前缩放，不是 LoadImage）
    for idx, fname in enumerate(ref_names):
        num, load_id, resize_id, _mp = SLOTS[idx + 1]
        wf[load_id]["inputs"]["image"] = fname
        wf[P_COND]["inputs"]["images.image_%d" % (num - 1)] = [resize_id, 0]

    # ③ 分辨率模式 → 169 开关 + 32 的宽高来源
    cond = wf[P_COND]["inputs"]
    if mode == "custom":
        rk = _ratio_key(ratio or wf[P_RATIO]["inputs"]["aspect_ratio"])
        wf[P_RATIO]["inputs"]["aspect_ratio"] = RATIOS[rk]
        if mp is not None:
            if not (MP_MIN <= float(mp) <= MP_MAX):
                raise SystemExit(f"[minimax-h3-edit] --mp 超出范围：{mp}（合法 {MP_MIN}~{MP_MAX} MP）")
            wf[P_MPF]["inputs"]["value"] = float(mp)
        else:
            mp = wf[P_MPF]["inputs"]["value"]
        wf[P_SWITCH]["inputs"]["switch"] = True
        cond["width"] = [P_RATIO, 0]      # 条件与画布保持同一尺寸（作者 2026-11-17 拍板）
        cond["height"] = [P_RATIO, 1]
        gw, gh = calc_size(rk, mp)
        gen_desc = f"{gw}x{gh}（自定义 {RATIOS[rk]} / {float(mp):g}MP）"
    else:
        if ratio or mp is not None:
            raise SystemExit("[minimax-h3-edit] base 模式不接受 --ratio/--mp（要自定义就加 --mode custom）")
        wf[P_SWITCH]["inputs"]["switch"] = False
        cond["width"] = [P_SIZE, 0]       # 底图尺寸（模板原样）
        cond["height"] = [P_SIZE, 1]
        gw = gh = None
        gen_desc = "底图尺寸（12MP 预缩放 + 32 对齐，由 91/92/164 决定）"

    # ④ 出图缩放 → 63
    if out_mp is not None:
        if not (OUT_MP_MIN <= float(out_mp) <= OUT_MP_MAX):
            raise SystemExit(f"[minimax-h3-edit] --out-mp 超出范围：{out_mp}（合法 {OUT_MP_MIN}~{OUT_MP_MAX} MP）")
        wf[P_OUTSCALE]["inputs"]["megapixels"] = float(out_mp)

    # ⑤ seed → 38
    seed_val = random.randint(1, 10 ** 15) if seed == -1 else int(seed)
    wf[P_KS]["inputs"]["seed"] = seed_val

    # ⑥ 输出前缀
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[P_SAVE]["inputs"]["filename_prefix"] = f"{today}/{safe}"

    # ⑦ dry-run 信息
    info = {
        "mode": mode,
        "gen_size": gen_desc,
        "images": {"图1(底图)": base_name,
                   **{f"图{num}": fname for (num, _l, _r, _m), fname in
                      zip(SLOTS[1:1 + len(ref_names)], ref_names)}},
        "out_mp": wf[P_OUTSCALE]["inputs"]["megapixels"],
        "out_size~": (f"{calc_out_size(gw, gh, wf[P_OUTSCALE]['inputs']['megapixels'])[0]}x"
                      f"{calc_out_size(gw, gh, wf[P_OUTSCALE]['inputs']['megapixels'])[1]}") if gw else "由底图决定",
        "seed": seed_val,
        "prefix": wf[P_SAVE]["inputs"]["filename_prefix"],
        "lora": f"{wf['142']['inputs']['lora_name']} @ {wf['142']['inputs']['strength_model']}",
    }
    if dry:
        info["nodes_touched"] = [P_PROMPT, SLOTS[0][1], P_COND, P_RATIO, P_MPF, P_SWITCH, P_OUTSCALE, P_KS, P_SAVE]
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print("[minimax-h3-edit] " + json.dumps(info, ensure_ascii=False), file=sys.stderr)
    return wf


def load_prompt(args):
    if args.prompt_file:
        path = Path(args.prompt_file).expanduser()
        if not path.is_file():
            print(f"[minimax-h3-edit] 提示词文件不存在或不是文件：{path}", file=sys.stderr)
            sys.exit(2)
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            print(f"[minimax-h3-edit] 提示词文件为空：{path}", file=sys.stderr)
            sys.exit(2)
        return text
    text = (args.prompt or "").strip()
    if not text:
        print("[minimax-h3-edit] --prompt 内容为空", file=sys.stderr)
        sys.exit(2)
    return text


def main():
    p = argparse.ArgumentParser(
        description="MiniMax H3 Image 图像编辑（图1=底图；--ref 依次为图2…图11；两种分辨率模式）")
    p.add_argument("--img1", required=True, help="底图（本地路径，必传）= 提示词里的「图1」")
    p.add_argument("--ref", action="append", default=[], metavar="图片",
                   help=f"参考图（可重复，最多 {MAX_REF} 张）：第 1 个=图2，第 2 个=图3 … 第 10 个=图11")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt", help="编辑指令（短稿直传；长文/多段/含引号用 --prompt-file）")
    src.add_argument("--prompt-file", dest="prompt_file", help="提示词文件路径（UTF-8）")
    p.add_argument("--mode", choices=["base", "custom"], default=None,
                   help="分辨率模式：base=采用底图的比例/尺寸（默认）；custom=自定义 --ratio/--mp。"
                        "不传时：给了 --ratio 或 --mp 就自动 custom，否则 base")
    p.add_argument("--ratio", "-r", default=None,
                   help="custom 模式的比例：1:1 / 2:3 / 3:2 / 3:4 / 4:3 / 9:16 / 16:9 / 21:9（短名或全名）")
    p.add_argument("--mp", type=float, default=None,
                   help="custom 模式的生成总像素（MP，写 162）：不传＝模板 8；合法 0.1~16")
    p.add_argument("--out-mp", dest="out_mp", type=float, default=None,
                   help="出图缩放后的总像素：不传＝模板 2.5（降采样）；要原生清晰给 8 或更高（上限 16）")
    p.add_argument("--name", default="output", help="成品名（自动加 日期/ 目录）")
    p.add_argument("--seed", type=int, default=-1, help="-1 随机 / 具体值固定（写入 38 KSampler）")
    p.add_argument("--dry-run", dest="dry_run", action="store_true",
                   help="只看将要改的节点与图号映射，不上传图片、不提交")
    args = p.parse_args()

    mode = args.mode or ("custom" if (args.ratio or args.mp is not None) else "base")
    prompt = load_prompt(args)

    if args.dry_run:
        base_name = os.path.basename(args.img1)
        ref_names = [os.path.basename(x) for x in args.ref]
        for path in [args.img1] + args.ref:
            if not os.path.isfile(path):
                raise SystemExit("[minimax-h3-edit] 图片不存在：%s" % path)
    else:
        base_name = _upload_image(args.img1)
        ref_names = [_upload_image(x) for x in args.ref]

    wf = build(prompt, base_name, ref_names, mode, args.ratio, args.mp,
               args.out_mp, args.name, args.seed, dry=args.dry_run)
    if args.dry_run:
        return
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
