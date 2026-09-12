# -*- coding: utf-8 -*-
# ============ pr_place_inner.py · PR 放置执行器（在 pymiere 环境跑，被 pr_audio_dub 调用） ============
# 由 pr_audio_dub.py 通过 subprocess 调入。只在装了 pymiere 的 venv 下运行。
# 职责：连接运行中的 PR → 取 activeSequence → 清空目标音频轨(可选) → 遍历字幕段，
#       按项目库已有 item（文件名 序号_文本.wav 匹配）→ insertClip 到字幕起始时间。
import argparse, csv, io, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import pymiere
from pymiere.wrappers import time_from_seconds


def tc_to_sec(tc, fps):
    parts = tc.replace(';', ':').split(':')
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2]) + ((int(parts[3]) / fps) if len(parts) > 3 else 0)


def main():
    import pymiere
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--audio-dir", required=True)
    p.add_argument("--fps", type=int, default=48)
    p.add_argument("--track", type=int, default=0)
    p.add_argument("--clear", action="store_true")
    p.add_argument("--segments", default="[]", help="字幕段 JSON（含 idx/start/end/text）")
    p.add_argument("--start-seg", type=int, default=None)
    p.add_argument("--end-seg", type=int, default=None)
    args = p.parse_args()

    segs = json.loads(args.segments)
    proj = pymiere.objects.app.project
    seq = proj.activeSequence
    at = seq.audioTracks[args.track]

    # 可选：清空目标轨
    if args.clear:
        while len(at.clips) > 0:
            try:
                at.clips[0].remove(False, False)
            except Exception as e:
                print("删clip失败:", e)
                break

    # 收集项目库 wav item（不重复导入，用现有）
    wav_items = {}
    def walk(c):
        try:
            for it in c:
                n = getattr(it, 'name', '')
                if n.lower().endswith('.wav') and n not in wav_items:
                    wav_items[n] = it
                if hasattr(it, 'children') and it.children:
                    walk(it.children)
        except Exception:
            pass
    walk(proj.rootItem.children)

    idx_item = {}
    for n, it in wav_items.items():
        m = re.match(r'^(\d+)_', n)
        if m:
            idx_item[int(m.group(1))] = it

    ok, skip = 0, 0
    for s in segs:
        idx = s["idx"]
        if args.start_seg is not None and idx < args.start_seg:
            continue
        if args.end_seg is not None and idx > args.end_seg:
            continue
        item = idx_item.get(idx)
        if not item:
            skip += 1
            print("SKIP %d (无item)" % idx, flush=True)
            continue
        t = time_from_seconds(s["start"])
        try:
            at.insertClip(item, t)
            ok += 1
            print("OK %d @%.3fs" % (idx, s["start"]), flush=True)
        except Exception as e:
            skip += 1
            print("FAIL %d: %s" % (idx, e), flush=True)

    res = {"placed": ok, "skipped": skip, "track_clips": len(at.clips)}
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
