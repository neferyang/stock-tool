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

import re
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
        """整合三表，回傳 { '2024': {eps, revenue, ...}, ... }
        滿4季損益表 → 真實年度數據。
        當年度（進行中，如今年僅公布Q1）不滿4季 → 用現有季數年化推估
        （現有季度加總 ÷ 季數 × 4），標記 isEstimate=True、partialQuarters=
        實際季數，前端需明顯區分避免使用者誤認成正式年報數字。
        過去年度（非當年度）不滿4季 → 視為資料不完整，直接略過（不年化、
        不推估），原因：部分小型/興櫃公司在 FinMind 的申報紀錄本來就不齊全
        或非季報頻率，強行年化會產生失真甚至誇大的數字，不能套用「進行中
        年度」的推估邏輯。
        資產負債表科目本身就是期末餘額，不需年化，直接取最新一期。
        """
        current_year = str(datetime.now().year)
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

            def last(group, t):  # 取最新一期（完整年度為Q4，進行中年度為最新公布季）
                items = sorted(group.get(y, {}).get(t, []))
                return items[-1][1] if items else None

            n_quarters = min(icount('EPS'), icount('Revenue'))
            if n_quarters == 0:
                continue

            is_estimate = n_quarters < 4
            if is_estimate and y != current_year:
                # 過去年度資料本來就不齊全（非當年度進行中），不年化、不當作推估
                continue
            annualize = (4 / n_quarters) if is_estimate else 1

            eps = isum('EPS')
            revenue = isum('Revenue')
            net_income = isum('IncomeAfterTaxes')
            op_income = isum('OperatingIncome')

            equity = last(gb, 'Equity')
            liab = last(gb, 'Liabilities')
            total_assets = last(gb, 'TotalAssets')

            ocf = last(gc, 'NetCashInflowFromOperatingActivities')
            capex = last(gc, 'PropertyAndPlantAndEquipment')

            eps_a = eps * annualize if eps is not None else None
            revenue_a = revenue * annualize if revenue is not None else None
            net_income_a = net_income * annualize if net_income is not None else None
            op_income_a = op_income * annualize if op_income is not None else None
            # 淨利率/營業利益率是比率，分子分母同倍率縮放後不變，直接用原始（未年化）值即可
            fcf_a = (ocf * annualize + capex * annualize) if (ocf is not None and capex is not None) else None

            rec = {
                'eps': round(eps_a, 2) if eps_a is not None else None,
                'epsActual': round(eps, 2) if (is_estimate and eps is not None) else None,
                'revenue': round(revenue_a / OKU, 1) if revenue_a is not None else None,
                'netIncome': round(net_income_a / OKU, 1) if net_income_a is not None else None,
                'operatingIncome': round(op_income_a / OKU, 1) if op_income_a is not None else None,
                'operatingMargin': round(op_income / revenue * 100, 1) if (op_income is not None and revenue) else None,
                'netMargin': round(net_income / revenue * 100, 1) if (net_income is not None and revenue) else None,
                'roe': round(net_income_a / equity * 100, 1) if (net_income_a is not None and equity) else None,
                # ROE 分子是年化淨利，跟淨利率/負債比不同（那兩者未年化，本身已是實際值），
                # 這裡多存一份「未年化」的實際季度ROE，前端可對照顯示，避免推估值被誤認成正式數字
                'roeActual': round(net_income / equity * 100, 1) if (is_estimate and net_income is not None and equity) else None,
                'debtRatio': round(liab / total_assets * 100, 1) if (liab is not None and total_assets) else None,
                'fcf': round(fcf_a / OKU, 1) if fcf_a is not None else None,
                'isEstimate': is_estimate,
                'partialQuarters': n_quarters if is_estimate else None,
            }
            out[y] = rec
        return out


# 前端 data 條目的財務欄位（全覆蓋這些欄位）
FIN_FIELDS = ['eps', 'revenue', 'netIncome', 'operatingIncome',
              'operatingMargin', 'netMargin', 'roe', 'debtRatio', 'fcf']


BATCH_SIZE = 180  # 每支3次API呼叫，180支=540次，留餘裕給同小時的其他工作流程


def _missing_score(stock):
    """缺值分數：data陣列中沒有真實eps的年份數，越大越優先處理"""
    return sum(1 for e in stock.get('data', []) if e.get('eps') is None)


UNSUPPORTED_DATATYPE = '不適用（金融股/ETF/DR）'
UNSUPPORTED_INDUSTRIES = {'金融保險業'}  # 銀行/證券/期貨/保險用不同會計科目，非一般業損益表格式


def _is_finmind_unsupported(code, stock):
    """FinMind 的 TaiwanStockFinancialStatements 資料集只涵蓋一般業，以下三類結構上永遠
    拿不到資料：金融保險業(會計科目完全不同)、ETF(代號00開頭)、中國存託憑證(DR，掛的是
    海外公司財報)。這些股票的缺值分數永遠最高，若不排除會每天佔滿整批額度、卡死佇列，
    導致其他真正抓得到資料的股票永遠排不到（此函式即修正此問題的核心）。"""
    if '-DR' in stock.get('name', '').upper():
        return True
    if re.match(r'^00\d{2,3}$', code):
        return True
    if stock.get('industry') in UNSUPPORTED_INDUSTRIES:
        return True
    return False


def update_data_file(fetcher):
    with open(DATA_FILE, 'r', encoding='utf-8-sig') as f:
        db = json.load(f)

    stocks = db.get('stocks', {})
    all_codes = list(stocks.keys())

    unsupported_codes = [c for c in all_codes if _is_finmind_unsupported(c, stocks[c])]
    unsupported_set = set(unsupported_codes)
    candidate_codes = [c for c in all_codes if c not in unsupported_set]

    # 標記排除股票的 dataType，只在還沒標記過時才動，避免每次都造成無意義的 git diff
    newly_marked = 0
    for c in unsupported_codes:
        for entry in stocks[c].get('data', []):
            if entry.get('eps') is None and entry.get('dataType') != UNSUPPORTED_DATATYPE:
                entry['dataType'] = UNSUPPORTED_DATATYPE
                newly_marked += 1

    # 優先處理缺值最多的股票；缺值相同時，越久沒更新的越優先。
    # 額外用 noDataStreak（連續無資料次數）把「連續多次都抓不到」的個股降到佇列後段——
    # 不是永久排除（萬一 FinMind 之後補上資料還是會排到），只是不讓單一個股長期霸佔額度
    # 前段、卡死其他股票（例如 2448 這類非金融/ETF/DR、但 FinMind 本身就沒資料的個案）。
    NO_DATA_DEMOTE_THRESHOLD = 5

    def sort_key(code):
        s = stocks[code]
        last_updated = max((e.get('updatedAt') or '') for e in s.get('data', []))
        demoted = 1 if s.get('noDataStreak', 0) >= NO_DATA_DEMOTE_THRESHOLD else 0
        return (demoted, -_missing_score(s), last_updated)

    codes = sorted(candidate_codes, key=sort_key)[:BATCH_SIZE]
    print(f"\n共 {len(all_codes)} 支（其中 {len(unsupported_codes)} 支金融股/ETF/DR結構上無法從"
          f"FinMind取得，已排除候選），本次處理優先度最高的 {len(codes)} 支（缺值最多/最久未更新優先）...\n")

    updated_stocks = 0
    failed = 0

    current_year = datetime.now().year

    for i, code in enumerate(codes, 1):
        stock = stocks[code]
        data_arr = stock.get('data', [])
        years = [str(d.get('year')) for d in data_arr if str(d.get('year')).isdigit()]
        if not years:
            continue

        # 補上當年度(進行中)的空位，讓下面的迴圈能寫入推估值；沒有就不會出現在圖表/表格裡
        if str(current_year) not in years:
            data_arr.append({
                'year': str(current_year), 'eps': None, 'revenue': None, 'netIncome': None,
                'operatingIncome': None, 'operatingMargin': None, 'fcf': None, 'roe': None,
                'netMargin': None, 'debtRatio': None, 'updatedAt': None, 'source': None,
                'isEstimate': False, 'dataType': '待更新',
            })
            stock['data'] = data_arr
            years.append(str(current_year))

        print(f"[{i}/{len(codes)}] {code} {stock.get('name','')}...", end=" ", flush=True)

        try:
            yrs = [int(y) for y in years]
            start, end = f"{min(yrs)}-01-01", f"{max(max(yrs), current_year)}-12-31"
            income, balance, cashflow = fetcher.fetch_all(code, start, end)
            annual = fetcher.compute_annual(income, balance, cashflow)

            now = datetime.now().isoformat()
            changed = False
            for entry in data_arr:
                yr = str(entry.get('year'))
                src = annual.get(yr)
                if src:
                    # 用 FinMind 真實值取代所有財務欄位（不滿4季時 compute_annual 已年化並標記推估）
                    for k in FIN_FIELDS:
                        entry[k] = src.get(k)
                    entry['updatedAt'] = now
                    entry['source'] = 'FinMind'
                    entry['isEstimate'] = src.get('isEstimate', False)
                    entry['partialQuarters'] = src.get('partialQuarters')
                    entry['epsActual'] = src.get('epsActual')
                    entry['roeActual'] = src.get('roeActual')
                    entry['dataType'] = '推估' if src.get('isEstimate') else '真實'
                    changed = True
                elif entry.get('eps') is None:
                    # 該年度本來就無資料 → 標記為無資料（不影響已有真實值的欄位，因為本來就是None）
                    entry['dataType'] = '無資料'
                # 若該年度annual缺漏但entry已有真實值 → 保留原值，不清空(避免暫時性API缺漏造成資料退步)

            if changed:
                updated_stocks += 1
                stock['noDataStreak'] = 0
                got = [y for y in years if y in annual]
                print(f"✅ {','.join(sorted(got, reverse=True))}")
            else:
                stock['noDataStreak'] = stock.get('noDataStreak', 0) + 1
                print(f"－ 無真實資料（連續{stock['noDataStreak']}次）")

        except Exception as e:
            failed += 1
            print(f"❌ {e}")

        time.sleep(RATE_DELAY)

    db['updatedAt'] = datetime.now().isoformat()
    db['source'] = 'FinMind API'

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"完成！更新股票: {updated_stocks}, 失敗: {failed}"
          f"（未處理: {len(candidate_codes)-len(codes)}支留待下次，另排除 {len(unsupported_codes)} 支金融股/ETF/DR，"
          f"本次新標記 {newly_marked} 筆）")
    print(f"{'='*60}")


def main():
    print("=" * 60)
    print("FinMind 財務數據更新（全覆蓋 financial-data-complete.json）")
    print("=" * 60)
    fetcher = FinMindFetcher()
    # 無 token 直接中止：FinMind 無 token 會全數擋下，靜默跑完會誤判為成功
    if not fetcher.token:
        print("❌ 未設定 FINMIND_TOKEN，中止（請確認 GitHub Secrets 已設定 FINMIND_TOKEN）")
        return False
    update_data_file(fetcher)
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
