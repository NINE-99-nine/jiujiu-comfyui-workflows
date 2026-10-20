# -*- coding: utf-8 -*-
# 把 34 段 flac 转成 wav（PR 对 wav 支持最稳），中文路径用 subprocess 传字节
import subprocess, glob, os

SRC = r"<voice_dir>/PR视频的配音内容/临时文件"
DST = r"<voice_dir>/PR视频的配音内容/temp_wav"
os.makedirs(DST, exist_ok=True)

files = glob.glob(os.path.join(SRC, "*.flac"))
def num_key(p):
    try: return int(os.path.basename(p).split("_")[0])
    except: return 9999
files.sort(key=num_key)

ffmpeg = r"<home>/AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe"

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
