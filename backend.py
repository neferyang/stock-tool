#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
後端 Flask 服務 - 本地數據聚合
用途：讀取本地 tw-stocks.json，返回完整的估值數據
"""

import sys
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 讀取本地 tw-stocks.json
def load_tw_stocks():
    """加載本地台股數據"""
    try:
        with open('tw-stocks.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('data', {})
    except Exception as e:
        print(f"❌ 讀取 tw-stocks.json 失敗: {e}")
        return {}

@app.route('/api/tw-stocks', methods=['GET'])
def get_tw_stocks():
    """
    獲取台股數據（完整估值數據）
    """
    try:
        stocks = load_tw_stocks()

        # 轉換格式並計算額外字段
        data = {}
        for code, info in stocks.items():
            # 基本數據
            price = info.get('price')
            pe = info.get('pe')
            pb = info.get('pb')
            div_yield = info.get('dividend_yield')

            # 計算額外字段
            eps = None
            if price and pe and pe > 0:
                eps = price / pe

            dividend = None
            if price and div_yield:
                dividend = price * div_yield / 100 if div_yield < 100 else price * div_yield

            # 52 週數據
            high_52 = info.get('52_week_high')
            low_52 = info.get('52_week_low')

            data[code] = {
                "code": code,
                "name": info.get('name', code),
                "price": price,
                "pe": pe,
                "pb": pb,
                "eps": eps,
                "dividend_yield": div_yield,  # 百分比
                "dividend": dividend,  # 股利金額
                "52_week_high": high_52,
                "52_week_low": low_52,
                "roe": info.get('roe'),
                "fcf": info.get('fcf'),
                "operating_margin": info.get('operating_margin'),
                "profit_margin": info.get('profit_margin'),
                "market_cap": info.get('market_cap'),
                "shares_outstanding": info.get('shares_outstanding'),
                "updated": info.get('updated_at')
            }

        return jsonify({
            "status": "success",
            "data": data,
            "count": len(data),
            "timestamp": datetime.now().isoformat(),
            "source": "Local tw-stocks.json (yfinance)"
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
        # 清理代碼
        code = code.replace('.TW', '').replace('.TWO', '')

        stocks = load_tw_stocks()

        if code not in stocks:
            return jsonify({
                "status": "error",
                "message": f"無法找到股票 {code}"
            }), 404

        info = stocks[code]

        # 計算額外字段
        price = info.get('price')
        pe = info.get('pe')
        pb = info.get('pb')
        div_yield = info.get('dividend_yield')

        eps = None
        if price and pe and pe > 0:
            eps = price / pe

        dividend = None
        if price and div_yield:
            dividend = price * div_yield / 100 if div_yield < 100 else price * div_yield

        # 計算估值指標
        peg = None
        if pe and info.get('growth'):
            peg = pe / info.get('growth')

        result = {
            "code": code,
            "name": info.get('name', code),
            "price": price,
            "pe": pe,
            "pb": pb,
            "eps": eps,
            "dividend_yield": div_yield,
            "dividend": dividend,
            "52_week_high": info.get('52_week_high'),
            "52_week_low": info.get('52_week_low'),
            "market_cap": info.get('market_cap'),
            "shares_outstanding": info.get('shares_outstanding'),
            "roe": info.get('roe'),
            "fcf": info.get('fcf'),
            "operating_margin": info.get('operating_margin'),
            "profit_margin": info.get('profit_margin'),
            "peg": peg,
            "updated": info.get('updated_at')
        }

        return jsonify({
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })

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
    try:
        stocks = load_tw_stocks()
        return jsonify({
            "status": "ok",
            "message": "後端服務運行正常",
            "stocks_loaded": len(stocks),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 本地數據聚合後端服務啟動")
    print("="*50)
    print("📍 地址：http://localhost:5000")
    print("📍 API 端點：")
    print("   - GET /api/tw-stocks        → 獲取台股列表（完整估值）")
    print("   - GET /api/stock/<code>    → 獲取單支股票詳細數據")
    print("   - GET /api/health          → 健康檢查")
    print("📊 數據來源：本地 tw-stocks.json (yfinance)")
    print("="*50 + "\n")

    app.run(debug=True, host='127.0.0.1', port=5000)
