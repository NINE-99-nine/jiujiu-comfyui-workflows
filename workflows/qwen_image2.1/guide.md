# qwen_image2.1 子技能 · 使用守则（guide v0.4 · **临时**）

> ⚠️ **临时子技能**：该工作流仍在作者手里迭代。本目录副本是**某一时点的快照**，
> 作者须显式说「更新副本 / 同步新版」时才重新拷贝原件覆盖，并同步改本 guide（节点地图可能变）。
> 加载一律用**本目录副本**，不用原件。

## 副本信息

| 项 | 值 |
|---|---|
| API 模板（引子读这个） | `workflows/qwen_image2.1/qwen_image2.1汇总_api.json` |
| UI 副本（仅供人看/部署参考） | `workflows/qwen_image2.1/qwen_image2.1汇总.json` |
| 原件 · API 版 | `<local_path>` |
| 原件 · UI 版 | `<local_path>` |
| 归档校验 | API `f03d63d06427ab4374d5a704f212fda4`（**v4 · 标准流 20 步**）／ UI `7b0b11a063056878c0a5a30cb0a716a3` |
| 入库 / 换代 | 2026-09-21 入库 ｜ **2026-09-24 模板换代**（扁平节点号 + String 提示词入口） ｜ **2026-10-11 当天先试 turbo、当日弃用 → 换回标准模型 + 默认 20 步** |

模型（模板内定值，不需要改）：`diffusion_models/qwen_image2.1/qwen_image_2.1_int8_convrot.safetensors`（**标准流；不用 turbo**）·
`text_encoders/qwen3vl_8b_int8_convrot.safetensors`（type=`qwen_image`）· `vae/qwen_image_2.1_vae_bf16.safetensors`

## 一、节点地图（v2 扁平编号）

| 节点 | 类 | 作用 |
|---|---|---|
| `568` | ResolutionSelector | 画布尺寸：`aspect_ratio` × `megapixels`（`multiple=36`） |
| `563` | LoadImage | **参考图 1**（编辑目标） |
| `580` | String | **提示词入口**（`579.prompt` ← `580.String`） |
| `579` | TextEncodeQwenImage21 | `negative_prompt` / `resolution`（参考图像素预算）/ `images.image_N` |
| `577` | ComfySwitchNode | 画布来源开关：True=文生图 / False=编辑 |
| `576` | KSampler | `seed` / `steps`(**模板 20**) / `cfg`(1) / euler+simple |
| `578` | QwenImage21Cache | `device`(模板 auto) / `dtype` —— A770 显存旋钮 |
| `574` / `575` | EmptyLatentImage / VAEDecode | 空 latent 与解码 |
| `569` | SaveImageAdvanced | `filename_prefix`（成品落盘） |
| `567` / `570` | PreviewImage / Image Comparer | UI 用；**570 由引子提交前删掉** |

## 二、两用机关：一个开关定「画布从哪来」

`ComfySwitchNode[577]` 决定 KSampler 的 latent 从哪来：

| switch | latent 来源 | 效果 |
|---|---|---|
| **True** | `EmptyLatentImage[574]` ← `ResolutionSelector[568]` | 画布 = `[568]` 的 aspect_ratio × megapixels（文生图**或**图生图开 `--custom-size`） |
| **False** | `TextEncodeQwenImage21[579]` 的**第 3 路输出 latent** | 画布跟随参考图 image_1（图生图默认） |

`TextEncodeQwenImage21` 的三路输出＝ `positive` / `negative` / `latent` —— 第三路就是被开关引用的那路。

**判据只有一个：不传参考图 → 文生图（switch True）；传了参考图 → 编辑（switch False）。** 没有 `--mode`，无需手动切。

🔴 **图生图同样能自定义输出画布**：加 `--custom-size` 就把 switch 抢成 True，画布交给 `[568]`。
官方 Note 原文：`custom_size off: canvas comes from the encode latent (image_1)` ／ `custom_size on: use ResolutionSelector width/height. Keep it close to the resized image_1 size, or the edit can shift.`
→ **自定义尺寸要贴近参考图缩放后的大小，否则编辑会偏移。**

⚠️ `--resolution` 只管**输入侧**（参考图喂多大），**不决定输出画布**。

## 三、多图参考（本工作流关键设计）

`TextEncodeQwenImage21` 的 `images` 是 **AUTOGROW 输入组**：节点声明 `image_1` … `image_16`（`min: 0`）。

- API 里**直接写键** `images.image_1`、`images.image_2` … 接 `LoadImage` 的输出即可。
- **不需要** flux2 那套 `VAEEncode` + `ReferenceLatent` 层层串接 —— 这是它比 flux2 编辑流干净的地方。
- **图 1 = 编辑目标**（模板走 `563 LoadImage`）；图 2…N 是参考。
- 官方模板文档只标「最多 10 张」，但**节点实际声明到 16**；引子按 16 上限做校验。
- 引子会自动为图 2…N 补 `LoadImage` 节点并接进 `images.image_N`（从 image_2 起连续编号）。
- 🔴 v2 模板**没有** `ImageScaleToTotalPixels` 节点：参考图统一缩放改由 `579.resolution`（像素预算）在编码器内部完成，引子也不再传 `--ref-mp`。

`resolution[579]`（**引子默认 1024**）：所有参考图被缩放到约 `resolution × resolution` 像素（保比例）；**0 = 每张保持各自原尺寸**。

⚠️ 这个参数在**输入侧**：它决定模型"看"到多大的参考图（也直接决定显存占用），**不决定输出画布**。想用大画布又要省显存，就是 `--resolution 1024 --custom-size --megapixels 2.0` 这个组合。

## 四、引子参数表（agent 只传这些）

```bash
python workflows/qwen_image2.1/qwen_image2.1汇总_api.py --prompt-file 词.txt
```

| 参数 | 默认 | 作用 | 落到节点 |
|---|---|---|---|
| `--prompt` / `--prompt-file` | 必填（二选一） | 提示词；长稿、含引号、多段一律走 file | `580.String` |
| `--images a.png,b.png` | 无 | 参考图（逗号分隔，可重复传参累加，最多 16 张）；**第 1 张＝编辑目标** | `563` ＋ 动态 `images.image_N` |
| `--ratio` | 模板 9:16 | 画布比例（8 档：1:1 / 2:3 / 3:2 / 3:4 / 4:3 / 9:16 / 16:9 / 21:9）；文生图，或图生图开了 `--custom-size` 时。🔴 **必须传完整枚举串** | `568.aspect_ratio` |
| `--megapixels` | 模板 2.0 | 画布总像素；文生图，或图生图开了 `--custom-size` 时 | `568.megapixels` |
| `--custom-size` | 关 | 🔴 图生图时把画布交给 `[568]`（`--ratio`×`--megapixels`），不再跟随参考图 | `577.switch` |
| `--resolution` | **1024** | 参考图统一缩放上限（像素预算）；`0`＝各自原尺寸 | `579.resolution` |
| `--steps` | **模板 20** | 采样步数。🔴 **默认 20（标准流）**——用户没额外说明就用 20；用户明说、或这张确实需要更精致（精细排版、文字点多）时才提高 | `576.steps` |
| `--cfg` | 模板 1 | cfg（官方路径保持 1） | `576.cfg` |
| `--seed` | `-1` 随机 | 固定复现用具体值 | `576.seed` |
| `--cache-device` | 模板 auto | `auto/gpu/cpu/off`：显存缓存位置（OOM 时先动它） | `578.device` |
| `--cache-dtype` | 模板 default | `default/int8/int4`：缓存存储精度 | `578.dtype` |
| `--name` | output | 成品名（自动加 `日期/` 目录） | `569.filename_prefix` |
| `--dry-run` | — | 只打印将提交的改动摘要，不提交 | — |

**没有负面提示词参数** —— cfg=1 时 `negative_prompt` 不生效，故不暴露。
**没有 `--ref-mp`** —— v2 模板已无 `ImageScaleToTotalPixels`，缩放统一走 `--resolution`。

提交方式：引子自动 内存拼 API（**不落盘**）→ `execution/comfy_submit.py` → 校验 `node_errors:{}` → 轮询 → 拷成品到 `_work/qwen_image2.1汇总_api/` → 打印一行 JSON `{"kind":"image","prompt_id":…,"file":…,"size":…}`。

## 五、提示词怎么写

→ 见同目录 **`prompting.md`（提示词编写指南 v1.0）**：语言/语法、五段结构骨架、写实与二次元的分野、角色还原、编辑模式写法、文字渲染、已验范式索引、常见翻车对照表。

## 六、qwen_image2.1 出图经验

1. **语言**：中文母语级，中文**文字渲染强于英文** —— 嵌字一律优先中文。
2. **语法**：段落式自然语言，不是 tag 堆砌（CLIP 是 Qwen3VL-8B）。官方支持 **1k token 级指令**，短提示词只会给"通用图"，越长越准。
3. **角色还原**：🔴 **它不认 danbooru 角色串**（`sensei` 之类对它无效）。非原创角色必须**把参考图里人物的样貌写进提示词**（发色/瞳色/服装款式逐项），再配合 `--images` 传参考图。
4. 🔴 **步数（铁律，2026-10-11 作者定 · 当日第二次修订）**：cfg=1、euler+simple。**默认 20 步**——这是标准模型（非 turbo）的稳妥档，质量与耗时的平衡点。步数规则：
   - **用户没额外说明 → 直接用默认 20 步**（不要自己加）
   - 用户明说步数 → 照做（如「40 步」）
   - 这张确实需要更精致（精细排版、文字点多、细节密集） → **可以适度提高**（30～40），**但要先说明、并在汇报里写清用了多少步**
   - **禁止静默抬高到 40/50**：历史上多次默认提到 40/50 步，用户白等很久，还一度以为是电脑故障
5. **尺寸**：**输出画布**文生图由 `[568]` 定（`--ratio` × `--megapixels`），图生图默认跟随 image_1、开 `--custom-size` 后交回 `[568]`。模型原生 2K、上限 4MP。
   常用档（实测）：**2.5K 横屏 = `16:9` + 3.7MP → 2624×1472**；3:4 + 1.6MP → 1120×1504；2:3 + 1.6MP → 1040×1584。
6. **透明底**：物料写 `This is an RGBA format image with transparency. [主体描述]. The image has an alpha channel and a transparent background.`，存 PNG 才留得住 alpha。
7. **长稿排版**（海报/人设卡/图鉴）：把"哪里写什么字"逐处写清，并给字号层级；文字点越多越容易崩，**按骨架级/内容级/装饰级分级投放**，崩了从装饰级往回砍。

## 七、Pitfalls（踩过的坑）

1. 🔴 **文生图时必须摘掉参考图**：只要 `images.image_1` 还挂在 `TextEncodeQwenImage21` 上，文本编码器仍会"看见"那张图并拼进序列 → 出图被污染。**引子在不传图时会自动 `pop` 该键，并删除 `563 LoadImage`**（否则它会去加载模板里残留的样本图名而报错）。手搓 API 时切记两件事都做。
2. 🔴 **图生图默认吃不到 `[568]` 的尺寸**（踩坑最常见的一条）：只要传了参考图，引子就把 switch 置 False，画布只能跟随 image_1；`--ratio` / `--megapixels` 这时**完全无效**，必须显式加 `--custom-size` 才会生效。
3. 🔴 **`--ratio` 必须传完整枚举字符串**：`--ratio "2:3 (Portrait Photo)"`、`--ratio "3:2 (Photo)"`。只传 `2:3` / `3:2` 会被 argparse 判 `invalid choice` 直接退出（整批任务连图都没提交）。八档全名：`1:1 (Square)` / `2:3 (Portrait Photo)` / `3:2 (Photo)` / `3:4 (Portrait Standard)` / `4:3 (Standard)` / `9:16 (Portrait Widescreen)` / `16:9 (Widescreen)` / `21:9 (Ultrawide)`。
4. 🔴 **提示词走 `580 String` 节点**（v2 改动）：`579.prompt` 是连接输入，直接写 `579.prompt` 无效；引子已改为注入 `580.String`。
5. **`570 Image Comparer` 提交前一律删掉**：它引用模板残留的临时图 URL 与 `563`，agent 出图不需要它；引子在 `build()` 里无条件 `pop`。
6. **实测规律（2026-09-22 + 2026-09-24 复测）**：图生图不开 `--custom-size` 时，**画布总像素 ≈ `resolution²`**（`--resolution 1024` → 出 1376×768 ≈ 1.06MP；`--resolution 1280` → 出 1696×960 ≈ 1.63MP）。要把画布抬到 2MP 必须开 `--custom-size`；硬顶 `resolution`（如 1414）只会撞 `TextEncodeQwenImage21` OOM。
7. **多图键名**：`images.image_N` 从 1 起连续编号，N 与 `LoadImage` 一一对应；漏号/重号会接线失败。
8. **显存**：`QwenImage21Cache[578]` 是 A770 16GB 上的关键旋钮（`device=cpu` 把 cache 放内存、`dtype=int8` 省一半显存）；OOM 时先动它，再降参考图数量/像素。v2 模板默认 `device=auto`。
9. **本子技能是临时的**：不要随作者原件实时同步副本；也不要因为"看起来不完善"就自己去改模板 json —— 模板只读，改动只进引子的注入逻辑。

## 八、验证记录

- 2026-09-21：旧版引子（`459:*` 节点组）零副作用自检通过。
- **2026-09-24（v2 模板换代后）**
  - `--dry-run` 三模式全通过：①无图 → `t2i` / switch=True / `image_1` 已摘除 / nodes=13 ②单图 → `edit` / `images.image_1` / nodes=14 ③双图 → `edit` / `images.image_2` 注入成功 / nodes=15；三组 `has_comparer:false`。
  - **真实出图端到端通过**：①文生图 `1:1` + 1MP → **1008×1008** ②编辑（参考图 + `--resolution 1024`）→ **1376×768**（≈1024²，与"画布≈resolution²"规律一致）。
  - 实测产出：`2:3` + 1.6MP → 1040×1584；`3:4` + 1.6MP → 1120×1504；`16:9` + 3.7MP → 2624×1472（人设图）。

## 九、版本日志

- v0.1（2026-09-21）：临时子技能首建。拷贝作者的 API 导出 + UI 工作流；新写多图注入引子（auto 双模式、无负面参数、参考图统一 1280）；零副作用自检通过。
- **v0.4（2026-10-11）：弃用 turbo，换回标准模型 + 默认 20 步。** 作者实测后判定 turbo 版效果不如预期（原以为"更好更快"，实际质量反而差），当日回退：模板 `[571] UNETLoader.unet_name` → `qwen_image_2.1_int8_convrot.safetensors`（**标准流**，同目录）；`[576] KSampler.steps` 8 → **20**；引子 `--steps` 帮助文本同步。**步数铁律改写为「默认 20；无额外说明用 20，用户明说或确实更精致时才提高，且不得静默改」**（见第六节第 4 条）。prompting.md、词汇库 `qwen_image2.1/`（README / 01 / 02 / 03）同步改口。API 模板 MD5 `4f10934e…` → `f03d63d0…`（＝ v0.3 之前的原值）。
- **v0.3（2026-10-11）：换 turbo 模型 + 默认 8 步（已被 v0.4 回退）。** 模板 `[571] UNETLoader.unet_name` → `qwen_image_2.1_turbo_int8_convrot.safetensors`（同目录，官方快速流）；`[576] KSampler.steps` 20 → **8**；引子 `--steps` 帮助文本同步。**新增步数铁律：默认 8，提高必须经用户同意**（见第六节第 4 条）。API 模板 MD5 `f03d63d0…` → `4f10934e…`。
- **v0.2（2026-09-24）：模板换代。** API 模板换为作者新版（扁平 `563/568/569/570/576~580` 节点）。引子同步重写：提示词改注入 `580.String`；参考图缩放改由 `579.resolution` 统管（删 `--ref-mp`）；无图时连 `563 LoadImage` 一起摘除；`570 Comparer` 无条件删除；`--resolution` 默认改 1024；补节点地图、三模式 dry-run 与真实出图验证；新增 `prompting.md` 提示词编写指南。
