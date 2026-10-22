# -*- coding: utf-8 -*-
"""封 v2 の採点 ― **A(席そのまま)対 C′(席 + Core)。D′・D″ は副比較。0 USD。**

spec `docs/XBRL_CD_MATERIAL_SPEC_2026-10-17.md`(§4 の腕・§7 の欠け・§8 の T5=0)。
封 `docs/XBRL_CD_SEAL_V2_2026-10-17.md`(Δ3 の 2 軸・Δ4 の 4 数・Z-1/Z-2)。

**採点の関数は (ア) の実物を使う**(書き直さない。監査の指摘 2)。
**席の答えは変換の前にそのまま commit する。**

  合成(spec §4・§7。**上書きしない**)
    A   = 席の判定と参照先をそのまま
    C′  = 席のまま。**席が `判定できない` の行だけ** Core の判定と参照先を使う
    D′  = 同じ規則で値検索を足す / D″ = 強くした値検索
    欠け(未回答・3 語の外・参照先の形が違う)= **4 腕すべて `欠け`。照合器を足さない**

    python3 measure/xbrl_cd_score_2026-10-17.py --answers <dir>
"""
import argparse
import collections
import importlib.util
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
MAT = os.path.join(FX, "material_2026-10-17.json")
OUT = os.path.join(FX, "score_2026-10-17.json")
SPEC = "docs/XBRL_CD_MATERIAL_SPEC_2026-10-17.md"
SEAL_V2 = "docs/XBRL_CD_SEAL_V2_2026-10-17.md"
WORDS = (u"確認済み", u"誤りが在る", u"判定できない")      # spec §3
PTR_RE = re.compile(r"^[A-Za-z0-9_\-]+@[A-Za-z0-9_\-]+$")
MISSING = u"欠け"

_sp = importlib.util.spec_from_file_location(
    "a_core_vs_grep", os.path.join(HERE, "xbrl_a_core_vs_grep_2026-10-17.py"))
A1 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(A1)


def seat_row(ans):
    """席の 1 行を読む。**3 語の外・参照先の形が違う・欠けは `欠け`。**"""
    if not isinstance(ans, dict):
        return {u"判定": MISSING, u"参照先": None, u"なぜ": u"行が無い"}
    v = ans.get(u"判定")
    if v not in WORDS:
        return {u"判定": MISSING, u"参照先": None, u"なぜ": u"3 語の外: %r" % (v,)}
    p = ans.get(u"参照先")
    if p in (None, "", u"なし", u"無し"):
        return {u"判定": v, u"参照先": None, u"なぜ": None}
    if not isinstance(p, str) or not PTR_RE.match(p.strip()):
        return {u"判定": MISSING, u"参照先": None,
                u"なぜ": u"参照先の形が違う: %r" % (p,)}
    return {u"判定": v, u"参照先": A1.norm_pointer(p.strip()), u"なぜ": None}


def compose(seat, checker):
    """spec §4・§7。**席を上書きしない。欠けには何も足さない。**"""
    if seat[u"判定"] == MISSING:
        return {u"判定": MISSING, u"参照先": None, u"足した": False}
    if seat[u"判定"] != u"判定できない":
        return {u"判定": seat[u"判定"], u"参照先": seat[u"参照先"], u"足した": False}
    say = checker.get(u"言うこと")
    judged = (u"確認済み" if say == u"確認済み"
              else (u"誤りが在る" if say == u"原資料と一致しない"
                    else u"判定できない"))
    return {u"判定": judged, u"参照先": checker.get(u"参照先"), u"足した": True}


def arms_of(seat, pre):
    """4 腕を同じ 1 行から作る。**C′ だけが得をする経路を作らない。**"""
    return {"A": {u"判定": seat[u"判定"], u"参照先": seat[u"参照先"], u"足した": False},
            "C′": compose(seat, pre["Core"]),
            "D′": compose(seat, pre[u"D′"]),
            "D″": compose(seat, pre[u"D″"])}


def verdict(arm, gold, injected):
    """1 行 1 腕。**分母に入るかどうかもここで決める。**"""
    out = {u"欠け": arm[u"判定"] == MISSING}
    if out[u"欠け"]:
        return out
    out[u"参照先を出した"] = arm[u"参照先"] is not None
    out[u"見逃し"] = bool(injected) and arm[u"判定"] == u"確認済み"
    out[u"止めた"] = bool(injected) and arm[u"判定"] != u"確認済み"
    out[u"保留"] = arm[u"参照先"] is None
    out[u"偽警報"] = (not injected) and arm[u"判定"] == u"誤りが在る"
    out[u"特定"] = None
    out[u"誤認定"] = False
    if gold is None:
        return out
    if gold[u"種類"] == u"参照先が在る":
        out[u"特定"] = (arm[u"参照先"] == gold[u"正解"])
        if arm[u"参照先"] is not None and not out[u"特定"]:
            out[u"誤認定"] = True
            out[u"値の持ち主だった"] = (arm[u"参照先"] == gold[u"偶然一致する側"])
    elif gold[u"種類"] == u"参照先は無い":
        out[u"誤認定"] = arm[u"参照先"] is not None
    else:
        out[u"誤認定"] = arm[u"判定"] == u"確認済み"
    return out


def tally(rows):
    """封 v2 Δ4 の 4 数 + 軸A・軸B。**分母を全部書く。**"""
    out = {}
    for arm in ("A", "C′", "D′", "D″"):
        live = [r for r in rows if not r[u"腕"][arm][u"判定結果"][u"欠け"]]
        inj = [r for r in live if r[u"注入か"]]
        t5 = [r for r in live if (r[u"正解"] or {}).get(u"種類") == u"参照先が在る"]
        pointed = [r for r in live if r[u"腕"][arm][u"判定結果"][u"参照先を出した"]]
        ident = [r for r in t5 if r[u"腕"][arm][u"判定結果"][u"特定"]]
        wrong = [r for r in pointed if r[u"腕"][arm][u"判定結果"][u"誤認定"]]
        miss = [r for r in inj if r[u"腕"][arm][u"判定結果"][u"見逃し"]]
        held = [r for r in live if r[u"腕"][arm][u"判定結果"][u"保留"]]
        plain = [r for r in live if not r[u"注入か"]]
        false_alarm = [r for r in plain if r[u"腕"][arm][u"判定結果"][u"偽警報"]]
        stopped = [r for r in inj if r[u"腕"][arm][u"判定結果"][u"止めた"]]
        cross = collections.Counter()
        for r in t5:
            v = r[u"腕"][arm][u"判定結果"]
            cross[u"%s × %s" % (u"止めた" if v[u"止めた"] else u"通した",
                                u"一致" if v[u"特定"] else
                                (u"違う" if v[u"参照先を出した"] else u"名指さない"))] += 1
        out[arm] = {
            u"誤認定": {u"分子": len(wrong), u"分母(参照先を出した件)": len(pointed),
                     u"率": pct(len(wrong), len(pointed))},
            u"見逃し": {u"分子": len(miss), u"分母(注入の件)": len(inj),
                     u"率": pct(len(miss), len(inj))},
            u"正しい参照先の特定": {u"分子": len(ident), u"分母(T5 の件)": len(t5),
                          u"率": pct(len(ident), len(t5)),
                          u"名指した件での率": pct(len(ident), len(pointed))},
            u"保留": {u"分子": len(held), u"分母(欠けを外した件)": len(live),
                    u"率": pct(len(held), len(live))},
            u"軸A 停止判定": {u"分子": len(stopped), u"分母(注入の件)": len(inj),
                         u"率": pct(len(stopped), len(inj))},
            u"偽警報(**判定には使わない**)": {u"分子": len(false_alarm),
                                  u"分母(無改変の件)": len(plain),
                                  u"率": pct(len(false_alarm), len(plain))},
            u"軸A × 軸B(T5)": dict(cross),
            u"値の持ち主を採った件": sum(
                1 for r in rows
                if r[u"腕"][arm][u"判定結果"].get(u"値の持ち主だった")),
            u"照合器を足した行": sum(1 for r in rows if r[u"腕"][arm].get(u"足した")),
            u"欠け": sum(1 for r in rows if r[u"腕"][arm][u"判定結果"][u"欠け"])}
    return out


def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def judge_z(t):
    """封 v2 §2。**両方満たしたときだけ「上回った」と書く。**"""
    a, c = t["A"], t["C′"]
    z1 = c[u"誤認定"][u"分子"] < a[u"誤認定"][u"分子"]
    z2 = (c[u"正しい参照先の特定"][u"分子"] > a[u"正しい参照先の特定"][u"分子"])
    if z1 and z2:
        v = u"**LLM + Core は LLM 単体を上回った**(Z-1・Z-2 の両方)"
    elif z1 or z2:
        v = u"**片方だけ**(Z-1 %s / Z-2 %s)" % (z1, z2)
    else:
        v = u"**この標本では支持されない**(Z-1・Z-2 ともに外れ)"
    return {u"Z-1 誤認定が減った": z1, u"Z-2 正しい特定が増えた": z2, u"判定": v}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", required=True, help="席の答えの json が在る dir")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit("既に在る: %s(採り直さない)" % a.out)
    mat = json.load(io.open(MAT, encoding="utf-8"))
    rows, per_doc = [], {}
    for p in mat[u"書類ごと"]:
        doc = p["docID"]
        path = os.path.join(a.answers, "%s_answer.json" % doc)
        if not os.path.exists(path):
            per_doc[doc] = {u"**答えが無い**": path}
            continue
        ans = json.load(io.open(path, encoding="utf-8"))
        by_id = {}
        for r in (ans if isinstance(ans, list) else ans.get(u"answers", [])):
            if isinstance(r, dict) and r.get("id"):
                by_id[str(r["id"]).strip()] = r
        n_rows = 0
        for rid, pre in sorted(p[u"席の前に出せる分"].items()):
            seat = seat_row(by_id.get(rid))
            arms = arms_of(seat, pre)
            gold = pre[u"正解"]
            injected = pre[u"注入か"]
            row = {u"doc": doc, u"id": rid, u"注入か": injected, u"正解": gold,
                   u"席": seat, u"腕": {}}
            for name, arm in arms.items():
                row[u"腕"][name] = dict(arm)
                row[u"腕"][name][u"判定結果"] = verdict(arm, gold, injected)
            rows.append(row)
            n_rows += 1
        per_doc[doc] = {u"行": n_rows, u"答えた行": len(by_id),
                        u"欠け": sum(1 for r in rows if r[u"doc"] == doc
                                   and r[u"腕"]["A"][u"判定結果"][u"欠け"])}
    t = tally(rows)
    gaps = {arm: t[arm][u"欠け"] for arm in t}
    if len(set(gaps.values())) > 1:
        raise SystemExit(u"**欠けが腕で違う: %s。止める**" % gaps)
    rec = {"spec": SPEC, "seal": SEAL_V2,
           "step": u"**封 v2 の採点。A 対 C′ が主比較**",
           u"採点の関数": u"**(ア) の実物を import して使った**",
           u"合成の規則": u"**席を上書きしない。席が `判定できない` の行だけ照合器を足す**",
           u"欠けの扱い": u"**4 腕すべて `欠け`。照合器を足さない**(spec §7)",
           u"書類ごと": per_doc, u"行の合計": len(rows),
           u"**欠けは 4 腕で同数**": gaps,
           u"採点": t, u"**主比較の判定**": judge_z(t),
           "limits": [
               u"**人工の誤りである。**実際の書類で起きる誤りではない",
               u"**誤りを示唆する問いの下での検出である**",
               u"**`S100YXF5` は T5 が 0 件なので軸B の分母に入らない**(spec §8)",
               u"**偽警報と種類は記録に残すが主比較の判定に使わない**(封 v2 Δ4)"],
           "rows": rows}
    json.dump(rec, io.open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(u"=== 封 v2 採点: 行 %d(欠け %s)===" % (len(rows), gaps))
    for arm in ("A", "C′", "D′", "D″"):
        v = t[arm]
        print(u"  %-3s 誤認定 %5s%% (%2d/%2d) / 見逃し %5s%% (%2d/%2d) / "
              u"特定 %5s%% (%2d/%2d) / 保留 %5s%% / 偽警報 %5s%% / 足した %d"
              % (arm, v[u"誤認定"][u"率"], v[u"誤認定"][u"分子"],
                 v[u"誤認定"][u"分母(参照先を出した件)"],
                 v[u"見逃し"][u"率"], v[u"見逃し"][u"分子"], v[u"見逃し"][u"分母(注入の件)"],
                 v[u"正しい参照先の特定"][u"率"], v[u"正しい参照先の特定"][u"分子"],
                 v[u"正しい参照先の特定"][u"分母(T5 の件)"],
                 v[u"保留"][u"率"], v[u"偽警報(**判定には使わない**)"][u"率"],
                 v[u"照合器を足した行"]))
    print(u"**%s**" % rec[u"**主比較の判定**"][u"判定"])
    print("->", a.out)


if __name__ == "__main__":
    main()
