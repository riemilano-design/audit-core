# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PLAN_SOURCE_SEAL_2026-11-17.md(PS ― engine が「計画・予想の数」として止めた行に、同じ短信のサマリーの予想の fact という当てる先が在るかを数える)の測定。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(``core/``・``adapters/``)は 1 行も変えない。**材料は TSS の置き場(~/.cache/audit-core/tanshin-self-2026-11-14/)の ZIP 400 本を読むだけ。

    python3 measure/xbrl_plan_source_2026-11-17.py states --out PATH [--material DIR] [--procs N]      # 400 本を作り直して TSS の記録と照らし、P・W・N を数える → fixtures/xbrl/plan_source/states_2026-11-17.json
    python3 measure/xbrl_plan_source_2026-11-17.py states --check [--material DIR] [--procs N]         # 書かずに作り直し、在る記録と比べる(時間の欄は除く)
    python3 measure/xbrl_plan_source_2026-11-17.py sheet --states PATH --material DIR --sheet PATH     # 封 §2-7 の標本を引き、読むための紙を repo の外に書く(標準出力は件数だけ)
    python3 measure/xbrl_plan_source_2026-11-17.py types --states PATH --typed PATH --out PATH         # 付けた字の file を確かめて read_types_2026-11-17.json を書く

実装の注(封が 1 通りに決めていない細部の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 前の便の部品は TSS の script(``load_module`` の形で読む)の ``cut``・``wrap``・``ST.default_cache_dir``・``ST.read_population``・``ST.validate_population`` を **呼ぶ**(写さない)。
  claim と raw の対応は 2026-11-09 の便の ``profile_rows`` と同じ(``verify_document(包んだ ZIP, "P33E")`` と ``build_raw_claims`` の zip)。鍵は raw の (文の番号, 位置)。reason は ``RUN.safe_reason`` を通す。
- 作り直しの確認(封 §2-1 の 2)は、本ごとに「切り出しの可否・数の claim の (文の番号, 位置, state, reason) の並び」が states の記録(封 §1 の 1)と同じこと。違えば Stop。
- 母集団: TSS の封の表(``ST.read_population``)を読み、材料の ZIP の sha256 を 1 本ずつ照らす。母集団の記録 population_2026-11-14.json の行(#・群・様式の種類・sha256)も同じ表と同じことを確かめ、その file の sha256 を記録に書く(封 §1 の表の外の追加の確認)。
- engine の指紋: ``verify_document.engine_fingerprint()`` のうち ``git_commit`` を除く 4 欄を、states の記録のものと照らす(``git_commit`` は HEAD で変わるので比べない・書かない)。記録は HEAD の commit も書かない(--check を commit をまたいで通すため)。
- サマリーの member = 名前が ``XBRLData/Summary/`` で始まり ``-ixbrl.htm`` で終わるもの(ちょうど 1 つ)。fact の「単位が無い」= unit が None か空の字。「値が 0」= value == 0。
- F の判定の「members」は context の ``members``(``:`` の後ろの名前が ForecastMember・UpperMember・LowerMember のどれか)。context が無い fact は F でなく R。
- F は切れた本だけで作る(切れない本は claim が無い)。「F が空の本」は切れた本のうち。
- 円の fact の単位 = 大文字にして JPY で始まるもの。% の fact の単位 = ``Pure`` と完全一致。
- % の照合の ``value`` は raw の claim の ``value``(符号つき)。円は ``value × unit_scale`` を ``match_value`` の target に渡す(梯子が絶対値でも当てる)。
- 単位の族(記録の行の欄)= raw の claim の ``unit`` が ``円`` なら 円・``%`` なら %・それ以外は 他(当てない行を含む。円で claim_scale が None の行は 円 の族のまま「当てない」が真)。
- 別の本(封 §2-6): 群の順は 甲・乙・丙(母集団の並び)、本は (群, #) の順。切れた本で F が空でないものだけが輪。輪が 1 本以下の群があれば Stop。
- 標本(封 §2-7)の番号: P の標本が 1 から(# の順・文の番号の順・位置の順)、続けて W の「自」が真の行が全部(同じ順)。W の「自」が真の行は P の標本の数の次の番号から。P と W の別は番号で決まる(記録の ``標本の規則`` に P の標本の数を持つ)。
- 読むための紙には、封が挙げた項目のほかに、読むために要る claim の span・合った fact の期(開始・終了・instant)と members を足した(紙は repo の外。記録には持たない)。
- 記録に持つ行は P と W の行だけ。N は数だけ(行を持たない)。記録は文・span・値・要素名・context の字・会社名・証券コード・docID を持たない(単位の id と fact の数だけ)。
- 封 §7(追記。commit 5b38862e): 主の数は字のとおりの読み(単位の字が 円 だけ)。並べて「円の族」の読み(円・千円・万円・百万円・億円・兆円で unit_scale と claim_scale が None でない)も数え、
  記録に「封の後・試走の数を見た後に足した読み」の字つきで別の塊として持つ。行は 2 つの読みの札を持つ。scale が無い claim(円の族の単位の字で unit_scale か claim_scale が None)はどちらの読みでも当てない(scale は作らない)。その行の数も持つ。
  標本は 甲組(字のとおりで自が真の P から 60)・乙組(円の族でだけ自が真の P から同じ種で 30)・W 組(円の族で自が真の W 全部)。
- 単位の族(記録の行の欄)は raw の単位の字が 円の族のどれか → 円・% → %・他 → 他(旧: 円だけ。§7 の円の族に合わせて広げた)。
- 封 §8(追記。commit 3e8a722d。独立監査の REVISE の後): ``load_instance`` の inline XBRL の読み取りは自己閉じの tag(``<ix:nonFraction ... xsi:nil="true" />``)を始まりの tag と読み、次の fact の終わりの tag までを 1 つの fact にする。
  主の数は §2-3 の字のとおり(``load_instance`` にそのまま)で数える。並べて「空の欄を除く読み」(サマリーの member の bytes から正規表現 ``<ix:nonFraction[^>]*/>`` に当たる所を取り除き、ほかは 1 byte も変えずに包む)でも
  同じ数を全部数え、「封の後・監査の数え直しを見た後に足した読み(あと知恵)」と字で添える。読みは 2 × 2 の 4 通り(単位: 字のとおり / 円の族 × サマリー: そのまま / 空の欄を除く)。行は 22 欄(前の 15 欄は不変・後ろに空の欄を除く読みの札)。
  別の本の輪(封 §2-6)は読みごとに、その読みの F が空でない本で作る(「対照の輪は §2 のまま」の読み。輪の作り方は変えず、F をその読みのものにする)。
  標本(封 §8 の 5)は「空の欄を除く読み」の札から引く(甲組 = 単位が字のとおりで自が真の P から 60・乙組 = 円の族でだけ自が真の P から 30・W組 = 円の族で自が真の W の全部)。紙の fact も空の欄を除く読みの F。
  自己閉じの tag から始まる読み取りの数と本の数を、サマリー(400 本の全部)と短信の本体(``XBRLData/Attachment/`` の ``.htm``)の両方で数える(engine と同じ正規表現 ``<ix:nonFraction([^>]*)>(.*?)</ix:nonFraction>``(re.S)の一致のうち属性の列が ``/`` で終わるもの。数えるだけ・engine は直さない)。
- ``--check`` は「作り直した記録が在る記録と同じか」を見るだけで、fact の読みが正しいかは見えない(封 §8 の欠陥は ``--check`` が緑のまま在った)。fact の読みの正しさは、読み取りを元の字と突き合わせる試験(門)で縛る。
- 時間(秒)以外は 2 回走らせて byte で同じ(本・辞書の順を固定)。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import random
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


TSS = load_module("xbrl_tanshin_self_2026-11-14.py", "tanshin_self_for_plan_source")      # TSS の script(cut・wrap・置き場・母集団・止め方)
ST = TSS.ST
TS = TSS.TS
Stop = ST.Stop

from adapters.xbrl import instance as I                 # noqa: E402
from adapters.xbrl import verify_document as VD         # noqa: E402
from adapters.xbrl import vocabulary as V               # noqa: E402

SEAL_REL = "docs/XBRL_PLAN_SOURCE_SEAL_2026-11-17.md"
SEAL_COMMIT = "a080ce5f"
ADDENDUM_COMMIT = "5b38862e"          # 封 §7(追記)の commit
ADDENDUM8_COMMIT = "3e8a722d"         # 封 §8(追記)の commit
SCRIPT_REL = "measure/xbrl_plan_source_2026-11-17.py"
REC_DIR_REL = "fixtures/xbrl/plan_source"
STATES_REL = REC_DIR_REL + "/states_2026-11-17.json"
TYPES_REL = REC_DIR_REL + "/read_types_2026-11-17.json"
DOC_REL = "docs/XBRL_PLAN_SOURCE_RESULT_2026-11-17.md"
POPULATION_REL = ST.POPULATION_REL

#: 封 §1 の入力 5 つ(# , path, sha256)。違えば止まる。門が封の表と 1 行ずつ照らす
INPUTS = (
    (1, "fixtures/xbrl/tanshin_self/states_2026-11-14.json", "00414222cfe8cb05d0a1fed3d3e5a09bacafa6547f1675975a3cebd3e4ef70f6"),
    (2, "fixtures/xbrl/tanshin_self/vm_types_2026-11-14.json", "d1392722f345c408372ec644e15170463554683c3c7ff3951a51d9f66a1f5183"),
    (3, "measure/xbrl_tanshin_self_2026-11-14.py", "fa603d1c2dbfdee7c3ad4197ab9c4a9f1428419ada57293f346418bc0997aeb6"),
    (4, "measure/xbrl_tanshin_self_stage_2026-11-14.py", "4ed60b591366dd65a431dba5348aff6edb3889676d8e9a4154a5b0298486f7f9"),
    (5, "measure/xbrl_tanshin_2026-11-09.py", "b7ea491bf5cd34c4976bde86c4329583e0d9af09ec8895ea0caf48491492b5bd"),
)
STATES_IN_REL, TYPES_IN_REL = INPUTS[0][1], INPUTS[1][1]

# ---- 封 §2 の決めごと(字で留める。門が封と照らす)
PROFILE = "P33E"
REASON_P = "target_or_plan"
STATE_N = "GROUNDED"
TYPE_W = u"ウ"
SUMMARY_PREFIX = "XBRLData/Summary/"
SUMMARY_SUFFIX = "-ixbrl.htm"
SUMMARY_MEMBER = "XBRL/PublicDoc/summary_ixbrl.htm"
BODY_PREFIX = "XBRLData/Attachment/"                  # 短信の本体(Attachment の側)
BODY_SUFFIX = ".htm"
#: 封 §8 の 4: 空の欄(値の無い自己閉じの tag)を取り除く正規表現(bytes に掛ける。ほかは 1 byte も変えない)
NIL_TAG_RE = re.compile(br"<ix:nonFraction[^>]*/>")
#: engine の ``load_instance`` の inline XBRL の読み取りと同じ正規表現(封 §8 の 6 の数え。属性の列が ``/`` で終わる一致 = 自己閉じの tag から始まる読み取り)
ENGINE_FACT_RE = re.compile(r"<ix:nonFraction([^>]*)>(.*?)</ix:nonFraction>", re.S)
FORECAST_MEMBERS = ("ForecastMember", "UpperMember", "LowerMember")
JPY_PREFIX = "JPY"
PURE_UNIT = "Pure"
PCT_TOLERANCE_DEFAULT = 0.15
SAMPLE_SEED = 20261117
SAMPLE_N = 60
EXPECT_P = 794
EXPECT_W = 20
GROUPS = (u"甲", u"乙", u"丙")
SET_P, SET_W = u"P", u"W"
GRP_KOU, GRP_OTSU, GRP_W = u"甲組", u"乙組", u"W組"
SAMPLE_N_OTSU = 30
FAM_YEN, FAM_PCT, FAM_OTHER = u"円", u"%", u"他"
YEN_UNITS = (u"円", u"千円", u"万円", u"百万円", u"億円", u"兆円")
READING_LITERAL, READING_FAMILY = u"字のとおり", u"円の族"
READINGS = (READING_LITERAL, READING_FAMILY)
FAMILY_NOTE = u"封の後・試走の数を見た後に足した読み(封 §7。あと知恵)"
SUM_RAW, SUM_NONNIL = u"そのまま", u"空の欄を除く"
NONNIL_NOTE = u"封の後・監査の数え直しを見た後に足した読み(封 §8。あと知恵)"
#: 4 通りの読み = (サマリーの読み, 単位の読み)。最初が主
READS = ((SUM_RAW, READING_LITERAL), (SUM_RAW, READING_FAMILY), (SUM_NONNIL, READING_LITERAL), (SUM_NONNIL, READING_FAMILY))
READ_LABELS = collections.OrderedDict([
    ((SUM_RAW, READING_LITERAL), u"字のとおりの読み(主)"),
    ((SUM_RAW, READING_FAMILY), u"円の族の読み(%s)" % FAMILY_NOTE),
    ((SUM_NONNIL, READING_LITERAL), u"字のとおりの読み × 空の欄を除く読み(%s)" % NONNIL_NOTE),
    ((SUM_NONNIL, READING_FAMILY), u"円の族の読み × 空の欄を除く読み(%s・%s)" % (FAMILY_NOTE, NONNIL_NOTE))])
FAMS = (FAM_YEN, FAM_PCT, FAM_OTHER)
READ_LETTERS = collections.OrderedDict([
    (u"あ", u"合った fact のどれかが、文の言う項目・期の予想そのもの"),
    (u"い", u"値は合うが別の項目か別の期(偶然か取り違え)"),
    (u"う", u"分けられない")])
TYPED_BY = u"司令塔(AI の席)。人は読んでいない"
STATES_LIMITS = (
    u"値が合うことは同定ではない。予想の fact は 1 本に 10〜20 個ほどで、桁の少ない数(% の 1 桁など)は偶然に合う。対照(別の本の予想の fact)と読み(AI の席 1 席・盲検でない・人は読んでいない)はそのために置く",
    u"engine は動かしていない。サマリーを engine に渡したとき、予想の context を期として扱えるか・正しく結べるか・実績の行の結びを壊さないかは測っていない。「合う fact が在る」は「engine が確かめられる」ではない",
    u"P は engine の規則(未来の期の門など)が止めた行で、文が本当に計画・予想の数かは読んでいない。W は型の読み(AI の席)の 20 行だけ。当てる先はサマリーの予想だけで、中期経営計画の目標・設備投資の計画・説明資料の数はこの出所には無い",
    u"円の族の読みは封の後・試走の数を見た後に足した読み(封 §7。あと知恵)で、主の数は字のとおりの読み。2 つの読みで判定が割れる予測は「封の字の欠陥で割れた」と書き、当たりに数えない",
    u"主の数(字のとおりの読み × サマリーをそのまま読む)は、壊れた fact に当てた数で、同じ短信のサマリーの予想の fact に当たった率としては読めない(封 §8 の 3。自己閉じの tag から始まる読み取りが次の fact の終わりの tag までを 1 つの fact にする)",
    u"空の欄を除く読みは封の後・監査の数え直しを見た後に足した読み(封 §8。あと知恵)。判定が読みで割れる予測は「封の字の欠陥で割れた」と書き、当たりに数えない。短信の本体にも同じ読み取りが当たる数は数えただけで、過去の便の数は数え直していない",
    u"行は [本の #, 文の番号, 位置, 組, 単位の族, 当てない, F が空, 自, 実, 他, (円の族の)当てない・自・実・他, scale が無い, (空の欄を除く読みの)F が空・自・実・他・(円の族の)自・実・他] だけで、文・span・値・要素名・context の字は持たない")
ROW_COLUMNS = (u"本の #", u"文の番号", u"位置", u"組(P か W)", u"単位の族", u"当てない", u"F が空", u"自", u"実", u"他",
               u"円の族: 当てない", u"円の族: 自", u"円の族: 実", u"円の族: 他", u"scale が無い",
               u"空の欄を除く: F が空", u"空の欄を除く: 自", u"空の欄を除く: 実", u"空の欄を除く: 他",
               u"空の欄を除く・円の族: 自", u"空の欄を除く・円の族: 実", u"空の欄を除く・円の族: 他")
(R_BOOK, R_SI, R_POS, R_SET, R_FAM, R_NA, R_FEMPTY, R_SELF, R_REAL, R_OTHER, R_NA2, R_SELF2, R_REAL2, R_OTHER2, R_NOSCALE,
 R_FEMPTY_N, R_SELF_N, R_REAL_N, R_OTHER_N, R_SELF2_N, R_REAL2_N, R_OTHER2_N) = range(22)
N_COLUMNS = 22
#: 読みごとの札の欄(当てない, F が空, 自, 実, 他)。当てないは単位の読みだけで決まる
IDX = collections.OrderedDict([
    ((SUM_RAW, READING_LITERAL), (R_NA, R_FEMPTY, R_SELF, R_REAL, R_OTHER)),
    ((SUM_RAW, READING_FAMILY), (R_NA2, R_FEMPTY, R_SELF2, R_REAL2, R_OTHER2)),
    ((SUM_NONNIL, READING_LITERAL), (R_NA, R_FEMPTY_N, R_SELF_N, R_REAL_N, R_OTHER_N)),
    ((SUM_NONNIL, READING_FAMILY), (R_NA2, R_FEMPTY_N, R_SELF2_N, R_REAL2_N, R_OTHER2_N))])


def rd_key(rd):
    u"""読みの鍵。単位の読みの字(字のとおり / 円の族)だけなら、サマリーをそのまま読む読み。"""
    return rd if isinstance(rd, tuple) else (SUM_RAW, rd)


def rate(n, d):
    u"""{分子, 分母, 率}。率は小数 1 桁の %(四捨五入は整数の計算)。分母 0 は「分母 0」。"""
    t = u"分母 0" if d == 0 else u"%d.%d%%" % divmod((n * 2000 + d) // (2 * d), 10)
    return collections.OrderedDict([(u"分子", n), (u"分母", d), (u"率", t)])


def ratio_text(a, b):
    u"""a ÷ b を小数 1 桁の字で。b が 0 なら「他は 0」(比を書かない)。"""
    if b == 0:
        return u"他は 0"
    return u"%d.%d" % divmod((a * 20 + b) // (2 * b), 10)


# ======================================================================================================
# 照合(封 §2-4)。1 つの claim と 1 つの fact
def claim_kind(claim, reading=READING_LITERAL):
    u"""claim の当て方: ``円`` / ``%`` / None(当てない)。値が 0・円で unit_scale か claim_scale が None・どちらの単位でもない → None。
    ``reading`` が 字のとおり なら金額の単位の字は 円 だけ・円の族 なら YEN_UNITS のどれか(封 §7)。"""
    if not claim.get("value"):
        return None
    yen = (u"円",) if reading == READING_LITERAL else YEN_UNITS
    if claim.get("unit") in yen:
        if claim.get("unit_scale") is None or claim.get("claim_scale") is None:
            return None
        return FAM_YEN
    if claim.get("unit") == u"%":
        return FAM_PCT
    return None


def unit_family(claim):
    u = claim.get("unit")
    return FAM_YEN if u in YEN_UNITS else (FAM_PCT if u == u"%" else FAM_OTHER)


def no_scale(claim):
    u"""円の族の単位の字で unit_scale か claim_scale が None(この便では当てられなかった行。scale は作らない)。"""
    return claim.get("unit") in YEN_UNITS and (claim.get("unit_scale") is None or claim.get("claim_scale") is None)


def match_fact(claim, fact_unit, fact_value, reading=READING_LITERAL):
    u"""claim 1 つと fact 1 つ(単位・値)が合うか。engine の ``vocabulary.match_value`` を呼ぶ(円)。% は raw の ``pct_tolerance`` の帯。"""
    kind = claim_kind(claim, reading)
    if kind == FAM_YEN:
        if not str(fact_unit).upper().startswith(JPY_PREFIX):
            return False
        return V.match_value(fact_value, claim["value"] * claim["unit_scale"], claim["claim_scale"], None, False) is not None
    if kind == FAM_PCT:
        if fact_unit != PURE_UNIT:
            return False
        tol = claim.get("pct_tolerance")
        tol = PCT_TOLERANCE_DEFAULT if tol is None else tol
        x = fact_value * 100
        return abs(x - claim["value"]) <= tol or abs(abs(x) - abs(claim["value"])) <= tol
    return False


def matches_any(claim, facts, reading=READING_LITERAL):
    return any(match_fact(claim, u, v, reading) for (u, v) in facts)


def claim_flags(claim, f_self, r_self, f_other, reading=READING_LITERAL):
    u"""(当てない, 自, 実, 他)。当てないなら自・実・他は全部偽。"""
    if claim_kind(claim, reading) is None:
        return True, False, False, False
    return False, matches_any(claim, f_self, reading), matches_any(claim, r_self, reading), matches_any(claim, f_other, reading)


# ======================================================================================================
# サマリーの fact(封 §2-3)
def strip_nil_tags(data):
    u"""封 §8 の 4: bytes から ``<ix:nonFraction[^>]*/>`` に当たる所(値の無い自己閉じの tag)を取り除く。ほかは 1 byte も変えない。"""
    return NIL_TAG_RE.sub(b"", data)


def summary_member_bytes(zb):
    u"""元の ZIP のサマリーの member の bytes(ちょうど 1 つ。違えば止める)。"""
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        cand = [n for n in z.namelist() if n.startswith(SUMMARY_PREFIX) and n.endswith(SUMMARY_SUFFIX)]
        if len(cand) != 1:
            raise Stop(u"**サマリーの member がちょうど 1 つでない(%d)。止める**" % len(cand))
        return z.read(cand[0])


def summary_zip(zb, strip=False):
    u"""元の ZIP から、サマリーの member を ``XBRL/PublicDoc/summary_ixbrl.htm`` として 1 つだけ入れた ZIP の bytes。ちょうど 1 つでなければ止める。
    ``strip`` が偽なら中身は 1 byte も変えない(封 §2-3)。真なら空の欄を除く(封 §8 の 4)。"""
    data = summary_member_bytes(zb)
    if strip:
        data = strip_nil_tags(data)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        out.writestr(TSS._info(SUMMARY_MEMBER), data)
    return buf.getvalue()


def is_forecast_context(ctx):
    return any(str(m).strip().split(":")[-1] in FORECAST_MEMBERS for m in ((ctx or {}).get("members") or []))


def split_facts(inst):
    u"""instance(``load_instance`` の結果)→ (F, R)。各 fact は辞書(name・context・unit・value)。値が 0・単位が無い fact は除く。"""
    f_list, r_list = [], []
    for f in inst["facts"]:
        if not f.get("unit") or not f.get("value"):
            continue
        (f_list if is_forecast_context(inst["contexts"].get(f.get("context"))) else r_list).append(f)
    return f_list, r_list


def summary_facts(zb, strip=False):
    return split_facts(I.load_instance(summary_zip(zb, strip)))


def self_closed_reads(raw_text):
    u"""engine の読み取りの正規表現の一致のうち、属性の列が ``/`` で終わる数(自己閉じの tag から始まる読み取り。封 §8 の 6)。"""
    return sum(1 for m in ENGINE_FACT_RE.finditer(raw_text) if m.group(1).endswith("/"))


def body_members(zb):
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        return [(n, z.read(n)) for n in sorted(z.namelist()) if n.startswith(BODY_PREFIX) and n.endswith(BODY_SUFFIX)]


def self_closed_counts(zb):
    u"""(サマリーの数, 本体の数)。engine と同じ読み方(utf-8・ignore)で数える。数えるだけ。"""
    s = self_closed_reads(summary_member_bytes(zb).decode("utf-8", "ignore"))
    b = sum(self_closed_reads(data.decode("utf-8", "ignore")) for _n, data in body_members(zb))
    return s, b


def pairs(facts):
    return [(f["unit"], f["value"]) for f in facts]


# ======================================================================================================
# 別の本(封 §2-6)
def group_rank(g):
    return GROUPS.index(g) if g in GROUPS else len(GROUPS)


def other_books(infos):
    u"""``infos`` = [(群, 本の #, 切れた, F が空でない)] → {本の #: 別の本の #}。
    本を (群, #) の順に並べ、切れた本で F が空でないものだけを群ごとに輪にする。輪の本は次の本(最後は最初)。輪に居ない本は同じ群で # が大きい最初の輪の本(無ければ輪の最初)。輪が 1 本以下なら止める。"""
    infos = sorted(infos, key=lambda t: (group_rank(t[0]), t[0], t[1]))
    ring = collections.OrderedDict()
    for g, n, cut_ok, nonempty in infos:
        ring.setdefault(g, [])
        if cut_ok and nonempty:
            ring[g].append(n)
    for g, r in ring.items():
        if len(r) <= 1:
            raise Stop(u"**輪の本が群 %s に 1 本以下。止める**" % g)
    out = {}
    for g, n, _c, _e in infos:
        r = ring[g]
        if n in r:
            out[n] = r[(r.index(n) + 1) % len(r)]
        else:
            later = [m for m in r if m > n]
            out[n] = later[0] if later else r[0]
    return out


# ======================================================================================================
# 本の作り直し(封 §2-1)
def claims_of(wrapped):
    u"""包んだ ZIP → [(raw の claim, verify の claim)](数の claim だけ。並びが対応しなければ止める)。鍵の重なりも止める。"""
    out = VD.verify_document(wrapped, PROFILE)
    nums, texts = TS.R.build_raw_claims(wrapped, V.PROFILES[PROFILE])
    raws = nums + texts
    cl = out["claims"]
    if len(cl) != len(raws) or any(c["id"] != r["id"] for c, r in zip(cl, raws)):
        raise Stop(u"**claim と raw の並びが対応しない。止める**")
    res, seen = [], set()
    for c, r in zip(cl, raws):
        if c["kind"] != "num":
            continue
        key = (r["sentence"], r["pos"])
        if key in seen:
            raise Stop(u"**数の claim の鍵(文の番号, 位置)が重なった。止める**")
        seen.add(key)
        res.append((r, c))
    return res


def claim_entry(r, c):
    return collections.OrderedDict([
        (u"si", r["sentence"]), (u"pos", r["pos"]), (u"state", c["state"]), (u"reason", TS.RUN.safe_reason(c["reason"])),
        (u"unit", r.get("unit")), (u"value", r.get("value")), (u"unit_scale", r.get("unit_scale")), (u"claim_scale", r.get("claim_scale")),
        (u"pct_tolerance", r.get("pct_tolerance"))])


def states_job(args):
    u"""1 本: 作り直し → TSS の記録の行と照らす → 数の claim とサマリーの F・R(単位と値だけ)を返す。"""
    n, grp, kind, sha, path, exp_cut, exp_rows = args
    if not os.path.exists(path):
        raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める**" % n)
    with io.open(path, "rb") as fh:
        zb = fh.read()
    if ST.sha256_bytes(zb) != sha:
        raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % n)
    text, _head, _why = TSS.cut(zb)
    sc_sum, sc_body = self_closed_counts(zb)
    book = collections.OrderedDict([(u"#", n), (u"群", grp), (u"切れた", text is not None), (u"claims", []), (u"F", []), (u"R", []), (u"F2", []), (u"R2", []),
                                    (u"自己閉じ", [sc_sum, sc_body])])
    if (text is not None) != exp_cut:
        raise Stop(u"**切り出しの可否が TSS の記録と違う(# %d)。止める**" % n)
    if text is None:
        if exp_rows:
            raise Stop(u"**切れない本に記録の行が在る(# %d)。止める**" % n)
        return book
    wrapped, _nf = TSS.wrap(zb, text)
    entries = [claim_entry(r, c) for r, c in claims_of(wrapped)]
    if [(e[u"si"], e[u"pos"], e[u"state"], e[u"reason"]) for e in entries] != [(r[0], r[1], r[2], r[3]) for r in exp_rows]:
        raise Stop(u"**作り直した行が TSS の記録の行と違う(# %d)。止める**" % n)
    f_list, r_list = summary_facts(zb)
    f2_list, r2_list = summary_facts(zb, True)
    book[u"claims"] = entries
    book[u"F"] = pairs(f_list)
    book[u"R"] = pairs(r_list)
    book[u"F2"] = pairs(f2_list)
    book[u"R2"] = pairs(r2_list)
    return book


# ======================================================================================================
# 数える(封 §2-2・§2-5・§3)
def analyze(books, w_keys, expect_p=None, expect_w=None):
    u"""作り直した本(``states_job`` の返り値の並び)→ (行[P と W], N の数 {(読み, 群): Counter})。
    読みは 4 通り(``READS``)。本の F・R(そのまま)と F2・R2(空の欄を除く)。別の本の輪はサマリーの読みごとに、その読みの F が空でない本で作る。"""
    other = {}
    for sr, fk in ((SUM_RAW, u"F"), (SUM_NONNIL, u"F2")):
        other[sr] = other_books([(b[u"群"], b[u"#"], b[u"切れた"], bool(b[fk])) for b in books])
    by_n = dict((b[u"#"], b) for b in books)
    rows = []
    n_counts = collections.OrderedDict(((rd, g), collections.Counter()) for rd in READS for g in GROUPS)
    w_left = set(w_keys)
    fk_of = {SUM_RAW: (u"F", u"R"), SUM_NONNIL: (u"F2", u"R2")}
    for b in books:
        if not b[u"切れた"]:
            continue
        for e in b[u"claims"]:
            key = (b[u"#"], e[u"si"], e[u"pos"])
            in_p = e[u"reason"] == REASON_P
            in_w = key in w_keys
            in_n = e[u"state"] == STATE_N
            if not (in_p or in_w or in_n):
                continue
            fl = {}
            for rd in READS:
                fk, rk = fk_of[rd[0]]
                f_other = by_n[other[rd[0]][b[u"#"]]][fk]
                fl[rd] = claim_flags(e, b[fk], b[rk], f_other, rd[1])
            if in_n:
                for rd in READS:
                    c = n_counts.setdefault((rd, b[u"群"]), collections.Counter())
                    c[u"行"] += 1
                    for nm, v in zip((u"当てない", u"自", u"実", u"他"), fl[rd]):
                        c[nm] += int(v)
                    c[u"scale が無い"] += int(no_scale(e))
            na, s, re_, ot = fl[READS[0]]
            na2, s2, re2, ot2 = fl[READS[1]]
            _na_n, s_n, re_n, ot_n = fl[READS[2]]
            _na2_n, s2_n, re2_n, ot2_n = fl[READS[3]]
            for flag, name in ((in_p, SET_P), (in_w, SET_W)):
                if flag:
                    rows.append([b[u"#"], e[u"si"], e[u"pos"], name, unit_family(e), na, not b[u"F"], s, re_, ot, na2, s2, re2, ot2, no_scale(e),
                                 not b[u"F2"], s_n, re_n, ot_n, s2_n, re2_n, ot2_n])
            if in_w:
                w_left.discard(key)
    if w_left:
        raise Stop(u"**W の行が作り直した claim に当たらない(%d 行)。止める**" % len(w_left))
    n_p = sum(1 for r in rows if r[R_SET] == SET_P)
    n_w = sum(1 for r in rows if r[R_SET] == SET_W)
    if expect_p is not None and n_p != expect_p:
        raise Stop(u"**P の行が %d(%d でない)。止める**" % (n_p, expect_p))
    if expect_w is not None and n_w != expect_w:
        raise Stop(u"**W の行が %d(%d でない)。止める**" % (n_w, expect_w))
    rows.sort(key=lambda r: (r[R_SET] != SET_P, r[R_BOOK], r[R_SI], r[R_POS]))
    return rows, n_counts


def rows_of(rows, which, grp_of=None, group=None):
    return [r for r in rows if r[R_SET] == which and (group is None or grp_of[r[R_BOOK]] == group)]


def p_part(rows, rd=READING_LITERAL):
    iNA, iFE, iS, iR, iO = IDX[rd_key(rd)]
    n = len(rows)
    na = sum(1 for r in rows if r[iNA])
    fe = sum(1 for r in rows if r[iFE])
    s = sum(1 for r in rows if r[iS])
    re_ = sum(1 for r in rows if r[iR])
    ot = sum(1 for r in rows if r[iO])
    applied = sum(1 for r in rows if not r[iNA] and not r[iFE])
    return collections.OrderedDict([
        (u"行", n), (u"当てない", na), (u"うち scale が無い行", sum(1 for r in rows if r[R_NOSCALE])), (u"F が空の本の行", fe), (u"当てた行で F が空でない本のもの", applied),
        (u"自", s), (u"実", re_), (u"他", ot),
        (u"主の率(自 / 行の全部)", rate(s, n)), (u"並べる率(自 / 当てた行で F が空でない本のもの)", rate(s, applied)),
        (u"実の率(実 / 行の全部)", rate(re_, n)), (u"他の率(他 / 行の全部)", rate(ot, n)),
        (u"自 ÷ 他", collections.OrderedDict([(u"自", s), (u"他", ot), (u"比", ratio_text(s, ot))]))])


def p_books(rows, rd=READING_LITERAL):
    iS = IDX[rd_key(rd)][2]
    per = collections.Counter(r[R_BOOK] for r in rows)
    per_self = collections.Counter(r[R_BOOK] for r in rows if r[iS])
    return collections.OrderedDict([
        (u"P の行を持つ本", len(per)), (u"自の行を持つ本", len(per_self)), (u"自の行を持つ本の率", rate(len(per_self), len(per))),
        (u"いちばん多い 1 本が持つ自の行の数", max(per_self.values()) if per_self else 0)])


def small_part(rows, rd=READING_LITERAL):
    iNA, _iFE, iS, iR, iO = IDX[rd_key(rd)]
    return collections.OrderedDict([
        (u"行", len(rows)), (u"当てない", sum(1 for r in rows if r[iNA])), (u"うち scale が無い行", sum(1 for r in rows if r[R_NOSCALE])),
        (u"自", sum(1 for r in rows if r[iS])), (u"実", sum(1 for r in rows if r[iR])), (u"他", sum(1 for r in rows if r[iO]))])


def n_part(c):
    n = c.get(u"行", 0)
    return collections.OrderedDict([
        (u"行", n), (u"当てない", c.get(u"当てない", 0)), (u"うち scale が無い行", c.get(u"scale が無い", 0)),
        (u"自", c.get(u"自", 0)), (u"実", c.get(u"実", 0)), (u"他", c.get(u"他", 0)),
        (u"自の率(自 / 行の全部)", rate(c.get(u"自", 0), n)), (u"他の率(他 / 行の全部)", rate(c.get(u"他", 0), n))])


def block(rows, n_c, grp_of, group=None, rd=READING_LITERAL):
    u"""全体(group が None)か 1 つの群の集計(読み rd)。行 [P と W] と N の数から数える。"""
    p_rows = rows_of(rows, SET_P, grp_of, group)
    w_rows = rows_of(rows, SET_W, grp_of, group)
    p = p_part(p_rows, rd)
    p[u"単位別"] = collections.OrderedDict((f, p_part([r for r in p_rows if r[R_FAM] == f], rd)) for f in FAMS)
    p[u"本"] = p_books(p_rows, rd)
    if group is None:
        nc = collections.Counter()
        for (rd2, _g), c in n_c.items():
            if rd2 == rd_key(rd):
                nc.update(c)
    else:
        nc = n_c.get((rd_key(rd), group), collections.Counter())
    return collections.OrderedDict([(u"P", p), (u"W", small_part(w_rows, rd)), (u"N", n_part(nc))])


def tally(rows, n_c, grp_of):
    out = collections.OrderedDict()
    for rd, label in READ_LABELS.items():
        out[label] = collections.OrderedDict([
            (u"全体", block(rows, n_c, grp_of, None, rd)),
            (u"群", collections.OrderedDict((g, block(rows, n_c, grp_of, g, rd)) for g in GROUPS))])
    return out


def fact_stats_of(cut_books, fk, rk):
    fu, ru = collections.Counter(), collections.Counter()
    for b in cut_books:
        fu.update(u for u, _v in b[fk])
        ru.update(u for u, _v in b[rk])
    return collections.OrderedDict([
        (u"F の fact の数の合計", sum(fu.values())), (u"F の単位別の数", collections.OrderedDict(sorted(fu.items()))),
        (u"R の fact の数の合計", sum(ru.values())), (u"R の単位別の数", collections.OrderedDict(sorted(ru.items()))),
        (u"F が空の本の数(切れた本のうち)", sum(1 for b in cut_books if not b[fk])),
        (u"F が空の本の数の群別", collections.OrderedDict((g, sum(1 for b in cut_books if b[u"群"] == g and not b[fk])) for g in GROUPS))])


def self_closed_stats(books):
    u"""自己閉じの tag から始まる読み取りの数と本の数(サマリー・本体。400 本の全部)。数えるだけ。"""
    out = collections.OrderedDict()
    for i, label in ((0, u"サマリー"), (1, u"短信の本体(Attachment の側の .htm)")):
        out[label] = collections.OrderedDict([
            (u"読み取りの数", sum(b[u"自己閉じ"][i] for b in books)), (u"その読み取りを持つ本", sum(1 for b in books if b[u"自己閉じ"][i] > 0)), (u"本", len(books))])
    return out


def fact_stats(books):
    u"""サマリーの fact の数の合計と単位別・F が空の本の数(切れた本のうち)。前の欄は主(そのまま)のもので不変。
    空の欄を除く読みの同じ数と、自己閉じの tag から始まる読み取りの数を足す。"""
    cut_books = [b for b in books if b[u"切れた"]]
    out = collections.OrderedDict([(u"切れた本", len(cut_books))])
    out.update(fact_stats_of(cut_books, u"F", u"R"))
    out[u"空の欄を除く読み(%s)" % NONNIL_NOTE] = fact_stats_of(cut_books, u"F2", u"R2")
    out[u"自己閉じの tag から始まる読み取り(engine と同じ正規表現の一致のうち属性の列が / で終わるもの)"] = self_closed_stats(books)
    return out


# ======================================================================================================
# 入力・記録
def load_json(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh, object_pairs_hook=collections.OrderedDict)


def check_inputs(root):
    u"""封 §1 の入力 5 つの sha256 が表と同じか。違えば止める。"""
    for no, rel, want in INPUTS:
        p = os.path.join(root, rel)
        if not os.path.isfile(p) or ST.sha256_file(p) != want:
            raise Stop(u"**入力 %d の sha256 が封の表と違う。止める**" % no)
    return [collections.OrderedDict([(u"#", no), (u"path", rel), (u"sha256", want)]) for no, rel, want in INPUTS]


def check_population(root, pop):
    u"""母集団の記録の行(#・群・様式の種類・sha256)が TSS の封の表と同じか。"""
    rec = load_json(os.path.join(root, POPULATION_REL))
    if [tuple(r[:4]) for r in rec[u"行"]] != [tuple(r) for r in pop]:
        raise Stop(u"**母集団の記録の行が TSS の封の表と違う。止める**")
    return ST.sha256_file(os.path.join(root, POPULATION_REL))


def w_keys_of(types_rec):
    return set((r[1], r[2], r[3]) for r in types_rec[u"行"] if r[4] == TYPE_W)


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


def build_record(root=ROOT, procs=1, material=None, out=None, say=print, clock=time.time, population=None, shape=None, clean=None):
    u"""400 本を作り直して記録(OrderedDict)を返す。書かない。"""
    mat, prod = material_dir(material, out, root)
    inputs = check_inputs(root)
    n_rows, groups = shape or (ST.N_ROWS, ST.GROUP_COUNTS)
    pop = ST.validate_population(population if population is not None else ST.read_population(root), n_rows, groups)
    pop_sha = check_population(root, pop)
    states_in = load_json(os.path.join(root, STATES_IN_REL))
    types_in = load_json(os.path.join(root, TYPES_IN_REL))
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
    jobs = [(n, g, k, sha, os.path.join(mat, sha + u".zip"), by_book[n][u"切り出し"] == TSS.CUT_OK, by_book[n][u"行"]) for (n, g, k, sha) in pop]
    say(u"states %d 本 × %s ― procs %d" % (len(jobs), PROFILE, procs))
    t0 = clock()
    books = TS.NF.map_pool(states_job, jobs, procs)
    elapsed = clock() - t0
    if before != ST.names_snapshot(mat):
        raise Stop(u"**材料の置き場の件数か名前が変わった。止める**")
    w_keys = w_keys_of(types_in)
    full = shape is None
    rows, n_c = analyze(books, w_keys, EXPECT_P if full else None, EXPECT_W if full else None)
    grp_of = dict((b[u"#"], b[u"群"]) for b in books)
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"封の追記(§7)の commit"] = ADDENDUM_COMMIT
    rec[u"封の追記(§8)の commit"] = ADDENDUM8_COMMIT
    rec[u"step"] = u"PS(止めた行にサマリーの予想の fact という当てる先が在るか)― 400 本の作り直し・P・W・N の照合(0 USD・通信なし・engine は 0 行)"
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"入力"] = inputs
    rec[u"母集団の記録の sha256"] = pop_sha
    rec[u"engine の指紋"] = fp
    rec[u"profile"] = PROFILE
    rec[u"材料"] = collections.OrderedDict([(u"置き場", ST.display_path(mat) if prod else u"使い捨ての置き場(本番の folder ではない)"), (u"表と一致した ZIP", len(pop))])
    rec[u"作り直しの確認"] = collections.OrderedDict([
        (u"本", len(books)), (u"切り出しの可否と数の claim の (文の番号, 位置, state, reason) が TSS の記録と同じ本", len(books)),
        (u"数の claim の合計", sum(len(b[u"claims"]) for b in books))])
    rec[u"照合の規則"] = collections.OrderedDict([
        (u"F の member の名", list(FORECAST_MEMBERS)), (u"円の fact の単位", u"大文字にして JPY で始まる"), (u"% の fact の単位", PURE_UNIT),
        (u"円の照合", u"vocabulary.match_value(fact の値, claim の値 × unit_scale, claim_scale, None, False)"),
        (u"% の照合", u"abs(fact の値 × 100 − claim の値) <= tol か abs(abs(fact の値 × 100) − abs(claim の値)) <= tol(tol は claim の pct_tolerance・無ければ 0.15)"),
        (u"当てない", u"単位が 円・% のどちらでもない・値が 0・円で claim_scale か unit_scale が None"),
        (u"主の読み", u"字のとおり(金額の単位の字が 円 だけ)"),
        (u"円の族の読み", FAMILY_NOTE + u": 金額の単位の字が " + u"・".join(YEN_UNITS) + u" のどれかで unit_scale と claim_scale が None でない。照合は字のとおりと同じ"),
        (u"scale が無い claim", u"どちらの読みでも当てない。単位の表から scale は作らない(この便では当てられなかった行として数に出す)"),
        (u"サマリーの主の読み", u"サマリーの member を 1 byte も変えずに load_instance に渡す(封 §2-3)。壊れた fact(自己閉じの tag から次の fact の終わりまで)を含む"),
        (u"空の欄を除く読み", NONNIL_NOTE + u": サマリーの member の bytes から正規表現 <ix:nonFraction[^>]*/> に当たる所を取り除き、ほかは 1 byte も変えずに包む。F・R の分け・値 0 と単位なしの除外・照合・札・対照の輪は同じ(輪は読みごとにその読みの F が空でない本)"),
        (u"読みの組", u"単位の読み(字のとおり・円の族)× サマリーの読み(そのまま・空の欄を除く)の 4 通り。主は 字のとおり × そのまま")])
    rec[u"別の本の決め方"] = u"本を (群, #) の順に並べ、切れた本で F が空でないものだけを群ごとに輪にする。輪の次の本(最後は最初)。輪に居ない本は同じ群で # が大きい最初の輪の本(無ければ輪の最初)"
    rec[u"サマリーの fact"] = fact_stats(books)
    rec[u"P の行の数"] = sum(1 for r in rows if r[R_SET] == SET_P)
    rec[u"W の行の数"] = sum(1 for r in rows if r[R_SET] == SET_W)
    rec[u"集計"] = tally(rows, n_c, grp_of)
    rec[u"限界"] = list(STATES_LIMITS)
    rec[u"行の欄"] = list(ROW_COLUMNS)
    rec[u"時間(秒)"] = round(elapsed, 1)
    rec[u"key_leaks"] = []
    rec[u"行"] = rows
    return rec


def record_text(rec, key_value=None):
    text = ST.dumps_record(rec)
    check_text(rec, text, key_value)
    return text


def check_text(rec, text, key_value=None):
    scan = text.replace(SEAL_REL, u"")
    for _no, rel, _sha in INPUTS:
        scan = scan.replace(rel, u"")                    # 封の path と入力の path は 32 字以上の _ - 英数字の連なり(TSS と同じく除いて検査する)
    TSS.check_clean(rec, scan, key_value)


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
    say(u"-> %s(P %d 行・W %d 行)" % (os.path.basename(out), rec[u"P の行の数"], rec[u"W の行の数"]))
    return rec


# ======================================================================================================
# 標本(封 §2-7)
def pick_sample(n_rows, seed=SAMPLE_SEED, k=SAMPLE_N):
    if n_rows <= k:
        return list(range(n_rows))
    return sorted(random.Random(seed).sample(range(n_rows), k))


def sample_items(states):
    u"""[(標本の番号(1 から), 本の #, 文の番号, 位置, 組)]。組は 甲組・乙組・W組(封 §7 の 4・§8 の 5)。**「空の欄を除く読み」の札から引く**(封 §8 の 5)。
    甲組 = 単位が字のとおりで「自」が真の P の行から 60 行(# の順・文の番号の順・位置の順に並べて引く)。
    乙組 = 円の族の読みでだけ「自」が真になる P の行から同じ種で 30 行(満たなければ全部)。
    W組 = 円の族の読みで「自」が真の W の行を全部。番号は 甲組 → 乙組 → W組 の順(それぞれ同じ並び)。"""
    key = lambda r: (r[R_BOOK], r[R_SI], r[R_POS])           # noqa: E731
    rows = states[u"行"]
    kou = sorted((r for r in rows if r[R_SET] == SET_P and r[R_SELF_N]), key=key)
    otsu = sorted((r for r in rows if r[R_SET] == SET_P and r[R_SELF2_N] and not r[R_SELF_N]), key=key)
    w_rows = sorted((r for r in rows if r[R_SET] == SET_W and r[R_SELF2_N]), key=key)
    chosen = ([(r, GRP_KOU) for r in (kou[j] for j in pick_sample(len(kou)))]
              + [(r, GRP_OTSU) for r in (otsu[j] for j in pick_sample(len(otsu), SAMPLE_SEED, SAMPLE_N_OTSU))]
              + [(r, GRP_W) for r in w_rows])
    return [(i + 1, r[R_BOOK], r[R_SI], r[R_POS], g) for i, (r, g) in enumerate(chosen)]


def n_in(items, g):
    return sum(1 for it in items if it[4] == g)


def sheet_text(item, entry, sentence, span, matched):
    n, num, si, pos, which = item
    lines = [u"=== 標本 %d / 組 %s / 本 # %d / 文 %d / 位置 %d ===" % (n, which, num, si, pos),
             u"文: %s" % sentence, u"span: %s" % span,
             u"読んだ値: %s %s(claim_scale %s・unit_scale %s)" % (entry[u"value"], entry[u"unit"], entry[u"claim_scale"], entry[u"unit_scale"])]
    for f, ctx in matched:
        lines.append(u"合った F の fact: 要素 %s / context %s / 値 %s / 単位 %s / 期 %s〜%s・instant %s / members %s" % (
            f["name"], f["context"], f["value"], f["unit"], ctx.get("start"), ctx.get("end"), ctx.get("instant"), u",".join(ctx.get("members") or [])))
    return u"\n".join(lines + [u"", u""])


def run_sheet(states_path, material, sheet, root=ROOT, say=print, repo=None, population=None):
    if TSS.inside_repo(sheet, repo):
        raise Stop(u"**--sheet が repo の中(または git の木の中)。文を持つ紙は repo の外に書く。止める**")
    sheet = os.path.abspath(sheet)
    if os.path.exists(sheet):
        raise Stop(u"**--sheet が既に在る。止める**")
    states = load_json(states_path)
    items = sample_items(states)
    pop = dict((r[0], r) for r in (population if population is not None else ST.validate_population(ST.read_population(root))))
    mat = os.path.abspath(material)
    by_book = collections.OrderedDict()
    for it in items:
        by_book.setdefault(it[1], []).append(it)
    chunks = {}
    for num, its in by_book.items():
        _n, _g, _k, sha = pop[num]
        with io.open(os.path.join(mat, sha + u".zip"), "rb") as fh:
            zb = fh.read()
        if ST.sha256_bytes(zb) != sha:
            raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % num)
        text, _h, _why = TSS.cut(zb)
        if text is None:
            raise Stop(u"**標本の本が切れない(# %d)。記録と合わない。止める**" % num)
        wrapped, _nf = TSS.wrap(zb, text)
        keyed = dict(((r["sentence"], r["pos"]), (r, c)) for r, c in claims_of(wrapped))
        sents = TS.RUN.sentence_list(wrapped, V.PROFILES[PROFILE])
        inst = I.load_instance(summary_zip(zb, True))                 # 紙の fact は空の欄を除く読み(封 §8 の 5)
        f_list, _r = split_facts(inst)
        for it in its:
            rc = keyed.get((it[2], it[3]))
            if rc is None:
                raise Stop(u"**標本の行が記録と合わない(標本 %d)。止める**" % it[0])
            r, c = rc
            entry = claim_entry(r, c)
            rd = READING_LITERAL if it[4] == GRP_KOU else READING_FAMILY      # 単位の読み(サマリーは空の欄を除く)
            matched = [(f, inst["contexts"].get(f["context"]) or {}) for f in f_list if match_fact(entry, f["unit"], f["value"], rd)]
            if not matched:
                raise Stop(u"**標本の行に合う F の fact が無い(標本 %d)。記録と合わない。止める**" % it[0])
            chunks[it[0]] = sheet_text(it, entry, sents[it[2]], r.get("span"), matched)
    d = os.path.dirname(sheet)
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(sheet, "w", encoding="utf-8", newline="") as fh:
        fh.write(u"".join(chunks[it[0]] + u"\n" for it in items))
    say(u"標本 %d 行(甲組 %d・乙組 %d・W組 %d)・本 %d" % (len(items), n_in(items, GRP_KOU), n_in(items, GRP_OTSU), n_in(items, GRP_W), len(by_book)))
    return items


# ======================================================================================================
# types
def read_typed(path, items):
    u"""TSV(標本の番号 TAB 本の # TAB 文の番号 TAB 位置 TAB 字)。標本の行と 1 対 1・字は あ/い/う だけ。{標本の番号: 字}。"""
    want = dict((it[0], it[1:4]) for it in items)
    out = {}
    with io.open(path, encoding="utf-8") as fh:
        for ln in fh.read().split(u"\n"):
            if not ln.strip():
                continue
            parts = ln.rstrip(u"\r").split(u"\t")
            if len(parts) != 5 or not all(re.fullmatch(r"[0-9]+", p) for p in parts[:4]) or parts[4] not in READ_LETTERS:
                raise Stop(u"**字の file の行が「標本の番号 TAB 本の # TAB 文の番号 TAB 位置 TAB 字(あ・い・う)」でない。止める**")
            k = int(parts[0])
            if k in out:
                raise Stop(u"**字の file に同じ標本の番号が 2 行ある。止める**")
            if k not in want or tuple(int(p) for p in parts[1:4]) != tuple(want[k]):
                raise Stop(u"**字の file の行が標本の行(本の #・文の番号・位置)と合わない。止める**")
            out[k] = parts[4]
    if sorted(out) != sorted(want):
        raise Stop(u"**字の file の標本の番号が標本の行(%d 行)とそろわない。止める**" % len(want))
    return out


def read_counts(items, typed):
    def part(sel):
        c = collections.Counter(typed[it[0]] for it in items if sel(it))
        n = sum(c.values())
        return collections.OrderedDict([(u"読んだ行", n)] + [(t, c.get(t, 0)) for t in READ_LETTERS] + [(u"あの率", rate(c.get(u"あ", 0), n))])
    out = collections.OrderedDict([(u"全部", part(lambda it: True))])
    for g in (GRP_KOU, GRP_OTSU, GRP_W):
        out[g] = part(lambda it, g=g: it[4] == g)
    return out


def run_types(states_path, typed_path, out, root=ROOT, say=print, key_value=None):
    out = os.path.abspath(out)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。止める**" % os.path.basename(out))
    states = load_json(states_path)
    items = sample_items(states)
    typed = read_typed(typed_path, items)
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"封の追記(§7)の commit"] = ADDENDUM_COMMIT
    rec[u"封の追記(§8)の commit"] = ADDENDUM8_COMMIT
    rec[u"step"] = u"PS ― 「自」が真の P の標本(甲組・乙組)と W の行(W組)の読み(0 USD)"
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"states の記録の sha256"] = ST.sha256_file(os.path.abspath(states_path))
    rec[u"型を付けた席"] = TYPED_BY
    rec[u"盲検"] = u"盲検ではない(封の予測と §0 の形を知ったうえで付けた)"
    rec[u"標本の規則"] = collections.OrderedDict([
        (u"読みの札", u"全部「空の欄を除く読み」の札から引く。" + NONNIL_NOTE + u"。封 §8 の 5(PS-6 は封のとおりには測らない・当たりに数えない)"),
        (u"甲組", u"空の欄を除く読みで、単位が字のとおりで「自」が真の P の行を (# の順・文の番号の順・位置の順)に並べ、random.Random(種).sample(range(行の数), 60) を番号の順に(60 に満たなければ全部)"),
        (u"乙組", u"空の欄を除く読みで、円の族の読みでだけ「自」が真になる P の行を同じ順に並べ、同じ種で 30 行(満たなければ全部)。" + FAMILY_NOTE),
        (u"W組", u"空の欄を除く読みで、円の族の読みで「自」が真の W の行を全部。" + FAMILY_NOTE),
        (u"種", SAMPLE_SEED),
        (u"甲組の行の数", sum(1 for r in states[u"行"] if r[R_SET] == SET_P and r[R_SELF_N])),
        (u"乙組の行の数", sum(1 for r in states[u"行"] if r[R_SET] == SET_P and r[R_SELF2_N] and not r[R_SELF_N])),
        (u"W組の行の数", sum(1 for r in states[u"行"] if r[R_SET] == SET_W and r[R_SELF2_N])),
        (u"甲組の標本の数", n_in(items, GRP_KOU)), (u"乙組の標本の数", n_in(items, GRP_OTSU)), (u"W組の標本の数", n_in(items, GRP_W)),
        (u"番号の割り当て", u"1 から 甲組・続けて 乙組・続けて W組")])
    rec[u"字の説明"] = collections.OrderedDict(READ_LETTERS)
    rec[u"集計"] = read_counts(items, typed)
    rec[u"行の欄"] = [u"標本の番号", u"本の #", u"文の番号", u"位置", u"字"]
    rec[u"行"] = [[it[0], it[1], it[2], it[3], typed[it[0]]] for it in items]
    rec[u"key_leaks"] = []
    text = ST.dumps_record(rec)
    check_text(rec, text, key_value)
    ST.write_text_exclusive(out, text)
    say(u"-> %s(標本 %d 行)" % (os.path.basename(out), len(items)))
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
    b = sub.add_parser("sheet")
    b.add_argument("--root", default=ROOT)
    b.add_argument("--states", required=True)
    b.add_argument("--material", required=True)
    b.add_argument("--sheet", required=True)
    c = sub.add_parser("types")
    c.add_argument("--root", default=ROOT)
    c.add_argument("--states", required=True)
    c.add_argument("--typed", required=True)
    c.add_argument("--out", required=True)
    a_ = ap.parse_args(argv)
    if a_.cmd == "states":
        run_states(root=a_.root, procs=a_.procs, out=a_.out, material=a_.material, check=a_.check)
    elif a_.cmd == "sheet":
        run_sheet(a_.states, a_.material, a_.sheet, root=a_.root)
    elif a_.cmd == "types":
        run_types(a_.states, a_.typed, a_.out, root=a_.root)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
