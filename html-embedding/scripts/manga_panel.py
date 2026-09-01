# -*- coding: utf-8 -*-
"""多格漫画拼版合成：3列xN行网格 + 对白嵌字 + 标题署名（2026-08 验证）
用法: python manga_panel.py <图目录> <输出路径>
图目录内须有 p01.png, p02.png ...（按格序）；DIALOG 按格序一一对应。
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont

SRC_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = sys.argv[2] if len(sys.argv) > 2 else "manga_panel.png"

FONT = r"C:/Windows/Fonts/msyh.ttc"          # 微软雅黑（只读）
FONT_BOLD = r"C:/Windows/Fonts/msyhbd.ttc"

DIALOG = [
    "「对白1」", "「对白2」", "「对白3」", "「对白4」", "「对白5」",
    "「对白6」", "「对白7」", "「对白8」", "「对白9」", "「对白10」",
    "「对白11」", "「对白12」", "「对白13」", "「对白14」", "「对白15」",
]

# 布局参数（15 格 = 3 列 x 5 行；改格数时调 ROWS）
THUMB_W, THUMB_H = 1024, 677          # 每格显示尺寸（1536x1016 缩 2/3）
COLS, ROWS = 3, 5
GAP = 36
MARGIN = 50
HEAD_H = 150
FOOT_H = 90
BAR_H = 56
BAR_A = (0, 0, 0, 200)

N = len(DIALOG)
W = MARGIN*2 + THUMB_W*COLS + GAP*(COLS-1)
H = MARGIN + HEAD_H + THUMB_H*((N+COLS-1)//COLS) + GAP*(((N+COLS-1)//COLS)-1) + FOOT_H + MARGIN

canvas = Image.new("RGBA", (W, H), (17, 15, 22, 255))
draw = ImageDraw.Draw(canvas)

f_head = ImageFont.truetype(FONT_BOLD, 46)
f_sub  = ImageFont.truetype(FONT, 20)
f_bar  = ImageFont.truetype(FONT, 21)
f_foot = ImageFont.truetype(FONT, 16)

title = "放学后の办公室 · 十五连"
sub   = "—— 副标题 ——  R-18 ｜ 全 %d 格" % N
tw = draw.textlength(title, font=f_head)
draw.text(((W-tw)/2, MARGIN+20), title, font=f_head, fill=(232, 184, 75, 255))
sw = draw.textlength(sub, font=f_sub)
draw.text(((W-sw)/2, MARGIN+92), sub, font=f_sub, fill=(154, 154, 168, 255))

for i in range(N):
    row, col = i // COLS, i % COLS
    x = MARGIN + col*(THUMB_W+GAP)
    y = MARGIN + HEAD_H + row*(THUMB_H+GAP)
    p = os.path.join(SRC_DIR, "p%02d.png" % (i+1))
    img = Image.open(p).convert("RGB").resize((THUMB_W, THUMB_H), Image.LANCZOS)
    draw.rectangle([x-3, y-3, x+THUMB_W+2, y+THUMB_H+2], outline=(232, 184, 75, 255), width=2)
    canvas.paste(img, (x, y))
    draw.rectangle([x, y+THUMB_H-BAR_H, x+THUMB_W, y+THUMB_H], fill=BAR_A)
    draw.text((x+16, y+THUMB_H-BAR_H+12), DIALOG[i], font=f_bar, fill=(255, 233, 217, 255))

foot = "制作人：作者 · 出品　｜　仅限成人读者"
fw = draw.textlength(foot, font=f_foot)
draw.text(((W-fw)/2, H-MARGIN-FOOT_H//2-10), foot, font=f_foot, fill=(122, 90, 118, 255))

canvas.convert("RGB").save(OUT, quality=92)
print("OK:", OUT, canvas.size, os.path.getsize(OUT)//1024, "KB")
