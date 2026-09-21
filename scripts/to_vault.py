# -*- coding: utf-8 -*-
"""把 2026-09-15 广州叠墅批次的核心素材归档进 Obsidian vault。

目标：<vault>/attachments/Clippings/<项目名>/NNN-<图面内容>.jpg|png
命名依据：逐张审图板目视核验结果（非来源标题）。
"""
import os, shutil, hashlib, sys

V = r"U:\DK_iCloud\iCloudDrive\iCloud~md~obsidian\Arch_Vault"
BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "img")
ATT = os.path.join(V, "attachments", "Clippings")

# (项目展示名, 源目录key, [(源文件名, 目标文件名), ...])
PLAN = [
    ("保利湖光悦色", "03-huguang", [
        ("HT02.png", "001-8B栋首层平面图.png"),
        ("HT01.png", "002-8B栋二层平面图.png"),
        ("HT03.png", "003-8B栋三层平面图.png"),
        ("KE-HT01.jpg", "004-天澜C户型200㎡四房两厅三卫.jpg"),
        ("KE-HT02.jpg", "005-分层平面-室内布置示意.jpg"),
        ("KE-HT03.jpg", "006-晴川B户型142㎡四房两厅两卫.jpg"),
        ("ZZ01-规划鸟瞰总图-夜景.jpg", "007-鸟瞰夜景（产品形态待核）.jpg"),
    ]),
    ("南天名苑", "06-nantian", [
        ("KE-HT01.jpg", "001-360㎡五房两厅四卫三阳台含工人套房.jpg"),
        ("KE-HT02.jpg", "002-A户型270㎡四房双套房.jpg"),
        ("KE-HT04.jpg", "003-C户型140㎡四房双套房.jpg"),
        ("KE-HT05.jpg", "004-B户型200㎡四房双套房.jpg"),
        ("KE-HT06.jpg", "005-E户型250㎡四房双套房.jpg"),
        ("KE-HT03.jpg", "006-分层平面-室内布置示意.jpg"),
    ]),
    ("御溪臻山墅", "08-yuxi", [
        ("HT01.png", "001-中叠A2a户型153.0㎡.png"),
        ("KE-HT01.jpg", "002-中叠A2b户型178.0㎡.jpg"),
        ("HT02.png", "003-下叠B1b户型163.6㎡.png"),
        ("KE-HT03.jpg", "004-下叠A1b户型205.9㎡.jpg"),
        ("KE-HT02.jpg", "005-上叠A3b户型193.0㎡.jpg"),
        ("HT03.jpg", "006-上叠B3b户型220.64㎡.jpg"),
        ("HT06.png", "007-合院A1户型238㎡.png"),
        ("HT05.png", "008-合院B1户型230㎡.png"),
        ("HT07.png", "009-合院C1户型255㎡.png"),
        ("HT04.png", "010-合院D1户型266㎡.png"),
        ("KE-HT05.jpg", "011-合院E户型282.4㎡.jpg"),
        ("ZZ01-规划鸟瞰总图.jpg", "012-规划鸟瞰总图.jpg"),
    ]),
    ("绿城臻园", "05-zhenyuan", [
        ("WX-ZZ01-鸟瞰总图-夜景.jpg", "001-鸟瞰总图-夜景.jpg"),
        ("WX-ZZ02-鸟瞰总图-日景.jpg", "002-鸟瞰总图-日景.jpg"),
        ("XHS-POSTER01-户型全网首发海报-上叠315+合院480-平面已打码.jpg",
         "003-海报-户型图全网首发（上叠与合院平面已打码）.jpg"),
        ("XHS-POSTER02-全户型官方测评海报-含五层缩略平面.jpg",
         "004-海报-全户型官方测评（含五层缩略平面）.jpg"),
    ]),
    ("金茂越秀璞樾墅", "01-puyueshu", [
        ("ZZ01-规划鸟瞰总图.jpg", "001-规划鸟瞰总图.jpg"),
        ("ZZ02-规划鸟瞰总图-组团.jpg", "002-规划鸟瞰总图-组团.jpg"),
    ]),
    ("南沙凤鸣山", "11-fengming", [
        ("HT01.jpg", "001-8栋02约97㎡三房两卫+灵动空间.jpg"),
        ("HT03.jpg", "002-8栋04约89㎡三房两卫+灵动空间.jpg"),
        ("HT04.jpg", "003-8栋06约107㎡三房两卫+灵动空间.jpg"),
        ("HT02.jpg", "004-04户型平面-室内布置示意.jpg"),
        ("ZZ01-规划鸟瞰总图.jpg", "005-规划鸟瞰总图.jpg"),
    ]),
    ("观樾天湖", "02-guanyue", [
        ("HT01.png", "001-190㎡户型鉴赏（大平层）.png"),
        ("HT02.png", "002-252㎡户型鉴赏（大平层）.png"),
        ("ZZ01-规划鸟瞰总图.jpg", "003-规划鸟瞰总图.jpg"),
        ("ZZ02-规划鸟瞰总图-标注版.jpg", "004-规划鸟瞰总图-标注版.jpg"),
    ]),
    ("中海熙园", "10-xinyuan", [
        ("ZZ03-规划鸟瞰总图-含批准许可证号20181414.jpg",
         "001-规划鸟瞰总图-含预售许可证号20181414.jpg"),
        ("ZZ01-规划鸟瞰总图.jpg", "002-规划鸟瞰总图.jpg"),
        ("ZZ02-规划鸟瞰总图-全景.jpg", "003-规划鸟瞰总图-全景.jpg"),
        ("ZZ04-规划鸟瞰总图-岭南组团.jpg", "004-规划鸟瞰总图-岭南组团.jpg"),
    ]),
    ("岭南1号", "07-lingnan1", [
        ("XHS-ZZ01-沙盘模型-临湖独栋与泳池.jpg", "001-沙盘模型-临湖独栋与泳池.jpg"),
        ("XHS-ZZ02-沙盘模型-四层错层露台.jpg", "002-沙盘模型-四层错层露台.jpg"),
    ]),
]

DRY = "--dry" in sys.argv
ok = miss = 0
report = []
for proj, key, files in PLAN:
    dst_dir = os.path.join(ATT, proj)
    if not DRY:
        os.makedirs(dst_dir, exist_ok=True)
    for src, dst in files:
        sp = os.path.join(IMG, key, src)
        dp = os.path.join(dst_dir, dst)
        if not os.path.exists(sp):
            print("  MISS %-16s %s" % (proj, src)); miss += 1; continue
        if os.path.exists(dp):
            print("  EXISTS %-16s %s" % (proj, dst)); continue
        if not DRY:
            tmp = dp + ".tmp"
            shutil.copy2(sp, tmp)                       # 1) 写 tmp
            assert os.path.getsize(tmp) == os.path.getsize(sp), "size mismatch"
            with open(tmp, "rb") as fh:                 # 2) 读回校验
                h1 = hashlib.md5(fh.read()).hexdigest()
            with open(sp, "rb") as fh:
                h2 = hashlib.md5(fh.read()).hexdigest()
            assert h1 == h2, "hash mismatch %s" % dst
            os.replace(tmp, dp)                          # 3) 原子改名
        report.append((proj, dst, os.path.getsize(sp)))
        ok += 1

for proj, dst, sz in report:
    print("  %-16s %-58s %8.1f KB" % (proj, dst, sz / 1024))
print()
print("复制 %d 个文件，缺失 %d 个%s" % (ok, miss, "（DRY RUN）" if DRY else ""))
