# ✅ 數據更新驗證清單

確保財金早報的市場數據 **確實在更新**，而不是使用舊數據。

---

## 🔍 **驗證方法**

### **方法 1：檢查時間戳**

**步驟：**
1. 打開瀏覽器開發者工具 (F12)
2. 進入 **Console** 標籤
3. 執行以下命令：
   ```javascript
   fetch('daily-report.json').then(r => r.json()).then(d => {
     console.log('版本:', d.version);
     console.log('最後更新:', d.lastUpdated);
     console.log('更新來源:', d.updateSource);
     console.log('版本歷史:', d.versionHistory);
   });
   ```

**期望看到：**
```javascript
版本: 1.0.5 (或更高)
最後更新: 2026-06-15T06:15:30.000Z
更新來源: GitHub Actions 自動更新 (或 手動強制更新)
版本歷史: Array(5) [
  {version: '1.0.5', date: '2026/6/15 下午 2:15:30', status: '自動更新 - 市場數據已刷新'},
  ...
]
```

### **方法 2：檢查市場數據**

**步驟：**
1. 打開開發者工具 Console
2. 執行：
   ```javascript
   fetch('daily-report.json').then(r => r.json()).then(d => {
     console.table(d.markets.map(m => ({
       市場: m.name,
       數據: m.items.join(' | ')
     })));
   });
   ```

**期望看到：**
```
市場              數據
🇺🇸 美國股市     道瓊：49,711（▼0.42%）| S&P 500：7,251（▼0.22%）
🇯🇵 日經225      64,261（▲0.13%）
🇮🇳 印度         NIFTY 50：24,825（▼1.96%）
🇻🇳 越南         1,791（▼1.61%）
```

**檢查要點：**
- ✓ 數值有變化（不是靜態的硬編碼數據）
- ✓ 包含上升/下跌箭頭 (▲/▼)
- ✓ 包含漲跌幅百分比

### **方法 3：檢查 daily-report.json 原始文件**

**步驟：**
1. 右鍵點擊頁面 → 查看網頁原始檔
2. 搜尋 `lastUpdated`
3. 檢查時間戳

**期望：**
```json
{
  "version": "1.0.5",
  "lastUpdated": "2026-06-15T06:15:30+08:00",
  "lastForcedUpdate": "2026-06-15T06:15:30+08:00",
  "updateSource": "GitHub Actions 自動更新",
  "versionHistory": [
    {"version": "1.0.5", "date": "2026/6/15 下午 2:15:30", "status": "自動更新 - 市場數據已刷新"},
    ...
  ],
  "markets": [
    {
      "name": "🇺🇸 美國股市",
      "items": [
        "道瓊：49,711（▼0.42%）",
        ...
      ]
    },
    ...
  ]
}
```

---

## 📊 **自動更新驗證**

### **GitHub Actions 運行狀態**

**查看最新運行：**
→ https://github.com/neferyang/stock-tool/actions

**每日 06:00 AM (台北時間) 應該看到：**

```
✅ Daily Financial Report Update
   Status: Success (or "In progress")
   Commit: 🔄 Daily report auto-update: 2026-06-15 22:00:00 UTC
   Time: ~1-2 分鐘
```

### **檢查運行日誌**

1. 點進最新的 "Daily Financial Report Update" 運行
2. 展開 "Run daily report update script" 步驟
3. 應該看到：

```
🚀 開始更新每日財金早報...

📊 正在從 Yahoo Finance 獲取最新市場數據...
✅ 成功獲取 8 個市場數據

🔄 更新市場指數數據...
✅ 市場數據已動態更新

✅ 每日財金早報已更新
   版本: v1.0.5
   更新時間: 2026-06-15T06:00:00Z
   台北時間: 2026/6/15 下午 2:00:00
   更新來源: GitHub Actions 自動更新
   資料源: Yahoo Finance API
```

### **失敗時的診斷**

如果運行失敗，日誌應該顯示原因：

```
❌ 更新失敗: Error: ...

常見原因：
- 網絡連接失敗 (Yahoo Finance API 無法連接)
- 文件權限問題 (daily-report.json 無寫入權限)
- JSON 格式錯誤 (daily-report.json 結構損壞)
```

---

## 🧪 **強制更新驗證**

### **測試強制更新功能**

1. **記下當前版本號**
   ```javascript
   fetch('daily-report.json').then(r => r.json()).then(d => console.log('當前版本:', d.version));
   ```
   例：`v1.0.5`

2. **點擊「🔄 強制更新」按鈕**
   - 位置：財金早報 → 右上角

3. **等待 2 秒**
   - 按鈕應顯示 「✅ 已更新」（綠色）

4. **驗證版本號已更新**
   ```javascript
   fetch('daily-report.json?t=' + Date.now()).then(r => r.json()).then(d => console.log('新版本:', d.version));
   ```
   期望：`v1.0.6` (或更高)

5. **驗證更新來源**
   ```javascript
   fetch('daily-report.json?t=' + Date.now()).then(r => r.json()).then(d => console.log('更新來源:', d.updateSource));
   ```
   期望：`手動強制更新`

---

## 📈 **數據新鮮度指標**

### **檢查清單**

- [ ] **版本號遞增**
  - 每次更新版本號應該增加
  - 例：1.0.1 → 1.0.2 → 1.0.3

- [ ] **時間戳準確**
  - 自動更新時間應接近 06:00 AM
  - 強制更新時間應接近點擊時間（< 3 秒誤差）

- [ ] **版本歷史記錄**
  - 每次更新都應新增一筆歷史記錄
  - 應顯示更新狀態（自動更新 / 手動強制更新）

- [ ] **市場數據變化**
  - 股價應該有小數點後 2-4 位
  - 漲跌幅應該帶 % 符號
  - 應該有 ▲/▼ 箭頭

- [ ] **更新來源標示**
  - 自動更新：「GitHub Actions 自動更新」
  - 手動更新：「手動強制更新」

---

## 🔧 **手動測試更新腳本**

如果想在本地測試更新功能：

```bash
cd stock-tool
node scripts/update-daily-report.js
```

**預期輸出：**
```
🚀 開始更新每日財金早報...

📊 正在從 Yahoo Finance 獲取最新市場數據...
✅ 成功獲取 8 個市場數據

🔄 更新市場指數數據...
✅ 市場數據已動態更新

✅ 每日財金早報已更新
   版本: v1.0.6
   更新時間: 2026-06-15T14:30:45.123Z
   台北時間: 2026/6/15 下午 10:30:45
   更新來源: GitHub Actions 自動更新
   資料源: Yahoo Finance API
```

---

## ⚠️ **常見問題**

### **Q: 為什麼版本號沒有變化？**
**A:** 可能的原因：
1. 瀏覽器快取舊數據 → 硬刷新 (Ctrl+Shift+R)
2. 自動更新還沒運行 → 等待 06:00 AM 或手動點擊強制更新
3. 更新失敗 → 檢查 GitHub Actions 運行日誌

### **Q: 為什麼市場數據沒有變化？**
**A:** 檢查：
1. Yahoo Finance API 是否可連接
2. 檢查瀏覽器 Console 是否有錯誤信息
3. 查看 GitHub Actions 日誌的詳細錯誤

### **Q: 如何確認數據確實來自 Yahoo Finance？**
**A:** 
1. 打開開發者工具 Network 標籤
2. 清除列表，點擊強制更新
3. 應該看到對 `daily-report.json` 的請求
4. 在 Console 執行：
   ```javascript
   fetch('daily-report.json').then(r => r.json()).then(d => console.log('數據源:', d.markets[0].items));
   ```

---

## 📋 **完整驗證流程**

```
初始狀態
   ↓
[檢查當前版本] → 例：v1.0.5
   ↓
[點擊強制更新]
   ↓
[等待按鈕變綠]
   ↓
[檢查新版本] → 應為 v1.0.6
   ↓
[檢查時間戳] → 應為當前時間
   ↓
[檢查更新來源] → 應為「手動強制更新」
   ↓
[檢查市場數據] → 應有實時價格
   ↓
✅ 驗證完成 - 數據確實在更新
```

---

## 🎯 **結論**

如果以上所有項目都通過驗證，說明：

✅ 市場數據確實在更新  
✅ 版本號正確遞增  
✅ 時間戳準確記錄  
✅ 自動更新機制正常  
✅ 強制更新功能有效  
✅ 用戶看到的是最新數據  

**系統正在正確地獲取和更新最新的市場資料！** 🎉
