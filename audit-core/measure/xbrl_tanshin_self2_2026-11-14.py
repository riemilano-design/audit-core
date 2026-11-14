# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TANSHIN_SELF2_SEAL_2026-11-14.md §0-2・§2・§5 ― TSS の第 2 便(一)中間の短信の期の名前を ``measure/`` の側で写して判定する・(二)「値が違う」のうち表の値に近い行だけを拾って読む。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(``core/``・``adapters/``)と ``measure/lib/`` は 1 行も変えない。**材料は TSS の置く script が置いた folder の ZIP を読むだけ(1 file も足さない)。
切り出し・包み直し・判定の部品・母集団の読み・止め方・書き方は、第 1 便の script ``xbrl_tanshin_self_2026-11-14.py``(以下 TSS)の関数を **呼ぶ**(書き写さない)。

    python3 measure/xbrl_tanshin_self2_2026-11-14.py interim --out PATH [--material DIR] [--procs N]                       # 中間 150 本(丙)に期の名前の置き換えを掛けて P33E で判定 → states_interim_2026-11-14.json
    python3 measure/xbrl_tanshin_self2_2026-11-14.py near --interim PATH --out PATH [--material DIR] [--procs N]           # A を写さずにもう 1 回・B を写して、近い行を拾う → near_2026-11-14.json
    python3 measure/xbrl_tanshin_self2_2026-11-14.py sheet --near PATH --material DIR --sheet PATH                           # 近い行(200 行以下は全部)の文・span・値・結んだ先を repo の外の紙に書く(標準出力は件数だけ)
    python3 measure/xbrl_tanshin_self2_2026-11-14.py types --near PATH --typed PATH --out PATH                               # 付けた型(あ〜お)の file を確かめて near_types_2026-11-14.json を書く

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めはここに書き、報告にも書いた):
- 母集団(封 §1): TSS の記録 ``population_2026-11-14.json`` の行 [#, 群, 様式の種類, sha256] を読み、TSS の封の表(``ST.read_population``)と **行ごとに** 同じでなければ止める(「sha256 が 1 つでも違えば止める」= この比べ)。
  材料の ZIP は、読むたびに sha256 が表と同じか確かめる(TSS と同じ)。TSS の判定の記録 ``states_2026-11-14.json`` を読むときは、本の ``ZIP の sha256`` が母集団と同じかも確かめる。
- 置き換え(封 §0-2 の 2): 中間(群 丙)だけ。TSS の ``wrap`` は変えず、``wrap`` が入れる member(``XBRLData/Attachment/`` の下で file 名が ``-ixbrl.htm`` で終わるもの。TSS の定数で判定)の byte 列にだけ 3 つの置き換えを
  **この順で**掛けた ZIP' を memory の中で作り、ZIP' を TSS の ``judge_book``(= TSS の ``cut`` と ``wrap``)に渡す。ZIP' のほかの member(文の元の file・サマリー)は 1 byte も変えない。
  3 つの置き換えは互いの出力に当たらない(``"InterimDuration`` は ``"Prior1InterimDuration`` の中に無い)ので、順を入れ替えても出力は変わらない。順は定数(``REPLACEMENTS``)の並びで留める。
- 名前がぶつかる本: 置き換える前の、``wrap`` が入れる member の byte 列のどれかに ``"CurrentYearDuration``・``"CurrentYearInstant``・``"Prior1YearDuration`` が在る本。切れない本も数える(``名前がぶつかる``)。
  ぶつかる本は ZIP をそのまま TSS の判定に渡す(写さない)。``写した`` = 切れた かつ ぶつからない本。``置き換えた回数`` は ``写した`` 本だけが持つ [規則 1・2・3 が当たった回数](診断用の欄で、封の予測には使わない。写さない本は 0)。
- 4 × 4 の動き: TSS の B の記録の本と、写した判定の本を # で結び、行を (文の番号, 位置) で結んで 4 state の遷移を数える。どちらかにしか無い行・切り出しの結果が違う本は別に数える(切り出しが違えば止める)。
- A の確かめ(封 §0-2 の 3・§2 の 3): ``near`` が A(甲・乙)を写さずにもう 1 回判定し、本ごとに行の (文の番号, 位置, state) の並びが TSS の記録と同じかを数える。違う本が 1 つでも在れば記録を書かずに止める。
  B も同じく、今回の判定が ``interim`` の記録と行ごとに同じでなければ止める。``interim`` の記録を作った script の sha256 が今の script と違っても止める。
- 近い行の規則(封 §0-2 の 4): 数は **repr の 10 進の字で厳密に(分数で)比べる**(float の誤差で「ちょうど 2%」「ちょうど 0.5」が外れない)。bool・nan・inf は数でない。
  N-円: ``0 < |c − f| / f ≤ 2%`` を ``c ≠ f かつ 50×|c − f| ≤ f``(f > 0)で見る。N-率: ``unit == "%"`` だけ(「ポイント」は入れない)で ``0 < ||v| − |r|| ≤ 1/2``。
  N-桁: ``v`` が整数(分母が 1)・``form == "direct_value"``・円の族。``a`` = ``|v|`` の整数の字。``b`` は ``floor(f / m)`` の字と「四捨五入(0.5 は切り上げ = ``floor(x + 1/2)``)した ``f / m``」の字の **両方**を試す。
  Python の ``round``(銀行丸め)は使わない。桁数が同じで 3 以上・``a ≠ b`` で、違う桁がちょうど 1 つ、または違う桁がとなり合う 2 つで中身が入れ替わっている、のどちらか。
- 行の数え: 「近い行」の母集団は A と B の VALUE_MISMATCH のうち ``recomputed`` が数の行。``recomputed`` が数でない行の数は別に数える。
- 近い行の並び(封 §0-2 の 5): 本の # の順(= A が先)・文の番号・位置。200 行以下なら全部、超えたら ``TSS.pick_sample(行の数, seed=20261115, k=200)``(``random.Random(種).sample(range(行の数), 200)`` を番号の順)。
- 紙(``sheet``): TSS の ``sheet_text`` に、群と当たった規則の 1 行を足したもの。紙の出力先が repo / git の木の中なら止める(TSS の ``inside_repo``)。
- 記録は値・文・span・pointer の字・要素名・会社名・証券コードを持たない。近い行の行は [本の #, 文の番号, 位置, 当たった規則, 単位の族] だけ。時間(秒)は記録の中で 1 つの欄。ほかは 2 回走らせて byte で同じになる。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import math
import os
import re
import sys
import time
import zipfile
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    u"""importlib で読み込む。読み込んだ file が中で読む前の便の script は決まった名前で ``sys.modules`` に登録し直して先に居た module を上書きする。
    読み込みの前に居た名前は、読み込みの後に元の object へ戻す(自分の名前 ``mod_name`` は残す)。"""
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != mod_name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


TSS = load_module("xbrl_tanshin_self_2026-11-14.py", "tanshin_self_for_tanshin_self2")                 # 第 1 便の script(切り出し・包み直し・判定・標本・止め方)
ST = TSS.ST                                                                                              # 置く script(同じ instance)
TS = TSS.TS                                                                                              # 2026-11-09 の便
Stop = ST.Stop

from adapters.xbrl import verify_document as VD         # noqa: E402
from adapters.xbrl import vocabulary as V               # noqa: E402

SEAL_REL = "docs/XBRL_TANSHIN_SELF2_SEAL_2026-11-14.md"
SEAL_COMMIT = "a1fd09bf"
SCRIPT_REL = "measure/xbrl_tanshin_self2_2026-11-14.py"
TSS_SCRIPT_REL = TSS.SCRIPT_REL
TSS_SEAL_REL = TSS.SEAL_REL
REC_DIR_REL = ST.REC_DIR_REL
INTERIM_REL = REC_DIR_REL + "/states_interim_2026-11-14.json"
NEAR_REL = REC_DIR_REL + "/near_2026-11-14.json"
NEAR_TYPES_REL = REC_DIR_REL + "/near_types_2026-11-14.json"
TSS_STATES_REL = TSS.STATES_REL
DOC_REL = "docs/XBRL_TANSHIN_SELF2_RESULT_2026-11-14.md"
PRODUCTION_RELS = (INTERIM_REL, NEAR_REL)

# ---- 封 §0-2 の決めごと(字で留める。門が封と照らす)
PROFILE = TSS.PROFILE
#: 封 §0-2 の 2 の 3 つの置き換え(二重引用符から始まる byte 列。この順)
REPLACEMENTS = ((b'"Prior1InterimDuration', b'"Prior1YearDuration'),
                (b'"InterimDuration', b'"CurrentYearDuration'),
                (b'"InterimInstant', b'"CurrentYearInstant'))
#: 置き換える前の byte 列にこれが在る本は「名前がぶつかる本」(写さない)
COLLISION_MARKS = (b'"CurrentYearDuration', b'"CurrentYearInstant', b'"Prior1YearDuration')
INTERIM_GROUPS = TSS.B_GROUPS
A_GROUPS = TSS.A_GROUPS
B_GROUPS = TSS.B_GROUPS
STATES = TSS.STATES
G, VM, UNV, PNF = STATES
# ---- 封 §0-2 の 4 の近い行の規則
#: N-円・N-桁の単位と倍率(円・千円・万円・百万円・億円・兆円)
YEN_UNITS = collections.OrderedDict([(u"円", 1), (u"千円", 10 ** 3), (u"万円", 10 ** 4), (u"百万円", 10 ** 6), (u"億円", 10 ** 8), (u"兆円", 10 ** 12)])
YEN_BAND = Fraction(2, 100)                     # N-円: |c − f| / f の上限(2%)
PCT_BAND = Fraction(1, 2)                       # N-率: ||v| − |r|| の上限(0.5)
MIN_DIGITS = 3                                  # N-桁: 桁数の下限
RULES = (u"N-円", u"N-桁", u"N-率")
# ---- 封 §0-2 の 5(近い行を読む)
SAMPLE_SEED = 20261115
SAMPLE_N = 200
#: 型(封 §0-2 の 5。字は封と同じ)
TYPES = collections.OrderedDict([
    (u"あ", u"本当の差の候補(文がその項目・その期・その範囲の数を言っていて、同じ短信の財務諸表の値と違って見える)"),
    (u"い", u"別の項目・一部分・別の期・定義の違い(セグメント、内訳、文の中で計算した率や差 など)"),
    (u"う", u"計画・予想・目標の数"),
    (u"え", u"丸め・単位・符号"),
    (u"お", u"読んでも分けられない")])
TYPED_BY = TSS.TYPED_BY

INTERIM_LIMITS = (
    u"標本は英文短信を出している会社の中間 150 本で、上場会社全体の率ではない(封 §6)",
    u"期の名前を写すのは measure/ の側の包み直しで、engine の読みそのものではない。前年の中間期末(Prior1InterimInstant)は写していない",
    u"engine の期の手がかりの語は通期の文に合わせてある。中間の文の「前年同期」「前中間連結会計期間」で前期の fact を選べているかは、この記録からは分けられない",
    u"切れない本は測れていない(見出しの書き方の違い。規則は広げない)",
    u"誤りを通す率は測っていない",
    u"行は TSS の記録と同じ形 [文の番号, 位置, state, reason, pointer の期, formula の有無, 単位の族, 両期の fact を引く a−b, span に % を含む] で、文・span・値・要素名は持たない")
NEAR_LIMITS = (
    u"近い行の規則は読む順を決めるだけで、engine の判定は 1 行も変えない。規則の外に在る本当の差は数えない",
    u"規則の幅(2%・0.5 ポイント・1 桁)は司令塔が行を読む前に決めた値で、最良の値かは測っていない",
    u"A は写さない(TSS と同じ包み直し)・B は期の名前を写した判定。A と B を足した数は、ほかの便の数と足さない",
    u"記録は本の #・文の番号・位置・当たった規則・単位の族だけを持つ。値・文・span・pointer の字・要素名は持たない",
    u"型を付けるのは司令塔(AI の席)1 席で、盲検ではない。人は読んでいない。(あ)は候補で、紙面で人が確かめるまで食い違いと呼ばない")
NEAR_ROW_COLUMNS = (u"本の #", u"文の番号", u"位置", u"当たった規則", u"単位の族")


# ======================================================================================================
# 近い行の規則(封 §0-2 の 4)。数は repr の 10 進の字から分数にして厳密に比べる
def is_number(x):
    u"""bool でない int・float(有限)。"""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return False
    return isinstance(x, int) or math.isfinite(x)


def exact(x):
    return Fraction(repr(x))


def digits_close(a, b):
    u"""``a``・``b`` は数字の字。桁数が同じで 3 以上・``a ≠ b`` で、違う桁がちょうど 1 つ、または違う桁がとなり合う 2 つで中身が入れ替わっている。"""
    if len(a) != len(b) or len(a) < MIN_DIGITS or a == b:
        return False
    diff = [i for i in range(len(a)) if a[i] != b[i]]
    if len(diff) == 1:
        return True
    return len(diff) == 2 and diff[1] == diff[0] + 1 and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]


def near_rules(value, unit, form, recomputed):
    u"""近い行の規則に当たったものの名前の列(``RULES`` の順)。``recomputed`` が数でなければ空。"""
    if not is_number(value) or not is_number(recomputed):
        return []
    v, r = exact(value), exact(recomputed)
    out = []
    m = YEN_UNITS.get(unit)
    if m is not None:
        c, f = abs(v) * m, abs(r)
        if f > 0 and c != f and abs(c - f) <= f * YEN_BAND:
            out.append(RULES[0])
        if form == u"direct_value" and v.denominator == 1:
            a = u"%d" % abs(int(v))
            fm = f / m
            floor_b = u"%d" % (fm.numerator // fm.denominator)
            half = fm + Fraction(1, 2)
            half_b = u"%d" % (half.numerator // half.denominator)
            if digits_close(a, floor_b) or digits_close(a, half_b):
                out.append(RULES[1])
    if unit == u"%":
        d = abs(abs(v) - abs(r))
        if 0 < d <= PCT_BAND:
            out.append(RULES[2])
    return [x for x in RULES if x in out]


# ======================================================================================================
# 期の名前の置き換え(封 §0-2 の 2)。包んだ ZIP ではなく、TSS の包み直しに渡す前の ZIP' を memory の中で作る
def is_wrapped_member(name):
    u"""TSS の ``wrap`` が包み直しに入れる member(TSS の定数と同じ判定)。"""
    base = name.rsplit(u"/", 1)[-1]
    return name.startswith(TSS.ATTACH_PREFIX) and base.endswith(TSS.OLD_SUFFIX)


def collides(data):
    return any(m in data for m in COLLISION_MARKS)


def rewrite_zip(zb):
    u"""(ZIP' の bytes, 名前がぶつかるか, 3 つの置き換えが当たった回数の列)。ぶつかるなら ZIP をそのまま返す。
    置き換えを掛けるのは ``is_wrapped_member`` の byte 列だけ(順に ``REPLACEMENTS``)。ほかの member・member の順・名前は変えない。"""
    try:
        with zipfile.ZipFile(io.BytesIO(zb)) as z:
            members = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    except zipfile.BadZipFile:
        raise Stop(u"**ZIP として読めない。止める**")
    if any(collides(d) for nm, d in members if is_wrapped_member(nm)):
        return zb, True, [0] * len(REPLACEMENTS)
    counts = [0] * len(REPLACEMENTS)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for nm, d in members:
            if is_wrapped_member(nm):
                for k, (old, new) in enumerate(REPLACEMENTS):
                    counts[k] += d.count(old)
                    d = d.replace(old, new)
            zi = zipfile.ZipInfo(nm, date_time=TSS.ZIP_DATE_TIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            out.writestr(zi, d)
    return buf.getvalue(), False, counts


def prepare(zb, replace):
    u"""(判定に渡す ZIP, ぶつかる, 回数)。``replace`` が偽なら ZIP を変えない(ぶつかるかは見ない)。"""
    if not replace:
        return zb, False, [0] * len(REPLACEMENTS)
    return rewrite_zip(zb)


def judge2(n, grp, kind, sha, zb, replace):
    u"""(本の記録, 判定に渡した ZIP)。記録は TSS の ``judge_book`` の記録に ``名前がぶつかる``・``写した``・``置き換えた回数`` を足したもの。"""
    zb2, hit, counts = prepare(zb, replace)
    book = TSS.judge_book(n, grp, kind, sha, zb2)
    book[u"名前がぶつかる"] = hit
    book[u"写した"] = bool(replace and not hit and book[u"切り出し"] == TSS.CUT_OK)
    book[u"置き換えた回数"] = counts if book[u"写した"] else [0] * len(REPLACEMENTS)
    return book, zb2


def read_material(n, sha, path):
    if not os.path.exists(path):
        raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める(置く script を先に)**" % n)
    with io.open(path, "rb") as fh:
        zb = fh.read()
    if ST.sha256_bytes(zb) != sha:
        raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % n)
    return zb


# ======================================================================================================
# 母集団・TSS の記録
def load_population(root=ROOT):
    u"""TSS の記録の行 [#, 群, 様式の種類, sha256] を読み、TSS の封の表と行ごとに同じでなければ止める。"""
    rec = TSS.load_json(os.path.join(root, ST.POPULATION_REL))
    rows = [tuple(r[:4]) for r in rec[u"行"]]
    pop = ST.validate_population(rows)
    if [tuple(r) for r in pop] != [tuple(r) for r in ST.read_population(root)]:
        raise Stop(u"**TSS の記録の母集団が TSS の封の表と違う。止める**")
    return pop


def load_tss_states(root, pop, path=None):
    u"""TSS の判定の記録の本 {#: 本}。本の ``ZIP の sha256`` が母集団と違えば止める。"""
    rec = TSS.load_json(path or os.path.join(root, TSS_STATES_REL))
    books = dict((b[u"#"], b) for b in rec[u"本"])
    if sorted(books) != [r[0] for r in pop] or any(books[r[0]][u"ZIP の sha256"] != r[3] for r in pop):
        raise Stop(u"**TSS の判定の記録の本が母集団と合わない。止める**")
    return books


def material_dir(material, out, root=ROOT):
    u"""材料の置き場。既定は本番の folder。本番の記録を書くときは本番の folder でなければ止める。"""
    prod = os.path.abspath(ST.default_cache_dir())
    mat = os.path.abspath(material) if material else prod
    if os.path.abspath(out) in [os.path.abspath(os.path.join(root, rel)) for rel in PRODUCTION_RELS] and mat != prod:
        raise Stop(u"**本番の記録を使い捨ての材料から作らない。止める**")
    return mat, mat == prod


def check_clean(rec, text, key_value=None):
    u"""記録に repo へ入れない欄・鍵らしい字が無いか(あれば止める)。封・TSS の封の path は長い英数字なので外して見る。"""
    bad = sorted(set(k for k in TS.RUN.walk_keys(rec) if k in TS.RUN.FORBIDDEN_KEYS))
    if bad:
        raise Stop(u"**記録に repo へ入れない欄がある: %s。止める**" % u",".join(bad))
    leaks = ST.key_leaks(text.replace(SEAL_REL, u"").replace(TSS_SEAL_REL, u""), key_value)
    if leaks:
        raise Stop(u"**鍵らしい字が記録に在る(%s)。書かずに止める**" % u" / ".join(sorted(set(leaks))))


def head_fields(rec, root, step, mat, prod, pop, before, after):
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = step
    rec[u"HEAD の commit"] = ST.git_head(root)
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"TSS の script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(TSS_SCRIPT_REL)))
    rec[u"置く script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(TSS.STAGE_SCRIPT_REL)))
    rec[u"2026-11-09 の便の script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(TSS.TS_SCRIPT_REL)))
    rec[u"engine の指紋"] = VD.engine_fingerprint()
    rec[u"profile"] = PROFILE
    rec[u"材料"] = collections.OrderedDict([
        (u"置き場", ST.display_path(mat) if prod else u"使い捨ての置き場(本番の folder ではない)"), (u"表と一致した ZIP", len(pop)),
        (u"置き場の一覧の前後", collections.OrderedDict([(u"前", list(before)), (u"後", list(after)), (u"変化なし", before == after)]))])


# ======================================================================================================
# interim(封 §0-2 の 2・§2 の 1・2)
def interim_job(args):
    n, grp, kind, sha, path = args
    zb = read_material(n, sha, path)
    return judge2(n, grp, kind, sha, zb, True)[0]


def moves(tss_books, new_books):
    u"""TSS の B の記録の本(写さない)と写した判定の本を # で結び、行を (文の番号, 位置) で結んだ 4 × 4 の遷移。切り出しの結果が違えば止める。"""
    table = collections.OrderedDict((s, collections.OrderedDict((t, 0) for t in STATES)) for s in STATES)
    only_old = only_new = 0
    for b in new_books:
        o = tss_books[b[u"#"]]
        if o[u"切り出し"] != b[u"切り出し"]:
            raise Stop(u"**写す前と後で切り出しの結果が違う本がある(# %d)。止める**" % b[u"#"])
        orow = dict(((r[0], r[1]), r[2]) for r in o[u"行"])
        nrow = dict(((r[0], r[1]), r[2]) for r in b[u"行"])
        for k, s in orow.items():
            if k in nrow:
                table[s][nrow[k]] += 1
            else:
                only_old += 1
        only_new += sum(1 for k in nrow if k not in orow)
    moved = sum(table[s][t] for s in STATES for t in STATES if s != t)
    return collections.OrderedDict([
        (u"行(写す前 → 写した後)", table), (u"動いた行", moved), (u"GROUNDED だった行のうち GROUNDED でなくなった行", sum(table[G][t] for t in STATES if t != G)),
        (u"写す前にだけ在る行", only_old), (u"写した後にだけ在る行", only_new)])


def run_interim(root=ROOT, procs=1, out=None, material=None, say=print, population=None, tss_states=None, key_value=None, clock=time.time, shape=None):
    if out is None:
        raise Stop(u"**--out を指定する。止める**")
    out = os.path.abspath(out)
    mat, prod = material_dir(material, out, root)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    pop = population if population is not None else load_population(root)
    if shape is not None:
        pop = ST.validate_population(pop, *shape)
    tss_books = tss_states if tss_states is not None else load_tss_states(root, pop)
    sel = [r for r in pop if r[1] in INTERIM_GROUPS]
    for (n, _g, _k, sha) in sel:
        if not os.path.exists(os.path.join(mat, sha + u".zip")):
            raise Stop(u"**材料の ZIP が置き場に無い(# %d)。何も書かずに止める(置く script を先に)**" % n)
    before = ST.names_snapshot(mat)
    jobs = [(n, g, k, sha, os.path.join(mat, sha + u".zip")) for (n, g, k, sha) in sel]
    say(u"interim %d 本 × %s ― procs %d" % (len(jobs), PROFILE, procs))
    t0 = clock()
    books = TS.NF.map_pool(interim_job, jobs, procs)
    elapsed = clock() - t0
    after = ST.names_snapshot(mat)
    if before != after:
        raise Stop(u"**材料の置き場の件数か名前が変わった。記録を書かずに止める**")
    rec = collections.OrderedDict()
    head_fields(rec, root, u"TSS 第 2 便(一)― 中間 150 本の期の名前を写した判定(0 USD・通信なし)", mat, prod, pop, before, after)
    rec[u"置き換え(この順。二重引用符から始まる byte 列)"] = [[old.decode("ascii"), new.decode("ascii")] for old, new in REPLACEMENTS]
    rec[u"置き換えを掛ける member"] = u"TSS の包み直しが入れる member(%s の下で file 名が %s で終わるもの)だけ。文の block・サマリーは TSS のまま" % (TSS.ATTACH_PREFIX, TSS.OLD_SUFFIX)
    rec[u"名前がぶつかる印(置き換える前に在れば写さない)"] = [m.decode("ascii") for m in COLLISION_MARKS]
    rec[u"本の数"] = len(books)
    rec[u"名前がぶつかる本"] = sum(1 for b in books if b[u"名前がぶつかる"])
    rec[u"名前がぶつかる本のうち切れた本"] = sum(1 for b in books if b[u"名前がぶつかる"] and b[u"切り出し"] == TSS.CUT_OK)
    rec[u"写した本"] = sum(1 for b in books if b[u"写した"])
    rec[u"置き換えた回数の合計(規則 1・2・3)"] = [sum(b[u"置き換えた回数"][k] for b in books) for k in range(len(REPLACEMENTS))]
    rec[u"集計"] = TSS.block(books)
    rec[u"TSS の B(写さない)との動き"] = moves(tss_books, books)
    rec[u"限界"] = list(INTERIM_LIMITS)
    rec[u"行の欄"] = list(TSS.ROW_COLUMNS)
    rec[u"時間(秒)"] = round(elapsed, 1)
    rec[u"key_leaks"] = []
    rec[u"本"] = books
    text = TS.dumps_states(rec)
    check_clean(rec, text, key_value)
    ST.write_text_exclusive(out, text)
    say(u"-> %s(本 %d)" % (os.path.basename(out), len(books)))
    return rec


# ======================================================================================================
# near(封 §0-2 の 4・§2 の 3・4)
def claims_of(wrapped):
    u"""(claim の列, raw の列)。並びが対応しなければ止める。"""
    nums, texts = TS.R.build_raw_claims(wrapped, V.PROFILES[PROFILE])
    raws = nums + texts
    cl = VD.verify_document(wrapped, PROFILE)["claims"]
    if len(cl) != len(raws) or any(c["id"] != r["id"] for c, r in zip(cl, raws)):
        raise Stop(u"**claim と raw の並びが対応しない。止める**")
    return cl, raws


def near_of_book(zb2):
    u"""判定に渡した ZIP' から (VALUE_MISMATCH の行, そのうち recomputed が数でない行, 近い行 [[文の番号, 位置, [規則], 単位の族]])。切れない本は (0, 0, [])。"""
    text, _h, _why = TSS.cut(zb2)
    if text is None:
        return 0, 0, []
    wrapped, _nf = TSS.wrap(zb2, text)
    cl, raws = claims_of(wrapped)
    vm = nonnum = 0
    rows = []
    for c, r in zip(cl, raws):
        if c["kind"] != "num" or c["state"] != VM:
            continue
        vm += 1
        if not is_number(c.get("recomputed")):
            nonnum += 1
            continue
        rules = near_rules(c["value"], c["unit"], c["form"], c["recomputed"])
        if rules:
            rows.append([r["sentence"], r["pos"], rules, TS.unit_family(c["unit"])])
    return vm, nonnum, sorted(rows, key=lambda x: (x[0], x[1]))


def near_job(args):
    n, grp, kind, sha, path = args
    zb = read_material(n, sha, path)
    book, zb2 = judge2(n, grp, kind, sha, zb, grp in B_GROUPS)
    vm, nonnum, rows = near_of_book(zb2)
    rows_vm = sum(1 for r in book[u"行"] if r[2] == VM)
    if rows_vm != vm:
        raise Stop(u"**判定の行の VALUE_MISMATCH の数と claim から数えた数が違う(# %d)。止める**" % n)
    return book, vm, nonnum, rows


def triples(book):
    return [(r[0], r[1], r[2]) for r in book[u"行"]]


def same_states(mine, ref, label):
    u"""{#: 本} と {#: 本} を、本ごとに行の (文の番号, 位置, state) の並びで比べる。(本の数, 行の数, 違う本の数)。"""
    diff = rows = 0
    for n, b in mine.items():
        rows += len(b[u"行"])
        if triples(b) != [tuple(t) for t in triples(ref[n])]:
            diff += 1
    return collections.OrderedDict([(u"本", len(mine)), (u"行", rows), (u"違う本", diff)])


def group_block(books, near_by_book, vm_by_book, nonnum_by_book):
    u"""群ごと(A・B)の集計。行から数える。"""
    rows = [(n, r) for b in books for n in [b[u"#"]] for r in near_by_book[n]]
    per_rule = collections.OrderedDict((k, sum(1 for _n, r in rows if k in r[2])) for k in RULES)
    per_rule_books = collections.OrderedDict((k, len(set(n for n, r in rows if k in r[2]))) for k in RULES)
    return collections.OrderedDict([
        (u"本", len(books)), (u"VALUE_MISMATCH の行", sum(vm_by_book[b[u"#"]] for b in books)),
        (u"うち recomputed が数でない行", sum(nonnum_by_book[b[u"#"]] for b in books)),
        (u"近い行", len(rows)), (u"規則ごとの行の数", per_rule), (u"規則ごとの 1 行以上持つ本の数", per_rule_books),
        (u"近い行を 1 行以上持つ本", len(set(n for n, _r in rows)))])


def run_near(root=ROOT, procs=1, interim=None, out=None, material=None, say=print, population=None, tss_states=None, key_value=None, clock=time.time, shape=None):
    if out is None or interim is None:
        raise Stop(u"**--interim と --out を指定する。止める**")
    out = os.path.abspath(out)
    mat, prod = material_dir(material, out, root)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    pop = population if population is not None else load_population(root)
    if shape is not None:
        pop = ST.validate_population(pop, *shape)
    tss_books = tss_states if tss_states is not None else load_tss_states(root, pop)
    irec = TSS.load_json(interim)
    if irec.get(u"この script の sha256") != ST.sha256_file(os.path.abspath(__file__)):
        raise Stop(u"**interim の記録が別の script で作られている。止める**")
    ibooks = dict((b[u"#"], b) for b in irec[u"本"])
    if sorted(ibooks) != [r[0] for r in pop if r[1] in B_GROUPS]:
        raise Stop(u"**interim の記録の本が母集団の丙と合わない。止める**")
    for (n, _g, _k, sha) in pop:
        if not os.path.exists(os.path.join(mat, sha + u".zip")):
            raise Stop(u"**材料の ZIP が置き場に無い(# %d)。何も書かずに止める(置く script を先に)**" % n)
    before = ST.names_snapshot(mat)
    jobs = [(n, g, k, sha, os.path.join(mat, sha + u".zip")) for (n, g, k, sha) in pop]
    say(u"near %d 本 × %s ― procs %d" % (len(jobs), PROFILE, procs))
    t0 = clock()
    res = TS.NF.map_pool(near_job, jobs, procs)
    elapsed = clock() - t0
    after = ST.names_snapshot(mat)
    if before != after:
        raise Stop(u"**材料の置き場の件数か名前が変わった。記録を書かずに止める**")
    books = [r[0] for r in res]
    vm_by = dict((r[0][u"#"], r[1]) for r in res)
    nonnum_by = dict((r[0][u"#"], r[2]) for r in res)
    near_by = dict((r[0][u"#"], r[3]) for r in res)
    a_books = [b for b in books if b[u"群"] in A_GROUPS]
    b_books = [b for b in books if b[u"群"] in B_GROUPS]
    a_same = same_states(dict((b[u"#"], b) for b in a_books), tss_books, u"A")
    b_same = same_states(dict((b[u"#"], b) for b in b_books), ibooks, u"B")
    if a_same[u"違う本"] or b_same[u"違う本"]:
        raise Stop(u"**もう 1 回走らせた行の state が記録と違う(A %d 本・B %d 本)。記録を書かずに止める**" % (a_same[u"違う本"], b_same[u"違う本"]))
    rows = [[n] + near_by[n][i] for n in sorted(near_by) for i in range(len(near_by[n]))]
    picked = TSS.pick_sample(len(rows), seed=SAMPLE_SEED, k=SAMPLE_N)
    rec = collections.OrderedDict()
    head_fields(rec, root, u"TSS 第 2 便(二)― 「値が違う」のうち表の値に近い行(0 USD・通信なし)", mat, prod, pop, before, after)
    rec[u"interim の記録の sha256"] = ST.sha256_file(os.path.abspath(interim))
    rec[u"TSS の判定の記録の sha256"] = ST.sha256_file(os.path.join(root, TSS_STATES_REL)) if tss_states is None else None
    rec[u"規則"] = collections.OrderedDict([
        (u"対象", u"A(写さない)と B(期の名前を写した)の VALUE_MISMATCH の行のうち recomputed が数である行"),
        (u"N-円", u"unit が 円・千円・万円・百万円・億円・兆円。c = |v| × 倍率、f = |r|。f > 0 かつ 0 < |c − f| / f ≤ 2%"),
        (u"N-桁", u"N-円と同じ unit・form が direct_value・v が整数。|v| の整数の字 a と、floor(f / 倍率) または 四捨五入(0.5 は切り上げ)した f / 倍率 の字 b が、桁数が同じで 3 桁以上、かつ ちょうど 1 桁違う または となり合う 2 桁の入れ替わり"),
        (u"N-率", u"unit が %。0 < ||v| − |r|| ≤ 0.5"),
        (u"数の比べ方", u"repr の 10 進の字から分数にして厳密に比べる")])
    rec[u"母集団の本"] = collections.OrderedDict([(u"A", len(a_books)), (u"B", len(b_books))])
    rec[u"A の state が TSS の記録と同じか"] = a_same
    rec[u"B の state が interim の記録と同じか"] = b_same
    rec[u"集計"] = collections.OrderedDict([(u"A(甲 + 乙)", group_block(a_books, near_by, vm_by, nonnum_by)), (u"B(丙)", group_block(b_books, near_by, vm_by, nonnum_by))])
    rec[u"近い行の数(A と B)"] = len(rows)
    rec[u"読む行の規則"] = collections.OrderedDict([(u"種", SAMPLE_SEED), (u"標本の数", SAMPLE_N), (u"近い行の数", len(rows)), (u"読む行の数", len(picked)),
                                           (u"引き方", u"200 行以下なら全部。超えたら random.Random(種).sample(range(行の数), 200) を番号の順に")])
    rec[u"限界"] = list(NEAR_LIMITS)
    rec[u"行の欄"] = list(NEAR_ROW_COLUMNS)
    rec[u"時間(秒)"] = round(elapsed, 1)
    rec[u"key_leaks"] = []
    rec[u"行"] = rows
    text = ST.dumps_record(rec)
    check_clean(rec, text, key_value)
    ST.write_text_exclusive(out, text)
    say(u"-> %s(近い行 %d)" % (os.path.basename(out), len(rows)))
    return rec


# ======================================================================================================
# sheet・types(封 §0-2 の 5)
def near_items(near_rec):
    u"""[(標本の番号(1 から), 本の #, 文の番号, 位置)]。近い行を # の順・文の番号の順・位置の順に並べ、200 行以下なら全部、超えたら種 20261115 で 200 行。"""
    rows = near_rec[u"行"]
    picked = TSS.pick_sample(len(rows), seed=SAMPLE_SEED, k=SAMPLE_N)
    return [(i + 1, rows[j][0], rows[j][1], rows[j][2]) for i, j in enumerate(picked)]


def run_sheet(near_path, material, sheet, root=ROOT, say=print, repo=None, population=None):
    if TSS.inside_repo(sheet, repo):
        raise Stop(u"**--sheet が repo の中(または git の木の中)。文を持つ紙は repo の外に書く。止める**")
    sheet = os.path.abspath(sheet)
    if os.path.exists(sheet):
        raise Stop(u"**--sheet が既に在る。止める**")
    rec = TSS.load_json(near_path)
    items = near_items(rec)
    rule_of = dict(((r[0], r[1], r[2]), r[3]) for r in rec[u"行"])
    pop = dict((r[0], r) for r in (population if population is not None else load_population(root)))
    mat = os.path.abspath(material)
    by_book = collections.OrderedDict()
    for it in items:
        by_book.setdefault(it[1], []).append(it)
    chunks = {}
    for num, its in by_book.items():
        _n, grp, _k, sha = pop[num]
        zb = read_material(num, sha, os.path.join(mat, sha + u".zip"))
        zb2, _hit, _counts = prepare(zb, grp in B_GROUPS)
        text, _h, _why = TSS.cut(zb2)
        if text is None:
            raise Stop(u"**標本の本が切れない(# %d)。記録と合わない。止める**" % num)
        wrapped, _nf = TSS.wrap(zb2, text)
        cl, raws = claims_of(wrapped)
        sents = TS.RUN.sentence_list(wrapped, V.PROFILES[PROFILE])
        keyed = dict(((r["sentence"], r["pos"]), c) for c, r in zip(cl, raws) if c["kind"] == "num")
        for it in its:
            c = keyed.get((it[2], it[3]))
            want = rule_of[(it[1], it[2], it[3])]
            if c is None or c["state"] != VM or near_rules(c["value"], c["unit"], c["form"], c.get("recomputed")) != want:
                raise Stop(u"**近い行が記録と合わない(標本 %d)。止める**" % it[0])
            head, rest = TSS.sheet_text(it, c, sents[it[2]]).split(u"\n", 1)
            chunks[it[0]] = head + u"\n" + u"群: %s  当たった規則: %s\n" % (u"A" if grp in A_GROUPS else u"B", u" , ".join(want)) + rest
    d = os.path.dirname(sheet)
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(sheet, "w", encoding="utf-8", newline="") as fh:
        fh.write(u"".join(chunks[it[0]] + u"\n" for it in items))
    say(u"近い行 %d・読む行 %d・本 %d" % (len(rec[u"行"]), len(items), len(by_book)))
    return items


def read_typed(path):
    u"""1 行に「標本の番号 TAB 型の字」。{番号: 型}。形が違う・番号が重なる・型が 5 つの外なら止める。"""
    out = {}
    with io.open(path, encoding="utf-8") as fh:
        for ln in fh.read().split(u"\n"):
            if not ln.strip():
                continue
            parts = ln.rstrip(u"\r").split(u"\t")
            if len(parts) != 2 or not re.fullmatch(r"[0-9]+", parts[0]) or parts[1] not in TYPES:
                raise Stop(u"**型の file の行が「番号 TAB 型の字(あ〜お)」でない。止める**")
            k = int(parts[0])
            if k in out:
                raise Stop(u"**型の file に同じ標本の番号が 2 行ある。止める**")
            out[k] = parts[1]
    return out


def run_types(near_path, typed_path, out, root=ROOT, say=print, key_value=None, population=None):
    out = os.path.abspath(out)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。止める**" % os.path.basename(out))
    rec_near = TSS.load_json(near_path)
    items = near_items(rec_near)
    typed = read_typed(typed_path)
    if sorted(typed) != [it[0] for it in items]:
        raise Stop(u"**型の file の標本の番号が読む行(%d 行)とそろわない。止める**" % len(items))
    group = dict((r[0], r[1]) for r in (population if population is not None else load_population(root)))
    counts = collections.Counter(typed.values())
    by_group = dict((g, collections.Counter(typed[it[0]] for it in items if group[it[1]] in gs)) for g, gs in ((u"A", A_GROUPS), (u"B", B_GROUPS)))
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"TSS 第 2 便(二)― 近い行を読んだ型分け(0 USD)"
    rec[u"HEAD の commit"] = ST.git_head(root)
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"near の記録の sha256"] = ST.sha256_file(os.path.abspath(near_path))
    rec[u"型を付けた席"] = TYPED_BY
    rec[u"盲検"] = u"盲検ではない(封の予測を知ったうえで付けた)。(あ)は候補で、紙面で確かめていない"
    rec[u"読む行の規則"] = collections.OrderedDict([
        (u"母集団", u"A と B の近い行を、本の # の順・文の番号の順・位置の順に並べた"), (u"種", SAMPLE_SEED),
        (u"引き方", u"200 行以下なら全部。超えたら random.Random(種).sample(range(行の数), 200) を番号の順に"),
        (u"近い行の数", len(rec_near[u"行"])), (u"読む行の数", len(items))])
    rec[u"型の字"] = collections.OrderedDict(TYPES)
    rec[u"型の集計"] = collections.OrderedDict((t, counts.get(t, 0)) for t in TYPES)
    rec[u"型の集計(A)"] = collections.OrderedDict((t, by_group[u"A"].get(t, 0)) for t in TYPES)
    rec[u"型の集計(B)"] = collections.OrderedDict((t, by_group[u"B"].get(t, 0)) for t in TYPES)
    rec[u"行の欄"] = [u"標本の番号", u"本の #", u"文の番号", u"位置", u"型"]
    rec[u"行"] = [[it[0], it[1], it[2], it[3], typed[it[0]]] for it in items]
    rec[u"key_leaks"] = []
    text = ST.dumps_record(rec)
    check_clean(rec, text, key_value)
    ST.write_text_exclusive(out, text)
    say(u"-> %s(読んだ行 %d)" % (os.path.basename(out), len(items)))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("interim")
    a.add_argument("--root", default=ROOT)
    a.add_argument("--out", required=True)
    a.add_argument("--material", default=None)
    a.add_argument("--procs", type=int, default=1)
    b = sub.add_parser("near")
    b.add_argument("--root", default=ROOT)
    b.add_argument("--interim", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--material", default=None)
    b.add_argument("--procs", type=int, default=1)
    c = sub.add_parser("sheet")
    c.add_argument("--root", default=ROOT)
    c.add_argument("--near", required=True)
    c.add_argument("--material", required=True)
    c.add_argument("--sheet", required=True)
    d = sub.add_parser("types")
    d.add_argument("--root", default=ROOT)
    d.add_argument("--near", required=True)
    d.add_argument("--typed", required=True)
    d.add_argument("--out", required=True)
    a_ = ap.parse_args(argv)
    if a_.cmd == "interim":
        run_interim(root=a_.root, procs=a_.procs, out=a_.out, material=a_.material)
    elif a_.cmd == "near":
        run_near(root=a_.root, procs=a_.procs, interim=a_.interim, out=a_.out, material=a_.material)
    elif a_.cmd == "sheet":
        run_sheet(a_.near, a_.material, a_.sheet, root=a_.root)
    elif a_.cmd == "types":
        run_types(a_.near, a_.typed, a_.out, root=a_.root)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
