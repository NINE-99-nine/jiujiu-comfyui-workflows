# qwen_image2.1 局部放大编辑 · 使用守则（guide v1.0）

> 本守则与三件配套：`qwenimage2.1局部放大编辑.json`（UI 版，**仅供人看/部署参考**）、`qwenimage2.1局部放大编辑_api.json`（API 版，**引子读这个**）、`qwenimage2.1局部放大编辑_api.py`（引子，agent 只传参数）。
> 🔒 引子物理上只读同 basename 的 API 版，UI 版摸不到（通则见主 skill 铁律 0a）。

## 这个流做什么

只改原图的一块：先在原图里定位目标，把那一块裁出来放大，只对这块做高分辨率编辑，最后无缝拼回原图，其余像素不动。

## 原理链路（五步）

```
图1[8] ─► SAM3.1[9 ─ 16，检索词 25] ─► 遮罩
                                        │
                     InpaintCropImproved[13]（裁出遮罩区域，带 1.2 倍上下文；输出缩放至目标尺寸=关）
                                        │  ├─ 第 1 路 stitcher ─────────────┐
                                        │  └─ 第 2 路 cropped_image        │
                                        ▼                                  │
              TextEncodeQwenImage21[6].images.image_1 ─► positive / negative / latent
                 prompt ← String[4]                                    │
                          │                                            │
              KSampler[18]（latent 来自 6 号第 3 路，20 步 / cfg 1 / euler+simple）
                          ▼                                            │
              VAEDecode[19] ─► Image to RGB[30] ─► 亮度对比度[14] ──────┤
                                                                       ▼
                                              InpaintStitchImproved[15] ─► SaveImageAdvanced[21]
```

**关键机关**：`ComfySwitchNode[11]` 的 `switch=false` → KSampler 的 latent 吃 `TextEncodeQwenImage21[6]` 的**第 3 路 latent**，也就是**裁剪块缩放后的尺寸**。所以「画布」不是 ResolutionSelector 给的，是裁剪块给的——这正是放大编辑要的：只画那一块，且画布足够大。

## 节点地图

| 节点 | 类 | 作用 |
|---|---|---|
| `1` | UNETLoader | qwen_image_2.1_int8_convrot |
| `2` | LoraLoaderModelOnly | qwen-image-2.1-uncensored-lora @1.0（`--lora-strength` 可调） |
| `3` | CLIPLoader | qwen3vl_8b_int8_convrot（type=qwen_image） |
| `4` | String | **编辑指令**入口（→ `6.prompt`） |
| `5` | VAELoader | qwen_image_2.1_vae_bf16 |
| `6` | TextEncodeQwenImage21 | prompt / negative_prompt / resolution / `images.image_1…16`（AUTOGROW） |
| `7` | ResolutionSelector | 9:16 × 1.6MP（**本流不生效**：11 号开关=false 时 `10` 被旁路） |
| `8` | LoadImage | **要编辑的原图（图1）** |
| `9` | CheckpointLoaderSimple | sam/sam3.1_multiplex_fp16 |
| `10` | EmptyLatentImage | 旁路（见 `7`） |
| `11` | ComfySwitchNode | switch=false → latent 跟裁剪块 |
| `12` | ImageAndMaskPreview | 预览遮罩（绿框），调检索词时看它 |
| `13` | InpaintCropImproved | 裁出遮罩区（**自适应当前比例**，`output_resize_to_target_size=false`；context 1.2 / blend 32 / 输出两路） |
| `14` | BrightnessContrastV2 | 1 / 1.1 / 1.06（模板定值） |
| `15` | InpaintStitchImproved | 把编辑结果按 stitcher 拼回原图 |
| `16` | SAM3_Detect | 按 25 号检索词出遮罩（threshold 0.5 / refine 2） |
| `17` | QwenImage21Cache | auto（XPU 显存旋钮，模板不暴露） |
| `18` | KSampler | seed / steps 20 / cfg 1 / euler / simple / denoise 1 |
| `19` | VAEDecode | 解码 |
| `21` | SaveImageAdvanced | 成品落盘（`--name`） |
| `25` | CLIPTextEncode | **SAM3.1 检索词（必须英文）** |
| `28` | PreviewImage | 预览裁剪块 |
| `30` | Image to RGB (RvTools) | 去 alpha |

UI 版另带四个备用 `LoadImage`（22/23/24/26，全部置为 bypass），是作者在界面里手动接多图参考的预留位；API 版不导出它们，多图由引子动态补节点。

## 可控节点（唯一修改面）

| 节点 | 功能 | 引子参数 |
|---|---|---|
| `8` | 要编辑的原图 | `--img1 <路径>`（必传） |
| `25` | SAM3.1 检索词（**英文**） | `--mask "the girl"`（必传） |
| `4` | 编辑指令 | `--prompt "…"`（必传） |
| `6.images.image_2…16` | 多图参考（引子动态补 LoadImage） | `--ref <路径>`（可重复/逗号，≤15 张） |
| `6.resolution` | 编辑画布边长 | `--canvas 1024` |
| `13.mask_expand_pixels` | 遮罩外扩 | `--mask-expand 0` |
| `13.context_from_mask_extend_factor` | 上下文松紧 | `--context 1.2` |
| `18` | seed / steps / cfg | `--seed -1` / `--steps 20` / `--cfg 1` |
| `17` | Cache 位置 | `--cache off` |
| `2` | LoRA 强度 | `--lora-strength 1.0` |
| `21` | 保存名 | `--name` |

## 提交方式（黑盒引子）

```bash
cd <技能根>
# 单图：只改其中一块
python workflows/qwenimage2.1局部放大编辑/qwenimage2.1局部放大编辑_api.py \
  --img1 "<local_path>" --mask "the girl" --prompt "把她的裙摆改成正红色亮片，其余保持不动" --name 裙摆改亮片

# 多图：换装 / 换人 / 带参考
python workflows/qwenimage2.1局部放大编辑/qwenimage2.1局部放大编辑_api.py \
  --img1 "<local_path>" --mask "the dress" --prompt "把图1的裙子换成图2那件，版型与配色照图2" \
  --ref "<local_path>" --name 换装

# 更细：画布与裁剪块一起抬（吃显存）
python workflows/qwenimage2.1局部放大编辑/qwenimage2.1局部放大编辑_api.py \
  --img1 "<local_path>" --mask "her face" --prompt "…" --canvas 1536 --name 脸部精修
```

引子自动：上传本地图 → 内存拼 API（**不落盘**）→ `execution/comfy_submit.py` → 校验 `node_errors:{}` → 轮询 → 拷成品到 `_work/qwenimage2.1局部放大编辑/` → 打印一行 JSON。
输出：`{"kind":"image","prompt_id":…,"file":"…<name>_<日期>.png","size":"…"}`。

## 多图怎么生效（本子技能的关键扩展）

`TextEncodeQwenImage21` 的 `images` 是 **AUTOGROW 组**（声明 `image_1`…`image_16`，min=0）：

- 引子为每张 `--ref` 补一个 `LoadImage` 节点，把输出接进 `images.image_2`、`image_3`…（**不需要** flux2 那套 `VAEEncode`+`ReferenceLatent`）。
- `image_1` 永远是**裁剪块**（节点 13 第 2 路输出）＝编辑目标兼画布来源；`--ref` 的图只作参考，不改变画布。
- 编码器按 `Picture 1 / Picture 2 / …` 顺序塞进序列，所以提示词里**用「图2」「picture 2」直接指代**即可。
- 上限：`image_2`…`image_16` = 15 张；超了引子直接退出。
- 所有图（含裁剪块）被 `6.resolution` 统一缩放到约 `canvas × canvas` 像素（保比例）——这就是 `--canvas` 同时控「编辑清晰度」和「显存」的原因。

## 提示词怎么写

**① 编辑指令（`--prompt`，节点 4）** —— 照 `workflows/qwen_image2.1/prompting.md` 第二节「图像参考编辑」，写明三件事：

1. **指哪张图**：单图写「图1里」「画面中」；多图逐图编号（图1 / 图2）。
2. **改什么**：具体到材质、颜色、款式、字。qwen2.1 中文母语级，长句比短句准。
3. **其余如何**：明写「其余部分保持不变 / 构图、光线、脸都不动」，这句能显著减少整块漂移。

例：`把图1里她的丝袜改成带蕾丝花边的黑色亮面连裤袜，袜口加一圈缎带蝴蝶结，其余部分（姿势、裙摆、地板、光线）完全保持原样。`

**② 检索词（`--mask`，节点 25）** —— 给 SAM3.1 找「改哪一块」：

- **必须英文**，中文直接无效。
- 用可观察的名词短语：`the girl` / `her face` / `the stockings` / `the dress` / `the left hand` / `the shoes`。
- 多目标要区分方位：`the girl on the left` / `the girl on the right`（同画面两人时必须写方位，否则只框中最显眼那个）。
- 别写抽象词（`beautiful`、`the mood`）、别写中文、别写完整句子。
- 框范围由 `13` 的 context（1.2 倍外扩）决定，想多带周边调 `--context 1.3`，想让模型只看到目标本体调 `--context 1.1`。

**③ 指令与检索词的配合**：检索词定「框」，指令定「框里怎么改」。指令里再提一次要改的物件（「她的丝袜」）比只写「改成红色」稳。

## 常用档速查

| 想做的事 | 参数组合 |
|---|---|
| 材质/配色微调 | `--mask "the skirt" --prompt "改成…，其余不变"` |
| 局部换装 | `--mask "the dress" --prompt "换成图2那件" --ref 衣服图` |
| 换人（图1 人物小） | `--mask "the girl" --prompt "换成图2的人物，样貌与发色照图2" --ref 立绘` |
| 面部精修 | `--mask "her face" --canvas 1536 --crop-size 1536 --context 1.15` |
| 只改一块但周边更松 | `--context 1.4 --mask-expand 32` |

## 注意事项（Pitfalls）

1. 🔴 **检索词必须英文**，中文 SAM3.1 认不出 → 空遮罩 → 裁不到东西直接报错或出鬼图。调词时看 `12` 号预览的绿框。
2. 🔴 **成品尺寸 = 原图尺寸**，不是 canvas。canvas 只决定「编辑时用多大分辨率画那一块」，画完按 stitcher 缩回原图位置。所以想看清细节，得原图本身够大。
3. **canvas 决定编辑清晰度**：`6.resolution` 把裁剪块缩放到约 canvas × canvas 像素（保比例），小裁剪块被拉大＝局部放大；canvas 越大越细，也越吃显存。
4. `7`/`10`/`11` 这条旁路**不要动**：把 `11.switch` 改 true，画布就变成 `7` 的 9:16×1.6MP，局部编辑会整体错位。
5. `14` 亮度对比度（1 / 1.1 / 1.06）是模板定值：整块拼回后局部会略偏亮偏艳，改它要同步预期颜色。
6. **同图同参重跑命中缓存** → 换 `--seed`；`--seed -1` 是随机，具体值可复现。
7. **显存**：qwen2.1 int8 + sam3.1 + 多参考一起上 A770 16G 会紧。顺序：先降 `--canvas`（1024 → 896），再减 `--ref`。
8. `--img1` 是**要编辑的原图**，别传裁剪块（裁剪由 13 号做）。
9. `--ref` 多张时给每张编号说明（「图2 是衣服、图3 是鞋」），只丢图不给指代，模型会混。
10. 保存前缀由 `--name` 决定（自动加 `日期/` 子目录），产成品同时拷一份到 `_work/qwenimage2.1局部放大编辑/`。
