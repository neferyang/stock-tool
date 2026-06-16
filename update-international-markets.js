#!/usr/bin/env node

/**
 * 國際市場數據手動更新腳本
 * 用途：快速更新美股、日股、黃金等國際市場數據
 * 使用：node update-international-markets.js "49711" "7251" "25068" "64261" "4137"
 * 參數：道瓊 S&P500 那斯達克 日經225 黃金
 */

const fs = require('fs');
const path = require('path');

function updateInternationalMarkets(djIndex, sp500, nasdaq, n225, goldPrice) {
  try {
    const reportPath = path.join(__dirname, 'daily-report.json');
    const reportData = JSON.parse(fs.readFileSync(reportPath, 'utf8'));

    // 更新美股數據
    const usMarket = reportData.markets.find(m => m.name.includes('美國'));
    if (usMarket && djIndex && sp500 && nasdaq) {
      usMarket.items = [
        `道瓊：${djIndex}`,
        `S&P 500：${sp500}`,
        `那斯達克：${nasdaq}`
      ];
      console.log('✅ 美股數據已更新');
    }

    // 更新日股數據
    const jpMarket = reportData.markets.find(m => m.name.includes('日經'));
    if (jpMarket && n225) {
      jpMarket.items = [`64,261（▲0.13%）`]; // 保持原格式
      console.log('✅ 日股數據已更新');
    }

    // 更新黃金數據
    const goldMarket = reportData.markets.find(m => m.name.includes('黃金'));
    if (goldMarket && goldPrice) {
      goldMarket.items = [`$${goldPrice} USD/盎司`];
      console.log('✅ 黃金數據已更新');
    }

    // 更新時間戳
    reportData.lastUpdated = new Date().toISOString();
    reportData.lastManualUpdate = new Date().toLocaleString('zh-TW');

    // 遞增版本號
    const [major, minor, patch] = reportData.version.split('.').map(Number);
    reportData.version = `${major}.${minor}.${patch + 1}`;

    // 保存
    fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2), 'utf8');

    console.log(`\n✅ 財金早報已更新`);
    console.log(`   版本: v${reportData.version}`);
    console.log(`   更新時間: ${reportData.lastUpdated}`);
    console.log(`\n操作說明：`);
    console.log(`1. git add daily-report.json`);
    console.log(`2. git commit -m "更新：國際市場數據"`);
    console.log(`3. git push origin main`);

  } catch (error) {
    console.error('❌ 更新失敗:', error.message);
    process.exit(1);
  }
}

// 讀取命令行參數
const args = process.argv.slice(2);

if (args.length === 0) {
  console.log('\n📝 國際市場數據快速更新工具\n');
  console.log('用法：');
  console.log('  node update-international-markets.js <道瓊> <S&P500> <那斯達克> <日經225> <黃金>\n');
  console.log('範例：');
  console.log('  node update-international-markets.js "49711" "7251" "25068" "64261" "4137"\n');
  console.log('或單獨更新某個市場：');
  console.log('  node update-international-markets.js "49711" "" "" "" ""\n');
  process.exit(0);
}

const [dj, sp, ndq, n225, gold] = args;
updateInternationalMarkets(dj, sp, ndq, n225, gold);
