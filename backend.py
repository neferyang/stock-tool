#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
後端 Flask 服務 - FinMind API 代理
用途：調用 FinMind API，為前端提供實時台股數據
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# FinMind API 配置
FINMIND_BASE_URL = "https://api.finmind.com.tw/v1/data"
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo1LmMvyL2lioibmVmZXlueWFuZGl3LkdzRW5VmZXluWFuZC5lcGFudlhRImRUlMH0.okL1XmB0OEXbbfIcTTi6R6uctugnRlaSK8uFL5aaRvs"

# 常見台股列表
TW_STOCKS = [
    "2330", "2454", "2317", "2308", "3008",
    "2207", "2002", "1101", "1303", "1326",
    "2883", "2891", "2892", "2887", "2890",
]

@app.route('/api/tw-stocks', methods=['GET'])
def get_tw_stocks():
    """
    獲取台股數據
    """
    try:
        # 獲取最近 10 天數據
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

        data = {}

        for code in TW_STOCKS:
            try:
                # 調用 FinMind API - TW_STOCK_DAY
                url = f"{FINMIND_BASE_URL}?dataset=TW_STOCK_DAY&data_id={code}&start_date={start_date}&end_date={end_date}"
                headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}

                response = requests.get(url, headers=headers, timeout=5)

                if response.status_code == 200:
                    result = response.json()
                    if result.get('data'):
                        latest = result['data'][-1]  # 最新數據
                        data[code] = {
                            "code": code,
                            "price": latest.get('close'),
                            "date": latest.get('date'),
                            "volume": latest.get('volume'),
                            "high": latest.get('high'),
                            "low": latest.get('low'),
                            "open": latest.get('open')
                        }
                        print(f"✅ {code} 數據成功")
                else:
                    print(f"❌ {code} 失敗: {response.status_code}")

            except Exception as e:
                print(f"❌ {code} 錯誤: {str(e)}")
                continue

        return jsonify({
            "status": "success",
            "data": data,
            "count": len(data),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/stock/<code>', methods=['GET'])
def get_stock(code):
    """
    獲取單支股票的詳細數據
    """
    try:
        # 參數
        days = request.args.get('days', 60, type=int)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # 清理代碼（移除 .TW 後綴）
        code = code.replace('.TW', '').replace('.TWO', '')

        # 調用 FinMind API
        url = f"{FINMIND_BASE_URL}?dataset=TW_STOCK_DAY&data_id={code}&start_date={start_date}&end_date={end_date}"
        headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}

        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            result = response.json()
            if result.get('data'):
                return jsonify({
                    "status": "success",
                    "code": code,
                    "data": result['data'],
                    "count": len(result['data']),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": f"無法找到股票 {code} 的數據"
                }), 404
        else:
            return jsonify({
                "status": "error",
                "message": f"FinMind API 錯誤: {response.status_code}"
            }), response.status_code

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康檢查
    """
    return jsonify({
        "status": "ok",
        "message": "後端服務運行正常",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 FinMind 後端服務啟動")
    print("="*50)
    print("📍 地址：http://localhost:5000")
    print("📍 API 端點：")
    print("   - GET /api/tw-stocks        → 獲取常見台股列表")
    print("   - GET /api/stock/<code>    → 獲取單支股票數據")
    print("   - GET /api/health          → 健康檢查")
    print("="*50 + "\n")

    app.run(debug=True, host='127.0.0.1', port=5000)
