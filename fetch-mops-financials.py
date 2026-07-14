#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOPS（公開資訊觀測站）爬蟲 - 抓取真實年度財報數據
作為 financial-data-complete.json（主資料源 FinMind）的備援/交叉驗證來源

真實 API（實測確認，2026-07-14）：
  POST https://mops.twse.com.tw/mops/api/{t164sb03|t164sb04|t164sb05}
  body: {"companyId":"2330","dataType":"2","year":"114","season":"4","subsidiaryCompanyId":""}
  - t164sb03 = 資產負債表, t164sb04 = 綜合損益表, t164sb05 = 現金流量表
  - year 為民國年字串；season="4" 為第四季累計（等同全年度）
輸出：financial-data-mops.json，結構與 financial-data-complete.json 一致
"""

import requests
import json
import time
import sys
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_BASE = "https://mops.twse.com.tw/mops/api"
OUTPUT_FILE = "financial-data-mops.json"
SOURCE_DB = "financial-data-complete.json"
TIMEOUT = 15
RATE_DELAY = 1.0

# 若讀不到 SOURCE_DB，退回這份原始清單
FALLBACK_STOCKS = ["2207", "3030", "2330", "1101", "2603", "2201"]


class MOPSCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
        })

    def _fetch_report(self, dataset, company_id, year, season="4"):
        """呼叫單一報表 API，回傳 reportList（列表的列表）或 None"""
        try:
            body = {
                "companyId": company_id,
                "dataType": "2",
                "year": year,
                "season": season,
                "subsidiaryCompanyId": "",
            }
            r = self.session.post(f"{API_BASE}/{dataset}", json=body, timeout=TIMEOUT)
            r.raise_for_status()
            try:
                d = r.json()
            except ValueError:
                print(f"    ✗ {dataset} 非JSON回應 status={r.status_code} body前200字={r.text[:200]!r}")
                return None
            if d.get("code") == 200 and d.get("result"):
                return d["result"].get("reportList", [])
            return None
        except Exception as e:
            print(f"    ✗ {dataset} 請求失敗: {e}")
            return None

    @staticmethod
    def _find(rows, *labels):
        """依標籤精確比對(去除縮排空白)取值，支援多個候選標籤(一般業/金融業科目不同)"""
        if not rows:
            return None
        for label in labels:
            for row in rows:
                if len(row) > 1 and row[0].strip() == label and row[1].strip() not in ("", "　"):
                    try:
                        return float(row[1].replace(",", ""))
                    except ValueError:
                        continue
        return None

    def fetch_annual(self, company_id, year):
        """
        抓取單一股票、單一民國年度的年度財報（三表）
        回傳 dict 或 None（三表皆無資料時）
        """
        income = self._fetch_report("t164sb04", company_id, year)
        time.sleep(0.3)
        balance = self._fetch_report("t164sb03", company_id, year)
        time.sleep(0.3)
        cashflow = self._fetch_report("t164sb05", company_id, year)

        if not income and not balance and not cashflow:
            return None

        # 一般業/保險業/金控業科目名稱不同，都嘗試
        revenue = self._find(income, "營業收入合計", "收入合計", "淨收益")
        op_income = self._find(income, "營業利益（損失）")
        net_income = self._find(income, "本期淨利（淨損）", "本期稅後淨利（淨損）")
        eps = self._find(income, "基本每股盈餘")

        equity = self._find(balance, "權益總額", "權益總計")
        liabilities = self._find(balance, "負債總額", "負債總計")
        total_assets = self._find(balance, "資產總額", "資產總計")

        ocf = self._find(cashflow, "營業活動之淨現金流入（流出）")
        capex = self._find(cashflow, "取得不動產、廠房及設備")

        OKU = 1e5  # MOPS 數值單位為千元，千元 -> 億元 除以 1e5
        return {
            "eps": round(eps, 2) if eps is not None else None,
            "revenue": round(revenue / OKU, 1) if revenue is not None else None,
            "netIncome": round(net_income / OKU, 1) if net_income is not None else None,
            "operatingIncome": round(op_income / OKU, 1) if op_income is not None else None,
            "operatingMargin": round(op_income / revenue * 100, 1) if (op_income is not None and revenue) else None,
            "netMargin": round(net_income / revenue * 100, 1) if (net_income is not None and revenue) else None,
            "roe": round(net_income / equity * 100, 1) if (net_income is not None and equity) else None,
            "debtRatio": round(liabilities / total_assets * 100, 1) if (liabilities is not None and total_assets) else None,
            "fcf": round((ocf + capex) / OKU, 1) if (ocf is not None and capex is not None) else None,
        }


def load_target_stocks():
    """優先從 financial-data-complete.json 取得完整股票清單，取不到則退回內建清單"""
    try:
        with open(SOURCE_DB, "r", encoding="utf-8-sig") as f:
            db = json.load(f)
        codes = list(db.get("stocks", {}).keys())
        if codes:
            return codes
    except Exception:
        pass
    return FALLBACK_STOCKS


def main():
    print("=" * 60)
    print("MOPS 財報數據爬蟲 - 備援/交叉驗證來源")
    print("=" * 60)

    stock_codes = load_target_stocks()
    roc_year_now = datetime.now().year - 1911
    # 抓最近兩個「應已公告」的年度（去年、前年），避免今年年報尚未公告
    years = [str(roc_year_now - 1), str(roc_year_now - 2)]

    print(f"\n目標股票數: {len(stock_codes)}，年度: {years}\n")

    crawler = MOPSCrawler()
    results = {}
    success = 0
    failed = 0

    for i, code in enumerate(stock_codes, 1):
        print(f"[{i}/{len(stock_codes)}] {code} ...", end=" ", flush=True)
        data_list = []
        for y in years:
            rec = crawler.fetch_annual(code, y)
            if rec:
                rec["year"] = int(y) + 1911
                rec["updatedAt"] = datetime.now().isoformat()
                rec["source"] = "MOPS"
                rec["isEstimate"] = False
                rec["dataType"] = "真實"
                data_list.append(rec)
            time.sleep(RATE_DELAY)

        if data_list:
            data_list.sort(key=lambda r: r["year"], reverse=True)
            results[code] = {"data": data_list}
            success += 1
            print(f"✅ {[d['year'] for d in data_list]}")
        else:
            failed += 1
            print("⚠️ 無資料")

    output = {
        "updatedAt": datetime.now().isoformat(),
        "source": "MOPS (公開資訊觀測站)",
        "stocks": results,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"完成！成功: {success}, 無資料: {failed}")
    print(f"已保存至 {OUTPUT_FILE}")
    print(f"{'='*60}")

    return success > 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
