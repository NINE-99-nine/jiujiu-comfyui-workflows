# MOSS-Image 子技能 · 使用守则（guide v2.0）

> 与 `moss_api.json`（固定副本）＋ `moss_api.py`（引子）配套。出图一律用本目录副本，不用原件。

## 副本信息

| 项 | 值 |
|---|---|
| 固定副本 | `workflows/moss/moss_api.json`（API 格式，**21 节点**，7.6 KB） |
| 归档校验 | MD5 `da1e5be4b1e4388ed08c81cbbd992249`（**2026-10-20 v2 入库**） |
| 来源 | 作者在 ComfyUI 导出：`<your_data_dir>\AI\AI生成的优秀案例\AI绘画优秀案例\MOSS-Image_API.json` |
| 模型族 | UNet `moss image\moss_image_base_int8_convrot` ＋ CLIP `qwen3.5_9b_int8_convrot`（type=`moss_image`）＋ VAE `flux2-vae` |
| 蒸馏加速 | `61` LoraLoaderModelOnly → `moss image\MOSS_Image_SFT_8_steps_dmd_v0.1`（strength 1.0，**原样保留**） |
| 用户 LoRA | `93` Lora Loader (LoraManager)，6 条可选，1 条默认开启 |
| 出图链路 | [13]UNet → [61]dmd → [93]LoRA 堆 → [19]KSampler（**8 步 / cfg 1 / er_sde / simple**）→ [22]VAEDecode |
| 放大链 | [103]AnySwitch → [85]SeedVR2VideoUpscaler（**短边 1440**，长边上限 2880）→ [97]AnySwitch → [81]SaveImageAdvanced |
| 提示词入口 | [99]String → [101]JoinStringMulti（串 1 接 [93] 的触发词输出）→ [4] 正向 CLIPTextEncode |

**实测（2026-10-20 v2 首跑）**：输入 3:4 / 1.2MP（960×1280）→ 成品 **1440×1912**。放大链确认生效（若退回原图档就是 960×1280）。

## 可改节点（作者划定）

| 节点 | 功能 | 引子参数 |
|---|---|---|
| `99` | 提示词（String） | `--prompt` / `--prompt-file` |
| `8` | 分辨率选择器 | `--ratio` ＋ `--megapixels` |
| `93` | LoRA 堆（LoraManager） | `--loras`（**只有作者点名时才传，默认不传**）/ `--no-default-lora` / `--list-loras` |
| `85` | SeedVR2 放大短边 | `--seedvr2-res` / `--no-upscale` |

其余一律不动：`5` 负面词（`worst quality, bad anatomy, watermark, jpeg artifact`）、`19` 8 步/cfg1/er_sde、`61` dmd 蒸馏 LoRA、`19`/`85` 的 seed 由引子统一写入。

## LoRA 怎么用

🔴 **P0 铁律：默认一律不动 LoRA。** 不传 `--loras`，就让模板原本那条 `moss_context_detaile_tweaker_20261018_rank2`（0.60）单独生效——**画风与画面内容全部靠提示词控制**（要油画感就写 `oil painting, thick impasto, varnished surface`；要动漫线稿就写 `crisp thin lineart, flat cel colouring`）。

- 只有作者**明确说出**「换 LoRA / 用某一条 / 开某一条」时才允许动；她给出编号（「4」「2 4 6」）就是授权。
- 🔴 她说「像鬼刀那种感觉」「要超写实油画」「要精致线稿」这类话，**是对画面的描述要求，不是授权我开 LoRA**——那种场合一律用提示词实现。
- 她自己没点名，就**一个都不许加**；宁可提示词写长一点，也不许"顺手开一条更合适"。
- 脚本侧已加保护：**不传 `--loras` 时，引子把除默认那条以外的条目全部强制置为关闭**，所以「默认只有一条 LoRA」是被程序钉住的，不靠自觉。

六条可选，**默认开着的是 `moss_context_detaile_tweaker_20261018_rank2`（0.60）——除作者点名，谁都不许关**。

```bash
# 只列清单（选择题用，不出图）
python workflows/moss/moss_api.py --list-loras

# 开一条、指定强度（可重复传，只动点名的，其余保持模板原样）
--loras "wlop12:0.8:on" --loras "anireal_moss_lora_v1:0.6:on"

# 关掉某条
--loras "wlop12:0.0:off"

# 关掉默认那条
--no-default-lora
```

格式 `名字:强度:on|off`，三段都可省（只写名字＝开关不管、强度不管；写 `名字:0.8` ＝只改强度）。

**引子会把 active 的条目同步回 `text` widget**（`<lora:名:强度>`），所以 UI 里看到的和实际生效的一致。

### 给作者做 LoRA 选择题时的规矩

1. **必须带编号**——六条按 `--list-loras` 的顺序编号，她习惯答「2 4 6 全用」「只要 3，0.7」；没编号她就得复述长名字。
2. **绝不凭记忆手打 LoRA 名**——一律先跑 `--list-loras` 取真名再拼参数。长名字（如 `moss_context_detaile_tweaker_20261018_rank2`）手打必错。
3. 引子已做两级兜底：精确名 → 唯一子串匹配；命中多条会打 `WARN: lora 名字不唯一` 并跳过，**完全不存在的会打 `WARN: lora 不存在(忽略,不新增)` 并跳过——出图照常完成、但那条 LoRA 根本没生效**。所以**批量跑时别只看末尾摘要，把完整 stderr 捞出来 grep 一次 `WARN`**。
4. **开与关都要回读核实**：改完看成品元数据里该条的 `active` 是否真的翻转、其余条目有没有被顺手动到。
5. 一次叠几条由她定，引子不设上限；经验上 **MOSS 上叠 2–3 条就够**，再多会互相打架。
6. **默认那条不许自作主张关**（它不是风格 LoRA，是细节调节器）；她要关会明说。

## 放大链

- 放大短边默认 **1440**（模板值），长边上限 2880；改成 1080/1200 可省显存与时间。
- **`--no-upscale`** 只出原图（引子把 [97] 的「优先输入」改指 [22] 原图，[85] 不再被引用而不执行）。
- 显存吃紧的症状：`85` 报 OOM / 卡很久 → 先降 `--seedvr2-res`，其次 `POST /free` 清显存。
- 成品尺寸 = 放大后短边 1440 + 按比例对齐 8 的倍数（3:4 → 1440×1912，不是 1440×1920）。

## 分辨率规则

- **比例**用完整枚举名，写 `9:16` 会报 `invalid choice`：
  `1:1 (Square)`｜`2:3 (Portrait Photo)`｜`3:2 (Photo)`｜`3:4 (Portrait Standard)`｜`4:3 (Standard)`｜`9:16 (Portrait Widescreen)`｜`16:9 (Widescreen)`｜`21:9 (Ultrawide)`
- **像素预算**由 `--megapixels` 决定，默认 **1.5**。官方推荐档 **1M / 1.5M / 2M**；低于 0.25M 或高于 4M 属外推区。
- **宽高必须是 16 的倍数**——MOSS-Image 自己的约束（模板 `multiple` 写的是 8，**引子固定改成 16，不要改回去**）。
- 比例按构图选：竖构图/立绘 → 9:16 或 2:3；横构图/场景/多人 → 16:9；超宽 → 21:9。

## 提交方式（黑盒引子，agent 只传参数）

```bash
# ① 短提示词
python workflows/moss/moss_api.py --prompt "A quiet summer room, a girl reading by the window" \
  --ratio "3:4 (Portrait Standard)" --megapixels 1.5 --name 夏日窗边 --seed -1

# ② 长提示词 / 含引号 / 多段（一律走文件）
python workflows/moss/moss_api.py --prompt-file 词.txt --ratio "16:9 (Widescreen)" --megapixels 2.0 --name 街景

# ③ 带画风 LoRA + 降档放大
python workflows/moss/moss_api.py --prompt-file 词.txt --ratio "2:3 (Portrait Photo)" --megapixels 1.5 \
  --loras "wlop12:0.8:on" --seedvr2-res 1200 --name 油画人像
```

- 引子自动：内存拼 API（不落盘）→ `execution/comfy_submit.py` 递交 → 校验 `node_errors` → 轮询 → 拷成品到 `_work/moss_api/` → 打印一行 JSON。
- 取成品只看返回的 `file` 绝对路径；文件名 `<name>_<YYYY-MM-DD>.png`。
- 提示词含英文双引号（要渲染的可见文字）时**必须**用 `--prompt-file`。

## 什么活派给 MOSS

强项是**版式与文字**，不是纯氛围：

- **优先给它**：带嵌字的海报 / 封面 / 卡片、要精确控制元素位置的多人物构图、需要中英文正确渲染的图、长提示词（撑得住 4K token）才说得清的复杂画面。
- 动漫与写实都能出；**风格由 LoRA ＋ 提示词定**（`wlop12` 油画、`anireal_*` 写实、`kzmynon` / `Nyalia` 动漫向，具体以实测为准）。
- **不必给它**：只求氛围的单人插画、纯平涂极简、要像素级精确几何版式的活（那类走 krea2 更稳）。

## 注意事项

- **不要为同一提示词反复重跑**：同提示词同分辨率会命中 ComfyUI 缓存，换 `--seed` 或微调 `--megapixels` 即可破。
- 提示词只放 caption 或编译后的 Layout 一行 JSON，不要把说明、坐标计算、工具指令写进去。
- 画面里要出现的文字必须**逐字写出并用引号包住**，同时说明位置与字号层级。
- 视觉保真度偏「厚重、有材质感」：适合插画、摄影、海报、织物/金属/玻璃质感；纯平涂极简或像素级精确版式走 krea2 / HTML。
- 出图后不做 vision 自检（作者习惯），直接交付；只有硬伤（空图、崩坏、该净空的区没净）才点一句。
- 临时提示词文件跑完即删。
- **`85` 的 seed 上限是 2^32-1**：引子已自动取模，不要手写 15 位随机数进模板。

## 版本日志

- **v2.0（2026-10-20）**：作者新建带 LoRA 堆 ＋ SeedVR2 放大的版本，21 节点。引子重写：提示词改注入 `99.String`（`101` 把 `93` 的触发词自动拼在前面）、保存改 `81`、LoRA 改 `93.loras[]`、新增 `--loras` / `--no-default-lora` / `--list-loras` / `--seedvr2-res` / `--no-upscale`；采样器从 `euler` 变 `er_sde`；引子给两个 AnySwitch 兜底补 `switch=True`。实测 3:4/1.2MP → 1440×1912。
- v1.0（2026-10-19）：首版，13 节点、无放大链、只有提示词与分辨率两个旋钮。
