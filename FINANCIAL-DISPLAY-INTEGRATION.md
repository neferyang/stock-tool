# 財務數據顯示工具集成指南

## 概述

將 `financial-display-utils.js` 集成到 `index.html`，改進財務數據的顯示效果。

## 集成步驟

### 1. 在 HTML 中添加腳本引用

在 `index.html` 的 `<head>` 標籤中添加：

```html
<script src="financial-display-utils.js"></script>
<style>
  /* 導入財務樣式 */
  @import url("financial-display-utils.js");
  
  /* 或在 <style> 標籤中嵌入 */
</style>
```

### 2. 改進財務指標顯示

**修改前的代碼（第 162186 行）：**
```javascript
function renderFinancialChart(financialData){
  // 原有邏輯，假設顯示數字時用 0.0 表示缺失
  // 例如：eps 值為 0.0 時不清楚是真 0 還是無數據
}
```

**修改後的代碼：**
```javascript
function renderFinancialChart(financialData){
  // 使用 financial-display-utils.js 中的工具
  const summary = FinancialDisplayFormatter.generateUpdateSummary(financialData);
  
  // 顯示進度條
  const progressBar = FinancialDisplayFormatter.generateProgressBar(summary);
  document.getElementById('financial-progress').innerHTML = progressBar;
  
  // 生成表格
  const table = FinancialDisplayFormatter.generateFinancialTable(financialData, {
    showStatus: true,
    highlightMissing: true,
    columns: ['eps', 'revenue', 'netIncome', 'roe', 'debtRatio']
  });
  document.getElementById('financial-table').innerHTML = table;
}
```

### 3. 改進數字顯示

**修改前：**
```javascript
// 存在的問題：0.0 既表示真 0，又表示無數據
const value = 0.0;
document.innerText = value.toFixed(2);  // 顯示 "0.00"，不清楚是什麼意思
```

**修改後：**
```javascript
// 使用格式化工具
const value = null; // 無數據用 null
const formatted = FinancialDisplayFormatter.formatNumber(value, {
  decimals: 2,
  zeroLabel: 'N/A'  // 缺失數據顯示 "N/A"
});
// 輸出：'N/A'
```

### 4. 添加狀態徽章

```javascript
// 為財務字段添加狀態指示
const badge = FinancialDisplayFormatter.createStatusBadge(value, {
  showDataSource: true,
  dataSource: 'MOPS',
  updateDate: '2026-06-23'
});
// 輸出: '<span class="financial-badge badge-valid">✓</span>'
```

### 5. 集成 CSS 樣式

將 `FINANCIAL_STYLES` 常數中的 CSS 添加到 `index.html` 的 `<style>` 標籤中，或在自己的 CSS 文件中：

```css
/* 財務數據表格 */
.financial-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
  margin: 1rem 0;
}

.financial-cell.missing-data {
  background-color: #fef2f2;  /* 淺紅色背景 */
  color: #991b1b;  /* 深紅色文字 */
}

.financial-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-updating {
  background-color: #fef3c7;  /* 黃色 */
  color: #92400e;
}

.badge-unavailable {
  background-color: #fee2e2;  /* 紅色 */
  color: #991b1b;
}
```

## 使用示例

### 示例 1：顯示財務指標表格

```javascript
const financialData = {
  name: '台積電 (2330)',
  data: [
    {
      year: '2025',
      eps: 16.25,
      revenue: 782.4,
      roe: 28.5,
      netMargin: 16.9,
      debtRatio: 18.2
    },
    {
      year: '2024',
      eps: null,  // 無數據
      revenue: null,
      roe: null,
      netMargin: null,
      debtRatio: null
    }
  ]
};

const table = FinancialDisplayFormatter.generateFinancialTable(financialData);
document.getElementById('financial-display').innerHTML = table;
```

### 示例 2：顯示更新進度

```javascript
const summary = FinancialDisplayFormatter.generateUpdateSummary(financialData);
// 輸出: { total: 30, updated: 15, pending: 15, percentage: 50 }

const progressBar = FinancialDisplayFormatter.generateProgressBar(summary);
// 輸出: <div class="progress-bar" style="width: 50%;">...

document.getElementById('progress-container').innerHTML = progressBar;
```

### 示例 3：格式化大數字

```javascript
const revenue = 782400; // 億元
const formatted = FinancialDisplayFormatter.formatLargeNumber(revenue, { decimals: 1 });
// 輸出: '782400.0'

// 或用於股票價格
const price = 650;
const display = FinancialDisplayFormatter.formatNumber(price, {
  decimals: 2,
  prefix: '$'
});
// 輸出: '$650.00'
```

## 修改清單

### 必須修改的部分

1. **Line 7 之後** - 添加 financial-display-utils.js 引用
2. **Line 162186** - 改進 renderFinancialChart() 函數
3. **財務指標顯示部分** - 使用新的格式化工具
4. **CSS 樣式** - 添加財務徽章和表格樣式

### 可選優化

1. 添加「數據更新進度」面板
2. 實現「缺失字段高亮」視覺效果
3. 添加「數據源和更新時間」提示
4. 實現「按需更新」按鈕

## 測試驗證

集成後需要測試以下情況：

1. **正常數據顯示**
   ```
   EPS: 16.25 ✓
   ```

2. **缺失數據顯示**
   ```
   EPS: N/A 🔴
   ```

3. **待更新狀態**
   ```
   EPS: 待更新 🟡
   ```

4. **進度條显示**
   ```
   ||||||||||||------- (50%)
   ```

## 性能考慮

- `financial-display-utils.js` 文件大小：~10KB
- 表格生成時間：< 100ms（對於 100 支股票）
- 進度條更新：實時無延遲

## 後續計劃

1. **自動化集成** - 創建集成腳本，自動修改 index.html
2. **實時更新** - 集成 WebSocket，實時推送數據更新
3. **導出功能** - 支持導出為 CSV/PDF 報告
4. **數據分析** - 添加多年度對比分析圖表

## 常見問題

**Q: 如何區分 0 和 N/A？**
A: 
- `0` = 真實值為零（例如某年沒有分紅）
- `null` = 無數據，顯示為 "N/A"
- 在表格中，null 值會高亮顯示

**Q: 進度條如何更新？**
A: 
```javascript
// 每次更新數據後調用
const summary = FinancialDisplayFormatter.generateUpdateSummary(financialData);
const bar = FinancialDisplayFormatter.generateProgressBar(summary);
document.getElementById('progress').innerHTML = bar;
```

**Q: 如何自定義顯示樣式？**
A: 修改 FINANCIAL_STYLES 中的 CSS，或在自己的 CSS 文件中覆蓋 `.financial-table` 等類的樣式。

---

**集成狀態：** Phase 3 進行中
**預計完成時間：** 1 小時
**下一步：** Phase 4 完整流程測試
