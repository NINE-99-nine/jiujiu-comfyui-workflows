# -*- coding: utf-8 -*-
# 把 34 段 flac 转成 wav（PR 对 wav 支持最稳），中文路径用 subprocess 传字节
import subprocess, glob, os

SRC = os.environ.get("PR_AUDIO_SRC", r"./临时文件")   # PR 导出的配音文件目录（*.flac）
DST = os.environ.get("PR_AUDIO_TMP", r"./temp_wav")   # 转出的 wav 输出目录
os.makedirs(DST, exist_ok=True)

files = glob.glob(os.path.join(SRC, "*.flac"))
def num_key(p):
    try: return int(os.path.basename(p).split("_")[0])
    except: return 9999
files.sort(key=num_key)

ffmpeg = os.environ.get("FFMPEG", "ffmpeg")           # ffmpeg 可执行文件；已在 PATH 则保持默认

ok = 0
for f in files:
    base = os.path.basename(f)
    wav = os.path.join(DST, base[:-5] + ".wav")
    if os.path.exists(wav):
        ok += 1
        continue
    r = subprocess.run([ffmpeg, "-y", "-i", f, wav], capture_output=True, text=True)
    if r.returncode == 0:
        ok += 1
    else:
        print("FAIL:", base, r.stderr[-200:])
print("转换完成", ok, "/", len(files))
