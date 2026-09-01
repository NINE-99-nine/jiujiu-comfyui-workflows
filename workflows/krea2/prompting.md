# krea2 子技能 · 提示词书写总纲（prompting.md）

> krea2 用 Qwen3VL CLIP（`qwen3vl_4b_heretic`），**自然语言长句理解强**，输入方式与 zimage 同族。
> 本文件是 [13] 人设二节点**怎么写提示词**的权威总纲。

## 输入方式

- **主输入 = [13] 人设二**（StringConstantMultiline，键 `string`），自然语言为主
- 中英**都可以**，**英文效果更好**（CLIP 训练语料英文为主）
- 另外 [10] 质量词 / [11] 人设一 / [12] 画风词 经 [14] JoinStringMulti 一并拼接进正向链——这三个一般不动（作者手动维护），**交付物 = [13] 一段文本 + [31] 两个数字**
- 负面词内嵌 [9]，绝不交付

## 书写顺序（作者定稿）：画风质感 → 画面内容 → 构图镜头

```
① 画风质感    → 材质/光影/风格基调（film photography / soft cinematic lighting / 赛璐璐 / 通透光感……）
② 画面内容    → 主体 → 人物外观（发/瞳/脸/身材）→ 服装 → 场景 → 细节，按合理顺序自然语言书写
③ 构图镜头    → 镜头类型/机位/视角/景别（low angle shot / close-up / full body / worm-eye view……）
```

- **一段连贯的自然语言**，不是 tag 堆砌——模型对"有前因后果的句子"理解远好于词汇表（与 zimage/anima 同理）
- 想强调的关键元素用 `(xxx:1.3~1.5)` 权重（与 SD 系一致）
- 词量上限参考 anima（~700 词后弱化），实际 150-400 词即可出好图

## 文字渲染（krea2 特性，重要！）

- 模型对**英文书写**支持好；**图片内要原生出现的文字，内容必须用引号标注**，否则模型无法识别文字
  - ✅ `a neon sign reading "PARADISE"` / `a storefront sign that says "CAFE"`
  - ❌ `a neon sign reading PARADISE`（无引号 → 大概率画成乱码/糊字）
- 中文文字支持弱，要画面文字建议用英文（标牌/招牌/书名/台词等）

## 画风质感常用词（① 段弹药）

- 摄影系：`film photography, soft cinematic lighting, golden hour, high contrast, film grain, bokeh, shallow depth of field, macro detail`
- 插画系：`anime illustration, cel shading, clean lineart, vibrant colors, soft pastel tones`
- 质感系：`ultra-detailed, 8k, textured fabric, glossy highlights, subsurface scattering`

## 完整示例（对照结构）

**示例 1 · 中文输入**：
```
电影摄影质感，柔和电影光，金色时刻的光线，细腻胶片颗粒，
一个银白色短发的少女站在日式传统街道上，穿着白色荷叶边露脐水手服和极短的浅蓝色百褶裙，背着红色小学生书包，回眸看向镜头，俏皮地嘟嘴，脸颊泛红，
背景是木质的町屋建筑和远处的青山，晴天强光，梦幻的光斑，
低角度镜头，全身构图
```

**示例 2 · 英文输入（效果更佳）**：
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

## 常见失误

- tag 堆砌（`white hair, blue eyes, school uniform` 连排）→ 模型抓不住主体，改自然语言长句
- 画面文字不加引号 → 文字画不出来/乱码（krea2 特有，最易踩）
- 顺序错乱（先镜头后内容）→ 模型理解弱化，严格按 画风质感→内容→镜头
- 提示词过短（<50 词）→ 画面空泛；过长（>700 词）→ 重点稀释

## 版本日志

- v1.0（2026-08-23）：作者提供使用原则（画风质感→画面内容→构图镜头、引号标文字、中英皆可英文更佳），初步成稿
