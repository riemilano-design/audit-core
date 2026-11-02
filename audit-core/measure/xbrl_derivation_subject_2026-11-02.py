# -*- coding: utf-8 -*-
u"""主語の制約つきの導出(封 docs/XBRL_DERIVATION_SUBJECT_SEAL_2026-11-02.md)。

前の便(全探索。measure/xbrl_derivation_full_2026-11-02.py)の fact の読み方・導出 6 型・帯・判定をそのまま使い(importlib で読む。
式は写し直さない)、候補を engine の記録(P16)の pointer から取った主語の要素 S とその計算リンクの近傍 N(S)(深さ 1)に限る。
材料は全部 repo の中(封 §0 の 6 file。sha256 を照らす)。engine(core/・adapters/)は import しない。通信しない。

    python3 measure/xbrl_derivation_subject_2026-11-02.py [--out fixtures/xbrl/derivation_subject_2026-11-02.json]

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- 手がかり A3 の「文の窓が重なる」は、一方の 文 の先頭 12 字か末尾 12 字が他方の 文 に含まれること(封 §1 の字どおり)。文 が 12 字未満なら重ならない。
- D4 の候補は前の便の script が「親」の名を候補に持つので、それを N と照らす。D5 は分子・分母の両方、D6 は金額(候補の fact の 1 つ目)だけ。
- 対照 249 は S = A1 ∪ A3(封 §2)。母数 53 は S = A1 ∪ A2 ∪ A3(A2 は A1 が空のときだけ)。
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

SEAL_REL = "docs/XBRL_DERIVATION_SUBJECT_SEAL_2026-11-02.md"
SEAL_COMMIT = "ab09aa6"
OUT_REL = "fixtures/xbrl/derivation_subject_2026-11-02.json"
MATERIALS = collections.OrderedDict([
    (u"claims", ("fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json", "c886a9e69353c677297341436f9777b779895054804adce1805f3d546dd4b579")),
    (u"labels", ("fixtures/xbrl/ai_prose_labels_2026-10-09.json", "7eac1450c40c68e0a25bf7f56c32db4ee6dad226e55df7efdb8019764a71173b")),
    (u"entry", ("fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json", "6c4c65d1d24ed46250d6bda41fc023d0624ec130f9c1fe791e840c6def7077da")),
    (u"zip", ("fixtures/xbrl/ai_prose_instance_2026-10-09.zip", "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799")),
    (u"prev_rec", ("fixtures/xbrl/derivation_full_2026-11-02.json", "2f16f3069165ec03a853387f8f5a677bb2204af74d4bad8f52e1474c3155a0ea")),
    (u"prev_script", ("measure/xbrl_derivation_full_2026-11-02.py", "7bcfafa99c300e97f72a887c8914564fb1e7779e84b414e15c6f9d806e4e3670")),
])
VERDICTS = (u"導出一致", u"保留", u"不一致")
NO_CLUE = u"手がかりなし"
TYPES = (u"D1", u"D2", u"D3", u"D4", u"D5", u"D6")
WINDOW = 12          # 封 §1 A3: 文の窓の先頭 / 末尾の字数
NEIGHBOURS = 3       # 封 §1 A3: entry の並びで前後 3 つ以内
BOUNDS = {u"E-1": (14, 24), u"E-2": (4, 12), u"E-3": (3, 10), u"E-4": (10, 18), u"E-5": (6, 8), u"E-6": 70.0, u"E-7": 90.0, u"E-8": (1, 3), u"E-9": (5, 7)}
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


def load_prev():
    u"""前の便の script を importlib で読む(engine ではない。measure/ の中)。"""
    spec = importlib.util.spec_from_file_location("derivation_full_prev", os.path.join(ROOT, MATERIALS[u"prev_script"][0]))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 封 §1: 手がかり

def elems_of(pointers):
    u"""pointer の字 'xbrl:<prefix>:<LocalName>@<context>' から '<prefix>:<LocalName>'。xbrl: で始まり @ を含むものだけ(導出の印は捨てる)。"""
    out = []
    for p in pointers or []:
        if isinstance(p, str) and p.startswith("xbrl:") and "@" in p:
            e = p[len("xbrl:"):].split("@")[0]
            if e not in out:
                out.append(e)
    return out


def window_overlap(a, b):
    a, b = a or u"", b or u""
    if len(a) < WINDOW or len(b) < WINDOW:
        return False
    return a[:WINDOW] in b or a[-WINDOW:] in b or b[:WINDOW] in a or b[-WINDOW:] in a


def subject_dict(entry_claims):
    u"""A2: subject の字 → engine が結んだ要素の和(entry の全 claim)。"""
    d = collections.defaultdict(list)
    for c in entry_claims:
        if c.get(u"subject"):
            for e in elems_of(c.get(u"pointers")):
                if e not in d[c[u"subject"]]:
                    d[c[u"subject"]].append(e)
    return d


def anchors(cid, entry_claims, pos, texts, subj, use_a2):
    c = entry_claims[pos[cid]]
    a1 = elems_of(c.get(u"pointers"))
    a2 = list(subj.get(c.get(u"subject"), [])) if (use_a2 and not a1 and c.get(u"subject")) else []
    a3 = []
    i = pos[cid]
    me = (texts.get(cid) or {}).get(u"文")
    for j in range(max(0, i - NEIGHBOURS), min(len(entry_claims), i + NEIGHBOURS + 1)):
        if j == i:
            continue
        o = entry_claims[j]
        if o.get(u"kind") != "num":
            continue
        if window_overlap(me, (texts.get(o[u"id"]) or {}).get(u"文")):
            for e in elems_of(o.get(u"pointers")):
                if e not in a3:
                    a3.append(e)
    S = []
    for e in a1 + a2 + a3:
        if e not in S:
            S.append(e)
    return collections.OrderedDict([(u"A1", a1), (u"A2", a2), (u"A3", a3)]), S


# ---------------------------------------------------------------- 封 §2: 近傍と制約

def neighbourhood(S, arcs):
    u"""N(S) = S ∪ 親 ∪ 子 ∪ 兄弟(親の子)。深さ 1。"""
    N = list(S)
    for s in S:
        parents = [p for p, ch in arcs.items() if s in ch]
        for p in parents:
            if p not in N:
                N.append(p)
            for sib in arcs[p]:
                if sib not in N:
                    N.append(sib)
        for ch in arcs.get(s, {}):
            if ch not in N:
                N.append(ch)
    return N


def keep(c, N):
    names = [f[u"name"] for f in c[u"fact"]]
    k = c[u"型"]
    if k in (u"D1", u"D2", u"D3"):
        return names[0] in N
    if k == u"D4":
        return c.get(u"親") in N or all(n in N for n in names)
    if k == u"D5":
        return names[0] in N and names[1] in N
    if k == u"D6":
        return names[0] in N
    return False


def verdict_of(n):
    return u"導出一致" if n == 1 else u"保留" if n >= 2 else u"不一致"


def grounds_have_values(grounds, c, idx):
    u"""参考(判定には使わない。封の予測の対象でもない): 札の根拠の字に、候補の fact の値(絶対値の整数部を 3 桁区切りで。
    例 506,218,000)が全部含まれるか。根拠が「同/前期=62,235,000円」のように要素名を書かず値だけ書く札を拾うための欄。
    2026-11-02 の 1 回目の走らせには無く、2 回目で足した(判定・集計の他の欄は不変)。"""
    g = grounds or u""
    vals = []
    for f in c[u"fact"]:
        v = idx_value(idx, f)
        if v is None:
            return None
        vals.append(u"{:,}".format(int(abs(v))))
    return all(s in g for s in vals)


def idx_value(idx, ref):
    for f in idx.by_name_unit.get((ref[u"name"], ref[u"unit"]), []):
        if f[u"context"] == ref[u"context"]:
            return f[u"value"]
    return None


def same_candidate(a, b):
    return a is not None and b is not None and a[u"型"] == b[u"型"] and [dict(f) for f in a[u"fact"]] == [dict(f) for f in b[u"fact"]]


def build_rows(prev, prev_rows, entry_claims, labels, texts, idx):
    pos = {c[u"id"]: i for i, c in enumerate(entry_claims)}
    subj = subject_dict(entry_claims)
    rows = []
    for pr in prev_rows:
        cid = pr[u"id"]
        c = entry_claims[pos[cid]]
        tx = texts[cid]
        lab = labels[cid]
        u0, found = prev.written_granularity(tx.get(u"文"), tx[u"数"], tx[u"単位"])
        cands, u, t = prev.derive({u"unit": tx[u"単位"], u"value": tx[u"数"], u"u": u0}, idx)
        A, S = anchors(cid, entry_claims, pos, texts, subj, use_a2=bool(pr[u"母数"]))
        N = neighbourhood(S, idx.arcs)
        kept = [x for x in cands if keep(x, N)] if S else []
        row = collections.OrderedDict([(u"id", cid), (u"札", lab[u"札"]), (u"state", c[u"state"]), (u"unit", tx[u"単位"]), (u"value", tx[u"数"]),
                                       (u"母数", pr[u"母数"]), (u"対照", pr[u"対照"]), (u"u", u), (u"t'", t),
                                       (u"手がかり", A), (u"S", S), (u"手がかりあり", bool(S)),
                                       (u"手がかりの出所", u"A1" if A[u"A1"] else u"A2" if A[u"A2"] else u"A3" if A[u"A3"] else u"なし"),
                                       (u"N の大きさ", len(N)), (u"N", N),
                                       (u"全探索の候補の数", len(cands)), (u"全探索の候補の数が前の便の記録と一致", len(cands) == pr[u"候補の数"]),
                                       (u"全探索の判定", pr[u"判定"]),
                                       (u"制約つきの候補の数", len(kept)), (u"型ごとの候補の数", collections.OrderedDict((k, sum(1 for x in kept if x[u"型"] == k)) for k in TYPES)),
                                       (u"判定", verdict_of(len(kept)) if S else NO_CLUE),
                                       (u"候補", kept[:20]), (u"候補が 20 を超えた", len(kept) > 20), (u"recomputed", c.get(u"recomputed"))])
        rc = c.get(u"recomputed")
        tol = None if rc is None else max(1e-6 * abs(float(rc)), 0.5 * (10.0 ** (-prev.decimals_of(rc))))
        row[u"D1 に recomputed の値が在る"] = (rc is not None and any(x[u"型"] == u"D1" and abs(abs(x[u"v"]) - abs(float(rc))) <= tol for x in kept))
        row[u"どの型かに recomputed の値が在る"] = (rc is not None and any(abs(abs(x[u"v"]) - abs(float(rc))) <= tol for x in kept))
        if row[u"判定"] == u"導出一致":
            row[u"根拠に要素名"] = any(f[u"name"].split(":")[-1] in (lab.get(u"根拠") or u"") for f in kept[0][u"fact"])
            row[u"根拠に候補の fact の値"] = grounds_have_values(lab.get(u"根拠"), kept[0], idx)
            row[u"全探索の導出一致と同じ候補"] = same_candidate(kept[0], pr[u"候補"][0]) if pr[u"判定"] == u"導出一致" else None
        else:
            row[u"根拠に要素名"] = None
            row[u"根拠に候補の fact の値"] = None
            row[u"全探索の導出一致と同じ候補"] = None
        rows.append(row)
    return rows


def _cnt(items):
    c = collections.Counter(items)
    return collections.OrderedDict(sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0]))))


def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def tally(rows):
    T = collections.OrderedDict()
    pop = [r for r in rows if r[u"母数"]]
    ctl = [r for r in rows if r[u"対照"]]
    clue = [r for r in pop if r[u"手がかりあり"]]
    none = [r for r in pop if not r[u"手がかりあり"]]
    T[u"母数"] = len(pop)
    T[u"対照"] = len(ctl)
    T[u"全探索の候補の数が前の便の記録と一致した行"] = sum(1 for r in rows if r[u"全探索の候補の数が前の便の記録と一致"])
    T[u"手がかりあり"] = len(clue)
    T[u"手がかりなし"] = len(none)
    T[u"手がかりの出所"] = _cnt(r[u"手がかりの出所"] for r in pop)
    T[u"手がかりありの unit"] = _cnt(r[u"unit"] for r in clue)
    T[u"手がかりありの S の大きさ"] = _cnt(len(r[u"S"]) for r in clue)
    T[u"手がかりありの N の大きさ"] = _cnt(min(r[u"N の大きさ"], 21) for r in clue)
    T[u"手がかりなしの全探索の判定"] = _cnt(r[u"全探索の判定"] for r in none)
    T[u"手がかりありの判定"] = collections.OrderedDict((v, sum(1 for r in clue if r[u"判定"] == v)) for v in VERDICTS)
    T[u"遷移(全探索 → 制約つき。手がかりあり)"] = collections.OrderedDict(
        (u"%s → %s" % (a, b), sum(1 for r in clue if r[u"全探索の判定"] == a and r[u"判定"] == b)) for a in VERDICTS for b in VERDICTS)
    held = [r for r in clue if r[u"全探索の判定"] == u"保留"]
    T[u"全探索で保留(手がかりあり)"] = len(held)
    T[u"全探索で保留のうち制約で導出一致"] = sum(1 for r in held if r[u"判定"] == u"導出一致")
    T[u"全探索で保留のうち制約で不一致"] = sum(1 for r in held if r[u"判定"] == u"不一致")
    was_one = [r for r in clue if r[u"全探索の判定"] == u"導出一致"]
    T[u"全探索で導出一致(手がかりあり)"] = len(was_one)
    T[u"全探索で導出一致のうち同じ候補で導出一致"] = sum(1 for r in was_one if r[u"全探索の導出一致と同じ候補"] is True)
    T[u"全探索で導出一致のうち制約で不一致"] = sum(1 for r in was_one if r[u"判定"] == u"不一致")
    one = [r for r in clue if r[u"判定"] == u"導出一致"]
    T[u"導出一致の型"] = _cnt(r[u"候補"][0][u"型"] for r in one)
    T[u"導出一致で根拠に要素名"] = sum(1 for r in one if r[u"根拠に要素名"])
    T[u"導出一致で根拠に要素名の割合"] = pct(T[u"導出一致で根拠に要素名"], len(one))
    T[u"導出一致で根拠に候補の fact の値(参考)"] = sum(1 for r in one if r[u"根拠に候補の fact の値"])
    T[u"導出一致で根拠に要素名か値のどちらか(参考)"] = sum(1 for r in one if r[u"根拠に要素名"] or r[u"根拠に候補の fact の値"])
    T[u"導出一致の id と候補の要素"] = collections.OrderedDict((r[u"id"], [f[u"name"] for f in r[u"候補"][0][u"fact"]]) for r in one)
    T[u"不一致の id と全探索の候補の数"] = collections.OrderedDict((r[u"id"], r[u"全探索の候補の数"]) for r in clue if r[u"判定"] == u"不一致")
    T[u"保留の候補の数の分布"] = _cnt(min(r[u"制約つきの候補の数"], 21) for r in clue if r[u"判定"] == u"保留")
    T[u"対照のうち D1 に recomputed の値が在る"] = sum(1 for r in ctl if r[u"D1 に recomputed の値が在る"])
    T[u"対照のうち どの型かに recomputed の値が在る"] = sum(1 for r in ctl if r[u"どの型かに recomputed の値が在る"])
    T[u"対照の割合(型を問わず)"] = pct(T[u"対照のうち どの型かに recomputed の値が在る"], len(ctl))
    T[u"対照で再現しなかった行の id"] = [r[u"id"] for r in ctl if not r[u"どの型かに recomputed の値が在る"]]
    T[u"対照の判定"] = collections.OrderedDict((v, sum(1 for r in ctl if r[u"判定"] == v)) for v in VERDICTS + (NO_CLUE,))
    pc = [r for r in clue if r[u"unit"] == u"%"]
    T[u"% の手がかりあり"] = len(pc)
    T[u"% のうち導出一致"] = sum(1 for r in pc if r[u"判定"] == u"導出一致")
    many = [r for r in clue if r[u"全探索の候補の数"] > 20]
    T[u"全探索で候補 20 超(手がかりあり)"] = len(many)
    T[u"全探索で候補 20 超のうち制約後 3 以下"] = sum(1 for r in many if r[u"制約つきの候補の数"] <= 3)
    T[u"全探索で候補 20 超の制約後の候補の数"] = collections.OrderedDict((r[u"id"], r[u"制約つきの候補の数"]) for r in many)
    T[u"母数の id と判定"] = collections.OrderedDict((r[u"id"], [r[u"全探索の判定"], r[u"判定"]]) for r in pop)
    return T


def judge(T):
    J = collections.OrderedDict()
    J[u"E-1"] = BOUNDS[u"E-1"][0] <= T[u"手がかりありの判定"][u"導出一致"] <= BOUNDS[u"E-1"][1]
    J[u"E-2"] = BOUNDS[u"E-2"][0] <= T[u"手がかりありの判定"][u"保留"] <= BOUNDS[u"E-2"][1]
    J[u"E-3"] = BOUNDS[u"E-3"][0] <= T[u"手がかりありの判定"][u"不一致"] <= BOUNDS[u"E-3"][1]
    J[u"E-4"] = BOUNDS[u"E-4"][0] <= T[u"全探索で保留のうち制約で導出一致"] <= BOUNDS[u"E-4"][1]
    J[u"E-5"] = BOUNDS[u"E-5"][0] <= T[u"全探索で導出一致のうち同じ候補で導出一致"] <= BOUNDS[u"E-5"][1]
    J[u"E-6"] = T[u"導出一致で根拠に要素名の割合"] is not None and T[u"導出一致で根拠に要素名の割合"] >= BOUNDS[u"E-6"]
    J[u"E-7"] = T[u"対照の割合(型を問わず)"] is not None and T[u"対照の割合(型を問わず)"] >= BOUNDS[u"E-7"]
    J[u"E-8"] = BOUNDS[u"E-8"][0] <= T[u"% のうち導出一致"] <= BOUNDS[u"E-8"][1]
    J[u"E-9"] = BOUNDS[u"E-9"][0] <= T[u"全探索で候補 20 超のうち制約後 3 以下"] <= BOUNDS[u"E-9"][1]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"E-10"] = u"判定しない"
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
    prev = load_prev()
    prev_rec = jload(os.path.join(ROOT, MATERIALS[u"prev_rec"][0]))
    texts = {x[u"id"]: x for x in jload(os.path.join(ROOT, MATERIALS[u"claims"][0]))[u"claims"]}
    labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, MATERIALS[u"labels"][0]))[u"labels"]}
    entry = jload(os.path.join(ROOT, MATERIALS[u"entry"][0]))
    zpath = os.path.join(ROOT, MATERIALS[u"zip"][0])
    facts, counts = prev.parse_facts(zpath)
    arcs, n_arcs = prev.parse_cal(zpath)
    idx = prev.Index(facts, arcs)
    rows = build_rows(prev, prev_rec[u"行"], entry[u"claims"], labels, texts, idx)
    T = tally(rows)
    T.update(prev.count_unjudged(entry[u"claims"], labels, texts, prev_rec[u"行"]))
    W = collections.OrderedDict()
    W[u"(a) 材料の sha256 が封の値"] = True
    W[u"(b) 前の便の記録の行が 302・母数 53・対照 249"] = (len(prev_rec[u"行"]) == 302 and T[u"母数"] == 53 and T[u"対照"] == 249)
    W[u"(c) entry の profile"] = entry.get(u"profile")
    W[u"(d) fact の読み取り(前の便と同じ関数)"] = counts
    W[u"(d) 計算リンクの arc"] = n_arcs
    W[u"(e) 全探索の候補の数が前の便の記録と一致した行"] = T[u"全探索の候補の数が前の便の記録と一致した行"]
    W[u"(f) 手がかりあり 34・なし 19(封 §1 の層)"] = (T[u"手がかりあり"] == 34 and T[u"手がかりなし"] == 19)
    W[u"(f) 手がかりの出所"] = T[u"手がかりの出所"]
    W[u"(g) 対照のどの型かが recomputed を再現した割合"] = T[u"対照の割合(型を問わず)"]
    W[u"通った"] = bool(W[u"(a) 材料の sha256 が封の値"] and W[u"(b) 前の便の記録の行が 302・母数 53・対照 249"]
                      and W[u"(e) 全探索の候補の数が前の便の記録と一致した行"] == 302 and W[u"(f) 手がかりあり 34・なし 19(封 §1 の層)"])
    rec = collections.OrderedDict()
    rec[u"注意"] = (u"AI の文の数字の導出(前の便の 6 型)を、engine の記録の pointer から取った主語の要素とその計算リンクの近傍に限って数え直した記録。"
                  u"近傍で 1 つに決まっても出所として正しいとは言えない。1 書類・1 model の AI の文。P16 の判定。docID は書かない。")
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT}
    rec[u"HEAD の commit"] = git_head()
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"読んだ材料の sha256"] = shas
    rec[u"定数"] = collections.OrderedDict([(u"手がかり", [u"A1 自身の pointer", u"A2 同じ主語の字に engine が結んだ要素(A1 が空のとき)", u"A3 前後 3 つ以内で文の窓(12 字)が重なる主張の pointer"]),
                                         (u"近傍", u"S ∪ 親 ∪ 子 ∪ 兄弟(深さ 1)"), (u"残す条件", {u"D1・D2・D3": u"要素 ∈ N", u"D4": u"親 ∈ N または子の全部 ∈ N", u"D5": u"分子・分母 ∈ N", u"D6": u"金額 ∈ N"}),
                                         (u"対照の手がかり", u"A1 ∪ A3"), (u"予測の幅", BOUNDS), (u"候補の保存", u"行ごとに先頭 20 まで(数は全部数える)")])
    rec[u"配線の門"] = W
    rec[u"行"] = rows
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T)
    rec[u"limits"] = [u"近傍で 1 つに決まっても出所として正しいとは言えない", u"手がかりなし 19 件には何も言えない", u"1 書類・1 model の AI の文。P16 の判定",
                     u"制約つきの導出を engine に入れるかは人間が決める"]
    rec[u"key_leaks"] = record_key_leaks(rec)
    text = json.dumps(rec, ensure_ascii=False)
    if DOCID_RE.search(text):
        raise Stop(u"記録に docID が入った")
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print(u"written: %s" % a.out)
    print(json.dumps(W, ensure_ascii=False)[:700])
    print(json.dumps(T[u"手がかりありの判定"], ensure_ascii=False), json.dumps(T[u"遷移(全探索 → 制約つき。手がかりあり)"], ensure_ascii=False))
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
