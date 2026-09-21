#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从 raw/cur_article.json（bsk evaluate 抓下的文章快照）下载正文图。

用法:
  python wx_from_article.py raw/cur_article.json img/01-puyueshu WX

会在目标目录写 WX01.jpg...，并输出 wx_dl_log.json 记录。
"""
import json
import os
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")


def fetch(url, referer="https://mp.weixin.qq.com/", timeout=40):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Referer": referer,
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def dims(b):
    try:
        if b[:8] == b"\x89PNG\r\n\x1a\n":
            import struct
            return struct.unpack(">II", b[16:24])
        if b[:2] == b"\xff\xd8":
            i = 2
            while i < len(b) - 9:
                if b[i] != 0xFF:
                    i += 1
                    continue
                m = b[i + 1]
                if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    return (int.from_bytes(b[i + 7:i + 9], "big"), int.from_bytes(b[i + 5:i + 7], "big"))
                i += 2 + int.from_bytes(b[i + 2:i + 4], "big")
    except Exception:
        pass
    return (None, None)


def main():
    snap, outrel, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    t = open(os.path.join(BASE, snap), encoding="utf-8", errors="replace").read()
    d = json.loads(t[t.find("{"):t.rfind("}") + 1])
    out = os.path.join(BASE, outrel)
    os.makedirs(out, exist_ok=True)
    imgs = d.get("imgs", [])
    log, ok = [], 0
    for i, u in enumerate(imgs, 1):
        name = "%s%02d.jpg" % (prefix, i)
        dst = os.path.join(out, name)
        rec = {"i": i, "name": name, "url": u.split("#")[0][:130], "src": "wx:" + d.get("t", "")[:40]}
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            rec["status"] = "exists"
            log.append(rec)
            continue
        cands = [u.replace("/640?", "/0?"), u.split("#")[0]]
        for cu in cands:
            try:
                st, data = fetch(cu)
            except Exception as e:
                rec.setdefault("errs", []).append("%s :: %s" % (cu[:60], str(e)[:70]))
                continue
            if st == 200 and data and len(data) > 1500:
                w, h = dims(data)
                tmp = dst + ".tmp"
                open(tmp, "wb").write(data)
                os.replace(tmp, dst)
                rec.update(status=200, bytes=len(data), px="%sx%s" % (w, h))
                ok += 1
                print("  [%02d] OK  %-9s %8dB  %sx%s" % (i, name, len(data), w, h))
                break
        else:
            rec["status"] = "fail"
            print("  [%02d] FAIL %s" % (i, name))
        log.append(rec)
        time.sleep(0.2)
    lp = os.path.join(BASE, "raw", "wx_dl_log.json")
    old = []
    if os.path.exists(lp):
        try:
            old = json.load(open(lp, encoding="utf-8"))
        except Exception:
            old = []
    old.append({"source": d.get("t", "")[:60], "account": d.get("acc", ""), "date": d.get("date", ""),
                "url": d.get("url", "")[:200], "out": outrel, "ok": ok, "n": len(imgs), "items": log})
    json.dump(old, open(lp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n下载 %d/%d -> %s" % (ok, len(imgs), outrel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
