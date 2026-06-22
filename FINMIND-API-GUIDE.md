# FinMind API 集成指南

## 概述

本系統集成 **FinMind API** 自動獲取台股真實財務數據。

- **數據來源**：FinMind（台灣免費金融數據平台）
- **支持指標**：EPS、ROE、淨利率、營業利率、負債比等
- **覆蓋年份**：2021-2025（5年歷史數據）
- **股票範圍**：前 50-100 支常交易股票

---

## 準備工作

### 1. 安裝依賴

```bash
pip install requests
```

### 2. 確保網絡連接

需要能夠訪問：
- `https://api.finmind.com.tw/` （FinMind API）

---

## 使用流程

### 步驟 1：獲取 FinMind 數據

在**有網絡連接**的環境中執行：

```bash
python3 finmind-data-fetcher.py
```

**輸出：**
- 自動查詢所有股票的財務數據
- 生成 `finmind-real-data.json` 文件
- 預計耗時：2-5 分鐘（取決於網絡速度）

**樣本輸出：**
```
[1/50] 2330 台積電... ✅ 成功
[2/50] 2207 和泰車... ✅ 成功
...
完成！成功: 50, 失敗: 0
```

### 步驟 2：導入到系統

將 FinMind 數據導入 FINANCIAL_DB：

```bash
python3 import-finmind-data.py
```

**輸出：**
```
導入進度：

2330: ✅ 新增股票
   └─ 年份：2021 → 2022 → 2023 → 2024 → 2025
2207: 🔄 更新現有股票
   └─ 年份：2021 → 2022 → 2023 → 2024 → 2025
...
導入完成：新增 X 支，更新 Y 支
✅ 已保存到 index.html
```

### 步驟 3：推送到 GitHub

```bash
git add index.html finmind-real-data.json
git commit -m "feat: 集成 FinMind API 真實台股財務數據

新增/更新股票的真實財務指標：
- EPS（每股收益）
- ROE（股東權益報酬率）
- 淨利率
- 營業利率
- 負債比

使用 FinMind API 自動獲取 2021-2025 年財務數據"

git push origin main
```

### 步驟 4：驗證效果

清除快取訪問網站：

```
Ctrl + Shift + R
https://neferyang.github.io/stock-tool/
```

搜尋任意股票，檢查數據是否為真實數據。

---

## API 限制與注意事項

### 速率限制

- **免費版**：600 requests/hour
- **建議**：每個請求間隔 0.2 秒（自動控制）

### 數據可用性

| 指標 | API 字段 | 可用性 |
|------|---------|--------|
| EPS | eps | ✅ 全部股票 |
| ROE | roe | ✅ 大部分股票 |
| 淨利率 | net_profit_margin | ✅ 大部分股票 |
| 營業利率 | operating_margin | ✅ 部分股票 |
| 負債比 | debt_ratio | ✅ 部分股票 |

### 常見問題

**Q: 查詢失敗怎麼辦？**
A: 檢查網絡連接，或稍後重試。系統會自動跳過失敗的股票。

**Q: 數據不完整怎麼辦？**
A: FinMind 可能沒有某些歷史年份的數據，系統會只導入可用的年份。

**Q: 如何更新已有的數據？**
A: 重新執行步驟 1-2，導入腳本會自動覆蓋舊數據。

---

## 完整工作流程

### 本地開發環境（推薦）

```bash
# 1. 獲取真實數據
python3 finmind-data-fetcher.py

# 2. 導入系統
python3 import-finmind-data.py

# 3. 本地測試（可選）
python3 -m http.server 8000
# 訪問 http://localhost:8000

# 4. 推送更新
git add .
git commit -m "feat: 更新 FinMind 真實數據"
git push origin main
```

### 自動化方案（GitHub Actions）

創建 `.github/workflows/update-finmind-data.yml`：

```yaml
name: Update FinMind Data

on:
  schedule:
    - cron: '0 0 * * 0'  # 每週日午夜執行
  workflow_dispatch:

jobs:
  update-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Fetch FinMind data
        run: python3 finmind-data-fetcher.py
      
      - name: Import to FINANCIAL_DB
        run: python3 import-finmind-data.py
      
      - name: Commit and push
        run: |
          git config user.name "FinMind Bot"
          git config user.email "bot@example.com"
          git add index.html finmind-real-data.json
          git commit -m "chore: 自動更新 FinMind 真實財務數據"
          git push
```

---

## 系統更新計劃

### Phase 1（已完成）
- ✅ 15 支重點股票的真實 MOPS 數據
- ✅ 數據驗證和年份排序修正

### Phase 2（FinMind 集成）
- ⏳ 前 50-100 支常交易股票的真實數據
- ⏳ 完整的 5 年財務指標

### Phase 3（自動化）
- 📅 GitHub Actions 週期更新
- 📅 實時數據監控
- 📅 擴展到全部 1,970+ 上市公司

---

## 支持與反饋

如遇問題，請檢查：
1. 網絡連接是否正常
2. Python 版本是否為 3.7+
3. 是否已安裝 requests 庫
4. FinMind API 是否正常運作

---

**最後更新**：2026-06-22
**狀態**：準備就緒，等待外網環境執行
