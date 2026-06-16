export default async function handler(req, res) {
  // CORS 設置
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    const { url } = req.query;

    if (!url) {
      return res.status(400).json({ error: '缺少 url 參數' });
    }

    // 只允許特定的安全 URL
    const allowedHosts = [
      'openapi.twse.com.tw',
      'query1.finance.yahoo.com',
      'query2.finance.yahoo.com',
      'www.tpex.org.tw',
      'finnhub.io'
    ];

    const urlObj = new URL(decodeURIComponent(url));

    if (!allowedHosts.includes(urlObj.hostname)) {
      return res.status(403).json({ error: '不允許的域名' });
    }

    // 轉發請求到目標 API
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
      },
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      return res.status(response.status).json({
        error: `上游 API 返回 ${response.status}`,
        url: url
      });
    }

    const data = await response.json();

    res.setHeader('Content-Type', 'application/json');
    res.status(200).json(data);

  } catch (error) {
    console.error('代理錯誤:', error);
    res.status(500).json({
      error: '代理請求失敗',
      message: error.message
    });
  }
}
