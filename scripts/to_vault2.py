# -*- coding: utf-8 -*-
"""第二轮 vault 归档：把「微信公众号通道」新增取得的总图级 / 证据类素材补进 vault。

与 to_vault.py 同策略：写 .tmp → 尺寸/ md5 校验 → 原子改名；目标已存在则跳过、绝不覆盖、绝不重命名既有文件。
编号一律**追加在既有编号之后**（按取得顺序），既有文件一个不动。
"""
import os, shutil, hashlib, sys

V = r"U:\DK_iCloud\iCloudDrive\iCloud~md~obsidian\Arch_Vault"
BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "img")
ATT = os.path.join(V, "attachments", "Clippings")

# (项目展示名, 源目录key, 起始编号, [(源文件名, 目标文件名), ...])
PLAN = [
    ("绿城臻园", "05-zhenyuan", 5, [
        ("WX-ZZ03-规划总平面图（地块边界·楼栋编号·绿化用地）.jpg",
         "005-规划总平面图（用地红线·楼栋功能标注·绿化用地BOO613023-040）.jpg"),
        ("WX-ZZ04-产品落位图（临江墅合院318-480㎡·望江墅上叠315㎡）.jpg",
         # ⚠️ 目标名不得含 `#`：Obsidian 的 [[...]] 会把 `#` 当成标题锚点，链接即失效
         "006-产品落位图（望江墅上叠315㎡·临江墅合院318-338-358-388-480㎡）.jpg"),
        ("WX-ZZ05-区位图（黄沙岛地块位置标注）.jpg", "007-区位图（黄沙岛地块位置标注）.jpg"),
        ("WX-ZZ06-区位图（番禺广场配套与地铁18-22号线）.jpg",
         "008-区位图（番禺广场配套与地铁18-22号线）.jpg"),
    ]),
    ("南天名苑", "06-nantian", 7, [
        ("WX-ZZ01-总平面图（产品分区标注）.jpg",
         "007-总平面图（产品分区标注·含指北针与图例）.jpg"),
        ("WX-ZZ02-岛尖整体鸟瞰（含配套标注）.jpg", "008-岛尖整体鸟瞰（含配套标注）.jpg"),
        ("WX-ZZ03-区位图（交通·珠江后航道）.jpg", "009-区位图（交通·珠江后航道）.jpg"),
    ]),
    ("岭南1号", "07-lingnan1", 3, [
        # ⚠️ WX-ZZ03 与 WX-ZZ04 为同一张渲染图的跨号重复（仅水印不同），
        #    且 WX-ZZ03 仅 673×345、WX-ZZ04 为 1290×660 → 保留高清版本 WX-ZZ04，弃 WX-ZZ03。
        ("WX-ZZ04-整体鸟瞰（含楼栋编号）.jpg",
         "003-整体鸟瞰（含凯悦系配套标注）.jpg"),
        ("WX-ZZ05-配套区位图（学校医院）.jpg", "004-配套区位图（学校医院）.jpg"),
    ]),
    ("金茂越秀璞樾墅", "01-puyueshu", 3, [
        ("WX-ZZ01-世界大观四组团规划鸟瞰（含各期容积率）.jpg",
         "003-世界大观四组团规划鸟瞰（含各期容积率）.jpg"),
        ("WX-ZZ02-观樾社区配套分布示意图.jpg", "004-观樾社区配套分布示意图.jpg"),
        ("WX-ZZ03-月亮湖·中心湖·太阳湖整体鸟瞰.jpg", "005-月亮湖·中心湖·太阳湖整体鸟瞰.jpg"),
        ("WX-ALB11-四进礼制与组团关系（含组团小平面）.jpg",
         "006-四进礼制与组团关系（含组团小平面）.jpg"),
        ("WX-ALB10-19栋上叠网签数据（331.3㎡·18.99万·6259万）.jpg",
         "007-19栋上叠网签数据（331.3㎡·18.99万·6259万）.jpg"),
    ]),
    ("中海熙园", "10-xinyuan", 5, [
        ("WX-ZZ06-总平面示意图（规划·含水景与动线）.jpg",
         "005-总平面示意图（规划·含水景与动线）.jpg"),
        ("WX-ZZ05-整体鸟瞰（叠墅群·中轴景观）.jpg", "006-整体鸟瞰（叠墅群·中轴景观）.jpg"),
        ("WX-ALB13-景观纹样与铺装设计图集.jpg", "007-景观纹样与铺装设计图集.jpg"),
    ]),
    ("城投花城壹号院", "09-huacheng1", 1, [
        ("WX-ZZ01-区位示意图（花都中轴）.jpg", "001-区位示意图（花都中轴）.jpg"),
        ("WX-ZZ02-区位配套九宫格.jpg", "002-区位配套九宫格.jpg"),
        ("WX-ALB07-项目信息表（容积率·户数·产品）.jpg", "003-项目信息表（容积率·户数·产品）.jpg"),
    ]),
]

DRY = "--dry" in sys.argv
ok = miss = 0
report = []
for proj, key, start, files in PLAN:
    dst_dir = os.path.join(ATT, proj)
    if not DRY:
        os.makedirs(dst_dir, exist_ok=True)
    for src, dst in files:
        sp = os.path.join(IMG, key, src)
        dp = os.path.join(dst_dir, dst)
        if not os.path.exists(sp):
            print("  MISS  %-16s %s" % (proj, src)); miss += 1; continue
        if os.path.exists(dp):
            print("  EXISTS %-16s %s" % (proj, dst)); continue
        if not DRY:
            tmp = dp + ".tmp"
            shutil.copy2(sp, tmp)
            assert os.path.getsize(tmp) == os.path.getsize(sp), "size mismatch %s" % dst
            with open(tmp, "rb") as fh:
                h1 = hashlib.md5(fh.read()).hexdigest()
            with open(sp, "rb") as fh:
                h2 = hashlib.md5(fh.read()).hexdigest()
            assert h1 == h2, "hash mismatch %s" % dst
            os.replace(tmp, dp)
        report.append((proj, dst, os.path.getsize(sp)))
        ok += 1

for proj, dst, sz in report:
    print("  %-14s %-62s %8.1f KB" % (proj, dst, sz / 1024))
print()
print("本轮复制 %d 个文件，缺失 %d 个%s" % (ok, miss, "（DRY RUN）" if DRY else ""))
