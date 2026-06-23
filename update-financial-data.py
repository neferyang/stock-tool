#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股財報數據更新腳本
從 FinMind API 獲取最新財務指標，更新 FINANCIAL_DB
"""

import requests
import json
import sys
from datetime import datetime
import time

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

print("\n" + "="*60)
print("台股財報數據更新")
print("="*60)

# FinMind API 設定
FINMIND_API = "https://api.finmindtrade.com/v1/data"
FINMIND_DATASETS = {
    'TaiwanStockFinancialStatements': '財務報表數據',
    'TaiwanStockMonthRevenue': '月營收',
    'TaiwanStockEPS': 'EPS',
}

def fetch_financial_data(stock_code):
    """從 FinMind 獲取單支股票的財務數據"""
    try:
        # 使用免費 API（無需 token）
        url = FINMIND_API
        params = {
            'dataset': 'TaiwanStockFinancialStatements',
            'data_id': stock_code,
            'response': 'json'
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('data'):
                # 返回最近 5 年的數據
                records = sorted(data['data'], key=lambda x: x.get('year', '0'), reverse=True)[:5]
                return records
        return None
    except Exception as e:
        print(f"  [WARN] {stock_code}: {e}")
        return None

def parse_financial_record(record):
    """解析 FinMind 財務數據記錄"""
    try:
        # FinMind 返回的欄位名稱可能不同，需要映射
        return {
            'year': record.get('year', record.get('date', '')[:4]),
            'eps': float(record.get('EPS', record.get('eps', 0)) or 0),
            'roe': float(record.get('ROE', record.get('roe', 0)) or 0),
            'netMargin': float(record.get('NetMargin', record.get('net_margin', 0)) or 0),
            'debtRatio': float(record.get('DebtRatio', record.get('debt_ratio', 0)) or 0),
            'operatingMargin': float(record.get('OperatingMargin', record.get('operating_margin', 0)) or 0),
            'revenue': float(record.get('Revenue', record.get('revenue', 0)) or 0),
            'netIncome': float(record.get('NetIncome', record.get('net_income', 0)) or 0),
            'operatingIncome': float(record.get('OperatingIncome', record.get('operating_income', 0)) or 0),
            'fcf': float(record.get('FreeCashFlow', record.get('fcf', 0)) or 0),
        }
    except Exception as e:
        print(f"    解析失敗: {e}")
        return None

def update_financial_db(html_path, stock_codes):
    """更新 HTML 文件中的 FINANCIAL_DB"""
    print(f"\n讀取 {html_path}...")
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 查找 FINANCIAL_DB 的位置
    db_start = html.find('const FINANCIAL_DB = {')
    if db_start == -1:
        print("❌ 找不到 FINANCIAL_DB")
        return False

    updated_count = 0
    for code in stock_codes:
        print(f"\n更新 {code}...")

        # 獲取財報數據
        records = fetch_financial_data(code)
        if not records:
            print(f"  ⚠️ 無法獲取數據")
            continue

        # 解析數據
        parsed = []
        for rec in records:
            p = parse_financial_record(rec)
            if p:
                parsed.append(p)

        if not parsed:
            print(f"  ⚠️ 解析失敗")
            continue

        # 在 FINANCIAL_DB 中查找該股票
        code_marker = f'"{code}":'
        code_pos = html.find(code_marker, db_start)

        if code_pos == -1:
            print(f"  ℹ️ 股票不在 DB 中（跳過）")
            continue

        # 找到該股票的 data 陣列
        data_start = html.find('"data": [', code_pos)
        data_end = html.find(']', data_start) + 1

        if data_start == -1:
            print(f"  ⚠️ 找不到 data 陣列")
            continue

        # 生成新的 data 陣列
        new_data = json.dumps(parsed, ensure_ascii=False, indent=3)
        new_data_section = f'"data": {new_data}'

        # 替換
        html = html[:data_start] + new_data_section + html[data_end:]
        updated_count += 1
        print(f"  ✅ 已更新（{len(parsed)} 年度數據）")

        # 避免 API 限流
        time.sleep(1)

    if updated_count > 0:
        print(f"\n保存修改... ({updated_count} 家公司)")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ 完成")
        return True
    else:
        print("\n❌ 無任何更新")
        return False

# 主程序
if __name__ == '__main__':
    # 目標股票代碼（可擴展）
    TARGET_STOCKS = [
        '2207',  # 和泰車
        '3030',  # 德律
        '2330',  # 台積電
        '1101',  # 台泥
        '2603',  # 長榮
    ]

    html_file = 'index.html'

    if update_financial_db(html_file, TARGET_STOCKS):
        print(f"\n更新時間: {datetime.now().isoformat()}")
    else:
        sys.exit(1)
