# flux2 图像正常编辑 · 节点与 LoRA 下载地址

> 适用文件：`flux2图像正常编辑.json`（UI 版，34 节点 / 5 分组）。
> LoRA 已按 SHA256 比对，地址里的文件与作者在用的完全一致。

## 一、自定义节点包

| # | 节点包 | 用到的节点 | 下载地址 | 何时需要 |
|---|---|---|---|---|
| 1 | comfyui-lora-manager | Lora Loader (LoraManager)、TriggerWord Toggle (LoraManager) | https://github.com/willmiao/ComfyUI-Lora-Manager | **必需** |
| 2 | ComfyUI-GGUF | UnetLoaderGGUF | https://github.com/city96/ComfyUI-GGUF | **必需** |
| 3 | gguf | ClipLoaderGGUF | https://github.com/calcuis/gguf | **必需** |
| 4 | comfyui-kjnodes | JoinStringMulti | https://github.com/kijai/ComfyUI-KJNodes | **必需** |
| 5 | comfyui_layerstyle | LayerUtility: ImageScaleByAspectRatio V2 | https://github.com/chflame163/ComfyUI_LayerStyle | **必需**（分辨率） |
| 6 | ComfyUI-Danbooru-Gallery | GroupIgnoreManager、ResolutionMasterSimplify | https://github.com/Aaalice233/ComfyUI-Danbooru-Gallery | **必需** |
| 7 | ComfyUI_JPS-Nodes | Latent Switch (JPS) | https://github.com/JPS-GER/ComfyUI_JPS-Nodes | **必需**（分支切换） |
| 8 | comfyui-easy-use | easy cleanGpuUsed、easy imageIndexSwitch | https://github.com/yolain/ComfyUI-Easy-Use | **必需** |
| 9 | rgthree-comfy | Image Comparer (rgthree) | https://github.com/rgthree/rgthree-comfy | 对比图 |
| 10 | comfyui_memory_cleanup | RAMCleanup | https://github.com/LAOGOU-666/Comfyui-Memory_Cleanup | 内存清理 |

> ⚠️ 同前：`UnetLoaderGGUF`（city96）与 `ClipLoaderGGUF`（calcuis）来自两个不同包，都要装。

**不用装的部分**：`EmptyFlux2LatentImage`、`ConditioningZeroOut`、`GetImageSize`、`ImageScaleToTotalPixels`、`VAEDecodeTiled`、`PrimitiveStringMultiline` 等 ComfyUI 自带（含图内 4 个子图）。

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
