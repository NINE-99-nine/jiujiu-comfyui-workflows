# anima 工作流 · 使用守则（guide v3.0，含提示词书写总纲）

> 本守则与 `anima模型（副本）.json`（固定副本）配套。**加载工作流一律用本目录内的副本**，不用本仓库目录下的原件——原件会被作者实时编辑，副本保证每次行为一致。
> 详细提示词规则见 `references/`（anima-prompt-rules.md 六层结构 / （已并入说明） / 已验证样例（已迁移） 已验证样例）。

## 副本信息

| 项 | 值 |
|---|---|
| 固定副本 | `workflows/anima/anima模型（副本）.json`（本技能内，2026-08-17 改名） |
| 原件位置 | `F:\Comfy-Desktop\ComfyUI-Installs\jiujiu-2\ComfyUI\user\default\workflows\anima模型.json` |
| **API 模板（定案 2026-08-19）** | `anima_quick_template.json` = **作者用 ComfyUI 内置导出功能导出的 API 版**（40 节点），MD5 `a6d244ba…`。**不再手动从副本/graphToPrompt 生成**（8-19 教训：dogma 自建模板导致画风错，官方导出即正常） |
| 节点数 | 40（官方导出 API 版） |

**40 节点模板结构要点（官方导出，勿改）**：
- **[51] TwoWaySwitch 只有 input_1**（`selection_setting: 1` 直接值）→ 纯文生图，无图生图链（[14][15][16] 不在模板内）
- **[21]/[379] denoise 是直接值**（1 / 1），非 AnySwitch 连接
- 无 [351]/[352]/[363] AnySwitch、无 [9] LoaderGGUF、无 [367] ModelPatchLoader
| 模型族 | anima（GGUF 基座 + turbo UNET + LoRA + Qwen3 CLIP + Qwen VAE + LLLite 修复） |

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

4. 模型目录：`F:\Comfy-Desktop\ComfyUI-Shared\models\loras\anima\`（优化/ 与 画风/ 两个子目录）。
5. **多画风 = 单图叠加（作者 2026-08-11 纠正）**：用户选多个画风时，默认是**一张图**同时叠加多个画风 LoRA——**API 直连：同时激活多个画风条目的 active 标记**；浏览器：text 并列写 `<lora:...>`，提交**一张**。**不是**每画风一张批量分图（曾误做成三张被作者纠正）。只有作者明确说"各出一张对比"时才循环提交多张。

**铁律**：
- **一切内容只写 `[23]`**——角色、场景、交互、构图、甚至敏感内容，全部写进人设二节点即可
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
- 引子自动 内存拼 API → 递交 → 校验 `node_errors:{}` → 轮询 → 拷成品到 `_work/<引子basename>/` → 一行 JSON。只改 [23]/[19]/[52]（normal 另 [344]），其余一字不动。
- **浏览器 UI 仅为备用**：仅全新工作流无模板时，走一次浏览器加载生成模板（见 EXECUTION.md 备用节）。
- 成品在 `F:\Comfy-Desktop\ComfyUI-Shared\output\<日期>\`（F 盘）。

## 提交铁律（2026-08-19 定案）

- 模板 = **作者官方导出的 API 文件**，不手动构建/不 graphToPrompt 生成（8-19 教训：dogma 自建模板 → 画风错；官方导出 → 正常）
- 只改 [19]/[23]/[52] 三节点，其余一字不动（含 seed、denoise 直接值、[51] 结构）
- 模板文件更新 = 作者重新导出后显式替换，MD5 记录于上文副本信息表

## 缓存坑（作者亲授，2026-08-12）

- **同提示词 + 同分辨率重复提交会命中 ComfyUI 缓存**，返回与上一张**完全一样**的图（文件大小都相同）。
- 需要重出/换种子变化时：**微调 [19] 分辨率**（如 832×1216 → 816×1248）即可破除缓存；不要用完全相同的宽高重提。

---

# 提示词书写总纲

> 本节是 `[23]` 人设二节点**怎么写提示词**的权威总纲（原 prompting.md 并入，v3.0）。

## 交付格式铁律（作者纠正过多次，硬性）

1. **只投喂正向提示词**到 `[23]`；负面词内嵌工作流 `[212]`，**绝不交付**（附带负面词曾被批"画蛇添足"）。
2. 分辨率单独给 `[19]`——**取值表见上文「分辨率规则」**（竖屏/横屏/方，1.5× 放大链）。
3. 提示词**纯英文**，tag 与自然语言交并：细节堆 tag、场景/交互/构图用自然语言长句。
4. 交付物 = 一个正向文本块 + 分辨率两个数字。不给负面词、不给多余参数表。

## 六层结构（作者亲授，v1.1）

```
① 一句话概括    → "一个XX样的人和另一个XX样的人在干XX"（锚定剧情）
② 人物1 细节    → 身份前缀 + 长相/身材/服装/配饰（或前缀+角色串）
③ 人物2 细节    → 同上（前缀必须区分两人；画面总人数 tag 必写，如 2girl）
④ 环境背景      → 画面中的其他元素与内容
⑤ 交互句        → "人物1和人物2在……"（长句描绘画面，色气的发动机）
⑥ 镜头/视角/构图 → 镜头类型、机位、元素位置、入画范围
```

**核心心法**：提示词写的是"正在发生什么"而不是"有什么"。给模型一个**剧本**，不是一张清单。纯 tag 堆砌 = 词汇表（被作者批评过）；六层结构 + 自然语言叙事 = 能出好画面的引擎。

## 提示词编写新格式（作者 v3 实测，2026-08-12）

> 三原则总纲：**主体原则**（写什么——开头定谁才是画面主角）／**优先原则**（怎么强调——顺序靠前 + 权重 `(xxx:1.3~2.0)`）／**注意力原则**（分多少——词量分配 = 模型注意力分配）。三者是一件事的三个面：先定主体 → 再排优先级 → 最后分配词量。

### 结构（段落分隔，便于检阅）
```
【主体长句】一大段有次序的自然语言叙事，定画面基调，占全文 ≥ 2/5
【The girl's appearance:】人物细节补充（人物串，按需取舍）
【Camera:】镜头类型 + 视角（特写/半身/远景/俯瞰/仰视/侧面……）
【Environment:】环境描写
【Interaction:】交互描写（人物×环境/物品/他人）
```
- 不是所有画面都含全部块——特写类 ~100 词即可，远景/群像 500-700+，**上限 1000**（anima 对 700 词后的内容理解弱化）。
- 重要的内容多写、放前面；次要的简短、放后面。

### a→the 指代铁律（防模型误认新人物）
- 主体长句首次引入用 `a`（a tiny gothic princess...）。
- 补充段**必须用 `the`**（The girl's appearance: The tiny gothic princess has...）——`a` 开头 = 另起新人物，画面会多画一个人。
- 标签明确指代：`The girl's appearance:` 就是"我刚刚说的那个女孩的长相"。

### 人物串取舍（谨慎）
- 人物为主 → 人物串近完整（写真需服装细节）；环境为主 → 远景缩句（白发/黑丝/剪影 3-5 特征）。
- **关键特征绝不可删**（删到 3 个特征 = 人物画没）；删减前综合：画面内容/占比/三原则/字数上限。

### 占比实操模板（浴室范例，见下节）

> 核心心法：**提示词里写了什么，AI 就画什么**——写进正向词的内容会被模型强调，没写的内容自由发挥。因此"写多少、先写谁、写哪些"直接决定画面侧重。

### 1. 侧重匹配（角色串不是万能钥匙）
- 画**背影/侧面/局部**时，不可无脑导入完整角色串——角色串含大量正面体态与服装描写（脸、胸、正面布局），AI 会尝试画出这些特征 → 背影图变成半转身。
- 正确做法：按画面角度**缩句**，只保留该角度可见的特征。例：莉莉丝背影 → 只写 `white hair, petite figure, black sheer bodysuit, evening gown`，删 `red eyes / detailed face / 锁链布局` 等正面特征词。

### 2. 画面侧重配平（占比 ≠ 死板词量比）
远景/环境图的正确配平**不是堆词量**（环境词堆到与人物串 3:1 的上千词不现实、且提示词过长本身有害），而是**四件套组合**：
1. **环境词"准确"增补**——加描写要**少而精**：抓住场景关键特征词（如 `vast autumn market square`、`cobblestone streets`、`gothic clock tower`），不追求数量碾压。
2. **主体长句强调**——在自然语言主体句里直接点明侧重：`the rich detailed scene dominating the entire frame`、`tiny figure in the vast square`——用句子语义告诉模型"谁才是主角"。
3. **人物串微缩**——**略微**削减：只删与画面无关的部分（如远景背影删正面面部/眼神描写），与画面可能相关的内容**尽量保留**（删太多 → 人物不像，得不偿失）。
4. **括号加权配平**——对要强调的内容用 `(xxx:1.3~1.6)` 权重（高于 1、甚至 1.5 以上），如 `(tiny figure:1.4)`、`(vast background:1.5)`、`(sex:1.6)`——**用权重配平，不用词量配平**。

**占比实操模板（作者亲授，2026-08-12 二版）**——参考浴室范例（top-down 全身场景）的排布：
```
质量词（masterpiece, best quality, 8k, ultra-detailed, anime illustration, cel-shading…）
→ 人物极简（1girl + 仅 2~3 个辨识特征词，如 black messy hair, purple eyes）
→ 人物动作链（服务于构图：bathing, upper body above water, arms resting, looking up toward viewer）
→ 镜头+场景定调（top-down overhead high angle shot, full bathroom scene）
→ 环境分区铺开（upper-left / middle-left / upper-right / bottom-right / bottom-left 五区，每区 3~6 个具体物品）
→ 环境细节总汇（材质/水珠/光线/氛围/质感词）
```
- **占比 = 词量分配**：人物压到 ~20 词（1girl+特征+动作链），环境用空间分区铺 ~65 词——**1:3 不是环境堆词，是人物压缩腾出空间**。
- **顺序可调换**：环境侧重图可以把环境/镜头词提前、人物词穿插在后，**不必死守六层顺序**。
- **削减人物 = 环境腾空间**：人物只留辨识特征 + 构图相关动作（如 looking up 服务俯视视角），删无关体态词。
- **最终出图质量为绝对优先**——一切取舍以此为准。

### 3. 主体优先（开头定调）
- **开头句子锚定画面侧重**：
  - 侧重人物 → 开头写"一个XX样的人正在干XX"
  - 侧重环境/远景 → **先写环境**（场景、光线、氛围），人物句后置（"……之中，一个微小的身影……"）
- 范例（作者验证过的远景正确写法）：`A tiny white-haired girl standing at the far edge of a vast autumn market square... the rich detailed scene dominating the entire frame.`——开头即点明"场景主导画面"，人物用 `tiny/far away/distant/barely visible` 缩句。

### 4. 特写聚焦（缩句防干扰）
- 特写/局部（足部、私处、手部）时：**削减人物串——不是全删、也不是全留**：
  - 全删 → 万一画面带出人物，人物不遵从角色串（发色/服装错乱）
  - 全留 → 无关特征词挤占权重，画面被拉远、焦点被稀释
  - 正确 → 保留**基本辨识特征**（莉莉丝例：白发、冷白皮、黑丝），删与焦点无关的正面体态与装饰词
- 范例：足部特写 → 写"一只黑丝玉足塞入装满精液的靴子"+ 人物缩句（白发、黑丝），不导入完整角色串。

### 5. 分区布局法（复杂场景/特写环境）
- 范例（作者验证过的浴室场景）：用**空间坐标分区**描述环境——`upper-left area: ...` / `middle-left: ...` / `upper-right: ...` / `bottom-right: ...` / `bottom-left: ...`，每区明确物品，再统一补细节氛围词。
- 适用：需要精确控制画面内容分布的复杂场景。环境词量大、物品具体、人物词简洁。

### 6. 前景-中景-背景层次（体积感）
- 只写背景不够——画面质感靠**前景-人物（中景）-背景**三层的空间层次撑起来。
- **前景元素**：画面最近处的遮挡物（虚化门框、窗沿、栅栏、枝条、翻倒的桌椅、散落的物件），制造纵深与体积感；前景常虚化（bokeh）。
- 写法：明确分层——`foreground: ...` / 中景（人物所在层）/ `background: ...`，或自然语言"through the X, ..., with Z in the far background"。
- 范例：远景图加 `foreground: an overturned velvet chair and a broken wine glass, softly blurred` → 画面从"平面"变"立体"，质感翻倍。
- 环境叙事补充：前景/背景的**物证**可以暗示人物经历（如翻倒酒杯、揉皱丝绸、散落衣物 = 发生过狂欢）。

### 7. 常见失误（新增）
- 远景图导入完整角色串 → 半转身/全身照
- 背景词量远小于人物词量却要求 wide shot → 人物过大
- 特写图全删或全留人物串 → 人物乱画 / 焦点被稀释
- 提示词过长堆砌 → 模型抓不住重点（用权重配平，不用词量）

## IP 角色串铁律

1. **角色串 = 该角色的完整默认外观**，写到角色串即完整，观众一眼认出。
2. **不要在角色串后追加服装描述**——错误/多余服装 tag 覆盖默认外观，人物走样（教训：阿罗娜补 `white sailor-style dress` 反而画错）。
3. **只有换装才强调**：`Arona from Blue Archive, arona_(blue_archive), (swimsuit:1.5)`。
4. 多人画面**每个角色必须加身份前缀**：`the first girl:` / `the second girl:` / `the girl in the left:` 等——只罗列角色串 → 模型把多人特征融成一人（真实教训：阿罗那+普拉娜被画成 1 人）。
5. **画面总人数 tag 必写**（`2girl`、`1girl`、`1boy and 1girl`），放人物层附近。

## 角色触发词来源（第一优先）

用户自建提示词小助手：`F:\Comfy-Desktop\ComfyUI-Installs\jiujiu-2\ComfyUI\user\default\prompt-assistant\tags\默认标签.csv`
（列：标签名, 标签值, 一级分类, 二级分类…）。**搜角色中文名**（守岸人/普拉娜/阿罗娜/圣娅/赛琳娜等），格式统一：`XXX from <Game>, xxx_(<game>)`。

- 守岸人：`shorekeeper_(wuthering_waves),Shorekeeper from Wuthering Waves`
- 普拉娜：`Plana from Blue Archive, plana_(blue_archive)`
- 阿罗娜：`Arona from Blue Archive, arona_(blue_archive)`

联网查人设被墙（萌娘百科/fandom Cloudflare）时降级：CSV 触发词 → LoRA `ss_tag_frequency`（`scripts/read_lora_meta.py` 读 safetensors 头部）→ LoRA 预览图 vision_analyze → 模型自身知识。

## 外观校准（作者审美，常驻）

- 正向必备：`young` / `teenage` / `petite` / `slender` / `small breasts` / `flat chest` + `innocent` 系表情词（底模默认熟女大胸 → 校准词不可省略）。
- **禁** large breasts / cleavage / mature / seductive。
- 男角色：少年感（纤细修长瘦弱、年幼紧张不安），忌壮硕成熟。
- 角色审美扩展见 `html-embedding/guide.md`（嵌字时同样适用）。

## 多人/多角色提示词（anime-multi-character-prompting 整合）

```
角色A触发词, 外观特征, 动作/交互动词,
角色B触发词, 外观特征, 反应/表情（与A的动作呼应）,
场景环境, 物品交互, 情绪, 氛围光照
```

1. **每个角色独立触发词 + 独立外观特征**（发色/瞳色/服装），否则模型融合两人
2. **身份前缀 + 总人数 tag**（见 IP 角色串铁律 4/5）
3. **动作必须成对呼应**：A 做动作（drag/tug/pull/point/hold/lean），B 给反应（reluctantly pulled/calm/slight smile/quietly holding）——"活"的关键
4. **环境物与人互动**：浪花溅脚、风吹发裙、灯光映脸、雨滴落伞
5. **情绪词给足**：cheerful laughing / calm expressionless / sparkling curious
6. 单场景提示词 ~70-90 词，质量词由工作流节点提供（不必重复）

## 镜头与构图（审美要求）

- **避免中心对称**（双人面对面居中=枯燥）；斜角/对角线构图、不对称平衡、元素错落。
- 更惊艳的机位：低角度仰拍、过肩视角、鱼眼/广角透视、大特写混搭全景、前景遮挡营造纵深。
- 构图句示例：`low angle shot, dynamic diagonal composition, Arona leaning in from the left foreground, Plana on the right with cafe lights creating depth`。

## 技术坑（投喂时的 JS 陷阱）

- 提示词含撇号（`worm's-eye` / `master's`）破坏 browser_console 单引号字符串 → JS 字符串用**双引号**包裹，或改写（`worm-eye`）。
- 角色串括号转义：CSV 里 `nozomi \\(blue archive\\)`——`\\(` 是**字面量括号**，去掉反斜杠会被 CLIP 解析为 1.1 倍权重，复合标签失效、角色跑偏（教训：橘望画错）。JS 里写 `\\\\(`，**原样保留反斜杠**。
- 超长单表达式偶发传输编码错（`'utf-8' codec can't decode byte 0xb4`）→ **拆步设置**：先分别设 52/23/19 各节点值（每步一条短表达式返回确认），最后单独 graphToPrompt + 提交，即可绕过（2026-08-11 实测）。
- 提交前检查输出目录在 F 盘（system_stats 实查，C 盘零写入铁律）。

## 已验证样例（复用改参数）

见 `references/已验证样例（已迁移）`（芭蕾三幕、小女仆玛丽珍等完整提示词，直接套结构改参数）。

## 版本日志

- v3.0（2026-08-18）：并入原 prompting.md 提示词书写总纲，guide 与 prompting 两文件合一
- v1.0：整合 anima-prompt-rules.md（六层结构 v1.1）+ anime-multi-character-prompting（多人结构/触发词来源）→ 统一收纳于本总纲（2026-08-09）
