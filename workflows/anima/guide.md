# anima 工作流 · 使用守则（guide v3.3）

> 本守则与 `anima模型（副本）.json`（固定副本）配套。**加载工作流一律用本目录内的副本**，不用作者目录下的原件——原件会被作者实时编辑，副本保证每次行为一致。

## 副本信息

| 项 | 值 |
|---|---|
| 固定副本 | `workflows/anima/anima模型（副本）.json`（本技能内，2026-08-17 改名） |
| 原件位置 | `<comfyui_installs>\jiujiu-2\ComfyUI\user\default\workflows\anima模型.json` |
| **API 模板（定案 2026-08-19）** | `anima_quick_template.json` = **作者用 ComfyUI 内置导出功能导出的 API 版**（40 节点）。**不再手动从副本/graphToPrompt 生成**（8-19 教训：作者 自建模板导致画风错，官方导出即正常） |
| 节点数 | 40（官方导出 API 版） |

> ⚠️ **2026-09-15 底模升级（作者下令的模板直改例外）**：三个 JSON 的 **[8] UNETLoader 模型名**统一由 `anima\anima-turbo-v1.0-int8-convrot.safetensors` 改为 **`anima\anima-turbo-v1.1-int8convrot.safetensors`**（注意 1.1 文件名**无连字符**；文件在 `models\unet\anima\`）。
> - 现 MD5：`anima_quick_template.json` = `d9e94a69…`｜`anima_normal_template.json` = `5781108b…`｜`anima模型（副本）.json` = `e504b689…`
> - 三个文件各留 `.bak_20260915`（改前原件，JSON 合法可整档回滚）；正常模板里 [9] LoaderGGUF（v1.0-Q8_0）与 UI 里的 [9]/[45]/[20] 属**未接入链路的分支**，本次未动
> - **若作者在 ComfyUI 里重新导出模板或被更新覆盖，此行改动需重打**（届时以新导出为准，再改 [8]）

**40 节点模板结构要点（官方导出，勿改）**：
- **[51] TwoWaySwitch 只有 input_1**（`selection_setting: 1` 直接值）→ 纯文生图，无图生图链（[14][15][16] 不在模板内）
- **[21]/[379] denoise 是直接值**（1 / 1），非 AnySwitch 连接
- 无 [351]/[352]/[363] AnySwitch、无 [9] LoaderGGUF、无 [367] ModelPatchLoader

## 使用模式（逻辑门切换，2026-08-19 定）

anima 工作流通过 GroupIgnoreManager 逻辑门切换两种模式（**正常生成 ↔ 快速生成 互斥**），搭配两种放大链（**anima放大 ↔ seedvr2**）。可改节点均为 [19]/[23]/[52]。

### 快速模式（默认 = `anima_quick_template.json`）
- 逻辑门：快速生成=开、正常生成=关；**anima放大=开、seedvr2=关**
- 采样：少步数（[21] 经开关实际 12 步 cfg 2）
- 放大：anima 放大链（[15] 缩放 ×1.5 → [59] VAEEncode → [379] 二次采样 6 步 cfg 1）
- 适用：追求速度 + 一定质量

### 正常模式（`anima_normal_template.json`）
- 逻辑门：正常生成=开、快速生成=关；**anima放大=关、seedvr2=开**
- 采样：FLS_SamplerV4 正常步数（10 步 cfg 1）
- 放大：**seedvr2 放大**（关闭 anima 二次采样，走 SeedVR2 超分链路）
- **最终分辨率 = [344] SeedVR2VideoUpscaler 的 `resolution`（默认 1600，上限 `max_resolution` 3140）+ 初始 [19] 分辨率**——出大图时同步调 344 与 [19]。实测逻辑（8-19）：`resolution` 决定放大倍率（按短边方向），`max_resolution` 为输出长边上限，超出即截断（例：1704×728 + resolution 2560 → 倍率 3.5×，长边 5990 被 max 3140 截为 3140×1342）
- **初始 [19] 设置原则**：初始分辨率决定初次出图质量——太低则 seedvr2 放大后质量差；太高则放大效果不显著（浪费放大性能）。**建议介于 1~1.6 百万像素之间**（如 832×1216≈101 万、1024×1216≈125 万、1152×1280≈147 万）
- 可改节点：**[19]/[23]/[52] + [344]（seedvr2 分辨率）**
- 适用：兼顾速度与质量

> 切换逻辑门须在 ComfyUI 浏览器 UI 操作（GroupIgnoreManager 纯前端节点，API 无法模拟）；切换后内置导出对应模板并存，按需选用。

## 可改节点（铁律：只准改这三个，其他一律不碰）

**严格禁止修改以下三个节点以外的任何节点**（参数、连接、bypass 状态均不碰）。其余节点（含 [18] 人设一、[211] 主链正面词、[212] 负面词、[225] 修手词等）不读、不改、不操作：

| 节点 ID | 功能 | 改法 |
|---|---|---|
| `19` | 分辨率大师简化版 `[宽,高]` | **节点对象路径**（hidden widget，数据路径无效），见下方分辨率规则 |
| `23` | 人设二（角色+场景+交互+构图提示词） | 数据路径 widgets_values[0] |
| `52` | **Lora Loader (LoraManager)**（LoRA 风格控制） | API 直连：改 `inputs.loras.__value__` 条目的 **active 标记**（默认一字不动）；浏览器：`widgets[1].value`（text） |

**52 号 LoraManager 使用规则（8-17 定案）**：
- 节点结构：`widgets[0]` = 隐藏元数据（不动）；`widgets[1]` = text；`widgets[2]` = loras 列表（完整条目，active 标记决定加载）
- **API 直连机制（实测铁证）**：后端 `load_loras()` 第一行 `del text` —— **text 输入被丢弃，无效**；真正生效 = `inputs.loras`（`{"__value__": [条目...]}`，**active=true 才加载**）；前端 `serialize_widgets=true` 会把 loras 序列化进提交参数
- **默认画风 = 工作流内置 loras 状态**：模板 `anima_quick_template.json` 的 loras = 完整 7 条（三件套 active + 4 画风 inactive，与副本 wv[2] 一致）。**提交时 [52] 一字不动**
- **改画风（API 直连）= 只改条目的 active 标记**：取消旧画风 active、激活新画风 active。**严禁增删/替换条目**（=修改工作流，8-17 教训）
- 浏览器改法（仅浏览器流程）：text widget 输入 `<lora:名:强度>`（前端 callback → merge 进 loras widget → serialize 进提交）

## 画风选择规则（作者 v2.0 定稿，2026-08-09）

1. **默认画风 = gpt-image-2**：用户没强调画风/LoRA 时不动 [52]（模板内置 = 优化两件套 + gpt-image-2）。
2. **用户说"换个画风/换个风格/换个 lora"时，给选择题**——用 Hermes 的 clarify 工具列出画风选项（A/B/C/D…），**绝不让作者手动打字输入长 LoRA 名**（作者明确要求，手打长名违反习惯4）。
3. 画风选项表（选项文字用简短中文描述，不带长文件名）：

| 选项 | 画风 LoRA（附加在优化两件套后） | 特征 |
|---|---|---|
| A. gpt-image-2（默认） | `gpt-image-2_anima-base1_v1-1:1.00` | GPT 图像增强，通用默认 |
| B. 天空之光 | `sky02Lightv3:1.00` | 通透天空光感 |
| C. 晨雾 | `far off in the morning haze024064645510a_30:0.80` | 朦胧晨雾氛围 |
| D. 写实更新 | `Anima_in_real_update_v2_epoch_20:1.00` | 写实质感 |
| E. 混合画风 | `mixed_styles_anima-base1_v5:1.00` | 多画师混合 |
| F. 线稿风 | `animeoutlineV4_16:0.90` | 描线清晰（备选） |
| G. 其他画风 | （画风/ 目录备选：chen-bin_V3.9、sheya chen-000192、wy-000029_purged） | 需先问作者 |

4. 模型目录：`<comfyui_dir>\models\loras\anima\`（优化/ 与 画风/ 两个子目录）。
5. **多画风 = 单图叠加（作者 2026-08-11 纠正）**：用户选多个画风时，默认是**一张图**同时叠加多个画风 LoRA——**API 直连：同时激活多个画风条目的 active 标记**；浏览器：text 并列写 `<lora:...>`，提交**一张**。**不是**每画风一张批量分图（曾误做成三张被作者纠正）。只有作者明确说"各出一张对比"时才循环提交多张。

**铁律**：
- **一切内容只写 `[23]`**——角色、场景、交互、构图、甚至 NSFW 内容，全部写进人设二节点即可
- 不需要清空/关注 [18] 等被屏蔽节点——它们不生效，无论画什么内容都不用管
- 分辨率永远走 [19]

## 提示词生效链路（官方导出 40 节点模板）

- 最终出图分支：`[21]` KSampler（初次）→ 放大链路 `[61]`→`[59]`→`[379]`（二次采样）→ `[349]` AnySwitch → `[40]` SaveImage
- **`[23]` 人设二接入 [7] JoinStringMulti → [1] CLIPTextEncode → [21]/[379]，内容在此生效**
- **纯文生图**：`[51]` TwoWaySwitch 只有 input_1（EmptyLatentImage），selection_setting=1 直接值——无图生图链、无底图参与

## 分辨率规则（1.5× 放大链路）

工作流含 UltimateSDUpscale + SeedVR2 放大，**基础分辨率会被放大 1.5 倍（像素 ×2.25）**：

| 想要的目标成品 | 基础设置 [19] |
|---|---|
| 1536×1024（横屏） | `1024×683` |
| 1536×1536（方） | `1024×1024` |
| 1248×1824（竖） | `832×1216` |

显存上限参考：A770 16GB，基础 1024×1024 安全；系统内存紧张时（<5GB 空闲）慎用更大尺寸。

## 加载与提交链路（黑盒引子）

- **两模式引子**（各配同 basename 模板，自动配对）：快速 `anima_quick_template.py` ↔ `anima_quick_template.json`；正常 `anima_normal_template.py` ↔ `anima_normal_template.json`。
- **快速：** `python anima_quick_template.py --prompt "…" --w 512 --h 768 --name 名字 [--loras 名:强度:on]`
- **正常：** `python anima_normal_template.py --prompt "…" --w 1024 --h 1536 --name 名字 [--seedvr2-res 1600 --loras 名:强度:on]`
- **长提示词／含英文双引号（气泡框台词、画面文字等）→ 把 `--prompt` 换成 `--prompt-file 提示词.txt`**（两模式均支持，与 `--prompt` 互斥，2026-09-14 与 krea2 同款改造）：根治"内嵌双引号被 PowerShell 截断参数"问题。文件按 UTF-8 **原样读取**（容 BOM、CRLF→LF、仅去首尾空白），段落与引号一字不改；文件不存在/为空 → 报错不递交。备份 `anima_quick_template.py.bak_20260914`、`anima_normal_template.py.bak_20260914`。
- 引子自动 内存拼 API → 递交 → 校验 `node_errors:{}` → 轮询 → 拷成品到 `_work/<引子basename>/` → 一行 JSON。只改 [23]/[19]/[52]（normal 另 [344]），其余一字不动。
- **浏览器 UI 仅为备用**：仅全新工作流无模板时，走一次浏览器加载生成模板（见 EXECUTION.md 备用节）。
- 成品在 `<comfyui_dir>\output\<日期>\`（F 盘）。

## 提交铁律（2026-08-19 定案）

- 模板 = **作者官方导出的 API 文件**，不手动构建/不 graphToPrompt 生成（8-19 教训：作者 自建模板 → 画风错；官方导出 → 正常）
- 只改 [19]/[23]/[52] 三节点，其余一字不动（含 seed、denoise 直接值、[51] 结构）
- 模板文件更新 = 作者重新导出后显式替换，MD5 记录于上文副本信息表

## 缓存坑（作者亲授，2026-08-12）

- **同提示词 + 同分辨率重复提交会命中 ComfyUI 缓存**，返回与上一张**完全一样**的图（文件大小都相同）。
- 需要重出/换种子变化时：**微调 [19] 分辨率**（如 832×1216 → 816×1248）即可破除缓存；不要用完全相同的宽高重提。
