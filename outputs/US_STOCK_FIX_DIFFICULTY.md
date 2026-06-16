# 美股數據修正難度評估

**評估日期**：2026-06-04  
**版本**：v4.13  
**評估類型**：技術可行性 + 工作量 + 優先級

---

## 📊 改進方案評估表

### 整體難度排序

| 優先級 | 方案 | 難度 | 工作量 | 收益 | 推薦 |
|--------|------|------|--------|------|------|
| **P1** | **添加美股提示說明** | ⭐ | 15分鐘 | ⭐⭐⭐ | ✅ 立即做 |
| **P2** | **增強英文 Sector 匹配** | ⭐⭐ | 30分鐘 | ⭐⭐ | ✅ 建議做 |
| **P3** | **自動隱藏無數據功能** | ⭐⭐⭐ | 1-2小時 | ⭐⭐⭐⭐ | △ 可做可不做 |
| **P4** | **集成付費 API** | ⭐⭐⭐⭐ | 4-8小時 | ⭐⭐⭐⭐⭐ | ❌ 暫不做 |
| **P5** | **爬取券商數據** | ⭐⭐⭐⭐⭐ | 8小時+ | ⭐⭐⭐⭐ | ❌ 不推薦 |

---

## 🔧 方案詳細分析

### P1：添加美股提示說明 ⭐ 簡單

**難度級別**：最簡單  
**工作量**：15-20分鐘  
**技術風險**：零

#### 實現方案

**位置**：應用程式 UI 中，基本面數據區域

```javascript
// 修改位置：基本面顯示邏輯（第 ~1200 行）

// 檢測是否為美股且無基本數據
const isUSStock = !ticker.endsWith('.TW') && !ticker.endsWith('.TWO');
const hasFinancialData = m.pe || m.eps || m.pb;

if (isUSStock && !hasFinancialData) {
  // 顯示提示信息
  showWarning(`
    ⚠️ 美股數據限制
    Yahoo Finance 免費 API 無法提供 P/E、EPS 等基本面數據。
    當前僅支持技術面分析（K線走勢、均線、成交量）。
  `);
}
```

**修改工作**：
- [ ] 添加 US stock 偵測邏輯（1 行代碼）
- [ ] 添加警告提示框 HTML（10 行代碼）
- [ ] 添加 CSS 樣式（5 行代碼）

**測試工作**：
- [ ] 查詢美股 AAPL → 顯示提示 ✓
- [ ] 查詢台股 2330 → 無提示 ✓
- [ ] 提示框樣式正確 ✓

**風險**：無

#### 代碼示例

```html
<!-- 在「基本面數據」區域添加 -->
<div id="us-warning" class="warning hidden">
  <div class="warn-icon">⚠️</div>
  <div class="warn-text">
    <strong>美股數據限制</strong><br>
    Yahoo Finance 免費 API 無法提供 P/E、EPS 等估值數據。
    當前支持技術面分析（K線走勢、均線、成交量）。<br>
    <a href="#" onclick="showUSStockGuide()">更多說明 →</a>
  </div>
</div>

<script>
function showUSStockGuide() {
  // 顯示說明對話框或導向幫助文檔
  alert(`
美股查詢指南：
- 股價走勢：可用 ✓
- 技術指標：可用 ✓
- 基本面數據：不可用 ✗
- 估值計算：不可用 ✗

建議參考：
1. Yahoo Finance 網頁版
2. 美股券商平台（TD、IB）
3. SEC Edgar
  `);
}
</script>
```

**優點**：
- ✅ 簡單快速
- ✅ 無技術風險
- ✅ 用戶體驗大幅提升
- ✅ 立即可做

**缺點**：
- ❌ 不能真正解決數據缺失問題

---

### P2：增強英文 Sector 匹配 ⭐⭐ 簡單-中等

**難度級別**：簡單到中等  
**工作量**：30-45分鐘  
**技術風險**：低

#### 實現方案

**位置**：classifyIndustry 函數的 L3 英文匹配規則（第 ~715 行）

```javascript
// 原有規則
const enMatches = [
  ['semiconductor|chip|processor', '半導體業'],
  ['computer hardware|computer|electronic equipment|peripherals', '電腦及週邊設備業'],
  // ... 其他規則
];

// 增強後的規則（新增）
const enMatches = [
  // ... 原有規則保持
  
  // 新增：針對常見美股
  ['consumer electronics|computer peripherals|computer hardware', '電腦及週邊設備業'],  // Apple
  ['semiconductor equipment|semiconductor|integrated circuits', '半導體業'],  // Intel
  ['software|internet software|software services', '數位雲端'],  // Microsoft
  ['financial services|bank|insurance', '金融保險業'],  // JPMorgan
  ['retail|consumer staples|food', '貿易百貨業'],  // Walmart, Costco
  ['health care|pharmaceutical|medical', '生技醫療業'],  // Pfizer, J&J
  ['energy|oil|gas|utilities', '油電燃氣業'],  // Exxon, NextEra
  ['industrial|machinery|equipment manufacturing', '電機機械'],  // 3M, CAT
];
```

**修改工作**：
- [ ] 補充 15-20 條英文匹配規則（30 行代碼）
- [ ] 測試每條規則（30分鐘）

**測試工作**：
- [ ] AAPL（Apple）→ 電腦及週邊設備業 ✓
- [ ] MSFT（Microsoft）→ 數位雲端 ✓
- [ ] INTC（Intel）→ 半導體業 ✓
- [ ] JNJ（Johnson & Johnson）→ 生技醫療業 ✓
- [ ] WMT（Walmart）→ 貿易百貨業 ✓

**效果**：
- 美股產業分類從「未分類」改善至正確分類
- 但仍無法計算估值（因為缺少 P/E 等數據）

**優點**：
- ✅ 簡單易實現
- ✅ 改善產業分類準確度
- ✅ 可立即做
- ✅ 低風險

**缺點**：
- ❌ 無法解決基本面數據缺失
- ❌ 英文規則維護成本（新美股常出現）

---

### P3：自動隱藏無數據功能 ⭐⭐⭐ 中等

**難度級別**：中等  
**工作量**：1-2 小時  
**技術風險**：中等

#### 實現方案

**邏輯**：
```javascript
// 檢測美股是否有基本面數據
const isUSStock = !ticker.endsWith('.TW') && !ticker.endsWith('.TWO');
const hasMissingData = isUSStock && (!m.pe && !m.eps && !m.pb);

if (hasMissingData) {
  // 隱藏估值模型試算區域
  document.getElementById('valuation-models').classList.add('hidden');
  
  // 隱藏買賣建議區域
  document.getElementById('price-targets').classList.add('hidden');
  
  // 顯示「技術面分析」提示
  showTechAnalysisOnly();
}
```

**修改工作**：
- [ ] 添加數據檢測邏輯（10 行代碼）
- [ ] 修改 HTML 結構添加 ID（5 處位置）
- [ ] 添加 CSS 隱藏規則（3 行代碼）
- [ ] 添加提示顯示邏輯（15 行代碼）

**涉及的 HTML 區域**：
```html
<!-- 需要添加 id 以便隱藏 -->
<div id="valuation-models">估值模型試算</div>
<div id="price-targets">買賣建議</div>
<div id="tech-analysis">技術面分析</div>
```

**測試工作**：
- [ ] AAPL 查詢 → 隱藏估值模型、展示技術面 ✓
- [ ] 2330 查詢 → 正常顯示全部功能 ✓
- [ ] SPY ETF → 正確分類、顯示相應內容 ✓

**風險**：
- 中等：涉及多個 UI 區域的修改，需要仔細測試
- 可能出現未預期的隱藏或顯示問題

**優點**：
- ✅ 改善用戶體驗（減少「資料不足」提示）
- ✅ 界面更清晰
- ✅ 邏輯清晰，易於維護

**缺點**：
- ❌ 仍無法解決數據缺失本質問題
- ❌ 修改多個 UI 區域，風險相對較高
- ❌ 需要仔細測試各種情況

---

### P4：集成付費 API（IEX Cloud）⭐⭐⭐⭐ 困難

**難度級別**：困難  
**工作量**：4-8 小時  
**技術風險**：高

#### 實現方案

**第三方 API 選項**：

| API | 費用 | 美股支持 | 難度 | 推薦度 |
|-----|------|---------|------|--------|
| **IEX Cloud** | $9-99/月 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ |
| Alpha Vantage | 免費/付費 | ⭐⭐⭐⭐ | ⭐⭐⭐ | △ |
| Polygon.io | $29/月 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | △ |
| Finnhub | 免費限制 | ⭐⭐⭐ | ⭐⭐ | △ |

**IEX Cloud 方案示例**：
```javascript
async function getUSStockData(symbol) {
  const apiKey = 'YOUR_IEX_CLOUD_KEY';
  const url = `https://cloud.iexapis.com/stable/stock/${symbol}/quote?token=${apiKey}`;
  
  try {
    const r = await fetch(url);
    if (r.ok) {
      const data = await r.json();
      return {
        pe: data.peRatio,
        eps: data.ttmEPS,
        pb: data.priceBook,
        div: data.dividendRate,
        divYield: data.dividendYield,
        // ... 更多數據
      };
    }
  } catch(e) {
    console.error('IEX API failed:', e);
    return null;  // 回退到 Yahoo Finance
  }
}
```

**修改工作**：
- [ ] 申請 IEX Cloud 賬戶（5分鐘，需信用卡）
- [ ] 添加新的數據獲取函數（50 行代碼）
- [ ] 修改數據整合邏輯，優先使用 IEX（20 行代碼）
- [ ] 添加回退邏輯（處理 API 失敗）（15 行代碼）
- [ ] 添加 API key 管理機制（10 行代碼）

**涉及的修改**：
1. **go() 函數中的並行請求**
   ```javascript
   // 原有
   const [twseArr, tpexArr, summaryResult, newsResult] = await Promise.all([...]);
   
   // 新增
   const [twseArr, tpexArr, summaryResult, newsResult, usStockData] = await Promise.all([
     // ...
     isUSStock ? getUSStockDataFromIEX(ticker) : Promise.resolve(null)
   ]);
   ```

2. **數據整合邏輯**
   ```javascript
   // IEX 數據優先，回退到 Yahoo Finance
   if (usStockData) {
     m.pe = usStockData.pe || m.pe;
     m.eps = usStockData.eps || m.eps;
     m.pb = usStockData.pb || m.pb;
     // ...
   }
   ```

**測試工作**：
- [ ] AAPL 查詢 → 成功獲取 P/E、EPS ✓
- [ ] MSFT 查詢 → 數據準確性驗證 ✓
- [ ] API 超時 → 正確回退到 Yahoo ✓
- [ ] 估值計算 → 基於 IEX 數據計算 ✓
- [ ] 台股查詢 → 不受影響，仍用 TWSE ✓

**成本考慮**：
- **IEX Cloud Starter 計畫**：$9/月（100 次/月）
  - 不夠日常使用
  - 適合小規模應用測試

- **IEX Cloud 成長計畫**：$30/月（300,000 次/月）
  - 足夠個人或中小應用
  - 推薦方案

- **企業計畫**：$99+/月
  - 適合商用應用

**風險**：
- 高：涉及外部 API 依賴，需要 API key 管理
- 需要處理 API 超時、配額限制、價格變動
- 跨域請求可能存在 CORS 問題
- 需要後端代理（安全考慮，不能在前端暴露 API key）

**優點**：
- ✅ 完全解決美股數據缺失問題
- ✅ 提供完整的估值計算功能
- ✅ 數據質量高、更新及時

**缺點**：
- ❌ 需要付費（$9-30/月）
- ❌ 需要後端支持（API key 保護）
- ❌ 複雜度高
- ❌ 額外的運維成本

---

### P5：爬取券商/SEC 數據 ⭐⭐⭐⭐⭐ 最困難

**難度級別**：最困難  
**工作量**：8+ 小時  
**技術風險**：極高

#### 為什麼不推薦？

```
❌ 法律風險高
  - 違反服務條款
  - 可能面臨法律訴訟

❌ 技術難度大
  - 需要處理反爬蟲機制
  - 需要瀏覽器自動化（Selenium、Puppeteer）
  - 維護成本高

❌ 不穩定
  - 網站結構變化導致爬蟲失效
  - 需要長期維護

❌ 倫理問題
  - 違反網站 robots.txt
  - 浪費服務器資源
  - 可能被 IP 封禁
```

**結論**：❌ 不推薦實現

---

## 📈 優先級建議

### 立即實施（v4.14）⏰ 30分鐘

```
P1：添加美股提示說明 ⭐
  工作量：15分鐘
  收益：⭐⭐⭐ 用戶體驗大幅改善
  
P2：增強英文 Sector 匹配 ⭐⭐
  工作量：15分鐘
  收益：⭐⭐ 產業分類更準確
```

**建議步驟**：
1. 添加美股警告提示框（P1）
2. 補充英文 Sector 規則（P2）
3. 更新版本到 v4.14
4. 測試驗證（10分鐘）

---

### 可選實施（v4.15 或未來）

```
P3：自動隱藏無數據功能 ⭐⭐⭐
  工作量：1-2小時
  收益：⭐⭐⭐⭐ 界面更清晰，用戶體驗更好
  風險：中等
```

**評估時機**：
- 當 P1、P2 完成後，根據用戶反饋再決定
- 如果用戶對「資料不足」提示反饋較多，優先做

---

### 不推薦實施

```
P4：集成付費 API ⭐⭐⭐⭐
  - 成本高（$9-30/月）
  - 複雜度高（需後端支持）
  - 維護成本高
  
  建議時機：
  ✓ 應用變成商用產品
  ✓ 用戶明確要求完整美股支持
  ✓ 有預算和技術人力支持

P5：爬取公開數據 ⭐⭐⭐⭐⭐
  - 法律風險高
  - 技術風險高
  - 不穩定
  ❌ 完全不推薦
```

---

## 🎯 成本-收益分析

### P1 vs P2 vs P3 比較

```
P1：添加提示說明
├─ 成本：15 分鐘 + 維護成本極低
├─ 收益：用戶知道為什麼無法獲取數據，滿意度提升
├─ 風險：無
└─ CP值：⭐⭐⭐⭐⭐ 最高

P2：增強 Sector 匹配
├─ 成本：30 分鐘 + 定期維護（新股票出現時）
├─ 收益：產業分類更準確，間接改善用戶體驗
├─ 風險：低（只是匹配規則，不影響其他功能）
└─ CP值：⭐⭐⭐⭐ 很高

P3：自動隱藏功能
├─ 成本：1-2 小時 + 長期維護
├─ 收益：界面更清晰，減少「資料不足」視覺污染
├─ 風險：中等（涉及 UI 修改）
└─ CP值：⭐⭐⭐ 中等

P4：集成付費 API
├─ 成本：4-8 小時開發 + $10-30/月 + 長期維護
├─ 收益：完全解決美股數據問題
├─ 風險：高（API 依賴、成本、複雜度）
└─ CP值：⭐ 低（除非商用）
```

---

## ✅ 最終建議

### 推薦方案：P1 + P2（v4.14）

**理由**：
- ✅ 工作量小（30分鐘）
- ✅ 改善明顯（用戶體驗提升）
- ✅ 風險低（基本無風險）
- ✅ 成本零（無付費成本）
- ✅ 立即可做

**預期效果**：
```
修正前：
  AAPL 查詢
  → 產業：未分類 (low)
  → 基本面：全 N/A
  → 估值：資料不足

修正後（P1+P2）：
  AAPL 查詢
  → 產業：電腦及週邊設備業 (high) ✓
  → 基本面：全 N/A（但有清晰提示說明）
  → 估值：美股數據限制提示 + 技術面分析可用 ✓
```

### 可選方案：添加 P3（v4.15）

**條件**：
- 當 v4.14 上線後，收集用戶反饋
- 如果多數用戶反映「資料不足」視覺污染，再做 P3
- 工作量可控（1-2小時），風險可管理

---

**評估完成**  
**推薦立即實施**：P1 + P2（v4.14）  
**預計時間**：30 分鐘  
**優先級**：高

