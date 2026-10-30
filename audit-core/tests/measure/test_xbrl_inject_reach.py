# -*- coding: utf-8 -*-
u"""注入 741 行の全部で「差し替えが基準の claim に届いたか」を数える診断の門 ― 封 docs/XBRL_INJECT_REACH_DIAG_SEAL_2026-10-28.md §5-2 の (a)〜(j)。

記録 ``fixtures/xbrl/inject_reach_2026-10-28.json``(``measure/xbrl_inject_reach_2026-10-28.py`` の出力)・文書 ``docs/XBRL_INJECT_REACH_DIAG_2026-10-28.md``。

  (a) 記録の 741 行の id が ``fresh_2026-10-21.json`` の ``注入の行`` の id と集合で同じ(字で留めない)。型別の数・行の 4 欄・結果(P22〜P26)も記録と同じ。
  (b) 配線の門が 741 / 741 と ``注入の件数(書類別)`` 120 組の一致で記録されている(行ごとの旗・書類ごとの数・材料の sha256 を記録から数え直す)。
  (c) 文書の表を記録から作り直して 1 行も違わない(``<!-- 門:start 名前 -->`` の中)。門の外の散文の数には【門なし】の印が要る。
  (d) R-1〜R-14 の当否を記録から求め(幅は封の表の字から読む。字で留めない)、封の字(予測・外れ方)と、文書の当否の表の字が一致する。
  (e) 分類(封 §2-3)を、記録の欄から別の書き方で求め直して一致する(届いた(文)・届いた(数)・T3 の届いた、の 3 つとも)。
  (f) engine の sha16 を留める(宣言された遷移の型: 値が宣言の値のときだけ、その封が履歴に在ること)。
  (g) 偽物で赤: 記録の写しの分類・文の番号・配線の旗・対応の付け方を 1 か所変えると (b)(c)(e) が赤になる。文書の表の 1 字で (c) が赤、封の予測の 1 字で (d)(c) が赤。
  (h) 封と文書に 30 書類の docID の字(``fetched_2026-10-21.json`` の「使う書類」から読む)も claim の id の字も無い。
  (i) 封の commit が script・記録・文書・門の commit より前(git の commit の順)。
  (j) 記録が持つ ``fresh_2026-10-21.json``・``fetched_2026-10-21.json`` の sha256 がいまの file と一致する(読み直しの元が不変)。

**(i) は、script・記録・文書・門のどれかが commit される前は赤になる**(追跡されていない file には『足した commit』が無い)。前例 ``test_xbrl_t2_pass_diag.py`` と同じ扱い。skip にしない。
使い捨ての git repo で、順序が正しければ緑・違反はそれぞれ特定の符号で赤になることを確かめる。

**変数名について**: 過去の門が tests/measure の行頭の名前(``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``)を数えるので、この門はそれらを行頭に置かない。
この file は docID の字を持たない(``fetched_2026-10-21.json`` から読む)。
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

SEAL_REL = "docs/XBRL_INJECT_REACH_DIAG_SEAL_2026-10-28.md"
DOC_REL = "docs/XBRL_INJECT_REACH_DIAG_2026-10-28.md"
REC_REL = "fixtures/xbrl/inject_reach_2026-10-28.json"
SCRIPT_REL = "measure/xbrl_inject_reach_2026-10-28.py"
GATE_REL = "tests/measure/test_xbrl_inject_reach.py"
FRESH_REL = "fixtures/xbrl/fresh/fresh_2026-10-21.json"
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
SEAL, DOC, REC = [os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL)]
FRESH_REC = os.path.join(ROOT, FRESH_REL)
FETCHED = os.path.join(ROOT, FETCHED_REL)
SCRIPT = os.path.join(ROOT, SCRIPT_REL)
SEAL_COMMIT_SHORT = "df5c215"
PROFILES5 = ("P22", "P23", "P24", "P25", "P26")
OBS = ("P22", "P26", "P27")
ALL6 = ("P22", "P23", "P24", "P25", "P26", "P27")
MAIN_TYPES = ("T1_VALUE", "T2_UNIT", "T5_COINCIDENT")
ALL_TYPES = MAIN_TYPES + ("T3_ABSENT",)
TSHORT = {"T1_VALUE": u"T1", "T2_UNIT": u"T2", "T5_COINCIDENT": u"T5", "T3_ABSENT": u"T3"}
NOT_GATED = u"【門なし】"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
FORBIDDEN = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")

W_NOMAP, W_NOSENT = u"(対応が付かない)", u"(文が 1 つに決まらない)"
W_RS, W_RP, W_NS, W_NP = u"(届いた・止めた)", u"(届いた・通した)", u"(届かない・止めた)", u"(届かない・通した)"
WORDS6 = (W_NOMAP, W_NOSENT, W_RS, W_RP, W_NS, W_NP)
K_BOTH, K_VALUE = u"値と字", u"値だけ"
D_NUM, D_OTHER = u"数の位置が合う", u"同じ文・別の数"
D_DIFFID, D_MOVED, D_SAME = u"注入後の claim が基準と別の id", u"同じ id・state が無改変と違う", u"同じ id・state も無改変と同じ"

#: engine の sha16(記録を測った時点の値。字で留める ― 測った事実)。変えるなら宣言された遷移として下の ENGINE_DECLARED に足す。
ENGINE_AT_MEASURE = {
    "adapters/xbrl/extract.py": "3cf55966f12919f0", "adapters/xbrl/vocabulary.py": "514ebb8104451c07", "adapters/xbrl/recipes.py": "52d645e713c53c1c",
    "adapters/xbrl/resolve.py": "a41043763c1d4073", "adapters/xbrl/comparators.py": "d8706338325e725b", "adapters/xbrl/verify_document.py": "c3791080ab5aef2f",
}
#: 宣言された遷移 {file: (遷移の後の sha16, その遷移を宣言した封)}。今は 0 件(この診断の commit 時点で engine は測った時点のまま)。
#: 足すときは、封が履歴に在り、値が宣言の値のときだけ受け入れる(tests/measure/test_xbrl_t2_pass_diag.py の型)。測った時点の値は消さない。
# 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。この 6 本のうち動くのは vocabulary.py(旗 1 つ・P27C・PROFILES の登録)と
# verify_document.py(Claim の欄 candidate)。測った時点の値は ENGINE_AT_MEASURE に残す。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
ENGINE_DECLARED = {"adapters/xbrl/vocabulary.py": ("7fbcfbf0e472f366", "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md"),
                   "adapters/xbrl/verify_document.py": ("6c76c8ade6c7b1c8", "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md")}

#: 記録から求めた当否のうち外れ・判定しないの名前(測った事実。外れは外れのまま残す。封も予測も直さない)。記録から求めた当否と食い違えば d_5 が赤。
#: 今回は 14 本とも当たりで、外れも判定しないも 0 本(R-3 と R-8 は幅の下限に当たった)。
MISSES = []
UNDECIDED = []


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    return json.loads(jtext(p))


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


def outcome(state):
    u"""state -> 通した / 違う / 要確認 / 対応が付かない(None)。測定の outcome_of と同じ表を、ここで別に持つ。"""
    if state is None:
        return u"対応が付かない"
    return {"GROUNDED": u"通した", "VALUE_MISMATCH": u"違う", "POINTER_NOT_FOUND": u"要確認", "UNVERIFIABLE": u"要確認"}[state]


def rate(a, b):
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b) if b else u"%d / 0" % a


def table(head, rows):
    lines = [u"| " + u" | ".join(head) + u" |", u"|" + u"|".join(u"---" for _ in head) + u"|"]
    for r in rows:
        lines.append(u"| " + u" | ".join(str(c) for c in r) + u" |")
    return lines


def mains(rec):
    return [r for r in rec[u"rows"] if r[u"型"] in MAIN_TYPES]


def t3s(rec):
    return [r for r in rec[u"rows"] if r[u"型"] == "T3_ABSENT"]


def of_type(rec, t):
    return [r for r in rec[u"rows"] if r[u"型"] == t]


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


# ----------------------------------------------------------------------------------------------------------------
# (e) 分類を別の書き方で求め直す(記録の欄だけから。記録の 分類 の欄・届いた の欄は読まない)
def reclass_main(x):
    u"""T1・T2・T5 の 1 行・1 profile: (分類, 届いた(文), 届いた(数), 細目, 結果の語)。"""
    after, base = x[u"注入後"][u"claim"], x[u"無改変"][u"claim"]
    tsent, toff = x[u"token"][u"文の番号"], x[u"token"][u"文の中で最初に違う位置"]
    reached = tsent is not None and base is not None and x[u"無改変"][u"文の番号"] == tsent
    st, en = x[u"無改変"][u"数の始まり"], x[u"無改変"][u"数の終わり"]
    num = bool(reached and st is not None and en is not None and toff is not None and st <= toff <= en + 2)
    word = outcome(None if after is None else after[u"state"])
    if after is None:
        cls = W_NOMAP
    elif tsent is None:
        cls = W_NOSENT
    elif reached:
        cls = W_RP if after[u"state"] == "GROUNDED" else W_RS
    else:
        cls = W_NP if after[u"state"] == "GROUNDED" else W_NS
    det = None
    if cls in (W_RS, W_RP):
        det = D_NUM if num else D_OTHER
    elif cls == W_NS:
        if after[u"id"] != (base or {}).get(u"id"):
            det = D_DIFFID
        else:
            same = x[u"注入後"][u"無改変の同じ id の state"] == after[u"state"]
            det = D_SAME if same else D_MOVED
    return cls, reached, num, det, word


def reclass_t3(x):
    u"""T3 の 1 行・1 profile: (分類, 届いた, 結果の語)。"""
    c = x[u"claim"]
    idx = x[u"挿入した文の番号"]
    reached = bool(idx is not None and c is not None and x[u"注入後の claim の文の番号"] == idx)
    word = outcome(None if c is None else c[u"state"])
    if c is None:
        return W_NOMAP, reached, word
    if idx is None:
        return W_NOSENT, reached, word
    if reached:
        return (W_RP if c[u"state"] == "GROUNDED" else W_RS), reached, word
    return (W_NP if c[u"state"] == "GROUNDED" else W_NS), reached, word


def check_e(rec):
    u"""問題の列(空なら通す)。"""
    out = []
    for r in rec[u"rows"]:
        if list(r[u"profile"]) != list(OBS):
            out.append(u"%s: profile の欄が %s でない" % (r["id"], list(OBS)))
            continue
        for p in OBS:
            x = r[u"profile"][p]
            if r[u"型"] == "T3_ABSENT":
                cls, reached, word = reclass_t3(x)
                if cls != x[u"分類"]:
                    out.append(u"%s %s: 分類が求め直しと違う(%s != %s)" % (r["id"], p, x[u"分類"], cls))
                if reached != x[u"届いた"]:
                    out.append(u"%s %s: 届いた(T3)が求め直しと違う" % (r["id"], p))
            else:
                cls, reached, num, det, word = reclass_main(x)
                if cls != x[u"分類"]:
                    out.append(u"%s %s: 分類が求め直しと違う(%s != %s)" % (r["id"], p, x[u"分類"], cls))
                if reached != x[u"届いた(文)"]:
                    out.append(u"%s %s: 届いた(文)が求め直しと違う" % (r["id"], p))
                if num != x[u"届いた(数)"]:
                    out.append(u"%s %s: 届いた(数)が求め直しと違う" % (r["id"], p))
                if det != x[u"細目"]:
                    out.append(u"%s %s: 細目が求め直しと違う" % (r["id"], p))
                if x[u"無改変"][u"対応の付け方"] not in (K_BOTH, K_VALUE, u"対応が付かない") or x[u"注入後"][u"対応の付け方"] not in (K_BOTH, K_VALUE, u"対応が付かない"):
                    out.append(u"%s %s: 対応の付け方の語が知らない語" % (r["id"], p))
                if not (x[u"無改変"][u"枝が本物の _find_base_claim と同じ"] and x[u"注入後"][u"枝が本物の claim_for と同じ"]):
                    out.append(u"%s %s: 対応の枝が本物と同じでない旗" % (r["id"], p))
            if word != x[u"結果"]:
                out.append(u"%s %s: 結果の語が claim の state と違う(%s != %s)" % (r["id"], p, x[u"結果"], word))
            if r[u"結果(P22〜P27)"][p] != x[u"結果"]:
                out.append(u"%s %s: 行の 結果(P22〜P27) と profile の結果が違う" % (r["id"], p))
            if x[u"分類"] not in WORDS6:
                out.append(u"%s %s: 分類の語が 6 語に無い" % (r["id"], p))
    return out


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
        for p in PROFILES5:
            if f[u"結果"][p] != r[u"結果の state・reason(P22〜P27)"][p]:
                out.append(u"%s: 結果 %s が fresh の行と違う" % (r["id"], p))
            if outcome((f[u"結果"][p] or [None])[0]) != r[u"結果(P22〜P27)"][p]:
                out.append(u"%s: 結果の語 %s が fresh と違う" % (r["id"], p))
    ty = collections.Counter(r[u"型"] for r in rec[u"rows"])
    if dict(ty) != fr[u"D"][u"型別の注入"] or len(rec[u"rows"]) != fr[u"D"][u"注入"]:
        out.append(u"型別の数が fresh の D と違う")
    if rec[u"配線の行ごと"] and [w["id"] for w in rec[u"配線の行ごと"]] != [r["id"] for r in rec[u"rows"]]:
        out.append(u"配線の行ごとの id が rows と違う")
    return out


def check_b(rec, fr, fetched):
    out = []
    g = rec[u"配線の門"]
    n = len(fr[u"注入の行"])
    if not rec[u"全書類"]:
        out.append(u"全書類の記録でない(試走の記録)")
    if not (g[u"通った"] and g[u"行"] == g[u"一致"] == n == len(rec[u"配線の行ごと"]) == g[u"記録の注入の行(対象の書類)"]):
        out.append(u"配線の門が %d / %d でない(行 %s・一致 %s)" % (n, n, g[u"行"], g[u"一致"]))
    if not g[u"id の集合が記録と同じ"]:
        out.append(u"配線の門の id の集合の旗が偽")
    for w in rec[u"配線の行ごと"]:
        f = w[u"一致"]
        if not all(f[k] for k in (u"記録に同じ id の行が在る", u"元の字", u"後の字", u"基準の claim", u"結果(P22〜P26)", u"4 欄とも一致")):
            out.append(u"%s: 4 欄のどれかが一致していない" % w["id"])
    docs = rec[u"書類(出てくる順)"]
    if docs != list(fetched[u"使う書類"]):
        out.append(u"書類の順が取得の記録の『使う書類』と違う")
    counts = fr[u"注入の件数(書類別)"]
    used = dict((r["docID"], r) for r in fetched[u"取得した書類"])
    n_pair = n_ok = 0
    for doc in docs:
        d = rec[u"書類ごと"][doc]
        for t in ALL_TYPES:
            n_pair += 1
            got, want = d[u"注入の件数"][t], counts[doc][t]
            if all(got[k] == want[k] for k in (u"注入の行になった", u"基準に対応が付かない", u"基準が GROUNDED でない")):
                n_ok += 1
            else:
                out.append(u"%s %s: 注入の件数の 3 つの数が記録と違う" % (doc, t))
            if not got[u"3 つの数が記録と一致"]:
                out.append(u"%s %s: 3 つの数の旗が偽" % (doc, t))
        n_rows = sum(1 for r in rec[u"rows"] if r["doc"] == doc)
        if n_rows != sum(d[u"注入の件数"][t][u"注入の行になった"] for t in ALL_TYPES):
            out.append(u"%s: 行の数が 注入の行になった の合計と違う" % doc)
        if not (d[u"材料の sha256 が取得の記録と一致"] and d[u"材料の sha256"] == used[doc]["sha256"]):
            out.append(u"%s: 材料の sha256 が取得の記録と違う" % doc)
    if (g[u"注入の件数の組"], g[u"注入の件数の組の一致"]) != (n_pair, n_ok) or n_pair != n_ok:
        out.append(u"注入の件数の組の一致が %d / %d でない" % (n_ok, n_pair))
    c = rec[u"cache"]
    if c[u"開始"] != c[u"終了"] or c[u"開始"][u"edinet"] != 281 or c[u"開始"][u"edinet-fresh-2026-10-21"] != 40:
        out.append(u"cache の件数が 281 / 40 のまま動いていない")
    if rec[u"key_leaks"] != []:
        out.append(u"key_leaks が空でない")
    return out


def check_j(rec):
    out = []
    got = rec[u"読んだ入力の sha256"]
    for rel in (FRESH_REL, FETCHED_REL):
        if got.get(rel) != sha64(rel):
            out.append(u"%s の sha256 が記録の写しと違う(読み直しの元が動いた)" % rel)
    return out


# ----------------------------------------------------------------------------------------------------------------
# (d) R-1〜R-14 の当否を記録から求める(幅は封の表の字から読む)
BOLD = re.compile(r"\*\*(.+?)\*\*")
RANGE_RE = re.compile(r"^(\d+(?:\.\d+)?)%? 以上 (\d+(?:\.\d+)?)%? 以下$")


def seal_predictions(seal):
    u"""封 §3 の表の行 {名前: (欄, 予測, 外れ方)}(封の字のまま)。"""
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(R-\d+)\*\* \| (.*) \|$", l)
        if m:
            cells = m.group(2).split(u" | ")
            assert len(cells) == 3, l
            out[m.group(1)] = tuple(c.strip() for c in cells)
    return out


def ranges_of(cell):
    return [(float(m.group(1)), float(m.group(2))) for m in (RANGE_RE.match(b) for b in BOLD.findall(cell)) if m]


def singles_of(cell):
    return [b for b in BOLD.findall(cell) if not RANGE_RE.match(b)]


def pcts_of(cell):
    u"""封の字の 『N% 以上』『N%』(範囲でない)。"""
    return [float(m.group(1)) for m in (re.match(r"^(\d+(?:\.\d+)?)% 以上$", b) for b in BOLD.findall(cell)) if m]


def n_of(n, d):
    return u"%d / %d" % (n, d)


def within(n, rg):
    return rg[0] <= n <= rg[1]


def hit_word(b):
    return u"**判定しない**" if b is None else (u"**当たり**" if b else u"**外れ**")


def judge(rec, fr, seal):
    u"""{名前: (実測の字, 当たりか(True / False / None=判定しない))}。封 §3 の予測を記録から。幅は封の字から読む。"""
    SP = seal_predictions(seal)
    out = collections.OrderedDict()
    M = mains(rec)

    def cls(r, p):
        return r[u"profile"][p][u"分類"]
    # R-1
    g = rec[u"配線の門"]
    a, b = [int(x) for x in singles_of(SP["R-1"][1])[0].split(u" / ")]
    pairs = int(re.search(r"(\d+) 組", SP["R-1"][1]).group(1))
    out["R-1"] = (u"配線の門 %s(id の集合が同じ: %s)、注入の件数の組 %s" % (n_of(g[u"一致"], g[u"行"]), yesno(g[u"id の集合が記録と同じ"]), n_of(g[u"注入の件数の組の一致"], g[u"注入の件数の組"])),
                  bool(g[u"通った"]) and g[u"一致"] == a and g[u"行"] == b and g[u"注入の件数の組"] == pairs == g[u"注入の件数の組の一致"] and bool(g[u"id の集合が記録と同じ"]))
    # R-2
    n = sum(1 for r in M if cls(r, "P22") == W_NOSENT)
    rg = ranges_of(SP["R-2"][1])[0]
    out["R-2"] = (u"P22 の %s: %s" % (W_NOSENT, n_of(n, len(M))), within(n, rg))
    # R-3
    t2 = of_type(rec, "T2_UNIT")
    n = sum(1 for r in t2 if cls(r, "P22") in (W_NS, W_NP))
    rg = ranges_of(SP["R-3"][1])[0]
    out["R-3"] = (u"T2 の届かない(P22。%s・%s): %s(うち通した %d)" % (W_NS, W_NP, n_of(n, len(t2)), sum(1 for r in t2 if cls(r, "P22") == W_NP)), within(n, rg))
    # R-4
    n22 = sum(1 for r in t2 if cls(r, "P22") == W_NS)
    n26 = sum(1 for r in t2 if cls(r, "P26") == W_NS)
    rgs = ranges_of(SP["R-4"][1])
    out["R-4"] = (u"T2 の%s: P22 %d・P26 %d" % (W_NS, n22, n26), within(n22, rgs[0]) and within(n26, rgs[1]))
    # R-5 / R-6
    for k, t in (("R-5", "T1_VALUE"), ("R-6", "T5_COINCIDENT")):
        rs = of_type(rec, t)
        n = sum(1 for r in rs if cls(r, "P22") in (W_NS, W_NP))
        n_pass = sum(1 for r in rs if cls(r, "P22") == W_NP)
        out[k] = (u"%s の届かない(P22): %s(うち通した %d)" % (TSHORT[t], n_of(n, len(rs)), n_pass), within(n, ranges_of(SP[k][1])[0]))
    # R-7
    c22 = sum(1 for r in M if cls(r, "P22") == W_RP)
    c26 = sum(1 for r in M if cls(r, "P26") == W_RP)
    zero = int(re.search(r"(\d+)$", singles_of(SP["R-7"][1])[0]).group(1))
    out["R-7"] = (u"%s: P22 %d・P26 %d(T1・T2・T5 の %d 行)" % (W_RP, c22, c26, len(M)), c22 == zero and c26 == zero)
    # R-8
    rows_all = rec[u"rows"]
    p27 = [r for r in rows_all if r[u"結果(P22〜P27)"]["P27"] == u"通した"]
    rp27 = [r for r in rows_all if cls(r, "P27") == W_RP]
    rp_types = collections.Counter(r[u"型"] for r in rp27)
    five = [r for r in fr[u"注入の行"] if all((r[u"結果"][p] or [None])[0] == "GROUNDED" for p in PROFILES5)]
    by_id = dict((r["id"], r) for r in rows_all)
    five_ok = all(r["id"] in by_id and by_id[r["id"]][u"結果(P22〜P27)"]["P27"] == u"通した" and cls(by_id[r["id"]], "P27") == W_NP for r in five)
    rgs = ranges_of(SP["R-8"][1])
    out["R-8"] = (u"P27 で通した行 %d(741 行の全部)。%s %d(型別 %s)。P22〜P26 の全部が通した %d 行は P27 でも全部%s: %s" % (
        len(p27), W_RP, len(rp27), u"・".join(u"%s %d" % (TSHORT[t], rp_types[t]) for t in ALL_TYPES), len(five), W_NP, yesno(five_ok)),
        within(len(p27), rgs[0]) and within(len(rp27), rgs[1]) and set(rp_types) <= {"T1_VALUE"} and five_ok)
    # R-9
    t3 = t3s(rec)
    cc = collections.Counter(cls(r, "P22") for r in t3)
    n_reach = cc[W_RS] + cc[W_RP]
    rgs = ranges_of(SP["R-9"][1])
    sg = singles_of(SP["R-9"][1])
    want_nomap, want_pass = int(sg[0]), int(sg[1])
    out["R-9"] = (u"T3(P22): 届いた %d・%s %d・%s %d・届いた行の通した %d(%d 行)" % (n_reach, W_NOSENT, cc[W_NOSENT], W_NOMAP, cc[W_NOMAP], cc[W_RP], len(t3)),
                  within(n_reach, rgs[0]) and within(cc[W_NOSENT], rgs[1]) and cc[W_NOMAP] == want_nomap and cc[W_RP] == want_pass)
    # R-10
    n = sum(1 for r in M if r[u"profile"]["P22"][u"届いた(文)"] and not r[u"profile"]["P22"][u"届いた(数)"])
    out["R-10"] = (u"届いた(文)だが数の位置が合わない(P22): %s" % n_of(n, len(M)), within(n, ranges_of(SP["R-10"][1])[0]))
    # R-11
    nr = [r for r in M if cls(r, "P22") in (W_NS, W_NP)]
    nv = sum(1 for r in nr if r[u"profile"]["P22"][u"注入後"][u"対応の付け方"] == K_VALUE)
    lo = pcts_of(SP["R-11"][1])[0]
    out["R-11"] = (u"届かない行の注入後が『値だけ』(P22): %s" % (rate(nv, len(nr)) if nr else u"分母 0"), (nv * 100 >= lo * len(nr)) if nr else None)
    # R-12
    parts, hit = [], True
    rg12 = ranges_of(SP["R-12"][1])[0]
    singles = [float(s.rstrip(u"%")) for s in singles_of(SP["R-12"][1])]
    want = {"P22": singles[0], "P26": singles[1]}
    for p in OBS:
        d = sum(1 for r in M if r[u"profile"][p][u"届いた(文)"])
        k = sum(1 for r in M if cls(r, p) == W_RP)
        pct = 100.0 * k / d if d else None
        parts.append(u"%s %s" % (p, rate(k, d)))
        if pct is None:
            hit = False
        elif p in want:
            hit = hit and round(pct, 1) == want[p]
        else:
            hit = hit and rg12[0] <= pct <= rg12[1]
    out["R-12"] = (u"通した率(分母 = 届いた(文)): " + u"・".join(parts), hit)
    # R-13
    cand = [r for r in M if r[u"profile"]["P26"][u"無改変"][u"claim"] is not None and r[u"profile"]["P26"][u"無改変"][u"claim"][u"state"] != "GROUNDED"]
    if cand:
        ok = all(r[u"profile"]["P26"][u"届いた(文)"] for r in cand)
        out["R-13"] = (u"P26 で基準の claim が無改変から GROUNDED でない行 %d(%s): 届いた(文) %s" % (
            len(cand), u"・".join(TSHORT[r[u"型"]] for r in cand), u"・".join(yesno(r[u"profile"]["P26"][u"届いた(文)"]) for r in cand)), ok)
    else:
        out["R-13"] = (u"P26 で基準の claim が無改変から GROUNDED でない行は無い", None)
    # R-14
    lo1, lo2 = pcts_of(SP["R-14"][1])
    s26 = sum(1 for r in M if cls(r, "P22") == cls(r, "P26"))
    s27 = sum(1 for r in M if cls(r, "P22") == cls(r, "P27"))
    out["R-14"] = (u"分類が同じ行: P22 と P26 %s・P22 と P27 %s" % (rate(s26, len(M)), rate(s27, len(M))), s26 * 100 >= lo1 * len(M) and s27 * 100 >= lo2 * len(M))
    return out


# ----------------------------------------------------------------------------------------------------------------
# (c) 文書の表
def cnt_by(rows, p, key):
    return collections.Counter(r[u"profile"][p][key] for r in rows)


def render_blocks(rec, fr, seal):
    B = collections.OrderedDict()
    pos = positions(rec)
    order = rec[u"書類(出てくる順)"]
    J = judge(rec, fr, seal)
    SP = seal_predictions(seal)
    assert list(SP) == list(J), list(SP)
    B["pred"] = table([u"#", u"欄", u"予測(封の字)", u"外れ方(封の字)", u"実測(記録から)", u"当たり外れ"],
                      [[u"**%s**" % k, SP[k][0], SP[k][1], SP[k][2], J[k][0], hit_word(J[k][1])] for k in J])
    # 材料と配線
    g = rec[u"配線の門"]
    drows = []
    for i, d in enumerate(order):
        pd = rec[u"書類ごと"][d]
        nrow = sum(pd[u"注入の件数"][t][u"注入の行になった"] for t in ALL_TYPES)
        nmatch = sum(1 for w in rec[u"配線の行ごと"] if w["doc"] == d and w[u"一致"][u"4 欄とも一致"])
        drows.append([u"書類 %d" % (i + 1), pd[u"材料の sha256"], str(nrow), str(nmatch), str(pd[u"claims"]["P22"]), str(pd[u"claims"]["P27"]),
                      str(pd[u"文の数"]["P22"]), str(pd[u"文の数"]["P27"])])
    B["docs"] = table([u"書類", u"材料の sha256(取得の記録と一致)", u"注入の行", u"配線の一致", u"claim(P22)", u"claim(P27)", u"文(P22)", u"文(P27)"], drows)
    B["wiring"] = table([u"配線の門", u"値"], [
        [u"作り直した行 / 4 欄とも一致", n_of(g[u"一致"], g[u"行"])], [u"記録 `注入の行`(対象の書類)", str(g[u"記録の注入の行(対象の書類)"])],
        [u"id の集合が記録と同じ", yesno(g[u"id の集合が記録と同じ"])], [u"注入の件数の組(書類 × 型)/ 3 つの数が一致", n_of(g[u"注入の件数の組の一致"], g[u"注入の件数の組"])],
        [u"全書類の記録", yesno(rec[u"全書類"])]])
    crow = []
    for t in ALL_TYPES:
        s = collections.Counter()
        for d in order:
            c = rec[u"書類ごと"][d][u"注入の件数"][t]
            for k in (u"作れる site", u"採った", u"注入の行になった", u"基準に対応が付かない", u"基準が GROUNDED でない"):
                s[k] += c[k]
        crow.append([TSHORT[t]] + [str(s[k]) for k in (u"作れる site", u"採った", u"注入の行になった", u"基準に対応が付かない", u"基準が GROUNDED でない")])
    B["counts"] = table([u"型", u"作れる site", u"採った", u"注入の行になった", u"基準に対応が付かない", u"基準が GROUNDED でない"], crow)
    eng = rec[u"engine sha16"]
    B["engine"] = table([u"項目", u"値"], [[u"`%s` の sha16" % k, u"`%s`" % v] for k, v in eng.items()] + [
        [u"DEFAULT_PROFILE", rec[u"DEFAULT_PROFILE"]], [u"測った木の HEAD", u"`%s`" % rec[u"HEAD"]], [u"封の commit", u"`%s`" % rec[u"封"][u"commit"]],
        [u"cache `edinet/`(開始 → 終了)", u"%d → %d" % (rec[u"cache"][u"開始"][u"edinet"], rec[u"cache"][u"終了"][u"edinet"])],
        [u"cache `edinet-fresh-2026-10-21/`(開始 → 終了)", u"%d → %d" % (rec[u"cache"][u"開始"][u"edinet-fresh-2026-10-21"], rec[u"cache"][u"終了"][u"edinet-fresh-2026-10-21"])],
        [u"key_leaks", str(len(rec[u"key_leaks"]))]])
    # 集計(T1・T2・T5)
    groups = [(TSHORT[t], of_type(rec, t)) for t in MAIN_TYPES] + [(u"計", mains(rec))]
    prow, crow, srow, drow = [], [], [], []
    for p in OBS:
        for name, rs in groups:
            nr = sum(1 for r in rs if r[u"profile"][p][u"届いた(文)"])
            nn = sum(1 for r in rs if r[u"profile"][p][u"届いた(数)"])
            unk = sum(1 for r in rs if r[u"profile"][p][u"token"][u"文の番号"] is None)
            prow.append([p, name, str(len(rs)), str(nr), str(nn), str(nr - nn), str(len(rs) - nr - unk), str(unk)])
            c = cnt_by(rs, p, u"分類")
            crow.append([p, name, str(len(rs))] + [str(c[w]) for w in WORDS6])
            sc = collections.Counter((r[u"profile"][p][u"分類"], r[u"profile"][p][u"結果"]) for r in rs)
            srow.append([p, name, str(sc[(W_RS, u"違う")]), str(sc[(W_RS, u"要確認")]), str(sc[(W_NS, u"違う")]), str(sc[(W_NS, u"要確認")]), str(c[W_NP]), str(c[W_RP])])
            dc = cnt_by(rs, p, u"細目")
            drow.append([p, name, str(dc[D_NUM]), str(dc[D_OTHER]), str(dc[D_DIFFID]), str(dc[D_MOVED]), str(dc[D_SAME]), str(c[W_NP])])
    B["pos"] = table([u"profile", u"型", u"行", u"届いた(文)", u"届いた(数)", u"同じ文・別の数", u"届かない", u"token の文が決まらない"], prow)
    B["cls"] = table([u"profile", u"型", u"行"] + list(WORDS6), crow)
    B["stops"] = table([u"profile", u"型", u"届いた・違う", u"届いた・要確認", u"届かない・違う", u"届かない・要確認", u"届かない・通した", u"届いた・通した"], srow)
    B["detail"] = table([u"profile", u"型", u"届いた: 数の位置が合う", u"届いた: 同じ文・別の数", u"届かない・止めた: 別の id", u"届かない・止めた: 同じ id・state が違う",
                         u"届かない・止めた: 同じ id・state も同じ", u"届かない・通した"], drow)
    # 基準の claim が無改変の profile で GROUNDED でない行(封 §4 の 5)
    brow = []
    for p in OBS:
        for name, rs in groups:
            bad = [r for r in rs if r[u"profile"][p][u"無改変"][u"claim"] is not None and r[u"profile"][p][u"無改変"][u"claim"][u"state"] != "GROUNDED"]
            same = sum(1 for r in bad if r[u"profile"][p][u"注入後"][u"state が無改変の同じ id と同じ"])
            reach = sum(1 for r in bad if r[u"profile"][p][u"届いた(文)"])
            nofound = sum(1 for r in rs if r[u"profile"][p][u"無改変"][u"claim"] is None)
            brow.append([p, name, str(len(rs)), str(nofound), str(len(bad)), str(same), str(reach)])
    B["basestate"] = table([u"profile", u"型", u"行", u"記録の基準の id が一覧に無い", u"基準が無改変から GROUNDED でない", u"うち注入後の state が無改変と同じ", u"うち届いた(文)"], brow)
    # D の読み直し
    rr = []
    for p in OBS:
        for name, rs in groups:
            c = cnt_by(rs, p, u"分類")
            w = cnt_by(rs, p, u"結果")
            nr = sum(1 for r in rs if r[u"profile"][p][u"届いた(文)"])
            nr_nomap = sum(1 for r in rs if r[u"profile"][p][u"届いた(文)"] and r[u"profile"][p][u"分類"] == W_NOMAP)
            stop_all = w[u"違う"] + w[u"要確認"]
            rs_w = collections.Counter(r[u"profile"][p][u"結果"] for r in rs if r[u"profile"][p][u"分類"] == W_RS)
            rr.append([p, name, str(len(rs)), rate(w[u"通した"], len(rs)), rate(w[u"違う"], stop_all), str(w[u"対応が付かない"]),
                       str(nr), rate(c[W_RP], nr), rate(rs_w[u"違う"], c[W_RS]), str(c[W_RS]), str(nr_nomap), str(c[W_NS] + c[W_NP])])
    d_all = []
    for p in OBS:
        w = cnt_by(rec[u"rows"], p, u"結果")
        stop_all = w[u"違う"] + w[u"要確認"]
        d_all.append([p, u"全 %d(T3 込み。元の D)" % len(rec[u"rows"]), str(len(rec[u"rows"])), rate(w[u"通した"], len(rec[u"rows"])), rate(w[u"違う"], stop_all),
                      str(w[u"対応が付かない"]), u"―", u"―", u"―", u"―", u"―", u"―"])
    B["reread"] = table([u"profile", u"型", u"元: 行", u"元: 通した率(分母 = 行)", u"元: 止めのうち違う(分母 = 違う + 要確認)", u"元: 対応が付かない",
                         u"読み直し: 届いた(文)", u"通した率(分母 = 届いた(文))", u"止めのうち違う(分母 = 届いた・止めた)", u"届いた・止めた", u"届いた(文)のうち対応が付かない", u"届かない(通した + 止めた)"],
                        rr + d_all)
    # T3
    t3 = t3s(rec)
    trow = []
    for p in OBS:
        c = cnt_by(t3, p, u"分類")
        w = collections.Counter((r[u"profile"][p][u"分類"], r[u"profile"][p][u"結果"]) for r in t3)
        one = sum(1 for r in t3 if r[u"profile"][p][u"挿入した文に在る claim の数"] == 1)
        known = sum(1 for r in t3 if r[u"profile"][p][u"挿入した文の番号"] is not None)
        trow.append([p, str(len(t3)), str(known), str(one), str(c[W_RS] + c[W_RP]), str(c[W_RP]), str(w[(W_RS, u"違う")]), str(w[(W_RS, u"要確認")]),
                     str(c[W_NS] + c[W_NP]), str(c[W_NOMAP]), str(c[W_NOSENT])])
    B["t3"] = table([u"profile", u"行", u"挿入した文が決まる", u"その文の claim が 1 つ", u"届いた", u"届いた・通した", u"届いた・違う", u"届いた・要確認",
                     u"届かない", u"対応が付かない", u"文が決まらない"], trow)
    # 対応の付け方
    mrow = []
    for p in OBS:
        for name, rs in groups:
            a0 = collections.Counter(r[u"profile"][p][u"無改変"][u"対応の付け方"] for r in rs)
            a1 = collections.Counter(r[u"profile"][p][u"注入後"][u"対応の付け方"] for r in rs)
            n_other = sum(1 for r in rs if not r[u"profile"][p][u"無改変"][u"基準の id が記録の P22 と同じ"])
            n_missing = sum(1 for r in rs if not r[u"profile"][p][u"無改変"][u"記録の基準の id が一覧に在る"])
            mrow.append([p, name, str(a0[K_BOTH]), str(a0[K_VALUE]), str(a0[u"対応が付かない"]), str(a1[K_BOTH]), str(a1[K_VALUE]), str(a1[u"対応が付かない"]), str(n_other), str(n_missing)])
    B["match"] = table([u"profile", u"型", u"無改変: 値と字", u"無改変: 値だけ", u"無改変: 付かない", u"注入後: 値と字", u"注入後: 値だけ", u"注入後: 付かない",
                        u"この profile の基準の id が記録の P22 と違う行", u"記録の基準の id が一覧に無い行"], mrow)
    # 分類の一致
    arow = []
    M = mains(rec)
    for name, rs in groups:
        for a, b in (("P22", "P26"), ("P22", "P27")):
            same_c = sum(1 for r in rs if r[u"profile"][a][u"分類"] == r[u"profile"][b][u"分類"])
            same_w = sum(1 for r in rs if r[u"profile"][a][u"結果"] == r[u"profile"][b][u"結果"])
            arow.append([name, u"%s と %s" % (a, b), str(len(rs)), rate(same_c, len(rs)), rate(same_w, len(rs))])
    B["agree"] = table([u"型", u"比べる profile", u"行", u"分類が同じ", u"結果の語が同じ"], arow)
    # 通した行(どれかの profile で)・届いた・通した の行
    prow2 = []
    for r in rec[u"rows"]:
        if any(r[u"profile"][p][u"結果"] == u"通した" or r[u"profile"][p][u"分類"] == W_RP for p in OBS):
            prow2.append([plabel(pos[r["id"]]), u"%s → %s" % (r[u"元の字"], r[u"後の字"]) if r[u"型"] != "T3_ABSENT" else u"挿入"] +
                         [u"%s %s" % (r[u"profile"][p][u"結果"], r[u"profile"][p][u"分類"]) for p in OBS])
    B["pass"] = table([u"位置", u"元の字 → 後の字"] + [u"%s(結果・分類)" % p for p in OBS], prow2)
    # 位置で呼ぶ例: 型ごとに P22 の届かない・決まらない・対応が付かない の先頭 6 行まで
    erow = []
    for t in MAIN_TYPES:
        k = 0
        for r in of_type(rec, t):
            x = r[u"profile"]["P22"]
            if x[u"分類"] in (W_NS, W_NP, W_NOSENT, W_NOMAP) and k < 6:
                k += 1
                erow.append([plabel(pos[r["id"]]), u"%s → %s" % (r[u"元の字"], r[u"後の字"]), x[u"無改変"][u"対応の付け方"], x[u"注入後"][u"対応の付け方"],
                             yesno(x[u"注入後"][u"記録の基準の id と同じ id"]), u"―" if x[u"注入後"][u"state が無改変の同じ id と同じ"] is None else yesno(x[u"注入後"][u"state が無改変の同じ id と同じ"]),
                             u"%s / %s" % (u"―" if x[u"token"][u"文の番号"] is None else x[u"token"][u"文の番号"], u"―" if x[u"無改変"][u"文の番号"] is None else x[u"無改変"][u"文の番号"])] +
                            [r[u"profile"][p][u"分類"] for p in OBS])
    B["examples"] = table([u"位置", u"元の字 → 後の字", u"付け方(無改変)", u"付け方(注入後)", u"注入後が基準と同じ id", u"state が無改変と同じ", u"文の番号(token / 基準)"] +
                          [u"%s の分類" % p for p in OBS], erow)
    order_of_doc = ("pred", "wiring", "counts", "docs", "engine", "pos", "cls", "stops", "detail", "basestate", "match", "t3", "agree", "pass", "examples", "reread")
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


def check_c(rec, fr, seal, doc):
    u"""文書の表を記録から作り直して比べる。問題の列。"""
    out = []
    try:
        B = render_blocks(rec, fr, seal)
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


def check_doc_prose(rec, fr, seal, doc):
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
    J = judge(rec, fr, seal)
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
    for lit in (u"記録は不変", u"配線の数", u"engine が止めた", u"仮説。測るまで断定しない", u"測っていない", u"診断だけ", NOT_GATED, u"edinetdb-p27", u"読み直し"):
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
def check_h(seal, doc, fetched, rec=None):
    out = []
    docs = list(fetched[u"使う書類"])
    cids = set()
    if rec is not None:
        for r in rec[u"rows"]:
            if r[u"基準の claim"]:
                cids.add(r[u"基準の claim"])
            for p in OBS:
                x = r[u"profile"][p]
                for k in (u"無改変", u"注入後"):
                    if isinstance(x.get(k), dict) and x[k].get(u"claim"):
                        cids.add(x[k][u"claim"][u"id"])
                if isinstance(x.get(u"claim"), dict):
                    cids.add(x[u"claim"][u"id"])
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
        self.dir = tempfile.mkdtemp(prefix="reach_", dir=base)
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
        cls.fr = jload(FRESH_REC)
        cls.fetched = jload(FETCHED)
        cls.seal = jtext(SEAL)

    def test_a_1_the_ids_equal_the_fresh_injection_rows(self):
        self.assertEqual(check_a(self.rec, self.fr), [])
        self.assertEqual(len(self.rec[u"rows"]), len(self.fr[u"注入の行"]))
        self.assertEqual(collections.Counter(r[u"型"] for r in self.rec[u"rows"]), collections.Counter(r[u"型"] for r in self.fr[u"注入の行"]))

    def test_a_2_the_id_set_is_read_from_fresh_not_hardcoded(self):
        u"""fresh の写しから 1 行を消す・id を変えると赤(id の集合は fresh から読む)。"""
        fr = copy.deepcopy(self.fr)
        fr[u"注入の行"].pop(7)
        self.assertNotEqual(check_a(self.rec, fr), [])
        fr = copy.deepcopy(self.fr)
        fr[u"注入の行"][3][u"後の字"] = u"X"
        self.assertNotEqual(check_a(self.rec, fr), [])

    def test_b_1_the_wiring_gate_matches_every_row_and_every_pair(self):
        self.assertEqual(check_b(self.rec, self.fr, self.fetched), [])
        g = self.rec[u"配線の門"]
        self.assertEqual(g[u"一致"], g[u"行"])
        self.assertEqual(g[u"注入の件数の組"], len(self.fetched[u"使う書類"]) * len(ALL_TYPES))
        self.assertEqual(g[u"注入の件数の組の一致"], g[u"注入の件数の組"])

    def test_b_2_the_record_is_the_full_run_and_has_no_leak(self):
        self.assertTrue(self.rec[u"全書類"])
        self.assertEqual(self.rec[u"key_leaks"], [])
        self.assertEqual(self.rec[u"cache"][u"開始"], self.rec[u"cache"][u"終了"])

    def test_e_1_the_classes_are_recomputed_from_the_fields(self):
        self.assertEqual(check_e(self.rec), [])

    def test_e_2_every_row_has_the_three_profiles_and_the_known_fields(self):
        for r in self.rec[u"rows"]:
            self.assertEqual(list(r[u"profile"]), list(OBS))
            for p in OBS:
                x = r[u"profile"][p]
                self.assertIn(x[u"分類"], WORDS6)
                if r[u"型"] == "T3_ABSENT":
                    for k in (u"挿入した文の番号", u"挿入した文に在る claim の数", u"claim", u"届いた", u"結果"):
                        self.assertIn(k, x)
                else:
                    for k in (u"無改変", u"token", u"注入後", u"届いた(文)", u"届いた(数)", u"細目"):
                        self.assertIn(k, x)
                    self.assertTrue(x[u"無改変"][u"枝が本物の _find_base_claim と同じ"])
                    self.assertTrue(x[u"注入後"][u"枝が本物の claim_for と同じ"])

    def test_e_3_the_six_words_cover_every_row_once(self):
        for p in OBS:
            c = collections.Counter(r[u"profile"][p][u"分類"] for r in self.rec[u"rows"])
            self.assertEqual(sum(c.values()), len(self.rec[u"rows"]))
            self.assertTrue(set(c) <= set(WORDS6))

    def test_e_4_t3_has_no_base_and_main_rows_have_a_base_from_p22(self):
        for r in self.rec[u"rows"]:
            if r[u"型"] == "T3_ABSENT":
                self.assertIsNone(r[u"基準の claim"])
            else:
                self.assertTrue(r[u"profile"]["P22"][u"無改変"][u"基準の id が記録の P22 と同じ"], r["id"])
                self.assertEqual(r[u"profile"]["P22"][u"無改変"][u"claim"][u"id"], r[u"基準の claim"])
                self.assertEqual(r[u"profile"]["P22"][u"無改変"][u"claim"][u"state"], "GROUNDED")     # 基準の条件(封 §0-4): 無改変の P22 で GROUNDED

    def test_j_1_the_inputs_read_are_unchanged(self):
        self.assertEqual(check_j(self.rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"読んだ入力の sha256"][FRESH_REL] = u"0" * 64
        self.assertNotEqual(check_j(rec), [])

    def test_d_1_judgments_are_recomputed_and_cover_the_fourteen_predictions(self):
        J = judge(self.rec, self.fr, self.seal)
        self.assertEqual(list(J), ["R-%d" % i for i in range(1, 15)])
        self.assertTrue(all(v[1] in (True, False, None) for v in J.values()))

    def test_d_2_the_judge_is_not_a_constant(self):
        u"""記録の写しの 1 か所を変えると当否が変わる(R-1 の配線の件数・R-7 の届いた・通した・R-12 の通した率・R-9 の T3)。"""
        J0 = judge(self.rec, self.fr, self.seal)
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"一致"] -= 1
        self.assertTrue(J0["R-1"][1] and not judge(rec, self.fr, self.seal)["R-1"][1])
        rec = copy.deepcopy(self.rec)
        m = [r for r in mains(rec) if r[u"profile"]["P22"][u"分類"] == W_RS][0]
        m[u"profile"]["P22"][u"分類"] = W_RP
        J1 = judge(rec, self.fr, self.seal)
        self.assertTrue(J0["R-7"][1] and not J1["R-7"][1])
        self.assertTrue(J0["R-12"][1] and not J1["R-12"][1])
        rec = copy.deepcopy(self.rec)
        t = t3s(rec)[0]
        t[u"profile"]["P22"][u"分類"] = W_RP
        self.assertNotEqual(judge(rec, self.fr, self.seal)["R-9"], J0["R-9"])
        rec = copy.deepcopy(self.rec)
        n_before = J0["R-14"][0]
        for r in mains(rec)[:60]:
            r[u"profile"]["P26"][u"分類"] = W_NOMAP if r[u"profile"]["P22"][u"分類"] != W_NOMAP else W_NOSENT
        self.assertNotEqual(judge(rec, self.fr, self.seal)["R-14"][0], n_before)

    def test_reread_original_rates_equal_the_D_of_the_fresh_record(self):
        u"""読み直しの表の『元』の列(741 行の全部)が fresh の D と同じ(記録は不変。元の率は D のまま)。"""
        for p in ("P22", "P26"):
            w = collections.Counter(r[u"結果(P22〜P27)"][p] for r in self.rec[u"rows"])
            d = self.fr[u"D"][p]
            self.assertEqual((w[u"通した"], w[u"違う"], w[u"要確認"], w[u"対応が付かない"]), (d[u"通した"], d[u"違う"], d[u"要確認"], d[u"対応が付かない"]), p)


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
        u"""宣言の無い file の sha が違えば赤、宣言があっても値が違えば赤(型の確認。実 file は触らない)。"""
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
        cls.fr = jload(FRESH_REC)
        cls.fetched = jload(FETCHED)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def test_c_1_the_tables_equal_the_ones_rebuilt_from_the_record(self):
        self.assertEqual(check_c(self.rec, self.fr, self.seal, self.doc), [])

    def test_c_2_the_prose_outside_the_tables_is_in_order(self):
        self.assertEqual(check_doc_prose(self.rec, self.fr, self.seal, self.doc), [])

    def test_d_3_the_prediction_table_copies_the_seal_and_the_judgments(self):
        SP = seal_predictions(self.seal)
        J = judge(self.rec, self.fr, self.seal)
        got = doc_blocks(self.doc)["pred"]
        self.assertEqual(len(got), 2 + len(J))
        for line, k in zip(got[2:], J):
            cells = [c.strip() for c in line.strip().strip(u"|").split(u" | ")]
            self.assertEqual(cells[0], u"**%s**" % k)
            self.assertEqual(tuple(cells[1:4]), SP[k], k)                  # 封の字(欄・予測・外れ方)のまま
            self.assertEqual(cells[4], J[k][0], k)                          # 実測は記録から
            self.assertEqual(cells[5], hit_word(J[k][1]), k)                # 当否は記録から

    def test_d_4_the_seal_prediction_table_is_what_this_gate_reads(self):
        u"""封の表の形(幅の数は字で留めない。『幅が何本あるか』『何が太字か』の形だけを見る)。"""
        SP = seal_predictions(self.seal)
        self.assertEqual(list(SP), ["R-%d" % i for i in range(1, 15)])
        self.assertEqual([len(ranges_of(SP["R-%d" % i][1])) for i in range(1, 15)], [0, 1, 1, 2, 1, 1, 0, 2, 2, 1, 0, 1, 0, 0])
        self.assertEqual(len(singles_of(SP["R-1"][1])), 1)
        self.assertEqual(len(pcts_of(SP["R-14"][1])), 2)
        self.assertEqual(len(pcts_of(SP["R-11"][1])), 1)

    def test_d_5_the_misses_are_kept_as_misses(self):
        J = judge(self.rec, self.fr, self.seal)
        # 外れは外れのまま残す。封も予測も直さない。記録から求めた当否の並びを留める。
        self.assertEqual([k for k, v in J.items() if v[1] is False], MISSES)
        self.assertEqual([k for k, v in J.items() if v[1] is None], UNDECIDED)
        self.assertEqual([k for k, v in J.items() if v[1] is True], [k for k in J if k not in MISSES and k not in UNDECIDED])

    def test_h_1_no_docid_and_no_claim_id_in_the_seal_and_the_document(self):
        self.assertEqual(check_h(self.seal, self.doc, self.fetched, self.rec), [])
        self.assertEqual(len(self.fetched[u"使う書類"]), 30)

    def test_h_2_the_record_names_the_documents_and_that_is_why_it_is_declared(self):
        txt = jtext(REC)
        docs = self.fetched[u"使う書類"]
        self.assertTrue(all(d in txt for d in docs))
        later = (REC_REL, SCRIPT_REL, GATE_REL)
        fresh_seal = jtext(os.path.join(HERE, "test_xbrl_fresh_seal.py"))
        for p in later:
            self.assertIn(u'"%s"' % p, fresh_seal, p)

    def test_doc_states_the_dated_note_about_the_original_rates(self):
        self.assertIn(u"2026-10-28", self.doc)
        self.assertIn(u"fresh_2026-10-21.json", self.doc)


class ScriptTest(unittest.TestCase):
    def test_script_does_not_remeasure_when_the_output_exists(self):
        before = hashlib.sha256(open(REC, "rb").read()).hexdigest()
        env = dict((k, v) for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "EDINET_API_KEY", "EDINETDB_API_KEY"))
        r = subprocess.run(["python3", SCRIPT, "--out", REC], cwd=ROOT, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        self.assertIn(u"測り直さない", r.stdout)
        self.assertEqual(hashlib.sha256(open(REC, "rb").read()).hexdigest(), before)


class FalseRecordsAreRedTest(unittest.TestCase):
    u"""(g) 偽物で赤: 記録の写しを 1 か所変えると (b)(c)(e) が赤になる(変異)。"""

    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.fr = jload(FRESH_REC)
        cls.fetched = jload(FETCHED)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def test_g_0_baseline_is_green(self):
        self.assertEqual(check_b(self.rec, self.fr, self.fetched), [])
        self.assertEqual(check_c(self.rec, self.fr, self.seal, self.doc), [])
        self.assertEqual(check_e(self.rec), [])

    def test_g_1_changing_one_class_turns_e_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in mains(rec) if x[u"profile"]["P26"][u"分類"] == W_RS][0]
        r[u"profile"]["P26"][u"分類"] = W_NP
        self.assertNotEqual(check_e(rec), [])
        self.assertNotEqual(check_c(rec, self.fr, self.seal, self.doc), [])
        self.assertEqual(check_b(rec, self.fr, self.fetched), [])                # b は分類を見ない(1 つの性質は所有する 1 か所で)

    def test_g_2_changing_one_sentence_number_turns_e_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in mains(rec) if x[u"profile"]["P22"][u"届いた(文)"]][0]
        r[u"profile"]["P22"][u"token"][u"文の番号"] += 1
        self.assertNotEqual(check_e(rec), [])
        rec = copy.deepcopy(self.rec)
        r = [x for x in mains(rec) if x[u"profile"]["P22"][u"届いた(文)"]][0]
        r[u"profile"]["P22"][u"無改変"][u"文の番号"] += 1
        self.assertNotEqual(check_e(rec), [])
        rec = copy.deepcopy(self.rec)
        r = t3s(rec)[0]
        r[u"profile"]["P22"][u"挿入した文の番号"] += 1
        self.assertNotEqual(check_e(rec), [])

    def test_g_3_changing_the_wiring_flag_turns_b_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"配線の行ごと"][0][u"一致"][u"4 欄とも一致"] = False
        self.assertNotEqual(check_b(rec, self.fr, self.fetched), [])
        self.assertNotEqual(check_c(rec, self.fr, self.seal, self.doc), [])

    def test_g_4_changing_the_wiring_count_turns_b_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"一致"] -= 1
        self.assertNotEqual(check_b(rec, self.fr, self.fetched), [])
        self.assertNotEqual(check_c(rec, self.fr, self.seal, self.doc), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"注入の件数の組の一致"] -= 1
        self.assertNotEqual(check_b(rec, self.fr, self.fetched), [])
        rec = copy.deepcopy(self.rec)
        d = rec[u"書類(出てくる順)"][0]
        rec[u"書類ごと"][d][u"注入の件数"]["T1_VALUE"][u"基準が GROUNDED でない"] += 1
        self.assertNotEqual(check_b(rec, self.fr, self.fetched), [])

    def test_g_5_changing_the_matching_kind_turns_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in mains(rec) if x[u"profile"]["P22"][u"注入後"][u"対応の付け方"] == K_VALUE][0]
        r[u"profile"]["P22"][u"注入後"][u"対応の付け方"] = K_BOTH
        self.assertNotEqual(check_c(rec, self.fr, self.seal, self.doc), [])
        rec = copy.deepcopy(self.rec)
        r = [x for x in mains(rec) if x[u"profile"]["P22"][u"無改変"][u"対応の付け方"] == K_BOTH][0]
        r[u"profile"]["P22"][u"無改変"][u"対応の付け方"] = K_VALUE
        self.assertNotEqual(check_c(rec, self.fr, self.seal, self.doc), [])

    def test_g_6_one_character_of_the_document_table_turns_c_red(self):
        for name in ("cls", "pos", "reread", "counts"):
            i = self.doc.index(u"<!-- 門:start %s -->" % name)
            j = self.doc.index(u"<!-- 門:end -->", i)
            seg = self.doc[i:j]
            s0 = seg.index(u"\n|---")
            k = re.search(r"\| (\d+) \|", seg[s0:])
            self.assertIsNotNone(k, name)
            seg2 = seg[:s0 + k.start(1)] + str(int(k.group(1)) + 1) + seg[s0 + k.end(1):]
            doc = self.doc[:i] + seg2 + self.doc[j:]
            self.assertNotEqual(doc, self.doc)
            self.assertNotEqual(check_c(self.rec, self.fr, self.seal, doc), [], name)
        i = self.doc.index(u"<!-- 門:start pred -->")
        doc = self.doc[:i] + self.doc[i:].replace(u"**当たり**", u"**外れ**", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(check_c(self.rec, self.fr, self.seal, doc), [])

    def test_g_7_changing_a_prediction_character_of_the_seal_turns_d_and_c_red(self):
        u"""封の予測の 1 字(R-1 の『741 / 741』の分母)を変えると、当否の判定が変わり(d)、文書の表の写しとも合わなくなる(c)。"""
        seal = u"\n".join(l.replace(u"**741 / 741**", u"**741 / 740**", 1) if l.startswith(u"| **R-1**") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(judge(self.rec, self.fr, seal)["R-1"], judge(self.rec, self.fr, self.seal)["R-1"])
        self.assertNotEqual(check_c(self.rec, self.fr, seal, self.doc), [])
        seal = u"\n".join(l.replace(u"**0 以上 30 以下**", u"**0 以上 29 以下**", 1) if l.startswith(u"| **R-2**") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(check_c(self.rec, self.fr, seal, self.doc), [])

    def test_g_8_a_docid_or_a_claim_id_in_the_document_turns_h_red(self):
        doc = self.doc + u"\n" + self.fetched[u"使う書類"][0] + u"\n"
        self.assertNotEqual(check_h(self.seal, doc, self.fetched, self.rec), [])
        doc = self.doc + u"\nN012\n"
        self.assertNotEqual(check_h(self.seal, doc, self.fetched, self.rec), [])
        cid = self.rec[u"rows"][0][u"基準の claim"]
        doc = self.doc + u"\n%s\n" % cid
        self.assertNotEqual(check_h(self.seal, doc, self.fetched, self.rec), [])

    def test_g_9_an_unmarked_number_in_prose_turns_the_prose_check_red(self):
        doc = self.doc + u"\n通した行は 7 行だった。\n"
        self.assertNotEqual(check_doc_prose(self.rec, self.fr, self.seal, doc), [])

    def test_g_10_changing_the_hit_word_in_the_prose_turns_the_prose_check_red(self):
        doc = self.doc.replace(u"外れた予測: ", u"外れた予測: R-99・", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(check_doc_prose(self.rec, self.fr, self.seal, doc), [])


class OrderTest(unittest.TestCase):
    u"""(i) 封の commit が script・記録・文書・門の commit より前。"""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="reach_root_")
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
