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

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

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


def call_claude(prompt):
    """呼叫 Claude API (claude-haiku-4-5)"""
    if not ANTHROPIC_API_KEY:
        raise ValueError('ANTHROPIC_API_KEY 未設定')

    body = json.dumps({
        'model': 'claude-haiku-4-5-20251001',
        'max_tokens': 200,
        'messages': [{'role': 'user', 'content': prompt}]
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=body,
        headers={
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        method='POST'
    )

    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.loads(resp.read().decode('utf-8'))

    return result['content'][0]['text'].strip()


def generate_analysis(market_key, headlines, price_data=None):
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
        return call_claude(prompt)
    except Exception as e:
        print(f'[Claude WARN] {label}: {e}')
        return None


def rule_based_analysis(market_key, price_data):
    """無 Claude key 時的規則式備援"""
    if not price_data:
        return None
    config = MARKET_QUERIES[market_key]
    arrow = price_data.get('arrow', '')
    pct = abs(price_data.get('changePct', 0))
    direction = '上漲' if arrow == '▲' else '下跌'
    label = config['label']
    return f'{label}{direction} {pct:.2f}%，市場持續追蹤中。'


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

    if not ANTHROPIC_API_KEY:
        print('⚠️  ANTHROPIC_API_KEY 未設定，將使用規則式備援文字')

    indices = load_market_data()
    results = {}

    for market_key, config in MARKET_QUERIES.items():
        label = config['label']
        print(f'📰 {label} - 抓取新聞...')

        headlines = gather_headlines(market_key)
        print(f'   取得 {len(headlines)} 則標題')

        price_data = find_price_for_market(indices, market_key)

        if ANTHROPIC_API_KEY and headlines:
            print(f'   🤖 Claude 生成分析...')
            analysis = generate_analysis(market_key, headlines, price_data)
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
