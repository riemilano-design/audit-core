# -*- coding: utf-8 -*-
u"""注入 T2(単位の差し替え)で P22〜P26 の全部が通した 5 行の診断の門 ― 封 docs/XBRL_T2_PASS_DIAG_SEAL_2026-10-28.md §5-2 の (a)〜(i)。

記録 ``fixtures/xbrl/t2_pass_diag_2026-10-28.json``(``measure/xbrl_t2_pass_diag_2026-10-28.py`` の出力)・文書 ``docs/XBRL_T2_PASS_DIAG_2026-10-28.md``。

  (a) 記録の 5 行の id が ``fresh_2026-10-21.json`` から**機械で選んだ**「P22〜P26 が全部 GROUNDED」の行と一致する(字で留めない。どれか 1 つの profile で GROUNDED の行も同じ)。
  (b) 配線の門が 13 / 13 で記録されている(行ごとの 4 欄の旗・id の集合が記録の T2_UNIT の行と同じ・書類ごとの数が ``注入の件数(書類別)`` と同じ・材料の sha256 が取得の記録と一致)。
  (c) 文書の表を記録から作り直して 1 行も違わない(``<!-- 門:start 名前 -->`` の中)。門の外の散文の数には【門なし】の印が要る。
  (d) T-1〜T-8(と T-3a)の当否を記録から求め、封の字(予測・外れ方)と、文書の当否の表の字が一致する。
  (e) 分類(封 §2-3 と §6-5)を、記録の claim の欄(pointers・unit・state・文の番号)から別の書き方で求め直して、記録の分類と一致する。
  (f) engine の sha16 を留める(宣言された遷移の型: 値が宣言の値のときだけ、その封が履歴に在ること)。
  (g) 偽物で赤: 記録の写しの分類・pointers・配線の旗を 1 か所変えると (b)(c)(e) が赤になる。
  (h) 封と文書に 30 書類の docID の字(``fetched_2026-10-21.json`` の「使う書類」から読む)も claim の id の字も無い。
  (i) 封の commit が script・記録・文書・門の commit より前(git の commit の順)。

**(i) は、script・記録・文書・門のどれかが commit される前は赤になる**(追跡されていない file には『足した commit』が無い)。前例 ``test_xbrl_p27_order.py`` と同じ扱い
(R が commit される前は赤で、R の中で初めて緑になる)。skip にしない(skip は緑に見える)。使い捨ての git repo で、順序が正しければ緑・違反はそれぞれ特定の符号で赤になることを確かめる。

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

SEAL_REL = "docs/XBRL_T2_PASS_DIAG_SEAL_2026-10-28.md"
DOC_REL = "docs/XBRL_T2_PASS_DIAG_2026-10-28.md"
REC_REL = "fixtures/xbrl/t2_pass_diag_2026-10-28.json"
SCRIPT_REL = "measure/xbrl_t2_pass_diag_2026-10-28.py"
GATE_REL = "tests/measure/test_xbrl_t2_pass_diag.py"
SEAL, DOC, REC = [os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL)]
FRESH_REC = os.path.join(ROOT, "fixtures", "xbrl", "fresh", "fresh_2026-10-21.json")
FETCHED = os.path.join(ROOT, "fixtures", "xbrl", "fresh", "fetched_2026-10-21.json")
SCRIPT = os.path.join(ROOT, SCRIPT_REL)
SEAL_COMMIT_SHORT = "2726563"
PROFILES5 = ("P22", "P23", "P24", "P25", "P26")
OBS = ("P22", "P26", "P27")
YEN_FAMILY = (u"円", u"千円", u"百万円", u"億円", u"兆円")
NOT_GATED = u"【門なし】"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
FORBIDDEN = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")

#: engine の sha16(記録を測った時点の値。字で留める ― 測った事実)。変えるなら宣言された遷移として下の ENGINE_DECLARED に足す。
ENGINE_AT_MEASURE = {
    "adapters/xbrl/extract.py": "3cf55966f12919f0", "adapters/xbrl/vocabulary.py": "514ebb8104451c07", "adapters/xbrl/recipes.py": "52d645e713c53c1c",
    "adapters/xbrl/resolve.py": "a41043763c1d4073", "adapters/xbrl/comparators.py": "d8706338325e725b", "adapters/xbrl/verify_document.py": "c3791080ab5aef2f",
}
#: 宣言された遷移 {file: (遷移の後の sha16, その遷移を宣言した封)}。今は 0 件(この診断の commit 時点で engine は測った時点のまま)。
#: 足すときは、封が履歴に在り、値が宣言の値のときだけ受け入れる(tests/measure/test_xbrl_default_p27_result.py の型)。測った時点の値は消さない。
ENGINE_DECLARED = {}


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    return json.loads(jtext(p))


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


# ----------------------------------------------------------------------------------------------------------------
# 記録の読み方
def passed_rows(fr):
    u"""(a) 記録 fresh から機械で選ぶ: P22〜P26 の全部が GROUNDED の行。どれか 1 つで GROUNDED の行も返す。"""
    rows = fr[u"注入の行"]
    allp = [r for r in rows if all((r[u"結果"].get(p) or [None])[0] == "GROUNDED" for p in PROFILES5)]
    anyp = [r for r in rows if any((r[u"結果"].get(p) or [None])[0] == "GROUNDED" for p in PROFILES5)]
    return allp, anyp


def positions(rec):
    u"""{id: (書類の番号, その書類の中の行の番号)}(記録の出てくる順。1 始まり)。"""
    order = rec[u"書類(出てくる順)"]
    seen, out = collections.Counter(), {}
    for r in rec[u"rows"]:
        d = order.index(r["doc"]) + 1
        seen[d] += 1
        out[r["id"]] = (d, seen[d])
    return out


def label(p):
    return u"書類 %d・行 %d" % p


def by_position(rec):
    pos = positions(rec)
    return dict((pos[r["id"]], r) for r in rec[u"rows"])


def fv0(side):
    u"""pointers の先頭の fact の value(無ければ None)。"""
    f = side[u"fact"]
    return f[0][u"facts"][0]["value"] if f and f[0][u"facts"] else None


def yesno(b):
    return u"はい" if b else u"いいえ"


def fmt_num(x):
    if x is None:
        return u"―"
    if isinstance(x, str):
        return x
    return u"%.4g" % x


# ----------------------------------------------------------------------------------------------------------------
# (e) 分類を別の書き方で求め直す(記録の claim の欄だけから。記録の 比較 の欄と 分類 の欄は読まない)
def reclassify(x):
    base, after = x[u"無改変"][u"claim"], x[u"注入後"][u"claim"]
    if base is None or after is None:
        return u"(エ)"
    if sorted(base["pointers"]) != sorted(after["pointers"]) or list(base["pointers"]) != list(after["pointers"]):
        return u"(イ)"
    tsent = x[u"token"][u"差し替えた token がある文の番号"]
    if base["unit"] == after["unit"]:
        if tsent is None:
            return u"(エ)"
        return u"(ウ-b)" if x[u"無改変"][u"文の番号"] == tsent else u"(ウ-a)"
    if after["state"] != "GROUNDED":
        return u"(エ)"
    scale_keys = YEN_FAMILY   # 円族 5 単位(UNIT_SCALE の key。封 §0-5)
    inside = [u in scale_keys for u in (base["unit"], after["unit"])]
    return u"(ア-1)" if not any(inside) else u"(ア-2)"


def check_e(rec):
    u"""問題の列(空なら通す)。"""
    out = []
    for r in rec[u"rows"]:
        for p in OBS:
            x = r[u"profile"][p]
            if reclassify(x) != x[u"分類"]:
                out.append(u"%s %s: 分類が求め直しと違う(%s != %s)" % (r["id"], p, x[u"分類"], reclassify(x)))
            base, after = x[u"無改変"][u"claim"], x[u"注入後"][u"claim"]
            c = x[u"比較"]
            if c[u"pointers が同じ"] != (base["pointers"] == after["pointers"]):
                out.append(u"%s %s: 比較の欄 pointers が claim と食い違う" % (r["id"], p))
            if c[u"unit が変わった"] != (base["unit"] != after["unit"]):
                out.append(u"%s %s: 比較の欄 unit が claim と食い違う" % (r["id"], p))
            if c[u"state が同じ"] != (base["state"] == after["state"]):
                out.append(u"%s %s: 比較の欄 state が claim と食い違う" % (r["id"], p))
            if c[u"元の token の位置が無改変の claim の文の中に在る"] != (x[u"token"][u"差し替えた token がある文の番号"] is not None
                                                                          and x[u"無改変"][u"文の番号"] == x[u"token"][u"差し替えた token がある文の番号"]):
                out.append(u"%s %s: 比較の欄 token の位置が文の番号と食い違う" % (r["id"], p))
    return out


# ----------------------------------------------------------------------------------------------------------------
# (a)(b)
def check_a(rec, fr):
    out = []
    allp, anyp = passed_rows(fr)
    if [r["id"] for r in allp] != [r["id"] for r in anyp]:
        out.append(u"どれか 1 つの profile で GROUNDED の行が、全部 GROUNDED の行と違う")
    ids = [r["id"] for r in allp]
    if rec[u"通した行(記録から)"] != ids:
        out.append(u"記録の『通した行(記録から)』が fresh から機械で選んだ行と違う")
    if sorted(r["id"] for r in rec[u"rows"]) != sorted(ids):
        out.append(u"記録の rows の id が fresh から機械で選んだ行と違う")
    by_id = dict((r["id"], r) for r in fr[u"注入の行"])
    for r in rec[u"rows"]:
        f = by_id[r["id"]]
        if (r["doc"], r[u"元の字"], r[u"後の字"], r[u"基準の claim"]) != (f["doc"], f[u"元の字"], f[u"後の字"], f[u"基準の claim"]):
            out.append(u"%s: 元の字・後の字・基準の claim が fresh の行と違う" % r["id"])
        for p in PROFILES5:
            if f[u"結果"][p] != r[u"結果"][p]:
                out.append(u"%s: 結果 %s が fresh の行と違う" % (r["id"], p))
    return out


def check_b(rec, fr, fetched):
    out = []
    g = rec[u"配線の門"]
    t2 = [r for r in fr[u"注入の行"] if r[u"型"] == "T2_UNIT" and r["doc"] in rec[u"書類(出てくる順)"]]
    if not (g[u"通った"] and g[u"行"] == g[u"一致"] == len(t2) == len(g[u"行ごと"])):
        out.append(u"配線の門が 13 / 13 でない(行 %s・一致 %s・記録の T2 の行 %s)" % (g[u"行"], g[u"一致"], len(t2)))
    if sorted(w["id"] for w in g[u"行ごと"]) != sorted(r["id"] for r in t2):
        out.append(u"配線の門の行の id の集合が fresh の T2_UNIT の行と違う")
    for w in g[u"行ごと"]:
        f = w[u"一致"]
        if not all(f[k] for k in (u"記録に同じ id の行が在る", u"元の字", u"後の字", u"基準の claim", u"結果(P22〜P26)", u"4 欄とも一致")):
            out.append(u"%s: 4 欄のどれかが一致していない" % w["id"])
    if not g[u"通した行の id が記録から機械で選んだ行と一致"]:
        out.append(u"通した行の id の旗が偽")
    counts = fr[u"注入の件数(書類別)"]
    used = dict((r["docID"], r) for r in fetched[u"取得した書類"])
    for doc in rec[u"書類(出てくる順)"]:
        d = rec[u"書類ごと"][doc]
        want = counts[doc]["T2_UNIT"][u"注入の行になった"]
        if d[u"T2 の行"] != want or d[u"配線の一致"] != want:
            out.append(u"%s: T2 の行 %s・配線の一致 %s が注入の件数(書類別) %s と違う" % (doc, d[u"T2 の行"], d[u"配線の一致"], want))
        if not (d[u"材料の sha256 が取得の記録と一致"] and d[u"材料の sha256"] == used[doc]["sha256"]):
            out.append(u"%s: 材料の sha256 が取得の記録と違う" % doc)
    c = rec[u"cache"]
    if c[u"開始"] != c[u"終了"] or c[u"開始"][u"edinet"] != 281 or c[u"開始"][u"edinet-fresh-2026-10-21"] != 40:
        out.append(u"cache の件数が 281 / 40 のまま動いていない")
    if rec[u"key_leaks"] != []:
        out.append(u"key_leaks が空でない")
    return out


# ----------------------------------------------------------------------------------------------------------------
# (d) T-1〜T-8(と T-3a)の当否を記録から求める
def n_of(n, d):
    return u"%d / %d" % (n, d)


def judge(rec, fr):
    u"""{名前: (実測の字, 当たりか)}。封 §3 の予測を記録から。"""
    P = by_position(rec)
    out = collections.OrderedDict()
    # T-1
    g = rec[u"配線の門"]
    ids_ok = bool(g[u"通した行の id が記録から機械で選んだ行と一致"]) and sorted(r["id"] for r in rec[u"rows"]) == sorted(r["id"] for r in passed_rows(fr)[0])
    out["T-1"] = (u"配線の門 %s(記録の T2_UNIT の行 %d)。通した 5 行の id が記録から機械で選んだ行と一致: %s" % (n_of(g[u"一致"], g[u"行"]), len(g[u"行ごと"]), yesno(ids_ok)),
                  bool(g[u"通った"]) and g[u"一致"] == g[u"行"] == 13 and ids_ok)
    # T-2: 書類 1・行 1
    r = P[(1, 1)]
    cl = [(p, r[u"profile"][p][u"分類"]) for p in OBS]
    out["T-2"] = (u"%s: %s" % (label((1, 1)), u"・".join(u"%s %s" % c for c in cl)), all(c[1] == u"(ア-1)" for c in cl))
    # T-3: 書類 2・行 1〜3
    rs = [P[(2, k)] for k in (1, 2, 3)]
    same = sum(1 for r in rs for p in OBS if all(r[u"profile"][p][u"比較"][k] for k in (u"pointers が同じ", u"value が同じ", u"recomputed が同じ")))
    unit = sum(1 for r in rs for p in OBS if r[u"profile"][p][u"注入後"][u"claim"]["unit"] == u"百万円")
    ucls = [[r[u"profile"][p][u"分類"] for p in OBS] for r in rs]
    out["T-3"] = (u"%s: %s(3 profile とも。pointers・value・recomputed が無改変と同じ %s、注入後の unit が百万円のまま %s)" % (
        u"書類 2", u"・".join(u"行 %d %s" % (k + 1, u"/".join(sorted(set(c)))) for k, c in enumerate(ucls)), n_of(same, 9), n_of(unit, 9)),
        all(c.startswith(u"(ウ") for cs in ucls for c in cs) and same == 9 and unit == 9)
    # T-3a: 書類 2・行 1 と 行 3(同じ基準の claim)
    same_base = P[(2, 1)][u"基準の claim"] == P[(2, 3)][u"基準の claim"]
    per = [(p, sum(1 for k in (1, 3) if P[(2, k)][u"profile"][p][u"分類"] == u"(ウ-a)")) for p in OBS]
    out["T-3a"] = (u"行 1 と 行 3 の基準の claim が同じ: %s。(ウ-a) の行(%s)" % (yesno(same_base), u"・".join(u"%s %s" % (p, n_of(n, 2)) for p, n in per)),
                   same_base and all(n >= 1 for _p, n in per))
    # T-4: 書類 3・行 1
    cl = [(p, P[(3, 1)][u"profile"][p][u"分類"]) for p in OBS]
    out["T-4"] = (u"%s: %s" % (label((3, 1)), u"・".join(u"%s %s" % c for c in cl)), all(c[1].startswith(u"(ウ") for c in cl))
    # T-5: 注入後の対応の付け方
    yen = [r for r in rec[u"rows"] if r[u"元の字"] in YEN_FAMILY]
    parts, hit = [], True
    for p in OBS:
        n_value = sum(1 for r in yen if r[u"profile"][p][u"注入後"][u"対応の付け方"] == u"値だけ")
        first = P[(1, 1)][u"profile"][p][u"注入後"][u"対応の付け方"]
        parts.append(u"%s 円族 %s が値だけ・書類 1・行 1 は%s" % (p, n_of(n_value, len(yen)), first))
        hit = hit and n_value >= 3 and first == u"値と字"
    out["T-5"] = (u"・".join(parts), hit)
    # T-6
    n_g = sum(1 for r in rec[u"rows"] if r[u"profile"]["P27"][u"注入後"][u"claim"]["state"] == "GROUNDED")
    n_p = sum(1 for r in rec[u"rows"] if r[u"profile"]["P27"][u"注入後"][u"claim"]["pointers"] == r[u"profile"]["P26"][u"注入後"][u"claim"]["pointers"]
              and r[u"profile"]["P27"][u"注入後"][u"claim"]["state"] == r[u"profile"]["P26"][u"注入後"][u"claim"]["state"])
    bases = collections.OrderedDict()
    for r in rec[u"rows"]:
        bases.setdefault(r[u"基準の claim"], r)
    b_g = sum(1 for r in bases.values() for p in OBS if r[u"profile"][p][u"無改変"][u"claim"]["state"] == "GROUNDED")
    b_p = sum(1 for r in bases.values() if len(set(json.dumps(r[u"profile"][p][u"無改変"][u"claim"]["pointers"]) for p in OBS)) == 1)
    out["T-6"] = (u"P27 の注入後の state が GROUNDED %s・pointers と state が P26 と同じ %s。無改変の基準の claim %d つ: 3 profile で GROUNDED %s・pointers が 3 profile で同じ %s" % (
        n_of(n_g, 5), n_of(n_p, 5), len(bases), n_of(b_g, 3 * len(bases)), n_of(b_p, len(bases))),
        n_g == 5 and n_p == 5 and len(bases) == 4 and b_g == 12 and b_p == 4)
    # T-7
    vals = [fv0(r[u"profile"][p][side]) for r in rec[u"rows"] for p in OBS for side in (u"無改変", u"注入後")]
    n_zero = sum(1 for v in vals if v == 0)
    n_none = sum(1 for v in vals if v is None)
    out["T-7"] = (u"先頭の fact の value が 0 の観測 %s(fact が無い %d)" % (n_of(n_zero, len(vals)), n_none), n_zero == 0 and n_none == 0)
    # T-8: P26 の型の集計
    cnt = collections.Counter(r[u"profile"]["P26"][u"分類"] for r in rec[u"rows"])
    u_n = cnt[u"(ウ-a)"] + cnt[u"(ウ-b)"]
    out["T-8"] = (u"(ウ) %d・(ア-1) %d・(イ) %d・(ア-2) %d・(エ) %d" % (u_n, cnt[u"(ア-1)"], cnt[u"(イ)"], cnt[u"(ア-2)"], cnt[u"(エ)"]),
                  (u_n, cnt[u"(ア-1)"], cnt[u"(イ)"], cnt[u"(ア-2)"], cnt[u"(エ)"]) == (4, 1, 0, 0, 0))
    return out


def seal_predictions(seal):
    u"""封 §3 の表の行 {名前: (欄, 予測, 外れ方)}(封の字のまま)。"""
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(T-\d+a?)\*\* \| (.*) \|$", l)
        if m:
            cells = m.group(2).split(u" | ")
            assert len(cells) == 3, l
            out[m.group(1)] = tuple(c.strip() for c in cells)
    return out


def hit_word(b):
    return u"**当たり**" if b else u"**外れ**"


# ----------------------------------------------------------------------------------------------------------------
# (c) 文書の表
def table(head, rows):
    lines = [u"| " + u" | ".join(head) + u" |", u"|" + u"|".join(u"---" for _ in head) + u"|"]
    for r in rows:
        lines.append(u"| " + u" | ".join(r) + u" |")
    return lines


def render_blocks(rec, fr, seal):
    B = collections.OrderedDict()
    pos = positions(rec)
    order = rec[u"書類(出てくる順)"]
    J = judge(rec, fr)
    SP = seal_predictions(seal)
    assert list(SP) == list(J), list(SP)
    B["pred"] = table([u"#", u"欄", u"予測(封の字)", u"外れ方(封の字)", u"実測(記録から)", u"当たり外れ"],
                      [[u"**%s**" % k, SP[k][0], SP[k][1], SP[k][2], J[k][0], hit_word(J[k][1])] for k in J])
    # 材料と配線
    g = rec[u"配線の門"]
    B["sha"] = table([u"書類", u"材料の sha256(取得の記録と一致)", u"T2 の行", u"配線の一致", u"claim(P22)", u"claim(P27)", u"fact", u"T2 の作れる site", u"採った"],
                     [[u"書類 %d" % (i + 1), rec[u"書類ごと"][d][u"材料の sha256"], str(rec[u"書類ごと"][d][u"T2 の行"]), str(rec[u"書類ごと"][d][u"配線の一致"]),
                       str(rec[u"書類ごと"][d][u"claims(P22)"]), str(rec[u"書類ごと"][d][u"claims(P27)"]), str(rec[u"書類ごと"][d][u"facts"]),
                       str(rec[u"書類ごと"][d][u"T2 の作れる site"]), str(rec[u"書類ごと"][d][u"採った"])] for i, d in enumerate(order)])
    wrows, kcount = [], collections.Counter()
    for w in g[u"行ごと"]:
        d = order.index(w["doc"]) + 1
        kcount[d] += 1
        f = w[u"一致"]
        wrows.append([u"書類 %d・T2 の %d 番目" % (d, kcount[d]), u"%s → %s" % (w[u"元の字"], w[u"後の字"]), yesno(f[u"元の字"]), yesno(f[u"後の字"]), yesno(f[u"基準の claim"]),
                      yesno(f[u"結果(P22〜P26)"]), yesno(f[u"4 欄とも一致"]),
                      label(pos[w["id"]]) if w["id"] in pos else u"―"])
    B["wiring"] = table([u"位置", u"元の字 → 後の字", u"元の字が一致", u"後の字が一致", u"基準の claim が一致", u"結果(P22〜P26)が一致", u"4 欄とも", u"通した行の位置"], wrows) + [
        u"", u"| 配線の門 | 値 |", u"|---|---|",
        u"| 作り直した行 / 4 欄とも一致 | %s |" % n_of(g[u"一致"], g[u"行"]), u"| 記録の T2_UNIT の行(3 書類) | %d |" % g[u"記録の T2_UNIT の行(3 書類)"],
        u"| id の集合が記録と同じ | %s |" % yesno(g[u"id の集合が記録と同じ"]), u"| 通した行の id が記録から機械で選んだ行と一致 | %s |" % yesno(g[u"通した行の id が記録から機械で選んだ行と一致"])]
    # 環境
    eng = rec[u"engine sha16"]
    B["engine"] = table([u"項目", u"値"], [[u"`%s` の sha16" % k, u"`%s`" % v] for k, v in eng.items()] + [
        [u"DEFAULT_PROFILE", rec[u"DEFAULT_PROFILE"]], [u"測った木の HEAD", u"`%s`" % rec[u"HEAD"]], [u"封の commit", u"`%s`" % rec[u"封"][u"commit"]],
        [u"cache `edinet/`(開始 → 終了)", u"%d → %d" % (rec[u"cache"][u"開始"][u"edinet"], rec[u"cache"][u"終了"][u"edinet"])],
        [u"cache `edinet-fresh-2026-10-21/`(開始 → 終了)", u"%d → %d" % (rec[u"cache"][u"開始"][u"edinet-fresh-2026-10-21"], rec[u"cache"][u"終了"][u"edinet-fresh-2026-10-21"])],
        [u"key_leaks", str(len(rec[u"key_leaks"]))]])
    # 観測
    orows = []
    for r in rec[u"rows"]:
        for p in OBS:
            x = r[u"profile"][p]
            b, a = x[u"無改変"], x[u"注入後"]
            ex0 = {True: u"はい", False: u"いいえ", None: u"―"}[b[u"digits_unchanged が claim の数の字と完全一致"]]
            ex1 = {True: u"はい", False: u"いいえ", None: u"―"}[a[u"digits_unchanged が claim の数の字と完全一致"]]
            tcl = x[u"token"][u"token の位置を文に持つ claim の数(無改変, 注入後)"]
            tin = x[u"token"][u"差し替えた token がある文の番号"] is not None and b[u"文の番号"] == x[u"token"][u"差し替えた token がある文の番号"]
            orows.append([label(pos[r["id"]]), p, u"%s → %s" % (r[u"元の字"], r[u"後の字"]), b[u"対応の付け方"], a[u"対応の付け方"], u"%s / %s" % (ex0, ex1),
                          yesno(tin), u"%d / %d" % tuple(tcl), yesno(b[u"claim"]["pointers"] == a[u"claim"]["pointers"]),
                          yesno(b[u"claim"]["unit"] != a[u"claim"]["unit"]), yesno(x[u"比較"][u"後の字が注入後の span に在る(字の包含)"]), a[u"claim"]["state"], x[u"分類"]])
    B["obs"] = table([u"位置", u"profile", u"元の字 → 後の字", u"対応の付け方(無改変)", u"対応の付け方(注入後)", u"数の字の完全一致(無改変 / 注入後)", u"token の位置が無改変の claim の文の中に在る",
                      u"token の文に在る claim の数(無改変 / 注入後)", u"pointers が同じ", u"unit が変わった", u"後の字が span に在る(字の包含)", u"注入後の state", u"分類"], orows)
    # fact(P27)
    frows = []
    for r in rec[u"rows"]:
        x = r[u"profile"]["P27"]
        b, a = x[u"無改変"], x[u"注入後"]
        f = a[u"fact"][0][u"facts"][0] if a[u"fact"] and a[u"fact"][0][u"facts"] else {}
        c = x[u"比較"]
        frows.append([label(pos[r["id"]]), u"`%s@%s`" % (f.get("name"), f.get("context")), fmt_num(f.get("value")), str(f.get("unit")), str(f.get("decimals")),
                      u"%s / %s" % tuple(fmt_num(v) for v in c[u"倍率(無改変, 注入後)"]), u"%s / %s" % (fmt_num(b[u"claim"]["value"]), fmt_num(a[u"claim"]["value"])),
                      fmt_num(c[u"無改変 value×倍率 / fact"]), fmt_num(c[u"注入後 value×倍率 / fact"]), yesno(x[u"fact が 0"])])
    B["fact"] = table([u"位置", u"pointers の先頭の fact", u"fact の value", u"unit", u"decimals", u"倍率(無改変 / 注入後。UNIT_SCALE に無ければ ―)", u"claim の value(無改変 / 注入後)",
                       u"無改変 value×倍率 / fact", u"注入後 value×倍率 / fact", u"fact が 0"], frows)
    # profile 間
    prow = []
    for r in rec[u"rows"]:
        v = [r[u"profile"][p] for p in OBS]
        same_claims = all(json.dumps(x[u"無改変"][u"claim"], sort_keys=True) == json.dumps(v[0][u"無改変"][u"claim"], sort_keys=True)
                          and json.dumps(x[u"注入後"][u"claim"], sort_keys=True) == json.dumps(v[0][u"注入後"][u"claim"], sort_keys=True) for x in v)
        prow.append([label(pos[r["id"]]), yesno(same_claims), yesno(len(set(x[u"分類"] for x in v)) == 1), yesno(len(set(json.dumps(x[u"token"], sort_keys=True) for x in v)) == 1)])
    B["profiles"] = table([u"位置", u"P22・P26・P27 で無改変の claim と注入後の claim が同じ(id・value・unit・span・state・reason・pointers・recomputed)", u"分類が同じ",
                           u"token の文・claim の数・その文の claim が同じ"], prow)
    # token の文の claim(P27)
    trows = []
    for r in rec[u"rows"]:
        t = r[u"profile"]["P27"][u"token"]

        def cell(lst):
            return u"; ".join(u"位置 %s %s %s %s(%s)" % (c["pos"], c["form"], c["unit"], c["state"], c["reason"]) for c in lst) if lst else u"なし"
        trows.append([label(pos[r["id"]]), cell(t[u"その文の claim"][u"無改変"]), cell(t[u"その文の claim"][u"注入後"])])
    B["tokensent"] = table([u"位置", u"token がある文の claim(無改変。文中の位置・form・unit・state・reason)", u"同(差し替え後)"], trows)
    # 分類の集計
    keys = [u"(ウ-a)", u"(ウ-b)", u"(イ)", u"(ア-1)", u"(ア-2)", u"(エ)"]
    crow = []
    for k in keys:
        crow.append([k] + [str(sum(1 for r in rec[u"rows"] if r[u"profile"][p][u"分類"] == k)) for p in OBS])
    crow.append([u"計"] + [str(len(rec[u"rows"])) for _ in OBS])
    B["classes"] = table([u"分類"] + list(OBS), crow)
    # 位置 → 記録の根拠(token の文の番号)
    return B


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
    bad = [l[:40] for l in stripped.split(u"\n") if re.search(r"\d+(?:\.\d+)?\s*(?:%|行|件|社|席|書類|試行|回|本|ポイント|USD|file|倍|桁|字)", l) and NOT_GATED not in l]
    if bad:
        out.append(u"散文の数に【門なし】の印が無い: %s" % bad)
    heads = re.findall(r"^## (\d+)\.", doc, re.M)
    if heads != [str(i) for i in range(1, len(heads) + 1)] or len(heads) < 8:
        out.append(u"節の番号が 1 から続いていない・8 節に足りない: %s" % heads)
    if not (doc.index(u"<!-- 門:start pred -->") < doc.index(u"## 2.")):
        out.append(u"予測の当否が先頭(第 2 節より前)にない")
    J = judge(rec, fr)
    missed = [k for k, v in J.items() if not v[1]]
    want = u"外れた予測: " + (u"・".join(missed) if missed else u"なし") + u"。外れは外れのまま残す(封も予測も直さない)。" + NOT_GATED
    if sum(1 for l in doc.split(u"\n") if l.strip() == want) != 1:
        out.append(u"『外れた予測』の行が記録から求めた当否と違う(期待: %s)" % want)
    for lit in (u"記録は不変", u"配線の数", u"engine が単位の誤りを通した数ではない", u"仮説。測るまで断定しない", u"測っていない", u"診断だけ", NOT_GATED, u"edinetdb-p27"):
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
def check_h(seal, doc, fetched):
    out = []
    docs = list(fetched[u"使う書類"])
    for name, t in ((u"封", seal), (u"文書", doc)):
        for d in docs:
            if d in t:
                out.append(u"%s に docID の字がある: %s" % (name, d))
        if re.findall(r"S100[0-9A-Z]{4}", t):
            out.append(u"%s に docID らしい字がある" % name)
        if re.findall(r"\b[NT]\d{3}\b", t):
            out.append(u"%s に claim の id らしい字がある" % name)
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
        self.dir = tempfile.mkdtemp(prefix="t2diag_", dir=base)
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

    def test_a_1_the_five_rows_are_the_machine_selected_ones(self):
        self.assertEqual(check_a(self.rec, self.fr), [])
        self.assertEqual(len(self.rec[u"rows"]), 5)
        allp, anyp = passed_rows(self.fr)
        self.assertEqual(len(allp), len(anyp))
        self.assertEqual(set(r[u"型"] for r in allp), {"T2_UNIT"})

    def test_a_2_the_selection_is_not_hardcoded(self):
        u"""fresh の写しで 1 行の P26 の結果を GROUNDED でなくすと、選ばれる行が変わる(選び方が字で留められていない)。"""
        fr = copy.deepcopy(self.fr)
        pid = self.rec[u"通した行(記録から)"][0]
        for r in fr[u"注入の行"]:
            if r["id"] == pid:
                r[u"結果"]["P26"] = ["VALUE_MISMATCH", None]
        self.assertNotEqual([r["id"] for r in passed_rows(fr)[0]], self.rec[u"通した行(記録から)"])
        self.assertNotEqual(check_a(self.rec, fr), [])

    def test_b_1_the_wiring_gate_is_13_of_13(self):
        self.assertEqual(check_b(self.rec, self.fr, self.fetched), [])
        g = self.rec[u"配線の門"]
        self.assertEqual((g[u"一致"], g[u"行"]), (13, 13))
        per = [self.rec[u"書類ごと"][d][u"T2 の行"] for d in self.rec[u"書類(出てくる順)"]]
        self.assertEqual(per, [6, 4, 3])

    def test_e_1_the_classes_are_recomputed_from_the_claims(self):
        self.assertEqual(check_e(self.rec), [])

    def test_e_2_every_row_has_the_three_profiles_and_the_known_fields(self):
        for r in self.rec[u"rows"]:
            self.assertEqual(list(r[u"profile"]), list(OBS))
            for p in OBS:
                x = r[u"profile"][p]
                for side in (u"無改変", u"注入後"):
                    self.assertIn(x[side][u"対応の付け方"], (u"値と字", u"値だけ"))
                    self.assertIsNotNone(x[side][u"claim"])
                self.assertTrue(x[u"注入後"][u"claim_for と同じ"])
                self.assertIn(u"digits_unchanged が claim の数の字と完全一致", x[u"無改変"])
                self.assertIn(u"token の位置を文に持つ claim の数(無改変, 注入後)", x[u"token"])

    def test_e_3_the_five_rows_all_pass_in_all_three_profiles(self):
        for r in self.rec[u"rows"]:
            for p in OBS:
                self.assertEqual(r[u"profile"][p][u"注入後"][u"claim"]["state"], "GROUNDED", (r["id"], p))
            for p in PROFILES5:
                self.assertEqual(r[u"結果"][p][0], "GROUNDED", (r["id"], p))

    def test_d_1_judgments_are_recomputed_and_cover_the_nine_predictions(self):
        J = judge(self.rec, self.fr)
        self.assertEqual(list(J), ["T-1", "T-2", "T-3", "T-3a", "T-4", "T-5", "T-6", "T-7", "T-8"])
        self.assertTrue(all(isinstance(v[1], bool) for v in J.values()))

    def test_d_2_the_judge_is_not_a_constant(self):
        u"""記録の写しで T-3(書類 2・行 1 の分類を (ア-1) にする)と T-1(配線の件数を 12 にする)を変えると、当否が変わる。"""
        J0 = judge(self.rec, self.fr)
        rec = copy.deepcopy(self.rec)
        P = by_position(rec)
        P[(2, 1)][u"profile"]["P26"][u"分類"] = u"(ア-1)"
        self.assertTrue(J0["T-3"][1] and not judge(rec, self.fr)["T-3"][1])
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"一致"] = 12
        self.assertTrue(J0["T-1"][1] and not judge(rec, self.fr)["T-1"][1])
        rec = copy.deepcopy(self.rec)
        by_position(rec)[(3, 1)][u"profile"]["P27"][u"分類"] = u"(ア-2)"
        self.assertTrue(J0["T-4"][1] and not judge(rec, self.fr)["T-4"][1])


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
        J = judge(self.rec, self.fr)
        got = doc_blocks(self.doc)["pred"]
        self.assertEqual(len(got), 2 + len(J))
        for line, k in zip(got[2:], J):
            cells = [c.strip() for c in line.strip().strip(u"|").split(u" | ")]
            self.assertEqual(cells[0], u"**%s**" % k)
            self.assertEqual(tuple(cells[1:4]), SP[k], k)                  # 封の字(欄・予測・外れ方)のまま
            self.assertEqual(cells[4], J[k][0], k)                          # 実測は記録から
            self.assertEqual(cells[5], hit_word(J[k][1]), k)                # 当否は記録から

    def test_d_4_the_seal_prediction_table_is_what_this_gate_reads(self):
        SP = seal_predictions(self.seal)
        self.assertEqual(list(SP), ["T-1", "T-2", "T-3", "T-3a", "T-4", "T-5", "T-6", "T-7", "T-8"])
        self.assertIn(u"**13 / 13**", SP["T-1"][1])
        self.assertIn(u"**(ア-1)**", SP["T-2"][1])
        self.assertIn(u"(ウ) **4** 行・(ア-1) **1** 行", SP["T-8"][1])

    def test_d_5_the_misses_are_kept_as_misses(self):
        J = judge(self.rec, self.fr)
        self.assertEqual([k for k, v in J.items() if not v[1]], ["T-2", "T-5", "T-8"])
        self.assertEqual([k for k, v in J.items() if v[1]], ["T-1", "T-3", "T-3a", "T-4", "T-6", "T-7"])

    def test_h_1_no_docid_and_no_claim_id_in_the_seal_and_the_document(self):
        self.assertEqual(check_h(self.seal, self.doc, self.fetched), [])
        self.assertEqual(len(self.fetched[u"使う書類"]), 30)

    def test_h_2_the_record_names_the_documents_and_that_is_why_it_is_declared(self):
        txt = jtext(REC)
        docs = self.fetched[u"使う書類"]
        self.assertTrue(any(d in txt for d in docs))
        later = ("fixtures/xbrl/t2_pass_diag_2026-10-28.json", "measure/xbrl_t2_pass_diag_2026-10-28.py", "tests/measure/test_xbrl_t2_pass_diag.py")
        fresh_seal = jtext(os.path.join(HERE, "test_xbrl_fresh_seal.py"))
        for p in later:
            self.assertIn(u'"%s"' % p, fresh_seal, p)

    def test_doc_states_the_dated_note_about_the_record_of_five(self):
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
        rec[u"rows"][1][u"profile"]["P26"][u"分類"] = u"(ア-1)"
        self.assertNotEqual(check_e(rec), [])
        self.assertNotEqual(check_c(rec, self.fr, self.seal, self.doc), [])
        self.assertEqual(check_b(rec, self.fr, self.fetched), [])                # b は分類を見ない(1 つの性質は所有する 1 か所で)

    def test_g_2_changing_one_pointer_turns_e_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"rows"][2][u"profile"]["P27"][u"注入後"][u"claim"]["pointers"] = ["xbrl:jppfs_cor:Other@CurrentYearDuration"]
        self.assertNotEqual(check_e(rec), [])
        self.assertNotEqual(check_c(rec, self.fr, self.seal, self.doc), [])

    def test_g_3_changing_the_wiring_flag_turns_b_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"行ごと"][0][u"一致"][u"4 欄とも一致"] = False
        self.assertNotEqual(check_b(rec, self.fr, self.fetched), [])
        self.assertNotEqual(check_c(rec, self.fr, self.seal, self.doc), [])

    def test_g_4_changing_the_wiring_count_turns_b_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"一致"] = 12
        self.assertNotEqual(check_b(rec, self.fr, self.fetched), [])
        self.assertNotEqual(check_c(rec, self.fr, self.seal, self.doc), [])

    def test_g_5_changing_the_matching_kind_turns_c_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"rows"][0][u"profile"]["P22"][u"注入後"][u"対応の付け方"] = u"値と字"
        self.assertNotEqual(check_c(rec, self.fr, self.seal, self.doc), [])

    def test_g_6_one_character_of_the_document_table_turns_c_red(self):
        i = self.doc.index(u"<!-- 門:start obs -->")
        doc = self.doc[:i] + self.doc[i:].replace(u"(ウ-a)", u"(ウ-b)", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(check_c(self.rec, self.fr, self.seal, doc), [])
        i = self.doc.index(u"<!-- 門:start pred -->")
        doc = self.doc[:i] + self.doc[i:].replace(u"**外れ**", u"**当たり**", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(check_c(self.rec, self.fr, self.seal, doc), [])

    def test_g_7_changing_a_prediction_character_of_the_seal_turns_c_red(self):
        seal = u"\n".join(l.replace(u"**(ア-1)**", u"**(ア-2)**", 1) if l.startswith(u"| **T-2**") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(check_c(self.rec, self.fr, seal, self.doc), [])

    def test_g_8_a_docid_in_the_document_turns_h_red(self):
        doc = self.doc + u"\n" + self.fetched[u"使う書類"][0] + u"\n"
        self.assertNotEqual(check_h(self.seal, doc, self.fetched), [])
        doc = self.doc + u"\nN012\n"
        self.assertNotEqual(check_h(self.seal, doc, self.fetched), [])

    def test_g_9_an_unmarked_number_in_prose_turns_the_prose_check_red(self):
        doc = self.doc + u"\n通した行は 7 行だった。\n"
        self.assertNotEqual(check_doc_prose(self.rec, self.fr, self.seal, doc), [])


class OrderTest(unittest.TestCase):
    u"""(i) 封の commit が script・記録・文書・門の commit より前。"""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="t2diag_root_")
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
