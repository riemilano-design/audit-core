# -*- coding: utf-8 -*-
"""型 3(原文に無い数)の「主張にならなかった件数」を 1 書類ぶん測る計器。

封 ``audit-core/docs/DETECTION_T1_T3_PLAN_2026-10-08.md`` 第 3 部の定義・
段を実装する。``run_detection_t2.py``(型 2)は 1 行も変えず、監査済みの
部品(``num_claim_sites`` / ``find_claim_sites_by_digits`` / ``run_core_rows``
/ ``clopper_pearson``)を import して使い回す。``measure/inject.py: build_t3``
/ ``measure/lib/sites.py`` も import して使い回す(作り直さない)。

型 2・型 1 から引き継がないもの(封 §3-1):

- ③「混ぜる前から辿れていない」は定義しない(「前」が無い)。
- ②「対応が曖昧」も起きない(挿入する文は自分で書く)。
- 条件付きの率は定義しない。**率は 1 つだけ**(分母 = 挿入した文の数)。

段の順番:

1. 原本の ZIP を読み sha256 を照合する(違えば止まる)。
2. 原本を P7 + Core で回す(``run_detection_t2.run_core_rows``)。基準線の
   Claim の列(順序つき)と ``num_claim_sites`` の digits 集合を取る。
3. MD&A の raw HTML から、句点の直後でタグの内側でない挿入点を列挙する
   (``tamper_insert.find_insertion_points``)。
4. 使える主語(``lib.sites.ABSENT_TEMPLATES["xbrl"]`` のうち本文/参照一覧の
   ラベルに実在しないもの、最大 6)を列挙する。
5. 種で ``min(--count, 使える主語の数, 挿入点の数)`` 件を抽選し、文ごとに
   別の主語・別の値を割り当てる(``tamper_insert.build_sentence`` ->
   ``inject.build_t3``)。
6. 1 件ごとに(1 ZIP に挿入は 1 件だけ)、原本 ZIP に挿入 -> P7 + Core で回す。
   挿入した値+「百万円」の digits が ``num_claim_sites`` に新しく現れたかを
   見る(値だけでなく「基準線に無かったこと」も確かめる -- 値だけでは、
   偶然同じ値の既存の主張と区別できない)。
7. 「主張にならなかった件数」(= 止めなかった)を見出しの数として出す。
   Core の判定(POINTER_NOT_FOUND/UNVERIFIABLE/VALUE_MISMATCH/GROUNDED)は
   内訳として添える。不変条件(Claim 総数が原本+k、他の主張の状態が不変)
   を 1 件ごとに確かめる。

通信はしない。EDINET には触れない。API キーは使わない。

Usage::

    python3 fixtures/xbrl/run_detection_t3.py --doc S100Z4B6 --profile P7 \\
        --count 6 --seed audit-core-detection-t3-2026-10-08-c73a --out <path>
"""

import argparse
import collections
import hashlib
import io
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "measure"))
sys.path.insert(0, HERE)

from adapters.xbrl import edinet as E, vocabulary as V  # noqa: E402
import run_detection_t2 as T2  # noqa: E402
import tamper_insert as TI  # noqa: E402

# 封(DETECTION_T1_T3_PLAN_2026-10-08.md 第 1 部「凍結するもの」)の表。
# run_detection_t2.py の同名の辞書と値は同じだが、ファイルを分けるため
# ここに独立に持つ(run_detection_t2.py は 1 行も変えない)。
FROZEN_ZIP_SHA256 = {
    "S100Z4Q1": "0731a291f10af5dd207e05d54df8e2b5dc34e79a84de94af1c1a5d4e207228f6",
    "S100Z4B6": "d617b6e1807c8aa6d2b1269f6b25ff57a6a71dbf683020f1859d2d4a04c02d26",
    "S100YMFV": "4a5982e7447d6e0614c6ad12e7c091d462ca61a0128c2ce2af957a8bdfe1d52c",
}


def row_fingerprint(row):
    """id を含まない、1 Claim の内容だけの比較用タプル。挿入は後続の Claim
    の id(N%03d/T%03d の番号)を必ずずらすので、不変条件(「他の主張の状態
    が 1 件も変わらない」)は id では比較できない。内容(unit・value・state・
    recomputed・reason)の列を順序つきで比べる。"""

    return (row["id"][0], row["unit"], row["state"], row["recomputed"], row["reason"])


def identify_inserted_claim(new_num_sites, baseline_digits_set, value_text, unit):
    """挿入した文が主張になったかを、**値だけで判定しない**(封 §3-2)。

    ``new_num_sites`` の digits(= 値+単位の文字列。``num_claim_sites`` の
    仕様)が ``value_text + unit`` と一致する候補を探すところまでは値の
    一致だが、その digits 文字列が**挿入する前の基準線にも既に在ったか**
    (``baseline_digits_set``)を必ず確かめる。無かった(= このドキュメント
    でその digits 文字列が初めて現れた)場合に限り「同定できた」とする。
    基準線にも同じ digits があれば、どちらが挿入した方か値だけでは言えない
    ので「同定できなかった」(``became_claim=None``)として分ける。

    戻り値 ``(became_claim, identified, preexisting_digits, inserted_ids)``:

    - 候補が 0 件: ``(False, None, False, set())``(主張にならなかった = 止めなかった)
    - 候補はあるが digits が基準線にも在る: ``(None, False, True, set())``(同定できない)
    - 候補があり、基準線には無い: ``(True, True, False, {候補の id 全部})``
      (``matched_claim_count>=2`` なら F-5 の「2 つ以上の主張になった」件)
    """

    digits_str = value_text + unit
    preexisting_digits = any(d == digits_str for d, _u in baseline_digits_set)
    candidates = T2.find_claim_sites_by_digits(new_num_sites, value_text, unit)
    candidate_ids = {c["id"] for c in candidates}

    if not candidates:
        return False, None, preexisting_digits, set()
    if preexisting_digits:
        return None, False, preexisting_digits, set()
    return True, True, preexisting_digits, candidate_ids


def check_other_claims_unchanged(baseline_rows, new_rows, inserted_ids):
    """挿入した Claim(``inserted_ids``)を取り除いた ``new_rows`` の内容の列
    (順序つき、id を見ない)が、``baseline_rows`` の内容の列と完全に一致
    するか。一致しなければ、最初に食い違った位置を返す。"""

    remaining = [r for r in new_rows if r["id"] not in inserted_ids]
    base_fp = [row_fingerprint(r) for r in baseline_rows]
    new_fp = [row_fingerprint(r) for r in remaining]
    if base_fp == new_fp:
        return True, None
    n = min(len(base_fp), len(new_fp))
    first_mismatch = None
    for i in range(n):
        if base_fp[i] != new_fp[i]:
            first_mismatch = {"index": i, "baseline": list(base_fp[i]), "new": list(new_fp[i])}
            break
    if first_mismatch is None:
        first_mismatch = {"index": n, "note": "length differs beyond common prefix",
                           "baseline_len": len(base_fp), "new_len": len(new_fp)}
    return False, first_mismatch


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--doc", required=True, choices=sorted(FROZEN_ZIP_SHA256))
    ap.add_argument("--profile", required=True, choices=sorted(V.PROFILES.keys()))
    ap.add_argument("--material", default=os.path.join(ROOT, "measure", "material", "xbrl"),
                     help="dir holding <doc>.original.txt / <doc>.reference_numbers.json")
    ap.add_argument("--count", type=int, default=6)
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

    text_path = os.path.join(a.material, "%s.original.txt" % a.doc)
    with io.open(text_path, encoding="utf-8") as fh:
        text = fh.read()
    text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    refs_path = os.path.join(a.material, "%s.reference_numbers.json" % a.doc)
    with io.open(refs_path, encoding="utf-8") as fh:
        refs = json.load(fh)["refs"]
    with io.open(refs_path, "rb") as fh:
        refs_sha256 = hashlib.sha256(fh.read()).hexdigest()

    # --- 2. 原本の基準線(型 2 の計器を使い回す) -------------------------------
    baseline_rows = T2.run_core_rows(zb, a.profile)
    baseline_claims_total = len(baseline_rows)
    baseline_state_tally = dict(collections.Counter(r["state"] for r in baseline_rows))
    baseline_num_sites = T2.num_claim_sites(zb)
    baseline_digits_set = {(s["digits"], s["unit"]) for s in baseline_num_sites}

    # --- 3. 挿入点(raw HTML、句点の直後・タグの外) ---------------------------
    try:
        _entry, _raw, mstart, mend, _local = TI.locate_mdna_raw(zb)
        inner = _raw[mstart:mend]
        mdna_error = None
    except TI.TamperError as ex:
        inner = None
        mdna_error = "%s: %s" % (type(ex).__name__, ex)

    insertion_points = TI.find_insertion_points(inner) if inner is not None else []

    # --- 4. 使える主語 ---------------------------------------------------------
    templates = TI.usable_templates(text, refs, "xbrl")
    all_subjects = [subj for subj, _tpl in TI.S.ABSENT_TEMPLATES.get("xbrl", [])]
    usable_subjects = [subj for subj, _tpl in templates]
    withheld_subjects = [s for s in all_subjects if s not in usable_subjects]

    # --- 5. 種で min(count, 使える主語, 挿入点) 件を抽選(決定的) -------------
    rng = random.Random(a.seed + ":" + a.doc)
    k = min(a.count, len(templates), len(insertion_points))
    shortfall = a.count - k
    idx = sorted(rng.sample(range(len(insertion_points)), k)) if k else []
    drawn_points = [insertion_points[i] for i in idx]

    used_subjects, used_values = set(), set()
    built_sentences = []
    for pos in drawn_points:
        built = TI.build_sentence(templates, refs, rng, used_subjects, used_values)
        if built is None:
            break
        built_sentences.append((pos, built))

    # --- 6. 1 件ごとに挿入し、P7 + Core で回す ---------------------------------
    rows_out = []
    invariant_violations = []
    for pos, built in built_sentences:
        value_text = str(int(built["new_value"]))
        unit = "百万円"
        try:
            new_zb = TI.insert_sentence(zb, pos, built["replacement"])
        except TI.TamperError as ex:
            rows_out.append({
                "position": pos, "subject": built["detail"]["fabricated_subject"],
                "value": built["new_value"], "sentence": built["replacement"],
                "error": "%s: %s" % (type(ex).__name__, ex), "became_claim": None,
            })
            continue

        new_rows = T2.run_core_rows(new_zb, a.profile)
        new_num_sites = T2.num_claim_sites(new_zb)
        became_claim, identified, preexisting_digits, inserted_ids = identify_inserted_claim(
            new_num_sites, baseline_digits_set, value_text, unit
        )
        new_by_id = {r["id"]: r for r in new_rows}

        post_states = [new_by_id[i]["state"] for i in inserted_ids if i in new_by_id]
        post_reasons = [new_by_id[i]["reason"] for i in inserted_ids if i in new_by_id]

        invariant_total_ok = (len(new_rows) == baseline_claims_total + len(inserted_ids))
        other_ok, first_mismatch = check_other_claims_unchanged(baseline_rows, new_rows, inserted_ids)
        if not (invariant_total_ok and other_ok):
            invariant_violations.append({
                "position": pos, "subject": built["detail"]["fabricated_subject"],
                "invariant_total_ok": invariant_total_ok,
                "baseline_claims_total": baseline_claims_total, "new_claims_total": len(new_rows),
                "inserted_ids_count": len(inserted_ids),
                "other_claims_unchanged": other_ok, "first_mismatch": first_mismatch,
            })

        rows_out.append({
            "position": pos,
            "subject": built["detail"]["fabricated_subject"],
            "value": built["new_value"],
            "sentence": built["replacement"],
            "became_claim": became_claim,
            "identified": identified,
            "preexisting_digits_collision": preexisting_digits,
            "matched_claim_ids": sorted(inserted_ids),
            "matched_claim_count": len(inserted_ids),
            "post_states": post_states,
            "post_reasons": post_reasons,
            "invariant_total_ok": invariant_total_ok,
            "other_claims_unchanged": other_ok,
        })

    # --- 7. 集計 ---------------------------------------------------------------
    inserted_total = len(rows_out)
    not_claimed = sum(1 for r in rows_out if r["became_claim"] is False)
    became_claim_total = sum(1 for r in rows_out if r["became_claim"] is True)
    unidentified_total = sum(1 for r in rows_out if r["became_claim"] is None and "error" not in r)
    error_total = sum(1 for r in rows_out if r.get("became_claim") is None and "error" in r)

    state_tally_of_inserted = collections.Counter()
    multi_claim_rows = 0
    for r in rows_out:
        if r["became_claim"] is True:
            for st in r["post_states"]:
                state_tally_of_inserted[st] += 1
            if r["matched_claim_count"] >= 2:
                multi_claim_rows += 1

    lo2, hi2 = T2.clopper_pearson(not_claimed, inserted_total, alpha=0.05, two_sided=True) if inserted_total else (None, None)
    lo1, hi1 = T2.clopper_pearson(not_claimed, inserted_total, alpha=0.05, two_sided=False) if inserted_total else (None, None)
    not_claimed_rate = collections.OrderedDict([
        ("k_not_claimed", not_claimed),
        ("n_inserted", inserted_total),
        ("rate", (not_claimed / inserted_total) if inserted_total else None),
        ("ci_two_sided_95", [lo2, hi2]),
        ("ci_one_sided_lower_95", [lo1, hi1]),
        ("note", "分母 = 挿入した文の数。条件付き/定義どおりの 2 本立てはしない(封 §3-1: 「前」が無い)。"),
    ])

    headline = "型3のみ・開発に使った3書類で、偽の文が主張にならなかった件数"

    out = collections.OrderedDict([
        ("tool", "run_detection_t3"),
        ("headline", headline),
        ("doc", a.doc),
        ("profile", a.profile),
        ("seed", a.seed),
        ("count_requested", a.count),
        ("zip_sha256", zip_sha),
        ("material_text_sha256", text_sha256),
        ("reference_numbers_sha256", refs_sha256),
        ("baseline_claims_total", baseline_claims_total),
        ("baseline_state_tally", baseline_state_tally),
        ("insertion_points_total", len(insertion_points)),
        ("usable_subjects", usable_subjects),
        ("withheld_subjects_present_in_text_or_labels", withheld_subjects),
        ("drawn_count", k),
        ("shortfall", shortfall),
        ("rows", rows_out),
        ("inserted_total", inserted_total),
        ("not_claimed_total", not_claimed),
        ("became_claim_total", became_claim_total),
        ("unidentified_total", unidentified_total),
        ("error_total", error_total),
        ("not_claimed_rate", not_claimed_rate),
        ("core_state_breakdown_of_claimed_insertions", dict(state_tally_of_inserted)),
        ("multi_claim_rows", multi_claim_rows),
        ("invariant_violations", invariant_violations),
    ])

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)

    print(json.dumps({
        "doc": a.doc, "profile": a.profile, "headline": headline,
        "insertion_points_total": len(insertion_points), "usable_subjects": usable_subjects,
        "withheld_subjects": withheld_subjects, "drawn_count": k, "shortfall": shortfall,
        "inserted_total": inserted_total, "not_claimed_total": not_claimed,
        "became_claim_total": became_claim_total, "unidentified_total": unidentified_total,
        "error_total": error_total, "not_claimed_rate": not_claimed_rate,
        "core_state_breakdown": dict(state_tally_of_inserted), "multi_claim_rows": multi_claim_rows,
        "invariant_violations": len(invariant_violations),
    }, ensure_ascii=False, indent=1))
    print("written:", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
