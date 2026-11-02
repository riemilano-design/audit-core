# -*- coding: utf-8 -*-
u"""AI の文 1 書類を P27 と P28 で再判定する(封 docs/XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02.md §5-1・§3-1)。

同梱の AI の文の書類(ZIP)を adapters.xbrl.verify_document で P27 と P28 の 2 つの profile で判定し、行の対応・形が真の行の一覧・動いた行・
O-1〜O-7 の判定を記録に書く。形が真か・候補の数・決まったかは verify_document の出力に出ないので、同じ engine の ``recipes.build_recipes`` の
``Claim.provenance["other_subject_2026_11_02"]`` から読む。標準ラベルは cache に在り sha256 が名簿と合うときだけ走る。通信しない・0 USD・LLM を呼ばない。

    python3 measure/xbrl_p28_ai_prose_2026-11-02.py [--out fixtures/xbrl/p28/ai_prose_2026-11-02.json]

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- O-1 の「HEAD c4b8221 の engine と byte 一致」は、``git archive c4b8221 audit-core/adapters audit-core/core`` を TMPDIR に取り出し(blob と byte 一致を確かめ)、
  同じ script を別の process で ``--dump-only`` で走らせて P27 の出力(``sort_keys`` の JSON。``engine`` の欄を除く)の sha256 を得て比べる。
  さらに §5-1 の配線の門として、P27 の出力(docID を <docID> に置換した claims)が ``fixtures/xbrl/entry_output_ai_prose_p27_2026-11-02.json`` の claims と欄ごとに一致することも求める。
- 候補の数 n は、形が真の claim の全部(engine が GROUNDED にした行も)で数える(O-5 の「候補 0 の行」に N162・N163 = engine が GROUNDED にした行が入る、と封が書いたため)。
  決まったは、engine が GROUNDED にしなかった行で候補がちょうど 1 つのときだけ真。
- O-3 の数 = 決まった行。O-4 = 決まった行の全部が下の EXPECT_O4 の id に在り、要素の local name と期が同じ(表の行が決まらなかったことは O-4 では数えず、別に書く)。
- O-5 の保留 = 候補 2 以上で決まらなかった行。候補 0 の行 = 形が真で候補 0 の行(engine が GROUNDED にした行を含む)。
- O-6 の「形が偽の行」 = provenance に欄が無い claim。P27 と state・reason・pointers・recomputed のどれかが違う行を数える。GROUNDED 340 は P27 で GROUNDED の行が P28 でも state・pointers が同じ。
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
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
ENGINE_ROOT = os.environ.get("P28_ENGINE_ROOT") or ROOT          # 比べる側(封の時点の engine の写し)を別の process で測るときだけ替える
sys.path.insert(0, os.path.join(ENGINE_ROOT, "core", "py"))
sys.path.insert(0, ENGINE_ROOT)

from adapters.xbrl import verify_document as VD   # noqa: E402
from adapters.xbrl import vocabulary as V         # noqa: E402

SEAL_REL = "docs/XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02.md"
SEAL_COMMIT = "c6cbfae"
BASELINE_COMMIT = "c4b8221"
OUT_REL = "fixtures/xbrl/p28/ai_prose_2026-11-02.json"
ENTRY_REL = "fixtures/xbrl/p28/entry_output_ai_prose_p28_2026-11-02.json"
PROFILES = ("P27", "P28")
KEY = "other_subject_2026_11_02"
MATERIALS = collections.OrderedDict([
    ("zip", ("fixtures/xbrl/ai_prose_instance_2026-10-09.zip", "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799")),
    ("entry_p27", ("fixtures/xbrl/entry_output_ai_prose_p27_2026-11-02.json", "82004d4c9c578fe70360dfea8b0779c76946b04445e5c79975a5d6094dc0c49f")),
    ("labels", ("fixtures/xbrl/ai_prose_labels_2026-10-09.json", "7eac1450c40c68e0a25bf7f56c32db4ee6dad226e55df7efdb8019764a71173b")),
    ("label_list", ("fixtures/xbrl/taxonomy_labels_sha256.txt", "92fe4bcad0d91fcc8256f7f3132494eafd231de9039fa99da3939af11298a13e")),
])
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
RITUAL_PLAIN = collections.OrderedDict([("GROUNDED", 340), ("POINTER_NOT_FOUND", 25), ("UNVERIFIABLE", 33), ("VALUE_MISMATCH", 14)])
#: 封 §3-1 O-4: docs/XBRL_OTHER_RULE_2026-11-02.md §2-2 の表(R1 で決まる 8 のうち engine が既に GROUNDED の N118 を除く 7)。期 = 結んだ fact の context の頭。
EXPECT_O4 = collections.OrderedDict([("N080", ("OtherNOI", "CurrentYear")), ("N081", ("OtherNOI", "Prior1Year")), ("N144", ("OtherCA", "CurrentYear")),
                                     ("N145", ("OtherCA", "Prior1Year")), ("N213", ("OtherNCL", "CurrentYear")), ("N290", ("OtherNetInvCF", "CurrentYear")),
                                     ("N299", ("OtherNetFinCF", "CurrentYear"))])
BOUNDS = {"O-2": (10, 16), "O-3": (6, 8), "O-5 保留": (0, 2), "O-5 候補 0": (3, 6),
          "O-7": collections.OrderedDict([("GROUNDED", (346, 348)), ("VALUE_MISMATCH", (11, 13)), ("UNVERIFIABLE", (33, 33)), ("POINTER_NOT_FOUND", (19, 22))])}
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
DOCID_ANY_RE = re.compile(r"S100[A-Z0-9]{4}")
POINTER_RE = re.compile(r"^xbrl:([A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+)@([A-Za-z0-9_\-]+)$")
KEY_PATTERNS = (r"sk-[A-Za-z0-9_\-]{10,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{20,}", r"xox[baprs]-[A-Za-z0-9\-]{10,}",
                r"-----BEGIN", r"Bearer [A-Za-z0-9._\-]{16,}", r"AIza[0-9A-Za-z_\-]{30,}")


class Stop(SystemExit):
    pass


def sha256_file(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dump_no_engine(out):
    d = dict(out)
    d.pop("engine", None)
    return json.dumps(d, ensure_ascii=False, sort_keys=True)


def scrub(obj):
    u"""文字列の中の docID を <docID> に。"""
    if isinstance(obj, dict):
        return collections.OrderedDict((k, scrub(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return [scrub(x) for x in obj]
    if isinstance(obj, str):
        return DOCID_ANY_RE.sub(u"<docID>", obj)
    return obj


def local_name(e):
    return e.split(":")[-1]


def pointer_parts(pointers):
    u"""pointers の 1 つ目の (要素 qname, context)。無ければ None。"""
    for p in pointers or []:
        m = POINTER_RE.match(p)
        if m:
            return m.group(1), m.group(2)
    return None


def period_kind(ctx):
    return "当期" if ctx.startswith("CurrentYear") else ("前期" if ctx.startswith("Prior1Year") else "他")


def prov_map(zb, profile_name):
    u"""id → {subject, other(provenance の欄。無ければ None), no_same_value}。verify_document の出力に出ない欄を同じ engine の Recipe から読む。"""
    from adapters.xbrl import recipes as R
    out = {}
    for r in R.build_recipes(zb, V.PROFILES[profile_name]):
        cl = r.claim
        out[cl.id] = {"subject": cl.subject, "other": cl.provenance.get(KEY), "no_same_value": cl.provenance.get("no_same_value")}
    return out


def run_profile(zb, profile_name):
    out = VD.verify_document(zb, profile_name, None)
    return out, prov_map(zb, profile_name)


# ---------------------------------------------------------------- ラベル file と engine の束

def label_dir():
    from adapters.xbrl import instance as I
    return I.taxonomy_dir() if hasattr(I, "taxonomy_dir") else (os.environ.get("EDINET_TAXONOMY_DIR") or I.TAXONOMY_DIR_DEFAULT)


def check_labels(list_path):
    d = label_dir()
    out = collections.OrderedDict()
    with io.open(list_path, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            want, name = ln.split()
            p = os.path.join(d, name)
            got = sha256_file(p) if os.path.exists(p) else None
            out[name] = collections.OrderedDict([("在る", got is not None), ("sha256 が名簿と合う", got == want)])
    return d, out


def engine_bundle():
    fb = load_module(os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py"), "frozen_bundle_sha_for_p28")
    cwd = os.getcwd()
    try:
        os.chdir(REPO)
        sha, rows = fb.bundle()
        dirty = fb._dirty_count()
    finally:
        os.chdir(cwd)
    return sha, len(rows), dirty


def git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode().strip() if r.returncode == 0 else None


def baseline_p27_dump(work, zpath):
    u"""HEAD の engine(封の commit の engine)を git archive で取り出し、別の process で P27 の出力の sha256 を得る。"""
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
                raise Stop("**取り出した写しが commit の blob と違う: %s。止める**" % rel)
        files[rel] = sha_bytes(blob)
    out_json = os.path.join(work, "baseline_dump.json")
    env = dict(os.environ, P28_ENGINE_ROOT=root)
    subprocess.run([sys.executable, os.path.abspath(__file__), "--dump-only", "--zip", zpath, "--out", out_json], env=env, check=True)
    return jload(out_json), files


# ---------------------------------------------------------------- 数える

def row_key(c):
    return (c["span"], c["value"], c["unit"])


def fields(c):
    return (c["state"], c["reason"], tuple(c["pointers"]), c["recomputed"])


def build(out27, out28, prov27, prov28, labels):
    c27, c28 = out27["claims"], out28["claims"]
    align = [c27[i]["id"] == c28[i]["id"] and row_key(c27[i]) == row_key(c28[i]) for i in range(min(len(c27), len(c28)))]
    rows, shape_rows, moved = [], [], []
    for a, b in zip(c27, c28):
        cid = a["id"]
        o = prov28[cid]["other"]
        pa, pb = pointer_parts(a["pointers"]), pointer_parts(b["pointers"])
        lab = labels.get(cid) or {}
        r = collections.OrderedDict()
        r["id"] = cid
        r["P27 の state"], r["P27 の reason"] = a["state"], a["reason"]
        r["P28 の state"], r["P28 の reason"] = b["state"], b["reason"]
        r["動いた"] = fields(a) != fields(b)
        r["形が真"] = o is not None
        r["P28 の provenance に P27 の欄が無い(P27 側)"] = prov27[cid]["other"] is None
        r["前期"] = o["前期"] if o else None
        r["候補"] = o["候補"] if o else None
        r["決まった"] = o["決まった"] if o else None
        r["P27 の要素"] = local_name(pa[0]) if pa else None
        r["P27 の期"] = period_kind(pa[1]) if pa else None
        nsv = pointer_parts([prov27[cid]["no_same_value"]["named"]]) if prov27[cid]["no_same_value"] else None
        r["P27 の named(no_same_value)"] = local_name(nsv[0]) if nsv else None
        r["P28 の要素"] = local_name(pb[0]) if pb else None
        r["P28 の期"] = period_kind(pb[1]) if pb else None
        r["P28 の context"] = pb[1] if pb else None
        r["主語なし(P28 の claim)"] = prov28[cid]["subject"] is None
        r["札"] = lab.get("札")
        rows.append(r)
        if r["動いた"]:
            moved.append(r)
        if o is not None:
            shape_rows.append(r)
    return align, rows, shape_rows, moved


def tally(out27, out28, rows, shape_rows, moved, align, base_sha, own_sha, rec_equal):
    T = collections.OrderedDict()
    T["claims"] = collections.OrderedDict([("P27", len(out27["claims"])), ("P28", len(out28["claims"]))])
    T["行の対応(同じ位置で id と 文の抜粋・数・単位の鍵が同じ)"] = collections.OrderedDict([("対応", sum(1 for x in align if x)), ("対応しない", sum(1 for x in align if not x))])
    T["4 state"] = collections.OrderedDict((p, collections.OrderedDict((s, out["document"]["states"].get(s, 0)) for s in STATES)) for p, out in (("P27", out27), ("P28", out28)))
    decided = [r for r in shape_rows if r["決まった"]]
    T["形が真の行"] = len(shape_rows)
    T["形が真の行の id"] = [r["id"] for r in shape_rows]
    T["決まって GROUNDED になった行"] = len(decided)
    T["決まった行の id"] = [r["id"] for r in decided]
    T["決まった行の P27 の state"] = collections.OrderedDict((s, sum(1 for r in decided if r["P27 の state"] == s)) for s in STATES)
    T["候補 2 以上で保留の行"] = sum(1 for r in shape_rows if r["候補"] is not None and r["候補"] >= 2 and not r["決まった"])
    T["候補 2 以上で保留の行の id"] = [r["id"] for r in shape_rows if r["候補"] is not None and r["候補"] >= 2 and not r["決まった"]]
    T["候補 0 の行"] = sum(1 for r in shape_rows if r["候補"] == 0)
    T["候補 0 の行の id"] = [r["id"] for r in shape_rows if r["候補"] == 0]
    T["候補の数の分布"] = collections.OrderedDict(sorted(collections.Counter(r["候補"] for r in shape_rows).items(), key=lambda kv: str(kv[0])))
    T["形が真で engine が P27 で GROUNDED の行"] = sum(1 for r in shape_rows if r["P27 の state"] == "GROUNDED")
    T["決まった行のうち主語なし(P28 の claim の subject が空)"] = sum(1 for r in decided if r["主語なし(P28 の claim)"])
    T["動いた行"] = len(moved)
    T["動いた行の向き"] = collections.OrderedDict(sorted(collections.Counter("%s → %s" % (r["P27 の state"], r["P28 の state"]) for r in moved).items()))
    shape_ids = set(r["id"] for r in shape_rows)
    T["形が偽の行で動いた行"] = sum(1 for r in moved if r["id"] not in shape_ids)
    T["P27 で GROUNDED の行が P28 で state か pointers が替わった行"] = sum(1 for r in rows if r["P27 の state"] == "GROUNDED" and r["動いた"])
    # O-4
    o4_bad, o4_ok = [], []
    for r in decided:
        want = EXPECT_O4.get(r["id"])
        got = (r["P28 の要素"], (r["P28 の context"] or "")[:len(want[1])] if want else None)
        (o4_ok if (want and got == want) else o4_bad).append(collections.OrderedDict([("id", r["id"]), ("結んだ要素", r["P28 の要素"]), ("結んだ期", r["P28 の期"]), ("表の要素と期", want)]))
    T["O-4 決まった行のうち表と同じ"] = len(o4_ok)
    T["O-4 決まった行のうち表と違う(表に無い id を含む)"] = o4_bad
    T["表の行(EXPECT_O4)で決まらなかった id"] = [i for i in EXPECT_O4 if i not in set(r["id"] for r in decided)]
    T["O-1 P27 の出力(engine の欄を除く sort_keys JSON)の sha256"] = collections.OrderedDict([("このtree", own_sha), ("HEAD の engine", base_sha), ("一致", own_sha == base_sha)])
    T["O-1 P27 の claims が記録 entry_output_ai_prose_p27 と欄ごとに一致"] = rec_equal
    return T


def judge(T):
    J = collections.OrderedDict()
    g = T["4 state"]["P27"]
    J["O-1"] = bool(T["O-1 P27 の出力(engine の欄を除く sort_keys JSON)の sha256"]["一致"] and T["O-1 P27 の claims が記録 entry_output_ai_prose_p27 と欄ごとに一致"]
                    and dict(g) == dict((s, RITUAL_PLAIN[s]) for s in STATES))
    J["O-2"] = BOUNDS["O-2"][0] <= T["形が真の行"] <= BOUNDS["O-2"][1]
    J["O-3"] = BOUNDS["O-3"][0] <= T["決まって GROUNDED になった行"] <= BOUNDS["O-3"][1]
    J["O-4"] = bool(T["決まって GROUNDED になった行"]) and not T["O-4 決まった行のうち表と違う(表に無い id を含む)"]
    J["O-5"] = (BOUNDS["O-5 保留"][0] <= T["候補 2 以上で保留の行"] <= BOUNDS["O-5 保留"][1]) and (BOUNDS["O-5 候補 0"][0] <= T["候補 0 の行"] <= BOUNDS["O-5 候補 0"][1])
    J["O-6"] = bool(T["形が偽の行で動いた行"] == 0 and T["P27 で GROUNDED の行が P28 で state か pointers が替わった行"] == 0 and g["GROUNDED"] == 340)
    J["O-7"] = all(BOUNDS["O-7"][s][0] <= T["4 state"]["P28"][s] <= BOUNDS["O-7"][s][1] for s in STATES)
    out = collections.OrderedDict((k, "当たり" if v else "外れ") for k, v in J.items())
    out["当たり"] = sum(1 for v in J.values() if v)
    out["外れ"] = sum(1 for v in J.values() if not v)
    return out


def record_key_leaks(rec):
    text = json.dumps(rec, ensure_ascii=False)
    return [p for p in KEY_PATTERNS if re.search(p, text)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--entry-out", default=os.path.join(ROOT, ENTRY_REL))
    ap.add_argument("--dump-only", action="store_true", help="(内部)比べる側の engine で P27 の出力の sha256 だけ書く")
    ap.add_argument("--zip", default=os.path.join(ROOT, MATERIALS["zip"][0]))
    a = ap.parse_args(argv)
    if a.dump_only:
        with io.open(a.zip, "rb") as fh:
            zb = fh.read()
        out = VD.verify_document(zb, "P27", None)
        with io.open(a.out, "w", encoding="utf-8") as fh:
            json.dump({"sha256": sha_bytes(dump_no_engine(out).encode("utf-8")), "bytes": len(dump_no_engine(out).encode("utf-8"))}, fh)
        return
    for p in (a.out, a.entry_out):
        if os.path.exists(p):
            raise Stop("**出力が既に在る: %s。測り直さない。止める**" % p)
    shas = collections.OrderedDict()
    for k, (rel, want) in MATERIALS.items():
        got = sha256_file(os.path.join(ROOT, rel))
        if want is not None and got != want:
            raise Stop("%s の sha256 が封と違う: %s" % (rel, got))
        shas[rel] = got
    ldir, labels_ok = check_labels(os.path.join(ROOT, MATERIALS["label_list"][0]))
    if not all(v["在る"] and v["sha256 が名簿と合う"] for v in labels_ok.values()):
        raise Stop("ラベル file が cache に無いか sha256 が名簿と合わない: %s" % json.dumps(labels_ok, ensure_ascii=False))
    bundle_sha, n_files, dirty = engine_bundle()
    zpath = os.path.join(ROOT, MATERIALS["zip"][0])
    with io.open(zpath, "rb") as fh:
        zb = fh.read()
    work = tempfile.mkdtemp(prefix="p28_ai_prose_", dir=os.environ.get("TMPDIR"))
    base, base_files = baseline_p27_dump(work, zpath)
    outs, provs = {}, {}
    for pf in PROFILES:
        o, pm = run_profile(zb, pf)
        outs[pf], provs[pf] = scrub(o), pm
        if DOCID_RE.search(json.dumps(outs[pf], ensure_ascii=False)):
            raise Stop("%s の entry に docID が残った" % pf)
    own_sha = sha_bytes(dump_no_engine(VD.verify_document(zb, "P27", None)).encode("utf-8"))
    rec27 = jload(os.path.join(ROOT, MATERIALS["entry_p27"][0]))
    rec_equal = json.dumps(outs["P27"]["claims"], ensure_ascii=False, sort_keys=True) == json.dumps(rec27["claims"], ensure_ascii=False, sort_keys=True)
    labels = dict((x["id"], x) for x in jload(os.path.join(ROOT, MATERIALS["labels"][0]))["labels"])
    align, rows, shape_rows, moved = build(outs["P27"], outs["P28"], provs["P27"], provs["P28"], labels)
    T = tally(outs["P27"], outs["P28"], rows, shape_rows, moved, align, base["sha256"], own_sha, rec_equal)
    rec = collections.OrderedDict()
    rec["注意"] = ("同梱の AI の文の書類を P27 と P28 で判定した記録。1 書類・1 model の AI の文。docID は書かない。"
                 "形・候補・決まったは engine の Claim.provenance から読んだ(verify_document の出力には出ない)。")
    rec["封"] = collections.OrderedDict([("file", SEAL_REL), ("commit", SEAL_COMMIT)])
    rec["HEAD の commit"] = git_head()
    rec["この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec["読んだ材料の sha256"] = shas
    rec["書いた entry"] = ENTRY_REL
    rec["定数"] = collections.OrderedDict([("profile", list(PROFILES)), ("比べる engine の commit", BASELINE_COMMIT), ("予測の幅", BOUNDS), ("O-4 の表", EXPECT_O4)])
    W = collections.OrderedDict()
    W["(a) 材料の sha256 が封の値"] = True
    W["(b) ラベル file(cache。repo の外)"] = labels_ok
    W["(c) engine の bundle の sha256(core/・adapters/。この tree)"] = bundle_sha
    W["(c) engine の file の数"] = n_files
    W["(c) engine の未 commit の file の数(commit 前の実測なので 0 でない)"] = dirty
    W["(d) 比べる側の engine の blob(adapters/xbrl の file の sha256)"] = base_files
    W["(e) 行の対応"] = T["行の対応(同じ位置で id と 文の抜粋・数・単位の鍵が同じ)"]
    W["(f) P27 の 4 state が儀式の記録の素の書類と一致"] = dict(T["4 state"]["P27"]) == dict((s, RITUAL_PLAIN[s]) for s in STATES)
    W["通った"] = bool(W["(e) 行の対応"]["対応しない"] == 0 and W["(f) P27 の 4 state が儀式の記録の素の書類と一致"])
    rec["配線の門"] = W
    rec["行"] = rows
    rec["集計"] = T
    rec["予測の判定"] = judge(T)
    rec["limits"] = ["1 書類・1 model の AI の文。この書類の数",
                     "決まった行の正しさは札の根拠と measure の表(O-4)でしか見ていない。偽の一致(代価)は 97 書類の読みで見る",
                     "engine の変更は本便の挿入だけ。既定は P27 のまま"]
    rec["key_leaks"] = record_key_leaks(rec)
    if not W["通った"]:
        raise Stop("配線の門が通らない: %s" % json.dumps(W, ensure_ascii=False)[:600])
    text = json.dumps(rec, ensure_ascii=False)
    if DOCID_RE.search(text) or rec["key_leaks"]:
        raise Stop("記録に docID か鍵が入った")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with io.open(a.entry_out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(outs["P28"], ensure_ascii=False, indent=1) + "\n")
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print("written: %s" % a.out)
    print(json.dumps(rec["予測の判定"], ensure_ascii=False))
    for k in ("4 state", "形が真の行", "決まって GROUNDED になった行", "決まった行の id", "候補 2 以上で保留の行", "候補 0 の行", "候補の数の分布", "動いた行の向き", "形が偽の行で動いた行",
              "O-4 決まった行のうち表と違う(表に無い id を含む)", "表の行(EXPECT_O4)で決まらなかった id"):
        print(k, json.dumps(T[k], ensure_ascii=False))


if __name__ == "__main__":
    main()
