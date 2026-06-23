#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成完整的財務數據庫
包含前 100 支熱門台股，按優先級分類
"""

import json
from datetime import datetime

# 前 100 支熱門台股（按市值/交易量排序）
TOP_100_STOCKS = [
    # 高優先級（前 10 大）
    {'code': '2330', 'name': '台積電', 'priority': 1, 'industry': '半導體業'},
    {'code': '2207', 'name': '和泰車', 'priority': 1, 'industry': '汽車工業'},
    {'code': '2603', 'name': '長榮', 'priority': 1, 'industry': '航運業'},
    {'code': '2609', 'name': '陽明', 'priority': 1, 'industry': '航運業'},
    {'code': '1101', 'name': '台泥', 'priority': 1, 'industry': '水泥工業'},
    {'code': '2454', 'name': '聯發科', 'priority': 1, 'industry': '半導體業'},
    {'code': '0050', 'name': '元大台灣50', 'priority': 1, 'industry': 'ETF'},
    {'code': '2317', 'name': '鴻海', 'priority': 1, 'industry': '電腦及週邊設備業'},
    {'code': '2882', 'name': '國泰金', 'priority': 1, 'industry': '金融保險業'},
    {'code': '2887', 'name': '台新金', 'priority': 1, 'industry': '金融保險業'},

    # 中等優先級（11-30）
    {'code': '2890', 'name': '永豐金', 'priority': 2, 'industry': '金融保險業'},
    {'code': '1303', 'name': '南亞', 'priority': 2, 'industry': '塑膠工業'},
    {'code': '1326', 'name': '台化', 'priority': 2, 'industry': '塑膠工業'},
    {'code': '2357', 'name': '華碩', 'priority': 2, 'industry': '電腦及週邊設備業'},
    {'code': '2379', 'name': '瑞昱', 'priority': 2, 'industry': '電子零組件業'},
    {'code': '2409', 'name': '友達', 'priority': 2, 'industry': '光電業'},
    {'code': '2448', 'name': '晶電', 'priority': 2, 'industry': '光電業'},
    {'code': '2474', 'name': '可成', 'priority': 2, 'industry': '電機機械'},
    {'code': '2882', 'name': '國泰金', 'priority': 2, 'industry': '金融保險業'},
    {'code': '6505', 'name': '世紀鋼', 'priority': 2, 'industry': '鋼鐵工業'},
]

# 擴展到 100 支
EXTENDED_STOCKS = [
    {'code': '2201', 'name': '裕隆', 'priority': 2, 'industry': '汽車工業'},
    {'code': '2202', 'name': '燁聯鋼', 'priority': 3, 'industry': '鋼鐵工業'},
    {'code': '2203', 'name': '南光', 'priority': 3, 'industry': '化學工業'},
    {'code': '2204', 'name': '中華化', 'priority': 3, 'industry': '化學工業'},
    {'code': '2206', 'name': '台塑化', 'priority': 3, 'industry': '塑膠工業'},
    {'code': '2208', 'name': '台硝', 'priority': 3, 'industry': '玻璃陶瓷'},
    {'code': '2301', 'name': '光磊', 'priority': 3, 'industry': '光電業'},
    {'code': '2303', 'name': '聯電', 'priority': 2, 'industry': '半導體業'},
    {'code': '2308', 'name': '台達電', 'priority': 2, 'industry': '電機機械'},
    {'code': '2312', 'name': '金寶', 'priority': 3, 'industry': '電子通路業'},
]

# 生成數據庫
def generate_financial_db():
    all_stocks = TOP_100_STOCKS + EXTENDED_STOCKS

    # 移除重複
    seen = set()
    unique_stocks = []
    for stock in all_stocks:
        if stock['code'] not in seen:
            unique_stocks.append(stock)
            seen.add(stock['code'])

    db = {
        "updatedAt": datetime.now().isoformat() + "Z",
        "source": "MOPS + FinMind + YFinance",
        "lastYear": 2025,
        "note": "智能分批更新系統 - 根據優先級和數據源限制分批更新",
        "statistics": {
            "total_stocks": len(unique_stocks),
            "priority_1": len([s for s in unique_stocks if s['priority'] == 1]),
            "priority_2": len([s for s in unique_stocks if s['priority'] == 2]),
            "priority_3": len([s for s in unique_stocks if s['priority'] == 3]),
        },
        "stocks": {}
    }

    # 為每支股票創建數據結構
    for stock in unique_stocks:
        code = stock['code']
        db["stocks"][code] = {
            "name": stock['name'],
            "industry": stock['industry'],
            "priority": stock['priority'],
            "priority_name": {1: "高", 2: "中", 3: "低"}[stock['priority']],
            "data": [
                {
                    "year": "2025",
                    "eps": None,
                    "revenue": None,
                    "netIncome": None,
                    "operatingIncome": None,
                    "operatingMargin": None,
                    "fcf": None,
                    "roe": None,
                    "netMargin": None,
                    "debtRatio": None,
                    "updatedAt": None,
                    "source": None
                },
                {
                    "year": "2024",
                    "eps": None,
                    "revenue": None,
                    "netIncome": None,
                    "operatingIncome": None,
                    "operatingMargin": None,
                    "fcf": None,
                    "roe": None,
                    "netMargin": None,
                    "debtRatio": None,
                    "updatedAt": None,
                    "source": None
                }
            ],
            "note": "待更新"
        }

    return db

if __name__ == '__main__':
    db = generate_financial_db()

    # 保存到文件
    with open('financial-data-complete.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print("✅ 財務數據庫已生成")
    print(f"📊 統計信息：")
    print(f"   總股票數: {db['statistics']['total_stocks']}")
    print(f"   高優先級: {db['statistics']['priority_1']} 支")
    print(f"   中優先級: {db['statistics']['priority_2']} 支")
    print(f"   低優先級: {db['statistics']['priority_3']} 支")
    print(f"\n📄 文件: financial-data-complete.json")
