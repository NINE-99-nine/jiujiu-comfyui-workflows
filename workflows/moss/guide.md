# MOSS-Image 说明书

一次一张图，8 步出图，默认不放大。提示词写法只认 `prompting.md`。

## 调用

```bash
cd <技能根>
# Caption
python workflows/moss/moss_api.py --prompt-file 词.txt --ratio 2:3 --megapixels 1.5 --name 名字 --seed -1
# Layout（宽高与 json 内的尺寸必须一致）
python workflows/moss/moss_api.py --layout 布局.json --width 1008 --height 1504 --name 名字
# 只列 LoRA，不出图
python workflows/moss/moss_api.py --list-loras
```

返回一行 JSON，`file` 是成品绝对路径；引子同时把成品拷到 `_work/moss_api/`。

## 参数

| 参数 | 说明 |
|---|---|
| `--prompt` / `--prompt-file` | 提示词；长文、含英文双引号、多段一律用文件 |
| `--layout` | Layout JSON 文件；自动清空质量词与触发词文本，禁用 `--prompt` |
| `--ratio` | `1:1` / `2:3` / `3:2` / `3:4` / `4:3` / `9:16` / `16:9` / `21:9`；不传＝模板 1024×1536 |
| `--megapixels` | 总像素（百万），常用 1.5 |
| `--width` / `--height` | 直接钉死，优先于 ratio/megapixels；自动对齐 16 倍数 |
| `--name` | 文件名前缀，也是输出子目录名 |
| `--seed` | `-1` 随机；固定值可复现 |
| `--loras` | `名:强度:on\|off`，可重复；默认不传＝只开默认三条（画风 1 + 质量 2） |
| `--no-default-lora` | 关掉默认三条 |
| `--steps` / `--cfg` | 覆盖采样档；只在明确要求时传 |
| `--upscale` / `--seedvr2-res` | SeedVR2 放大（默认关，短边 1440） |

## 钉死档位

- 采样：**8 步 / cfg 1.0 / `er_sde` / `simple` / denoise 1.0**。（2026-10-26 实测：cfg 1.0 画质明显高于 3.5，已钉为默认）
- 加速 LoRA：`lodestones-8-steps-dmd2-lora` @ 1.0（节点 61）。
- 负面词固定：`worst quality, bad anatomy, watermark, jpeg artifact`。
- 质量词框（节点 98）**已清空**：正向提示词＝LoRA 触发词＋用户提示词，不要再写 `masterpiece`/`8k`。

## 分辨率（1.5 MP 档）

| 比例 | 宽×高 | 比例 | 宽×高 |
|---|---|---|---|
| 1:1 | 1232×1232 | 16:9 | 1632×912 |
| 2:3 | 1008×1504 | 9:16 | 912×1632 |
| 3:4 | 1056×1408 | 21:9 | 1872×800 |
| 4:3 | 1408×1056 | 3:2 | 1504×1008 |

其他像素档：`w=√(MP×1e6×r)`，宽高各自取 16 的倍数。低于 0.25 MP 或高于 4 MP 画面会散。

## LoRA

**12 条槽位，默认开三条：画风 1 + 质量 2**（2026-11-18 按作者当前 ComfyUI 工作流同步）。其余九条由引子强制关闭。

| # | 名字 | 定位 | 默认 |
|---|---|---|---|
| 1 | `moss-masterpieces-moss-timestep` | **质量**（masterpieces 向） | ★ 1.0 |
| 2 | `moss_context_detaile_tweaker_20261018_rank2` | **质量**·细节调节 | ★ 0.60 |
| 3 | `KOOK-MOSS-SFT-观澜` | 写实画风（不是质量档） | 关（实测降质量，与 cfg 1.0 冲突） |
| 4 | `mossNai5E585B6E4B889.Ng66` | **画风**（painterly cine；带 civitai 触发词 `@painterly cine`、`nuanced lighting transitions…moist glossy skin highlight`） | ★ 1.0 |
| 5 | `LP Flat-moss-v2` | 线稿 / 平涂 | 关 |
| 6 | `Nyalia_moss_v1_lokr` | 动漫画风 | 关 |
| 7 | `fkey-lora-r4-muon-step6840-comfy` | 画风 | 关 |
| 8 | `kzmynon-moss-v1_comfyui` | 动漫画风 | 关 |
| 9 | `anireal_moss_lora_v1` | 写实 | 关 |
| 10 | `MOSS-HOCF_000001925` | 巨构 | 关 |
| 11 | `wlop12` | 油画 | 关 |
| 12 | `gladas-style-moss_v1` | 画风（未实测） | 关 |

- ⚠️ **触发词串是假信号**：`LoraManager` 会把 12 条名字**全都**写进正向提示词的 `<lora:…>` 串，不管开没开。所以照别人的图推配置时，长串里出现的名字 ≠ 生效的 LoRA——真正吃进去的只有 ★ 三条（或你点名的）。
- 第 4 条画风档带 civitai 触发词（`@painterly cine` 等），但**当前工作流没有把它写进提示词**；想更贴它的训练分布可以手动加进 caption。
- 不点名就不开；她说「用 LoRA」没说哪条＝先 `--list-loras` 带编号让她挑。
- MOSS 上叠 2–3 条为上限（默认已占 2 条）。
- 名字打错只往 stderr 打 `WARN`，图照出但该条没生效——批量跑完 grep 一次 `WARN`。

## 提示词

只有两种形态：Caption 纯文本，或 Layout 单行 JSON。规则、篇幅、自检清单见 `prompting.md`。

## 放大

默认关，成品＝输入分辨率。`--upscale` 才在内存补 SeedVR2 链（短边 1440，长边封顶 2880）；显存紧张时先降 `--seedvr2-res`。

## 翻车点

- 不传 `--megapixels` 且不传 `--ratio` → 沿用模板 1024×1536。
- `--ratio` 写错直接退出并列出合法值。
- 同提示词同尺寸重跑命中缓存出同一张 → 换 `--seed`。
- Layout 的宽高按实际出图算，小偏差可容忍，别为像素对齐反复重跑。
- 动 `98` 质量词、`5` 负面词、`19` 步数/cfg、`61` 加速 LoRA → 画面或净空直接变。
