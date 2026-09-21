# -*- coding: utf-8 -*-
"""生成可视化候选清单 HTML（相对路径引用 img/<key>/）"""
import os, json, html

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = "img"

# score = 可信度*0.35 + 相关度*0.30 + 完整度*0.25 + 新鲜度*0.10
P = [
 dict(key="01-puyueshu", name="金茂越秀·璞樾墅", city="广州天河", folder="住宅居住",
      arch="广州宸茂置业有限公司（中国金茂 + 越秀地产联合开发）",
      year="2025 首开", loc="天河区世界大观板块（天河智谷）",
      area="上合墅 190–335㎡ / 下合墅 200–360㎡ / 临湖端头墅 360–550㎡",
      feat="新规四代合墅：分台入户、7m 挑高客厅、层高约 3.5m，拓展使用率约 200%",
      cred=70, rel=95, comp=52, fresh=95,
      srcs=["吉屋 lpcp/34762", "搜狐焦点 2026.8.31", "腾讯新闻·全国高端20强入围", "克而瑞好房点评", "贝壳 p_jmyxpysboazg（无户型图）"],
      note="⚠️ 经逐张视觉核验，原先计入的「户型图 1 张」实为**室内渲染俯视效果图**，已改判为非户型图 → **本项目户型图 0 张**。吉屋相册另有 2 张疑为图库占位素材（超高层塔楼效果图、带 P&L 标识的办公楼效果图），与「新规四代合墅」产品完全不符，已标注待到现场核验；贝壳 p_jmyxpysboazg 户型图位为空。✅ 本轮补入总图级素材 2 张（规划鸟瞰总图、组团鸟瞰，来自吉屋相册）。字段冲突：总户数 110/111；楼栋 28/29；上叠面积上限 260/335 两口径"),

 dict(key="03-huguang", name="保利湖光悦色（含「湖心墅」新组团）", city="广州海珠", folder="住宅居住",
      arch="广州穗鸿置业有限公司（保利发展）",
      year="2024-07 实景交付", loc="海珠区华洲路 61 号（海珠国家湿地公园东南侧）",
      area="下叠 218–254㎡ / 中叠 179–206㎡ / 上叠 326–362㎡",
      feat="480m 石榴岗河岸一字排布，全玻璃幕墙 + 转角曲面玻璃 + 深灰铝板，私梯入户、使用率>200%",
      cred=70, rel=95, comp=88, fresh=90,
      srcs=["吉屋 lpcp/31640", "吉屋 lpcp/36820", "南方+（湖心墅入市）", "搜狐焦点", "贝壳 p_blhgysbmrjv（户型图 3 张）"],
      note="✅ 已有户型图 6 张，经逐张核验：8B# 首层 / 二层 / 三层平面图 3 张（＝叠墅分层平面，图面标注各层面积计算表），贝壳 C「天澜」200㎡ 4房2厅3卫、B「晴川」142㎡ 4房2厅2卫 及 1 张分层平面（含南向大面宽标注）。✅ 另补总图 1 张（规划鸟瞰夜景）。⚠️ 多源合并：「保利湖心墅」经核为湖光悦色洋房开发收尾后推出的新组团，非独立项目；备案名 颂展花园 / 保利朗境花园 两口径"),

 dict(key="08-yuxi", name="御溪臻山墅", city="广州增城", folder="住宅居住",
      arch="口径冲突：广州孚创 / 广州御溪 / 广州天盈（另称中建东孚+侨建+劲和+融创）",
      year="2026 分批交付", loc="增城区中新镇广汕公路旁（备案名 孚创雅苑）",
      area="中叠 155–167㎡ / 下叠 165–166㎡ / 上叠 185–220㎡ / 合院 220–265㎡",
      feat="半山台地、背靠古浪山，距 21 号线中新站约 300–500m；合院赠送率 312%–351%",
      cred=55, rel=95, comp=92, fresh=85,
      srcs=["吉屋 lpcp/31273", "吉屋 lpcp/36466", "搜狐焦点 2026.8–9", "吉屋 info/11783815", "贝壳 p_yxzssbnzlq（户型图 8 张，含合院重复）"],
      note="✅ 已有户型图 15 张，经逐张核验**均为开发商正式平面图**（吉屋 7 张 + 贝壳 8 张）：中叠 A2b 153㎡ / 下叠 B1b 163㎡ / 上叠 B3b 200.6㎡ / 中叠 A 178㎡ / 上叠 A 193㎡ / 下叠 A 205.9㎡；合院 A1 238㎡、B1 230㎡、C1 255㎡、D1 266㎡、E 282.4㎡（均含一/二/三层平面与赠送面积标注）。⚠️ 存在跨渠道重复（合院 A1/B1/C1/D1 各有 2 份来源），**去重后约 9–10 套**。✅ 另补总图 1 张。⚠️ 字段冲突严重：容积率 1.1/1.8/1.98；户数 1632/1280；开发商四套口径 —— 已置 status=待核查"),

 dict(key="11-fengming", name="南沙凤鸣山", city="广州南沙", folder="住宅居住",
      arch="广州市佳业辉鸿房地产开发有限公司（佳兆业集团）",
      year="2020 年底首开", loc="南沙区黄阁新城（备案名 悦珀花园）",
      area="叠墅 103–149㎡（6 层建筑、两层一户、上/中/下三叠）",
      feat="16 栋生态叠墅 + 8 栋高层洋房；户户带入户花园，空间拓展率最高 300%；楼间距约 90m",
      cred=65, rel=85, comp=78, fresh=75,
      srcs=["吉屋 lpcp/28420", "吉屋 lpcp/37098", "搜狐焦点 2026.4.30"],
      note="✅ 户型图 4 张，经逐张核验：8栋02 约97㎡ 三房两卫+灵动空间、8栋04 约89㎡、8栋06 约107㎡、及 1 张纯平面（04 户型）。⚠️ **这 4 张均属 89–107㎡ 三房洋房产品，并非本项目 103–149㎡ 叠墅**——叠墅户型图仍缺，落库时须标明产品错配。✅ 另补总图 1 张。⚠️ 相册另有 2 张疑为图库占位素材（滨海度假小镇远景、CBD 超高层夜景），与南沙黄阁产品不符，已标注待核。容积率 2.6 偏高，属「高低配」社区（叠墅 + 高层），非纯墅区"),

 dict(key="05-zhenyuan", name="绿城·臻园", city="广州番禺", folder="住宅居住",
      arch="广州绿兴房地产开发有限公司（绿城中国华南区域全资子公司）",
      year="2026-06 亮相，2027 底交付", loc="番禺区市桥街道黄沙岛环岛路（备案名 黄沙岛花园·臻园组团）",
      area="叠拼 245–306㎡ / 联排·合院 318–600㎡",
      feat="三面环水岛居，约 500m 南向一线江景；全盘 54 席（26 联排合院 + 28 叠拼）；五层临江会所「臻境十雅」1500㎡",
      cred=72, rel=95, comp=58, fresh=90,
      srcs=["小红书《绿城臻园江景岛墅合院&叠拼户型》+《江景岛墅全户型官方测评》（11 张，经核：9 张实景 + 2 张含打码/缩略平面的海报）", "公众号《绿城臻园（1700万起）》（6 张：区位示意图 + 鸟瞰总图 + 效果图）", "搜狐焦点（黄沙岛别墅）", "腾讯新闻 2026.9.2", "东方财富·克而瑞测评", "吉屋 lpcp/29062", "贝壳 p_lczyboffo（户型图位为空）"],
      note="⚠️ **重要更正（逐张视觉核验后）：本项目实际未取得可用户型图。** 小红书两篇「全网首发」笔记共取回 11 张图，核验结果：① **9 张为会所 / 景观 / 大堂实景照**（芙蓉池、柳波廊、臻境会所、会所江景、大堂等），与户型无关；② 1 张「户型图全网首发」营销海报——其中的上叠（临江315）与合院（临江480）平面**已被发布方主动打码模糊**，不可用；③ 1 张「全户型官方测评」营销海报——底部含 5 个极小尺寸分层平面缩略图（地下一层至地上四层），单体仅约 170×260px，**仅可作线索，不能作交付图纸**。⚠️ 方法教训：**小红书笔记标题与图面内容常不一致**（标题写「全套户型图」，正文实际全是实景照），此前按标题归类导致虚报（由 0 虚报为 11 张），现按实测改正。✅ 已取得总图级素材 2 张（公众号原文鸟瞰总图：夜景 + 日景，可见江岸线、合院组团与道路关系）。✅ 海报图面目视确认：**28 叠拼 + 26 联排**，与笔记正文「全盘 54 席＝26 联排合院 + 28 叠拼」一致。公开栏目仍普遍为空：吉屋户型图位 0 张；房天下标注「暂无户型」；贝壳已收录（p_lczyboffo）但户型图位为空，其相册图实为图库占位素材（纽约中央公园天际线照）——已弃用；相册另 1 张超高层塔楼效果图亦疑占位。⚠️ 三处口径冲突（均需以阳光家缘网备案为准）：① 开发商 = 广州绿兴房地产开发有限公司（门户口径）/ 广州西溪投资发展有限公司（测评笔记口径）；② 预售证 = 穗房预(网)字第 20260156 号 / 字第 20250160 号；③ 面积 = 合院建面 318–480㎡（另一口径 318–600㎡）、叠拼建面 240–315㎡（另一口径 245–306㎡）。✅ 笔记正文补充字段（未逐条核验，供参考）：合院实用 600–1000㎡（庭院最大约 600㎡）、叠拼实用 400–500㎡（庭院 50–100㎡）；地下室层高 6.3m；合院六层立体功能分离（负一社交宴会 / 夹层家庭休闲 / 一层公共起居 / 二层家人休憩 / 三层整层主卧 / 四层空中花园），双立面风格可选「隐奢岭南·现代中式」或「逸奢岭南·南洋度假风」"),
 dict(key="02-guanyue", name="观樾·天湖", city="广州天河", folder="住宅居住",
      arch="广州观湖房地产开发有限公司（越秀地产 + 国贸地产）",
      year="2024-11 首开", loc="天河区悦景路（备案名 观樾天湖花园）",
      area="140 / 190 / 252㎡ 大平层 + 210㎡、280–330㎡ 四层合墅",
      feat="日月双湖 + 台地环湖，独梯独户板式小高层与临湖合墅并列的产品谱系",
      cred=65, rel=80, comp=78, fresh=90,
      srcs=["吉屋 news/6028333", "吉屋 info/11782078", "吉屋 loupan/1654244"],
      note="✅ 户型图 2 张，经逐张核验为 190㎡ 与 252㎡ 平面（带入户玄关、超长景观阳台、独梯入户标注）——**属大平层产品，并非 210㎡ / 280–330㎡ 四层合墅**；合墅户型图仍缺，落库时须标注产品口径。✅ 另补总图级素材 2 张（规划鸟瞰总图、带标注版鸟瞰）。⚠️ 冲突：容积率 1.91/1.6；户数 262/760；车配 1:2.15/1:15（后者明显笔误）"),

 dict(key="09-huacheng1", name="城投花城壹号院", city="广州花都", folder="住宅居住",
      arch="广州花都城市建设投资集团有限公司（花都区属国企）；项目公司 广州市花都区恒晟房地产开发有限公司（花都城投旗下）",
      year="2026-05-01 首期开盘", loc="花都区花城街融创文旅城北（备案名 恒瑞花园）",
      area="叠墅 180–220㎡ / 合院 260–320㎡ / 双拼（双院独栋）340–370㎡（小红书渠道另作 叠墅 101–230 / 联排 190–265 / 双拼 265–368㎡）",
      feat="容积率 1.02，全盘 50 幢 3–5 层、7 个分区、无高低配；整体抬地使中叠亦带独立花园；负一层私家车库 + M 层地上室",
      cred=75, rel=95, comp=50, fresh=88,
      srcs=["小红书 6 篇花城壹号院笔记（6 张，经核全部为笔记封面 / 实景 / 正文截图，均非户型图）", "大公报 2026-06-28（湾区置业）", "搜狐焦点", "网易·楼盘评测", "花城（广州日报系）", "贝壳 p_hcyhyboghv（无户型图）"],
      note="⚠️ 户型图与总图均缺。小红书 6 篇项目笔记已逐条访问并**逐张视觉核验**，正文均为「叠墅+合院+双院」卖点与总价话术，6 张图分别为：4 张笔记封面（含人物口播截图）、1 张项目门头实景、1 张**笔记正文文字截图**（此前误标为「疑图纸」，经核实为文字帖截图，非图纸）——**无一张户型图或总图**；贝壳（p_hcyhyboghv）户型图位为空、相册 5 张为图库占位素材；两条通道均告空。✅ 本轮新增字段：预售证 穗房字第 20260028 号；总价约 500–2000 万（价格有效期 2026-12-31）；代理机构 广州市盛业行房地产顾问有限公司。⚠️ 面积口径冲突：门户 180–220 / 260–320 / 340–370㎡ vs 笔记 101–230 / 190–265 / 265–368㎡。⚠️ 户数 297/289 两口径。⇒ 建议改走售楼处直取或市规资局批后公布"),

 dict(key="06-nantian", name="南天名苑（珑岸组团）", city="广州番禺", folder="住宅居住",
      arch="广州市番禺区得宝立房产实业有限公司（霍英东集团 / 广州粤发房产）",
      year="部分组团现楼", loc="番禺区洛浦街洛溪岛尖（三江汇流）",
      area="珑岸叠墅 279–437㎡（含三叠与两叠，6 层叠墅）；已获得 A 户型 270㎡ 四房（双套房）平面",
      feat="三江汇流岛尖低密大盘，容积率 1.05（叠墅组团 0.99）；2.3km 滨江绿道、800+ 原生古榕；一户一私梯、客厅挑高 6.8m",
      cred=70, rel=90, comp=82, fresh=85,
      srcs=["贝壳新房 p_ntmyaaufh（户型图 6 张）", "吉屋 lpcp/32463", "吉屋 info/11736925", "搜狐焦点 2026.9.8"],
      note="✅ 户型图 6 张，经逐张核验**均为开发商正式平面图**（图面带建筑面积、房间中文名、朝向与技术指标：360㎡ 5房2厅4卫3阳台+工人套房、A 270㎡ 四房双套房、C 140㎡、B 200㎡、E 250㎡，另有 1 张分层平面含绿色标注块）。⚠️ 其中 360㎡ 一张为**单层平面**（含电梯厅与楼梯核心筒），属叠墅单层还是大平层尚待核；其余各张按「4房/双层」标注，与珑岸叠墅 279–437㎡ 面积段吻合。⚠️ 总图仍缺（规划鸟瞰未获取），建议走市规资局批后公布"),

 dict(key="10-xinyuan", name="中海熙园", city="广州南沙", folder="住宅居住",
      arch="中海地产（央企）",
      year="2021–2022 交付现房", loc="南沙区东涌文化广场旁（庆盛枢纽板块）",
      area="叠拼 131㎡（上/中/下三叠），中叠实用约 300㎡",
      feat="中海首进南沙的叠拼作品；现代岭南中式，「五堂九巷」街巷结构；景观由 SED 新西林景观国际设计",
      cred=65, rel=85, comp=56, fresh=55,
      srcs=["吉屋 lcp/33623", "吉屋 loupan/831124", "小红书 3 篇中海熙园笔记（房源 / 装修实景 12 张，经核无户型图）"],
      note="⚠️ 户型图仍缺，但**总图级素材本轮补齐 4 张**（均经逐张核验）：其中最关键是 1 张**带「批准许可证号 20181414」的规划鸟瞰总图**——可直接作为报建口径的总平面依据；另有全景鸟瞰、组团圆鸟瞰、岭南组团鸟瞰各 1 张。小红书 12 张经核为业主直售房源实拍（1 张小区大门、1 张楼道）、复式楼梯实景 6 张、街道实景与视频封面，**无一张户型图**；且房源帖描述「102.5㎡ 大三房」属高层产品、非叠拼，仅可作氛围参考。另有 3 张高层塔楼效果图疑为图库占位素材（中海熙园以叠拼为主），已标注待核。贝壳新房未收录。⚠️ 容积率 1.27/1.5、户数 330/900、绿化率 30%/35% 均两口径；项目 2021–2022 已交付，本批「在售」状态需现场复核"),

 dict(key="07-lingnan1", name="岭南1号", city="广州白云", folder="住宅居住",
      arch="益云集团 + 龙湖龙智造（合作开发）",
      year="2026 在售", loc="白云区六片山（原白云六片山 123 地块）",
      area="临湖独栋约 500㎡（10 套）/ 叠墅约 300㎡（一栋 4 户，各自独立入户）/ 大平层 169–252㎡",
      feat="临湖独栋 + 叠墅 + 大平层三种产品并列；配套五星级凯悦酒店并由凯悦提供物业服务",
      cred=60, rel=85, comp=45, fresh=88,
      srcs=["小红书《龙湖益云岭南1号》（沙盘模型照 2 张）", "公众号「广州楼市发布」", "克而瑞榜单转述"],
      note="⚠️ 仍缺户型图与总图。本轮经小红书取得 2 张**沙盘模型照片**（经核为实体模型：临湖独栋含泳池与庭院、四层错层逐层露台），可用作**体量形态与错层关系参考**，但非图纸，已归入总图级素材。⚠️ 检索坑：关键词含「六片山」时两次误召回六片山**登山徒步帖**共 22 张，已全部剔除、未入库。✅ 笔记补出产品描述：一线滨水叠墅，四层错层流线型玻璃立面、层层露台；首层花园会客 / 中层居家起居 / 顶层空中会客厅；户户私属庭院 + 露天泳池，独立游艇码头直达湖面；另有高层湖景大平层作伴——**已由沙盘照目视印证**。⚠️ 仍仅公众号单一来源，容积率 1.7、约 330 户待核实。贝壳新房未收录（838 个广州楼盘 URL 中无白云六片山「岭南1号」，仅有荔湾「岭南V谷」为同名干扰项）"),
]

def buckets(key):
    """按文件名前缀分类：户型图 HT / 总图 ZZ / 海报 POSTER / 楼盘图 ALB"""
    d = os.path.join(BASE, IMG, key)
    files = sorted(os.listdir(d)) if os.path.isdir(d) else []
    ht = [f for f in files if "HT" in f]
    zz = [f for f in files if "ZZ" in f]
    po = [f for f in files if "POSTER" in f]
    alb = [f for f in files if f not in ht and f not in zz and f not in po]
    return ht, zz, po, alb


for p in P:
    p["score"] = round(p["cred"]*0.35 + p["rel"]*0.30 + p["comp"]*0.25 + p["fresh"]*0.10, 1)
    # 收录建议以「得分 + 是否真有户型图」双条件判定，避免高分盘无图占位
    p["ht_n"] = len(buckets(p["key"])[0])
    p["zz_n"] = len(buckets(p["key"])[1])
    p["status"] = "建议收录" if (p["score"] >= 70 and p["ht_n"] >= 1) else "待补图候选"


def pick_cover(key, files):
    """题图：优先横向中等比例的最大图"""
    best, bestv = None, -1
    for f in files:
        fp = os.path.join(BASE, IMG, key, f)
        try:
            import hashlib
            sz = os.path.getsize(fp)
        except Exception:
            continue
        v = sz
        if v > bestv:
            bestv, best = v, f
    return best


def cell(p):
    ht, zz, po, alb = buckets(p["key"])
    # 贝壳开发商正式户型图（KE-HT）优先作题图，其次总图，再次海报与楼盘图
    ht.sort(key=lambda f: (not f.startswith("KE-HT"), f))
    order = ht + zz + po + alb
    cover = pick_cover(p["key"], order)
    cov = f'{IMG}/{p["key"]}/{cover}' if cover else None
    thumbs = order
    th = "".join(
        f'<a href="{IMG}/{p["key"]}/{f}" target="_blank"><img src="{IMG}/{p["key"]}/{f}" loading="lazy"></a>'
        for f in thumbs[:8])
    badge = {"建议收录": "ok", "待补图候选": "warn"}.get(p["status"], "warn")
    if cover in ht:
        covtag = "开发商户型图" if cover.startswith("KE-HT") else "户型图"
    elif cover in zz:
        covtag = "总图 / 鸟瞰"
    elif cover in po:
        covtag = "营销海报"
    else:
        covtag = "楼盘图"
    miss = []
    if not ht:
        miss.append("无户型图")
    if not zz:
        miss.append("无总图")
    misstag = (f'<span class="miss">{" · ".join(miss)}</span>' if miss else "")
    return f'''
    <article class="card {badge}">
      <div class="cov">{f'<img src="{cov}" loading="lazy"><span class="covtag">{covtag}</span>' if cov else '<div class="nocov">无题图<br><small>该渠道未覆盖</small></div>'}</div>
      <div class="body">
        <div class="hdr">
          <h3>{html.escape(p["name"])}{misstag}</h3>
          <span class="score s{badge}">{p["score"]}</span>
        </div>
        <p class="sub">{html.escape(p["city"])} · {html.escape(p["loc"])}</p>
        <table class="kv">
          <tr><th>设计/开发</th><td>{html.escape(p["arch"])}</td></tr>
          <tr><th>年份</th><td>{html.escape(p["year"])}</td></tr>
          <tr><th>面积段</th><td>{html.escape(p["area"])}</td></tr>
          <tr><th>库内查重</th><td>新案例（未命中）</td></tr>
          <tr><th>来源</th><td>{html.escape(" · ".join(p["srcs"]))}</td></tr>
        </table>
        <p class="feat">★ {html.escape(p["feat"])}</p>
        <p class="note">{html.escape(p["note"])}</p>
        <p class="cnt">素材（逐张视觉核验）：户型图 <b>{len(ht)}</b> · 总图 <b>{len(zz)}</b> · 海报 <b>{len(po)}</b> · 楼盘图 <b>{len(alb)}</b></p>
        <div class="thumbs">{th}</div>
      </div>
    </article>'''


ok = [p for p in P if p["status"] == "建议收录"]
warn = [p for p in P if p["status"] == "待补图候选"]


def _cnt(pred):
    n = 0
    for p in P:
        d = os.path.join(BASE, IMG, p["key"])
        if os.path.isdir(d):
            n += sum(1 for f in os.listdir(d) if pred(f))
    return n


xhs_n = _cnt(lambda f: f.startswith("XHS"))
xhs_ht = _cnt(lambda f: f.startswith("XHS") and "HT" in f)
ht_n = _cnt(lambda f: "HT" in f)
zz_n = _cnt(lambda f: "ZZ" in f)
poster_n = _cnt(lambda f: "POSTER" in f)
alb_n = _cnt(lambda f: "HT" not in f and "ZZ" not in f and "POSTER" not in f and "ALB" in f)
nohuxing = len([p for p in P if p["ht_n"] == 0])

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>候选清单 · 广州在售叠墅（户型与总图）</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f6f7f9;color:#1c2024;
 font:14px/1.7 "PingFang SC","Microsoft YaHei",system-ui,sans-serif}}
.wrap{{max-width:1120px;margin:0 auto;padding:28px 20px 60px}}
h1{{font-size:23px;margin:0 0 6px}}
.lead{{color:#5b6570;font-size:13px;margin:0 0 22px}}
.stats{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px}}
.stat{{background:#fff;border:1px solid #e5e8ec;border-radius:10px;padding:10px 16px;min-width:104px}}
.stat b{{display:block;font-size:19px}}
.stat span{{color:#7b848f;font-size:12px}}
.stat span small{{font-size:11px;color:#a7aeb6}}
.stat.hot{{border-color:#f0c36d;background:#fffdf5}}
.miss{{display:inline-block;margin-left:8px;font-size:11px;font-weight:400;
 color:#9a6200;background:#fdf1dc;border-radius:20px;padding:1px 8px;vertical-align:middle}}
.tagz{{display:inline-block;font-size:11px;font-weight:400;border-radius:20px;
 padding:1px 8px;vertical-align:middle;margin-left:6px}}
.tagz.have{{color:#12794a;background:#e6f6ed}}
.tagz.lack{{color:#9a6200;background:#fdf1dc}}
h2{{font-size:16px;margin:30px 0 4px;padding-left:10px;border-left:3px solid #3d7eff}}
h2 small{{font-weight:400;color:#7b848f;font-size:12px;margin-left:8px}}
.grid{{display:grid;grid-template-columns:1fr;gap:16px;margin-top:12px}}
.card{{display:grid;grid-template-columns:260px 1fr;background:#fff;border:1px solid #e5e8ec;
 border-radius:12px;overflow:hidden}}
.card.ok{{border-left:3px solid #1a9c5b}}
.card.warn{{border-left:3px solid #d98a00}}
.cov{{position:relative;background:#eef1f4;display:flex;align-items:center;justify-content:center;min-height:190px}}
.cov img{{width:100%;height:100%;object-fit:cover;object-position:center}}
.covtag{{position:absolute;left:8px;bottom:8px;background:rgba(28,32,36,.72);color:#fff;
 font-size:11px;padding:2px 8px;border-radius:20px}}
.nocov{{color:#8b949e;text-align:center;font-size:13px}}
.body{{padding:14px 18px}}
.hdr{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}}
h3{{font-size:16px;margin:0}}
.score{{font-weight:700;font-size:15px;padding:2px 10px;border-radius:20px;white-space:nowrap}}
.sok{{background:#e6f6ed;color:#12794a}}
.swarn{{background:#fdf1dc;color:#9a6200}}
.sub{{color:#7b848f;font-size:12.5px;margin:3px 0 10px}}
.kv{{width:100%;border-collapse:collapse;font-size:12.5px;margin-bottom:9px}}
.kv th{{text-align:left;color:#7b848f;font-weight:400;width:74px;padding:2px 8px 2px 0;vertical-align:top}}
.kv td{{padding:2px 0;color:#2b3238}}
.feat{{margin:0 0 6px;font-size:13px;color:#1c2024}}
.note{{margin:0 0 8px;font-size:12.5px;color:#9a6200;background:#fffaf0;border-radius:6px;padding:6px 9px}}
.cnt{{margin:0 0 7px;font-size:12px;color:#7b848f}}
.thumbs{{display:flex;gap:6px;flex-wrap:wrap}}
.thumbs img{{width:74px;height:54px;object-fit:cover;border-radius:5px;border:1px solid #e5e8ec;cursor:zoom-in}}
footer{{margin-top:30px;color:#7b848f;font-size:12.5px;border-top:1px solid #e5e8ec;padding-top:14px}}
</style></head><body><div class="wrap">
<h1>候选清单 · 广州地区在售叠墅（户型与总图资料）</h1>
<p class="lead">批次 2026-09-15-广州叠墅 ｜ 口径：产品研究 ｜ 地域：广州全域 ｜ 产品边界：叠墅 + 合院 + 联排 ｜
 全部候选经 01 - 案例库 全库查重，<b>均为新案例</b> ｜
 <b>本批图片已全部逐张视觉核验</b>后按「户型图 / 总图 / 海报 / 楼盘图」重新分类（见文末第七节）</p>

<div class="stats">
  <div class="stat"><b>{len(P)}</b><span>候选总数</span></div>
  <div class="stat"><b>{len(ok)}</b><span>建议收录<br><small>≥70 分且已有户型图</small></span></div>
  <div class="stat"><b>{len(warn)}</b><span>待补图候选</span></div>
  <div class="stat hot"><b>{ht_n}</b><span>户型图（张）<br><small>已逐张视觉核验</small></span></div>
  <div class="stat"><b>{zz_n}</b><span>总图 / 鸟瞰（张）</span></div>
  <div class="stat"><b>{poster_n}</b><span>营销海报（张）<br><small>含打码/缩略平面</small></span></div>
  <div class="stat"><b>{nohuxing}</b><span>仍无户型图项目</span></div>
</div>

<h2>一、建议收录<small>得分 ≥ 70 且已取得户型图</small></h2>
<div class="grid">{''.join(cell(p) for p in ok)}</div>

<h2>二、待补图候选<small>得分不足 70，或尚无户型图 —— 二者缺其一即入此列</small></h2>
<div class="grid">{''.join(cell(p) for p in warn)}</div>

<h2>三、库内已有<small>与 01 - 案例库 全库查重</small></h2>
<p class="lead">经项目中文名 / 别名 / 备案名 / 开发商 + 城市三键检索，本轮候选<b>全部为新案例</b>，无库内重复。仅「保利湖心墅」经核为「保利湖光悦色」新组团，已按多源合并规则并入同一篇，不计为独立案例。</p>

<h2>四、已排除</h2>
<p class="lead">「星河余荫溪谷」（番禺南村）经核为 <b>8–11 层纯板式洋房</b>（容积率 2.09、156 户、无叠拼产品），
 不符合本批「叠墅 + 合院 + 联排」产品边界，按类型硬过滤出局。另有 1 条焦点网稿件称其含「12 栋低密叠墅」，
 与吉屋三处口径矛盾，判定为营销稿件失实，不采信。</p>

<h2>五、图源通道实测<small>本批新增：打通贝壳新房通道</small></h2>
<p class="lead">
<b>✅ 贝壳新房 PC 站（gz.fang.ke.com）—— 免登录可用</b>：sitemap 提供全库 <b>838 个</b>楼盘 URL；楼盘详情页可 GET。
其中 <code>hdic-frame</code> 图组 = <b>开发商正式户型图</b>（图面带项目名、面积、房间标注，无门户水印）；
图片 URL 尾部 <code>.690x.jpg</code> 改为 <code>.2000x.jpg</code> 即取高清。<br>
本批由此补入：<b>南天名苑 6 张</b>、<b>御溪臻山墅 8 张</b>、<b>保利湖光悦色 3 张</b>。<br>
⚠️ 该通道仍受限于：户型图专页 <code>/huxingtu/</code>、列表第 4 页起、搜索接口均<b>需登录</b>；
相册图（<code>newhouse-user-image</code>/<code>hdic-resblock</code>）存在<b>图库占位素材</b>风险（绿城·臻园即误传为纽约中央公园照），<b>不可采信为项目实景</b>。
定位楼盘靠 PID 前缀＝楼盘名拼音首字母（如 <code>p_ntmyaaufh</code>＝南天名苑）。<br>
<b>✅ 广州市规划和自然资源局批后公布</b>：S 级<b>带盖章总平面示意图</b>，PDF 经 PyMuPDF 渲染（本批 3 份）。<br>
<b>✅ 吉屋</b>：<code>/housetype/</code>＝户型图、<code>/album/</code>＝楼盘图。<br>
<b>❌ 房天下 / 搜狐焦点</b>：图片 JS 懒加载；搜索接口不按关键词返回。<b>❌ 安居客 / 贝壳移动端</b>：CAPTCHA 或需登录。
<b>❌ 百度图片</b>：<code>antiFlag=1</code> 禁爬。<b>❌ 搜狗微信</b>：结果页可 GET，但 <code>/link?url=</code> 跳转被 antispider 拦（需真实浏览器指纹）。<br>
<b>✅ 浏览器登录态（本轮已接通并实测）</b>：<br>
① <b>搜狗微信 → 微信正文「可行」</b>：真实浏览器能过 <code>/link?url=</code> 的 antispider 拦截，落到 <code>mp.weixin.qq.com</code>；正文图在 <code>#js_content img[data-src]</code>（懒加载，需滚动触发）。本次据此取回绿城·臻园区位示意图与效果图 6 张。<b>但公众号正文以效果图/样板间为主，户型图覆盖率低。</b><br>
② <b>小红书「可读但不可尽信」（本轮新打通 + 已修正）</b>：搜索页 <code>search_result?keyword=</code> 可读；笔记直连<b>必须带 <code>xsec_token</code></b>（从结果页 <code>a.cover</code> 的 <code>href</code> 取——<code>a[href^="/explore/"]</code> 是 0 尺寸 SEO 壳，取不到），<code>/explore/&lt;id&gt;</code> 裸链或失效 token 一律跳 <code>/404</code> 并报「当前笔记暂时无法浏览」。正文图就在页面 <code>img</code> 里，URL 含后缀 <code>!nd_dft_wlteh_webp_3</code>（＝详情页大图）；<b>该后缀参与签名 —— 自行替换成别的后缀、或去掉后缀，均 403</b>，必须原样带着下载，并附 <code>Referer: www.xiaohongshu.com</code>。<br>
⚠️⚠️ <b>本轮最重要的教训：小红书「取到图」≠「取到户型图」</b>。标题写「全套户型图 / 全户型首发」的笔记，正文实际可能整篇都是会所与景观实景照；即便真有户型，也可能被发布方<b>主动打码</b>，或只做成海报底部的小缩略图。本轮 10 个项目共从小红书取回 40 余张图，<b>经逐张视觉核验后，可计入「户型图」的为 0 张</b>——全部为实景照、封面、正文截图或打码海报。⇒ <b>小红书只能作为「线索发现 + 卖点字段补充」渠道，其图片必须逐张核验后才能归类，绝不可按标题计入户型图。</b><br>
⚠️ <b>踩坑（务必先做）</b>：小红书关键词搜索会大量召回<b>同名或泛主题</b>笔记——搜「岭南1号 六片山」竟召回六片山<b>登山徒步帖</b> 22 张。**必须先按「项目名」收敛候选池再入闸**，否则会往案例库里塞一堆无关风景照。<br>
③ <b>百度图片</b>浏览器渲染同样不出结果（滚动后仅 4 个 img）；<b>安居客</b> <code>?kw=</code> 搜索被重定向回首页。<br>
④ 绿城·臻园房天下 pid＝<code>2811223652</code>（经 百度结果 → <code>baidu.com/link?url=</code> → curl 跟跳取得），但该盘页面标注「暂无户型」。<br>
</p>

<h2>六、各项目户型图得手情况<small>渠道实测记录，供后续换渠道</small></h2>
<p class="lead">
<b>绿城·臻园 ✗（本轮已更正）</b>：小红书两篇「全网首发」户型笔记 → 取回 11 张，但<b>逐张核验后为 9 张实景照 + 2 张含打码 / 缩略平面的海报</b>，<b>无可用户型图</b>。此前按笔记标题计为 11 张，属误判，已改正。<br>
<b>花城壹号院 ✗</b>：小红书 6 篇项目笔记（《别墅叠墅联排》《夜探全墅盘》《花都区院墅来了》《单边墅认筹》《花城壹号院》《融创院墅开放参观》）逐条打开并逐张核验，6 张图为封面 / 门头实景 / 正文文字截图，<b>无一张户型图或总图</b>；贝壳户型图位为空 → <b>户型图与总图均缺</b>。<br>
<b>中海熙园 ✗（户型）/ ✅（总图）</b>：小红书 4 篇笔记 → 12 张房源 / 装修实景（含业主直售高层房源），无户型图；但吉屋相册中捞出 <b>4 张规划鸟瞰总图，含 1 张带「批准许可证号 20181414」者</b> → 总图口径已可支撑，户型图仍缺。<br>
<b>岭南1号 ✗</b>：小红书全站仅 1 篇相关笔记《龙湖益云岭南1号》→ 2 张沙盘模型照（可作体量参考）；贝壳未收录 → <b>户型图与总图均缺</b>。<br>
⇒ <b>结论（已修正）</b>：小红书对<b>线索发现与卖点字段补充</b>有效，但对<b>户型图本身</b>普遍无效——标题承诺与图面内容脱节、且常主动打码。真正的户型图仍在<b>贝壳新房 <code>hdic-frame</code> 图组</b>（本批 33 张中 17 张来自此）与<b>吉屋 <code>/housetype/</code></b>。总图则优先走<b>市规资局批后公布</b>与<b>项目方相册中的审批版鸟瞰</b>；售楼处直取仍是兜底手段。
</p>

<h2>七、逐张视觉核验记录<small>本轮新增环节，用于纠正按标题归类造成的虚报</small></h2>
<p class="lead">
<b>为什么加这一步</b>：此前图片全部按「来源笔记标题 / 门户栏目」归类，从未核验图面实际内容。本轮补做核验后发现<b>标签错误率极高</b>，已按实测重建分类（<code>HT</code> 户型图 / <code>ZZ</code> 总图·鸟瞰·沙盘 / <code>POSTER</code> 海报 / <code>ALB</code> 楼盘图），脚本见 <code>audit_sheet.py</code>（把图片拼成带编号的审图板，逐板读图判定）。<br>
<b>核验方式</b>：<code>audit_sheet.py</code> 生成 9 张「原判为户型图」审图板 + 13 张「原判为非户型图」反向审图板，共 22 板、99 张图，逐板目视判定。<br>
<br>
<b>✅ 确认有效的户型图（33 张，全部为开发商 / 门户正式平面图）</b>：御溪臻山墅 15（含跨渠道重复，去重约 9–10 套）· 保利湖光悦色 6（含 8B# 三层叠墅分层平面）· 南天名苑 6 · 南沙凤鸣山 4（★ 属 89–107㎡ 洋房，非叠墅）· 观樾·天湖 2（★ 属大平层，非合墅）。<br>
<b>❌ 被纠正的误判（4 处）</b>：<br>
① 绿城·臻园：11 张「开发商户型图」→ 实为 9 张实景 + 2 张打码 / 缩略海报，<b>户型图 0 张</b>；<br>
② 金茂越秀·璞樾墅：1 张「户型图」→ 实为<b>室内渲染俯视图</b>，<b>户型图 0 张</b>；<br>
③ 城投花城壹号院：1 张「疑图纸」→ 实为<b>笔记正文文字截图</b>；<br>
④ 岭南1号：2 张「笔记图」→ 实为<b>实体沙盘模型照</b>（有价值，但非图纸，已转总图级）。<br>
<b>⚠️ 疑图库占位素材（已标注待核，未计入实景）</b>：璞樾墅（超高层塔楼、P&amp;L 办公楼）、绿城·臻园（超高层塔楼）、御溪臻山墅（写字楼群夜景）、南沙凤鸣山（滨海度假小镇、CBD 超高层夜景）、中海熙园（高层塔楼 ×3）——均与项目产品形态明显不符，疑为门户相册混入的通用图库素材。<br>
<b>⇒ 固化为流程</b>：图片下载后<b>必须逐张核验图面内容再归类</b>；「按标题归类」只允许作为待核状态，不得直接计入户型图数量。
</p>

<footer>
生成时间 2026-09-15 ｜ 批次目录 <code>staging/2026-09-15-广州叠墅/</code> ｜
题图与缩略图均为本地暂存副本（<code>img/&lt;项目&gt;/</code>），点击可放大 ｜
⚠️ 本批来源以楼盘官方信息页 / 房产门户 / 专业媒体为主，属<b>产品研究口径</b>（非建成案例的建筑师署名口径）；
各项目「在售」状态具时效性，需以阳光家缘网备案为准。
</footer>
</div></body></html>'''

with open(os.path.join(BASE, "候选清单.html"), "w", encoding="utf-8") as f:
    f.write(HTML)
print("候选清单.html OK")
for p in P:
    print(f'  {p["score"]:>5}  {p["status"]:<6} {p["name"]}')
