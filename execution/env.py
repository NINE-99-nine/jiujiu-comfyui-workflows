# -*- coding: utf-8 -*-
# ============ env.py · 统一配置层 ============
# 这是全库唯一的环境入口。所有工作流脚本从这里取值，不再各自写死路径和端口。
#
# 取值优先级：环境变量  >  config.yaml  >  本文件内置默认值
# 换机器 / 换端口 / 换目录时，改根目录的 config.yaml 就够了（它是本机配置，不进 git）。
#
# 零依赖：自带一个只认「两层 key: value」的极简 YAML 解析器，不需要装 PyYAML。
#   支持：  区块: / 两空格缩进的子键 / # 注释 / 值加不加引号都行
#   不支持：列表、多行字符串、锚点、行内注释（值里出现 # 会被当注释截断，路径里请避开 #）

import json, os, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config.yaml"

# --- 内置默认值（config.yaml 缺失时用这套，保证 clone 下来就能跑）---
_DEFAULTS = {
    "comfyui": {"url": "http://127.0.0.1:8188", "input_dir": "", "models_dir": ""},
    "paths": {"work_root": str(ROOT / "_work")},
    "network": {"proxy": ""},
    "misc": {"serve_port": "8765"},
}

# --- 环境变量覆盖表：变量名 -> (区块, 键) ---
_ENV_MAP = {
    "COMFYUI_URL": ("comfyui", "url"),
    "COMFYUI_INPUT_DIR": ("comfyui", "input_dir"),
    "COMFYUI_MODELS_DIR": ("comfyui", "models_dir"),
    "COMFYUI_WORK_ROOT": ("paths", "work_root"),
    "COMFYUI_PROXY": ("network", "proxy"),
    "COMFYUI_SERVE_PORT": ("misc", "serve_port"),
}


def _parse_simple_yaml(text):
    root, cur = {}, None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip())
        key, _, val = line.strip().partition(":")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if indent == 0:
            if val:
                root[key] = val
                cur = None
            else:
                root[key] = {}
                cur = key
        elif cur is not None:
            root[cur][key] = val
    return root


def _load():
    cfg = {sec: dict(vals) for sec, vals in _DEFAULTS.items()}
    if CONFIG_FILE.is_file():
        try:
            user = _parse_simple_yaml(CONFIG_FILE.read_text(encoding="utf-8-sig"))
        except Exception as e:
            raise SystemExit("config.yaml 读取失败：%s\n（文件位置：%s）" % (e, CONFIG_FILE))
        for sec, vals in user.items():
            if isinstance(vals, dict):
                cfg.setdefault(sec, {}).update({k2: v2 for k2, v2 in vals.items() if v2 != ""})
    for env_key, (sec, key) in _ENV_MAP.items():
        v = os.environ.get(env_key)
        if v:
            cfg.setdefault(sec, {})[key] = v
    return cfg


CFG = _load()

# --- 对外常量（保持老名字，现有脚本无需改动）---
COMFY_URL = CFG["comfyui"]["url"].rstrip("/")
INPUT_DIR = CFG["comfyui"]["input_dir"]
MODELS_DIR = CFG["comfyui"]["models_dir"]
WORK_ROOT = CFG["paths"]["work_root"]
PROXY = CFG["network"]["proxy"]
SERVE_PORT = int(CFG["misc"].get("serve_port") or 8765)


def comfy_output_dir():
    """从 /system_stats 读 ComfyUI 运行时实际 --output-directory（防 C 盘漂移）。"""
    try:
        raw = json.loads(urllib.request.urlopen(COMFY_URL + "/system_stats", timeout=10).read().decode("utf-8"))
    except Exception as e:
        raise SystemExit("无法连 ComfyUI %s/system_stats: %s\n（检查 config.yaml 的 comfyui.url，或 ComfyUI 是否已启动）"
                         % (COMFY_URL, e))
    argv = raw.get("system", {}).get("argv", [])
    for i, a in enumerate(argv):
        if a == "--output-directory" and i + 1 < len(argv):
            return argv[i + 1]
    return ""
