# GitHub Actions 自動化設置指南

## 📋 概述

本指南說明如何設置 GitHub Actions 自動化每日更新股票財務數據。

**更新頻率**: 每天午夜 00:00 UTC (台北時間上午 8:00)  
**成本**: 完全免費（GitHub 提供每月 2,000 分鐘免費額度）  
**數據來源**: FinMind API (免費，無需認證)

---

## 🚀 設置步驟

### 步驟 1️⃣：上傳文件到 GitHub

確保以下文件在你的 GitHub 倉庫中：

```
stock-tool/
├── index.html                          # 主應用文件
├── update_financial_data.py            # 數據更新腳本
├── financial_db_output.js              # 生成的財務數據（自動生成）
├── financial_db_output.json            # JSON 備份（自動生成）
└── .github/
    └── workflows/
        └── update-financial-data.yml   # GitHub Actions 工作流 ← 新增
```

**上傳方式**:
```bash
# 1. 克隆倉庫
git clone https://github.com/neferyang/stock-tool.git
cd stock-tool

# 2. 創建 .github/workflows 目錄
mkdir -p .github/workflows

# 3. 複製工作流文件
# 將 update-financial-data.yml 複製到 .github/workflows/

# 4. 上傳到 GitHub
git add -A
git commit -m "feat: add GitHub Actions auto update workflow"
git push origin main
```

---

### 步驟 2️⃣：驗證 GitHub Actions 已啟用

1. 打開你的 GitHub 倉庫
2. 導航到 **Settings** → **Actions** → **General**
3. 確保 "Actions permissions" 選項為 **Allow all actions**
4. 點擊 **Save**

---

### 步驟 3️⃣：首次手動測試

1. 進入倉庫的 **Actions** 頁籤
2. 在左側找到 **"Update Financial Data Daily"** 工作流
3. 點擊右上角 **Run workflow**
4. 選擇 **main** 分支，點擊 **Run workflow**

**等待結果** (約 2-5 分鐘):
- ✅ 綠色勾號 = 成功
- ❌ 紅色 X = 失敗

---

### 步驟 4️⃣：檢查生成的數據

成功運行後，檢查以下文件：

1. **GitHub 倉庫中**:
   - `financial_db_output.js` - 最新的 JavaScript 數據
   - `financial_db_output.json` - 最新的 JSON 數據

2. **Actions Artifacts**:
   - 進入 Actions 頁籤 → 選擇最新的 Run
   - 下滑找到 **Artifacts** 部分
   - 下載 `financial-data-output.zip` 查看詳細數據

---

## 📅 自動化時間表

### 當前設置

```
時間       事件
─────────────────────────────
00:00 UTC → ⏰ 工作流開始執行
  ├─ 2 分鐘  拉取倉庫代碼
  ├─ 5 分鐘  調用 FinMind API 獲取 30 支股票數據
  └─ 1 分鐘  生成文件並推送到 GitHub
00:08 UTC → ✅ 完成
          → 08:08 台北時間 ← 本地時間

網頁自動更新  (GitHub Pages 快取 ~ 30 秒)
```

### 修改更新時間（可選）

編輯 `.github/workflows/update-financial-data.yml`:

```yaml
on:
  schedule:
    # 改為每天下午 3 點 (台北時間)
    - cron: '7 19 * * *'   # 19:07 UTC = 03:07 台北時間
```

**常用時間參考**:
```
台北時間         UTC 時間 (cron)
─────────────────────────────
12:00 (午夜)  → 0 4 * * *
01:00        → 0 5 * * *
03:00        → 0 7 * * *  (當前設置)
08:00        → 0 0 * * *  (當前設置)
```

---

## 🔧 工作流文件說明

### 主要步驟

| 步驟 | 說明 | 耗時 |
|------|------|------|
| **Checkout** | 拉取倉庫代碼 | < 1 分鐘 |
| **Python Setup** | 安裝 Python 3.10 | < 1 分鐘 |
| **Install Deps** | 安裝 requests 庫 | < 1 分鐘 |
| **Fetch Data** | 從 FinMind API 獲取數據 | 2-3 分鐘 |
| **Check Changes** | 檢查數據是否變化 | < 1 分鐘 |
| **Commit & Push** | 提交到 GitHub | < 1 分鐘 |

**總耗時**: 約 5-8 分鐘

---

## 📊 數據驗證

### 檢查更新狀態

**方式 1: GitHub 網頁界面**
1. 進入倉庫 → **Actions** 頁籤
2. 查看最新的 workflow run
3. 點擊看詳細日誌

**方式 2: 命令行**
```bash
# 查看最新提交
git log --oneline -5

# 查看最新數據文件
cat financial_db_output.json | head -20
```

### 驗證數據完整性

檢查 `financial_db_output.json` 中是否包含所有 30 支股票：

```bash
# 統計股票數量
grep -o '"[0-9]\{4\}":' financial_db_output.json | sort -u | wc -l

# 應該輸出: 30 (代表 30 支股票)
```

---

## ⚠️ 常見問題排查

### 問題 1: 工作流未執行

**原因**: GitHub Actions 未啟用或調度時間不對

**解決方案**:
1. 檢查 Settings → Actions → Permissions
2. 在 Actions 頁籤點擊 **Run workflow** 手動測試
3. 檢查時區（應為 UTC）

### 問題 2: FinMind API 超時

**原因**: API 請求過多或網絡波動

**解決方案**:
1. 檢查 GitHub Actions 日誌
2. 查看 https://status.finmind.com.tw 是否有故障
3. 手動重新運行工作流

### 問題 3: 數據未更新到網頁

**原因**: GitHub Pages 快取未清除

**解決方案**:
1. 等待 30-60 秒讓快取過期
2. 按 **Ctrl+Shift+Delete** 清除瀏覽器快取
3. 或按 **Ctrl+F5** 強制刷新頁面

### 問題 4: `financial_db_output.js` 無法找到

**原因**: 首次運行時腳本失敗

**解決方案**:
1. 在本地運行 `python update_financial_data.py`
2. 手動生成 `financial_db_output.js`
3. 提交到 GitHub

---

## 🔄 整合到網頁

### 方式 1: 使用生成的 JavaScript 文件（推薦）

在 `index.html` 中引入生成的數據文件：

```html
<!-- 替換原有的 const FINANCIAL_DB = {...} -->
<script src="financial_db_output.js"></script>
```

### 方式 2: 自動導入 JSON

```javascript
// 在 index.html 的 <script> 中添加
fetch('financial_db_output.json')
  .then(r => r.json())
  .then(data => {
    // 使用 data 替換 FINANCIAL_DB
    Object.assign(FINANCIAL_DB, data);
  });
```

---

## 📈 性能考慮

### API 調用頻率

- **30 支股票** × **1 次調用/股票** = 30 次 API 請求
- **FinMind 免費版**: 無限制（最多 10 req/sec）
- **GitHub Actions 用量**: ~2-3 分鐘 (在 2,000 分鐘月度額度內)

### 數據新鮮度

| 更新方式 | 延遲 | 成本 |
|---------|------|------|
| 每小時更新 | ✅ 實時性最強 | 計算量大 |
| **每天更新** | ✅ 夠實時 | **平衡最優** |
| 每周更新 | ⚠️ 可能過舊 | 計算最少 |

---

## 🎯 后续改進方向

### Phase 1 (當前) ✅
- ✅ 每日自動更新
- ✅ GitHub Actions 自動化
- ✅ 數據備份

### Phase 2 (可選)
- 實時數據推送（WebSocket）
- Slack/Discord 通知
- 數據異常告警

### Phase 3 (進階)
- 多時間間隔（如同時獲取周數據）
- 歷史數據備份到 AWS S3
- 數據對比和變化分析

---

## 📞 支持

### 調試日誌位置

GitHub Actions → 選擇 Workflow → 點擊 Run → 查看詳細日誌

**有用的日誌位置**:
- `Fetch Financial Data` - API 調用結果
- `Commit and Push Changes` - 提交狀態
- `Create Workflow Summary` - 更新統計

### 手動運行

如需立即更新（無需等待定時任務）:

1. 進入 GitHub 倉庫 → **Actions**
2. 選擇 **Update Financial Data Daily**
3. 點擊 **Run workflow** → **Run workflow**

---

## ✅ 檢查清單

完成以下所有項目以確保設置正確：

- [ ] `.github/workflows/update-financial-data.yml` 已上傳
- [ ] `update_financial_data.py` 已上傳
- [ ] GitHub Actions 已啟用
- [ ] 首次手動測試已通過 ✅
- [ ] `financial_db_output.js` 已生成
- [ ] `index.html` 已引入生成的數據文件
- [ ] GitHub Pages 網站顯示最新數據
- [ ] 工作流已添加到日程安排中

**全部完成**？🎉 你的股票估價工具現在已完全自動化！

---

**最後更新**: 2026-06-05  
**版本**: v4.32 + GitHub Actions  
**下一步**: 監控工作流運行，確保數據持續更新
