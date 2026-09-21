# -*- coding: utf-8 -*-
"""为指定图片清单生成带编号的审图板（3 列 × 3 行/板），用于逐板目视核验图面内容。
用法：python board_new.py <清单文件名> <输出前缀>
清单文件：每行 `项目key/文件名`
"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "img")
OUT = os.path.join(BASE, "raw", "boards")
os.makedirs(OUT, exist_ok=True)

listfile = os.path.join(BASE, "raw", "new_files.txt")
prefix = "NEW"

items = []
for ln in open(listfile, encoding="utf-8"):
    ln = ln.strip()
    if not ln or ln.startswith("#"):
        continue
    key, fn = ln.split("/", 1)
    items.append((key, fn))

try:
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 26)
except Exception:
    font = ImageFont.load_default()

COLS, ROWS = 3, 3
CELL = 620
PAD = 34
LAB = 46

per = COLS * ROWS
boards = []
for b in range(0, len(items), per):
    chunk = items[b:b + per]
    W = COLS * CELL + PAD * (COLS + 1)
    H = ROWS * (CELL + LAB) + PAD * (ROWS + 1)
    canvas = Image.new("RGB", (W, H), (245, 245, 245))
    dr = ImageDraw.Draw(canvas)
    for i, (key, fn) in enumerate(chunk):
        idx = b + i
        r, c = divmod(i, COLS)
        x = PAD + c * (CELL + PAD)
        y = PAD + r * (CELL + LAB + PAD)
        dr.rectangle([x, y, x + CELL, y + LAB + CELL], outline=(120, 120, 120))
        dr.text((x + 6, y + 8), "[%d] %s" % (idx, fn[:44]), fill=(10, 10, 10), font=font)
        fp = os.path.join(IMG, key, fn)
        try:
            im = Image.open(fp).convert("RGB")
            im.thumbnail((CELL - 10, CELL - 10))
            canvas.paste(im, (x + (CELL - im.width) // 2, y + LAB + (CELL - im.height) // 2))
        except Exception as e:
            dr.text((x + 6, y + LAB + 40), "ERR %s" % e, fill=(200, 0, 0), font=font)
    boards.append(canvas)

for i, bd in enumerate(boards):
    p = os.path.join(OUT, "%s_board%d.jpg" % (prefix, i + 1))
    bd.save(p, quality=86)
    print("board ->", p)

print("\n索引清单：")
for i, (key, fn) in enumerate(items):
    print("%3d  %-14s %s" % (i, key, fn))
