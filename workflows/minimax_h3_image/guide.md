# MiniMax H3 Image · 子技能使用守则（guide v1.1，2026-11-17）

> 两个工作流共用一套规则：**文生图**（t2i）与**图生图 / 图像编辑**（edit）。
> 加载与执行一律走本目录副本 + 对应引子，不用原件。

## 〇 · 副本信息

| 项 | 文生图 | 图像编辑 |
|---|---|---|
| API 模板 | `minimax_h3_image_t2i_api.json` | `minimax_h3_image_edit_api.json` |
| 引子 | `minimax_h3_image_t2i_api.py` | `minimax_h3_image_edit_api.py` |
| 来源 | 作者「导出(API 格式)」 | 作者「导出(API 格式)」 |
| 归档 MD5 | `ADFD229A0A7394A3D5920BEB31BD71D1` | `21C59596F5FF6436057534A071DAB2E9` |
| 体量 | 9 229 B / 14 节点 | 12 045 B / 36 节点 |
| 入库 | 2026-11-17 | 2026-11-17 |

静态原则：副本是快照，**不随原件实时更新**；作者说「同步新版」才重拷并同步本 guide。

## 一 · 文生图节点地图（14 节点）

| ID | class_type | 作用 | 引子是否碰 |
|---|---|---|---|
| 102 / 103 / 104 | UNETLoader / CLIPLoader / VAELoader | H3 int8 三件套 | ❌ |
| **105** | PrimitiveStringMultiline | 提示词入口（`.value`） | ✅ |
| 108 | MiniMaxH3ImageConditioning | 提示词 + 宽高 → CONDITIONING + LATENT | ❌（宽高由 138 供线） |
| 109 | ConditioningZeroOut | 负向条件 | ❌ |
| 170 | LoraLoaderModelOnly | 尘星 LoRA @ 0.8（固定） | ❌ |
| **120** | KSampler | seed / 6 步 / cfg 1 / lcm / sgm_uniform | ✅ 只写 seed |
| 123 | VAEDecode | 解码 | ❌ |
| **124** | ImageScaleToTotalPixels | 出图按总像素缩放 | ✅ |
| **127** | SaveImage | 落盘 | ✅ |
| 132 | PreviewImage | 预览（不落盘） | ❌ |
| **138** | ResolutionSelector | 比例 + 总像素 → 宽高（`multiple=32`） | ✅ |
| 122 | PrimitiveBoolean | `Enable PE?` —— **悬空残留，无人引用** | ❌ |

## 二 · 图像编辑节点地图（36 节点）

| ID | class_type | 作用 | 引子是否碰 |
|---|---|---|---|
| 29 / 30 / 31 | UNET / CLIP / VAE | 同文生图 | ❌ |
| **43** | PrimitiveStringMultiline | 提示词入口 | ✅ |
| **32** | MiniMaxH3ImageConditioning | prompt / width / height / `images.image_N` | ✅ |
| 33 | ConditioningZeroOut | 负向 | ❌ |
| 142 | LoraLoaderModelOnly | 尘星 0.8 固定 | ❌ |
| **38** | KSampler | seed / 6 步 / cfg 1 / lcm | ✅ 只写 seed |
| 42 | VAEDecode | 解码 | ❌ |
| **63** | ImageScaleToTotalPixels | 出图缩放 | ✅ |
| **9** | SaveImage | 落盘 | ✅ |
| **90** | LoadImage（底图） | 提示词里的「图1」 | ✅ 写文件名 |
| 91 | ResizeImageMaskNode | 底图预缩放 **12MP**（area） | ❌ 固定 |
| 92 | ResizeImageMaskNode | 对齐 32 倍数 | ❌ 固定 |
| **93 / 96 / 99 / 139 / 149 / 145 / 146 / 147 / 148 / 150** | LoadImage | 图2 / 图3 / 图4 / 图5 / **图6** / 图7 / 图8 / 图9 / 图10 / 图11 | ✅ 写文件名 |
| **171** | ResizeImageMaskNode | 输入前缩放（底图 1.2MP） | ✅ 挂到 image_0 |
| **172…181** | ResizeImageMaskNode | 输入前缩放（参考 1.5MP） | ✅ 挂到 image_1…image_10 |
| **164** | GetImageSize（←92） | 底图实际宽高 | ✅ (base 模式供 32) |
| **162** | PrimitiveFloat | custom 模式的像素数（8） | ✅ |
| **165** | ResolutionSelector | custom 模式比例 + 32 对齐 | ✅ |
| 168 | EmptyLatentImage | custom 模式画布 | ❌ |
| **169** | ComfySwitchNode | `false`=底图 latent / `true`=自定义 | ✅ |
| 61 | PrimitiveBoolean | `Enable PE?` 悬空残留 | ❌ |

## 三 · 参数面

### 文生图

```
python minimax_h3_image_t2i_api.py --prompt-file 词.txt [--ratio 21:9 --mp 8 --out-mp 2.5 --name 名字 --seed -1]
python minimax_h3_image_t2i_api.py --prompt "短词" --dry-run
```

| 参数 | 落到 | 默认 |
|---|---|---|
| `--prompt` / `--prompt-file`（互斥必填） | 105 `.value` | 模板长示例 |
| `--ratio` / `-r` | 138 `.aspect_ratio` | `21:9 (Ultrawide)` |
| `--mp` | 138 `.megapixels` | 8（合法 0.1~16） |
| `--out-mp` | 124 `.megapixels` | 2.5（合法 0.01~16） |
| `--name` | 127 `.filename_prefix` | `日期/成品名` |
| `--seed` | 120 `.seed` | -1 随机 |
| `--dry-run` | — | 只看改动与预计尺寸 |

### 图像编辑

```
python minimax_h3_image_edit_api.py --img1 底图.png --ref 图2.png --ref 图3.png --prompt-file 词.txt \
       [--ratio 3:4 --mp 8 --out-mp 2.5 --name 名字 --seed -1]
python minimax_h3_image_edit_api.py --img1 底图.png --prompt "…" --dry-run
```

| 参数 | 落到 | 说明 |
|---|---|---|
| `--img1`（必填） | 90 `.image` | 底图 = 提示词里的「图1」，先上传到 ComfyUI input |
| `--ref`（可重复 ≤10） | 93/96/99/139/149/145/146/147/148/150 + 172…181 | 第 1 个=图2、第 2 个=图3 … 第 10 个=图11；自动挂 `32.images.image_N` |
| `--mode` | 169 `.switch` | `base`（默认，用底图比例/尺寸）/ `custom`；不传时给了 `--ratio` 或 `--mp` 就自动 custom |
| `--ratio` / `-r` | 165 `.aspect_ratio` | 仅 custom；8 个合法值同文生图 |
| `--mp` | **162 `.value`** | 仅 custom；默认 8，0.1~16 |
| `--out-mp` | 63 `.megapixels` | 默认 2.5 |
| `--prompt` / `--prompt-file` | 43 `.value` | 长文一律走文件 |
| `--name` / `--seed` / `--dry-run` | 9 / 38 / — | 同上 |

**故意不暴露**（两个工作流共享）：`steps=6`、`cfg=1`、`sampler=lcm`、`scheduler=sgm_uniform`、`denoise=1`、`multiple=32`、`resolution_steps=1`、`upscale_method=nearest-exact`、LoRA（尘星 0.8 固定）、`91` 的 12MP 预缩放、`171…181` 的 1.2/1.5MP 预缩放。

## 四 · 分辨率机制（本模型最反直觉的地方）

1. **宽高必须 32 的倍数**：条件节点的 `width/height` 定义就是 `step=32`，描边写明模型按 **2048×2048 面积**调优。取整全交给节点的 `multiple=32`，引子另算一遍预估并打印。
2. **总像素 8MP 起步，上限 16MP**：别家 2MP/4MP 正常，这里**太小就糊、明显低质**。
3. **`--out-mp` 是第二道缩放**：默认 2.5 < 生成 8，即成品是**降采样**。要原生清晰度给 `--out-mp 8`（或与 `--mp` 相同），上限 16。
4. **文生图**：尺寸由 138 一节点决定（`108` 的宽高被 138 占线，写它无效）。
5. **图像编辑两个模式**：
   - `base`：`169=false`，画布 = 32 吐出的底图 latent（底图经 91 缩到 12MP + 92 对齐 32，再由 164 取尺寸）。**不传 `--ratio/--mp`**。
   - `custom`：`169=true`，画布 = 165+168。此时本引子**把 32 的宽高也从 164 切到 165**，保证「条件尺寸 = 画布尺寸」（作者 2026-11-17 拍板）。
   - custom 的像素数必须写 **162**（`165.megapixels` 已被 `[162,0]` 占线，写 165 无效）。

## 五 · 多图输入规则（编辑版）

- **`32.images` 是 AUTOGROW 输入**：键名 `images.image_0`、`images.image_1` …，上限 100。
- **键名 0 基、提示词 1 基**：`image_0` = 提示词里的「图1」= 底图；`image_1` = 图2 … `image_10` = 图11。写提示词时按这个编号引用。
- **一律挂「输入前缩放」节点（171…181），绝不直接连 LoadImage**：原图可能很大，先缩到 1.2/1.5MP 再进条件节点，既省显存又几乎不掉画质。
- 模板槽位 = **11 张**（1 底图 + 10 参考）。**模型本身支持 16 张**（作者 2026-11-17 说明），但 A770 上两张就已经很吃力；要更多得克隆 LoadImage + 缩放节点（属新增节点，需作者点头，引子不擅自加）。

## 六 · 提交链路

1. 引子读同 basename 模板 → 内存改 → `execution/comfy_submit.py`
2. `node_errors:{}` 校验 → 轮询 `/history` → 成品拷到 `_work/<引子名>/`
3. 只输出一行 JSON：`{"kind":"image","prompt_id":…,"file":"…","size":"WxH"}`

## 七 · Pitfalls

- **别改条件节点的宽高**（t2i 的 108 / edit 的 32）：前者被 138 占线，后者由引子按模式切——手改必被覆盖。
- **别指望 122 / 61（Enable PE?）**：两个模板里都是悬空残留，填 true 也不会触发任何增强。
- **别把 `--mp` 调到 4 以下**：不是省时间，是直接出糊图。
- **忘了 `--out-mp`**：默认 2.5 会把 8MP 结果缩小落盘，「不够清晰」先查这里。
- **base 模式别传 `--ratio/--mp`**：会直接报错（要自定义就加 `--mode custom`）。
- seed 必须引子自己写：`comfy_submit` 只处理 `class_type` 以 `Seed` 开头的节点的 seed，KSampler 不在其列。
- 编辑版的 10 个参考槽位在模板里带着样本图片名（其中图9 是 `%Empty Latent Image.width%x…` 这种占位串）；不用它们时不接线就不会执行，但**一旦接线就必须改文件名**，否则会去加载不存在的图。

## 八 · 提示词写法

两套写法在同目录 `prompting.md`：**第一部分 文生图 / 第二部分 图像编辑**。写提示词前先读对应部分。
编辑篇的指代用 `<Picture 1>` 这类官方写法（本机条件节点 tooltip 明确认这个），中文「图1」同样可用，同一份里不混用。
