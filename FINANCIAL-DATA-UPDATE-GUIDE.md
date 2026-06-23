# 財報數據更新指南

## 系統架構

```
financial-data-template.json (財報數據源)
           ↓
merge-financial-data.py (合併腳本)
           ↓
index.html (FINANCIAL_DB 更新)
           ↓
網頁顯示
```

## 更新流程

### 1️⃣ 編輯財報數據

編輯 `financial-data-template.json`，填入最新的年度財報：

```json
{
  "stocks": {
    "2330": {
      "name": "台積電",
      "data": [
        {
          "year": "2025",
          "eps": 28.0,           // 每股盈餘
          "revenue": 980.0,      // 營收（百萬）
          "netIncome": 320.0,    // 淨利（百萬）
          "operatingIncome": 250.0,
          "operatingMargin": 25.5,  // 營業利率 (%)
          "fcf": 150.0,          // 自由現金流（百萬）
          "roe": 35.2,           // 股東報酬率 (%)
          "netMargin": 32.5,     // 淨利率 (%)
          "debtRatio": 15.0      // 負債比 (%)
        }
      ]
    }
  }
}
```

### 2️⃣ 運行合併腳本

```bash
python3 merge-financial-data.py
```

輸出示例：
```
2330: ✅ 已更新 (2025 EPS=28.0, ROE=35.2%)
3030: ✅ 已更新 (2025 EPS=20.73, ROE=28.2%)

✅ 完成 - 更新 2 支股票
```

### 3️⃣ 推送到 GitHub

```bash
git add financial-data-template.json index.html
git commit -m "update: 更新 2025 年度財報數據"
git push origin main
```

GitHub Pages 會自動部署最新版本。

---

## 數據來源

### 獲取財報數據的方法

#### 方法 1️⃣：MOPS 公開資訊觀測站（推薦）
- 網址：https://mops.twse.com.tw
- 搜尋股票代號 → 查詢財務報表
- 從中提取：EPS、ROE、淨利率、營業利率等

#### 方法 2️⃣：公司官網投資人關係部分
- 下載年度報告 PDF
- 提取財務指標

#### 方法 3️⃣：電子書籍平台（TWSE 或證交所公開資訊）
- 年度財務報表
- 季度財務報表

### 常見欄位解釋

| 欄位 | 單位 | 說明 | 範例 |
|------|------|------|------|
| eps | 元 | 每股盈餘 | 7.57 |
| revenue | 百萬元 | 年度營收 | 317.97 |
| netIncome | 百萬元 | 淨利 | 38.71 |
| roe | % | 股東權益報酬率 | 20.7 |
| netMargin | % | 淨利率 | 12.3 |
| debtRatio | % | 負債占資產比率 | 46.4 |
| operatingMargin | % | 營業利率 | 13.0 |
| fcf | 百萬元 | 自由現金流 | 19.35 |

---

## 自動化更新（可選）

### GitHub Actions 自動執行

在 `.github/workflows/` 中建立 `update-financials.yml`：

```yaml
name: Update Financial Data
on:
  schedule:
    - cron: '0 9 1 * *'  # 每月 1 日台北時間 17:00
  workflow_dispatch:     # 允許手動觸發

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Merge financial data
        run: python3 merge-financial-data.py
      
      - name: Commit and push
        run: |
          git config user.email "action@github.com"
          git config user.name "GitHub Action"
          git add index.html
          git commit -m "🔄 自動更新: 財報數據 $(date -u +'%Y-%m-%d')"
          git push
```

---

## 常見問題

### Q: 如何知道數據是否正確更新？
**A:** 查看網頁，搜尋股票代號，檢查「5年財報趨勢」圖表中最新年份的 EPS 值。

### Q: 能否同時更新多支股票？
**A:** 可以。在 `financial-data-template.json` 中添加多支股票的數據，一次運行腳本會全部更新。

### Q: 歷史數據（2021-2024）會被覆蓋嗎？
**A:** 不會。腳本只更新指定股票的 `data` 陣列。如果您提供了多年數據，會全部保留。

### Q: 如何驗證合併是否成功？
**A:** 
1. 查看腳本輸出中是否有 ✅ 標記
2. 在 index.html 中搜尋股票代號，檢查 EPS 值是否已更新

---

## 支持的股票

目前 `financial-data-template.json` 包含模板：
- 2207（和泰車）
- 3030（德律）
- 2330（台積電）

需要更新其他股票，請：
1. 在 `financial-data-template.json` 中添加新股票
2. 運行 `merge-financial-data.py`

---

## 文件清單

- **financial-data-template.json** - 財報數據源（需定期更新）
- **merge-financial-data.py** - 合併腳本（自動執行）
- **update-financial-data.py** - MOPS 爬蟲腳本（實驗性，可選）
- **index.html** - 主應用（自動更新，無需手動編輯）

---

## 支持

遇到問題？
1. 確認 JSON 格式正確（用線上 JSON 驗證工具檢查）
2. 確認數據單位正確（EPS 以元為單位，百分比去掉 % 符號）
3. 查看腳本執行日誌是否有錯誤信息
