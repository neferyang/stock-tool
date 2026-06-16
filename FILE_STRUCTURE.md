# 📁 檔案結構指南

**最後更新**：2026-06-08  
**整理狀態**：✅ 完成  
**結構版本**：v1.0

---

## 🗂️ 目錄結構

```
stock-tool/
├── 📄 核心文件（主應用）
│   ├── index.html                    ⭐ 主應用程式（3.1M）
│   └── test-2026-eps.html            測試工具
│
├── 📋 計劃文檔（當前用途 - 根目錄保留）
│   ├── README.md                     📖 項目說明
│   ├── TOMORROW_WORKPLAN.md          📅 明天工作計劃
│   ├── PROGRESS_TRACKER.md           📊 進度追蹤
│   ├── SESSION_SUMMARY.md            📝 本次會話總結
│   ├── IMPROVEMENT_PLAN_v6_1.md      🎯 v6.1 改善計劃
│   ├── LEGAL_PERSON_PLAN.md          🏢 法人面功能規劃
│   └── TROUBLESHOOTING.md            🔧 故障排除指南
│
├── 📂 _docs/                         歸檔文檔（參考用）
│   ├── SYSTEM_STATUS_REPORT.md       完整狀態分析
│   ├── DECISION_MATRIX.md            三方案決策對比
│   ├── CURRENT_STATE_SUMMARY.md      當前狀態摘要
│   ├── VALUATION_LOGIC_SYNC_REPORT.md 估值邏輯修正說明
│   └── TEST_AND_OPTIMIZATION_REPORT.md v6.05/v6.06 測試報告
│
├── 📂 _data/                         數據檔案（內嵌數據）
│   ├── financial_db_all_twse.js      TWSE 完整財務數據（1.4M）
│   ├── financial_db_complete.js      合併後的完整數據（2.9M）
│   └── financial_db_output.js        輸出格式化數據（43K）
│
├── 📂 crawler/                       爬蟲系統（已禁用）
│   ├── mops_crawler.py               MOPS 爬蟲
│   ├── validate_mops_data.py         數據驗證工具
│   └── README_v607.md                爬蟲文檔
│
└── 📂 .github/                       CI/CD 工作流（自動化）
    └── workflows/
        ├── mops_crawler.yml          爬蟲工作流
        └── update-financial-data.yml 財務數據更新
```

---

## 📌 各檔案用途說明

### ⭐ 核心文件（必需）

#### `index.html` (3.1M)
- **用途**：主應用程式
- **包含**：HTML + CSS + JavaScript (全合一)
- **功能**：股票估價分析、技術指標、企業診斷卡
- **版本**：v6.04（穩定）
- **狀態**：✅ 生產環境

#### `test-2026-eps.html` (12K)
- **用途**：測試工具
- **功能**：測試 2026 年度 EPS 推估功能
- **使用場景**：開發測試、驗證新功能
- **狀態**：⚠️ 測試用（功能已禁用）

---

### 📋 計劃文檔（根目錄 - 當前活用）

#### `README.md` (7.7K) ⭐ 必讀
- **用途**：項目說明書
- **包含**：
  - 項目概述
  - 快速開始指南
  - 功能列表
  - 版本歷史
- **更新頻率**：每次發布時更新

#### `TOMORROW_WORKPLAN.md` (6.4K) 📅 明天用
- **用途**：明天的詳細工作計劃
- **包含**：
  - v6.1.0 三個修改任務
  - 詳細的代碼位置
  - 逐步驗證清單
  - 預計耗時
- **有效期**：2026-06-09
- **行動**：明天開始時參考

#### `PROGRESS_TRACKER.md` (4.1K) 📊 進度管理
- **用途**：進度追蹤表
- **包含**：
  - 每日工作進度
  - 質量指標
  - 下一個檢查點
- **更新頻率**：每天更新

#### `SESSION_SUMMARY.md` (5.5K) 📝 本次會話記錄
- **用途**：本次會話的完整總結
- **包含**：
  - 會話成果
  - 決策過程
  - 暫存內容
  - 下次會話檢查清單
- **備份**：✅ 完整記錄

#### `IMPROVEMENT_PLAN_v6_1.md` (19K) 🎯 改善計劃
- **用途**：v6.1 版本的詳細改善計劃
- **包含**：
  - 三階段改善內容
  - 每個任務的詳細描述
  - 產業防呆機制
- **狀態**：進行中

#### `LEGAL_PERSON_PLAN.md` (8.2K) 🏢 功能規劃
- **用途**：法人面模組的完整規劃
- **包含**：
  - 融資融券數據結構
  - 法人持股數據結構
  - UI 設計模板
  - 4 階段實施計劃
- **優先級**：v6.2.0 功能

#### `TROUBLESHOOTING.md` (3.8K) 🔧 故障排除
- **用途**：常見問題診斷指南
- **包含**：
  - API 連接問題排查
  - 緩存問題解決
  - 瀏覽器相容性
  - 本地文件測試方法
- **使用場景**：系統出現問題時參考

---

### 📂 _docs/ 文件夾（歸檔 - 參考用）

放置已完成、但當前不需要日常參考的文檔。

#### `SYSTEM_STATUS_REPORT.md`
- 完整的系統分析報告
- 包含所有工作的詳細記錄
- 當需要查閱完整背景時參考

#### `DECISION_MATRIX.md`
- 三種方案的對比表
- 決策過程的記錄
- 當需要重新評估方案時參考

#### `CURRENT_STATE_SUMMARY.md`
- 當前狀態的快速摘要
- 簡潔版本的狀態報告
- 當需要快速了解狀態時參考

#### `VALUATION_LOGIC_SYNC_REPORT.md`
- 估值邏輯修正的詳細說明
- 修改代碼和邏輯的對應關係
- 當需要理解修改細節時參考

#### `TEST_AND_OPTIMIZATION_REPORT.md`
- v6.05/v6.06 的測試報告
- 歷史版本的優化記錄
- 當需要了解歷史優化時參考

---

### 📂 _data/ 文件夾（數據檔案）

存放內嵌的財務數據檔案。

#### `financial_db_all_twse.js` (1.4M)
- TWSE 上市公司的完整財務數據
- 包含：EPS、ROE、淨利率、FCF、負債比等
- 更新頻率：季度更新

#### `financial_db_complete.js` (2.9M)
- 合併後的完整數據集
- 包含所有上市、上櫃、興櫃公司
- 用於本地備用時的數據源

#### `financial_db_output.js` (43K)
- 格式化輸出的數據
- 用於測試和驗證
- 緊湊格式

---

### 📂 crawler/ 文件夾（已禁用）

MOPS 爬蟲系統，當前因堆棧溢出問題已禁用。

#### `mops_crawler.py`
- Python 爬蟲，用於自動抓取 MOPS 數據
- **狀態**：⚠️ 禁用（導致堆棧溢出）

#### `validate_mops_data.py`
- 數據驗證工具
- 檢查爬蟲結果的完整性和準確性

#### `README_v607.md`
- 爬蟲系統的詳細文檔

---

### 📂 .github/workflows/ 文件夾（CI/CD）

GitHub Actions 自動化工作流，定期執行爬蟲和數據更新。

#### `mops_crawler.yml`
- 週期性執行 MOPS 爬蟲
- 當前因堆棧溢出已禁用

#### `update-financial-data.yml`
- 自動更新財務數據
- 定時觸發（例如每週一）

---

## 🎯 使用指南

### 日常使用（根目錄優先）

**需要快速參考**：
1. `README.md` - 項目說明
2. `TOMORROW_WORKPLAN.md` - 今天的任務
3. `PROGRESS_TRACKER.md` - 進度檢查

**需要詳細資訊**：
1. `SESSION_SUMMARY.md` - 會話記錄
2. `IMPROVEMENT_PLAN_v6_1.md` - 改善計劃
3. `LEGAL_PERSON_PLAN.md` - 功能規劃

**遇到問題**：
1. `TROUBLESHOOTING.md` - 故障排除
2. `_docs/SYSTEM_STATUS_REPORT.md` - 完整分析

### 開發測試

```
# 主應用
file:///C:/Users/AD83734/stock-tool/index.html

# 測試工具
file:///C:/Users/AD83734/stock-tool/test-2026-eps.html
```

### 查看歸檔文檔

```
# 查看完整系統分析
cat _docs/SYSTEM_STATUS_REPORT.md

# 查看決策過程
cat _docs/DECISION_MATRIX.md
```

---

## 🔄 整理規則

### ✅ 根目錄保留（當前活用）
- 實施計劃（TOMORROW_WORKPLAN.md）
- 進度追蹤（PROGRESS_TRACKER.md）
- 參考指南（README.md、TROUBLESHOOTING.md）
- 功能規劃（IMPROVEMENT_PLAN_v6_1.md、LEGAL_PERSON_PLAN.md）
- 會話記錄（SESSION_SUMMARY.md）

### 📂 移到 _docs/（參考用）
- 完整分析報告（SYSTEM_STATUS_REPORT.md）
- 決策過程（DECISION_MATRIX.md）
- 歷史報告（TEST_AND_OPTIMIZATION_REPORT.md）
- 修改說明（VALUATION_LOGIC_SYNC_REPORT.md）

### 📂 移到 _data/（數據檔案）
- JavaScript 數據檔案（financial_db_*.js）

---

## 📊 現狀統計

| 類別 | 檔案數 | 大小 | 狀態 |
|------|--------|------|------|
| 核心應用 | 2 | 3.1M | ✅ |
| 計劃文檔（根目錄） | 7 | 55K | ✅ |
| 歸檔文檔（_docs） | 5 | 40K | 📂 |
| 數據檔案（_data） | 3 | 4.3M | 📂 |
| 爬蟲系統 | 3 | - | ⚠️ 禁用 |
| CI/CD 工作流 | 2 | - | ⚠️ 禁用 |

**總大小**：約 7.4M（主要是 index.html 和數據文件）

---

## 🚀 下次整理計劃

- [ ] 週一：評估是否刪除或歸檔 financial_db_*.js
- [ ] 週二：評估爬蟲系統是否需要重啟
- [ ] 周三：建立自動化整理腳本

---

**檔案結構整理完成！** ✅

