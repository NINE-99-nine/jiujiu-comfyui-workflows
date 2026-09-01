# Comfy Desktop 运维速查

## 日志
- 目录: `%APPDATA%\Comfy Desktop\logs\`
- `app.log` = 当前/最近一次启动（正在运行的实例实时写入）
- `app.log_<UTC时间戳>.log` = 历史启动滚动归档（按修改时间排序找最新）
- 启动窗口消失 ≠ 日志消失：启动完成后日志继续在后台写
- 诊断 grep: `ERROR|WARNING|Traceback|sqlite3.OperationalError|DLL load failed|Failed`

## 崩溃转储
- `%APPDATA%\Comfy Desktop\Crashpad\reports\*.dmp`（每个约 35MB，纯历史参考）

## 目录布局（实测案例）
- 安装实例: `F:\Comfy-Desktop\ComfyUI-Installs\<实例名>\ComfyUI`（.venv 在实例内）
- 共享模型: `F:\Comfy-Desktop\ComfyUI-Shared\models\{checkpoints,unet,loras,vae,text_encoders,...}`
- 输出: `--output-directory` 启动参数（可在 `/system_stats` 的 argv 里读到真实值）
- 工作流存档: `<实例>\ComfyUI\user\default\workflows\`
- 实例名常与用户相关（如 jiujiu-2）——别假设默认名，从 argv/log 里确认

## 启动 argv 解读（/system_stats 返回）
```
--extra-model-paths-config C:\Users\...\shared_model_paths.yaml  ← 共享模型路径配置
--input-directory / --output-directory                           ← 输入/输出目录（可能跨盘）
--enable-manager                                                ← ComfyUI-Manager 已启用
```
注意: Comfy Desktop 默认 output 可能在 C 盘；用户若厌恶 C 盘写入，提示其在设置中改到其他盘。

## 常见启动告警分级
- 🔴 真问题: sqlite3.OperationalError（某自定义节点 DB 路径坏）、DLL load failed（装坏的节点）、
  TTS/音频套件缺依赖（日志常自带 `install.py` 修复命令，原样给用户）、LoRA 文件名冲突（Manager Doctor 面板）
- 🟡 无害: pip invalid distribution 残留、deprecated API 警告、Manager 网络拉取失败、matrix-nio 缺失
- 模型缓存健康信号: "Lora cache hydrated ... N models" / "Checkpoint cache hydrated ... N models"

## 提示词小助手（用户提示词素材源）
- 位置: `<实例>\ComfyUI\user\default\prompt-assistant\tags\默认标签.csv`
- 列结构: `标签名 | 标签值 | 一级分类 | 二级分类 | ...`
- 用户在此存自定义 IP 角色串（例: 守岸人 → `shorekeeper_(wuthering_waves),Shorekeeper from Wuthering Waves`，分类 IP角色/鸣潮）
- 写角色提示词前先 grep 这里——用户可能已备好标准触发词；无匹配再自行从 safetensors 标签提取

## 实例环境（jiujiu-2，实测）
- GPU: Intel Arc A770 16GB（PyTorch 2.10.0+xpu）——SDXL 系流畅，Flux/视频类吃力
- anima 工作流（anima模型.json）有两条提示词链: 主链[228] FLS_SamplerV4（inpaint 修复分支，提示词=质量词+修手词）；最终出图链 [60] KSampler → UltimateSDUpscale → [40] SaveImage（提示词=[7] 拼接: 质量词+画风+人设一+人设二+LLM扩写）——改人设二[23]即改最终出图内容
