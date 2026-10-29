# -*- coding: utf-8 -*-
u"""P27 が「証拠が無く名指さない」で止めた行で、engine が内側に持つ「名指さなかった fact」は原本の fact か ― 診断の門。封 docs/XBRL_UNNAMED_FACT_DIAG_SEAL_2026-10-29.md §5-2 の (a)〜(j)。

記録 ``fixtures/xbrl/unnamed_fact_2026-10-29.json``(``measure/xbrl_unnamed_fact_2026-10-29.py`` の出力)・文書 ``docs/XBRL_UNNAMED_FACT_DIAG_2026-10-29.md``。

  (a) 記録の 741 行の id が ``fresh_2026-10-21.json`` の ``注入の行`` の id と順も集合も同じ(字で留めない)。型別の数も同じ。
  (b) 配線の門 W-1〜W-3 が記録の数で通っている。P27 の注入後の claim を ``stop_reason_2026-10-29.json`` と門が自分で比べ直して 741 / 741、W-2 を ``regress97`` と ``default_p27`` で門が自分で比べ直す、
      W-3 の「鍵が在る行 = reason の行」を門が数え直す。
  (c) 文書の表を記録から作り直して 1 行も違わない(``<!-- 門:start 名前 -->`` の中)。門の外の散文の数には【門なし】の印が要る。
  (d) UF-1〜UF-14 の当否を記録から求め(幅は封の表の字から読む。字で留めない)、封の字(欄・予測・外れ方)と、文書の当否の表の字が一致する。
  (e) 一致の語(6 語)・帯・10 の冪・要素名の切り出しを、記録の欄(named・pointer の字・value・claim の value と unit)から別の書き方で求め直して一致する。
  (f) engine の sha16 を ``ENGINE_AT_MEASURE``(字で留める)と ``ENGINE_DECLARED``(宣言された遷移。今は空)で留める。
  (g) 偽物で赤: 記録の named・value・比・一致の語・配線の旗を 1 か所変えると (b)(c)(e) が赤。文書の表の 1 字で (c) が赤、封の予測の 1 字で (d)(c) が赤、文書に提出者別の接頭辞の字を 1 つ足すと (h) が赤。
  (h) 封と文書に 30 書類の docID・記録の claim の id・提出者別の接頭辞の字が無い。
  (i) 封の commit が script・記録・文書・門の commit より前(git の commit の順)。
  (j) 記録が持つ読んだ入力 5 つの sha256 がいまの file と一致する。

**(i) は、script・記録・文書・門のどれかが commit される前は赤になる**(追跡されていない file には『足した commit』が無い)。skip にしない。前例 ``test_xbrl_stop_reason.py`` と同じ扱い。
**変数名について**: 過去の門が tests/measure の行頭の名前を数えるので、この門はそれらを行頭に置かない。この file は docID の字を持たない(``fetched_2026-10-21.json`` から読む)。
"""
import collections
import copy
import hashlib
import io
import json
import math
import os
import re
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"

SEAL_REL = "docs/XBRL_UNNAMED_FACT_DIAG_SEAL_2026-10-29.md"
DOC_REL = "docs/XBRL_UNNAMED_FACT_DIAG_2026-10-29.md"
REC_REL = "fixtures/xbrl/unnamed_fact_2026-10-29.json"
SCRIPT_REL = "measure/xbrl_unnamed_fact_2026-10-29.py"
GATE_REL = "tests/measure/test_xbrl_unnamed_fact.py"
STOP_REL = "fixtures/xbrl/stop_reason_2026-10-29.json"
FRESH_REL = "fixtures/xbrl/fresh/fresh_2026-10-21.json"
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
REGRESS_REL = "fixtures/xbrl/p27/regress97_2026-10-27.json"
DEFAULT27_REL = "fixtures/xbrl/default_p27_2026-10-28.json"
INPUT_RELS = [STOP_REL, FRESH_REL, FETCHED_REL, REGRESS_REL, DEFAULT27_REL]
SEAL, DOC, REC = [os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL)]
SCRIPT = os.path.join(ROOT, SCRIPT_REL)
SEAL_COMMIT_SHORT = "d31371e"
MAIN_TYPES = ("T1_VALUE", "T2_UNIT", "T5_COINCIDENT")
ALL_TYPES = MAIN_TYPES + ("T3_ABSENT",)
TSHORT = {"T1_VALUE": u"T1", "T2_UNIT": u"T2", "T5_COINCIDENT": u"T5", "T3_ABSENT": u"T3"}
NOT_GATED = u"【門なし】"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
FORBIDDEN = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社", u"貴社の DB の誤り")
STATES4 = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
NSV = "no_same_value"

A_NONAMED, A_NOHEAD, A_SAME = u"(named なし)", u"(照らす先なし)", u"(同じ)"
A_CTX, A_ELEM, A_BOTH = u"(context だけ違う)", u"(要素だけ違う)", u"(両方違う)"
AGREE = (A_SAME, A_CTX, A_ELEM, A_BOTH, A_NONAMED, A_NOHEAD)
B_15, B_2, B_10, B_10K, B_OVER, B_NONE = u"(15% 以内)", u"(2 倍以内)", u"(10 倍以内)", u"(10,000 倍以内)", u"(10,000 倍超)", u"(比なし)"
BANDS = (B_15, B_2, B_10, B_10K, B_OVER, B_NONE)
UNIT_SCALE = {u"百万円": 1e6, u"千円": 1e3, u"億円": 1e8, u"兆円": 1e12, u"円": 1}
SOLE = "NonConsolidatedMember"
FILER = u"(提出者別の要素)"
FILER_PREFIX = u"(提出者別の接頭辞)"

#: engine の sha16(記録を測った時点の値。字で留める ― 測った事実。止めた理由の記録と同じ 6 本)。変えるなら宣言された遷移として下の ENGINE_DECLARED に足す。
ENGINE_AT_MEASURE = {
    "adapters/xbrl/extract.py": "3cf55966f12919f0", "adapters/xbrl/vocabulary.py": "514ebb8104451c07", "adapters/xbrl/recipes.py": "52d645e713c53c1c",
    "adapters/xbrl/resolve.py": "a41043763c1d4073", "adapters/xbrl/comparators.py": "d8706338325e725b", "adapters/xbrl/verify_document.py": "c3791080ab5aef2f",
}
#: 宣言された遷移 {file: (遷移の後の sha16, その遷移を宣言した封)}。今は 0 件。足すときは、封が履歴に在り、値が宣言の値のときだけ受け入れる。測った時点の値は消さない。
ENGINE_DECLARED = {}

#: 記録から求めた当否のうち外れ・判定しないの名前(測った事実。外れは外れのまま残す。封も予測も直さない)。食い違えば d_5 が赤。
#: 今回は 14 本のうち 2 本が外れ(UF-12・UF-14)。判定しないは 0 本。
MISSES = ["UF-12", "UF-14"]
UNDECIDED = []


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    return json.loads(jtext(p))


def rload(rel):
    return jload(os.path.join(ROOT, rel))


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def sha64(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def yesno(b):
    return u"はい" if b else u"いいえ"


def rate(a, b):
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b) if b else u"%d / 0" % a


def n_of(n, d):
    return u"%d / %d" % (n, d)


def table(head, rows):
    lines = [u"| " + u" | ".join(head) + u" |", u"|" + u"|".join(u"---" for _ in head) + u"|"]
    for r in rows:
        lines.append(u"| " + u" | ".join(str(c) for c in r) + u" |")
    return lines


def inputs():
    u"""門が読む入力(記録以外)。"""
    return {"fr": rload(FRESH_REL), "fetched": rload(FETCHED_REL), "stop": rload(STOP_REL), "reg": rload(REGRESS_REL), "d27": rload(DEFAULT27_REL)}


# ----------------------------------------------------------------------------------------------------------------
# 記録の読み出し
def nsv_rows(rec):
    u"""注入後の P27 の reason が no_same_value の行。"""
    return [r for r in rec[u"rows"] if r["reason"] == NSV]


def of_type(rows, t):
    return [r for r in rows if r[u"型"] == t]


def mains_of(rows):
    return [r for r in rows if r[u"型"] in MAIN_TYPES]


def agree_of(r):
    u"""行の一致の語(T1・T2・T5 は 一致(基準)、T3 は 一致(P22))。"""
    return r[u"一致(P22)"] if r[u"型"] == "T3_ABSENT" else r[u"一致(基準)"]


def groups_main(rows):
    return [(TSHORT[t], of_type(rows, t)) for t in MAIN_TYPES] + [(u"計", mains_of(rows))]


def positions(rec):
    u"""{id: (書類の番号, 型, その書類・その型の中の番号)}(記録の出てくる順。1 始まり)。"""
    order = rec[u"書類(出てくる順)"]
    seen, out = collections.Counter(), {}
    for r in rec[u"rows"]:
        d = order.index(r["doc"]) + 1
        seen[(d, r[u"型"])] += 1
        out[r["id"]] = (d, r[u"型"], seen[(d, r[u"型"])])
    return out


def plain_positions(rec):
    order = rec[u"書類(出てくる順)"]
    seen, out = collections.Counter(), {}
    for r in rec[u"plain_rows"]:
        d = order.index(r["doc"]) + 1
        seen[d] += 1
        out[(r["doc"], r["id"])] = (d, seen[d])
    return out


# ----------------------------------------------------------------------------------------------------------------
# (e) 一致の語・帯・10 の冪・要素名の切り出しを、別の書き方で求め直す(script の関数は import しない)
PTR_RE = re.compile(r"^xbrl:(?P<el>(?P<pre>[^:@]*):?(?P<nm>[^@]*))@?(?P<ctx>.*)$")
PERIOD_RE = re.compile(r"^(CurrentYear|Prior1Year|Prior2Year)(Duration|Instant)")


def resplit(p):
    u"""pointer の字から (scheme, 要素名, 接頭辞, context, 期, member の分類, 標準の接頭辞か)。member の分類: なし / 単体 / それ以外。None なら None。"""
    if p is None:
        return None
    if not p.startswith("xbrl:"):
        return (p.split(":", 1)[0], u"(xbrl でない)", None, None, None, None, None)
    m = PTR_RE.match(p)
    ctx = m.group("ctx")
    pm = PERIOD_RE.match(ctx)
    tail = ctx[ctx.index("_") + 1:] if "_" in ctx else ""
    mem = u"なし" if "Member" not in tail else (u"単体" if tail == SOLE else u"それ以外")
    return (u"xbrl", m.group("el"), m.group("pre"), ctx, pm.group(0) if pm else u"その他", mem, re.fullmatch(r"jp[a-z]+_cor", m.group("pre")) is not None)


def reagree(named, h):
    u"""封 §2-3 の表の 1〜6 を、条件の並びとして書く(script は if の連なり)。"""
    a, b = resplit(named), resplit(h)
    rules = [
        (named is None, A_NONAMED),
        (h is None, A_NOHEAD),
        (named == h, A_SAME),
        (a is not None and b is not None and a[0] == b[0] == u"xbrl" and a[1] == b[1] and a[3] != b[3], A_CTX),
        (a is not None and b is not None and a[0] == b[0] == u"xbrl" and a[3] == b[3] and a[1] != b[1], A_ELEM),
        (True, A_BOTH),
    ]
    for cond, w in rules:
        if cond:
            return w
    raise AssertionError("到達しない")


def reband(sent, nv):
    u"""封 §2-4: (帯, 比, 10 の冪に近いか, k)を、帯の端を表にして求める。"""
    if sent is None or nv is None or nv == 0:
        return B_NONE, None, None, None
    r = abs(sent) / abs(nv)
    if r == 0:
        return B_OVER, 0.0, False, None
    edges = [(0.85, 1.15, B_15), (0.5, 2.0, B_2), (0.1, 10.0, B_10), (0.0001, 10000.0, B_10K)]
    band = B_OVER
    for lo, hi, name in edges:
        if lo <= r <= hi:
            band = name
            break
    lg = math.log10(r)
    k = int(math.floor(lg + 0.5))
    return band, r, abs(lg - k) <= 0.01, k


def sent_value(row):
    u"""文の値(円): claim の value × 単位の倍率(単位が表に無ければ None)。"""
    v, u = (row.get(u"claim の value"), row.get(u"unit")) if u"claim の value" in row else ((row[u"claim"] or {}).get("value"), (row[u"claim"] or {}).get("unit"))
    if v is None or u not in UNIT_SCALE:
        return None
    return v * UNIT_SCALE[u]


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def check_e(rec, inp):
    u"""問題の列(空なら通す)。rows と plain_rows の一致の語・帯・10 の冪・文の値・先頭の pointer を、記録の欄と入力の記録から求め直す。"""
    out = []
    stop = dict((r["id"], r) for r in inp["stop"][u"rows"])
    for r in rec[u"rows"]:
        s = stop[r["id"]]
        if r[u"型"] == "T3_ABSENT":
            bh, p22c = None, s[u"profile"]["P22"]["claim"]
        else:
            bc = s[u"profile"]["P27"][u"無改変"]["claim"]
            bh = ((bc or {}).get("pointers") or [None])[0]
            p22c = s[u"profile"]["P22"][u"注入後"]["claim"]
        ph = ((p22c or {}).get("pointers") or [None])[0]
        if r[u"基準の先頭"] != bh:
            out.append(u"%s: 基準の先頭が stop_reason の P27 の無改変の先頭と違う" % r["id"])
        if r[u"P22 の注入後の先頭"] != ph or r[u"P22 の recomputed"] != (p22c or {}).get("recomputed"):
            out.append(u"%s: P22 の先頭か recomputed が stop_reason と違う" % r["id"])
        if r[u"型"] != "T3_ABSENT" and r[u"基準の form"] != (bc or {}).get("form"):
            out.append(u"%s: 基準の form が違う" % r["id"])
        has = r["reason"] == NSV
        if has != (r["named"] is not None) or has != (r[u"named の value"] is not None):
            out.append(u"%s: named・value の有無が reason と合わない" % r["id"])
        if r[u"一致(基準)"] != reagree(r["named"], bh) or r[u"一致(P22)"] != reagree(r["named"], ph):
            out.append(u"%s: 一致の語が求め直しと違う" % r["id"])
        eq = None if (r[u"named の value"] is None or r[u"P22 の recomputed"] is None) else (r[u"named の value"] == r[u"P22 の recomputed"])
        if r[u"value = P22 の recomputed"] != eq:
            out.append(u"%s: value = P22 の recomputed が違う" % r["id"])
        sv = sent_value(r)
        band, ratio, p10, k = reband(sv, r[u"named の value"])
        if (r[u"文の値"], r[u"帯"], r[u"10 の冪に近い"], r[u"k"]) != (sv, band, p10, k) or r[u"比"] != ratio:
            out.append(u"%s: 文の値・比・帯・10 の冪が求め直しと違う" % r["id"])
        if (r[u"claim"] or {}).get("state") != r["state"] or (r[u"claim"] or {}).get("reason") != r["reason"]:
            out.append(u"%s: claim の欄と state・reason が違う" % r["id"])
        if r[u"claim"] is not None and u"span" in r[u"claim"]:
            out.append(u"%s: 記録の claim に span がある(書かない)" % r["id"])
    fr_c = dict(((d, x["id"]), x) for d, xs in inp["fr"][u"claims"].items() for x in xs)
    fr_named = {}
    for x in inp["fr"][u"動いた行"]:
        dp = (x.get("dossier") or {}).get("P26")
        if isinstance(dp, dict):
            fr_named[(x["doc"], x["id"])] = dp.get(u"名指した fact")
    for r in rec[u"plain_rows"]:
        key = (r["doc"], r["id"])
        if r["reason"] != NSV or r["named"] is None or r[u"named の value"] is None:
            out.append(u"%s: 無改変の行の reason か named が違う" % r["id"])
        if r[u"一致(P22)"] != reagree(r["named"], r[u"P22 の先頭"]):
            out.append(u"%s: 無改変の一致(P22)が求め直しと違う" % r["id"])
        p22 = fr_c.get(key)
        if p22 is None or (r[u"P22 の state"], r[u"P22 の reason"]) != (p22["states"][0], p22["reasons"][0]):
            out.append(u"%s: P22 の state・reason が fresh の記録と違う" % r["id"])
        if r[u"fresh P26 の 名指した fact"] != fr_named.get(key):
            out.append(u"%s: fresh の P26 の 名指した fact が fresh の記録と違う" % r["id"])
        if r[u"一致(fresh P26)"] != (None if fr_named.get(key) is None else r["named"] == fr_named.get(key)):
            out.append(u"%s: 一致(fresh P26)が違う" % r["id"])
        if r[u"fresh P26 の no_same_value に在る"] != (p26_reason(fr_c, key) == NSV):
            out.append(u"%s: fresh の P26 の no_same_value の旗が違う" % r["id"])
        sv = sent_value(r)
        band, ratio, p10, k = reband(sv, r[u"named の value"])
        if (r[u"文の値"], r[u"帯"], r[u"10 の冪に近い"], r[u"k"]) != (sv, band, p10, k) or r[u"比"] != ratio:
            out.append(u"%s: 無改変の文の値・比・帯が求め直しと違う" % r["id"])
    return out


def p26_reason(fr_c, key):
    x = fr_c.get(key)
    return None if x is None else x["reasons"][4]


# ----------------------------------------------------------------------------------------------------------------
# (a)(b)(j)
def check_a(rec, fr):
    out = []
    want = fr[u"注入の行"]
    if [r["id"] for r in rec[u"rows"]] != [r["id"] for r in want]:
        out.append(u"記録の rows の id(順も)が fresh の 注入の行 の id と違う")
        return out
    if sorted(r["id"] for r in rec[u"rows"]) != sorted(r["id"] for r in want) or len(rec[u"rows"]) != len(want):
        out.append(u"id の集合が違う")
    by_id = dict((r["id"], r) for r in want)
    for r in rec[u"rows"]:
        if (r["doc"], r[u"型"]) != (by_id[r["id"]]["doc"], by_id[r["id"]][u"型"]):
            out.append(u"%s: doc・型が fresh の行と違う" % r["id"])
    ty = collections.Counter(r[u"型"] for r in rec[u"rows"])
    if dict(ty) != fr[u"D"][u"型別の注入"] or len(rec[u"rows"]) != fr[u"D"][u"注入"]:
        out.append(u"型別の数が fresh の D と違う")
    if rec[u"配線の行ごと"] and [w["id"] for w in rec[u"配線の行ごと"]] != [r["id"] for r in rec[u"rows"]]:
        out.append(u"配線の行ごとの id が rows と違う")
    return out


def _g(c, k):
    return None if c is None else c.get(k)


def dumps(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


CLAIM_FIELDS = ("id", "kind", "form", "value", "unit", "state", "reason", "pointers", "recomputed")


def w1_recount(rec, stop):
    u"""W-1 (ii) を門が自分で数え直す: P27 の注入後の claim(span を除く 9 欄)が stop_reason の同じ id の行と何行一致するか。"""
    rid = dict((r["id"], r) for r in stop[u"rows"])
    f = collections.Counter()
    missing = 0
    for r in rec[u"rows"]:
        o = rid.get(r["id"])
        if o is None:
            missing += 1
            continue
        oc = o[u"profile"]["P27"]["claim"] if r[u"型"] == "T3_ABSENT" else o[u"profile"]["P27"][u"注入後"]["claim"]
        c = r[u"claim"]
        f["state"] += int(_g(c, "state") == _g(oc, "state"))
        f["reason"] += int(_g(c, "reason") == _g(oc, "reason"))
        f["pointers"] += int(_g(c, "pointers") == _g(oc, "pointers"))
        f[u"全欄"] += int(dumps(c) == dumps(None if oc is None else dict((k, oc.get(k)) for k in CLAIM_FIELDS)))
    return {"rows": len(rec[u"rows"]), "missing": missing, "state": f["state"], "reason": f["reason"], "pointers": f["pointers"], "全欄": f[u"全欄"]}


def w2_recount(rec, reg, d27):
    u"""W-2 を門が自分で数え直す: (P27 の一致した書類, P22 の一致した書類, 書類数, P27 の和, default_p27 の和と同じか)。"""
    regd = dict((x["docID"], x) for x in reg[u"書類"])
    ok27 = ok22 = 0
    tot = collections.Counter()
    for d in rec[u"書類(出てくる順)"]:
        st = rec[u"書類ごと"][d][u"無改変の 4 state"]
        ok27 += int(all(st["P27"][k] == regd[d][u"4 state"]["P27"].get(k, 0) for k in STATES4))
        ok22 += int(all(st["P22"][k] == regd[d][u"4 state"]["P22"].get(k, 0) for k in STATES4))
        for k in STATES4:
            tot[k] += st["P27"][k]
    want = d27["S3"][u"既定の 4 state"]
    return ok27, ok22, len(rec[u"書類(出てくる順)"]), dict((k, tot[k]) for k in STATES4), all(tot[k] == want[k] for k in STATES4)


def w3_recount(rec):
    u"""W-3 を門が自分で数え直す。記録の行から: (鍵が在る行, reason が no_same_value の行, 食い違い, claim が None の行, 無改変の鍵 = plain_rows の数, 書類ごとの無改変の行数の和)。"""
    rows = rec[u"rows"]
    keyed = sum(1 for r in rows if r["named"] is not None)
    byreason = sum(1 for r in rows if r["reason"] == NSV)
    mism = sum(1 for r in rows if (r["named"] is not None) != (r["reason"] == NSV))
    none_claim = sum(1 for r in rows if r[u"claim"] is None)
    per_doc = sum(rec[u"書類ごと"][d][u"P27 の no_same_value の行数(無改変)"] for d in rec[u"書類(出てくる順)"])
    return keyed, byreason, mism, none_claim, len(rec[u"plain_rows"]), per_doc


def check_b(rec, fr, fetched, stop, reg, d27):
    out = []
    g = rec[u"配線の門"]
    n = len(fr[u"注入の行"])
    nd = len(fetched[u"使う書類"])
    if not rec[u"全書類"]:
        out.append(u"全書類の記録でない(試走の記録)")
    if not g[u"通った"] or not (g[u"W-1"][u"通った"] and g[u"W-2"][u"通った"] and g[u"W-3"][u"通った"]):
        out.append(u"配線の門の旗が偽")
    w1 = g[u"W-1"]
    if not (w1[u"前の便の門(4 欄とも一致)"] == [n, n] == [len(rec[u"配線の行ごと"])] * 2 and w1[u"id の集合が記録と同じ"] and w1[u"注入の件数の組"] == [4 * nd] * 2):
        out.append(u"W-1 (i) が 741 / 741・120 / 120 でない")
    for w in rec[u"配線の行ごと"]:
        f = w[u"一致"]
        if not all(f[k] for k in (u"記録に同じ id の行が在る", u"元の字", u"後の字", u"基準の claim", u"結果(P22〜P26)", u"4 欄とも一致")):
            out.append(u"%s: 4 欄のどれかが一致していない" % w["id"])
    c = w1_recount(rec, stop)
    if not (c["rows"] == n and c["missing"] == 0 and all(c[k] == n for k in ("state", "reason", "pointers", "全欄"))):
        out.append(u"W-1 (ii) を門が数え直すと 741 / 741 でない: %s" % c)
    for k, key in (("state", u"P27 の state"), ("reason", u"P27 の reason"), ("pointers", u"P27 の pointers")):
        if w1[key] != c[k]:
            out.append(u"W-1 (ii) の記録の数『%s』が門の数え直しと違う" % key)
    if w1[u"P27 の全欄(10 欄 + recomputed)"] != c[u"全欄"]:
        out.append(u"W-1 (ii) の記録の数『全欄』が門の数え直しと違う")
    ok27, ok22, tot, sums, same = w2_recount(rec, reg, d27)
    if not (ok27 == ok22 == tot == nd and same and sums == g[u"W-2"][u"P27 の和"] and g[u"W-2"][u"default_p27 S3 の既定の 4 state"] == d27["S3"][u"既定の 4 state"]):
        out.append(u"W-2 を門が数え直すと 30 / 30・和の一致でない: %s" % ((ok27, ok22, tot, sums, same),))
    if g[u"W-2"][u"P27 の 4 state が regress97 と一致"] != [ok27, nd] or g[u"W-2"][u"P22 の 4 state が regress97 と一致"] != [ok22, nd]:
        out.append(u"W-2 の記録の数が門の数え直しと違う")
    keyed, byreason, mism, nonec, nplain, perdoc = w3_recount(rec)
    w3 = g[u"W-3"]
    if not (keyed == byreason and mism == 0 and nplain == perdoc and byreason > 0):
        out.append(u"W-3 を門が数え直すと『鍵が在る行 = reason の行』『食い違い 0』『無改変の行』が通らない: %s" % ((keyed, byreason, mism, nonec, nplain, perdoc),))
    if not (w3[u"鍵が在る行(注入後)"] == keyed and w3[u"reason が no_same_value の行(注入後)"] == byreason and w3[u"鍵と reason が食い違う行(注入後)"] == mism
            and w3[u"claim が None の行(raw を見ない)"] == nonec and w3[u"id と reason の照合"] == [n - nonec, n - nonec]
            and w3[u"捕捉 注入後 / 行"] == [n, n] and w3[u"捕捉 無改変 / 書類"] == [nd, nd]
            and w3[u"無改変 鍵が在る行"] == w3[u"無改変 reason が no_same_value の行"] == nplain and w3[u"無改変 鍵と reason が食い違う行"] == 0):
        out.append(u"W-3 の記録の数が門の数え直しと違う")
    if w3[u"reason が no_same_value の行の型別"] != dict(collections.Counter(r[u"型"] for r in nsv_rows(rec))):
        out.append(u"W-3 の型別の数が違う")
    docs = rec[u"書類(出てくる順)"]
    if docs != list(fetched[u"使う書類"]):
        out.append(u"書類の順が取得の記録の『使う書類』と違う")
    counts = fr[u"注入の件数(書類別)"]
    used = dict((r["docID"], r) for r in fetched[u"取得した書類"])
    for doc in docs:
        d = rec[u"書類ごと"][doc]
        for t in ALL_TYPES:
            got, want = d[u"注入の件数"][t], counts[doc][t]
            if not all(got[k] == want[k] for k in (u"注入の行になった", u"基準に対応が付かない", u"基準が GROUNDED でない")):
                out.append(u"%s %s: 注入の件数の 3 つの数が記録と違う" % (doc, t))
            if not got[u"3 つの数が記録と一致"]:
                out.append(u"%s %s: 3 つの数の旗が偽" % (doc, t))
        n_rows = sum(1 for r in rec[u"rows"] if r["doc"] == doc)
        if n_rows != sum(d[u"注入の件数"][t][u"注入の行になった"] for t in ALL_TYPES):
            out.append(u"%s: 行の数が 注入の行になった の合計と違う" % doc)
        if d[u"捕捉"] != {u"注入後": n_rows, u"無改変": 1}:
            out.append(u"%s: 捕捉の回数が行数・1 と違う" % doc)
        if d[u"P27 の no_same_value の行数(無改変)"] != sum(1 for r in rec[u"plain_rows"] if r["doc"] == doc):
            out.append(u"%s: 無改変の no_same_value の行数が plain_rows と違う" % doc)
        if not (d[u"材料の sha256 が取得の記録と一致"] and d[u"材料の sha256"] == used[doc]["sha256"]):
            out.append(u"%s: 材料の sha256 が取得の記録と違う" % doc)
    cc = rec[u"cache"]
    if cc[u"開始"] != cc[u"終了"] or cc[u"開始"][u"edinet"] != 281 or cc[u"開始"][u"edinet-fresh-2026-10-21"] != 40:
        out.append(u"cache の件数が 281 / 40 のまま動いていない")
    if rec[u"key_leaks"] != []:
        out.append(u"key_leaks が空でない")
    if rec[u"観測する profile"] != ["P27"]:
        out.append(u"観測する profile が P27 だけでない")
    return out


def check_j(rec):
    out = []
    got = rec[u"読んだ入力の sha256"]
    if sorted(got) != sorted(INPUT_RELS):
        out.append(u"読んだ入力の sha256 の file が 5 つでない")
    for rel in INPUT_RELS:
        if got.get(rel) != sha64(rel):
            out.append(u"%s の sha256 が記録の写しと違う(読み直しの元が動いた)" % rel)
    return out


# ----------------------------------------------------------------------------------------------------------------
# (d) UF-1〜UF-14 の当否を記録から求める(幅は封の表の字から読む)
BOLD = re.compile(r"\*\*(.+?)\*\*")
RANGE_RE = re.compile(r"^(\d+(?:\.\d+)?)%? 以上 (\d+(?:\.\d+)?)%? 以下$")
PCT_RE = re.compile(r"^(\d+(?:\.\d+)?)% 以上$")


def seal_predictions(seal):
    u"""封 §3 の表の行 {名前: (欄, 予測, 外れ方)}(封の字のまま)。"""
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(UF-\d+)\*\* \| (.*) \|$", l)
        if m:
            cells = m.group(2).split(u" | ")
            assert len(cells) == 3, l
            out[m.group(1)] = tuple(c.strip() for c in cells)
    return out


def ranges_of(cell):
    return [(float(m.group(1)), float(m.group(2))) for m in (RANGE_RE.match(b) for b in BOLD.findall(cell)) if m]


def singles_of(cell):
    return [b for b in BOLD.findall(cell) if not RANGE_RE.match(b) and not PCT_RE.match(b)]


def pcts_of(cell):
    return [float(m.group(1)) for m in (PCT_RE.match(b) for b in BOLD.findall(cell)) if m]


def frac_of(s):
    a, b = [int(x) for x in s.split(u" / ")]
    return a, b


def within(n, rg):
    return rg[0] <= n <= rg[1]


def hit_word(b):
    return u"**判定しない**" if b is None else (u"**当たり**" if b else u"**外れ**")


def std_pre(r):
    c = resplit(r["named"])
    return c is not None and c[6] is True


def judge(rec, inp, seal):
    u"""{名前: (実測の字, 当たりか(True / False / None=判定しない))}。封 §3 の予測を記録から。幅は封の字から読む。"""
    SP = seal_predictions(seal)
    out = collections.OrderedDict()
    ALL = rec[u"rows"]
    n = len(ALL)
    NS = nsv_rows(rec)
    NM = mains_of(NS)
    T3 = of_type(NS, "T3_ABSENT")
    PL = rec[u"plain_rows"]
    nd = len(rec[u"書類(出てくる順)"])
    g = rec[u"配線の門"]

    # UF-1
    sg = singles_of(SP["UF-1"][1])
    a, b = frac_of(sg[0])
    pairs = frac_of(sg[1])
    w1 = w1_recount(rec, inp["stop"])
    g1 = g[u"W-1"]
    hit = (g1[u"前の便の門(4 欄とも一致)"] == [a, b] and a == b == n and list(pairs) == g1[u"注入の件数の組"] and g1[u"id の集合が記録と同じ"]
           and frac_of(sg[2]) == (n, n) and all(w1[k] == frac_of(sg[2])[0] for k in ("state", "reason", "pointers", u"全欄")))
    out["UF-1"] = (u"W-1 (i) %s・注入の件数の組 %s、(ii) 欄ごと state %s・reason %s・pointers %s、全欄 %s" % (
        n_of(*g1[u"前の便の門(4 欄とも一致)"]), n_of(*g1[u"注入の件数の組"]), n_of(w1["state"], n), n_of(w1["reason"], n), n_of(w1["pointers"], n), n_of(w1[u"全欄"], n)), hit)
    # UF-2
    sg = singles_of(SP["UF-2"][1])
    ok27, ok22, tot, sums, same = w2_recount(rec, inp["reg"], inp["d27"])
    want = [int(x.replace(u",", u"")) for x in re.search(r"\(([\d,]+(?:・[\d,]+){3})\)", SP["UF-2"][1]).group(1).split(u"・")]
    out["UF-2"] = (u"無改変の P27 の 4 state: %s 書類、和 %s(default_p27 S3 と同じ: %s)、P22 の 4 state: %s 書類" % (
        n_of(ok27, tot), u"・".join(str(sums[k]) for k in STATES4), yesno(same), n_of(ok22, tot)),
        frac_of(sg[0]) == (ok27, tot) == frac_of(sg[1]) == (ok22, tot) and [sums[k] for k in STATES4] == want and same)
    # UF-3
    sg = singles_of(SP["UF-3"][1])
    keyed, byreason, mism, nonec, nplain, perdoc = w3_recount(rec)
    wt = [int(x) for x in re.search(r"T1 (\d+)・T2 (\d+)・T5 (\d+)・T3 (\d+)", SP["UF-3"][1]).groups()]
    bt = [sum(1 for r in NS if r[u"型"] == t) for t in ALL_TYPES]
    g3 = g[u"W-3"]
    chk = frac_of(sg[2])
    out["UF-3"] = (u"捕捉 注入後 %d・無改変 %d、id と reason の照合 %s、鍵が在る行 %d = reason が no_same_value の行 %d(T1 %d・T2 %d・T5 %d・T3 %d)、食い違う行 %d" % (
        g3[u"捕捉 注入後 / 行"][0], g3[u"捕捉 無改変 / 書類"][0], n_of(*g3[u"id と reason の照合"]), keyed, byreason, bt[0], bt[1], bt[2], bt[3], mism),
        g3[u"捕捉 注入後 / 行"][0] == int(sg[0]) == n and g3[u"捕捉 無改変 / 書類"][0] == int(sg[1]) == nd and tuple(g3[u"id と reason の照合"]) == chk == (n - nonec, n - nonec)
        and keyed == byreason == int(sg[3]) and bt == wt and mism == int(sg[4]) == 0)
    # UF-4
    sg = singles_of(SP["UF-4"][1])
    c_x = sum(1 for r in NS if isinstance(r["named"], str) and r["named"].startswith(u"xbrl:"))
    c_v = sum(1 for r in NS if is_num(r[u"named の value"]))
    c_0 = sum(1 for r in NS if r[u"named の value"] == 0)
    out["UF-4"] = (u"named が xbrl: で始まる字 %s、value が数 %s、value が 0 の行 %d" % (n_of(c_x, len(NS)), n_of(c_v, len(NS)), c_0),
                   (c_x, len(NS)) == frac_of(sg[0]) and (c_v, len(NS)) == frac_of(sg[1]) and c_0 == int(sg[2]))
    # UF-5
    sg = singles_of(SP["UF-5"][1])
    rgs = ranges_of(SP["UF-5"][1])
    same_by = [sum(1 for r in of_type(NS, t) if r[u"一致(基準)"] == A_SAME) for t in MAIN_TYPES]
    t1n = len(of_type(NS, "T1_VALUE"))
    out["UF-5"] = (u"一致(基準)が(同じ): T1 %s・T2 %d・T5 %d" % (n_of(same_by[0], t1n), same_by[1], same_by[2]),
                   (same_by[0], t1n) == frac_of(sg[0]) and within(same_by[1], rgs[0]) and within(same_by[2], rgs[1]))
    # UF-6
    rg = ranges_of(SP["UF-6"][1])[0]
    zero = int(singles_of(SP["UF-6"][1])[0])
    diff = [r for r in NM if r[u"一致(基準)"] != A_SAME]
    cw = collections.Counter(r[u"一致(基準)"] for r in diff)
    ok6 = within(len(diff), rg) and (len(diff) == 0 or (cw[A_CTX] >= cw[A_ELEM] + cw[A_BOTH] and cw[A_NONAMED] == zero and cw[A_NOHEAD] == zero))
    out["UF-6"] = (u"(同じ)でない行(T1・T2・T5 の計)%d。中身: (context だけ違う)%d・(要素だけ違う)%d・(両方違う)%d・(named なし)%d・(照らす先なし)%d" % (
        len(diff), cw[A_CTX], cw[A_ELEM], cw[A_BOTH], cw[A_NONAMED], cw[A_NOHEAD]), ok6)
    # UF-7
    sg = singles_of(SP["UF-7"][1])
    rg = ranges_of(SP["UF-7"][1])[0]
    c_n = sum(1 for r in T3 if r["named"] is not None)
    c_s = sum(1 for r in T3 if r[u"一致(P22)"] == A_SAME)
    out["UF-7"] = (u"T3 の named 在り %s、一致(P22 の注入後の先頭)が(同じ)%d" % (n_of(c_n, len(T3)), c_s), (c_n, len(T3)) == frac_of(sg[0]) and within(c_s, rg))
    # UF-8
    same_rows = [r for r in NS if agree_of(r) == A_SAME]
    vt = sum(1 for r in same_rows if r[u"value = P22 の recomputed"] is True)
    vf = sum(1 for r in same_rows if r[u"value = P22 の recomputed"] is False)
    vn = sum(1 for r in same_rows if r[u"value = P22 の recomputed"] is None)
    out["UF-8"] = (u"一致が(同じ)の行 %d のうち value = P22 の recomputed: 真 %d・偽 %d・数えない %d" % (len(same_rows), vt, vf, vn), len(same_rows) > 0 and vt == len(same_rows) and vf == 0 and vn == 0)
    # UF-9
    rg = ranges_of(SP["UF-9"][1])[0]
    sp = singles_of(SP["UF-9"][1])
    c_n = sum(1 for r in PL if isinstance(r["named"], str) and r["named"].startswith(u"xbrl:"))
    c_p = sum(1 for r in PL if r[u"P22 の state"] == "VALUE_MISMATCH" and r[u"P22 の先頭"] is not None)
    want9 = [float(s.rstrip(u"%")) for s in sp]
    out["UF-9"] = (u"無改変の P27 の no_same_value %d 行、named 在り %s、P22 は VALUE_MISMATCH・pointers 空でない %s" % (len(PL), rate(c_n, len(PL)), rate(c_p, len(PL))),
                   within(len(PL), rg) and len(PL) > 0 and c_n * 100 >= want9[0] * len(PL) and c_p * 100 >= want9[1] * len(PL) and want9 == [100.0, 100.0])
    # UF-10
    sg = singles_of(SP["UF-10"][1])
    fresh_nsv = set((d, x["id"]) for d in rec[u"書類(出てくる順)"] for x in inp["fr"][u"claims"][d] if x["reasons"][4] == NSV)
    mine = set((r["doc"], r["id"]) for r in PL)
    a10, b10 = len(fresh_nsv - mine), len(mine - fresh_nsv)
    out["UF-10"] = (u"fresh の P26 に在って P27 に無い %d・P27 に在って fresh に無い %d" % (a10, b10), a10 == int(sg[0]) and b10 == int(sg[1]))
    # UF-11
    lo = pcts_of(SP["UF-11"][1])
    hasf = [r for r in PL if r[u"fresh P26 の 名指した fact"] is not None]
    s_f = sum(1 for r in hasf if r[u"一致(fresh P26)"] is True)
    s_p = sum(1 for r in PL if r[u"一致(P22)"] == A_SAME)
    out["UF-11"] = (u"fresh の P26 の 名指した fact と(同じ): %s(fresh に無い行 %d は分母から除く)、P22 の先頭と(同じ): %s" % (rate(s_f, len(hasf)), len(PL) - len(hasf), rate(s_p, len(PL))),
                    len(hasf) > 0 and s_f * 100 >= lo[0] * len(hasf) and len(PL) > 0 and s_p * 100 >= lo[1] * len(PL))
    # UF-12
    cell = SP["UF-12"][1]
    rgs = ranges_of(cell)
    sg = singles_of(cell)
    cnt = lambda rows, *bs: sum(1 for r in rows if r[u"帯"] in bs)
    t1, t2, t5, t3 = [of_type(NS, t) for t in ALL_TYPES]
    p10 = sum(1 for r in t2 if r[u"10 の冪に近い"] is True)
    ok12 = (cnt(t1, B_15, B_2) == frac_of(sg[0])[0] and len(t1) == frac_of(sg[0])[1]
            and p10 == frac_of(sg[1])[0] and len(t2) == frac_of(sg[1])[1]
            and within(cnt(t2, B_OVER), rgs[0]) and within(cnt(t2, B_10K), rgs[1]) and cnt(t2, B_15, B_2, B_10) == int(sg[2])
            and within(cnt(t5, B_15), rgs[2]) and within(cnt(t5, B_2, B_10), rgs[3]) and within(cnt(t5, B_10K, B_OVER), rgs[4])
            and within(cnt(t3, B_OVER), rgs[5]) and cnt(NS, B_NONE) == int(sg[3]))
    out["UF-12"] = (u"T1 の(15%% 以内)+(2 倍以内)%s。T2: 10 の冪に近い %s・(10,000 倍超)%d・(10,000 倍以内)%d・(15%% 以内)+(2 倍以内)+(10 倍以内)%d。T5: (15%% 以内)%d・(2 倍以内)+(10 倍以内)%d・(10,000 倍以内)+(10,000 倍超)%d。T3: (10,000 倍超)%d。比なし %d" % (
        n_of(cnt(t1, B_15, B_2), len(t1)), n_of(p10, len(t2)), cnt(t2, B_OVER), cnt(t2, B_10K), cnt(t2, B_15, B_2, B_10),
        cnt(t5, B_15), cnt(t5, B_2, B_10), cnt(t5, B_10K, B_OVER), cnt(t3, B_OVER), cnt(NS, B_NONE)), ok12)
    # UF-13
    rgs = ranges_of(SP["UF-13"][1])
    b15 = sum(1 for r in PL if r[u"帯"] == B_15)
    bnone = sum(1 for r in PL if r[u"帯"] == B_NONE)
    out["UF-13"] = (u"無改変の P27 の no_same_value %d 行のうち(15%% 以内)%d・比なし %d" % (len(PL), b15, bnone), within(b15, rgs[0]) and within(bnone, rgs[1]))
    # UF-14
    lo = pcts_of(SP["UF-14"][1])
    sm = [r for r in NM if r[u"一致(基準)"] == A_SAME]
    std = sum(1 for r in sm if std_pre(r))
    cur = sum(1 for r in sm if resplit(r["named"])[4] in ("CurrentYearDuration", "CurrentYearInstant"))
    mem = [r for r in sm if resplit(r["named"])[5] != u"なし"]
    sole = sum(1 for r in mem if resplit(r["named"])[5] == u"単体")
    out["UF-14"] = (u"(同じ)の行(T1・T2・T5)%d: 標準の接頭辞 %s・CurrentYear %s・member あり %d のうち単体 %d" % (len(sm), rate(std, len(sm)), rate(cur, len(sm)), len(mem), sole),
                    len(sm) > 0 and std * 100 >= lo[0] * len(sm) and cur * 100 >= lo[1] * len(sm) and sole == len(mem))
    return out


# ----------------------------------------------------------------------------------------------------------------
# (c) 文書の表
def mem_cat(c):
    return c[5]


def pair_of(ptr):
    u"""pointer の字から (期, member の分類)。xbrl でなければ None。"""
    c = resplit(ptr)
    if c is None or c[0] != u"xbrl":
        return None
    return (c[4], c[5])


def edit_label(r):
    return u"%s・%s・%s" % (TSHORT[r[u"型"]], agree_of(r), r[u"帯"])


def render_blocks(rec, inp, seal):
    B = collections.OrderedDict()
    J = judge(rec, inp, seal)
    SP = seal_predictions(seal)
    assert list(SP) == list(J), list(SP)
    rows = rec[u"rows"]
    n = len(rows)
    NS = nsv_rows(rec)
    NM = mains_of(NS)
    PL = rec[u"plain_rows"]
    order = rec[u"書類(出てくる順)"]
    B["pred"] = table([u"#", u"欄", u"予測(封の字)", u"外れ方(封の字)", u"実測(記録から)", u"当たり外れ"],
                      [[u"**%s**" % k, SP[k][0], SP[k][1], SP[k][2], J[k][0], hit_word(J[k][1])] for k in J])
    # 配線
    g = rec[u"配線の門"]
    w1, w2, w3 = g[u"W-1"], g[u"W-2"], g[u"W-3"]
    c1 = w1_recount(rec, inp["stop"])
    ok27, ok22, tot, sums, same = w2_recount(rec, inp["reg"], inp["d27"])
    keyed, byreason, mism, nonec, nplain, perdoc = w3_recount(rec)
    B["wiring"] = table([u"配線の門", u"値"], [
        [u"W-1 (i) 前の便の門(4 欄とも一致した行 / 作り直した行)", n_of(*w1[u"前の便の門(4 欄とも一致)"])],
        [u"W-1 (i) id の集合が記録と同じ", yesno(w1[u"id の集合が記録と同じ"])],
        [u"W-1 (i) 注入の件数の組(書類 × 型 / 3 つの数が一致)", n_of(*w1[u"注入の件数の組"])],
        [u"W-1 (ii) P27 の注入後の claim の state が stop_reason と同じ行(門の数え直し)", n_of(c1["state"], n)],
        [u"W-1 (ii) 同 reason", n_of(c1["reason"], n)],
        [u"W-1 (ii) 同 pointers", n_of(c1["pointers"], n)],
        [u"W-1 (ii) 同 全欄(span を除く 9 欄。門の数え直し)", n_of(c1[u"全欄"], n)],
        [u"W-1 (ii) 同 全欄(10 欄 + recomputed。script の数)", n_of(w1[u"P27 の全欄(10 欄 + recomputed)"], w1[u"行"])],
        [u"W-2 無改変の P27 の 4 state が regress97 と同じ書類", n_of(ok27, tot)],
        [u"W-2 無改変の P22 の 4 state が regress97 と同じ書類", n_of(ok22, tot)],
        [u"W-2 P27 の和(GROUNDED・VALUE_MISMATCH・UNVERIFIABLE・POINTER_NOT_FOUND)", u"・".join(str(sums[k]) for k in STATES4)],
        [u"W-2 和が default_p27 S3 の既定の 4 state と同じ", yesno(same)],
        [u"W-3 (i) 捕捉 注入後(回数 / 行)", n_of(*w3[u"捕捉 注入後 / 行"])],
        [u"W-3 (i) 捕捉 無改変(回数 / 書類)", n_of(*w3[u"捕捉 無改変 / 書類"])],
        [u"W-3 (ii) 行の claim の id が raw に在り reason の真偽が同じ(claim が None の %d 行を除く)" % nonec, n_of(*w3[u"id と reason の照合"])],
        [u"W-3 (iii) raw に no_same_value の鍵が在る行(注入後。門の数え直し)", str(keyed)],
        [u"W-3 (iii) reason が no_same_value の行(注入後。門の数え直し)", str(byreason)],
        [u"W-3 (iii) 鍵と reason が食い違う行(注入後)", str(mism)],
        [u"W-3 (iii) 無改変: 鍵が在る行 / reason が no_same_value の行 / 食い違う行", u"%d / %d / %d" % (w3[u"無改変 鍵が在る行"], w3[u"無改変 reason が no_same_value の行"], w3[u"無改変 鍵と reason が食い違う行"])],
        [u"全書類の記録", yesno(rec[u"全書類"])]])
    eng = rec[u"engine sha16"]
    B["engine"] = table([u"項目", u"値"], [[u"`%s` の sha16" % k, u"`%s`" % v] for k, v in eng.items()] + [
        [u"DEFAULT_PROFILE", rec[u"DEFAULT_PROFILE"]], [u"測った木の HEAD", u"`%s`" % rec[u"HEAD"]], [u"封の commit", u"`%s`" % rec[u"封"][u"commit"]],
        [u"cache `edinet/`(開始 → 終了)", u"%d → %d" % (rec[u"cache"][u"開始"][u"edinet"], rec[u"cache"][u"終了"][u"edinet"])],
        [u"cache `edinet-fresh-2026-10-21/`(開始 → 終了)", u"%d → %d" % (rec[u"cache"][u"開始"][u"edinet-fresh-2026-10-21"], rec[u"cache"][u"終了"][u"edinet-fresh-2026-10-21"])],
        [u"key_leaks", str(len(rec[u"key_leaks"]))]])
    # nsv: 型別の行
    nrow = []
    for t in ALL_TYPES:
        rs = of_type(rows, t)
        ns = of_type(NS, t)
        nrow.append([TSHORT[t], str(len(rs)), str(len(ns)), str(sum(1 for r in ns if r["named"] is not None)),
                     str(sum(1 for r in ns if isinstance(r["named"], str) and r["named"].startswith(u"xbrl:"))),
                     str(sum(1 for r in ns if is_num(r[u"named の value"]))), str(sum(1 for r in ns if r[u"named の value"] == 0))])
    nrow.append([u"計", str(n), str(len(NS)), str(sum(1 for r in NS if r["named"] is not None)),
                 str(sum(1 for r in NS if isinstance(r["named"], str) and r["named"].startswith(u"xbrl:"))),
                 str(sum(1 for r in NS if is_num(r[u"named の value"]))), str(sum(1 for r in NS if r[u"named の value"] == 0))])
    B["nsv"] = table([u"型", u"行(P27 の注入後)", u"reason が no_same_value", u"named 在り", u"named が xbrl: で始まる", u"value が数", u"value が 0"], nrow)
    # agree
    arow = []
    for name, rs in groups_main(NS):
        c = collections.Counter(r[u"一致(基準)"] for r in rs)
        arow.append([name, str(len(rs))] + [str(c[w]) for w in AGREE])
    B["agree"] = table([u"型(一致(基準): named と無改変の基準の先頭)", u"行"] + list(AGREE), arow)
    prow = []
    for name, rs in groups_main(NS) + [(u"T3", of_type(NS, "T3_ABSENT"))]:
        c = collections.Counter(r[u"一致(P22)"] for r in rs)
        prow.append([name, str(len(rs))] + [str(c[w]) for w in AGREE])
    B["agree_p22"] = table([u"型(一致(P22): named と P22 の注入後の先頭)", u"行"] + list(AGREE), prow)
    # value
    vrow = []
    for name, rs in groups_main(NS) + [(u"T3", of_type(NS, "T3_ABSENT"))]:
        sm = [r for r in rs if agree_of(r) == A_SAME]
        vc = lambda xs: [str(sum(1 for r in xs if r[u"value = P22 の recomputed"] is v)) for v in (True, False, None)]
        vrow.append([name, str(len(rs))] + vc(rs) + [str(len(sm))] + vc(sm))
    B["value"] = table([u"型", u"行", u"全行: 真", u"全行: 偽", u"全行: 数えない", u"一致が(同じ)の行", u"(同じ)の行: 真", u"(同じ)の行: 偽", u"(同じ)の行: 数えない"], vrow)
    # plain
    per = [rec[u"書類ごと"][d][u"P27 の no_same_value の行数(無改変)"] for d in order]
    p22c = collections.Counter((r[u"P22 の state"], r[u"P22 の reason"]) for r in PL)
    aw = collections.Counter(r[u"一致(P22)"] for r in PL)
    hasf = [r for r in PL if r[u"fresh P26 の 名指した fact"] is not None]
    fresh_nsv = set((d, x["id"]) for d in order for x in inp["fr"][u"claims"][d] if x["reasons"][4] == NSV)
    mine = set((r["doc"], r["id"]) for r in PL)
    vv = collections.Counter(None if (r[u"named の value"] is None or r[u"P22 の recomputed"] is None) else (r[u"named の value"] == r[u"P22 の recomputed"]) for r in PL)
    plain = [[u"無改変の 30 書類の P27 の no_same_value の行数(書類ごとの最小 / 最大 / 計)", u"%d / %d / %d" % (min(per), max(per), sum(per))],
             [u"named 在り(xbrl: で始まる字)", n_of(sum(1 for r in PL if isinstance(r["named"], str) and r["named"].startswith(u"xbrl:")), len(PL))],
             [u"P22 の pointers が空でない行", n_of(sum(1 for r in PL if r[u"P22 の先頭"] is not None), len(PL))]]
    for (s_, rs_), k in sorted(p22c.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        plain.append([u"P22 の state・reason: %s・%s" % (s_, u"(なし)" if rs_ is None else rs_), str(k)])
    for w in AGREE:
        plain.append([u"一致(P22 の無改変の先頭): %s" % w, str(aw[w])])
    plain += [[u"fresh の P26 の 名指した fact と同じ字", str(sum(1 for r in hasf if r[u"一致(fresh P26)"] is True))],
              [u"fresh の P26 の 名指した fact と違う字", str(sum(1 for r in hasf if r[u"一致(fresh P26)"] is False))],
              [u"fresh に 名指した fact が無い行(分母から除く)", str(len(PL) - len(hasf))],
              [u"fresh の P26 の no_same_value に在って P27 に無い行(足りない)", str(len(fresh_nsv - mine))],
              [u"P27 に在って fresh の P26 の no_same_value に無い行(余り)", str(len(mine - fresh_nsv))],
              [u"足りない行が regress97 の『P26 → P27』で no_same_value から動いた行の集合と同じ", yesno(fresh_nsv - mine == set((x["docID"], x["id"]) for x in inp["reg"][u"動いた行"][u"新しい標本 30"][u"P26 → P27"] if x[u"前"]["reason"] == NSV))],
              [u"named の value = P22 の recomputed: 真 / 偽 / 数えない", u"%d / %d / %d" % (vv[True], vv[False], vv[None])]]
    B["plain"] = table([u"無改変の 30 書類(P27 の no_same_value の行)", u"値"], plain)
    # ratio
    def band_row(label, rs):
        c = collections.Counter(r[u"帯"] for r in rs)
        return [label, str(len(rs))] + [str(c[b]) for b in BANDS[:5]] + [str(c[B_NONE]), str(sum(1 for r in rs if r[u"10 の冪に近い"] is True))]
    t2 = of_type(NS, "T2_UNIT")
    rrow = [band_row(u"T1", of_type(NS, "T1_VALUE")),
            band_row(u"T2(基準が direct_value)", [r for r in t2 if r[u"基準の form"] == "direct_value"]),
            band_row(u"T2(基準が derived_value)", [r for r in t2 if r[u"基準の form"] == "derived_value"]),
            band_row(u"T2 計", t2), band_row(u"T5", of_type(NS, "T5_COINCIDENT")), band_row(u"T3", of_type(NS, "T3_ABSENT")),
            band_row(u"無改変の P27 の no_same_value", PL)]
    B["ratio"] = table([u"型・区分", u"行"] + list(BANDS[:5]) + [u"比なし", u"10 の冪に近い"], rrow)
    krow = []
    for label, rs in ((u"T2 注入後", t2), (u"無改変", PL)):
        kc = collections.Counter((r[u"基準の form"] if label == u"T2 注入後" else u"―", r["k"]) for r in rs if r[u"10 の冪に近い"] is True)
        for (f_, k), v in sorted(kc.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
            krow.append([label, f_, str(k), str(v)])
    B["pow10"] = table([u"区分(10 の冪に近い行)", u"基準の form", u"k(round(log10 比))", u"行"], krow)
    # P27E の B が名指しに移した行との突き合わせ(比の(15% 以内)の行の集合)
    chg = set(r["id"] for r in inp["stop"][u"rows"] if r[u"profile"]["P27"][u"名指し"][u"語"] != r[u"profile"]["P27E"][u"名指し"][u"語"])
    b15 = set(r["id"] for r in NS if r[u"帯"] == B_15 and r[u"型"] in MAIN_TYPES)
    mv = set((x["docID"], x["id"]) for x in inp["reg"][u"動いた行"][u"新しい標本 30"][u"P27 → P27E"])
    pb15 = set((r["doc"], r["id"]) for r in PL if r[u"帯"] == B_15)
    B["p27e"] = table([u"区分", u"比が(15% 以内)の行", u"P27 → P27E で動いた行(出どころ)", u"集合が同じ"], [
        [u"注入後 T1・T2・T5(stop_reason の記録の語が変わった行)", str(len(b15)), str(len(chg)), yesno(b15 == chg)],
        [u"無改変(regress97 の P27 → P27E)", str(len(pb15)), str(len(mv)), yesno(pb15 == mv)]])
    # elements / prefix / context
    def same_set(label):
        if label == u"注入後(T1・T2・T5)":
            return [r for r in NM if r[u"一致(基準)"] == A_SAME]
        return [r for r in PL if r[u"一致(P22)"] == A_SAME]
    erow = []
    labels = (u"注入後(T1・T2・T5)", u"無改変")
    for lab in labels:
        rs = same_set(lab)
        cnt, filer = collections.Counter(), 0
        for r in rs:
            c = resplit(r["named"])
            if c[6]:
                cnt[c[1]] += 1
            else:
                filer += 1
        for i, (k, v) in enumerate(sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[:10]):
            erow.append([lab, str(i + 1), k, str(v)])
        erow.append([lab, u"―", FILER, str(filer)])
        erow.append([lab, u"―", u"((同じ)の行の計)", str(len(rs))])
    B["elements"] = table([u"区分", u"順位(標準の接頭辞の要素)", u"要素名", u"行"], erow)
    cols = [(lab, lab) for lab in labels]
    pre_names = sorted(set(resplit(r["named"])[2] for lab in labels for r in same_set(lab) if resplit(r["named"])[6]))
    xrow = [[p_] + [str(sum(1 for r in same_set(lab) if resplit(r["named"])[6] and resplit(r["named"])[2] == p_)) for lab in labels] for p_ in pre_names]
    xrow.append([FILER_PREFIX] + [str(sum(1 for r in same_set(lab) if not resplit(r["named"])[6])) for lab in labels])
    B["prefix"] = table([u"接頭辞((同じ)の行)"] + list(labels), xrow)
    mcats = [u"なし", u"単体", u"それ以外"]
    crow = []
    for per_ in [a + b for a in ("CurrentYear", "Prior1Year", "Prior2Year") for b in ("Duration", "Instant")] + [u"その他"]:
        for mc in mcats:
            crow.append([per_, mc] + [str(sum(1 for r in same_set(lab) if (resplit(r["named"])[4], resplit(r["named"])[5]) == (per_, mc))) for lab in labels])
    B["context"] = table([u"期", u"member(単体 = NonConsolidatedMember のみ)"] + list(labels), crow)
    # 同じでない行の期・member の対
    drow = []
    for lab, rs, hk, acc in ((u"注入後(T1・T2・T5。基準の先頭と)", [r for r in NM if r[u"一致(基準)"] != A_SAME], u"基準の先頭", u"一致(基準)"),
                             (u"注入後(T3。P22 の先頭と)", [r for r in of_type(NS, "T3_ABSENT") if r[u"一致(P22)"] != A_SAME], u"P22 の注入後の先頭", u"一致(P22)"),
                             (u"無改変(P22 の先頭と)", [r for r in PL if r[u"一致(P22)"] != A_SAME], u"P22 の先頭", u"一致(P22)")):
        pc = collections.Counter()
        for r in rs:
            pc[(r[acc], pair_of(r["named"]), pair_of(r[hk]))] += 1
        if not pc:
            drow.append([lab, u"―", u"(該当する行は無い)", u"―", u"0"])
        for (wd, a_, b_), v in sorted(pc.items(), key=lambda kv: str(kv[0])):
            drow.append([lab, wd, (u"%s・%s" % a_) if a_ else u"―", (u"%s・%s" % b_) if b_ else u"―", str(v)])
    B["diffpairs"] = table([u"区分((同じ)でない行)", u"一致の語", u"named の期・member", u"照らす先の期・member", u"行"], drow)
    # examples
    pos, ppos = positions(rec), plain_positions(rec)
    ex = []
    for w in AGREE:
        k = 0
        for r in NS:
            if agree_of(r) == w and k < 3:
                k += 1
                p_ = pos[r["id"]]
                ex.append([u"注入後", w, u"書類 %d・%s の %d 番目" % (p_[0], TSHORT[p_[1]], p_[2]), TSHORT[r[u"型"]], r[u"帯"]])
        if k == 0:
            ex.append([u"注入後", w, u"(この語の行は無い)", u"―", u"―"])
    for w in AGREE:
        k = 0
        for r in PL:
            if r[u"一致(P22)"] == w and k < 3:
                k += 1
                p_ = ppos[(r["doc"], r["id"])]
                ex.append([u"無改変", w, u"書類 %d・無改変の %d 番目" % p_, u"―", r[u"帯"]])
        if k == 0:
            ex.append([u"無改変", w, u"(この語の行は無い)", u"―", u"―"])
    B["examples"] = table([u"区分", u"語(型 T1・T2・T5 は一致(基準)、T3 と無改変は一致(P22))", u"位置", u"型", u"帯"], ex)
    order_of_doc = ("pred", "wiring", "engine", "nsv", "agree", "agree_p22", "value", "plain", "ratio", "pow10", "p27e", "elements", "prefix", "context", "diffpairs", "examples")
    assert sorted(order_of_doc) == sorted(B), sorted(set(order_of_doc) ^ set(B))
    return collections.OrderedDict((k, B[k]) for k in order_of_doc)


BLOCK_RE = re.compile(r"<!-- 門:start (\S+) -->\n(.*?)\n<!-- 門:end -->", re.S)


def doc_blocks(doc):
    out = collections.OrderedDict()
    for m in BLOCK_RE.finditer(doc):
        if m.group(1) in out:
            raise AssertionError(u"同じ名前の門の表が 2 つ: " + m.group(1))
        out[m.group(1)] = m.group(2).split(u"\n")
    return out


def check_c(rec, inp, seal, doc):
    u"""文書の表を記録から作り直して比べる。問題の列。"""
    out = []
    try:
        B = render_blocks(rec, inp, seal)
    except Exception as e:      # 記録が壊れていれば作り直せない(それも赤)
        return [u"記録から表を作れない: %r" % (e,)]
    got = doc_blocks(doc)
    if list(got) != list(B):
        out.append(u"文書の門の表の名前と順が違う: %s" % list(got))
        return out
    for k, lines in B.items():
        if got[k] != lines:
            out.append(u"文書の表『%s』が記録から作った表と違う" % k)
    return out


DOC_LITERALS = (u"記録は不変", u"配線の数", u"仮説。測るまで断定しない", u"測っていない", u"診断だけ", NOT_GATED, u"edinetdb-p27", u"良し悪し", u"この便で決めない")


def check_doc_prose(rec, inp, seal, doc):
    out = []
    stripped = BLOCK_RE.sub(u"", doc)
    if [l for l in stripped.split(u"\n") if l.lstrip().startswith(u"|")]:
        out.append(u"門の外に表の行がある")
    bad = [l[:40] for l in stripped.split(u"\n") if re.search(r"\d+(?:\.\d+)?\s*(?:%|行|件|社|席|書類|試行|回|本|ポイント|USD|file|倍|桁|字|組|つ)", l) and NOT_GATED not in l]
    if bad:
        out.append(u"散文の数に【門なし】の印が無い: %s" % bad)
    heads = re.findall(r"^## (\d+)\.", doc, re.M)
    if heads != [str(i) for i in range(1, len(heads) + 1)] or len(heads) < 8:
        out.append(u"節の番号が 1 から続いていない・8 節に足りない: %s" % heads)
    if not (doc.index(u"<!-- 門:start pred -->") < doc.index(u"## 2.")):
        out.append(u"予測の当否が先頭(第 2 節より前)にない")
    J = judge(rec, inp, seal)
    missed = [k for k, v in J.items() if v[1] is False]
    want = u"外れた予測: " + (u"・".join(missed) if missed else u"なし") + u"。外れは外れのまま残す(封も予測も直さない)。" + NOT_GATED
    if sum(1 for l in doc.split(u"\n") if l.strip() == want) != 1:
        out.append(u"『外れた予測』の行が記録から求めた当否と違う(期待: %s)" % want)
    undecided = [k for k, v in J.items() if v[1] is None]
    want2 = u"判定しない予測: " + u"・".join(undecided) + u"(当たりにも外れにも数えない)。" + NOT_GATED
    n2 = sum(1 for l in doc.split(u"\n") if l.strip() == want2)
    if undecided and n2 != 1:
        out.append(u"『判定しない予測』の行が記録から求めた当否と違う(期待: %s)" % want2)
    if not undecided and u"判定しない予測:" in doc:
        out.append(u"判定しない予測が無いのに、その行がある")
    for lit in DOC_LITERALS:
        if lit not in doc:
            out.append(u"必要な字が無い: %s" % lit)
    for w in FORBIDDEN:
        if w in doc:
            out.append(u"禁止語: %s" % w)
    if u"```" in doc:
        out.append(u"code fence がある")
    return out


# ----------------------------------------------------------------------------------------------------------------
# (h)(i)
FILER_PTR = re.compile(r"xbrl:([^:@\s]+):")


def filer_prefixes(rec):
    u"""記録のどこかの pointer(named・基準の先頭・P22 の先頭・claim の pointers)に出る、標準でない接頭辞の字の集合(文書に書いてはいけない字)。"""
    out = set()

    def add(ptr):
        m = FILER_PTR.match(ptr) if isinstance(ptr, str) else None
        if m and not re.fullmatch(r"jp[a-z]+_cor", m.group(1)):
            out.add(m.group(1))
    for r in rec[u"rows"]:
        for k in (u"named", u"基準の先頭", u"P22 の注入後の先頭"):
            add(r[k])
        for ptr in (r[u"claim"] or {}).get("pointers") or []:
            add(ptr)
    for r in rec[u"plain_rows"]:
        for k in (u"named", u"P22 の先頭", u"fresh P26 の 名指した fact"):
            add(r[k])
    return out


def check_h(seal, doc, fetched, rec=None):
    out = []
    docs = list(fetched[u"使う書類"])
    cids, fprefs = set(), set()
    if rec is not None:
        fprefs = filer_prefixes(rec)
        for r in rec[u"rows"]:
            if (r[u"claim"] or {}).get("id"):
                cids.add(r[u"claim"]["id"])
        for r in rec[u"plain_rows"]:
            cids.add(r["id"])
    for name, t in ((u"封", seal), (u"文書", doc)):
        for d in docs:
            if d in t:
                out.append(u"%s に docID の字がある: %s" % (name, d))
        if re.findall(r"S100[0-9A-Z]{4}", t):
            out.append(u"%s に docID らしい字がある" % name)
        if re.findall(r"\b[NT]\d{3}\b", t):
            out.append(u"%s に claim の id らしい字がある" % name)
        for cid in cids:
            if re.search(r"(?<![0-9A-Za-z])%s(?![0-9A-Za-z])" % re.escape(cid), t):
                out.append(u"%s に記録の claim の id の字がある: %s" % (name, cid))
                break
        for fp in sorted(fprefs):
            if fp in t:
                out.append(u"%s に提出者別の接頭辞の字がある" % name)
                break
        if u"```" in t:
            out.append(u"%s に code fence がある" % name)
        for w in FORBIDDEN:
            if w in t:
                out.append(u"%s に禁止語: %s" % (name, w))
    return out


def make_run(repo_dir):
    def run(*args):
        r = subprocess.run(["git", "-C", repo_dir] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r.returncode, r.stdout.decode("utf-8", "replace").strip()
    return run


def added_commits(run, path):
    rc, out = run("log", "--diff-filter=A", "--format=%H", "--", path)
    return [l for l in out.splitlines() if l.strip()] if rc == 0 else []


def is_anc(run, a, b):
    return a is not None and b is not None and run("merge-base", "--is-ancestor", a, b)[0] == 0


def order_problems(run, prefix, head="HEAD"):
    u"""(i) 封の commit が script・記録・文書・門の commit より前。問題の列 [(符号, 文)]。追跡されていない file は『足した commit が無い』で赤(skip にしない)。"""
    problems = []
    seal = prefix + SEAL_REL
    s_list = added_commits(run, seal)
    if len(s_list) != 1 or not HEX40.match(s_list[0]):
        problems.append(("SEAL_ONCE", u"封を足した commit がちょうど 1 つに決まらない(%d 行)" % len(s_list)))
        return problems
    S = s_list[0]
    if not is_anc(run, S, head):
        problems.append(("SEAL<=HEAD", u"封の commit が HEAD の祖先でない"))
    for name, rel in (("SCRIPT", SCRIPT_REL), ("RECORD", REC_REL), ("DOC", DOC_REL), ("GATE", GATE_REL)):
        lst = added_commits(run, prefix + rel)
        if len(lst) == 0:
            problems.append((name + "_UNCOMMITTED", u"%s がまだ commit されていない(足した commit が無い)" % rel))
        elif len(lst) != 1 or not HEX40.match(lst[0]):
            problems.append((name + "_ONCE", u"%s を足した commit がちょうど 1 つに決まらない(%d 行)" % (rel, len(lst))))
        elif not (lst[0] != S and is_anc(run, S, lst[0])):
            problems.append((name + "_BEFORE_SEAL", u"%s の commit が封の commit より前か同じ" % rel))
    # 封を後から直していない(削除の行が 0 = 日付つきの追記だけ)
    rc, txt = run("log", "--format=%H", "%s..%s" % (S, head), "--", seal)
    for h in [l for l in txt.splitlines() if l.strip()]:
        rc2, parent = run("rev-parse", h + "^")
        base = parent if rc2 == 0 else EMPTY_TREE
        rc3, num = run("diff", "--numstat", base, h, "--", seal)
        for line in num.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1] != "0":
                problems.append(("SEAL_REWRITE", u"封の commit より後の commit %s が封の行を消している" % h[:7]))
    return problems


def codes(problems):
    return sorted(set(c for c, _m in problems))


class Tmp(object):
    def __init__(self, base):
        self.dir = tempfile.mkdtemp(prefix="unnamedfact_", dir=base)
        self.run = make_run(self.dir)
        self._g("init", "-q")

    def _g(self, *args):
        r = subprocess.run(["git", "-C", self.dir, "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"] + list(args),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert r.returncode == 0, (args, r.stderr[:300])
        return r.stdout.decode("utf-8").strip()

    def write(self, rel, text):
        p = os.path.join(self.dir, rel)
        if os.path.dirname(p) and not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)

    def commit(self, msg, *paths):
        self._g("add", "--", *paths)
        self._g("commit", "-q", "-m", msg)
        return self._g("rev-parse", "HEAD")


FILES = {"SEAL": SEAL_REL, "SCRIPT": SCRIPT_REL, "RECORD": REC_REL, "DOC": DOC_REL, "GATE": GATE_REL}


def build(base, steps):
    u"""steps は 'SEAL' 'SCRIPT' 'RECORD' 'DOC' 'GATE'(その file を 1 つの commit で足す)と変異の手 'SEAL_REWRITE' 'SEAL_APPEND' 'SEAL_TWICE' 'ALL4'(4 つを 1 commit)。"""
    t = Tmp(base)
    for s in steps:
        if s in FILES:
            t.write(FILES[s], u"# %s\n\n行 1\n行 2\n行 3\n" % s)
            t.commit(s, FILES[s])
        elif s == "ALL4":
            for k in ("SCRIPT", "RECORD", "DOC", "GATE"):
                t.write(FILES[k], u"# %s\n" % k)
            t.commit("ALL4", *[FILES[k] for k in ("SCRIPT", "RECORD", "DOC", "GATE")])
        elif s == "SEAL_REWRITE":
            t.write(FILES["SEAL"], u"# SEAL\n\n行 1\n行 3\n")
            t.commit("封を書き換える", FILES["SEAL"])
        elif s == "SEAL_APPEND":
            with open(os.path.join(t.dir, FILES["SEAL"]), "a", encoding="utf-8") as f:
                f.write(u"\n## 追記\n行 4\n")
            t.commit("封に追記", FILES["SEAL"])
        elif s == "SEAL_TWICE":
            t._g("rm", "-q", "--", FILES["SEAL"])
            t._g("commit", "-q", "-m", "封を消す")
            t.write(FILES["SEAL"], u"# SEAL\n")
            t.commit("封を足し直す", FILES["SEAL"])
        else:
            raise AssertionError(s)
    return t


# ----------------------------------------------------------------------------------------------------------------
def extract_fns(path, names, fns, extra=None):
    u"""script の AST から、names の代入と fns の関数だけを取り出して exec した名前空間(import しない)。"""
    import ast
    tree = ast.parse(jtext(path))
    body = []
    for n in tree.body:
        if isinstance(n, ast.Assign):
            tn = set(t.id for t in n.targets if isinstance(t, ast.Name)) | set(e.id for t in n.targets if isinstance(t, ast.Tuple) for e in t.elts if isinstance(e, ast.Name))
            if tn & set(names):
                body.append(n)
        elif isinstance(n, ast.FunctionDef) and n.name in fns:
            body.append(n)
    ns = {"re": re, "math": math}
    ns.update(extra or {})
    exec(compile(ast.Module(body=body, type_ignores=[]), path, "exec"), ns)
    return ns


class _NS(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)


def script_ns():
    u"""script の agree_word・ratio_of を、SR.split_pointer(止めた理由の script から AST で取る)と V.UNIT_SCALE の代わりを渡して取り出す。"""
    sr = extract_fns(os.path.join(ROOT, "measure/xbrl_stop_reason_2026-10-29.py"), ["STD_PREFIX", "PERIOD", "SOLE_MEMBER"], ["split_pointer"])
    return extract_fns(SCRIPT, ["A_NONAMED", "A_NOHEAD", "A_SAME", "A_CTX", "A_ELEM", "A_BOTH", "B_15", "B_2", "B_10", "B_10K", "B_OVER", "B_NONE"], ["agree_word", "ratio_of"],
                       {"SR": _NS(split_pointer=sr["split_pointer"]), "V": _NS(UNIT_SCALE=dict(UNIT_SCALE))})


# ----------------------------------------------------------------------------------------------------------------
class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)

    def test_a_1_the_ids_equal_the_fresh_injection_rows(self):
        self.assertEqual(check_a(self.rec, self.inp["fr"]), [])
        self.assertEqual(len(self.rec[u"rows"]), len(self.inp["fr"][u"注入の行"]))
        self.assertEqual(collections.Counter(r[u"型"] for r in self.rec[u"rows"]), collections.Counter(r[u"型"] for r in self.inp["fr"][u"注入の行"]))

    def test_a_2_the_id_set_is_read_from_fresh_not_hardcoded(self):
        fr = copy.deepcopy(self.inp["fr"])
        fr[u"注入の行"].pop(7)
        self.assertNotEqual(check_a(self.rec, fr), [])
        fr = copy.deepcopy(self.inp["fr"])
        fr[u"注入の行"][3], fr[u"注入の行"][4] = fr[u"注入の行"][4], fr[u"注入の行"][3]
        self.assertNotEqual(check_a(self.rec, fr), [])

    def b(self, rec):
        i = self.inp
        return check_b(rec, i["fr"], i["fetched"], i["stop"], i["reg"], i["d27"])

    def test_b_1_the_wiring_gates_pass_and_the_gate_recounts_them(self):
        self.assertEqual(self.b(self.rec), [])

    def test_b_2_the_record_is_the_full_run_and_has_no_leak(self):
        self.assertTrue(self.rec[u"全書類"])
        self.assertEqual(self.rec[u"key_leaks"], [])
        self.assertEqual(self.rec[u"cache"][u"開始"], self.rec[u"cache"][u"終了"])
        self.assertEqual(self.rec[u"観測する profile"], ["P27"])

    def test_b_3_w2_is_recounted_from_regress97_and_default_p27_not_from_the_record_flags(self):
        ok27, ok22, tot, sums, same = w2_recount(self.rec, self.inp["reg"], self.inp["d27"])
        self.assertEqual((ok27, ok22, tot), (len(self.inp["fetched"][u"使う書類"]),) * 3)
        self.assertTrue(same)
        self.assertEqual(sums, dict((k, self.inp["d27"]["S3"][u"既定の 4 state"][k]) for k in STATES4))

    def test_b_4_w3_the_keyed_rows_are_the_reason_rows_and_the_plain_rows_are_the_per_doc_counts(self):
        keyed, byreason, mism, nonec, nplain, perdoc = w3_recount(self.rec)
        self.assertEqual((keyed, mism), (byreason, 0))
        self.assertEqual(nplain, perdoc)
        self.assertGreater(byreason, 0)
        self.assertEqual(sum(1 for r in self.rec[u"rows"] if r[u"claim"] is None), nonec)

    def test_e_1_the_agreement_words_the_bands_and_the_heads_are_recomputed(self):
        self.assertEqual(check_e(self.rec, self.inp), [])

    def test_e_2_every_row_has_the_known_fields_and_no_text(self):
        keys = set([u"doc", u"id", u"型", u"state", u"reason", u"claim", u"named", u"named の value", u"基準の先頭", u"基準の form", u"P22 の注入後の先頭", u"P22 の recomputed",
                    u"一致(基準)", u"一致(P22)", u"value = P22 の recomputed", u"文の値", u"比", u"帯", u"10 の冪に近い", u"k"])
        for r in self.rec[u"rows"]:
            self.assertEqual(set(r), keys)
            self.assertEqual(set(r[u"claim"] or CLAIM_FIELDS), set(CLAIM_FIELDS))
        pkeys = set([u"doc", u"id", u"state", u"reason", u"named", u"named の value", u"P22 の state", u"P22 の reason", u"P22 の先頭", u"P22 の recomputed", u"一致(P22)",
                     u"fresh P26 の 名指した fact", u"一致(fresh P26)", u"fresh P26 の no_same_value に在る", u"unit", u"claim の value", u"文の値", u"比", u"帯", u"10 の冪に近い", u"k"])
        for r in self.rec[u"plain_rows"]:
            self.assertEqual(set(r), pkeys)

    def test_e_3_the_six_words_cover_every_row_once(self):
        for r in self.rec[u"rows"] + self.rec[u"plain_rows"]:
            for k in (u"一致(基準)", u"一致(P22)"):
                if k in r:
                    self.assertIn(r[k], AGREE)
        for r in self.rec[u"rows"]:
            if r["reason"] != NSV:
                self.assertEqual((r["named"], r[u"一致(基準)"], r[u"一致(P22)"]), (None, A_NONAMED, A_NONAMED))

    def test_e_4_t3_has_no_base_and_main_rows_have_a_base_from_the_stop_reason_record(self):
        for r in self.rec[u"rows"]:
            if r[u"型"] == "T3_ABSENT":
                self.assertEqual((r[u"基準の先頭"], r[u"基準の form"], r[u"一致(基準)"] in (A_NOHEAD, A_NONAMED)), (None, None, True))
            elif r["reason"] == NSV:
                self.assertIsNotNone(r[u"基準の先頭"])

    def test_e_5_the_plain_rows_are_the_p27_no_same_value_rows_with_a_p22_head(self):
        for r in self.rec[u"plain_rows"]:
            self.assertEqual(r["reason"], NSV)
            self.assertEqual(r["state"], "POINTER_NOT_FOUND")

    def test_e_6_the_gate_words_and_bands_cover_each_case_by_a_hand_made_pair(self):
        h = u"xbrl:jppfs_cor:A@CurrentYearDuration"
        cases = [(None, h, A_NONAMED), (h, None, A_NOHEAD), (None, None, A_NONAMED), (h, h, A_SAME), (u"xbrl:jppfs_cor:A@Prior1YearDuration", h, A_CTX),
                 (u"xbrl:jppfs_cor:B@CurrentYearDuration", h, A_ELEM), (u"xbrl:jppfs_cor:B@Prior1YearDuration", h, A_BOTH), (u"formula:a-b", h, A_BOTH),
                 (h, u"formula:a-b", A_BOTH), (u"xbrl:jppfs_cor:A@CurrentYearDuration_NonConsolidatedMember", h, A_CTX)]
        for a, b, want in cases:
            self.assertEqual(reagree(a, b), want, (a, b))
        self.assertEqual(set(w for _a, _b, w in cases), set(AGREE))
        edges = [(1.0, B_15), (0.85, B_15), (1.15, B_15), (0.84, B_2), (1.16, B_2), (0.5, B_2), (2.0, B_2), (0.49, B_10), (2.01, B_10), (0.1, B_10), (10.0, B_10),
                 (0.09, B_10K), (10.01, B_10K), (0.0001, B_10K), (10000.0, B_10K), (0.00009, B_OVER), (10001.0, B_OVER), (1e9, B_OVER)]
        for r, want in edges:
            self.assertEqual(reband(r, 1.0)[0], want, r)
        self.assertEqual(reband(5, 0)[0], B_NONE)
        self.assertEqual(reband(None, 5)[0], B_NONE)
        self.assertEqual(reband(5, None)[0], B_NONE)
        self.assertEqual(reband(0, 5)[0], B_OVER)
        self.assertEqual([reband(r, 1.0)[2:] for r in (1000.0, 1010.0, 1100.0, 0.001, 1e8, 2.5)], [(True, 3), (True, 3), (False, 3), (True, -3), (True, 8), (False, 0)])

    def test_e_7_the_script_functions_agree_with_the_gate_on_made_up_pairs(self):
        ns = script_ns()
        ptrs = [None, u"xbrl:jppfs_cor:A@CurrentYearDuration", u"xbrl:jppfs_cor:A@Prior1YearDuration", u"xbrl:jppfs_cor:B@CurrentYearDuration", u"xbrl:jppfs_cor:B@Prior1YearDuration",
                u"xbrl:jppfs_cor:A@CurrentYearDuration_NonConsolidatedMember", u"xbrl:jpcrp_cor:C@CurrentYearInstant", u"xbrl:jpcrp030000-asr_E99999-000:Foo@CurrentYearDuration",
                u"formula:a-b", u"builtin:x", u"xbrl:jppfs_cor:Z@Weird"]
        seen = set()
        for a in ptrs:
            for b in ptrs:
                w = ns["agree_word"](a, b)
                self.assertEqual(w, reagree(a, b), (a, b))
                seen.add(w)
        self.assertEqual(seen, set(AGREE))
        vals = [(100.0, u"千円", 100000.0), (100.0, u"千円", 100.0), (100.0, u"千円", 1.0), (5.0, u"百万円", 5.0), (51.0, u"百万円", 51000000.0), (51.0, u"百万円", 0.0), (5.0, u"億円", 3.0),
                (5.0, u"兆円", 7.0), (5.0, u"円", 5.0), (5.0, u"円", 6.0), (5.0, u"円", 4.0), (5.0, u"円", 1e9), (5.0, u"円", 1e-3), (5.0, u"円", None), (None, u"円", 5.0), (5.0, None, 5.0),
                (5.0, u"ドル", 5.0), (0.0, u"円", 5.0), (-5.0, u"円", 5.0), (5.0, u"円", -5.0)]
        vals += [(r, u"円", 1.0) for r in (0.85, 0.84, 1.15, 1.16, 0.5, 0.49, 2.0, 2.01, 0.1, 0.09, 10.0, 10.01, 0.0001, 0.00009, 10000.0, 10001.0, 1000.0, 1010.0, 1100.0)]
        for cv, unit, nv in vals:
            got = ns["ratio_of"](cv, unit, nv)
            sv = None if (cv is None or unit not in UNIT_SCALE) else cv * UNIT_SCALE[unit]
            band, ratio, p10, k = reband(sv, nv)
            self.assertEqual((got[u"帯"], got[u"比"], got[u"10 の冪に近い"], got[u"k"], got[u"文の値"]), (band, ratio, p10, k, sv), (cv, unit, nv))

    def test_e_8_the_script_wrapper_keeps_the_return_value_restores_the_function_and_stops_when_it_cannot(self):
        u"""run_doc の包みを AST で取り出し、偽の RE・LB で動かす: 返り値は同じ・捕捉は P27 と無改変の P22 だけ・例外でも戻る・戻せなければ止まる。"""
        ns = extract_fns(SCRIPT, ["NSV"], ["run_doc"])
        calls = []

        def fake_verify(tap, zb, prof, text=None):
            calls.append((prof, text))
            out = {"claims": [{"id": "N001", "reason": NSV if prof == "P27" else None, "state": "POINTER_NOT_FOUND"}]}
            raw = {"N001": {"id": "N001", "reason": "value differs" if prof == "P22" else NSV, NSV: {"named": u"xbrl:jppfs_cor:A@CurrentYearDuration", "value": 5.0} if prof == "P27" else None}}
            return out, raw, ["s"]
        results = []

        class LBfake(object):
            verify_raw = staticmethod(fake_verify)

        class REfake(object):
            LB_ = LBfake

            @staticmethod
            def work_doc(a):
                for prof, text in (("P22", None), ("P26", None), ("P27", None), ("P27", u"t1"), ("P27", u"t2"), ("P22", u"t3")):
                    results.append(LBfake.verify_raw(None, None, prof, text))
                return {"rows": [1, 2]}
        ns["RE"], ns["LB"] = REfake, LBfake
        orig = LBfake.verify_raw
        r = ns["run_doc"](("d",))
        self.assertIs(LBfake.verify_raw, orig)                                     # 戻っている
        self.assertEqual(len(calls), 6)
        self.assertEqual(len(r[u"cap"][u"P27 注入後"]), 2)                          # 注入後の P27 の捕捉は 2 回
        self.assertEqual(len(r[u"cap"][u"P27 無改変"]), 1)
        self.assertEqual(len(r[u"cap"][u"P22 無改変"]), 1)                          # 注入後の P22・P26 は捕捉しない
        self.assertEqual(r[u"cap"][u"P27 注入後"][0][u"nsv"]["N001"], {"named": u"xbrl:jppfs_cor:A@CurrentYearDuration", "value": 5.0})
        self.assertEqual(r[u"cap"][u"P27 無改変"][0][u"raw reason"]["N001"], NSV)
        for (out, raw, sents), prof in zip(results, ("P22", "P26", "P27", "P27", "P27", "P22")):   # 返り値は包みの無いときと同じ内容
            self.assertEqual(out["claims"][0]["reason"], NSV if prof == "P27" else None)
            self.assertEqual(sents, ["s"])
        # 例外でも戻る
        REfake.work_doc = staticmethod(lambda a: (_ for _ in ()).throw(RuntimeError("x")))
        with self.assertRaises(RuntimeError):
            ns["run_doc"](("d",))
        self.assertIs(LBfake.verify_raw, orig)

        # 戻せなければ止まる(代入を無視する LB)
        class LBstuck(object):
            def __init__(self):
                object.__setattr__(self, "verify_raw", fake_verify)
                object.__setattr__(self, "_n", 0)

            def __setattr__(self, k, v):
                if k == "verify_raw" and self._n >= 1:
                    return                                                          # 2 回目(戻す代入)を無視する
                object.__setattr__(self, k, v)
                object.__setattr__(self, "_n", self._n + 1)
        stuck = LBstuck()

        class REstuck(object):
            @staticmethod
            def work_doc(a):
                return {"rows": []}
        ns["RE"], ns["LB"] = REstuck, stuck
        with self.assertRaises(SystemExit):
            ns["run_doc"](("d",))

    def test_j_1_the_inputs_read_are_unchanged(self):
        self.assertEqual(check_j(self.rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"読んだ入力の sha256"][DEFAULT27_REL] = u"0" * 64
        self.assertNotEqual(check_j(rec), [])
        rec = copy.deepcopy(self.rec)
        del rec[u"読んだ入力の sha256"][STOP_REL]
        self.assertNotEqual(check_j(rec), [])

    def test_d_1_judgments_are_recomputed_and_cover_the_fourteen_predictions(self):
        J = judge(self.rec, self.inp, self.seal)
        self.assertEqual(list(J), ["UF-%d" % i for i in range(1, 15)])
        self.assertTrue(all(v[1] in (True, False, None) for v in J.values()))

    def test_d_2_the_judge_is_not_a_constant(self):
        J0 = judge(self.rec, self.inp, self.seal)
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"W-1"][u"前の便の門(4 欄とも一致)"][0] -= 1
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-1"], J0["UF-1"])
        rec = copy.deepcopy(self.rec)
        r = [x for x in nsv_rows(rec) if x[u"型"] == "T1_VALUE"][0]
        r[u"一致(基準)"] = A_ELEM
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-5"], J0["UF-5"])
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-6"], J0["UF-6"])
        rec = copy.deepcopy(self.rec)
        r = [x for x in nsv_rows(rec) if x[u"型"] == "T3_ABSENT"][0]
        r["named"] = None
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-7"], J0["UF-7"])
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-4"], J0["UF-4"])
        rec = copy.deepcopy(self.rec)
        r = [x for x in nsv_rows(rec) if agree_of(x) == A_SAME][0]
        r[u"value = P22 の recomputed"] = False
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-8"], J0["UF-8"])
        rec = copy.deepcopy(self.rec)
        rec[u"plain_rows"].pop()
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-9"], J0["UF-9"])
        rec = copy.deepcopy(self.rec)
        rec[u"plain_rows"][0][u"帯"] = B_OVER if rec[u"plain_rows"][0][u"帯"] == B_15 else B_15
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-13"], J0["UF-13"])
        rec = copy.deepcopy(self.rec)
        for r in nsv_rows(rec):
            if r[u"型"] == "T5_COINCIDENT":
                r[u"帯"] = B_OVER
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-12"], J0["UF-12"])
        rec = copy.deepcopy(self.rec)
        for r in nsv_rows(rec):
            if r[u"型"] != "T3_ABSENT" and r[u"一致(基準)"] == A_SAME:
                r["named"] = r["named"].split(u"@")[0] + u"@Prior2YearInstant"
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-14"], J0["UF-14"])
        rec = copy.deepcopy(self.rec)
        rec[u"plain_rows"][0][u"一致(fresh P26)"] = not rec[u"plain_rows"][0][u"一致(fresh P26)"] if rec[u"plain_rows"][0][u"一致(fresh P26)"] is not None else True
        rec[u"plain_rows"][0][u"fresh P26 の 名指した fact"] = rec[u"plain_rows"][0][u"fresh P26 の 名指した fact"] or u"xbrl:jppfs_cor:Q@CurrentYearDuration"
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-11"], J0["UF-11"])
        rec = copy.deepcopy(self.rec)
        d = rec[u"書類(出てくる順)"][0]
        rec[u"書類ごと"][d][u"無改変の 4 state"]["P27"]["GROUNDED"] += 1
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-2"], J0["UF-2"])
        rec = copy.deepcopy(self.rec)
        rec[u"rows"][0][u"claim"] = None if rec[u"rows"][0][u"claim"] is not None else rec[u"rows"][0][u"claim"]
        rec[u"plain_rows"] = rec[u"plain_rows"][:-1]
        self.assertNotEqual(judge(rec, self.inp, self.seal)["UF-10"], J0["UF-10"])


class EngineTest(unittest.TestCase):
    def test_f_1_engine_sha16_are_pinned_or_declared(self):
        rec = jload(REC)
        self.assertEqual(rec[u"engine sha16"], ENGINE_AT_MEASURE)
        self.assertEqual(rec[u"DEFAULT_PROFILE"], "P27")
        self.assertEqual(rec[u"engine sha16"], rload(STOP_REL)[u"engine sha16"])
        for rel, want in ENGINE_AT_MEASURE.items():
            got = sha16(rel)
            if got != want and rel in ENGINE_DECLARED:
                later, seal_rel = ENGINE_DECLARED[rel]
                added = git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split()
                self.assertTrue(added, u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, u"**%s が動いている**" % rel)

    def test_f_2_the_declared_transition_form_is_red_for_an_unknown_value(self):
        def accepts(got, rel, want, declared):
            if got != want and rel in declared:
                return got == declared[rel][0]
            return got == want
        rel = "adapters/xbrl/vocabulary.py"
        want = ENGINE_AT_MEASURE[rel]
        self.assertTrue(accepts(want, rel, want, {}))
        self.assertFalse(accepts("0" * 16, rel, want, {}))
        self.assertTrue(accepts("1" * 16, rel, want, {rel: ("1" * 16, "x")}))
        self.assertFalse(accepts("2" * 16, rel, want, {rel: ("1" * 16, "x")}))

    def test_f_3_core_and_adapters_have_no_uncommitted_change(self):
        r = git("status", "--porcelain", "--", "adapters", "core")
        self.assertEqual(r.stdout.strip(), u"", u"engine の file に未 commit の変更がある")


class SealAndDocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def test_c_1_the_tables_equal_the_ones_rebuilt_from_the_record(self):
        self.assertEqual(check_c(self.rec, self.inp, self.seal, self.doc), [])

    def test_c_2_the_prose_outside_the_tables_is_in_order(self):
        self.assertEqual(check_doc_prose(self.rec, self.inp, self.seal, self.doc), [])

    def test_d_3_the_prediction_table_copies_the_seal_and_the_judgments(self):
        SP = seal_predictions(self.seal)
        J = judge(self.rec, self.inp, self.seal)
        got = doc_blocks(self.doc)["pred"]
        self.assertEqual(len(got), 2 + len(J))
        for line, k in zip(got[2:], J):
            cells = [c.strip() for c in line.strip().strip(u"|").split(u" | ")]
            self.assertEqual(cells[0], u"**%s**" % k)
            self.assertEqual(tuple(cells[1:4]), SP[k], k)
            self.assertEqual(cells[4], J[k][0], k)
            self.assertEqual(cells[5], hit_word(J[k][1]), k)

    def test_d_4_the_seal_prediction_table_is_what_this_gate_reads(self):
        u"""封の表の形(幅の数は字で留めない。『幅が何本あるか』『何が太字か』の形だけを見る)。"""
        SP = seal_predictions(self.seal)
        self.assertEqual(list(SP), ["UF-%d" % i for i in range(1, 15)])
        self.assertEqual([len(ranges_of(SP["UF-%d" % i][1])) for i in range(1, 15)], [0, 0, 0, 0, 2, 1, 1, 0, 1, 0, 0, 6, 2, 0])
        self.assertEqual([len(singles_of(SP["UF-%d" % i][1])) for i in range(1, 15)], [3, 2, 5, 3, 1, 1, 1, 1, 2, 2, 0, 4, 0, 1])
        self.assertEqual([len(pcts_of(SP["UF-%d" % i][1])) for i in range(1, 15)], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 2])
        self.assertEqual(singles_of(SP["UF-14"][1]), [u"全部"])

    def test_d_5_the_misses_are_kept_as_misses(self):
        J = judge(self.rec, self.inp, self.seal)
        self.assertEqual([k for k, v in J.items() if v[1] is False], MISSES)
        self.assertEqual([k for k, v in J.items() if v[1] is None], UNDECIDED)
        self.assertEqual([k for k, v in J.items() if v[1] is True], [k for k in J if k not in MISSES and k not in UNDECIDED])

    def test_h_1_no_docid_no_claim_id_and_no_filer_prefix_in_the_seal_and_the_document(self):
        fetched = self.inp["fetched"]
        self.assertEqual(check_h(self.seal, self.doc, fetched, self.rec), [])
        self.assertEqual(len(fetched[u"使う書類"]), 30)
        # 提出者別の接頭辞が記録に 1 つも出ないなら、集める関数が黙る。本物に効くことは下の h_3・g_8 で見る
        self.assertTrue(any(r["named"] and r["named"].startswith(u"xbrl:") for r in self.rec[u"rows"]))

    def test_h_3_the_filer_prefix_collector_works_on_a_made_up_pointer(self):
        rec = copy.deepcopy(self.rec)
        nsv_rows(rec)[0]["named"] = u"xbrl:jpcrp030000-asr_E99999-000:Foo@CurrentYearDuration"
        self.assertEqual(filer_prefixes(rec) - filer_prefixes(self.rec), set([u"jpcrp030000-asr_E99999-000"]))
        fetched = self.inp["fetched"]
        self.assertEqual(check_h(self.seal, self.doc, fetched, rec), [])
        self.assertNotEqual(check_h(self.seal, self.doc + u"\njpcrp030000-asr_E99999-000\n", fetched, rec), [])
        self.assertNotEqual(check_h(self.seal + u"\njpcrp030000-asr_E99999-000\n", self.doc, fetched, rec), [])

    def test_h_2_the_record_names_the_documents_and_that_is_why_it_is_declared(self):
        txt = jtext(REC)
        docs = self.inp["fetched"][u"使う書類"]
        self.assertTrue(all(d in txt for d in docs))
        fresh_seal = jtext(os.path.join(HERE, "test_xbrl_fresh_seal.py"))
        for p in (REC_REL, SCRIPT_REL, GATE_REL):
            self.assertIn(u'"%s"' % p, fresh_seal, p)
        harness = jtext(os.path.join(HERE, "test_xbrl_inject_harness_review.py"))
        self.assertIn(u'("%s", u"使う側", u"有", "run_doc", u"r = RE.work_doc(a)", "2026-10-29")' % SCRIPT_REL, harness)

    def test_doc_states_the_dated_notes(self):
        self.assertIn(u"2026-10-29", self.doc)
        self.assertIn(u"stop_reason_2026-10-29.json", self.doc)


class ScriptTest(unittest.TestCase):
    def test_script_does_not_remeasure_when_the_output_exists(self):
        before = hashlib.sha256(open(REC, "rb").read()).hexdigest()
        env = dict((k, v) for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "EDINET_API_KEY", "EDINETDB_API_KEY"))
        r = subprocess.run(["python3", SCRIPT, "--out", REC], cwd=ROOT, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        self.assertIn(u"測り直さない", r.stdout)
        self.assertEqual(hashlib.sha256(open(REC, "rb").read()).hexdigest(), before)

    def test_script_has_one_word_function_and_one_ratio_function_and_sets_only_obs(self):
        import ast
        tree = ast.parse(jtext(SCRIPT))
        fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        self.assertEqual(fns.count("agree_word"), 1)
        self.assertEqual(fns.count("ratio_of"), 1)
        self.assertEqual(fns.count("run_doc"), 1)
        sets = [ast.unparse(n.targets[0]) for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Attribute)]
        self.assertEqual(sorted(sets), ["RE.ALLP", "RE.OBS"])                                   # 前の便の module の値を替えるのはこの 2 つだけ
        self.assertEqual(sum(1 for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) == "RE.work_doc"), 1)

    def test_script_imports_no_network_module_and_reads_no_key(self):
        import ast
        tree = ast.parse(jtext(SCRIPT))
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods |= set(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        self.assertEqual(mods, set(["__future__", "argparse", "collections", "concurrent", "importlib", "io", "json", "math", "multiprocessing", "os", "shutil", "sys", "tempfile", "time"]))
        consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        self.assertFalse([c for c in consts if "API_KEY" in c or "environ" in c])
        self.assertFalse([n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr in ("environ", "getenv")])


class FalseRecordsAreRedTest(unittest.TestCase):
    u"""(g) 偽物で赤: 記録の写しを 1 か所変えると (b)(c)(e) が赤になる(変異)。"""

    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def b(self, rec):
        i = self.inp
        return check_b(rec, i["fr"], i["fetched"], i["stop"], i["reg"], i["d27"])

    def c(self, rec, doc=None, seal=None):
        return check_c(rec, self.inp, seal or self.seal, doc or self.doc)

    def e(self, rec):
        return check_e(rec, self.inp)

    def test_g_0_baseline_is_green(self):
        self.assertEqual(self.b(self.rec), [])
        self.assertEqual(self.c(self.rec), [])
        self.assertEqual(self.e(self.rec), [])

    def test_g_1_changing_one_agreement_word_turns_e_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in nsv_rows(rec) if x[u"型"] == "T5_COINCIDENT" and x[u"一致(基準)"] == A_SAME][0]
        r[u"一致(基準)"] = A_CTX
        self.assertNotEqual(self.e(rec), [])
        self.assertNotEqual(self.c(rec), [])
        self.assertEqual(self.b(rec), [])                                   # b は語を見ない(1 つの性質は所有する 1 か所で)
        rec = copy.deepcopy(self.rec)
        r = [x for x in rec[u"plain_rows"] if x[u"一致(P22)"] == A_SAME][0]
        r[u"一致(P22)"] = A_ELEM
        self.assertNotEqual(self.e(rec), [])
        self.assertNotEqual(self.c(rec), [])

    def test_g_2_changing_named_turns_e_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in nsv_rows(rec) if x[u"型"] == "T5_COINCIDENT" and x[u"一致(基準)"] == A_SAME][0]
        r["named"] = u"xbrl:jppfs_cor:ZZZ@CurrentYearInstant"
        self.assertNotEqual(self.e(rec), [])
        self.assertNotEqual(self.c(rec), [])                                # (同じ)の行の要素名の表が動く
        rec = copy.deepcopy(self.rec)
        r = [x for x in nsv_rows(rec) if x[u"型"] == "T5_COINCIDENT"][0]
        r["named"] = None
        self.assertNotEqual(self.e(rec), [])
        self.assertNotEqual(self.b(rec), [])                                # 鍵が在る行 != reason の行

    def test_g_3_changing_the_named_value_turns_e_red_and_the_flag_turns_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in nsv_rows(rec) if agree_of(x) == A_SAME][0]
        r[u"named の value"] += 1
        self.assertNotEqual(self.e(rec), [])                                # value = P22 の recomputed と 比 が動く
        rec = copy.deepcopy(self.rec)
        r = [x for x in nsv_rows(rec) if agree_of(x) == A_SAME][0]
        r[u"value = P22 の recomputed"] = False
        self.assertNotEqual(self.e(rec), [])
        self.assertNotEqual(self.c(rec), [])                                # value の表と UF-8 が動く

    def test_g_4_changing_the_ratio_or_the_band_turns_e_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in nsv_rows(rec) if x[u"型"] == "T5_COINCIDENT"][0]
        r[u"比"] = r[u"比"] * 1.5
        self.assertNotEqual(self.e(rec), [])
        rec = copy.deepcopy(self.rec)
        r = [x for x in nsv_rows(rec) if x[u"型"] == "T5_COINCIDENT" and x[u"帯"] != B_OVER][0]
        r[u"帯"] = B_OVER
        self.assertNotEqual(self.e(rec), [])
        self.assertNotEqual(self.c(rec), [])
        rec = copy.deepcopy(self.rec)
        r = [x for x in nsv_rows(rec) if x[u"型"] == "T2_UNIT" and x[u"10 の冪に近い"] is True][0]
        r[u"10 の冪に近い"] = False
        self.assertNotEqual(self.e(rec), [])
        self.assertNotEqual(self.c(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"plain_rows"][0][u"文の値"] = (rec[u"plain_rows"][0][u"文の値"] or 1.0) * 3
        self.assertNotEqual(self.e(rec), [])

    def test_g_5_changing_the_wiring_flag_turns_b_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"配線の行ごと"][0][u"一致"][u"4 欄とも一致"] = False
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"W-1"][u"P27 の pointers"] -= 1
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"W-1"][u"P27 の全欄(10 欄 + recomputed)"] -= 1
        self.assertNotEqual(self.b(rec), [])
        self.assertNotEqual(self.c(rec), [])                                # 表『wiring』は script の全欄の数も写す
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"W-3"][u"鍵が在る行(注入後)"] -= 1
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"W-3"][u"id と reason の照合"][0] -= 1
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        d = rec[u"書類(出てくる順)"][0]
        rec[u"書類ごと"][d][u"無改変の 4 state"]["P27"]["VALUE_MISMATCH"] += 1
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"W-2"][u"P27 の和"]["GROUNDED"] += 1
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"通った"] = False
        self.assertNotEqual(self.b(rec), [])

    def test_g_6_changing_the_claim_turns_b_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"rows"][0][u"claim"]["pointers"] = rec[u"rows"][0][u"claim"]["pointers"] + [u"xbrl:jppfs_cor:Q@CurrentYearDuration"]
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"rows"][0][u"claim"]["recomputed"] = 1.5
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"rows"][0][u"claim"][u"span"] = u"x"
        self.assertNotEqual(self.e(rec), [])

    def test_g_7_one_character_of_the_document_table_turns_c_red(self):
        for name in ("agree", "agree_p22", "value", "plain", "ratio", "elements", "context", "wiring", "nsv"):
            i = self.doc.index(u"<!-- 門:start %s -->" % name)
            j = self.doc.index(u"<!-- 門:end -->", i)
            seg = self.doc[i:j]
            s0 = seg.index(u"\n|---")
            k = re.search(r"\| (\d+) \|", seg[s0:]) or re.search(r"\| (\d+) ", seg[s0:])
            self.assertIsNotNone(k, name)
            seg2 = seg[:s0 + k.start(1)] + str(int(k.group(1)) + 1) + seg[s0 + k.end(1):]
            doc = self.doc[:i] + seg2 + self.doc[j:]
            self.assertNotEqual(doc, self.doc)
            self.assertNotEqual(self.c(self.rec, doc=doc), [], name)
        i = self.doc.index(u"<!-- 門:start pred -->")
        doc = self.doc[:i] + self.doc[i:].replace(u"**当たり**", u"**外れ**", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(self.c(self.rec, doc=doc), [])

    def test_g_8_changing_a_prediction_character_of_the_seal_turns_d_and_c_red(self):
        seal = u"\n".join(l.replace(u"**741 / 741**", u"**741 / 740**", 1) if l.startswith(u"| **UF-1**") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(judge(self.rec, self.inp, seal)["UF-1"], judge(self.rec, self.inp, self.seal)["UF-1"])
        self.assertNotEqual(self.c(self.rec, seal=seal), [])
        seal = u"\n".join(l.replace(u"**290 以上 300 以下**", u"**290 以上 295 以下**", 1) if l.startswith(u"| **UF-9**") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(self.c(self.rec, seal=seal), [])

    def test_g_9_a_docid_a_claim_id_or_a_filer_prefix_in_the_document_turns_h_red(self):
        fetched = self.inp["fetched"]
        doc = self.doc + u"\n" + fetched[u"使う書類"][0] + u"\n"
        self.assertNotEqual(check_h(self.seal, doc, fetched, self.rec), [])
        doc = self.doc + u"\nN012\n"
        self.assertNotEqual(check_h(self.seal, doc, fetched, self.rec), [])
        cid = self.rec[u"plain_rows"][0]["id"]
        doc = self.doc + u"\n%s\n" % cid
        self.assertNotEqual(check_h(self.seal, doc, fetched, self.rec), [])
        rec = copy.deepcopy(self.rec)
        nsv_rows(rec)[0]["named"] = u"xbrl:jpcrp030000-asr_E99999-000:Foo@CurrentYearDuration"
        doc = self.doc + u"\njpcrp030000-asr_E99999-000\n"
        self.assertNotEqual(check_h(self.seal, doc, fetched, rec), [])

    def test_g_10_an_unmarked_number_in_prose_turns_the_prose_check_red(self):
        doc = self.doc + u"\n同じ行は 7 行だった。\n"
        self.assertNotEqual(check_doc_prose(self.rec, self.inp, self.seal, doc), [])

    def test_g_11_changing_the_hit_word_in_the_prose_turns_the_prose_check_red(self):
        doc = self.doc.replace(u"外れた予測: ", u"外れた予測: UF-99・", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(check_doc_prose(self.rec, self.inp, self.seal, doc), [])


class OrderTest(unittest.TestCase):
    u"""(i) 封の commit が script・記録・文書・門の commit より前。"""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="unnamedfact_root_")
        cls.grun = staticmethod(make_run(REPO))

    def _p(self, steps):
        t = build(self.base, steps)
        return order_problems(t.run, "")

    def test_i_1_the_real_history_has_the_seal_before_the_four_files(self):
        u"""script・記録・文書・門のどれかが未 commit なら赤(足した commit が無い)。4 つとも commit された後で初めて緑。"""
        p = order_problems(self.grun, PREFIX)
        self.assertEqual(p, [])

    def test_i_2_the_real_seal_is_one_commit_and_an_ancestor_of_head(self):
        lst = added_commits(self.grun, PREFIX + SEAL_REL)
        self.assertEqual(len(lst), 1)
        self.assertTrue(lst[0].startswith(SEAL_COMMIT_SHORT))
        self.assertTrue(is_anc(self.grun, lst[0], "HEAD"))

    def test_i_3_a_correct_order_is_green(self):
        self.assertEqual(self._p(["SEAL", "SCRIPT", "RECORD", "DOC", "GATE"]), [])
        self.assertEqual(self._p(["SEAL", "ALL4"]), [])
        self.assertEqual(self._p(["SEAL", "ALL4", "SEAL_APPEND"]), [])

    def test_i_4_a_file_before_the_seal_is_red(self):
        for first in ("SCRIPT", "RECORD", "DOC", "GATE"):
            steps = [first, "SEAL"] + [k for k in ("SCRIPT", "RECORD", "DOC", "GATE") if k != first]
            self.assertIn(first + "_BEFORE_SEAL", codes(self._p(steps)), first)

    def test_i_5_an_uncommitted_file_is_red_not_skipped(self):
        self.assertIn("GATE_UNCOMMITTED", codes(self._p(["SEAL", "SCRIPT", "RECORD", "DOC"])))
        self.assertIn("SCRIPT_UNCOMMITTED", codes(self._p(["SEAL"])))

    def test_i_6_the_seal_missing_or_added_twice_is_red(self):
        self.assertIn("SEAL_ONCE", codes(self._p(["ALL4"])))
        self.assertIn("SEAL_ONCE", codes(self._p(["SEAL", "ALL4", "SEAL_TWICE"])))

    def test_i_7_rewriting_the_seal_after_the_fact_is_red(self):
        self.assertIn("SEAL_REWRITE", codes(self._p(["SEAL", "ALL4", "SEAL_REWRITE"])))

    def test_i_8_the_same_commit_as_the_seal_is_red(self):
        t = Tmp(self.base)
        for k in ("SEAL", "SCRIPT", "RECORD", "DOC", "GATE"):
            t.write(FILES[k], u"# %s\n" % k)
        t.commit("all", *FILES.values())
        self.assertIn("SCRIPT_BEFORE_SEAL", codes(order_problems(t.run, "")))


if __name__ == "__main__":
    unittest.main()
