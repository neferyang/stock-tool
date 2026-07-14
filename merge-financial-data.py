#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合併財報數據到 index.html
從 financial-data-mops.json 讀取，更新 index.html 的 FINANCIAL_DB
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

print("\n" + "="*70)
print("合併財報數據到 FINANCIAL_DB")
print("="*70 + "\n")

def merge_financial_data(html_path, json_path):
    """
    從 JSON 檔案讀取最新財報，更新 HTML 中的 FINANCIAL_DB
    """

    # 讀取財報數據
    print(f"讀取財報數據: {json_path}")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            financial_source = json.load(f)
    except FileNotFoundError:
        print(f"❌ 找不到 {json_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失敗: {e}")
        return False

    # 讀取 HTML
    print(f"讀取 HTML: {html_path}")
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 查找 FINANCIAL_DB 位置
    db_start = html.find('const FINANCIAL_DB = {')
    if db_start == -1:
        print("❌ 找不到 FINANCIAL_DB")
        return False

    print(f"\n開始合併 {len(financial_source.get('stocks', {}))} 支股票...\n")

    updated_count = 0

    # 對每支股票進行更新
    for stock_code, stock_info in financial_source.get('stocks', {}).items():
        if not stock_info.get('data'):
            print(f"{stock_code}: ⚠️ 無數據，跳過")
            continue

        # 在 FINANCIAL_DB 中查找該股票
        code_marker = f'"{stock_code}":'
        code_pos = html.find(code_marker, db_start)

        if code_pos == -1:
            print(f"{stock_code}: ℹ️ 不在 FINANCIAL_DB 中")
            continue

        # 找到 "data": [ 的位置
        data_array_start = html.find('"data": [', code_pos)
        if data_array_start == -1:
            print(f"{stock_code}: ⚠️ 找不到 data 陣列")
            continue

        # 找到 ] 的位置（關閉 data 陣列）
        # 需要找到對應的 ] （配對的括號）
        bracket_count = 0
        pos = data_array_start + len('"data": [')
        while pos < len(html):
            if html[pos] == '[':
                bracket_count += 1
            elif html[pos] == ']':
                if bracket_count == 0:
                    data_array_end = pos + 1
                    break
                bracket_count -= 1
            pos += 1
        else:
            print(f"{stock_code}: ⚠️ 找不到 data 陣列結尾")
            continue

        # 生成新的 data 陣列 JSON
        new_data_json = json.dumps(stock_info['data'], ensure_ascii=False, indent=3)

        # 替換
        new_data = f'"data": {new_data_json}'

        html = html[:data_array_start] + new_data + html[data_array_end:]
        updated_count += 1

        # 顯示更新內容
        latest_year = stock_info['data'][0]['year']
        latest_eps = stock_info['data'][0]['eps']
        latest_roe = stock_info['data'][0]['roe']
        data_years = len(stock_info['data'])
        print(f"{stock_code}: ✅ 已更新 ({latest_year} EPS={latest_eps}, ROE={latest_roe}%, {data_years}年數據)")

    if updated_count == 0:
        print("❌ 沒有任何更新")
        return False

    # 保存更新
    print(f"\n保存修改到 {html_path}...")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ 完成 - 更新 {updated_count} 支股票")
    return True

if __name__ == '__main__':
    html_file = 'index.html'
    json_file = 'financial-data-mops.json'

    if merge_financial_data(html_file, json_file):
        print(f"\n更新時間: {datetime.now().isoformat()}")
        print("="*70)
    else:
        print("="*70)
        sys.exit(1)
