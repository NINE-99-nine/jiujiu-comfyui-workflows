---
name: jiujiu-comfyui-workflows
description: "用户使用 ComfyUI 工作流库核心总入口，内部高度集成，一工作流一子技能。"
version: 1.0.0
author: 作者
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [comfyui, workflow, image-generation, tts, poster, anime]
    category: creative
---

# 作者的 ComfyUI 工作流库

本技能是作者所有 ComfyUI 相关能力的**统一入口**。以**工作流**为核心组织：一个 ComfyUI 工作流 = 一个子技能文件夹（`workflows/<名>/`），含固定副本 json + 专属使用守则。所有生图/配音/海报任务从这里进入。

> ⚠️ **使用前必读**：先看本文件（总索引），再按任务类型进入对应子技能。加载子技能用 `skill_view(name='jiujiu-comfyui-workflows', file_path='workflows/<名>/guide.md')`。

## 目录结构

```
jiujiu-comfyui-workflows/
├── SKILL.md                  ← 本文件：总介绍 + 使用说明 + 环境速查
├── NEW_WORKFLOW_GUIDE.md     ← 新增子技能 SOP（先读；含"导出 API 模板→建同 basename 引子"）
├── config.yaml               ← 本机配置：端口/目录/代理（不进 git）
├── config.example.yaml       ← 配置模板（发布版只带这个）
├── release.json              ← 发布构建规则（作者工具，不进发布版）
├── workflows/                ← 每个 ComfyUI 工作流一个子技能文件夹
│   ├── anima/                ← 🎨 生图主力（动漫向；两模式：快速/正常）
│   │   ├── guide.md          ← anima 使用守则 + 提示词书写总纲（六层/NSFW/多人/角色串）
│   │   ├── anima_quick_template.json/.py  ← 快速模式 API 模板 + 引子（同 basename 配对）
│   │   ├── anima_normal_template.json/.py ← 正常模式 API 模板 + 引子（seedvr2 放大，--seedvr2-res）
│   │   ├── anima模型（副本）.json  ← 固定副本（静态，不随原件实时更新）
│   │   └── references/       ← 提示词规则 / 已验证样例 / NSFW 技巧
│   ├── zimage/               ← 🎨 Z-Image-Turbo 生图（无二次放大）
│   │   ├── guide.md          ← zimage 使用守则 + 四段式提示词指导 + 角色串加载规则
│   │   ├── zimage_full_template.json/.py ← 唯一合法 API 模板 + 引子
│   │   ├── z image.json      ← 工作流原件副本（存档参考）
│   │   └── references/       ← 提示词规则 / 已验证样例
│   ├── krea2/                ← 🎨 krea2 生图（Qwen3VL 自然语言 CLIP，×1.5 放大）
│   │   ├── guide.md          ← krea2 使用守则 +  提交方式（引子接口）
│   │   ├── prompting.md      ← 提示词总纲（画风质感→画面内容→构图镜头；**无词量硬限**，设计类可长可细；引号标文字）
│   │   ├── krea2汇总_api.json/.py   ← 唯一合法 API 模板 + 引子
│   │   └── krea2汇总.json    ← 固定副本（UI 格式）
│   ├── moss/                 ← 🎨 MOSS-Image 生图（**8 步 / cfg 1.0** ＋ **LoRA 堆 9 条**，默认只开 1 条：细节档 ＋ **放大默认关**（模板无 SeedVR2 节点，`--upscale` 时引子内存补链到短边 1440）；Caption / Layout 两种提示词）
│   │   ├── guide.md          ← 使用守则（能力边界 / 模型体量与显存 / 两份副本分工 / **两个提示词框** / 分辨率节点 154 / 采样档 / LoRA / 放大 / UI 独有分组 / 致命错误）
│   │   ├── prompting.md      ← 提示词编写（**§1 三形态判定 / §2 九要素下笔骨架 / §3 Caption 硬规则 / §4 扩写档 / §5 Tag 串 / §6 Layout / §7 bbox 保护九条 / §8 与工作流的关系 / §9 JSON 管不了的三件事 / §10 翻车对照＋自查**）
│   │   ├── moss_api.json/.py ← API 模板（**20 节点**）+ 引子（--loras / --upscale / --seedvr2-res / --list-loras）
│   │   └── moss_image.json   ← UI 副本（**34 节点 / 7 分组**，手动开图用；含提示词增强、边界框、latent 高清放大、seedvr2 四个默认旁路分组）
│   ├── qwen_image2.1/        ← 🎨 Qwen-Image 2.1 生图（**临时**；无图=文生图 / 有图=编辑，多图参考）
│   │   ├── guide.md          ← 使用守则（节点地图 / 两用开关 / 多图机制 / 引子参数 / Pitfalls）
│   │   ├── prompting.md      ← 提示词编写指南（五段骨架 / 写实vs二次元 / 编辑写法 / 文字渲染 / 翻车对照）
│   │   ├── qwen_image2.1汇总_api.json/.py ← API 模板 + 引子（同 basename 配对）
│   │   └── qwen_image2.1汇总.json ← UI 副本（测试版存档，仅供人看）
│   ├── qwenimage2.1局部放大编辑/ ← 🎨 **qwen2.1 局部放大编辑**（SAM3.1 定位遮罩 → 裁出放大 → 只改这一块 → 拼回原图；图1[8]=原图 / 英文检索词[25] / 编辑词[4] + 多图参考 --ref）
│   │   ├── guide.md          ← 使用守则（五步链路 / 节点地图 / 参数表 / 多图语义 / 提示词三件事 / Pitfalls）
│   │   ├── qwenimage2.1局部放大编辑_api.json/.py ← API 模板 + 引子（同 basename 配对）
│   │   └── qwenimage2.1局部放大编辑.json ← UI 副本（6 分组 28 节点，仅供人看）
│   ├── indextts2/            ← 🎙️ IndexTTS-2 配音（narrator=none，需 [角色名] 标签）
│   │   ├── guide.md          ← TTS 使用守则（提交方式/[65] 文本 + 角色语法）
│   │   ├── 🌈 IndexTTS-2 integration-API.json/.py ← 导出 API 模板 + 引子
│   │   ├── IndexTTS-2集成工作流.json  ← 旧 UI 副本（备用参考）
│   │   └── references/       ← 角色库清单
│   ├── voxcpm/               ← 🎙️ VoxCPM 配音（API 直连，可控克隆）
│   │   ├── guide.md          ← VoxCPM 使用守则（提交方式/默认设置/Pitfalls）
│   │   └── voxcpm全能工作流.json/.py ← API 模板副本 + 引子
│   ├── pr-audio-dubbing/     ← 📽️ PR 自动配音（音频对齐字幕，pymiere 控制 PR）
│   │   ├── guide.md          ← PR 配音使用守则（前置配置/参数/Pitfalls）
│   │   └── pr_audio_dub.py    ← 引子（--dry-run 查对照表 / 放置，只传参）
│   └── _archive/             ← 历史残留（zimage_live.json 等，不再引用）
├── execution/
│   ├── comfy_submit.py       ← 通用递交执行器（图像+音频，唯一真正碰 ComfyUI 的件）
│   ├── env.py                ← 环境脚本（换 ComfyUI 环境只改这里）
│   └── EXECUTION.md          ← 黑盒链路说明 + 两脚本职责 + 使用方式
│   ├── guide.md              ← 嵌字使用守则（流程/布局铁律/风格索引/人设图章节）
│   ├── styles/               ← ★风格库：一风格一子目录（guide.md 指导 + case.html 案例）
│   ├── references/           ← 活文档（character-tags 角色串速查/批量流程）
│   ├── scripts/              ← manga_panel.py（唯一脚本）
│   └── _archive/             ← 历史死文档（不再引用）
├── prompt-library/           ← 📚 优质提示词库（**成品范式 + 复刻资料**，非工作流操作）
│   ├── README.md             ← 分类机制：模型风格库（`<模型>/`）+ 通用内容词库
│   ├── krea2/                ← ★krea2 风格库（一风格一份 `NN_风格.md`；见其 README）
│   │   ├── README.md         ← krea2 分类机制 + 风格索引
│   │   ├── 01_巨构指导学.md   ← 巨构/砼核（超广角尺度反差，纯英文）
│   │   ├── 02_设计海报.md     ← 实验性设计/概念主视觉（十段骨架 + 6 例成品）
│   │   ├── 03_人设卡片.md     ← 日系赛璐璐人设卡片（白框贴纸 + 线条主义/色块感）
│   │   └── 04_旅行海报卡片.md ← 旅行 vlog 海报卡片（四边纹样 + 左侧文字版块 + 白框窗口）
│   ├── anima/                ← anima 风格库（01 杂志封面贴纸网点海报；见其 README）
│   ├── qwen_image2.1/        ← ★qwen_image2.1 风格库（01 立绘卡片风格编辑；见其 README）
│   ├── moss/                 ← ★MOSS-Image 提示词库（01 多人图 Scene JSON bbox 布局；见其 README）
├── scripts/
│   └── serve_wf.py           ← CORS 文件服务器（仅浏览器备用流程用）
└── references/               ← 通用环境参考（本机安装地图等）
```

## 任务类型 → 入口速查

| 任务 | 入口 |
|---|---|
| 「用 anima 画 XX」/ 正常图 / NSFW 图 / 多人图 | `workflows/anima/guide.md` |
| 「用 krea2 画 XX」/ krea2 生图 | `workflows/krea2/guide.md` |
| 「用 MOSS 画 XX」/ MOSS-Image 生图（caption / 精确文字版式；**8 步 cfg 1.0、默认一条 LoRA（细节档）、默认不放大**） | `workflows/moss/guide.md` |
| 「我要自己在 ComfyUI 里跑 MOSS」/ 看 MOSS 的 UI 结构 | `workflows/moss/moss_image.json` ＋ guide 的「§三 两份 json 的分工」「§九 UI 版独有的四个分组」 |
| 「用 z image 画 XX」（中文提示词/大宽图/巨构） | `workflows/zimage/guide.md` |
| 「用 qwen_image 2.1 画 XX」/ 拿参考图编辑（临时子技能） | `workflows/qwen_image2.1/guide.md` |
| 「qwen2.1 局部放大编辑」/ 只改原图某一块（脸/衣服/丝袜）+ 多图参考 | `workflows/qwenimage2.1局部放大编辑/guide.md` |
| 「换个画风/换个风格/换个 lora」 | `workflows/anima/guide.md` → **画风选择规则**（clarify 选择题 A/B/C…，默认 gpt-image-2） |
| 「用 IndexTTS-2 配音/念台词」 | `workflows/indextts2/guide.md` |
| 「用 VoxCPM 配音/生成语音」（API 直连，改文本即可） | `workflows/voxcpm/guide.md` |
| 「把音频导入 PR 对齐字幕/配音自动放置」 | `workflows/pr-audio-dubbing/guide.md` |
| 「找优质提示词范本 / 复刻某种风格」（巨构·设计海报·人设卡片） | `prompt-library/krea2/README.md` |
| 「找 qwen_image2.1 提示词范本 / 炫丽卡面复刻」 | `prompt-library/qwen_image2.1/README.md` |
| 提交 / 执行 / 排障 | 各工作流**引子脚本**（`workflows/<名>/<名>_api.py`，与模板同 basename 自动配对；走 `execution/comfy_submit.py` 黑盒） |
| 要接入新工作流 | `NEW_WORKFLOW_GUIDE.md` |
| XPU/补丁/性能排障 | 独立技能（不并入本库）：`comfyui-xpu-troubleshooting` 等 |

## 配置（config.yaml）

**全库只有一个环境入口**：技能根目录的 `config.yaml`。所有工作流引子都从它取值，不用改任何 `.py`。

| 键 | 作用 | 默认 |
|---|---|---|
| `comfyui.url` | ComfyUI 基址（含端口） | `htt<local_path>` |
| `comfyui.input_dir` | 往 ComfyUI 塞图时的 input 目录 | 空（不指定） |
| `comfyui.models_dir` | ComfyUI models 目录 | 空（不指定） |
| `paths.work_root` | 成品拷到这里，按 `_work/<引子名>/` 分目录 | 技能目录下 `_work/` |
| `network.proxy` | 下载模型/访问外网用的代理 | 空（直连） |
| `misc.serve_port` | `scripts/serve_wf.py` 的端口 | `8765` |

- **换机器 / 换端口 / 换目录：只改 `config.yaml`**，脚本一律不动。
- 也可用环境变量覆盖（优先级更高）：`COMFYUI_URL` / `COMFYUI_INPUT_DIR` / `COMFYUI_MODELS_DIR` / `COMFYUI_WORK_ROOT` / `COMFYUI_PROXY` / `COMFYUI_SERVE_PORT`。
- `config.yaml` 是**本机配置、不进 git**；发布版只带 `config.example.yaml`（复制成 `config.yaml` 即可用）。
- 解析器是内置的极简 YAML（零依赖，不装 PyYAML）：只认「两层 key: value + # 注释」，值里别出现 `#`。

## 环境速查（本机，仅供参考）

| 项 | 值 |
|---|---|
| ComfyUI 地址 | `htt<local_path>`（Comfy Desktop 启动） |
| 工作流原件目录 | `<local_path>`（只读） |
| 模型目录 | `<local_path>` |
| 输出目录 | `<local_path>`（**提交前必查 system_stats，防漂移 C 盘**） |
| 角色语音库 | `<local_path>` |
| 提示词小助手 | `<local_path>` |
| GPU | Intel Arc A770 16GB（XPU） |
| 启动参数 | **禁加 `--enable-dynamic-vram`**（8-19 大图画风漂移根因，已移除；详见 `references/user-comfyui-environment.md`） |
| 临时脚本/产物 | 一律 D 盘（工作区 `_work\` 或 D 盘 tmp），**严禁 C 盘写入**；成品自动拷到 `_work/<引子basename>/` |

## 核心铁律（贯穿所有子技能）


0a. **两文件边界（全工作流通用，8-31 作者明确）**：每个工作流有 **两个 json**。①API 版（不带 UI 描述、由引子 `with_suffix(".json")` 读同 basename 的文件，如 `krea2汇总_api.json`）——**日常出图唯一被引子读取的**；②UI 版（带 `nodes/links/groups` 的完整 LiteGraph 格式，如 `krea2汇总.json` / `anima模型（副本）.json`）——**仅供人类使用/备份/分享部署参考**。**引子物理上只认"同 basename + .json"，永远读不到 UI 版**（UI 版 basename 跟引子对不上）。agent 出图链路**零 UI 版 token 损耗**；除非用户明确要求部署/解锁/排查 UI 界面本身，才去看 UI 版。

0. **提交铁律（硬性）**：统一走**引子黑盒**——每个工作流一个与模板同 basename 的 `_api.py`（如 `krea2汇总_api.py`）。agent 只填参数：`python workflows/<名>/<名>_api.py --prompt "…" [--w … --h … --name … --loras 名:强度:on]`。引子自动 内存拼 API（**不落盘**）→ 递交 `execution/comfy_submit.py` → 校验 `node_errors:{}` → 轮询 → 拷贝成品到 `_work/<引子basename>/` → 打印一行 JSON。**模板=固定样本只读；引子只改 guide 指定节点；loras 默认=模板原样，传参只改点名条目（绝不增删/绝不误开其他）**。无 API 模板的全新工作流：浏览器 UI 加载一次导出 API 模板（见 `NEW_WORKFLOW_GUIDE.md`）。agent 不看引子/comfy_submit 内部，只用接口。

1. **工作流原件只读**——加载/执行一律用技能库内固定副本，绝不改动 `<local_path>` 原件（作者会检查）。
2. **临时脚本/文件一律 D 盘**（`<local_path>`），C 盘零写入。
3. **提交前查输出目录**：`GET /system_stats` → argv → `--output-directory` 必须在 F 盘，漂移 C 盘则先告知作者处理，不擅自生成。
4. **graphToPrompt() 结果在 `.output`**（仅浏览器备用流程用；主流程走引子不涉及）。
5. **提交后必查 `node_errors: {}`**，非空则排障（execution/EXECUTION.md），不轮询注定失败的任务。
6. **最终交付文件重命名为有意义中文名**（主题+版本+日期），禁止自动编号/临时名（作者习惯7，硬性）。
7. **出图链路只有三步：写提示词 → 提交 → `MEDIA:` 交付。** 禁 vision 自检、禁联网查证角色资料（角色外观凭已知/角色串直接写）、禁长篇汇报与逐项核对清单——除非作者明确要求「自检」「查一下」「详细说」。她反复纠正过：分析图片、查资料、写汇报都算节外生枝，耗时远超出图本身。（作者习惯6）
8. **browser_console 单行 promise 链**、变量用 `window.__xxx` 防冲突、提示词含撇号用双引号包裹 JS 字符串。
9. **完成后清理**：杀掉临时 CORS 服务器，删除 D 盘 tmp 临时脚本。
10. **工作流副本是静态的**：用户没明确要求，绝不实时更新副本（见 NEW_WORKFLOW_GUIDE.md）。

## 验证清单（总）

- [ ] 加载的是技能库副本，原件 hash 未变
- [ ] 输出目录在 F 盘（system_stats 实查）
- [ ] 提交返回 node_errors: {}
- [ ] 成品重命名为有意义中文名后 MEDIA: 交付
- [ ] 临时服务器已 kill、临时脚本已清理

