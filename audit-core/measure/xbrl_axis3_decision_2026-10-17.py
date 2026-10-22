# -*- coding: utf-8 -*-
"""② **本番の軸3 の定義を決めるための採点のやり直し**(人間の指示 2026-10-17)。

> 私の推奨は、「**停止していても pointer を読む**」側を採用することです。ただし、
> **停止状態で参照先を出せば正解とみなすのではなく、参照先の正しさを独立に採点します。
> 停止判定と参照先の特定は別々の評価軸にします。**

**(ア) の記録を読み直すだけ。engine も判定ロジックも 1 行も触らない。0 USD。**
**これは評価指標の作り直しであって、判定ロジックの修正ではない。**

  軸A **停止判定**: 誤りを入れた行で「確認済み」と言わなかったか(= 止めたか)
  軸B **参照先**:   名指した参照先が正解と一致するか(**状態に関わらず読む**)

**2 つを掛け合わせた表も出す** ― 「止めたが参照先は誤り」を隠さないため。
**対応が付かない行は分母から外し、件数を別に書く。**

    python3 measure/xbrl_axis3_decision_2026-10-17.py
"""
import collections
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
SRC = os.path.join(FX, "a_core_vs_grep_2026-10-17.json")
OUT = os.path.join(FX, "axis3_decision_2026-10-17.json")
ARMS = ("Core-P", "D′", "D″")        # **Core は 1 つ。読み方を pointer 側に決めた**


def stopped(say):
    """**軸A**: 「確認済み」でなければ止めた。**対応が付かない行は None。**"""
    if say["言うこと"] == "対応が付かない":
        return None
    return say["言うこと"] != "確認済み"


def pointer_verdict(row, arm):
    """**軸B**: 名指したか / 正解と一致するか。**状態は見ない。**"""
    say = row["腕"][arm]
    p = say["参照先"]
    if p is None:
        return "名指さない"
    if row["正解"]["種類"] != "参照先が在る":
        return "名指した(正解が無い場面)"
    return "正解と一致" if p == row["正解"]["正解"] else "正解と違う"


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    src = json.load(io.open(SRC, encoding="utf-8"))
    rows = src["rows"]
    out = {}
    for arm in ARMS:
        a_den = [r for r in rows if stopped(r["腕"][arm]) is not None]
        a_ok = [r for r in a_den if stopped(r["腕"][arm])]
        by_type = {}
        for t in ("T5_COINCIDENT", "T1_VALUE", "T3_ABSENT"):
            d = [r for r in a_den if r["型"] == t]
            by_type[t] = {"分母(対応が付いた件)": len(d),
                          "止めた": sum(1 for r in d if stopped(r["腕"][arm])),
                          "率": pct(sum(1 for r in d if stopped(r["腕"][arm])), len(d))}
        t5 = [r for r in rows if r["型"] == "T5_COINCIDENT"]
        named = [r for r in t5 if r["腕"][arm]["参照先"] is not None]
        hit = [r for r in named if pointer_verdict(r, arm) == "正解と一致"]
        miss = [r for r in named if pointer_verdict(r, arm) == "正解と違う"]
        owner = [r for r in miss
                 if r["腕"][arm]["参照先"] == r["正解"]["偶然一致する側"]]
        cross = collections.Counter()
        for r in t5:
            s = stopped(r["腕"][arm])
            cross["%s × %s" % ("止めた" if s else ("通した" if s is False else "対応が付かない"),
                               pointer_verdict(r, arm))] += 1
        out[arm] = {
            "軸A 停止判定": {"分母(対応が付いた件)": len(a_den), "止めた": len(a_ok),
                        "率": pct(len(a_ok), len(a_den)), "型ごと": by_type},
            "軸B 参照先(T5。状態に関わらず読む)": {
                "T5 の件数": len(t5), "名指した": len(named),
                "**名指した率**": pct(len(named), len(t5)),
                "正解と一致": len(hit),
                "**名指したうち正しい率**": pct(len(hit), len(named)),
                "**T5 全体での特定率**": pct(len(hit), len(t5)),
                "正解と違う": len(miss),
                "うち値の持ち主を採った": len(owner)},
            "軸A × 軸B(T5)": dict(cross)}
    unmapped = [r["id"] for r in rows if not r["対応が付いた"]]
    rec = {"step": "**② 軸3 の定義のやり直し。記録を読み直すだけ。0 USD**",
           "**読み直した記録**": os.path.relpath(SRC, ROOT),
           "**触っていないもの**": ["engine(`adapters/`・`core/`)", "判定ロジック",
                           "(ア) の記録", "席つき本番の封"],
           "決めた読み方": ("**停止していても `pointers` を読む。"
                      "ただし『止めた』ことを正解に数えない** ― "
                      "軸A(停止判定)と軸B(参照先の正しさ)を別に採る"),
           "腕": out,
           "対応が付かなかった件": {"件数": len(unmapped), "ids": unmapped,
                          "扱い": "**軸A の分母から外し、件数を別に書く**"},
           "limits": [
               "**これは評価指標の作り直しであって、判定ロジックの修正ではない**",
               "**(ア) と同じ標本である。**新しい書類は 1 件も使っていない",
               "**使用済みの 8 書類。**未使用データでの再現性は測っていない",
               "**正解そのものが誤りうる**((ア) の §3-2 の 4 番)"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== ② 軸3 の定義のやり直し(0 USD・engine は触っていない)===")
    for arm in ARMS:
        v = out[arm]
        a, b = v["軸A 停止判定"], v["軸B 参照先(T5。状態に関わらず読む)"]
        print("  %-6s 軸A 止めた %5s%% (%d/%d) | 軸B 名指し %5s%% / "
              "名指したうち正しい %5s%% / T5 全体の特定 %5s%% / 値の持ち主 %d 件"
              % (arm, a["率"], a["止めた"], a["分母(対応が付いた件)"],
                 b["**名指した率**"], b["**名指したうち正しい率**"],
                 b["**T5 全体での特定率**"], b["うち値の持ち主を採った"]))
    print("--- 軸A × 軸B(T5)---")
    for arm in ARMS:
        print("  %-6s %s" % (arm, json.dumps(out[arm]["軸A × 軸B(T5)"],
                                             ensure_ascii=False)))
    print("対応が付かなかった件: %d(軸A の分母から外した)" % len(unmapped))
    print("->", OUT)


def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


if __name__ == "__main__":
    main()
