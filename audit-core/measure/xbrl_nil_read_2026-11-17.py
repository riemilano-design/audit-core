# -*- coding: utf-8 -*-
u"""封 docs/XBRL_NIL_READ_SEAL_2026-11-17.md(NR ― engine の inline XBRL の読み取りが「自己閉じの空の欄」を次の fact まで読む欠陥は、過去の便の数にどれだけ効いたか)の測定。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(``core/``・``adapters/``)は 1 行も変えない。**材料は TSS の置き場(~/.cache/audit-core/tanshin-self-2026-11-14/)の ZIP 400 本と、
2026-11-09 の便が engine に渡す ZIP(17 本)と、~/.cache/audit-core/ の下の ZIP の棚卸しだけ。

    python3 measure/xbrl_nil_read_2026-11-17.py states --out PATH [--material DIR] [--procs N]      # 棚卸し・400 本の作り直しと直した入力・fact の差・判定の差 → fixtures/xbrl/nil_read/states_2026-11-17.json
    python3 measure/xbrl_nil_read_2026-11-17.py states --check [--material DIR] [--procs N]         # 書かずに作り直し、在る記録と比べる(時間の欄は除く)

実装の注(封が 1 通りに決めていない細部の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 前の便の部品は TSS の script(``load_module`` の形で読む)の ``cut``・``wrap``・``judge_book``・``tally``・``_info`` と 2026-11-09 の script の ``load_books``・``profile_rows``・``row_entry`` を **呼ぶ**(写さない)。
  「そのまま」の本は ``TSS.judge_book`` の結果で、TSS の記録の本と全部同じ(JSON に通して比べる)でなければ止まる。「直した入力」の本は ``judge_book`` と同じ手順(``profile_rows``・``row_entry``)を直した ZIP に掛ける。
- 直した入力(封 §2-2)= TSS の ``wrap`` が包んだ ZIP の ``XBRL/PublicDoc/`` の下の ``.htm`` の bytes に ``<ix:nonFraction[^>]*/>`` を掛けて消す(ほかは 1 byte も変えない)。zz_overview の文の member も同じ扱い(当たらない)。
- 自己閉じの数(本ごとの欄)= 直した入力で消した数(``NIL_TAG_RE`` の一致の数)。engine の読み取りの正規表現の一致のうち属性の列が ``/`` で終わる数(自己閉じから始まる読み取り)は全体の数として別に持つ。
- 独立の読み(封 §2-1)= 開始の tag ``<ix:nonFraction([^>]*)>`` を順に探し、属性の列が ``/`` で終わるものは飛ばし、それ以外は次の ``</ix:nonFraction>`` までを中身にして、値の式は engine と同じ(属性の読み・tag を消す・``,`` を消す・数の形・scale・sign)。
  直した入力を ``load_instance`` に通した fact の多重集合(要素名・context・単位・decimals・値)と本ごとに同じでなければ止まる(数は出さない)。
- 作られた fact = そのままに在って直した入力に無い fact(多重集合の差)・消えた fact = 逆。**期の取り違えの形** = 作られた fact のうち、同じ要素名で context が違う fact が消えた fact の側に在るもの(作られた fact の個数で数える。単位・decimals は問わない)。
- 本ごとの欄は切れた本(包んだ本)だけ。切れない本は fact も行も無い(数に入らない)。行の鍵は (本の #, 文の番号, 位置)。そのままの行の集合と直した入力の行の集合が本ごとに違えば止まる。
- 「合った」state は TSS の記録の字 ``GROUNDED``。「そのままでだけ合う」= そのまま GROUNDED で直した入力が GROUNDED でない。逆も同じ。
- 集計の鍵の並べ方: TSS の記録の ``集計`` の数の葉を全部、道を ``/`` でつないだ字で並べ、そのまま・直した入力・差(直した入力 − そのまま)を出す。そのまま側は TSS の記録の ``集計`` と全部同じでなければ止まる。
- 棚卸し(封 §1 の 1)= ``~/.cache/audit-core/`` の下の file のうち ``zipfile.is_zipfile`` が真のもの(xlsx も ZIP として数える)を folder ごとに、engine の ``load_instance`` の分岐(``XBRL/PublicDoc/`` の ``.xbrl`` が在れば xbrl の経路・無くて ``.htm`` が在れば htm の経路・どちらも無ければ どちらも無い)で数える。
  封が字で書いた folder(7 つ)は封の数と違えば止まる。ほかの folder は数を記録するだけ。
- 2026-11-09 の便の ZIP(封 §1 の 3)= その script の ``states_job`` が ``verify_document`` に渡す ``zb``(有報の ZIP)と ``build_raw_claims`` に渡す ``zm``(文を差し替えた ZIP)の両方の経路を数える。経路が htm の本は自己閉じの数も。
- 記録の時間(秒)以外は 2 回走らせて byte で同じ。率は整数の分子・分母を並べ、% は小数 1 桁(整数の計算)。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import re
import sys
import time
import zipfile

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


TSS = load_module("xbrl_tanshin_self_2026-11-14.py", "tanshin_self_for_nil_read")      # TSS の script(cut・wrap・judge_book・tally・置き場・母集団・止め方)
ST = TSS.ST
TS = TSS.TS
Stop = ST.Stop

from adapters.xbrl import instance as I                 # noqa: E402
from adapters.xbrl import verify_document as VD         # noqa: E402

SEAL_REL = "docs/XBRL_NIL_READ_SEAL_2026-11-17.md"
SEAL_COMMIT = "720a473d"
SCRIPT_REL = "measure/xbrl_nil_read_2026-11-17.py"
REC_DIR_REL = "fixtures/xbrl/nil_read"
STATES_REL = REC_DIR_REL + "/states_2026-11-17.json"
POPULATION_REL = ST.POPULATION_REL
TSS_STATES_REL = "fixtures/xbrl/tanshin_self/states_2026-11-14.json"

#: 入力(# , path, sha256)。違えば止まる。門が実物と 1 つずつ照らす
INPUTS = (
    (1, "fixtures/xbrl/tanshin_self/population_2026-11-14.json", "48ba8e5574be70d85b3d1affacc9403cffbfc698f529c095c6c882cd8ccfa9b0"),
    (2, "fixtures/xbrl/tanshin_self/states_2026-11-14.json", "00414222cfe8cb05d0a1fed3d3e5a09bacafa6547f1675975a3cebd3e4ef70f6"),
    (3, "measure/xbrl_tanshin_self_2026-11-14.py", "fa603d1c2dbfdee7c3ad4197ab9c4a9f1428419ada57293f346418bc0997aeb6"),
    (4, "measure/xbrl_tanshin_self_stage_2026-11-14.py", "4ed60b591366dd65a431dba5348aff6edb3889676d8e9a4154a5b0298486f7f9"),
    (5, "measure/xbrl_tanshin_2026-11-09.py", "b7ea491bf5cd34c4976bde86c4329583e0d9af09ec8895ea0caf48491492b5bd"),
    (6, "fixtures/xbrl/tanshin/states_2026-11-09.json", "6779b451b30aa7619923cbc8c390049f682deeb7bf5e198ddb21c9005b6362d4"),
)

PROFILE = "P33E"
PUBLIC_DOC = "XBRL/PublicDoc/"
#: 封 §2-2: 直した入力で消す正規表現(bytes に掛ける。ほかは 1 byte も変えない)
NIL_TAG_RE = re.compile(br"<ix:nonFraction[^>]*/>")
#: engine の ``load_instance`` の inline XBRL の読み取りと同じ正規表現(属性の列が ``/`` で終わる一致 = 自己閉じの tag から始まる読み取り)
ENGINE_FACT_RE = re.compile(r"<ix:nonFraction([^>]*)>(.*?)</ix:nonFraction>", re.S)
START_RE = re.compile(r"<ix:nonFraction([^>]*)>")
CLOSE_TAG = "</ix:nonFraction>"
STATE_G = u"GROUNDED"
STATES = tuple(TS.STATES)
#: 棚卸しの経路の字
ROUTE_XBRL, ROUTE_HTM, ROUTE_NONE = u".xbrl の経路", u".htm の経路", u"どちらも無い"
ROUTES = (ROUTE_XBRL, ROUTE_HTM, ROUTE_NONE)
#: 封 §1 の 1 が字で書いた folder の数(.xbrl の経路・.htm の経路・どちらも無い)。違えば止まる
SEALED_INVENTORY = collections.OrderedDict([
    ("edinet", (281, 0, 0)), ("edinet-demo-cabocia", (3, 0, 0)), ("edinet-fresh-2026-10-21", (40, 0, 0)), ("edinet-prior-2026-11-02", (94, 0, 0)),
    ("tanshin-self-2026-11-14", (0, 0, 400)), ("tanshin-2026-11-09", (0, 0, 17)), ("sheet", (0, 0, 10))])
LIMITS = (
    u"数えるのは states(判定)の差だけ。型の読み(AI の席 1 席)・注入・near は数え直さない",
    u"「直した入力」は司令塔が決めた 1 つの直し方(自己閉じを消す)で、engine の直しそのものではない。engine の直しの封は別に書き、そこで同じ数が出ることを確かめる",
    u".htm の経路には、ほかの読み取りの欠陥(入れ子・ix:continuation・負の表記の format)が在るかもしれない。この便は自己閉じだけを見る",
    u"state が変わらなくても、engine が選んだ fact が変わっているかもしれない。reason の字の差でしか見えない",
    u"英文短信の側の数への効きは測らない(別のセッションに知らせる)",
    u"材料は英文短信を出している会社から引いた 400 本で、上場会社全体の標本ではない。切れない本は測れていない。EDINET の便は .xbrl の経路だけを通ることを棚卸しの数で示すにとどめ、数え直していない",
    u"行は [本の #, 文の番号, 位置, そのままの state, 直した入力の state, reason が同じか] だけで、文・span・値・要素名・context の字は持たない")
ROW_COLUMNS = (u"本の #", u"文の番号", u"位置", u"そのままの state", u"直した入力の state", u"reason が同じか")
BOOK_COLUMNS = (u"本の #", u"自己閉じの数(消した数)", u"作られた fact", u"消えた fact", u"期の取り違えの形(作られた fact のうち)")


def rate(n, d):
    u"""{分子, 分母, 率}。率は小数 1 桁の %(四捨五入は整数の計算)。分母 0 は「分母 0」。"""
    t = u"分母 0" if d == 0 else u"%d.%d%%" % divmod((n * 2000 + d) // (2 * d), 10)
    return collections.OrderedDict([(u"分子", n), (u"分母", d), (u"率", t)])


# ======================================================================================================
# 直した入力(封 §2-2)
def strip_nil(data):
    u"""bytes から ``<ix:nonFraction[^>]*/>`` に当たる所(値の無い自己閉じの tag)を全部取り除く。ほかは 1 byte も変えない。(取り除いた bytes, 取り除いた数)。"""
    return NIL_TAG_RE.subn(b"", data)


def fix_zip(zb):
    u"""TSS の ``wrap`` が包んだ ZIP の ``XBRL/PublicDoc/`` の下の ``.htm`` から空の欄を取り除いた ZIP の bytes と、取り除いた数。member の順・名前・ほかの bytes は変えない。"""
    buf = io.BytesIO()
    total = 0
    with zipfile.ZipFile(io.BytesIO(zb)) as z, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for info in z.infolist():
            data = z.read(info.filename)
            if info.filename.startswith(PUBLIC_DOC) and info.filename.endswith(".htm"):
                data, k = strip_nil(data)
                total += k
            out.writestr(TSS._info(info.filename), data)
    return buf.getvalue(), total


# ======================================================================================================
# 独立の読み(封 §2-1)と fact の差(封 §2-3)
def read_value(attrs_text, content):
    u"""engine と同じ式(属性の読み・tag を消す・``,`` を消す・数の形・scale・sign)。数の形でなければ None。(名前, context, 単位, decimals, 値)。"""
    a = dict(re.findall(r'(\w+)="([^"]*)"', attrs_text))
    v = re.sub(r"<[^>]+>", "", content).replace(",", "").strip()
    if not re.fullmatch(r"-?\d+(\.\d+)?", v or ""):
        return None
    val = float(v) * (10 ** int(a.get("scale", "0") or 0))
    if a.get("sign") == "-":
        val = -val
    return (a.get("name"), a.get("contextRef"), a.get("unitRef"), a.get("decimals"), val)


def independent_reads(raw):
    u"""1 つの .htm の字から fact の列。属性の列が ``/`` で終わる開始の tag は空の欄で、fact を作らない(封 §2-1 の規則 1 つ)。"""
    out = []
    pos = 0
    while True:
        m = START_RE.search(raw, pos)
        if not m:
            break
        if m.group(1).endswith("/"):
            pos = m.end()
            continue
        end = raw.find(CLOSE_TAG, m.end())
        if end < 0:
            break
        f = read_value(m.group(1), raw[m.end():end])
        if f is not None:
            out.append(f)
        pos = end + len(CLOSE_TAG)
    return out


def htm_members(zb):
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        return [(n, z.read(n)) for n in z.namelist() if n.startswith(PUBLIC_DOC) and n.endswith(".htm")]


def independent_counter(zb):
    u"""ZIP の ``XBRL/PublicDoc/`` の ``.htm`` を独立に読んだ fact の多重集合(engine を呼ばない)。"""
    c = collections.Counter()
    for _n, data in htm_members(zb):
        c.update(independent_reads(data.decode("utf-8", "ignore")))
    return c


def engine_counter(zb):
    u"""engine の ``load_instance`` が作った fact の多重集合(要素名・context・単位・decimals・値)。"""
    return collections.Counter((f["name"], f["context"], f["unit"], f["decimals"], f["value"]) for f in I.load_instance(zb)["facts"])


def engine_self_reads(zb):
    u"""engine の読み取りの正規表現の一致のうち、属性の列が ``/`` で終わる数(自己閉じの tag から始まる読み取り)。数えるだけ。"""
    return sum(1 for _n, data in htm_members(zb) for m in ENGINE_FACT_RE.finditer(data.decode("utf-8", "ignore")) if m.group(1).endswith("/"))


def fact_diff(before, after):
    u"""(作られた fact の数, 消えた fact の数, 期の取り違えの形の数)。before = そのまま・after = 直した入力の fact の多重集合。
    作られた = before に在って after に無い。消えた = after に在って before に無い。期の取り違えの形 = 作られた fact のうち、同じ要素名で context が違う fact が消えた側に在るもの(作られた fact の個数で数える)。"""
    made = before - after
    gone = after - before
    gone_ctx = collections.defaultdict(set)
    for (name, ctx, _u, _d, _v) in gone:
        gone_ctx[name].add(ctx)
    swap = sum(k for (name, ctx, _u, _d, _v), k in made.items() if any(c != ctx for c in gone_ctx.get(name, ())))
    return sum(made.values()), sum(gone.values()), swap


# ======================================================================================================
# 棚卸し(封 §1 の 1・3)
def route_of(zb):
    u"""engine の ``load_instance`` が通る経路。``XBRL/PublicDoc/`` の ``.xbrl`` が在れば xbrl・無くて ``.htm`` が在れば htm・どちらも無ければ どちらも無い。"""
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        names = z.namelist()
    if any(n.startswith(PUBLIC_DOC) and n.endswith(".xbrl") for n in names):
        return ROUTE_XBRL
    if any(n.startswith(PUBLIC_DOC) and n.endswith(".htm") for n in names):
        return ROUTE_HTM
    return ROUTE_NONE


def cache_base_dir():
    return os.path.dirname(os.path.abspath(ST.default_cache_dir()))


def inventory(base=None):
    u"""``base`` の下の folder ごとの、ZIP として読める file の経路の数。{folder: {経路: 数, ``ZIP として読める file``, ``ZIP でない file``}}。folder の名の順。"""
    base = base or cache_base_dir()
    out = collections.OrderedDict()
    for name in sorted(os.listdir(base)):
        top = os.path.join(base, name)
        if not os.path.isdir(top):
            continue
        c = collections.Counter()
        for dp, dns, fns in os.walk(top):
            dns.sort()
            for fn in sorted(fns):
                p = os.path.join(dp, fn)
                if not zipfile.is_zipfile(p):
                    c[u"ZIP でない file"] += 1
                    continue
                with io.open(p, "rb") as fh:
                    c[route_of(fh.read())] += 1
        out[name] = collections.OrderedDict([(r, c.get(r, 0)) for r in ROUTES] + [(u"ZIP として読める file", sum(c.get(r, 0) for r in ROUTES)), (u"ZIP でない file", c.get(u"ZIP でない file", 0))])
    return out


def check_inventory(inv, sealed=None):
    u"""封が字で書いた folder の数と違えば止める。封の字の数と一致した folder の名の並びを返す。"""
    sealed = SEALED_INVENTORY if sealed is None else sealed
    ok = []
    for name, want in sealed.items():
        if name not in inv:
            raise Stop(u"**棚卸しに封が書いた folder が無い(%s)。止める**" % name)
        got = tuple(inv[name][r] for r in ROUTES)
        if got != tuple(want):
            raise Stop(u"**棚卸しの数が封の字の数と違う(%s)。止める**" % name)
        ok.append(name)
    return ok


def tanshin_0911(root=ROOT):
    u"""封 §1 の 3: 2026-11-09 の便の script が engine に渡す ZIP の経路。``verify_document`` に渡す ``zb`` と ``build_raw_claims`` に渡す ``zm`` の両方。
    返り値 = [(その便の表の行番号, zb の経路, zm の経路, 自己閉じの数(zm が htm の経路なら消せる数・そうでなければ 0))]。"""
    out = []
    for (n, _code, _number, _sha, _chars, _claims, row, text) in TS.load_books(root):
        zb = TS.GEN.read_zip(row, TS.GEN.EXISTING_CACHES)
        zm = TS.PR.build_modified_zip(zb, text)[0]
        rb, rm = route_of(zb), route_of(zm)
        nil = sum(len(NIL_TAG_RE.findall(d)) for _n, d in htm_members(zm)) if rm == ROUTE_HTM else 0
        out.append((n, rb, rm, nil))
    return out


def tanshin_0911_block(rows):
    u"""封 §1 の 3 の数。NR-6 の分子・分母。"""
    htm = [r for r in rows if ROUTE_HTM in (r[1], r[2])]
    return collections.OrderedDict([
        (u"本", len(rows)),
        (u"verify_document に渡す ZIP の経路", collections.OrderedDict((r_, sum(1 for r in rows if r[1] == r_)) for r_ in ROUTES)),
        (u"build_raw_claims に渡す ZIP の経路", collections.OrderedDict((r_, sum(1 for r in rows if r[2] == r_)) for r_ in ROUTES)),
        (u".htm の経路を通る本", len(htm)),
        (u".htm の経路で自己閉じを持つ本", sum(1 for r in htm if r[3] > 0)),
        (u".htm の経路の本の自己閉じの数の合計", sum(r[3] for r in htm)),
        (u"本ごと([その便の表の行番号, verify_document の経路, build_raw_claims の経路, 自己閉じの数])", [list(r) for r in rows])])


# ======================================================================================================
# 1 本(封 §2-1〜§2-4)
def judge_fixed(n, grp, kind, sha, text, head, fixed_zb, nfiles):
    u"""``TSS.judge_book`` と同じ手順を直した ZIP に掛けた本の記録(OrderedDict)。"""
    nfacts = len(I.load_instance(fixed_zb)["facts"])
    rows, ok, ncl = TS.profile_rows(fixed_zb, None, fixed_zb, PROFILE)
    return collections.OrderedDict([
        (u"#", n), (u"群", grp), (u"様式の種類", kind), (u"ZIP の sha256", sha), (u"切り出し", TSS.CUT_OK), (u"理由", None), (u"見出しの番号", head), (u"字数", len(text)),
        (u"入れた iXBRL の file の数", nfiles), (u"fact の数", nfacts), (u"claim", ncl), (u"対応", bool(ok)), (u"行", [TS.row_entry(k, v) for k, v in rows.items()])])


def jsonable(o):
    return json.loads(json.dumps(o, ensure_ascii=False), object_pairs_hook=collections.OrderedDict)


def check_asis(n, asis, rec_book):
    u"""「そのまま」の本が TSS の記録の本と全部同じでなければ止める(数を出さない)。"""
    if jsonable(asis) != rec_book:
        raise Stop(u"**「そのまま」の本が TSS の記録の本と違う(# %d)。止める**" % n)


def check_independent(n, indep, engine_fixed):
    u"""独立の読みの fact の多重集合が、直した入力を engine に通した fact の多重集合と違えば止める(自己閉じ以外の読み取りの差)。"""
    if indep != engine_fixed:
        raise Stop(u"**独立の読みが直した入力の engine の fact と違う(# %d)。自己閉じ以外の読み取りの差。止める**" % n)


def check_same_rows(n, asis, fixed):
    u"""行の鍵(文の番号, 位置)の並びがそのままと直した入力で違えば止める。"""
    if [(r[0], r[1]) for r in asis[u"行"]] != [(r[0], r[1]) for r in fixed[u"行"]] or not fixed[u"対応"]:
        raise Stop(u"**行の集合がそのままと直した入力で違う(# %d)。止める**" % n)


def states_job(args):
    u"""1 本: 「そのまま」を TSS の記録の本と照らす → 直した入力を作る → 独立の読みと照らす → fact の差・行の対を返す。"""
    n, grp, kind, sha, path, rec_book = args
    if not os.path.exists(path):
        raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める**" % n)
    with io.open(path, "rb") as fh:
        zb = fh.read()
    if ST.sha256_bytes(zb) != sha:
        raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % n)
    asis = TSS.judge_book(n, grp, kind, sha, zb)
    check_asis(n, asis, rec_book)
    res = collections.OrderedDict([(u"#", n), (u"群", grp), (u"切れた", asis[u"切り出し"] == TSS.CUT_OK), (u"asis", asis), (u"fixed", asis)])
    if not res[u"切れた"]:
        return res
    text, head, _why = TSS.cut(zb)
    wrapped, nfiles = TSS.wrap(zb, text)
    fixed_zb, nil = fix_zip(wrapped)
    c_as, c_fx = engine_counter(wrapped), engine_counter(fixed_zb)
    check_independent(n, independent_counter(wrapped), c_fx)
    made, gone, swap = fact_diff(c_as, c_fx)
    fixed = judge_fixed(n, grp, kind, sha, text, head, fixed_zb, nfiles)
    check_same_rows(n, asis, fixed)
    res[u"fixed"] = fixed
    res[u"nil"] = nil
    res[u"engine の自己閉じの読み取り"] = engine_self_reads(wrapped)
    res[u"fact の差"] = (made, gone, swap)
    return res


# ======================================================================================================
# 数える(封 §2-3・§2-4)
def leaves(o, path=()):
    u"""数(真偽でない)の葉を (道, 数) で。辞書の順のとおり。"""
    if isinstance(o, dict):
        for k, v in o.items():
            for x in leaves(v, path + (k,)):
                yield x
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        yield u"/".join(path), o


def key_diff_table(tally_as, tally_fx):
    u"""TSS の記録の集計の鍵ごとに [道, そのまま, 直した入力, 差(直した入力 − そのまま)]。鍵の集合が違えば止める。"""
    a, b = list(leaves(tally_as)), list(leaves(tally_fx))
    if [p for p, _v in a] != [p for p, _v in b]:
        raise Stop(u"**集計の鍵の集合がそのままと直した入力で違う。止める**")
    return [[p, x, y, y - x] for (p, x), (_p, y) in zip(a, b)]


def pair_rows(books):
    u"""切れた本の行を [本の #, 文の番号, 位置, そのままの state, 直した入力の state, reason が同じか] に。そのまま・直した入力の行の鍵は同じ並び(``states_job`` が確かめ済み)。"""
    rows = []
    for b in books:
        if not b[u"切れた"]:
            continue
        for ra, rf in zip(b[u"asis"][u"行"], b[u"fixed"][u"行"]):
            if (ra[0], ra[1]) != (rf[0], rf[1]):
                raise Stop(u"**行の鍵が対にならない。止める**")
            rows.append([b[u"#"], ra[0], ra[1], ra[2], rf[2], ra[3] == rf[3]])
    return rows


def transition_table(rows):
    c = collections.Counter((r[3], r[4]) for r in rows)
    return collections.OrderedDict((u"%s → %s" % (a, b), c.get((a, b), 0)) for a in STATES for b in STATES)


def fact_block(books):
    cut = [b for b in books if b[u"切れた"]]
    per = [[b[u"#"], b[u"nil"], b[u"fact の差"][0], b[u"fact の差"][1], b[u"fact の差"][2]] for b in cut]
    made, gone, swap = sum(p[2] for p in per), sum(p[3] for p in per), sum(p[4] for p in per)
    return collections.OrderedDict([
        (u"切れた本", len(cut)),
        (u"自己閉じの数(消した数)", sum(p[1] for p in per)),
        (u"自己閉じを 1 つ以上持つ本", sum(1 for p in per if p[1] > 0)),
        (u"engine の読み取りのうち自己閉じの tag から始まるもの", sum(b[u"engine の自己閉じの読み取り"] for b in cut)),
        (u"作られた fact", made), (u"消えた fact", gone),
        (u"作られた fact を持つ本", sum(1 for p in per if p[2] > 0)), (u"消えた fact を持つ本", sum(1 for p in per if p[3] > 0)),
        (u"作られた fact か消えた fact が 1 つ以上の本", sum(1 for p in per if p[2] > 0 or p[3] > 0)),
        (u"期の取り違えの形(作られた fact のうち)", rate(swap, made))]), per


def judge_block(rows, per_book):
    changed = [r for r in rows if r[3] != r[4]]
    reason_only = [r for r in rows if r[3] == r[4] and not r[5]]
    only_as = [r for r in rows if r[3] == STATE_G and r[4] != STATE_G]
    only_fx = [r for r in rows if r[3] != STATE_G and r[4] == STATE_G]
    changed_books = sorted(set(r[0] for r in changed))
    return collections.OrderedDict([
        (u"行の数(切れた本の全部の行)", len(rows)),
        (u"state の移り変わり(そのまま → 直した入力)", transition_table(rows)),
        (u"state が変わった行", rate(len(changed), len(rows))),
        (u"state が変わった行を持つ本", len(changed_books)),
        (u"state が変わった行を持つ本の #", changed_books),
        (u"state は同じで reason だけ変わった行", len(reason_only)),
        (u"そのままでだけ合う行(作られた fact に頼っていた一致)", len(only_as)),
        (u"直した入力でだけ合う行", len(only_fx))])


def prediction_numbers(fb, jb, per_book, tanshin_block):
    u"""予測 NR-1〜NR-6 の判定に要る分子と分母(当たり・外れの字は書かない)。"""
    n_rows = jb[u"行の数(切れた本の全部の行)"]
    changed = jb[u"state が変わった行"][u"分子"]
    nil_books = fb[u"自己閉じを 1 つ以上持つ本"]
    return collections.OrderedDict([
        (u"NR-1 state が変わった行 / 全部の行", rate(changed, n_rows)),
        (u"NR-2 直した入力でだけ値が合う行・そのままでだけ値が合う行", collections.OrderedDict([
            (u"直した入力でだけ", jb[u"直した入力でだけ合う行"]), (u"そのままでだけ", jb[u"そのままでだけ合う行(作られた fact に頼っていた一致)"])])),
        (u"NR-3 そのままでだけ値が合う行", jb[u"そのままでだけ合う行(作られた fact に頼っていた一致)"]),
        (u"NR-4 期の取り違えの形の作られた fact / 作られた fact", fb[u"期の取り違えの形(作られた fact のうち)"]),
        (u"NR-5 state が変わった行を持つ本 / 自己閉じを持つ本", rate(jb[u"state が変わった行を持つ本"], nil_books)),
        (u"NR-6 2026-11-09 の便の ZIP のうち .htm の経路で自己閉じを持つ本", collections.OrderedDict([
            (u"分子", tanshin_block[u".htm の経路で自己閉じを持つ本"]), (u"分母", tanshin_block[u"本"])]))])


# ======================================================================================================
# 入力・記録
def load_json(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh, object_pairs_hook=collections.OrderedDict)


def check_inputs(root):
    u"""入力の sha256 が表と同じか。違えば止める。"""
    for no, rel, want in INPUTS:
        p = os.path.join(root, rel)
        if not os.path.isfile(p) or ST.sha256_file(p) != want:
            raise Stop(u"**入力 %d の sha256 が表と違う。止める**" % no)
    return [collections.OrderedDict([(u"#", no), (u"path", rel), (u"sha256", want)]) for no, rel, want in INPUTS]


def check_population(root, pop):
    rec = load_json(os.path.join(root, POPULATION_REL))
    if [tuple(r[:4]) for r in rec[u"行"]] != [tuple(r) for r in pop]:
        raise Stop(u"**母集団の記録の行が TSS の封の表と違う。止める**")


FP_KEYS = ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files")


def engine_fp(states_rec):
    fp = VD.engine_fingerprint()
    now = collections.OrderedDict((k, fp[k]) for k in FP_KEYS)
    was = states_rec[u"engine の指紋"]
    if any(now[k] != was.get(k) for k in FP_KEYS):
        raise Stop(u"**engine の指紋が TSS の記録のものと違う。止める**")
    return now


def material_dir(material, out, root=ROOT):
    prod = os.path.abspath(ST.default_cache_dir())
    mat = os.path.abspath(material) if material else prod
    if out and os.path.abspath(out) == os.path.abspath(os.path.join(root, STATES_REL)) and mat != prod:
        raise Stop(u"**本番の記録を使い捨ての材料から作らない。止める**")
    return mat, mat == prod


def build_record(root=ROOT, procs=1, material=None, out=None, say=print, clock=time.time, base=None, tanshin_rows=None):
    u"""棚卸し・400 本の作り直し・直した入力・fact の差・判定の差を数えた記録(OrderedDict)を返す。書かない。"""
    mat, prod = material_dir(material, out, root)
    inputs = check_inputs(root)
    inv = inventory(base)
    sealed_ok = check_inventory(inv)
    pop = ST.validate_population(ST.read_population(root), ST.N_ROWS, ST.GROUP_COUNTS)
    check_population(root, pop)
    states_in = load_json(os.path.join(root, TSS_STATES_REL))
    fp = engine_fp(states_in)
    if states_in[u"profile"] != PROFILE:
        raise Stop(u"**TSS の記録の profile が %s でない。止める**" % PROFILE)
    by_book = dict((b[u"#"], b) for b in states_in[u"本"])
    if sorted(by_book) != [r[0] for r in pop]:
        raise Stop(u"**TSS の記録の本が母集団とそろわない。止める**")
    for (n, _g, _k, sha) in pop:
        if not os.path.exists(os.path.join(mat, sha + u".zip")):
            raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める**" % n)
        if by_book[n][u"ZIP の sha256"] != sha:
            raise Stop(u"**TSS の記録の ZIP の sha256 が表と違う(# %d)。止める**" % n)
    before = ST.names_snapshot(mat)
    jobs = [(n, g, k, sha, os.path.join(mat, sha + u".zip"), by_book[n]) for (n, g, k, sha) in pop]
    say(u"states %d 本 × %s ― procs %d" % (len(jobs), PROFILE, procs))
    t0 = clock()
    books = TS.NF.map_pool(states_job, jobs, procs)
    elapsed = clock() - t0
    if before != ST.names_snapshot(mat):
        raise Stop(u"**材料の置き場の件数か名前が変わった。止める**")
    tally_as = TSS.tally([b[u"asis"] for b in books])
    if jsonable(tally_as) != states_in[u"集計"]:
        raise Stop(u"**「そのまま」の集計が TSS の記録の集計と違う。止める**")
    tally_fx = TSS.tally([b[u"fixed"] for b in books])
    rows = pair_rows(books)
    fb, per_book = fact_block(books)
    jb = judge_block(rows, per_book)
    tb = tanshin_0911_block(tanshin_rows if tanshin_rows is not None else tanshin_0911(root))
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"NR(engine の inline XBRL の読み取りが自己閉じの空の欄を次の fact まで読む欠陥の、過去の便の数への効き)― 棚卸し・400 本の直した入力・fact の差・判定の差(0 USD・通信なし・engine は 0 行)"
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"入力"] = inputs
    rec[u"engine の指紋"] = fp
    rec[u"profile"] = PROFILE
    rec[u"材料"] = collections.OrderedDict([(u"置き場", ST.display_path(mat) if prod else u"使い捨ての置き場(本番の folder ではない)"), (u"表と一致した ZIP", len(pop))])
    rec[u"棚卸し(封 §1 の 1)"] = collections.OrderedDict([
        (u"置き場", ST.display_path(cache_base_dir())), (u"封が字で書いた数と一致した folder", sealed_ok), (u"folder ごと", inv),
        (u"ZIP として読める file の合計", sum(v[u"ZIP として読める file"] for v in inv.values())),
        (u"経路ごとの合計", collections.OrderedDict((r, sum(v[r] for v in inv.values())) for r in ROUTES))])
    rec[u"2026-11-09 の便の ZIP(封 §1 の 3)"] = tb
    rec[u"直した入力の規則(封 §2-2)"] = u"TSS の wrap が包んだ ZIP の XBRL/PublicDoc/ の下の .htm の bytes から、正規表現 <ix:nonFraction[^>]*/> に当たる所を全部消す。ほかは 1 byte も変えない。engine は変えない"
    rec[u"独立の読みの確認(封 §2-1)"] = collections.OrderedDict([
        (u"確かめた本", fb[u"切れた本"]), (u"直した入力の engine の fact と要素名・context・単位・decimals・値の多重集合が同じ本", fb[u"切れた本"])])
    rec[u"作り直しの確認"] = collections.OrderedDict([
        (u"本", len(books)), (u"「そのまま」の本が TSS の記録の本と全部同じ本", len(books)), (u"「そのまま」の集計が TSS の記録の集計と同じ", True),
        (u"行の集合がそのままと直した入力で同じ本", fb[u"切れた本"])])
    rec[u"fact の差(封 §2-3)"] = fb
    rec[u"判定の差(封 §2-4)"] = jb
    rec[u"集計の鍵ごと(封 §2-4。[道, そのまま, 直した入力, 差])"] = key_diff_table(tally_as, tally_fx)
    rec[u"予測の判定に要る数(NR-1〜NR-6。当たり・外れは結果の文書で)"] = prediction_numbers(fb, jb, per_book, tb)
    rec[u"本ごとの欄"] = list(BOOK_COLUMNS)
    rec[u"本ごと(切れた本だけ)"] = per_book
    rec[u"限界"] = list(LIMITS)
    rec[u"行の欄"] = list(ROW_COLUMNS)
    rec[u"時間(秒)"] = round(elapsed, 1)
    rec[u"key_leaks"] = []
    rec[u"行"] = rows
    return rec


def check_text(rec, text, key_value=None):
    scan = text.replace(SEAL_REL, u"")
    for _no, rel, _sha in INPUTS:
        scan = scan.replace(rel, u"")                    # path は 32 字以上の _ - 英数字の連なり(TSS と同じく除いて検査する)
    TSS.check_clean(rec, scan, key_value)


def record_text(rec, key_value=None):
    text = ST.dumps_record(rec)
    check_text(rec, text, key_value)
    return text


def run_states(root=ROOT, procs=1, out=None, material=None, say=print, check=False, **kw):
    if not check and out is None:
        raise Stop(u"**--out を指定する(書かずに比べるなら --check)。止める**")
    out = os.path.abspath(out) if out else None
    if out and os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    rec = build_record(root=root, procs=procs, material=material, out=out, say=say, **kw)
    text = record_text(rec)
    if check:
        want = os.path.join(root, STATES_REL)
        if not os.path.isfile(want):
            raise Stop(u"**在る記録が無い。止める**")
        cur = load_json(want)
        cur[u"時間(秒)"] = 0
        rec2 = collections.OrderedDict(rec)
        rec2[u"時間(秒)"] = 0
        if ST.dumps_record(cur) != ST.dumps_record(rec2):
            raise Stop(u"**作り直した記録が在る記録と違う(時間の欄は除く)。止める**")
        say(u"--check: 在る記録と同じ(時間の欄は除く)")
        return rec
    ST.write_text_exclusive(out, text)
    say(u"-> %s(行 %d)" % (os.path.basename(out), len(rec[u"行"])))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("states")
    a.add_argument("--root", default=ROOT)
    a.add_argument("--out", default=None)
    a.add_argument("--check", action="store_true")
    a.add_argument("--material", default=None)
    a.add_argument("--procs", type=int, default=1)
    a_ = ap.parse_args(argv)
    if a_.cmd == "states":
        run_states(root=a_.root, procs=a_.procs, out=a_.out, material=a_.material, check=a_.check)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
