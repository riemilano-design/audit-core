# -*- coding: utf-8 -*-
"""誤りを通す率(人間の問い 2026-10-14「誤りを通す率は調べて。0 を目指さないと意味ない」)。

やること: 書類の経営分析の本文を NFKC で正規化した文章を土台(baseline)にし、その土台で
GROUNDED になった**数の主張**の数字を 1 つずつわざと変え(V1 = 10 倍、V2 = 末尾の桁を
+1)、変えた後も GROUNDED と言う件数を数える。**通した = 誤りを通した**。目標は 0。
数は文の中の位置で同定し、主張の id は数の並び順で付くので、変えた前後で同じ id を
突き合わせる(変えた後の値が期待どおりでない行は「id がずれた」として別に数える)。

**既定は全部の行に 2 通りの変え方を両方当てる**(``--kinds V1,V2``)。1 行に 1 通りだけ
当てる版は、どの行にどちらが当たるかで標本が変わり、profile 間の比較も、限界の型が
標本に入るかどうかも、割り当てに左右された(2026-10-14 に実測。順番で割り振った版 →
id で決める版 → 両方当てる版と直した)。

**``--batch 1`` が正**(2026-10-15 に実測した 3 つ目の欠陥)。1 回の検証で 25 件まとめて
変えると、**変えた数そのものが「書類の丸め方」の根拠に入り**(``profile.doc_rounding``)、
書類単位の決定が round / truncate で入れ替わることがある。入れ替わると、同じ束の他の
主張の照合の帯が変わる ― つまり**変えた件数が互いの結果を汚す**。実測: ``S100Z4Q1`` を
P19 で 25 件ずつ変えると、原文では truncate だった決定が変えた後は round に入れ替わり、
末尾 +1 の誤りが 22 件通った。``--batch 1`` でも 1 件分の汚染は残る(0 にはできない ―
文章を変えずに誤りを混ぜることはできない)。

使い方::  python3 -B measure/false_pass_2026-10-14.py [--docs A,B] [--profiles P16,P17] [--tag x]
出力: fixtures/xbrl/p17/false_pass_2026-10-14<tag>.json
"""

import io
import json
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

from adapters.xbrl import extract as E  # noqa: E402
from adapters.xbrl import instance as I  # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V  # noqa: E402

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
OUT = os.path.join(ROOT, "fixtures", "xbrl", "p17")
BATCH = 25   # --batch で変える。**1 が正**(下の注)


def mdna_text(zb):
    inst = I.load_instance(zb)
    name = I.select_mdna(inst["textblocks"])
    return unicodedata.normalize("NFKC", I.strip_html(inst["textblocks"][name]))


def number_sites(text, profile):
    """engine と同じ順で、数の主張になる数の (id, 文番号, 文中の開始, 終了, 元の字, 値) を返す。
    (``recipes._build_raw_num_claims`` の除外と同じ条件で id を数える。)"""

    sentences = E.split_sentences(text, profile.paren_sentence)
    sites, n = [], 0
    for si, s in enumerate(sentences):
        for (a, b, signed, unit, prec) in E.iter_numbers(s):
            after = s[b:b + 3]
            around = s[max(0, a - 12):b + 4]
            if E.EXCLUDE_AFTER.match(after) or E.EXCLUDE_CONTEXT.search(around):
                continue
            n += 1
            sites.append({"id": "N%03d" % n, "si": si, "a": a, "b": b, "raw": s[a:b], "value": signed, "unit": unit})
    return sentences, sites


def _digits_part(raw):
    """raw(例 '2,523,449' / '27.6' / '△1,234')の数字部分の (前置き, 数字字列, 後置き)。"""

    i = 0
    while i < len(raw) and not raw[i].isdigit():
        i += 1
    j = len(raw)
    while j > i and not raw[j - 1].isdigit():
        j -= 1
    return raw[:i], raw[i:j], raw[j:]


def mutation_kind(claim_id):
    """**変え方は claim の id で決める。**(profile や並び順で変わらない ― profile 間で
    同じ文に同じ変え方が当たらないと、通した件数を比べられない。2026-10-14 に
    順番で割り振っていた版を直した: 170 件のうち同じ変え方だったのは 96 件だけだった。)
    id は ``N###`` / ``T###``。番号が偶数なら V1(10 倍)、奇数なら V2(末尾の桁 +1)。"""

    digits = "".join(ch for ch in claim_id if ch.isdigit())
    return "V1" if (int(digits or 0) % 2 == 0) else "V2"


def mutate(raw, how):
    pre, num, post = _digits_part(raw)
    if not num or not any(ch.isdigit() for ch in num):
        return None
    if how == "V1":  # 10 倍: 小数なら小数点を 1 つ右へ、整数なら末尾に 0
        if "." in num:
            ip, fp = num.split(".", 1)
            if len(fp) == 1:
                new = ip.replace(",", "") + fp
                new = "{:,}".format(int(new)) if "," in ip else new
            else:
                new = ip + fp[0] + "." + fp[1:]
        else:
            new = num + "0"
            if "," in num:
                new = "{:,}".format(int(num.replace(",", "") + "0"))
    else:  # V2: 末尾の桁を +1(9 なら 8)
        last = num[-1]
        rep = str((int(last) + 1) % 10) if last != "9" else "8"
        new = num[:-1] + rep
    if new == num:
        return None
    return pre + new + post


def expected_value(site, new_raw):
    s = site["raw"]
    vals = [v for (_a, _b, v, _u, _p) in E.iter_numbers(new_raw)]
    return vals[0] if len(vals) == 1 else None


def run_doc(doc, profile_name, zb, text0, kind=None, batch_size=None):
    profile = V.PROFILES[profile_name]
    base = VD.verify_document(zb, profile_name, text0)
    orig = VD.verify_document(zb, profile_name, None)
    sentences, sites = number_sites(text0, profile)
    by_id = {c["id"]: c for c in base["claims"]}
    # 土台の整合: 数の主張の id が engine と同じ並びか(値で突き合わせる)
    mismatched = [s["id"] for s in sites if s["id"] not in by_id or by_id[s["id"]].get("value") is None
                  or abs(by_id[s["id"]]["value"] - s["value"]) > 1e-6 * max(1.0, abs(s["value"]))]
    targets = [s for s in sites if s["id"] in by_id and by_id[s["id"]]["state"] == "GROUNDED" and s["id"] not in mismatched]
    rows = []
    # 1 文に 1 つずつ、BATCH 件ずつ変える
    pending = list(targets)
    while pending:
        batch, used_si = [], set()
        rest = []
        cap = batch_size or BATCH
        for s in pending:
            if len(batch) < cap and s["si"] not in used_si:
                batch.append(s); used_si.add(s["si"])
            else:
                rest.append(s)
        pending = rest
        new_sents = list(sentences)
        plan = []
        for s in batch:
            how = kind or mutation_kind(s["id"])
            new_raw = mutate(s["raw"], how)
            if new_raw is None:
                rows.append({"id": s["id"], "doc": doc, "how": how, "raw": s["raw"], "outcome": "unmutable"})
                continue
            exp = expected_value(s, new_raw)
            sent = new_sents[s["si"]]
            new_sents[s["si"]] = sent[:s["a"]] + new_raw + sent[s["b"]:]
            plan.append((s, how, new_raw, exp))
        if not plan:
            continue
        # 文を元の文章の位置で差し替える(文の切り出しは NFKC 済みの text0 の部分文字列)
        text = text0
        for (s, how, new_raw, exp) in sorted(plan, key=lambda t: -text0.find(sentences[t[0]["si"]])):
            pos = text.find(sentences[s["si"]])
            if pos < 0:
                rows.append({"id": s["id"], "doc": doc, "how": how, "raw": s["raw"], "outcome": "sentence_not_found"})
                continue
            text = text[:pos] + new_sents[s["si"]] + text[pos + len(sentences[s["si"]]):]
        out = VD.verify_document(zb, profile_name, text)
        got = {c["id"]: c for c in out["claims"]}
        for (s, how, new_raw, exp) in plan:
            c = got.get(s["id"])
            if c is None:
                outcome = "missing"
            elif exp is None or c.get("value") is None or abs(c["value"] - exp) > 1e-6 * max(1.0, abs(exp)):
                outcome = "id_shift"
            elif c["state"] == "GROUNDED":
                outcome = "PASSED"
            else:
                outcome = "detected:" + c["state"]
            rows.append({"id": s["id"], "doc": doc, "how": how, "raw": s["raw"], "new": new_raw, "outcome": outcome,
                         "base_pointer": by_id[s["id"]]["pointers"][:1], "after_pointer": (c or {}).get("pointers", [])[:1],
                         "span": s and sentences[s["si"]][max(0, s["a"] - 25):s["b"] + 10]})
    counts = {}
    for r in rows:
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    return {"doc": doc, "profile": profile_name, "kind": kind or "by_id", "batch": batch_size or BATCH, "baseline_claims": base["document"]["claims"],
            "original_claims": orig["document"]["claims"], "baseline_states": base["document"]["states"],
            "original_states": orig["document"]["states"], "sites": len(sites), "id_mismatch_in_baseline": len(mismatched),
            "targets": len(targets), "counts": counts, "rows": rows}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    docs = ["S100Z39P", "S100Z4N9", "S100Z4Q1"]
    profiles = ["P16", "P17"]
    kinds = ["V1", "V2"]
    batch_size = None
    tag = ""
    while argv:
        if argv[0] == "--docs":
            docs = argv[1].split(","); argv = argv[2:]
        elif argv[0] == "--profiles":
            profiles = argv[1].split(","); argv = argv[2:]
        elif argv[0] == "--batch":
            batch_size = int(argv[1]); argv = argv[2:]
        elif argv[0] == "--kinds":
            kinds = argv[1].split(","); argv = argv[2:]
        elif argv[0] == "--tag":
            tag = "_" + argv[1]; argv = argv[2:]
        else:
            raise SystemExit("unknown arg %r" % argv[0])
    rep = []
    for doc in docs:
        zb = open(os.path.join(CACHE, doc + ".zip"), "rb").read()
        text0 = mdna_text(zb)
        for pn in profiles:
            for kind in kinds:
                r = run_doc(doc, pn, zb, text0, None if kind == "by_id" else kind, batch_size)
                rep.append(r)
                print("%s %s %s targets %d -> %s" % (
                    doc, pn, kind, r["targets"], json.dumps(r["counts"], ensure_ascii=False)))
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "false_pass_2026-10-14%s.json" % tag)
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=1)
    print("->", p)


if __name__ == "__main__":
    main()
