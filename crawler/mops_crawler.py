#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOPS 爬蟲 - 獲取台灣上市公司季度 EPS 數據
v6.07 數據源驗證

功能：
1. 從 MOPS 爬取 2026 年 Q1-Q2 季度 EPS 數據
2. 存儲為 JSON 格式供前端使用
3. 跟蹤數據版本和抓取時間
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MOPSCrawler:
    """MOPS 網站爬蟲"""

    # MOPS 查詢端點
    MOPS_URL = "https://mops.twse.com.tw/mops/web/t05st01"

    # 請求頭（模擬瀏覽器）
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    # 測試股票列表
    TEST_STOCKS = {
        '2330': '台積電 (TSMC)',
        '2207': '和泰汽車',
        '1101': '台泥',
        '2887': '國泰金',
        '2409': '友達',
    }

    def __init__(self, timeout=10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.results = {}

    def fetch_stock_data(self, code: str, year: int = 2026) -> Optional[Dict]:
        """
        獲取單支股票的季度數據

        Args:
            code: 股票代碼 (e.g., "2330")
            year: 查詢年份 (default: 2026)

        Returns:
            {
                'code': '2330',
                'name': '台積電',
                'year': 2026,
                'quarters': [
                    {'season': 1, 'eps': 15.50, 'status': 'actual'},
                    {'season': 2, 'eps': 16.20, 'status': 'actual'},
                    ...
                ],
                'source': 'mops_html',
                'timestamp': '2026-06-08T10:30:00',
                'error': None
            }
        """
        try:
            logger.info(f"正在爬取 {code}({self.TEST_STOCKS.get(code, '未知')}) 的 {year} 年數據...")

            # 構建查詢 URL
            url = f"{self.MOPS_URL}?code={code}&year={year}"

            # 發送請求
            response = self.session.get(url, timeout=self.timeout)
            response.encoding = 'utf-8'

            if response.status_code != 200:
                logger.warning(f"{code} 請求失敗 (HTTP {response.status_code})")
                return {
                    'code': code,
                    'error': f'HTTP {response.status_code}',
                    'timestamp': datetime.now().isoformat()
                }

            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 嘗試提取數據
            quarters = self._parse_quarters(soup, code)

            if not quarters:
                logger.warning(f"{code} 無法解析季度數據")
                return {
                    'code': code,
                    'error': '無法解析 HTML',
                    'timestamp': datetime.now().isoformat()
                }

            logger.info(f"✓ 成功獲取 {code}：{len(quarters)} 個季度")

            return {
                'code': code,
                'name': self.TEST_STOCKS.get(code, ''),
                'year': year,
                'quarters': quarters,
                'source': 'mops_html',
                'timestamp': datetime.now().isoformat(),
                'error': None
            }

        except requests.Timeout:
            logger.error(f"{code} 請求超時")
            return {'code': code, 'error': 'Timeout', 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"{code} 爬取失敗: {str(e)}")
            return {'code': code, 'error': str(e), 'timestamp': datetime.now().isoformat()}

    def _parse_quarters(self, soup: BeautifulSoup, code: str) -> List[Dict]:
        """
        從 HTML 解析季度 EPS 數據

        多層次解析策略：
        1. 查找包含 "EPS" 或 "每股盈餘" 的表格
        2. 識別 Q1-Q4 行
        3. 提取對應的 EPS 值
        """
        quarters = []

        try:
            # 策略 1：查找所有表格
            tables = soup.find_all('table')
            logger.debug(f"找到 {len(tables)} 個表格")

            for table_idx, table in enumerate(tables):
                # 提取表格的所有行
                rows = table.find_all('tr')

                for row_idx, row in enumerate(rows):
                    cells = row.find_all(['td', 'th'])
                    cell_texts = [cell.get_text(strip=True) for cell in cells]

                    # 查找含 "Q1" 或 "第1季" 的行
                    for col_idx, cell_text in enumerate(cell_texts):
                        match = re.search(r'第?(\d)季|Q(\d)', cell_text, re.IGNORECASE)
                        if match:
                            season = int(match.group(1) or match.group(2))

                            # 嘗試從相鄰列獲取 EPS 值
                            eps_value = self._extract_eps_value(cell_texts, col_idx)

                            if eps_value is not None:
                                quarters.append({
                                    'season': season,
                                    'eps': eps_value,
                                    'status': 'actual',
                                    'table': table_idx,
                                    'row': row_idx
                                })
                                logger.debug(f"  找到 Q{season}: {eps_value}")

            # 策略 2：如果沒有找到，嘗試通用 EPS 關鍵字搜尋
            if not quarters:
                logger.debug("表格搜尋失敗，嘗試關鍵字搜尋...")
                quarters = self._search_by_keywords(soup)

            return quarters

        except Exception as e:
            logger.error(f"解析失敗: {str(e)}")
            return []

    def _extract_eps_value(self, cell_texts: List[str], season_col_idx: int) -> Optional[float]:
        """
        從相鄰列提取 EPS 數值

        嘗試順序：
        1. 同列後續內容
        2. 下一列
        3. 上一列
        """
        # 嘗試同列
        current_cell = cell_texts[season_col_idx]
        eps_match = re.search(r'(\d+\.?\d*)', current_cell)
        if eps_match:
            try:
                return float(eps_match.group(1))
            except ValueError:
                pass

        # 嘗試下一列
        if season_col_idx + 1 < len(cell_texts):
            next_cell = cell_texts[season_col_idx + 1]
            eps_match = re.search(r'^(\d+\.?\d*)', next_cell)
            if eps_match:
                try:
                    return float(eps_match.group(1))
                except ValueError:
                    pass

        # 嘗試前一列
        if season_col_idx > 0:
            prev_cell = cell_texts[season_col_idx - 1]
            eps_match = re.search(r'(\d+\.?\d*)$', prev_cell)
            if eps_match:
                try:
                    return float(eps_match.group(1))
                except ValueError:
                    pass

        return None

    def _search_by_keywords(self, soup: BeautifulSoup) -> List[Dict]:
        """
        通過關鍵字搜尋 EPS 數據（備用方案）
        """
        quarters = []
        text = soup.get_text()

        # 查找 "每股盈餘" 或 "EPS" 後的數字
        eps_pattern = r'(?:EPS|每股盈餘)[\s：]*(\d+\.?\d*)'
        matches = re.findall(eps_pattern, text, re.IGNORECASE)

        for idx, match in enumerate(matches[:4]):  # 最多 4 個季度
            try:
                eps_value = float(match)
                if eps_value > 0:  # 過濾無效數據
                    quarters.append({
                        'season': idx + 1,
                        'eps': eps_value,
                        'status': 'estimated'
                    })
            except ValueError:
                pass

        return quarters

    def run_test(self) -> Dict:
        """
        執行測試爬蟲
        """
        logger.info("=" * 60)
        logger.info("MOPS 爬蟲測試開始")
        logger.info("=" * 60)

        for code, name in self.TEST_STOCKS.items():
            result = self.fetch_stock_data(code)
            self.results[code] = result

        logger.info("=" * 60)
        logger.info("MOPS 爬蟲測試完成")
        logger.info("=" * 60)

        return self.results

    def save_results(self, filepath: str = 'mops_2026_data.json'):
        """
        保存結果為 JSON
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ 結果已保存到 {filepath}")
        except Exception as e:
            logger.error(f"保存失敗: {str(e)}")

    def print_summary(self):
        """
        打印摘要
        """
        logger.info("\n【爬蟲結果摘要】")
        logger.info("-" * 60)

        success_count = 0
        failure_count = 0

        for code, result in self.results.items():
            if result.get('error'):
                logger.info(f"❌ {code} - {result['error']}")
                failure_count += 1
            else:
                quarters = result.get('quarters', [])
                logger.info(f"✅ {code} - {len(quarters)} 個季度數據")
                for q in quarters:
                    logger.info(f"   Q{q['season']}: {q['eps']} 元 ({q.get('status', 'unknown')})")
                success_count += 1

        logger.info("-" * 60)
        logger.info(f"成功: {success_count}/{len(self.TEST_STOCKS)}")
        logger.info(f"失敗: {failure_count}/{len(self.TEST_STOCKS)}")


def main():
    """主函數"""
    crawler = MOPSCrawler()
    results = crawler.run_test()
    crawler.save_results()
    crawler.print_summary()

    # 返回成功/失敗狀態
    success_count = sum(1 for r in results.values() if not r.get('error'))
    return 0 if success_count > 0 else 1


if __name__ == '__main__':
    exit(main())
