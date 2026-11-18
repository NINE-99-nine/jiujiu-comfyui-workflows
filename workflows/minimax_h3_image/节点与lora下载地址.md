# MiniMax H3 Image 工作流 · 节点与 LoRA 下载地址

> 适用文件：`minimax_h3_image.json`（UI 版，73 节点 / 12 分组；文生图与图像编辑两套链路在同一个文件里，按分组切换）。
> 模型三条直链均已实测可下载（HEAD 200），SHA256 与 Hugging Face 官方仓库逐位一致。

## 一、自定义节点包

**一个都不用装。** 工作流用到的全部节点来自 ComfyUI 本体，2026-11-18 在本机 ComfyUI **0.45.3** 上逐个向 `/object_info` 核对了 `python_module`：

| 节点 | 来源模块 |
|---|---|
| MiniMaxH3ImageConditioning | `comfy_extras.nodes_minimax_h3` |
| ResolutionSelector | `comfy_extras.nodes_resolution` |
| ComfySwitchNode | `comfy_extras.nodes_logic` |
| ResizeImageMaskNode、ImageScaleToTotalPixels | `comfy_extras.nodes_post_processing` |
| GetImageSize | `comfy_extras.nodes_images` |
| PrimitiveStringMultiline、PrimitiveFloat、PrimitiveBoolean | `comfy_extras.nodes_primitive` |
| UNETLoader、CLIPLoader、VAELoader、LoraLoaderModelOnly、KSampler、VAEDecode、ConditioningZeroOut、EmptyLatentImage、LoadImage、SaveImage、PreviewImage | 内置 `nodes` |

**版本要求**：ComfyUI 需包含 `nodes_minimax_h3`（0.45.x 已带）。老版本会报「节点缺失 MiniMaxH3ImageConditioning」。

- ComfyUI 本体：https://github.com/comfyanonymous/ComfyUI
- 官方工作流模板（本工作流的原型，可对照节点结构）：https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_minimax_h3_image_t2i.json

**不用装的部分**：机器上可能装着 `llm-toolkit` 之类的包，它也提供过一个同名 `ResolutionSelector`，但**工作流吃的是 ComfyUI 自带的 `comfy_extras.nodes_resolution`**（输入是 aspect_ratio / megapixels / multiple）。所以不装任何自定义包也能完整跑通。

## 二、模型下载（魔搭 ModelScope）

仓库：https://www.modelscope.cn/models/Comfy-Org/MiniMax-H3-Image （DiT + VAE）
　　　https://www.modelscope.cn/models/Comfy-Org/minimax-H3 （文本编码器在这个仓库里）

| # | 放到 ComfyUI 的 | 文件 | 大小 | 魔搭直链 |
|---|---|---|---|---|
| 1 | `models/diffusion_models/` | minimax_h3_image_pruned_int8_convrot.safetensors | 21.0 GB | https://www.modelscope.cn/models/Comfy-Org/MiniMax-H3-Image/resolve/master/diffusion_models/minimax_h3_image_pruned_int8_convrot.safetensors |
| 2 | `models/text_encoders/` | qwen3vl_32b_minimax_h3_int8_convrot.safetensors | 27.1 GB | https://www.modelscope.cn/models/Comfy-Org/minimax-H3/resolve/master/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors |
| 3 | `models/vae/` | minimax_h3_image_vae_fp16.safetensors | 1.17 GB | https://www.modelscope.cn/models/Comfy-Org/MiniMax-H3-Image/resolve/master/vae/minimax_h3_image_vae_fp16.safetensors |

Hugging Face 官方源（同文件，二选一）：

- https://huggingface.co/Comfy-Org/MiniMax-H3-Image
- https://huggingface.co/Comfy-Org/MiniMax-H3

**SHA256 校验**（与官方仓库一致，可用来验证下载完整）：

| 文件 | SHA256 |
|---|---|
| minimax_h3_image_pruned_int8_convrot.safetensors | `83eb140f1ff95c068f8a6886e6d3f3d0d4ab2e07bb2fe6d2ef992a51146ee622` |
| qwen3vl_32b_minimax_h3_int8_convrot.safetensors | `bc2ced0fbea64757fa9acddccfc0b3f4819d1dcf1da6c124d690d368be283923` |

**可选，不是必需**：`qwen3.5_9b_w4a8_gptq.safetensors`（7.3 GB，`models/text_encoders/`）是官方「提示词增强（PE）」用的编码器；本工作流的 PE 开关是残留节点、默认旁路，**不装也能正常出图**。要玩提示词扩写再下：
https://www.modelscope.cn/models/Comfy-Org/MiniMax-H3-Image/resolve/master/text_encoders/qwen3.5_9b_w4a8_gptq.safetensors

## 三、LoRA

| 文件 | 放哪 | 默认强度 | 来源 |
|---|---|---|---|
| KOOK-Minimax-H3-image-尘星.safetensors | `models/loras/Minimax_H3_Image/` | 0.8 | **未找到公开下载页** |

说明：这套工作流的作者 LoRA「尘星」（KOOK 出品，基于 MiniMax H3 Image）在魔搭与 Hugging Face 上都没有检索到公开仓库，属于作者自有文件。

**没有这个 LoRA 的两种处理**：

1. 把 `LoraLoaderModelOnly` 右键设为「忽略」（或删掉），模型直连 KSampler——6 步 / cfg 1 / lcm 的原生路径照样出图；
2. 换成你自己想要的任意 H3-Image LoRA，强度按 0.6–0.8 起调。

LoRA 目录里的文件名必须与工作流里写的完全一致（`Minimax_H3_Image\KOOK-Minimax-H3-image-尘星.safetensors`），改过名就要在节点里重新选一次。

## 四、模型存放结构

```
📂 ComfyUI/
└── 📂 models/
    ├── 📂 diffusion_models/
    │   └── minimax_h3_image_pruned_int8_convrot.safetensors
    ├── 📂 text_encoders/
    │   ├── qwen3vl_32b_minimax_h3_int8_convrot.safetensors
    │   └── qwen3.5_9b_w4a8_gptq.safetensors        ← 可选（提示词增强）
    ├── 📂 vae/
    │   └── minimax_h3_image_vae_fp16.safetensors
    └── 📂 loras/
        └── 📂 Minimax_H3_Image/
            └── KOOK-Minimax-H3-image-尘星.safetensors   ← 没有就忽略该节点
```

## 五、显存与磁盘提醒

- 三件套合计约 **49 GB 磁盘**；按 INT8 运行，需要一张能吃下 20 GB 级权重的卡（外加 VAE 与激活），16 GB 显存需靠系统内存卸载，速度会明显变慢。
- 生成分辨率按 **8MP 起步、上限 16MP**、宽高为 **32 的倍数**；2–4MP 会明显发糊。
- 提示词扩写模型（PE）另占 7.3 GB，不用可以不下。
