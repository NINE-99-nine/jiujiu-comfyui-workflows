# anima 提示词说明书

> anima 的文本编码器是小参数 CLIP：它读的是**词与词的向量关系**，不是文章。
> 写提示词的目标只有一个——**让每个词都落成一个准确的向量**。

## 〇 总则（三条，先读这一节）

1. **是说明，不是文章**：只写"画面上有什么、正在发生什么、镜头在哪"。不写感受、不写比喻、不写抒情。
2. **要肯定，不要否定**：写"要什么"；不要的东西直接不写。`no` / `without` / `不要` / `没有` 一律不出现。
3. **一个意思只说一次**：同一件事写两遍，两个词互相抢权重，等于把注意力摊薄。

## 一 语言与体裁

- 纯英文。
- tag 与短句混用：**外形用 tag，动作、机位、构图用短句**。
- 同类 tag 成组、每组一行（外貌 / 服装 / 配饰 / 背景），不排成长串。

## 二 写法骨架（六层，自上而下写）

| 层 | 写什么 | 例句 |
|---|---|---|
| ① 概括 | 一句：谁正在做什么 | `Close-up of a girl adjusting her glasses.` |
| ② 人物 | 人数 tag ＋ 年龄体型 ＋ 发 / 瞳 / 脸 ＋ 服装配饰 | `1girl, solo, petite 13-year-old girl, ...` |
| ③ 动作 | 正在发生的那一个动作 | `One hand pushing the frame up.` |
| ④ 环境 | 背景与画面内其他元素 | `Plain white background.` |
| ⑤ 机位与构图 | 距离、机位高度、朝向、裁切、构图 | `High angle, front view, extreme close-up.` |
| ⑥ 风格 | 画风与质感词 | `crisp anime lineart, flat cel shading.` |

## 三 人物写法

**OC（手写）**
`1girl, solo, (13-year-old petite slender girl:1.2), waist-length silver-white hair, crimson eyes, pale skin, black halter top, ...`
外观逐项写全；服装逐件写全。

**知名角色（角色串）**
角色串本身就是该角色的完整默认外观。**串后不再追加服装描述**——追加会覆盖默认外观、人物走样；只有换装时用 `(swimsuit:1.5)` 压过默认造型。

**多人**
每个角色前加身份前缀（`the first girl:` / `the girl on the left:`），画面总人数 tag 必写（`2girls` / `1boy and 1girl`）。

**校准词**
幼态画面必备 `young / petite / slender / small breasts / flat chest` 与清纯表情词；`large breasts / cleavage / mature / seductive` 不写。

## 四 镜头与构图（可复制清单）

- 机位高度：`eye-level` / `high angle`（俯视，从上往下看）/ `low angle`（仰视）/ `from above`
- 镜头距离：`extreme close-up` / `close-up` / `upper body` / `full body` / `wide shot`
- 朝向：`front view` / `three-quarter view` / `profile` / `back view`
- 构图：`diagonal composition` / `asymmetric balance` / `foreground framing`（前景遮挡）
- 合成一句：`High angle, front view, extreme close-up, diagonal composition.`

## 五 动态与瞬间

- 动作写成**进行中**：`pushing the frame up, caught mid-action`。
- 局部动态逐处写：`head tilted slightly to her right` / `a few strands flipped up` / `skirt swaying`。
- 前景遮挡：`one hand raised in the foreground, partially covering her cheek`。
- **只写入画的手脚**。原图只有一只手入画就只写一只手——写了"two hands"，模型就会补出第二只。

## 六 词量与配平

| 画面 | 词量 |
|---|---|
| 单人头肩特写 | 80–120 |
| 单人半身 / 全身 | 120–200 |
| 双人 | 250–350 |
| 群像 / 远景 | 500–700（上限 1000） |

- 主体先写：人物为主则人物段在前；环境为主则环境段在前，人物用 `tiny / distant` 缩句。
- 角度不匹配就缩句：背影、侧面、局部不导入完整外观串，只留可辨识特征。

## 七 翻车对照表

| 不合格写法 | 问题 | 合格写法 |
|---|---|---|
| `no glasses, without a hat` | 否定句 | 只写要出现的东西，其余不写 |
| `like a gentle fairy, dreamlike` | 比喻、抒情 | `soft smile, relaxed eyes` |
| `two hands raised`（原图单手） | 入画手脚数不符 | `one hand raised to the frame` |
| `eye-level camera`（原图俯视） | 机位写反 | `high angle, looking down at her` |
| 同一段里"微笑"写三遍 | 同义重复抢权重 | 只写一次，必要时 `(smile:1.2)` |
| 角色串后追加服装 tag | 覆盖默认外观 | 串后不写服装；换装才加 `(xxx:1.5)` |
| 人物段很长却没有动作与机位 | 人物站桩 | 补第 ③ 层与第 ⑤ 层 |

## 八 写完自查（逐条过）

- [ ] 全英文；无否定句；无比喻与抒情句
- [ ] 一个意思只出现一次
- [ ] 有动作（进行中）与机位（高度 / 距离 / 朝向）
- [ ] 入画的手脚数量、动作与参考图一致
- [ ] 人数 tag 与实际人数一致
- [ ] 分组换行，同类 tag 成组
- [ ] 词量落在对应区间内
