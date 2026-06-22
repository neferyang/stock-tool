#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
準備季度財報更新 - 正確方式
從 FINANCIAL_DB 提取完整 5 年歷史數據，只更新最新年份
"""

import re
import json
import sys
from pathlib import Path
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

print("\n準備季度財報更新\n")

html = Path('index.html').read_text(encoding='utf-8')
start = html.find('const FINANCIAL_DB = {')
end = html.find('\n};', start) + 3
db_str = html[start:end]

# 目標股票
target_codes = ['2207', '3030', '2330', '1101', '2603', '2201']
extracted_data = {}

for code in target_codes:
    # 提取該股票的完整數據（包含所有年份）
    pattern = f'"({code})"' + r':\s*\{[^}]*?"name":\s*"([^"]*)"[^}]*?"data":\s*\[(.*?)\]'
    match = re.search(pattern, db_str, re.DOTALL)

    if match:
        name = match.group(2)
        data_str = '[' + match.group(3) + ']'

        try:
            data = json.loads(data_str)
            extracted_data[code] = {
                'name': name,
                'data': data  # 保留所有年份！
            }
            print(f"✓ {code} ({name}): {len(data)} 年數據 (最新: {data[0]['year']} EPS={data[0]['eps']})")
        except Exception as e:
            print(f"✗ {code}: {e}")
    else:
        print(f"✗ {code}: 未找到")

# 保存到模板
template_path = 'financial-data-template.json'
with open(template_path, 'r', encoding='utf-8') as f:
    template = json.load(f)

template['stocks'] = extracted_data
template['updatedAt'] = datetime.now().isoformat()
template['note'] = '包含完整 5 年歷史數據。編輯最新年份數據後運行 merge-financial-data.py'

with open(template_path, 'w', encoding='utf-8') as f:
    json.dump(template, f, ensure_ascii=False, indent=2)

print(f"\n✓ 已準備 {len(extracted_data)} 支股票的完整數據到 financial-data-template.json")
print(f"\n下一步：編輯最新年份的財報數據，然後運行 merge-financial-data.py")
