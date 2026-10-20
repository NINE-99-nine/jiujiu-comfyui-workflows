# jiujiu-comfyui-workflows

面向 **ComfyUI 的自动化工作流库**：每个 workflow 是一个子技能目录，含 **API 模板（json）+ 引子脚本（py）**，统一通过 `execution/comfy_submit.py` 递交，把出图/配音黑盒化。

> 💡 **核心设计：引子黑盒** —— 每个 workflow 一个与模板同 basename 的 `_api.py`。你只传参数，脚本自动完成「上传图片 → 内存拼 API（不落盘）→ 递交 → 校验 `node_errors` → 轮询 → 拷成品 → 返回一行 JSON」。不用打开界面拼节点，也不占用对话上下文。

## 能干什么

- **出图**：anima / krea2 / zimage / moss / qwen_image2.1 五条生图线，覆盖动漫向、写实向、海报排版、多人群像
- **改图**：flux2 局部编辑（SAM3.1 遮罩 → 裁剪放大 → 重绘 → 拼回）与整图 / 多参考融合
- **配音**：IndexTTS-2 与 VoxCPM，含音色克隆
- **提示词库**：`prompt-library/` 按模型分目录，每条风格都带实出样图

## 工作流列表

| 工作流 | 用途 | 引子脚本 |
|---|---|---|
| **anima** | 🎨 动漫向生图（快速 / 正常两模式，正常带 SeedVR2 放大） | `anima_quick_template.py` · `anima_normal_template.py` |
| **krea2** | 🎨 krea2 生图（Qwen3VL 自然语言 CLIP，×1.5 放大） | `krea2汇总_api.py` |
| **zimage** | 🎨 Z-Image-Turbo 生图（无二次放大） | `zimage_full_template.py` |
| **moss** | 🎨 MOSS-Image 生图（6 条 LoRA 堆 + SeedVR2；原生支持 JSON 布局控制多人物位置） | `moss_api.py` |
| **qwen_image2.1** | 🎨 人设卡片 / 设计字海报（多图参考） | `qwen_image2.1汇总_api.py` |
| **flux2图像放大编辑** | 🖼️ 局部编辑（遮罩 → 裁剪放大 → 重绘 → 拼回） | `flux2图像放大编辑_api.py` |
| **flux2图像正常编辑** | 🖼️ 整图 / 多参考编辑（最多 3 图融合） | `flux2图像正常编辑_api.py` |
| **indextts2** | 🎙️ IndexTTS-2 配音 | `🌈 IndexTTS-2 integration-API.py` |
| **voxcpm** | 🎙️ VoxCPM 配音（音色克隆） | `voxcpm全能工作流.py` |
| **pr-audio-dubbing** | 🎬 Premiere 工程配音替换链路 | `pr_audio_dub.py` · `conv_wav.py` |

## 快速开始

```bash
git clone <本仓库>
cd jiujiu-comfyui-workflows

# 1. 建配置（唯一必做的一步）
cp config.example.yaml config.yaml
#    然后改 comfyui.url 指向你的 ComfyUI

# 2. 跑一个例子
python workflows/anima/anima_quick_template.py \
  --prompt "masterpiece, best quality, 1girl, silver hair, red eyes, standing in a library" \
  --w 864 --h 1280 --name my_image
```

返回一行 JSON，含成品绝对路径。

## 配置

**全库只有一个配置入口**：根目录的 `config.yaml`（由 `config.example.yaml` 复制而来）。所有引子都从它取值，不用改任何 `.py`。

| 键 | 作用 | 默认 |
|---|---|---|
| `comfyui.url` | ComfyUI 基址（含端口） | `http://127.0.0.1:8188` |
| `comfyui.input_dir` | 往 ComfyUI 塞图时的 input 目录 | 空（不指定） |
| `comfyui.models_dir` | ComfyUI models 目录 | 空（不指定） |
| `paths.work_root` | 成品拷到这里，按 `_work/<引子名>/` 分目录 | 仓库下 `_work/` |
| `network.proxy` | 下载模型 / 访问外网用的代理 | 空（直连） |
| `misc.serve_port` | `scripts/serve_wf.py` 的端口 | `8765` |

也可以用环境变量覆盖（优先级更高）：

```bash
COMFYUI_URL / COMFYUI_INPUT_DIR / COMFYUI_MODELS_DIR
COMFYUI_WORK_ROOT / COMFYUI_PROXY / COMFYUI_SERVE_PORT
```

> 配置解析是内置的极简 YAML，**不依赖 PyYAML**：只认「两层 `key: value` + `#` 注释」，值里避免出现 `#`。

## 目录结构

```
jiujiu-comfyui-workflows/
├── config.example.yaml     ← 配置模板（复制成 config.yaml）
├── SKILL.md                ← 完整使用手册（含各工作流细则，比本文件详细）
├── NEW_WORKFLOW_GUIDE.md   ← 新增工作流 SOP
├── execution/              ← 统一递交引擎
│   ├── comfy_submit.py     ← 递交 / 校验 / 轮询 / 拷成品
│   ├── env.py              ← 配置层（环境变量 > config.yaml > 默认）
│   └── EXECUTION.md        ← 递交链路与排障
├── workflows/              ← 一个工作流一个子目录
│   └── <名>/
│       ├── <名>_api.json   ← API 模板（引子读这份）
│       ├── <名>.json       ← UI 版（人看 / 备份，引子不读）
│       ├── <名>_api.py     ← 引子（你调用的就是它）
│       ├── guide.md        ← 该工作流的使用守则
│       └── prompting.md    ← 该模型的提示词写法（部分工作流有）
├── prompt-library/         ← 提示词词汇库，按模型分目录
│   └── <模型>/
│       ├── 01_xxx.md       ← 风格条目（骨架 + 参数 + 易错点）
│       └── samples/        ← 该风格的实出样图

├── references/             ← 环境与排障笔记
└── scripts/                ← 小工具（CORS 服务器 / LoRA 元数据读取）
```

## 两文件边界（重要）

每个工作流都有**两个 json**，职责严格分开：

- **`<名>_api.json`** —— API 格式（无 `nodes/links`）。**引子只会读这份**（按「同 basename + `.json`」找）。
- **`<名>.json`** —— UI 版完整 LiteGraph 格式。**只供人看、备份、或部署参考**，引子物理上读不到。

所以日常出图链路上没有任何 UI 版的开销；只有你需要排查界面本身时才去动它。

## 提示词库

`prompt-library/<模型>/` 是按模型分的**词汇库**，不是教程：

- 每个 `NN_风格名.md` = 一套风格的骨架 + 参数 + 易错点
- `samples/` 里是对应的实出样图，README 有索引表
- 用法：按目标模型进目录，选风格，抄骨架改内容

多人物 / 多元素的图，`prompt-library/moss/01_多人图提示词.md` 有基于 bbox 的 JSON 布局写法，比堆形容词可靠得多。

## 模型（不在仓库内）

工作流依赖的模型动辄数 GB，**不打包**，需自行下载后挂进 ComfyUI 的 `models/`。各子技能的 `guide.md` 写明了需要哪些、放哪个子目录。常见模型族：

- SAM3.1（flux2 遮罩识别）
- flux2-klein 9B（编辑）
- qwen3vl / Qwen3 clip
- flux2 / wan2.1 VAE
- krea2 turbo、zimage、anima 底模
- MOSS-Image 及配套 LoRA / SeedVR2

## 环境要求

- **ComfyUI** 本地运行（默认 `http://127.0.0.1:8188`）
- **GPU**：工作流针对 **Intel Arc / XPU** 调优（含 int8 / convrot 量化），NVIDIA 亦可跑（去掉 XPU 专用节点）
- **Python 3.11+**（引子脚本）
- **ffmpeg**：只有音视频相关功能需要，其余功能不装也能正常用

## 排障

| 现象 | 看哪里 |
|---|---|
| 连不上 / `node_errors` 非空 | `execution/EXECUTION.md` |
| 自定义节点加载失败 | `references/comfyui-custom-node-load-failure.md` |
| 桌面版路径漂移、输出跑到 C 盘 | `references/comfy-desktop-ops.md` |
| 输出目录不对 | 引子每次都会查 `/system_stats` 的 `--output-directory`，漂移会在日志里体现 |

## License

MIT
