# -*- coding: utf-8 -*-
# ============ zimage_full_template.py · z image 引子（黑盒，agent 只传参数） ============
# 与 zimage_full_template.json 同 basename → 自动配对。
# 用法（提示词来源二选一，不可同时给）：
#   短提示词：python zimage_full_template.py --prompt "…" [--w 768 --h 1024 --name 名字 --loras 名:强度:on]
#   长/含引号：python zimage_full_template.py --prompt-file 提示词.txt [同上参数]
# 只输出一行 JSON：{"kind":"image","prompt_id":…,"file":…,"size":…}
# ⚠️ 提示词含英文双引号（画面文字须引号标注）时，shell 传参遇内嵌双引号会截断参数
#    → 长提示词、含引号/多段的提示词一律走 --prompt-file（从 UTF-8 文件原样读取）。

import argparse, json, os, sys, datetime, re
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_suffix(".json")
P_PROMPT, P_RES, P_PREFIX, P_LORA = "636", "629", "35", "628"


def load_prompt(args):
    """提示词来源：--prompt 直传（短）或 --prompt-file 读文件（长/含引号），二者互斥。"""
    if args.prompt_file:
        path = Path(args.prompt_file).expanduser()
        if not path.is_file():
            print(f"[zimage引子] 提示词文件不存在或不是文件：{path}", file=sys.stderr)
            sys.exit(2)
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            print(f"[zimage引子] 提示词文件为空：{path}", file=sys.stderr)
            sys.exit(2)
        return text
    text = (args.prompt or "").strip()
    if not text:
        print("[zimage引子] --prompt 内容为空", file=sys.stderr)
        sys.exit(2)
    return text


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
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt", help="四段式提示词（全英文；短提示词直传）")
    src.add_argument("--prompt-file", dest="prompt_file",
                     help="提示词文件路径（UTF-8；长文/含英文引号/多段换行一律用这个，避免 shell 截断）")
    p.add_argument("--w", type=int, default=768, help="最终宽（8 的倍数）")
    p.add_argument("--h", type=int, default=1024, help="最终高（8 的倍数）")
    p.add_argument("--name", default="output")
    p.add_argument("--loras", action="append", default=None, help="可重复：NAME:STRENGTH:on|off，只改点名条目")
    args = p.parse_args()
    wf = build(load_prompt(args), args.w, args.h, args.name, args.loras)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
