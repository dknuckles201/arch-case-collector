# -*- coding: utf-8 -*-
"""校验 候选清单.html 中的图片引用是否都能在 img/ 下找到"""
import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

B = os.path.dirname(os.path.abspath(__file__))
html = open(os.path.join(B, "候选清单.html"), encoding="utf-8").read()

refs = re.findall(r'(?:src|href)="(img/[^"]+)"', html)
uniq = sorted(set(refs))
missing = []
for r in uniq:
    fp = os.path.join(B, r.replace("/", os.sep))
    if not os.path.exists(fp):
        missing.append(r)

print("引用总数(去重) =", len(uniq), " 缺失 =", len(missing))
for m in missing:
    print("  MISSING:", m)

# 逐盘列出目录下未被引用的文件
print("\n--- 未被 HTML 引用的文件（提示用） ---")
for k in sorted(os.listdir(os.path.join(B, "img"))):
    d = os.path.join(B, "img", k)
    if not os.path.isdir(d):
        continue
    used = {os.path.basename(r) for r in uniq if r.startswith("img/" + k + "/")}
    unused = [f for f in sorted(os.listdir(d)) if f not in used]
    if unused:
        print(f"[{k}] 共 {len(os.listdir(d))} 张，未引用 {len(unused)} 张")
        for u in unused:
            print("    -", u)
