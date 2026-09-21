#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微信文章图片下载器（mmbiz.qpic.cn 非签名 CDN，可直下）

用法:
  python wx_dl.py raw/wx_batch_xxx.json

json 结构:
{
  "out": "img/01-puyueshu",
  "prefix": "WX",
  "referer": "https://mp.weixin.qq.com/",
  "items": [ {"url": "https://mmbiz.qpic.cn/...", "note": "文章标题/第N张"} ]
}

行为:
  * 依次尝试 原图(/0) -> 页面给的尺寸(/640) -> 原始URL
  * 文件名 <prefix><序号>.jpg（序号从 01 起，保持文章内顺序）
  * 记录 raw/wx_dl_log.json：每张的最终URL/HTTP状态/字节数/像素
"""
import json
import os
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")


def fetch(url, referer, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Referer": referer or "https://mp.weixin.qq.com/",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def candidates(u):
    """生成候选 URL：优先原图 /0，其次页面尺寸，最后原样"""
    out = []
    if "/640?" in u:
        out.append(u.replace("/640?", "/0?"))
    if "/640?" in u:
        out.append(u.split("#")[0])
    out.append(u.split("#")[0])
    seen, res = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            res.append(x)
    return res


def size_of(b):
    """从字节流头部读 PNG/JPEG 尺寸"""
    try:
        if b[:8] == b"\x89PNG\r\n\x1a\n":
            import struct
            w, h = struct.unpack(">II", b[16:24])
            return w, h
        if b[:2] == b"\xff\xd8":
            i = 2
            while i < len(b) - 9:
                if b[i] != 0xFF:
                    i += 1
                    continue
                m = b[i + 1]
                if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h = int.from_bytes(b[i + 5:i + 7], "big")
                    w = int.from_bytes(b[i + 7:i + 9], "big")
                    return w, h
                seg = int.from_bytes(b[i + 2:i + 4], "big")
                i += 2 + seg
    except Exception:
        pass
    return None, None


def main():
    cfgp = sys.argv[1]
    cfg = json.load(open(cfgp, encoding="utf-8"))
    out = os.path.join(BASE, cfg["out"])
    os.makedirs(out, exist_ok=True)
    prefix = cfg.get("prefix", "WX")
    referer = cfg.get("referer", "https://mp.weixin.qq.com/")
    log = []
    ok = 0
    for i, it in enumerate(cfg["items"], 1):
        u = it["url"]
        name = "%s%02d.jpg" % (prefix, i)
        dst = os.path.join(out, name)
        rec = {"i": i, "name": name, "note": it.get("note", ""), "url": u}
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            rec["status"] = "exists"
            log.append(rec)
            print("  [%02d] EXISTS %s" % (i, name))
            continue
        got = False
        for cu in candidates(u):
            try:
                st, data = fetch(cu, referer)
            except Exception as e:
                rec.setdefault("errs", []).append("%s -> %s" % (cu[:70], type(e).__name__ + ":" + str(e)[:60]))
                continue
            if st == 200 and data and len(data) > 1500:
                w, h = size_of(data)
                tmp = dst + ".tmp"
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, dst)
                rec.update(status=200, bytes=len(data), px="%sx%s" % (w, h), final=cu[:110])
                got = True
                ok += 1
                print("  [%02d] OK %-10s %8d B  %s  %s" % (i, name, len(data), "%sx%s" % (w, h), cu[:60]))
                break
            rec.setdefault("errs", []).append("%s -> HTTP %s len=%s" % (cu[:70], st, len(data) if data else 0))
        if not got:
            rec["status"] = "fail"
            print("  [%02d] FAIL %s" % (i, name))
        log.append(rec)
        time.sleep(0.25)
    lp = os.path.join(BASE, "raw", "wx_dl_log.json")
    old = []
    if os.path.exists(lp):
        try:
            old = json.load(open(lp, encoding="utf-8"))
        except Exception:
            old = []
    old.append({"source": cfg.get("source", os.path.basename(cfgp)), "out": cfg["out"], "ok": ok, "n": len(cfg["items"]), "items": log})
    json.dump(old, open(lp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n完成: %d/%d 张 -> %s" % (ok, len(cfg["items"]), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
