# -*- coding: utf-8 -*-
u"""「その他」の行の主語の結びつき(封 docs/XBRL_OTHER_RULE_SEAL_2026-11-02.md)。

engine を変えずに、封 §2 の規則 R0(全部の Other)/ R1(engine の近傍の Other)を AI の文の「その他」の行に当て、
何件が 1 つに決まり、決めた fact が札の根拠と合うかを数える。fact と計算リンクの読み方は全探索の便の script
(measure/xbrl_derivation_full_2026-11-02.py)を importlib で読んで使う。材料は全部 repo の中(封 §0 の 6 file。
sha256 を照らす)。engine(core/・adapters/)は import しない。通信しない。

    python3 measure/xbrl_other_rule_2026-11-02.py [--out fixtures/xbrl/other_rule_2026-11-02.json]

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- 数の位置は 文 の中の正規表現の一致を左から順に見て、字の値 × 倍率が |数| × 数の単位の倍率(claims の 数 は 単位 百万円 の行では百万円の値)
  と相対 1e-6 で一致するものを数える。1 回目の走らせは 数 に倍率を掛け忘れ、百万円 の行 108 が全部「位置なし」になった(追記 1)。
- 「同」の辿りは、文の中でその数より前にある一致(値は問わない。字の数の位置すべて)のうち最も近いものの W で決める。
  辿った W がまた「(同」なら更に前へ(最大 5 回)。
- 期の context: 当期 = "CurrentYear" で始まり "_" を含まない。前期 = "Prior1Year" で始まり "_" を含まない。
- R0 の単位: 文の単位が 円・千円・百万円 なら unitRef JPY の fact だけ。それ以外(%・名 など)は unitRef を問わない。
- R1 の近傍は計算リンクの arcs(親 → 子)で、E・E の親・E の子・E の親の子。E は pointers の 1 つ目の "xbrl:prefix:Local@ctx" の要素。
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SEAL_REL = "docs/XBRL_OTHER_RULE_SEAL_2026-11-02.md"
SEAL_COMMIT = "8d4cf3b"
OUT_REL = "fixtures/xbrl/other_rule_2026-11-02.json"
MATERIALS = collections.OrderedDict([
    (u"claims", ("fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json", "c886a9e69353c677297341436f9777b779895054804adce1805f3d546dd4b579")),
    (u"labels", ("fixtures/xbrl/ai_prose_labels_2026-10-09.json", "7eac1450c40c68e0a25bf7f56c32db4ee6dad226e55df7efdb8019764a71173b")),
    (u"entry", ("fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json", "6c4c65d1d24ed46250d6bda41fc023d0624ec130f9c1fe791e840c6def7077da")),
    (u"zip", ("fixtures/xbrl/ai_prose_instance_2026-10-09.zip", "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799")),
    (u"full_script", ("measure/xbrl_derivation_full_2026-11-02.py", "7bcfafa99c300e97f72a887c8914564fb1e7779e84b414e15c6f9d806e4e3670")),
    (u"prev_rec", ("fixtures/xbrl/derivation_stopped_2026-11-02.json", "cacbdb62a958522f9284cfc026f057ddb8d7be4c8e648f5ad579faa7edd4775e")),
])
NUM_RE = re.compile(u"(△|▲|-)?([\\d,]+(?:\\.\\d+)?)(百万円|千円|円|%|ポイント|名|人|株|社|件)")
SCALE = {u"百万円": 1e6, u"千円": 1e3, u"円": 1.0}
MONEY_UNITS = (u"円", u"千円", u"百万円")
TRAIL = u":" + u":" + u"、はがをでに 　"
OTHER_RE = re.compile(u"その他(の[^、。::()()\\s]{0,8})?$")
POINTER_RE = re.compile(r"^xbrl:([A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+)@([A-Za-z0-9_\-]+)$")
VERDICTS = (u"決まる", u"保留", u"無し")
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
T5_OTHER_IDS = (u"N080", u"N081", u"N144", u"N145", u"N213", u"N290")
BOUNDS = {u"H-1": (8, 20), u"H-2": (0, 3), u"H-3": 40.0, u"H-4": 60.0, u"H-5": 100.0, u"H-6": 6, u"H-7": (0, 2)}
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
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


def load_module(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 封 §1: 「その他」の行の拾い方

def tokens_of(text):
    u"""文の中の数の字(位置・値の大きさ・単位・小数の桁)。"""
    out = []
    for m in NUM_RE.finditer(text or u""):
        digits = m.group(2).replace(u",", u"")
        try:
            val = float(digits)
        except ValueError:
            continue
        unit = m.group(3)
        dec = len(digits.split(u".")[1]) if u"." in digits else 0
        out.append(collections.OrderedDict([(u"start", m.start()), (u"end", m.end()), (u"字", m.group(0)), (u"値", val * SCALE.get(unit, 1.0)),
                                            (u"単位", unit), (u"小数", dec)]))
    return out


def locate(text, value, unit):
    u"""数の位置: 字の値 × 倍率が |数| × 数の単位の倍率 と一致する字の一覧(0 → 位置なし、1 → 決まる、2 以上 → 曖昧)。
    claims の 数 は 単位 が 百万円 の行では百万円の値のまま(円 の行は円)なので、両方を円に揃えて比べる(1 回目の走らせの欠陥。追記 1)。"""
    t = abs(float(value)) * SCALE.get(unit, 1.0)
    toks = tokens_of(text)
    hits = [k for k in toks if abs(k[u"値"] - t) <= 1e-6 * max(1.0, t)]
    return toks, hits


def strip_trail(w):
    return w.rstrip(TRAIL)


def subject_of(text, toks, tok, hops=0):
    u"""直前の字 W を見て、「同」なら直前の数へ辿り、(W, 同か, 主語なしか) を返す。"""
    w = strip_trail(text[:tok[u"start"]])
    if w.endswith(u"(同") or w.endswith(u"(同"):
        prev = [k for k in toks if k[u"end"] <= tok[u"start"]]
        if not prev or hops >= 5:
            return w, True, True
        w2, _, none2 = subject_of(text, toks, prev[-1], hops + 1)
        return w2, True, none2
    return w, False, False


def is_other(w):
    return bool(OTHER_RE.search(w))


def u_of(tok):
    base = SCALE.get(tok[u"単位"], 1.0)
    return base * (10.0 ** (-tok[u"小数"])) if tok[u"小数"] else base


# ---------------------------------------------------------------- 封 §2: 規則

def in_engine_band(v, t, u):
    d = abs(v) - abs(t)
    return (abs(d) <= u / 2.0) or (0 <= d < u)


def period_ok(ctx, prior):
    if u"_" in ctx:
        return False
    return ctx.startswith(u"Prior1Year") if prior else ctx.startswith(u"CurrentYear")


def local_name(name):
    return name.split(u":")[-1]


def r0_candidates(facts, t, u, prior, money):
    out = []
    for f in facts:
        if not local_name(f[u"name"]).startswith(u"Other"):
            continue
        if money and f[u"unit"] != u"JPY":
            continue
        if not period_ok(f[u"context"], prior):
            continue
        if in_engine_band(f[u"value"], t, u):
            out.append(f)
    return out


def neighbourhood(E, arcs):
    N = set([E])
    parents = [p for p, ch in arcs.items() if E in ch]
    N.update(parents)
    N.update(arcs.get(E, {}).keys())
    for p in parents:
        N.update(arcs[p].keys())
    return N


def first_pointer(pointers):
    for p in pointers or []:
        m = POINTER_RE.match(p)
        if m:
            return m.group(1), m.group(2)
    return None


def verdict_of(cands):
    return u"決まる" if len(cands) == 1 else (u"保留" if len(cands) >= 2 else u"無し")


def fact_ref(f):
    return collections.OrderedDict([(u"要素", f[u"name"]), (u"context", f[u"context"]), (u"unit", f[u"unit"]), (u"v", f[u"value"])])


def build_rows(claims, labels, entry_claims, facts, arcs):
    rows = []
    for c in claims:
        cid = c[u"id"]
        lab = labels.get(cid) or {}
        ec = entry_claims.get(cid) or {}
        text = c.get(u"文") or u""
        toks, hits = locate(text, c[u"数"], c.get(u"単位")) if c.get(u"数") is not None else ([], [])   # 数の無い行(text の主張)は位置なし
        r = collections.OrderedDict()
        r[u"id"] = cid
        r[u"札"] = lab.get(u"札")
        r[u"state"] = ec.get(u"state")
        r[u"数"] = c.get(u"数")
        r[u"単位"] = c.get(u"単位")
        r[u"数の位置"] = u"決まる" if len(hits) == 1 else (u"なし" if not hits else u"曖昧")
        r[u"数の字"] = hits[0][u"字"] if len(hits) == 1 else None
        r[u"W"] = None
        r[u"同"] = None
        r[u"同(主語なし)"] = None
        r[u"その他の行"] = False
        r[u"期"] = None
        r[u"u"] = None
        r[u"R0 の候補の数"] = None
        r[u"R0 の判定"] = None
        r[u"R0 の候補"] = []
        r[u"R0 で決まった候補の要素が根拠に在る"] = None
        r[u"engine の要素 E"] = None
        r[u"R1 の近傍の大きさ"] = None
        r[u"R1 の候補の数"] = None
        r[u"R1 の判定"] = None
        r[u"R1 の候補"] = []
        r[u"R1 で決まった候補の要素が根拠に在る"] = None
        r[u"engine の要素が Other"] = None
        r[u"engine の fact が R1 の候補に在る"] = None
        if len(hits) == 1:
            tok = hits[0]
            w, same, none = subject_of(text, toks, tok)
            r[u"W"] = w[-30:]
            r[u"同"] = same
            r[u"同(主語なし)"] = none if same else None
            r[u"その他の行"] = bool(not none and is_other(w))
            if r[u"その他の行"]:
                prior = same
                r[u"期"] = u"前期" if prior else u"当期"
                u = u_of(tok)
                r[u"u"] = u
                t = tok[u"値"]
                money = tok[u"単位"] in MONEY_UNITS
                grounds = lab.get(u"根拠") or u""
                c0 = r0_candidates(facts, t, u, prior, money)
                r[u"R0 の候補の数"] = len(c0)
                r[u"R0 の判定"] = verdict_of(c0)
                r[u"R0 の候補"] = [fact_ref(f) for f in c0[:20]]
                r[u"R0 で決まった候補の要素が根拠に在る"] = (local_name(c0[0][u"name"]) in grounds) if len(c0) == 1 else None
                ptr = first_pointer(ec.get(u"pointers"))
                if ptr:
                    E, ectx = ptr
                    N = neighbourhood(E, arcs)
                    c1 = [f for f in c0 if f[u"name"] in N]
                    r[u"engine の要素 E"] = E
                    r[u"R1 の近傍の大きさ"] = len(N)
                    r[u"R1 の候補の数"] = len(c1)
                    r[u"R1 の判定"] = verdict_of(c1)
                    r[u"R1 の候補"] = [fact_ref(f) for f in c1[:20]]
                    r[u"R1 で決まった候補の要素が根拠に在る"] = (local_name(c1[0][u"name"]) in grounds) if len(c1) == 1 else None
                    r[u"engine の要素が Other"] = local_name(E).startswith(u"Other")
                    r[u"engine の fact が R1 の候補に在る"] = any(f[u"name"] == E and f[u"context"] == ectx for f in c1)
                else:
                    r[u"R1 の判定"] = u"指せず"
        r[u"根拠"] = lab.get(u"根拠")
        r[u"文"] = text
        rows.append(r)
    return rows


# ---------------------------------------------------------------- 封 §3: 数えるもの

def _cnt(items):
    c = collections.Counter(items)
    return collections.OrderedDict(sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0]))))


def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def tally(rows):
    T = collections.OrderedDict()
    T[u"claims"] = len(rows)
    T[u"数の位置"] = collections.OrderedDict((k, sum(1 for r in rows if r[u"数の位置"] == k)) for k in (u"決まる", u"なし", u"曖昧"))
    other_all = [r for r in rows if r[u"その他の行"]]
    T[u"その他の行(札を問わず)"] = len(other_all)
    T[u"その他の行の札の分布"] = _cnt(r[u"札"] for r in other_all)
    pop = [r for r in other_all if r[u"札"] == u"真"]
    T[u"その他の行(札 真)"] = len(pop)
    T[u"その他の行(札 真)の id"] = [r[u"id"] for r in pop]
    T[u"その他の行の期"] = collections.OrderedDict((k, sum(1 for r in pop if r[u"期"] == k)) for k in (u"当期", u"前期"))
    T[u"その他の行の state"] = collections.OrderedDict((s, sum(1 for r in pop if r[u"state"] == s)) for s in STATES)
    T[u"その他の行で GROUNDED の id"] = [r[u"id"] for r in pop if r[u"state"] == u"GROUNDED"]
    T[u"同(主語なし)の行"] = sum(1 for r in rows if r[u"同(主語なし)"])
    T[u"R0 の判定"] = collections.OrderedDict((v, sum(1 for r in pop if r[u"R0 の判定"] == v)) for v in VERDICTS)
    T[u"R0 の候補の数の分布"] = _cnt(r[u"R0 の候補の数"] for r in pop)
    T[u"R0 で決まる割合"] = pct(T[u"R0 の判定"][u"決まる"], len(pop))
    T[u"R0 で決まった行で候補の要素が根拠に在る"] = sum(1 for r in pop if r[u"R0 で決まった候補の要素が根拠に在る"])
    T[u"R1 の判定"] = collections.OrderedDict((v, sum(1 for r in pop if r[u"R1 の判定"] == v)) for v in VERDICTS + (u"指せず",))
    r1 = [r for r in pop if r[u"R1 の判定"] in VERDICTS]
    T[u"R1 を当てた行(pointers あり)"] = len(r1)
    T[u"R1 で決まる割合(pointers あり)"] = pct(T[u"R1 の判定"][u"決まる"], len(r1))
    T[u"R1 で決まった行で候補の要素が根拠に在る"] = sum(1 for r in pop if r[u"R1 で決まった候補の要素が根拠に在る"])
    T[u"R1 で決まった行で候補の要素が根拠に在る割合"] = pct(T[u"R1 で決まった行で候補の要素が根拠に在る"], T[u"R1 の判定"][u"決まる"])
    T[u"R1 で決まった行の id"] = [r[u"id"] for r in pop if r[u"R1 の判定"] == u"決まる"]
    T[u"R1 で決まった行で候補の要素が根拠に無い id"] = [r[u"id"] for r in pop if r[u"R1 の判定"] == u"決まる" and not r[u"R1 で決まった候補の要素が根拠に在る"]]
    T[u"R1 で保留の id"] = [r[u"id"] for r in pop if r[u"R1 の判定"] == u"保留"]
    T[u"R1 で無しの id"] = [r[u"id"] for r in pop if r[u"R1 の判定"] == u"無し"]
    T[u"R1 で指せずの id"] = [r[u"id"] for r in pop if r[u"R1 の判定"] == u"指せず"]
    byid = {r[u"id"]: r for r in rows}
    T[u"配線: T5 の「その他」6 行が その他の行として拾われた"] = sum(1 for i in T5_OTHER_IDS if byid[i][u"その他の行"])
    T[u"配線: T5 の「その他」6 行で R1 が決まる"] = sum(1 for i in T5_OTHER_IDS if byid[i][u"R1 の判定"] == u"決まる")
    T[u"配線: T5 の「その他」6 行の R1 の判定"] = collections.OrderedDict((i, byid[i][u"R1 の判定"]) for i in T5_OTHER_IDS)
    gr = [r for r in pop if r[u"state"] == u"GROUNDED"]
    T[u"GROUNDED の その他の行で engine の要素が Other"] = sum(1 for r in gr if r[u"engine の要素が Other"])
    T[u"GROUNDED の その他の行で engine の fact が R1 の候補に在る"] = sum(1 for r in gr if r[u"engine の fact が R1 の候補に在る"])
    T[u"その他の行(札 偽・判定不能)"] = len(other_all) - len(pop)
    T[u"その他の行(札 真)の単位の分布"] = _cnt(r[u"単位"] for r in pop)
    return T


def judge(T):
    b = BOUNDS
    J = collections.OrderedDict()
    J[u"H-1"] = b[u"H-1"][0] <= T[u"その他の行(札 真)"] <= b[u"H-1"][1]
    J[u"H-2"] = b[u"H-2"][0] <= T[u"その他の行の state"][u"GROUNDED"] <= b[u"H-2"][1]
    J[u"H-3"] = T[u"R0 で決まる割合"] is not None and T[u"R0 で決まる割合"] <= b[u"H-3"]
    J[u"H-4"] = T[u"R1 で決まる割合(pointers あり)"] is not None and T[u"R1 で決まる割合(pointers あり)"] >= b[u"H-4"]
    J[u"H-5"] = T[u"R1 で決まった行で候補の要素が根拠に在る割合"] is not None and T[u"R1 で決まった行で候補の要素が根拠に在る割合"] >= b[u"H-5"]
    J[u"H-6"] = (T[u"配線: T5 の「その他」6 行が その他の行として拾われた"] == b[u"H-6"] and T[u"配線: T5 の「その他」6 行で R1 が決まる"] == b[u"H-6"])
    J[u"H-7"] = b[u"H-7"][0] <= T[u"数の位置"][u"曖昧"] <= b[u"H-7"][1]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"H-8"] = u"判定しない"
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


def record_key_leaks(obj):
    t = json.dumps(obj, ensure_ascii=False)
    return sorted(set(p for p in KEY_PATTERNS if re.search(p, t)))


def git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode().strip() if r.returncode == 0 else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % a.out)
    shas = collections.OrderedDict()
    for k, (rel, want) in MATERIALS.items():
        got = sha256_file(os.path.join(ROOT, rel))
        if got != want:
            raise Stop(u"%s の sha256 が封と違う: %s" % (rel, got))
        shas[rel] = got
    full = load_module(MATERIALS[u"full_script"][0], "derivation_full_for_other_rule")
    claims = jload(os.path.join(ROOT, MATERIALS[u"claims"][0]))[u"claims"]
    labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, MATERIALS[u"labels"][0]))[u"labels"]}
    entry = jload(os.path.join(ROOT, MATERIALS[u"entry"][0]))
    entry_claims = {c[u"id"]: c for c in entry[u"claims"]}
    prev = jload(os.path.join(ROOT, MATERIALS[u"prev_rec"][0]))
    zpath = os.path.join(ROOT, MATERIALS[u"zip"][0])
    facts, counts = full.parse_facts(zpath)
    arcs, n_arcs = full.parse_cal(zpath)
    rows = build_rows(claims, labels, entry_claims, facts, arcs)
    T = tally(rows)
    prev_t5 = [r[u"id"] for r in prev[u"行"] if r[u"型"] == u"T5 別の要素"]
    W = collections.OrderedDict()
    W[u"(a) 材料の sha256 が封の値"] = True
    W[u"(b) claims 415・札 415・entry 412"] = (len(claims) == 415 and len(labels) == 415 and len(entry_claims) == 412)
    W[u"(c) entry の profile"] = entry.get(u"profile")
    W[u"(d) fact の読み取り(全探索の便と同じ関数)"] = counts
    W[u"(d) 計算リンクの arc"] = n_arcs
    W[u"(e) Other で始まる要素の数"] = len(set(f[u"name"] for f in facts if local_name(f[u"name"]).startswith(u"Other")))
    W[u"(f) 前の便の T5 の 7 行に「その他」6 行が入っている"] = all(i in prev_t5 for i in T5_OTHER_IDS)
    W[u"(g) 位置が決まる行"] = T[u"数の位置"][u"決まる"]
    W[u"通った"] = bool(W[u"(a) 材料の sha256 が封の値"] and W[u"(b) claims 415・札 415・entry 412"] and W[u"(f) 前の便の T5 の 7 行に「その他」6 行が入っている"] and W[u"(e) Other で始まる要素の数"] > 0)
    rec = collections.OrderedDict()
    rec[u"注意"] = (u"AI の文の「その他」の行(字の規則で拾う)に、engine を変えずに規則 R0(全部の Other)/ R1(engine の近傍の Other)を当て、1 つに決まる数と"
                  u"札の根拠との一致を数えた記録。engine は走らせていない。1 書類・1 model の AI の文。P16 の判定。docID は書かない。")
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT}
    rec[u"HEAD の commit"] = git_head()
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"読んだ材料の sha256"] = shas
    rec[u"定数"] = collections.OrderedDict([(u"数の字の正規表現", NUM_RE.pattern), (u"その他の正規表現", OTHER_RE.pattern), (u"落とす区切り", TRAIL),
                                         (u"帯", u"engine の帯の形: round |d| ≤ u / 2 か truncate 0 ≤ d < u(d = |v| − |t|)のどちらか"),
                                         (u"期の context", u"当期 = CurrentYear で始まり _ を含まない。前期 = Prior1Year で始まり _ を含まない"),
                                         (u"R1 の近傍", u"E・E の親・E の子・E の親の子(計算リンク)"), (u"T5 の「その他」6 行", list(T5_OTHER_IDS)),
                                         (u"予測の幅", BOUNDS), (u"候補の保存", u"行ごとに先頭 20 まで(数は全部数える)")])
    rec[u"配線の門"] = W
    rec[u"行"] = rows
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T)
    rec[u"limits"] = [u"規則を engine に入れたときの他の claim への影響は測っていない(engine は走らせていない)", u"「その他」の拾い方は字の規則で、書き方を全部は覆わない",
                     u"1 書類・1 model の AI の文。P16 の判定", u"規則を engine に入れるかは人間が決める"]
    rec[u"key_leaks"] = record_key_leaks(rec)
    text = json.dumps(rec, ensure_ascii=False)
    if DOCID_RE.search(text):
        raise Stop(u"記録に docID が入った")
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print(u"written: %s" % a.out)
    print(json.dumps(W, ensure_ascii=False)[:600])
    for k in (u"数の位置", u"その他の行(札を問わず)", u"その他の行の札の分布", u"その他の行(札 真)", u"その他の行(札 真)の id", u"その他の行の期", u"その他の行の state",
              u"R0 の判定", u"R0 の候補の数の分布", u"R0 で決まる割合", u"R1 の判定", u"R1 で決まる割合(pointers あり)", u"R1 で決まった行で候補の要素が根拠に在る",
              u"R1 で決まった行で候補の要素が根拠に無い id", u"R1 で保留の id", u"R1 で無しの id", u"R1 で指せずの id", u"配線: T5 の「その他」6 行の R1 の判定",
              u"GROUNDED の その他の行で engine の要素が Other", u"GROUNDED の その他の行で engine の fact が R1 の候補に在る", u"同(主語なし)の行"):
        print(k, json.dumps(T[k], ensure_ascii=False))
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
