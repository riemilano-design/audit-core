# -*- coding: utf-8 -*-
"""① の続き ― **記録に 1 件だけ在った入出力の内訳から単価の形を解く。0 USD。**

`fixtures/xbrl/ai_prose_generation_meta_2026-10-09.json` に
**入力 22,490 / 出力 6,000 / 実費 0.26245 USD / prompt 35,428 字** が残っていた
(model `claude-opus-5`・2026-10-09・calls 1・retries 0)。

ここから機械で出せるのは 3 つ。

  1. **1 字あたりの入力トークン**(prompt の字数と入力トークンの比)
  2. **入出力の単価の組**(候補の組を当てて、実費がぴったり再現するものを探す)
  3. その単価の形を使った **8 便 1 席の見積もり**

**これは 1 件の記録である。**モデルも違う(opus)。**sonnet の単価は確かめていない。**
**実請求額の確認は人間が課金の画面でやる必要が在る**(私から見えない)。

    python3 measure/xbrl_cost_split_2026-10-17.py
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
META = os.path.join(ROOT, "fixtures", "xbrl",
                    "ai_prose_generation_meta_2026-10-09.json")
DRY = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "dryrun_2026-10-17.json")
BRK = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "cost_breakdown_2026-10-17.json")
OUT = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "cost_split_2026-10-17.json")
# 当てる単価の候補(USD/1M)。**結果を見てから足さない**
RATES = [1, 1.25, 3, 5, 8, 10, 15, 25, 30, 75]
GUIDE = 3.0


def solve(inp, out, usd):
    """**実費をぴったり再現する (入力, 出力) の単価の組を全部返す。**"""
    hits = []
    for i in RATES:
        for o in RATES:
            if abs((inp * i + out * o) / 1e6 - usd) < 5e-7:
                hits.append({"入力 USD/1M": i, "出力 USD/1M": o,
                             "出力は入力の何倍": round(float(o) / i, 2)})
    return hits


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    m = json.load(io.open(META, encoding="utf-8"))
    inp, out, usd = m["input_tokens"], m["output_tokens"], m["cost_usd"]
    per_char = round(float(inp) / m["prompt_chars"], 4)
    hits = solve(inp, out, usd)
    brk = json.load(io.open(BRK, encoding="utf-8"))
    mat_chars = brk["2 1 便のトークンの分け方"]["1 便の材料の字数"]
    loop_tok = brk["2 1 便のトークンの分け方"]["**席の往復(材料に依らない分)**"]
    per_call_total = brk["2 1 便のトークンの分け方"]["1 便の合計トークン"]
    # 見積もりの 2 通り。**どちらも仮定を字で書く**
    in_tok = int(mat_chars * per_char)
    scen = []
    for name, i_tok, o_tok, note in (
            ("A 材料だけを入力・出力は上限 6,000", in_tok, 6000,
             "**席の往復を数えない**(1 回の API 呼び出しだと仮定)"),
            ("B 1 便の合計トークンを 入力:出力 = 9:1 で割る",
             int(per_call_total * 0.9), int(per_call_total * 0.1),
             "**席の往復を入力として数える**(subagent の往復が在ると仮定)"),
            ("C 1 便の合計トークンを全部出力(repo の既定の上限)",
             0, per_call_total, "**上限。実費より必ず大きい**")):
        for rate in ({"in": 3.0, "out": 15.0, "名": "sonnet(出力 15 と仮定・入力は 1/5)"},):
            usd1 = (i_tok * rate["in"] + o_tok * rate["out"]) / 1e6
            scen.append({"場合": name, "注": note, "単価": rate["名"],
                         "入力トークン": i_tok, "出力トークン": o_tok,
                         "1 便 USD": round(usd1, 3),
                         "8 便 USD": round(8 * usd1, 2),
                         "目安 3 USD の中": 8 * usd1 <= GUIDE})
    rec = {"step": "**① の続き。記録 1 件から単価の形を解いた。0 USD**",
           "**使った記録**": {"file": os.path.relpath(META, ROOT),
                        "model": m["model"], "calls": m["calls"],
                        "retries": m["retries"],
                        "prompt_chars": m["prompt_chars"],
                        "input_tokens": inp, "output_tokens": out,
                        "cost_usd": usd, "stop_reason": m.get("stop_reason")},
           "1 1 字あたりの入力トークン(実測)": per_char,
           "2 実費を再現する単価の組": {
               "候補": hits,
               "**解は 1 つか**": len(hits) == 1,
               "note": ("**候補の表に無い単価なら解けない。**"
                        "解が 1 つなら、その組で実費がぴったり再現する")},
           "3 8 便 1 席の見積もり(**sonnet の単価は確かめていない**)": scen,
           "**確定していないこと**": [
               "**これは 1 件の記録で、モデルは opus である。**sonnet の単価は未確認",
               "**席の往復(subagent)の入出力の割れ方は記録に無い**(場合 B は仮定)",
               "**実請求額は私から見えない。**人間が課金の画面で確かめる必要が在る",
               "**推定を実測として扱わない**(人間の指示 2026-10-17)"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== ① 記録 1 件から解いた単価の形(0 USD)===")
    print("記録: %s / model %s / 入力 %d / 出力 %d / 実費 %.5f USD"
          % (os.path.basename(META), m["model"], inp, out, usd))
    print("**1 字あたりの入力トークン: %.4f**(prompt %d 字)"
          % (per_char, m["prompt_chars"]))
    print("**実費を再現する単価の組: %s**" % json.dumps(hits, ensure_ascii=False))
    for s in scen:
        print("  %-42s 入 %7d / 出 %7d -> 1 便 %6.3f / 8 便 %6.2f USD %s"
              % (s["場合"], s["入力トークン"], s["出力トークン"],
                 s["1 便 USD"], s["8 便 USD"],
                 "**目安の中**" if s["目安 3 USD の中"] else ""))
    print("->", OUT)


if __name__ == "__main__":
    main()
