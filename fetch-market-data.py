#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
財金早報市場指數抓取腳本
使用 yfinance 獲取全球主要市場指數
"""

import yfinance as yf
import json
from datetime import datetime, timedelta
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 需要抓取的市場指數
INDICES = {
    '^DJI':    {'name': '道瓊',          'group': 'US'},
    '^GSPC':   {'name': 'S&P 500',       'group': 'US'},
    '^IXIC':   {'name': '那斯達克',       'group': 'US'},
    '^N225':   {'name': '日經225',        'group': 'JP'},
    '^BSESN':  {'name': 'SENSEX',        'group': 'IN'},
    '^NSEI':   {'name': 'NIFTY 50',      'group': 'IN'},
    '^TWII':   {'name': '台灣加權指數',   'group': 'TW'},
    'GC=F':    {'name': '黃金',          'group': 'GOLD'},
    'VNI':     {'name': '越南 VN-Index', 'group': 'VN'},
}

def fetch_index(symbol, info):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='5d')

        if hist.empty:
            print(f'[WARN] {info["name"]} ({symbol}): 無數據')
            return None

        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) >= 2 else latest

        close = float(latest['Close'])
        prev_close = float(prev['Close'])
        change = close - prev_close
        change_pct = (change / prev_close * 100) if prev_close != 0 else 0
        arrow = '▲' if change >= 0 else '▼'
        date_str = hist.index[-1].strftime('%m/%d')

        result = {
            'name': info['name'],
            'group': info['group'],
            'price': round(close, 2),
            'change': round(change, 2),
            'changePct': round(change_pct, 2),
            'arrow': arrow,
            'date': date_str,
            'displayStr': f'{close:,.0f}（{date_str}，{arrow}{abs(change_pct):.2f}%）'
        }

        print(f'[OK] {info["name"]}: {close:,.0f} ({arrow}{abs(change_pct):.2f}%)')
        return result

    except Exception as e:
        print(f'[WARN] {info["name"]} ({symbol}): {e}')
        return None

def main():
    print('\n=== 財金早報市場數據抓取 ===\n')
    results = {}

    for symbol, info in INDICES.items():
        data = fetch_index(symbol, info)
        if data:
            results[symbol] = data

    # 儲存結果
    output = {
        'updatedAt': datetime.utcnow().isoformat() + 'Z',
        'indices': results,
        'count': len(results)
    }

    with open('market-data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n=== 完成：{len(results)}/{len(INDICES)} 個指數已獲取 ===')
    print(f'輸出：market-data.json')

if __name__ == '__main__':
    main()
