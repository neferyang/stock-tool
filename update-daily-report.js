#!/usr/bin/env node
/**
 * 每日財金早報自動更新腳本
 * 執行時機：GitHub Actions 每日 UTC 22:00 (台北時間 06:00)
 * 數據來源：fetch-market-data.py 產出的 market-data.json
 */

const fs = require('fs');
const path = require('path');

const weekDayChars = ['日', '一', '二', '三', '四', '五', '六'];

function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const weekday = weekDayChars[date.getDay()];
  return `${year}年${month}月${day}日（星期${weekday}）`;
}

function getPreviousTradingDay(date) {
  const day = date.getDay();
  let offset;
  if (day === 0) offset = 2;       // 週日 → 週五
  else if (day === 1) offset = 3;  // 週一 → 週五
  else offset = 1;
  return new Date(date.getTime() - offset * 24 * 60 * 60 * 1000);
}

function loadMarketData() {
  const p = path.join(__dirname, 'market-data.json');
  if (!fs.existsSync(p)) {
    console.warn('⚠️ market-data.json 不存在，跳過市場數據更新');
    return null;
  }
  try {
    const raw = JSON.parse(fs.readFileSync(p, 'utf8'));
    console.log(`✅ 讀取 market-data.json (${raw.count} 個指數，更新於 ${raw.updatedAt})`);
    return raw.indices || {};
  } catch (e) {
    console.warn(`⚠️ 讀取 market-data.json 失敗: ${e.message}`);
    return null;
  }
}

function loadAnalysisData() {
  const p = path.join(__dirname, 'market-analysis.json');
  if (!fs.existsSync(p)) {
    console.warn('⚠️ market-analysis.json 不存在，跳過分析文字更新');
    return null;
  }
  try {
    const raw = JSON.parse(fs.readFileSync(p, 'utf8'));
    console.log(`✅ 讀取 market-analysis.json (${Object.keys(raw.markets || {}).length} 個市場)`);
    return raw.markets || {};
  } catch (e) {
    console.warn(`⚠️ 讀取 market-analysis.json 失敗: ${e.message}`);
    return null;
  }
}

// 根據市場 name，從 market-data.json 的 indices 中找到對應資料
function findIndexData(indices, groupOrNameHints) {
  for (const [symbol, data] of Object.entries(indices)) {
    for (const hint of groupOrNameHints) {
      if (data.name.includes(hint) || (data.group && data.group === hint)) {
        return data;
      }
    }
  }
  return null;
}

function buildDisplayStr(data) {
  if (!data) return null;
  const { price, arrow, changePct, date } = data;
  const priceStr = price >= 1000 ? price.toLocaleString('en-US', {maximumFractionDigits: 0}) : price.toFixed(2);
  return `${priceStr}（${date}，${arrow}${Math.abs(changePct).toFixed(2)}%）`;
}

function updateMarkets(markets, indices) {
  if (!markets || !Array.isArray(markets)) return;

  for (const market of markets) {
    const name = market.name || '';

    // 美國股市
    if (name.includes('美國') || name.includes('美股')) {
      const dji = findIndexData(indices, ['道瓊', 'DJI']);
      const sp = findIndexData(indices, ['S&P', 'GSPC']);
      const nasdaq = findIndexData(indices, ['那斯達克', 'IXIC']);
      const items = [];
      if (dji) items.push(`道瓊：${buildDisplayStr(dji)}`);
      if (sp) items.push(`S&P 500：${buildDisplayStr(sp)}`);
      if (nasdaq) items.push(`那斯達克：${buildDisplayStr(nasdaq)}`);
      if (items.length > 0) {
        market.items = items;
        console.log(`✅ 美國股市更新 (${items.length} 項)`);
      }
    }

    // 日本
    if (name.includes('日經') || name.includes('日本')) {
      const d = findIndexData(indices, ['日經', 'N225', 'JP']);
      if (d) { market.items = [`日經225：${buildDisplayStr(d)}`]; console.log('✅ 日經225 更新'); }
    }

    // 台灣
    if (name.includes('台灣') || name.includes('台股')) {
      const d = findIndexData(indices, ['台灣加權', 'TWII', 'TW']);
      if (d) { market.items = [`台灣加權指數：${buildDisplayStr(d)}`]; console.log('✅ 台灣加權指數更新'); }
    }

    // 黃金
    if (name.includes('黃金') || name.includes('商品')) {
      const d = findIndexData(indices, ['黃金', 'GOLD', 'GC=F']);
      if (d) { market.items = [`黃金：${buildDisplayStr(d)}`]; console.log('✅ 黃金更新'); }
    }

    // 印度
    if (name.includes('印度') || name.includes('新興')) {
      const sensex = findIndexData(indices, ['SENSEX', 'IN']);
      const nifty = findIndexData(indices, ['NIFTY', 'NSEI']);
      const items = [];
      if (sensex) items.push(`SENSEX：${buildDisplayStr(sensex)}`);
      if (nifty) items.push(`NIFTY 50：${buildDisplayStr(nifty)}`);
      if (items.length > 0) { market.items = items; console.log('✅ 印度市場更新'); }
    }

    // 越南
    if (name.includes('越南') || name.includes('東南亞')) {
      const d = findIndexData(indices, ['越南', 'VN']);
      if (d) { market.items = [`越南 VN-Index：${buildDisplayStr(d)}`]; console.log('✅ 越南市場更新'); }
    }
  }
}

async function main() {
  const reportPath = path.join(__dirname, 'daily-report.json');
  console.log('🚀 財金早報自動更新開始\n');

  if (!fs.existsSync(reportPath)) {
    console.error(`❌ 找不到 daily-report.json`);
    process.exit(1);
  }

  const reportData = JSON.parse(fs.readFileSync(reportPath, 'utf8'));

  // 版本號保持不變（自動執行不遞增，只在功能更新時手動改）
  // reportData.version = '2.0.0';  // 保留此行供手動編輯

  // 時間更新（UTC+8 台北）
  const now = new Date();
  const twhTime = new Date(now.getTime() + 8 * 60 * 60 * 1000);
  reportData.lastUpdated = now.toISOString();
  reportData.updateSource = 'GitHub Actions (yfinance)';

  // 日期更新
  reportData.date = formatDate(twhTime);

  // basedOn：優先從美股實際交易日提取，否則用前一交易日估算
  let basedOnDate = null;
  const indices = marketData || {};
  const djiData = findIndexData(indices, ['道瓊', 'DJI']);
  if (djiData && djiData.date) {
    // 美股實際交易日：如 "06/20" → 構造完整日期
    const [month, day] = djiData.date.split('/');
    basedOnDate = new Date(twhTime.getFullYear(), parseInt(month) - 1, parseInt(day));
    console.log(`✅ 使用美股實際交易日: ${djiData.date}`);
  } else {
    // 無美股數據時，用估算
    basedOnDate = getPreviousTradingDay(twhTime);
    console.log(`⚠️ 使用估算交易日`);
  }
  const basedOnStr = formatDate(basedOnDate);
  reportData.basedOn = basedOnStr.substring(0, basedOnStr.indexOf('（')) + '（前一交易日）';

  // 版本歷史
  if (!reportData.versionHistory) reportData.versionHistory = [];
  reportData.versionHistory.unshift({
    version: reportData.version,
    date: twhTime.toLocaleString('zh-TW'),
    status: '自動更新 - yfinance 市場數據'
  });

  console.log(`📝 版本: v${reportData.version}`);
  console.log(`📅 日期: ${reportData.date}`);
  console.log(`📅 basedOn: ${reportData.basedOn}\n`);

  // 載入市場數據並更新數字
  const indices = loadMarketData();
  if (indices && Object.keys(indices).length > 0) {
    updateMarkets(reportData.markets, indices);
  } else {
    console.warn('⚠️ 無市場數據，僅更新版本和日期');
  }

  // 載入分析文字並更新 analysis 欄位
  const analysisMap = loadAnalysisData();
  if (analysisMap && reportData.markets) {
    const groupKeyMap = {
      '美國': 'US', '美股': 'US',
      '日經': 'JP', '日本': 'JP',
      '台灣': 'TW', '台股': 'TW',
      '黃金': 'GOLD', '商品': 'GOLD',
      '印度': 'IN',
      '越南': 'VN', '東南亞': 'VN',
    };
    for (const market of reportData.markets) {
      const name = market.name || '';
      let groupKey = null;
      for (const [keyword, key] of Object.entries(groupKeyMap)) {
        if (name.includes(keyword)) { groupKey = key; break; }
      }
      if (groupKey && analysisMap[groupKey]?.analysis) {
        market.analysis = analysisMap[groupKey].analysis;
        console.log(`✅ ${name} 分析文字已更新`);
      }
    }
  }

  reportData.updateSource = 'GitHub Actions (yfinance + Claude)';

  // 儲存
  fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2), 'utf8');
  console.log(`\n✅ 完成：v${reportData.version} 已儲存`);
}

main().catch(e => {
  console.error('❌ 更新失敗:', e.message);
  process.exit(1);
});
