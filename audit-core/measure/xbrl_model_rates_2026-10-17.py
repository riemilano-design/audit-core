# -*- coding: utf-8 -*-
"""① の続き ― **使ったモデル ID を記録から数え、単価の候補ごとに見積もりを作る。0 USD。**

人間の訂正(2026-10-17):
> **「Sonnet だから入力 5 ドル・出力 25 ドル」とは判断できません。**
> その単価は今回の Sonnet の実請求額から確定したものではなく、
> **別の Opus 記録から再現された候補**です。
> **Sonnet の単価はモデルのバージョンによって異なります。**
> そのため、**今回の実験で使ったモデル ID を特定することが先**です。

**受ける。**だからこの便でやるのは 3 つ。

  1. **記録に在るモデル ID を全部数える**(私が名乗っただけの字も分けて数える)
  2. **単価の候補 × 入出力の割れ方**で見積もりの表を作る(**どれも仮定と明記**)
  3. **人間が Console で照合するための記録**(鍵を含まない)を csv に出す

**実請求額・適用単価・キャッシュ・API 呼び出し回数は私から見えない。**

    python3 measure/xbrl_model_rates_2026-10-17.py
"""
import collections
import csv
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
BRK = os.path.join(FX, "cost_breakdown_2026-10-17.json")
SPLIT = os.path.join(FX, "cost_split_2026-10-17.json")
OUT = os.path.join(FX, "model_rates_2026-10-17.json")
CSV_OUT = os.path.join(FX, "seat_runs_for_console_2026-10-17.csv")

# 人間が公開料金表で確かめた組(2026-10-17)。**私が確かめたのではない**
PUBLISHED = [("Claude Sonnet 5", 2.0, 10.0, "人間が公開料金表で確認(2026-10-17)"),
             ("Claude Sonnet 4.6", 3.0, 15.0, "同上")]
# 私が記録 1 本から解いた組(**opus の記録。sonnet には使えない**)
SOLVED = [("opus の記録から解いた組", 5.0, 25.0,
           "`ai_prose_generation_meta_2026-10-09`(model claude-opus-5)の実費を再現")]
OUT_SHARES = (0.1, 0.5, 1.0)       # 出力の割合の仮定
GUIDE = 3.0
CALLS = 8
KEYISH = re.compile(r"[A-Za-z0-9_\-]{32,}")


def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k, v
            for r in walk(v):
                yield r
    elif isinstance(o, list):
        for v in o:
            for r in walk(v):
                yield r


def model_ids():
    """記録に在るモデルの字を数える。**私が名乗った字と、harness が書いた字を分ける。**"""
    counts, where = collections.Counter(), collections.defaultdict(list)
    for base, _, names in os.walk(os.path.join(ROOT, "fixtures")):
        for n in names:
            if not n.endswith(".json"):
                continue
            p = os.path.join(base, n)
            try:
                j = json.load(io.open(p, encoding="utf-8"))
            except ValueError:
                continue
            for k, v in walk(j):
                if k in ("model", "model_id") and isinstance(v, str):
                    counts[v] += 1
                    where[v].append(os.path.relpath(p, ROOT))
    rows = []
    for m, c in counts.most_common():
        looks_like_id = bool(re.match(r"^claude-[a-z0-9\-]+$", m))
        rows.append({"字": m, "件数": c, "**モデル ID の形か**": looks_like_id,
                     "例": where[m][:2]})
    return rows


def seat_runs():
    """席を呼んだ記録(合計トークンが在るもの)。**鍵を含む欄は出さない。**"""
    rows = []
    for base, _, names in os.walk(os.path.join(ROOT, "fixtures")):
        for n in sorted(names):
            if not n.endswith(".json"):
                continue
            p = os.path.join(base, n)
            try:
                j = json.load(io.open(p, encoding="utf-8"))
            except ValueError:
                continue
            tok, model, when = None, None, None
            for k, v in walk(j):
                if k == "使ったトークン(実測)" and isinstance(v, int):
                    tok = v
                if k in ("model", "model_id") and isinstance(v, str) and not model:
                    model = v
                if k in ("answered_at", "generated_at", "when") and isinstance(v, str):
                    when = v
            if tok:
                rows.append({"file": os.path.relpath(p, ROOT), "model": model or "",
                             "合計トークン(実測)": tok, "時刻": when or ""})
    return rows


def estimate(total_per_call, in_only, out_only):
    """単価の組ごとの見積もり。**入出力の割れ方は仮定として表に出す。**"""
    out = []
    for name, i, o, src in PUBLISHED + SOLVED:
        for share in OUT_SHARES:
            tok_out = total_per_call * share
            tok_in = total_per_call - tok_out
            usd = (tok_in * i + tok_out * o) / 1e6
            out.append({"単価の組": name, "入力 USD/1M": i, "出力 USD/1M": o,
                        "出どころ": src, "出力の割合(仮定)": share,
                        "1 便 USD": round(usd, 3),
                        "%d 便 USD" % CALLS: round(CALLS * usd, 2),
                        "目安 %.0f USD の中" % GUIDE: CALLS * usd <= GUIDE})
        usd2 = (in_only * i + out_only * o) / 1e6
        out.append({"単価の組": name, "入力 USD/1M": i, "出力 USD/1M": o,
                    "出どころ": src,
                    "出力の割合(仮定)": "材料だけ入力 + 出力 %d" % out_only,
                    "1 便 USD": round(usd2, 3),
                    "%d 便 USD" % CALLS: round(CALLS * usd2, 2),
                    "目安 %.0f USD の中" % GUIDE: CALLS * usd2 <= GUIDE})
    return out


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    brk = json.load(io.open(BRK, encoding="utf-8"))["2 1 便のトークンの分け方"]
    sp = json.load(io.open(SPLIT, encoding="utf-8"))
    per_call = brk["1 便の合計トークン"]
    mat_chars = brk["1 便の材料の字数"]
    per_char = sp["1 1 字あたりの入力トークン(実測)"]
    in_only = int(mat_chars * per_char)
    ids = model_ids()
    runs = seat_runs()
    est = estimate(per_call, in_only, 6000)
    with io.open(CSV_OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "model(記録のまま)", "合計トークン(実測)", "時刻"])
        for r in runs:
            w.writerow([r["file"], r["model"], r["合計トークン(実測)"], r["時刻"]])
    # **鍵の走査は「中身の欄」だけに当てる。**file 名に当てると日付つきの長い名前が
    # 当たって止まる(最初にそう書いて止まった)
    blob = " ".join([r["model"] for r in runs] + [r["時刻"] for r in runs]
                    + [r["字"] for r in ids])
    leaks = [s for s in KEYISH.findall(blob) if not re.fullmatch(r"[0-9a-f]{32,}", s)]
    if leaks:
        raise SystemExit("**鍵らしい字が出力に在る。止める: %s**" % leaks[:2])
    rec = {"step": "**① の続き。モデル ID と単価の候補。0 USD・通信なし**",
           "**人間の訂正を受ける**": (
               "**opus の記録から解いた 5 / 25 は sonnet の単価ではない。**"
               "**Sonnet の単価はバージョンで違う**ので、"
               "**使ったモデル ID を特定するのが先**(人間の指摘 2026-10-17)"),
           "1 記録に在るモデルの字": ids,
           "**席を呼んだときの実際の経路**": (
               "記録の字は `claude-sonnet-4-5(Agent, subagent_type=general-purpose, "
               "model=sonnet)` のような形 ― **API を直接叩いたのではなく "
               "Agent(subagent)の harness を通している。**"
               "**だから 1 便が API 何回に化けたかは私の記録に無い。**"),
           "2 単価の候補 × 入出力の割れ方": est,
           "3 Console 照合用の記録": {"csv": os.path.relpath(CSV_OUT, ROOT),
                             "件数": len(runs),
                             "欄": ["file", "model(記録のまま)",
                                   "合計トークン(実測)", "時刻"],
                             "**鍵は含まない**": True,
                             "note": "**入出力の内訳は記録に無いので csv にも無い**"},
           "**確定していないこと**": [
               "**実験で使うモデル ID を封に字で固定していない**(本番の封は「sonnet 1 席」)",
               "**`claude-sonnet-4-5` は人間が挙げた表(Sonnet 5 / Sonnet 4.6)に無い**",
               "**席 1 便の API 呼び出し回数**(harness の中は記録に無い)",
               "**キャッシュの課金**",
               "**実請求額**(Console の Cost。私から見えない)"],
           "limits": ["**どの行も仮定を含む。実測は実請求額だけが決める**",
                      "**公開料金表は人間が確かめたものを写した。私は確かめていない**"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== ① モデル ID と単価の候補(0 USD)===")
    for r in ids:
        print("  %-62s %3d 件  ID の形: %s"
              % (r["字"][:62], r["件数"], r["**モデル ID の形か**"]))
    print("--- 見積もり(1 便 %d トークン / 材料だけなら入力 %d)---"
          % (per_call, in_only))
    for e in est:
        print("  %-24s 入 %4.1f / 出 %4.1f / 出力の割合 %-18s -> 8 便 %6.2f USD %s"
              % (e["単価の組"], e["入力 USD/1M"], e["出力 USD/1M"],
                 str(e["出力の割合(仮定)"]), e["8 便 USD"],
                 "**目安の中**" if e["目安 3 USD の中"] else ""))
    print("Console 照合用 csv: %s(%d 件・鍵なし)"
          % (os.path.relpath(CSV_OUT, ROOT), len(runs)))
    print("->", OUT)


if __name__ == "__main__":
    main()
