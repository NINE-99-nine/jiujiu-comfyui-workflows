# qwen_image2.1 工作流 · 节点与 LoRA 下载地址

> 适用文件：`qwen_image2.1汇总.json`（UI 版，10 节点）。
> **本工作流不含任何 LoRA**——它靠模型本身做文生图/图像编辑，没有风格 LoRA 挂载。

## 一、自定义节点包

| # | 节点包 | 用到的节点 | 下载地址 | 何时需要 |
|---|---|---|---|---|
| 1 | rgthree-comfy | Image Comparer (rgthree) | https://github.com/rgthree/rgthree-comfy | 前后对比图（非必需） |

**不用装的部分**：`LoadImage`、`SaveImageAdvanced`、`ResolutionSelector`、`ImageScaleToTotalPixels`、`MarkdownNote`、`Note` 都是 ComfyUI 自带（含两个子图 subgraph，内部也全是自带节点）。

## 二、LoRA

无。本工作流没有 Lora 加载节点，不需要下载任何 LoRA。

## 三、说明

- 需要的是**模型文件**（Qwen-Image 2.1 主模型 / 文本编码器 / VAE），不是 LoRA；模型下载地址不在本文件范围。
- 如果用的时候发现节点报红，八成是 ComfyUI 版本太旧（`SaveImageAdvanced`、`ResolutionSelector`、`QwenImage21` 系列都是较新版本才有的原生节点），更新 ComfyUI 本体即可。
