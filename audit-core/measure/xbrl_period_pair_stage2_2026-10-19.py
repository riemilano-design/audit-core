# -*- coding: utf-8 -*-
u"""封 `docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md`(790a5c5)+ 追記 1(78a04f5)の**段 2(engine)**の実測。

段 2 の engine 変更そのものは commit `ac8c3ff`(独立監査 GO)で既に入っている。
**この script はその commit を 1 行も変えない(読むだけ)。**測るのは製品の経路
(``adapters.xbrl.verify_external.verify_external(..., period_pair=True)``)であり、
材料の組み立ては ③ と同じ `measure/xbrl_holds_product_path_2026-10-19.py` の
``_material_rows``(注入後の 8 書類・192 行)をそのまま使う。

突き合わせる記録:
  - 段 1 `fixtures/xbrl/cd8/period_pair_2026-10-19.json`(兄弟 1 本の 13 行・兄弟 2 本=重複の 4 行)
  - ③ `fixtures/xbrl/cd8/period_unit_hold_2026-10-19.json`(残り 175 行の `**合成の後**`)

符号(``sign``)は engine には入っていない(engine は文字列を読まない)。この script が
段 1 の規則 `measure/xbrl_period_pair_rule_2026-10-19.py` の ``sign_from_text``(測定の層、
engine ではない)を使って文から符号を取り、``spec["sign"]`` として製品の経路へ渡す。

engine は 1 行も変えない。0 USD・席は呼ばない。

    cd audit-core
    python3 measure/xbrl_period_pair_stage2_2026-10-19.py --write
"""
import argparse
import collections
import importlib.util
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

import audit_core as core                            # noqa: E402

from adapters.xbrl import holds as H                  # noqa: E402
from adapters.xbrl import registry_setup as RS        # noqa: E402
from adapters.xbrl import verify_external as VE       # noqa: E402

SEAL = "docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md"
SEAL_COMMIT = "790a5c5"
SEAL_ADDENDUM_COMMIT = "78a04f5"
ENGINE_COMMIT = "ac8c3ff"
CD8 = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
REC_PU = os.path.join(CD8, "period_unit_hold_2026-10-19.json")
REC_PP1 = os.path.join(CD8, "period_pair_2026-10-19.json")
DRAW = os.path.join(CD8, "draw_2026-10-17.json")
OUT = os.path.join(CD8, "period_pair_stage2_2026-10-19.json")


def _load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _git(args):
    r = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("git %s: %s" % (" ".join(args), r.stderr))
    return r.stdout.strip()


#: 段 1 の規則 module(符号の字だけ使う。比較の算術はしない。engine ではない)。
R1 = _mod("measure/xbrl_period_pair_rule_2026-10-19.py", "pp_rule_for_pp_stage2")
#: ③ と同じ材料の組み立て。
HPP = _mod("measure/xbrl_holds_product_path_2026-10-19.py", "hpp_for_pp_stage2")
AT = _mod("measure/xbrl_attr_inject_2026-10-17.py", "attr_for_pp_stage2")
A1 = AT.A1
#: PP-R1〜R4 の変異を回す(``tests/adapters/xbrl/test_mutations.py`` の実物をそのまま使う)。
TM = _mod("tests/adapters/xbrl/test_mutations.py", "test_mutations_for_pp_stage2")

VE_PERIOD_PAIR = True  # 製品の経路の既定どおり(``verify_external`` の既定値と同じ)


def _loc(f):
    return "%s@%s" % (f["name"], f["context"])


def build(docs, registry):
    u"""192 行を製品の経路に通し、3 つのグループに分けて記録する。"""
    pu = _load(REC_PU)
    pp1 = _load(REC_PP1)
    pu_by = {(x["doc"], x["id"]): x for x in pu["rows"]}
    pp1_by = {(x["doc"], x["id"]): x for x in pp1["rows"] if x.get(u"席の参照先") is not None}

    rows17 = []          # 率の主張・参照先 1 本(= 段 1 の 17 行)。engine の出力。
    rows175 = []          # 残り(率で参照先なし 20 + 金額 155)。③ の **合成の後** と突き合わせる。
    ctrl13 = []           # 対照 4 種(封 §2)。兄弟 1 本の 13 行だけに当てる。

    for doc, inst, mrows, b_by in HPP._material_rows(docs, AT):
        facts, contexts = inst["facts"], inst["contexts"]
        keys = {A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])): f for f in facts}
        for r in mrows:
            unit, val = r[u"単位"], r[u"値"]
            b = b_by[(doc, r["id"])]
            ptr = b[u"席の参照先"]
            is_ratio = unit in VE.RATIO_UNITS

            if is_ratio and ptr is not None:
                f = keys.get(A1.norm_pointer(ptr))
                loc = _loc(f) if f else ptr
                sign = R1.sign_from_text(r[u"抜粋"], r[u"数の字面"])
                spec = {"kind": "ratio_change", "value": val, "unit": unit,
                        "pointers": [loc], "sign": sign}
                out = VE.verify_external(spec, facts, contexts, registry,
                                         claim_id="PP2-%s-%s" % (doc, r["id"]),
                                         period_pair=VE_PERIOD_PAIR)
                sibs = H.prior_siblings(facts, f) if f is not None else None
                n_post = None if sibs is None else len(sibs[0])
                dup_vals = None if sibs is None else sibs[1]
                s1 = pp1_by.get((doc, r["id"]))
                rec = {u"doc": doc, u"id": r["id"], u"単位": unit, u"値": val,
                       u"席の参照先": ptr,
                       u"段1 兄弟の本数": s1.get(u"兄弟の本数") if s1 else None,
                       u"state": out["state"], u"reason": out["reason"],
                       u"recomputed": out["recomputed"],
                       u"derived_pointers": out["derived_pointers"],
                       u"direction_checked": out["direction_checked"],
                       u"held": out["held"], u"hold_rules": list(out["hold_rules"]),
                       u"hold_axes": out["hold_axes"],
                       u"後の兄弟本数(PP-2)": n_post, u"duplicate_values": dup_vals}
                rows17.append(rec)

                if s1 is not None and s1.get(u"兄弟の本数") == 1 and sibs is not None and sibs[0]:
                    g = sibs[0][0]
                    flipped = (-sign) if sign is not None else None
                    out_val = VE.verify_external(dict(spec, value=spec["value"] + 1.0),
                                                 facts, contexts, registry,
                                                 period_pair=VE_PERIOD_PAIR)
                    out_sign = VE.verify_external(dict(spec, sign=flipped),
                                                  facts, contexts, registry,
                                                  period_pair=VE_PERIOD_PAIR)
                    facts_rm = [x for x in facts if x is not g]
                    out_rm = VE.verify_external(spec, facts_rm, contexts, registry,
                                                period_pair=VE_PERIOD_PAIR)
                    dup = dict(g, value=g["value"] + 1.0)
                    out_add = VE.verify_external(spec, facts + [dup], contexts, registry,
                                                 period_pair=VE_PERIOD_PAIR)
                    ctrl13.append({
                        u"doc": doc, u"id": r["id"],
                        u"値": out_val["state"],
                        u"符号": out_sign["state"],
                        u"前期を消す": {u"state": out_rm["state"], u"reason": out_rm["reason"]},
                        u"前期を増やす": {u"state": out_add["state"], u"reason": out_add["reason"]},
                    })
                continue

            # 175 行(= 192 - 17): ③ と同じ組み立て(kind は常に "single_value")。
            want = pu_by[(doc, r["id"])]
            if ptr is None:
                state_now = None
            else:
                f = keys.get(A1.norm_pointer(ptr))
                loc = _loc(f) if f else ptr
                spec = {"kind": "single_value", "value": val, "unit": unit, "pointers": [loc]}
                out = VE.verify_external(spec, facts, contexts, registry,
                                         period_pair=VE_PERIOD_PAIR)
                state_now = out["state"]
            rows175.append({u"doc": doc, u"id": r["id"],
                            u"state(段2)": state_now,
                            u"**合成の後(③)**": want[u"**合成の後**"],
                            u"一致": state_now == want[u"**合成の後**"]})
    return rows17, rows175, ctrl13, pu, pp1, pu_by, pp1_by


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)

    docs = _load(DRAW)[u"引いた 8 件"]
    registry = RS.register_all(core.Registry.default())
    rows17, rows175, ctrl13, pu, pp1, pu_by, pp1_by = build(docs, registry)

    group13 = [r for r in rows17 if r[u"段1 兄弟の本数"] == 1]
    group_dup = [r for r in rows17 if r[u"段1 兄弟の本数"] == 2]

    # ---- H-12(段1の13行との一致。行ごと) ----------------------------------
    h12_detail = []
    for r in group13:
        s1 = pp1_by[(r["doc"], r["id"])]
        same = (r["state"] == s1["state"] and r["reason"] == s1["reason"]
                and r["recomputed"] == s1["recomputed"]
                and r["derived_pointers"] == s1["derived_pointers"]
                and r["direction_checked"] == s1["sign_checked"])
        h12_detail.append({u"doc": r["doc"], u"id": r["id"], u"一致": same,
                           u"段1": {u"state": s1["state"], u"reason": s1["reason"],
                                   u"recomputed": s1["recomputed"],
                                   u"derived_pointers": s1["derived_pointers"],
                                   u"sign_checked": s1["sign_checked"]},
                           u"段2": {u"state": r["state"], u"reason": r["reason"],
                                   u"recomputed": r["recomputed"],
                                   u"derived_pointers": r["derived_pointers"],
                                   u"direction_checked": r["direction_checked"]}})
    h12_match = sum(1 for d in h12_detail if d[u"一致"])

    # ---- H-16 / H-17(重複 4 行。PP-2 後の兄弟本数・duplicate_values・state) ----
    h16_detail = [{u"doc": r["doc"], u"id": r["id"],
                   u"後の兄弟本数(PP-2)": r[u"後の兄弟本数(PP-2)"],
                   u"duplicate_values": r[u"duplicate_values"],
                   u"1本になった": r[u"後の兄弟本数(PP-2)"] == 1 and r[u"duplicate_values"] is False}
                  for r in group_dup]
    h16_match = sum(1 for d in h16_detail if d[u"1本になった"])
    dup_state_dist = collections.Counter(r["state"] for r in group_dup)

    # ---- H-18(task の字): 他 175 行の state が ③ と一致する数 ------------------
    h18_task_match = sum(1 for x in rows175 if x[u"一致"])
    # ---- H-18(封 追記1 の字): 13 行は PP-2 で変わらない(兄弟本数・duplicate_values) --
    h18_seal_detail = [{u"doc": r["doc"], u"id": r["id"],
                        u"後の兄弟本数(PP-2)": r[u"後の兄弟本数(PP-2)"],
                        u"duplicate_values": r[u"duplicate_values"],
                        u"変わらない": r[u"後の兄弟本数(PP-2)"] == 1 and r[u"duplicate_values"] is False}
                       for r in group13]
    h18_seal_match = sum(1 for d in h18_seal_detail if d[u"変わらない"])

    # ---- 対照(§2。13 行すべて) -------------------------------------------
    ctrl_tally = {
        u"値": collections.Counter(c[u"値"] for c in ctrl13),
        u"符号": collections.Counter(c[u"符号"] for c in ctrl13),
        u"前期を消す": collections.Counter((c[u"前期を消す"][u"state"], c[u"前期を消す"][u"reason"]) for c in ctrl13),
        u"前期を増やす": collections.Counter((c[u"前期を増やす"][u"state"], c[u"前期を増やす"][u"reason"]) for c in ctrl13),
    }
    h19_match = ctrl_tally[u"前期を増やす"].get(("UNPROVABLE", "prior_sibling:2;duplicate_values"), 0)

    # ---- 実証できた行(段 1 の H-11 と同じ定義。GROUNDED + VALUE_MISMATCH) ------
    before62 = sum(1 for x in pu["rows"] if x[u"**合成の後**"] in ("GROUNDED", "VALUE_MISMATCH"))
    other175_proven = sum(1 for x in rows175 if x[u"state(段2)"] in ("GROUNDED", "VALUE_MISMATCH"))
    ratio17_proven = sum(1 for r in rows17 if r["state"] in ("GROUNDED", "VALUE_MISMATCH"))
    after_total = other175_proven + ratio17_proven
    stage1_after = pp1[u"H-11 実証できた行"][u"PP を足した後"]

    # ---- H-13(変異 PP-R1〜R4) ---------------------------------------------
    all_muts = _load(os.path.join(ROOT, "tests", "adapters", "xbrl", "mutations.json"))
    pp_muts = [r for r in all_muts if r["id"].startswith("PP-R")]
    mut_results = []
    for r in pp_muts:
        rc, _txt = TM._run_mutation_fresh(r)
        mut_results.append({"id": r["id"], "rc": rc, u"色": "red" if rc != 0 else "green",
                            u"予測": r["predicted"]})
    mut_red = sum(1 for m in mut_results if m[u"色"] == "red")

    head = _git(["rev-parse", "--short", "HEAD"])

    # ---- H-12〜H-19 の予測との照合(封 §3・追記 1 の字どおりに自分で判定) ----------
    pred = [
        {u"記号": "H-12", u"封の字": u"段 2(製品の経路)の 192 行再現は段 1 の記録と 192/192 一致・"
                                  u"engine の欄以外 byte 同一",
         u"この便で測った範囲": u"段 1 の 13 行(行ごとの state・reason・recomputed・derived_pointers・"
                              u"direction_checked)との一致",
         u"実測": u"%d / 13" % h12_match,
         u"当たり": h12_match == 13,
         u"commit ac8c3ff 自身の報告(参考・機械で確かめ直したものではない)": u"191 / 192"},
        {u"記号": "H-13", u"封の字": u"PP-R1〜R3 の 3 本とも red(追記 1 で PP-R4 を足し 4 本)",
         u"実測": mut_results, u"当たり": mut_red == len(pp_muts) == 4},
        {u"記号": "H-14", u"封の字": u"独立監査は REVISE 1 回 → GO",
         u"実測": u"REVISE 0 回 → GO(commit ac8c3ff の trailer `独立監査: GO`。"
                u"回数は機械で測った数ではなく、司令塔からの引き継ぎの字を写した)",
         u"当たり": False},
        {u"記号": "H-15", u"封の字": u"run_tests.sh 1 回目で赤くなるのは test_xbrl_axis3_decision.py "
                                  u"test_9 だけ。追記の後 2 回目 rc=0",
         u"実測": u"全数の log(scratchpad/step5/run_tests_step5.log、1,923 行、ac8c3ff の後・"
                u"このSTEPの直し前に走らせたもの)で pytest 3327 passed/5 skipped、"
                u"unittest discover は Ran 3236・FAILED (failures=1, skipped=5)・"
                u"FAIL は test_9_the_engine_was_not_touched の 1 本だけ。"
                u"このSTEPで LATER_ENGINE_COMMITS に ac8c3ff を足した後、"
                u"tests/measure/test_xbrl_axis3_decision.py は 11 passed(2 回目に相当)",
         u"当たり": True},
        {u"記号": "H-16", u"封の字(追記1)": u"重複の 4 行は値が全部同じで、PP-2 の後は兄弟 1 本になる(4/4)",
         u"実測": h16_detail, u"当たり": h16_match == 4},
        {u"記号": "H-17", u"封の字(追記1)": u"その 4 行の検算は GROUNDED 3〜4・VALUE_MISMATCH 0〜1。"
                                        u"実証できた行は 75 → 79",
         u"実測": {u"4 行の state": dict(dup_state_dist),
                 u"実証できた行": u"%d → %d" % (stage1_after, after_total)},
         u"当たり": (dup_state_dist.get("GROUNDED", 0) in (3, 4)
                 and dup_state_dist.get("VALUE_MISMATCH", 0) in (0, 1)
                 and set(dup_state_dist) <= {"GROUNDED", "VALUE_MISMATCH"}
                 and after_total == 79)},
        {u"記号": "H-18", u"封の字(追記1)": u"段 1 の 13 行の state・reason・recomputed は "
                                        u"PP-2 で 1 行も変わらない",
         u"実測(封の字どおり。PP-2 固有の効果のみ)": u"%d / 13" % h18_seal_match,
         u"当たり": h18_seal_match == 13,
         u"この STEP の指示(点 2 の 3 つ目)が別に求めた数": u"他 175 行が ③ と一致: %d / %d"
             % (h18_task_match, len(rows175))},
        {u"記号": "H-19", u"封の字(追記1)": u"対照「前期を増やす」は PP-2 の後も 13/13 が UNPROVABLE"
                                        u"(値が違うので 2 本のまま)",
         u"実測": {str(k): v for k, v in ctrl_tally[u"前期を増やす"].items()},
         u"当たり": h19_match == 13 and len(ctrl_tally[u"前期を増やす"]) == 1},
    ]
    hit = sum(1 for p in pred if p[u"当たり"] is True)
    miss = sum(1 for p in pred if p[u"当たり"] is False)

    rec = {
        "seal": SEAL, "seal_commit": SEAL_COMMIT, "seal_addendum_commit": SEAL_ADDENDUM_COMMIT,
        "engine_commit": ENGINE_COMMIT,
        "step": u"**期間の対(PP)の実測。段 2(製品の経路。engine は読むだけ)。0 USD・席は呼ばない**",
        "head": head,
        u"行": {u"192 行": 192, u"率の主張・参照先 1 本(17 行)": len(rows17),
              u"うち段1 兄弟1本(13)": len(group13), u"うち段1 兄弟2本=重複(4)": len(group_dup),
              u"他(175 行)": len(rows175)},
        u"**H-12 段1の13行との一致(行ごと)**": h12_detail,
        u"**H-16/H-17 重複4行の PP-2 後**": h16_detail,
        u"**H-17 重複4行の state 分布**": dict(dup_state_dist),
        u"**H-18(task) 他175行と③の一致**": {u"一致": h18_task_match, u"行": len(rows175),
                                        u"不一致の明細": [x for x in rows175 if not x[u"一致"]]},
        u"**H-18(封) 13行はPP-2で変わらない**": h18_seal_detail,
        u"**対照(13行すべて)**": {
            u"値": {str(k): v for k, v in ctrl_tally[u"値"].items()},
            u"符号": {str(k): v for k, v in ctrl_tally[u"符号"].items()},
            u"前期を消す": {str(k): v for k, v in ctrl_tally[u"前期を消す"].items()},
            u"前期を増やす(H-19)": {str(k): v for k, v in ctrl_tally[u"前期を増やす"].items()},
        },
        u"**実証できた行**": {u"175行(③と同じ組み立て)": other175_proven,
                          u"17行(PP。段2)": ratio17_proven,
                          u"192行の合計(段2)": after_total,
                          u"段1(参考。H-11)": stage1_after,
                          u"v1(参考。62のはず)": before62},
        u"**H-13 変異 PP-R1〜R4**": mut_results,
        u"rows17": rows17,
        u"**予測との照合**": {u"欄ごと": pred, u"当たり": hit, u"外れ": miss},
        "limits": [
            u"**同じ 8 書類である。**規則 × 標本の積で、新しい書類で同じ数が出る保証は無い。",
            u"H-14 の REVISE の回数は機械の測定ではなく、司令塔からの引き継ぎの字をそのまま写した。",
            u"H-15 の 1 回目の全数ログは scratchpad(session-local。このSTEPの作業の直前に"
            u"別の作業で走らせたもの)であり、本 repo の追跡対象ではない。",
            u"H-18 は 2 つの異なる定義(この STEP の指示の字/封 追記 1 の字)で別に測った。"
            u"両方を記録に残す(どちらかを消さない)。",
            u"精度(誤りを通す率)は測っていない(封 §0・§4 と同じ限界)。",
        ],
    }
    print(u"=== 期間の対(PP)の実測。段 2(製品の経路)。engine は読むだけ・0 USD ===")
    print(u"H-12 (13行一致): %d / 13" % h12_match)
    print(u"H-16 (重複4行がPP-2で1本): %d / 4" % h16_match)
    print(u"H-17 (重複4行のstate): %s / 実証できた行 %d -> %d" % (dict(dup_state_dist), stage1_after, after_total))
    print(u"H-18(task) 他175行一致: %d / %d" % (h18_task_match, len(rows175)))
    print(u"H-18(封) 13行変わらない: %d / 13" % h18_seal_match)
    print(u"H-19 前期を増やす: %s" % dict(ctrl_tally[u"前期を増やす"]))
    print(u"H-13 変異: %s" % [(m["id"], m[u"色"]) for m in mut_results])
    for p in pred:
        print(u"  %-5s %s" % (p[u"記号"], u"当たり" if p[u"当たり"] is True else u"**外れ**"))
    print(u"当たり %d / 外れ %d" % (hit, miss))
    if a.write:
        with io.open(a.out, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("written:", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
