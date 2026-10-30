# -*- coding: utf-8 -*-
"""見積もりの内訳(人間の問い 2026-10-17: **どのモデルを何回・入出力トークン・課金対象**)。

**0 USD。席を呼ばない。生成しない。**下見の記録と過去の実測だけを読む。

答えるのは 4 つ。

  1. **何回呼ぶか**(封の設計)
  2. **1 便のトークンを「席の往復」と「材料」に分ける** ―
     過去 2 点(11,151 字 → 101,111 / 20,300 字 → 103,778)の差から傾きを出す。
     **2 点では傾きは決まらない。だから帯で出し、別の見方(字種)で検算する**
  3. **材料のどの部分が大きいか**(本文 / refs / 問い / 回答の雛形。字種の内訳つき)
  4. **削って効くのはどれか** ― 呼ぶ回数を減らす / refs を縮める を**数で比べる**

**入出力の単価の内訳は私の記録に無い**(過去の記録は合計トークンだけ)。
だから **(a) 全部を出力として数える上限**(repo の既定)と
**(b) 入力が出力の 1/5 だと仮定した場合**の 2 通りを並べ、(b) は**仮定と明記する**。

    python3 measure/xbrl_cd_cost_breakdown_2026-10-17.py
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
DRY = os.path.join(FX, "dryrun_2026-10-17.json")
OUT = os.path.join(FX, "cost_breakdown_2026-10-17.json")
SEAL = "docs/XBRL_CD_SEAL_2026-10-17.md"
STRUCT_KEY = "構造(**使用済みの書類で測った。新しい 8 件は開いていない**)"
USD_OUT = 15.0            # sonnet の出力 USD/1M(repo の既定)
IN_RATIO = 0.2            # **仮定**: 入力は出力の 1/5(私の記録に単価は無い)
GUIDE = 3.0
Q_CHARS = 1800            # 問いと回答の形(下見と同じ数)
ROWS = 24                 # 注入 8 + 無改変 16
ROW_CHARS = 120


def ascii_share(s):
    a = sum(1 for ch in s if ord(ch) < 128)
    return a, len(s) - a


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    dry = json.load(io.open(DRY, encoding="utf-8"))
    per = dry[STRUCT_KEY]["書類ごと"]
    past = {r["席"]: r for r in dry["費用の実測見積もり"]["過去の席の実測(記録から読んだ)"]}
    s1, s2 = past["errdet seat1 sonnet"], past["poc_c seat1 sonnet"]
    dchars = s2["材料の字数"] - s1["材料の字数"]
    dtok = s2["トークン(実測)"] - s1["トークン(実測)"]
    slope = float(dtok) / dchars                      # 材料 1 字あたりのトークン
    loop = s1["トークン(実測)"] - slope * s1["材料の字数"]   # 席の往復(材料に依らない分)

    text_avg = sum(p["本文の字数"] for p in per) / float(len(per))
    refs_avg = sum(p["refs を 1 行にした字数"] for p in per) / float(len(per))
    mat = Q_CHARS + text_avg + refs_avg + ROWS * ROW_CHARS
    parts = [("問い・回答の形", Q_CHARS), ("本文(MD&A)", text_avg),
             ("**refs(fact の一覧)**", refs_avg), ("回答する行の雛形", ROWS * ROW_CHARS)]
    breakdown = [{"部分": n, "字数": int(c), "材料に占める割合": round(100.0 * c / mat, 1),
                  "この部分のトークン(傾き %.2f)" % slope: int(slope * c),
                  "1 便のトークンに占める割合": round(100.0 * slope * c / (loop + slope * mat), 1)}
                 for n, c in parts]

    # 字種での検算(refs はほぼ ASCII・本文は日本語)
    sample = per[0]["docID"]
    tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), "cd8_dryrun")
    kinds = {}
    for name, path in (("本文", os.path.join(tmp, sample + ".original.txt")),
                       ("refs", os.path.join(tmp, sample + ".reference_numbers.json"))):
        if os.path.exists(path):
            a, j = ascii_share(io.open(path, encoding="utf-8").read())
            kinds[name] = {"ASCII": a, "非 ASCII": j,
                           "ASCII の割合": round(100.0 * a / (a + j), 1)}
    cross = None
    if "本文" in kinds and "refs" in kinds:
        # ASCII は 4 字 ≒ 1 トークン、日本語は 1 字 ≒ 1 トークンの素朴な見方
        t_tok = kinds["本文"]["ASCII"] / 4.0 + kinds["本文"]["非 ASCII"]
        r_tok = kinds["refs"]["ASCII"] / 4.0 + kinds["refs"]["非 ASCII"]
        cross = {"参考にした書類": sample, "本文のトークン(素朴)": int(t_tok),
                 "refs のトークン(素朴)": int(r_tok),
                 "材料のトークン(素朴)": int(t_tok + r_tok),
                 "傾きから出した材料のトークン": int(slope * mat),
                 "note": ("**2 つの見方が同じ桁なら、材料の項の桁は確かめられた**と言える。"
                          "**席の往復の項は検算していない**")}

    per_call = loop + slope * mat
    calls = 8
    plans = []
    for name, n_calls, m in (("封のまま(8 書類 × 1 便)", 8, mat),
                             ("書類を 2 件に減らす", 2, mat),
                             ("refs を半分に縮める(8 便)", 8, mat - refs_avg / 2),
                             ("refs を半分 + 2 便", 2, mat - refs_avg / 2),
                             ("4 書類を 1 便に束ねる(2 便)", 2, Q_CHARS + 4 * (text_avg + refs_avg) + 4 * ROWS * ROW_CHARS)):
        tok = n_calls * (loop + slope * m)
        plans.append({"案": name, "便の数": n_calls, "1 便の材料の字数": int(m),
                      "合計トークン": int(tok),
                      "上限 USD(全部を出力として)": round(tok * USD_OUT / 1e6, 2),
                      "USD(入力が出力の 1/5 **仮定**)": round(tok * USD_OUT * IN_RATIO / 1e6, 2),
                      "目安 3 USD の中(上限の数え方)": tok * USD_OUT / 1e6 <= GUIDE})

    rec = {"seal": SEAL, "step": "**見積もりの内訳。0 USD・生成なし・席を呼ばない**",
           "1 何回呼ぶか": {"model": "sonnet(封 §4 のとおり 1 席)",
                      "便の数": calls, "割り当て": "1 書類 1 便",
                      "再試行": "見込まない(見込むなら別に足す)",
                      "note": "**2 席にしない**(軸3 の正解は構成上決まるので席の一致を使わない)"},
           "2 1 便のトークンの分け方": {
               "過去の 2 点": [s1, s2],
               "材料 1 字あたりのトークン(傾き)": round(slope, 3),
               "**席の往復(材料に依らない分)**": int(loop),
               "1 便の材料の字数": int(mat), "1 便の材料のトークン": int(slope * mat),
               "1 便の合計トークン": int(per_call),
               "**材料が占める割合**": round(100.0 * slope * mat / per_call, 1),
               "**席の往復が占める割合**": round(100.0 * loop / per_call, 1),
               "limits": ("**2 点から出した傾きである。**材料をほぼ 2 倍にしても"
                          "トークンは %d → %d しか増えていない(+%d 字で +%d トークン)"
                          % (s1["トークン(実測)"], s2["トークン(実測)"], dchars, dtok))},
           "3 材料のどこが大きいか": {"部分ごと": breakdown, "字種": kinds, "検算": cross},
           "4 削って効くのはどれか": plans,
           "**入出力の単価の内訳**": {
               "私の記録に在るか": False,
               "記録に在るのは": "合計トークンだけ(過去の席の記録 4 本すべて)",
               "既定の数え方": "**全部を出力として数える上限**(sonnet 15 USD/1M)",
               "仮定の数え方": "入力が出力の 1/5(**仮定であり実測ではない**)",
               "確かめ方": "単価と入出力の内訳は人間が課金の記録で確かめる必要が在る"},
           "limits": [
               "**材料の構造は使用済みの書類で測った。**新しい 8 件は違いうる",
               "**席の往復の項は検算していない。**別の harness なら変わる",
               "**入出力別の実測は 1 件も無い。**内訳は仮定を含む",
               "**費用を下げる案の効き目は見積もりである。**実測は生成してからしか出ない"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== 見積もりの内訳(0 USD)===")
    print("傾き %.3f トークン/字 / **席の往復 %d トークン**(材料に依らない)"
          % (slope, loop))
    print("1 便: 材料 %d 字 -> %d トークン + 往復 %d = **%d トークン**"
          % (mat, slope * mat, loop, per_call))
    print("   **材料 %.1f%% / 往復 %.1f%%**"
          % (100.0 * slope * mat / per_call, 100.0 * loop / per_call))
    print("--- 材料の内訳 ---")
    for b in breakdown:
        k = [x for x in b if x.startswith("この部分のトークン")][0]
        print("  %-22s %6d 字(材料の %4.1f%%)-> %6d トークン(1 便の %4.1f%%)"
              % (b["部分"], b["字数"], b["材料に占める割合"], b[k],
                 b["1 便のトークンに占める割合"]))
    if cross:
        print("  字種での検算: 材料 %d トークン(素朴)対 %d トークン(傾き)"
              % (cross["材料のトークン(素朴)"], cross["傾きから出した材料のトークン"]))
    print("--- 削って効くのはどれか ---")
    for p in plans:
        print("  %-28s %d 便 -> %7d トークン / 上限 %5.2f USD / 仮定 %4.2f USD %s"
              % (p["案"], p["便の数"], p["合計トークン"],
                 p["上限 USD(全部を出力として)"], p["USD(入力が出力の 1/5 **仮定**)"],
                 "**目安の中**" if p["目安 3 USD の中(上限の数え方)"] else ""))
    print("->", OUT)


if __name__ == "__main__":
    main()
