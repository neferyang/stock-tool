#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自動擴充財報資料庫 - 依市值排名(上市+上櫃+興櫃全市場)逐步補齊
每次執行新增市值最高的 BATCH_SIZE 支「尚未收錄」的股票，並用 FinMind 抓真實數據填入。
全市場涵蓋完畢後自動切換成常態模式：改呼叫 finmind-data-fetcher.py 的既有邏輯，
刷新資料庫裡缺值最多/最久未更新的既有股票（不再是一次性任務，變成持續維護）。
"""

import requests
import json
import time
import sys
import os
import importlib.util
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATA_FILE = "financial-data-complete.json"
BATCH_SIZE = 100
UA = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 20

# 產業別代碼 -> 官方33種產業名稱對照(不完整的用「其他業」保底，非即時消費欄位，影響有限)
INDUSTRY_NAME = {
    "01": "水泥工業", "02": "食品工業", "03": "塑膠工業", "04": "紡織纖維", "05": "電機機械",
    "06": "電器電纜", "08": "玻璃陶瓷", "09": "造紙工業", "10": "鋼鐵工業", "11": "橡膠工業",
    "12": "汽車工業", "14": "建材營造", "15": "航運業", "16": "觀光餐旅", "17": "金融保險業",
    "18": "貿易百貨業", "19": "綜合", "20": "其他業", "21": "化學工業", "22": "生技醫療業",
    "23": "油電燃氣業", "24": "半導體業", "25": "電腦及週邊設備業", "26": "光電業",
    "27": "通信網路業", "28": "電子零組件業", "29": "電子通路業", "30": "資訊服務業",
    "31": "其他電子業", "32": "文化創意業", "33": "農業科技業", "34": "電子商務",
    "35": "綠能環保", "36": "數位雲端", "37": "運動休閒", "80": "管理股票",
}


def fetch_json(url):
    # TPEx(tpex.org.tw)憑證缺 Subject Key Identifier，屬官方已知瑕疵，非安全疑慮，關閉嚴格驗證避免握手失敗
    verify = "tpex.org.tw" not in url
    r = requests.get(url, headers=UA, timeout=TIMEOUT, verify=verify)
    r.raise_for_status()
    return r.json()


def build_universe():
    """回傳 {code: {name, industry, market_cap}}，涵蓋上市+上櫃+興櫃"""
    universe = {}

    # 上市
    twse_comp = fetch_json("https://openapi.twse.com.tw/v1/opendata/t187ap03_L")
    twse_price = fetch_json("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL")
    price_map = {p["Code"]: p.get("ClosingPrice") for p in twse_price}
    for c in twse_comp:
        code = c["公司代號"]
        try:
            price = float(price_map.get(code) or 0)
            shares = float(c["已發行普通股數或TDR原股發行股數"])
            if price <= 0 or shares <= 0:
                continue
            universe[code] = {
                "name": c["公司簡稱"],
                "industry": INDUSTRY_NAME.get(c["產業別"], "其他業"),
                "market_cap": price * shares,
            }
        except (ValueError, KeyError, TypeError):
            continue

    # 上櫃
    tpex_comp = fetch_json("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O")
    tpex_price = fetch_json("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes")
    tpex_price_map = {p["SecuritiesCompanyCode"]: p.get("Close") for p in tpex_price}
    for c in tpex_comp:
        code = c["SecuritiesCompanyCode"]
        if code in universe:
            continue
        try:
            price = float(tpex_price_map.get(code) or 0)
            shares = float(c["IssueShares"])
            if price <= 0 or shares <= 0:
                continue
            universe[code] = {
                "name": c["CompanyAbbreviation"],
                "industry": INDUSTRY_NAME.get(c["SecuritiesIndustryCode"], "其他業"),
                "market_cap": price * shares,
            }
        except (ValueError, KeyError, TypeError):
            continue

    # 興櫃(無標準已發行股數欄位可靠取得，且流動性/資料品質較差 -> 只用最新成交價排序權重打折，仍可用)
    try:
        em_comp = fetch_json("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_R")
        em_price = fetch_json("https://www.tpex.org.tw/openapi/v1/tpex_esb_latest_statistics")
        em_price_map = {p["SecuritiesCompanyCode"]: p.get("LatestPrice") for p in em_price}
        for c in em_comp:
            code = c["SecuritiesCompanyCode"]
            if code in universe:
                continue
            try:
                price = float(em_price_map.get(code) or 0)
                if price <= 0:
                    continue
                # 興櫃無公開已發行股數欄位，用價格本身排序(市值排名優先度自然最低，符合股票流動性小的現實)
                universe[code] = {
                    "name": c["CompanyAbbreviation"],
                    "industry": INDUSTRY_NAME.get(c["SecuritiesIndustryCode"], "其他業"),
                    "market_cap": price * 1_000_000,  # 無股數資料，給予固定低權重，確保排在上市櫃股票之後
                }
            except (ValueError, KeyError, TypeError):
                continue
    except Exception as e:
        print(f"興櫃資料抓取失敗(略過): {e}")

    return universe


def main():
    print("=" * 60)
    print("每日自動擴充財報資料庫")
    print("=" * 60)

    with open(DATA_FILE, "r", encoding="utf-8-sig") as f:
        db = json.load(f)
    existing = set(db["stocks"].keys())
    print(f"目前已收錄: {len(existing)} 支")

    universe = build_universe()
    print(f"全市場(上市+上櫃+興櫃)共 {len(universe)} 支")

    candidates = [(c, v) for c, v in universe.items() if c not in existing]
    candidates.sort(key=lambda x: -x[1]["market_cap"])

    if not candidates:
        print("✅ 全市場已完整涵蓋，無新股票可擴充，改為刷新既有資料（缺值最多/最久未更新優先）")
        spec = importlib.util.spec_from_file_location("fm", os.path.join(os.path.dirname(__file__) or ".", "finmind-data-fetcher.py"))
        fm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fm)
        fetcher = fm.FinMindFetcher()
        if not fetcher.token:
            print("❌ 未設定 FINMIND_TOKEN，中止（請確認 GitHub Secrets 已設定 FINMIND_TOKEN）")
            return False
        fm.update_data_file(fetcher)
        return True

    batch = candidates[:BATCH_SIZE]
    print(f"本次新增 {len(batch)} 支（剩餘可擴充 {len(candidates)} 支）")

    def blank_year(y):
        return {"year": str(y), "eps": None, "revenue": None, "netIncome": None, "operatingIncome": None,
                "operatingMargin": None, "fcf": None, "roe": None, "netMargin": None, "debtRatio": None,
                "updatedAt": None, "source": None, "isEstimate": False, "dataType": "待更新"}

    for code, info in batch:
        db["stocks"][code] = {
            "name": info["name"],
            "industry": info["industry"],
            "priority": 3,
            "priority_name": "一般",
            "data": [blank_year(y) for y in (2025, 2024, 2023, 2022, 2021)],
        }

    # 匯入 finmind-data-fetcher.py 的抓取邏輯，只對新增的這批打 API
    spec = importlib.util.spec_from_file_location("fm", os.path.join(os.path.dirname(__file__) or ".", "finmind-data-fetcher.py"))
    fm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fm)
    fetcher = fm.FinMindFetcher()

    # 無 token 直接中止：避免靜默跑完卻一支都沒抓到，還把空骨架寫進資料庫
    if not fetcher.token:
        print("❌ 未設定 FINMIND_TOKEN，中止（請確認 GitHub Secrets 已設定 FINMIND_TOKEN）")
        return False

    success, nodata, failed = 0, 0, 0
    for i, (code, info) in enumerate(batch, 1):
        entry = db["stocks"][code]
        years = [str(d["year"]) for d in entry["data"]]
        print(f"[{i}/{len(batch)}] {code} {info['name']}...", end=" ", flush=True)
        try:
            income, balance, cashflow = fetcher.fetch_all(code, f"{min(int(y) for y in years)}-01-01", f"{max(int(y) for y in years)}-12-31")
            annual = fetcher.compute_annual(income, balance, cashflow)
            changed = False
            for e in entry["data"]:
                yr = str(e["year"])
                if yr in annual:
                    for k, v in annual[yr].items():
                        e[k] = v
                    e["updatedAt"] = datetime.now().isoformat()
                    e["source"] = "FinMind"
                    e["dataType"] = "真實"
                    changed = True
                else:
                    e["dataType"] = "無資料"
            if changed:
                success += 1
                print("OK")
            else:
                nodata += 1
                print("無資料")
        except Exception as ex:
            failed += 1
            # 抓取失敗(API錯誤/額度)不留空骨架污染資料庫，下次執行時重新納入候選
            db["stocks"].pop(code, None)
            print(f"錯誤: {ex}")
        time.sleep(0.2)

    if success == 0 and failed > 0:
        print(f"\n❌ {failed} 支全數抓取失敗，未寫入任何資料（可能為 API 額度或 token 問題）")
        return False

    db["updatedAt"] = datetime.now().isoformat()
    total = len(db["stocks"])
    p1 = sum(1 for s in db["stocks"].values() if s.get("priority") == 1)
    p2 = sum(1 for s in db["stocks"].values() if s.get("priority") == 2)
    p3 = sum(1 for s in db["stocks"].values() if s.get("priority") == 3)
    db["statistics"] = {"total_stocks": total, "priority_1": p1, "priority_2": p2, "priority_3": p3}

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"\n完成！新增成功:{success} 無真實資料:{nodata} 失敗:{failed}")
    print(f"資料庫總計: {total} 支（剩餘待擴充: {len(candidates) - len(batch)} 支）")
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
