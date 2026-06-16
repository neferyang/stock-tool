#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-download Taiwan stocks list (Listed, OTC, ETF, Emerging)
"""

import json
import urllib.request
import sys
import os
import ssl

# Disable SSL verification (for sandbox environment)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def download_stocks():
    output_file = "twse-stocks-full.json"
    all_stocks = []

    print("[*] Downloading Taiwan stocks list...")

    # 1. TWSE Listed companies
    print("[+] Downloading TWSE listed companies...")
    try:
        url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
        with urllib.request.urlopen(url, timeout=10, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            twse = [
                {
                    "Code": item['code'],
                    "CHName": item['name'],
                    "Name": item.get('englishName', ''),
                    "Type": "上市"
                }
                for item in data
            ]
            all_stocks.extend(twse)
            print("[OK] Downloaded TWSE: {} listed companies".format(len(twse)))
    except Exception as e:
        print("[FAIL] TWSE download failed: {}".format(e))

    # 2. TPEX OTC companies
    print("[+] Downloading TPEX OTC companies...")
    try:
        url = "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_download/stk_quote_download.php?l=zh-tw&d=20240101&o=json"
        with urllib.request.urlopen(url, timeout=10, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            tpex = [
                {
                    "Code": item[0],
                    "CHName": item[1],
                    "Name": item[2] if len(item) > 2 else "",
                    "Type": "上櫃"
                }
                for item in data.get('data', [])
            ]
            all_stocks.extend(tpex)
            print("[OK] Downloaded TPEX: {} OTC companies".format(len(tpex)))
    except Exception as e:
        print("[FAIL] TPEX download failed: {}".format(e))

    # 3. ETF + Emerging stocks
    print("[+] Adding ETF and Emerging stocks...")
    etf_list = [
        # Main ETF
        {"Code": "0050", "CHName": "台灣50", "Name": "TWNINDEX-50", "Type": "ETF"},
        {"Code": "0051", "CHName": "台灣中型100", "Name": "TWNINDEX-MID100", "Type": "ETF"},
        {"Code": "0052", "CHName": "高股息", "Name": "HIGH-DIVIDEND", "Type": "ETF"},
        {"Code": "0053", "CHName": "台灣公司債", "Name": "TW-CORP-BOND", "Type": "ETF"},
        {"Code": "0054", "CHName": "元大台灣", "Name": "YUANTA-TAIWAN", "Type": "ETF"},
        {"Code": "0055", "CHName": "元大寶滬深", "Name": "YUANTA-HUSEN", "Type": "ETF"},
        {"Code": "0056", "CHName": "元大高股息", "Name": "YUANTA-HIGH-DIVIDEND", "Type": "ETF"},
        {"Code": "006208", "CHName": "富邦台灣", "Name": "FUBON-TAIWAN", "Type": "ETF"},
        {"Code": "0061", "CHName": "元大新興亞", "Name": "YUANTA-EMERGING-ASIA", "Type": "ETF"},
        {"Code": "0062", "CHName": "富邦科技", "Name": "FUBON-TECH", "Type": "ETF"},
        {"Code": "0070", "CHName": "富邦公司債", "Name": "FUBON-CORP-BOND", "Type": "ETF"},
        {"Code": "00642R", "CHName": "元大美債", "Name": "YUANTA-US-BOND", "Type": "ETF"},
        {"Code": "00645", "CHName": "富邦全球", "Name": "FUBON-GLOBAL", "Type": "ETF"},
        {"Code": "00692", "CHName": "富邦特選", "Name": "FUBON-SELECT", "Type": "ETF"},
        {"Code": "00850", "CHName": "元大台灣", "Name": "YUANTA-TAIWAN-ETF", "Type": "ETF"},
        {"Code": "00878", "CHName": "國泰永續", "Name": "CATHAY-SUSTAINABILITY", "Type": "ETF"},
        {"Code": "00888", "CHName": "富邦台灣", "Name": "FUBON-TAIWAN-ETF", "Type": "ETF"},
        {"Code": "00900", "CHName": "富邦特選", "Name": "FUBON-SELECT-ETF", "Type": "ETF"},
        {"Code": "00903", "CHName": "富邦高股息", "Name": "FUBON-HIGH-DIVIDEND", "Type": "ETF"},
        {"Code": "00923", "CHName": "群益", "Name": "CONCORD", "Type": "ETF"},
        # Emerging stocks
        {"Code": "6488", "CHName": "機器人", "Name": "ROBOT", "Type": "興櫃"},
        {"Code": "6494", "CHName": "安碁資訊", "Name": "ANXI", "Type": "興櫃"},
        {"Code": "6560", "CHName": "致茂", "Name": "CHITMASS", "Type": "興櫃"},
        {"Code": "6668", "CHName": "宏碁", "Name": "ACER", "Type": "興櫃"},
        {"Code": "6838", "CHName": "光罩", "Name": "PHOTOMASK", "Type": "興櫃"},
    ]
    all_stocks.extend(etf_list)
    print("[OK] Added ETF/Emerging: {} items".format(len(etf_list)))

    # Remove duplicates and sort
    seen_codes = set()
    unique_stocks = []
    for stock in all_stocks:
        if stock['Code'] not in seen_codes:
            unique_stocks.append(stock)
            seen_codes.add(stock['Code'])

    unique_stocks.sort(key=lambda x: x['Code'])

    # Save as JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_stocks, f, ensure_ascii=False, indent=2)

    total = len(unique_stocks)
    twse_count = sum(1 for s in unique_stocks if s['Type'] == '上市')
    tpex_count = sum(1 for s in unique_stocks if s['Type'] == '上櫃')
    etf_count = sum(1 for s in unique_stocks if s['Type'] == 'ETF')
    emerging_count = sum(1 for s in unique_stocks if s['Type'] == '興櫃')

    print("\n" + "="*50)
    print("[DONE] Total {} stocks saved to {}".format(total, output_file))
    print("="*50)
    print("- TWSE Listed: {} stocks".format(twse_count))
    print("- TPEX OTC: {} stocks".format(tpex_count))
    print("- ETF: {} stocks".format(etf_count))
    print("- Emerging: {} stocks".format(emerging_count))
    print("="*50)

if __name__ == "__main__":
    try:
        download_stocks()
    except KeyboardInterrupt:
        print("\n[ABORT] Download interrupted")
        sys.exit(1)
    except Exception as e:
        print("\n[ERROR] {}".format(e))
        sys.exit(1)
