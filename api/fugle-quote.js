// Fugle 富果行情 API 代理：FUGLE_API_KEY 只存在 Vercel 環境變數，不進前端原始碼
// （跟同目錄 proxy.js 轉發的公開 API 不同，這把 Key 有用量額度，直接讓前端帶著打
// 會被任何訪客抽出來盜刷，所以用這支 serverless function 包一層）
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

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(
      `https://api.fugle.tw/marketdata/v1.0/stock/intraday/quote/${code}`,
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
