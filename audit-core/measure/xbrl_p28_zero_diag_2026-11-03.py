# -*- coding: utf-8 -*-
u"""候補 0 の行の分類(0 件・少数は先に自分の欠陥を疑う)。封 docs/XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02.md の結果の便の追加(司令塔 2026-11-03)。

``fixtures/xbrl/p28/regress97_2026-11-02.json`` の「形が真の行」(42 行)の docID と id を入力に、cache の ZIP(読むだけ)を開いて 1 行ずつ上から順に 1 つへ分類し、
数と id の一覧を ``fixtures/xbrl/p28/zero_diag_2026-11-03.json`` に書く。記録に文・数の字・金額・span は入れない。engine は変えない。通信なし・0 USD。

    cd audit-core
    python3 measure/xbrl_p28_zero_diag_2026-11-03.py [--procs 4] [--out fixtures/xbrl/p28/zero_diag_2026-11-03.json]

分類(形が真の 42 行を上から順に 1 つ。候補 1 で決まった行は別立て「決まった」):
  (a) engine が P27 で GROUNDED(候補の数は数えるが決まる対象外)
  (b) 数の直後 6 字に「増」「減」(増加・減少・増益…を含む)、または claim の form が derived_value(増減の形)
  (c) 書類のどの context(member つき・別の期も含む)にも ``Other…`` の JPY の fact で engine の帯(``V.match_value``。claim の丸め方・桁)の中のものが無い
  (d) 帯の中の ``Other…`` の fact は在るが、member なし・同じ期のものが 0(member つきだけ / 別の期だけ / 両方 を数える)
  (e) 帯の中の member なし・同じ期の ``Other…`` の fact が 2 つ以上(保留)
  (f) その他(上に当たらない。id を列挙。member なし・同じ期がちょうど 1 つなのに決まっていない行もここ = engine との食い違いの検出)
実装の注(実装より先に決め、結果を見て変えない): 帯の判定は claim の ``unit_scale``・``claim_scale``・``rounding``・``magnitude_truncate`` から engine と同じ式(target = claim の数 × unit_scale)。
緩めた字の内訳: 97 書類の MD&A の文で ``その他[^。]{0,10}?[0-9][0-9,.]*(百万円|千円|円|億|万)`` に当たる件数を数え、封の形(shape が真)と
封の形でないもの(鉤括弧 / 「(前期」 / 「その他」の後に「の」以外が続く(9 字以上を含む) / 円族の数でない / その他)に分ける。封の形の行は増減の文かどうかも数える。
"""
from __future__ import print_function

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
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

from adapters.xbrl import vocabulary as V   # noqa: E402


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


E97 = load_module(os.path.join(HERE, "xbrl_p28_regress97_2026-11-02.py"), "p28_regress97_for_zero_diag")
D = E97.D

SEAL_REL = "docs/XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02.md"
SEAL_COMMIT = "c6cbfae"
IN_REL = "fixtures/xbrl/p28/regress97_2026-11-02.json"
OUT_REL = "fixtures/xbrl/p28/zero_diag_2026-11-03.json"
CATS = (u"(a) engine が P27 で GROUNDED", u"(b) 増減額の文", u"(c) どの context にも帯の中の Other が無い",
        u"(d) 帯の中の Other は在るが member なし・同じ期には無い", u"(e) member なし・同じ期に 2 つ以上(保留)", u"(f) その他")
DECIDED = u"決まった(候補 1)"
LOOSE_RE = re.compile(u"その他[^。]{0,10}?[0-9][0-9,\\.]*(百万円|千円|円|億|万)")
LOOSE_REASONS = (u"鉤括弧", u"「(前期」", u"「その他」の後に「の」以外が続く(9 字以上を含む)", u"円族の数でない", u"その他")
KEY_PATTERNS = D.KEY_PATTERNS


def sha256_file(p):
    return E97.sha256_file(p)


def is_other_jpy(f):
    return f["name"].split(":")[-1].startswith("Other") and bool(f["unit"]) and f["unit"].upper().startswith("JPY")


def classify_row(row, claim, facts, sentence_tail):
    u"""row = regress97 の形が真の行。claim = raw claim。返す: (分類, 数の辞書)。"""
    info = collections.OrderedDict()
    if row[u"決まった"]:
        return DECIDED, info
    if row[u"P27 の state"] == "GROUNDED":
        return CATS[0], info
    inc_dec = (u"増" in sentence_tail) or (u"減" in sentence_tail) or claim.get("form") == "derived_value"
    info[u"数の直後 6 字に増減"] = (u"増" in sentence_tail) or (u"減" in sentence_tail)
    info[u"form が derived_value"] = claim.get("form") == "derived_value"
    if inc_dec:
        return CATS[1], info
    target = claim["value"] * (claim.get("unit_scale") or 1.0)
    scale = claim["claim_scale"]
    rounding = claim.get("rounding")
    mt = bool(claim.get("magnitude_truncate"))
    want = "Prior1Year" if row[u"前期"] else "CurrentYear"
    band = [f for f in facts if is_other_jpy(f) and V.match_value(f["value"], target, scale, rounding, mt)]
    same = [f for f in band if f["context"].startswith(want) and "_" not in f["context"]]
    member_only = [f for f in band if f["context"].startswith(want) and "_" in f["context"]]
    other_period = [f for f in band if not f["context"].startswith(want)]
    info[u"帯の中の Other の fact(全部)"] = len(band)
    info[u"同じ期・member なし"] = len(same)
    info[u"同じ期・member つき"] = len(member_only)
    info[u"別の期"] = len(other_period)
    if not band:
        return CATS[2], info
    if not same:
        return CATS[3], info
    if len(same) >= 2:
        return CATS[4], info
    return CATS[5], info


def loose_reason(s, mm, prof, R):
    nums = [(a, b, u) for (a, b, _v, u, _p) in R._numbers_of(prof, s) if mm.start() <= a <= mm.end()]
    money = [(a, b, u) for (a, b, u) in nums if u in V.UNIT_SCALE]
    if not money:
        return u"円族の数でない"
    a = money[0][0]
    w = s[:a].rstrip(u"::、はがをでに 　")
    if w.endswith((u"」", u"』")):
        return u"鉤括弧"
    if w.endswith((u"(前期", u"(前期")):
        return u"「(前期」"
    if re.search(u"その他", w[-14:]):
        return u"「その他」の後に「の」以外が続く(9 字以上を含む)"
    return u"その他"


def doc_job(args):
    doc, zpath, expect_sha, rows = args
    import hashlib
    from adapters.xbrl import extract as E
    from adapters.xbrl import instance as I
    from adapters.xbrl import recipes as R
    with io.open(zpath, "rb") as fh:
        zb = fh.read()
    if hashlib.sha256(zb).hexdigest() != expect_sha:
        raise SystemExit(u"**ZIP の sha256 が記録と違う: %s。止める**" % doc)
    prof = V.PROFILES["P28"]
    inst = I.load_instance(zb)
    tbs = inst["textblocks"]
    mdna = I.select_mdna(tbs)
    text = I.strip_html(tbs[mdna]) if mdna else ""
    sents = E.split_sentences(text, prof.paren_sentence)
    nums, _t = R.build_raw_claims(zb, prof)
    byid = dict((c["id"], c) for c in nums)
    out_rows = []
    for row in rows:
        c = byid[row[u"id"]]
        s = sents[c["sentence"]]
        a = c["pos"]
        b = [b2 for (a2, b2, _v, _u, _p) in R._numbers_of(prof, s) if a2 == a][0]
        cat, info = classify_row(row, c, inst["facts"], s[b:b + 6])
        out_rows.append(collections.OrderedDict([(u"docID", doc), (u"id", row[u"id"]), (u"分類", cat), (u"内訳", info), (u"P27 の state", row[u"P27 の state"]), (u"候補", row[u"候補"])]))
    loose = collections.Counter()
    for s in sents:
        for mm in LOOSE_RE.finditer(s):
            hit = False
            tail = u""
            for (a, b, _v, u, _p) in R._numbers_of(prof, s):
                if u in V.UNIT_SCALE and mm.start() <= a <= mm.end() and R._other_subject_shape_2026_11_02(prof, s, a)[0]:
                    hit = True
                    tail = s[b:b + 6]
                    break
            if hit:
                loose[u"封の形"] += 1
                loose[u"封の形・数の直後 6 字に増減" if (u"増" in tail or u"減" in tail) else u"封の形・増減でない"] += 1
            else:
                loose[u"封の形でない"] += 1
                loose[u"封の形でない・" + loose_reason(s, mm, prof, R)] += 1
    return {u"doc": doc, u"rows": out_rows, u"loose": dict(loose), u"loose 件数": sum(1 for s in sents for _ in LOOSE_RE.finditer(s))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise E97.Stop(u"**出力が既に在る。測り直さない。止める**")
    P = E97.prec()
    names_before = collections.OrderedDict((k, P.names_sha(v)) for k, v in E97.CACHES.items())
    in_path = os.path.join(ROOT, IN_REL)
    with io.open(in_path, encoding="utf-8") as fh:
        rec97 = json.load(fh)
    shape = rec97[u"形が真の行"]
    by_doc = collections.OrderedDict()
    for r in shape:
        by_doc.setdefault(r[u"docID"], []).append(r)
    jobs0, _i67, _i30 = E97.make_jobs(("P28",))
    jobs = [(j[0], j[4], j[2], by_doc.get(j[0], [])) for j in jobs0]
    res = E97.run_pool(doc_job, jobs, a.procs)
    names_after = collections.OrderedDict((k, P.names_sha(v)) for k, v in E97.CACHES.items())
    if names_before != names_after:
        raise E97.Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rows = [r for x in res for r in x[u"rows"]]
    cnt = collections.OrderedDict((c, sum(1 for r in rows if r[u"分類"] == c)) for c in CATS + (DECIDED,))
    zero_rows = [r for r in rows if r[u"候補"] == 0]
    cnt0 = collections.OrderedDict((c, sum(1 for r in zero_rows if r[u"分類"] == c)) for c in CATS)
    loose = collections.Counter()
    for x in res:
        loose.update(x[u"loose"])
    d_member = [r for r in rows if r[u"分類"] == CATS[3]]
    T = collections.OrderedDict()
    T[u"形が真の行"] = len(rows)
    T[u"分類(形が真の 42 行。上から順に 1 つ)"] = cnt
    T[u"候補 0 の行"] = len(zero_rows)
    T[u"候補 0 の行の分類"] = cnt0
    T[u"各分類の id"] = collections.OrderedDict((c, [[r[u"docID"], r[u"id"]] for r in rows if r[u"分類"] == c]) for c in cnt)
    T[u"(d) の内訳"] = collections.OrderedDict([(u"member つきだけ(別の期なし)", sum(1 for r in d_member if r[u"内訳"][u"同じ期・member つき"] and not r[u"内訳"][u"別の期"])),
                                              (u"別の期だけ(member つきなし)", sum(1 for r in d_member if r[u"内訳"][u"別の期"] and not r[u"内訳"][u"同じ期・member つき"])),
                                              (u"両方", sum(1 for r in d_member if r[u"内訳"][u"別の期"] and r[u"内訳"][u"同じ期・member つき"]))])
    T[u"(b) の内訳"] = collections.OrderedDict([(u"数の直後 6 字に増減", sum(1 for r in rows if r[u"分類"] == CATS[1] and r[u"内訳"][u"数の直後 6 字に増減"])),
                                              (u"form が derived_value", sum(1 for r in rows if r[u"分類"] == CATS[1] and r[u"内訳"][u"form が derived_value"]))])
    T[u"緩めた字で数えた件数(97 書類の MD&A)"] = sum(x[u"loose 件数"] for x in res)
    T[u"緩めた字の内訳"] = collections.OrderedDict(sorted(loose.items()))
    rec = collections.OrderedDict()
    rec[u"注意"] = u"候補 0 の行の 1 行ごとの分類。文・数の字・金額は入れない。97 書類の手元の原文。engine は変えていない。"
    rec[u"封"] = collections.OrderedDict([(u"file", SEAL_REL), (u"commit", SEAL_COMMIT)])
    rec[u"HEAD の commit"] = E97.git_head()
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"入力の sha256"] = collections.OrderedDict([(IN_REL, sha256_file(in_path)), (E97.PRECEDENT_REL, sha256_file(os.path.join(ROOT, E97.PRECEDENT_REL)))])
    rec[u"cache の前後"] = collections.OrderedDict([(u"前", names_before), (u"後", names_after), (u"変化なし", names_before == names_after)])
    rec[u"集計"] = T
    rec[u"行"] = [collections.OrderedDict((k, v) for k, v in r.items()) for r in rows]
    rec[u"limits"] = [u"分類は上から順に 1 つ。(b) は数の直後 6 字の字面と form で見るので、増減の語が 6 字より後ろにある文は (b) に入らない",
                     u"帯の判定は engine と同じ式(claim の丸め方・桁)。member つき・別の期の fact は数えるだけで結ばない", u"緩めた字の内訳は文の字面の分類で、正しさの判定ではない"]
    rec[u"key_leaks"] = [p for p in KEY_PATTERNS if re.search(p, json.dumps(rec, ensure_ascii=False))]
    if rec[u"key_leaks"]:
        raise E97.Stop(u"記録に鍵が入った")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + u"\n")
    print(u"-> %s" % a.out)
    for k in (u"形が真の行", u"分類(形が真の 42 行。上から順に 1 つ)", u"候補 0 の行", u"候補 0 の行の分類", u"(b) の内訳", u"(d) の内訳", u"緩めた字で数えた件数(97 書類の MD&A)", u"緩めた字の内訳"):
        print(k, json.dumps(T[k], ensure_ascii=False))


if __name__ == "__main__":
    main()
