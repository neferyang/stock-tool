# 📊 股票估價分析工具

智能股票估價工具，支援台股、美股和 ETF，提供全面的估值分析。

## ✨ 功能特點

- 🔍 **智能搜尋** - 支援中文股票名稱、代號、英文代號
- 📈 **多模型估值** - 本益比、股價淨值比、DCF、GGM、PEG 等 8 種模型
- 📊 **技術分析** - K線圖表、MACD、RSI、布林通道等指標
- 💼 **基本面分析** - ROE、淨利率、現金流、負債比等財務指標
- 🏢 **33 種產業分類** - 官方標準 TWSE 產業分類
- 🌍 **國際市場支援** - Yahoo Finance 美股即時數據
- 📱 **響應式設計** - 完美適配手機、平板、桌面

## 🚀 快速開始

### 本地開發
```bash
# 無需安裝依賴，直接在瀏覽器打開
open index.html
```

### 線上使用
訪問：https://neferyang.github.io/stock-tool/

## 📋 支援的股票

- **台股** - 輸入 4-6 位數字代碼（自動加 .TW）
- **上櫃股** - 輸入代碼後自動嘗試 .TWO
- **美股** - 輸入英文代號（如 AAPL、SPY）
- **ETF** - 台股 ETF（0050、0051 等）

## 🔧 技術棧

- **前端** - Vanilla JavaScript (ES6+)
- **圖表** - Chart.js 4.4
- **資料來源** - Yahoo Finance、TWSE、FinHub
- **部署** - GitHub Pages + Vercel 後端代理
- **API 代理** - Vercel Serverless Functions

## 📦 主要文件

```
├── index.html              # 主應用（股票估價工具）
├── index_v6_ai.html        # 財金早報分頁
├── api/proxy.js            # Vercel 後端代理
├── vercel.json             # Vercel 配置
├── daily-report.json       # 每日財金早報數據
└── .github/workflows/      # GitHub Actions 自動化
```

## 🔄 自動更新

財金早報每天台北時間 06:00 自動更新。支援手動觸發：
- 進入 GitHub Actions
- 選擇 "Daily Financial Report Update"
- 點擊 "Run workflow"

## ⚙️ 環境設定

### GitHub Pages
- 分支：`main`
- 來源：根目錄
- HTTPS：已啟用

### Vercel 部署
- 專案名稱：stock-tool
- 自動部署：啟用（GitHub 連接）
- 後端代理：api/proxy.js

## 🐛 已知限制

- 免費 API 代理可能受流量限制
- 某些美股資料延遲 15 分鐘
- 歷史財報資料依賴 FinMind 免費配額

## 📝 版本

- 當前版本：v6.6.5
- 包含：完全 toFixed 安全防護、Vercel 代理優化、GitHub Actions 穩定性改善、財金早報多路徑加載優化

## 🤝 貢獻

提交 Issue 或 PR 以改進此工具。

## 📄 授權

MIT License - 自由使用和修改
