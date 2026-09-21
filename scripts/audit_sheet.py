# -*- coding: utf-8 -*-
"""审图板生成器：把各项目目录里的图片拼成带编号的拼板，供视觉核验图片真实内容。
用法:
  python audit_sheet.py            # 全部图片
  python audit_sheet.py HT         # 仅文件名含 HT 的
  python audit_sheet.py ALB        # 仅文件名含 ALB 的（复核有无漏判的户型图）
输出: _audit/sheet_<目录>_<序号>.png
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "img")
OUT = os.path.join(BASE, "_audit")
os.makedirs(OUT, exist_ok=True)

CELL = 420
COLS = 3
PAD = 8
LBL = 30
PER = 9

try:
    FONT = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 17)
    FONT_S = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 15)
except Exception:
    FONT = FONT_S = ImageFont.load_default()


def sheet(paths, out_path, title=""):
    rows = (len(paths) + COLS - 1) // COLS
    W = COLS * (CELL + PAD) + PAD
    H = rows * (CELL + LBL + PAD) + PAD + (34 if title else 0)
    canvas = Image.new("RGB", (W, H), (250, 250, 250))
    d = ImageDraw.Draw(canvas)
    y0 = PAD
    if title:
        d.text((PAD, PAD), title, fill=(20, 20, 20), font=FONT)
        y0 += 34
    for i, p in enumerate(paths):
        r, c = divmod(i, COLS)
        x = PAD + c * (CELL + PAD)
        y = y0 + r * (CELL + LBL + PAD)
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((CELL, CELL))
            bg = Image.new("RGB", (CELL, CELL), (255, 255, 255))
            bg.paste(im, ((CELL - im.width) // 2, (CELL - im.height) // 2))
            canvas.paste(bg, (x, y))
        except Exception as e:
            d.rectangle([x, y, x + CELL, y + CELL], fill=(240, 230, 230))
            d.text((x + 6, y + 6), "ERR " + str(e)[:40], fill=(150, 0, 0), font=FONT)
        d.rectangle([x, y + CELL, x + CELL, y + CELL + LBL], fill=(30, 30, 30))
        nm = os.path.basename(p)
        nm = nm if len(nm) <= 28 else nm[:12] + "…" + nm[-13:]
        d.text((x + 5, y + CELL + 6), "[%02d] %s" % (i + 1, nm), fill=(255, 235, 120), font=FONT_S)
    canvas.save(out_path)
    return out_path, canvas.size


def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else "ALL").upper()
    made = []
    for dd in sorted(os.listdir(IMG)):
        p = os.path.join(IMG, dd)
        if not os.path.isdir(p):
            continue
        fs = sorted(os.listdir(p))
        if mode == "HT":
            fs = [f for f in fs if "HT" in f]
        elif mode == "ALB":
            fs = [f for f in fs if "ALB" in f]
        if not fs:
            continue
        for k in range(0, len(fs), PER):
            chunk = [os.path.join(p, f) for f in fs[k:k + PER]]
            out = os.path.join(OUT, "sheet_%s_%s%d.png" % (dd, mode, k // PER + 1))
            t = "%s [%s]  (%d/%d)" % (dd, mode, k // PER + 1, (len(fs) + PER - 1) // PER)
            r = sheet(chunk, out, t)
            made.append(r)
            print("  %-14s n=%-2d -> %s %s" % (dd, len(chunk), os.path.basename(out), r[1]))
    print("\n合计 %d 张审图板，输出: %s" % (len(made), OUT))


if __name__ == "__main__":
    main()
