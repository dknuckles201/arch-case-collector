# -*- coding: utf-8 -*-
"""小红书笔记图下载器（浏览器登录态配合）

用法:
    python xhs_dl.py batch.json

batch.json 结构:
[
  {"note": "笔记标题", "dest": "img/05-zhenyuan", "prefix": "XHS-HT",
   "urls": ["https://sns-webpic-qc.xhscdn.com/....!nd_dft_wlteh_webp_3", ...]}
]

要点（踩坑记录）:
- 必须原样使用页面 img.src 里的后缀（!nd_dft_wlteh_webp_3 = 笔记详情大图）。
  擅自替换成别的后缀（如 !nd_dft_wgth_webp_3）会 403 —— 后缀参与签名。
- 必须带 Referer: https://www.xiaohongshu.com/ 与常规 UA，否则 403。
- 落地统一转 jpg，便于 Obsidian / Word 引用。
"""
import json, os, sys, urllib.request, io

BASE = os.path.dirname(os.path.abspath(__file__))

HDR = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
    "Referer": "https://www.xiaohongshu.com/",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

try:
    from PIL import Image
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False


def fetch(url):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read(), r.headers.get("Content-Type", "")


def save(raw, outdir, stem):
    """webp/png/jpg 统一落成 .jpg；PIL 不可用时按原始字节存，扩展名从魔数猜。"""
    os.makedirs(outdir, exist_ok=True)
    if HAVE_PIL:
        try:
            im = Image.open(io.BytesIO(raw))
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGB")
            p = os.path.join(outdir, stem + ".jpg")
            im.save(p, "JPEG", quality=92)
            return p, os.path.getsize(p), "%dx%d" % im.size
        except Exception:
            pass
    ext = ".jpg"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        ext = ".webp"
    elif raw[:8] == b"\x89PNG\r\n\x1a\n":
        ext = ".png"
    p = os.path.join(outdir, stem + ext)
    with open(p, "wb") as f:
        f.write(raw)
    return p, os.path.getsize(p), "?"


def main():
    batch = json.load(open(sys.argv[1], encoding="utf-8"))
    print("PIL:", HAVE_PIL)
    ok = fail = 0
    for grp in batch:
        note = grp.get("note", "")
        outdir = os.path.join(BASE, grp["dest"])
        prefix = grp["prefix"]
        print("\n=== %s -> %s ===" % (note, grp["dest"]))
        for i, u in enumerate(grp["urls"], 1):
            stem = "%s%02d" % (prefix, i)
            try:
                raw, ct = fetch(u)
                p, sz, dim = save(raw, outdir, stem)
                print("  [OK] %-14s %7d B  %-10s %s" % (os.path.basename(p), sz, dim, ct.split(";")[0]))
                ok += 1
            except Exception as e:
                print("  [FAIL] %s  %s  <- %s" % (stem, e, u[:90]))
                fail += 1
    print("\n合计 OK=%d FAIL=%d" % (ok, fail))


if __name__ == "__main__":
    main()
