# -*- coding: utf-8 -*-
# ============ zimage_full_template.py · z image 引子（黑盒，agent 只传参数） ============
# 与 zimage_full_template.json 同 basename → 自动配对。
# 用法：
#   python zimage_full_template.py --prompt "…" [--w 768 --h 1024 --name 名字 --loras 名:强度:on]
# 只输出一行 JSON：{"kind":"image","prompt_id":…,"file":…,"size":…}

import argparse, json, os, sys, datetime, re
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_suffix(".json")
P_PROMPT, P_RES, P_PREFIX, P_LORA = "636", "629", "35", "628"


def build(prompt, w, h, name, lora_specs):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    wf[P_PROMPT]["inputs"]["value"] = prompt          # PrimitiveStringMultiline → value
    wf[P_RES]["inputs"]["width"] = w
    wf[P_RES]["inputs"]["height"] = h
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[P_PREFIX]["inputs"]["filename_prefix"] = f"{today}/{safe}"
    node = wf[P_LORA]
    raw = node["inputs"].get("loras")
    loras = raw["__value__"] if isinstance(raw, dict) and "__value__" in raw else (raw or [])
    node["inputs"]["loras"] = comfy_submit.apply_lora_specs(loras, lora_specs)
    return wf


def main():
    p = argparse.ArgumentParser(description="z image 引子（无二次放大：629 即最终尺寸）")
    p.add_argument("--prompt", required=True, help="四段式提示词（全英文）")
    p.add_argument("--w", type=int, default=768, help="最终宽（8 的倍数）")
    p.add_argument("--h", type=int, default=1024, help="最终高（8 的倍数）")
    p.add_argument("--name", default="output")
    p.add_argument("--loras", action="append", default=None, help="可重复：NAME:STRENGTH:on|off，只改点名条目")
    args = p.parse_args()
    wf = build(args.prompt, args.w, args.h, args.name, args.loras)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
