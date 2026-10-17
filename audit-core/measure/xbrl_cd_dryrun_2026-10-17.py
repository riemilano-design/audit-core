# -*- coding: utf-8 -*-
"""C′ 対 D′ の **0 USD の事前確認**(封 docs/XBRL_CD_SEAL_2026-10-17.md §9 の段 2・3)。

**席を 1 回も呼ばない。生成しない。新しい 8 書類を 1 件も取らない。**
やることは 4 つ。

  1. **引く規則を機械で回し、封の 8 件が再現することを確かめて記録する**
  2. **取得の経路**(鍵の有無は**名前だけ**。値は読まない・書かない)
  3. **構造の実測** ― ただし**使用済みの書類**(2026-10-14 に開封した最終評価 8 件)で測る。
     **新しい 8 件は開かない**(1 度しか開けないので、下見で使い潰さない)
  4. **費用の実測見積もり** ― 過去の席の実測(字数とトークン)から帯で出す

    python3 measure/xbrl_cd_dryrun_2026-10-17.py
"""
import collections
import io
import json
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import sites as S          # noqa: E402  注入はしない。数えるだけ
import prepare_material as PM       # noqa: E402  **adapters を import しない道具**

HP = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17")
OUTDIR = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
DRAW = os.path.join(OUTDIR, "draw_2026-10-17.json")
OUT = os.path.join(OUTDIR, "dryrun_2026-10-17.json")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
SEAL = "docs/XBRL_CD_SEAL_2026-10-17.md"
SEED_HEX = "6a24d72"
NEED = 8
DOC_RE = re.compile(r"S100[A-Z0-9]{4}")
KEY_NAME = "EDINET_API_KEY"          # **名前だけ。値は読まない**
USD_PER_M_OUTPUT = 15.0              # sonnet の出力。全部を出力として数える上限
HUMAN_GUIDE_USD = 3.0                # 人間の目安(2026-10-17)

ROSTER = {"fixtures/xbrl/holdout_p17/pool2_clean_2026-10-14.json",
          "fixtures/xbrl/holdout_p17/fetched_not_read_2026-10-14.json",
          "fixtures/xbrl/holdout_p17/pool_meta_2026-10-14.json",
          "fixtures/xbrl/holdout_p17/pool2_meta_2026-10-14.json"}
THIS_RUN = {SEAL, "fixtures/xbrl/cd8/draw_2026-10-17.json",
            "fixtures/xbrl/cd8/dryrun_2026-10-17.json",
            "docs/XBRL_CD_RESULT_2026-10-17.md",
            "docs/XBRL_CD_DRYRUN_2026-10-17.md",
            "tests/measure/test_xbrl_cd_seal.py",
            "tests/measure/test_xbrl_cd_dryrun.py",
            "measure/xbrl_cd_draw_2026-10-17.py",
            "measure/xbrl_cd_dryrun_2026-10-17.py"}

# 過去の席の実測(**この便で測った数ではない。記録から読む**)
PAST = [("errdet seat1 sonnet", "fixtures/sheet/errdet_answers_seat1_2026-10-17.json", 11151),
        ("errdet seat2 haiku", "fixtures/sheet/errdet_answers_seat2_2026-10-17.json", 11151),
        ("poc_c seat1 sonnet", "fixtures/sheet/poc_c_answers_seat1_2026-10-17.json", 20300),
        ("poc_c seat2 haiku", "fixtures/sheet/poc_c_answers_seat2_2026-10-17.json", 20300)]


def sealed_order():
    pool = json.load(io.open(os.path.join(HP, "pool2_clean_2026-10-14.json"),
                             encoding="utf-8"))["pool_clean"]
    order = sorted(pool)
    random.Random(int(SEED_HEX, 16)).shuffle(order)
    sp = json.load(io.open(os.path.join(HP, "split_2026-10-14.json"),
                           encoding="utf-8"))
    for name, a, b in (("used", 0, 6), ("development", 6, 14),
                       ("final_eval_sealed", 14, 22)):
        if sp[name] != order[a:b]:
            raise SystemExit("**封じた群 %s が再現しない。止める**" % name)
    return order, sp


def mentioned_outside_roster():
    out = {}
    files = subprocess.run(["git", "ls-files"], cwd=ROOT,
                           capture_output=True, text=True).stdout.split()
    for f in files:
        if f in ROSTER or f in THIS_RUN or f.endswith((".xlsx", ".zip", ".png", ".pdf")):
            continue
        try:
            t = io.open(os.path.join(ROOT, f), encoding="utf-8").read()
        except (IOError, OSError, UnicodeDecodeError):
            continue
        for d in set(DOC_RE.findall(t)):
            out.setdefault(d, f)
    return out


def draw():
    """封 §1-2 の規則。**飛ばした理由も残す**(黙って飛ばさない)。"""
    order, sp = sealed_order()
    seen = mentioned_outside_roster()
    taken, skipped = [], []
    for i, d in enumerate(order[22:], 22):
        if len(taken) >= NEED:
            break
        if d in seen:
            skipped.append({"位置": i, "docID": d, "名前が出た file": seen[d]})
        else:
            taken.append({"位置": i, "docID": d})
    if len(taken) != NEED:
        raise SystemExit("**規則で %d 件しかそろわない。止める**" % len(taken))
    cached = set(DOC_RE.findall("\n".join(os.listdir(CACHE)))) if os.path.isdir(CACHE) else set()
    in_cache = [t["docID"] for t in taken if t["docID"] in cached]
    if in_cache:
        raise SystemExit("**引いた書類が既にキャッシュに在る: %s。止める**" % in_cache)
    free = sum(1 for d in order[22:] if d not in seen)
    return {"seal": SEAL, "rule": "封 §1-2。order[22:] を順に見て、名簿以外で名前が出ていない先頭 8 件",
            "seed_hex": SEED_HEX, "pool": len(order),
            "予備": len(order) - 22, "規則を満たす書類": free,
            "引いた 8 件": [t["docID"] for t in taken],
            "位置": [t["位置"] for t in taken],
            "飛ばした件": skipped,
            "**キャッシュに在るか**": {"在った": in_cache, "note": "1 件も無い = 一度も取っていない"}}


def material_of(doc_id, zip_path, out_dir):
    """**使用済みの書類**で構造を測る。`prepare_material` をそのまま呼ぶ。"""
    class A(object):
        pass
    a = A()
    a.zip, a.doc, a.out = zip_path, doc_id, out_dir
    PM.prepare_xbrl(a)
    base = os.path.join(out_dir, doc_id)
    tp, rp = base + ".original.txt", base + ".reference_numbers.json"
    text = io.open(tp, encoding="utf-8").read() if os.path.exists(tp) else None
    refs = None
    if os.path.exists(rp):
        refs = json.load(io.open(rp, encoding="utf-8"))
        if isinstance(refs, dict):
            refs = refs.get("refs", refs)
    return text, refs


def compact_refs(refs):
    """席に見せる形(1 件 1 行)。**どれが答えかの手がかりを足さない。**"""
    return "\n".join("%s|%s|%s" % (r["key"], r["value"], r.get("unit") or "")
                     for r in refs)


def value_collision(refs):
    """**同じ値を持つ fact の数 n** の分布(封 §5-3 の層)。"""
    c = collections.Counter(round(r["value"], 6) for r in refs)
    hist = collections.Counter()
    for n in c.values():
        hist["n=1" if n == 1 else ("n=2〜5" if n <= 5 else "n>=6")] += n
    return dict(hist), len(c)


def past_runs():
    rows = []
    for name, path, chars in PAST:
        j = json.load(io.open(os.path.join(ROOT, path), encoding="utf-8"))
        tok = j["費用"]["使ったトークン(実測)"]
        rows.append({"席": name, "材料の字数": chars, "トークン(実測)": tok,
                     "1 字あたり": round(float(tok) / chars, 2)})
    return rows


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    rec = {"seal": SEAL, "step": "封 §9 の段 2・段 3。**費用 0 USD・生成なし**"}
    d = draw()
    os.makedirs(OUTDIR, exist_ok=True)
    if not os.path.exists(DRAW):
        json.dump(d, io.open(DRAW, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    rec["引いた 8 件"] = d["引いた 8 件"]
    rec["取得の経路"] = {
        "鍵の環境変数の名前": KEY_NAME,
        "**この session で設定されているか**": bool(os.environ.get(KEY_NAME)),
        "値": "**読まない・書かない**",
        "取得の道具": "adapters/xbrl/edinet.py の fetch(doc_id)",
        "note": ("鍵が無いと**新しい 8 件は取れない**。"
                 "**下見はそれを待たずにできる**(構造は使用済みの書類で測る)")}

    _, sp = sealed_order()
    ref_docs = sp["final_eval_sealed"]
    tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), "cd8_dryrun")
    os.makedirs(tmp, exist_ok=True)
    per, miss = [], []
    for doc in ref_docs:
        zp = os.path.join(CACHE, doc + ".zip")
        if not os.path.exists(zp):
            miss.append(doc)
            continue
        try:
            text, refs = material_of(doc, zp, tmp)
        except SystemExit as e:
            miss.append("%s(%s)" % (doc, e))
            continue
        if text is None or refs is None:
            miss.append("%s(材料の file が見つからない)" % doc)
            continue
        cr = compact_refs(refs)
        hist, distinct = value_collision(refs)
        counts = {"T1_VALUE": len(S.t1_sites(text, refs)),
                  "T2_UNIT": len(S.t2_sites(text, refs)),
                  "T3_ABSENT": len(S.t3_sites(text, refs, "xbrl")),
                  "T5_COINCIDENT": len(S.t5_sites(text, refs))}
        per.append({"docID": doc, "本文の字数": len(text), "refs 件数": len(refs),
                    "refs を 1 行にした字数": len(cr),
                    "値の異なり": distinct, "同じ値を持つ fact の数 n": hist,
                    "注入できる site の数": counts,
                    "数の token": len(S.data_bearing_sites(text, refs)),
                    "一意に同定できる token": len(S.identified_sites(text, refs))})
    rec["構造(**使用済みの書類で測った。新しい 8 件は開いていない**)"] = {
        "参考にした書類": ref_docs, "読めなかった": miss, "書類ごと": per}
    if not per:
        raise SystemExit("**参考書類が 1 件も読めない。止める**")

    text_avg = sum(p["本文の字数"] for p in per) / float(len(per))
    refs_avg = sum(p["refs を 1 行にした字数"] for p in per) / float(len(per))
    t5_zero = [p["docID"] for p in per if p["注入できる site の数"]["T5_COINCIDENT"] == 0]
    past = past_runs()
    # 席 1 便の材料 = 問い + 本文 + refs + 回答する行の雛形(封 §4・§5 の設計)
    q_chars = 1800            # 問いと回答の形(段 11 の問いと同じ桁)
    rows_chars = 24 * 120     # 注入 8 + 無改変 16 の行
    mat = q_chars + text_avg + refs_avg + rows_chars
    low_slope = 0.29          # sonnet の 2 点から出した傾き(**2 点では傾きは決まらない**)
    low = 97900 + low_slope * mat
    high = 70000 + 1.0 * mat  # 1 字 ≒ 1 トークンの悲観側
    band = {"1 便の材料の字数(平均の見込み)": int(mat),
            "1 便のトークン(低い側)": int(low), "1 便のトークン(高い側)": int(high),
            "8 便 1 席の上限 USD(低い側)": round(8 * low * USD_PER_M_OUTPUT / 1e6, 2),
            "8 便 1 席の上限 USD(高い側)": round(8 * high * USD_PER_M_OUTPUT / 1e6, 2)}
    rec["費用の実測見積もり"] = {
        "過去の席の実測(記録から読んだ)": past,
        "数え方": "**全部のトークンを出力として数える上限**(sonnet 15 USD/1M)",
        "見積もりの帯": band,
        "人間の目安": HUMAN_GUIDE_USD,
        "**目安の中か**": band["8 便 1 席の上限 USD(高い側)"] <= HUMAN_GUIDE_USD,
        "note": ("**2 点から傾きを出しているので、低い側は確かな下限ではない。**"
                 "高い側は 1 字 ≒ 1 トークンの悲観側")}
    rec["止める"] = {"封 §8 の 1": "見積もりが目安を超えたら生成の前に止めて報告する",
                   "**規模を自分で削らない**": "削り方の選択肢を出して人間が決める",
                   "T5 が 0 件の書類": t5_zero}
    rec["limits"] = [
        "**構造は使用済みの書類で測った。**新しい 8 件の本文の長さ・refs の件数は違いうる",
        "**注入はしていない。**site の数は「作れる機会」であって注入の結果ではない",
        "**費用は見積もりである。**実測は生成してからしか出ない",
        "**T5 の正解は、改変前の文で値が一意に当たった ref である** ― "
        "だから T5 は『元の値が一意に同定できた主張』に偏る(一般化の限界)"]
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== 0 USD の事前確認(生成なし・新しい 8 件は開いていない)===")
    print("引いた 8 件: %s" % " ".join(d["引いた 8 件"]))
    print("飛ばした件: %d / 規則を満たす書類: %d" % (len(d["飛ばした件"]), d["規則を満たす書類"]))
    print("%s がこの session に在るか: %s" % (KEY_NAME, bool(os.environ.get(KEY_NAME))))
    print("--- 構造(使用済みの書類 %d 件)---" % len(per))
    for p in per:
        print("  %s 本文 %6d 字 / refs %4d 件(%6d 字)/ site T1 %3d T2 %3d T3 %3d **T5 %3d**"
              % (p["docID"], p["本文の字数"], p["refs 件数"], p["refs を 1 行にした字数"],
                 p["注入できる site の数"]["T1_VALUE"], p["注入できる site の数"]["T2_UNIT"],
                 p["注入できる site の数"]["T3_ABSENT"], p["注入できる site の数"]["T5_COINCIDENT"]))
    print("  平均: 本文 %d 字 / refs %d 字" % (text_avg, refs_avg))
    print("--- 費用 ---")
    for r in past:
        print("  過去 %-20s 材料 %6d 字 -> %7d トークン(1 字 %.2f)"
              % (r["席"], r["材料の字数"], r["トークン(実測)"], r["1 字あたり"]))
    print("  1 便の材料 %d 字 -> %d〜%d トークン" % (mat, low, high))
    print("  **8 便 1 席の上限: %.2f〜%.2f USD(人間の目安 %.1f)**"
          % (band["8 便 1 席の上限 USD(低い側)"],
             band["8 便 1 席の上限 USD(高い側)"], HUMAN_GUIDE_USD))
    print("  **目安の中か: %s**" % rec["費用の実測見積もり"]["**目安の中か**"])
    print("->", OUT)


if __name__ == "__main__":
    main()
