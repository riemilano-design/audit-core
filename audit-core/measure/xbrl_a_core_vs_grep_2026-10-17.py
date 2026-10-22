# -*- coding: utf-8 -*-
"""(ア) **Core 単体 対 D′・D″**(封 docs/XBRL_A_CORE_VS_GREP_SEAL_2026-10-17.md)。

**0 USD。席を 1 回も呼ばない。通信しない。**材料はキャッシュに在る**使用済みの 8 書類**。

  1 件注入して 1 回 Core を回す(まとめて変えると丸めの根拠が汚れる)。
  腕は 3 つ。**同じ改変後の値・同じ refs** を当てる。
    Core = verify_document(zip, P16, 改変後の文) の state と pointers
    D′   = 値が一致する fact を全部返す(単位換算なし・帯なし・意味的選別なし)
    D″   = D′ + 単位の倍率 + 最小桁 ±1 の帯

**D′・D″ には改変後の値を構成から直接渡す**(文から数を拾う手間を与えない =
**値検索に有利な側に倒す**)。**Core の丸め規約は渡さない。**

    python3 measure/xbrl_a_core_vs_grep_2026-10-17.py [--docs A,B] [--profile P16]
"""
import argparse
import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, HERE)

from adapters.xbrl import edinet as ED          # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
import inject as IJ                             # noqa: E402
import prepare_material as PM                   # noqa: E402

FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
OUT = os.path.join(FX, "a_core_vs_grep_2026-10-17.json")
SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")
SEED_FILE = os.path.join(HERE, "SEED.json")
SEAL = "docs/XBRL_A_CORE_VS_GREP_SEAL_2026-10-17.md"
TMP = os.path.join(os.environ.get("TMPDIR", "/tmp"), "a_core_vs_grep")
CAP = {"T5_COINCIDENT": 40, "T1_VALUE": 5, "T3_ABSENT": 5}   # 封 §2
TOL = 1e-9
MULTIPLIERS = (1.0, 1000.0, 1000000.0, 0.001, 0.000001)      # 封 §3 の D″


# ---------------------------------------------------------------- 封 §3-1
def norm_pointer(p):
    """**Core・D′・D″・正解の 4 つ全部に掛ける 1 つの関数**(封 §3-1)。

    `xbrl:jppfs_cor:NetSales@CurrentYearDuration` も
    `NetSales@CurrentYearDuration` も `netsales@currentyearduration` にする。
    **掛け忘れが一致率を作るので、往復を門で確かめる。**
    """
    if p is None:
        return None
    s = str(p).strip()
    if s.startswith("xbrl:"):
        s = s[len("xbrl:"):]
    head, _, ctx = s.partition("@")
    if ":" in head:                     # 分類体系の前置きを落とす
        head = head.rsplit(":", 1)[1]
    return "%s@%s" % (head.lower(), ctx.lower())


def value_index(refs):
    idx = collections.defaultdict(list)
    for r in refs:
        idx[round(r["value"], 6)].append(r)
    return idx


def d_prime(value, idx):
    """**D′**: 値が一致する fact を全部。0 / 1 / 2 件以上で言うことが決まる。"""
    hits = idx.get(round(value, 6), [])
    return _say(hits)


def d_double(value, idx, raw_text):
    """**D″**: D′ + 単位の倍率 + 最小桁 ±1 の帯。**意味的選別は足さない。**"""
    seen, hits = set(), []
    step = last_digit_step(raw_text)
    for m in MULTIPLIERS:
        base = value * m
        for cand in (base, base - step * m, base + step * m):
            for r in idx.get(round(cand, 6), []):
                if r["key"] not in seen:
                    seen.add(r["key"])
                    hits.append(r)
    return _say(hits)


def last_digit_step(raw_text):
    """文中の数の**最小桁の 1**(`27.6` なら 0.1、`1,234` なら 1)。"""
    s = str(raw_text or "")
    m = re.search(r"\.(\d+)", s)
    return 10.0 ** (-len(m.group(1))) if m else 1.0


def _say(hits):
    """**封 §3-1**: `refs` の鍵にも `norm_pointer` を掛ける。

    最初の実装はここで生の鍵を返していた。Core 側だけ正規化されていたので、
    **D′ の参照先は正解と字が合わず、「偶然一致する側だった」が 0 件に見えた。**
    記憶 `normalize-both-sides-of-a-comparison` の型(これで 6 回目)。
    """
    keys = sorted({norm_pointer(r["key"]) for r in hits})
    if not keys:
        return {"言うこと": "原資料と一致しない", "参照先": None, "当たり": 0}
    if len(keys) > 1:
        return {"言うこと": "一意でない", "参照先": None, "当たり": len(keys)}
    return {"言うこと": "確認済み", "参照先": keys[0], "当たり": 1}


def core_say(claim):
    """Core の言うことを同じ 3 語に翻訳する(**腕ごとに語を変えない**)。"""
    if claim is None:
        return {"言うこと": "対応が付かない", "参照先": None, "state": None}
    st = claim.get("state")
    ptrs = sorted({norm_pointer(p) for p in (claim.get("pointers") or [])})
    if st == "GROUNDED" and len(ptrs) == 1:
        return {"言うこと": "確認済み", "参照先": ptrs[0], "state": st}
    if st == "GROUNDED":
        return {"言うこと": "一意でない", "参照先": None, "state": st}
    return {"言うこと": "止めた(%s)" % st, "参照先": None, "state": st}


def core_pointer_say(claim):
    """**封 §3 の「`state` と `pointers`」のもう 1 つの読み方。**

    Core は値が合わないとき **`VALUE_MISMATCH` で止めながら参照先を名指す。**
    厳しい読み方(`core_say`)は「確認済み」でないと参照先を捨てるので、
    **T5 では構造上 0% になる**(正しく止めた Core が特定 0 になる)。
    だから**止めても pointer を読む**読み方を並べて出す。**腕を増やしたのではない。**
    """
    if claim is None:
        return {"言うこと": "対応が付かない", "参照先": None, "state": None}
    ptrs = sorted({norm_pointer(p) for p in (claim.get("pointers") or [])})
    st = claim.get("state")
    if len(ptrs) == 1:
        return {"言うこと": ("確認済み" if st == "GROUNDED"
                         else "止めたが参照先を名指した(%s)" % st),
                "参照先": ptrs[0], "state": st}
    if not ptrs:
        return {"言うこと": "参照先を出さない(%s)" % st, "参照先": None, "state": st}
    return {"言うこと": "一意でない", "参照先": None, "state": st}


def gold_of(inj):
    """**軸3 の正解。構成から決まるものだけ**(封 §2)。"""
    d, t = inj["detail"], inj["type"]
    if t == "T5_COINCIDENT":
        return {"種類": "参照先が在る", "正解": norm_pointer(d["true_ref_key"]),
                "偶然一致する側": norm_pointer(d["coincident_ref_key"])}
    if t == "T3_ABSENT":
        return {"種類": "参照先は無い", "正解": None, "偶然一致する側": None}
    return {"種類": "値がどこにも無い", "正解": None, "偶然一致する側": None}


def judge(inj, say, gold):
    """1 件 1 腕の判定。**判定を 1 か所に置く**(字で散らすと変異が黙る)。"""
    out = {"参照先を出した": say["参照先"] is not None, "特定": None, "誤認定": False,
           "保留": say["参照先"] is None}
    if gold["種類"] == "参照先が在る":
        out["特定"] = (say["参照先"] == gold["正解"])
        if say["参照先"] is not None and not out["特定"]:
            out["誤認定"] = True
            out["偶然一致する側だった"] = (say["参照先"] == gold["偶然一致する側"])
    elif gold["種類"] == "参照先は無い":
        out["誤認定"] = say["参照先"] is not None
    else:                                     # 値がどこにも無い
        out["誤認定"] = (say["言うこと"] == "確認済み")
    return out


def claim_for(claims, inj):
    """注入した場所の主張を探す。**0 件・2 件以上は「対応が付かない」。**"""
    if inj["type"] == "T3_ABSENT":
        sent = inj["detail"]["inserted_sentence"]
        cands = [c for c in claims if c.get("span") and c["span"][:20] in sent]
    else:
        v = inj["new_value"]
        cands = [c for c in claims
                 if c.get("value") is not None and abs(c["value"] - v) <= TOL
                 and c.get("span") and inj["replacement"] in c["span"]]
        if len(cands) != 1:                   # 字の手がかりが無いときは値だけで
            cands = [c for c in claims if c.get("value") is not None
                     and abs(c["value"] - v) <= TOL]
    return cands[0] if len(cands) == 1 else None


def material(doc):
    class A(object):
        pass
    a = A()
    a.zip, a.doc, a.out = ED.cache_path(doc), doc, TMP
    PM.prepare_xbrl(a)
    base = os.path.join(TMP, doc)
    text = io.open(base + ".original.txt", encoding="utf-8").read()
    refs = json.load(io.open(base + ".reference_numbers.json", encoding="utf-8"))
    if isinstance(refs, dict):
        refs = refs.get("refs", refs)
    return text, refs


def run_doc(doc, seed, profile):
    zb = io.open(ED.cache_path(doc), "rb").read()
    text, refs = material(doc)
    idx = value_index(refs)
    rows, counts = [], {}
    for t, cap in CAP.items():
        chosen, cat, _, _ = IJ.select(text, refs, "xbrl", seed, doc, cap, types=[t])
        counts[t] = {"作れる site": cat[t], "注入した": len(chosen)}
        for inj in chosen:
            tampered, placements = IJ.apply_edits(text, [inj])
            back = IJ.revert(tampered, [inj], placements, text)
            if back != text:
                raise SystemExit("**round-trip が合わない: %s %s。止める**"
                                 % (doc, inj["id"]))
            out = VD.verify_document(zb, profile, tampered)
            claim = claim_for(out["claims"], inj)
            gold = gold_of(inj)
            n = len(idx.get(round(inj["new_value"], 6), []))
            says = {"Core": core_say(claim),
                    "Core-P": core_pointer_say(claim),
                    "D′": d_prime(inj["new_value"], idx),
                    "D″": d_double(inj["new_value"], idx,
                                   inj.get("replacement"))}
            row = {"doc": doc, "id": inj["id"], "型": t,
                   "改変後の値": inj["new_value"],
                   "同じ値を持つ fact の数 n": n,
                   "層": "n=1" if n == 1 else ("n=2〜5" if n <= 5 else "n>=6"),
                   "正解": gold, "対応が付いた": claim is not None,
                   "腕": {k: {"言うこと": v["言うこと"], "参照先": v["参照先"],
                            "判定": judge(inj, v, gold)} for k, v in says.items()}}
            rows.append(row)
    return rows, counts


def tally(rows):
    """腕ごとに**分母を分けて**数える(封 §4)。"""
    out = {}
    for arm in ("Core", "Core-P", "D′", "D″"):
        t5 = [r for r in rows if r["型"] == "T5_COINCIDENT"]
        pointed = [r for r in rows if r["腕"][arm]["判定"]["参照先を出した"]]
        ident = [r for r in t5 if r["腕"][arm]["判定"]["特定"]]
        wrong = [r for r in pointed if r["腕"][arm]["判定"]["誤認定"]]
        held = [r for r in rows if r["腕"][arm]["判定"]["保留"]]
        t1 = [r for r in rows if r["型"] == "T1_VALUE"]
        t3 = [r for r in rows if r["型"] == "T3_ABSENT"]
        t1_pass = [r for r in t1 if r["腕"][arm]["言うこと"] == "確認済み"]
        t3_named = [r for r in t3 if r["腕"][arm]["判定"]["参照先を出した"]]
        strata = {}
        for s in ("n=1", "n=2〜5", "n>=6"):
            sr = [r for r in t5 if r["層"] == s]
            sp = [r for r in sr if r["腕"][arm]["判定"]["参照先を出した"]]
            strata[s] = {"T5 の件数": len(sr),
                         "特定": sum(1 for r in sr if r["腕"][arm]["判定"]["特定"]),
                         "参照先を出した": len(sp),
                         "誤認定": sum(1 for r in sp if r["腕"][arm]["判定"]["誤認定"])}
        out[arm] = {
            "特定率(分母 = T5 の件数)": {"分子": len(ident), "分母": len(t5),
                                "率": pct(len(ident), len(t5))},
            "誤認定率(分母 = 参照先を出した件)": {"分子": len(wrong), "分母": len(pointed),
                                    "率": pct(len(wrong), len(pointed))},
            "保留率(分母 = 注入した件)": {"分子": len(held), "分母": len(rows),
                                "率": pct(len(held), len(rows))},
            "T1 の通し(値がどこにも無いのに確認済み)": {"分子": len(t1_pass),
                                        "分母": len(t1),
                                        "率": pct(len(t1_pass), len(t1))},
            "T3 の名指し(参照先が無いのに名指した)": {"分子": len(t3_named), "分母": len(t3),
                                       "率": pct(len(t3_named), len(t3))},
            "層別(T5)": strata,
            "偶然一致する側を採った件": sum(
                1 for r in rows if r["腕"][arm]["判定"].get("偶然一致する側だった")),
            "**正解と食い違った対**": [
                {"id": r["id"], "正解": r["正解"]["正解"],
                 "この腕の参照先": r["腕"][arm]["参照先"]}
                for r in t5 if r["腕"][arm]["参照先"] is not None
                and not r["腕"][arm]["判定"]["特定"]][:20]}
    return out


def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default=None)
    ap.add_argument("--profile", default="P16")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit("既に在る: %s(測り直さない)" % a.out)
    # **封 §3-1 の往復を先に当てる。通らなければ数を 1 つも出さない**
    pair = ("xbrl:jppfs_cor:NetSales@CurrentYearDuration",
            "NetSales@CurrentYearDuration")
    if norm_pointer(pair[0]) != norm_pointer(pair[1]):
        raise SystemExit("**norm_pointer の往復が通らない。止める**")
    seed, meta = IJ.verify_seed_sealed(SEED_FILE)
    docs = (a.docs.split(",") if a.docs
            else json.load(io.open(SPLIT, encoding="utf-8"))["final_eval_sealed"])
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(FX, exist_ok=True)
    rows, counts = [], {}
    for doc in docs:
        r, c = run_doc(doc, seed, a.profile)
        rows.extend(r)
        counts[doc] = c
        print("  %s 注入 %d 件(T5 %d / T1 %d / T3 %d)"
              % (doc, len(r), c["T5_COINCIDENT"]["注入した"],
                 c["T1_VALUE"]["注入した"], c["T3_ABSENT"]["注入した"]))
    t = tally(rows)
    unmapped = [r["id"] for r in rows if not r["対応が付いた"]]
    rec = {"seal": SEAL, "step": "**(ア)。0 USD・席を呼ばない・通信しない**",
           "profile": a.profile, "書類": docs,
           "材料": "**使用済みの 8 書類**(2026-10-14 開封)。未使用の 8 件は使っていない",
           "注入の種": {"file": "measure/SEED.json", "sealed_on": meta.get("sealed_on"),
                   "note": "**git に追跡され、コミット内容と一致している**"},
           "注入の件数": counts, "注入の合計": len(rows),
           "**対応が付かなかった件**": {"件数": len(unmapped), "ids": unmapped,
                            "note": "**推測で埋めない**"},
           "正規化": "**norm_pointer を Core・D′・D″・正解の 4 つ全部に掛けた**",
           "採点": t,
           "limits": [
               "**Core の照合機能の切り分けであって、LLM + Core の優位性の証明ではない**",
               "**Core 単体の差が小さくても、LLM との相互補完は否定されない**",
               "**使用済みの書類である。**未使用データでの再現性は測っていない",
               "**T5 の正解は「改変前の文で値が一意に当たった主張」に偏る**",
               "**D′・D″ には改変後の値を構成から渡した**(値検索に有利な側に倒してある)",
               "**正解は `identified_sites`(値の一意性 + 単位・ラベルの手がかり)で"
               "作られている。正解そのものが誤りうる** ― "
               "食い違った対を `**正解と食い違った対**` に残したので 1 件ずつ読める"],
           "rows": rows}
    json.dump(rec, io.open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== (ア) Core 単体 対 D′・D″(profile %s・注入 %d 件)==="
          % (a.profile, len(rows)))
    for arm in ("Core", "Core-P", "D′", "D″"):
        v = t[arm]
        print("  %-6s 特定 %5s%% (%2d/%2d) / 誤認定 %5s%% (%2d/%2d) / 保留 %5s%% / "
              "T1 通し %5s%% / T3 名指し %5s%%"
              % (arm, v["特定率(分母 = T5 の件数)"]["率"],
                 v["特定率(分母 = T5 の件数)"]["分子"], v["特定率(分母 = T5 の件数)"]["分母"],
                 v["誤認定率(分母 = 参照先を出した件)"]["率"],
                 v["誤認定率(分母 = 参照先を出した件)"]["分子"],
                 v["誤認定率(分母 = 参照先を出した件)"]["分母"],
                 v["保留率(分母 = 注入した件)"]["率"],
                 v["T1 の通し(値がどこにも無いのに確認済み)"]["率"],
                 v["T3 の名指し(参照先が無いのに名指した)"]["率"]))
    print("  **対応が付かなかった件: %d**" % len(unmapped))
    for arm in ("Core", "Core-P", "D′", "D″"):
        print("  層別(T5)%-6s %s" % (arm, json.dumps(t[arm]["層別(T5)"],
                                                  ensure_ascii=False)))
    print("->", a.out)


if __name__ == "__main__":
    main()
