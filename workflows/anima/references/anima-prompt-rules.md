# anima 系 AI 绘画提示词撰写规则（作者亲授，v1.1）

适用于 anima 类 SDXL/Illustrious 系动漫模型。**tag 与自然语言交并使用，纯英文。**
本规则持续成长：每次作者指正即回写更新（见文末版本日志）。

## 六层结构（自上而下）

```
① 一句话概括    → "一个XX样的人和另一个XX样的人在干XX"（相对长，但比细节短；锚定剧情）
② 人物1 细节    → **身份前缀** + 长相/身材/服装/配饰（或前缀+角色串）
③ 人物2 细节    → 同上（前缀必须区分两人；画面总人数 tag 必写，如 2girl）
④ 环境背景      → 画面中的其他元素与内容
⑤ 交互句        → "人物1和人物2在……"（一句或几句长句，描绘画面）
⑥ 镜头/视角/构图 → 镜头类型、机位、元素位置、入画范围
```

## 人物细节三种写法（按人物类型）

| 类型 | 写法 | 示例 |
|---|---|---|
| 纯 OC（tag 流） | 人设句开头 + 1girl/年龄/身材 + 五官 + 发型 + 服装逐项 tag | `A cute maid lolita with snow white hair and red eyes wearing a very short backless maid dress..., solo, solo_focus, 1girl, young, teenage, petite, slender, small breasts...` |
| 纯 OC（自然语言流） | 描述性长句 + `(关键词:权重)` 加权 | `(white_hair:1.8),(red hair ribbons:1.1),(black and white checkered pattern:1.2)` |
| 知名 IP 角色 | **角色串即默认外观**（见下方铁律）；多人画面必带身份前缀 | `the first girl: Arona from Blue Archive, arona_(blue_archive)` |

## IP 角色串使用铁律（v1.1 补充，最重要）

1. **角色串 = 该角色的完整默认外观**（模型训练数据里的经典服装与造型）。写到角色串就已完整——**观众一眼认出："这个经典服装，就是她/他"**。
2. **不要在角色串后追加服装描述**——错误或多余的服装 tag 会覆盖默认外观，导致**人物走样**（教训：给阿罗娜补 `white sailor-style dress` 反而画错了人）。
3. **只有换装才强调**：角色默认穿厚衣、想画泳装 → 在角色串后加 `(swimsuit:1.5)` 或更高权重，压过默认造型：
   ```
   Arona from Blue Archive, arona_(blue_archive), (swimsuit:1.5)
   ```
4. 若确需补充外观细节（如守岸人案例），只补**该角色正确的默认特征**（发色瞳色、标志配饰、经典服装分组），不要发明新服装。
5. **多人画面必须给每个角色加身份前缀**——`the first girl:` / `the second girl:`，或 `the girl in the left:` / `the girl in the right:` 等，写在角色串前面，让 anima 的 CLIP 编码器知道这是**两个不同人物**。只罗列角色串不写前缀 → 模型把多人特征融合成一个角色（真实教训：阿罗那+普拉娜被画成 1 人）
6. **必须写明画面总人数 tag**（`2girl`、`1girl`、`1boy and 1girl` 等），放在人物层附近，让模型明确画面里有几个人

## 案例三（IP 角色串格式，分行分组）

```
shorekeeper_\(wuthering_waves\)
purple eyes, bright_pupils, blue hair, blue eyelashes
butterfly hair ornament, two-tone veil, silver choker, blue nails
sleeveless dress, two-tone dress, jewelry_on_cleavage, see-through_leotard, leotard_under_clothes
silver armlet, bare shoulders
high heel sandals, heel_less
```

## 镜头与构图（v1.1 补充，审美要求）

- **避免中心对称**——双人面对面居中 = 枯燥。
- **要活泼灵动**：斜角/对角线构图、不对称平衡、元素错落有层次。
- **更惊艳的机位**：低角度仰拍、过肩视角、鱼眼/广角透视、大特写混搭全景、前景遮挡营造纵深。
- 构图句示例：`low angle shot, dynamic diagonal composition, Arona leaning in from the left foreground, Plana on the right with cafe lights creating depth`。

## 语言策略心法

- 细节堆 **tag**（模型词表友好、权重可控）；场景/交互/构图用**自然语言**（模型理解句意关系）
- 括号加权 `(xxx:1.1)` 强调关键特征；换装等强需求用 ≥1.5
- **同类 tag 分组换行**（视觉/配饰/服装/鞋），勿大杂烩一长串
- 双人画面**必须**在 ⑤⑥ 层把两人绑定进同一动作 + 明确空间关系（谁在画面左/右、谁上半身入画）

## 常见失误（教训库）

- 只堆两人 tag 不写交互 → 画面只有一个人（模型只抓单主体）
- 有环境无构图 → 背景与人物无空间关系
- ⑤交互句太薄、⑥镜头构图缺失 = "干站桩"的根源
- 角色串后追加错误服装 tag → 覆盖默认外观，人物走样（v1.1）
- 多人画面只罗列角色串、不加身份前缀 → 两人特征融成一人（v1.2）
- 不写总人数 tag（2girl 等）→ 模型搞不清画面有几人（v1.2）
- 中心对称构图 → 画面枯燥（v1.1）

## 版本日志

- **v1.0**：六层结构；三种人物写法；语言策略心法
- **v1.1**：IP 角色串铁律（角色串=默认外观、勿覆盖、换装加权）；镜头构图审美（避中心对称、求灵动惊艳）
- **v1.2**：多人画面身份前缀铁律（the first girl / the girl in the left 等，防特征融合成一人）；总人数 tag（2girl 等）必写

## 本机角色串速查（作者提示词小助手 tags/默认标签.csv）

| 角色 | 串 |
|---|---|
| 守岸人 | `shorekeeper_(wuthering_waves),Shorekeeper from Wuthering Waves` |
| 普拉娜 | `Plana from Blue Archive,plana_(blue_archive)` |
| 阿罗娜 | `Arona from Blue Archive,arona_(blue_archive)` |
| 莉莉丝 | `A gothic princess with long flowing white hair and icy pale skin, red eyes, wearing a black full-body sheer bodysuit covering her from neck to toes with skin-tight sleeves and black gloves, no panties beneath, no panty outline visible through the fabric, over it a silky lingerie evening gown with a bustle at the back, decorated with delicate chains across her shoulders, an underbust chain, a chain across her lower abdomen, and a waist chain, solo, solo_focus, 1girl, young, teenage, petite, slender, small breasts, princess, elegant, noble aura, cold beauty, detailed eyes, perfect face, blush, innocent, gothic, skin not visible, no exposed skin, no arm warmers, no puffy sleeves, sheer fabric, body chains` |
| （更多） | grep `F:\...\prompt-assistant\tags\默认标签.csv` |
