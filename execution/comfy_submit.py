# -*- coding: utf-8 -*-
# ============ comfy_submit.py · 通用 API 递交执行器 ============
# 唯一真正碰 ComfyUI 的件：提交 → 校验 node_errors → 轮询 → 拷贝 → 打印一行 JSON。
# agent 不读本文件：只通过引子脚本调用 submit()，标准输出即为最终 JSON。

import json, time, urllib.request, os, sys, shutil, struct, datetime, random, re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 让同目录 env 可导入
import env

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def _get(url, timeout=30):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _post(url, payload, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _unwrap(node):
    """把前端序列化的 {\"__value__\": X} 包装解开为裸值（如 loras），服务端才认。"""
    ins = node.get("inputs", {})
    for k, v in list(ins.items()):
        if isinstance(v, dict) and "__value__" in v:
            ins[k] = v["__value__"]
    return node


def _png_size(path):
    try:
        with open(path, "rb") as f:
            hdr = f.read(26)
        if hdr[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", hdr[16:24])
            return "%dx%d" % (w, h)
    except Exception:
        pass
    return ""


def apply_lora_specs(loras, specs):
    """只改点名条目的 active/strength；绝不增删、绝不误开其他。返回新 list。"""
    loras = [dict(x) for x in loras]
    if specs:
        for spec in specs:
            parts = spec.split(":")
            name = parts[0]
            strength = float(parts[1]) if len(parts) > 1 and parts[1] else None
            on = parts[2].lower() in ("on", "1", "true") if len(parts) > 2 else None
            for e in loras:
                if e["name"] == name:
                    if strength is not None:
                        e["strength"] = strength
                        e["clipStrength"] = strength
                    if on is not None:
                        e["active"] = bool(on)
                    break
            else:
                print("WARN: lora 不存在(忽略,不新增): %s" % name, file=sys.stderr)
    return loras


def submit(api_dict, name, out_subdir, seed=-1, max_poll=240):
    """提交若干 API dict → 轮询 → 拷贝到 WORK_ROOT/<out_subdir>/<name>_<date>.<ext>，打印 JSON。"""
    wf = {k: _unwrap(v) for k, v in api_dict.items()}

    # seed：-1 → 随机；具体值 → 固定；None → 用模板原值
    if seed is not None:
        seed_val = random.randint(1, 10 ** 15) if seed == -1 else seed
        for node in wf.values():
            ins = node.get("inputs", {})
            if node.get("class_type", "").startswith("Seed") and "seed" in ins:
                # seedvr2 等节点的 seed 字段上限是 2^32（4294967295），15 位随机数会爆。
                # 对超出范围的 seed 钳制到合法区间（seedvr2 节点 class_type / 节点含 SeedVR）。
                if node.get("class_type", "").startswith("SeedVR") and seed_val > 4294967295:
                    ins["seed"] = seed_val % 4294967296
                else:
                    ins["seed"] = seed_val

    resp = _post(env.COMFY_URL + "/prompt", {"prompt": wf})
    if resp.get("node_errors"):
        raise SystemExit("node_errors: " + json.dumps(resp["node_errors"], ensure_ascii=False)[:600])
    pid = resp["prompt_id"]

    # 轮询：只关心状态与最终输出，不打印中间体
    hist = None
    for _ in range(max_poll):
        time.sleep(3)
        try:
            hist = _get(f"{env.COMFY_URL}/history/{pid}")[pid]
        except Exception:
            continue
        st = hist.get("status", {})
        if st.get("completed"):
            break
        if st.get("status_str") in ("error", "error_internal"):
            raise SystemExit("exec error: " + json.dumps(hist, ensure_ascii=False)[:500])
    else:
        raise SystemExit("poll timeout")

    # 定位成品：优先 image(type=output)，其次 audio（SaveAudio）
    file = None
    kind = None
    for val in hist.get("outputs", {}).values():
        for im in val.get("images", []):
            if im.get("type") == "output":
                file, kind = im, "image"
                break
        if file:
            break
        if val.get("audio"):
            a = val["audio"][0]
            if not a.get("type") or a.get("type") == "output":
                file, kind = a, "audio"
                break
    if not file:
        raise SystemExit("no output (image/audio) found")

    outdir = env.comfy_output_dir() or ""
    parts = [p for p in [file.get("subfolder", ""), file["filename"]] if p]
    src = os.path.join(outdir, *parts)

    dst_dir = os.path.join(env.WORK_ROOT, out_subdir)
    os.makedirs(dst_dir, exist_ok=True)
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    date = datetime.date.today().strftime("%Y-%m-%d")
    ext = os.path.splitext(src)[1] or (".png" if kind == "image" else ".wav")
    dst = os.path.join(dst_dir, f"{safe}_{date}{ext}")
    shutil.copy2(src, dst)

    res = {"kind": kind, "prompt_id": pid, "file": dst}
    if kind == "image":
        res["size"] = _png_size(dst)
    print(json.dumps(res, ensure_ascii=False))
    return res
