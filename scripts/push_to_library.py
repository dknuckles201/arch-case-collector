# -*- coding: utf-8 -*-
"""把 staging 的广州叠墅候选清单写入资料库（专题研究 / 住宅产品研究）。

用法：
    python push_to_library.py <token> create            # 建库（写入 raw/db_created.json）
    python push_to_library.py <token> records <db_id>   # 写记录
"""
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
LIB = r"H:\Workbuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills\library"
SPACE_ID = "s6lHlWeIyV6AZpZZoj0DE0"
PARENT_ID = "bBPXWPXNh5VvPWqgYJw4sX"          # 住宅产品研究
DB_TITLE = "广州叠墅产品案例库"
VERIFY_DATE = "2026-09-15"

PY = sys.executable
SPACE_API = os.path.join(LIB, "space_api.py")
CREATE_DB = os.path.join(LIB, "database", "create_database.py")
ADD_RECORDS = os.path.join(LIB, "database", "batch_add_database_records.py")

# 产品类型（按各案例面积段/特点原文里明确出现的产品词归纳）
PROD_TYPES = {
    "01-puyueshu": ["合院", "独栋"],
    "03-huguang": ["叠墅"],
    "08-yuxi": ["叠墅", "合院"],
    "11-fengming": ["叠墅"],
    "05-zhenyuan": ["叠墅", "合院", "联排"],
    "02-guanyue": ["大平层", "合院"],
    "09-huacheng1": ["叠墅", "合院", "双拼"],
    "06-nantian": ["叠墅"],
    "10-xinyuan": ["叠墅"],
    "07-lingnan1": ["独栋", "叠墅", "大平层"],
}

SCHEMA = {
    "title": DB_TITLE,
    "space_id": SPACE_ID,
    "parent_id": PARENT_ID,
    "properties": [
        {"name": "项目名称", "config": {"text": ""}},
        {"name": "所在区域", "config": {"text": ""}},
        {"name": "板块/区位", "config": {"text": ""}},
        {"name": "产品类型", "config": {"multi_select": {"options": [
            {"text": "叠墅"}, {"text": "合院"}, {"text": "联排"},
            {"text": "双拼"}, {"text": "独栋"}, {"text": "大平层"},
        ]}}},
        {"name": "设计/开发单位", "config": {"text": ""}},
        {"name": "入市/交付节奏", "config": {"text": ""}},
        {"name": "面积段", "config": {"text": ""}},
        {"name": "产品特点", "config": {"text": ""}},
        {"name": "收录得分", "config": {"number": {"decimalPlaces": 1, "useSeparate": False}}},
        {"name": "收录状态", "config": {"select": {"options": [
            {"text": "建议收录"}, {"text": "待补图候选"},
        ]}}},
        {"name": "户型图(张)", "config": {"number": {"decimalPlaces": 0, "useSeparate": False}}},
        {"name": "总图/鸟瞰(张)", "config": {"number": {"decimalPlaces": 0, "useSeparate": False}}},
        {"name": "楼盘图(张)", "config": {"number": {"decimalPlaces": 0, "useSeparate": False}}},
        {"name": "已有可用户型图", "config": {"checkbox": False}},
        {"name": "来源通道", "config": {"text": ""}},
        {"name": "字段冲突与待核事项", "config": {"text": ""}},
        {"name": "核验日期", "config": {"date": "yyyy-mm-dd"}},
    ],
}


def run(script, token, payload=None, extra_args=()):
    """token 走 stdin 首行；payload 走第二行起的 JSON（--stdin）。"""
    stdin_text = token + "\n" + json.dumps(payload, ensure_ascii=False) if payload else token
    cmd = [PY, script, "--token-stdin", *extra_args]
    p = subprocess.run(cmd, input=stdin_text, capture_output=True, text=True, encoding="utf-8")
    return p.stdout.strip(), p.stderr.strip()


def build_records():
    cases = json.load(open(os.path.join(BASE, "raw", "cases_dump.json"), encoding="utf-8"))
    recs = []
    for c in cases:
        recs.append({
            "项目名称": {"text": c["name"]},
            "所在区域": {"text": c["city"]},
            "板块/区位": {"text": c["loc"]},
            "产品类型": {"multi_select": PROD_TYPES.get(c["key"], [])},
            "设计/开发单位": {"text": c["arch"]},
            "入市/交付节奏": {"text": c["year"]},
            "面积段": {"text": c["area"]},
            "产品特点": {"text": c["feat"]},
            "收录得分": {"number": c["score"]},
            "收录状态": {"select": c["status"]},
            "户型图(张)": {"number": c["ht"]},
            "总图/鸟瞰(张)": {"number": c["zz"]},
            "楼盘图(张)": {"number": c["alb"]},
            "已有可用户型图": {"checkbox": c["ht"] >= 1},
            "来源通道": {"text": " · ".join(c["srcs"])},
            "字段冲突与待核事项": {"text": c["note"]},
            "核验日期": {"date": VERIFY_DATE},
        })
    return recs


def main():
    token = sys.argv[1]
    mode = sys.argv[2]
    if mode == "create":
        out, err = run(CREATE_DB, token, SCHEMA, ("--stdin",))
        print(out)
        print("[stderr]", err[:400])
        try:
            data = json.loads(out)
        except Exception:
            return
        if "database_id" in data:
            json.dump(data, open(os.path.join(BASE, "raw", "db_created.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            print("\n>>> database_id =", data["database_id"])
            print(">>> space_id =", data.get("space_id"))
            print(">>> 字段数 =", data.get("property_count"))
    elif mode == "records":
        db_id = sys.argv[3]
        recs = build_records()
        print("records:", len(recs))
        out, err = run(ADD_RECORDS, token, {"database_id": db_id, "records": recs}, ("--stdin",))
        print(out[:4000])
        print("[stderr]", err[:400])


if __name__ == "__main__":
    main()
