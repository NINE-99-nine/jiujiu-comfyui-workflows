# flux2 图像放大编辑 · 节点与 LoRA 下载地址

> 适用文件：`flux2图像放大编辑.json`（UI 版，35 节点 / 3 分组）。
> LoRA 已按 SHA256 比对，地址里的文件与作者在用的完全一致。

## 一、自定义节点包

| # | 节点包 | 用到的节点 | 下载地址 | 何时需要 |
|---|---|---|---|---|
| 1 | comfyui-lora-manager | Lora Loader (LoraManager) | https://github.com/willmiao/ComfyUI-Lora-Manager | **必需** |
| 2 | ComfyUI-GGUF | UnetLoaderGGUF | https://github.com/city96/ComfyUI-GGUF | **必需**（主模型是 GGUF） |
| 3 | gguf | ClipLoaderGGUF | https://github.com/calcuis/gguf | **必需**（文本编码器 GGUF） |
| 4 | comfyui-inpaint-cropandstitch | InpaintCropImproved、InpaintStitchImproved | https://github.com/lquesada/ComfyUI-Inpaint-CropAndStitch | **必需**（局部放大链路） |
| 5 | comfyui-kjnodes | INTConstant、ImageAndMaskPreview | https://github.com/kijai/ComfyUI-KJNodes | **必需** |
| 6 | ComfyUI-Danbooru-Gallery | GroupIgnoreManager（逻辑门） | https://github.com/Aaalice233/ComfyUI-Danbooru-Gallery | **必需**（分组开关） |
| 7 | comfyui_layerstyle | LayerColor: BrightnessContrastV2、LayerUtility: PurgeVRAM V2 | https://github.com/chflame163/ComfyUI_LayerStyle | 亮度/显存清理 |
| 8 | comfyui_essentials | MaskBlur+ | https://github.com/cubiq/ComfyUI_essentials | 遮罩柔化 |
| 9 | rgthree-comfy | Seed (rgthree)、Image Comparer (rgthree) | https://github.com/rgthree/rgthree-comfy | 种子/对比图 |
| 10 | comfyui-easy-use | easy cleanGpuUsed | https://github.com/yolain/ComfyUI-Easy-Use | 显存清理 |
| 11 | comfyui_memory_cleanup | RAMCleanup | https://github.com/LAOGOU-666/Comfyui-Memory_Cleanup | 内存清理 |

> ⚠️ **GGUF 两个包不是一回事**：`UnetLoaderGGUF` 来自 city96 的 `ComfyUI-GGUF`；`ClipLoaderGGUF`（小写 lip）来自 calcuis 的 `gguf`。两个都要装。

**不用装的部分**：`EmptyFlux2LatentImage`、`ReferenceLatent`、`SAM3_Detect`、`ConditioningZeroOut`、`VAEEncode`、`VAEDecode`、`KSampler`、`CLIPTextEncode` 等 ComfyUI 自带。

## 二、LoRA 清单（默认挂载 2 条）

| 文件名 | 放置目录 | 大小 | 默认状态 | 作用 | 下载地址 |
|---|---|---|---|---|---|
| Klein_9B-一致性consis.safetensors | loras/flux2/ | 272 MB | **开** 0.35 | 换图保一致性（主用） | https://civitai.com/models/1939453?modelVersionId=2634354 |
| flux-2-klein-NSFW.safetensors | loras/flux2/ | 158 MB | 关 0.80 | NSFW 表现（换脸不变） | https://civitai.com/models/2319552?modelVersionId=2609505 |

## 三、放哪里

```
ComfyUI/models/loras/flux2/
├── Klein_9B-一致性consis.safetensors
└── flux-2-klein-NSFW.safetensors
```

## 四、未找到的

无。2 条均为 Civitai 原发布页。
