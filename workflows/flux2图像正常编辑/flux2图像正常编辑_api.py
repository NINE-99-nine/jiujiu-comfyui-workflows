# -*- coding: utf-8 -*-
# ==================== flux2图像正常编辑 · 引子（黑盒，agent 只传参数） ====================
# 与 flux2图像正常编辑_api.json 同 basename → 自动配对。
# 原理：flux2-klein 万能图像编辑。不做 SAM 遮罩裁剪放大（那是放大编辑工作流），
#       而是把整图/多参考图作为 reference 喂给 flux2-klein 全图重绘/融合。
#
# 可控节点（agent 只传这些）：
#   [1301] 编辑内容 Prompt（PrimitiveStringMultiline）  --prompt "将图1人物换成..."
#   [1306] 分辨率（ResolutionMasterSimplify）            --w / --h  (动态1.2~1.6M，图多则低)
#   [1326] 图1（LoadImage, 主图）                        --img1 <本地路径>
#   [1327] 图2（LoadImage, 默认绕过）                    --img2 <本地路径>
#   [1328] 图3（LoadImage, 默认绕过）                    --img3 <本地路径>
#   [1333] Lora Manager                                  --loras 名:强度:on
#   [1325] SaveImage 保存名                              --name
#
# 单图模式（默认）：只用图1 + prompt，KSampler[1313].positive=[1319:741]/negative=[1319:739] 直连主图 reference。
# 多图模式（--img2/--img3）：像放大编辑一样"动态注入"被绕过的子图分支——
#   展开 1317/1318（Reference Conditioning 子图：
#       VAEEncode(像素=各自缩放图1315/1316) + ReferenceLatent(conditioning=前层输出, latent=该图VAEEncode) ),
#   把 1317 接在 1319(主图) 之后、1318 接在 1317 之后，最终 1318 → KSampler(1313)。
#
# 用法:
#   python flux2图像正常编辑_api.py --img1 "f:/x.png" --prompt "把图1的人换成白发红瞳少女" [--img2 "f:/y.png"] [--img3 "f:/z.png"] [--w 1344 --h 768]
# 只输出一行 JSON: {"kind":"image","prompt_id":…,"file":…,"size":…}

import argparse, json, os, sys, datetime, re, urllib.request
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_suffix(".json")
COMFY = "http://127.0.0.1:8188"
VAE = "1338"          # VAELoader 复用主图的
KS = "1313"
P_PROMPT, P_RES, P_IMG1, P_IMG2, P_IMG3, P_PREFIX, P_LORA = "1301", "1306", "1326", "1327", "1328", "1325", "1333"


def _upload_image(path):
    path = str(path)
    fname = os.path.basename(path)
    ext = os.path.splitext(fname)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        raise SystemExit("不支持的图片格式: %s" % ext)
    with open(path, "rb") as f:
        data = f.read()
    boundary = "----hermesflux2normal" + str(os.getpid())
    parts = []
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{fname}\"\r\nContent-Type: image/png\r\n\r\n".encode())
    parts.append(data + b"\r\n")
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n".encode())
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(COMFY + "/upload/image", data=b"".join(parts),
                                 headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary}, method="POST")
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
    name = r.get("name"); sub = r.get("subfolder", "")
    return name if not sub else f"{sub}/{name}"


# ---- 图2/图3 子图展开注入（与主图1319同构，但 condition 串接前层） ----
def _inject_ref(wf, img_node_id, scale_node_id, prev_pos, prev_neg, new_pos_id, new_neg_id, up_id, encode_id, extra):
    """展开一个 Reference Conditioning 子图：
       scale(1315/1316 缩放) <- img_node(LoadImage)
       encode(VAEEncode)    <- scale, vae
       pos(ReferenceLatent) <- prev_pos(conditioning), encode(latent)
       neg(ReferenceLatent) <- prev_neg(conditioning), encode(latent)
       extra 里已铺好的 scale 节点需要 image 连回 img_node"""
    # 缩放节点（复用模板里绕过存在但 API 无的 1315/1316 —— 直接内置）
    wf[scale_node_id] = {"inputs": {"upscale_method": "nearest-exact", "megapixels": extra["mp"],
                                    "resolution_steps": 1, "image": [img_node_id, 0]},
                         "class_type": "LayerUtility: ImageScaleByAspectRatio V2" if extra.get("byaspect") else "ImageScaleToTotalPixels",
                         "_meta": {"title": "图%d缩放" % extra["n"]}}
    # VAEEncode
    wf[encode_id] = {"inputs": {"pixels": [scale_node_id, 0], "vae": [VAE, 0]}, "class_type": "VAEEncode",
                     "_meta": {"title": "图%d编码" % extra["n"]}}
    # pos / neg ReferenceLatent
    wf[new_pos_id] = {"inputs": {"conditioning": prev_pos, "latent": [encode_id, 0]}, "class_type": "ReferenceLatent",
                      "_meta": {"title": "图%d positive" % extra["n"]}}
    wf[new_neg_id] = {"inputs": {"conditioning": prev_neg, "latent": [encode_id, 0]}, "class_type": "ReferenceLatent",
                      "_meta": {"title": "图%d negative" % extra["n"]}}
    return [new_pos_id, 0], [new_neg_id, 0]


def build(prompt, w, h, img1name, img2name, img3name, name, lora_specs):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    if prompt is not None:
        wf[P_PROMPT]["inputs"]["value"] = prompt          # PrimitiveStringMultiline → value
    if w is not None and h is not None:
        wf[P_RES]["inputs"]["width"] = w
        wf[P_RES]["inputs"]["height"] = h
    if img1name:
        wf[P_IMG1]["inputs"]["image"] = img1name

    # ---- 多图注入（主图 ref. 起始 = KSampler 直连的 1319:741/739） ----
    # 主图 positive/negative 参考就是 KSampler 当前接的
    pos_ref = wf[KS]["inputs"]["positive"]
    neg_ref = wf[KS]["inputs"]["negative"]

    # 用每个 image 传入自动铺开：缩放节点用 ImageScaleToTotalPixels（1.25MP, 同主图1310）
    # 注：模板里 图2/图3 缩放用的 LayerUtility ImageScaleByAspectRatio，这里用 ImageScaleToTotalPixels 等效。
    counter = {"n": 0}
    def add_ref(imgname, prev_pos, prev_neg):
        if not imgname:
            return prev_pos, prev_neg
        counter["n"] += 1
        n = counter["n"]
        uid = f"img{n}_load"
        # 该图的 LoadImage 节点（避开与模板主图1326冲突；图2/3 用新id而不是 1327/1328 以避免和模板潜在冲突）
        wf[uid] = {"inputs": {"image": imgname}, "class_type": "LoadImage", "_meta": {"title": "图%d" % (n+1)}}
        scale_id = f"img{n}_scale"
        encode_id = f"img{n}_enc"
        pos_id = f"img{n}_pos"
        neg_id = f"img{n}_neg"
        wf[scale_id] = {"inputs": {"upscale_method": "nearest-exact", "megapixels": 1.25, "resolution_steps": 1,
                                   "image": [uid, 0]}, "class_type": "ImageScaleToTotalPixels", "_meta": {"title": "图%d缩放" % (n+1)}}
        wf[encode_id] = {"inputs": {"pixels": [scale_id, 0], "vae": [VAE, 0]}, "class_type": "VAEEncode", "_meta": {"title": "图%d编码" % (n+1)}}
        wf[pos_id] = {"inputs": {"conditioning": prev_pos, "latent": [encode_id, 0]}, "class_type": "ReferenceLatent", "_meta": {"title": "图%d positive" % (n+1)}}
        wf[neg_id] = {"inputs": {"conditioning": prev_neg, "latent": [encode_id, 0]}, "class_type": "ReferenceLatent", "_meta": {"title": "图%d negative" % (n+1)}}
        return [pos_id, 0], [neg_id, 0]

    # 图2 → 图3 依次串接（图2 接主图，图3 接图2）
    pos_ref, neg_ref = add_ref(img2name, pos_ref, neg_ref)
    pos_ref, neg_ref = add_ref(img3name, pos_ref, neg_ref)
    wf[KS]["inputs"]["positive"] = pos_ref
    wf[KS]["inputs"]["negative"] = neg_ref

    # Lora + 保存名
    node = wf[P_LORA]
    raw = node["inputs"].get("loras")
    loras = raw["__value__"] if isinstance(raw, dict) and "__value__" in raw else (raw or [])
    node["inputs"]["loras"] = comfy_submit.apply_lora_specs(loras, lora_specs)
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[P_PREFIX]["inputs"]["filename_prefix"] = f"{today}/{safe}"
    return wf


def main():
    p = argparse.ArgumentParser(description="flux2 正常编辑引子（flux2-klein 整图/多参考编辑，最多3图）")
    p.add_argument("--img1", help="图1：主图（本地路径）")
    p.add_argument("--img2", help="图2：可选参考图（本地路径）")
    p.add_argument("--img3", help="图3：可选参考图（本地路径）")
    p.add_argument("--prompt", help="编辑内容（图1人物换成... / 换上图2服装...）")
    p.add_argument("--w", type=int, help="分辨率宽（动态1.2~1.6M，图多则低，贴参考图比例）")
    p.add_argument("--h", type=int, help="分辨率高")
    p.add_argument("--name", default="output")
    p.add_argument("--loras", action="append", default=None, help="可重复：NAME:STRENGTH:on|off，只改点名条目")
    args = p.parse_args()
    img1 = _upload_image(args.img1) if args.img1 else None
    img2 = _upload_image(args.img2) if args.img2 else None
    img3 = _upload_image(args.img3) if args.img3 else None
    wf = build(args.prompt, args.w, args.h, img1, img2, img3, args.name, args.loras)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
