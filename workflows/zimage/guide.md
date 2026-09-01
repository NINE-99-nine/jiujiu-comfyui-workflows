# z image 工作流 · 使用与提示词指导（v2.0，2026-08-19 优化版）

## 工作流概览
- **模型**：Z-Image-Turbo 双 UNET（644 GGUF `z-image-turbo-Q8_0.gguf` 作 base + 666 int8_convrot 作 turbo）+ CLIP **V6**（101 `Z-Image-Engineer-V6-Q8_0.gguf`，lumina2）
- **文件**（本目录）：
  - `zimage_full_template.json` = **作者 ComfyUI 内置导出的 API 版**（28 节点，2026-08-19 优化版，唯一合法模板）
  - `z image.json` = 工作流原件副本（UI 版，2026-08-19 14:00 同步）
- 链路：636 提示词 → 633 拼接（+628 LoRA 文本）→ 5 正面编码；**12 两阶段采样**（12 base 9 步 cfg2 `res_multistep/simple` 保留噪声 → 13 turbo 9 步 cfg1 接 666 模型）；660 VAEDecodeTiled 分块解码；35 保存

## 可编辑节点（仅三处，其余一律不碰）
| 节点 | 类型 | 作用 |
|---|---|---|
| **636** | PrimitiveStringMultiline | 提示词（中英文直输，四段式） |
| **629** | ResolutionMasterSimplify | 分辨率宽高 |
| **628** | Lora Loader (LoraManager) | LoRA 管理——**默认配置勿动**：skin texture v4.5(0.50) + Z-Detail-Slider(1.50) active；Comics_Factory / NSFW_master 为 inactive。需换画风时经作者指示再改 |

## 分辨率规则
- **629 设置多少，最终就是多少——无二次放大**（与 anima 的 ×1.5 放大链不同）
- 大宽图示例：2048×768；竖图示例：768×1280；1.5K 竖版：864×1536

## 提示词四段式（从先往后，顺序不可乱）

**① 画质画风（开头）**——英文短句定调：风格 + 质感/色调
> Blue-toned mirror selfie, realistic style

**② 主体句段落（主要段）**——人物本体：年龄/身材/肤色/发型 + 姿势/动作/神态（英文自然语言）
> A woman in her 20s with a natural body proportion, neutral fair skin, very long straight hair with slightly curled ends, medium auburn. Standing with slight weight shifted, right hand raised holding a phone covering her face for a selfie, left arm relaxed at her side, slight midriff visible.

**③ 细节补丁（补充主体句，可长可短）**——服装（括号细节）+ 场景道具清单 + 光线色温（英文）
> Wearing a light blue cropped knit cardigan (two buttons), a blue top faintly showing beneath, denim ultra-short shorts (blue bows on both sides), blue-and-white striped over-knee socks... natural daylight coming through a gauze curtain from the left window, soft diffusion, 5200K.

**④ 镜头（收尾）**——拍摄设备/参数 + 构图 + 机位（英文）
> Rear phone camera, non-portrait mode, 26mm equivalent, realistic phone depth of field, no bokeh; 1:1 composition, subject centered, from top of head to mid-thigh, slight high angle.

## 要点
- **强制英文（作者 2026-08-20 定）**：提示词**必须用英文**——英文速度更快、效果更好；虽支持中文，但**默认/一律用英文写**（四段式全英文）。
- 细节补丁 ≠ 独立场景段：它补充主体句（服装/场景/光线可长可短）
- 具体数字与括号标注（扣数、色温 5200K、焦距 26mm）
- 巨构/尺度场景用具体数字（数千米高的房梁，几万米长的回廊）
- 负面提示词（节点 7）已配完整中文负面清单（泛黄/畸形/水印/构图透视问题等），一般不动
- 图生图链存在（572 LoadImage → 625 缩放 → 630 TwoWaySwitch）但**默认 selection=1 文生图**，图生图暂不使用

## 角色串/人物加载规则（8-19 测验定）
- **不可完全全量无脑加载**：案例——巨构背影图，赛琳娜全量载入（含服装细节），构图与场景高度遵从、背影正确，**但服装反穿**（背部出现正面服装：衣襟蝴蝶结/荷叶边跑到了背后）
- **但可以加载得比简单描述多**：关键外观（发色/发型/发饰/体态）保留没问题，构图与场景依然遵从
- **背影场景**：服装细节描述越少越安全；正面服装细节（衣襟/扣位/蝴蝶结位置）在背影图易导致反穿——需写服装时用"背面视角的…"或只写大轮廓

## 提交方式（黑盒引子，agent 只传参数）

> 直接调用本目录引子 `zimage_full_template.py`（与模板同 basename 自动配对），内部自动 内存拼 API → 递交 → 校验 node_errors → 轮询 → 拷成品 → 一行 JSON。agent 不看脚本内容。

```
python zimage_full_template.py --prompt "四段式英文提示词" --w 768 --h 1024 --name 名字 [--loras 名:强度:on]
```
- `--prompt` 必填，其余可选；**无二次放大**：`--w/--h` 即最终尺寸（8 的倍数）。
- 628 LoRA 默认不动；`--loras` 仅改点名条目，绝不误开其他。
- 返回 JSON：`{"kind":"image","prompt_id":…,"file":"…","size":"…"}`，取 `file` 交付。
