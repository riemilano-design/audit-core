# -*- coding: utf-8 -*-
u"""儀式の注入 243 件を P27E と P28E で走らせる(封 docs/XBRL_P28E_SEAL_2026-11-03.md §3-3・§5)。

``measure/ritual_2026-10-20.py`` の ``check_labels``・``build`` を importlib で読んで使う(写さない・編集しない。注入の仕掛けは持たない ― 儀式の仕掛けを使う側)。
同梱の AI の文の書類(ZIP)に、1 文に 1 つずつ数を変える注入(V1 = 最小の桁の 1 字 / V2 = 値を ±1 最小単位)を入れ、P27E と P28E のそれぞれで 通した(GROUNDED のまま)/ 止めた(VALUE_MISMATCH)を数える。
既定 P27 の記録 ``fixtures/xbrl/ritual_2026-10-20.json`` は採り直さない。ラベル file(cache。repo の外)が無ければ止める。通信しない・0 USD・LLM を呼ばない。

    python3 measure/xbrl_p28e_ritual_2026-11-03.py [--out fixtures/xbrl/p28e/ritual_2026-11-03.json]

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- E-7 = P27E の 通した が 2〜4。E-8 = P28E の 通した が P27E の 通した を超えない(1 件でも増えたら、その id と要素を記録)。E-9 = P28E の 止めた(detected:VALUE_MISMATCH)が P27E 以上。
  判定は profile ごとの全部の注入(profile ごとに注入の対象 = その profile で素の書類が GROUNDED の site)の件数で求める(封の字)。注入の対象の集合が 2 つの profile で違う場合は、
  その id を記録に書き、2 つの profile に共通の id だけで数えた件数も参考に書く(判定には使わない)。
- 記録に注入の字(元の字・後の字・文脈)は入れない。注入ごとの id・型・2 つの profile の結果だけ。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RT = load_module(os.path.join(HERE, "ritual_2026-10-20.py"), "ritual_for_p28e")

SEAL_REL = "docs/XBRL_P28E_SEAL_2026-11-03.md"
SEAL_COMMIT = "7bfad77"
OUT_REL = "fixtures/xbrl/p28e/ritual_2026-11-03.json"
PROFILES = ("P27E", "P28E")
PASSED, DETECTED = "PASSED", "detected:VALUE_MISMATCH"
BOUND_E7 = (2, 4)
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
KEY_PATTERNS = (r"sk-[A-Za-z0-9_\-]{10,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{20,}", r"xox[baprs]-[A-Za-z0-9\-]{10,}", r"-----BEGIN", r"Bearer [A-Za-z0-9._\-]{16,}", r"AIza[0-9A-Za-z_\-]{30,}")


class Stop(SystemExit):
    pass


def sha256_file(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def element_of(pointer):
    if not pointer:
        return None
    m = re.match(r"^xbrl:([A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+)@", pointer)
    return m.group(1).split(":")[-1] if m else None


def per_profile(rec):
    rows = collections.OrderedDict((x[u"id"], x) for x in rec[u"注入の一覧"])
    passed = [x for x in rec[u"注入の一覧"] if x[u"結果"] == PASSED]
    detected = [x for x in rec[u"注入の一覧"] if x[u"結果"] == DETECTED]
    other = collections.Counter(x[u"結果"] for x in rec[u"注入の一覧"] if x[u"結果"] not in (PASSED, DETECTED))
    return rows, passed, detected, other


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise Stop(u"**出力が既に在る。測り直さない。止める**")
    label_shas, why = RT.check_labels()
    if label_shas is None:
        raise Stop(u"**ラベル file が使えない: %s。止める**" % why)
    zpath = os.path.join(ROOT, RT.ZIP_REL)
    with io.open(zpath, "rb") as fh:
        zb = fh.read()
    if hashlib.sha256(zb).hexdigest() != RT.ZIP_SHA256 or len(zb) != RT.ZIP_BYTES:
        raise Stop(u"**同梱の ZIP の sha256 か大きさが儀式の封と違う。止める**")
    recs = collections.OrderedDict((p, RT.build(zb, p, label_shas)) for p in PROFILES)
    info = collections.OrderedDict((p, per_profile(recs[p])) for p in PROFILES)
    ids = collections.OrderedDict((p, set(info[p][0])) for p in PROFILES)
    common = sorted(ids["P27E"] & ids["P28E"])
    summary = collections.OrderedDict()
    for p in PROFILES:
        rows, passed, detected, other = info[p]
        summary[p] = collections.OrderedDict([
            (u"注入の対象", len(rows)), (u"通した", len(passed)), (u"止めた(VALUE_MISMATCH)", len(detected)), (u"止めた でも 通した でもない結果", collections.OrderedDict(sorted(other.items()))),
            (u"素の書類の state の分布", recs[p][u"素の書類"][u"state の分布"]), (u"素の書類の claim", recs[p][u"素の書類"][u"claim"]),
            (u"型別", recs[p][u"型別"]), (u"通した の分け方", collections.OrderedDict((c, v[u"件"]) for c, v in recs[p][u"通した の分け方"].items())),
            (u"通した のうち参照先が動いた", recs[p][u"通した のうち参照先が動いた(注入の前後で GROUNDED の参照先が違う)"]),
            (u"通した の id", [x[u"id"] for x in passed])])
    s27, s28 = summary["P27E"], summary["P28E"]
    only28 = sorted(ids["P28E"] - ids["P27E"])
    only27 = sorted(ids["P27E"] - ids["P28E"])
    cmp_rows = []
    for i in sorted(ids["P27E"] | ids["P28E"]):
        r27, r28 = info["P27E"][0].get(i), info["P28E"][0].get(i)
        cmp_rows.append(collections.OrderedDict([(u"id", i), (u"型", (r28 or r27)[u"型"]), (u"P27E の結果", r27[u"結果"] if r27 else None), (u"P28E の結果", r28[u"結果"] if r28 else None),
                                              (u"P28E の参照先(注入前)の要素", element_of(r28.get(u"参照先(注入前)")) if r28 else None),
                                              (u"P28E の参照先(注入後)の要素", element_of(r28.get(u"参照先(注入後)")) if r28 else None),
                                              (u"P28E の分類(通した行のみ)", r28.get(u"分類") if r28 else None)]))
    common_pass = collections.OrderedDict((p, sum(1 for i in common if info[p][0][i][u"結果"] == PASSED)) for p in PROFILES)
    common_det = collections.OrderedDict((p, sum(1 for i in common if info[p][0][i][u"結果"] == DETECTED)) for p in PROFILES)
    passed28_not27 = [i for i in sorted(ids["P28E"]) if info["P28E"][0][i][u"結果"] == PASSED and not (i in info["P27E"][0] and info["P27E"][0][i][u"結果"] == PASSED)]
    J = collections.OrderedDict()
    J["E-7"] = bool(BOUND_E7[0] <= s27[u"通した"] <= BOUND_E7[1])
    J["E-8"] = bool(s28[u"通した"] <= s27[u"通した"])
    J["E-9"] = bool(s28[u"止めた(VALUE_MISMATCH)"] >= s27[u"止めた(VALUE_MISMATCH)"])
    judged = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    judged["E-10"] = u"判定しない"
    out = collections.OrderedDict()
    out[u"注意"] = u"同梱の AI の文の書類(1 書類・243 件前後の注入)を P27E と P28E で走らせた記録。外部の数の実際の分布ではない。注入の字は入れない。"
    out[u"封"] = collections.OrderedDict([(u"file", SEAL_REL), (u"commit", SEAL_COMMIT)])
    out[u"HEAD の commit"] = RT.git_head()
    out[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    out[u"儀式の script の sha256"] = sha256_file(os.path.join(HERE, "ritual_2026-10-20.py"))
    out[u"入力"] = collections.OrderedDict([(u"path", RT.ZIP_REL), (u"sha256", hashlib.sha256(zb).hexdigest()), (u"bytes", len(zb)), (u"profile", list(PROFILES))])
    bundle, n_files = RT.engine_bundle_sha256()
    out[u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く)"] = bundle
    out[u"engine の file 数"] = n_files
    out[u"ラベル 2 file の sha256(起動時に照合)"] = label_shas
    out[u"鍵の名前の有無(値は読まない)"] = collections.OrderedDict((k, k in os.environ) for k in RT.KEY_NAMES)
    out[u"profile ごとの集計"] = summary
    out[u"注入の対象の集合"] = collections.OrderedDict([(u"2 つの profile に共通の id", len(common)), (u"P28E だけの id", only28), (u"P27E だけの id", only27)])
    out[u"共通の id だけで数えた件数(参考。判定に使わない)"] = collections.OrderedDict([(u"通した", common_pass), (u"止めた(VALUE_MISMATCH)", common_det)])
    out[u"P28E で通して P27E で通さなかった id(E-8 の外れの場合に見る)"] = [collections.OrderedDict([(u"id", i), (u"P28E の参照先(注入前)の要素", element_of(info["P28E"][0][i].get(u"参照先(注入前)"))),
                                                                                          (u"P28E の参照先(注入後)の要素", element_of(info["P28E"][0][i].get(u"参照先(注入後)")))]) for i in passed28_not27]
    out[u"注入ごとの結果"] = cmp_rows
    out[u"予測の判定"] = judged
    out[u"限界"] = [u"1 書類・243 件前後の注入。外部の数の実際の分布ではない。E-8 が当たっても「偽の一致が無い」証拠は 1 書類の範囲",
                  u"engine の変更は本便の vocabulary.py への挿入だけ。既定は P27 のまま"]
    text = json.dumps(out, ensure_ascii=False)
    out[u"key_leaks"] = [p for p in KEY_PATTERNS if re.search(p, text)]
    if out[u"key_leaks"] or DOCID_RE.search(text):
        raise Stop(u"記録に鍵か docID が入った")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(out, ensure_ascii=False, indent=1) + u"\n")
    print(u"-> %s" % a.out)
    print(json.dumps(judged, ensure_ascii=False))
    for p in PROFILES:
        print(p, json.dumps(dict((k, v) for k, v in summary[p].items() if k in (u"注入の対象", u"通した", u"止めた(VALUE_MISMATCH)", u"止めた でも 通した でもない結果", u"通した の id", u"素の書類の state の分布")), ensure_ascii=False))
    print(u"共通 %d・P28E だけ %s・P27E だけ %s" % (len(common), only28, only27))


if __name__ == "__main__":
    main()
