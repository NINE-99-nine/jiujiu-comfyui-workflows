# VoxCPM 工作流 · 节点与 LoRA 下载地址

> ⚠️ 本工作流**没有 UI 版文件**，只有 API 版：`voxcpm全能工作流_API.json`（+ 同名 `.py` 引子），在 ComfyUI 界面里直接打开不会得到完整画布。
> 因此下面的节点清单取自这份 API 模板本身。

## 一、自定义节点包

| # | 节点包 | 用到的节点 | 下载地址 | 何时需要 |
|---|---|---|---|---|
| 1 | ComfyUI-VoxCPM-nkxx | voxcpm_nkxx_unified_generator（唯一主节点） | https://github.com/jieg9341-lab/ComfyUI-VoxCPM-nkxx | **必需** |
| 2 | TTS-Audio-Suite | CharacterVoicesNode（多角色音色表） | https://github.com/diodiogod/TTS-Audio-Suite | **必需**（用多角色模式时） |

**不用装的部分**：`SaveAudio`、`PrimitiveStringMultiline` 都是 ComfyUI 自带。

## 二、LoRA

**本工作流的 LoRA 不提供下载，也不会提供。**

| LoRA | 情况 |
|---|---|
| `浊心斯卡蒂_20260901_223158.safetensors` | 作者**本地自己炼的音色 LoRA**，只在本机训练产出的，没有公开仓库、也没有发布页，因此无法给出地址（不是没找到，是不存在公开来源）。 |

### 拿不到这条 LoRA 时怎么跑

1. 把该节点的 `lora_name` **清空/置空** —— 工作流会用 VoxCPM 基础音色，配合"极致克隆 + 参考音频"照常出结果；
2. 或者换成你自己的音色 LoRA（同一目录 `ComfyUI/models/loras/` 下任意 `.safetensors`）；
3. 参考音频放在 `ComfyUI/models/voices/`（本项目里 `浊心斯卡蒂.mp3` 就是参考音频，不是 LoRA）。

## 三、为什么这里没有可下载的 LoRA

VoxCPM 是"可控克隆"型 TTS：音色由**参考音频 + 自炼音色 LoRA**共同决定。作者用的那条是私人训练产物，属于本机资产，发布版里只保留说明，不给文件也不给地址。

## 四、未找到的

不适用——这一条属于"作者自炼、无公开来源"，不是搜索遗漏。
