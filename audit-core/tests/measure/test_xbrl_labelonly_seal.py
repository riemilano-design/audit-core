# -*- coding: utf-8 -*-
"""封 docs/XBRL_LABEL_ONLY_RATES_SEAL_2026-11-10.md(札のある行だけの率 LB ― AI の文 200 本の数の claim で GROUNDED の率と札ごとの率を『全部の行』と『札のある行だけ』で並べる。engine は変えない)の測定の門。封 §0-2・§1・§2・§4・§5・§6。

**この門が縛るもの**(結果の門 ``test_xbrl_labelonly_result.py`` は記録・文書・L-0〜L-2 の照合・表・記録の形を縛る)

1. 封の字: §2 の表が L-0〜L-4 の 5 行でどの行も欄・照合 / 予測・外れ方を持つ・§4 の path(script・門 2 本・結果の文書)・§0-2 の記録の path・決めの要点(札は P28E の (本, id)・既存の行は鍵
   (文の番号, 文の中の位置)・新しい行は札なし・通した = GROUNDED・判定は無い便)。封の字を 1 字変えると赤。
2. 封の字と script の定数が同じ: 封の path と commit(封 9ad2c7d0)・profile 5 つ・記録と結果の文書の path・L-0〜L-2 の数(封の字から読んだ値を literal に留めた値と照らす)。
3. 触らない file は **封の commit の blob と同じ**: engine(``core/``・``adapters/``)・``measure/``(この便の script だけ新しい)・``fixtures/xbrl``(この便の記録だけ新しい)。未 commit の変更・追加も赤。
4. 順序: 封 9ad2c7d0 ⊏ script・門 2 本(記録・結果の文書の順序は結果の門が見る)。未 commit は赤(skip にしない)。
5. 配線(手で作った小さな標本の振る舞い): 札の結び方が P28E の (本, id)・既存の判定が鍵 (文の番号, 文の中の位置) の一致・新しい行は札なし・1 本 5 profile を 1 回ずつ・数の claim は num の列だけ・
   ``run`` の本番の守り(--only で記録を作らない・出力が在れば止まる)・``tally`` は file を書かない・前の便の関数を呼び同名を定義しない・
   script が読み込む前の便の script が ``sys.modules`` の名前を上書きしても、読み込みの前に居た名前は元の object へ戻る。
6. 新しい門が、既存の門が行頭の名前を数える変数名を行頭に置いていない。script・門に docID の字が無い。
7. 門の変異: 封の字・script の定数・順序・触らない file・配線を 1 つずつ壊した標本で上の検査が赤になる。

この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import ast
import collections
import importlib.util
import os
import re
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "measure"))


def load_module(rel, name):
    u"""importlib で読み込む。読み込んだ file が中で読む前の便の script は、決まった名前で ``sys.modules`` に登録し直して**先に居た module を上書きする**。
    読み込みの前に居た名前は、読み込みの後に元の object へ戻す(7109c97 の直しと同じ形)。読み込んだ module 自身の名前 ``name`` は残す。"""
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


NSG = load_module("tests/measure/test_xbrl_nonfunc_seal.py", "nonfunc_seal_gate_for_labelonly_seal")      # 順序・触らない file の部品。門としては走らせない
SGR = NSG.SGR
PR = NSG.PR
SC = load_module("measure/xbrl_labelonly_2026-11-10.py", "labelonly_script_for_seal_gate")

SEAL_REL = SC.SEAL_REL
SEAL_COMMIT_SHORT = "9ad2c7d0"                    # 封の最初の commit(literal に留める。script の定数と違えば script_problems が赤)
DOC_REL = SC.DOC_REL
SCRIPT_RELS = ("measure/xbrl_labelonly_2026-11-10.py",)
GATE_RELS = ("tests/measure/test_xbrl_labelonly_seal.py", "tests/measure/test_xbrl_labelonly_result.py")
RECORD_REL = "fixtures/xbrl/labelonly/rates_2026-11-10.json"
#: 封の commit から 0 行でなければならない path(engine・measure 全部・既存の記録)と、そこに新しく足してよい file(この便の script と記録)
NOT_TOUCHED_RELS = ("adapters", "core", "measure", "fixtures/xbrl")
ALLOWED_NEW = (SCRIPT_RELS[0], RECORD_REL)
#: 封の後の便が、日付と理由を書いて届けた新しい file(字で留める。NF の門の ``later_declared_problems`` をこの便の封で使う。届けていない新しい file・在る file の変更は今も赤)
DECLARED_NEW_AFTER_SEAL = (
    # 2026-11-12: 止まった数字の「見る順」の診断(docs/XBRL_STOP_TRIAGE_DIAG_2026-11-12.md。封なし)。既に在る記録を数え直すだけで engine を呼ばない script 1 本と記録 1 つ。
    # この便の script はどちらも読まない(この便が読む file は READ_ONLY_RELS の byte の一致で別に守る)
    "measure/xbrl_stop_triage_2026-11-12.py", "fixtures/xbrl/aiforms/stop_triage_2026-11-12.json",
    # 2026-11-14: TSS(決算短信の概況の文を同じ短信の添付の財務諸表で確かめる。封 docs/XBRL_TANSHIN_SELF_SEAL_2026-11-14.md e56d6782)の script 2 本。
    # 材料を新しい置き場へ写す script と、切り出し・包み直し・P33E で測る script。engine(core/・adapters/)は 0 行。前の便の script は読み込むだけ
    "measure/xbrl_tanshin_self_stage_2026-11-14.py", "measure/xbrl_tanshin_self_2026-11-14.py",
    # 2026-11-14: TSS の記録 4 つ(置いた 400 本の表・400 本の判定・標本 120 行の型・型の細目。fixtures/xbrl/tanshin_self/)。script 2 本が書いた数と、司令塔(AI の席)が付けた型。
    # 会社名・証券コード・文・値を持たない。結果の門 tests/measure/test_xbrl_tanshin_self_result.py が縛る。engine(core/・adapters/)は 0 行
    "fixtures/xbrl/tanshin_self/population_2026-11-14.json", "fixtures/xbrl/tanshin_self/states_2026-11-14.json",
    "fixtures/xbrl/tanshin_self/vm_types_2026-11-14.json", "fixtures/xbrl/tanshin_self/vm_types_subreading_2026-11-14.json",
    # 2026-11-14: TSS の第 2 便(中間の短信の期の名前を measure/ の側で写して読む・「値が違う」のうち表の値に近い行を拾って読む。封 docs/XBRL_TANSHIN_SELF2_SEAL_2026-11-14.md a1fd09bf)の script 1 本。
    # 第 1 便の script の関数を呼ぶ(書き写さない)。engine(core/・adapters/)は 0 行。この便の記録(fixtures/xbrl/tanshin_self/ の 3 つ)は本番の後に届ける
    "measure/xbrl_tanshin_self2_2026-11-14.py",
    # 2026-11-14: TSS の便 1b の注入(短信の概況の文に誤りを 1 件ずつ入れ、同じ短信の財務諸表に当てる。封 docs/XBRL_TANSHIN_SELF_INJECT_SEAL_2026-11-14.md bcc244ae)の script 1 本。
    # TSS・第 2 便・2026-11-09 の便の関数を呼ぶ(書き写さない)。engine(core/・adapters/)は 0 行。この便の記録(fixtures/xbrl/tanshin_self/ の 2 つ)は本番の後に届ける
    "measure/xbrl_tanshin_self_inject_2026-11-14.py",
    # 2026-11-15: KAM(有価証券報告書の監査報告書の「監査上の主要な検討事項」の文を、同じ有報の fact で確かめる。封 docs/XBRL_KAM_SEAL_2026-11-15.md 497a4661)の script 1 本。
    # TSS・2026-11-09 の便の関数を呼ぶ(書き写さない)。engine(core/・adapters/)は 0 行。この便の記録(fixtures/xbrl/kam/ の 3 つ)は本番の後に届ける
    "measure/xbrl_kam_2026-11-15.py",
    # 2026-11-16: YS(有価証券報告書の「経営者による分析」以外の 3 つの節 = 研究開発活動・設備投資等の概要・配当政策の文を、同じ有報の fact で確かめる。封 docs/XBRL_YUHO_SECTIONS_SEAL_2026-11-16.md e7754d70)の script 1 本。
    # KAM の script・TSS・2026-11-09 の便の関数を呼ぶ(書き写さない)。engine(core/・adapters/)は 0 行。この便の記録(fixtures/xbrl/yuho_sections/ の 3 つ)は本番の後に届ける
    "measure/xbrl_yuho_sections_2026-11-16.py",
    # 2026-11-14: TSS の第 2 便の記録 3 つ(中間 150 本を期の名前を写して判定した行・「値が違う」のうち近い行・読んだ 200 行の型。fixtures/xbrl/tanshin_self/)。script が書いた数と、司令塔(AI の席)が付けた型。
    # 会社名・証券コード・文・値を持たない。結果の門 tests/measure/test_xbrl_tanshin_self2_result.py が縛る。engine(core/・adapters/)は 0 行
    "fixtures/xbrl/tanshin_self/states_interim_2026-11-14.json", "fixtures/xbrl/tanshin_self/near_2026-11-14.json", "fixtures/xbrl/tanshin_self/near_types_2026-11-14.json",
    # 2026-11-14: TSS の便 1b の記録 2 つ(注入の 3,726 行と本ごとの数え・配線・集計・覆い / 通した行を読んだ札。fixtures/xbrl/tanshin_self/)。script が書いた数と、司令塔(AI の席)が付けた札。
    # 会社名・証券コード・文・値を持たない。結果の門 tests/measure/test_xbrl_tanshin_self_inject_result.py が縛る。engine(core/・adapters/)は 0 行
    "fixtures/xbrl/tanshin_self/inject_2026-11-14.json", "fixtures/xbrl/tanshin_self/inject_passed_types_2026-11-14.json",
    # 2026-11-15: KAM の記録 3 つ(母集団 201 本の表 / 201 本の切り出しと判定の行 / 読んだ 133 行の型。fixtures/xbrl/kam/)。script が書いた数と、司令塔(AI の席)が付けた型。
    # 会社名・証券コード・文・値を持たない。結果の門 tests/measure/test_xbrl_kam_result.py が縛る。engine(core/・adapters/)は 0 行
    "fixtures/xbrl/kam/population_2026-11-15.json", "fixtures/xbrl/kam/states_2026-11-15.json", "fixtures/xbrl/kam/read_types_2026-11-15.json",
    # 2026-11-16: YS の記録 3 つ(母集団 201 本の表 / 201 本 × 3 つの節の切り出しと判定の行 / 読んだ 169 行の型。fixtures/xbrl/yuho_sections/)。script が書いた数と、司令塔(AI の席)が付けた型。
    # 会社名・証券コード・文・値を持たない。結果の門 tests/measure/test_xbrl_yuho_sections_result.py が縛る。engine(core/・adapters/)は 0 行
    "fixtures/xbrl/yuho_sections/population_2026-11-16.json", "fixtures/xbrl/yuho_sections/states_2026-11-16.json", "fixtures/xbrl/yuho_sections/read_types_2026-11-16.json",
    # 2026-11-17: AT(便をまたいだ集計。封 docs/XBRL_ATTR_TALLY_SEAL_2026-11-17.md 52f3a228)の script 1 本と記録 1 つ(fixtures/xbrl/attr_tally/)。
    # 既に在る型の読みの記録 5 つを sha256 で確かめて数え直すだけの標準ライブラリだけの script で、engine(core/・adapters/)・材料の本・前の便の script を読まない。記録は数だけで、行・文・値・本の番号を持たない
    "measure/xbrl_attr_tally_2026-11-17.py", "fixtures/xbrl/attr_tally/tally_2026-11-17.json",
    # 2026-11-17: PS(止めた行にサマリーの予想の fact という当てる先が在るか。封 docs/XBRL_PLAN_SOURCE_SEAL_2026-11-17.md a080ce5f・追記 §7 5b38862e)の script 1 本と記録(fixtures/xbrl/plan_source/)。
    # 材料は TSS の置き場の ZIP 400 本(新しく取らない)・engine(core/・adapters/)は 0 行。記録は数と、P・W の行の [本の #, 文の番号, 位置, 組, 札] だけで、文・span・値・要素名・context の字・会社名・証券コード・docID を持たない
    "measure/xbrl_plan_source_2026-11-17.py", "fixtures/xbrl/plan_source/states_2026-11-17.json",
    # 2026-11-17(2): PS の読みの軸の記録 1 つ(fixtures/xbrl/plan_source/read_types_2026-11-17.json。読みの軸の封 docs/XBRL_PLAN_SOURCE_READ_AXES_SEAL_2026-11-17.md 06d7b8a7 §6)。
    # 標本の行 [標本の番号, 本の #, 文の番号, 位置, 組, 値の軸, 身元の 5 字, 字] と数だけで、文・span・値・要素名・context の字・会社名・証券コード・docID を持たない。新しい取得 0・engine は 0 行
    "fixtures/xbrl/plan_source/read_types_2026-11-17.json",
    # 2026-11-17(3): NR(engine の inline XBRL の読み取りが自己閉じの空の欄を次の fact まで読む欠陥は過去の便の数にどれだけ効いたか。封 docs/XBRL_NIL_READ_SEAL_2026-11-17.md 720a473d)の script 1 本と記録(fixtures/xbrl/nil_read/)。
    # 材料は TSS の置き場の ZIP 400 本(新しく取らない)と ~/.cache/audit-core/ の ZIP の棚卸し・engine(core/・adapters/)は 0 行。記録は数と、行 [本の #, 文の番号, 位置, そのままの state, 直した入力の state, reason が同じか]・本ごとの数だけで、文・span・値・要素名・context の字・会社名・証券コード・docID を持たない
    "measure/xbrl_nil_read_2026-11-17.py", "fixtures/xbrl/nil_read/states_2026-11-17.json",
    # 2026-11-17(4): NRE(engine の inline XBRL の読み取りが自己閉じの空の欄を始まりの tag と読まないようにする直し。封 docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md 36ca78f1)の script 1 本と記録(fixtures/xbrl/nil_read_engine/)。
    # 材料は NR と同じ(TSS の置き場の ZIP 400 本・~/.cache/audit-core/ の ZIP。新しく取らない)。engine の変更は instance.py の式 1 行(挿入 1・削除 1)だけで、届けではなく封が宣言した遷移。記録は数と行 [本の #, 文の番号, 位置, state, 同じか, state]・本ごとの数だけで、文・span・値・要素名・context の字・会社名・証券コード・docID を持たない
    "measure/xbrl_nil_read_engine_2026-11-17.py", "fixtures/xbrl/nil_read_engine/states_2026-11-17.json",
    # 2026-11-18(5): RT(TSS の系列 = 第 1 便・第 2 便・便 1b・便 PS を、直した engine で取り直して前の記録と並べる。封 docs/XBRL_TSS_RETAKE_SEAL_2026-11-18.md b4c08fc6)の script 1 本と記録(fixtures/xbrl/tss_retake/)。
    # 材料は TSS の置き場の ZIP 400 本(新しく取らない)・engine(core/・adapters/)は 0 行・前の 4 便の script と記録は 1 byte も変えない(sha256 を門が縛る)。記録は数と、変わった行の [本の #, 文の番号, 位置, state] 等の記号だけで、文・span・値・要素名・context の字・会社名・証券コード・docID・金額を持たない
    "measure/xbrl_tss_retake_2026-11-18.py", "fixtures/xbrl/tss_retake/retake_2026-11-18.json",
    # 2026-11-18(6): SE(サマリーを engine に渡したときに動く行と、engine の語彙が予想の枠の fact に届くか。封 docs/XBRL_SUMMARY_ENGINE_SEAL_2026-11-18.md fabd87ba)の script 1 本と記録(fixtures/xbrl/summary_engine/)。
    # 材料は TSS の置き場の ZIP 400 本(新しく取らない)・engine(core/・adapters/)は 0 行・前の便の script と記録は 1 byte も変えない(sha256 を門が縛る)。記録は数と、鍵 [本の #, 文の番号, 位置] と札だけで、文・値・要素名・主語の語・枠の id・会社名・証券コード・docID・金額を持たない
    "measure/xbrl_summary_engine_2026-11-18.py", "fixtures/xbrl/summary_engine/states_2026-11-18.json",
    # 2026-11-19(1): SC(文は一部分を言うのに全体の fact に結んだ行を文の字で止める後付けの規則が、取り違えをどれだけ止め、正しい結びをどれだけ減らすか。封 docs/XBRL_SCOPE_COND_SEAL_2026-11-19.md 5b77133b)の script 1 本と記録(fixtures/xbrl/scope_cond/)。
    # 材料は TSS の置き場の ZIP 400 本と KAM・YS の 3 つの folder の ZIP 201 本(新しく取らない)・engine(core/・adapters/)は 0 行・前の便の script と記録は 1 byte も変えない(sha256 を門が縛る)。記録は数と、鍵 [便, 本の #, 文の種類か節, 文の番号, 位置] と state・member が空か・段ごとの当たりの類だけで、文・値・要素名・枠の id・pointer の字・主語の語・会社名・証券コード・docID・金額を持たない
    "measure/xbrl_scope_cond_2026-11-19.py", "fixtures/xbrl/scope_cond/stops_2026-11-19.json",
    # 2026-11-19(2): PA(実績の数でないのに実績の fact に結んだ行を文の字で止める後付けの規則が、取り違えをどれだけ止め、正しい結びをどれだけ減らすか。封 docs/XBRL_PLAN_ATTR_SEAL_2026-11-19.md e69b733c)の script 1 本と記録(fixtures/xbrl/plan_attr/)。
    # 材料は TSS の置き場の ZIP 400 本と KAM・YS の 3 つの folder の ZIP 201 本(新しく取らない)・engine(core/・adapters/)は 0 行・前の便の script(便 SC のものを含む)と記録は 1 byte も変えない(sha256 を門が縛る)。記録は数と、鍵 [便, 本の #, 文の種類か節, 文の番号, 位置] と state・段ごとの当たりの類だけで、文・値・要素名・枠の id・pointer の字・主語の語・会社名・証券コード・docID・金額を持たない
    "measure/xbrl_plan_attr_2026-11-19.py", "fixtures/xbrl/plan_attr/stops_2026-11-19.json",
    # 2026-11-19(3): LX(文の字だけを読んだ LLM の席の答え(範囲・性質)で結んだ行を止める後付けの規則が、語の表の規則と比べて、取り違えをどれだけ止め、正しい結びをどれだけ減らすか。封 docs/XBRL_LLM_EXTRACT_SEAL_2026-11-19.md 198961e6)の script 1 本と記録(fixtures/xbrl/llm_extract/。記録は本番が全部済んだ 2026-11-20 に書かれた)。
    # 材料は TSS の置き場の ZIP 400 本と KAM・YS の 3 つの folder の ZIP 201 本(新しく取らない)・engine(core/・adapters/)は 0 行・前の便の script(便 SC・便 PA を含む)と記録は 1 byte も変えない(sha256 を門が縛る)。有料の script(--dry-run・--check は鍵も通信も無い。鍵は環境変数だけから読み記録に出さない)。記録は数と、鍵 [便, 本の #, 文の種類か節, 文の番号, 位置] と state・member が空か・席ごとの答えの語・指示文の sha256・呼び出しの数だけで、文・見出し・値・要素名・枠の id・pointer の字・主語の語・会社名・証券コード・docID・金額・席の返した text を持たない
    "measure/xbrl_llm_extract_2026-11-19.py", "fixtures/xbrl/llm_extract/answers_2026-11-19.json",
    # 2026-11-21: CT0(治験の公開データで、いまの engine の数の読み取りが英語の論文の要旨の数をどれだけ拾うか。封 docs/CTGOV_WALL_SEAL_2026-11-21.md 9e41971b)の script 1 本。
    # 材料は新しく取る(ClinicalTrials.gov・NCBI。置き場は repo の外)・engine(core/・adapters/)は 0 行・前の便の script と記録は読まない。記録 fixtures/ctgov/wall_2026-11-21.json はこの門が見る path の外(fixtures/ctgov/)。
    "measure/ctgov_wall_2026-11-21.py",
    # 2026-11-21: XG0(有価証券報告書の計算書の行で、行の字と標準タクソノミの表だけで要素が 1 つに決まる行はどれだけか。封 docs/XBRL_TAG_WALL_SEAL_2026-11-21.md 3374e504)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本と標準タクソノミのラベルの file(新しく取らない)・engine(core/・adapters/)は 0 行・前の便の script と記録は読まない。記録 fixtures/xbrl/cd8/tag_wall_2026-11-21.json は記録の commit で足す(script だけここで届ける)。
    "measure/xbrl_tag_wall_2026-11-21.py",
    # 2026-11-21: XG0 の記録 1 本(script 5305f855 を 1 回走らせて書いた。67 本の数だけ。docID・会社の名・EDINET コード・行の字・要素の名は持たない)。
    "fixtures/xbrl/cd8/tag_wall_2026-11-21.json",
    # 2026-11-21: XG1(XG0 で候補が 2 つ以上だった行を、数を持てる要素・計算書の種類・業種の科目の一覧で絞る。封 docs/XBRL_TAG_NARROW_SEAL_2026-11-21.md 1bda1997)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本・標準ラベルの file・標準タクソノミの zip 1 本(置き場は repo の外)・engine(core/・adapters/)は 0 行・便 XG0 の script は importlib で読み関数を呼ぶ。記録 fixtures/xbrl/cd8/tag_narrow_2026-11-21.json は記録の commit で足す(script だけここで届ける)。
    "measure/xbrl_tag_narrow_2026-11-21.py",
    # 2026-11-21: XG1 の記録 1 本(script 762d361e を 1 回走らせて書いた。67 本の数だけ。docID・会社の名・EDINET コード・行の字・見出しの字・業種の値・要素の名は持たない)。
    "fixtures/xbrl/cd8/tag_narrow_2026-11-21.json",
    # 便 XV0 の記録(記録の commit で足す)
    "fixtures/xbrl/cd8/edinet_validate_2026-11-21.json",
    # 2026-11-21: XV0(公開の検査の道具 Arelle の EDINET の規則を、提出済みの有報 67 本に掛ける。封 docs/XBRL_EDINET_VALIDATE_SEAL_2026-11-21.md 1bda1997)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本(置き場は変えない)と repo の外に置く道具の venv 2 つ・engine(core/・adapters/)は 0 行・便 XG0 の script は importlib で読み関数を呼ぶ。記録 fixtures/xbrl/cd8/edinet_validate_2026-11-21.json は記録の commit で足す(script だけここで届ける)。
    "measure/xbrl_edinet_validate_2026-11-21.py",
    # 2026-11-21: XB0(受理済みの有報の inline XBRL を、タグを剥がした本文と fact の表から組み直す。封 docs/XBRL_INLINE_BUILD_SEAL_2026-11-21.md 9c528c49)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本(置き場は変えない)と repo の外に置く道具の venv・engine(core/・adapters/)は 0 行・便 XG0・XV0 の script は importlib で読み関数を呼ぶ。記録は記録の commit で足す(script だけここで届ける)。
    "measure/xbrl_inline_build_2026-11-21.py",
    # 2026-11-21: XB0 の記録 1 本(script 82b44aef を 1 回走らせて書いた。67 本の数だけ。docID・会社の名・EDINET コード・file の名・fact の値・要素の名・指摘の行の本文は持たない)。
    "fixtures/xbrl/cd8/inline_build_2026-11-21.json",
    # 2026-11-22: XT0 の記録 1 本(script 9417a869 を 1 回走らせて書いた。67 本の数だけ。docID・会社の名・EDINET コード・file の名・fact の値・要素の名・ラベルの字・role の URI・指摘の行の本文は持たない)。
    "fixtures/xbrl/cd8/taxonomy_build_2026-11-22.json",
    # 2026-11-22: XT0(受理済みの有報の提出者別タクソノミ(.xsd と linkbase 5 つ)を、中身を読んだ表から自前の部品で組み直す。封 docs/XBRL_TAXONOMY_BUILD_SEAL_2026-11-22.md dae701b0)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本(置き場は変えない)と repo の外に置く道具の venv・engine(core/・adapters/)は 0 行・便 XG0・XV0・XB0 の script は importlib で読み関数を呼ぶ。記録は記録の commit で足す(script だけここで届ける)。
    "measure/xbrl_taxonomy_build_2026-11-22.py",
    # 2026-11-22: XP0(受理済みの有報の公開用の file を原稿の folder に落とし、folder だけを読む別の process の命令で htm・xsd・linkbase を組み直す。封 docs/XBRL_PACK_BUILD_SEAL_2026-11-22.md c03a3348)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本(置き場は変えない)と repo の外に置く道具の venv・engine(core/・adapters/)は 0 行・便 XG0・XV0・XB0・XT0 の script は importlib で読み関数を呼ぶ。記録は記録の commit で足す(script だけここで届ける)。
    "measure/xbrl_pack_build_2026-11-22.py",
    # 2026-11-22: XP0 の記録 1 本(script 465d0bc7 を 1 回走らせて書いた。67 本の数だけ。docID・会社の名・EDINET コード・file の名・fact の値・要素の名・ラベルの字・role の URI・指摘の行の本文は持たない)。
    "fixtures/xbrl/cd8/pack_build_2026-11-22.json",
    # 2026-11-22: XA0(受理済みの有報の数の fact の属性が、表の行ごと・列ごとの決めでどれだけ決まるかを数える。封 docs/XBRL_SHEET_WALL_SEAL_2026-11-22.md 3062223e)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本(置き場は変えない)・engine(core/・adapters/)は 0 行・道具(Arelle)は呼ばない・便 XG0・XB0 の script は importlib で読み関数を呼ぶ。記録は記録の commit で足した。
    "measure/xbrl_sheet_wall_2026-11-22.py",
    # 2026-11-22: XA0 の記録 1 本(script f60f374b を 1 回走らせて書いた。67 本の数だけ。docID・会社の名・EDINET コード・file の名・fact の値・要素の名・文脈の名・表の字は持たない)。
    "fixtures/xbrl/cd8/sheet_wall_2026-11-22.json",
    # 2026-11-22: XA1(行・列の紙に収まらなかった fact の文脈を、終わりの日と member の組に分けて別々の線で決めると、どれだけ収まるか。封 docs/XBRL_SHEET_CONTEXT_SEAL_2026-11-22.md d46f92aa)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本(置き場は変えない)・engine(core/・adapters/)は 0 行・道具(Arelle)は呼ばない・便 XA0 の script は importlib で読み関数を呼ぶ。記録は記録の commit で足した。
    "measure/xbrl_sheet_context_2026-11-22.py",
    # 2026-11-22: XA1 の記録 1 本(script 4f836c94 を 1 回走らせて書いた。67 本の数だけ。docID・会社の名・EDINET コード・file の名・要素の名・文脈の名・member の名・日付・表の字は持たない)。
    "fixtures/xbrl/cd8/sheet_context_2026-11-22.json",
    # 2026-11-22: XS0(行・列の紙から数の fact の属性を作り直し、便 XP0 の組む命令で包みを組むと、道具が読む fact は元と同じになるか。封 docs/XBRL_SHEET_BUILD_SEAL_2026-11-22.md 483e3e93)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本(置き場は変えない)・engine(core/・adapters/)は 0 行・道具(Arelle)は便 XP0 の組む命令を通して呼ぶ・前の便の script は importlib で読み関数を呼ぶ。記録は記録の commit で足した。
    "measure/xbrl_sheet_build_2026-11-22.py",
    # 2026-11-22: XS0 の記録 1 本(script 6d82a612 を 1 回走らせて書いた。67 本の数だけ。docID・会社の名・EDINET コード・file の名・fact の値・要素の名・文脈の名・member の名・日付・表の字・紙の中身・行の字は持たない)。
    "fixtures/xbrl/cd8/sheet_build_2026-11-22.json",
    # 2026-11-22: XH0(数の置き場を表の cell の字から決め、文脈と単位の定義を紙から作って包みを組むと、道具が読む fact は元と同じになるか。封 docs/XBRL_PLACE_CONTEXT_BUILD_SEAL_2026-11-22.md 97eff9a2)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本(置き場は変えない)・engine(core/・adapters/)は 0 行・道具(Arelle)は便 XP0 の組む命令を通して呼ぶ・前の便の script は importlib で読み関数を呼ぶ。記録は記録の commit で足した。
    "measure/xbrl_place_context_build_2026-11-22.py",
    # 2026-11-22: XH0 の記録 1 本(script 2761b2dd を 1 回走らせて書いた。67 本の書類ごとの数と合計。docID・会社の名・EDINET コード・file の名・要素の名は持たない)。
    "fixtures/xbrl/cd8/place_context_build_2026-11-22.json",
    # 2026-11-22: XD0(候補が残る行の要素を LLM の席に選ばせ、2 席の一致で通す測定。有料。封 docs/XBRL_AI_TAG_PICK_SEAL_2026-11-22.md 7bb4fa24)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本(置き場は変えない)・engine(core/・adapters/)は 0 行・便 XG1 の script は importlib で読み関数を呼ぶ。有料の入口(--trial・--run)は司令塔だけが走らせた。記録は記録の commit で足した。
    "measure/xbrl_ai_tag_pick_2026-11-22.py",
    # 2026-11-22: XD0 の記録 1 本(script f119b80c を本番 1 回走らせて書いた。394 行の席ごとの札・呼び出しの数と token と費用。docID・会社の名・EDINET コード・行の字・要素の名・席の返事の字・鍵は持たない)。
    "fixtures/xbrl/cd8/ai_tag_pick_2026-11-22.json",
    # 2026-11-22: XY0(同じ会社の前の年の提出書類の「行の字 → 要素」を今年の行に当てる測定。0 USD。封 docs/XBRL_PRIOR_YEAR_DRAFT_SEAL_2026-11-22.md ce70f71f)の script 1 本。
    # 材料は置き場の有価証券報告書の zip(今年の側 67 本と前の年の側の組 63。置き場は変えない)・engine(core/・adapters/)は 0 行・便 XG0・XG1 の script は importlib で読み関数を呼ぶ。通信しない。記録は記録の commit で足した。
    "measure/xbrl_prior_year_draft_2026-11-22.py",
    # 2026-11-22: XY0 の記録 1 本(script 150c7fe6 を本番 1 回走らせて書いた。63 組の書類ごと・段ごとの類別の数と合計。docID・会社の名・EDINET コード・file の名・期末の日付・行の字・要素の名は持たない)。
    "fixtures/xbrl/cd8/prior_year_draft_2026-11-22.json",
    # 2026-11-22: XZ0(同じ会社の前の年の提出書類の「表の中の置き場 → 数の fact の属性」を今年の下書きに使う測定。0 USD。封 docs/XBRL_PRIOR_YEAR_FACT_DRAFT_SEAL_2026-11-22.md 4ee140d2)の script 1 本。
    # 材料は置き場の有価証券報告書の zip(今年の側 67 本と前の年の側の組 63。置き場は変えない)・engine(core/・adapters/)は 0 行・便 XG0・XG1・XY0 の script は importlib で読み関数を呼ぶ。通信しない。記録は記録の commit で足した。
    "measure/xbrl_prior_year_fact_draft_2026-11-22.py",
    # 2026-11-22: XZ0 の記録 1 本(script 77662224 を本番 1 回走らせて書いた。63 組の書類ごと・束と段ごとの類別の数と合計。docID・会社の名・EDINET コード・file の名・行の字・見出しの字・要素の名・文脈の名・単位の名は持たない)。
    "fixtures/xbrl/cd8/prior_year_fact_draft_2026-11-22.json",
    # 2026-11-22: XZ1(前の年の下書きが黙って違う属性を付ける fact を、行の順で番号を振り直す規則と表の頭の字の守りで直す・止める測定。0 USD。封 docs/XBRL_PRIOR_YEAR_FACT_GUARD_SEAL_2026-11-22.md 2079af62)の script 1 本。
    # 材料は置き場の有価証券報告書の zip(今年の側 67 本と前の年の側の組 63。置き場は変えない)・engine(core/・adapters/)は 0 行・便 XG0・XG1・XY0・XZ0 の script は importlib で読み関数を呼ぶ。通信しない。記録は記録の commit で足した。
    "measure/xbrl_prior_year_fact_guard_2026-11-22.py",
    # 2026-11-22: XZ1 の記録 1 本(script d6a18d51 を本番 1 回走らせて書いた。63 組の書類ごと・段ごとの類別の数・段の間の移り・止めた fact の類別・番号の列を使った fact・違う属性の数・旗と、60 組・3 組・63 組の合計。docID・会社の名・EDINET コード・file の名・行の字・見出しの字・要素の名・文脈の名・形の字は持たない)。
    "fixtures/xbrl/cd8/prior_year_fact_guard_2026-11-22.json",
    # 2026-11-22: XM0(機械の側が決めた入力の型(第 0 版)と対応表だけから、fact の属性と文脈・単位の定義を作る測定。0 USD。封 docs/XBRL_INPUT_TYPE_SEAL_2026-11-22.md 34afe495)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本(置き場は変えない)と repo の外に置く道具の venv・engine(core/・adapters/)は 0 行・便 XG0・XV0・XB0・XT0・XP0 の script は importlib で読み関数を呼ぶ。記録は記録の commit で足す(script だけここで届ける)。
    "measure/xbrl_input_type_2026-11-22.py",
    # 2026-11-22: XM0 の記録 1 本(script 6f719410 で書いた。67 本の書類ごと・型に入った fact・型の外の fact の理由ごとの数・型の行・対応表の行・作った定義・比べ方 1 と 2・混ぜ物・表示の字の検査と、開発の 5 本・本番だけの 62 本・全部の合計。docID・会社の名・EDINET コード・file の名・値・要素の名・文脈の名・日付は持たない)。
    "fixtures/xbrl/cd8/input_type_2026-11-22.json",
    # 2026-11-22: XK0(同じ会社の前の年の型と対応表が今年の型にどれだけ持ち越せるかを数える測定。0 USD。封 docs/XBRL_TYPE_CARRYOVER_SEAL_2026-11-22.md 1fc4c736)の script 1 本。
    # 材料は置き場の有価証券報告書の zip(今年の側 67 本と前の年の側の組 63。置き場は変えない)・engine(core/・adapters/)は 0 行・便 XM0・XY0 の script は importlib で読み関数を呼ぶ。通信しない。記録は記録の commit で足す(script だけここで届ける)。
    "measure/xbrl_type_carryover_2026-11-22.py",
    # 2026-11-22: XK0 の記録 1 本(script aaeeb21c で書いた。63 組の組ごと・対応表の名の持ち越し・名が足りる行・期の区分・同じ行と中身の分け・枠が在る行・逆向き・型の外の fact の理由ごとの数と、訓練の 3 組・判定の 60 組・全部の合計。docID・会社の名・EDINET コード・file の名・値・要素の名・文脈の名・日付は持たない)。
    "fixtures/xbrl/cd8/type_carryover_2026-11-22.json",
    # 2026-11-22: XE0(会社が Excel で出すとしたら、XBRL の言葉を書かない欄だけで今年の型はどれだけ決まり・黙って違い・止まるかを数える測定。0 USD。封 docs/XBRL_COMPANY_EXCEL_SEAL_2026-11-22.md aec0496d)の script 1 本。
    # 材料は置き場の有価証券報告書の zip(今年の側 67 本と前の年の側の組 63。置き場は変えない)・engine(core/・adapters/)は 0 行・便 XG1・XM0・XY0・XZ0・XZ1 の script は importlib で読み関数を呼ぶ。通信しない。xlsx は一時の folder にだけ書く。記録は記録の commit で足す(script だけここで届ける)。
    "measure/xbrl_company_excel_2026-11-22.py",
    # 2026-11-23: XE0 の記録 1 本(script 7cc388be で書いた。63 組の組ごと・行の中の数の fact・書かなかった fact の理由ごとの数・決めて全部同じ・決めたが違う(欄ごと)・止めた(理由ごと)・守りごとの正しかった止め・場面ごとの数・無くなった行と、訓練の 3 組・判定の 60 組・全部の合計。docID・会社の名・EDINET コード・file の名・値・要素の名・文脈の名・行の字・日付は持たない)。
    "fixtures/xbrl/cd8/company_excel_2026-11-22.json",
    # 2026-11-23: XJ0(入力の型の第 1 版を字で決め、会社の AI に渡す指示書と、型どおりでない file を理由つきで断る受け口の検査を作る測定。0 USD。封 docs/XBRL_INPUT_TYPE_V1_SEAL_2026-11-23.md 8f3ec76b)の script 1 本。
    # 材料は置き場の有価証券報告書の zip 67 本(置き場は変えない)と repo の外に置く道具の venv・engine(core/・adapters/)は 0 行・便 XM0 の script は importlib で読み関数を呼ぶ(受け口の検査は別の process で型の file と辞書だけを読む)。記録は記録の commit で足す(script だけここで届ける)。
    "measure/xbrl_input_type_v1_2026-11-23.py",
    # 2026-11-23: XJ0 の記録 1 本(script 48cf7135 で書いた。67 本の書類ごと・対象の fact・型に入った fact・型の外の fact(理由ごと)・型の行・名の数・受け口の断り(規則ごと)・比べ方 1・比べ方 2・壊し方 44 通りと変え方 6 通りの数と、開発の 5 本・残りの 62 本の集計。
    # docID・会社の名・EDINET コード・file の名・値・要素の名・文脈の名・行の字・日付は持たない)。
    "fixtures/xbrl/cd8/input_type_v1_2026-11-23.json",
    # 2026-11-23: UM0(開示に限らない共通構造(材料の型 第 0 版)で、資料の指定から資料の生成までの 7 段を 1 本につなぐ測定。0 USD。封 docs/UNIVERSAL_MATERIAL_SEAL_2026-11-23.md 4ef1368c)の script 2 本(素材を作る側と確かめる側)。
    # XBRL・EDINET・開示の書類・置き場・道具の venv は 1 つも使わない。engine(core/・adapters/)は 0 行。素材は作り物で repo に置かない(scratchpad)。記録は記録の commit で足す(script だけここで届ける)。
    "measure/universal_source_gen_2026-11-23.py", "measure/universal_check_2026-11-23.py",
    # 2026-11-23: UM2(別の席が形を決めた架空の会計ソフトの file 一式から、資料の指定から人が読む版の資料までの 7 段を 2 期ぶん通す測定。0 USD。封 docs/UNIVERSAL_THROUGH_SEAL_2026-11-23.md 9ff5af9e)の script 2 本(確かめる側と答えを知っている側)。
    # XBRL・EDINET・開示の書類・置き場・道具の venv は 1 つも使わない。engine(core/・adapters/)は 0 行。素材・正解・材料の束・置き場・資料は repo に置かない(scratchpad)。記録は記録の commit で足す(script だけここで届ける)。
    "measure/universal_through_check_2026-11-23.py", "measure/universal_through_tally_2026-11-23.py",
    # 2026-11-24: UM3(UM2 と同じ素材を型も検査も持たない AI の席に資料まで作らせ、作る過程を数える測定。0 USD。封 docs/UNIVERSAL_PROCESS_SEAL_2026-11-24.md 6c4457fe)の script 1 本(席の folder を作る・会話の記録を数える・行ごとに正解と照合する・抜き書きを書く)。
    # XBRL・EDINET・開示の書類・置き場・道具の venv は 1 つも使わない。engine(core/・adapters/)は 0 行。素材・正解・席の folder・会話の記録・抜き書きは repo に置かない(scratchpad)。記録は記録の commit で足す(script だけここで届ける)。
    "measure/universal_process_tally_2026-11-24.py",
)
#: この便が読み込む前の便の script・読むだけの記録(封の commit の blob と byte が同じでなければならない)
READ_ONLY_RELS = (
    "measure/xbrl_pbind_2026-11-06.py", "measure/xbrl_rmix_2026-11-04.py", "measure/xbrl_rmix_regress97_2026-11-04.py", "measure/xbrl_pswap_idmap_2026-11-06.py", "measure/xbrl_pswap_2026-11-06.py",
    "measure/xbrl_numfix_2026-11-04.py", "measure/xbrl_p28_regress97_2026-11-02.py", "measure/xbrl_aiforms_gen_2026-11-03.py", "measure/xbrl_aiforms_run_2026-11-03.py",
    "adapters/xbrl/verify_document.py", "adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py",
    "fixtures/xbrl/aiforms/labels_2026-11-03.json", "fixtures/xbrl/aiforms/f5_labels_2026-11-03.json", "fixtures/xbrl/numfix/ai200_2026-11-04.json")
RESERVED_PREFIXES = SGR.RESERVED_PREFIXES
DOCID_RE = SGR.DOCID_RE
PRED_IDS = tuple("L-%d" % i for i in range(0, 5))
EYE = u"人の" + u"目"                                  # 札を言い表すのに使わない語(否定の言い方だけ許す)
#: 前の便の関数(この script は同名の関数を定義せず、前の便の module の関数を呼ぶ)。(module の別名, 関数名)
REUSED_FUNCS = (("RM", "load_jobs"), ("RM", "caches_all"), ("RM", "load_labels"), ("NF", "map_pool"), ("GEN", "caches_snapshot"), ("GEN", "read_zip"), ("RUN", "read_text"), ("RUN", "write_record"),
                ("D", "record_key_leaks"))
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"札は P28E の (本, claim の id) で結ぶ",
    u"数の claim の鍵は `(文の番号, 文の中の位置)`",
    u"各 profile で 200 本に `verify_document` を 1 回ずつ新しく走らせ",
    u"同じ鍵の P28E の数の claim が在れば「既存の行」、無ければ「新しい行」",
    u"既存の行は、同じ鍵の P28E の行の札を持つ。新しい行は「札なし」",
    u"「通した」= GROUNDED。「止めた」= GROUNDED 以外の 3 つ",
    u"札 偽の行を通した率は「偽の行の GROUNDED ÷ 偽の行」",
    u"判定(採用 / 不採用)は無い便",
    u"文の claim(`kind == text`)は札が無い作りなので母集団に入れない",
    u"新しい生成・新しい札付けはしない(既存の札だけを使う)",
    u"P28E の数の claim 10,371 行は全部に札がある(真 9,590・偽 368・判定不能 413)",
    u"新しく claim になった行 6,231 には札が無い",
    u"札の無い行だけだと P33E 4,646 / 6,231",
    u"札は盲検の LLM の席の読みで、人の目ではない。正解でもない",
    u"札の無い行(P29E 以降に新しく claim になった 6,231 行)の正しさは測らない",
)
#: 封 §2 の L-0〜L-2 の数(封の字を門が読み、ここに留めた値と照らす)
EXPECT_PIN = collections.OrderedDict([
    ("L-0", 10371),
    ("L-1", collections.OrderedDict([("P28E", (10371, 10371)), ("P29E", (16588, 10357)), ("P30E", (16588, 10357)), ("P32E", (16588, 10357)), ("P33E", (16588, 10357))])),
    ("L-2", collections.OrderedDict([("P28E", (None, 6597)), ("P29E", (11137, 6586)), ("P30E", (11260, 6696)), ("P32E", (11259, 6695)), ("P33E", (11625, 6979))]))])


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. 封の字
def seal_paths(seal):
    u"""封 §4 に書かれた ``measure/...py``・``tests/measure/test_xbrl_labelonly_*.py``・``docs/XBRL_LABEL_ONLY_RATES_RESULT_...md`` の path。無ければ空。"""
    try:
        sec4 = seal[seal.index("## §4"):seal.index("## §5")]
    except ValueError:
        return []
    return re.findall(r"`((?:measure|tests/measure|docs)/[A-Za-z0-9_./-]*?(?:\.py|\.md))`", sec4)


def seal_record_path(seal):
    u"""封 §0-2 の 5 の新しい記録の path(``fixtures/xbrl/labelonly/<名前>.json``)。ちょうど 1 つ。"""
    try:
        sec = seal[seal.index("### §0-2"):seal.index("## §1")]
    except ValueError:
        return []
    return re.findall(r"`(fixtures/xbrl/labelonly/[a-z0-9_.-]+\.json)`", sec)


def seal_problems(seal):
    out = []
    try:
        ids = SGR.table_ids(seal, "## §2", "## §3", r"^\| (L-\d+) \| (.*) \|$")
        sec = seal[seal.index("## §2"):seal.index("## §3")]
        seal[seal.index("## §4"):seal.index("## §5")]
        seal[seal.index("## §6"):]
    except ValueError:
        return [u"封の節(§0-2・§1・§2・§3・§4・§5・§6)が揃っていない"]
    if ids != list(PRED_IDS):
        out.append(u"封 §2 の表が L-0〜L-4 の 5 行でない: %s" % ids)
    for line in sec.splitlines():
        m = re.match(r"^\| (L-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            if len(cells) < 3 or any(not c.strip() for c in cells[:3]):
                out.append(u"封 §2 の %s の欄(欄・照合 / 予測・外れ方)が埋まっていない" % m.group(1))
    paths = seal_paths(seal)
    for rel in SCRIPT_RELS + GATE_RELS + (DOC_REL,):
        if rel not in paths:
            out.append(u"封 §4 に path が無い: %s" % rel)
    if seal_record_path(seal) != [RECORD_REL]:
        out.append(u"封 §0-2 の記録の path が script・門の持つ 1 つと違う: %s" % seal_record_path(seal))
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に決めの要点の字が無い: %s" % ph)
    return out


# ---------------------------------------------------------------- 2. 封の字と script の定数
def script_problems(seal, sc=None):
    u"""封の字と script の定数が同じか。sc = script の module(試験が壊した写しを渡す)。"""
    sc = sc or SC
    out = []
    if sc.SEAL_REL != SEAL_REL or sc.SEAL_COMMIT != SEAL_COMMIT_SHORT:
        out.append(u"封の path・commit が違う")
    if tuple(sc.PROFILES) != ("P28E", "P29E", "P30E", "P32E", "P33E") or sc.BASE != "P28E":
        out.append(u"profile が (P28E, P29E, P30E, P32E, P33E) でないか土台が P28E でない")
    if (sc.EXISTING, sc.NEWROW, sc.L_NONE, tuple(sc.LABEL_WORDS)) != (u"既存", u"新", u"なし", (u"真", u"偽", u"判定不能")):
        out.append(u"既存 / 新 / 札の語が違う")
    if sc.G != "GROUNDED":
        out.append(u"通した = GROUNDED でない")
    if [sc.REC_REL] != seal_record_path(seal) or sc.REC_REL != RECORD_REL:
        out.append(u"記録の path が封 §0-2 と違う")
    if sc.DOC_REL != DOC_REL or sc.SCRIPT_REL != SCRIPT_RELS[0] or DOC_REL not in seal_paths(seal) or sc.SCRIPT_REL not in seal_paths(seal):
        out.append(u"結果の文書・script の path が封 §4 と違う")
    try:
        got = sc.seal_expect(seal)
    except Exception as e:                                   # noqa: BLE001  壊れた封は読めない = 赤
        return out + [u"封から照合の数を読めない(%s)" % type(e).__name__]
    for k, v in EXPECT_PIN.items():
        if repr(got.get(k)) != repr(v):
            out.append(u"%s: 封の字から読んだ値 %r と留めた値 %r が違う" % (k, got.get(k), v))
    if list(sc.seal_pred_rows(seal)) != list(PRED_IDS):
        out.append(u"封の予測の行が L-0〜L-4 でない")
    return out


# ---------------------------------------------------------------- 3. 触らない file
def untouched_problems(rels=NOT_TOUCHED_RELS, root=REPO, seal_rel=SEAL_REL, allowed_new=ALLOWED_NEW):
    return NSG.untouched_problems(rels=rels, root=root, seal_rel=seal_rel, allowed_new=allowed_new)


def later_declared_problems(declared=DECLARED_NEW_AFTER_SEAL, allowed_new=ALLOWED_NEW, rels=NOT_TOUCHED_RELS, root=REPO, seal_rel=SEAL_REL):
    return NSG.later_declared_problems(declared=declared, allowed_new=allowed_new, rels=rels, root=root, seal_rel=seal_rel)


def frozen_problems(rels=READ_ONLY_RELS, root=REPO, base=ROOT, seal_rel=SEAL_REL):
    return NSG.frozen_problems(rels=rels, root=root, base=base, seal_rel=seal_rel)


def seal_commit_of(root=REPO, seal_rel=SEAL_REL):
    return NSG.seal_commit_of(root, seal_rel)


reserved_problems = SGR.reserved_problems


# ---------------------------------------------------------------- 5. 配線(ast)
def _func(src, name):
    return NSG._func(src, name)


def own_function_problems(src):
    u"""前の便の関数と同じ名前を、script 自身が定義・代入していないか(差し替えていない)。"""
    names = set()
    for n in ast.parse(src).body:
        if isinstance(n, ast.FunctionDef):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return [u"前の便の関数 %s をこの script が自分で定義している" % f for _m, f in REUSED_FUNCS if f in names]


def calls_problems(src):
    u"""script の本文が ``<module>.<関数>`` を呼んでいる(または引いている)か。"""
    return [u"この script が %s.%s を使っていない" % (m, f) for m, f in REUSED_FUNCS if u"%s.%s" % (m, f) not in src]


def wiring_problems(sc=None):
    u"""この script が前の便の script の同じ instance を使っているか。問題の列。"""
    sc = sc or SC
    out = []
    missing = object()
    checks = (("RM", sc.PB, "RM"), ("D", sc.PB, "D"), ("NF", sc.PB, "NF"), ("GEN", sc.PB, "GEN"), ("RUN", sc.PB, "RUN"), ("GEN", sc.RM, "GEN"), ("RUN", sc.RM, "RUN"))
    for mine, holder, theirs in checks:
        if getattr(sc, mine, missing) is missing or getattr(sc, mine, missing) is not getattr(holder, theirs, missing):
            out.append(u"%s がこの script と前の便の script で同じ instance でない" % mine)
    return out


def verify_call_problems(src):
    u"""``verify_document`` を呼ぶのは script 全体で ``num_view`` の中の 1 か所だけ(1 本 1 profile で 1 回)。"""
    out = []
    calls = NSG.own_calls(src, "verify_document")
    if len(calls) != 1:
        out.append(u"verify_document を呼ぶのが script 全体で 1 か所でない(%d)" % len(calls))
    fn = _func(src, "num_view")
    if fn is None or sum(1 for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "verify_document") != 1:
        out.append(u"num_view の中の verify_document の呼び出しが 1 つでない")
    return out


class Patch(object):
    u"""module の属性を差し替えて、終わりに戻す。"""

    def __init__(self):
        self.saved = []

    def set(self, mod, name, value):
        self.saved.append((mod, name, getattr(mod, name)))
        setattr(mod, name, value)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        for mod, name, old in reversed(self.saved):
            setattr(mod, name, old)
        self.saved = []
        return False


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_seal_tables_paths_and_key_phrases_are_complete(self):
        self.assertEqual([], seal_problems(self.seal))

    def test_a_2_a_changed_key_phrase_turns_the_seal_check_red(self):
        for ph in SEAL_PHRASES:
            self.assertIn(ph, self.seal)
            mutated = self.seal.replace(ph, ph[:-1] + u"？")                       # 同じ字が 2 か所に在る要点も全部壊す
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], seal_problems(mutated), ph)

    def test_a_3_a_broken_prediction_table_or_missing_section_turns_it_red(self):
        lines = self.seal.split("\n")
        n4 = [i for i, ln in enumerate(lines) if ln.startswith("| L-4 |")]
        self.assertEqual(1, len(n4))
        self.assertNotEqual([], seal_problems("\n".join(lines[:n4[0]] + lines[n4[0] + 1:])))                       # 5 行が 4 行
        n2 = [i for i, ln in enumerate(lines) if ln.startswith("| L-2 |")][0]
        cells = lines[n2].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:n2] + [" | ".join(cells[:2]) + " |"] + lines[n2 + 1:])))   # 外れ方の欄が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:n2] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[n2 + 1:])))   # 照合の欄が空
        self.assertNotEqual([], seal_problems(self.seal.replace("`measure/xbrl_labelonly_2026-11-10.py`", "`measure/x.py`")))
        self.assertNotEqual([], seal_problems(self.seal.replace("`tests/measure/test_xbrl_labelonly_result.py`", "`tests/measure/x.py`")))
        self.assertNotEqual([], seal_problems(self.seal.replace("`tests/measure/test_xbrl_labelonly_seal.py`", "`tests/measure/x.py`")))
        self.assertNotEqual([], seal_problems(self.seal.replace("`docs/XBRL_LABEL_ONLY_RATES_RESULT_2026-11-10.md`", "`docs/x.md`")))
        self.assertNotEqual([], seal_problems(self.seal.replace("`fixtures/xbrl/labelonly/rates_2026-11-10.json`", "`fixtures/xbrl/labelonly/x.json`")))
        self.assertNotEqual([], seal_problems(self.seal.replace("## §4", "## 四", 1)))
        self.assertNotEqual([], seal_problems(self.seal.replace("## §2", "## 二", 1)))

    def test_a_4_the_record_path_and_the_paths_are_read_from_the_seal(self):
        self.assertEqual([RECORD_REL], seal_record_path(self.seal))
        self.assertTrue(set(SCRIPT_RELS + GATE_RELS + (DOC_REL,)) <= set(seal_paths(self.seal)))
        self.assertEqual([], seal_record_path(self.seal.replace("### §0-2", "### 0-2", 1)))
        self.assertEqual([], seal_paths(self.seal.replace("## §4", "## 四", 1)))


class ScriptMatchesSealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_b_1_the_script_agrees_with_the_seal(self):
        self.assertEqual([], script_problems(self.seal))

    def _fake(self, **ov):
        d = dict((k, getattr(SC, k)) for k in ("SEAL_REL", "SEAL_COMMIT", "PROFILES", "BASE", "EXISTING", "NEWROW", "L_NONE", "LABEL_WORDS", "G", "REC_REL", "DOC_REL", "SCRIPT_REL",
                                               "seal_expect", "seal_pred_rows"))
        d.update(ov)
        return types.SimpleNamespace(**d)

    def test_b_2_a_changed_script_constant_turns_it_red(self):
        self.assertEqual([], script_problems(self.seal, self._fake()))
        for ov in (dict(SEAL_COMMIT="0000000"), dict(SEAL_REL="docs/XBRL_NONFUNCTIONAL_SEAL_2026-11-10.md"), dict(PROFILES=("P28E", "P29E", "P30E", "P32E")), dict(PROFILES=("P29E", "P28E", "P30E", "P32E", "P33E")),
                   dict(PROFILES=("P28E", "P29E", "P30E", "P32E", "P33E", "P27")), dict(BASE="P29E"), dict(EXISTING=u"在"), dict(NEWROW=u"新規"), dict(L_NONE=u"無"), dict(LABEL_WORDS=(u"真", u"偽")),
                   dict(G="VALUE_MISMATCH"), dict(REC_REL="fixtures/xbrl/labelonly/x.json"), dict(DOC_REL="docs/x.md"), dict(SCRIPT_REL="measure/x.py")):
            self.assertNotEqual([], script_problems(self.seal, self._fake(**ov)), sorted(ov))
        self.assertNotEqual([], script_problems(self.seal.replace("11,137 / 6,586", "11,137 / 6,587", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal.replace("P28E の札のある行 6,597", "P28E の札のある行 6,598", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal.replace("16,588 / 10,357", "16,588 / 10,358", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal.replace("数の claim の行数 10,371", "数の claim の行数 10,372", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal.replace("| L-4 |", "| L-4x |", 1), self._fake()))

    def test_b_3_the_numbers_are_read_from_the_seal_not_copied(self):
        self.assertEqual(repr(EXPECT_PIN), repr(SC.seal_expect(self.seal)))
        changed = self.seal.replace("P33E 11,625 / 6,979", "P33E 11,625 / 6,980", 1)
        self.assertNotEqual(repr(EXPECT_PIN), repr(SC.seal_expect(changed)))
        for bad in (self.seal.replace("P29E〜P33E 16,588", "P29E〜P33E 16,5x8", 1), self.seal.replace("P28E の札のある行 6,597", "P28E の札の行 6,597", 1)):
            with self.assertRaises(Exception):
                SC.seal_expect(bad)


class NotTouchedAndFrozenTest(unittest.TestCase):
    def test_c_1_engine_measure_and_the_records_are_untouched_since_the_seal_commit(self):
        self.assertEqual([], untouched_problems(allowed_new=ALLOWED_NEW + DECLARED_NEW_AFTER_SEAL))
        self.assertEqual([], later_declared_problems())

    def test_c_1a_a_later_declared_file_with_this_seal_must_be_new_outside_the_engine_and_exactly_what_was_added(self):
        def repo():
            r = self._repo()
            r.put("measure/later.py")
            r.commit("measure/later.py")                                             # 後の便が足した script(commit 済み)
            return r
        good = ("measure/later.py",)
        kw = dict(allowed_new=("measure/new.py",), rels=self.RELS)
        self.assertEqual([], later_declared_problems(declared=good, root=repo().d, **kw))
        self.assertNotEqual([], later_declared_problems(declared=(), root=repo().d, **kw))                          # 届けずに足した file
        self.assertNotEqual([], later_declared_problems(declared=good + ("measure/ghost.py",), root=repo().d, **kw))  # 届けたのに木に無い
        r2 = repo()
        r2.put("measure/prev.py")                                                    # 封の木に在る file の変更は届けても赤
        self.assertNotEqual([], later_declared_problems(declared=good + ("measure/prev.py",), root=r2.d, **kw))
        r3 = repo()
        r3.put("adapters/xbrl/later.py")                                             # engine の置き場の新しい file は届けても赤
        self.assertNotEqual([], later_declared_problems(declared=good + ("adapters/xbrl/later.py",), root=r3.d, **kw))
        r4 = repo()
        r4.put("measure/undeclared.py")                                              # 届けの外の新しい file は、届けを足した検査でも赤
        self.assertNotEqual([], untouched_problems(rels=self.RELS, root=r4.d, allowed_new=("measure/new.py",) + good))

    def test_c_1b_the_seal_commit_is_found_from_history(self):
        s = seal_commit_of()
        self.assertTrue(s and s.startswith(SEAL_COMMIT_SHORT))

    def test_c_1c_the_read_only_files_are_byte_identical_to_the_seal_commit(self):
        self.assertEqual([], frozen_problems())
        self.assertEqual(len(READ_ONLY_RELS), len(set(READ_ONLY_RELS)))
        for rel in READ_ONLY_RELS:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def _repo(self):
        r = PR.Repo()
        for f in ("measure/lib/x.py", "measure/prev.py", "adapters/xbrl/recipes.py", "fixtures/xbrl/a/rec.json"):
            r.put(f)
        r.put(SEAL_REL)
        r.commit("measure/lib/x.py", "measure/prev.py", "adapters/xbrl/recipes.py", "fixtures/xbrl/a/rec.json", SEAL_REL)
        return r

    RELS = ("adapters", "measure", "fixtures/xbrl")

    def _probe(self, r, allowed=("measure/new.py",)):
        return untouched_problems(rels=self.RELS, root=r.d, allowed_new=allowed)

    def test_c_2_the_untouched_check_with_this_seal_sees_changes_new_files_and_lets_the_allowed_ones_through(self):
        r = self._repo()
        self.assertEqual([], self._probe(r))
        for rel in ("measure/prev.py", "adapters/xbrl/recipes.py", "fixtures/xbrl/a/rec.json"):
            r2 = self._repo()
            r2.put(rel)                                                              # 未 commit の変更
            self.assertNotEqual([], self._probe(r2), rel)
        r3 = self._repo()
        r3.put("measure/prev.py")
        r3.commit("measure/prev.py")                                                 # 封の後に commit された変更
        self.assertNotEqual([], self._probe(r3))
        r4 = self._repo()
        r4.put("measure/other_new.py")                                               # 許していない新しい file(未追跡)
        self.assertNotEqual([], self._probe(r4))
        r6 = self._repo()
        r6.put("measure/new.py")                                                     # 許した新しい file は赤にならない
        self.assertEqual([], self._probe(r6))
        r6.commit("measure/new.py")
        self.assertEqual([], self._probe(r6))
        r7 = PR.Repo()                                                               # この便の封が無い repo
        r7.put("measure/prev.py")
        r7.commit("measure/prev.py")
        self.assertNotEqual([], self._probe(r7))

    def test_c_3_the_allowed_new_files_are_exactly_the_script_and_the_record(self):
        self.assertEqual((SCRIPT_RELS[0], RECORD_REL), ALLOWED_NEW)
        self.assertEqual({"measure", "fixtures/xbrl", "adapters", "core"}, set(NOT_TOUCHED_RELS))

    def test_c_4_the_frozen_check_with_this_seal_sees_a_changed_and_a_missing_file(self):
        r = self._repo()
        base = os.path.join(r.d, "audit-core")
        self.assertEqual([], frozen_problems(rels=("measure/prev.py",), root=r.d, base=base))
        with open(os.path.join(base, "measure/prev.py"), "a", encoding="utf-8") as fh:
            fh.write("x = 1\n")
        self.assertEqual([u"封の commit の blob と byte が違う: measure/prev.py"], frozen_problems(rels=("measure/prev.py",), root=r.d, base=base))
        self.assertEqual([u"封の commit に無い: measure/later.py"], frozen_problems(rels=("measure/later.py",), root=r.d, base=base))
        self.assertNotEqual([], frozen_problems(rels=READ_ONLY_RELS + ("measure/nonexistent_file.py",)))

    def test_e_1_gate_files_do_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems(rels=tuple(r for r in GATE_RELS if os.path.exists(os.path.join(ROOT, r))), base=ROOT))

    def test_e_2_the_reserved_name_check_sees_a_planted_name(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("FROZEN_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rels=("g.py",), base=d))

    def test_f_1_scripts_and_gates_carry_no_docid(self):
        for rel in SCRIPT_RELS + GATE_RELS:
            if os.path.exists(os.path.join(ROOT, rel)):
                self.assertIsNone(DOCID_RE.search(read(rel)), rel)

    def test_f_2_scripts_name_the_seal(self):
        for rel in SCRIPT_RELS:
            self.assertIn("XBRL_LABEL_ONLY_RATES_SEAL_2026-11-10.md", read(rel), rel)

    def test_f_3_the_script_and_the_gates_do_not_call_the_label_a_human_eye(self):
        u"""札は盲検の LLM の席の読み。『人の目』は否定の言い方(人の目ではない・人の目でも…ない)だけ。"""
        for rel in SCRIPT_RELS + GATE_RELS:
            if not os.path.exists(os.path.join(ROOT, rel)):
                continue
            for n, line in enumerate(read(rel).splitlines(), 1):
                for m in re.finditer(EYE, line):
                    tail = line[m.end():m.end() + 6]
                    self.assertTrue(re.match(u"(ではない|でも|なし|で見ていない)", tail) is not None or u"『" + EYE + u"』" in line or u"「" + EYE + u"」" in line, (rel, n, line[:80]))


# ---------------------------------------------------------------- 標本の部品(通信しない・cache を読まない)
def fake_views(rows_by_profile, ok=True):
    u"""{profile: [(id, 鍵, state)]} → ``num_view`` の返り値の形 {profile: (rows, ok)}。"""
    return collections.OrderedDict((p, (list(rows), ok)) for p, rows in rows_by_profile.items())


class WiringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = read(SCRIPT_RELS[0])

    def test_w_1_the_script_uses_the_same_instances_as_the_previous_scripts(self):
        self.assertEqual([], wiring_problems())
        self.assertIs(SC.RM, SC.PB.RM)
        self.assertIs(SC.GEN, SC.RM.GEN)
        self.assertIs(SC.RUN, SC.RM.RUN)
        self.assertIs(SC.NF, SC.PB.NF)

    def test_w_2_another_instance_turns_the_wiring_check_red(self):
        for name in ("RM", "D", "NF", "GEN", "RUN"):
            fake = types.SimpleNamespace(**dict((k, getattr(SC, k)) for k in dir(SC) if not k.startswith("__")))
            setattr(fake, name, types.SimpleNamespace())
            self.assertNotEqual([], wiring_problems(fake), name)
        self.assertEqual([], wiring_problems())

    def test_w_3_the_script_defines_none_of_the_previous_functions_and_uses_them(self):
        src = self.src
        self.assertEqual([], own_function_problems(src))
        self.assertEqual([], calls_problems(src))
        for m, f in REUSED_FUNCS:
            self.assertTrue(callable(getattr(getattr(SC, m), f)), (m, f))
            self.assertFalse(hasattr(SC, f), f)                                   # この script の名前空間に同名の関数を持たない
            self.assertNotEqual([], own_function_problems(src + u"\n\ndef %s(*a):\n    return None\n" % f), f)
            self.assertNotEqual([], own_function_problems(src + u"\n%s = None\n" % f), f)
            self.assertNotEqual([], calls_problems(src.replace(u"%s.%s" % (m, f), u"X.%s" % f)), (m, f))

    def test_w_4_the_script_loads_the_pb_script_with_importlib_once(self):
        self.assertIn(u'load_module("xbrl_pbind_2026-11-06.py"', self.src)
        self.assertEqual(1, self.src.count(u"load_module(\"xbrl_"))

    def test_w_5_the_loader_puts_back_the_names_that_were_there_before_and_keeps_its_own(self):
        before = dict(sys.modules)
        probe = "labelonly_script_loader_probe"
        try:
            mod = SC.load_module("xbrl_pbind_2026-11-06.py", probe)
            self.assertIsNot(mod.XR, SC.PB.XR)                                    # 前提: 読み直しは別の object を作る(上書きの機会がある)
            self.assertEqual([], sorted(k for k, v in before.items() if sys.modules.get(k) is not v))
            self.assertIs(sys.modules.get(probe), mod)
        finally:
            sys.modules.pop(probe, None)

    def test_w_6_a_loader_without_the_restore_lines_overwrites_the_names(self):
        u"""戻す行(``finally`` の中)を外した版の loader を同じ file の字から作って走らせると、先に居た名前が上書きされる(= w_5 が赤になる形)。"""
        src = self.src
        i = src.index(u"def load_module(")
        j = src.index(u"\n\n\n", i)
        fn = src[i:j]
        self.assertIn(u"finally:", fn)
        k = fn.index(u"    finally:")
        broken = fn[:k].rstrip() + u"\n    except ZeroDivisionError:\n        pass\n    return mod\n"
        self.assertNotIn(u"sys.modules[k] = v", broken)
        ns = {"importlib": importlib, "os": os, "sys": sys, "HERE": os.path.join(ROOT, "measure")}
        exec(compile(u"import importlib.util\n" + broken, "<broken_loader>", "exec"), ns)
        before = dict(sys.modules)
        probe = "labelonly_script_broken_loader_probe"
        try:
            ns["load_module"]("xbrl_pbind_2026-11-06.py", probe)
            self.assertNotEqual([], sorted(k for k, v in before.items() if sys.modules.get(k) is not v))
        finally:
            for k, v in before.items():
                sys.modules[k] = v
            for k in list(sys.modules):
                if k not in before:
                    sys.modules.pop(k, None)

    def test_w_7_verify_document_is_called_in_one_place_and_the_check_sees_a_second_call(self):
        self.assertEqual([], verify_call_problems(self.src))
        self.assertNotEqual([], verify_call_problems(self.src + u"\n\ndef extra(zb, t):\n    return VD.verify_document(zb, 'P28E', t)\n"))
        self.assertNotEqual([], verify_call_problems(self.src.replace(u"VD.verify_document(", u"VD.other(")))


class BindingTest(unittest.TestCase):
    u"""札の結び方(P28E の (本, id))・既存の判定(鍵 (文の番号, 文の中の位置) の一致)・新しい行は札なし。手で作った小さな標本の振る舞い。"""

    LABELS = {"N001": u"真", "N002": u"偽", "N003": u"判定不能", "N004": u"真"}
    G, VM, U, PN = "GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"

    def book(self, p28, later, labels=None, ok=True):
        views = collections.OrderedDict()
        views["P28E"] = (p28, ok)
        for p in SC.PROFILES[1:]:
            views[p] = (later, ok)
        return SC.assemble_book("B0_F2_m", "F2", "m", "aiforms", views, self.LABELS if labels is None else labels)

    def rows_of(self, rows, profile):
        return [(r[3], r[4], r[5], r[6], r[7]) for r in rows if r[2] == profile]

    def test_g_1_p28e_rows_take_their_label_by_id_and_every_p28e_row_is_existing(self):
        p28 = [("N001", (0, 0), self.G), ("N002", (0, 5), self.VM), ("N003", (1, 0), self.U), ("N004", (2, 0), self.PN)]
        book, rows = self.book(p28, [])
        self.assertEqual([(0, 0, self.G, u"真", u"既存"), (0, 5, self.VM, u"偽", u"既存"), (1, 0, self.U, u"判定不能", u"既存"), (2, 0, self.PN, u"真", u"既存")], self.rows_of(rows, "P28E"))
        self.assertEqual({"P28E": 4, "P29E": 0, "P30E": 0, "P32E": 0, "P33E": 0}, dict(book[u"数の claim の数"]))

    def test_g_2_later_profiles_take_the_label_by_key_not_by_id_and_new_rows_have_none(self):
        p28 = [("N001", (0, 0), self.G), ("N002", (0, 5), self.VM), ("N003", (1, 0), self.U)]
        # P29E 以降は id が前にずれる(新しい行が先に入る)。id N002 が P28E で偽だったが、鍵 (0, 0) の行は P28E で真(N001)。id で結べば偽になる
        later = [("N001", (0, 3), self.G), ("N002", (0, 0), self.G), ("N003", (0, 5), self.VM), ("N004", (1, 0), self.U), ("N005", (4, 4), self.G)]
        book, rows = self.book(later=later, p28=p28)
        for p in SC.PROFILES[1:]:
            self.assertEqual([(0, 3, self.G, u"なし", u"新"), (0, 0, self.G, u"真", u"既存"), (0, 5, self.VM, u"偽", u"既存"), (1, 0, self.U, u"判定不能", u"既存"), (4, 4, self.G, u"なし", u"新")],
                             self.rows_of(rows, p), p)

    def test_g_3_a_new_row_never_takes_a_label_even_when_its_id_is_in_the_label_record(self):
        p28 = [("N001", (0, 0), self.G)]
        later = [("N001", (7, 7), self.G), ("N002", (0, 0), self.G)]                        # 鍵 (7, 7) は P28E に無い。id N001 は札の記録に在る(真)
        _book, rows = self.book(p28=p28, later=later)
        self.assertEqual([(7, 7, self.G, u"なし", u"新"), (0, 0, self.G, u"真", u"既存")], self.rows_of(rows, "P29E"))

    def test_g_4_the_existing_judgement_looks_at_the_key_of_both_numbers(self):
        p28 = [("N001", (3, 1), self.G)]
        for key, existing in (((3, 1), True), ((3, 2), False), ((2, 1), False), ((1, 3), False)):
            _b, rows = self.book(p28=p28, later=[("N001", key, self.G)])
            word = self.rows_of(rows, "P33E")[0][4]
            self.assertEqual(u"既存" if existing else u"新", word, key)

    def test_g_5_label_words_outside_the_three_become_none_and_the_l0_difference_counts_both_sides(self):
        labels = {"N001": u"真", "N002": u"どちらでもない", "N009": u"偽", "N010": u"真"}          # N002 は語が違う・N009 N010 は今回の P28E に無い
        p28 = [("N001", (0, 0), self.G), ("N002", (0, 1), self.G), ("N003", (0, 2), self.G)]         # N003 は札の記録に無い
        book, rows = self.book(p28=p28, later=[], labels=labels)
        self.assertEqual([u"真", u"なし", u"なし"], [r[6] for r in rows if r[2] == "P28E"])
        self.assertEqual({u"P28E のみ": 1, u"札のみ": 2, u"札の記録の id の数": 4}, dict(book[u"L-0 の差"]))     # P28E のみ = N003(札の記録に無い id)・札のみ = N009 N010。語が違う N002 は id が在るので数えない

    def test_g_6_the_row_carries_the_name_the_form_and_the_profile_in_the_declared_order(self):
        book, rows = self.book(p28=[("N001", (0, 0), self.G)], later=[("N001", (0, 0), self.VM)])
        self.assertEqual(list(SC.ROW_FIELDS), [u"本の id", u"形", u"profile", u"文の番号", u"文の中の位置", u"state", u"札", u"既存か新か"])
        self.assertEqual([["B0_F2_m", "F2", "P28E", 0, 0, self.G, u"真", u"既存"]] + [["B0_F2_m", "F2", p, 0, 0, self.VM, u"真", u"既存"] for p in SC.PROFILES[1:]], rows)
        self.assertEqual(list(SC.BOOK_KEYS), list(book))
        self.assertEqual((u"B0_F2_m", "F2", "m", "aiforms"), (book[u"本の id"], book[u"形"], book[u"model"], book[u"材料"]))

    def test_g_7_a_not_matching_book_keeps_all_rows_and_records_the_flag(self):
        p28 = [("N001", (0, 0), self.G), ("N002", (0, 0), self.G)]                           # 鍵の重複
        book, rows = self.book(p28=p28, later=[], ok=False)
        self.assertEqual(2, len(rows))
        self.assertEqual({p: False for p in SC.PROFILES}, dict(book[u"対応"]))
        self.assertEqual([u"真", u"偽"], [r[6] for r in rows])                               # P28E の行は自分の id で引く(鍵が重複しても行は残る)

    def test_g_8_a_duplicated_p28e_key_gives_the_later_profiles_the_label_of_the_first_row(self):
        p28 = [("N001", (0, 0), self.G), ("N002", (0, 0), self.G)]
        _b, rows = self.book(p28=p28, later=[("N001", (0, 0), self.G)])
        self.assertEqual(u"真", self.rows_of(rows, "P29E")[0][3])


class NumViewTest(unittest.TestCase):
    u"""``num_view`` は raw の num の列だけを数の claim にし、鍵は raw の (sentence, pos)、id と state は verify_document の claim から取る。"""

    def run_view(self, claims, nums, texts):
        class FakeVD(object):
            calls = []

            @staticmethod
            def verify_document(zb, prof, text):
                FakeVD.calls.append((zb, prof, text))
                return {"claims": claims}

        class FakePR(object):
            @staticmethod
            def build_modified_zip(zb, text):
                return (b"zm",)

        class FakeR(object):
            @staticmethod
            def build_raw_claims(zm, prof):
                assert zm == b"zm"
                return nums, texts
        with Patch() as pt:
            pt.set(SC, "VD", FakeVD)
            pt.set(SC, "PR", FakePR)
            pt.set(SC, "R", FakeR)
            pt.set(SC, "V", types.SimpleNamespace(PROFILES={"P28E": "prof28"}))
            got = SC.num_view(b"zip", u"文", "P28E")
        self.assertEqual([(b"zip", "P28E", u"文")], FakeVD.calls)              # 1 回だけ・同じ入力
        return got

    def test_n_1_the_number_rows_are_the_num_list_with_the_raw_key_and_the_claim_state(self):
        claims = [{"id": "N001", "kind": "num", "state": "GROUNDED"}, {"id": "N002", "kind": "num", "state": "VALUE_MISMATCH"}, {"id": "T001", "kind": "text", "state": "UNVERIFIABLE"}]
        nums = [{"id": "N001", "sentence": 4, "pos": 7}, {"id": "N002", "sentence": 5, "pos": 0}]
        texts = [{"id": "T001", "sentence": 5, "pos": 0}]
        rows, ok = self.run_view(claims, nums, texts)
        self.assertEqual([("N001", (4, 7), "GROUNDED"), ("N002", (5, 0), "VALUE_MISMATCH")], rows)       # 文の claim は母集団に入れない
        self.assertTrue(ok)

    def test_n_2_a_mismatch_of_ids_kinds_counts_or_duplicate_keys_turns_the_flag_false_but_keeps_the_rows(self):
        claims = [{"id": "N001", "kind": "num", "state": "GROUNDED"}, {"id": "N002", "kind": "num", "state": "GROUNDED"}]
        nums = [{"id": "N001", "sentence": 1, "pos": 1}, {"id": "N002", "sentence": 1, "pos": 2}]
        self.assertTrue(self.run_view(claims, nums, [])[1])
        rows, ok = self.run_view(claims, [{"id": "N001", "sentence": 1, "pos": 1}, {"id": "N009", "sentence": 1, "pos": 2}], [])
        self.assertFalse(ok)                                                                           # id の並びが違う
        self.assertEqual(2, len(rows))
        rows, ok = self.run_view(claims, [{"id": "N001", "sentence": 1, "pos": 1}, {"id": "N002", "sentence": 1, "pos": 1}], [])
        self.assertFalse(ok)                                                                           # 鍵の重複
        self.assertEqual(2, len(rows))
        self.assertFalse(self.run_view(claims + [{"id": "T001", "kind": "text", "state": "GROUNDED"}], nums, [])[1])        # 数が合わない
        self.assertFalse(self.run_view([dict(claims[0], kind="text"), claims[1]], nums, [])[1])        # kind の位置が違う

    def test_n_3_the_key_uses_the_raw_sentence_and_pos_not_the_claim_id(self):
        claims = [{"id": "N010", "kind": "num", "state": "GROUNDED"}]
        rows, _ok = self.run_view(claims, [{"id": "N010", "sentence": 12, "pos": 34}], [])
        self.assertEqual([("N010", (12, 34), "GROUNDED")], rows)


class JudgeBookTest(unittest.TestCase):
    u"""``judge_book_lb`` は 1 本に 5 profile を 1 回ずつ走らせ(順は PROFILES)、書類の ZIP と文を時計に関係なく 1 回だけ読む。"""

    def test_j_1_one_book_runs_each_profile_once_in_order_and_binds_labels_by_p28e_id(self):
        seen = []
        tables = {"P28E": [("N001", (0, 0), "GROUNDED"), ("N002", (0, 4), "VALUE_MISMATCH")], "P29E": [("N001", (0, 1), "GROUNDED"), ("N002", (0, 0), "GROUNDED"), ("N003", (0, 4), "GROUNDED")]}
        for p in SC.PROFILES[2:]:
            tables[p] = tables["P29E"]

        def fake_view(zb, text, p):
            seen.append((zb, text, p))
            return tables[p], True
        reads = []
        with Patch() as pt:
            pt.set(SC, "num_view", fake_view)
            pt.set(SC.GEN, "read_zip", lambda row, caches: reads.append(("zip", row, caches)) or b"zb")
            pt.set(SC.RUN, "read_text", lambda name, item, d: reads.append(("text", name, d)) or u"文")
            job = ("aiforms", "B1_F3_m", {u"form": "F3", u"model": "m"}, {"row": 1}, "/textdir", {"c": 1}, {}, {"N001": u"偽", "N002": u"真"}, {})
            book, rows = SC.judge_book_lb(job)
        self.assertEqual([(b"zb", u"文", p) for p in SC.PROFILES], seen)
        self.assertEqual([("zip", {"row": 1}, {"c": 1}), ("text", "B1_F3_m", "/textdir")], reads)
        self.assertEqual([[0, 0, u"偽", u"既存"], [0, 4, u"真", u"既存"]], [[r[3], r[4], r[6], r[7]] for r in rows if r[2] == "P28E"])
        self.assertEqual([[0, 1, u"なし", u"新"], [0, 0, u"偽", u"既存"], [0, 4, u"真", u"既存"]], [[r[3], r[4], r[6], r[7]] for r in rows if r[2] == "P33E"])
        self.assertEqual("F3", book[u"形"])


class RunWiringTest(unittest.TestCase):
    u"""``run`` の本番の守り・出力が既に在れば止まる・順(本 → profile)・procs。入力と判定は偽の部品(通信も cache の読みも要らない)。"""

    def _fakes(self, names, calls=None):
        fake_rm = types.SimpleNamespace(
            load_jobs=lambda root, only: [("aiforms", n, {u"form": "F1", u"model": "m"}, {}, "/nope", {}, {}, {"N001": u"真"}, {}) for n in names],
            caches_all=lambda: {}, load_labels=lambda root: {"aiforms": dict((n, {"N001": u"真"}) for n in names)}, LABELS_REL=SC.RM.LABELS_REL)

        def fake_pool(fn, jobs, procs):
            if calls is not None:
                calls.append((fn, [j[1] for j in jobs], procs))
            return [(collections.OrderedDict([(u"本の id", j[1]), (u"L-0 の差", collections.OrderedDict([(u"P28E のみ", 0), (u"札のみ", 0), (u"札の記録の id の数", 1)]))]), [[j[1], "F1", "P28E", 0, 0, "GROUNDED", u"真", u"既存"]])
                    for j in jobs]
        fake_nf = types.SimpleNamespace(map_pool=fake_pool, STATES=SC.NF.STATES)
        pt = Patch()
        pt.set(SC, "RM", fake_rm)
        pt.set(SC, "NF", fake_nf)
        pt.set(SC.GEN, "caches_snapshot", lambda caches: {})
        pt.set(SC.GEN, "git_head", lambda d: "1" * 40)
        pt.set(SC.GEN, "sha256_file", lambda p: "2" * 64)
        pt.set(SC.VD, "engine_fingerprint", lambda: {"adapter_xbrl_py_sha256": "3" * 64})
        return pt

    def test_r_1_the_run_passes_the_books_in_order_to_one_pool_call_and_writes_the_record(self):
        calls = []
        before = SC.GEN.key_leaks
        with self._fakes(["B0", "B1", "B2"], calls), tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            out = os.path.join(d, "t.json")
            rec = SC.run(root=SC.ROOT, only="x", out=out, procs=3, say=lambda *a: None)
            self.assertIs(before, SC.GEN.key_leaks)                                  # 書き込みの間だけ差し替えた鍵の検査は戻る
            self.assertTrue(os.path.exists(out))
            with open(out, encoding="utf-8") as fh:
                text = fh.read()
        self.assertEqual([(SC.judge_book_lb, ["B0", "B1", "B2"], 3)], calls)
        self.assertEqual(["B0", "B1", "B2"], [b[u"本の id"] for b in rec[u"本"]])
        self.assertEqual(3, len(rec[u"行"]))
        self.assertEqual(list(SC.PROFILES), rec[u"profile"])
        self.assertEqual(u"**--only の docID だけ(本番の記録ではない)**", rec[u"範囲"])
        self.assertEqual(3, rec[u"札の記録の (本, id) の数"])                             # 偽の load_labels は 3 本 × 1 id
        self.assertEqual({"aiforms": "2" * 64, "f5": "2" * 64}, dict(rec[u"札の記録の sha256"]))
        self.assertEqual(("1" * 40, "2" * 64, {"adapter_xbrl_py_sha256": "3" * 64}), (rec[u"HEAD の commit"], rec[u"この script の sha256"], rec[u"engine の指紋"]))
        self.assertEqual((SC.SEAL_REL, SC.SEAL_COMMIT, []), (rec[u"seal"], rec[u"封の commit"], rec[u"key_leaks"]))
        self.assertEqual(list(SC.LIMITS), rec[u"限界"])
        import json
        self.assertEqual(json.loads(text)[u"行"], rec[u"行"])                          # 書いた字を読み戻すと同じ(行の 1 行ずつの書き方が JSON として正しい)

    def test_r_2_production_needs_no_only_and_a_valid_procs(self):
        with self._fakes(["B0"]), tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with self.assertRaises(SC.Stop):
                SC.run(root=d, only="x", say=lambda *a: None)                        # out なし = 本番の記録の path
            self.assertFalse(os.path.exists(os.path.join(d, SC.REC_REL)))
            for bad in (0, -1, 1.5):
                with self.assertRaises(SC.Stop):
                    SC.run(root=SC.ROOT, out=os.path.join(d, "u.json"), procs=bad, say=lambda *a: None)

    def test_r_3_an_existing_output_stops_the_run_before_any_work(self):
        calls = []
        with self._fakes(["B0"], calls), tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            out = os.path.join(d, "t.json")
            with open(out, "w", encoding="utf-8") as fh:
                fh.write("{}")
            with self.assertRaises(SC.Stop):
                SC.run(root=SC.ROOT, out=out, say=lambda *a: None)
            self.assertEqual([], calls)                                              # 測る前に止まる
            with open(out, encoding="utf-8") as fh:
                self.assertEqual("{}", fh.read())                                    # 既に在る出力は書き換えない

    def test_r_4_the_cache_change_stops_the_run_and_writes_nothing(self):
        snaps = iter([{"a": 1}, {"a": 2}])
        with self._fakes(["B0"]) as pt, tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            pt.set(SC.GEN, "caches_snapshot", lambda caches: next(snaps))
            out = os.path.join(d, "t.json")
            with self.assertRaises(SC.Stop):
                SC.run(root=SC.ROOT, out=out, say=lambda *a: None)
            self.assertFalse(os.path.exists(out))

    def test_r_5_the_cli_options_and_the_tally_does_not_write(self):
        src = read(SCRIPT_RELS[0])
        self.assertEqual(1, src.count(u"add_argument(\"--procs\""))
        self.assertNotIn(u"--reps", src)
        i = src.index(u"def run_tally(")
        j = src.index(u"\n\n\n", i)
        self.assertNotIn(u"open(", src[i:j])
        self.assertNotIn(u"write", src[i:j])

    def test_r_6_the_record_holds_no_sentence_value_or_pointer_field(self):
        u"""行の欄は 8 つで、文・要素名・会社名・pointer・値の欄を持たない。"""
        self.assertEqual(8, len(SC.ROW_FIELDS))
        for bad in (u"文", u"span", u"value", u"値", u"要素名", u"pointer", u"理由", u"会社名"):
            self.assertNotIn(bad, SC.ROW_FIELDS)


class RateTest(unittest.TestCase):
    def test_t_1_the_rate_is_an_integer_half_up_rounding_in_tenths(self):
        for g, n, want in ((1, 2000, u"0.1"), (3, 2000, u"0.2"), (1, 3, u"33.3"), (2, 3, u"66.7"), (0, 5, u"0.0"), (5, 5, u"100.0"), (1, 8, u"12.5"), (1, 16, u"6.3"), (1, 2, u"50.0"), (6979, 11625, u"60.0")):
            self.assertEqual(want, SC.rate_str(g, n), (g, n))
        self.assertEqual(u"なし", SC.rate_str(0, 0))
        self.assertIsNone(SC.rate_tenths(5, 0))


class OrderTest(unittest.TestCase):
    def test_o_1_the_real_history_has_the_seal_before_the_scripts_and_gates(self):
        u"""script・門のどれかが未 commit なら赤(足した commit が無い)。この便は engine を変えないので実装の commit は無い。"""
        self.assertEqual([], PR.order_problems(REPO, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [], SCRIPT_RELS + GATE_RELS))


OTHERS = ["measure/a.py", "tests/g.py"]
SEALF = "docs/seal.md"


def order_of(r, seal_short):
    return PR.order_problems(r.d, PREFIX, SEALF, seal_short, [], OTHERS)


class OrderMutationTest(unittest.TestCase):
    def _repo(self, before_seal=(), after=OTHERS, seal_touches=None):
        r = PR.Repo()
        for f in before_seal:
            r.put(f)
            r.commit(f)
        if seal_touches:
            r.put(seal_touches)
        r.put(SEALF)
        s = r.commit(SEALF, *([seal_touches] if seal_touches else []))
        for f in after:
            r.put(f)
        if after:
            r.commit(*after)
        return r, s[:7]

    def test_p_1_a_correct_order_is_green(self):
        r, s = self._repo()
        self.assertEqual([], order_of(r, s))

    def test_p_2_a_script_before_the_seal_is_red(self):
        r, s = self._repo(before_seal=[OTHERS[0]], after=OTHERS[1:])
        self.assertIn("BEFORE_SEAL:" + OTHERS[0], order_of(r, s))

    def test_p_3_an_uncommitted_script_is_red_not_skipped(self):
        r, s = self._repo(after=OTHERS[:1])
        self.assertEqual(["UNCOMMITTED:" + OTHERS[1]], order_of(r, s))
        r2, s2 = self._repo(after=[])
        self.assertEqual(sorted("UNCOMMITTED:" + o for o in OTHERS), sorted(order_of(r2, s2)))

    def test_p_4_a_wrong_seal_hash_or_a_seal_that_touches_the_engine_is_red(self):
        r, s = self._repo()
        self.assertIn("SEAL_NOT_THE_SEALED", order_of(r, "0000000"))
        r2, s2 = self._repo(before_seal=["adapters/xbrl/recipes.py"], seal_touches="adapters/xbrl/recipes.py")
        self.assertIn("SEAL_TOUCHES_ENGINE", order_of(r2, s2))

    def test_p_5_the_seal_is_found_by_the_commit_that_added_it(self):
        r, s = self._repo()
        self.assertTrue(seal_commit_of(r.d, SEALF).startswith(s))
        r2 = PR.Repo()
        r2.put("measure/x.py")
        r2.commit("measure/x.py")
        self.assertIsNone(seal_commit_of(r2.d, SEALF))


if __name__ == "__main__":
    unittest.main()
