# moss 工作流 · 节点与 LoRA 下载地址

> 适用文件：`moss_image.json`（UI 版，34 节点 / 7 分组）。
> LoRA 已按 SHA256 比对；9 条里 8 条定位到发布页，1 条未找到（见末节）。

## 一、自定义节点包

| # | 节点包（custom_nodes 目录名） | 工作流里用到的节点 | 下载地址 | 何时需要 |
|---|---|---|---|---|
| 1 | comfyui-kjnodes | JoinStringMulti | https://github.com/kijai/ComfyUI-KJNodes | **必需** |
| 2 | comfyui-lora-manager | Lora Loader (LoraManager) | https://github.com/willmiao/ComfyUI-Lora-Manager | **必需** |
| 3 | ComfyUI-Danbooru-Gallery | ResolutionMasterSimplify（分辨率大师）、GroupIgnoreManager（逻辑门） | https://github.com/Aaalice233/ComfyUI-Danbooru-Gallery | **必需** |
| 4 | AnySwitch | AnySwitch | https://github.com/kevinzilin/AnySwitch | **必需**（分支切换） |
| 5 | ComfyLiterals | String | https://github.com/M1kep/ComfyLiterals | **必需**（字符串常量） |
| 6 | seedvr2_videoupscaler | SeedVR2LoadDiTModel、SeedVR2LoadVAEModel、SeedVR2VideoUpscaler | https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler | 高清放大分支 |
| 7 | raffle | Raffle | https://github.com/rainlizard/ComfyUI-Raffle | 抽卡（可选） |

**不用装的部分**：`CLIPTextEncode`、`KSampler`、`VAEDecode`、`VAEEncode`、`VAELoader`、`UNETLoader`、`CLIPLoader`、`LoadImage`、`SaveImage`、`PreviewImage`、`EmptyLatentImage`、`LatentUpscaleBy`、`PrimitiveString`、`PrimitiveStringMultiline`、`Note`、`MOSSImageLayoutPrompt`、`CreateBoundingBoxes`、`TextGenerate`、`SaveImageAdvanced`、`VAEDecodeTiled` 都是 ComfyUI 自带（MOSS 是官方原生支持）。

## 二、LoRA 清单（默认挂载 9 条）

| 文件名 | 放置目录 | 大小 | 默认状态 | 触发词 | 作用 | 下载地址 |
|---|---|---|---|---|---|---|
| moss_context_detaile_tweaker_20261018_rank2.safetensors | loras/moss image/ | 9 MB | **开** 0.60 | — | 细节微调（小体积必备） | https://civitai.com/models/3007815?modelVersionId=3412961 |
| KOOK-MOSS-SFT-观澜.safetensors | loras/moss image/ | 138 MB | **开** 1.0 | — | 观澜画风（默认开启） | **未找到发布页** |
| fkey-lora-r4-muon-step6840-comfy.safetensors | loras/moss image/ | 18 MB | 关 1.0 | — | FKEY 绘画风 | https://civitai.com/models/3013321?modelVersionId=3420175 |
| Nyalia_moss_v1_lokr.safetensors | loras/moss image/ | 138 MB | 关 1.0 | — | nyalia 画风 | https://civitai.com/models/3006584?modelVersionId=3411356 |
| kzmynon-moss-v1_comfyui.safetensors | loras/moss image/ | 142 MB | 关 1.0 | — | Kzmynon 画风 | https://civitai.com/models/2878242?modelVersionId=3411295 |
| anireal_moss_lora_v1.safetensors | loras/moss image/ | 123 MB | 关 1.0 | — | 二次元写实 | https://civitai.com/models/3006790?modelVersionId=3411644 |
| MOSS-HOCF_000001925.safetensors | loras/moss image/ | 62 MB | 关 1.0 | — | 厚涂 2.5D | https://civitai.com/models/2230912?modelVersionId=3412725 |
| wlop12.safetensors | loras/moss image/ | 123 MB | 关 1.0 | — | wlop 画风 | https://civitai.com/models/2637182?modelVersionId=3413922 |
| moss_image_sft_4_steps_lora_v2_600_avg_rank_72_bf16.safetensors | loras/moss image/ | 312 MB | 挂载（4 步加速） | — | 官方 SFT 4 步加速 LoRA | https://civitai.com/models/3006599?modelVersionId=3414934 |

- 前 2 条默认开启（细节 + 观澜）；其余换画风时切 active。

## 三、放哪里

```
ComfyUI/models/loras/moss image/
├── moss_context_detaile_tweaker_20261018_rank2.safetensors
├── KOOK-MOSS-SFT-观澜.safetensors
├── moss_image_sft_4_steps_lora_v2_600_avg_rank_72_bf16.safetensors
└── …（其余 6 条）
```

## 四、未找到的

| LoRA | 情况 |
|---|---|
| `KOOK-MOSS-SFT-观澜.safetensors`（138 MB） | Civitai、魔搭、HuggingFace 均未搜到对应发布页，作者（KOOK）可能只在群内分享。**这是默认开启的 2 条之一**——缺它时把该条 active 关掉即可正常出图，只是画风不同。 |
