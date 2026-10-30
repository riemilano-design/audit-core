# -*- coding: utf-8 -*-
"""PoC 第 1 便: **方式 A(一般 LLM 単体)と方式 B(Audit Core)を採点する**。

封 `docs/DOMAIN1_POC_ABC_SEAL_2026-10-17.md` §4。**費用 0 USD**(どちらも凍結済み)。

  **A1** = `claude-sonnet-4-5`(段 11 の seat1) ― **1 席ずつ別に採点する**
  **A2** = `claude-haiku-4-5`(段 11 の seat2)   **2 席の一致を証拠に数えない**
                                              (CLAUDE.md 8(2))
  **B**  = Audit Core(段 11 の binds_new)

指標(封 §4。**分母を字で**):
  M-1 誤接続率        = 誤接続 / **正解集合**
  M-2 回収率          = 正しい接続 / **正解集合**(M-1 と必ず並べる)
  M-3 根拠の再現性    = 到達できた / **その方式が接続した件**
  M-4 失敗時の挙動    = **別枠**で推測したか / 保留したか

**6 欄 → 原資料のセルの引き当ては `resolve()` 1 つで、A にも B にも同じものを当てる**
(封 §4-1。記憶 `normalize-both-sides-of-a-comparison`)。
**pointer の有無は M-3 の分母にしない**(A に pointer は無い)。

会計の欄は**二重採点**(寛容 = 印字でも正本でも正解 / 厳格 = 印字のみ。封 §3)。

    python3 measure/sheet_poc_ab_score_2026-10-17.py
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
SEAT1 = os.path.join(FX, "m11_answers_seat1_2026-10-16.json")
SEAT2 = os.path.join(FX, "m11_answers_seat2_2026-10-16.json")
OUT = os.path.join(FX, "poc_ab_score_2026-10-17.json")
SEAL = "docs/DOMAIN1_POC_ABC_SEAL_2026-10-17.md"
HOLD_WORDS = ("判定不能", "根拠なし")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


G = _mod("gold_for_poc", "sheet_poc_gold_2026-10-17.py")
E = _mod("m5_for_poc", "sheet_m5_engine_2026-10-15.py")
M2 = E.M2
SURFACE = G.SURFACE
scope_forms = G.scope_forms
_IDX = {}


def index():
    """**canonicalize を通していない索引**(別名表を使わない)。"""
    if "raw" in _IDX:
        return _IDX["raw"]
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    _IDX["raw"] = E.fix_total_level(E.build_index(
        M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
        M2.parse_meisai(books[M2.MEISAI])))
    return _IDX["raw"]


def _s(x):
    return (x or "").replace(" ", "").replace("　", "").strip()


def _parent(x):
    return " > ".join(p.strip() for p in (x or "").split(">") if p.strip())


def col_match(a, b):
    """列の一致。**封 §2-4 の表層形を両側に当てる**(片側だけにしない)。"""
    if _s(a) == _s(b):
        return True
    for head, forms in SURFACE.items():
        f = {_s(head)} | {_s(x) for x in forms}
        if _s(a) in f and _s(b) in f:
            return True
    return False


def scope_match(a, b, strict=False):
    """会計の一致。**寛容なら印字形でも接頭辞なしでも可。厳格なら字そのまま。**

    **A にも B にも同じ関数を当てる**(封 §3)。
    """
    if strict:
        return _s(a) == _s(b)
    return bool({_s(x) for x in scope_forms(a)} & {_s(x) for x in scope_forms(b)})


def same_row(ans, gold, strict_scope=False):
    """6 欄が同じ行を指しているか。**判定を 1 か所に置く。**"""
    if ans is None or gold is None:
        return False
    return (scope_match(ans.get("会計"), gold["会計(印字)"], strict_scope)
            or scope_match(ans.get("会計"), gold["会計(接頭辞なし)"], strict_scope)) \
        and _s(ans.get("階層")) == _s(gold["階層"]) \
        and _parent(ans.get("親")) == _parent(gold["親"]) \
        and _s(ans.get("科目名")) == _s(gold["科目名"]) \
        and col_match(ans.get("列"), gold["列"]) \
        and int(ans.get("値") or 0) == int(gold["値"])


def resolve(ans, want_value):
    """**6 欄 → 原資料のセル。A にも B にも C にも同じ関数を当てる**(封 §4-1)。

    返すのは (到達できたか, 理由, セルの住所)。
    到達できた = **一意のセルが見つかり、その値が主張の金額と一致**すること。
    """
    if ans is None:
        return False, "答えが住所になっていない", None
    hits = []
    for e in index():
        if not scope_match(ans.get("会計"), e["scope"]):
            continue
        if _s(ans.get("階層")) != _s(e["level"]):
            continue
        if _parent(ans.get("親")) != _parent(e["parent"]):
            continue
        if _s(ans.get("科目名")) != _s(e["name"]):
            continue
        if not col_match(ans.get("列"), e["column"]):
            continue
        ev = e.get("evidence") or {}
        hits.append({"file": e["file"], "cell": ev.get("value_ref"),
                     "value": e["value"]})
    cells = {(h["file"], h["cell"]) for h in hits}
    if not hits:
        return False, "原資料に当たる行が無い", None
    if len(cells) > 1:
        return False, "一意に定まらない(%d セル)" % len(cells), None
    h = hits[0]
    if h["value"] != want_value:
        return False, ("到達したセルの値が主張と違う(%s != %s)"
                       % (h["value"], want_value)), h
    return True, None, h


def answer_of_seat(a):
    """席の答えを (接続か, 6 欄 or None, 保留の字) に開く。"""
    if a is None:
        return "欠け", None, None
    v = a.get("verdict")
    if v:
        return ("保留" if v in HOLD_WORDS else "判定不能"), None, v
    return "接続", a, None


def answer_of_core(b):
    """Core の bind を同じ形に開く。**VALUE_MISMATCH は「値の食い違いを検出」。**"""
    st = b["state"]
    if st == "GROUNDED":
        ev = b.get("evidence") or {}
        return "接続", {"会計": ev.get("scope"), "階層": ev.get("level"),
                      "親": ev.get("parent"), "科目名": ev.get("name"),
                      "列": ev.get("column"), "値": ev.get("value")}, None
    if st == "VALUE_MISMATCH":
        return "保留", None, "値の食い違いを検出"
    if st == "POINTER_NOT_FOUND":
        return "対象外", None, "範囲が特定できない"
    return "保留", None, b.get("hold_reason") or "保留"


def score_arm(name, answers, gold_rows, claims, strict_scope=False):
    """1 方式を採点する。**A にも B にも同じ関数。**"""
    out = {"方式": name, "正解集合": {"正しい接続": 0, "誤接続": 0, "保留": 0,
                                "判定不能": 0, "欠け": 0},
           "別枠": {"推測して答えた": 0, "保留した": 0, "判定不能": 0, "欠け": 0},
           "M-3": {"接続した件": 0, "到達できた": 0, "到達できない理由": {}},
           "rows": []}
    whys = collections.Counter()
    for r in gold_rows:
        cid = r["id"]
        kind, ans, hold = answers[cid]
        row = {"id": cid, "正解の状態": "正解集合" if r["正解"] else "別枠",
               "方式の答え": kind, "保留の字": hold}
        if kind == "接続":
            out["M-3"]["接続した件"] += 1
            ok, why, cell = resolve(ans, claims[cid]["value"])
            row["根拠の再現"] = ok
            row["住所"] = cell
            if ok:
                out["M-3"]["到達できた"] += 1
            else:
                whys[why] += 1
                row["到達できない理由"] = why
        if r["正解"]:
            if kind == "接続":
                hit = same_row(ans, r["正解"], strict_scope)
                row["判定"] = "正しい接続" if hit else "誤接続"
                out["正解集合"]["正しい接続" if hit else "誤接続"] += 1
                if not hit:
                    row["違った欄"] = [
                        f for f in ("会計", "階層", "親", "科目名", "列", "値")
                        if not same_row(dict(ans, **{}), r["正解"], strict_scope)
                        and str(_s(str(ans.get(f)))) !=
                        str(_s(str(r["正解"].get(f if f != "会計"
                                                 else "会計(印字)"))))]
            else:
                out["正解集合"][kind if kind in out["正解集合"] else "欠け"] += 1
                row["判定"] = kind
        else:
            if kind == "接続":
                out["別枠"]["推測して答えた"] += 1
                row["判定"] = "推測して答えた(正解不明)"
            elif kind == "保留":
                out["別枠"]["保留した"] += 1
                row["判定"] = "保留した"
            else:
                out["別枠"][kind if kind in out["別枠"] else "欠け"] += 1
                row["判定"] = kind
        out["rows"].append(row)
    out["M-3"]["到達できない理由"] = dict(whys)
    g = out["正解集合"]
    den = g["正しい接続"] + g["誤接続"] + g["保留"] + g["判定不能"] + g["欠け"]
    out["M-1 誤接続率"] = {"num": g["誤接続"], "den": den,
                      "rate": (float(g["誤接続"]) / den) if den else None}
    out["M-2 回収率"] = {"num": g["正しい接続"], "den": den,
                     "rate": (float(g["正しい接続"]) / den) if den else None}
    m3 = out["M-3"]
    out["M-3 根拠の再現性"] = {"num": m3["到達できた"], "den": m3["接続した件"],
                        "rate": (float(m3["到達できた"]) / m3["接続した件"])
                        if m3["接続した件"] else None}
    return out


def main():
    if os.path.exists(OUT):
        raise SystemExit("採点が既に在る: %s(採点し直さない)" % OUT)
    gold = json.load(io.open(GOLD, encoding="utf-8"))
    rec_in = json.load(io.open(BINDS, encoding="utf-8"))
    claims = {c["id"]: c for c in rec_in["claims"]}
    bn = {b["claim_id"]: b for b in rec_in["binds_new"]}
    s1 = {a["id"]: a for a in json.load(io.open(SEAT1, encoding="utf-8"))["answers"]}
    s2 = {a["id"]: a for a in json.load(io.open(SEAT2, encoding="utf-8"))["answers"]}
    rows = gold["rows"]
    arms = {
        "A1 一般 LLM(sonnet)": {r["id"]: answer_of_seat(s1.get(r["id"]))
                             for r in rows},
        "A2 一般 LLM(haiku)": {r["id"]: answer_of_seat(s2.get(r["id"]))
                            for r in rows},
        "B Audit Core": {r["id"]: answer_of_core(bn[r["id"]]) for r in rows},
    }
    res, strict = {}, {}
    for name, ans in arms.items():
        res[name] = score_arm(name, ans, rows, claims, strict_scope=False)
        strict[name] = score_arm(name, ans, rows, claims, strict_scope=True)

    per_claim = []
    for r in rows:
        line = {"id": r["id"], "値": r["値"], "正解の状態": r["第 1 段"],
                "正解集合か": bool(r["正解"]),
                "別枠の理由": r.get("別枠の理由")}
        for name in arms:
            row = [x for x in res[name]["rows"] if x["id"] == r["id"]][0]
            line[name] = {"答え": row["方式の答え"], "判定": row["判定"],
                          "根拠の再現": row.get("根拠の再現"),
                          "保留の字": row.get("保留の字")}
        per_claim.append(line)

    rec = {"seal": SEAL, "step": "封 §9 の 3。**費用 0 USD。どちらも凍結済み**",
           "gold": "fixtures/sheet/poc_gold_2026-10-17.json",
           "正解集合": gold["正解集合"]["件数"],
           "別枠": gold["別枠"]["件数"],
           "別枠の理由ごと": gold["別枠"]["理由ごと"],
           "主採点(寛容な会計)": {k: {m: v[m] for m in
                              ("M-1 誤接続率", "M-2 回収率", "M-3 根拠の再現性",
                               "正解集合", "別枠", "M-3")}
                           for k, v in res.items()},
           "**厳格な会計(印字のみ)。埋もれさせない**": {
               k: {m: v[m] for m in ("M-1 誤接続率", "M-2 回収率", "正解集合")}
               for k, v in strict.items()},
           "**2 席の一致は証拠に数えない**": ("A1 と A2 を別々に採点した"
                                 "(CLAUDE.md 8(2))。**一致率は書かない**"),
           "M-3 の注": ("**pointer の有無を分母にしていない。**"
                     "6 欄 → 原資料のセルの引き当ては `resolve()` 1 つで、"
                     "**A にも B にも同じものを当てた**(封 §4-1)。"
                     "索引は **canonicalize を通していない**(別名表を使わない)"),
           "件ごとの記録(35 件すべて)": per_claim,
           "arms": res}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=== PoC 第 1 便 A / B の採点(封 §4)===")
    print("正解集合 %d 件 / 別枠 %d 件(正解不明)" % (rec["正解集合"], rec["別枠"]))
    print("%-22s %-12s %-12s %-14s %s" % ("方式", "M-2 回収率", "M-1 誤接続率",
                                          "M-3 再現性", "別枠での挙動"))
    for name, v in res.items():
        m1, m2, m3 = v["M-1 誤接続率"], v["M-2 回収率"], v["M-3 根拠の再現性"]
        print("%-22s %5.1f%% (%2d/%2d) %5.1f%% (%2d/%2d) %5.1f%% (%2d/%2d)  "
              "推測 %d / 保留 %d"
              % (name, 100 * (m2["rate"] or 0), m2["num"], m2["den"],
                 100 * (m1["rate"] or 0), m1["num"], m1["den"],
                 100 * (m3["rate"] or 0) if m3["rate"] is not None else 0,
                 m3["num"], m3["den"],
                 v["別枠"]["推測して答えた"], v["別枠"]["保留した"]))
    print("--- 厳格な会計(印字のみ)---")
    for name, v in strict.items():
        print("%-22s 回収 %2d / 誤接続 %2d"
              % (name, v["M-2 回収率"]["num"], v["M-1 誤接続率"]["num"]))
    print("--- 正解集合の中の内訳 ---")
    for name, v in res.items():
        print("%-22s %s" % (name, json.dumps(v["正解集合"], ensure_ascii=False)))
    print("--- M-3 で到達できなかった理由 ---")
    for name, v in res.items():
        if v["M-3"]["到達できない理由"]:
            print("%-22s %s" % (name, json.dumps(v["M-3"]["到達できない理由"],
                                                 ensure_ascii=False)))
    print("->", OUT)


if __name__ == "__main__":
    main()
