#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改進版：yfinance 數據抓取腳本 - 獲取完整財務數據
"""

import yfinance as yf
import json
from datetime import datetime
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("\n[START] Stock Data Fetch - Enhanced Version\n")

    # 測試股票列表
    tickers = ["2330.TW", "2207.TW", "2454.TW", "1101.TW", "1303.TW"]
    data = {}

    for ticker in tickers:
        try:
            code = ticker.replace('.TW', '')
            print("[{}] Fetching...".format(ticker), flush=True)

            stock = yf.Ticker(ticker)
            info = stock.info

            # 基本數據
            price = info.get('currentPrice') or info.get('regularMarketPrice')

            # 估值數據
            pe = info.get('trailingPE')
            pb = info.get('priceToBook')
            dividend_yield = info.get('dividendYield')

            # 財務數據（透過 info）
            eps = info.get('trailingEps')
            roe = info.get('returnOnEquity')

            # 現金流和利潤率
            fcf = info.get('freeCashflow')
            operating_margin = info.get('operatingMargins')
            profit_margin = info.get('profitMargins')

            # 股息數據
            dividend = info.get('dividendRate')
            last_dividend_date = info.get('lastDividendDate')

            # 52週數據
            high_52 = info.get('fiftyTwoWeekHigh')
            low_52 = info.get('fiftyTwoWeekLow')

            # 市值和股份數
            market_cap = info.get('marketCap')
            shares_outstanding = info.get('sharesOutstanding')

            data[code] = {
                "code": code,
                "name": info.get('longName') or info.get('shortName') or ticker,
                "price": price,
                "pe": pe,
                "pb": pb,
                "eps": eps,
                "roe": roe,
                "dividend_yield": dividend_yield,
                "dividend": dividend,
                "last_dividend_date": last_dividend_date,
                "fcf": fcf,
                "operating_margin": operating_margin,
                "profit_margin": profit_margin,
                "52_week_high": high_52,
                "52_week_low": low_52,
                "market_cap": market_cap,
                "shares_outstanding": shares_outstanding,
                "updated_at": datetime.now().isoformat()
            }
            print("[{}] OK".format(code))

        except Exception as e:
            print("[{}] ERROR: {}".format(ticker, str(e)))

    # 保存為 JSON
    output = {
        "updated": datetime.now().isoformat(),
        "stocks": data,
        "data": data,  # 後端兼容性
        "count": len([v for v in data.values() if v.get('price')])
    }

    with open('tw-stocks.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n[SUCCESS] Fetched {} stocks".format(output['count']))
    print("[FILE] Saved to tw-stocks.json\n")

if __name__ == "__main__":
    main()
