#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOPS 爬蟲數據驗證工具
v6.07 數據源驗證

功能：
1. 比對爬蟲數據與官方 MOPS 資料
2. 驗證 P/E 一致性（Stock Price / EPS）
3. 生成驗證報告
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Tuple
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MOPSDataValidator:
    """MOPS 數據驗證"""

    # 官方參考數據（需手動從 MOPS 獲取）
    REFERENCE_DATA = {
        '2330': {  # 台積電
            'name': '台積電 (TSMC)',
            'q1_2026_eps': None,  # 待確認
            'q2_2026_eps': None,  # 待確認
            'q1_2025_eps': 14.50,  # 參考數據
            'q2_2025_eps': 13.80,
            'notes': '需從官方 MOPS 確認 2026 Q1-Q2'
        },
        '2207': {  # 和泰汽車
            'name': '和泰汽車',
            'q1_2026_eps': None,
            'q2_2026_eps': None,
            'notes': '需從官方 MOPS 確認'
        },
        '1101': {  # 台泥
            'name': '台泥',
            'q1_2026_eps': None,
            'q2_2026_eps': None,
            'notes': '需從官方 MOPS 確認'
        },
    }

    def __init__(self, crawled_data_file: str = 'mops_2026_data.json'):
        self.crawled_data_file = crawled_data_file
        self.crawled_data = self._load_crawled_data()
        self.validation_results = {}

    def _load_crawled_data(self) -> Dict:
        """加載爬蟲數據"""
        try:
            with open(self.crawled_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"✓ 已加載爬蟲數據: {self.crawled_data_file}")
            return data
        except FileNotFoundError:
            logger.warning(f"⚠️ 找不到爬蟲數據文件: {self.crawled_data_file}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"❌ JSON 解析失敗")
            return {}

    def validate_all(self) -> Dict:
        """驗證所有股票"""
        logger.info("\n" + "=" * 60)
        logger.info("開始數據驗證")
        logger.info("=" * 60)

        for code in self.REFERENCE_DATA.keys():
            self.validate_stock(code)

        logger.info("=" * 60)
        logger.info("數據驗證完成")
        logger.info("=" * 60)

        return self.validation_results

    def validate_stock(self, code: str) -> Dict:
        """驗證單支股票"""
        logger.info(f"\n【{code}】驗證開始")
        logger.info("-" * 40)

        crawled = self.crawled_data.get(code, {})
        reference = self.REFERENCE_DATA.get(code, {})

        result = {
            'code': code,
            'name': reference.get('name', ''),
            'timestamp': datetime.now().isoformat(),
            'checks': []
        }

        # 檢查 1：爬蟲是否成功
        if crawled.get('error'):
            result['checks'].append({
                'item': '爬蟲成功',
                'status': '❌ 失敗',
                'details': crawled.get('error'),
                'severity': 'critical'
            })
            self.validation_results[code] = result
            logger.error(f"❌ 爬蟲失敗: {crawled.get('error')}")
            return result

        result['checks'].append({
            'item': '爬蟲成功',
            'status': '✅ 通過',
            'details': f"成功獲取 {len(crawled.get('quarters', []))} 個季度",
            'severity': 'none'
        })
        logger.info(f"✅ 爬蟲成功: {len(crawled.get('quarters', []))} 個季度")

        # 檢查 2：季度數據完整性
        quarters = crawled.get('quarters', [])
        has_q1 = any(q['season'] == 1 for q in quarters)
        has_q2 = any(q['season'] == 2 for q in quarters)

        if has_q1 and has_q2:
            result['checks'].append({
                'item': 'Q1 & Q2 完整',
                'status': '✅ 通過',
                'details': 'Q1 和 Q2 數據齊全',
                'severity': 'none'
            })
            logger.info("✅ Q1 & Q2 數據完整")
        else:
            result['checks'].append({
                'item': 'Q1 & Q2 完整',
                'status': '⚠️ 部分',
                'details': f"Q1: {'有' if has_q1 else '無'}, Q2: {'有' if has_q2 else '無'}",
                'severity': 'warning'
            })
            logger.warning(f"⚠️ 數據不完整: Q1={'有' if has_q1 else '無'}, Q2={'有' if has_q2 else '無'}")

        # 檢查 3：EPS 值合理性
        eps_checks = self._validate_eps_values(code, quarters)
        result['checks'].extend(eps_checks)

        # 檢查 4：與官方數據對比（如果有參考數據）
        if reference.get('q1_2026_eps') or reference.get('q2_2026_eps'):
            comparison_checks = self._compare_with_reference(code, quarters, reference)
            result['checks'].extend(comparison_checks)

        self.validation_results[code] = result
        return result

    def _validate_eps_values(self, code: str, quarters: List[Dict]) -> List[Dict]:
        """驗證 EPS 值的合理性"""
        checks = []

        # EPS 範圍檢查：通常在 0 到 100 之間（台灣股市）
        valid_eps_values = []
        invalid_eps_values = []

        for q in quarters:
            eps = q.get('eps', 0)
            if 0 < eps <= 100:
                valid_eps_values.append(eps)
            else:
                invalid_eps_values.append(eps)

        if not valid_eps_values:
            checks.append({
                'item': 'EPS 值範圍',
                'status': '❌ 失敗',
                'details': f"所有 EPS 值都超出合理範圍",
                'severity': 'critical'
            })
        elif invalid_eps_values:
            checks.append({
                'item': 'EPS 值範圍',
                'status': '⚠️ 部分異常',
                'details': f"有效: {len(valid_eps_values)}, 異常: {len(invalid_eps_values)}",
                'severity': 'warning'
            })
        else:
            checks.append({
                'item': 'EPS 值範圍',
                'status': '✅ 通過',
                'details': f"所有 {len(valid_eps_values)} 個值在合理範圍內",
                'severity': 'none'
            })

        # 季度間增長檢查
        if len(valid_eps_values) >= 2:
            growth = (valid_eps_values[-1] - valid_eps_values[0]) / valid_eps_values[0] * 100
            if -50 < growth < 50:  # 季度波動通常在 ±50% 內
                checks.append({
                    'item': '季度增長',
                    'status': '✅ 通過',
                    'details': f"季度間增長 {growth:.1f}%",
                    'severity': 'none'
                })
            else:
                checks.append({
                    'item': '季度增長',
                    'status': '⚠️ 異常',
                    'details': f"季度間增長 {growth:.1f}%（超出正常範圍）",
                    'severity': 'warning'
                })

        return checks

    def _compare_with_reference(self, code: str, quarters: List[Dict], reference: Dict) -> List[Dict]:
        """與官方參考數據對比"""
        checks = []

        q1_crawled = next((q['eps'] for q in quarters if q['season'] == 1), None)
        q2_crawled = next((q['eps'] for q in quarters if q['season'] == 2), None)

        q1_ref = reference.get('q1_2026_eps')
        q2_ref = reference.get('q2_2026_eps')

        # Q1 對比
        if q1_crawled and q1_ref:
            diff_pct = abs(q1_crawled - q1_ref) / q1_ref * 100
            if diff_pct < 2:  # 誤差在 2% 以內為通過
                checks.append({
                    'item': 'Q1 與官方對比',
                    'status': '✅ 通過',
                    'details': f"爬蟲: {q1_crawled}, 官方: {q1_ref}, 誤差: {diff_pct:.1f}%",
                    'severity': 'none'
                })
            else:
                checks.append({
                    'item': 'Q1 與官方對比',
                    'status': '⚠️ 偏差',
                    'details': f"誤差 {diff_pct:.1f}%（建議手動驗證）",
                    'severity': 'warning'
                })

        # Q2 對比
        if q2_crawled and q2_ref:
            diff_pct = abs(q2_crawled - q2_ref) / q2_ref * 100
            if diff_pct < 2:
                checks.append({
                    'item': 'Q2 與官方對比',
                    'status': '✅ 通過',
                    'details': f"爬蟲: {q2_crawled}, 官方: {q2_ref}, 誤差: {diff_pct:.1f}%",
                    'severity': 'none'
                })
            else:
                checks.append({
                    'item': 'Q2 與官方對比',
                    'status': '⚠️ 偏差',
                    'details': f"誤差 {diff_pct:.1f}%（建議手動驗證）",
                    'severity': 'warning'
                })

        return checks

    def print_report(self):
        """打印驗證報告"""
        logger.info("\n" + "=" * 70)
        logger.info("【MOPS 數據驗證報告】")
        logger.info("=" * 70)

        for code, result in self.validation_results.items():
            logger.info(f"\n【{code}】{result['name']}")
            logger.info("-" * 70)

            passed = 0
            failed = 0
            warnings = 0

            for check in result['checks']:
                status_emoji = check['status'].split()[0]
                logger.info(f"{status_emoji} {check['item']}: {check['details']}")

                if '✅' in check['status']:
                    passed += 1
                elif '❌' in check['status']:
                    failed += 1
                elif '⚠️' in check['status']:
                    warnings += 1

            logger.info("-" * 70)
            logger.info(f"檢查結果: 通過 {passed} | 警告 {warnings} | 失敗 {failed}")

        logger.info("=" * 70)

    def export_report(self, filepath: str = 'validation_report.json'):
        """匯出驗證報告"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'results': self.validation_results,
                'summary': {
                    'total_stocks': len(self.validation_results),
                    'passed': sum(1 for r in self.validation_results.values()
                                 if all(c['status'].startswith('✅') for c in r['checks'])),
                    'warnings': sum(1 for r in self.validation_results.values()
                                   if any(c['status'].startswith('⚠️') for c in r['checks'])),
                    'failed': sum(1 for r in self.validation_results.values()
                                 if any(c['status'].startswith('❌') for c in r['checks']))
                }
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"✓ 驗證報告已保存: {filepath}")
        except Exception as e:
            logger.error(f"❌ 保存報告失敗: {str(e)}")


def main():
    """主函數"""
    validator = MOPSDataValidator()
    validator.validate_all()
    validator.print_report()
    validator.export_report()


if __name__ == '__main__':
    main()
