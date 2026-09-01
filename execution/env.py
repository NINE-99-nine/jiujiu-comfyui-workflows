# -*- coding: utf-8 -*-
# ============ env.py · 环境脚本 ============
# 通用配置层：所有工作流共享。普通用户无需改动即可运行。
# 如需自定义（不同 ComfyUI 端口 / 特殊模型目录），通过环境变量或下方常量覆盖即可。
#
# 可用环境变量（优先级高于下方默认值）：
#   COMFYUI_URL        ComfyUI 基址（含端口），默认 http://127.0.0.1:8188
#   COMFYUI_INPUT_DIR  输入目录（可选）
#   COMFYUI_MODELS_DIR 模型目录（可选）
#   COMFYUI_WORK_ROOT  成品拷贝工作区目录（可选）

import json, os, urllib.request

# --- ComfyUI 基址（含端口）---
COMFY_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")

# --- 模型/输入目录（通常留空即可，工作流通过 ComfyUI 模型路径配置挂载）---
INPUT_DIR = os.environ.get("COMFYUI_INPUT_DIR", "")     # 可填 ComfyUI 的 input 目录
MODELS_DIR = os.environ.get("COMFYUI_MODELS_DIR", "")   # 可填 ComfyUI 的 models 目录

# --- 成品拷贝工作区（相对当前目录的 _work，或自定义）---
WORK_ROOT = os.environ.get("COMFYUI_WORK_ROOT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_work"))


def comfy_output_dir():
    """从 /system_stats 读 ComfyUI 运行时实际 --output-directory（避免写入系统盘）。"""
    try:
        raw = json.loads(urllib.request.urlopen(COMFY_URL + "/system_stats", timeout=10).read().decode("utf-8"))
    except Exception as e:
        raise SystemExit("无法连 ComfyUI /system_stats: %s" % e)
    argv = raw.get("system", {}).get("argv", [])
    for i, a in enumerate(argv):
        if a == "--output-directory" and i + 1 < len(argv):
            return argv[i + 1]
    return ""
