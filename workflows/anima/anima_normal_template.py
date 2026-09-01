# -*- coding: utf-8 -*-
# ============ anima_normal_template.py · anima 正常模式引子（黑盒，agent 只传参数） ============
# 与 anima_normal_template.json 同 basename → 自动配对。
# 用法：
#   python anima_normal_template.py --prompt "…" [--w 1024 --h 1536 --name 名字 --seedvr2-res 1600 --loras 名:强度:on]
# 只输出一行 JSON。正常模式走 seedvr2 放大链，最终分辨率 = [344].resolution + 初始[19]。
# anima 无 Seed 节点（靠分辨率破缓存）。

import argparse, json, os, sys, datetime, re
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_suffix(".json")
P_PROMPT, P_RES, P_PREFIX, P_LORA, P_SEEDVR2 = "23", "19", "40", "52", "344"


def build(prompt, w, h, name, seedvr2_res, lora_specs):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    wf[P_PROMPT]["inputs"]["string"] = prompt
    wf[P_RES]["inputs"]["width"] = w
    wf[P_RES]["inputs"]["height"] = h
    if seedvr2_res is not None:
        wf[P_SEEDVR2]["inputs"]["resolution"] = seedvr2_res
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[P_PREFIX]["inputs"]["filename_prefix"] = f"{today}/{safe}"
    node = wf[P_LORA]
    raw = node["inputs"].get("loras")
    loras = raw["__value__"] if isinstance(raw, dict) and "__value__" in raw else (raw or [])
    node["inputs"]["loras"] = comfy_submit.apply_lora_specs(loras, lora_specs)
    return wf


def main():
    p = argparse.ArgumentParser(description="anima 正常模式引子（seedvr2 放大链）")
    p.add_argument("--prompt", required=True, help="人设二提示词（纯英文，六层结构）")
    p.add_argument("--w", type=int, default=1024, help="初始宽（8 的倍数）")
    p.add_argument("--h", type=int, default=1536, help="初始高（8 的倍数）")
    p.add_argument("--name", default="output")
    p.add_argument("--seedvr2-res", type=int, default=None, help="[344] seedvr2 resolution（默认 1600，决定放大倍率）")
    p.add_argument("--loras", action="append", default=None, help="可重复：NAME:STRENGTH:on|off，只改点名条目")
    args = p.parse_args()
    wf = build(args.prompt, args.w, args.h, args.name, args.seedvr2_res, args.loras)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
