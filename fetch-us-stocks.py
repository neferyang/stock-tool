#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產生 us-stocks.json：美股搜尋自動補全用的代號+公司名清單。
資料源：Finnhub /stock/symbol?exchange=US（免費額度涵蓋，index.html 已內建同一組 FINNHUB_KEY）。
只保留 Common Stock/ADR/ETP 三類，過濾掉權證/債券等雜訊，避免清單過度膨脹。
格式為純陣列 [{Code,Name}]，對應 index.html 的 US_STOCK_CACHE 直接 fetch 後即用（無需 wrapper）。
"""
import json
import sys
import urllib.request

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FINNHUB_KEY = 'd8f8m4hr01qub7kgc2j0d8f8m4hr01qub7kgc2jg'
URL = f"https://finnhub.io/api/v1/stock/symbol?exchange=US&token={FINNHUB_KEY}"
KEEP_TYPES = {"Common Stock", "ADR", "ETP"}


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    raw = fetch_json(URL)
    print(f"Finnhub 回傳 {len(raw)} 筆原始資料")

    seen = set()
    out = []
    for row in raw:
        symbol = row.get("symbol")
        name = row.get("description")
        typ = row.get("type")
        if not symbol or not name or typ not in KEEP_TYPES:
            continue
        if symbol in seen:
            continue
        seen.add(symbol)
        out.append({"Code": symbol, "Name": name, "Type": typ})

    with open("us-stocks.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"✅ 已寫入 us-stocks.json：{len(out)} 檔（Common Stock/ADR/ETP）")


if __name__ == "__main__":
    main()
