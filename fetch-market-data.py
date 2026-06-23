#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
財金早報市場指數抓取腳本
使用 yfinance 獲取全球主要市場指數
"""

import yfinance as yf
import json
from datetime import datetime, timedelta
import pytz
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 需要抓取的市場指數
# tz: 各交易所本地時區（用於正確顯示交易日期）
INDICES = {
    '^DJI':    {'name': '道瓊',          'group': 'US',   'tz': 'America/New_York'},
    '^GSPC':   {'name': 'S&P 500',       'group': 'US',   'tz': 'America/New_York'},
    '^IXIC':   {'name': '那斯達克',       'group': 'US',   'tz': 'America/New_York'},
    '^N225':   {'name': '日經225',        'group': 'JP',   'tz': 'Asia/Tokyo'},
    '^BSESN':  {'name': 'SENSEX',        'group': 'IN',   'tz': 'Asia/Kolkata'},
    '^NSEI':   {'name': 'NIFTY 50',      'group': 'IN',   'tz': 'Asia/Kolkata'},
    '^TWII':   {'name': '台灣加權指數',   'group': 'TW',   'tz': 'Asia/Taipei'},
    'GC=F':    {'name': '黃金',          'group': 'GOLD', 'tz': 'America/New_York'},
    'VNI':     {'name': '越南 VN-Index', 'group': 'VN',   'tz': 'Asia/Ho_Chi_Minh'},
}

def fetch_index(symbol, info):
    try:
        ticker = yf.Ticker(symbol)
        # 取 10 天以確保拿到最新交易日（有時 5 天不足，尤其是非美股時區）
        hist = ticker.history(period='10d')

        if hist.empty:
            print(f'[WARN] {info["name"]} ({symbol}): 無數據')
            return None

        # 過濾掉今天尚未收盤的資料：
        # 用交易所本地時區判斷最後一筆是否為「已收盤交易日」
        tz_name = info.get('tz', 'UTC')
        local_tz = pytz.timezone(tz_name)
        # pytz 的 datetime.now(tz) 有陷阱，改用 UTC 轉換
        now_local = datetime.now(pytz.UTC).astimezone(local_tz)

        # hist.index 是 DatetimeIndex（yfinance 通常返回 UTC aware）
        # 統一轉成本地交易所的 date
        def to_local_date(ts):
            # 若是 UTC aware，轉到本地時區；否則假設已是本地日期
            if hasattr(ts, 'tz_convert'):  # pandas Timestamp
                return ts.tz_convert(local_tz).date()
            elif hasattr(ts, 'astimezone') and ts.tzinfo:  # datetime with tzinfo
                return ts.astimezone(local_tz).date()
            elif hasattr(ts, 'date'):
                return ts.date()
            return ts  # 已是 date 對象

        today_local = now_local.date()
        # 改進：檢查最後一筆是否為「未來日期」（如果時區差異導致顯示未來日），而不是「今天」
        # 因為 yfinance 返回的是已完成的交易日，不應該排除
        last_date = to_local_date(hist.index[-1])
        # 只有當最後一筆日期 > 今日時才排除（表示跨越時區邊界獲取到未來數據）
        if last_date > today_local:
            print(f'[DEBUG] {info["name"]}: 排除未來日期 {last_date}')
            hist = hist.iloc[:-1]  # 排除未來數據
            if hist.empty:
                print(f'[WARN] {info["name"]} ({symbol}): 排除未來日期後無數據')
                return None

        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) >= 2 else latest

        close = float(latest['Close'])
        prev_close = float(prev['Close'])
        change = close - prev_close
        change_pct = (change / prev_close * 100) if prev_close != 0 else 0
        arrow = '▲' if change >= 0 else '▼'
        # 用交易所本地時區顯示日期
        date_str = to_local_date(hist.index[-1]).strftime('%m/%d')

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
