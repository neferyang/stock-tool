#!/usr/bin/env node

/**
 * 每日財金早報自動更新腳本
 * 用途：從各種API獲取最新市場數據，更新 daily-report.json
 * 執行時機：GitHub Actions 每日 UTC 22:00 (台北時間 06:00)
 */

const fs = require('fs');
const path = require('path');

// FinMind API 基礎 URL
const FINMIND_API = 'https://api.finmind.com.tw/v1/data';
const FINMIND_TOKEN = process.env.FINMIND_TOKEN || '';
const TWSE_API_KEY = process.env.TWSE_API_KEY || '';

// 兼容的超時實現（支持 Node 16+）
function createTimeoutSignal(ms) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), ms);
  return { signal: controller.signal, timeout };
}

async function fetchFinMindData() {
  /**
   * 使用 FinMind API + token 獲取市場數據
   * 支援：台股加權指數、各國際指數
   */
  const data = {};

  if (!FINMIND_TOKEN) {
    console.warn('⚠️ 沒有 FINMIND_TOKEN，跳過 FinMind 數據獲取');
    return data;
  }

  console.log('📡 使用 FinMind API (含 token) 獲取數據...');

  // 今天日期和昨天日期（用於查詢）
  const today = new Date();
  const startDate = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000); // 往前7天確保有數據
  const startStr = startDate.toISOString().split('T')[0];

  // 台灣加權指數
  try {
    const url = `${FINMIND_API}?dataset=TaiwanStockPrice&data_id=TSE001&start_date=${startStr}&token=${FINMIND_TOKEN}`;
    const { signal, timeout } = createTimeoutSignal(10000);
    const r = await fetch(url, { signal });
    clearTimeout(timeout);
    if (r.ok) {
      const json = await r.json();
      if (json.data && json.data.length > 0) {
        const latest = json.data[json.data.length - 1];
        const close = parseFloat(latest.close || 0);
        const open = parseFloat(latest.open || close);
        const change = close - open;
        const changePct = (change / open * 100);
        const arrow = change >= 0 ? '▲' : '▼';
        data['TWII'] = {
          name: '台灣加權指數',
          price: close.toFixed(0),
          displayStr: `${close.toFixed(0)}（${latest.date}，${arrow}${Math.abs(changePct).toFixed(2)}%）`
        };
        console.log(`✅ 台灣加權指數: ${close.toFixed(0)}`);
      }
    }
  } catch (e) {
    console.warn(`⚠️ 台灣加權指數獲取失敗: ${e.message}`);
  }

  // 美國道瓊、S&P500、那斯達克 - 使用 TaiwanStockPrice 的 ETF 替代
  // 或直接使用 FinMind 的 USA 市場數據
  const usaSymbols = [
    { id: 'DJIA', name: '道瓊', key: 'DJI' },
    { id: 'SPX', name: 'S&P 500', key: 'GSPC' },
    { id: 'COMP', name: '那斯達克', key: 'IXIC' },
  ];

  for (const sym of usaSymbols) {
    try {
      const url = `${FINMIND_API}?dataset=StockMarket&data_id=${sym.id}&start_date=${startStr}&token=${FINMIND_TOKEN}`;
      const { signal, timeout } = createTimeoutSignal(10000);
      const r = await fetch(url, { signal });
      clearTimeout(timeout);
      if (r.ok) {
        const json = await r.json();
        if (json.data && json.data.length > 0) {
          const latest = json.data[json.data.length - 1];
          const close = parseFloat(latest.close || 0);
          const change = parseFloat(latest.Change || 0);
          const changePct = parseFloat(latest.ChangePercent || 0);
          if (close > 0) {
            const arrow = change >= 0 ? '▲' : '▼';
            data[sym.key] = {
              name: sym.name,
              price: close.toFixed(2),
              displayStr: `${close.toFixed(0)}（${arrow}${Math.abs(changePct).toFixed(2)}%）`
            };
            console.log(`✅ ${sym.name}: ${close.toFixed(0)}`);
          }
        }
      }
    } catch (e) {
      console.warn(`⚠️ ${sym.name} 獲取失敗: ${e.message}`);
    }
  }

  // 日本日經225
  try {
    const url = `${FINMIND_API}?dataset=StockMarket&data_id=N225&start_date=${startStr}&token=${FINMIND_TOKEN}`;
    const { signal, timeout } = createTimeoutSignal(10000);
    const r = await fetch(url, { signal });
    clearTimeout(timeout);
    if (r.ok) {
      const json = await r.json();
      if (json.data && json.data.length > 0) {
        const latest = json.data[json.data.length - 1];
        const close = parseFloat(latest.close || 0);
        const change = parseFloat(latest.Change || 0);
        const changePct = parseFloat(latest.ChangePercent || 0);
        if (close > 0) {
          const arrow = change >= 0 ? '▲' : '▼';
          data['N225'] = {
            name: '日經225',
            price: close.toFixed(0),
            displayStr: `${close.toFixed(0)}（${arrow}${Math.abs(changePct).toFixed(2)}%）`
          };
          console.log(`✅ 日經225: ${close.toFixed(0)}`);
        }
      }
    }
  } catch (e) {
    console.warn(`⚠️ 日經225 獲取失敗: ${e.message}`);
  }

  console.log(`📊 FinMind 獲取完成：${Object.keys(data).length} 個指數`);
  return data;
}

async function fetchYahooFinanceData(symbols) {
  /**
   * 從 Yahoo Finance 取得股市指數數據
   * symbols: { 'GSPC': 'S&P 500', '^DJI': '道瓊', '^IXIC': '那斯達克', '0050.TW': '台灣50' }
   */
  const data = {};

  for (const [symbol, name] of Object.entries(symbols)) {
    try {
      // 嘗試多個 Yahoo Finance 端點
      const endpoints = [
        `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${symbol}&fields=regularMarketPrice,regularMarketChange,regularMarketChangePercent`,
        `https://query2.finance.yahoo.com/v7/finance/quote?symbols=${symbol}&fields=regularMarketPrice,regularMarketChange,regularMarketChangePercent`,
        `https://finance.yahoo.com/quote/${symbol}`
      ];

      let response = null;
      let json = null;

      for (const url of endpoints) {
        try {
          const { signal, timeout: timeoutHandle } = createTimeoutSignal(8000);
          const req = await fetch(url, {
            headers: {
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
              'Accept': 'application/json',
              'Accept-Language': 'en-US,en;q=0.9',
              'DNT': '1',
              'Connection': 'keep-alive',
              'Upgrade-Insecure-Requests': '1'
            },
            signal
          });
          clearTimeout(timeoutHandle);

          if (req.ok) {
            response = req;
            try {
              json = await req.json();
            } catch (e) {
              // 如果不是 JSON，繼續嘗試下一個端點
              continue;
            }
            break;
          }
        } catch (err) {
          // 繼續嘗試下一個端點
          continue;
        }
      }

      if (!response || !json) {
        throw new Error('所有端點都無法訪問');
      }

      const quote = json.quoteResponse?.result?.[0];

      if (quote) {
        const price = quote.regularMarketPrice || 0;
        const change = quote.regularMarketChange || 0;
        const changePct = quote.regularMarketChangePercent || 0;
        const changeStr = change >= 0 ? '▲' : '▼';
        const pctStr = Math.abs(changePct).toFixed(2);

        data[symbol] = {
          name,
          price: price.toFixed(2),
          change: `${changeStr}${Math.abs(change).toFixed(2)}`,
          changePct: `${changeStr}${pctStr}%`
        };
        console.log(`✅ ${name}: ${price} (${changePct > 0 ? '+' : ''}${changePct.toFixed(2)}%)`);
      } else {
        throw new Error('無效的響應格式');
      }
    } catch (error) {
      console.warn(`⚠️ 無法獲取 ${name} 數據: ${error.message}`);
    }
  }

  return data;
}

async function fetchTWSEData() {
  /**
   * 從 TWSE OpenAPI 取得台灣股市指數（使用 API key）
   */
  try {
    const headers = { 'Accept': 'application/json' };
    if (TWSE_API_KEY) headers['Authorization'] = `Bearer ${TWSE_API_KEY}`;

    const url = 'https://openapi.twse.com.tw/v1/opendata/t187ap03_L';
    const { signal, timeout } = createTimeoutSignal(5000);
    const response = await fetch(url, { signal, headers });
    clearTimeout(timeout);

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    console.log(`✅ TWSE 數據已獲取`);
    return data;
  } catch (error) {
    console.warn('⚠️ 無法獲取 TWSE 數據:', error.message);
    return null;
  }
}

async function updateDailyReport() {
  const reportPath = path.join(__dirname, 'daily-report.json');
  console.log('🚀 開始更新每日財金早報...\n');
  console.log(`📂 配置文件: ${reportPath}`);

  try {
    // 讀取現有數據
    if (!fs.existsSync(reportPath)) {
      throw new Error(`配置文件不存在: ${reportPath}`);
    }

    const reportData = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    console.log(`✅ 配置文件已讀取\n`);

    // 【關鍵】先更新版本號和時間戳，即使後續 API 調用失敗
    const now = new Date();
    const utcTime = now.toISOString();
    const twhTime = new Date(now.getTime() + 8 * 60 * 60 * 1000);

    reportData.lastUpdated = utcTime;
    reportData.lastForcedUpdate = utcTime;
    reportData.updateSource = 'GitHub Actions 自動更新';

    // 版本遞增
    const currentVersion = reportData.version || '2.0.0';
    const [major, minor, patch] = currentVersion.split('.').map(Number);
    const newVersion = `${major}.${minor}.${patch + 1}`;
    reportData.version = newVersion;

    console.log(`📝 版本更新: v${newVersion}`);
    console.log(`⏰ 更新時間: ${twhTime.toLocaleString('zh-TW')}\n`);

    // 添加版本歷史
    if (!reportData.versionHistory) {
      reportData.versionHistory = [];
    }
    reportData.versionHistory.unshift({
      version: newVersion,
      date: twhTime.toLocaleString('zh-TW'),
      status: '自動更新 - 市場數據已刷新'
    });

    // 【改進】更新日期（基於當前時間的前一交易日）
    const today = new Date(twhTime);
    const dayOfWeek = today.getDay();
    let tradingDayOffset = 0;

    // 計算前一交易日（跳過週末）
    if (dayOfWeek === 0) {
      tradingDayOffset = 2; // 週日往回推2天（到週五）
    } else if (dayOfWeek === 1) {
      tradingDayOffset = 3; // 週一往回推3天（到週五）
    } else {
      tradingDayOffset = 1; // 其他日期往回推1天
    }

    const tradingDay = new Date(today.getTime() - tradingDayOffset * 24 * 60 * 60 * 1000);
    const weekDayChars = ['日', '一', '二', '三', '四', '五', '六'];

    // 格式化日期字符串
    const formatDate = (date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const weekday = weekDayChars[date.getDay()];
      return `${year}年${month}月${day}日（星期${weekday}）`;
    };

    reportData.date = formatDate(today);

    // basedOn 格式：2026年6月17日（前一交易日）
    const tradingDayFormatted = formatDate(tradingDay);
    const basedOnDate = tradingDayFormatted.substring(0, tradingDayFormatted.indexOf('（'));
    reportData.basedOn = basedOnDate + '（前一交易日）';

    // 【改進】先保存版本更新，再嘗試獲取市場數據
    console.log('💾 保存版本更新...');
    fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2), 'utf8');
    console.log(`✅ 版本已保存: v${reportData.version}\n`);

    // 獲取最新市場數據
    console.log('📊 正在獲取最新市場數據...\n');

    try {
      const finmindData = await fetchFinMindData();

      if (Object.keys(finmindData).length > 0) {
        console.log('✅ 獲得 FinMind 數據，更新 markets...');

        if (!Array.isArray(reportData.markets)) reportData.markets = [];

        for (const market of reportData.markets) {
          if (!market.items) continue;

          // 美國股市
          if (market.name.includes('美國')) {
            const items = [];
            if (finmindData['DJI']) items.push(`道瓊：${finmindData['DJI'].displayStr}`);
            if (finmindData['GSPC']) items.push(`S&P 500：${finmindData['GSPC'].displayStr}`);
            if (finmindData['IXIC']) items.push(`那斯達克：${finmindData['IXIC'].displayStr}`);
            if (items.length > 0) { market.items = items; console.log(`✅ 美國股市已更新`); }
          }

          // 日經225
          if (market.name.includes('日經')) {
            if (finmindData['N225']) {
              market.items = [finmindData['N225'].displayStr];
              console.log(`✅ 日經225已更新`);
            }
          }

          // 台灣加權指數
          if (market.name.includes('台灣')) {
            if (finmindData['TWII']) {
              market.items = [finmindData['TWII'].displayStr];
              console.log(`✅ 台灣加權指數已更新`);
            }
          }
        }
      } else {
        console.warn('⚠️ FinMind 未返回數據，保持現有市場數據');
      }
    } catch (dataError) {
      console.warn(`⚠️ 市場數據更新失敗（不影響版本更新）: ${dataError.message}`);
    }

    // 【關鍵】最終保存 - 即使 API 失敗也要保存版本號更新
    try {
      fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2), 'utf8');
      console.log('\n✅ 配置文件已保存');
    } catch (writeError) {
      console.error(`❌ 無法寫入配置文件: ${writeError.message}`);
      throw writeError;
    }

    console.log('\n✅ 每日財金早報已更新');
    console.log(`   版本: v${reportData.version}`);
    console.log(`   更新時間: ${utcTime}`);
    console.log(`   台北時間: ${twhTime.toLocaleString('zh-TW')}`);
    console.log(`   更新來源: ${reportData.updateSource}`);

    return true;
  } catch (error) {
    console.error('❌ 更新失敗:', error.message);
    console.error('堆棧追蹤:', error.stack);
    process.exit(1);
  }
}

// 檢查 fetch 是否可用（Node 18+ 原生支持）
if (typeof fetch === 'undefined') {
  console.error('❌ 此 Node.js 版本不支持 fetch。需要 Node 18 或更高版本。');
  process.exit(1);
}

// 運行更新
console.log('Node.js 版本:', process.version);
console.log('開始執行更新脚本...\n');

updateDailyReport()
  .then(() => {
    console.log('\n✅ 脚本執行成功');
    process.exit(0);
  })
  .catch(error => {
    console.error('\n❌ 脚本執行失敗:', error.message);
    process.exit(1);
  });
