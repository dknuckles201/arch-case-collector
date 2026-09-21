# -*- coding: utf-8 -*-
"""按「逐张视觉核验」的结论重建图片分类与命名。

分类前缀：
  HT     户型图（平面图）
  ZZ     总图 / 规划鸟瞰 / 沙盘模型（总平面级）
  POSTER 营销海报（含户型缩略或打码，不可作正式户型图）
  ALB    楼盘图（效果图 / 实景 / 景观 / 室内）
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "img")

# key: 目录 -> {旧名: 新名}
MAP = {
    "01-puyueshu": {
        # HT01 是室内渲染俯视图，不是户型图
        "HT01.jpg": "ALB07-室内渲染俯视-非户型图.jpg",
        "ALB01.jpg": "ALB01-疑图库占位-超高层塔楼.jpg",
        "ALB06.jpg": "ALB06-疑图库占位-P&L办公楼.jpg",
        "ALB03.jpg": "ZZ01-规划鸟瞰总图.jpg",
        "ALB04.jpg": "ZZ02-规划鸟瞰总图-组团.jpg",
    },
    "02-guanyue": {
        "ALB07.jpg": "ZZ01-规划鸟瞰总图.jpg",
        "ALB09.png": "ZZ02-规划鸟瞰总图-标注版.png",
    },
    "03-huguang": {
        "ALB01.jpg": "ZZ01-规划鸟瞰总图-夜景.jpg",
    },
    "05-zhenyuan": {
        "XHS-HT01-合院叠拼户型1.jpg": "XHS-ALB07-芙蓉池水景.jpg",
        "XHS-HT02-合院叠拼户型2.jpg": "XHS-POSTER01-户型全网首发海报-上叠315+合院480-平面已打码.jpg",
        "XHS-HT03-合院叠拼户型3.jpg": "XHS-ALB08-会所江景.jpg",
        "XHS-HT04-合院叠拼户型4.jpg": "XHS-ALB09-臻境会所.jpg",
        "XHS-HT05-合院叠拼户型5.jpg": "XHS-ALB10-柳波廊.jpg",
        "XHS-HT06-全户型测评1.jpg": "XHS-POSTER02-全户型官方测评海报-含五层缩略平面.jpg",
        "XHS-HT07-全户型测评2.jpg": "XHS-ALB11-会所大堂.jpg",
        "XHS-HT08-全户型测评3.jpg": "XHS-ALB12-会所旋转梯与江景.jpg",
        "XHS-HT09-全户型测评4.jpg": "XHS-ALB13-会所露台江景.jpg",
        "XHS-HT10-全户型测评5.jpg": "XHS-ALB14-会所环廊.jpg",
        "XHS-HT11-全户型测评6.jpg": "XHS-ALB15-芙蓉池与柳波廊.jpg",
        "WX-ALB08-夜景效果图.jpg": "WX-ZZ01-鸟瞰总图-夜景.jpg",
        "WX-ALB09-建筑效果图.jpg": "WX-ZZ02-鸟瞰总图-日景.jpg",
        "ALB06.jpg": "ALB06-疑图库占位-超高层塔楼.jpg",
    },
    "07-lingnan1": {
        "XHS-ALB01-岭南1号-笔记图1.jpg": "XHS-ZZ01-沙盘模型-临湖独栋与泳池.jpg",
        "XHS-ALB02-岭南1号-笔记图2.jpg": "XHS-ZZ02-沙盘模型-四层错层露台.jpg",
    },
    "08-yuxi": {
        "ALB03.jpg": "ZZ01-规划鸟瞰总图.jpg",
        "ALB05.jpg": "ALB05-疑图库占位-写字楼群夜景.jpg",
    },
    "09-huacheng1": {
        # 该图经核为小红书正文文字截图，不是图纸
        "XHS-ALB05-疑图纸-花都看房帖.jpg": "XHS-ALB05-笔记正文截图-非图纸.jpg",
    },
    "10-xinyuan": {
        "ALB02.jpg": "ZZ01-规划鸟瞰总图.jpg",
        "ALB04.jpg": "ZZ02-规划鸟瞰总图-全景.jpg",
        "ALB05.jpg": "ZZ03-规划鸟瞰总图-含批准许可证号20181414.jpg",
        "ALB07.jpg": "ZZ04-规划鸟瞰总图-岭南组团.jpg",
    },
    "11-fengming": {
        "ALB03.jpg": "ALB03-疑图库占位-滨海度假小镇.jpg",
        "ALB04.jpg": "ALB04-疑图库占位-CBD超高层夜景.jpg",
        "ALB05.jpg": "ZZ01-规划鸟瞰总图.jpg",
    },
}


def bucket(fn):
    if "POSTER" in fn:
        return "POSTER"
    if "ZZ" in fn:
        return "ZZ"
    if "HT" in fn:
        return "HT"
    return "ALB"


def main():
    todo, missing = 0, []
    for key, m in MAP.items():
        d = os.path.join(IMG, key)
        for old, new in m.items():
            po, pn = os.path.join(d, old), os.path.join(d, new)
            if not os.path.exists(po):
                if not os.path.exists(pn):
                    missing.append("%s/%s" % (key, old))
                continue
            if os.path.exists(pn):
                os.remove(pn)
            os.rename(po, pn)
            print("  [%s] %s\n        -> %s" % (key, old, new))
            todo += 1
    print("\n改名 %d 个文件" % todo)
    if missing:
        print("未找到（可能已改过）:")
        for x in missing:
            print("   ", x)

    print("\n" + "=" * 74)
    print("重建后分类统计（前 4 列 = 户型图 / 总图 / 海报 / 楼盘图）")
    print("=" * 74)
    tot = {"HT": 0, "ZZ": 0, "POSTER": 0, "ALB": 0}
    for key in sorted(os.listdir(IMG)):
        d = os.path.join(IMG, key)
        if not os.path.isdir(d):
            continue
        cnt = {"HT": 0, "ZZ": 0, "POSTER": 0, "ALB": 0}
        for f in sorted(os.listdir(d)):
            if key == "05-zhenyuan" and f.endswith(".jpg") and f.startswith("XHS-POSTER"):
                pass
            cnt[bucket(f)] += 1
        for k in cnt:
            tot[k] += cnt[k]
        flag = ""
        if cnt["HT"] == 0:
            flag = "  ← 无户型图"
        if cnt["ZZ"] == 0 and cnt["HT"] > 0:
            flag += "  ← 无总图"
        print("  %-14s HT=%-2d ZZ=%-2d POSTER=%-2d ALB=%-2d%s"
              % (key, cnt["HT"], cnt["ZZ"], cnt["POSTER"], cnt["ALB"], flag))
    print("-" * 74)
    print("  合计            HT=%-2d ZZ=%-2d POSTER=%-2d ALB=%-2d"
          % (tot["HT"], tot["ZZ"], tot["POSTER"], tot["ALB"]))
    print("  即有：户型图 %d 张、总图级 %d 张" % (tot["HT"], tot["ZZ"]))


if __name__ == "__main__":
    main()
