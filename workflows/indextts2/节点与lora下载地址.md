# IndexTTS-2 工作流 · 节点与 LoRA 下载地址

> 适用文件：`IndexTTS-2集成工作流.json`（UI 版，26 节点 / 6 分组）。
> **本工作流不含 LoRA**——它是 TTS 配音，靠"参考音频"定音色，不靠 LoRA。

## 一、自定义节点包

| # | 节点包 | 用到的节点 | 下载地址 | 何时需要 |
|---|---|---|---|---|
| 1 | TTS-Audio-Suite | IndexTTSEngineNode、IndexTTSEmotionOptionsNode、CharacterVoicesNode、UnifiedTTSTextNode、UnifiedTTSSRTNode、QwenEmotionNode | https://github.com/diodiogod/TTS-Audio-Suite | **必需**（全部音频节点都来自这一个包） |

**不用装的部分**：`PreviewAudio`、`LoadAudio`、`PreviewAny`、`PrimitiveStringMultiline`、`Reroute`、`MarkdownNote` 都是 ComfyUI 自带（新版原生音频节点）。

## 二、LoRA

无。本工作流没有 LoRA 加载节点，不需要下载任何 LoRA。

## 三、为什么这里没有 LoRA

IndexTTS-2 的音色来自**参考音频**（`models/voices/\*.mp3` 或节点里指定的人声样本），不是 LoRA：

- 想要某个角色的声音 → 放一段该角色的干净人声到 `ComfyUI/models/voices/`，在角色节点里选中即可。
- 本工作流里的 `CharacterVoicesNode` 读的就是这个目录，跟 LoRA 体系无关，所以没有可下载的 LoRA 地址。

## 四、说明

需要的是 IndexTTS-2 的模型权重（首次运行自动下载）与参考音频；节点包只有上面这一个。
