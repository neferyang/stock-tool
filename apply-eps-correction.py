#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
應用 EPS 修正 - 只修正 5 年 EPS 趨勢異常的股票
保留其他診斷卡的數據不變
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

print("\n應用 EPS 修正到 FINANCIAL_DB\n")

# 讀取修正數據
correction_path = 'eps-correction-template.json'
try:
    with open(correction_path, 'r', encoding='utf-8') as f:
        corrections = json.load(f)
except FileNotFoundError:
    print(f"ERROR: 找不到 {correction_path}")
    sys.exit(1)

# 讀取 HTML
html_path = 'index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

print(f"處理 {len(corrections.get('corrections', {}))} 支股票\n")

updated_count = 0

for stock_code, correction_data in corrections.get('corrections', {}).items():
    # 檢查是否有有效的修正數據
    has_valid_data = any(
        item.get('eps', 0) > 0
        for item in correction_data.get('historicalEPS', [])
    )

    if not has_valid_data:
        print(f"{stock_code}: ⚠️ 跳過 - 無有效 EPS 數據")
        continue

    # 在 FINANCIAL_DB 中查找該股票
    db_start = html.find('const FINANCIAL_DB = {')
    code_marker = f'"{stock_code}":'
    code_pos = html.find(code_marker, db_start)

    if code_pos == -1:
        print(f"{stock_code}: ⚠️ 股票不在 FINANCIAL_DB 中")
        continue

    # 找到 "data": [ 的位置
    data_array_start = html.find('"data": [', code_pos)
    if data_array_start == -1:
        print(f"{stock_code}: ⚠️ 找不到 data 陣列")
        continue

    # 找到對應的 ] 位置
    bracket_count = 0
    pos = data_array_start + len('"data": [')
    data_array_end = -1

    while pos < len(html):
        if html[pos] == '[':
            bracket_count += 1
        elif html[pos] == ']':
            if bracket_count == 0:
                data_array_end = pos + 1
                break
            bracket_count -= 1
        pos += 1

    if data_array_end == -1:
        print(f"{stock_code}: ⚠️ 找不到 data 陣列結尾")
        continue

    # 提取原有的 data 陣列
    data_str = html[data_array_start + len('"data": '):data_array_end]
    try:
        original_data = json.loads(data_str)
    except json.JSONDecodeError:
        print(f"{stock_code}: ⚠️ JSON 解析失敗")
        continue

    # 應用 EPS 修正
    corrected_data = []
    for item in original_data:
        item_year = str(item.get('year', ''))

        # 查找修正數據中是否有該年份
        correction_found = False
        for correction_item in correction_data.get('historicalEPS', []):
            if str(correction_item.get('year', '')) == item_year:
                if correction_item.get('eps', 0) > 0:
                    # 應用修正的 EPS
                    item['eps'] = correction_item['eps']
                    corrected_data.append(item)
                    correction_found = True
                    break

        if not correction_found:
            # 沒有修正數據，保留原值
            corrected_data.append(item)

    # 生成新的 data 陣列
    new_data_json = json.dumps(corrected_data, ensure_ascii=False, indent=3)
    new_data_section = f'"data": {new_data_json}'

    # 替換
    html = html[:data_array_start] + new_data_section + html[data_array_end:]
    updated_count += 1

    print(f"{stock_code}: ✅ 已應用 EPS 修正")
    for item in corrected_data:
        print(f"   {item['year']}: EPS={item['eps']}")

if updated_count == 0:
    print("❌ 無任何修正被應用")
    sys.exit(1)

# 保存
print(f"\n保存修改到 {html_path}...")
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ 完成 - 已應用 {updated_count} 支股票的 EPS 修正\n")
