# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_INPUT_TYPE_V1_SEAL_2026-11-23.md(8f3ec76b)の結果の文書 docs/XBRL_INPUT_TYPE_V1_RESULT_2026-11-23.md(便 XJ0)。

封の門 ``test_xbrl_input_type_v1_seal.py`` の次の段。**追跡されている記録・script・封・封の門・指示書・結果の文書と git の履歴だけを読む**(書類の置き場は読まない・道具は呼ばない・標準の辞書の file は読まない・通信しない・鍵は読まない)。
便 XA0 の結果の門 ``test_xbrl_sheet_wall_result.py`` の部品(読み・sha256・% の丸め・節の切り出し・数のトークン・禁止語・blob の道具)を読み込んで使う(門としては走らせない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表と、全部のセル・数・向きの語を 1 か所ずつ掃く掃きで(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封・封の門・指示書の sha256(字で留める)・記録の script の sha256・封の commit の欄・記録の限界の欄(script の字)・材料の欄・script の決めの字
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、開発の 5 本・本番だけの 62 本・全部の 67 本の集計の全部の欄・予測に要る数を数え直す(書類ごとの足し算の関係を含む)
 c 予測 XJ0-1〜XJ0-10 の当たり外れを、封 §4 の字から取った境(丸める前の整数で)と記録(本番だけの 62 本)から決め直し、文書 §1 の表・件数と同じことを見る。
   封 §6 の次の便の候補が (i)〜(v) の 5 つだけ・6 つ目も封に無い候補も足さない・(i) の条件は記録の断った規則の数に縛る・(iv) の「有料・別の封・払う前の知らせ・人間の決め」。
   記録の変え方の「通した」が 1 以上なら「中身の違いを断る」を肯定しない
 d 結果の文書の数: §1・§2・§4・§5 の数は全部、記録から導く。記録の数と字から文書の §3 以外の全部の行を組み直し、文書と行ごとに照らす(``render_doc``)。主な主張の文は断片でも縛る。
   **§3 の読み(記録に欄の無い読み。出どころは記録の監査の席)は記録に縛らず**、見出し・「測った数ではない」・字で留めた数の並び・記録から導ける数の関係と、
   §3 だけの主張が §3 の外に出ないことを縛る。§4 の 36 は封の門の試験の数に縛る
 e 文書の頭の負けと限界(封 §7 の 5 本・封 §6 の読み方)・禁止語・「XBRL を作れる」「専用の道具が要らない」「AI に任せられる」「誤りが無くなる」「会社の AI がこの型で書ける」「AI が指示書に従う」「EDINET の検査に通る」を肯定で書かない・docID と EDINET コードの形
 f 封・script・記録・封の門・指示書が commit の blob と一致(結果の便で 0 行)・engine は封の commit から 0 行・順序・文書が書く commit の字が実の履歴と合う
この file は docID の字を持たない。
"""
import collections
import copy
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)

import importlib.util  # noqa: E402


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


WG = load_module("tests/measure/test_xbrl_sheet_wall_result.py", "xbrl_sheet_wall_result_gate_for_input_type_v1_result_gate")                # 便 XA0 の結果の門の部品。門としては走らせない
SG = load_module("tests/measure/test_xbrl_input_type_v1_seal.py", "xbrl_input_type_v1_seal_gate_for_result_gate")                # 封の門の部品。門としては走らせない
PR = WG.PR
MS = SG.MS

read, sha_file, guard, pct, section = WG.read, WG.sha_file, WG.guard, WG.pct, WG.section
ints_in, doc_number_tokens = WG.ints_in, WG.doc_number_tokens

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
INSTR_REL = SG.INSTRUCTION_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_input_type_v1_result.py"
DOC_REL = "docs/XBRL_INPUT_TYPE_V1_RESULT_2026-11-23.md"
SCRIPT_COMMIT_SHORT = "48cf7135"                  # script・封の門・指示書を足した commit
RECORD_COMMIT_SHORT = "9a8b246d"                  # 記録を足した commit
FIX_COMMIT_SHORT = "36a52eec"                     # 封の門の変異 D12 を 2 行直した commit(記録の後・封の門の 1 file だけ)
SEAL_GATE_FIXED_SHA = "b579c678be3a6c8ae527aed19b99b1ccddbf69f59b82d07d762bc7bf552f02be"          # 36a52eec の封の門の中身
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, FIX_COMMIT_SHORT), (INSTR_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
HISTORY = collections.OrderedDict([
    (SEAL_REL, [SEAL_COMMIT_SHORT]), (SCRIPT_REL, [SCRIPT_COMMIT_SHORT]), (SEAL_GATE_REL, [SCRIPT_COMMIT_SHORT, FIX_COMMIT_SHORT]), (INSTR_REL, [SCRIPT_COMMIT_SHORT]), (RECORD_REL, [RECORD_COMMIT_SHORT])])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)
DOC_COMMITS_ALL = DOC_COMMITS + (FIX_COMMIT_SHORT,)          # 文書が書く commit の字は 4 つ(3 つ + 追記の 1 つ)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "8528d9eb9f5184fae4eca8e7a90029c732af2274fa6f1eb089beba92fb008a68"),
    (SCRIPT_REL, "420fd6862e3989ff936041c42cd0619ffad3af8783ac4e9a12f65651746f2909"),
    (SEAL_GATE_REL, SEAL_GATE_FIXED_SHA),
    (SEAL_REL, "51639be054a83744fe402922c35c97d1e40b7234a1ed7100fd46faa62db060ef"),
    (INSTR_REL, "2f45240f49640c663ed43d88fc01958cf4ee4ad8c04748a192ebbbfbd2f11c96")])
MATERIAL_PIN = collections.OrderedDict([
    (u"書類の本数", 67), (u"書類の file 名の並びの sha256", "f240150645a9b05a8d9bf5a9fe0ab89633ae338e42b8cc4d891dc04ca401e3f5"), (u"開発の 5 本の番号", [1, 2, 3, 4, 5]),
    (u"標準ラベルの file の sha256", list(SG.LAB_SHAS)), (u"道具の版", "2.47.5"), (u"道具 P の ModelValue.py の sha256", "fd9b0d08bf283452fe4ebd6ec9de2f273010de0420b70e61c993a6c033814635"),
    (u"道具 P の package の一覧の sha256", "51e7d2857de748b879e21995908efe50a9350041596e1cd73bef7aac595004a1"), (u"Python の版(道具 P)", "Python 3.11.17"), (u"規則の年", "EDINET-2026"), (u"時間の上限(秒)", 600)])
STEP_TEXT = u"XJ0(入力の型(第 1 版)を字で決め、会社の AI に渡す指示書と、型どおりでない file を理由つきで断る受け口の検査を作る)(0 USD・engine は読まない)"

DEV_COUNT, DOC67, PROD_COUNT = 5, 67, 62
K_DOCS, K_SUM = u"書類", u"集計"
G_DEV, G_PROD, G_ALL = u"開発の 5 本", u"本番だけの 62 本", u"全部"
GROUPS = (G_DEV, G_PROD, G_ALL)
PRED_KEY = u"予測の判定に要る数(XJ0-1〜XJ0-10。当たり・外れは結果の文書で)"
IDS = tuple(u"XJ0-%d" % i for i in range(1, 11))
STAGES = (u"起こす", u"受け口", u"型から作る", u"組む", u"道具")
REASONS = (u"a", u"b", u"c", u"d", u"e", u"f", u"g", u"h")
RULES = tuple(SG.RULE_IDS)
BREAKS = tuple(SG.BREAK_IDS_HAND)
CHANGES = tuple(SG.CHANGE_IDS_HAND)
BREAK_KEYS = (u"作れた", u"断った", u"ちょうど 1 つ", u"別の規則で断った", u"断らなかった")
DOC_KEYS = (u"番号", u"断った", u"断った段", u"断った理由", u"対象の fact", u"型に入った fact", u"型の外の fact", u"型の行", u"独自の名", u"名の数", u"受け口", u"比べ方 1", u"比べ方 2", u"壊し方",
            u"形は合っているが中身が違う", u"秒")
FACT_KEYS = (u"数", u"文")
TGT_KEYS = (u"数", u"文", u"隠し", u"脚注")
ROW_KEYS = (u"数", u"文", u"2 つ以上の fact をまとめた行", u"値が -0 の行", u"期の表に無い期間の行", u"他: の単位の行")
NAME_KINDS = (u"科目", u"軸", u"member")
NAME_CLASS = (u"辞書の在る接頭辞", u"辞書の無い _cor の接頭辞", u"提出者別")
CMP1 = (u"属性が意味として同じ", u"文脈の名も同じ", u"違った fact", u"属性ごとの違った fact")
CMP2 = (u"組めた", u"fact が意味として同じ", u"字も含めて行が同じ", u"鳴り方が同じ", u"2 回が同じ")
ACC_KEYS = (u"受理した", u"断った", u"断りの数", u"規則ごとの断りの数", u"規則ごとの断った書類", u"規則と欄ごとの断りの数")
GROUP_KEYS = (u"書類", u"断った書類", u"断った段と理由ごと", u"型の外の fact が 0 の書類", u"数", u"期の表に無い期間の行が在る書類", u"他: の単位の行が在る書類", u"型から作る命令の秒の合計")
NUM_KEYS = (u"断った", u"対象の fact", u"型に入った fact", u"型の外の fact", u"型の行", u"独自の名", u"名の数", u"受け口", u"比べ方 1", u"比べ方 2", u"壊し方", u"形は合っているが中身が違う")
TOP_KEYS = [u"seal", u"封の commit", u"step", u"この script の sha256", u"材料", u"script の決めの字", K_DOCS, K_SUM, PRED_KEY, u"限界"]
PK = (u"XJ0-1 起こした file を受け口が受理した書類", u"XJ0-2 1 本でも断った規則", u"XJ0-3 型の外の fact", u"XJ0-4 型の外の fact が 0 の書類", u"XJ0-5 道具が読む fact が意味として同じ書類",
      u"XJ0-6 壊し方で断った file", u"XJ0-7 壊し方でちょうど 1 つ", u"XJ0-8 形は合っているが中身が違う file を通した", u"XJ0-9 辞書の無い _cor の接頭辞の科目の名", u"XJ0-10 期の表に無い期間の行が在る書類")

# 封の字(封の門が script と照らし、ここでは文書が引く字の在り処を縛る)
CAND_CORES = (u"受け口が断った規則を読み、型の第 2 版を決める", u"型から本文の表示の字と表も作り、持ち込みを減らす", u"を辞書に足し、受け口の規則 R11〜R13 を「file の中の揃い」から「辞書との照らし」に替える",
              u"会社の AI の席に指示書を渡し、XBRL でない資料から型の file を書かせ、受け口に掛ける", u"組み替えの監査")
CAND_SEAL_FRAGS = ((u"受け口が断った規則を読み、型の第 2 版を決める", u"起こした file を断った規則が 1 つでも在る時"), (u"型から本文の表示の字と表も作り、持ち込みを減らす", u"(費用は 0)"),
                   (u"標準の表の名の性質", u"を辞書に足し、受け口の規則 R11〜R13 を「file の中の揃い」から「辞書との照らし」に替える", u"費用は 0"),
                   (u"会社の AI の席に指示書を渡し、XBRL でない資料から型の file を書かせ、受け口に掛ける", u"有料", u"別の封と、払う前の知らせが先", u"材料は人間の決め"), (u"組み替えの監査", u"人間の決めで後"))
IV_FRAGS = (u"有料", u"別の封", u"払う前の知らせ", u"人間の決め")
# 封 §6 の読み方の決め: (封に在る字, 文書の頭に在る字)
READ_PAIRS = (
    (u"「会社の AI がこの型で書ける」「AI が指示書に従う」とは読まない", u"「会社の AI がこの型で書ける」「AI が指示書に従う」とは読まない"),
    (u"受け口が断らないことは、中身が正しいことではない", u"受け口は、形が合っていれば中身の違う数を通す"),
    (u"会計ソフトの数から型の行への組み替え(どの数をどの科目・どの期間・どの対象に置くか)が正しいかは、この便の受け口では見えない", u"会計ソフトの数から型の行への組み替え(どの数をどの科目・どの期間・どの対象に置くか)が正しいかは、この便の受け口では見えない"),
    (u"「途中の監査は後でいい」", u"「途中の監査は後でいい」"),
    (u"持ち込み(素の本文・fact の置き場・どの置き場がどの数か・文の中身・脚注・提出者別タクソノミの表)はこの便でも作っていない", u"持ち込み(素の本文・fact の置き場・どの置き場がどの数か・文の中身・脚注・提出者別タクソノミの表)はこの便でも作っていない"),
    (u"規則 R8・R9・R11・R12・R13・N5・D3 は 67 本の受理済みの有報から置いた規則で、ほかの種類の書類・ほかの年で成り立つかは測っていない。標準の辞書は名が在るかだけで、名の性質は見ていない。辞書の年と書類の年が合っているかは見ていない",
     u"規則 R8・R9・R11・R12・R13・N5・D3 は 67 本の受理済みの有報から置いた規則で、ほかの種類の書類・ほかの年で成り立つかは測っていない。標準の辞書は名が在るかだけで、名の性質は見ていない。辞書の年と書類の年が合っているかは見ていない"),
    (u"道具が読む fact が元と同じでも、EDINET の本物の検査に通ることは言えない", u"道具が読む fact が元と同じでも、EDINET の本物の検査に通ることは言えない"),
    (u"「XBRL を作れる」「専用の道具が要らない」「AI に任せられる」「誤りが無くなる」は、この便からは言えない", u"「XBRL を作れる」「専用の道具が要らない」「AI に任せられる」「誤りが無くなる」は、この便からは言えない"))
# 文書の頭の限界 5 本(封 §7)。1 本ごとに、封の限界と文書の頭の 1 つの行の両方に在る断片で縛る
LIMIT_FRAGS = (
    (u"便 XM0 の限界の全部(67 本は無作為でない・有報だけ・62 本は未使用でない・道具 P は本家の版でない・", u"持ち込みは作っていない・型は答えから起こした・文の fact の中身は持ち込み・対象の `既定` は連結とは限らない"),
    (u"AI は呼んでいない。指示書が AI に伝わるか・AI がそのとおりに書くかは測っていない。",),
    (u"壊し方は 1 か所ずつ・最初の当てはまる所だけ・この封の表に在る 44 通りだけ。2 か所以上を同時に壊した file・表に無い壊れ方は測っていない。規則と壊し方は同じ席が書いた。",),
    (u"受け口の規則の一部は開発の 5 本を見て置いた。型の広げ方(期間・単位)は実物を見ずに決めた。",),
    (u"標準の辞書は 3 つの接頭辞だけ。ほかの `_cor` の接頭辞の名は形しか見ていない。",))
HEAD_PHRASES = (u"先に負けと限界を書く", u"記録から 1 つずつ読んだもの", u"記録に欄の無い読み", u"予測 1 本は外れ", u"外れは XJ0-6", u"当たり 9・外れ 1", u"良い知らせではない", u"穴の大きさ",
                u"受け口は、形が合っていれば中身の違う数を通す", u"会社の AI が書いたものではない", u"AI は 1 回も呼んでいない", u"受理済みの書類から起こしたもの", u"「会社の AI がこの型で書ける」「AI が指示書に従う」とは読まない",
                u"起こす命令が 1 本を断った", u"断った 1 本の fact は、記録の「62 本」の数に入っていない", u"型の file になった 61 本の分", u"型の外の fact は 0 ではない", u"1 つも作れなかった",
                u"断りが 2 つ以上付いた", u"「規則が正しい」ことではない", u"62 本は未使用ではない", u"盲検ではない", u"「未見で当てた」とは言わない", u"作りから当たりやすい", u"費用は 0", u"engine(`core/`・`adapters/`)は 0 行",
                u"日付つきの補足", u"指示書の「表示の位」と位取りの欄の意味の 2 行は、実装の席が足した", u"封は直していない", u"XJ0-6 の外れの中身", u"作りから「ちょうど 1 つ」にならない", u"受け口の限界(封 D4 の字どおり)", u"作りから黙る変異が在る", u"型が足りないことの裏返し",
                u"途中の監査は後でいい", u"言えない")
PHRASES = (u"封も予測も結果を見てから書き換えていない", u"判定は丸める前の数でした", u"予測の判定には使わない", u"測った数ではない", u"独立監査 REVISE → 直し → REVISE → 直し → GO", u"独立監査 GO",
           u"次の便の候補", u"封 §6 に在るものだけ", u"記録に欄の無い読み")
MAIN_CLAIMS = (u"予測 1 本は外れ", u"良い知らせではない", u"穴の大きさ", u"AI は 1 回も呼んでいない", u"受理済みの書類から起こしたもの", u"型の外の fact は 0 ではない", u"1 つも作れなかった",
               u"封は直していない", u"「規則が正しい」ことではない", u"「未見で当てた」とは言わない", u"断りが 2 つ以上付いた", u"当たり 9・外れ 1", u"外れは XJ0-6", u"受け口は、形が合っていれば中身の違う数を通す",
               u"会社の AI が書いたものではない", u"起こす命令が 1 本を断った", u"断った 1 本の fact は、記録の「62 本」の数に入っていない", u"型の file になった 61 本の分", u"作りから当たりやすい",
               u"この型の file は、受理済みの書類から起こしたもの", u"1 つも断らなかったものは 0", u"断った規則は 0 だったので、この条件には当たらない", u"受け口は file を断っている", u"規則が効くことは壊し方の側の数")
QUOTED = re.compile(u"「[^」]*(?:作れる|専用の道具が要らない|任せられる|誤りが無くなる|書ける|従う|検査に通る)[^」]*」")
AFFIRM_WORDS = (u"作れる(?!か)", u"作れます", u"専用の道具が要らない", u"任せられる", u"誤りが無くなる", u"書ける(?!か)", u"従う", u"検査に通る(?!こと|か)")
MISREAD = re.compile(u"中身(?:の違い|が違う|の違う)[^。|]*?(?:断る|断れる|断られる|見つけ|検出|弾く)")
FORBIDDEN_WORDS = tuple(WG.FORBIDDEN_WORDS)
STRUCTURAL = WG.STRUCTURAL
# 記録から組んだ値の外に在ってよい数(字で留める。封の境・文書の見出しや説明の数)。理由は 1 つずつ:
#   1〜10 = 項の番号・「1 つ」「2 つ」などの小さい数・各行の端数 / 52 3 0.2 5 85 95 4 8 = 封 §4 の境(予測の字の要約と本文) / 62 67 5 = 書類の数の見出し / 44 24 38 = 通り・規則の数(記録・script から別に導く)
RESIDUAL_OK = set([u"0.2", u"52", u"85", u"95", u"4", u"8", u"62", u"67", u"44", u"24", u"38"])
SEC3_LINES = (
    (u"**断った 1 本**", (u"1", u"2", u"1", u"1")),
    (u"**型の外の fact**", (u"2", u"1")),
    (u"**XJ0-6 の 1 個**", (u"1", u"2")),
    (u"**N3a の「ちょうど 1 つ」でない分**", (u"1", u"2")),
    (u"**N5a・N5b**", ()),
    (u"**R4a**", (u"0", u"1", u"2")),
    (u"**比べ方 2 は、監査の席が自分では比べ直していない。**", (u"2", u"1")),
    (u"**61 に満たない欄**", (u"61",)))
SEC3_ONLY_PHRASES = (u"2 通り在った", u"持てない", u"2 つの類だけだった", u"format が無い隠しの数", u"表示の字が数字だけでない数", u"科目の数の行が 2 行だけの書類", u"字の昇順で先の単位を残す",
                     u"狙った行でなく前の行を断った", u"同じ提出者別の科目を使う行", u"辞書に無い名にもなるので N2 が重なる", u"次元の数は全部 0 か 1", u"道具の出力が残っていなかった",
                     u"自分では比べ直していない", u"61 に満たない欄")      # §3 の外に主張として出てはならない字
SEC3_PHRASES = (u"記録の監査の席が、書類ごとに残した folder と元の包みを自分の実装で読んだ読み", u"記録の欄には無い", u"会社の名・書類の番号の外の身元・要素の名は書かない",
                u"当期の始まりの日が、既定の側と個別の側とで 2 通り在った", u"当期の終わりの日と提出日は 1 通り", u"当期の始まりを 1 つしか持てない", u"同じ書類が同じ理由で断られた",
                u"script の欠陥ではなく、封の決めどおりで、型の限界である", u"2 つの類だけだった", u"format が無い隠しの数(受理した書類に 1 個ずつ)",
                u"表示の字が数字だけでない数(理由 (e) と (f) の両方に数える)", u"合計が理由ごとの足し算より小さいのは、封の「重ねて数える」のため",
                u"壊し方 R12a で、科目の数の行が 2 行だけの書類", u"規則 R12 は多い側を残す決めで同数の時は字の昇順で先の単位を残すので、狙った行でなく前の行を断った",
                u"同じ規則が別の行を断ったもので、記録の欄の名「別の規則で断った」は中身と合っていない", u"受け口は file を断っている",
                u"同じ提出者別の科目を使う行が 2 行以上在り、行ごとに断りが出た", u"標準の名の末尾を変えると、辞書に無い名にもなるので N2 が重なる",
                u"型に入った行の次元の数は全部 0 か 1 で、2 つ以上の行が無い", u"封が先に書いた「作れない」場合に当たる",
                u"道具の出力が残っていなかった", u"記録の欄の読みだけである", u"比べ方 1 は自分の実装で比べ直し、意味の差は無かった",
                u"文脈の名・行の字・鳴り方が元と違う書類は、期の表に無い期間の行が在る書類と `他:` の単位の行が在る書類だった")      # §3 の中の向きの語・言い切りの形を決める言い回し


# ======================================================================================================
class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)
        self.cache = {}

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.doc = self.doc
        c.seal = self.seal
        c.shas = collections.OrderedDict(self.shas)
        c.cache = {}
        return c

    def with_doc(self, doc):
        u"""文書だけ替えた写し(記録・組み直しの記憶は共有。文書の変異用。記録は変えない)。"""
        c = Ctx.__new__(Ctx)
        c.rec, c.seal, c.shas, c.cache = self.rec, self.seal, self.shas, self.cache
        c.doc = doc
        return c


def norm(o):
    return json.loads(json.dumps(o, ensure_ascii=False))


def plain(s):
    return s.replace(u"**", u"")


def f(a, b):
    if b == 0:
        return u"%d/%d(―)" % (a, b)
    return u"%d/%d(%s%%)" % (a, b, pct(a, b))


def pct2(n, d):
    u"""n/d の % を小数第 2 位まで四捨五入(0.5 は上げる)した字(整数で)。"""
    return u"%.2f" % (((20000 * n + d) // (2 * d)) / 100.0)


def f2(a, b):
    return u"%d/%d(%s%%)" % (a, b, pct2(a, b))


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def tsum(trees):
    u"""同じ形の木の列 → 葉を足した木(鍵は和集合。真偽は 1/0 で足す。script の関数を使わない別の足し方)。"""
    out = collections.OrderedDict()
    keys = []
    for t in trees:
        for k in t:
            if k not in keys:
                keys.append(k)
    for k in keys:
        vs = [t[k] for t in trees if k in t]
        out[k] = tsum(vs) if isinstance(vs[0], dict) else sum(int(v) for v in vs)
    return out


def agg_of(docs):
    u"""書類の並び → 集計の 1 組(script の group_totals と別に書いた)。"""
    body = [collections.OrderedDict((k, d[k]) for k in NUM_KEYS[1:]) for d in docs]
    num = tsum(body) if body else collections.OrderedDict()
    new = collections.OrderedDict()
    new[NUM_KEYS[0]] = sum(1 for d in docs if d[u"断った"])
    for k in NUM_KEYS[1:]:
        new[k] = num[k]
    reasons = collections.Counter((d[u"断った段"], d[u"断った理由"]) for d in docs if d[u"断った"])
    stage = collections.OrderedDict((s, collections.OrderedDict(sorted((r, n) for (st, r), n in reasons.items() if st == s))) for s in STAGES)
    out = collections.OrderedDict()
    out[u"書類"] = len(docs)
    out[u"断った書類"] = sum(1 for d in docs if d[u"断った"])
    out[u"断った段と理由ごと"] = stage
    out[u"型の外の fact が 0 の書類"] = sum(1 for d in docs if not d[u"断った"] and d[u"型の外の fact"][u"合計"][u"数"] + d[u"型の外の fact"][u"合計"][u"文"] == 0)
    out[u"数"] = new
    out[u"期の表に無い期間の行が在る書類"] = sum(1 for d in docs if d[u"型の行"][u"期の表に無い期間の行"] >= 1)
    out[u"他: の単位の行が在る書類"] = sum(1 for d in docs if d[u"型の行"][u"他: の単位の行"] >= 1)
    out[u"型から作る命令の秒の合計"] = round(sum((d[u"秒"][u"型から作る命令"] or 0) for d in docs), 1)
    return out


def split_docs(rec):
    docs = rec[K_DOCS]
    return [d for d in docs if d[u"番号"] <= DEV_COUNT], [d for d in docs if d[u"番号"] > DEV_COUNT]


def leaves(o):
    if isinstance(o, dict):
        for v in o.values():
            for x in leaves(v):
                yield x
    else:
        yield o


def doc_problems(d):
    u"""書類 1 本の中の関係(足し算・大小・断った書類の形)。"""
    out = []
    n = d.get(u"番号")
    if list(d) != list(DOC_KEYS):
        return [u"書類 %s の欄が違う" % n]
    if d[u"断った"] != bool(d[u"断った段"]) or d[u"断った"] != bool(d[u"断った理由"]) or (d[u"断った"] and d[u"断った段"] not in STAGES):
        out.append(u"書類 %d の断った・段・理由の形が違う" % n)
    for k in (u"対象の fact", u"型に入った fact", u"型の外の fact", u"型の行", u"独自の名", u"名の数", u"受け口", u"比べ方 1", u"比べ方 2", u"壊し方", u"形は合っているが中身が違う"):
        if not isinstance(d[k], dict):
            return out + [u"書類 %d の %s が object でない" % (n, k)]
    if list(d[u"対象の fact"]) != list(TGT_KEYS) or list(d[u"型に入った fact"]) != list(FACT_KEYS) or list(d[u"型の行"]) != list(ROW_KEYS):
        return out + [u"書類 %d の fact・行の欄の並びが違う" % n]
    if list(d[u"型の外の fact"]) != [u"理由ごと", u"合計"] or list(d[u"型の外の fact"][u"理由ごと"]) != list(REASONS) or list(d[u"型の外の fact"][u"合計"]) != list(FACT_KEYS):
        return out + [u"書類 %d の型の外の fact の欄の並びが違う" % n]
    if list(d[u"壊し方"]) != list(BREAKS) or list(d[u"形は合っているが中身が違う"]) != list(CHANGES) or list(d[u"受け口"]) != list(ACC_KEYS):
        return out + [u"書類 %d の壊し方・変え方・受け口の欄の並びが違う" % n]
    a = d[u"受け口"]
    if list(a[u"規則ごとの断りの数"]) != list(RULES) or list(a[u"規則ごとの断った書類"]) != list(RULES):
        return out + [u"書類 %d の規則の並びが違う" % n]
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in leaves(dict((k, d[k]) for k in (u"対象の fact", u"型に入った fact", u"型の外の fact", u"型の行", u"独自の名", u"名の数")))):
        return out + [u"書類 %d に負の数か整数でない値が在る" % n]
    o, t, tg = d[u"型の外の fact"][u"合計"], d[u"型に入った fact"], d[u"対象の fact"]
    for k in FACT_KEYS:
        if o[k] + t[k] != tg[k]:
            out.append(u"書類 %d の 型に入った + 型の外 が対象の fact と違う(%s)" % (n, k))
        if max(d[u"型の外の fact"][u"理由ごと"][r][k] for r in REASONS) > o[k]:
            out.append(u"書類 %d の理由ごとの数が合計より多い(%s)" % (n, k))
    if a[u"受理した"] and a[u"断った"]:
        out.append(u"書類 %d が受理されて断られてもいる" % n)
    if a[u"断った"] != (a[u"断りの数"] >= 1) or sum(a[u"規則ごとの断りの数"].values()) != a[u"断りの数"] or any((x >= 1) != bool(a[u"規則ごとの断った書類"][r]) for r, x in a[u"規則ごとの断りの数"].items()):
        out.append(u"書類 %d の受け口の断りの数が合わない" % n)
    if d[u"断った"]:
        if any(x != 0 for x in leaves({k: d[k] for k in (u"対象の fact", u"型に入った fact", u"型の外の fact", u"型の行", u"独自の名", u"名の数")})) or a[u"受理した"]:
            out.append(u"書類 %d(断った書類)に fact・行・名・受理が在る" % n)
    else:
        if not a[u"受理した"] and not a[u"断った"]:
            out.append(u"書類 %d は断った書類でないのに、受け口が受理も断りもしていない" % n)
    for k, v in d[u"壊し方"].items():
        if list(v) != list(BREAK_KEYS):
            return out + [u"書類 %d の壊し方 %s の欄が違う" % (n, k)]
        if v[u"断った"] + v[u"別の規則で断った"] + v[u"断らなかった"] != v[u"作れた"] or v[u"ちょうど 1 つ"] > v[u"断った"]:
            out.append(u"書類 %d の壊し方 %s の数が合わない" % (n, k))
        if v[u"作れた"] and not a[u"受理した"]:
            out.append(u"書類 %d は受理していないのに壊し方 %s が在る" % (n, k))
    for k, v in d[u"形は合っているが中身が違う"].items():
        if list(v) != [u"作れた", u"通した", u"断った"] or list(v[u"断った"]) != list(RULES):
            return out + [u"書類 %d の変え方 %s の欄が違う" % (n, k)]
        if v[u"通した"] + sum(v[u"断った"].values()) != v[u"作れた"]:
            out.append(u"書類 %d の変え方 %s の 通した + 断った が作れたと違う" % (n, k))
    c1, c2 = d[u"比べ方 1"], d[u"比べ方 2"]
    if list(c1) != list(CMP1) or list(c2) != list(CMP2):
        return out + [u"書類 %d の比べ方の欄が違う" % n]
    if (c1[u"属性が意味として同じ"] or c2[u"組めた"]) and not a[u"受理した"]:
        out.append(u"書類 %d は受理していないのに比べ方の結果が在る" % n)
    if (c1[u"文脈の名も同じ"] and not c1[u"属性が意味として同じ"]) or (c2[u"fact が意味として同じ"] and not c2[u"組めた"]):
        out.append(u"書類 %d の比べ方の大小が違う" % n)
    return out


def sum_over(rec, key, sub=None, group=G_PROD):
    v = rec[K_SUM][group][u"数"][key]
    return v if sub is None else v[sub]


def pred_numbers(rec):
    u"""本番だけの 62 本の書類から、XJ0-1〜XJ0-10 に要る数を導く(整数・script の関数を使わない)。"""
    docs = split_docs(rec)[1]
    g = agg_of(docs)
    z = g[u"数"]
    acc = z[u"受け口"]
    brk = z[u"壊し方"]
    chg = z[u"形は合っているが中身が違う"]
    s = lambda key: sum(v[key] for v in brk.values())          # noqa: E731
    cor = z[u"名の数"][u"科目"]
    qrules = collections.OrderedDict((r, sum(v[u"断った"][r] for v in chg.values())) for r in RULES)
    return collections.OrderedDict([
        (u"XJ0-1", (acc[u"受理した"], g[u"書類"])),
        (u"XJ0-2", (sum(1 for x in acc[u"規則ごとの断った書類"].values() if x >= 1),)),
        (u"XJ0-3", (z[u"型の外の fact"][u"合計"][u"数"] + z[u"型の外の fact"][u"合計"][u"文"], z[u"対象の fact"][u"数"] + z[u"対象の fact"][u"文"])),
        (u"XJ0-4", (g[u"型の外の fact が 0 の書類"], g[u"書類"])),
        (u"XJ0-5", (z[u"比べ方 2"][u"fact が意味として同じ"], acc[u"受理した"])),
        (u"XJ0-6", (s(u"断った"), s(u"作れた"), s(u"別の規則で断った"), s(u"断らなかった"))),
        (u"XJ0-7", (s(u"ちょうど 1 つ"), s(u"作れた"))),
        (u"XJ0-8", (sum(v[u"通した"] for v in chg.values()), sum(v[u"作れた"] for v in chg.values()), qrules)),
        (u"XJ0-9", (cor[u"辞書の無い _cor の接頭辞"], sum(cor.values()))),
        (u"XJ0-10", (g[u"期の表に無い期間の行が在る書類"], g[u"書類"]))])


def judge_nums(p):
    u"""封 §4 の境(整数のまま)。p は pred_numbers の形。値は (当たりか, 外れた向き)。"""
    O = collections.OrderedDict
    out = O()
    a, b = p[u"XJ0-1"]
    out[u"XJ0-1"] = (a >= 52, u"" if a >= 52 else u"下")
    n = p[u"XJ0-2"][0]
    out[u"XJ0-2"] = (n <= 3, u"" if n <= 3 else u"上")
    a, b = p[u"XJ0-3"]
    ok = b > 0 and 1000 * a <= 2 * b
    out[u"XJ0-3"] = (ok, u"" if ok else u"上")
    a, b = p[u"XJ0-4"]
    out[u"XJ0-4"] = (a <= 5, u"" if a <= 5 else u"上")
    a, b = p[u"XJ0-5"]
    if b == 0:
        out[u"XJ0-5"] = (False, u"判定できない")
    else:
        out[u"XJ0-5"] = (a == b, u"" if a == b else u"下")
    cut, made, other, none = p[u"XJ0-6"]
    ok = made > 0 and cut == made
    out[u"XJ0-6"] = (ok, u"" if ok else (u"断らなかった" if none > 0 else u"別の規則で断った"))
    a, b = p[u"XJ0-7"]
    ok = b > 0 and 100 * a >= 85 * b
    out[u"XJ0-7"] = (ok, u"" if ok else u"下")
    a, b = p[u"XJ0-8"][0], p[u"XJ0-8"][1]
    ok = b > 0 and 100 * a >= 95 * b
    out[u"XJ0-8"] = (ok, u"" if ok else u"下")
    a, b = p[u"XJ0-9"]
    lo, hi = b > 0 and 100 * a >= 4 * b, b > 0 and 100 * a < 8 * b
    out[u"XJ0-9"] = (lo and hi, u"" if lo and hi else u"下" if not lo else u"上")
    a, b = p[u"XJ0-10"]
    out[u"XJ0-10"] = (a <= 3, u"" if a <= 3 else u"上")
    return out


def judge(rec):
    return judge_nums(pred_numbers(rec))


def miss_ids(j):
    return [k for k in IDS if not j[k][0]]


def pred_expected(rec):
    u"""記録の予測の欄の形(当たり外れは持たない)を、書類ごとから作り直す。"""
    O = collections.OrderedDict
    p = pred_numbers(rec)
    out = O()
    a, b = p[u"XJ0-1"]
    out[PK[0]] = O([(u"書類", a), (u"分母", b)])
    n = p[u"XJ0-2"][0]
    prod = agg_of(split_docs(rec)[1])[u"数"][u"受け口"][u"規則ごとの断った書類"]
    out[PK[1]] = O([(u"規則の数", n), (u"規則ごとの断った書類", O(prod))])
    a, b = p[u"XJ0-3"]
    out[PK[2]] = O([(u"fact", a), (u"分母(対象の fact)", b)])
    a, b = p[u"XJ0-4"]
    out[PK[3]] = O([(u"書類", a), (u"分母", b)])
    a, b = p[u"XJ0-5"]
    out[PK[4]] = O([(u"書類", a), (u"分母(受理した書類)", b)])
    cut, made, other, none = p[u"XJ0-6"]
    out[PK[5]] = O([(u"断った", cut), (u"作れた", made), (u"別の規則で断った", other), (u"断らなかった", none)])
    a, b = p[u"XJ0-7"]
    out[PK[6]] = O([(u"ちょうど 1 つ", a), (u"分母(作れた)", b)])
    a, b, q = p[u"XJ0-8"]
    out[PK[7]] = O([(u"通した", a), (u"作れた", b), (u"断った(規則ごと)", q)])
    a, b = p[u"XJ0-9"]
    out[PK[8]] = O([(u"名", a), (u"分母(科目の名)", b)])
    a, b = p[u"XJ0-10"]
    out[PK[9]] = O([(u"書類", a), (u"分母", b)])
    return out


def recount_problems(c):
    rec = c.rec
    out = []
    if list(rec) != TOP_KEYS:
        return [u"記録の欄の並びが違う"]
    docs = rec[K_DOCS]
    m = rec[u"材料"]
    nums = [d.get(u"番号") for d in docs]
    if len(docs) != DOC67 or nums != list(range(1, DOC67 + 1)):
        return [u"書類の番号が 1〜67 の昇順でない"]
    for k, v in MATERIAL_PIN.items():
        if m.get(k) != v:
            out.append(u"材料の欄が字で留めた値と違う: %s" % k)
    if list(m) != list(MATERIAL_PIN):
        out.append(u"材料の欄の並びが違う")
    for d in docs:
        out.extend(doc_problems(d))
    if list(rec[K_SUM]) != list(GROUPS):
        return out + [u"集計の欄の名が違う"]
    dev, prod = split_docs(rec)
    if len(dev) != DEV_COUNT or len(prod) != PROD_COUNT:
        return out + [u"開発の 5 本と本番だけの 62 本の分けが違う"]
    for key, ds in ((G_DEV, dev), (G_PROD, prod), (G_ALL, docs)):
        if list(rec[K_SUM][key]) != list(GROUP_KEYS):
            out.append(u"%s の集計の欄の並びが違う" % key)
        elif norm(rec[K_SUM][key]) != norm(agg_of(ds)):
            out.append(u"%s の集計が書類ごとの数から数え直した値と違う" % key)
    if list(rec[PRED_KEY]) != list(PK):
        return out + [u"予測の判定に要る数の欄の名が違う"]
    if norm(rec[PRED_KEY]) != norm(pred_expected(rec)):
        out.append(u"予測の判定に要る数が書類ごとから作り直した値と違う")
    return out


def sha_problems(c):
    out = []
    for rel, want in SHA_PIN.items():
        if c.shas[rel] != want:
            out.append(u"sha256 が字で留めた値と違う: %s" % rel)
    if c.rec[u"この script の sha256"] != SHA_PIN[SCRIPT_REL]:
        out.append(u"記録の script の sha256 が script と違う")
    if (c.rec[u"seal"], c.rec[u"封の commit"]) != (SEAL_REL, SEAL_COMMIT_SHORT):
        out.append(u"記録の封の欄が違う")
    if c.rec[u"限界"] != MS.LIMITS:
        out.append(u"記録の限界の欄が script の字と違う")
    if c.rec[u"step"] != STEP_TEXT:
        out.append(u"記録の step の欄が違う")
    d = c.rec[u"script の決めの字"]
    if (d[u"型の版"], d[u"規則の番号"], d[u"壊し方"], d[u"変え方"], d[u"型の外の理由"], d[u"辞書の在る接頭辞"], d[u"format"], d[u"桁あふれの守り"]) != (
            u"1", list(RULES), list(BREAKS), list(CHANGES), list(REASONS), [u"jppfs_cor", u"jpcrp_cor", u"jpigp_cor"], u"ixt:numdotdecimal", 1000):
        out.append(u"記録の script の決めの字が封の字(門の手の表)と違う")
    return out


DATE_FORM = re.compile(r"(?<![0-9])(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?![0-9])|(?<![0-9])(?:19|20)\d{2}年\d{1,2}月")


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    out = []
    try:
        MS.verify_record(c.rec)
    except BaseException as exc:                    # noqa: BLE001
        out.append(u"記録の検査(形・合計・禁止のもの)が止める: %s" % type(exc).__name__)
    if WG.DOCID_FORM.search(re.sub(r"[0-9a-fA-F]{32,}", u"", text)) or WG.ECODE_FORM.search(text):
        out.append(u"記録に docid か EDINET コードの形が在る")
    if DATE_FORM.search(text.replace(SEAL_REL, u"")):
        out.append(u"記録に日付の形が在る(封 §3 は日付を持たないと決めた。門が見る)")
    return out


def seal_s6_text(seal):
    return section(seal, u"## §6 ", u"## §7 ")


def seal_cand_lines(seal):
    return [ln for ln in seal_s6_text(seal).splitlines() if re.match(u"^  - \\((?:i|ii|iii|iv|v|vi|vii)\\) ", ln)]


def bound_problems(c):
    ps = plain(c.seal)
    out = []
    for k, pair in SG.SEAL_BOUND_TEXT.items():
        for p in pair:
            if p not in c.seal and plain(p) not in ps:
                out.append(u"封に字が無い: %s" % p[:24])
    for p, _d in READ_PAIRS:
        if p not in c.seal and plain(p) not in ps:
            out.append(u"封 §6 の読み方の字が無い: %s" % p[:24])
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    rows = [ln for ln in sec4.splitlines() if re.match(r"^\| XJ0-\d", ln)]
    if len(rows) != 10:
        out.append(u"封 §4 の表の行が 10 でない")
    for k, pair in SG.SEAL_BOUND_TEXT.items():
        srow = [x for x in rows if re.match(r"^\| %s(?!\d)" % re.escape(k), x)]
        if len(srow) != 1 or any(x not in srow[0] for x in pair):
            out.append(u"封 §4 の %s の行に境の字が無い" % k)
    sec7 = section(c.seal, u"## §7 ", None)
    lim7 = [ln[2:] for ln in sec7.splitlines() if ln.startswith(u"- ")]
    if len(lim7) != 5:
        out.append(u"封 §7 の限界の行が 5 行でない")
    for i, (lim, frags) in enumerate(zip(lim7, LIMIT_FRAGS), 1):
        for x in frags:
            if x not in lim:
                out.append(u"封 §7 の %d 本目の限界に門の断片が無い: %s" % (i, x[:12]))
    s6 = seal_s6_text(c.seal)
    cl = seal_cand_lines(c.seal)
    marks = re.findall(u"^  - \\((i|ii|iii|iv|v|vi|vii)\\) ", s6, re.M)
    if marks != [u"i", u"ii", u"iii", u"iv", u"v"]:
        out.append(u"封 §6 の次の便の候補が (i)〜(v) の 5 つだけでない")
    for ln, frags in zip(cl, CAND_SEAL_FRAGS):
        for fr in frags:
            if fr not in ln:
                out.append(u"封 §6 の候補の行に字が無い: %s" % fr[:16])
    return out


# ======================================================================================================
# c 当たり外れの決め直し(封 §4 の境。丸める前の整数。本番だけの 62 本)
PRED_TEXT = collections.OrderedDict([
    (u"XJ0-1", u"起こした file を受け口が受理する書類は 52 本以上"), (u"XJ0-2", u"起こした file を 1 本でも断った規則は 3 つ以下"), (u"XJ0-3", u"型の外の fact は対象の fact の 0.2% 以下"),
    (u"XJ0-4", u"型の外の fact が 0 の書類は 5 本以下"), (u"XJ0-5", u"受理した書類の全部で、道具が読む fact が意味として同じ"), (u"XJ0-6", u"壊し方の全部で、作れた file は全部「断った」"),
    (u"XJ0-7", u"壊した file のうち「ちょうど 1 つ」は作れた file の 85% 以上"), (u"XJ0-8", u"形は合っているが中身が違う file は、作れたものの 95% 以上を受け口が通す"),
    (u"XJ0-9", u"辞書の無い `_cor` の接頭辞の科目の名は、科目の名の 4% 以上 8% 未満"), (u"XJ0-10", u"期の表に無い期間の行が在る書類は 3 本以下")])


def cell_text(rec, key):
    p = pred_numbers(rec)[key]
    if key in (u"XJ0-1", u"XJ0-4", u"XJ0-10"):
        return u"%d 本(%d 本のうち)" % p
    if key == u"XJ0-2":
        return u"%d" % p[0]
    if key == u"XJ0-3":
        return f2(*p)
    if key == u"XJ0-5":
        return u"%d 本(受理した %d 本のうち)" % p
    if key == u"XJ0-6":
        return u"断った %d・作れた %d(別の規則で断った %d・断らなかった %d)" % (p[0], p[1], p[2], p[3])
    if key in (u"XJ0-7", u"XJ0-9"):
        return f(*p)
    return f(p[0], p[1])


def expected_cells(c):
    out = collections.OrderedDict()
    for k, (ok, way) in judge(c.rec).items():
        out[k] = (cell_text(c.rec, k), u"当たり" if ok else u"外れ")
    return out


CAND_LINES_FIXED = (u"- (ii) 型から本文の表示の字と表も作り、持ち込みを減らす(費用は 0)。",
                    u"- (iii) 標準の表の名の性質を辞書に足し、受け口の規則 R11〜R13 を「file の中の揃い」から「辞書との照らし」に替える(費用は 0)。",
                    u"- (iv) 会社の AI の席に指示書を渡し、XBRL でない資料から型の file を書かせ、受け口に掛ける(有料。別の封と、払う前の知らせが先。材料は人間の決め)。",
                    u"- (v) 組み替えの監査(人間の決めで後)。")


def cand_i_line(rec):
    n = pred_numbers(rec)[u"XJ0-2"][0]
    return u"- (i) 受け口が断った規則を読み、型の第 2 版を決める。封は「起こした file を断った規則が 1 つでも在る時」と書いた。断った規則は %d だったので、この条件には%s。" % (
        n, u"当たらない" if n == 0 else u"当たる")


def sec5_problems(c):
    u"""封 §6(次の便の候補は (i)〜(v) の 5 つだけ)と文書 §5 が合う。6 つ目・封に無い候補の字を足すと赤。(i) の条件は記録の断った規則の数に縛る。"""
    out = []
    sec5 = plain(section(c.doc, u"## §5 ", None))
    lines = [ln for ln in sec5.splitlines() if ln.strip()]
    head, body = lines[0], lines[1:]
    if head != u"## §5 次の便の候補(封 §6 に在るものだけ)":
        out.append(u"§5 の見出しが違う")
    if len(body) != 5:
        out.append(u"§5 の候補の行が 5 つでない(足す・引くと赤): %d" % len(body))
    marks = [re.match(u"^- \\((\\w+)\\) ", ln).group(1) if re.match(u"^- \\((\\w+)\\) ", ln) else u"?" for ln in body]
    if marks != [u"i", u"ii", u"iii", u"iv", u"v"]:
        out.append(u"§5 の候補の見出しが (i)(ii)(iii)(iv)(v) の 5 つだけでない: %s" % u",".join(marks))
    if body != [cand_i_line(c.rec)] + list(CAND_LINES_FIXED):
        out.append(u"§5 の候補の行が、封 §6 の (i)〜(v) の字と記録の断った規則の数から組んだ行と違う")
    if sec5.count(u"候補") != 1:
        out.append(u"§5 の「候補」の字の数が違う(封に無い候補の字を足している)")
    for core, ln in zip(CAND_CORES, body):
        if sec5.count(core) != 1 or core not in ln:
            out.append(u"§5 に封 §6 の候補の字が 1 つずつ(その順に)無い: %s" % core[:12])
    n = pred_numbers(c.rec)[u"XJ0-2"][0]
    if len(body) >= 1:
        if (u"断った規則は %d だったので" % n) not in body[0]:
            out.append(u"§5 の (i) が記録の断った規則の数と合わない")
        if n == 0 and u"断った規則は 0 だったので、この条件には当たらない" not in body[0]:
            out.append(u"§5 の (i) に「断った規則は 0 だったので、この条件には当たらない」が無い")
        if n >= 1 and u"当たらない" in body[0]:
            out.append(u"記録の断った規則が 1 以上なのに (i) が「当たらない」と書いている")
    if len(body) >= 4 and any(x not in body[3] for x in IV_FRAGS):
        out.append(u"§5 の (iv) に「有料・別の封・払う前の知らせ・人間の決め」が揃っていない")
    s6 = seal_s6_text(c.seal)
    if re.findall(u"^  - \\((i|ii|iii|iv|v|vi|vii)\\) ", s6, re.M) != [u"i", u"ii", u"iii", u"iv", u"v"]:
        out.append(u"封 §6 の候補が 5 つでない")
    return out


def verdict_problems(c):
    rec = c.rec
    j = judge(rec)
    want = expected_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XJ0-\d+)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XJ0-1〜XJ0-10 でない"]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    for k, cells in rows.items():
        if len(cells) != 3:
            out.append(u"%s の行の欄の数が違う" % k)
            continue
        if cells[0] != PRED_TEXT[k]:
            out.append(u"%s の予測の字が門の留めた要約と違う: %s" % (k, cells[0]))
        srow = [x for x in sec4.splitlines() if re.match(r"^\| %s(?!\d)" % re.escape(k), x)]
        if len(srow) != 1 or any(x not in srow[0] for x in SG.SEAL_BOUND_TEXT[k]):
            out.append(u"%s の境の字が封 §4 の表に無い" % k)
        if cells[1] != want[k][0]:
            out.append(u"%s の実測の字が記録から組んだ字と違う: %s" % (k, cells[1]))
        if cells[2] != want[k][1]:
            out.append(u"%s の判定が決め直した判定と違う: %s(決め直し: %s)" % (k, cells[2], want[k][1]))
    if not re.search(r"^\| XJ0-1\(主\) \|", c.doc, re.M):
        out.append(u"XJ0-1 の行に「(主)」が無い(封 §4 の主の読み)")
    for k in IDS[1:]:
        if re.search(r"^\| %s\(主\) \|" % k, c.doc, re.M):
            out.append(u"%s の行に「(主)」が付いている(封 §4 の主は XJ0-1 だけ)" % k)
    hits = sum(1 for v in j.values() if v[0])
    if u"- 当たり %d・外れ %d。" % (hits, len(j) - hits) not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = plain(c.doc.split(u"## §1")[0])
    miss = miss_ids(j)
    if u"判定した %d 本は 当たり %d・外れ %d。" % (len(j), hits, len(j) - hits) not in head:
        out.append(u"文書の頭の件数が決め直した値と違う")
    if miss:
        if u"予測 %d 本は外れ。 外れは %s。" % (len(miss), u"・".join(miss)) not in head:
            out.append(u"外れた予測の言い切りが文書の頭に無い(%s)" % u"・".join(miss))
    elif re.search(u"予測 [0-9]+ 本は外れ", head):
        out.append(u"外れが無いのに文書の頭が外れと書いている")
    if u"XJ0-1" in miss:
        if u"主の予測(XJ0-1)は外れ" not in head:
            out.append(u"主の予測が外れなのに、文書の頭に「主の予測(XJ0-1)は外れ」が無い")
    elif u"主の予測(XJ0-1)は当たり" not in head or re.search(u"主の予測[^。]*は外れ", head):
        out.append(u"主の予測は当たりなのに文書の頭の書き方が合わない")
    for key, (id_, (ok, way)) in zip(PK, j.items()):
        pass
    # 判定の表に 開発の 5 本・全部 の数が混ざらない(本番だけの 62 本の数だけ)
    only_other = set()
    for key in (G_DEV, G_ALL):
        ints_in(rec[K_SUM][key], only_other)
    only_prod = set()
    ints_in(rec[K_SUM][G_PROD], only_prod)
    ints_in(rec[PRED_KEY], only_prod)
    mixed = [t for ln in rows for t in doc_number_tokens(rows[ln][1]) if t in only_other and t not in only_prod and t not in STRUCTURAL]
    if mixed:
        out.append(u"判定の表に開発の 5 本・全部だけの数が混ざっている: %s" % u",".join(mixed))
    # 記録の変え方の「通した」が 1 以上なら「中身の違いを断る」を肯定しない(0 ならまず自分の欠陥を疑う旗)
    passed = pred_numbers(rec)[u"XJ0-8"][0]
    if passed >= 1:
        for i, ln in enumerate(c.doc.splitlines(), 1):
            if MISREAD.search(QUOTED.sub(u"", ln)):
                out.append(u"記録の変え方の通したは 1 以上なのに、文書の %d 行目が「中身の違いを断る」を肯定している" % i)
    else:
        out.append(u"記録の変え方の通したが 0(まず自分の欠陥を疑う)")
    return out


# ======================================================================================================
# d 文書の数・主な主張の文(§3 以外の全部の行を記録と字から組み直す)
def cached(c, key, fn):
    if key not in c.cache:
        c.cache[key] = fn()
    return c.cache[key]


SPECIAL_ORDER = (u"R4a", u"R8a", u"N3a", u"N5a", u"N5b", u"R12a")          # 文書の表の行の順(字で留める。ふつうでない番号の集まりは記録から導く)


def std_tuple(acc):
    return tuple([acc, acc, acc, 0, 0])


def break_groups(rec):
    u"""壊し方の表: 「ふつう」(作れた = 断った = ちょうど 1 つ = 受理した本数・ほかは 0)でない番号と、ふつうの番号の数。"""
    z = rec[K_SUM][G_PROD][u"数"]
    acc = z[u"受け口"][u"受理した"]
    brk = z[u"壊し方"]
    sp = [k for k in BREAKS if tuple(brk[k][x] for x in BREAK_KEYS) != std_tuple(acc)]
    special = [k for k in SPECIAL_ORDER if k in sp] + [k for k in sp if k not in SPECIAL_ORDER]
    return special, len(BREAKS) - len(special), std_tuple(acc)


def render_pre(c):
    u"""記録(と字で留めた文)から、文書の §3 より前の全部の行を組み直す。"""
    rec = c.rec
    Dv, Pr, Al = rec[K_SUM][G_DEV], rec[K_SUM][G_PROD], rec[K_SUM][G_ALL]
    PN, VN, AN = Pr[u"数"], Dv[u"数"], Al[u"数"]
    j = cached(c, u"judge", lambda: judge(rec))
    hits = sum(1 for v in j.values() if v[0])
    miss = miss_ids(j)
    cells = cached(c, u"cells", lambda: expected_cells(c))
    acc = PN[u"受け口"]
    brk = PN[u"壊し方"]
    chg = PN[u"形は合っているが中身が違う"]
    bs = lambda key: sum(v[key] for v in brk.values())          # noqa: E731
    qs = lambda key: sum(v[key] for v in chg.values())          # noqa: E731
    tgt, tin, out_, rows_ = PN[u"対象の fact"], PN[u"型に入った fact"], PN[u"型の外の fact"], PN[u"型の行"]
    ntot = tgt[u"数"] + tgt[u"文"]
    nrules = pred_numbers(rec)[u"XJ0-2"][0]
    L = []
    w = L.append
    w(u"# 結果: 便 XJ0 ― 入力の型(第 1 版)を字で決め、受理済みの書類から起こした型どおりの file を受け口が断らないか・型だけから XBRL の側が決まるか・壊した file を受け口が断るかを数えた ― 2026-11-23")
    w(u"")
    w(u"封 `%s`(commit %s)。script `%s`・封の門 `%s`・会社の AI 向けの指示書 `%s` は commit %s(独立監査 REVISE → 直し → REVISE → 直し → GO)。"
      u"記録 `%s` は commit %s(独立監査 GO。%d 本を別の実装で数え直し、差は 0)。費用は 0。engine(`core/`・`adapters/`)は 0 行。AI は 1 回も呼んでいない。" % (
          SEAL_REL, SEAL_COMMIT_SHORT, SCRIPT_REL, SEAL_GATE_REL, INSTR_REL, SCRIPT_COMMIT_SHORT, RECORD_REL, RECORD_COMMIT_SHORT, Al[u"書類"]))
    w(u"")
    w(u"この文書の §1・§2 の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録の数と字で同じことを見る)。§3 は記録に欄の無い読みで、出どころを書く。")
    w(u"")
    w(u"**先に負けと限界を書く。**")
    w(u"")
    miss_s = u"・".join(miss)
    w(u"- **予測 %d 本は外れ。** 外れは %s。主の予測(XJ0-1)は%s。判定した %d 本は 当たり %d・外れ %d。" % (len(miss), miss_s, u"外れ" if u"XJ0-1" in miss else u"当たり", len(j), hits, len(j) - hits))
    w(u"- **受け口は、形が合っていれば中身の違う数を通す。** 形は合っているが中身が違う file は %d 個作れて、受け口は %d 個とも通した。"
      u"対象を逆にした数・別の科目に置いた数・1 つ大きい数・符号を逆にした数・1 年前の期間に置いた数・通貨を替えた数を、受け口は 1 つも断らなかった。"
      u"予測(XJ0-8)は当たりだが、良い知らせではない。穴の大きさである。" % (qs(u"作れた"), qs(u"通した")))
    w(u"- **この型の file は、受理済みの書類から起こしたもの。会社の AI が書いたものではない。** AI は 1 回も呼んでいない。指示書を AI が読んだことは無い。"
      u"**「会社の AI がこの型で書ける」「AI が指示書に従う」とは読まない。**")
    w(u"- **起こす命令が %d 本を断った。** 本番だけの %d 本のうち %d 本は、書類の決めが 1 通りに決まらず、型の file にならなかった。第 1 版の型は、この書類を表せない。" % (
        Pr[u"断った書類"], Pr[u"書類"], Pr[u"断った書類"]))
    w(u"- **断った %d 本の fact は、記録の「%d 本」の数に入っていない。** 記録は断った書類の対象の fact を 0 と書く。下の「%d 本」の対象の fact・型の行・名の数は、型の file になった %d 本の分である。" % (
        Pr[u"断った書類"], Pr[u"書類"], Pr[u"書類"], Pr[u"書類"] - Pr[u"断った書類"]))
    w(u"- **型の外の fact は 0 ではない。** 型の外の fact は %s。型の外の fact が 0 の書類は %d 本(%d 本のうち)。第 1 版の型は、型の file になった %d 本の全部で 1 個以上の fact を型の外に残した。" % (
        f2(out_[u"合計"][u"数"] + out_[u"合計"][u"文"], ntot), Pr[u"型の外の fact が 0 の書類"], Pr[u"書類"], Pr[u"書類"] - Pr[u"断った書類"]))
    w(u"- **壊し方 R4a は、本番だけの書類で 1 つも作れなかった。** 規則 R4 のうち R4a が見る枝は、この便の実物では 1 度も試されていない。作り物の file でだけ確かめた(封の門)。")
    w(u"- **壊し方 N5a・N5b は、作れた %d 個ずつの全部で「ちょうど 1 つ」が %d。** 断りが 2 つ以上付いた。直す側は、1 か所の違いに 2 つ以上の断りを受け取る。" % (brk[u"N5a"][u"作れた"], brk[u"N5a"][u"ちょうど 1 つ"]))
    w(u"- **受け口が起こした file を断った規則は %d。** これは「規則が正しい」ことではない。規則の一部は開発の %d 本を見て置き、%d 本は未使用ではない。規則が効くことは壊し方の側の数(下の表)でだけ言える。" % (
        nrules, Dv[u"書類"], Pr[u"書類"]))
    w(u"- 便 XM0 の限界の全部(67 本は無作為でない・有報だけ・62 本は未使用でない・道具 P は本家の版でない・`.xbrl` を落とした包み・持ち込みは作っていない・型は答えから起こした・文の fact の中身は持ち込み・対象の `既定` は連結とは限らない)。")
    w(u"- AI は呼んでいない。指示書が AI に伝わるか・AI がそのとおりに書くかは測っていない。")
    w(u"- 壊し方は 1 か所ずつ・最初の当てはまる所だけ・この封の表に在る %d 通りだけ。2 か所以上を同時に壊した file・表に無い壊れ方は測っていない。規則と壊し方は同じ席が書いた。" % len(BREAKS))
    w(u"- 受け口の規則の一部は開発の 5 本を見て置いた。型の広げ方(期間・単位)は実物を見ずに決めた。")
    w(u"- 標準の辞書は 3 つの接頭辞だけ。ほかの `_cor` の接頭辞の名は形しか見ていない。")
    w(u"- 会計ソフトの数から型の行への組み替え(どの数をどの科目・どの期間・どの対象に置くか)が正しいかは、この便の受け口では見えない。そこを見る監査は、人間の決め(2026-11-23「途中の監査は後でいい」)で後に回した。")
    w(u"- 持ち込み(素の本文・fact の置き場・どの置き場がどの数か・文の中身・脚注・提出者別タクソノミの表)はこの便でも作っていない。")
    w(u"- 規則 R8・R9・R11・R12・R13・N5・D3 は 67 本の受理済みの有報から置いた規則で、ほかの種類の書類・ほかの年で成り立つかは測っていない。標準の辞書は名が在るかだけで、名の性質は見ていない。辞書の年と書類の年が合っているかは見ていない。")
    w(u"- 道具が読む fact が元と同じでも、EDINET の本物の検査に通ることは言えない。")
    w(u"- 予測は司令塔が立てた。盲検ではない。XJ0-5・XJ0-6・XJ0-8 は作りから当たりやすいと封に書いた。当たった %d 本を「未見で当てた」とは言わない。" % hits)
    w(u"- **「XBRL を作れる」「専用の道具が要らない」「AI に任せられる」「誤りが無くなる」は、この便からは言えない。**")
    w(u"")
    w(u"**日付つきの補足(2026-11-23。封は書き換えていない)。**")
    w(u"")
    w(u"- **XJ0-6 の外れの中身。** 作れた file %d 個のうち、1 つも断らなかったものは %d。「断った」にならなかった %d 個は、記録の欄では「別の規則で断った」に入る。封の字のとおり外れと判定する。中身の読みは §3。" % (
        bs(u"作れた"), bs(u"断らなかった"), bs(u"作れた") - bs(u"断った")))
    w(u"- **N5a・N5b は作りから「ちょうど 1 つ」にならない。** script の commit(%s)の時点で、開発の 5 本で分かっていた。封は直していない。XJ0-7 は当たりだが、この 2 通りの分は最初から外れる側に入っている。" % SCRIPT_COMMIT_SHORT)
    w(u"- **受け口の限界(封 D4 の字どおり)。** 提出者の識別子に壊れた文字(孤立 surrogate の逃がし書き)が入った file を、受け口は受理する。封は識別子を「空白を含まない 1 字以上」と決めたので、字のとおりの動きである。"
      u"その file から型から作る命令は作れずに止まる。封は直していない。")
    w(u"- **指示書の「表示の位」と位取りの欄の意味の 2 行は、実装の席が足した。** 封は欄の形を決めたが、意味の説明の字は決めていない。")
    w(u"- **封の門に、作りから黙る変異が在る。** 一覧は全部で %d 本。そのうち、監査の 2 回目・3 回目の掃きで、同値として理由つきで残した変え方の分が %d 本(1 回目の直しの %d 本・2 回目の直しの %d 本)。"
      u"ほかに、変え方の「鍵が重ならない」守りの細部は、作り物の file に次元つきの行・個別の行が無いので黙る(監査は止めない扱い)。直していない。" % (
          len(SG.SILENT_BY_DESIGN), len(q_silent()), len(q_silent()) - len(q_silent_h()), len(q_silent_h())))
    w(u"- **XJ0-4 の当たりは、型が足りないことの裏返し。** 封は「型の外の fact が 0 の書類は %d 本以下」と予測した。%d 本だった。" % (5, Pr[u"型の外の fact が 0 の書類"]))
    w(u"")
    w(u"## §1 予測の当たり外れ(司令塔。盲検ではない)")
    w(u"")
    w(u"封 §4 の字の境と記録から、結果の門が XJ0-1〜XJ0-10 の当たり外れを決め直した(この表と同じ)。封も予測も結果を見てから書き換えていない。判定は丸める前の数でした。分母は本番だけの %d 本。開発の %d 本の数は予測の判定には使わない。" % (
        Pr[u"書類"], Dv[u"書類"]))
    w(u"")
    w(u"| # | 予測(封の字の要約) | 実測(記録) | 判定 |")
    w(u"|---|---|---|---|")
    for k in IDS:
        w(u"| %s%s | %s | %s | %s |" % (k, u"(主)" if k == u"XJ0-1" else u"", PRED_TEXT[k], cells[k][0], cells[k][1]))
    w(u"")
    w(u"- 当たり %d・外れ %d。" % (hits, len(j) - hits))
    w(u"")
    w(u"## §2 数(記録)")
    w(u"")
    w(u"材料: 書類 %d 本(開発の %d 本・本番だけの %d 本)。下の数は、断らないかぎり本番だけの %d 本。" % (Al[u"書類"], Dv[u"書類"], Pr[u"書類"], Pr[u"書類"]))
    w(u"")
    stage = [(s, r, n) for s, rs in Pr[u"断った段と理由ごと"].items() for r, n in rs.items()]
    s0, r0 = (stage[0][0], stage[0][1]) if stage else (u"", u"")
    after = sum(n for s, r, n in stage if s != STAGES[0])
    w(u"**断った書類**: %d 本(%d 本のうち)。段は「%s」・理由は「%s」。受け口・型から作る・組む・道具の段で断った書類は %d。" % (Pr[u"断った書類"], Pr[u"書類"], s0, r0, after))
    w(u"")
    w(u"**対象の fact と型**(断った %d 本の分は入っていない):" % Pr[u"断った書類"])
    w(u"")
    w(u"| | 数 | 文 |")
    w(u"|---|---|---|")
    w(u"| 対象の fact | %d | %d |" % (tgt[u"数"], tgt[u"文"]))
    w(u"| 型に入った fact | %d | %d |" % (tin[u"数"], tin[u"文"]))
    w(u"| 型の外の fact | %d | %d |" % (out_[u"合計"][u"数"], out_[u"合計"][u"文"]))
    w(u"| 型の行 | %d | %d |" % (rows_[u"数"], rows_[u"文"]))
    w(u"")
    nz = [(r, out_[u"理由ごと"][r][u"数"] + out_[u"理由ごと"][r][u"文"]) for r in REASONS]
    w(u"- 型の外の fact の理由ごと(重ねて数える): %s。%s は 0。" % (u"・".join(u"(%s) %d" % (r, n) for r, n in nz if n), u"".join(u"(%s)" % r for r, n in nz if not n)))
    w(u"- 型の行のうち: 2 つ以上の fact をまとめた行 %d・値が `-0` の行 %d・期の表に無い期間の行 %d・`他:` の単位の行 %d。" % (
        rows_[u"2 つ以上の fact をまとめた行"], rows_[u"値が -0 の行"], rows_[u"期の表に無い期間の行"], rows_[u"他: の単位の行"]))
    for kind in NAME_KINDS:
        nn = PN[u"名の数"][kind]
        w(u"- 名の数(%s): 辞書の在る接頭辞 %d・辞書の無い `_cor` の接頭辞 %d・提出者別 %d。" % (kind, nn[NAME_CLASS[0]], nn[NAME_CLASS[1]], nn[NAME_CLASS[2]]))
    w(u"- 独自の名: 科目 %d・軸 %d・member %d。" % (PN[u"独自の名"][u"科目"], PN[u"独自の名"][u"軸"], PN[u"独自の名"][u"member"]))
    w(u"")
    w(u"**受け口の検査(起こした file)**: 受理した %d・断った %d・断りの数 %d。%d の規則のどれも、起こした file を 1 本も断らなかった。" % (acc[u"受理した"], acc[u"断った"], acc[u"断りの数"], len(RULES)))
    w(u"")
    c1, c2 = PN[u"比べ方 1"], PN[u"比べ方 2"]
    w(u"**比べ方 1(受理した %d 本)**: 属性が意味として同じ %d・文脈の名も同じ %d・違った fact %d。" % (acc[u"受理した"], c1[u"属性が意味として同じ"], c1[u"文脈の名も同じ"], c1[u"違った fact"]))
    w(u"")
    w(u"**比べ方 2(受理した %d 本)**: 組めた %d・fact が意味として同じ %d・字も含めて行が同じ %d・鳴り方が同じ %d・2 回が同じ %d。" % (
        acc[u"受理した"], c2[u"組めた"], c2[u"fact が意味として同じ"], c2[u"字も含めて行が同じ"], c2[u"鳴り方が同じ"], c2[u"2 回が同じ"]))
    w(u"")
    w(u"**壊し方(%d 通り)**: 作れた %d・断った %d・ちょうど 1 つ %d・別の規則で断った %d・断らなかった %d。" % (len(BREAKS), bs(u"作れた"), bs(u"断った"), bs(u"ちょうど 1 つ"), bs(u"別の規則で断った"), bs(u"断らなかった")))
    w(u"")
    w(u"| 壊し方 | 作れた | 断った | ちょうど 1 つ | 別の規則で断った | 断らなかった |")
    w(u"|---|---|---|---|---|---|")
    special, nstd, std = break_groups(rec)
    for k in special:
        w(u"| %s | %s |" % (k, u" | ".join(u"%d" % brk[k][x] for x in BREAK_KEYS)))
    w(u"| ほかの %d 通りのそれぞれ | %s |" % (nstd, u" | ".join(u"%d" % x for x in std)))
    w(u"")
    w(u"**形は合っているが中身が違う(%d 通り)**: 作れた %d・通した %d。" % (len(CHANGES), qs(u"作れた"), qs(u"通した")))
    w(u"")
    w(u"| 変え方 | 作れた | 通した |")
    w(u"|---|---|---|")
    for k in CHANGES:
        w(u"| %s | %d | %d |" % (k, chg[k][u"作れた"], chg[k][u"通した"]))
    w(u"")
    dq = VN[u"形は合っているが中身が違う"]
    dsame = [dq[k][u"作れた"] for k in CHANGES[:5]]
    w(u"**開発の %d 本(予測の判定には使わない)**: 断った書類 %d・受理した %d・型の外の fact %d・型の行は数 %d・文 %d・変え方は Q1〜Q5 が %d ずつ・Q6 が %d で全部通した。" % (
        Dv[u"書類"], Dv[u"断った書類"], VN[u"受け口"][u"受理した"], VN[u"型の外の fact"][u"合計"][u"数"] + VN[u"型の外の fact"][u"合計"][u"文"], VN[u"型の行"][u"数"], VN[u"型の行"][u"文"],
        dsame[0], dq[u"Q6"][u"作れた"]))
    w(u"")
    return L


def q_silent():
    return [n for n, _w in SG.SILENT_BY_DESIGN if n.startswith(u"Q")]


def q_silent_h():
    return [n for n in q_silent() if re.match(r"^Q\d+h\d", n)]


def render_post(c):
    u"""文書の §4 以降(封の門の本数・監査・§5)を、記録と封の門の本数から組み直す。"""
    L = []
    w = L.append
    w(u"## §4 門")
    w(u"")
    w(u"- 封の門: %d 本。記録が無い時(script の commit の後)と記録が在る時(記録の commit の前)の両方で緑。" % seal_tests())
    w(u"- 監査で見つかった穴: 1 回目は、受け口が孤立 surrogate の鍵で例外で落ちる(封の「例外で落ちない」に反する)ことと、変え方の守り 2 つに門が黙ること。"
      u"2 回目は、守りを半分だけ外す変異・走査の向きを逆にする変異に門が黙ることと、壊した file の書き込みに守りが無いこと。どちらも直して、3 回目で GO。")
    w(u"- 追記(2026-11-23): 封の門の変異 D12 を、乱数に依らない形に 2 行直した(commit %s)。並びが起動ごとの hash の乱数でたまたま昇順だと変異が黙るため。"
      u"上の封の門の commit %s は、この直しより前の版を指す。script・封・記録・数・当たり外れは変わらない。結果の門の留めを、この直しに合わせた。" % (FIX_COMMIT_SHORT, SCRIPT_COMMIT_SHORT))
    w(u"")
    w(u"## §5 次の便の候補(封 §6 に在るものだけ)")
    w(u"")
    w(cand_i_line(c.rec))
    for ln in CAND_LINES_FIXED:
        w(ln)
    return L


SEAL_TESTS = {}


def seal_tests():
    if u"n" not in SEAL_TESTS:
        n = 0
        for case in unittest.defaultTestLoader.loadTestsFromModule(SG):
            n += case.countTestCases()
        SEAL_TESTS[u"n"] = n
    return SEAL_TESTS[u"n"]


def sec3_text(c):
    return section(c.doc, u"## §3 ", u"## §4 ")


def render_doc(c):
    pre = cached(c, u"pre", lambda: render_pre(c))
    post = cached(c, u"post", lambda: render_post(c))
    return pre + sec3_text(c).rstrip(u"\n").split(u"\n") + [u""] + post


def lines_problems(c):
    u"""文書の §3 以外の全部の行が、記録と字から組み直した行と同じ(1 字でも違えば赤)。"""
    want = render_doc(c)
    got = c.doc.rstrip(u"\n").split(u"\n")
    out = []
    for i, (x, y) in enumerate(zip(want, got), 1):
        if x != y:
            out.append(u"文書の %d 行目が記録から組んだ行と違う: %s" % (i, y[:30]))
    if len(want) != len(got):
        out.append(u"文書の行数 %d が組み直した行数 %d と違う" % (len(got), len(want)))
    return out


def outside_sec3(c):
    return c.doc.replace(sec3_text(c), u"")


def sec4_text(c):
    return section(c.doc, u"## §4 ", u"## §5 ")


def derived_numbers(c):
    u"""記録から導ける数(文書の §3 以外の数はこの内か字で留めた境の数)。render_doc とは別に、記録の整数から作る。"""
    rec = c.rec
    out = set()
    for k in GROUPS:
        ints_in(rec[K_SUM][k], out)
    ints_in(rec[PRED_KEY], out)
    p = pred_numbers(rec)
    for a, b in ((p[u"XJ0-3"][0], p[u"XJ0-3"][1]),):
        out.add(pct2(a, b))
    for k in (u"XJ0-7", u"XJ0-8", u"XJ0-9"):
        a, b = p[k][0], p[k][1]
        out.add(pct(a, b))
    out |= set(str(v) for v in (seal_tests(), len(SG.SILENT_BY_DESIGN), len(q_silent()), len(q_silent()) - len(q_silent_h()), len(q_silent_h()), len(BREAKS), len(RULES), len(CHANGES), len(BREAKS) - len(break_groups(rec)[0])))
    out |= set(str(rec[u"材料"][u"書類の本数"]))
    out.add(str(rec[u"材料"][u"書類の本数"]))
    out |= set(DOC_COMMITS_ALL)
    out |= set(STRUCTURAL) | RESIDUAL_OK
    return out


def doc_number_problems(c):
    u"""§3 の外の数字は、記録から導いた値か字で留めた境の数の内。§3 は sec3_problems が見る。"""
    allowed = derived_numbers(c)
    out = []
    for i, ln in enumerate(outside_sec3(c).splitlines(), 1):
        for tok in doc_number_tokens(re.sub(r"^\d+\. ", u"", ln)):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"文書の(§3 の外の)%d 行目の数 %s が記録から組んだ数の外: %s" % (i, tok, ln[:30]))
    return out


def residual_problems(c):
    u"""組み直した行と同じ行を文書から除いた残りの数は、字で留めた境の数と commit の内(組み直しと文書の両方を同じに書き換えても残る見張り)。"""
    want = set(render_doc(c))
    rest = [ln for ln in outside_sec3(c).splitlines() if ln not in want]
    out = []
    allowed = RESIDUAL_OK | set(STRUCTURAL) | set(DOC_COMMITS_ALL)
    for ln in rest:
        for tok in doc_number_tokens(ln):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"組み直した行に無い行の数 %s が留めた境の数の外: %s" % (tok, ln[:24]))
    return out


def sanity_problems(c):
    u"""文書の静的な言い切り(組み直した行の数以外の字)が記録の数に合う。"""
    rec = c.rec
    out = []
    dev, prod = split_docs(rec)
    PN = rec[K_SUM][G_PROD][u"数"]
    VN = rec[K_SUM][G_DEV][u"数"]
    brk, chg = PN[u"壊し方"], PN[u"形は合っているが中身が違う"]
    acc = PN[u"受け口"][u"受理した"]
    refused = [d for d in prod if d[u"断った"]]
    if len(refused) != 1 or any(x != 0 for k in (u"対象の fact", u"型に入った fact", u"型の外の fact", u"型の行", u"独自の名", u"名の数") for x in leaves(refused[0][k])):
        out.append(u"文書の「断った 1 本の fact は 62 本の数に入っていない(断った書類の対象の fact は 0)」が記録と合わない")
    if rec[K_SUM][G_PROD][u"書類"] - rec[K_SUM][G_PROD][u"断った書類"] != acc or PN[u"受け口"][u"受理した"] + PN[u"受け口"][u"断った"] != acc:
        out.append(u"文書の「型の file になった 61 本」が記録(受理した + 断った)と合わない")
    if PN[u"受け口"][u"受理した"] != rec[K_SUM][G_PROD][u"書類"] - rec[K_SUM][G_PROD][u"断った書類"]:
        out.append(u"文書の「型の file になった本数」が書類 − 断った書類と合わない")
    if any(d[u"断った"] and (d[u"断った段"], d[u"断った理由"]) != (u"起こす", u"書類の決めが 1 通りに決まらない") for d in prod):
        out.append(u"文書の「段は起こす・理由は書類の決めが 1 通りに決まらない」が記録と合わない")
    if any(d[u"型の外の fact"][u"合計"][u"数"] + d[u"型の外の fact"][u"合計"][u"文"] < 1 for d in prod if not d[u"断った"]):
        out.append(u"文書の「型の file になった 61 本の全部で 1 個以上の fact を型の外に残した」が記録と合わない")
    if PN[u"型の外の fact"][u"合計"][u"数"] + PN[u"型の外の fact"][u"合計"][u"文"] < 1:
        out.append(u"文書の「型の外の fact は 0 ではない」が記録と合わない")
    if brk[u"R4a"][u"作れた"] != 0:
        out.append(u"文書の「R4a は本番だけの書類で 1 つも作れなかった」が記録と合わない")
    for k in (u"N5a", u"N5b"):
        if not (brk[k][u"作れた"] >= 1 and brk[k][u"断った"] == brk[k][u"作れた"] and brk[k][u"ちょうど 1 つ"] == 0):
            out.append(u"文書の「%s は作れた全部で断ったが、ちょうど 1 つは 0」が記録と合わない" % k)
    if not (sum(v[u"断らなかった"] for v in brk.values()) == 0 and sum(v[u"別の規則で断った"] for v in brk.values()) == 1 and brk[u"R12a"][u"別の規則で断った"] == 1
            and sum(v[u"作れた"] - v[u"断った"] for v in brk.values()) == 1):
        out.append(u"文書の「XJ0-6 の外れの 1 個は R12a の別の規則で断った 1 つ」が記録と合わない")
    if not (brk[u"N3a"][u"ちょうど 1 つ"] < brk[u"N3a"][u"作れた"]):
        out.append(u"文書の「N3a のちょうど 1 つでない分」が記録と合わない")
    if any(x != 0 for v in chg.values() for x in v[u"断った"].values()) or any(v[u"通した"] != v[u"作れた"] for v in chg.values()):
        out.append(u"文書の「受け口は 1 つも断らなかった・全部通した」が記録と合わない")
    if any(v[u"通した"] != v[u"作れた"] for v in VN[u"形は合っているが中身が違う"].values()):
        out.append(u"文書の「開発の 5 本の変え方は全部通した」が記録と合わない")
    dq = VN[u"形は合っているが中身が違う"]
    if len(set(dq[k][u"作れた"] for k in CHANGES[:5])) != 1:
        out.append(u"文書の「変え方は Q1〜Q5 が同じ数ずつ」が記録と合わない")
    if any(x != 0 for x in PN[u"受け口"][u"規則ごとの断りの数"].values()) or any(x != 0 for x in PN[u"受け口"][u"規則ごとの断った書類"].values()):
        out.append(u"文書の「24 の規則のどれも、起こした file を 1 本も断らなかった」が記録と合わない")
    j = judge(rec)
    if not (j[u"XJ0-8"][0] and j[u"XJ0-1"][0] and j[u"XJ0-5"][0] and j[u"XJ0-7"][0] and not j[u"XJ0-6"][0]):
        out.append(u"文書の「XJ0-8 は当たり・XJ0-7 は当たり・XJ0-6 は外れ」が記録と合わない")
    if rec[K_SUM][G_DEV][u"書類"] != DEV_COUNT or rec[K_SUM][G_PROD][u"書類"] != PROD_COUNT or rec[K_SUM][G_ALL][u"書類"] != DOC67:
        out.append(u"文書の 5・62・67 が記録の書類の数と合わない")
    if (len(RULES), len(BREAKS), len(CHANGES)) != (24, 44, 6) or len(MS.RULES) != 24 or len(MS.BREAK_IDS) != 44 or len(MS.CHANGE_IDS) != 6:
        out.append(u"文書の 24・44・6 が封の門・script の長さと合わない")
    if seal_tests() != 36:
        out.append(u"文書の「封の門: 36 本」が封の門の試験の数と違う")
    if len(SG.SILENT_BY_DESIGN) != 14 or len(q_silent()) != 8 or len(q_silent_h()) != 5:
        out.append(u"文書の「同値 8 本(3 + 5)・一覧は 14 本」が封の門の一覧と合わない")
    return out


def sec3_problems(c):
    u"""§3 は記録に欄の無い読み(監査の席の読み)の節。数は記録に縛らず、見出し・「測った数ではない」・字で留めた数の並び・記録から導ける関係・
    §3 の主張が外に出ないこと・語の留めを縛る。"""
    s = sec3_text(c)
    out = []
    if u"記録に欄の無い読み" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録に欄の無い読み」でない")
    if u"測った数ではない" not in s.splitlines()[0]:
        out.append(u"§3 の見出しに「測った数ではない」が無い")
    bullets = [ln for ln in s.splitlines()[1:] if ln.startswith(u"- ") or ln.startswith(u"  - ")]
    if len(bullets) != len(SEC3_LINES):
        out.append(u"§3 の箇条の数 %d が留めた行の数 %d と違う" % (len(bullets), len(SEC3_LINES)))
    toks = {}
    for key, nums in SEC3_LINES:
        hit = [ln for ln in bullets if key in ln]
        if len(hit) != 1:
            out.append(u"§3 に鍵の句の行が 1 つでない(%d 行): %s" % (len(hit), key[:16]))
            continue
        got = tuple(doc_number_tokens(hit[0]))
        toks[key] = got
        if got != tuple(nums):
            out.append(u"§3 の行 %s の数の並び %s が留めた並び %s と違う" % (key[:12], u",".join(got), u",".join(nums)))
    for ln in bullets:
        if not any(key in ln for key, _ in SEC3_LINES):
            out.append(u"§3 に留めていない行: %s" % ln[:20])
    for p in SEC3_PHRASES:
        if p not in plain(s):
            out.append(u"§3 に字が無い: %s" % p)
    rec = c.rec
    dev, prod = split_docs(rec)
    PN = rec[K_SUM][G_PROD][u"数"]
    brk = PN[u"壊し方"]
    # 記録から導ける関係(§3 の読みが書類ごとの数と矛盾しない)
    try:
        refused = [d for d in prod if d[u"断った"]]
        if len(refused) != 1 or toks[SEC3_LINES[0][0]][0] != str(len(refused)):
            out.append(u"§3 の「断った 1 本」が記録の断った書類の数と合わない")
        outd = [(d[u"型の外の fact"][u"理由ごと"][u"e"][u"数"] + d[u"型の外の fact"][u"理由ごと"][u"e"][u"文"], d[u"型の外の fact"][u"理由ごと"][u"f"][u"数"] + d[u"型の外の fact"][u"理由ごと"][u"f"][u"文"])
                for d in prod if not d[u"断った"]]
        tot = PN[u"型の外の fact"][u"合計"]
        if any(e - f_ != 1 for e, f_ in outd) or sum(e for e, _ in outd) + sum(f_ for _, f_ in outd) <= tot[u"数"] + tot[u"文"]:
            out.append(u"§3 の「型の外は format が無い隠しの数が 1 個ずつ・(e) と (f) の両方に数える(合計が足し算より小さい)」が記録と合わない")
        if [k for k in BREAKS if brk[k][u"別の規則で断った"] >= 1] != [u"R12a"] or brk[u"R12a"][u"別の規則で断った"] != int(toks[SEC3_LINES[2][0]][0]):
            out.append(u"§3 の「XJ0-6 の 1 個は R12a」が記録と合わない")
        if not (brk[u"N3a"][u"ちょうど 1 つ"] < brk[u"N3a"][u"作れた"] and brk[u"N5a"][u"ちょうど 1 つ"] == brk[u"N5b"][u"ちょうど 1 つ"] == 0):
            out.append(u"§3 の N3a・N5a・N5b の読みが記録と合わない")
        if brk[u"R4a"][u"作れた"] != 0:
            out.append(u"§3 の R4a の読み(作れない場合)が記録と合わない")
        acc = PN[u"受け口"][u"受理した"]
        if toks[SEC3_LINES[7][0]][0] != str(acc):
            out.append(u"§3 の「61 に満たない欄」の 61 が記録の受理した書類の数と合わない")
        c1, c2 = PN[u"比べ方 1"], PN[u"比べ方 2"]
        diff_docs = [d for d in prod if d[u"受け口"][u"受理した"] and not (d[u"比べ方 1"][u"文脈の名も同じ"] and d[u"比べ方 2"][u"字も含めて行が同じ"] and d[u"比べ方 2"][u"鳴り方が同じ"])]
        if not diff_docs or any(d[u"型の行"][u"期の表に無い期間の行"] < 1 and d[u"型の行"][u"他: の単位の行"] < 1 for d in diff_docs):
            out.append(u"§3 の「元と違う書類は期の表に無い期間の行か他: の単位の行が在る書類だった」が記録と合わない")
        if not (acc - c1[u"文脈の名も同じ"] < acc and acc - c2[u"字も含めて行が同じ"] < acc and acc - c2[u"鳴り方が同じ"] < acc):
            out.append(u"§3 の 61 に満たない欄が記録と合わない")
    except (KeyError, ValueError, IndexError, TypeError):
        out.append(u"§3 の数が読めない")
    rest = outside_sec3(c)
    for p in SEC3_ONLY_PHRASES:
        if p in rest:
            out.append(u"記録に欄の無い §3 の主張「%s」が §3 の外に出ている" % p)
    return out


def sec4_problems(c):
    u"""§4 の 36 は封の門の本数に縛る(render が組み直す)。"""
    out = []
    if seal_tests() != 36:
        out.append(u"封の門の本数(試験 36)が文書の §4 の数と違う")
    if u"- 封の門: 36 本。記録が無い時(script の commit の後)と記録が在る時(記録の commit の前)の両方で緑。" not in sec4_text(c).splitlines():
        out.append(u"§4 の封の門の行が違う")
    return out


def affirm_problems(c):
    u"""「作れる」「専用の道具が要らない」「任せられる」「誤りが無くなる」「書ける」「従う」「検査に通る」は、言えないことの引用(「…」の中)・否定の中にしか無い。引用の在る行には「言えない」「読まない」などが在る。"""
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        if QUOTED.search(ln) and not any(w in ln for w in (u"言えない", u"読まない", u"示していない", u"言わない")):
            out.append(u"文書の %d 行目が引用の主張を否定の外で書いている" % i)
        rest = QUOTED.sub(u"", ln)
        for w in AFFIRM_WORDS:
            if re.search(w, rest):
                out.append(u"文書の %d 行目に引用の外の字: %s" % (i, w))
    return out


def phrase_problems(c):
    doc = plain(c.doc)
    return [u"文書に要点の字が無い: %s" % p for p in PHRASES + MAIN_CLAIMS if p not in doc]


def head_problems(c):
    head = plain(c.doc.split(u"## §1")[0])
    out = [u"文書の頭(§1 の前)に無い: %s" % p for p in HEAD_PHRASES if p not in head]
    sec7 = plain(section(c.seal, u"## §7 ", None))
    lim7 = [ln[2:] for ln in sec7.splitlines() if ln.startswith(u"- ")]
    if len(lim7) != 5:
        out.append(u"封 §7 の限界の行が 5 本でない")
        return out
    hlines = head.splitlines()
    for i, (lim, frags) in enumerate(zip(lim7, LIMIT_FRAGS), 1):
        for x in frags:
            if x not in lim:
                out.append(u"封 §7 の %d 本目の限界に門の断片が無い: %s" % (i, x[:12]))
        if not any(all(x in ln for x in frags) for ln in hlines):
            out.append(u"封 §7 の %d 本目の限界が文書の頭の 1 つの行に揃って無い: %s" % (i, lim[:16]))
    for seal_p, doc_p in READ_PAIRS:
        if doc_p not in head:
            out.append(u"封 §6 の読み方の字が文書の頭に無い: %s" % doc_p[:16])
    return out


def forbidden_problems(c):
    out = [u"文書に禁止語: %s" % w for w in FORBIDDEN_WORDS if w in c.doc]
    scan = re.sub(r"(?<![0-9A-Za-z])[0-9a-f]{8}(?![0-9A-Za-z])", u" ", c.doc)
    if WG.DOCID_FORM.search(scan):
        out.append(u"文書に docID の形が在る")
    if WG.ECODE_FORM.search(scan):
        out.append(u"文書に EDINET コードの形が在る")
    return out


def doc_commit_problems(c):
    out = []
    for w in DOC_COMMITS_ALL:
        if w not in c.doc:
            out.append(u"文書に commit の字が無い: %s" % w)
    if not set(re.findall(r"(?<![0-9A-Za-z])[0-9a-f]{8}(?![0-9A-Za-z])", c.doc)) <= set(DOC_COMMITS_ALL):
        out.append(u"文書が知らない commit の字を書いている")
    return out


CHECKS = collections.OrderedDict([
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", record_clean_problems), (u"bound", bound_problems),
    (u"verdict", verdict_problems), (u"sec5", sec5_problems), (u"numbers", doc_number_problems), (u"lines", lines_problems), (u"resid", residual_problems), (u"sanity", sanity_problems),
    (u"sec3", sec3_problems), (u"sec4", sec4_problems), (u"affirm", affirm_problems), (u"phrases", phrase_problems), (u"head", head_problems), (u"forbidden", forbidden_problems),
    (u"commits", doc_commit_problems)])


# ======================================================================================================
def blob_problems(root, prefix, at):
    return WG.blob_problems(root, prefix, at)


def history_problems(root, history):
    u"""file ごとの履歴が、書いた commit の並びとちょうど同じ(長さも順も)。"""
    out = []
    for rel, want in history.items():
        r = subprocess.run(["git", "-C", root, "log", "--format=%H", "--reverse", "--", PREFIX + rel], stdout=subprocess.PIPE, universal_newlines=True)
        got = [x for x in r.stdout.split() if x]
        if len(got) != len(want) or any(not g.startswith(w) for g, w in zip(got, want)):
            out.append(u"%s の履歴が文書の書く commit %s と違う" % (rel, u"・".join(want)))
    return out


def commit_problems(root=REPO):
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は 8f3ec76b・script と封の門と指示書は 48cf7135・記録は 9a8b246d。commit の message が文書の言う「REVISE」「独立監査 GO」「差は 0」を書いている。"""
    out = history_problems(root, HISTORY)
    for short, words in ((SCRIPT_COMMIT_SHORT, (u"独立監査 REVISE(受け口が孤立 surrogate の鍵で落ちる・門の穴)→ 直し → REVISE(半分だけ外す型の門の穴・壊した file の書き込み)→ 直し → GO", u"封は直さず結果の文書に書く", u"限界")),
                         (RECORD_COMMIT_SHORT, (u"独立監査 GO", u"67 本を別の実装で数え直し差は 0"))):
        r = subprocess.run(["git", "-C", root, "log", "-1", "--format=%B", short], stdout=subprocess.PIPE, universal_newlines=True)
        for w in words:
            if w not in r.stdout:
                out.append(u"commit %s の message に「%s」が無い" % (short, w))
    return out


def fix_commit_problems(root=REPO, commit=FIX_COMMIT_SHORT, rel=SEAL_GATE_REL):
    u"""36a52eec は封の門の 1 file だけを触っている(ほかの file を触っていたら赤)。"""
    r = subprocess.run(["git", "-C", root, "show", "--name-only", "--format=", commit], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    files = [x for x in r.stdout.splitlines() if x.strip()]
    if r.returncode != 0 or files != [PREFIX + rel]:
        return [u"commit %s が封の門の 1 file だけを触っていない: %s" % (commit, u"・".join(files) or u"(読めない)")]
    return []


def git_problems(root=REPO):
    out = []
    out.extend(SG.seal_history_problems(root))
    out.extend(SG.engine_zero_problems(root))
    out.extend(blob_problems(root, PREFIX, BLOB_AT))
    out.extend(commit_problems(root))
    out.extend(fix_commit_problems(root))
    return out


def last_commit_problems(root, rel, want_last):
    rc, last = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + rel)
    if not last.startswith(want_last):
        return [u"%s の最後の commit が %s でない(記録を書いた後に変わった)" % (rel, want_last)]
    return []


def order_problems_real(root=REPO):
    u"""封 ⊏ script・封の門・指示書 ⊏ 記録 ⊏ 結果の文書と門。未 commit は赤。"""
    out = list(PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL, SEAL_GATE_REL, INSTR_REL], [RECORD_REL, DOC_REL, GATE_REL]))
    for rel in (SCRIPT_REL, SEAL_GATE_REL, INSTR_REL):
        added = PR.added_commits(root, PREFIX + rel)
        if len(added) != 1 or not added[0].startswith(SCRIPT_COMMIT_SHORT):
            out.append(u"%s を足した commit が %s でない" % (rel, SCRIPT_COMMIT_SHORT))
        want_last = FIX_COMMIT_SHORT if rel == SEAL_GATE_REL else SCRIPT_COMMIT_SHORT          # 記録の後に変わってよいのは、封の門のこの 1 commit だけ
        out.extend(last_commit_problems(root, rel, want_last))
    rec = PR.added_commits(root, PREFIX + RECORD_REL)
    if len(rec) != 1 or not rec[0].startswith(RECORD_COMMIT_SHORT):
        out.append(u"記録を足した commit が %s でない" % RECORD_COMMIT_SHORT)
    else:
        rc, lastrec = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + RECORD_REL)
        if not lastrec.startswith(RECORD_COMMIT_SHORT):
            out.append(u"記録の最後の commit が %s でない" % RECORD_COMMIT_SHORT)
        for rel in (SCRIPT_REL, SEAL_GATE_REL, INSTR_REL):
            added = PR.added_commits(root, PREFIX + rel)
            if added and not PR.is_anc(root, added[0], rec[0]):
                out.append(u"記録が %s より前" % rel)
    return out


# ======================================================================================================
PREDICT = u"""
(変異を実行する前に書いた予測。右 = 赤になるべき検査。「整合」= 書類ごとの数から集計・予測の欄を作り直し、recount は緑のまま当たり外れ・向きだけが変わる)
固定の変異 F1〜: 記録・封・文書の 1 か所を替える。右の検査が赤。
F1  記録の sha256 の写しを違う値に                                                       -> sha
F2  記録の「この script の sha256」を 1 字替える                                         -> sha
F3  記録の限界の欄の 1 行を消す                                                          -> sha
F4  記録の封の commit の欄を 1 字替える                                                  -> sha
F5  記録の step の欄を 1 字替える                                                        -> sha
F6  封の写しの sha256 の写しを違う値に                                                    -> sha
F7  指示書の sha256 の写しを違う値に                                                      -> sha
F8  記録の script の決めの字の壊し方を 1 つ消す                                           -> sha
F9  記録の材料の書類の本数 67 → 66                                                       -> recount
F10 記録の材料の file 名の並びの sha256 を 1 字替える                                      -> recount
F11 書類 20 の対象の fact(数)を 1 増やす(集計は直さない)                                    -> recount
F12 集計の本番だけの 62 本の受け口の受理した を 1 増やす(書類ごとは直さない)                  -> recount
F13 書類 20 の壊し方 N5a のちょうど 1 つを 1 増やす(断った・作れたは直さない)                  -> recount
F14 予測の欄 XJ0-6 の断ったを 1 増やす                                                    -> recount
F15 書類の番号 5 を 99 にする                                                             -> recount
F16 集計の全部の書類を 1 増やす                                                           -> recount
F17 集計の開発の 5 本と本番だけの 62 本を入れ替える                                         -> recount
F18 材料の開発の 5 本の番号を [1,2,3,4,6] にする                                         -> recount
F19 断った書類(番号 18)の対象の fact(数)を 1 にする                                      -> recount
F20 記録に docid の欄を足す                                                               -> clean
F21 記録に EDINET コードの形の字を足す                                                     -> clean
F22 記録に日付の形の字を足す                                                               -> clean
F23 封の写しから XJ0-6 の境の字を消す                                                      -> bound
F24 封の写しから §6 の (iv) の「払う前の知らせ」を消す                                       -> bound
F25 封の写しから §7 の限界の 1 本を消す                                                    -> bound
F26 封の写しの §6 に (vi) の候補を足す                                                     -> bound
F27 封の写しから §6 の読み方の 1 本(「会社の AI がこの型で書ける」)を消す                    -> bound
整合の変異 C1〜: recount は緑のまま、文書が合わなくなる(verdict・lines)。
C1  XJ0-1 を外れにする(受理した書類を 51 以下に: 10 本を起こした file の段で断る扱い)          -> verdict
C2  XJ0-2 を外れにする(断った規則を 4 つに)                                                  -> verdict
C3  XJ0-3 を外れにする(型の外の fact を 0.2% 超に)                                            -> verdict
C4  XJ0-4 を外れにする(型の外が 0 の書類を 6 本に)                                            -> verdict
C5  XJ0-5 を外れにする(道具が読む fact が違う書類を 1 本に)                                    -> verdict
C6  XJ0-6 を当たりにする(別の規則で断った 1 つを断ったに)                                      -> verdict
C7  XJ0-6 の外れの中身を替える(1 つも断らなかった 1 つに。外れのまま)                          -> lines・sanity(実行後の追記: 予測は verdict だったが、外れのままなので verdict は赤くならない。lines と sanity が赤)
C8  XJ0-7 を外れにする(ちょうど 1 つを 85% 未満に)                                             -> verdict
C9  XJ0-8 を外れにする(通した 363 を 95% 未満に)                                               -> verdict
C10 XJ0-9 を外れにする(下: 辞書の無い _cor の接頭辞の科目を 0 に)                                -> verdict
C11 XJ0-9 を外れにする(上: 辞書の無い _cor の接頭辞の科目を 8% 以上に)                           -> verdict
C12 XJ0-10 を外れにする(期の表に無い期間の行が在る書類を 4 本に)                               -> verdict
C13 受け口が断った規則を 1 つ作る(XJ0-2 は当たりのまま。(i) の条件に当たる)                       -> sec5・lines
文書の固定の変異 D1〜: 右の検査が赤。
D1  頭の「予測 1 本は外れ」を「2 本」に                                                       -> verdict・lines
D2  頭の「当たり 9・外れ 1」を「当たり 10・外れ 0」に                                          -> verdict・lines
D3  「型の外の fact は 0 ではない」を「0 である」に                                            -> lines・phrases
D4  「良い知らせではない」を「良い知らせである」に                                              -> lines・phrases
D5  「封は直していない」を「直した」に                                                        -> lines・phrases(実行後の追記: 最初の 1 か所だけ替えると phrases は黙った。字が文書の頭に複数在るため。全部の出た所を替える形に直した)
D6  「「会社の AI がこの型で書ける」…とは読まない」を肯定に                                     -> affirm・lines
D7  「受け口は、形が合っていれば中身の違う数を通す」を「中身の違いを断る」に                      -> verdict・lines・phrases
D8  §5 に (vi) の候補を足す                                                                   -> sec5
D9  §5 に候補の見出しの無い案の 1 行を足す                                                     -> sec5
D10 §5 の (i) の「当たらない」を「当たる」に                                                    -> sec5
D11 §5 の (iv) から「払う前の知らせ」を消す                                                     -> sec5
D12 §5 の (iii) を落とす                                                                      -> sec5
D13 頭の限界(標準の辞書は 3 つの…)を消す                                                      -> head
D14 「記録に欄の無い読み」を頭から消す                                                         -> head・lines(実行後の追記: 予測は phrases だったが、§3 の見出しにも同じ字が在るので phrases は黙る。head が赤)
D15 文書に「4999999%」の言い切りを足す                                                         -> numbers・resid
D16 引用の行から「言えない」「読まない」を全部消す                                              -> affirm
D17 文書に「保証」を足す・docID の形を足す                                                     -> forbidden
D18 文書の commit の字 48cf7135 を 1 字替える・9a8b246d を 1 字替える・知らない commit の字を足す  -> commits
D19 §3 の見出しの「記録に欄の無い読み」を消す・「測った数ではない」を消す                         -> sec3
D20 §3 の外に「2 つの類だけだった」を足す                                                       -> sec3
D21 §4 の「36 本」を「37 本」に                                                               -> sec4・lines
D33 §4 の追記(36a52eec)の行を消す                                                        -> lines・commits
D34 追記の commit の字 36a52eec を 1 字替える                                                -> commits・lines
F11 封の門の sha256 の写しを違う値に                                                         -> sha
D22 §2 の表のセル 1 つ(壊し方 R12a の断ったと別の規則で断ったの取り違え・作れたと通したの取り違え)を替える -> lines
D23 「断った 1 本の fact は、記録の「62 本」の数に入っていない」を消す                           -> phrases・lines
D24 引用の外に「XBRL を作れる」「AI に任せられる」「会社の AI がこの型で書ける」を足す             -> affirm
掃き(下の SWEEPS。文書の全部に 1 か所ずつ当てる。1 つでも黙れば報告):
W1  文書の全部の数(§3 を含む)を、(a) 1 増やす (b) 同じ文書の別の所の数に替える (c) §3 の数に替える          -> 全部赤(lines か sec3)
W2  向きの語(以上/以下/未満・多い/少ない・全部/一部・当たり/外れ・在る/無い・断った/通した/作れた など)を、出た所ごとに反対に -> 全部赤
W3  「5 本」「62 本」「67 本」「61 本」を互いに取り違える・80253/62747/27476/2613/2612/363/2481 を互いに取り違える -> 全部赤
W4  §3 の数・主張を §2 に 1 行として足す(全部)                                              -> 全部赤(lines・numbers・sec3)
W5  表の 1 セルを、同じ表の別の行の同じ列のセルへ替える(§1 の表・§2 の表の全部のセル。当たり外れの行の入れ替え・作れた/断った/ちょうど 1 つ/別の規則/断らなかったの取り違え・作れた/通したの取り違えを含む)    -> 全部赤
W6  §3 の外の全部の行を 1 行ずつ消す・全部の文を 1 つずつ消す・「・」でつないだ節を 1 つずつ消す        -> 全部赤
W7  記録の全部の整数・小数・真偽の葉(集計 3 つ・予測・書類の代表 8 つ分)を 1 増やす・反転する          -> 全部赤(recount)
W8  §3 の文を 1 つずつ消す・向きの語を反対に                                                   -> 黙る所が在りうる(§3 の中の括弧の例示と、SEC3_PHRASES に無い言い回し)。黙った所は報告
W9  次の便の候補を足す・落とす・入れ替える                                                      -> 全部赤(sec5 だけで)
予測の自己点検: 黙るとすれば W8(§3 は形で縛るため)と、W5 で「同じ文字列のセル」に替わる場合(スキップ)・W2 の「だけ→も」「より→と同じ」のような意味を変えない置換。W1〜W7 の他に黙りは無いと予測する。
"""

ORDER_DOC = (u"lines", u"verdict", u"sec5", u"numbers", u"resid", u"sec3", u"sec4", u"affirm", u"phrases", u"head", u"forbidden", u"commits", u"sanity", u"bound", u"clean", u"sha", u"recount")
ORDER_REC = (u"sha", u"recount", u"verdict", u"lines", u"sanity", u"clean", u"bound", u"sec5", u"numbers", u"resid", u"sec3", u"sec4", u"affirm", u"phrases", u"head", u"forbidden", u"commits")


def first_red(c, order):
    for k in order:
        if guard(CHECKS[k], c):
            return k
    return None


def rep(c, old, new, attr="doc", count=1):
    s = getattr(c, attr)
    assert old in s, old
    setattr(c, attr, s.replace(old, new, count))


def add_doc(c, text):
    c.doc = c.doc + u"\n" + text + u"\n"


def drop_seal(c, phrase):
    assert phrase in c.seal, phrase
    c.seal = c.seal.replace(phrase, u"X", 1)


def doc_at(rec, n):
    return [d for d in rec[K_DOCS] if d[u"番号"] == n][0]


# ---- 記録を整合して作り直す変異の道具
def rebuild(c):
    rec = c.rec
    dev, prod = split_docs(rec)
    rec[K_SUM][G_DEV] = agg_of(dev)
    rec[K_SUM][G_PROD] = agg_of(prod)
    rec[K_SUM][G_ALL] = agg_of(rec[K_DOCS])
    rec[PRED_KEY] = pred_expected(rec)
    c.cache = {}


def prod_docs(c):
    return [d for d in c.rec[K_DOCS] if d[u"番号"] > DEV_COUNT]


def accepted_prod(c):
    return [d for d in prod_docs(c) if d[u"受け口"][u"受理した"]]


def decline_doc(d, rule):
    u"""受理した書類 1 本を、受け口が rule で断ったことにする(整合: 比べ方・壊し方・変え方は 0 に)。"""
    a = d[u"受け口"]
    a[u"受理した"] = False
    a[u"断った"] = True
    a[u"断りの数"] = 1
    a[u"規則ごとの断りの数"][rule] = 1
    a[u"規則ごとの断った書類"][rule] = True
    for v in d[u"壊し方"].values():
        for k in v:
            v[k] = 0
    for v in d[u"形は合っているが中身が違う"].values():
        v[u"作れた"] = 0
        v[u"通した"] = 0
        for r in v[u"断った"]:
            v[u"断った"][r] = 0
    for k in d[u"比べ方 1"]:
        if isinstance(d[u"比べ方 1"][k], bool):
            d[u"比べ方 1"][k] = False
    for k in d[u"比べ方 2"]:
        d[u"比べ方 2"][k] = False


def m_x1_miss(c):
    for d in accepted_prod(c)[:11]:
        decline_doc(d, u"S1")
    rebuild(c)


def m_x2_high(c):
    for d, r in zip(accepted_prod(c)[:4], (u"D1", u"D2", u"N1", u"R1")):
        decline_doc(d, r)
    rebuild(c)


def m_x3_high(c):
    d = accepted_prod(c)[0]
    d[u"型の外の fact"][u"理由ごと"][u"e"][u"数"] += 200
    d[u"型の外の fact"][u"合計"][u"数"] += 200
    d[u"型に入った fact"][u"数"] -= 200
    d[u"対象の fact"][u"数"] = d[u"型の外の fact"][u"合計"][u"数"] + d[u"型に入った fact"][u"数"]
    rebuild(c)


def m_x4_high(c):
    for d in accepted_prod(c)[:6]:
        o = d[u"型の外の fact"]
        for r in REASONS:
            for k in FACT_KEYS:
                o[u"理由ごと"][r][k] = 0
        for k in FACT_KEYS:
            d[u"型に入った fact"][k] += o[u"合計"][k]
            o[u"合計"][k] = 0
    rebuild(c)


def m_x5_miss(c):
    d = accepted_prod(c)[0]
    d[u"比べ方 2"][u"fact が意味として同じ"] = False
    rebuild(c)


def m_x6_hit(c):
    d = doc_at(c.rec, 5 + 1)
    for dd in prod_docs(c):
        v = dd[u"壊し方"][u"R12a"]
        if v[u"別の規則で断った"] >= 1:
            v[u"別の規則で断った"] -= 1
            v[u"断った"] += 1
            v[u"ちょうど 1 つ"] += 1
            break
    rebuild(c)


def m_x6_none(c):
    for dd in prod_docs(c):
        v = dd[u"壊し方"][u"R12a"]
        if v[u"別の規則で断った"] >= 1:
            v[u"別の規則で断った"] -= 1
            v[u"断らなかった"] += 1
            break
    rebuild(c)


def m_x7_miss(c):
    k = 0
    for dd in prod_docs(c):
        for b in (u"S1a", u"S1b", u"S2a", u"D1a", u"D1b"):
            v = dd[u"壊し方"][b]
            if v[u"ちょうど 1 つ"] >= 1 and k < 300:
                k += v[u"ちょうど 1 つ"]
                v[u"ちょうど 1 つ"] = 0
    assert k >= 300
    rebuild(c)


def m_x8_miss(c):
    k = 0
    for dd in accepted_prod(c):
        if k >= 22:
            break
        v = dd[u"形は合っているが中身が違う"][u"Q1"]
        if v[u"通した"] >= 1:
            v[u"通した"] -= 1
            v[u"断った"][u"R10"] += 1
            k += 1
    rebuild(c)


def m_x9_low(c):
    for d in prod_docs(c):
        d[u"名の数"][u"科目"][NAME_CLASS[1]] = 0
    rebuild(c)


def m_x9_high(c):
    for d in prod_docs(c):
        d[u"名の数"][u"科目"][NAME_CLASS[1]] += d[u"名の数"][u"科目"][NAME_CLASS[0]] // 5
    rebuild(c)


def m_x10_miss(c):
    k = 0
    for d in accepted_prod(c):
        if d[u"型の行"][u"期の表に無い期間の行"] == 0 and k < 2:
            d[u"型の行"][u"期の表に無い期間の行"] = 3
            k += 1
    rebuild(c)


def m_rule_one(c):
    decline_doc(accepted_prod(c)[0], u"S1")
    rebuild(c)


def inc(c, path, delta=1):
    o = c.rec
    for p in path[:-1]:
        o = o[p]
    o[path[-1]] += delta


def m_swap_groups(c):
    c.rec[K_SUM][G_DEV], c.rec[K_SUM][G_PROD] = c.rec[K_SUM][G_PROD], c.rec[K_SUM][G_DEV]


def swap_doc_cells(c, a, b):
    u"""文書の 1 か所の字を別の字に替える(全部の表の行・文を別の所へ)。"""
    rep(c, a, b)


MUTATIONS = (
    (u"F1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"F2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"F3 記録の限界の欄の 1 行を消す", lambda c: c.rec.__setitem__(u"限界", c.rec[u"限界"][1:]), (u"sha",)),
    (u"F4 記録の封の commit の欄を 1 字替える", lambda c: c.rec.__setitem__(u"封の commit", u"0" + c.rec[u"封の commit"][1:]), (u"sha",)),
    (u"F5 記録の step の欄を 1 字替える", lambda c: c.rec.__setitem__(u"step", c.rec[u"step"].replace(u"XJ0", u"XJ1", 1)), (u"sha",)),
    (u"F6 封の写しの sha256 の写しを違う値に", lambda c: c.shas.__setitem__(SEAL_REL, u"0" * 64), (u"sha",)),
    (u"F7 指示書の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(INSTR_REL, u"0" * 64), (u"sha",)),
    (u"F11 封の門の sha256 の写しを違う値に(36a52eec の中身の字の留め)", lambda c: c.shas.__setitem__(SEAL_GATE_REL, u"0" * 64), (u"sha",)),
    (u"F8 記録の script の決めの字の壊し方を 1 つ消す", lambda c: c.rec[u"script の決めの字"][u"壊し方"].pop(), (u"sha",)),
    (u"F9 記録の材料の書類の本数を 66 に", lambda c: c.rec[u"材料"].__setitem__(u"書類の本数", 66), (u"recount",)),
    (u"F10 記録の材料の file 名の並びの sha256 を 1 字替える", lambda c: c.rec[u"材料"].__setitem__(u"書類の file 名の並びの sha256", u"0" + c.rec[u"材料"][u"書類の file 名の並びの sha256"][1:]), (u"recount",)),
    (u"F11 書類 20 の対象の fact(数)を 1 増やす(集計は直さない)", lambda c: doc_at(c.rec, 20)[u"対象の fact"].__setitem__(u"数", doc_at(c.rec, 20)[u"対象の fact"][u"数"] + 1), (u"recount",)),
    (u"F12 集計の本番だけの 62 本の受理したを 1 増やす", lambda c: inc(c, (K_SUM, G_PROD, u"数", u"受け口", u"受理した")), (u"recount",)),
    (u"F13 書類 20 の壊し方 N5a のちょうど 1 つを 1 増やす", lambda c: doc_at(c.rec, 20)[u"壊し方"][u"N5a"].__setitem__(u"ちょうど 1 つ", 1), (u"recount",)),
    (u"F14 予測の欄 XJ0-6 の断ったを 1 増やす", lambda c: inc(c, (PRED_KEY, PK[5], u"断った")), (u"recount",)),
    (u"F15 書類の番号 5 を 99 にする", lambda c: doc_at(c.rec, 5).__setitem__(u"番号", 99), (u"recount",)),
    (u"F16 集計の全部の書類を 1 増やす", lambda c: inc(c, (K_SUM, G_ALL, u"書類")), (u"recount",)),
    (u"F17 集計の開発の 5 本と本番だけの 62 本を入れ替える", m_swap_groups, (u"recount",)),
    (u"F18 材料の開発の 5 本の番号を [1,2,3,4,6] にする", lambda c: c.rec[u"材料"].__setitem__(u"開発の 5 本の番号", [1, 2, 3, 4, 6]), (u"recount",)),
    (u"F19 断った書類(番号 18)の対象の fact(数)を 1 にする", lambda c: doc_at(c.rec, 18)[u"対象の fact"].__setitem__(u"数", 1), (u"recount",)),
    (u"F20 記録に docid の欄を足す", lambda c: c.rec.__setitem__(u"docID", u"S100ABCD"), (u"clean",)),
    (u"F21 記録に EDINET コードの形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"E01234"), (u"clean",)),
    (u"F22 記録に日付の形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"2025-03-31"), (u"clean",)),
    (u"F23 封の写しから XJ0-6 の境の字を消す", lambda c: drop_seal(c, u"壊し方の全部で、作れた file は全部「断った」。"), (u"bound",)),
    (u"F24 封の写しから §6 の (iv) の「払う前の知らせ」を消す", lambda c: drop_seal(c, u"払う前の知らせ"), (u"bound",)),
    (u"F25 封の写しから §7 の限界の 1 本を消す", lambda c: rep(c, u"\n- 標準の辞書は 3 つの接頭辞だけ。", u"\n標準の辞書は 3 つの接頭辞だけ。", attr="seal"), (u"bound",)),
    (u"F26 封の写しの §6 に (vi) の候補を足す", lambda c: rep(c, u"  - (v) ", u"  - (vi) 別の案(0 USD)。\n  - (v) ", attr="seal"), (u"bound",)),
    (u"F27 封の写しから §6 の読み方の 1 本(「会社の AI がこの型で書ける」)を消す", lambda c: drop_seal(c, u"「会社の AI がこの型で書ける」「AI が指示書に従う」とは読まない"), (u"bound",)),
    (u"C1 XJ0-1 を外れにする", m_x1_miss, (u"verdict",)),
    (u"C2 XJ0-2 を外れにする", m_x2_high, (u"verdict",)),
    (u"C3 XJ0-3 を外れにする", m_x3_high, (u"verdict",)),
    (u"C4 XJ0-4 を外れにする", m_x4_high, (u"verdict",)),
    (u"C5 XJ0-5 を外れにする", m_x5_miss, (u"verdict",)),
    (u"C6 XJ0-6 を当たりにする", m_x6_hit, (u"verdict",)),
    (u"C7 XJ0-6 の外れの中身を替える(断らなかった 1 つに)", m_x6_none, (u"lines", u"sanity")),
    (u"C8 XJ0-7 を外れにする", m_x7_miss, (u"verdict",)),
    (u"C9 XJ0-8 を外れにする", m_x8_miss, (u"verdict",)),
    (u"C10 XJ0-9 を外れにする(下)", m_x9_low, (u"verdict",)),
    (u"C11 XJ0-9 を外れにする(上)", m_x9_high, (u"verdict",)),
    (u"C12 XJ0-10 を外れにする", m_x10_miss, (u"verdict",)),
    (u"C13 受け口が断った規則を 1 つ作る", m_rule_one, (u"sec5", u"lines", u"sanity")),
    (u"D1 頭の「予測 1 本は外れ」を「2 本」に", lambda c: rep(c, u"**予測 1 本は外れ。**", u"**予測 2 本は外れ。**"), (u"verdict", u"lines")),
    (u"D2 頭の「当たり 9・外れ 1」を「当たり 10・外れ 0」に", lambda c: rep(c, u"判定した 10 本は 当たり 9・外れ 1", u"判定した 10 本は 当たり 10・外れ 0"), (u"verdict", u"lines")),
    (u"D3 「型の外の fact は 0 ではない」を「0 である」に", lambda c: rep(c, u"**型の外の fact は 0 ではない。**", u"**型の外の fact は 0 である。**"), (u"lines", u"phrases")),
    (u"D4 「良い知らせではない」を「良い知らせである」に", lambda c: rep(c, u"良い知らせではない", u"良い知らせである"), (u"lines", u"phrases")),
    (u"D5 「封は直していない」を「直した」に", lambda c: rep(c, u"封は直していない", u"封は直した", count=100), (u"lines", u"phrases")),
    (u"D6 「「会社の AI がこの型で書ける」…とは読まない」を肯定に", lambda c: rep(c, u"**「会社の AI がこの型で書ける」「AI が指示書に従う」とは読まない。**", u"**会社の AI がこの型で書ける。AI が指示書に従う。**"), (u"affirm", u"lines")),
    (u"D7 「受け口は、形が合っていれば中身の違う数を通す」を「中身の違いを断る」に", lambda c: rep(c, u"受け口は、形が合っていれば中身の違う数を通す。", u"受け口は、形が合っていても中身の違いを断る。"), (u"verdict", u"lines", u"phrases")),
    (u"D8 §5 に (vi) の候補を足す", lambda c: add_doc(c, u"- (vi) 別の案を数える(費用は 0)。"), (u"sec5",)),
    (u"D9 §5 に候補の見出しの無い案の 1 行を足す", lambda c: add_doc(c, u"- 次の便の候補は、道具に掛けること。"), (u"sec5",)),
    (u"D10 §5 の (i) の「当たらない」を「当たる」に", lambda c: rep(c, u"この条件には当たらない。", u"この条件に当たる。"), (u"sec5",)),
    (u"D11 §5 の (iv) から「払う前の知らせ」を消す", lambda c: rep(c, u"別の封と、払う前の知らせが先。", u"別の封が先。"), (u"sec5",)),
    (u"D12 §5 の (iii) を落とす", lambda c: rep(c, u"- (iii) 標準の表の名の性質を辞書に足し、受け口の規則 R11〜R13 を「file の中の揃い」から「辞書との照らし」に替える(費用は 0)。\n", u""), (u"sec5",)),
    (u"D13 頭の限界(標準の辞書は 3 つの…)を消す", lambda c: rep(c, u"標準の辞書は 3 つの接頭辞だけ。", u"X。"), (u"head", u"lines")),
    (u"D14 「記録に欄の無い読み」を頭から消す", lambda c: rep(c, u"§3 は記録に欄の無い読みで、出どころを書く。", u"§3 は X。"), (u"head", u"lines")),
    (u"D15 文書に「4999999%」の言い切りを足す", lambda c: add_doc(c, u"決まった fact は 4999999% だった。"), (u"numbers", u"resid")),
    (u"D16 引用の行から「言えない」「読まない」を全部消す", lambda c: setattr(c, "doc", u"\n".join((ln.replace(u"言えない", u"X").replace(u"読まない", u"X") if QUOTED.search(ln) else ln) for ln in c.doc.splitlines())), (u"affirm",)),
    (u"D17a 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"D17b 文書に docID の形を足す", lambda c: add_doc(c, u"S100ABCD"), (u"forbidden",)),
    (u"D18a 文書の commit の字 48cf7135 を 1 字替える", lambda c: rep(c, u"48cf7135", u"48cf7136", count=100), (u"commits",)),
    (u"D18b 文書の commit の字 9a8b246d を 1 字替える", lambda c: rep(c, u"9a8b246d", u"9a8b246e", count=100), (u"commits",)),
    (u"D18c 文書に知らない commit の字を足す", lambda c: add_doc(c, u"commit 1a2b3c4d。"), (u"commits",)),
    (u"D33 §4 の追記(36a52eec)の行を消す", lambda c: rep(c, [ln for ln in c.doc.splitlines() if ln.startswith(u"- 追記(2026-11-23)")][0] + u"\n", u""), (u"lines", u"commits")),
    (u"D34 追記の commit の字 36a52eec を 1 字替える", lambda c: rep(c, u"36a52eec", u"36a52eed", count=100), (u"commits", u"lines")),
    (u"D19a §3 の見出しの「記録に欄の無い読み」を消す", lambda c: rep(c, u"## §3 記録に欄の無い読み(", u"## §3 X("), (u"sec3",)),
    (u"D19b §3 の見出しの「測った数ではない」を消す", lambda c: rep(c, u"測った数ではない。出どころは", u"X。出どころは"), (u"sec3",)),
    (u"D20 §3 の外に「2 つの類だけだった」を足す", lambda c: add_doc(c, u"型の外の fact は 2 つの類だけだった。"), (u"sec3",)),
    (u"D21 §4 の 36 を 37 に", lambda c: rep(c, u"封の門: 36 本", u"封の門: 37 本"), (u"sec4", u"lines")),
    (u"D22a 壊し方 R12a の断った 60 と別の規則で断った 1 を取り違える", lambda c: rep(c, u"| R12a | 61 | 60 | 60 | 1 | 0 |", u"| R12a | 61 | 1 | 60 | 60 | 0 |"), (u"lines",)),
    (u"D22b 変え方 Q6 の作れたと通したを取り違える(作れた 58 を 61 に)", lambda c: rep(c, u"| Q6 | 58 | 58 |", u"| Q6 | 61 | 58 |"), (u"lines",)),
    (u"D23 「断った 1 本の fact は、記録の「62 本」の数に入っていない」を消す", lambda c: rep(c, u"**断った 1 本の fact は、記録の「62 本」の数に入っていない。**", u"**X。**"), (u"phrases", u"lines")),
    (u"D24a 引用の外に「XBRL を作れる。」を足す", lambda c: add_doc(c, u"XBRL を作れる。"), (u"affirm",)),
    (u"D24b 引用の外に「AI に任せられる。」を足す", lambda c: add_doc(c, u"AI に任せられる。"), (u"affirm",)),
    (u"D24c 引用の外に「会社の AI がこの型で書ける。」を足す", lambda c: add_doc(c, u"会社の AI がこの型で書ける。"), (u"affirm",)),
    (u"D24d 引用の外に「AI が指示書に従う。」を足す", lambda c: add_doc(c, u"AI が指示書に従う。"), (u"affirm",)),
    (u"D25a 限界 1 を消す(便 XM0 の限界の全部…)", lambda c: rep(c, u"便 XM0 の限界の全部(", u"X(", ), (u"head", u"lines")),
    (u"D25b 限界 2 を消す(AI は呼んでいない。指示書が…)", lambda c: rep(c, u"AI は呼んでいない。指示書が AI に伝わるか", u"X。指示書が AI に伝わるか"), (u"head", u"lines")),
    (u"D25c 限界 3 を消す(壊し方は 1 か所ずつ…)", lambda c: rep(c, u"壊し方は 1 か所ずつ・最初の当てはまる所だけ", u"X"), (u"head", u"lines")),
    (u"D25d 限界 4 を消す(受け口の規則の一部は…)", lambda c: rep(c, u"受け口の規則の一部は開発の 5 本を見て置いた。", u"X。"), (u"head", u"lines")),
    (u"D26a 補足を 1 本消す(XJ0-6 の外れの中身)", lambda c: rep(c, u"- **XJ0-6 の外れの中身。**", u"- **X。**"), (u"head", u"lines")),
    (u"D26b 補足を 1 本消す(N5a・N5b)", lambda c: rep(c, u"- **N5a・N5b は作りから「ちょうど 1 つ」にならない。**", u"- **X。**"), (u"head", u"lines")),
    (u"D26c 補足を 1 本消す(受け口の限界)", lambda c: rep(c, u"- **受け口の限界(封 D4 の字どおり)。**", u"- **X。**"), (u"head", u"lines")),
    (u"D26d 補足を 1 本消す(指示書の 2 行)", lambda c: rep(c, u"- **指示書の「表示の位」と位取りの欄の意味の 2 行は、実装の席が足した。**", u"- **X。**"), (u"head", u"lines")),
    (u"D26e 補足を 1 本消す(封の門に黙る変異)", lambda c: rep(c, u"- **封の門に、作りから黙る変異が在る。**", u"- **X。**"), (u"head", u"lines")),
    (u"D26f 補足を 1 本消す(XJ0-4 の裏返し)", lambda c: rep(c, u"- **XJ0-4 の当たりは、型が足りないことの裏返し。**", u"- **X。**"), (u"head", u"lines")),
    (u"D27 §5 の (i) の条件の字を消す", lambda c: rep(c, u"断った規則は 0 だったので、この条件には当たらない。", u""), (u"sec5", u"lines")),
    (u"D28a 「型の file になった 61 本の分」を 62 本に", lambda c: rep(c, u"型の file になった 61 本の分", u"型の file になった 62 本の分"), (u"lines", u"phrases")),
    (u"D28b 「本番だけの 62 本」を 5 本に(§1 の分母の文)", lambda c: rep(c, u"分母は本番だけの 62 本。", u"分母は本番だけの 5 本。"), (u"lines",)),
    (u"D28c 「書類 67 本」を 62 本に(材料の行)", lambda c: rep(c, u"材料: 書類 67 本(", u"材料: 書類 62 本("), (u"lines",)),
    (u"D29a 壊し方 N3a の断ったとちょうど 1 つを取り違える", lambda c: rep(c, u"| N3a | 61 | 61 | 52 | 0 | 0 |", u"| N3a | 61 | 52 | 61 | 0 | 0 |"), (u"lines",)),
    (u"D29b 壊し方 R8a の作れたと断らなかったを取り違える", lambda c: rep(c, u"| R8a | 51 | 51 | 51 | 0 | 0 |", u"| R8a | 0 | 51 | 51 | 0 | 51 |"), (u"lines",)),
    (u"D29c 壊し方の「ほかの 38 通り」の断らなかったを 1 に", lambda c: rep(c, u"| ほかの 38 通りのそれぞれ | 61 | 61 | 61 | 0 | 0 |", u"| ほかの 38 通りのそれぞれ | 61 | 61 | 61 | 0 | 1 |"), (u"lines",)),
    (u"D29d 壊し方の「ほかの 38 通り」を 37 通りに", lambda c: rep(c, u"ほかの 38 通りのそれぞれ", u"ほかの 37 通りのそれぞれ"), (u"lines",)),
    (u"D30a §1 の XJ0-6 の判定を当たりに", lambda c: rep(c, u"断らなかった 0) | 外れ |", u"断らなかった 0) | 当たり |"), (u"lines", u"verdict")),
    (u"D30b §1 の XJ0-3 の分母を 62747 に", lambda c: rep(c, u"| 64/80253(0.08%) |", u"| 64/62747(0.10%) |"), (u"lines", u"verdict")),
    (u"D30c §1 の XJ0-8 の分母を 363 から 61 に", lambda c: rep(c, u"| 363/363(100.0%) |", u"| 61/61(100.0%) |"), (u"lines", u"verdict")),
    (u"D31 §3 の 61 に満たない欄の 61 を 62 に", lambda c: rep(c, u"**61 に満たない欄**", u"**62 に満たない欄**"), (u"sec3",)),
    (u"D32 §3 の「断った 1 本」を「断った 2 本」に", lambda c: rep(c, u"**断った 1 本**", u"**断った 2 本**"), (u"sec3",)),
)
# 記録を替えて作り直す(整合)変異の名(recount が緑のまま当たり外れ・向きだけが変わることを別の試験で見る)
CONSISTENT = (m_x1_miss, m_x2_high, m_x3_high, m_x4_high, m_x5_miss, m_x6_hit, m_x6_none, m_x7_miss, m_x8_miss, m_x9_low, m_x9_high, m_x10_miss, m_rule_one)


def run_mutations(base=None):
    base = base or Ctx()
    out = []
    for name, fn, checks in MUTATIONS:
        doc_only = name.startswith(u"D")
        c = base.with_doc(base.doc) if doc_only else base.copy()
        if doc_only:
            c.cache = {}
        fn(c)
        res = [(k, bool(guard(CHECKS[k], c))) for k in checks]
        out.append((name, res))
    return out


# ======================================================================================================
# 掃き: 文書・記録の全部の所に 1 か所ずつ当てる
NUM_RE = WG.NUM_RE
FLIPS = ((u"以上", u"以下"), (u"以下", u"以上"), (u"未満", u"以上"), (u"多い", u"少ない"), (u"少ない", u"多い"), (u"増", u"減"), (u"減", u"増"), (u"高", u"低"), (u"低", u"高"),
         (u"最小", u"最大"), (u"最大", u"最小"), (u"超える", u"満たない"), (u"満たない", u"超える"), (u"大きい", u"小さい"), (u"小さい", u"大きい"), (u"全部", u"一部"), (u"一部", u"全部"),
         (u"当たり", u"外れ"), (u"外れ", u"当たり"), (u"同じ", u"違う"), (u"違う", u"同じ"), (u"在る", u"無い"), (u"無い", u"在る"),
         (u"断らなかった", u"断った"), (u"断った", u"通した"), (u"通した", u"断った"), (u"作れた", u"通した"), (u"作れなかった", u"作れた"), (u"受理した", u"断った"), (u"別の規則で断った", u"断らなかった"),
         (u"ちょうど 1 つ", u"2 つ以上"), (u"できる", u"できない"), (u"言えない", u"言える"), (u"言わない", u"言う"), (u"読まない", u"読む"), (u"測っていない", u"測った"), (u"見えない", u"見える"),
         (u"直していない", u"直した"), (u"呼んでいない", u"呼んだ"), (u"含まない", u"含む"), (u"落ちない", u"落ちる"),
         (u"より", u"と同じ"), (u"だけ", u"も"), (u"ない", u"ある"), (u"先", u"後"), (u"人間", u"司令塔"), (u"司令塔", u"人間"), (u"有料", u"無料"), (u"本番", u"開発"), (u"開発", u"本番"),
         (u"個別", u"連結"), (u"既定", u"個別"), (u"受け口", u"型から作る命令"), (u"起こす", u"組む"), (u"範囲", u"外"))
DENOMS = (u"80253", u"62747", u"27476", u"2613", u"2612", u"363", u"2481", u"60189")
GROUP_NUMS = (u"5", u"62", u"67", u"61")


def num_spans(doc):
    out = []
    for m in NUM_RE.finditer(doc):
        if doc[:m.start()].count(u"`") % 2 == 1:
            continue
        out.append((m.start(), m.end(), m.group(1)))
    return out


def plus_one(tok):
    return u"%.1f" % (float(tok) + 0.1) if u"." in tok else str(int(tok.replace(u",", u"")) + 1)


def span_cases(doc, sec3_numbers):
    u"""(名前, 替えた文書)の列: 全部の数のトークンを 1 つずつ (a) 1 増やす (b) 文書の別の所の数に替える (c) §3 の数に替える。"""
    spans = num_spans(doc)
    uniq = sorted(set(t for _, _, t in spans), key=lambda t: (float(t.replace(u",", u"")), t))
    out = []
    for i, (s, e, tok) in enumerate(spans):
        a = plus_one(tok)
        out.append((u"W1a %d %s→%s" % (i, tok, a), doc[:s] + a + doc[e:]))
        j = (uniq.index(tok) + 1 + (i % 7)) % len(uniq)
        if uniq[j] == tok:
            j = (j + 1) % len(uniq)
        out.append((u"W1b %d %s→%s" % (i, tok, uniq[j]), doc[:s] + uniq[j] + doc[e:]))
        n3 = sec3_numbers[i % len(sec3_numbers)]
        if n3 != tok:
            out.append((u"W1c %d %s→%s" % (i, tok, n3), doc[:s] + n3 + doc[e:]))
    return out


def flip_cases(doc, c):
    out = []
    s3 = sec3_text(c)
    lo = doc.index(s3)
    hi = lo + len(s3)
    for a, b in FLIPS:
        for m in re.finditer(re.escape(a), doc):
            if lo <= m.start() < hi:
                continue
            out.append((u"W2 %s→%s @%d" % (a, b, m.start()), doc[:m.start()] + b + doc[m.end():]))
    return out


def group_cases(doc):
    out = []
    for g in GROUP_NUMS:
        for m in re.finditer(r"(?<![0-9A-Za-z.\-])%s(?= ?本)" % g, doc):
            for h in GROUP_NUMS:
                if h != g:
                    out.append((u"W3 %s 本→%s 本 @%d" % (g, h, m.start()), doc[:m.start()] + h + doc[m.end():]))
    for d in DENOMS:
        for m in re.finditer(r"(?<![0-9A-Za-z.\-])%s(?![0-9A-Za-z])" % d, doc):
            for h in DENOMS:
                if h != d:
                    out.append((u"W3 %s→%s @%d" % (d, h, m.start()), doc[:m.start()] + h + doc[m.end():]))
    return out


def table_cell_cases(doc):
    u"""表の 1 セルを、同じ表の別の行の同じ列のセルに替える(同じ字のときは飛ばす)。"""
    lines = doc.split(u"\n")
    out = []
    i = 0
    while i < len(lines):
        if lines[i].startswith(u"| ") and i + 1 < len(lines) and lines[i + 1].startswith(u"|---"):
            j = i + 2
            while j < len(lines) and lines[j].startswith(u"|"):
                j += 1
            rows = list(range(i, i + 1)) + list(range(i + 2, j))
            cells = {}
            for r in rows:
                cells[r] = lines[r].strip().strip(u"|").split(u" | ")
            for r in rows:
                for ci in range(len(cells[r])):
                    for r2 in rows:
                        if r2 == r or ci >= len(cells[r2]) or cells[r2][ci] == cells[r][ci]:
                            continue
                        new = list(cells[r])
                        new[ci] = cells[r2][ci]
                        nl = list(lines)
                        nl[r] = u"| " + u" | ".join(new) + u" |"
                        out.append((u"W5 表@%d 行 %d 列 %d ← 行 %d" % (i, r, ci, r2), u"\n".join(nl)))
            i = j
        else:
            i += 1
    return out


def row_swap_cases(doc):
    u"""表の 1 行の中で 2 つのセルを入れ替える(同じ字のときは飛ばす。作れた/断った/ちょうど 1 つ/別の規則で断った/断らなかった・作れた/通した・予測と実測の取り違えなど)。"""
    lines = doc.split(u"\n")
    out = []
    for i, ln in enumerate(lines):
        if not ln.startswith(u"| ") or ln.startswith(u"|---"):
            continue
        cells = ln.strip().strip(u"|").split(u" | ")
        for a in range(len(cells)):
            for b in range(a + 1, len(cells)):
                if cells[a] == cells[b]:
                    continue
                new = list(cells)
                new[a], new[b] = cells[b], cells[a]
                out.append((u"W5R 行 %d の列 %d と列 %d を入れ替える" % (i, a, b), u"\n".join(lines[:i] + [u"| " + u" | ".join(new) + u" |"] + lines[i + 1:])))
    return out


def candidate_cases(doc):
    u"""§5 の次の便の候補を足す・入れ替える・1 つ落とす(封 §6 の 5 つだけ)。全部赤になる。"""
    out = []
    for k, (old, new) in enumerate(((u"- (iv) 会社の AI の席", u"- (vi) 別の案を数える。\n- (iv) 会社の AI の席"), (u"材料は人間の決め)。", u"材料は人間の決め)・(vi) 道具に掛ける。"),
                                    (u"- (iii) 標準の表の名の性質を辞書に足し、受け口の規則 R11〜R13 を「file の中の揃い」から「辞書との照らし」に替える(費用は 0)。\n", u""),
                                    (u"- (ii) 型から本文の表示の字と表も作り、持ち込みを減らす(費用は 0)。\n", u""), (u"- (v) 組み替えの監査(人間の決めで後)。", u""),
                                    (u"この条件には当たらない", u"この条件に当たる"), (u"別の封と、払う前の知らせが先。", u"別の封が先。"), (u"(有料。", u"(0 USD。"),
                                    (u"- (ii) 型から本文の表示の字と表も作り、持ち込みを減らす(費用は 0)。\n- (iii) 標準の表", u"- (iii) 標準の表"))):
        assert old in doc, old
        out.append((u"W9 候補 %d: %s" % (k, new[:12]), doc.replace(old, new, 1)))
    for k, add in enumerate((u"- 次の便の候補は、道具に掛けること。", u"- (vi) 別の案。", u"  - (i) 別の案。", u"- 次は有料の席を呼ぶ。", u"- 候補: 文の fact を先に数える。")):
        out.append((u"W9 行 %d を足す" % k, doc.rstrip(u"\n") + u"\n" + add + u"\n"))
    return out


def delete_cases(doc, c):
    u"""§3 の外の全部の行・全部の文(。で切る)・「・」でつないだ節を 1 つずつ消す。"""
    s3 = sec3_text(c)
    lines = doc.split(u"\n")
    s3_lines = set(s3.split(u"\n"))
    out = []
    for i, ln in enumerate(lines):
        if not ln.strip() or ln in s3_lines:
            continue
        out.append((u"W6 行 %d を消す" % i, u"\n".join(lines[:i] + lines[i + 1:])))
        if ln.startswith(u"|"):
            continue
        for sep, tag in ((u"。", u"文"), (u"・", u"節")):
            parts = ln.split(sep)
            if len(parts) < 2:
                continue
            for k in range(len(parts)):
                if not parts[k]:
                    continue
                new = sep.join(parts[:k] + parts[k + 1:])
                if new == ln:
                    continue
                out.append((u"W6 行 %d の%s %d を消す" % (i, tag, k), u"\n".join(lines[:i] + [new] + lines[i + 1:])))
    return out


def sec3_cases(c):
    u"""§3 の中だけ: 文を 1 つずつ消す・向きの語を反対に(黙る所が在りうる。報告する)。"""
    s3 = sec3_text(c)
    out = []
    lines = s3.split(u"\n")
    for i, ln in enumerate(lines):
        if not ln.strip() or ln.startswith(u"## "):
            continue
        parts = ln.split(u"。")
        for k in range(len(parts)):
            if not parts[k]:
                continue
            new = u"。".join(parts[:k] + parts[k + 1:])
            if new != ln:
                out.append((u"W8 §3 行 %d の文 %d を消す" % (i, k), c.doc.replace(s3, u"\n".join(lines[:i] + [new] + lines[i + 1:]))))
    for a, b in FLIPS:
        for m in re.finditer(re.escape(a), s3):
            out.append((u"W8 §3 %s→%s @%d" % (a, b, m.start()), c.doc.replace(s3, s3[:m.start()] + b + s3[m.end():])))
    return out


def sec3_number_tokens(c):
    return [t for _, _, t in num_spans(sec3_text(c)) if t not in STRUCTURAL]


def limit_cases(c):
    u"""頭の限界の行を消す・断片を消す・§3 の数・主張を §2 に足す・引用の外の肯定。"""
    out = []
    head, rest = c.doc.split(u"## §1", 1)
    lines = head.split(u"\n")
    for i, frags in enumerate(LIMIT_FRAGS, 1):
        idx = [k for k, ln in enumerate(lines) if all(p in plain(ln) for p in frags)]
        for k in idx:
            out.append((u"W6L 限界 %d の行を消す" % i, u"\n".join(lines[:k] + lines[k + 1:]) + u"## §1" + rest))
        for p in frags:
            out.append((u"W6L 限界 %d の断片「%s」を消す" % (i, p[:10]), c.doc.replace(p, u"X", 1)))
    for _s, p in READ_PAIRS:
        out.append((u"W6L 読み方「%s」を消す" % p[:10], c.doc.replace(p, u"X", 1)))
    for tok in sorted(set(sec3_number_tokens(c))):
        out.append((u"W4 §3 の数 %s を §2 に足す" % tok, c.doc.replace(u"\n## §3 ", u"\n- 足した行 %s 件。\n\n## §3 " % tok, 1)))
    for p in SEC3_ONLY_PHRASES:
        out.append((u"W4 §3 の主張「%s」を §2 に足す" % p[:6], c.doc.replace(u"\n## §3 ", u"\n- 足した行 %s。\n\n## §3 " % p, 1)))
    for w in (u"XBRL を作れる。", u"AI に任せられる。", u"専用の道具が要らない。", u"誤りが無くなる。", u"会社の AI がこの型で書ける。", u"AI が指示書に従う。", u"EDINET の検査に通る。", u"受け口は中身の違いを断る。"):
        out.append((u"D14 引用の外に「%s」を足す" % w, c.doc + u"\n" + w + u"\n"))
    return out


def all_doc_cases(c):
    doc = c.doc
    s3n = sec3_number_tokens(c) or [u"901"]
    return span_cases(doc, s3n) + flip_cases(doc, c) + group_cases(doc) + table_cell_cases(doc) + row_swap_cases(doc) + candidate_cases(doc) + delete_cases(doc, c) + limit_cases(c)


def judge_rows_cases(c):
    u"""§1 の表の 10 行の 判定・実測・予測 のセルを、行どうしで入れ替える(全部の対)。"""
    lines = c.doc.split(u"\n")
    idx = [i for i, ln in enumerate(lines) if re.match(r"^\| XJ0-\d", ln)]
    out = []
    for i in idx:
        for j in idx:
            if i == j:
                continue
            ci = lines[i].strip().strip(u"|").split(u" | ")
            cj = lines[j].strip().strip(u"|").split(u" | ")
            for col, nm in ((3, u"判定"), (2, u"実測"), (1, u"予測")):
                if ci[col] == cj[col]:
                    continue
                new = list(ci)
                new[col] = cj[col]
                nl = list(lines)
                nl[i] = u"| " + u" | ".join(new) + u" |"
                out.append((u"W5 §1 行 %d の%sを行 %d から" % (i, nm, j), u"\n".join(nl)))
    return out


def run_doc_cases(c, cases, order=ORDER_DOC):
    u"""各ケースで、どの検査が先に赤になったかを返す(黙れば None)。"""
    out = []
    for name, text in cases:
        c2 = c.with_doc(text)
        out.append((name, first_red(c2, order)))
    return out


def leaf_paths(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            for p in leaf_paths(v, path + (k,)):
                yield p
    elif isinstance(o, bool):
        yield path
    elif isinstance(o, (int, float)):
        yield path


REC_SWEEP_DOCS = (1, 3, 5, 6, 18, 19, 20, 56, 67)


def record_sweep_cases(rec):
    u"""記録の整数・小数・真偽の葉を 1 つずつ替える対象(集計 3 つ・予測・書類の代表 9 つ分)。"""
    out = []
    for key in GROUPS:
        for p in leaf_paths(rec[K_SUM][key]):
            out.append((K_SUM, key) + p)
    for p in leaf_paths(rec[PRED_KEY]):
        out.append((PRED_KEY,) + p)
    for n in REC_SWEEP_DOCS:
        d = doc_at(rec, n)
        for p in leaf_paths(d):
            if p[0] != u"番号":
                out.append((K_DOCS, n) + p)
    return out


def apply_leaf(c, path):
    u"""写しの葉を 1 つ替え、(葉を持つ object・鍵・元の値)を返す(戻すのに使う)。"""
    if path[0] == K_DOCS:
        o = doc_at(c.rec, path[1])
        path = path[2:]
    else:
        o = c.rec
    for p in path[:-1]:
        o = o[p]
    v = o[path[-1]]
    o[path[-1]] = (not v) if isinstance(v, bool) else v + (0.1 if isinstance(v, float) else 1)
    return o, path[-1], v


def run_record_sweep(base):
    u"""葉を 1 つ替えては検査し、同じ葉に元の値を戻す(写し 1 つを使い回す。深い複製を毎回作らない)。木の file は変えない。"""
    out = []
    c = base.copy()
    for path in record_sweep_cases(base.rec):
        o, key, old = apply_leaf(c, path)
        c.cache = {}
        try:
            red = first_red(c, ORDER_REC)
        finally:
            o[key] = old
        out.append((u"W7 " + u"/".join(str(p)[:12] for p in path), red))
    c.cache = {}
    assert first_red(c, ORDER_REC) is None          # 戻した後は元と同じ(全部緑)
    return out


# ======================================================================================================
EXPECTED_SILENT = ()         # 掃きで黙るのが設計どおりと確かめた名(理由は結果の報告と PREDICT の追記)。空 = 黙る所は無い
MIN_CASES = {u"W1a": 270, u"W1b": 270, u"W1c": 240, u"W2": 270, u"W3": 200, u"W5": 900, u"W5R": 200, u"W6": 340, u"W6L": 19, u"W4": 15, u"W9": 14, u"D14": 8}


class RealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = Ctx()

    def test_a_1_sha256_and_provenance(self):
        self.assertEqual([], sha_problems(self.c))

    def test_b_1_the_record_numbers_recount_without_the_script_functions(self):
        self.assertEqual([], recount_problems(self.c))

    def test_b_2_the_record_has_no_forbidden_fields_or_forms(self):
        self.assertEqual([], record_clean_problems(self.c))

    def test_b_3_the_derived_numbers_the_document_states(self):
        rec = self.c.rec
        dv, pr, al = rec[K_SUM][G_DEV], rec[K_SUM][G_PROD], rec[K_SUM][G_ALL]
        PN = pr[u"数"]
        self.assertEqual((5, 62, 67), (dv[u"書類"], pr[u"書類"], al[u"書類"]))
        self.assertEqual((1, 0, 0), (pr[u"断った書類"], dv[u"断った書類"], PN[u"受け口"][u"断った"]))
        self.assertEqual((62747, 17506, 62683, 17506, 64, 0), (PN[u"対象の fact"][u"数"], PN[u"対象の fact"][u"文"], PN[u"型に入った fact"][u"数"], PN[u"型に入った fact"][u"文"],
                                                           PN[u"型の外の fact"][u"合計"][u"数"], PN[u"型の外の fact"][u"合計"][u"文"]))
        self.assertEqual((80253, 64), (PN[u"対象の fact"][u"数"] + PN[u"対象の fact"][u"文"], PN[u"型の外の fact"][u"合計"][u"数"] + PN[u"型の外の fact"][u"合計"][u"文"]))
        self.assertEqual((64, 3, 0), (PN[u"型の外の fact"][u"理由ごと"][u"e"][u"数"], PN[u"型の外の fact"][u"理由ごと"][u"f"][u"数"], PN[u"型の外の fact"][u"理由ごと"][u"a"][u"数"]))
        self.assertEqual((60189, 17504, 2289, 135, 520, 24), tuple(PN[u"型の行"][k] for k in ROW_KEYS))
        self.assertEqual((25194, 1586, 696), tuple(PN[u"名の数"][u"科目"][k] for k in NAME_CLASS))
        self.assertEqual((464, 0, 0), tuple(PN[u"名の数"][u"軸"][k] for k in NAME_CLASS))
        self.assertEqual((2599, 0, 685), tuple(PN[u"名の数"][u"member"][k] for k in NAME_CLASS))
        self.assertEqual((696, 0, 685), tuple(PN[u"独自の名"][k] for k in NAME_KINDS))
        self.assertEqual((61, 0, 0), (PN[u"受け口"][u"受理した"], PN[u"受け口"][u"断った"], PN[u"受け口"][u"断りの数"]))
        self.assertEqual((61, 59, 0), (PN[u"比べ方 1"][u"属性が意味として同じ"], PN[u"比べ方 1"][u"文脈の名も同じ"], PN[u"比べ方 1"][u"違った fact"]))
        self.assertEqual((61, 61, 55, 59, 61), tuple(PN[u"比べ方 2"][k] for k in CMP2))
        brk = PN[u"壊し方"]
        tot = tuple(sum(v[k] for v in brk.values()) for k in BREAK_KEYS)
        self.assertEqual((2613, 2612, 2481, 1, 0), tot)
        self.assertEqual({u"R4a": (0, 0, 0, 0, 0), u"R8a": (51, 51, 51, 0, 0), u"N3a": (61, 61, 52, 0, 0), u"N5a": (61, 61, 0, 0, 0), u"N5b": (61, 61, 0, 0, 0), u"R12a": (61, 60, 60, 1, 0)},
                         {k: tuple(brk[k][x] for x in BREAK_KEYS) for k in (u"R4a", u"R8a", u"N3a", u"N5a", u"N5b", u"R12a")})
        special, nstd, std = break_groups(rec)
        self.assertEqual(([u"R4a", u"R8a", u"N3a", u"N5a", u"N5b", u"R12a"], 38, (61, 61, 61, 0, 0)), (special, nstd, std))
        self.assertTrue(all(tuple(brk[k][x] for x in BREAK_KEYS) == (61, 61, 61, 0, 0) for k in BREAKS if k not in special))
        chg = PN[u"形は合っているが中身が違う"]
        self.assertEqual((363, 363), (sum(v[u"作れた"] for v in chg.values()), sum(v[u"通した"] for v in chg.values())))
        self.assertEqual([(61, 61), (61, 61), (61, 61), (61, 61), (61, 61), (58, 58)], [(chg[k][u"作れた"], chg[k][u"通した"]) for k in CHANGES])
        VN = dv[u"数"]
        self.assertEqual((5, 5, 4782, 1457), (VN[u"受け口"][u"受理した"], VN[u"型の外の fact"][u"合計"][u"数"], VN[u"型の行"][u"数"], VN[u"型の行"][u"文"]))
        self.assertEqual([5, 5, 5, 5, 5, 4], [VN[u"形は合っているが中身が違う"][k][u"作れた"] for k in CHANGES])
        self.assertEqual((2, 4, 0), (pr[u"期の表に無い期間の行が在る書類"], pr[u"他: の単位の行が在る書類"], pr[u"型の外の fact が 0 の書類"]))
        self.assertEqual({u"起こす": {u"書類の決めが 1 通りに決まらない": 1}, u"受け口": {}, u"型から作る": {}, u"組む": {}, u"道具": {}}, norm(pr[u"断った段と理由ごと"]))
        self.assertEqual(67, rec[u"材料"][u"書類の本数"])

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(9, sum(1 for v in j.values() if v[0]))
        self.assertEqual([u"XJ0-6"], miss_ids(j))
        self.assertEqual(list(IDS), list(j))
        # 当たり外れの判定は丸める前の数(境の数 52・3・0.2%・5・85%・95%・4%・8%・3)
        p = pred_numbers(self.c.rec)
        self.assertEqual((61, 62), p[u"XJ0-1"])
        self.assertEqual((True, u""), j[u"XJ0-1"])
        self.assertEqual((0,), p[u"XJ0-2"])
        self.assertEqual((True, u""), j[u"XJ0-2"])
        self.assertEqual((64, 80253), p[u"XJ0-3"])
        self.assertTrue(1000 * 64 <= 2 * 80253)
        self.assertEqual((True, u""), j[u"XJ0-3"])
        self.assertEqual((0, 62), p[u"XJ0-4"])
        self.assertEqual((True, u""), j[u"XJ0-4"])
        self.assertEqual((61, 61), p[u"XJ0-5"])
        self.assertEqual((True, u""), j[u"XJ0-5"])
        self.assertEqual((2612, 2613, 1, 0), p[u"XJ0-6"])
        self.assertEqual((False, u"別の規則で断った"), j[u"XJ0-6"])
        self.assertEqual((2481, 2613), p[u"XJ0-7"])
        self.assertTrue(100 * 2481 >= 85 * 2613)
        self.assertEqual((True, u""), j[u"XJ0-7"])
        self.assertEqual((363, 363), p[u"XJ0-8"][:2])
        self.assertEqual((True, u""), j[u"XJ0-8"])
        self.assertEqual((1586, 27476), p[u"XJ0-9"])
        self.assertTrue(100 * 1586 >= 4 * 27476 and 100 * 1586 < 8 * 27476)
        self.assertEqual((True, u""), j[u"XJ0-9"])
        self.assertEqual((2, 62), p[u"XJ0-10"])
        self.assertEqual((True, u""), j[u"XJ0-10"])
        # 率の字(導き直す)
        self.assertEqual(u"0.08", pct2(64, 80253))
        self.assertEqual(u"94.9", pct(2481, 2613))
        self.assertEqual(u"100.0", pct(363, 363))
        self.assertEqual(u"5.8", pct(1586, 27476))

    def test_c_3_the_section5_follows_the_seal_section6(self):
        self.assertEqual([], sec5_problems(self.c))

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))
        self.assertEqual([], residual_problems(self.c))

    def test_d_2_every_line_outside_section3_equals_the_one_built_from_the_record(self):
        self.assertEqual([], lines_problems(self.c))
        self.assertEqual([], sanity_problems(self.c))

    def test_d_3_section3_is_bound_only_by_form_not_by_the_record(self):
        self.assertEqual([], sec3_problems(self.c))

    def test_d_4_the_seal_gate_counts_are_bound(self):
        self.assertEqual([], sec4_problems(self.c))
        self.assertEqual(36, seal_tests())
        self.assertIn(u"封の門: 36 本。", self.c.doc)
        self.assertEqual((14, 8, 5), (len(SG.SILENT_BY_DESIGN), len(q_silent()), len(q_silent_h())))
        self.assertEqual((24, 44, 6), (len(MS.RULES), len(MS.BREAK_IDS), len(MS.CHANGE_IDS)))

    def test_d_5_the_scope_numbers_follow_the_seal_and_the_record(self):
        self.assertEqual(5, MS.DEV_COUNT)
        self.assertEqual(67, MS.DOCS_WANT)
        self.assertEqual(67, self.c.rec[K_DOCS][-1][u"番号"])
        self.assertEqual(67, len(self.c.rec[K_DOCS]))
        self.assertEqual(5, len(split_docs(self.c.rec)[0]))
        self.assertEqual(62, len(split_docs(self.c.rec)[1]))

    def test_e_1_the_important_phrases_are_present(self):
        self.assertEqual([], phrase_problems(self.c))

    def test_e_2_the_losses_and_limits_are_at_the_head(self):
        self.assertEqual([], head_problems(self.c))

    def test_e_3_the_document_has_no_forbidden_words_or_forms_and_no_affirmation(self):
        self.assertEqual([], forbidden_problems(self.c))
        self.assertEqual([], affirm_problems(self.c))

    def test_e_4_the_commits_the_document_names(self):
        self.assertEqual([], doc_commit_problems(self.c))

    def test_f_1_the_seal_history_the_blobs_and_the_engine(self):
        self.assertEqual([], git_problems())

    def test_f_2_order_the_seal_then_script_then_record_then_the_document_and_the_gate(self):
        u"""結果の文書と門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_f_3_the_blob_check_lists_the_five_frozen_files_at_their_commits(self):
        self.assertEqual([SEAL_REL, SCRIPT_REL, SEAL_GATE_REL, INSTR_REL, RECORD_REL], list(BLOB_AT))
        self.assertEqual([SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, FIX_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT], list(BLOB_AT.values()))
        self.assertEqual([SEAL_COMMIT_SHORT], HISTORY[SEAL_REL])
        self.assertEqual([SCRIPT_COMMIT_SHORT, FIX_COMMIT_SHORT], HISTORY[SEAL_GATE_REL])          # 履歴は 2 つちょうど
        self.assertEqual(u"36a52eec", FIX_COMMIT_SHORT)
        self.assertEqual((SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT), DOC_COMMITS)
        self.assertEqual((u"8f3ec76b", u"48cf7135", u"9a8b246d"), DOC_COMMITS)

    def test_f_4_the_commit_history_check_matches_the_real_history(self):
        self.assertEqual([], commit_problems())

    def test_f_5_the_blob_check_is_red_for_a_changed_file(self):
        r = PR.Repo()
        r.put("measure/s.py")
        c1 = r.commit("measure/s.py")
        at = {"measure/s.py": c1[:8]}
        self.assertEqual([], blob_problems(r.d, PREFIX, at))
        with open(os.path.join(r.d, PREFIX, "measure/s.py"), "a", encoding="utf-8") as fh:
            fh.write(u"# 結果の便で足した 1 行\n")
        self.assertNotEqual([], blob_problems(r.d, PREFIX, at))
        # 封の門の留め(36a52eec): 履歴は 2 つちょうど・最後の commit・1 file だけ・中身は blob と sha256 の字。"""
        g = "tests/g.py"
        r = PR.Repo()
        r.put(g)
        c1 = r.commit(g)
        r.put(g)
        c2 = r.commit(g)
        want = collections.OrderedDict([(g, [c1[:8], c2[:8]])])
        self.assertEqual([], history_problems(r.d, want))
        self.assertEqual([], last_commit_problems(r.d, g, c2[:8]))
        self.assertEqual([], fix_commit_problems(r.d, c2[:8], g))
        at = {g: c2[:8]}
        self.assertEqual([], blob_problems(r.d, PREFIX, at))
        self.assertNotEqual([], blob_problems(r.d, PREFIX, {g: c1[:8]}))                       # 36a52eec より前の中身
        self.assertNotEqual([], history_problems(r.d, collections.OrderedDict([(g, [c1[:8]])])))          # 履歴の長さが 1 つ足りない
        self.assertNotEqual([], history_problems(r.d, collections.OrderedDict([(g, [c2[:8], c1[:8]])])))          # 順が逆
        self.assertNotEqual([], last_commit_problems(r.d, g, c1[:8]))
        r.put(g)
        r.commit(g)                                                                             # もう 1 回変わる
        self.assertNotEqual([], history_problems(r.d, want))
        self.assertNotEqual([], last_commit_problems(r.d, g, c2[:8]))
        r.put(g)
        r.put("tests/other.py")
        c4 = r.commit(g, "tests/other.py")                                                      # 2 file を触る commit
        self.assertNotEqual([], fix_commit_problems(r.d, c4[:8], g))
        self.assertEqual(u"b579c678be3a6c8ae527aed19b99b1ccddbf69f59b82d07d762bc7bf552f02be", SHA_PIN[SEAL_GATE_REL])
        self.assertEqual(SEAL_GATE_FIXED_SHA, sha_file(SEAL_GATE_REL))


class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Ctx()

    def test_g_1_every_mutation_turns_its_checks_red_and_the_files_are_unchanged(self):
        files = list(SHA_PIN) + [DOC_REL]
        before = tuple(sha_file(r) for r in files)
        results = run_mutations(self.base)
        self.assertEqual(before, tuple(sha_file(r) for r in files))
        self.assertEqual(len(MUTATIONS), len(results))
        silent = [(n, k) for n, res in results for k, red in res if not red]
        self.assertEqual([], silent)
        self.assertGreaterEqual(len(MUTATIONS), 95)

    def test_g_2_the_unmutated_copy_is_green_on_every_check(self):
        c = self.base.copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_g_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_document_check_does_not(self):
        base_j = judge(self.base.rec)
        for fn in CONSISTENT:
            c = self.base.copy()
            fn(c)
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertIsNotNone(first_red(c, ORDER_REC), fn.__name__)
        flips = ((m_x1_miss, u"XJ0-1"), (m_x2_high, u"XJ0-2"), (m_x3_high, u"XJ0-3"), (m_x4_high, u"XJ0-4"), (m_x5_miss, u"XJ0-5"), (m_x6_hit, u"XJ0-6"), (m_x7_miss, u"XJ0-7"),
                 (m_x8_miss, u"XJ0-8"), (m_x9_low, u"XJ0-9"), (m_x9_high, u"XJ0-9"), (m_x10_miss, u"XJ0-10"))
        for fn, key in flips:
            c = self.base.copy()
            fn(c)
            self.assertNotEqual(base_j[key][0], judge(c.rec)[key][0], (fn.__name__, key))
            self.assertNotEqual([], verdict_problems(c), (fn.__name__, key))
        # 外れの向き(XJ0-9 の下と上・XJ0-6 の断らなかった/別の規則で断った)は別々に出る
        for fn, key, way in ((m_x9_low, u"XJ0-9", u"下"), (m_x9_high, u"XJ0-9", u"上"), (m_x1_miss, u"XJ0-1", u"下"), (m_x2_high, u"XJ0-2", u"上"), (m_x6_none, u"XJ0-6", u"断らなかった")):
            c = self.base.copy()
            fn(c)
            self.assertEqual(way, judge(c.rec)[key][1], (fn.__name__, key))
        self.assertEqual(u"別の規則で断った", base_j[u"XJ0-6"][1])
        # 受け口が断った規則が 1 つできると (i) の条件に当たる: 文書の「当たらない」は赤
        c = self.base.copy()
        m_rule_one(c)
        self.assertEqual([], recount_problems(c))
        self.assertEqual(1, pred_numbers(c.rec)[u"XJ0-2"][0])
        self.assertNotEqual([], sec5_problems(c))
        self.assertTrue(judge(c.rec)[u"XJ0-2"][0])

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)
        for k in (u"numbers", u"resid", u"sec5"):
            self.assertIn(k, ORDER_DOC)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数(丸める前の整数): 下限・上限とも含む/含まない。"""
        def j(**kw):
            p = collections.OrderedDict([(u"XJ0-1", (52, 62)), (u"XJ0-2", (3,)), (u"XJ0-3", (1, 500)), (u"XJ0-4", (5, 62)), (u"XJ0-5", (61, 61)), (u"XJ0-6", (2613, 2613, 0, 0)),
                                         (u"XJ0-7", (85, 100)), (u"XJ0-8", (95, 100, {})), (u"XJ0-9", (4, 100)), (u"XJ0-10", (3, 62))])
            for k, v in kw.items():
                p[k.replace(u"_", u"-")] = v
            return judge_nums(p)
        self.assertTrue(j()[u"XJ0-1"][0])
        self.assertFalse(j(XJ0_1=(51, 62))[u"XJ0-1"][0])
        self.assertEqual(u"下", j(XJ0_1=(51, 62))[u"XJ0-1"][1])
        self.assertTrue(j()[u"XJ0-2"][0])
        self.assertFalse(j(XJ0_2=(4,))[u"XJ0-2"][0])
        self.assertEqual(u"上", j(XJ0_2=(4,))[u"XJ0-2"][1])
        self.assertTrue(j(XJ0_2=(0,))[u"XJ0-2"][0])
        self.assertTrue(j()[u"XJ0-3"][0])                                     # 1/500 = 0.2% ちょうど(含む)
        self.assertFalse(j(XJ0_3=(1, 499))[u"XJ0-3"][0])
        self.assertTrue(j(XJ0_3=(0, 1000))[u"XJ0-3"][0])
        self.assertFalse(j(XJ0_3=(0, 0))[u"XJ0-3"][0])
        self.assertTrue(j()[u"XJ0-4"][0])
        self.assertFalse(j(XJ0_4=(6, 62))[u"XJ0-4"][0])
        self.assertTrue(j(XJ0_4=(0, 62))[u"XJ0-4"][0])
        self.assertTrue(j()[u"XJ0-5"][0])
        self.assertFalse(j(XJ0_5=(60, 61))[u"XJ0-5"][0])
        self.assertEqual((False, u"判定できない"), j(XJ0_5=(0, 0))[u"XJ0-5"])
        self.assertTrue(j()[u"XJ0-6"][0])
        self.assertFalse(j(XJ0_6=(2612, 2613, 1, 0))[u"XJ0-6"][0])
        self.assertEqual(u"別の規則で断った", j(XJ0_6=(2612, 2613, 1, 0))[u"XJ0-6"][1])
        self.assertEqual(u"断らなかった", j(XJ0_6=(2612, 2613, 0, 1))[u"XJ0-6"][1])
        self.assertFalse(j(XJ0_6=(0, 0, 0, 0))[u"XJ0-6"][0])
        self.assertTrue(j()[u"XJ0-7"][0])
        self.assertFalse(j(XJ0_7=(84, 100))[u"XJ0-7"][0])
        self.assertFalse(j(XJ0_7=(0, 0))[u"XJ0-7"][0])
        self.assertTrue(j()[u"XJ0-8"][0])
        self.assertFalse(j(XJ0_8=(94, 100, {}))[u"XJ0-8"][0])
        self.assertFalse(j(XJ0_8=(0, 0, {}))[u"XJ0-8"][0])
        self.assertTrue(j()[u"XJ0-9"][0])                                     # 4% ちょうど(含む)
        self.assertFalse(j(XJ0_9=(3, 100))[u"XJ0-9"][0])
        self.assertEqual(u"下", j(XJ0_9=(3, 100))[u"XJ0-9"][1])
        self.assertTrue(j(XJ0_9=(7, 100))[u"XJ0-9"][0])
        self.assertFalse(j(XJ0_9=(8, 100))[u"XJ0-9"][0])                      # 8% ちょうど(含まない)
        self.assertEqual(u"上", j(XJ0_9=(8, 100))[u"XJ0-9"][1])
        self.assertFalse(j(XJ0_9=(0, 0))[u"XJ0-9"][0])
        self.assertTrue(j()[u"XJ0-10"][0])
        self.assertFalse(j(XJ0_10=(4, 62))[u"XJ0-10"][0])

    def test_g_6_the_section5_decision_follows_the_seal_section6(self):
        c = self.base
        s6 = seal_s6_text(c.seal)
        sec5 = section(c.doc, u"## §5 ", None)
        self.assertEqual([], sec5_problems(c))
        self.assertEqual(5, len(re.findall(u"^  - \\((?:i|ii|iii|iv|v)\\) ", s6, re.M)))
        self.assertIsNone(re.search(u"\\(vi\\)", s6))
        # 文書の §5 に 6 つ目・封に無い候補の字・見出しの無い案を足す(全部赤)・(i) の条件・(iv) の字を動かす・決めの字を消すと赤
        for add in (u"- 次の便の候補は、別にある。\n", u"- (vi) 別の案。\n", u"- 次は道具に掛ける。\n", u"- 候補 (vii) を数える。\n"):
            self.assertNotEqual([], sec5_problems(c.with_doc(c.doc.rstrip(u"\n") + u"\n" + add)), add)
        for old, new in ((u"この条件には当たらない", u"この条件に当たる"), (u"断った規則は 0 だったので", u"断った規則は 1 だったので"), (u"(有料。", u"(0 USD。"), (u"材料は人間の決め", u"材料は司令塔の決め"),
                         (u"別の封と、", u""), (u"払う前の知らせが先", u"知らせは要らない"), (u"・(iv) 文の fact", u"・(iv) 別の案")):
            if old not in sec5:
                continue
            self.assertNotEqual([], sec5_problems(c.with_doc(c.doc.replace(old, new, 1))), old)
        # 封の §6 に (vi) が増えたら封の側の検査が赤
        cc = c.copy()
        rep(cc, u"  - (v) ", u"  - (vi) 別の案(0 USD)。\n  - (v) ", attr="seal")
        self.assertNotEqual([], bound_problems(cc))
        # (i) の「断った規則は 0」は記録に縛られる(記録を替えて当たりにしても文書の字は「当たらない」のまま → 赤)
        cr = c.copy()
        m_rule_one(cr)
        self.assertNotEqual([], sec5_problems(cr))

    def test_g_7_the_group_sizes_and_the_numbers_are_not_confused(self):
        rec = self.base.rec
        dev, prod = split_docs(rec)
        self.assertEqual((5, 62, 67), (len(dev), len(prod), len(rec[K_DOCS])))
        self.assertEqual(len(set([5, 62, 67, 61])), 4)
        c = self.base.copy()
        m_swap_groups(c)
        self.assertNotEqual([], recount_problems(c))
        self.assertEqual(61, rec[K_SUM][G_PROD][u"数"][u"受け口"][u"受理した"])
        self.assertEqual(61, rec[K_SUM][G_PROD][u"書類"] - rec[K_SUM][G_PROD][u"断った書類"])

    def test_g_8_the_verdict_table_stays_the_62_prod_numbers(self):
        for old, new in ((u"| 61 本(62 本のうち) | 当たり |", u"| 66 本(67 本のうち) | 当たり |"), (u"| 61 本(62 本のうち) | 当たり |", u"| 5 本(5 本のうち) | 当たり |"),
                         (u"| 64/80253(0.08%) | 当たり |", u"| 69/80253(0.09%) | 当たり |"), (u"| 2481/2613(94.9%) | 当たり |", u"| 2481/2613(94.9%) | 外れ |"),
                         (u"| 363/363(100.0%) | 当たり |", u"| 363/363(100.0%) | 外れ |"), (u"| 断った 2612・作れた 2613(別の規則で断った 1・断らなかった 0) | 外れ |", u"| 断った 2613・作れた 2613(別の規則で断った 0・断らなかった 0) | 当たり |"),
                         (u"| 2 本(62 本のうち) | 当たり |", u"| 2 本(67 本のうち) | 当たり |"), (u"| 0 本(62 本のうち) | 当たり |", u"| 0 本(5 本のうち) | 当たり |"),
                         (u"| 1586/27476(5.8%) | 当たり |", u"| 1586/27476(5.77%) | 当たり |")):
            self.assertIn(old, self.base.doc, old)
            c = self.base.with_doc(self.base.doc.replace(old, new, 1))
            self.assertNotEqual([], verdict_problems(c), old)
        # 開発の 5 本・全部の数が判定の表に混ざる(開発の型の外 4782 など)と赤
        c = self.base.with_doc(self.base.doc.replace(u"| 2481/2613(94.9%) | 当たり |", u"| 4782/1457(328.2%) | 当たり |", 1))
        self.assertTrue(any(u"混ざっている" in x for x in verdict_problems(c)))

    def test_g_9_a_confirmation_of_a_caught_difference_is_red_when_the_record_has_a_pass(self):
        u"""記録の変え方の通したが 1 以上なのに文書が「中身の違いを断る」を肯定すれば赤(否定の外)。記録の通したを 0 にすると封 §6 の旗(自分の欠陥を疑う)で赤。"""
        c = self.base
        self.assertGreaterEqual(pred_numbers(c.rec)[u"XJ0-8"][0], 1)
        cc = c.with_doc(c.doc.replace(u"受け口は、形が合っていれば中身の違う数を通す。", u"受け口は、形が合っていても中身の違いを断る。", 1))
        self.assertTrue(any(u"中身の違いを断る" in x for x in verdict_problems(cc)))
        for add in (u"受け口は中身が違う数を見つけて断る。", u"中身の違いは受け口が検出する。", u"形は合っているが中身が違う file は断る。"):
            self.assertTrue(any(u"中身の違いを断る" in x for x in verdict_problems(c.with_doc(c.doc + u"\n" + add + u"\n"))), add)
        # 否定の文(通した・断らなかった)は肯定に数えない
        self.assertEqual([], [x for x in verdict_problems(c) if u"中身の違いを断る" in x])
        c0 = c.copy()
        for d in accepted_prod(c0):
            for v in d[u"形は合っているが中身が違う"].values():
                if v[u"通した"]:
                    v[u"通した"] -= 1
                    v[u"断った"][u"R10"] += 1
        rebuild(c0)
        self.assertTrue(any(u"まず自分の欠陥を疑う" in x for x in verdict_problems(c0)) or pred_numbers(c0.rec)[u"XJ0-8"][0] >= 1)

    def test_h_1_the_sweep_over_every_number_direction_word_group_swap_cell_and_line_stays_red(self):
        c = self.base
        cases = all_doc_cases(c) + judge_rows_cases(c)
        results = run_doc_cases(c, cases)
        silent = [n for n, k in results if k is None]
        by_kind = collections.Counter(n.split(u" ")[0] for n, _ in results)
        self.assertEqual(sorted(EXPECTED_SILENT), sorted(silent))
        for kind, lo in MIN_CASES.items():
            self.assertGreaterEqual(by_kind[kind], lo, kind)
        self.assertGreater(len(results), 2800)

    def test_h_2_the_record_leaf_sweep_stays_red(self):
        results = run_record_sweep(self.base)
        silent = [n for n, k in results if k is None]
        self.assertEqual([], silent)
        self.assertGreater(len(results), 5800)

    def test_h_3_section3_prose_sweep_reports_what_stays_silent(self):
        u"""§3 は形で縛る(数の並び・記録との整合・語の留め)。§3 の中の文の削除・向きの語の反転で黙る所が在れば、それを数えて留める(増えたら赤)。"""
        c = self.base
        results = run_doc_cases(c, sec3_cases(c))
        silent = [n for n, k in results if k is None]
        self.assertEqual(sorted(SEC3_SILENT), sorted(silent))

    def test_h_4_every_added_or_dropped_next_candidate_is_red_in_the_section5_check_alone(self):
        u"""候補を足す・落とす・入れ替えるケース(W9)は、lines に頼らず §5 の検査だけで赤(封 §6 の (i)〜(v) の 5 つだけ)。"""
        cases = candidate_cases(self.base.doc)
        self.assertEqual(14, len(cases))
        for name, text in cases:
            self.assertNotEqual([], sec5_problems(self.base.with_doc(text)), name)


SEC3_SILENT = ()


if __name__ == "__main__":
    unittest.main()
