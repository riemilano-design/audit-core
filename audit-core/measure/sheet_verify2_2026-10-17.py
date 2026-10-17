# -*- coding: utf-8 -*-
"""検証層の直し(封 docs/DOMAIN1_VERIFY2_SEAL_2026-10-17.md)。**費用 0 USD。**

**席の答えは読むだけ**(commit `1ab6a79` で凍結)。**engine も材料も正解ラベルも触らない。**
**変えるのは合成の規則 1 か所だけ。**

  **軸 1 誤りの存在**(3 値)・**軸 2 誤りの種類**・**軸 3 本来の参照先**を**別々に**出す。
  **検出 / 見落とし / 保留 / 偽警報を独立に数える。**罠は**別記**。

5 方式(封 §3): **A** 席そのまま / **B** Core 単体(参考群)/
**C′** 席 + Core(**申告を消さない**)/ **D** 席 + 素朴な値一致照合(**申告を使わない**)/
**D′** 席 + 素朴な値一致照合(**申告を残す**)。

**この便の数のほとんどは算術で決まる**(封 §0)。**「性能」という語を使わない。**

    python3 measure/sheet_verify2_2026-10-17.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAKE = os.path.join(FX, "errdet_make_2026-10-17.json")
MAT11 = os.path.join(FX, "m11_material_2026-10-16.json")
COREREC = os.path.join(FX, "errdet_core_2026-10-17.json")
OUT = os.path.join(FX, "verify2_2026-10-17.json")
SEAL = "docs/DOMAIN1_VERIFY2_SEAL_2026-10-17.md"
TRAP_ID = "R035"
KIND_FIELD = "不一致の種類"
SEATS = (("seat1", "claude-sonnet-4-5"), ("seat2", "claude-haiku-4-5"))
ARMS = ("A 席そのまま", "C′ 席 + Core", "D 席 + grep(申告を使わない)",
        "D′ 席 + grep(申告を残す)")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


SC = _mod("errdet_score_for_v2", "sheet_errdet_score_2026-10-17.py")
CO = SC.CO                         # Core の engine と ref_of
S = SC.S                           # same_row(A にも C にも同じもの)
A3 = SC.A3                         # reach(M-3′)
OPP = _mod("opp9_for_v2", "sheet_m9_opportunity_2026-10-16.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------ 席
def seat_says(a):
    """席が**何を言ったか**(封 §1-1 の左の列)。(言い分, 種類) を返す。

    **判定を 1 か所に置く。**「黙っている」だけが検証器に委ねられる。
    """
    kind = a.get(KIND_FIELD, "不明")
    v = a.get("verdict")
    if v == "根拠なし":
        return "誤りが在る", (kind if kind != "不明" else "値が原資料に無い")
    if v == "判定不能":
        return "判定できない", kind
    if not SC.six(a):
        return "判定できない", kind
    if kind != "不明":
        return "誤りが在る", kind
    return "黙っている", "不明"


# ------------------------------------------------------------------ 検証器
def grep_check(want, values):
    """**素朴な値一致照合。**封 §3 の字のまま ― 値の出現回数だけを見る。

    **席の住所を使わない。**だから `D` は実質「値の出現回数だけの検出器」である。
    """
    n = values.get(want, 0)
    if n == 0:
        return "原資料と一致しない"
    if n == 1:
        return "確認済み"
    return "確認できない(値が一意でない)"


def compose(says, checker_out):
    """**封 §1-1 の合成。席が言ったときは消さない。**

    席が黙っているときだけ検証器の判定を使う。**論理和。**
    """
    if says == "誤りが在る":
        return "誤りが在る"
    if says == "判定できない":
        return "判定できない"
    if checker_out == "原資料と一致しない":
        return "誤りが在る"
    if checker_out == "確認済み":
        return "確認済み"
    return "判定できない"


def axis2(seat_kind, axis1):
    """**軸 2 誤りの種類**(封 §1-2)。**検証器は言えないものを言わない。**"""
    if seat_kind != "不明":
        return seat_kind
    return "値が原資料に無い" if axis1 == "誤りが在る" else "不明"


def axis3_core(claim, bind):
    """**軸 3 本来の参照先**(封 §1-3)。Core の鍵が 1 通りのときだけ出す。"""
    return CO.ref_of(claim, bind)


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    mk = load(MAKE)
    planted = {p["id"]: p for p in mk["植えた誤り"]}
    cells = OPP.cells_of(OPP.extract_of(load(MAT11)))
    values = collections.Counter(c["value"] for c in cells)
    claims, binds = CO.run_core(mk["束ねた変種"]["本文"])
    cm = {c["id"]: c for c in claims}
    bm = {b["claim_id"]: b for b in binds}
    want = {c["id"]: c["value"] for c in claims}
    core = load(COREREC)

    out, rows_all = {}, {}
    for seat, model in SEATS:
        ans = {a["id"]: a for a in load(os.path.join(
            FX, "errdet_answers_%s_2026-10-17.json" % seat))["answers"]}
        for arm in ARMS:
            rows = []
            for cid in sorted(ans):
                a = ans[cid]
                says, kind = seat_says(a)
                addr = {k: a.get(k) for k in
                        ("会計", "階層", "親", "科目名", "列", "値")} \
                    if SC.six(a) else None
                if arm.startswith("A "):
                    ax1 = {"誤りが在る": "誤りが在る",
                           "判定できない": "判定できない",
                           "黙っている": "確認済み"}[says]
                    chk = None
                elif arm.startswith("C′"):
                    chk, _why = (SC.verify(a, want[cid]) if addr
                                 else ("確認できない(参照先が無い)", None))
                    ax1 = compose(says, chk)
                elif arm.startswith("D "):
                    chk = grep_check(want[cid], values)
                    ax1 = {"原資料と一致しない": "誤りが在る",
                           "確認済み": "確認済み"}.get(chk, "判定できない")
                else:
                    chk = grep_check(want[cid], values)
                    ax1 = compose(says, chk)
                ref = (axis3_core(cm[cid], bm[cid]) if arm.startswith("C′")
                       else None)
                src_ok = (A3.reach(addr, planted[cid]["植えた値"])[0]
                          if (addr and cid in planted) else None)
                rows.append({
                    "id": cid, "軸 1 誤りの存在": ax1,
                    "軸 2 誤りの種類": axis2(kind, ax1),
                    "軸 3 本来の参照先": ref,
                    "席の言い分": says, "席の申告": kind,
                    "検証器の出力": chk,
                    "席が指した住所(出どころ)": addr,
                    "出どころの行を指したか": src_ok})
            rows_all["%s / %s" % (arm, seat)] = rows
    for key, rows in rows_all.items():
        by = {r["id"]: r for r in rows}
        err, unalt, fa, a2, a3, src = [], collections.Counter(), [], [], [], []
        for cid, p in sorted(planted.items()):
            r = by[cid]
            ok2 = (r["軸 1 誤りの存在"] == "誤りが在る"
                   and r["軸 2 誤りの種類"] == p["誤りの種類(正解ラベル)"])
            ok3 = bool(r["軸 3 本来の参照先"]
                       and S.same_row(r["軸 3 本来の参照先"],
                                      p["正しい参照先(改変前)"]))
            err.append({"id": cid, "型": p["型"], "群": p["群"],
                        "Core が結べた主張か": p["Core が結べた主張か"],
                        "軸 1": r["軸 1 誤りの存在"],
                        "軸 2": r["軸 2 誤りの種類"],
                        "軸 2 正解ラベル": p["誤りの種類(正解ラベル)"],
                        "軸 2 一致": ok2,
                        "軸 3 を出せた": bool(r["軸 3 本来の参照先"]),
                        "軸 3 が正しい行": ok3,
                        "出どころの行を指した": r["出どころの行を指したか"]})
            if ok2:
                a2.append(cid)
            if ok3:
                a3.append(cid)
            if r["出どころの行を指したか"]:
                src.append(cid)
        for cid, r in sorted(by.items()):
            if cid in planted or cid == TRAP_ID:
                continue
            k = {"誤りが在る": "偽警報", "判定できない": "保留",
                 "確認済み": "確認済み"}[r["軸 1 誤りの存在"]]
            unalt[k] += 1
            if k == "偽警報":
                fa.append(cid)
        out[key] = {
            "検出": [e["id"] for e in err if e["軸 1"] == "誤りが在る"],
            "見落とし": [e["id"] for e in err if e["軸 1"] == "確認済み"],
            "保留": [e["id"] for e in err if e["軸 1"] == "判定できない"],
            "偽警報(無改変 26 件)": {"件数": len(fa), "ids": fa},
            "無改変 26 件の内訳": dict(unalt),
            "軸 2 種類を当てた": {"件数": len(a2), "ids": a2},
            "軸 3 本来の参照先が正しい": {"件数": len(a3), "ids": a3},
            "軸 3 を出せた": [e["id"] for e in err if e["軸 3 を出せた"]],
            "出どころの行を指した": {"件数": len(src), "ids": src},
            "罠(%s)" % TRAP_ID: {
                "軸 1": by[TRAP_ID]["軸 1 誤りの存在"],
                "軸 2": by[TRAP_ID]["軸 2 誤りの種類"],
                "**文書は正しいのに誤りが在ると言ったか**":
                    by[TRAP_ID]["軸 1 誤りの存在"] == "誤りが在る"},
            "誤りの件ごと": err}

    b = {"検出": sorted(i for i, r in
                      {x["id"]: x for x in core["束ねた変種"]["誤りの採点"]}.items()
                      if r["答え"] == "検出"),
         "保留": sorted(i for i, r in
                      {x["id"]: x for x in core["束ねた変種"]["誤りの採点"]}.items()
                      if r["答え"] == "保留"),
         "見落とし": [], "軸 2 種類を当てた": core["検出-3 種類を特定"]["ids"],
         "軸 3 本来の参照先が正しい": core["検出-2 正しい根拠を提示"]["ids"],
         "無改変 26 件の内訳": core["束ねた変種"]["無改変"],
         "注": "**参考群。製品の結論にしない**"}

    def n(key, field):
        v = out[key][field]
        return len(v["ids"]) if isinstance(v, dict) else len(v)

    k1 = "C′ 席 + Core / seat1"
    k1d = "D′ 席 + grep(申告を残す) / seat1"
    k1a = "A 席そのまま / seat1"
    k1D = "D 席 + grep(申告を使わない) / seat1"
    checks = {
        "H-1 C′ の検出は seat1 で 8 件(**算術**)": n(k1, "検出") == 8,
        "H-2 C′ の見落としは 0 件(seat1)": n(k1, "見落とし") == 0,
        "H-3 C′ の軸 3 は 4 / 8":
            out[k1]["軸 3 本来の参照先が正しい"]["件数"] == 4,
        "H-4 D′ の検出は C′ と同じ(**算術**)":
            n(k1d, "検出") == n(k1, "検出"),
        "H-5 D′ の軸 3 は 0 / 8":
            out[k1d]["軸 3 本来の参照先が正しい"]["件数"] == 0,
        "H-6 D の検出は 4 / 8": n(k1D, "検出") == 4,
        "H-7 罠で C′ は「誤りが在る」と言う(偽警報 0 → 1。**論理和の代価**)":
            out[k1]["罠(%s)" % TRAP_ID][
                "**文書は正しいのに誤りが在ると言ったか**"] is True
            and out[k1a]["罠(%s)" % TRAP_ID][
                "**文書は正しいのに誤りが在ると言ったか**"] is False,
        "H-8 無改変 26 件の偽警報は全方式 0 件(**算術**)":
            all(v["偽警報(無改変 26 件)"]["件数"] == 0 for v in out.values()),
        "H-9 軸 2 は C′ 8 / D′ 8 / D 2〜4 / B 2":
            (out[k1]["軸 2 種類を当てた"]["件数"] == 8
             and out[k1d]["軸 2 種類を当てた"]["件数"] == 8
             and 2 <= out[k1D]["軸 2 種類を当てた"]["件数"] <= 4
             and len(b["軸 2 種類を当てた"]) == 2),
        "H-10 C′ と D′ の差は軸 3 だけ":
            (out[k1]["検出"] == out[k1d]["検出"]
             and out[k1]["見落とし"] == out[k1d]["見落とし"]
             and out[k1]["軸 2 種類を当てた"] == out[k1d]["軸 2 種類を当てた"]
             and out[k1]["軸 3 本来の参照先が正しい"]
             != out[k1d]["軸 3 本来の参照先が正しい"]),
    }

    rec = {"seal": SEAL,
           "step": "封 §8 の 3。**費用 0 USD。席の答えは読むだけ**",
           "**この便の数のほとんどは算術で決まる。性能ではない**": True,
           "変えたもの": "**合成の規則 1 か所だけ**(封 §1)",
           "変えていないもの": ["engine", "索引", "別名表", "親の規則", "6 欄の鍵",
                        "正解ラベル", "誤りの材料", "席の答え"],
           "方式ごと": out, "B(参考群)": b,
           "予測の照合(H-1〜H-10)": checks,
           "**算術で決まる予測(手柄にしない)**": ["H-1", "H-4", "H-8"],
           "**測る意味が在った予測**": ["H-3", "H-5", "H-7", "H-10"],
           "limits": [
               "**同じ材料・凍結した席の答えである。設計の確認であって性能ではない**"
               "(封 §0・§7 の 1)。",
               "**既存製品は手元で測れない。**比べたのは**素朴な値一致照合**だけ"
               "(封 §3)。",
               "**D は席の住所を使わない**ので、実質「値の出現回数だけの検出器」である。",
               "**人工の誤り 8 件。**実際の文書の誤りの分布は測っていない。",
               "**罠(%s)は私の切り出しの欠陥であって文書の誤りではない。**" % TRAP_ID,
               "**B は参考群である。**",
           ],
           "件ごとの記録": rows_all}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=== 検証層の直し(同じ材料。費用 0。**性能ではない**)===")
    print("%-34s %-10s %-10s %-8s %-8s %-8s %s"
          % ("方式", "検出", "見落とし", "保留", "軸2", "軸3", "偽警報26"))
    for key in sorted(out):
        v = out[key]
        print("%-34s %-10s %-10s %-8s %-8s %-8s %s"
              % (key, len(v["検出"]), len(v["見落とし"]), len(v["保留"]),
                 v["軸 2 種類を当てた"]["件数"],
                 v["軸 3 本来の参照先が正しい"]["件数"],
                 v["偽警報(無改変 26 件)"]["件数"]))
    print("%-34s %-10s %-10s %-8s %-8s %-8s %s"
          % ("B Core 単体(参考群)", len(b["検出"]), 0, len(b["保留"]),
             len(b["軸 2 種類を当てた"]), len(b["軸 3 本来の参照先が正しい"]),
             b["無改変 26 件の内訳"]["偽警報"]))
    print("--- 罠(%s)---" % TRAP_ID)
    for key in sorted(out):
        print("%-34s %s" % (key, json.dumps(out[key]["罠(%s)" % TRAP_ID],
                                            ensure_ascii=False)))
    print("--- 予測の照合 ---")
    for k, v in checks.items():
        print("  %-62s %s" % (k, "当たり" if v else "**外れ**"))
    print("->", OUT)


if __name__ == "__main__":
    main()
