# krea2 子技能 · 提示词编写总纲（prompting.md）

> krea2 走 Qwen3VL CLIP（`qwen3vl_4b_heretic`），**自然语言长句理解强**，与 zimage 同族。
> 本文件是 [13] 人设二节点**怎么写提示词**的权威总纲。完整范式/案例库见 `prompt-library/krea2-poster-examples/`。

## 0. 核心认知（先看这条，和 anima 完全不同）

- krea2 能消化**"设计说明"级别的长文本**。**不要用 anima 的"砍短防稀释"思维**——那不是 krea2 的写法。
- 写法两句话：① **把设计意图写透**（构图/色彩/材质/遮挡/层次/排除项全写清，喂给它的理解力）；② **守住全篇一致性**（一张图正反不打架）。
- 唯一硬约束 = **一致性**。一份提示词里"要什么"和"不要什么"必须始终如一（例：既要求"文字准确可读"又声明"完全禁止文字"必翻车）。
- 一句话：**anima 是"把提示词砍短到不扰注意力"，krea2 是"把提示词写透到像一份设计说明"。**

## 1. 输入方式

- 主输入 = [13] 人设二（StringConstantMultiline 键 `string`），自然语言为主。
- 中英**都可以**，**英文效果更好**（CLIP 训练语料英文为主）。
- [10] 质量词 / [11] 人设一 / [12] 画风词 经 [14] 拼接进正向链，**一般不动**；交付物 = [13] 一段文本 + [31] 尺寸。
- 负面词内嵌 [9]，绝不交付。

## 2. 词量（无硬限，按复杂度弹性）

- krea2 **没有"几百词上限"**。词量按画面复杂度伸缩：
  - **单人/特写/简单场景**：150-400 词即可。
  - **设计海报/概念主视觉/复杂叠层**：**500-2000+ 词，越细越准**，krea2 吃得下（参考案例库 5 例均为长文）。
- **但别为凑数堆词**——每个描述都必须是**可执行的视觉指令**（具体、有画面、能指导模型落笔），不是形容词罗列。**信息密度 ≠ 词数**。
- 判断标准：**再加词能带来新的视觉指令就加；只是重复/形容词就砍。**
- ⚠️ 设计类**别过早砍词**：砍到 150 词会把构图/层次/排除项全丢，只剩一张"好看的空白海报"。

## 3. 基础书写顺序（作者定稿，适配一般角色/写真/场景）

```
① 画风质感    → 材质/光影/风格基调（film photography / soft cinematic lighting / 赛璐璐 / 通透光感……）
② 画面内容    → 主体 → 人物外观（发/瞳/脸/身材）→ 服装 → 场景 → 细节，按合理顺序自然语言书写
③ 构图镜头    → 镜头类型/机位/视角/景别（low angle shot / close-up / full body / worm-eye view……）
```

- **一段连贯的自然语言**，不是 tag 堆砌（模型对"有前因后果的句子"理解远好于词汇表）。
- 想强调的关键元素用 `(xxx:1.3~1.5)` 权重（与 SD 系一致）。

## 4. 进阶：设计海报/概念主视觉 · 十段骨架

写「实验性设计海报 / 概念游戏主视觉 / 编辑海报 / 抽象专辑封面」这类产物时用这套；**其他情况按 §3 即可**。按顺序成段，每段一个职能：

1. **开场定调**：给整图定性（是哪种东西），并**反向框死**别跑偏——`The result should feel intentionally chaotic... rather than randomly cluttered` / `not a natural scene and not a conventional illustration`。
2. **角色锚定**：唯一角色 + 保识别度不改造型 + 禁加无关特征 + **脸部/眼神/表情 = 绝对保护区**（外围发梢/服装/下半身允许被设计层分割覆盖，但绝不动脸）。
3. **分区构图**：每个设计元素写清 **位置 + 占比量化 + 相对关系**，并给**焦点层级**（第 1/2/3 焦点）。
4. **色彩系统 = 分配预算**：主色归主体、点缀色只给指定小元件、明确禁色。
5. **材质质感**：质感词库堆叠 + **反质感排除**（不做光滑 CG/精致摄影/3D 渲染/奇幻光效/过量粒子）。
6. **层次遮挡**（krea2 最吃这口）：让东西与背景**真正融合、不是干净的抠图图层**——穿插、半透明叠印、正反相蒙版、**遮罩"边缘锐利但内影柔软"**、同时**留干净区**（脸周不穿线）。
7. **细节充实**：小型标识/刻度/元素堆叠（空心圆、十字定位符、取样框、扫描线、撕裂边），保证耐细看。
8. **负面排除**：尤其"**完全禁止文字/字母/数字/水印/二维码**"、"避免过度光效/杂乱/密度失衡"。
9. **情感概念句**：给一句"它想表达什么"（`在显现与消失之间建立强烈张力` / `困在记忆层中的声音`），帮模型抓情绪温度。
10. **结尾风格标签连排**：comma list 钉一组风格坐标收口（Swiss grid / glitch / brutalist / Y2K cyber / 现代游戏主视觉…）。

> 每一步的具体示范与 5 例完整案例 → `prompt-library/krea2-poster-examples/`。

## 5. 文字渲染（krea2 特性，重要！）

- 模型对**英文书写**支持好；**要原生出现的文字，内容必须用引号标注**，否则识别不出。
  - ✅ `a neon sign reading "PARADISE"` / `a storefront sign that says "CAFE"`
  - ❌ `a neon sign reading PARADISE`（无引号 → 大概率画成乱码/糊字）
- 中文文字支持弱，要画面文字建议用英文。
- **文字策略二选一并贯彻到底**：要么「带引号 + 指定内容」（这类可读），要么「声明完全禁止文字/水印/二维码」（这类留纯抽象）。**绝不在一张图里混用。**

## 6. 画风质感/材质常用词（① 段 / 第 5 段弹药）

- 摄影系：`film photography, soft cinematic lighting, golden hour, high contrast, film grain, bokeh, shallow depth of field, macro detail`
- 插画系：`anime illustration, cel shading, clean lineart, vibrant colors, soft pastel tones`
- 质感系：`ultra-detailed, 8k, textured fabric, glossy highlights, subsurface scattering`
- 设计海报材质系（多用）：`rough matte paper, old archive folder, chalkboard, paper fiber, ink absorption, dry brush, photocopy grain, registration offset, halftone, grid, blueprint, distressed print texture`

## 7. 完整示例（对照结构）

**示例 1 · 中文基础（角色/场景）**：
```
电影摄影质感，柔和电影光，金色时刻的光线，细腻胶片颗粒，
一个银白色短发的少女站在日式传统街道上，穿着白色荷叶边露脐水手服和极短的浅蓝色百褶裙，背着红色小学生书包，回眸看向镜头，俏皮地嘟嘴，脸颊泛红，
背景是木质的町屋建筑和远处的青山，晴天强光，梦幻的光斑，
低角度镜头，全身构图
```

**示例 2 · 英文基础（效果更佳）**：
```
film photography, soft cinematic lighting, golden hour rays, delicate film grain,
a silver-haired girl in a white ruffled sailor crop top and an extremely short blue pleated skirt standing on a traditional Japanese street, holding a red randoseru backpack, looking back over her shoulder with a playful pout, cheeks flushed,
wooden machiya houses and pale blue mountains in the distance, bright warm sunlight, dreamy bokeh,
low angle shot, full body, (playful mood:1.2)
```

**示例 3 · 带画面文字**：
```
masterpiece, best quality, neon-lit night alley, cinematic lighting,
a girl in a white sailor uniform standing under a flickering neon sign, the sign reading "PARADISE" in glowing pink letters,
rain-slicked asphalt reflecting the lights, steam rising from a food stall,
medium shot, eye-level, moody atmosphere
```

**示例 4 · 设计海报（十段骨架，长文，无文字）**：
> 完整案例见 `prompt-library/krea2-poster-examples/01_优秀案例.md`（黑档案 X 光花 / 城市钴蓝 / 鹰 Y2K / 初音模块化等 5 例，含中英双叙述）。

## 8. 常见失误

- **tag 堆砌**（`white hair, blue eyes, school uniform` 连排）→ 抓不住主体，改自然语言长句。
- **画面文字不加引号** → 文字画不出来/乱码（krea2 特有，最易踩）。
- **顺序错乱**（先镜头后内容）→ 理解弱化，严格按 画风质感→内容→镜头。
- **过早砍词**（设计类写太短）→ 指导不足、画面空泛；设计海报别砍到 150 词。
- **内部矛盾**（文字可读 vs 禁止文字 / 交叉版型 vs 侧开 / 竞速紧身 vs 兔女郎情趣）→ krea2 越强越容不下，必翻车。
- **为长而长**（堆无意义形容词、密度低）→ 模型找不到重点。

## 版本日志

- v1.1（2026-09-07）：**去除词量硬限**，升级为"设计 brief 式"书写法；新增十段骨架（设计海报/概念主视觉）；新增案例库入口；补充"别过早砍词/别内部矛盾/别为长而长"三条防坑。
- v1.0（2026-08-23）：作者提供使用原则（画风质感→画面内容→构图镜头、引号标文字、中英皆可英文更佳），初步成稿。
