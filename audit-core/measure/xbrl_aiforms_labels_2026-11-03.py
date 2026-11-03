# -*- coding: utf-8 -*-
u"""封 docs/XBRL_AI_FORMS_SEAL_2026-11-03.md §0-2 の 6 (a)・§1-2 ― 盲検の席の札の答えを読んで検査し、札の記録に書く。**0 USD・通信なし・鍵は読まない。**

    python3 measure/xbrl_aiforms_labels_2026-11-03.py [--out fixtures/xbrl/aiforms/labels_2026-11-03.json]

入力(repo の外 ``~/.cache/audit-core/aiforms-2026-11-03/dossiers/``): 札付けの束 ``<鍵>.json``(判定の script が作る)・対応表 ``index.json``・
席の答え ``<鍵>.seat1.json``(全部の本)と ``<鍵>.seat2.json``(2 席目を立てる 32 本)。席の答えの形は run script の ``LABELLER_PROMPT`` の字::

    {"札": [{"id": "N001", "札": "真|偽|判定不能", "根拠": "<1〜2 文>", "誤りの型": "<型>|null", "確信": "高|中|低"}, ...]}

検査(1 つでも外れれば止める。席のやり直しの理由を累積して渡せるよう、外れの件数と本の鍵を出す):
  - 束の claim の id と札が 1 対 1(欠け・余り・重複なし)。
  - 札は 真 / 偽 / 判定不能。誤りの型は 札が偽のときだけ ``ERROR_TYPES`` の 1 つ、そのほかは null。確信は 高 / 中 / 低。根拠は空でない文字列。
記録に書くのは id・札・誤りの型・確信・根拠の要素名(根拠の自由文のうち、fact の表に在る要素の名前に当たる字だけを取り出す。自由文そのものは書かない)。
**本の札は 1 席目の答え。** 2 席目は一致率(札が同じ claim の率)を測るためだけに使い、札には使わない(封に無い決め ― 報告に書く)。
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
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GEN = load_module("xbrl_aiforms_gen_2026-11-03.py", "aiforms_gen_for_labels")
RUN = load_module("xbrl_aiforms_run_2026-11-03.py", "aiforms_run_for_labels")

Stop = GEN.Stop
LABELS_REL = GEN.REC_DIR_REL + "/labels_2026-11-03.json"
FORBIDDEN_KEYS = (u"根拠", u"理由", u"文", u"span", u"value", u"text")
QNAME_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_\-]*(?::[A-Za-z0-9_\-]+)?")
TABLE_QNAME_RE = re.compile(r"^\| ([^|]+?) \|", re.M)


def fact_names(facts_path):
    u"""fact の表(``facts/<docID>.md``)の 1 列目(要素名)の集合。"""
    with io.open(facts_path, encoding="utf-8") as fh:
        text = fh.read()
    names = set()
    for m in TABLE_QNAME_RE.finditer(text):
        n = m.group(1).strip()
        if ":" in n:
            names.add(n)
    return names


def basis_elements(basis, qnames):
    u"""根拠の自由文のうち、fact の表に在る要素の名前に当たる字。qname そのものか、表の中で局所名が 1 つに決まる局所名。(昇順の列)"""
    locals_ = collections.defaultdict(set)
    for q in qnames:
        locals_[q.split(":")[-1]].add(q)
    found = set()
    for tok in QNAME_TOKEN.findall(basis):
        if tok in qnames:
            found.add(tok)
        elif ":" not in tok and len(locals_.get(tok, ())) == 1:
            found.add(next(iter(locals_[tok])))
    return sorted(found)


def validate_seat(d, want_ids, key, seat):
    u"""席の答え d を検査して {id: (札, 誤りの型, 確信, 根拠)} を返す。外れは Stop(鍵と席の名・件数だけ。自由文は出さない)。"""
    labels = d.get(u"札") if isinstance(d, dict) else None
    if not isinstance(labels, list):
        raise Stop(u"**%s %s: 札の列が無い。止める**" % (key, seat))
    out, problems = {}, []
    for lab in labels:
        cid = lab.get("id") if isinstance(lab, dict) else None
        if cid in out:
            problems.append(u"同じ id が 2 回")
            continue
        if not isinstance(lab, dict):
            problems.append(u"札の行が辞書でない")
            continue
        word, etype, conf, basis = lab.get(u"札"), lab.get(u"誤りの型"), lab.get(u"確信"), lab.get(u"根拠")
        if word not in RUN.LABEL_WORDS:
            problems.append(u"札が語でない")
        if word == u"偽":
            if etype not in RUN.ERROR_TYPES:
                problems.append(u"札が偽なのに誤りの型が型の語でない")
        elif etype is not None:
            problems.append(u"札が偽でないのに誤りの型がある")
        if conf not in RUN.CONFIDENCE:
            problems.append(u"確信が語でない")
        if not isinstance(basis, str) or not basis.strip():
            problems.append(u"根拠が無い")
        out[cid] = (word, etype, conf, basis if isinstance(basis, str) else u"")
    if set(out) != set(want_ids):
        problems.append(u"id と札が 1 対 1 でない(束 %d・札 %d・足りない %d・余り %d)" % (
            len(want_ids), len(out), len(set(want_ids) - set(out)), len(set(out) - set(want_ids))))
    if problems:
        raise Stop(u"**%s %s: %s。止める**" % (key, seat, u" / ".join(sorted(set(problems)))))
    return out


def tally_labels(books):
    u"""本の札(1 席目)の分布。全体と 形 × model。"""
    def cell(rows):
        c = collections.Counter(r[1] for r in rows)
        n = len(rows)
        return collections.OrderedDict([(u"数の claim", n)] + [(w, collections.OrderedDict([(u"件", c.get(w, 0)), (u"率", round(100.0 * c.get(w, 0) / n, 1) if n else None)])) for w in RUN.LABEL_WORDS])
    allrows = [r for b in books for r in b[u"札"]]
    out = collections.OrderedDict([(u"全体", cell(allrows))])
    by = collections.OrderedDict()
    for form in GEN.FORMS:
        for model in GEN.MODELS:
            rows = [r for b in books if b[u"form"] == form and b[u"model"] == model for r in b[u"札"]]
            by[u"%s×%s" % (form, GEN.MODEL_TAG[model])] = cell(rows)
    out[u"形 × model"] = by
    return out


def agreement(books):
    u"""2 席目の本での札の一致率(札の語が同じ claim の率)。"""
    rows = [(r[1], s2) for b in books if b.get(u"2 席目") for r, s2 in zip(b[u"札"], [x[1] for x in b[u"2 席目"]])]
    n = len(rows)
    same = sum(1 for a, b in rows if a == b)
    conf = collections.Counter((a, b) for a, b in rows)
    return collections.OrderedDict([(u"2 席目を立てた本", sum(1 for b in books if b.get(u"2 席目"))), (u"claim", n), (u"一致", same),
                                    (u"一致率", round(100.0 * same / n, 1) if n else None),
                                    (u"1 席目 → 2 席目の札の組", collections.OrderedDict((u"%s→%s" % k, v) for k, v in sorted(conf.items())))])


def run(root=ROOT, new_cache=None, claims_path=None, out=None, key_value=None, say=print):
    new_cache = new_cache or GEN.NEW_CACHE
    claims_path = claims_path or os.path.join(root, RUN.CLAIMS_REL)
    out = out or os.path.join(root, LABELS_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    claims = GEN.jload(claims_path)
    if claims[u"札付けの席の指示文の sha256"] != RUN.LABELLER_PROMPT_SHA256:
        raise Stop(u"**札付けの席の指示文の sha256 が判定の記録と違う。止める**")
    ddir = os.path.join(new_cache, "dossiers")
    s2set = set(claims[u"2 席目を立てる本"])
    books, missing = [], []
    for b in claims[u"本"]:
        if b.get(u"欠け"):
            continue
        key, name = b[u"札付けの束の鍵"], b[u"name"]
        dossier = GEN.jload(os.path.join(ddir, key + ".json"))
        ids = [c["id"] for c in dossier["claims"]]
        qn = fact_names(dossier["facts"])
        p1 = os.path.join(ddir, key + ".seat1.json")
        if not os.path.exists(p1):
            missing.append(key + u" seat1")
            continue
        s1 = validate_seat(GEN.jload(p1), ids, key, u"seat1")
        rec = collections.OrderedDict([(u"name", name), (u"docID", b[u"docID"]), (u"form", b[u"form"]), (u"model", b[u"model"]), (u"writer", b[u"writer"]),
                                       (u"札付けの束の鍵", key), (u"seat1 の sha256", GEN.sha256_file(p1))])
        rec[u"札"] = [[cid, s1[cid][0], s1[cid][1], s1[cid][2], basis_elements(s1[cid][3], qn)] for cid in ids]
        if name in s2set:
            p2 = os.path.join(ddir, key + ".seat2.json")
            if not os.path.exists(p2):
                missing.append(key + u" seat2")
                continue
            s2 = validate_seat(GEN.jload(p2), ids, key, u"seat2")
            rec[u"seat2 の sha256"] = GEN.sha256_file(p2)
            rec[u"2 席目"] = [[cid, s2[cid][0], s2[cid][1], s2[cid][2], basis_elements(s2[cid][3], qn)] for cid in ids]
        books.append(rec)
    if missing:
        raise Stop(u"**席の答えが足りない(%d 件): %s。止める**" % (len(missing), u", ".join(missing[:8])))
    rec = collections.OrderedDict([
        (u"seal", GEN.SEAL_REL), (u"封の commit", GEN.SEAL_COMMIT), (u"step", u"AI の形 4 × model 2 ― 盲検の席の札(0 USD)"),
        (u"HEAD の commit", GEN.git_head(os.path.dirname(root))), (u"この script の sha256", GEN.sha256_file(os.path.abspath(__file__))),
        (u"判定の記録の sha256", GEN.sha256_file(claims_path)), (u"札付けの席の指示文の sha256", RUN.LABELLER_PROMPT_SHA256),
        (u"欄", collections.OrderedDict([(u"札", [u"id", u"札", u"誤りの型", u"確信", u"根拠の要素名"]),
                                        (u"本の札", u"1 席目の答え。2 席目は一致率だけに使う")])),
        (u"語", collections.OrderedDict([(u"札", list(RUN.LABEL_WORDS)), (u"誤りの型", list(RUN.ERROR_TYPES)), (u"確信", list(RUN.CONFIDENCE))])),
        (u"集計", collections.OrderedDict([(u"札の分布", tally_labels(books)), (u"2 席目との一致", agreement(books))])),
        (u"本", books),
        (u"key_leaks", []),
    ])
    text = json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    leaks = GEN.key_leaks(text, key_value, long_alnum=False)
    bad = [k for k in RUN.walk_keys(rec) if k in FORBIDDEN_KEYS]
    if leaks or bad:
        raise Stop(u"**記録に鍵らしい字か repo へ入れない欄がある。止める**")
    GEN.write_text(out, text)
    say(u"-> %s(本 %d)" % (out, len(books)))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    run(root=a.root, out=a.out)


if __name__ == "__main__":
    main()
