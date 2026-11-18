# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TSS_RETAKE_SEAL_2026-11-18.md(RT ― TSS の系列(第 1 便・第 2 便・便 1b・便 PS)を、直した engine で取り直して前の記録と並べる)の測定。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(``core/``・``adapters/``)は 1 行も変えない。**材料は TSS の置き場(~/.cache/audit-core/tanshin-self-2026-11-14/)の ZIP 400 本を読むだけ。

    python3 measure/xbrl_tss_retake_2026-11-18.py run --out PATH --scratch DIR [--material DIR] [--procs N]      # 段 1〜5 を取り直して前の記録と並べる → fixtures/xbrl/tss_retake/retake_2026-11-18.json
    python3 measure/xbrl_tss_retake_2026-11-18.py run --check --scratch DIR [--material DIR] [--procs N]        # 書かずに作り直し、在る記録と比べる(時間の欄は除く)

``--scratch`` は repo の外の folder(取り直した大きい出力を置く。段 2・3・4 の出力の file は中に作る。在れば止まる)。

実装の注(封 §2 が 1 通りに決めていない細部の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 前の 4 便の script(第 2 便 ``xbrl_tanshin_self2_2026-11-14.py``・便 1b ``xbrl_tanshin_self_inject_2026-11-14.py``・便 PS ``xbrl_plan_source_2026-11-17.py``。第 1 便は第 2 便が読む TSS)は
  ``load_module`` の形(読み込みの前に居た名前を元の object へ戻す)で読み、関数を **呼ぶ**(写さない)。前の script・前の記録は 1 byte も変えない(入力の表の sha256 が 1 つでも違えば止まる)。
- 段 1 = TSS の ``states_job``(400 本。記録は書かない)。段 2 = 第 2 便の ``run_interim``(引数 ``tss_states`` に段 1 の本)。段 3 = 第 2 便の ``run_near``(``interim`` に段 2 の出力の file・``tss_states`` に段 1 の本)。
  段 4 = 便 1b の ``run_inject``(引数 ``bases`` に 段 1 の A の本と段 2 の丙の本)。段 5 = 便 PS の ``states_job`` と ``analyze``(``build_record`` は呼ばない。理由は「読み替えた所」)。
- 段 2・3・4 の出力の file は ``--scratch`` の下に作る(repo に置かない)。repo に置くのは ``--out`` の 1 本だけ。
- 段 1 の後に RT-1(便 NRE の記録の「直した engine の state」と行ごとに同じか)を判定し、違う行が 1 行でも在れば(行の鍵の集合が違っても)段 2 へ進まず止める(数だけ出す)。
- 行の鍵 = 段 1・2 は (本の #, 文の番号, 位置)・段 3 は同じ・段 4 は (本の #, 注入の行の id)(注入の行は文の番号・位置を持たない)・段 5 は (本の #, 文の番号, 位置, 組)。
  前の記録の行は、今回の母集団の本の # に限って取り出す(全数の走らせでは 400 本の全部)。片方にしか無い行は「消えた行」「増えた行」として別に数える。
- 率は整数の分子・分母を並べ、% は小数 1 桁の整数計算(便 NR と同じ)。ポイントの差は分数から小数 2 桁(整数の計算)。
- 記録は文・span・値・要素名・context の字・会社名・証券コード・docID・金額を持たない。時間(秒)以外は 2 回走らせて byte で同じ。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import json
import os
import sys
import time
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


S2 = load_module("xbrl_tanshin_self2_2026-11-14.py", "tanshin_self2_for_tss_retake")                    # 第 2 便(中に TSS)
INJ = load_module("xbrl_tanshin_self_inject_2026-11-14.py", "tanshin_self_inject_for_tss_retake")        # 便 1b
PS = load_module("xbrl_plan_source_2026-11-17.py", "plan_source_for_tss_retake")                          # 便 PS
TSS = S2.TSS
ST = TSS.ST
TS = TSS.TS
VD = S2.VD
Stop = ST.Stop

SEAL_REL = "docs/XBRL_TSS_RETAKE_SEAL_2026-11-18.md"
SEAL_COMMIT = "b4c08fc6"
SCRIPT_REL = "measure/xbrl_tss_retake_2026-11-18.py"
REC_DIR_REL = "fixtures/xbrl/tss_retake"
RECORD_REL = REC_DIR_REL + "/retake_2026-11-18.json"
POPULATION_REL = ST.POPULATION_REL
TSS_STATES_REL = "fixtures/xbrl/tanshin_self/states_2026-11-14.json"
INTERIM_REL = "fixtures/xbrl/tanshin_self/states_interim_2026-11-14.json"
NEAR_REL = "fixtures/xbrl/tanshin_self/near_2026-11-14.json"
INJECT_REL = "fixtures/xbrl/tanshin_self/inject_2026-11-14.json"
VM_TYPES_REL = "fixtures/xbrl/tanshin_self/vm_types_2026-11-14.json"
NEAR_TYPES_REL = "fixtures/xbrl/tanshin_self/near_types_2026-11-14.json"
PASSED_TYPES_REL = "fixtures/xbrl/tanshin_self/inject_passed_types_2026-11-14.json"
PS_STATES_REL = "fixtures/xbrl/plan_source/states_2026-11-17.json"
PS_READ_TYPES_REL = "fixtures/xbrl/plan_source/read_types_2026-11-17.json"
NRE_STATES_REL = "fixtures/xbrl/nil_read_engine/states_2026-11-17.json"
SCRATCH_NAMES = ("interim_2026-11-18.json", "near_2026-11-18.json", "inject_2026-11-18.json")

#: 入力(# , path, sha256)。違えば止まる(前の 4 便の script と記録・便 NRE の記録を 1 byte も変えない)。門が実物と 1 つずつ照らす
INPUTS = (
    (1, "fixtures/xbrl/tanshin_self/population_2026-11-14.json", "48ba8e5574be70d85b3d1affacc9403cffbfc698f529c095c6c882cd8ccfa9b0"),
    (2, "fixtures/xbrl/tanshin_self/states_2026-11-14.json", "00414222cfe8cb05d0a1fed3d3e5a09bacafa6547f1675975a3cebd3e4ef70f6"),
    (3, "fixtures/xbrl/tanshin_self/states_interim_2026-11-14.json", "ef443ec1b1331fa05ca314122fe36ad28746816e890f73f27efde55738bb5e7e"),
    (4, "fixtures/xbrl/tanshin_self/near_2026-11-14.json", "5c2b6ee418495ac184ab51eb424e2e0ef11a04b881bbf719cb31e2c3018e0952"),
    (5, "fixtures/xbrl/tanshin_self/inject_2026-11-14.json", "ea9a2e22932f0c5f4c8158291b0fa224c47709b07bb1fd4f61b3a64e8148b742"),
    (6, "fixtures/xbrl/tanshin_self/vm_types_2026-11-14.json", "d1392722f345c408372ec644e15170463554683c3c7ff3951a51d9f66a1f5183"),
    (7, "fixtures/xbrl/tanshin_self/near_types_2026-11-14.json", "f59cfc68a6ddf98b9a713efdda52f8bf04d183bc9b415964bb724812810f779f"),
    (8, "fixtures/xbrl/tanshin_self/inject_passed_types_2026-11-14.json", "6387b09d9e51f20da9e7fd8d2cf36ba5d006b7f72d93da3d56f2fe1bdb8aa01b"),
    (9, "fixtures/xbrl/plan_source/states_2026-11-17.json", "d007b1454c0b4c6f30b3627d54221376767d0f0a1233578dbd37bcfe2df51424"),
    (10, "fixtures/xbrl/plan_source/read_types_2026-11-17.json", "c244d1bf51e7867e1772f98bd6d4c0085fa816faf1ec09f7855050aa99fe5e56"),
    (11, "fixtures/xbrl/nil_read_engine/states_2026-11-17.json", "13674c80a367e2c54889cccce0c59418891c8ad66dc10bf52f5744e4697900a0"),
    (12, "measure/xbrl_tanshin_self_stage_2026-11-14.py", "4ed60b591366dd65a431dba5348aff6edb3889676d8e9a4154a5b0298486f7f9"),
    (13, "measure/xbrl_tanshin_self_2026-11-14.py", "fa603d1c2dbfdee7c3ad4197ab9c4a9f1428419ada57293f346418bc0997aeb6"),
    (14, "measure/xbrl_tanshin_self2_2026-11-14.py", "7a3db37e77e8013f56668d7202dbddae023778d57fecaf7b8bc5c621a68583b8"),
    (15, "measure/xbrl_tanshin_self_inject_2026-11-14.py", "ad33fef1537cfb7a0d866dfe38576abe0528b441f50512e03ad72232a7cc2c9a"),
    (16, "measure/xbrl_plan_source_2026-11-17.py", "0617d75a98e9aca390426b2751bed5ae40a8aa8759b3e80bffab163e1abeb8ea"),
    (17, "measure/xbrl_tanshin_2026-11-09.py", "b7ea491bf5cd34c4976bde86c4329583e0d9af09ec8895ea0caf48491492b5bd"),
)

PROFILE = "P33E"
FP_KEYS = PS.FP_KEYS
STATES = tuple(TS.STATES)
G = STATES[0]
VM = STATES[1]
CUT_OK = TSS.CUT_OK
A_GROUPS = TSS.A_GROUPS
B_GROUPS = TSS.B_GROUPS
T_PRIOR = INJ.T9
MAIN_TYPES = tuple(INJ.MAIN_TYPES)
WORD_PASS = INJ.LABEL_PASS
WORD_ORIGINAL = INJ.TUNE.LABEL_NAMED_ORIGINAL
GROUP_NAMES = tuple(INJ.GROUP_NAMES)
SET_P, SET_W = PS.SET_P, PS.SET_W
READ_LITERAL_RAW = (PS.SUM_RAW, PS.READING_LITERAL)
READ_LITERAL_NONNIL = (PS.SUM_NONNIL, PS.READING_LITERAL)
GRP_P_SETS = (PS.GRP_KOU, PS.GRP_OTSU)

K_STAGES = (u"段 1(第 1 便。400 本の判定)", u"段 2(第 2 便(一)。中間 150 本の期の名前を写した判定)", u"段 3(第 2 便(二)。近い行)", u"段 4(便 1b。注入)", u"段 5(便 PS。サマリーの当てる先)")
K_PRED = u"予測の判定に要る数(RT-1〜RT-6。当たり・外れは結果の文書で)"
K_READ = u"読み替えた所"
K_RT1 = u"RT-1(段 1 の行 対 便 NRE の記録の「直した engine の state」)"

LIMITS = (
    u"標本は英文短信を出している会社の 400 本で、上場会社全体の率ではない(前の 4 便と同じ)",
    u"AI の席の読み(第 1 便の標本の型・近い行の型・通した行の札・便 PS の 2 軸の読み)は付け直していない。取り直しで新しく「値が違う」「近い」「通した」「P」になった行は誰も読んでいない",
    u"丙は期の名前を measure/ の側で写した読みの上の数で、engine の読みそのものではない(第 2 便と同じ)",
    u"便 KAM・便 YS・英文短信の側・2026-11-09 の短信の便は取り直していない。便 AT(型の読みの数え直し)も取り直していない",
    u"空白入りの自己閉じの形は直した式でも始まりと読む(便 NRE の限界のまま)",
    u"注入の行は文の番号・位置を持たないので、前後の突き合わせの鍵は (本の #, 行の id)。同じ id が前と後で別の site を指していても、鍵の上では同じ行として並べる(基準の claim・単位・形が同じかは別の欄で数える)",
    u"行は [本の #, 文の番号, 位置, 前の state, 後の state] などの数と記号だけで、文・span・値・要素名・context の字・会社名・証券コード・docID・金額は持たない")

READ_NOTES = (
    u"段 2: 第 2 便の run_interim の引数 tss_states(前の script は TSS の記録の file を読む)に、段 1 の取り直した本を渡した。run_interim の中の「写す前(TSS の B)との動き」は段 1 の取り直した B との動きになる",
    u"段 3: 第 2 便の run_near の引数 tss_states(A の state の一致の比べの相手)に段 1 の取り直した本・interim(B の state の一致の比べの相手と、同じ script で作られたかの確かめ)に段 2 の出力の file を渡した。"
    u"「前の記録と同じでなければ止める」(A は TSS の記録・B は interim の記録)は「取り直した前の段と同じでなければ止める」に読み替わった。それ以外の守り(材料の sha256・母集団・置き場の前後)は外していない",
    u"段 4: 便 1b の run_inject の引数 bases(前の script は TSS の記録と interim の記録から load_bases で作る)に、段 1 の A(甲・乙)の本と段 2 の丙の本を渡した。無改変の文の判定が土台の行と同じでなければ止める守りは取り直した土台に対して働く",
    u"段 5: 便 PS の build_record は呼ばず(「engine の指紋が TSS の記録のものと同じ」「TSS の記録の ZIP の sha256」「P が 794 行・W が 20 行」の守りが直した engine では必ず止まるため)、states_job と analyze を呼ぶ。"
    u"states_job の引数 exp_cut・exp_rows に段 1 の取り直した本を渡し(前の script は TSS の記録)、analyze の expect_p・expect_w は渡さない(None)",
    u"段 5: W の鍵(第 1 便の標本の型 ウ の行)のうち、取り直した claim に当たらない鍵は analyze に渡す前に除き、「W の消えた行」として数えた(analyze はそのとき止まる作りのため)",
    u"段 5: 別の本の輪・読み 4 通り・単位の族・札の列は便 PS の関数のまま。前の記録の P・W の行との突き合わせの鍵は (本の #, 文の番号, 位置, 組)",
    u"前の記録の取り出し: 前の「集計」「行」は各記録の file の欄をそのまま読んだ(作り直していない)")


def rate(n, d):
    u"""{分子, 分母, 率}。率は小数 1 桁の %(四捨五入は整数の計算)。分母 0 は「分母 0」。"""
    t = u"分母 0" if d == 0 else u"%d.%d%%" % divmod((n * 2000 + d) // (2 * d), 10)
    return collections.OrderedDict([(u"分子", n), (u"分母", d), (u"率", t)])


def point_diff(n1, d1, n2, d2):
    u"""(n2/d2 − n1/d1) × 100 を小数 2 桁の字で(整数の計算。四捨五入は 0 から遠い側へ)。分母 0 があれば「分母 0」。"""
    if d1 == 0 or d2 == 0:
        return u"分母 0"
    x = Fraction(n2 * 100, d2) - Fraction(n1 * 100, d1)
    neg = x < 0
    k = int(abs(x) * 100 + Fraction(1, 2))
    return u"%s%d.%02d" % (u"-" if neg and k else u"", k // 100, k % 100)


def load_json(p):
    return TSS.load_json(p)


# ======================================================================================================
# 突き合わせ(鍵で前と後を結ぶ)
def key_sorted(d):
    return sorted(d)


def pair_up(before, after):
    u"""{鍵: 値} と {鍵: 値} → (両方に在る鍵の列, 前にだけ在る鍵の列, 後にだけ在る鍵の列)。鍵の順。"""
    both = [k for k in key_sorted(before) if k in after]
    return both, [k for k in key_sorted(before) if k not in after], [k for k in key_sorted(after) if k not in before]


def state_rows(books, nums=None):
    u"""本の集まり → {(本の #, 文の番号, 位置): 行 [文の番号, 位置, state, reason, ...]}。nums が在ればその本だけ。"""
    out = {}
    for b in books:
        if nums is not None and b[u"#"] not in nums:
            continue
        for r in b[u"行"]:
            out[(b[u"#"], r[0], r[1])] = r
    return out


def state_compare(old_books, new_books, nums=None):
    u"""段 1・2。行の (本の #, 文の番号, 位置) で前と後の state を結ぶ。"""
    old, new = state_rows(old_books, nums), state_rows(new_books, nums)
    both, only_old, only_new = pair_up(old, new)
    changed = [k for k in both if old[k][2] != new[k][2]]
    trans = collections.Counter((old[k][2], new[k][2]) for k in both)
    table = collections.OrderedDict((u"%s → %s" % (a, b), trans.get((a, b), 0)) for a in STATES for b in STATES)
    return collections.OrderedDict([
        (u"行(前)", len(old)), (u"行(後)", len(new)), (u"両方に在る行", len(both)),
        (u"前にだけ在る行(消えた行)", len(only_old)), (u"後にだけ在る行(増えた行)", len(only_new)),
        (u"state が変わった行", rate(len(changed), len(both))), (u"state が変わった行を持つ本", len(set(k[0] for k in changed))),
        (u"両方に在る行の state の移り変わり(前 → 後)", table),
        (u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)", sum(1 for k in changed if old[k][2] == G)),
        (u"前は GROUNDED でなく後は GROUNDED の行(両方に在る行)", sum(1 for k in changed if new[k][2] == G)),
        (u"前は GROUNDED で消えた行", sum(1 for k in only_old if old[k][2] == G)),
        (u"state は同じで reason だけ変わった行", sum(1 for k in both if old[k][2] == new[k][2] and old[k][3] != new[k][3])),
        (u"変わった行の欄", [u"本の #", u"文の番号", u"位置", u"前の state", u"後の state"]),
        (u"変わった行", [[k[0], k[1], k[2], old[k][2], new[k][2]] for k in changed]),
        (u"消えた行の欄", [u"本の #", u"文の番号", u"位置", u"前の state"]),
        (u"消えた行", [[k[0], k[1], k[2], old[k][2]] for k in only_old]),
        (u"増えた行の欄", [u"本の #", u"文の番号", u"位置", u"後の state"]),
        (u"増えた行", [[k[0], k[1], k[2], new[k][2]] for k in only_new])])


def cut_differences(old_books, new_books, nums=None):
    u"""前と後で切り出しの結果(切れた・切れない)が違う本の数。"""
    old = dict((b[u"#"], b[u"切り出し"]) for b in old_books if nums is None or b[u"#"] in nums)
    new = dict((b[u"#"], b[u"切り出し"]) for b in new_books if nums is None or b[u"#"] in nums)
    return sum(1 for n in old if n in new and old[n] != new[n]) + len(set(old) ^ set(new))


def rt1_numbers(new_books, nre_rows, nums=None):
    u"""RT-1: 取り直した段 1 の行の state と、便 NRE の記録の「直した engine の state」(行の 4 番目)を、行の鍵 (本の #, 文の番号, 位置) で突き合わせる。"""
    new = dict((k, r[2]) for k, r in state_rows(new_books, nums).items())
    nre = dict(((r[0], r[1], r[2]), r[3]) for r in nre_rows if nums is None or r[0] in nums)
    both, only_nre, only_new = pair_up(nre, new)
    diff = [k for k in both if nre[k] != new[k]]
    return collections.OrderedDict([
        (u"行(便 NRE の記録)", len(nre)), (u"行(取り直し)", len(new)), (u"両方に在る行", len(both)),
        (u"state が違う行", rate(len(diff), len(both))),
        (u"便 NRE の記録にだけ在る行", len(only_nre)), (u"取り直しにだけ在る行", len(only_new))])


def near_compare(old_rec, new_rec, nums=None):
    u"""段 3。近い行 [本の #, 文の番号, 位置, [当たった規則], 単位の族] を (本の #, 文の番号, 位置) で結ぶ。"""
    old = dict(((r[0], r[1], r[2]), r) for r in old_rec[u"行"] if nums is None or r[0] in nums)
    new = dict(((r[0], r[1], r[2]), r) for r in new_rec[u"行"] if nums is None or r[0] in nums)
    both, only_old, only_new = pair_up(old, new)
    rule_changed = [k for k in both if old[k][3] != new[k][3]]
    fam_changed = [k for k in both if old[k][4] != new[k][4]]
    return collections.OrderedDict([
        (u"近い行(前)", len(old)), (u"近い行(後)", len(new)), (u"前の近い行のうち後も近い行", len(both)),
        (u"前にだけ在る行(消えた行)", len(only_old)), (u"後にだけ在る行(増えた行)", len(only_new)),
        (u"両方に在る行のうち当たった規則が変わった行", len(rule_changed)), (u"両方に在る行のうち単位の族が変わった行", len(fam_changed)),
        (u"消えた行の欄", [u"本の #", u"文の番号", u"位置", u"当たった規則", u"単位の族"]), (u"消えた行", [list(old[k]) for k in only_old]),
        (u"増えた行の欄", [u"本の #", u"文の番号", u"位置", u"当たった規則", u"単位の族"]), (u"増えた行", [list(new[k]) for k in only_new]),
        (u"規則が変わった行の欄", [u"本の #", u"文の番号", u"位置", u"前の規則", u"後の規則"]),
        (u"規則が変わった行", [[k[0], k[1], k[2], list(old[k][3]), list(new[k][3])] for k in rule_changed])])


def inject_key(r):
    return (r[u"本の #"], r[u"id"])


def inject_rows(rows, nums=None):
    return dict((inject_key(r), r) for r in rows if nums is None or r[u"本の #"] in nums)


def inject_word(r):
    return r[PROFILE][u"結果"]


def inject_cells(rows):
    u"""群(A・丙)× 型(値・偶然の一致・比)の 6 つの升の (「名指して原本の値を返した」の件数, 注入の行)。"""
    out = collections.OrderedDict()
    for g in GROUP_NAMES:
        for t in MAIN_TYPES:
            sel = [r for r in rows if INJ.group_name(r[u"群"]) == g and r[u"型"] == t]
            out[(g, t)] = (sum(1 for r in sel if inject_word(r) == WORD_ORIGINAL), len(sel))
    return out


def inject_passed(rows):
    u"""通した行の数 {全体, 丙 × 期の入れ替えの型, 型ごと}。"""
    p = [r for r in rows if inject_word(r) == WORD_PASS]
    return collections.OrderedDict([
        (u"通した行の合計", len(p)), (u"うち丙の期の入れ替えの型", sum(1 for r in p if r[u"群"] in B_GROUPS and r[u"型"] == T_PRIOR)),
        (u"型ごと", collections.OrderedDict((t, sum(1 for r in p if r[u"型"] == t)) for t in INJ.TYPES))])


def inject_compare(old_rows, new_rows, nums=None):
    u"""段 4。注入の行を (本の #, id) で結ぶ。"""
    old, new = inject_rows(old_rows, nums), inject_rows(new_rows, nums)
    both, only_old, only_new = pair_up(old, new)
    changed = [k for k in both if inject_word(old[k]) != inject_word(new[k])]
    other_site = [k for k in both if (old[k][u"型"], old[k][u"形"], old[k][u"単位"], old[k][u"基準の claim"]) != (new[k][u"型"], new[k][u"形"], new[k][u"単位"], new[k][u"基準の claim"])]
    words = INJ.LABELS
    trans = collections.Counter((inject_word(old[k]), inject_word(new[k])) for k in both)
    table = collections.OrderedDict((u"%s → %s" % (a, b), trans.get((a, b), 0)) for a in words for b in words)
    cells_old, cells_new = inject_cells(list(old.values())), inject_cells(list(new.values()))
    cells = [collections.OrderedDict([
        (u"群", g), (u"型", t), (u"前の分子", cells_old[(g, t)][0]), (u"前の分母", cells_old[(g, t)][1]), (u"後の分子", cells_new[(g, t)][0]), (u"後の分母", cells_new[(g, t)][1]),
        (u"差(ポイント。小数 2 桁。後 − 前)", point_diff(cells_old[(g, t)][0], cells_old[(g, t)][1], cells_new[(g, t)][0], cells_new[(g, t)][1]))]) for (g, t) in cells_old]
    return collections.OrderedDict([
        (u"注入の行(前)", len(old)), (u"注入の行(後)", len(new)), (u"両方に在る行", len(both)),
        (u"前にだけ在る行(消えた行)", len(only_old)), (u"後にだけ在る行(増えた行)", len(only_new)),
        (u"結果の語が変わった行", rate(len(changed), len(both))), (u"両方に在る行のうち型・形・単位・基準の claim のどれかが違う行", len(other_site)),
        (u"両方に在る行の結果の語の移り変わり(前 → 後)", table),
        (u"通した行(前)", inject_passed(list(old.values()))), (u"通した行(後)", inject_passed(list(new.values()))),
        (u"升ごとの「名指して原本の値を返した」", cells),
        (u"変わった行の欄", [u"本の #", u"id", u"型", u"前の結果の語", u"後の結果の語"]),
        (u"変わった行", [[k[0], k[1], old[k][u"型"], inject_word(old[k]), inject_word(new[k])] for k in changed]),
        (u"消えた行の欄", [u"本の #", u"id", u"型", u"前の結果の語"]), (u"消えた行", [[k[0], k[1], old[k][u"型"], inject_word(old[k])] for k in only_old]),
        (u"増えた行の欄", [u"本の #", u"id", u"型", u"後の結果の語"]), (u"増えた行", [[k[0], k[1], new[k][u"型"], inject_word(new[k])] for k in only_new])])


def ps_key(r):
    return (r[PS.R_BOOK], r[PS.R_SI], r[PS.R_POS], r[PS.R_SET])


def ps_rows(rows, nums=None):
    return dict((ps_key(r), r) for r in rows if nums is None or r[PS.R_BOOK] in nums)


def ps_compare(old_rows, new_rows, nums=None):
    u"""段 5。P・W の行を (本の #, 文の番号, 位置, 組) で結ぶ。"""
    old, new = ps_rows(old_rows, nums), ps_rows(new_rows, nums)
    both, only_old, only_new = pair_up(old, new)
    n_cols = PS.N_COLUMNS
    changed = [(k, [i for i in range(4, n_cols) if old[k][i] != new[k][i]]) for k in both]
    changed = [(k, c) for k, c in changed if c]
    per_read = collections.OrderedDict()
    for rd, idx in PS.IDX.items():
        per_read[PS.READ_LABELS[rd]] = sum(1 for k in both if tuple(old[k][i] for i in idx) != tuple(new[k][i] for i in idx))
    iS, iR, iO = PS.IDX[READ_LITERAL_RAW][2:5]
    nS, nR, nO = PS.IDX[READ_LITERAL_NONNIL][2:5]
    p_both = [k for k in both if k[3] == SET_P]
    rt5b = [k for k in p_both if (new[k][iS], new[k][iR], new[k][iO]) != (old[k][nS], old[k][nR], old[k][nO])]
    p_new = [k for k in new if k[3] == SET_P]
    ident = [k for k in p_new if (new[k][iS], new[k][iR], new[k][iO]) != (new[k][nS], new[k][nR], new[k][nO])]
    return collections.OrderedDict([
        (u"P の行(前)", sum(1 for k in old if k[3] == SET_P)), (u"P の行(後)", len(p_new)),
        (u"W の行(前)", sum(1 for k in old if k[3] == SET_W)), (u"W の行(後)", sum(1 for k in new if k[3] == SET_W)),
        (u"両方に在る行", len(both)), (u"両方に在る P の行", len(p_both)),
        (u"前にだけ在る行(消えた行)", len(only_old)), (u"後にだけ在る行(増えた行)", len(only_new)),
        (u"どれかの欄が変わった行", len(changed)), (u"読みごとの札が変わった行", per_read),
        (u"両方に在る P の行のうち後の字のとおりの読みの自・実・他が前の字のとおり × 空の欄を除く読みの自・実・他と違う行", len(rt5b)),
        (u"参考: 後の P の行のうち字のとおりの読みの自・実・他が空の欄を除く読みの自・実・他と違う行", len(ident)),
        (u"変わった行の欄", [u"本の #", u"文の番号", u"位置", u"組", u"変わった欄の番号(行の欄の 0 始まり)"]),
        (u"変わった行", [[k[0], k[1], k[2], k[3], c] for k, c in changed]),
        (u"消えた行の欄", [u"本の #", u"文の番号", u"位置", u"組"]), (u"消えた行", [list(k) for k in only_old]),
        (u"増えた行の欄", [u"本の #", u"文の番号", u"位置", u"組"]), (u"増えた行", [list(k) for k in only_new])])


def rt6_block(vm_rows, near_read_rows, near_rows_new, passed_rows, passed_new, read_rows, ps_new_keys, new_states, nums=None):
    u"""RT-6 の 4 つの分子と分母。行の列は前の記録の型の file の「行」(各 file の行の欄の並び)。nums があればその本の行だけ。"""
    def pick(rows, n_at):
        return [r for r in rows if nums is None or r[n_at] in nums]
    vm = pick(vm_rows, 1)
    vm_bad = [r for r in vm if new_states.get((r[1], r[2], r[3]), [None, None, None])[2] != VM]
    near_keys = set((r[0], r[1], r[2]) for r in near_rows_new)
    nr = pick(near_read_rows, 1)
    nr_bad = [r for r in nr if (r[1], r[2], r[3]) not in near_keys]
    pr = pick(passed_rows, 1)
    pr_bad = [r for r in pr if (r[1], r[2]) not in passed_new or inject_word(passed_new[(r[1], r[2])]) != WORD_PASS]
    rd = pick(read_rows, 1)
    rd_bad = [r for r in rd if (r[1], r[2], r[3], SET_W if r[4] == PS.GRP_W else SET_P) not in ps_new_keys]
    return collections.OrderedDict([
        (u"第 1 便の標本(state が「値が違う」でなくなった行)", rate(len(vm_bad), len(vm))),
        (u"近い行の読み(近い行でなくなった行)", rate(len(nr_bad), len(nr))),
        (u"通した行の札(通した行でなくなった行)", rate(len(pr_bad), len(pr))),
        (u"便 PS の読みの行(P か W でなくなった行)", rate(len(rd_bad), len(rd)))])


# ======================================================================================================
# 予測の判定に要る数(当たり・外れの字は書かない)
def prediction_numbers(s1, s2, s3, s4, s5, rt1, rt6):
    cells = s4[u"升ごとの「名指して原本の値を返した」"]
    return collections.OrderedDict([
        (u"RT-1 段 1 の行の state が便 NRE の記録の「直した engine の state」と違う行 / 両方に在る行", rt1[u"state が違う行"]),
        (u"RT-1 便 NRE の記録にだけ在る行・取り直しにだけ在る行", collections.OrderedDict([(u"便 NRE の記録にだけ", rt1[u"便 NRE の記録にだけ在る行"]), (u"取り直しにだけ", rt1[u"取り直しにだけ在る行"])])),
        (u"RT-2a 段 2 で state が変わった行 / 両方に在る行", s2[u"state が変わった行"]),
        (u"RT-2a 段 2 の前の行・消えた行・増えた行", collections.OrderedDict([(u"前の行", s2[u"行(前)"]), (u"消えた行", s2[u"前にだけ在る行(消えた行)"]), (u"増えた行", s2[u"後にだけ在る行(増えた行)"])])),
        (u"RT-2b 段 2 で前は GROUNDED で後は GROUNDED でない行(両方に在る行)・前は GROUNDED で消えた行", collections.OrderedDict([
            (u"両方に在る行", s2[u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)"]), (u"消えた行", s2[u"前は GROUNDED で消えた行"])])),
        (u"RT-3a 段 3 の近い行の数(後)", s3[u"近い行(後)"]),
        (u"RT-3b 前の近い行のうち後も近い行 / 前の近い行", collections.OrderedDict([(u"分子", s3[u"前の近い行のうち後も近い行"]), (u"分母", s3[u"近い行(前)"])])),
        (u"RT-4a 段 4 の注入の行の数(後)", s4[u"注入の行(後)"]),
        (u"RT-4b 通した行の合計(前・後)と、うち丙の期の入れ替えの型(前・後)", collections.OrderedDict([
            (u"合計(前)", s4[u"通した行(前)"][u"通した行の合計"]), (u"合計(後)", s4[u"通した行(後)"][u"通した行の合計"]),
            (u"丙の期の入れ替えの型(前)", s4[u"通した行(前)"][u"うち丙の期の入れ替えの型"]), (u"丙の期の入れ替えの型(後)", s4[u"通した行(後)"][u"うち丙の期の入れ替えの型"])])),
        (u"RT-4c 群 × 型の 6 つの升の「名指して原本の値を返した」の率の差(ポイント。後 − 前)", collections.OrderedDict(
            (u"%s × %s" % (c[u"群"], c[u"型"]), c[u"差(ポイント。小数 2 桁。後 − 前)"]) for c in cells)),
        (u"RT-5a 段 5 の P の行の数(後)", s5[u"P の行(後)"]),
        (u"RT-5b 両方に在る P の行のうち後の字のとおりの読みの自・実・他が前の字のとおり × 空の欄を除く読みの旗と違う行 / 両方に在る P の行", collections.OrderedDict([
            (u"分子", s5[u"両方に在る P の行のうち後の字のとおりの読みの自・実・他が前の字のとおり × 空の欄を除く読みの自・実・他と違う行"]), (u"分母", s5[u"両方に在る P の行"])])),
        (u"RT-5b 参考(後の字のとおりの読み 対 後の空の欄を除く読み)の違う行 / 後の P の行", collections.OrderedDict([
            (u"分子", s5[u"参考: 後の P の行のうち字のとおりの読みの自・実・他が空の欄を除く読みの自・実・他と違う行"]), (u"分母", s5[u"P の行(後)"])])),
        (u"RT-6 AI の席が読んだ行のうち前提が変わった行", rt6)])


# ======================================================================================================
# 入力・記録
def check_inputs(root):
    u"""入力の sha256 が表と同じか。違えば止める。"""
    out = []
    for no, rel, want in INPUTS:
        p = os.path.join(root, rel)
        if not os.path.isfile(p) or ST.sha256_file(p) != want:
            raise Stop(u"**入力 %d の sha256 が表と違う。止める**" % no)
        out.append(collections.OrderedDict([(u"#", no), (u"path", rel), (u"sha256", want)]))
    return out


def engine_fp(nre_rec, tss_rec):
    u"""今の engine の指紋(4 欄)。便 NRE の記録の「直した後」と同じでなければ止める。TSS の記録(直す前)と同じでも止める(直した engine が走っていない)。"""
    fp = VD.engine_fingerprint()
    now = collections.OrderedDict((k, fp[k]) for k in FP_KEYS)
    after_nre = collections.OrderedDict((k, nre_rec[u"engine の指紋(直した後)"][k]) for k in FP_KEYS)
    was = collections.OrderedDict((k, tss_rec[u"engine の指紋"][k]) for k in FP_KEYS)
    if now != after_nre:
        raise Stop(u"**engine の指紋が便 NRE の記録の「直した後」と違う。止める**")
    if now == was:
        raise Stop(u"**engine の指紋が直す前(TSS の記録)と同じ。直した engine が走っていない。止める**")
    return now, was


def material_dir(material):
    prod = os.path.abspath(ST.default_cache_dir())
    mat = os.path.abspath(material) if material else prod
    return mat, mat == prod


def scratch_paths(scratch):
    u"""段 2・3・4 の出力の file の path。scratch が repo の中なら止める。どれかが既に在れば止める。"""
    d = os.path.abspath(scratch)
    if TSS.inside_repo(d):
        raise Stop(u"**--scratch が repo の中(または git の木の中)。取り直した大きい出力は repo の外に置く。止める**")
    paths = [os.path.join(d, n) for n in SCRATCH_NAMES]
    if any(os.path.exists(p) for p in paths):
        raise Stop(u"**--scratch の中に出力の file が既に在る。止める**")
    os.makedirs(d, exist_ok=True)
    return paths


def subset_shape(pop):
    u"""母集団が 400 行そのままなら None(既定)。小さい表(配線の確かめ)なら (行数, 群の数)。"""
    if len(pop) == ST.N_ROWS:
        return None
    return len(pop), collections.OrderedDict((g, sum(1 for r in pop if r[1] == g)) for g in ST.GROUP_COUNTS)


def stage1(pop, mat, procs, say, shape=None):
    u"""段 1 = TSS の ``states_job``(400 本。記録は書かない)。"""
    ST.validate_population(pop, *(shape or (ST.N_ROWS, ST.GROUP_COUNTS)))
    for (n, _g, _k, sha) in pop:
        if not os.path.exists(os.path.join(mat, sha + u".zip")):
            raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める**" % n)
    before = ST.names_snapshot(mat)
    jobs = [(n, g, k, sha, os.path.join(mat, sha + u".zip")) for (n, g, k, sha) in pop]
    say(u"段 1 states %d 本 × %s ― procs %d" % (len(jobs), PROFILE, procs))
    books = TS.NF.map_pool(TSS.states_job, jobs, procs)
    if before != ST.names_snapshot(mat):
        raise Stop(u"**材料の置き場の件数か名前が変わった。止める**")
    return books


def stage5(pop, mat, procs, say, books1, w_keys):
    u"""段 5 = 便 PS の ``states_job`` と ``analyze``。(P・W の行, N の数, 本ごとの作り直し, W の消えた鍵の数)。"""
    by_book = dict((b[u"#"], b) for b in books1)
    before = ST.names_snapshot(mat)
    jobs = [(n, g, k, sha, os.path.join(mat, sha + u".zip"), by_book[n][u"切り出し"] == CUT_OK, by_book[n][u"行"]) for (n, g, k, sha) in pop]
    say(u"段 5 plan_source %d 本 × %s ― procs %d" % (len(jobs), PROFILE, procs))
    books5 = TS.NF.map_pool(PS.states_job, jobs, procs)
    if before != ST.names_snapshot(mat):
        raise Stop(u"**材料の置き場の件数か名前が変わった。止める**")
    claim_keys = set((b[u"#"], e[u"si"], e[u"pos"]) for b in books5 if b[u"切れた"] for e in b[u"claims"])
    nums = set(r[0] for r in pop)
    w_here = set(k for k in w_keys if k[0] in nums)
    w_present = set(k for k in w_here if k in claim_keys)
    rows, n_c = PS.analyze(books5, w_present, None, None)
    return rows, n_c, books5, len(w_here) - len(w_present)


OLD_RELS = collections.OrderedDict([
    (u"tss", TSS_STATES_REL), (u"nre", NRE_STATES_REL), (u"interim", INTERIM_REL), (u"near", NEAR_REL), (u"inject", INJECT_REL), (u"ps", PS_STATES_REL),
    (u"vm_types", VM_TYPES_REL), (u"near_types", NEAR_TYPES_REL), (u"passed_types", PASSED_TYPES_REL), (u"read_types", PS_READ_TYPES_REL)])


def load_old(root):
    u"""前の記録(入力の表の sha256 を確かめたあとに読む)。{名前: 記録}。"""
    return dict((k, load_json(os.path.join(root, rel))) for k, rel in OLD_RELS.items())


def orchestrate(root=ROOT, procs=1, material=None, scratch=None, say=print, population=None, clock=time.time, old=None):
    u"""段 1 → RT-1 の判定 → 段 2 → 3 → 4 → 5 を前の段の取り直した出力を引数で渡して走らせ、記録(OrderedDict)を返す。書かない。
    ``old`` を渡すと(試験用)入力の sha256 の確かめと前の記録の読みを飛ばして、渡された記録を前の記録として使う。"""
    mat, prod = material_dir(material)
    if old is None:
        inputs = check_inputs(root)
        old = load_old(root)
    else:
        inputs = []
    pop = S2.load_population(root) if population is None else population
    shape = subset_shape(pop)
    nums = None if shape is None else set(r[0] for r in pop)
    p_interim, p_near, p_inject = scratch_paths(scratch)
    tss_rec, nre_rec = old[u"tss"], old[u"nre"]
    fp_now, fp_was = engine_fp(nre_rec, tss_rec)
    if tss_rec[u"profile"] != PROFILE or nre_rec[u"profile"] != PROFILE:
        raise Stop(u"**TSS・NRE の記録の profile が %s でない。止める**" % PROFILE)
    t0 = clock()
    # ---- 段 1 と RT-1
    books1 = stage1(pop, mat, procs, say, shape)
    s1_cut = cut_differences(tss_rec[u"本"], books1, nums)
    if s1_cut:
        raise Stop(u"**切り出しの結果が TSS の記録と違う本が %d 本ある。止める**" % s1_cut)
    rt1 = rt1_numbers(books1, nre_rec[u"行"], nums)
    if rt1[u"state が違う行"][u"分子"] or rt1[u"便 NRE の記録にだけ在る行"] or rt1[u"取り直しにだけ在る行"]:
        raise Stop(u"**RT-1 が外れた。段 2 へ進まず止める(数: state が違う行 %d・便 NRE の記録にだけ在る行 %d・取り直しにだけ在る行 %d・両方に在る行 %d)**" % (
            rt1[u"state が違う行"][u"分子"], rt1[u"便 NRE の記録にだけ在る行"], rt1[u"取り直しにだけ在る行"], rt1[u"両方に在る行"]))
    by1 = dict((b[u"#"], b) for b in books1)
    s1 = state_compare(tss_rec[u"本"], books1, nums)
    s1[u"集計(前。TSS の記録の集計の欄)"] = tss_rec[u"集計"]
    s1[u"集計(後)"] = TSS.tally(books1)
    # ---- 段 2
    old_interim = old[u"interim"]
    rec2 = S2.run_interim(root=root, procs=procs, out=p_interim, material=material, say=say, population=pop, tss_states=by1, shape=shape)
    books2 = rec2[u"本"]
    if cut_differences(old_interim[u"本"], books2, nums):
        raise Stop(u"**第 2 便の切り出しの結果が前の記録と違う本がある。止める**")
    s2 = state_compare(old_interim[u"本"], books2, nums)
    for k in (u"本の数", u"名前がぶつかる本", u"写した本", u"置き換えた回数の合計(規則 1・2・3)", u"集計", u"TSS の B(写さない)との動き"):
        s2[u"%s(前)" % k] = old_interim[k]
        s2[u"%s(後)" % k] = rec2[k]
    # ---- 段 3
    old_near = old[u"near"]
    rec3 = S2.run_near(root=root, procs=procs, interim=p_interim, out=p_near, material=material, say=say, population=pop, tss_states=by1, shape=shape)
    s3 = near_compare(old_near, rec3, nums)
    for k in (u"集計", u"近い行の数(A と B)", u"読む行の規則"):
        s3[u"%s(前)" % k] = old_near[k]
        s3[u"%s(後)" % k] = rec3[k]
    # ---- 段 4
    bases = dict(by1)
    bases.update((b[u"#"], b) for b in books2)
    old_inject = old[u"inject"]
    rec4 = INJ.run_inject(root=root, procs=procs, out=p_inject, material=material, say=say, population=pop, bases=bases)
    s4 = inject_compare(old_inject[u"行"], rec4[u"行"], nums)
    for k in (u"集計", u"母集団"):
        s4[u"%s(前)" % k], s4[u"%s(後)" % k] = old_inject[k], rec4[k]
    s4[u"覆い(群ごと。前)"], s4[u"覆い(群ごと。後)"] = old_inject[u"覆い"][u"群ごと"], rec4[u"覆い"][u"群ごと"]
    # ---- 段 5
    old_ps = old[u"ps"]
    rows5, n_c, books5, w_gone = stage5(pop, mat, procs, say, books1, PS.w_keys_of(old[u"vm_types"]))
    grp_of = dict((b[u"#"], b[u"群"]) for b in books5)
    s5 = ps_compare(old_ps[u"行"], rows5, nums)
    s5[u"W の鍵のうち取り直した claim に当たらない数(W の消えた行)"] = w_gone
    s5[u"集計(前。便 PS の記録の集計の欄)"] = old_ps[u"集計"]
    s5[u"集計(後)"] = PS.tally(rows5, n_c, grp_of)
    s5[u"サマリーの fact(前)"] = old_ps[u"サマリーの fact"]
    s5[u"サマリーの fact(後)"] = PS.fact_stats(books5)
    # ---- RT-6
    rt6 = rt6_block(old[u"vm_types"][u"行"], old[u"near_types"][u"行"], rec3[u"行"], old[u"passed_types"][u"行"], inject_rows(rec4[u"行"]), old[u"read_types"][u"行"],
                    set(ps_key(r) for r in rows5), state_rows(books1, None), nums)
    elapsed = clock() - t0
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"RT(TSS の系列を直した engine で取り直して前の記録と並べる)― 段 1〜5(0 USD・通信なし・engine は 0 行)"
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"入力"] = inputs
    rec[u"engine の指紋(今。便 NRE の記録の直した後と同じ)"] = fp_now
    rec[u"engine の指紋(直す前。TSS の記録のもの)"] = fp_was
    rec[u"profile"] = PROFILE
    rec[u"材料"] = collections.OrderedDict([(u"置き場", ST.display_path(mat) if prod else u"使い捨ての置き場(本番の folder ではない)"), (u"表と一致した ZIP", len(pop))])
    rec[u"段の順"] = list(K_STAGES)
    rec[K_RT1] = rt1
    rec[K_STAGES[0]] = s1
    rec[K_STAGES[1]] = s2
    rec[K_STAGES[2]] = s3
    rec[K_STAGES[3]] = s4
    rec[K_STAGES[4]] = s5
    rec[K_PRED] = prediction_numbers(s1, s2, s3, s4, s5, rt1, rt6)
    rec[K_READ] = list(READ_NOTES)
    rec[u"限界"] = list(LIMITS)
    rec[u"時間(秒)"] = round(elapsed, 1)
    rec[u"key_leaks"] = []
    return rec


def check_text(rec, text, key_value=None):
    scan = text.replace(SEAL_REL, u"")
    for _no, rel, _sha in INPUTS:
        scan = scan.replace(rel, u"")
    TSS.check_clean(rec, scan, key_value)


def dumps(o, level=0):
    u"""記録の字。辞書は 1 欄 1 行・数と字だけの並びは 1 行・並びの並び(行の表)は 1 行 1 組(読みやすさのため。内容は json と同じ)。"""
    pad = u" " * (level + 1)
    if isinstance(o, dict):
        if not o:
            return u"{}"
        body = u",\n".join(u"%s%s: %s" % (pad, json.dumps(k, ensure_ascii=False), dumps(v, level + 1)) for k, v in o.items())
        return u"{\n" + body + u"\n" + u" " * level + u"}"
    if isinstance(o, list):
        if all(not isinstance(x, (dict, list)) for x in o):
            return json.dumps(o, ensure_ascii=False)
        if all(not isinstance(x, dict) and all(not isinstance(y, (dict, list)) for y in (x if isinstance(x, list) else [x])) for x in o):
            return u"[\n" + u",\n".join(pad + json.dumps(x, ensure_ascii=False) for x in o) + u"\n" + u" " * level + u"]"
        return u"[\n" + u",\n".join(pad + dumps(x, level + 1) for x in o) + u"\n" + u" " * level + u"]"
    return json.dumps(o, ensure_ascii=False)


def record_text(rec, key_value=None):
    text = dumps(rec) + u"\n"
    check_text(rec, text, key_value)
    return text


def run(root=ROOT, procs=1, out=None, scratch=None, material=None, say=print, check=False, **kw):
    if not check and out is None:
        raise Stop(u"**--out を指定する(書かずに比べるなら --check)。止める**")
    if scratch is None:
        raise Stop(u"**--scratch を指定する(repo の外の folder)。止める**")
    out = os.path.abspath(out) if out else None
    if out and os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    rec = orchestrate(root=root, procs=procs, material=material, scratch=scratch, say=say, **kw)
    text = record_text(rec)
    if check:
        want = os.path.join(root, RECORD_REL)
        if not os.path.isfile(want):
            raise Stop(u"**在る記録が無い。止める**")
        cur = load_json(want)
        cur[u"時間(秒)"] = 0
        rec2 = json.loads(text, object_pairs_hook=collections.OrderedDict)
        rec2[u"時間(秒)"] = 0
        if dumps(cur) != dumps(rec2):
            raise Stop(u"**作り直した記録が在る記録と違う(時間の欄は除く)。止める**")
        say(u"--check: 在る記録と同じ(時間の欄は除く)")
        return rec
    ST.write_text_exclusive(out, text)
    say(u"-> %s" % os.path.basename(out))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("run")
    a.add_argument("--root", default=ROOT)
    a.add_argument("--out", default=None)
    a.add_argument("--scratch", default=None)
    a.add_argument("--check", action="store_true")
    a.add_argument("--material", default=None)
    a.add_argument("--procs", type=int, default=1)
    a_ = ap.parse_args(argv)
    if a_.cmd == "run":
        run(root=a_.root, procs=a_.procs, out=a_.out, scratch=a_.scratch, material=a_.material, check=a_.check)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
