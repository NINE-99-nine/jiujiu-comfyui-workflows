# krea2 工作流 · 使用守则（guide v1.0）

> 本守则与 `krea2汇总.json`（UI 格式，skill 内备份，**实际出图不用它**）+ `krea2汇总_api.json`（API 格式，**实际出图用这个**，由引子 `krea2汇总_api.py` 调用）配套。
> 
> ⚠️ **分工（8-31 作者明确）**：`krea2汇总.json`（不带 API 后缀）仅作 skill 内备份，出图全程用不到；实际调用靠 `krea2汇总_api.py` + `krea2汇总_api.json` 这套。两者不要混用。
>
> 🔒 **两文件边界**：引子只读同 basename 的 API 版 json（`krea2汇总_api.json`），UI 版物理不可达。**通则见主 skill 核心铁律 0a。**
>
> 📌 **提示词怎么写**（基础=画风质感→画面内容→构图镜头；设计海报/概念图进阶=十段骨架；**无词量硬限，可长可细**；引号标文字；中英皆可英文更佳）：见同目录 `prompting.md`；完整案例库见 `prompt-library/krea2-poster-examples/`。

## 副本信息

| 项 | 值 |
|---|---|
| 固定副本 | `workflows/krea2/krea2汇总.json`（UI 格式，29 节点，MD5 `d2c51e14…`） |
| API 参考 | `workflows/krea2/krea2汇总_api.json`（API 格式，27 节点，2026-08-23 作者导出） |
| 原件位置 | `F:\Comfy-Desktop\ComfyUI-Installs\jiujiu-2\ComfyUI\user\default\workflows\Krea2汇总.json` |
| 模型族 | krea2 turbo（`krea2_turbo_int8_convrot`）+ wan_2.1 VAE + qwen3vl_4b_heretic CLIP（krea2 型） |
| 出图链路（**三次处理**，8-31 作者新版） | [33] EmptyLatentImage（[31] 分辨率）→ [17] KSampler 7 步 cfg1（turbo 初次）→ [19] LatentUpscale 1.5× → [23] KSampler 10 步（精修）→ [21] VAEDecodeTiled → [20] ColorMatchV2 → [58] **SeedVR2 放大**（resolution=1600 短边 / max_resolution=2560 上限）→ [24] SaveImage。中间 [60] 清理显存 + [61] RAMCleanup 挂在 [20] 后 |
| 图生图残留 | [30] LoadImage → [28] 缩放 1.5MP → [29] VAEEncode → [32] Latent Switch（select=0 走 [33] 生成路径，图生图链不生效；提交前按需 bypass） |

## 可改节点（唯一可控面）

**作者已确认只有以下三个节点生效**：

| 节点 ID | 功能 | 改法 |
|---|---|---|
| `13` | 人设二（**主提示词输入**，StringConstantMultiline） | widgets_values[0]（键 `string`） |
| `16` | Lora Loader (LoraManager)（LoRA 控制） | wv[1] = text；**实际加载看 wv[2] loras 列表的 active**（见下方铁律） |
| `31` | 分辨率大师简化版 `[宽,高]` | **节点对象路径**（hidden widget，数据路径无效，同 anima [19]） |

**提示词生效链路**：[13] 人设二 → [14] JoinStringMulti（拼接 [10] 质量词 / [11] 人设一 / [12] 画风词 / [16] 触发词）→ [1] easy stylesSelector（风格选择器，默认 `krea2_397styles-photography_摄影`）→ [15] CLIPTextEncode → [17]/[23] KSampler。

- **默认只改 [13] 提示词 + [31] 分辨率**；[16] LoRA 只有作者点名换画风时才动
- [10] 质量词 / [11] 人设一 / [12] 画风词 参与拼接但**一般不动**（作者手动维护）
- [1] 风格选择器默认保持 `krea2_397styles-photography_摄影`，未经确认不动

## 🚨 LoraManager 铁律（anima 同款坑，8-17 实锤）

- 服务端 `load_loras()` 把 `text` 参数 `del` 掉，**加载只看 `loras` 列表（wv[2]）的 `active:true` 条目**
- `get_loras_list` 无 `loras` 键返回 `[]` = **0 个 LoRA 加载（裸模型）**
- API 直连必须传 `inputs["loras"] = wv[2]`（引子 comfy_submit 已内置解包：把 `{"__value__": [...]}` 解为裸 list，服务端只按 active 加载）
- **krea2 默认激活三件套**（8-23 作者工作流当前状态）：`krea2-Cc-天魔-身材:1.00` + `Krea2-realism_engine_v2_轻量:1.00` + `Krea2-滑块-细节PornMaster_Detail_Slider_Krea2_V1:0.70`；其余 8 个（2D动漫/Afterlight/Yoneyama_Mai/gpt anime render/harustyle/25D动漫/asianMix/动漫补丁）默认 inactive
- ⚠️ **三件套 = 画质增强，不是画风**（作者 8-31 强调）：默认三件套全是**画质/细节/身材增强**，**没有一个是画风 lora**。其中 `Krea2-realism_engine_v2_轻量` 名字看着像"写实画风"，**其实是增强图片准确性/真实度**（画质类），**千万别当画风**。**换画风 lora 时，是在这三件套基础上额外加，绝不撤掉/替换它们**；传 `--loras` 只新增/激活目标画风条目，三件套保持 active（引子 + apply_lora_specs 仅改点名条目，天然不误撤）。

## 分辨率规则（⚠️ 三次处理 + 显存限制，8-31 作者新版）

工作流共 **三次处理**：
1. **初次**：[33] EmptyLatentImage 按 [31] 初始分辨率生成
2. **1.5× 高清放大**：[19] LatentUpscaleBy 1.5×（长宽各 ×1.5，**实际像素 ×2.25**）→ [23] 精修
3. **SeedVR2 放大**：[58] 把二次后的图放大——出图分辨率由 `resolution=1600`（**最小边**）与 `max_resolution=2560`（**最大边上限**）共同决定：目标是把最小边推到 1600，同时保证最大边 ≤2560；**二者矛盾时长边封顶 2560、短边被压缩**（保证不爆显存）。真正决定画质的是 [31] 初始分辨率。**最终长边 ≤2560，短边 ≤1600**

**约束（作者 8-31 定）：**
- **初始 [31] 分辨率 ≈ 60 万像素（0.6M px，宽×高≈600000）**。因为后续放大 ×2.25，初始太大再放大必爆显存。
- **第二次处理（1.5× 后）的成品最短边 ≤ 1600**。理由：SeedVR2 设定的放大短边就是 1600，若 1.5× 后短边已 ≥1600，seedvr2 就被跳过/白费；且 1600×1600 这种尺寸 krea2 主模型本就跑不出（爆显存）。极限情况也不会这么干。
- 按"**总像素量级 + 目标比例**"定 [31]，8 的倍数，贴合目标宽高比。

| 目标最终（seedvr2 后） | 初始 [31] | 说明 |
|---|---|---|
| 竖 960×1440 | 640×960 | 0.61M |
| 竖 1152×1728 | 768×1152 | 0.88M 略超→偏安全取小 |
| 横 1536×1024 | 1024×683 | 0.70M |
| 横 1088×552 | 1088×552 | 0.60M（21:9 巨构图） |
| 横 1176×504 | 1176×504 | 0.59M（21:9） |

## 提交方式（黑盒引子，agent 只传参数）

> ⚡ 直接调用本目录引子 `krea2汇总_api.py`（与模板同名自动配对），内部自动完成 内存拼 API → 递交 → 轮询 → 拷成品，全程黑盒。agent 不看脚本内容。

**引子接口（唯一需要填的参数）：**
```
python krea2汇总_api.py --prompt "人设二提示词" --w 672 --h 1000 --name 梦核巨构图 --seed -1 [--loras 名:强度:on]
```
- `--prompt` 必填，其余可选：`--w/--h` 初始分辨率（最后 ×1.5，8 的倍数）、`--name` 成品名、`--seed`（-1 随机 / 具体值固定 / 缺省为模板初始值）、`--loras`（可重复，只改点名条目）。
- 返回一行 JSON：`{"prompt_id":"…","file":"…\\_work\\krea2汇总_api\\<name>_<日期>.png","size":"…"}`，取 `file` 即可。

**可选 LoRA 控制（只改点名，绝不误开全部）：**
- 不传 `--loras` = 完全用模板默认（激活三件套 realism 等，即默认写实画风）。
- 传 `--loras 名字:强度:on` 仅定位模板内同名条目改 active/strength；点名项模板里不存在则忽略并 stderr 提示，**不新增条目**。

## 缓存坑

- 同提示词 + 同分辨率重复提交命中 ComfyUI 缓存 → 微调 [31] 宽高破缓存（如 640×960 → 656×976）

## 版本日志

- v1.0（2026-08-23）：作者提供 API 导出 + 使用原则，初步建立子技能（副本/guide/prompting）
- v1.1（2026-09-07）：第 9 行提示词入口措辞更新——去词量硬限（可长可细），并指向案例库 `prompt-library/krea2-poster-examples/`
