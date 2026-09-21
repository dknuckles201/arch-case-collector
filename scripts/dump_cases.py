# -*- coding: utf-8 -*-
"""把 make_list.py 里的案例数据 + 磁盘图片实况导出为 raw/cases_dump.json（供资料库建表用）"""
import os, json

BASE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(BASE, "make_list.py"), encoding="utf-8").read().splitlines()
end = None
for i, l in enumerate(src):
    if i > 5 and l.strip() == "]":
        end = i
        break
ns = {"__file__": os.path.join(BASE, "make_list.py")}
exec("\n".join(src[: end + 1]), ns)
P = ns["P"]
print("n =", len(P))


def buckets(key):
    d = os.path.join(BASE, "img", key)
    files = sorted(os.listdir(d)) if os.path.isdir(d) else []
    ht = [f for f in files if "HT" in f]
    zz = [f for f in files if "ZZ" in f]
    po = [f for f in files if "POSTER" in f]
    alb = [f for f in files if f not in ht and f not in zz and f not in po]
    return ht, zz, po, alb


out = []
for p in P:
    ht, zz, po, alb = buckets(p["key"])
    score = round(p["cred"] * 0.35 + p["rel"] * 0.30 + p["comp"] * 0.25 + p["fresh"] * 0.10, 1)
    status = "建议收录" if (score >= 70 and len(ht) >= 1) else "待补图候选"
    out.append(dict(
        key=p["key"], name=p["name"], city=p["city"], arch=p["arch"], year=p["year"],
        loc=p["loc"], area=p["area"], feat=p["feat"], score=score, status=status,
        ht=len(ht), zz=len(zz), po=len(po), alb=len(alb),
        srcs=p["srcs"], note=p["note"],
    ))
    print("%-14s %-26s score=%5.1f %-8s HT=%2d ZZ=%d PO=%d ALB=%d"
          % (p["key"], p["name"], score, status, len(ht), len(zz), len(po), len(alb)))

os.makedirs(os.path.join(BASE, "raw"), exist_ok=True)
json.dump(out, open(os.path.join(BASE, "raw", "cases_dump.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("saved raw/cases_dump.json")
print("TOTAL HT", sum(o["ht"] for o in out), "| ZZ", sum(o["zz"] for o in out))
