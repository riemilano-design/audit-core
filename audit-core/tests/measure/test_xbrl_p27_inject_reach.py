# -*- coding: utf-8 -*-
u"""評価用・調整用 P27 の注入で「差し替えが基準の claim に届いたか」を数える診断の門 ― 封 docs/XBRL_P27_INJECT_REACH_SEAL_2026-10-29.md §5-2 の (a)〜(j)。

記録 ``fixtures/xbrl/p27/inject_reach_2026-10-29.json``(``measure/xbrl_p27_inject_reach_2026-10-29.py`` の出力)・文書 ``docs/XBRL_P27_INJECT_REACH_DIAG_2026-10-29.md``。

  (a) 記録の行の (docID, id) の集合が ``eval_inject``・``tune_p27_inject``・``tune_inject`` の行の集合と同じ(字で留めない)。型別の数・行の欄・結果も記録と同じ。
  (b) 配線の門(評価用 96 / 96・調整用 101 / 101 の全欄一致・書類別の数え 40 組・round-trip 113 / 122)が記録されている(行ごとの旗・書類ごとの数・文の sha256 を記録から数え直す)。
  (c) 文書の表を記録から作り直して 1 行も違わない(``<!-- 門:start 名前 -->`` の中)。門の外の散文の数には【門なし】の印が要る。
  (d) IR-1〜IR-14 の当否を記録から求め(幅は封の表の字から読む。字で留めない)、封の字(予測・外れ方)と、文書の当否の表の字が一致する。
  (e) 分類(封 §2-3)を、記録の欄から別の書き方で求め直して一致する(届いた(文)・届いた(数)・id が同じ・細目の 4 つとも)。
  (f) engine の sha16 を留める(宣言された遷移の型: 値が宣言の値のときだけ、その封が履歴に在ること)。
  (g) 偽物で赤: 記録の写しの分類・文の番号・id の旗・配線の旗・対応の付け方を 1 か所変えると (b)(c)(e) が赤。文書の表の 1 字で (c) が赤、封の予測の 1 字で (d)(c) が赤、
      包みが返り値を変える偽の包み(作り物の backend)で包みの門が赤。
  (h) 封と文書に評価用・調整用 20 書類の docID の字も claim の id の字も無い。記録に持てない欄の鍵が 0(封 §2-5)。
  (i) 封の commit が script・記録・文書・門の commit より前(git の commit の順)。
  (j) 記録が持つ入力の sha256(8 本)がいまの file と一致する(読み直しの元が不変)。

**(i) は、script・記録・文書・門のどれかが commit される前は赤になる**(追跡されていない file には『足した commit』が無い)。skip にしない。
**変数名について**: 過去の門が tests/measure の行頭の名前を数えるので、この門はそれらを行頭に置かない。この file は docID の字を持たない(W の記録から読む)。
"""
import collections
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"

SEAL_REL = "docs/XBRL_P27_INJECT_REACH_SEAL_2026-10-29.md"
DOC_REL = "docs/XBRL_P27_INJECT_REACH_DIAG_2026-10-29.md"
REC_REL = "fixtures/xbrl/p27/inject_reach_2026-10-29.json"
SCRIPT_REL = "measure/xbrl_p27_inject_reach_2026-10-29.py"
GATE_REL = "tests/measure/test_xbrl_p27_inject_reach.py"
FIX = "fixtures/xbrl/p27/"
EVAL_INJ_REL, TUNE_INJ_REL, TUNE_P27_INJ_REL = FIX + "eval_inject_2026-10-27.json", FIX + "tune_inject_2026-10-27.json", FIX + "tune_p27_inject_2026-10-27.json"
W_REL = FIX + "reports_2026-10-27.json"
INPUT_RELS = (EVAL_INJ_REL, TUNE_INJ_REL, TUNE_P27_INJ_REL, FIX + "eval_2026-10-27.json", FIX + "tune_p27_2026-10-27.json", W_REL,
              "fixtures/xbrl/fresh/fetched_2026-10-21.json", FIX + "dbfetch_2026-10-27.json")
SEAL, DOC, REC, SCRIPT = [os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL)]
SEAL_COMMIT_SHORT = "071abb4"
PROFILES = ("P22", "P26", "P27", "P27E")
GROUPS = (u"調整用", u"評価用")
TYPES = ("T1_VALUE", "T8_REL")
TSHORT = {"T1_VALUE": u"T1", "T8_REL": u"T8"}
NOT_GATED = u"【門なし】"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
FORBIDDEN = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")

W_NOMAP, W_NOSENT = u"(対応が付かない)", u"(文が 1 つに決まらない)"
W_RS, W_RP, W_NS, W_NP = u"(届いた・止めた)", u"(届いた・通した)", u"(届かない・止めた)", u"(届かない・通した)"
WORDS6 = (W_NOMAP, W_NOSENT, W_RS, W_RP, W_NS, W_NP)
K_BOTH, K_VALUE, K_NONE = u"値と字", u"値だけ", u"対応が付かない"
D_NUM, D_OTHER = u"数の位置が合う", u"同じ文・別の数"
D_DIFFID, D_MOVED, D_SAME = u"注入後の claim が基準と別の id", u"同じ id・state が無改変と違う", u"同じ id・state も無改変と同じ"
L_PASS, L_ORIG, L_OTHER = u"通した", u"名指して原本の値を返した", u"名指したが別の値"
L_PNF, L_UNV, L_NOMAP = u"止めたが名指さない(POINTER_NOT_FOUND)", u"止めたが名指さない(UNVERIFIABLE)", u"対応が付かない"
LABELS = (L_PASS, L_ORIG, L_OTHER, L_PNF, L_UNV, L_NOMAP)
ROUNDTRIP_PIN = {u"評価用": 113, u"調整用": 122}
ROWS_PIN = {u"評価用": 96, u"調整用": 101}

#: engine の sha16(記録を測った時点の値。字で留める ― 測った事実)。変えるなら宣言された遷移として下の ENGINE_DECLARED に足す。
ENGINE_AT_MEASURE = {
    "adapters/xbrl/extract.py": "3cf55966f12919f0", "adapters/xbrl/vocabulary.py": "514ebb8104451c07", "adapters/xbrl/recipes.py": "52d645e713c53c1c",
    "adapters/xbrl/resolve.py": "a41043763c1d4073", "adapters/xbrl/comparators.py": "d8706338325e725b", "adapters/xbrl/verify_document.py": "c3791080ab5aef2f",
}
#: 宣言された遷移 {file: (遷移の後の sha16, その遷移を宣言した封)}。今は 0 件。足すときは、封が履歴に在り、値が宣言の値のときだけ受け入れる。測った時点の値は消さない。
ENGINE_DECLARED = {}

#: 記録から求めた当否のうち外れ・判定しないの名前(測った事実。外れは外れのまま残す。封も予測も直さない)。記録から求めた当否と食い違えば d_5 が赤。
MISSES = []
UNDECIDED = []

#: 記録に持てる欄(封 §2-5・§6-5。この門が独立に持つ一覧 ― script の一覧とは別に書いた)。
RECORD_KEYS_OK = frozenset([
    u"注意", u"封", u"file", u"commit", u"期待する commit", u"全書類", u"頭", u"HEAD の commit", u"DEFAULT_PROFILE", u"engine sha16", u"engine の指紋",
    u"adapter_xbrl_py_sha256", u"adapter_xbrl_py_files", u"core_py_sha256", u"core_py_files", u"git_commit", u"種", u"sealed_in_commit", u"seed_file_sha256",
    u"読んだ入力の sha256", u"cache", u"開始", u"終了", u"cache_snapshot が同じ", u"対象", u"PROFILES4 が同じ", u"段 1 の file の sha256 が同じ",
    u"engine に未 commit の差が無い", u"観測する profile", u"組の順", u"配線", u"行", u"一致", u"記録の行", u"(docID, id) の集合が同じ", u"書類別の数えの組",
    u"書類別の数えが一致した組", u"round-trip", u"round-trip の期待", u"包みの呼ばれた回数", u"対応を数えた行 × 4", u"claim の一覧の id() が控えに在る", u"通った",
    u"書類ごと", u"組", u"docID", u"書類の位置", u"文の sha256", u"文の sha256 が一致", u"ZIP の sha256 が一致", u"書類別の数え", u"書類別の数えが記録と一致",
    u"claim の数", u"文の数", u"秒", u"所要秒", u"limits", u"key_leaks", u"rows", u"注入の id", u"型", u"文体", u"r", u"r を決めた回", u"基準の claim",
    u"基準の対応の付け方", u"profile", u"注入後の claim の id", u"注入後の id が基準と同じ", u"注入後の対応の付け方", u"基準の claim の無改変の state",
    u"基準の claim の文の番号", u"基準の claim の文の中の位置", u"数の始まり", u"数の終わり", u"token の文の番号", u"文の中で最初に違う位置",
    u"文の数(無改変, 注入後)", u"注入後の claim の文の番号", u"届いた(文)", u"届いた(数)", u"state", u"reason", u"結果", u"注入後の state が無改変の同じ id と同じ",
    u"注入後の pointers が在る", u"注入後の pointers の先頭が基準と同じ", u"分類", u"細目", u"配線の行ごと", u"不一致の欄",
    u"作れる site", u"採った", u"両方 GROUNDED", u"どちらも GROUNDED でない", u"基準に対応が付かない", u"円族の token", u"r が決まらず site にしない",
    u"P22 のみ GROUNDED", u"P26 のみ GROUNDED", u"profile 間で claim が合わない", u"T1_VALUE", u"T8_REL", u"P22", u"P26", u"P27", u"P27E",
    u"edinet", u"edinet-fresh-2026-10-21", u"調整用", u"評価用",
] + list(ENGINE_AT_MEASURE) + list(INPUT_RELS))
#: 持てない欄(封 §2-5)。鍵がこの名前なら赤(一覧の外の鍵も赤)。
RECORD_KEYS_NG = (u"span", u"subject", u"value", u"recomputed", u"pointers", u"元の字", u"後の字", u"新しい値", u"数の字", u"周り", u"抜粋", u"文", u"本文", u"new_value", u"replacement")


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


def outcome_of_state(state):
    u"""state -> 結果の語の候補(この門が別に持つ表)。"""
    return {None: (L_NOMAP,), "GROUNDED": (L_PASS,), "VALUE_MISMATCH": (L_ORIG, L_OTHER), "POINTER_NOT_FOUND": (L_PNF,), "UNVERIFIABLE": (L_UNV,)}[state]


def rate(a, b):
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b) if b else u"%d / 0" % a


def table(head, rows):
    lines = [u"| " + u" | ".join(head) + u" |", u"|" + u"|".join(u"---" for _ in head) + u"|"]
    for r in rows:
        lines.append(u"| " + u" | ".join(str(c) for c in r) + u" |")
    return lines


def rows_of(rec, group=None, typ=None):
    return [r for r in rec[u"rows"] if (group is None or r[u"組"] == group) and (typ is None or r[u"型"] == typ)]


def cls(r, p):
    return r[u"profile"][p][u"分類"]


def positions(rec):
    u"""{(組, docID, id): (組, 書類の番号, 型, その書類・その型の中の番号)}(記録の出てくる順。1 始まり)。"""
    order = dict((g, [e[u"docID"] for e in rec[u"書類ごと"] if e[u"組"] == g]) for g in GROUPS)
    seen, out = collections.Counter(), {}
    for r in rec[u"rows"]:
        d = order[r[u"組"]].index(r["docID"]) + 1
        seen[(r[u"組"], d, r[u"型"])] += 1
        out[(r[u"組"], r["docID"], r[u"注入の id"])] = (r[u"組"], d, r[u"型"], seen[(r[u"組"], d, r[u"型"])])
    return out


def plabel(p):
    return u"%sの書類 %d・%s の %d 番目" % (p[0], p[1], TSHORT[p[2]], p[3])


# ----------------------------------------------------------------------------------------------------------------
# (e) 分類を別の書き方で求め直す(記録の欄だけから。記録の 分類・届いた の欄は読まない)
def reclass(r, p):
    u"""1 行・1 profile: (分類, 届いた(文), 届いた(数), 細目)。"""
    x = r[u"profile"][p]
    aid, tsent, toff = x[u"注入後の claim の id"], x[u"token の文の番号"], x[u"文の中で最初に違う位置"]
    bsent = x[u"基準の claim の文の番号"]
    reached = tsent is not None and bsent == tsent
    st, en = x[u"数の始まり"], x[u"数の終わり"]
    num = bool(reached and st is not None and en is not None and toff is not None and st <= toff <= en + 2)
    if aid is None:
        c = W_NOMAP
    elif tsent is None:
        c = W_NOSENT
    elif reached:
        c = W_RP if x[u"state"] == "GROUNDED" else W_RS
    else:
        c = W_NP if x[u"state"] == "GROUNDED" else W_NS
    det = None
    if c in (W_RS, W_RP):
        det = D_NUM if num else D_OTHER
    elif c in (W_NS, W_NP):
        if aid != r[u"基準の claim"]:
            det = D_DIFFID
        else:
            det = D_SAME if x[u"注入後の state が無改変の同じ id と同じ"] else D_MOVED
    return c, reached, num, det


def check_e(rec):
    u"""問題の列(空なら通す)。"""
    out = []
    for r in rec[u"rows"]:
        if list(r[u"profile"]) != list(PROFILES):
            out.append(u"%s: profile の欄が %s でない" % (r[u"注入の id"], list(PROFILES)))
            continue
        if r[u"型"] not in TYPES or r[u"組"] not in GROUPS:
            out.append(u"%s: 型か組が知らない語" % r[u"注入の id"])
        for p in PROFILES:
            x = r[u"profile"][p]
            c, reached, num, det = reclass(r, p)
            tag = u"%s %s" % (r[u"注入の id"], p)
            if c != x[u"分類"]:
                out.append(u"%s: 分類が求め直しと違う(%s != %s)" % (tag, x[u"分類"], c))
            if reached != x[u"届いた(文)"]:
                out.append(u"%s: 届いた(文)が求め直しと違う" % tag)
            if num != x[u"届いた(数)"]:
                out.append(u"%s: 届いた(数)が求め直しと違う" % tag)
            if det != x[u"細目"]:
                out.append(u"%s: 細目が求め直しと違う" % tag)
            if x[u"注入後の id が基準と同じ"] != (x[u"注入後の claim の id"] == r[u"基準の claim"]):
                out.append(u"%s: id が同じ旗が求め直しと違う" % tag)
            if x[u"結果"] not in outcome_of_state(x[u"state"]):
                out.append(u"%s: 結果の語が state と合わない" % tag)
            if x[u"結果"] == L_ORIG and not x[u"注入後の pointers の先頭が基準と同じ"]:
                out.append(u"%s: 名指して原本の値を返したのに pointers の先頭が基準と同じでない旗" % tag)
            if x[u"分類"] not in WORDS6:
                out.append(u"%s: 分類の語が 6 語に無い" % tag)
            if x[u"注入後の対応の付け方"] not in (K_BOTH, K_VALUE, K_NONE) or r[u"基準の対応の付け方"] not in (K_BOTH, K_VALUE):
                out.append(u"%s: 対応の付け方の語が知らない語" % tag)
            if (x[u"注入後の claim の id"] is None) != (x[u"注入後の対応の付け方"] == K_NONE):
                out.append(u"%s: 注入後の対応の付け方と id の有無が合わない" % tag)
    return out


# ----------------------------------------------------------------------------------------------------------------
# (a)(b)(j)
def old_records():
    return rload(EVAL_INJ_REL), rload(TUNE_P27_INJ_REL), rload(TUNE_INJ_REL)


def check_a(rec, ev, tp, ti):
    out = []
    got = dict((g, set((r["docID"], r[u"注入の id"]) for r in rows_of(rec, g))) for g in GROUPS)
    sets = {u"評価用": [set((r["docID"], r["id"]) for r in ev[u"行"])], u"調整用": [set((r["docID"], r["id"]) for r in tp[u"行"]), set((r["docID"], r["id"]) for r in ti[u"行"])]}
    for g in GROUPS:
        for s in sets[g]:
            if got[g] != s:
                out.append(u"%s: (docID, id) の集合が既存の記録と違う" % g)
        if len(rows_of(rec, g)) != len(got[g]):
            out.append(u"%s: (docID, id) が重複している" % g)
    for g, recs in ((u"評価用", [(ev, PROFILES)]), (u"調整用", [(tp, PROFILES), (ti, ("P22", "P26"))])):
        mine = dict(((r["docID"], r[u"注入の id"]), r) for r in rows_of(rec, g))
        for old, profs in recs:
            for a in old[u"行"]:
                r = mine.get((a["docID"], a["id"]))
                if r is None:
                    continue
                for f in (u"型", u"文体", u"基準の claim", u"r", u"r を決めた回"):
                    if (f in r) != (f in a) or r.get(f) != a.get(f):
                        out.append(u"%s: %s が既存の記録と違う" % (r[u"注入の id"], f))
                for p in profs:
                    x = r[u"profile"][p]
                    if (x[u"state"], x[u"reason"], x[u"結果"]) != (a[p][u"state"], a[p][u"reason"], a[p][u"結果"]) or (x[u"注入後の claim の id"] is not None) != a[p][u"対応"]:
                        out.append(u"%s: %s の対応・結果・state・reason が既存の記録と違う" % (r[u"注入の id"], p))
    for g, old in ((u"評価用", ev), (u"調整用", tp)):
        want = collections.Counter(r[u"型"] for r in old[u"行"])
        if collections.Counter(r[u"型"] for r in rows_of(rec, g)) != want:
            out.append(u"%s: 型別の数が既存の記録と違う" % g)
    return out


def check_b(rec, ev, tp, ti, w, fetched):
    out = []
    if not rec[u"全書類"]:
        out.append(u"全書類の記録でない(試走の記録)")
    if list(rec[u"組の順"]) != list(GROUPS):
        out.append(u"組の順が調整用 → 評価用でない")
    olds = {u"評価用": [ev], u"調整用": [tp, ti]}
    pairs = pairs_ok = 0
    for g in GROUPS:
        gate = rec[u"配線"][g]
        n = len(olds[g][0][u"行"])
        if not (gate[u"通った"] and gate[u"行"] == gate[u"一致"] == gate[u"記録の行"] == n == ROWS_PIN[g]):
            out.append(u"%s: 配線の門が %d / %d でない(行 %s・一致 %s)" % (g, ROWS_PIN[g], ROWS_PIN[g], gate[u"行"], gate[u"一致"]))
        if not gate[u"(docID, id) の集合が同じ"]:
            out.append(u"%s: 集合の旗が偽" % g)
        fl = [f for f in rec[u"配線の行ごと"] if f[u"組"] == g]
        if len(fl) != n or not all(f[u"一致"] and f[u"不一致の欄"] == [] for f in fl):
            out.append(u"%s: 行ごとの旗が全部真でない" % g)
        if [(f["docID"], f[u"注入の id"]) for f in fl] != [(r["docID"], r[u"注入の id"]) for r in rows_of(rec, g)]:
            out.append(u"%s: 配線の行ごとの id が rows と違う" % g)
        if gate[u"round-trip"] != ROUNDTRIP_PIN[g] or gate[u"round-trip の期待"] != ROUNDTRIP_PIN[g]:
            out.append(u"%s: round-trip が %d でない" % (g, ROUNDTRIP_PIN[g]))
        if gate[u"包みの呼ばれた回数"] != gate[u"対応を数えた行 × 4"] or gate[u"対応を数えた行 × 4"] != 4 * n or not gate[u"claim の一覧の id() が控えに在る"]:
            out.append(u"%s: 包みの呼ばれた回数が 行 × 4 でないか、id() が控えに無い" % g)
        want_docs = [c["docID"] for c in w[u"会社"] if c[u"区分"] == g]
        docs = [e for e in rec[u"書類ごと"] if e[u"組"] == g]
        if [e["docID"] for e in docs] != want_docs or [e[u"書類の位置"] for e in docs] != list(range(1, len(want_docs) + 1)):
            out.append(u"%s: 書類の順が W の記録の並びと違う" % g)
        used = dict((r["docID"], r) for r in fetched[u"取得した書類"])
        for e in docs:
            d = e["docID"]
            if e[u"文の sha256"] != dict((c["docID"], c[u"文の sha256"]) for c in w[u"会社"])[d] or not e[u"文の sha256 が一致"]:
                out.append(u"%s: 文の sha256 が W の記録と違う" % d)
            if not e[u"ZIP の sha256 が一致"] or d not in used:
                out.append(u"%s: ZIP の sha256 の旗が偽か、取得の記録に無い" % d)
            if e[u"行"] != sum(1 for r in rows_of(rec, g) if r["docID"] == d):
                out.append(u"%s: 行の数が rows と違う" % d)
            for t in TYPES:
                pairs += 1
                mine = json.dumps(e[u"書類別の数え"][t], ensure_ascii=False, sort_keys=True)
                if all(json.dumps(o[u"書類別の数え"][d][t], ensure_ascii=False, sort_keys=True) == mine for o in olds[g]):
                    pairs_ok += 1
                else:
                    out.append(u"%s %s: 書類別の数えが既存の記録と違う" % (d, t))
            if not e[u"書類別の数えが記録と一致"]:
                out.append(u"%s: 書類別の数えの旗が偽" % d)
            if sum(e[u"書類別の数え"][t].get(u"採った", 0) for t in TYPES) <= 0:
                out.append(u"%s: 採った注入が 0" % d)
        if gate[u"書類別の数えの組"] != gate[u"書類別の数えが一致した組"] or gate[u"書類別の数えの組"] != 2 * len(want_docs):
            out.append(u"%s: 書類別の数えの組の旗が 全部一致でない" % g)
        if sum(sum(e[u"書類別の数え"][t].get(u"採った", 0) for t in TYPES) for e in docs) != ROUNDTRIP_PIN[g]:
            out.append(u"%s: 書類別の数えの『採った』の合計が round-trip の数と違う" % g)
    if (pairs, pairs_ok) != (40, 40):
        out.append(u"書類別の数えの組が 40 / 40 でない(%d / %d)" % (pairs_ok, pairs))
    c = rec[u"頭"][u"cache"]
    if c[u"開始"] != c[u"終了"] or c[u"開始"][u"edinet"] != 281 or c[u"開始"][u"edinet-fresh-2026-10-21"] != 40 or not rec[u"頭"][u"cache_snapshot が同じ"]:
        out.append(u"cache の件数が 281 / 40 のまま動いていない")
    if rec[u"key_leaks"] != []:
        out.append(u"key_leaks が空でない")
    for k in (u"PROFILES4 が同じ", u"段 1 の file の sha256 が同じ", u"engine に未 commit の差が無い"):
        if rec[u"頭"][k] is not True:
            out.append(u"頭の %s が真でない" % k)
    return out


def check_j(rec):
    out = []
    got = rec[u"頭"][u"読んだ入力の sha256"]
    if sorted(got) != sorted(INPUT_RELS):
        out.append(u"読んだ入力の一覧が封の 8 本と違う")
    for rel in INPUT_RELS:
        if got.get(rel) != sha64(rel):
            out.append(u"%s の sha256 が記録の写しと違う(読み直しの元が動いた)" % rel)
    return out


# ----------------------------------------------------------------------------------------------------------------
# (d) IR-1〜IR-14 の当否を記録から求める(幅は封の表の字から読む)
BOLD = re.compile(r"\*\*(.+?)\*\*")
RANGE_RE = re.compile(r"^(\d+(?:\.\d+)?)%? 以上 (\d+(?:\.\d+)?)%? 以下$")


def seal_predictions(seal):
    u"""封 §3 の表の行 {名前: (欄, 予測, 外れ方)}(封の字のまま)。"""
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(IR-\d+)\*\* \| (.*) \|$", l)
        if m:
            cells = m.group(2).split(u" | ")
            assert len(cells) == 3, l
            out[m.group(1)] = tuple(c.strip() for c in cells)
    return out


def ranges_of(cell):
    return [(float(m.group(1)), float(m.group(2))) for m in (RANGE_RE.match(b) for b in BOLD.findall(cell)) if m]


def singles_of(cell):
    return [b for b in BOLD.findall(cell) if not RANGE_RE.match(b)]


def within(n, rg):
    return rg[0] <= n <= rg[1]


def hit_word(b):
    return u"**判定しない**" if b is None else (u"**当たり**" if b else u"**外れ**")


def reread_sets(rec, group, typ):
    u"""(元の分母の行 = 4 profile の全部で対応が付く行, 読み直しの分母の行 = そのうち 4 profile の全部で (届いた・止めた) か (届いた・通した) の行)。"""
    orig = [r for r in rows_of(rec, group, typ) if all(cls(r, p) != W_NOMAP for p in PROFILES)]
    re_ = [r for r in orig if all(cls(r, p) in (W_RS, W_RP) for p in PROFILES)]
    return orig, re_


def pct(n, d):
    return None if not d else 100.0 * n / d


def judge(rec, seal):
    u"""{名前: (実測の字, 当たりか(True / False / None=判定しない))}。封 §3 の予測を記録から。幅は封の字から読む。"""
    SP = seal_predictions(seal)
    out = collections.OrderedDict()

    def per_gp(fn):
        return dict(((g, p), fn(rows_of(rec, g), p)) for g in GROUPS for p in PROFILES)

    def fmt(d):
        return u"・".join(u"%s %s" % (g, u" ".join(u"%s %d" % (p, d[(g, p)]) for p in PROFILES)) for g in (u"評価用", u"調整用"))
    # IR-1
    c = SP["IR-1"][1]
    ev_a, ev_b = [int(x) for x in re.search(r"評価用 (\d+) / (\d+) 行", c).groups()]
    tu_a, tu_b = [int(x) for x in re.search(r"調整用 (\d+) / (\d+) 行", c).groups()]
    npair = int(re.search(r"(\d+) 組", c).group(1))
    rt_e, rt_t = [int(x) for x in re.search(r"round-trip 評価用 (\d+)・調整用 (\d+)", c).groups()]
    G = rec[u"配線"]
    ok = all(G[g][u"通った"] and G[g][u"(docID, id) の集合が同じ"] for g in GROUPS)
    ok = ok and (G[u"評価用"][u"一致"], G[u"評価用"][u"行"]) == (ev_a, ev_b) and (G[u"調整用"][u"一致"], G[u"調整用"][u"行"]) == (tu_a, tu_b)
    ok = ok and sum(G[g][u"書類別の数えが一致した組"] for g in GROUPS) == npair == sum(G[g][u"書類別の数えの組"] for g in GROUPS)
    ok = ok and (G[u"評価用"][u"round-trip"], G[u"調整用"][u"round-trip"]) == (rt_e, rt_t)
    out["IR-1"] = (u"配線の門 評価用 %d / %d・調整用 %d / %d(集合が同じ: %s)、書類別の数え %d / %d、round-trip 評価用 %d・調整用 %d" % (
        G[u"評価用"][u"一致"], G[u"評価用"][u"行"], G[u"調整用"][u"一致"], G[u"調整用"][u"行"], yesno(all(G[g][u"(docID, id) の集合が同じ"] for g in GROUPS)),
        sum(G[g][u"書類別の数えが一致した組"] for g in GROUPS), sum(G[g][u"書類別の数えの組"] for g in GROUPS), G[u"評価用"][u"round-trip"], G[u"調整用"][u"round-trip"]), ok)
    # IR-2 / IR-4: 評価用の幅・調整用の幅(予測の字の順 = 評価用, 調整用)
    d2 = per_gp(lambda rs, p: sum(1 for r in rs if r[u"profile"][p][u"注入後の claim の id"] is not None and not r[u"profile"][p][u"注入後の id が基準と同じ"]))
    rg = ranges_of(SP["IR-2"][1])
    out["IR-2"] = (u"注入後の id が基準と違う行: " + fmt(d2), all(within(d2[(g, p)], rg[0] if g == u"評価用" else rg[1]) for g in GROUPS for p in PROFILES))
    d3 = per_gp(lambda rs, p: sum(1 for r in rs if cls(r, p) == W_NOSENT))
    out["IR-3"] = (u"%s: " % W_NOSENT + fmt(d3), all(within(v, ranges_of(SP["IR-3"][1])[0]) for v in d3.values()))
    d4 = per_gp(lambda rs, p: sum(1 for r in rs if cls(r, p) in (W_NS, W_NP)))
    rg = ranges_of(SP["IR-4"][1])
    out["IR-4"] = (u"届かない(文): " + fmt(d4), all(within(d4[(g, p)], rg[0] if g == u"評価用" else rg[1]) for g in GROUPS for p in PROFILES))
    # IR-5
    def mism(rs, p):
        return sum(1 for r in rs if cls(r, p) in (W_RS, W_RP, W_NS, W_NP) and r[u"profile"][p][u"注入後の id が基準と同じ"] != r[u"profile"][p][u"届いた(文)"])
    d5 = per_gp(mism)
    z5 = int(singles_of(SP["IR-5"][1])[0])
    out["IR-5"] = (u"id が同じと届いた(文)の食い違い: " + fmt(d5), all(v == z5 for v in d5.values()))
    # IR-6(P22)
    d6 = dict((g, sum(1 for r in rows_of(rec, g) if r[u"profile"]["P22"][u"細目"] == D_OTHER)) for g in GROUPS)
    out["IR-6"] = (u"同じ文・別の数(P22): 評価用 %d・調整用 %d" % (d6[u"評価用"], d6[u"調整用"]), all(within(v, ranges_of(SP["IR-6"][1])[0]) for v in d6.values()))
    # IR-7 / IR-8
    d7 = per_gp(lambda rs, p: sum(1 for r in rs if r[u"profile"][p][u"結果"] == L_PASS and cls(r, p) != W_RP))
    n7 = per_gp(lambda rs, p: sum(1 for r in rs if r[u"profile"][p][u"結果"] == L_PASS))
    rg = ranges_of(SP["IR-7"][1])[0]
    out["IR-7"] = (u"通したのうち %s でない行: %s(通した: %s)" % (W_RP, fmt(d7), fmt(n7)),
                   all((within(d7[(g, p)], rg) if p in ("P22", "P26") else d7[(g, p)] == 0) for g in GROUPS for p in PROFILES))
    d8 = per_gp(lambda rs, p: sum(1 for r in rs if r[u"profile"][p][u"結果"] == L_OTHER and cls(r, p) != W_RS))
    n8 = per_gp(lambda rs, p: sum(1 for r in rs if r[u"profile"][p][u"結果"] == L_OTHER))
    out["IR-8"] = (u"名指したが別の値のうち %s でない行: %s(名指したが別の値: %s)" % (W_RS, fmt(d8), fmt(n8)), all(within(v, ranges_of(SP["IR-8"][1])[0]) for v in d8.values()))
    # IR-9
    lo, hi = [int(x) for x in re.search(r"(\d+) 行以上 / (\d+)", singles_of(SP["IR-9"][1])[0]).groups()]
    un = [r for r in rec[u"rows"] if cls(r, "P22") == W_NOMAP]
    k9 = sum(1 for r in un if r[u"profile"]["P22"][u"届いた(文)"])
    out["IR-9"] = (u"P22 の対応が付かない行 %d のうち token の文 = 基準の claim の文: %d" % (len(un), k9), k9 >= lo and len(un) == hi)
    # IR-10 / IR-11
    def reread_judge(k, group, with_p22):
        c = SP[k][1]
        rg = ranges_of(c)[0]
        orig, re_ = reread_sets(rec, group, "T8_REL")
        n = len(re_)
        tol = float(re.search(r"± (\d+(?:\.\d+)?) pt", c).group(1))
        pass_c = float(re.search(r"\*\*(\d+(?:\.\d+)?)% ± ", c).group(1))
        names = dict((p, float(re.search(r"%s \**(\d+(?:\.\d+)?)%%" % p, c.split(u"名指して原本")[1]).group(1))) for p in (("P22",) if with_p22 else ()) + ("P26", "P27", "P27E"))
        zero = float(re.search(r"P27・P27E\s*は?\s*\*\*(\d+(?:\.\d+)?)%\*\*", c).group(1))
        parts, hit = [], within(n, rg)
        for p in PROFILES:
            kp = sum(1 for r in re_ if r[u"profile"][p][u"結果"] == L_PASS)
            kn = sum(1 for r in re_ if r[u"profile"][p][u"結果"] == L_ORIG)
            a, b = pct(kp, n), pct(kn, n)
            parts.append(u"%s 通した %s・名指して原本 %s" % (p, rate(kp, n), rate(kn, n)))
            if a is None:
                hit = False
                continue
            hit = hit and (abs(a - pass_c) <= tol if p in ("P22", "P26") else round(a, 1) == zero)
            if p in names:
                hit = hit and abs(b - names[p]) <= tol
        return (u"%sの T8_REL: 元の分母 %d・読み直しの分母 %d。" % (group, len(orig), n) + u"・".join(parts)), hit
    out["IR-10"] = reread_judge("IR-10", u"評価用", False)
    out["IR-11"] = reread_judge("IR-11", u"調整用", True)
    # IR-12
    n_e, n_t = [int(x) for x in re.search(r"評価用 (\d+)・調整用 (\d+)", SP["IR-12"][0]).groups()]
    want_cls = singles_of(SP["IR-12"][1])[0]
    d12 = {}
    for g in GROUPS:
        rs = rows_of(rec, g, "T1_VALUE")
        mapped = dict((p, [r for r in rs if cls(r, p) != W_NOMAP]) for p in PROFILES)
        d12[g] = (len(mapped["P22"]), all(len(mapped[p]) == len(mapped["P22"]) for p in PROFILES) and all(cls(r, p) == want_cls for p in PROFILES for r in mapped[p]))
    out["IR-12"] = (u"T1_VALUE の対応が付く行: 評価用 %d・調整用 %d。全部 %s: 評価用 %s・調整用 %s" % (d12[u"評価用"][0], d12[u"調整用"][0], want_cls, yesno(d12[u"評価用"][1]), yesno(d12[u"調整用"][1])),
                   d12[u"評価用"][0] == n_e and d12[u"調整用"][0] == n_t and d12[u"評価用"][1] and d12[u"調整用"][1])
    # IR-13
    nd = int(re.search(r"(\d+) 書類", SP["IR-13"][1]).group(1))
    docs = rec[u"書類ごと"]
    same = [e for e in docs if len(set(e[u"文の数"][p] for p in PROFILES)) == 1]
    out["IR-13"] = (u"無改変の文の数が 4 profile で同じ書類: %d / %d" % (len(same), len(docs)), len(docs) == nd == len(same))
    # IR-14
    n14 = int(re.search(r"(\d+) 行", SP["IR-14"][0]).group(1))
    c14 = [r for r in rec[u"rows"] if r[u"profile"]["P27"][u"基準の claim の無改変の state"] == "UNVERIFIABLE"]
    ok14 = bool(c14) and all(r[u"profile"]["P27"][u"届いた(文)"] and cls(r, "P27") not in (W_NOMAP, W_NOSENT) for r in c14)
    out["IR-14"] = (u"P27 の無改変で基準が UNVERIFIABLE の行 %d: 届いた(文) %s" % (len(c14), u"・".join(yesno(r[u"profile"]["P27"][u"届いた(文)"]) for r in c14)), len(c14) == n14 and ok14)
    return out


# ----------------------------------------------------------------------------------------------------------------
# (c) 文書の表
def cnt(rs, p, key):
    return collections.Counter(r[u"profile"][p][key] for r in rs)


def render_blocks(rec, seal):
    B = collections.OrderedDict()
    pos = positions(rec)
    J = judge(rec, seal)
    SP = seal_predictions(seal)
    assert list(SP) == list(J), list(SP)
    B["pred"] = table([u"#", u"欄", u"予測(封の字)", u"外れ方(封の字)", u"実測(記録から)", u"当たり外れ"],
                      [[u"**%s**" % k, SP[k][0], SP[k][1], SP[k][2], J[k][0], hit_word(J[k][1])] for k in J])
    wrows = []
    for g in GROUPS:
        x = rec[u"配線"][g]
        wrows.append([g, u"%d / %d" % (x[u"一致"], x[u"行"]), str(x[u"記録の行"]), yesno(x[u"(docID, id) の集合が同じ"]), u"%d / %d" % (x[u"書類別の数えが一致した組"], x[u"書類別の数えの組"]),
                      str(x[u"round-trip"]), u"%d / %d" % (x[u"包みの呼ばれた回数"], x[u"対応を数えた行 × 4"]), yesno(x[u"claim の一覧の id() が控えに在る"])])
    B["wiring"] = table([u"組", u"作り直した行 / 全欄一致", u"記録の行", u"(docID, id) の集合が同じ", u"書類別の数えの組 / 一致", u"round-trip", u"包みの呼ばれた回数 / 対応を数えた行 × 4",
                         u"claim の一覧の id() が控えに在る"], wrows)
    crow = []
    for g in GROUPS:
        for t in TYPES:
            s = collections.Counter()
            for e in rec[u"書類ごと"]:
                if e[u"組"] == g:
                    for k, v in e[u"書類別の数え"][t].items():
                        s[k] += v
            crow.append([g, TSHORT[t], str(s[u"作れる site"]), str(s[u"採った"]), str(s[u"両方 GROUNDED"]), str(s[u"どちらも GROUNDED でない"]), str(s[u"基準に対応が付かない"])])
    B["counts"] = table([u"組", u"型", u"作れる site", u"採った", u"両方 GROUNDED", u"どちらも GROUNDED でない", u"基準に対応が付かない"], crow)
    drows = []
    for g in GROUPS:
        for e in rec[u"書類ごと"]:
            if e[u"組"] == g:
                nmatch = sum(1 for f in rec[u"配線の行ごと"] if f["docID"] == e["docID"] and f[u"一致"])
                drows.append([u"%sの書類 %d" % (g, e[u"書類の位置"]), e[u"文の sha256"], str(e[u"行"]), str(nmatch), str(e[u"claim の数"]["P22"]), str(e[u"claim の数"]["P27E"]),
                              str(e[u"文の数"]["P22"]), str(e[u"文の数"]["P27E"])])
    B["docs"] = table([u"書類", u"文の sha256(W の記録と一致)", u"注入の行", u"配線の一致", u"claim(P22)", u"claim(P27E)", u"文(P22)", u"文(P27E)"], drows)
    h = rec[u"頭"]
    B["engine"] = table([u"項目", u"値"], [[u"`%s` の sha16" % k, u"`%s`" % v] for k, v in h[u"engine sha16"].items()] + [
        [u"DEFAULT_PROFILE", h[u"DEFAULT_PROFILE"]], [u"測った木の HEAD", u"`%s`" % h[u"HEAD の commit"]], [u"封の commit", u"`%s`" % rec[u"封"][u"commit"]],
        [u"cache `edinet/`(開始 → 終了)", u"%d → %d" % (h[u"cache"][u"開始"][u"edinet"], h[u"cache"][u"終了"][u"edinet"])],
        [u"cache `edinet-fresh-2026-10-21/`(開始 → 終了)", u"%d → %d" % (h[u"cache"][u"開始"][u"edinet-fresh-2026-10-21"], h[u"cache"][u"終了"][u"edinet-fresh-2026-10-21"])],
        [u"key_leaks", str(len(rec[u"key_leaks"]))]])
    # 位置・分類・細目・対応の付け方(組 × profile × 型 + 計)
    prow, crow, drow, mrow, brow = [], [], [], [], []
    for g in GROUPS:
        for p in PROFILES:
            groups = [(TSHORT[t], rows_of(rec, g, t)) for t in TYPES] + [(u"計", rows_of(rec, g))]
            for name, rs in groups:
                mapped = [r for r in rs if r[u"profile"][p][u"注入後の claim の id"] is not None]
                same = sum(1 for r in mapped if r[u"profile"][p][u"注入後の id が基準と同じ"])
                rc = sum(1 for r in mapped if cls(r, p) in (W_RS, W_RP))
                rn = sum(1 for r in mapped if cls(r, p) in (W_RS, W_RP) and r[u"profile"][p][u"届いた(数)"])
                nr = sum(1 for r in mapped if cls(r, p) in (W_NS, W_NP))
                ns = sum(1 for r in mapped if cls(r, p) == W_NOSENT)
                prow.append([g, p, name, str(len(rs)), str(len(rs) - len(mapped)), str(len(mapped)), str(same), str(rc), str(rn), str(rc - rn), str(nr), str(ns)])
                c = cnt(rs, p, u"分類")
                crow.append([g, p, name, str(len(rs))] + [str(c[w]) for w in WORDS6])
                dc = cnt(rs, p, u"細目")
                drow.append([g, p, name, str(dc[D_NUM]), str(dc[D_OTHER]), str(dc[D_DIFFID]), str(dc[D_MOVED]), str(dc[D_SAME])])
                a0 = collections.Counter(r[u"基準の対応の付け方"] for r in rs)
                a1 = cnt(rs, p, u"注入後の対応の付け方")
                mrow.append([g, p, name, str(a0[K_BOTH]), str(a0[K_VALUE]), str(a1[K_BOTH]), str(a1[K_VALUE]), str(a1[K_NONE])])
                bad = [r for r in rs if r[u"profile"][p][u"基準の claim の無改変の state"] != "GROUNDED"]
                brow.append([g, p, name, str(len(rs)), str(len(bad)), str(sum(1 for r in bad if r[u"profile"][p][u"注入後の state が無改変の同じ id と同じ"])),
                             str(sum(1 for r in bad if r[u"profile"][p][u"届いた(文)"]))])
    B["pos"] = table([u"組", u"profile", u"型", u"行", u"対応が付かない", u"対応が付く", u"id が同じ", u"届いた(文)", u"届いた(数)", u"同じ文・別の数", u"届かない", u"文が決まらない"], prow)
    B["cls"] = table([u"組", u"profile", u"型", u"行"] + list(WORDS6), crow)
    B["detail"] = table([u"組", u"profile", u"型", u"届いた: 数の位置が合う", u"届いた: 同じ文・別の数", u"届かない: 別の id", u"届かない: 同じ id・state が違う", u"届かない: 同じ id・state も同じ"], drow)
    B["match"] = table([u"組", u"profile", u"型", u"無改変: 値と字", u"無改変: 値だけ", u"注入後: 値と字", u"注入後: 値だけ", u"注入後: 付かない"], mrow)
    B["basestate"] = table([u"組", u"profile", u"型", u"行", u"基準が無改変から GROUNDED でない", u"うち注入後の state が無改変と同じ", u"うち届いた(文)"], brow)
    # 結果の語 × 分類(組 × profile。0 の組み合わせは出さない)
    wrow = []
    for g in GROUPS:
        for p in PROFILES:
            rs = rows_of(rec, g)
            sc = collections.Counter((r[u"profile"][p][u"結果"], cls(r, p)) for r in rs)
            for lab in LABELS:
                if sum(sc[(lab, w)] for w in WORDS6):
                    wrow.append([g, p, lab, str(sum(sc[(lab, w)] for w in WORDS6))] + [str(sc[(lab, w)]) for w in WORDS6])
    B["words"] = table([u"組", u"profile", u"結果の語", u"行"] + list(WORDS6), wrow)
    # 問い 3: 通した行と名指したが別の値の行のうち、届いていない行
    qrow = []
    for g in GROUPS:
        for p in PROFILES:
            rs = rows_of(rec, g)
            for lab in (L_PASS, L_OTHER):
                sel = [r for r in rs if r[u"profile"][p][u"結果"] == lab]
                reach = sum(1 for r in sel if cls(r, p) in (W_RS, W_RP))
                qrow.append([g, p, lab, str(len(sel)), str(reach), str(len(sel) - reach)])
    B["q3"] = table([u"組", u"profile", u"結果の語", u"行", u"うち届いた(文)", u"うち届いていない(届かない・決まらない・対応が付かない)"], qrow)
    # 読み直し(封 §2-4): 組 × 型 × profile。元の率と読み直した率の 2 本
    rr = []
    for g in GROUPS:
        for t in TYPES:
            orig, re_ = reread_sets(rec, g, t)
            for p in PROFILES:
                row = [g, TSHORT[t], p, str(len(orig)), str(len(re_))]
                for lab in (L_PASS, L_ORIG, L_OTHER):
                    row.append(rate(sum(1 for r in orig if r[u"profile"][p][u"結果"] == lab), len(orig)))
                    row.append(rate(sum(1 for r in re_ if r[u"profile"][p][u"結果"] == lab), len(re_)))
                rr.append(row)
    B["reread"] = table([u"組", u"型", u"profile", u"元の分母(4 profile の全部で対応が付く行)", u"読み直しの分母(4 profile の全部で届いた)", u"元: 通した率", u"読み直し: 通した率",
                         u"元: 名指して原本の値を返した率", u"読み直し: 名指して原本の値を返した率", u"元: 名指したが別の値の率", u"読み直し: 名指したが別の値の率"], rr)
    # 外に出した紙の 5 つの数(評価用 T8_REL)
    orig, re_ = reread_sets(rec, u"評価用", "T8_REL")
    prow5 = []
    for name, p, lab in ((u"通した率 P26", "P26", L_PASS), (u"通した率 P27", "P27", L_PASS), (u"名指して原本の値を返した率 P26", "P26", L_ORIG),
                         (u"名指して原本の値を返した率 P27", "P27", L_ORIG), (u"名指して原本の値を返した率 P27E", "P27E", L_ORIG)):
        prow5.append([name, rate(sum(1 for r in orig if r[u"profile"][p][u"結果"] == lab), len(orig)), rate(sum(1 for r in re_ if r[u"profile"][p][u"結果"] == lab), len(re_))])
    B["paper"] = table([u"評価用 T8_REL の数", u"元(分母 = 4 profile の全部で対応が付く行)", u"読み直し(分母 = 4 profile の全部で届いた)"], prow5)
    # 対応が付かない行(P22)
    urow = []
    for g in GROUPS:
        for t in TYPES:
            un = [r for r in rows_of(rec, g, t) if cls(r, "P22") == W_NOMAP]
            urow.append([g, TSHORT[t], str(len(un)), str(sum(1 for r in un if r[u"profile"]["P22"][u"届いた(文)"])), str(sum(1 for r in un if r[u"profile"]["P22"][u"token の文の番号"] is None))])
    B["unmapped"] = table([u"組", u"型", u"P22 で対応が付かない行", u"うち token の文 = 基準の claim の文", u"うち token の文が決まらない"], urow)
    # 位置で呼ぶ例: 組ごとに、どれかの profile で 届かない・決まらない・対応が付かない の行の先頭 8 行まで
    erow = []
    for g in GROUPS:
        k = 0
        for r in rows_of(rec, g):
            if any(cls(r, p) in (W_NS, W_NP, W_NOSENT, W_NOMAP) for p in PROFILES) and k < 8:
                k += 1
                x = r[u"profile"]["P22"]
                erow.append([plabel(pos[(g, r["docID"], r[u"注入の id"])]), r[u"基準の対応の付け方"], x[u"注入後の対応の付け方"], yesno(x[u"注入後の id が基準と同じ"]),
                             u"%s / %s" % (u"―" if x[u"token の文の番号"] is None else x[u"token の文の番号"], u"―" if x[u"基準の claim の文の番号"] is None else x[u"基準の claim の文の番号"])] +
                            [cls(r, p) for p in PROFILES])
    B["examples"] = table([u"位置", u"付け方(無改変)", u"付け方(注入後。P22)", u"注入後が基準と同じ id(P22)", u"文の番号(token / 基準。P22)"] + [u"%s の分類" % p for p in PROFILES], erow)
    order_of_doc = ("pred", "wiring", "counts", "docs", "engine", "pos", "cls", "detail", "match", "basestate", "words", "unmapped", "examples", "q3", "reread", "paper")
    assert sorted(order_of_doc) == sorted(B)
    return collections.OrderedDict((k, B[k]) for k in order_of_doc)


BLOCK_RE = re.compile(r"<!-- 門:start (\S+) -->\n(.*?)\n<!-- 門:end -->", re.S)


def doc_blocks(doc):
    out = collections.OrderedDict()
    for m in BLOCK_RE.finditer(doc):
        if m.group(1) in out:
            raise AssertionError(u"同じ名前の門の表が 2 つ: " + m.group(1))
        out[m.group(1)] = m.group(2).split(u"\n")
    return out


def check_c(rec, seal, doc):
    u"""文書の表を記録から作り直して比べる。問題の列。"""
    try:
        B = render_blocks(rec, seal)
    except Exception as e:      # 記録が壊れていれば作り直せない(それも赤)
        return [u"記録から表を作れない: %r" % (e,)]
    got = doc_blocks(doc)
    if list(got) != list(B):
        return [u"文書の門の表の名前と順が違う: %s" % list(got)]
    return [u"文書の表『%s』が記録から作った表と違う" % k for k, lines in B.items() if got[k] != lines]


def check_doc_prose(rec, seal, doc):
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
    J = judge(rec, seal)
    missed = [k for k, v in J.items() if v[1] is False]
    want = u"外れた予測: " + (u"・".join(missed) if missed else u"なし") + u"。外れは外れのまま残す(封も予測も直さない)。" + NOT_GATED
    if sum(1 for l in doc.split(u"\n") if l.strip() == want) != 1:
        out.append(u"『外れた予測』の行が記録から求めた当否と違う(期待: %s)" % want)
    undecided = [k for k, v in J.items() if v[1] is None]
    want2 = u"判定しない予測: " + u"・".join(undecided) + u"(当たりにも外れにも数えない)。" + NOT_GATED
    if undecided and sum(1 for l in doc.split(u"\n") if l.strip() == want2) != 1:
        out.append(u"『判定しない予測』の行が記録から求めた当否と違う(期待: %s)" % want2)
    if not undecided and u"判定しない予測:" in doc:
        out.append(u"判定しない予測が無いのに、その行がある")
    for lit in (u"記録は不変", u"配線の数", u"engine が止めた", u"仮説。測るまで断定しない", u"測っていない", u"診断だけ", NOT_GATED, u"edinetdb-p27", u"読み直し", u"2026-10-29"):
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
def all_docids(w):
    return [c["docID"] for c in w[u"会社"]]


def claim_ids(rec):
    ids = set()
    for r in rec[u"rows"]:
        ids.add(r[u"基準の claim"])
        for p in PROFILES:
            if r[u"profile"][p][u"注入後の claim の id"]:
                ids.add(r[u"profile"][p][u"注入後の claim の id"])
    return ids


def check_h(seal, doc, w, rec):
    out = []
    docs = all_docids(w)
    cids = claim_ids(rec)
    for name, t in ((u"封", seal), (u"文書", doc)):
        for d in docs:
            if d in t:
                out.append(u"%s に docID の字がある" % name)
        if re.findall(r"S100[0-9A-Z]{4}", t):
            out.append(u"%s に docID らしい字がある" % name)
        if re.findall(r"\b[NT]\d{3}\b", t):
            out.append(u"%s に claim の id らしい字がある" % name)
        for cid in cids:
            if re.search(r"(?<![0-9A-Za-z])%s(?![0-9A-Za-z])" % re.escape(cid), t):
                out.append(u"%s に記録の claim の id の字がある" % name)
                break
        if u"```" in t:
            out.append(u"%s に code fence がある" % name)
        for fw in FORBIDDEN:
            if fw in t:
                out.append(u"%s に禁止語: %s" % (name, fw))
    return out


def walk_keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            for x in walk_keys(v):
                yield x
    elif isinstance(o, list):
        for v in o:
            for x in walk_keys(v):
                yield x


def check_h_keys(rec):
    u"""記録の鍵が持てる欄の一覧に在り、持てない欄の名前でない。問題の列。"""
    keys = set(walk_keys(rec))
    out = []
    bad = sorted(k for k in keys if k in RECORD_KEYS_NG)
    if bad:
        out.append(u"記録に持てない欄の鍵がある: %s" % u"・".join(bad))
    extra = sorted(k for k in keys if k not in RECORD_KEYS_OK)
    if extra:
        out.append(u"記録に持てる欄の一覧に無い鍵がある(%d 個)" % len(extra))
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
        self.dir = tempfile.mkdtemp(prefix="p27reach_", dir=base)
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
        cls.ev, cls.tp, cls.ti = old_records()
        cls.w = rload(W_REL)
        cls.fetched = rload("fixtures/xbrl/fresh/fetched_2026-10-21.json")
        cls.seal = jtext(SEAL)

    def test_a_1_the_ids_equal_the_existing_records(self):
        self.assertEqual(check_a(self.rec, self.ev, self.tp, self.ti), [])
        self.assertEqual(len(rows_of(self.rec, u"評価用")), len(self.ev[u"行"]))
        self.assertEqual(len(rows_of(self.rec, u"調整用")), len(self.tp[u"行"]))

    def test_a_2_the_id_sets_are_read_from_the_records_not_hardcoded(self):
        ev = copy.deepcopy(self.ev)
        ev[u"行"].pop(7)
        self.assertNotEqual(check_a(self.rec, ev, self.tp, self.ti), [])
        ti = copy.deepcopy(self.ti)
        ti[u"行"][3]["id"] = ti[u"行"][3]["id"] + u"x"
        self.assertNotEqual(check_a(self.rec, self.ev, self.tp, ti), [])
        tp = copy.deepcopy(self.tp)
        tp[u"行"][2][u"P27"][u"結果"] = u"通した" if tp[u"行"][2][u"P27"][u"結果"] != u"通した" else u"対応が付かない"
        self.assertNotEqual(check_a(self.rec, self.ev, tp, self.ti), [])

    def test_b_1_the_wiring_gate_matches_every_row_and_every_pair(self):
        self.assertEqual(check_b(self.rec, self.ev, self.tp, self.ti, self.w, self.fetched), [])
        self.assertEqual(len(rows_of(self.rec, u"評価用")), 96)
        self.assertEqual(len(rows_of(self.rec, u"調整用")), 101)
        self.assertEqual(sum(self.rec[u"配線"][g][u"書類別の数えの組"] for g in GROUPS), 40)

    def test_b_2_the_record_is_the_full_run_and_has_no_leak(self):
        self.assertTrue(self.rec[u"全書類"])
        self.assertEqual(self.rec[u"key_leaks"], [])
        self.assertEqual(self.rec[u"頭"][u"cache"][u"開始"], self.rec[u"頭"][u"cache"][u"終了"])
        self.assertEqual(self.rec[u"頭"][u"DEFAULT_PROFILE"], "P27")
        self.assertEqual(self.rec[u"封"][u"期待する commit"], SEAL_COMMIT_SHORT)
        self.assertTrue(self.rec[u"封"][u"commit"].startswith(SEAL_COMMIT_SHORT))

    def test_e_1_the_classes_are_recomputed_from_the_fields(self):
        self.assertEqual(check_e(self.rec), [])

    def test_e_2_every_row_has_the_four_profiles_and_the_known_fields(self):
        for r in self.rec[u"rows"]:
            self.assertEqual(list(r[u"profile"]), list(PROFILES))
            self.assertEqual(("r" in r), r[u"型"] == "T8_REL")
            for p in PROFILES:
                self.assertIn(r[u"profile"][p][u"分類"], WORDS6)

    def test_e_3_the_six_words_cover_every_row_once(self):
        for g in GROUPS:
            for p in PROFILES:
                c = collections.Counter(cls(r, p) for r in rows_of(self.rec, g))
                self.assertEqual(sum(c.values()), len(rows_of(self.rec, g)))
                self.assertTrue(set(c) <= set(WORDS6))

    def test_e_4_the_base_is_grounded_in_p22_and_p26_for_every_row(self):
        u"""土台の条件(封 §0-3): 無改変で P22 と P26 の両方が GROUNDED。P27・P27E は条件に入らない(欄を持つ)。"""
        for r in self.rec[u"rows"]:
            self.assertEqual(r[u"profile"]["P22"][u"基準の claim の無改変の state"], "GROUNDED")
            self.assertEqual(r[u"profile"]["P26"][u"基準の claim の無改変の state"], "GROUNDED")

    def test_j_1_the_inputs_read_are_unchanged(self):
        self.assertEqual(check_j(self.rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"頭"][u"読んだ入力の sha256"][EVAL_INJ_REL] = u"0" * 64
        self.assertNotEqual(check_j(rec), [])
        rec = copy.deepcopy(self.rec)
        del rec[u"頭"][u"読んだ入力の sha256"][INPUT_RELS[4]]
        self.assertNotEqual(check_j(rec), [])

    def test_d_1_judgments_are_recomputed_and_cover_the_fourteen_predictions(self):
        J = judge(self.rec, self.seal)
        self.assertEqual(list(J), ["IR-%d" % i for i in range(1, 15)])
        self.assertTrue(all(v[1] in (True, False, None) for v in J.values()))

    def test_d_2_the_judge_is_not_a_constant(self):
        u"""記録の写しの 1 か所を変えると当否が変わる(IR-1 の配線の件数・IR-7 の通した・IR-9・IR-12・IR-13・IR-14)。"""
        J0 = judge(self.rec, self.seal)
        rec = copy.deepcopy(self.rec)
        rec[u"配線"][u"評価用"][u"一致"] -= 1
        self.assertTrue(J0["IR-1"][1] and not judge(rec, self.seal)["IR-1"][1])
        rec = copy.deepcopy(self.rec)
        m = [r for r in rows_of(rec, u"評価用", "T1_VALUE") if cls(r, "P22") == W_RS][0]
        m[u"profile"]["P22"][u"分類"] = W_NP
        self.assertTrue(J0["IR-12"][1] and not judge(rec, self.seal)["IR-12"][1])
        rec = copy.deepcopy(self.rec)
        m = [r for r in rows_of(rec, u"評価用", "T8_REL") if r[u"profile"]["P27"][u"結果"] != L_PASS][0]
        m[u"profile"]["P27"][u"結果"] = L_PASS
        m[u"profile"]["P27"][u"分類"] = W_RP
        J1 = judge(rec, self.seal)
        self.assertNotEqual(J1["IR-7"][0], J0["IR-7"][0])
        self.assertNotEqual(J1["IR-10"][0], J0["IR-10"][0])
        rec = copy.deepcopy(self.rec)
        rec[u"書類ごと"][0][u"文の数"]["P26"] += 1
        self.assertTrue(J0["IR-13"][1] and not judge(rec, self.seal)["IR-13"][1])
        rec = copy.deepcopy(self.rec)
        for r in rec[u"rows"]:
            if r[u"profile"]["P27"][u"基準の claim の無改変の state"] == "UNVERIFIABLE":
                r[u"profile"]["P27"][u"基準の claim の無改変の state"] = "GROUNDED"
        self.assertNotEqual(judge(rec, self.seal)["IR-14"][0], J0["IR-14"][0])
        rec = copy.deepcopy(self.rec)
        un = [r for r in rec[u"rows"] if cls(r, "P22") == W_NOMAP]
        self.assertTrue(un)
        un[0][u"profile"]["P22"][u"届いた(文)"] = not un[0][u"profile"]["P22"][u"届いた(文)"]
        self.assertNotEqual(judge(rec, self.seal)["IR-9"][0], J0["IR-9"][0])

    def test_reread_original_rates_equal_the_existing_records(self):
        u"""読み直しの表の『元』の列が既存の記録の結果の語の数と同じ(記録は不変。元の率は記録のまま)。"""
        for g, old in ((u"評価用", self.ev), (u"調整用", self.tp)):
            for p in PROFILES:
                want = collections.Counter(r[p][u"結果"] for r in old[u"行"])
                got = collections.Counter(r[u"profile"][p][u"結果"] for r in rows_of(self.rec, g))
                self.assertEqual(dict(want), dict(got), (g, p))


class EngineTest(unittest.TestCase):
    def test_f_1_engine_sha16_are_pinned_or_declared(self):
        rec = jload(REC)
        self.assertEqual(rec[u"頭"][u"engine sha16"], ENGINE_AT_MEASURE)
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
        cls.w = rload(W_REL)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def test_c_1_the_tables_equal_the_ones_rebuilt_from_the_record(self):
        self.assertEqual(check_c(self.rec, self.seal, self.doc), [])

    def test_c_2_the_prose_outside_the_tables_is_in_order(self):
        self.assertEqual(check_doc_prose(self.rec, self.seal, self.doc), [])

    def test_d_3_the_prediction_table_copies_the_seal_and_the_judgments(self):
        SP = seal_predictions(self.seal)
        J = judge(self.rec, self.seal)
        got = doc_blocks(self.doc)["pred"]
        self.assertEqual(len(got), 2 + len(J))
        for line, k in zip(got[2:], J):
            cells = [c.strip() for c in line.strip().strip(u"|").split(u" | ")]
            self.assertEqual(cells[0], u"**%s**" % k)
            self.assertEqual(tuple(cells[1:4]), SP[k], k)
            self.assertEqual(cells[4], J[k][0], k)
            self.assertEqual(cells[5], hit_word(J[k][1]), k)

    def test_d_4_the_seal_prediction_table_is_what_this_gate_reads(self):
        u"""封の表の形(幅の数は字で留めない。『幅が何本あるか』の形だけを見る)。"""
        SP = seal_predictions(self.seal)
        self.assertEqual(list(SP), ["IR-%d" % i for i in range(1, 15)])
        self.assertEqual([len(ranges_of(SP["IR-%d" % i][1])) for i in range(1, 15)], [0, 2, 1, 2, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0])
        self.assertEqual(len(singles_of(SP["IR-5"][1])), 1)
        self.assertEqual(len(singles_of(SP["IR-9"][1])), 1)

    def test_d_5_the_misses_are_kept_as_misses(self):
        J = judge(self.rec, self.seal)
        self.assertEqual([k for k, v in J.items() if v[1] is False], MISSES)
        self.assertEqual([k for k, v in J.items() if v[1] is None], UNDECIDED)
        self.assertEqual([k for k, v in J.items() if v[1] is True], [k for k in J if k not in MISSES and k not in UNDECIDED])

    def test_h_1_no_docid_and_no_claim_id_in_the_seal_and_the_document(self):
        self.assertEqual(check_h(self.seal, self.doc, self.w, self.rec), [])
        self.assertEqual(len(all_docids(self.w)), 20)

    def test_h_2_the_record_has_no_key_outside_the_allowed_list(self):
        self.assertEqual(check_h_keys(self.rec), [])
        txt = jtext(REC)
        self.assertTrue(all(d in txt for d in all_docids(self.w)))          # 記録は 20 書類の docID を持つ ― だから引きの門に宣言する
        fresh_seal = jtext(os.path.join(HERE, "test_xbrl_fresh_seal.py"))
        for p in (REC_REL, SCRIPT_REL, GATE_REL):
            self.assertIn(u'"%s"' % p, fresh_seal, p)

    def test_doc_states_the_dated_note_about_the_original_rates(self):
        self.assertIn(u"2026-10-29", self.doc)
        self.assertIn(u"eval_inject_2026-10-27.json", self.doc)


class ScriptTest(unittest.TestCase):
    def test_script_does_not_remeasure_when_the_output_exists(self):
        before = hashlib.sha256(open(REC, "rb").read()).hexdigest()
        env = dict((k, v) for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "EDINET_API_KEY", "EDINETDB_API_KEY"))
        r = subprocess.run(["python3", SCRIPT, "--out", REC], cwd=ROOT, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        self.assertIn(u"測り直さない", r.stdout)
        self.assertEqual(hashlib.sha256(open(REC, "rb").read()).hexdigest(), before)

    def test_script_refuses_docs_for_the_evaluation_set(self):
        u"""評価用は --docs を受け付けない(本番の 1 回だけ全書類)。出力が無い path を渡しても、文を開く前に止まる。"""
        out = os.path.join(tempfile.mkdtemp(prefix="p27reach_out_", dir=os.environ.get("TMPDIR")), "x.json")
        env = dict((k, v) for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "EDINET_API_KEY", "EDINETDB_API_KEY"))
        r = subprocess.run(["python3", SCRIPT, "--docs", "1", "--out", out], cwd=ROOT, capture_output=True, text=True, env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(os.path.exists(out))
        shutil.rmtree(os.path.dirname(out), ignore_errors=True)


class FalseRecordsAreRedTest(unittest.TestCase):
    u"""(g) 偽物で赤: 記録の写しを 1 か所変えると (b)(c)(e) が赤になる(変異)。"""

    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.ev, cls.tp, cls.ti = old_records()
        cls.w = rload(W_REL)
        cls.fetched = rload("fixtures/xbrl/fresh/fetched_2026-10-21.json")
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def b(self, rec):
        return check_b(rec, self.ev, self.tp, self.ti, self.w, self.fetched)

    def test_g_0_baseline_is_green(self):
        self.assertEqual(self.b(self.rec), [])
        self.assertEqual(check_c(self.rec, self.seal, self.doc), [])
        self.assertEqual(check_e(self.rec), [])

    def test_g_1_changing_one_class_turns_e_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in rows_of(rec, u"評価用", "T8_REL") if cls(x, "P26") == W_RS][0]
        r[u"profile"]["P26"][u"分類"] = W_NP
        self.assertNotEqual(check_e(rec), [])
        self.assertNotEqual(check_c(rec, self.seal, self.doc), [])
        self.assertEqual(self.b(rec), [])                       # b は分類を見ない(1 つの性質は所有する 1 か所で)

    def test_g_2_changing_one_sentence_number_turns_e_red(self):
        for key in (u"token の文の番号", u"基準の claim の文の番号"):
            rec = copy.deepcopy(self.rec)
            r = [x for x in rec[u"rows"] if x[u"profile"]["P22"][u"届いた(文)"]][0]
            r[u"profile"]["P22"][key] += 1
            self.assertNotEqual(check_e(rec), [], key)             # 文の番号を所有するのは (e)(表は旗と件数だけを見る)

    def test_g_3_changing_the_id_flag_turns_e_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = rec[u"rows"][0]
        r[u"profile"]["P22"][u"注入後の id が基準と同じ"] = not r[u"profile"]["P22"][u"注入後の id が基準と同じ"]
        self.assertNotEqual(check_e(rec), [])
        self.assertNotEqual(check_c(rec, self.seal, self.doc), [])
        rec = copy.deepcopy(self.rec)
        r = rec[u"rows"][0]
        r[u"profile"]["P22"][u"注入後の claim の id"] = r[u"profile"]["P22"][u"注入後の claim の id"] + u"x"
        self.assertNotEqual(check_e(rec), [])

    def test_g_4_changing_the_wiring_flag_turns_b_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"配線の行ごと"][0][u"一致"] = False
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線"][u"調整用"][u"一致"] -= 1
        self.assertNotEqual(self.b(rec), [])
        self.assertNotEqual(check_c(rec, self.seal, self.doc), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線"][u"評価用"][u"書類別の数えが一致した組"] -= 1
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"書類ごと"][0][u"書類別の数え"]["T1_VALUE"][u"採った"] += 1
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線"][u"評価用"][u"包みの呼ばれた回数"] -= 1
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線"][u"調整用"][u"round-trip"] -= 1
        self.assertNotEqual(self.b(rec), [])

    def test_g_5_changing_the_matching_kind_turns_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in rec[u"rows"] if x[u"profile"]["P22"][u"注入後の対応の付け方"] == K_BOTH][0]
        r[u"profile"]["P22"][u"注入後の対応の付け方"] = K_VALUE
        self.assertNotEqual(check_c(rec, self.seal, self.doc), [])
        rec = copy.deepcopy(self.rec)
        r = [x for x in rec[u"rows"] if x[u"基準の対応の付け方"] == K_BOTH][0]
        r[u"基準の対応の付け方"] = K_VALUE
        self.assertNotEqual(check_c(rec, self.seal, self.doc), [])

    def test_g_6_one_character_of_the_document_table_turns_c_red(self):
        for name in ("cls", "pos", "reread", "counts", "words", "q3"):
            i = self.doc.index(u"<!-- 門:start %s -->" % name)
            j = self.doc.index(u"<!-- 門:end -->", i)
            seg = self.doc[i:j]
            s0 = seg.index(u"\n|---")
            k = re.search(r"\| (\d+) \|", seg[s0:])
            self.assertIsNotNone(k, name)
            seg2 = seg[:s0 + k.start(1)] + str(int(k.group(1)) + 1) + seg[s0 + k.end(1):]
            doc = self.doc[:i] + seg2 + self.doc[j:]
            self.assertNotEqual(doc, self.doc)
            self.assertNotEqual(check_c(self.rec, self.seal, doc), [], name)
        i = self.doc.index(u"<!-- 門:start pred -->")
        doc = self.doc[:i] + self.doc[i:].replace(u"**当たり**", u"**外れ**", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(check_c(self.rec, self.seal, doc), [])

    def test_g_7_changing_a_prediction_character_of_the_seal_turns_d_and_c_red(self):
        u"""封の予測の 1 字(IR-1 の評価用の行数)を変えると、当否の判定が変わり(d)、文書の表の写しとも合わなくなる(c)。"""
        seal = u"\n".join(l.replace(u"評価用 96 / 96 行", u"評価用 96 / 95 行", 1) if l.startswith(u"| **IR-1**") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(judge(self.rec, seal)["IR-1"], judge(self.rec, self.seal)["IR-1"])
        self.assertNotEqual(check_c(self.rec, seal, self.doc), [])
        seal = u"\n".join(l.replace(u"**0 以上 2 以下**", u"**0 以上 1 以下**", 1) if l.startswith(u"| **IR-3**") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(check_c(self.rec, seal, self.doc), [])

    def test_g_8_a_docid_or_a_claim_id_in_the_document_turns_h_red(self):
        doc = self.doc + u"\n" + all_docids(self.w)[0] + u"\n"
        self.assertNotEqual(check_h(self.seal, doc, self.w, self.rec), [])
        doc = self.doc + u"\nN012\n"
        self.assertNotEqual(check_h(self.seal, doc, self.w, self.rec), [])
        doc = self.doc + u"\n%s\n" % self.rec[u"rows"][0][u"基準の claim"]
        self.assertNotEqual(check_h(self.seal, doc, self.w, self.rec), [])
        seal = self.seal + u"\n" + all_docids(self.w)[-1] + u"\n"
        self.assertNotEqual(check_h(seal, self.doc, self.w, self.rec), [])

    def test_g_9_an_unmarked_number_in_prose_turns_the_prose_check_red(self):
        doc = self.doc + u"\n通した行は 7 行だった。\n"
        self.assertNotEqual(check_doc_prose(self.rec, self.seal, doc), [])

    def test_g_10_changing_the_hit_word_in_the_prose_turns_the_prose_check_red(self):
        doc = self.doc.replace(u"外れた予測: ", u"外れた予測: IR-99・", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(check_doc_prose(self.rec, self.seal, doc), [])

    def test_g_11_a_key_the_record_may_not_hold_turns_h_red(self):
        for key in (u"pointers", u"value", u"span", u"元の字", u"新しい値", u"数の字"):
            rec = copy.deepcopy(self.rec)
            rec[u"rows"][0][u"profile"]["P22"][key] = u"x"
            self.assertNotEqual(check_h_keys(rec), [], key)
        rec = copy.deepcopy(self.rec)
        rec[u"rows"][0][u"新しい欄"] = 1
        self.assertNotEqual(check_h_keys(rec), [])


# ----------------------------------------------------------------------------------------------------------------
# 包みの門(作り物の backend で通す。engine は呼ばない)
def load_script():
    spec = importlib.util.spec_from_file_location("p27_reach_script_under_test", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


BIG_TEXT = u"大きい文\n" + u"\n".join(u"・項目%d は%s百万円だった。" % (i, "{:,}".format(i * 1000)) for i in range(1, 41))
BIG_FACTS = [{"name": "jppfs_cor:Item%02d" % i, "context": "CurrentYearDuration", "unit": "JPY", "decimals": "-6", "value": float(i * 1000) * 1e6} for i in range(1, 41)]


class FakeCtx(object):
    u"""``inject_doc`` が使う口だけを持つ作り物(文・ZIP は使い捨て folder)。"""

    def __init__(self, tmp, doc):
        self.doc = doc
        self.text = BIG_TEXT
        self.zb = json.dumps({"facts": BIG_FACTS}).encode("utf-8")
        self.path = os.path.join(tmp, doc + ".zip")
        with open(self.path, "wb") as fh:
            fh.write(self.zb)
        self.styles = {doc: "A"}
        self.report_sha = {doc: hashlib.sha256(self.text.encode("utf-8")).hexdigest()}

    def read_report(self, doc):
        return self.text, self.text.encode("utf-8")

    def read_zip(self, doc):
        return self.zb

    def zip_path(self, doc):
        return self.path


class WrapGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.M = load_script()

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p27reach_wrap_", dir=os.environ.get("TMPDIR"))
        self.M.T.PROFILES = PROFILES
        self.ctx = FakeCtx(self.tmp, "ZZ0DOC01")

    def tearDown(self):
        self.M.T.PROFILES = ("P22", "P26")
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _observe_for(self, inner):
        return lambda zb, p, t: (inner.verify(zb, p, t), {}, [])

    def _run(self, name, wrapper_factory):
        w = os.path.join(self.tmp, name)
        os.makedirs(w)
        return self.M.wrap_gate_problems(self.ctx, self.M.T.StubBackend, "ZZ0DOC01", "test-seed", w, self._observe_for, wrapper_factory)

    def test_g_12_the_wrapper_keeps_the_return_values_byte_for_byte(self):
        chk = os.path.join(self.tmp, "chk")
        os.makedirs(chk)
        rows = self.M.T.inject_doc(self.ctx, self.M.T.StubBackend(), "ZZ0DOC01", "test-seed", chk, self.M.T.INJECT_CAP)
        self.assertEqual(set(r[u"型"] for r in rows[0]), set(TYPES))
        self.assertTrue(rows[0], u"作り物の材料で注入の行が 0 件(門が空振りになる)")
        self.assertEqual(self._run("a", self.M.make_wrapper), [])

    def test_g_13_a_wrapper_that_changes_the_return_value_is_red(self):
        orig_factory = self.M.make_wrapper

        def evil(orig, calls):
            inner = orig_factory(orig, calls)

            def wrap(claims, inj, unit):
                r = inner(claims, inj, unit)
                return None if inj["type"] == "T8_REL" else r
            return wrap
        self.assertNotEqual(self._run("b", evil), [])

    def test_g_14_a_wrapper_that_returns_a_copy_is_red(self):
        orig_factory = self.M.make_wrapper

        def copier(orig, calls):
            inner = orig_factory(orig, calls)

            def wrap(claims, inj, unit):
                r = inner(claims, inj, unit)
                return copy.deepcopy(r)
            return wrap
        probs = self._run("c", copier)
        self.assertNotEqual(probs, [])

    def test_g_15_the_attribute_is_restored_even_when_the_run_raises(self):
        orig = self.M.T.claim_for_p27

        class Boom(self.M.T.StubBackend):
            def verify(self, zb, profile, text):
                raise RuntimeError("boom")
        w = os.path.join(self.tmp, "d")
        os.makedirs(w)
        with self.assertRaises(RuntimeError):
            self.M.run_wrapped(self.ctx, Boom(), "ZZ0DOC01", "test-seed", w, lambda zb, p, t: (Boom().verify(zb, p, t), {}, []))
        self.assertIs(self.M.T.claim_for_p27, orig)

    def test_work_doc_runs_with_a_stub_and_counts_four_calls_per_row(self):
        class Tap(object):
            def __enter__(s):
                stub = self.M.T.StubBackend()
                return lambda zb, p, t: (stub.verify(zb, p, t), {}, [])

            def __exit__(s, *a):
                return False
        w = os.path.join(self.tmp, "e")
        os.makedirs(w)
        obs, rows, counts, ncalls, info = self.M.work_doc(self.ctx, self.M.T.StubBackend(), Tap, "ZZ0DOC01", "test-seed", w)
        self.assertTrue(rows)
        self.assertEqual(ncalls, 4 * len(rows))
        self.assertEqual([o[u"注入の id"] for o in obs], [r["id"] for r in rows])
        self.assertTrue(info[u"claim の一覧の id() が控えに在る"])
        for o in obs:
            self.assertEqual(list(o[u"profile"]), list(PROFILES))
            for p in PROFILES:
                self.assertIn(o[u"profile"][p][u"分類"], WORDS6)

    def test_wiring_check_flags_a_changed_field_by_name_only(self):
        rows = [{"docID": "ZZ0DOC01", "id": "a-1", u"型": "T1_VALUE", u"文体": "A", u"基準の claim": "N001", "P22": {"x": 1}, "P26": {"x": 1}}]
        old = [dict(rows[0])]
        flags, same, n_pair, n_ok, problems = self.M.wiring_check(rows, {"ZZ0DOC01": {"T1_VALUE": {"a": 1}, "T8_REL": {"a": 2}}}, {"o": (old, {"ZZ0DOC01": {"T1_VALUE": {"a": 1}, "T8_REL": {"a": 2}}}, ("P22", "P26"))}, {"ZZ0DOC01"}, u"調整用")
        self.assertEqual((same, n_pair, n_ok, problems), (True, 2, 2, []))
        old[0]["P26"] = {"x": 2}
        flags, same, n_pair, n_ok, problems = self.M.wiring_check(rows, {"ZZ0DOC01": {"T1_VALUE": {"a": 1}, "T8_REL": {"a": 3}}}, {"o": (old, {"ZZ0DOC01": {"T1_VALUE": {"a": 1}, "T8_REL": {"a": 2}}}, ("P22", "P26"))}, {"ZZ0DOC01"}, u"調整用")
        self.assertFalse(flags[0][u"一致"])
        self.assertEqual(n_ok, 1)
        self.assertEqual(problems[0][2], [u"P26(o)"])


class ScriptGuardTest(unittest.TestCase):
    u"""script の守り(配線の門が見る欄・記録に持てる欄の一覧)が、1 欄ずつ効いていること。"""

    @classmethod
    def setUpClass(cls):
        cls.M = load_script()

    def test_wiring_check_flags_every_field_it_is_meant_to_check(self):
        u"""封 §2-1 の欄(型・文体・基準の claim・r・r を決めた回)を 1 つずつ変えると、配線の門は不一致の欄の名前を返す(script の一覧とは別に、この門が一覧を持つ)。"""
        base = {"docID": "ZZ0DOC01", "id": "a-1", u"型": "T8_REL", u"文体": "A", u"基準の claim": "N001", "r": 0.03, u"r を決めた回": 1, "P22": {"x": 1}, "P26": {"x": 1}}
        cnt = {"ZZ0DOC01": {"T1_VALUE": {"a": 1}, "T8_REL": {"a": 2}}}
        for f, other in ((u"型", "T1_VALUE"), (u"文体", "B"), (u"基準の claim", "N002"), ("r", 0.1), (u"r を決めた回", 2)):
            old = dict(base)
            old[f] = other
            flags, same, n_pair, n_ok, problems = self.M.wiring_check([dict(base)], cnt, {"o": ([old], cnt, ("P22", "P26"))}, {"ZZ0DOC01"}, u"調整用")
            self.assertFalse(flags[0][u"一致"], f)
            self.assertEqual(problems[0][2], [u"%s(o)" % f], f)
        old = dict(base)
        del old["r"]
        flags, _s, _p, _o, problems = self.M.wiring_check([dict(base)], cnt, {"o": ([old], cnt, ("P22", "P26"))}, {"ZZ0DOC01"}, u"調整用")
        self.assertFalse(flags[0][u"一致"])                                  # 欄の有る無しも違い
        flags, same, _p, _o, problems = self.M.wiring_check([dict(base)], cnt, {"o": ([dict(base)], cnt, ("P22", "P26"))}, {"ZZ0DOC01"}, u"調整用")
        self.assertEqual((flags[0][u"一致"], same, problems), (True, True, []))
        flags, same, _p, _o, problems = self.M.wiring_check([dict(base)], cnt, {"o": ([dict(base, id="a-2")], cnt, ("P22", "P26"))}, {"ZZ0DOC01"}, u"調整用")
        self.assertFalse(same)                                               # (docID, id) の集合が違う

    def test_script_stops_on_a_key_outside_the_allowed_list(self):
        with self.assertRaises(SystemExit):
            self.M.assert_allowed_keys({u"rows": [{u"新しい欄": 1}]})
        with self.assertRaises(SystemExit):
            self.M.assert_allowed_keys({u"rows": [{u"pointers": [u"x"]}]})
        self.M.assert_allowed_keys({u"rows": [{u"注入の id": u"x", u"profile": {u"P22": {u"分類": u"x"}}}]})            # 持てる欄だけなら通る

    def test_script_stops_on_a_forbidden_key_even_if_listed(self):
        u"""段 1 の assert_record_clean(span・subject・value・recomputed)は script が書く前に当てる。"""
        with self.assertRaises(SystemExit):
            self.M.T.assert_record_clean({u"rows": [{u"value": 1.0}]})

    def test_the_script_does_not_name_a_document_id(self):
        txt = jtext(SCRIPT)
        w = rload(W_REL)
        for d in all_docids(w):
            self.assertNotIn(d, txt)
        self.assertEqual(re.findall(r"S100[0-9A-Z]{4}", txt), [])


class OrderTest(unittest.TestCase):
    u"""(i) 封の commit が script・記録・文書・門の commit より前。"""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="p27reach_root_", dir=os.environ.get("TMPDIR"))
        cls.grun = staticmethod(make_run(REPO))

    def _p(self, steps):
        t = build(self.base, steps)
        return order_problems(t.run, "")

    def test_i_1_the_real_history_has_the_seal_before_the_four_files(self):
        u"""script・記録・文書・門のどれかが未 commit なら赤(足した commit が無い)。4 つとも commit された後で初めて緑。"""
        self.assertEqual(order_problems(self.grun, PREFIX), [])

    def test_i_2_the_real_seal_is_one_commit_and_an_ancestor_of_head(self):
        lst = added_commits(self.grun, PREFIX + SEAL_REL)
        self.assertEqual(len(lst), 1)
        self.assertTrue(lst[0].startswith(SEAL_COMMIT_SHORT))
        self.assertTrue(is_anc(self.grun, lst[0], "HEAD"))

    def test_i_3_a_correct_order_is_green(self):
        self.assertEqual(self._p(["SEAL", "SCRIPT", "RECORD", "DOC", "GATE"]), [])
        self.assertEqual(self._p(["SEAL", "ALL4"]), [])
        self.assertEqual(self._p(["SEAL", "ALL4", "SEAL_APPEND"]), [])               # 日付つきの追記(削除 0)は許される

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
