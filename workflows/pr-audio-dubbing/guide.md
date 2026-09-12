# PR 自动配音子技能 · 使用守则（guide v1.0）

> 将 VoxCPM 生成的配音音频，**自动导入 PR 并对齐到字幕起始时间**。核心价值：从"逐段点音频手动拖到字幕"变成"一次脚本全自动放置"，**省大量人工 + 省 token（agent 只传参数）**。

## 完整工作链路（本次部署验证成功）

```
VoxCPM 生成(十四行诗/lora+参考) → flac
   ↓ ffmpeg 转 wav（conv_wav.py，或 pr_audio_dub.py --convert 自动转）
   ↓ pr_audio_dub.py --dry-run（算 音频vs字幕时长对照表，辅助手动调整）
   ↓ pr_audio_dub.py（清空目标音频轨 → 遍历字幕段 → 按项目库 item 匹配 → insertClip 到字幕起始秒）
   → PR 时间轴 A 轨出现 34 段音频，各在字幕开头
```

## 环境配置（一次性，本机已配好）

| 项 | 位置 | 说明 |
|---|---|---|
| **pymiere venv** | `<你的 pymiere venv 目录>\` | 独立 D 盘 venv（不污染 Hermes），装 `pymiere==1.4.1` |
| **Pymiere Link 扩展** | `<Adobe Premiere Pro 安装目录>\CEP\extensions\com.qmasingarbe.PymiereLink\` | 手动放置（解压 zxp），PR 2026 可加载（窗口→扩展→Pymiere Link） |
| **ffmpeg** | `<你的 ffmpeg.exe 路径>`（或 PATH 中的 `ffmpeg`） | 转 wav 用（Windows 环境，中文路径用 subprocess 传字节） |
| **venv python** | `<你的 pymiere venv>\Scripts\python.exe` | 跑 pr_place_inner 用的解释器 |

> ⚠️ **前置**：PR 必须**正在运行**且能加载 Pymiere Link（不运行则 pymiere 连不上）。pymiere 官方测到 PR 2023，本机 PR 2026 实测兼容（`isDocumentOpen: True`、`insertClip` 正常）。

## 参数（agent 只填这些）

```
python pr_audio_dub.py \
  --csv "字幕.csv"          # 必填，含 Start Time/End Time/Text（帧格式 HH:MM:SS:FF）
  --audio-dir "音频目录"     # 必填，文件名 = 序号_文本.wav/.flac
  --fps 48                  # 序列帧率（字幕 FF→秒换算），默认48
  --track 0                 # 目标音频轨序号，默认0（第一条）
  --clear                   # 放置前清空目标轨（默认追加式）
  --start-seg N --end-seg M # 只放第N~M段（分段调试用）
  --dry-run                 # 只输出时长对照表，不改PR
```

## 关键坑（踩过，务必记住）

1. **中文路径编码**：ffmpeg/ffprobe 在 bash 里传中文文件名会 `Illegal byte sequence`。**必须用 Python subprocess 传 Unicode**（pr_audio_dub.py 的 `audio_durations` 已处理）。wav/flac 文件名带中文，脚本内用 `glob` + `os.path`，别在 shell 直传。
2. **音频时长 > 字幕** → 尾巴盖进下一条字幕（本次主问题）。对策：`--dry-run` 先看对照表，差的段手动缩 in/out 点，或参考 "audio_vs_subtitle_table" 输出。**放置逻辑没问题，是"对齐开头"必然导致长音频溢出**——需手动微调或按字幕时长重新裁剪音频。
3. **`importFiles` 签名**：`project.importFiles([path], suppressUI=False, targetBin=proj.rootItem, importAsNumberedStills=False)`。返回 `bool` 不是 item，所以**拿 item 用 `proj.rootItem.children` 遍历**（按文件名后缀 .wav 匹配），或 `findItemsMatchingMediaPath(path, ignoreSubclips)` 但**须用反斜杠路径**才准。
4. **避免重复导入**：反复 importFiles 同一音频会在项目库堆积重复副本。**最优**：音频已在库时不再导入，直接遍历库匹配 item。
5. **`insertClip(item, time)`**：`time` 用 `time_from_seconds(秒)` 生成。`audioTracks[N].insertClip` 后 clips 计数可能含子项（返回数 ≠ 段数，正常）。
6. **`clip.remove(inRipple, inAlignToVideo)`**：删除剪辑须传 2 参（`False, False`）。
7. **序列帧率**从主视频读（ffprobe `r_frame_rate`）。字幕 `HH:MM:SS:FF` 的 FF 按此 fps 换算。
8. **`Time.getFormatted()`** 缺参数，别用。用 `.seconds`/`.ticks`。

## 验证清单

- [ ] `pr_audio_dub.py --dry-run` 能读到 Pymiere Link + 输出对照表（PR 需运行）
- [ ] 放置后 PR 时间轴 A 轨各段位于字幕起始
- [ ] 长音频段（差分>0）手动微调或耗时重裁
- [ ] 交付前 PR 内预览确认无重叠/错位
