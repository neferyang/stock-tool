#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將 FinMind API 獲取的真實數據導入 FINANCIAL_DB
"""

import json
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

print("\n從 FinMind 數據導入到 FINANCIAL_DB\n")

# 讀取 FinMind 數據
try:
    with open('finmind-real-data.json', 'r', encoding='utf-8') as f:
        finmind_data = json.load(f)
except FileNotFoundError:
    print("❌ 找不到 finmind-real-data.json")
    print("   請先執行 finmind-data-fetcher.py 獲取數據")
    sys.exit(1)

print(f"✅ 已讀取 FinMind 數據：{len(finmind_data.get('stocks', {}))} 支股票\n")

# 讀取 index.html
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 尋找 FINANCIAL_DB 位置
db_start = html.find('const FINANCIAL_DB = {')
if db_start == -1:
    print("❌ 找不到 FINANCIAL_DB")
    sys.exit(1)

# 找到結束位置
db_content_start = html.find('{', db_start)
brace_count = 0
db_end = db_content_start
in_string = False
escape = False

for i in range(db_content_start, len(html)):
    c = html[i]

    if escape:
        escape = False
        continue

    if c == '\\' and in_string:
        escape = True
        continue

    if c == '"' and not in_string:
        in_string = True
    elif c == '"' and in_string:
        in_string = False
    elif c == '{' and not in_string:
        brace_count += 1
    elif c == '}' and not in_string:
        brace_count -= 1
        if brace_count == 0:
            db_end = i + 1
            break

# 解析現有 FINANCIAL_DB
existing_db_start = html.find('const FINANCIAL_DB = {') + len('const FINANCIAL_DB = ')
existing_db_content = html[existing_db_start:db_end]

try:
    financial_db = json.loads(existing_db_content)
except:
    print("⚠️ 解析現有 FINANCIAL_DB 失敗，將從空開始")
    financial_db = {}

# 導入 FinMind 數據
imported_count = 0
updated_count = 0

print("導入進度：\n")

for stock_code, stock_data in finmind_data.get('stocks', {}).items():
    data_array = stock_data.get('data', [])

    if not data_array:
        print(f"{stock_code}: ⚠️ 無數據")
        continue

    if stock_code not in financial_db:
        print(f"{stock_code}: ✅ 新增股票")
        imported_count += 1
        financial_db[stock_code] = {
            "name": stock_data.get('name', ''),
            "type": "上市",
            "data": []
        }
    else:
        print(f"{stock_code}: 🔄 更新現有股票")
        updated_count += 1

    # 整合數據
    financial_db[stock_code]['data'] = data_array

    # 按年份升序排列
    financial_db[stock_code]['data'].sort(key=lambda x: int(str(x.get('year', '0'))))

    # 列印樣本
    if data_array:
        years_str = ' → '.join([str(d.get('year', '')) for d in data_array])
        print(f"   └─ 年份：{years_str}")

print(f"\n{'='*60}")
print(f"導入完成：新增 {imported_count} 支，更新 {updated_count} 支")
print(f"{'='*60}\n")

# 生成新的 FINANCIAL_DB JSON
new_db_json = json.dumps(financial_db, ensure_ascii=False, indent=3)
new_db_section = f'const FINANCIAL_DB = {new_db_json};'

# 替換 HTML 中的 FINANCIAL_DB
html = html[:db_start] + new_db_section + html[db_end:]

# 保存
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ 已保存到 index.html\n")

# 統計信息
print("統計信息：")
print(f"  FINANCIAL_DB 中股票總數：{len(financial_db)}")
print(f"  本次導入的真實數據股票：{imported_count + updated_count}")
print(f"\n✨ FinMind 真實數據已成功導入系統！")
