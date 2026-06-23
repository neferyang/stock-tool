#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成每日新聞和重點觀察
用於更新 daily-report.json 中的 news 和 observations 字段
"""

import json
import requests
import sys
from datetime import datetime
from urllib.parse import quote

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def fetch_news_from_google(query, max_items=5):
    """從 Google News RSS 抓取新聞"""
    try:
        encoded = quote(query)
        url = f'https://news.google.com/rss/search?q={encoded}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'

        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'

        # 使用 XML 解析（更可靠）
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            headlines = []
            # 遍歷所有 item 元素
            for item in root.findall('.//item')[:max_items]:
                title_elem = item.find('title')
                desc_elem = item.find('description')

                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip()
                    # 去除 HTML 標籤
                    if '<' in title:
                        title = title.split('<')[0].strip()

                    desc = ''
                    if desc_elem is not None and desc_elem.text:
                        desc = desc_elem.text.strip()
                        # 去除 HTML 標籤和實體
                        import re
                        desc = re.sub(r'<[^>]+>', '', desc)  # 移除 HTML 標籤
                        desc = desc.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')

                    if not desc:
                        desc = f"更新於 {datetime.now().strftime('%Y-%m-%d')}"

                    if title and len(title) > 5:  # 跳過過短的標題
                        headlines.append({
                            'title': title[:100],
                            'description': desc[:200]
                        })

            return headlines

        except Exception as xml_error:
            print(f'⚠️ XML 解析失敗，嘗試文本解析: {xml_error}')
            # 備援：文本解析
            headlines = []
            lines = response.text.split('\n')

            for i, line in enumerate(lines):
                if '<title>' in line and '</title>' in line:
                    title = line.split('<title>')[1].split('</title>')[0].strip()
                    title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

                    # 嘗試找下一行的 description
                    desc = ''
                    for j in range(i+1, min(i+10, len(lines))):
                        if '<description>' in lines[j]:
                            desc = lines[j].split('<description>')[1].split('</description>')[0].strip()
                            desc = desc.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                            break

                    if title and len(title) > 5 and title not in [h['title'] for h in headlines]:
                        if not desc:
                            desc = f"查詢: {query}"
                        headlines.append({
                            'title': title[:100],
                            'description': desc[:200]
                        })

                    if len(headlines) >= max_items:
                        break

            return headlines

    except Exception as e:
        print(f'⚠️ 新聞抓取失敗 ({query}): {e}')
        return []

def generate_observations(markets_data):
    """根據市場數據生成觀察"""
    observations = []

    try:
        # 美股觀察
        if 'US' in markets_data:
            us_data = markets_data['US']
            change_sum = sum([m.get('change', 0) for m in us_data.values()])
            avg_change = change_sum / len(us_data) if us_data else 0

            if avg_change > 1:
                observations.append({
                    'emoji': '📈',
                    'title': '美股全面上漲',
                    'content': '美股三大指數普漲，市場情緒偏樂觀，科技股表現亮眼。'
                })
            elif avg_change < -1:
                observations.append({
                    'emoji': '📉',
                    'title': '美股回檔調整',
                    'content': '美股出現調整，投資人謹慎情緒升溫，避險資金流入。'
                })
            else:
                observations.append({
                    'emoji': '➡️',
                    'title': '美股漲跌互見',
                    'content': '美股三大指數表現分化，市場等待政策方向明確。'
                })

        # 亞股觀察
        if 'JP' in markets_data or 'TW' in markets_data:
            observations.append({
                'emoji': '🌏',
                'title': '亞股跟風美股',
                'content': '亞股走勢跟隨美股，日股和台股表現受美股指引。'
            })

        # 商品觀察
        if 'GOLD' in markets_data:
            observations.append({
                'emoji': '💰',
                'title': '貴金屬波動',
                'content': '黃金價格波動，受美元走勢和風險情緒影響。'
            })

    except Exception as e:
        print(f'⚠️ 生成觀察失敗: {e}')

    return observations

def main():
    print('\n=== 生成每日新聞和重點觀察 ===\n')

    news_sources = {
        '美股': '美國股市 S&P 500 NASDAQ',
        '台股': '台灣股市加權指數',
        '全球經濟': '全球經濟 央行'
    }

    all_news = []
    for category, query in news_sources.items():
        print(f'📰 {category}: 正在抓取...')
        news = fetch_news_from_google(query, max_items=2)
        all_news.extend(news)
        print(f'   ✅ 取得 {len(news)} 則')

    # 讀取市場數據以生成觀察
    try:
        with open('market-data.json', 'r', encoding='utf-8') as f:
            market_data_raw = json.load(f)
            # 按 group 分組
            markets_by_group = {}
            for symbol, data in market_data_raw.get('indices', {}).items():
                group = data.get('group', 'OTHER')
                if group not in markets_by_group:
                    markets_by_group[group] = {}
                markets_by_group[group][symbol] = data

        observations = generate_observations(markets_by_group)
        print(f'\n💡 已生成 {len(observations)} 個觀察')

    except Exception as e:
        observations = []
        print(f'\n⚠️ 無法生成觀察: {e}')

    # 生成重點
    key_observations = [
        {'number': 1, 'title': '市場波動性增加'},
        {'number': 2, 'title': '美元指數堅挺'},
        {'number': 3, 'title': '科技股領漲'}
    ]

    # 保存到文件
    output = {
        'updatedAt': datetime.utcnow().isoformat() + 'Z',
        'news': all_news,
        'observations': observations,
        'keyObservations': key_observations
    }

    with open('news-highlights.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n✅ 完成！已保存 news-highlights.json')
    print(f'   新聞：{len(all_news)} 則')
    print(f'   觀察：{len(observations)} 個')
    print(f'   重點：{len(key_observations)} 項')

if __name__ == '__main__':
    main()
