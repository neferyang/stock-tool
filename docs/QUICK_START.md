# 🚀 快速開始 - GitHub Actions 自動化

## 5 分鐘設置指南

### ✅ 需要的文件清單

```
stock-tool (你的 GitHub 倉庫)
├── update_financial_data.py              ← 已創建 ✓
├── .github/workflows/
│   └── update-financial-data.yml         ← 已創建 ✓
└── index.html                            ← 已有 ✓
```

---

## 📋 簡單 3 步設置

### Step 1️⃣: 上傳新文件到 GitHub

```bash
# 進入你的倉庫目錄
cd /path/to/your/stock-tool

# 複製以下文件到倉庫
# 1. update_financial_data.py
# 2. .github/workflows/update-financial-data.yml (新建目錄如果不存在)

# 提交到 GitHub
git add update_financial_data.py .github/
git commit -m "feat: add financial data auto-update via GitHub Actions"
git push origin main
```

### Step 2️⃣: 在 GitHub 中啟用 Actions

1. 打開: https://github.com/neferyang/stock-tool
2. 進入 **Settings** → **Actions** → **General**
3. 選擇 **Allow all actions and reusable workflows**
4. 點擊 **Save**

### Step 3️⃣: 手動觸發首次運行

1. 進入 **Actions** 頁籤
2. 左側選擇 **"Update Financial Data Daily"**
3. 點擊 **Run workflow** → **Run workflow**
4. 等待 5-10 分鐘完成 ✅

---

## 🎯 驗證成功

運行完成後，檢查以下內容：

✅ **GitHub 倉庫中**
- 查看 `financial_db_output.js` 文件是否已生成
- 查看 `financial_db_output.json` 是否包含最新數據

✅ **GitHub Pages 網站**
- 訪問: https://neferyang.github.io/stock-tool/
- 搜尋任何股票 (如: 2330)
- 確保企業診斷卡顯示正確的財務數據

✅ **Actions 日誌**
- 進入 Actions → 查看最新的 workflow run
- 應該看到綠色 ✅ 表示成功

---

## 📅 自動運行時間

```
每天 00:00 UTC (台北時間 08:00)
自動執行以下操作:

1. 獲取 30 支股票的最新財務數據 (FinMind API)
2. 生成 JavaScript 常數
3. 自動提交到 GitHub
4. 更新 GitHub Pages (約 30 秒後生效)
```

---

## 🔧 如果遇到問題

### 工作流沒有執行？

```bash
# 1. 檢查 .github/workflows/ 目錄是否存在且包含 .yml 文件
ls -la .github/workflows/

# 2. 驗證文件格式（YAML 語法）
# 使用 https://www.yamllint.com/ 檢查

# 3. 檢查 GitHub Actions 是否啟用
# Settings → Actions → 確認已允許
```

### 數據沒有更新到網頁？

```bash
# 1. 清除瀏覽器快取: Ctrl+Shift+Delete
# 2. 強制刷新: Ctrl+F5
# 3. 等待 30-60 秒（GitHub Pages 快取延遲）

# 4. 檢查 financial_db_output.js 是否已更新
git log --oneline financial_db_output.js | head -3
```

### API 調用失敗？

```bash
# 1. 檢查 FinMind API 狀態: https://api.finmind.com.tw/
# 2. 手動運行 Python 腳本測試（在本地或 GitHub Actions 中）
# 3. 查看完整的 Actions 日誌找出具體原因
```

---

## 📊 預期結果

### 首次運行

```
✅ 成功提交 30 支股票的財務數據
📊 生成的文件:
  - financial_db_output.js (自動生成的 JavaScript 代碼)
  - financial_db_output.json (JSON 備份)
  
⏱️ 耗時: 約 5-8 分鐘
```

### 後續每日更新

```
時間        事件
─────────────────────────────
08:00      ⏰ 自動運行
08:05      📡 獲取 API 數據
08:08      ✅ 完成並提交
08:09      🌐 GitHub Pages 更新
```

---

## 🎉 完成！

現在你的股票估價工具已經：

✅ 每天自動更新 30 支股票的真實財務數據  
✅ 自動推送到 GitHub  
✅ 自動更新 GitHub Pages 網站  
✅ 完全免費，無需任何配置  
✅ 無需手動干預

**訪問你的網站：** https://neferyang.github.io/stock-tool/

---

## 📚 更多幫助

- **詳細文檔**: 查看 `GITHUB_ACTIONS_SETUP.md`
- **故障排查**: 見上方「如果遇到問題」
- **自定義時間**: 編輯 `.github/workflows/update-financial-data.yml` 的 `cron` 欄位

---

**下一步：**
1. ✅ 上傳文件到 GitHub
2. ✅ 啟用 GitHub Actions
3. ✅ 首次手動測試
4. ✅ 驗證結果

祝你成功！ 🚀
