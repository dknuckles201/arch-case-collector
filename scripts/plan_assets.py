# -*- coding: utf-8 -*-
"""为 vault 归档准备素材：按项目生成带编号的审图板 + 输出归档计划 raw/asset_plan.json"""
import os, json
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "img")
OUT = os.path.join(BASE, "_audit")
os.makedirs(OUT, exist_ok=True)

# 项目展示名（用于 vault 路径）——按分数降序
PROJ = [
    ("03-huguang",   "保利湖光悦色"),
    ("06-nantian",   "南天名苑"),
    ("08-yuxi",      "御溪臻山墅"),
    ("05-zhenyuan",  "绿城臻园"),
    ("09-huacheng1", "城投花城壹号院"),
    ("01-puyueshu",  "金茂越秀璞樾墅"),
    ("11-fengming",  "南沙凤鸣山"),
    ("02-guanyue",   "观樾天湖"),
    ("10-xinyuan",   "中海熙园"),
    ("07-lingnan1",  "岭南1号"),
]
CLS = {"HT": "HT", "ZZ": "ZZ", "POSTER": "POSTER"}


def cls_of(f):
    for c in ("POSTER", "ZZ", "HT"):
        if c in f:
            return c
    return "ALB"


items = []          # 全局序号 → 元数据
for key, name in PROJ:
    d = os.path.join(IMG, key)
    if not os.path.isdir(d):
        continue
    fs = sorted(os.listdir(d))
    core = [f for f in fs if cls_of(f) in ("HT", "ZZ", "POSTER")]
    # 排序：HT → ZZ → POSTER，组内按原文件名
    order = {"HT": 0, "ZZ": 1, "POSTER": 2}
    core.sort(key=lambda f: (order[cls_of(f)], f))
    for f in core:
        items.append({"key": key, "proj": name, "src": f, "cls": cls_of(f)})

for i, it in enumerate(items, 1):
    it["no"] = i

json.dump(items, open(os.path.join(BASE, "raw", "asset_plan_raw.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---- 生成审图板：3x3，格 560px ----
CELL, COLS, ROWS = 560, 3, 3
PER = COLS * ROWS
sheets = []
for s in range(0, len(items), PER):
    chunk = items[s:s + PER]
    W, H = CELL * COLS, CELL * ROWS
    sheet = Image.new("RGB", (W, H), (24, 26, 30))
    dr = ImageDraw.Draw(sheet)
    for j, it in enumerate(chunk):
        cx, cy = (j % COLS) * CELL, (j // COLS) * CELL
        try:
            im = Image.open(os.path.join(IMG, it["key"], it["src"])).convert("RGB")
        except Exception as e:
            dr.text((cx + 8, cy + 8), "ERR %s" % e, fill=(255, 90, 90))
            continue
        im.thumbnail((CELL - 16, CELL - 44))
        sheet.paste(im, (cx + (CELL - im.width) // 2, cy + 38 + (CELL - 44 - im.height) // 2))
        dr.rectangle([cx + 2, cy + 2, cx + CELL - 2, cy + 36], fill=(12, 14, 18))
        dr.text((cx + 8, cy + 8), "[%02d] %s" % (it["no"], it["proj"]), fill=(255, 214, 102))
        dr.text((cx + 8, cy + 21), it["src"][:52], fill=(190, 198, 210))
        dr.rectangle([cx + 1, cy + 1, cx + CELL - 2, cy + CELL - 2], outline=(70, 76, 86))
    p = os.path.join(OUT, "core_%02d.png" % (s // PER + 1))
    sheet.save(p)
    sheets.append((p, len(chunk)))

print("核心素材 %d 张，审图板 %d 张：" % (len(items), len(sheets)))
for p, n in sheets:
    print("   %s  (%d 格)" % (os.path.basename(p), n))
print()
for it in items:
    print("  [%02d] %-16s %-10s %s" % (it["no"], it["proj"], it["cls"], it["src"]))
