#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
補上 tw-stocks.json 缺漏的台股 ETF。

背景：tw-stocks.json 原本只從 TWSE/TPEx「上市公司/上櫃公司」名冊(t187ap03_L /
mopsfin_t187ap03_O)建立，這兩份名冊本身結構上不含 ETF(ETF 是基金，不是公司)，
導致 ETF 搜尋補全完全空白(0050 這類要直接輸入代號才查得到，下拉建議搜不到)。

資料源改用 TWSE OpenAPI「基金基本資料彙總表」(t187ap47_L)——這才是官方真正
涵蓋全部台股 ETF(一般型/國外成分/槓桿反向/主動式等)的名冊，含中英文名稱。
"""
import json
import sys
import requests
import urllib3
from datetime import datetime, timezone

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ETF_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap47_L"


def fetch_etf_list():
    # TWSE 憑證缺 Subject Key Identifier，屬官方已知瑕疵(同 tpex.org.tw)，關閉嚴格驗證避免握手失敗
    r = requests.get(ETF_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30, verify=False)
    r.raise_for_status()
    return r.json()


def main():
    with open("tw-stocks.json", "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    stocks = data["stocks"]

    etf_rows = fetch_etf_list()
    added = 0
    for row in etf_rows:
        code = row.get("基金代號")
        if not code:
            continue
        stocks[code] = {
            "code": code,
            "name": row.get("基金簡稱") or code,
            "name_en": row.get("基金英文名稱") or row.get("基金簡稱") or code,
            "type": "ETF",
            "industry": row.get("基金類型") or "",
            "listed_date": row.get("上市日期") or "",
            "short": row.get("基金簡稱") or code,
        }
        added += 1

    data["count"] = len(stocks)
    data["updated"] = datetime.now(timezone.utc).isoformat()

    with open("tw-stocks.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"OK 已補上 {added} 支ETF，tw-stocks.json 總數: {len(stocks)}")


if __name__ == "__main__":
    main()
