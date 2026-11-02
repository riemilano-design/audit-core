# -*- coding: utf-8 -*-
u"""AI の文を P27E と P27 で再判定する(封 docs/XBRL_P27E_RERUN_SEAL_2026-11-02.md)。

engine を変えずに走らせる: 同梱の AI の文の書類(ZIP)を adapters.xbrl.verify_document で P27E と P27 の 2 つの profile で判定し、
claim ごとの記録 2 つと、P16 の記録(2026-10-13)との突き合わせの記録 1 つを書く。ラベル file は cache に在り sha256 が名簿と合う
ときだけ走る。材料は全部 repo の中(封 §0 の 8 file。sha256 を照らす)。engine の字は変えない(bundle の sha256 と HEAD を記録する)。

    python3 measure/xbrl_rerun_p27e_2026-11-02.py [--out-dir fixtures/xbrl]

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- 行の対応は P16 の entry の claims と新しい claims を id の順(配列の順)で並べ、同じ位置の (span, value, unit) が一致すれば対応。
  一致しない行は同じ鍵で未対応の行から探し直す。対応しない行は数だけ。新しい記録の行には P16 の id を「P16 の id」として書く。
- 記録に書く entry は verify_document の返り値そのまま。ただし文字列の中の docID(S100 + 英数 4 字)は「<docID>」に置き換える。
- 札の根拠との照らし(M-9)は pointers の要素の local name が根拠の字に部分文字列として在るか(「止めた真の文」の便と同じ)。
- 53 行は止めた真の文の記録の行(全部 母数)。12 行は「その他」の便の記録で その他の行 かつ 札 真。8 行は期の印の記録で
  取り違えの中身が「札が文の期と合う(engine の期の取り違え)」かつ向きが「前期の文 × engine 当期」。249 行は P16 で GROUNDED・札 真・kind num。
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SEAL_REL = "docs/XBRL_P27E_RERUN_SEAL_2026-11-02.md"
SEAL_COMMIT = "35f624c"
OUT_REL = "fixtures/xbrl/rerun_p27e_2026-11-02.json"
ENTRY_REL = collections.OrderedDict([(u"P27E", "fixtures/xbrl/entry_output_ai_prose_p27e_2026-11-02.json"), (u"P27", "fixtures/xbrl/entry_output_ai_prose_p27_2026-11-02.json")])
MATERIALS = collections.OrderedDict([
    (u"zip", ("fixtures/xbrl/ai_prose_instance_2026-10-09.zip", "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799")),
    (u"entry16", ("fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json", "6c4c65d1d24ed46250d6bda41fc023d0624ec130f9c1fe791e840c6def7077da")),
    (u"claims", ("fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json", "c886a9e69353c677297341436f9777b779895054804adce1805f3d546dd4b579")),
    (u"labels", ("fixtures/xbrl/ai_prose_labels_2026-10-09.json", "7eac1450c40c68e0a25bf7f56c32db4ee6dad226e55df7efdb8019764a71173b")),
    (u"stopped", ("fixtures/xbrl/derivation_stopped_2026-11-02.json", "cacbdb62a958522f9284cfc026f057ddb8d7be4c8e648f5ad579faa7edd4775e")),
    (u"other", ("fixtures/xbrl/other_rule_2026-11-02.json", "76ad667f53314e4548626dde1176329d951fd853382e9b8949a8fe5a7b962783")),
    (u"period", ("fixtures/xbrl/period_mark_2026-11-02.json", "7e026ac938f38e5e7f1dd09ba85466419e3831734eaa8f329cdb7d1f37a34901")),
    (u"label_list", ("fixtures/xbrl/taxonomy_labels_sha256.txt", "92fe4bcad0d91fcc8256f7f3132494eafd231de9039fa99da3939af11298a13e")),
])
PROFILES = (u"P27E", u"P27")
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
RITUAL_PLAIN = collections.OrderedDict([(u"GROUNDED", 340), (u"POINTER_NOT_FOUND", 25), (u"UNVERIFIABLE", 33), (u"VALUE_MISMATCH", 14)])
BOUNDS = {u"M-1": RITUAL_PLAIN, u"M-2": 412, u"M-3": (5, 15), u"M-4": (0, 12), u"M-5": (0, 3), u"M-6": (0, 2), u"M-7": (0, 10), u"M-9": (0, 10)}
TYPES_T = (u"T1 指せず", u"T2 同じ fact", u"T3 導出の量", u"T4 同じ要素・別の期", u"T5 別の要素", u"T6 導出も決めない")
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


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
            out[name] = collections.OrderedDict([(u"在る", got is not None), (u"sha256 が名簿と合う", got == want)])
    return d, out


def engine_bundle():
    fb = load_module(os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py"), "frozen_bundle_sha_for_rerun")
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


# ---------------------------------------------------------------- 封 §1: 走らせ方

def scrub(obj):
    u"""文字列の中の docID を <docID> に。"""
    if isinstance(obj, dict):
        return collections.OrderedDict((k, scrub(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return [scrub(x) for x in obj]
    if isinstance(obj, str):
        return DOCID_ANY_RE.sub(u"<docID>", obj)
    return obj


def run_engine(zb, profile):
    from adapters.xbrl import verify_document as VD
    return VD.verify_document(zb, profile, None)


# ---------------------------------------------------------------- 封 §2: 行の対応と数えるもの

def key_of(c):
    return (c.get(u"span"), c.get(u"value"), c.get(u"unit"))  # 封 §2 の鍵そのまま


def align(claims16, claims_new):
    u"""P16 の i 行目と新しい i 行目の鍵が同じなら対応。違えば未対応の行から鍵で探す。返す: P16 の id → 新しい claim(無ければ None)、数。"""
    mapping = collections.OrderedDict()
    used = set()
    direct = 0
    for i, c in enumerate(claims16):
        if i < len(claims_new) and key_of(claims_new[i]) == key_of(c):
            mapping[c[u"id"]] = claims_new[i]
            used.add(i)
            direct += 1
        else:
            mapping[c[u"id"]] = None
    searched = 0
    for c in claims16:
        if mapping[c[u"id"]] is None:
            for j, n in enumerate(claims_new):
                if j not in used and key_of(n) == key_of(c):
                    mapping[c[u"id"]] = n
                    used.add(j)
                    searched += 1
                    break
    unmatched = [c[u"id"] for c in claims16 if mapping[c[u"id"]] is None]
    extra = len(claims_new) - len(used)
    return mapping, collections.OrderedDict([(u"同じ位置で対応", direct), (u"探し直して対応", searched), (u"対応しない P16 の行", len(unmatched)), (u"対応しない P16 の id", unmatched), (u"新しい方の余り", extra)])


def local_name(e):
    return e.split(u":")[-1]


def period_of(pointers):
    for p in pointers or []:
        m = POINTER_RE.match(p)
        if m:
            ctx = m.group(2)
            return u"当期" if ctx.startswith(u"CurrentYear") else (u"前期" if ctx.startswith(u"Prior1Year") else u"他")
    return None


def elements_in_grounds(pointers, grounds):
    els = [POINTER_RE.match(p).group(1) for p in pointers or [] if POINTER_RE.match(p)]
    if not els:
        return None
    return any(local_name(e) in (grounds or u"") for e in els)


def grounds_form(form, grounds):
    u"""参考: 札の根拠の字の形。「同」で始まる(同元素・同/前期 など略した根拠)、導出の文(form が derived_value。根拠は数式)、それ以外(要素名が書かれうる)。
    M-9 の照らし(local name の部分文字列)は略した根拠・数式の根拠では当たらない。判定は封の定義のまま、内訳だけ参考に書く。"""
    g = grounds or u""
    if g.startswith(u"同"):
        return u"同(略した根拠)"
    if form == u"derived_value":
        return u"数式(導出の文)"
    return u"要素名を書きうる"


GROUNDS_FORMS = (u"同(略した根拠)", u"数式(導出の文)", u"要素名を書きうる")


def build_rows(entry16, new_entries, labels, sets):
    claims16 = entry16[u"claims"]
    maps = collections.OrderedDict((pf, align(claims16, new_entries[pf][u"claims"])) for pf in PROFILES)
    rows = []
    for c in claims16:
        cid = c[u"id"]
        lab = labels.get(cid) or {}
        r = collections.OrderedDict()
        r[u"id"] = cid
        r[u"札"] = lab.get(u"札")
        r[u"kind"] = c.get(u"kind")
        r[u"unit"] = c.get(u"unit")
        r[u"value"] = c.get(u"value")
        r[u"P16 の state"] = c.get(u"state")
        r[u"P16 の pointers"] = c.get(u"pointers") or []
        for pf in PROFILES:
            n = maps[pf][0][cid]
            r[u"%s で対応" % pf] = n is not None
            r[u"%s の state" % pf] = n.get(u"state") if n else None
            r[u"%s の pointers" % pf] = (n.get(u"pointers") or []) if n else []
            r[u"%s の reason" % pf] = n.get(u"reason") if n else None
            r[u"%s の recomputed" % pf] = n.get(u"recomputed") if n else None
            r[u"%s の期" % pf] = period_of(n.get(u"pointers")) if n else None
            r[u"%s で GROUNDED の要素が根拠に在る" % pf] = elements_in_grounds(n.get(u"pointers"), lab.get(u"根拠")) if (n and n.get(u"state") == u"GROUNDED" and lab.get(u"札") == u"真") else None
        r[u"P27E と P27 で state が違う"] = (r[u"P27E の state"] != r[u"P27 の state"]) if (r[u"P27E で対応"] and r[u"P27 で対応"]) else None
        r[u"根拠の形(参考)"] = grounds_form(c.get(u"form"), lab.get(u"根拠"))
        r[u"53 行"] = cid in sets[u"53"]
        r[u"型(53 行)"] = sets[u"53"].get(cid)
        r[u"12 行"] = cid in sets[u"12"]
        r[u"R1 の判定(12 行)"] = sets[u"12"].get(cid)
        r[u"8 行"] = cid in sets[u"8"]
        r[u"249 行(P16 で GROUNDED・札 真・num)"] = (lab.get(u"札") == u"真" and c.get(u"kind") == u"num" and c.get(u"state") == u"GROUNDED")
        r[u"根拠"] = lab.get(u"根拠")
        rows.append(r)
    return rows, collections.OrderedDict((pf, maps[pf][1]) for pf in PROFILES)


def _dist(items):
    return collections.OrderedDict((s, sum(1 for x in items if x == s)) for s in STATES)


def tally(rows, new_entries):
    T = collections.OrderedDict()
    T[u"P16 の claim"] = len(rows)
    for pf in PROFILES:
        T[u"%s の claim" % pf] = len(new_entries[pf][u"claims"])
        T[u"%s の state の分布(全 claim)" % pf] = _dist(c.get(u"state") for c in new_entries[pf][u"claims"])
        T[u"%s で対応した行" % pf] = sum(1 for r in rows if r[u"%s で対応" % pf])
    pop = [r for r in rows if r[u"札"] == u"真" and r[u"kind"] == u"num"]
    T[u"札 真・num の行"] = len(pop)
    for pf in PROFILES:
        T[u"P16 → %s の state(札 真・num)" % pf] = collections.OrderedDict((s, _dist(r[u"%s の state" % pf] for r in pop if r[u"P16 の state"] == s)) for s in STATES)
    s53 = [r for r in rows if r[u"53 行"]]
    T[u"53 行"] = len(s53)
    for pf in PROFILES:
        T[u"53 行の %s の state" % pf] = _dist(r[u"%s の state" % pf] for r in s53)
        T[u"53 行で %s で GROUNDED" % pf] = sum(1 for r in s53 if r[u"%s の state" % pf] == u"GROUNDED")
        T[u"53 行で %s で GROUNDED の id" % pf] = [r[u"id"] for r in s53 if r[u"%s の state" % pf] == u"GROUNDED"]
        T[u"53 行で %s で GROUNDED(型ごと)" % pf] = collections.OrderedDict((t, sum(1 for r in s53 if r[u"型(53 行)"] == t and r[u"%s の state" % pf] == u"GROUNDED")) for t in TYPES_T)
        T[u"53 行で %s で GROUNDED の要素が根拠に在る" % pf] = sum(1 for r in s53 if r[u"%s の state" % pf] == u"GROUNDED" and r[u"%s で GROUNDED の要素が根拠に在る" % pf])
    s12 = [r for r in rows if r[u"12 行"]]
    T[u"12 行"] = len(s12)
    for pf in PROFILES:
        T[u"12 行の %s の state" % pf] = _dist(r[u"%s の state" % pf] for r in s12)
        T[u"12 行で P16 が VALUE_MISMATCH の 9 行のうち %s で GROUNDED" % pf] = sum(1 for r in s12 if r[u"P16 の state"] == u"VALUE_MISMATCH" and r[u"%s の state" % pf] == u"GROUNDED")
        T[u"12 行で R1 が決まった 8 行のうち %s で GROUNDED" % pf] = sum(1 for r in s12 if r[u"R1 の判定(12 行)"] == u"決まる" and r[u"%s の state" % pf] == u"GROUNDED")
        T[u"12 行で %s で GROUNDED の id" % pf] = [r[u"id"] for r in s12 if r[u"%s の state" % pf] == u"GROUNDED"]
    T[u"12 行で P16 が VALUE_MISMATCH"] = sum(1 for r in s12 if r[u"P16 の state"] == u"VALUE_MISMATCH")
    s8 = [r for r in rows if r[u"8 行"]]
    T[u"8 行"] = len(s8)
    for pf in PROFILES:
        T[u"8 行の %s の state" % pf] = _dist(r[u"%s の state" % pf] for r in s8)
        T[u"8 行で %s で GROUNDED" % pf] = sum(1 for r in s8 if r[u"%s の state" % pf] == u"GROUNDED")
        T[u"8 行の %s の期" % pf] = collections.OrderedDict((k, sum(1 for r in s8 if r[u"%s の期" % pf] == k)) for k in (u"当期", u"前期", u"他", None))
        T[u"8 行の %s の state と期(id ごと)" % pf] = collections.OrderedDict((r[u"id"], u"%s / %s" % (r[u"%s の state" % pf], r[u"%s の期" % pf])) for r in s8)
    g249 = [r for r in rows if r[u"249 行(P16 で GROUNDED・札 真・num)"]]
    T[u"249 行"] = len(g249)
    for pf in PROFILES:
        T[u"249 行で %s で GROUNDED でなくなった" % pf] = sum(1 for r in g249 if r[u"%s の state" % pf] != u"GROUNDED")
        T[u"249 行で %s で GROUNDED でなくなった id" % pf] = [r[u"id"] for r in g249 if r[u"%s の state" % pf] != u"GROUNDED"]
        T[u"249 行で %s で GROUNDED でなくなった state" % pf] = _dist(r[u"%s の state" % pf] for r in g249 if r[u"%s の state" % pf] != u"GROUNDED")
    both = [r for r in rows if r[u"P27E と P27 で state が違う"] is not None]
    T[u"P27E と P27 で state が違う行"] = sum(1 for r in both if r[u"P27E と P27 で state が違う"])
    T[u"P27E と P27 で state が違う id"] = [r[u"id"] for r in both if r[u"P27E と P27 で state が違う"]]
    T[u"P27E と P27 で state が違う行(P27E → P27)"] = collections.OrderedDict((r[u"id"], u"%s → %s" % (r[u"P27E の state"], r[u"P27 の state"])) for r in both if r[u"P27E と P27 で state が違う"])
    for pf in PROFILES:
        gr = [r for r in pop if r[u"%s の state" % pf] == u"GROUNDED"]
        T[u"%s で GROUNDED の 札 真・num" % pf] = len(gr)
        T[u"%s で GROUNDED の 札 真・num のうち要素が根拠に無い" % pf] = sum(1 for r in gr if r[u"%s で GROUNDED の要素が根拠に在る" % pf] is False)
        T[u"%s で GROUNDED の 札 真・num のうち要素が根拠に無い id" % pf] = [r[u"id"] for r in gr if r[u"%s で GROUNDED の要素が根拠に在る" % pf] is False]
        T[u"%s で GROUNDED の 札 真・num のうち要素が根拠に無い(根拠の形ごと。参考)" % pf] = collections.OrderedDict(
            (f, sum(1 for r in gr if r[u"%s で GROUNDED の要素が根拠に在る" % pf] is False and r[u"根拠の形(参考)"] == f)) for f in GROUNDS_FORMS)
    fake = [r for r in rows if r[u"札"] == u"偽"]
    T[u"札 偽 の行"] = collections.OrderedDict((r[u"id"], collections.OrderedDict([(u"P16", r[u"P16 の state"])] + [(pf, r[u"%s の state" % pf]) for pf in PROFILES])) for r in fake)
    T[u"札 偽 が P27E・P27 とも GROUNDED でない"] = all(r[u"%s の state" % pf] != u"GROUNDED" for r in fake for pf in PROFILES) if fake else None
    T[u"判定不能 の行"] = sum(1 for r in rows if r[u"札"] == u"判定不能")
    T[u"札の無い行(P16 の entry にあって札に無い)"] = sum(1 for r in rows if r[u"札"] is None)
    return T


def judge(T, align_counts):
    b = BOUNDS
    J = collections.OrderedDict()
    J[u"M-1"] = dict(T[u"P27 の state の分布(全 claim)"]) == dict(b[u"M-1"])  # 並びの順は比べない(中身だけ)
    J[u"M-2"] = all(align_counts[pf][u"同じ位置で対応"] == b[u"M-2"] and align_counts[pf][u"対応しない P16 の行"] == 0 for pf in PROFILES) and T[u"P16 の claim"] == b[u"M-2"]
    J[u"M-3"] = b[u"M-3"][0] <= T[u"53 行で P27E で GROUNDED"] <= b[u"M-3"][1]
    J[u"M-4"] = b[u"M-4"][0] <= T[u"249 行で P27E で GROUNDED でなくなった"] <= b[u"M-4"][1]
    J[u"M-5"] = b[u"M-5"][0] <= T[u"8 行で P27E で GROUNDED"] <= b[u"M-5"][1]
    J[u"M-6"] = b[u"M-6"][0] <= T[u"12 行で P16 が VALUE_MISMATCH の 9 行のうち P27E で GROUNDED"] <= b[u"M-6"][1]
    J[u"M-7"] = b[u"M-7"][0] <= T[u"P27E と P27 で state が違う行"] <= b[u"M-7"][1]
    J[u"M-8"] = T[u"札 偽 が P27E・P27 とも GROUNDED でない"] is True
    J[u"M-9"] = b[u"M-9"][0] <= T[u"P27E で GROUNDED の 札 真・num のうち要素が根拠に無い"] <= b[u"M-9"][1]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"M-10"] = u"判定しない"
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


def record_key_leaks(obj):
    t = json.dumps(obj, ensure_ascii=False)
    return sorted(set(p for p in KEY_PATTERNS if re.search(p, t)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args(argv)
    outs = [a.out] + [os.path.join(ROOT, rel) for rel in ENTRY_REL.values()]
    for p in outs:
        if os.path.exists(p):
            raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % p)
    shas = collections.OrderedDict()
    for k, (rel, want) in MATERIALS.items():
        got = sha256_file(os.path.join(ROOT, rel))
        if got != want:
            raise Stop(u"%s の sha256 が封と違う: %s" % (rel, got))
        shas[rel] = got
    ldir, labels_ok = check_labels(os.path.join(ROOT, MATERIALS[u"label_list"][0]))
    if not all(v[u"在る"] and v[u"sha256 が名簿と合う"] for v in labels_ok.values()):
        raise Stop(u"ラベル file が cache に無いか sha256 が名簿と合わない: %s" % json.dumps(labels_ok, ensure_ascii=False))
    bundle_sha, n_files, dirty = engine_bundle()
    if dirty:
        raise Stop(u"engine(core/・adapters/)に未 commit の変更が %d file ある。止める" % dirty)
    with io.open(os.path.join(ROOT, MATERIALS[u"zip"][0]), "rb") as fh:
        zb = fh.read()
    new_entries = collections.OrderedDict()
    for pf in PROFILES:
        new_entries[pf] = scrub(run_engine(zb, pf))
        text = json.dumps(new_entries[pf], ensure_ascii=False)
        if DOCID_RE.search(text):
            raise Stop(u"%s の entry に docID が残った" % pf)
    entry16 = jload(os.path.join(ROOT, MATERIALS[u"entry16"][0]))
    labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, MATERIALS[u"labels"][0]))[u"labels"]}
    stopped = jload(os.path.join(ROOT, MATERIALS[u"stopped"][0]))
    other = jload(os.path.join(ROOT, MATERIALS[u"other"][0]))
    period = jload(os.path.join(ROOT, MATERIALS[u"period"][0]))
    sets = {
        u"53": collections.OrderedDict((r[u"id"], r[u"型"]) for r in stopped[u"行"]),
        u"12": collections.OrderedDict((r[u"id"], r[u"R1 の判定"]) for r in other[u"行"] if r[u"その他の行"] and r[u"札"] == u"真"),
        u"8": collections.OrderedDict((r[u"id"], True) for r in period[u"行"] if r.get(u"取り違えの中身(参考)") == u"札が文の期と合う(engine の期の取り違え)" and r.get(u"取り違え(engine)") == u"前期の文 × engine 当期"),
    }
    rows, align_counts = build_rows(entry16, new_entries, labels, sets)
    T = tally(rows, new_entries)
    W = collections.OrderedDict()
    W[u"(a) 材料の sha256 が封の値"] = True
    W[u"(b) ラベル file(cache。repo の外)"] = labels_ok
    W[u"(c) engine の bundle の sha256(core/・adapters/)"] = bundle_sha
    W[u"(c) engine の file の数"] = n_files
    W[u"(c) engine の未 commit の file"] = dirty
    W[u"(d) 53 行・12 行・8 行の数"] = collections.OrderedDict([(u"53", len(sets[u"53"])), (u"12", len(sets[u"12"])), (u"8", len(sets[u"8"]))])
    W[u"(e) 行の対応"] = align_counts
    W[u"(f) P27 の state の分布が儀式の記録の素の書類と一致"] = (dict(T[u"P27 の state の分布(全 claim)"]) == dict(RITUAL_PLAIN))
    W[u"通った"] = bool(W[u"(d) 53 行・12 行・8 行の数"] == collections.OrderedDict([(u"53", 53), (u"12", 12), (u"8", 8)]) and dirty == 0
                      and all(align_counts[pf][u"対応しない P16 の行"] == 0 for pf in PROFILES))
    rec = collections.OrderedDict()
    rec[u"注意"] = (u"同梱の AI の文の書類を engine(変えていない)で P27E と P27 で判定し、P16 の記録と行を対応させて state の動きを数えた記録。"
                  u"1 書類・1 model の AI の文。docID は書かない。")
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT}
    rec[u"HEAD の commit"] = git_head()
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"読んだ材料の sha256"] = shas
    rec[u"書いた entry"] = collections.OrderedDict((pf, rel) for pf, rel in ENTRY_REL.items())
    rec[u"定数"] = collections.OrderedDict([(u"profile", list(PROFILES)), (u"行の対応の鍵", u"(span, value, unit)。id の順で同じ位置、違えば探し直す"),
                                         (u"儀式の記録の素の書類の分布(M-1)", RITUAL_PLAIN), (u"予測の幅", BOUNDS)])
    rec[u"配線の門"] = W
    rec[u"行"] = rows
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T, align_counts)
    rec[u"limits"] = [u"1 書類・1 model の AI の文。P27 / P27E の数はこの書類の数",
                     u"札の根拠との照らしは local name の部分文字列。「同」で略した根拠と数式の根拠(導出の文)では当たらない(「根拠の形(参考)」の内訳を見る)",
                     u"engine の変更はこの便にない。P27E を既定にするかは人間が決める"]
    rec[u"key_leaks"] = record_key_leaks(rec)
    text = json.dumps(rec, ensure_ascii=False)
    if DOCID_RE.search(text):
        raise Stop(u"記録に docID が入った")
    for pf, rel in ENTRY_REL.items():
        with io.open(os.path.join(ROOT, rel), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(new_entries[pf], ensure_ascii=False, indent=1) + "\n")
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print(u"written: %s" % a.out)
    print(json.dumps(W, ensure_ascii=False)[:900])
    for k in (u"P27E の state の分布(全 claim)", u"P27 の state の分布(全 claim)", u"53 行で P27E で GROUNDED", u"53 行で P27 で GROUNDED", u"53 行で P27E で GROUNDED(型ごと)",
              u"12 行で P16 が VALUE_MISMATCH の 9 行のうち P27E で GROUNDED", u"8 行で P27E で GROUNDED", u"8 行の P27E の state と期(id ごと)",
              u"249 行で P27E で GROUNDED でなくなった", u"249 行で P27 で GROUNDED でなくなった", u"P27E と P27 で state が違う行(P27E → P27)",
              u"P27E で GROUNDED の 札 真・num のうち要素が根拠に無い", u"P27E で GROUNDED の 札 真・num のうち要素が根拠に無い(根拠の形ごと。参考)", u"札 偽 の行"):
        print(k, json.dumps(T[k], ensure_ascii=False))
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
