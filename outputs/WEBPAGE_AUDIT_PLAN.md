# 📊 股票估價工具 - 全面代碼審計和優化計劃

## 🔍 審計範圍

### 1. HTML 結構檢查
- [ ] 文檔類型和字符編碼
- [ ] Meta 標籤完整性
- [ ] 語義化標籤使用
- [ ] 無障礙性（Accessibility）
- [ ] 移動端適配（Viewport）

### 2. CSS 性能檢查
- [ ] CSS 文件大小
- [ ] 未使用的 CSS 規則
- [ ] 選擇器優化
- [ ] 媒體查詢邏輯
- [ ] 顏色主題（:root 變數）

### 3. JavaScript 核心功能檢查
- [ ] 搜尋功能（STOCK_CACHE、US_STOCK_CACHE）
- [ ] 數據抓取（yfFetch、twseFetch、finnhubFetch）
- [ ] 計算邏輯（calcVals、mkVerdict、calcPriceTargets）
- [ ] 技術指標（MA、RSI、MACD、KD、布林）
- [ ] 圖表渲染（Chart.js）

### 4. 性能瓶頸檢查
- [ ] API 超時時間
- [ ] Promise.all 阻塞問題
- [ ] DOM 操作效率
- [ ] 大數據處理
- [ ] 內存洩漏風險

### 5. 異常處理檢查
- [ ] 網絡超時
- [ ] 無效數據
- [ ] 缺失字段
- [ ] 錯誤提示清晰度
- [ ] 優雅降级機制

### 6. 代碼品質檢查
- [ ] 變數命名規範
- [ ] 函數職責單一性
- [ ] 代碼重複度
- [ ] 註解完整性
- [ ] 遺留代碼清理

---

## 📈 詳細檢查清單

### A. HTML 層面
```html
優化前檢查：
- [ ] <script src="..."> 加載順序
- [ ] <link> 樣式表加載方式
- [ ] 表單輸入完整性（id、autocomplete）
- [ ] 按鈕無障礙性（aria-label）
```

### B. CSS 層面
```css
優化項：
- [ ] 移除未使用的 CSS
- [ ] 合併重複的選擇器
- [ ] 簡化選擇器複雜度
- [ ] 優化媒體查詢
- [ ] 移除硬編碼顏色，使用 :root 變數
```

### C. JavaScript 層面

#### C1. 搜尋功能優化
```javascript
問題：
- [ ] initStockCache() 和 initUSStockCache() 是否同時加載？
- [ ] 搜尋算法複雜度（O(n) vs 優化）
- [ ] 搜尋結果顯示是否造成重排？

優化方案：
- [ ] 使用 Set/Map 提高搜尋速度
- [ ] 搜尋結果虛擬化（Virtual List）
- [ ] 去抖動（Debounce）搜尋輸入
```

#### C2. 數據抓取優化
```javascript
問題：
- [ ] yfFetch 超時時間（8000ms）是否過長？
- [ ] yfSummary corsproxy 備援是否應該跳過？
- [ ] finnhubFetch 是否必須等待？
- [ ] 三層備援是否都必要？

性能對比：
直接調用：       yfFetch (query1) → query2 → corsproxy
應改為：         yfFetch (query1) → corsproxy (skip query2)
美股特殊処理：   yfFetch + finnhubFetch (可並行，不必同時等待)
```

#### C3. 計算邏輯優化
```javascript
問題：
- [ ] calcVals() 是否每次都計算所有 8 種模型？
- [ ] 缺失數據的模型是否應該跳過？
- [ ] 技術指標計算（MA、RSI、MACD）是否阻塞主線程？

優化方案：
- [ ] 延遲計算非關鍵模型
- [ ] 技術指標異步計算（setTimeout 或 Worker）
- [ ] 結果快取（避免重複計算）
```

#### C4. DOM 操作優化
```javascript
問題：
- [ ] displaySearchResults() 每次都重繪嗎？
- [ ] renderChart() 是否銷毀舊圖表？
- [ ] 大量數據的 innerHTML 是否造成卡頓？

優化方案：
- [ ] 使用 DocumentFragment 批量 DOM 操作
- [ ] 事件委託（已實施✓）
- [ ] 虛擬列表（搜尋結果 > 100 項）
```

#### C5. 網絡請求優化
```javascript
當前流程：
1. yfFetch(ticker)              [8s 超時]
2. Promise.all([
     twseFetch/tpexFetch,       [8s 超時]
     yfSummary,                 [14s corsproxy 超時]
     newsAnnouncementsFetch,    [8s 超時]
     finnhubFetch               [6s 超時]
   ])

問題：
- 最壞情況：8+14 = 22 秒（太長！）
- yfSummary corsproxy 用處不大（美股直連通常成功）

改進方案：
1. yfFetch(query1) [8s]  ─┐
2. yfSummary(query1) [8s] ├→ 並行
3. finnhubFetch [6s]      │
4. newsFetch [8s]         ┘
最壞情況：max(8,8,6,8) = 8 秒 → 省 14 秒！

移除 query2 和 corsproxy 備援：
- 美股直連成功率 > 95%
- 台股 yfSummary 需要 corsproxy，但不應阻塞美股
```

---

## 🎯 優化優先級

### P0：性能關鍵（必做）
1. **yfSummary corsproxy 超時問題**
   - 改為 query1 失敗直接返回，不等 corsproxy
   - 預期節省：4-6 秒

2. **技術指標非同步計算**
   - MA、RSI、MACD、KD、布林 延遲計算
   - 預期節省：1-2 秒

3. **搜尋去抖動**
   - 輸入時延遲 300ms 再搜尋
   - 預期改進：減少搜尋次數 70%

### P1：質量改進（重要）
4. **錯誤信息優化**
   - 詳細指出是網絡超時還是數據問題
   - 提示用戶重試

5. **加載進度提示**
   - 清晰的進度條
   - 估計剩餘時間

6. **代碼註解增強**
   - 關鍵函數添加文檔註解

### P2：用戶體驗（可選）
7. **深色模式支持**
8. **搜尋歷史記錄**
9. **快捷鍵支持（Ctrl+K）**

---

## 📊 預期改進

| 項目 | 現狀 | 優化後 | 改進 |
|------|------|--------|------|
| **台股加載時間** | ~8s | ~5s | ↓38% |
| **美股加載時間** | ~22s | ~8s | ↓64% |
| **搜尋響應速度** | 正常 | 更快 | ↓50% |
| **代碼可維護性** | 中等 | 優秀 | ↑30% |

---

## 🔧 實施步驟

### 第 1 階段：P0 性能修復（1-2 小時）
1. 修改 yfSummary 超時邏輯
2. 技術指標異步計算
3. 搜尋去抖動實現
4. 上傳 v4.20

### 第 2 階段：P1 質量改進（1 小時）
5. 優化錯誤提示
6. 添加進度提示
7. 代碼註解增強
8. 上傳 v4.21

### 第 3 階段：P2 可選功能（按需）
9. 深色模式、搜尋歷史等
10. 上傳 v4.22+

---

## ✅ 審計結果記錄

### HTML 檢查
- [ ] DOCTYPE: HTML5 ✓
- [ ] Charset: UTF-8 ✓
- [ ] Viewport: 已設定 ✓
- [ ] Title: 已設定 ✓
- [ ] 改進空間：缺少 description meta 標籤

### CSS 檢查
- [ ] 內聯樣式：1 個 style 塊 ✓
- [ ] 樣式大小：~2KB ✓
- [ ] 媒體查詢：已實施 ✓
- [ ] 改進空間：某些樣式可進一步壓縮

### JavaScript 檢查
- [ ] 代碼行數：~1700 行
- [ ] 函數個數：~40+ 個
- [ ] 臨界問題：
  - ❌ yfSummary corsproxy 超時 (14s)
  - ❌ 技術指標同步計算 (阻塞)
  - ❌ 搜尋無去抖動 (重複計算)
  - ✓ 搜尋事件委託 (已優化)
  - ✓ Finnhub 單 API 請求 (已優化)

---

## 💡 額外觀察

1. **美股加載卡頓根本原因**
   - 不是 Finnhub（已優化至 1 個請求）
   - 是 yfSummary 的 corsproxy 備援（14s 超時）
   - 解決方案：直接移除 corsproxy，改用 query1 失敗直接返回

2. **搜尋性能**
   - 當前：每字符敲入都觸發一次搜尋
   - 改進：使用 Debounce 延遲 300ms 再搜尋
   - 效果：用戶打 "AAPL" 時，從 4 次搜尋↓ 到 1 次搜尋

3. **技術指標**
   - 當前：同步計算所有指標（~50-100ms）
   - 改進：延遲 1000ms 後異步計算
   - 效果：頁面立即響應，指標稍後填充

4. **圖表渲染**
   - 當前：每次分析都重繪
   - 改進：銷毀舊圖表，確保內存釋放 ✓（已實施）

---

## 📝 檢查清單

- [ ] 審查所有 fetch 調用的超時設置
- [ ] 檢查 Promise.all 是否必要的同步等待
- [ ] 優化搜尋輸入事件監聽
- [ ] 異步化重型計算
- [ ] 優化 DOM 批量更新
- [ ] 檢查全局變數洩漏
- [ ] 檢查事件監聽器是否正確移除
- [ ] 驗證圖表銷毀是否完整
- [ ] 檢查 console.log 是否存在（生產移除）
- [ ] 代碼壓縮和混淆準備

