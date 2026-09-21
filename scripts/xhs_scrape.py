# -*- coding: utf-8 -*-
"""小红书笔记批量抓取驱动（依赖 browser-skill 登录态会话）

用法:
    python xhs_scrape.py session.json

session.json:
{ "session": "dtrv", "dest_root": "img", "wait": 7,
  "cands": [
    {"key": "09-huacheng1", "note": "花城壹号院 别墅、叠墅、联排",
     "href": "/search_result/6a938a3b0000000008012668?xsec_token=...&xsec_source=",
     "prefix": "XHS-HT", "start": 1,
     "host": "https://www.xiaohongshu.com"}
  ] }

流程: bsk navigate -> 等待 SPA 渲染 -> bsk evaluate 取标题/正文/图片直链 -> 落盘 jpg
失败不中断，全量记 raw/xhs_scrape_log.json
"""
import json, os, subprocess, sys, time, urllib.request, io

BSK = r"C:\Users\DK\.local\bin\bsk.exe"
BASE = os.path.dirname(os.path.abspath(__file__))

HDR = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
    "Referer": "https://www.xiaohongshu.com/",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

JS = ('JSON.stringify({'
      't:(document.querySelector("#detail-title")||{}).innerText||"",'
      'd:(document.querySelector("#detail-desc")||{}).innerText||"",'
      's:[...new Set([...document.querySelectorAll("img")].map(x=>x.currentSrc||x.src)'
      '.filter(u=>u&&u.indexOf("!nd_dft_wlteh_webp_3")>-1))]})')

from PIL import Image  # noqa: E402


def bsk(*args, timeout=120):
    try:
        r = subprocess.run([BSK] + list(args), capture_output=True, timeout=timeout)
        out = r.stdout.decode("utf-8", "replace")
        err = r.stderr.decode("utf-8", "replace")
        return r.returncode, out, err
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        return -9, out, "TIMEOUT"


def fetch(url):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def save(raw, outdir, stem):
    os.makedirs(outdir, exist_ok=True)
    im = Image.open(io.BytesIO(raw))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGB")
    p = os.path.join(outdir, stem + ".jpg")
    im.save(p, "JPEG", quality=92)
    return p, os.path.getsize(p), "%dx%d" % im.size


def main():
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    sess = cfg["session"]
    wait = cfg.get("wait", 7)
    root = cfg.get("dest_root", "img")
    log = []
    for c in cfg["cands"]:
        url = c.get("host", "https://www.xiaohongshu.com") + c["href"]
        item = {"key": c["key"], "note": c["note"], "url": url,
                "title": "", "desc": "", "got": [], "failed": []}
        print("\n" + "=" * 78)
        print("[%s] %s" % (c["key"], c["note"]))

        rc, out, err = bsk("navigate", "--session", sess, url)
        if "404" in out or "error_code" in out:
            print("  !! 404 / 反爬拦截")
            item["error"] = "404"
            log.append(item)
            continue
        time.sleep(wait)

        rc, out, err = bsk("evaluate", "--session", sess, JS)
        out = out.strip()
        try:
            i = out.index("{")
            data = json.loads(out[i:out.rindex("}") + 1])
        except Exception as e:
            print("  !! evaluate 解析失败: %s | raw=%s" % (e, out[:200]))
            item["error"] = "parse"
            log.append(item)
            continue

        item["title"] = data.get("t", "")
        item["desc"] = (data.get("d", "") or "")[:600]
        urls = data.get("s", [])
        print("  标题: %s" % item["title"])
        print("  图片: %d 张" % len(urls))
        if item["desc"]:
            print("  正文: %s" % item["desc"].replace("\n", " ")[:180])

        outdir = os.path.join(BASE, root, c["key"])
        n = c.get("start", 1)
        for u in urls:
            stem = "%s%02d" % (c["prefix"], n)
            try:
                raw = fetch(u)
                p, sz, dim = save(raw, outdir, stem)
                print("    [OK] %-14s %7d B  %s" % (os.path.basename(p), sz, dim))
                item["got"].append(os.path.basename(p))
                n += 1
            except Exception as e:
                print("    [FAIL] %s %s" % (stem, e))
                item["failed"].append(stem)
        log.append(item)

    lp = os.path.join(BASE, "raw", "xhs_scrape_log.json")
    json.dump(log, open(lp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n" + "=" * 78)
    print("汇总: 笔记 %d 篇, 成功取图 %d 张, 失败 %d 张"
          % (len(log), sum(len(x["got"]) for x in log), sum(len(x["failed"]) for x in log)))
    print("日志: %s" % lp)


if __name__ == "__main__":
    main()
