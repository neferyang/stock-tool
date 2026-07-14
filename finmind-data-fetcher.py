#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從 FinMind API 更新 financial-data-complete.json 的歷史財務數據

設計原則：
  - 正確 API：https://api.finmindtrade.com/api/v4/data
  - FinMind 為唯一資料來源：每個年度全覆蓋（含當年），無完整資料則設為 null
  - 全部為真實數據，無推估、無佔位
  - 單位：營收/淨利/營業利益/FCF = 億元；EPS = 元；比率 = %

資料集與整合方式：
  - 損益表 TaiwanStockFinancialStatements：單季值 → 年度加總
      EPS、Revenue、IncomeAfterTaxes(稅後淨利)、OperatingIncome(營業利益)
  - 資產負債表 TaiwanStockBalanceSheet：年底餘額 → 取 Q4
      Equity(權益)、Liabilities(負債)、TotalAssets(資產總額)
  - 現金流量表 TaiwanStockCashFlowsStatement：累計值 → 取 Q4
      NetCashInflowFromOperatingActivities(營業現金流)、PropertyAndPlantAndEquipment(資本支出)

衍生指標：
  netMargin = 稅後淨利 / 營收 × 100
  operatingMargin = 營業利益 / 營收 × 100
  roe = 稅後淨利 / 年底權益 × 100
  debtRatio = 年底負債 / 年底資產 × 100
  fcf = 營業現金流 + 資本支出（資本支出為負值）
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# dotenv 為選用：本地方便，CI 用環境變數（無 dotenv 不應崩潰）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_URL = "https://api.finmindtrade.com/api/v4/data"
DATA_FILE = "financial-data-complete.json"
TIMEOUT = 25
RATE_DELAY = 0.4
OKU = 1e8  # 億元換算


class FinMindFetcher:
    def __init__(self):
        self.token = os.getenv('FINMIND_TOKEN', '')
        self.headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
        if not self.token:
            print("⚠️  未設定 FINMIND_TOKEN，資料可能受限")

    def _get(self, dataset, code, start, end):
        params = {"dataset": dataset, "data_id": code, "start_date": start, "end_date": end}
        r = requests.get(API_URL, params=params, headers=self.headers, timeout=TIMEOUT)
        r.raise_for_status()
        d = r.json()
        if d.get('status') != 200:
            raise RuntimeError(f"{dataset} status {d.get('status')}: {d.get('msg')}")
        return d.get('data', [])

    def fetch_all(self, code, start, end):
        """回傳 (損益表, 資產負債表, 現金流量表) 三組原始資料"""
        income = self._get("TaiwanStockFinancialStatements", code, start, end)
        balance = self._get("TaiwanStockBalanceSheet", code, start, end)
        cashflow = self._get("TaiwanStockCashFlowsStatement", code, start, end)
        return income, balance, cashflow

    @staticmethod
    def _group(rows):
        """rows → { year: { type: [(date, value), ...] } }"""
        g = {}
        for r in rows:
            y = r['date'][:4]
            g.setdefault(y, {}).setdefault(r['type'], []).append((r['date'], r['value']))
        return g

    def compute_annual(self, income, balance, cashflow):
        """整合三表，回傳 { '2024': {eps, revenue, ...}, ... }（僅完整年度）"""
        gi, gb, gc = self._group(income), self._group(balance), self._group(cashflow)
        years = set(gi) | set(gb) | set(gc)
        out = {}

        for y in years:
            it = gi.get(y, {})

            def isum(t):  # 損益表：單季加總
                vals = [v for _, v in it.get(t, [])]
                return sum(vals) if vals else None

            def icount(t):
                return len(it.get(t, []))

            def last(group, t):  # 取 Q4（最後日期）
                items = sorted(group.get(y, {}).get(t, []))
                return items[-1][1] if items else None

            # 至少需 4 季損益表才算完整年度
            if icount('EPS') < 4 or icount('Revenue') < 4:
                continue

            eps = isum('EPS')
            revenue = isum('Revenue')
            net_income = isum('IncomeAfterTaxes')
            op_income = isum('OperatingIncome')

            equity = last(gb, 'Equity')
            liab = last(gb, 'Liabilities')
            total_assets = last(gb, 'TotalAssets')

            ocf = last(gc, 'NetCashInflowFromOperatingActivities')
            capex = last(gc, 'PropertyAndPlantAndEquipment')

            rec = {
                'eps': round(eps, 2) if eps is not None else None,
                'revenue': round(revenue / OKU, 1) if revenue is not None else None,
                'netIncome': round(net_income / OKU, 1) if net_income is not None else None,
                'operatingIncome': round(op_income / OKU, 1) if op_income is not None else None,
                'operatingMargin': round(op_income / revenue * 100, 1) if (op_income is not None and revenue) else None,
                'netMargin': round(net_income / revenue * 100, 1) if (net_income is not None and revenue) else None,
                'roe': round(net_income / equity * 100, 1) if (net_income is not None and equity) else None,
                'debtRatio': round(liab / total_assets * 100, 1) if (liab is not None and total_assets) else None,
                'fcf': round((ocf + capex) / OKU, 1) if (ocf is not None and capex is not None) else None,
            }
            out[y] = rec
        return out


# 前端 data 條目的財務欄位（全覆蓋這些欄位）
FIN_FIELDS = ['eps', 'revenue', 'netIncome', 'operatingIncome',
              'operatingMargin', 'netMargin', 'roe', 'debtRatio', 'fcf']


def update_data_file(fetcher):
    with open(DATA_FILE, 'r', encoding='utf-8-sig') as f:
        db = json.load(f)

    stocks = db.get('stocks', {})
    codes = list(stocks.keys())
    print(f"\n開始更新 {len(codes)} 支股票（FinMind 全覆蓋）...\n")

    updated_stocks = 0
    failed = 0

    for i, code in enumerate(codes, 1):
        stock = stocks[code]
        data_arr = stock.get('data', [])
        years = [str(d.get('year')) for d in data_arr if str(d.get('year')).isdigit()]
        if not years:
            continue

        print(f"[{i}/{len(codes)}] {code} {stock.get('name','')}...", end=" ", flush=True)

        try:
            yrs = [int(y) for y in years]
            start, end = f"{min(yrs)}-01-01", f"{max(yrs)}-12-31"
            income, balance, cashflow = fetcher.fetch_all(code, start, end)
            annual = fetcher.compute_annual(income, balance, cashflow)

            now = datetime.now().isoformat()
            changed = False
            for entry in data_arr:
                yr = str(entry.get('year'))
                src = annual.get(yr)
                if src:
                    # 全覆蓋：用 FinMind 真實值取代所有財務欄位
                    for k in FIN_FIELDS:
                        entry[k] = src.get(k)
                    entry['updatedAt'] = now
                    entry['source'] = 'FinMind'
                    entry['isEstimate'] = False
                    entry['dataType'] = '真實'
                    changed = True
                else:
                    # 該年度無完整真實資料 → 全部設為 null（不留佔位）
                    for k in FIN_FIELDS:
                        entry[k] = None
                    entry['source'] = None
                    entry['dataType'] = '無資料'

            if changed:
                updated_stocks += 1
                got = [y for y in years if y in annual]
                print(f"✅ {','.join(sorted(got, reverse=True))}")
            else:
                print("－ 無真實資料")

        except Exception as e:
            failed += 1
            print(f"❌ {e}")

        time.sleep(RATE_DELAY)

    db['updatedAt'] = datetime.now().isoformat()
    db['source'] = 'FinMind API'

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"完成！更新股票: {updated_stocks}, 失敗: {failed}")
    print(f"{'='*60}")


def main():
    print("=" * 60)
    print("FinMind 財務數據更新（全覆蓋 financial-data-complete.json）")
    print("=" * 60)
    fetcher = FinMindFetcher()
    update_data_file(fetcher)


if __name__ == "__main__":
    main()
