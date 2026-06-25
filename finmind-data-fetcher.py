#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從 FinMind API 補足 financial-data-complete.json 的歷史財務數據

設計原則：
  - 正確 API：https://api.finmindtrade.com/api/v4/data
  - 只填補 data 陣列中為 null 的欄位，保留既有真實數據（不覆蓋）
  - 全部為真實數據，無推估
  - 單位：營收/淨利/營業利益 = 億元（FinMind 原始值 ÷ 1e8）；EPS = 元
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# dotenv 為選用：本地開發方便，CI 環境直接用環境變數（無 dotenv 不應崩潰）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Windows 編碼修復
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_URL = "https://api.finmindtrade.com/api/v4/data"
DATA_FILE = "financial-data-complete.json"
TIMEOUT = 20
RATE_DELAY = 0.3  # 請求間隔（秒）— 免費版 600 req/hr
OKU = 1e8         # 億元換算


class FinMindFetcher:
    def __init__(self):
        self.token = os.getenv('FINMIND_TOKEN', '')
        self.headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
        if not self.token:
            print("⚠️  未設定 FINMIND_TOKEN，部分資料集可能受限")

    def fetch_financial_statements(self, stock_code, start_date, end_date):
        """獲取財務報表（季資料，type/value 長格式）"""
        params = {
            "dataset": "TaiwanStockFinancialStatements",
            "data_id": stock_code,
            "start_date": start_date,
            "end_date": end_date,
        }
        r = requests.get(API_URL, params=params, headers=self.headers, timeout=TIMEOUT)
        r.raise_for_status()
        d = r.json()
        if d.get('status') != 200:
            raise RuntimeError(f"API status {d.get('status')}: {d.get('msg')}")
        return d.get('data', [])

    @staticmethod
    def compute_annual(rows):
        """把季資料整合成年度指標。回傳 { '2023': {eps, revenue, ...}, ... }"""
        # 依年份 → type → [(date, value)]
        by_year = {}
        for r in rows:
            year = r['date'][:4]
            by_year.setdefault(year, {}).setdefault(r['type'], []).append((r['date'], r['value']))

        result = {}
        for year, types in by_year.items():
            def vals(t):
                return [v for _, v in types.get(t, [])]

            eps_q = vals('EPS')
            revenue_q = vals('Revenue')
            net_income_q = vals('IncomeAfterTaxes')
            op_income_q = vals('OperatingIncome')

            # 只在當年有完整 4 季資料時才計入年度（避免不完整年度產生錯誤年值）
            if len(eps_q) < 4 or len(revenue_q) < 4:
                continue

            eps = round(sum(eps_q), 2)
            revenue = sum(revenue_q)          # 原始 NTD
            net_income = sum(net_income_q) if net_income_q else None
            op_income = sum(op_income_q) if op_income_q else None

            rec = {
                'eps': eps,
                'revenue': round(revenue / OKU, 1),
                'netIncome': round(net_income / OKU, 1) if net_income is not None else None,
                'operatingIncome': round(op_income / OKU, 1) if op_income is not None else None,
                'netMargin': round(net_income / revenue * 100, 1) if (net_income is not None and revenue) else None,
                'operatingMargin': round(op_income / revenue * 100, 1) if (op_income is not None and revenue) else None,
            }
            result[year] = rec
        return result


def update_data_file(fetcher):
    """讀取 financial-data-complete.json，逐檔補足 null 欄位，寫回"""
    with open(DATA_FILE, 'r', encoding='utf-8-sig') as f:
        db = json.load(f)

    stocks = db.get('stocks', {})
    codes = list(stocks.keys())
    print(f"\n開始補足 {len(codes)} 支股票的歷史財務數據...\n")

    # 補足 FinMind 可填的欄位（ROE/debtRatio/fcf 需資產負債表與現金流量表，本腳本不處理 → 保持原值）
    FILLABLE = ['eps', 'revenue', 'netIncome', 'operatingIncome', 'netMargin', 'operatingMargin']

    filled_count = 0
    updated_stocks = 0
    failed = 0

    for i, code in enumerate(codes, 1):
        stock = stocks[code]
        data_arr = stock.get('data', [])
        years_in_file = [str(d.get('year')) for d in data_arr]
        if not years_in_file:
            continue

        print(f"[{i}/{len(codes)}] {code} {stock.get('name','')}...", end=" ", flush=True)

        try:
            yrs = [int(y) for y in years_in_file if str(y).isdigit()]
            start = f"{min(yrs)}-01-01"
            end = f"{max(yrs)}-12-31"
            rows = fetcher.fetch_financial_statements(code, start, end)
            annual = fetcher.compute_annual(rows)

            stock_changed = False
            for entry in data_arr:
                yr = str(entry.get('year'))
                if yr not in annual:
                    continue
                src = annual[yr]
                entry_changed = False
                for key in FILLABLE:
                    # 只填補目前為 null/缺漏的欄位，不覆蓋既有真實值
                    if entry.get(key) is None and src.get(key) is not None:
                        entry[key] = src[key]
                        filled_count += 1
                        entry_changed = True
                if entry_changed:
                    entry['updatedAt'] = datetime.now().isoformat()
                    entry['source'] = 'FinMind'
                    entry['isEstimate'] = False
                    entry['dataType'] = '真實'
                    stock_changed = True

            if stock_changed:
                updated_stocks += 1
                print("✅ 已補足")
            else:
                print("－ 無新增")

        except Exception as e:
            failed += 1
            print(f"❌ {e}")

        time.sleep(RATE_DELAY)

    # 更新頂層元數據
    db['updatedAt'] = datetime.now().isoformat()

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"完成！更新股票: {updated_stocks}, 補足欄位: {filled_count}, 失敗: {failed}")
    print(f"{'='*60}")
    return filled_count


def main():
    print("=" * 60)
    print("FinMind 財務數據補足工具（更新 financial-data-complete.json）")
    print("=" * 60)

    fetcher = FinMindFetcher()
    update_data_file(fetcher)


if __name__ == "__main__":
    main()
