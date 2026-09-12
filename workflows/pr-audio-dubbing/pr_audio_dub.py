# -*- coding: utf-8 -*-
# ============ pr_audio_dub.py · PR 自动配音引子（黑盒，agent 只传参数） ============
# 将 VoxCPM 已生成的音频（flac→wav）自动导入 PR，并对齐到字幕 CSV 起始时间。
# 依赖：pymiere（已装到独立 venv）、正在运行的 PR + Pymiere Link 扩展。
#
# 用法：
#   python pr_audio_dub.py --csv "字幕.csv" --audio-dir "音频目录" [--fps 48]
#        [--track 0] [--clear] [--start-seg N --end-seg M] [--dry-run]
#   --dry-run       只输出 "音频 vs 字幕时长对照表"（辅助手动调整），不改 PR
#   --clear         放置前清空目标音频轨（默认不清，追加式）
#
# 输出：一行 JSON {"placed": N, "skipped": M, "track_clips": K}
#
# 前置条件（本机一次性配置，见 guide.md）：
#   pip 在独立 venv（如 <你的 venv>/Scripts/python.exe），用环境变量 PYMIERE_PY 指定
#   PR 需运行，Pymiere Link 扩展需可在 窗口→扩展 加载

import argparse, csv, io, json, os, re, sys, glob, subprocess

PYMIERE_PY = None  # 运行时通过 --pymiere-py 指定，或自动探测

def find_pymiere_py():
    """定位装了 pymiere 的 python。优先 --pymiere-py，其次环境变量 PYMIERE_PY，最后用当前解释器。"""
    cands = [c for c in [os.environ.get("PYMIERE_PY")] if c]
    for c in cands:
        if os.path.exists(c):
            return c
    return sys.executable


def tc_to_sec(tc, fps):
    parts = tc.replace(';', ':').split(':')
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2]) + ((int(parts[3]) / fps) if len(parts) > 3 else 0)


def read_csv(csv_path, fps):
    raw = open(csv_path, 'rb').read()
    for enc in ['utf-8-sig', 'utf-8', 'gbk']:
        try:
            t = raw.decode(enc)
            break
        except Exception:
            continue
    rows = list(csv.reader(io.StringIO(t)))
    segs = []
    for i, r in enumerate(rows[1:], 1):
        if len(r) >= 3 and r[0].strip():
            segs.append({"idx": i, "start": round(tc_to_sec(r[0].strip(), fps), 3),
                         "end": round(tc_to_sec(r[1].strip(), fps), 3), "text": r[2].strip()})
    return segs


def audio_durations(audio_dir):
    """用声学库或 ffprobe 读每个音频时长。优先本进程已有 soundfile，否则 subprocess ffprobe。"""
    durs = {}
    try:
        import soundfile as sf
        for f in glob.glob(os.path.join(audio_dir, "*.wav")) + glob.glob(os.path.join(audio_dir, "*.flac")):
            try:
                idx = int(os.path.basename(f).split("_")[0])
                durs[idx] = round(sf.info(f).duration, 2)
            except Exception:
                pass
        return durs
    except ImportError:
        pass
    # 回退：ffprobe（中文路径用 subprocess 字节，避免 bash 编码问题）
    ffprobe = os.environ.get("FFPROBE", "ffprobe")   # 已在 PATH 则保持默认
    for f in glob.glob(os.path.join(audio_dir, "*.wav")) + glob.glob(os.path.join(audio_dir, "*.flac")):
        try:
            idx = int(os.path.basename(f).split("_")[0])
            r = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=noprint_wrappers=1:nokey=1", f],
                               capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                durs[idx] = round(float(r.stdout.strip()), 2)
        except Exception:
            pass
    return durs


def convert_flac_to_wav(audio_dir, ffmpeg=None):
    """把音频目录里所有 .flac 转成 .wav（PR 对 wav 支持最稳）。中文路径用 subprocess 传字节。"""
    if ffmpeg is None:
        ffmpeg = os.environ.get("FFMPEG", "ffmpeg")      # 已在 PATH 则保持默认
    files = glob.glob(os.path.join(audio_dir, "*.flac"))
    ok = 0
    for f in files:
        base = os.path.basename(f)
        wav = os.path.join(audio_dir, base[:-5] + ".wav")
        if os.path.exists(wav):
            ok += 1
            continue
        r = subprocess.run([ffmpeg, "-y", "-i", f, wav], capture_output=True, text=True)
        if r.returncode == 0:
            ok += 1
        else:
            print("转换失败:", base, r.stderr[-200:], file=sys.stderr)
    print("flac→wav 转换完成 %d/%d" % (ok, len(files)))
    return ok


def do_place(csv_path, audio_dir, fps, track, clear, start_seg, end_seg, segments):
    """在 PR 内执行放置（须在 pymiere 环境，通过 subprocess 调 pr_place_inner）。"""
    inner = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pr_place_inner.py")
    py = find_pymiere_py()
    cmd = [py, inner, "--csv", csv_path, "--audio-dir", audio_dir, "--fps", str(fps),
           "--track", str(track), "--segments", json.dumps(segments)]
    if clear:
        cmd.append("--clear")
    if start_seg is not None:
        cmd += ["--start-seg", str(start_seg)]
    if end_seg is not None:
        cmd += ["--end-seg", str(end_seg)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit("放置失败: " + r.stderr[-800:])
    return r.stdout.strip()


def main():
    p = argparse.ArgumentParser(description="PR 自动配音：音频对齐字幕（黑盒引子）")
    p.add_argument("--csv", required=True, help="字幕 CSV（含 Start Time/End Time/Text）")
    p.add_argument("--audio-dir", required=True, help="音频目录（文件名 序号_文本.wav/.flac）")
    p.add_argument("--fps", type=int, default=48, help="序列帧率（字幕 FF 换算用，默认48）")
    p.add_argument("--track", type=int, default=0, help="目标音频轨序号（默认0=第一条）")
    p.add_argument("--clear", action="store_true", help="放置前清空目标音频轨")
    p.add_argument("--start-seg", type=int, default=None, help="只放置从第N段起")
    p.add_argument("--end-seg", type=int, default=None, help="只放置到第M段止")
    p.add_argument("--dry-run", action="store_true", help="只输出时长对照表，不改PR")
    p.add_argument("--pymiere-py", default=None, help="pymiere 的 python 路径（默认自动探测）")
    p.add_argument("--convert", action="store_true", help="放置前先把 *.flac 转成 *.wav")
    args = p.parse_args()

    segs = read_csv(args.csv, args.fps)
    if not segs:
        raise SystemExit("没读到字幕段")

    durs = audio_durations(args.audio_dir)

    # 时长对照表（无论 dry-run 与否都打印，辅助手动调整）
    print("=== 音频 vs 字幕时长对照 ===")
    print("段 | 字幕起 | 字幕长 | 音频长 | 差(音-字) | 需处理")
    for s in segs:
        sub_dur = round(s["end"] - s["start"], 2)
        aud_dur = durs.get(s["idx"], 0)
        diff = round(aud_dur - sub_dur, 2)
        mark = "⚠️缩短" if diff > 0.1 else ""
        print("%2d | %.2fs | %.2f | %.2f | %+5.2f | %s" % (s["idx"], s["start"], sub_dur, aud_dur, diff, mark))

    if args.dry_run:
        print("\nDRY-RUN：未改动 PR。去掉 --dry-run 执行放置。")
        return

    if args.convert:
        convert_flac_to_wav(args.audio_dir)

    out = do_place(args.csv, args.audio_dir, args.fps, args.track, args.clear,
                   args.start_seg, args.end_seg, segs)
    print(out)


if __name__ == "__main__":
    main()
