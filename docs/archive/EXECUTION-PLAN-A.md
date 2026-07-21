# 方案 A：外網環境執行計劃

## 📋 概述

在**有外網連接**的環境中自動獲取 FinMind 真實台股數據，然後推送到 GitHub。

---

## ✅ 前置準備（當前環境已完成）

- ✅ `finmind-data-fetcher.py` - 數據獲取腳本
- ✅ `import-finmind-data.py` - 數據導入腳本
- ✅ `FINMIND-API-GUIDE.md` - 完整使用文檔
- ✅ `index.html` - 系統文件（待更新）
- ✅ GitHub 倉庫設置完成

---

## 🚀 執行步驟

### 在**有外網連接**的環境中執行以下命令：

#### 步驟 1：進入項目目錄

```bash
cd /path/to/Claude-workspace
```

#### 步驟 2：安裝依賴

```bash
pip install requests
```

#### 步驟 3：獲取 FinMind 真實數據

```bash
python3 finmind-data-fetcher.py
```

**預期輸出：**
```
============================================================
FinMind API 台股財務數據獲取工具
============================================================

將查詢 31 支股票的財務數據（2021-2025）

[1/31] 2330 台積電... ✅ 成功
[2/31] 2207 和泰車... ✅ 成功
[3/31] 2454 聯發科... ✅ 成功
...
完成！成功: 31, 失敗: 0
✅ 數據已保存至 finmind-real-data.json
```

**耗時：** 2-5 分鐘（取決於網絡速度）

#### 步驟 4：導入到系統

```bash
python3 import-finmind-data.py
```

**預期輸出：**
```
從 FinMind 數據導入到 FINANCIAL_DB

✅ 已讀取 FinMind 數據：31 支股票

導入進度：

2330: ✅ 新增股票
   └─ 年份：2021 → 2022 → 2023 → 2024 → 2025
2207: 🔄 更新現有股票
   └─ 年份：2021 → 2022 → 2023 → 2024 → 2025
...
導入完成：新增 X 支，更新 Y 支
✅ 已保存到 index.html
```

#### 步驟 5：驗證數據

```bash
# 檢查是否有新的 finmind-real-data.json 文件
ls -lh finmind-real-data.json

# 查看 HTML 文件大小是否增加
ls -lh index.html
```

#### 步驟 6：提交到 GitHub

```bash
# 查看變更
git status

# 添加變更
git add index.html finmind-real-data.json

# 提交
git commit -m "feat: 集成 FinMind 真實台股財務數據 - 31 支股票完整 5 年數據"

# 推送
git push origin main
```

---

## 📊 預期結果

執行完成後，系統將：

1. **新增 31 支常交易股票**的真實財務數據
2. **覆蓋 5 年時間段**（2021-2025）
3. **包含 5 個關鍵指標**：
   - EPS（每股收益）
   - ROE（股東權益報酬率）
   - 淨利率
   - 營業利率
   - 負債比

4. **自動排序年份**（2021→2025 升序）
5. **生成 finmind-real-data.json**（備份檔案）
6. **更新 FINANCIAL_DB**（主系統）

---

## 🔍 驗證成功

執行後在網站上驗證：

### 1. 清除快取
```
Ctrl + Shift + R
```

### 2. 搜尋任意股票
訪問：https://neferyang.github.io/stock-tool/

搜尋以下任意一支股票：

| 股票代號 | 公司名 | 應見數據 |
|---------|--------|--------|
| 2330 | 台積電 | EPS 13.05→24.05, ROE 45.2%→58.1% |
| 2207 | 和泰車 | 真實財務數據 |
| 2454 | 聯發科 | 完整 5 年趨勢 |
| 2603 | 長榮 | ROE 15.2%→45.5% |
| 1101 | 台泥 | 完整歷年指標 |

### 3. 檢查診斷卡
✅ 應顯示真實的財務指標（不是 0.0%）
✅ 5 年趨勢圖應顯示完整數據
✅ 年份順序應為 2021→2025

---

## ⚙️ 故障排除

### 問題 1：連接超時

**症狀：** `HTTPSConnectionPool ... Max retries exceeded`

**解決：**
```bash
# 重試（FinMind 可能暫時無法訪問）
python3 finmind-data-fetcher.py

# 或檢查網絡
ping api.finmind.com.tw
```

### 問題 2：某些股票無數據

**症狀：** 查詢失敗，某股票為 ⚠️

**解決：** FinMind 可能沒有該股票的完整歷史，腳本會自動跳過，只導入可用數據

### 問題 3：導入後數據不顯示

**症狀：** 網站上仍顯示舊數據

**解決：**
```bash
# 清除 GitHub 快取
CTRL + SHIFT + R（Chrome）
CTRL + F5（Firefox）
⌘ + SHIFT + R（Safari）
```

---

## 🔄 後續更新

### 一次性更新
重複執行步驟 3-6 即可更新所有數據

### 自動化更新（可選）
在 GitHub Actions 中配置週期性執行：

1. 創建 `.github/workflows/update-finmind.yml`
2. 配置每週更新
3. 自動推送更新

詳見 `FINMIND-API-GUIDE.md` 中的「GitHub Actions」章節

---

## 📞 支持

如遇問題，檢查：
1. ✅ 網絡連接是否正常
2. ✅ Python 3.7+ 已安裝
3. ✅ `pip install requests` 已執行
4. ✅ 在正確的目錄中執行

---

## 📈 系統升級路線圖

```
Phase 1（已完成）
  15 支真實 MOPS 數據 ✅
  
Phase 2（方案 A）
  + 31 支 FinMind 真實數據 ⏳
  = 46 支股票完整真實數據
  
Phase 3（未來可選）
  + 自動化週期更新 📅
  + GitHub Actions 集成 🤖
  = 永遠保持最新數據
```

---

**準備好在有外網的環境中執行？**

確保：
1. ✅ 網絡能訪問 api.finmind.com.tw
2. ✅ Python 3.7+ 已安裝
3. ✅ 已在項目目錄中
4. ✅ GitHub 帳號已配置

**然後執行上述步驟 1-6！** 🚀
