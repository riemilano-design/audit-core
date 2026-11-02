# -*- coding: utf-8 -*-
u"""導出の検証の診断(後半): AI の文の数字を instance の全 fact と計算リンクから導出できるか(封 docs/XBRL_DERIVATION_FULL_SEAL_2026-11-02.md)。

材料は全部 repo の中(封 §0 の 4 file。sha256 を照らす)。engine(core/・adapters/)は import しない。
inline XBRL(ix:nonFraction)と計算リンク(calculationArc)は zipfile と正規表現で読む。通信しない。

    python3 measure/xbrl_derivation_full_2026-11-02.py [--out fixtures/xbrl/derivation_full_2026-11-02.json]

実装の注(封 §1 の字の解釈。実装より先に決め、結果を見て変えない):
- 封 §1 の「金額」の fact は unitRef が JPY のもの。**1 株あたり円(unitRef JPYPerShares)の fact は、円で表された値なので
  円の文の D1 の対象に含める**(engine が 円 の文を 1 株あたりの fact に結ぶ経路を対照 C-1 で再現するため)。百万円の文には含めない。
- 文の最下位の桁 u は、数の小数部の桁数 d から 10^(−d) × s(s は単位の倍率。%・ポイント・名は s = 1)。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SEAL_REL = "docs/XBRL_DERIVATION_FULL_SEAL_2026-11-02.md"
SEAL_COMMIT = "42b51d3"
OUT_REL = "fixtures/xbrl/derivation_full_2026-11-02.json"
MATERIALS = collections.OrderedDict([
    (u"claims", ("fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json", "c886a9e69353c677297341436f9777b779895054804adce1805f3d546dd4b579")),
    (u"labels", ("fixtures/xbrl/ai_prose_labels_2026-10-09.json", "7eac1450c40c68e0a25bf7f56c32db4ee6dad226e55df7efdb8019764a71173b")),
    (u"entry", ("fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json", "6c4c65d1d24ed46250d6bda41fc023d0624ec130f9c1fe791e840c6def7077da")),
    (u"zip", ("fixtures/xbrl/ai_prose_instance_2026-10-09.zip", "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799")),
])
UNIT_SCALE = {u"円": 1.0, u"千円": 1e3, u"百万円": 1e6}
RATIO_UNITS = (u"%", u"ポイント")
COUNT_UNITS = (u"名",)
STAGES = (u"完全一致", u"丸めの帯 H", u"丸めの帯 F", u"不一致")
IN_BAND = (u"完全一致", u"丸めの帯 H", u"丸めの帯 F")
VERDICTS = (u"導出一致", u"保留", u"不一致")
TYPES = (u"D1", u"D2", u"D3", u"D4", u"D5", u"D6")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
KEY_PATTERNS = (r"sk-[A-Za-z0-9_\-]{10,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{20,}", r"xox[baprs]-[A-Za-z0-9\-]{10,}",
                r"-----BEGIN", r"Bearer [A-Za-z0-9._\-]{16,}", r"AIza[0-9A-Za-z_\-]{30,}")
NONFRACTION_RE = re.compile(r"<ix:nonFraction\b([^>]*?)(/>|>(.*?)</ix:nonFraction>)", re.S)
ATTR_RE = re.compile(r'([\w:]+)="([^"]*)"')
ARC_RE = re.compile(r"<link:calculationArc\b([^>]*)/?>")
TAG_RE = re.compile(r"<[^>]+>")


class Stop(SystemExit):
    pass


def sha256_file(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- 封 §1: fact の読み方

def parse_facts(zpath):
    u"""ix:nonFraction を全部読む。返す: facts(重複を除く)、読み取りの数。"""
    z = zipfile.ZipFile(zpath)
    raw, unparsed, nil = 0, 0, 0
    seen = collections.OrderedDict()
    for nm in sorted(z.namelist()):
        if not (nm.endswith("_ixbrl.htm") and "/PublicDoc/" in nm):
            continue
        text = z.read(nm).decode("utf-8", "replace")
        for m in NONFRACTION_RE.finditer(text):
            raw += 1
            attrs = dict(ATTR_RE.findall(m.group(1)))
            inner = TAG_RE.sub(u"", m.group(3) or u"").strip()
            if attrs.get("xsi:nil") == "true" or not inner:
                nil += 1
                continue
            fmt = attrs.get("format", "")
            if fmt.endswith("zerodash") or inner in (u"-", u"－", u"―", u"—"):
                val = 0.0
            else:
                s = inner.replace(u",", u"").replace(u"，", u"")
                try:
                    val = float(s)
                except ValueError:
                    unparsed += 1
                    continue
            scale = int(attrs.get("scale", "0") or 0)
            val = val * (10.0 ** scale)
            if attrs.get("sign") == "-":
                val = -val
            dec = attrs.get("decimals", "0")
            g = 0.0 if dec == "INF" else float(10) ** (-int(dec))
            key = (attrs.get("name"), attrs.get("contextRef"), attrs.get("unitRef"), val)
            if key not in seen:
                seen[key] = collections.OrderedDict([(u"name", attrs.get("name")), (u"context", attrs.get("contextRef")),
                                                     (u"unit", attrs.get("unitRef")), (u"value", val), (u"g", g)])
    facts = list(seen.values())
    counts = collections.OrderedDict([(u"ix:nonFraction の数", raw), (u"nil・空", nil), (u"数に読めない", unparsed),
                                      (u"重複を除いた fact", len(facts)), (u"context の数", len(set(f[u"context"] for f in facts))),
                                      (u"name の数", len(set(f[u"name"] for f in facts))),
                                      (u"unitRef ごと", collections.OrderedDict(sorted(collections.Counter(f[u"unit"] for f in facts).items())))])
    return facts, counts


def parse_cal(zpath):
    u"""calculationArc(from = 親, to = 子, weight)。親 → [(子, weight)](同じ子は 1 つ)。要素名は '_' を ':' に戻す(jppfs_cor_Assets → jppfs_cor:Assets)。"""
    z = zipfile.ZipFile(zpath)
    arcs = collections.OrderedDict()
    n = 0
    for nm in sorted(z.namelist()):
        if not nm.endswith("_cal.xml"):
            continue
        text = z.read(nm).decode("utf-8", "replace")
        for m in ARC_RE.finditer(text):
            a = dict(ATTR_RE.findall(m.group(1)))
            n += 1
            parent, child = to_qname(a.get("xlink:from", "")), to_qname(a.get("xlink:to", ""))
            w = float(a.get("weight", "1") or 1)
            arcs.setdefault(parent, collections.OrderedDict())
            arcs[parent].setdefault(child, w)
    return arcs, n


def to_qname(label):
    u"""'jppfs_cor_Assets' → 'jppfs_cor:Assets'(最初の 2 つの '_' の 2 つ目を ':' に)。"""
    parts = label.split("_", 2)
    if len(parts) == 3:
        return parts[0] + "_" + parts[1] + ":" + parts[2]
    return label


# ---------------------------------------------------------------- 封 §2: 導出の集合

WRITTEN_RE = re.compile(u"([0-9][0-9,]*(?:\\.[0-9]+)?)\\s*(百万円|千円|億円|円|%|％|ポイント|名|株)?")
WRITTEN_SCALE = {u"百万円": 1e6, u"千円": 1e3, u"億円": 1e8, u"円": 1.0, u"%": 1.0, u"％": 1.0, u"ポイント": 1.0, u"名": 1.0, u"株": 1.0, None: None}


def written_granularity(sentence, number, unit):
    u"""封 §1「u = 文の最下位の桁 × s」。文に書かれた数字(例: 945百万円)を探し、その最下位の桁の幅を円(または比率・個数)の尺で返す。
    材料の file は 945百万円 を 数 945000000・単位 円 と正規化して持つ主張があるので、数 の小数桁からは桁が取れない(2026-11-02 の 2 回目までの欠陥)。
    返す: (u, 文で見つけたか)。見つからなければ 数 の小数桁から(fallback)。"""
    target = abs(float(number))                       # 「46.0%減」は 数 −46.0 で書かれる。文の字は正なので絶対値で照らす
    base = UNIT_SCALE.get(unit, 1.0)
    for m in WRITTEN_RE.finditer(sentence or u""):
        txt, uw = m.group(1), m.group(2)
        try:
            v = float(txt.replace(u",", u""))
        except ValueError:
            continue
        sw = WRITTEN_SCALE.get(uw)
        if sw is None:
            continue
        # 文の数 × 書かれた単位 = 数 × 単位(円の尺)か、比率・個数ならそのまま一致か
        if unit in UNIT_SCALE and uw in (u"百万円", u"千円", u"億円", u"円") and abs(v * sw - target * base) <= 1e-6 * max(1.0, abs(target * base)):
            d = len(txt.split(u".")[1]) if u"." in txt else 0
            return sw * (10.0 ** (-d)), True
        if unit not in UNIT_SCALE and uw not in (u"百万円", u"千円", u"億円", u"円") and abs(v - target) <= 1e-9 * max(1.0, abs(target)):
            d = len(txt.split(u".")[1]) if u"." in txt else 0
            return 10.0 ** (-d), True
    d = decimals_of(number)
    return base * (10.0 ** (-d)) if unit in UNIT_SCALE else 10.0 ** (-d), False


def decimals_of(value):
    s = repr(float(value))
    if "e" in s or "E" in s:
        return 0
    frac = s.split(".")[1] if "." in s else ""
    frac = frac.rstrip("0")
    return len(frac)


def stage_of(e, G):
    if e == 0:
        return u"完全一致"
    if e <= G / 2.0:
        return u"丸めの帯 H"
    if e <= G:
        return u"丸めの帯 F"
    return u"不一致"


def fact_ref(f):
    return collections.OrderedDict([(u"name", f[u"name"]), (u"context", f[u"context"]), (u"unit", f[u"unit"])])


def cand(kind, facts, v, t, G):
    e = abs(abs(v) - t)
    st = stage_of(e, G)
    if st not in IN_BAND:
        return None
    return collections.OrderedDict([(u"型", kind), (u"fact", [fact_ref(f) for f in facts]), (u"v", v), (u"e", e), (u"G", G), (u"段", st)])


class Index(object):
    def __init__(self, facts, arcs):
        self.facts = facts
        self.arcs = arcs
        self.money = [f for f in facts if f[u"unit"] == "JPY"]
        self.per_share = [f for f in facts if f[u"unit"] == "JPYPerShares"]
        self.shares = [f for f in facts if f[u"unit"] == "shares"]
        self.pure = [f for f in facts if f[u"unit"] not in ("JPY", "JPYPerShares", "shares")]
        self.by_name_unit = collections.defaultdict(list)
        for f in facts:
            self.by_name_unit[(f[u"name"], f[u"unit"])].append(f)
        self.money_by_ctx = collections.defaultdict(list)
        for f in self.money:
            self.money_by_ctx[f[u"context"]].append(f)
        self.money_lookup = {(f[u"name"], f[u"context"]): f for f in self.money}

    def pairs_same_name(self, pool_unit):
        for (nm, un), fs in self.by_name_unit.items():
            if un != pool_unit or len(fs) < 2:
                continue
            for i in range(len(fs)):
                for j in range(len(fs)):
                    if i != j:
                        yield fs[i], fs[j]


def derive(claim, idx):
    u"""1 つの文の数に対する候補(帯の中)の一覧。u(文の最下位の桁の幅)は claim[u"u"]。"""
    unit, t0 = claim[u"unit"], abs(float(claim[u"value"]))     # 文の字は正(「46.0%減」「△120百万円」は 数 が負で記録される)。封 §2 の e = ||v| − t'| は大きさの比較
    out = []
    if unit in UNIT_SCALE:
        s = UNIT_SCALE[unit]
        t = t0 * s
        u = claim[u"u"]
        pool = idx.money + (idx.per_share if unit == u"円" else [])
        for f in pool:                                                   # D1
            c = cand(u"D1", [f], f[u"value"], t, f[u"g"] + u)
            if c:
                out.append(c)
        seen = set()
        for a, b in idx.pairs_same_name("JPY"):                          # D2(|a−b| は順序で同じなので 1 つに)
            key = tuple(sorted([(a[u"context"], a[u"value"]), (b[u"context"], b[u"value"])])) + (a[u"name"],)
            if key in seen:
                continue
            seen.add(key)
            c = cand(u"D2", [a, b], a[u"value"] - b[u"value"], t, a[u"g"] + b[u"g"] + u)
            if c:
                out.append(c)
        for parent, children in idx.arcs.items():                        # D4(親の fact が無い context だけ)
            for ctx in idx.money_by_ctx:
                if (parent, ctx) in idx.money_lookup:
                    continue
                present = [(idx.money_lookup[(ch, ctx)], w) for ch, w in children.items() if (ch, ctx) in idx.money_lookup]
                if len(present) < 2:
                    continue
                v = sum(w * f[u"value"] for f, w in present)
                G = sum(f[u"g"] for f, _ in present) + u
                c = cand(u"D4", [f for f, _ in present], v, t, G)
                if c:
                    c[u"親"] = parent
                    c[u"context"] = ctx
                    out.append(c)
        if unit == u"円":                                                 # D6
            for a in idx.money:
                for b in idx.shares:
                    if b[u"value"] == 0:
                        continue
                    v = a[u"value"] / abs(b[u"value"])
                    G = u + (a[u"g"] / abs(b[u"value"]) + b[u"g"] * abs(a[u"value"]) / (b[u"value"] ** 2))
                    c = cand(u"D6", [a, b], v, t, G)
                    if c:
                        out.append(c)
    elif unit in RATIO_UNITS:
        t = t0
        u = claim[u"u"]
        if unit == u"%":
            for f in idx.pure:                                           # D1(pure × 100)
                c = cand(u"D1", [f], f[u"value"] * 100.0, t, f[u"g"] * 100.0 + u)
                if c:
                    out.append(c)
            for a, b in idx.pairs_same_name("JPY"):                      # D3(順序あり)
                if b[u"value"] == 0:
                    continue
                v = (a[u"value"] - b[u"value"]) / abs(b[u"value"]) * 100.0
                G = u + 100.0 * (a[u"g"] / abs(b[u"value"]) + b[u"g"] * abs(a[u"value"]) / (b[u"value"] ** 2))
                c = cand(u"D3", [a, b], v, t, G)
                if c:
                    out.append(c)
            for ctx, fs in idx.money_by_ctx.items():                     # D5(同じ context、順序あり)
                for a in fs:
                    for b in fs:
                        if a is b or b[u"value"] == 0:
                            continue
                        v = a[u"value"] / abs(b[u"value"]) * 100.0
                        G = u + 100.0 * (a[u"g"] / abs(b[u"value"]) + b[u"g"] * abs(a[u"value"]) / (b[u"value"] ** 2))
                        c = cand(u"D5", [a, b], v, t, G)
                        if c:
                            out.append(c)
        else:                                                            # ポイント: D2 on pure × 100
            seen = set()
            for (nm, un), fs in idx.by_name_unit.items():
                if un in ("JPY", "JPYPerShares", "shares") or len(fs) < 2:
                    continue
                for i in range(len(fs)):
                    for j in range(len(fs)):
                        if i == j:
                            continue
                        key = tuple(sorted([(fs[i][u"context"], fs[i][u"value"]), (fs[j][u"context"], fs[j][u"value"])])) + (nm,)
                        if key in seen:
                            continue
                        seen.add(key)
                        c = cand(u"D2", [fs[i], fs[j]], (fs[i][u"value"] - fs[j][u"value"]) * 100.0, t, (fs[i][u"g"] + fs[j][u"g"]) * 100.0 + u)
                        if c:
                            out.append(c)
    elif unit in COUNT_UNITS:
        t = t0
        u = claim[u"u"]
        for f in idx.pure:                                               # D1(個数)
            c = cand(u"D1", [f], f[u"value"], t, f[u"g"] + u)
            if c:
                out.append(c)
    else:
        return None, None, None
    return out, u, t


def verdict_of(cands):
    n = len(cands)
    return u"導出一致" if n == 1 else u"保留" if n >= 2 else u"不一致"


def local_names(c):
    return [f[u"name"].split(":")[-1] for f in c[u"fact"]]


def build_rows(entry_claims, labels, texts, idx):
    u"""texts = AI の文の主張(id → {数, 単位})。文の数と単位は**こちら**から取る(封 §0。engine の記録の value・unit は
    正規化後の値(例: 945 百万円 → 円 945,000,000)で、文の最下位の桁が失われる。2026-11-02 の最初の走らせの欠陥)。"""
    rows = []
    for c in entry_claims:
        lab = labels.get(c[u"id"])
        tx = texts.get(c[u"id"])
        if lab is None or tx is None or c.get(u"kind") != "num" or tx.get(u"数") is None:
            continue
        u0, found = written_granularity(tx.get(u"文"), tx[u"数"], tx[u"単位"])
        claim = {u"unit": tx[u"単位"], u"value": tx[u"数"], u"u": u0}
        cands, u, t = derive(claim, idx)
        if cands is None:
            continue
        row = collections.OrderedDict([(u"id", c[u"id"]), (u"札", lab[u"札"]), (u"state", c[u"state"]), (u"unit", tx[u"単位"]), (u"value", tx[u"数"]),
                                       (u"engine の unit・value", [c.get(u"unit"), c.get(u"value")]), (u"桁を文で見つけた", found),
                                       (u"u", u), (u"t'", t), (u"recomputed", c.get(u"recomputed")),
                                       (u"候補の数", len(cands)), (u"型ごとの候補の数", collections.OrderedDict((k, sum(1 for x in cands if x[u"型"] == k)) for k in TYPES)),
                                       (u"判定", verdict_of(cands)), (u"候補", cands[:20]), (u"候補が 20 を超えた", len(cands) > 20)])
        row[u"D1 が帯の中"] = any(x[u"型"] == u"D1" for x in cands)
        rc = c.get(u"recomputed")
        tol = None if rc is None else max(1e-6 * abs(float(rc)), 0.5 * (10.0 ** (-decimals_of(rc))))   # recomputed は丸めて記録されている(例 2.94)
        row[u"D1 に recomputed の値が在る"] = (rc is not None and any(x[u"型"] == u"D1" and abs(abs(x[u"v"]) - abs(float(rc))) <= tol for x in cands))
        # 追加の配線(封の予測の対象ではない): engine の recomputed は engine 自身が導出した値(前期比・増減額)も含むので、型を問わず再現したか
        row[u"どの型かに recomputed の値が在る"] = (rc is not None and any(abs(abs(x[u"v"]) - abs(float(rc))) <= tol for x in cands))
        if row[u"判定"] == u"導出一致":
            row[u"根拠に要素名"] = any(n in (lab.get(u"根拠") or u"") for n in local_names(cands[0]))
        else:
            row[u"根拠に要素名"] = None
        row[u"母数"] = lab[u"札"] == u"真" and c[u"state"] != "GROUNDED"
        row[u"対照"] = lab[u"札"] == u"真" and c[u"state"] == "GROUNDED"
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
    T[u"数値の主張(札あり)"] = len(rows)
    T[u"母数"] = len(pop)
    T[u"母数の state"] = _cnt(r[u"state"] for r in pop)
    T[u"母数の unit"] = _cnt(r[u"unit"] for r in pop)
    T[u"対照"] = len(ctl)
    T[u"対照のうち D1 に recomputed の値が在る"] = sum(1 for r in ctl if r[u"D1 に recomputed の値が在る"])
    T[u"対照の割合"] = pct(T[u"対照のうち D1 に recomputed の値が在る"], len(ctl))
    T[u"桁を文で見つけた行"] = sum(1 for r in rows if r[u"桁を文で見つけた"])
    T[u"桁を文で見つけられなかった行の id"] = [r[u"id"] for r in rows if not r[u"桁を文で見つけた"]]
    T[u"対照のうち どの型かに recomputed の値が在る"] = sum(1 for r in ctl if r[u"どの型かに recomputed の値が在る"])
    T[u"対照の割合(型を問わず)"] = pct(T[u"対照のうち どの型かに recomputed の値が在る"], len(ctl))
    T[u"対照で再現しなかった行の unit"] = _cnt(r[u"unit"] for r in ctl if not r[u"どの型かに recomputed の値が在る"])
    T[u"対照で再現しなかった行の id"] = [r[u"id"] for r in ctl if not r[u"どの型かに recomputed の値が在る"]]
    T[u"母数のうち D1 が帯の中"] = sum(1 for r in pop if r[u"D1 が帯の中"])
    T[u"母数の判定"] = collections.OrderedDict((v, sum(1 for r in pop if r[u"判定"] == v)) for v in VERDICTS)
    T[u"母数の判定 × state"] = collections.OrderedDict((v, _cnt(r[u"state"] for r in pop if r[u"判定"] == v)) for v in VERDICTS)
    T[u"母数の判定 × unit"] = collections.OrderedDict((v, _cnt(r[u"unit"] for r in pop if r[u"判定"] == v)) for v in VERDICTS)
    one = [r for r in pop if r[u"判定"] == u"導出一致"]
    T[u"導出一致の型"] = _cnt(r[u"候補"][0][u"型"] for r in one)
    T[u"導出一致の型(D1 以外)"] = _cnt(r[u"候補"][0][u"型"] for r in one if r[u"候補"][0][u"型"] != u"D1")
    T[u"導出一致で根拠に要素名"] = sum(1 for r in one if r[u"根拠に要素名"])
    T[u"導出一致で根拠に要素名の割合"] = pct(T[u"導出一致で根拠に要素名"], len(one))
    T[u"保留の候補の数の分布"] = _cnt(min(r[u"候補の数"], 21) for r in pop if r[u"判定"] == u"保留")
    T[u"保留で候補の型に D1 を含む"] = sum(1 for r in pop if r[u"判定"] == u"保留" and r[u"型ごとの候補の数"][u"D1"] > 0)
    pc = [r for r in pop if r[u"unit"] == u"%"]
    T[u"% の母数"] = len(pc)
    T[u"% のうち D3 か D5 が帯の中"] = sum(1 for r in pc if r[u"型ごとの候補の数"][u"D3"] + r[u"型ごとの候補の数"][u"D5"] > 0)
    yen = [r for r in pop if r[u"unit"] == u"円"]
    T[u"円 の母数"] = len(yen)
    T[u"円 のうち D6 が帯の中"] = sum(1 for r in yen if r[u"型ごとの候補の数"][u"D6"] > 0)
    T[u"母数の型ごとの帯の中の行"] = collections.OrderedDict((k, sum(1 for r in pop if r[u"型ごとの候補の数"][k] > 0)) for k in TYPES)
    T[u"母数の id と判定"] = collections.OrderedDict((r[u"id"], r[u"判定"]) for r in pop)
    return T


def count_unjudged(entry_claims, labels, texts, rows):
    u"""封 C-10「判定不能・偽は判定しない。数だけ記録」の数を、行(build_rows の出力)ではなく entry と札から直接数える。
    最初の記録は行から数えて「判定不能の num 0」と誤った(単位 株 の主張 2 件は導出 6 型の対象外で行にならず、黙って落ちていた。
    2026-11-02 の独立監査で見つかった)。"""
    row_ids = set(r[u"id"] for r in rows)
    C = collections.OrderedDict()
    num = [c for c in entry_claims if c.get(u"kind") == "num" and c[u"id"] in labels]
    C[u"札ありの num の主張(entry)"] = len(num)
    C[u"行になった num"] = len(rows)
    dropped = [c for c in num if c[u"id"] not in row_ids]
    C[u"行にならなかった num の id と単位(単位が導出 6 型の対象外)"] = collections.OrderedDict((c[u"id"], (texts.get(c[u"id"]) or {}).get(u"単位")) for c in dropped)
    unj = [c for c in num if labels[c[u"id"]][u"札"] == u"判定不能"]
    C[u"判定不能の num"] = len(unj)
    C[u"判定不能の num の id と単位"] = collections.OrderedDict((c[u"id"], (texts.get(c[u"id"]) or {}).get(u"単位")) for c in unj)
    C[u"判定不能の num のうち行になった"] = sum(1 for c in unj if c[u"id"] in row_ids)
    C[u"偽の num"] = sum(1 for c in num if labels[c[u"id"]][u"札"] == u"偽")
    C[u"偽の text(母数外)"] = sum(1 for c in entry_claims if c[u"id"] in labels and labels[c[u"id"]][u"札"] == u"偽" and c.get(u"kind") != "num")
    return C


def d4_opportunities(idx):
    u"""D4 が候補を作れる余地: 計算リンクの親 × 金額の context のうち、子の fact が 2 つ以上そろう組の数と、そのうち親の fact が無い組の数。
    後者が 0 なら、この instance では D4 は候補を 1 つも作れない(「当たらなかった」ではなく「作る機会が無かった」)。"""
    pairs = 0
    without_parent = 0
    for parent, children in idx.arcs.items():
        for ctx in idx.money_by_ctx:
            present = [ch for ch in children if (ch, ctx) in idx.money_lookup]
            if len(present) < 2:
                continue
            pairs += 1
            if (parent, ctx) not in idx.money_lookup:
                without_parent += 1
    return collections.OrderedDict([(u"子が 2 つ以上そろう親 × context", pairs), (u"そのうち親の fact が無い組(D4 が候補を作れる組)", without_parent)])


def judge(T):
    J = collections.OrderedDict()
    J[u"C-1"] = T[u"対照の割合"] is not None and T[u"対照の割合"] >= 95.0
    J[u"C-2"] = 10 <= T[u"母数のうち D1 が帯の中"] <= 25
    J[u"C-3"] = 15 <= T[u"母数の判定"][u"導出一致"] <= 35
    J[u"C-4"] = 8 <= T[u"母数の判定"][u"不一致"] <= 25
    J[u"C-5"] = 5 <= T[u"母数の判定"][u"保留"] <= 20
    top = list(T[u"導出一致の型(D1 以外)"].items())
    J[u"C-6"] = bool(top) and top[0][0] == u"D2" and (len(top) == 1 or top[0][1] > top[1][1])
    J[u"C-7"] = 3 <= T[u"% のうち D3 か D5 が帯の中"] <= 5
    J[u"C-8"] = T[u"導出一致で根拠に要素名の割合"] is not None and T[u"導出一致で根拠に要素名の割合"] >= 60.0
    J[u"C-9"] = 5 <= T[u"円 のうち D6 が帯の中"] <= 20
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"C-10"] = u"判定しない"
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


def record_key_leaks(obj):
    t = json.dumps(obj, ensure_ascii=False)
    return sorted(set(p for p in KEY_PATTERNS if re.search(p, t)))


def git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode().strip() if r.returncode == 0 else None


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


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
    claims_src = jload(os.path.join(ROOT, MATERIALS[u"claims"][0]))
    labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, MATERIALS[u"labels"][0]))[u"labels"]}
    entry = jload(os.path.join(ROOT, MATERIALS[u"entry"][0]))
    zpath = os.path.join(ROOT, MATERIALS[u"zip"][0])
    facts, counts = parse_facts(zpath)
    arcs, n_arcs = parse_cal(zpath)
    idx = Index(facts, arcs)
    texts = {x[u"id"]: x for x in claims_src[u"claims"]}
    rows = build_rows(entry[u"claims"], labels, texts, idx)
    T = tally(rows)
    T.update(count_unjudged(entry[u"claims"], labels, texts, rows))
    W = collections.OrderedDict()
    W[u"(a) 材料の sha256 が封の値"] = True
    W[u"(b) 札の数"] = _cnt(x[u"札"] for x in labels.values())
    W[u"(b) 札が 415・entry の claim が 412"] = len(labels) == 415 and len(entry[u"claims"]) == 412 and len(claims_src[u"claims"]) == 415
    W[u"(c) entry の profile"] = entry.get(u"profile")
    W[u"(d) 母数が 53"] = T[u"母数"] == 53
    W[u"(e) 対照が 249"] = T[u"対照"] == 249
    W[u"(f) fact の読み取り"] = counts
    W[u"(f) 計算リンクの arc"] = n_arcs
    W[u"(f) 計算リンクの親の数"] = len(arcs)
    W[u"(f) D4 の余地"] = d4_opportunities(idx)
    W[u"(g) 対照の D1 が recomputed を再現した割合"] = T[u"対照の割合"]
    W[u"(g) 対照のどの型かが recomputed を再現した割合"] = T[u"対照の割合(型を問わず)"]
    W[u"通った"] = all(v for k, v in W.items() if k[:3] in (u"(a)", u"(d)", u"(e)") and isinstance(v, bool)) and W[u"(b) 札が 415・entry の claim が 412"]
    rec = collections.OrderedDict()
    rec[u"注意"] = (u"AI の文の数字を instance の全 fact と計算リンクに当て、固定した導出 6 型で帯の中に入る候補の数を数えた記録。帯の中に入っても"
                  u"出所として正しいとは言えない(instance 全体を探すので偶然の一致が増える)。1 書類・1 model の AI の文。P16 の判定で母数を取った。docID は書かない。")
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT}
    rec[u"HEAD の commit"] = git_head()
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"読んだ材料の sha256"] = shas
    rec[u"定数"] = collections.OrderedDict([(u"型", list(TYPES)), (u"段", list(STAGES)), (u"帯の中", list(IN_BAND)), (u"判定", list(VERDICTS)),
                                         (u"単位の倍率", UNIT_SCALE), (u"円の D1 の対象", u"JPY と JPYPerShares の fact(実装の注)"),
                                         (u"母数", u"札 真・kind num・P16 の state が GROUNDED でない"), (u"対照", u"札 真・kind num・GROUNDED"),
                                         (u"候補の保存", u"行ごとに先頭 20 まで(数は全部数える)")])
    rec[u"配線の門"] = W
    rec[u"行"] = rows
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T)
    rec[u"limits"] = [u"帯の中は出所の正しさではない(偶然の一致を除いていない)", u"1 書類・1 model の AI の文", u"P16 の判定で母数を取った(P27 ではない)",
                     u"導出一致の行を engine に入れるかは人間が決める"]
    rec[u"key_leaks"] = record_key_leaks(rec)
    text = json.dumps(rec, ensure_ascii=False)
    if DOCID_RE.search(text):
        raise Stop(u"記録に docID が入った")
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(dumps(rec))
    print(u"written: %s" % a.out)
    print(json.dumps(W, ensure_ascii=False)[:600])
    print(json.dumps(T[u"母数の判定"], ensure_ascii=False), json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
