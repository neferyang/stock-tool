#!/usr/bin/env python3
"""
股票數據抓取腳本 - 使用 yfinance
用途：定期從 Yahoo Finance 抓取台股和美股數據，保存為 JSON
"""

import yfinance as yf
import json
from datetime import datetime
import sys

# 常見台股列表（可擴展）
TW_STOCKS = [
    "1101.TW",  # 台泥
    "1102.TW",  # 亞泥
    "1301.TW",  # 台塑
    "1303.TW",  # 南亞
    "1326.TW",  # 台化
    "2330.TW",  # 台積電
    "2317.TW",  # 鴻海
    "2308.TW",  # 台達電
    "2454.TW",  # 聯發科
    "3008.TW",  # 大立光
    "2883.TW",  # 開發金
    "2891.TW",  # 中信金
    "2892.TW",  # 第一金
    "2002.TW",  # 裕隆
    "2207.TW",  # 和泰
]

# 常見美股列表（可擴展）
US_STOCKS = [
    "AAPL",   # 蘋果
    "MSFT",   # 微軟
    "GOOGL",  # 谷歌
    "AMZN",   # 亞馬遜
    "TSLA",   # 特斯拉
    "META",   # Meta
    "NVDA",   # 英偉達
    "JPM",    # JP Morgan
    "V",      # Visa
    "WMT",    # 沃爾瑪
    "SPY",    # S&P 500 ETF
    "QQQ",    # Nasdaq 100 ETF
    "IVV",    # iShares Core S&P 500 ETF
]

def fetch_stock_data(ticker_list, market_name):
    """
    抓取股票數據

    Args:
        ticker_list: 股票代號列表
        market_name: 市場名稱 ('TW' 或 'US')

    Returns:
        dict: {ticker: {price, pe, pb, dividend_yield, ...}}
    """
    data = {}

    for ticker in ticker_list:
        try:
            print(f"  抓取 {ticker}...", end=" ", flush=True)

            # 使用 yfinance 抓取數據
            stock = yf.Ticker(ticker)
            info = stock.info

            # 提取關鍵數據
            stock_data = {
                "code": ticker.replace('.TW', '').replace('.TWO', ''),
                "name": info.get('longName', '') or info.get('shortName', ticker),
                "price": info.get('currentPrice') or info.get('regularMarketPrice'),
                "pe": info.get('trailingPE'),
                "pb": info.get('priceToBook'),
                "dividend_yield": info.get('dividendYield'),
                "52_week_high": info.get('fiftyTwoWeekHigh'),
                "52_week_low": info.get('fiftyTwoWeekLow'),
                "market_cap": info.get('marketCap'),
                "eps": info.get('trailingEps'),
                "roe": info.get('returnOnEquity'),
                "updated_at": datetime.now().isoformat()
            }

            # 只保留非 None 的字段
            stock_data = {k: v for k, v in stock_data.items() if v is not None}

            data[ticker] = stock_data
            print("✅")

        except Exception as e:
            print(f"❌ 錯誤: {str(e)}")
            continue

    return data

def main():
    """主程序"""
    print(f"\n🚀 股票數據抓取 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 抓取台股
    print("\n📍 抓取台股數據...")
    tw_data = fetch_stock_data(TW_STOCKS, "TW")

    # 抓取美股
    print("\n📍 抓取美股數據...")
    us_data = fetch_stock_data(US_STOCKS, "US")

    # 保存為 JSON
    print("\n💾 保存 JSON 文件...")

    tw_output = {
        "market": "Taiwan",
        "updated_at": datetime.now().isoformat(),
        "data": tw_data,
        "count": len(tw_data)
    }

    us_output = {
        "market": "United States",
        "updated_at": datetime.now().isoformat(),
        "data": us_data,
        "count": len(us_data)
    }

    # 寫入文件
    with open('tw-stocks.json', 'w', encoding='utf-8') as f:
        json.dump(tw_output, f, ensure_ascii=False, indent=2)
    print("  ✅ tw-stocks.json 已保存")

    with open('us-stocks.json', 'w', encoding='utf-8') as f:
        json.dump(us_output, f, ensure_ascii=False, indent=2)
    print("  ✅ us-stocks.json 已保存")

    print("\n" + "=" * 50)
    print(f"✅ 完成！共抓取 {len(tw_data)} 支台股，{len(us_data)} 支美股")
    print(f"📝 下次更新時間：{datetime.now().isoformat()}")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ 用戶中止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        sys.exit(1)
