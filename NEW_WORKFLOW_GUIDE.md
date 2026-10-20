# 新增子技能 SOP（NEW_WORKFLOW_GUIDE.md）

作者要把新的 ComfyUI 工作流接入本库时的标准流程。**新增任何子技能前先读本文件。**

## ⚠️ 核心原则：静态副本，不做实时更新（作者明确要求，稳定性优先）

1. **工作流副本是静态快照**——入库时拷贝一份固定副本，之后**绝不随作者的原件实时同步**。用户没有明确要求，禁止偷偷更新副本。
2. 为什么：原件被作者实时编辑（调参/改节点/清默认词），副本若跟着变，每次出图行为不一致、历史结果不可复现。副本保证**行为一致、可复现**。
3. **副本什么时候更新**：作者显式说"更新副本" / "同步新版" / "工作流升级了"时，才重新拷贝原件覆盖副本，并同步更新该子技能的 guide.md（节点地图可能变）。
4. 更新后必须记录：拷贝时间、变更要点、guide.md 版本号。

## 新增工作流四步（对作者：你只需在 ComfyUI 导出 API 模板，剩下的我来）

```
① 作者 ComfyUI「导出(API 格式)」→ 存为 workflows/<新工作流名>/<名>_api.json（模板）
② 写引子 <名>_api.py（与模板同 basename）→ 参数注入模板指定节点 → 调 execution/comfy_submit.submit()
③ 写 guide.md → 接口参数表 + 提示词构筑 + 注意事项
④ 更新总 SKILL.md → 任务类型速查表加一行 + 目录结构图补一项
```

详细步骤：

### Step 1 — 固化 API 模板（唯一合法 = 作者 ComfyUI 内置「导出(API 格式)」）

- 作者在 ComfyUI 打开工作流 → 菜单「导出(API)」→ 存为 `workflows/<工作流名>/<名>_api.json`。
- **禁止手动构建 / 禁止 graphToPrompt 产物当模板**（历史教训：自建模板画风错，官方导出正常）。
- 归档记录 MD5；模板**只读**——引子只在内存改，绝不写模板文件。

### Step 2 — 写使用守则 guide.md

每个子技能文件夹必含 guide.md，结构模板（拷贝 `workflows/_template/`）：

```markdown
# <工作流名> 子技能 · 使用守则（guide v1.0）

> 本守则与 <文件>.json（固定副本）配套。加载一律用本目录副本，不用原件。

## 副本信息
| 项 | 值 |
|---|---|
| 固定副本 | workflows/<名>/<文件>.json |
| 原件位置 | F:\...\user\default\workflows\<原件>.json |
| 归档校验 | MD5：<归档时> |

## 可改节点（唯一可控面）
| 节点 ID | 功能 | 改法 |
|---|---|---|
| ... | ... | 数据路径 widgets_values[0] / 节点对象 widgets[i].value |

⚠️ 作者已屏蔽/生效节点说明（以实测为准，不要照抄别的 guide）

## 提交方式（黑盒引子，agent 只传参数）
1. 直接调本目录引子 `python <名>_api.py --prompt "…" [--w … --h … --name … --loras 名:强度:on]`
2. 引子自动 内存拼 API → `execution/comfy_submit.py` → `node_errors:{}` 校验 → 轮询 → 拷成品到 `_work/<引子basename>/` → 一行 JSON
3. 输出 = `{"kind":"image|audio","prompt_id":…,"file":"…"}`，取 `file` 交付
```

**写 guide.md / 引子前必须先看 API 模板**：确认可改节点 id、`class_type`、`inputs` 字段名（如 PrimitiveStringMultiline→`value`、StringConstantMultiline→`string`）、输出节点（SaveImage/SaveAudio）——不要从 SKILL.md 或旧 guide 猜。可临时写个 inspect 脚本读模板打印关键节点，用完即删。

### Step 3 — 注册到总 SKILL.md

- 「任务类型 → 入口速查」表加一行
- 「目录结构」图补一项
- 如有独立提示词规则，放子技能 references/ 并在 guide 中引用

## 子技能文件夹规范

```
workflows/<工作流名>/
├── <名>_api.json        ← 官方导出 API 模板（静态只读）
├── <名>_api.py          ← 引子（同 basename 自动配对，agent 只传参）
├── guide.md             ← 使用守则（接口参数表 / 规则 / 注意事项）
└── references/          ← 该工作流专属参考（提示词规则、参数表等）
```

## 验证清单（新增子技能后）

- [ ] 副本入库，MD5 已记录
- [ ] guide.md 写完，可改节点经实测验证（非猜测）
- [ ] 总 SKILL.md 速查表已更新
- [ ] 引子可一键跑通（`--prompt` 必填，返回一行 JSON，成品落 `_work/<引子basename>/`）
- [ ] 作者确认后：出图/执行实测一次（可复现）
- [ ] 副本未随原件实时更新（除非作者显式要求）

## 版本日志

- v1.0：静态副本原则 + 三步注册流程（2026-08-09）
