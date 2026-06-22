#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""將 FinMind 200 支股票數據導入 FINANCIAL_DB"""

import json
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("\n從 FinMind 數據導入到 FINANCIAL_DB\n")

try:
    with open('finmind-real-data-200.json', 'r', encoding='utf-8') as f:
        finmind_data = json.load(f)
except FileNotFoundError:
    print("找不到 finmind-real-data-200.json")
    sys.exit(1)

print(f"已讀取 FinMind 數據：{len(finmind_data.get('stocks', {}))} 支股票\n")

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

db_start = html.find('const FINANCIAL_DB = {')
if db_start == -1:
    print("找不到 FINANCIAL_DB")
    sys.exit(1)

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
    if c == '\' and in_string:
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

existing_db_start = html.find('const FINANCIAL_DB = {') + len('const FINANCIAL_DB = ')
existing_db_content = html[existing_db_start:db_end]

try:
    financial_db = json.loads(existing_db_content)
except:
    financial_db = {}

imported_count = 0
updated_count = 0

print("導入進度：\n")

for stock_code, stock_data in finmind_data.get('stocks', {}).items():
    data_array = stock_data.get('data', [])

    if not data_array:
        continue

    if stock_code not in financial_db:
        imported_count += 1
        financial_db[stock_code] = {"name": stock_data.get('name', ''), "type": "上市", "data": []}
    else:
        updated_count += 1

    financial_db[stock_code]['data'] = data_array
    financial_db[stock_code]['data'].sort(key=lambda x: int(str(x.get('year', '0'))))

    if (imported_count + updated_count) % 50 == 0:
        print(f"已處理 {imported_count + updated_count} 支股票...", flush=True)

new_db_json = json.dumps(financial_db, ensure_ascii=False, indent=3)
new_db_section = f'const FINANCIAL_DB = {new_db_json};'

html = html[:db_start] + new_db_section + html[db_end:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n{'='*60}")
print(f"導入完成：新增 {imported_count} 支，更新 {updated_count} 支")
print(f"{'='*60}\n")

print("統計信息：")
print(f"  FINANCIAL_DB 中股票總數：{len(financial_db)}")
print(f"  本次導入的股票：{imported_count + updated_count}")
print(f"\n✨ 200 支股票數據已成功導入系統！")
