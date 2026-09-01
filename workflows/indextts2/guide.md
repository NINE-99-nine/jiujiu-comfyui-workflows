# IndexTTS-2 子技能 · 配音使用守则（guide v1.0）

> 本守则与 `IndexTTS-2集成工作流.json`（固定副本）配套。**加载一律用本目录副本**，不用本仓库目录原件。

## 副本信息

| 项 | 值 |
|---|---|
| 固定副本 | `workflows/indextts2/IndexTTS-2集成工作流.json`（本技能内） |
| 原件位置 | `F:\Comfy-Desktop\ComfyUI-Installs\jiujiu-2\ComfyUI\user\default\workflows\🌈 IndexTTS-2 integration.json` |
| 角色库（voices） | `F:\Comfy-Desktop\ComfyUI-Shared\models\voices\`（extra_model_paths 映射 `'voices': 'voices/'`） |
| 已入库角色 | 守岸人 / 十四行诗 / 库珀花环 / 铅玻璃（音频+同名 txt，清单见 `references/voice-library.md`） |
| 模型目录 | `F:\Comfy-Desktop\ComfyUI-Shared\models\TTS\IndexTTS\` |
| 输出 | `F:\Comfy-Desktop\ComfyUI-Shared\output\YYYY-MM-DD\`（F 盘 ✓） |
| GPU | Intel Arc A770 16GB（XPU） |

> ⚠️ **narrator 已设为 none**（作者设定）：**所有输入文本必须带角色标签**，不能依赖 narrator 兜底。未在库中的角色回退到 David_Attenborough 示例音——务必只用已入库角色。

## 提交方式（黑盒引子，agent 只传参数）

> 直接调用本目录引子 `🌈 IndexTTS-2 integration-API.py`（与导出的 API 模板同 basename 自动配对），内部自动 内存拼 API → 递交 → 校验 node_errors → 轮询 → 拷贝音频 → 一行 JSON。agent 不看脚本内容。

```
python "🌈 IndexTTS-2 integration-API.py" --text "台词" [--name 名字]
```
- `--text` 必填：台词（narrator=none，**必须带 `[角色名]` 标签**，角色名与 voices 库一致）。只改 [65] 文本节点。
- 返回 JSON：`{"kind":"audio","prompt_id":…,"file":"…"}`，取 `file` 交付。

## 手动流程（备用，一般不用）

### 1. 起临时 CORS 服务器（喂工作流副本给浏览器前端）

```bash
# D 盘运行（严禁 C 盘！），后台启动
cd "<你的目录>/tmp" && python serve_wf.py   # background=true
curl -s http://127.0.0.1:8765/ping   # 验证：pong
```

脚本从伞技能 `scripts/serve_wf.py` 复制（WF_DIR 需指向伞技能 workflows/ 目录）。

### 2. 浏览器加载工作流副本 + 改 [65] 文本节点

```js
// ① 导航到 http://127.0.0.1:8188/（browser_navigate）
// ② fetch 工作流副本（中文文件名必须 encodeURIComponent）：
fetch('http://127.0.0.1:8765/wf/'+encodeURIComponent('indextts2/IndexTTS-2集成工作流.json')).then(r=>r.json())
  .then(d=>{ window.__wf=d; return app.loadGraphData(d); });

// ③ 只改 [65] 默认文本输入节点的 widgets[0].value（完整台词）：
//    ⚠️ 节点对象路径（loadGraphData 后直接改 widget 值），不是数据路径！
const n65 = app.graph.getNodeById(65);
n65.widgets[0].value = '[守岸人] 守岸人，这个称呼就很好。\n[库珀花环] Mr. Kozlov would always paint my face.';
```

### 3. 官方转换 + 提交

```js
app.graphToPrompt().then(res=>{
  const p=res.output;   // ⚠️ 结果在 .output 字段！
  window.__final_prompt=p;
  return fetch('/api/prompt',{method:'POST',body:JSON.stringify({prompt:p,client_id:'dogma-'+Date.now()})})
    .then(r=>r.json());   // node_errors 为空即零错误
});
```

### 4. 轮询 + 交付

```bash
for i in $(seq 1 60); do sleep 10; h=$(curl -s -m 5 "http://127.0.0.1:8188/history/<PROMPT_ID>" 2>/dev/null); if [ -n "$h" ] && [ "$h" != "{}" ]; then echo "$h" | python -c "import sys,json; h=json.load(sys.stdin); [print('音频:',o.get('audio',[{}])[0].get('filename') if o.get('audio') else [a.get('filename') for a in o.get('images',[])]) for e in h.values() for o in e.get('outputs',{}).values()]"; break; fi; done
```

音频成品在 `F:\Comfy-Desktop\ComfyUI-Shared\output\<YYYY-MM-DD>\` → **重命名为有意义中文名**后 MEDIA: 交付（如「守岸人_台词_20260809.mp3」）。

## 文本输入语法

| 语法 | 效果 | 示例 |
|---|---|---|
| `[角色名] 台词` | 该角色的声音 | `[守岸人] 你好呀` |
| 多角色分段 | 自动拼接多人对话 | `[守岸人] 第一句\n[铅玻璃] 第二句` |
| `[角色A:情感参考] 台词` | 角色A声音 + 情感参考音频的情绪 | `[库珀花环:crestfallen_original] 我的病会好吗` |
| 无标签文本 | ⚠️ 用 narrator（已设 none → 不适用） | 避免！ |

**角色名必须与角色库音频文件名完全一致**（含大小写/中文）。查找优先级：`models/voices/` > `models/TTS/voices/` > `voices_examples/`。

## 角色库维护（新增角色）

```bash
# 1. 角色音频（5-15s 最佳，.wav/.mp3/.flac/.ogg/.m4a/.aac）
# 2. 同名 .txt（纯参考文本，无多余内容——作者习惯）
cp "源音频.mp3" "<ComfyUI模型路径>/models/voices/角色名.mp3"
echo "参考文本" > "<ComfyUI模型路径>/models/voices/角色名.txt"
# 3. ComfyUI 里点「♻️ Refresh Voice Cache」或重启
```

## 性能参数（引擎节点 [123] 默认值）

| 参数 | 值 | 说明 |
|---|---|---|
| `device` | xpu | A770 推理 |
| `emotion_alpha` | 0.7 | 情感强度 |
| `num_beams` | **1** | ⚠️ 默认3会慢3倍，已调1 |
| `use_fp16` | True | 加速 |
| `max_text_tokens_per_segment` | 120 | 每段上限 |
| `interval_silence` | 200ms | 段间静音 |

⚠️ **首次运行加载模型需 2-3 分钟**（6 个组件 ~9GB），之后引擎缓存复用，每段 ~18s。

## 节点地图（本工作流）

| 节点 ID | 类型 | 作用 | 改法 |
|---|---|---|---|
| **65** | PrimitiveStringMultiline | **默认文本输入（唯一要改的）** | 节点对象 widgets[0].value |
| 123 | ⚙️ IndexTTS-2 Engine | 引擎配置 | 一般不碰 |
| 47 | 🎤 TTS Text | 统一入口（text 来自 65 链路） | 不碰 |
| 130 | 🎭 Character Voices | 角色选择（narrator=none） | 不碰 |
| 124 | 🌈 Text Emotion | 情感模板（`{seg}` 动态） | 可选 |
| 125 | 🌈 Emotion Vectors | 8 维情感滑杆 | 可选 |
| 131 | LoadAudio | 情感参考音频 | 可选 |

⚠️ 链路：65 → 98 → 132 → 99 → 47(text)。**82 是断链旧节点，不要改它**！
⚠️ 131 引用的音频文件若被移动会提交失败——改 65 前先确认可选节点无断链。

## Pitfalls

1. **输入必须带角色标签**（narrator=none）——不带会回退示例音或报错。
2. **`[角色:情感]` 里的情感参考**：必须是语音库已有角色名或 voices_examples 里存在的音频名。
3. **graphToPrompt() 结果在 `.output`** 字段。
4. **browser_console 全局变量**用 `window.__xxx` 防冲突。
5. **fetch 中文文件名必须 encodeURIComponent**。
6. **临时服务器脚本必须放 D 盘**（严禁 C 盘写入）。
7. **首次生成 2-3 分钟**是模型加载，不是卡死；后续复用缓存。
8. **角色音频 >15s 可能带入杂质**，克隆音色不纯——必要时用 [130] 的 trim 参数裁剪。
9. 完成后**清理**：杀掉临时服务器进程，删除 D 盘 tmp 脚本（可选）。
10. **输出音频重命名**为有意义中文名交付（如「守岸人_台词_20260809.mp3」）。

## 验证清单

- [ ] curl 8765/ping 返回 pong
- [ ] 65 节点文本已更新（含角色标签）
- [ ] 提交返回 node_errors: {}
- [ ] history 状态 success，音频在 F 盘 output
- [ ] 原件未改（副本机制）
- [ ] 交付文件为有意义中文名
