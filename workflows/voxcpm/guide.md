# VoxCPM 子技能 · 配音使用守则（guide v1.0）

> 本守则与 `voxcpm全能工作流.json`（固定副本，**API 格式**）配套。**加载一律用本目录副本**，不用本仓库目录原件。

## 副本信息

| 项 | 值 |
|---|---|
| 固定副本 | `workflows/voxcpm/voxcpm全能工作流.json`（API 格式，5 节点：3/4/32/33） |
| 原件位置 | `F:\Comfy-Desktop\ComfyUI-Installs\jiujiu-2\ComfyUI\user\default\workflows\voxcpm全能工作流.json` |
| 归档 MD5 | `b0b2168c47d271f125a45bdc7d5fd594`（2026-08-25 入库） |
| 模型目录 | `F:\Comfy-Desktop\ComfyUI-Shared\models\voxcpm\VoxCPM2` |
| LoRA 目录 | `F:\Comfy-Desktop\ComfyUI-Installs\jiujiu-2\ComfyUI\models\voxcpm\loras\` |
| 角色语音库 | `F:\Comfy-Desktop\ComfyUI-Shared\models\voices\`（33 号节点引用 `voices/xxx.mp3`） |
| 输出 | `F:\Comfy-Desktop\ComfyUI-Shared\output\<YYYY-MM-DD>\audio\` |
| GPU | Intel Arc A770 16GB（XPU，graph 化已生效 ~7it/s） |

> 本工作流为 **API 格式**（作者官方导出，2026-08-25）：可直接改节点 inputs 提交，**无需浏览器加载转换**。

## 可改节点（唯一可控面，作者指定）

| 节点 ID | 功能 | 改法（JSON `inputs` 字段） | 使用频率 |
|---|---|---|---|
| **4** | VoxCPM 全能生成（综合汇总） | `target_text` = **生成文本**（最常改） | ★★★ 每次必改 |
| **4** | 同上 | `control_instruction` = **口吻**（中文自然语言描述声音特征/情绪） | ★ 偶尔 |
| **4** | 同上 | `lora_name` = **LoRA**（默认 `shorekeeper_20260729_114945.safetensors`） | ★ 偶尔 |
| **33** | 🎭 Character Voices（参考音频） | `voice_name` = 参考音频（默认 `voices/铅玻璃.mp3`）；`trim_start/trim_end` 裁剪 | ★ 偶尔 |
| 4 | 同上 | `seed`（默认 184692569466983；同文本可换 seed 换效果） | ☆ 可选 |
| 33 | 同上 | `reference_text`（参考音频的文本内容，auto_asr=true 时可空） | ☆ 极少 |

⚠️ 其余节点/参数（`work_mode`/`cfg_value`/`inference_steps`/`denoise_reference`/`normalize_*`/`model_profiles_json`/`reference_audio` 连接/32 号字符串节点）**一律不动**——作者默认设置。32 号是未连接遗留节点，不要改。

## 作者默认设置（勿动）

| 参数 | 值 |
|---|---|
| `work_mode` | 可控克隆 |
| `cfg_value` | 2 |
| `inference_steps` | 10 |
| `denoise_reference` | true（参考音频去噪，XPU 已适配） |
| `normalize_text` / `normalize_loudness` | true |
| `auto_asr` | true |
| `lora_name` | `shorekeeper_20260729_114945.safetensors` |
| `voice_name` | `voices/铅玻璃.mp3` |

## 口吻（control_instruction）写法

中文自然语言描述目标声音：**年龄/身份 + 音色 + 情绪/语调**。示例：
- 「年轻的英国贵族少女，声音优雅而冷清，仿佛在朗读文学作品」（副本默认）
- 「低沉沙哑的成熟女声，带着倦怠和一丝嘲讽」
- 「活泼俏皮的少女，语速快，尾音上扬」

## 提交方式（黑盒引子，agent 只传参数）

> 直接调用本目录引子 `voxcpm全能工作流.py`（与模板同 basename 自动配对），内部自动 内存拼 API → 递交 → 校验 node_errors → 轮询 → 拷贝音频 → 一行 JSON。agent 不看脚本内容。

```
python voxcpm全能工作流.py --text "台词" [--control "口吻" --lora xxx.safetensors --voice voices/x.mp3 --seed -1 --name 名字]
```
- `--text` 必填；`--control`（口吻）/`--lora`/`--voice`/`--seed`（-1 随机）可选，缺省保留模板默认。
- 返回 JSON：`{"kind":"audio","prompt_id":…,"file":"…"}`，取 `file` 交付。

## 手动脚本（备用，一般不用）

```bash
# ① 复制副本 → 改 [4].inputs.target_text（或 lora/口吻/参考音频）→ POST
cd "<你的目录>/tmp"
python - <<'EOF'
import json, uuid, requests
wf = json.load(open(r"<本仓库>\workflows\voxcpm\voxcpm全能工作流.json", encoding="utf-8"))
wf["4"]["inputs"]["target_text"] = "要生成的文本"          # ← 主要修改
# wf["4"]["inputs"]["control_instruction"] = "口吻..."      # 偶尔
# wf["4"]["inputs"]["lora_name"] = "xxx.safetensors"        # 偶尔
# wf["33"]["inputs"]["voice_name"] = "voices/xxx.mp3"       # 偶尔
r = requests.post("http://127.0.0.1:8188/prompt", json={"prompt": wf, "client_id": "dogma-voxcpm-" + uuid.uuid4().hex[:8]})
print(r.json())   # 须 node_errors: {}
EOF
# ② 轮询 /history/<prompt_id> → SaveAudio 输出文件名
# ③ 成品在 F 盘 output/<日期>/audio/ → 重命名有意义中文名后 MEDIA: 交付
```

> ⚠️ 提交前先查 `/queue`（作者跑图时禁开独立 GPU 进程，DEVICE_LOST 纪律）；提交后必查 `node_errors: {}`。
> ⚠️ 首次生成含 graph capture（~50s 一次性，三组件 captured 日志）——不是卡死；同模型实例后续生成免 capture。

## Pitfalls

1. **改文本是主操作**；改 lora/参考音频/口吻前先想清楚是不是真需要（默认设置是作者的偏好）。
2. **换 LoRA** = 模型重载 + graph 重新 capture（~60s 固定开销，技术必然）；**换参考音频** = 去噪/ASR/encode 重跑（首次 ~5-10s）；**同参考音频连续生成**命中缓存（显存级，~7s 固定）。
3. **临时文件已改 D 盘/F 盘**（`F:\Comfy-Desktop\ComfyUI-Shared\tmp\`，C 盘零写入）；正常流程自动清理。
4. **seed 上限 2^50**；副本默认 seed 可用，改文本后可留可换。
5. **zipenhancer 已 XPU 适配**（logs 不再 `cuda is not available`）；SenseVoice ASR 亦 XPU。
6. 交付文件**重命名为有意义中文名**（如「铅玻璃_测试台词_20260825.mp3」），禁自动编号。
7. 完成后清理：无临时服务器（API 直连无浏览器依赖）；D 盘临时脚本若建了则删。
8. **原件只读**：副本静态，不随作者原件实时更新（除非作者显式要求同步）。

## 验证清单

- [ ] 副本 JSON 加载（4 号节点 inputs 完整）
- [ ] 提交返回 node_errors: {}
- [ ] history status success，音频在 F 盘 output
- [ ] 交付文件为有意义中文名
