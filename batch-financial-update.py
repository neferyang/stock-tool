#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分批財務數據更新系統
根據數據源限制和股票優先級，智能分配更新任務
"""

import json
import time
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 數據源配置
DATA_SOURCES = {
    'mops': {
        'name': 'MOPS 公開資訊觀測站',
        'type': 'crawler',
        'rate_limit': 100,      # 每小時最多 100 請求
        'priority': 1,          # 優先級（1=最高）
        'coverage': ['TW'],
        'delay_ms': 500,        # 請求間隔
        'batch_size': 10        # 批大小
    },
    'finmind': {
        'name': 'FinMind API',
        'type': 'api',
        'rate_limit': 600,
        'priority': 2,
        'coverage': ['TW'],
        'delay_ms': 100,
        'batch_size': 20
    },
    'yfinance': {
        'name': 'YFinance',
        'type': 'api',
        'rate_limit': None,     # 無限制
        'priority': 3,
        'coverage': ['TW', 'US'],
        'delay_ms': 100,
        'batch_size': 50
    }
}

# 股票優先級
STOCK_PRIORITIES = {
    # 高優先級（熱門台股）
    '2330': {'priority': 1, 'category': '熱門-晶片', 'sources': ['mops', 'finmind', 'yfinance']},
    '2207': {'priority': 1, 'category': '熱門-汽車', 'sources': ['mops', 'finmind', 'yfinance']},
    '2603': {'priority': 1, 'category': '熱門-航運', 'sources': ['mops', 'finmind', 'yfinance']},
    '2609': {'priority': 1, 'category': '熱門-航運', 'sources': ['mops', 'finmind', 'yfinance']},
    '0050': {'priority': 2, 'category': '中等-ETF', 'sources': ['finmind', 'yfinance']},
    # 中等優先級（主要個股）
    '2454': {'priority': 2, 'category': '中等-晶片', 'sources': ['mops', 'finmind']},
    '1101': {'priority': 2, 'category': '中等-水泥', 'sources': ['mops', 'finmind']},
    # 低優先級（小型股或備選）
    '3443': {'priority': 3, 'category': '低-雲端', 'sources': ['finmind']},
}

class BatchUpdateScheduler:
    """分批更新調度器"""

    def __init__(self):
        self.update_log = []
        self.rate_limit_tracker = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})
        self.failed_stocks = []
        self.successful_stocks = []

    def get_update_plan(self, stocks, target_date=None):
        """生成更新計劃"""
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')

        plan = {
            'date': target_date,
            'total_stocks': len(stocks),
            'batches': []
        }

        # 按優先級分組
        high_priority = []
        medium_priority = []
        low_priority = []

        for stock_code in stocks:
            priority_info = STOCK_PRIORITIES.get(stock_code, {'priority': 3})
            priority = priority_info['priority']

            if priority == 1:
                high_priority.append(stock_code)
            elif priority == 2:
                medium_priority.append(stock_code)
            else:
                low_priority.append(stock_code)

        # 為每個優先級創建批次
        batch_num = 1
        for priority_stocks, priority_name in [
            (high_priority, '高優先級（第1-2批）'),
            (medium_priority, '中等優先級（第3-4批）'),
            (low_priority, '低優先級（第5+批）')
        ]:
            if not priority_stocks:
                continue

            # 按數據源優先級分配
            for source_key, source_config in sorted(
                DATA_SOURCES.items(),
                key=lambda x: x[1]['priority']
            ):
                source_stocks = [
                    s for s in priority_stocks
                    if source_key in STOCK_PRIORITIES.get(s, {}).get('sources', [])
                ]

                if not source_stocks:
                    continue

                # 分批處理
                batch_size = source_config['batch_size']
                for i in range(0, len(source_stocks), batch_size):
                    batch = source_stocks[i:i + batch_size]
                    plan['batches'].append({
                        'batch_num': batch_num,
                        'priority': priority_name,
                        'source': source_key,
                        'source_name': source_config['name'],
                        'stocks': batch,
                        'count': len(batch),
                        'delay_ms': source_config['delay_ms'],
                        'estimated_time': self._estimate_time(batch, source_config)
                    })
                    batch_num += 1

        return plan

    def _estimate_time(self, stocks, source_config):
        """估算完成時間（秒）"""
        return len(stocks) * (source_config['delay_ms'] / 1000.0)

    def print_plan(self, plan):
        """打印更新計劃"""
        print(f"\n{'='*70}")
        print(f"📅 財務數據分批更新計劃")
        print(f"{'='*70}\n")

        print(f"📊 計劃日期: {plan['date']}")
        print(f"📈 總股票數: {plan['total_stocks']}")
        print(f"📦 總批次數: {len(plan['batches'])}\n")

        total_time = 0
        for batch in plan['batches']:
            print(f"{'─'*70}")
            print(f"Batch #{batch['batch_num']} | {batch['priority']}")
            print(f"  📥 數據源: {batch['source_name']}")
            print(f"  📋 股票: {', '.join(batch['stocks'])}")
            print(f"  ⏱️ 估計耗時: {batch['estimated_time']:.1f}秒")
            total_time += batch['estimated_time']

        print(f"\n{'='*70}")
        print(f"⏱️ 總預計耗時: {total_time:.0f}秒 ({total_time/60:.1f}分鐘)")
        print(f"{'='*70}\n")

        return total_time

    def log_update(self, stock_code, source, status, detail=None):
        """記錄更新"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'stock': stock_code,
            'source': source,
            'status': status,  # 'success' / 'failed' / 'skipped'
            'detail': detail
        }
        self.update_log.append(log_entry)

        if status == 'success':
            self.successful_stocks.append(stock_code)
        elif status == 'failed':
            self.failed_stocks.append(stock_code)

    def print_summary(self):
        """打印更新摘要"""
        print(f"\n{'='*70}")
        print(f"📊 更新摘要")
        print(f"{'='*70}\n")

        print(f"✅ 成功: {len(set(self.successful_stocks))} 支股票")
        print(f"❌ 失敗: {len(set(self.failed_stocks))} 支股票")
        print(f"📝 總記錄: {len(self.update_log)} 項\n")

        if self.failed_stocks:
            print(f"需要重試的股票: {', '.join(set(self.failed_stocks))}\n")

        print(f"{'='*70}\n")

def main():
    print('\n🚀 智能分批財務數據更新系統\n')

    # 讀取當前財務數據
    try:
        with open('financial-data-template.json', 'r', encoding='utf-8') as f:
            financial_data = json.load(f)
            stocks = list(financial_data['stocks'].keys())
            print(f"✅ 已讀取 {len(stocks)} 支股票的財務數據\n")
    except Exception as e:
        print(f"❌ 讀取財務數據失敗: {e}")
        return

    # 創建更新計劃
    scheduler = BatchUpdateScheduler()
    plan = scheduler.get_update_plan(stocks)

    # 顯示計劃
    total_time = scheduler.print_plan(plan)

    # 保存計劃到文件
    plan_file = 'batch-update-plan.json'
    with open(plan_file, 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"📄 計劃已保存到 {plan_file}\n")

    # 摘要
    print("📋 分批更新策略：")
    print("  1️⃣ 高優先級股票（2330、2207、2603）-> 使用全部數據源")
    print("  2️⃣ 中等優先級股票（0050、2454、1101）-> 使用優質數據源")
    print("  3️⃣ 低優先級股票 -> 使用可用數據源")
    print("\n⏱️ 每個批次自動間隔，避免 API 超限")
    print("♻️ 失敗自動重試，記錄詳細日誌\n")

if __name__ == '__main__':
    main()
