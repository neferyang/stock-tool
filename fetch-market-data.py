#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
財金報告市場指數抓取腳本
使用 yfinance 獲取全球主要市場指數
"""

import yfinance as yf
import requests
import json
import os
from datetime import datetime, timedelta
import pytz
import sys
import time

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

FUGLE_API_KEY = os.environ.get('FUGLE_API_KEY', '')

# 財金報告的台股焦點個股：挑幾檔市值權值股，讓報告不是只有大盤指數
HOT_STOCKS = [
    ('2330', '台積電'),
    ('2317', '鴻海'),
    ('2454', '聯發科'),
    ('2308', '台達電'),
    ('2382', '廣達'),
    ('2881', '富邦金'),
]

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
    '^SOX':    {'name': '費城半導體指數',  'group': 'US',   'tz': 'America/New_York'},
    '^N225':   {'name': '日經225',        'group': 'JP',   'tz': 'Asia/Tokyo'},
    '^KS11':   {'name': 'KOSPI',         'group': 'KR',   'tz': 'Asia/Seoul'},
    '^BSESN':  {'name': 'SENSEX',        'group': 'IN',   'tz': 'Asia/Kolkata'},
    '^NSEI':   {'name': 'NIFTY 50',      'group': 'IN',   'tz': 'Asia/Kolkata'},
    'GC=F':    {'name': '黃金',          'group': 'GOLD', 'tz': 'America/New_York'},
}

# 各市場收盤時間（當地時區，含30分鐘緩衝讓yfinance資料落地）。
# 用於判斷 yfinance 回傳「今天」那根K棒是否為完整收盤價：早報一天跑多次，
# 若執行當下該市場還在盤中，yfinance的當日K棒是即時跳動價、非收盤價，
# 若不過濾會把盤中報價誤植為「收盤數字」寫進早報，導致同一天內每次早報數字
# 都不同、且跟使用者當下看到的即時報價對不上（美股/黃金收盤後才抓，天然不受影響）。
MARKET_CLOSE = {
    '^N225':  (15, 30),
    '^KS11':  (16, 0),
    '^BSESN': (16, 0),
    '^NSEI':  (16, 0),
}


def fugle_quote(symbol):
    """Fugle 富果即時報價，沒設 FUGLE_API_KEY 或請求失敗回 None，呼叫端自行 fallback。"""
    if not FUGLE_API_KEY:
        return None
    try:
        r = requests.get(
            f'https://api.fugle.tw/marketdata/v1.0/stock/intraday/quote/{symbol}',
            headers={'X-API-KEY': FUGLE_API_KEY}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f'[WARN] Fugle quote {symbol}: {e}')
        return None


def fetch_taiex_fugle():
    """
    台灣加權指數優先用 Fugle 即時指數（symbol: IX0001）。
    TWSE 官方 FMTQIK 是收盤後才更新的日線資料，Fugle 盤中就能拿到當下指數，
    報告數字更貼近當下盤勢。失敗（無 Key／額度用盡／查無資料）就回 None，
    呼叫端 fallback 回 fetch_taiex() 的 TWSE 官方資料，不影響既有穩定度。
    """
    q = fugle_quote('IX0001')
    if not q or 'closePrice' not in q:
        return None
    close = q['closePrice']
    change = q.get('change', 0)
    change_pct = q.get('changePercent', 0)
    arrow = '▲' if change >= 0 else '▼'
    date = q.get('date', '')  # Fugle格式 "2026-10-13"
    date_str = f'{date[5:7]}/{date[8:10]}' if len(date) == 10 else ''

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
    print(f'[OK] 台灣加權指數: {close:,.0f} ({arrow}{abs(change_pct):.2f}%) [Fugle即時]')
    return result


def fetch_hot_stocks():
    """
    財金報告的台股焦點個股：用 Fugle 即時報價抓 HOT_STOCKS 清單裡的幾檔權值股，
    讓報告不是只有大盤指數。沒設 FUGLE_API_KEY 直接回空陣列，
    update-daily-report.js 沒資料就不渲染這個區塊，不影響報告其他部分。
    """
    if not FUGLE_API_KEY:
        return []
    results = []
    for code, name in HOT_STOCKS:
        q = fugle_quote(code)
        if not q or 'lastPrice' not in q:
            print(f'[WARN] 焦點個股 {name}({code}): 無資料')
            continue
        price = q['lastPrice']
        change = q.get('change', 0)
        change_pct = q.get('changePercent', 0)
        arrow = '▲' if change > 0 else ('▼' if change < 0 else '-')
        results.append({
            'code': code,
            'name': name,
            'price': price,
            'change': change,
            'changePct': change_pct,
            'arrow': arrow,
        })
        print(f'[OK] {name}({code}): {price} ({arrow}{abs(change_pct):.2f}%)')
    return results


def fetch_taiex():
    """
    台股加權指數改用 TWSE 官方 API（FMTQIK）
    原因：yfinance 的 ^TWII 會缺漏交易日（實測 2026/07/14 台股有交易且大跌642點，
          但 yfinance 完全沒有該筆資料，導致早報顯示過期且方向相反的數據）
    """
    # TWSE 偶發回傳空內容(非JSON)，r.json()會拋ValueError；比照auto-expand-stocks.py的
    # fetch_json()，加3次重試(5s/10s/15s遞增)，避免單次空回應就整個放棄、白丟這次台股數字
    # （update-daily-report.js找不到新資料時會保留舊值，不會顯示壞掉的數字，但數字就沒更新到）。
    rows = None
    last_err = None
    for attempt in range(3):
        try:
            r = requests.get('https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK',
                             headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            r.raise_for_status()
            rows = r.json()
            break
        except (requests.exceptions.RequestException, ValueError) as e:
            last_err = e
            if attempt < 2:
                time.sleep(5 * (attempt + 1))

    try:
        if rows is None:
            raise last_err
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
            last_date = to_local_date(hist.index[-1])

        # 排除「今天盤中還沒收盤」的即時報價：早報一天跑多次，若執行當下
        # 該市場仍在交易時段，yfinance當日K棒是即時跳動價、非收盤價，
        # 直接採用會讓早報數字每次不同、且跟即時報價本身就對不上。
        close_hm = MARKET_CLOSE.get(symbol)
        if close_hm and last_date == today_local:
            close_h, close_m = close_hm
            settle_dt = now_local.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
            if now_local < settle_dt:
                print(f'[DEBUG] {info["name"]}: 今日尚未收盤（{now_local.strftime("%H:%M")} < {close_h:02d}:{close_m:02d}），改用前一已收盤交易日')
                hist = hist.iloc[:-1]
                if hist.empty:
                    print(f'[WARN] {info["name"]} ({symbol}): 排除盤中報價後無數據')
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
    print('\n=== 財金報告市場數據抓取 ===\n')
    results = {}

    for symbol, info in INDICES.items():
        data = fetch_index(symbol, info)
        if data:
            results[symbol] = data

    # 台股優先用 Fugle 即時指數，失敗才 fallback 回 TWSE 官方 API
    taiex = fetch_taiex_fugle() or fetch_taiex()
    if taiex:
        results['^TWII'] = taiex

    # 越南 VN-Index 單獨處理（fast_info 快照，非日線）
    vnindex = fetch_vnindex()
    if vnindex:
        results['^VNINDEX.VN'] = vnindex

    # 台股焦點個股（Fugle 即時報價，沒設 Key 就是空陣列）
    hot_stocks = fetch_hot_stocks()

    # 儲存結果
    output = {
        'updatedAt': datetime.utcnow().isoformat() + 'Z',
        'indices': results,
        'count': len(results),
        'hotStocks': hot_stocks
    }

    with open('market-data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n=== 完成：{len(results)}/{len(INDICES) + 2} 個指數已獲取 ===')  # +2 為台股、越南(另外抓)
    print(f'輸出：market-data.json')

if __name__ == '__main__':
    main()
