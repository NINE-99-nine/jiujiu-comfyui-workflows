# -*- coding: utf-8 -*-
# ==================== flux2图像放大编辑 · 引子（黑盒，agent 只传参数） ====================
# 与 flux2图像放大编辑_api.json 同 basename → 自动配对。
# 原理：SAM3.1 遮罩识别(5号) → Inpaint Crop 抽取放大(15号) → flux2-klein 编辑(7号) → Inpaint Stitch 叠加回原图(24号)。
#
# 可控节点（agent 只传这些）：
#   [1]  图1（要编辑的原图 LoadImage）            --img1 <本地图片路径>
#   [5]  遮罩区域 CLIPTextEncode(SAM3.1识别范围, 须英文)  --mask "face / the girl / clothes ..."
#   [7]  编辑内容 CLIPTextEncode(flux2-klein 编辑词)       --prompt "change her expression to..."
#   [16] 图2（可选参考图 LoadImage, 默认跳过）      --img2 <本地图片路径>
#   [35] 图2开启开关(GroupIgnoreManager)           --use-img2
#   [33] Lora Manager                              --loras 名:强度:on
#   [27] SaveImage 保存名                          --name
#
# 单图模式（默认）：只用图1+遮罩词+编辑词，KSampler[25].positive=[22]/negative=[19] 直连主链。
# 多参考模式（--img2 --use-img2）：注入图2分支 [16]→[14]→[8]→[13]/[12]，重接 [25].positive=[13]/negative=[12]，
#   [13]conditioning=[22]/latent=[8(图2)]，[12]conditioning=[19]/latent=[8(图2)]——以图2作参考、文本控制编辑。
#
# 用法:
#   python flux2图像放大编辑_api.py --img1 f:/x.png --mask "the girl" --prompt "change her expression to..." \
#         [--img2 f:/y.png --use-img2]
# 只输出一行 JSON: {"kind":"image","prompt_id":…,"file":…,"size":…}

import argparse, json, os, sys, datetime, re, urllib.request
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_suffix(".json")
COMFY = "http://127.0.0.1:8188"

P_IMG1, P_MASK, P_PROMPT, P_IMG2, P_GIM, P_LORA, P_PREFIX, P_KS = "1", "5", "7", "16", "35", "33", "27", "25"


def _upload_image(path):
    """把本地图片上传到 ComfyUI input 目录，返回可填入 LoadImage['image'] 的文件名。"""
    path = str(path)
    fname = os.path.basename(path)
    ext = os.path.splitext(fname)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        raise SystemExit("不支持的图片格式: %s" % ext)
    with open(path, "rb") as f:
        data = f.read()
    boundary = "----hermesflux2" + str(os.getpid())
    parts = []
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{fname}\"\r\nContent-Type: image/png\r\n\r\n".encode())
    parts.append(data + b"\r\n")

    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n".encode())
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    req = urllib.request.Request(COMFY + "/upload/image", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary}, method="POST")
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
    name = r.get("name")
    sub = r.get("subfolder", "")
    return name if not sub else f"{sub}/{name}"


def _inject_img2(wf, img2_fname):
    """注入图2多参考分支：[16]→[14]→[8]→[13]/[12]，重接 KSampler[25] 的 positive/negative。"""
    wf["16"] = {"inputs": {"image": img2_fname}, "class_type": "LoadImage", "_meta": {"title": "图片2"}}
    wf["14"] = {"inputs": {"upscale_method": "nearest-exact", "megapixels": 1, "resolution_steps": 1,
                           "image": ["16", 0]}, "class_type": "ImageScaleToTotalPixels", "_meta": {"title": "图2缩放"}}
    wf["8"] = {"inputs": {"pixels": ["14", 0], "vae": ["34", 0]}, "class_type": "VAEEncode", "_meta": {"title": "图2编码"}}
    wf["13"] = {"inputs": {"conditioning": ["22", 0], "latent": ["8", 0]}, "class_type": "ReferenceLatent", "_meta": {"title": "positive-图2"}}
    wf["12"] = {"inputs": {"conditioning": ["19", 0], "latent": ["8", 0]}, "class_type": "ReferenceLatent", "_meta": {"title": "negative-图2"}}
    wf[P_KS]["inputs"]["positive"] = ["13", 0]
    wf[P_KS]["inputs"]["negative"] = ["12", 0]


def build(img1, mask, prompt, img2name, use_img2, name, lora_specs):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    if img1:
        wf[P_IMG1]["inputs"]["image"] = _upload_image(img1)
    if mask is not None:
        wf[P_MASK]["inputs"]["text"] = mask
    if prompt is not None:
        wf[P_PROMPT]["inputs"]["text"] = prompt
    if img2name and use_img2:
        _inject_img2(wf, img2name)
    node = wf[P_LORA]
    raw = node["inputs"].get("loras")
    loras = raw["__value__"] if isinstance(raw, dict) and "__value__" in raw else (raw or [])
    node["inputs"]["loras"] = comfy_submit.apply_lora_specs(loras, lora_specs)
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[P_PREFIX]["inputs"]["filename_prefix"] = f"{today}/{safe}"
    return wf


def main():
    p = argparse.ArgumentParser(description="flux2 图像放大编辑引子（SAM3.1 + flux2-klein）")
    p.add_argument("--img1", help="图1：要编辑的原图（本地路径，必传）")
    p.add_argument("--mask", help="遮罩区域(SAM3.1识别范围, 须英文, 如 face / the girl)")
    p.add_argument("--prompt", help="编辑内容(flux2-klein, 如 change her expression to...)")
    p.add_argument("--img2", help="图2：可选参考图（本地路径）")
    p.add_argument("--use-img2", action="store_true", help="开启图2多参考（配合 --img2 使用）")
    p.add_argument("--name", default="output")
    p.add_argument("--loras", action="append", default=None, help="可重复：NAME:STRENGTH:on|off，只改点名条目")
    args = p.parse_args()
    img2name = _upload_image(args.img2) if args.img2 else None
    wf = build(args.img1, args.mask, args.prompt, img2name, args.use_img2, args.name, args.loras)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
