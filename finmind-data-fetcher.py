#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從 FinMind API 獲取台股真實財務數據
支持：EPS、ROE、淨利率、營業利率、負債比等指標
"""

import requests
import json
import time
import sys
from datetime import datetime

# 修復 Windows 編碼問題
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class FinMindFetcher:
    def __init__(self):
        self.base_url = "https://api.finmind.com.tw/v1/data"
        self.timeout = 10
        self.rate_limit_delay = 0.2  # 請求間隔（秒）

        # 從環境變數或 .env 讀取 token
        import os
        from dotenv import load_dotenv
        load_dotenv()
        self.token = os.getenv('FINMIND_TOKEN', '')
        self.headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}

    def fetch_stock_data(self, stock_code, years=5):
        """
        從 FinMind 獲取單支股票的財務數據

        Args:
            stock_code: 股票代碼（如 '2330'）
            years: 要獲取的年份數（預設 5 年）

        Returns:
            dict: 整理後的財務數據
        """
        print(f"\n正在查詢 {stock_code} 的財務數據...", end=" ", flush=True)

        try:
            # 查詢月度報告（包含 EPS）
            monthly_data = self._fetch_monthly_reporting(stock_code)

            # 查詢財務報表（包含 ROE、淨利率等）
            financial_data = self._fetch_financial_statements(stock_code)

            # 整合數據
            result = self._merge_data(stock_code, monthly_data, financial_data)

            print("✅ 成功")
            return result

        except Exception as e:
            print(f"❌ 錯誤：{str(e)}")
            return None

    def _fetch_monthly_reporting(self, stock_code):
        """獲取月度報告數據"""
        try:
            params = {
                "dataset": "TaiwanStockMonthlyReporting",
                "data_id": stock_code,
                "start_date": "2020-01-01",
                "end_date": datetime.now().strftime("%Y-%m-%d")
            }

            response = requests.get(self.base_url, params=params, timeout=self.timeout, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get('status') == 200 and data.get('data'):
                return data['data']
            return []

        except Exception as e:
            print(f"月度報告查詢失敗：{e}")
            return []

    def _fetch_financial_statements(self, stock_code):
        """獲取財務報表數據"""
        try:
            params = {
                "dataset": "TaiwanStockFinancialStatements",
                "data_id": stock_code,
                "start_date": "2020-01-01",
                "end_date": datetime.now().strftime("%Y-%m-%d")
            }

            response = requests.get(self.base_url, params=params, timeout=self.timeout, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get('status') == 200 and data.get('data'):
                return data['data']
            return []

        except Exception as e:
            print(f"財務報表查詢失敗：{e}")
            return []

    def _merge_data(self, stock_code, monthly_data, financial_data):
        """整合不同來源的數據"""
        # 按年份整理數據
        years_dict = {}

        # 處理月度報告中的 EPS
        for item in monthly_data:
            year = item.get('year')
            if year and year >= 2021:  # 改為 2021-2025 年
                if year not in years_dict:
                    years_dict[year] = {'year': year}

                # EPS 數據
                if 'eps' in item and item['eps']:
                    years_dict[year]['eps'] = float(item['eps'])

        # 處理財務報表中的其他指標
        for item in financial_data:
            year = item.get('year')
            if year and year >= 2021:  # 改為 2021-2025 年
                if year not in years_dict:
                    years_dict[year] = {'year': year}

                # ROE（股東權益報酬率）
                if 'roe' in item and item['roe']:
                    years_dict[year]['roe'] = float(item['roe']) * 100

                # 淨利率（Net Profit Margin）
                if 'net_profit_margin' in item and item['net_profit_margin']:
                    years_dict[year]['netMargin'] = float(item['net_profit_margin']) * 100
                elif 'profit_margin' in item and item['profit_margin']:
                    years_dict[year]['netMargin'] = float(item['profit_margin']) * 100

                # 營業利率（Operating Margin）
                if 'operating_margin' in item and item['operating_margin']:
                    years_dict[year]['operatingMargin'] = float(item['operating_margin']) * 100

                # 負債比（Debt Ratio）
                if 'debt_ratio' in item and item['debt_ratio']:
                    years_dict[year]['debtRatio'] = float(item['debt_ratio']) * 100

                # 收益相關數據
                if 'revenue' in item and item['revenue']:
                    years_dict[year]['revenue'] = float(item['revenue'])

                if 'net_income' in item and item['net_income']:
                    years_dict[year]['netIncome'] = float(item['net_income'])

                if 'operating_income' in item and item['operating_income']:
                    years_dict[year]['operatingIncome'] = float(item['operating_income'])

        # 按年份排序（降序 - 最新年份在前）
        sorted_years = sorted(years_dict.items(), key=lambda x: x[0], reverse=True)

        # 為每筆數據添加元數據
        result_data = []
        for year, data in sorted_years:
            data['updatedAt'] = datetime.now().isoformat()
            data['source'] = 'FinMind'
            data['isEstimate'] = False
            data['dataType'] = '真實'
            result_data.append(data)

        return {
            'code': stock_code,
            'data': result_data
        }

    def fetch_multiple_stocks(self, stock_codes, years=5):
        """
        批量獲取多支股票的財務數據

        Args:
            stock_codes: 股票代碼列表
            years: 要獲取的年份數

        Returns:
            dict: 所有股票的數據
        """
        print(f"\n開始從 FinMind 獲取 {len(stock_codes)} 支股票的財務數據...\n")

        results = {}
        successful = 0
        failed = 0

        for i, code in enumerate(stock_codes, 1):
            print(f"[{i}/{len(stock_codes)}]", end=" ")

            data = self.fetch_stock_data(code, years)

            if data:
                results[code] = data
                successful += 1
            else:
                failed += 1

            # 速率限制
            time.sleep(self.rate_limit_delay)

        print(f"\n{'='*60}")
        print(f"完成！成功: {successful}, 失敗: {failed}")
        print(f"{'='*60}\n")

        return results


def main():
    """主程序：演示如何使用"""

    print("="*60)
    print("FinMind API 台股財務數據獲取工具")
    print("="*60)

    # 初始化
    fetcher = FinMindFetcher()

    # 要查詢的股票清單（第 1 階段 15 支 + 第 2-3 階段前 50 支）
    stock_codes = [
        # 第 1 階段（真實 MOPS 數據）
        "2330", "2207", "3030", "2454", "2317", "1216", "2308",
        "1102", "1109", "1108", "2409", "2412", "1101", "2603", "2201",
        # 第 2 階段（補充真實數據）
        "2344", "2357", "2382", "2390", "2392", "2395", "2408", "2419",
        "2421", "2423", "2424", "2425", "2427", "2428", "2430", "2436",
    ]

    print(f"\n將查詢 {len(stock_codes)} 支股票的財務數據（2021-2025）\n")
    print("注意：")
    print("  - 需要網絡連接到 https://api.finmindtrade.com/")
    print("  - 免費版限制：600 requests/hour")
    print("  - 首次查詢可能需要 2-5 分鐘\n")

    # 獲取數據
    all_data = fetcher.fetch_multiple_stocks(stock_codes)

    # 保存結果
    output_file = "finmind-real-data.json"
    output_data = {
        "description": "FinMind API 真實台股財務數據",
        "source": "FinMind API",
        "updated_at": datetime.now().isoformat(),
        "stocks": all_data
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 數據已保存至 {output_file}")
    print(f"   包含 {len(all_data)} 支股票的財務數據")

    # 打印樣本
    if all_data:
        sample_code = list(all_data.keys())[0]
        sample_data = all_data[sample_code]
        print(f"\n樣本數據（{sample_code}）：")
        print(json.dumps(sample_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
