# jiujiu-comfyui-workflows

一个面向 **ComfyUI 的自动化工作流库**：每个 workflow 是一个子技能目录，含 **API 模板（json）+ 引子脚本（py）**，通过 `execution/comfy_submit.py` 统一递交，黑盒化出图/配音。

> 💡 核心设计：**引子黑盒** —— 每个 workflow 一个同 basename 的 `_api.py`，脚本自动完成「上传图片 → 拼 API（不落盘）→ 递交 → 校验 → 轮询 → 拷成品 → 返回一行 JSON」。你只需传参，无需手动拼节点。

## 工作流列表

| 工作流 | 用途 | 引子脚本 |
|---|---|---|
| **anima** | 🎨 生图主力（动漫向，快速/正常两模式） | `anima_quick_template.py` / `anima_normal_template.py` |
| **krea2** | 🎨 krea2 生图（Qwen3VL 自然语言 CLIP，×1.5 放大） | `krea2汇总_api.py` |
| **zimage** | 🎨 Z-Image-Turbo 生图（无二次放大） | `zimage_full_template.py` |
| **flux2图像放大编辑** | 🖼️ flux2 局部编辑（SAM3.1 遮罩 → 裁剪放大 → 重绘 → 拼回） | `flux2图像放大编辑_api.py` |
| **flux2图像正常编辑** | 🖼️ flux2 整图/多参考编辑（最多 3 图融合） | `flux2图像正常编辑_api.py` |
| **indextts2** | 🎙️ IndexTTS-2 配音 | `🌈 IndexTTS-2 integration-API.py` |
| **voxcpm** | 🎙️ VoxCPM 配音（API 直连） | `voxcpm全能工作流.py` |

## 环境要求

- **ComfyUI**（本地运行，默认 `http://127.0.0.1:8188`）
- **Intel Arc / XPU** 或兼容的 GPU（工作流针对 XPU 优化，含 int8/convrot 量化模型）
- **Python 3.11+**（引子脚本运行环境）

## 安装

```bash
git clone <本仓库>
cd jiujiu-comfyui-workflows
```

## 配置（关键）

编辑或通过环境变量覆盖 `execution/env.py`：

```bash
# 可选环境变量
export COMFYUI_URL=http://127.0.0.1:8188          # ComfyUI 地址
export COMFYUI_WORK_ROOT=/path/to/your/_work      # 成品拷贝目录
export COMFYUI_INPUT_DIR=/path/to/comfy/input     # 可选
export COMFYUI_MODELS_DIR=/path/to/comfy/models   # 可选
```

`COMFYUI_URL` 默认 `http://127.0.0.1:8188`，改一行即可用。

## 使用（一个例子）

```bash
# anima 快速模式生图
python workflows/anima/anima_quick_template.py \
  --prompt "masterpiece, best quality, 1girl, ..." \
  --w 864 --h 1280 --name my_image

# flux2 局部编辑（换表情）
python workflows/flux2图像放大编辑/flux2图像放大编辑_api.py \
  --img1 "/path/to/portrait.png" --mask "face" \
  --prompt "change her expression to a smile" --name edit
```

每次调用自动：上传图片 → 拼 API → 递交 → 轮询 → 拷成品 → 打印一行 JSON（含成品路径）。

## 模型

工作流依赖多个模型（**不在仓库内，需自行下载**），各子技能的 `guide.md` 有说明。常见模型族：
- SAM3.1（flux2 遮罩识别）
- flux2-klein 9B（编辑）
- qwen3vl / Qwen3 clip
- flux2 / wan2.1 VAE
- krea2 turbo、zimage、anima 底模

> 模型文件路径由你的 ComfyUI `models/` 目录挂载，工作流通过相对路径引用。

## 目录结构

```
jiujiu-comfyui-workflows/
├── SKILL.md                ← 总介绍 + 使用说明
├── NEW_WORKFLOW_GUIDE.md   ← 新增子技能 SOP
├── execution/              ← 统一递交引擎（comfy_submit.py / env.py）
├── workflows/              ← 每个 ComfyUI 工作流一个子技能
│   ├── anima/  krea2/  zimage/  flux2*/  indextts2/  voxcpm/
├── html-embedding/         ← HTML 嵌字/海报样式库
├── prompt-library/         ← 提示词参考
└── references/  scripts/
```

## License

MIT
