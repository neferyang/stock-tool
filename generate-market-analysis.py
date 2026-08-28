#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
財金報告市場分析生成腳本
流程：Google News RSS 抓標題 → Claude API 生成繁中分析 → 輸出 market-analysis.json
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-flash-latest')

MARKET_QUERIES = {
    'US': {
        'label': '美國股市',
        'queries': ['Dow Jones S&P500 Nasdaq market June 2026', 'US stock market Federal Reserve 2026', 'Philadelphia Semiconductor Index SOX 2026'],
        'symbols': ['道瓊', 'S&P500', '那斯達克', '費城半導體指數'],
    },
    'JP': {
        'label': '日經225',
        'queries': ['日経225 株式市場 2026年6月', 'Nikkei 225 Japan stock market 2026'],
        'symbols': ['日經225'],
    },
    'KR': {
        'label': '南韓 KOSPI',
        'queries': ['코스피 주식시장 2026', 'KOSPI Korea stock market 2026'],
        'symbols': ['KOSPI'],
    },
    'TW': {
        'label': '台灣加權指數',
        'queries': ['台股 加權指數 外資 2026年6月', '台灣股市 行情分析 2026'],
        'symbols': ['台灣加權指數'],
    },
    'GOLD': {
        'label': '黃金',
        'queries': ['gold price market 2026 June Fed', '黃金 金價 走勢 2026年6月'],
        'symbols': ['黃金'],
    },
    'IN': {
        'label': '印度',
        'queries': ['India SENSEX NIFTY stock market June 2026'],
        'symbols': ['SENSEX', 'NIFTY'],
    },
    'VN': {
        'label': '越南 VN-Index',
        'queries': ['Vietnam VN-Index stock market 2026'],
        'symbols': ['越南 VN-Index'],
    },
}


def fetch_news_rss(query, max_items=5):
    """從 Google News RSS 抓新聞標題"""
    encoded = urllib.parse.quote(query)
    url = f'https://news.google.com/rss/search?q={encoded}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            tree = ET.parse(resp)
        items = tree.findall('.//item')
        headlines = []
        for item in items[:max_items]:
            title = item.findtext('title', '').strip()
            if title:
                # 移除 - Google News 後綴
                title = title.split(' - ')[0].strip()
                headlines.append(title)
        return headlines
    except Exception as e:
        print(f'[RSS WARN] {query[:30]}: {e}')
        return []


def gather_headlines(market_key):
    """為某市場收集所有新聞標題"""
    config = MARKET_QUERIES[market_key]
    all_headlines = []
    for q in config['queries']:
        headlines = fetch_news_rss(q, max_items=4)
        all_headlines.extend(headlines)
        if len(all_headlines) >= 6:
            break
    # 去重
    seen = set()
    unique = []
    for h in all_headlines:
        if h not in seen:
            seen.add(h)
            unique.append(h)
    return unique[:8]


def call_gemini(prompt):
    """呼叫 Google Gemini API，免費層 429 限流時退避重試（與 generate-news-highlights.py 同一套）"""
    if not GEMINI_API_KEY:
        raise ValueError('GEMINI_API_KEY 未設定')

    url = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}'

    def _build_body(with_thinking_config):
        generation_config = {'maxOutputTokens': 300, 'temperature': 0.3}
        if with_thinking_config:
            # gemini-2.5/3.7系列預設開啟thinking，會先扣maxOutputTokens額度做內部推理，
            # 可見輸出被擠壓到只剩幾個字就被截斷（實測黃金分析被砍成「（今日上漲0」）。
            # 這種格式化短輸出任務不需要thinking，設thinkingBudget=0關閉。
            # 部分較新模型不接受此參數（400 INVALID_ARGUMENT），失敗時改不帶此參數重試，
            # 邏輯與generate-news-highlights.py的call_gemini()同一套。
            generation_config['thinkingConfig'] = {'thinkingBudget': 0}
        return json.dumps({
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': generation_config,
        }).encode('utf-8')

    def _request(with_thinking_config):
        req = urllib.request.Request(url, data=_build_body(with_thinking_config),
            headers={'content-type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        return result['candidates'][0]['content']['parts'][0]['text'].strip()

    for attempt in range(3):
        try:
            try:
                return _request(with_thinking_config=True)
            except urllib.error.HTTPError as e:
                if e.code == 400:
                    print('   🔎 帶 thinkingConfig 遭 400，改不帶此參數重試...')
                    return _request(with_thinking_config=False)
                raise
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                wait = 20 * (attempt + 1)
                print(f'   ⏳ Gemini 429 限流，{wait}s 後重試 ({attempt+1}/2)...')
                time.sleep(wait)
                continue
            raise


def generate_analysis(market_key, headlines, price_data=None, ai_func=None):
    """用 Claude 生成市場分析"""
    config = MARKET_QUERIES[market_key]
    label = config['label']

    price_info = ''
    if price_data:
        arrow = price_data.get('arrow', '')
        pct = abs(price_data.get('changePct', 0))
        direction = '上漲' if arrow == '▲' else '下跌'
        price_info = f'今日{direction} {pct:.2f}%。'

    headlines_text = '\n'.join(f'- {h}' for h in headlines) if headlines else ''
    news_section = f'\n相關新聞：\n{headlines_text}' if headlines_text else ''

    prompt = f"""你是財經分析師，請用繁體中文為「{label}」寫一段市場分析摘要。

數據：{price_info if price_info else '今日行情平穩。'}{news_section}

要求：
- 50字以內
- 說明可能的市場驅動因素
- 客觀簡潔，不加標題
- 直接輸出分析文字"""

    try:
        return ai_func(prompt)
    except Exception as e:
        print(f'[AI WARN] {label}: {e}')
        return None


RULE_TEMPLATES = {
    'US': {
        'up':   '美股三大指數收漲，市場情緒偏樂觀，科技股帶動漲勢，Fed 政策方向持續牽引盤面。',
        'down': '美股三大指數收跌，升息預期升溫或獲利了結賣壓拖累，投資人觀望情緒濃厚。',
        'flat': '美股小幅震盪，多空力道相當，市場靜待重要經濟數據或 Fed 官員發言指引。',
    },
    'JP': {
        'up':   '日股收漲，日圓走弱提振出口類股，避險資金回流，整體市場氣氛偏正向。',
        'down': '日股收跌，日圓走強壓抑出口股獲利，全球風險情緒降溫拖累日本市場。',
        'flat': '日股小幅整理，投資人等待日銀政策方向，盤面呈現觀望態勢。',
    },
    'KR': {
        'up':   '南韓KOSPI收漲，半導體及科技權值股領漲，外資買盤支撐市場氣氛偏正向。',
        'down': '南韓KOSPI收跌，科技股獲利了結賣壓拖累，外資賣超壓抑指數表現。',
        'flat': 'KOSPI小幅震盪，投資人觀望半導體循環及Fed政策方向，盤面呈整理格局。',
    },
    'TW': {
        'up':   '台股收漲，外資買超支撐，AI 及半導體族群領漲，加權指數維持強勢格局。',
        'down': '台股收跌，外資賣超壓抑，高檔獲利了結賣壓出現，技術面短線需整理。',
        'flat': '台股小幅震盪，量縮整理，主流族群輪動，指數維持盤整格局。',
    },
    'GOLD': {
        'up':   '金價上漲，地緣政治風險或美元走弱提供支撐，避險需求推升買盤。',
        'down': '金價下跌，美元走強或風險偏好回升壓抑金價，市場需求降溫。',
        'flat': '金價窄幅震盪，多空因素相互抵消，市場等待明確方向指引。',
    },
    'IN': {
        'up':   '印度股市上漲，經濟成長動能強勁，外資持續流入新興市場。',
        'down': '印度股市回落，全球資金緊縮預期壓抑新興市場表現。',
        'flat': '印度股市持平，投資人觀望政策動向，市場整體偏謹慎。',
    },
    'VN': {
        'up':   '越南 VN-Index 上漲，外資買超及經濟成長前景吸引資金流入。',
        'down': '越南 VN-Index 下跌，全球升息預期與資金外流壓力拖累東南亞市場。',
        'flat': '越南市場持平整理，觀望情緒主導，靜待外部環境明朗化。',
    },
}

def rule_based_analysis(market_key, price_data):
    """Gemini 失敗時的規則式備援文字"""
    templates = RULE_TEMPLATES.get(market_key)
    if not templates:
        return None
    if price_data:
        pct = price_data.get('changePct', 0)
        key = 'up' if pct > 0.1 else ('down' if pct < -0.1 else 'flat')
    else:
        key = 'flat'
    return templates[key]


def load_market_data():
    try:
        with open('market-data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('indices', {})
    except Exception as e:
        print(f'[WARN] 無法讀取 market-data.json: {e}')
        return {}


def find_price_for_market(indices, market_key):
    group_map = {'US': '^DJI', 'JP': '^N225', 'KR': '^KS11', 'TW': '^TWII', 'GOLD': 'GC=F', 'IN': '^BSESN', 'VN': '^VNINDEX.VN'}
    symbol = group_map.get(market_key)
    return indices.get(symbol) if symbol else None


def main():
    print('\n=== 財金報告市場分析生成 ===\n')

    if not GEMINI_API_KEY:
        print('⚠️  GEMINI_API_KEY 未設定，將使用規則式備援文字')

    indices = load_market_data()
    results = {}

    for market_key, config in MARKET_QUERIES.items():
        label = config['label']
        print(f'📰 {label} - 抓取新聞...')

        headlines = gather_headlines(market_key)
        print(f'   取得 {len(headlines)} 則標題')

        price_data = find_price_for_market(indices, market_key)

        if GEMINI_API_KEY:
            print(f'   🤖 Gemini 生成分析（{len(headlines)} 則新聞）...')
            analysis = generate_analysis(market_key, headlines, price_data, call_gemini)
            time.sleep(13)  # 免費層限流 5 req/min，7 個市場需間隔避免爆量
            if not analysis:
                print(f'   ⚠️  Gemini 失敗，改用規則式備援')
                analysis = rule_based_analysis(market_key, price_data)
        else:
            analysis = rule_based_analysis(market_key, price_data)

        if analysis:
            results[market_key] = {
                'label': label,
                'analysis': analysis,
                'headlines': headlines[:3],
            }
            print(f'   ✅ {analysis[:40]}...')
        else:
            print(f'   ⚠️  無法生成分析')

    output = {
        'updatedAt': datetime.utcnow().isoformat() + 'Z',
        'markets': results,
    }

    with open('market-analysis.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n=== 完成：{len(results)} 個市場分析已生成 → market-analysis.json ===')


if __name__ == '__main__':
    main()
