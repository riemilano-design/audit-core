# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TANSHIN_HUMAN_TEXT_SEAL_2026-11-09.md §0-1 の 3・§0-2・§2・§3・§5 ― TS(人が書いた有報の外の文 = 決算短信「経営成績等の概況」17 社で engine を測る)の測定と、結果の表(tally)。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。**(取得は ``measure/xbrl_tanshin_fetch_2026-11-09.py``。この script は cache の新しい folder の ZIP を読むだけ)

    python3 measure/xbrl_tanshin_2026-11-09.py states [--procs N] [--only <証券コード>] [--out PATH] [--cache DIR]   # 17 社の概況 × profile の判定 → fixtures/xbrl/tanshin/states_2026-11-09.json
    python3 measure/xbrl_tanshin_2026-11-09.py inject [--procs N] [--only <証券コード>] [--out PATH] [--cache DIR]   # T1・T5・T8・T9 の注入(P30E・P32E)→ fixtures/xbrl/tanshin/inject_2026-11-09.json
    python3 measure/xbrl_tanshin_2026-11-09.py tally  [--root DIR]                                                   # 記録(取得・states・inject)から H-1〜H-10 の表を出す(file は書かない)

``--only`` を付けた走らせ方は本番の記録ではない: ``--out`` を必ず指定する(指定が無ければ止める)。``--cache`` の既定は ``--out`` が無ければ本番の置き場、
``--out`` が有れば ``<--out の folder>/cache``(取得の script と同じ規則)。
前の便の script は **1 byte も変えず**、importlib で読み込んで使う(写さない)。PB の便の script ``xbrl_pbind_2026-11-06.py``(PB)は states の部品(``period5``・``diff_rows``)、
T5Y の便の script ``xbrl_t5y_2026-11-06.py``(TY。その先に T9 の第 2 便 PI・T9 PS・J・H の便)は注入の部品(``PI.id_map``・``PS.t9_all_sites``・``PS.build_t9``・``TY.t5_all_sites``・
``IJ.select``・``RUN.t8_candidates4``・切り替え 2 つ)。読み込みの前に居た ``sys.modules`` の名前は、読み込みの後に元の object へ戻す。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- 切り出し(封 §0-1 の 3): ZIP の ``XBRLData/Attachment/qualitative.htm`` → script・style を除く → ``<br>``・``</p>``・``</div>``・``</tr>``・``</h*>``・``</li>`` を改行に → 他の tag を除く → ``html.unescape`` →
  各行の空白(半角・tab・全角)の連なりを 1 つの半角空白に(**行頭・行末の空白は削らない**。下見の字数 84,378 と 17 社とも一致する作りで、削ると 84,055)・空白だけの行を詰める →
  「１．経営成績等の概況」で始まり(行頭の空白は無視)「……」を持たない行のうち**最後**の行から、その後で最初の「２．」で始まる行の直前まで → NFKC。切り出せなければ止める。
- states の行 = (文の番号, 位置, state, reason, pointer の期, formula の有無, 単位の族, 両期の fact を引く a−b, span に % を含む)。数の claim だけ(kind == num)。鍵 = raw claim の (文の番号, 位置)。pointer の期は PB の ``period5``(CurrentYear / Prior1Year / Prior2Year / 他 / なし)。
  formula の有無 = pointers に ``formula:`` で始まる字が在る。両期の fact を引く a−b = pointers に ``formula:a-b``(ちょうどこの字)が在り単位の族が円族。単位の族: ``%`` と ``ポイント`` = %・円族(``TUNE.MONEY_FAMILY``)= 円族・他は 他(参考の欄。H-5 の % の数には使わない)。span に % を含む = claim の span に ``%`` の字が在るかの真偽だけ(span の字は記録に持たない)。
- 動いた行(P30E → P32E)= PB の ``diff_rows`` の定義(state か pointers が違う行。reason だけが違う行は別に数える)。H-4 の「動いた行」はこの数。
- H-5 の機械の内訳は P32E の VALUE_MISMATCH の行で、導出 = formula の有無が真・**% の数 = span に ``%`` を含む行・円族の数 = それ以外の行**(2 値。司令塔の下見の定義 ``"pct" if "%" in (claim の span or "") else "yen"`` = 司令塔の決め 2026-11-10。単位の欄は見ない)・両期の fact を引く a−b(円)= 上の定義。単位の族の 3 欄は参考に別名で残す(単位の族が % / 円族 / 他)。
- H-9 の文 = P32E の profile の文の列(``RUN.sentence_list``)のうち行頭が ``|`` の文。
- 注入の行の reason: ``TUNE.classify`` が引く ``TUNE.safe_reason`` を with の中だけ ``RUN.safe_reason``(engine が宣言した固定の符号も通す)にする(短信の文では ``no_element(no prior2 for prior-year diff)`` のように
  括弧の中に数字を持つ宣言済みの符号が出て、TUNE の版は止まる。AI の文の便では出なかった)。数や文が混ざる字は RUN の版も止める。
- 注入: site・並べ替え・cap・差し替え・対応付け(id で引く 3 条件)は T9 の第 2 便・T5Y の便のまま。T1 は ``IJ.select(types=[T1_VALUE])``(新しい token に絞らない)・T8 は ``RUN.t8_candidates4``(土台の判定を (P32E, P30E) の対にして差し替える)。
  土台 = P30E が GROUNDED の claim。P32E の claim は (value, span, unit) が同じ 1 件があれば結ぶ(PB の便と同じ)。cap は型ごと 1 本あたり ``RUN.INJECT_CAP``(T1 は select の採用に・T8 は site に・T5 と T9 は土台 GROUNDED の site を先頭から)。
  ``inject.select`` と乱数の種の「本の名前」には ``<証券コード>_TS`` を渡す。切り替え 2 つ(``yen_scan_2026_11_05``・``t5_yen_2026_11_06``)は with の中だけ真。
  行の欄は T9 の第 2 便と同じ(型を足した)。「届いた」と注入後の pointer の期は id で引いた claim で決める(「届いた」は P32E の claim)。
- 記録は文・span・value・会社名・pointer の字(要素名)を持たない。docID は取得の記録の file だけ(``LATER_NAMING_FILES`` に宣言)。この script の記録は証券コードで本を引く。

engine(``core/``・``adapters/``)・``measure/inject.py``・``measure/lib``・前の便の script と記録は 1 行も変えない。
"""
from __future__ import print_function

import argparse
import collections
import contextlib
import html
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import unicodedata
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    u"""importlib で読み込む。読み込んだ file が中で読む前の便の script は決まった名前で ``sys.modules`` に登録し直して先に居た module を上書きする。
    読み込みの前に居た名前は、読み込みの後に元の object へ戻す(自分の名前 ``mod_name`` は残す。``--procs`` の fork は名前で引かない)。"""
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


FE = load_module("xbrl_tanshin_fetch_2026-11-09.py", "tanshin_fetch_for_tanshin")
PB = load_module("xbrl_pbind_2026-11-06.py", "pbind_for_tanshin")
TY = load_module("xbrl_t5y_2026-11-06.py", "t5y_for_tanshin")
PI, PS, JT, NS = TY.PI, TY.PS, TY.JT, TY.NS
RM, NF, RUN, GEN, TUNE, IJ = TY.RM, TY.NF, TY.RUN, TY.GEN, TY.TUNE, TY.IJ
N, S, SC = TY.N, TY.S, TY.SC
Stop = GEN.Stop

from adapters.xbrl import prose as PR                 # noqa: E402
from adapters.xbrl import recipes as R                # noqa: E402
from adapters.xbrl import verify_document as VD       # noqa: E402
from adapters.xbrl import vocabulary as V             # noqa: E402

SEAL_REL = FE.SEAL_REL
SEAL_COMMIT = FE.SEAL_COMMIT
DOC_REL = "docs/XBRL_TANSHIN_HUMAN_TEXT_RESULT_2026-11-09.md"
SCRIPT_REL = "measure/xbrl_tanshin_2026-11-09.py"
FETCH_SCRIPT_REL = FE.SCRIPT_REL
REC_DIR_REL = FE.REC_DIR_REL
FETCH_REL = FE.OUT_REL
STATES_REL = REC_DIR_REL + "/states_2026-11-09.json"
INJECT_REL = REC_DIR_REL + "/inject_2026-11-09.json"
REC_REL = collections.OrderedDict([("fetch", FETCH_REL), ("states", STATES_REL), ("inject", INJECT_REL)])
PB_SCRIPT_REL, TY_SCRIPT_REL = "measure/xbrl_pbind_2026-11-06.py", "measure/xbrl_t5y_2026-11-06.py"
PI_SCRIPT_REL, PS_SCRIPT_REL = "measure/xbrl_pswap_idmap_2026-11-06.py", "measure/xbrl_pswap_2026-11-06.py"
PREV_SCRIPT_RELS = (PB_SCRIPT_REL, TY_SCRIPT_REL, PI_SCRIPT_REL, PS_SCRIPT_REL)
LIB_RELS = TY.LIB_RELS
DEVICE_RELS = TY.DEVICE_RELS
TABLE = FE.TABLE
#: 注入の profile の対(古い → 測る側)と states の profile(P33E が engine に在れば足す)
OLD, NEW = "P30E", "P32E"
INJECT_PROFILES = (OLD, NEW)
STATES_PROFILES_BASE = ("P27", "P30E", "P32E")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
G, VM, UNV, PNF = STATES
PERIODS5 = PB.PERIODS5
TYPES = ("T1_VALUE", "T5_COINCIDENT", "T8_REL", "T9_PRIOR_TO_CURRENT")
TYPE_SHORT = collections.OrderedDict([("T1_VALUE", "T1"), ("T5_COINCIDENT", "T5"), ("T8_REL", "T8"), ("T9_PRIOR_TO_CURRENT", "T9")])
T1, T5, T8, T9 = TYPES
LINK_KEY = u"P32E の土台に対応"
LABEL_PASS, LABEL_NAMED_ORIGINAL = TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL
SHAPES = PS.SHAPES
PIPE = u"|"
#: 切り出しの字(封 §0-1 の 3)
HEAD_PREFIX = u"１．経営成績等の概況"
END_PREFIX = u"２．"
TOC_MARK = u"……"
QUALITATIVE = "XBRLData/Attachment/qualitative.htm"
SCOPE_ONLY = u"**--only(本番の記録ではない)**"
STATES_LIMITS = (
    u"材料は 17 社・2026 年 5〜7 月期の短信の概況だけ。業種・規模・書き手の偏りは AI の文の 20 社の選びを引き継ぐ(封 §6 の 1)",
    u"短信は会社が書いた文だが、監査の前の数で、有報と数が違う行がありうる。VALUE_MISMATCH の全部を「誤って止めた」とは言わない(封 §6 の 2)",
    u"セグメント・事業別の数は engine が名寄せを持たないので engine の外。この便は数えるだけで直さない(封 §6 の 3)",
    u"切り出しは HTML の tag を剥がした字で、表の構造(列)は失われる(封 §6 の 4)",
    u"行は (文の番号, 位置, state, reason, pointer の期, formula の有無, 単位の族, 両期の fact を引く a−b, span に % を含む真偽)だけで、文・span・値・要素名は持たない",
    u"H-5 の「% の数」は span に % を含む行・「円族の数」はそれ以外の行(司令塔の決め 2026-11-10。下見の定義)。単位の族(% と ポイント が %・TUNE.MONEY_FAMILY が円族・他は 他)は参考の欄で、H-5 には使わない")
INJECT_LIMITS = (
    u"注入の site は仕掛けが作れる場所だけ(仕掛けの選び方は AI の文の便のまま)。「通した」「止めた」は engine の state で、人の目の札は無い(封 §6 の 5)",
    u"人が書いた文での測定は、「人の文で engine が動く」ことの確認で、買い手の文での再現を言うものではない(封 §6 の 6)",
    u"土台は P30E が GROUNDED の claim。P32E の claim は (value, span, unit) が同じ 1 件があれば結ぶ(無ければ P32E の欄は対応なし)",
    u"対応付けは基準の claim の id で引く 3 条件(T9 の第 2 便と同じ)。「届いた」は P32E の claim、pointer の期は profile ごとに id で引いた claim。claim が無い行の期は なし",
    u"T1 は新しい token に絞らない select、T8 は RUN.t8_candidates4 の写しでない本物の関数(土台の判定の差し替え)。round-trip 不一致は止めずに数える")


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def norm(x):
    return json.loads(json.dumps(x))


def within(x, lo_hi):
    return x is not None and lo_hi[0] <= x <= lo_hi[1]


# ======================================================================================================
# 切り出し(封 §0-1 の 3)
_SCRIPT_STYLE = re.compile(r"(?is)<(script|style)\b.*?</\1\s*>")
_BREAKS = re.compile(r"(?i)<br\s*/?>|</p\s*>|</div\s*>|</tr\s*>|</h[1-6]\s*>|</li\s*>")
_TAGS = re.compile(r"(?s)<[^>]*>")
_SPACES = re.compile(r"[ \t　]+")


def html_to_lines(h):
    u"""tag を剥がして行の列にする。各行の空白の連なりを 1 つの半角空白に(行頭・行末は削らない)・空白だけの行を詰める。"""
    h = _SCRIPT_STYLE.sub(u"", h)
    h = _BREAKS.sub(u"\n", h)
    h = _TAGS.sub(u"", h)
    h = html.unescape(h)
    out = []
    for ln in h.split(u"\n"):
        ln = _SPACES.sub(u" ", ln)
        if ln.strip():
            out.append(ln)
    return out


def cut_overview(lines):
    u"""行の列から概況の行の列を切り出す(NFKC の前)。始まり = 「１．経営成績等の概況」で始まり「……」を持たない行のうち最後。終わり = その後で最初の「２．」で始まる行の直前。無ければ止める。"""
    start = None
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith(HEAD_PREFIX) and TOC_MARK not in ln:
            start = i
    if start is None:
        raise Stop(u"**「１．経営成績等の概況」で始まる本文の行が無い。止める**")
    for j in range(start + 1, len(lines)):
        if lines[j].lstrip().startswith(END_PREFIX):
            return lines[start:j]
    raise Stop(u"**「２．」で始まる行が概況の後に無い。止める**")


def overview_from_html(h):
    return unicodedata.normalize("NFKC", u"\n".join(cut_overview(html_to_lines(h))))


def overview_from_zip(zb):
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        if QUALITATIVE not in z.namelist():
            raise Stop(u"**ZIP に qualitative.htm が無い。止める**")
        h = z.read(QUALITATIVE).decode("utf-8")
    return overview_from_html(h)


def read_tanshin(cache_dir, code, number, sha):
    u"""cache の ZIP を読み、sha256 が封 §1 の表と違えば止め、概況の字を返す。"""
    p = FE.zip_path(cache_dir, code, number)
    if not os.path.exists(p):
        raise Stop(u"**材料の ZIP が cache に無い。止める(取得の script を先に)**")
    with io.open(p, "rb") as fh:
        zb = fh.read()
    FE.check_zip_bytes(zb, sha)
    return overview_from_zip(zb)


# ======================================================================================================
# 配線・記録の共通部品
def cache_dir_for(out, cache):
    u"""材料の置き場: --cache があればそれ・無くて --out も無ければ本番・無くて --out が有れば <--out の folder>/cache。"""
    if cache:
        return os.path.abspath(cache)
    if out is None:
        return FE.default_cache_dir()
    return os.path.join(os.path.dirname(os.path.abspath(out)), "cache")


def is_production_out(root, out, rel):
    u"""出力が本番の記録の path か(本番なら材料の置き場も本番)。"""
    return os.path.abspath(out) == os.path.abspath(os.path.join(root, rel))


def caches_all():
    return FE.read_caches()


def sha_rel(root, rel):
    return GEN.sha256_file(os.path.join(root, rel))


def engine_profiles_now():
    u"""states の profile(P27・P30E・P32E。engine に P33E が在れば足す)。"""
    return STATES_PROFILES_BASE + (("P33E",) if "P33E" in V.PROFILES else ())


def key_leaks_ts(text, key_value=None, long_alnum=True):
    u"""この便の封の path(32 字に近い英数字・_・- の連なり)を除いて、T5Y の便の検査に渡す。"""
    return TY.key_leaks_ty(text.replace(SEAL_REL, u""), key_value, long_alnum)


@contextlib.contextmanager
def key_check_ts():
    old = GEN.key_leaks
    GEN.key_leaks = key_leaks_ts
    try:
        yield
    finally:
        GEN.key_leaks = old


def write_json_ts(out, rec, text=None, key_value=None):
    text = text if text is not None else json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    with key_check_ts():
        RUN.write_record(out, text, rec, key_value)


def header_ts(root, kind, step, before, after, profiles, cache_dir, only):
    h = collections.OrderedDict()
    h[u"seal"] = SEAL_REL
    h[u"封の commit"] = SEAL_COMMIT
    h[u"step"] = step
    h[u"HEAD の commit"] = GEN.git_head(os.path.dirname(root))
    h[u"この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    h[u"取得の script の sha256"] = sha_rel(root, FETCH_SCRIPT_REL)
    h[u"前の便の script の sha256"] = collections.OrderedDict((rel, sha_rel(root, rel)) for rel in PREV_SCRIPT_RELS)
    fp = os.path.join(root, FETCH_REL)
    h[u"取得の記録の sha256"] = GEN.sha256_file(fp) if os.path.exists(fp) else None
    h[u"engine の指紋"] = VD.engine_fingerprint()
    h[u"lib の指紋"] = collections.OrderedDict((rel, sha_rel(root, rel)) for rel in LIB_RELS)
    h[u"仕掛けの 2 file の sha256"] = collections.OrderedDict((rel, sha_rel(root, rel)) for rel in DEVICE_RELS)
    h[u"profile"] = list(profiles)
    h[u"cache の前後"] = collections.OrderedDict([(u"前", before), (u"後", after), (u"変化なし", before == after)])
    prod = os.path.abspath(cache_dir) == os.path.abspath(FE.default_cache_dir())
    h[u"材料の置き場"] = FE.display_path(cache_dir) if prod else u"使い捨ての置き場(本番の folder ではない)"
    h[u"範囲"] = u"封 §1 の 17 社" if only is None else SCOPE_ONLY
    return h


def seal_text(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def load_books(root=ROOT, only=None, cache_dir=None):
    u"""17 社の (行番号, 証券コード, 番号, sha, 下見の字数, 下見の claim, 97 の記録の行, 概況の字)。表の順。取得の script の ``map_docids`` で有報の行を結ぶ(1 対 1 でなければ止まる)。"""
    cache_dir = cache_dir or FE.default_cache_dir()
    rows = FE.select_rows(only)
    mapping = FE.map_docids(root, [r[1] for r in rows])
    _ids, by = FE.company_rows(root)
    out = []
    for (n, code, number, sha, chars, claims) in rows:
        out.append((n, code, number, sha, chars, claims, by[mapping[code][0]], read_tanshin(cache_dir, code, number, sha)))
    return out


# ======================================================================================================
# states
def unit_family(u):
    u"""単位の族: % と ポイント = %・円族 = 円族・他は 他。"""
    if u in (u"%", u"ポイント"):
        return u"%"
    if u in TUNE.MONEY_FAMILY:
        return u"円族"
    return u"他"


def is_formula(pointers):
    return any(isinstance(p, str) and p.startswith(u"formula:") for p in (pointers or ()))


def is_ab_yen(pointers, family):
    u"""両期の fact を引く a−b(円): pointers に ``formula:a-b``(ちょうどこの字)が在り、単位の族が円族。"""
    return bool(family == u"円族" and u"formula:a-b" in list(pointers or ()))


def profile_rows(zb, text, zm, pname):
    u"""({(文の番号, 位置): (state, reason, pointers, 単位の族, span に % を含む)}, 並びが対応したか, 数の claim の数)。数の claim だけ。span の字は持たず真偽だけ。"""
    prof = V.PROFILES[pname]
    out = VD.verify_document(zb, pname, text)
    nums, texts = R.build_raw_claims(zm, prof)
    raws = nums + texts
    cl = out["claims"]
    ok = len(cl) == len(raws) and all(c["id"] == r["id"] for c, r in zip(cl, raws))
    rows = collections.OrderedDict()
    n = 0
    for c, r in zip(cl, raws):
        if c["kind"] != "num":
            continue
        n += 1
        key = (r["sentence"], r["pos"])
        if key in rows:
            ok = False
        rows[key] = (c["state"], RUN.safe_reason(c["reason"]), tuple(c["pointers"] or ()), unit_family(c["unit"]), u"%" in (c.get("span") or u""))
    return rows, ok, n


def row_entry(key, v):
    u"""記録の行 [文の番号, 位置, state, reason, pointer の期, formula の有無, 単位の族, 両期の fact を引く a−b, span に % を含む]。"""
    return [key[0], key[1], v[0], v[1], PB.period5(v[2]), bool(is_formula(v[2])), v[3], bool(is_ab_yen(v[2], v[3])), bool(v[4])]


def reason_counts(rows):
    out = collections.OrderedDict((s, collections.Counter()) for s in STATES)
    for r in rows:
        out[r[2]][r[3] if r[3] is not None else u"なし"] += 1
    return collections.OrderedDict((s, collections.OrderedDict(sorted(c.items()))) for s, c in out.items())


def state_counts(rows):
    c = collections.Counter(r[2] for r in rows)
    return collections.OrderedDict((s, c.get(s, 0)) for s in STATES)


VM_KEYS = (u"行", u"導出(formula)", u"直接", u"% の数", u"円族の数", u"両期の fact を引く a−b(円)", u"単位の族が %", u"単位の族が円族", u"単位の族が他")


def vm_breakdown(rows):
    u"""VALUE_MISMATCH の行の機械の内訳(封 H-5 の 3 欄 + 直接・参考の単位の族・pointer の期)。"""
    vm = [r for r in rows if r[2] == VM]
    per = collections.Counter(r[4] for r in vm)
    return collections.OrderedDict([
        (u"行", len(vm)), (u"導出(formula)", sum(1 for r in vm if r[5])), (u"直接", sum(1 for r in vm if not r[5])),
        (u"% の数", sum(1 for r in vm if r[8])), (u"円族の数", sum(1 for r in vm if not r[8])),
        (u"両期の fact を引く a−b(円)", sum(1 for r in vm if r[7])),
        (u"単位の族が %", sum(1 for r in vm if r[6] == u"%")), (u"単位の族が円族", sum(1 for r in vm if r[6] == u"円族")), (u"単位の族が他", sum(1 for r in vm if r[6] == u"他")),
        (u"pointer の期", collections.OrderedDict((k, per.get(k, 0)) for k in PERIODS5))])


def profile_block(rows):
    return collections.OrderedDict([
        (u"claim", len(rows)), (u"4 state", state_counts(rows)), (u"reason", reason_counts(rows)), (u"VALUE_MISMATCH の内訳", vm_breakdown(rows)), (u"行", rows)])


def move_entry(key, a, b):
    u"""動いた行 [文の番号, 位置, 前の state, 後の state, 前の期, 後の期]。"""
    return [key[0], key[1], a[0], b[0], PB.period5(a[2]), PB.period5(b[2])]


def states_job(args):
    n, code, number, sha, chars_expect, claims_expect, row, text, profiles = args
    zb = GEN.read_zip(row, GEN.EXISTING_CACHES)
    zm = PR.build_modified_zip(zb, text)[0]
    views, ok, nclaims = collections.OrderedDict(), collections.OrderedDict(), collections.OrderedDict()
    for p in profiles:
        views[p], ok[p], nclaims[p] = profile_rows(zb, text, zm, p)
    sents = RUN.sentence_list(zm, V.PROFILES[NEW])
    common, moved, reason_only = PB.diff_rows(views[OLD], views[NEW])
    book = collections.OrderedDict([
        (u"#", n), (u"証券コード", code), (u"番号", number), (u"ZIP の sha256", sha), (u"概況の字数", len(text)), (u"下見の字数", chars_expect),
        (u"下見の claim(P32E)", claims_expect), (u"文の数", len(sents)), (u"行頭が | の文の数", sum(1 for s in sents if s.startswith(PIPE))),
        (u"対応", ok)])
    book[u"profile"] = collections.OrderedDict((p, profile_block([row_entry(k, v) for k, v in views[p].items()])) for p in profiles)
    book[u"P30E から P32E で動いた行"] = [move_entry(k, views[OLD][k], views[NEW][k]) for k in moved]
    book[u"P30E から P32E で reason だけが違う行"] = len(reason_only)
    return book


def sum_reason(books, p, state, reason):
    return sum(b[u"profile"][p][u"reason"][state].get(reason, 0) for b in books)


def states_columns(books, profiles):
    u"""H-2〜H-5・H-7〜H-9 の欄を ``本`` から数える(記録の ``H の欄`` と tally の判定が使う)。"""
    p32 = [b[u"profile"][NEW] for b in books]
    p27 = [b[u"profile"][u"P27"] for b in books]
    g32 = sum(x[u"4 state"][G] for x in p32)
    g27 = sum(x[u"4 state"][G] for x in p27)
    moved = sum(len(b[u"P30E から P32E で動いた行"]) for b in books)
    vm = collections.OrderedDict((k, sum(x[u"VALUE_MISMATCH の内訳"][k] for x in p32)) for k in
                                 VM_KEYS)
    return collections.OrderedDict([
        (u"H-2", collections.OrderedDict([(u"概況の字数の合計", sum(b[u"概況の字数"] for b in books)), (u"P32E の数の claim の合計", sum(x[u"claim"] for x in p32)),
                                         (u"下見の字数と同じ社", sum(1 for b in books if b[u"概況の字数"] == b[u"下見の字数"])), (u"下見の claim と同じ社", sum(1 for b in books if b[u"profile"][NEW][u"claim"] == b[u"下見の claim(P32E)"]))])),
        (u"H-3", collections.OrderedDict((s, sum(x[u"4 state"][s] for x in p32)) for s in STATES)),
        (u"H-4", collections.OrderedDict([(u"P27 の GROUNDED", g27), (u"P32E の GROUNDED", g32), (u"P27 の GROUNDED は P32E の何 %", pct(g27, g32)),
                                         (u"P30E から P32E で動いた行", moved), (u"reason だけが違う行", sum(b[u"P30E から P32E で reason だけが違う行"] for b in books))])),
        (u"H-5", vm),
        (u"H-7", collections.OrderedDict([(u"target_or_plan", sum_reason(books, NEW, UNV, u"target_or_plan")), (u"no_subject", sum_reason(books, NEW, UNV, u"no_subject"))])),
        (u"H-8", collections.OrderedDict([(u"no_element", sum_reason(books, NEW, PNF, u"no_element")), (u"no_same_value", sum_reason(books, NEW, PNF, u"no_same_value"))])),
        (u"H-9", collections.OrderedDict([(u"行頭が | の文の数", sum(b[u"行頭が | の文の数"] for b in books)), (u"文の数", sum(b[u"文の数"] for b in books))]))])


def states_totals(books, profiles):
    u"""profile ごとの集計(claim・4 state・reason・VALUE_MISMATCH の内訳)。"""
    out = collections.OrderedDict()
    for p in profiles:
        sel = [b[u"profile"][p] for b in books]
        o = collections.OrderedDict([(u"claim", sum(x[u"claim"] for x in sel)),
                                     (u"4 state", collections.OrderedDict((s, sum(x[u"4 state"][s] for x in sel)) for s in STATES))])
        rs = collections.OrderedDict()
        for s in STATES:
            c = collections.Counter()
            for x in sel:
                c.update(x[u"reason"][s])
            rs[s] = collections.OrderedDict(sorted(c.items()))
        o[u"reason"] = rs
        vms = collections.OrderedDict()
        for k in VM_KEYS:
            vms[k] = sum(x[u"VALUE_MISMATCH の内訳"][k] for x in sel)
        pc = collections.Counter()
        for x in sel:
            pc.update(x[u"VALUE_MISMATCH の内訳"][u"pointer の期"])
        vms[u"pointer の期"] = collections.OrderedDict((k, pc.get(k, 0)) for k in PERIODS5)
        o[u"VALUE_MISMATCH の内訳"] = vms
        out[p] = o
    return out


def dumps_states(rec):
    u"""``本`` の中の ``行`` を 1 行 1 claim にして書く。"""
    rec2 = json.loads(json.dumps(rec, ensure_ascii=False))
    stash = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in list(o.items()):
                if k == u"行" and isinstance(v, list) and v and isinstance(v[0], list):
                    stash.append(v)
                    o[k] = u"@@ROWS%d@@" % (len(stash) - 1)
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(rec2)
    text = json.dumps(rec2, ensure_ascii=False, indent=1)
    for i, rows in enumerate(stash):
        body = u"[\n" + u",\n".join(u"   " + json.dumps(r, ensure_ascii=False) for r in rows) + u"\n   ]"
        text = text.replace(json.dumps(u"@@ROWS%d@@" % i), body)
    return text + u"\n"


def run_states(root=ROOT, procs=1, only=None, out=None, cache=None, key_value=None, say=print):
    if out is None:
        if only is not None:
            raise Stop(u"**--only を付けた走らせ方は本番の記録を作らない。--out を指定する。止める**")
        out = os.path.join(root, STATES_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    cache_dir = cache_dir_for(None if is_production_out(root, out, STATES_REL) else out, cache)
    profiles = engine_profiles_now()
    books_in = load_books(root, only, cache_dir)
    caches = caches_all()
    before = GEN.caches_snapshot(caches)
    jobs_ = [(n, code, number, sha, chars, claims, row, text, profiles) for (n, code, number, sha, chars, claims, row, text) in books_in]
    say(u"states %d 社 × profile %s ― procs %d" % (len(jobs_), u"・".join(profiles), procs))
    books = NF.map_pool(states_job, jobs_, procs)
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header_ts(root, "states", u"TS(人が書いた有報の外の文)― 決算短信の概況 × profile の判定(0 USD)", before, after, profiles, cache_dir, only)
    rec[u"切り出し"] = collections.OrderedDict([
        (u"規則", u"qualitative.htm の tag を剥がし(script・style を除き、br・/p・/div・/tr・/h*・/li を改行)、unescape、行の空白の連なりを 1 つに(行頭・行末は削らない)・空白だけの行を詰め、"
                u"「１．経営成績等の概況」で始まり「……」を持たない最後の行から、その後で最初の「２．」で始まる行の直前まで、NFKC"),
        (u"NFKC", True), (u"下見の字数の合計", sum(r[4] for r in FE.select_rows(only))), (u"字数の合計", sum(b[u"概況の字数"] for b in books)),
        (u"下見と字数が同じ社", sum(1 for b in books if b[u"概況の字数"] == b[u"下見の字数"]))])
    rec[u"社の数"] = len(books)
    rec[u"集計"] = states_totals(books, profiles)
    rec[u"H の欄"] = states_columns(books, profiles)
    rec[u"限界"] = list(STATES_LIMITS)
    rec[u"key_leaks"] = []
    rec[u"本"] = books
    write_json_ts(out, rec, text=dumps_states(rec), key_value=key_value)
    say(u"-> %s(社 %d)" % (os.path.basename(out), len(books)))
    return rec


# ======================================================================================================
# inject
@contextlib.contextmanager
def base_pair():
    u"""``RM.base_status_rb`` が引く (比較, 土台) の対を with の中だけ (P32E, P30E) にする。出るときは必ず戻す。"""
    old = RM.INJECT_PROFILES
    RM.INJECT_PROFILES = (NEW, OLD)
    try:
        yield
    finally:
        RM.INJECT_PROFILES = old


def base_status_ts(base_claims, base_by_id, tok, text):
    u"""(状態, 土台)。土台 = 無改変の文で P30E が GROUNDED の claim。P32E の claim は (value, span, unit) が同じ 1 件があれば結ぶ。``RM.base_status_rb`` をそのまま呼ぶ(対だけ替える)。"""
    with base_pair():
        return RM.base_status_rb(base_claims, base_by_id, tok, text)


@contextlib.contextmanager
def t8_base_status():
    u"""``RUN.base_status4``(``RUN.t8_candidates4`` が引く名前)を with の中だけ ``base_status_ts`` にする。出るときは必ず戻す。"""
    old = RUN.base_status4
    RUN.base_status4 = base_status_ts
    try:
        yield
    finally:
        RUN.base_status4 = old


def wiring_problems():
    out = list(TY.wiring_problems())
    with t8_base_status():
        if RUN.t8_candidates4.__globals__["base_status4"] is not base_status_ts:
            out.append(u"RUN.t8_candidates4 が引く base_status4 が差し替えた先でない")
    if tuple(INJECT_PROFILES) != (OLD, NEW):
        out.append(u"profile の対が (P30E, P32E) でない")
    return out


@contextlib.contextmanager
def relaxed_reason():
    u"""``TUNE.safe_reason``(``TUNE.classify`` が引く名前)を with の中だけ ``RUN.safe_reason``(engine が宣言した固定の reason も通す)にする。出るときは必ず戻す。
    決算短信の文では reason に ``no_element(no prior2 for prior-year diff)`` のように括弧の中に数字を持つ engine 宣言の符号が出て、TUNE の版は止まる。数や文が混ざる字は RUN の版も止める。"""
    old = TUNE.safe_reason
    TUNE.safe_reason = RUN.safe_reason
    try:
        yield
    finally:
        TUNE.safe_reason = old


def classify_ts(res, base):
    with relaxed_reason():
        return TUNE.classify(res, base)


def pair_period(found):
    return PB.period5(found.get("pointers")) if found is not None else u"なし"


def build_row(zb, text, verify, base_claims, base_by_id, typ, inj, tok, bc, extra):
    u"""注入 1 件の行(T9 の第 2 便と同じ欄 + 型。対応は id で引く 3 条件)。(行, 注入後の文)。"""
    profiles = INJECT_PROFILES
    tampered, placements = IJ.apply_edits(text, [inj])
    rt = IJ.revert(tampered, [inj], placements, text) == text
    target = SC.scaled_value(inj["new_value"], tok.unit)
    orig_digits = text[tok.start:tok.end]
    row = collections.OrderedDict([
        ("id", inj["id"]), ("型", typ), ("形", PS.shape_of_token(tok)), ("単位", tok.unit),
        ("基準の claim", bc["id"]), (LINK_KEY, bc["ids"][NEW] is not None),
        ("round-trip", bool(rt)), ("読み直し", bool(JT.reread_j(tampered, tok, inj["new_value"], tok.unit))),
        ("先頭の位が減った", bool(tok.groups is not None and NS.groups_in(inj["replacement"]) < len(tok.groups))),
        ("engine の手がかり", PS.engine_cue(text, tok)), ("文に前期の語", PS.has_prior_word(text, tok)),
        ("基準の pointer の期", PB.period5(bc.get("pointers")))])
    row.update(extra)
    conds, miss, old, found = {}, {}, {}, {}
    same_n = False
    for p in profiles:
        if bc["ids"][p] is None:
            row[p] = classify_ts(None, None)
            conds[p], miss[p], found[p] = None, [PI.NO_BASE], None
            old[p] = collections.OrderedDict([(PI.OLD_KEYS[0], False), (PI.OLD_KEYS[1], False)])
            continue
        claims = verify(zb, p, tampered)["claims"]
        res, conds[p], miss[p], found[p] = PI.id_map(claims, bc["ids"][p], target, inj["replacement"])
        row[p] = classify_ts(res, base_by_id[p][bc["ids"][p]])
        old[p] = PI.old_map(claims, inj, tok.unit, bc["ids"][p])
        if p == NEW:
            same_n = len(claims) == len(base_claims[p])
    for p in profiles:
        row[u"%s の注入後の pointer の期" % p] = pair_period(found[p])
    row["届いた"] = PS.reached_of(orig_digits, bc.get("span"), found[NEW], inj["replacement"])
    for p in profiles:
        row[PI.F_COND % p] = conds[p]
    for p in profiles:
        row[PI.F_MISS % p] = miss[p]
    for p in profiles:
        row[PI.F_OLD % p] = old[p]
    row[u"注入の前後で claim の数が同じ(P32E)"] = bool(same_n)
    return row


def status_counter(pop):
    return collections.OrderedDict(sorted(pop.items()))


def inject_text_ts(zb, text, refs, seed, key, cap=None, verify=None):
    u"""1 社の注入(T1・T5・T8・T9 を 1 件ずつ。round-trip は止めずに数える)。(行, 数え)。切り替え 2 つ 真の中で呼ぶ。"""
    cap = RUN.INJECT_CAP if cap is None else cap
    if N.normalize_digits(text) != text:
        return [], collections.OrderedDict([(u"注入しない", u"文に全角の数字がある(select は半角の文を前提にする)")])
    verify = verify or VD.verify_document
    profiles = INJECT_PROFILES
    base_claims = dict((p, verify(zb, p, text)["claims"]) for p in profiles)
    base_by_id = dict((p, dict((c["id"], c) for c in base_claims[p])) for p in profiles)
    toks = dict(((t.start, t.end), t) for t in N.scan(text))
    counts = collections.OrderedDict()
    work = []                                              # (型, inj, tok, bc, extra)

    # ---- T1(仕掛けの select のまま。cap は採用に掛ける)
    chosen, cat, _a, _w = IJ.select(text, refs, "xbrl", seed, key, cap, types=[T1])
    pop = collections.Counter()
    n = 0
    for inj in chosen:
        tok = toks[tuple(inj["span"])]
        st, bc = base_status_ts(base_claims, base_by_id, tok, text)
        pop[st] += 1
        if bc is not None:
            n += 1
            inj["id"] = "%s-T1-%02d" % (key, n)
            work.append((T1, inj, tok, bc, collections.OrderedDict()))
    counts[T1] = collections.OrderedDict([(u"作れる site", cat[T1]), (u"採った", len(chosen)), (u"採った の状態", status_counter(pop))])

    # ---- T5(土台 GROUNDED の site を先頭から cap 件)
    sites, rng = TY.t5_all_sites(text, refs, seed, key)
    ok, pop = [], collections.Counter()
    for s in sites:
        st, bc = base_status_ts(base_claims, base_by_id, s["token"], text)
        pop[st] += 1
        if bc is not None:
            ok.append((s, bc))
    c5 = collections.OrderedDict([(u"作れる site", TY.shape_counter(sites)), (u"作れる site の状態", status_counter(pop)),
                                  (u"土台 P30E が GROUNDED の site", len(ok)), (u"cap を基準で絞る前に掛けた数", min(cap, len(sites)))])
    n = 0
    for s, bc in ok[:cap]:
        n += 1
        tok = s["token"]
        inj = IJ.build_t5(s, refs, rng)
        inj["type"] = T5
        inj["id"] = "%s-T5-%02d" % (key, n)
        ckey = inj["detail"]["coincident_ref_key"]
        extra = collections.OrderedDict([("相手の fact の期", TY.partner_period(ckey)), ("相手と同じ要素か", bool(TY.same_element(inj["detail"]["true_ref_key"], ckey)))])
        work.append((T5, inj, tok, bc, extra))
    c5[u"採った"] = n
    counts[T5] = c5

    # ---- T8(RUN.t8_candidates4。土台の判定を (P32E, P30E) の対に差し替える。cap は site に掛ける)
    with t8_base_status():
        t8, c8 = RUN.t8_candidates4(text, refs, base_claims, base_by_id, seed, key, cap)
    counts[T8] = collections.OrderedDict(sorted(c8.items()))
    for inj, tok, bc in t8:
        work.append((T8, inj, tok, bc, collections.OrderedDict([("r", inj["detail"]["relative"]), ("r を決めた回", inj["detail"]["tries"])])))

    # ---- T9(土台 GROUNDED の site を先頭から cap 件。T9 の第 2 便と同じ作り)
    stages, sites = PS.t9_all_sites(text, refs, seed, key)
    ok, pop = [], collections.Counter()
    for s in sites:
        st, bc = base_status_ts(base_claims, base_by_id, s["token"], text)
        pop[st] += 1
        if bc is not None:
            ok.append((s, bc))
    c9 = collections.OrderedDict([(u"段", stages), (u"作れる site", PS.shape_counter(sites)), (u"作れる site の状態", status_counter(pop)),
                                  (u"土台 P30E が GROUNDED の site", len(ok)), (u"cap を基準で絞る前に掛けた数", min(cap, len(sites)))])
    n = 0
    for s, bc in ok[:cap]:
        n += 1
        work.append((T9, PS.build_t9(s, "%s-T9-%02d" % (key, n)), s["token"], bc, collections.OrderedDict()))
    c9[u"採った"] = n
    counts[T9] = c9

    rows = [build_row(zb, text, verify, base_claims, base_by_id, typ, inj, tok, bc, extra) for typ, inj, tok, bc, extra in work]
    return rows, counts


def inject_job_ts(args):
    n, code, number, sha, row, text, zip_caches, seed, work_root = args
    if not getattr(N, TY.FLAG) or not getattr(S, TY.FLAG2):
        raise Stop(u"**切り替えが偽のまま inject を走らせた。止める**")
    zb = GEN.read_zip(row, zip_caches)
    refs = RUN.refs_for(row, zip_caches, work_root)
    rows, counts = inject_text_ts(zb, text, refs, seed, "%s_TS" % code)
    out = []
    for r in rows:
        d = collections.OrderedDict([(u"証券コード", code)])
        d.update(r)
        out.append(d)
    return code, out, counts


def inject_summary(rows):
    u"""型 × profile の結果の語の数(分母 = その型の注入の行)。"""
    labels = (LABEL_PASS, LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
    out = collections.OrderedDict()
    for t in TYPES:
        sel = [r for r in rows if r[u"型"] == t]
        o = collections.OrderedDict([(u"注入の行", len(sel))])
        for p in INJECT_PROFILES:
            c = collections.Counter(r[p][u"結果"] for r in sel)
            d = collections.OrderedDict([(u"注入の行", len(sel))])
            for w in labels:
                d[w] = collections.OrderedDict([(u"件", c.get(w, 0)), (u"率", pct(c.get(w, 0), len(sel)))])
            o[p] = d
        out[t] = o
    return out


def inject_columns(per, rows):
    u"""H-6 の欄(型ごとの通した率 P32E・T9 の注入の行)と参考の欄を ``本ごとの数え`` と ``行`` から数える。"""
    def rate(t, p):
        sel = [r for r in rows if r[u"型"] == t]
        return pct(sum(1 for r in sel if r[p][u"結果"] == LABEL_PASS), len(sel))
    n9 = sum(1 for r in rows if r[u"型"] == T9)
    ref = collections.OrderedDict([
        (u"注入の行", len(rows)), (u"型ごとの注入の行", collections.OrderedDict((t, sum(1 for r in rows if r[u"型"] == t)) for t in TYPES)),
        (u"通した率 P30E", collections.OrderedDict((TYPE_SHORT[t], rate(t, OLD)) for t in TYPES)),
        (u"P32E に対応が付かない行", sum(1 for r in rows if not r[LINK_KEY])),
        (u"round-trip 不一致", sum(1 for r in rows if not r[u"round-trip"])), (u"読み直し不一致", sum(1 for r in rows if not r[u"読み直し"])),
        (u"届かない行(P32E に対応が付く行の中)", sum(1 for r in rows if r[NEW][u"対応"] and not r[u"届いた"]))])
    return collections.OrderedDict([
        (u"H-6", collections.OrderedDict([(u"通した率 P32E", collections.OrderedDict((TYPE_SHORT[t], rate(t, NEW)) for t in TYPES)), (u"T9 の注入の行", n9)])),
        (u"参考", ref)])


def run_inject(root=ROOT, procs=1, only=None, out=None, cache=None, key_value=None, say=print, work_root=None):
    if out is None:
        if only is not None:
            raise Stop(u"**--only を付けた走らせ方は本番の記録を作らない。--out を指定する。止める**")
        out = os.path.join(root, INJECT_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    if getattr(N, TY.FLAG) or getattr(S, TY.FLAG2):
        raise Stop(u"**切り替えが真のまま inject を始めた。止める**")
    bad = wiring_problems()
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    cache_dir = cache_dir_for(None if is_production_out(root, out, INJECT_REL) else out, cache)
    seed, seed_meta = GEN.seed_value(root)
    books_in = load_books(root, only, cache_dir)
    caches = caches_all()
    before = GEN.caches_snapshot(caches)
    work_root = work_root or tempfile.mkdtemp(prefix="tanshin_inject_", dir=os.environ.get("TMPDIR"))
    jobs_ = [(n, code, number, sha, row, text, GEN.EXISTING_CACHES, seed, work_root) for (n, code, number, sha, _c, _cl, row, text) in books_in]
    say(u"注入 %d 社 × 4 型 × 2 profile(P30E・P32E)。切り替え 2 つ 真・id で引く対応付け ― procs %d(1 件ごとに判定。時間がかかる)" % (len(jobs_), procs))
    with NS.yen_scan_on():
        with TY.t5_yen_on():
            if not getattr(N, TY.FLAG) or not getattr(S, TY.FLAG2) or wiring_problems():
                raise Stop(u"**切り替えを真にできない・配線が崩れた。止める**")
            results = NF.map_pool(inject_job_ts, jobs_, procs)
    if getattr(N, TY.FLAG) or getattr(S, TY.FLAG2):
        raise Stop(u"**with を出ても切り替えが真のまま。止める**")
    rows, per = [], collections.OrderedDict()
    for code, r, c in results:
        rows += r
        per[code] = c
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header_ts(root, "inject", u"TS(人が書いた有報の外の文)― 決算短信の概況への注入 T1・T5・T8・T9(P30E・P32E。切り替え 2 つ 真。0 USD)", before, after, INJECT_PROFILES, cache_dir, only)
    rec[u"切り替え"] = collections.OrderedDict([
        (u"名前", TY.FLAG), (u"inject の中の値", True), (u"出たあとの値", bool(getattr(N, TY.FLAG))),
        (u"T5 の切り替えの名前", TY.FLAG2), (u"T5 の切り替え inject の中の値", True), (u"T5 の切り替え 出たあとの値", bool(getattr(S, TY.FLAG2))), (u"配線の問題", wiring_problems())])
    rec[u"種"] = {u"file": RUN.SEED_REL_STR, u"種の確認": seed_meta}
    rec[u"cap"] = RUN.INJECT_CAP
    rec[u"型"] = collections.OrderedDict([
        (T1, u"inject.select(types=[T1_VALUE]) のまま(新しい token に絞らない)。cap は採用に掛ける(基準で絞る前)"),
        (T5, u"S.t5_sites(切り替え 2 つ 真)の site を token の start の順に並べ <seed>|<本の名前>|T5_COINCIDENT で並べ替え、土台 P30E GROUNDED の site を先頭から cap 件。差し替えは IJ.build_t5"),
        (T8, u"RUN.t8_candidates4(円族の token・r ∈ %s・%d 回まで。土台の判定を (P32E, P30E) の対に差し替える)。cap は site に掛ける" % (list(TUNE.T8_R_VALUES), TUNE.T8_TRIES)),
        (T9, u"T9 の第 2 便と同じ site・並べ替え・cap・差し替え(PS.t9_all_sites・PS.build_t9)"),
        (u"上限", u"型ごと・1 本あたり %d" % RUN.INJECT_CAP),
        (u"土台", PS.BASE_WORD),
        (u"土台の結び方", u"P30E の claim を find_base_claim で 1 件に決め、P32E の claim は (value, span, unit) が同じ 1 件があれば結ぶ。無ければその行の P32E の欄は対応なし(判定しない)"),
        (u"対応付け", u"注入後の文の claim のうち id が基準の claim の id の claim c が、(ア)在る (イ)値が注入した値(円に直して TUNE.same_number) (ウ)span に差し替えの字が在る、の 3 つ全部のときだけ対応が付く。欠けた条件は行に持つ"),
        (u"期", u"id で引いた claim の pointers の先頭の context の先頭の語: CurrentYear / Prior1Year / Prior2Year / 他 / なし。要素名は持たない"),
        (u"inject の本の名前の引数", u"<証券コード>_TS")])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"] = inject_summary(rows)
    rec[u"H の欄"] = inject_columns(per, rows)
    rec[u"限界"] = list(INJECT_LIMITS)
    rec[u"key_leaks"] = []
    rec[u"行"] = rows
    write_json_ts(out, rec, text=RUN.dumps_inject(rec), key_value=key_value)
    say(u"-> %s(注入の行 %d)" % (os.path.basename(out), len(rows)))
    return rec


# ======================================================================================================
# tally: 封の表(§3 の H-1〜H-10)を読み、記録から判定する(H-10 は門なし = 判定しない)
HIT, MISS = u"当たり", u"外れ"
READ = u"司令塔が読む"
H_IDS = tuple("H-%d" % i for i in range(1, 11))
H_NOT_GATED = u"H-10"


def read_seal(root=ROOT):
    return seal_text(root)


def seal_pred_rows(seal):
    u"""封 §3 の表の行 {H-n: (欄, 予測, 外れ方)}。"""
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| (H-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            out[m.group(1)] = (cells[0], cells[1], cells[2] if len(cells) > 2 else u"")
    return out


_NUM = r"\d[\d,]*(?:\.\d+)?"


def _f(s):
    return float(s.replace(u",", u""))


def pred_numbers(cell):
    u"""予測の欄の単独の数(コンマ付きも)を出る順に。ラベル(T1 など)を持つ欄では使わない。"""
    return [_f(x) for x in re.findall(_NUM, cell)]


def pred_ranges(cell):
    u"""予測の欄の ``a〜b`` を出る順に (a, b)。"""
    return [(_f(a), _f(b)) for a, b in re.findall(u"(%s)〜(%s)" % (_NUM, _NUM), cell)]


def seal_bounds(seal):
    u"""封の字から読んだ幅(門が literal に留めた値と照らす)。{H-n: 値}。"""
    rows = seal_pred_rows(seal)
    b = collections.OrderedDict()
    for k in H_IDS:
        cell = rows[k][1] if k in rows else u""
        if k in ("H-1", "H-2", "H-3", "H-5", "H-7", "H-8", "H-9"):
            b[k] = pred_numbers(cell)
        elif k in ("H-4", "H-6"):
            b[k] = pred_ranges(cell)
        else:
            b[k] = None
    return b


def columns_from_records(fetch, states, inject):
    u"""H-1〜H-9 の実測の値(記録の行・本から数え直す)。"""
    frows = fetch[u"行"]
    table = dict((r[1], r) for r in TABLE)
    matched = sum(1 for r in frows if r[u"証券コード"] in table and r[u"ZIP の sha256"] == table[r[u"証券コード"]][3] and r[u"番号"] == table[r[u"証券コード"]][2])
    sc = states_columns(states[u"本"], list(states[u"集計"]))
    ic = inject_columns(inject[u"本ごとの数え"], inject[u"行"])
    return collections.OrderedDict([
        (u"H-1", (matched, len(frows))),
        (u"H-2", (sc[u"H-2"][u"概況の字数の合計"], sc[u"H-2"][u"P32E の数の claim の合計"])),
        (u"H-3", tuple(sc[u"H-3"][s] for s in STATES)),
        (u"H-4", (sc[u"H-4"][u"P27 の GROUNDED は P32E の何 %"], sc[u"H-4"][u"P30E から P32E で動いた行"])),
        (u"H-5", (sc[u"H-5"][u"導出(formula)"], sc[u"H-5"][u"% の数"], sc[u"H-5"][u"両期の fact を引く a−b(円)"])),
        (u"H-6", tuple(ic[u"H-6"][u"通した率 P32E"][TYPE_SHORT[t]] for t in TYPES) + (ic[u"H-6"][u"T9 の注入の行"],)),
        (u"H-7", (sc[u"H-7"][u"target_or_plan"], sc[u"H-7"][u"no_subject"])),
        (u"H-8", (sc[u"H-8"][u"no_element"], sc[u"H-8"][u"no_same_value"])),
        (u"H-9", (sc[u"H-9"][u"行頭が | の文の数"],))])


def judge_from(cols, bounds):
    u"""{H-n: 判定(当たり / 外れ / 司令塔が読む)}。None(分母 0 など)は外れ。H-10 は判定しない。"""
    def same(v, want):
        return v is not None and len(v) == len(want) and all(x is not None and abs(x - w) < 1e-9 for x, w in zip(v, want))
    out = collections.OrderedDict()
    for k in H_IDS:
        v = cols.get(k)
        if k == H_NOT_GATED:
            out[k] = READ
        elif k in ("H-1", "H-2", "H-3", "H-5", "H-7", "H-8", "H-9"):
            out[k] = HIT if same(v, bounds[k]) else MISS
        elif k == "H-4":
            r = bounds[k]
            out[k] = HIT if (v is not None and len(r) == 2 and within(v[0], r[0]) and within(v[1], r[1])) else MISS
        else:                                                   # H-6: T1・T5・T8・T9 の率 4 つ + T9 の行
            r = bounds[k]
            out[k] = HIT if (v is not None and len(r) == 5 and all(within(v[i], r[i]) for i in range(5))) else MISS
    return out


def fmt(v):
    if v is None:
        return u"なし(分母 0)"
    if isinstance(v, (tuple, list)):
        return u" / ".join(fmt(x) for x in v)
    if isinstance(v, float):
        return (u"%.1f" % v).rstrip(u"0").rstrip(u".") if v != int(v) else u"%d" % int(v)
    if isinstance(v, int):
        return u"{:,}".format(v)
    return u"%s" % v


MEASURE_LABELS = {
    u"H-1": u"取得した ZIP の sha256 が表と一致 / 行",
    u"H-2": u"概況の字数の合計 / P32E の数の claim の合計",
    u"H-3": u"P32E の GROUNDED / VALUE_MISMATCH / UNVERIFIABLE / POINTER_NOT_FOUND",
    u"H-4": u"P27 の GROUNDED は P32E の何 %(%)/ P30E から P32E で動いた行",
    u"H-5": u"導出(formula)/ % の数(span に % を含む行)/ 両期の fact を引く a−b(円)",
    u"H-6": u"通した率 P32E %(T1 / T5 / T8 / T9)/ T9 の注入の行",
    u"H-7": u"UNVERIFIABLE の reason: target_or_plan / no_subject",
    u"H-8": u"POINTER_NOT_FOUND の reason: no_element / no_same_value",
    u"H-9": u"行頭が | の文の数"}


def render_pred(cols, judge, seal):
    u"""予測の表(封の字の欄・予測 + 実測 + 判定)。"""
    rows = seal_pred_rows(seal)
    lines = [u"| # | 欄 | 予測(封) | 実測 | 判定 |", u"|---|---|---|---|---|"]
    for k in H_IDS:
        a, p, _o = rows[k]
        if k == H_NOT_GATED:
            lines.append(u"| %s | %s | %s | %s | %s |" % (k, a, p, u"(司令塔が結果の文書で読む)", READ))
        else:
            lines.append(u"| %s | %s | %s | %s: %s | %s |" % (k, a, p, MEASURE_LABELS[k], fmt(cols[k]), judge[k]))
    return u"\n".join(lines)


def render_states(states, inject):
    u"""state の表(profile ごとの 4 state・注入の型 × profile の結果)。"""
    tot = states[u"集計"]
    lines = [u"| profile | 数の claim | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND |", u"|---|---|---|---|---|---|"]
    for p, o in tot.items():
        lines.append(u"| %s | %s | %s | %s | %s | %s |" % ((p, fmt(o[u"claim"])) + tuple(fmt(o[u"4 state"][s]) for s in STATES)))
    lines += [u"", u"| 型 | profile | 注入の行 | 通した | 名指して原本 | 名指したが別の値 | 止めたが名指さない(PNF) | 止めたが名指さない(UNV) | 対応が付かない |", u"|---|---|---|---|---|---|---|---|---|"]
    labels = (LABEL_PASS, LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
    for t in TYPES:
        for p in INJECT_PROFILES:
            d = inject[u"集計"][t][p]
            lines.append(u"| %s | %s | %s | %s |" % (TYPE_SHORT[t], p, fmt(d[u"注入の行"]), u" | ".join(u"%s(%s %%)" % (fmt(d[w][u"件"]), fmt(d[w][u"率"])) for w in labels)))
    return u"\n".join(lines)


def load_records(root=ROOT):
    return collections.OrderedDict((k, FE.GEN.jload(os.path.join(root, rel))) for k, rel in REC_REL.items())


def build_H(R_, seal):
    cols = columns_from_records(R_[u"fetch"], R_[u"states"], R_[u"inject"])
    bounds = seal_bounds(seal)
    return collections.OrderedDict([(u"cols", cols), (u"bounds", bounds), (u"judge", judge_from(cols, bounds))])


def run_tally(root=ROOT, say=print):
    R_ = load_records(root)
    seal = read_seal(root)
    H = build_H(R_, seal)
    say(u"## 予測の表\n")
    say(render_pred(H[u"cols"], H[u"judge"], seal))
    say(u"\n## state の表\n")
    say(render_states(R_[u"states"], R_[u"inject"]))
    return H


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("states", "inject", "tally"))
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--only", default=None, help="この証券コードの 1 社だけ(本番の記録ではない。--out が要る)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--cache", default=None, help="材料の ZIP の置き場(既定: --out が無ければ本番・有れば <--out の folder>/cache)")
    a = ap.parse_args(argv)
    if a.cmd == "states":
        run_states(root=a.root, procs=a.procs, only=a.only, out=a.out, cache=a.cache)
    elif a.cmd == "inject":
        run_inject(root=a.root, procs=a.procs, only=a.only, out=a.out, cache=a.cache)
    else:
        run_tally(root=a.root)


if __name__ == "__main__":
    main()
