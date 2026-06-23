#!/usr/bin/env node
/**
 * 增強財務數據顯示工具
 * 添加時間戳標註和數據真實性指示
 */

class FinancialDisplayEnhanced {
    /**
     * 格式化帶時間戳和源標記的數據
     */
    static formatDataWithMetadata(value, metadata = {}) {
        const {
            decimals = 2,
            suffix = '',
            prefix = '',
            zeroLabel = 'N/A',
            updatedAt = null,
            source = null,
            isEstimate = false,
            zeroLabel = 'N/A'
        } = metadata;

        // 檢查值是否有效
        if (value === null || value === undefined) {
            return {
                display: zeroLabel,
                html: `<span class="data-unavailable" title="數據不可用">${zeroLabel}</span>`,
                tooltip: '數據不可用'
            };
        }

        if (typeof value !== 'number' || isNaN(value) || !isFinite(value)) {
            return {
                display: zeroLabel,
                html: `<span class="data-unavailable" title="數據不可用">${zeroLabel}</span>`,
                tooltip: '數據不可用'
            };
        }

        // 格式化數字
        const formatted = value.toFixed(decimals);
        const display = prefix + formatted + suffix;

        // 生成 HTML（帶提示信息）
        let tooltip = display;
        let html = `<span class="data-value">${display}</span>`;

        // 添加數據源和時間戳標記
        if (source || updatedAt || isEstimate !== undefined) {
            const badges = [];

            // 數據類型徽章
            if (isEstimate) {
                badges.push('span class="badge badge-estimate" title="推估數據">推估</span>');
            } else if (source) {
                badges.push(`<span class="badge badge-real" title="真實數據，來源: ${source}">✓</span>`);
            }

            // 時間戳
            if (updatedAt) {
                const date = new Date(updatedAt);
                const dateStr = date.toLocaleDateString('zh-TW');
                badges.push(`<span class="badge badge-timestamp" title="更新於 ${dateStr}">${dateStr}</span>`);
                tooltip += ` (更新於 ${dateStr})`;
            }

            if (badges.length > 0) {
                html += ' <small class="data-badges">' + badges.join('') + '</small>';
            }

            // 添加資料源信息
            if (source) {
                tooltip += ` [來源: ${source}]`;
            }
            if (isEstimate) {
                tooltip += ' [推估數據]';
            }
        }

        html = `<span class="data-with-meta" title="${tooltip}">${html}</span>`;

        return {
            display,
            html,
            tooltip
        };
    }

    /**
     * 生成帶元數據的財務表格
     */
    static generateFinancialTableWithMetadata(financialData, options = {}) {
        if (!financialData || typeof financialData !== 'object') {
            return '<p class="financial-error">無可用的財務數據</p>';
        }

        const {
            showMetadata = true,
            columns = ['year', 'eps', 'revenue', 'roe', 'netMargin', 'debtRatio']
        } = options;

        let html = '<table class="financial-table-enhanced">';
        html += '<thead><tr>';

        // 表頭
        for (const col of columns) {
            const label = this.getColumnLabel(col);
            html += `<th>${label}`;
            if (showMetadata && col !== 'year') {
                html += '<small class="table-hint">📝 含時間戳</small>';
            }
            html += '</th>';
        }
        html += '</tr></thead>';
        html += '<tbody>';

        // 表格行
        const years = financialData.data || [];
        years.forEach((yearData, idx) => {
            html += '<tr>';

            for (const col of columns) {
                const value = yearData[col];

                if (col === 'year') {
                    html += `<td class="year-cell">${value || '未知'}</td>`;
                    continue;
                }

                // 獲取元數據
                const metadata = {
                    updatedAt: yearData.updatedAt,
                    source: yearData.source,
                    isEstimate: yearData.isEstimate || false
                };

                // 根據字段類型格式化
                let fieldMetadata = { ...metadata };
                if (col.includes('Margin') || col.includes('Yield') || col.includes('ROE')) {
                    fieldMetadata.suffix = '%';
                } else if (col === 'revenue' || col === 'netIncome' || col === 'fcf') {
                    fieldMetadata.suffix = 'B';
                }

                const result = this.formatDataWithMetadata(value, fieldMetadata);
                const cellClass = value === null || value === undefined ? 'missing-data' : '';

                html += `<td class="data-cell ${cellClass}" title="${result.tooltip}">`;
                html += result.html;
                html += '</td>';
            }

            html += '</tr>';
        });

        html += '</tbody>';
        html += '</table>';

        return html;
    }

    /**
     * 生成帶時間戳的統計信息
     */
    static generateStatsWithTimestamp(stats, metadata = {}) {
        const { updatedAt, source } = metadata;

        let html = '<div class="stats-container">';
        html += '<div class="stats-main">';

        if (stats.total > 0) {
            const pct = (stats.updated / stats.total * 100).toFixed(1);
            html += `
                <div class="stat-item">
                    <div class="stat-label">數據完整度</div>
                    <div class="stat-value">${stats.updated}/${stats.total}</div>
                    <div class="stat-percentage">${pct}%</div>
                </div>
            `;
        }

        html += '</div>';

        // 元數據信息
        if (updatedAt || source) {
            html += '<div class="stats-metadata">';

            if (updatedAt) {
                const date = new Date(updatedAt);
                const timeStr = date.toLocaleString('zh-TW');
                html += `<span class="meta-item">📅 最後更新: ${timeStr}</span>`;
            }

            if (source) {
                html += `<span class="meta-item">📊 來源: ${source}</span>`;
            }

            html += '</div>';
        }

        html += '</div>';
        return html;
    }

    /**
     * 生成數據品質指示卡
     */
    static generateDataQualityCard(stock) {
        let html = `
            <div class="quality-card">
                <div class="quality-header">${stock.name} (${stock.code || 'N/A'})</div>
                <div class="quality-content">
        `;

        let realCount = 0;
        let estimateCount = 0;
        let missingCount = 0;

        // 統計數據品質
        (stock.data || []).forEach(yearData => {
            for (const key in yearData) {
                if (key === 'year' || key === 'updatedAt' || key === 'source' || key === 'isEstimate') continue;

                const value = yearData[key];
                if (value === null || value === undefined) {
                    missingCount++;
                } else if (yearData.isEstimate) {
                    estimateCount++;
                } else {
                    realCount++;
                }
            }
        });

        const total = realCount + estimateCount + missingCount;

        html += `
                    <div class="quality-stat">
                        <span class="quality-badge real">✓ 真實: ${realCount}</span>
                        <span class="quality-badge estimate">📈 推估: ${estimateCount}</span>
                        <span class="quality-badge missing">❌ 缺失: ${missingCount}</span>
                    </div>

                    <div class="quality-bar">
                        <div class="quality-segment real" style="width: ${(realCount/total*100)}%;"></div>
                        <div class="quality-segment estimate" style="width: ${(estimateCount/total*100)}%;"></div>
                        <div class="quality-segment missing" style="width: ${(missingCount/total*100)}%;"></div>
                    </div>

                    <div class="quality-notes">
                        <small>📝 共 ${total} 個指標，${((realCount/total)*100).toFixed(0)}% 為真實數據</small>
                    </div>
        `;

        html += '</div></div>';
        return html;
    }

    /**
     * 獲取列標籤
     */
    static getColumnLabel(col) {
        const labels = {
            'eps': 'EPS (每股盈餘)',
            'revenue': '營收 (B)',
            'netIncome': '淨收益 (B)',
            'operatingIncome': '營業收入 (B)',
            'operatingMargin': '營業利益率 (%)',
            'fcf': '自由現金流 (B)',
            'roe': 'ROE (%)',
            'netMargin': '淨利率 (%)',
            'debtRatio': '負債比 (%)',
            'year': '年份'
        };
        return labels[col] || col;
    }
}

// CSS 樣式
const ENHANCED_STYLES = `
    /* 數據顯示 */
    .data-value {
        font-weight: 600;
        color: #1f2937;
    }

    .data-unavailable {
        color: #ef4444;
        font-style: italic;
        opacity: 0.7;
    }

    .data-with-meta {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* 徽章 */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.4rem;
        border-radius: 0.2rem;
        font-size: 0.7rem;
        font-weight: 600;
        white-space: nowrap;
    }

    .badge-real {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #86efac;
    }

    .badge-estimate {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fcd34d;
    }

    .badge-timestamp {
        background-color: #dbeafe;
        color: #1e3a8a;
        border: 1px solid #93c5fd;
    }

    /* 表格增強 */
    .financial-table-enhanced {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
        margin: 1rem 0;
    }

    .financial-table-enhanced thead {
        background-color: #f3f4f6;
        font-weight: 600;
    }

    .financial-table-enhanced th {
        border: 1px solid #e5e7eb;
        padding: 0.75rem;
        text-align: center;
    }

    .financial-table-enhanced th small {
        display: block;
        font-size: 0.7rem;
        font-weight: 400;
        opacity: 0.7;
        margin-top: 0.25rem;
    }

    .financial-table-enhanced td {
        border: 1px solid #e5e7eb;
        padding: 0.75rem;
        text-align: center;
    }

    .financial-table-enhanced .year-cell {
        font-weight: 600;
        background: #f9fafb;
        text-align: left;
    }

    .financial-table-enhanced .data-cell.missing-data {
        background-color: #fef2f2;
        color: #991b1b;
    }

    /* 統計容器 */
    .stats-container {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }

    .stats-main {
        margin-bottom: 1rem;
    }

    .stat-item {
        text-align: center;
    }

    .stat-label {
        font-size: 0.85rem;
        color: #6b7280;
        margin-bottom: 0.5rem;
    }

    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f2937;
    }

    .stat-percentage {
        font-size: 0.9rem;
        color: #667eea;
    }

    .stats-metadata {
        border-top: 1px solid #e5e7eb;
        padding-top: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        font-size: 0.85rem;
        color: #6b7280;
    }

    .meta-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* 品質卡 */
    .quality-card {
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 0.75rem;
        overflow: hidden;
        margin: 1rem 0;
    }

    .quality-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        font-weight: 600;
    }

    .quality-content {
        padding: 1rem;
    }

    .quality-stat {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }

    .quality-badge {
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-size: 0.85rem;
        font-weight: 600;
        flex: 1;
        text-align: center;
    }

    .quality-badge.real {
        background: #dcfce7;
        color: #166534;
    }

    .quality-badge.estimate {
        background: #fef3c7;
        color: #92400e;
    }

    .quality-badge.missing {
        background: #fee2e2;
        color: #991b1b;
    }

    .quality-bar {
        display: flex;
        height: 20px;
        border-radius: 0.5rem;
        overflow: hidden;
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
    }

    .quality-segment {
        transition: width 0.3s ease;
    }

    .quality-segment.real {
        background: #10b981;
    }

    .quality-segment.estimate {
        background: #f59e0b;
    }

    .quality-segment.missing {
        background: #ef4444;
    }

    .quality-notes {
        background: #f3f4f6;
        padding: 0.75rem;
        border-radius: 0.5rem;
        text-align: center;
        color: #6b7280;
    }
`;

// 導出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FinancialDisplayEnhanced, ENHANCED_STYLES };
}
