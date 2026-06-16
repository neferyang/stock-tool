# -*- coding: utf-8 -*-
import sys

SEP = "=" * 20

report = "\n".join([
    "📊 每日財金早報 — 2026年6月16日（星期二）",
    "資料基準：2026年6月15日（前一交易日）",
    "",
    "【🇺🇸 美國股市】",
    "・道瓊：（沿用前值，待確認）",
    "・S&P 500：（沿用前值，待確認）",
    "・那斯達克：（沿用前值，待確認）",
    "→ 美股受伊朗協議消息提振；Fed新主席Warsh 6/16-17首次會議定調後勢，市場高度聚焦其政策立場。",
    "",
    "【🇯🇵 日經225】",
    "・69,503（▲5.28%）",
    "→ 日股破歷史新高69,000點大關！伊朗協議帶動全球風險資產反彈，美日聯動上攻。",
    "",
    "【🇮🇳 印度】",
    "・NIFTY 50：23,854（▲0.98%）",
    "・SENSEX：76,264（▲0.97%）",
    "→ 印度股市反彈，伊朗協議扭轉前一日預算日跌勢；地緣風險緩和提振新興市場人氣。",
    "",
    "【🇻🇳 越南 VN-Index】",
    "・（待確認）",
    "→ 跟隨亞股反彈，受美伊和平協議提振。",
    "",
    "【🇹🇼 台灣加權指數】",
    "・（待確認）",
    "→ 台股今日走勢待觀察；外資近日賣超未止，新台幣貶勢延續至31.7元。",
    "",
    "【🥇 黃金】",
    "・$4,350 USD/盎司（6月15日）",
    "→ 金價強勢反彈▲3.12%；地緣和平訊號弱化避險需求，但仍受升息預期掣肘。",
    "",
    "━" * 20,
    "📡 市場風險指標儀表板",
    "🗓 2026年6月16日",
    "⚠️ 綜合評級：高度警戒",
    "🔴×4　🟠×4　🟡×5　🟢×2",
    "━" * 20,
    "",
    "【第一層】結構性估值",
    "📌 市場現在貴不貴？",
    "──────────────────",
    "🔴 CAPE 席勒本益比",
    "　現值　▶ 40（6月最新估計）",
    "　狀態　▶ 達歷史第二高，僅次2000年網路泡沫44.2倍；結構性泡沫風險最強",
    "",
    "🔴 巴菲特指標（市值/GDP）",
    "　現值　▶ 231.7%（5月高點）",
    "　狀態　▶ 突破歷史最高記錄，遠超警戒（>200%），股市嚴重高估",
    "",
    "🟠 S&P 500 自由現金流殖利率",
    "　現值　▶ 約2.4~3.0%（沿用前值）",
    "　狀態　▶ 已觸及或跌破警戒（<3.0%），處歷史低點，高利率環境下買點困難",
    "",
    "🔴 台股年乖離率",
    "　現值　▶ 約42~45%（6月中旬）",
    "　狀態　▶ 已進警戒區（>45%），外資賣超帶動技術面調整，過熱訊號未消",
    "",
    "━" * 20,
    "【第二層】總體貨幣環境",
    "📌 資金環境緊不緊？",
    "──────────────────",
    "🟠 美10年期公債殖利率",
    "　現值　▶ 4.47%（6月12日）",
    "　狀態　▶ 距警戒（>4.80%）約0.33%；升息預期與Fed新主席Warsh的鷹派立場支撑殖利率",
    "",
    "🔴 Fed 全年降息預期",
    "　現值　▶ <1次（市場定價零降息機率96%+）",
    "　狀態　▶ 深度觸發警戒（<2次），Kevin Warsh 6/16-17首次會議將傳遞升息或按兵不動訊號",
    "",
    "🟡 DXY 美元指數",
    "　現值　▶ 99.48（沿用6月中旬數據）",
    "　狀態　▶ 逼近100大關，升勢持續，距警戒（>105）仍有空間但強勢態勢明確",
    "",
    "🟠 美元兌台幣 USD/TWD",
    "　現值　▶ 31.60~31.70（6月12日）",
    "　狀態　▶ 低於警戒（>32.50），但升勢明顯，外資賣超導致新台幣連五日走貶",
    "",
    "━" * 20,
    "【第三層】市場情緒",
    "📌 市場現在情緒如何？",
    "──────────────────",
    "🟡 VIX 恐慌指數",
    "　現值　▶ 20.0+（6月中旬）",
    "　狀態　▶ 逼近警戒下緣（20~30），科技股調整與Fed會議預期推升波動率，隨時可能加速上升",
    "",
    "🟡 美債10Y－2Y利差",
    "　現值　▶ +0.37%（10Y 4.52% - 2Y 4.15%）（沿用前值）",
    "　狀態　▶ 正值擴張但幅度仍小，遠低於健康擴張期100bps，曲線仍顯控制",
    "",
    "🟢 高收益債信用利差",
    "　現值　▶ 275 bps（2.75%）（沿用前值）",
    "　狀態　▶ 遠低於警戒（>5.0%），處寬鬆狀態；與股市估值脫鉤，風險定價不足",
    "",
    "━" * 20,
    "【第四層】實體經濟",
    "📌 基本面有沒有裂縫？",
    "──────────────────",
    "🟡 Sahm 法則指標",
    "　現值　▶ 0.13（4月）（沿用前值）",
    "　狀態　▶ 未達警戒（≥0.50），但失業率持續攀升，衰退預警升溫；6月數據待7月初公布",
    "",
    "🟡 Conference Board LEI",
    "　現值　▶ 97.4（4月）（沿用前值）",
    "　狀態　▶ 六個月環比仍為負，領先指標疲軟；5月+6月數據待18日發布",
    "",
    "🟡 WTI 原油",
    "　現值　▶ $86（6月12日）",
    "　狀態　▶ 距警戒（>$100）有距離；川普取消對伊空襲暫緩地緣風險，但供應鏈脆弱性存在",
    "",
    "🟢 初領失業救濟金",
    "　現值　▶ 22.9萬/週（沿用前值）",
    "　狀態　▶ 低於警戒（>25萬），但升勢明顯逼近警戒，距警戒僅2~3萬人；失業惡化趨勢清晰",
    "",
    "━" * 20,
    "【綜合研判】",
    "高估值與衰退預警並存、地緣風險緩和提振但基本面隱憂未消：CAPE 40、巴菲特指標231.7%創歷史新高；同時初領22.9萬逼近警戒線、Sahm持續上升顯示衰退預警升溫。伊朗協議帶動全球風險資產反彈（日經破69000、新興市場齊漲），但Fed新主席Warsh今日首次FOMC會議仍是關鍵轉折點—市場預期98%維持利率，但任何升息或鷹派措辭將重燃估值重估壓力。台股外資賣壓未止、新台幣連貶至31.7元，高收益債利差275bps與股市估值脫鉤表示風險定價不足，一旦升息或衰退跡象確認，流動性快速收縮將衝擊高估值資產。",
    "📌 最關鍵觀察指標：（1）Fed 6/16-17 Warsh首次會議政策聲明與點陣圖走向；（2）初領失業救濟金本週是否突破23萬；（3）新興市場（台股、台幣）能否持續參與風險反彈或再度遭資金撤出",
    "━" * 20,
    "【📰 重要新聞】",
    "・Fed新主席Warsh今日(6/16-17)首次FOMC會議掌舵、市場聚焦其政策訊號：市場預期98%概率維持利率在3.50%-3.75%；但Warsh鷹派姿態與新任主席首次發言備受關注，將決定下半年升降息預期轉折。",
    "・美伊和平協議釋出、全球風險資產應聲反彈：日經指數破69,000歷史新高（▲5.28%）；NIFTY 50與SENSEX齊漲；金價反彈至4,350美元（▲3%）。",
    "・台股外資賣壓持續、新台幣連貶至31.7元：短期技術面仍顯弱勢；年乖離率45%+過熱訊號未消，需警戒外資後續大幅匯出。",
    "",
    "━" * 20,
    "【💡 今日觀察】",
    "1️⃣ 地緣風險緩和激發全球風險反彈、但結構性隱憂未消：美伊達成協議帶動日經破69,000歷史新高（▲5.28%）、新興市場齊漲；但CAPE 40、巴菲特指標231.7%創歷史高位，估值泡沫風險依舊；初領22.9萬逼近警戒線、Sahm 0.13持續上升，衰退預警仍然升溫。",
    "2️⃣ Fed首度決議成關鍵分界點、Warsh的政策訊號將決定後續方向：市場預期98%維持利率、但任何升息或鷹派措辭都將重燃估值重估壓力。高盛已放棄2026年降息預期，轉向升息預期；市場零降息定價達96%。",
    "3️⃣ 台股技術面弱勢、外資賣壓未止為隱患：外資近期大幅賣超、新台幣連貶至31.7元；年乖離率45%+過熱訊號未消。一旦全球風險偏好再度逆轉，台股將面臨重大調整壓力。建議逢反彈高檔減碼，提高現金部位應對波動。",
    "",
    "⚠️ 本資訊僅供參考，不構成投資建議",
])


def send_line_message(text):
    import json
    import ssl
    import socket
    import os

    token = "RhVWmwVlV5Jx5HFwd/SRnCuvvixMeQwIeEoOLRC3CfJVjGAxbrFktSXayzbdD0GmT+AgtNjdr/QLRsaaxb5Unp79M/PvnYOUQLzO0NGbSc4SL/XuEuUodv4OluvywH2EJEwJVJURaMrtAmmMNkXUnwdB04t89/1O/w1cDnyilFU="
    to_id = "Ua518c606809ebc65bba7239b11e346af"

    body = json.dumps({
        "messages": [{"type": "text", "text": text}]
    }, ensure_ascii=False).encode("utf-8")

    host = "api.line.me"
    path = "/v2/bot/message/broadcast"

    # 移除所有 proxy 環境變數
    for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "all_proxy"]:
        os.environ.pop(k, None)

    # 直接用 raw socket + ssl 連線，完全繞過 proxy
    ctx = ssl.create_default_context()
    raw_sock = socket.create_connection((host, 443), timeout=30)
    ssl_sock = ctx.wrap_socket(raw_sock, server_hostname=host)

    request = (
        "POST {} HTTP/1.1\r\n"
        "Host: {}\r\n"
        "Content-Type: application/json\r\n"
        "Authorization: Bearer {}\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).format(path, host, token, len(body)).encode("utf-8") + body

    ssl_sock.sendall(request)

    response_data = b""
    while True:
        chunk = ssl_sock.recv(4096)
        if not chunk:
            break
        response_data += chunk
    ssl_sock.close()

    response_str = response_data.decode("utf-8", errors="replace")
    status_line = response_str.split("\r\n")[0]
    status_code = int(status_line.split(" ")[1]) if " " in status_line else 0
    resp_body = response_str.split("\r\n\r\n", 1)[-1] if "\r\n\r\n" in response_str else response_str
    return status_code, resp_body

RESULT_PATH = r"C:\Users\AD83734\OneDrive - 和泰汽車-經銷商\桌面\Claude-workspace\line_result.txt"

try:
    from datetime import datetime
    _d = datetime.now()
    _today = "{}年{}月{}日".format(_d.year, _d.month, _d.day)
    if _today not in report.split("\n")[0]:
        msg = "略過發送：報告日期非當天（今天 {}，報告為「{}」）\n".format(_today, report.split("\n")[0])
        print(msg)
        with open(RESULT_PATH, "w", encoding="utf-8") as f:
            f.write(msg)
        sys.exit(0)

    print("正在傳送 LINE 訊息...")
    status, resp = send_line_message(report)
    result = "LINE API status: {}\nResponse: {}\n".format(status, resp)
    print(result)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        f.write(result)
    print("完成！")
except Exception as e:
    err = "Error: {}\n".format(e)
    print(err)
    import traceback
    traceback.print_exc()
    try:
        with open(RESULT_PATH, "w", encoding="utf-8") as f:
            f.write(err)
    except:
        pass
    sys.exit(1)
