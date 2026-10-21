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

import dataclasses
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

# ---------------------------------------------------------------------------
# XBRL 直し §7c(人間の判断、2026-10-08): 「手書きの語彙が存在しない要素を指して
# いたと分かった分は、手書きの語彙そのものも直す。」
#
# 直すのは**この 2 語だけ**。許可された標準タクソノミ(jppfs 2025-11-01)で
# 機械確認した結果、次の 3 つを同時に満たすのがこの 2 語しかなかった:
#
#   (i)   手書きが指す要素名が 2025-11-01 の標準タクソノミに**実在しない**
#   (ii)  **同じ日本語の標準ラベル**を持つ実在の要素が在る
#   (iii) 3 書類とも手書きの要素では fact を 1 件も引けない
#
# 手書き 78 語のうち 43 語は「要素名のどれか 1 つが標準タクソノミに無い」が、
# ``facts_for`` の部分一致が ``PurchaseOfInvestmentSecurities`` ->
# ``PurchaseOfInvestmentSecuritiesInvCF`` のような接尾の族を吸収しているので
# 実際には引けている。**「名前が無い」だけでは直す理由にしない。**
# ``長期借入金の返済``(複数形 ``Repayments…``)は 3 書類とも fact 0 だが、
# 同じ日本語ラベルの要素が無い(ラベルは ``長期借入金の返済による支出``)ので
# ここでは直さず、§8 が**語として足す**側で解く。
#
# **古い要素名は消さずに足す**(会社拡張がその名前を使っている書類がありうる)。
# **``SUBJECTS_P6``・``SUBJECTS_P8`` は 1 文字も変えない** ― 変えると
# ``P7``(「直す前」)と ``P10`` の既に測った数が黙って動き、これまでの全部の
# 比較の土台が崩れる。直しは**新しい版**として入れる。
# 根拠は docs/XBRL_LABEL_VOCAB2_PLAN_2026-10-08.md §1.3。
# ---------------------------------------------------------------------------
SUBJECTS_P12_FIXES = {
    "退職給付に係る資産": ["RetirementBenefitAsset", "NetDefinedBenefitAsset"],
    "退職給付に係る負債": ["RetirementBenefitLiability", "NetDefinedBenefitLiability"],
}
SUBJECTS_P12 = tuple(
    (w, list(SUBJECTS_P12_FIXES[w])) if w in SUBJECTS_P12_FIXES else (w, e)
    for (w, e) in SUBJECTS_P8
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


def match_value(fact_value, target, unit, mode=None, magnitude_truncate=False):
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
        if mode in (None, "truncate"):
            # P19(``magnitude_truncate``、計画 docs/P17_PLAN_2026-10-14.md §8):
            # 切り捨ての帯を**絶対値で**当てる。符号つきのまま当てると、負の値で
            # 「実際より絶対値が 1 単位大きい額」を通す(実測 2 件: fact −300,297,000 に
            # 対して「4億円」)。偽なら写し元と 1 行も違わない。
            lo, hi = ((abs(fv), abs(t)) if magnitude_truncate else (fv, t))
            if 0 <= lo - hi < unit:
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


# ---------------------------------------------------------------------------
# S4(主語の規則の直し、人間の判断 1、2026-10-08): 向きの語そのものが主語の
# 範囲を決める 2 つの族。**語は字で書く。**
#
# 「増収」は収益の増、「増益」は利益の増である ― これは手書きの知識
# (CLAUDE.md の区分では記述的知識)なので、既定 False のフラグ
# ``direction_word_lexicon`` の下にだけ置く。
#
# **部分一致では決めない。** 「減損損失」は「損失」を含むが利益の族ではない。
# だから「利益」「損失」の部分一致ではなく、**この一覧の語そのもの**を文の
# 中から探す(入れ子になった出現は長い方だけを採る ― 「当期純損失」は
# 「親会社株主に帰属する当期純損失」の中にあるので 1 件と数える)。
# ---------------------------------------------------------------------------
REVENUE_WORDS = ("売上高", "営業収益", "売上収益")
PROFIT_WORDS = ("営業利益", "営業損失", "経常利益", "経常損失",
                "当期純利益", "当期純損失",
                "親会社株主に帰属する当期純利益", "親会社株主に帰属する当期純損失",
                "セグメント利益", "税引前利益")

# 向きの語 → 探す族。ここに無い向きの語(増加・減少・拡大…)には S4 を当てない
# (「増加」が何の増加かは語そのものからは決まらない)。
DIRECTION_WORD_FAMILY = {
    "増収": REVENUE_WORDS, "減収": REVENUE_WORDS,
    "増益": PROFIT_WORDS, "減益": PROFIT_WORDS,
}


def direction_family_words(sentence, word):
    """S4。向きの語 ``word`` の族の語のうち、``sentence`` に**現れるもの**。
    入れ子の出現は長い方だけを採る。戻りは (語, 出現位置) の列(文の左から)。
    族が無い向きの語なら ``None``(「当てない」と「0 件」を言い分ける)。
    """

    family = DIRECTION_WORD_FAMILY.get(word)
    if family is None:
        return None
    spans = []
    for w in family:
        start = 0
        while True:
            i = sentence.find(w, start)
            if i < 0:
                break
            spans.append((i, i + len(w), w))
            start = i + 1
    kept = [(i, j, w) for (i, j, w) in spans
            if not any((a <= i and j <= b and (b - a) > (j - i)) for (a, b, _x) in spans)]
    kept.sort()
    out, seen = [], set()
    for (i, _j, w) in kept:
        if w in seen:
            continue
        seen.add(w)
        out.append((w, i))
    return out


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
    # XBRL 直し §5 を狭める(人間の指示で確かめた結果、2026-10-08)。P10 だけ。
    # 広い版 drop_qualitative は消さずに残し、両方を測って並べる。
    drop_state_words_only: bool = False  # §5' 状態語だけを落とす(向きの語は残す)
    # XBRL 直し §7(人間の指示、2026-10-08)。P11 だけ。書類自身のインライン
    # XBRL から「日本語の勘定科目名 → 要素」を取って語彙の後ろに足す。
    label_vocabulary: bool = False       # §7 書類のラベルで主語を引く
    # XBRL 直し §7a・§7b・§8(人間の判断、2026-10-08)。P12 以降だけ。
    # P1〜P11 はこれらの既定値 False のまま変わらない(定義そのものを書き換えていない)。
    label_statement_rows_only: bool = False   # §7a 計算書の行から来たラベルだけ使う
    label_overrides_dead_hand: bool = False   # §7b 手書きが fact を引けない語はラベルで引く
    taxonomy_labels: bool = False             # §8  標準タクソノミの日本語ラベルで引く
    taxonomy_labels_all_ns: bool = False      # §8  **参考専用**。jppfs の限定を外す
    # 主語の規則の直し(人間の判断 1、2026-10-08)。P15 以降だけ。
    # P1〜P14 はこれらの既定値 False のまま変わらない(定義そのものを書き換えていない)。
    # 計画と予測は docs/XBRL_SUBJECT_RULE_PLAN_2026-10-08.md(実装前に封じた)。
    subject_skip_coordinated_cause: bool = False  # S1 「A及びBによる/により」の成分を採らない
    subject_direction_object: bool = False        # S2 「<名詞>を増加/減少」の目的語に向きが掛かる
    subject_not_part_of_aggregate: bool = False   # S3 「A及びBの合計」の成分を採らない
    direction_word_lexicon: bool = False          # S4 増収→売上高系・増益→利益系
    direction_amount_check: bool = False          # A1 向きの語と同じ節の金額も照合する
    # 概念で結ぶ直し(2026-10-13、人間の指示「根本課題を解決し、システムとして稼働させる」)。
    # P16 だけ。P1〜P15 はこれらの既定値 False のまま変わらない。
    statement_facts_first: bool = False   # C1 同じ値の候補が複数なら計算書(jppfs_cor)の fact を先に置く
    period_cue: bool = False              # C2 数の直前の「前期」「(同」などで前期の context を選ぶ
    flow_item_from_label: bool = False    # C3 「Xの増加/減少(額)」は X の CF 増減項目に結ぶ(ラベルで引く)
    pct_change_phrase: bool = False       # C4 「46.0%の大幅減益」も % の増減(当期/前期の対)として読む
    ratio_table: bool = False             # C5 「売上総利益率」などを分子/分母の 2 fact で照合する(RATIO_TABLE)
    # P17(2026-10-14 夜、人間の委任「任せる、承認いらない」。計画 docs/P17_PLAN_2026-10-14.md)。
    # 未使用 2 書類の VALUE_MISMATCH 44 件の型(HOLDOUT_P16_RESULT §11)から作った旗 5 つ。
    # P1〜P16 はこれらの既定値 False のまま変わらない。
    segment_carry_to_result_sentence: bool = False  # A' 事業名は段落をまたいで「結果の文」にだけ引き継ぐ(A は棄却、計画 §5)
    external_revenue_for_sales: bool = False      # A2 「売上高」に RevenuesFromExternalCustomers を足す(fact が在れば)
    subject_skip_before_cause_marker: bool = False  # B1 候補と数の間に「により/による」が在り、前に「〜は」の候補が在れば飛ばす
    loss_variants: bool = False                   # B2 「〜利益」の語に「〜損失」を同じ要素で足す
    prefer_net_when_labelled: bool = False        # C  ラベルに「W(純額)」が在れば、その要素を W の先頭に置く
    # P18(2026-10-14 夜、人間の問い「誤りを通す率は調べて。0 を目指さないと意味ない」)。
    # % の照合の許容を、書かれた桁の半分(1 桁なら ±0.05、0 桁なら ±0.5)+ 0.01 にする。
    # 偽なら従来どおり ±0.15(P1〜P17 は変わらない)。
    pct_tolerance_from_decimals: bool = False
    # P19(2026-10-15 未明、誤りを通す率の網羅の測定で見つけた金額の許容の符号の欠陥)。
    # 切り捨ての帯を絶対値で当てる。P1〜P18 は False のまま(振る舞いは 1 行も変わらない)。
    truncate_on_magnitude: bool = False
    # P20: 連結財務諸表が**無い**書類で、単体(NonConsolidatedMember)の枠を素の枠として
    # 扱う。書類レベルで 1 度だけ決め、連結の枠に財務の要素が 1 種でも在れば落とさない
    # (封 docs/CONSOLIDATION_P20_PLAN_2026-10-14.md §2)。
    # 実装は instance.with_nonconsolidated_fallback / instance.plain_context で、
    # 呼ぶのは recipes.build_raw_claims の 1 か所。**resolve.make_resolver ではない** ―
    # 最初そこに置いたが、止める判定はもっと上流(facts_for → ctx_ok → plain_context)に
    # 在り、変更 0 件と検出 0 件が同時に出た(結果 §1)。
    nonconsolidated_fallback: bool = False
    # P21(封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md §0): 値が一致する fact が無いときの最後の枝
    # (recipes._direct_value_claim)に、期の手がかり(F1′)・セグメントの枠が無いセグメント利益は
    # 名指さない(F2′)・増減の文が選んだ当期の残高は残高の対にする(F3b)を足す。偽なら 1 行も変わらない。
    last_branch_cues: bool = False
    # P22(封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md §1, 2026-10-20): 前期の手がかりが無い数を Prior1Year の fact に値だけで結ばない。偽なら 1 行も変わらない。
    period_bind: bool = False
    # P23(封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md §1, 2026-10-21): 書類の丸め方が切り捨てと判定されたとき、照合の帯だけを絶対値で片側(0 <= |fact| - |文| < 桁)にする。
    # ``truncate_on_magnitude``(P19)と違い ``decide_rounding`` の判定の軸は変えない。偽なら 1 行も変わらない。
    truncate_abs_band: bool = False
    # P24(封の下調べ 試作 v3、2026-10-21): ``vocab_2026_10_21`` = 語彙の登録 3 種(前期の手がかり語・ポイントの前期の語・資金の主語の句)と
    # CF 合計の要素の文字の主張を値そのものの符号で照合する。``frame_rebind`` = 取った枠で値が合わず同じ要素の別の枠で合うとき、
    # VALUE_MISMATCH をやめて UNVERIFIABLE(other_frame / ambiguous(member))。**GROUNDED は作らない。** 偽なら 1 行も変わらない。
    vocab_2026_10_21: bool = False
    frame_rebind: bool = False


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

# XBRL 直し §5' (人間の指示で確かめた結果、2026-10-08): 直し 5 を状態語だけに
# 狭めた版。P9 との差は drop_qualitative → drop_state_words_only の 1 つだけ。
# P9 の定義は書き換えない(広い版の数の照合ができるように両方残す)。
P10 = Profile(
    name="P10",
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
    drop_qualitative=False,
    text_prior_year_paren=True,
    drop_state_words_only=True,
)

# XBRL 直し §7(人間の指示、2026-10-08): P10(正本)+ ラベルの語彙。
# P10 の定義は書き換えない。
P11 = Profile(
    name="P11",
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
    drop_qualitative=False,
    text_prior_year_paren=True,
    drop_state_words_only=True,
    label_vocabulary=True,
)

# XBRL 直し §7a/§7b/§7c(人間の判断、2026-10-08): P11 の悪化 2 件のうち原因が
# 分かっている 1 件を消し(§7a)、手書きが fact を引けない語をラベルで引き(§7b)、
# 手書きの語彙そのものを直した版(§7c = SUBJECTS_P12)。
# P10・P11 の定義は書き換えない。
P12 = Profile(
    name="P12",
    subjects=SUBJECTS_P12,
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
    drop_qualitative=False,
    text_prior_year_paren=True,
    drop_state_words_only=True,
    label_vocabulary=True,
    label_statement_rows_only=True,
    label_overrides_dead_hand=True,
)

# XBRL 直し §8(人間の許可、2026-10-08): P12 + 標準タクソノミの日本語ラベル。
P13 = Profile(
    name="P13",
    subjects=SUBJECTS_P12,
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
    drop_qualitative=False,
    text_prior_year_paren=True,
    drop_state_words_only=True,
    label_vocabulary=True,
    label_statement_rows_only=True,
    label_overrides_dead_hand=True,
    taxonomy_labels=True,
)

# **参考専用**。P13 から名前空間の限定(jppfs だけ)を外した版。
# 「jppfs に限って何を失ったか」を数で言えるようにするためだけに在る。
P14 = Profile(
    name="P14",
    subjects=SUBJECTS_P12,
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
    drop_qualitative=False,
    text_prior_year_paren=True,
    drop_state_words_only=True,
    label_vocabulary=True,
    label_statement_rows_only=True,
    label_overrides_dead_hand=True,
    taxonomy_labels=True,
    taxonomy_labels_all_ns=True,
)

# 主語の規則の直し(人間の判断 1、2026-10-08): P13 + S1・S2・S3・S4・A1。
# **P13 の定義は 1 行も書き換えない**(直す前と直した後を並べて測るため)。
P15 = Profile(
    name="P15",
    subjects=SUBJECTS_P12,
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
    drop_qualitative=False,
    text_prior_year_paren=True,
    drop_state_words_only=True,
    label_vocabulary=True,
    label_statement_rows_only=True,
    label_overrides_dead_hand=True,
    taxonomy_labels=True,
    subject_skip_coordinated_cause=True,
    subject_direction_object=True,
    subject_not_part_of_aggregate=True,
    direction_word_lexicon=True,
    direction_amount_check=True,
)

# ---------------------------------------------------------------------------
# P16 = P13(標準タクソノミのラベルで主語を引く)+ 概念で結ぶ直し C1・C2・C3。
# 独立ラベル 183 件(docs/research/e2_labels)で根拠の正しさを測って選ぶ。
# P15 の S1〜S4・A1 は含めない(別に測る)。
# ---------------------------------------------------------------------------
# C5 の表(記述的知識。CLAUDE.md 4 番の区分では承認の要る判断的知識ではなく、率の定義)。
# 語は本文の言い回し、値は (分子の要素, 分母の要素)。同じ期の 2 fact で 分子/分母*100。
RATIO_TABLE = {
    "売上総利益率": ("GrossProfit", "NetSales"),
    "売上原価率": ("CostOfSales", "NetSales"),
    "売上高営業利益率": ("OperatingIncome", "NetSales"),
    "営業利益率": ("OperatingIncome", "NetSales"),
    "売上高経常利益率": ("OrdinaryIncome", "NetSales"),
    "経常利益率": ("OrdinaryIncome", "NetSales"),
}

P16 = dataclasses.replace(P13, name="P16", taxonomy_labels_all_ns=True, statement_facts_first=True,
                          period_cue=True, flow_item_from_label=True, pct_change_phrase=True,
                          ratio_table=True)

# P17 = P16 + 未使用 2 書類で読んだ型の規則 5 つ(計画と予測は docs/P17_PLAN_2026-10-14.md)。
# 既定 profile ではない(未使用の書類で確認するまで)。
P17 = dataclasses.replace(P16, name="P17", segment_carry_to_result_sentence=True, external_revenue_for_sales=True,
                          subject_skip_before_cause_marker=True, loss_variants=True, prefer_net_when_labelled=True)

# P18 = P17 + % の許容を書かれた桁から決める(誤りを通す率の測定 1 回目で、% の末尾 0.1 の
# ずれが ±0.15 の許容を通っていた。計画 docs/P17_PLAN_2026-10-14.md §7)。
P18 = dataclasses.replace(P17, name="P18", pct_tolerance_from_decimals=True)

# P19 = P18 + 切り捨ての帯を絶対値で当てる(計画 docs/P17_PLAN_2026-10-14.md §8)。
P19 = dataclasses.replace(P18, name="P19", truncate_on_magnitude=True)

# P20 = P16 + 連結財務諸表が無い書類で単体の枠を使う(封 docs/CONSOLIDATION_P20_PLAN_2026-10-14.md)。
# **P17〜P19 の上には積まない。**P17 は未使用の 6 書類で効果 +0.0 ポイントだった
# (docs/HOLDOUT_P17_RESULT_2026-10-14.md)ので、P16 を土台にする。
P20 = dataclasses.replace(P16, name="P20", nonconsolidated_fallback=True)

# P21 = P20 + 最後の枝の 3 つの直し(封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md)。段 1 では既定にしない。
P21 = dataclasses.replace(P20, name="P21", last_branch_cues=True)
P22 = dataclasses.replace(P21, name="P22", period_bind=True)    # 封 XBRL_PERIOD_BIND_SEAL_2026-10-20。段 1 では既定にしない

# P23 = P22 + 率の帯を書かれた桁から(P18 の旗、既存)+ 切り捨ての帯を絶対値で片側(新しい旗)。**P19 の truncate_on_magnitude は積まない**(判定の軸も変わり 3 書類で金額 55 行が落ちる、封 §0)。段 1 では既定にしない。
P23 = dataclasses.replace(P22, name="P23", pct_tolerance_from_decimals=True, truncate_abs_band=True)

# ---------------------------------------------------------------------------
# P24 vocab_2026_10_21 (3): 資金の主語の句。下調べで件数 2 以上だった 19 通り(助詞「は」を除いた形。既存 6 句
# 「営業活動の結果獲得した資金」等と同じ書き方)を、同じ要素に結ぶ。旗が真のときだけ recipes.build_raw_claims が
# 主語の一覧の先頭に足す。P1〜P23 の subjects は不変。
# ---------------------------------------------------------------------------
_CF_OPE = ["NetCashProvidedByUsedInOperatingActivities"]
_CF_INV = ["NetCashProvidedByUsedInInvestingActivities"]
_CF_FIN = ["NetCashProvidedByUsedInFinancingActivities"]
CF_FUND_SUBJECTS_2026_10_21 = (
    ("営業活動の結果得られた資金", _CF_OPE), ("営業活動により得られた資金", _CF_OPE), ("営業活動による資金の増加", _CF_OPE),
    ("営業活動の結果増加した資金", _CF_OPE), ("営業活動の結果支出した資金", _CF_OPE), ("営業活動による資金の獲得額", _CF_OPE),
    ("投資活動による資金の減少", _CF_INV), ("投資活動の結果支出した資金", _CF_INV), ("投資活動により使用した資金", _CF_INV),
    ("投資活動の結果増加した資金", _CF_INV), ("投資活動による資金の支出額", _CF_INV),
    ("財務活動の結果支出した資金", _CF_FIN), ("財務活動による資金の増加", _CF_FIN), ("財務活動により獲得した資金", _CF_FIN),
    ("財務活動により使用した資金", _CF_FIN), ("財務活動の結果得られた資金", _CF_FIN), ("財務活動の結果増加した資金", _CF_FIN),
    ("財務活動により得られた資金", _CF_FIN), ("財務活動による資金の減少", _CF_FIN),
)

# P24 = P23 + 語彙の登録 + 枠の取り直し(UNVERIFIABLE だけ)。段 1 では既定にしない。
P24 = dataclasses.replace(P23, name="P24", vocab_2026_10_21=True, frame_rebind=True)

PROFILES = {"P1": P1, "P5F": P5F, "P6": P6, "P7": P7, "P8": P8, "P9": P9, "P10": P10, "P11": P11,
            "P12": P12, "P13": P13, "P14": P14, "P15": P15, "P16": P16, "P17": P17, "P18": P18,
            "P19": P19, "P20": P20, "P21": P21, "P22": P22, "P23": P23, "P24": P24}

# **既定 profile(人間の決定 2026-10-13、第 2 段階)。字で留める。**
# 測定で採用候補にした P16(開発書類 183 件で 146/8/29、未使用 2 書類 217 件で E1' 66.8% / E2 8.2% / E3 27.2%)。
# 明示的に P7・P13 などを渡す既存の呼び出しは変えない。変えるときは人間の決定と DECISION_LOG の項目が要る。
# 2026-10-14 の人間の決定で P16 -> P20。根拠は docs/FINAL_EVAL_8_RESULT_2026-10-14.md(Q1・Q3)と
# docs/Q2_NONCONSOLIDATED_RESULT_2026-10-14.md(Q2)。P16 と P20 を分ける 3 つの数が P20 に有利か中立:
#   連結のある未使用 8 書類 683 行で差 0 行 / 連結の無い 2 書類で P16 は 0/250 行 /
#   その 2 書類で P20 の新規接続が N-1 60.5%・N-2 5.3%・N-3 0 件(母数 21 行)。独立監査 GO 2 回。
# **engine 全体の品質合格ではない**: 同じ 8 書類で E2/G = 11.6%(合格線 10% 未達)が P16・P20 ともに残る。
# 2026-10-20 に P20 -> P21(段 2)。人間の指示「アダプターの問題か。とにかく精度を改善して。何してもいいから」の
# 委任のもと、封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md の段 2 の条件が当たったので切り替えた:
#   N-4 無改変 40 書類で GROUNDED の行が動いた 0 / N-5 gen_c 8 書類の VM -> PNF は 7(幅 0〜10)。
# 結果は docs/XBRL_NAMING_FIX_RESULT_2026-10-20.md。**P20 の字は消さず**、P20 を明示した呼び出しは変えない。
# 2026-10-20 に P21 -> P22(期を縛る P22 の段 2)。人間の決定 2026-10-20「任せる」。段 1 3320c8c の結果(67 書類の無改変で、前期の値への置き換えを
# 通した 458 / 485 -> 1 / 485、代価は正しい GROUNDED を離れた 25 行うち正しい前期の文 11 が VALUE_MISMATCH)と、客の席の回し直し(同じ書類で
# 誤り 5 / 5 止め・正しい 39 行の空振り 0。開発側でない客の席の日記。repo の外 = scratchpad、記録なし。司令塔が読んで諮った数)を見てから。封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md の段 2(E-8)、結果は
# docs/XBRL_PERIOD_BIND_RESULT_2026-10-20.md。**P21 の字は消さず**、P21 を明示した呼び出しは変えない(P21 の既定は 2026-10-20 a516288)。
DEFAULT_PROFILE = "P22"
