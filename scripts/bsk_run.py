#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bsk 稳健调用器（Windows 本机 bash shim 缺 dirname/head/cat，且 daemon 升级期会丢 session）

用法:
  python bsk_run.py status
  python bsk_run.py ensure <session>          # 确保 session 存在（不存在则新建），打印 session id
  python bsk_run.py nav <session> <url>       # 导航
  python bsk_run.py eval <session> <js>       # 求值（返回 JSON 字符串）
  python bsk_run.py html <session> | text <session> | shot <session> <out.png>
  python bsk_run.py raw <session> <args...>   # 直接透传其余参数给 bsk
"""
import json
import subprocess
import sys
import time

BSK = r"C:\Users\DK\.local\bin\bsk.exe"


def run(args, timeout=90):
    p = subprocess.run([BSK] + args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def clean(s):
    # 过滤 shim 噪声与版本提示
    out = []
    for line in (s or "").splitlines():
        if "shell-runtime-bash-env.sh" in line:
            continue
        if "A new bsk version is available" in line:
            continue
        out.append(line)
    return "\n".join(out).strip()


def status():
    rc, o, e = run(["status"])
    print("rc=%s\n%s\n[stderr]%s" % (rc, clean(o), clean(e)))
    return rc


def ensure(sess):
    """确保 session 可用；返回实际 session id"""
    rc, o, e = run(["session", "list"])
    body = clean(o)
    if sess in body:
        print("session %s 已存在" % sess)
        return sess
    rc, o, e = run(["session", "start"])
    got = clean(o).strip().splitlines()[-1].strip() if clean(o).strip() else ""
    print("session start -> %r (rc=%s) %s" % (got, rc, clean(e)[:200]))
    return got or sess


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "status":
        return status()
    if cmd == "ensure":
        ensure(sys.argv[2])
        time.sleep(0.4)
        return status()
    if cmd == "nav":
        sess, url = sys.argv[2], sys.argv[3]
        rc, o, e = run(["navigate", "--session", sess, url], timeout=120)
        print("rc=%s %s %s" % (rc, clean(o)[:400], clean(e)[:300]))
        return rc
    if cmd == "eval":
        sess, js = sys.argv[2], sys.argv[3]
        rc, o, e = run(["evaluate", "--session", sess, js], timeout=120)
        print(clean(o)[:200] if rc else clean(o))
        if rc:
            print("[stderr]", clean(e)[:300])
        return rc
    if cmd == "html":
        rc, o, e = run(["get-html", "--session", sys.argv[2]], timeout=120)
        print(clean(o))
        return rc
    if cmd == "text":
        rc, o, e = run(["get-text", "--session", sys.argv[2]], timeout=120)
        print(clean(o))
        return rc
    if cmd == "shot":
        rc, o, e = run(["screenshot", "--session", sys.argv[2], "--out", sys.argv[3]], timeout=120)
        print("rc=%s %s" % (rc, clean(o)[:300]))
        return rc
    if cmd == "raw":
        sess = sys.argv[2]
        rest = sys.argv[3:]
        for i, a in enumerate(rest):
            if a == "@session":
                rest[i] = sess
        rc, o, e = run(rest, timeout=180)
        print(clean(o))
        if rc:
            print("[stderr]", clean(e)[:400])
        return rc
    print("unknown cmd", cmd)
    return 1


if __name__ == "__main__":
    sys.exit(main())
