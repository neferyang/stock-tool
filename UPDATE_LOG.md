# 📊 財金早報更新日誌

## 自動化更新系統說明

### 🚀 工作原理

1. **自動運行時間**：每日台北時間 **06:00** (UTC 22:00)
2. **數據來源**：Yahoo Finance API + TWSE OpenAPI
3. **更新內容**：`daily-report.json` 文件
4. **部署方式**：GitHub Actions 自動化

### 📋 版本追蹤

網站上會顯示：
- ✅ **最後更新時間**：`daily-report.json` 的 `lastUpdated` 字段
- ✅ **版本號**：`daily-report.json` 的 `version` 字段
- ✅ **自動更新提交**：每次更新會產生帶時間戳的 Git 提交

### 📁 相關文件

| 文件 | 說明 |
|------|------|
| `daily-report.json` | 每日市場數據（每日早上6:00自動更新） |
| `.github/workflows/daily-report-update.yml` | GitHub Actions 工作流配置 |
| `scripts/update-daily-report.js` | 更新執行腳本 |
| `index.html` | 網站前端（從 JSON 動態加載） |

### 🔄 更新流程

```
[06:00 Taiwan Time]
       ↓
[GitHub Actions Triggers]
       ↓
[Run update-daily-report.js]
       ↓
[Fetch from Yahoo Finance & TWSE API]
       ↓
[Update daily-report.json]
       ↓
[Auto-commit with timestamp]
       ↓
[Push to GitHub]
       ↓
[GitHub Pages deploys automatically]
       ↓
[Website shows new data within 1-2 minutes]
```

### 📊 更新歷史

#### v1.0.1 - 2026-06-15
- ✅ 初始版本發佈
- ✅ 設置每日自動更新
- ✅ 從 Yahoo Finance 獲取市場指數
- ✅ 網站顯示更新時間和版本號
- ✅ 自動提交到 GitHub

### 🔧 手動更新（測試）

運行更新腳本：
```bash
cd stock-tool
node scripts/update-daily-report.js
```

### 📈 市場指數追蹤

每日自動更新以下指數：
- 🇺🇸 美國：道瓊、S&P 500、那斯達克
- 🇯🇵 日本：日經225
- 🇮🇳 印度：NIFTY 50
- 🇻🇳 越南：VN-Index
- 🇹🇼 台灣：加權指數
- 🥇 貴金屬：黃金

### ⚠️ 故障排除

| 問題 | 解決方案 |
|------|---------|
| 數據未更新 | 檢查 GitHub Actions 運行日誌 |
| 顯示舊時間 | 硬刷新瀏覽器（Ctrl+Shift+R） |
| API 無法連接 | 使用預設硬編碼數據（自動降級） |

### 📞 支援

- 📌 查看 GitHub Actions 運行狀態：https://github.com/neferyang/stock-tool/actions
- 📌 檢查最新提交：https://github.com/neferyang/stock-tool/commits/main
- 📌 報告問題：https://github.com/neferyang/stock-tool/issues

---

**上次更新**：此文件自動維護（首次版本 v1.0.1）
