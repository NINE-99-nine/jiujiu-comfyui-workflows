# -*- coding: utf-8 -*-
# ============ moss_api.py · MOSS-Image 引子 v2（黑盒，agent 只传参数） ============
# 与 moss_api.json 同 basename → 自动配对。模板 = 作者 2026-10-20 版（21 节点，含 LoRA 堆 + SeedVR2 放大）。
#
# 链路：13 UNet → 61 dmd 蒸馏 LoRA → 93 LoraManager(6 条) → 19 KSampler(8步 er_sde cfg1)
#       → 22 VAEDecode → 103 AnySwitch → 85 SeedVR2(1440) → 97 AnySwitch → 81 SaveImageAdvanced
# 提示词：99 String → 101 JoinStringMulti(串1=93 的触发词) → 4 正向 CLIPTextEncode
#
# 用法：
#   python moss_api.py --prompt "…" [--ratio "9:16 (Portrait Widescreen)" --megapixels 1.5 --name 名字 --seed -1]
#   python moss_api.py --prompt-file 词.txt [同上]
#   python moss_api.py --list-loras                                # 只列可选 LoRA（选择题用），不出图
#   python moss_api.py --prompt-file 词.txt --loras "wlop12:0.8:on" --loras "Nyalia_moss_v1_lokr:0.6:on"
#   python moss_api.py --prompt-file 词.txt --no-default-lora      # 关掉默认那条 0.60
#   python moss_api.py --prompt-file 词.txt --seedvr2-res 1080     # 降放大分辨率
#   python moss_api.py --prompt-file 词.txt --no-upscale           # 只要原图，不走 SeedVR2
#
# 只输出一行 JSON：{"kind":"image","prompt_id":…,"file":…,"size":…}

import argparse, datetime, json, random, re, sys
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_suffix(".json")

# ---- 节点号（v2 模板）----
P_PROMPT   = "99"    # String：提示词入口
P_RES      = "8"     # ResolutionSelector：尺寸
P_SAMPLER  = "19"    # KSampler：步数 / cfg / seed
P_LORA     = "93"    # Lora Loader (LoraManager)：LoRA 堆
P_UPSCALER = "85"    # SeedVR2VideoUpscaler：放大
P_PREFIX   = "81"    # SaveImageAdvanced
P_SW_HI    = "97"    # AnySwitch：优先=放大后[85] / 备用=原图[22]
P_SW_LO    = "103"   # AnySwitch：喂给放大器的输入

DEFAULT_LORA = "moss_context_detaile_tweaker_20261018_rank2"
SEED_MAX = 4294967295   # seedvr2 节点的 seed 上限 2^32-1

# MOSS-Image 要求宽高是 16 的倍数（模板 ResolutionSelector 写的是 8）
MULTIPLE = 16


def _loras(wf):
    return wf[P_LORA]["inputs"]["loras"]["__value__"]


def _sync_lora_text(wf):
    """把 active 的 LoRA 回写成 text widget，保持 UI 显示与数组一致。"""
    act = " ".join(f"<lora:{e['name']}:{float(e['strength']):.2f}>"
                   for e in _loras(wf) if e.get("active"))
    wf[P_LORA]["inputs"]["text"] = act


def apply_loras(wf, specs, no_default):
    """specs: ["名:强度:on|off", ...] —— 只动点名条目，其余保持模板原样。

    🔴 P0：不传 specs 且不关默认那条时，除默认那条以外全部强制关闭。
    「默认只有一条 LoRA」由程序钉住，不靠自觉（作者 2026-10-20 明确要求）。
    """
    arr = _loras(wf)
    if not specs and not no_default:
        for e in arr:
            e["active"] = (e["name"] == DEFAULT_LORA)
    if no_default:
        for e in arr:
            if e["name"] == DEFAULT_LORA:
                e["active"] = False
    for spec in specs or []:
        parts = spec.split(":")
        name = parts[0].strip()
        strength = None
        state = None
        for p in parts[1:]:
            p = p.strip()
            if p.lower() in ("on", "off"):
                state = (p.lower() == "on")
            else:
                try:
                    strength = float(p)
                except ValueError:
                    pass
        hit = [e for e in arr if e["name"] == name]
        if not hit:   # 允许唯一子串匹配（防长名手打错），命中多条则拒绝
            cand = [e for e in arr if name.lower() in e["name"].lower()]
            if len(cand) == 1:
                hit = cand
            elif len(cand) > 1:
                print(f"WARN: lora 名字不唯一，跳过: {name} → {[c['name'] for c in cand]}", file=sys.stderr)
                continue
        if not hit:
            print(f"WARN: lora 不存在(忽略,不新增): {name}", file=sys.stderr)
            continue
        for e in hit:
            if state is not None:
                e["active"] = state
            if strength is not None:
                e["strength"] = f"{strength:.2f}"
    _sync_lora_text(wf)
    return wf


def build(prompt, ratio, megapixels, name, steps=None, cfg=None,
          loras=None, no_default_lora=False, seedvr2_res=None,
          no_upscale=False, seed=-1):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    # ① 提示词 → 99 String（101 会把 93 的触发词自动接在前面）
    wf[P_PROMPT]["inputs"]["String"] = prompt

    # ② 尺寸 → 8 ResolutionSelector
    res = wf[P_RES]["inputs"]
    res["aspect_ratio"] = ratio
    res["megapixels"] = megapixels
    res["multiple"] = MULTIPLE

    # ③ 采样器
    if steps:
        wf[P_SAMPLER]["inputs"]["steps"] = steps
    if cfg is not None:
        wf[P_SAMPLER]["inputs"]["cfg"] = cfg
    seed_val = random.randint(1, 10 ** 15) if seed == -1 else seed
    wf[P_SAMPLER]["inputs"]["seed"] = seed_val

    # ④ LoRA → 93 LoraManager
    apply_loras(wf, loras, no_default_lora)

    # ⑤ 放大 → 85 SeedVR2
    if seedvr2_res:
        wf[P_UPSCALER]["inputs"]["resolution"] = int(seedvr2_res)
    if no_upscale:
        # 97 的「优先输入」改成与「备用输入」同源（22 原图）→ 85 不再被引用，放大链不执行
        wf[P_SW_HI]["inputs"]["优先输入"] = list(wf[P_SW_HI]["inputs"]["备用输入"])
    elif "seed" in wf[P_UPSCALER]["inputs"]:
        wf[P_UPSCALER]["inputs"]["seed"] = seed_val % (SEED_MAX + 1)

    # ⑥ 兜底：AnySwitch 若缺 switch 键，按「用优先输入」补 True，避免 node_errors
    for nid in (P_SW_HI, P_SW_LO):
        ins = wf.get(nid, {}).get("inputs", {})
        if ins and "switch" not in ins:
            ins["switch"] = True

    # ⑦ 输出前缀
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[P_PREFIX]["inputs"]["filename_prefix"] = f"{today}/{safe}"
    return wf


def load_prompt(args):
    if args.prompt_file:
        path = Path(args.prompt_file).expanduser()
        if not path.is_file():
            print(f"[moss引子] 提示词文件不存在或不是文件：{path}", file=sys.stderr)
            sys.exit(2)
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            print(f"[moss引子] 提示词文件为空：{path}", file=sys.stderr)
            sys.exit(2)
        return text
    text = (args.prompt or "").strip()
    if not text:
        print("[moss引子] --prompt 内容为空", file=sys.stderr)
        sys.exit(2)
    return text


def print_loras():
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    arr = _loras(wf)
    print(f"可选 LoRA（{len(arr)} 条，★ = 模板默认开启，不点名就一直是它）：")
    for i, e in enumerate(arr, 1):
        star = "★" if e.get("active") else " "
        tag = "  ← 默认，除作者点名不许关" if e["name"] == DEFAULT_LORA else ""
        print(f"  {i:>2}. {star} {e['name']}  (strength {e['strength']}){tag}")
    print('\n用法：--loras "<名字>:<强度>:on|off"，可重复传；--no-default-lora 关掉默认那条。')


def main():
    p = argparse.ArgumentParser(description="MOSS-Image 引子 v2（8 步 dmd · LoRA 堆 · SeedVR2 放大）")
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument("--prompt", help="正向提示词（caption 自然语言段）")
    src.add_argument("--prompt-file", dest="prompt_file",
                     help="提示词文件路径（UTF-8；长文/含引号/多段换行一律用这个）")
    p.add_argument("--ratio", default="9:16 (Portrait Widescreen)",
                   help='画面比例，须为完整枚举名：1:1 (Square) / 2:3 (Portrait Photo) / 3:2 (Photo) / '
                        '3:4 (Portrait Standard) / 4:3 (Standard) / 9:16 (Portrait Widescreen) / '
                        '16:9 (Widescreen) / 21:9 (Ultrawide)')
    p.add_argument("--megapixels", type=float, default=1.5, help="目标总像素（百万），默认 1.5")
    p.add_argument("--name", default="output")
    p.add_argument("--seed", type=int, default=-1, help="-1 随机 / 具体值固定（同时写入 KSampler 与 SeedVR2）")
    p.add_argument("--steps", type=int, default=None,
                   help="覆盖模板步数（默认不传=模板 8 步；蒸馏 LoRA 配套档位是 8）")
    p.add_argument("--cfg", type=float, default=None, help="覆盖 CFG（默认模板 1）")
    p.add_argument("--loras", action="append", default=[],
                   help='LoRA 开关，格式 "名:强度:on|off"，可重复传。'
                        '🔴 默认不传＝只有模板那条 moss_context_detaile_tweaker@0.60 生效，'
                        '画风请用提示词控制；只有作者明确点名某条时才传这个参数')
    p.add_argument("--no-default-lora", dest="no_default_lora", action="store_true",
                   help=f"关掉模板默认开启的 {DEFAULT_LORA}")
    p.add_argument("--seedvr2-res", dest="seedvr2_res", type=int, default=None,
                   help="SeedVR2 放大短边目标（模板 1440）；显存吃紧时降到 1080")
    p.add_argument("--no-upscale", dest="no_upscale", action="store_true",
                   help="跳过 SeedVR2 放大，直接输出原图")
    p.add_argument("--list-loras", dest="list_loras", action="store_true",
                   help="只打印可选 LoRA 清单（选择题用），不出图")
    args = p.parse_args()

    if args.list_loras:
        print_loras()
        return

    wf = build(load_prompt(args), args.ratio, args.megapixels, args.name,
               args.steps, args.cfg, args.loras, args.no_default_lora,
               args.seedvr2_res, args.no_upscale, args.seed)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
