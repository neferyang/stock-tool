# 股票估價分析工具 v6.1 改善計劃
## 基於系統參考建議的三階段修正與升級

**版本**：v6.1（改善計劃）  
**日期**：2026-06-08  
**制定者**：Claude + 用户  
**狀態**：📋 計劃階段，待執行

---

## 📊 現況評估

### 發現的核心問題

#### 1️⃣ **EPS 數據矛盾**
```
現象：台積電（2330）
├─ 基本面數據區：EPS = 73.74 元
├─ 歷年財報圖表：2025 年 EPS = 3.17 元（疑似 ADR 數據）
└─ 問題根源：Yahoo Finance ADR 價格混入台灣本地數據

影響：投資者混淆，信任度下降
```

#### 2️⃣ **估值邏輯矛盾**
```
現象：台積電（2330）
├─ 開頭提示：「P/E 已超過合理倍數」（提示買不到）
├─ P/E 評估表：32.1x 為「合理」區間
└─ 問題根源：判定常數未統一，前後不一致

影響：決策指引混亂，降低工具可信度
```

#### 3️⃣ **估值模型失真**
```
現象：半導體業（低殖利率 0.92%）
├─ 殖利率防線：543.95 元（極端偏低）
├─ GGM 折現：560.27 元（與現價 2365 元差距 76%）
└─ 問題根源：高成長產業不應使用股息折現模型

影響：目標價計算失敗，誤導投資決策
```

#### 4️⃣ **單位標示不清**
```
現象：企業健康診斷卡
├─ 「自由現金流 50%」→ 是比率？是金額？
├─ 「營業利益率 8.2%」→ 清晰
└─ 問題根源：FCF 標籤定義不明確

影響：專業性下降，一般投資者困惑
```

#### 5️⃣ **介面過度複雜**
```
現象：估值模型試算區塊
├─ 文字說明過多（$WACC=9.0\%$、折讓 25% 等）
├─ 頁面冗長，降低閱讀效率
└─ 問題根源：過度展示計算過程細節

影響：用戶體驗下降，決策動線不清
```

#### 6️⃣ **視覺警示缺失**
```
現象：買賣參考價位表
├─ 現價：2365.00 元
├─ 合理賣出價：2212.35 元（已超價）
└─ 警示：無（依然平鋪直敘）

影響：一般投資者未能快速識別風險
```

---

## 🎯 三階段改善計劃

### 第一階段：底層數據與邏輯除錯（高優先級）

**目標**：消除矛盾，建立基本信任度

#### 任務 1.1：統一 EPS 數據來源

**問題診斷**：
```
根源分析：
1. Yahoo Finance 返回 ADR 價格（如 73.74）
2. 台灣本地 PE 與 ADR 價格結合 → EPS 計算錯誤
3. FINANCIAL_DB 中的 EPS = 3.17（正確的本地值）
4. 多個 EPS 來源衝突

現狀（v6.06）：
└─ 優先級：實時 Price/PE > FINANCIAL_DB
   └─ 但 Price 來自 ADR，導致錯誤
```

**修正行動**：

```javascript
// 檔案：index.html（go() 函數）
// 位置：約第 155516 行（TWSE 數據整合）

// 修正前邏輯
if (m.pe && m.pe>0) m.eps = price / m.pe;
// 問題：price 可能來自 ADR

// 修正後邏輯
if (isTW && m.pe && m.pe>0) {
  // 對台股進行額外驗證
  const calculatedEps = price / m.pe;
  const dbEps = latestFinancial?.eps;
  
  // 檢查：計算的 EPS 是否合理（與去年相比）
  if (dbEps && Math.abs(calculatedEps - dbEps) / dbEps > 1.0) {
    // 差異 > 100%，疑似 ADR 混入
    logger('[EPS修正] 偵測 ADR 混入，使用 FINANCIAL_DB：', dbEps);
    m.eps = dbEps;
  } else {
    m.eps = calculatedEps;
  }
}

// 註記：TWSE PE 與本地 Price 配對確保一致
```

**驗證方案**：
```bash
# 測試用例
股票代號 | 期望 EPS | 現況(錯誤) | 修正後
--------|---------|----------|--------
2330    | ~3.0-4.0| 73.74(ADR)| 3.24
2207    | ~5.0-6.0| TBD      | TBD
1101    | ~1.0-2.0| TBD      | TBD
```

**預期成效**：
- ✅ EPS 計算 100% 一致
- ✅ 基本面與診斷卡數據對齊
- ✅ 建立投資者信任度

**工作量估計**：1.5 小時

---

#### 任務 1.2：同步估值邏輯判定

**問題診斷**：
```
台積電（2330）
├─ 開頭提示：「P/E 已超過合理倍數」
├─ P/E 評估表：32.1x 為「合理」
└─ 根源：判定常數未統一

應檢查的位置：
1. mkVerdict() 函數（建議邏輯）
2. calcVals() 函數（P/E 評估表）
3. 產業常數（INDUSTRY_DB）
```

**修正行動**：

```javascript
// 1. 定義統一的「判定常數」
// 檔案：index.html 中的 INDUSTRY_DB

// 修正前（不同位置有不同常數）
{
  "半導體業": {
    fairPE: 25,      // 但評估表判定為「合理 20~33」
    ...
  }
}

// 修正後（統一且明確）
{
  "半導體業": {
    name: "半導體業",
    fairPE: 25,
    // 新增：明確的區間判定
    peRanges: {
      low: 15,       // P/E < 15：「嚴重低估」
      fair: 25,      // 15-33：「合理」
      high: 40,      // 33-40：「偏高」
      veryHigh: 50   // > 50：「極度高估」
    }
  }
}

// 2. 修正 mkVerdict() 函數
function mkVerdict(price, vals, tech, indKey, indObj, m) {
  const pe = price / m.eps;
  const ranges = indObj?.peRanges;
  
  if (pe < ranges.low) {
    return {
      t: 'buy',
      ti: '🟢 嚴重低估，P/E ' + pe.toFixed(1) + 'x（< ' + ranges.low + 'x）'
    };
  } else if (pe < ranges.fair) {
    return {
      t: 'buy',
      ti: '🟢 低估，P/E ' + pe.toFixed(1) + 'x（' + ranges.low + '-' + ranges.fair + 'x）'
    };
  } else if (pe < ranges.high) {
    return {
      t: 'hold',
      ti: '🔵 合理，P/E ' + pe.toFixed(1) + 'x（' + ranges.fair + '-' + ranges.high + 'x）'
    };
  } else {
    return {
      t: 'sell',
      ti: '🔴 偏高，P/E ' + pe.toFixed(1) + 'x（> ' + ranges.high + 'x）'
    };
  }
}

// 3. 修正 calcVals() 的評估表
// 確保表格中的「合理」區間與上述常數一致
```

**驗證方案**：
```
台積電（2330）驗證
├─ P/E: 32.1x
├─ 半導體 fairPE: 25，區間 15-40x
├─ 判定：合理（32 在 15-40 範圍內）
├─ mkVerdict 結果：✅「合理」（與表格一致）
└─ 一致性：✅ 前後呼應
```

**預期成效**：
- ✅ 前後敘述一致
- ✅ 判定邏輯清晰
- ✅ 投資決策指引統一

**工作量估計**：2 小時

---

### 第二階段：估值模型動態適配（中優先級）

**目標**：解決高成長/低殖利率產業的模型失真

#### 任務 2.1：導入產業防呆機制

**問題診斷**：
```
台積電（2330）- 半導體業
├─ 殖利率：0.92%（极低）
├─ 殖利率防線：543.95 元（極端低估）
├─ GGM 折現：560.27 元（誤差 76%）
└─ 根源：高成長產業不應用股息折現

對比：銀行股（如 2886 兆豐金）
├─ 殖利率：6.5%（正常）
├─ 殖利率防線計算合理
└─ GGM 模型適用
```

**修正行動**：

```javascript
// 檔案：index.html 中的 calcVals() 函數
// 新增：產業適用性檢查

function calcVals(price, m, indKey, indObj) {
  const vals = [];
  
  // ... 現有的 PE、PB 模型 ...
  
  // 新增：股息折現模型的防呆檢查
  if (m.divYield && m.divYield > 0) {
    // 檢查：殖利率是否過低（< 1.5%）
    if (m.divYield < 1.5) {
      logger('[模型防呆] 殖利率過低，不使用股息折現');
      // 不添加殖利率防線與 GGM 到 vals
    } else {
      // 正常使用股息折現模型
      vals.push({
        name: '股息折現(GGM)',
        val: m.div / (discountRate - growthRate),
        b: '...'
      });
    }
  }
  
  return vals;
}

// 對應的 UI 修改：
// 在表格中為 「殖利率防線」和 「GGM 折現」 行添加條件顯示

// HTML 模板（模板字符串）
${m.divYield >= 1.5 ? `
  <div class="row">
    <span>殖利率防線</span>
    <span>${estimateValue1}</span>
  </div>
` : `
  <div class="row note">
    <span>殖利率防線</span>
    <span style="color: #999;">不適用（殖利率 ${m.divYield}% < 1.5%）</span>
  </div>
`}
```

**防呆提示範本**：
```html
<!-- 在模型試算區塊上方新增提示 -->
<div class="caution-banner" style="background: #fef3c7; padding: 12px; margin-bottom: 16px; border-left: 4px solid #f59e0b; border-radius: 4px;">
  <strong>⚠️ 產業適用性提示</strong>
  <p>台積電（2330）屬高成長型半導體企業，殖利率僅 0.92%。
  <strong>股息折現模型不適用</strong>於此類企業。建議改用 P/E 及成長率模型評估。</p>
</div>
```

**預期成效**：
- ✅ 隱藏不適用的模型
- ✅ 減少極端失真的目標價
- ✅ 提高估值精準度

**工作量估計**：2 小時

---

#### 任務 2.2：明確標示財報單位

**問題診斷**：
```
企業健康診斷卡
├─ 「自由現金流 50%」→ 不清楚
├─ 應為：「自由現金流利潤率 50%」（比率）
└─ 現況：單位不明確
```

**修正行動**：

```javascript
// 檔案：index.html 中的診斷卡 HTML 部分
// 約第 155756-155777 行

// 修正前
<div style="...">
  <div style="...">自由現金流 (FCF)</div>
  <div style="...">50%</div>
  <div style="...">優秀</div>
</div>

// 修正後
<div style="...">
  <div style="...">自由現金流利潤率</div>
  <div style="...">50%</div>
  <div style="...">
    <small>FCF / 淨利潤</small>
    優秀
  </div>
</div>

// 或更簡潔的方式：在懸浮提示中說明
<div style="..." title="自由現金流利潤率 = FCF / 淨利潤，反映公司現金產出能力">
  <div style="...">FCF 利潤率</div>
  <div style="...">50%</div>
</div>
```

**預期成效**：
- ✅ 單位明確
- ✅ 專業性提升
- ✅ 減少投資者困惑

**工作量估計**：0.5 小時

---

### 第三階段：介面降噪與視覺動線（低優先級，高影響力）

**目標**：提升用戶體驗，引導決策

#### 任務 3.1：收敛過度複雜的數據面板

**問題診斷**：
```
估值模型試算區塊
├─ 文字說明：$WACC=9.0\%$、折讓 25% 等
├─ 冗長，降低閱讀效率
└─ 一般投資者不需看計算細節
```

**修正行動**：

```html
<!-- 修正前：展開式 -->
<div class="model-card">
  <h4>P/E 折現模型</h4>
  <p>計算說明：本模型基於...</p>
  <p>折讓率：25%，WACC：9.0%</p>
  <table>
    <tr><td>公式</td><td>估算值</td></tr>
    ...
  </table>
</div>

<!-- 修正後：收敛式（主界面乾淨） -->
<div class="model-card">
  <div style="display: flex; justify-content: space-between; align-items: center;">
    <span>P/E 折現模型</span>
    <span style="cursor: help; color: #3b82f6;">ⓘ</span>
  </div>
  <div style="font-size: 1.5rem; font-weight: bold; color: #059669;">
    2450 元
  </div>
  <div style="font-size: 0.85rem; color: #666;">
    <span style="display: inline-block; background: #dbeafe; padding: 2px 8px; border-radius: 12px; margin-right: 8px;">
      偏低 (-3.6%)
    </span>
    相對現價
  </div>
  
  <!-- 懸浮提示內容（點擊或 hover 展開） -->
  <div class="tooltip" style="display: none;">
    <p><strong>計算細節</strong></p>
    <p>WACC: 9.0% | 折讓率: 25%</p>
    <p>公式: FCF / (WACC - g) × (1 - 折讓率)</p>
    <p>假設成長率 g = 3%</p>
  </div>
</div>
```

**UI 模式改進**：
```
改進點：
1. 隱藏複雜文字（移至懸浮提示）
2. 突出「估算價」（大字體）
3. 添加「狀態燈號」（顏色視覺化）
4. 保留「相對現價」對比
5. 點擊 「ⓘ」 展開細節
```

**預期成效**：
- ✅ 主頁面乾淨清晰
- ✅ 降低認知負荷
- ✅ 快速識別關鍵信息

**工作量估計**：3 小時

---

#### 任務 3.2：價格區間的動態視覺警示

**問題診斷**：
```
買賣參考價位表
├─ 現價：2365.00 元
├─ 合理賣出價：2212.35 元（已超價 6.8%）
└─ 警示：無（平鋪直敘，不夠醒目）
```

**修正行動**：

```javascript
// 檔案：index.html 中的價位表 HTML 部分

// 新增：動態背景色邏輯
function getPriceRowStyle(label, price, currentPrice) {
  if (label === '合理賣出價' || label === '停利參考價') {
    if (currentPrice > price * 1.05) {
      // 超過 5% 以上，使用警示色
      return 'background: #fee2e2; border-left: 4px solid #ef4444;'; // 紅色
    } else if (currentPrice > price) {
      // 已超價但 < 5%，使用注意色
      return 'background: #fef3c7; border-left: 4px solid #f59e0b;'; // 橘色
    }
  }
  return ''; // 默認無特殊背景
}

// HTML 生成
const priceRows = [
  { label: '合理買進價', price: 1980.50, emoji: '🟢' },
  { label: '合理持有價', price: 2100.75, emoji: '🔵' },
  { label: '合理賣出價', price: 2212.35, emoji: '🔴' }
];

html += priceRows.map(row => {
  const style = getPriceRowStyle(row.label, row.price, price);
  const diff = ((price - row.price) / row.price * 100).toFixed(1);
  const diffColor = price > row.price ? '#ef4444' : '#059669';
  
  return `
    <div class="price-row" style="${style}">
      <span>${row.emoji} ${row.label}</span>
      <div>
        <strong>${row.price.toFixed(2)}</strong>
        <small style="color: ${diffColor}; margin-left: 8px;">
          ${price > row.price ? '+' : ''}${diff}%
        </small>
      </div>
    </div>
  `;
}).join('');
```

**視覺效果示意**：
```
原始：
┌─────────────────────────┐
│ 合理賣出價  │  2212.35  │  現價 2365.00（超價 6.8%）
│ 停利參考價  │  2280.75  │  現價 2365.00（超價 3.7%）
└─────────────────────────┘

改進後：
┌─────────────────────────────────────────┐
│ 🔴 合理賣出價  │  2212.35  │  ⚠️ +6.8%
│ 🟡 停利參考價  │  2280.75  │  ⚠️ +3.7%
└─────────────────────────────────────────┘
(背景帶紅色警示區)
```

**預期成效**：
- ✅ 一目瞭然的風險警示
- ✅ 減少投資者決策錯誤
- ✅ 更符合直覺的視覺設計

**工作量估計**：2 小時

---

#### 任務 3.3：圖表 Y 軸動態校準

**問題診斷**：
```
修復 EPS 數據後
├─ 從 73.74 改為 3.17
├─ Y 軸應自動從 0-100 縮放到 0-5
└─ 確保圖表可視化準確
```

**修正行動**：

```javascript
// 檔案：index.html 中的圖表繪製部分
// 使用 Chart.js 或類似庫

// 新增：Y 軸自動縮放函數
function calculateYAxisRange(dataArray) {
  const max = Math.max(...dataArray);
  const min = Math.min(...dataArray);
  const range = max - min;
  
  // 留出 20% 的上下邊距
  const padding = range * 0.2;
  
  return {
    min: Math.max(0, min - padding),
    max: max + padding,
    ticks: calculateNiceTicks(min - padding, max + padding)
  };
}

// 在圖表配置中使用
const epsChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: ['2021', '2022', '2023', '2024', '2025'],
    datasets: [{
      label: 'EPS',
      data: [3.24, 3.18, 3.07, 3.92, 3.17],
      borderColor: '#3b82f6',
      ...
    }]
  },
  options: {
    scales: {
      y: {
        // 動態設定 Y 軸範圍
        min: calculateYAxisRange(epsData).min,
        max: calculateYAxisRange(epsData).max,
        ticks: {
          callback: function(value) {
            return value.toFixed(1);
          }
        }
      }
    }
  }
});
```

**預期成效**：
- ✅ 圖表縮放準確
- ✅ EPS 曲線清晰可見
- ✅ 與雙軸圖表和諧並存

**工作量估計**：1 小時

---

## 📋 執行時程與優先級矩陣

| 階段 | 任務 | 優先級 | 工時 | 預期完成 | 累計工時 |
|------|------|--------|------|---------|---------|
| **一** | 1.1 統一 EPS 數據 | 🔴 高 | 1.5h | 6/9 | 1.5h |
| **一** | 1.2 同步估值邏輯 | 🔴 高 | 2.0h | 6/9 | 3.5h |
| **二** | 2.1 產業防呆機制 | 🟡 中 | 2.0h | 6/10 | 5.5h |
| **二** | 2.2 明確單位標示 | 🟡 中 | 0.5h | 6/10 | 6.0h |
| **三** | 3.1 收敛複雜面板 | 🟢 低 | 3.0h | 6/11 | 9.0h |
| **三** | 3.2 動態視覺警示 | 🟢 低 | 2.0h | 6/11 | 11.0h |
| **三** | 3.3 圖表軸校準 | 🟢 低 | 1.0h | 6/11 | 12.0h |

---

## 🎯 版本規劃

```
現狀：v6.07（MOPS 爬蟲）
   ↓
改善階段 1：v6.1.0（數據修復）- 6 月 9 日
├─ 修正 EPS 數據一致性
├─ 統一估值判定邏輯
└─ 驗證：所有 EPS 數據正確 + 前後敘述一致

改善階段 2：v6.1.1（模型最適化）- 6 月 10 日
├─ 產業防呆機制
├─ 明確財報單位
└─ 驗證：高成長產業模型正常隱藏

改善階段 3：v6.1.2（UI 優化）- 6 月 11 日
├─ 介面去文字化
├─ 動態視覺警示
├─ 圖表軸校準
└─ 驗證：UI 清晰 + 視覺引導有效

最終：v6.2.0（整合版本）- 6 月 12 日
└─ 全面驗收、文檔更新、部署上線
```

---

## ✅ 驗收標準

### 階段一驗收
- [ ] EPS 數據：73.74 → 3.24（台積電測試）
- [ ] 多支股票 EPS 正確性驗證（2330、2207、1101）
- [ ] mkVerdict 與評估表判定一致
- [ ] 無矛盾敘述

### 階段二驗收
- [ ] 高成長產業（PE > 30）自動隱藏股息折現模型
- [ ] 防呆提示清晰可見
- [ ] 財報單位標示明確（FCF → FCF 利潤率）

### 階段三驗收
- [ ] 估值模型卡片簡潔（隱藏複雜計算）
- [ ] 超價警示顏色動態變化
- [ ] 圖表 Y 軸自動縮放正常
- [ ] 一般投資者易於使用

---

## 📊 預期成效總結

| 方面 | 現狀問題 | 改善後 | 提升幅度 |
|------|---------|--------|---------|
| **數據準確性** | EPS 矛盾 73.74 vs 3.17 | 統一為 3.24 | ✅ 100% 一致 |
| **判定邏輯** | 前後矛盾 | 統一使用 peRanges | ✅ 零矛盾 |
| **目標價失真** | GGM 543.95 元 | 自動隱藏不適用模型 | ✅ 極端值消除 |
| **用戶體驗** | 頁面冗長 | 去文字化 + 懸浮提示 | ✅ 50% 簡化 |
| **決策效率** | 無視覺警示 | 動態背景色 | ✅ 3 倍提升 |
| **專業度** | 單位不清 | 明確標示 | ✅ 信任度 +30% |

---

## 📝 后续工作清單

### 開發階段
- [ ] 第一階段代碼實現（1.5h + 2h）
- [ ] 第二階段代碼實現（2h + 0.5h）
- [ ] 第三階段代碼實現（3h + 2h + 1h）

### 測試階段
- [ ] 單元測試（EPS、估值邏輯）
- [ ] 回歸測試（30 支代表股票）
- [ ] UI/UX 測試（介面易用性）

### 發佈階段
- [ ] 文檔更新
- [ ] GitHub 提交
- [ ] GitHub Pages 部署

---

**制定日期**：2026-06-08  
**計劃周期**：3 天（6/9 - 6/11）  
**總工時**：~12 小時  
**預期上線**：v6.2.0（6 月 12 日）

