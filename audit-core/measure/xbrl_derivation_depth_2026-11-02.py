# -*- coding: utf-8 -*-
u"""近傍の深さ 2 と型 2 つ(D7 二項の和・D8 比率の差)(封 docs/XBRL_DERIVATION_DEPTH_SEAL_2026-11-02.md)。

前の便(主語の制約。measure/xbrl_derivation_subject_2026-11-02.py)の手がかり S・近傍・残す条件と、前々便(全探索。
measure/xbrl_derivation_full_2026-11-02.py)の fact の読み方・6 型・帯・判定を importlib で読んで使う(写し直さない)。
足すのは、近傍を 2 回たどる K1、D7・D8 を N の中だけで作る K2、両方の K3 と、K0(前の便の記録)からの遷移の数え方。
材料は全部 repo の中(封 §0 の 7 file。sha256 を照らす)。engine(core/・adapters/)は import しない。通信しない。

    python3 measure/xbrl_derivation_depth_2026-11-02.py [--out fixtures/xbrl/derivation_depth_2026-11-02.json]

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- 深さ 2 の近傍 N2 = neighbourhood(neighbourhood(S))(前の便の関数を 2 回)。
- D7 は同じ context の金額(JPY)fact の組で name が違うもの。順序なしなので (a, b) と (b, a) は 1 つ。値が同じ fact が 2 つ在れば 2 つ。
- D8 の context の組は順序なし(c1 < c2 の字の順で 1 つ)。|v| で帯を比べるので符号は問わない(前々便の封 §2 の e = ||v| − t'|)。
- K0 は前の便の記録の行の判定をそのまま使う(測り直さない)。配線として、深さ 1・6 型を同じ関数で出し直し、記録と一致した行の数を書く。
- F-4 の「D8 を含む候補で導出一致」は、判定が導出一致で、その唯一の候補の型が D8 であること。
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

SEAL_REL = "docs/XBRL_DERIVATION_DEPTH_SEAL_2026-11-02.md"
SEAL_COMMIT = "cb3ba0d"
OUT_REL = "fixtures/xbrl/derivation_depth_2026-11-02.json"
MATERIALS = collections.OrderedDict([
    (u"claims", ("fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json", "c886a9e69353c677297341436f9777b779895054804adce1805f3d546dd4b579")),
    (u"labels", ("fixtures/xbrl/ai_prose_labels_2026-10-09.json", "7eac1450c40c68e0a25bf7f56c32db4ee6dad226e55df7efdb8019764a71173b")),
    (u"entry", ("fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json", "6c4c65d1d24ed46250d6bda41fc023d0624ec130f9c1fe791e840c6def7077da")),
    (u"zip", ("fixtures/xbrl/ai_prose_instance_2026-10-09.zip", "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799")),
    (u"prev_rec", ("fixtures/xbrl/derivation_subject_2026-11-02.json", "6703ae50e2fcee8bf6340fc96c89b7bd530b472b5b103efc83e2e40c0eb02de0")),
    (u"prev_script", ("measure/xbrl_derivation_subject_2026-11-02.py", "21f1f19bc2934ea148b72536770c17f901514e2fe4dc085ddd0facc4c440addc")),
    (u"full_script", ("measure/xbrl_derivation_full_2026-11-02.py", "7bcfafa99c300e97f72a887c8914564fb1e7779e84b414e15c6f9d806e4e3670")),
])
CONDITIONS = (u"K1", u"K2", u"K3")
DEPTH = {u"K1": 2, u"K2": 1, u"K3": 2}
EXTRA = {u"K1": False, u"K2": True, u"K3": True}
VERDICTS = (u"導出一致", u"保留", u"不一致")
NO_CLUE = u"手がかりなし"
TYPES = (u"D1", u"D2", u"D3", u"D4", u"D5", u"D6", u"D7", u"D8")
SUM_IDS = (u"N220", u"N292", u"N293", u"N294", u"N304")      # 封 §3 F-3: 2 項の和の 5 行
POINT_IDS = (u"N035", u"N070")                                 # 封 §3 F-4: ポイント 2 行
BOUNDS = {u"F-1": (2, 5), u"F-2": (3, 8), u"F-3": (0, 1), u"F-4": (1, 2), u"F-5": (0, 3), u"F-6": (12, 18), u"F-7": (7, 11), u"F-8": 95.0, u"F-9": 80.0}
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


def load_prev():
    u"""前の便の script(手がかり・近傍・残す条件)と、それが読む前々便の script(fact・6 型・帯)。engine ではない。"""
    subj = load_module(MATERIALS[u"prev_script"][0], "derivation_subject_prev")
    full = subj.load_prev()
    return subj, full


# ---------------------------------------------------------------- 封 §2: 足す型(N の中だけで作る)

def d7_candidates(full, idx, N, t, u):
    out = []
    for ctx, fs in idx.money_by_ctx.items():
        inside = [f for f in fs if f[u"name"] in N]
        for i in range(len(inside)):
            for j in range(i + 1, len(inside)):
                a, b = inside[i], inside[j]
                if a[u"name"] == b[u"name"]:
                    continue
                c = full.cand(u"D7", [a, b], a[u"value"] + b[u"value"], t, a[u"g"] + b[u"g"] + u)
                if c:
                    c[u"context"] = ctx
                    out.append(c)
    return out


def d8_candidates(full, idx, N, t, u):
    names = sorted(n for n in N if (n, "JPY") in idx.by_name_unit)
    out = []
    for x in names:
        for y in names:
            if x == y:
                continue
            xs = {f[u"context"]: f for f in idx.by_name_unit[(x, "JPY")]}
            ys = {f[u"context"]: f for f in idx.by_name_unit[(y, "JPY")]}
            ctxs = sorted(c for c in xs if c in ys and ys[c][u"value"] != 0)
            for i in range(len(ctxs)):
                for j in range(i + 1, len(ctxs)):
                    c1, c2 = ctxs[i], ctxs[j]
                    x1, y1, x2, y2 = xs[c1], ys[c1], xs[c2], ys[c2]
                    v = (x1[u"value"] / abs(y1[u"value"]) - x2[u"value"] / abs(y2[u"value"])) * 100.0
                    G = u + 100.0 * sum(xx[u"g"] / abs(yy[u"value"]) + yy[u"g"] * abs(xx[u"value"]) / (yy[u"value"] ** 2) for xx, yy in ((x1, y1), (x2, y2)))
                    c = full.cand(u"D8", [x1, y1, x2, y2], v, t, G)
                    if c:
                        out.append(c)
    return out


def verdict_of(n):
    return u"導出一致" if n == 1 else u"保留" if n >= 2 else u"不一致"


def grounds_names(lab, c):
    return any(f[u"name"].split(":")[-1] in (lab.get(u"根拠") or u"") for f in c[u"fact"])


def build_rows(subj, full, prev_rows, labels, texts, idx):
    rows = []
    for pr in prev_rows:
        cid = pr[u"id"]
        tx, lab = texts[cid], labels[cid]
        u0, _ = full.written_granularity(tx.get(u"文"), tx[u"数"], tx[u"単位"])
        cands6, u, t = full.derive({u"unit": tx[u"単位"], u"value": tx[u"数"], u"u": u0}, idx)
        S = pr[u"S"]
        N1 = subj.neighbourhood(S, idx.arcs)
        N2 = subj.neighbourhood(N1, idx.arcs)
        k0_again = [c for c in cands6 if subj.keep(c, N1)] if S else []
        row = collections.OrderedDict([(u"id", cid), (u"札", pr[u"札"]), (u"state", pr[u"state"]), (u"unit", tx[u"単位"]), (u"value", tx[u"数"]),
                                       (u"母数", pr[u"母数"]), (u"対照", pr[u"対照"]), (u"手がかりあり", pr[u"手がかりあり"]), (u"S", S),
                                       (u"u", u), (u"t'", t), (u"N1 の大きさ", len(N1)), (u"N2 の大きさ", len(N2)), (u"N2", N2),
                                       (u"全探索の候補の数", len(cands6)), (u"全探索の候補の数が前の便の記録と一致", len(cands6) == pr[u"全探索の候補の数"]),
                                       (u"K0 の判定", pr[u"判定"]), (u"K0 の候補の数", pr[u"制約つきの候補の数"]),
                                       (u"K0 を出し直して記録と一致", (len(k0_again) == pr[u"制約つきの候補の数"]) if S else True),
                                       (u"recomputed", pr[u"recomputed"])])
        rc = pr[u"recomputed"]
        tol = None if rc is None else max(1e-6 * abs(float(rc)), 0.5 * (10.0 ** (-full.decimals_of(rc))))
        unit_money = tx[u"単位"] in full.UNIT_SCALE
        unit_point = tx[u"単位"] == u"ポイント"
        for K in CONDITIONS:
            N = N2 if DEPTH[K] == 2 else N1
            if not S:
                row[K] = collections.OrderedDict([(u"判定", NO_CLUE), (u"候補の数", 0)])
                continue
            kept = [c for c in cands6 if subj.keep(c, N)]
            if EXTRA[K]:
                if unit_money:
                    kept += d7_candidates(full, idx, N, t, u)
                if unit_point:
                    kept += d8_candidates(full, idx, N, t, u)
            r = collections.OrderedDict()
            r[u"候補の数"] = len(kept)
            r[u"型ごとの候補の数"] = collections.OrderedDict((k, sum(1 for x in kept if x[u"型"] == k)) for k in TYPES)
            r[u"判定"] = verdict_of(len(kept))
            r[u"候補"] = kept[:20]
            r[u"候補が 20 を超えた"] = len(kept) > 20
            r[u"どの型かに recomputed の値が在る"] = (rc is not None and any(abs(abs(x[u"v"]) - abs(float(rc))) <= tol for x in kept))
            if r[u"判定"] == u"導出一致":
                r[u"根拠に要素名"] = grounds_names(lab, kept[0])
                r[u"根拠に候補の fact の値"] = subj.grounds_have_values(lab.get(u"根拠"), kept[0], idx)
                r[u"根拠に名か値"] = bool(r[u"根拠に要素名"] or r[u"根拠に候補の fact の値"])
                r[u"K0 の導出一致と同じ候補"] = subj.same_candidate(kept[0], pr[u"候補"][0]) if pr[u"判定"] == u"導出一致" else None
            else:
                r[u"根拠に要素名"] = r[u"根拠に候補の fact の値"] = r[u"根拠に名か値"] = r[u"K0 の導出一致と同じ候補"] = None
            row[K] = r
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
    T[u"母数"] = len(pop)
    T[u"対照"] = len(ctl)
    T[u"手がかりあり"] = len(clue)
    T[u"手がかりなし"] = len(pop) - len(clue)
    T[u"全探索の候補の数が前の便の記録と一致した行"] = sum(1 for r in rows if r[u"全探索の候補の数が前の便の記録と一致"])
    T[u"K0 を出し直して記録と一致した行"] = sum(1 for r in rows if r[u"K0 を出し直して記録と一致"])
    T[u"K0 の判定(手がかりあり)"] = collections.OrderedDict((v, sum(1 for r in clue if r[u"K0 の判定"] == v)) for v in VERDICTS)
    T[u"手がかりありの N2 の大きさ"] = _cnt(min(r[u"N2 の大きさ"], 41) // 10 * 10 for r in clue)
    for K in CONDITIONS:
        T[u"%s の判定(手がかりあり)" % K] = collections.OrderedDict((v, sum(1 for r in clue if r[K][u"判定"] == v)) for v in VERDICTS)
        T[u"%s の遷移(K0 → %s)" % (K, K)] = collections.OrderedDict(
            (u"%s → %s" % (a, b), sum(1 for r in clue if r[u"K0 の判定"] == a and r[K][u"判定"] == b)) for a in VERDICTS for b in VERDICTS)
        T[u"%s の型ごとの帯の中の行(手がかりあり)" % K] = collections.OrderedDict((k, sum(1 for r in clue if r[K][u"型ごとの候補の数"][k] > 0)) for k in TYPES)
        one = [r for r in clue if r[K][u"判定"] == u"導出一致"]
        T[u"%s の導出一致の型" % K] = _cnt(r[K][u"候補"][0][u"型"] for r in one)
        T[u"%s の導出一致で根拠に要素名" % K] = sum(1 for r in one if r[K][u"根拠に要素名"])
        T[u"%s の導出一致で根拠に名か値" % K] = sum(1 for r in one if r[K][u"根拠に名か値"])
        T[u"%s の導出一致で根拠に名か値の割合" % K] = pct(T[u"%s の導出一致で根拠に名か値" % K], len(one))
        T[u"%s で K0 の導出一致のうち同じ候補で導出一致" % K] = sum(1 for r in clue if r[u"K0 の判定"] == u"導出一致" and r[K][u"K0 の導出一致と同じ候補"] is True)
        T[u"%s の導出一致の id と候補の要素" % K] = collections.OrderedDict((r[u"id"], [f[u"name"] for f in r[K][u"候補"][0][u"fact"]]) for r in one)
        T[u"%s の不一致の id" % K] = [r[u"id"] for r in clue if r[K][u"判定"] == u"不一致"]
        T[u"%s の保留の id と候補の数" % K] = collections.OrderedDict((r[u"id"], r[K][u"候補の数"]) for r in clue if r[K][u"判定"] == u"保留")
        T[u"%s の対照のうち どの型かに recomputed の値が在る" % K] = sum(1 for r in ctl if r[K][u"どの型かに recomputed の値が在る"])
        T[u"%s の対照の割合(型を問わず)" % K] = pct(T[u"%s の対照のうち どの型かに recomputed の値が在る" % K], len(ctl))
        T[u"%s の対照の判定" % K] = collections.OrderedDict((v, sum(1 for r in ctl if r[K][u"判定"] == v)) for v in VERDICTS)
    was_miss = [r for r in clue if r[u"K0 の判定"] == u"不一致"]
    was_one = [r for r in clue if r[u"K0 の判定"] == u"導出一致"]
    T[u"K0 の不一致のうち K1 で導出一致か保留"] = sum(1 for r in was_miss if r[u"K1"][u"判定"] in (u"導出一致", u"保留"))
    T[u"K0 の不一致のうち K1 で導出一致か保留の id と判定"] = collections.OrderedDict((r[u"id"], r[u"K1"][u"判定"]) for r in was_miss if r[u"K1"][u"判定"] != u"不一致")
    T[u"K0 の導出一致のうち K1 で保留"] = sum(1 for r in was_one if r[u"K1"][u"判定"] == u"保留")
    T[u"K0 の導出一致のうち K2 で保留"] = sum(1 for r in was_one if r[u"K2"][u"判定"] == u"保留")
    T[u"K0 の導出一致のうち K3 で保留"] = sum(1 for r in was_one if r[u"K3"][u"判定"] == u"保留")
    byid = {r[u"id"]: r for r in clue}
    T[u"2 項の和の 5 行で K2 の D7 が帯の中"] = sum(1 for i in SUM_IDS if byid[i][u"K2"][u"型ごとの候補の数"][u"D7"] > 0)
    T[u"2 項の和の 5 行の K2 の D7 の候補の数"] = collections.OrderedDict((i, byid[i][u"K2"][u"型ごとの候補の数"][u"D7"]) for i in SUM_IDS)
    T[u"2 項の和の 5 行の K3 の D7 の候補の数"] = collections.OrderedDict((i, byid[i][u"K3"][u"型ごとの候補の数"][u"D7"]) for i in SUM_IDS)
    T[u"ポイント 2 行で K2 の D8 の候補で導出一致"] = sum(1 for i in POINT_IDS if byid[i][u"K2"][u"判定"] == u"導出一致" and byid[i][u"K2"][u"候補"][0][u"型"] == u"D8")
    T[u"ポイント 2 行の K2 の判定と D8 の候補の数"] = collections.OrderedDict((i, [byid[i][u"K2"][u"判定"], byid[i][u"K2"][u"型ごとの候補の数"][u"D8"]]) for i in POINT_IDS)
    T[u"母数の id と判定(K0・K1・K2・K3)"] = collections.OrderedDict((r[u"id"], [r[u"K0 の判定"]] + [r[K][u"判定"] for K in CONDITIONS]) for r in pop)
    return T


def judge(T):
    J = collections.OrderedDict()
    J[u"F-1"] = BOUNDS[u"F-1"][0] <= T[u"K0 の不一致のうち K1 で導出一致か保留"] <= BOUNDS[u"F-1"][1]
    J[u"F-2"] = BOUNDS[u"F-2"][0] <= T[u"K0 の導出一致のうち K1 で保留"] <= BOUNDS[u"F-2"][1]
    J[u"F-3"] = BOUNDS[u"F-3"][0] <= T[u"2 項の和の 5 行で K2 の D7 が帯の中"] <= BOUNDS[u"F-3"][1]
    J[u"F-4"] = BOUNDS[u"F-4"][0] <= T[u"ポイント 2 行で K2 の D8 の候補で導出一致"] <= BOUNDS[u"F-4"][1]
    J[u"F-5"] = BOUNDS[u"F-5"][0] <= T[u"K0 の導出一致のうち K2 で保留"] <= BOUNDS[u"F-5"][1]
    J[u"F-6"] = BOUNDS[u"F-6"][0] <= T[u"K3 の判定(手がかりあり)"][u"導出一致"] <= BOUNDS[u"F-6"][1]
    J[u"F-7"] = BOUNDS[u"F-7"][0] <= T[u"K3 の判定(手がかりあり)"][u"不一致"] <= BOUNDS[u"F-7"][1]
    J[u"F-8"] = T[u"K3 の対照の割合(型を問わず)"] is not None and T[u"K3 の対照の割合(型を問わず)"] >= BOUNDS[u"F-8"]
    J[u"F-9"] = T[u"K3 の導出一致で根拠に名か値の割合"] is not None and T[u"K3 の導出一致で根拠に名か値の割合"] >= BOUNDS[u"F-9"]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"F-10"] = u"判定しない"
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
    subj, full = load_prev()
    prev_rec = jload(os.path.join(ROOT, MATERIALS[u"prev_rec"][0]))
    texts = {x[u"id"]: x for x in jload(os.path.join(ROOT, MATERIALS[u"claims"][0]))[u"claims"]}
    labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, MATERIALS[u"labels"][0]))[u"labels"]}
    entry = jload(os.path.join(ROOT, MATERIALS[u"entry"][0]))
    zpath = os.path.join(ROOT, MATERIALS[u"zip"][0])
    facts, counts = full.parse_facts(zpath)
    arcs, n_arcs = full.parse_cal(zpath)
    idx = full.Index(facts, arcs)
    rows = build_rows(subj, full, prev_rec[u"行"], labels, texts, idx)
    T = tally(rows)
    T.update(full.count_unjudged(entry[u"claims"], labels, texts, prev_rec[u"行"]))
    W = collections.OrderedDict()
    W[u"(a) 材料の sha256 が封の値"] = True
    W[u"(b) 前の便の記録の行が 302・母数 53・対照 249・手がかりあり 34"] = (len(prev_rec[u"行"]) == 302 and T[u"母数"] == 53 and T[u"対照"] == 249 and T[u"手がかりあり"] == 34)
    W[u"(c) entry の profile"] = entry.get(u"profile")
    W[u"(d) fact の読み取り(前々便と同じ関数)"] = counts
    W[u"(d) 計算リンクの arc"] = n_arcs
    W[u"(e) 全探索の候補の数が前の便の記録と一致した行"] = T[u"全探索の候補の数が前の便の記録と一致した行"]
    W[u"(e) K0 を出し直して記録と一致した行"] = T[u"K0 を出し直して記録と一致した行"]
    W[u"(f) K0 の判定(手がかりあり)が 15・5・14"] = list(T[u"K0 の判定(手がかりあり)"].values()) == [15, 5, 14]
    W[u"(g) K3 の対照のどの型かが recomputed を再現した割合"] = T[u"K3 の対照の割合(型を問わず)"]
    W[u"通った"] = bool(W[u"(a) 材料の sha256 が封の値"] and W[u"(b) 前の便の記録の行が 302・母数 53・対照 249・手がかりあり 34"]
                      and W[u"(e) 全探索の候補の数が前の便の記録と一致した行"] == 302 and W[u"(e) K0 を出し直して記録と一致した行"] == 302
                      and W[u"(f) K0 の判定(手がかりあり)が 15・5・14"])
    rec = collections.OrderedDict()
    rec[u"注意"] = (u"主語の制約つきの導出の近傍を深さ 2 に広げ(K1)、型 D7(二項の和)・D8(比率の差)を足し(K2)、両方(K3)にして、K0(深さ 1・6 型)からの"
                  u"遷移を数えた記録。広げて 1 つに決まっても出所として正しいとは言えない。1 書類・1 model の AI の文。P16 の判定。docID は書かない。")
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT}
    rec[u"HEAD の commit"] = git_head()
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"読んだ材料の sha256"] = shas
    rec[u"定数"] = collections.OrderedDict([(u"条件", collections.OrderedDict((K, {u"深さ": DEPTH[K], u"D7・D8": EXTRA[K]}) for K in CONDITIONS)),
                                         (u"D7", u"同じ context の金額 fact 2 つ(name が違う。両方 ∈ N)。a + b。順序なし"),
                                         (u"D8", u"name x・y(両方 ∈ N)の金額 fact で context c1 ≠ c2 の 4 つ。(x1/|y1| − x2/|y2|) × 100。context の組は順序なし。ポイントだけ"),
                                         (u"2 項の和の 5 行", list(SUM_IDS)), (u"ポイント 2 行", list(POINT_IDS)), (u"予測の幅", BOUNDS),
                                         (u"候補の保存", u"条件ごと・行ごとに先頭 20 まで(数は全部数える)")])
    rec[u"配線の門"] = W
    rec[u"行"] = rows
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T)
    rec[u"limits"] = [u"近傍で 1 つに決まっても出所として正しいとは言えない", u"手がかりなし 19 件には何も言えない", u"1 書類・1 model の AI の文。P16 の判定",
                     u"どの条件を engine に入れるかは人間が決める"]
    rec[u"key_leaks"] = record_key_leaks(rec)
    text = json.dumps(rec, ensure_ascii=False)
    if DOCID_RE.search(text):
        raise Stop(u"記録に docID が入った")
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print(u"written: %s" % a.out)
    print(json.dumps(W, ensure_ascii=False)[:600])
    for K in CONDITIONS:
        print(K, json.dumps(T[u"%s の判定(手がかりあり)" % K], ensure_ascii=False), json.dumps(T[u"%s の遷移(K0 → %s)" % (K, K)], ensure_ascii=False))
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
