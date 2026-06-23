/**
 * 財務數據顯示工具
 * 優雅處理 null/N/A/待更新的情況
 */

class FinancialDisplayFormatter {
  /**
   * 格式化數字顯示
   * @param {number|null} value - 數值
   * @param {object} options - 選項
   * @returns {string} 格式化後的字符串
   */
  static formatNumber(value, options = {}) {
    const {
      decimals = 2,
      showSign = false,
      prefix = '',
      suffix = '',
      zeroLabel = 'N/A'  // 值為 0 或 null 時的標籤
    } = options;

    // 檢查值是否有效
    if (value === null || value === undefined) {
      return zeroLabel;
    }

    if (typeof value !== 'number' || isNaN(value) || !isFinite(value)) {
      return zeroLabel;
    }

    // 格式化數字
    let formatted = value.toFixed(decimals);

    // 添加正負號
    if (showSign && value > 0) {
      formatted = '+' + formatted;
    }

    return prefix + formatted + suffix;
  }

  /**
   * 格式化百分比
   */
  static formatPercentage(value, options = {}) {
    return this.formatNumber(value, {
      decimals: 2,
      suffix: '%',
      ...options
    });
  }

  /**
   * 格式化大數字（K/M/B/T）
   */
  static formatLargeNumber(value, options = {}) {
    const { decimals = 2, zeroLabel = 'N/A' } = options;

    if (value === null || value === undefined || isNaN(value)) {
      return zeroLabel;
    }

    const abs = Math.abs(value);

    if (abs >= 1e12) {
      return (value / 1e12).toFixed(decimals) + 'T';
    }
    if (abs >= 1e9) {
      return (value / 1e9).toFixed(decimals) + 'B';
    }
    if (abs >= 1e6) {
      return (value / 1e6).toFixed(decimals) + 'M';
    }
    if (abs >= 1e3) {
      return (value / 1e3).toFixed(decimals) + 'K';
    }

    return value.toFixed(0);
  }

  /**
   * 創建財務數據狀態標籤
   */
  static createStatusBadge(value, options = {}) {
    const {
      showDataSource = false,
      dataSource = null,
      updateDate = null
    } = options;

    let badge = '';
    let title = '';

    if (value === null || value === undefined) {
      badge = `<span class="financial-badge badge-updating" title="數據待更新">待更新</span>`;
      title = '該財務指標尚未更新';
    } else if (typeof value === 'number' && (isNaN(value) || !isFinite(value))) {
      badge = `<span class="financial-badge badge-unavailable" title="數據不可用">N/A</span>`;
      title = '該財務指標暫無數據';
    } else if (value === 0) {
      badge = `<span class="financial-badge badge-zero" title="數值為零">0</span>`;
      title = '該財務指標的值為零';
    } else {
      badge = `<span class="financial-badge badge-valid">✓</span>`;
      title = '數據有效';
    }

    // 添加數據源和更新日期
    if (showDataSource) {
      if (dataSource) {
        title += ` | 來源: ${dataSource}`;
      }
      if (updateDate) {
        title += ` | 更新: ${updateDate}`;
      }
    }

    return `${badge}`;
  }

  /**
   * 生成財務指標表格 HTML
   */
  static generateFinancialTable(financialData, options = {}) {
    const {
      showStatus = true,
      highlightMissing = true,
      columns = ['eps', 'revenue', 'netIncome', 'roe', 'debtRatio']
    } = options;

    if (!financialData || typeof financialData !== 'object') {
      return '<p class="financial-error">無可用的財務數據</p>';
    }

    let html = '<table class="financial-table">';
    html += '<thead><tr>';
    html += '<th>指標</th>';
    html += columns.map(col => `<th>${this.getColumnLabel(col)}</th>`).join('');
    html += '</tr></thead>';
    html += '<tbody>';

    // 遍歷每一年的數據
    const years = financialData.data || [];
    years.forEach(yearData => {
      html += '<tr>';
      html += `<td>${yearData.year || '未知'}</td>`;

      columns.forEach(col => {
        const value = yearData[col];
        const isMissing = value === null || value === undefined;

        let cellClass = 'financial-cell';
        if (isMissing && highlightMissing) {
          cellClass += ' missing-data';
        }

        let cellContent = this.formatNumber(value);

        // 特殊格式化
        if (col.includes('Margin') || col.includes('Yield')) {
          cellContent = this.formatPercentage(value);
        } else if (col === 'revenue' || col === 'netIncome' || col === 'fcf') {
          cellContent = this.formatLargeNumber(value, { decimals: 1 });
        }

        if (showStatus && isMissing) {
          cellContent = `待更新 ${this.createStatusBadge(value)}`;
        }

        html += `<td class="${cellClass}">${cellContent}</td>`;
      });

      html += '</tr>';
    });

    html += '</tbody>';
    html += '</table>';

    return html;
  }

  /**
   * 獲取列標籤
   */
  static getColumnLabel(col) {
    const labels = {
      'eps': 'EPS',
      'revenue': '營收',
      'netIncome': '淨收益',
      'operatingIncome': '營業收入',
      'operatingMargin': '營業利益率',
      'fcf': '自由現金流',
      'roe': 'ROE',
      'netMargin': '淨利率',
      'debtRatio': '負債比',
      'year': '年份'
    };
    return labels[col] || col;
  }

  /**
   * 生成更新狀態摘要
   */
  static generateUpdateSummary(financialData) {
    if (!financialData || !financialData.data) {
      return {
        total: 0,
        updated: 0,
        pending: 0,
        percentage: 0
      };
    }

    let total = 0;
    let updated = 0;

    financialData.data.forEach(yearData => {
      for (const key in yearData) {
        if (key === 'year' || key === 'note') continue;
        total++;
        if (yearData[key] !== null && yearData[key] !== undefined) {
          updated++;
        }
      }
    });

    return {
      total,
      updated,
      pending: total - updated,
      percentage: total > 0 ? Math.round((updated / total) * 100) : 0
    };
  }

  /**
   * 生成更新進度條 HTML
   */
  static generateProgressBar(summary) {
    const { updated, total, percentage } = summary;

    if (total === 0) {
      return '<div class="progress-bar empty">暫無數據</div>';
    }

    const barColor = percentage < 30 ? '#ef4444' : percentage < 70 ? '#f59e0b' : '#10b981';

    return `
      <div class="progress-container">
        <div class="progress-bar" style="width: ${percentage}%; background-color: ${barColor};">
          <span class="progress-text">${updated}/${total} (${percentage}%)</span>
        </div>
      </div>
    `;
  }
}

// CSS 樣式
const FINANCIAL_STYLES = `
  /* 財務數據表格 */
  .financial-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
    margin: 1rem 0;
  }

  .financial-table thead {
    background-color: #f3f4f6;
    font-weight: 600;
  }

  .financial-table th,
  .financial-table td {
    border: 1px solid #e5e7eb;
    padding: 0.75rem;
    text-align: right;
  }

  .financial-table th:first-child,
  .financial-table td:first-child {
    text-align: left;
  }

  .financial-table tbody tr:hover {
    background-color: #f9fafb;
  }

  /* 缺失數據高亮 */
  .financial-cell.missing-data {
    background-color: #fef2f2;
    color: #991b1b;
  }

  /* 財務徽章 */
  .financial-badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.5rem;
  }

  .badge-updating {
    background-color: #fef3c7;
    color: #92400e;
    border: 1px solid #fcd34d;
  }

  .badge-unavailable {
    background-color: #fee2e2;
    color: #991b1b;
    border: 1px solid #fca5a5;
  }

  .badge-zero {
    background-color: #dbeafe;
    color: #1e3a8a;
    border: 1px solid #93c5fd;
  }

  .badge-valid {
    background-color: #dcfce7;
    color: #166534;
    border: 1px solid #86efac;
  }

  /* 進度條 */
  .progress-container {
    width: 100%;
    height: 24px;
    background-color: #e5e7eb;
    border-radius: 0.5rem;
    overflow: hidden;
    margin: 0.5rem 0;
  }

  .progress-bar {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: width 0.3s ease;
  }

  .progress-bar.empty {
    background-color: #d1d5db;
    color: #6b7280;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
  }

  .progress-text {
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  }

  .financial-error {
    color: #991b1b;
    background-color: #fef2f2;
    padding: 1rem;
    border-radius: 0.5rem;
    text-align: center;
  }
`;

// 導出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { FinancialDisplayFormatter, FINANCIAL_STYLES };
}
