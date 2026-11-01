# -*- coding: utf-8 -*-
u"""帯を fact の ``decimals`` の粒度にした版の門。封 ``docs/XBRL_DELTA_DECIMALS_SEAL_2026-11-01.md`` §5 の 5。

記録 ``fixtures/xbrl/delta_decimals_2026-11-01.json``(``measure/xbrl_delta_decimals_2026-11-01.py`` の出力)・文書 ``docs/XBRL_DELTA_DECIMALS_DIAG_2026-11-01.md``。
**帯の中に入っても出所と判定しない(封 §4 の 1)。** 門もその言い方だけを許す。

  (a) 記録が在り、鍵が揃う(行 296・配線の門・集計 3 本・定数・key_leaks 空)。
  (b) 配線 (a)〜(d) を記録と前の便の記録から数え直す。
  (e) 段・k・符号の照合・集計(全体・探索・検証)を、行の値から別実装で求め直して記録と一致させる。
  (c) 文書の表(``<!-- 門:start 名前 -->``)を記録と封から作り直して 1 字も違わない。門の外の散文の数には【門なし】の印が要る。
  (d) B-1〜B-9 の当否を、封の字(幅)と記録から求め直す。封の字と文書の当否の表の字が一致する。
  (h) docID・claim の id が封と文書に無い。禁止語・言い過ぎの語が文書に無い。
  (i) 順序: 封の commit < script・記録・文書・門の commit。追跡されていない file は『足した commit が無い』で赤(skip にしない)。
  (l) script は engine・網の module を import しない。script の純関数が記録の全行と一致する。帯の式の字が封と同じ。
  (g) 偽物で赤(記録の 1 行の段・e の 1 字・文書の表の 1 字・封の幅の 1 字・文書に docID・script の帯の式の変異)。
  (m) ``tests/measure/test_xbrl_fresh_seal.py`` の ``LATER_NAMING_FILES`` に記録・script・門の 3 つ組が在る。
"""
import collections
import copy
import importlib.util
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"

SEAL_REL = "docs/XBRL_DELTA_DECIMALS_SEAL_2026-11-01.md"
DOC_REL = "docs/XBRL_DELTA_DECIMALS_DIAG_2026-11-01.md"
REC_REL = "fixtures/xbrl/delta_decimals_2026-11-01.json"
SCRIPT_REL = "measure/xbrl_delta_decimals_2026-11-01.py"
GATE_REL = "tests/measure/test_xbrl_delta_decimals.py"
INPUT_REL = "fixtures/xbrl/delta_naming_2026-10-30.json"
FRESH_SEAL_REL = "tests/measure/test_xbrl_fresh_seal.py"
SEAL, DOC, REC, SCRIPT = [os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL)]
SEAL_COMMIT_SHORT = "777003b"
INPUT_SHA256 = "27aca660570ddb37e8d9d1bc4826d8d2cfef931e0120c2484d688a4fe449b78f"
NOT_GATED = u"【門なし】"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社", u"USD", u"金額")
OVERCLAIM = (u"出所として正しい", u"正しい出所", u"出所と判定", u"出所を特定", u"出所を突き止め", u"仮説は正しかった", u"仮説が正しい",
             u"仮説は裏づけ", u"根拠になる")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
CLAIM_ID_RE = re.compile(r"(?<![A-Za-z0-9_\-])N\d{3}(?![0-9])")

NROWS, N_UNCOMPARABLE, N_PREV_IN_BAND = 296, 16, 39
STAGES = (u"完全一致", u"丸めの帯 H", u"丸めの帯 F", u"不一致", u"比較不能")
IN_BAND = (u"完全一致", u"丸めの帯 H", u"丸めの帯 F")
PREV_IN_BAND = (u"完全一致", u"許容差内", u"符号不一致")
EXPLORE, VERIFY = u"探索", u"検証"
GROUPS = (u"全体", EXPLORE, VERIFY)
TABLE_NAMES = ["pred", "wiring", "stages", "k", "sign", "width", "ten"]
PRED_IDS = [u"B-%d" % i for i in range(1, 10)]
STAGE_KEYS = (u"段", u"帯の中", u"前の段 × 新の段", u"単位 × 段", u"decimals(当期, 前期)× 単位 × 段", u"型 × 段", u"期 × 段", u"粗い × 段",
              u"member × 段", u"型 × 帯の中", u"単位 × 帯の中", u"粗い × 帯の中", u"粗い × 帯の中 × 段")
K_KEYS = (u"帯の中の k", u"k がちょうど +1", u"k がちょうど -1", u"k が負", u"|k| が 2 以上", u"前の段が不一致で帯の中に入った行の k",
          u"前の段が不一致で帯の中に入った行")
SIGN_KEYS = (u"帯の中の符号の照合", u"帯の中の向き")
WIDTH_KEYS = (u"G の値 × 行数", u"G の値 × 帯の中")


# ---------------------------------------------------------------- 読む

def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def git(*args):
    u"""repo の根(audit-core/ の親)で git を呼ぶ。道は PREFIX つき(``audit-core/...``)。"""
    r = subprocess.run(["git"] + list(args), cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout.decode("utf-8", "replace").strip()


def yesno(b):
    return u"はい" if b else u"いいえ"


def table(head, rows):
    out = [u"| " + u" | ".join(head) + u" |", u"|" + u"---|" * len(head)]
    for r in rows:
        out.append(u"| " + u" | ".join(u"%s" % c for c in r) + u" |")
    return out


# ---------------------------------------------------------------- 別実装(封 §2-1〜§2-3)

def ref_g(dec):
    return None if dec is None else 10.0 ** (-int(dec))


def ref_stage(prev, d, t, g_c, g_p, u):
    if prev == u"比較不能" or None in (d, t, g_c, g_p):
        return u"比較不能", None, None, None
    G = g_c + g_p + u
    H = G / 2.0
    e = abs(abs(d) - t)
    if e == 0:
        s = u"完全一致"
    elif e <= H:
        s = u"丸めの帯 H"
    elif e <= G:
        s = u"丸めの帯 F"
    else:
        s = u"不一致"
    return s, e, G, H


def ref_k(d, t, g_c, g_p):
    return round((abs(d) - t) / max(g_c, g_p), 6)


def ref_sign(direction, d, in_band):
    if not in_band or direction not in (u"増", u"減") or d == 0:
        return None
    return u"期待どおり" if ((d > 0) if direction == u"増" else (d < 0)) else u"符号不一致"


def ref_bucket(k):
    if k <= -3:
        return u"-3 以下"
    if k >= 3:
        return u"3 以上"
    return (u"%g" % k) if k != 0 else u"0"


def row_problems(r):
    g_c, g_p = ref_g(r[u"当期の decimals"]), ref_g(r[u"前期の decimals"])
    s, e, G, H = ref_stage(r[u"前の段"], r[u"差"], r[u"文の値"], g_c, g_p, r[u"帯の幅"])
    p = []
    if r[u"段"] != s:
        p.append(u"段 %s != %s" % (r[u"段"], s))
    if r.get(u"g_c") != g_c or r.get(u"g_p") != g_p:
        p.append(u"g")
    if s == u"比較不能":
        if any(r[k] is not None for k in (u"G", u"H", u"e", u"k", u"符号の照合")):
            p.append(u"比較不能の行に値")
        return p
    if r[u"G"] != G or r[u"H"] != H or r[u"e"] != e:
        p.append(u"G/H/e")
    if r[u"k"] != ref_k(r[u"差"], r[u"文の値"], g_c, g_p):
        p.append(u"k")
    if r[u"符号の照合"] != ref_sign(r[u"向き"], r[u"差"], s in IN_BAND):
        p.append(u"符号")
    if (r[u"探索/検証"] == EXPLORE) != (r[u"位置"] <= 37):
        p.append(u"探索/検証")
    return p


def _cnt(it):
    c = collections.Counter(it)
    return collections.OrderedDict((k, c[k]) for k in sorted(c, key=lambda x: (str(type(x)), x)))


def _full(keys, it):
    c = collections.Counter(it)
    return collections.OrderedDict((k, c.get(k, 0)) for k in keys)


def ref_tally(rows):
    inb = [r for r in rows if r[u"段"] in IN_BAND]
    coarse = lambda r: u"粗い" if r[u"decimals が文の単位より粗い"] else u"粗くない"
    st = collections.OrderedDict([
        (u"段", _full(STAGES, (r[u"段"] for r in rows))), (u"帯の中", len(inb)),
        (u"前の段 × 新の段", _cnt(u"%s / %s" % (r[u"前の段"], r[u"段"]) for r in rows)),
        (u"単位 × 段", _cnt(u"%s / %s" % (r[u"単位"], r[u"段"]) for r in rows)),
        (u"decimals(当期, 前期)× 単位 × 段", _cnt(u"(%s, %s) / %s / %s" % (r[u"当期の decimals"], r[u"前期の decimals"], r[u"単位"], r[u"段"]) for r in rows)),
        (u"型 × 段", _cnt(u"%s / %s" % (r[u"型"], r[u"段"]) for r in rows)),
        (u"期 × 段", _cnt(u"%s / %s" % (r[u"期"], r[u"段"]) for r in rows)),
        (u"粗い × 段", _cnt(u"%s / %s" % (coarse(r), r[u"段"]) for r in rows)),
        (u"member × 段", _cnt(u"%s / %s" % (r[u"member"], r[u"段"]) for r in rows)),
        (u"型 × 帯の中", _cnt(r[u"型"] for r in inb)), (u"単位 × 帯の中", _cnt(r[u"単位"] for r in inb)),
        (u"粗い × 帯の中", _cnt(coarse(r) for r in inb)),
        (u"粗い × 帯の中 × 段", _cnt(r[u"段"] for r in inb if r[u"decimals が文の単位より粗い"]))])
    K = collections.OrderedDict([
        (u"帯の中の k", _cnt(ref_bucket(r[u"k"]) for r in inb)), (u"k がちょうど +1", sum(1 for r in inb if r[u"k"] == 1)),
        (u"k がちょうど -1", sum(1 for r in inb if r[u"k"] == -1)), (u"k が負", sum(1 for r in inb if r[u"k"] < 0)),
        (u"|k| が 2 以上", sum(1 for r in inb if abs(r[u"k"]) >= 2)),
        (u"前の段が不一致で帯の中に入った行の k", _cnt(ref_bucket(r[u"k"]) for r in inb if r[u"前の段"] == u"不一致")),
        (u"前の段が不一致で帯の中に入った行", sum(1 for r in inb if r[u"前の段"] == u"不一致"))])
    S = collections.OrderedDict([
        (u"帯の中の符号の照合", _full((u"期待どおり", u"符号不一致"), (r[u"符号の照合"] for r in inb if r[u"符号の照合"]))),
        (u"帯の中の向き", _full((u"増", u"減", u"不明", u"なし"), (r[u"向き"] for r in inb)))])
    W = collections.OrderedDict([
        (u"G の値 × 行数", _cnt(u"%g" % r[u"G"] for r in rows if r[u"G"] is not None)),
        (u"G の値 × 帯の中", _cnt(u"%g" % r[u"G"] for r in inb))])
    ten = [[r[u"位置"], r[u"前の段"], r[u"段"]] for r in sorted(rows, key=lambda x: x[u"位置"]) if r[u"10 行"]]
    return collections.OrderedDict([("stages", st), ("k", K), ("sign", S), ("width", W), ("ten", ten)])


def groups_of(rows):
    return collections.OrderedDict([(u"全体", rows), (EXPLORE, [r for r in rows if r[u"探索/検証"] == EXPLORE]),
                                    (VERIFY, [r for r in rows if r[u"探索/検証"] == VERIFY])])


def tally_problems(rec):
    p = []
    for g, rows in groups_of(rec[u"行"]).items():
        want = json.loads(json.dumps(ref_tally(rows), ensure_ascii=False))
        got = rec[u"集計"][g]
        for sec in ("stages", "k", "sign", "width", "ten"):
            if json.dumps(got.get(sec), sort_keys=True) != json.dumps(want[sec], sort_keys=True):
                p.append(u"%s/%s" % (g, sec))
    return p


# ---------------------------------------------------------------- 配線(記録と前の記録から数え直す)

def wiring_problems(rec, inp):
    p = []
    g = rec[u"配線の門"]
    rows = rec[u"行"]
    src = dict((r[u"位置"], r) for r in inp[u"行"])
    if rec[u"読んだ入力の sha256"].get(INPUT_REL) != INPUT_SHA256 or g[u"(a) 入力の sha256 が封の値と一致"] is not True:
        p.append("a")
    pos = sorted(r[u"位置"] for r in rows)
    unc = sum(1 for r in rows if r[u"段"] == u"比較不能")
    if not (len(rows) == NROWS and pos == list(range(NROWS)) and unc == N_UNCOMPARABLE and g[u"(b) 行 296・位置 0〜295 が 1 回ずつ・比較不能 16"] == [True, True]):
        p.append("b")
    prev = [r for r in rows if r[u"前の段"] in PREV_IN_BAND]
    c = [sum(1 for r in prev if r[u"段"] in IN_BAND), len(prev)]
    if not (c == [N_PREV_IN_BAND, N_PREV_IN_BAND] and g[u"(c) 前の便の帯の中 39 行が全部この便の帯の中"] == c):
        p.append("c")
    same = sum(1 for r in rows if (r[u"文の値"], r[u"差"], r[u"帯の幅"], r[u"前の段"], r[u"当期の decimals"], r[u"前期の decimals"], r[u"型"], r[u"単位"], r[u"向き"], r[u"10 行"])
               == (src[r[u"位置"]][u"文の値"], src[r[u"位置"]][u"差"], src[r[u"位置"]][u"帯の幅"], src[r[u"位置"]][u"段"], src[r[u"位置"]][u"当期の decimals"],
                   src[r[u"位置"]][u"前期の decimals"], src[r[u"位置"]][u"型"], src[r[u"位置"]][u"単位"], src[r[u"位置"]][u"向き"], src[r[u"位置"]][u"10 行"]))
    if not (same == NROWS and g[u"(d) 行ごとの t・d・u が前の記録と同じ"] == [NROWS, NROWS]):
        p.append("d")
    if g[u"通った"] is not True:
        p.append(u"通った")
    return p


# ---------------------------------------------------------------- 封 §3 の当否(幅は封の字から読む)

def seal_predictions(seal):
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(B-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            cells = [c.strip() for c in body.split(u" | ")]
            assert len(cells) == 3, l
            out[m.group(1)] = tuple(cells)
    return out


def num(s):
    return int(s.replace(u",", u""))


def rng(s):
    m = re.match(r"^\s*(\d[\d,]*)(?:〜(\d[\d,]*))?", s)
    lo = num(m.group(1))
    return (lo, num(m.group(2)) if m.group(2) else lo)


def within(v, r):
    return r[0] <= v <= r[1]


def bolds(pred):
    return [rng(x) for x in re.findall(r"\*\*(\d[^*]*)\*\*", pred)]


def after_label(pred, label):
    m = re.search(re.escape(label) + r"\s*(\d+〜\d+)", pred)
    return rng(m.group(1))


def measures(rec, group=u"全体"):
    T = rec[u"集計"][group]
    st, K, S = T["stages"], T["k"], T["sign"]
    m = collections.OrderedDict()
    m[u"比較不能"] = st[u"段"][u"比較不能"]
    m[u"帯の中"] = st[u"帯の中"]
    m[u"完全一致"] = st[u"段"][u"完全一致"]
    m[u"H"] = st[u"段"][u"丸めの帯 H"]
    m[u"F"] = st[u"段"][u"丸めの帯 F"]
    m[u"不一致から帯の中"] = K[u"前の段が不一致で帯の中に入った行"]
    m[u"不一致のまま"] = st[u"前の段 × 新の段"].get(u"不一致 / 不一致", 0)
    for u in (u"円", u"千円", u"百万円"):
        m[u"単位 %s" % u] = st[u"単位 × 帯の中"].get(u, 0)
    m[u"粗い 帯の中"] = st[u"粗い × 帯の中"].get(u"粗い", 0)
    m[u"粗い 完全一致"] = st[u"粗い × 帯の中 × 段"].get(u"完全一致", 0)
    m[u"k +1"] = K[u"k がちょうど +1"]
    m[u"k 負"] = K[u"k が負"]
    m[u"|k| 2 以上"] = K[u"|k| が 2 以上"]
    kk = K[u"帯の中の k"]
    m[u"k 最多"] = (max(kk, key=lambda x: (kk[x], x == u"1")) == u"1") if kk else False
    m[u"符号不一致"] = S[u"帯の中の符号の照合"].get(u"符号不一致", 0)
    for t in (u"増減の型", u"流量の型", u"区分の型", u"その他"):
        m[u"型 %s" % t] = st[u"型 × 帯の中"].get(t, 0)
    return m


def judge(rec, seal):
    u"""{B-n: (実測の字, 当たり/外れ(True/False))}。幅は封の予測の字から読む。"""
    P = seal_predictions(seal)
    m = measures(rec)
    g = rec[u"配線の門"]
    J = collections.OrderedDict()
    J[u"B-1"] = (u"配線 (a)〜(e) 通った: %s。比較不能 %d" % (yesno(g[u"通った"]), m[u"比較不能"]),
                 bool(g[u"通った"]) and m[u"比較不能"] == N_UNCOMPARABLE)
    b = bolds(P[u"B-2"][1])
    J[u"B-2"] = (u"帯の中 %d(完全一致 %d・丸めの帯 H %d・丸めの帯 F %d)" % (m[u"帯の中"], m[u"完全一致"], m[u"H"], m[u"F"]),
                 within(m[u"帯の中"], b[0]) and within(m[u"完全一致"], b[1]) and within(m[u"H"], b[2]) and within(m[u"F"], b[3]))
    b = bolds(P[u"B-3"][1])
    J[u"B-3"] = (u"不一致 241 から帯の中に入った行 %d・不一致のまま %d" % (m[u"不一致から帯の中"], m[u"不一致のまま"]),
                 within(m[u"不一致から帯の中"], b[0]) and within(m[u"不一致のまま"], b[1]))
    b = bolds(P[u"B-4"][1])
    units = [m[u"単位 円"], m[u"単位 千円"], m[u"単位 百万円"]]
    J[u"B-4"] = (u"帯の中の単位: 円 %d・千円 %d・百万円 %d" % tuple(units),
                 all(within(v, r) for v, r in zip(units, b)) and units[1] > max(units[0], units[2]))
    b = bolds(P[u"B-5"][1])
    r_exact = after_label(P[u"B-5"][1], u"完全一致")
    J[u"B-5"] = (u"粗い行の帯の中 %d(うち完全一致 %d)" % (m[u"粗い 帯の中"], m[u"粗い 完全一致"]),
                 within(m[u"粗い 帯の中"], b[0]) and within(m[u"粗い 完全一致"], r_exact))
    b = bolds(P[u"B-6"][1])
    J[u"B-6"] = (u"k がちょうど +1 の行 %d(最多: %s)・k が負の行 %d・|k| が 2 以上の行 %d" % (m[u"k +1"], yesno(m[u"k 最多"]), m[u"k 負"], m[u"|k| 2 以上"]),
                 within(m[u"k +1"], b[0]) and m[u"k 最多"] and within(m[u"k 負"], b[1]) and within(m[u"|k| 2 以上"], b[2]))
    b = bolds(P[u"B-7"][1])
    ex = measures(rec, EXPLORE)
    J[u"B-7"] = (u"探索 38 行の帯の中 %d" % ex[u"帯の中"], within(ex[u"帯の中"], b[0]))
    b = bolds(P[u"B-8"][1])
    J[u"B-8"] = (u"帯の中の符号不一致 %d" % m[u"符号不一致"], within(m[u"符号不一致"], b[0]))
    b = bolds(P[u"B-9"][1])
    types = [m[u"型 増減の型"], m[u"型 流量の型"], m[u"型 区分の型"], m[u"型 その他"]]
    J[u"B-9"] = (u"帯の中の型: 増減の型 %d・流量の型 %d・区分の型 %d・その他 %d" % tuple(types),
                 all(within(v, r) for v, r in zip(types, b)) and types[0] >= max(types[1:]))
    assert list(J) == PRED_IDS
    return J


def group_text(rec, k):
    u"""探索・検証の実測の字(当否は付けない)。"""
    out = []
    for g in (EXPLORE, VERIFY):
        m = measures(rec, g)
        if k == u"B-1":
            out.append(u"比較不能 %d" % m[u"比較不能"])
        elif k == u"B-2":
            out.append(u"帯の中 %d(完全一致 %d・H %d・F %d)" % (m[u"帯の中"], m[u"完全一致"], m[u"H"], m[u"F"]))
        elif k == u"B-3":
            out.append(u"不一致から帯の中 %d・不一致のまま %d" % (m[u"不一致から帯の中"], m[u"不一致のまま"]))
        elif k == u"B-4":
            out.append(u"円 %d・千円 %d・百万円 %d" % (m[u"単位 円"], m[u"単位 千円"], m[u"単位 百万円"]))
        elif k == u"B-5":
            out.append(u"粗い行の帯の中 %d(完全一致 %d)" % (m[u"粗い 帯の中"], m[u"粗い 完全一致"]))
        elif k == u"B-6":
            out.append(u"k +1 %d・負 %d・|k| 2 以上 %d" % (m[u"k +1"], m[u"k 負"], m[u"|k| 2 以上"]))
        elif k == u"B-7":
            out.append(u"帯の中 %d" % m[u"帯の中"])
        elif k == u"B-8":
            out.append(u"符号不一致 %d" % m[u"符号不一致"])
        else:
            out.append(u"増減 %d・流量 %d・区分 %d・その他 %d" % (m[u"型 増減の型"], m[u"型 流量の型"], m[u"型 区分の型"], m[u"型 その他"]))
    return out


def fmt(v):
    if isinstance(v, dict):
        return u"・".join(u"%s %s" % (k, v[k]) for k in v) if v else u"(なし)"
    return u"%s" % v


def three_cols(rec, sec, keys):
    rows = []
    for k in keys:
        rows.append([k] + [fmt(rec[u"集計"][g][sec].get(k)) for g in GROUPS])
    return table([u"項目", u"全体 296", u"探索 38", u"検証 258"], rows)


def render_blocks(rec, seal):
    B = collections.OrderedDict()
    P = seal_predictions(seal)
    J = judge(rec, seal)
    rows = []
    for k, (field, pred, miss) in P.items():
        text, hit = J[k]
        g = group_text(rec, k)
        rows.append([u"**%s**" % k, field, pred, miss, text, u"**当たり**" if hit else u"**外れ**", g[0], g[1]])
    B["pred"] = table([u"#", u"欄", u"予測(封の字)", u"外れ方(封の字)", u"実測 全体 296(記録から)", u"当たり外れ(296 で判定)", u"探索 38 の実測(当否なし)", u"検証 258 の実測(当否なし)"], rows)
    g = rec[u"配線の門"]
    rows = [[u"(a) 入力の sha256 が封の値と一致", yesno(g[u"(a) 入力の sha256 が封の値と一致"])],
            [u"(b) 行 296・位置 0〜295 が 1 回ずつ・比較不能 16", u"%s・%s" % tuple(yesno(x) for x in g[u"(b) 行 296・位置 0〜295 が 1 回ずつ・比較不能 16"])],
            [u"(c) 前の便の帯の中 39 行が全部この便の帯の中", u"%d / %d" % tuple(g[u"(c) 前の便の帯の中 39 行が全部この便の帯の中"])],
            [u"(d) 行ごとの t・d・u が前の記録と同じ", u"%d / %d" % tuple(g[u"(d) 行ごとの t・d・u が前の記録と同じ"])],
            [u"(e) adapters・core・入力の記録に未 commit の変更なし", yesno(g[u"(e) adapters・core・入力の記録に未 commit の変更なし"])],
            [u"(e) 封の commit が HEAD の祖先", yesno(g[u"(e) 封の commit が HEAD の祖先"])],
            [u"配線の門が通って script は記録を書いた", yesno(g[u"通った"])],
            [u"読んだ入力の sha256", u"`%s`" % rec[u"読んだ入力の sha256"][INPUT_REL]],
            [u"測定時の HEAD の commit", u"`%s`" % rec[u"HEAD の commit"]],
            [u"封の commit", u"`%s`" % rec[u"封"][u"commit"]],
            [u"key_leaks(記録の鍵らしい字の件数)", u"%d" % len(rec[u"key_leaks"])],
            [u"行の数(全体・探索・検証)", u"%d・%d・%d" % tuple(len(v) for v in groups_of(rec[u"行"]).values())]]
    B["wiring"] = table([u"配線の門", u"値"], rows)
    B["stages"] = three_cols(rec, "stages", STAGE_KEYS)
    B["k"] = three_cols(rec, "k", K_KEYS)
    B["sign"] = three_cols(rec, "sign", SIGN_KEYS)
    B["width"] = three_cols(rec, "width", WIDTH_KEYS)
    B["ten"] = table([u"位置", u"前の段", u"新の段", u"探索/検証"], [r + [EXPLORE if r[0] <= 37 else VERIFY] for r in rec[u"集計"][u"全体"]["ten"]])
    assert list(B) == TABLE_NAMES
    return B


BLOCK_RE = re.compile(r"<!-- 門:start (\S+) -->\n(.*?)\n<!-- 門:end -->", re.S)


def doc_blocks(doc):
    return collections.OrderedDict((m.group(1), m.group(2).split(u"\n")) for m in BLOCK_RE.finditer(doc))


def block_problems(rec, seal, doc):
    D = doc_blocks(doc)
    B = render_blocks(rec, seal)
    p = []
    if list(D) != TABLE_NAMES:
        p.append(u"表の名前と順: %s" % list(D))
    for k in TABLE_NAMES:
        if D.get(k) != B[k]:
            p.append(k)
    return p


def prose_problems(doc):
    p = []
    in_block = False
    for ln in doc.splitlines():
        if ln.startswith(u"<!-- 門:start"):
            in_block = True
            continue
        if ln.startswith(u"<!-- 門:end"):
            in_block = False
            continue
        if in_block or ln.startswith(u"|") or ln.startswith(u"#") or not ln.strip():
            continue
        s = re.sub(r"`[^`]*`", u" ", ln)
        s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
        s = re.sub(r"[BDE]-\d+|§\d+(-\d+)*", u" ", s)
        if re.search(r"\d", s) and NOT_GATED not in ln:
            p.append(ln[:60])
    if u"<!-- 門:start pred -->" not in doc or doc.index(u"<!-- 門:start pred -->") > doc.index(u"## 2."):
        p.append(u"pred が先頭でない")
    for w in FORBIDDEN + OVERCLAIM:
        if w in doc:
            p.append(u"禁止語 %s" % w)
    return p


def id_problems(text):
    return sorted(set(DOCID_RE.findall(text)) | set(CLAIM_ID_RE.findall(text)))


# ---------------------------------------------------------------- 順序(git)

def added_commits(path):
    rc, out = git("log", "--diff-filter=A", "--format=%H", "--", path)
    return [l for l in out.splitlines() if l.strip()] if rc == 0 else []


def is_anc(a, b):
    return a is not None and b is not None and git("merge-base", "--is-ancestor", a, b)[0] == 0


def order_problems():
    p = []
    s = added_commits(PREFIX + SEAL_REL)
    if len(s) != 1 or not HEX40.match(s[0]):
        return [u"封を足した commit がちょうど 1 つに決まらない(%d)" % len(s)]
    S = s[0]
    if not S.startswith(SEAL_COMMIT_SHORT):
        p.append(u"封の commit が %s でない" % SEAL_COMMIT_SHORT)
    if not is_anc(S, "HEAD"):
        p.append(u"封の commit が HEAD の祖先でない")
    for rel in (SCRIPT_REL, REC_REL, DOC_REL, GATE_REL):
        a = added_commits(PREFIX + rel)
        if not a:
            p.append(u"%s を足した commit が無い(未 commit)" % rel)
            continue
        A = a[-1]
        if A == S or not is_anc(S, A):
            p.append(u"%s が封の後でない" % rel)
    return p


# ---------------------------------------------------------------- script

def load_script():
    spec = importlib.util.spec_from_file_location("delta_decimals_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = jload(os.path.join(ROOT, INPUT_REL))
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def test_a_1_keys_rows_and_constants(self):
        for k in (u"注意", u"封", u"HEAD の commit", u"この script の sha256", u"読んだ入力の sha256", u"定数", u"配線の門", u"行", u"集計", u"limits", u"key_leaks"):
            self.assertIn(k, self.rec)
        self.assertEqual(len(self.rec[u"行"]), NROWS)
        self.assertEqual(self.rec[u"key_leaks"], [])
        self.assertEqual(self.rec[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertEqual(self.rec[u"定数"][u"G"], u"g_c + g_p + u(切り捨ての帯)")
        self.assertEqual(self.rec[u"定数"][u"H"], u"G / 2(四捨五入の帯)")
        self.assertEqual(list(self.rec[u"集計"]), list(GROUPS))

    def test_b_1_wiring_recounted(self):
        self.assertEqual(wiring_problems(self.rec, self.inp), [])

    def test_e_1_every_row_recomputed(self):
        bad = [(r[u"位置"], p) for r in self.rec[u"行"] for p in [row_problems(r)] if p]
        self.assertEqual(bad, [])

    def test_e_2_tallies_recounted(self):
        self.assertEqual(tally_problems(self.rec), [])

    def test_e_3_stage_counts_add_up(self):
        st = self.rec[u"集計"][u"全体"]["stages"][u"段"]
        self.assertEqual(sum(st.values()), NROWS)
        self.assertEqual(st[u"比較不能"], N_UNCOMPARABLE)
        self.assertEqual(sum(self.rec[u"集計"][g]["stages"][u"帯の中"] for g in (EXPLORE, VERIFY)), st[u"完全一致"] + st[u"丸めの帯 H"] + st[u"丸めの帯 F"])

    def test_j_1_no_text_in_record(self):
        keys = set()

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    keys.add(k)
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(self.rec)
        for bad in (u"span", u"文", u"段落", u"窓", u"ラベル", u"pointers", u"named"):
            self.assertNotIn(bad, keys)
        self.assertEqual(id_problems(json.dumps(self.rec[u"集計"], ensure_ascii=False)), [])

    def test_d_1_judgments_cover_nine_and_are_not_constant(self):
        J = judge(self.rec, self.seal)
        self.assertEqual(list(J), PRED_IDS)
        rec2 = copy.deepcopy(self.rec)
        for r in rec2[u"行"]:
            if r[u"段"] == u"不一致":
                r[u"段"] = u"丸めの帯 F"
        for g, rows in groups_of(rec2[u"行"]).items():
            rec2[u"集計"][g] = json.loads(json.dumps(ref_tally(rows), ensure_ascii=False))
        self.assertNotEqual([h for _, h in judge(rec2, self.seal).values()], [h for _, h in J.values()])

    def test_d_2_widths_are_read_from_the_seal(self):
        P = seal_predictions(self.seal)
        self.assertEqual(list(P), PRED_IDS)
        for k in PRED_IDS:
            self.assertTrue(P[k][2], u"%s の外れ方が空" % k)
        self.assertEqual(len(bolds(P[u"B-2"][1])), 4)
        self.assertEqual(len(bolds(P[u"B-9"][1])), 4)

    def test_c_1_tables_equal_rebuilt(self):
        self.assertEqual(block_problems(self.rec, self.seal, self.doc), [])

    def test_c_2_prose_is_marked_and_clean(self):
        self.assertEqual(prose_problems(self.doc), [])
        self.assertIn(u"丸めの帯の中に入った", self.doc)
        self.assertIn(SEAL_REL, self.doc)

    def test_h_1_no_docid_or_claim_id(self):
        self.assertEqual(id_problems(self.doc), [])
        self.assertEqual(id_problems(self.seal), [])
        self.assertEqual(id_problems(jtext(os.path.join(ROOT, GATE_REL))), [])

    def test_i_1_order(self):
        self.assertEqual(order_problems(), [])

    def test_l_1_script_is_pure_and_agrees(self):
        src = jtext(SCRIPT)
        import ast
        imported = set()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        for bad in ("adapters", "core", "audit_core", "urllib", "requests", "socket", "http", "zipfile", "importlib"):
            self.assertNotIn(bad, imported, bad)
        for bad in (u"os.environ", u"getenv", u"load_instance", u"verify_document("):
            self.assertNotIn(bad, src, bad)
        self.assertIn(u"G = g_c + g_p + u", src)
        self.assertIn(u"G / 2.0", src)
        self.assertIn(u"g_c + g_p + u", self.seal)
        self.assertIn(u"`H = G / 2`", self.seal)
        mod = load_script()
        rows = mod.build_rows(self.inp[u"行"])
        self.assertEqual(json.loads(json.dumps(rows, ensure_ascii=False)), self.rec[u"行"])
        self.assertEqual(mod.g_of("-3"), 1000.0)
        self.assertEqual(mod.band_of(1000.0, 1000.0, 1000), (3000.0, 1500.0))
        self.assertEqual(mod.stage_of(u"不一致", 3000.0, 1500.0, 3000.0, 1500.0)[0], u"丸めの帯 H")
        self.assertEqual(mod.stage_of(u"不一致", 4000.0, 1500.0, 3000.0, 1500.0)[0], u"丸めの帯 F")
        # 境界: e == H は H、e が H を 1 越えると F、e == G は F、e が G を 1 越えると不一致(封 §2-2 の ≤)
        self.assertEqual(mod.stage_of(u"不一致", 3001.0, 1500.0, 3000.0, 1500.0)[0], u"丸めの帯 F")
        self.assertEqual(mod.stage_of(u"不一致", 4500.0, 1500.0, 3000.0, 1500.0)[0], u"丸めの帯 F")
        self.assertEqual(mod.stage_of(u"不一致", 4501.0, 1500.0, 3000.0, 1500.0)[0], u"不一致")
        self.assertEqual(mod.stage_of(u"不一致", 5000.0, 1500.0, 3000.0, 1500.0)[0], u"不一致")
        self.assertEqual(mod.stage_of(u"不一致", 1500.0, 1500.0, 3000.0, 1500.0)[0], u"完全一致")
        self.assertEqual(mod.stage_of(u"比較不能", 1500.0, 1500.0, 3000.0, 1500.0)[0], u"比較不能")
        with io.open(SCRIPT, "rb") as fh:
            import hashlib
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), self.rec[u"この script の sha256"])

    def test_m_1_declared_in_fresh_seal(self):
        t = jtext(os.path.join(ROOT, FRESH_SEAL_REL))
        for rel in (REC_REL, SCRIPT_REL, GATE_REL):
            self.assertIn(u'"%s"' % rel, t)


class MutationTest(unittest.TestCase):
    u"""(g) 偽物で赤。"""

    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = jload(os.path.join(ROOT, INPUT_REL))
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def test_g_0_baseline_green(self):
        self.assertEqual(wiring_problems(self.rec, self.inp) + tally_problems(self.rec) + block_problems(self.rec, self.seal, self.doc) + prose_problems(self.doc), [])

    def test_g_1_one_stage_turned(self):
        rec = copy.deepcopy(self.rec)
        r = next(x for x in rec[u"行"] if x[u"段"] == u"丸めの帯 H")
        r[u"段"] = u"不一致"
        self.assertTrue(row_problems(r))
        self.assertTrue(tally_problems(rec))
        self.assertTrue(wiring_problems(rec, self.inp) or tally_problems(rec))

    def test_g_2_one_e_digit_turned(self):
        rec = copy.deepcopy(self.rec)
        r = next(x for x in rec[u"行"] if x[u"段"] == u"不一致")
        r[u"e"] = r[u"e"] + 1
        self.assertIn(u"G/H/e", row_problems(r))

    def test_g_3_one_table_character_turned(self):
        doc = self.doc.replace(u"| 帯の中 | 50 |", u"| 帯の中 | 51 |", 1) if u"| 帯の中 | 50 |" in self.doc else self.doc.replace(u"丸めの帯 H |", u"丸めの帯 H  |", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertTrue(block_problems(self.rec, self.seal, doc))

    def test_g_4_one_seal_width_turned(self):
        seal = self.seal.replace(u"帯の中に入る行 **10〜70**", u"帯の中に入る行 **12〜70**", 1)     # B-3 の下限を 1 字(実測 11 が幅の外に出る)
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(judge(self.rec, seal)[u"B-3"][1], judge(self.rec, self.seal)[u"B-3"][1])
        self.assertTrue(block_problems(self.rec, seal, self.doc))

    def test_g_5_docid_in_doc(self):
        fake_doc, fake_claim = u"S100" + u"ABCD", u"N" + u"001"      # この file 自身に docID・claim の id の字を残さないため分けて書く
        self.assertEqual(id_problems(self.doc + u"\n" + fake_doc + u" " + fake_claim), [fake_claim, fake_doc])

    def test_g_6_unmarked_number_or_overclaim_in_prose(self):
        self.assertTrue(prose_problems(self.doc + u"\n帯の中は 999 行であった。"))
        self.assertTrue(prose_problems(self.doc + u"\nこれで出所として正しいと分かった。"))

    def test_g_7_tally_recount_catches_a_moved_row(self):
        rec = copy.deepcopy(self.rec)
        rec[u"集計"][u"全体"]["stages"][u"帯の中"] += 1
        self.assertIn(u"全体/stages", tally_problems(rec))

    def test_g_8_wiring_input_sha_turned(self):
        rec = copy.deepcopy(self.rec)
        rec[u"読んだ入力の sha256"][INPUT_REL] = "0" * 64
        self.assertIn("a", wiring_problems(rec, self.inp))

    def test_g_9_a_copied_value_turned_is_caught_by_d(self):
        rec = copy.deepcopy(self.rec)
        rec[u"行"][5][u"文の値"] = rec[u"行"][5][u"文の値"] + 1
        self.assertIn("d", wiring_problems(rec, self.inp))


if __name__ == "__main__":
    unittest.main()
