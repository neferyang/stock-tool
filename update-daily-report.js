#!/usr/bin/env node

/**
 * 每日財金早報自動更新腳本
 * 用途：從各種API獲取最新市場數據，更新 daily-report.json
 * 執行時機：GitHub Actions 每日 UTC 22:00 (台北時間 06:00)
 */

const fs = require('fs');
const path = require('path');

async function fetchYahooFinanceData(symbols) {
  /**
   * 從 Yahoo Finance 取得股市指數數據
   * symbols: { 'GSPC': 'S&P 500', '^DJI': '道瓊', '^IXIC': '那斯達克', '0050.TW': '台灣50' }
   */
  const data = {};

  for (const [symbol, name] of Object.entries(symbols)) {
    try {
      const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${symbol}&fields=regularMarketPrice,regularMarketChange,regularMarketChangePercent`;
      const response = await fetch(url, {
        headers: { 'User-Agent': 'Mozilla/5.0' },
        signal: AbortSignal.timeout(5000)
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const json = await response.json();
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
      }
    } catch (error) {
      console.warn(`⚠️ 無法獲取 ${name} 數據:`, error.message);
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
    const response = await fetch(url, {
      signal: AbortSignal.timeout(5000)
    });

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
    const reportData = JSON.parse(fs.readFileSync(reportPath, 'utf8'));

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

    // 嘗試獲取最新市場數據
    console.log('📊 正在從 Yahoo Finance 和 TWSE 獲取最新市場數據...\n');
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
    console.log(`✅ Yahoo Finance: ${Object.keys(marketData).length} 個市場數據已獲取`);

    // TWSE 台股數據
    console.log('📡 正在從 TWSE OpenAPI 獲取台股數據...');
    const twseData = await fetchTWSEData();
    if (twseData) {
      console.log(`✅ TWSE 台股數據已獲取\n`);
    } else {
      console.log(`⚠️ TWSE 數據取得失敗\n`);
    }

    // 【重要】動態更新市場數據
    let updateCount = 0;

    if (Object.keys(marketData).length > 0) {
      console.log('🔄 更新 Yahoo Finance 市場數據...');

      // 更新 markets 數組中的數據（根據獲取的最新數據）
      reportData.markets = reportData.markets.map(market => {
        const symbolMap = {
          '🇺🇸 美國股市': ['^DJI', '^GSPC', '^IXIC'],
          '🇯🇵 日經225': ['^N225'],
          '🇮🇳 印度': ['^NSEI'],
          '🇻🇳 越南 VN-Index': ['^VN'],
          '🥇 黃金': ['GC=F']
        };

        // 尋找對應的市場符號
        for (const [marketName, symbols] of Object.entries(symbolMap)) {
          if (market.name.includes(marketName.split(' ')[1] || marketName)) {
            market.items = symbols
              .filter(sym => marketData[sym])
              .map(sym => {
                const data = marketData[sym];
                const change = data.changePct >= 0 ? '▲' : '▼';
                return `${data.name}：${data.price}（${change}${Math.abs(data.changePct).toFixed(2)}%）`;
              });
            break;
          }
        }
        return market;
      });

      console.log(`✅ Yahoo Finance 市場數據已更新`);
      updateCount++;
    } else {
      console.warn('⚠️ Yahoo Finance 未能獲取新市場數據');
    }

    // 【新增】 TWSE 台股數據整合
    if (twseData && Array.isArray(twseData)) {
      console.log('🔄 更新 TWSE 台股數據...');

      // 尋找台股市場項目
      const taiwanMarket = reportData.markets.find(m => m.name.includes('台灣'));
      if (taiwanMarket && twseData.length > 0) {
        // 提取加權指數數據（通常第一筆記錄）
        const indexData = twseData.find(d => d['name'] && d['name'].includes('加權'));
        if (indexData) {
          const price = indexData['price'] || indexData['close'] || '—';
          const change = indexData['change'] || '—';
          const changePct = indexData['changePct'] || '—';
          const changeSymbol = (parseFloat(change) || 0) >= 0 ? '▲' : '▼';

          taiwanMarket.items = [
            `加權指數：${price}（${changeSymbol}${changePct}）`
          ];
          console.log(`✅ 台股加權指數已更新`);
          updateCount++;
        }
      }
    } else if (twseData === null) {
      console.warn('⚠️ TWSE 台股數據暫時無法更新');
    }

    if (updateCount === 0) {
      console.warn('⚠️ 未能獲取新市場數據，保持現有數據');
    }

    // 保存更新後的數據
    fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2), 'utf8');

    console.log('\n✅ 每日財金早報已更新');
    console.log(`   版本: v${reportData.version}`);
    console.log(`   更新時間: ${utcTime}`);
    console.log(`   台北時間: ${twhTime.toLocaleString('zh-TW')}`);
    console.log(`   更新來源: ${reportData.updateSource}`);
    console.log(`   資料源: Yahoo Finance API`);

    return true;
  } catch (error) {
    console.error('❌ 更新失敗:', error);
    process.exit(1);
  }
}

// 檢查 fetch 是否可用（Node 18+ 原生支持）
if (typeof fetch === 'undefined') {
  console.error('❌ 此 Node.js 版本不支持 fetch。需要 Node 18 或更高版本。');
  process.exit(1);
}

// 運行更新
updateDailyReport().then(() => {
  process.exit(0);
});
