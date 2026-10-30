# -*- coding: utf-8 -*-
"""A / B / C を採点する(封 docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md §3・§5)。

**主比較は A 対 C。B(Core 単体)は参考群で、勝っても製品の結論にしない。**

  **A** = 席の答えそのまま
  **C** = **A と同じ答え**に Core の検証を当てたもの(**入力差ゼロ・生成は 1 回**)
  **B** = `fixtures/sheet/errdet_core_2026-10-17.json` の束ねた変種の結果(参考群)

**C の検証は封 §5-3 の 4 値。**引き当ては追記の `reach()`(**M-3′**)を使い、
**封の M-3(一意のセル)での数も併記する。**

**封が字で書いていない所を 2 つ、ここで埋めた(答えを見る前に commit する)。**
  (a) 席が 6 欄を答え、かつ `不一致の種類` が `不明` 以外 ⇒ **不一致の申告 = 検出**。
      `不明` なら **確認済み**(= 誤りなら見落とし)。封 §3-1 の 2 つの字を
      両方立てるには、この境目を決める必要がある。
  (b) 席が 6 欄を出していない(`根拠なし` / `判定不能`)とき、**C は検証する対象が無い**。
      だから **C は席の答えをそのまま引き継ぐ**(`根拠なし` ⇒ 検出 / `判定不能` ⇒ 保留)。

    python3 measure/sheet_errdet_score_2026-10-17.py
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
COREREC = os.path.join(FX, "errdet_core_2026-10-17.json")
MATREC = os.path.join(FX, "errdet_material_2026-10-17.json")
GOLD = os.path.join(FX, "poc_gold_2026-10-17.json")
OUT = os.path.join(FX, "errdet_score_2026-10-17.json")
SEAL = "docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md"
TRAP_ID = "R035"
KIND_FIELD = "不一致の種類"
HOLD_WORDS = ("判定不能",)
NOGROUND_WORDS = ("根拠なし",)
SEATS = (("seat1", "claude-sonnet-4-5"), ("seat2", "claude-haiku-4-5"))


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


S = _mod("abscore_for_errdet", "sheet_poc_ab_score_2026-10-17.py")
A3 = _mod("m3add_for_errdet", "sheet_poc_m3_addendum_2026-10-17.py")
CO = _mod("core_for_errdet_score", "sheet_errdet_core_2026-10-17.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def six(a):
    """6 欄を答えているか(verdict でないか)。"""
    return all(f in a for f in ("会計", "階層", "親", "科目名", "列", "値"))


def classify_seat(a):
    """**A の答え**を 検出 / 保留 / 確認済み に割る(封 §3-1 + 上の (a))。"""
    v = a.get("verdict")
    if v in NOGROUND_WORDS:
        return "検出"
    if v in HOLD_WORDS or not six(a):
        return "保留"
    if a.get(KIND_FIELD, "不明") != "不明":
        return "検出"
    return "確認済み"


def verify(a, want):
    """**C の検証**(封 §5-3 の 4 値)。`reach()`(M-3′)を使う。"""
    ok, why, _n = A3.reach(a, want)
    if ok:
        return "確認済み", None
    if why == "原資料に当たる行が無い":
        return "確認できない(参照先が無い)", why
    if why == "答えが住所になっていない":
        return "確認できない(参照先が無い)", why
    if why and why.startswith("当たった行の値が揺れる"):
        return "確認できない(値が一意でない)", why
    return "原資料と一致しない", why


def classify_c(a, want, strict=False):
    """**C の答え**を 検出 / 保留 / 確認済み に割る(上の (b) を含む)。"""
    if not six(a):
        # **検証する対象が無い。席の答えをそのまま引き継ぐ**
        return classify_seat(a), "席の答えを引き継いだ(住所が無い)", None
    if strict:
        ok, why, _c = S.resolve(a, want)
        out = ("確認済み" if ok else
               ("原資料と一致しない"
                if (why or "").startswith("到達したセルの値が主張と違う")
                else "確認できない"))
    else:
        out, why = verify(a, want)
    kind = {"確認済み": "確認済み", "原資料と一致しない": "検出"}.get(out, "保留")
    return kind, out, why


def main():
    if os.path.exists(OUT):
        raise SystemExit("採点が既に在る: %s(採点し直さない)" % OUT)
    mk = load(MAKE)
    planted = {p["id"]: p for p in mk["植えた誤り"]}
    core = load(COREREC)
    gold = {r["id"]: r for r in load(GOLD)["rows"]}
    bundle = mk["束ねた変種"]["本文"]
    claims, _b = CO.run_core(bundle)
    want = {c["id"]: c["value"] for c in claims}

    arms, rows_by_arm = {}, {}
    for seat, model in SEATS:
        rec = load(os.path.join(FX, "errdet_answers_%s_2026-10-17.json" % seat))
        a = {x["id"]: x for x in rec["answers"]}
        for arm, is_c in (("A %s" % seat, False), ("C %s" % seat, True)):
            rows = []
            for cid in sorted(a):
                ans = a[cid]
                if is_c:
                    kind, out, why = classify_c(ans, want[cid])
                    skind, sout, _sw = classify_c(ans, want[cid], strict=True)
                else:
                    kind, out, why = classify_seat(ans), None, None
                    skind, sout = kind, None
                rows.append({"id": cid, "答え": kind, "C の出力": out,
                             "理由": why, "封の M-3 での答え": skind,
                             "封の M-3 での出力": sout,
                             "種類の申告": ans.get(KIND_FIELD, "不明"),
                             "6 欄": six(ans), "verdict": ans.get("verdict"),
                             "住所": {k: ans.get(k) for k in
                                    ("会計", "階層", "親", "科目名", "列", "値")}
                             if six(ans) else None})
            rows_by_arm[arm] = rows
            arms[arm] = {"seat": seat, "model": model, "C か": is_c}

    def tally(arm):
        rows = {r["id"]: r for r in rows_by_arm[arm]}
        err, unalt = [], collections.Counter()
        fa = []
        for cid, r in sorted(rows.items()):
            if cid in planted:
                p = planted[cid]
                ref = r["住所"]
                err.append({
                    "id": cid, "型": p["型"], "群": p["群"],
                    "Core が結べた主張か": p["Core が結べた主張か"],
                    "答え": r["答え"],
                    "検出-1 誤りだと言えた": r["答え"] == "検出",
                    "保留": r["答え"] == "保留",
                    "見落とし": r["答え"] == "確認済み",
                    "検出-2 正しい根拠": (S.same_row(ref, p["正しい参照先(改変前)"])
                                  if ref else None),
                    "検出-3 種類": r["種類の申告"],
                    "検出-3 正解ラベル": p["誤りの種類(正解ラベル)"],
                    "検出-3 一致": (r["答え"] == "検出"
                               and r["種類の申告"]
                               == p["誤りの種類(正解ラベル)"]),
                    "封の M-3 での答え": r["封の M-3 での答え"]})
            elif cid == TRAP_ID:
                pass
            else:
                unalt[r["答え"]] += 1
                if r["答え"] == "検出":
                    fa.append(cid)
        trap = rows[TRAP_ID]
        return {
            "誤りの採点": err,
            "検出": [e["id"] for e in err if e["検出-1 誤りだと言えた"]],
            "保留": [e["id"] for e in err if e["保留"]],
            "見落とし": [e["id"] for e in err if e["見落とし"]],
            "検出-2 正しい根拠": [e["id"] for e in err
                          if e["検出-2 正しい根拠"] is True],
            "検出-3 種類を特定": [e["id"] for e in err if e["検出-3 一致"]],
            "無改変(26 件。罠は別記)": dict(unalt), "偽警報の id": fa,
            "罠(%s)" % TRAP_ID: {"答え": trap["答え"],
                                "種類の申告": trap["種類の申告"],
                                "**文書は正しいのに一致しないと言ったか**":
                                    trap["答え"] == "検出"},
            "封の M-3 での見落とし": [e["id"] for e in err
                            if e["封の M-3 での答え"] == "確認済み"],
            "封の M-3 での偽警報": [r["id"] for r in rows_by_arm[arm]
                           if r["id"] not in planted and r["id"] != TRAP_ID
                           and r["封の M-3 での答え"] == "検出"],
        }

    t = {arm: tally(arm) for arm in rows_by_arm}
    b_err = {r["id"]: r for r in core["束ねた変種"]["誤りの採点"]}
    b = {"検出": sorted(i for i, r in b_err.items() if r["答え"] == "検出"),
         "保留": sorted(i for i, r in b_err.items() if r["答え"] == "保留"),
         "見落とし": sorted(i for i, r in b_err.items() if r["答え"] == "確認済み"),
         "無改変": core["束ねた変種"]["無改変"],
         "検出-3 種類を特定": core["検出-3 種類を特定"]["ids"],
         "注": "**参考群。勝っても製品の結論にしない**"}

    judge = []
    for seat, _m in SEATS:
        a, c = t["A %s" % seat], t["C %s" % seat]
        g1 = len(c["見落とし"]) < len(a["見落とし"])
        g2 = len(c["偽警報の id"]) <= len(a["偽警報の id"])
        judge.append({
            "席": seat,
            "G-1 見落としが減る": {"A": len(a["見落とし"]), "C": len(c["見落とし"]),
                          "満たした": g1},
            "G-2 偽警報が増えない": {"A": len(a["偽警報の id"]),
                           "C": len(c["偽警報の id"]), "満たした": g2},
            "判定": ("**C が A を上回った(この条件で)**" if (g1 and g2) else
                   ("**G-1 のみ**" if g1 else
                    ("**G-2 のみ**" if g2 else "**どちらも満たさない**"))),
            "注": ("**両方でなければ「上回った」と書かない**(封 §5-4)。"
                  "**差が無ければ「機械検証を加える価値はこの条件では"
                  "確認できない」と書く**")})

    costs = {}
    for seat, _m in SEATS:
        r = load(os.path.join(FX, "errdet_answers_%s_2026-10-17.json" % seat))
        costs[seat] = {"model": r["model"], "費用": r["費用"],
                       "累計": r["費用の累計"],
                       "機械検査に落ちた件": len(r["機械検査に落ちた件"]),
                       "足した欄で落ちた件": len(r["足した欄で落ちた件"]),
                       "やり直し": r["regenerated"]}
    total = max(c["累計"]["2 席の合計の上限"] for c in costs.values())

    rec = {"seal": SEAL, "step": "封 §8 の 5",
           "**主比較は A 対 C。B は参考群**": True,
           "**A と C は同じ生成を共有する(入力差ゼロ)**":
               load(MATREC)["**A と C は同じ材料・同じ生成を共有する(入力差ゼロ)**"],
           "封が書いていなかった 2 点をここで決めた(答えを見る前に commit した)": [
               "(a) 6 欄 + 種類の申告が `不明` 以外 ⇒ 不一致の申告 = 検出。"
               "`不明` なら確認済み",
               "(b) 住所が無い答え(根拠なし / 判定不能)は C に検証する対象が無いので、"
               "**席の答えをそのまま引き継ぐ**"],
           "費用": {"席ごと": costs, "2 席の合計の上限": total,
                  "人間が決めた上限": 4.0, "上限の中か": total <= 4.0,
                  "注": "**全部が出力だと仮定した上限。実費はこれより小さい**"},
           "**判定(封 §5-4 の G-1・G-2)**": judge,
           "A / C の内訳": {arm: {k: v for k, v in val.items()
                            if k != "誤りの採点"}
                       for arm, val in t.items()},
           "B(参考群)": b,
           "誤りの型ごと": {arm: {
               e["型"]: e["答え"] for e in val["誤りの採点"]}
               for arm, val in t.items()},
           "誤りの件ごと": {arm: val["誤りの採点"] for arm, val in t.items()},
           "件ごとの記録(35 件)": {arm: rows_by_arm[arm] for arm in rows_by_arm},
           "limits": [
               "**誤りを示唆する問いの下での検出性能である。**"
               "通常の報告文を自然に読む場面の検出性能とは区別する(人間の指示)。",
               "**無改変 26 件で偽警報が増えなかったとしても、"
               "あらゆる正しい主張に対する偽警報率が低いとまでは言えない**(人間の指示)。",
               "**人工の誤りでの合格を、顧客価値や売却価値の証明にしない**(人間の指示)。",
               "**B は参考群である。**",
               "**2 席の一致を証拠に数えない**(CLAUDE.md 8(2))。",
           ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=== 誤り検出 A / B / C の採点(封 §3・§5)===")
    print("%-14s %-22s %-18s %-14s %s"
          % ("方式", "検出", "保留", "見落とし", "偽警報(無改変 26)"))
    for arm in sorted(t):
        v = t[arm]
        print("%-14s %-22s %-18s %-14s %s"
              % (arm, "%d %s" % (len(v["検出"]), v["検出"]),
                 "%d %s" % (len(v["保留"]), v["保留"]),
                 "%d %s" % (len(v["見落とし"]), v["見落とし"]),
                 "%d %s" % (len(v["偽警報の id"]), v["偽警報の id"])))
    print("%-14s %-22s %-18s %-14s %s"
          % ("B(参考群)", "%d %s" % (len(b["検出"]), b["検出"]),
             "%d %s" % (len(b["保留"]), b["保留"]),
             "%d %s" % (len(b["見落とし"]), b["見落とし"]),
             "%d" % b["無改変"]["偽警報"]))
    print("--- 検出-2 / 検出-3 ---")
    for arm in sorted(t):
        print("%-14s 正しい根拠 %d / 種類を特定 %d"
              % (arm, len(t[arm]["検出-2 正しい根拠"]),
                 len(t[arm]["検出-3 種類を特定"])))
    print("--- 罠(%s)---" % TRAP_ID)
    for arm in sorted(t):
        print("%-14s %s" % (arm, json.dumps(t[arm]["罠(%s)" % TRAP_ID],
                                            ensure_ascii=False)))
    print("--- 封の M-3(一意のセル)で測ると ---")
    for arm in sorted(t):
        print("%-14s 見落とし %s / 偽警報 %s"
              % (arm, t[arm]["封の M-3 での見落とし"],
                 t[arm]["封の M-3 での偽警報"]))
    print("--- **判定** ---")
    for j in judge:
        print("%s: G-1 %s / G-2 %s -> %s"
              % (j["席"], j["G-1 見落としが減る"], j["G-2 偽警報が増えない"],
                 j["判定"]))
    print("費用: 合計の上限 %.4f USD(上限 4 USD の中か %s)"
          % (total, total <= 4.0))
    print("->", OUT)


if __name__ == "__main__":
    main()
