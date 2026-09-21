#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用审图板：把某目录下所有图片拼成 N 板（每板 3x3，带编号），供逐张视觉核验。

用法:
  python sheet_any.py <目录> <输出前缀> [列数]
例:
  python sheet_any.py img/_wx_probe _audit/wx_puyueshu 3
"""
import os
import sys

from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    d = os.path.join(BASE, sys.argv[1])
    prefix = sys.argv[2]
    cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    files = sorted(f for f in os.listdir(d)
                   if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")))
    if not files:
        print("无图片"); return 1
    cell_w, cell_h = 640, 520
    per = cols * 3
    os.makedirs(os.path.dirname(os.path.join(BASE, prefix)) or ".", exist_ok=True)
    sheets = 0
    for si in range(0, len(files), per):
        chunk = files[si:si + per]
        rows = (len(chunk) + cols - 1) // cols
        W, H = cols * cell_w, rows * cell_h + 30
        sheet = Image.new("RGB", (W, H), (248, 248, 248))
        dr = ImageDraw.Draw(sheet)
        dr.text((8, 8), "%s  (%d-%d / %d)" % (prefix, si + 1, si + len(chunk), len(files)), fill=(20, 20, 20))
        for k, fn in enumerate(chunk):
            r, c = divmod(k, cols)
            try:
                im = Image.open(os.path.join(d, fn)).convert("RGB")
            except Exception as e:
                print("  skip", fn, e); continue
            im.thumbnail((cell_w - 16, cell_h - 40))
            x = c * cell_w + (cell_w - im.width) // 2
            y = 30 + r * cell_h + 22
            sheet.paste(im, (x, y))
            dr.rectangle([c * cell_w + 4, 30 + r * cell_h + 4, (c + 1) * cell_w - 4, 30 + (r + 1) * cell_h - 4],
                         outline=(200, 200, 200))
            dr.text((c * cell_w + 12, 30 + r * cell_h + 8), "[%02d] %s  %dx%d" % (si + k + 1, fn, im.width, im.height),
                    fill=(180, 30, 30))
        out = os.path.join(BASE, "%s%d.png" % (prefix, si // per + 1))
        sheet.save(out)
        print("  板 ->", os.path.relpath(out, BASE), sheet.size)
        sheets += 1
    print("共 %d 板 / %d 张" % (sheets, len(files)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
