#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
補上 tw-stocks.json 缺漏的興櫃股。

背景：tw-stocks.json 原本只從 TWSE/TPEx「上市公司/上櫃公司」名冊(t187ap03_L /
mopsfin_t187ap03_O)建立，兩份都不含興櫃(Emerging Stock Market)公司，導致興櫃股
（如和運租車 7855）就算 financial-data-complete.json 有真實財報資料，
名稱搜尋/下拉建議還是完全找不到代號，只能碰運氣直接打代號查。

資料源改用 TPEx OpenAPI「興櫃公司基本資料」(mopsfin_t187ap03_R)——涵蓋全部興櫃
公司名冊。Yahoo Finance 對興櫃股的報價後綴跟上櫃股一樣是 .TWO（已實測 7855.TWO
有正常報價），前端既有的 .TW→.TWO fallback 邏輯不用改，只要把代號補進搜尋清單即可。
"""
import json
import sys
import requests
import urllib3
from datetime import datetime, timezone

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

EMERGING_URL = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_R"


def fetch_emerging_list():
    r = requests.get(EMERGING_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30, verify=False)
    r.raise_for_status()
    return r.json()


def main():
    with open("tw-stocks.json", "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    stocks = data["stocks"]

    rows = fetch_emerging_list()
    added = 0
    skipped_existing = 0
    for row in rows:
        code = row.get("SecuritiesCompanyCode")
        name = row.get("CompanyAbbreviation")
        if not code or not name:
            continue
        if code in stocks:
            # 代號如果已經在上市/上櫃/ETF名冊裡（例如剛從興櫃轉上市），不覆蓋既有資料
            skipped_existing += 1
            continue
        stocks[code] = {
            "code": code,
            "name": row.get("CompanyName") or name,
            "name_en": "",
            "type": "興櫃",
            "industry": row.get("SecuritiesIndustryCode") or "",
            "listed_date": row.get("DateOfListing") or "",
            "short": name,
        }
        added += 1

    data["count"] = len(stocks)
    data["updated"] = datetime.now(timezone.utc).isoformat()

    with open("tw-stocks.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"OK 已補上 {added} 支興櫃股（{skipped_existing} 支代號已存在略過），"
          f"tw-stocks.json 總數: {len(stocks)}")


if __name__ == "__main__":
    main()
