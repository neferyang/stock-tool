#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從 FinMind API 更新 financial-data-complete.json 的歷史財務數據

設計原則：
  - 正確 API：https://api.finmindtrade.com/api/v4/data
  - FinMind 為唯一資料來源：每個年度全覆蓋（含當年），無完整資料則設為 null
  - 全部為真實數據，無推估、無佔位
  - 單位：營收/淨利/營業利益/FCF = 億元；EPS = 元；比率 = %

資料集與整合方式：
  - 損益表 TaiwanStockFinancialStatements：單季值 → 年度加總
      EPS、Revenue、IncomeAfterTaxes(稅後淨利)、OperatingIncome(營業利益)
  - 資產負債表 TaiwanStockBalanceSheet：年底餘額 → 取 Q4
      Equity(權益)、Liabilities(負債)、TotalAssets(資產總額)
  - 現金流量表 TaiwanStockCashFlowsStatement：累計值 → 取 Q4
      NetCashInflowFromOperatingActivities(營業現金流)、PropertyAndPlantAndEquipment(資本支出)

衍生指標：
  netMargin = 稅後淨利 / 營收 × 100
  operatingMargin = 營業利益 / 營收 × 100
  roe = 稅後淨利 / 年底權益 × 100
  debtRatio = 年底負債 / 年底資產 × 100
  fcf = 營業現金流 + 資本支出（資本支出為負值）
"""

import re
import requests
import json
import time
import sys
import os
from datetime import datetime, timedelta

# dotenv 為選用：本地方便，CI 用環境變數（無 dotenv 不應崩潰）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_URL = "https://api.finmindtrade.com/api/v4/data"
DATA_FILE = "financial-data-complete.json"
TIMEOUT = 25
RATE_DELAY = 0.4
OKU = 1e8  # 億元換算


class FinMindQuotaError(Exception):
    """FinMind額度用盡/被限速(HTTP或回應body的status為402/429)，跟其他錯誤(單一股票
    資料格式異常、網路瞬斷等)分開處理——這種錯誤代表整個額度池已經打滿，繼續對剩下的
    候選股逐一發送必敗請求，等於短時間內狂發錯誤請求，有觸發FinMind IP封鎖的風險。"""
    def __init__(self, status_code, msg):
        self.status_code = status_code
        super().__init__(msg)


class FinMindFetcher:
    def __init__(self):
        self.token = os.getenv('FINMIND_TOKEN', '')
        self.headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
        if not self.token:
            print("⚠️  未設定 FINMIND_TOKEN，資料可能受限")

    def _get(self, dataset, code, start, end):
        params = {"dataset": dataset, "data_id": code, "start_date": start, "end_date": end}
        r = requests.get(API_URL, params=params, headers=self.headers, timeout=TIMEOUT)
        if r.status_code in (402, 429):
            raise FinMindQuotaError(r.status_code, f"{dataset} HTTP {r.status_code}")
        r.raise_for_status()
        d = r.json()
        if d.get('status') in (402, 429):
            raise FinMindQuotaError(d.get('status'), f"{dataset} status {d.get('status')}: {d.get('msg')}")
        if d.get('status') != 200:
            raise RuntimeError(f"{dataset} status {d.get('status')}: {d.get('msg')}")
        return d.get('data', [])

    def fetch_all(self, code, start, end):
        """回傳 (損益表, 資產負債表, 現金流量表) 三組原始資料"""
        income = self._get("TaiwanStockFinancialStatements", code, start, end)
        balance = self._get("TaiwanStockBalanceSheet", code, start, end)
        cashflow = self._get("TaiwanStockCashFlowsStatement", code, start, end)
        return income, balance, cashflow

    @staticmethod
    def _group(rows):
        """rows → { year: { type: [(date, value), ...] } }"""
        g = {}
        for r in rows:
            y = r['date'][:4]
            g.setdefault(y, {}).setdefault(r['type'], []).append((r['date'], r['value']))
        return g

    def compute_annual(self, income, balance, cashflow):
        """整合三表，回傳 { '2024': {eps, revenue, ...}, ... }
        滿4季損益表 → 真實年度數據。
        當年度（進行中，如今年僅公布Q1）不滿4季 → 用現有季數年化推估
        （現有季度加總 ÷ 季數 × 4），標記 isEstimate=True、partialQuarters=
        實際季數，前端需明顯區分避免使用者誤認成正式年報數字。
        過去年度（非當年度）不滿4季 → 視為資料不完整，直接略過（不年化、
        不推估），原因：部分小型/興櫃公司在 FinMind 的申報紀錄本來就不齊全
        或非季報頻率，強行年化會產生失真甚至誇大的數字，不能套用「進行中
        年度」的推估邏輯。
        資產負債表科目本身就是期末餘額，不需年化，直接取最新一期。
        """
        current_year = str(datetime.now().year)
        gi, gb, gc = self._group(income), self._group(balance), self._group(cashflow)
        years = set(gi) | set(gb) | set(gc)
        out = {}

        for y in years:
            it = gi.get(y, {})

            def isum(t):  # 損益表：單季加總
                vals = [v for _, v in it.get(t, [])]
                return sum(vals) if vals else None

            def icount(t):
                return len(it.get(t, []))

            def last(group, t):  # 取最新一期（完整年度為Q4，進行中年度為最新公布季）
                items = sorted(group.get(y, {}).get(t, []))
                return items[-1][1] if items else None

            n_quarters = min(icount('EPS'), icount('Revenue'))
            if n_quarters == 0:
                continue

            is_estimate = n_quarters < 4
            if is_estimate and y != current_year:
                # 過去年度資料本來就不齊全（非當年度進行中），不年化、不當作推估
                continue
            annualize = (4 / n_quarters) if is_estimate else 1

            eps = isum('EPS')
            revenue = isum('Revenue')
            net_income = isum('IncomeAfterTaxes')
            op_income = isum('OperatingIncome')

            equity = last(gb, 'Equity')
            liab = last(gb, 'Liabilities')
            total_assets = last(gb, 'TotalAssets')

            ocf = last(gc, 'NetCashInflowFromOperatingActivities')
            capex = last(gc, 'PropertyAndPlantAndEquipment')

            eps_a = eps * annualize if eps is not None else None
            revenue_a = revenue * annualize if revenue is not None else None
            net_income_a = net_income * annualize if net_income is not None else None
            op_income_a = op_income * annualize if op_income is not None else None
            # 淨利率/營業利益率是比率，分子分母同倍率縮放後不變，直接用原始（未年化）值即可
            fcf_a = (ocf * annualize + capex * annualize) if (ocf is not None and capex is not None) else None

            rec = {
                'eps': round(eps_a, 2) if eps_a is not None else None,
                'epsActual': round(eps, 2) if (is_estimate and eps is not None) else None,
                'revenue': round(revenue_a / OKU, 1) if revenue_a is not None else None,
                'netIncome': round(net_income_a / OKU, 1) if net_income_a is not None else None,
                'operatingIncome': round(op_income_a / OKU, 1) if op_income_a is not None else None,
                'operatingMargin': round(op_income / revenue * 100, 1) if (op_income is not None and revenue) else None,
                'netMargin': round(net_income / revenue * 100, 1) if (net_income is not None and revenue) else None,
                'roe': round(net_income_a / equity * 100, 1) if (net_income_a is not None and equity) else None,
                # ROE 分子是年化淨利，跟淨利率/負債比不同（那兩者未年化，本身已是實際值），
                # 這裡多存一份「未年化」的實際季度ROE，前端可對照顯示，避免推估值被誤認成正式數字
                'roeActual': round(net_income / equity * 100, 1) if (is_estimate and net_income is not None and equity) else None,
                'debtRatio': round(liab / total_assets * 100, 1) if (liab is not None and total_assets) else None,
                'fcf': round(fcf_a / OKU, 1) if fcf_a is not None else None,
                'isEstimate': is_estimate,
                'partialQuarters': n_quarters if is_estimate else None,
            }
            out[y] = rec
        return out


# 前端 data 條目的財務欄位（全覆蓋這些欄位）
FIN_FIELDS = ['eps', 'revenue', 'netIncome', 'operatingIncome',
              'operatingMargin', 'netMargin', 'roe', 'debtRatio', 'fcf']


BATCH_SIZE = 200  # 每支固定3次API呼叫(income/balance/cashflow)，200支=600次，打滿FinMind
# 免費方案 api_request_limit_hour=600 上限，不留額外緩衝。原本160支(480次，留20%緩衝)
# 是為了應付跟auto-expand-stocks.yml(00:23跑，最多300次)撞額度的風險，2026-07-24
# 已改用schedule上的時間緩衝解決(update-financial-data.yml跳過UTC 0、1點兩小時，
# 讓auto-expand到下一次財報更新間隔114分鐘)，不再需要靠壓低BATCH_SIZE留餘裕。
# 每支呼叫次數固定不變，不會有重試造成的額外消耗，打滿600次是安全的。


def _missing_score(stock, current_year):
    """缺值分數：data陣列中沒有真實eps的年份數，越大越優先處理。
    當年度（進行中）即使已抓過推估值，只要還是 isEstimate，代表季數還沒抓滿，
    仍算作缺值，否則抓到Q1推估值後就永久掉出優先序，之後公布的Q2/Q3永遠等不到
    重抓（此為3-4筆/天問題的根因）。
    另：當年度 entry 若根本不存在（像早期收錄、年報齊全但從沒補當年度的股票，如
    2330），也算缺一年——否則這種股票缺值分數恆為0、永遠排在佇列最後，補當年度空位
    的邏輯（update_data_file 只在股票被選進batch後才補）永遠輪不到它，季報追不上。
    另：新上市股票（如7780大研生醫）上市前年度FinMind結構上不可能有資料（MOPS本來就
    沒有申報紀錄，不是抓不到），若跟一般缺值一樣計分，分數會永久偏高、每輪都被選進batch
    卻永遠補不到——用「最早一筆真實資料的年份」當推定上市年下限，更早的年份視為結構性
    缺值不計分；該年份之後才出現的缺值（如小型/興櫃公司申報不齊全）仍正常計分，因為
    那些之後有機會補齊。"""
    score = 0
    has_current = False
    data = stock.get('data', [])
    real_years = [int(e['year']) for e in data
                  if e.get('eps') is not None and str(e.get('year')).isdigit()]
    earliest_real_year = min(real_years) if real_years else None
    for e in data:
        yr_str = str(e.get('year'))
        if yr_str == current_year:
            has_current = True
        if e.get('eps') is None:
            if earliest_real_year is not None and yr_str.isdigit() and int(yr_str) < earliest_real_year:
                continue  # 推定上市前，結構性缺值，不計分
            score += 1
        elif yr_str == current_year and e.get('isEstimate'):
            score += 1
    if not has_current:
        score += 1
    return score


UNSUPPORTED_DATATYPE = '不適用（金融股/ETF/DR）'


def _is_finmind_unsupported(code, stock):
    """ETF(代號00開頭)、中國存託憑證(DR，掛的是海外公司財報)這兩類結構上永遠拿不到任何
    財務資料(不是公司、或財報不在台灣申報體系)，排除候選，避免每天佔滿整批額度、卡死佇列。
    金融保險業(銀行/證券/期貨/保險)不在此列——FinMind的eps/revenue/debtRatio對這類公司
    抓得到，只有netIncome(用不同會計科目申報)抓不到，但_missing_score只看eps，不會因為
    netIncome/roe/netMargin永遠null而被卡住，所以讓它們正常進候選池，抓得到的欄位維持
    更新，抓不到的欄位維持null顯示，不需要特殊排除。"""
    if '-DR' in stock.get('name', '').upper():
        return True
    if re.match(r'^00\d{2,3}$', code):
        return True
    return False


def update_data_file(fetcher):
    with open(DATA_FILE, 'r', encoding='utf-8-sig') as f:
        db = json.load(f)

    stocks = db.get('stocks', {})
    all_codes = list(stocks.keys())

    unsupported_codes = [c for c in all_codes if _is_finmind_unsupported(c, stocks[c])]
    unsupported_set = set(unsupported_codes)

    # 只要這次有真的抓到資料（不管抓到哪一年），就先讓路給其他候選股，等下一輪再排——
    # 否則像新上市股票這種「有幾年結構性缺值、但當年度每次都抓得到」的股票，missing_score
    # 永遠居高不下，會每輪都卡在batch前段班，佔掉本該給其他股票的名額。
    # 只看有沒有實際跑過（lastAttemptAt），跟有沒有抓到資料/抓到哪年無關；額度不足等
    # exception不算「跑過」（見下方迴圈），才能讓被額度擋下的股票下一輪還能盡快重試。
    ATTEMPT_COOLDOWN_HOURS = 20

    def _recently_attempted(s):
        ts = s.get('lastAttemptAt')
        if not ts:
            return False
        try:
            return datetime.now() - datetime.fromisoformat(ts) < timedelta(hours=ATTEMPT_COOLDOWN_HOURS)
        except ValueError:
            return False

    candidate_codes = [c for c in all_codes
                        if c not in unsupported_set and not _recently_attempted(stocks[c])]

    # 標記排除股票的 dataType，只在還沒標記過時才動，避免每次都造成無意義的 git diff
    newly_marked = 0
    for c in unsupported_codes:
        for entry in stocks[c].get('data', []):
            if entry.get('eps') is None and entry.get('dataType') != UNSUPPORTED_DATATYPE:
                entry['dataType'] = UNSUPPORTED_DATATYPE
                newly_marked += 1

    # 優先處理缺值最多的股票；缺值相同時，越久沒更新的越優先。
    # noDataStreak（連續無資料次數）原本用獨立的 tuple 層把「連續多次都抓不到」的個股
    # 降到佇列最後面，但候選池（demoted=0那群）遠大於單次batch(180)、水位永遠夠，
    # 導致降級股永遠輪不到、noDataStreak永遠沒機會清零——等於永久放逐，不是懲罰
    # （2026-07-22 實測：314支demoted股票本月0支被摸過）。
    # 改成扣分併入 missing_score：降級股仍會被排後面，但不是絕對否決，只要missing_score
    # 夠高或last_updated夠舊，還是有機會被排進batch重試、清零noDataStreak。
    # （2026-07-23 改用「門檻+固定扣分」取代原本的min(streak,cap)：候選池裡缺2025的股票
    # missing_score幾乎全部頂格(=6)，min(streak,cap)這種cap越小扣越少的設計，cap調小
    # 反而讓連續失敗股「demote力道變弱」，方向剛好搞反——實測cap=3時扣到6-3=3，cap=2時只
    # 扣到6-2=4，比cap=3還不容易被排到後面。改成streak>=THRESHOLD才觸發，觸發後扣固定
    # PENALTY（要夠大，蓋過同組其他股票的分數差距，才能真的把它們壓到隊尾）。
    NO_DATA_STREAK_THRESHOLD = 2   # 連續失敗幾次後開始降級
    NO_DATA_STREAK_PENALTY = 5     # 降級固定扣分（不是streak本身，避免cap調整方向又搞反）

    # 2026-07-23 光靠扣分還是不夠：候選池裡「缺2025」這組實測426支，扣分後沒被罰的只剩
    # 110支(<batch 160)，缺口一定要從已扣分那組硬補滿——不管streak是2還是8，扣分都封在
    # 同一個固定值，結果變成連續失敗8次的股票照樣每輪陪榜，真正該被排到的「只缺當年度」
    # 那組(如2330，資料源已確認FinMind有、只是排序排不到)永遠插不進來。
    # 改成真的「跳過」：streak>=EXCLUDE_THRESHOLD直接排除出candidate_codes，不進排序也
    # 不進batch，讓路給其他候選股；但不是永久放逐——冷卻COOLDOWN_DAYS天后自動解禁一次，
    # 讓FinMind如果之後補上資料還是抓得到，也避免真的資料源缺漏的股票被永久鎖死查不到。
    EXCLUDE_STREAK_THRESHOLD = 3
    COOLDOWN_DAYS = 7

    def _is_cooling_down(s):
        # 注意：不能用 entry 的 updatedAt 判斷「上次嘗試時間」——完全抓不到真實資料的股票
        # (changed=False那條路)從來不會寫入entry['updatedAt']，這個欄位對它們永遠是None，
        # 會被誤判成「從沒抓過」而永遠不冷卻。改用 stock 層級專門記錄的 lastAttemptAt，
        # 這個欄位不管成功失敗、每次被選進batch處理過就一定會更新。
        streak = s.get('noDataStreak', 0) or 0
        if streak < EXCLUDE_STREAK_THRESHOLD:
            return False
        last_attempt = s.get('lastAttemptAt') or ''
        if not last_attempt:
            return False  # 從沒真的抓過，不算冷卻中
        try:
            last_dt = datetime.fromisoformat(last_attempt)
        except ValueError:
            return False
        return (datetime.now() - last_dt) < timedelta(days=COOLDOWN_DAYS)

    # 前端進度百分比只看「去年」（PREV_YEAR）這個完整年度算不算真實資料，跟這裡缺值分數
    # 算的「任何一年缺值」是兩件事——2026-07-20 實測發現：批次剛好抽到一堆「去年已完整、
    # 只差今年Q1」的股票，佇列雖然真的有在動（更新股票數>0），但前端百分比完全沒感覺在漲。
    # 所以缺「去年」真實資料的股票要排最前面，把這批補完後，才輪到原本缺值分數的排序邏輯。
    PREV_YEAR_STR = str(datetime.now().year - 1)
    CURRENT_YEAR_STR = str(datetime.now().year)

    def _prev_year_missing(s):
        entry = next((e for e in s.get('data', []) if str(e.get('year')) == PREV_YEAR_STR), None)
        return entry is None or entry.get('eps') is None

    def sort_key(code):
        s = stocks[code]
        last_updated = max((e.get('updatedAt') or '') for e in s.get('data', []))
        prev_missing_first = 0 if _prev_year_missing(s) else 1
        streak = s.get('noDataStreak', 0)
        streak_penalty = NO_DATA_STREAK_PENALTY if streak >= NO_DATA_STREAK_THRESHOLD else 0
        score = _missing_score(s, CURRENT_YEAR_STR) - streak_penalty
        return (prev_missing_first, -score, last_updated)

    cooling_codes = [c for c in candidate_codes if _is_cooling_down(stocks[c])]
    active_codes = [c for c in candidate_codes if c not in set(cooling_codes)]

    codes = sorted(active_codes, key=sort_key)[:BATCH_SIZE]
    if len(codes) < BATCH_SIZE:
        # active池不夠湊滿一批才會用到冷卻中的股票（正常情況下active池遠大於BATCH_SIZE，
        # 幾乎不會走到這裡；真的走到，代表候選池整體已經很乾淨，可以讓冷卻股提前解禁）
        codes += sorted(cooling_codes, key=sort_key)[:BATCH_SIZE - len(codes)]

    print(f"\n共 {len(all_codes)} 支（其中 {len(unsupported_codes)} 支金融股/ETF/DR結構上無法從"
          f"FinMind取得，已排除候選；另有 {len(cooling_codes)} 支連續{EXCLUDE_STREAK_THRESHOLD}次"
          f"以上抓不到真實資料，冷卻{COOLDOWN_DAYS}天中，暫不排入），本次處理優先度最高的 "
          f"{len(codes)} 支（缺{PREV_YEAR_STR}年真實資料優先，其餘按缺值最多/最久未更新排序）...\n")

    updated_stocks = 0
    failed = 0
    QUOTA_BACKOFF_SECONDS = 300  # 額度/限速錯誤只backoff重試一次，不做無限重試——排程本身
    # 每小時就會重跑一次，撞到額度上限時整批中止、留給下次排程處理即可，重試太多次沒有
    # 意義還會拖長runtime，只需要避免「明知額度爆了還繼續逐支硬打」這個IP封鎖風險。
    quota_backoff_used = False

    current_year = datetime.now().year

    for i, code in enumerate(codes, 1):
        stock = stocks[code]
        data_arr = stock.get('data', [])
        years = [str(d.get('year')) for d in data_arr if str(d.get('year')).isdigit()]
        if not years:
            continue

        # 補上當年度(進行中)的空位，讓下面的迴圈能寫入推估值；沒有就不會出現在圖表/表格裡
        if str(current_year) not in years:
            data_arr.append({
                'year': str(current_year), 'eps': None, 'revenue': None, 'netIncome': None,
                'operatingIncome': None, 'operatingMargin': None, 'fcf': None, 'roe': None,
                'netMargin': None, 'debtRatio': None, 'updatedAt': None, 'source': None,
                'isEstimate': False, 'dataType': '待更新',
            })
            stock['data'] = data_arr
            years.append(str(current_year))

        print(f"[{i}/{len(codes)}] {code} {stock.get('name','')}...", end=" ", flush=True)
        # lastAttemptAt只在「真的完成一次嘗試」時才寫入(成功、或非額度的真實失敗)——
        # 額度/限速(FinMindQuotaError)不算，才能讓被額度擋下的股票下一輪馬上重試，不會
        # 被誤判成「跑過了」而白白等20小時(_recently_attempted)或算進noDataStreak的
        # 冷卻判斷(_is_cooling_down)。

        try:
            yrs = [int(y) for y in years]
            start, end = f"{min(yrs)}-01-01", f"{max(max(yrs), current_year)}-12-31"
            try:
                income, balance, cashflow = fetcher.fetch_all(code, start, end)
            except FinMindQuotaError as qe:
                if quota_backoff_used:
                    print(f"❌ 重試後仍額度/限速錯誤(HTTP {qe.status_code})，"
                          f"中止本次批次剩餘{len(codes)-i+1}支(含這支)，留待下次排程")
                    break
                print(f"\n⚠️  額度/限速錯誤(HTTP {qe.status_code})，暫停"
                      f"{QUOTA_BACKOFF_SECONDS//60}分鐘後重試一次...")
                time.sleep(QUOTA_BACKOFF_SECONDS)
                quota_backoff_used = True
                try:
                    income, balance, cashflow = fetcher.fetch_all(code, start, end)
                except FinMindQuotaError as qe2:
                    print(f"❌ 重試後仍額度/限速錯誤(HTTP {qe2.status_code})，"
                          f"中止本次批次剩餘{len(codes)-i+1}支(含這支)，留待下次排程")
                    break
            annual = fetcher.compute_annual(income, balance, cashflow)

            now = datetime.now().isoformat()
            changed = False
            for entry in data_arr:
                yr = str(entry.get('year'))
                src = annual.get(yr)
                if src:
                    # 用 FinMind 真實值取代所有財務欄位（不滿4季時 compute_annual 已年化並標記推估）
                    for k in FIN_FIELDS:
                        entry[k] = src.get(k)
                    entry['updatedAt'] = now
                    entry['source'] = 'FinMind'
                    entry['isEstimate'] = src.get('isEstimate', False)
                    entry['partialQuarters'] = src.get('partialQuarters')
                    entry['epsActual'] = src.get('epsActual')
                    entry['roeActual'] = src.get('roeActual')
                    entry['dataType'] = '推估' if src.get('isEstimate') else '真實'
                    changed = True
                elif entry.get('eps') is None:
                    # 該年度本來就無資料 → 標記為無資料（不影響已有真實值的欄位，因為本來就是None）
                    entry['dataType'] = '無資料'
                # 若該年度annual缺漏但entry已有真實值 → 保留原值，不清空(避免暫時性API缺漏造成資料退步)

            # noDataStreak 該不該歸零，要看「去年真實資料」有沒有拿到，不是「任何一年有沒有變動」——
            # 否則FinMind只有當年度(進行中)資料、去年以前完全空白的股票(通常是近期才公開發行/興櫃，
            # FinMind覆蓋範圍從掛牌後才開始)，每次都會抓到當年度Q1而觸發changed=True，streak永遠
            # 被打回0、missing_score永遠頂格最高分，變成永久最高優先權，反而把它們的batch名額
            # 佔死、擠掉其他候選股，去年真實資料缺口永遠補不上也永遠看不出來（2026-07-23實測發現）。
            prev_year_str = str(current_year - 1)
            got_real_prev = bool(annual.get(prev_year_str)) and not annual[prev_year_str].get('isEstimate')

            stock['lastAttemptAt'] = now

            if changed:
                updated_stocks += 1
                got = [y for y in years if y in annual]
                if got_real_prev:
                    stock['noDataStreak'] = 0
                    print(f"✅ {','.join(sorted(got, reverse=True))}")
                else:
                    stock['noDataStreak'] = stock.get('noDataStreak', 0) + 1
                    print(f"✅ {','.join(sorted(got, reverse=True))}（但無{prev_year_str}真實資料，"
                          f"連續{stock['noDataStreak']}次）")
            else:
                stock['noDataStreak'] = stock.get('noDataStreak', 0) + 1
                print(f"－ 無真實資料（連續{stock['noDataStreak']}次）")

        except Exception as e:
            failed += 1
            stock['lastAttemptAt'] = datetime.now().isoformat()  # 真的失敗(非額度)，算一次嘗試
            print(f"❌ {e}")

        time.sleep(RATE_DELAY)

    db['updatedAt'] = datetime.now().isoformat()
    db['source'] = 'FinMind API'

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"完成！更新股票: {updated_stocks}, 失敗: {failed}"
          f"（未處理: {len(candidate_codes)-len(codes)}支留待下次，另排除 {len(unsupported_codes)} 支金融股/ETF/DR，"
          f"本次新標記 {newly_marked} 筆）")
    print(f"{'='*60}")


def main():
    print("=" * 60)
    print("FinMind 財務數據更新（全覆蓋 financial-data-complete.json）")
    print("=" * 60)
    fetcher = FinMindFetcher()
    # 無 token 直接中止：FinMind 無 token 會全數擋下，靜默跑完會誤判為成功
    if not fetcher.token:
        print("❌ 未設定 FINMIND_TOKEN，中止（請確認 GitHub Secrets 已設定 FINMIND_TOKEN）")
        return False
    update_data_file(fetcher)
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
