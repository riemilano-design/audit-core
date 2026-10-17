# -*- coding: utf-8 -*-
"""方式 C を採点する(封 docs/DOMAIN1_POC_C_SEAL_2026-10-17.md §4)。

**A / B の採点器を import してそのまま使う。C 用に書き直さない**(封 §4)。
`score_arm` / `resolve` / `same_row` / `col_match` / `scope_match` /
`answer_of_seat` / `answer_of_core` は 1 つの持ち主(`sheet_poc_ab_score_2026-10-17.py`)。
M-3′ は追記の `reach()` を使う。**どちらも A にも C にも同じ関数。**

**門**: A1 / A2 / B を**ここで採り直して、凍結した記録と一致することを確かめる。**
一致しなければ採点を書かない(採点器が動いていたら C と A を比べられない)。

席は**モデルで対にする**(C1 ↔ A1 = sonnet / C2 ↔ A2 = haiku)。
**2 席の一致は証拠に数えない**(CLAUDE.md 8(2))。

    python3 measure/sheet_poc_c_score_2026-10-17.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
GOLD = os.path.join(FX, "poc_gold_2026-10-17.json")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")
A1P = os.path.join(FX, "m11_answers_seat1_2026-10-16.json")
A2P = os.path.join(FX, "m11_answers_seat2_2026-10-16.json")
C1P = os.path.join(FX, "poc_c_answers_seat1_2026-10-17.json")
C2P = os.path.join(FX, "poc_c_answers_seat2_2026-10-17.json")
ABREC = os.path.join(FX, "poc_ab_score_2026-10-17.json")
MATREC = os.path.join(FX, "poc_c_material_2026-10-17.json")
OUT = os.path.join(FX, "poc_c_score_2026-10-17.json")
SEAL = "docs/DOMAIN1_POC_C_SEAL_2026-10-17.md"

A1, A2 = "A1 一般 LLM(sonnet)", "A2 一般 LLM(haiku)"
C1, C2 = "C1 一般 LLM + 証拠(sonnet)", "C2 一般 LLM + 証拠(haiku)"
B = "B Audit Core"
PAIRS = ((C1, A1), (C2, A2))       # **同じモデル・同じ順序で対にする**


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


S = _mod("abscore_for_c", "sheet_poc_ab_score_2026-10-17.py")
A3 = _mod("m3add_for_c", "sheet_poc_m3_addendum_2026-10-17.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def answers_of(path):
    return {a["id"]: a for a in load(path)["answers"]}


def core_row(b):
    """道具が特定した行を**正解集合と同じ形**に開く(`same_row` を使い回すため)。"""
    ev = b.get("evidence") or {}
    if b["state"] != "GROUNDED":
        return None
    return {"会計(印字)": ev.get("scope"), "会計(接頭辞なし)": ev.get("scope"),
            "階層": ev.get("level"), "親": ev.get("parent"),
            "科目名": ev.get("name"), "列": ev.get("column"),
            "値": ev.get("value")}


def unfounded(ans, want):
    """**原資料に無い数を在るかのように答えた**件(追記と同じ条件)。"""
    hit, why, _n = A3.reach(ans, want)
    return (not hit) and why == "到達した行の値が主張と違う"


def check_a_reproduces(res):
    """**A1 / A2 / B が凍結した記録と一致すること。**違えば採点を書かない。"""
    want = load(ABREC)["主採点(寛容な会計)"]
    diff = []
    for name in (A1, A2, B):
        for m in ("M-1 誤接続率", "M-2 回収率", "M-3 根拠の再現性"):
            if res[name][m] != want[name][m]:
                diff.append({"方式": name, "指標": m,
                             "いま": res[name][m], "記録": want[name][m]})
        if res[name]["正解集合"] != want[name]["正解集合"]:
            diff.append({"方式": name, "指標": "正解集合",
                         "いま": res[name]["正解集合"],
                         "記録": want[name]["正解集合"]})
    if diff:
        raise SystemExit("**採点器が動いている: %s**"
                         % json.dumps(diff[:4], ensure_ascii=False))
    return True


def verdict(pairs):
    """封 §4-2 の**判定の順**。**3 だけ増えても 1・2 が悪化したら改善と書かない。**"""
    out = []
    for c, a in pairs:
        d = pairs[(c, a)]
        bad_wrong = d["誤接続の差"] > 0
        bad_recall = d["回収の差"] < 0
        better_detect = d["検出の差"] > 0
        if bad_wrong:
            v = "**悪化(誤接続が増えた)。検出の改善で相殺しない**"
        elif bad_recall and better_detect:
            v = "**代価つきの変化(検出は増えたが回収が落ちた)。改善とは書かない**"
        elif bad_recall:
            v = "**悪化(回収が落ちた)**"
        elif better_detect:
            v = "**改善(誤接続は増えず・回収は落ちず・検出が増えた)**"
        else:
            v = "**差が出なかった**"
        out.append({"席": c, "対照": a, "判定": v, "内訳": d})
    return out


def main():
    if os.path.exists(OUT):
        raise SystemExit("採点が既に在る: %s(採点し直さない)" % OUT)
    gold = load(GOLD)
    rows = gold["rows"]
    rec_in = load(BINDS)
    claims = {c["id"]: c for c in rec_in["claims"]}
    bn = {b["claim_id"]: b for b in rec_in["binds_new"]}
    seats = {A1: answers_of(A1P), A2: answers_of(A2P),
             C1: answers_of(C1P), C2: answers_of(C2P)}
    arms = {name: {r["id"]: S.answer_of_seat(a.get(r["id"])) for r in rows}
            for name, a in seats.items()}
    arms[B] = {r["id"]: S.answer_of_core(bn[r["id"]]) for r in rows}

    res, strict = {}, {}
    for name, ans in arms.items():
        res[name] = S.score_arm(name, ans, rows, claims, strict_scope=False)
        strict[name] = S.score_arm(name, ans, rows, claims, strict_scope=True)
    check_a_reproduces(res)                 # **採点器が動いていないことの門**

    # ---------------------------------------------------------------- M-3′
    m3p = {}
    for name, ans in arms.items():
        n = ok = 0
        why = collections.Counter()
        for r in rows:
            kind, a, _h = ans[r["id"]]
            if kind != "接続":
                continue
            n += 1
            hit, w, _nf = A3.reach(a, claims[r["id"]]["value"])
            if hit:
                ok += 1
            else:
                why[w] += 1
        m3p[name] = {"接続した件": n, "到達できた": ok,
                     "rate": (float(ok) / n) if n else None,
                     "到達できない理由": dict(why)}

    # ------------------------------------------------------------ D-1〜D-5
    core_ok = sorted(cid for cid in bn if bn[cid]["state"] == "GROUNDED")
    core_held = sorted(cid for cid in bn if bn[cid]["state"] != "GROUNDED")
    gold_of = {r["id"]: r for r in rows}
    mismatch_ids = sorted(r["id"] for r in rows if r["第 1 段"] == "値が不一致")

    d1, d2, d3, d5 = {}, {}, {}, {}
    for name, ans in arms.items():
        # D-1 追随率
        same = conn = 0
        for cid in core_ok:
            kind, a, _h = ans[cid]
            if kind != "接続":
                continue
            conn += 1
            if S.same_row(a, core_row(bn[cid])):
                same += 1
        d1[name] = {"道具が特定し、この方式も接続した件": conn,
                    "同じ行を答えた": same,
                    "rate": (float(same) / conn) if conn else None}
        # D-2 道具が絞れなかった件での挙動
        kinds = collections.Counter()
        right = wrong = held_g = 0
        for cid in core_held:
            kind, a, _h = ans[cid]
            kinds[kind] += 1
            g = gold_of[cid]["正解"]
            if not g:
                continue
            if kind == "接続":
                if S.same_row(a, g):
                    right += 1
                else:
                    wrong += 1
            else:
                held_g += 1
        d2[name] = {"道具が絞れなかった件": len(core_held),
                    "この方式の答え": dict(kinds),
                    "そのうち正解集合の 12 件": {"正しい接続": right,
                                      "誤接続": wrong, "保留など": held_g}}
        # D-3 不整合の検出
        det = []
        for cid in mismatch_ids:
            kind, a, h = ans[cid]
            det.append({"id": cid, "答え": kind, "保留の字": h,
                        "根拠のない確認": bool(kind == "接続" and
                                       unfounded(a, claims[cid]["value"]))})
        all_unf = sorted(r["id"] for r in rows
                         if ans[r["id"]][0] == "接続"
                         and unfounded(ans[r["id"]][1], claims[r["id"]]["value"]))
        d3[name] = {"「値が不一致」の件": det,
                    # **「検出できた」= 確認しなかった(接続しなかった)件**。
                    # 席は 6 欄か保留のどちらかしか書けないので、
                    # 食い違いを述べる道は**保留**しかない
                    "検出できた件数(確認しなかった)": sum(1 for x in det
                                          if x["答え"] != "接続"),
                    "**根拠のない確認(35 件すべてで)**": {"件数": len(all_unf),
                                              "ids": all_unf}}
        d5[name] = res[name]["別枠"]

    # D-4 A から落ちた件 / 増えた件(**席はモデルで対にする**)
    pairs = {}
    for c, a in PAIRS:
        rc = {x["id"]: x for x in res[c]["rows"]}
        ra = {x["id"]: x for x in res[a]["rows"]}
        lost = sorted(cid for cid in rc
                      if ra[cid].get("判定") == "正しい接続"
                      and rc[cid].get("判定") != "正しい接続")
        gained = sorted(cid for cid in rc
                        if ra[cid].get("判定") != "正しい接続"
                        and rc[cid].get("判定") == "正しい接続")
        pairs[(c, a)] = {
            "回収": {"C": res[c]["M-2 回収率"]["num"],
                   "A": res[a]["M-2 回収率"]["num"]},
            "回収の差": res[c]["M-2 回収率"]["num"] - res[a]["M-2 回収率"]["num"],
            "誤接続": {"C": res[c]["M-1 誤接続率"]["num"],
                    "A": res[a]["M-1 誤接続率"]["num"]},
            "誤接続の差": res[c]["M-1 誤接続率"]["num"] - res[a]["M-1 誤接続率"]["num"],
            "検出": {"C": len(d3[c]["**根拠のない確認(35 件すべてで)**"]["ids"]),
                   "A": len(d3[a]["**根拠のない確認(35 件すべてで)**"]["ids"])},
            "検出の差": (len(d3[a]["**根拠のない確認(35 件すべてで)**"]["ids"])
                    - len(d3[c]["**根拠のない確認(35 件すべてで)**"]["ids"])),
            "D-4 A から落ちた件": lost, "A に無く C で正しくなった件": gained,
            "別枠": {"C": res[c]["別枠"], "A": res[a]["別枠"]},
            "M-3": {"C": res[c]["M-3 根拠の再現性"],
                  "A": res[a]["M-3 根拠の再現性"]},
            "M-3′": {"C": m3p[c], "A": m3p[a]}}

    per_claim = []
    for r in rows:
        line = {"id": r["id"], "値": r["値"], "第 1 段": r["第 1 段"],
                "正解集合か": bool(r["正解"]), "別枠の理由": r.get("別枠の理由"),
                "道具の状態": bn[r["id"]]["state"]}
        for name in (A1, A2, C1, C2, B):
            x = [y for y in res[name]["rows"] if y["id"] == r["id"]][0]
            line[name] = {"答え": x["方式の答え"], "判定": x["判定"],
                          "保留の字": x.get("保留の字"),
                          "根拠の再現": x.get("根拠の再現")}
        per_claim.append(line)

    mat = load(MATREC)
    costs = {}
    for seat, p in (("seat1", C1P), ("seat2", C2P)):
        r = load(p)
        costs[seat] = {"model": r["model"], "order": r["order"],
                       "費用": r["費用"], "累計": r["費用の累計"],
                       "機械検査に落ちた件": len(r["機械検査に落ちた件"]),
                       "やり直し": r["regenerated"]}
    total = max(c["累計"]["2 席の合計の上限"] for c in costs.values())

    rec = {"seal": SEAL, "step": "封 §9 の 5",
           "採点器": ("**`sheet_poc_ab_score_2026-10-17.py` を import した。"
                   "C 用に書き直していない**"),
           "A を採り直して記録と一致": True,
           "正解集合": gold["正解集合"]["件数"], "別枠": gold["別枠"]["件数"],
           "入力": {"A が接頭": all(f["A が接頭"] for f in mat["files"]),
                  "足した字数": {f["seat"]: f["足した字数"] for f in mat["files"]},
                  "証拠の出どころ": mat["証拠の出どころ"],
                  "**B′ は使っていない**": mat["**B′(抜粋 76 行)は使っていない**"]},
           "費用": {"席ごと": costs, "2 席の合計の上限": total,
                  "人間が決めた上限": 4.0, "上限の中か": total <= 4.0,
                  "注": ("**全部が出力トークンだと仮定した上限。実費はこれより小さい。**"
                        "**推測した実費は書かない**")},
           "主採点(寛容な会計)": {k: {m: v[m] for m in
                              ("M-1 誤接続率", "M-2 回収率", "M-3 根拠の再現性",
                               "正解集合", "別枠")}
                           for k, v in res.items()},
           "**厳格な会計(印字のみ)。埋もれさせない**": {
               k: {m: v[m] for m in ("M-1 誤接続率", "M-2 回収率", "正解集合")}
               for k, v in strict.items()},
           "M-3′(追記の到達定義)": m3p,
           "D-1 追随率": d1, "D-2 道具が絞れなかった件での挙動": d2,
           "D-3 不整合の検出": d3, "D-5 別枠での挙動": d5,
           "D-4 と判定(**席はモデルで対にする**)": verdict(pairs),
           "**2 席の一致は証拠に数えない**": ("C1 と C2 を別々に採点した"
                                 "(CLAUDE.md 8(2))。**一致率は書かない**"),
           "件ごとの記録(35 件すべて)": per_claim}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=== 方式 C の採点(封 §4)===")
    print("正解集合 %d 件 / 別枠 %d 件" % (rec["正解集合"], rec["別枠"]))
    print("%-26s %-14s %-14s %-14s %s"
          % ("方式", "M-2 回収率", "M-1 誤接続率", "M-3′ 再現性", "別枠"))
    for name in (A1, C1, A2, C2, B):
        v, p = res[name], m3p[name]
        print("%-26s %5.1f%% (%2d/%2d) %5.1f%% (%2d/%2d) %5.1f%% (%2d/%2d) 推測 %d / 保留 %d"
              % (name, 100 * (v["M-2 回収率"]["rate"] or 0),
                 v["M-2 回収率"]["num"], v["M-2 回収率"]["den"],
                 100 * (v["M-1 誤接続率"]["rate"] or 0),
                 v["M-1 誤接続率"]["num"], v["M-1 誤接続率"]["den"],
                 100 * (p["rate"] or 0), p["到達できた"], p["接続した件"],
                 v["別枠"]["推測して答えた"], v["別枠"]["保留した"]))
    print("--- D-1 追随率(道具が特定した行をそのまま使ったか)---")
    for name in (C1, C2, A1, A2):
        d = d1[name]
        print("%-26s %s / %s" % (name, d["同じ行を答えた"],
                                 d["道具が特定し、この方式も接続した件"]))
    print("--- D-3 根拠のない確認(原資料に無い数を在るかのように答えた)---")
    for name in (A1, A2, C1, C2, B):
        print("%-26s %s" % (name, d3[name]["**根拠のない確認(35 件すべてで)**"]))
    print("--- D-4 と判定 ---")
    for v in rec["D-4 と判定(**席はモデルで対にする**)"]:
        print("%-26s 回収 %s / 誤接続 %s / 落ちた %s"
              % (v["席"], v["内訳"]["回収"], v["内訳"]["誤接続"],
                 v["内訳"]["D-4 A から落ちた件"] or "なし"))
        print("   **%s**" % v["判定"])
    print("費用: 2 席の合計の上限 %.4f USD(上限 4 USD の中か: %s)"
          % (total, total <= 4.0))
    print("->", OUT)


if __name__ == "__main__":
    main()
