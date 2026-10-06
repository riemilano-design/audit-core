# -*- coding: utf-8 -*-
"""XBRL 探り 1 本目(使い捨て)。予測 docs/XBRL_PROBE_PREDICTION_2026-10-06.md §1 の設計をそのまま機械にした。
- 材料: 会社自身の MD&A textBlock。LLM は使わない。
- 数の Claim: 正規表現で抜く(§1.2)。数えない規則は EXCLUDE_*。
- 文章の Claim: 方向の語・状態の語の一覧(DIRECTION_WORDS / STATE_WORDS)で抜く(予測では「人が抜く」だったが、語の一覧を先に固定して機械で抜く。結果に明記)。
- 束縛: 主語 → 要素名の対応表(SUBJECTS。実データを見る前に書いた)と、値の一致(decimals を既定の許容幅)。
- 出力: 1 本の JSON。鍵は出力に書かない。
"""
import os, sys, re, json, zipfile, io, html, math, unicodedata, urllib.request, urllib.parse
from html.parser import HTMLParser

API = "https://api.edinet-fsa.go.jp/api/v2/"
KEY = os.environ.get("EDINET_API_KEY")  # 取りに行くときだけ要る(検査の import では要らない)
RUN = os.environ.get("PROBE_RUN", "A")  # A = 封じた主語表のまま / B = 実データを読んだ後に主語表を広げた(結果に明記)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xbrl")

# ---------- 主語 → 要素名の部分文字列(実データを見る前に固定) ----------
SUBJECTS = [
    ("親会社株主に帰属する当期純利益", ["ProfitLossAttributableToOwnersOfParent"]),
    ("親会社の所有者に帰属する当期利益", ["ProfitLossAttributableToOwnersOfParent"]),
    ("当期純利益", ["ProfitLossAttributableToOwnersOfParent", "ProfitLoss"]),
    ("当期利益", ["ProfitLossAttributableToOwnersOfParent", "ProfitLoss"]),
    ("純利益", ["ProfitLossAttributableToOwnersOfParent", "ProfitLoss"]),
    ("税引前当期純利益", ["IncomeBeforeIncomeTaxes"]),
    ("税引前利益", ["IncomeBeforeIncomeTaxes", "ProfitLossBeforeTax"]),
    ("営業利益", ["OperatingIncome", "OperatingProfit"]),
    ("営業損失", ["OperatingIncome", "OperatingProfit"]),
    ("経常利益", ["OrdinaryIncome", "OrdinaryProfit"]),
    ("経常損失", ["OrdinaryIncome", "OrdinaryProfit"]),
    ("売上総利益", ["GrossProfit"]),
    ("売上収益", ["Revenue", "NetSales"]),
    ("営業収益", ["OperatingRevenue", "NetSales", "Revenue"]),
    ("売上高", ["NetSales", "Revenue"]),
    ("総資産", ["Assets", "TotalAssets"]),
    ("資産合計", ["Assets", "TotalAssets"]),
    ("純資産", ["NetAssets", "Equity"]),
    ("自己資本比率", ["EquityToAssetRatio", "CapitalAdequacyRatio"]),
    ("自己資本", ["Equity", "NetAssets"]),
    ("有利子負債", ["InterestBearing"]),
    ("負債合計", ["Liabilities"]),
    ("負債", ["Liabilities"]),
    ("現金及び現金同等物", ["CashAndCashEquivalents"]),
    ("営業活動によるキャッシュ・フロー", ["OperatingActivities"]),
    ("投資活動によるキャッシュ・フロー", ["InvestingActivities"]),
    ("財務活動によるキャッシュ・フロー", ["FinancingActivities"]),
    ("設備投資", ["CapitalExpenditure", "IncreaseInPropertyPlantAndEquipment"]),
    ("研究開発費", ["ResearchAndDevelopment"]),
    ("減価償却費", ["DepreciationAndAmortization", "Depreciation"]),
    ("従業員数", ["NumberOfEmployees"]),
    ("従業員", ["NumberOfEmployees"]),
    ("受注高", ["OrdersReceived"]),
    ("受注残高", ["OrderBacklog"]),
    ("販売費及び一般管理費", ["SellingGeneralAndAdministrativeExpenses"]),
    ("1株当たり当期純利益", ["BasicEarningsLossPerShare"]),
    ("１株当たり当期純利益", ["BasicEarningsLossPerShare"]),
    ("1株当たり配当", ["DividendPaidPerShare"]),
    ("配当", ["DividendPaidPerShare"]),
]
if RUN == "B":
    # 実データ(S100Z4Q1 の MD&A)を読んだ後に足した主語。Run A には入れない。
    SUBJECTS = [
        ("純資産合計", ["NetAssets"]), ("資産合計", ["Assets"]), ("負債合計", ["Liabilities"]),
        ("税金等調整前当期純利益", ["IncomeBeforeIncomeTaxes"]),
        ("受取手形及び売掛金", ["NotesAndAccountsReceivableTrade", "NotesAndAccountsReceivableTradeAndContractAssets"]),
        ("投資有価証券", ["InvestmentSecurities"]), ("退職給付に係る資産", ["RetirementBenefitAsset"]), ("退職給付に係る調整累計額", ["RemeasurementsOfDefinedBenefitPlans"]),
        ("現金及び預金", ["CashAndDeposits"]), ("契約資産", ["ContractAssets"]), ("契約負債", ["ContractLiabilities"]),
        ("完成業務補償引当金", ["ProvisionForWarranties", "ProvisionForLossOnOrders"]), ("繰延税金負債", ["DeferredTaxLiabilities"]),
        ("業務未払金", ["AccountsPayableOther", "AccountsPayable"]), ("未払法人税等", ["IncomeTaxesPayable"]), ("長期借入金の返済", ["RepaymentsOfLongTermLoansPayable", "RepaymentsOfLongTermBorrowings"]),
        ("長期借入金", ["LongTermLoansPayable", "LongTermBorrowings"]), ("その他有価証券評価差額金", ["ValuationDifferenceOnAvailableForSaleSecurities"]),
        ("売上債権", ["DecreaseIncreaseInNotesAndAccountsReceivableTrade", "DecreaseIncreaseInTradeReceivables"]),
        ("仕入債務", ["IncreaseDecreaseInNotesAndAccountsPayableTrade", "IncreaseDecreaseInTradePayables"]),
        ("営業活動の結果獲得した資金", ["NetCashProvidedByUsedInOperatingActivities"]), ("営業活動の結果使用した資金", ["NetCashProvidedByUsedInOperatingActivities"]),
        ("投資活動の結果使用した資金", ["NetCashProvidedByUsedInInvestingActivities"]), ("投資活動の結果獲得した資金", ["NetCashProvidedByUsedInInvestingActivities"]),
        ("財務活動の結果使用した資金", ["NetCashProvidedByUsedInFinancingActivities"]), ("財務活動の結果獲得した資金", ["NetCashProvidedByUsedInFinancingActivities"]),
        ("有形固定資産の取得による支出", ["PurchaseOfPropertyPlantAndEquipment"]), ("無形固定資産の取得による支出", ["PurchaseOfIntangibleAssets"]),
        ("配当金の支払額", ["DividendsPaid"]), ("剰余金の配当", ["DividendsFromSurplus"]), ("法人税等の支払額", ["IncomeTaxesPaid"]),
        ("株主資本利益率", ["RateOfReturnOnEquity"]), ("現金及び現金同等物の期末残高", ["CashAndCashEquivalents"]),
        ("減価償却費", ["DepreciationAndAmortizationOpeCF", "DepreciationAndAmortization"]),
    ] + SUBJECTS

DIRECTION_WORDS = {
    "増収": +1, "増益": +1, "増加": +1, "増え": +1, "上回": +1, "伸び": +1, "増大": +1, "拡大": +1, "改善": +1,
    "減収": -1, "減益": -1, "減少": -1, "減り": -1, "下回": -1, "縮小": -1, "悪化": -1, "低下": -1,
}
STATE_WORDS = ["堅調", "好調", "底堅", "厳しい", "低調", "回復", "軟調", "横ばい", "順調", "不透明", "持ち直し", "足踏み", "減速", "加速"]
PROFIT_SUBJECTS = ("利益", "損失")

UNIT_SCALE = {"百万円": 1e6, "千円": 1e3, "億円": 1e8, "兆円": 1e12, "円": 1}
# 文は NFKC で正規化してから当てる(全角数字・全角 % を半角に。道具の直し P-1)
NUM_RE = re.compile(r"(?<![\d.,])(△|▲|－|-|マイナス)?\s*(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?\s*(百万円|千円|億円|兆円|円|％|%|ポイント|名|人|店舗|店|件|社|倍|台|千株|株|トン|kl|ｋｌ)")
# 漢数字混じりの金額(380億6千4百万円 / 3億円 / 9千3百万円 / 26億5百万円)。道具の直し P-1(実データで初めて見た表記)
AMOUNT_JP_RE = re.compile(r"(?<![\d.,])(△|▲|－|-|マイナス)?\s*(?:(\d+(?:\.\d+)?)兆)?(?:(\d+(?:\.\d+)?)億)?(?:(\d+)千)?(?:(\d+)百)?(?:(\d+)?(万))?円")
EXCLUDE_AFTER = re.compile(r"^(年|月|日|期|頁|ページ|四半期|号|条|項|回目)")
EXCLUDE_CONTEXT = re.compile(r"(第\s*\d+\s*四半期|\d{4}年\d{1,2}月|\d{1,2}月\d{1,2}日|令和\s*\d+|平成\s*\d+|※\s*\d|注\s*\d)")
PCT_DIR_RE = re.compile(r"(前年同期比|前期比|前連結会計年度比|前年度比|前年比)\s*(\d+(?:\.\d+)?)\s*(％|%)\s*(増|減)|(\d+(?:\.\d+)?)\s*(％|%)\s*(増|減|増加|減少)")
# 「前連結会計年度比 106.0%」「(同 102.9%)」= 当期 / 前期 × 100 の比(道具の直し P-2。実データで初めて見た形)
PCT_RATIO_RE = re.compile(r"(前連結会計年度比|前年同期比|前期比|前年度比|前年比|同)\s*(\d+(?:\.\d+)?)\s*(％|%)(?!\s*(増|減))")


def iter_numbers(s):
    """文の中の数を位置順に (start, end, 値, 単位, 主張の精度) で返す。漢数字混じりの金額は円に直し、精度は書かれた最小の位。"""
    return sorted(_iter_numbers(s), key=lambda t: t[0])


def _iter_numbers(s):
    taken = []
    for m in AMOUNT_JP_RE.finditer(s):
        if not any(m.group(i) for i in (2, 3, 4, 5, 6)):
            continue
        big = bool(m.group(2) or m.group(3) or m.group(7))   # 兆・億・万 が在れば 千・百 は「千万」「百万」
        mults = {2: 1e12, 3: 1e8, 4: 1e7 if big else 1e3, 5: 1e6 if big else 1e2, 6: 1e4}
        yen = 0.0; prec = None
        for i in (2, 3, 4, 5, 6):
            if m.group(i):
                yen += float(m.group(i)) * mults[i]; prec = mults[i]
        if m.group(7) and not m.group(6) and prec is None:
            continue
        sign = -1 if m.group(1) else 1
        taken.append((m.start(), m.end()))
        yield m.start(), m.end(), sign * yen, "円", prec
    for m in NUM_RE.finditer(s):
        if any(a <= m.start() < b for a, b in taken):
            continue
        sign = -1 if m.group(1) else 1
        num = float(m.group(2).replace(",", "") + (m.group(3) or ""))
        unit = m.group(4)
        yield m.start(), m.end(), sign * num, unit, (UNIT_SCALE.get(unit) or 1.0)


def api(path, **params):
    params["Subscription-Key"] = KEY
    url = API + path + "?" + urllib.parse.urlencode(params)
    return urllib.request.urlopen(url, timeout=120).read()


class Stripper(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, d): self.parts.append(d)
    def handle_starttag(self, tag, attrs):
        if tag in ("p", "br", "div", "tr", "li", "h1", "h2", "h3", "h4", "td"): self.parts.append("\n" if tag != "td" else " ")
    def text(self): return re.sub(r"[ \t　]+", " ", "".join(self.parts))


def strip_html(s):
    p = Stripper(); p.feed(html.unescape(s)); return p.text()


# ---------- インスタンスの読み込み(.xbrl があればそれ、無ければ iXBRL の htm) ----------
def load_instance(zbytes):
    z = zipfile.ZipFile(io.BytesIO(zbytes))
    names = z.namelist()
    xbrl = [n for n in names if n.startswith("XBRL/PublicDoc/") and n.endswith(".xbrl")]
    htm = [n for n in names if n.startswith("XBRL/PublicDoc/") and n.endswith(".htm")]
    facts, contexts, textblocks = [], {}, {}
    src = None
    if xbrl:
        src = xbrl[0]
        raw = z.read(src).decode("utf-8")
        ns = dict(re.findall(r'xmlns:([A-Za-z0-9_\-]+)="([^"]+)"', raw))
        uri2pre = {v: k for k, v in ns.items()}
        import xml.etree.ElementTree as ET
        root = ET.fromstring(raw)
        XBRLI = "{http://www.xbrl.org/2003/instance}"
        for c in root.iter(XBRLI + "context"):
            cid = c.get("id"); per = c.find(XBRLI + "period")
            inst = per.find(XBRLI + "instant"); st = per.find(XBRLI + "startDate"); en = per.find(XBRLI + "endDate")
            members = [m.text for m in c.iter() if m.tag.endswith("explicitMember")]
            contexts[cid] = {"instant": inst.text if inst is not None else None, "start": st.text if st is not None else None,
                             "end": en.text if en is not None else None, "members": members}
        for el in root:
            tag = el.tag
            if not tag.startswith("{"): continue
            uri, local = tag[1:].split("}")
            pre = uri2pre.get(uri)
            if pre in (None, "xbrli", "link", "xlink"): continue
            name = f"{pre}:{local}"
            cref = el.get("contextRef")
            if cref is None: continue
            txt = (el.text or "")
            if local.endswith("TextBlock"):
                textblocks[name] = textblocks.get(name) or txt
                continue
            dec = el.get("decimals"); unit = el.get("unitRef")
            v = txt.strip()
            if unit and re.fullmatch(r"-?\d+(\.\d+)?", v):
                facts.append({"name": name, "context": cref, "unit": unit, "decimals": dec, "value": float(v)})
    else:
        # iXBRL fallback(簡易)
        src = ",".join(htm[:3])
        for n in htm:
            raw = z.read(n).decode("utf-8", "ignore")
            for m in re.finditer(r'<ix:nonFraction([^>]*)>(.*?)</ix:nonFraction>', raw, re.S):
                a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
                v = re.sub(r"<[^>]+>", "", m.group(2)).replace(",", "").strip()
                if not re.fullmatch(r"-?\d+(\.\d+)?", v or ""): continue
                val = float(v) * (10 ** int(a.get("scale", "0") or 0))
                if a.get("sign") == "-": val = -val
                facts.append({"name": a.get("name"), "context": a.get("contextRef"), "unit": a.get("unitRef"), "decimals": a.get("decimals"), "value": val})
            for m in re.finditer(r'<ix:nonNumeric([^>]*name="([^"]*TextBlock)"[^>]*)>(.*?)</ix:nonNumeric>', raw, re.S):
                textblocks[m.group(2)] = textblocks.get(m.group(2)) or m.group(3)
            for m in re.finditer(r'<xbrli:context id="([^"]+)">(.*?)</xbrli:context>', raw, re.S):
                body = m.group(2)
                def g(t):
                    mm = re.search(rf"<xbrli:{t}>([^<]+)<", body); return mm.group(1) if mm else None
                contexts[m.group(1)] = {"instant": g("instant"), "start": g("startDate"), "end": g("endDate"),
                                        "members": re.findall(r"explicitMember[^>]*>([^<]+)<", body)}
    return {"source": src, "facts": facts, "contexts": contexts, "textblocks": textblocks, "names": names}


def is_consolidated(cid):
    return not any("NonConsolidated" in m for m in (cid or "")) and "NonConsolidated" not in (cid or "")


def plain_context(cid, contexts):
    c = contexts.get(cid) or {}
    return not c.get("members") and "NonConsolidated" not in cid


def tol_of(fact, claim_scale):
    d = fact.get("decimals")
    try:
        if d is not None and d not in ("INF",):
            return max(0.5 * (10 ** (-int(d))), 0.5 * claim_scale)
    except ValueError:
        pass
    return 0.5 * claim_scale


def match_value(fact_value, target, unit):
    """値の一致の仕方を返す(None = 不一致)。
    round    : 四捨五入(|差| ≤ 単位/2。decimals の既定)
    truncate : 切り捨て(0 ≤ fact − claim < 単位。有報の本文は百万円未満切捨てが普通 ― 道具の直し P-4。X-1 の「文章側の丸めは人が承認」に当たる)
    abs      : 符号を落として一致(CF の支出・配当・減少額は本文で絶対値 ― 道具の直し P-5)
    """
    for sign_mode, fv in (("", fact_value), ("abs", abs(fact_value))):
        t = abs(target) if sign_mode else target
        if abs(fv - t) <= unit / 2:
            return (sign_mode + "+round").strip("+")
        if 0 <= fv - t < unit:
            return (sign_mode + "+truncate").strip("+")
    return None


def subject_of(sentence, pos):
    """数の直前(同じ文)でいちばん近い主語。終わりの位置が最も右のものを取り、同じなら長い語(「純資産合計」>「資産合計」)。道具の直し P-3。"""
    head = sentence[:pos]
    best = None
    for word, elems in SUBJECTS:
        i = head.rfind(word)
        if i < 0: continue
        end = i + len(word)
        if best is None or end > best[0] or (end == best[0] and len(word) > len(best[1])):
            best = (end, word, elems)
    return (best[1], best[2]) if best else (None, None)


def facts_for(elems, facts, contexts, want_ctx=None):
    """要素名の照合: まず局所名の完全一致(と Summary 版)、無ければ部分一致。道具の直し P-3(「資産合計」が NetAssets に当たっていた)。"""
    exact, loose = [], []
    for f in facts:
        local = f["name"].split(":")[-1]
        if not plain_context(f["context"], contexts): continue
        if want_ctx and not f["context"].startswith(want_ctx): continue
        if any(local == e or local == e + "SummaryOfBusinessResults" or local == e.replace("Income", "IncomeLoss") + "SummaryOfBusinessResults" for e in elems):
            exact.append(f)
        elif any(e.lower() in local.lower() for e in elems):
            loose.append(f)
    return exact or loose


def main(date, pick_index=0):
    os.makedirs(OUT, exist_ok=True)
    lst = json.loads(api("documents.json", date=date, type=2).decode("utf-8"))
    allc = sorted([d for d in lst.get("results", []) if d.get("docTypeCode") == "120" and d.get("xbrlFlag") == "1"], key=lambda d: d["docID"])
    # 投資信託の有報は連結財務諸表を持たない(規則「連結財務諸表があり」の安い前段。本判定は下の jppfs の連結 fact で行う)
    cands = [d for d in allc if "投資信託" not in (d.get("docDescription") or "")]
    print(f"[{date}] 有報(120,xbrl) {len(allc)} 件、うち投資信託を除く {len(cands)} 件")
    if not cands:
        return 2
    tried = []
    for d in cands:
        zb = api(f"documents/{d['docID']}", type=1)
        inst = load_instance(zb)
        cons = [f for f in inst["facts"] if f["name"].startswith("jppfs") and plain_context(f["context"], inst["contexts"])]
        tried.append({"docID": d["docID"], "filer": d.get("filerName"), "consolidated_jppfs_facts": len(cons), "facts": len(inst["facts"])})
        if cons:
            chosen = d; break
    else:
        print("no consolidated candidate", tried); return 3
    open(os.path.join(OUT, f"{chosen['docID']}.zip"), "wb").write(zb)
    facts, contexts, tbs = inst["facts"], inst["contexts"], inst["textblocks"]
    # MD&A textBlock
    mdna_name = next((n for n in tbs if "ManagementAnalysis" in n and n.endswith("TextBlock")), None)
    if mdna_name is None:
        mdna_name = next((n for n in tbs if "AnalysisOfFinancialPosition" in n or "OverviewOfBusinessResults" in n), None)
    text = strip_html(tbs[mdna_name]) if mdna_name else ""
    sentences = [unicodedata.normalize("NFKC", s.strip()) for s in re.split(r"(?<=。)|\n", text) if s and s.strip()]
    # ---------- 数の Claim ----------
    num_claims = []
    class _M:  # 旧コードの m.start()/m.end() の器
        def __init__(self, a, b): self._a, self._b = a, b
        def start(self): return self._a
        def end(self): return self._b
    for si, s in enumerate(sentences):
        for (a, b, signed, unit, prec) in iter_numbers(s):
            m = _M(a, b)
            after = s[m.end():m.end() + 3]
            around = s[max(0, m.start() - 12):m.end() + 4]
            if EXCLUDE_AFTER.match(after) or EXCLUDE_CONTEXT.search(around):
                continue
            sign = -1 if signed < 0 else 1
            num = abs(signed)
            subj, elems = subject_of(s, m.start())
            claim = {"id": f"N{len(num_claims)+1:03d}", "sentence": si, "span": s[max(0, m.start()-30):m.end()+10], "value": sign * num, "unit": unit,
                     "subject": subj, "form": None, "pointer": None, "bound": False, "reason": None, "result": None, "recomputed": None}
            # 派生(前年同期比 x% 増減)か
            pm = PCT_DIR_RE.search(s[max(0, m.start()-25):m.end()+6]) if unit in ("％", "%") else None
            pr = PCT_RATIO_RE.search(s[max(0, m.start()-12):m.end()+3]) if unit in ("％", "%") and not pm else None
            if unit in ("％", "%") and pr:
                # 比(当期 / 前期 × 100)。道具の直し P-2
                claim["form"] = "derived_value"
                if subj:
                    cur = [f for f in facts_for(elems, facts, contexts) if f["context"].startswith("CurrentYear")]
                    pri = [f for f in facts_for(elems, facts, contexts) if f["context"].startswith("Prior1Year")]
                    pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
                    if pairs:
                        c, p = pairs[0]
                        claim["pointer"] = [f"xbrl:{c['name']}@{c['context']}", f"xbrl:{p['name']}@{p['context']}", "formula:cur/prior*100"]
                        claim["bound"] = True
                        if p["value"] != 0:
                            ratio = c["value"] / p["value"] * 100
                            claim["recomputed"] = round(ratio, 2)
                            claim["result"] = "GROUNDED" if abs(ratio - num) <= 0.15 else "VALUE_MISMATCH"
                        else:
                            claim["result"] = "UNVERIFIABLE"; claim["reason"] = "prior is 0"
                    else:
                        claim["reason"] = "no_element"
                else:
                    claim["reason"] = "no_subject"
            elif unit in ("％", "%") and pm and (pm.group(4) or pm.group(7)):
                claim["form"] = "derived_value"
                sgn = 1 if (pm.group(4) or pm.group(7)) in ("増", "増加") else -1
                claim["value"] = sgn * num
                if subj:
                    cur = [f for f in facts_for(elems, facts, contexts) if f["context"].startswith("CurrentYear")]
                    pri = [f for f in facts_for(elems, facts, contexts) if f["context"].startswith("Prior1Year")]
                    pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
                    if pairs:
                        c, p = pairs[0]
                        claim["pointer"] = [f"xbrl:{c['name']}@{c['context']}", f"xbrl:{p['name']}@{p['context']}"]
                        claim["bound"] = True
                        if p["value"] != 0:
                            pct = (c["value"] - p["value"]) / abs(p["value"]) * 100
                            claim["recomputed"] = round(pct, 2)
                            claim["result"] = "GROUNDED" if abs(pct - claim["value"]) <= 0.15 else "VALUE_MISMATCH"
                        else:
                            claim["result"] = "UNVERIFIABLE"; claim["reason"] = "prior is 0"
                    else:
                        claim["reason"] = "no_element"
                else:
                    claim["reason"] = "no_subject"
            elif unit in UNIT_SCALE:
                claim["form"] = "direct_value"
                scale = prec if unit == "円" else UNIT_SCALE[unit]   # 漢数字混じりは値が円・精度が書かれた最小の位
                target = sign * num * (1.0 if unit == "円" else UNIT_SCALE[unit])
                pool = facts_for(elems, facts, contexts) if subj else [f for f in facts if plain_context(f["context"], contexts)]
                pool = [f for f in pool if f["unit"] and f["unit"].upper().startswith("JPY")]
                is_diff = bool(re.search(r"(増加|減少|増|減)", s[m.end():m.end() + 4])) or bool(re.search(r"(増加額|減少額|比べて)", s[max(0, m.start() - 25):m.start()]))
                hits = [(f, match_value(f["value"], target, scale)) for f in pool]
                hits = [(f, how) for f, how in hits if how]
                if hits and not (is_diff and subj):
                    fams = sorted({f["name"] for f, _ in hits})
                    if subj or len(fams) == 1:
                        f, how = hits[0]
                        claim["pointer"] = f"xbrl:{f['name']}@{f['context']}"; claim["bound"] = True; claim["result"] = "GROUNDED"
                        claim["recomputed"] = f["value"]; claim["match"] = how
                        if not subj: claim["reason"] = "value_only(no subject)"
                    else:
                        claim["reason"] = f"ambiguous({len(fams)} elements)"
                elif subj:
                    # 差額(「前連結会計年度末と比べて X 増加」= 当期 − 前期 / 「前連結会計年度は X 増加」= 前期 − 前々期。道具の直し P-6)
                    fs = facts_for(elems, facts, contexts)
                    fs = [f for f in fs if f["unit"] and f["unit"].upper().startswith("JPY")]
                    by = {}
                    for f in fs:
                        by.setdefault(f["name"], {})[f["context"]] = f
                    found = None
                    prev_year_phrase = "前連結会計年度は" in s[max(0, m.start() - 15):m.start()]
                    for name, ctxs in by.items():
                        def ctx(prefix):
                            return next((v for k, v in ctxs.items() if k.startswith(prefix)), None)
                        pairs = [("Prior1Year", "Prior2Year")] if prev_year_phrase else [("CurrentYear", "Prior1Year")]
                        for a, b in pairs:
                            fa, fb = ctx(a), ctx(b)
                            if fa and fb:
                                how = match_value(fa["value"] - fb["value"], target, scale)
                                if how:
                                    found = (fa, fb, how); break
                        if found: break
                    if found:
                        fa, fb, how = found
                        claim["form"] = "derived_value"; claim["pointer"] = [f"xbrl:{fa['name']}@{fa['context']}", f"xbrl:{fb['name']}@{fb['context']}", "formula:a-b"]
                        claim["bound"] = True; claim["result"] = "GROUNDED"; claim["recomputed"] = fa["value"] - fb["value"]; claim["match"] = how
                    elif hits:
                        f, how = hits[0]
                        claim["pointer"] = f"xbrl:{f['name']}@{f['context']}"; claim["bound"] = True; claim["result"] = "GROUNDED"
                        claim["recomputed"] = f["value"]; claim["match"] = how; claim["reason"] = "diff phrase but value matched a fact"
                    else:
                        cur = [f for f in fs if f["context"].startswith("CurrentYear")]
                        if cur:
                            claim["pointer"] = f"xbrl:{cur[0]['name']}@{cur[0]['context']}"; claim["bound"] = True
                            claim["result"] = "VALUE_MISMATCH"; claim["recomputed"] = cur[0]["value"]; claim["reason"] = "value differs(segment/other period?)"
                        else:
                            claim["reason"] = "no_element"
                else:
                    claim["reason"] = "no_element"
            elif unit in ("％", "%", "ポイント"):
                claim["form"] = "direct_value"
                # 比率の fact(unit が pure)を持つ主語なら当てる(自己資本比率・ROE 等。道具の直し P-7)
                if subj and any((f["unit"] or "").lower().startswith("pure") for f in facts_for(elems, facts, contexts)):
                    cur = [f for f in facts_for(elems, facts, contexts) if f["context"].startswith("CurrentYear") and (f["unit"] or "").lower().startswith("pure")]
                    if cur:
                        fv = cur[0]["value"]; fvp = fv * 100 if abs(fv) <= 1.5 else fv
                        claim["pointer"] = f"xbrl:{cur[0]['name']}@{cur[0]['context']}"; claim["bound"] = True; claim["recomputed"] = round(fvp, 2)
                        claim["result"] = "GROUNDED" if abs(fvp - num) <= 0.15 else "VALUE_MISMATCH"
                    else:
                        claim["reason"] = "no_element"
                else:
                    claim["reason"] = "no_element(ratio without fact)" if subj else "no_subject"
            elif unit in ("名", "人"):
                claim["form"] = "direct_value"
                cur = [f for f in facts_for(["NumberOfEmployees"], facts, contexts) if f["context"].startswith("CurrentYear")]
                if subj and elems == ["NumberOfEmployees"] and cur:
                    hit = [f for f in cur if abs(f["value"] - num) <= 0.5]
                    claim["pointer"] = f"xbrl:{(hit or cur)[0]['name']}@{(hit or cur)[0]['context']}"; claim["bound"] = True
                    claim["result"] = "GROUNDED" if hit else "VALUE_MISMATCH"; claim["recomputed"] = (hit or cur)[0]["value"]
                else:
                    claim["reason"] = "no_element"
            else:
                claim["form"] = "direct_value"; claim["reason"] = "no_element(unit not in XBRL)"
            num_claims.append(claim)
    # ---------- 文章の Claim ----------
    text_claims = []
    for si, s in enumerate(sentences):
        if NUM_RE.search(s): pass  # 数を含む文にも方向の語は在りうる
        for w, sg in DIRECTION_WORDS.items():
            for m in re.finditer(w, s):
                subj, elems = subject_of(s, m.start())
                claim = {"id": f"T{len(text_claims)+1:03d}", "sentence": si, "word": w, "span": s[max(0, m.start()-30):m.end()+5], "subject": subj,
                         "form": "threshold", "pointer": None, "bound": False, "result": None, "reason": None}
                if subj:
                    cur = [f for f in facts_for(elems, facts, contexts) if f["context"].startswith("CurrentYear") and f["unit"] and f["unit"].upper().startswith("JPY")]
                    pri = [f for f in facts_for(elems, facts, contexts) if f["context"].startswith("Prior1Year")]
                    pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
                    if pairs:
                        c, p = pairs[0]
                        claim["pointer"] = [f"xbrl:{c['name']}@{c['context']}", f"xbrl:{p['name']}@{p['context']}", "builtin:sign(cur-prior)"]
                        claim["bound"] = True
                        actual = 1 if c["value"] - p["value"] > 0 else -1
                        claim["result"] = "GROUNDED" if actual == sg else "VALUE_MISMATCH"
                        claim["recomputed"] = c["value"] - p["value"]
                    else:
                        claim["reason"] = "no_element"
                else:
                    claim["reason"] = "no_subject"
                text_claims.append(claim)
        for w in STATE_WORDS:
            for m in re.finditer(w, s):
                text_claims.append({"id": f"T{len(text_claims)+1:03d}", "sentence": si, "word": w, "span": s[max(0, m.start()-30):m.end()+5],
                                    "subject": None, "form": "threshold", "pointer": None, "bound": False, "result": "UNVERIFIABLE", "reason": "state_word(no line)"})
    # ---------- 集計 ----------
    def rate(a, b): return round(100.0 * a / b, 1) if b else None
    nb = [c for c in num_claims if c["bound"]]
    tb = [c for c in text_claims if c["bound"]]
    recomp = [c for c in nb if c["form"] == "derived_value"]
    direct = [c for c in nb if c["form"] == "direct_value"]
    from collections import Counter
    stats = {
        "num_claims": len(num_claims), "num_bound": len(nb), "num_binding_rate_pct": rate(len(nb), len(num_claims)),
        "text_claims": len(text_claims), "text_bound": len(tb), "text_binding_rate_pct": rate(len(tb), len(text_claims)),
        "recompute_targets": len(recomp), "recompute_grounded": sum(c["result"] == "GROUNDED" for c in recomp),
        "recompute_match_rate_pct": rate(sum(c["result"] == "GROUNDED" for c in recomp), len(recomp)),
        "direct_targets": len(direct), "direct_grounded": sum(c["result"] == "GROUNDED" for c in direct),
        "direct_match_rate_pct": rate(sum(c["result"] == "GROUNDED" for c in direct), len(direct)),
        "num_forms": dict(Counter(c["form"] for c in num_claims)),
        "unbound_reasons_num": dict(Counter(c["reason"] for c in num_claims if not c["bound"])),
        "unbound_reasons_text": dict(Counter(c["reason"] for c in text_claims if not c["bound"])),
        "mismatch_num": [c["id"] for c in num_claims if c["result"] == "VALUE_MISMATCH"],
        "schemes_used": sorted({(p if isinstance(p, str) else p[0]).split(":")[0] for c in num_claims + text_claims for p in ([c["pointer"]] if isinstance(c["pointer"], str) else (c["pointer"] or []))}),
    }
    out = {"probe": "xbrl-probe-1", "date_listed": date, "selection_rule": "docTypeCode 120, xbrlFlag 1, consolidated jppfs facts > 0, min docID", "tried": tried,
           "document": {k: chosen.get(k) for k in ("docID", "filerName", "docDescription", "submitDateTime", "periodStart", "periodEnd", "edinetCode", "secCode")},
           "instance_source": inst["source"], "facts_total": len(facts), "contexts_total": len(contexts), "textblocks_total": len(tbs),
           "mdna_textblock": mdna_name, "mdna_chars": len(text), "mdna_sentences": len(sentences),
           "stats": stats, "num_claims": num_claims, "text_claims": text_claims}
    out["run"] = RUN; out["subjects_count"] = len(SUBJECTS)
    path = os.path.join(OUT, f"probe1{RUN}_{chosen['docID']}.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"document": out["document"], "instance_source": inst["source"], "facts": len(facts), "mdna": mdna_name, "mdna_chars": len(text), "stats": stats}, ensure_ascii=False, indent=1))
    print("written:", path)
    return 0


if __name__ == "__main__":
    # 規則 §1.4: 直前の平日から始め、該当 0 件なら 1 平日ずつさかのぼる(上限 10 平日)
    import datetime
    d = datetime.date.fromisoformat(sys.argv[1] if len(sys.argv) > 1 else "2026-10-05")
    for _ in range(10):
        rc = main(d.isoformat())
        if rc == 0:
            sys.exit(0)
        d -= datetime.timedelta(days=1)
        while d.weekday() >= 5:
            d -= datetime.timedelta(days=1)
    sys.exit(1)
