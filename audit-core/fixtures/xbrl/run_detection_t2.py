# -*- coding: utf-8 -*-
"""型 2(単位のずれ)の検出率を 1 書類ぶん測る計器。

封 ``audit-core/docs/DETECTION_T2_PLAN_2026-10-08.md`` 第 1 部(段 3/段 4)の
測り方 1〜7 を実装する。Core(``audit_core``)のコードではなく、Core/Adapter を
P7 プロファイルで回して結果を見るだけの計測 script(``run_core_path.py`` と
同じ位置づけ)。

段の順番(封のとおり):

1. 原本の ZIP を読み、sha256 を凍結済みの表と照合する(違えば止まる)。
2. 原本を P7 + Core で回して基準線を取る。
3. 型 2 の現場の一覧を ``measure/lib/sites.t2_sites`` で取る(``refs=[]``)。
4. 現場ごとに (a) HTML で一意に特定できるか (b) 対応する基準線の Claim が
   GROUNDED か (c) 兄弟の単位が在るか(``t2_sites`` が既に保証)の 3 門。
5. 残った現場から種で ``--count`` 件を抽選する(決定的)。
6. 1 件ごとに混入 ZIP を作り、P7 + Core で回し、同じ Claim の状態を見る。
7. 入口から全段の件数と、1 件ごとの行、族ごとの集計を 1 本の JSON に書く。

通信はしない(ZIP は ``~/.cache/audit-core/edinet/`` から)。EDINET には
触れない。API キーは使わない。

Usage::

    python3 fixtures/xbrl/run_detection_t2.py --doc S100Z4B6 --profile P7 \\
        --material audit-core/measure/material/xbrl --count 12 \\
        --seed audit-core-detection-t2-2026-10-08-9c41 --out <path>

対応づけ(型 2 の現場 -> 基準線の Claim)について
--------------------------------------------------
``measure/lib/sites.t2_sites`` は ``measure/prepare_material.py`` が独立に
strip した平文(``material/xbrl/<doc>.original.txt``)の上で動く。Adapter 自身
は ``adapters.xbrl.instance.strip_html`` で**別に** strip した平文の上で
Claim を作る。実測(2026-10-08): 2 つの平文は長さが毎書類で違う(意図的に
独立 ― prepare_material.py の docstring参照)。したがって offset で対応づける
ことはできない。

最初に provenance.span(平文の 40 字程度の窓)を文字列として検索する方法を
試したが、実測(S100Z4Q1)で密な文(「...394億1千9百万円(前連結会計年度比
106.0%)、受注残高は214億2千2百万円(同106.8%)...」)が並ぶ所で、窓が隣の数
の単位まで拾ってしまい、本来一意な現場が「2 件以上に対応」という偽の曖昧
さを量産した(例: 106.8% は N003 の窓にも N004 の窓にも出る)。

そこで、Adapter が Claim の id を振る**まさにその列挙**
(``extract.split_sentences`` -> ``extract.iter_numbers`` -> 除外判定
``EXCLUDE_AFTER``/``EXCLUDE_CONTEXT``)をこの計器でも独立に再現し
(:func:`num_claim_sites`)、各現場の「全文一致」(``s[a:b]`` が
``number_text + 区切り + unit`` と完全一致)で対応づける。数字はどこにも
動かさないので、この列挙は混入の前後で同じ順序・同じ id を作るはずであり、
実際そうなることを ``id_cross_check_agrees`` で混入ごとに確かめる(確かめ
損ねた場合に初めて "post_claim_id is None" が起きる)。
"""

import argparse
import collections
import hashlib
import io
import json
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "measure"))
sys.path.insert(0, HERE)

import audit_core as core  # noqa: E402
from adapters.xbrl import edinet as E, extract as Ex, instance as I, recipes as R, resolve as RV, registry_setup as RS, vocabulary as V  # noqa: E402
from lib import numbers as N  # noqa: E402
from lib import sites as S  # noqa: E402
import tamper_unit as T  # noqa: E402

# 封(DETECTION_T2_PLAN_2026-10-08.md 第 1 部「凍結する対象」)の表。測る対象は
# この 3 書類だけ。ここにしか ZIP の sha256 は書かない(run_core_path.py の
# --zip-sha256 は呼び出し側が渡す任意引数だが、この計器は人間の決定どおり
# 「違えば止まる」を既定の挙動にするため、表そのものをここで持つ)。
FROZEN_ZIP_SHA256 = {
    "S100Z4Q1": "0731a291f10af5dd207e05d54df8e2b5dc34e79a84de94af1c1a5d4e207228f6",
    "S100Z4B6": "d617b6e1807c8aa6d2b1269f6b25ff57a6a71dbf683020f1859d2d4a04c02d26",
    "S100YMFV": "4a5982e7447d6e0614c6ad12e7c091d462ca61a0128c2ce2af957a8bdfe1d52c",
}

_SEP_RE_SRC = r"[ 　]*"


def run_core_rows(zb, profile_name):
    """run_core_path.py の 8 行の組み立てと同じ(重複を避けるため import は
    せず、同じ 8 行をここでも書く ― run_core_path.py は CLI 単体で動く計器
    であり、この計器が依存してよい「核」ではないため)。"""

    inst = I.load_instance(zb)
    recipes = list(R.build_recipes(zb, V.PROFILES[profile_name]))
    resolver = RV.make_resolver(inst["facts"])
    registry = RS.register_all(core.Registry.default())
    results = core.verify_all(recipes, resolver, registry)
    rows = []
    for rc, rs in zip(recipes, results):
        c = rc.claim
        rows.append({
            "id": c.id,
            "unit": c.unit,
            "state": rs.state.value,
            "recomputed": rs.recomputed,
            "reason": rs.reason,
        })
    return rows


def num_claim_sites(zb):
    """Adapter が数の Claim に id を振るまさにその列挙(``recipes.
    _build_raw_num_claims``)を、Claim を作らずに再現する。読むだけ
    (``adapters.xbrl.extract``/``instance`` の関数をそのまま呼ぶ。1 行も
    書き換えない)。戻り値は Claim の出現順 == id の番号順。"""

    inst = I.load_instance(zb)
    name = I.select_mdna(inst["textblocks"])
    text = I.strip_html(inst["textblocks"][name]) if name else ""
    sentences = Ex.split_sentences(text)
    out = []
    n = 0
    for si, s in enumerate(sentences):
        for (a, b, signed, unit, _prec) in Ex.iter_numbers(s):
            after = s[b:b + 3]
            around = s[max(0, a - 12):b + 4]
            if Ex.EXCLUDE_AFTER.match(after) or Ex.EXCLUDE_CONTEXT.search(around):
                continue
            n += 1
            out.append({
                "id": "N%03d" % n,
                "sentence_index": si,
                "start": a,
                "end": b,
                "unit": unit,
                "value": signed,
                "digits": s[a:b],
            })
    return out


def all_iter_numbers_raw(zb):
    """REVISE 2026-10-08(独立監査、2 回目、人間の追加指示)§①の構造判定用の
    診断道具。``num_claim_sites`` と同じ列挙(``extract.split_sentences`` ->
    ``extract.iter_numbers``)だが、``EXCLUDE_AFTER``/``EXCLUDE_CONTEXT`` の
    除外を**かけない**(採点には使わない。「t2_sites の現場は Adapter の
    iter_numbers が拾う数の部分集合か」と「除外が何回発火したか」を実測
    するためだけの、読むだけの道具)。戻り値は ``(all_digits, excluded_digits)``
    ― それぞれ ``digits`` 文字列(number+unit)の集合。"""

    inst = I.load_instance(zb)
    name = I.select_mdna(inst["textblocks"])
    text = I.strip_html(inst["textblocks"][name]) if name else ""
    sentences = Ex.split_sentences(text)
    all_digits = []
    excluded_digits = []
    for si, s in enumerate(sentences):
        for (a, b, signed, unit, _prec) in Ex.iter_numbers(s):
            digits = s[a:b]
            all_digits.append(digits)
            after = s[b:b + 3]
            around = s[max(0, a - 12):b + 4]
            if Ex.EXCLUDE_AFTER.match(after) or Ex.EXCLUDE_CONTEXT.search(around):
                excluded_digits.append(digits)
    return all_digits, excluded_digits


def structural_check_for_bucket1(zb, raw_sites):
    """①(対応する Claim が 0 件)が **構造的に 0 件になる** かどうかを実測
    する(人間の指示: 「0 件」に理由を測らず付けない)。

    2 つを測る:

    1. ``t2_sites`` の各現場(number_text+unit, 単位の両形)が、除外を**かけ
       ない** ``all_iter_numbers_raw`` の列(= Adapter の ``iter_numbers`` が
       そもそも認識する数の全体)に**部分集合として含まれるか**。
    2. 含まれる場合、その出現が ``EXCLUDE_AFTER``/``EXCLUDE_CONTEXT`` で**実際
       に除外された回数**(除外後の列に残らなかった回数)。

    両方が 0(=全現場が認識され、除外も 0 回)なら、①=0 は**この 3 書類で
    構造的に保証されている**(たまたま 0 件なのではない)。そうでない現場
    があれば、その現場を名指しで報告する(推測で「構造的」と言わない)。
    """

    all_digits, excluded_digits = all_iter_numbers_raw(zb)
    all_counter = collections.Counter(all_digits)
    excluded_counter = collections.Counter(excluded_digits)

    not_in_all = []
    excluded_hits = []
    for site in raw_sites:
        tok = site["token"]
        variants = _unit_text_variants(tok.unit)
        pats = [re.compile(r"^" + re.escape(tok.text) + _SEP_RE_SRC + re.escape(v) + r"$") for v in variants]
        in_all = any(any(p.match(d) for p in pats) for d in all_counter)
        excluded_n = sum(excluded_counter[d] for d in excluded_counter if any(p.match(d) for p in pats))
        if not in_all:
            not_in_all.append({"number_text": tok.text, "unit": tok.unit})
        if excluded_n:
            excluded_hits.append({"number_text": tok.text, "unit": tok.unit, "excluded_count": excluded_n})

    return {
        "sites_checked": len(raw_sites),
        "sites_not_subset_of_iter_numbers": len(not_in_all),
        "not_subset_examples": not_in_all[:20],
        "exclude_after_or_context_fired_for_sites": len(excluded_hits),
        "exclude_fired_examples": excluded_hits[:20],
        "exclude_after_fired_total_in_document": sum(
            1 for d in excluded_digits if True
        ),  # 文書全体で何回発火したか(t2_sites の現場に限らない全数)
        "is_structural_zero": (len(not_in_all) == 0 and len(excluded_hits) == 0),
    }


def _unit_text_variants(unit):
    """``adapters.xbrl.extract.split_sentences`` NFKC-normalises the
    Adapter's own copy of the text before building Claims (``unicodedata.
    normalize("NFKC", s.strip())``); ``measure/lib/numbers.py`` does not (it
    only folds digits, not ％ -> %). Measured 2026-10-08: without this,
    every ％ site in ``S100Z4Q1`` had 0 matches (the Adapter's own text held
    ``%``, the token's unit was ``％``). Trying both forms covers this
    without special-casing ％ by name."""

    import unicodedata

    return sorted({unit, unicodedata.normalize("NFKC", unit)})


def find_claim_sites_by_digits(num_sites, number_text, unit):
    """Exact (not fuzzy) match: ``num_sites`` entries whose ``digits`` field
    equals ``number_text`` immediately followed (modulo a run of spaces) by
    ``unit`` -- the literal text the Adapter's own number scanner matched,
    not a window search. See the module docstring for why this replaced an
    earlier provenance.span substring search."""

    pats = [re.compile(r"^" + re.escape(number_text) + _SEP_RE_SRC + re.escape(v) + r"$") for v in _unit_text_variants(unit)]
    return [ns for ns in num_sites if any(p.match(ns["digits"]) for p in pats)]


def draw_sites(eligible, seed, doc_id, count):
    """段 5: 種で ``count`` 件を決定的に抽選し、兄弟の単位も同じ種から選ぶ。

    ``eligible`` は辞書の列で、各辞書が ``"siblings"``(非空のリスト)を持つ
    こと。抽選・兄弟選択のどちらも ``seed + ":" + doc_id`` から作る 1 本の
    ``random.Random`` を順番に消費するので、同じ入力なら必ず同じ結果になる
    (試験: 抽選が決定的・種を変えると変わる)。

    戻り値 ``(drawn, new_units, k)``: ``drawn`` は ``eligible`` から選ばれた
    要素(元の並び順を保つ)、``new_units`` は対応する要素ごとに割り当てた
    兄弟の単位、``k`` は実際に抽選できた件数(``len(eligible) < count`` なら
    ``len(eligible)``)。"""

    rng = random.Random(seed + ":" + doc_id)
    k = min(count, len(eligible))
    idx = sorted(rng.sample(range(len(eligible)), k)) if k else []
    drawn = [eligible[i] for i in idx]
    new_units = [d["siblings"][rng.randrange(len(d["siblings"]))] for d in drawn]
    return drawn, new_units, k


def classify_site(tok, siblings, baseline_num_sites, baseline_by_id, inner):
    """REVISE 2026-10-08(独立監査、2 回目、人間の追加指示)§A: 型 2 の現場を
    ①〜④ の順で分類する。**(b) 対応づけ(拾われたか/辿れていたか)を先に
    見て、(a) HTML の一意性は最後にしか見ない**(前回までの逆順)。(a) は
    こちらの道具の限界、(b) は測る対象の性質なので、同じ箱に入れない。

    戻り値の ``bucket``:

    - ``"1_not_picked_up"``           : 対応する Claim が 0 件
      (「止めなかった」。定義どおりの検出率の分母に入る)
    - ``"2_ambiguous_correspondence"` : 対応する Claim が 2 件以上
      (この 1 回の出現が主張になったかを digits だけでは言い切れない。
      「場所を特定できない」として除外)
    - ``"3_not_grounded_before_mixing"`` : 対応する Claim が 1 件だが
      混ぜる前から GROUNDED でない(除外。3 状態の内訳つき)
    - ``"4a_html_ambiguous"``         : 対応する Claim が 1 件で GROUNDED
      だが、HTML で一意に特定できない(道具の限界。除外)
    - ``"4b_eligible"``               : 対応する Claim が 1 件で GROUNDED、
      HTML でも一意に特定できる(混ぜられる = 母数)
    """

    cands = find_claim_sites_by_digits(baseline_num_sites, tok.text, tok.unit)
    if len(cands) == 0:
        return {"bucket": "1_not_picked_up", "claim_candidates": len(cands)}
    if len(cands) >= 2:
        return {"bucket": "2_ambiguous_correspondence", "claim_candidates": len(cands)}
    base_claim = baseline_by_id[cands[0]["id"]]
    if base_claim["state"] != "GROUNDED":
        return {
            "bucket": "3_not_grounded_before_mixing", "claim_candidates": 1,
            "baseline_claim_id": base_claim["id"], "baseline_state": base_claim["state"],
        }
    if inner is None:
        return {
            "bucket": "4a_html_ambiguous", "claim_candidates": 1,
            "baseline_claim_id": base_claim["id"], "baseline_state": base_claim["state"],
            "html_match_count": None,
        }
    try:
        T.find_unit_site(inner, tok.text, tok.unit)
    except T.AmbiguousSite as ex:
        return {
            "bucket": "4a_html_ambiguous", "claim_candidates": 1,
            "baseline_claim_id": base_claim["id"], "baseline_state": base_claim["state"],
            "html_match_count": ex.match_count,
        }
    return {
        "bucket": "4b_eligible", "claim_candidates": 1,
        "baseline_claim_id": base_claim["id"], "baseline_state": base_claim["state"],
        "html_match_count": 1,
    }


def _binom_cdf_at_least(n, k, p):
    """P(X >= k) for X ~ Binomial(n, p). Pure stdlib (``math.comb``);
    exact for the small ``n`` this tool ever sees (<= 175)."""

    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def _binom_cdf_at_most(n, k, p):
    """P(X <= k) for X ~ Binomial(n, p)."""

    if k >= n:
        return 1.0
    if k < 0:
        return 0.0
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))


def clopper_pearson(k, n, alpha=0.05, two_sided=True):
    """Exact (Clopper-Pearson) confidence bound(s) for a binomial rate
    ``k`` successes out of ``n`` trials, computed by bisecting the exact
    binomial CDF (no ``scipy``/incomplete-beta dependency; verified against
    textbook values -- n=10,k=5,two_sided -> [0.1871, 0.8129] -- and against
    the human's own worked check for this封: n=30,k=30,one-sided(alpha=0.05)
    -> lower == 0.05**(1/30) == 0.904966...).

    ``two_sided=True`` splits ``alpha`` into ``alpha/2`` per tail (the usual
    "95% interval" reading). ``two_sided=False`` uses the full ``alpha`` on
    the lower tail only (upper fixed at 1.0) -- the one-sided lower bound
    the human's worked example uses. Both are reported in this tool's
    output so the method is never ambiguous.
    """

    if n == 0:
        return (None, None)
    tail = alpha / 2 if two_sided else alpha
    if k <= 0:
        lower = 0.0
    else:
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2
            if _binom_cdf_at_least(n, k, mid) > tail:
                hi = mid
            else:
                lo = mid
        lower = lo
    if not two_sided:
        return (lower, 1.0)
    if k >= n:
        upper = 1.0
    else:
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2
            if _binom_cdf_at_most(n, k, mid) < tail:
                hi = mid
            else:
                lo = mid
        upper = hi
    return (lower, upper)


def is_detected(claim_present_after, post_state):
    """段 6 の人間の決定をそのまま: 混入後にその位置の Claim が 1 件も
    作られなかった場合は「止めなかった」(``False``)。作られた場合は、
    状態が ``GROUNDED`` でなければ検出(``True``) ― VALUE_MISMATCH /
    POINTER_NOT_FOUND / UNVERIFIABLE のどれでも検出に数える。"""

    if not claim_present_after:
        return False
    return post_state != "GROUNDED"


def aggregate_injections(injection_rows):
    """人間の指示(2026-10-08、3 回目の REVISE)1: ``main()`` の外へ切り出し
    た、混入の集計。1 件の判定行(``detected``・``unit_family`` を含む辞書)
    の列を受け取り、``(detected_total, not_stopped_total, family_tally)``
    を返す。``if detected: ... else: ...`` の分岐は**この関数の中**にある。

    ``detected`` が ``None``(混入そのものが失敗したエラー行)の場合は、
    族の ``n`` だけ増え、``detected``/``not_stopped`` のどちらにも数えない
    (``main()`` に元からあった挙動のまま ― エラー行は検出の判定対象で
    はない)。"""

    by_family = collections.OrderedDict()
    detected_total = 0
    not_stopped_total = 0
    for row in injection_rows:
        fam = row["unit_family"]
        fam_bucket = by_family.setdefault(fam, collections.OrderedDict([("n", 0), ("detected", 0), ("not_stopped", 0)]))
        fam_bucket["n"] += 1
        detected = row["detected"]
        if detected is None:
            continue
        if detected:
            detected_total += 1
            fam_bucket["detected"] += 1
        else:
            not_stopped_total += 1
            fam_bucket["not_stopped"] += 1

    family_tally = collections.OrderedDict()
    for fam, b in by_family.items():
        rate = (b["detected"] / b["n"]) if b["n"] else None
        family_tally[fam] = collections.OrderedDict(
            [("n", b["n"]), ("detected", b["detected"]), ("not_stopped", b["not_stopped"]), ("detection_rate", rate)]
        )
    return detected_total, not_stopped_total, family_tally


def _rate_block(k, n):
    """1 つの率(k/n)を Clopper-Pearson の両側/片側の幅つきで組む。"""

    if n == 0:
        return collections.OrderedDict([
            ("k", k), ("n", n), ("rate", None),
            ("ci_two_sided_95", [None, None]), ("ci_one_sided_lower_95", [None, None]),
            ("method", "Clopper-Pearson(exact, binomial CDF bisection)"),
        ])
    lo2, hi2 = clopper_pearson(k, n, alpha=0.05, two_sided=True)
    lo1, hi1 = clopper_pearson(k, n, alpha=0.05, two_sided=False)
    return collections.OrderedDict([
        ("k", k), ("n", n), ("rate", k / n),
        ("ci_two_sided_95", [lo2, hi2]),
        ("ci_one_sided_lower_95", [lo1, hi1]),
        ("method", "Clopper-Pearson(exact, binomial CDF bisection); "
                   "two_sided splits alpha=0.05 into 0.025/tail; "
                   "one_sided_lower uses the full alpha=0.05 on the lower tail "
                   "(matches the worked check: k=n=30 -> lower=0.05**(1/30)=0.904966...)"),
    ])


def build_detection_rates(detected_total, drawn_total, not_picked_up_n):
    """人間の指示(2026-10-08、3 回目の REVISE)1: ``main()`` の外へ切り出し
    た、率の組み立て。``classification_counts`` の ①(``not_picked_up_n``)・
    混入数(``drawn_total``)・検出数(``detected_total``)を**引数で受け取り**、
    ``{conditional_on_traceable_before_mixing: ..., per_definition_including_not_picked_up: ...,
    note: ...}`` を返す。``defn_n = 混入数 + ①の件数`` の足し算は**この関数
    の中**にある(``main()`` には無い)。

    ①=0 のときは両方の率(分母・分子とも)が一致する ― それは「計算してい
    ない」からではなく、①=0 だからそうなる(``①>0`` の合成入力の試験で、
    一致しなくなることを別に確かめている)。"""

    cond_n, cond_k = drawn_total, detected_total
    defn_n, defn_k = cond_n + not_picked_up_n, detected_total
    return collections.OrderedDict([
        ("conditional_on_traceable_before_mixing", _rate_block(cond_k, cond_n)),
        ("per_definition_including_not_picked_up", _rate_block(defn_k, defn_n)),
        ("note", (
            "条件付き = 検出数/混入数(混入できた現場だけ)。定義どおり = "
            "検出数/(混入数 + ①拾われなかった件数)。①の現場は混入していない"
            "(そもそも対応する Claim が元から無いので、混ぜても「止めなかった」"
            "になることが定義から保証されている ― 実行していない)。"
        )),
    ])


def load_material_text(material_dir, doc):
    path = os.path.join(material_dir, "%s.original.txt" % doc)
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def _tampered_plain_text(new_zb):
    """混入後の ZIP から、prepare_material.py と同じやり方(独立な
    strip_html + normalize_digits)で MD&A の平文を作る。D-8(human_sites の
    件数が混入の前後で変わらないか)を測るためだけに使う ― 採点には使わない。"""

    import prepare_material as PM  # measure/prepare_material.py (measure は sys.path にある)
    import html as _html

    entry, raw, start, end, _local = T.locate_mdna_raw(new_zb)
    body = _html.unescape(raw[start:end])
    text = N.normalize_digits(PM.strip_html(body))
    text = re.sub(r"[ \t　]+\n", "\n", text).strip() + "\n"
    return text


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--doc", required=True, choices=sorted(FROZEN_ZIP_SHA256))
    ap.add_argument("--profile", required=True, choices=sorted(V.PROFILES.keys()))
    ap.add_argument("--material", required=True, help="dir holding <doc>.original.txt (measure/material/xbrl)")
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--seed", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    # --- 1. 原本の ZIP を読み sha256 を照合 ---------------------------------
    path = E.cache_path(a.doc)
    zb = open(path, "rb").read()
    zip_sha = hashlib.sha256(zb).hexdigest()
    expected_sha = FROZEN_ZIP_SHA256[a.doc]
    if zip_sha != expected_sha:
        print(json.dumps({"error": "zip_sha_mismatch", "doc": a.doc, "got": zip_sha, "expected": expected_sha}))
        return 4

    # --- 2. 原本の基準線 ------------------------------------------------------
    baseline_rows = run_core_rows(zb, a.profile)
    baseline_by_id = {r["id"]: r for r in baseline_rows}
    baseline_state_tally = dict(collections.Counter(r["state"] for r in baseline_rows))
    baseline_num_sites = num_claim_sites(zb)
    if len(baseline_num_sites) != sum(1 for r in baseline_rows if r["id"].startswith("N")):
        # 列挙の再現が核とずれている ― 推測で進めず、はっきり止まる。
        print(json.dumps({
            "error": "num_claim_sites_mismatch", "doc": a.doc,
            "replicated": len(baseline_num_sites),
            "core_num_claims": sum(1 for r in baseline_rows if r["id"].startswith("N")),
        }))
        return 6

    # --- 3. 型 2 の現場の一覧(material text, refs=[]) ------------------------
    text = load_material_text(a.material, a.doc)
    text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    raw_sites = S.t2_sites(text, [])

    human_before = S.human_sites(text, "xbrl")

    # MD&A の raw 位置は 1 文書で 1 回だけ取る(現場ごとに毎回 ZIP を開き直さない)。
    mdna_error = None
    inner = None
    try:
        _entry, _raw, mstart, mend, _local = T.locate_mdna_raw(zb)
        inner = _raw[mstart:mend]
    except T.TamperError as ex:
        mdna_error = "%s: %s" % (type(ex).__name__, ex)

    stage = collections.OrderedDict([
        ("t2_sites_total", len(raw_sites)),
        ("html_ambiguous", 0),          # (a) 落ち: raw HTML で 0 件または 2 件以上
        ("html_usable", 0),
        ("baseline_no_claim", 0),       # (b) 落ち: 基準線に対応する Claim が 0 件(「原本で Claim にならない数」)
        ("baseline_ambiguous_claim", 0),  # (b) 落ち: 対応する Claim が 2 件以上(帰属が曖昧)
        ("baseline_not_grounded", 0),   # (b) 落ち: 対応する Claim が 1 件だが GROUNDED でない
        ("baseline_grounded", 0),       # (a)+(b) 通過。(c) は t2_sites が構成上保証
        ("eligible_pool", 0),
        ("requested_count", a.count),
        ("drawn_count", 0),
        ("shortfall", 0),
    ])

    site_rows = []
    eligible = []

    for site in raw_sites:
        tok = site["token"]
        # REVISE 2026-10-08(独立監査、1 回目)§5: 「道具の欠陥 X 件 / 材料の
        # 性質 Y 件」を推測でなく実測で仕分けるため、使えない現場は標本では
        # なく全件、material.original.txt 上の位置(文字オフセット)と前後の
        # 文字列を出力に残す(司令塔・監査が裏取りできるように)。
        ctx_a = max(0, tok.start - 40)
        ctx_b = min(len(text), tok.unit_end + 40)
        row = {
            "number_text": tok.text,
            "unit": tok.unit,
            "unit_family": N.unit_family(tok.unit) or "count",
            "siblings": list(site["siblings"]),
            "material_sentence_index": tok.sentence_index,
            "material_start": tok.start,
            "material_unit_end": tok.unit_end,
            "material_context": text[ctx_a:ctx_b],
        }
        if inner is None:
            row["gate_a"] = "error(%s)" % mdna_error
            row["gate_a_match_count"] = None
            stage["html_ambiguous"] += 1
            site_rows.append(row)
            continue
        try:
            T.find_unit_site(inner, tok.text, tok.unit)
        except T.AmbiguousSite as ex:
            row["gate_a"] = "ambiguous(%d)" % ex.match_count
            row["gate_a_match_count"] = ex.match_count
            stage["html_ambiguous"] += 1
            site_rows.append(row)
            continue
        row["gate_a"] = "unique"
        row["gate_a_match_count"] = 1
        stage["html_usable"] += 1

        cands = find_claim_sites_by_digits(baseline_num_sites, tok.text, tok.unit)
        if len(cands) == 0:
            row["gate_b"] = "no_claim"
            stage["baseline_no_claim"] += 1
            site_rows.append(row)
            continue
        if len(cands) >= 2:
            row["gate_b"] = "ambiguous(%d)" % len(cands)
            stage["baseline_ambiguous_claim"] += 1
            site_rows.append(row)
            continue
        base_site = cands[0]
        base_claim = baseline_by_id[base_site["id"]]
        row["baseline_claim_id"] = base_claim["id"]
        row["baseline_state"] = base_claim["state"]
        if base_claim["state"] != "GROUNDED":
            row["gate_b"] = "not_grounded"
            stage["baseline_not_grounded"] += 1
            site_rows.append(row)
            continue
        row["gate_b"] = "grounded"
        stage["baseline_grounded"] += 1
        eligible.append({"row": row, "token": tok, "siblings": site["siblings"], "base_claim": base_claim})
        site_rows.append(row)

    stage["eligible_pool"] = len(eligible)

    # --- 4'. 人間の追加指示(2026-10-08、2 回目の REVISE): ①〜④ の分類 ------
    # (a) HTML の一意性より先に (b) 対応づけ(拾われたか/辿れていたか)を見る。
    # stage(上記、(a) を先に見る旧い順序)はそのまま残し、比較できるように
    # しておく。実際に混ぜる母数は、こちらの新しい順序の ④b から取る。
    classification_counts = collections.OrderedDict([
        ("1_not_picked_up", 0),
        ("2_ambiguous_correspondence", 0),
        ("3_not_grounded_before_mixing", 0),
        ("3_not_grounded_before_mixing_by_state", collections.OrderedDict(
            [("POINTER_NOT_FOUND", 0), ("VALUE_MISMATCH", 0), ("UNVERIFIABLE", 0)])),
        ("4a_html_ambiguous", 0),
        ("4b_eligible", 0),
    ])
    eligible2 = []
    # site_rows は raw_sites と添字が 1:1(同じループ順で作られた)。
    # classify_site は 1 現場につき 1 回だけ呼ぶ。
    for row, site in zip(site_rows, raw_sites):
        tok = site["token"]
        cls = classify_site(tok, site["siblings"], baseline_num_sites, baseline_by_id, inner)
        bucket = cls["bucket"]
        classification_counts[bucket] += 1
        if bucket == "3_not_grounded_before_mixing":
            classification_counts["3_not_grounded_before_mixing_by_state"][cls["baseline_state"]] += 1
        if bucket == "4b_eligible":
            base_claim2 = baseline_by_id[cls["baseline_claim_id"]]
            eligible2.append({"token": tok, "siblings": site["siblings"], "base_claim": base_claim2})
        row["classification_bucket"] = bucket
        row["classification_claim_candidates"] = cls["claim_candidates"]
        if "baseline_claim_id" in cls:
            row["classification_baseline_claim_id"] = cls["baseline_claim_id"]
            row["classification_baseline_state"] = cls["baseline_state"]
        if "html_match_count" in cls:
            row["classification_html_match_count"] = cls["html_match_count"]

    classification_total = (
        classification_counts["1_not_picked_up"]
        + classification_counts["2_ambiguous_correspondence"]
        + classification_counts["3_not_grounded_before_mixing"]
        + classification_counts["4a_html_ambiguous"]
        + classification_counts["4b_eligible"]
    )
    classification_counts["total"] = classification_total
    classification_counts["t2_sites_total"] = len(raw_sites)
    classification_counts["sums_to_total_check"] = (classification_total == len(raw_sites))

    structural_check = structural_check_for_bucket1(zb, raw_sites)

    # --- 5. 種で count 件を抽選(決定的)。母数は新しい分類の ④b。----------
    drawn, new_units, k = draw_sites(eligible2, a.seed, a.doc, a.count)
    stage["drawn_count"] = k
    stage["shortfall"] = a.count - k

    # --- 6. 1 件ごとに混入 ZIP を作り、P7 + Core で回す ----------------------
    injection_rows = []
    human_after_mismatches = []

    for d, new_unit in zip(drawn, new_units):
        tok, siblings, base_claim = d["token"], d["siblings"], d["base_claim"]
        fam = N.unit_family(tok.unit) or "count"

        try:
            new_zb = T.tamper_unit_word(zb, tok.text, tok.unit, new_unit)
        except T.TamperError as ex:
            # 選定の際に同じ (inner, text, unit) で一意性を確かめているので
            # ここに来るのは想定外。クラッシュさせず、行に理由を残して次へ。
            injection_rows.append({
                "number_text": tok.text, "unit_before": tok.unit, "unit_after": new_unit, "unit_family": fam,
                "baseline_claim_id": base_claim["id"], "baseline_state": base_claim["state"],
                "error": "%s: %s" % (type(ex).__name__, ex), "detected": None,
            })
            continue

        new_rows = run_core_rows(new_zb, a.profile)
        new_by_id = {r["id"]: r for r in new_rows}
        new_num_sites = num_claim_sites(new_zb)
        content_after = find_claim_sites_by_digits(new_num_sites, tok.text, new_unit)

        post_claim = new_by_id.get(base_claim["id"])
        claim_present_after = post_claim is not None
        post_state = post_claim["state"] if post_claim else None
        id_cross_check_agrees = (
            claim_present_after and len(content_after) == 1 and content_after[0]["id"] == base_claim["id"]
        )

        detected = is_detected(claim_present_after, post_state)

        human_after = None
        human_mismatch = None
        try:
            tampered_text = _tampered_plain_text(new_zb)
            human_after = len(S.human_sites(tampered_text, "xbrl"))
            if human_after != len(human_before):
                human_mismatch = {"before": len(human_before), "after": human_after}
                human_after_mismatches.append({
                    "number_text": tok.text, "unit_before": tok.unit, "unit_after": new_unit,
                    "before": len(human_before), "after": human_after,
                })
        except T.TamperError as ex:
            human_mismatch = "error(%s)" % ex

        injection_rows.append({
            "number_text": tok.text,
            "unit_before": tok.unit,
            "unit_after": new_unit,
            "unit_family": fam,
            "baseline_claim_id": base_claim["id"],
            "baseline_state": base_claim["state"],
            "claim_present_after": claim_present_after,
            "post_claim_id": post_claim["id"] if post_claim else None,
            "post_unit": post_claim["unit"] if post_claim else None,
            "post_state": post_state,
            "post_recomputed": post_claim["recomputed"] if post_claim else None,
            "post_reason": post_claim["reason"] if post_claim else None,
            "content_match_after_count": len(content_after),
            "id_cross_check_agrees": id_cross_check_agrees,
            "human_sites_before": len(human_before),
            "human_sites_after": human_after,
            "human_sites_mismatch": human_mismatch,
            "detected": detected,
        })

    # --- 人間の指示(2026-10-08、3 回目の REVISE)1: main() の外(モジュール
    # レベルの純粋関数)で集計・率の組み立てを行う。main() はここから先、
    # 呼ぶだけ。------------------------------------------------------------
    detected_total, not_stopped_total, family_tally = aggregate_injections(injection_rows)
    overall_rate = (detected_total / len(drawn)) if drawn else None
    not_picked_up_n = classification_counts["1_not_picked_up"]
    detection_rates = build_detection_rates(detected_total, len(drawn), not_picked_up_n)

    excluded_table = collections.OrderedDict([
        ("location_cannot_be_pinned_down", collections.OrderedDict([
            ("reason", "場所を特定できない(② 主張の対応が曖昧 ― digits だけでは "
                       "どちらの出現が主張になったか区別できない / ④a HTML で一意で "
                       "ない ― 道具の限界)"),
            ("ambiguous_correspondence_2plus_claims", classification_counts["2_ambiguous_correspondence"]),
            ("html_not_unique_among_grounded", classification_counts["4a_html_ambiguous"]),
            ("total", classification_counts["2_ambiguous_correspondence"] + classification_counts["4a_html_ambiguous"]),
        ])),
        ("not_grounded_before_mixing", collections.OrderedDict([
            ("reason", "混ぜる前から辿れていない(③ 対応する Claim は 1 件だが GROUNDED でない)"),
            ("total", classification_counts["3_not_grounded_before_mixing"]),
            ("by_state", classification_counts["3_not_grounded_before_mixing_by_state"]),
        ])),
        ("not_picked_up", collections.OrderedDict([
            ("reason", "拾われなかった(① 対応する Claim が 0 件) ― これは除外では"
                       "なく、定義どおりの検出率の分母に入れた件数"),
            ("total", not_picked_up_n),
        ])),
    ])

    headline = "型2のみ・開発に使った3書類での検出率"

    out = collections.OrderedDict([
        ("tool", "run_detection_t2"),
        ("headline", headline),
        ("doc", a.doc),
        ("profile", a.profile),
        ("seed", a.seed),
        ("zip_sha256", zip_sha),
        ("material_text_sha256", text_sha256),
        ("baseline_claims_total", len(baseline_rows)),
        ("baseline_state_tally", baseline_state_tally),
        ("stage", stage),
        ("classification", classification_counts),
        ("structural_check_for_bucket1", structural_check),
        ("sites", site_rows),
        ("human_sites_before_count", len(human_before)),
        ("human_sites_after_mismatches", human_after_mismatches),
        ("injections", injection_rows),
        ("detected_total", detected_total),
        ("not_stopped_total", not_stopped_total),
        ("drawn_total", len(drawn)),
        ("detection_rate", overall_rate),
        ("detection_rates", detection_rates),
        ("excluded_table", excluded_table),
        ("family_tally", family_tally),
    ])

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)

    print(json.dumps({
        "doc": a.doc, "profile": a.profile, "headline": headline, "stage": stage,
        "classification": classification_counts,
        "drawn_total": len(drawn), "detected_total": detected_total, "not_stopped_total": not_stopped_total,
        "detection_rate": overall_rate, "detection_rates": detection_rates, "family_tally": family_tally,
        "human_sites_before": len(human_before), "human_sites_after_mismatches": len(human_after_mismatches),
    }, ensure_ascii=False, indent=1))
    print("written:", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
