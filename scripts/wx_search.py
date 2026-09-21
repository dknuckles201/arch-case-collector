#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微信公众号自动检索 + 取图（搜狗微信入口）

用法:
  python wx_search.py raw/wx_tasks.json

流程（每个 query）:
  1) navigate 搜狗微信文章搜索
  2) 抽取结果列表（标题/链接/日期）
  3) 按项目别名过滤命中
  4) 逐个打开文章 → 抽取标题/公众号/日期/正文/图片直链 → 落 raw/wx_articles/
  5) 下载正文图到 img/_wx/<key>/，拼审图板由 sheet_any.py 负责
输出: raw/wx_digest.md（追加写，含每篇的字段摘要与图片数）

要点:
  * 搜狗结果链接是 /link?url=…，必须在页内 location.href 跳转（保留 referer）
  * 搜狗分词很粗（「璞樾墅」会召回北京一堆盘），所以用**项目全名**检索 + 别名过滤
  * 微信图片 mmbiz.qpic.cn 非签名，/640 -> /0 取原图
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")

JS_LIST = ('JSON.stringify([...document.querySelectorAll(".news-list li")].map(li=>{'
           'const a=li.querySelector("h3 a");const s=li.querySelector(".s-p");const d=li.querySelector(".s2");'
           'return {t:a?a.innerText.trim():"",h:a?a.getAttribute("href"):"",s:s?s.innerText.trim().replace(/\\s+/g," ").slice(0,120):"",d:d?d.innerText.trim():""};}))')

JS_ART = ('JSON.stringify({t:(document.querySelector("#activity-name")||{}).innerText,'
          'acc:(document.querySelector("#js_name")||{}).innerText,'
          'date:(document.querySelector("#publish_time")||{}).innerText,'
          'url:location.href,'
          'text:((document.querySelector("#js_content")||{}).innerText||"").replace(/\\n{2,}/g,"\\n").slice(0,9000),'
          'imgs:[...document.querySelectorAll("#js_content img")].map(i=>i.getAttribute("data-src")||i.src)})')


def clean(s):
    out = []
    for line in (s or "").splitlines():
        if "shell-runtime-bash-env.sh" in line or "A new bsk version is available" in line:
            continue
        out.append(line)
    return "\n".join(out).strip()


def bsk(args, timeout=150):
    try:
        p = subprocess.run(["bsk"] + args, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, clean(p.stdout), clean(p.stderr)
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


def ev(sess, js):
    rc, o, e = bsk(["evaluate", "--session", sess, js])
    if rc != 0:
        print("      [ev fail %s] %s" % (rc, e[:120]))
        return None
    return o


def parse_json(s, arr_first=False):
    """从混杂输出里抠出 JSON（兼容 bsk 直接回显字符串 / 回显 JSON 转义字符串两种）"""
    if not s:
        return None
    variants = [s]
    if '\\"' in s:
        variants.append(s.replace('\\"', '"').replace("\\n", "\n"))
    for src in variants:
        order = ("[", "{") if arr_first else ("{", "[")
        for op in order:
            cl = {"[": "]", "{": "}"}[op]
            i, j = src.find(op), src.rfind(cl)
            if 0 <= i < j:
                try:
                    return json.loads(src[i:j + 1])
                except Exception:
                    pass
        for i, ch in enumerate(src):
            if ch in "[{":
                cl = {"[": "]", "{": "}"}[ch]
                j = src.rfind(cl)
                if j > i:
                    try:
                        return json.loads(src[i:j + 1])
                    except Exception:
                        continue
    return None


def fetch_image(url, referer="https://mp.weixin.qq.com/", timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer,
                                               "Accept": "image/*,*/*;q=0.8"})
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


def download_all(imgs, outdir, prefix, referer):
    os.makedirs(outdir, exist_ok=True)
    recs, ok = [], 0
    for i, u in enumerate(imgs, 1):
        name = "%s%02d.jpg" % (prefix, i)
        dst = os.path.join(outdir, name)
        rec = {"i": i, "name": name, "url": u.split("#")[0][:140]}
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            rec["status"] = "exists"
            recs.append(rec); ok += 1
            continue
        done = False
        for cu in [u.replace("/640?", "/0?"), u.split("#")[0]]:
            try:
                st, data = fetch_image(cu, referer)
            except Exception as e:
                rec.setdefault("errs", []).append(str(e)[:80]); continue
            if st == 200 and data and len(data) > 1500:
                w, h = dims(data)
                open(dst + ".tmp", "wb").write(data)
                os.replace(dst + ".tmp", dst)
                rec.update(status=200, bytes=len(data), px="%sx%s" % (w, h))
                ok += 1; done = True
                break
        if not done:
            rec["status"] = "fail"
        recs.append(rec)
        time.sleep(0.15)
    return ok, recs


def main():
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    sess = cfg["session"]
    wait = cfg.get("wait", 4)
    digest = []
    stat = []
    for task in cfg["tasks"]:
        key, name = task["key"], task["name"]
        aliases = task.get("aliases", [name])
        excls = task.get("exclude", [])
        tops = task.get("top", 2)
        seen_hrefs = set()
        print("\n" + "=" * 78)
        print("### %s  %s" % (key, name))
        picked = []
        for q in task["queries"]:
            url = "https://weixin.sogou.com/weixin?type=2&ie=utf8&query=" + urllib.parse.quote(q)
            rc, o, e = bsk(["navigate", "--session", sess, url])
            if rc != 0:
                print("  nav fail", e[:120]); continue
            time.sleep(0.6)
            lst = parse_json(ev(sess, JS_LIST), arr_first=True)
            if not lst:
                page = ev(sess, 'JSON.stringify({t:document.title,a:document.body.innerText.slice(0,150)})')
                print("  [%s] 无结果页: %s" % (q, (page or "")[:140]))
                continue
            hits = []
            for idx, x in enumerate(lst):
                if not x.get("h"):
                    continue
                t = x.get("t") or ""
                if any(al in t for al in aliases) and not any(ex in t for ex in excls):
                    hits.append((idx, x))
            print("  [%s] 结果 %d 条 → 命中项目名 %d 条" % (q, len(lst), len(hits)))
            for idx, x in hits:
                if x["h"] in seen_hrefs:
                    continue
                if len([p for p in picked if p["q"] == q]) >= tops:
                    break
                seen_hrefs.add(x["h"])
                picked.append({"q": q, "search": url, "idx": idx, "t": x["t"], "d": x.get("d", "")})
            for idx, x in hits:
                print("      · %s  (%s)" % (x["t"][:64], x.get("d", "")))
        # 打开候选文章
        for n, x in enumerate(picked, 1):
            print("   -> 打开 [%d] %s" % (n, x["t"][:60]))
            # 必须先回到该 query 的结果页，再于页内跳转（搜狗校验 referer）
            rc, o, e = bsk(["navigate", "--session", sess, x["search"]])
            if rc != 0:
                print("      nav(search) fail")
                continue
            time.sleep(1.2)
            rc, o, e = bsk(["evaluate", "--session", sess,
                            'location.href=document.querySelectorAll(".news-list li h3 a")[%d].href; "go"' % x["idx"]])
            if rc != 0:
                print("      jump fail")
                continue
            time.sleep(wait)
            art = parse_json(ev(sess, JS_ART))
            if not art or not art.get("imgs"):
                cur = ev(sess, 'JSON.stringify({u:location.href,t:document.title,n:document.body.innerText.length})')
                print("      × 未取到正文: %s" % (cur or "")[:150])
                continue
            if "mp.weixin.qq.com" not in (art.get("url") or ""):
                print("      × 非文章页: %s" % (art.get("url") or "")[:120])
                continue
            ad = os.path.join(BASE, "raw", "wx_articles")
            os.makedirs(ad, exist_ok=True)
            snap = os.path.join(ad, "%s-%02d.json" % (key, n))
            json.dump(art, open(snap, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            outdir = os.path.join(BASE, "img", "_wx", key)
            ok, recs = download_all(art["imgs"], outdir, "WX%02d-" % n, art.get("url") or "https://mp.weixin.qq.com/")
            print("      ✓ %s | %s | %s | 图 %d/%d" % (art.get("t", "")[:40], art.get("acc", ""),
                                                        art.get("date", ""), ok, len(art["imgs"])))
            digest.append({
                "key": key, "n": n, "title": art.get("t", ""), "acc": art.get("acc", ""),
                "date": art.get("date", ""), "url": art.get("url", ""),
                "imgs_n": len(art["imgs"]), "imgs_ok": ok, "snap": os.path.relpath(snap, BASE),
                "text": art.get("text", ""), "recs": recs})
            stat.append((key, ok))
    # 摘要
    if digest:
        dp = os.path.join(BASE, "raw", "wx_digest.md")
        old = open(dp, encoding="utf-8").read() if os.path.exists(dp) else "# 微信公众号抓取记录（追加）\n"
        lines = [old.rstrip(), "", "## 批次 %s" % time.strftime("%Y-%m-%d %H:%M")]
        for it in digest:
            lines.append("### [%s] %s | %s | %s | 图 %d/%d" % (it["key"], it["title"][:70], it["acc"], it["date"],
                                                              it["imgs_ok"], it["imgs_n"]))
            lines.append("snap: `%s`" % it["snap"])
            lines.append("")
            lines.append("```")
            lines.append(it["text"][:2600])
            lines.append("```")
            lines.append("")
        open(dp, "w", encoding="utf-8").write("\n".join(lines))
        print("\n摘要 -> raw/wx_digest.md")
    print("\n完成: 文章 %d 篇，图片 %d 张" % (len(digest), sum(s[1] for s in stat)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
