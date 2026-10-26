# -*- coding: utf-8 -*-
# ============ qwenimage2.1局部放大编辑_api.py · 引子（黑盒，agent 只传参数） ============
# 与 qwenimage2.1局部放大编辑_api.json 同 basename → 自动配对。模板只读，只在内存里改。
#
# 原理（局部放大编辑）：
#   图1[8 LoadImage] → SAM3.1[9 模型 + 16 SAM3_Detect，检索词来自 25 CLIPTextEncode]
#   → 遮罩[16] → InpaintCropImproved[13] 按遮罩裁出目标区域并放大到 768×768（第 2 路输出 cropped_image）
#   → TextEncodeQwenImage21[6] 的 images.image_1（**画布跟着这张裁剪图走**，因为 11 号开关=false，
#     KSampler 的 latent 吃 6 号的第 3 路 latent）
#   → 提示词[4 String → 6.prompt] → KSampler[18]（20 步 / cfg 1 / euler+simple）
#   → VAEDecode[19] → Image to RGB[30] → 亮度对比度[14] → InpaintStitchImproved[15] 拼回原图
#   → 12 预览遮罩 / 28 预览裁剪块 / 21 保存
#
# 可控节点（agent 只传这些）：
#   [8]  要编辑的原图 LoadImage                          --img1 <本地路径>
#   [25] SAM3.1 检索词 CLIPTextEncode（**必须英文**）      --mask "the girl in the left"
#   [4]  编辑指令 String → 6.prompt                       --prompt "change ... to ..."
#   [6]  images.image_2..16 多图参考（引子动态补 LoadImage） --ref <本地路径>（可重复 / 逗号）
#   [6]  resolution 参考图/裁剪块像素预算＝编辑画布边长   --canvas 1024
#   [13] 输出缩放至目标尺寸 **已关**（裁剪块按遮罩自适应当前比例，不再钉 768×768）
#   [13] 遮罩外扩像素 / 上下文系数                         --mask-expand 0 / --context 1.2
#   [18] steps/cfg/seed                                   --steps 20 / --cfg 1 / --seed -1
#   [2]  LoRA 强度                                         --lora-strength 1.0
#   [21] 保存名                                            --name
#
# 多图语义：图 1（裁剪块）永远是编辑目标与画布来源；--ref 追加的图按 Picture 2、3… 进同一段 conditioning，
#   提示词里直接用 "the person in picture 2" 指代即可（Qwen3VL 的 tokenize 自动加 Picture N 前缀）。
#   ⚠️ 不注入 VAEEncode/ReferenceLatent —— qwen2.1 的 images 是 AUTOGROW 组，直接接 LoadImage 输出。
#
# 用法：
#   python qwenimage2.1局部放大编辑_api.py --img1 <local_path> --mask "the girl" \
#          --prompt "repaint her stockings in glossy black with a lace top" --name 黑丝放大
#   python qwenimage2.1局部放大编辑_api.py --img1 <local_path> --mask "the dress" \
#          --prompt "replace the dress with the one in picture 2" --ref <local_path> --name 换装
#   只输出一行 JSON：{"kind":"image","prompt_id":…,"file":…,"size":…}

import argparse, json, os, sys, datetime, re, urllib.request
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit, env

TEMPLATE = _here.with_suffix(".json")
COMFY = env.COMFY_URL          # 由 config.yaml 的 comfyui.url 决定

# ---- 可控节点（唯一合法改动面） ----
N_IMG1   = "8"     # LoadImage             : 要编辑的原图
N_MASK   = "25"    # CLIPTextEncode(SAM3)  : 检索词，必须英文
N_PROMPT = "4"     # String                : 编辑指令 → 6.prompt
N_TE     = "6"     # TextEncodeQwenImage21 : resolution / images.image_N
N_CROP   = "13"    # InpaintCropImproved   : 裁剪块尺寸 / 遮罩外扩 / 上下文系数
N_KS     = "18"    # KSampler              : seed / steps / cfg
N_CACHE  = "17"    # QwenImage21Cache      : device（A770 显存旋钮；多图参考出鬼影时试 off）
N_LORA   = "2"     # LoraLoaderModelOnly   : strength_model
N_SAVE   = "21"    # SaveImageAdvanced     : filename_prefix

MAX_REFS = 15      # images.image_2 … image_16


def _upload_image(path):
    """把本地图片上传到 ComfyUI input 目录，返回可填入 LoadImage['image'] 的文件名。"""
    path = str(path)
    if not os.path.isfile(path):
        raise SystemExit("图片不存在：%s" % path)
    fname = os.path.basename(path)
    ext = os.path.splitext(fname)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        raise SystemExit("不支持的图片格式: %s" % ext)
    with open(path, "rb") as f:
        data = f.read()
    boundary = "----hermesqwen21crop" + str(os.getpid())
    parts = []
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
                  "Content-Type: image/png\r\n\r\n" % (boundary, fname)).encode())
    parts.append(data + b"\r\n")
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n" % boundary).encode())
    parts.append(("--%s--\r\n" % boundary).encode())
    req = urllib.request.Request(COMFY + "/upload/image", data=b"".join(parts),
                                 headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary},
                                 method="POST")
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
    name = r.get("name"); sub = r.get("subfolder", "")
    return name if not sub else "%s/%s" % (sub, name)


def _split_list(values):
    """--ref 支持重复传参，也支持逗号分隔。"""
    out = []
    for v in values or []:
        out.extend([x.strip() for x in str(v).split(",") if x.strip()])
    return out


def build(img1_name, mask, prompt, ref_names, canvas, mask_expand, context,
          steps, cfg, seed, lora_strength, cache, name):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    wf[N_IMG1]["inputs"]["image"] = img1_name
    if mask is not None:
        wf[N_MASK]["inputs"]["text"] = mask
    if prompt is not None:
        wf[N_PROMPT]["inputs"]["String"] = prompt

    # 参考图 2..N：动态补 LoadImage，接进 AUTOGROW 组（不串 VAEEncode/ReferenceLatent）
    ref_names = ref_names or []
    if len(ref_names) > MAX_REFS:
        raise SystemExit("参考图最多 %d 张（image_2…image_16），收到 %d 张" % (MAX_REFS, len(ref_names)))
    for i, fname in enumerate(ref_names, start=2):
        lid = "ref%d_load" % i
        wf[lid] = {"inputs": {"image": fname}, "class_type": "LoadImage",
                   "_meta": {"title": "图%d" % i}}
        wf[N_TE]["inputs"]["images.image_%d" % i] = [lid, 0]

    # 画布＝裁剪块被缩放到 canvas×canvas 后的尺寸（AUTOGROW 首图决定 latent 长宽）
    if canvas is not None:
        wf[N_TE]["inputs"]["resolution"] = canvas

    crop = wf[N_CROP]["inputs"]
    if mask_expand is not None:
        crop["mask_expand_pixels"] = mask_expand
    if context is not None:
        crop["context_from_mask_extend_factor"] = context

    ks = wf[N_KS]["inputs"]
    if steps is not None:
        ks["steps"] = steps
    if cfg is not None:
        ks["cfg"] = cfg
    if seed is not None and seed != -1:
        ks["seed"] = seed

    if cache is not None:
        wf[N_CACHE]["inputs"]["device"] = cache

    if lora_strength is not None:
        wf[N_LORA]["inputs"]["strength_model"] = lora_strength

    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[N_SAVE]["inputs"]["filename_prefix"] = "%s/%s" % (today, safe)
    return wf


def main():
    p = argparse.ArgumentParser(description="qwen_image2.1 局部放大编辑引子（SAM3.1 遮罩 + 裁剪放大 + qwen2.1 编辑）")
    p.add_argument("--img1", required=True, help="图1：要编辑的原图（本地路径，必传）")
    p.add_argument("--mask", required=True,
                   help="SAM3.1 检索词（**必须英文**）：face / the girl in the left / her stockings / the dress")
    p.add_argument("--prompt", required=True, help="编辑指令（中文或英文皆可；要干什么写清楚）")
    p.add_argument("--ref", action="append", default=[],
                   help="可选参考图（本地路径，可重复传参或用逗号分隔，最多 15 张）：图2、图3…")
    p.add_argument("--canvas", type=int, default=None,
                   help="编辑画布边长（参考图/裁剪块统一缩放预算，默认模板 1024；越大越细也越吃显存）")
    p.add_argument("--mask-expand", dest="mask_expand", type=int, default=None,
                   help="遮罩外扩像素（默认 0；想多带一点周边就 16～64）")
    p.add_argument("--context", type=float, default=None,
                   help="遮罩外上下文系数（默认 1.2；越大裁剪框越松，周边信息越多）")
    p.add_argument("--steps", type=int, default=None, help="采样步数（默认模板 20）")
    p.add_argument("--cfg", type=float, default=None, help="CFG（默认模板 1）")
    p.add_argument("--seed", type=int, default=None, help="-1 随机 / 具体值固定（默认沿用模板 seed）")
    p.add_argument("--lora-strength", dest="lora_strength", type=float, default=None,
                   help="模板内 uncensored LoRA 强度（默认模板 1.0）")
    p.add_argument("--cache", default=None, choices=["auto", "gpu", "cpu", "off"],
                   help="QwenImage21Cache 位置（默认模板 auto；OOM 或出鬼影时试 cpu/off）")
    p.add_argument("--name", default="output", help="成品名（自动加 日期/ 目录）")
    args = p.parse_args()

    img1_name = _upload_image(args.img1)
    refs = [_upload_image(x) for x in _split_list(args.ref)]
    wf = build(img1_name, args.mask, args.prompt, refs, args.canvas,
               args.mask_expand, args.context, args.steps, args.cfg, args.seed,
               args.lora_strength, args.cache, args.name)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
