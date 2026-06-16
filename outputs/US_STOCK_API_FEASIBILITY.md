# 美股基本面 API 集成可行性評估

**評估日期**：2026-06-04  
**目標**：使用免費 API 取得美股 P/E、EPS 等基本面數據

---

## 📊 免費 API 詳細對比

### 1️⃣ Alpha Vantage ⭐⭐⭐

**官網**：https://www.alphavantage.co/  
**申請**：需要免費 API Key

**優點**：
- ✅ 提供美股基本面數據（P/E、EPS、ROE 等）
- ✅ 支持 K線數據
- ✅ 文檔完整
- ✅ 無需付費即可使用

**缺點**：
- ❌ 配額限制：5 requests/minute（免費版）
- ❌ 對於高頻查詢不友好
- ❌ 美股數據不如 Yahoo Finance 完整

**API 示例**：
```
GET https://www.alphavantage.co/query?function=OVERVIEW&symbol=AAPL&apikey=YOUR_KEY

返回：
{
  "Symbol": "AAPL",
  "PERatio": "28.5",
  "EPS": "6.05",
  "BookValue": "3.82",
  "PriceToBookRatio": "187.5",
  "DividendYield": "0.0046"
}
```

**難度**：⭐⭐ 簡單-中等  
**工作量**：1-2 小時  
**實現風險**：低

---

### 2️⃣ Finnhub ⭐⭐⭐⭐

**官網**：https://finnhub.io/  
**申請**：需要免費 API Key

**優點**：
- ✅ 數據完整（P/E、EPS、ROE、PB 等）
- ✅ 配額較高：60 requests/minute（免費版）
- ✅ 響應速度快
- ✅ 文檔詳細
- ✅ 還提供新聞、公司新聞等

**缺點**：
- ❌ 某些高級功能需要付費
- ❌ 免費版功能受限

**API 示例**：
```
GET https://finnhub.io/api/v1/stock/profile2?symbol=AAPL&token=YOUR_KEY

返回：
{
  "name": "Apple Inc",
  "exchange": "NASDAQ",
  "marketCapitalization": 3070000,
  "country": "US",
  "currency": "USD"
}

獲取估值數據：
GET https://finnhub.io/api/v1/stock/valuation?symbol=AAPL&token=YOUR_KEY
```

**難度**：⭐⭐ 簡單-中等  
**工作量**：1.5-2 小時  
**實現風險**：低

---

### 3️⃣ IEX Cloud ⭐⭐⭐⭐⭐

**官網**：https://iexcloud.io/  
**申請**：需要信用卡（但有免費試用）

**優點**：
- ✅ 數據質量最高
- ✅ 完整的美股基本面數據
- ✅ 高配額（免費試用）
- ✅ 支持實時數據
- ✅ 文檔最完整

**缺點**：
- ❌ **需要付費**（$9/月 起）
- ❌ 試用期後自動計費

**API 示例**：
```
GET https://cloud.iexapis.com/stable/stock/AAPL/quote?token=YOUR_KEY

返回：
{
  "symbol": "AAPL",
  "peRatio": 28.5,
  "ttmEPS": 6.05,
  "bookValue": 3.82,
  "priceToBook": 187.5,
  "lastTrade": 310.26
}
```

**難度**：⭐⭐ 簡單-中等  
**工作量**：1.5-2 小時  
**實現風險**：低  
**成本**：$9-30/月

---

### 4️⃣ Polygon.io ⭐⭐⭐

**官網**：https://polygon.io/  
**申請**：需要免費註冊

**優點**：
- ✅ 提供美股基本面和K線數據
- ✅ 文檔詳細

**缺點**：
- ❌ 免費版功能受限
- ❌ 高級功能需要付費

**難度**：⭐⭐⭐ 中等  
**工作量**：2-3 小時  
**實現風險**：中等

---

## 🎯 推薦方案評估

### 方案 A：使用 Finnhub（推薦）⭐⭐⭐⭐⭐

**理由**：
1. ✅ 完全免費（無需信用卡）
2. ✅ 配額充足（60 req/min）
3. ✅ 數據完整
4. ✅ 實現簡單（1.5-2 小時）
5. ✅ 風險低

**實現步驟**：
```javascript
// 1. 申請免費 API Key（2分鐘）
// 2. 添加 Finnhub Fetch 函數（30分鐘）
async function finnhubFetch(symbol) {
  const apiKey = 'YOUR_FINNHUB_KEY';
  const url = `https://finnhub.io/api/v1/stock/profile2?symbol=${symbol}&token=${apiKey}`;
  
  try {
    const r = await fetch(url);
    if (r.ok) return await r.json();
  } catch(e) {}
  return null;
}

// 3. 集成到數據流程中（30分鐘）
// 4. 測試驗證（30分鐘）
```

**成本**：$0  
**工作量**：2 小時  
**預期效果**：AAPL 顯示 P/E、EPS 等數據

---

### 方案 B：使用 Alpha Vantage

**理由**：
- ✅ 完全免費
- ✅ 文檔完整
- ⚠️ 配額低（5 req/min）

**缺點**：
- 高頻查詢時可能超配額
- 用戶密集使用可能觸發限制

**難度**：⭐⭐  
**工作量**：1.5 小時  
**成本**：$0  
**推薦度**：△（如果用戶量小可用）

---

### 方案 C：使用 IEX Cloud（最佳體驗）

**理由**：
- ✅ 數據質量最高
- ✅ 配額最充足
- ✅ 官方支持

**缺點**：
- ❌ 需要付費（$9/月）

**難度**：⭐⭐  
**工作量**：1.5-2 小時  
**成本**：$9-30/月  
**推薦度**：⭐⭐⭐⭐（如果商用或用戶多）

---

## 💡 集成架構設計

### 三層 API 策略

```javascript
// 優先級順序：Finnhub → Alpha Vantage → Yahoo Finance（備援）

async function getUSStockData(symbol) {
  // Layer 1：嘗試 Finnhub（最佳數據源）
  let data = await finnhubFetch(symbol);
  if (data) return {source: 'Finnhub', ...data};
  
  // Layer 2：回退到 Alpha Vantage
  data = await alphaVantageFetch(symbol);
  if (data) return {source: 'AlphaVantage', ...data};
  
  // Layer 3：回退到 Yahoo Finance（無基本面數據但有 K線）
  data = await yahooFinanceFetch(symbol);
  if (data) return {source: 'YahooFinance', ...data, note: '無基本面數據'};
  
  // 所有都失敗
  return null;
}
```

**優點**：
- ✅ 自動選擇最優數據源
- ✅ 失敗自動回退
- ✅ 用戶無感知

---

## ✅ 實施計畫（如果選擇 Finnhub）

### Phase 1：準備（5分鐘）
```
1. 訪問 https://finnhub.io/
2. 註冊免費賬戶
3. 獲取 API Key
```

### Phase 2：開發（2小時）
```
【時間分配】
- 添加 Finnhub Fetch 函數        (30分鐘)
- 集成到 go() 函數                (30分鐘)
- 解析數據並映射到 m 對象          (30分鐘)
- 測試和調試                      (30分鐘)
```

### Phase 3：部署
```
- 替換 API Key
- 測試 AAPL、MSFT、GOOGL 等
- 驗證數據準確性
```

---

## 📊 成本-收益分析

| 方案 | 成本 | 工作量 | 數據質量 | 配額 | 推薦度 |
|------|------|--------|---------|------|--------|
| **Finnhub** | $0 | 2h | ⭐⭐⭐⭐ | 充足 | ⭐⭐⭐⭐⭐ |
| Alpha Vantage | $0 | 1.5h | ⭐⭐⭐ | 有限 | ⭐⭐⭐ |
| IEX Cloud | $9/月 | 2h | ⭐⭐⭐⭐⭐ | 充足 | ⭐⭐⭐⭐ |
| 現狀 Yahoo | $0 | 0h | ⭐ | 無限 | ⭐ |

---

## 🎯 最終建議

### 如果選擇 Finnhub（推薦）
```
優點：
  ✅ 完全免費（無信用卡要求）
  ✅ 配額充足（60 req/min）
  ✅ 工作量合理（2 小時）
  ✅ 風險低
  ✅ 數據品質好

缺點：
  ❌ 需要管理 API Key

預期效果：
  AAPL → 顯示 P/E、EPS 等 ✓
  MSFT → 顯示完整基本面 ✓
  GOOGL → 顯示完整基本面 ✓
```

### 如果暫不修改
```
繼續使用 Yahoo Finance：
  ✅ 零成本
  ✅ 零工作量
  ✗ 美股無基本面數據
```

---

## 🚀 下一步建議

**選項 1：立即集成 Finnhub（v4.15 或 v4.16）**
```
優先級：P2（中等）
工作量：2 小時
時間：可在 v4.15 之後進行
```

**選項 2：暫時保持現狀**
```
優先級：P3（可選）
原因：美股無基本面數據是行業現象
替代：告知用戶參考其他來源
```

**選項 3：等待用戶反饋**
```
優先級：P3（暫時觀察）
原因：確認是否必要
時機：當有多個用戶要求時
```

---

**建議**：選擇 **Finnhub 方案**（完全免費 + 配額充足）

**預計時間**：2 小時（在 v4.16 實施）

