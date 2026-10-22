# -*- coding: utf-8 -*-
"""封 v2 §3 段 3 ― **材料を組み、0 USD の下見を通す。席は 1 回も呼ばない。**

spec: `docs/XBRL_CD_MATERIAL_SPEC_2026-10-17.md`(§1〜§5 と §7 の追記)。
封: `docs/XBRL_CD_SEAL_V2_2026-10-17.md`(差分)/ `docs/XBRL_CD_SEAL_2026-10-17.md`(v1)。

**独立監査(2026-10-17)の REVISE に応える形で書く。**

  指摘 2: **採点の関数は (ア) の実物をそのまま import して使う**
          (書き直すと正規化の掛け忘れが再発する。あの型は 6 回目と記録されている)
  指摘 3: **「見せない字が材料に 0 件」をコードの検査にし、結果を記録に残す**

やること(**どれも 0 USD**)
  1. 8 書類の材料(本文・refs)を作る ― `prepare_material`(**adapters を import しない**)
  2. 注入 8 件(**T5 → T3 → T1** の順。T2 は入れない)を **1 本の文に当てる**
  3. round-trip を確かめる(合わなければその書類で止める)
  4. 判定する 24 行(注入 8 + 無改変 16)を**本文の出現順**で選ぶ ―
     **行の一覧は Core を通さずに作る**(`lib.numbers` の走査。材料が Core に依存しない)
  5. **見せない字の検査**(0 件でなければ止める)
  6. Core・D′・D″ を**同じ改変後の文**に当てて記録する(**席の答えが来る前に出せる分**)
  7. **丸めの汚染の検査**: 原文と改変後で Core の書類単位の決定が変わっていないか
  8. 材料の字数とトークンの見込みを記録する

    python3 measure/xbrl_cd_material_2026-10-17.py [--docs A,B]
"""
import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, HERE)

from adapters.xbrl import edinet as ED          # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
import inject as IJ                             # noqa: E402
from lib import numbers as N                    # noqa: E402

FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
DRAW = os.path.join(FX, "draw_2026-10-17.json")
OUT = os.path.join(FX, "material_2026-10-17.json")
TMP = os.path.join(os.environ.get("TMPDIR", "/tmp"), "cd8_material")
SEED_FILE = os.path.join(HERE, "SEED.json")
SPEC = "docs/XBRL_CD_MATERIAL_SPEC_2026-10-17.md"
SEAL_V2 = "docs/XBRL_CD_SEAL_V2_2026-10-17.md"
PROFILE = "P16"
N_INJECT = 8                 # spec §1
N_PLAIN = 16                 # spec §1
TYPE_ORDER = ("T5_COINCIDENT", "T3_ABSENT", "T1_VALUE")   # spec §1(T2 は入れない)
# spec §2 の「見せないもの」。**字で持つ**
BANNED = ("注入", "正解", "Core", "engine", "GROUNDED", "pointer",
          "T1", "T3", "T5", "profile", "P16", "P20", "VALUE_MISMATCH")

# **(ア) の実物をそのまま使う**(監査の指摘 2)
_sp = importlib.util.spec_from_file_location(
    "a_core_vs_grep", os.path.join(HERE, "xbrl_a_core_vs_grep_2026-10-17.py"))
A1 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(A1)

PROMPT = u"""次の文章は、ある会社が提出した報告書の一部です。
あわせて、その会社が同じ報告書とともに提出した数値データの一覧を渡します。
一覧の各行は `名前@期間や区分|値|単位` の形です。

文章の中の数について、下の一覧の行ごとに次の 3 つを答えてください。

1. `id` ― 一覧の id をそのまま書く
2. `判定` ― 次の 3 語のどれか 1 つだけ
   - `確認済み` : その数が、渡した数値データのどれかと対応していると言える
   - `誤りが在る` : その数は、渡した数値データと合わない
   - `判定できない` : どちらとも言えない
3. `参照先` ― その数が指していると考える数値データの行の名前を
   `名前@期間や区分` の形で 1 つだけ書く。決められないときは `なし` と書く

**全部の行に答えてください。**自由な文章や、3 語以外の言葉は書かないでください。
"""


def pick_injections(text, refs, seed, doc):
    """spec §1: **T5 → T3 → T1 の順に 8 件まで。足りなければ足りないと書く。**"""
    chosen, counts = [], {}
    for t in TYPE_ORDER:
        if len(chosen) >= N_INJECT:
            counts[t] = {"作れる site": None, "採った": 0, "注": "8 件そろったので見ていない"}
            continue
        want = N_INJECT - len(chosen)
        got, cat, _, _ = IJ.select(text, refs, "xbrl", seed, doc, want, types=[t])
        counts[t] = {"作れる site": cat[t], "採った": len(got)}
        chosen.extend(got)
    return chosen, counts


def quantity_tokens(text):
    """**行の一覧は Core を通さずに作る**(材料が Core に依存しないため)。"""
    out = []
    for t in N.scan(text):
        if N.is_quantity(text, t):
            out.append(t)
    return out


def excerpt(text, a, b, span=40):
    s = max(0, a - span)
    return text[s:min(len(text), b + span)].replace("\n", " ")


def build_rows(text, chosen, placements):
    """注入 8 行 + 無改変 16 行。**本文の出現順。**"""
    inj_by_span = {}
    for c in chosen:
        a, b = placements[c["id"]]
        inj_by_span[(a, b)] = c
    rows, plain = [], []
    for t in quantity_tokens(text):
        hit = None
        for (a, b), c in inj_by_span.items():
            if not (t.end <= a or t.start >= b):
                hit = c
                break
        rec = {"数の字面": t.text, "値": t.value, "単位": t.unit,
               "span": [t.start, t.end], "抜粋": excerpt(text, t.start, t.end)}
        if hit is not None:
            rec["**注入**"] = hit["id"]
            rows.append(rec)
        else:
            plain.append(rec)
    rows.extend(plain[:N_PLAIN])
    for i, r in enumerate(sorted(rows, key=lambda r: r["span"][0]), 1):
        r["id"] = "R%03d" % i
    return sorted(rows, key=lambda r: r["span"][0]), len(plain)


def seat_text(rows, text, refs):
    """席に渡す字(spec §2 の 4 つだけ)。**正解も注入も Core も入れない。**"""
    lines = [PROMPT, u"\n---- 文章 ----\n", text,
             u"\n---- 数値データの一覧 ----\n",
             A1.compact_refs(refs) if hasattr(A1, "compact_refs")
             else "\n".join("%s|%s|%s" % (r["key"], r["value"], r.get("unit") or "")
                            for r in refs),
             u"\n---- 判定する行 ----\n"]
    for r in rows:
        lines.append(u"%s\t%s\t%s\t%s" % (r["id"], r["数の字面"],
                                         r["単位"] or "", r["抜粋"]))
    return "\n".join(lines)


def claim_key(c):
    """原文と改変後で**同じ主張**を突き合わせる鍵(id は注入でずれる)。"""
    return (c.get("subject"), c.get("form"), c.get("value"), c.get("unit"))


def contamination(out_o, out_t):
    """**8 件まとめて注入したことが、他の行の判定を動かしていないか。**

    v1 §3 は「1 便 1 件」(まとめて変えると書類単位の丸めの根拠が汚れる)。
    spec §1 は「1 本の文に 8 件」なので、**汚染を測って出す**。
    一意に対になる主張だけを比べ、**対にならなかった件数も書く**。
    """
    def index(out):
        d = {}
        for c in out["claims"]:
            d.setdefault(claim_key(c), []).append(c)
        return d
    io_, it = index(out_o), index(out_t)
    both = [k for k in io_ if k in it and len(io_[k]) == 1 and len(it[k]) == 1]
    changed = []
    for k in both:
        a, b = io_[k][0], it[k][0]
        pa = sorted({A1.norm_pointer(p) for p in (a.get("pointers") or [])})
        pb = sorted({A1.norm_pointer(p) for p in (b.get("pointers") or [])})
        if a.get("state") != b.get("state") or pa != pb:
            changed.append({"鍵": [str(x) for x in k], "原文": a.get("state"),
                            "改変後": b.get("state")})
    return {"一意に対になった主張": len(both),
            "**判定が動いた**": len(changed), "明細": changed[:10],
            "対にならなかった(原文側)": len([k for k in io_ if k not in both]),
            "対にならなかった(改変後側)": len([k for k in it if k not in both]),
            "書類単位の決定": {"原文": out_o["document"].get("unverifiable"),
                       "改変後": out_t["document"].get("unverifiable"),
                       "**変わったか**": out_o["document"].get("unverifiable")
                                 != out_t["document"].get("unverifiable")},
            "注": "**対にならない行には注入した 8 件が入る**(値が変わったので対にならない)"}


def check_banned(blob):
    """spec §2・監査の指摘 3。**0 件でなければ止める。**"""
    found = {w: blob.count(w) for w in BANNED if w in blob}
    return found


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default=None)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit("既に在る: %s(作り直さない)" % a.out)
    seed, meta = IJ.verify_seed_sealed(SEED_FILE)
    docs = (a.docs.split(",") if a.docs
            else json.load(io.open(DRAW, encoding="utf-8"))["引いた 8 件"])
    os.makedirs(TMP, exist_ok=True)
    per, all_rows = [], []
    for doc in docs:
        zb = io.open(ED.cache_path(doc), "rb").read()
        old_tmp, A1.TMP = A1.TMP, TMP
        try:
            text, refs = A1.material(doc)
        finally:
            A1.TMP = old_tmp
        idx = A1.value_index(refs)
        chosen, counts = pick_injections(text, refs, seed, doc)
        if not chosen:
            per.append({"docID": doc, "**止めた**": "注入が 1 件も作れない"})
            continue
        tampered, placements = IJ.apply_edits(text, chosen)
        back = IJ.revert(tampered, chosen, placements, text)
        if back != text:
            raise SystemExit("**round-trip が合わない: %s。止める**" % doc)
        rows, plain_total = build_rows(tampered, chosen, placements)
        task = seat_text(rows, tampered, refs)
        banned = check_banned(task)
        if banned:
            raise SystemExit("**見せない字が材料に在る: %s。生成の前に止める**" % banned)
        path = os.path.join(TMP, "%s_task.txt" % doc)
        io.open(path, "w", encoding="utf-8").write(task)
        # **席の答えが来る前に出せる分**(Core・D′・D″)
        out_t = VD.verify_document(zb, PROFILE, tampered)
        out_o = VD.verify_document(zb, PROFILE, text)
        claims = out_t["claims"]
        by_id = {c["id"]: c for c in claims}
        pre = {}
        for r in rows:
            inj = next((c for c in chosen if c["id"] == r.get("**注入**")), None)
            claim = None
            for c in claims:
                if c.get("value") is None:
                    continue
                if abs(c["value"] - r["値"]) <= A1.TOL and r["数の字面"] in (c.get("span") or ""):
                    claim = c
                    break
            pre[r["id"]] = {
                "Core": A1.core_pointer_say(claim),
                "Core(厳しい読み方)": A1.core_say(claim),
                "D′": A1.d_prime(r["値"], idx),
                "D″": A1.d_double(r["値"], idx, r["数の字面"]),
                "注入か": bool(inj),
                "正解": A1.gold_of(inj) if inj else None}
        per.append({
            "docID": doc, "本文の字数": len(text), "改変後の字数": len(tampered),
            "refs 件数": len(refs),
            "注入": {"件数": len(chosen), "型ごと": counts,
                   "**8 件そろったか**": len(chosen) == N_INJECT,
                   "ids": [c["id"] for c in chosen],
                   "型の内訳": dict(collections.Counter(c["type"] for c in chosen))},
            "行": {"合計": len(rows), "注入の行": sum(1 for r in rows if r.get("**注入**")),
                  "無改変の行": sum(1 for r in rows if not r.get("**注入**")),
                  "無改変の候補の総数": plain_total,
                  "**24 行そろったか**": len(rows) == N_INJECT + N_PLAIN},
            "材料": {"path": "**scratchpad のみ(repo に入れない)**",
                   "字数": len(task),
                   "sha256": hashlib.sha256(task.encode("utf-8")).hexdigest()},
            "**見せない字**": {"検査した語": list(BANNED), "見つかった": banned,
                        "**0 件か**": not banned},
            "**他の行への影響の検査**": contamination(out_o, out_t),
            "席の前に出せる分": pre})
        all_rows.extend([{"doc": doc, "id": r["id"]} for r in rows])
        print("  %s 注入 %d(%s)/ 行 %d / 材料 %d 字 / 見せない字 %s / 丸め %s"
              % (doc, len(chosen),
                 ",".join("%s:%d" % (k.split("_")[0], v) for k, v in
                          sorted(collections.Counter(c["type"] for c in chosen).items())),
                 len(rows), len(task), "0 件" if not banned else banned,
                 "他の行が動いた %d 件" % per[-1]["**他の行への影響の検査**"]["**判定が動いた**"]))
    rec = {"spec": SPEC, "seal": SEAL_V2,
           "step": "**封 v2 §3 の段 3。0 USD・席を 1 回も呼んでいない**",
           "profile": PROFILE,
           "注入の種": {"file": "measure/SEED.json", "sealed_on": meta.get("sealed_on")},
           "採点の関数": ("**(ア) の実物を import して使った**"
                    "(`norm_pointer` / `_say` / `core_say` / `core_pointer_say` / "
                    "`d_prime` / `d_double` / `gold_of` / `judge`)― 監査の指摘 2"),
           "問いの sha256": hashlib.sha256(PROMPT.encode("utf-8")).hexdigest(),
           "問いの字数": len(PROMPT),
           "書類ごと": per,
           "合計": {"書類": len(per), "行": len(all_rows),
                  "注入": sum(p.get("注入", {}).get("件数", 0) for p in per)},
           "limits": [
               "**席は 1 回も呼んでいない。**A と C′ の数はまだ 1 つも無い",
               "**`席の前に出せる分` は Core・D′・D″ の言うことだけ**で、"
               "腕の成績ではない(腕は席の答えと合わせて初めて決まる)",
               "**1 本の文に 8 件まとめて注入している**(spec §1)。"
               "v1 §3 の `--batch 1` と違うので、**他の行への影響を測って出した**",
               "**汚染が 0 でなくても A 対 C′ の比較は成立する**"
               "(席と Core が同じ文を見るので入力の差はゼロ)。"
               "**ただし Core の絶対の成績はこの文に固有である**"]}
    json.dump(rec, io.open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== 段 3 下見: 書類 %d / 行 %d / 注入 %d(0 USD)==="
          % (len(per), len(all_rows), rec["合計"]["注入"]))
    print("->", a.out)


if __name__ == "__main__":
    main()
