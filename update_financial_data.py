#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stock Financial Data Auto Update Script (v1.0)
從 FinMind API 獲取真實財務數據，生成 JavaScript 常數

使用方法:
    python update_financial_data.py

輸出: financial_db_output.js (可直接複製到 index.html)
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# ==================== 配置 ====================

# 30 支股票代碼清單
STOCKS = [
    # 電子科技（10支）
    "2330",  # 台積電
    "2454",  # 聯發科
    "2357",  # 華碩
    "3231",  # 緯創
    "3533",  # 嘉澤
    "3019",  # 亞光
    "3034",  # 聯詠
    "2303",  # 聯電
    "2498",  # HTC
    "2382",  # 廣達

    # 金融保險（2支）
    "2887",  # 台新金
    "2890",  # 永豐金

    # 汽車工業（1支）
    "2207",  # 和泰車

    # 航運業（2支）
    "2603",  # 長榮
    "2609",  # 陽明

    # 傳統產業（3支）
    "1101",  # 台泥
    "2002",  # 中鋼
    "6244",  # 茂迪

    # 食品工業（1支）
    "1210",  # 大成

    # 化學工業（3支）
    "1301",  # 台塑
    "1402",  # 遠東新世紀
    "1303",  # 南亞塑膠

    # 紡織纖維（1支）
    "1477",  # 聚陽

    # 電腦製造（1支）
    "2912",  # 統一超

    # 面板製造（1支）
    "2409",  # 友達

    # 通訊業（1支）
    "2412",  # 中華電信

    # 電子零組件（1支）
    "2325",  # 日月光

    # ETF（1支）
    "0050",  # 台灣50 ETF
]

# FinMind API 配置
FINMIND_API_BASE = "https://api.finmind.com.tw/v1/data"
FINMIND_DATASET = "TaiwanStockFinancialStatements"

# 目標年份（2021-2025）
TARGET_YEARS = [2021, 2022, 2023, 2024, 2025]

# ==================== 工具函數 ====================

def fetch_financial_data(stock_code: str, retry: int = 3) -> Optional[Dict]:
    """
    從 FinMind API 獲取單支股票的財務數據

    Args:
        stock_code: 股票代碼（如 "2330"）
        retry: 重試次數

    Returns:
        財務數據字典，失敗返回 None
    """
    url = FINMIND_API_BASE
    params = {
        "dataset": FINMIND_DATASET,
        "data_id": stock_code
    }

    for attempt in range(retry):
        try:
            print(f"  [正在獲取] {stock_code}... (嘗試 {attempt+1}/{retry})")
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 200 and data.get("data"):
                    print(f"  ✓ {stock_code} 成功獲取 {len(data['data'])} 筆數據")
                    return data
                else:
                    print(f"  ✗ {stock_code} API 返回空數據")
                    return None
            else:
                print(f"  ✗ {stock_code} HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"  ✗ {stock_code} 超時 (嘗試 {attempt+1}/{retry})")
        except Exception as e:
            print(f"  ✗ {stock_code} 錯誤: {str(e)}")

        # 重試延遲
        if attempt < retry - 1:
            time.sleep(2)

    return None


def parse_financial_data(api_data: Dict, stock_code: str) -> Optional[Dict]:
    """
    解析 FinMind API 返回的數據，提取目標字段

    Returns:
        {
            "2025": {"eps": 31.2, "revenue": 924, ...},
            "2024": {...},
            ...
        }
    """
    if not api_data or not api_data.get("data"):
        return None

    result = {}

    # API 數據格式: [{"year": 2025, "season": 4, "eps": 31.2, ...}, ...]
    # 我們需要提取每年度的最新數據（通常是 season=4 的年報）

    for record in api_data["data"]:
        year = record.get("year")
        season = record.get("season", 4)

        # 只取年報數據（season=4）或者是該年最新的數據
        if year not in TARGET_YEARS:
            continue

        year_key = str(year)

        # 如果已有該年數據，比較 season 決定是否覆蓋
        if year_key in result:
            if season <= result[year_key].get("season", 0):
                continue

        # 提取字段
        try:
            result[year_key] = {
                "year": year_key,
                "eps": float(record.get("eps", 0)) or 0,
                "revenue": float(record.get("revenue", 0)) / 1000 or 0,  # 轉換為十億
                "netIncome": float(record.get("net_income", 0)) / 1000 or 0,
                "operatingIncome": float(record.get("operating_income", 0)) / 1000 or 0,
                "operatingMargin": float(record.get("operating_margin", 0)) or 0,
                "fcf": float(record.get("fcf", 0)) / 1000 or 0,
                "roe": float(record.get("roe", 0)) or 0,
                "netMargin": float(record.get("net_margin", 0)) or 0,
                "debtRatio": float(record.get("debt_ratio", 0)) or 0,
                "season": season
            }

            # 移除 season 字段（最終輸出不需要）
            del result[year_key]["season"]

        except (ValueError, TypeError) as e:
            print(f"    ⚠ {stock_code}/{year_key} 解析失敗: {e}")
            continue

    # 檢查是否有足夠的年份數據
    if len(result) < 2:
        print(f"  ⚠ {stock_code} 數據不足 (只有 {len(result)} 年)")
        return result if result else None

    return result


def get_stock_name(stock_code: str) -> str:
    """
    從 API 或本地映射獲取股票名稱
    """
    # 本地名稱映射（作為備用）
    name_map = {
        "2330": "台積電",
        "2454": "聯發科",
        "2357": "華碩",
        "3231": "緯創",
        "3533": "嘉澤",
        "3019": "亞光",
        "3034": "聯詠",
        "2303": "聯電",
        "2498": "HTC",
        "2382": "廣達",
        "2887": "台新金",
        "2890": "永豐金",
        "2207": "和泰車",
        "2603": "長榮",
        "2609": "陽明",
        "1101": "台泥",
        "2002": "中鋼",
        "6244": "茂迪",
        "1210": "大成",
        "1301": "台塑",
        "1402": "遠東新世紀",
        "1303": "南亞塑膠",
        "1477": "聚陽",
        "2912": "統一超",
        "2409": "友達",
        "2412": "中華電信",
        "2325": "日月光",
        "0050": "台灣50 ETF",
    }

    return name_map.get(stock_code, f"未知{stock_code}")


def build_financial_db(all_data: Dict) -> Dict:
    """
    構建最終的 FINANCIAL_DB 結構

    返回格式：
    {
        "2330": {
            "name": "台積電",
            "data": [
                {"year": "2025", "eps": 31.2, ...},
                {"year": "2024", "eps": 24.6, ...},
                ...
            ]
        },
        ...
    }
    """
    db = {}

    for stock_code, yearly_data in all_data.items():
        if not yearly_data:
            continue

        # 按年份倒序排列（新到舊）
        sorted_years = sorted(yearly_data.keys(), reverse=True)
        data_array = [yearly_data[year] for year in sorted_years]

        db[stock_code] = {
            "name": get_stock_name(stock_code),
            "data": data_array
        }

    return db


def generate_js_output(db: Dict) -> str:
    """
    生成 JavaScript 代碼，可直接粘貼到 index.html
    """
    js_code = """// ========================================
// 自動生成的財務數據庫 (Real-time API)
// 更新時間: {timestamp}
// 數據來源: FinMind API
// ========================================

const FINANCIAL_DB = {json_data};
""".format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        json_data=json.dumps(db, ensure_ascii=False, indent=2)
    )

    return js_code


def main():
    """主程序"""
    print("\n" + "="*60)
    print("📊 股票財務數據自動更新腳本 v1.0")
    print("="*60)
    print(f"目標股票數: {len(STOCKS)}")
    print(f"目標年份: {TARGET_YEARS}")
    print(f"數據來源: FinMind API")
    print("="*60 + "\n")

    all_data = {}
    success_count = 0
    failed_stocks = []

    # 逐支股票獲取數據
    for i, stock_code in enumerate(STOCKS, 1):
        print(f"\n[{i}/{len(STOCKS)}] 處理 {stock_code}...")

        # 獲取 API 數據
        api_data = fetch_financial_data(stock_code)

        if not api_data:
            print(f"  ✗ {stock_code} 失敗（跳過）")
            failed_stocks.append(stock_code)
            continue

        # 解析數據
        parsed_data = parse_financial_data(api_data, stock_code)

        if parsed_data:
            all_data[stock_code] = parsed_data
            success_count += 1
            print(f"  ✓ {stock_code} 成功 ({len(parsed_data)} 年份)")
        else:
            failed_stocks.append(stock_code)
            print(f"  ✗ {stock_code} 解析失敗")

        # API 請求延遲（避免被限流）
        time.sleep(1)

    print("\n" + "="*60)
    print(f"✓ 成功: {success_count}/{len(STOCKS)}")
    if failed_stocks:
        print(f"✗ 失敗: {', '.join(failed_stocks)}")
    print("="*60 + "\n")

    if success_count == 0:
        print("❌ 未獲取任何數據，終止")
        return

    # 構建最終數據庫
    print("正在構建 FINANCIAL_DB...")
    db = build_financial_db(all_data)
    print(f"✓ 數據庫已構建 ({len(db)} 支股票)")

    # 生成 JavaScript 輸出
    print("正在生成 JavaScript 代碼...")
    js_output = generate_js_output(db)

    # 保存到文件
    output_file = "financial_db_output.js"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(js_output)

    print(f"✓ 已保存到 {output_file}")

    # 同時保存 JSON 版本（用於驗證）
    json_file = "financial_db_output.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"✓ JSON 版本已保存到 {json_file}")

    # 統計信息
    print("\n" + "="*60)
    print("📈 數據統計")
    print("="*60)

    total_records = sum(len(data) for data in all_data.values())
    print(f"總記錄數: {total_records}")
    print(f"平均每支股票: {total_records / len(db):.1f} 年份")

    # 示例數據
    if db:
        first_stock = list(db.keys())[0]
        print(f"\n【示例】{first_stock} ({db[first_stock]['name']})")
        for record in db[first_stock]['data'][:2]:
            print(f"  {record['year']}: EPS={record['eps']}, ROE={record['roe']}%")

    print("\n✅ 更新完成！\n")
    print(f"📋 下一步: 將 {output_file} 的內容複製到 index.html")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ 用戶中斷")
    except Exception as e:
        print(f"\n\n❌ 致命錯誤: {e}")
        import traceback
        traceback.print_exc()
