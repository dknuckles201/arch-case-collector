# -*- coding: utf-8 -*-
"""校验 vault 笔记里的 ![[...]] 图片引用是否全部命中，并检查 frontmatter。"""
import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

V = r"U:\DK_iCloud\iCloudDrive\iCloud~md~obsidian\Arch_Vault"
D = os.path.join(V, "06 - 专题研究", "住宅产品研究")

for fn in sorted(os.listdir(D)):
    if not fn.endswith(".md"):
        continue
    p = os.path.join(D, fn)
    t = open(p, encoding="utf-8").read()
    refs = re.findall(r"!\[\[([^\]|#]+?)(?:\|[^\]]*)?\]\]", t)
    miss = []
    for r in refs:
        fp = os.path.join(V, r.replace("/", os.sep))
        if not os.path.exists(fp):
            miss.append(r)
    fm = t.startswith("---")
    print("== %s  字符 %d  frontmatter=%s  引用 %d  缺失 %d" % (fn, len(t), fm, len(refs), len(miss)))
    for m in miss:
        print("    MISS:", m)
    if fm:
        end = t.find("\n---", 3)
        print("    fm keys:", [l.split(":")[0] for l in t[3:end].strip().split("\n") if ":" in l])
