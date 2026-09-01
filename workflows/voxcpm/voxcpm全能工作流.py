# -*- coding: utf-8 -*-
# ============ voxcpm全能工作流.py · VoxCPM 配音引子（黑盒，agent 只传参数） ============
# 与 voxcpm全能工作流.json 同 basename → 自动配对。输出为音频。
# 用法：
#   python voxcpm全能工作流.py --text "台词" [--control "口吻" --lora xxx.safetensors --voice voices/x.mp3 --seed -1 --name 名字]
# 只输出一行 JSON：{"kind":"audio","prompt_id":…,"file":…}

import argparse, json, os, sys, datetime, re, random
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_suffix(".json")
P_GEN, P_VOICE, P_PREFIX = "4", "33", "3"


def build(text, control, lora, voice, seed, name):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    g = wf[P_GEN]["inputs"]
    g["target_text"] = text
    if control is not None:
        g["control_instruction"] = control
    if lora is not None:
        g["lora_name"] = lora
    if voice is not None:
        wf[P_VOICE]["inputs"]["voice_name"] = voice
    if seed is not None:
        g["seed"] = random.randint(1, 2 ** 50) if seed == -1 else seed
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name) or "output"
    today = datetime.date.today().strftime("%Y-%m-%d")
    wf[P_PREFIX]["inputs"]["filename_prefix"] = f"audio/{today}/{safe}"
    return wf


def main():
    p = argparse.ArgumentParser(description="VoxCPM 配音引子（API 直连，输出音频）")
    p.add_argument("--text", required=True, help="要生成的台词（可含多角色分段）")
    p.add_argument("--control", default=None, help="口吻：中文描述声音特征/情绪")
    p.add_argument("--lora", default=None, help="LoRA 权名（默认保留模板值）")
    p.add_argument("--voice", default=None, help="参考音频（如 voices/铅玻璃.mp3）")
    p.add_argument("--seed", type=int, default=None, help="-1 随机 / 具体值固定；缺省用模板值")
    p.add_argument("--name", default="output")
    args = p.parse_args()
    wf = build(args.text, args.control, args.lora, args.voice, args.seed, args.name)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
