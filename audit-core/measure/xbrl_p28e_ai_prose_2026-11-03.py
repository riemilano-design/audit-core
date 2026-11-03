# -*- coding: utf-8 -*-
u"""AI の文 1 書類を P27E・P28E(・P28)で再判定する(封 docs/XBRL_P28E_SEAL_2026-11-03.md §3-1・§5)。

同梱の AI の文の書類(ZIP)を ``adapters.xbrl.verify_document`` で P27E・P28E・P28 の 3 つの profile で判定し、行の対応・形が真の行・動いた行・E-1〜E-4 の判定を記録に書く。
前の便の ``measure/xbrl_p28_ai_prose_2026-11-02.py`` を importlib で読み、その関数(材料の確認・ラベル file の確認・engine の束・prov_map・scrub・dump_no_engine)を使う(写さない・編集しない)。
標準ラベルは cache に在り sha256 が名簿と合うときだけ走る。通信しない・0 USD・LLM を呼ばない。

    python3 measure/xbrl_p28e_ai_prose_2026-11-03.py [--out fixtures/xbrl/p28e/ai_prose_2026-11-03.json]

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- E-1 の「HEAD a5d18e6 の engine と byte 一致」は、``git archive a5d18e6 audit-core/adapters audit-core/core`` を TMPDIR に取り出し(blob と byte 一致を確かめ)、同じ script を別の process で
  ``--dump-only`` で走らせて P27E(と P28)の出力(``sort_keys`` の JSON。``engine`` の欄を除く)の sha256 を得て比べる。P27E の 4 state が 340・15・33・24 であることも求める。
  さらに P27E の claims(docID を <docID> に置換)が ``fixtures/xbrl/entry_output_ai_prose_p27e_2026-11-02.json`` の claims と欄ごとに一致することも求める。
- E-2 の「state が違う行」は P28E と P28 で ``state`` が違う行。参考に state・reason・pointers・recomputed のどれかが違う行も数える(判定は state)。
- E-3 の動いた行 = P27E と P28E で state・reason・pointers・recomputed のどれかが違う行。決まった行 = provenance の欄 ``other_subject_2026_11_02`` の 決まった が真の行。
- E-4 の「形が偽の行」 = P28E の provenance に欄が無い claim。その行で state・reason・pointers が P27E と違う行を数える。P27E で GROUNDED の行は P28E でも state と pointers が同じであること。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# 前の便の script を先に読む(P28_ENGINE_ROOT が在れば、その engine を sys.path の先頭に置く。比べる側の process で使う)
D = load_module(os.path.join(HERE, "xbrl_p28_ai_prose_2026-11-02.py"), "p28_ai_prose_for_p28e")
VD, V = D.VD, D.V

SEAL_REL = "docs/XBRL_P28E_SEAL_2026-11-03.md"
SEAL_COMMIT = "7bfad77"
BASELINE_COMMIT = "a5d18e6"
OUT_REL = "fixtures/xbrl/p28e/ai_prose_2026-11-03.json"
ENTRY_REL = "fixtures/xbrl/p28e/entry_output_ai_prose_p28e_2026-11-03.json"
PROFILES = ("P27E", "P28E", "P28")
KEY = D.KEY
STATES = D.STATES
MATERIALS = collections.OrderedDict(list(D.MATERIALS.items()) + [
    ("entry_p27e", ("fixtures/xbrl/entry_output_ai_prose_p27e_2026-11-02.json", None)),
    ("p28_record", ("fixtures/xbrl/p28/ai_prose_2026-11-02.json", None)),
])
#: 封 §3-1(実装より先に固定)
EXPECT_P27E = collections.OrderedDict([("GROUNDED", 340), ("VALUE_MISMATCH", 15), ("UNVERIFIABLE", 33), ("POINTER_NOT_FOUND", 24)])
EXPECT_P28E = collections.OrderedDict([("GROUNDED", 347), ("VALUE_MISMATCH", 12), ("UNVERIFIABLE", 33), ("POINTER_NOT_FOUND", 20)])
EXPECT_IDS = ["N080", "N081", "N144", "N145", "N213", "N290", "N299"]
EXPECT_DIRECTIONS = collections.OrderedDict([("POINTER_NOT_FOUND → GROUNDED", 4), ("VALUE_MISMATCH → GROUNDED", 3)])


def fields(c):
    return (c["state"], c["reason"], tuple(c["pointers"]), c["recomputed"])


def baseline_dump(work, zpath):
    u"""HEAD の engine を git archive で取り出し、別の process で P27E と P28 の出力の sha256 を得る。"""
    base = os.path.join(work, "baseline_engine")
    os.makedirs(base)
    arc = subprocess.run(["git", "-C", REPO, "archive", BASELINE_COMMIT, "audit-core/adapters", "audit-core/core"], stdout=subprocess.PIPE, check=True)
    subprocess.run(["tar", "-x", "-C", base], input=arc.stdout, check=True)
    root = os.path.join(base, "audit-core")
    files = collections.OrderedDict()
    for rel in ["adapters/xbrl/%s" % f for f in sorted(os.listdir(os.path.join(root, "adapters", "xbrl"))) if f.endswith(".py")]:
        blob = subprocess.run(["git", "-C", REPO, "show", "%s:audit-core/%s" % (BASELINE_COMMIT, rel)], stdout=subprocess.PIPE, check=True).stdout
        with io.open(os.path.join(root, rel), "rb") as fh:
            if fh.read() != blob:
                raise D.Stop("**取り出した写しが commit の blob と違う: %s。止める**" % rel)
        files[rel] = D.sha_bytes(blob)
    out_json = os.path.join(work, "baseline_dump.json")
    env = dict(os.environ, P28_ENGINE_ROOT=root)
    subprocess.run([sys.executable, os.path.abspath(__file__), "--dump-only", "--zip", zpath, "--out", out_json], env=env, check=True)
    return D.jload(out_json), files


def build_rows(outs, provs, labels):
    a, b, c28 = outs["P27E"]["claims"], outs["P28E"]["claims"], outs["P28"]["claims"]
    rows = []
    for x, y, z in zip(a, b, c28):
        cid = y["id"]
        o = provs["P28E"][cid]["other"]
        pb = D.pointer_parts(y["pointers"])
        r = collections.OrderedDict()
        r["id"] = cid
        r["同じ位置で id と(文の抜粋・数・単位)の鍵が 3 profile で同じ"] = bool(x["id"] == y["id"] == z["id"] and D.row_key(x) == D.row_key(y) == D.row_key(z))
        r["P27E の state"], r["P27E の reason"] = x["state"], x["reason"]
        r["P28E の state"], r["P28E の reason"] = y["state"], y["reason"]
        r["P28 の state"] = z["state"]
        r["P27E → P28E で動いた"] = fields(x) != fields(y)
        r["P28E と P28 で state が違う"] = y["state"] != z["state"]
        r["P28E と P28 で state・reason・pointers・recomputed のどれかが違う"] = fields(y) != fields(z)
        r["形が真"] = o is not None
        r["前期"] = o["前期"] if o else None
        r["候補"] = o["候補"] if o else None
        r["決まった"] = o["決まった"] if o else None
        r["P28E の要素"] = D.local_name(pb[0]) if pb else None
        r["P28E の期"] = D.period_kind(pb[1]) if pb else None
        r["P28E の context"] = pb[1] if pb else None
        r["札"] = (labels.get(cid) or {}).get("札")
        rows.append(r)
    return rows


def tally(outs, rows, base, own_shas, rec_equal):
    T = collections.OrderedDict()
    T["claims"] = collections.OrderedDict((p, len(outs[p]["claims"])) for p in PROFILES)
    same = "同じ位置で id と(文の抜粋・数・単位)の鍵が 3 profile で同じ"
    T["行の対応(3 profile で同じ位置の id と鍵が同じ)"] = collections.OrderedDict([("対応", sum(1 for r in rows if r[same])), ("対応しない", sum(1 for r in rows if not r[same]))])
    T["4 state"] = collections.OrderedDict((p, collections.OrderedDict((s, outs[p]["document"]["states"].get(s, 0)) for s in STATES)) for p in PROFILES)
    shape = [r for r in rows if r["形が真"]]
    decided = [r for r in shape if r["決まった"]]
    moved = [r for r in rows if r["P27E → P28E で動いた"]]
    T["形が真の行"] = len(shape)
    T["形が真の行の id"] = [r["id"] for r in shape]
    T["決まって GROUNDED になった行"] = len(decided)
    T["決まった行の id"] = [r["id"] for r in decided]
    T["決まった行の P27E の state"] = collections.OrderedDict((s, sum(1 for r in decided if r["P27E の state"] == s)) for s in STATES)
    T["候補 2 以上で保留の行"] = sum(1 for r in shape if r["候補"] is not None and r["候補"] >= 2 and not r["決まった"])
    T["候補 0 の行"] = sum(1 for r in shape if r["候補"] == 0)
    T["候補 0 の行の id"] = [r["id"] for r in shape if r["候補"] == 0]
    T["候補の数の分布"] = collections.OrderedDict(sorted(collections.Counter(str(r["候補"]) for r in shape).items()))
    T["動いた行(P27E → P28E)"] = len(moved)
    T["動いた行の id"] = [r["id"] for r in moved]
    T["動いた行の向き"] = collections.OrderedDict(sorted(collections.Counter("%s → %s" % (r["P27E の state"], r["P28E の state"]) for r in moved).items()))
    T["動いた行のうち決まった行でない行"] = sum(1 for r in moved if not r["決まった"])
    T["P28E と P28 で state が違う行"] = sum(1 for r in rows if r["P28E と P28 で state が違う"])
    T["P28E と P28 で state・reason・pointers・recomputed のどれかが違う行"] = sum(1 for r in rows if r["P28E と P28 で state・reason・pointers・recomputed のどれかが違う"])
    T["P28E と P28 の 4 state が同じ"] = dict(T["4 state"]["P28E"]) == dict(T["4 state"]["P28"])
    shape_ids = set(r["id"] for r in shape)
    a, b = outs["P27E"]["claims"], outs["P28E"]["claims"]
    T["形が偽の行で P27E と state・reason・pointers が違う行"] = sum(1 for x, y in zip(a, b) if y["id"] not in shape_ids and (x["state"], x["reason"], x["pointers"]) != (y["state"], y["reason"], y["pointers"]))
    T["形が偽の行で P27E と state・reason・pointers・recomputed のどれかが違う行"] = sum(1 for x, y in zip(a, b) if y["id"] not in shape_ids and fields(x) != fields(y))
    g27 = [(x, y) for x, y in zip(a, b) if x["state"] == "GROUNDED"]
    T["P27E で GROUNDED の行"] = len(g27)
    T["P27E で GROUNDED の行のうち P28E で GROUNDED でない行"] = sum(1 for x, y in g27 if y["state"] != "GROUNDED")
    T["P27E で GROUNDED の行のうち P28E で pointers か recomputed が替わった行"] = sum(1 for x, y in g27 if x["pointers"] != y["pointers"] or x["recomputed"] != y["recomputed"])
    T["E-1 P27E の出力(engine の欄を除く sort_keys JSON)の sha256"] = collections.OrderedDict([("このtree", own_shas["P27E"]), ("HEAD の engine", base["P27E"]), ("一致", own_shas["P27E"] == base["P27E"])])
    T["E-1 参考: P28 の出力の sha256"] = collections.OrderedDict([("このtree", own_shas["P28"]), ("HEAD の engine", base["P28"]), ("一致", own_shas["P28"] == base["P28"])])
    T["E-1 P27E の claims が記録 entry_output_ai_prose_p27e と欄ごとに一致"] = rec_equal
    return T


def judge(T):
    J = collections.OrderedDict()
    J["E-1"] = bool(T["E-1 P27E の出力(engine の欄を除く sort_keys JSON)の sha256"]["一致"] and T["E-1 P27E の claims が記録 entry_output_ai_prose_p27e と欄ごとに一致"]
                    and dict(T["4 state"]["P27E"]) == dict(EXPECT_P27E))
    J["E-2"] = bool(dict(T["4 state"]["P28E"]) == dict(EXPECT_P28E) and T["P28E と P28 で state が違う行"] == 0)
    J["E-3"] = bool(T["決まって GROUNDED になった行"] == 7 and sorted(T["決まった行の id"]) == EXPECT_IDS and T["動いた行(P27E → P28E)"] == 7
                    and dict(T["動いた行の向き"]) == dict(EXPECT_DIRECTIONS))
    J["E-4"] = bool(T["形が偽の行で P27E と state・reason・pointers が違う行"] == 0 and T["P27E で GROUNDED の行のうち P28E で GROUNDED でない行"] == 0 and T["P27E で GROUNDED の行"] == 340)
    out = collections.OrderedDict((k, "当たり" if v else "外れ") for k, v in J.items())
    out["当たり"] = sum(1 for v in J.values() if v)
    out["外れ"] = sum(1 for v in J.values() if not v)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--entry-out", default=os.path.join(ROOT, ENTRY_REL))
    ap.add_argument("--dump-only", action="store_true", help="(内部)比べる側の engine で P27E と P28 の出力の sha256 だけ書く")
    ap.add_argument("--zip", default=os.path.join(ROOT, MATERIALS["zip"][0]))
    a = ap.parse_args(argv)
    if a.dump_only:
        with io.open(a.zip, "rb") as fh:
            zb = fh.read()
        res = dict((p, D.sha_bytes(D.dump_no_engine(VD.verify_document(zb, p, None)).encode("utf-8"))) for p in ("P27E", "P28"))
        with io.open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh)
        return
    for p in (a.out, a.entry_out):
        if os.path.exists(p):
            raise D.Stop("**出力が既に在る: %s。測り直さない。止める**" % p)
    shas = collections.OrderedDict()
    for k, (rel, want) in MATERIALS.items():
        got = D.sha256_file(os.path.join(ROOT, rel))
        if want is not None and got != want:
            raise D.Stop("%s の sha256 が封と違う: %s" % (rel, got))
        shas[rel] = got
    ldir, labels_ok = D.check_labels(os.path.join(ROOT, MATERIALS["label_list"][0]))
    if not all(v["在る"] and v["sha256 が名簿と合う"] for v in labels_ok.values()):
        raise D.Stop("ラベル file が cache に無いか sha256 が名簿と合わない: %s" % json.dumps(labels_ok, ensure_ascii=False))
    bundle_sha, n_files, dirty = D.engine_bundle()
    zpath = os.path.join(ROOT, MATERIALS["zip"][0])
    with io.open(zpath, "rb") as fh:
        zb = fh.read()
    work = tempfile.mkdtemp(prefix="p28e_ai_prose_", dir=os.environ.get("TMPDIR"))
    base, base_files = baseline_dump(work, zpath)
    outs, provs, own_shas = {}, {}, {}
    for pf in PROFILES:
        o, pm = D.run_profile(zb, pf)
        own_shas[pf] = D.sha_bytes(D.dump_no_engine(o).encode("utf-8"))
        outs[pf], provs[pf] = D.scrub(o), pm
        if D.DOCID_RE.search(json.dumps(outs[pf], ensure_ascii=False)):
            raise D.Stop("%s の entry に docID が残った" % pf)
    rec27e = D.jload(os.path.join(ROOT, MATERIALS["entry_p27e"][0]))
    rec_equal = json.dumps(outs["P27E"]["claims"], ensure_ascii=False, sort_keys=True) == json.dumps(rec27e["claims"], ensure_ascii=False, sort_keys=True)
    labels = dict((x["id"], x) for x in D.jload(os.path.join(ROOT, MATERIALS["labels"][0]))["labels"])
    rows = build_rows(outs, provs, labels)
    T = tally(outs, rows, base, own_shas, rec_equal)
    rec = collections.OrderedDict()
    rec["注意"] = ("同梱の AI の文の書類を P27E・P28E・P28 で判定した記録。1 書類・1 model の AI の文。docID は書かない。"
                 "形・候補・決まったは engine の Claim.provenance から読んだ(verify_document の出力には出ない)。")
    rec["封"] = collections.OrderedDict([("file", SEAL_REL), ("commit", SEAL_COMMIT)])
    rec["HEAD の commit"] = D.git_head()
    rec["この script の sha256"] = D.sha256_file(os.path.abspath(__file__))
    rec["読んだ材料の sha256"] = shas
    rec["書いた entry"] = ENTRY_REL
    rec["定数"] = collections.OrderedDict([("profile", list(PROFILES)), ("比べる engine の commit", BASELINE_COMMIT), ("E-1 の 4 state", EXPECT_P27E), ("E-2 の 4 state", EXPECT_P28E),
                                         ("E-3 の id", EXPECT_IDS), ("E-3 の向き", EXPECT_DIRECTIONS)])
    W = collections.OrderedDict()
    W["(b) ラベル file(cache。repo の外)"] = labels_ok
    W["(c) engine の bundle の sha256(core/・adapters/。この tree)"] = bundle_sha
    W["(c) engine の file の数"] = n_files
    W["(c) engine の未 commit の file の数(commit 前の実測なので 0 でない)"] = dirty
    W["(d) 比べる側の engine の blob(adapters/xbrl の file の sha256)"] = base_files
    W["(e) 行の対応"] = T["行の対応(3 profile で同じ位置の id と鍵が同じ)"]
    W["通った"] = bool(W["(e) 行の対応"]["対応しない"] == 0)
    rec["配線の門"] = W
    rec["行"] = rows
    rec["集計"] = T
    rec["予測の判定"] = judge(T)
    rec["limits"] = ["1 書類・1 model の AI の文。この書類の数",
                     "決まった 7 行の正しさは前の便(P28 の封)で読み済み。ここは盲検ではない(E-3 は当たりやすい)",
                     "engine の変更は本便の vocabulary.py への挿入だけ。既定は P27 のまま"]
    rec["key_leaks"] = D.record_key_leaks(rec)
    if not W["通った"]:
        raise D.Stop("配線の門が通らない: %s" % json.dumps(W, ensure_ascii=False)[:600])
    text = json.dumps(rec, ensure_ascii=False)
    if D.DOCID_RE.search(text) or rec["key_leaks"]:
        raise D.Stop("記録に docID か鍵が入った")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with io.open(a.entry_out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(outs["P28E"], ensure_ascii=False, indent=1) + "\n")
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print("written: %s" % a.out)
    print(json.dumps(rec["予測の判定"], ensure_ascii=False))
    for k in ("4 state", "形が真の行", "決まって GROUNDED になった行", "決まった行の id", "動いた行(P27E → P28E)", "動いた行の向き", "P28E と P28 で state が違う行",
              "形が偽の行で P27E と state・reason・pointers が違う行", "P27E で GROUNDED の行のうち P28E で GROUNDED でない行", "候補 2 以上で保留の行", "候補 0 の行"):
        print(k, json.dumps(T[k], ensure_ascii=False))


if __name__ == "__main__":
    main()
