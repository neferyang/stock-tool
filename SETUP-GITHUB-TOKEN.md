# GitHub Token 自動化配置指南

## 📋 概述

財金早報頁面現已支持自動 GitHub Token 管理，用戶點擊「更新數據」按鈕時，系統會自動讀取 token 並觸發 GitHub Actions 工作流。

## 🔑 配置步驟（只需一次）

### 步驟 1：在 GitHub 中添加 Secret

1. 訪問你的 GitHub repo 設置：
   ```
   https://github.com/neferyang/stock-tool/settings/secrets/actions
   ```

2. 點擊 **「New repository secret」**

3. 填入以下信息：
   - **Name**: `GITHUB_TOKEN_CONFIG`
   - **Value**: 你的 GitHub Personal Access Token

4. 點擊 **「Add secret」**

#### 如何獲取 GitHub Personal Access Token：

1. 訪問 https://github.com/settings/tokens
2. 點擊「Generate new token (classic)」
3. 填寫信息：
   - **Token name**: `github-actions-config`
   - **Expiration**: 選擇「No expiration」或根據需要設置
   - **Scopes**: 選擇以下權限：
     - ✅ `repo` - 完整的 repo 訪問
     - ✅ `workflow` - 工作流訪問
4. 點擊「Generate token」
5. 複製生成的 token（只會顯示一次！）
6. 粘貼到 GitHub Secrets 的 Value 字段中

### 步驟 2：等待工作流運行（自動）

- GitHub Actions 會在每天台北時間 05:00 和 06:00 自動運行
- 工作流會自動生成 `github-config.json` 文件，其中包含你的 token
- 該文件會自動提交到 repo 中（GitHub Pages）

### 步驟 3：使用財金早報頁面

1. 訪問財金早報頁面：`index_v6_ai.html`
2. 點擊「🔄 更新數據」按鈕
3. 系統自動：
   - 讀取 `github-config.json` 中的 token
   - 觸發 GitHub Actions 工作流
   - 生成最新市場數據、分析和新聞
   - 1-2 分鐘後自動刷新頁面

## 🔄 Token 讀取優先順序

系統按以下順序自動讀取 token：

1. **優先 1**：`github-config.json` 中的 token（工作流自動生成）
2. **優先 2**：瀏覽器 `localStorage` 中的緩存
3. **備選**：提示用戶手動輸入

## 🛡️ 安全特性

✅ **Token 不在代碼中**
- Token 只存儲在 GitHub Secrets（加密）
- 不會在任何版本控制文件中暴露

✅ **自動刷新**
- `github-config.json` 在每次工作流運行時自動更新
- 確保使用最新的有效 token

✅ **智能緩存**
- 本地 `localStorage` 作為備選快取
- 減少不必要的遠程調用

✅ **完整的錯誤處理**
- Token 過期自動清除
- 失敗時有明確的錯誤提示

## 📊 工作流執行流程

當你點擊「更新數據」按鈕時：

```
1️⃣ 讀取 token（自動）
   ↓
2️⃣ 觸發 GitHub Actions 工作流
   ↓
3️⃣ 工作流執行 4 個步驟：
   - fetch-market-data.py
   - generate-market-analysis.py
   - generate-news-highlights.py
   - update-daily-report.js
   ↓
4️⃣ 生成 github-config.json（包含 token）
   ↓
5️⃣ 自動提交更新到 repo
   ↓
6️⃣ 1-2 分鐘後自動刷新頁面
```

## 🔗 相關 GitHub Pages

- **財金早報頁面**：`https://neferyang.github.io/stock-tool/index_v6_ai.html`
- **GitHub Actions 頁面**：`https://github.com/neferyang/stock-tool/actions`
- **Secrets 管理**：`https://github.com/neferyang/stock-tool/settings/secrets/actions`

## 📝 工作流配置文件

```yaml
# .github/workflows/daily-report-update.yml
```

### 觸發方式：
- ✅ 定時執行（台北 05:00 和 06:00）
- ✅ 手動觸發（workflow_dispatch）
- ✅ 其他工作流調用

### 執行步驟：
1. **fetch-market-data.py** - 抓取全球市場指數（美股、台股、日股等）
2. **generate-market-analysis.py** - 使用 Gemini AI 生成市場分析
3. **generate-news-highlights.py** - 從 Google News 抓取新聞並生成觀察
4. **update-daily-report.js** - 整合所有數據到 `daily-report.json`
5. **Generate config** - 生成 `github-config.json` 包含 token
6. **Push files** - 自動提交更新到 GitHub Pages

## 🐛 故障排除

### Q: 點擊按鈕后沒有任何反應
**A**: 
- 檢查瀏覽器控制台（F12 → Console）中是否有錯誤信息
- 確認已在 GitHub Secrets 中添加 `GITHUB_TOKEN_CONFIG`
- 刷新頁面重試

### Q: 顯示 "Token 無效或已過期"
**A**:
- 更新 GitHub Secrets 中的 token
- 清除瀏覽器 localStorage：
  ```javascript
  localStorage.removeItem('github_token');
  ```
- 刷新頁面重試

### Q: 工作流未執行
**A**:
- 訪問 GitHub Actions 頁面查看工作流狀態
- 檢查是否有錯誤日誌
- 確認工作流文件（.github/workflows/daily-report-update.yml）已推送到 main 分支

### Q: github-config.json 未生成
**A**:
- 工作流需要在工作流運行一次後生成配置文件
- 可手動觸發工作流：
  - 訪問 GitHub Actions 頁面
  - 選擇 "Daily Financial Report Update"
  - 點擊「Run workflow」

## 📚 相關文件

- `index_v6_ai.html` - 財金早報頁面，包含自動 token 讀取邏輯
- `.github/workflows/daily-report-update.yml` - GitHub Actions 工作流配置
- `github-config.json` - 自動生成的配置文件（包含 token）
- `daily-report.json` - 每日財務報告數據

## ✅ 驗證設置是否成功

1. **第一步**：確認 Secrets 已添加
   - 訪問 GitHub Secrets 管理頁面
   - 應顯示 `GITHUB_TOKEN_CONFIG`（值隱藏）

2. **第二步**：工作流運行
   - 訪問 GitHub Actions 頁面
   - 應看到最近的工作流運行

3. **第三步**：檢查文件
   - 訪問 GitHub repo 中的 `github-config.json`
   - 應包含 token 和 `generatedAt` 時間戳

4. **第四步**：頁面測試
   - 訪問財金早報頁面
   - 點擊「更新數據」按鈕
   - 應顯示「✅ 已觸發更新！」

---

**配置完成！**✨ 

現在你可以通過財金早報頁面一鍵更新所有市場數據，完全無需手動管理 GitHub token。
