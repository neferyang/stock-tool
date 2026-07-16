# 📅 明天的工作計劃（2026-06-09）

**開始時間**：早上  
**目標**：實施 v6.1.0 第一個修改 - 估值邏輯同步  
**預計耗時**：2 小時（1 小時實施 + 1 小時驗證）

---

## 🎯 計劃概述

### 本周目標（3 天）
- **Day 1（明天）**：v6.1.0 - 估值邏輯同步
- **Day 2**：v6.1.1 - 本地備用數據
- **Day 3**：v6.2.0 - 法人面模組

### 當前狀態
- ✅ 系統已回滾到 v6.04（穩定版）
- ✅ 所有修改代碼已暫存（安全保存）
- ✅ 詳細的實施說明已準備
- ✅ 驗證清單已準備

---

## 📝 明天的任務詳解

### 任務 1：估值邏輯同步（v6.1.0）

**修改內容**：3 層修正
1. **估值模型動態適配**（Line 1299-1324）
   - 識別成長型產業（fairYield < 2%）
   - 隱藏不適用的 GGM/股息折現模型
   - 添加防呆提示

2. **P/E 判定同步**（mkVerdict 函數）
   - Buy 建議：基於 `fairPE × 0.8` 動態判定
   - Sell 建議：基於 `fairPE × 1.3` 動態判定

3. **FCF 標籤明確化**（Line 155810）
   - 「自由現金流」→「FCF 利潤率」

---

## ✅ 驗證清單

### 修改 A：估值模型動態適配

**準備工作**（10 分鐘）
- [ ] 打開 index.html
- [ ] 找到 calcVals() 函數（第 1273 行）
- [ ] 將修改代碼複製進去

**代碼**：
```javascript
// Line 1299-1324 的修改
// 【防呆】：若 fairYield < 2%（成長型產業），則隱藏此模型
const isGrowthIndustry = params.fairYield < 2;

// 殖利率防線 - 成長型產業隱藏
if (div && div > 0 && !isGrowthIndustry) {
  // 計算並顯示
}

// GGM 股息折現 - 成長型產業隱藏並提示
if (div && div > 0 && !isGrowthIndustry) {
  // 計算並顯示
} else if (isGrowthIndustry && div && div > 0) {
  // 顯示防呆提示
  res.push({m:'GGM 股息折現', d:`【成長型產業提示】${indName}為成長型產業，股息折現模型不適用，建議使用 P/E 或 DCF 模型`, t:'N/A', b:'<span class="badge bn">不適用</span>'});
}

// 殖利率合理價 - 成長型產業隱藏
if (divYield && divYield > 0 && !isGrowthIndustry) {
  // 計算並顯示
}
```

**驗證方式**（15 分鐘）
```
假設本地有數據或 API 恢復：
□ 台積電 (2330)：GGM 應隱藏 + 防呆提示
□ 台泥 (1101)：GGM 應保留
□ P/B 正常顯示
□ 其他模型正常顯示
```

---

### 修改 B：P/E 判定同步

**準備工作**（5 分鐘）
- [ ] 找到 mkVerdict() 函數（第 1404 行）
- [ ] 修改 buy 建議部分（第 1443 行附近）
- [ ] 修改 sell 建議部分（第 1479 行附近）

**Buy 建議的修改**：
```javascript
// 基於產業 fairPE 的統一判定
const fairPE = params.fairPE || 16;
const lowerBound = Math.round(fairPE * 0.8);
const peRatioMsg = m.pe ? `P/E ${m.pe.toFixed(1)}x 低於 ${indName}合理下限 ${lowerBound}x` : '估值指標偏低';

return {
  t: 'buy',
  ti: '🟢 估值偏低，可考慮買進或分批布局',
  bo: `【基本面】
• ${peRatioMsg}
• 多個估值模型顯示股價低於合理價值...`
}
```

**Sell 建議的修改**：
```javascript
// 基於產業 fairPE 的統一判定
const fairPE = params.fairPE || 16;
const upperBound = Math.round(fairPE * 1.3);
const peRatioMsg = m.pe ? `P/E ${m.pe.toFixed(1)}x 已超過 ${indName}合理上限 ${upperBound}x` : '估值指標偏高';

return {
  t: 'sell',
  ti: '🔴 估值偏高，建議謹慎或考慮減碼',
  bo: `【估值分析】
• ${peRatioMsg}
• 股價溢價 15-20%...`
}
```

**驗證方式**（15 分鐘）
```
假設本地有數據或 API 恢復：
□ Buy 建議包含「P/E X.Xx 低於 XXX 合理下限 Xx」
□ Sell 建議包含「P/E X.Xx 已超過 XXX 合理上限 Xx」
□ 不同產業的 fairPE 應自動適應
```

---

### 修改 C：FCF 標籤明確化

**準備工作**（2 分鐘）
- [ ] 找到企業健康診斷卡代碼（第 155810 行）
- [ ] 將「自由現金流 (FCF)」改為「FCF 利潤率」

**修改**：
```javascript
// 原文
<div style="font-size:.85rem;color:#666;margin-bottom:3px;">自由現金流 (FCF)</div>

// 改為
<div style="font-size:.85rem;color:#666;margin-bottom:3px;">FCF 利潤率</div>
```

**驗證方式**（5 分鐘）
```
□ 診斷卡中的標籤改為「FCF 利潤率」
□ 下方數字仍為百分比（% 符號）
□ 提示或說明清楚表示這是比率
```

---

## 🧪 完整驗證步驟

### 前置條件
- API 恢復或本地數據可用
- 頁面能正常加載

### 驗證順序

**Step 1：測試成長型產業（台積電 2330）**
```
預期結果：
✅ P/E 評估顯示「合理」
✅ P/B 評估正常
✅ 【成長型產業提示】GGM 不適用
✅ 殖利率防線和殖利率合理價隱藏
```

**Step 2：測試防禦型產業（台泥 1101）**
```
預期結果：
✅ P/E 評估正常
✅ P/B 評估正常
✅ GGM 股息折現顯示
✅ 殖利率防線和殖利率合理價顯示
```

**Step 3：測試買賣建議**
```
預期結果（若 P/E 偏低）：
✅ Buy 建議包含「P/E XX.Xx 低於 XXX 合理下限 Xx」

預期結果（若 P/E 偏高）：
✅ Sell 建議包含「P/E XX.Xx 已超過 XXX 合理上限 Xx」
```

**Step 4：測試診斷卡**
```
預期結果：
✅ FCF 標籤改為「FCF 利潤率」
✅ 數字仍為百分比（例如 50%）
```

---

## 📊 如果 API 仍然失敗

**不要等待**，改用本地測試：

### 選項 1：使用本地測試數據
```javascript
// 在 Console 中直接測試
const testData = FINANCIAL_DB['2330'];
console.log(testData);
// 應顯示台積電數據
```

### 選項 2：手動插入測試數據
```javascript
// 在 go() 函數中手動設置數據
m.pe = 31.8;  // 台積電的 P/E
m.pb = 10.4;
m.div = 0.92;
// 然後驗證估值表格的輸出
```

---

## 📌 完成後的行動

**若驗證成功**：
1. 提交代碼：`git commit -m "v6.1.0: 估值邏輯同步 + FCF 標籤明確化"`
2. 更新 README.md 版本號
3. 開始 Day 2 的任務

**若發現問題**：
1. 記錄問題描述和截圖
2. 我會協助調試
3. 修復後重新驗證

---

## 💾 參考資源

- **詳細修改說明**：`VALUATION_LOGIC_SYNC_REPORT.md`
- **系統狀態**：`SYSTEM_STATUS_REPORT.md`
- **API 問題排查**：`TROUBLESHOOTING.md`

---

## ⏰ 時間表

| 時段 | 任務 | 預計時間 |
|------|------|---------|
| 早上 1h | 修改代碼 | 30 分鐘 |
| 早上 2h | 驗證測試 | 30 分鐘 |
| 中午 | 修復問題（若有）| 30-60 分鐘 |
| 下午 | 提交和記錄 | 15 分鐘 |

**總計**：1.5-2 小時

---

**準備好明天開始了嗎？** 🚀

