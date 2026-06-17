/**
 * Vercel 動態路由 - 單支股票數據 API
 */

const fs = require('fs');
const path = require('path');

// 讀取本地股票數據
function loadStockData() {
  try {
    const dataPath = path.join(process.cwd(), 'tw-stocks.json');
    const data = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
    return data.data || data.stocks || {};
  } catch (e) {
    console.error('❌ 讀取 tw-stocks.json 失敗:', e.message);
    return {};
  }
}

// 處理 CORS
function setCorsHeaders(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
}

module.exports = (req, res) => {
  setCorsHeaders(res);

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    const { code } = req.query;

    if (!code) {
      return res.status(400).json({
        status: 'error',
        message: '請提供股票代碼'
      });
    }

    const stocks = loadStockData();
    const cleanCode = String(code).replace('.TW', '').replace('.TWO', '');

    if (!stocks[cleanCode]) {
      return res.status(404).json({
        status: 'error',
        message: `無法找到股票 ${cleanCode}`
      });
    }

    const info = stocks[cleanCode];
    const price = info.price;
    const pe = info.pe;
    const pb = info.pb;
    const div_yield = info.dividend_yield;

    let eps = null;
    if (price && pe && pe > 0) {
      eps = price / pe;
    }

    let dividend = null;
    if (price && div_yield) {
      dividend = price * div_yield / 100 > 1 ? price * div_yield / 100 : price * div_yield;
    }

    const result = {
      code: cleanCode,
      name: info.name || cleanCode,
      price: price,
      pe: pe,
      pb: pb,
      eps: eps,
      dividend_yield: div_yield,
      dividend: dividend,
      '52_week_high': info['52_week_high'],
      '52_week_low': info['52_week_low'],
      market_cap: info.market_cap,
      shares_outstanding: info.shares_outstanding,
      roe: info.roe,
      fcf: info.fcf,
      operating_margin: info.operating_margin,
      profit_margin: info.profit_margin,
      updated: info.updated_at
    };

    res.status(200).json({
      status: 'success',
      data: result,
      timestamp: new Date().toISOString()
    });
  } catch (e) {
    res.status(500).json({
      status: 'error',
      message: e.message
    });
  }
};
