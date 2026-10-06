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


def match_value(fact_value, target, unit):
    """xbrl_probe.py: match_value の写し(round / truncate / abs の組)。"""

    for sign_mode, fv in (("", fact_value), ("abs", abs(fact_value))):
        t = abs(target) if sign_mode else target
        if abs(fv - t) <= unit / 2:
            return (sign_mode + "+round").strip("+")
        if 0 <= fv - t < unit:
            return (sign_mode + "+truncate").strip("+")
    return None


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

PROFILES = {"P1": P1, "P5F": P5F, "P6": P6}
