@echo off
chcp 65001 >nul
echo 正在傳送財金早報到 LINE...

curl -s -X POST https://api.line.me/v2/bot/message/push ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer RhVWmwVlV5Jx5HFwd/SRnCuvvixMeQwIeEoOLRC3CfJVjGAxbrFktSXayzbdD0GmT+AgtNjdr/QLRsaaxb5Unp79M/PvnYOUQLzO0NGbSc4SL/XuEuUodv4OluvywH2EJEwJVJURaMrtAmmMNkXUnwdB04t89/1O/w1cDnyilFU=" ^
  -d "{\"to\":\"Ua518c606809ebc65bba7239b11e346af\",\"messages\":[{\"type\":\"text\",\"text\":\"📊 每日財金早報 — 2026年5月26日\n\n[🇺🇸 美國股市](5/23收盤)\n・道瓊：50,579 +0.58%\n・S&P 500：7,473 +0.37%\n・那斯達克：26,343 +0.19%\n→ 道瓊創歷史新高，S&P 500連八週收紅\n\n[🇯🇵 日經225]\n・63,339(5/22)…65,158(5/25新高) +2.87%\n\n[🇮🇳 印度](5/25)\n・NIFTY：24,031 +1.32%\n・SENSEX：76,489 +1.42%\n\n[🇻🇳 越南 VN-Index]\n・1,886(5/25) +0.45%，年增逾41%\n\n[🇹🇼 台灣加權](5/23)\n・43,644 +0.13%\n\n[🥇 黃金]\n・$4,579/盎司(5/25) +1.39%\n\n━━━━━━━━\n[📈 風險指標]\n・VIX：16.59（平靜）\n・DXY：99.3（偏弱）\n・美10年債殖利率：4.56%\n\n━━━━━━━━\n[💡 今日觀察]\n1 美股連八週收紅，勿追高\n2 黃金高位，可逢回分批布局\n3 美債30年期5.2%，科技股估值壓力需留意\"}]}"

echo.
echo 傳送完成！請檢查您的 LINE。
pause
