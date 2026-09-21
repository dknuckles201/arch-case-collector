# -*- coding: utf-8 -*-
"""小红书「搜索 → 自动访问 → 自动落图」一体驱动（依赖 browser-skill 登录态会话）

用法:
    python xhs_search.py search.json

search.json:
{ "session": "dtrv", "wait": 7,
  "queries": [
    {"key": "09-huacheng1", "keyword": "花城壹号院 户型图",
     "prefix": "XHS-HT", "top": 6, "min_hit": 2}
  ] }

行为:
 1) 搜索结果页取 .note-item（标题 + a.cover 的 href，href 内含有效 xsec_token）
 2) 命中关键词（户型/平面/图/资料/测评/解读/首发/样板）的优先，不足 min_hit 条则补足 top 条
 3) 逐条直连笔记页，取 #detail-title / #detail-desc / 详情页大图（!nd_dft_wlteh_webp_3）并落盘 jpg
 4) 编号自动接续目录内已有同前缀文件；全量写 raw/xhs_digest.md 供人工核对文案
"""
import io, json, os, re, subprocess, sys, time, urllib.request

BSK = r"C:\Users\DK\.local\bin\bsk.exe"
BASE = os.path.dirname(os.path.abspath(__file__))

HDR = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
    "Referer": "https://www.xiaohongshu.com/",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

JS_LIST = ('JSON.stringify([...document.querySelectorAll(".note-item")].map(n=>{'
           'const a=n.querySelector("a.cover");const t=n.querySelector(".title");'
           'return {t:t?t.innerText.replace(/\\s+/g," "):"",h:a?a.getAttribute("href"):""}}))')

JS_NOTE = ('JSON.stringify({'
           't:(document.querySelector("#detail-title")||{}).innerText||"",'
           'd:(document.querySelector("#detail-desc")||{}).innerText||"",'
           's:[...new Set([...document.querySelectorAll("img")].map(x=>x.currentSrc||x.src)'
           '.filter(u=>u&&u.indexOf("!nd_dft_wlteh_webp_3")>-1))]})')

HIT = ("户型", "平面", "图", "资料", "测评", "解读", "首发", "样板", "全解", "干货")

from PIL import Image  # noqa: E402


def bsk(*args, timeout=120):
    try:
        r = subprocess.run([BSK] + list(args), capture_output=True, timeout=timeout)
        return (r.stdout or b"").decode("utf-8", "replace"), (r.stderr or b"").decode("utf-8", "replace")
    except subprocess.TimeoutExpired as e:
        o = e.stdout or b""
        return (o.decode("utf-8", "replace") if isinstance(o, bytes) else o), "TIMEOUT"


def parse_json(s):
    """从 bsk evaluate 的 stdout 里抠出 JSON。

    ⚠️ 不能一律先找 '['：笔记对象 {"t":..,"s":[...]} 里也含 '['，
    那时会从 '[' 解析出一个 list 而不是 dict（踩过）。
    改为按**第一个出现的 { 或 [** 判定类型。
    """
    s = (s or "").strip()
    if not s:
        return None
    cands = [p for p in (s.find("{"), s.find("[")) if p >= 0]
    if not cands:
        return None
    i = min(cands)
    close = "}" if s[i] == "{" else "]"
    for end_ch in (close, "}", "]"):
        end = s.rfind(end_ch)
        if end > i:
            try:
                return json.loads(s[i:end + 1])
            except Exception:
                pass
    return None


def next_index(folder, prefix):
    if not os.path.isdir(folder):
        return 1
    mx = 0
    for f in os.listdir(folder):
        m = re.match(re.escape(prefix) + r"(\d+)", f)
        if m:
            mx = max(mx, int(m.group(1)))
    return mx + 1


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
    sess, wait = cfg["session"], cfg.get("wait", 7)
    # ⚠️ 摘要必须【追加】：早先用 'w' 覆盖，第二次运行把第一批笔记文案冲掉了（踩过）
    dp = os.path.join(BASE, "raw", "xhs_digest.md")
    if not os.path.exists(dp):
        open(dp, "w", encoding="utf-8").write("# 小红书抓取记录（自动生成）\n")
    digest = ["\n\n---\n\n## 运行 %s\n" % time.strftime("%Y-%m-%d %H:%M:%S")]

    for q in cfg["queries"]:
        key, kw = q["key"], q["keyword"]
        prefix, top, min_hit = q.get("prefix", "XHS-HT"), q.get("top", 6), q.get("min_hit", 2)
        print("\n" + "#" * 78)
        print("# [%s] 搜索: %s" % (key, kw))

        url = ("https://www.xiaohongshu.com/search_result?keyword="
               + urllib.parse.quote(kw) + "&source=web_explore_feed")
        bsk("navigate", "--session", sess, url)
        time.sleep(wait)
        out, _ = bsk("evaluate", "--session", sess, JS_LIST)
        items = parse_json(out) or []
        items = [x for x in items if x.get("h")]
        print("  搜索结果 %d 条" % len(items))

        # ⚠️ 必须先按项目名收敛：关键词搜索会返回大量泛「户型」笔记（踩过）
        must = q.get("must", [])
        pool = [x for x in items if any(t in (x.get("t") or "") for t in must)] if must else items
        print("  项目名命中 %d / 结果 %d" % (len(pool), len(items)))
        if not pool:
            pool = items
        hit = [x for x in pool if any(k in (x.get("t") or "") for k in HIT)]
        cands = hit[:top]
        if len(cands) < min_hit:
            for x in pool:
                if x not in cands:
                    cands.append(x)
                if len(cands) >= max(min_hit, 3):
                    break
        for x in cands:
            print("   * %s" % x["t"][:50])

        folder = os.path.join(BASE, "img", key)
        n = next_index(folder, prefix)
        digest.append("\n## %s ｜ 搜索词「%s」\n" % (key, kw))

        for it in cands:
            href = it["h"]
            full = "https://www.xiaohongshu.com" + href if href.startswith("/") else href
            print("\n  -> %s" % it["t"][:56])
            o, _ = bsk("navigate", "--session", sess, full)
            if "404" in o:
                print("     404 跳过")
                continue
            time.sleep(wait)
            o, _ = bsk("evaluate", "--session", sess, JS_NOTE)
            d = parse_json(o) or {}
            title, desc, urls = d.get("t", ""), (d.get("d", "") or ""), d.get("s", []) or []
            print("     标题: %s" % title)
            print("     图片: %d 张" % len(urls))
            digest.append("\n### %s\n" % (title or it["t"]))
            if desc:
                digest.append("> " + desc.replace("\n", " ")[:800] + "\n")
            got = []
            for u in urls:
                stem = "%s%02d" % (prefix, n)
                try:
                    p, sz, dim = save(fetch(u), folder, stem)
                    print("     [OK] %-16s %7d B %s" % (os.path.basename(p), sz, dim))
                    got.append(os.path.basename(p))
                    n += 1
                except Exception as e:
                    print("     [FAIL] %s %s" % (stem, e))
            digest.append("- 落盘: %s\n" % (", ".join(got) if got else "无"))

    with open(dp, "a", encoding="utf-8") as f:
        f.write("\n".join(digest))
    print("\n" + "#" * 78)
    print("摘要: %s" % dp)


import urllib.parse  # noqa: E402

if __name__ == "__main__":
    main()
