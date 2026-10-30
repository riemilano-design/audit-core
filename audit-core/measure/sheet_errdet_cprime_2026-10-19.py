# -*- coding: utf-8 -*-
"""方式 C の直し(C′・C″)。封 docs/DOMAIN1_ERRDET_CPRIME_SEAL_2026-10-19.md §1。

**規則は「疑いは足せるが、消せない」。**席の 3 値と検証器の 4 値から C′ を引く
(封 §1-2 の 8 行)。C″ は C′ に Core の「あるべき行」を足す(封 §1-3)。

**席の答え・採点の関数・Core の束縛は書き直さない**(全部 import)。
**費用 0 USD。生成しない。**

    python3 measure/sheet_errdet_cprime_2026-10-19.py
"""
import collections
import hashlib
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
OUT = os.path.join(FX, "errdet_cprime_2026-10-19.json")
SEAL = "docs/DOMAIN1_ERRDET_CPRIME_SEAL_2026-10-19.md"

SEAT_KINDS = ("検出", "保留", "確認済み")
VERIFIER_OUTS = ("確認済み", "原資料と一致しない",
                 "確認できない(参照先が無い)", "確認できない(値が一意でない)")
# 疑いの順(封 §1-2 の不変条件)
SUSPICION = {"確認済み": 0, "保留": 1, "検出": 2}
KIND_FIELD = "不一致の種類"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


SC = _mod("score_for_cprime", "sheet_errdet_score_2026-10-17.py")
CO = SC.CO
S = SC.S


def compose_cprime(seat_kind, verifier_out):
    """封 §1-2 の 8 行。**(C′ の状態, 行番号, 付記) を返す。**

    `verifier_out` は 4 値のどれか、または **None**(席の答えに住所が無い)。
    **席が検出なら検出(行 1〜4)。検証器が動かせるのは席が確認済みのときだけ(行 6〜8)。**
    """
    if seat_kind not in SEAT_KINDS:
        raise ValueError("seat_kind: %r" % (seat_kind,))
    if verifier_out is not None and verifier_out not in VERIFIER_OUTS:
        raise ValueError("verifier_out: %r" % (verifier_out,))
    if seat_kind == "検出":
        if verifier_out is None:
            return "検出", 4, "席を引き継ぐ"
        if verifier_out == "確認済み":
            return "検出", 1, "出どころ確認済み"
        if verifier_out == "原資料と一致しない":
            return "検出", 2, "出どころ不一致"
        return "検出", 3, "出どころ未確認"
    if seat_kind == "保留":
        return "保留", 5, "席を引き継ぐ"
    # 確認済み
    if verifier_out == "確認済み":
        return "確認済み", 6, "機械確認済み"
    if verifier_out == "原資料と一致しない":
        return "検出", 7, "検証器が止めた"
    return "保留", 8, "検証器が下げた"


def kind_of_cprime(row, seat_kind_declared):
    """種類の申告: 行 1〜4 は席の申告、行 7 は `値が原資料に無い`、他は `不明`。"""
    if row in (1, 2, 3, 4):
        return seat_kind_declared
    if row == 7:
        return "値が原資料に無い"
    return "不明"


def compose_cdouble(cprime_state, row, b_state):
    """封 §1-3。**席が確認済み(行 6・8)で B が VALUE_MISMATCH のときだけ検出へ。**

    B の保留(UNVERIFIABLE / POINTER_NOT_FOUND)は状態を動かさない。
    """
    if row in (6, 8) and b_state == "VALUE_MISMATCH":
        return "検出", "Core が自分の鍵で結んだ行の値と食い違った"
    return cprime_state, None


def sha(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def verdict_word(v):
    if v is True:
        return "当たり"
    if v is None:
        return "未測定"
    if v is False:
        return "外れ"
    raise ValueError("verdict must be True/False/None: %r" % (v,))


def main():
    if os.path.exists(OUT):
        raise SystemExit("記録が既に在る: %s(測り直さない)" % OUT)
    mk = SC.load(SC.MAKE)
    planted = {p["id"]: p for p in mk["植えた誤り"]}
    bundle = mk["束ねた変種"]["本文"]
    claims, binds = CO.run_core(bundle)
    want = {c["id"]: c["value"] for c in claims}
    b_by_id = {c["id"]: (c, b) for c, b in zip(claims, binds)}

    arms = {}
    inputs = {}
    for seat, model in SC.SEATS:
        p = os.path.join(FX, "errdet_answers_%s_2026-10-17.json" % seat)
        inputs[seat] = {"file": os.path.relpath(p, ROOT), "sha256": sha(p)}
        rec = SC.load(p)
        answers = {x["id"]: x for x in rec["answers"]}
        rows = []
        for cid in sorted(answers):
            ans = answers[cid]
            frozen = json.dumps(ans, ensure_ascii=False, sort_keys=True)
            seat_kind = SC.classify_seat(ans)
            declared = ans.get(KIND_FIELD, "不明")
            if SC.six(ans):
                vout, vwhy = SC.verify(ans, want[cid])
                sok, swhy, _c = S.resolve(ans, want[cid])
                strict_out = ("確認済み" if sok else
                              ("原資料と一致しない"
                               if (swhy or "").startswith("到達したセルの値が主張と違う")
                               else "確認できない(値が一意でない)"
                               if (swhy or "").startswith("一意に定まらない")
                               else "確認できない(参照先が無い)"))
                addr = {k: ans.get(k) for k in
                        ("会計", "階層", "親", "科目名", "列", "値")}
            else:
                vout, vwhy, strict_out, addr = None, None, None, None
            st, row, note = compose_cprime(seat_kind, vout)
            st_strict, row_strict, _n = compose_cprime(seat_kind, strict_out)
            claim, b = b_by_id[cid]
            b_state = b["state"]
            core_row = CO.ref_of(claim, b)
            st2, note2 = compose_cdouble(st, row, b_state)
            assert json.dumps(ans, ensure_ascii=False, sort_keys=True) == frozen, \
                "席の答えが動いた: %s" % cid
            rows.append({
                "id": cid, "席": seat_kind, "席の申告": declared,
                "検証器": vout, "検証器の理由": vwhy,
                "C′": st, "行": row, "付記": note,
                "C′ の種類": kind_of_cprime(row, declared),
                "封の M-3 での検証器": strict_out,
                "封の M-3 での C′": st_strict, "封の M-3 での行": row_strict,
                "B の状態": b_state, "C″": st2, "C″ の注": note2,
                "出どころの行(席)": addr, "あるべき行(Core)": core_row,
            })
        arms[seat] = {"model": model, "rows": rows}

    def tally(seat, key_state, key_row):
        rows = {r["id"]: r for r in arms[seat]["rows"]}
        err, unalt, fa, machine_ok, origin_ok, overwritten = [], collections.Counter(), [], [], [], []
        for cid, r in sorted(rows.items()):
            st = r[key_state]
            if cid in planted:
                p = planted[cid]
                seat_addr = r["出どころの行(席)"]
                core_row = r["あるべき行(Core)"]
                err.append({
                    "id": cid, "型": p["型"], "群": p["群"],
                    "Core が結べた主張か": p["Core が結べた主張か"],
                    "席": r["席"], "答え": st, "行": r[key_row],
                    "検出-1": st == "検出", "保留": st == "保留", "見落とし": st == "確認済み",
                    "検出-2 正しい行(席の住所)": (S.same_row(seat_addr, p["正しい参照先(改変前)"])
                                         if seat_addr else None),
                    "検出-2 正しい行(Core の行)": (S.same_row(core_row, p["正しい参照先(改変前)"])
                                          if core_row else None),
                    "追-2 植えた値の出どころ(席の住所)": (
                        bool(seat_addr) and int(seat_addr.get("値") or 0) == int(p["植えた値"])
                        and r["検証器"] == "確認済み"),
                    "検出-3 種類": r["C′ の種類"],
                    "検出-3 正解ラベル": p["誤りの種類(正解ラベル)"],
                    "検出-3 一致": st == "検出" and r["C′ の種類"] == p["誤りの種類(正解ラベル)"],
                })
                if r["席"] == "検出" and st == "確認済み":
                    overwritten.append(cid)
                if r[key_row] == 1:
                    origin_ok.append(cid)
            elif cid == SC.TRAP_ID:
                continue
            else:
                unalt[st] += 1
                if st == "検出":
                    fa.append(cid)
                if r["席"] == "検出" and st == "確認済み":
                    overwritten.append(cid)
                if r[key_row] == 6:
                    machine_ok.append(cid)
        trap = rows[SC.TRAP_ID]
        return {
            "誤りの採点": err,
            "検出": [e["id"] for e in err if e["検出-1"]],
            "保留": [e["id"] for e in err if e["保留"]],
            "見落とし": [e["id"] for e in err if e["見落とし"]],
            "検出-2 正しい行(席の住所)": [e["id"] for e in err if e["検出-2 正しい行(席の住所)"] is True],
            "検出-2 正しい行(Core の行)": [e["id"] for e in err if e["検出-2 正しい行(Core の行)"] is True],
            "追-2 出どころの行": [e["id"] for e in err if e["追-2 植えた値の出どころ(席の住所)"]],
            "検出-3 種類を特定": [e["id"] for e in err if e["検出-3 一致"]],
            "無改変 26": dict(unalt), "偽警報の id": fa,
            "上書き(席 検出 → 確認済み)": overwritten,
            "機械確認済み(行 6)": machine_ok,
            "出どころ確認済み(行 1)": origin_ok,
            "罠(%s)" % SC.TRAP_ID: {"席": trap["席"], "答え": trap[key_state],
                                   "行": trap[key_row], "付記": trap["付記"],
                                   "**文書は正しいのに一致しないと言ったか**": trap[key_state] == "検出"},
        }

    T = {}
    for seat, _m in SC.SEATS:
        T[seat] = {"A": None, "C′": tally(seat, "C′", "行"),
                   "C′(封の M-3)": tally(seat, "封の M-3 での C′", "封の M-3 での行"),
                   "C″": tally(seat, "C″", "行")}
        # A は席の 3 値そのもの
        rows = arms[seat]["rows"]
        a_err = [r for r in rows if r["id"] in planted]
        a_un = collections.Counter(r["席"] for r in rows
                                   if r["id"] not in planted and r["id"] != SC.TRAP_ID)
        T[seat]["A"] = {"検出": [r["id"] for r in a_err if r["席"] == "検出"],
                        "保留": [r["id"] for r in a_err if r["席"] == "保留"],
                        "見落とし": [r["id"] for r in a_err if r["席"] == "確認済み"],
                        "無改変 26": dict(a_un),
                        "偽警報の id": [r["id"] for r in rows if r["id"] not in planted
                                      and r["id"] != SC.TRAP_ID and r["席"] == "検出"],
                        "罠(%s)" % SC.TRAP_ID: {"答え": [r for r in rows if r["id"] == SC.TRAP_ID][0]["席"]}}

    # 旧 C(2026-10-17 の採点)との突き合わせ ― 旧 C の見落とし 4 件が C′ で検出に戻るか
    old = SC.load(SC.OUT)
    old_c = {s: old["A / C の内訳"]["C %s" % s] for s, _m in SC.SEATS}

    # 合否 K-1〜K-4(封 §3)
    K = {}
    for seat, _m in SC.SEATS:
        a, c, c2 = T[seat]["A"], T[seat]["C′"], T[seat]["C″"]
        K[seat] = {
            "K-1 退化なし": {"A 見落とし": len(a["見落とし"]), "C′ 見落とし": len(c["見落とし"]),
                        "A 偽警報": len(a["偽警報の id"]), "C′ 偽警報": len(c["偽警報の id"]),
                        "満たした": len(c["見落とし"]) <= len(a["見落とし"])
                        and len(c["偽警報の id"]) <= len(a["偽警報の id"])},
            "K-2 上書き 0": {"件数": len(c["上書き(席 検出 → 確認済み)"]),
                         "ids": c["上書き(席 検出 → 確認済み)"],
                         "満たした": len(c["上書き(席 検出 → 確認済み)"]) == 0},
            "K-3 足した情報(数)": {"機械確認済み(行 6)": len(c["機械確認済み(行 6)"]),
                           "出どころ確認済み(行 1)": len(c["出どころ確認済み(行 1)"])},
            "K-4 C″ ≧ C′": {"C′ 検出-2(Core の行)": len(c["検出-2 正しい行(Core の行)"]),
                         "C′ 検出-2(席の住所)": len(c["検出-2 正しい行(席の住所)"]),
                         "C″ 検出-2(Core の行)": len(c2["検出-2 正しい行(Core の行)"]),
                         "C″ 見落とし": len(c2["見落とし"]), "C″ 偽警報": len(c2["偽警報の id"]),
                         "満たした": len(c2["検出-2 正しい行(Core の行)"]) >= len(c["検出-2 正しい行(席の住所)"])
                         and len(c2["見落とし"]) == len(c["見落とし"])
                         and len(c2["偽警報の id"]) == len(c["偽警報の id"])},
        }
        K[seat]["判定"] = ("**設計欠陥は直った(この材料で)**"
                         if all(K[seat][k]["満たした"] for k in ("K-1 退化なし", "K-2 上書き 0", "K-4 C″ ≧ C′"))
                         else "**直っていない**")

    # 予測 P-1〜P-10(封 §4)
    s1, s2 = T["seat1"], T["seat2"]
    strict_hold = {s: T[s]["C′(封の M-3)"]["無改変 26"].get("保留", 0) for s, _m in SC.SEATS}
    c2_diff = {s: [r["id"] for r in arms[s]["rows"] if r["C′"] != r["C″"]] for s, _m in SC.SEATS}
    P = [
        ("P-1", "C′ seat1: 検出 8・保留 0・見落とし 0",
         (len(s1["C′"]["検出"]), len(s1["C′"]["保留"]), len(s1["C′"]["見落とし"])) == (8, 0, 0)),
        ("P-2", "C′ seat2: 検出 7・見落とし 1(R024)",
         (len(s2["C′"]["検出"]), s2["C′"]["見落とし"]) == (7, ["R024"])),
        ("P-3", "上書き 0 件・両席",
         all(len(T[s]["C′"]["上書き(席 検出 → 確認済み)"]) == 0 for s in T)),
        ("P-4", "無改変 26: 偽警報 0・保留 0・確認済み 26・両席",
         all(T[s]["C′"]["無改変 26"] == {"確認済み": 26} for s in T)),
        ("P-5", "罠 R035: C′ = 検出・両席",
         all(T[s]["C′"]["罠(R035)"]["答え"] == "検出" for s in T)),
        ("P-6", "検出-3: seat1 8/8・seat2 7/8",
         (len(s1["C′"]["検出-3 種類を特定"]), len(s2["C′"]["検出-3 種類を特定"])) == (8, 7)),
        ("P-7", "出どころ確認済み(行 1): seat1 4(R001 R004 R009 R024)・seat2 3",
         s1["C′"]["出どころ確認済み(行 1)"] == ["R001", "R004", "R009", "R024"]
         and len(s2["C′"]["出どころ確認済み(行 1)"]) == 3),
        ("P-8", "C″ の状態は C′ と 35 × 2 で全部同じ",
         all(not c2_diff[s] for s in c2_diff)),
        ("P-9", "C″ 検出-2(Core の行) 4/8 両席(R004 R009 R010 R012)。C′(席の住所)は 0/8",
         all(T[s]["C″"]["検出-2 正しい行(Core の行)"] == ["R004", "R009", "R010", "R012"]
             and len(T[s]["C′"]["検出-2 正しい行(席の住所)"]) == 0 for s in T)),
        ("P-10", "封の M-3 で C′ の見落としは M-3′ と同じ(0・1)。無改変の保留 18〜24・両席",
         (len(s1["C′(封の M-3)"]["見落とし"]), len(s2["C′(封の M-3)"]["見落とし"])) == (0, 1)
         and all(18 <= strict_hold[s] <= 24 for s in strict_hold)),
    ]
    preds = [{"id": i, "予測": d, "判定": verdict_word(v)} for i, d, v in P]

    rec = {
        "seal": SEAL, "費用": "0 USD(生成なし)",
        "入力(凍結済みの席の答え)": inputs,
        "規則": {"席の 3 値": SEAT_KINDS, "検証器の 4 値": VERIFIER_OUTS,
               "疑いの順": SUSPICION,
               "8 行": [{"行": r, "席": sk, "検証器": vo, "C′": compose_cprime(sk, vo)[0],
                        "付記": compose_cprime(sk, vo)[2]}
                       for sk, vo, r in (("検出", "確認済み", 1), ("検出", "原資料と一致しない", 2),
                                         ("検出", "確認できない(参照先が無い)", 3), ("検出", None, 4),
                                         ("保留", None, 5), ("確認済み", "確認済み", 6),
                                         ("確認済み", "原資料と一致しない", 7),
                                         ("確認済み", "確認できない(参照先が無い)", 8))]},
        "**判定(封 §3 の K-1〜K-4)**": K,
        "予測(封 §4)": preds,
        "予測の集計": collections.Counter(p["判定"] for p in preds),
        "方式ごとの内訳": {s: {arm: {k: v for k, v in val.items() if k != "誤りの採点"}
                          for arm, val in T[s].items()} for s in T},
        "誤りの件ごと": {s: {arm: T[s][arm]["誤りの採点"] for arm in ("C′", "C″", "C′(封の M-3)")}
                    for s in T},
        "旧 C(2026-10-17)との突き合わせ": {
            s: {"旧 C の見落とし": old_c[s]["見落とし"],
                "C′ の見落とし": T[s]["C′"]["見落とし"],
                "旧 C の見落としのうち C′ で検出に戻った": sorted(
                    set(old_c[s]["見落とし"]) & set(T[s]["C′"]["検出"]))}
            for s in old_c},
        "封の M-3 での無改変の保留": strict_hold,
        "C′ と C″ が違う id": c2_diff,
        "件ごとの記録(35 件 × 2 席)": {s: arms[s]["rows"] for s in arms},
        "limits": [
            "**同じ材料・同じ答えの再利用である。**規則は 4 件の失敗を知った上で書いた(封 §0)。",
            "**別資料で同じ数が出るかは測っていない**(封 §7)。",
            "**人工の誤り 8 件である。**",
            "**C′ が A を上回ったとは書かない**(検出数は A と同じ)。",
            "**B は参考群のまま。**C″ に B を足しても Core の優位性は書かない。",
        ],
    }
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)

    print("=== 方式 C の直し(封 §3 の K-1〜K-4)===")
    for s in T:
        print(s, json.dumps(K[s], ensure_ascii=False))
    print("--- 方式 × 席(検出 / 保留 / 見落とし / 偽警報 / 無改変) ---")
    for s in T:
        for arm in ("A", "C′", "C″", "C′(封の M-3)"):
            v = T[s][arm]
            print("%-6s %-10s 検出 %d 保留 %d 見落とし %d 偽警報 %d 無改変 %s"
                  % (s, arm, len(v["検出"]), len(v["保留"]), len(v["見落とし"]),
                     len(v["偽警報の id"]), v["無改変 26"]))
    print("--- 予測 ---")
    for p in preds:
        print("%-5s %s: %s" % (p["id"], p["判定"], p["予測"]))
    print(dict(rec["予測の集計"]))
    print("->", OUT)


if __name__ == "__main__":
    main()
