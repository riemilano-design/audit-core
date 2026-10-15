# -*- coding: utf-8 -*-
"""段 7 の診断(封 §7・§8 の 3)。**段 6 の 25 件は診断用で、合否には使わない。**

やること:
  1. 封の §7 の表を**文書から読む**(予測を script に写さない)
  2. 凍結した段 6 の報告文に **旧 engine と新 engine** を当てる
  3. 行ごとの変化を予測と照合し、**段 6 の 13 件の接続が壊れていないか**を見る

**合否は出さない。**性能の評価は新しい報告文だけで行う(封 §4・§5)。

    python3 measure/sheet_m7_diagnostic_2026-10-15.py
"""
import collections
import importlib.util
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M7_SEAL_2026-10-15.md")
REPORT = os.path.join(FX, "m6_report_2026-10-15.json")
M6 = os.path.join(FX, "m6_binds_2026-10-15.json")
M6S = os.path.join(FX, "m6_score_2026-10-15.json")
OUT = os.path.join(FX, "m7_diagnostic_2026-10-15.json")


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


NEW = _mod("m7", "sheet_m7_engine_2026-10-15.py")
OLD = _mod("m5_for_diag", "sheet_m5_engine_2026-10-15.py")
L = _mod("label_spec_for_diag", "sheet_label_spec_2026-10-15.py")
M2 = NEW.M2


def _ids(cell):
    """`R002〜R007・R009〜R013` のような欄を id の一覧に開く。"""
    out = []
    for a, b in re.findall(r"R(\d{3})〜R(\d{3})", cell):
        out += ["R%03d" % i for i in range(int(a), int(b) + 1)]
    flat = re.sub(r"R\d{3}〜R\d{3}", "", cell)
    out += re.findall(r"R\d{3}", flat)
    return sorted(set(out))


def read_prediction():
    """**封の文書から**予測を読む。script に数を写さない(段 4 で立てた決まり)。"""
    t = io.open(SEAL, encoding="utf-8").read()
    i = t.index("## 7. 段 6 の 25 件への予測")
    j = t.find("\n## ", i + 1)
    s = t[i:(j if j > 0 else len(t))]
    rows, want = {}, {}
    for line in s.split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5 or cells[1] in ("件数", "---"):
            continue
        ids = _ids(cells[0])
        if not ids:
            continue
        n = int(re.sub(r"[^0-9]", "", cells[1]) or 0)
        if len(ids) != n:
            raise AssertionError("封の群 %r は %d 件と書いてあるが id は %d 件"
                                 % (cells[0], n, len(ids)))
        pred = cells[3].replace("*", "")
        for x in ids:
            rows[x] = pred
    for line in s.split("\n"):
        m = re.match(r"\| (D-\d) \| (.+?) \|$", line.strip())
        if m:
            want[m.group(1)] = m.group(2).replace("*", "")
    if len(rows) != 25:
        raise AssertionError("封の群の id が 25 件でない: %d" % len(rows))
    return rows, want, s


def main():
    pred, dlines, _ = read_prediction()
    report = json.load(io.open(REPORT, encoding="utf-8"))["report"]
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    args = (M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
            M2.parse_meisai(books[M2.MEISAI]))
    old = OLD.run(report, *args)
    new = NEW.run(report, *args)
    ob = {b["claim_id"]: b for b in old["binds"]}
    nb = {b["claim_id"]: b for b in new["binds"]}
    oc = {c["id"]: c for c in old["claims"]}
    nc = {c["id"]: c for c in new["claims"]}
    # 行の対応は **(文の番号, 値)** で取る(id の付け方に頼らない)
    assert sorted(oc) == sorted(nc), "切り出した主張の id が旧と新で違う"
    for cid in oc:
        assert (oc[cid].get("sentence_index"), oc[cid].get("value")) == \
               (nc[cid].get("sentence_index"), nc[cid].get("value")), cid

    frozen = json.load(io.open(M6, encoding="utf-8"))
    frozen_b = {b["claim_id"]: b for b in frozen["binds"]}
    # 段 6 の**凍結した確定ラベル**を N-1/N-2/E2 の診断に使う。
    # **段 6 の合否は動かさない**(封 §6 の 1)。これは診断の数である。
    label6 = {r["id"]: r["label6"] for r in
              json.load(io.open(M6S, encoding="utf-8"))["rows"]}
    alias = NEW.alias_table(NEW.fix_total_level(NEW.build_index(*args)))["table"]

    rows, changed, broke = [], [], []
    for cid in sorted(oc):
        if oc[cid].get("skipped"):
            continue
        o, n = ob[cid], nb[cid]
        kind = ("変化なし" if (o["state"], o.get("hold_reason")) ==
                (n["state"], n.get("hold_reason")) else None)
        if kind is None:
            if o["state"] != "GROUNDED" and n["state"] == "GROUNDED":
                kind = "保留 → 接続"
            elif o["state"] == "GROUNDED" and n["state"] != "GROUNDED":
                kind = "接続 → 保留"
            elif o["state"] == "GROUNDED" and n["state"] == "GROUNDED":
                kind = "接続先が変わった" if o["pointer"] != n["pointer"] else "変化なし"
            else:
                kind = "保留のまま。理由だけ変わる"
        rows.append({
            "id": cid, "subject": nc[cid].get("subject"), "column": nc[cid].get("column"),
            "old_state": o["state"], "new_state": n["state"],
            "old_hold": o.get("hold_reason"), "new_hold": n.get("hold_reason"),
            "old_pointer": o["pointer"], "new_pointer": n["pointer"],
            "parent_cues": n.get("parent_cues"), "parent_filtered": n.get("parent_filtered"),
            "parent_kept": n.get("parent_kept"),
            "parent_before": n.get("parent_before"), "parent_after": n.get("parent_after"),
            "new_parent": (n.get("evidence") or {}).get("parent"),
            "kind": kind, "predicted": pred[cid],
            "hit": kind == pred[cid]})
        # N-1 / N-2(封 §3): 親で絞った主張について、残った親がラベルの親と合うか
        lab = label6.get(cid)
        lab_parent = (lab[1][2] if lab and lab[0] == "label" else None)
        rows[-1]["label_parent"] = lab_parent
        rows[-1]["label_is_verdict"] = bool(lab and lab[0] != "label")
        if n.get("parent_filtered"):
            kept = [M2.norm(x.replace(" ", "")) for x in (n.get("parent_kept") or [])]
            rows[-1]["parent_correct"] = (
                None if lab_parent is None else (len(kept) == 1 and kept[0] == lab_parent))
        else:
            rows[-1]["parent_correct"] = None
        # E2 の診断: 新しく GROUNDED になった行がラベルと一致しているか
        if n["state"] == "GROUNDED" and lab is not None:
            ek = L.engine_label(n, alias)
            rows[-1]["agree_6"] = (
                lab[0] == "label"
                and tuple(ek.get(f, "") for f in L.FIELDS) == tuple(lab[1]))
        else:
            rows[-1]["agree_6"] = None
        if kind != "変化なし":
            changed.append(cid)
        # 回帰: 凍結した段 6 の接続が壊れていないか
        if frozen_b[cid]["state"] == "GROUNDED" and (
                n["state"] != "GROUNDED" or n["pointer"] != frozen_b[cid]["pointer"]):
            broke.append(cid)

    filt = [r for r in rows if r["parent_filtered"]]
    hits = sum(1 for r in rows if r["hit"])
    o_g = sum(1 for r in rows if r["old_state"] == "GROUNDED")
    n_g = sum(1 for r in rows if r["new_state"] == "GROUNDED")
    print("採点対象 %d 件 / 予測と一致 %d 件 / 外れ %d 件"
          % (len(rows), hits, len(rows) - hits))
    print("接続: 旧 %d → 新 %d(増分 %+d)" % (o_g, n_g, n_g - o_g))
    state_changed = [r["id"] for r in rows
                     if (r["old_state"] == "GROUNDED") != (r["new_state"] == "GROUNDED")]
    print("**状態(接続/保留)が変わった主張: %d 件 %s**" % (len(state_changed), state_changed))
    print("記録が変わった主張(理由だけの変化を含む): %d 件 %s" % (len(changed), changed))
    print("親で絞った主張: %d 件 %s" % (len(filt), [r["id"] for r in filt]))
    for r in filt:
        print("   %s 候補 %d → %d / 残った親 %s"
              % (r["id"], r["parent_before"], r["parent_after"], r["parent_kept"]))
    print("**段 6 の接続が壊れた主張: %d 件 %s**" % (len(broke), broke))
    print("保留の理由(新):")
    for k, v in collections.Counter(
            r["new_hold"] for r in rows if r["new_state"] != "GROUNDED").items():
        print("   %-60s %d" % (k, v))
    for r in rows:
        if not r["hit"]:
            print("  **外れ** %s 予測=%s 実測=%s(旧 %s / 新 %s)"
                  % (r["id"], r["predicted"], r["kind"], r["old_hold"], r["new_hold"]))
    n1 = sum(1 for r in rows if r["parent_correct"] is True)
    n2 = sum(1 for r in rows if r["parent_correct"] is False)
    n_unk = sum(1 for r in rows if r["parent_filtered"] and r["parent_correct"] is None)
    e2 = sum(1 for r in rows if r["agree_6"] is False)
    print("N-1 親を正しく抽出 %d 件 / N-2 親を誤って抽出 %d 件 / 判定できず %d 件"
          % (n1, n2, n_unk))
    print("**診断の E2(段 6 の凍結ラベルで照合。段 6 の合否は動かさない)= %d 件**" % e2)
    print("封の D 行(文書から読んだ):")
    for k in sorted(dlines):
        print("   %s %s" % (k, dlines[k]))

    rec = {"purpose": "段 7 の診断。**合否は出さない。**段 6 の 25 件は診断用",
           "seal": "docs/DOMAIN1_M7_SEAL_2026-10-15.md",
           "not_performance_evidence": True,
           "prediction_read_from": "docs/DOMAIN1_M7_SEAL_2026-10-15.md §7",
           "old_engine": "measure/sheet_m5_engine_2026-10-15.py",
           "new_engine": "measure/sheet_m7_engine_2026-10-15.py",
           "applied_times": 1,
           "scorable": len(rows), "prediction_hits": hits,
           "prediction_misses": len(rows) - hits,
           "grounded_old": o_g, "grounded_new": n_g, "grounded_delta": n_g - o_g,
           "changed_record": changed, "changed_state": state_changed,
           "parent_filtered": [r["id"] for r in filt],
           "N-1_親を正しく抽出": n1, "N-2_親を誤って抽出": n2,
           "N-1_判定できず": n_unk,
           "診断の E2": e2,
           "E2_note": ("段 6 の凍結した確定ラベルで照合した**診断の数**。"
                       "段 6 の合否は動かさない(封 §6 の 1)"),
           "broke_stage6_binds": broke,
           "d_lines": dlines, "rows": rows}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
