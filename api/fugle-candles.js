// Fugle 富果歷史 K 線 API 代理：同 fugle-quote.js，Key 只存 Vercel 環境變數
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
  res.setHeader('Content-Type', 'application/json; charset=utf-8');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  const apiKey = process.env.FUGLE_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'FUGLE_API_KEY 未設定' });
  }

  const { code } = req.query;
  if (!code || !/^\d{4,6}$/.test(code)) {
    return res.status(400).json({ error: '缺少或無效的 code 參數（需為台股數字代號）' });
  }

  // 抓兩年日K，跟原本 Yahoo Finance chart 的 range=2y 對齊，估價工具的歷史走勢圖才夠長
  const to = new Date();
  const from = new Date(to.getTime() - 730 * 24 * 60 * 60 * 1000);
  const fmt = d => d.toISOString().slice(0, 10);

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(
      `https://api.fugle.tw/marketdata/v1.0/stock/historical/candles/${code}?from=${fmt(from)}&to=${fmt(to)}`,
      { headers: { 'X-API-KEY': apiKey }, signal: controller.signal }
    );
    clearTimeout(timeout);

    if (!response.ok) {
      return res.status(response.status).json({ error: `Fugle API 返回 ${response.status}` });
    }

    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    res.status(500).json({ error: 'Fugle 請求失敗', message: error.message });
  }
}
