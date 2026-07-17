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
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-flash-latest')


def call_gemini(prompt):
    """呼叫 Google Gemini API；與 generate-market-analysis.py 同一套。"""
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}'
    body = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        # gemini-2.5 系列預設開啟 thinking，會吃掉 maxOutputTokens 導致實際輸出被截斷；
        # 這種格式化短輸出的任務不需要 thinking，設 thinkingBudget=0 關閉並拉高 token 上限。
        'generationConfig': {
            'maxOutputTokens': 2048,
            'temperature': 0.3,
            'thinkingConfig': {'thinkingBudget': 0},
        },
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

NUMBER_EMOJI = ['1️⃣', '2️⃣', '3️⃣']


def generate_observations_rule_based(markets_data):
    """規則式備援：Gemini 不可用時的最低限度版本，不牽涉真實數字判讀。"""
    observations = []
    try:
        if 'US' in markets_data:
            us_data = markets_data['US']
            change_sum = sum([m.get('change', 0) for m in us_data.values()])
            avg_change = change_sum / len(us_data) if us_data else 0
            if avg_change > 1:
                title, content = '美股全面上漲', '美股三大指數普漲，市場情緒偏樂觀，科技股表現亮眼。'
            elif avg_change < -1:
                title, content = '美股回檔調整', '美股出現調整，投資人謹慎情緒升溫，避險資金流入。'
            else:
                title, content = '美股漲跌互見', '美股三大指數表現分化，市場等待政策方向明確。'
            observations.append({'emoji': NUMBER_EMOJI[0], 'title': title, 'content': content})

        if 'JP' in markets_data or 'TW' in markets_data:
            observations.append({'emoji': NUMBER_EMOJI[1], 'title': '亞股跟風美股',
                                  'content': '亞股走勢跟隨美股，日股和台股表現受美股指引。'})

        if 'GOLD' in markets_data:
            observations.append({'emoji': NUMBER_EMOJI[2], 'title': '貴金屬波動',
                                  'content': '黃金價格波動，受美元走勢和風險情緒影響。'})
    except Exception as e:
        print(f'⚠️ 規則式觀察生成失敗: {e}')
    return observations


def generate_observations(markets_data, news, indices_flat):
    """歸納「今日觀察」3點：1.最大價格異常/悖論 2.最大地緣政治/外部風險 3.最關鍵總經數據矛盾/Fed訊號。
    餵真實市場數字(indices_flat 的 displayStr，已含漲跌%)＋新聞標題與其一句話意涵給 Gemini 歸納，
    嚴禁捏造輸入數據沒有的具體數字；Gemini 不可用或解析失敗則 fallback 回規則式版本。"""
    if not GEMINI_API_KEY or not news:
        if not GEMINI_API_KEY:
            print('   ⚠️ GEMINI_API_KEY 未設定，今日觀察改用規則式備援')
        return generate_observations_rule_based(markets_data)

    market_lines = '\n'.join(f"- {v['name']}：{v.get('displayStr', '')}" for v in indices_flat.values())
    news_lines = '\n'.join(
        f"- {n['title']}" + (f"（意涵：{n['description']}）" if n.get('description') else '')
        for n in news
    )
    prompt = (
        '你是財經編輯，請從以下「真實市場數據」與「今日新聞」中，歸納出3個最值得投資人關注的'
        '觀察重點，作為每日財金早報的結尾區塊。\n\n'
        '選材邏輯（依序對應第1、2、3點）：\n'
        '1. 當天最大的價格異常或市場悖論（例如利多出盡、暴跌反彈、預期與結果背離）\n'
        '2. 最大的地緣政治或外部風險變數\n'
        '3. 最關鍵的總經數據矛盾或 Fed 政策訊號\n\n'
        '格式規則：\n'
        '- 每點有 title（4-6字關鍵詞）與 body（1句話，20-30字，點出矛盾或影響，不要重複標題）\n'
        '- 3點合計不超過150字，繁體中文，語氣精煉直白、不用敬語\n'
        '- 只能引用下方數據與新聞裡出現過的數字/事實，嚴禁捏造未提及的具體數字、日期\n'
        '- 若某一類找不到明顯素材，改選次要但仍具體的觀察，不要硬套或留白\n\n'
        f'真實市場數據：\n{market_lines}\n\n'
        f'今日新聞：\n{news_lines}\n\n'
        '請直接輸出 JSON 陣列（不要加 ```json 或其他說明文字），格式：\n'
        '[{"title":"...","body":"..."},{"title":"...","body":"..."},{"title":"...","body":"..."}]'
    )

    import time
    raw = None
    for attempt in range(3):
        try:
            raw = call_gemini(prompt)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                wait = 20 * (attempt + 1)
                print(f'   ⏳ Gemini 429 限流，{wait}s 後重試 ({attempt+1}/2)...')
                time.sleep(wait)
                continue
            print(f'   ⚠️ 今日觀察 Gemini 失敗（改用規則式備援）: HTTP {e.code}')
            return generate_observations_rule_based(markets_data)
        except Exception as e:
            print(f'   ⚠️ 今日觀察 Gemini 失敗（改用規則式備援）: {e}')
            return generate_observations_rule_based(markets_data)

    try:
        cleaned = re.sub(r'^```(json)?|```$', '', raw.strip(), flags=re.MULTILINE).strip()
        items = json.loads(cleaned)
        observations = []
        for i, item in enumerate(items[:3]):
            title = str(item.get('title', '')).strip()[:12]
            body = str(item.get('body', '')).strip()[:60]
            if title and body:
                observations.append({'emoji': NUMBER_EMOJI[i], 'title': title, 'content': body})
        if len(observations) < 3:
            raise ValueError(f'只解析出 {len(observations)} 點，不足3點')
        print(f'   ✅ Gemini 產生 {len(observations)} 點今日觀察')
        return observations
    except Exception as e:
        print(f'   ⚠️ 今日觀察解析失敗（改用規則式備援）: {e}')
        return generate_observations_rule_based(markets_data)

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
        indices_flat = market_data_raw.get('indices', {})
        # 按 group 分組（規則式備援用）
        markets_by_group = {}
        for symbol, data in indices_flat.items():
            group = data.get('group', 'OTHER')
            markets_by_group.setdefault(group, {})[symbol] = data

        print('\n💡 產生今日觀察...')
        observations = generate_observations(markets_by_group, all_news, indices_flat)
        print(f'   已生成 {len(observations)} 個觀察')

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
