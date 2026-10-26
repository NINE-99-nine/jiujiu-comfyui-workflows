# -*- coding: utf-8 -*-
# ============ moss_api.py · MOSS-Image 引子 v4（黑箱，agent 只传参数） ============
# 与 moss_api.json 同 basename → 自动配对。模板 = 20 节点（LoRA 堆 + 分辨率大师简化版）。
#
# 链路：13 UNet → 61 加速 LoRA(lodestones-8-steps-dmd2-lora @1.0) → 93 LoraManager(9 条，默认 1 条)
#       → 19 KSampler(8 步 / cfg 1.0 / er_sde / simple) → 22 VAEDecode
#       → 103 AnySwitch → 97 AnySwitch → 81 SaveImage
# 提示词：93 触发词 → 101 JoinStringMulti(串1=触发词 / 串2=98 质量词 / 串3=99 提示词) → 121 AnySwitch → 4 正向 CLIPTextEncode
# 质量词：98 已清空（2026-10-25 作者要求），正向提词 = LoRA 触发词 + 用户提示词，不再拼固定质量标签。
# 分辨率：154 ResolutionMasterSimplify 的 width / height（直接写数字，无比例下拉）→ 7 EmptyLatentImage
#
# **默认不放大**：97 的优先输入来自 103 原图，成品 = 输入分辨率。
# SeedVR2 链保留在代码里但默认不启用（作者 2026-10-25 要求）；要放大才传 --upscale。
#
# 用法：
#   python moss_api.py --prompt "…" [--ratio "2:3" --megapixels 1.5 --name 名字 --seed -1]
#   python moss_api.py --prompt-file 词.txt
#   python moss_api.py --layout 布局.json --width 1776 --height 1184
#   python moss_api.py --list-loras                                # 只列可选 LoRA，不出图
#   python moss_api.py --prompt-file 词.txt --loras "Nyalia_moss_v1_lokr:1:on"
#
# 只输出一行 JSON：{"kind":"image","prompt_id":…,"file":…,"size":…}

import argparse, copy, datetime, json, math, random, re, sys
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_suffix(".json")

# ---- 节点号（v3 模板）----
P_PROMPT   = "99"    # String：提示词入口（可变的那一框）
P_QUALITY  = "98"    # String：质量词（固定，引子绝不写）
P_RES      = "154"   # ResolutionMasterSimplify：width / height
P_SAMPLER  = "19"    # KSampler：步数 / cfg / seed
P_LORA     = "93"    # Lora Loader (LoraManager)：LoRA 堆
P_PREFIX   = "81"    # SaveImage
P_SW_HI    = "97"    # AnySwitch：优先=放大后[85] / 备用=原图[22]
P_SW_LO    = "103"   # AnySwitch：喂给放大器的输入
P_UPSCALER = "85"    # SeedVR2VideoUpscaler（模板里没有，--upscale 时内存补）

DEFAULT_STEPS = 8                                               # 2026-10-25 定档；模板已同步为 8
DEFAULT_LORA = "moss_context_detaile_tweaker_20261018_rank2"   # 细节调节器（不许自作主张关）
DEFAULT_LORAS = (DEFAULT_LORA,)                                 # 默认只开细节档；观澜是写实画风 LoRA，不是质量档（2026-10-26 控制变量实测：它拉低质量、且与 cfg 1.0 冲突），默认关闭
SEED_MAX = 4294967295   # seedvr2 节点的 seed 上限 2^32-1

# MOSS-Image 要求宽高是 16 的倍数
MULTIPLE = 16

# 比例枚举（--ratio 只认这些，写 "9:16" 也接受，会自动补全名）
RATIOS = {
    "1:1": "1:1 (Square)",
    "2:3": "2:3 (Portrait Photo)",
    "3:2": "3:2 (Photo)",
    "3:4": "3:4 (Portrait Standard)",
    "4:3": "4:3 (Standard)",
    "9:16": "9:16 (Portrait Widescreen)",
    "16:9": "16:9 (Widescreen)",
    "21:9": "21:9 (Ultrawide)",
}

# SeedVR2 三节点（从作者 UI 版原样搬来；--upscale 时注入内存）
SEEDVR2_NODES = {
    "79": {"inputs": {"model": "ema_vae_fp16.safetensors", "device": "xpu:0", "encode_tiled": False,
                      "encode_tile_size": 1024, "encode_tile_overlap": 128, "decode_tiled": True,
                      "decode_tile_size": 1024, "decode_tile_overlap": 128, "tile_debug": "false",
                      "offload_device": "cpu", "cache_model": False},
           "class_type": "SeedVR2LoadVAEModel", "_meta": {"title": "SeedVR2 (Down)Load VAE Model"}},
    "80": {"inputs": {"model": "seedvr2_ema_3b-Q4_K_M.gguf", "device": "xpu:0", "blocks_to_swap": 32,
                      "swap_io_components": False, "offload_device": "cpu", "cache_model": False,
                      "attention_mode": "flash_attn_3"},
           "class_type": "SeedVR2LoadDiTModel", "_meta": {"title": "SeedVR2 (Down)Load DiT Model"}},
    P_UPSCALER: {"inputs": {"seed": 2150721059, "resolution": 1440, "max_resolution": 2880, "batch_size": 1,
                            "uniform_batch_size": False, "color_correction": "lab", "temporal_overlap": 0,
                            "prepend_frames": 0, "input_noise_scale": 0, "latent_noise_scale": 0,
                            "offload_device": "xpu:0", "enable_debug": False,
                            "image": [P_SW_LO, 1], "dit": ["80", 0], "vae": ["79", 0]},
                 "class_type": "SeedVR2VideoUpscaler",
                 "_meta": {"title": "SeedVR2 Video Upscaler (v2.5.24)"}},
}


def _loras(wf):
    return wf[P_LORA]["inputs"]["loras"]["__value__"]


def _sync_lora_text(wf):
    """把 active 的 LoRA 回写成 text widget，保持 UI 显示与数组一致。"""
    act = " ".join(f"<lora:{e['name']}:{float(e['strength']):.2f}>"
                   for e in _loras(wf) if e.get("active"))
    wf[P_LORA]["inputs"]["text"] = act


def apply_loras(wf, specs, no_default):
    """specs: ["名:强度:on|off", ...] —— 只动点名条目，其余保持模板原样。

    🔴 P0：不传 specs 且不关默认时，除默认那条（细节档）以外全部强制关闭。
    「默认只有一条 LoRA」由程序钉住，不靠自觉（作者 2026-10-26 改：观澜降级为普通画风 LoRA）。
    """
    arr = _loras(wf)
    if not specs and not no_default:
        for e in arr:
            e["active"] = (e["name"] in DEFAULT_LORAS)
    if no_default:
        for e in arr:
            if e["name"] in DEFAULT_LORAS:
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


def _parse_ratio(ratio):
    """'2:3' / '2:3 (Portrait Photo)' → (2, 3)；不认识的抛 SystemExit 并列出合法值。"""
    key = (ratio or "").split("(")[0].strip()
    if key not in RATIOS:
        raise SystemExit(f"[moss引子] --ratio 不认识：{ratio}\n合法值：{' / '.join(RATIOS.values())}")
    rw, rh = key.split(":")
    return int(rw), int(rh)


def _snap(v):
    return max(MULTIPLE, int(math.floor(v / MULTIPLE + 0.5)) * MULTIPLE)


def calc_size(ratio, megapixels):
    """按比例 + 像素预算算宽高，各对齐到 16 的倍数（MOSS 的硬约束）。"""
    rw, rh = _parse_ratio(ratio)
    px = float(megapixels) * 1_000_000
    w = math.sqrt(px * rw / rh)
    h = px / w
    return _snap(w), _snap(h)


def build(prompt, ratio=None, megapixels=None, name="output", steps=None, cfg=None,
          loras=None, no_default_lora=False, seedvr2_res=None, upscale=False, seed=-1,
          layout=False, width=None, height=None):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    # ① 提示词 → 99 String（101 自动把 93 触发词 + 98 质量词拼在前面；98 绝不动）
    wf[P_PROMPT]["inputs"]["String"] = prompt

    # ② 尺寸 → 154 ResolutionMasterSimplify
    #    不传时沿用模板里的宽高（1024×1536 ≈ 2:3 / 1.57MP），传了就按比例 + 像素预算重算
    res = wf[P_RES]["inputs"]
    if ratio is not None or megapixels is not None:
        if ratio is None:
            ratio = f"{res['width']}:{res['height']}"
        if megapixels is None:
            megapixels = res["width"] * res["height"] / 1e6
        res["width"], res["height"] = calc_size(ratio, megapixels)
    # --width / --height 直接钉死（16 的倍数，优先于 --ratio/--megapixels）
    if width:
        res["width"] = _snap(int(width))
    if height:
        res["height"] = _snap(int(height))

    # ③ 采样器（默认 8 步；模板已 8，显式写死防模板回退）
    wf[P_SAMPLER]["inputs"]["steps"] = steps or DEFAULT_STEPS
    if cfg is not None:
        wf[P_SAMPLER]["inputs"]["cfg"] = cfg
    seed_val = random.randint(1, 10 ** 15) if seed == -1 else seed
    wf[P_SAMPLER]["inputs"]["seed"] = seed_val

    # ④ LoRA → 93 LoraManager
    apply_loras(wf, loras, no_default_lora)

    # ④b Layout 模式：101 JoinStringMulti 会把 93 触发词 + 98 质量词无分隔符拼在 99 前面，
    #     layout JSON 必须独占文本，否则 JSON 前有前缀、解析失败 → 这里把两段置空。
    #     LoRA 仍由 93 的 loras 数组挂载，强度与生效不变；只影响拼进提示词的那串文本。
    if layout:
        wf[P_QUALITY]["inputs"]["String"] = ""
        wf[P_LORA]["inputs"]["text"] = ""

    # ⑤ 放大 → 默认不放大（模板无 SeedVR2 节点，97 直接吃 103 的原图）
    if upscale or seedvr2_res:
        for nid, node in SEEDVR2_NODES.items():
            wf[nid] = copy.deepcopy(node)
        if seedvr2_res:
            wf[P_UPSCALER]["inputs"]["resolution"] = int(seedvr2_res)
        wf[P_UPSCALER]["inputs"]["seed"] = seed_val % (SEED_MAX + 1)
        wf[P_SW_HI]["inputs"]["优先输入"] = [P_UPSCALER, 0]

    # ⑥ 兜底：AnySwitch 的判据是「优先输入非 None 且非 ExecutionBlocker」，空着会输出 None 断链
    for nid in (P_SW_LO, P_SW_HI):
        ins = wf.get(nid, {}).get("inputs", {})
        if ins and "优先输入" not in ins and "备用输入" in ins:
            ins["优先输入"] = list(ins["备用输入"])

    # ⑦ 输出前缀
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[P_PREFIX]["inputs"]["filename_prefix"] = f"{today}/{safe}"
    return wf


def load_prompt(args):
    if getattr(args, "layout", None):
        path = Path(args.layout).expanduser()
        if not path.is_file():
            print(f"[moss引子] layout 文件不存在或不是文件：{path}", file=sys.stderr)
            sys.exit(2)
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            print(f"[moss引子] layout 文件为空：{path}", file=sys.stderr)
            sys.exit(2)
        try:
            json.loads(text)
        except Exception as e:
            print(f"[moss引子] layout 文件不是合法 JSON：{path} → {e}", file=sys.stderr)
            sys.exit(2)
        return text
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
    print(f"可选 LoRA（{len(arr)} 条，★ = 模板默认开启，不点名就一直开着）：")
    for i, e in enumerate(arr, 1):
        star = "★" if e.get("active") else " "
        tag = ""
        if e["name"] == DEFAULT_LORA:
            tag = "  ← 默认·细节档，除作者点名不许关"
        elif e["name"] in DEFAULT_LORAS:
            tag = "  ← 默认·质量提升档(KOOK)，除作者点名不许关"
        print(f"  {i:>2}. {star} {e['name']}  (strength {e['strength']}){tag}")
    print('\n用法：--loras "<名字>:<强度>:on|off"，可重复传；--no-default-lora 关掉默认那条（细节档）。')


def main():
    p = argparse.ArgumentParser(description="MOSS-Image 引子 v4（8 步 / cfg 1.0 · LoRA 堆 · 默认不放大）")
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument("--prompt", help="正向提示词（caption 自然语言段）")
    src.add_argument("--prompt-file", dest="prompt_file",
                     help="提示词文件路径（UTF-8；长文/含引号/多段换行一律用这个）")
    src.add_argument("--layout", metavar="JSON文件",
                     help="Layout JSON 文件路径（UTF-8）。走 layout 模式：99 只吃这段 JSON，"
                          "自动清空质量词与 LoRA 触发词文本（否则 101 拼前缀会让 JSON 解析失败），"
                          "LoRA 强度不受影响。多人/要控位置的构图一律用它")
    p.add_argument("--width", type=int, default=None,
                   help="直接钉死宽度（自动对齐 16 的倍数），优先于 --ratio/--megapixels")
    p.add_argument("--height", type=int, default=None,
                   help="直接钉死高度（自动对齐 16 的倍数），优先于 --ratio/--megapixels")
    p.add_argument("--ratio", default=None,
                   help='画面比例：不传＝沿用模板 1024×1536（2:3）。合法值 '
                        '1:1 / 2:3 / 3:2 / 3:4 / 4:3 / 9:16 / 16:9 / 21:9（全名或短名都行）')
    p.add_argument("--megapixels", type=float, default=None,
                   help="目标总像素（百万）：不传＝沿用模板（约 1.57MP）。常用 1.5（默认建议档）")
    p.add_argument("--name", default="output")
    p.add_argument("--seed", type=int, default=-1, help="-1 随机 / 具体值固定（同时写入 KSampler 与 SeedVR2）")
    p.add_argument("--steps", type=int, default=None, help="覆盖模板步数（模板 8 步；一般不传）")
    p.add_argument("--cfg", type=float, default=None, help="覆盖 CFG（模板 1.0，2026-10-26 实测 1.0 质量高于 3.5）")
    p.add_argument("--loras", action="append", default=[],
                   help='LoRA 开关，格式 "名:强度:on|off"，可重复传。'
                        '🔴 默认不传＝只有模板那条 moss_context_detaile_tweaker@0.60 生效，'
                        '画风请用提示词控制；只有作者明确点名某条时才传这个参数')
    p.add_argument("--no-default-lora", dest="no_default_lora", action="store_true",
                   help=f"关掉默认 LoRA（{' + '.join(DEFAULT_LORAS)}）")
    p.add_argument("--seedvr2-res", dest="seedvr2_res", type=int, default=None,
                   help="SeedVR2 放大短边目标（默认 1440）；传了就等于要放大（隐含 --upscale）")
    p.add_argument("--upscale", dest="upscale", action="store_true",
                   help="走 SeedVR2 放大链（短边 1440，节点在内存补）。**默认不放大**，成品 = 输入分辨率")
    p.add_argument("--no-upscale", dest="no_upscale", action="store_true",
                   help="兼容旧命令用；不放大本来就是默认，传了无副作用")
    p.add_argument("--list-loras", dest="list_loras", action="store_true",
                   help="只打印可选 LoRA 清单（选择题用），不出图")
    args = p.parse_args()

    if args.list_loras:
        print_loras()
        return

    wf = build(load_prompt(args), args.ratio, args.megapixels, args.name,
               args.steps, args.cfg, args.loras, args.no_default_lora,
               args.seedvr2_res, args.upscale, args.seed,
               layout=bool(getattr(args, "layout", None)),
               width=args.width, height=args.height)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
