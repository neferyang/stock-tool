# 股票估價分析工具 - 股票資料更新指南

## 📊 目前狀態

- **應用版本**：v4.15.4
- **搜尋資料來源**：三層備援機制
  1. TWSE 官方 API（直連）
  2. TWSE 官方 API（corsproxy 代理）
  3. **本地 JSON 檔案** `twse-stocks.json`

- **目前包含**：150+ 支常見股票（包括上市、上櫃、ETF）

---

## 🚀 完整資料下載（推薦）

### 方法 1：自動化下載（最簡單）

#### Windows 用戶：
```powershell
# 1. 打開 PowerShell
# 2. 進入應用目錄
cd "C:\Users\AD83734\OneDrive - 和泰汽車-經銷商\桌面\Claude-workspace\outputs\github-pages"

# 3. 執行 Python 下載腳本
python download-stocks.py
```

#### Mac/Linux 用戶：
```bash
cd /path/to/github-pages
python3 download-stocks.py
```

### 方法 2：手動下載（需要 Python）

運行上述命令後，會自動：
- ✅ 從 TWSE 官方 API 下載所有 **上市公司**（1500+ 支）
- ✅ 從 TPEX 官方 API 下載所有 **上櫃公司**（數百支）
- ✅ 添加主要 **ETF**（50+ 支）
- ✅ 添加常見 **興櫃**（數十支）

**生成檔案**：`twse-stocks-full.json`（包含 1500+ 支股票）

---

## 📋 股票資料來源

| 來源 | 說明 | 備註 |
|------|------|------|
| **TWSE 官方 API** | 台灣上市公司 | https://openapi.twse.com.tw/ |
| **TPEX 官方 API** | 台灣上櫃公司 | https://www.tpex.org.tw/ |
| **本地 JSON** | 預定義的 ETF 和興櫃 | `twse-stocks.json` |

---

## 🔧 應用配置

### 更新搜尋資料

下載完整資料後，有三種方式更新應用：

#### 方式 1：覆蓋現有 JSON（推薦）
```bash
# 將下載的資料改名為應用使用的檔案
mv twse-stocks-full.json twse-stocks.json
```

然後刷新應用（Ctrl+F5），應該看到：
```
✅ 台股數據已加載 (本地 JSON，1500+ 支上市公司)
```

#### 方式 2：修改應用代碼
編輯 `index.html`，找到 `initStockCache()` 函數，改為加載新檔案：
```javascript
const resp = await fetch('twse-stocks-full.json', ...);
```

---

## ✅ 驗證搜尋功能

下載完整資料後，測試搜尋：

1. **刷新應用**（Ctrl+Shift+Delete 清除緩存 → Ctrl+F5）
2. 搜尋以下股票，應該都能找到：
   - ✅ 「台積」→ 台積電 (2330)
   - ✅ 「群聯」→ 群聯 (8299)
   - ✅ 「和泰」→ 和泰 (2207)
   - ✅ 「長榮」→ 長榮 (2603)
   - ✅ 「中信」→ 中信金 (2891)
   - ✅ 「台灣50」→ 0050 (ETF)

---

## 📊 資料統計

完整下載後，應該包含：

| 類型 | 數量 |
|------|------|
| 上市公司 | 1500+ |
| 上櫃公司 | 500+ |
| ETF | 50+ |
| 興櫃 | 數十 |
| **總計** | **2000+** |

---

## 🐛 常見問題

### Q: 搜尋仍然找不到某些股票？
**A:** 
1. 確認已執行 `python download-stocks.py`
2. 確認已覆蓋 `twse-stocks.json`
3. 清除瀏覽器緩存（Ctrl+Shift+Delete）並硬刷新（Ctrl+F5）

### Q: 下載腳本失敗？
**A:** 
- 確認有網路連線
- 確認 Python 3 已安裝（`python --version`）
- 手動訪問 API 檢查是否可用：
  - TWSE: https://openapi.twse.com.tw/v1/opendata/t187ap03_L
  - TPEX: https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_download/stk_quote_download.php?l=zh-tw&o=json

### Q: 應用加載緩慢？
**A:** 
1. 首次加載時會初始化搜尋資料，可能需要 1-2 秒
2. 之後搜尋速度會很快（本地緩存）
3. 可以清除 `twse-stocks.json`，回到更小的版本

---

## 🔄 定期更新

為確保搜尋資料最新，建議：
- **每月執行一次**：`python download-stocks.py`
- **或手動檢查** TWSE/TPEX 官方網站新增股票

---

## 📝 檔案結構

```
github-pages/
├── index.html                 # 主應用
├── twse-stocks.json          # 本地備援資料（150+ 支）
├── twse-stocks-full.json     # 完整資料（2000+ 支，執行腳本後生成）
├── download-stocks.py        # 自動下載腳本
└── README.md                 # 本文檔
```

---

## 🎯 下一步

1. **立即執行**：`python download-stocks.py`
2. **驗證結果**：覆蓋 `twse-stocks.json`，刷新應用
3. **測試搜尋**：嘗試搜尋各類股票

如有問題，查看應用控制台（F12）的日誌訊息。

---

**更新時間**：2026-06-04  
**版本**：v4.15.4
