#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
財金早報市場指數抓取腳本
使用 yfinance 獲取全球主要市場指數
"""

import yfinance as yf
import requests
import json
from datetime import datetime, timedelta
import pytz
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 需要抓取的市場指數
# tz: 各交易所本地時區（用於正確顯示交易日期）
# 註：台股改用 TWSE 官方 API（見 fetch_taiex），因 yfinance 的 ^TWII 資料常缺交易日
#     越南 VN-Index 改用 fetch_vnindex()：正確 ticker 為 ^VNINDEX.VN（先前漏了開頭的
#     ^ 才誤判無資料），但此 ticker 在 yfinance 只有單筆快照、無日線歷史，
#     history() 抓不到，需改用 fast_info 的 lastPrice/previousClose
INDICES = {
    '^DJI':    {'name': '道瓊',          'group': 'US',   'tz': 'America/New_York'},
    '^GSPC':   {'name': 'S&P 500',       'group': 'US',   'tz': 'America/New_York'},
    '^IXIC':   {'name': '那斯達克',       'group': 'US',   'tz': 'America/New_York'},
    '^N225':   {'name': '日經225',        'group': 'JP',   'tz': 'Asia/Tokyo'},
    '^BSESN':  {'name': 'SENSEX',        'group': 'IN',   'tz': 'Asia/Kolkata'},
    '^NSEI':   {'name': 'NIFTY 50',      'group': 'IN',   'tz': 'Asia/Kolkata'},
    'GC=F':    {'name': '黃金',          'group': 'GOLD', 'tz': 'America/New_York'},
}


def fetch_taiex():
    """
    台股加權指數改用 TWSE 官方 API（FMTQIK）
    原因：yfinance 的 ^TWII 會缺漏交易日（實測 2026/07/14 台股有交易且大跌642點，
          但 yfinance 完全沒有該筆資料，導致早報顯示過期且方向相反的數據）
    """
    try:
        r = requests.get('https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK',
                         headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            print('[WARN] 台灣加權指數: TWSE API 無數據')
            return None

        latest = rows[-1]
        close = float(latest['TAIEX'].replace(',', ''))
        change = float(latest['Change'].replace(',', ''))
        prev_close = close - change
        change_pct = (change / prev_close * 100) if prev_close else 0
        arrow = '▲' if change >= 0 else '▼'

        # 民國年日期 1150714 -> 07/14
        roc = latest['Date']
        date_str = f'{roc[3:5]}/{roc[5:7]}'

        result = {
            'name': '台灣加權指數',
            'group': 'TW',
            'price': round(close, 2),
            'change': round(change, 2),
            'changePct': round(change_pct, 2),
            'arrow': arrow,
            'date': date_str,
            'displayStr': f'{close:,.0f}（{date_str}，{arrow}{abs(change_pct):.2f}%）'
        }
        print(f'[OK] 台灣加權指數: {close:,.0f} ({arrow}{abs(change_pct):.2f}%) [TWSE官方]')
        return result

    except Exception as e:
        print(f'[WARN] 台灣加權指數 (TWSE API): {e}')
        return None

def fetch_vnindex():
    """
    越南 VN-Index：yfinance 的 ^VNINDEX.VN 只提供單筆即時快照，沒有日線歷史
    （history() 只回傳最新一筆），改用 fast_info 的 lastPrice/previousClose
    計算漲跌。日期沒有官方欄位可用，取當下越南當地日期（UTC+7）代替。
    """
    try:
        ticker = yf.Ticker('^VNINDEX.VN')
        fi = ticker.fast_info

        close = fi.get('lastPrice')
        prev_close = fi.get('previousClose')
        if close is None or prev_close is None:
            print('[WARN] 越南 VN-Index: fast_info 缺少價格資料')
            return None

        close = float(close)
        prev_close = float(prev_close)
        change = close - prev_close
        change_pct = (change / prev_close * 100) if prev_close != 0 else 0
        arrow = '▲' if change >= 0 else '▼'

        local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        date_str = datetime.now(pytz.UTC).astimezone(local_tz).strftime('%m/%d')

        result = {
            'name': '越南 VN-Index',
            'group': 'VN',
            'price': round(close, 2),
            'change': round(change, 2),
            'changePct': round(change_pct, 2),
            'arrow': arrow,
            'date': date_str,
            'displayStr': f'{close:,.0f}（{date_str}，{arrow}{abs(change_pct):.2f}%）'
        }
        print(f'[OK] 越南 VN-Index: {close:,.0f} ({arrow}{abs(change_pct):.2f}%) [快照，非日線]')
        return result

    except Exception as e:
        print(f'[WARN] 越南 VN-Index: {e}')
        return None

def fetch_index(symbol, info):
    try:
        ticker = yf.Ticker(symbol)
        # 取 10 天以確保拿到最新交易日（有時 5 天不足，尤其是非美股時區）
        hist = ticker.history(period='10d')

        if hist.empty:
            print(f'[WARN] {info["name"]} ({symbol}): 無數據')
            return None

        # 排除 Close 為 NaN 的列：yfinance 在盤前/盤中常回傳一筆空資料，
        # 若不濾掉會算出 nan 並寫進 JSON（實測美股在美東盤前抓取時全為 nan）
        hist = hist.dropna(subset=['Close'])
        if hist.empty:
            print(f'[WARN] {info["name"]} ({symbol}): 濾除NaN後無有效數據')
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

    # 台股用官方 API 單獨處理
    taiex = fetch_taiex()
    if taiex:
        results['^TWII'] = taiex

    # 越南 VN-Index 單獨處理（fast_info 快照，非日線）
    vnindex = fetch_vnindex()
    if vnindex:
        results['^VNINDEX.VN'] = vnindex

    # 儲存結果
    output = {
        'updatedAt': datetime.utcnow().isoformat() + 'Z',
        'indices': results,
        'count': len(results)
    }

    with open('market-data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n=== 完成：{len(results)}/{len(INDICES) + 2} 個指數已獲取 ===')  # +2 為台股、越南(另外抓)
    print(f'輸出：market-data.json')

if __name__ == '__main__':
    main()
