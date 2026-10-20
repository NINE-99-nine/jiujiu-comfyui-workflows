# flux2 图像放大编辑 · 使用守则（guide v1.0）

> 本守则与 `flux2图像放大编辑.json`（UI 格式，skill 内备份，**实际出图不用它**）+ `flux2图像放大编辑_api.json`（API 格式，**实际出图用这个**，由引子 `flux2图像放大编辑_api.py` 调用）配套。
>
> ⚠️ **分工**：`flux2图像放大编辑.json`（不带 API 后缀）仅作 skill 内备份/分享给人类参考（含 SAM3.1 节点、flux2-klein 节点、模型加载器、图2多参考分支的可视化接线）；实际调用靠 `flux2图像放大编辑_api.py` + `flux2图像放大编辑_api.json` 这套。两者不要混用。
>
> 🔒 **两文件边界**：引子只读同 basename 的 API 版 json（`flux2图像放大编辑_api.json`），UI 版物理不可达。**通则见主 skill 核心铁律 0a。**

## 原理（SAM3.1 遮罩 + flux2-klein 编辑）

1. **SAM3.1 遮罩识别**：SAM3_Detect(2) 用 sam3.1 模型(3) 按 5 号遮罩词识别图 1 里的目标区域（如 face / hair / the girl），产出遮罩。
2. **抽取放大**：MaskBlur+(6) 柔化遮罩 → InpaintCropImproved(15) 按遮罩裁剪抽出目标区域并放大。
3. **flux2-klein 编辑**：7 号编辑词 + 裁剪后的图（VAEEncode）经 ReferenceLatent(19/22) 变 conditioning，喂给 KSampler(25)（flux2-klein 9B 模型，5 步 cfg1）编辑。
4. **叠加回原图**：VAEDecode(21) → 亮度对比度(23) → InpaintStitchImproved(24) 把编辑结果拼回原图 → PurgeVRAM/清理 → SaveImage(27)。

## 可控节点（唯一修改面）

**作者已确认的输入节点：** 1（图1）、5（遮罩词）、7（编辑词）、16（图2，默认跳过）、35（图2开启开关）。

| 节点 | 功能 | 引子参数 |
|---|---|---|
| `1` | 图1：要编辑的原图（LoadImage） | `--img1 <本地路径>` |
| `5` | 遮罩区域：SAM3.1 识别范围（**必须英文**：face/hair/clothes/skin/the girl/the boy in the left…） | `--mask "..."` |
| `7` | 编辑内容：给 flux2-klein 的提示词（如 change her expression to…） | `--prompt "..."` |
| `16` | 图2：可选参考图（LoadImage，默认跳过） | `--img2 <本地路径>` |
| `35` | 图2开启开关（GroupIgnoreManager） | `--use-img2` |

其余（33 Lora Manager / 27 SaveImage 保存名）可通过 `--loras` / `--name` 控制。

## 单图 vs 多参考模式

**单图模式（默认）**：只用图1 + 遮罩词 + 编辑词。KSampler[25].positive=[22]/negative=[19] 直连主链。典型用途：**换表情/人物差分**（--img1 原图，--mask "face"，--prompt "change her expression to…"）。

**多参考模式（--img2 + --use-img2）**：注入图2分支 [16]→[14]→[8]→[13]/[12]，重接 [25].positive=[13]/negative=[12]（[13]conditioning=[22]/latent=[8图2]，[12]conditioning=[19]/latent=[8图2]）。以图2作参考、文本控制编辑。典型用途：
- 图1 是风景照（人物很小），把人物换成图2的立绘 → --img2 图2立绘
- 图1 的人物穿上图2的服装（图2是衣服图）→ --img2 服装图

⚠️ 多参考必须 **同时** 传 `--img2` 和 `--use-img2`，否则图2分支不生效（默认单图直连）。

## 提交方式（黑盒引子，agent 只传参数）

引子自动完成 图片上传（本地 → ComfyUI input 目录）→ 内存拼 API（**不落盘**）→ 递交 `execution/comfy_submit.py` → 校验 `node_errors:{}` → 轮询 → 拷贝成品到 `_work/flux2图像放大编辑/` → 打印一行 JSON。

```bash
python flux2图像放大编辑_api.py --img1 "f:/x.png" --mask "face" --prompt "change her expression to a shy blush" --name 人物差分
# 多参考：
python flux2图像放大编辑_api.py --img1 "f:/scene.png" --mask "the girl" --prompt "replace her with the person from image2" --img2 "f:/char.png" --use-img2 --name 换人物
```

- `--img1` 必传（编辑原图）
- `--mask`/`--prompt` 一般必传（编辑才有意义）
- `--img2`/`--use-img2` 可选（多参考）
- `--loras` 可重复改点名条目（默认 active=一致性consis，`flux-2-klein-NSFW` inactive）
- 返回一行 JSON：`{"kind":"image","prompt_id":"…","file":"…\\_work\\flux2图像放大编辑\\<name>_<日期>.png","size":"…"}`

## 注意事项

- **遮罩词必须英文**（SAM3.1 识别），中文无效；用简洁名词/指代（face/hair/clothes/skin/the girl/the boy in the left）。
- **模型大**（seedvr2/flux2-klein 9B），首测建议从单图简单编辑开始，避免一上来大分辨率多参考爆显存。
- 图2分支引子用**接线注入**而非依 UI 的 GroupIgnoreManager（API 无组概念），逻辑等价：单图直连 / 多参考重接。
- 缓存坑：同图同参重复提交命中缓存，换 `--seed`（或改图）破缓存；引子默认 seed=模板原值，可后期加 `--seed` 支持。

## 版本日志

- v1.0（2026-08-31）：作者提供 UI + API 两版 json，建立子技能（引子/guide/两 json）。API 版为单图直连，引子支持 `--img2 --use-img2` 动态注入图2多参考分支。
