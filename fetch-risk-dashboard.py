#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動更新 daily-report.json 的 riskDashboard（市場風險指標儀表板）。

可自動化的 11 項指標（FRED + yfinance，官方/免費資料源）：
  巴菲特指標、台股年乖離率、美10年期公債殖利率、DXY、USD/TWD、VIX、
  美債10Y-2Y利差、高收益債信用利差、Sahm法則、Conference Board... (LEI無API不含)
  、WTI原油、初領失業救濟金

其餘 4 項（CAPE、S&P500 FCF殖利率、Fed全年降息預期、Conference Board LEI）
無穩定免費 API，維持人工更新；若超過 STALE_DAYS 天未更新，自動加註過舊警示。
"""
import json
import os
import urllib.request
from datetime import datetime, timezone

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# 人工維護指標（Tier C）：只做「資料過舊」檢查，不動數值
MANUAL_INDICATORS = {"CAPE 席勒本益比", "S&P 500 自由現金流殖利率", "Fed 全年降息預期", "Conference Board LEI"}


def fred_latest(series_id):
    url = (f"https://api.stlouisfed.org/fred/series/observations"
           f"?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json"
           f"&sort_order=desc&limit=1")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    obs = data["observations"][0]
    return float(obs["value"]), obs["date"]


def fred_series(series_id, limit=1):
    url = (f"https://api.stlouisfed.org/fred/series/observations"
           f"?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json"
           f"&sort_order=desc&limit={limit}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [(o["date"], float(o["value"])) for o in data["observations"] if o["value"] != "."]


def yf_latest(ticker):
    import yfinance as yf
    hist = yf.Ticker(ticker).history(period="5d")
    if hist.empty:
        raise RuntimeError(f"yfinance no data for {ticker}")
    last = hist.iloc[-1]
    date = hist.index[-1].strftime("%Y-%m-%d")
    return float(last["Close"]), date


def fmt_date(iso_date):
    y, m, d = iso_date.split("-")
    return f"{int(m)}/{int(d)}"


def tier(value, bounds, labels):
    """bounds 由小到大排序的門檻，labels 對應每個區間的 (status, key)"""
    for b, lab in zip(bounds, labels[:-1]):
        if value < b:
            return lab
    return labels[-1]


def build_buffett_indicator():
    will5000, d1 = fred_latest("WILL5000PRFC")
    gdp_data = fred_series("GDP", limit=1)
    gdp_date, gdp = gdp_data[0]
    ratio = will5000 / gdp * 100  # 近似值：Wilshire 5000 Full Cap Price Index / GDP
    status, note = tier(ratio, [150, 180, 200], [
        ("🟢", "低於150%，估值溫和"),
        ("🟡", "150~180%，估值偏熱"),
        ("🟠", "180~200%，接近警戒（>200%）"),
        ("🔴", "突破警戒（>200%），股市嚴重高估"),
    ])
    return {
        "name": "巴菲特指標（市值/GDP）",
        "current": f"{ratio:.1f}%（{fmt_date(d1)}，近似值：Wilshire5000/GDP）",
        "status": status,
        "statusText": note,
    }


def build_taiwan_deviation():
    import yfinance as yf
    hist = yf.Ticker("^TWII").history(period="400d")
    if len(hist) < 240:
        raise RuntimeError("TAIEX history insufficient")
    close = hist["Close"]
    ma240 = close.rolling(240).mean().iloc[-1]
    last = close.iloc[-1]
    dev = (last - ma240) / ma240 * 100
    date = close.index[-1].strftime("%Y-%m-%d")
    status, note = tier(dev, [15, 30, 45], [
        ("🟢", "乖離率溫和，未過熱"),
        ("🟡", "乖離率偏高，留意拉回風險"),
        ("🟠", "接近警戒（>45%），過熱訊號浮現"),
        ("🔴", "已進警戒區（>45%），過熱訊號明確"),
    ])
    return {
        "name": "台股年乖離率",
        "current": f"約{dev:.0f}%（{fmt_date(date)}，加權指數 vs 240日均線）",
        "status": status,
        "statusText": note,
    }


def build_us10y():
    val, date = fred_latest("DGS10")
    status, note = tier(val, [4.0, 4.5, 4.8], [
        ("🟢", "殖利率溫和"),
        ("🟡", "殖利率偏高，留意升勢"),
        ("🟠", f"距警戒（>4.80%）約{4.8-val:.2f}%"),
        ("🔴", "突破警戒（>4.80%），資金環境緊縮"),
    ])
    return {
        "name": "美10年期公債殖利率",
        "current": f"{val:.2f}%（{fmt_date(date)}）",
        "status": status,
        "statusText": note,
    }


def build_dxy():
    val, date = yf_latest("DX-Y.NYB")
    status, note = tier(val, [95, 100, 105], [
        ("🟢", "美元指數溫和"),
        ("🟡", "逼近100大關，升勢持續"),
        ("🟠", "接近警戒（>105）"),
        ("🔴", "突破警戒（>105），美元強勢施壓風險資產"),
    ])
    return {
        "name": "DXY 美元指數",
        "current": f"{val:.2f}（{fmt_date(date)}）",
        "status": status,
        "statusText": note,
    }


def build_usdtwd():
    val, date = yf_latest("TWD=X")
    status, note = tier(val, [31.0, 32.0, 32.5], [
        ("🟢", "新台幣匯價穩定"),
        ("🟡", "新台幣走貶，留意升勢"),
        ("🟠", "低於警戒（>32.50），但升勢明顯"),
        ("🔴", "突破警戒（>32.50），資金外流壓力升高"),
    ])
    return {
        "name": "美元兌台幣 USD/TWD",
        "current": f"{val:.2f}（{fmt_date(date)}）",
        "status": status,
        "statusText": note,
    }


def build_vix():
    val, date = yf_latest("^VIX")
    status, note = tier(val, [15, 20, 30], [
        ("🟢", "市場情緒平靜"),
        ("🟡", "波動率上升，留意情緒轉變"),
        ("🟠", "逼近警戒（20~30），波動率明顯上升"),
        ("🔴", "突破警戒（>30），市場恐慌"),
    ])
    return {
        "name": "VIX 恐慌指數",
        "current": f"{val:.1f}（{fmt_date(date)}）",
        "status": status,
        "statusText": note,
    }


def build_yield_curve():
    d10, date = fred_latest("DGS10")
    d2, _ = fred_latest("DGS2")
    spread = d10 - d2
    status, note = tier(spread, [0, 0.5, 1.0], [
        ("🔴", "殖利率曲線倒掛，衰退警訊"),
        ("🟡", "正值但幅度小，曲線仍顯壓抑"),
        ("🟠", "擴張中，尚未達健康擴張期（100bps）"),
        ("🟢", "曲線健康擴張（>100bps）"),
    ])
    return {
        "name": "美債10Y－2Y利差",
        "current": f"{spread:+.2f}%（10Y {d10:.2f}% - 2Y {d2:.2f}%，{fmt_date(date)}）",
        "status": status,
        "statusText": note,
    }


def build_hy_spread():
    val, date = fred_latest("BAMLH0A0HYM2")
    status, note = tier(val, [3.0, 4.0, 5.0], [
        ("🟢", "遠低於警戒（>5.0%），處寬鬆狀態"),
        ("🟡", "信用利差略升，留意風險定價"),
        ("🟠", "接近警戒（>5.0%）"),
        ("🔴", "突破警戒（>5.0%），信用風險升溫"),
    ])
    return {
        "name": "高收益債信用利差",
        "current": f"{val*100:.0f} bps（{val:.2f}%，{fmt_date(date)}）",
        "status": status,
        "statusText": note,
    }


def build_sahm():
    val, date = fred_latest("SAHMREALTIME")
    status, note = tier(val, [0.3, 0.5], [
        ("🟢", "未達警戒（≥0.50），景氣尚穩"),
        ("🟡", "接近警戒（≥0.50），失業率轉向留意"),
        ("🔴", "觸發警戒（≥0.50），衰退訊號確立"),
    ])
    return {
        "name": "Sahm 法則指標",
        "current": f"{val:.2f}（{fmt_date(date)}）",
        "status": status,
        "statusText": note,
    }


def build_wti():
    val, date = yf_latest("CL=F")
    status, note = tier(val, [70, 90, 100], [
        ("🟢", "原油價格溫和"),
        ("🟡", "距警戒（>$100）有距離"),
        ("🟠", "接近警戒（>$100）"),
        ("🔴", "突破警戒（>$100），通膨與供應風險升高"),
    ])
    return {
        "name": "WTI 原油",
        "current": f"${val:.0f}（{fmt_date(date)}）",
        "status": status,
        "statusText": note,
    }


def build_initial_claims():
    val, date = fred_latest("ICSA")
    val_k = val / 1000
    status, note = tier(val_k, [250, 300, 350], [
        ("🟢", "低於警戒（>25萬），勞動市場穩健"),
        ("🟡", "接近警戒（>25萬），留意升勢"),
        ("🟠", "逼近警戒（>30萬）"),
        ("🔴", "突破警戒（>35萬），勞動市場明顯惡化"),
    ])
    return {
        "name": "初領失業救濟金",
        "current": f"{val_k:.1f}萬/週（{fmt_date(date)}）",
        "status": status,
        "statusText": note,
    }


BUILDERS = [
    build_buffett_indicator,
    build_taiwan_deviation,
    build_us10y,
    build_dxy,
    build_usdtwd,
    build_vix,
    build_yield_curve,
    build_hy_spread,
    build_sahm,
    build_wti,
    build_initial_claims,
]


def main():
    if not FRED_API_KEY:
        print("❌ 缺少 FRED_API_KEY，略過風險儀表板更新")
        return

    with open("daily-report.json", "r", encoding="utf-8") as f:
        report = json.load(f)

    dashboard = report.get("riskDashboard")
    if not dashboard:
        print("❌ daily-report.json 缺少 riskDashboard 欄位")
        return

    updated_map = {}
    for builder in BUILDERS:
        try:
            result = builder()
            updated_map[result["name"]] = result
            print(f"✅ {result['name']} → {result['current']} {result['status']}")
        except Exception as e:
            print(f"⚠️ {builder.__name__} 更新失敗，保留原值：{e}")

    counts = {"🔴": 0, "🟠": 0, "🟡": 0, "🟢": 0}
    now = datetime.now(timezone.utc)
    today_str = f"{now.year}年{now.month}月{now.day}日"

    for layer in dashboard["layers"]:
        for ind in layer["indicators"]:
            if ind["name"] in updated_map:
                ind.update(updated_map[ind["name"]])
            elif ind["name"] in MANUAL_INDICATORS:
                if "⚠️ 資料已逾期" not in ind["statusText"]:
                    ind["statusText"] = f"⚠️ 資料已逾期，待人工更新｜{ind['statusText']}"
            counts[ind.get("status", "🟡")] = counts.get(ind.get("status", "🟡"), 0) + 1

    dashboard["date"] = today_str
    dashboard["summary"] = f"🔴×{counts['🔴']}　🟠×{counts['🟠']}　🟡×{counts['🟡']}　🟢×{counts['🟢']}"
    if counts["🔴"] >= 4:
        dashboard["rating"] = "高度警戒"
    elif counts["🔴"] + counts["🟠"] >= 4:
        dashboard["rating"] = "中度警戒"
    else:
        dashboard["rating"] = "正常觀察"

    with open("daily-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 風險儀表板已更新：{len(updated_map)}/{len(BUILDERS)} 項自動更新成功")


if __name__ == "__main__":
    main()
