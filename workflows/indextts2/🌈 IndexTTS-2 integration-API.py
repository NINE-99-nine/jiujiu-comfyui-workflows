# -*- coding: utf-8 -*-
# ============ 🌈 IndexTTS-2 integration-API.py · IndexTTS-2 引子（黑盒，agent 只传参数） ============
# 与 🌈 IndexTTS-2 integration-API.json 同 basename → 自动配对。输出为音频。
# 用法（台词来源二选一，不可同时给）：
#   短台词：python "🌈 IndexTTS-2 integration-API.py" --text "台词" [--name 名字]
#   长/含引号：python "🌈 IndexTTS-2 integration-API.py" --text-file 台词.txt [--name 名字]
# 只输出一行 JSON：{"kind":"audio","prompt_id":…,"file":…}
# ⚠️ 台词含英文双引号（对白引语/书名等）时，shell 传参遇内嵌双引号会截断参数
#    → 多段台词、含引号/换行的台词一律走 --text-file（从 UTF-8 文件原样读取）。

import argparse, json, os, sys, datetime, re
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_suffix(".json")
P_TEXT, P_PREFIX = "65", "137"          # 65=文本输入(value), 137=SaveAudio; 82 断链勿删


def load_text(args):
    """台词来源：--text 直传（短）或 --text-file 读文件（长/含引号），二者互斥。"""
    if args.text_file:
        path = Path(args.text_file).expanduser()
        if not path.is_file():
            print(f"[IndexTTS-2引子] 台词文件不存在或不是文件：{path}", file=sys.stderr)
            sys.exit(2)
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            print(f"[IndexTTS-2引子] 台词文件为空：{path}", file=sys.stderr)
            sys.exit(2)
        return text
    text = (args.text or "").strip()
    if not text:
        print("[IndexTTS-2引子] --text 内容为空", file=sys.stderr)
        sys.exit(2)
    return text


def build(text, name):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    wf[P_TEXT]["inputs"]["value"] = text              # PrimitiveStringMultiline → value
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[P_PREFIX]["inputs"]["filename_prefix"] = f"audio/{today}/{safe}"
    return wf


def main():
    p = argparse.ArgumentParser(description="IndexTTS-2 配音引子（输出音频，narrator=none 需角色标签）")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="台词（短句直传；多角色用 [角色名] 分段，必须带标签）")
    src.add_argument("--text-file", dest="text_file",
                     help="台词文件路径（UTF-8；多段台词/含引号换行一律用这个，避免 shell 截断）")
    p.add_argument("--name", default="output")
    args = p.parse_args()
    wf = build(load_text(args), args.name)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
