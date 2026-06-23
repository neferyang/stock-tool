#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
為財務數據添加元數據（時間戳和真實性標記）
"""

import json
from datetime import datetime

def add_metadata_to_db():
    """為數據庫中的所有數據添加元數據"""

    with open('financial-data-complete.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    updated_count = 0

    # 為每支股票的每條數據添加元數據
    for code, stock in db['stocks'].items():
        for year_data in stock.get('data', []):
            year = year_data.get('year')

            # 檢查是否有真實數據
            has_real_data = year_data.get('source') is not None

            # 添加/更新元數據
            if has_real_data:
                # 真實數據
                year_data['updatedAt'] = year_data.get('updatedAt') or datetime.now().isoformat() + 'Z'
                year_data['source'] = year_data.get('source', 'MOPS')
                year_data['isEstimate'] = False
                year_data['dataType'] = '真實'
            else:
                # 待更新數據
                year_data['updatedAt'] = None
                year_data['source'] = None
                year_data['isEstimate'] = False
                year_data['dataType'] = '待更新'

            updated_count += 1

    # 保存更新
    with open('financial-data-complete.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"✅ 已添加元數據: {updated_count} 條數據")
    print(f"   • 時間戳: updatedAt")
    print(f"   • 數據來源: source")
    print(f"   • 真實性: isEstimate (false=真實, true=推估)")
    print(f"   • 數據類型: dataType (真實/待更新/推估)")

if __name__ == '__main__':
    add_metadata_to_db()
