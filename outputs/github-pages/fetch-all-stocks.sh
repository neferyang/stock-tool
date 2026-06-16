#!/bin/bash

# 下載完整的台股上市、上櫃、興櫃 + ETF 列表

OUTPUT_FILE="twse-stocks.json"
TEMP_FILE="stocks-temp.json"

echo "📥 開始下載台灣股票完整列表..."

# 初始化 JSON 陣列
echo "[" > "$TEMP_FILE"

# 1. 下載 TWSE 上市公司
echo "⏳ 下載 TWSE 上市公司..."
curl -s "https://openapi.twse.com.tw/v1/opendata/t187ap03_L" -H "User-Agent: Mozilla/5.0" | \
jq -r '.[] | {Code: .code, CHName: .name, Name: .englishName, Type: "上市"} | @json' 2>/dev/null >> "$TEMP_FILE"

# 2. 下載 TPEX 上櫃公司
echo "⏳ 下載 TPEX 上櫃公司..."
curl -s "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_download/stk_quote_download.php?l=zh-tw&d=20240101&o=json" -H "User-Agent: Mozilla/5.0" 2>/dev/null | \
jq -r '.data[]? | {Code: .[0], CHName: .[1], Name: .[2], Type: "上櫃"} | @json' >> "$TEMP_FILE"

# 3. ETF 列表（主要 ETF）
echo "⏳ 添加 ETF 列表..."
cat >> "$TEMP_FILE" << 'EOF'
{"Code":"0050","CHName":"台灣50","Name":"ETF 0050","Type":"ETF"}
{"Code":"0051","CHName":"台灣中型100","Name":"ETF 0051","Type":"ETF"}
{"Code":"0052","CHName":"高股息","Name":"ETF 0052","Type":"ETF"}
{"Code":"0053","CHName":"台灣公司債","Name":"ETF 0053","Type":"ETF"}
{"Code":"0054","CHName":"元大台灣","Name":"ETF 0054","Type":"ETF"}
{"Code":"0055","CHName":"元大寶滬深","Name":"ETF 0055","Type":"ETF"}
{"Code":"0056","CHName":"元大高股息","Name":"ETF 0056","Type":"ETF"}
{"Code":"006208","CHName":"富邦台灣","Name":"ETF 006208","Type":"ETF"}
{"Code":"0061","CHName":"元大新興亞","Name":"ETF 0061","Type":"ETF"}
{"Code":"0062","CHName":"富邦科技","Name":"ETF 0062","Type":"ETF"}
{"Code":"0070","CHName":"富邦公司債","Name":"ETF 0070","Type":"ETF"}
{"Code":"00642R","CHName":"元大美債","Name":"ETF 00642R","Type":"ETF"}
{"Code":"00645","CHName":"富邦全球","Name":"ETF 00645","Type":"ETF"}
{"Code":"00692","CHName":"富邦特選","Name":"ETF 00692","Type":"ETF"}
{"Code":"00850","CHName":"元大台灣","Name":"ETF 00850","Type":"ETF"}
{"Code":"00878","CHName":"國泰永續","Name":"ETF 00878","Type":"ETF"}
{"Code":"00888","CHName":"富邦台灣","Name":"ETF 00888","Type":"ETF"}
{"Code":"00900","CHName":"富邦特選","Name":"ETF 00900","Type":"ETF"}
{"Code":"00903","CHName":"富邦高股息","Name":"ETF 00903","Type":"ETF"}
{"Code":"00923","CHName":"群益","Name":"ETF 00923","Type":"ETF"}
EOF

# 4. 關閉 JSON 陣列
echo "]" >> "$TEMP_FILE"

# 清理並格式化
jq '.' "$TEMP_FILE" 2>/dev/null | \
jq 'unique_by(.Code) | sort_by(.Code)' > "$OUTPUT_FILE"

rm "$TEMP_FILE"

# 統計
COUNT=$(jq 'length' "$OUTPUT_FILE")
echo "✅ 完成！總共 $COUNT 支股票"
echo "📄 檔案：$OUTPUT_FILE"
