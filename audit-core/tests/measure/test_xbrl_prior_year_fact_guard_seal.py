# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PRIOR_YEAR_FACT_GUARD_SEAL_2026-11-22.md(XZ1 ― 前の年の下書きが黙って違う属性を付ける fact を、行の順の番号の振り直しと表の頭の字の守りで直す・止める)の封の門。

**この門は置き場を読まない**(今年の側・前の年の側の置き場は 1 度も開かない)。通信しない。
読むのは repo の中の封の file・script だけ。作り物の zip(今年の側と前の年の側の組)を、本物の関数のまま通す。作り物の字は全部作り物(本物の見出し・要素・文脈・形の字は使わない)。

**この門が縛るもの**

1. 封の字: 封の commit(2079af62)・封の file が commit した blob と同じ・組の数 63・60 組の fact の合計 61100・file の名(script・記録・門)・予測の境(XZ1-1〜XZ1-8)・先に疑う旗の境(30%)・
   記録に書かないものの字・限界の 6 行・4 つの段・類の字・番号つきのメンバーの形が script の定数と同じ。
2. engine は封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 作り物の組で、形(当たる部品 0・1・2 つ・1 つ目の部品)・表 COL・番号の列を使う条件の 2 つの枝・行の番号 k(T が空の行と番号の列を使わない行は数えない・表が変われば 1 から・file が変われば 1 から)・
   表の頭の印(fact の行より前の行だけ・数字とタグを除く)・段 HT・O・G・OG・類 S(X と N は止めない)・段 OG で番号の列を使う fact の印の比べ先・W1 の中身(7 通り・番号だけの違い)・
   段の間の移り・60 組と 3 組の分けを、手で数えた値と照らす(類ごとに違う数)。
4. 今年の fact の属性は候補を作る関数に渡さない。前の年の側として今年の zip を読まない。
5. 便 XZ0 の記録と段 HT の類の数が 1 つでも違えば・60 組の fact の合計が 61100 でなければ止まる(作り物の記録と合計で確かめる)。先に疑う旗は止めず記録に書き、境(ちょうど 30%)で変わる。
6. script の import は標準ライブラリと engine の 1 module(verify_document)と importlib だけ。前の便の script は importlib で読み(一意の名)、関数は呼ぶ(写さない)。
7. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
黙る変異は ``SILENT_BY_DESIGN`` に理由とともに置き、「黙ること」自体を別の試験で縛る。
記録(``fixtures/xbrl/cd8/prior_year_fact_guard_2026-11-22.json``)は本番の走りの後に書かれる。記録が在れば中身を見て、無ければ見ない(skip にしない。見る作りが「在れば」)。
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
    mod = types.ModuleType("xbrl_prior_year_fact_guard_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_PRIOR_YEAR_FACT_GUARD_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "2079af62"                # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_prior_year_fact_guard_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_prior_year_fact_guard_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/prior_year_fact_guard_2026-11-22.json"
DRAFT_RECORD_REL = "fixtures/xbrl/cd8/prior_year_fact_draft_2026-11-22.json"
MS = load_module(SCRIPT_REL, "xbrl_prior_year_fact_guard_script_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_prior_year_fact_guard_seal")      # 順序・履歴の部品。門としては走らせない
ORDER_FILES = (SCRIPT_REL, GATE_REL)          # 記録の順序は記録が在るときの結果の門に置く
od = collections.OrderedDict
CLS = ("X", "U", "A", "W1", "W2", "N")
CLS_S = CLS + ("S",)


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
        self.d = tempfile.mkdtemp(prefix="xz1_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


# ======================================================================== 作り物の書類
CA, CB, UJ, US = u"ctxA", u"ctxB", u"unitJ", u"unitS"


def F(key, ctx=CA, unit=UJ):
    u"""数の fact 1 つ(要素の名は作り物 ``fk:Item<key>``)。"""
    return u'<ix:nonFraction name="fk:Item%s" contextRef="%s" unitRef="%s" decimals="-6" scale="6" format="fmtZ">100</ix:nonFraction>' % (key, ctx, unit)


def NILF(key, ctx=CA, unit=UJ):
    u"""空の欄の数の fact 1 つ(``xsi:nil="true"`` の自己閉じ。unit が None なら unitRef の属性を書かない)。"""
    return u'<ix:nonFraction name="fk:Item%s" contextRef="%s"%s decimals="-6" scale="6" format="fmtZ" xsi:nil="true" />' % (key, ctx, u"" if unit is None else u' unitRef="%s"' % unit)


def NO(n):
    u"""番号つきの文脈(作り物の字)。形は ``C_No#Member``。"""
    return u"C_No%dMember" % n


def row(label, *cells):
    return u"<tr><td>%s</td>%s</tr>" % (label, u"".join(u"<td>%s</td>" % c for c in cells))


def head(h):
    return u"<p>【%s】</p>" % h


def table(rows):
    return u"<table>" + u"".join(rows) + u"</table>"


def rows_of(label, n, *cells):
    return [row(label, *cells) for _ in range(n)]


# ---- 場面 1: 表の頭の守り(段 G・OG)。番号の列は使わない
#: 前の年: 見出しア・表 0(頭 = 「期ア年|単位ア」・末尾の行は fact の後)・表 1(頭 = 「期ア年」)
PRIOR1 = [("a_ixbrl.htm", head(u"見出しア")
           + table([row(u"期ア 2024年"), row(u"単位ア"), row(u"科目甲", F("01")), row(u"科目乙", F("02")), row(u"科目丙", F("03")), row(u"科目丙", F("03b")), row(u"注 末尾イ")])
           + table([row(u"期ア 2025年"), row(u"科目甲", F("01"))])
           + table([row(u"期エ 2025年"), row(u"科目甲", F("01"))]))]
#: 今年: 表 0 は頭が年の数字・空白の字(全角)・タグ・末尾の行だけ違う(止めない)・表 1 は頭が表 1 と同じ(表 0 の頭とは違う。止めない)・表 2 は頭の字が違う(止める)
CUR1 = [("a_ixbrl.htm", head(u"見出しア")
         + table([row(u"期ア　2030年"), u"<tr><td><b>単位ア</b></td></tr>"]
                 + rows_of(u"科目甲", 2, F("01")) + rows_of(u"科目乙", 2, F("02", CB)) + rows_of(u"科目丙", 2, F("03")) + rows_of(u"科目丙", 4, F("05"))
                 + rows_of(u"科目丁", 6, F("06")) + [row(u"", F("07")), row(u"注 末尾ウ")])
         + table([row(u"期ア 2031年")] + rows_of(u"科目甲", 1, F("01")))
         + table([row(u"期ウ 2030年")] + rows_of(u"科目甲", 2, F("01")) + [row(u"科目甲", F("01", CB))]))]
#: 手で数える(類は X・U・A・W1・W2・N の順。G・OG は S を足す)。今年の fact 21。
HAND1 = dict(facts=21, HT=(1, 5, 2, 3, 4, 6), O=(1, 5, 2, 3, 4, 6), G=(1, 3, 2, 2, 4, 6, 3), OG=(1, 3, 2, 2, 4, 6, 3),
             stopped_g=(0, 2, 0, 1, 0, 0), stopped_og=(0, 2, 0, 1, 0, 0), numcol=0, w1_diff=(0, 3, 0, 0, 0, 0, 0), number_only=0)

# ---- 場面 2: 番号の列(行の番号 k)。頭は全部同じ(止めない)
PRIOR2 = [("a_ixbrl.htm", head(u"見出しイ")
           + table([row(u"順 表頭 1"), row(u"役員甲", F("11", NO(1)), F("12", NO(1))), row(u"役員乙", F("11", NO(2)), F("12", NO(2))), row(u"役員辛", F("16"))])
           + table([row(u"順 表頭 1"), row(u"役員甲", F("15", NO(1)))])),
          ("b_ixbrl.htm", head(u"見出しイ") + table([row(u"順 表頭 1"), row(u"役員甲", F("11", NO(1)))]))]
CUR2 = [("a_ixbrl.htm", head(u"見出しイ")
         + table([row(u"順 表頭 2"),
                  row(u"役員乙", F("11", NO(1)), F("12", NO(1))),                       # k=1。HT は W1(前の年の乙は No2)
                  row(u"", F("11", NO(9))),                                             # T が空: X。k に数えない
                  row(u"役員戊", u"－", u"－", F("14")), row(u"役員戊", u"－", u"－", F("14")),   # 番号の列を使わない行(td 4 に COL が無い): N。k に数えない
                  row(u"役員辛", F("16")),                                              # 文脈に形が無い候補だけが在る行(表 COL に鍵は在る): 番号の列を使わない。k に数えない。U
                  row(u"役員丙", F("11", NO(2)), F("12", NO(2))),                       # k=2。HT は N(行の字が前の年に無い)
                  row(u"役員丁", F("13")), row(u"役員丁", F("13")),                     # k=3・4。文脈に形が無い fact が COL の候補(No3・No4)に外れて W1
                  row(u"役員己", F("11", NO(5)), F("12", NO(5)))])                      # k=5
         + table([row(u"順 表頭 7"), row(u"役員甲", F("15", NO(1))), row(u"役員甲", F("15", NO(1)))])),   # 表が変われば k は 1 から。2 行目は k=2 で W1
        ("b_ixbrl.htm", head(u"見出しイ") + table([row(u"順 表頭 3"), row(u"役員甲", F("11", NO(1)))]))]                # file が変われば k は 1 から
HAND2 = dict(facts=15, HT=(1, 4, 0, 2, 0, 8), O=(1, 9, 0, 3, 0, 2), G=(1, 4, 0, 2, 0, 8, 0), OG=(1, 9, 0, 3, 0, 2, 0),
             stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=11, w1_diff=(0, 2, 0, 0, 0, 0, 0), number_only=2,
             move={("X", "X"): 1, ("U", "U"): 3, ("U", "W1"): 1, ("W1", "U"): 2, ("N", "N"): 2, ("N", "U"): 4, ("N", "W1"): 2})

# ---- 場面 3: 段 OG で番号の列を使う fact の印の比べ先(表 COL の側の印の集まり)。前の年の 2 つの file が同じ (h, th) で頭が違う
PRIOR3 = [("a_ixbrl.htm", head(u"見出しウ")
           + table([row(u"ア頭 1"), row(u"科目甲", F("11", NO(1)))])
           + table([row(u"エ頭 1"), row(u"科目乙", F("21"))])),
          ("b_ixbrl.htm", head(u"見出しウ") + table([row(u"イ頭 1"), row(u"科目戊", F("11", NO(2)))]))]
CUR3 = [("t_ixbrl.htm", head(u"見出しウ")
         + table([row(u"イ頭 9"), row(u"科目甲", F("11", NO(1))), row(u"科目甲", F("11", NO(2))), row(u"科目甲", F("11", NO(3))), row(u"科目丙", F("11", NO(4)))])
         + table([row(u"オ頭 1")] + rows_of(u"科目乙", 2, F("21")))),
        ("u_ixbrl.htm", head(u"見出しウ") + table([row(u"ウ頭 1")] + [row(u"科目丙", F("11", NO(k))) for k in (1, 2, 3)]))]      # 頭が表 COL の側のどの印にも無い(行の字は前の年に無い: HT は N・O は U・OG は S)
HAND3 = dict(facts=9, HT=(0, 3, 0, 2, 0, 4), O=(0, 9, 0, 0, 0, 0), G=(0, 0, 0, 0, 0, 4, 5), OG=(0, 4, 0, 0, 0, 0, 5),
             stopped_g=(0, 3, 0, 2, 0, 0), stopped_og=(0, 5, 0, 0, 0, 0), numcol=7, w1_diff=(0, 2, 0, 0, 0, 0, 0), number_only=2,
             move={("U", "U"): 3, ("W1", "U"): 2, ("N", "U"): 4})

# ---- 場面 4: W1 の違う属性の組(7 通り)。頭は同じ
PRIOR4 = [("a_ixbrl.htm", head(u"見出しエ") + table([row(u"表頭 1")] + [row(l, F("31")) for l in (u"科目ア", u"科目イ", u"科目ウ", u"科目エ", u"科目オ", u"科目カ", u"科目キ")]))]
CUR4 = [("a_ixbrl.htm", head(u"見出しエ")
         + table([row(u"表頭 2")] + rows_of(u"科目ア", 1, F("32")) + rows_of(u"科目イ", 2, F("31", CB)) + rows_of(u"科目ウ", 3, F("31", CA, US)) + rows_of(u"科目エ", 4, F("32", CB))
                 + rows_of(u"科目オ", 5, F("32", CA, US)) + rows_of(u"科目カ", 6, F("31", CB, US)) + rows_of(u"科目キ", 7, F("32", CB, US))))]
HAND4 = dict(facts=28, HT=(0, 0, 0, 28, 0, 0), O=(0, 0, 0, 28, 0, 0), G=(0, 0, 0, 28, 0, 0, 0), OG=(0, 0, 0, 28, 0, 0, 0),
             stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=0, w1_diff=(1, 2, 3, 4, 5, 6, 7), number_only=0)

# ---- 場面 5: 番号 3 の組(見た 3 組の端)。頭は同じ
PRIOR5 = [("a_ixbrl.htm", head(u"見出しオ") + table([row(u"表頭 1"), row(u"科目子", F("41"))]))]
CUR5 = [("a_ixbrl.htm", head(u"見出しオ") + table([row(u"表頭 2")] + rows_of(u"科目子", 2, F("41")) + rows_of(u"科目孫", 1, F("42"))))]
HAND5 = dict(facts=3, HT=(0, 2, 0, 0, 0, 1), O=(0, 2, 0, 0, 0, 1), G=(0, 2, 0, 0, 0, 1, 0), OG=(0, 2, 0, 0, 0, 1, 0),
             stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=0, w1_diff=(0,) * 7, number_only=0)

# ---- 場面 6〜8(独立監査が見つけた 4 つの穴を塞ぐ。既存の場面の数は変えない)。番号の列の外の属性・今年の文脈の形・行の中の並び
#: 場面 6: 番号の列を使う fact で、表 COL の候補と name だけが違う(k=1〜3)・unit だけが違う(k=4・5)。段 O でも W1 のまま(段 O の候補の name・unit を今年の fact で埋めると U になる)
PRIOR6 = [("a_ixbrl.htm", head(u"見出しカ") + table([row(u"表頭 1"), row(u"科目A", F("51", NO(2)))]))]
CUR6 = [("a_ixbrl.htm", head(u"見出しカ")
         + table([row(u"表頭 2")] + [row(u"科目A", F("52", NO(k))) for k in (1, 2, 3)] + [row(u"科目A", F("51", NO(k), US)) for k in (4, 5)]))]
HAND6 = dict(facts=5, HT=(0, 0, 0, 5, 0, 0), O=(0, 0, 0, 5, 0, 0), G=(0, 0, 0, 5, 0, 0, 0), OG=(0, 0, 0, 5, 0, 0, 0),
             stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=5, w1_diff=(1, 0, 0, 2, 0, 2, 0), number_only=0, move={("W1", "W1"): 5})
#: 場面 7: 表 HT の候補が空でなく・候補の文脈に形が無く・今年の文脈には形が在り・(h, th, td) は表 COL に在る → 番号の列を使わない fact のまま(段 O は段 HT の類。今年の文脈の形で使うと U になる)
PRIOR7 = [("a_ixbrl.htm", head(u"見出しキ") + table([row(u"表頭 1"), row(u"科目B", F("61")), row(u"科目C", F("61", NO(1)))]))]
CUR7 = [("a_ixbrl.htm", head(u"見出しキ") + table([row(u"表頭 2")] + [row(u"科目B", F("61", NO(k))) for k in (1, 2, 3, 4)]))]
HAND7 = dict(facts=4, HT=(0, 0, 0, 4, 0, 0), O=(0, 0, 0, 4, 0, 0), G=(0, 0, 0, 4, 0, 0, 0), OG=(0, 0, 0, 4, 0, 0, 0),
             stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=0, w1_diff=(0, 4, 0, 0, 0, 0, 0), number_only=0, move={("W1", "W1"): 4})
#: 場面 8: 1 つの行に「番号の列を使う fact → 使わない fact」の順(その行も k に数える。k=1〜3)
PRIOR8 = [("a_ixbrl.htm", head(u"見出しク") + table([row(u"表頭 1"), row(u"科目D", F("71", NO(2)), F("72"))]))]
CUR8 = [("a_ixbrl.htm", head(u"見出しク") + table([row(u"表頭 2")] + [row(u"科目D", F("71", NO(k)), F("72")) for k in (1, 2, 3)]))]
HAND8 = dict(facts=6, HT=(0, 4, 0, 2, 0, 0), O=(0, 6, 0, 0, 0, 0), G=(0, 4, 0, 2, 0, 0, 0), OG=(0, 6, 0, 0, 0, 0, 0),
             stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=3, w1_diff=(0, 2, 0, 0, 0, 0, 0), number_only=2, move={("U", "U"): 4, ("W1", "U"): 2})
#: 場面 9(再監査の N2): 番号の列を使う fact で、今年の文脈の形(Row)が表 COL の形(No)と違う。段 O の候補は表 COL の形に k を入れたもの(No1〜No3)なので W1 のまま
#: (段 O の候補の形を今年の文脈の形から作ると U になる)。k=1〜3
PRIOR9 = [("a_ixbrl.htm", head(u"見出しケ") + table([row(u"表頭 1"), row(u"科目E", F("81", NO(2)))]))]
CUR9 = [("a_ixbrl.htm", head(u"見出しケ") + table([row(u"表頭 2")] + [row(u"科目E", F("81", u"C_Row%dMember" % k)) for k in (1, 2, 3)]))]
HAND9 = dict(facts=3, HT=(0, 0, 0, 3, 0, 0), O=(0, 0, 0, 3, 0, 0), G=(0, 0, 0, 3, 0, 0, 0), OG=(0, 0, 0, 3, 0, 0, 0),
             stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=3, w1_diff=(0, 3, 0, 0, 0, 0, 0), number_only=0, move={("W1", "W1"): 3})
#: 場面 10(再監査の N4): 同じ表の中で、「番号の列を使わない fact(候補に形が無い)で今年の文脈に形が在る行」のあとに「番号の列を使う行」が続く。使う行の k は 1 から(2 行目は 2)
#: 行 1(科目B)は使わない: 段 HT・O とも W1。行 2(科目E・k=1): 段 HT は W1(候補は No2)・段 O は U。行 3(科目E・k=2): 段 HT は U・段 O は U
PRIOR10 = [("a_ixbrl.htm", head(u"見出しコ") + table([row(u"表頭 1"), row(u"科目B", F("91")), row(u"科目E", F("92", NO(2)))]))]
CUR10 = [("a_ixbrl.htm", head(u"見出しコ") + table([row(u"表頭 2"), row(u"科目B", F("91", NO(1))), row(u"科目E", F("92", NO(1))), row(u"科目E", F("92", NO(2)))]))]
HAND10 = dict(facts=3, HT=(0, 1, 0, 2, 0, 0), O=(0, 2, 0, 1, 0, 0), G=(0, 1, 0, 2, 0, 0, 0), OG=(0, 2, 0, 1, 0, 0, 0),
              stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=2, w1_diff=(0, 2, 0, 0, 0, 0, 0), number_only=1, move={("W1", "W1"): 1, ("W1", "U"): 1, ("U", "U"): 1})
#: 場面 11(自分で作った近くの形): 行の番号 k は、番号の列を使う fact を持つ行を、今年の unit・今年の contextRef の形の有無に関わらず数える。k=1(unit だけ違う)・k=2(文脈に形が無い)・k=3(U)
PRIOR11 = [("a_ixbrl.htm", head(u"見出しサ") + table([row(u"表頭 1"), row(u"科目F", F("a1", NO(2)))]))]
CUR11 = [("a_ixbrl.htm", head(u"見出しサ") + table([row(u"表頭 2"), row(u"科目F", F("a1", NO(1), US)), row(u"科目F", F("a1", CB)), row(u"科目F", F("a1", NO(3)))]))]
HAND11 = dict(facts=3, HT=(0, 0, 0, 3, 0, 0), O=(0, 1, 0, 2, 0, 0), G=(0, 0, 0, 3, 0, 0, 0), OG=(0, 1, 0, 2, 0, 0, 0),
              stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=3, w1_diff=(0, 2, 0, 0, 0, 1, 0), number_only=1, move={("W1", "W1"): 2, ("W1", "U"): 1})
#: 場面 12(自分で作った近くの形): 表 COL に 2 つの形(Row・No)が在るとき、段 O の候補は各要素の自分の形に k を入れる(今年の文脈の形を全部に使わない)。段 O は W2(今年の文脈の形を全部に使うと A)
PRIOR12 = [("a_ixbrl.htm", head(u"見出しシ") + table([row(u"表頭 1"), row(u"科目G", F("a1", u"C_Row2Member")), row(u"科目H", F("b1", NO(2)))]))]
CUR12 = [("a_ixbrl.htm", head(u"見出しシ") + table([row(u"表頭 2"), row(u"科目G", F("b1", u"C_Row1Member")), row(u"科目G", F("b1", u"C_Row2Member"))]))]
HAND12 = dict(facts=2, HT=(0, 0, 0, 2, 0, 0), O=(0, 0, 0, 0, 2, 0), G=(0, 0, 0, 2, 0, 0, 0), OG=(0, 0, 0, 0, 2, 0, 0),
              stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=2, w1_diff=(1, 0, 0, 1, 0, 0, 0), number_only=0, move={("W1", "W2"): 2})
#: 場面 13(3 回目の監査の穴 A): 段 G・OG が A と W2 も止める(そのままなのは X と N だけ)。番号の列は使わない。頭が違う(「頭一」と「頭二」)。A 3・W2 1
PRIOR13 = [("a_ixbrl.htm", head(u"見出しス") + table([row(u"頭一 1"), row(u"科目P", F("a1")), row(u"科目P", F("a2")), row(u"科目Q", F("b1")), row(u"科目Q", F("b2"))]))]
CUR13 = [("a_ixbrl.htm", head(u"見出しス") + table([row(u"頭二 9")] + rows_of(u"科目P", 3, F("a1")) + rows_of(u"科目Q", 1, F("b3"))))]
HAND13 = dict(facts=4, HT=(0, 0, 3, 0, 1, 0), O=(0, 0, 3, 0, 1, 0), G=(0, 0, 0, 0, 0, 0, 4), OG=(0, 0, 0, 0, 0, 0, 4),
              stopped_g=(0, 0, 3, 0, 1, 0), stopped_og=(0, 0, 3, 0, 1, 0), numcol=0, w1_diff=(0,) * 7, number_only=0, move={("A", "A"): 3, ("W2", "W2"): 1})
#: 場面 14(穴 A): 番号の列を使う fact の段 OG が A と W2 を止める(表 COL の側の頭の印と比べる。頭は「頭三」と「頭四」で違う)。k=1〜3。段 O の A 2・W2 3(td1 は A・td2 は W2)
PRIOR14 = [("a_ixbrl.htm", head(u"見出しセ")
            + table([row(u"頭三 1"), row(u"科目R", F("c1", NO(1)), F("d1", NO(1))), row(u"科目R", F("c2", NO(2)), F("d2", NO(2)))]))]
CUR14 = [("a_ixbrl.htm", head(u"見出しセ")
          + table([row(u"頭四 9"), row(u"科目R", F("c1", NO(1)), F("d3", NO(1))), row(u"科目R", F("c2", NO(2)), F("d3", NO(2))), row(u"科目R", u"－", F("d3", NO(3)))]))]
HAND14 = dict(facts=5, HT=(0, 0, 2, 0, 3, 0), O=(0, 0, 2, 0, 3, 0), G=(0, 0, 0, 0, 0, 0, 5), OG=(0, 0, 0, 0, 0, 0, 5),
              stopped_g=(0, 0, 2, 0, 3, 0), stopped_og=(0, 0, 2, 0, 3, 0), numcol=5, w1_diff=(0,) * 7, number_only=0, move={("A", "A"): 2, ("W2", "W2"): 3})
#: 場面 15(穴 B): 行の番号 k の「番号の列を使う fact を 1 つ以上持つ行」は行の中の fact の順に依らない。行 0 は「－」のあとに使う fact(k=1)・行 1 と行 2 は先頭の fact(td 1)が使わず後ろ(td 2)が使う(k=2・3)。
#: 行の先頭の fact だけで決めると行 1・2 が k に数えられず、段 O で W1 のまま残る
PRIOR15 = [("a_ixbrl.htm", head(u"見出しソ") + table([row(u"頭五 1"), row(u"科目T", F("e1"), F("e2", NO(2)))]))]
CUR15 = [("a_ixbrl.htm", head(u"見出しソ") + table([row(u"頭五 2"), row(u"科目T", u"－", F("e2", NO(1))), row(u"科目T", F("e1"), F("e2", NO(2))), row(u"科目T", F("e1"), F("e2", NO(3)))]))]
HAND15 = dict(facts=5, HT=(0, 3, 0, 2, 0, 0), O=(0, 5, 0, 0, 0, 0), G=(0, 3, 0, 2, 0, 0, 0), OG=(0, 5, 0, 0, 0, 0, 0),
              stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=3, w1_diff=(0, 2, 0, 0, 0, 0, 0), number_only=2, move={("U", "U"): 3, ("W1", "U"): 2})
#: 場面 16(4 回目の監査の穴): 表 HT の候補が 3 つ以上(科目M の前の年の行が 3 本)・今年の fact が段 HT で U・A・W2 の混在。全部が番号の列を使う(k=1〜6)。
#: k=1 科目N(U → U)・k=2・3 科目M の No2・No3(候補 No1〜No3 の中に在る: A → U)・k=4〜6 科目M の No4〜No6(候補の外: W2 → U)。表 COL は 1 つの (name, 形, unit) だけなので段 O は候補 1 つで U になる
PRIOR16 = [("a_ixbrl.htm", head(u"見出しタ")
            + table([row(u"表頭 1"), row(u"科目M", F("m1", NO(1))), row(u"科目M", F("m1", NO(2))), row(u"科目M", F("m1", NO(3))), row(u"科目N", F("m1", NO(1)))]))]
CUR16 = [("a_ixbrl.htm", head(u"見出しタ")
          + table([row(u"表頭 2"), row(u"科目N", F("m1", NO(1)))] + [row(u"科目M", F("m1", NO(k))) for k in (2, 3, 4, 5, 6)]))]
HAND16 = dict(facts=6, HT=(0, 1, 2, 0, 3, 0), O=(0, 6, 0, 0, 0, 0), G=(0, 1, 2, 0, 3, 0, 0), OG=(0, 6, 0, 0, 0, 0, 0),
              stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=6, w1_diff=(0,) * 7, number_only=0, move={("U", "U"): 1, ("A", "U"): 2, ("W2", "U"): 3})
#: 場面 17(4 回目の監査の穴 R1): 同じ (h, th, T, td) に、形の在る行(頭甲)と形の無い行(頭乙)が頭の違う別 file に在る。表 HT の側の印の集まりは {頭甲, 頭乙}・表 COL の側は {頭甲} だけ。
#: 頭甲の表(1 行)は段 OG でも通る・頭乙の表(2 行)は番号の列を使うので表 COL の側の印と比べて止まる(段 O の類 U が 2)。表 HT の側の印と比べると通ってしまう
PRIOR17 = [("a_ixbrl.htm", head(u"見出しチ") + table([row(u"頭甲 1"), row(u"科目V", F("w1", NO(7)))])),
           ("b_ixbrl.htm", head(u"見出しチ") + table([row(u"頭乙 1"), row(u"科目V", F("w1"))]))]
CUR17 = [("t_ixbrl.htm", head(u"見出しチ") + table([row(u"頭甲 9"), row(u"科目V", F("w1", NO(1)))])),
         ("u_ixbrl.htm", head(u"見出しチ") + table([row(u"頭乙 9"), row(u"科目V", F("w1", NO(1))), row(u"科目V", F("w1", NO(2)))]))]
HAND17 = dict(facts=3, HT=(0, 0, 0, 0, 3, 0), O=(0, 3, 0, 0, 0, 0), G=(0, 0, 0, 0, 3, 0, 0), OG=(0, 1, 0, 0, 0, 0, 2),
              stopped_g=(0,) * 6, stopped_og=(0, 2, 0, 0, 0, 0), numcol=3, w1_diff=(0,) * 7, number_only=0, move={("W2", "U"): 3})
#: 場面 18(4 回目の監査の穴 R6): th だけ違う 2 つの鍵(表 0・表 1)で表の頭の印の集まりが違う(表 0 = {頭甲}・表 1 = {頭乙})。
#: 今年の表 0(頭乙)・表 1(頭甲 2 行)は鍵の th の側の集まりに無いので止まる(U 3)。別 file の表 0(頭甲)は在るので通る(W1 1)。th を鍵から外すと全部通る
PRIOR18 = [("a_ixbrl.htm", head(u"見出しツ") + table([row(u"頭甲 1"), row(u"科目Z", F("z1"))]) + table([row(u"頭乙 1"), row(u"科目Z", F("z1"))]))]
CUR18 = [("a_ixbrl.htm", head(u"見出しツ") + table([row(u"頭乙 9"), row(u"科目Z", F("z1"))]) + table([row(u"頭甲 9")] + rows_of(u"科目Z", 2, F("z1")))),
         ("b_ixbrl.htm", head(u"見出しツ") + table([row(u"頭甲 9"), row(u"科目Z", F("z1", CB))]))]
HAND18 = dict(facts=4, HT=(0, 3, 0, 1, 0, 0), O=(0, 3, 0, 1, 0, 0), G=(0, 0, 0, 1, 0, 0, 3), OG=(0, 0, 0, 1, 0, 0, 3),
              stopped_g=(0, 3, 0, 0, 0, 0), stopped_og=(0, 3, 0, 0, 0, 0), numcol=0, w1_diff=(0, 1, 0, 0, 0, 0, 0), number_only=0, move={("U", "U"): 3, ("W1", "W1"): 1})
#: 場面 19(鍵の端): 段 G(番号の列を使わない fact。段 OG も同じ鍵)の比べ先の鍵 (h, th, T, td) の端。今年の表(頭乙)の行 科目P・td 1・見出しナ・表 0 の鍵の集まりは {頭甲} だけ。
#: 頭乙の印は前の年に、td だけ違う鍵(b)・見出し h だけ違う鍵(c)・行の字 T だけ違う鍵(d)で在るので、鍵のどれか 1 つを外すと止められない。今年の頭乙の 2 行は止まり(U 2)・頭甲の 1 行は通る
PRIOR19 = [("a_ixbrl.htm", head(u"見出しナ") + table([row(u"頭甲 1"), row(u"科目P", F("p1"))])),
           ("b_ixbrl.htm", head(u"見出しナ") + table([row(u"頭乙 1"), row(u"科目P", u"－", F("p2"))])),
           ("c_ixbrl.htm", head(u"見出しニ") + table([row(u"頭乙 1"), row(u"科目P", F("p1"))])),
           ("d_ixbrl.htm", head(u"見出しナ") + table([row(u"頭乙 1"), row(u"科目Q", F("p1"))]))]
CUR19 = [("t_ixbrl.htm", head(u"見出しナ") + table([row(u"頭乙 9"), row(u"科目P", F("p1")), row(u"科目P", F("p1"))])),
         ("u_ixbrl.htm", head(u"見出しナ") + table([row(u"頭甲 9"), row(u"科目P", F("p1"))]))]
HAND19 = dict(facts=3, HT=(0, 3, 0, 0, 0, 0), O=(0, 3, 0, 0, 0, 0), G=(0, 1, 0, 0, 0, 0, 2), OG=(0, 1, 0, 0, 0, 0, 2),
              stopped_g=(0, 2, 0, 0, 0, 0), stopped_og=(0, 2, 0, 0, 0, 0), numcol=0, w1_diff=(0,) * 7, number_only=0, move={("U", "U"): 3})
#: 場面 20(鍵の端): 段 OG の番号の列を使う fact の比べ先の鍵 (h, th, td) の端。今年の表(頭乙 2 行)の鍵 (見出しヌ, 表 0, td 1) の集まりは {頭甲} だけ。
#: 頭乙の印は前の年に、th だけ違う鍵(a の表 1)・td だけ違う鍵(b)・見出し h だけ違う鍵(c)で在る。鍵のどれか 1 つを外すと止められない。段 G は表 HT の側(行の字が違う行の印は混ざらない)で頭乙を止める。頭甲の 1 行は通る
PRIOR20 = [("a_ixbrl.htm", head(u"見出しヌ") + table([row(u"頭甲 1"), row(u"科目P", F("w", NO(7)))]) + table([row(u"頭乙 1"), row(u"科目S", F("w", NO(7)))])),
           ("b_ixbrl.htm", head(u"見出しヌ") + table([row(u"頭乙 1"), row(u"科目R", u"－", F("w", NO(7)))])),
           ("c_ixbrl.htm", head(u"見出しネ") + table([row(u"頭乙 1"), row(u"科目R", F("w", NO(7)))]))]
CUR20 = [("t_ixbrl.htm", head(u"見出しヌ") + table([row(u"頭乙 9"), row(u"科目P", F("w", NO(1))), row(u"科目P", F("w", NO(2)))])),
         ("u_ixbrl.htm", head(u"見出しヌ") + table([row(u"頭甲 9"), row(u"科目P", F("w", NO(1)))]))]
HAND20 = dict(facts=3, HT=(0, 0, 0, 3, 0, 0), O=(0, 3, 0, 0, 0, 0), G=(0, 0, 0, 1, 0, 0, 2), OG=(0, 1, 0, 0, 0, 0, 2),
              stopped_g=(0, 0, 0, 2, 0, 0), stopped_og=(0, 2, 0, 0, 0, 0), numcol=3, w1_diff=(0, 3, 0, 0, 0, 0, 0), number_only=3, move={("W1", "U"): 3})
#: 場面 21(比べは完全一致): 今年の表の頭の印が、前の年の印の一部(頭丁 ⊂ 頭丁丁)・前の年の印を含む(頭丁丁丁 ⊃ 頭丁丁)だけのとき、止める。番号の列を使う行(頭戊・頭戊戊戊 と 頭戊戊)も同じ。部分一致で比べると通る
PRIOR21 = [("a_ixbrl.htm", head(u"見出しテ") + table([row(u"頭丁丁 1"), row(u"科目P", F("p1"))])),
           ("b_ixbrl.htm", head(u"見出しト") + table([row(u"頭戊戊 1"), row(u"科目P", F("w", NO(7)))]))]
CUR21 = [("t_ixbrl.htm", head(u"見出しテ") + table([row(u"頭丁 9"), row(u"科目P", F("p1"))])),
         ("u_ixbrl.htm", head(u"見出しテ") + table([row(u"頭丁丁丁 9"), row(u"科目P", F("p1"))])),
         ("v_ixbrl.htm", head(u"見出しト") + table([row(u"頭戊 9"), row(u"科目P", F("w", NO(1)))])),
         ("x_ixbrl.htm", head(u"見出しト") + table([row(u"頭戊戊戊 9"), row(u"科目P", F("w", NO(1))), row(u"科目P", F("w", NO(2)))]))]
HAND21 = dict(facts=5, HT=(0, 2, 0, 3, 0, 0), O=(0, 5, 0, 0, 0, 0), G=(0, 0, 0, 0, 0, 0, 5), OG=(0, 0, 0, 0, 0, 0, 5),
              stopped_g=(0, 2, 0, 3, 0, 0), stopped_og=(0, 5, 0, 0, 0, 0), numcol=3, w1_diff=(0, 3, 0, 0, 0, 0, 0), number_only=3, move={("U", "U"): 2, ("W1", "U"): 3})
#: 場面 22(5 回目の監査の穴: nil の fact。封 §2-4 と便 XZ0 の封のとおり、空の欄(xsi:nil="true")も fact と数える): 表の頭は「最初に fact(空の欄を含む)を持つ行」より前。
#: 表 A: 頭の行 → 空の欄だけの科目行(今年と前の年で行の字が違う) → 空でない fact の科目行 2 つ。頭の印は空の欄の行で閉じるので「頭ヘ」同士で通る(U 2・空の欄は前の年に行の字が無く N 1)。
#:   空の欄の行を頭に入れると印が「頭ヘ|科目ホ」と「頭ヘ|科目ミ」で違い、U の 2 つが止まる。
#: 表 B: 前の年にも今年にも、同じ行の字・同じ属性の空の欄の行と空でない fact の行。どちらも U(前の年の表 HT・表 COL・印の集まりに空の欄を入れる・今年の類分けに空の欄を入れる。どれか 1 つでも落とすと数が変わる)。
#: 表 C: 前の年は番号つき文脈の空の欄 1 つ(unitRef なし)。今年は同じ行の字の空の欄 3 行(No1・No2・No3。unitRef なし)。全部が番号の列を使う(k=1〜3 に空の欄の行も数える)。段 HT は W1・U・W1、段 O は U 3。
PRIOR22 = [("a_ixbrl.htm", head(u"見出しハ") + table([row(u"頭ヘ 1"), row(u"科目ホ", NILF("a1")), row(u"科目マ", F("a2"))])
            + head(u"見出しヒ") + table([row(u"頭ム 1"), row(u"科目メ", NILF("b1")), row(u"科目モ", F("b2"))])
            + head(u"見出しフ") + table([row(u"頭ヤ 1"), row(u"科目ユ", NILF("c1", NO(2), None))]))]
CUR22 = [("a_ixbrl.htm", head(u"見出しハ") + table([row(u"頭ヘ 9"), row(u"科目ミ", NILF("a1"))] + rows_of(u"科目マ", 2, F("a2")))
         + head(u"見出しヒ") + table([row(u"頭ム 9"), row(u"科目メ", NILF("b1")), row(u"科目モ", F("b2"))])
         + head(u"見出しフ") + table([row(u"頭ヤ 9"), row(u"科目ユ", NILF("c1", NO(1), None)), row(u"科目ユ", NILF("c1", NO(2), None)), row(u"科目ユ", NILF("c1", NO(3), None))]))]
HAND22 = dict(facts=8, HT=(0, 5, 0, 2, 0, 1), O=(0, 7, 0, 0, 0, 1), G=(0, 5, 0, 2, 0, 1, 0), OG=(0, 7, 0, 0, 0, 1, 0),
              stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=3, w1_diff=(0, 2, 0, 0, 0, 0, 0), number_only=2, move={("N", "N"): 1, ("U", "U"): 5, ("W1", "U"): 2})
#: 場面 23(6 回目の監査の穴 Q4・R3): 同じ見出しの表が 2 つ(表 0 = th 0・表 1 = th 1)。表 0 の番号の列は td 1 だけ(形 Row・頭「頭ア」)・表 1 の番号の列は td 1 と td 2(形 No・頭「頭イ」)。
#: 表 1 の td 2 の鍵 (見出し, th 1, td 2) は表 COL に在るが、th を 0 にした鍵 (見出し, 0, td 2) は無い(番号の列を使うかが変わる: 段 O の W1 が U になる)。
#: 段 OG の比べ先の集まり SIGC は鍵の th ごとに違う(表 0 = {頭ア}・表 1 = {頭イ})ので、th を 0 にして引くと表 1 の fact が全部止まる(S 4)。今年の表 1 は 2 行(k=1・2)
PRIOR23 = [("a_ixbrl.htm", head(u"見出しノ")
            + table([row(u"頭ア 1"), row(u"科目J", F("g1", u"C_Row2Member"))])
            + table([row(u"頭イ 1"), row(u"科目J", F("g1", NO(2)), F("g2", NO(2)))]))]
CUR23 = [("a_ixbrl.htm", head(u"見出しノ")
          + table([row(u"頭ア 9"), row(u"科目J", F("g1", u"C_Row1Member"))])
          + table([row(u"頭イ 9"), row(u"科目J", F("g1", NO(1)), F("g2", NO(1))), row(u"科目J", F("g1", NO(2)), F("g2", NO(2)))]))]
HAND23 = dict(facts=5, HT=(0, 2, 0, 3, 0, 0), O=(0, 5, 0, 0, 0, 0), G=(0, 2, 0, 3, 0, 0, 0), OG=(0, 5, 0, 0, 0, 0, 0),
              stopped_g=(0,) * 6, stopped_og=(0,) * 6, numcol=5, w1_diff=(0, 3, 0, 0, 0, 0, 0), number_only=3, move={("W1", "U"): 3, ("U", "U"): 2})
EXTRA_SCENARIOS = ((u"場面 6", CUR6, PRIOR6, HAND6), (u"場面 7", CUR7, PRIOR7, HAND7), (u"場面 8", CUR8, PRIOR8, HAND8), (u"場面 9", CUR9, PRIOR9, HAND9), (u"場面 10", CUR10, PRIOR10, HAND10), (u"場面 11", CUR11, PRIOR11, HAND11), (u"場面 12", CUR12, PRIOR12, HAND12), (u"場面 13", CUR13, PRIOR13, HAND13), (u"場面 14", CUR14, PRIOR14, HAND14), (u"場面 15", CUR15, PRIOR15, HAND15), (u"場面 16", CUR16, PRIOR16, HAND16), (u"場面 17", CUR17, PRIOR17, HAND17), (u"場面 18", CUR18, PRIOR18, HAND18), (u"場面 19", CUR19, PRIOR19, HAND19), (u"場面 20", CUR20, PRIOR20, HAND20), (u"場面 21", CUR21, PRIOR21, HAND21), (u"場面 22", CUR22, PRIOR22, HAND22), (u"場面 23", CUR23, PRIOR23, HAND23))

SCENARIOS = ((u"場面 1", CUR1, PRIOR1, HAND1), (u"場面 2", CUR2, PRIOR2, HAND2), (u"場面 3", CUR3, PRIOR3, HAND3), (u"場面 4", CUR4, PRIOR4, HAND4), (u"場面 5", CUR5, PRIOR5, HAND5))


def tup(d, keys):
    return tuple(d[k] for k in keys)


def acc_hand(acc):
    st = acc["stages"]
    return dict(facts=acc["facts"], HT=tup(st["HT"], CLS), O=tup(st["O"], CLS), G=tup(st["G"], CLS_S), OG=tup(st["OG"], CLS_S),
                stopped_g=tup(acc["stopped_g"], CLS), stopped_og=tup(acc["stopped_og"], CLS), numcol=acc["numcol"],
                w1_diff=tuple(acc["w1_diff"].values()), number_only=acc["w1_number_only"])


def move_of(acc):
    return dict(((a, b), v) for a, r in acc["move"].items() for b, v in r.items() if v)


# ---- 組の e2e(6 本の今年の側の書類。6 本目は前の年の側に相手が居ない)
CUR_STEMS = ["S1ZZ0001", "S1ZZ0002", "S1ZZ0003", "S1ZZ0004", "S1ZZ0005", "S1ZZ0006"]
CODES = {"S1ZZ0001": u"E99001", "S1ZZ0002": u"E99002", "S1ZZ0003": u"E99003", "S1ZZ0004": u"E99004", "S1ZZ0005": u"E99005", "S1ZZ0006": u"E99006"}
PRV = {"E99001": "S1ZP0005", "E99002": "S1ZP0004", "E99003": "S1ZP0003", "E99004": "S1ZP0002", "E99005": "S1ZP0001"}
PRV_STEMS = ["S1ZP0005", "S1ZP0004", "S1ZP0003", "S1ZP0002", "S1ZP0001"]
CUR_END, PRV_END = "2026-03-31", "2025-03-31"
DOC_CUR = {"S1ZZ0001": CUR2, "S1ZZ0002": CUR1, "S1ZZ0003": CUR5, "S1ZZ0004": CUR3, "S1ZZ0005": CUR4, "S1ZZ0006": [("a_ixbrl.htm", table([row(u"科目ア", F("01"))]))]}
DOC_PRIOR = {"E99001": PRIOR2, "E99002": PRIOR1, "E99003": PRIOR5, "E99004": PRIOR3, "E99005": PRIOR4}
#: 番号 1・2・3・4・5 の組。番号 3 以下の 3 組(場面 2・1・5)が「3 組」・番号 4 以上の 2 組(場面 3・4)が「60 組」
SUM60 = 9 + 28
SUM3 = 15 + 21 + 3


def fname(code, end, suffix=u".xsd"):
    return u"XBRL/PublicDoc/jpcrp030000-asr-001_%s-000_%s_01_%s%s" % (code, end, end[:4] + u"-06-30", suffix)


def make_doc_zip(path, code, end, texts):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(fname(code, end), b"<schema/>")
        for n, t in texts:
            z.writestr(fname(code, end, suffix=u"_" + n), t.encode("utf-8"))
        decoy = head(u"見出しア") + table([row(u"科目甲", F("99"))] * 3)
        z.writestr(u"XBRL/AuditDoc/0000_audit_ixbrl.htm", decoy.encode("utf-8"))
        z.writestr(fname(code, end, suffix=u"_other.htm"), decoy.encode("utf-8"))


def make_dirs(d):
    docs, prior = os.path.join(d, "docs"), os.path.join(d, "prior")
    os.makedirs(docs)
    os.makedirs(prior)
    for stem in CUR_STEMS:
        make_doc_zip(os.path.join(docs, stem + ".zip"), CODES[stem], CUR_END, DOC_CUR[stem])
    for code, stem in sorted(PRV.items()):
        make_doc_zip(os.path.join(prior, stem + ".zip"), code, PRV_END, DOC_PRIOR[code])
    return docs, prior


def fake_draft(docs, prior):
    u"""作り物の置き場から、本物の便 XZ0 の関数で、便 XZ0 の記録(の形)を作る。"""
    rec, _s = MS.Z.build_record(docs, prior, 6, 5)
    return rec


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XZ1-1", (1.0,)), ("XZ1-2", (72.0,)), ("XZ1-3", (300, 50)), ("XZ1-4", (400,)), ("XZ1-5", (1.0, 8.0)), ("XZ1-6", (50,)), ("XZ1-7", (10, 45)), ("XZ1-8", (20,))])
SEAL_BOUND_TEXT = {
    "XZ1-1": u"段 OG の類 W1 は fact の 1.0% 以下", "XZ1-2": u"段 OG の類 U は fact の 72.0% 以上",
    "XZ1-3": u"段 O の W1 は段 HT の W1 より 300 以上少なく、段 HT で W1 でも W2 でもなかった fact が段 O で W1 になった数は 50 以下",
    "XZ1-4": u"段 O の U は段 HT の U より 400 以上多い", "XZ1-5": u"段 G が止めた段 HT の U は、fact の 1.0% 以上 8.0% 以下",
    "XZ1-6": u"段 G が止めた段 HT の W1 は、段 HT の W1 の 50% 以上", "XZ1-7": u"段 HT の W1 のうち「番号だけの違い」は 10% 以上 45% 以下",
    "XZ1-8": u"段 OG の W1 が 0 の組は 20 組以上"}


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL:
        out.append(u"封の commit・path が門と違う")
    for rel in (SCRIPT_REL, RECORD_REL, GATE_REL):
        if rel not in seal:
            out.append(u"封に path が無い: %s" % rel)
    if ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL or ms.DRAFT_RECORD_REL != DRAFT_RECORD_REL:
        out.append(u"script・記録の path が封・門と違う")
    want_prior = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-prior-2026-11-02")
    if ms.PRIOR_DIR != want_prior or ms.PRIOR_DIR == ms.DOCS_DIR:
        out.append(u"前の年の側の置き場が便 XZ0 の字(edinet-prior-2026-11-02。今年の側の edinet/ でない)と違う")
    if ms.PAIRS_WANT != 63 or u"組の数が 63 でなければ script は止まる" not in seal:
        out.append(u"組の数 63 が封と違う")
    if ms.DOCS_WANT != 67:
        out.append(u"今年の側の本数 67 が便 XZ0 の字と違う")
    if ms.SUM60_WANT != 61100 or u"61100" not in seal or u"番号 4〜63 の 60 組" not in seal:
        out.append(u"60 組の fact の合計 61100 が封と違う")
    if ms.SEEN_MAX_NO != 3 or u"(便 XZ0 の記録の番号 1・2・3)" not in seal:
        out.append(u"見た 3 組の分け(番号 3 以下)が封と違う")
    if tuple(ms.CLASSES) != CLS or tuple(ms.STAGES4) != (u"HT", u"O", u"G", u"OG") or ms.STOP_CLASS != u"S":
        out.append(u"類・段の名が封と違う")
    for w in (u"**番号つきの文脈の形**", u"**前の年の表 COL**", u"**段 O(行の順で番号を振り直す)**", u"**番号の列を使う fact**", u"**行の番号 k**", u"**表の頭の印**", u"**段 G(表の頭の字が違えば止める)**",
              u"類 **S(止めた)**", u"**段 OG**", u"**W1 の中身**(段 HT)", u"`^(No|Row)[0-9]+[A-Za-z]*Member$`", u"T が空でない行だけ", u"X と N はそのまま", u"最初に数の fact を持つ行より前に在る行"):
        if w not in seal:
            out.append(u"封に字が無い: %s" % w)
    if tuple(ms.ATTRS3) != (u"name", u"contextRef", u"unitRef"):
        out.append(u"束 3 の属性が違う")
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS):
        out.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [ln for ln in seal.splitlines() if re.match(r"^\| %s(?!\d)" % re.escape(k), ln)]
        if len(row_) != 1 or t not in row_[0]:
            out.append(u"封の予測の行の字が違う: %s" % k)
    if ms.FLAG_S_OVER != 30 or u"S が fact の 30% を超えた" not in seal or u"段 OG の W1 が 60 組の全部で 0" not in seal or u"番号の列を使った fact が 60 組で 0" not in seal:
        out.append(u"先に疑う旗の 3 つ(OG の W1・S の 30%・番号の列)が封と違う")
    if u"**docID・会社の名・EDINET コード・期末の日付・file の名・行の字・見出しの字・表の頭の印の字・要素の名・文脈の名・形の字は書かない。**" not in seal:
        out.append(u"封の記録に書かないものの字が違う")
    if u"材料の並びの sha256" not in seal or u"engine の指紋" not in seal:
        out.append(u"封の記録の項目が違う")
    sec7 = seal.split(u"## §7", 1)[-1]
    want = (u"規則と守りは 3 組を見て作った", u"番号つきのメンバーの形は `No`・`Row` で始まる 2 通りだけ", u"段 O の行の番号は「今年の表の行の順が、今年の正しい番号の順」という仮定",
            u"表の頭の印は、最初に fact を持つ行より前の行の字だけ", u"便 XZ0 の限界はそのまま", u"「XBRL を作れる」")
    want_script = (u"規則と守りは 3 組を見て作った", u"番号つきのメンバーの形は No・Row で始まる 2 通りだけ", u"段 O の行の番号は「今年の表の行の順が、今年の正しい番号の順」という仮定",
                   u"表の頭の印は、最初に fact を持つ行より前の行の字だけ", u"便 XZ0 の限界はそのまま", u"「XBRL を作れる」")
    if len([ln for ln in sec7.splitlines() if ln.startswith(u"- ")]) != 6:
        out.append(u"封 §7 の限界の行が 6 行でない")
    if len(ms.LIMITS) != 6 or any(p not in sec7 for p in want) or any(p not in u"".join(ms.LIMITS) for p in want_script):
        out.append(u"限界の 6 行が封 §7 と違う")
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


# ======================================================================== 2. 形・印・表 COL・数の部品
SHAPE_CASES = ((None, None), (u"", None), (u"C", None), (u"C_No12Member", u"C_No#Member"), (u"C_Row3AMember", u"C_Row#AMember"), (u"C_X_No1Member", u"C_X_No#Member"),
               (u"C_No1Member_Other", u"C_No#Member_Other"), (u"C_No1Member_No2Member", None), (u"No1Member_C", None), (u"C_NoXMember", None), (u"C_no1Member", None),
               (u"C_No1Members", None), (u"C_Row1Member_Other_Row2Member", None), (u"No1Member", None))


def pure_problems(ms=None):
    ms = ms or MS
    out = []
    for ctx, want in SHAPE_CASES:
        if ms.shape_of(ctx) != want:
            out.append(u"形が違う: %r -> %r(正しくは %r)" % (ctx, ms.shape_of(ctx), want))
    if ms.with_number(u"C_No#Member", 12) != u"C_No12Member" or ms.with_number(u"C_Row#AMember", 3) != u"C_Row3AMember" or ms.with_number(u"C_No#Member_X", 7) != u"C_No7Member_X":
        out.append(u"形の # を k の字にする置き換えが違う")
    got = ms.head_mark([u"<tr><td>期ア 2024年</td></tr>", u"<tr><td><b>単位 ア</b></td></tr>", u"<tr><td></td></tr>", u"<tr><td>ＡＢ　１２</td></tr>"])
    if got != u"期ア年|単位ア||AB":
        out.append(u"表の頭の印が違う(タグ・空白・数字(全角を含む)を除き ``|`` でつなぐ): %r" % got)
    if ms.head_mark([]) != u"":
        out.append(u"頭の行が無い表の印が空の字でない")
    a, b = (u"n", u"c_No1Member", u"u"), (u"n", u"c_No2Member", u"u")
    for t, c, want in ((a, b, True), (a, a, False), (a, (u"m", b[1], u"u"), False), (a, (u"n", b[1], u"v"), False), (a, (u"n", u"d_No2Member", u"u"), False), (a, (u"n", u"ctxA", u"u"), False),
                       ((u"n", u"ctxA", u"u"), b, False), ((u"n", None, u"u"), (u"n", None, u"u"), False), ((u"n", u"ctxA", u"u"), (u"n", u"ctxB", u"u"), False)):
        if ms.number_only(t, c) != want:
            out.append(u"番号だけの違いの判定が違う: %s %s -> %s" % (t, c, ms.number_only(t, c)))
    for t, c, want in (((u"n", u"c", u"u"), (u"n", u"c", u"u"), u""), ((u"m", u"c", u"u"), (u"n", u"c", u"u"), u"name"), ((u"n", u"d", u"u"), (u"n", u"c", u"u"), u"contextRef"),
                       ((u"n", u"c", u"v"), (u"n", u"c", u"u"), u"unitRef"), ((u"m", u"d", u"u"), (u"n", u"c", u"u"), u"name+contextRef"), ((u"m", u"c", u"v"), (u"n", u"c", u"u"), u"name+unitRef"),
                       ((u"n", u"d", u"v"), (u"n", u"c", u"u"), u"contextRef+unitRef"), ((u"m", u"d", u"v"), (u"n", u"c", u"u"), u"name+contextRef+unitRef")):
        if ms.diff_key(t, c) != want:
            out.append(u"違う属性の組が違う: %s %s -> %s" % (t, c, ms.diff_key(t, c)))
    if tuple(ms.DIFF_KEYS) != (u"name", u"contextRef", u"unitRef", u"name+contextRef", u"name+unitRef", u"contextRef+unitRef", u"name+contextRef+unitRef"):
        out.append(u"違う属性の 7 通りの並びが違う")
    return out


def rows_problems(ms=None):
    ms = ms or MS
    out = []
    # table_rows: file の昇順・表の識別は file の位置と表の通し番号・頭の印は最初の fact の行より前の行だけ
    texts = [("b_ixbrl.htm", head(u"見出しA") + table([row(u"頭A 1"), row(u"科目", F("01"))]) + table([row(u"科目", F("01")), row(u"後記 1")])),
             ("a_ixbrl.htm", table([row(u"頭B"), row(u"頭C"), row(u"科目甲", F("01")), row(u"後記"), row(u"科目乙", F("01"))]))]
    got = [(T, ser, mark) for _h, _th, T, _f, ser, mark in ms.table_rows(texts)]
    # 表の識別 = (file の位置, 行の始まりより前の ``<table`` の開きタグの数)
    want = [(u"頭B", (0, 1), u"頭B|頭C"), (u"頭C", (0, 1), u"頭B|頭C"), (u"科目甲", (0, 1), u"頭B|頭C"), (u"後記", (0, 1), u"頭B|頭C"), (u"科目乙", (0, 1), u"頭B|頭C"),
            (u"頭A1", (1, 1), u"頭A"), (u"科目", (1, 1), u"頭A"), (u"科目", (1, 2), u""), (u"後記1", (1, 2), u"")]
    if got != want:
        out.append(u"table_rows の (行の字・表の識別・頭の印) が違う: %s" % got)
    rows = ms.table_rows([("a_ixbrl.htm", table([row(u"頭部"), row(u"後記")]))])
    if [r[5] for r in rows] != [u"頭部|後記", u"頭部|後記"]:
        out.append(u"fact を持つ行が無い表は、全部の行が頭になっていない: %s" % [r[5] for r in rows])
    rows = ms.table_rows([("a_ixbrl.htm", table([row(u"", F("01")), row(u"後記")]))])
    if rows[0][5] != u"" or rows[1][5] != u"":
        out.append(u"T が空でも fact を持つ行が最初の fact の行になっていない: %s" % [r[5] for r in rows])
    # 前の年の側の表 COL・頭の印の集まり
    at = lambda n, c: {"name": n, "contextRef": c, "unitRef": "u"}                       # noqa: E731
    prv = [("H", 0, u"T1", [(2, at("n1", "c_No1Member")), (3, at("n2", "c"))], (0, 0), u"m1"),
           ("H", 0, u"", [(2, at("n9", "c_No9Member"))], (0, 0), u"m2"),
           ("H", 0, u"T2", [(2, at("n1", "c_No2Member"))], (0, 0), u"m3"),
           ("H", 1, u"T3", [(2, at("n5", "c_Plain"))], (0, 1), u"m4")]
    sig, col, sigc = ms.build_col(prv)
    if sig != {("H", 0, u"T1", 2): {u"m1"}, ("H", 0, u"T1", 3): {u"m1"}, ("H", 0, u"T2", 2): {u"m3"}, ("H", 1, u"T3", 2): {u"m4"}}:
        out.append(u"表 HT の頭の印の集まりが違う(T が空の行は入れない): %s" % sig)
    if col != {("H", 0, 2): {(u"n1", u"c_No#Member", u"u")}} or sigc != {("H", 0, 2): {u"m1", u"m3"}}:
        out.append(u"表 COL・表 COL の頭の印の集まりが違う(形の在る文脈だけ・T が空の行は入れない): %s %s" % (col, sigc))
    sh = (u"n", u"c_No1Member", u"u")
    pl = (u"n", u"c", u"u")
    for cands, key, want in ((set(), ("H", 0, 2), True), ({sh}, ("H", 0, 2), True), ({pl}, ("H", 0, 2), False), ({pl, sh}, ("H", 0, 2), True), (set(), ("H", 0, 3), False), ({sh}, ("H", 0, 3), False),
                             (set(), ("H", 1, 2), False)):
        if ms.uses_number_col(cands, key, col) != want:
            out.append(u"番号の列を使う条件が違う: %s %s -> %s" % (cands, key, ms.uses_number_col(cands, key, col)))
    # 行の切り方が engine の _TR_RE の全部と 1 対 1 でなければ止まる
    real = ms.Z.read_rows
    try:
        ms.Z.read_rows = lambda text: (real(text)[0][:-1], 0)
        if not stops(ms, ms.table_rows, [("a_ixbrl.htm", table([row(u"科目ア", F("01")), row(u"科目イ", F("02"))]))]):
            out.append(u"read_rows の行が engine の _TR_RE の全部と 1 対 1 でないのに止まらない")
    finally:
        ms.Z.read_rows = real
    return out


# ======================================================================== 3. 組 1 つの手の数
def count_problems(ms=None):
    ms = ms or MS
    out = []
    for name, cur, prior, hand in SCENARIOS + EXTRA_SCENARIOS:
        acc = ms.count_pair(cur, prior)
        got = acc_hand(acc)
        for k, w in hand.items():
            if k == "move":
                continue
            if got[k] != w:
                out.append(u"%s の数 %s が手で数えた値と違う: %s != %s" % (name, k, got[k], w))
        if "move" in hand and move_of(acc) != hand["move"]:
            out.append(u"%s の段の間の移りが手で数えた値と違う: %s" % (name, move_of(acc)))
        if "move" not in hand:
            # 手の移りを書かない場面は、対角(段 HT の類 = 段 O の類)の合計が段 HT の合計と合う形だけ
            if sum(v for v in move_of(acc).values()) != acc["facts"]:
                out.append(u"%s の段の間の移りの合計が fact の数と違う" % name)
    # 前の年の側と今年の側を入れ替えると別の数になる(前の年の側として今年の書類を読んでいない)
    if acc_hand(ms.count_pair(CUR2, PRIOR2))["O"] == acc_hand(ms.count_pair(PRIOR2, CUR2))["O"]:
        out.append(u"今年の側と前の年の側を入れ替えても数が変わらない")
    # 前の年の側へ今年の書類そのものを渡すと、番号の列を使う fact が 1 つも W1 にならず、頭は全部同じ(S は 0)
    same = ms.count_pair(CUR2, CUR2)
    if same["stages"]["OG"]["S"] or same["stages"]["G"]["S"]:
        out.append(u"同じ書類を両側に渡すと止める fact が出る(頭が同じなのに)")
    return out


def hand_shape_problems():
    u"""手で決めた値が足し算と合い、類・止めた数が互いに違う(近くの数と同じにしない)。"""
    out = []
    for name, _c, _p, h in SCENARIOS + EXTRA_SCENARIOS:
        for s in ("HT", "O"):
            if sum(h[s]) != h["facts"]:
                out.append(u"%s %s の合計が fact の数と違う" % (name, s))
        for s in ("G", "OG"):
            if sum(h[s]) != h["facts"]:
                out.append(u"%s %s の合計が fact の数と違う" % (name, s))
        if h["numcol"] > h["facts"]:
            out.append(u"%s の番号の列の数が fact より多い" % name)
        if sum(h["stopped_g"]) != h["G"][6] or sum(h["stopped_og"]) != h["OG"][6]:
            out.append(u"%s の止めた数が S と違う" % name)
        if sum(h["w1_diff"]) != h["HT"][3]:
            out.append(u"%s の W1 の中身の合計が W1 と違う" % name)
    if len(set(HAND1["HT"])) != 6 or len(set(HAND4["w1_diff"])) != 7 or len(set(HAND2["HT"][:2] + HAND2["HT"][3:4] + HAND2["HT"][5:])) != 4:
        out.append(u"類・属性の数が互いに違わない")
    return out


JUDGE_ACC = {"facts": 1000, "HT": (10, 700, 50, 100, 20, 120), "O": (10, 800, 60, 40, 20, 70), "OG": (10, 750, 60, 5, 20, 70, 85),
             "stopped_g": (0, 40, 0, 60, 0, 0), "stopped_og": (0, 30, 0, 0, 0, 0), "w1_number_only": 25,
             "move": {("U", "W1"): 7, ("N", "W1"): 3, ("W1", "W1"): 30, ("W2", "W1"): 1}}


def judge_problems(ms=None):
    ms = ms or MS
    out = []
    t = ms.new_acc()
    t["facts"] = JUDGE_ACC["facts"]
    for s, v in (("HT", JUDGE_ACC["HT"]), ("O", JUDGE_ACC["O"]), ("OG", JUDGE_ACC["OG"])):
        for c, n in zip(CLS_S, v):
            t["stages"][s][c] = n
    for c, n in zip(CLS, JUDGE_ACC["stopped_g"]):
        t["stopped_g"][c] = n
    for c, n in zip(CLS, JUDGE_ACC["stopped_og"]):
        t["stopped_og"][c] = n
    t["w1_number_only"] = JUDGE_ACC["w1_number_only"]
    for (a, b), n in JUDGE_ACC["move"].items():
        t["move"][a][b] = n
    j = ms.judgment_numbers(t)
    look = lambda prefix: [v for k, v in j.items() if k.startswith(prefix)]               # noqa: E731
    for prefix, w in ((u"XZ1-1 段 OG の類 W1 / 行", 0.5), (u"XZ1-1 段 OG の類 W1 / 通", 0.7), (u"XZ1-2", 75.0), (u"XZ1-5", 4.0), (u"XZ1-6", 60.0), (u"XZ1-7", 25.0)):
        hit = look(prefix)
        if len(hit) != 1 or hit[0][u"%"] != w:
            out.append(u"判定の数 %s が手で数えた値 %s と違う: %s" % (prefix, w, hit))
    x3 = look(u"XZ1-3")[0]
    if tuple(x3.values()) != (100, 40, 60, 10):
        out.append(u"XZ1-3 の数が違う(段 HT で W1 でも W2 でもなかったものだけ): %s" % dict(x3))
    x4 = look(u"XZ1-4")[0]
    if tuple(x4.values()) != (700, 800, 100):
        out.append(u"XZ1-4 の数が違う: %s" % dict(x4))
    r = look(u"読み方の 4 区分")[0]
    if tuple(r.values()) != (755, 85, 80, 80, 30, 35.3):
        out.append(u"読み方の 4 区分が違う: %s" % dict(r))
    # 足し合わせ
    a1, a2 = ms.new_acc(), ms.new_acc()
    a1["facts"], a2["facts"] = 3, 4
    a1["stages"]["G"]["S"], a2["stages"]["G"]["S"] = 1, 5
    a1["move"]["N"]["U"], a2["move"]["N"]["U"] = 2, 7
    tot = ms.totals([a1, a2])
    if (tot["facts"], tot["stages"]["G"]["S"], tot["move"]["N"]["U"]) != (7, 6, 9) or a1["facts"] != 3:
        out.append(u"totals が足し合わせでない(か元を変えた)")
    return out


# ======================================================================== 4. 記録・e2e
def build_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    with Temp() as d:
        docs, prior = make_dirs(d)
        draft = fake_draft(docs, prior)
        rec, secret = ms.build_record(docs, prior, 6, 5, draft, SUM60)
        mat = rec[u"材料"]
        if (mat[u"今年の側の書類の本数"], mat[u"組の数"], mat[u"除いた今年の書類の数"], list(mat.values())[5], list(mat.values())[6]) != (6, 5, 1, 2, 3):
            out.append(u"材料の数が違う(60 組の組の数・3 組の組の数を含む): %s" % dict(mat))
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
        if rec[u"限界"] != list(ms.LIMITS) or len(rec[u"限界"]) != 6:
            out.append(u"記録の限界が 6 行でない")
        if [r[u"番号"] for r in rec[u"書類"]] != [1, 2, 3, 4, 5]:
            out.append(u"書類の番号が違う(除いた書類の番号は飛ぶ): %s" % [r[u"番号"] for r in rec[u"書類"]])
        keyed = lambda prefix: [v for k, v in rec.items() if k.startswith(prefix)][0]          # noqa: E731
        t60, t3, t63 = keyed(u"集計 60 組"), keyed(u"集計 3 組"), keyed(u"集計 63 組")
        st = lambda t, s: tuple(t[u"段ごとの類別"][s].values())                                    # noqa: E731
        want = {u"60": (0, 3, 0, 30, 0, 4), u"3": (2, 11, 2, 5, 4, 15)}
        if t60[u"行の中の数の fact の数"] != SUM60 or t3[u"行の中の数の fact の数"] != SUM3 or t63[u"行の中の数の fact の数"] != SUM60 + SUM3:
            out.append(u"60 組・3 組・63 組の fact の数が違う: %s %s %s" % (t60[u"行の中の数の fact の数"], t3[u"行の中の数の fact の数"], t63[u"行の中の数の fact の数"]))
        if st(t60, "HT") != want[u"60"] or st(t3, "HT") != want[u"3"]:
            out.append(u"60 組と 3 組の分けが違う(番号 3 以下が 3 組): 60=%s 3=%s" % (st(t60, "HT"), st(t3, "HT")))
        if st(t60, "OG") != (0, 4, 0, 28, 0, 0, 5):
            out.append(u"60 組の段 OG の合計が違う: %s" % (st(t60, "OG"),))
        if tuple(a + b for a, b in zip(st(t60, "HT"), st(t3, "HT"))) != st(t63, "HT"):
            out.append(u"63 組の合計が 60 組と 3 組の和でない")
        d1 = rec[u"書類"][0]
        if st(d1, "HT") != HAND2["HT"] or st(d1, "O") != HAND2["O"] or d1[u"番号の列を使った fact の数"] != 11 or d1[u"段 HT の W1 のうち番号だけの違いの数"] != 2:
            out.append(u"記録の書類 1 が手で数えた値(場面 2)と違う: %s" % dict(d1))
        mv = d1[u"段 HT の類 → 段 O の類(行が段 HT の類・列が段 O の類)"]
        if mv[u"N"][u"U"] != 4 or mv[u"N"][u"W1"] != 2 or mv[u"U"][u"U"] != 3 or mv[u"U"][u"W1"] != 1 or mv[u"W1"][u"U"] != 2 or mv[u"X"][u"X"] != 1:
            out.append(u"記録の段の間の移りが違う: %s" % dict(mv))
        pv = [v for k, v in rec.items() if k.startswith(u"予測の判定に要る数")][0]
        x8 = [v for k, v in pv.items() if k.startswith(u"XZ1-8")][0]
        if (x8[u"W1 が 0 の組"], x8[u"60 組の組の数"]) != (1, 2):
            out.append(u"XZ1-8 の数が違う(60 組のうち段 OG の W1 が 0 の組): %s" % dict(x8))
        fl = [v for k, v in rec.items() if k.startswith(u"先に自分の欠陥を疑う旗")][0]
        fv = list(fl.values())
        if [f[u"分母"] for f in fv[1:3]] != [SUM60, SUM60] or [f[u"fact"] for f in fv[1:3]] != [5, 5] or fv[3][u"fact"] != 7 or (fv[0][u"W1 が 0 の組の数"], fv[0][u"60 組の組の数"]) != (1, 2) \
                or any(f[u"旗"] for f in fv):
            out.append(u"旗の数が違う(60 組だけの分母・S は段 G 5・段 OG 5・番号の列 7): %s" % [dict(f) for f in fv])
        x2 = [v for k, v in pv.items() if k.startswith(u"XZ1-2")][0]
        if (x2[u"fact"], x2[u"分母"], x2[u"%"]) != (4, SUM60, 10.8):
            out.append(u"XZ1-2 の数が違う(60 組だけ。3 組を混ぜない): %s" % dict(x2))
        text = ms.record_text(rec, secret)
        for leak in CUR_STEMS + PRV_STEMS + [u"E99", u"S1ZZ", u"S1ZP", u"Item", u"ctxA", u"unitJ", u"科目", u"見出し", u"ア頭", u"オ頭", u"順表頭", u"役員", u"2026-03", u"2025-03", u"_ixbrl", u"fk:", u"C_No"]:
            if leak in text:
                out.append(u"記録に材料の字が在る: %s" % leak)
        # 便 XZ0 の記録と段 HT の類の数が 1 つでも違えば止まる(1 つずつ変える)
        for what, mutate_draft in ((u"U の数", lambda r: r[u"書類"][2][u"束と段ごとの類別"][u"束 3"]["HT"].__setitem__("U", r[u"書類"][2][u"束と段ごとの類別"][u"束 3"]["HT"]["U"] + 1)),
                                   (u"N の数", lambda r: r[u"書類"][0][u"束と段ごとの類別"][u"束 3"]["HT"].__setitem__("N", r[u"書類"][0][u"束と段ごとの類別"][u"束 3"]["HT"]["N"] - 1)),
                                   (u"最後の組の W1", lambda r: r[u"書類"][3][u"束と段ごとの類別"][u"束 3"]["HT"].__setitem__("W1", 0)),
                                   (u"fact の数", lambda r: r[u"書類"][1].__setitem__(u"行の中の数の fact の数", 99))):
            bad = json.loads(json.dumps(draft), object_pairs_hook=od)
            mutate_draft(bad)
            if not stops(ms, ms.build_record, docs, prior, 6, 5, bad, SUM60):
                out.append(u"便 XZ0 の記録と段 HT の類の数が違うのに止まらない(%s)" % what)
        short = json.loads(json.dumps(draft), object_pairs_hook=od)
        short[u"書類"] = short[u"書類"][:3]
        if not stops(ms, ms.build_record, docs, prior, 6, 5, short, SUM60):
            out.append(u"便 XZ0 の記録に同じ番号が無いのに止まらない")
        if not stops(ms, ms.build_record, docs, prior, 6, 5, draft, SUM60 + 1) or not stops(ms, ms.build_record, docs, prior, 6, 5, draft, SUM60 - 1):
            out.append(u"60 組の fact の合計が違うのに止まらない")
        if not stops(ms, ms.build_record, docs, prior, 6, 4, draft, SUM60):
            out.append(u"組の数が違うのに止まらない")
        rec2, _s2 = ms.build_record(docs, prior, 6, 5, None, None)
        if ms.dumps(rec2) != ms.dumps(rec):
            out.append(u"便 XZ0 の記録を照らさなくても数が同じになっていない(照らすだけの検査)")
    return out


def e2e_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    with Temp() as d:
        docs, prior = make_dirs(d)
        draft = fake_draft(docs, prior)
        kw = dict(docs=docs, prior=prior, want_docs=6, want_pairs=5, draft=draft, want_sum60=SUM60)
        rec_path = os.path.join(d, "rec", "r.json")
        lines = []
        before = sha_or_none(RECORD_REL)
        ms.run(root=d, out=rec_path, say=lines.append, **kw)
        if not os.path.isfile(rec_path) or lines != [u"-> r.json(組 5)"] or sha_or_none(RECORD_REL) != before:
            out.append(u"本番が記録を書かない・本物の記録を触った: %s" % lines)
        if not stops(ms, ms.run, root=d, out=rec_path, say=lambda *a: None, **kw):
            out.append(u"記録が既に在るのに run が止まらない")
        ms.check(root=d, rec_path=rec_path, say=lambda *a: None, **kw)
        text = io.open(rec_path, encoding="utf-8").read()
        bad = text.replace(u'"行の中の数の fact の数": 15', u'"行の中の数の fact の数": 16', 1)
        bp = os.path.join(d, "bad.json")
        with io.open(bp, "w", encoding="utf-8") as fh:
            fh.write(bad)
        if bad == text or not stops(ms, ms.check, rec_path=bp, say=lambda *a: None, **kw):
            out.append(u"数を変えた記録で --check が止まらない")
        if not stops(ms, ms.check, rec_path=os.path.join(d, "none.json"), say=lambda *a: None, **kw):
            out.append(u"記録が無いのに --check が止まらない")
        # 前の年の側の書類を替えると --check が止まる
        make_doc_zip(os.path.join(prior, "S1ZP0005.zip"), "E99001", PRV_END, CUR2)
        if not stops(ms, ms.check, rec_path=rec_path, say=lambda *a: None, **kw):
            out.append(u"前の年の側の書類を変えても --check が止まらない")
        # 便 XZ0 の記録が無ければ本番が止まる
        if not stops(ms, ms.run, root=d, out=os.path.join(d, "rec", "r2.json"), say=lambda *a: None, docs=docs, prior=prior, want_docs=6, want_pairs=5, want_sum60=SUM60):
            out.append(u"便 XZ0 の記録が無い(root に無い)のに run が止まらない")
    return out


def mini_flags(ms, curs, prior_texts):
    u"""作り物の書類 ``curs``(各書類の [(file 名, 字)])を同じ前の年の書類と組にして、先に疑う旗(4 つ・番号 0 以上を 60 組として)を返す。"""
    saved = ms.SEEN_MAX_NO
    ms.SEEN_MAX_NO = 0
    try:
        with Temp() as d:
            docs, prior = os.path.join(d, "docs"), os.path.join(d, "prior")
            os.makedirs(docs)
            os.makedirs(prior)
            for i, texts in enumerate(curs, 1):
                make_doc_zip(os.path.join(docs, "S1ZZ%04d.zip" % i), u"E9910%d" % i, CUR_END, texts)
                make_doc_zip(os.path.join(prior, "S1ZP%04d.zip" % i), u"E9910%d" % i, PRV_END, prior_texts)
            rec, _s = ms.build_record(docs, prior, len(curs), len(curs), None, None)
    finally:
        ms.SEEN_MAX_NO = saved
    return [f[u"旗"] for f in [v for k, v in rec.items() if k.startswith(u"先に自分の欠陥を疑う旗")][0].values()]


MINI_PRIOR = [("a_ixbrl.htm", head(u"見出しア") + table([row(u"頭 1"), row(u"科目ア", F("01")), row(u"科目ネ", F("11", NO(1)))]))]


def mini_cur(n_ok, n_w1, n_bad, n_badnum):
    u"""file a: 頭が同じ(止めない)ok 行と W1 行。file b: 頭が違う・同じ鍵の行 n_bad(U → S)・鍵が無く番号の列を使う行 n_badnum(段 O で U・段 OG で S)。"""
    a = head(u"見出しア") + table([row(u"頭 2")] + rows_of(u"科目ア", n_ok, F("01")) + rows_of(u"科目ア", n_w1, F("01", CB)))
    b = head(u"見出しア") + table([row(u"別 2")] + rows_of(u"科目ア", n_bad, F("01")) + [row(u"科目丙", F("11", NO(k))) for k in range(1, n_badnum + 1)])
    return [("a_ixbrl.htm", a), ("b_ixbrl.htm", b)]


#: [(ok, W1, bad, badnum) の書類の並び] → (旗 1: 段 OG の W1 が全部の書類で 0, 旗 2: 段 G の S が 30% 超, 旗 3: 段 OG の S が 30% 超, 旗 4: 番号の列を使った fact が 0)。境(ちょうど 30%)は含まない。
FLAG_CASES = (([(10, 0, 0, 0)], (True, False, False, True)), ([(8, 1, 0, 1)], (False, False, False, False)), ([(5, 0, 0, 1), (4, 1, 0, 1)], (False, False, False, False)),
              ([(6, 1, 3, 0)], (False, False, False, True)), ([(5, 1, 4, 0)], (False, True, True, True)), ([(5, 1, 0, 4)], (False, False, True, False)))


def flags_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    for docs, want in FLAG_CASES:
        got = tuple(mini_flags(ms, [mini_cur(*args) for args in docs], MINI_PRIOR))
        if got != want:
            out.append(u"旗が違う %s: %s != %s" % (docs, got, want))
    return out


def clean_problems(ms=None):
    ms = ms or MS
    out = []
    secret = (set([u"科目ア", u"頭"]), set([u"Item01"]), ["S1ZZ0001", "S1ZP0001"], set(["E99001"]), set([u"見出しア"]), set())
    for what, bad in ((u"docID の形", od([(u"x", u"S1ZZ9999")])), (u"EDINET コードの形", od([(u"x", u"E99991")])), (u"日付の形", od([(u"x", u"2026-03-31")])),
                      (u"禁止の欄", od([(u"docid", 1)])), (u"禁止の欄(名)", od([(u"name", 1)])), (u"今年の側の docID", od([(u"x", u"a S1ZZ0001 b")])),
                      (u"前の年の側の docID", od([(u"x", u"a S1ZP0001 b")])), (u"コード", od([(u"x", u"a E99001 b")])), (u"要素の名", od([(u"x", u"a Item01 b")])),
                      (u"行の字", od([(u"x", u"科目ア")])), (u"表の頭の印の字", od([(u"x", u"頭")])), (u"見出しの字", od([(u"x", u"見出しア")]))):
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
    return out


def secret_problems(ms=None):
    u"""本番の ``build_record`` が作る secret の配線と、``check()`` が secret を ``check_clean`` に渡していること。作り物の置き場だけ。"""
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    with Temp() as d:
        docs, prior = make_dirs(d)
        draft = fake_draft(docs, prior)
        kw = dict(docs=docs, prior=prior, want_docs=6, want_pairs=5, draft=draft, want_sum60=SUM60)
        rec, secret = ms.build_record(docs, prior, 6, 5, draft, SUM60)
        labels, elems, ids, ecodes, heads, inds = secret
        if sorted(ids) != sorted(CUR_STEMS + PRV_STEMS):
            out.append(u"secret の docID が今年の側と前の年の側の stem でない: %s" % (list(ids),))
        if not set([u"E99001", u"E99002", u"E99004", u"E99005"]) <= set(ecodes):
            out.append(u"secret の EDINET コードに組の提出者のコードが無い: %s" % (sorted(ecodes),))
        if not set([u"役員甲", u"科目乙", u"科目キ"]) <= set(labels):
            out.append(u"secret の行の字が作り物の行と違う: %s" % sorted(labels))
        if not set([u"順表頭", u"ア頭", u"イ頭", u"エ頭", u"オ頭", u"期ア年", u"単位ア", u"表頭"]) <= set(labels):
            out.append(u"secret に表の頭の印の各行の字が入っていない(今年の側・前の年の側の両方): %s" % sorted(labels))
        if not set([u"Item11", u"Item32", u"ctxB", u"unitS", u"C_No1Member"]) <= set(elems):
            out.append(u"secret の要素・文脈・単位の字(今年の側と前の年の側)が作り物の fact と違う: %s" % sorted(elems))
        if not set([u"見出しア", u"見出しイ", u"見出しウ", u"見出しエ"]) <= set(heads):
            out.append(u"secret の見出しの字が違う: %s" % sorted(heads))
        real_build = ms.build_record
        for ln, (what, leak) in enumerate(((u"前の年の側の docID", u"a S1ZP0004 b"), (u"組のコード", u"a E99004 b"), (u"見出しの字(全部一致)", u"見出しエ"), (u"要素の名", u"a Item32 b"),
                                           (u"文脈の字", u"a ctxB b"), (u"単位の字", u"a unitS b"), (u"行の字", u"科目キ"), (u"表の頭の印の字(今年の側にだけ在る頭)", u"オ頭"),
                                           (u"表の頭の印の字(前の年の側にだけ在る頭)", u"エ頭"))):
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


# ======================================================================== 5. 配線
STDLIB_OK = ("__future__", "argparse", "bisect", "collections", "hashlib", "importlib", "io", "json", "os", "re", "sys", "zipfile", "adapters")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "subprocess")
Z_CALLED = ("read_rows", "TABLE_RE", "FACT_RE", "build_tables", "stage_ht", "classify6", "bundle3", "check_clean", "rate_of", "build_record_unused")
Z_REQUIRED = ("read_rows", "TABLE_RE", "FACT_RE", "build_tables", "stage_ht", "classify6", "bundle3", "rate_of", "DATE_RE", "I")
WALL_CALLED = ("order_sha256", "HEX_RE")
NARROW_CALLED = ("doc_texts", "check_clean")
PRIOR_CALLED = ("make_pairs",)
NOT_COPIED = ("select_docs", "make_pairs", "code_and_end", "prior_index", "norm_label", "file_rows", "kind_of", "doc_texts", "order_sha256", "read_rows", "build_tables",
              "classify6", "bundle3", "stage_ht", "texts_rows", "is_nil", "parse_attrs", "check_clean_unused")
CUR_FACT_NAMES = ("a", "t", "b3", "attrs")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
PRIOR_NAME = "_xz1_prior_year_fact_draft_2026_11_22"
HARNESS_WORDS = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(")


def import_problems(src=None):
    u"""script の import は標準ライブラリと engine の 1 module と importlib だけ。前の便の関数は ``Z.``・``Y.``・``N.``・``W.`` から呼び写さない。今年の fact の属性は候補を作る呼び出しに渡さない。"""
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
    if eng != ["verify_document"]:
        out.append(u"engine から読む module が verify_document の 1 つだけでない: %s" % eng)
    attrs = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]
    if ("os", "environ") in attrs or ("os", "getenv") in attrs:
        out.append(u"環境変数を読んでいる")
    for table_, owner, label in ((Z_REQUIRED, "Z", u"便 XZ0"), (WALL_CALLED, "W", u"便 XG0"), (NARROW_CALLED, "N", u"便 XG1"), (PRIOR_CALLED, "Y", u"便 XY0")):
        for fn in table_:
            if (owner, fn) not in attrs:
                out.append(u"%s の %s を %s から呼んでいない" % (label, fn, owner))
    if ("Z.I", "_TR_RE") in attrs:
        pass
    if not any(isinstance(n, ast.Attribute) and n.attr == "_TR_RE" and isinstance(n.value, ast.Attribute) and n.value.attr == "I" for n in ast.walk(tree)):
        out.append(u"engine の _TR_RE を Z.I から呼んでいない")
    funcs = dict((n.name, n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    for fn in NOT_COPIED:
        if fn in funcs:
            out.append(u"前の便の %s を script が自分で定義している(写している)" % fn)
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "stage_ht":
            bad = set(x.id for arg in n.args for x in ast.walk(arg) if isinstance(x, ast.Name)) & set(CUR_FACT_NAMES)
            if bad:
                out.append(u"候補を作る関数 stage_ht の呼び出しに今年の fact の属性 %s が渡っている" % sorted(bad))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("build_col", "uses_number_col"):
            bad = set(x.id for arg in n.args for x in ast.walk(arg) if isinstance(x, ast.Name)) & set(("a", "t", "cur", "cur_rows", "cur_texts"))
            if bad:
                out.append(u"%s の呼び出しに今年の側の字・fact の属性 %s が渡っている" % (n.func.id, sorted(bad)))
    for fn in ("build_col",):
        f = funcs.get(fn)
        if f is None:
            out.append(u"表 COL を作る関数 %s が無い" % fn)
        else:
            used = set(x.id for x in ast.walk(f) if isinstance(x, ast.Name)) | set(a.arg for a in f.args.args)
            if used & set(("cur", "cur_rows", "cur_texts")):
                out.append(u"表 COL を作る関数 %s が今年の fact の属性を使っている" % fn)
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
    # ---- 形(§2-1)
    (u"M1 形の「ちょうど 1 つ」を「1 つ以上」にする", u"    if len(hits) != 1:\n        return None", u"    if len(hits) < 1:\n        return None", ("pure",)),
    (u"M2 1 つ目の部品も形に数える", u"for i, p in enumerate(parts) if i >= 1 and MEMBER_RE.match(p)]", u"for i, p in enumerate(parts) if MEMBER_RE.match(p)]", ("pure",)),
    (u"M3 2 つ目の部品を形に数えない(「2 つ目より後ろ」を厳密に読む)", u"for i, p in enumerate(parts) if i >= 1 and MEMBER_RE.match(p)]", u"for i, p in enumerate(parts) if i >= 2 and MEMBER_RE.match(p)]", ("pure", "count")),
    (u"M4 形の数字の並びを # に置き換えない", u'    parts[hits[0]] = m.group(1) + "#" + m.group(3)', u'    parts[hits[0]] = m.group(1) + "1" + m.group(3)', ("pure", "count")),
    (u"M5 形の後ろの字(A など)を落とす", u'    parts[hits[0]] = m.group(1) + "#" + m.group(3)', u'    parts[hits[0]] = m.group(1) + "#Member"', ("pure",)),
    (u"M6 形の Row を数えない", u'MEMBER_RE = re.compile(r"^(No|Row)([0-9]+)([A-Za-z]*Member)$")', u'MEMBER_RE = re.compile(r"^(No)([0-9]+)([A-Za-z]*Member)$")', ("pure",)),
    (u"M7 形の数字を 1 桁にする", u'MEMBER_RE = re.compile(r"^(No|Row)([0-9]+)([A-Za-z]*Member)$")', u'MEMBER_RE = re.compile(r"^(No|Row)([0-9])([A-Za-z]*Member)$")', ("pure",)),
    # ---- 表 COL・番号の列を使う条件(§2-2・§2-3)
    (u"M9 表 COL の鍵に T が空の行を入れる", u"    for h, th, T, facts, _ser, mark in prior_rows:\n        if not T:\n            continue\n        for td, a in facts:\n            b = Z.bundle3(a)",
     u"    for h, th, T, facts, _ser, mark in prior_rows:\n        for td, a in facts:\n            b = Z.bundle3(a)", ("rows",)),
    (u"M10 表 COL に形の無い文脈の fact も入れる", u"            sh = shape_of(b[1])\n            if sh is not None:", u"            sh = shape_of(b[1]) or u\"\"\n            if True:", ("rows", "count")),
    (u"M11 表 COL の鍵から th を外す", u"                col.setdefault((h, th, td), set()).add((b[0], sh, b[2]))", u"                col.setdefault((h, 0, td), set()).add((b[0], sh, b[2]))", ("count",)),
    (u"M12 番号の列を使う条件から「表 COL に鍵が在る」を外す", u"    if key_col not in col:\n        return False\n", u"    if False:\n        return False\n", ("rows", "count")),
    (u"M13 番号の列を使う条件の「候補が空」の枝を外す", u"    return (not cands_ht) or any(", u"    return any(", ("rows", "count")),
    (u"M14 番号の列を使う条件の「形の在る文脈」の枝を外す", u"    return (not cands_ht) or any(shape_of(b[1]) is not None for b in cands_ht)", u"    return (not cands_ht)", ("rows", "count")),
    (u"M15 番号の列を使う条件を、候補が在れば常に使うにする", u"    return (not cands_ht) or any(shape_of(b[1]) is not None for b in cands_ht)", u"    return True", ("rows", "count")),
    (u"M16 表 COL を今年の側から作る", u"    sig, col, sigc = build_col(prv)", u"    sig, col, sigc = build_col(cur)", ("count", "import")),
    # ---- 行の番号 k(§2-3)
    (u"M17 T が空の行を k に数える", u"        if numrow:\n            row_no[ser] = row_no.get(ser, 0) + 1", u"        if numrow or not T:\n            row_no[ser] = row_no.get(ser, 0) + 1", ("count",)),
    (u"M18 番号の列を使わない行も k に数える", u"        if numrow:\n            row_no[ser] = row_no.get(ser, 0) + 1", u"        if T:\n            row_no[ser] = row_no.get(ser, 0) + 1", ("count",)),
    (u"M19 k を表でなく file で数える", u"    for h, th, T, facts, ser, mark in cur:\n        plan = []", u"    for h, th, T, facts, ser, mark in [(a_, b_, c_, d_, e_[0], f_) for a_, b_, c_, d_, e_, f_ in cur]:\n        plan = []", ("count",)),
    (u"M20 k を file をまたいで表の通し番号だけで数える", u"    for h, th, T, facts, ser, mark in cur:\n        plan = []", u"    for h, th, T, facts, ser, mark in [(a_, b_, c_, d_, e_[1], f_) for a_, b_, c_, d_, e_, f_ in cur]:\n        plan = []", ("count",)),
    (u"M21 k を 0 から数える", u"            row_no[ser] = row_no.get(ser, 0) + 1", u"            row_no[ser] = row_no.get(ser, -1) + 1", ("count",)),
    (u"M22 k を行でなく fact ごとに数える", u"        k = row_no.get(ser)\n        for td, a, cands, use in plan:", u"        k = row_no.get(ser)\n        for td, a, cands, use in plan:\n            if use:\n                row_no[ser] = row_no.get(ser, 0) + 1\n                k = row_no[ser]", ("count",)),
    (u"M23 段 O の候補の k を 1 に固定する", u"set((nm, with_number(shape, k), u) for nm, shape, u in col[(h, th, td)])", u"set((nm, with_number(shape, 1), u) for nm, shape, u in col[(h, th, td)])", ("count",)),
    (u"M24 段 O の候補の鍵から th を外す", u"for nm, shape, u in col[(h, th, td)])", u"for nm, shape, u in col[(h, 0, td)])", ("count",)),
    (u"M25 段 O の候補に表 HT の候補を足す", u"                y = Z.classify6(t, o_cands)", u"                y = Z.classify6(t, o_cands | cands)", ("count",)),
    (u"M26 番号の列を使う fact でも段 O が段 HT の類のまま", u"                y = Z.classify6(t, o_cands)", u"                y = x", ("count",)),
    # ---- 表の頭の印(§2-4)
    (u"M27 印に fact の行より後ろの行を混ぜる", u"            elif ser not in closed:\n                head_rows.setdefault(ser, []).append(m.group(0))", u"            else:\n                head_rows.setdefault(ser, []).append(m.group(0))", ("rows", "count")),
    (u"M28 印の数字を除かない", u'DIGIT_RE = re.compile(r"[0-9]")', u'DIGIT_RE = re.compile(r"[^\\s\\S]")', ("pure", "count")),
    (u"M29 印のタグを除かない", u'TAG_RE = re.compile(r"<[^>]*>")', u'TAG_RE = re.compile(r"[^\\s\\S]")', ("pure", "count")),
    (u"M30 印に norm_label を掛けない", u'    return u"|".join(DIGIT_RE.sub(u"", norm_label(TAG_RE.sub(u"", t))) for t in row_texts)', u'    return u"|".join(DIGIT_RE.sub(u"", TAG_RE.sub(u"", t)) for t in row_texts)', ("pure", "count")),
    (u"M31 印を fact の行を含めて作る(最初の fact の行も入れる)", u"            if Z.FACT_RE.search(m.group(0)):\n                closed.add(ser)", u"            if Z.FACT_RE.search(m.group(0)):\n                closed.add(ser)\n                head_rows.setdefault(ser, []).append(m.group(0))", ("rows", "count")),
    (u"M32 印を最初の fact の行でなく T が空でない行で閉じる", u"            if Z.FACT_RE.search(m.group(0)):\n                closed.add(ser)", u"            if Z.FACT_RE.search(m.group(0)) and not Z.read_rows(m.group(0))[0][0][2] == u\"\":\n                closed.add(ser)", ("rows",)),
    (u"M33 印の表の識別を file をまたいで通し番号だけにする", u"        sers = [(fi, bisect.bisect_left(starts, m.start())) for m in matches]", u"        sers = [(0, bisect.bisect_left(starts, m.start())) for m in matches]", ("rows", "count")),
    (u"M34 印の区切りを空にする", u'    return u"|".join(DIGIT_RE', u'    return u"".join(DIGIT_RE', ("pure", "rows")),
    (u"M35 table_rows が file を昇順に並べない", u"    for fi, (_n, text) in enumerate(sorted(texts, key=lambda q: q[0])):", u"    for fi, (_n, text) in enumerate(texts):", ("rows",)),
    (u"M36 行の 1 対 1 の照合を外す", u"        if len(rows) != len(matches):", u"        if False:", ("rows",)),
    # ---- 段 G・OG・類 S(§2-5・§2-6)
    (u"M37 段 G が N を S にする", u'            g = x if (x in ("N", "X") or ok_g) else STOP_CLASS', u'            g = x if (x in ("X",) or ok_g) else STOP_CLASS', ("count",)),
    (u"M39 段 OG が N を S にする", u'            og = y if (y in ("N", "X") or ok_og) else STOP_CLASS', u'            og = y if (y in ("X",) or ok_og) else STOP_CLASS', ("count",)),
    (u"M41 段 OG の番号の列を使う fact の比べ先を表 HT の側にする", u"                ok_og = mark in sigc.get((h, th, td), ())", u"                ok_og = mark in sig.get((h, th, T, td), ())", ("count",)),
    (u"M42 段 OG の番号の列を使わない fact の比べ先を表 COL の側にする", u"                ok_og = mark in sig.get((h, th, T, td), ())", u"                ok_og = mark in sigc.get((h, th, td), ())", ("count",)),
    (u"M43 段 G の比べ先を表 COL の側にする", u"            ok_g = mark in sig.get((h, th, T, td), ())", u"            ok_g = mark in sigc.get((h, th, td), ())", ("count",)),
    (u"M44 段 G の比べ先の鍵から th を外す", u"            ok_g = mark in sig.get((h, th, T, td), ())", u"            ok_g = mark in sig.get((h, 0, T, td), ())", ("count",)),
    (u"M45 段 G を段 O の類に掛ける", u'            g = x if (x in ("N", "X") or ok_g) else STOP_CLASS', u'            g = y if (y in ("N", "X") or ok_g) else STOP_CLASS', ("count",)),
    (u"M46 段 OG を段 HT の類に掛ける", u'            og = y if (y in ("N", "X") or ok_og) else STOP_CLASS', u'            og = x if (x in ("N", "X") or ok_og) else STOP_CLASS', ("count",)),
    (u"M47 守りが常に止める(印を比べない)", u'            ok_g = mark in sig.get((h, th, T, td), ())', u'            ok_g = False', ("count",)),
    (u"M48 守りが何も止めない", u'            ok_g = mark in sig.get((h, th, T, td), ())', u'            ok_g = True', ("count",)),
    (u"M49 止めた fact を段 O の類で数える(段 G)", u'                acc["stopped_g"][x] += 1', u'                acc["stopped_g"][y] += 1', ("count",)),
    (u"M50 止めた fact を段 HT の類で数える(段 OG)", u'                acc["stopped_og"][y] += 1', u'                acc["stopped_og"][x] += 1', ("count",)),
    # ---- 段・類・移り
    (u"M51 段 HT の候補に今年の fact の束を足す", u"            cands = Z.stage_ht(ht3, h, th, T, td)", u"            cands = Z.stage_ht(ht3, h, th, T, td) | set([Z.bundle3(a)])", ("count",)),
    (u"M52 前の年の表を今年の側の行から作る", u'    ht3 = Z.build_tables([r[:4] for r in prv])["HT3"]', u'    ht3 = Z.build_tables([r[:4] for r in cur])["HT3"]', ("count",)),
    (u"M53 T が空の fact を X にしない(N にする)", u'                for s in STAGES4:\n                    st[s]["X"] += 1\n                acc["move"]["X"]["X"] += 1', u'                for s in STAGES4:\n                    st[s]["N"] += 1\n                acc["move"]["N"]["N"] += 1', ("count",)),
    (u"M54 段の間の移りの行と列を入れ替える", u'            acc["move"][x][y] += 1', u'            acc["move"][y][x] += 1', ("count",)),
    (u"M55 番号の列を使った fact を数えない", u'                acc["numcol"] += 1', u'                acc["numcol"] += 0', ("count",)),
    (u"M56 W1 の中身を段 O の W1 で数える", u'            if x == "W1":\n                c = next(iter(cands))', u'            if y == "W1":\n                c = next(iter(cands))', ("count",)),
    (u"M57 W1 の違う属性を違わない属性で数える", u"    return \"+\".join(ATTRS3[i] for i in range(3) if t[i] != c[i])", u"    return \"+\".join(ATTRS3[i] for i in range(3) if t[i] == c[i])", ("pure", "count")),
    (u"M58 番号だけの違いに name の違いを許す", u"    if t[1] == c[1] or t[0] != c[0] or t[2] != c[2]:", u"    if t[1] == c[1] or t[2] != c[2]:", ("pure",)),
    (u"M59 番号だけの違いに形が違うものを許す", u"    return st is not None and st == sc", u"    return st is not None and sc is not None", ("pure",)),
    (u"M60 番号だけの違いに形が無いものを許す", u"    return st is not None and st == sc", u"    return st == sc", ("pure",)),
    # ---- 記録・判定・60 組と 3 組
    (u"M61 60 組に番号 1〜3 を混ぜる", u"    rest = [a for n, a in zip(nos, accs) if n > SEEN_MAX_NO]", u"    rest = [a for n, a in zip(nos, accs)]", ("build",)),
    (u"M62 3 組に番号 4 以上を混ぜる", u"    seen = [a for n, a in zip(nos, accs) if n <= SEEN_MAX_NO]", u"    seen = [a for n, a in zip(nos, accs) if n <= SEEN_MAX_NO + 1]", ("build",)),
    (u"M63 60 組と 3 組を入れ替える", u"    t60, t3, t63 = totals(rest), totals(seen), totals(accs)", u"    t3, t60, t63 = totals(rest), totals(seen), totals(accs)", ("build",)),
    (u"M64 見た 3 組の分けの番号を 2 にする", u"SEEN_MAX_NO = 3", u"SEEN_MAX_NO = 2", ("seal", "build")),
    (u"M65 60 組の fact の合計の照合を外す", u"    if want_sum60 is not None and t60[\"facts\"] != want_sum60:", u"    if False:", ("build",)),
    (u"M66 便 XZ0 の記録との照合を外す", u"    if draft is not None:\n        check_against_draft(nos, accs, draft)", u"    if False:\n        check_against_draft(nos, accs, draft)", ("build",)),
    (u"M67 便 XZ0 の記録との照合が fact の数だけを見る", u"        if want != got or d[u\"行の中の数の fact の数\"] != acc[\"facts\"]:", u"        if d[u\"行の中の数の fact の数\"] != acc[\"facts\"]:", ("build",)),
    (u"M68 便 XZ0 の記録との照合が類の数だけを見る", u"        if want != got or d[u\"行の中の数の fact の数\"] != acc[\"facts\"]:", u"        if want != got:", ("build",)),
    (u"M69 便 XZ0 の記録との照合が段 H の類を読む", u"        want = dict(d[u\"束と段ごとの類別\"][Z.RECORD_LABELS[\"b3\"]][\"HT\"])", u"        want = dict(d[u\"束と段ごとの類別\"][Z.RECORD_LABELS[\"b3\"]][\"H\"])", ("build",)),
    (u"M70 便 XZ0 の記録に同じ番号が無くても止めない", u"        if n not in by_no:\n            raise Stop(u\"**便 XZ0 の記録に同じ番号が無い。止める**\")", u"        if n not in by_no:\n            continue", ("build",)),
    (u"M71 組の数 63 を 62 にする", u"PAIRS_WANT = 63", u"PAIRS_WANT = 62", ("seal",)),
    (u"M72 60 組の合計 61100 を 61101 にする", u"SUM60_WANT = 61100", u"SUM60_WANT = 61101", ("seal",)),
    (u"M73 XZ1-1 の分母を段 O にする", u'(u"XZ1-1 段 OG の類 W1 / 行の中の数の fact", rate_of(og["W1"], D))', u'(u"XZ1-1 段 OG の類 W1 / 行の中の数の fact", rate_of(o["W1"], D))', ("judge",)),
    (u"M74 XZ1-2 を段 O の U にする", u'(u"XZ1-2 段 OG の類 U / 行の中の数の fact", rate_of(og["U"], D))', u'(u"XZ1-2 段 OG の類 U / 行の中の数の fact", rate_of(o["U"], D))', ("judge",)),
    (u"M75 XZ1-3 の新しい W1 に W2 から来たものを数える", u'    new_w1 = sum(t["move"][hc]["W1"] for hc in CLASSES if hc not in ("W1", "W2"))', u'    new_w1 = sum(t["move"][hc]["W1"] for hc in CLASSES if hc != "W1")', ("judge",)),
    (u"M76 XZ1-3 の新しい W1 に W1 のままのものを数える", u'    new_w1 = sum(t["move"][hc]["W1"] for hc in CLASSES if hc not in ("W1", "W2"))', u'    new_w1 = sum(t["move"][hc]["W1"] for hc in CLASSES)', ("judge",)),
    (u"M77 XZ1-4 の差の向きを逆にする", u'(u"段 O の U から段 HT の U を引いた数", o["U"] - ht["U"])', u'(u"段 O の U から段 HT の U を引いた数", ht["U"] - o["U"])', ("judge",)),
    (u"M78 XZ1-5 を W1 で数える", u'(u"XZ1-5 段 G が止めた段 HT の U / 行の中の数の fact", rate_of(t["stopped_g"]["U"], D))', u'(u"XZ1-5 段 G が止めた段 HT の U / 行の中の数の fact", rate_of(t["stopped_g"]["W1"], D))', ("judge",)),
    (u"M79 XZ1-6 の分母を fact の全部にする", u'rate_of(t["stopped_g"]["W1"], ht["W1"])', u'rate_of(t["stopped_g"]["W1"], D)', ("judge",)),
    (u"M80 XZ1-7 の分子を W1 の全部にする", u'rate_of(t["w1_number_only"], ht["W1"])', u'rate_of(ht["W1"], ht["W1"])', ("judge",)),
    (u"M81 読み方の通した数を U だけにする", u'    pass_og = og["U"] + og["W1"]', u'    pass_og = og["U"]', ("judge",)),
    (u"M82 止めたうち正しかった数を段 OG の U にする", u'(u"止めたうち正しかった(段 O の類 U)", t["stopped_og"]["U"])', u'(u"止めたうち正しかった(段 O の類 U)", og["U"])', ("judge",)),
    (u"M83 totals が足さない", u"    for a in accs:\n        merge(tot, a)", u"    for a in accs[:1]:\n        merge(tot, a)", ("judge", "build")),
    (u"M84 merge が入れ子を足さない", u"        if isinstance(v, dict):\n            merge(into[k], v)", u"        if isinstance(v, dict):\n            pass", ("judge", "build")),
    # ---- 旗
    (u"M85 旗 1 を「どれかの組で 0」にする", u'(u"旗", len(rest) > 0 and og_w1_zero == len(rest))', u'(u"旗", len(rest) > 0 and og_w1_zero > 0)', ("flags",)),
    (u"M86 旗 2 の「超えた」を「以上」にする", u'(u"旗", 100 * t60["stages"]["G"]["S"] > FLAG_S_OVER * D60)', u'(u"旗", 100 * t60["stages"]["G"]["S"] >= FLAG_S_OVER * D60)', ("flags",)),
    (u"M87 旗 3 の「超えた」を「以上」にする", u'(u"旗", 100 * t60["stages"]["OG"]["S"] > FLAG_S_OVER * D60)', u'(u"旗", 100 * t60["stages"]["OG"]["S"] >= FLAG_S_OVER * D60)', ("flags",)),
    (u"M88 旗 2 を段 OG の S で数える", u'(u"fact", t60["stages"]["G"]["S"]), (u"分母", D60), (u"旗", 100 * t60["stages"]["G"]["S"] > FLAG_S_OVER * D60)', u'(u"fact", t60["stages"]["OG"]["S"]), (u"分母", D60), (u"旗", 100 * t60["stages"]["OG"]["S"] > FLAG_S_OVER * D60)', ("flags",)),
    (u"M89 旗 3 を段 G の S で数える", u'(u"fact", t60["stages"]["OG"]["S"]), (u"分母", D60), (u"旗", 100 * t60["stages"]["OG"]["S"] > FLAG_S_OVER * D60)', u'(u"fact", t60["stages"]["G"]["S"]), (u"分母", D60), (u"旗", 100 * t60["stages"]["G"]["S"] > FLAG_S_OVER * D60)', ("flags",)),
    (u"M90 旗 4 を「少ない」にする", u'(u"旗", t60["numcol"] == 0)', u'(u"旗", t60["numcol"] < 2)', ("flags",)),
    (u"M91 旗の分母を 63 組にする", u"    D60 = t60[\"facts\"]", u"    D60 = t63[\"facts\"]", ("build",)),
    (u"M92 旗が立ったら止める", u'    j = judgment_numbers(t60)', u'    if t60["numcol"] == 0:\n        raise Stop(u"旗")\n    j = judgment_numbers(t60)', ("flags",)),
    (u"M93 旗 1 の W1 が 0 の組を 3 組も含めて数える", u"    og_w1_zero = sum(1 for a in rest if a[\"stages\"][\"OG\"][\"W1\"] == 0)", u"    og_w1_zero = sum(1 for a in accs if a[\"stages\"][\"OG\"][\"W1\"] == 0)", ("build",)),
    # ---- 記録の検査・書き方
    (u"M94 記録を排他で書かない", u'    if os.path.exists(path):\n        raise Stop(u"**記録が既に在る', u'    if False:\n        raise Stop(u"**記録が既に在る', ("clean", "e2e")),
    (u"M95 --check が secret を検査に渡さない", u"    check_clean(rec, text, secret)\n    say(u\"--check", u"    check_clean(rec, text)\n    say(u\"--check", ("secret",)),
    (u"M96 前の便の script を一意でない名で読む", u'name = "_xz1_prior_year_fact_draft_2026_11_22"', u'name = "xbrl_prior_year_fact_draft"', ("import",)),
    (u"M97 記録の engine の指紋を空にする", u'rec[u"engine の指紋"] = od((k, fp[k]) for k in', u'rec[u"engine の指紋"] = od((k, u"") for k in', ("build",)),
    (u"M98 記録の script の sha256 を空にする", u'rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))', u'rec[u"この script の sha256"] = u""', ("build",)),
    (u"M99 記録の限界を 5 行にする", u'rec[u"限界"] = list(LIMITS)', u'rec[u"限界"] = list(LIMITS)[:5]', ("build",)),
    (u"M100 表の頭の印を secret に入れない(各行)", u'    for part in mark.split(u"|"):\n        if part:\n            secret[0].add(part)\n', u'', ("secret",)),
    (u"M101 見出しの字を secret に入れない", u"    if h:\n        secret[4].add(h)\n", u"", ("secret",)),
    (u"M102 前の年の側の行の字・印を secret に入れない", u"    for h, th, T, facts, _ser, mark in prv:\n        if secret is not None:\n            note_secret(secret, T, mark, h)\n", u"    for h, th, T, facts, _ser, mark in prv:\n        if secret is not None:\n            pass\n", ("secret",)),
    (u"M103 前の年の側の docID を secret に入れない", u"[d[0] for d in docs] + [p[3] for p in pairs]", u"[d[0] for d in docs]", ("secret",)),
    (u"M104 前の年の側として今年の zip を読む", u"        with zipfile.ZipFile(pp) as z:", u"        with zipfile.ZipFile(p) as z:", ("build", "e2e")),
    (u"M106 行の字が空の fact(X)を段 G で S に数える", u'                for s in STAGES4:\n                    st[s]["X"] += 1', u'                for s in STAGES4:\n                    st[s]["S" if s == "G" else "X"] += 1', ("count",)),
    (u"M107 行の字が空の fact(X)を段 OG で S に数える", u'                for s in STAGES4:\n                    st[s]["X"] += 1', u'                for s in STAGES4:\n                    st[s]["S" if s == "OG" else "X"] += 1', ("count",)),
    # ---- 独立監査が約束の側から作った 4 本(場面 6〜8 が縛る)
    (u"M108 段 O の候補の unit を今年の fact の unit に置き換える", u"set((nm, with_number(shape, k), u) for nm, shape, u in col[(h, th, td)])", u"set((nm, with_number(shape, k), t[2]) for nm, shape, u in col[(h, th, td)])", ("count",)),
    (u"M109 段 O の候補の name を今年の fact の name に置き換える", u"set((nm, with_number(shape, k), u) for nm, shape, u in col[(h, th, td)])", u"set((t[0], with_number(shape, k), u) for nm, shape, u in col[(h, th, td)])", ("count",)),
    (u"M110 番号の列を使う判定に今年の contextRef の形を混ぜる(形が在れば使う)", u"            use = uses_number_col(cands, (h, th, td), col)\n", u"            use = uses_number_col(cands, (h, th, td), col) or ((h, th, td) in col and shape_of(a.get(\"contextRef\")) is not None)\n", ("count",)),
    (u"M111 番号の列を使う判定の「候補の形」を今年の contextRef の形に替える", u"            use = uses_number_col(cands, (h, th, td), col)\n", u"            use = (h, th, td) in col and ((not cands) or shape_of(a.get(\"contextRef\")) is not None)\n", ("count",)),
    (u"M112 行の番号 k を数える条件を行の最後の fact が使うにする", u"            numrow = numrow or use\n", u"            numrow = use\n", ("count",)),
    # ---- 再監査が約束の側から作った 2 本(場面 9・10 が縛る)と、自分で作った近くの形
    (u"M113 段 O の候補の形を今年の contextRef の形があればそれにする", u"set((nm, with_number(shape, k), u) for nm, shape, u in col[(h, th, td)])", u"set((nm, with_number(shape_of(a.get(\"contextRef\")) or shape, k), u) for nm, shape, u in col[(h, th, td)])", ("count",)),
    (u"M114 行の番号 k を数える条件に今年の fact の contextRef に形が在ることを足す", u"            numrow = numrow or use\n", u"            numrow = numrow or use or shape_of(a.get(\"contextRef\")) is not None\n", ("count",)),
    (u"M115 行の番号 k を数える条件を今年の unit が unitJ のときだけにする", u"            numrow = numrow or use\n", u"            numrow = numrow or (use and a.get(\"unitRef\") == \"unitJ\")\n", ("count",)),
    (u"M116 行の番号 k を数える条件を今年の contextRef が ctxB でないときだけにする", u"            numrow = numrow or use\n", u"            numrow = numrow or (use and a.get(\"contextRef\") != \"ctxB\")\n", ("count",)),
    (u"M117 行の番号 k を数える条件を今年の contextRef に形が在るときだけにする", u"            numrow = numrow or use\n", u"            numrow = numrow or (use and shape_of(a.get(\"contextRef\")) is not None)\n", ("count",)),
    (u"M118 番号の列を使う条件に「候補の中に今年の fact と同じ unit が在る」を足す", u"            use = uses_number_col(cands, (h, th, td), col)\n", u"            use = uses_number_col(cands, (h, th, td), col) and (not cands or any(c[2] == Z.bundle3(a)[2] for c in cands))\n", ("count",)),
    (u"M119 番号の列を使う条件に「候補の中に今年の fact と同じ name が在る」を足す", u"            use = uses_number_col(cands, (h, th, td), col)\n", u"            use = uses_number_col(cands, (h, th, td), col) and (not cands or any(c[0] == Z.bundle3(a)[0] for c in cands))\n", ("count",)),
    (u"M120 段 O の候補の形を、表 HT の候補の形と同じなら今年の contextRef の形にする", u"set((nm, with_number(shape, k), u) for nm, shape, u in col[(h, th, td)])", u"set((nm, with_number(shape_of(a.get(\"contextRef\")) if shape_of(a.get(\"contextRef\")) in [shape_of(c[1]) for c in cands] else shape, k), u) for nm, shape, u in col[(h, th, td)])", ("count",)),
    # ---- 3 回目の監査が約束の側から作った 5 本(場面 13〜15 が縛る)と、自分で作った近くの形
    (u"M121 段 G が W2 を通す(止めるのは A・U・W1 だけ)", u'            g = x if (x in ("N", "X") or ok_g) else STOP_CLASS', u'            g = x if (x in ("N", "X", "W2") or ok_g) else STOP_CLASS', ("count",)),
    (u"M122 段 G が A を通す(止めるのは U・W1・W2 だけ)", u'            g = x if (x in ("N", "X") or ok_g) else STOP_CLASS', u'            g = x if (x in ("N", "X", "A") or ok_g) else STOP_CLASS', ("count",)),
    (u"M123 段 OG が A を通す(止めるのは U・W1・W2 だけ)", u'            og = y if (y in ("N", "X") or ok_og) else STOP_CLASS', u'            og = y if (y in ("N", "X", "A") or ok_og) else STOP_CLASS', ("count",)),
    (u"M124 段 OG が W2 を通す(止めるのは U・A・W1 だけ)", u'            og = y if (y in ("N", "X") or ok_og) else STOP_CLASS', u'            og = y if (y in ("N", "X", "W2") or ok_og) else STOP_CLASS', ("count",)),
    (u"M125 行の番号 k を行の先頭の fact だけが使うかで決める", u'            numrow = numrow or use\n', u'            numrow = use if td == facts[0][0] else numrow\n', ("count",)),
    (u"M126 段 G が U だけ止める", u'            g = x if (x in ("N", "X") or ok_g) else STOP_CLASS', u'            g = x if (x != "U" or ok_g) else STOP_CLASS', ("count",)),
    (u"M127 段 G が W1 だけ止める", u'            g = x if (x in ("N", "X") or ok_g) else STOP_CLASS', u'            g = x if (x != "W1" or ok_g) else STOP_CLASS', ("count",)),
    (u"M128 段 OG が U と W1 だけ止める", u'            og = y if (y in ("N", "X") or ok_og) else STOP_CLASS', u'            og = y if (y not in ("U", "W1") or ok_og) else STOP_CLASS', ("count",)),
    (u"M129 行の番号 k を、行の fact の過半が使うときだけ数える", u'        if numrow:\n            row_no[ser]', u'        if sum(1 for q in plan if q[3]) * 2 > len(plan):\n            row_no[ser]', ("count",)),
    # ---- 4 回目の監査が約束の側から作った 6 本(場面 16〜18 が縛る)と、自分で作った鍵の端・比べ方の近くの形(場面 19〜21 が縛る)
    (u'M130 番号の列を使う条件を、表 HT の候補が 2 つ以下のときだけにする', u'    if key_col not in col:\n        return False\n', u'    if key_col not in col or len(cands_ht) > 2:\n        return False\n', ("count",)),
    (u'M131 段 O の類を、段 HT が A か W2 のときは段 HT の類のままにする(O の数だけ)', u'            st["O"][y] += 1\n', u'            st["O"][y if x not in ("A", "W2") else x] += 1\n', ("count",)),
    (u'M132 番号の列を使う fact の段 O の類を、段 HT が A のときは段 HT の類のままにする', u'                y = Z.classify6(t, o_cands)\n', u"                y = Z.classify6(t, o_cands) if x != 'A' else x\n", ("count",)),
    (u'M133 番号の列を使う fact の段 O の類を、段 HT が W2 のときは段 HT の類のままにする', u'                y = Z.classify6(t, o_cands)\n', u"                y = Z.classify6(t, o_cands) if x != 'W2' else x\n", ("count",)),
    (u'M134 段 OG の番号の列を使う fact の比べ先に表 HT の側の印の集まりも足す', u'                ok_og = mark in sigc.get((h, th, td), ())', u'                ok_og = mark in sigc.get((h, th, td), ()) or mark in sig.get((h, th, T, td), ())', ("count",)),
    (u'M135 段 G の比べ先の鍵から th を落とす(th の違う鍵の印も足す)', u'            ok_g = mark in sig.get((h, th, T, td), ())', u'            ok_g = any(mark in v for kk, v in sig.items() if kk[0]==h and kk[2]==T and kk[3]==td)', ("count",)),
    (u'M136 段 G の比べ先の鍵から h を落とす', u'            ok_g = mark in sig.get((h, th, T, td), ())', u'            ok_g = any(mark in v for kk, v in sig.items() if kk[1]==th and kk[2]==T and kk[3]==td)', ("count",)),
    (u'M137 段 G の比べ先の鍵から T を落とす', u'            ok_g = mark in sig.get((h, th, T, td), ())', u'            ok_g = any(mark in v for kk, v in sig.items() if kk[0]==h and kk[1]==th and kk[3]==td)', ("count",)),
    (u'M138 段 G の比べ先の鍵から td を落とす', u'            ok_g = mark in sig.get((h, th, T, td), ())', u'            ok_g = any(mark in v for kk, v in sig.items() if kk[0]==h and kk[1]==th and kk[2]==T)', ("count",)),
    (u'M139 段 OG(番号の列を使わない fact)の比べ先の鍵から th を落とす', u'                ok_og = mark in sig.get((h, th, T, td), ())', u'                ok_og = any(mark in v for kk, v in sig.items() if kk[0]==h and kk[2]==T and kk[3]==td)', ("count",)),
    (u'M140 段 OG(番号の列を使わない fact)の比べ先の鍵から h を落とす', u'                ok_og = mark in sig.get((h, th, T, td), ())', u'                ok_og = any(mark in v for kk, v in sig.items() if kk[1]==th and kk[2]==T and kk[3]==td)', ("count",)),
    (u'M141 段 OG(番号の列を使わない fact)の比べ先の鍵から T を落とす', u'                ok_og = mark in sig.get((h, th, T, td), ())', u'                ok_og = any(mark in v for kk, v in sig.items() if kk[0]==h and kk[1]==th and kk[3]==td)', ("count",)),
    (u'M142 段 OG(番号の列を使わない fact)の比べ先の鍵から td を落とす', u'                ok_og = mark in sig.get((h, th, T, td), ())', u'                ok_og = any(mark in v for kk, v in sig.items() if kk[0]==h and kk[1]==th and kk[2]==T)', ("count",)),
    (u'M143 段 OG(番号の列を使う fact)の比べ先の鍵から th を落とす', u'                ok_og = mark in sigc.get((h, th, td), ())', u'                ok_og = any(mark in v for kk, v in sigc.items() if kk[0]==h and kk[2]==td)', ("count",)),
    (u'M144 段 OG(番号の列を使う fact)の比べ先の鍵から h を落とす', u'                ok_og = mark in sigc.get((h, th, td), ())', u'                ok_og = any(mark in v for kk, v in sigc.items() if kk[1]==th and kk[2]==td)', ("count",)),
    (u'M145 段 OG(番号の列を使う fact)の比べ先の鍵から td を落とす', u'                ok_og = mark in sigc.get((h, th, td), ())', u'                ok_og = any(mark in v for kk, v in sigc.items() if kk[0]==h and kk[1]==th)', ("count",)),
    (u'M146 段 G の頭の印の比べを部分一致にする', u'            ok_g = mark in sig.get((h, th, T, td), ())', u'            ok_g = any(m in mark or mark in m for m in sig.get((h, th, T, td), ()))', ("count",)),
    (u'M147 段 OG(番号の列を使わない fact)の頭の印の比べを部分一致にする', u'                ok_og = mark in sig.get((h, th, T, td), ())', u'                ok_og = any(m in mark or mark in m for m in sig.get((h, th, T, td), ()))', ("count",)),
    (u'M148 段 OG(番号の列を使う fact)の頭の印の比べを部分一致にする', u'                ok_og = mark in sigc.get((h, th, td), ())', u'                ok_og = any(m in mark or mark in m for m in sigc.get((h, th, td), ()))', ("count",)),
    (u'M149 段 G の頭の印の比べを前方一致にする', u'            ok_g = mark in sig.get((h, th, T, td), ())', u'            ok_g = any(m.startswith(mark) or mark.startswith(m) for m in sig.get((h, th, T, td), ()))', ("count",)),
    (u'M150 表 COL の側の印の集まりに形の無い文脈の fact の行の印も入れる', u'            sh = shape_of(b[1])\n            if sh is not None:\n', u'            sh = shape_of(b[1])\n            sigc.setdefault((h, th, td), set()).add(mark)\n            if sh is not None:\n', ("count",)),
    (u'M151 表 COL の側の印の集まりの鍵から th を落とす', u'                sigc.setdefault((h, th, td), set()).add(mark)', u'                sigc.setdefault((h, 0, td), set()).add(mark)', ("count",)),
    (u'M152 表 HT の側の印の集まりの鍵から th を落とす', u'            sig.setdefault((h, th, T, td), set()).add(mark)', u'            sig.setdefault((h, 0, T, td), set()).add(mark)', ("count",)),
    # ---- 空の欄(nil)の fact(5 回目の監査の穴。封 §2-4・便 XZ0 の封: 空の欄も fact と数える)
    (u"N2 表の頭を閉じる行を「空の欄でない fact を持つ最初の行」にする", u"            if Z.FACT_RE.search(m.group(0)):\n                closed.add(ser)", u"            if Z.FACT_RE.search(m.group(0)) and 'xsi:nil' not in m.group(0):\n                closed.add(ser)", ("count",)),
    (u"P2 前の年の側の表(SIG・COL・SIGC)の作りから空の欄を落とす", u"        for td, a in facts:\n            b = Z.bundle3(a)\n            sig.setdefault", u"        for td, a in facts:\n            if Z.is_nil(a):\n                continue\n            b = Z.bundle3(a)\n            sig.setdefault", ("count",)),
    (u"P3 今年の側の類分けから空の欄を落とす", u"        for td, a in facts:\n            if not T:\n", u"        for td, a in facts:\n            if Z.is_nil(a):\n                continue\n            if not T:\n", ("count",)),
    (u"Q1 行の番号 k の数えから、空の欄だけで番号の列を使う行を落とす", u"            numrow = numrow or use\n", u"            numrow = numrow or (use and not Z.is_nil(a))\n", ("count",)),
    (u"Q2 表 COL の unitRef が無いとき空の字にする", u"                col.setdefault((h, th, td), set()).add((b[0], sh, b[2]))", u"                col.setdefault((h, th, td), set()).add((b[0], sh, b[2] or u\"\"))", ("count",)),
    (u"Q3 表 HT の側の印の集まり SIG だけから空の欄を落とす", u"            sig.setdefault((h, th, T, td), set()).add(mark)\n", u"            if not Z.is_nil(a):\n                sig.setdefault((h, th, T, td), set()).add(mark)\n", ("count",)),
    (u"Q4 表 COL だけから空の欄を落とす", u"            sh = shape_of(b[1])\n            if sh is not None:\n                col.", u"            sh = shape_of(b[1])\n            if sh is not None and not Z.is_nil(a):\n                col.", ("count",)),
    (u"Q5 今年の空の欄を番号の列を使う fact にしない", u"            use = uses_number_col(cands, (h, th, td), col)\n", u"            use = uses_number_col(cands, (h, th, td), col) and not Z.is_nil(a)\n", ("count",)),
    (u"Q6 今年の空の欄を行の字の無い fact(X)と同じに扱う", u"            if not T:\n                plan.append((td, a, None, None))", u"            if not T or Z.is_nil(a):\n                plan.append((td, a, None, None))", ("count",)),
    # ---- 6 回目の監査の穴(場面 23 が縛る: 同じ見出しの 2 番目の表(th 1)にだけ在る番号の列)
    (u"Z1 番号の列を使う条件の表 COL の引きの鍵から th を落とす", u"use = uses_number_col(cands, (h, th, td), col)", u"use = uses_number_col(cands, (h, 0, td), col)", ("count",)),
    (u"Z2 段 OG の番号の列を使う fact の比べ先の引きの鍵から th を落とす(引くだけ。作りは元のまま)", u"ok_og = mark in sigc.get((h, th, td), ())", u"ok_og = mark in sigc.get((h, 0, td), ())", ("count",)),
    (u"M105 走りが便 XZ0 の記録を読まずに進む", u'    if draft == "auto":\n        draft = load_draft(root)\n    rec, secret = build_record(docs, prior, want_docs, want_pairs, draft, want_sum60)\n    out = out or', u'    if draft == "auto":\n        draft = None\n    rec, secret = build_record(docs, prior, want_docs, want_pairs, draft, want_sum60)\n    out = out or', ("e2e",)),
)

#: 黙るのが設計どおりの変異(同値)。理由を書き、別の試験で「黙ること」を縛る
SILENT_BY_DESIGN = (
    (u"S2 k の字への置き換えを最初の # だけにする", u'    return shape.replace("#", str(k))', u'    return shape.replace("#", str(k), 1)',
     u"形の字(``shape_of`` の返り)には # が 1 つしか入らない(数字の並びを置き換えるのは番号つきの部品 1 つだけ)ので、最初の # だけの置き換えは同値の変異。"),
    (u"S3 段 G が X を S にする(X の枝を外す)", u'            g = x if (x in ("N", "X") or ok_g) else STOP_CLASS', u'            g = x if (x in ("N",) or ok_g) else STOP_CLASS',
     u"行の字が空の fact(類 X)は、守りに届く前に ``continue`` で各段の X に数えられる。守りの文の ``X`` の枝は届かない(同値の変異)。X が S にならないことは M-X の変異が縛る。"),
    (u"S4 段 OG が X を S にする(X の枝を外す)", u'            og = y if (y in ("N", "X") or ok_og) else STOP_CLASS', u'            og = y if (y in ("N",) or ok_og) else STOP_CLASS',
     u"S3 と同じ(X は守りに届かない)。"),
    (u"S5 段 O の候補の k に、今年の文脈に形が無いときだけ 1 を足す", u"set((nm, with_number(shape, k), u) for nm, shape, u in col[(h, th, td)])", u"set((nm, with_number(shape, k + (1 if shape_of(a.get(\"contextRef\")) is None else 0)), u) for nm, shape, u in col[(h, th, td)])",
     u"今年の文脈に形が無い fact は、段 O の候補(文脈に形が在る)のどれとも文脈が等しくならない。k がいくつでも類は同じ(同値の変異)。contextRef に # の字が入らないかぎり同値(XML の ID に # は入らない)。k の数え方は、次の行の fact が形を持つ場面 2・10・11 が縛る。"),
    (u"S6 表の通し番号を bisect_left でなく bisect_right で数える", u"bisect.bisect_left(starts, m.start())", u"bisect.bisect_right(starts, m.start())",
     u"starts は ``<table`` の開きタグの位置・m.start() は ``<tr`` の開きタグの位置。2 つの開きタグは同じ位置に在りえない(字が違う)ので、bisect_left と bisect_right は同じ値を返す(同値の変異)。"),
    (u"S1 組の提出者のコードを secret に入れない", u"set(p[5] for p in pairs), set(), set())", u"set(), set(), set())",
     u"組の相手は同じ提出者のコードで見つかるので、今年の側の zip の xsd の名から正規表現で集める EDINET コードに同じコードが入る(同値の変異)。"),
)


def check_by_name(name, mod, src):
    table_ = {u"seal": seal_problems, u"pure": pure_problems, u"rows": rows_problems, u"count": count_problems, u"judge": judge_problems, u"build": build_problems,
              u"clean": clean_problems, u"e2e": e2e_problems, u"secret": secret_problems, u"flags": flags_problems}
    if name in table_:
        return table_[name](mod)
    if name == u"import":
        return import_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"pure", u"rows", u"count", u"judge", u"build", u"clean", u"e2e", u"secret", u"flags", u"import")


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
        for old, new in ((u"段 OG の類 W1 は fact の 1.0% 以下", u"段 OG の類 W1 は fact の 2.0% 以下"),
                         (u"段 OG の類 U は fact の 72.0% 以上", u"段 OG の類 U は fact の 73.0% 以上"),
                         (u"組の数が 63 でなければ script は止まる", u"組の数が 62 でなければ script は止まる"),
                         (u"段 G が止めた段 HT の U は、fact の 1.0% 以上 8.0% 以下", u"段 G が止めた段 HT の U は、fact の 1.0% 以上 9.0% 以下"),
                         (u"S が fact の 30% を超えた", u"S が fact の 31% を超えた"), (u"便 XZ0 の記録から 61100", u"便 XZ0 の記録から 61101"),
                         (u"段 OG の W1 が 0 の組は 20 組以上", u"段 OG の W1 が 0 の組は 21 組以上"), (u"X と N はそのまま", u"X はそのまま"),
                         (u"表の頭の印の字・要素の名", u"要素の名"), (u"段 O の W1 は段 HT の W1 より 300 以上少なく", u"段 O の W1 は段 HT の W1 より 301 以上少なく"),
                         (u"表の頭の印は、最初に fact を持つ行より前の行の字だけ", u"表の頭の印は、fact を持つ行より前の行の字だけ")):
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"prior_year_fact_guard", body)
        self.assertNotIn(u"xbrl_prior_year", body)


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_the_order_check_lists_the_script_and_the_gate_and_not_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)


class PureTest(unittest.TestCase):
    def test_b_1_shape_mark_and_difference_parts(self):
        self.assertEqual([], pure_problems())

    def test_b_2_rows_marks_col_and_the_number_col_condition(self):
        self.assertEqual([], rows_problems())

    def test_b_3_made_up_pairs_equal_the_hand_count(self):
        self.assertEqual([], count_problems())

    def test_b_4_the_hand_counts_are_consistent_and_not_nearby_numbers(self):
        self.assertEqual([], hand_shape_problems())

    def test_b_5_the_judgment_numbers_and_the_sum_by_hand(self):
        self.assertEqual([], judge_problems())

    def test_b_6_the_fake_zips_have_the_decoys_the_checks_say(self):
        with Temp() as d:
            docs, prior = make_dirs(d)
            with zipfile.ZipFile(os.path.join(docs, "S1ZZ0001.zip")) as z:
                names = z.namelist()
            self.assertTrue(any(n.startswith(u"XBRL/AuditDoc/") for n in names) and any(n.endswith(u"_other.htm") for n in names))
            self.assertEqual(6, len([x for x in os.listdir(docs) if x.endswith(".zip")]))
            self.assertEqual(5, len([x for x in os.listdir(prior) if x.endswith(".zip")]))
        self.assertEqual(SUM60 + SUM3, sum(h["facts"] for _n, _c, _p, h in SCENARIOS))


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
            MS.N.check_clean(rec, text)
            self.assertEqual(list(MS.LIMITS), rec[u"限界"])
            self.assertEqual(MS.SEAL_COMMIT, rec[u"封の commit"])
            self.assertEqual(63, rec[u"材料"][u"組の数"])
            self.assertEqual(63, len(rec[u"書類"]))
            t60 = [v for k, v in rec.items() if k.startswith(u"集計 60 組")][0]
            self.assertEqual(MS.SUM60_WANT, t60[u"行の中の数の fact の数"])
            self.assertTrue(all(n > MS.SEEN_MAX_NO for n in [r[u"番号"] for r in rec[u"書類"] if r[u"番号"] > MS.SEEN_MAX_NO]))
            # 便 XZ0 の記録と段 HT の類の数が同じ(在れば)
            dp = os.path.join(ROOT, DRAFT_RECORD_REL)
            if os.path.exists(dp):
                draft = json.loads(read(DRAFT_RECORD_REL), object_pairs_hook=od)
                by = dict((d[u"番号"], d) for d in draft[u"書類"])
                for r in rec[u"書類"]:
                    self.assertEqual(dict(by[r[u"番号"]][u"束と段ごとの類別"][u"束 3"]["HT"]), dict(r[u"段ごとの類別"]["HT"]), r[u"番号"])
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
        self.assertNotEqual([], import_problems(base + u"\ndef classify6(a, b):\n    return None\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = '_lab.xml'\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef mutate(x):\n    return x\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = 'run_doc('\n"))
        self.assertNotEqual([], import_problems(base.replace(u"Z.stage_ht(ht3, h, th, T, td)", u"Z.stage_ht(ht3, h, th, T, td, a)")))
        self.assertNotEqual([], import_problems(base.replace(u"build_col(prv)", u"build_col(cur)")))
        self.assertNotEqual([], import_problems(base.replace(u"Z.I._TR_RE", u"None")))
        self.assertNotEqual([], import_problems(base.replace(u"from adapters.xbrl import verify_document as VD", u"from adapters.xbrl import verify_document as VD\nfrom adapters.xbrl import instance as I")))
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
        mod = load_module(SCRIPT_REL, "xbrl_prior_year_fact_guard_script_for_sysmodules_check")
        self.assertEqual([], [k for k, v in before.items() if sys.modules.get(k) is not v])
        self.assertIn(PRIOR_NAME, sys.modules)
        self.assertIs(mod.Z, sys.modules[PRIOR_NAME])
        self.assertIs(mod.Y, mod.Z.Y)
        self.assertIs(mod.W, mod.Z.W)
        self.assertIs(mod.N, mod.Z.N)
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
        self.assertGreaterEqual(len(MUTANTS), 60)

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
            for c in (u"pure", u"rows", u"count", u"judge", u"build", u"clean", u"e2e", u"secret", u"flags"):
                self.assertEqual([], check_by_name(c, mod, None), (name, c))


if __name__ == "__main__":
    unittest.main()
