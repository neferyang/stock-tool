#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOPS（公開資訊觀測站）爬蟲 - 獲取台股財報數據
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import sys
import re
from datetime import datetime
from urllib.parse import urlencode
import urllib3

# 禁用 SSL 警告（MOPS 有時 SSL 驗證問題）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

print("\n" + "="*70)
print("MOPS 財報數據爬蟲 - 獲取最新年度財務數據")
print("="*70)

class MOPSCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.base_url = "https://mops.twse.com.tw/mops/web_api"
        self.financial_data = {}

    def fetch_annual_report(self, stock_code, year=2025):
        """
        從 MOPS 公司基本資料查詢獲取年度財報
        """
        try:
            # 使用公司基本資料查詢頁面（避免 API 被檢測）
            url = "https://mops.twse.com.tw/mops/web/t05_query"
            params = {
                'code': stock_code,
                'type': 'json'
            }

            print(f"  [爬蟲] {stock_code} 基本資料頁面")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://mops.twse.com.tw/mops/web/t05_query',
            }

            r = self.session.get(url, params=params, timeout=10, verify=False, headers=headers)
            r.encoding = 'utf-8'

            if r.status_code == 200:
                # 嘗試解析 JSON
                try:
                    data = r.json()
                    if data.get('data') and len(data['data']) > 0:
                        print(f"    ✓ 獲得 {len(data['data'])} 筆記錄")
                        return data
                except json.JSONDecodeError:
                    # 如果不是 JSON，嘗試用 BeautifulSoup 解析 HTML
                    print(f"    ✗ JSON 解析失敗，嘗試 HTML 解析")
                    soup = BeautifulSoup(r.text, 'html.parser')
                    return self._parse_html_table(soup)
        except Exception as e:
            print(f"    ✗ 錯誤: {e}")

        return None

    def _parse_html_table(self, soup):
        """
        從 HTML 表格中解析財報數據
        """
        try:
            # 查找表格
            table = soup.find('table')
            if not table:
                return None

            # 解析表格行
            rows = table.find_all('tr')
            data = []

            for row in rows[1:]:  # 跳過表頭
                cells = row.find_all('td')
                if len(cells) > 0:
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    data.append(row_data)

            return {'data': data} if data else None
        except Exception as e:
            print(f"    ✗ HTML 解析失敗: {e}")
            return None

    def fetch_monthly_revenue(self, stock_code):
        """
        從 MOPS 獲取月營收
        """
        try:
            url = f"{self.base_url}/t163302"
            params = {
                'code': stock_code,
                'type': 'json'
            }

            print(f"  [查詢] {stock_code} 月營收")
            r = self.session.get(url, params=params, timeout=10, verify=False)
            r.encoding = 'utf-8'

            if r.status_code == 200:
                try:
                    data = r.json()
                    if data.get('aaData') and len(data['aaData']) > 0:
                        print(f"    ✓ 獲得 {len(data['aaData'])} 筆記錄")
                        return data
                except json.JSONDecodeError:
                    pass

        except Exception as e:
            print(f"    ✗ 錯誤: {e}")

        return None

    def extract_financials(self, stock_code, report_data, monthly_data=None):
        """
        從財報數據中提取關鍵財務指標
        """
        try:
            if not report_data or not report_data.get('aaData'):
                return None

            # 取最新一年的數據（通常是第一筆）
            record = report_data['aaData'][0]

            # MOPS 返回的欄位通常為中文，需要根據實際響應調整
            # 這是一個範例映射，實際欄位名需要根據 API 響應確認
            financial = {
                'year': str(datetime.now().year),
                'eps': 0.0,
                'roe': 0.0,
                'netMargin': 0.0,
                'debtRatio': 0.0,
                'operatingMargin': 0.0,
                'revenue': 0.0,
                'netIncome': 0.0,
                'operatingIncome': 0.0,
                'fcf': 0.0,
            }

            # 根據實際 MOPS API 響應結構調整
            # 這需要先查看實際的 API 輸出來確定正確的欄位名
            if isinstance(record, list):
                # 如果是列表形式，需要根據列的順序映射
                # [0] 通常是股票代碼, [1] 年份, [2] EPS 等
                if len(record) > 2:
                    financial['eps'] = float(str(record[2]).replace(',', '') or 0)
            elif isinstance(record, dict):
                # 如果是字典形式，直接訪問鍵
                financial['eps'] = float(record.get('EPS', record.get('eps', 0)) or 0)
                financial['roe'] = float(record.get('ROE', record.get('roe', 0)) or 0)
                financial['netMargin'] = float(record.get('NetMargin', 0) or 0)
                financial['debtRatio'] = float(record.get('DebtRatio', 0) or 0)
                financial['operatingMargin'] = float(record.get('OperatingMargin', 0) or 0)
                financial['revenue'] = float(record.get('Revenue', record.get('revenue', 0)) or 0)
                financial['netIncome'] = float(record.get('NetIncome', 0) or 0)

            return financial

        except Exception as e:
            print(f"    ✗ 提取失敗: {e}")
            return None

    def crawl_stocks(self, stock_codes):
        """
        爬取多支股票的財報
        """
        results = {}

        for code in stock_codes:
            print(f"\n獲取 {code} 的財報數據...")

            # 獲取年度報告
            annual = self.fetch_annual_report(code)
            monthly = self.fetch_monthly_revenue(code)

            # 提取數據
            financial = self.extract_financials(code, annual, monthly)

            if financial:
                results[code] = financial
                print(f"  ✅ 已獲取財務數據")
            else:
                print(f"  ⚠️ 無法獲取數據")

            # 避免過度請求
            time.sleep(2)

        return results

def main():
    crawler = MOPSCrawler()

    # 目標股票
    target_stocks = [
        '2207',  # 和泰車
        '3030',  # 德律
        '2330',  # 台積電
        '1101',  # 台泥
        '2603',  # 長榮
        '2201',  # 裕隆
    ]

    print(f"\n目標股票: {', '.join(target_stocks)}")
    print(f"開始時間: {datetime.now().isoformat()}\n")

    # 爬取數據
    financial_data = crawler.crawl_stocks(target_stocks)

    if financial_data:
        # 保存為 JSON
        output_file = 'financial-data-mops.json'
        output = {
            'updatedAt': datetime.now().isoformat(),
            'source': 'MOPS (公開資訊觀測站)',
            'stocks': financial_data
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*70}")
        print(f"✅ 完成 - 已保存 {len(financial_data)} 家公司的數據到 {output_file}")
        print(f"{'='*70}\n")

        # 顯示摘要
        for code, data in financial_data.items():
            print(f"{code}: EPS={data['eps']}, ROE={data['roe']}%, 淨利率={data['netMargin']}%")

        return True
    else:
        print("\n❌ 未獲取到任何數據")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
