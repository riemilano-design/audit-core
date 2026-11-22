# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PRIOR_YEAR_FACT_DRAFT_SEAL_2026-11-22.md(XZ0 ― 前の年の「表の中の置き場 → 数の fact の属性」を今年の下書きに使う)の封の門。

**この門は置き場を読まない**(今年の側・前の年の側の置き場は 1 度も開かない)。通信しない。
読むのは repo の中の封の file・script だけ。作り物の zip(今年の側と前の年の側の組)を、本物の関数のまま通す。作り物の字は全部作り物(本物の見出し・要素・文脈の名は使わない)。

**この門が縛るもの**

1. 封の字: 封の commit(4ee140d2)・封の file が commit した blob と同じ・組の数 63・今年の側 67 本・file の名(script・記録・門)・予測の境(XZ0-1〜XZ0-8)・
   先に疑う旗の 4 つの境・記録に書かないものの字・限界の 7 行・鍵の 4 つの部品・2 つの表・3 つの段・2 つの束・6 つの類の字が script の定数と同じ。
2. engine は封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 作り物の組で、鍵の 4 つの部品(見出し h・表の番号 th・行の字 T・セルの番号 td)・表 HT と表 H・段 HT・H・F(落とし先)・束 3 と束 5(空の欄は束 5 に入れない)・
   類 X・U・A・W1・W2・N・属性ごとの類・行の外の fact の数・空の欄の扱いを、手で数えた値と照らす(類ごとに違う数)。
4. 今年の fact の属性は、候補を作る関数(段 HT・段 H・段 F)に渡さない。前の年の側として今年の zip を読まない。
5. 記録の禁止の検査(docID・EDINET コード・行の字・見出しの字・要素・文脈・単位の字・日付の形)が作り物で止まる。先に疑う旗は止めず記録に書き、境(ちょうど 95%・30%・70%・5%)で変わる。
6. script の import は標準ライブラリと engine の 2 module(instance・verify_document)と importlib だけ。前の便の script は importlib で読み(一意の名)、関数は呼ぶ(写さない)。
7. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
黙る変異は ``SILENT_BY_DESIGN`` に理由とともに置き、「黙ること」自体を別の試験で縛る。
記録(``fixtures/xbrl/cd8/prior_year_fact_draft_2026-11-22.json``)は本番の走りの後に書かれる。記録が在れば中身を見て、無ければ見ない(skip にしない。見る作りが「在れば」)。
"""
import ast
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)


def load_module(rel, name):
    u"""importlib で読み込む。読み込みの前に居た名前は、読み込みの後に元の object へ戻す(自分の名前 ``name`` は残す)。"""
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


def load_source(src):
    u"""script の字(``src``)から module を memory の中に作る。file は読み書きしない。``__file__`` は本物の script。"""
    mod = types.ModuleType("xbrl_prior_year_fact_draft_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_PRIOR_YEAR_FACT_DRAFT_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "4ee140d2"                # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_prior_year_fact_draft_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_prior_year_fact_draft_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/prior_year_fact_draft_2026-11-22.json"
MS = load_module(SCRIPT_REL, "xbrl_prior_year_fact_draft_script_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_prior_year_fact_draft_seal")      # 順序・履歴の部品。門としては走らせない
ORDER_FILES = (SCRIPT_REL, GATE_REL)          # 記録の順序は記録が在るときの結果の門に置く
od = collections.OrderedDict
CLS = ("X", "U", "A", "W1", "W2", "N")
LAB = {"b3": u"束 3", "b5": u"束 5", "name": u"属性 name だけ", "ctx": u"属性 contextRef だけ", "unit": u"属性 unitRef だけ", "b3nn": u"束 3(空の欄でない fact の分母)"}


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_of(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_or_none(rel):
    return sha_of(rel) if os.path.exists(os.path.join(ROOT, rel)) else None


def guard(fn, *a, **kw):
    u"""fn が例外(``SystemExit`` を含む)を投げたら、その例外の型の名前の字を返す。違いを見るための道具。"""
    try:
        return fn(*a, **kw)
    except BaseException as exc:                # noqa: BLE001
        return [u"例外: %s" % type(exc).__name__]


def stops(ms, fn, *a, **kw):
    u"""fn が ``ms.Stop`` を投げれば True。投げなければ False。別の例外は投げ直す。"""
    try:
        fn(*a, **kw)
    except ms.Stop:
        return True
    return False


class Temp(object):
    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="xz0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


def cls_of(counts):
    return tuple(counts[c] for c in CLS)


# ======================================================================== 作り物の書類
#: 要素・文脈・単位の字は全部作り物。K 系の字(Item01 など)は本物の要素の名に無い形。
EL = dict((k, u"fk:Item%s" % k) for k in ("01", "01x", "01n", "01e", "01i", "02", "03", "03b", "04", "05", "06", "07", "09", "10", "11", "12", "13", "99"))
CA, CB, UJ, US = u"ctxA", u"ctxB", u"unitJ", u"unitS"


def fact(key, ctx=CA, unit=UJ, dec=u"-6", scale=u"6", nil=False):
    u"""数の fact 1 つ。nil なら空の欄(自己閉じ・``xsi:nil="true"``)。"""
    if nil == "false":                              # xsi:nil="false" は空の欄でない
        return u'<ix:nonFraction name="%s" contextRef="%s" unitRef="%s" decimals="%s" scale="%s" xsi:nil="false">100</ix:nonFraction>' % (EL[key], ctx, unit, dec, scale)
    if nil:
        return u'<ix:nonFraction name="%s" contextRef="%s" unitRef="%s" decimals="%s" scale="%s" xsi:nil="true"/>' % (EL[key], ctx, unit, dec, scale)
    return u'<ix:nonFraction name="%s" contextRef="%s" unitRef="%s" decimals="%s" scale="%s" format="fmtZ">100</ix:nonFraction>' % (EL[key], ctx, unit, dec, scale)


def row(label, *cells):
    u"""``<tr>``: 左端のセルが行の字。あとのセルは、字 ``<ix:`` で始まれば fact・そうでなければ字そのまま。"""
    return u"<tr><td>%s</td>%s</tr>" % (label, u"".join(u"<td>%s</td>" % c for c in cells))


def head(h):
    return u"<p>【%s】</p>" % h


def table(rows):
    return u"<table>" + u"".join(rows) + u"</table>"


NO_FACT_ROW = row(u"見出し行")
EMPTY_TABLE = u"<table></table>"                    # 行を持たない表(表の通し番号だけ進む)


def prior_files():
    u"""前の年の側。p0=見出し無し・p1=見出しア(表 0・表 1)と見出しイ・p2=別の file の見出しア・p3=見出しが空の字。"""
    p0 = table([row(u"科目ア", fact("01n"))])
    p1 = (head(u"見出しア")
          + u'<p>%s</p>' % fact("99")                                                              # 行の外
          + table([row(u"科目　ア", fact("01"), fact("01", CB)),                                  # 行の字は全角の空白つき。td 1・2
                   row(u"科目イ", fact("02")),
                   row(u"科目ウ", fact("03")),
                   row(u"科目ウ", fact("03b")),
                   row(u"", fact("09")),                                                          # 行の字が無い(表に入れない)
                   row(u"科目ク", fact("11", dec=u"0", scale=u"0", nil=True)),                    # 空の欄(束 5 の表に入れない)
                   row(u"科目ク", fact("11")),
                   row(u"科目キ", fact("10")),
                   row(u"科目ケ", fact("12", nil=True))])                                         # 空の欄だけ(束 3 の表には入る・束 5 の表には入らない)
          + table([row(u"科目ア", fact("01x")), row(u"科目ｽ", fact("13"))])                      # 表 1(行の字は半角のカナ。NFKC で当たる)
          + head(u"見出しイ")
          + table([row(u"科目ア", fact("01i"))]))
    p2 = head(u"見出しア") + table([row(u"科目エ", fact("04"))])
    p3 = head(u" ") + table([row(u"科目ア", fact("01e"))])
    return [("p0_ixbrl.htm", p0), ("p1_ixbrl.htm", p1), ("p2_ixbrl.htm", p2), ("p3_ixbrl.htm", p3)]


def cur_files():
    u"""今年の側。並びは昇順でない。見出しの字は全角の空白つき(正規化して当たる)。"""
    c0 = table([row(u"科目ア", fact("01n"))])
    c1 = (head(u"見出しイ")                                                                         # 前の年の側と並びが違う(イが先)。th は見出しごと
          + table([NO_FACT_ROW, row(u"科目ア", fact("01i")), row(u"科目ア", fact("01i")), row(u"科目ア", fact("01i"))])
          + head(u"見出し　ア")
          + u'<p>%s</p>' % fact("99")                                                              # 行の外 1
          + table([NO_FACT_ROW,
                   row(u"科目ア", fact("01"), fact("01", CB)),                                    # a1: td1 HT U/H A・td2 U/U
                   row(u"科目イ", fact("02", CB)), row(u"科目イ", fact("02", CB)),                 # a2 a17: W1(文脈)
                   row(u"科目ウ", fact("03")), row(u"科目ウ", fact("03b")), row(u"科目ウ", fact("03")),  # a3 a14 a14b: A
                   row(u"科目ウ", fact("05")), row(u"科目ウ", fact("05")),                       # a4 a15: W2
                   row(u"科目オ", fact("06")), row(u"科目オ", fact("06")), row(u"科目オ", fact("06")),  # a5 a16 a19: N
                   row(u"", fact("07")),                                                          # a6: X
                   row(u"科目ク", fact("11")),                                                    # a7: 束 3 U・束 5 U
                   row(u"科目キ", fact("10", dec=u"-3", scale=u"3")),                             # a8: 束 3 U・束 5 W1
                   row(u"科目ケ", fact("12", nil=True)),                                          # a9: 空の欄(束 3 U・束 5 の外)
                   row(u"科目ケ", fact("12", nil="false")),                                       # a10: 束 3 U・束 5 N(前の年は空の欄だけ)。xsi:nil="false" は空の欄でない
                   NO_FACT_ROW])
          + EMPTY_TABLE
          + table([row(u"科目ア", fact("01x")), row(u"科目ア", fact("01x")), row(u"科目ア", fact("01x")),    # a11 ×3: HT U・H A
                   row(u"科目イ", fact("02")),                                                    # a12: HT N・H U(段 F が段 H へ落ちる)
                   row(u"科目ス", fact("13", unit=US))]))                                         # a13: 単位だけ違う W1
    c2 = head(u"見出しウ") + table([row(u"科目ア", fact("01")), row(u"科目ア", fact("01"))])             # 前の年に見出しが無い(N)
    c3 = head(u"見出しア") + table([row(u"科目エ", fact("04")),
                                    u"<tr><td>科目ア</td><th>－</th><td>%s</td></tr>" % fact("01")])   # 3 つ目のセル(td 3)。th も数える。前の年の同じ置き場は文脈が違う fact
    return [("c3_ixbrl.htm", c3), ("c1_ixbrl.htm", c1), ("c0_ixbrl.htm", c0), ("c2_ixbrl.htm", c2)]


#: 手で数える(類は X・U・A・W1・W2・N の順)。今年の fact 30 のうち空の欄 1・行の外 1・行 32(fact を持たない行 3)
#: b3 の段 HT: U 14(c0 1・a1 2・a7・a8・a9・a10・a11×3・c3 エ・イ×3)・A 3(a3 a14 a14b)・W1 4(a2 a17 a13・c3 ア td2)・W2 2(a4 a15)・N 6(a5 a16 a19・a12・見出しウ 2)・X 1(a6)
#: 段 H は a1 td1 と a11×3 が A に・a12 が U に。段 F は段 HT が空の 6 つ(N 6)のうち a12 だけが段 H の U で、残り 5 は N。
#: b5(空の欄 a9 を数えない 29 fact): a8 は桁が違い W1・a10 は前の年が空の欄だけで N。
HAND_D1 = dict(rows=32, facts=30, nil=1, outside=1,
               b3=((1, 14, 3, 4, 2, 6), (1, 11, 7, 4, 2, 5), (1, 15, 3, 4, 2, 5)),
               b5=((1, 11, 3, 5, 2, 7), (1, 8, 7, 5, 2, 6), (1, 12, 3, 5, 2, 6)),
               b3nn=((1, 13, 3, 4, 2, 6), (1, 10, 7, 4, 2, 5), (1, 14, 3, 4, 2, 5)),
               name_ht=(1, 18, 3, 0, 2, 6), ctx_ht=(1, 20, 0, 3, 0, 6), unit_ht=(1, 22, 0, 1, 0, 6),
               fall=6, fallc=(0, 1, 0, 0, 0, 5))


def acc_hand(acc):
    c = acc["C"]
    return dict(rows=acc["rows"], facts=acc["facts"], nil=acc["nil"], outside=acc["outside"],
                b3=tuple(cls_of(c["b3"][s]) for s in ("HT", "H", "F")), b5=tuple(cls_of(c["b5"][s]) for s in ("HT", "H", "F")),
                b3nn=tuple(cls_of(c["b3nn"][s]) for s in ("HT", "H", "F")),
                name_ht=cls_of(c["name"]["HT"]), ctx_ht=cls_of(c["ctx"]["HT"]), unit_ht=cls_of(c["unit"]["HT"]),
                fall=acc["fall"], fallc=cls_of(acc["fallc"]))


# ---- e2e 用の 5 本(今年の側)。1 本目は上の組・2〜5 本目は 1 つの置き場(見出しア・科目ア・td 1)だけの小さい組
#: (stem, 提出者のコード, 今年の fact の並び: (同じ要素の行の数, 違う要素の行の数))。3 本目は前の年の側に相手が居ない(除く)
MINI = {"S1ZZ0002": (u"E99002", 20, 0, 0), "S1ZZ0004": (u"E99004", 19, 1, 1), "S1ZZ0005": (u"E99005", 18, 2, 0)}      # (コード, 同じ要素の行, 違う要素の行, fact を持たない行)
CUR_STEMS = ["S1ZZ0001", "S1ZZ0002", "S1ZZ0003", "S1ZZ0004", "S1ZZ0005"]
#: 前の年の側の stem は、今年の側の番号の順(1・2・4・5)が昇順の逆になるようにする
PRV = {"E99001": "S1ZP0005", "E99002": "S1ZP0004", "E99004": "S1ZP0002", "E99005": "S1ZP0001"}
PRV_STEMS = ["S1ZP0005", "S1ZP0004", "S1ZP0002", "S1ZP0001"]
CODES = {"S1ZZ0001": u"E99001", "S1ZZ0003": u"E99003"}
CUR_END, PRV_END = "2026-03-31", "2025-03-31"
MINI_PRIOR = [("0a_ixbrl.htm", head(u"見出しア") + table([row(u"科目ア", fact("01"))]))]


def mini_cur(good, bad, empty=0):
    return [("0a_ixbrl.htm", head(u"見出しア") + table([row(u"科目ア", fact("01"))] * good + [row(u"科目ア", fact("99"))] * bad + [NO_FACT_ROW] * empty))]


def fname(code, end, no=1, suffix=u".xsd"):
    return u"XBRL/PublicDoc/jpcrp030000-asr-%03d_%s-000_%s_01_%s%s" % (no, code, end, end[:4] + u"-06-30", suffix)


def make_doc_zip(path, code, end, texts):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(fname(code, end), b"<schema/>")
        for n, t in texts:
            z.writestr(fname(code, end, suffix=u"_" + n), t.encode("utf-8"))
        # 読んではいけない file(読めば数が変わる): PublicDoc の外の ixbrl・PublicDoc の中の _ixbrl.htm でない htm・提出者の linkbase
        decoy = head(u"見出しア") + table([row(u"科目ア", fact("99"))] * 3)
        z.writestr(u"XBRL/AuditDoc/0000_audit_ixbrl.htm", decoy.encode("utf-8"))
        z.writestr(fname(code, end, suffix=u"_other.htm"), decoy.encode("utf-8"))
        z.writestr(fname(code, end, suffix=u"_lab.xml"), b"<x/>")


def make_dirs(d, cur_end=CUR_END, prv_end=PRV_END):
    docs, prior = os.path.join(d, "docs"), os.path.join(d, "prior")
    os.makedirs(docs)
    os.makedirs(prior)
    texts = {"S1ZZ0001": cur_files(), "S1ZZ0003": mini_cur(5, 0)}
    for stem, (code, good, bad, empty) in MINI.items():
        texts[stem] = mini_cur(good, bad, empty)
        CODES[stem] = code
    for stem in CUR_STEMS:
        make_doc_zip(os.path.join(docs, stem + ".zip"), CODES[stem], cur_end, texts[stem])
    for code, stem in sorted(PRV.items()):
        make_doc_zip(os.path.join(prior, stem + ".zip"), code, prv_end, prior_files() if code == "E99001" else MINI_PRIOR)
    return docs, prior


def kw_of(docs, prior):
    return dict(docs=docs, prior=prior, want_docs=5, want_pairs=4)


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XZ0-1", (70, 86)), ("XZ0-2", (None, 2.5)), ("XZ0-3", (6, 20)), ("XZ0-4", (1, 3.5)), ("XZ0-5", (15,)), ("XZ0-6", (-2,)), ("XZ0-7", (0,)), ("XZ0-8", (3, 20, 50))])
SEAL_BOUND_TEXT = {
    "XZ0-1": u"段 HT・束 3 の類 U は 70% 以上 86% 以下", "XZ0-2": u"段 HT・束 3 の類 W1 は 2.5% 以下", "XZ0-3": u"段 HT・束 3 の類 N と類 X の合計は 6% 以上 20% 以下",
    "XZ0-4": u"段 F・束 3 の類 U は段 HT より 1 ポイント以上高く、類 W1 は 3.5% 以下", "XZ0-5": u"段 H・束 3 の類 U は、段 HT より 15 ポイント以上低い",
    "XZ0-6": u"段 HT の束 5 の類 U の率は、束 3 の類 U の率より 2 ポイントを超えて低くはならない", "XZ0-7": u"`contextRef` だけの類 U の率は `name` だけの類 U の率以上",
    "XZ0-8": u"U の率が 95% 以上の書類は 3 本以下で、80% 以上の書類は 20 本以上 50 本以下"}


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL:
        out.append(u"封の commit・path が門と違う")
    for rel in (SCRIPT_REL, RECORD_REL, GATE_REL):
        if rel not in seal:
            out.append(u"封に path が無い: %s" % rel)
    if ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out.append(u"script・記録の path が封・門と違う")
    want_prior = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-prior-2026-11-02")
    if ms.PRIOR_DIR != want_prior or ms.PRIOR_DIR == ms.DOCS_DIR:
        out.append(u"前の年の側の置き場が封の字(edinet-prior-2026-11-02。今年の側の edinet/ でない)と違う")
    if ms.PAIRS_WANT != 63 or u"組の数が 63 でなければ script は止まる" not in seal or u"書類の数の予測: 63" not in seal:
        out.append(u"組の数 63 が封と違う")
    if ms.DOCS_WANT != 67 or u"今年の側 67 本" not in seal:
        out.append(u"今年の側の本数 67 が封と違う")
    if tuple(ms.CLASSES) != CLS or tuple(ms.STAGES) != (u"HT", u"H", u"F"):
        out.append(u"類・段の名が封と違う")
    for w in (u"- **X**", u"- **U**", u"- **A**", u"- **W1**", u"- **W2**", u"- **N**", u"**段 HT**", u"**段 H**", u"**段 F**", u"**束 3**", u"**束 5**",
              u"表 HT: (h, th, T, td)", u"表 H: (h, T, td)", u"**見出し h**", u"**表の番号 th**", u"**行の字 T**", u"**セルの番号 td**"):
        if w not in seal:
            out.append(u"封に字が無い: %s" % w)
    if tuple(ms.ATTRS3) != (u"name", u"contextRef", u"unitRef") or tuple(ms.ATTRS5) != (u"name", u"contextRef", u"unitRef", u"decimals", u"scale") \
            or u"**束 3**: (`name`, `contextRef`, `unitRef`)" not in seal or u"**束 5**: (`name`, `contextRef`, `unitRef`, `decimals`, `scale`)" not in seal:
        out.append(u"束 3・束 5 の属性が封と違う")
    if ms.NIL_ATTR != u"xsi:nil" or u"開きタグに `xsi:nil=\"true\"` が在る fact" not in seal or u"今年の側も前の年の側も、空の欄でない fact だけ" not in seal:
        out.append(u"空の欄の決めが封と違う")
    if u"段 HT の候補が 1 つ以上なら段 HT の候補。空なら段 H の候補" not in seal:
        out.append(u"段 F の決めが封と違う")
    if ms.U_DOC_HI_PCT != 95 or ms.U_DOC_LO_PCT != 80 or u"95% 以上の書類は 3 本以下で、80% 以上の書類は 20 本以上 50 本以下" not in seal:
        out.append(u"XZ0-8 の 95%・80% が封と違う")
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS):
        out.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [ln for ln in seal.splitlines() if re.match(r"^\| %s[ (]" % re.escape(k), ln)]
        if len(row_) != 1 or t not in row_[0]:
            out.append(u"封の予測の行の字が違う: %s" % k)
    flags = ((ms.FLAG_HT_U_OVER, 95, u"段 HT・束 3 の U が 95% を超えた"), (ms.FLAG_HT_N_OVER, 30, u"N が 30% を超えた"),
             (ms.FLAG_NAME_U_UNDER, 70, u"`name` だけの U が 70% 未満"), (ms.FLAG_OUTSIDE_OVER, 5, u"行の外の fact が全体の 5% を超えた"))
    for got, want, text in flags:
        if got != want or text not in seal:
            out.append(u"先に疑う旗の境が封と違う: %s" % text)
    if u"**docID・会社の名・EDINET コード・期末の日付・file の名・行の字・見出しの字・要素の名・文脈の名は書かない。**" not in seal:
        out.append(u"封の記録に書かないものの字が違う")
    if u"engine の指紋" not in seal or u"材料の並びの sha256" not in seal:
        out.append(u"封の記録の項目が違う")
    sec7 = seal.split(u"## §7", 1)[-1]
    want = (u"どのセルに fact を置くか", u"専用の道具が組んだ後の字", u"文脈は `contextRef` の字(名)で比べる", u"`sign`・`format`", u"前の年の XBRL が在る会社にしか使えない", u"63 組は無作為ではない", u"「XBRL を作れる」")
    want_script = (u"どのセルに fact を置くか", u"専用の道具が組んだ後の字", u"文脈は contextRef の字(名)で比べる", u"sign・format", u"前の年の XBRL が在る会社にしか使えない", u"63 組は無作為ではない", u"「XBRL を作れる」")
    if len([ln for ln in sec7.splitlines() if ln.startswith(u"- ")]) != 7:
        out.append(u"封 §7 の限界の行が 7 行でない")
    if len(ms.LIMITS) != 7 or any(p not in sec7 for p in want) or any(p not in u"".join(ms.LIMITS) for p in want_script):
        out.append(u"限界の 7 行が封 §7 と違う")
    return out


def seal_history_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "log", "--format=%H", "--", PREFIX + SEAL_REL], stdout=subprocess.PIPE, universal_newlines=True)
    hs = [x for x in rc.stdout.split() if x]
    if len(hs) != 1 or not hs[0].startswith(SEAL_COMMIT_SHORT):
        return [u"封の file の履歴が封 %s の 1 commit でない" % SEAL_COMMIT_SHORT]
    blob = subprocess.run(["git", "-C", root, "show", "%s:%s" % (hs[0], PREFIX + SEAL_REL)], stdout=subprocess.PIPE).stdout.decode("utf-8")
    if blob != seal_text():
        return [u"今の封が封の commit の blob と違う"]
    return []


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    u"""封 ⊏ script・この門(足した commit が封の後)。未 commit は赤。"""
    others = list(ORDER_FILES) if others is None else others
    return list(PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))


def engine_zero_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core"], stdout=subprocess.PIPE, universal_newlines=True)
    return [u"engine が封の後に変わっている: %s" % ln for ln in rc.stdout.splitlines() if ln.strip()]


# ======================================================================== 2. 鍵の部品(行・fact・th・td)
def read_problems(ms=None):
    ms = ms or MS
    out = []
    a = ms.parse_attrs(u'<ix:nonFraction name="n1" contextRef="c1" unitRef="u1" decimals="-3" xsi:nil="true"/>')
    if a != {"name": "n1", "contextRef": "c1", "unitRef": "u1", "decimals": "-3", "xsi:nil": "true"} or not ms.is_nil(a):
        out.append(u"fact の開きタグの読み取りが違う: %s" % a)
    if ms.is_nil({"xsi:nil": "false"}) or ms.is_nil({}) or not ms.is_nil({"xsi:nil": "true"}):
        out.append(u"空の欄の判定が違う(true だけ)")
    if ms.bundle3({"name": "n", "contextRef": "c", "unitRef": "u", "decimals": "1", "scale": "2"}) != ("n", "c", "u") \
            or ms.bundle5({"name": "n", "contextRef": "c", "unitRef": "u", "decimals": "1", "scale": "2"}) != ("n", "c", "u", "1", "2") or ms.bundle5({"name": "n"}) != ("n", None, None, None, None):
        out.append(u"束 3・束 5 の作りが違う(属性が無ければ None)")
    # 行・見出し・th・td・行の外
    t1 = (head(u"見出し　ア") + u"<p>%s</p>" % fact("99") + u"<p>%s</p>" % fact("99")
          + table([row(u"科目ア", fact("01")), NO_FACT_ROW, u"<tr><td>科目　イ</td><th>－</th><td>%s</td></tr>" % fact("02"), row(u"", fact("03")), row(u"科目エ", fact("06"), fact("07")), row(u"ＡＢ　Ｃ", fact("09"))])
          + EMPTY_TABLE + EMPTY_TABLE
          + table([row(u"科目ウ", fact("04"))])
          + head(u"見出しイ") + table([row(u"科目ア", fact("05"))]))
    rows, outside = ms.read_rows(t1)
    got = [(h, th, T, [(td, a["name"], a["contextRef"]) for td, a in facts]) for h, th, T, facts in rows]
    want = [(u"見出しア", 0, u"科目ア", [(2, EL["01"], CA)]), (u"見出しア", 0, u"見出し行", []), (u"見出しア", 0, u"科目イ", [(3, EL["02"], CA)]),
            (u"見出しア", 0, u"", [(2, EL["03"], CA)]), (u"見出しア", 0, u"科目エ", [(2, EL["06"], CA), (3, EL["07"], CA)]), (u"見出しア", 0, u"ABC", [(2, EL["09"], CA)]), (u"見出しア", 1, u"科目ウ", [(2, EL["04"], CA)]), (u"見出しイ", 0, u"科目ア", [(2, EL["05"], CA)])]
    if got != want or outside != 2:
        out.append(u"行・見出し h(正規化)・表の番号 th(見出しごと・行を持たない表は数えない)・セルの番号 td(td と th を数える)・行の外の fact が違う: %s %s" % (got, outside))
    rows0, o0 = ms.read_rows(table([row(u"科目ア", fact("01"))]) + head(u"見出しア") + table([row(u"科目イ", fact("02"))]))
    if [r[0] for r in rows0] != [None, u"見出しア"] or o0 != 0:
        out.append(u"見出しが無い行の h が None でない(行より前の最後の見出し)")
    rows1, _o = ms.read_rows(head(u" ") + table([row(u"科目ア", fact("01"))]))
    if rows1[0][0] != u"" or rows1[0][0] is None:
        out.append(u"見出しの字が正規化で空になる行の h が空の字でない(None と別)")
    # 行の中で始まる表(入れ子)は、その行の表の通し番号に数えない(行の始まりより前に始まる `<table` だけ)
    nested = u"<table><tr><td>科目ア<table><tr><td>科目ウ</td></tr><tr><td>科目イ</td></tr></table></td></tr></table>"
    rows_n, _o = ms.read_rows(nested)
    if [r[1] for r in rows_n] != [0, 1]:
        out.append(u"入れ子の表の行の th が違う(行の始まりより前の表だけ数える): %s" % [r[1] for r in rows_n])
    # file ごとに th を数え直す・file の昇順に並べる
    rr, oo = ms.texts_rows([("b_ixbrl.htm", head(u"見出しア") + table([row(u"科目イ", fact("02"))]) + table([row(u"科目ウ", fact("03"))]) + u"<p>%s</p>" % fact("99")),
                            ("a_ixbrl.htm", head(u"見出しア") + table([row(u"科目ア", fact("01"))]))])
    if [(r[1], r[2]) for r in rr] != [(0, u"科目ア"), (0, u"科目イ"), (1, u"科目ウ")] or oo != 1:
        out.append(u"th が file ごとに数え直されていない・file の昇順に並べていない・行の外の合計が違う: %s %s" % ([(r[1], r[2]) for r in rr], oo))
    # 行の切り方が file_rows と 1 対 1でなければ止まる
    real = ms.N.file_rows
    try:
        ms.N.file_rows = lambda text: real(text)[:-1]
        if not stops(ms, ms.read_rows, table([row(u"科目ア", fact("01")), row(u"科目イ", fact("02"))])):
            out.append(u"行の切り方が file_rows と 1 対 1 でないのに止まらない")
    finally:
        ms.N.file_rows = real
    return out


# ======================================================================== 3. 表・段・類
def tables_problems(ms=None):
    ms = ms or MS
    out = []
    rows, _o = ms.texts_rows(prior_files())
    tabs = ms.build_tables(rows)
    b = lambda k, c=CA, u=UJ, d=u"-6", s=u"6": (EL[k], c, u, d, s)               # noqa: E731
    b3 = lambda k, c=CA, u=UJ: (EL[k], c, u)                                      # noqa: E731
    ht3, h3, ht5, h5 = tabs["HT3"], tabs["H3"], tabs["HT5"], tabs["H5"]
    want_ht3 = {(u"見出しア", 0, u"科目ア", 2): {b3("01")}, (u"見出しア", 0, u"科目ア", 3): {b3("01", CB)}, (u"見出しア", 1, u"科目ア", 2): {b3("01x")},
                (u"見出しア", 0, u"科目ウ", 2): {b3("03"), b3("03b")}, (u"見出しア", 0, u"科目ク", 2): {b3("11")}, (u"見出しア", 0, u"科目ケ", 2): {b3("12")},
                (u"見出しア", 1, u"科目ス", 2): {b3("13")}, (u"見出しイ", 0, u"科目ア", 2): {b3("01i")}, (None, 0, u"科目ア", 2): {b3("01n")}, (u"", 0, u"科目ア", 2): {b3("01e")},
                (u"見出しア", 0, u"科目エ", 2): {b3("04")}}
    for k, v in want_ht3.items():
        if ht3.get(k) != v:
            out.append(u"表 HT の鍵 %s の束 3 が違う: %s" % (k, ht3.get(k)))
    if any(k[2] == u"" for k in ht3) or any(k[1] == u"" for k in h3):
        out.append(u"行の字が空の行を表に入れている")
    if ht3[(u"見出しア", 0, u"科目ア", 2)] != {b3("01")} or h3[(u"見出しア", u"科目ア", 2)] != {b3("01"), b3("01x")}:
        out.append(u"表 H が表の番号 th を落として表 1 の fact を足した集まりになっていない")
    if h3.get((u"見出しア", u"科目ケ", 2)) != {b3("12")} or ht5.get((u"見出しア", 0, u"科目ケ", 2)) is not None or h5.get((u"見出しア", u"科目ケ", 2)) is not None:
        out.append(u"空の欄だけの行が束 3 の表にだけ入る形になっていない")
    if ht5.get((u"見出しア", 0, u"科目ク", 2)) != {b("11")} or ht3[(u"見出しア", 0, u"科目ク", 2)] != {b3("11")}:
        out.append(u"空の欄(桁 0)が束 5 の表に混ざっている(束 3 の表は束 3 の鍵だけ)")
    if (None, u"科目ア", 2) not in h3 or (u"", u"科目ア", 2) not in h3 or h3[(None, u"科目ア", 2)] != {b3("01n")}:
        out.append(u"見出しが無い h(None)と空の字の h が別になっていない")
    # 段
    if ms.stage_ht(ht3, u"見出しア", 0, u"科目ア", 2) != {b3("01")} or ms.stage_ht(ht3, u"見出しア", 5, u"科目ア", 2) != set() or ms.stage_ht(ht3, u"見出しウ", 0, u"科目ア", 2) != set():
        out.append(u"段 HT の候補が違う(鍵の 4 つの部品の全部で引く)")
    if ms.stage_ht(ht3, u"見出しア", 0, u"科目ア", 3) != {b3("01", CB)} or ms.stage_ht(ht3, u"見出しア", 0, u"科目ア", 4) != set() or ms.stage_ht(ht3, u"見出しア", 0, u"科目イ", 3) != set():
        out.append(u"段 HT が行の字 T・セルの番号 td で引いていない")
    if ms.stage_h(h3, u"見出しア", u"科目ア", 2) != {b3("01"), b3("01x")} or ms.stage_h(h3, u"見出しウ", u"科目ア", 2) != set():
        out.append(u"段 H の候補が違う(h・T・td で引く)")
    if ms.stage_f({1}, {1, 2}) != {1} or ms.stage_f(set(), {1, 2}) != {1, 2} or ms.stage_f(set(), set()) != set():
        out.append(u"段 F が段 HT が空のときだけ段 H へ落ちる形になっていない")
    ret = ms.stage_f({1}, {1, 2})
    if ret is {1}:
        out.append(u"段 F が元の集まりを返している")
    # 類
    for value, cands, want in ((1, set(), "N"), (1, {1}, "U"), (1, {1, 2}, "A"), (1, {2}, "W1"), (1, {2, 3}, "W2"), (None, set(), "N"), (None, {(None, 1)}, "W1")):
        if ms.classify6(value, cands) != want:
            out.append(u"類が違う: %s %s -> %s" % (value, cands, ms.classify6(value, cands)))
    if ms.project({(1, 2, 3), (1, 5, 3)}, 0) != {1} or ms.project({(1, 2, 3), (1, 5, 3)}, 1) != {2, 5}:
        out.append(u"属性ごとの候補(束 3 の候補の射影)が違う")
    return out


# ======================================================================== 4. 組 1 つの手の数
def doc_problems(ms=None):
    ms = ms or MS
    got = acc_hand(ms.count_pair(cur_files(), prior_files()))
    out = []
    for k, w in HAND_D1.items():
        if got[k] != w:
            out.append(u"作り物の組の数 %s が手で数えた値と違う: %s != %s" % (k, got[k], w))
    # 前の年の側と今年の側を入れ替えると別の数になる(前の年の側として今年の書類を読んでいない)
    swapped = acc_hand(ms.count_pair(prior_files(), cur_files()))
    if swapped["b3"] == got["b3"]:
        out.append(u"今年の側と前の年の側を入れ替えても数が変わらない(作り物が見分けていない)")
    # 前の年の側へ今年の書類そのものを渡すと全部 U(旗の根拠)
    same = ms.count_pair(cur_files(), cur_files())
    ht = same["C"]["b3"]["HT"]
    if ht["W1"] or ht["W2"] or ht["N"] or ht["U"] + ht["A"] != same["facts"] - ht["X"]:
        out.append(u"同じ書類を両側に渡したとき、鍵が作れる fact が全部 U か A(自分の束を含む)になっていない")
    return out


def small_problems(ms=None):
    u"""束 5 の桁(decimals だけ・scale だけが違う fact)と、行の字が空の fact の空の欄の数え方(束 3 では X に入り・束 5 と束 3(空の欄でない fact)では入らない)。"""
    ms = ms or MS
    out = []
    prior = [("0a_ixbrl.htm", head(u"見出しア") + table([row(u"科目ア", fact("01"))]))]
    cur = [("0a_ixbrl.htm", head(u"見出しア") + table([row(u"科目ア", fact("01", scale=u"3")), row(u"科目ア", fact("01", dec=u"-3")), row(u"科目ア", fact("01"))]))]
    a = ms.count_pair(cur, prior)
    if cls_of(a["C"]["b3"]["HT"]) != (0, 3, 0, 0, 0, 0) or cls_of(a["C"]["b5"]["HT"]) != (0, 1, 0, 2, 0, 0):
        out.append(u"束 5 が桁(decimals)・scale の片方だけの違いを W1 にしていない: %s" % (cls_of(a["C"]["b5"]["HT"]),))
    cur2 = [("0a_ixbrl.htm", head(u"見出しア") + table([row(u"", fact("07", nil=True)), row(u"", fact("07")), row(u"科目ア", fact("01"))]))]
    a2 = ms.count_pair(cur2, prior)
    got = (a2["facts"], a2["nil"], cls_of(a2["C"]["b3"]["HT"]), cls_of(a2["C"]["b5"]["HT"]), cls_of(a2["C"]["b3nn"]["HT"]), cls_of(a2["C"]["name"]["HT"]))
    want = (3, 1, (2, 1, 0, 0, 0, 0), (1, 1, 0, 0, 0, 0), (1, 1, 0, 0, 0, 0), (2, 1, 0, 0, 0, 0))
    if got != want:
        out.append(u"行の字が空の fact の空の欄の数え方が違う: %s != %s" % (got, want))
    return out


# ======================================================================== 5. 記録・e2e
def build_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    with Temp() as d:
        docs, prior = make_dirs(d)
        rec, secret = ms.build_record(docs, prior, 5, 4)
        mat = rec[u"材料"]
        if (mat[u"今年の側の書類の本数"], mat[u"組の数"], mat[u"除いた今年の書類の数"]) != (5, 4, 1):
            out.append(u"材料の数が違う: %s" % dict(mat))
        if mat[u"今年の側の書類の file 名の並びの sha256"] != hashlib.sha256(u"\n".join(CUR_STEMS).encode("utf-8")).hexdigest():
            out.append(u"今年の側の並びの sha256 が違う")
        if mat[u"前の年の側の組の相手の file 名の並びの sha256"] != hashlib.sha256(u"\n".join(PRV_STEMS).encode("utf-8")).hexdigest():
            out.append(u"前の年の側の組の相手の並びの sha256 が違う(今年の側の番号の順)")
        fp = ms.VD.engine_fingerprint()
        keys = ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files")
        if list(rec[u"engine の指紋"].keys()) != list(keys) or any(not rec[u"engine の指紋"][k] for k in keys) or any(rec[u"engine の指紋"][k] != fp[k] for k in keys):
            out.append(u"記録の engine の指紋が engine の指紋でない(か空)")
        if rec[u"この script の sha256"] != sha_of(SCRIPT_REL):
            out.append(u"記録の script の sha256 が script の file の sha256 でない(か空)")
        if rec[u"限界"] != list(ms.LIMITS) or len(rec[u"限界"]) != 7:
            out.append(u"記録の限界が 7 行でない")
        docs_rec = rec[u"書類"]
        if [r[u"番号"] for r in docs_rec] != [1, 2, 4, 5]:
            out.append(u"書類の番号が違う(除いた書類の番号は飛ぶ): %s" % [r[u"番号"] for r in docs_rec])
        d1 = docs_rec[0]
        cells = d1[u"束と段ごとの類別"]
        if (d1[u"行の数"], d1[u"行の中の数の fact の数"], d1[u"空の欄の fact の数"], d1[u"行の外の fact の数"]) != (32, 30, 1, 1) \
                or tuple(cells[LAB["b3"]]["HT"].values()) != HAND_D1["b3"][0] or tuple(cells[LAB["b5"]]["F"].values()) != HAND_D1["b5"][2] \
                or d1[u"段 F で段 H へ落ちた fact の数"] != 6 or tuple(d1[u"段 F で段 H へ落ちた fact の類別(束 3)"].values()) != HAND_D1["fallc"] or d1[u"段 HT・束 3 の U の率(%)"] != 46.7:
            out.append(u"記録の書類 1 が手で数えた値と違う: %s" % dict(d1))
        if [r[u"段 HT・束 3 の U の率(%)"] for r in docs_rec] != [46.7, 100.0, 95.0, 90.0]:
            out.append(u"書類ごとの U の率が違う: %s" % [r[u"段 HT・束 3 の U の率(%)"] for r in docs_rec])
        agg = rec[u"集計"]
        if (agg[u"行の数"], agg[u"行の中の数の fact の数"], agg[u"空の欄の fact の数"], agg[u"空の欄でない fact の数"], agg[u"行の外の fact の数"], agg[u"fact が 1 つ以上在る書類の数"]) != (93, 90, 1, 89, 1, 4):
            out.append(u"集計の数が違う: %s" % dict(agg))
        c = agg[u"束と段ごとの類別"]
        for key, stage, want in (("b3", "HT", (1, 71, 3, 7, 2, 6)), ("b3", "H", (1, 68, 7, 7, 2, 5)), ("b3", "F", (1, 72, 3, 7, 2, 5)), ("b5", "HT", (1, 68, 3, 8, 2, 7)),
                                 ("b3nn", "HT", (1, 70, 3, 7, 2, 6)), ("name", "HT", (1, 75, 3, 3, 2, 6)), ("ctx", "HT", (1, 80, 0, 3, 0, 6)), ("unit", "HT", (1, 82, 0, 1, 0, 6))):
            got = tuple(c[LAB[key]][stage].values())
            if got != want:
                out.append(u"集計の束 %s・段 %s が手で数えた値と違う: %s" % (key, stage, got))
        if agg[u"段 F で段 H へ落ちた fact の数"] != 6:
            out.append(u"集計の落ちた fact の数が違う")
        pv = [v for k, v in rec.items() if k.startswith(u"予測の判定に要る数")][0]
        def look(prefix):
            hit = [v for k, v in pv.items() if k.startswith(prefix)]
            return hit
        want_pct = {u"XZ0-1 ": 78.9, u"XZ0-2 段 HT・束 3 の類 W1 / 行": 7.8, u"XZ0-2 段 HT・束 3 の類 W1 / (U": 9.0, u"XZ0-3 ": 7.8, u"XZ0-4 段 F・束 3 の類 W1 / 行": 7.8, u"XZ0-4 段 F・束 3 の類 W1 / (U": 8.9}
        for prefix, w in want_pct.items():
            hit = look(prefix)
            if len(hit) != 1 or hit[0][u"%"] != w:
                out.append(u"判定の数 %s が手で数えた値 %s と違う: %s" % (prefix, w, hit))
        x4 = look(u"XZ0-4 段 F・束 3 の類 U")[0]
        if (x4[u"段 F の U の fact"], x4[u"段 HT の U の fact"], x4[u"分母"], x4[u"段 F の U の %"], x4[u"段 HT の U の %"], x4[u"段 F から段 HT を引いた差(ポイント)"]) != (72, 71, 90, 80.0, 78.9, 1.1):
            out.append(u"XZ0-4 の数が違う: %s" % dict(x4))
        x5 = look(u"XZ0-5")[0]
        if (x5[u"段 H の U の fact"], x5[u"段 HT の U の fact"], x5[u"段 H の U の %"], x5[u"段 HT から段 H を引いた差(ポイント)"]) != (68, 71, 75.6, 3.3):
            out.append(u"XZ0-5 の数が違う: %s" % dict(x5))
        x6 = look(u"XZ0-6")[0]
        if (x6[u"束 5 の U の fact"], x6[u"束 3 の U の fact(空の欄でない fact だけ)"], x6[u"分母(空の欄でない fact)"], x6[u"束 5 の U の %"], x6[u"束 3 の U の %"], x6[u"束 5 から束 3 を引いた差(ポイント)"]) \
                != (68, 70, 89, 76.4, 78.7, -2.2):
            out.append(u"XZ0-6 の数が違う(分母は空の欄でない fact・束 3 も同じ分母): %s" % dict(x6))
        x7 = look(u"XZ0-7")[0]
        if (x7[u"contextRef の U の fact"], x7[u"name の U の fact"], x7[u"contextRef の U の %"], x7[u"name の U の %"], x7[u"unitRef の U の fact"], x7[u"unitRef の U の %"]) != (80, 75, 88.9, 83.3, 82, 91.1):
            out.append(u"XZ0-7 の数が違う: %s" % dict(x7))
        x8 = look(u"XZ0-8")[0]
        if tuple(x8.values()) != (2, 3, 4, 4):
            out.append(u"XZ0-8 の数が違う(95.0% は含む・書類は fact を持つ組だけ): %s" % dict(x8))
        fl = list(rec[u"先に自分の欠陥を疑う旗(止めない。当たり外れではない)"].values())
        if len(fl) != 4 or any(f[u"旗"] for f in fl) or [f[u"分母"] for f in fl] != [90, 90, 90, 91] or [f[u"fact"] for f in fl] != [71, 6, 75, 1]:
            out.append(u"旗の数が違う: %s" % [dict(f) for f in fl])
        text = ms.record_text(rec, secret)
        for leak in CUR_STEMS + PRV_STEMS + [u"E99", u"S1ZZ", u"S1ZP", u"Item", u"ctxA", u"unitJ", u"科目", u"見出しア", u"見出しイ", u"見出しウ", u"2026-03", u"2025-03", u"_ixbrl", u"fk:"]:
            if leak in text:
                out.append(u"記録に材料の字が在る: %s" % leak)
        if stops(ms, ms.build_record, docs, prior, 5, 3) is False:
            out.append(u"組の数が違うのに止まらない")
    return out


def e2e_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    with Temp() as d:
        docs, prior = make_dirs(d)
        kw = kw_of(docs, prior)
        rec_path = os.path.join(d, "rec", "r.json")
        lines = []
        before = sha_or_none(RECORD_REL)
        ms.run(root=d, out=rec_path, say=lines.append, **kw)
        if not os.path.isfile(rec_path) or lines != [u"-> r.json(組 4)"] or sha_or_none(RECORD_REL) != before:
            out.append(u"本番が記録を書かない・本物の記録を触った: %s" % lines)
        if not stops(ms, ms.run, root=d, out=rec_path, say=lambda *a: None, **kw):
            out.append(u"記録が既に在るのに run が止まらない")
        ms.check(root=d, rec_path=rec_path, say=lambda *a: None, **kw)
        text = io.open(rec_path, encoding="utf-8").read()
        bad = text.replace(u'"行の中の数の fact の数": 30', u'"行の中の数の fact の数": 31', 1)
        bp = os.path.join(d, "bad.json")
        with io.open(bp, "w", encoding="utf-8") as fh:
            fh.write(bad)
        if bad == text or not stops(ms, ms.check, rec_path=bp, say=lambda *a: None, **kw):
            out.append(u"数を変えた記録で --check が止まらない")
        if not stops(ms, ms.check, rec_path=os.path.join(d, "none.json"), say=lambda *a: None, **kw):
            out.append(u"記録が無いのに --check が止まらない")
        # 前の年の側の書類を替えると --check が止まる
        make_doc_zip(os.path.join(prior, "S1ZP0005.zip"), "E99001", PRV_END, cur_files())
        if not stops(ms, ms.check, rec_path=rec_path, say=lambda *a: None, **kw):
            out.append(u"前の年の側の書類を変えても --check が止まらない")
    return out


def mini_record(ms, cur_texts, prior_texts):
    with Temp() as d:
        docs, prior = os.path.join(d, "docs"), os.path.join(d, "prior")
        os.makedirs(docs)
        os.makedirs(prior)
        make_doc_zip(os.path.join(docs, "S1ZZ0001.zip"), "E99001", CUR_END, cur_texts)
        make_doc_zip(os.path.join(prior, "S1ZP0001.zip"), "E99001", PRV_END, prior_texts)
        rec, _s = ms.build_record(docs, prior, 1, 1)
    return [f[u"旗"] for f in rec[u"先に自分の欠陥を疑う旗(止めない。当たり外れではない)"].values()]


def flag_cases(n_u, n_w1, n_n, n_out):
    rows = [row(u"科目ア", fact("01"))] * n_u + [row(u"科目ア", fact("99"))] * n_w1 + [row(u"科目ネ", fact("01"))] * n_n
    return [("0a_ixbrl.htm", head(u"見出しア") + u"".join(u"<p>%s</p>" % fact("99") for _ in range(n_out)) + table(rows))]


#: (今年の U 行・W1 行・N 行・行の外の fact) → (旗 1: U が 95% を超えた, 旗 2: N が 30% を超えた, 旗 3: name の U が 70% 未満, 旗 4: 行の外が全体の 5% を超えた)。境(ちょうど)は含まない。
FLAG_CASES = (((20, 0, 0, 0), (True, False, False, False)), ((191, 9, 0, 0), (True, False, False, False)), ((19, 1, 0, 0), (False, False, False, False)), ((14, 0, 6, 0), (False, False, False, False)),
              ((13, 0, 7, 0), (False, True, True, False)), ((18, 1, 0, 1), (False, False, False, False)), ((18, 1, 0, 2), (False, False, False, True)),
              ((0, 0, 20, 0), (False, True, True, False)))


def flags_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    for args, want in FLAG_CASES:
        got = tuple(mini_record(ms, flag_cases(*args), MINI_PRIOR))
        if got != want:
            out.append(u"旗が違う %s: %s != %s" % (args, got, want))
    return out


def clean_problems(ms=None):
    ms = ms or MS
    out = []
    secret = (set([u"科目ア"]), set([u"Item01"]), ["S1ZZ0001", "S1ZP0001"], set(["E99001"]), set([u"見出しア"]), set())
    for what, bad in ((u"docID の形", od([(u"x", u"S1ZZ9999")])), (u"EDINET コードの形", od([(u"x", u"E99991")])), (u"日付の形", od([(u"x", u"2026-03-31")])),
                      (u"禁止の欄", od([(u"docid", 1)])), (u"禁止の欄(名)", od([(u"name", 1)])), (u"今年の側の docID", od([(u"x", u"a S1ZZ0001 b")])),
                      (u"前の年の側の docID", od([(u"x", u"a S1ZP0001 b")])), (u"コード", od([(u"x", u"a E99001 b")])), (u"要素の名", od([(u"x", u"a Item01 b")])),
                      (u"行の字", od([(u"x", u"科目ア")])), (u"見出しの字", od([(u"x", u"見出しア")]))):
        if not stops(ms, ms.record_text, bad, secret):
            out.append(u"記録の検査が止めない: %s" % what)
    if stops(ms, ms.record_text, od([(u"a", 1), (u"seal", ms.SEAL_REL)]), secret):
        out.append(u"封の path の中の日付で止まる(封の path は書いてよい)")
    with Temp() as d:
        p = os.path.join(d, "r.json")
        good = od([(u"x", 1)])
        ms.write_record(p, good)
        if not stops(ms, ms.write_record, p, good):
            out.append(u"記録が既に在るのに書き直せる")
        q = os.path.join(d, "q.json")
        orig = ms.write_exclusive
        ms.write_exclusive = lambda path, data: orig(path, data + b" 2026-03-31")
        try:
            stopped = stops(ms, ms.write_record, q, good)
        finally:
            ms.write_exclusive = orig
        if not stopped or os.path.exists(q):
            out.append(u"書いた後の検査が止めない(か file を消さない)")
        v = os.path.join(d, "v.json")
        ms.write_exclusive = lambda path, data: orig(path, b"{}")
        try:
            stopped = stops(ms, ms.write_record, v, od([(u"x", u"2026-03-31")]))
        finally:
            ms.write_exclusive = orig
        if not stopped:
            out.append(u"書く前の検査が止めない(書いた後の検査だけで止まっている)")
    return out


def secret_problems(ms=None):
    u"""本番の ``build_record`` が作る secret の配線と、``check()`` が secret を ``check_clean`` に渡していること。作り物の置き場だけ。"""
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    with Temp() as d:
        docs, prior = make_dirs(d)
        kw = kw_of(docs, prior)
        rec, secret = ms.build_record(docs, prior, 5, 4)
        labels, elems, ids, ecodes, heads, inds = secret
        if sorted(ids) != sorted(CUR_STEMS + PRV_STEMS):
            out.append(u"secret の docID が今年の側と前の年の側の stem でない: %s" % (list(ids),))
        if not set([u"E99001", u"E99002", u"E99004", u"E99005"]) <= set(ecodes):
            out.append(u"secret の EDINET コードに組の提出者のコードが無い: %s" % (sorted(ecodes),))
        if not set([u"科目ア", u"科目イ", u"科目ウ", u"科目エ", u"科目オ", u"科目ク"]) <= set(labels) or not set([u"Item01", u"Item02", u"Item13", u"Item07", u"ctxA", u"ctxB", u"unitJ", u"unitS"]) <= set(elems):
            out.append(u"secret の行の字・要素・文脈・単位の字が作り物の行と違う: %s" % sorted(elems))
        if heads != set([u"見出しア", u"見出しイ", u"見出しウ"]):
            out.append(u"secret の見出しの字が違う(空の字は入れない): %s" % sorted(heads))
        real_build = ms.build_record
        for ln, (what, leak) in enumerate(((u"前の年の側の docID", u"a S1ZP0004 b"), (u"組のコード", u"a E99004 b"), (u"見出しの字(全部一致)", u"見出しウ"), (u"要素の名", u"a Item02 b"),
                                           (u"文脈の字", u"a ctxB b"), (u"単位の字", u"a unitS b"), (u"行の字", u"科目ク"))):
            leaky = od(rec)
            leaky[u"仕込み"] = leak
            lp = os.path.join(d, "leak_%d.json" % ln)
            with io.open(lp, "w", encoding="utf-8") as fh:
                fh.write(ms.dumps(leaky))
            ms.build_record = lambda *a, **k: (leaky, secret)
            try:
                stopped = stops(ms, ms.check, rec_path=lp, say=lambda *a: None, **kw)
            finally:
                ms.build_record = real_build
            if not stopped:
                out.append(u"check() が secret(%s)の仕込みで止まらない" % what)
    return out


# ======================================================================== 6. 配線
STDLIB_OK = ("__future__", "argparse", "bisect", "collections", "hashlib", "importlib", "io", "json", "os", "re", "sys", "zipfile", "adapters")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "subprocess")
ENGINE_CALLED = ("_row_label", "_TR_RE")
WALL_CALLED = ("Stop", "sha256_bytes", "sha256_file", "dumps", "pct1", "norm_label", "order_sha256", "HEX_RE")
NARROW_CALLED = ("file_rows", "doc_texts", "check_clean")
PRIOR_CALLED = ("make_pairs",)
NOT_COPIED = ("select_docs", "make_pairs", "code_and_end", "prior_index", "norm_label", "file_rows", "kind_of", "doc_texts", "order_sha256", "classify5")
CAND_FUNCS = ("stage_ht", "stage_h", "stage_f")
CUR_FACT_NAMES = ("a", "b3", "b5", "attrs", "nil", "value", "E")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
PRIOR_NAME = "_xz0_prior_year_draft_2026_11_22"
HARNESS_WORDS = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(")


def import_problems(src=None):
    u"""script の import は標準ライブラリと engine の 2 module と importlib だけ。前の便の関数は ``Y.``・``N.``・``W.`` から呼び写さない。今年の fact の属性は候補を作る関数に渡さない。提出者の file を読まない。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out = []
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            names = [(n.module or u"")]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("__import__", "eval", "exec"):
            out.append(u"動的な import・eval・exec の呼び出し")
        for nm in names:
            top = nm.split(".")[0]
            if top in NETWORK_MODULES:
                out.append(u"許さない module を import している: %s" % nm)
            elif top not in STDLIB_OK:
                out.append(u"許す一覧に無い module: %s" % nm)
    eng = sorted(a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "adapters.xbrl" for a in n.names)
    if eng != ["instance", "verify_document"]:
        out.append(u"engine から読む module が instance・verify_document の 2 つだけでない: %s" % eng)
    attrs = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]
    if ("os", "environ") in attrs or ("os", "getenv") in attrs:
        out.append(u"環境変数を読んでいる")
    for table_, owner, label in ((ENGINE_CALLED, "I", u"engine"), (WALL_CALLED, "W", u"便 XG0"), (NARROW_CALLED, "N", u"便 XG1"), (PRIOR_CALLED, "Y", u"便 XY0")):
        for fn in table_:
            if (owner, fn) not in attrs:
                out.append(u"%s の %s を %s から呼んでいない" % (label, fn, owner))
    funcs = dict((n.name, n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    for fn in NOT_COPIED:
        if fn in funcs:
            out.append(u"前の便の %s を script が自分で定義している(写している)" % fn)
    for fn in CAND_FUNCS:
        f = funcs.get(fn)
        if f is None:
            out.append(u"候補を作る関数 %s が無い" % fn)
            continue
        argn = [a.arg for a in f.args.args]
        used = set(x.id for x in ast.walk(f) if isinstance(x, ast.Name))
        if set(argn) & set(CUR_FACT_NAMES) or used & set(CUR_FACT_NAMES):
            out.append(u"候補を作る関数 %s に今年の fact の属性が渡っている・使われている" % fn)
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in CAND_FUNCS:
            bad = set(x.id for arg in n.args for x in ast.walk(arg) if isinstance(x, ast.Name)) & set(CUR_FACT_NAMES)
            if bad:
                out.append(u"候補を作る関数 %s の呼び出しに今年の fact の属性 %s が渡っている" % (n.func.id, sorted(bad)))
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            doc.add(id(n.body[0].value))
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            v = n.value
            if u".env" in v or u"dotenv" in v or u"API_KEY" in v:
                out.append(u"鍵・.env の字が在る")
            if any(s in v for s in (u"_lab.xml", u"_pre.xml", u"_cal.xml", u"_def.xml", u".xsd")):
                out.append(u"提出者の file の名の字が在る: %s" % v)
            if any(s in v for s in HARNESS_WORDS):
                out.append(u"注入の仕掛けの規準の字が在る: %s" % v)
    if PRIOR_NAME not in consts:
        out.append(u"前の便の script を読む名が一意の名(%s)でない" % PRIOR_NAME)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and (n.func.value.id, n.func.attr) == ("N", "doc_texts")]
    if len(calls) != 2:
        out.append(u"書類の字を N.doc_texts で読む呼び出しが 2 つ(今年の側・前の年の側)でない: %d" % len(calls))
    for n in funcs:
        if any(w.rstrip(u"(").split(u".")[-1] == n for w in HARNESS_WORDS):
            out.append(u"関数の名が注入の仕掛けの規準の字に当たる: %s" % n)
    return out


def reserved_problems(rel=GATE_REL, base=ROOT):
    out = []
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for n, line in enumerate(lines, 1):
        if any(line.startswith(p) for p in RESERVED_PREFIXES):
            out.append(u"%s:%d" % (rel, n))
    return out


# ======================================================================== 変異
#: (名前, 置き換え前(script の中でちょうど 1 回)・置き換え後・赤になるべき検査の名前)。**約束の側から作った。予測は「その検査が赤になる」。**
MUTANTS = (
    # ---- 類
    (u"M1 W1 を U に数える", u'return "W1" if len(cands) == 1 else "W2"', u'return "U" if len(cands) == 1 else "W2"', ("tables", "doc", "build")),
    (u"M2 W1 と W2 を入れ替える", u'return "W1" if len(cands) == 1 else "W2"', u'return "W2" if len(cands) == 1 else "W1"', ("tables", "doc", "build")),
    (u"M3 U の条件を候補 2 つ以下にする", u'return "U" if len(cands) == 1 else "A"', u'return "U" if len(cands) <= 2 else "A"', ("tables", "doc", "build")),
    (u"M4 候補が無い fact を N に数えない", u'    if not cands:\n        return "N"', u'    if not cands:\n        return "W2"', ("tables", "doc", "build")),
    (u"M5 候補が 1 つの値を含むかを見ない", u"    if value not in cands:\n        return", u"    if value in cands and False:\n        return", ("tables", "doc", "build")),
    (u"M6 X を N に数える(鍵が作れない fact)", u'                        acc["C"][b][s]["X"] += 1', u'                        acc["C"][b][s]["N"] += 1', ("doc", "build")),
    (u"M7 X を数えない(分母から外す)", u'                        acc["C"][b][s]["X"] += 1', u"                        pass", ("doc", "build")),
    # ---- 鍵の部品(書く側と引く側を別々に)
    (u"M8 表 HT の鍵(書く側)から h を外す", u'tabs["HT3"].setdefault((h, th, T, td), set()).add(b3)', u'tabs["HT3"].setdefault((None, th, T, td), set()).add(b3)', ("tables", "doc", "build")),
    (u"M9 段 HT の鍵(引く側)から h を外す", u"return set(tab.get((h, th, T, td), ()))", u"return set(tab.get((None, th, T, td), ()))", ("tables", "doc", "build")),
    (u"M10 表 HT の鍵(書く側)から th を外す", u'tabs["HT3"].setdefault((h, th, T, td), set()).add(b3)', u'tabs["HT3"].setdefault((h, 0, T, td), set()).add(b3)', ("tables", "doc", "build")),
    (u"M11 段 HT の鍵(引く側)から th を外す", u"return set(tab.get((h, th, T, td), ()))", u"return set(tab.get((h, 0, T, td), ()))", ("tables", "doc", "build")),
    (u"M12 表 HT の鍵(書く側)から T を外す", u'tabs["HT3"].setdefault((h, th, T, td), set()).add(b3)', u'tabs["HT3"].setdefault((h, th, u"", td), set()).add(b3)', ("tables", "doc", "build")),
    (u"M13 段 HT の鍵(引く側)から T を外す", u"return set(tab.get((h, th, T, td), ()))", u'return set(tab.get((h, th, u"", td), ()))', ("tables", "doc", "build")),
    (u"M14 表 HT の鍵(書く側)から td を外す", u'tabs["HT3"].setdefault((h, th, T, td), set()).add(b3)', u'tabs["HT3"].setdefault((h, th, T, 0), set()).add(b3)', ("tables", "doc", "build")),
    (u"M15 段 HT の鍵(引く側)から td を外す", u"return set(tab.get((h, th, T, td), ()))", u"return set(tab.get((h, th, T, 0), ()))", ("tables", "doc", "build")),
    (u"M16 表 H の鍵(書く側)から h を外す", u'tabs["H3"].setdefault((h, T, td), set()).add(b3)', u'tabs["H3"].setdefault((None, T, td), set()).add(b3)', ("tables", "doc", "build")),
    (u"M17 段 H の鍵(引く側)から td を外す", u"return set(tab.get((h, T, td), ()))", u"return set(tab.get((h, T, 0), ()))", ("tables", "doc", "build")),
    (u"M18 表 H の鍵(書く側)に th を入れる", u'tabs["H3"].setdefault((h, T, td), set()).add(b3)', u'tabs["H3"].setdefault((h, T, td, th), set()).add(b3)', ("tables", "doc", "build")),
    # ---- 鍵の部品の読み取り
    (u"M19 th を表の通し番号そのままにする(行を持たない表も数える)", u"        th = ranks[serial]", u"        th = serial", ("read", "doc", "build")),
    (u"M20 th の番号を見出しごとに振り直さない", u"        ranks = seen.setdefault(h, {})", u"        ranks = seen.setdefault(0, {})", ("read", "doc", "build")),
    (u"M21 th の番号を file をまたいで振る", u"    seen = {}\n    out = []\n    inside = 0", u'    seen = globals().setdefault("_SEEN_ACROSS", {})\n    out = []\n    inside = 0', ("read", "doc", "build")),
    (u"M22 見出し h に norm_label を掛けない", u"        h = norm_label(head) if head is not None else None", u"        h = head", ("read", "doc", "build")),
    (u"M23 見出しが無い行の h を空の字にする", u"        h = norm_label(head) if head is not None else None", u'        h = norm_label(head) if head is not None else u""', ("read", "doc", "build")),
    (u"M24 行の字 T に norm_label を掛けない", u'        T = norm_label(label) if label else u""', u'        T = label if label else u""', ("read", "doc", "build")),
    (u"M25 td を td だけで数える(th を数えない)", u'CELL_RE = re.compile(r"<t[dh]\\b", re.I)', u'CELL_RE = re.compile(r"<td\\b", re.I)', ("read", "doc", "build")),
    (u"M26 td を行の中の全部の数にする(fact の開きタグより前に限らない)", u"            td = len(CELL_RE.findall(rowtext[:fm.start()]))", u"            td = len(CELL_RE.findall(rowtext))", ("read", "doc", "build")),
    (u"M27 表の通し番号を行の終わりより前で数える", u"        serial = bisect.bisect_left(starts, m.start())", u"        serial = bisect.bisect_left(starts, m.end())", ("read",)),
    (u"M28 行の外の fact を数えない", u"    return out, len(FACT_RE.findall(text)) - inside", u"    return out, 0", ("read", "doc", "build")),
    (u"M29 行の外の fact を file の全部の数にする", u"    return out, len(FACT_RE.findall(text)) - inside", u"    return out, len(FACT_RE.findall(text))", ("read", "doc", "build")),
    (u"M29b texts_rows が file を昇順に並べない", u"    for _n, text in sorted(texts, key=lambda q: q[0]):\n        r, o = read_rows(text)", u"    for _n, text in texts:\n        r, o = read_rows(text)", ("read",)),
    (u"M30 行の切り方の 1 対 1 の照合を外す", u"    if len(matches) != len(frows) or any(m.group(0) != fr[0] for m, fr in zip(matches, frows)):", u"    if False:", ("read",)),
    (u"M31 空の欄の判定を true 以外にも広げる", u'    return attrs.get(NIL_ATTR) == "true"', u"    return NIL_ATTR in attrs", ("read", "doc", "build")),
    (u"M33 行の字が空の行を表に入れる", u"        if not T:\n            continue\n        for td, a in facts:", u"        for td, a in facts:", ("tables",)),
    (u"M34 束 5 の表に空の欄を混ぜる", u"            if not is_nil(a):\n                b5 = bundle5(a)", u"            if True:\n                b5 = bundle5(a)", ("tables", "doc", "build")),
    (u"M35 束 3 の表から空の欄を外す", u'            tabs["HT3"].setdefault((h, th, T, td), set()).add(b3)\n            tabs["H3"].setdefault((h, T, td), set()).add(b3)',
     u'            if not is_nil(a):\n                tabs["HT3"].setdefault((h, th, T, td), set()).add(b3)\n                tabs["H3"].setdefault((h, T, td), set()).add(b3)', ("tables", "doc", "build")),
    (u"M36 束 5 を束 3 と同じ 3 つの属性で作る", u"    return tuple(attrs.get(k) for k in ATTRS5)", u"    return tuple(attrs.get(k) for k in ATTRS3)", ("read", "tables", "small")),
    (u"M37 束 5 の桁(scale)を落とす", u'ATTRS5 = ATTRS3 + ("decimals", "scale")', u'ATTRS5 = ATTRS3 + ("decimals",)', ("read", "small", "seal")),
    (u"M38 今年の側の束 5 の類を空の欄の fact にも数える", u"            if not nil:\n                ht5 = stage_ht(", u"            if True:\n                ht5 = stage_ht(", ("doc", "build")),
    (u"M39 束 3(空の欄でない fact)の分母に空の欄を入れる", u"                if not nil:\n                    acc[\"C\"][\"b3nn\"][s][classify6(b3, by_stage3[s])] += 1", u"                if True:\n                    acc[\"C\"][\"b3nn\"][s][classify6(b3, by_stage3[s])] += 1", ("doc", "build")),
    (u"M40 X の fact を空の欄でも束 5 に数える", u'                    if b in ("b5", "b3nn") and nil:', u'                    if False and b in ("b5", "b3nn") and nil:', ("small",)),
    # ---- 段
    (u"M41 段 F が常に段 H を使う", u"    if c_ht:\n        return set(c_ht)\n    return set(c_h)", u"    return set(c_h)", ("tables", "doc", "build")),
    (u"M42 段 F が段 HT と段 H の和集合になる", u"    if c_ht:\n        return set(c_ht)\n    return set(c_h)", u"    return set(c_ht) | set(c_h)", ("tables", "doc", "build")),
    (u"M43 段 F が段 H へ落とさない(段 HT が空なら空のまま)", u"    if c_ht:\n        return set(c_ht)\n    return set(c_h)", u"    return set(c_ht)", ("tables", "doc", "build")),
    (u"M44 段 F の落とし先を段 H でなく段 HT の別の鍵にする", u"    return set(c_h)\n\n\ndef classify6", u"    return set()\n\n\ndef classify6", ("tables", "doc", "build")),
    (u"M45 候補に今年の fact の束を足す", u"            ht3 = stage_ht(tabs[\"HT3\"], h, th, T, td)\n", u"            ht3 = stage_ht(tabs[\"HT3\"], h, th, T, td) | set([bundle3(a)])\n", ("doc", "build")),
    (u"M46 前の年の表を今年の側の字から作る", u"    tabs = build_tables(prior_rows, secret)", u"    tabs = build_tables(cur_rows, secret)", ("doc", "build")),
    (u"M47 前の年の側として今年の zip を読む", u"        with zipfile.ZipFile(pp) as z:", u"        with zipfile.ZipFile(p) as z:", ("build", "e2e")),
    (u"M48 落ちた fact の条件を段 H の空にする", u"            if not ht3:\n                acc[\"fall\"] += 1", u"            if not h3:\n                acc[\"fall\"] += 1", ("doc", "build")),
    (u"M49 落ちた fact の類を段 HT の類で数える", u'                acc["fallc"][classify6(b3, by_stage3["F"])] += 1', u'                acc["fallc"][classify6(b3, by_stage3["HT"])] += 1', ("doc", "build")),
    # ---- 属性ごと
    (u"M50 属性ごとの候補を射影でなく束のままにする", u"                    acc[\"C\"][key][s][classify6(b3[i], project(by_stage3[s], i))] += 1", u"                    acc[\"C\"][key][s][classify6(b3[i], by_stage3[s])] += 1", ("doc", "build")),
    (u"M51 属性ごとの contextRef と name を取り違える", u'for i, key in enumerate(("name", "ctx", "unit")):', u'for i, key in enumerate(("ctx", "name", "unit")):', ("doc", "build")),
    (u"M52 属性の取り出しの添字を 1 つずらす", u"def project(cands, i):\n    return set(b[i] for b in cands)", u"def project(cands, i):\n    return set(b[(i + 1) % 3] for b in cands)", ("tables", "doc", "build")),
    # ---- 合計・判定
    (u"M53 95% の境を 90% にする", u"U_DOC_HI_PCT = 95", u"U_DOC_HI_PCT = 90", ("seal", "build")),
    (u"M54 95% の境でちょうど 95.0% を含めない", u"    return bool(d) and 100 * u >= pct * d", u"    return bool(d) and 100 * u > pct * d", ("build",)),
    (u"M55 書類ごとの率の分母を行の数にする", u"            if doc_u_rate_ge(u_ht, f, U_DOC_HI_PCT):", u'            if doc_u_rate_ge(u_ht, acc["rows"], U_DOC_HI_PCT):', ("build",)),
    (u"M56 XZ0-6 の差の向きを逆にする", u'diff_points(b5ht["U"], NN, b3nn["U"], NN)', u'diff_points(b3nn["U"], NN, b5ht["U"], NN)', ("build",)),
    (u"M57 XZ0-6 の束 3 を空の欄を含む分母の U にする", u'(u"束 3 の U の fact(空の欄でない fact だけ)", b3nn["U"])', u'(u"束 3 の U の fact(空の欄でない fact だけ)", b3["HT"]["U"])', ("build",)),
    (u"M58 XZ0-5 の差の向きを逆にする", u'diff_points(ht["U"], D, hh["U"], D)', u'diff_points(hh["U"], D, ht["U"], D)', ("build",)),
    (u"M59 XZ0-2 の分母を U だけにする", u'rate_of(ht["W1"], ht["U"] + ht["W1"])', u'rate_of(ht["W1"], ht["U"])', ("build",)),
    (u"M60 XZ0-3 を N だけにする(X を足さない)", u'rate_of(ht["N"] + ht["X"], D)', u'rate_of(ht["N"], D)', ("build",)),
    (u"M61 XZ0-7 の name と contextRef を取り違える", u'(u"contextRef の U の fact", C["ctx"]["HT"]["U"]), (u"name の U の fact", C["name"]["HT"]["U"])', u'(u"contextRef の U の fact", C["name"]["HT"]["U"]), (u"name の U の fact", C["ctx"]["HT"]["U"])', ("build",)),
    (u"M62 前の年の側の並びの sha256 を今年の側の stem で作る", u'u"\\n".join(p[3] for p in pairs)', u'u"\\n".join(p[1] for p in pairs)', ("build",)),
    (u"M63 前の年の側の並びの sha256 を昇順にする", u'u"\\n".join(p[3] for p in pairs)', u'u"\\n".join(sorted(p[3] for p in pairs))', ("build",)),
    (u"M64 予測の境 XZ0-1 の上限を替える", u'("XZ0-1", (70, 86))', u'("XZ0-1", (70, 87))', ("seal",)),
    (u"M65 組の数を 62 にする", u"PAIRS_WANT = 63", u"PAIRS_WANT = 62", ("seal",)),
    (u"M66 先に疑う旗の 95% を 96% にする", u"FLAG_HT_U_OVER = 95", u"FLAG_HT_U_OVER = 96", ("seal", "flags")),
    # ---- 旗
    (u"M67 旗 1 の「超えた」を「以上」にする", u'(u"旗", 100 * b3["HT"]["U"] > FLAG_HT_U_OVER * D)', u'(u"旗", 100 * b3["HT"]["U"] >= FLAG_HT_U_OVER * D)', ("flags",)),
    (u"M68 旗 2 の「超えた」を「以上」にする", u'(u"旗", 100 * b3["HT"]["N"] > FLAG_HT_N_OVER * D)', u'(u"旗", 100 * b3["HT"]["N"] >= FLAG_HT_N_OVER * D)', ("flags",)),
    (u"M69 旗 3 の「未満」を「以下」にする", u'(u"旗", 100 * C["name"]["HT"]["U"] < FLAG_NAME_U_UNDER * D)', u'(u"旗", 100 * C["name"]["HT"]["U"] <= FLAG_NAME_U_UNDER * D)', ("flags",)),
    (u"M70 旗 4 の分母を行の中の fact だけにする", u'(u"分母", D + tot["outside"]), (u"旗", 100 * tot["outside"] > FLAG_OUTSIDE_OVER * (D + tot["outside"]))',
     u'(u"分母", D), (u"旗", 100 * tot["outside"] > FLAG_OUTSIDE_OVER * D)', ("flags", "build")),
    (u"M71 旗が立ったら止める", u'    rec[u"限界"] = list(LIMITS)\n    return rec, secret', u'    if any(f[u"旗"] for f in rec[u"先に自分の欠陥を疑う旗(止めない。当たり外れではない)"].values()):\n        raise Stop(u"旗")\n    rec[u"限界"] = list(LIMITS)\n    return rec, secret', ("flags",)),
    # ---- 記録の検査・書き方
    (u"M72 日付の形の検査を外す", u"    if DATE_RE.search(", u"    if False and DATE_RE.search(", ("clean",)),
    (u"M73 前の年の側の docID を secret に入れない", u"[d[0] for d in docs] + [p[3] for p in pairs]", u"[d[0] for d in docs]", ("secret",)),
    (u"M75 記録を排他で書かない", u'    if os.path.exists(path):\n        raise Stop(u"**記録が既に在る', u'    if False:\n        raise Stop(u"**記録が既に在る', ("clean", "e2e")),
    (u"M76 --check が secret を検査に渡さない", u"    check_clean(rec, text, secret)\n    say(u\"--check", u"    check_clean(rec, text)\n    say(u\"--check", ("secret",)),
    (u"M77 前の便の script を一意でない名で読む", u'name = "_xz0_prior_year_draft_2026_11_22"', u'name = "xbrl_prior_year_draft"', ("import",)),
    (u"M78 記録の engine の指紋を空にする", u'rec[u"engine の指紋"] = od((k, fp[k]) for k in', u'rec[u"engine の指紋"] = od((k, u"") for k in', ("build",)),
    (u"M79 記録の script の sha256 を空にする", u'rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))', u'rec[u"この script の sha256"] = u""', ("build",)),
    (u"M80 記録の限界を 6 行にする", u'rec[u"限界"] = list(LIMITS)', u'rec[u"限界"] = list(LIMITS)[:6]', ("build",)),
    (u"M82 見出しの字を secret に入れない", u"            secret[0].add(T)\n            if h:\n                secret[4].add(h)\n    return acc", u"            secret[0].add(T)\n    return acc", ("secret",)),
)

#: 黙るのが設計どおりの変異(同値)。理由を書き、別の試験で「黙ること」を縛る
SILENT_BY_DESIGN = (
    (u"S2 count_pair が前の年の側の file の並びを逆にして渡す",
     u"    cur_rows, outside = texts_rows(cur_texts)\n    prior_rows, _o = texts_rows(prior_texts)", u"    cur_rows, outside = texts_rows(cur_texts)\n    prior_rows, _o = texts_rows(list(reversed(prior_texts)))",
     u"前の年の側の file の並びは表の集まりに効かない(同値の変異)。``texts_rows`` が file 名で並べ直す。"),
    (u"S3 組の提出者のコードを secret に入れない",
     u"set(p[5] for p in pairs), set(), set())", u"set(), set(), set())",
     u"組の相手は同じ提出者のコードで見つかるので、今年の側の zip の xsd の名から正規表現で集める EDINET コードに同じコードが入る(同値の変異)。"),
)


def check_by_name(name, mod, src):
    table_ = {u"seal": seal_problems, u"read": read_problems, u"tables": tables_problems, u"doc": doc_problems, u"build": build_problems,
              u"clean": clean_problems, u"e2e": e2e_problems, u"secret": secret_problems, u"flags": flags_problems, u"small": small_problems}
    if name in table_:
        return table_[name](mod)
    if name == u"import":
        return import_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"read", u"tables", u"doc", u"small", u"build", u"clean", u"e2e", u"secret", u"flags", u"import")


def run_mutants(table_=MUTANTS):
    base = read(SCRIPT_REL)
    out = []
    for name, old, new, checks in table_:
        assert base.count(old) == 1, (name, base.count(old))
        src = base.replace(old, new)
        try:
            mod = load_source(src)
        except BaseException as exc:                # noqa: BLE001
            out.append((name, [(c, True) for c in checks], u"読めない: %s" % type(exc).__name__))
            continue
        res = [(c, bool(guard(check_by_name, c, mod, src))) for c in checks]
        out.append((name, res, u""))
    return out


# ======================================================================== 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_constants_equal_the_seal(self):
        self.assertEqual([], seal_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        for old, new in ((u"段 HT・束 3 の類 U は 70% 以上 86% 以下", u"段 HT・束 3 の類 U は 70% 以上 87% 以下"),
                         (u"95% 以上の書類は 3 本以下で、80% 以上の書類は 20 本以上 50 本以下", u"95% 以上の書類は 4 本以下で、80% 以上の書類は 20 本以上 50 本以下"),
                         (u"組の数が 63 でなければ script は止まる", u"組の数が 62 でなければ script は止まる"), (u"段 HT・束 3 の類 W1 は 2.5% 以下", u"段 HT・束 3 の類 W1 は 3.5% 以下"),
                         (u"段 HT・束 3 の U が 95% を超えた", u"段 HT・束 3 の U が 96% を超えた"), (u"今年の側 67 本", u"今年の側 68 本"),
                         (u"空なら段 H の候補", u"空なら段 HT の候補"), (u"文脈は `contextRef` の字(名)で比べる", u"文脈は `contextRef` の字(名)で比べない"),
                         (u"表 HT: (h, th, T, td)", u"表 HT: (h, T, td)")):
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"prior_year_fact_draft", body)
        self.assertNotIn(u"xbrl_prior_year", body)


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_the_order_check_lists_the_script_and_the_gate_and_not_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)


class PureTest(unittest.TestCase):
    def test_b_1_the_key_parts_rows_th_td_and_fact_attributes(self):
        self.assertEqual([], read_problems())

    def test_b_2_tables_stages_and_classes(self):
        self.assertEqual([], tables_problems())

    def test_b_3_made_up_pair_equals_the_hand_count(self):
        self.assertEqual([], doc_problems())
        self.assertEqual([], small_problems())

    def test_b_4_the_hand_counts_are_not_the_same_as_nearby_numbers(self):
        u"""手で決めた値が足し算と合い、類の数が段ごとに互いに違い(U・A・W1・W2・N・X)、段が違えば U が違う。"""
        h = HAND_D1
        for key in ("b3", "b3nn"):
            for stage in h[key]:
                self.assertEqual(len(set(stage)), 6, (key, stage))
        self.assertEqual(h["facts"], sum(h["b3"][0]))
        self.assertEqual(h["facts"], sum(h["b3"][1]))
        self.assertEqual(h["facts"], sum(h["b3"][2]))
        for stage in h["b5"]:
            self.assertEqual(h["facts"] - h["nil"], sum(stage))
            self.assertEqual(len(set(stage)), 6, stage)
        for stage in h["b3nn"]:
            self.assertEqual(h["facts"] - h["nil"], sum(stage))
        self.assertEqual(h["fall"], sum(h["fallc"]))
        self.assertEqual(h["fall"], h["b3"][0][5])                        # 段 HT が空の fact の数は段 HT の N と一致(X は落ちない)
        us = [s[1] for s in h["b3"]]
        self.assertEqual(len(set(us)), 3)
        self.assertTrue(us[1] < us[0] < us[2])                           # 段 H < 段 HT < 段 F
        self.assertNotEqual(h["b5"][0][1], h["b3nn"][0][1])              # 束 5 の U と束 3 の U が違う
        for key in ("name_ht", "ctx_ht", "unit_ht"):
            self.assertEqual(h["facts"], sum(h[key]))
        self.assertTrue(h["ctx_ht"][1] > h["name_ht"][1] > h["b3"][0][1])
        self.assertNotIn(h["rows"], (h["facts"], h["facts"] + h["outside"]))
        self.assertNotEqual(h["nil"], h["outside"] + 1)

    def test_b_5_the_fake_zips_have_the_decoys_the_checks_say(self):
        with Temp() as d:
            docs, prior = make_dirs(d)
            with zipfile.ZipFile(os.path.join(docs, "S1ZZ0001.zip")) as z:
                names = z.namelist()
            self.assertTrue(any(n.startswith(u"XBRL/AuditDoc/") for n in names) and any(n.endswith(u"_other.htm") for n in names) and any(n.endswith(u"_lab.xml") for n in names))
            self.assertEqual(5, len([x for x in os.listdir(docs) if x.endswith(".zip")]))
            self.assertEqual(4, len([x for x in os.listdir(prior) if x.endswith(".zip")]))
        u"""読んではいけない file が数に入らないこと: 組 1 の数は decoy の有無で変わらない。"""
        got = acc_hand(MS.count_pair(cur_files(), prior_files()))
        self.assertEqual(HAND_D1["facts"], got["facts"])


class RecordTest(unittest.TestCase):
    def test_c_1_the_forbidden_checks_stop_planted_content(self):
        self.assertEqual([], clean_problems())

    def test_c_2_cache_to_record_to_check_without_reading_the_real_cache(self):
        self.assertEqual([], build_problems())
        self.assertEqual([], e2e_problems())

    def test_c_3_the_production_secret_is_built_and_check_passes_it_to_the_clean_check(self):
        self.assertEqual([], secret_problems())

    def test_c_4_the_flags_are_written_not_stopped_and_change_at_the_exact_boundaries(self):
        self.assertEqual([], flags_problems())

    def test_c_5_the_real_record_when_present_is_clean(self):
        u"""記録は本番の走りの後に書かれる。在れば中身を見て、無ければ見ない(skip にしない)。"""
        p = os.path.join(ROOT, RECORD_REL)
        if os.path.exists(p):
            text = read(RECORD_REL)
            rec = json.loads(text, object_pairs_hook=od)
            MS.check_clean(rec, text)
            self.assertEqual(list(MS.LIMITS), rec[u"限界"])
            self.assertEqual(MS.SEAL_COMMIT, rec[u"封の commit"])
            self.assertEqual(63, rec[u"材料"][u"組の数"])
            self.assertEqual(63, len(rec[u"書類"]))
        else:
            self.assertFalse(os.path.exists(p))


class WiringTest(unittest.TestCase):
    def test_e_1_imports_engine_calls_and_the_current_fact_is_not_given_to_the_candidates(self):
        self.assertEqual([], import_problems())

    def test_e_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], import_problems(base + u"\nimport socket\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport urllib.request\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = os.environ.get('A')\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef select_docs(a, b):\n    return None\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = '_lab.xml'\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef mutate(x):\n    return x\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = 'run_doc('\n"))
        self.assertNotEqual([], import_problems(base.replace(u"def stage_h(tab, h, T, td):", u"def stage_h(tab, h, T, td, a):")))
        self.assertNotEqual([], import_problems(base.replace(u"stage_h(tabs[\"H3\"], h, T, td)", u"stage_h(tabs[\"H3\"], h, T, td, a)")))
        self.assertNotEqual([], import_problems(base.replace(u"I._row_label(rowtext)", u"None")))
        self.assertNotEqual([], import_problems(base.replace(u"from adapters.xbrl import instance as I", u"from adapters.xbrl import instance as I\nfrom adapters.xbrl import recipes as R")))
        self.assertNotEqual([], import_problems(base.replace(u"prv = N.doc_texts(z)", u"prv = []")))
        self.assertNotEqual([], import_problems(base.replace(u"Y.make_pairs(", u"make_pairs(")))

    def test_e_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_e_4_the_script_leaves_sys_modules_as_it_found_them_except_its_own_prior_name(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_prior_year_fact_draft_script_for_sysmodules_check")
        self.assertEqual([], [k for k, v in before.items() if sys.modules.get(k) is not v])
        self.assertIn(PRIOR_NAME, sys.modules)
        self.assertIs(mod.Y, sys.modules[PRIOR_NAME])
        self.assertIs(mod.W, mod.Y.W)
        self.assertIs(mod.N, mod.Y.N)
        del mod

    def test_e_5_the_default_places_are_outside_the_repo_and_the_gate_never_opens_them(self):
        top = os.path.realpath(REPO)
        for p in (MS.DOCS_DIR, MS.PRIOR_DIR):
            self.assertFalse(os.path.realpath(p).startswith(top + os.sep), p)
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(run|check|build_record)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"\bd\b|docs|\*\*kw|rec_path|prior", m.group(2)), m.group(0))

    def test_e_6_the_script_uses_no_name_of_the_injection_harness_criteria(self):
        src = read(SCRIPT_REL)
        for w in HARNESS_WORDS:
            self.assertNotIn(w, src, w)


class MutantTest(unittest.TestCase):
    def test_f_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL))
        modules_before = dict(sys.modules)
        results = run_mutants()
        self.assertEqual(before, (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL)))
        self.assertEqual([], [k for k, v in modules_before.items() if sys.modules.get(k) is not v])
        silent = [(n, c) for n, res, _w in results for c, red in res if not red]
        self.assertEqual([], silent)
        self.assertEqual(len(MUTANTS), len(results))
        self.assertEqual([], [n for n, res, _w in results if not res])                   # 検査を 1 つも持たない変異は無い
        self.assertGreaterEqual(len(MUTANTS), 40)

    def test_f_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ALL_CHECKS:
            self.assertEqual([], check_by_name(name, mod, base), name)

    def test_f_3_the_silent_mutants_are_silent_for_the_stated_reason(self):
        u"""同値の変異は、作り物の全部の検査でも、元と同じ。"""
        base = read(SCRIPT_REL)
        for name, old, new, _why in SILENT_BY_DESIGN:
            self.assertEqual(1, base.count(old), name)
            mod = load_source(base.replace(old, new))
            for c in (u"read", u"tables", u"doc", u"small", u"build", u"clean", u"e2e", u"secret", u"flags"):
                self.assertEqual([], check_by_name(c, mod, None), (name, c))
            self.assertEqual(acc_hand(MS.count_pair(cur_files(), prior_files())), acc_hand(mod.count_pair(cur_files(), prior_files())), name)


if __name__ == "__main__":
    unittest.main()
