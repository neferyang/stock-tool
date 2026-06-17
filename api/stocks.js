/**
 * Vercel Serverless Function - 台股數據 API
 * 讀取本地 tw-stocks.json 並返回估值數據
 */

const fs = require('fs');
const path = require('path');

// 讀取本地股票數據
function loadStockData() {
  try {
    // 嘗試多個可能的路徑
    const possiblePaths = [
      path.join(process.cwd(), 'tw-stocks.json'),
      path.join(__dirname, '..', 'tw-stocks.json'),
      path.join(__dirname, '..', '..', 'tw-stocks.json'),
      'tw-stocks.json'
    ];

    let dataPath;
    for (const p of possiblePaths) {
      if (fs.existsSync(p)) {
        dataPath = p;
        console.log('✅ 找到 tw-stocks.json:', dataPath);
        break;
      }
    }

    if (!dataPath) {
      console.error('❌ 找不到 tw-stocks.json，嘗試的路徑:', possiblePaths);
      return {};
    }

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

// 主處理函數
module.exports = (req, res) => {
  setCorsHeaders(res);

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathname = url.pathname;
  const code = url.searchParams.get('code');

  // 路由處理
  if ((pathname === '/api/tw-stocks' || pathname === '/api/stocks') && req.method === 'GET') {
    // 如果有 code 查詢參數，返回單支股票；否則返回所有股票
    if (code) {
      handleSingleStock(res, code);
    } else {
      handleTwStocks(res);
    }
  } else if (pathname === '/api/health' && req.method === 'GET') {
    handleHealth(res);
  } else {
    res.status(404).json({ status: 'error', message: '端點不存在' });
  }
};

// 獲取所有台股數據
function handleTwStocks(res) {
  try {
    const stocks = loadStockData();
    const data = {};

    for (const [code, info] of Object.entries(stocks)) {
      const price = info.price;
      const pe = info.pe;
      const pb = info.pb;
      const div_yield = info.dividend_yield;

      // 計算額外字段
      let eps = null;
      if (price && pe && pe > 0) {
        eps = price / pe;
      }

      let dividend = null;
      if (price && div_yield) {
        dividend = price * div_yield / 100 > 1 ? price * div_yield / 100 : price * div_yield;
      }

      data[code] = {
        code: code,
        name: info.name || code,
        price: price,
        pe: pe,
        pb: pb,
        eps: eps,
        dividend_yield: div_yield,
        dividend: dividend,
        '52_week_high': info['52_week_high'],
        '52_week_low': info['52_week_low'],
        roe: info.roe,
        fcf: info.fcf,
        operating_margin: info.operating_margin,
        profit_margin: info.profit_margin,
        market_cap: info.market_cap,
        shares_outstanding: info.shares_outstanding,
        updated: info.updated_at
      };
    }

    res.status(200).json({
      status: 'success',
      data: data,
      count: Object.keys(data).length,
      timestamp: new Date().toISOString(),
      source: 'Vercel API (tw-stocks.json)'
    });
  } catch (e) {
    res.status(500).json({
      status: 'error',
      message: e.message
    });
  }
}

// 獲取單支股票數據
function handleSingleStock(res, code) {
  try {
    const stocks = loadStockData();
    console.log('✅ 載入股票數據:', Object.keys(stocks).length, '支股票');
    console.log('🔍 查詢代碼:', code);

    if (!stocks[code]) {
      console.log('❌ 找不到股票:', code, '可用代碼:', Object.keys(stocks).slice(0, 5));
      return res.status(404).json({
        status: 'error',
        message: `無法找到股票 ${code}`,
        availableCodes: Object.keys(stocks).slice(0, 10)
      });
    }

    console.log('✅ 找到股票:', code, stocks[code]);

    const info = stocks[code];
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
      code: code,
      name: info.name || code,
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
}

// 健康檢查
function handleHealth(res) {
  try {
    const stocks = loadStockData();
    res.status(200).json({
      status: 'ok',
      message: 'Vercel API 服務運行正常',
      stocks_loaded: Object.keys(stocks).length,
      timestamp: new Date().toISOString()
    });
  } catch (e) {
    res.status(500).json({
      status: 'error',
      message: e.message
    });
  }
}
