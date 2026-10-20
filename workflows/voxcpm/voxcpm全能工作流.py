# -*- coding: utf-8 -*-
# ============ voxcpm全能工作流.py · VoxCPM 配音引子（黑盒，agent 只传参数） ============
# 与 voxcpm全能工作流_API.json 同目录同 basename(前缀) → 自动配对。输出为音频。
# 用法：
#   python voxcpm全能工作流.py --text "台词" [--mode 极致克隆] [--voice voices/x.wav] [--lora x.safetensors] [--seed -1] [--name 名字]
#   --mode 可控克隆 时用 --control 指定口吻。
# 只输出一行 JSON：{"kind":"audio","prompt_id":…,"file":…}

import argparse, json, os, sys, random
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(_here.parents[2]))
from execution import comfy_submit

TEMPLATE = _here.with_name("voxcpm全能工作流_API.json")
P_GEN, P_VOICE = "4", "33"


def build(text, control, lora, voice, seed, name, mode):
    wf = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    g = wf[P_GEN]["inputs"]
    g["work_mode"] = mode
    g["target_text"] = text
    if control is not None and mode == "可控克隆":
        g["control_instruction"] = control
    if lora is not None:
        g["lora_name"] = lora
    if voice is not None:
        wf[P_VOICE]["inputs"]["voice_name"] = voice
    if seed is not None:
        g["seed"] = random.randint(1, 2 ** 50) if seed == -1 else seed
    return wf


def main():
    p = argparse.ArgumentParser(description="VoxCPM 配音引子（API 直连，输出音频）")
    p.add_argument("--text", required=True, help="要生成的台词")
    p.add_argument("--mode", default="极致克隆", choices=["极致克隆", "可控克隆"], help="模式：极致克隆(默认)/可控克隆")
    p.add_argument("--control", default=None, help="口吻：仅 --mode 可控克隆 时生效")
    p.add_argument("--lora", default=None, help="LoRA 权名（默认保留模板值）")
    p.add_argument("--voice", default=None, help="参考音频（如 voices/守岸人.wav）")
    p.add_argument("--seed", type=int, default=None, help="-1 随机 / 具体值固定；缺省用模板值")
    p.add_argument("--name", default="output")
    args = p.parse_args()
    wf = build(args.text, args.control, args.lora, args.voice, args.seed, args.name, args.mode)
    comfy_submit.submit(wf, name=args.name, out_subdir=_here.stem, seed=None)


if __name__ == "__main__":
    main()
