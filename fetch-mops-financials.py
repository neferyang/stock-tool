#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
官方財報交叉驗證來源 - 改用 TWSE/TPEx OpenAPI（一般業）
作為 financial-data-complete.json（主資料源 FinMind）的備援/交叉驗證來源

背景：原本打 mops.twse.com.tw/mops/api 逐股查詢，2026年中起被反爬蟲擋下
（持續回應空值/逾時）。改用 TWSE/TPEx 官方開放資料平台的批次資料集，
同一網域本專案其他功能已長期穩定使用，且一次回傳全市場資料，效率更高。

涵蓋：上市(TWSE) + 上櫃/興櫃(TPEx)，僅「一般業」科目（ci 系列）。
金融/保險/證券期貨/金控/異業等特殊科目格式不同，暫不支援（如需要可
比照 DATASETS 的模式擴充 basi/bd/fh/ins/mim 變體）。

限制：這些資料集只回傳「每家公司最新一次申報」的單一季度，無法像
MOPS 舊版那樣指定任意歷史年度查詢——只有在年報公告季（约3-5月，
季別="4"代表全年度累計）才會抓到完整年度數據，其餘月份多半是Q1~Q3
的季度累計數字，本腳本只採用季別="4"（全年度）的資料，其餘略過。
無現金流量表資料集，fcf 一律為 null。
"""

import requests
import json
import sys
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OUTPUT_FILE = "financial-data-mops.json"
SOURCE_DB = "financial-data-complete.json"
TIMEOUT = 30
UNIT = 1e5  # 原始數值為千元，除以1e5換算成億元

# (資料集網址, income/balance)
DATASETS = [
    ("https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci", "income"),
    ("https://openapi.twse.com.tw/v1/opendata/t187ap07_L_ci", "balance"),
    ("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap06_O_ci", "income"),
    ("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap07_O_ci", "balance"),
    ("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap06_U_ci", "income"),
    ("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap07_U_ci", "balance"),
]


def fetch_json(url):
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def pick(row, *keys):
    """欄位名稱在 TWSE/TPEx、損益表/資產負債表之間不完全一致，依序嘗試候選鍵名"""
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
    return None


def load_target_codes():
    """僅用於統計涵蓋率，不限制抓取範圍（資料集本身就是全市場批次回傳）"""
    try:
        with open(SOURCE_DB, "r", encoding="utf-8-sig") as f:
            db = json.load(f)
        return set(db.get("stocks", {}).keys())
    except Exception:
        return set()


def main():
    print("=" * 60)
    print("官方財報交叉驗證來源（TWSE/TPEx OpenAPI）")
    print("=" * 60)

    income_rows = {}
    balance_rows = {}

    for url, kind in DATASETS:
        try:
            rows = fetch_json(url)
        except Exception as e:
            print(f"⚠️ {url} 抓取失敗：{e}")
            continue

        target = income_rows if kind == "income" else balance_rows
        count = 0
        for row in rows:
            code = pick(row, "公司代號", "SecuritiesCompanyCode")
            season = pick(row, "季別", "Season")
            if not code or season != "4":
                continue
            target[code] = row
            count += 1
        print(f"✅ {url.split('/')[-1]}：{len(rows)} 筆，其中全年度(季別4)資料 {count} 筆")

    codes = set(income_rows) | set(balance_rows)
    target_codes = load_target_codes()
    print(f"\n本次取得全年度資料的公司數：{len(codes)}（資料庫既有 {len(target_codes)} 檔中命中 {len(codes & target_codes)} 檔）\n")

    results = {}
    for code in codes:
        inc = income_rows.get(code)
        bal = balance_rows.get(code)

        revenue = to_float(pick(inc, "營業收入")) if inc else None
        op_income = to_float(pick(inc, "營業利益（損失）")) if inc else None
        net_income = to_float(pick(inc, "淨利（淨損）歸屬於母公司業主", "本期淨利（淨損）")) if inc else None
        eps = to_float(pick(inc, "基本每股盈餘（元）")) if inc else None
        year_roc = pick(inc or {}, "年度", "Year") or pick(bal or {}, "年度", "Year")

        equity = to_float(pick(bal, "歸屬於母公司業主之權益合計", "權益總額", "權益總計")) if bal else None
        liabilities = to_float(pick(bal, "負債總額", "負債總計")) if bal else None
        total_assets = to_float(pick(bal, "資產總額", "資產總計")) if bal else None

        if not year_roc:
            continue

        rec = {
            "year": int(year_roc) + 1911,
            "eps": round(eps, 2) if eps is not None else None,
            "revenue": round(revenue / UNIT, 1) if revenue else None,
            "netIncome": round(net_income / UNIT, 1) if net_income else None,
            "operatingIncome": round(op_income / UNIT, 1) if op_income else None,
            "operatingMargin": round(op_income / revenue * 100, 1) if (op_income is not None and revenue) else None,
            "netMargin": round(net_income / revenue * 100, 1) if (net_income is not None and revenue) else None,
            "roe": round(net_income / equity * 100, 1) if (net_income is not None and equity) else None,
            "debtRatio": round(liabilities / total_assets * 100, 1) if (liabilities is not None and total_assets) else None,
            "fcf": None,
            "updatedAt": datetime.now().isoformat(),
            "source": "TWSE/TPEx OpenAPI",
            "isEstimate": False,
            "dataType": "真實",
        }
        results[code] = {"data": [rec]}

    output = {
        "updatedAt": datetime.now().isoformat(),
        "source": "TWSE/TPEx OpenAPI（官方開放資料，一般業）",
        "stocks": results,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"完成！{len(results)} 檔公司取得全年度交叉驗證資料")
    print(f"已保存至 {OUTPUT_FILE}")

    return len(results) > 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
