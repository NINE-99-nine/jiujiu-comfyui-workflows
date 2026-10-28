# krea2 工作流 · 节点与 LoRA 下载地址

> 适用文件：`krea2汇总.json`（UI 版，56 节点 / 5 分组）。
> LoRA 已按 SHA256 逐一比对，表里的地址下载到的文件与作者在用文件完全一致。

## 一、自定义节点包

装法二选一：ComfyUI Manager 搜包名安装；或 `git clone` 到 `ComfyUI/custom_nodes/` 后重启。

| # | 节点包（custom_nodes 目录名） | 工作流里用到的节点 | 下载地址 | 何时需要 |
|---|---|---|---|---|
| 1 | comfyui-kjnodes | StringConstantMultiline、JoinStringMulti、ColorMatchV2 | https://github.com/kijai/ComfyUI-KJNodes | **必需**（提示词拼装） |
| 2 | comfyui-krea2edit | Krea2EditGroundedEncode、Krea2EditModelPatch | https://github.com/lbouaraba/comfyui-krea2edit | **必需**（krea2 专用编码/补丁节点） |
| 3 | comfyui-lora-manager | Lora Loader (LoraManager) | https://github.com/willmiao/ComfyUI-Lora-Manager | **必需**（画风 LoRA） |
| 4 | comfyui-easy-use | easy cleanGpuUsed、easy stylesSelector | https://github.com/yolain/ComfyUI-Easy-Use | **必需**（显存清理 + 风格选择） |
| 5 | ComfyUI-Danbooru-Gallery | ResolutionMasterSimplify（分辨率大师） | https://github.com/Aaalice233/ComfyUI-Danbooru-Gallery | **必需**（分辨率） |
| 6 | ComfyUI_JPS-Nodes | Latent Switch (JPS) | https://github.com/JPS-GER/ComfyUI_JPS-Nodes | **必需**（潜空间分支切换） |
| 7 | rgthree-comfy | Seed (rgthree) | https://github.com/rgthree/rgthree-comfy | 随机种子 |
| 8 | seedvr2_videoupscaler | SeedVR2LoadDiTModel、SeedVR2LoadVAEModel、SeedVR2VideoUpscaler | https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler | seedvr2 放大分支 |
| 9 | comfyui_memory_cleanup | RAMCleanup | https://github.com/LAOGOU-666/Comfyui-Memory_Cleanup | 内存清理（可选但建议装） |

**不用装的部分**：`CLIPTextEncode`、`KSampler`、`VAEDecode`、`VAEEncode`、`VAELoader`、`UNETLoader`、`CLIPLoader`、`LoadImage`、`SaveImage`、`PreviewImage`、`EmptyLatentImage`、`LatentUpscaleBy`、`PrimitiveString`、`PrimitiveStringMultiline`、`Note`、`KSamplerAdvanced`、`VAEDecodeTiled`、`EmptySD3LatentImage`、`ImageScaleToTotalPixels`、`ResolutionSelector`、`LoraLoaderModelOnly` 都是 ComfyUI 自带。

## 二、LoRA 清单（默认挂载 12 条）

| 文件名 | 放置目录 | 大小 | 默认状态 | 触发词 | 作用 | 下载地址 |
|---|---|---|---|---|---|---|
| krea2-Cc-天魔-身材.safetensors | loras/krea2/ | 218 MB | **开** 1.0 | — | 国人画风 · 身材特化 | https://modelscope.cn/models/yan303145427/krea2-Cc-TM-GreatFigure |
| Krea2-realism_engine_v2_轻量.safetensors | loras/krea2/ | 41 MB | **开** 1.0 | — | 写实引擎（轻量版） | https://civitai.com/models/2742336?modelVersionId=3086201 |
| Krea2-滑块-细节PornMaster_Detail_Slider_Krea2_V1.safetensors | loras/krea2/ | 27 MB | **开** 0.70 | — | 细节滑块 | https://civitai.com/models/2736613?modelVersionId=3077180 |
| Krea2-2D动漫Anime_Flat_V20_nnegret.safetensors | loras/krea2/ | 218 MB | 关 1.0 | — | 2D 平涂动漫 | https://civitai.com/models/2741033?modelVersionId=3103017 |
| Afterlight_v1.safetensors | loras/krea2/ | 109 MB | 关 0.3 | — | 逆光氛围 | https://civitai.com/models/2776767?modelVersionId=3126819 |
| Yoneyama_Mai_Krea2.safetensors | loras/krea2/ | 109 MB | 关 1.0 | — | 米山舞画风 | https://civitai.com/models/2629905?modelVersionId=3160574 |
| Krea2-gpt anime render.safetensors | loras/krea2/ | 218 MB | 关 1.0 | — | GPT 动漫渲染 | https://civitai.com/models/2747738?modelVersionId=3090885 |
| harustyle_v1.6.safetensors | loras/krea2/ | 218 MB | 关 0.60 | — | 半写实插画 | https://civitai.com/models/2782337?modelVersionId=3196113 |
| Krea2-25D动漫Semi_Real_Anime_V2_NSW.safetensors | loras/krea2/ | 218 MB | 关 1.0 | — | 2.5D 厚涂动漫 | https://civitai.com/models/2741736?modelVersionId=3093169 |
| Krea2-亚洲asianMix_v1-bf16.safetensors | loras/krea2/ | 218 MB | 关 1.0 | — | 亚洲面孔混合 | https://civitai.com/models/2746042?modelVersionId=3093245 |
| 动漫补丁.safetensors | loras/krea2/ | 218 MB | 关 1.0 | — | 动漫角色融合 | https://civitai.com/models/2744462?modelVersionId=3086861 |
| krea2_identity_edit_v1.safetensors | loras/krea2/ | 1744 MB | 挂载（换脸/一致性链路） | — | 身份编辑（替代 InstantID 的角色一致性） | https://civitai.com/models/2761113?modelVersionId=3107391 |

- 前 3 条是默认开启组合；其余为风格库，换风格时**只切 active，不增删条目**。
- 天魔那条发布页在**魔搭**：https://modelscope.cn/models/yan303145427/krea2-Cc-TM-GreatFigure （文件同名、大小 228,616,016 B、SHA256 与本地一致）。

## 三、放哪里

```
ComfyUI/models/loras/krea2/
├── krea2-Cc-天魔-身材.safetensors
├── Krea2-realism_engine_v2_轻量.safetensors
├── Krea2-滑块-细节PornMaster_Detail_Slider_Krea2_V1.safetensors
├── …（其余 9 条同上表）
└── krea2_identity_edit_v1.safetensors     ← 1.8 GB，体积大，不用换脸可以先不下
```

目录名用 `krea2/` 只是跟作者一致（LoraManager 按文件名索引，子目录不影响识别）。Civitai 部分页面需登录才能下载。

## 四、未找到的

无。12 条 LoRA 全部定位到原始发布页（11 条 Civitai + 1 条魔搭）。
