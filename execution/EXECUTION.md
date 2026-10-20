# 提交执行（黑盒链路）

> ComfyUI 出图统一走「引子脚本 → 通用递交」黑盒链路。agent 只填引子暴露的参数，全程不看脚本内部。

## 链路
```
引子脚本(传参) → 内存拼一次性 API dict(不落盘) → execution/comfy_submit.py 递交
→ ComfyUI 对应工作流 → 提交校验 node_errors → 轮询 → 成品自动拷到 _work/<引子basename>/
→ 打印一行 JSON {"prompt_id","file","size"}
```

## execution/ 两个脚本
- `env.py` —— **环境脚本，唯一随环境改的件**：ComfyUI 地址、模型/输入目录、工作区 `WORK_ROOT`。换 ComfyUI 环境只改这里，全部工作流照常跑。
- `comfy_submit.py` —— **通用 API 递交执行器**（唯一真正碰 ComfyUI 的件）：提交 → 校验 `node_errors:{}` → 轮询 → 拷贝并打印 JSON。含 seed 随机化、`__value__` 解包（含 loras）。

## 使用（agent）
1. 进工作流目录，读 `guide.md` 的接口参数表 + 提示词构筑。
2. `python workflows/<名>/<名汇总_api>.py --prompt "…" [--w … --h … --name … --seed … --loras …]`
3. 只读返回的那行 JSON，取 `file` 即可交付。

## 硬约束
- 引子与模板**同 basename**，自动配对 `Path(__file__).with_suffix('.json')`，无需指定模板路径。
- 只改各工作流 guide 允许的节点；loras **默认=模板原样**，传参只改**点名条目**（绝不增删/绝不误开其他）。
- 中间 API dict 只在内存，**绝不落盘**；固定模板只读，绝不改动。
