# -*- coding: utf-8 -*-
"""P-5 診断(封 docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md §4・§5)。

**段 9 の凍結した報告文・問い・2 席のラベルに、歳入側の裏づけを使う engine を当てる。**
生成しない(費用 0)。`MIN_INDEPENDENT` は触らない。

> **診断で、新しく正しく接続した主張が 1 件以上生まれた場合だけ**、本実験に進む。
> 生まれなければ**この経路は打ち切る。規則も閾値も緩めない。**(封 §5)

**採点器の正規化は engine と同じ別名表を使う**(両側に同じ正規化。
`sheet_symmetry_audit_2026-10-16.py` の S-1〜S-5 で確かめた器)。
**別名表を片側だけ入れ替えると段 8 の正規化の欠陥を作り直すことになる**ので、
**非対称にした場合の数も併記して開示する。**

  usage: python3 measure/sheet_sainyuu_p5_2026-10-16.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
OUT = os.path.join(FX, "sainyuu_p5_2026-10-16.json")
SEAL = "docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md"
BINDS = os.path.join(FX, "m9_binds_2026-10-16.json")
REPORT = os.path.join(FX, "m9_report_2026-10-16.json")
SEAT1 = os.path.join(FX, "m9_answers_seat1_2026-10-16.json")
SEAT2 = os.path.join(FX, "m9_answers_seat2_2026-10-16.json")
M9SCORE = os.path.join(FX, "m9_score_2026-10-16.json")
ALIAS_HOLD_MARK = "会計が未確認の別名"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


SE = _mod("sainyuu_engine_p5", "sheet_sainyuu_engine_2026-10-16.py")
M7 = SE.M7
OLD = SE.OLD
S8 = _mod("m8score_for_p5", "sheet_m8_score_2026-10-16.py")
RUN9 = _mod("run9_for_p5", "sheet_m9_run_2026-10-16.py")
M2 = SE.M2
norm = SE.norm


def stop_verdict(increment):
    """封 §5 の停止規則。**判定を 1 か所に置く**(字で固定すると変異が黙る)。"""
    return "本実験に進める" if increment >= 1 else "**打ち切る**"


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def measure():
    """**記録を作らずに測る。**門がその場で測り直せるように切り出す
    (記録を読むだけの門は、ここを壊す変異に黙る)。"""
    shas = RUN9.check_shas()        # **凍結した engine が動いていたら結果は無効**
    report = load(REPORT)["report"]
    rec_in = load(BINDS)
    claims_in = {c["id"]: c for c in rec_in["claims"]}
    s1 = {a["id"]: a for a in load(SEAT1)["answers"]}
    s2 = {a["id"]: a for a in load(SEAT2)["answers"]}
    scorable = sorted(cid for cid, c in claims_in.items() if c.get("scorable"))

    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    args = (M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
            M2.parse_meisai(books[M2.MEISAI]))

    m9 = M7.run(report, *args)                 # 段 9 の新 engine(別名 1 件)
    new = SE.run(report, *args)                # 歳入側の裏づけを使う engine
    b9 = {b["claim_id"]: b for b in m9["binds"]}
    bn = {b["claim_id"]: b for b in new["binds"]}
    assert sorted(b9) == sorted(bn), "主張の id が違う"
    for cid in claims_in:
        for src in (m9["claims"], new["claims"]):
            pass
    claims = {c["id"]: dict(c, novelty=claims_in[c["id"]].get("novelty"))
              for c in new["claims"] if c["id"] in claims_in}

    def score(binds, alias_table):
        S8.ALIAS = alias_table
        return S8.tally(binds, claims, scorable, s1, s2)

    a9 = m9["alias"]["table"]
    an = new["alias"]["table"]
    sym_old = score(b9, a9)                    # 段 9 の再現(対称)
    sym_new = score(bn, an)                    # 新(対称。**これが答え**)
    asym = score(bn, a9)                       # **非対称。開示用**

    # ③の発火(ラベルを使わない定義。段 9 の run と同じ)
    def a_counts(binds, alias):
        unconf = {norm(u["name"]) for u in alias["unconfirmed"]}
        a1 = a2 = a3 = 0
        for cid in scorable:
            b = binds[cid]
            if b["state"] == "GROUNDED":
                if norm((b.get("evidence") or {}).get("scope")) in unconf:
                    a3 += 1
                continue
            if b["state"] == "POINTER_NOT_FOUND":
                continue
            if b.get("unconfirmed_scope") or ALIAS_HOLD_MARK in (b.get("hold_reason") or ""):
                a1 += 1
            else:
                a2 += 1
        return {"A-1": a1, "A-2": a2, "A-3": a3}

    # **循環を切る。**採点器は「別名表」を使って席の答えを正本に直す。
    # つまり**試している写像そのものを採点に使っている。**
    # だから「会計の欄を除いた 5 欄」が一致するかを**別名表に頼らずに**数える。
    # 5 欄が合っていれば、残る違いは会計の字だけであり、
    # その 1 点は P-6(誤った対 0/324・歯つき)が扱っている。
    F5 = tuple(f for f in S8.F6 if f != "会計")

    def five_field_agreement(binds, ids):
        same = diff = unknown = 0
        detail = []
        S8.ALIAS = {}                     # **別名表を使わない**
        for cid in ids:
            lab, _ = S8.confirmed(s1.get(cid, {}), s2.get(cid, {}), F5)
            ek = S8.engine_key(binds[cid], F5)
            if lab[0] != "label" or ek is None:
                unknown += 1
                continue
            if ek == lab:
                same += 1
            else:
                diff += 1
                detail.append({"id": cid, "engine": ek[1], "label": lab[1]})
        return {"一致": same, "食い違い": diff, "判定不能": unknown,
                "食い違いの明細": detail[:5], "欄": list(F5)}

    # 段 9 で正しく接続していた主張が壊れていないか
    ok9 = {r["id"] for r in sym_old["rows"] if r["verdict"] == "正しい接続"}
    okn = {r["id"] for r in sym_new["rows"] if r["verdict"] == "正しい接続"}
    m9rec = load(M9SCORE)

    rec = {"seal": SEAL, "step": "P-5 診断(生成しない。費用 0)",
           "engine_shas_unchanged": shas,
           "min_independent": new["alias"]["min_independent"],
           "別名": {"段 9 で通った": len(a9), "新で通った": len(an),
                  "歳入で通った": len(new["alias"]["promoted_by_sainyuu"]),
                  "未確認のまま": len(new["alias"]["unconfirmed"])},
           "採点対象": len(scorable),
           "対称(段 9 の再現)": {k: sym_old[k] for k in
                           ("g1", "g2", "g3", "e2", "hold_total", "hold_ok", "split")},
           "対称(新。**これが答え**)": {k: sym_new[k] for k in
                                ("g1", "g2", "g3", "e2", "hold_total", "hold_ok",
                                 "split")},
           "非対称(開示用。採点器だけ段 9 の別名表)": {
               k: asym[k] for k in ("g1", "g2", "g3", "e2")},
           "A の数え(段 9 の engine)": a_counts(b9, m9["alias"]),
           "A の数え(新 engine)": a_counts(bn, new["alias"]),
           "会計の欄を除いた 5 欄の一致(別名表を使わない)":
               five_field_agreement(bn, sorted(okn - ok9)),
           "N-接続-正の増分": len(okn) - len(ok9),
           "新しく正しく接続した主張": sorted(okn - ok9),
           "壊れた主張(段 9 で正しかったのに新で正しくない)": sorted(ok9 - okn),
           "保留の理由(新)": sym_new["hold_reasons"],
           "停止規則": ("新しく正しく接続した主張が 1 件以上なら本実験に進める。"
                    "0 件ならこの経路を打ち切る(規則も閾値も緩めない)"),
           "停止規則の判定": stop_verdict(len(okn - ok9)),
           "limits": [
               "**既知の標本に対する診断であり、性能の証明ではない。**"
               "私は段 9 のラベルを既に読んでいる。",
               "**採点器は engine と同じ別名表を使う**(両側に同じ正規化)。"
               "非対称にした数も併記した。",
               "**「別名規則の安全性が改善した」とは書かない。**",
               "**採点器は試している写像そのものを使う。**だから会計の欄を除いた "
               "5 欄の一致を別に数え、残る 1 点(会計の字)は P-6 が扱う。",
           ]}
    return rec


def main():
    rec = measure()
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    sym_old = rec["対称(段 9 の再現)"]
    sym_new = rec["対称(新。**これが答え**)"]
    asym = rec["非対称(開示用。採点器だけ段 9 の別名表)"]
    a9, an = {}, {}
    okn = set(rec["新しく正しく接続した主張"])
    ok9 = set()
    new = {"alias": {"promoted_by_sainyuu": [None] * rec["別名"]["歳入で通った"],
                     "unconfirmed": [None] * rec["別名"]["未確認のまま"]}}
    print("=== P-5 診断(生成しない。MIN_INDEPENDENT = %d)==="
          % rec["min_independent"])
    print("別名: 段 9 で通った %d -> 新で通った %d(歳入で %d 件昇格・未確認 %d)"
          % (rec["別名"]["段 9 で通った"], rec["別名"]["新で通った"],
             rec["別名"]["歳入で通った"], rec["別名"]["未確認のまま"]))
    print("採点対象 %d 件" % rec["採点対象"])
    for lbl, d in (("対称(段 9 の再現)", sym_old), ("対称(新)", sym_new)):
        print("%-18s 正しい接続 %d / 誤接続 %d / 根拠なし接続 %d / E2 %d / 保留 %d(正しく保留 %d)"
              % (lbl, d["g1"], d["g2"], d["g3"], d["e2"], d["hold_total"], d["hold_ok"]))
    print("**非対称(開示用)**  正しい接続 %d / 誤接続 %d / E2 %d"
          % (asym["g1"], asym["g2"], asym["e2"]))
    print("③の発火: 段 9 %s -> 新 %s"
          % (rec["A の数え(段 9 の engine)"], rec["A の数え(新 engine)"]))
    print("**N-接続-正の増分: %+d**(新しく %s / 壊れた %s)"
          % (rec["N-接続-正の増分"], rec["新しく正しく接続した主張"] or "なし",
             rec["壊れた主張(段 9 で正しかったのに新で正しくない)"] or "なし"))
    f5 = rec["会計の欄を除いた 5 欄の一致(別名表を使わない)"]
    print("**会計の欄を除いた 5 欄(別名表なし): 一致 %d / 食い違い %d / 判定不能 %d**"
          % (f5["一致"], f5["食い違い"], f5["判定不能"]))
    print("**停止規則の判定: %s**" % rec["停止規則の判定"])
    print("->", OUT)


if __name__ == "__main__":
    main()
