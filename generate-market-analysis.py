#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
財金早報市場分析生成腳本
流程：Google News RSS 抓標題 → Claude API 生成繁中分析 → 輸出 market-analysis.json
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

MARKET_QUERIES = {
    'US': {
        'label': '美國股市',
        'queries': ['Dow Jones S&P500 Nasdaq market June 2026', 'US stock market Federal Reserve 2026'],
        'symbols': ['道瓊', 'S&P500', '那斯達克'],
    },
    'JP': {
        'label': '日經225',
        'queries': ['日経225 株式市場 2026年6月', 'Nikkei 225 Japan stock market 2026'],
        'symbols': ['日經225'],
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
    """呼叫 Google Gemini API (gemini-2.0-flash，免費層)"""
    if not GEMINI_API_KEY:
        raise ValueError('GEMINI_API_KEY 未設定')

    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}'
    body = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'maxOutputTokens': 200, 'temperature': 0.3}
    }).encode('utf-8')

    req = urllib.request.Request(url, data=body,
        headers={'content-type': 'application/json'}, method='POST')

    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.loads(resp.read().decode('utf-8'))

    return result['candidates'][0]['content']['parts'][0]['text'].strip()


def generate_analysis(market_key, headlines, price_data=None, ai_func=None):
    """用 Claude 生成市場分析"""
    config = MARKET_QUERIES[market_key]
    label = config['label']

    price_info = ''
    if price_data:
        arrow = price_data.get('arrow', '')
        pct = abs(price_data.get('changePct', 0))
        price_info = f'今日漲跌：{arrow}{pct:.2f}%。'

    headlines_text = '\n'.join(f'- {h}' for h in headlines) if headlines else '（無最新新聞）'

    prompt = f"""根據以下{label}最新新聞標題，用繁體中文寫一段50字內的市場分析摘要。
要求：客觀簡潔，說明主要驅動因素，不加標題，直接輸出內文。

{price_info}
相關新聞：
{headlines_text}

輸出格式：直接寫分析文字，50字以內。"""

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
    group_map = {'US': '^DJI', 'JP': '^N225', 'TW': '^TWII', 'GOLD': 'GC=F', 'IN': '^BSESN', 'VN': 'VNI'}
    symbol = group_map.get(market_key)
    return indices.get(symbol) if symbol else None


def main():
    print('\n=== 財金早報市場分析生成 ===\n')

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

        if GEMINI_API_KEY and headlines:
            print(f'   🤖 Gemini 生成分析...')
            analysis = generate_analysis(market_key, headlines, price_data, call_gemini)
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
