# -*- coding: utf-8 -*-
# ============ qwen_image2.1汇总_api.py · qwen_image2.1 引子（黑盒，agent 只传参数） ============
# 与 qwen_image2.1汇总_api.json 同 basename → 自动配对。模板只读，只在内存里改。
#
# ── 节点地图（2026-09-24 新版模板，扁平编号）─────────────────────────────
#   568 ResolutionSelector   画布尺寸（aspect_ratio / megapixels / multiple=36）
#   563 LoadImage            参考图 1（编辑目标）
#   580 String               提示词入口（579.prompt ← 580.String）
#   579 TextEncodeQwenImage21 prompt / negative_prompt / resolution / images.image_N
#   577 ComfySwitchNode      画布来源开关
#   576 KSampler             seed / steps(默认20) / cfg(1) / euler+simple
#   578 QwenImage21Cache     device / dtype（XPU 显存旋钮；新模板默认 auto）
#   569 SaveImageAdvanced    filename_prefix（成品落盘）
#   567 PreviewImage / 570 Image Comparer（UI 专用对比器，提交前一律删）
#
# ── 两用机关（ComfySwitchNode[577]）────────────────────────────────────
#   switch = True  → KSampler 的 latent ← EmptyLatentImage[574]        = 画布由 ResolutionSelector[568] 定
#   switch = False → KSampler 的 latent ← TextEncodeQwenImage21[579] 第3路 latent = 画布跟随 image_1
#   → 判据只有一个：**不传参考图 = 文生图，传了参考图 = 编辑**（没有 --mode，无需手动切）。
#   → 图生图默认画布跟随参考图；加 **--custom-size** 才抢成 ResolutionSelector 的自定义尺寸
#     （官方 Note：custom_size on = use ResolutionSelector width/height；尺寸要贴近 image_1
#      缩放后的大小，否则编辑会偏移）。--resolution 只管输入侧，与画布无关。
#   ⚠️ 文生图时必须摘掉参考图：只要 images.image_1 还挂在 TextEncodeQwenImage21 上，
#      文本编码器仍会"看见"那张图并把它拼进序列 —— 所以无图时会 pop 该键，并删掉 LoadImage[563]。
#
# ── 多图参考 ────────────────────────────────────────────────────────────
#   TextEncodeQwenImage21 的 images 是 AUTOGROW 组（声明 image_1 … image_16，min=0）：
#   API 里直接写键 `images.image_N` 接 LoadImage 输出即可（**不需要** VAEEncode/ReferenceLatent 串接）。
#   图 1 = 编辑目标；图 2…N 由本引子动态补 LoadImage 节点后接入。
#   参考图统一缩放由 579.resolution（像素预算）控制，**不再需要 ImageScaleToTotalPixels 节点**。
#
# 用法：
#   python qwen_image2.1汇总_api.py --prompt-file 词.txt
#   python qwen_image2.1汇总_api.py --prompt "..." --images "f:/a.png"                 # auto → 编辑
#   python qwen_image2.1汇总_api.py --prompt "..." --images "f:/a.png,f:/b.png"        # 图1目标 + 图2参考
#   python qwen_image2.1汇总_api.py --prompt "..." --ratio "9:16 (Portrait Widescreen)" --megapixels 2
#   python qwen_image2.1汇总_api.py --prompt "..." --images "f:/a.png" --resolution 1024 \
#          --custom-size --ratio "16:9 (Widescreen)" --megapixels 2.0   # 图生图 + 自定义 2MP 画布
#   只输出一行 JSON：{"kind":"image","prompt_id":…,"file":…,"size":…}

import argparse, json, os, sys, random, datetime, re, urllib.request
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit, env

TEMPLATE = _here.with_suffix(".json")
COMFY = env.COMFY_URL          # 由 config.yaml 的 comfyui.url 决定

# ---- 可控节点（唯一合法改动面） ----
N_RATIO  = "568"       # ResolutionSelector    : 画布尺寸（aspect_ratio / megapixels）
N_SAVE   = "569"       # SaveImageAdvanced     : filename_prefix
N_IMG1   = "563"       # LoadImage             : 参考图 1（编辑目标）
N_KS     = "576"       # KSampler              : seed / steps / cfg
N_SWITCH = "577"       # ComfySwitchNode       : True=文生图 / False=编辑
N_CACHE  = "578"       # QwenImage21Cache      : device / dtype（XPU 显存旋钮）
N_TE     = "579"       # TextEncodeQwenImage21 : negative_prompt / resolution / images.image_N
N_STR    = "580"       # String                : **提示词走这里**（579.prompt ← 580.String）
N_CMP    = "570"       # Image Comparer (rgthree) : UI 专用对比器，agent 提交前一律删除

RATIOS = ["1:1 (Square)", "2:3 (Portrait Photo)", "3:2 (Photo)", "3:4 (Portrait Standard)",
          "4:3 (Standard)", "9:16 (Portrait Widescreen)", "16:9 (Widescreen)", "21:9 (Ultrawide)"]


def _upload_image(path):
    """把本地图上传到 ComfyUI 的 input 目录，返回可喂给 LoadImage 的名字。"""
    path = str(path)
    if not os.path.isfile(path):
        raise SystemExit("参考图不存在：%s" % path)
    fname = os.path.basename(path)
    ext = os.path.splitext(fname)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        raise SystemExit("不支持的图片格式: %s" % ext)
    with open(path, "rb") as f:
        data = f.read()
    boundary = "----hermesqwen21" + str(os.getpid())
    parts = []
    parts.append(('--%s\r\nContent-Disposition: form-data; name="image"; filename="%s"\r\n'
                  'Content-Type: image/png\r\n\r\n' % (boundary, fname)).encode())
    parts.append(data + b"\r\n")
    parts.append(('--%s\r\nContent-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n' % boundary).encode())
    parts.append(("--%s--\r\n" % boundary).encode())
    req = urllib.request.Request(COMFY + "/upload/image", data=b"".join(parts),
                                 headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary},
                                 method="POST")
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
    name = r.get("name"); sub = r.get("subfolder", "")
    return name if not sub else "%s/%s" % (sub, name)


def build(prompt, images, custom_size, ratio, megapixels, resolution,
          steps, cfg, seed, cache_device, cache_dtype, name):
    """images = 已上传到 ComfyUI 的文件名列表（图1 在前）。"""
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    images = images or []

    # 提示词（新模板走 String[580] → TextEncodeQwenImage21[579].prompt）
    if prompt is not None:
        wf[N_STR]["inputs"]["String"] = prompt
    # 参考图统一缩放上限（像素预算；0 = 各自原尺寸）
    if resolution is not None:
        wf[N_TE]["inputs"]["resolution"] = resolution

    # 图 1（编辑目标）：模板自带的 LoadImage[563]
    if images:
        wf[N_IMG1]["inputs"]["image"] = images[0]

    # 图 2..N：动态注入 LoadImage → images.image_N（缩放交给 579.resolution）
    for i, fname in enumerate(images[1:], start=2):
        lid = "img%d_load" % i
        wf[lid] = {"inputs": {"image": fname}, "class_type": "LoadImage",
                   "_meta": {"title": "图%d" % i}}
        wf[N_TE]["inputs"]["images.image_%d" % i] = [lid, 0]

    # UI 专用对比器（引用模板里残留的临时图）一律删掉，避免拉无用节点
    wf.pop(N_CMP, None)

    # 判据只有一个：无图 = 文生图（并摘掉参考图，否则文本编码器仍会看见它）
    has_img = bool(images)
    if not has_img:
        wf[N_TE]["inputs"].pop("images.image_1", None)
        wf.pop(N_IMG1, None)          # 连 LoadImage 一起摘掉，否则它会去加载模板里的样本图名
    # 画布来源：无图必走 EmptyLatentImage；有图默认跟随 image_1，开了 --custom-size 才抢成 ResolutionSelector
    use_custom = has_img and bool(custom_size)
    wf[N_SWITCH]["inputs"]["switch"] = (not has_img) or use_custom

    # 文生图尺寸（仅 switch=True 生效）
    if ratio:
        wf[N_RATIO]["inputs"]["aspect_ratio"] = ratio
    if megapixels:
        wf[N_RATIO]["inputs"]["megapixels"] = megapixels

    # 采样
    if steps:
        wf[N_KS]["inputs"]["steps"] = steps
    if cfg is not None:
        wf[N_KS]["inputs"]["cfg"] = cfg
    wf[N_KS]["inputs"]["seed"] = random.randint(1, 10 ** 15) if seed in (-1, None) else seed

    # XPU 显存缓存
    if cache_device:
        wf[N_CACHE]["inputs"]["device"] = cache_device
    if cache_dtype:
        wf[N_CACHE]["inputs"]["dtype"] = cache_dtype

    # 保存名（带横线日期目录，与 UI 出图同目录）
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[N_SAVE]["inputs"]["filename_prefix"] = "%s/%s" % (today, safe)
    return wf, has_img


def load_prompt(args):
    if args.prompt_file:
        path = Path(args.prompt_file).expanduser()
        if not path.is_file():
            print("[qwen_image2.1引子] 提示词文件不存在：%s" % path, file=sys.stderr)
            sys.exit(2)
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            print("[qwen_image2.1引子] 提示词文件为空：%s" % path, file=sys.stderr)
            sys.exit(2)
        return text
    text = (args.prompt or "").strip()
    if not text:
        print("[qwen_image2.1引子] --prompt 内容为空", file=sys.stderr)
        sys.exit(2)
    return text


def main():
    p = argparse.ArgumentParser(description="qwen_image2.1 引子（无图=文生图 / 有图=编辑；--custom-size 自定义画布）")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt", help="提示词（短稿直传；长稿/含引号一律用 --prompt-file）")
    src.add_argument("--prompt-file", dest="prompt_file", help="提示词文件路径（UTF-8）")
    p.add_argument("--images", action="append", default=None,
                   help="参考图本地路径，逗号分隔可多张；第 1 张=编辑目标。可重复传参累加。")
    p.add_argument("--ratio", choices=RATIOS, default=None,
                   help="画布比例（文生图；开了 --custom-size 时也是图生图的画布比例）。"
                        "必须传完整枚举串，如 \"2:3 (Portrait Photo)\"")
    p.add_argument("--megapixels", type=float, default=None,
                   help="画布总像素（默认沿用模板 2.0；开了 --custom-size 时也是图生图的画布总像素）")
    p.add_argument("--custom-size", dest="custom_size", action="store_true",
                   help="图生图时把画布交给 ResolutionSelector（--ratio/--megapixels），不再跟随参考图；"
                        "尺寸要贴近参考图缩放后的大小，否则编辑会偏移")
    p.add_argument("--resolution", type=int, default=1024,
                   help="参考图统一缩放到约 N×N 像素（保比例，36 的倍数）；0=各自原尺寸（默认 1024）")
    p.add_argument("--steps", type=int, default=None,
                   help="采样步数（template 默认 20 = 标准流）。用户没额外说明就用 20；"
                        "用户明说、或这张确实需要更精致时再提高（提高要在汇报里说明，别静默改）")
    p.add_argument("--cfg", type=float, default=None, help="cfg（官方路径=1，默认沿用模板）")
    p.add_argument("--seed", type=int, default=-1, help="-1 随机 / 具体值固定")
    p.add_argument("--cache-device", dest="cache_device", default=None,
                   choices=["auto", "gpu", "cpu", "off"], help="QwenImage21Cache 缓存位置（模板默认 auto）")
    p.add_argument("--cache-dtype", dest="cache_dtype", default=None,
                   choices=["default", "int8", "int4"], help="QwenImage21Cache 存储精度")
    p.add_argument("--name", default="output", help="成品名（自动加日期目录）")
    p.add_argument("--dry-run", dest="dry_run", action="store_true",
                   help="只打印将要提交的改动摘要，不提交")
    args = p.parse_args()

    # 收集参考图（逗号分隔 + 可重复）
    raw = []
    for chunk in (args.images or []):
        raw += [x.strip() for x in chunk.split(",") if x.strip()]
    if len(raw) > 16:
        raise SystemExit("参考图最多 16 张（节点声明 image_1..image_16），当前 %d 张" % len(raw))
    uploaded = [_upload_image(x) for x in raw]

    wf, has_img = build(load_prompt(args), uploaded, args.custom_size, args.ratio, args.megapixels,
                        args.resolution, args.steps, args.cfg,
                        args.seed, args.cache_device, args.cache_dtype, args.name)

    if args.dry_run:
        te = wf[N_TE]["inputs"]
        print(json.dumps({
            "dry_run": True,
            "mode": ("edit+custom_size" if (has_img and args.custom_size)
                     else ("edit" if has_img else "t2i")),
            "switch": wf[N_SWITCH]["inputs"]["switch"],
            "ref_images": [k for k in te if k.startswith("images.image_")],
            "resized_to": te.get("resolution"),
            "t2i_aspect_ratio": wf[N_RATIO]["inputs"].get("aspect_ratio"),
            "t2i_megapixels": wf[N_RATIO]["inputs"].get("megapixels"),
            "steps": wf[N_KS]["inputs"].get("steps"),
            "cfg": wf[N_KS]["inputs"].get("cfg"),
            "seed": wf[N_KS]["inputs"].get("seed"),
            "cache": [wf[N_CACHE]["inputs"].get("device"), wf[N_CACHE]["inputs"].get("dtype")],
            "save_prefix": wf[N_SAVE]["inputs"]["filename_prefix"],
            "prompt_head": (wf[N_STR]["inputs"].get("String") or "")[:60],
            "has_comparer": N_CMP in wf,
            "nodes": len(wf),
        }, ensure_ascii=False, indent=2))
        return

    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
