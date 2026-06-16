# 🏦 融資券 + 法人持股數據揭示系統

**版本**：v6.2（新功能開發）  
**日期**：2026-06-08  
**狀態**：📋 規劃階段

---

## 🎯 核心需求

### 1️⃣ 融資券數據面板

#### 顯示內容
```
融資餘額
├─ 金額：NT$ XXX 億
├─ 張數：XXX 張
└─ 增減：↑ +XXX 億 (+X.X%)

融券餘額
├─ 金額：NT$ XXX 萬
├─ 張數：XXX 張
└─ 增減：↓ -XXX 萬 (-X.X%)

融資券比例
├─ 融資佔流通股比例：X.X%
├─ 融券佔流通股比例：X.X%
└─ 融資/融券比：X.X

融資維持率警示
├─ 當前維持率：XXX.X%
├─ 警示線：130% (紅色警告)
└─ 危險線：120% (極端警告)
```

### 2️⃣ 法人持股變化面板

#### 顯示內容
```
法人持股統計
├─ 外資持股比例：X.X% (↑ +X.X%)
├─ 投信持股比例：X.X% (↓ -X.X%)
├─ 自營商持股比例：X.X% (→ 0.X%)
└─ 法人合計：X.X% (↑ +X.X%)

持股增減趨勢（過去 30 天折線圖）
├─ X軸：日期
├─ Y軸：持股比例 (%)
├─ 線條 1：外資
├─ 線條 2：投信
├─ 線條 3：自營商
└─ 線條 4：法人合計
```

---

## 📊 數據源規劃

### TWSE 官方 API

| 數據 | 端點 | 更新頻率 | 備註 |
|------|------|---------|------|
| 融資融券餘額 | `/v1/exchangeReport/BWIBBU_*` | 每日收盤後 | 已有備援 |
| 法人持股 | `/v1/opendata/mopsfin_*` | 每日收盤後 | 需驗證 |
| 法人買賣 | MOPS 爬蟲 | 每日 | 需開發 |

### 備援方案
```
1. AllOrigins API 代理
   https://api.allorigins.win/get?url=[TWSE_URL]

2. corsproxy.io
   https://corsproxy.io/?[TWSE_URL]

3. 本地 JSON 快取
   每日定時更新，CORS 失敗時使用
```

---

## 🏗️ 架構設計

### 新增模塊

#### Module 1: 融資券數據模塊
```javascript
const marginModule = {
  // 獲取融資融券數據
  fetchMarginData(code) => Promise<MarginData>,
  
  // 計算融資維持率
  calculateMaintenanceRatio(marginData) => number,
  
  // 生成趨勢預測
  predictTrend(historicalData) => 'up' | 'down' | 'stable',
  
  // 警示級別判定
  getAlertLevel(maintenanceRatio) => 'safe' | 'warning' | 'danger'
}

interface MarginData {
  code: string;
  date: string;
  
  // 融資
  marginBalance: number;        // 融資金額 (NT$)
  marginShares: number;         // 融資張數
  marginChange: number;         // 增減金額
  marginChangePercent: number;  // 增減百分比
  
  // 融券
  shortBalance: number;         // 融券金額 (NT$)
  shortShares: number;          // 融券張數
  shortChange: number;          // 增減金額
  shortChangePercent: number;   // 增減百分比
  
  // 比例
  marginRatio: number;          // 融資佔流通股比例 (%)
  shortRatio: number;           // 融券佔流通股比例 (%)
  marginToShortRatio: number;   // 融資/融券比
  
  // 維持率
  maintenanceRatio: number;     // 融資維持率 (%)
  maintenanceRatioChange: number; // 變化
}
```

#### Module 2: 法人持股模塊
```javascript
const legalPersonModule = {
  // 獲取法人持股數據
  fetchLegalPersonData(code) => Promise<LegalPersonData>,
  
  // 獲取歷史趨勢
  fetchHistoricalTrend(code, days = 30) => Promise<TrendData[]>,
  
  // 識別法人買賣信號
  detectSignal(currentData, previousData) => Signal,
  
  // 計算持股穩定度
  calculateStability(trendData) => number
}

interface LegalPersonData {
  code: string;
  date: string;
  
  // 各類法人持股
  foreignInvestors: {
    percentage: number;        // 持股比例 (%)
    change: number;            // 增減 (%)
    changeAmount: number;      // 增減張數
  };
  
  investmentTrusts: {
    percentage: number;
    change: number;
    changeAmount: number;
  };
  
  dealers: {                     // 自營商
    percentage: number;
    change: number;
    changeAmount: number;
  };
  
  total: {                       // 法人合計
    percentage: number;
    change: number;
    changeAmount: number;
  };
}

interface TrendData {
  date: string;
  foreignInvestors: number;
  investmentTrusts: number;
  dealers: number;
  total: number;
}

interface Signal {
  type: 'buy' | 'sell' | 'neutral';
  strength: 'strong' | 'moderate' | 'weak';
  description: string;
}
```

---

## 🎨 UI 設計

### 新增面板位置
```
基本面區塊（現有）
    ↓
技術指標區塊（現有）
    ↓
【新增】法人面板 ← 新增獨立面板
├─ 融資融券卡片
│  ├─ 融資餘額展示
│  ├─ 融券餘額展示
│  ├─ 融資維持率警示
│  └─ 融資/融券比例視覺化
│
└─ 法人持股卡片
   ├─ 四類法人持股比例表
   ├─ 持股增減箭頭指示
   └─ 30天趨勢折線圖
```

### 卡片設計範本

#### 融資融券卡片
```html
<div class="legal-panel">
  <div class="card margin-card">
    <h3>📊 融資融券</h3>
    
    <div class="metric-grid">
      <!-- 融資 -->
      <div class="metric">
        <label>融資餘額</label>
        <div class="value">NT$ 123 億</div>
        <div class="change up">↑ +5 億 (+4.3%)</div>
      </div>
      
      <!-- 融券 -->
      <div class="metric">
        <label>融券餘額</label>
        <div class="value">NT$ 45 萬</div>
        <div class="change down">↓ -2 萬 (-4.2%)</div>
      </div>
      
      <!-- 比例 -->
      <div class="metric">
        <label>融資佔比</label>
        <div class="value">2.3%</div>
        <div class="bar"><div class="fill" style="width: 2.3%"></div></div>
      </div>
      
      <!-- 維持率 -->
      <div class="metric warning">
        <label>⚠️ 融資維持率</label>
        <div class="value">145.2%</div>
        <div class="threshold">警示：130% | 危險：120%</div>
      </div>
    </div>
  </div>
</div>
```

#### 法人持股卡片
```html
<div class="card legal-person-card">
  <h3>🏢 法人持股</h3>
  
  <div class="legal-grid">
    <!-- 表格 -->
    <table class="legal-table">
      <tr>
        <th>法人</th>
        <th>持股比例</th>
        <th>增減</th>
      </tr>
      <tr>
        <td>外資</td>
        <td>25.3%</td>
        <td class="up">↑ +1.2%</td>
      </tr>
      <tr>
        <td>投信</td>
        <td>8.5%</td>
        <td class="down">↓ -0.3%</td>
      </tr>
      <tr>
        <td>自營商</td>
        <td>3.2%</td>
        <td class="neutral">→ 0.0%</td>
      </tr>
      <tr class="highlight">
        <td>法人合計</td>
        <td>37.0%</td>
        <td class="up">↑ +0.9%</td>
      </tr>
    </table>
    
    <!-- 趨勢圖 -->
    <div class="trend-chart">
      <canvas id="legalPersonTrend"></canvas>
      <div class="legend">
        <span style="color: #2563eb;">外資</span>
        <span style="color: #16a34a;">投信</span>
        <span style="color: #dc2626;">自營</span>
        <span style="color: #7c3aed;">合計</span>
      </div>
    </div>
  </div>
</div>
```

---

## 🔄 實施步驟

### Phase 1：數據層開發（第 1 天）
- [ ] 開發 `marginModule` 數據抓取邏輯
- [ ] 開發 `legalPersonModule` 數據抓取邏輯
- [ ] 集成 CORS 代理備援方案
- [ ] 建立 localStorage 快取機制

### Phase 2：UI 開發（第 2 天）
- [ ] 新增「法人面」面板 HTML 結構
- [ ] 實現融資融券卡片樣式
- [ ] 實現法人持股卡片樣式
- [ ] 集成 Chart.js 繪製趨勢圖

### Phase 3：邏輯集成（第 3 天）
- [ ] 整合到主 `go()` 函數
- [ ] 實現每日自動更新
- [ ] 添加警示邏輯
- [ ] 完整測試

### Phase 4：優化與上線（第 4 天）
- [ ] 性能優化
- [ ] 移動端適配
- [ ] 發佈 v6.2.0

---

## 📊 預期結果

### v6.2.0 完成時
```
✅ 融資融券數據：實時更新
✅ 法人持股數據：實時更新 + 30天趨勢圖
✅ 自動警示系統：融資維持率 < 130%
✅ 新增獨立面板：「法人面」
✅ 移動端適配：完全響應式設計
```

---

## 📌 關鍵決策點

| 項目 | 選項 | 狀態 |
|------|------|------|
| 趨勢圖天數 | 7日 / 30日 / 90日 | 待決定 |
| 更新頻率 | 實時 / 每小時 / 每日 | 每日（現定） |
| 緩存機制 | localStorage / sessionStorage | 待決定 |
| 告警閾值 | 自訂 / 內置 | 內置 130% / 120% |

---

**準備開始開發？** 🚀
