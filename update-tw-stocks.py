#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新 tw-stocks.json：補上官方公司簡稱（TWSE 上市 + TPEx 上櫃）"""
import json
import urllib.request
from datetime import datetime, timezone

TWSE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
TPEX_URL = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def build_short_name_map():
    short_names = {}

    for row in fetch_json(TWSE_URL):
        code = row.get("公司代號")
        name = row.get("公司簡稱")
        if code and name:
            short_names[code] = name

    for row in fetch_json(TPEX_URL):
        code = row.get("SecuritiesCompanyCode")
        name = row.get("CompanyAbbreviation")
        if code and name:
            short_names[code] = name

    return short_names


def main():
    with open("tw-stocks.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    short_names = build_short_name_map()
    matched = 0
    for code, stock in data["stocks"].items():
        short = short_names.get(code)
        if short:
            stock["short"] = short
            matched += 1

    data["updated"] = datetime.now(timezone.utc).isoformat()

    with open("tw-stocks.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已補上 {matched}/{len(data['stocks'])} 檔股票的官方簡稱")


if __name__ == "__main__":
    main()
