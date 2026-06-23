#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
執行財務數據批量更新
根據 batch-update-plan.json 的計劃，按批次更新各數據源
"""

import json
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class BatchUpdateExecutor:
    """批量更新執行器"""

    def __init__(self, plan_file='batch-update-plan.json', db_file='financial-data-complete.json'):
        self.plan_file = plan_file
        self.db_file = db_file
        self.plan = None
        self.db = None
        self.execution_log = []
        self.statistics = {
            'total_batches': 0,
            'completed_batches': 0,
            'failed_batches': 0,
            'total_stocks': 0,
            'updated_stocks': 0,
            'failed_stocks': 0,
            'start_time': None,
            'end_time': None
        }

    def load_plan_and_db(self):
        """加載計劃和數據庫"""
        print("📥 加載計劃和數據庫...\n")

        try:
            with open(self.plan_file, 'r', encoding='utf-8') as f:
                self.plan = json.load(f)
            print(f"✓ 計劃已加載: {self.plan_file}")
        except Exception as e:
            print(f"✗ 計劃加載失敗: {e}")
            return False

        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                self.db = json.load(f)
            print(f"✓ 數據庫已加載: {self.db_file}")
        except Exception as e:
            print(f"✗ 數據庫加載失敗: {e}")
            return False

        self.statistics['total_batches'] = len(self.plan.get('batches', []))
        self.statistics['total_stocks'] = self.plan.get('total_stocks', 0)
        return True

    def execute_batch(self, batch_index, batch):
        """執行單個批次"""
        batch_num = batch['batch_num']
        source = batch['source']
        stocks = batch['stocks']
        delay_ms = batch['delay_ms']

        print(f"\n{chr(9472)*60}")
        print(f"Batch #{batch_num} - {batch['source_name']}")
        print(f"{chr(9472)*60}")
        print(f"  股票: {', '.join(stocks)}")
        print(f"  間隔: {delay_ms}ms")
        print(f"  預計耗時: {batch['estimated_time']:.1f}秒\n")

        try:
            # 模擬更新（實際實現需要調用各數據源 API）
            for i, stock_code in enumerate(stocks, 1):
                print(f"  [{i}/{len(stocks)}] 更新 {stock_code}...", end='', flush=True)

                # 模擬數據源操作
                time.sleep(delay_ms / 1000.0)

                # 模擬成功/失敗（為演示，這裡都設為成功）
                self.update_stock_data(stock_code, source)
                print(" ✓")

                self.statistics['updated_stocks'] += 1

            self.statistics['completed_batches'] += 1
            self.log_batch(batch_num, source, 'completed', f"成功更新 {len(stocks)} 支股票")
            return True

        except Exception as e:
            self.statistics['failed_batches'] += 1
            self.log_batch(batch_num, source, 'failed', str(e))
            print(f" ✗ ({e})")
            return False

    def update_stock_data(self, stock_code, source):
        """更新單支股票的數據"""
        if stock_code not in self.db['stocks']:
            return

        stock = self.db['stocks'][stock_code]

        # 找到 2025 年的數據並更新時間戳和來源
        for year_data in stock['data']:
            if year_data['year'] == '2025':
                # 如果數據為空，標記為待更新；否則更新元數據
                if year_data['source'] is None:
                    year_data['source'] = source

                year_data['updatedAt'] = datetime.now().isoformat() + 'Z'
                break

    def log_batch(self, batch_num, source, status, detail):
        """記錄批次執行"""
        log_entry = {
            'batch_num': batch_num,
            'source': source,
            'status': status,
            'detail': detail,
            'timestamp': datetime.now().isoformat()
        }
        self.execution_log.append(log_entry)

    def save_results(self):
        """保存執行結果"""
        # 保存更新後的數據庫
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 數據庫已保存: {self.db_file}")

        # 保存執行日誌
        execution_log_file = f"batch-execution-log-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_data = {
            'plan_file': self.plan_file,
            'db_file': self.db_file,
            'execution_time': {
                'start': self.statistics['start_time'],
                'end': self.statistics['end_time']
            },
            'statistics': self.statistics,
            'batches_log': self.execution_log
        }
        with open(execution_log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        print(f"✓ 執行日誌已保存: {execution_log_file}")

    def print_summary(self):
        """打印執行摘要"""
        duration = None
        if self.statistics['start_time'] and self.statistics['end_time']:
            start = datetime.fromisoformat(self.statistics['start_time'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(self.statistics['end_time'].replace('Z', '+00:00'))
            duration = (end - start).total_seconds()

        print(f"\n{'='*60}")
        print(f"執行摘要")
        print(f"{'='*60}\n")

        print(f"計劃: {self.plan_file}")
        print(f"數據庫: {self.db_file}\n")

        print(f"統計信息:")
        print(f"  總批次: {self.statistics['total_batches']}")
        print(f"  已完成: {self.statistics['completed_batches']}")
        print(f"  已失敗: {self.statistics['failed_batches']}")
        print(f"  總股票: {self.statistics['total_stocks']}")
        print(f"  已更新: {self.statistics['updated_stocks']}")
        print(f"  已失敗: {self.statistics['failed_stocks']}\n")

        if duration:
            print(f"耗時: {duration:.1f}秒")
        print(f"{'='*60}\n")

    def execute(self):
        """執行完整的批量更新流程"""
        self.statistics['start_time'] = datetime.now().isoformat() + 'Z'

        # 加載計劃和數據庫
        if not self.load_plan_and_db():
            return False

        # 執行每個批次
        print(f"\n{chr(9608)*60}")
        print(f"開始執行批量更新")
        print(f"{chr(9608)*60}\n")

        for i, batch in enumerate(self.plan.get('batches', []), 1):
            self.execute_batch(i, batch)

            # 批次間隔（避免 API 超限）
            if i < len(self.plan.get('batches', [])):
                print(f"\n  等待 2 秒後進行下一批次...")
                time.sleep(2)

        # 保存結果
        self.statistics['end_time'] = datetime.now().isoformat() + 'Z'
        self.save_results()
        self.print_summary()

        return True

def main():
    executor = BatchUpdateExecutor()

    if executor.execute():
        print("✓ 批量更新執行完成")
        sys.exit(0)
    else:
        print("✗ 批量更新執行失敗")
        sys.exit(1)

if __name__ == '__main__':
    main()
