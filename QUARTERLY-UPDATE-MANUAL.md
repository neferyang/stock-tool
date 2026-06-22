# 季度財報更新手冊

## 📅 自動更新計畫

系統已配置為**每季自動更新**財報數據。

| 季度 | 執行日期 | 台北時間 | UTC |
|------|---------|---------|-----|
| **Q1** | 2月1日 | 06:00 | 22:00 前一日 |
| **Q2** | 5月1日 | 06:00 | 22:00 前一日 |
| **Q3** | 8月1日 | 06:00 | 22:00 前一日 |
| **Q4** | 11月1日 | 06:00 | 22:00 前一日 |

---

## 🎯 更新流程

### 1️⃣ 自動執行（系統自動）

每季首日，GitHub Actions 會自動：
1. 嘗試從 MOPS 爬蟲獲取最新財報
2. 合併數據到 `index.html`
3. 推送至 GitHub Pages

### 2️⃣ 自動失敗時（需手動操作）

如果自動更新失敗（如 MOPS 無法訪問）：

#### 方式 A：手動編輯（推薦）
```bash
# 編輯模板
vi financial-data-template.json

# 填入最新季度數據
# 保存後執行合併
python3 merge-financial-data.py

# 推送
git add index.html
git commit -m "update: Q1 2026 季度財報更新"
git push
```

#### 方式 B：使用提取工具
```bash
# 嘗試從 MOPS 爬蟲手動抓取
python3 fetch-mops-financials.py

# 查看結果
cat financial-data-mops.json

# 如果成功，合併到 index.html
python3 merge-financial-data.py
```

---

## 🔄 手動觸發更新

### 從 GitHub UI 觸發

1. 進入 GitHub 倉庫 → **Actions** 標籤
2. 選擇 **「Quarterly Financial Data Update」**
3. 點擊 **「Run workflow」**
4. 選擇分支 **main**
5. 輸入股票代號（可選）：`2330,2207,3030`
6. 點擊 **「Run workflow」**

工作流會立即執行。

### 從命令行觸發

```bash
# 使用 GitHub CLI（需安裝）
gh workflow run quarterly-financial-update.yml \
  -f stocks="2330,2207,3030"
```

---

## 📊 編輯目標股票

編輯 `quarterly-update.config.json`：

```json
{
  "targetStocks": [
    {
      "code": "2330",
      "name": "台積電",
      "enabled": true      // 改為 false 以跳過
    },
    {
      "code": "2207",
      "name": "和泰車",
      "enabled": true
    },
    // 添加更多股票...
  ]
}
```

保存後，下次季度更新時會使用新的目標列表。

---

## 📋 更新檢查清單

每季更新前，確認：

- [ ] 公司已公佈年度或季度財報
- [ ] 數據包含以下欄位：
  - [ ] EPS（每股盈餘）
  - [ ] ROE（股東權益報酬率）
  - [ ] 淨利率
  - [ ] 負債比
  - [ ] 營業利率
  - [ ] 營收、淨利
  - [ ] FCF（自由現金流，可選）

- [ ] 數據格式正確：
  - [ ] 百分比去掉 `%` 符號
  - [ ] 營收單位統一為百萬元
  - [ ] 數字格式為數值，不含逗號

---

## ⚠️ 常見問題

### Q: 工作流執行失敗了怎麼辦？

**A:** 系統會自動建立一個 GitHub Issue 通知您。此時需要手動更新：

1. 從 MOPS 或公司官網獲取最新財報
2. 編輯 `financial-data-template.json`
3. 運行 `python3 merge-financial-data.py`
4. 推送變更

### Q: 可以同時更新多支股票嗎？

**A:** 可以。在 `financial-data-template.json` 的 `stocks` 物件中添加多支股票：

```json
{
  "stocks": {
    "2330": { "data": [...] },
    "2207": { "data": [...] },
    "1101": { "data": [...] }
  }
}
```

### Q: 歷史數據會被覆蓋嗎？

**A:** 不會。只要在 `data` 陣列中保留所有年份的數據，歷史數據會被保留。

### Q: 怎樣驗證更新是否成功？

**A:** 
1. 訪問網頁應用，搜尋股票代號
2. 查看「5年財報趨勢」圖表
3. 檢查最新年份的 EPS 值是否已更新

---

## 🔔 通知設置

### 接收更新通知

1. 進入倉庫設置 → **Notifications**
2. 選擇 **Watch** → **All Activity**
3. 接收所有 Actions 執行的通知

### 自訂通知

每次更新失敗時，GitHub 會自動建立 Issue（標籤：`財報數據`、`manual-action`）。

---

## 📞 支持

如遇問題：

1. 查看 `FINANCIAL-DATA-UPDATE-GUIDE.md` 獲取詳細用法
2. 檢查 GitHub Actions 日誌：**Actions** → **Quarterly Financial Data Update** → 最新執行
3. 查看自動建立的 Issue

---

## 📝 更新記錄

自動系統會維護更新歷史。查看提交日誌：

```bash
# 查看最近的財報更新提交
git log --oneline | grep "自動更新\|季度財報"
```

每次更新都會建立一個帶時間戳記的提交。

---

**下次季度更新時，系統會自動執行。如需手動更新或有任何問題，請參考本指南。** 📊
