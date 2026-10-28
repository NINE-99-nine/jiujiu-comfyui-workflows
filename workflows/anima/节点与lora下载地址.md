# anima 工作流 · 节点与 LoRA 下载地址

> 适用文件：`anima模型（副本）.json`（UI 版，128 节点 / 21 分组；快速模式与正常模式共用同一份图）。
> 本文件只解决"缺件装不上"的问题：**装哪些自定义节点包、下哪些 LoRA、放哪里**。
> LoRA 已按 SHA256 逐一比对——本表里的地址下载到的文件，与作者本机在用的文件**大小与哈希完全一致**。

---

## 一、自定义节点包（ComfyUI Manager 可搜）

安装方式二选一：
1. **推荐**：ComfyUI Manager → Custom Nodes Manager → 搜包名 → Install → 重启 ComfyUI。
2. 手动：`git clone <地址>` 到 `ComfyUI/custom_nodes/`，再 `pip install -r requirements.txt`，重启。

| # | 节点包（custom_nodes 目录名） | 工作流里用到的节点 | 下载地址 | 何时需要 |
|---|---|---|---|---|
| 1 | comfyui-kjnodes | JoinStringMulti、StringConstantMultiline、GetNode / SetNode | https://github.com/kijai/ComfyUI-KJNodes | **必需**（提示词拼装主线） |
| 2 | comfyui-lora-manager | Lora Loader (LoraManager) | https://github.com/willmiao/ComfyUI-Lora-Manager | **必需**（画风 LoRA 全靠它加载） |
| 3 | comfyui-easy-use | easy cleanGpuUsed、easy float | https://github.com/yolain/ComfyUI-Easy-Use | **必需**（显存清理 + 浮点值） |
| 4 | comfyui_layerstyle | LayerUtility: ImageScaleByAspectRatio V2、LayerUtility: ImageReel / ImageReelComposit | https://github.com/chflame163/ComfyUI_LayerStyle | **必需**（分辨率链路） |
| 5 | ComfyUI-Danbooru-Gallery | ResolutionMasterSimplify（分辨率大师）、GroupIgnoreManager（逻辑门开关） | https://github.com/Aaalice233/ComfyUI-Danbooru-Gallery | **必需**（切快速/正常模式就靠它） |
| 6 | AnySwitch | AnySwitch | https://github.com/kevinzilin/AnySwitch | **必需**（分支选择） |
| 7 | controlaltai-nodes | TwoWaySwitch | https://github.com/gseth/ControlAltAI-Nodes | **必需**（文生图 / 图生图切换） |
| 8 | gguf | LoaderGGUF、ClipLoaderGGUF | https://github.com/calcuis/gguf | **必需**（GGUF 模型加载；正常模式的 LoaderGGUF 只在这里） |
| 9 | comfyui_essentials | SimpleMath+、MaskPreview+ | https://github.com/cubiq/ComfyUI_essentials | 特化修复分支 |
| 10 | comfyui-inpaint-cropandstitch | InpaintCropImproved、InpaintStitchImproved | https://github.com/lquesada/ComfyUI-Inpaint-CropAndStitch | 局部重绘/修复分支 |
| 11 | comfyui_controlnet_aux | CannyEdgePreprocessor、LineArtPreprocessor、ScribblePreprocessor、DWPreprocessor、Zoe_DepthAnythingPreprocessor、InpaintPreprocessor | https://github.com/Fannovel16/comfyui_controlnet_aux | 「🔼control生图」整组 |
| 12 | comfyui_ultimatesdupscale | UltimateSDUpscale | https://github.com/ssitu/ComfyUI_UltimateSDUpscale | SD 放大分支（默认旁路） |
| 13 | ComfyUI-Anima-LLLite | AnimaLLLiteApply | https://github.com/kohya-ss/ComfyUI-Anima-LLLite | 特化修复（LLLite 补丁） |
| 14 | seedvr2_videoupscaler | SeedVR2LoadDiTModel、SeedVR2LoadVAEModel、SeedVR2VideoUpscaler | https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler | **正常模式必需**（seedvr2 放大链） |
| 15 | comfyui-impact-pack | ImpactSwitch | https://github.com/ltdrdata/ComfyUI-Impact-Pack | 分支选择 |
| 16 | comfyui-wd14-tagger | WD14Tagger\|pysssss | https://github.com/pythongosssss/ComfyUI-WD14-Tagger | 图片反推标签 |
| 17 | comfyui-custom-scripts | LoraLoader\|pysssss、ShowText\|pysssss | https://github.com/pythongosssss/ComfyUI-Custom-Scripts | 辅助/兼容旧节点 |
| 18 | rgthree-comfy | Image Comparer (rgthree)、Any Switch (rgthree)、Fast Groups Bypasser (rgthree) | https://github.com/rgthree/rgthree-comfy | 对比图 / 分组开关面板 |
| 19 | ComfyUI_RH_LLM_API | RH_LLMAPI_NODE（提示词助手） | https://github.com/HM-RunningHub/ComfyUI_RH_LLM_API | 可选（外接大模型扩写提示词） |
| 20 | raffle | Raffle（抽卡） | https://github.com/rainlizard/ComfyUI-Raffle | 可选 |

**最小安装集**：只跑「快速模式」→ 装第 1–8 项即可；要跑「正常模式」（seedvr2 放大）→ 再加第 14 项。其余包里 9–13、15–18 属于特化修复 / ControlNet / SD 放大这些旁路分组，不点开就不用装（但缺了会报红节点）。

**不用装的部分**：`CLIPTextEncode`、`KSampler`、`UNETLoader`、`VAELoader`、`VAEEncode`/`VAEDecode`、`EmptyLatentImage`、`LoadImage`、`SaveImage`、`PreviewImage`、`ImageScaleBy`、`ImageScaleToTotalPixels`、`GetImageSize`、`ModelPatchLoader`、`SetLatentNoiseMask`、`PrimitiveFloat`/`PrimitiveInt`、`UpscaleModelLoader`、`Note` 都是 ComfyUI 自带（comfy-core）。

> ⚠️ 第 8 项容易装错：本工作流用的是 **`gguf` 包（calcuis）**，节点名是 `LoaderGGUF` / `ClipLoaderGGUF`。
> 另一个常见的 `city96/ComfyUI-GGUF` 节点名是 `UnetLoaderGGUF` / `CLIPLoaderGGUF`，**名字不同、不能互相顶替**。

---

## 二、LoRA 清单（工作流里真实挂载的 8 条）

| 文件名 | 放置目录 | 大小 | 触发词 | 作用 | 下载地址 |
|---|---|---|---|---|---|
| anima-turbo-lora-v0.1.safetensors | loras/anima/ | 142 MB | — | 加速 LoRA（快速/正常模式都用） | https://civitai.com/models/2560840?modelVersionId=2877687 |
| anima-base-1-masterpiece-v51.safetensors | loras/anima/优化/ | 132 MB | — | 画质优化三件套①（默认开） | https://civitai.com/models/929497?modelVersionId=2961717 |
| anima_context_detailer_base10.safetensors | loras/anima/优化/ | 88 MB | — | 画质优化三件套②（默认开，强度 0.6） | https://civitai.com/models/2620171?modelVersionId=2945421 |
| gpt-image-2_anima-base1_v1-1.safetensors | loras/anima/优化/ | 22 MB | @gpt-image-2 | 默认画风（默认开） | https://civitai.com/models/2564225?modelVersionId=2998634 |
| sky02Lightv3.safetensors | loras/anima/画风/ | 88 MB | — | 画风 B · 天空光感 | https://civitai.com/models/2652568?modelVersionId=2984923 |
| far off in the morning haze024064645510a_30.safetensors | loras/anima/画风/ | 175 MB | @cwuuuu | 画风 C · 晨雾 | https://civitai.com/models/2789826?modelVersionId=3143770 |
| Anima_in_real_update_v2_epoch_20.safetensors | loras/anima/画风/ | 264 MB | @Ani3rel | 画风 D · 写实化 | https://civitai.com/models/1979448?modelVersionId=3202009 |
| mixed_styles_anima-base1_v5.safetensors | loras/anima/画风/ | 178 MB | @style_name | 画风 E · 多画师混合 | https://civitai.com/models/723360?modelVersionId=2960448 |

- 前 3 条（masterpiece / context_detailer / gpt-image-2）是 [52] 节点里**默认 active 的画质三件套**；第 1 条 turbo 是独立挂在模型上的加速 LoRA；后 4 条是画风备选（默认关闭，换画风时才启用）。
- 换画风**不要增删条目**，只切 active；具体规则见 `guide.md` 的「画风选择规则」。

### 附录：guide 里还提到的四个备选画风（工作流默认不含，换画风时才下）

| 文件名 | 放置目录 | 大小 | 触发词 | 作用 | 下载地址 |
|---|---|---|---|---|---|
| animeoutlineV4_16.safetensors | loras/anima/画风/ | 18 MB | lineart, monochrome | 画风 F · 线稿 | https://civitai.com/models/16014?modelVersionId=28907 |
| chen-bin_V3.9.safetensors | loras/anima/画风/ | 89 MB | @4x0style | 画风 G · 鬼针草 | https://civitai.com/models/2511478?modelVersionId=3031167 |
| sheya chen-000192.safetensors | loras/anima/画风/ | 88 MB | @sheya chen | 画风 G · sheya chen | https://civitai.com/models/2774932?modelVersionId=3124633 |
| wy-000029_purged.safetensors | loras/anima/画风/ | 264 MB | @mochizuki kei | 画风 G · 望月けい | https://civitai.com/models/2487741?modelVersionId=3087653 |

---

## 三、放哪里（目录结构）

```
ComfyUI/models/loras/
└── anima/
    ├── anima-turbo-lora-v0.1.safetensors      ← 必须在 anima/ 根下（节点里写死了 anima\ 前缀）
    ├── 优化/
    │   ├── anima-base-1-masterpiece-v51.safetensors
    │   ├── anima_context_detailer_base10.safetensors
    │   └── gpt-image-2_anima-base1_v1-1.safetensors
    └── 画风/
        ├── sky02Lightv3.safetensors
        ├── far off in the morning haze024064645510a_30.safetensors
        ├── Anima_in_real_update_v2_epoch_20.safetensors
        └── mixed_styles_anima-base1_v5.safetensors
```

- `优化/`、`画风/` 只是分类习惯（LoraManager 按文件名索引，子目录不影响识别）；**`anima/` 这一层必须保留**。
- 下载后把预览图（.png/.jpg）一起放进去，LoraManager 才能显示缩略图。
- 部分 Civitai 页面需登录才能下载；下不动时挂代理，或到页面右侧 Files 里手动选同一版本。

---

## 四、核对方法

想确认自己下对没下错：文件大小应与上表一致；有 `sha256` 工具可对本地文件算哈希，与下表比对（本表哈希 = Civitai 该版本文件哈希，与作者本机在用的文件一致）。

| 文件名 | SHA256（前 16 位） |
|---|---|
| anima-turbo-lora-v0.1 | 68ed0aec6ff4ebc3 |
| anima-base-1-masterpiece-v51 | b330b46df1c71e44 |
| anima_context_detailer_base10 | aaaca6107e97bf98 |
| gpt-image-2_anima-base1_v1-1 | 6ecff93984c1b084 |
| sky02Lightv3 | c294ccf980206f38 |
| far off in the morning haze024064645510a_30 | 3ca7179d58d56a99 |
| Anima_in_real_update_v2_epoch_20 | f517e791fadba65e |
| mixed_styles_anima-base1_v5 | d77ccff18628e5bf |
| animeoutlineV4_16 | 2fcd88e6aa07b2db |
| chen-bin_V3.9 | 5eeebcf1afda7e36 |
| sheya chen-000192 | 59c55b1cca40058d |
| wy-000029_purged | 43ebff02888860af |

## 五、未找到的

无。12 个 LoRA 全部定位到原始发布页。

> 本文件只覆盖**节点包**与**LoRA**。底模（anima-turbo v1.1）、VAE、Qwen3-0.6B 文本编码器 GGUF、RealESRGAN 放大模型、SeedVR2 模型、LLLite 补丁这类**大模型文件**不在本次范围内。
