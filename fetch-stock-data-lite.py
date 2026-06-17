#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版：只抓取關鍵股票數據（測試用）
"""

import yfinance as yf
import json
from datetime import datetime
import sys

# 設定 stdout 編碼
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("\n[START] Stock Data Fetch - Test\n")

    # 只測試 2 支台股和 2 支美股
    tickers = ["2330.TW", "2207.TW", "AAPL", "MSFT"]
    data = {}

    for ticker in tickers:
        try:
            print("[{}] Fetching...".format(ticker), flush=True)
            stock = yf.Ticker(ticker)
            info = stock.info

            data[ticker] = {
                "price": info.get('currentPrice') or info.get('regularMarketPrice'),
                "pe": info.get('trailingPE'),
                "pb": info.get('priceToBook'),
                "name": info.get('longName', ticker),
            }
            print("[{}] OK".format(ticker))

        except Exception as e:
            print("[{}] ERROR: {}".format(ticker, str(e)))

    # 保存為 JSON
    output = {
        "updated": datetime.now().isoformat(),
        "stocks": data,
        "count": len([v for v in data.values() if v.get('price')])
    }

    with open('test-stocks.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print("\n[SUCCESS] Fetched {} stocks".format(output['count']))
    print("[FILE] Saved to test-stocks.json\n")

if __name__ == "__main__":
    main()
