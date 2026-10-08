# -*- coding: utf-8 -*-
"""Subject -> element-name vocabulary, unit scale, value matching, and
the two Adapter profiles (``P1`` / ``P5F``).

The word lists below are a transcription (not an import) of
``fixtures/xbrl/xbrl_probe.py`` (``SUBJECTS``, ``RUN == "B"`` branch) and
``fixtures/xbrl/xbrl_probe4.py`` (``VOCAB4``). ``tests/adapters/xbrl/test_lineage.py``
compares these, value for value and in order, against the originals
loaded with ``importlib`` so that any drift is caught by the lineage
test rather than relying on this comment.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# SUBJECTS: 1 本目(PROBE_RUN="A")の 39 語。xbrl_probe.py の SUBJECTS リテラル
# そのまま(RUN=="B" の足し込みを行う前の状態)。
# ---------------------------------------------------------------------------
SUBJECTS_BASE_39 = [
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

# ---------------------------------------------------------------------------
# RUN=="B" で足される 34 語(xbrl_probe.py の `if RUN == "B":` ブロックのリテラル、
# 足す順のまま)。最終の SUBJECTS_73 はこの 34 語 + 上の 39 語(この順)。
# ---------------------------------------------------------------------------
SUBJECTS_RUN_B_EXTRA_34 = [
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
]

# 1 本目 Run B = SUBJECTS_RUN_B_EXTRA_34 + SUBJECTS_BASE_39(この順、34 + 39 = 73 語)。
SUBJECTS_73 = SUBJECTS_RUN_B_EXTRA_34 + SUBJECTS_BASE_39

# 4 本目の変更 A: 先頭に 1 行足す(P.SUBJECTS.insert(0, VOCAB4))。
VOCAB4 = ("セグメント利益", ["OperatingIncome"])
SUBJECTS_74 = [VOCAB4] + SUBJECTS_73

# ---------------------------------------------------------------------------
# Core 接続 C-1g §1-1(人間の承認、2026-10-06): profile P6 だけの語彙 7 行
# (3 社目の結果文書 §5 XP-3rd-2/XP-3rd-4 に出た語彙の穴)。P6 の語彙の先頭に足す。
# ---------------------------------------------------------------------------
SUBJECTS_P6_EXTRA_7 = [
    ("流動負債", ["CurrentLiabilities"]),
    ("固定負債", ["NoncurrentLiabilities"]),
    ("投資有価証券の取得による支出", ["PurchaseOfInvestmentSecurities"]),
    ("1年内返済予定の長期借入金", ["CurrentPortionOfLongTermLoansPayable", "CurrentPortionOfLongTermBorrowings"]),
    ("持分法による投資利益", [
        "ShareOfProfitOfEntitiesAccountedForUsingEquityMethod",
        "ShareOfProfitLossOfEntitiesAccountedForUsingEquityMethod",
        "EquityInEarningsOfAffiliates",
    ]),
    ("ROE", ["RateOfReturnOnEquity"]),
    ("退職給付に係る負債", ["RetirementBenefitLiability"]),
]
SUBJECTS_P6 = tuple(SUBJECTS_P6_EXTRA_7) + tuple(SUBJECTS_74)

# ---------------------------------------------------------------------------
# XBRL 直し §1a(人間の決定、2026-10-08): 「資産合計」の要素に ``TotalAssets``
# を足す。``instance.facts_for`` は ``要素名 + "SummaryOfBusinessResults"`` を
# 完全一致に数えるので、これで業績概要の要素
# ``jpcrp_cor:TotalAssetsSummaryOfBusinessResults``(前々期まで在る)が引ける。
# 「純資産合計」は ``["NetAssets"]`` のまま
# ``NetAssetsSummaryOfBusinessResults`` が引けていた ― その非対称を直すだけで、
# 新しい主語は 1 つも足していない。P6 の語彙(``SUBJECTS_P6``)は不変。
# ---------------------------------------------------------------------------
SUBJECTS_P8 = tuple(
    ("資産合計", ["Assets", "TotalAssets"]) if w == "資産合計" else (w, e)
    for (w, e) in SUBJECTS_P6
)

PROFIT_SUBJECTS = ("利益", "損失")

UNIT_SCALE = {"百万円": 1e6, "千円": 1e3, "億円": 1e8, "兆円": 1e12, "円": 1}


def tol_of(fact, claim_scale):
    """xbrl_probe.py: tol_of の写し。"""

    d = fact.get("decimals")
    try:
        if d is not None and d not in ("INF",):
            return max(0.5 * (10 ** (-int(d))), 0.5 * claim_scale)
    except ValueError:
        pass
    return 0.5 * claim_scale


def match_value(fact_value, target, unit, mode=None):
    """xbrl_probe.py: match_value の写し(round / truncate / abs の組)。

    ``mode`` は XBRL 直し §2(人間の決定、2026-10-08)で足した省略可能な引数。
    ``None`` のとき、この関数は写し元と 1 行も違わない振る舞いをする
    (P1/P5F/P6/P7 はすべて ``None`` で呼ぶ)。``"round"`` / ``"truncate"``
    のときは**その 1 つだけ**を試す ― 主張ごとに 4 つの梯子を順に試すのを
    やめ、書類単位で決めた 1 つの丸め方で照合するため。許容幅は
    ``mode=None`` の実質 ``-unit/2 .. +unit`` から、``"round"`` なら
    ``-unit/2 .. +unit/2``、``"truncate"`` なら ``0 .. +unit`` に狭まる。
    """

    for sign_mode, fv in (("", fact_value), ("abs", abs(fact_value))):
        t = abs(target) if sign_mode else target
        if mode in (None, "round") and abs(fv - t) <= unit / 2:
            return (sign_mode + "+round").strip("+")
        if mode in (None, "truncate") and 0 <= fv - t < unit:
            return (sign_mode + "+truncate").strip("+")
    return None


# ---------------------------------------------------------------------------
# XBRL 直し §2(人間の決定、2026-10-08): 書類単位の丸め方。``profile.doc_rounding``
# が真のときだけ使う。既定の札(どちらとも言えないとき)は字で書く。
# ---------------------------------------------------------------------------
DOC_ROUNDING_DEFAULT = "round"
ROUNDING_MODES = ("round", "truncate")


def decide_rounding(evidence):
    """書類の丸め方を 1 つに決める。``evidence`` は ``(diff, unit)`` の列
    (``diff`` は照合が実際に使った軸での fact − 目標、``unit`` は主張の桁)。

    ``R`` = round しか説明できない件数(``diff < 0``)。
    ``T`` = truncate しか説明できない件数(``diff > unit/2``)。
    ``T > R`` なら ``"truncate"``、そうでなければ ``DOC_ROUNDING_DEFAULT``。
    戻り値は ``(mode, R, T)`` ― 決めた根拠の数も一緒に返す(記録に残すため)。
    """

    r = sum(1 for d, u in evidence if d < 0)
    t = sum(1 for d, u in evidence if d > u / 2.0)
    return (("truncate" if t > r else DOC_ROUNDING_DEFAULT), r, t)


# ---------------------------------------------------------------------------
# Core 接続 C-1g §1-2(人間の決定、2026-10-06、CF 流量項目の符号の規約 b)。
# 要素の局所名(接頭辞を除いた部分。会社拡張でも同じ判定)が
# DecreaseIncreaseIn… なら正 = 減少(規約 -1)、IncreaseDecreaseIn…
# (NetIncreaseDecreaseIn… を含む)なら正 = 増加(規約 +1)。該当しなければ
# None(流量項目ではない)。
# ---------------------------------------------------------------------------
_FLOW_DECREASE_INCREASE_RE = re.compile(r"^(?:Net)?DecreaseIncreaseIn")
_FLOW_INCREASE_DECREASE_RE = re.compile(r"^(?:Net)?IncreaseDecreaseIn")


def flow_convention(element_name):
    """CF 流量項目の符号の規約(C-1g §1-2)。``element_name`` は
    ``prefix:Local`` でも局所名だけでもよい(``:`` で分けて末尾を使う)。
    """

    local = element_name.split(":")[-1]
    if _FLOW_INCREASE_DECREASE_RE.match(local):
        return 1
    if _FLOW_DECREASE_INCREASE_RE.match(local):
        return -1
    return None


# ---------------------------------------------------------------------------
# Core 接続 C-1h §1-1(人間の決定、2026-10-06)。CF の「支出」系項目(負で
# 記録され、文の「増加/減少」は大きさの増減)。``ProceedsFrom…`` は含めない。
# ``flow_convention`` が非 None の要素(DecreaseIncreaseIn…/IncreaseDecreaseIn…)
# は呼び出し側で先に試すので、このチェックはそちら向け。
# ---------------------------------------------------------------------------
_EXPENDITURE_RE = re.compile(
    r"^(PurchaseOf|PaymentsFor|Payments|RepaymentsOf|RepaymentOf|RedemptionOf|DividendsPaid|IncomeTaxesPaid|InterestPaid)"
)


def expenditure_convention(element_name):
    """CF の「支出」系項目かどうか(C-1h §1-1)。``element_name`` は
    ``prefix:Local`` でも局所名だけでもよい。
    """

    local = element_name.split(":")[-1]
    return bool(_EXPENDITURE_RE.match(local))


@dataclass(frozen=True)
class Profile:
    """A named bundle of Adapter settings (Adapter-only knowledge; the Core
    never sees a profile name).
    """

    name: str
    subjects: Tuple[Tuple[str, List[str]], ...]
    member_on: bool
    claim_level_member: bool
    run3: Optional[str]
    # Core 接続 C-1g §1(人間の承認、2026-10-06): P6 だけの 3 つのフラグ。
    # P1・P5F はこれらの既定値 False のまま変わらない(定義そのものを書き
    # 換えていない)。
    flow_sign: bool = False
    point_diff: bool = False
    segment_denominator: bool = False
    # Core 接続 C-1h §1(人間の決定、2026-10-06): P7 だけの 3 つのフラグ。
    # P1・P5F・P6 はこれらの既定値 False のまま変わらない(定義そのものを
    # 書き換えていない)。
    expenditure_sign: bool = False
    target_word: bool = False
    text_reason_split: bool = False
    # XBRL 直し(人間の決定、2026-10-08): P8 だけの 5 つのフラグ。
    # P1・P5F・P6・P7 はこれらの既定値 False のまま変わらない。
    # 1 つずつ独立に測れるように、5 つを 1 つのフラグに束ねていない。
    prior2_required: bool = False      # §1b 前々期が無ければ代用せず止める
    doc_rounding: bool = False         # §2  丸め方は書類単位で 1 つ
    target_both: bool = False          # §3  目標・見通しを数と文字の両方に
    paren_sentence: bool = False       # §4  括弧の中の句点では切らない
    drop_qualitative: bool = False     # §5  定性的な語を主張にしない
    # XBRL 直し §6(人間の決定、2026-10-08)。P9 だけ。P1〜P8 は既定の False。
    text_prior_year_paren: bool = False  # §6 括弧内の前期の方向語を前期−前々期に


P1 = Profile(
    name="P1",
    subjects=tuple(SUBJECTS_73),
    member_on=False,
    claim_level_member=False,
    run3=None,
)

P5F = Profile(
    name="P5F",
    subjects=tuple(SUBJECTS_74),
    member_on=True,
    claim_level_member=True,
    run3="L",
)

P6 = Profile(
    name="P6",
    subjects=SUBJECTS_P6,
    member_on=True,
    claim_level_member=True,
    run3="L",
    flow_sign=True,
    point_diff=True,
    segment_denominator=True,
)

P7 = Profile(
    name="P7",
    subjects=SUBJECTS_P6,
    member_on=True,
    claim_level_member=True,
    run3="L",
    flow_sign=True,
    point_diff=True,
    segment_denominator=True,
    expenditure_sign=True,
    target_word=True,
    text_reason_split=True,
)

P8 = Profile(
    name="P8",
    subjects=SUBJECTS_P8,
    member_on=True,
    claim_level_member=True,
    run3="L",
    flow_sign=True,
    point_diff=True,
    segment_denominator=True,
    expenditure_sign=True,
    target_word=True,
    text_reason_split=True,
    prior2_required=True,
    doc_rounding=True,
    target_both=True,
    paren_sentence=True,
    drop_qualitative=True,
)

# XBRL 直し §6(人間の決定、2026-10-08): 6 つ目の直しを足した profile。
# P8 の定義は書き換えない(5 つと 6 つの差が読めるように両方残す)。
P9 = Profile(
    name="P9",
    subjects=SUBJECTS_P8,
    member_on=True,
    claim_level_member=True,
    run3="L",
    flow_sign=True,
    point_diff=True,
    segment_denominator=True,
    expenditure_sign=True,
    target_word=True,
    text_reason_split=True,
    prior2_required=True,
    doc_rounding=True,
    target_both=True,
    paren_sentence=True,
    drop_qualitative=True,
    text_prior_year_paren=True,
)

PROFILES = {"P1": P1, "P5F": P5F, "P6": P6, "P7": P7, "P8": P8, "P9": P9}
