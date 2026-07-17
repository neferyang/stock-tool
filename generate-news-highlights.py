#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成每日新聞和重點觀察
用於更新 daily-report.json 中的 news 和 observations 字段
"""

import json
import os
import re
import requests
import sys
import urllib.error
import urllib.request
from datetime import datetime
from urllib.parse import quote

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
# gemini-2.0-flash 免費層已被 Google 關閉(limit:0)，改用仍有免費配額的 2.5-flash。
# 可用環境變數 GEMINI_MODEL 覆寫，方便日後不改 code 換模型。
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')


def call_gemini(prompt):
    """呼叫 Google Gemini API；與 generate-market-analysis.py 同一套。"""
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}'
    body = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'maxOutputTokens': 500, 'temperature': 0.3}
    }).encode('utf-8')
    req = urllib.request.Request(url, data=body,
        headers={'content-type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=25) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    return result['candidates'][0]['content']['parts'][0]['text'].strip()


def summarize_headlines(news):
    """用 Gemini 為每則新聞產生「一句話市場意涵」。只有標題、無全文，故定位為依標題判讀的
    意涵而非逐字摘要，prompt 明確禁止杜撰數字/事實。單次請求批次處理所有標題以省額度。
    失敗或未設 key 時不動 description（維持空字串 → 前端顯示為純連結）。"""
    if not GEMINI_API_KEY:
        print('   ⚠️ GEMINI_API_KEY 未設定，跳過重點摘要（維持純連結）')
        return
    # 診斷：列出這把 key 實際可用、且支援 generateContent 的模型（避免猜模型名）
    try:
        lm_url = f'https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}&pageSize=100'
        with urllib.request.urlopen(lm_url, timeout=15) as r:
            models = json.loads(r.read().decode('utf-8')).get('models', [])
        usable = [m['name'].replace('models/', '') for m in models
                  if 'generateContent' in m.get('supportedGenerationMethods', [])]
        print('   🔎 可用模型: ' + ', '.join(usable[:20]))
    except Exception as e:
        print(f'   🔎 ListModels 失敗: {e}')
    titles = [n['title'] for n in news]
    numbered = '\n'.join(f'{i+1}. {t}' for i, t in enumerate(titles))
    prompt = (
        '你是財經編輯。以下是今天的財經新聞標題，請針對每一則，用繁體中文寫「一句話」點出它對'
        '市場或投資人的意涵與重要性（每則不超過40字）。\n'
        '規則：\n'
        '- 只能根據標題本身與總體經濟常識推理，嚴禁杜撰標題沒有的具體數字、日期或事實。\n'
        '- 聚焦「所以呢／為什麼重要」，不要重複標題原文。\n'
        '- 每則只輸出一行，格式為「編號. 意涵」，編號需與輸入對應，不要加其他說明。\n\n'
        f'標題：\n{numbered}'
    )
    import time
    out = None
    for attempt in range(3):
        try:
            out = call_gemini(prompt)
            break
        except urllib.error.HTTPError as e:
            # 印出 Gemini 回傳的錯誤 body：429 的 body 會寫是哪個 quota metric/限額，
            # 用來判斷是「真的用量超標」還是「key 根本不是付費 key/專案沒綁計費」
            try:
                err_body = e.read().decode('utf-8', 'replace')[:500]
            except Exception:
                err_body = '(無法讀取錯誤內容)'
            print(f'   🔎 Gemini HTTP {e.code} 詳情: {err_body}')
            # 429=限流，退避重試；其餘 HTTP 錯誤直接放棄
            if e.code == 429 and attempt < 2:
                wait = 20 * (attempt + 1)
                print(f'   ⏳ Gemini 429 限流，{wait}s 後重試 ({attempt+1}/2)...')
                time.sleep(wait)
                continue
            print(f'   ⚠️ Gemini 重點摘要失敗（維持純連結）: HTTP {e.code}')
            return
        except Exception as e:
            print(f'   ⚠️ Gemini 重點摘要失敗（維持純連結）: {e}')
            return
    if out is None:
        return
    # 解析「編號. 意涵」，對回原新聞
    parsed = {}
    for line in out.splitlines():
        m = re.match(r'\s*(\d+)[\.\、\)]\s*(.+)', line.strip())
        if m:
            parsed[int(m.group(1))] = m.group(2).strip()
    filled = 0
    for i, n in enumerate(news, 1):
        s = parsed.get(i, '').strip()
        # 防呆：意涵若跟標題實質重複就不用
        if s and not _is_dup_desc(s, n['title']):
            n['description'] = s[:120]
            filled += 1
    print(f'   ✅ Gemini 產生 {filled}/{len(news)} 則重點摘要')


def _norm(s):
    """正規化：去掉空白與常見標點/分隔符，供標題與摘要比對是否實質相同"""
    return re.sub(r'[\s\-|｜–—:：,，。、!！?？“”"\'（）()【】\[\]]+', '', s or '').lower()


def _is_dup_desc(desc, title):
    """Google News RSS 的 description 幾乎都是「標題＋來源」的重複，不是真摘要。
    正規化後若摘要與標題互為包含關係，視為無效摘要（回傳 True，交由前端改用連結）。"""
    nd, nt = _norm(desc), _norm(title)
    if not nd:
        return True
    return nd == nt or nt in nd or nd in nt

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
                link_elem = item.find('link')

                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip()
                    # 去除 HTML 標籤
                    if '<' in title:
                        title = title.split('<')[0].strip()

                    url = link_elem.text.strip() if (link_elem is not None and link_elem.text) else ''

                    desc = ''
                    if desc_elem is not None and desc_elem.text:
                        desc = re.sub(r'<[^>]+>', '', desc_elem.text.strip())  # 移除 HTML 標籤
                        desc = (desc.replace('&amp;', '&').replace('&lt;', '<')
                                    .replace('&gt;', '>').replace('&quot;', '"').replace('&nbsp;', ' '))
                        desc = re.sub(r'\s+', ' ', desc).strip()

                    # 摘要若只是標題的重複就捨棄，前端改把標題做成新聞連結
                    if _is_dup_desc(desc, title):
                        desc = ''

                    if title and len(title) > 5:  # 跳過過短的標題
                        headlines.append({
                            'title': title[:100],
                            'description': desc[:200],
                            'url': url
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

                    # 嘗試找下一行的 description 與 link
                    desc = ''
                    url = ''
                    for j in range(i+1, min(i+10, len(lines))):
                        if '<description>' in lines[j] and not desc:
                            desc = lines[j].split('<description>')[1].split('</description>')[0].strip()
                            desc = re.sub(r'<[^>]+>', '', desc)
                            desc = desc.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ')
                            desc = re.sub(r'\s+', ' ', desc).strip()
                        if '<link>' in lines[j] and not url:
                            url = lines[j].split('<link>')[1].split('</link>')[0].strip()

                    if title and len(title) > 5 and title not in [h['title'] for h in headlines]:
                        if _is_dup_desc(desc, title):
                            desc = ''
                        headlines.append({
                            'title': title[:100],
                            'description': desc[:200],
                            'url': url
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

    # 新聞聚焦在風險儀表板追蹤的總經驅動因子(為什麼市場會動)，而非指數漲跌(市場概況已呈現)。
    # (分類, 查詢字串, 取幾則)
    news_sources = [
        ('貨幣政策', 'Fed 升息 降息 美國公債殖利率', 2),      # 對應第2層 總體貨幣環境
        ('通膨與景氣', '美國 通膨 CPI 經濟數據 衰退', 2),     # 對應第1/4層 估值與實體經濟
        ('全球風險', '全球經濟 央行 金融穩定 風險', 1),        # 綜合系統性風險
        ('台灣總經', '台股 外資 台幣匯率', 1),                # 對應第2層 USD/TWD、外資動向
    ]

    all_news = []
    seen = set()  # 跨分類去重(總經查詢常撈到同一則)，用網址優先、否則用標題
    for category, query, n in news_sources:
        print(f'📰 {category}: 正在抓取...')
        news = fetch_news_from_google(query, max_items=n)
        added = 0
        for item in news:
            key = item.get('url') or item.get('title')
            if key in seen:
                continue
            seen.add(key)
            all_news.append(item)
            added += 1
        print(f'   ✅ 取得 {added} 則')

    # 用 Gemini 為每則新聞產生一句話市場意涵（依標題判讀，非逐字摘要）
    print('\n🧠 產生新聞重點摘要...')
    summarize_headlines(all_news)

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
