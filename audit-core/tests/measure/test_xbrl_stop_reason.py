# -*- coding: utf-8 -*-
u"""注入 741 行で「道具が止めた理由」と「名指し」を分類し、P27E を同じ 741 行で測る診断の門 ― 封 docs/XBRL_STOP_REASON_DIAG_SEAL_2026-10-29.md §5-2 の (a)〜(j)。

記録 ``fixtures/xbrl/stop_reason_2026-10-29.json``(``measure/xbrl_stop_reason_2026-10-29.py`` の出力)・文書 ``docs/XBRL_STOP_REASON_DIAG_2026-10-29.md``。

  (a) 記録の 741 行の id が ``fresh_2026-10-21.json`` の ``注入の行`` の id と順も集合も同じ(字で留めない)。型別の数も同じ。
  (b) 配線の門 W-1〜W-3 が記録の数で通っている。P22・P26・P27 の欄を ``inject_reach_2026-10-28.json`` と門が自分で比べ直して 741 / 741、W-2 を ``regress97`` と門が自分で比べ直して 30 書類 × 4 profile と 24 行。
  (c) 文書の表を記録から作り直して 1 行も違わない(``<!-- 門:start 名前 -->`` の中)。``eval`` の表は ``eval_inject_2026-10-27.json`` から。門の外の散文の数には【門なし】の印が要る。
  (d) SR-1〜SR-17 の当否を記録から求め(幅は封の表の字から読む。字で留めない)、封の字(欄・予測・外れ方)と、文書の当否の表の字が一致する。
  (e) 分類(13 語)・名指しの 2 本・要素名の切り出しを、記録の欄(claim の state・reason・pointers・recomputed)から別の書き方で求め直して一致する。
  (f) engine の sha16 を ``ENGINE_AT_MEASURE``(字で留める)と ``ENGINE_DECLARED``(宣言された遷移。今は空)で留める。
  (g) 偽物で赤: 記録の写しの語・先頭の pointer・recomputed・配線の旗を 1 か所変えると (b)(c)(e) が赤。文書の表の 1 字で (c) が赤、封の予測の 1 字で (d)(c) が赤、文書に提出者別の接頭辞の字を 1 つ足すと (h) が赤。
  (h) 封と文書に 30 書類の docID・記録の claim の id・提出者別の接頭辞の字が無い。
  (i) 封の commit が script・記録・文書・門の commit より前(git の commit の順)。
  (j) 記録が持つ読んだ入力 4 つの sha256 がいまの file と一致する。

**(i) は、script・記録・文書・門のどれかが commit される前は赤になる**(追跡されていない file には『足した commit』が無い)。skip にしない。前例 ``test_xbrl_inject_reach.py`` と同じ扱い。
**変数名について**: 過去の門が tests/measure の行頭の名前を数えるので、この門はそれらを行頭に置かない。この file は docID の字を持たない(``fetched_2026-10-21.json`` から読む)。
"""
import collections
import copy
import hashlib
import io
import json
import os
import re
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"

SEAL_REL = "docs/XBRL_STOP_REASON_DIAG_SEAL_2026-10-29.md"
DOC_REL = "docs/XBRL_STOP_REASON_DIAG_2026-10-29.md"
REC_REL = "fixtures/xbrl/stop_reason_2026-10-29.json"
SCRIPT_REL = "measure/xbrl_stop_reason_2026-10-29.py"
GATE_REL = "tests/measure/test_xbrl_stop_reason.py"
FRESH_REL = "fixtures/xbrl/fresh/fresh_2026-10-21.json"
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
REACH_REL = "fixtures/xbrl/inject_reach_2026-10-28.json"
REGRESS_REL = "fixtures/xbrl/p27/regress97_2026-10-27.json"
EVAL_REL = "fixtures/xbrl/p27/eval_inject_2026-10-27.json"
SEAL, DOC, REC = [os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL)]
SCRIPT = os.path.join(ROOT, SCRIPT_REL)
SEAL_COMMIT_SHORT = "6bea94b"
P4 = ("P22", "P26", "P27", "P27E")
MAIN_TYPES = ("T1_VALUE", "T2_UNIT", "T5_COINCIDENT")
ALL_TYPES = MAIN_TYPES + ("T3_ABSENT",)
TSHORT = {"T1_VALUE": u"T1", "T2_UNIT": u"T2", "T5_COINCIDENT": u"T5", "T3_ABSENT": u"T3"}
NOT_GATED = u"【門なし】"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
FORBIDDEN = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")
STATES4 = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")

W_NOMAP, W_PASS = u"(対応が付かない)", u"(通した)"
W_NAMED, W_OTHERFACT, W_NOBASE = u"(名指した・原本)", u"(名指した・別の fact)", u"(名指した・基準なし)"
W_NOSAME, W_OTHERCON, W_NOELEM, W_NOPTR = u"(要確認・証拠が無く名指さない)", u"(要確認・別の概念)", u"(要確認・要素が無い)", u"(要確認・pointer が引けない)"
W_NOSUBJ, W_AMBIG, W_FRAME, W_OUT = u"(要確認・主語が無い)", u"(要確認・候補が複数)", u"(要確認・主張の形で保留)", u"(形の外)"
WORDS = (W_NOMAP, W_PASS, W_NAMED, W_OTHERFACT, W_NOBASE, W_NOSAME, W_OTHERCON, W_NOELEM, W_NOPTR, W_NOSUBJ, W_AMBIG, W_FRAME, W_OUT)
STOPPED = WORDS[2:]                                        # 『止めた』= 語 3〜13
NAMED3 = (W_NAMED, W_OTHERFACT, W_NOBASE)                  # 語 3・4・5
SOLE = "NonConsolidatedMember"
PERIODS = [a + b for a in ("CurrentYear", "Prior1Year", "Prior2Year") for b in ("Duration", "Instant")] + [u"その他"]
FILER = u"(提出者別の要素)"
FILER_PREFIX = u"(提出者別の接頭辞)"

#: engine の sha16(記録を測った時点の値。字で留める ― 測った事実。前の便の記録と同じ 6 本)。変えるなら宣言された遷移として下の ENGINE_DECLARED に足す。
ENGINE_AT_MEASURE = {
    "adapters/xbrl/extract.py": "3cf55966f12919f0", "adapters/xbrl/vocabulary.py": "514ebb8104451c07", "adapters/xbrl/recipes.py": "52d645e713c53c1c",
    "adapters/xbrl/resolve.py": "a41043763c1d4073", "adapters/xbrl/comparators.py": "d8706338325e725b", "adapters/xbrl/verify_document.py": "c3791080ab5aef2f",
}
#: 宣言された遷移 {file: (遷移の後の sha16, その遷移を宣言した封)}。今は 0 件。足すときは、封が履歴に在り、値が宣言の値のときだけ受け入れる。測った時点の値は消さない。
# 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。この 6 本のうち動くのは vocabulary.py(旗 1 つ・P27C・PROFILES の登録)と
# verify_document.py(Claim の欄 candidate)。測った時点の値は ENGINE_AT_MEASURE に残す。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
ENGINE_DECLARED = {"adapters/xbrl/vocabulary.py": ("7fbcfbf0e472f366", "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md"),
                   "adapters/xbrl/verify_document.py": ("6c76c8ade6c7b1c8", "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md")}

#: 記録から求めた当否のうち外れ・判定しないの名前(測った事実。外れは外れのまま残す。封も予測も直さない)。食い違えば d_5 が赤。
#: 今回は 17 本のうち 3 本が外れ(SR-6・SR-12・SR-13)。判定しないは 0 本。
MISSES = ["SR-6", "SR-12", "SR-13"]
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
    return {"fr": rload(FRESH_REL), "fetched": rload(FETCHED_REL), "reach": rload(REACH_REL), "reg": rload(REGRESS_REL), "eval": rload(EVAL_REL)}


# ----------------------------------------------------------------------------------------------------------------
# 記録の読み出し
def mains(rec):
    return [r for r in rec[u"rows"] if r[u"型"] in MAIN_TYPES]


def of_type(rec, t):
    return [r for r in rec[u"rows"] if r[u"型"] == t]


def nm(r, p):
    return r[u"profile"][p][u"名指し"]


def word(r, p):
    return nm(r, p)[u"語"]


def after_claim(r, p):
    x = r[u"profile"][p]
    return x[u"claim"] if r[u"型"] == "T3_ABSENT" else x[u"注入後"][u"claim"]


def base_claim(r, p):
    return None if r[u"型"] == "T3_ABSENT" else r[u"profile"][p][u"無改変"][u"claim"]


def groups(rec):
    return [(TSHORT[t], of_type(rec, t)) for t in MAIN_TYPES] + [(u"計", mains(rec)), (TSHORT["T3_ABSENT"], of_type(rec, "T3_ABSENT"))]


def positions(rec):
    u"""{id: (書類の番号, 型, その書類・その型の中の番号)}(記録の出てくる順。1 始まり)。"""
    order = rec[u"書類(出てくる順)"]
    seen, out = collections.Counter(), {}
    for r in rec[u"rows"]:
        d = order.index(r["doc"]) + 1
        seen[(d, r[u"型"])] += 1
        out[r["id"]] = (d, r[u"型"], seen[(d, r[u"型"])])
    return out


def plabel(p):
    return u"書類 %d・%s の %d 番目" % (p[0], TSHORT[p[1]], p[2])


def edit_of(r):
    return u"挿入" if r[u"型"] == "T3_ABSENT" else u"%s → %s" % (r[u"元の字"], r[u"後の字"])


# ----------------------------------------------------------------------------------------------------------------
# (e) 分類・名指し・要素名の切り出しを、記録の claim の欄から別の書き方で求め直す(script の関数は import しない)
def _first_ptr(c):
    ps = (c or {}).get("pointers") or []
    return ps[0] if ps else None


def _rules():
    u"""(条件, 語) の並び。先に当たったものを取る(封 §2-3 の表の 1〜13)。条件は (typ, claim, base) を取る。"""
    rs = lambda c: (c["state"], c["reason"])
    hold = set([u"other_frame", u"rounded_diff_within_double_band", u"per_unit_counter", u"target_or_plan", u"state_word(no line)", u"direction_on_cause_item", u"prior is 0"])
    return [
        (lambda t, c, b: c is None, W_NOMAP),
        (lambda t, c, b: c["state"] == "GROUNDED", W_PASS),
        (lambda t, c, b: c["state"] == "VALUE_MISMATCH" and _first_ptr(c) is not None and t in MAIN_TYPES and b is not None and _first_ptr(b) is not None and _first_ptr(b) == _first_ptr(c), W_NAMED),
        (lambda t, c, b: c["state"] == "VALUE_MISMATCH" and _first_ptr(c) is not None and t in MAIN_TYPES, W_OTHERFACT),
        (lambda t, c, b: c["state"] == "VALUE_MISMATCH" and _first_ptr(c) is not None and t == "T3_ABSENT", W_NOBASE),
        (lambda t, c, b: rs(c) == ("POINTER_NOT_FOUND", u"no_same_value"), W_NOSAME),
        (lambda t, c, b: rs(c) == ("POINTER_NOT_FOUND", u"other_concept"), W_OTHERCON),
        (lambda t, c, b: c["state"] == "POINTER_NOT_FOUND" and c["reason"] is not None and re.match(r"^(no_element($|\()|no_prior_member_context$)", c["reason"]) is not None, W_NOELEM),
        (lambda t, c, b: c["state"] == "POINTER_NOT_FOUND" and c["reason"] is not None and re.match(r"^(no_pointer$|unresolved:)", c["reason"]) is not None, W_NOPTR),
        (lambda t, c, b: rs(c) == ("UNVERIFIABLE", u"no_subject"), W_NOSUBJ),
        (lambda t, c, b: c["state"] == "UNVERIFIABLE" and c["reason"] is not None and c["reason"].startswith(u"ambiguous("), W_AMBIG),
        (lambda t, c, b: c["state"] == "UNVERIFIABLE" and c["reason"] in hold, W_FRAME),
        (lambda t, c, b: True, W_OUT),
    ]


RULES = _rules()


def reword(typ, c, b):
    for cond, w in RULES:
        if cond(typ, c, b):
            return w
    raise AssertionError("到達しない")


PTR_RE = re.compile(r"^xbrl:(?P<el>(?P<pre>[^:@]*):?(?P<nm>[^@]*))@?(?P<ctx>.*)$")
PERIOD_RE = re.compile(r"^(CurrentYear|Prior1Year|Prior2Year)(Duration|Instant)")


def resplit(p):
    u"""先頭の pointer の字から (scheme, 要素名, 接頭辞, 期, member の分類, 標準の接頭辞か)。member の分類: なし / 単体 / それ以外。None なら None。"""
    if p is None:
        return None
    if not p.startswith("xbrl:"):
        return (p.split(":", 1)[0], u"(xbrl でない)", None, None, None, None)
    m = PTR_RE.match(p)
    ctx = m.group("ctx")
    pm = PERIOD_RE.match(ctx)
    tail = ctx[ctx.index("_") + 1:] if "_" in ctx else ""
    mem = u"なし" if "Member" not in tail else (u"単体" if tail == SOLE else u"それ以外")
    return (u"xbrl", m.group("el"), m.group("pre"), pm.group(0) if pm else u"その他", mem, re.fullmatch(r"jp[a-z]+_cor", m.group("pre")) is not None)


def cut_of(cell):
    u"""記録の 先頭の切り方 から resplit と同じ形の組へ。"""
    c = cell[u"先頭の切り方"]
    if c is None:
        return None
    if c[u"scheme"] != u"xbrl":
        return (c[u"scheme"], c[u"要素名"], c[u"接頭辞"], c[u"期"], None, c[u"標準の接頭辞"])
    mem = u"なし" if not c[u"member"] else (u"単体" if c[u"member が単体のみ"] else u"それ以外")
    return (u"xbrl", c[u"要素名"], c[u"接頭辞"], c[u"期"], mem, c[u"標準の接頭辞"])


def check_e(rec):
    u"""問題の列(空なら通す)。"""
    out = []
    for r in rec[u"rows"]:
        if list(r[u"profile"]) != list(P4):
            out.append(u"%s: profile の欄が %s でない" % (r["id"], list(P4)))
            continue
        for p in P4:
            c, b = after_claim(r, p), base_claim(r, p)
            x = nm(r, p)
            w = reword(r[u"型"], c, b)
            if w != x[u"語"]:
                out.append(u"%s %s: 語が求め直しと違う(%s != %s)" % (r["id"], p, x[u"語"], w))
            if x[u"語"] not in WORDS:
                out.append(u"%s %s: 語が 13 語に無い" % (r["id"], p))
            if x[u"止めた"] != (w in STOPPED):
                out.append(u"%s %s: 止めたの旗が語と合わない" % (r["id"], p))
            head = _first_ptr(c)
            if x[u"先頭の pointer"] != head:
                out.append(u"%s %s: 先頭の pointer が claim の pointers の先頭と違う" % (r["id"], p))
            same = head is not None and _first_ptr(b) is not None and head == _first_ptr(b)
            if x[u"先頭が同じ"] != same:
                out.append(u"%s %s: 先頭が同じ が求め直しと違う" % (r["id"], p))
            rc_same = bool(same and c.get("recomputed") is not None and b.get("recomputed") is not None and c["recomputed"] == b["recomputed"])
            if x[u"recomputed が同じ"] != rc_same:
                out.append(u"%s %s: recomputed が同じ が求め直しと違う" % (r["id"], p))
            if cut_of(x) != resplit(head):
                out.append(u"%s %s: 先頭の切り方が求め直しと違う" % (r["id"], p))
            if x[u"基準の state"] != (None if b is None else b["state"]) or x[u"基準が GROUNDED"] != (None if b is None else b["state"] == "GROUNDED"):
                out.append(u"%s %s: 基準の state の欄が違う" % (r["id"], p))
            if r[u"型"] != "T3_ABSENT" and x[u"届いた(文)"] != r[u"profile"][p][u"届いた(文)"]:
                out.append(u"%s %s: 届いた(文)の写しが違う" % (r["id"], p))
    return out


def named_counts(rec, p, rows=None):
    u"""名指しの 2 本を claim の欄から数える(記録の旗は読まない): (名指し(pointers), 名指し(pointers + recomputed), 別の fact)。T1・T2・T5。"""
    n1 = n2 = n3 = 0
    for r in (rows if rows is not None else mains(rec)):
        c, b = after_claim(r, p), base_claim(r, p)
        if c is None or c["state"] != "VALUE_MISMATCH" or _first_ptr(c) is None:
            continue
        if _first_ptr(b) is not None and _first_ptr(b) == _first_ptr(c):
            n1 += 1
            if c.get("recomputed") is not None and c.get("recomputed") == (b or {}).get("recomputed"):
                n2 += 1
        else:
            n3 += 1
    return n1, n2, n3


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
        f = by_id[r["id"]]
        if (r["doc"], r[u"型"], r[u"元の字"], r[u"後の字"], r[u"基準の claim"]) != (f["doc"], f[u"型"], f[u"元の字"], f[u"後の字"], f[u"基準の claim"]):
            out.append(u"%s: doc・型・元の字・後の字・基準の claim が fresh の行と違う" % r["id"])
    ty = collections.Counter(r[u"型"] for r in rec[u"rows"])
    if dict(ty) != fr[u"D"][u"型別の注入"] or len(rec[u"rows"]) != fr[u"D"][u"注入"]:
        out.append(u"型別の数が fresh の D と違う")
    if rec[u"配線の行ごと"] and [w["id"] for w in rec[u"配線の行ごと"]] != [r["id"] for r in rec[u"rows"]]:
        out.append(u"配線の行ごとの id が rows と違う")
    return out


def _g(c, k):
    return None if c is None else c.get(k)


def strip_keys(v, drop):
    if isinstance(v, dict):
        return dict((k, strip_keys(w, drop)) for k, w in v.items() if k not in drop)
    return v


def dumps(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


def w1_recount(rec, reach):
    u"""W-1 (ii) を門が自分で数え直す: P22・P26・P27 の欄が inject_reach の同じ id の行と、欄ごと・全欄で何行一致するか。"""
    rid = dict((r["id"], r) for r in reach[u"rows"])
    f = collections.Counter()
    missing = 0
    for r in rec[u"rows"]:
        o = rid.get(r["id"])
        if o is None:
            missing += 1
            continue
        ok = dict((k, True) for k in ("state", "reason", "pointers", "分類", "全欄"))
        for p in ("P22", "P26", "P27"):
            x, y = r[u"profile"][p], o[u"profile"][p]
            ax, ay = after_claim(r, p), after_claim(o, p)
            ok["state"] &= _g(ax, "state") == _g(ay, "state")
            ok["reason"] &= _g(ax, "reason") == _g(ay, "reason")
            ok["pointers"] &= _g(ax, "pointers") == _g(ay, "pointers")
            ok[u"分類"] &= x[u"分類"] == y[u"分類"]
            ok[u"全欄"] &= dumps(strip_keys(x, (u"recomputed", u"名指し"))) == dumps(y)
        for k, v in ok.items():
            f[k] += int(v)
    return {"rows": len(rec[u"rows"]), "missing": missing, "state": f["state"], "reason": f["reason"], "pointers": f["pointers"], "分類": f[u"分類"], "全欄": f[u"全欄"]}


def w2_recount(rec, reg):
    u"""W-2 を門が自分で数え直す: (一致した書類 × profile の数, 書類 × profile の数, 動いた行の集合が同じか, 動いた行の数, 全部 PNF/no_same_value → VALUE_MISMATCH/None か)。"""
    regd = dict((x["docID"], x) for x in reg[u"書類"])
    ok = n = 0
    for d in rec[u"書類(出てくる順)"]:
        for p in P4:
            n += 1
            got = rec[u"書類ごと"][d][u"無改変の 4 state"][p]
            want = regd[d][u"4 state"][p]
            ok += int(all(got[k] == want.get(k, 0) for k in STATES4))
    docs = set(rec[u"書類(出てくる順)"])
    mine = sorted((m["doc"], m["id"], tuple(m[u"前"]), tuple(m[u"後"])) for m in rec[u"P27 → P27E で動いた無改変の行"])
    theirs = sorted((x["docID"], x["id"], (x[u"前"]["state"], x[u"前"]["reason"]), (x[u"後"]["state"], x[u"後"]["reason"]))
                    for x in reg[u"動いた行"][u"新しい標本 30"][u"P27 → P27E"] if x["docID"] in docs)
    shape = all(m[2] == ("POINTER_NOT_FOUND", "no_same_value") and m[3] == ("VALUE_MISMATCH", None) for m in mine)
    return ok, n, mine == theirs, len(mine), shape


def w3_recount(rec):
    k = s = c_n = c_ok = 0
    for r in rec[u"rows"]:
        k += int(list(r[u"profile"]) == list(P4))
        s += int("P27E" in r[u"結果(P22〜P27)"])
        cl = [after_claim(r, p) for p in P4] + [base_claim(r, p) for p in P4]
        cl = [c for c in cl if c is not None]
        c_n += len(cl)
        c_ok += sum(1 for c in cl if "recomputed" in c)
    return k, s, len(rec[u"rows"]), c_ok, c_n


def check_b(rec, fr, fetched, reach, reg):
    out = []
    g = rec[u"配線の門"]
    n = len(fr[u"注入の行"])
    if not rec[u"全書類"]:
        out.append(u"全書類の記録でない(試走の記録)")
    if not g[u"通った"]:
        out.append(u"配線の門の旗が偽")
    w1 = g[u"W-1"]
    if not (w1[u"前の便の門(4 欄とも一致)"] == [n, n] == [len(rec[u"配線の行ごと"])] * 2 and w1[u"id の集合が記録と同じ"] and w1[u"注入の件数の組"] == [4 * len(fetched[u"使う書類"])] * 2):
        out.append(u"W-1 (i) が 741 / 741・120 / 120 でない")
    for w in rec[u"配線の行ごと"]:
        f = w[u"一致"]
        if not all(f[k] for k in (u"記録に同じ id の行が在る", u"元の字", u"後の字", u"基準の claim", u"結果(P22〜P26)", u"4 欄とも一致")):
            out.append(u"%s: 4 欄のどれかが一致していない" % w["id"])
    c = w1_recount(rec, reach)
    if not (c["rows"] == n and c["missing"] == 0 and all(c[k] == n for k in ("state", "reason", "pointers", "分類", "全欄"))):
        out.append(u"W-1 (ii) を門が数え直すと 741 / 741 でない: %s" % c)
    for k, key in (("state", u"P22・P26・P27 の state"), ("reason", u"P22・P26・P27 の reason"), ("pointers", u"P22・P26・P27 の pointers"),
                   (u"分類", u"P22・P26・P27 の分類(6 語)"), (u"全欄", u"P22・P26・P27 の全欄(recomputed と 名指し を除く)")):
        if w1[key] != c[k]:
            out.append(u"W-1 (ii) の記録の数『%s』が門の数え直しと違う" % key)
    ok, tot, same, nmoved, shape = w2_recount(rec, reg)
    if not (ok == tot == 4 * len(fetched[u"使う書類"]) and same and nmoved == len(reg[u"動いた行"][u"新しい標本 30"][u"P27 → P27E"]) and shape):
        out.append(u"W-2 を門が数え直すと 30 書類 × 4 profile・24 行でない: %s" % ((ok, tot, same, nmoved, shape),))
    k, s, t, c_ok, c_n = w3_recount(rec)
    if not (k == s == t == n and c_ok == c_n and c_n > 0):
        out.append(u"W-3 を門が数え直すと通らない: %s" % ((k, s, t, c_ok, c_n),))
    if g[u"W-3"][u"claim に recomputed の鍵"] != [c_ok, c_n]:
        out.append(u"W-3 の記録の数が門の数え直しと違う")
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
        if not (d[u"材料の sha256 が取得の記録と一致"] and d[u"材料の sha256"] == used[doc]["sha256"]):
            out.append(u"%s: 材料の sha256 が取得の記録と違う" % doc)
    cc = rec[u"cache"]
    if cc[u"開始"] != cc[u"終了"] or cc[u"開始"][u"edinet"] != 281 or cc[u"開始"][u"edinet-fresh-2026-10-21"] != 40:
        out.append(u"cache の件数が 281 / 40 のまま動いていない")
    if rec[u"key_leaks"] != []:
        out.append(u"key_leaks が空でない")
    return out


def check_j(rec):
    out = []
    got = rec[u"読んだ入力の sha256"]
    if sorted(got) != sorted([FRESH_REL, FETCHED_REL, REACH_REL, REGRESS_REL]):
        out.append(u"読んだ入力の sha256 の file が 4 つでない")
    for rel in (FRESH_REL, FETCHED_REL, REACH_REL, REGRESS_REL):
        if got.get(rel) != sha64(rel):
            out.append(u"%s の sha256 が記録の写しと違う(読み直しの元が動いた)" % rel)
    return out


# ----------------------------------------------------------------------------------------------------------------
# (d) SR-1〜SR-17 の当否を記録から求める(幅は封の表の字から読む)
BOLD = re.compile(r"\*\*(.+?)\*\*")
RANGE_RE = re.compile(r"^(\d+(?:\.\d+)?)%? 以上 (\d+(?:\.\d+)?)%? 以下$")


def seal_predictions(seal):
    u"""封 §3 の表の行 {名前: (欄, 予測, 外れ方)}(封の字のまま)。"""
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(SR-\d+)\*\* \| (.*) \|$", l)
        if m:
            cells = m.group(2).split(u" | ")
            assert len(cells) == 3, l
            out[m.group(1)] = tuple(c.strip() for c in cells)
    return out


def ranges_of(cell):
    return [(float(m.group(1)), float(m.group(2))) for m in (RANGE_RE.match(b) for b in BOLD.findall(cell)) if m]


def singles_of(cell):
    return [b for b in BOLD.findall(cell) if not RANGE_RE.match(b) and not re.match(r"^\d+(?:\.\d+)?% 以上$", b)]


def pcts_of(cell):
    return [float(m.group(1)) for m in (re.match(r"^(\d+(?:\.\d+)?)% 以上$", b) for b in BOLD.findall(cell)) if m]


def within(n, rg):
    return rg[0] <= n <= rg[1]


def pct_within(n, d, rg):
    return d > 0 and rg[0] * d <= 100.0 * n <= rg[1] * d


def hit_word(b):
    return u"**判定しない**" if b is None else (u"**当たり**" if b else u"**外れ**")


def named_rows(rec, p, w=W_NAMED):
    return [r for r in mains(rec) if word(r, p) == w]


def judge(rec, inp, seal):
    u"""{名前: (実測の字, 当たりか(True / False / None=判定しない))}。封 §3 の予測を記録から。幅は封の字から読む。"""
    SP = seal_predictions(seal)
    out = collections.OrderedDict()
    M = mains(rec)
    ALL = rec[u"rows"]
    T3 = of_type(rec, "T3_ABSENT")

    # SR-1
    w1 = w1_recount(rec, inp["reach"])
    n = len(ALL)
    sg = singles_of(SP["SR-1"][1])
    a, b = [int(x) for x in sg[0].split(u" / ")]
    pairs = int(re.search(r"(\d+) 組", SP["SR-1"][1]).group(1))
    g1 = rec[u"配線の門"][u"W-1"]
    hit = (g1[u"前の便の門(4 欄とも一致)"] == [a, b] and g1[u"注入の件数の組"][0] == pairs == g1[u"注入の件数の組"][1] and g1[u"id の集合が記録と同じ"]
           and all(w1[k] == a == b == n for k in ("state", "reason", "pointers", "分類", "全欄")) and sg[1] == sg[0])
    out["SR-1"] = (u"W-1 (i) %s・注入の件数の組 %s、(ii) 欄ごと state %s・reason %s・pointers %s・分類 %s、全欄 %s" % (
        n_of(*g1[u"前の便の門(4 欄とも一致)"]), n_of(*g1[u"注入の件数の組"]), n_of(w1["state"], n), n_of(w1["reason"], n), n_of(w1["pointers"], n), n_of(w1[u"分類"], n), n_of(w1[u"全欄"], n)), hit)
    # SR-2
    ok, tot, same, nmoved, shape = w2_recount(rec, inp["reg"])
    sg = singles_of(SP["SR-2"][1])
    a, b = [int(x) for x in sg[0].split(u" / ")]
    nd = len(rec[u"書類(出てくる順)"])
    regd = dict((x["docID"], x) for x in inp["reg"][u"書類"])
    docs_ok = sum(1 for d in rec[u"書類(出てくる順)"] if all(rec[u"書類ごと"][d][u"無改変の 4 state"][p] == dict((k, regd[d][u"4 state"][p].get(k, 0)) for k in STATES4) for p in P4))
    out["SR-2"] = (u"無改変の 4 state: %s 書類(各 4 profile 一致)、動いた行 %d(集合が regress97 と同じ: %s。前後の形が 24 行とも同じ: %s)" % (n_of(docs_ok, nd), nmoved, yesno(same), yesno(shape)),
                   docs_ok == a == b == nd and ok == tot == 4 * nd and same and shape and nmoved == int(sg[1]))
    # SR-3
    rgs = ranges_of(SP["SR-3"][1])
    cnt = [sum(1 for r in of_type(rec, t) if word(r, "P27") == W_NAMED) for t in MAIN_TYPES]
    out["SR-3"] = (u"P27 の(名指した・原本): T1 %d・T2 %d・T5 %d" % tuple(cnt), all(within(c, rg) for c, rg in zip(cnt, rgs)))
    # SR-4
    rg = ranges_of(SP["SR-4"][1])[0]
    n4 = sum(1 for r in M if word(r, "P27") == W_OTHERFACT)
    out["SR-4"] = (u"P27 の(名指した・別の fact)(T1・T2・T5): %d" % n4, within(n4, rg))
    # SR-5
    rgs = ranges_of(SP["SR-5"][1])
    t5_22 = sum(1 for r in of_type(rec, "T5_COINCIDENT") if word(r, "P22") == W_NAMED)
    d5 = len(named_rows(rec, "P22")) - len(named_rows(rec, "P27"))
    out["SR-5"] = (u"P22 の T5 の(名指した・原本): %d、P22 − P27 の(名指した・原本)(T1・T2・T5): %d" % (t5_22, d5), within(t5_22, rgs[0]) and within(d5, rgs[1]))
    # SR-6
    rg = ranges_of(SP["SR-6"][1])[0]
    diffs = []
    for p in P4:
        n1, n2, _n3 = named_counts(rec, p)
        diffs.append(n1 - n2)
    out["SR-6"] = (u"名指し(pointers) − 名指し(pointers + recomputed): " + u"・".join(u"%s %d" % (p, d) for p, d in zip(P4, diffs)), all(within(d, rg) for d in diffs))
    # SR-7
    sg = singles_of(SP["SR-7"][1])
    want_pass, want_nomap = int(sg[0]), int(sg[1])
    pe = [r for r in ALL if word(r, "P27E") == W_PASS]
    p27 = [r for r in ALL if word(r, "P27") == W_PASS]
    nomap = sum(1 for r in ALL if word(r, "P27E") == W_NOMAP)
    out["SR-7"] = (u"P27E の(通した)%d(P27 の通した行と同じ id: %s)、(対応が付かない)%d" % (len(pe), yesno([r["id"] for r in pe] == [r["id"] for r in p27]), nomap),
                   len(pe) == want_pass and [r["id"] for r in pe] == [r["id"] for r in p27] and nomap == want_nomap)
    # SR-8
    rgs = ranges_of(SP["SR-8"][1])
    ch = [r for r in ALL if word(r, "P27") != word(r, "P27E")]
    bt = collections.Counter(r[u"型"] for r in ch)
    shape8 = all(word(r, "P27") == W_NOSAME and word(r, "P27E") in NAMED3 for r in ch)
    ok8 = within(len(ch), rgs[0]) and within(bt["T5_COINCIDENT"], rgs[1]) and within(bt["T1_VALUE"], rgs[2]) and within(bt["T2_UNIT"], rgs[3]) and within(bt["T3_ABSENT"], rgs[4]) and shape8
    out["SR-8"] = (u"P27 → P27E で語が変わった行 %d(T5 %d・T1 %d・T2 %d・T3 %d)。前が(要確認・証拠が無く名指さない)で後が語 3・4・5: %s" % (
        len(ch), bt["T5_COINCIDENT"], bt["T1_VALUE"], bt["T2_UNIT"], bt["T3_ABSENT"], yesno(shape8)), ok8)
    # SR-9
    rg = ranges_of(SP["SR-9"][1])[0]
    lo = pcts_of(SP["SR-9"][1])[0]
    diff9 = len(named_rows(rec, "P27E")) - len(named_rows(rec, "P27"))
    chm = [r for r in ch if r[u"型"] in MAIN_TYPES]
    nn = sum(1 for r in chm if word(r, "P27E") == W_NAMED)
    share_ok = True if not chm else nn * 100 >= lo * len(chm)
    out["SR-9"] = (u"P27E の(名指した・原本) − P27: %d。変わった T1・T2・T5 の行のうち(名指した・原本): %s" % (diff9, rate(nn, len(chm)) if chm else u"変わった行 0(判定しない)"), within(diff9, rg) and share_ok)
    # SR-10
    rg = ranges_of(SP["SR-10"][1])[0]
    hold = [r for r in ALL if word(r, "P27E") in (W_NOSAME, W_OTHERCON, W_NOELEM, W_NOPTR, W_NOSUBJ, W_AMBIG, W_FRAME)
            or (word(r, "P27E") == W_OUT and after_claim(r, "P27E")["state"] in ("POINTER_NOT_FOUND", "UNVERIFIABLE"))]
    out["SR-10"] = (u"P27E の要確認(741 行): %d" % len(hold), within(len(hold), rg))
    # SR-11
    rg = ranges_of(SP["SR-11"][1])[0]
    nr = named_rows(rec, "P27")
    top = collections.Counter(nm(r, "P27")[u"先頭の切り方"][u"要素名"] for r in nr).most_common(1)
    topn = top[0][1] if top else 0
    out["SR-11"] = (u"P27 の(名指した・原本)の先頭の要素名の上位 1 つ: %s" % rate(topn, len(nr)), pct_within(topn, len(nr), rg))
    # SR-12
    lo = pcts_of(SP["SR-12"][1])[0]
    rg = ranges_of(SP["SR-12"][1])[0]
    std = sum(1 for r in nr if nm(r, "P27")[u"先頭の切り方"][u"標準の接頭辞"])
    jp = sum(1 for r in nr if nm(r, "P27")[u"先頭の切り方"][u"接頭辞"] == "jppfs_cor")
    out["SR-12"] = (u"P27 の(名指した・原本)の先頭: 標準の接頭辞 %s・jppfs_cor %s" % (rate(std, len(nr)), rate(jp, len(nr))), len(nr) > 0 and std * 100 >= lo * len(nr) and pct_within(jp, len(nr), rg))
    # SR-13
    lo = pcts_of(SP["SR-13"][1])[0]
    rg = ranges_of(SP["SR-13"][1])[0]
    cur = sum(1 for r in nr if nm(r, "P27")[u"先頭の切り方"][u"期"] in ("CurrentYearDuration", "CurrentYearInstant"))
    mem = sum(1 for r in nr if nm(r, "P27")[u"先頭の切り方"][u"member"])
    out["SR-13"] = (u"P27 の(名指した・原本)の先頭: CurrentYear %s・member あり %s" % (rate(cur, len(nr)), rate(mem, len(nr))), len(nr) > 0 and cur * 100 >= lo * len(nr) and pct_within(mem, len(nr), rg))
    # SR-14
    rgs = ranges_of(SP["SR-14"][1])
    sg = singles_of(SP["SR-14"][1])
    c3 = collections.Counter(word(r, "P27") for r in T3)
    ok14 = (within(c3[W_NOELEM], rgs[0]) and within(c3[W_NOSAME], rgs[1]) and within(c3[W_NOSUBJ], rgs[2]) and within(c3[W_AMBIG], rgs[3])
            and c3[W_NOMAP] == int(sg[0]) and c3[W_PASS] == int(sg[1]) and c3[W_NOBASE] == int(sg[1]))
    out["SR-14"] = (u"P27 の T3(%d 行): 要素が無い %d・証拠が無く名指さない %d・主語が無い %d・候補が複数 %d・対応が付かない %d・通した %d・名指した・基準なし %d" % (
        len(T3), c3[W_NOELEM], c3[W_NOSAME], c3[W_NOSUBJ], c3[W_AMBIG], c3[W_NOMAP], c3[W_PASS], c3[W_NOBASE]), ok14)
    # SR-15
    want = int(singles_of(SP["SR-15"][1])[0])
    c15 = dict((p, (sum(1 for r in ALL if word(r, p) == W_OUT), sum(1 for r in ALL if word(r, p) == W_NOPTR))) for p in P4)
    out["SR-15"] = (u"(形の外)/(要確認・pointer が引けない): " + u"・".join(u"%s %d/%d" % (p, c15[p][0], c15[p][1]) for p in P4), all(a == want and b == want for a, b in c15.values()))
    # SR-16
    sg = singles_of(SP["SR-16"][1])
    z, t3n = int(sg[0]), int(sg[1])
    a16 = sum(1 for r in ALL if word(r, "P22") in (W_NOSAME, W_OTHERCON))
    b16 = sum(1 for r in T3 if word(r, "P22") == W_NOBASE)
    out["SR-16"] = (u"P22 の(要確認・証拠が無く名指さない)+(要確認・別の概念)%d、T3 の(名指した・基準なし)%d" % (a16, b16), a16 == z and b16 == t3n)
    # SR-17
    lo = pcts_of(SP["SR-17"][1])[0]
    s17 = sum(1 for r in M if word(r, "P26") == word(r, "P27"))
    out["SR-17"] = (u"P26 と P27 で語が同じ(T1・T2・T5): %s" % rate(s17, len(M)), s17 * 100 >= lo * len(M))
    return out


# ----------------------------------------------------------------------------------------------------------------
# (c) 文書の表
def ctx_cat(cell):
    c = cell[u"先頭の切り方"]
    if c is None or c[u"scheme"] != u"xbrl":
        return None
    return (c[u"期"], u"なし" if not c[u"member"] else (u"単体(NonConsolidatedMember)" if c[u"member が単体のみ"] else u"それ以外の member"))


def eval_block(ev):
    a = ev[u"集計(4 profile の全部で対応が付く行が分母。V-1〜V-3)"]
    rows = []
    for t in ("T8_REL", "T1_VALUE"):
        for p in ("P26", "P27", "P27E"):
            x = a[t][p][u"全体"]
            nm_ = x[u"名指して原本の値を返した"]
            ot = x[u"名指したが別の値"]
            pnf, unv = x[u"止めたが名指さない(POINTER_NOT_FOUND)"], x[u"止めたが名指さない(UNVERIFIABLE)"]
            rows.append([t, p, str(x[u"対応が付く"]), rate(nm_[u"件"], nm_[u"分母"]), rate(ot[u"件"], ot[u"分母"]), rate(pnf[u"件"] + unv[u"件"], pnf[u"分母"])])
    return table([u"型(評価用 10 社)", u"profile", u"4 profile の全部で対応が付く行", u"名指して原本の値を返した", u"名指したが別の値", u"止めたが名指さない"], rows)


def render_blocks(rec, inp, seal):
    B = collections.OrderedDict()
    pos = positions(rec)
    order = rec[u"書類(出てくる順)"]
    J = judge(rec, inp, seal)
    SP = seal_predictions(seal)
    assert list(SP) == list(J), list(SP)
    B["pred"] = table([u"#", u"欄", u"予測(封の字)", u"外れ方(封の字)", u"実測(記録から)", u"当たり外れ"],
                      [[u"**%s**" % k, SP[k][0], SP[k][1], SP[k][2], J[k][0], hit_word(J[k][1])] for k in J])
    # 配線
    g = rec[u"配線の門"]
    w1, w2, w3 = g[u"W-1"], g[u"W-2"], g[u"W-3"]
    B["wiring"] = table([u"配線の門", u"値"], [
        [u"W-1 (i) 前の便の門(4 欄とも一致した行 / 作り直した行)", n_of(*w1[u"前の便の門(4 欄とも一致)"])],
        [u"W-1 (i) id の集合が記録と同じ", yesno(w1[u"id の集合が記録と同じ"])],
        [u"W-1 (i) 注入の件数の組(書類 × 型 / 3 つの数が一致)", n_of(*w1[u"注入の件数の組"])],
        [u"W-1 (ii) P22・P26・P27 の state が inject_reach と同じ行", n_of(w1[u"P22・P26・P27 の state"], w1[u"行"])],
        [u"W-1 (ii) 同 reason", n_of(w1[u"P22・P26・P27 の reason"], w1[u"行"])],
        [u"W-1 (ii) 同 pointers", n_of(w1[u"P22・P26・P27 の pointers"], w1[u"行"])],
        [u"W-1 (ii) 同 分類(6 語)", n_of(w1[u"P22・P26・P27 の分類(6 語)"], w1[u"行"])],
        [u"W-1 (ii) 同 全欄(recomputed と 名指し を除く)", n_of(w1[u"P22・P26・P27 の全欄(recomputed と 名指し を除く)"], w1[u"行"])],
        [u"W-2 無改変の 4 state が regress97 と同じ書類(各 4 profile)", n_of(*w2[u"書類の 4 state が regress97 と一致"])],
        [u"W-2 P27 → P27E で動いた無改変の行(今回 / regress97)", u"%d / %d" % (w2[u"動いた行(今回)"], w2[u"動いた行(regress97。対象の書類)"])],
        [u"W-2 動いた行の集合が同じ", yesno(w2[u"動いた行の集合が同じ"])],
        [u"W-3 profile の鍵が 4 つの順", n_of(*w3[u"profile の鍵が 4 つの順"])],
        [u"W-3 結果(P22〜P27)に P27E", n_of(*w3[u"結果(P22〜P27)に P27E"])],
        [u"W-3 claim に recomputed の鍵", n_of(*w3[u"claim に recomputed の鍵"])],
        [u"全書類の記録", yesno(rec[u"全書類"])]])
    eng = rec[u"engine sha16"]
    B["engine"] = table([u"項目", u"値"], [[u"`%s` の sha16" % k, u"`%s`" % v] for k, v in eng.items()] + [
        [u"DEFAULT_PROFILE", rec[u"DEFAULT_PROFILE"]], [u"測った木の HEAD", u"`%s`" % rec[u"HEAD"]], [u"封の commit", u"`%s`" % rec[u"封"][u"commit"]],
        [u"cache `edinet/`(開始 → 終了)", u"%d → %d" % (rec[u"cache"][u"開始"][u"edinet"], rec[u"cache"][u"終了"][u"edinet"])],
        [u"cache `edinet-fresh-2026-10-21/`(開始 → 終了)", u"%d → %d" % (rec[u"cache"][u"開始"][u"edinet-fresh-2026-10-21"], rec[u"cache"][u"終了"][u"edinet-fresh-2026-10-21"])],
        [u"key_leaks", str(len(rec[u"key_leaks"]))]])
    crow = []
    for t in ALL_TYPES:
        s = collections.Counter()
        for d in order:
            c = rec[u"書類ごと"][d][u"注入の件数"][t]
            for k in (u"作れる site", u"採った", u"注入の行になった", u"基準に対応が付かない", u"基準が GROUNDED でない"):
                s[k] += c[k]
        crow.append([TSHORT[t]] + [str(s[k]) for k in (u"作れる site", u"採った", u"注入の行になった", u"基準に対応が付かない", u"基準が GROUNDED でない")])
    B["counts"] = table([u"型", u"作れる site", u"採った", u"注入の行になった", u"基準に対応が付かない", u"基準が GROUNDED でない"], crow)
    # 無改変の 4 state の合計
    prow = []
    for p in P4:
        s = collections.Counter()
        for d in order:
            for k in STATES4:
                s[k] += rec[u"書類ごと"][d][u"無改変の 4 state"][p][k]
        prow.append([p, str(sum(s.values()))] + [str(s[k]) for k in STATES4])
    mv = rec[u"P27 → P27E で動いた無改変の行"]
    prow.append([u"P27 → P27E で動いた行", str(len(mv)), u"―", u"―", u"―", u"―"])
    B["plain4"] = table([u"profile(無改変の 30 書類)", u"claim", u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND"], prow)
    # reasons: profile × 型 × (state, reason)
    rr = []
    for p in P4:
        for t in ALL_TYPES:
            c = collections.Counter()
            for r in of_type(rec, t):
                a = after_claim(r, p)
                c[(u"(対応が付かない)", u"―") if a is None else (a["state"], u"(なし)" if a["reason"] is None else a["reason"])] += 1
            for (s_, rs_), n in sorted(c.items()):
                rr.append([p, TSHORT[t], s_, rs_, str(n)])
    B["reasons"] = table([u"profile", u"型", u"state", u"reason", u"行"], rr)
    # cls
    clr = []
    for p in P4:
        for name, rs in groups(rec):
            c = collections.Counter(word(r, p) for r in rs)
            clr.append([p, name, str(len(rs))] + [str(c[w]) for w in WORDS])
    B["cls"] = table([u"profile", u"型", u"行"] + list(WORDS), clr)
    # named
    nr = []
    for p in P4:
        for name, rs in groups(rec):
            c = collections.Counter(word(r, p) for r in rs)
            stop = sum(c[w] for w in STOPPED)
            named = c[W_NAMED]
            both = sum(1 for r in rs if word(r, p) == W_NAMED and nm(r, p)[u"recomputed が同じ"])
            reach = sum(1 for r in rs if nm(r, p)[u"届いた(文)"]) if name != u"T3" else None
            row = [p, name, str(len(rs)), str(stop), u"―" if reach is None else str(reach), str(named), str(both), str(named - both), str(c[W_OTHERFACT]), str(c[W_NOBASE])]
            row += [u"―", u"―"] if name == u"T3" else [rate(named, stop), rate(named, reach)]
            nr.append(row)
    B["named"] = table([u"profile", u"型", u"行", u"止めた(語 3〜13)", u"届いた(文)", u"名指した・原本(pointers)", u"うち recomputed も同じ(pointers + recomputed)", u"先頭は同じで recomputed が違う",
                        u"名指した・別の fact", u"名指した・基準なし", u"名指しの率(分母 = 止めた)", u"名指しの率(分母 = 届いた(文))"], nr)
    # forms: 名指した・原本の行を、recomputed が同じか違うかと、基準・注入後の form で分ける
    fr_ = []
    for p in P4:
        c = collections.Counter()
        for r in mains(rec):
            if word(r, p) == W_NAMED:
                c[(TSHORT[r[u"型"]], u"同じ" if nm(r, p)[u"recomputed が同じ"] else u"違う", base_claim(r, p)["form"], after_claim(r, p)["form"])] += 1
        for k, n in sorted(c.items()):
            fr_.append([p] + list(k) + [str(n)])
    B["forms"] = table([u"profile", u"型", u"recomputed(名指した・原本の行)", u"基準の form", u"注入後の form", u"行"], fr_)
    # p27e
    chg = collections.Counter()
    for r in rec[u"rows"]:
        a, b = word(r, "P27"), word(r, "P27E")
        chg[(r[u"型"], u"(変わらない)", u"(変わらない)") if a == b else (r[u"型"], a, b)] += 1
    B["p27e"] = table([u"型", u"P27 の語", u"P27E の語", u"行"], [[TSHORT[k[0]], k[1], k[2], str(n)] for k, n in sorted(chg.items(), key=lambda kv: (ALL_TYPES.index(kv[0][0]), kv[0][1], kv[0][2]))])
    # elements / prefix / context
    erow = []
    for p in ("P22", "P27", "P27E"):
        rs = named_rows(rec, p)
        cnt, filer = collections.Counter(), 0
        for r in rs:
            c = nm(r, p)[u"先頭の切り方"]
            if c[u"標準の接頭辞"]:
                cnt[c[u"要素名"]] += 1
            else:
                filer += 1
        for i, (k, n) in enumerate(sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[:10]):
            erow.append([p, str(i + 1), k, str(n)])
        erow.append([p, u"―", FILER, str(filer)])
        erow.append([p, u"―", u"(名指した・原本の計)", str(len(rs))])
    B["elements"] = table([u"profile", u"順位(標準の接頭辞の要素)", u"要素名", u"行"], erow)
    cols = [(w, p) for w in (W_NAMED, W_OTHERFACT) for p in P4]
    heads = [u"%s %s" % (p, u"原本" if w == W_NAMED else u"別の fact") for w, p in cols]

    def row_set(rs_by):
        return [str(sum(1 for r in mains(rec) if word(r, p) == w and rs_by(nm(r, p)[u"先頭の切り方"]))) for w, p in cols]
    pre_names = sorted(set(nm(r, p)[u"先頭の切り方"][u"接頭辞"] for r in mains(rec) for p in P4 if word(r, p) in (W_NAMED, W_OTHERFACT) and nm(r, p)[u"先頭の切り方"][u"標準の接頭辞"]))
    prow2 = [[n_] + row_set(lambda c, n_=n_: c[u"標準の接頭辞"] and c[u"接頭辞"] == n_) for n_ in pre_names]
    prow2.append([FILER_PREFIX] + row_set(lambda c: c[u"標準の接頭辞"] is False))
    B["prefix"] = table([u"接頭辞"] + heads, prow2)
    mcats = [u"なし", u"単体(NonConsolidatedMember)", u"それ以外の member"]
    xrow = []
    for per in PERIODS:
        for mc in mcats:
            xrow.append([per, mc] + row_set(lambda c, per=per, mc=mc: (c[u"期"], u"なし" if not c[u"member"] else (u"単体(NonConsolidatedMember)" if c[u"member が単体のみ"] else u"それ以外の member")) == (per, mc)))
    B["context"] = table([u"期", u"member"] + heads, xrow)
    # basestate
    brow = []
    for p in P4:
        for t in MAIN_TYPES:
            rs = of_type(rec, t)
            nob = sum(1 for r in rs if base_claim(r, p) is None)
            bad = [r for r in rs if base_claim(r, p) is not None and base_claim(r, p)["state"] != "GROUNDED"]
            wc = collections.Counter(word(r, p) for r in bad)
            brow.append([p, TSHORT[t], str(len(rs)), str(nob), str(len(bad)), u"・".join(u"%s %d" % (w, wc[w]) for w in WORDS if wc[w]) or u"―"])
    B["basestate"] = table([u"profile", u"型", u"行", u"記録の基準の id が一覧に無い", u"基準が無改変から GROUNDED でない", u"その行の語(P27E を含む各 profile の語)"], brow)
    B["eval"] = eval_block(inp["eval"])
    # examples
    ex = []
    for w in WORDS:
        k = 0
        for r in rec[u"rows"]:
            if word(r, "P27") == w and k < 3:
                k += 1
                ex.append([w, plabel(pos[r["id"]]), edit_of(r), word(r, "P27"), word(r, "P27E")])
        if k == 0:
            ex.append([w, u"(P27 でこの語の行は無い)", u"―", u"―", u"―"])
    k = 0
    for r in rec[u"rows"]:
        if word(r, "P27") != word(r, "P27E") and k < 3:
            k += 1
            ex.append([u"(P27 → P27E で変わった行)", plabel(pos[r["id"]]), edit_of(r), word(r, "P27"), word(r, "P27E")])
    B["examples"] = table([u"語(P27)", u"位置", u"元の字 → 後の字", u"P27 の語", u"P27E の語"], ex)
    xr = []
    k = 0
    for r in mains(rec):
        if word(r, "P27") == W_NAMED and not nm(r, "P27")[u"recomputed が同じ"] and k < 3:
            k += 1
            b, a = base_claim(r, "P27"), after_claim(r, "P27")
            xr.append([plabel(pos[r["id"]]), edit_of(r), u"%s / %s" % (b["form"], b["unit"]), u"%s / %s" % (a["form"], a["unit"]), str(b["recomputed"]), str(a["recomputed"])])
    B["examples_recomputed"] = table([u"位置(P27。先頭は同じで recomputed が違う行)", u"元の字 → 後の字", u"基準の form / unit", u"注入後の form / unit", u"基準の recomputed", u"注入後の recomputed"], xr)
    xo = []
    k = 0
    for r in mains(rec):
        if word(r, "P27") == W_OTHERFACT and k < 3:
            k += 1
            b, a = base_claim(r, "P27"), after_claim(r, "P27")
            bc, ac = resplit(_first_ptr(b)), resplit(_first_ptr(a))
            xo.append([plabel(pos[r["id"]]), edit_of(r), u"%s・%s" % (bc[3], bc[4]), u"%s・%s" % (ac[3], ac[4]), b["form"], a["form"]])
    B["examples_otherfact"] = table([u"位置(P27。名指した・別の fact の行)", u"元の字 → 後の字", u"基準の先頭の期・member", u"注入後の先頭の期・member", u"基準の form", u"注入後の form"], xo)
    order_of_doc = ("pred", "wiring", "counts", "engine", "plain4", "reasons", "cls", "named", "forms", "p27e", "elements", "prefix", "context", "basestate", "examples", "examples_recomputed", "examples_otherfact", "eval")
    assert sorted(order_of_doc) == sorted(B), sorted(set(B) ^ set(order_of_doc))
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
    for lit in (u"記録は不変", u"配線の数", u"engine が止めた", u"仮説。測るまで断定しない", u"測っていない", u"診断だけ", NOT_GATED, u"edinetdb-p27", u"良し悪し"):
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
    u"""記録のどこかの claim の pointers に出る、標準でない接頭辞の字の集合(文書に書いてはいけない字)。"""
    out = set()
    for r in rec[u"rows"]:
        for p in P4:
            x = r[u"profile"][p]
            cl = [x.get(u"claim")] if r[u"型"] == "T3_ABSENT" else [x[u"無改変"][u"claim"], x[u"注入後"][u"claim"]]
            for c in cl:
                for ptr in (c or {}).get("pointers") or []:
                    m = FILER_PTR.match(ptr)
                    if m and not re.fullmatch(r"jp[a-z]+_cor", m.group(1)):
                        out.add(m.group(1))
    return out


def check_h(seal, doc, fetched, rec=None):
    out = []
    docs = list(fetched[u"使う書類"])
    cids, fprefs = set(), set()
    if rec is not None:
        fprefs = filer_prefixes(rec)
        for r in rec[u"rows"]:
            if r[u"基準の claim"]:
                cids.add(r[u"基準の claim"])
            for p in P4:
                for c in (after_claim(r, p), base_claim(r, p)):
                    if c:
                        cids.add(c[u"id"])
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
        self.dir = tempfile.mkdtemp(prefix="stopreason_", dir=base)
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
        fr[u"注入の行"][3][u"後の字"] = u"X"
        self.assertNotEqual(check_a(self.rec, fr), [])

    def test_b_1_the_wiring_gates_pass_and_the_gate_recounts_them(self):
        self.assertEqual(check_b(self.rec, self.inp["fr"], self.inp["fetched"], self.inp["reach"], self.inp["reg"]), [])

    def test_b_2_the_record_is_the_full_run_and_has_no_leak(self):
        self.assertTrue(self.rec[u"全書類"])
        self.assertEqual(self.rec[u"key_leaks"], [])
        self.assertEqual(self.rec[u"cache"][u"開始"], self.rec[u"cache"][u"終了"])

    def test_b_3_w2_is_recounted_from_regress97_not_from_the_record_flags(self):
        ok, tot, same, nmoved, shape = w2_recount(self.rec, self.inp["reg"])
        self.assertEqual((ok, tot), (4 * len(self.inp["fetched"][u"使う書類"]),) * 2)
        self.assertEqual(nmoved, len(self.inp["reg"][u"動いた行"][u"新しい標本 30"][u"P27 → P27E"]))
        self.assertTrue(same and shape)

    def test_e_1_the_words_and_the_cuts_are_recomputed_from_the_claim_fields(self):
        self.assertEqual(check_e(self.rec), [])

    def test_e_2_every_row_has_the_four_profiles_and_the_known_fields(self):
        for r in self.rec[u"rows"]:
            self.assertEqual(list(r[u"profile"]), list(P4))
            for p in P4:
                x = nm(r, p)
                for k in (u"語", u"止めた", u"届いた(文)", u"先頭が同じ", u"recomputed が同じ", u"先頭の pointer", u"先頭の切り方", u"基準の state", u"基準が GROUNDED"):
                    self.assertIn(k, x)
                self.assertIn(x[u"語"], WORDS)

    def test_e_3_the_thirteen_words_cover_every_row_once(self):
        for p in P4:
            c = collections.Counter(word(r, p) for r in self.rec[u"rows"])
            self.assertEqual(sum(c.values()), len(self.rec[u"rows"]))
            self.assertTrue(set(c) <= set(WORDS))

    def test_e_4_t3_has_no_base_and_main_rows_have_a_base_from_p22(self):
        for r in self.rec[u"rows"]:
            if r[u"型"] == "T3_ABSENT":
                self.assertIsNone(r[u"基準の claim"])
                self.assertIsNone(nm(r, "P22")[u"基準の state"])
            else:
                self.assertEqual(r[u"profile"]["P22"][u"無改変"][u"claim"][u"id"], r[u"基準の claim"])
                self.assertEqual(r[u"profile"]["P22"][u"無改変"][u"claim"][u"state"], "GROUNDED")

    def test_e_5_the_two_named_counts_are_recounted_from_the_claims(self):
        for p in P4:
            n1, n2, n3 = named_counts(self.rec, p)
            self.assertEqual(n1, len(named_rows(self.rec, p)))
            self.assertEqual(n2, sum(1 for r in named_rows(self.rec, p) if nm(r, p)[u"recomputed が同じ"]))
            self.assertEqual(n3, sum(1 for r in mains(self.rec) if word(r, p) == W_OTHERFACT))

    def test_e_6_the_stop_word_rules_cover_each_word_by_a_hand_made_claim(self):
        u"""手で作った claim で 13 語が 1 つずつ出る(記録に無い語の枝も、規則の表が正しいことを見る)。"""
        def c(state, reason=None, ptrs=None, rc=None):
            return {"state": state, "reason": reason, "pointers": ptrs or [], "recomputed": rc}
        base = c("GROUNDED", None, ["xbrl:jppfs_cor:A@CurrentYearDuration"], 5)
        same = c("VALUE_MISMATCH", None, ["xbrl:jppfs_cor:A@CurrentYearDuration"], 5)
        other = c("VALUE_MISMATCH", None, ["xbrl:jppfs_cor:B@CurrentYearDuration"], 5)
        cases = [("T1_VALUE", None, base, W_NOMAP), ("T1_VALUE", c("GROUNDED"), base, W_PASS), ("T1_VALUE", same, base, W_NAMED), ("T1_VALUE", other, base, W_OTHERFACT),
                 ("T2_UNIT", same, None, W_OTHERFACT), ("T3_ABSENT", same, None, W_NOBASE), ("T1_VALUE", c("POINTER_NOT_FOUND", "no_same_value"), base, W_NOSAME),
                 ("T1_VALUE", c("POINTER_NOT_FOUND", "other_concept"), base, W_OTHERCON), ("T1_VALUE", c("POINTER_NOT_FOUND", "no_element(point without prior phrase)"), base, W_NOELEM),
                 ("T1_VALUE", c("POINTER_NOT_FOUND", "no_prior_member_context"), base, W_NOELEM), ("T1_VALUE", c("POINTER_NOT_FOUND", "unresolved:xbrl:x"), base, W_NOPTR),
                 ("T1_VALUE", c("POINTER_NOT_FOUND", "no_pointer"), base, W_NOPTR), ("T3_ABSENT", c("UNVERIFIABLE", "no_subject"), None, W_NOSUBJ),
                 ("T3_ABSENT", c("UNVERIFIABLE", "ambiguous(elements)"), None, W_AMBIG), ("T3_ABSENT", c("UNVERIFIABLE", "per_unit_counter"), None, W_FRAME),
                 ("T1_VALUE", c("VALUE_MISMATCH", None, []), base, W_OUT), ("T1_VALUE", c("POINTER_NOT_FOUND", None), base, W_OUT), ("T1_VALUE", c("UNVERIFIABLE", "unknown_reason"), base, W_OUT)]
        for t, a, b, want in cases:
            self.assertEqual(reword(t, a, b), want, (t, a, want))

    def test_e_7_the_script_functions_agree_with_the_gate_on_made_up_claims_and_pointers(self):
        u"""script の stop_word・split_pointer を AST で取り出し(import しない)、手で作った claim・pointer で本門の別実装と比べる。"""
        import ast
        tree = ast.parse(jtext(SCRIPT))
        want_names = set(["W_NOMAP", "W_PASS", "W_NAMED", "W_OTHERFACT", "W_NOBASE", "W_NOSAME", "W_OTHERCON", "W_NOELEM", "W_NOPTR", "W_NOSUBJ", "W_AMBIG", "W_FRAME", "W_OUT",
                          "HOLD_REASONS", "STD_PREFIX", "PERIOD", "SOLE_MEMBER", "MAIN_TYPES"])
        fns = set(["stop_word", "same_head", "same_recomputed", "split_pointer"])
        body = []
        for n in tree.body:
            if isinstance(n, ast.Assign):
                names = set(t.id for t in n.targets if isinstance(t, ast.Name)) | set(e.id for t in n.targets if isinstance(t, ast.Tuple) for e in t.elts if isinstance(e, ast.Name))
                if names & want_names:
                    body.append(n)
            elif isinstance(n, ast.FunctionDef) and n.name in fns:
                body.append(n)
        ns = {"re": re}
        exec(compile(ast.Module(body=body, type_ignores=[]), SCRIPT, "exec"), ns)
        self.assertEqual(set(fns) - set(ns), set())

        def c(state, reason=None, ptrs=None, rc=None):
            return {"state": state, "reason": reason, "pointers": ptrs or [], "recomputed": rc}
        base = c("GROUNDED", None, ["xbrl:jppfs_cor:A@CurrentYearDuration"], 5)
        cases = [(None, base), (c("GROUNDED"), base), (c("VALUE_MISMATCH", None, ["xbrl:jppfs_cor:A@CurrentYearDuration"], 5), base),
                 (c("VALUE_MISMATCH", None, ["xbrl:jppfs_cor:B@CurrentYearDuration"], 5), base), (c("VALUE_MISMATCH", None, ["xbrl:jppfs_cor:A@CurrentYearDuration"], 5), None),
                 (c("VALUE_MISMATCH", None, ["xbrl:jppfs_cor:A@CurrentYearDuration"], 5), c("GROUNDED", None, [], 5)),
                 (c("POINTER_NOT_FOUND", "no_same_value"), base), (c("POINTER_NOT_FOUND", "other_concept"), base), (c("POINTER_NOT_FOUND", "no_element"), base),
                 (c("POINTER_NOT_FOUND", "no_element(unit not in XBRL)"), base), (c("POINTER_NOT_FOUND", "no_prior_member_context"), base),
                 (c("POINTER_NOT_FOUND", "no_pointer"), base), (c("POINTER_NOT_FOUND", "unresolved:xbrl:x"), base), (c("POINTER_NOT_FOUND", None), base),
                 (c("UNVERIFIABLE", "no_subject"), base), (c("UNVERIFIABLE", "ambiguous(member)"), base), (c("UNVERIFIABLE", "other_frame"), base),
                 (c("UNVERIFIABLE", "prior is 0"), base), (c("UNVERIFIABLE", "something_new"), base), (c("UNVERIFIABLE", None), base), (c("VALUE_MISMATCH", None, []), base)]
        seen = set()
        for typ in ("T1_VALUE", "T3_ABSENT"):
            for a, b in cases:
                w = ns["stop_word"](typ, a, None if typ == "T3_ABSENT" else b)
                self.assertEqual(w, reword(typ, a, None if typ == "T3_ABSENT" else b), (typ, a, b))
                seen.add(w)
        self.assertEqual(seen, set(WORDS))                                                # 13 語の全部が手で作った claim から出る
        ptrs = [u"xbrl:jppfs_cor:Assets@CurrentYearInstant", u"xbrl:jpcrp_cor:X@Prior1YearDuration_NonConsolidatedMember", u"xbrl:jppfs_cor:Y@CurrentYearDuration_ConsolidatedMember",
                u"xbrl:jppfs_cor:Y@Prior2YearInstant_AMember_BMember", u"xbrl:jpcrp030000-asr_E99999-000:Foo@CurrentYearDuration", u"xbrl:jppfs_cor:Z@Weird", u"formula:a+b", u"builtin:x", None]
        for ptr in ptrs:
            cut = ns["split_pointer"](ptr)
            if ptr is None:
                self.assertIsNone(cut)
                continue
            mem = None
            if cut[u"member"] is not None:
                mem = u"なし" if not cut[u"member"] else (u"単体" if cut[u"member が単体のみ"] else u"それ以外")
            self.assertEqual((cut[u"scheme"], cut[u"要素名"], cut[u"接頭辞"], cut[u"期"], mem, cut[u"標準の接頭辞"]), resplit(ptr), ptr)
        self.assertFalse(ns["split_pointer"](ptrs[4])[u"標準の接頭辞"])                    # 提出者別の接頭辞は標準でない
        self.assertTrue(ns["split_pointer"](ptrs[0])[u"標準の接頭辞"])

    def test_j_1_the_inputs_read_are_unchanged(self):
        self.assertEqual(check_j(self.rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"読んだ入力の sha256"][REACH_REL] = u"0" * 64
        self.assertNotEqual(check_j(rec), [])

    def test_d_1_judgments_are_recomputed_and_cover_the_seventeen_predictions(self):
        J = judge(self.rec, self.inp, self.seal)
        self.assertEqual(list(J), ["SR-%d" % i for i in range(1, 18)])
        self.assertTrue(all(v[1] in (True, False, None) for v in J.values()))

    def test_d_2_the_judge_is_not_a_constant(self):
        J0 = judge(self.rec, self.inp, self.seal)
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"W-1"][u"前の便の門(4 欄とも一致)"][0] -= 1
        self.assertNotEqual(judge(rec, self.inp, self.seal)["SR-1"], J0["SR-1"])
        rec = copy.deepcopy(self.rec)
        r = [x for x in of_type(rec, "T1_VALUE") if word(x, "P27") == W_NAMED][0]
        nm(r, "P27")[u"語"] = W_OTHERFACT
        self.assertNotEqual(judge(rec, self.inp, self.seal)["SR-3"], J0["SR-3"])
        self.assertNotEqual(judge(rec, self.inp, self.seal)["SR-4"], J0["SR-4"])
        rec = copy.deepcopy(self.rec)
        for r in of_type(rec, "T3_ABSENT")[:60]:
            nm(r, "P27")[u"語"] = W_PASS
        self.assertNotEqual(judge(rec, self.inp, self.seal)["SR-14"], J0["SR-14"])
        rec = copy.deepcopy(self.rec)
        for r in mains(rec)[:80]:
            nm(r, "P26")[u"語"] = W_NOMAP if word(r, "P27") != W_NOMAP else W_PASS
        self.assertNotEqual(judge(rec, self.inp, self.seal)["SR-17"], J0["SR-17"])
        rec = copy.deepcopy(self.rec)
        for r in named_rows(rec, "P27")[:30]:
            nm(r, "P27")[u"先頭の切り方"][u"期"] = u"Prior1YearDuration"
        self.assertNotEqual(judge(rec, self.inp, self.seal)["SR-13"], J0["SR-13"])


class EngineTest(unittest.TestCase):
    def test_f_1_engine_sha16_are_pinned_or_declared(self):
        rec = jload(REC)
        self.assertEqual(rec[u"engine sha16"], ENGINE_AT_MEASURE)
        self.assertEqual(rec[u"DEFAULT_PROFILE"], "P27")
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

    def test_c_3_the_eval_table_is_read_from_the_eval_record_and_kept_apart(self):
        a = self.inp["eval"][u"集計(4 profile の全部で対応が付く行が分母。V-1〜V-3)"]
        for t in ("T8_REL", "T1_VALUE"):
            for p in ("P26", "P27", "P27E"):
                x = a[t][p][u"全体"][u"名指して原本の値を返した"]
                self.assertEqual(round(100.0 * x[u"件"] / x[u"分母"], 1), x[u"率"], (t, p))
        blocks = doc_blocks(self.doc)
        self.assertTrue(all(l.count(u"T8_REL") == 0 for k, ls in blocks.items() if k != "eval" for l in ls))
        self.assertTrue(all(w not in u"\n".join(blocks["eval"]) for w in (W_NAMED, W_NOSAME)))

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
        self.assertEqual(list(SP), ["SR-%d" % i for i in range(1, 18)])
        self.assertEqual([len(ranges_of(SP["SR-%d" % i][1])) for i in range(1, 18)], [0, 0, 3, 1, 2, 1, 0, 5, 1, 1, 1, 1, 1, 4, 0, 0, 0])
        self.assertEqual([len(singles_of(SP["SR-%d" % i][1])) for i in range(1, 18)], [2, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 1, 2, 0])
        self.assertEqual([len(pcts_of(SP["SR-%d" % i][1])) for i in range(1, 18)], [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1])

    def test_d_5_the_misses_are_kept_as_misses(self):
        J = judge(self.rec, self.inp, self.seal)
        self.assertEqual([k for k, v in J.items() if v[1] is False], MISSES)
        self.assertEqual([k for k, v in J.items() if v[1] is None], UNDECIDED)
        self.assertEqual([k for k, v in J.items() if v[1] is True], [k for k in J if k not in MISSES and k not in UNDECIDED])

    def test_h_1_no_docid_no_claim_id_and_no_filer_prefix_in_the_seal_and_the_document(self):
        fetched = self.inp["fetched"]
        self.assertEqual(check_h(self.seal, self.doc, fetched, self.rec), [])
        self.assertEqual(len(fetched[u"使う書類"]), 30)
        # この材料では、claim の pointers に提出者別の接頭辞が 1 つも出ない(測った事実)。0 件の門は黙るので、集める関数が本物に効くことは下の h_2・g_8 で見る
        std = collections.Counter()
        for r in self.rec[u"rows"]:
            for p in P4:
                for c in (after_claim(r, p), base_claim(r, p)):
                    for ptr in (c or {}).get("pointers") or []:
                        std[ptr.split(u":", 1)[0]] += 1
        self.assertTrue(std["xbrl"] > 0)
        self.assertEqual(filer_prefixes(self.rec), set())

    def test_h_3_the_filer_prefix_collector_works_on_a_made_up_pointer(self):
        rec = copy.deepcopy(self.rec)
        after_claim(rec[u"rows"][0], "P22")["pointers"].append(u"xbrl:jpcrp030000-asr_E99999-000:Foo@CurrentYearDuration")
        self.assertEqual(filer_prefixes(rec), set([u"jpcrp030000-asr_E99999-000"]))
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

    def test_doc_states_the_dated_notes(self):
        self.assertIn(u"2026-10-29", self.doc)
        self.assertIn(u"inject_reach_2026-10-28.json", self.doc)


class ScriptTest(unittest.TestCase):
    def test_script_does_not_remeasure_when_the_output_exists(self):
        before = hashlib.sha256(open(REC, "rb").read()).hexdigest()
        env = dict((k, v) for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "EDINET_API_KEY", "EDINETDB_API_KEY"))
        r = subprocess.run(["python3", SCRIPT, "--out", REC], cwd=ROOT, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        self.assertIn(u"測り直さない", r.stdout)
        self.assertEqual(hashlib.sha256(open(REC, "rb").read()).hexdigest(), before)

    def test_script_has_one_classifier_and_one_splitter(self):
        import ast
        tree = ast.parse(jtext(SCRIPT))
        fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        self.assertEqual(fns.count("stop_word"), 1)
        self.assertEqual(fns.count("split_pointer"), 1)


class FalseRecordsAreRedTest(unittest.TestCase):
    u"""(g) 偽物で赤: 記録の写しを 1 か所変えると (b)(c)(e) が赤になる(変異)。"""

    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def b(self, rec):
        return check_b(rec, self.inp["fr"], self.inp["fetched"], self.inp["reach"], self.inp["reg"])

    def c(self, rec, doc=None, seal=None):
        return check_c(rec, self.inp, seal or self.seal, doc or self.doc)

    def test_g_0_baseline_is_green(self):
        self.assertEqual(self.b(self.rec), [])
        self.assertEqual(self.c(self.rec), [])
        self.assertEqual(check_e(self.rec), [])

    def test_g_1_changing_one_word_turns_e_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in mains(rec) if word(x, "P26") == W_NAMED][0]
        nm(r, "P26")[u"語"] = W_OTHERFACT
        self.assertNotEqual(check_e(rec), [])
        self.assertNotEqual(self.c(rec), [])
        self.assertEqual(self.b(rec), [])                                   # b は語を見ない(1 つの性質は所有する 1 か所で)

    def test_g_2_changing_the_first_pointer_turns_e_b_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in mains(rec) if word(x, "P27") == W_NAMED][0]
        r[u"profile"]["P27"][u"注入後"][u"claim"]["pointers"][0] = u"xbrl:jppfs_cor:ZZZ@CurrentYearInstant"
        self.assertNotEqual(check_e(rec), [])
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        r = [x for x in mains(rec) if word(x, "P27") == W_NAMED][0]
        nm(r, "P27")[u"先頭の切り方"][u"期"] = u"Prior2YearInstant"
        self.assertNotEqual(check_e(rec), [])
        self.assertNotEqual(self.c(rec), [])

    def test_g_3_changing_recomputed_turns_e_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in mains(rec) if word(x, "P22") == W_NAMED and nm(x, "P22")[u"recomputed が同じ"]][0]
        r[u"profile"]["P22"][u"注入後"][u"claim"]["recomputed"] += 1
        self.assertNotEqual(check_e(rec), [])
        self.assertNotEqual(self.c(rec), [])                                # SR-6 の実測(名指し 2 本の差)が動く
        self.assertEqual(self.b(rec), [])                                   # recomputed は前の便の記録に無い欄なので b は見ない(所有は e)
        rec = copy.deepcopy(self.rec)
        r = [x for x in mains(rec) if word(x, "P22") == W_NAMED and nm(x, "P22")[u"recomputed が同じ"]][0]
        nm(r, "P22")[u"recomputed が同じ"] = False
        self.assertNotEqual(check_e(rec), [])
        self.assertNotEqual(self.c(rec), [])

    def test_g_4_changing_the_wiring_flag_turns_b_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"配線の行ごと"][0][u"一致"][u"4 欄とも一致"] = False
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"W-1"][u"P22・P26・P27 の pointers"] -= 1
        self.assertNotEqual(self.b(rec), [])
        self.assertNotEqual(self.c(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"W-3"][u"claim に recomputed の鍵"][0] -= 1
        self.assertNotEqual(self.b(rec), [])
        self.assertNotEqual(self.c(rec), [])
        rec = copy.deepcopy(self.rec)
        d = rec[u"書類(出てくる順)"][0]
        rec[u"書類ごと"][d][u"無改変の 4 state"]["P27E"]["VALUE_MISMATCH"] += 1
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"P27 → P27E で動いた無改変の行"].pop()
        self.assertNotEqual(self.b(rec), [])

    def test_g_5_removing_the_recomputed_key_or_the_p27e_profile_turns_b_red(self):
        rec = copy.deepcopy(self.rec)
        del after_claim(rec[u"rows"][0], "P22")["recomputed"]
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        del rec[u"rows"][0][u"結果(P22〜P27)"]["P27E"]
        self.assertNotEqual(self.b(rec), [])

    def test_g_6_one_character_of_the_document_table_turns_c_red(self):
        for name in ("cls", "named", "reasons", "counts", "p27e", "elements", "context", "wiring", "eval"):
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

    def test_g_7_changing_a_prediction_character_of_the_seal_turns_d_and_c_red(self):
        seal = u"\n".join(l.replace(u"**741 / 741**", u"**741 / 740**", 1) if l.startswith(u"| **SR-1**") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(judge(self.rec, self.inp, seal)["SR-1"], judge(self.rec, self.inp, self.seal)["SR-1"])
        self.assertNotEqual(self.c(self.rec, seal=seal), [])
        seal = u"\n".join(l.replace(u"**0 以上 40 以下**", u"**0 以上 39 以下**", 1) if l.startswith(u"| **SR-4**") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(self.c(self.rec, seal=seal), [])

    def test_g_8_a_docid_a_claim_id_or_a_filer_prefix_in_the_document_turns_h_red(self):
        fetched = self.inp["fetched"]
        doc = self.doc + u"\n" + fetched[u"使う書類"][0] + u"\n"
        self.assertNotEqual(check_h(self.seal, doc, fetched, self.rec), [])
        doc = self.doc + u"\nN012\n"
        self.assertNotEqual(check_h(self.seal, doc, fetched, self.rec), [])
        cid = self.rec[u"rows"][0][u"基準の claim"]
        doc = self.doc + u"\n%s\n" % cid
        self.assertNotEqual(check_h(self.seal, doc, fetched, self.rec), [])
        rec = copy.deepcopy(self.rec)
        after_claim(rec[u"rows"][0], "P22")["pointers"].append(u"xbrl:jpcrp030000-asr_E99999-000:Foo@CurrentYearDuration")
        doc = self.doc + u"\njpcrp030000-asr_E99999-000\n"
        self.assertNotEqual(check_h(self.seal, doc, fetched, rec), [])

    def test_g_9_an_unmarked_number_in_prose_turns_the_prose_check_red(self):
        doc = self.doc + u"\n通した行は 7 行だった。\n"
        self.assertNotEqual(check_doc_prose(self.rec, self.inp, self.seal, doc), [])

    def test_g_10_changing_the_hit_word_in_the_prose_turns_the_prose_check_red(self):
        doc = self.doc.replace(u"外れた予測: ", u"外れた予測: SR-99・", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(check_doc_prose(self.rec, self.inp, self.seal, doc), [])


class OrderTest(unittest.TestCase):
    u"""(i) 封の commit が script・記録・文書・門の commit より前。"""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="stopreason_root_")
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
