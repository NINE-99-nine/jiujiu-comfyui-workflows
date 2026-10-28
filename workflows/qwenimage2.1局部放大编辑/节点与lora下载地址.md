# qwenimage2.1 局部放大编辑 · 节点与 LoRA 下载地址

> 适用文件：`qwenimage2.1局部放大编辑.json`（UI 版，28 节点 / 6 分组）。
> **本工作流不含任何 LoRA**——它是 SAM3 定位 + 裁剪放大 + 局部重绘的编辑链路，不挂风格 LoRA。

## 一、自定义节点包

| # | 节点包 | 用到的节点 | 下载地址 | 何时需要 |
|---|---|---|---|---|
| 1 | comfyui-inpaint-cropandstitch | InpaintCropImproved、InpaintStitchImproved | https://github.com/lquesada/ComfyUI-Inpaint-CropAndStitch | **必需**（裁出局部再拼回原图） |
| 2 | comfyui-rvtools_v2 | Image to RGB [RvTools] | https://github.com/r-vage/ComfyUI-RvTools_v2 | **必需**（转 RGB） |
| 3 | comfyui_layerstyle | LayerColor: BrightnessContrastV2 | https://github.com/chflame163/ComfyUI_LayerStyle | 亮度/对比微调 |
| 4 | comfyui-kjnodes | ImageAndMaskPreview | https://github.com/kijai/ComfyUI-KJNodes | 遮罩预览 |

**不用装的部分**：`UNETLoader`、`CLIPLoader`、`VAELoader`、`CheckpointLoaderSimple`、`KSampler`、`VAEDecode`、`CLIPTextEncode`、`LoadImage`、`SaveImageAdvanced`、`ResolutionSelector`、`SAM3_Detect`、`TextEncodeQwenImage21`、`QwenImage21Cache`、`ComfySwitchNode`、`String` 都是 ComfyUI 自带。

> `SAM3_Detect` / `QwenImage21Cache` 属于新版原生节点，ComfyUI 太旧会报红——更新本体即可。

## 二、LoRA

无。虽然图里保留了 `LoraLoaderModelOnly` 节点位（旁路状态），但**没有挂任何 LoRA 文件**，不需要下载。

## 三、说明

- 需要的是 Qwen-Image 2.1 主模型 + SAM3 权重（首次运行会自动从 HuggingFace 拉取），不涉及 LoRA。
