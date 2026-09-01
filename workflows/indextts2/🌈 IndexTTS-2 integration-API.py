# -*- coding: utf-8 -*-
# ============ 🌈 IndexTTS-2 integration-API.py · IndexTTS-2 引子（黑盒，agent 只传参数） ============
# 与 🌈 IndexTTS-2 integration-API.json 同 basename → 自动配对。输出为音频。
# 用法：
#   python "🌈 IndexTTS-2 integration-API.py" --text "台词" [--name 名字]
# 只输出一行 JSON：{"kind":"audio","prompt_id":…,"file":…}

import argparse, json, os, sys, datetime, re
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_suffix(".json")
P_TEXT, P_PREFIX = "65", "137"          # 65=文本输入(value), 137=SaveAudio; 82 断链勿删


def build(text, name):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    wf[P_TEXT]["inputs"]["value"] = text              # PrimitiveStringMultiline → value
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[P_PREFIX]["inputs"]["filename_prefix"] = f"audio/{today}/{safe}"
    return wf


def main():
    p = argparse.ArgumentParser(description="IndexTTS-2 配音引子（输出音频，narrator=none 需角色标签）")
    p.add_argument("--text", required=True, help="台词（多角色用 [角色名] 分段，必须带标签）")
    p.add_argument("--name", default="output")
    args = p.parse_args()
    wf = build(args.text, args.name)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
