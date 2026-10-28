# zimage 工作流 · 节点与 LoRA 下载地址

> 适用文件：`z image.json`（UI 版，56 节点 / 9 分组）。
> LoRA 已按 SHA256 比对，地址里的文件与作者在用的完全一致。

## 一、自定义节点包

| # | 节点包（custom_nodes 目录名） | 工作流里用到的节点 | 下载地址 | 何时需要 |
|---|---|---|---|---|
| 1 | comfyui-kjnodes | JoinStringMulti、INTConstant | https://github.com/kijai/ComfyUI-KJNodes | **必需** |
| 2 | ComfyUI-GGUF | UnetLoaderGGUF（主模型 GGUF 加载） | https://github.com/city96/ComfyUI-GGUF | **必需** |
| 3 | gguf | ClipLoaderGGUF（文本编码器 GGUF 加载） | https://github.com/calcuis/gguf | **必需** |
| 4 | comfyui_layerstyle | LayerUtility: ImageReel、ImageReelComposit、ImageScaleByAspectRatio V2 | https://github.com/chflame163/ComfyUI_LayerStyle | **必需**（分辨率/对比展示） |
| 5 | ComfyUI-Danbooru-Gallery | ResolutionMasterSimplify（分辨率大师） | https://github.com/Aaalice233/ComfyUI-Danbooru-Gallery | **必需** |
| 6 | controlaltai-nodes | TwoWaySwitch | https://github.com/gseth/ControlAltAI-Nodes | 文生图/图生图切换 |
| 7 | comfyui-easy-use | easy cleanGpuUsed、easy getNode、easy setNode、easy seed | https://github.com/yolain/ComfyUI-Easy-Use | **必需**（显存与节点引用） |
| 8 | comfyui_controlnet_aux | CannyEdgePreprocessor、HEDPreprocessor、DWPreprocessor、Zoe_DepthAnythingPreprocessor | https://github.com/Fannovel16/comfyui_controlnet_aux | ControlNet 组 |
| 9 | rgthree-comfy | Any Switch (rgthree)、Fast Groups Bypasser (rgthree) | https://github.com/rgthree/rgthree-comfy | 分组开关面板 |
| 10 | comfyui-custom-scripts | PlaySound\|pysssss | https://github.com/pythongosssss/ComfyUI-Custom-Scripts | 出图提示音（可选） |
| 11 | comfyui_memory_cleanup | RAMCleanup | https://github.com/LAOGOU-666/Comfyui-Memory_Cleanup | 内存清理 |
| 12 | raffle | Raffle | https://github.com/rainlizard/ComfyUI-Raffle | 抽卡（可选） |

> ⚠️ **GGUF 两个包不是一回事**：`UnetLoaderGGUF` 来自 city96 的 `ComfyUI-GGUF`；`ClipLoaderGGUF`（小写 lip）来自 calcuis 的 `gguf`。两个都装，别只装一个。

**不用装的部分**：`CLIPTextEncode`、`KSampler`、`VAEDecode`、`VAEEncode`、`VAELoader`、`UNETLoader`、`CLIPLoader`、`LoadImage`、`SaveImage`、`PreviewImage`、`EmptyLatentImage`、`LatentUpscaleBy`、`PrimitiveString`、`PrimitiveStringMultiline`、`Note`、`KSamplerAdvanced`、`VAEDecodeTiled`、`ModelPatchLoader`、`ModelSamplingAuraFlow`、`QwenImageDiffsynthControlnet`、`ConditioningZeroOut`、`ImageScaleToTotalPixels`、`LoraLoaderModelOnly` 都是 ComfyUI 自带。

## 二、LoRA 清单（默认挂载 4 条）

| 文件名 | 放置目录 | 大小 | 默认状态 | 触发词 | 作用 | 下载地址 |
|---|---|---|---|---|---|---|
| skin texture Photorealistic style v4.5.safetensors | loras/z image/ | 162 MB | **开** 0.50 | — | 写实皮肤质感 | https://civitai.com/models/580857?modelVersionId=2674760 |
| Z-Detail-Slider.safetensors | loras/z image/ | 20 MB | **开** 1.50 | — | 细节滑块 | https://civitai.com/models/2234266?modelVersionId=2515203 |
| Comics_Factory_V6T1_E10.safetensors | loras/z image/ | 162 MB | 关 0.85 | — | 美漫风格 | https://civitai.com/models/1285927?modelVersionId=3017301 |
| NSFW_master_ZIT_000017532.safetensors | loras/z image/ | 593 MB | 关 0.80 | — | NSFW 表现强化（体积最大） | https://civitai.com/models/667086?modelVersionId=2904324 |

## 三、放哪里

```
ComfyUI/models/loras/z image/
├── skin texture Photorealistic style v4.5.safetensors
├── Z-Detail-Slider.safetensors
├── Comics_Factory_V6T1_E10.safetensors
└── NSFW_master_ZIT_000017532.safetensors
```

## 四、未找到的

无。4 条全部为 Civitai 原发布页。
