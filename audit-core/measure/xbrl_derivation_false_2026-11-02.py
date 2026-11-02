# -*- coding: utf-8 -*-
u"""偽の数に導出一致を出す率(誤受理)(封 docs/XBRL_DERIVATION_FALSE_SEAL_2026-11-02.md)。

主語の制約の便(measure/xbrl_derivation_subject_2026-11-02.py)の手がかり S・近傍・残す条件と、全探索の便
(measure/xbrl_derivation_full_2026-11-02.py)の fact の読み方・6 型・帯・判定を importlib で読んで使う(写し直さない)。
足すのは、真の数 t を 3 通りの偽の数(V1 桁ずらし・V2 1 割増・V3 別の文の数)に差し替える部分と、誤受理の数え方。
材料は全部 repo の中(封 §0 の 7 file。sha256 を照らす)。engine(core/・adapters/)は import しない。通信しない。

    python3 measure/xbrl_derivation_false_2026-11-02.py [--out fixtures/xbrl/derivation_false_2026-11-02.json]

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- 数の差し替えは、全探索の便の derive に渡す claim の value を t_new / s(s は単位の倍率。%・ポイント・名は 1)にして行う。
  derive が返す t が t_new と一致することを行ごとに確かめる(配線)。u は前の便の記録の u をそのまま渡す。
- V3 の「id の順に並べ、同じ単位の次の行」は手がかりあり 34 の中で取る(封 §1)。対照 249 は V0 と V1 だけ(封 §2)。
  手がかりなし 19 は S が空なので K0 は作らず、V1・V2 の全探索の候補の数だけを書く(V3 は 34 の中で定義されるので作らない)。
- 「V0 の候補と同じ fact」は、偽の数の候補の (型, fact の組) が V0 の K0 の候補のどれかと一致すること(前の便の same_candidate)。
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

SEAL_REL = "docs/XBRL_DERIVATION_FALSE_SEAL_2026-11-02.md"
SEAL_COMMIT = "79dba8b"
OUT_REL = "fixtures/xbrl/derivation_false_2026-11-02.json"
MATERIALS = collections.OrderedDict([
    (u"claims", ("fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json", "c886a9e69353c677297341436f9777b779895054804adce1805f3d546dd4b579")),
    (u"labels", ("fixtures/xbrl/ai_prose_labels_2026-10-09.json", "7eac1450c40c68e0a25bf7f56c32db4ee6dad226e55df7efdb8019764a71173b")),
    (u"entry", ("fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json", "6c4c65d1d24ed46250d6bda41fc023d0624ec130f9c1fe791e840c6def7077da")),
    (u"zip", ("fixtures/xbrl/ai_prose_instance_2026-10-09.zip", "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799")),
    (u"prev_rec", ("fixtures/xbrl/derivation_subject_2026-11-02.json", "6703ae50e2fcee8bf6340fc96c89b7bd530b472b5b103efc83e2e40c0eb02de0")),
    (u"prev_script", ("measure/xbrl_derivation_subject_2026-11-02.py", "21f1f19bc2934ea148b72536770c17f901514e2fe4dc085ddd0facc4c440addc")),
    (u"full_script", ("measure/xbrl_derivation_full_2026-11-02.py", "7bcfafa99c300e97f72a887c8914564fb1e7779e84b414e15c6f9d806e4e3670")),
])
VARIANTS = (u"V0", u"V1", u"V2", u"V3")
FALSE_VARIANTS = (u"V1", u"V2", u"V3")
VERDICTS = (u"導出一致", u"保留", u"不一致")
TYPES = (u"D1", u"D2", u"D3", u"D4", u"D5", u"D6")
BOUNDS = {u"G-1": (0, 3), u"G-2": (0, 2), u"G-3": (0, 4), u"G-4": 80.0, u"G-5": (15, 30), u"G-6": 34, u"G-7": 5.0, u"G-8": 0}
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
    subj = load_module(MATERIALS[u"prev_script"][0], "derivation_subject_prev_for_false")
    full = subj.load_prev()
    return subj, full


# ---------------------------------------------------------------- 封 §1: 偽の数

def v2_of(t, u):
    v = round(t * 1.1 / u) * u
    return v if abs(v - t) > 1e-9 * max(1.0, t) else t + 2 * u


def v3_of(i, clue_rows):
    u"""手がかりあり 34 を id の順に並べ、同じ単位の次の行(末尾は先頭へ)の t。同じ値なら更に次。"""
    me = clue_rows[i]
    n = len(clue_rows)
    for step in range(1, n):
        o = clue_rows[(i + step) % n]
        if o[u"unit"] == me[u"unit"] and abs(o[u"t'"] - me[u"t'"]) > 1e-9 * max(1.0, me[u"t'"]):
            return o[u"t'"], o[u"id"]
    return None, None


def variants_of(i, clue_rows):
    me = clue_rows[i]
    t, u = me[u"t'"], me[u"u"]
    v3, src = v3_of(i, clue_rows)
    out = collections.OrderedDict([(u"V0", t), (u"V1", t + u), (u"V2", v2_of(t, u)), (u"V3", v3)])
    return out, src


def verdict_of(n):
    return u"導出一致" if n == 1 else u"保留" if n >= 2 else u"不一致"


def one_sided(c, t, u, money):
    u"""切り捨ての片側の帯(参考): 金額の文なら −(G − u) ≤ |v| − t < u。金額以外は K0 の帯(候補は既に帯の中)のまま。"""
    if not money:
        return True
    d = abs(c[u"v"]) - t
    return -(c[u"G"] - u) - 1e-9 * max(1.0, t) <= d < u - 1e-9 * max(1.0, t)


def judge_variant(subj, full, idx, pr, N1, t_new):
    u"""数 t_new で全探索(6 型)と K0(深さ 1 の制約)を出す。返す: (全探索の候補, K0 の候補, derive が返した t)。"""
    s = full.UNIT_SCALE.get(pr[u"unit"], 1.0)
    cands, u, t = full.derive({u"unit": pr[u"unit"], u"value": t_new / s, u"u": pr[u"u"]}, idx)
    kept = [c for c in cands if subj.keep(c, N1)] if pr[u"S"] else []
    return cands, kept, t


def build_rows(subj, full, prev_rows, idx):
    clue = [r for r in prev_rows if r[u"母数"] and r[u"手がかりあり"]]
    clue_index = {r[u"id"]: i for i, r in enumerate(clue)}
    rows = []
    for pr in prev_rows:
        N1 = subj.neighbourhood(pr[u"S"], idx.arcs) if pr[u"S"] else []
        row = collections.OrderedDict([(u"id", pr[u"id"]), (u"札", pr[u"札"]), (u"state", pr[u"state"]), (u"unit", pr[u"unit"]), (u"value", pr[u"value"]),
                                       (u"母数", pr[u"母数"]), (u"対照", pr[u"対照"]), (u"手がかりあり", pr[u"手がかりあり"]), (u"S", pr[u"S"]),
                                       (u"u", pr[u"u"]), (u"t", pr[u"t'"]), (u"K0 の判定(前の便の記録)", pr[u"判定"]), (u"K0 の候補の数(前の便の記録)", pr[u"制約つきの候補の数"])])
        if pr[u"母数"] and pr[u"手がかりあり"]:
            vs, src = variants_of(clue_index[pr[u"id"]], clue)
            names = VARIANTS
            row[u"V3 の出所の id"] = src
        elif pr[u"対照"]:
            vs = collections.OrderedDict([(u"V0", pr[u"t'"]), (u"V1", pr[u"t'"] + pr[u"u"])])
            names = (u"V0", u"V1")
        else:
            vs = collections.OrderedDict([(u"V0", pr[u"t'"]), (u"V1", pr[u"t'"] + pr[u"u"]), (u"V2", v2_of(pr[u"t'"], pr[u"u"]))])
            names = (u"V0", u"V1", u"V2")
        v0_kept = None
        for V in names:
            t_new = vs[V]
            cands, kept, t_back = judge_variant(subj, full, idx, pr, N1, t_new)
            r = collections.OrderedDict()
            r[u"t"] = t_new
            r[u"derive が返した t が一致"] = abs(t_back - t_new) <= 1e-6 * max(1.0, abs(t_new))
            r[u"全探索の候補の数"] = len(cands)
            r[u"全探索の判定"] = verdict_of(len(cands))
            if pr[u"S"]:
                r[u"K0 の候補の数"] = len(kept)
                r[u"K0 の判定"] = verdict_of(len(kept))
                r[u"型ごとの候補の数"] = collections.OrderedDict((k, sum(1 for x in kept if x[u"型"] == k)) for k in TYPES)
                r[u"候補"] = kept[:20]
                # 参考(封の予測の対象ではない。2 回目の走らせで足した): 帯を H(G/2)までに絞ったときの候補の数と判定
                tight = [x for x in kept if x[u"段"] in (u"完全一致", u"丸めの帯 H")]
                r[u"H までの候補の数"] = len(tight)
                r[u"H までの判定"] = verdict_of(len(tight))
                r[u"候補の段"] = _cnt(x[u"段"] for x in kept)
                # 参考(封の予測の対象ではない。3 回目の走らせで足した): 金額の文を切り捨て(百万円未満切捨て)と見た片側の帯
                # −(G − u) ≤ |v| − t < u(fact の桁 g の分だけ下に、文の桁 u の分だけ上に)。金額以外の単位は K0 の帯のまま
                one = [x for x in kept if one_sided(x, t_new, pr[u"u"], pr[u"unit"] in full.UNIT_SCALE)]
                r[u"片側の候補の数"] = len(one)
                r[u"片側の判定"] = verdict_of(len(one))
                if V == u"V0":
                    v0_kept = kept
                    r[u"前の便の記録と一致"] = (len(kept) == pr[u"制約つきの候補の数"] and verdict_of(len(kept)) == pr[u"判定"] and len(cands) == pr[u"全探索の候補の数"])
                elif r[u"K0 の判定"] == u"導出一致":
                    r[u"V0 の候補と同じ fact"] = any(subj.same_candidate(kept[0], c0) for c0 in v0_kept)
                else:
                    r[u"V0 の候補と同じ fact"] = None
            else:
                r[u"K0 の判定"] = u"手がかりなし"
                if V == u"V0":
                    r[u"前の便の記録と一致"] = (len(cands) == pr[u"全探索の候補の数"])
            row[V] = r
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
    T[u"手がかりあり"] = len(clue)
    T[u"手がかりなし"] = len(none)
    T[u"V0 で前の便の記録と一致した行(全行)"] = sum(1 for r in rows if r[u"V0"][u"前の便の記録と一致"])
    T[u"V0 で前の便の記録と一致した行(手がかりあり)"] = sum(1 for r in clue if r[u"V0"][u"前の便の記録と一致"])
    T[u"derive が返した t が一致しなかった行×変種"] = sum(1 for r in rows for V in VARIANTS if V in r and not r[V][u"derive が返した t が一致"])
    T[u"手がかりありの unit"] = _cnt(r[u"unit"] for r in clue)
    for V in VARIANTS:
        T[u"%s の K0 の判定(手がかりあり)" % V] = collections.OrderedDict((v, sum(1 for r in clue if r[V][u"K0 の判定"] == v)) for v in VERDICTS)
        T[u"%s の全探索の判定(手がかりあり)" % V] = collections.OrderedDict((v, sum(1 for r in clue if r[V][u"全探索の判定"] == v)) for v in VERDICTS)
        T[u"%s の全探索で帯の中(候補 1 以上。手がかりあり)" % V] = sum(1 for r in clue if r[V][u"全探索の候補の数"] >= 1)
        if V != u"V0":
            T[u"%s の誤受理の id と候補の要素" % V] = collections.OrderedDict((r[u"id"], [f[u"name"] for f in r[V][u"候補"][0][u"fact"]]) for r in clue if r[V][u"K0 の判定"] == u"導出一致")
            T[u"%s の誤受理で V0 の候補と同じ fact" % V] = sum(1 for r in clue if r[V][u"K0 の判定"] == u"導出一致" and r[V][u"V0 の候補と同じ fact"])
            T[u"%s の K0 の判定 × K0 の元の判定" % V] = collections.OrderedDict(
                (u"%s → %s" % (a, b), sum(1 for r in clue if r[u"K0 の判定(前の便の記録)"] == a and r[V][u"K0 の判定"] == b)) for a in VERDICTS for b in VERDICTS)
    total = len(clue) * len(FALSE_VARIANTS)
    T[u"偽の数の件数(手がかりあり × 3)"] = total
    T[u"偽の数で K0 が導出一致(誤受理)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"K0 の判定"] == u"導出一致")
    T[u"偽の数で K0 が保留"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"K0 の判定"] == u"保留")
    T[u"偽の数で K0 が不一致(退けた)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"K0 の判定"] == u"不一致")
    T[u"偽の数で K0 が退けた割合"] = pct(T[u"偽の数で K0 が不一致(退けた)"], total)
    T[u"偽の数で全探索が不一致(退けた)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"全探索の判定"] == u"不一致")
    T[u"偽の数で全探索が退けた割合"] = pct(T[u"偽の数で全探索が不一致(退けた)"], total)
    T[u"偽の数で全探索が導出一致"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"全探索の判定"] == u"導出一致")
    T[u"誤受理で V0 の候補と同じ fact(合計)"] = sum(T[u"%s の誤受理で V0 の候補と同じ fact" % V] for V in FALSE_VARIANTS)
    T[u"対照の V0 で前の便の記録と一致"] = sum(1 for r in ctl if r[u"V0"][u"前の便の記録と一致"])
    T[u"対照の V1 で K0 が導出一致"] = sum(1 for r in ctl if r[u"V1"][u"K0 の判定"] == u"導出一致")
    T[u"対照の V1 で K0 が導出一致の割合"] = pct(T[u"対照の V1 で K0 が導出一致"], len(ctl))
    T[u"対照の V1 の K0 の判定"] = collections.OrderedDict((v, sum(1 for r in ctl if r[u"V1"][u"K0 の判定"] == v)) for v in VERDICTS)
    T[u"対照の V1 で全探索が帯の中"] = sum(1 for r in ctl if r[u"V1"][u"全探索の候補の数"] >= 1)
    T[u"対照の V0 の K0 の判定"] = collections.OrderedDict((v, sum(1 for r in ctl if r[u"V0"][u"K0 の判定"] == v)) for v in VERDICTS)
    # 参考(封の予測の対象ではない): 帯を H までに絞ったときの判定
    for V in VARIANTS:
        T[u"%s の H までの判定(手がかりあり)" % V] = collections.OrderedDict((v, sum(1 for r in clue if r[V][u"H までの判定"] == v)) for v in VERDICTS)
        if V != u"V0":
            T[u"%s の誤受理の候補の段" % V] = _cnt(r[V][u"候補"][0][u"段"] for r in clue if r[V][u"K0 の判定"] == u"導出一致")
    T[u"偽の数で H までで導出一致(誤受理)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"H までの判定"] == u"導出一致")
    T[u"偽の数で H までで不一致(退けた)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"H までの判定"] == u"不一致")
    T[u"偽の数で H までで退けた割合"] = pct(T[u"偽の数で H までで不一致(退けた)"], total)
    T[u"V0 で H までで導出一致(真の数の受理)"] = T[u"V0 の H までの判定(手がかりあり)"][u"導出一致"]
    T[u"対照の V1 で H までで導出一致"] = sum(1 for r in ctl if r[u"V1"][u"H までの判定"] == u"導出一致")
    T[u"対照の V1 で H までで導出一致の割合"] = pct(T[u"対照の V1 で H までで導出一致"], len(ctl))
    T[u"対照の V0 で H までで導出一致"] = sum(1 for r in ctl if r[u"V0"][u"H までの判定"] == u"導出一致")
    # 参考(封の予測の対象ではない): 金額の文を切り捨てと見た片側の帯
    for V in VARIANTS:
        T[u"%s の片側の判定(手がかりあり)" % V] = collections.OrderedDict((v, sum(1 for r in clue if r[V][u"片側の判定"] == v)) for v in VERDICTS)
    T[u"偽の数で片側で導出一致(誤受理)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"片側の判定"] == u"導出一致")
    T[u"偽の数で片側で不一致(退けた)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"片側の判定"] == u"不一致")
    T[u"偽の数で片側で退けた割合"] = pct(T[u"偽の数で片側で不一致(退けた)"], total)
    T[u"V0 で片側で導出一致(真の数の受理)"] = T[u"V0 の片側の判定(手がかりあり)"][u"導出一致"]
    T[u"V1 の片側の誤受理の id"] = [r[u"id"] for r in clue if r[u"V1"][u"片側の判定"] == u"導出一致"]
    T[u"対照の V1 で片側で導出一致"] = sum(1 for r in ctl if r[u"V1"][u"片側の判定"] == u"導出一致")
    T[u"対照の V1 で片側で導出一致の割合"] = pct(T[u"対照の V1 で片側で導出一致"], len(ctl))
    T[u"対照の V0 で片側で導出一致"] = sum(1 for r in ctl if r[u"V0"][u"片側の判定"] == u"導出一致")
    T[u"対照の V0 の片側の判定"] = collections.OrderedDict((v, sum(1 for r in ctl if r[u"V0"][u"片側の判定"] == v)) for v in VERDICTS)
    T[u"手がかりなしの V1 で全探索が帯の中"] = sum(1 for r in none if r[u"V1"][u"全探索の候補の数"] >= 1)
    T[u"手がかりなしの V2 で全探索が帯の中"] = sum(1 for r in none if r[u"V2"][u"全探索の候補の数"] >= 1)
    T[u"母数の id と判定(K0: V0・V1・V2・V3)"] = collections.OrderedDict((r[u"id"], [r[V][u"K0 の判定"] for V in VARIANTS if V in r]) for r in pop)
    return T


def judge(T):
    J = collections.OrderedDict()
    J[u"G-1"] = BOUNDS[u"G-1"][0] <= T[u"V1 の K0 の判定(手がかりあり)"][u"導出一致"] <= BOUNDS[u"G-1"][1]
    J[u"G-2"] = BOUNDS[u"G-2"][0] <= T[u"V2 の K0 の判定(手がかりあり)"][u"導出一致"] <= BOUNDS[u"G-2"][1]
    J[u"G-3"] = BOUNDS[u"G-3"][0] <= T[u"V3 の K0 の判定(手がかりあり)"][u"導出一致"] <= BOUNDS[u"G-3"][1]
    J[u"G-4"] = T[u"偽の数で K0 が退けた割合"] is not None and T[u"偽の数で K0 が退けた割合"] >= BOUNDS[u"G-4"]
    J[u"G-5"] = BOUNDS[u"G-5"][0] <= T[u"V1 の全探索で帯の中(候補 1 以上。手がかりあり)"] <= BOUNDS[u"G-5"][1]
    J[u"G-6"] = T[u"V0 で前の便の記録と一致した行(手がかりあり)"] == BOUNDS[u"G-6"]
    J[u"G-7"] = T[u"対照の V1 で K0 が導出一致の割合"] is not None and T[u"対照の V1 で K0 が導出一致の割合"] <= BOUNDS[u"G-7"]
    J[u"G-8"] = T[u"誤受理で V0 の候補と同じ fact(合計)"] == BOUNDS[u"G-8"]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"G-9"] = u"判定しない"
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
    rows = build_rows(subj, full, prev_rec[u"行"], idx)
    T = tally(rows)
    T.update(full.count_unjudged(entry[u"claims"], labels, texts, prev_rec[u"行"]))
    W = collections.OrderedDict()
    W[u"(a) 材料の sha256 が封の値"] = True
    W[u"(b) 前の便の記録の行が 302・母数 53・対照 249・手がかりあり 34"] = (len(prev_rec[u"行"]) == 302 and T[u"母数"] == 53 and T[u"対照"] == 249 and T[u"手がかりあり"] == 34)
    W[u"(c) entry の profile"] = entry.get(u"profile")
    W[u"(d) fact の読み取り(全探索の便と同じ関数)"] = counts
    W[u"(d) 計算リンクの arc"] = n_arcs
    W[u"(e) V0 で前の便の記録と一致した行(全行)"] = T[u"V0 で前の便の記録と一致した行(全行)"]
    W[u"(e) derive が返した t が一致しなかった行×変種"] = T[u"derive が返した t が一致しなかった行×変種"]
    W[u"(f) V3 の出所が全行で決まった"] = all(r.get(u"V3 の出所の id") for r in rows if r[u"母数"] and r[u"手がかりあり"])
    W[u"(g) 対照の V1 で K0 が導出一致の割合"] = T[u"対照の V1 で K0 が導出一致の割合"]
    W[u"通った"] = bool(W[u"(a) 材料の sha256 が封の値"] and W[u"(b) 前の便の記録の行が 302・母数 53・対照 249・手がかりあり 34"]
                      and W[u"(e) V0 で前の便の記録と一致した行(全行)"] == 302 and W[u"(e) derive が返した t が一致しなかった行×変種"] == 0 and W[u"(f) V3 の出所が全行で決まった"])
    rec = collections.OrderedDict()
    rec[u"注意"] = (u"主語の制約つきの導出(深さ 1・6 型)に、真の数を 3 通りに変えた偽の数(桁ずらし・1 割増・別の文の数)を与え、導出一致(誤受理)・保留・"
                  u"不一致(退けた)を数えた記録。偽の数は機械的に作ったもので AI の誤りの分布ではない。1 書類・1 model の AI の文。P16 の判定。docID は書かない。")
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT}
    rec[u"HEAD の commit"] = git_head()
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"読んだ材料の sha256"] = shas
    rec[u"定数"] = collections.OrderedDict([(u"変種", collections.OrderedDict([(u"V0", u"t"), (u"V1", u"t + u"), (u"V2", u"round(t × 1.1 / u) × u。t と同じなら t + 2u"), (u"V3", u"手がかりあり 34 を id の順で同じ単位の次の行の t。同じ値なら更に次")])),
                                         (u"K0", u"深さ 1・6 型(前の便の script の近傍と残す条件)"), (u"対照の変種", [u"V0", u"V1"]), (u"手がかりなしの変種", [u"V0", u"V1", u"V2"]),
                                         (u"予測の幅", BOUNDS), (u"候補の保存", u"変種ごと・行ごとに K0 の候補を先頭 20 まで(数は全部数える)")])
    rec[u"配線の門"] = W
    rec[u"行"] = rows
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T)
    rec[u"limits"] = [u"偽の数は機械的に作った 3 通り(AI の誤りの分布ではない)", u"保留は誤受理に数えない", u"1 書類・1 model の AI の文。P16 の判定",
                     u"導出を engine に入れるかは人間が決める"]
    rec[u"key_leaks"] = record_key_leaks(rec)
    text = json.dumps(rec, ensure_ascii=False)
    if DOCID_RE.search(text):
        raise Stop(u"記録に docID が入った")
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print(u"written: %s" % a.out)
    print(json.dumps(W, ensure_ascii=False)[:700])
    for V in VARIANTS:
        print(V, u"K0", json.dumps(T[u"%s の K0 の判定(手がかりあり)" % V], ensure_ascii=False), u"全探索", json.dumps(T[u"%s の全探索の判定(手がかりあり)" % V], ensure_ascii=False))
    print(u"退けた割合", T[u"偽の数で K0 が退けた割合"], u"対照 V1 誤受理", T[u"対照の V1 で K0 が導出一致"], T[u"対照の V1 で K0 が導出一致の割合"])
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
