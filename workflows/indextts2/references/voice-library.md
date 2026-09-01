# 角色库速查（F:\Comfy-Desktop\ComfyUI-Shared\models\voices\）

> 更新日期：2026-08-09。新增角色后在此追加。

## 当前角色（4 个）

| 角色名（标签用） | 音频文件 | 参考文本（.txt） | 备注 |
|---|---|---|---|
| 守岸人 | 守岸人.wav | 守岸人，这个称呼就很好，它表示，某种因你而有的意义与决心。 | 鸣潮，11.1s |
| 十四行诗 | 十四行诗.mp3 | know the moon, and this is an alien city. | 重返未来1999，3.7s（偏短） |
| 库珀花环 | 库珀花环.mp3 | Mr. Kozlov would always paint my face before each show. ... | 重返未来1999，20.8s（偏长） |
| 铅玻璃 | 铅玻璃.mp3 | The doctor says that as long as I work hard, my disease will be cured. ... | 重返未来1999，22.9s（偏长） |

## 使用规则

- 文本里 `[角色名]` 必须与上表"角色名"完全一致（中文）
- narrator 已设 none → 必须带角色标签
- `[角色:情感参考]` 的情感参考可用 voices_examples/ 里的示例音频名（如 crestfallen_original）

## 新增角色流程

1. 音频 5-15s（.wav/.mp3/.flac/.ogg/.m4a/.aac），>15s 建议裁剪
2. `cp 源音频 <ComfyUI模型路径>/models/voices/角色名.扩展名`
3. `echo "纯参考文本" > <ComfyUI模型路径>/models/voices/角色名.txt`
4. ComfyUI 刷新角色缓存（Refresh Voice Cache 节点）或重启
5. 更新本速查表
