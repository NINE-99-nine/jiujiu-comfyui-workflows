# -*- coding: utf-8 -*-
# ============ krea2汇总_api.py · krea2 引子（黑盒，agent 只传参数） ============
# 与 krea2汇总_api.json 同 basename → 自动配对。
# 用法（二选一，不可同时给）：
#   短提示词：python krea2汇总_api.py --prompt "…" [--w 672 --h 1000 --name 名字 --seed -1 --loras 名:强度:on]
#   长/含引号：python krea2汇总_api.py --prompt-file 提示词.txt [同上参数]
# 只输出一行 JSON：{"kind":"image","prompt_id":…,"file":…,"size":…}
# ⚠️ krea2 要求画面文字用英文双引号标注（如 "SELINA"），而 shell 传参遇内嵌双引号会截断参数
#    → 长提示词、含引号/多段的提示词一律走 --prompt-file（从 UTF-8 文件原样读取）。

import argparse, json, os, sys, datetime, re
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_suffix(".json")
P_PROMPT, P_RES, P_PREFIX, P_LORA = "13", "31", "24", "16"


def build(prompt, w, h, name, lora_specs):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    wf[P_PROMPT]["inputs"]["string"] = prompt
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


def load_prompt(args):
    """提示词来源：--prompt 直传（短）或 --prompt-file 读文件（长/含引号），二者互斥。"""
    if args.prompt_file:
        path = Path(args.prompt_file).expanduser()
        if not path.is_file():
            print(f"[krea2引子] 提示词文件不存在或不是文件：{path}", file=sys.stderr)
            sys.exit(2)
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            print(f"[krea2引子] 提示词文件为空：{path}", file=sys.stderr)
            sys.exit(2)
        return text
    text = (args.prompt or "").strip()
    if not text:
        print("[krea2引子] --prompt 内容为空", file=sys.stderr)
        sys.exit(2)
    return text


def main():
    p = argparse.ArgumentParser(description="krea2 引子（×1.5 放大链：最终=初始×1.5）")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt", help="人设二提示词（短提示词直传；画风质感→画面内容→构图镜头）")
    src.add_argument("--prompt-file", dest="prompt_file",
                     help="提示词文件路径（UTF-8；长文/含英文引号/多段换行一律用这个，避免 shell 截断）")
    p.add_argument("--w", type=int, default=672, help="初始宽（8 的倍数）")
    p.add_argument("--h", type=int, default=1000, help="初始高（8 的倍数）")
    p.add_argument("--name", default="output")
    p.add_argument("--seed", type=int, default=-1, help="-1 随机 / 具体值固定（模板有 Seed 节点时生效）")
    p.add_argument("--loras", action="append", default=None, help="可重复：NAME:STRENGTH:on|off，只改点名条目")
    args = p.parse_args()
    wf = build(load_prompt(args), args.w, args.h, args.name, args.loras)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=args.seed)


if __name__ == "__main__":
    main()
