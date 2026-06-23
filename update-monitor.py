#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動更新監控工具
定期檢查更新進度並生成進度報告
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class UpdateMonitor:
    """更新監控工具"""

    def __init__(self):
        self.db_file = 'financial-data-complete.json'
        self.status_file = 'UPDATE-STATUS.json'
        self.log_pattern = 'batch-execution-log-*.json'

    def get_latest_log(self):
        """獲取最新的執行日誌"""
        import glob
        logs = sorted(glob.glob(self.log_pattern), reverse=True)
        if logs:
            try:
                with open(logs[0], 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None

    def calculate_progress(self):
        """計算數據庫更新進度"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                db = json.load(f)

            total = 0
            updated = 0
            by_priority = {1: {'total': 0, 'updated': 0},
                          2: {'total': 0, 'updated': 0},
                          3: {'total': 0, 'updated': 0}}

            for code, stock in db['stocks'].items():
                priority = stock.get('priority', 3)
                by_priority[priority]['total'] += 1

                # 檢查 2025 年的數據是否有效
                for year_data in stock.get('data', []):
                    if year_data['year'] == '2025':
                        if year_data.get('source') is not None:
                            updated += 1
                            by_priority[priority]['updated'] += 1
                        total += 1
                        break

            percentage = (updated / total * 100) if total > 0 else 0

            return {
                'total': total,
                'updated': updated,
                'pending': total - updated,
                'percentage': round(percentage, 1),
                'by_priority': by_priority
            }
        except Exception as e:
            return None

    def generate_status(self):
        """生成進度狀態"""
        progress = self.calculate_progress()
        latest_log = self.get_latest_log()

        status = {
            'generated_at': datetime.now().isoformat() + 'Z',
            'progress': progress,
            'latest_execution': None,
            'next_scheduled': self.get_next_schedule()
        }

        if latest_log:
            exec_time = latest_log.get('execution_time', {})
            status['latest_execution'] = {
                'time': exec_time.get('end'),
                'duration_seconds': latest_log.get('statistics', {}).get('updated_stocks', 0),
                'stats': latest_log.get('statistics', {})
            }

        return status

    def get_next_schedule(self):
        """計算下次計劃執行時間"""
        now = datetime.now()

        # 台北時間的計劃
        next_executions = []

        # 今天 05:00
        today_5am = now.replace(hour=5, minute=0, second=0, microsecond=0)
        if now < today_5am:
            next_executions.append(today_5am)
        else:
            # 今天 06:00
            today_6am = now.replace(hour=6, minute=0, second=0, microsecond=0)
            if now < today_6am:
                next_executions.append(today_6am)
            else:
                # 明天 05:00
                tomorrow_5am = (now + timedelta(days=1)).replace(hour=5, minute=0, second=0, microsecond=0)
                next_executions.append(tomorrow_5am)

        return next_executions[0].isoformat() + '+08:00' if next_executions else None

    def print_progress_report(self):
        """打印進度報告"""
        progress = self.calculate_progress()

        if not progress:
            print("無法讀取進度信息")
            return

        print("\n" + "="*60)
        print("📊 自動更新監控 - 進度報告")
        print("="*60 + "\n")

        print(f"📈 整體進度: {progress['updated']}/{progress['total']} ({progress['percentage']}%)")
        print(f"   ├─ 已更新: {progress['updated']} 支")
        print(f"   └─ 待更新: {progress['pending']} 支\n")

        print("優先級進度:")
        for priority in [1, 2, 3]:
            stats = progress['by_priority'][priority]
            pct = (stats['updated'] / stats['total'] * 100) if stats['total'] > 0 else 0
            priority_name = ['', '🔴 高', '🟡 中', '🔵 低'][priority]
            print(f"   {priority_name}: {stats['updated']}/{stats['total']} ({pct:.0f}%)")

        latest_log = self.get_latest_log()
        if latest_log:
            print(f"\n⏱️ 最近執行:")
            exec_time = latest_log.get('execution_time', {})
            print(f"   時間: {exec_time.get('end', 'N/A')}")
            stats = latest_log.get('statistics', {})
            print(f"   結果: {stats.get('completed_batches', 0)}/{stats.get('total_batches', 0)} 批次完成")

        next_exec = self.get_next_schedule()
        if next_exec:
            print(f"\n🔔 下次計劃執行: {next_exec}")

        print("\n" + "="*60 + "\n")

    def save_status(self):
        """保存狀態到文件"""
        status = self.generate_status()
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
        print(f"✅ 狀態已保存: {self.status_file}")

def main():
    monitor = UpdateMonitor()

    # 打印報告
    monitor.print_progress_report()

    # 保存狀態
    monitor.save_status()

if __name__ == '__main__':
    main()
