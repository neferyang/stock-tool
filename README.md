# 📊 股票估價分析工具

**最新版本**：v6.1（改善計劃中）  
**當前穩定版**：v6.07（MOPS 爬蟲系統）  
**上一穩定版**：v6.06（2026 年度 EPS 推估）

---

## 🎯 項目概述

完整的 **台灣股票估價分析工具**，支援：
- ✅ 台灣上市、上櫃、興櫃股票（2,327 家）
- ✅ 美國股票 + ETF
- ✅ 8 種估值模型（P/E、P/B、GGM 等）
- ✅ 實時技術指標（RSI、MACD、K/D、Bollinger Bands）
- ✅ 企業健康診斷卡（4 項財務指標）
- ✅ MOPS 爬蟲系統（自動更新季度 EPS）

---

## 📁 項目結構

```
stock-tool/
├─ 📄 核心程式
│  ├─ index.html                      主應用程序（155KB）
│  └─ test-2026-eps.html              測試工具
│
├─ 📚 文檔 & 計劃
│  ├─ README.md                       本文件
│  ├─ IMPROVEMENT_PLAN_v6_1.md        v6.1 改善計劃
│  ├─ TEST_AND_OPTIMIZATION_REPORT.md v6.05/v6.06 測試報告
│  └─ .gitignore                      Git 配置
│
├─ 🔄 爬蟲系統 (v6.07)
│  ├─ crawler/
│  │  ├─ mops_crawler.py              MOPS 爬蟲（Python）
│  │  ├─ validate_mops_data.py        數據驗證工具
│  │  ├─ README_v607.md               v6.07 詳細文檔
│  │  ├─ mops_2026_data.json          爬蟲結果（自動生成）
│  │  └─ validation_report.json       驗證報告（自動生成）
│  │
│  └─ .github/
│     └─ workflows/
│        ├─ mops_crawler.yml          週期爬蟲工作流
│        └─ update-financial-data.yml 財務數據更新工作流
│
└─ 🗂️ 其他
   └─ .gitignore                      排除臨時文件
```

---

## 🚀 快速開始

### 在線使用（推薦）
```
https://neferyang.github.io/stock-tool/
```

### 本地開發
```bash
# 克隆倉庫
git clone https://github.com/neferyang/stock-tool.git
cd stock-tool

# 在本地瀏覽器打開
open index.html  # macOS
# 或在 Windows 中雙擊 index.html
```

### 運行 MOPS 爬蟲（Python）
```bash
cd crawler

# 安裝依賴
pip install requests beautifulsoup4

# 運行爬蟲
python mops_crawler.py

# 驗證數據
python validate_mops_data.py

# 查看結果
cat mops_2026_data.json
cat validation_report.json
```

---

## 📋 版本歷史

| 版本 | 日期 | 主要功能 | 狀態 |
|------|------|--------|------|
| **v6.07** | 2026-06-08 | MOPS 爬蟲 + 數據驗證 | ✅ 穩定 |
| **v6.06** | 2026-06-08 | 2026 年度 EPS 推估 UI | ✅ 穩定 |
| **v6.05** | 2026-06-08 | MOPS 爬蟲 + 緩存系統 | ✅ 穩定 |
| **v6.04** | 2026-06-08 | 混合方案：TWSE PE + 實時 EPS | ✅ 穩定 |
| **v6.1（計劃）** | 2026-06-09 ~ 06-12 | 數據修復 & UI 優化 | 📋 進行中 |
| **v6.2.0（計劃）** | 2026-06-12 | 完整整合版本 | 📋 計劃中 |

---

## 🎯 v6.1 改善計劃（進行中）

根據系統參考建議，制定三階段改善計劃：

### 第一階段：底層數據與邏輯除錯（6月9日）
- ✅ 修復 EPS 數據一致性
- ✅ 同步估值邏輯判定
- **預期成效**：零矛盾

### 第二階段：估值模型動態適配（6月10日）
- ✅ 產業防呆機制
- ✅ 明確財報單位標示
- **預期成效**：目標價精準度 +50%

### 第三階段：介面降噪與視覺動線（6月11日）
- ✅ 收敏複雜面板
- ✅ 動態視覺警示
- ✅ 圖表軸自動縮放
- **預期成效**：決策效率 +3 倍

**詳細計劃**：見 `IMPROVEMENT_PLAN_v6_1.md`

---

## 📊 核心功能

### 1. 估值分析
```
8 種模型同時計算：
├─ P/E 本益比法
├─ P/B 股價淨值比
├─ PEG 相對本益比
├─ 股息折現（GGM）
├─ FCF 折現（DCF）
├─ 成長率調整
├─ 產業平均法
└─ 綜合評分
```

### 2. 技術分析
```
實時指標：
├─ RSI 相對強度指數
├─ MACD 指數平滑異同平均線
├─ K/D 隨機指標
├─ Bollinger Bands 布林帶
└─ 5 條移動平均線（MA5/10/20/60/240）
```

### 3. 企業診斷卡
```
4 項財務指標：
├─ ROE 股東權益報酬率
├─ 營業利益率
├─ FCF 自由現金流
└─ 負債比率

評級系統：✅ 優秀 | 🟢 良好 | 🟡 普通 | 🔴 風險
```

### 4. 建議系統
```
買賣建議：
├─ 🟢 買進（估值低估 + 技術面）
├─ 🔵 持有（估值合理）
├─ 🔴 賣出（估值高估）
└─ 含重大公告提示
```

---

## 🔄 數據來源

### 實時數據
| 數據類型 | 來源 | 更新頻率 |
|---------|------|---------|
| 股價、K線 | Yahoo Finance | 實時 |
| P/E、P/B、股利率 | TWSE/TPEX API | 實時 |
| 季度 EPS | MOPS（爬蟲） | 週一 14:00 |
| 5年財報 | FINANCIAL_DB | 手動更新 |

### API 端點
```
TWSE: https://openapi.twse.com.tw/
Yahoo Finance: https://query1.finance.yahoo.com/
MOPS: https://mops.twse.com.tw/
```

---

## 🧪 測試工具

### 前端測試
```
test-2026-eps.html
├─ 單支股票測試
├─ 批量測試（5 支股票）
├─ 緩存管理
└─ 詳細日誌輸出
```

### 後端測試
```
crawler/validate_mops_data.py
├─ 爬蟲成功檢查
├─ 季度數據完整性驗證
├─ EPS 值合理性檢查
└─ 與官方數據對比（誤差 < 2%）
```

**測試文檔**：見 `TEST_AND_OPTIMIZATION_REPORT.md`

---

## 📈 使用統計

- **支持股票數**：2,327 家（台灣全市場）
- **估值模型**：8 種
- **技術指標**：15+ 種
- **K線數據**：5 年歷史
- **財報數據**：5 年歷史

---

## 🛠️ 開發指南

### 開發環境要求
```
- 瀏覽器：Chrome / Firefox / Safari（最新版）
- Python 3.8+（如果運行爬蟲）
- Git（版本控制）
```

### 本地修改 & 測試
```bash
# 1. 編輯 index.html
vim index.html

# 2. 在瀏覽器打開本地文件測試
open index.html

# 3. 推送到 GitHub
git add index.html
git commit -m "描述你的改動"
git push origin main
```

### GitHub Pages 自動部署
```
推送到 main 分支後，GitHub Pages 自動更新
訪問：https://neferyang.github.io/stock-tool/
```

---

## 🐛 已知限制 & 改進計劃

### 現有限制
- ADR 股票（美股在台灣交易）混入可能性（v6.1 修復中）
- 部分過時股票列表（已刪除）
- 介面複雜度較高（v6.1.2 改善中）

### 計劃改進
- [ ] v6.1.0（6/9）：數據修復
- [ ] v6.1.1（6/10）：模型最適化
- [ ] v6.1.2（6/11）：UI 優化
- [ ] v6.2.0（6/12）：整合上線
- [ ] v6.3.0（計劃中）：行業周期調整
- [ ] v6.4.0（計劃中）：長期監控儀表板

---

## 📞 支持 & 回報

### 問題回報
```
GitHub Issues: https://github.com/neferyang/stock-tool/issues
```

### 開發文檔
```
├─ IMPROVEMENT_PLAN_v6_1.md   改善計劃（詳細）
├─ TEST_AND_OPTIMIZATION_REPORT.md  測試報告
└─ crawler/README_v607.md     爬蟲文檔
```

---

## 📄 許可證

MIT License - 自由使用、修改、分發

---

## 👨‍💻 開發者

**Claude** + **用戶**  
共同開發的股票估價分析工具

**最後更新**：2026-06-08  
**聯繫方式**：GitHub Issues

---

## 🔗 相關鏈接

| 鏈接 | 說明 |
|------|------|
| [GitHub 倉庫](https://github.com/neferyang/stock-tool) | 源代碼 |
| [線上工具](https://neferyang.github.io/stock-tool/) | 使用入口 |
| [TWSE OpenAPI](https://openapi.twse.com.tw/) | 數據源 |
| [MOPS](https://mops.twse.com.tw/) | 財務公告 |

---

**享受分析！** 📈

