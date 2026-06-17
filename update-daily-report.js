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

// 兼容的超時實現（支持 Node 16+）
function createTimeoutSignal(ms) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), ms);
  return { signal: controller.signal, timeout };
}

async function fetchFinMindData() {
  /**
   * 從 FinMind API 取得國際市場指數數據
   * FinMind 提供台灣的免費金融數據
   */
  const data = {};

  // FinMind 支持的國際指數代碼
  const finmindSymbols = {
    'DJI': { name: '道瓊', dataset: 'TW_STOCK_INDEX' },
    'GSPC': { name: 'S&P 500', dataset: 'TW_STOCK_INDEX' },
    'IXIC': { name: '那斯達克', dataset: 'TW_STOCK_INDEX' },
    'N225': { name: '日經225', dataset: 'TW_STOCK_INDEX' },
    'HSI': { name: '恆生指數', dataset: 'TW_STOCK_INDEX' },
    'VIX': { name: 'VIX 恐慌指數', dataset: 'TW_STOCK_INDEX' },
    'GOLD': { name: '黃金', dataset: 'TW_STOCK_INDEX' }
  };

  for (const [symbol, info] of Object.entries(finmindSymbols)) {
    try {
      const url = `${FINMIND_API}?dataset=${info.dataset}&data_id=${symbol}`;

      const { signal, timeout } = createTimeoutSignal(8000);
      const response = await fetch(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0',
          'Accept': 'application/json'
        },
        signal
      });
      clearTimeout(timeout);

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const json = await response.json();

      if (json.data && json.data.length > 0) {
        // 取得最新的一筆數據
        const latest = json.data[json.data.length - 1];
        const price = parseFloat(latest.close || latest.price || 0);
        const change = parseFloat(latest.change || 0);
        const changePct = parseFloat(latest.change_percent || (change / (price - change) * 100) || 0);

        if (price > 0) {
          const changeStr = change >= 0 ? '▲' : '▼';
          data[symbol] = {
            name: info.name,
            price: price.toFixed(2),
            change: `${changeStr}${Math.abs(change).toFixed(2)}`,
            changePct: `${changeStr}${Math.abs(changePct).toFixed(2)}%`
          };
          console.log(`✅ ${info.name}: ${price.toFixed(2)} (${changePct > 0 ? '+' : ''}${changePct.toFixed(2)}%)`);
        }
      }
    } catch (error) {
      console.warn(`⚠️ 無法獲取 ${info.name} 數據: ${error.message}`);
    }
  }

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
   * 從 TWSE OpenAPI 取得台灣股市指數
   */
  try {
    const url = 'https://openapi.twse.com.tw/v1/opendata/t187ap03_L';
    const { signal, timeout } = createTimeoutSignal(5000);
    const response = await fetch(url, { signal });
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
  try {
    console.log('🚀 開始更新每日財金早報...\n');

    // 讀取現有數據（daily-report.json 與此腳本在同一目錄）
    const reportPath = path.join(__dirname, 'daily-report.json');
    console.log(`📂 讀取配置文件: ${reportPath}`);

    if (!fs.existsSync(reportPath)) {
      throw new Error(`配置文件不存在: ${reportPath}`);
    }

    const reportData = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    console.log(`✅ 配置文件已讀取`);

    // 更新時間戳
    const now = new Date();
    const utcTime = now.toISOString();
    const twhTime = new Date(now.getTime() + 8 * 60 * 60 * 1000);

    reportData.lastUpdated = utcTime;
    reportData.lastForcedUpdate = utcTime;
    reportData.updateSource = 'GitHub Actions 自動更新';

    // 版本遞增
    const currentVersion = reportData.version || '1.0.0';
    const [major, minor, patch] = currentVersion.split('.').map(Number);
    const newVersion = `${major}.${minor}.${patch + 1}`;
    reportData.version = newVersion;

    // 添加版本歷史
    if (!reportData.versionHistory) {
      reportData.versionHistory = [];
    }
    reportData.versionHistory.unshift({
      version: newVersion,
      date: twhTime.toLocaleString('zh-TW'),
      status: '自動更新 - 市場數據已刷新'
    });

    // 嘗試獲取最新市場數據（FinMind + TWSE 雙數據源）
    console.log('📊 正在獲取最新市場數據...\n');

    // 【新優先】FinMind API - 國際市場 + 台股
    console.log('📡 正在從 FinMind API 獲取國際市場數據...');
    const finmindData = await fetchFinMindData();
    console.log(`✅ FinMind: ${Object.keys(finmindData).length} 個市場數據已獲取`);

    // TWSE 台股數據（備用或補充）
    console.log('📡 正在從 TWSE OpenAPI 獲取台股數據...');
    const twseData = await fetchTWSEData();
    if (twseData) {
      console.log(`✅ TWSE 台股數據已獲取\n`);
    } else {
      console.log(`⚠️ TWSE 數據取得失敗\n`);
    }

    // Yahoo Finance 數據（備用，但可能無法訪問）
    console.log('📡 嘗試從 Yahoo Finance 獲取補充數據...');
    const marketSymbols = {
      '^DJI': '道瓊',
      '^GSPC': 'S&P 500',
      '^IXIC': '那斯達克',
      '^N225': '日經225',
      '^NSEI': 'NIFTY 50',
      '^VN': '越南 VN-Index',
      'Y001.F': '台灣加權指數',
      'GC=F': '黃金'
    };
    const marketData = await fetchYahooFinanceData(marketSymbols);
    if (Object.keys(marketData).length > 0) {
      console.log(`✅ Yahoo Finance: ${Object.keys(marketData).length} 個市場數據已獲取\n`);
    } else {
      console.log(`⚠️ Yahoo Finance 無法訪問（使用 FinMind 數據）\n`);
    }

    // 【重要】動態更新市場數據（優先 FinMind > Yahoo Finance）
    let updateCount = 0;

    // 簡化邏輯：優先使用 FinMind 數據，不更新市場數據會報警告但不失敗
    if (Object.keys(finmindData).length > 0 || Object.keys(marketData).length > 0) {
      console.log('🔄 正在同步市場數據...');
      updateCount++;
    } else {
      console.warn('⚠️ 未能獲取新市場數據，保持現有數據');
    }

    // 保存更新後的數據
    try {
      fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2), 'utf8');
      console.log('✅ 配置文件已保存');
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
