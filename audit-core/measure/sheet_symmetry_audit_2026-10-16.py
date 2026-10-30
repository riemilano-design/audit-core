# -*- coding: utf-8 -*-
"""採点器の**両側の正規化が対称か**を機械で確かめる(人間の指示 2026-10-16)。

> 段 8 で明らかになった採点器の正規化の問題は、別名規則を評価する前に、
> **両側の正規化が対称であることを確認する対象に含めるべきです。**
> これは閾値の変更ではなく、**測定器が比較するものを正しく比較できているか**という問題です。

段 8 で踏んだ型は「同じ関数 `norm` を両側に掛けていたが、**空欄の持ち方が
片側で `None`・片側で `""`** だった」ことだった(`norm(None)` は `None` を返す)。
記憶 `normalize-both-sides-of-a-comparison.md` の **5 回目**である。
だから対策を記憶ではなく**実行前に赤くなる試験**にする。

確かめるのは次の 5 本。**どれも「読んで判断する」のではなく数で落ちる。**

  S-1 空欄の不変性(X)    抜粋側 / engine 側の空欄を `None` ↔ `""` に入れ替えても
                          X-1〜X-4 が**全部同じ**
  S-2 空欄の不変性(採点)  同じ入れ替えで G-1〜G-8・N-1〜N-2 が**全部同じ**
  S-3 恒等                **正解ラベルをそのまま engine の答えとして入れたら満点**
                          (G-1 = ラベルが答えの行の数 / E2 = 0 / X-2 = 0)
  S-4 退化値              席が書きうる字の揺れ(全角数字・カンマ・`円`・全角 `＞`・
                          余分な空白)を入れても S-3 の満点が崩れない
  S-5 逆(緩すぎない)     ラベルの欄を 1 つだけ変えたら**必ず外れる**
                          (S-3 が「何でも一致する照合器」で通っていないこと)

**S-5 が無いと S-3 は無意味である。**照合器が全部を一致と言えば S-3 は満点になる。
"""
import copy
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
OUT = os.path.join(FX, "symmetry_audit_2026-10-16.json")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


S = _mod("m8_score_for_audit", "sheet_m8_score_2026-10-16.py")
L = S.L
OPP = _mod("m8_opp_for_audit", "sheet_m8_opportunity_2026-10-16.py")

# 空欄になりうる欄(SPEC の `blank_at` が空でない欄)の engine 側の名前
BLANKABLE = tuple(f["from"] for f in L.SPEC["fields"] if f["blank_at"])


def load():
    rec = json.load(io.open(os.path.join(FX, "m8_binds_2026-10-16.json"),
                            encoding="utf-8"))
    mat = json.load(io.open(os.path.join(FX, "m8_material_2026-10-16.json"),
                            encoding="utf-8"))
    s1 = {a["id"]: a for a in json.load(io.open(
        os.path.join(FX, "m8_answers_seat1_2026-10-16.json"),
        encoding="utf-8"))["answers"]}
    s2 = {a["id"]: a for a in json.load(io.open(
        os.path.join(FX, "m8_answers_seat2_2026-10-16.json"),
        encoding="utf-8"))["answers"]}
    return rec, mat, s1, s2


def set_alias():
    M2 = L.M2
    E = S.E
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    raw = E.fix_total_level(E.build_index(
        M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
        M2.parse_meisai(books[M2.MEISAI])))
    S.ALIAS = E.alias_table(raw)["table"]
    return S.ALIAS


# ------------------------------------------------------------ 空欄の入れ替え
def flip_blanks(obj, keys, to):
    """`obj` の `keys` の欄のうち**空欄だけ**を `to`(`None` か `""`)に替える。

    空欄でない値は触らない。**これで数が動いたら、その比較は非対称である。**
    """
    out = copy.deepcopy(obj)
    for k in keys:
        v = out.get(k)
        if v is None or (isinstance(v, str) and v.strip() == ""):
            out[k] = to
    return out


def x_counts(binds_new, cells, rows_key):
    """X-1 / X-2 を**ラベルを使わずに**数える(run 側と同じ形)。"""
    in_extract = {rows_key(c) for c in cells}
    x1 = x2 = 0
    for b in binds_new:
        if b["state"] != "GROUNDED":
            continue
        ev = b.get("evidence") or {}
        if rows_key(ev) in in_extract:
            x1 += 1
        else:
            x2 += 1
    return {"X-1": x1, "X-2": x2}


def raw_key(d):
    """run 側の鍵(生の `norm` を両側に掛ける形)。"""
    norm = L.norm
    return (norm(d.get("scope")), norm(d.get("level")), norm(d.get("parent")),
            norm(d.get("name")))


def folded_key(d):
    """**空欄を `""` に畳んだ**鍵(段 8 の直しで入れた形)。"""
    norm = L.norm
    return tuple(norm(d.get(k)) or ""
                 for k in ("scope", "level", "parent", "name"))


# ------------------------------------------------------------------ S-1 / S-2
def s1_blank_invariance(rec, mat):
    """抜粋側 / engine 側の空欄を入れ替えても X が動かないこと。"""
    cells = OPP.cells_of(OPP.extract_of(mat))
    results = {}
    for name, key in (("生の norm", raw_key), ("空欄を畳む", folded_key)):
        per = {}
        for tag, (eb, cb) in (("そのまま", (None, None)),
                              ("engine 側を空文字", ("", None)),
                              ("抜粋側を空文字", (None, "")),
                              ("両側を空文字", ("", ""))):
            bs = [flip_blanks(b.get("evidence") or {}, BLANKABLE, eb)
                  if b["state"] == "GROUNDED" else {}
                  for b in rec["binds_new"]]
            binds = [{"state": b["state"], "evidence": ev}
                     for b, ev in zip(rec["binds_new"], bs)]
            cs = [flip_blanks(c, BLANKABLE, cb) for c in cells]
            per[tag] = x_counts(binds, cs, key)
        results[name] = per
    return results


def s2_score_blank_invariance(rec, s1, s2):
    """空欄の入れ替えで G-1〜G-4・N-1〜N-2 が動かないこと(採点器の側)。"""
    claims = {c["id"]: c for c in rec["claims"]}
    scorable = sorted(cid for cid, c in claims.items() if c.get("scorable"))
    out = {}
    for tag, to in (("そのまま", None), ("engine 側を空文字", "")):
        bn = {}
        for b in rec["binds_new"]:
            b = copy.deepcopy(b)
            if b["state"] == "GROUNDED" and b.get("evidence"):
                b["evidence"] = flip_blanks(b["evidence"], BLANKABLE, to)
            bn[b["claim_id"]] = b
        t = S.tally(bn, claims, scorable, s1, s2)
        out[tag] = {k: t[k] for k in ("g1", "g2", "g3", "e2", "hold_total",
                                      "hold_ok", "n1", "n2", "agree_4",
                                      "parent_filtered")}
    for tag, to in (("席側を空文字", ""),):
        a1 = {k: flip_blanks(v, L.FIELDS, to) for k, v in s1.items()}
        a2 = {k: flip_blanks(v, L.FIELDS, to) for k, v in s2.items()}
        bn = {b["claim_id"]: b for b in rec["binds_new"]}
        t = S.tally(bn, claims, scorable, a1, a2)
        out[tag] = {k: t[k] for k in ("g1", "g2", "g3", "e2", "hold_total",
                                      "hold_ok", "n1", "n2", "agree_4",
                                      "parent_filtered")}
    return out


# ----------------------------------------------------------- S-3 / S-4 / S-5
FIELD_TO_EV = {f["key"]: f["from"] for f in L.SPEC["fields"]}


def binds_from_labels(rec, s1, s2, tweak=None, perturb_field=None):
    """**正解ラベルをそのまま engine の答えに変える**(恒等試験の入力)。

    `tweak` は席の字の揺れを作る関数(S-4)。
    `perturb_field` を渡すと**その欄だけを壊す**(S-5)。
    """
    claims = {c["id"]: c for c in rec["claims"]}
    scorable = sorted(cid for cid, c in claims.items() if c.get("scorable"))
    binds, n_label, n_verdict, n_perturbed = {}, 0, 0, 0
    for cid in scorable:
        label, _ = S.confirmed(s1.get(cid, {}), s2.get(cid, {}), L.FIELDS)
        if label[0] != "label":
            n_verdict += 1
            binds[cid] = {"claim_id": cid, "state": "UNVERIFIABLE",
                          "evidence": None, "route": None, "pointer": None,
                          "hold_reason": "(恒等試験: ラベルが保留)"}
            continue
        n_label += 1
        ev = {}
        for key, v in zip(L.FIELDS, label[1]):
            ev[FIELD_TO_EV[key]] = v
        if tweak:
            ev = tweak(ev)
        if perturb_field:
            src = FIELD_TO_EV[perturb_field]
            cur = ev.get(src)
            if cur not in (None, ""):
                ev[src] = (str(int(cur) + 1) if perturb_field == "値"
                           else u"%s_X" % cur)
                n_perturbed += 1
        binds[cid] = {"claim_id": cid, "state": "GROUNDED", "evidence": ev,
                      "route": "R-1", "pointer": "(恒等試験)",
                      "hold_reason": None}
    return binds, claims, scorable, n_label, n_verdict, n_perturbed


def wobble(ev):
    """席が書きうる字の揺れ(S-4)。**値は同じまま、字だけ崩す。**"""
    ev = dict(ev)
    if ev.get("value") not in (None, ""):
        ev["value"] = u"{:,}".format(int(ev["value"])) + u"円"
    if ev.get("parent"):
        ev["parent"] = ev["parent"].replace(u">", u" ＞ ")
    for k in ("scope", "name", "column"):
        if ev.get(k):
            ev[k] = u" " + ev[k] + u"　"
    return ev


def wobble_changed():
    """`wobble` が**実際に字を変えた欄**を数える(S-4 が空でないことの証拠)。"""
    ev = {"scope": u"一般会計", "parent": u"福祉費>子供費", "name": u"児童費",
          "column": u"支出済額", "value": u"1234567"}
    w = wobble(ev)
    return sorted(k for k in ev if w[k] != ev[k])


# 期待する入れ替えの札(**この集合が縮んだら落とす**。札を 1 つ落として
# 「全部同じ」を保つ、という緩め方を防ぐ)
TAGS_X = ("そのまま", "engine 側を空文字", "抜粋側を空文字", "両側を空文字")
TAGS_SCORE = ("そのまま", "engine 側を空文字", "席側を空文字")


def judge(report):
    """**報告から落ちた本を出す。**試験が壊した報告を食わせて赤を確かめられるよう、
    main から切り出してある(記憶 `guard-that-only-fires-on-failure.md`)。
    """
    fail = []
    r1 = report["S-1 空欄の不変性(X)"]
    folded, raw = r1["空欄を畳む"], r1["生の norm"]
    for name, per in (("空欄を畳む", folded), ("生の norm", raw)):
        if tuple(per) != TAGS_X:
            fail.append("S-1 入れ替えの札が %s の側で縮んだ: %s" % (name, list(per)))
    if len({json.dumps(v, sort_keys=True) for v in folded.values()}) != 1:
        fail.append("S-1 空欄を畳んだ鍵が入れ替えで動いた: %s" % folded)
    if len({json.dumps(v, sort_keys=True) for v in raw.values()}) == 1:
        fail.append("S-1 **生の norm でも動かなかった**。この試験は段 8 の型を"
                    "検出できていない(外れようがない予測になっている)")

    r2 = report["S-2 空欄の不変性(採点)"]
    if tuple(r2) != TAGS_SCORE:
        fail.append("S-2 入れ替えの札が縮んだ: %s" % list(r2))
    if len({json.dumps(v, sort_keys=True) for v in r2.values()}) != 1:
        fail.append("S-2 採点の数が空欄の入れ替えで動いた: %s"
                    % json.dumps(r2, ensure_ascii=False))

    r3 = report["S-3 恒等"]
    if not (r3["G-1"] == r3["ラベルが答えの行"] and r3["G-2"] == 0
            and r3["G-3"] == 0
            and r3["保留の分母"] == r3["ラベルが保留の行"]
            and r3["正しく保留"] == r3["ラベルが保留の行"]):
        fail.append("S-3 恒等が崩れた(正解を入れて満点にならない): %s"
                    % json.dumps(r3, ensure_ascii=False))

    r4 = report["S-4 退化値"]
    if not (r4["G-1"] == r4["ラベルが答えの行"] and r4["G-2"] == 0
            and r4["G-3"] == 0):
        fail.append("S-4 字の揺れで恒等が崩れた: %s"
                    % json.dumps(r4, ensure_ascii=False))
    if not r4.get("揺れが字を変えた欄"):
        fail.append("S-4 **字の揺れが 1 欄も字を変えていない**(試験が空になっている)")

    r5 = report["S-5 逆(緩すぎない)"]
    if tuple(sorted(r5)) != tuple(sorted(L.FIELDS)):
        fail.append("S-5 欄が足りない: %s" % sorted(r5))
    for key, v in r5.items():
        if v["壊した行"] == 0:
            fail.append("S-5 欄 %s を**1 行も壊していない**(逆の試験が空)" % key)
        if v["G-1"] != v["期待 G-1"] or v["G-2"] != v["期待 G-2"]:
            fail.append("S-5 欄 %s を壊しても照合が外れない(照合器が緩い): %s"
                        % (key, json.dumps(v, ensure_ascii=False)))
    return fail


def main():
    set_alias()
    rec, mat, s1, s2 = load()
    report = {}

    report["S-1 空欄の不変性(X)"] = s1_blank_invariance(rec, mat)
    report["S-2 空欄の不変性(採点)"] = s2_score_blank_invariance(rec, s1, s2)

    b, claims, scorable, n_lab, n_ver, _ = binds_from_labels(rec, s1, s2)
    t = S.tally(b, claims, scorable, s1, s2)
    report["S-3 恒等"] = {
        "ラベルが答えの行": n_lab, "ラベルが保留の行": n_ver,
        "G-1": t["g1"], "G-2": t["g2"], "G-3": t["g3"],
        "保留の分母": t["hold_total"], "正しく保留": t["hold_ok"]}

    b, claims, scorable, n_lab4, _, _ = binds_from_labels(
        rec, s1, s2, tweak=wobble)
    t4 = S.tally(b, claims, scorable, s1, s2)
    report["S-4 退化値"] = {
        "G-1": t4["g1"], "G-2": t4["g2"], "G-3": t4["g3"],
        "ラベルが答えの行": n_lab4,
        "揺れが字を変えた欄": wobble_changed(),
        "入れた揺れ": "値にカンマと「円」/ 親を全角 ＞ と空白 / 名前の前後に空白"}

    r5 = {}
    for key in L.FIELDS:
        b, claims, scorable, n_lab5, _, n_pert = binds_from_labels(
            rec, s1, s2, perturb_field=key)
        t5 = S.tally(b, claims, scorable, s1, s2)
        r5[key] = {"壊した行": n_pert, "G-1": t5["g1"], "G-2": t5["g2"],
                   "期待 G-1": n_lab5 - n_pert, "期待 G-2": n_pert}
    report["S-5 逆(緩すぎない)"] = r5

    fail = judge(report)
    print("=== 採点器の正規化の対称性(人間の指示 2026-10-16)===")
    for k, v in report.items():
        print("%s: %s" % (k, json.dumps(v, ensure_ascii=False)))
    print()
    if fail:
        print("**落ちた %d 本:**" % len(fail))
        for f in fail:
            print("  - %s" % f)
    else:
        print("5 本すべて通った。**閾値は 1 つも触っていない。**")

    rec_out = {"purpose": ("採点器の**両側の正規化が対称か**。"
                           "人間の指示 2026-10-16。**閾値ではなく測定器の検査**"),
               "instrument": "measure/sheet_m8_score_2026-10-16.py",
               "material": "段 8 の凍結した binds・材料・2 席の回答",
               "checks": report, "failures": fail,
               "note": ("S-1 は**生の norm でも動かなかったら落とす**。"
                        "動かないなら、その試験は段 8 の型(片側 `None`・片側 `\"\"`)を"
                        "検出できていない。S-5 が無いと S-3 は無意味である"
                        "(何でも一致する照合器なら S-3 は満点になる)")}
    json.dump(rec_out, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print("->", OUT)
    if fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
