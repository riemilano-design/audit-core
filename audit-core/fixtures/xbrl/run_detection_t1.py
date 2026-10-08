# -*- coding: utf-8 -*-
"""型 1(数字の置換)の検出率を 1 書類ぶん測る計器。

封 ``audit-core/docs/DETECTION_T1_T3_PLAN_2026-10-08.md`` 第 2 部の定義・
段を実装する。``run_detection_t2.py``(型 2)は 1 行も変えず、監査済みの
部品(``num_claim_sites`` / ``find_claim_sites_by_digits`` /
``clopper_pearson`` / ``build_detection_rates`` / ``aggregate_injections``)
を import して使い回す。

段の順番(封 §2 のとおり):

1. 原本の ZIP を読み sha256 を照合する(違えば止まる)。
2. 原本を P7 + Core で回す(``run_core_rows_params`` -- ``run_detection_t2.
   run_core_rows`` と同じ 8 行の組み立てだが、``Contract.params`` も読む)。
3. **現場 = 原本の判定で GROUNDED な「数の主張」**(id が ``N`` で始まるもの)。
   ``measure/lib/sites.t1_sites`` は使わない(封 §2-1: 既定の定義では現場が
   節番号・注番号などを含み、率が同語反復になる)。
4. 現場ごとに門を通す: (a) 平文の「数字+単位」の形か (b) HTML で一意に
   特定できるか (c) 許容が読めるか (d) 層を割り当てられるか。
5. 層 (a)(b)(c)(a') ごとに ``--per-stratum`` 件を種で抽選(決定的)。
6. 1 件ごとに混入 ZIP を作り、P7 + Core で回し、同じ Claim の状態を見る。
7. 層ごとの検出率 + 条件付き/定義どおりの 2 率(Clopper-Pearson の幅つき)
   + (a') は別の箱(分母に入れない)+ 外した件数の表、を 1 本の JSON に書く。

通信はしない(ZIP は ``~/.cache/audit-core/edinet/`` から)。EDINET には
触れない。API キーは使わない。

Usage::

    python3 fixtures/xbrl/run_detection_t1.py --doc S100Z4B6 --profile P7 \\
        --per-stratum 6 --seed audit-core-detection-t1-2026-10-08-5b2e --out <path>
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

import audit_core as core  # noqa: E402
from adapters.xbrl import edinet as E, instance as I, recipes as R, resolve as RV, registry_setup as RS, vocabulary as V  # noqa: E402
import run_detection_t2 as T2  # noqa: E402
import tamper_value as TV  # noqa: E402

# 封(DETECTION_T1_T3_PLAN_2026-10-08.md 第 1 部「凍結するもの」)の表。
# run_detection_t2.py の同名の辞書と値は同じだが、ファイルを分けるため
# ここに独立に持つ(run_detection_t2.py は 1 行も変えない)。
FROZEN_ZIP_SHA256 = {
    "S100Z4Q1": "0731a291f10af5dd207e05d54df8e2b5dc34e79a84de94af1c1a5d4e207228f6",
    "S100Z4B6": "d617b6e1807c8aa6d2b1269f6b25ff57a6a71dbf683020f1859d2d4a04c02d26",
    "S100YMFV": "4a5982e7447d6e0614c6ad12e7c091d462ca61a0128c2ce2af957a8bdfe1d52c",
}

LAYERS = ["a_just_outside", "b_one_digit", "c_order_of_magnitude"]
LAYER_APRIME = "aprime_within_tolerance"


def run_core_rows_params(zb, profile_name):
    """``run_detection_t2.run_core_rows`` と同じ 8 行の組み立て(重複はその
    ファイルの docstring と同じ理由で意図的 ― run_core_path.py は CLI 単体の
    計器であり依存してよい「核」ではない)。追加で ``Contract.params`` /
    ``comparator`` も読む(型 1 の層の組み立てに要る。型 2 の計器は読まない
    ので、そちらを 1 行も変えずに済ませるには、ここで独立に読むしかない)。"""

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
            "value": c.value,
            "state": rs.state.value,
            "recomputed": rs.recomputed,
            "reason": rs.reason,
            "comparator": rc.contract.comparator if rc.contract else None,
            "params": dict(rc.contract.params) if (rc.contract and rc.contract.params) else None,
        })
    return rows


def classify_claim(row, digits):
    """段 4 の門 (a)(b)(c) を 1 件ぶん通す。``row`` は
    :func:`run_core_rows_params` が作る辞書(``state=="GROUNDED"`` 済みの
    行のみ渡される前提)。戻り値は ``dict``(``gate_a``/``gate_b``/``gate_c``
    と、通った場合の ``number_text``/``unit``/``params``)。"""

    out = {"claim_id": row["id"], "digits": digits}
    if not TV.is_plain_number_unit(digits):
        out["gate_a"] = "not_plain_number_unit"
        return out
    sign, number_text, unit = TV.parse_plain_number_unit(digits)
    out["gate_a"] = "plain"
    out["sign"] = sign
    out["number_text"] = number_text
    out["unit"] = unit
    return out


def build_layer_summary(injection_rows_by_layer, shortfall_by_layer, layer_build_excluded):
    """人間の指示(2026-10-08)1 と同じ形: ``main()`` の外へ切り出した、層
    ごとの検出率・合計・(a') の箱の組み立て。``main()`` はこれを呼ぶだけ。

    **(a') はここで初めて検出率の分母から外される**(封 §2-2)。層
    ``LAYERS``(a/b/c)だけを ``T2.aggregate_injections``/``T2.
    build_detection_rates`` に渡し、``LAYER_APRIME`` の行は
    ``layer_rates``/``combined_rates`` のどちらにも混ぜない(試験:
    ``aprime`` 側に何件足しても ``layer_rates``/``combined_rates`` の
    ``n``/``k`` が変わらないこと)。"""

    layer_rates = collections.OrderedDict()
    combined_detected = 0
    combined_drawn = 0
    for layer in LAYERS:
        rows = injection_rows_by_layer.get(layer, [])
        detected_total, not_stopped_total, _fam = T2.aggregate_injections(
            [{"unit_family": "layer", "detected": r.get("detected")} for r in rows]
        )
        drawn_n = len(rows)
        combined_detected += detected_total
        combined_drawn += drawn_n
        layer_rates[layer] = collections.OrderedDict([
            ("drawn", drawn_n),
            ("shortfall", shortfall_by_layer.get(layer)),
            ("detected", detected_total),
            ("not_stopped", not_stopped_total),
            ("rates", T2.build_detection_rates(detected_total, drawn_n, 0)),
        ])

    combined_note = (
        "合計 = 層 (a)(b)(c) を単純に足した数。層の混ぜ方(どれだけ遠くへ"
        "置換したか)で動く数であり、Core の性質ではない。層ごとの率を主とする。"
    )
    combined_rates = T2.build_detection_rates(combined_detected, combined_drawn, 0)

    aprime_rows = injection_rows_by_layer.get(LAYER_APRIME, [])
    aprime_box = collections.OrderedDict([
        ("note", "許容の内側(契約が同じ値と決めている範囲)。検出率の分母には入れない。"),
        ("drawn", len(aprime_rows)),
        ("shortfall", shortfall_by_layer.get(LAYER_APRIME)),
        ("cannot_build_or_collides", layer_build_excluded.get(LAYER_APRIME)),
        ("stayed_grounded", sum(1 for r in aprime_rows if r.get("post_state") == "GROUNDED")),
        ("not_grounded", sum(1 for r in aprime_rows if r.get("post_state") not in (None, "GROUNDED"))),
        ("not_stopped_i.e._no_claim_at_all", sum(1 for r in aprime_rows if r.get("claim_present_after") is False)),
        ("rows", aprime_rows),
    ])

    return {
        "layer_rates": layer_rates,
        "combined_note": combined_note,
        "combined_detected": combined_detected,
        "combined_drawn": combined_drawn,
        "combined_rates": combined_rates,
        "aprime_box": aprime_box,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--doc", required=True, choices=sorted(FROZEN_ZIP_SHA256))
    ap.add_argument("--profile", required=True, choices=sorted(V.PROFILES.keys()))
    ap.add_argument("--material", default=os.path.join(ROOT, "measure", "material", "xbrl"),
                     help="dir holding <doc>.reference_numbers.json (default: measure/material/xbrl)")
    ap.add_argument("--per-stratum", type=int, default=6)
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

    refs_path = os.path.join(a.material, "%s.reference_numbers.json" % a.doc)
    with io.open(refs_path, encoding="utf-8") as fh:
        refs_doc = json.load(fh)
    refs = refs_doc["refs"]
    with io.open(refs_path, "rb") as fh:
        refs_sha256 = hashlib.sha256(fh.read()).hexdigest()

    # --- 2. 原本の基準線(params つき) -----------------------------------------
    baseline_rows = run_core_rows_params(zb, a.profile)
    baseline_by_id = {r["id"]: r for r in baseline_rows}
    baseline_state_tally = dict(collections.Counter(r["state"] for r in baseline_rows))
    baseline_claims_total = len(baseline_rows)
    baseline_grounded_total = baseline_state_tally.get("GROUNDED", 0)

    baseline_num_sites = T2.num_claim_sites(zb)
    if len(baseline_num_sites) != sum(1 for r in baseline_rows if r["id"].startswith("N")):
        print(json.dumps({
            "error": "num_claim_sites_mismatch", "doc": a.doc,
            "replicated": len(baseline_num_sites),
            "core_num_claims": sum(1 for r in baseline_rows if r["id"].startswith("N")),
        }))
        return 6
    num_sites_by_id = {s["id"]: s for s in baseline_num_sites}

    # --- 3. 現場 = GROUNDED な数の主張(id が N で始まる) --------------------
    grounded_num_rows = [r for r in baseline_rows if r["id"].startswith("N") and r["state"] == "GROUNDED"]

    try:
        _entry, _raw, mstart, mend, _local = TV.locate_mdna_raw(zb)
        inner = _raw[mstart:mend]
        mdna_error = None
    except TV.TamperError as ex:
        inner = None
        mdna_error = "%s: %s" % (type(ex).__name__, ex)

    stage = collections.OrderedDict([
        ("grounded_num_claims_total", len(grounded_num_rows)),
        ("gate_a_not_plain_number_unit", 0),
        ("gate_a_plain", 0),
        ("gate_b_html_ambiguous", 0),
        ("gate_b_html_unique", 0),
        ("gate_c_tolerance_unreadable", 0),
        ("gate_c_tolerance_readable", 0),
    ])

    classified = []  # 1 行 / claim。どの門まで通ったかを必ず記録する。
    for row in grounded_num_rows:
        site = num_sites_by_id.get(row["id"])
        digits = site["digits"] if site else None
        c = classify_claim(row, digits)
        c["baseline_state"] = row["state"]
        c["baseline_unit"] = row["unit"]
        c["baseline_value"] = row["value"]
        if c["gate_a"] != "plain":
            stage["gate_a_not_plain_number_unit"] += 1
            classified.append(c)
            continue
        stage["gate_a_plain"] += 1

        if inner is None:
            c["gate_b"] = "error(%s)" % mdna_error
            c["gate_b_match_count"] = None
            stage["gate_b_html_ambiguous"] += 1
            classified.append(c)
            continue
        try:
            TV.find_number_site(inner, c["number_text"], c["unit"])
        except TV.AmbiguousSite as ex:
            c["gate_b"] = "ambiguous(%d)" % ex.match_count
            c["gate_b_match_count"] = ex.match_count
            stage["gate_b_html_ambiguous"] += 1
            classified.append(c)
            continue
        c["gate_b"] = "unique"
        c["gate_b_match_count"] = 1
        stage["gate_b_html_unique"] += 1

        params = row["params"]
        tol, tol_source = TV.tolerance_base_of(params)
        if tol is None:
            c["gate_c"] = "unreadable"
            stage["gate_c_tolerance_unreadable"] += 1
            classified.append(c)
            continue
        c["gate_c"] = "readable"
        c["tolerance_base"] = tol
        c["tolerance_source"] = tol_source
        c["params"] = params
        stage["gate_c_tolerance_readable"] += 1
        classified.append(c)

    eligible_base = [c for c in classified if c.get("gate_c") == "readable"]

    # --- 4. 層ごとの構成可否(gate d)。置換値が参照一覧に在る現場は使わない。---
    layer_pools = collections.OrderedDict()
    layer_build_excluded = collections.OrderedDict()
    for layer in LAYERS + [LAYER_APRIME]:
        pool = []
        excluded_cannot_build = 0
        excluded_collides = 0
        for c in eligible_base:
            number_text, unit, params = c["number_text"], c["unit"], c["params"]
            sign_mult = -1.0 if c["sign"] else 1.0

            if layer == "b_one_digit":
                # 層 (b) は RNG が要るので、母数の段では「桁が 1 つ以上ある」
                # ことだけを条件にする(実際の桁の選び方は抽選後に 1 回だけ、
                # 種を消費して決める ― ここで試し引きはしない。衝突の有無も
                # 抽選後にしか分からないので、この段では数えない)。
                if not any(ch.isdigit() for ch in number_text):
                    excluded_cannot_build += 1
                    continue
                pool.append(c)
                continue

            if layer == "a_just_outside":
                delta = TV.layer_a_delta_doc(number_text, params)
            elif layer == "c_order_of_magnitude":
                delta = 0.0  # 乗算なので「幅」は使わない(下で別に計算する)
            else:
                delta = TV.layer_aprime_delta_doc(number_text, params)
            if delta is None:
                excluded_cannot_build += 1
                continue

            written_unsigned = TV.written_value_of(number_text)
            if layer == "c_order_of_magnitude":
                new_unsigned = written_unsigned * TV.LAYER_C_MULTIPLIER
            else:
                new_unsigned = written_unsigned + delta
            new_signed = sign_mult * new_unsigned
            if TV.collides_with_reference(new_signed, unit, refs):
                excluded_collides += 1
                continue
            pool.append(c)
        layer_pools[layer] = pool
        layer_build_excluded[layer] = {"cannot_build": excluded_cannot_build, "collides_with_reference": excluded_collides}

    # --- 5. 層ごとに種で --per-stratum 件を抽選(決定的) ----------------------
    rng = random.Random(a.seed + ":" + a.doc)
    drawn_by_layer = collections.OrderedDict()
    shortfall_by_layer = collections.OrderedDict()
    for layer in LAYERS + [LAYER_APRIME]:
        pool = layer_pools[layer]
        k = min(a.per_stratum, len(pool))
        idx = sorted(rng.sample(range(len(pool)), k)) if k else []
        drawn_by_layer[layer] = [pool[i] for i in idx]
        shortfall_by_layer[layer] = a.per_stratum - k

    # --- 6. 1 件ごとに混入し、P7 + Core で回す --------------------------------
    injection_rows_by_layer = collections.OrderedDict()
    invariant_violations = []

    for layer in LAYERS + [LAYER_APRIME]:
        rows_out = []
        for c in drawn_by_layer[layer]:
            number_text, unit, params = c["number_text"], c["unit"], c["params"]
            sign_mult = -1.0 if c["sign"] else 1.0
            base_unsigned = TV.written_value_of(number_text)

            if layer == "a_just_outside":
                delta = TV.layer_a_delta_doc(number_text, params)
                new_unsigned = base_unsigned + delta
                layer_detail = {"delta_doc": delta}
            elif layer == "c_order_of_magnitude":
                new_unsigned = base_unsigned * TV.LAYER_C_MULTIPLIER
                layer_detail = {"multiplier": TV.LAYER_C_MULTIPLIER}
            elif layer == LAYER_APRIME:
                delta = TV.layer_aprime_delta_doc(number_text, params)
                new_unsigned = base_unsigned + delta
                layer_detail = {"delta_doc": delta}
            else:  # b_one_digit: RNG を 1 件ごとに消費して桁を決める(ここで初めて)
                new_text = TV.layer_b_new_text(number_text, rng)
                if new_text is None:
                    rows_out.append({
                        "claim_id": c["claim_id"], "number_text": number_text, "unit": unit,
                        "error": "layer_b_new_text returned None (no candidate digit)", "detected": None,
                    })
                    continue
                new_unsigned = float(new_text.replace(",", ""))
                layer_detail = {"new_text": new_text}

            if layer != "b_one_digit":
                new_text = TV.render_like(new_unsigned, number_text)

            new_signed = sign_mult * new_unsigned
            if layer != LAYER_APRIME and TV.collides_with_reference(new_signed, unit, refs):
                # 層 (b) は数字そのものが抽選後に初めて決まるので、この収集は
                # ここでしか行えない(事前の母数の段では引けない)。
                rows_out.append({
                    "claim_id": c["claim_id"], "number_text": number_text, "unit": unit,
                    "new_text": new_text, "error": "replacement_collides_with_reference", "detected": None,
                })
                continue

            try:
                new_zb = TV.tamper_value(zb, number_text, unit, new_text)
            except TV.TamperError as ex:
                rows_out.append({
                    "claim_id": c["claim_id"], "number_text": number_text, "unit": unit, "new_text": new_text,
                    "error": "%s: %s" % (type(ex).__name__, ex), "detected": None,
                })
                continue

            new_rows = run_core_rows_params(new_zb, a.profile)
            new_by_id = {r["id"]: r for r in new_rows}
            new_num_sites = T2.num_claim_sites(new_zb)
            content_after = T2.find_claim_sites_by_digits(new_num_sites, new_text, unit)

            post_claim = new_by_id.get(c["claim_id"])
            claim_present_after = post_claim is not None
            post_state = post_claim["state"] if post_claim else None
            id_cross_check_agrees = (
                claim_present_after and len(content_after) == 1 and content_after[0]["id"] == c["claim_id"]
            )
            detected = T2.is_detected(claim_present_after, post_state)

            # 構造の不変条件(封 §2-3): 混ぜた後の Claim 総数が原本と同じで、
            # **混入した主張以外**の状態が 1 件も変わらないこと。id ベースで
            # 1 件ずつ比べる(集計した GROUNDED の数だけを見ると、無関係な 2
            # 件が逆方向に動いて総数が偶然そろう場合を見逃す)。
            #
            # 「混入した主張自身が GROUNDED を離れるか」は、この構造の不変
            # 条件には**含めない**。それは E-0/E-5/E-8 本文の後半(層 (a)(b)(c)
            # は必ず VALUE_MISMATCH になるはず)が測る対象そのものであり、
            # ``detected``/``layer_rates`` の not_stopped で既に報告している。
            # 層 (a) で許容の片側(truncate 分岐・abs 分岐)が 1 単位分広い
            # ため、「+1 単位」でも GROUNDED のまま残る実例が実測された
            # (2026-10-08、S100YMFV N051/N071)。ここをこの不変条件の違反
            # として数えると、測定対象そのもの(封が「外れとして記録する」
            # と明記している E-5 の失敗モード)を道具の欠陥と取り違える。
            invariant_total_ok = (len(new_rows) == baseline_claims_total)
            other_claims_unchanged = True
            first_other_mismatch = None
            for oid, brow in baseline_by_id.items():
                if oid == c["claim_id"]:
                    continue
                nrow = new_by_id.get(oid)
                if nrow is None or nrow["state"] != brow["state"]:
                    other_claims_unchanged = False
                    first_other_mismatch = {
                        "id": oid, "baseline_state": brow["state"],
                        "new_state": nrow["state"] if nrow else None,
                    }
                    break
            if not (invariant_total_ok and other_claims_unchanged):
                invariant_violations.append({
                    "layer": layer, "claim_id": c["claim_id"],
                    "invariant_total_ok": invariant_total_ok,
                    "other_claims_unchanged": other_claims_unchanged,
                    "first_other_mismatch": first_other_mismatch,
                    "post_state": post_state,
                })

            rows_out.append({
                "claim_id": c["claim_id"],
                "unit": unit,
                "number_text_before": number_text,
                "number_text_after": new_text,
                "value_before": sign_mult * base_unsigned,
                "value_after": new_signed,
                "tolerance_base": c["tolerance_base"],
                "tolerance_source": c["tolerance_source"],
                "layer_detail": layer_detail,
                "baseline_state": "GROUNDED",
                "post_claim_id": post_claim["id"] if post_claim else None,
                "post_state": post_state,
                "post_recomputed": post_claim["recomputed"] if post_claim else None,
                "post_reason": post_claim["reason"] if post_claim else None,
                "content_match_after_count": len(content_after),
                "id_cross_check_agrees": id_cross_check_agrees,
                "claim_present_after": claim_present_after,
                "invariant_total_ok": invariant_total_ok,
                "other_claims_unchanged": other_claims_unchanged,
                "detected": detected,
            })
        injection_rows_by_layer[layer] = rows_out

    # --- 7. 集計(main() の外の既存関数を使い回す) -----------------------------
    excluded_table = collections.OrderedDict([
        ("cannot_mix_this_form", collections.OrderedDict([
            ("reason", "混ぜられない書き方(平文の「数字+単位」の形でない。漢数字混じりの"
                       "金額など)"),
            ("total", stage["gate_a_not_plain_number_unit"]),
        ])),
        ("location_cannot_be_pinned_down", collections.OrderedDict([
            ("reason", "場所を特定できない(HTML で 0 件または 2 件以上)"),
            ("total", stage["gate_b_html_ambiguous"]),
        ])),
        ("tolerance_unreadable", collections.OrderedDict([
            ("reason", "許容が読めない(contract.params に abs_tolerance/claim_scale/"
                       "tolerance のいずれも無い)"),
            ("total", stage["gate_c_tolerance_unreadable"]),
        ])),
        ("per_layer_cannot_build_or_collides", collections.OrderedDict([
            (layer, layer_build_excluded[layer]) for layer in LAYERS + [LAYER_APRIME]
        ])),
    ])

    summary = build_layer_summary(injection_rows_by_layer, shortfall_by_layer, layer_build_excluded)
    layer_rates = summary["layer_rates"]
    combined_note = summary["combined_note"]
    combined_detected = summary["combined_detected"]
    combined_drawn = summary["combined_drawn"]
    combined_rates = summary["combined_rates"]
    aprime_box = summary["aprime_box"]

    headline = "型1のみ・開発に使った3書類での検出率(層ごと)"

    out = collections.OrderedDict([
        ("tool", "run_detection_t1"),
        ("headline", headline),
        ("doc", a.doc),
        ("profile", a.profile),
        ("seed", a.seed),
        ("per_stratum_requested", a.per_stratum),
        ("zip_sha256", zip_sha),
        ("reference_numbers_sha256", refs_sha256),
        ("baseline_claims_total", baseline_claims_total),
        ("baseline_state_tally", baseline_state_tally),
        ("stage", stage),
        ("layer_pool_sizes", collections.OrderedDict([(layer, len(layer_pools[layer])) for layer in LAYERS + [LAYER_APRIME]])),
        ("layer_build_excluded", layer_build_excluded),
        ("classified_sites", classified),
        ("injections_by_layer", injection_rows_by_layer),
        ("layer_rates", layer_rates),
        ("combined_rate_note", combined_note),
        ("combined_detected_total", combined_detected),
        ("combined_drawn_total", combined_drawn),
        ("combined_rates", combined_rates),
        ("contract_allows_this_box", aprime_box),
        ("excluded_table", excluded_table),
        ("invariant_violations", invariant_violations),
    ])

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)

    print(json.dumps({
        "doc": a.doc, "profile": a.profile, "headline": headline, "stage": stage,
        "layer_pool_sizes": out["layer_pool_sizes"], "layer_build_excluded": layer_build_excluded,
        "layer_rates": {k: {"drawn": v["drawn"], "detected": v["detected"], "not_stopped": v["not_stopped"],
                             "rate_conditional": v["rates"]["conditional_on_traceable_before_mixing"]["rate"]}
                        for k, v in layer_rates.items()},
        "combined_detected_total": combined_detected, "combined_drawn_total": combined_drawn,
        "aprime_stayed_grounded": aprime_box["stayed_grounded"], "aprime_drawn": aprime_box["drawn"],
        "invariant_violations": len(invariant_violations),
    }, ensure_ascii=False, indent=1))
    print("written:", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
