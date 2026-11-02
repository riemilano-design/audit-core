# -*- coding: utf-8 -*-
u"""文の期の印と engine の context(封 docs/XBRL_PERIOD_MARK_SEAL_2026-11-02.md)。

engine を変えずに、AI の文の数の直前の字から期の印(同 / 前期 / 当期 / なし)を字の規則で拾い、engine が指した fact の
context の期・札の根拠の期と突き合わせて、取り違えの数と向きを数える。数の位置と直前の字 W の読み方は「その他」の便の
script(measure/xbrl_other_rule_2026-11-02.py)を importlib で読んで使う。材料は全部 repo の中(封 §0 の 5 file。sha256 を照らす)。
engine(core/・adapters/)は import しない。通信しない。

    python3 measure/xbrl_period_mark_2026-11-02.py [--out fixtures/xbrl/period_mark_2026-11-02.json]

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- W は「その他」の便の strip_trail(text[:数の字の始まり]) で、「(同」を辿る前のもの(封 §1-1)。印 同 は W の末尾が「(同」か「(同」。
- 前期・当期の字は W の末尾 14 字で見る。前期の字が 1 つでも在れば 前期、無ければ 当期の字を見る(封 §1-3・§1-4 の順)。
- 率の文(単位 % ・ ポイント)は印 × engine の表に入れるが、取り違えと K-9 の分母からは外す(封 §5)。
- 取り違え(engine)は 位置が決まる・率の文でない・engine の期が 当期 か 前期 の行で数える(札は問わない。札 真 の内訳も書く)。
- 2 回目の走らせで「取り違えの中身(参考)」を足した(封の予測の対象ではない。結果を見てから足した欄。文書の追記 1): 差の文(entry の form が
  derived_value) / 札が engine の期と合う(印の読み違い) / 札が文の期と合う(engine の期の取り違え) / 札が両方・読めず。上から順に当てる。
  1 回目との違いはこの欄と集計の 4 項だけ(他の欄・判定は不変)。
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

SEAL_REL = "docs/XBRL_PERIOD_MARK_SEAL_2026-11-02.md"
SEAL_COMMIT = "5a3b2a0"
OUT_REL = "fixtures/xbrl/period_mark_2026-11-02.json"
MATERIALS = collections.OrderedDict([
    (u"claims", ("fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json", "c886a9e69353c677297341436f9777b779895054804adce1805f3d546dd4b579")),
    (u"labels", ("fixtures/xbrl/ai_prose_labels_2026-10-09.json", "7eac1450c40c68e0a25bf7f56c32db4ee6dad226e55df7efdb8019764a71173b")),
    (u"entry", ("fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json", "6c4c65d1d24ed46250d6bda41fc023d0624ec130f9c1fe791e840c6def7077da")),
    (u"prev_script", ("measure/xbrl_other_rule_2026-11-02.py", "f81a9baa9ed84bccf405e7385d15d5819dff876d0a51cea7be986c2296868272")),
    (u"prev_rec", ("fixtures/xbrl/other_rule_2026-11-02.json", "76ad667f53314e4548626dde1176329d951fd853382e9b8949a8fe5a7b962783")),
])
MARKS = (u"同", u"前期", u"当期", u"なし")
PRIOR_WORDS = (u"前期末", u"前期", u"前年同期", u"前年度", u"前連結会計年度", u"前年")
CUR_WORDS = (u"当期末", u"当期", u"当連結会計年度", u"当年度", u"期末時点")
TAIL = 14
ENGINE_PERIODS = (u"当期", u"前期", u"2 期前以前", u"他", u"指せず")
GROUNDS_PRIOR = (u"前期", u"Prior1Year", u"前年")
GROUNDS_CUR = (u"CY", u"当期", u"CurrentYear", u"当年度")
RATE_UNITS = (u"%", u"ポイント")
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
WIRE_IDS = (u"N081", u"N145")
POINTER_RE = re.compile(r"^xbrl:([A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+)@([A-Za-z0-9_\-]+)$")
BOUNDS = {u"K-1": (90, 180), u"K-2": (20, 60), u"K-3": 50.0, u"K-4": (10, 40), u"K-5": (0, 8), u"K-6": (0, 4), u"K-7": (0, 5), u"K-8": 2, u"K-9": 15.0}
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


# ---------------------------------------------------------------- 封 §1: 期の印

def mark_of(w):
    if w.endswith(u"(同") or w.endswith(u"(同"):
        return u"同"
    tail = w[-TAIL:]
    if any(x in tail for x in PRIOR_WORDS):
        return u"前期"
    if any(x in tail for x in CUR_WORDS):
        return u"当期"
    return u"なし"


def text_period(mark):
    return u"前期" if mark in (u"同", u"前期") else u"当期"


# ---------------------------------------------------------------- 封 §2: 突き合わせ

def engine_period(pointers):
    for p in pointers or []:
        m = POINTER_RE.match(p)
        if m:
            ctx = m.group(2)
            if ctx.startswith(u"CurrentYear"):
                return u"当期", ctx
            if ctx.startswith(u"Prior1Year"):
                return u"前期", ctx
            if re.match(r"^Prior[2-9]Year", ctx):
                return u"2 期前以前", ctx
            return u"他", ctx
    return u"指せず", None


def grounds_period(grounds):
    g = grounds or u""
    prior = any(x in g for x in GROUNDS_PRIOR)
    cur = any(x in g for x in GROUNDS_CUR)
    if prior and cur:
        return u"両方"
    if prior:
        return u"前期"
    if cur:
        return u"当期"
    return u"読めず"


KINDS = (u"差の文(engine が a − b)", u"札が engine の期と合う(印の読み違い)", u"札が文の期と合う(engine の期の取り違え)", u"札が両方・読めず")


def kind_of(form, grounds_p, engine_p, text_p):
    u"""取り違えの中身(参考。2 回目の走らせで足した。封の予測の対象ではない)。上から順に当てる。"""
    if form == u"derived_value":
        return KINDS[0]
    if grounds_p == engine_p:
        return KINDS[1]
    if grounds_p == text_p:
        return KINDS[2]
    return KINDS[3]


def build_rows(oth, claims, labels, entry_claims, prev_rows):
    r1_decided = set(r[u"id"] for r in prev_rows if r.get(u"R1 の判定") == u"決まる")
    rows = []
    for c in claims:
        cid = c[u"id"]
        lab = labels.get(cid) or {}
        ec = entry_claims.get(cid) or {}
        text = c.get(u"文") or u""
        toks, hits = oth.locate(text, c[u"数"], c.get(u"単位")) if c.get(u"数") is not None else ([], [])
        r = collections.OrderedDict()
        r[u"id"] = cid
        r[u"札"] = lab.get(u"札")
        r[u"state"] = ec.get(u"state")
        r[u"単位"] = c.get(u"単位")
        r[u"率の文"] = c.get(u"単位") in RATE_UNITS
        r[u"数の位置"] = u"決まる" if len(hits) == 1 else (u"なし" if not hits else u"曖昧")
        r[u"W の末尾"] = None
        r[u"印"] = None
        r[u"文の期"] = None
        ep, ctx = engine_period(ec.get(u"pointers"))
        r[u"engine の期"] = ep
        r[u"engine の context"] = ctx
        r[u"根拠の期"] = grounds_period(lab.get(u"根拠")) if lab.get(u"札") == u"真" else None
        r[u"取り違え(engine)"] = None
        r[u"取り違えの中身(参考)"] = None
        r[u"form"] = ec.get(u"form")
        r[u"印の確かめ(札)で違う"] = None
        r[u"R1 で決まった行"] = cid in r1_decided
        if len(hits) == 1:
            w = oth.strip_trail(text[:hits[0][u"start"]])
            r[u"W の末尾"] = w[-TAIL:]
            r[u"印"] = mark_of(w)
            r[u"文の期"] = text_period(r[u"印"])
            if not r[u"率の文"] and ep in (u"当期", u"前期"):
                r[u"取り違え(engine)"] = (u"なし" if ep == r[u"文の期"] else (u"前期の文 × engine 当期" if r[u"文の期"] == u"前期" else u"当期の文 × engine 前期"))
                if r[u"取り違え(engine)"] != u"なし":
                    r[u"取り違えの中身(参考)"] = kind_of(ec.get(u"form"), r[u"根拠の期"], ep, r[u"文の期"])
            if r[u"根拠の期"] in (u"当期", u"前期"):
                r[u"印の確かめ(札)で違う"] = (r[u"根拠の期"] != r[u"文の期"])
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
    loc = [r for r in rows if r[u"数の位置"] == u"決まる"]
    T[u"位置が決まる行"] = len(loc)
    T[u"印の分布"] = collections.OrderedDict((m, sum(1 for r in loc if r[u"印"] == m)) for m in MARKS)
    T[u"印あり(同 + 前期 + 当期)"] = sum(1 for r in loc if r[u"印"] != u"なし")
    T[u"印の分布(札ごと)"] = collections.OrderedDict((s, collections.OrderedDict((m, sum(1 for r in loc if r[u"札"] == s and r[u"印"] == m)) for m in MARKS)) for s in (u"真", u"偽", u"判定不能"))
    T[u"印 × engine の期"] = collections.OrderedDict((m, collections.OrderedDict((e, sum(1 for r in loc if r[u"印"] == m and r[u"engine の期"] == e)) for e in ENGINE_PERIODS)) for m in MARKS)
    T[u"率の文(位置が決まる)"] = sum(1 for r in loc if r[u"率の文"])
    same = [r for r in loc if r[u"印"] == u"同" and r[u"engine の期"] in (u"当期", u"前期")]
    T[u"印 同 で engine が 当期 か 前期 の行"] = len(same)
    T[u"印 同 で engine が 前期"] = sum(1 for r in same if r[u"engine の期"] == u"前期")
    T[u"印 同 で engine が 前期 の割合"] = pct(T[u"印 同 で engine が 前期"], len(same))
    mis = [r for r in loc if r[u"取り違え(engine)"] not in (None, u"なし")]
    T[u"取り違え(engine)"] = len(mis)
    T[u"取り違え(engine)の向き"] = collections.OrderedDict((k, sum(1 for r in mis if r[u"取り違え(engine)"] == k)) for k in (u"前期の文 × engine 当期", u"当期の文 × engine 前期"))
    T[u"取り違え(engine)の state"] = collections.OrderedDict((s, sum(1 for r in mis if r[u"state"] == s)) for s in STATES)
    T[u"取り違え(engine)の札"] = _cnt(r[u"札"] for r in mis)
    T[u"取り違え(engine)の印"] = collections.OrderedDict((m, sum(1 for r in mis if r[u"印"] == m)) for m in MARKS)
    T[u"取り違え(engine)の id"] = [r[u"id"] for r in mis]
    T[u"取り違え(engine)で GROUNDED の id"] = [r[u"id"] for r in mis if r[u"state"] == u"GROUNDED"]
    T[u"取り違えの中身(参考)"] = collections.OrderedDict((k, sum(1 for r in mis if r[u"取り違えの中身(参考)"] == k)) for k in KINDS)
    T[u"取り違えの中身(参考)× 向き"] = collections.OrderedDict((d, collections.OrderedDict((k, sum(1 for r in mis if r[u"取り違え(engine)"] == d and r[u"取り違えの中身(参考)"] == k)) for k in KINDS))
                                                      for d in (u"前期の文 × engine 当期", u"当期の文 × engine 前期"))
    T[u"取り違えの中身(参考)× GROUNDED"] = collections.OrderedDict((k, sum(1 for r in mis if r[u"state"] == u"GROUNDED" and r[u"取り違えの中身(参考)"] == k)) for k in KINDS)
    T[u"取り違えの中身(参考)の id"] = collections.OrderedDict((k, [r[u"id"] for r in mis if r[u"取り違えの中身(参考)"] == k]) for k in KINDS)
    T[u"取り違え(engine)で R1 で決まった行"] = sum(1 for r in mis if r[u"R1 で決まった行"])
    T[u"取り違え(engine)で R1 で決まった行の id"] = [r[u"id"] for r in mis if r[u"R1 で決まった行"]]
    judged = [r for r in loc if r[u"取り違え(engine)"] is not None]
    T[u"取り違えを判定した行(率でなく engine が 当期 か 前期)"] = len(judged)
    chk = [r for r in loc if r[u"印の確かめ(札)で違う"] is not None]
    T[u"印の確かめ(札)を当てた行"] = len(chk)
    T[u"印の確かめ(札)で違う"] = sum(1 for r in chk if r[u"印の確かめ(札)で違う"])
    T[u"印の確かめ(札)で違う id"] = [r[u"id"] for r in chk if r[u"印の確かめ(札)で違う"]]
    T[u"根拠の期の分布(札 真・位置が決まる)"] = _cnt(r[u"根拠の期"] for r in loc if r[u"札"] == u"真")
    byid = {r[u"id"]: r for r in rows}
    T[u"配線: N081・N145 が 印 同・engine 当期"] = sum(1 for i in WIRE_IDS if byid[i][u"印"] == u"同" and byid[i][u"engine の期"] == u"当期")
    T[u"配線: N039 の印と engine の期"] = collections.OrderedDict([(u"印", byid[u"N039"][u"印"]), (u"engine の期", byid[u"N039"][u"engine の期"]), (u"根拠の期", byid[u"N039"][u"根拠の期"])])
    none_rows = [r for r in loc if r[u"印"] == u"なし" and not r[u"率の文"] and r[u"engine の期"] in (u"当期", u"前期")]
    T[u"印なし(率でなく engine が 当期 か 前期)"] = len(none_rows)
    T[u"印なし で engine が 前期"] = sum(1 for r in none_rows if r[u"engine の期"] == u"前期")
    T[u"印なし で engine が 前期 の割合"] = pct(T[u"印なし で engine が 前期"], len(none_rows))
    T[u"印なし で engine が 前期 の id"] = [r[u"id"] for r in none_rows if r[u"engine の期"] == u"前期"]
    T[u"engine の期の分布(位置が決まる)"] = collections.OrderedDict((e, sum(1 for r in loc if r[u"engine の期"] == e)) for e in ENGINE_PERIODS)
    return T


def judge(T):
    b = BOUNDS
    J = collections.OrderedDict()
    J[u"K-1"] = b[u"K-1"][0] <= T[u"印あり(同 + 前期 + 当期)"] <= b[u"K-1"][1]
    J[u"K-2"] = b[u"K-2"][0] <= T[u"印の分布"][u"同"] <= b[u"K-2"][1]
    J[u"K-3"] = T[u"印 同 で engine が 前期 の割合"] is not None and T[u"印 同 で engine が 前期 の割合"] <= b[u"K-3"]
    J[u"K-4"] = b[u"K-4"][0] <= T[u"取り違え(engine)の向き"][u"前期の文 × engine 当期"] <= b[u"K-4"][1]
    J[u"K-5"] = b[u"K-5"][0] <= T[u"取り違え(engine)の向き"][u"当期の文 × engine 前期"] <= b[u"K-5"][1]
    J[u"K-6"] = b[u"K-6"][0] <= T[u"取り違え(engine)の state"][u"GROUNDED"] <= b[u"K-6"][1]
    J[u"K-7"] = b[u"K-7"][0] <= T[u"印の確かめ(札)で違う"] <= b[u"K-7"][1]
    J[u"K-8"] = (T[u"配線: N081・N145 が 印 同・engine 当期"] == b[u"K-8"] and T[u"配線: N039 の印と engine の期"][u"engine の期"] == u"当期")
    J[u"K-9"] = T[u"印なし で engine が 前期 の割合"] is not None and T[u"印なし で engine が 前期 の割合"] <= b[u"K-9"]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"K-10"] = u"判定しない"
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
    oth = load_module(MATERIALS[u"prev_script"][0], "other_rule_for_period_mark")
    claims = jload(os.path.join(ROOT, MATERIALS[u"claims"][0]))[u"claims"]
    labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, MATERIALS[u"labels"][0]))[u"labels"]}
    entry = jload(os.path.join(ROOT, MATERIALS[u"entry"][0]))
    entry_claims = {c[u"id"]: c for c in entry[u"claims"]}
    prev = jload(os.path.join(ROOT, MATERIALS[u"prev_rec"][0]))
    rows = build_rows(oth, claims, labels, entry_claims, prev[u"行"])
    T = tally(rows)
    prev_loc = {r[u"id"]: r[u"数の位置"] for r in prev[u"行"]}
    W = collections.OrderedDict()
    W[u"(a) 材料の sha256 が封の値"] = True
    W[u"(b) claims 415・札 415・entry 412"] = (len(claims) == 415 and len(labels) == 415 and len(entry_claims) == 412)
    W[u"(c) entry の profile"] = entry.get(u"profile")
    W[u"(d) 数の位置が「その他」の便の記録と一致した行"] = sum(1 for r in rows if prev_loc.get(r[u"id"]) == r[u"数の位置"])
    W[u"(e) 位置が決まる行"] = T[u"位置が決まる行"]
    W[u"(f) R1 で決まった行(前の便の記録)"] = sum(1 for r in rows if r[u"R1 で決まった行"])
    W[u"通った"] = bool(W[u"(a) 材料の sha256 が封の値"] and W[u"(b) claims 415・札 415・entry 412"] and W[u"(d) 数の位置が「その他」の便の記録と一致した行"] == len(rows))
    rec = collections.OrderedDict()
    rec[u"注意"] = (u"AI の文の数の直前の字から期の印(同 / 前期 / 当期 / なし)を字の規則で拾い、engine(P16)が指した fact の context の期・札の根拠の期と突き合わせて"
                  u"取り違えの数と向きを数えた記録。engine は走らせていない。1 書類・1 model の AI の文。docID は書かない。")
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT}
    rec[u"HEAD の commit"] = git_head()
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"読んだ材料の sha256"] = shas
    rec[u"定数"] = collections.OrderedDict([(u"印", list(MARKS)), (u"前期の字", list(PRIOR_WORDS)), (u"当期の字", list(CUR_WORDS)), (u"W の末尾の字数", TAIL),
                                         (u"engine の期", u"pointers の 1 つ目の context: CurrentYear → 当期、Prior1Year → 前期、Prior2〜9Year → 2 期前以前、他、空 → 指せず"),
                                         (u"根拠の期の字", collections.OrderedDict([(u"前期", list(GROUNDS_PRIOR)), (u"当期", list(GROUNDS_CUR))])),
                                         (u"率の文の単位", list(RATE_UNITS)), (u"配線の id", list(WIRE_IDS)), (u"予測の幅", BOUNDS)])
    rec[u"配線の門"] = W
    rec[u"行"] = rows
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T)
    rec[u"limits"] = [u"印の字の規則は AI の文の書き方を全部は覆わない", u"engine が期をどう決めているかは読まない(pointers の context だけ)",
                     u"1 書類・1 model の AI の文。P16 の判定。P27 は期を留めているので同じ行の判定は別", u"engine の期の結びつきを変えるかは人間が決める"]
    rec[u"key_leaks"] = record_key_leaks(rec)
    text = json.dumps(rec, ensure_ascii=False)
    if DOCID_RE.search(text):
        raise Stop(u"記録に docID が入った")
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print(u"written: %s" % a.out)
    print(json.dumps(W, ensure_ascii=False))
    for k in (u"印の分布", u"印あり(同 + 前期 + 当期)", u"印 × engine の期", u"率の文(位置が決まる)", u"印 同 で engine が 当期 か 前期 の行", u"印 同 で engine が 前期", u"印 同 で engine が 前期 の割合",
              u"取り違え(engine)", u"取り違え(engine)の向き", u"取り違え(engine)の state", u"取り違え(engine)の札", u"取り違え(engine)の印", u"取り違え(engine)の id",
              u"取り違え(engine)で GROUNDED の id", u"取り違え(engine)で R1 で決まった行の id", u"印の確かめ(札)を当てた行", u"印の確かめ(札)で違う", u"印の確かめ(札)で違う id",
              u"根拠の期の分布(札 真・位置が決まる)", u"配線: N081・N145 が 印 同・engine 当期", u"配線: N039 の印と engine の期", u"印なし(率でなく engine が 当期 か 前期)",
              u"印なし で engine が 前期", u"印なし で engine が 前期 の割合", u"engine の期の分布(位置が決まる)"):
        print(k, json.dumps(T[k], ensure_ascii=False))
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
