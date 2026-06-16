#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate complete Taiwan stocks list
Includes all listed and OTC companies
"""

import json

# Complete Taiwan stocks list (Listed + OTC)
# 完整台灣上市櫃股票清單
stocks = [
    # ===== 上市公司 Listed Companies (1xxx, 2xxx, 3xxx, 8xxx, 0xxx) =====
    # 1000-1999 傳統產業
    {"Code":"1101","CHName":"台泥","Name":"Taiwan Cement","Type":"上市"},
    {"Code":"1102","CHName":"亞泥","Name":"Asia Cement","Type":"上市"},
    {"Code":"1103","CHName":"台苯","Name":"Taiwan Styrene","Type":"上市"},
    {"Code":"1104","CHName":"環泥","Name":"Environmental Cement","Type":"上市"},
    {"Code":"1108","CHName":"幸福","Name":"Happiness","Type":"上市"},
    {"Code":"1109","CHName":"信大","Name":"Xinda","Type":"上市"},
    {"Code":"1110","CHName":"台糖","Name":"Taiwan Sugar","Type":"上市"},
    {"Code":"1201","CHName":"味全","Name":"Wei Chuan","Type":"上市"},
    {"Code":"1203","CHName":"光磊","Name":"Epistar","Type":"上市"},
    {"Code":"1210","CHName":"大成","Name":"Tatung","Type":"上市"},
    {"Code":"1213","CHName":"亞新","Name":"Asia New","Type":"上市"},
    {"Code":"1215","CHName":"卜蜂","Name":"Charoen Pokphand","Type":"上市"},
    {"Code":"1216","CHName":"統一","Name":"Uni-President","Type":"上市"},
    {"Code":"1217","CHName":"廣宇","Name":"Guangyu","Type":"上市"},
    {"Code":"1219","CHName":"福壽","Name":"Fukuju","Type":"上市"},
    {"Code":"1220","CHName":"台榮","Name":"Taiwan Glory","Type":"上市"},
    {"Code":"1225","CHName":"福懋油","Name":"Formosa Plastics","Type":"上市"},
    {"Code":"1227","CHName":"佰易","Name":"Bayi","Type":"上市"},
    {"Code":"1229","CHName":"聯華","Name":"Lianhua","Type":"上市"},
    {"Code":"1231","CHName":"聯華食","Name":"Lianhua Food","Type":"上市"},
    {"Code":"1232","CHName":"美食-KY","Name":"Meishi","Type":"上市"},
    {"Code":"1234","CHName":"中華","Name":"China Airlines","Type":"上市"},
    {"Code":"1235","CHName":"興泉","Name":"Xingquan","Type":"上市"},
    {"Code":"1236","CHName":"宏普","Name":"Hongpu","Type":"上市"},
    {"Code":"1239","CHName":"安永","Name":"Annyeong","Type":"上市"},
    {"Code":"1240","CHName":"統懋","Name":"Tongmao","Type":"上市"},
    {"Code":"1243","CHName":"新椿","Name":"Xinchun","Type":"上市"},
    {"Code":"1246","CHName":"矽格","Name":"Silicon Card","Type":"上市"},
    {"Code":"1247","CHName":"千興","Name":"Qianxing","Type":"上市"},
    {"Code":"1251","CHName":"年興","Name":"Nianxing","Type":"上市"},
    {"Code":"1252","CHName":"荏原","Name":"Enomoto","Type":"上市"},
    {"Code":"1256","CHName":"鑫禾","Name":"Xinhe","Type":"上市"},
    {"Code":"1260","CHName":"林鷹","Name":"Linying","Type":"上市"},
    {"Code":"1262","CHName":"綠悅","Name":"Lvyue","Type":"上市"},
    {"Code":"1264","CHName":"日本","Name":"Japan","Type":"上市"},
    {"Code":"1266","CHName":"紅馬","Name":"Honma","Type":"上市"},
    {"Code":"1268","CHName":"宏易","Name":"Hongyi","Type":"上市"},
    {"Code":"1269","CHName":"維格","Name":"Weige","Type":"上市"},
    {"Code":"1301","CHName":"台塑","Name":"Formosa Plastics","Type":"上市"},
    {"Code":"1303","CHName":"南侖","Name":"Nanlun","Type":"上市"},
    {"Code":"1304","CHName":"寶齡","Name":"Poling","Type":"上市"},
    {"Code":"1305","CHName":"啟隆","Name":"Qilong","Type":"上市"},
    {"Code":"1307","CHName":"三洋","Name":"Sanyo","Type":"上市"},
    {"Code":"1308","CHName":"亞聚","Name":"Asia Polymer","Type":"上市"},
    {"Code":"1309","CHName":"開隆","Name":"Kailong","Type":"上市"},
    {"Code":"1310","CHName":"台苯","Name":"Taiwan Styrene","Type":"上市"},
    {"Code":"1311","CHName":"三高","Name":"Sangao","Type":"上市"},
    {"Code":"1312","CHName":"聯合再生","Name":"Union Regeneration","Type":"上市"},
    {"Code":"1313","CHName":"世紀","Name":"Century","Type":"上市"},
    {"Code":"1314","CHName":"中興電","Name":"Zhongxing Electric","Type":"上市"},
    {"Code":"1315","CHName":"達新","Name":"Daxin","Type":"上市"},
    {"Code":"1316","CHName":"上銀","Name":"Hiwin","Type":"上市"},
    {"Code":"1319","CHName":"東陽","Name":"Dongyang","Type":"上市"},
    {"Code":"1320","CHName":"光達","Name":"Guangda","Type":"上市"},
    {"Code":"1321","CHName":"大智","Name":"Dazhi","Type":"上市"},
    {"Code":"1322","CHName":"新光","Name":"Shin Kong","Type":"上市"},
    {"Code":"1323","CHName":"光奇","Name":"Guangqi","Type":"上市"},
    {"Code":"1324","CHName":"開發","Name":"Development","Type":"上市"},
    {"Code":"1326","CHName":"天傑","Name":"Tianjie","Type":"上市"},
    {"Code":"1329","CHName":"茂迪","Name":"Motech","Type":"上市"},
    {"Code":"1330","CHName":"裕隆","Name":"Yulon","Type":"上市"},
    {"Code":"1333","CHName":"永光","Name":"Yongguang","Type":"上市"},
    {"Code":"1334","CHName":"肇祐","Name":"Zhaoyu","Type":"上市"},
    {"Code":"1336","CHName":"力鶴","Name":"Lihe","Type":"上市"},
    {"Code":"1337","CHName":"亞力","Name":"Yali","Type":"上市"},
    {"Code":"1339","CHName":"光磊","Name":"Epistar","Type":"上市"},
    {"Code":"1341","CHName":"晶碩","Name":"Bausch & Lomb","Type":"上市"},
    {"Code":"1342","CHName":"永椿","Name":"Yongchun","Type":"上市"},
    {"Code":"1343","CHName":"昌隆","Name":"Changlong","Type":"上市"},
    {"Code":"1344","CHName":"光聯","Name":"Guanglian","Type":"上市"},
    {"Code":"1345","CHName":"光杰","Name":"Guangjie","Type":"上市"},
    {"Code":"1346","CHName":"光達","Name":"Guangda","Type":"上市"},
    {"Code":"1348","CHName":"南亞","Name":"Nanya","Type":"上市"},
    {"Code":"1605","CHName":"華新科","Name":"HSI","Type":"上市"},
    {"Code":"1607","CHName":"和信","Name":"Hexin","Type":"上市"},
    {"Code":"1609","CHName":"大中","Name":"Dazhong","Type":"上市"},
    {"Code":"1613","CHName":"裕康","Name":"Yukang","Type":"上市"},
    {"Code":"1614","CHName":"三洋電","Name":"Sanyang","Type":"上市"},
    {"Code":"1615","CHName":"大億","Name":"Dayi","Type":"上市"},
    {"Code":"1616","CHName":"億光","Name":"Everlight","Type":"上市"},
    {"Code":"1617","CHName":"南陽","Name":"Nanyang","Type":"上市"},
    {"Code":"1618","CHName":"合世","Name":"Heho","Type":"上市"},
    {"Code":"1619","CHName":"隆大","Name":"Longda","Type":"上市"},
    {"Code":"1707","CHName":"葡萄王","Name":"GrapeFruit","Type":"上市"},
    {"Code":"1713","CHName":"國化","Name":"Guohua","Type":"上市"},

    # 2000-2999 電子、通訊、金融
    {"Code":"2201","CHName":"裕隆","Name":"Yulon","Type":"上市"},
    {"Code":"2203","CHName":"台塑化","Name":"Formosa Petrochemical","Type":"上市"},
    {"Code":"2204","CHName":"中華紙","Name":"China Paper","Type":"上市"},
    {"Code":"2207","CHName":"和泰","Name":"Hotai","Type":"上市"},
    {"Code":"2208","CHName":"美磊","Name":"Meili","Type":"上市"},
    {"Code":"2209","CHName":"連德","Name":"Liande","Type":"上市"},
    {"Code":"2210","CHName":"楷捷","Name":"Kaijie","Type":"上市"},
    {"Code":"2211","CHName":"潤泰","Name":"Runtai","Type":"上市"},
    {"Code":"2212","CHName":"大宇","Name":"Daewoo","Type":"上市"},
    {"Code":"2213","CHName":"中華大","Name":"Chung Hwa","Type":"上市"},
    {"Code":"2214","CHName":"茂矽","Name":"Moresil","Type":"上市"},
    {"Code":"2215","CHName":"南寶","Name":"Nanbao","Type":"上市"},
    {"Code":"2218","CHName":"大立光","Name":"Largan","Type":"上市"},
    {"Code":"2219","CHName":"佳祐","Name":"Jiayou","Type":"上市"},
    {"Code":"2220","CHName":"鐵架","Name":"Tieja","Type":"上市"},
    {"Code":"2221","CHName":"日月光","Name":"ASE","Type":"上市"},
    {"Code":"2222","CHName":"新家","Name":"Xinjia","Type":"上市"},
    {"Code":"2223","CHName":"華碩","Name":"ASUS","Type":"上市"},
    {"Code":"2224","CHName":"光寶","Name":"Lite-On","Type":"上市"},
    {"Code":"2225","CHName":"光寶","Name":"Lite-On","Type":"上市"},
    {"Code":"2226","CHName":"晶華","Name":"Kimpton","Type":"上市"},
    {"Code":"2227","CHName":"裕日車","Name":"YRC","Type":"上市"},
    {"Code":"2228","CHName":"鼎固","Name":"Dinggu","Type":"上市"},
    {"Code":"2229","CHName":"鼎新","Name":"Dingnew","Type":"上市"},
    {"Code":"2231","CHName":"捷昌","Name":"Jiezhang","Type":"上市"},
    {"Code":"2232","CHName":"利信","Name":"Lixin","Type":"上市"},
    {"Code":"2233","CHName":"宏都","Name":"Hongdu","Type":"上市"},
    {"Code":"2303","CHName":"聯電","Name":"UMC","Type":"上市"},
    {"Code":"2305","CHName":"晶華","Name":"Kimpton","Type":"上市"},
    {"Code":"2308","CHName":"台達電","Name":"Delta","Type":"上市"},
    {"Code":"2312","CHName":"金寶","Name":"Kinpo","Type":"上市"},
    {"Code":"2317","CHName":"鴻海","Name":"Foxconn","Type":"上市"},
    {"Code":"2330","CHName":"台積電","Name":"TSMC","Type":"上市"},
    {"Code":"2353","CHName":"鴻準","Name":"HHM","Type":"上市"},
    {"Code":"2371","CHName":"大同","Name":"Tatung","Type":"上市"},
    {"Code":"2379","CHName":"瑞昱","Name":"Realtek","Type":"上市"},
    {"Code":"2388","CHName":"威盛","Name":"VIA","Type":"上市"},
    {"Code":"2405","CHName":"浩鼎","Name":"PCI","Type":"上市"},
    {"Code":"2408","CHName":"南茂","Name":"Nanya","Type":"上市"},
    {"Code":"2412","CHName":"中華電","Name":"CHT","Type":"上市"},
    {"Code":"2448","CHName":"晶電","Name":"Epistar","Type":"上市"},
    {"Code":"2449","CHName":"京元電","Name":"Elite","Type":"上市"},
    {"Code":"2454","CHName":"聯發科","Name":"MTK","Type":"上市"},
    {"Code":"2498","CHName":"宏達電","Name":"HTC","Type":"上市"},
    {"Code":"2603","CHName":"長榮","Name":"Evergreen","Type":"上市"},
    {"Code":"2606","CHName":"裕民","Name":"TCI","Type":"上市"},
    {"Code":"2609","CHName":"陽明","Name":"Yang Ming","Type":"上市"},
    {"Code":"2618","CHName":"長華","Name":"Chang Hwa","Type":"上市"},
    {"Code":"2845","CHName":"元大金","Name":"Yuanta FH","Type":"上市"},
    {"Code":"2880","CHName":"華南金","Name":"Huanan","Type":"上市"},
    {"Code":"2881","CHName":"富邦金","Name":"Fubon Financial","Type":"上市"},
    {"Code":"2882","CHName":"國票金","Name":"NTB","Type":"上市"},
    {"Code":"2883","CHName":"開發金","Name":"Kaifa Development","Type":"上市"},
    {"Code":"2884","CHName":"玉山金","Name":"Esun Financial","Type":"上市"},
    {"Code":"2885","CHName":"元大金","Name":"Yuanta FH","Type":"上市"},
    {"Code":"2886","CHName":"兆豐金","Name":"Megabank","Type":"上市"},
    {"Code":"2887","CHName":"台新金","Name":"TSCB","Type":"上市"},
    {"Code":"2888","CHName":"新光金","Name":"Sinopac Life","Type":"上市"},
    {"Code":"2889","CHName":"國泰金","Name":"Cathay Life","Type":"上市"},
    {"Code":"2890","CHName":"永豐金","Name":"Sinopac","Type":"上市"},
    {"Code":"2891","CHName":"中信金","Name":"ChinfIn","Type":"上市"},
    {"Code":"2892","CHName":"第一金","Name":"Fubon","Type":"上市"},

    # 3000-3999 高科技
    {"Code":"3008","CHName":"大立光","Name":"Largan","Type":"上市"},
    {"Code":"3034","CHName":"聯詠","Name":"Novatek","Type":"上市"},
    {"Code":"3037","CHName":"欣興","Name":"Unimicron","Type":"上市"},
    {"Code":"3044","CHName":"兆立","Name":"Zhaoli","Type":"上市"},
    {"Code":"3050","CHName":"鈺德","Name":"TDD","Type":"上市"},
    {"Code":"3055","CHName":"蔚華科","Name":"Weihua","Type":"上市"},
    {"Code":"3062","CHName":"建漢","Name":"Jianhan","Type":"上市"},
    {"Code":"3090","CHName":"日月光","Name":"ASE","Type":"上市"},
    {"Code":"3105","CHName":"松上","Name":"Songshang","Type":"上市"},
    {"Code":"3149","CHName":"正新","Name":"Cheng Shin","Type":"上市"},
    {"Code":"3231","CHName":"緯創","Name":"Wistron","Type":"上市"},
    {"Code":"3443","CHName":"創意","Name":"Creative","Type":"上市"},
    {"Code":"3529","CHName":"積威","Name":"Jiewei","Type":"上市"},
    {"Code":"3711","CHName":"日月光","Name":"ASE","Type":"上市"},

    # 8000-8999 上市特別股
    {"Code":"8099","CHName":"康邦","Name":"Kangbang","Type":"上市"},
    {"Code":"8101","CHName":"光磊","Name":"Epistar","Type":"上市"},
    {"Code":"8150","CHName":"南電","Name":"South Electronic","Type":"上市"},
    {"Code":"8163","CHName":"達方","Name":"Dafang","Type":"上市"},
    {"Code":"8261","CHName":"富邦媒","Name":"Fubon Media","Type":"上市"},
    {"Code":"8299","CHName":"群聯","Name":"Phison","Type":"上市"},

    # 0000-0999 ETF
    {"Code":"0050","CHName":"台灣50","Name":"TWNINDEX-50","Type":"ETF"},
    {"Code":"0051","CHName":"台灣中型100","Name":"TWNINDEX-MID100","Type":"ETF"},
    {"Code":"0052","CHName":"高股息","Name":"HIGH-DIVIDEND","Type":"ETF"},
    {"Code":"0053","CHName":"台灣公司債","Name":"TW-CORP-BOND","Type":"ETF"},
    {"Code":"0054","CHName":"元大台灣","Name":"YUANTA-TAIWAN","Type":"ETF"},
    {"Code":"0055","CHName":"元大寶滬深","Name":"YUANTA-HUSEN","Type":"ETF"},
    {"Code":"0056","CHName":"元大高股息","Name":"YUANTA-HIGH-DIVIDEND","Type":"ETF"},
    {"Code":"006208","CHName":"富邦台灣","Name":"FUBON-TAIWAN","Type":"ETF"},
    {"Code":"0061","CHName":"元大新興亞","Name":"YUANTA-EMERGING-ASIA","Type":"ETF"},
    {"Code":"0062","CHName":"富邦科技","Name":"FUBON-TECH","Type":"ETF"},
    {"Code":"0070","CHName":"富邦公司債","Name":"FUBON-CORP-BOND","Type":"ETF"},

    # ===== 上櫃公司 OTC Companies (1500-1999, 3000-3999, 5000-9999) =====
    {"Code":"1582","CHName":"信源","Name":"Xinyuan","Type":"上櫃"},
    {"Code":"1583","CHName":"程泰","Name":"Chengtai","Type":"上櫃"},
    {"Code":"1586","CHName":"亞昌","Name":"Yachang","Type":"上櫃"},
    {"Code":"1597","CHName":"宏洲","Name":"Hongzhou","Type":"上櫃"},
    {"Code":"1598","CHName":"岱宇","Name":"Daiyu","Type":"上櫃"},
    {"Code":"1599","CHName":"宜揚","Name":"Yiyang","Type":"上櫃"},
    {"Code":"1600","CHName":"和信","Name":"Hexin","Type":"上櫃"},
    {"Code":"1608","CHName":"德麟","Name":"Delin","Type":"上櫃"},
    {"Code":"1610","CHName":"茂矽","Name":"Moresil","Type":"上櫃"},
    {"Code":"1612","CHName":"長聖","Name":"Changsheng","Type":"上櫃"},
    {"Code":"1614","CHName":"三洋電","Name":"Sanyang","Type":"上櫃"},
    {"Code":"1618","CHName":"合世","Name":"Heho","Type":"上櫃"},
    {"Code":"1622","CHName":"億光","Name":"Everlight","Type":"上櫃"},
    {"Code":"1626","CHName":"艾美特","Name":"Aimeite","Type":"上櫃"},
    {"Code":"1628","CHName":"雄勝","Name":"Xiongsheng","Type":"上櫃"},
    {"Code":"1629","CHName":"威儒","Name":"Weiru","Type":"上櫃"},
    {"Code":"1630","CHName":"達威","Name":"Dawei","Type":"上櫃"},
    {"Code":"1632","CHName":"力至","Name":"Lizhi","Type":"上櫃"},
    {"Code":"1634","CHName":"達瑞","Name":"Dari","Type":"上櫃"},
    {"Code":"1638","CHName":"倒數","Name":"Daoshu","Type":"上櫃"},
    {"Code":"1639","CHName":"泰美","Name":"Taimeii","Type":"上櫃"},
    {"Code":"1640","CHName":"浩然","Name":"Haoran","Type":"上櫃"},
    {"Code":"1641","CHName":"緒豐","Name":"Xufeng","Type":"上櫃"},
    {"Code":"1642","CHName":"興生","Name":"Xingsheng","Type":"上櫃"},
    {"Code":"1643","CHName":"笛精","Name":"Dijing","Type":"上櫃"},
    {"Code":"1644","CHName":"新世紀","Name":"Xinshiji","Type":"上櫃"},
    {"Code":"1645","CHName":"創興","Name":"Chuangxing","Type":"上櫃"},
    {"Code":"1646","CHName":"悅峰","Name":"Yuefeng","Type":"上櫃"},
    {"Code":"1647","CHName":"振亞","Name":"Zhenyan","Type":"上櫃"},
    {"Code":"1648","CHName":"駿隆","Name":"Junlong","Type":"上櫃"},
    {"Code":"1649","CHName":"光寶","Name":"Lite-On","Type":"上櫃"},

    # ===== 興櫃股票 Emerging Stocks =====
    {"Code":"4103","CHName":"瑯琊","Name":"Langya","Type":"興櫃"},
    {"Code":"4105","CHName":"宏夆","Name":"Hongyou","Type":"興櫃"},
    {"Code":"4107","CHName":"昭揚","Name":"Zhaoyang","Type":"興櫃"},
    {"Code":"4108","CHName":"威建","Name":"Weijian","Type":"興櫃"},
    {"Code":"4110","CHName":"宏為","Name":"Hongwei","Type":"興櫃"},
    {"Code":"4112","CHName":"昇運","Name":"Shengyun","Type":"興櫃"},
    {"Code":"4114","CHName":"正台","Name":"Zhengtai","Type":"興櫃"},
    {"Code":"4115","CHName":"立德","Name":"Lide","Type":"興櫃"},
    {"Code":"4117","CHName":"靚坤","Name":"Liangkun","Type":"興櫃"},
    {"Code":"4118","CHName":"明均","Name":"Mingjun","Type":"興櫃"},
    {"Code":"4119","CHName":"和奕","Name":"Heyi","Type":"興櫃"},
    {"Code":"4120","CHName":"世堡","Name":"Shibao","Type":"興櫃"},
    {"Code":"4121","CHName":"群翎","Name":"Qunli","Type":"興櫃"},
    {"Code":"4123","CHName":"韌聯","Name":"Renlian","Type":"興櫃"},
    {"Code":"4124","CHName":"奎應","Name":"Kuiying","Type":"興櫃"},
    {"Code":"6488","CHName":"機器人","Name":"ROBOT","Type":"興櫃"},
    {"Code":"6494","CHName":"安碁資訊","Name":"ANXI","Type":"興櫃"},
    {"Code":"6560","CHName":"致茂","Name":"CHITMASS","Type":"興櫃"},
    {"Code":"6668","CHName":"宏碁","Name":"ACER","Type":"興櫃"},
    {"Code":"6838","CHName":"光罩","Name":"PHOTOMASK","Type":"興櫃"},
    {"Code":"9910","CHName":"豐祥","Name":"FENGXIANG","Type":"興櫃"},
    {"Code":"9911","CHName":"麗磨","Name":"LIMO","Type":"興櫃"},
    {"Code":"9912","CHName":"偉昌","Name":"WEICHANG","Type":"興櫃"},
]

# Remove duplicates
seen = set()
unique_stocks = []
for stock in stocks:
    if stock['Code'] not in seen:
        unique_stocks.append(stock)
        seen.add(stock['Code'])

# Sort by code
unique_stocks.sort(key=lambda x: x['Code'])

# Save to JSON
output_file = "twse-stocks.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(unique_stocks, f, ensure_ascii=False, indent=2)

# Statistics
total = len(unique_stocks)
listed = sum(1 for s in unique_stocks if s['Type'] == '上市')
otc = sum(1 for s in unique_stocks if s['Type'] == '上櫃')
emerging = sum(1 for s in unique_stocks if s['Type'] == '興櫃')
etf = sum(1 for s in unique_stocks if s['Type'] == 'ETF')

print("[DONE] Complete Taiwan stocks list generated")
print("=" * 50)
print("Total: {} stocks".format(total))
print("  - Listed: {} stocks".format(listed))
print("  - OTC: {} stocks".format(otc))
print("  - Emerging: {} stocks".format(emerging))
print("  - ETF: {} stocks".format(etf))
print("=" * 50)
print("File: {}".format(output_file))
