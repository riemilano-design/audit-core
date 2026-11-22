# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_COMPANY_EXCEL_SEAL_2026-11-22.md(aec0496d)の結果の文書 docs/XBRL_COMPANY_EXCEL_RESULT_2026-11-22.md(便 XE0)。

封の門 ``test_xbrl_company_excel_seal.py`` の次の段。**追跡されている記録・script・封・封の門・結果の文書と git の履歴だけを読む**(書類の置き場は読まない・道具は呼ばない・通信しない・鍵は読まない・xlsx は書かない)。
便 XA0 の結果の門 ``test_xbrl_sheet_wall_result.py`` の部品(読み・sha256・% の丸め・節の切り出し・数のトークン・禁止語・blob の道具)を読み込んで使う(門としては走らせない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表と、全部のセル・数・向きの語を 1 か所ずつ掃く ``SWEEPS`` で(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封・封の門の sha256(字で留める)・記録の script の sha256・封の commit の欄・記録の限界の欄(script の字)・材料の欄・型の欄ごとの出どころ(字で留める)
 b 記録の数え直し: 組ごとの数から、**script の関数を使わずに**、訓練の 3 組・判定の 60 組・全部の 63 組の集計の全部の欄・予測に要る数・旗を数え直す(組ごとの足し算の関係を含む)
 c 予測 XE0-1〜XE0-9 の当たり外れを、封 §4 の字から取った境(丸める前の整数で)と記録(判定の 60 組だけ)から決め直し、文書 §1 の表・件数と同じことを見る。
   封 §6 の決め(次の便の候補は (i)〜(iv) の 4 つだけ・5 つ目も封に無い候補も足さない・(i)(ii)(iv) は司令塔・(iii) と範囲の拡大は人間)と文書 §5 が合う。記録の決めたが違うが 1 以上なら「誤りなく受ける」を肯定しない
 d 結果の文書の数: §1・§2・§4・§5 の数は全部、記録から導く(組ごとの率の最小・中央・最大・組の数・止めた率・決めたが違うが在る書類などは門の中で組ごとから導き直す)。
   記録の数と字から文書の §3 以外の全部の行を組み直し、文書と行ごとに照らす(``render_doc``)。主な主張の文は断片でも縛る。
   **§3 の読み(記録に欄の無い読み。出どころは記録の監査の席)は記録に縛らず**、見出し・「測った数ではない」・字で留めた数の並び・記録から導ける数(118 の内訳 60・32+20+2・4・17 本・43 本・36 本・537 の内訳・502・229・8 行の表)・
   §3 だけの数(32・20・516・1028・9 桁)と主張が §3 の外に出ないことを縛る。§4 の数(35・479・7)は封の門の本数に、130・3・127 は記録に縛る
 e 文書の頭の負けと限界(封 §7 の 8 本・封 §6 の読み方)・禁止語・「XBRL を作れる」「専用の道具が要らない」「会社が Excel で出せる」「経理の人が書ける」「誤りなく受ける」「誤りが無くなる」「EDINET の検査に通る」を肯定で書かない・docID と EDINET コードの形
 f 封・script・記録・封の門が commit の blob と一致(結果の便で 0 行)・engine は封の commit から 0 行・順序・文書が書く commit の字が実の履歴と合う
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
from fractions import Fraction

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


WG = load_module("tests/measure/test_xbrl_sheet_wall_result.py", "xbrl_sheet_wall_result_gate_for_company_excel_result_gate")                # 便 XA0 の結果の門の部品。門としては走らせない
SG = load_module("tests/measure/test_xbrl_company_excel_seal.py", "xbrl_company_excel_seal_gate_for_result_gate")                # 封の門の部品。門としては走らせない
PR = WG.PR
MS = SG.MS

read, sha_file, guard, pct, section = WG.read, WG.sha_file, WG.guard, WG.pct, WG.section
ints_in, doc_number_tokens = WG.ints_in, WG.doc_number_tokens

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_company_excel_result.py"
DOC_REL = "docs/XBRL_COMPANY_EXCEL_RESULT_2026-11-22.md"
SCRIPT_COMMIT_SHORT = "7cc388be"                  # script と封の門を足した commit
RECORD_COMMIT_SHORT = "e59be6e6"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
HISTORY = collections.OrderedDict([
    (SEAL_REL, [SEAL_COMMIT_SHORT]), (SCRIPT_REL, [SCRIPT_COMMIT_SHORT]), (SEAL_GATE_REL, [SCRIPT_COMMIT_SHORT]), (RECORD_REL, [RECORD_COMMIT_SHORT])])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "c611402da78914bc397bdc60ee953d3d9c1e635143d774658f2cd997a6fefecb"),
    (SCRIPT_REL, "58b888fd5f9ae9c9a8698d392e6d0e7ad2337fafd31599fffbaaefc04fb97808"),
    (SEAL_GATE_REL, "b93279b36e7aaf795b259169aaf4ca2584a3b1f3c0d3213d58765ed2d771d7b1"),
    (SEAL_REL, "587c5218c7aae37fe9c922e8ee606f64b1db4065b013b33781ca15462e51b888")])
MATERIAL_PIN = collections.OrderedDict([
    (u"今年の側の書類の本数", 67), (u"今年の側の書類の file 名の並びの sha256", "f240150645a9b05a8d9bf5a9fe0ab89633ae338e42b8cc4d891dc04ca401e3f5"), (u"組の数", 63), (u"訓練の組の数", 3), (u"判定の組の数", 60),
    (u"除いた今年の書類の数", 4), (u"前の年の側の組の相手の file 名の並びの sha256", "8ddf19964316e3a88e72b0ea12c8a691f8a3520a317c3bb94cb7cd24b55a5cf6")])
ORIGIN_PIN = collections.OrderedDict([
    (u"名・個別か既定か・区分", u"去年から持ち越し"), (u"期の日", u"会社が書いた欄からそのまま"), (u"期の種類", u"規則で(日付が 1 つか 2 つか)"),
    (u"値の大きさ", u"会社が書いた欄からそのまま(表示の位は規則で)"), (u"値の符号", u"規則で(負の印)と去年から持ち越し(符号の向き)"),
    (u"単位の形・表示の位", u"規則で(単位の字の表の逆引き)"), (u"精度", u"規則で(数のセルの表示形式)"), (u"空か", u"会社が書いた欄からそのまま(「－」)")])
SEAL_TRAIN_PIN = collections.OrderedDict([(u"行の中の数の fact", 3434), (u"決めて全部同じ", 2636), (u"決めたが違う", 0), (u"止めた", 669)])      # 封 §0 の字

PAIR_COUNT, TRAIN_COUNT, JUDGE_COUNT, DOC67 = 63, 3, 60, 67
K_DOCS = u"書類"
K_SUM = u"集計"
K_ORIGIN = u"型の欄ごとの出どころ"
K_FLAG = u"§3 の旗"
G_TRAIN, G_JUDGE, G_ALL = u"訓練の 3 組", u"判定の 60 組", u"全部"
GROUPS = (G_TRAIN, G_JUDGE, G_ALL)
NOT_SUMMED = (u"番号",)
PRED_KEY = u"予測の判定に要る数(XE0-1〜XE0-9。判定の 60 組だけ。当たり・外れ)"
DOC_KEYS = (u"番号", u"行の中の数の fact", u"突き合わせの外", u"xlsx に書かなかった fact", u"D", u"決めて全部同じ", u"決めたが違う", u"止めた", u"決めたが違うの内訳", u"止めた理由ごと", u"守りの止め", u"場面", u"無くなった行")
OUTSIDE = (u"file", u"ix:nonFraction の fact", u"うち行の中の数の fact")
EXC = (u"行の字が空", u"型の外", u"単位が書けない", u"有効数字が 15 桁を超える")
FIELDS10 = (u"名", u"個別か既定か", u"区分", u"期の日", u"期の種類", u"値", u"単位の形", u"表示の位", u"精度", u"空か")
INNER = (u"欄ごと", u"符号だけ違う", u"符号だけ違うのうち答えの値が符号つきの 0", u"去年が空で既定の順を使った")
STOPS7 = (u"去年に無い行", u"候補が 2 つ以上", u"表の頭が違う", u"期が違う", u"番号つき", u"単位が違う", u"符号の向きが 2 通り")
GUARD_OF = collections.OrderedDict([(u"表の頭が違う", u"守り G 表の頭"), (u"期が違う", u"守り G1 期"), (u"番号つき", u"守り G3 番号つき"), (u"単位が違う", u"守り G2 単位")])
SCENE = (u"負の印あり", u"表示の数が 0", u"空", u"符号の向きが逆", u"去年の同じ鍵と表示の位が違う")
SCENE_SUB = (u"件数", u"決めて全部同じ", u"決めたが違う", u"止めた")
IDS = tuple(u"XE0-%d" % i for i in range(1, 10))
PK = (u"XE0-1 決めて全部同じ ÷ D", u"XE0-2 決めたが違う ÷ D(1 fact 以上)", u"XE0-3 決めたが違うのうち符号だけ違う", u"XE0-4 止めた ÷ D", u"XE0-5 守りの止めのうち正しかった止め",
      u"XE0-6 守り G1(期)と G2(単位)の止め ÷ D(1 fact 以上)", u"XE0-7 単位が書けない・15 桁を超える ÷ 行の中の数の fact", u"XE0-8 決めたが違うが 0 の書類",
      u"XE0-9 決めて全部同じ ÷ その書類の D が 95.0% 以上の書類")
FLAG_KEYS = (u"訓練の 3 組の数", u"封 §0 の数", u"§0 と違う")

# 封の字(封の門が script と照らし、ここでは文書が引く字の在り処を縛る)
READ_WAYS = (u"「会社が Excel で出せる」「経理の人が書ける」とは言わない", u"決めたが違うが 1 fact でも在れば「誤りなく受ける」とは言わない", u"**合って当たり前**",
             u"「XBRL の知識が要る欄は 0」は xlsx の欄の決め(§2-1)から **作りで** そうなる。測った数として書かない。", u"止めた行は、会社へ問いとして返す行。この便は返し方・答え方を測らない。")
CAND_CORES = (u"止めた行を「候補つきの問い」として返したとき、候補の中に答えが在る割合を数える", u"去年の書類が無い会社の道を数える", u"人が実際にこの Excel を書く", u"文の fact と行の中でない fact を会社の側の欄に入れる")
CAND_SEAL_FRAGS = ((u"止めた行を「候補つきの問い」として返したとき、候補の中に答えが在る割合を数える", u"(0 USD)"), (u"去年の書類が無い会社", u"の道を数える", u"(0 USD)"),
                   (u"人が実際にこの Excel を書く", u"人間が決める"), (u"文の fact", u"行の中でない fact を会社の側の欄に入れる", u"(0 USD)"))
BOUND_SEAL_PHRASES = tuple(x for pair in SG.SEAL_BOUND_TEXT.values() for x in pair) + READ_WAYS + (
    u"(i)", u"(ii)", u"(iii)", u"(iv)", u"続けるか・どれにするかは、前からの委任の内側((i)(ii)(iv))なら司令塔が決め、(iii) と範囲の拡大は人間が決める。",
    u"行の中の数の fact 3434・決めて全部同じ 2636・決めたが違う 0・止めた 669", u"番号 1・2・3 が訓練、番号 4〜63 が判定の 60 組", u"**言えない**" if False else u"言えない" if False else u"数えるだけ")
# 文書の頭の限界 8 本(封 §7)。封の字そのままでなく、文書の書き方(xlsx → Excel・測らない → 測っていない)で書いてある。1 本ごとに、封の限界と文書の頭の 1 つの行の両方に在る断片で縛る
LIMIT_FRAGS = (
    (u"道具で作られ受理された書類から起こした", u"会社の手元の原稿ではない", u"経理の人が同じ字・同じ並びで書くか"),
    (u"鍵の欄(見出し・表の番号・列の番号・表の頭の印)は「去年の書類と同じ並びの表に入れる」ことを会社に求める", u"会社の負担であり、この便は負担を測"),
    (u"単位の字は答えから表で作った字。", u"会社が実際に書く単位の字"),
    (u"期の日は答えの文脈の日をそのまま書いた。会社が期をどう書くかは見ていない。",),
    (u"去年の書類が在る会社の、続いた 2 年だけ。63 組(判定は 60 組)。有報だけ。",),
    (u"数の fact で行の中に在るものだけ。文の fact・隠しの fact・行の外の数の fact・行の字が空の fact は扱",),
    (u"XBRL の側を組んでいない。決めた型の行から XBRL が作れるかは便 XM0 の範囲(型も対応表も答えから作った)。",),
    (u"答えは提出された書類そのもので、提出された書類の誤りは見ていない。",))
HEAD_PHRASES = (u"先に負けと限界を書く", u"記録から 1 つずつ読んだもの", u"記録に欄の無い読み", u"予測 2 本は外れ", u"黙って違う fact は 0 ではない", u"「誤りなく受ける」とは言えない",
                u"封を書く前の下調べの見落とし", u"Excel を実際には通さなかった", u"封は直していない", u"外れは外れとして残す", u"去年から持ち越す決め方の負け", u"この便の守りでは防げなかった",
                u"止めなくても合っていた行を多く止めた", u"5 個に 1 個は止まる", u"会社の手元の原稿ではない", u"「会社が Excel で出せる」「経理の人が書ける」とは言わない", u"合って当たり前",
                u"成果として読まない", u"「XBRL の知識が要る欄は 0」", u"測った数ではない", u"返し方・答え方は測っていない", u"盲検ではない", u"「未見で当てた」とは言わない", u"費用は 0 USD",
                u"engine(`core/`・`adapters/`)は 0 行", u"日付つきの補足", u"封 §0 の申告の数", u"封 §2-2 の字と実装が合わない所", u"XE0-3 の読み方", u"XE0-8 の当たりは境から 1 本",
                u"XE0-7 の 0 は作りに寄る", u"作りから黙る変異が 7 本在る", u"言えない")
PHRASES = (u"封も予測も結果を見てから書き換えていない", u"判定は丸める前の数でした", u"予測の判定には使わない", u"測った数ではない", u"記録から言えること", u"記録から言えないこと",
           u"XBRL は組んでいない", u"道具には掛けていない", u"人は Excel を書いていない", u"独立監査 REVISE → 直し → REVISE → 直し → GO", u"次の便の候補は (i)", u"(iii) と範囲の拡大は人間が決める")
MAIN_CLAIMS = (u"予測 2 本は外れ", u"黙って違う fact は 0 ではない", u"Excel を実際には通さなかった", u"封は直していない", u"去年から持ち越す決め方の負け", u"この便の守りでは防げなかった",
               u"5 個に 1 個は止まる", u"会社の手元の原稿ではない", u"合って当たり前", u"成果として読まない", u"「未見で当てた」とは言わない", u"外れは外れとして残す", u"「誤りなく受ける」とは言えない",
               u"予測(40% 以上 65% 以下)より多い側の外れ", u"止めなくても合っていた行を多く止めた", u"「XBRL の知識が要る欄は 0」は Excel の欄の決めから作りでそうなる", u"当たり 7・外れ 2",
               u"返し方・答え方は測っていない", u"(i)(ii)(iv) は前からの委任の内側で司令塔が決める")
QUOTED = re.compile(u"「[^」]*(?:作れる|専用の道具が要らない|人が書ける|誤りが無くなる|Excel で出せる|誤りなく受ける|検査に通る)[^」]*」")
AFFIRM_WORDS = (u"作れる(?!か)", u"作れます", u"専用の道具が要らない", u"人が書ける(?!か)", u"誤りが無くなる", u"Excel で出せる(?!か)", u"誤りなく受ける", u"検査に通る(?!こと|か)")
FORBIDDEN_WORDS = tuple(WG.FORBIDDEN_WORDS)
STRUCTURAL = WG.STRUCTURAL
# 記録から組んだ値の外に在ってよい数(字で留める。封の境・文書の見出しや説明の数)。理由は 1 つずつ:
#   1 2 3 4 5 6 7 8 9 10 = 項の番号・「6 つ」「1 つ」「2 本」「5 組」「4 本」・判定の件数・各行の端数 / 74.0 0.5 30 16.0 26.0 40 65 2.0 1.0 35 95 = 封 §4 の境(予測の字の要約と本文)
#   90 80 70 60 = 書類ごとの率の見出し(90% 以上・80% 以上・70% 以上・60% 未満) / 60 63 67 15 = 組・書類の数の見出し・15 桁 / 130 は記録(全部の「符号だけ違う」)から別に導く
RESIDUAL_OK = set([u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"10", u"74.0", u"0.5", u"30", u"16.0", u"26.0", u"40", u"65", u"2.0", u"1.0", u"35", u"95", u"90", u"80", u"70", u"60", u"63", u"67", u"15"])
SEC3_LINES = (
    (u"**決めたが違うのうち、符号つきの 0 でない 118 の中身。**", (u"0", u"118")),
    (u"個別か既定かが替わった 60。", (u"60", u"1", u"1")),
    (u"同じ行の字が別の区分の科目に替わった 32", (u"32",)),
    (u"上から何番目かで決まる相手が入れ替わった 20", (u"20", u"2")),
    (u"会社が足した科目と標準の科目が入れ替わった 2。", (u"2",)),
    (u"member が替わった 4。", (u"4",)),
    (u"118 は判定の 60 本のうち 17 本に在り", (u"118", u"60", u"17", u"1")),
    (u"**符号の向きの持ち越しそのものの誤りは見つからなかった。**", (u"0", u"0", u"43", u"36")),
    (u"**型の外 537 の中身。**", (u"537", u"516", u"20", u"1", u"1", u"502")),
    (u"**0 の欄の確かめ。**", (u"0",)),
    (u"単位が書けない 0・15 桁を超える 0:", (u"0", u"15", u"0", u"8", u"9")),
    (u"守り G2(単位)0:", (u"0", u"8", u"0")),
    (u"符号の向きが 2 通り 0:", (u"2", u"0")),
    (u"守り G1(期)も、順を無視すれば 1028 に当たる。", (u"1028", u"229")),
    (u"**Excel の実物の字。**", ()),
    (u"**Excel の実物の検査**(63 本)", (u"63", u"2", u"0", u"0", u"0", u"8")),
)
SEC3_ONLY_PHRASES = (u"個別か既定かが替わった", u"別の区分の科目に替わった", u"上から何番目かで決まる相手", u"会社が足した科目と標準の科目が入れ替わった", u"member が替わった", u"期の名が作れない文脈",
                     u"単位の形が作れない", u"表示の形式と値の字", u"順を無視すれば", u"崩れた字", u"隠しのシート", u"最大 9 桁", u"17 本に在り", u"43 本になる", u"符号の向きの持ち越しそのものの誤り")      # §3 の外に主張として出てはならない字
SEC3_PHRASES = (u"記録の監査の席が実物を読んで分けた数", u"記録にも門にも縛っていない", u"全部、同じ鍵の行が去年と今年で別のものを指していた類", u"半分は 1 本の書類。年によらず決まる類とは言わない",
                u"見つからなかった", u"止めなかったものは全部正しく決まった", u"既定の「順」が逆になった fact も見つからなかった", u"Excel を通さない実装では「符号だけ違う」は 0 で",
                u"決めたが違うが 0 の書類は 43 本になる", u"XE0-8 の判定は記録の 36 本でした", u"1 つの書類が 502 を占める", u"表の 8 行だけだった", u"表示の字の有効数字は最大 9 桁",
                u"全部、先の止めに取られた", u"「単位の違いは起きない」とは言わない", u"「守り G2 まで届いたものは 0」", u"去年の表の鍵で符号の向きが両方在るものは無かった", u"229 は先の止めの残り",
                u"道具が抜いた字そのもの", u"経理の人が書く字とは違う", u"シートは 2 枚だけ", u"XBRL の言葉(要素の名の接頭辞・文脈・`decimals` の字など)は見つからなかった", u"単位の字は 8 種",
                u"測った数ではない", u"記録は「なぜ違ったか」「なぜ 0 か」を分けていない", u"期の名が作れない文脈 516・単位の形が作れない 20・表示の形式と値の字 1", u"型の外でない数の fact の単位の形と表示の位の組は",
                u"符号の向きが逆の fact は、止めなかったものは全部正しく決まった")      # §3 の中の向きの語・言い切りの形を決める言い回し(§3 の文の削除・向きの語の反転の掃きが黙らないように留める)


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


def pct_fr(x):
    u"""分数の % を小数第 1 位まで四捨五入した字。"""
    return pct(x.numerator, x.denominator)


def median(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def tsum(trees):
    u"""同じ形の木の列 → 葉を足した木(script の関数を使わない別の足し方)。"""
    first = trees[0]
    out = collections.OrderedDict()
    for k, v in first.items():
        if isinstance(v, dict):
            out[k] = tsum([t[k] for t in trees])
        else:
            out[k] = sum(t[k] for t in trees)
    return out


def agg_of(docs):
    body = [collections.OrderedDict((k, v) for k, v in d.items() if k not in NOT_SUMMED) for d in docs]
    return collections.OrderedDict([(u"組", len(docs)), (u"数", tsum(body) if body else collections.OrderedDict())])


def split_docs(rec):
    docs = rec[K_DOCS]
    return [d for d in docs if d[u"番号"] <= TRAIN_COUNT], [d for d in docs if d[u"番号"] > TRAIN_COUNT]


def leaves(o):
    if isinstance(o, dict):
        for v in o.values():
            for x in leaves(v):
                yield x
    else:
        yield o


def doc_problems(d):
    u"""組 1 つの中の関係(足し算・大小)。"""
    out = []
    n = d.get(u"番号")
    if list(d) != list(DOC_KEYS):
        return [u"組 %s の欄が違う" % n]
    if any((isinstance(x, bool) or not isinstance(x, int) or x < 0) for x in leaves(d)):
        out.append(u"組 %d に負の数か整数でない値が在る" % n)
        return out
    o, x, inner, sp, gs, sc = d[u"突き合わせの外"], d[u"xlsx に書かなかった fact"], d[u"決めたが違うの内訳"], d[u"止めた理由ごと"], d[u"守りの止め"], d[u"場面"]
    if list(o) != list(OUTSIDE) or list(x) != list(EXC) or list(inner) != list(INNER) or list(sp) != list(STOPS7) or list(gs) != list(GUARD_OF.values()) or list(sc) != list(SCENE):
        return out + [u"組 %d の欄の並びが違う" % n]
    if list(inner[u"欄ごと"]) != list(FIELDS10) or any(list(v) != [u"止めた", u"正しかった止め"] for v in gs.values()) or list(sc[SCENE[-1]]) != list(SCENE_SUB):
        return out + [u"組 %d の内側の欄の並びが違う" % n]
    if d[u"D"] != d[u"行の中の数の fact"] - o[OUTSIDE[2]] - sum(x.values()):
        out.append(u"組 %d の D が 行の中の数の fact − 突き合わせの外の行の中 − 書かなかった fact と違う" % n)
    if d[u"決めて全部同じ"] + d[u"決めたが違う"] + d[u"止めた"] != d[u"D"]:
        out.append(u"組 %d の 同じ・違う・止めた の合計が D と違う" % n)
    if sum(inner[u"欄ごと"].values()) != d[u"決めたが違う"]:
        out.append(u"組 %d の決めたが違うの欄ごとの合計が決めたが違うと違う(1 つの fact が 2 つ以上の欄で違わない)" % n)
    if not (inner[u"欄ごと"][u"値"] >= inner[u"符号だけ違う"] >= inner[u"符号だけ違うのうち答えの値が符号つきの 0"] and inner[u"去年が空で既定の順を使った"] <= d[u"決めたが違う"]):
        out.append(u"組 %d の決めたが違うの内訳の大小が違う" % n)
    if sum(sp.values()) != d[u"止めた"]:
        out.append(u"組 %d の止めた理由ごとの合計が止めたと違う" % n)
    for r, lab in GUARD_OF.items():
        if gs[lab][u"止めた"] != sp[r] or gs[lab][u"正しかった止め"] > gs[lab][u"止めた"]:
            out.append(u"組 %d の守りの止め(%s)が止めた理由と合わない" % (n, lab))
    s5 = sc[SCENE[-1]]
    if s5[u"件数"] != s5[u"決めて全部同じ"] + s5[u"決めたが違う"] + s5[u"止めた"]:
        out.append(u"組 %d の場面(表示の位が違う fact)の分けが件数と合わない" % n)
    if o[OUTSIDE[2]] > o[OUTSIDE[1]]:
        out.append(u"組 %d の突き合わせの外の行の中の数が ix:nonFraction の数より多い" % n)
    return out


def pred_numbers(rec):
    u"""判定の 60 組から、XE0-1〜XE0-9 の (数, 分母) を導く(XE0-8・9 は 書類の数, 判定の組の数)。"""
    docs = split_docs(rec)[1]
    g = agg_of(docs)[u"数"]
    inner, gs, ex = g[u"決めたが違うの内訳"], g[u"守りの止め"], g[u"xlsx に書かなかった fact"]
    D = g[u"D"]
    g_stop = sum(v[u"止めた"] for v in gs.values())
    g_ok = sum(v[u"正しかった止め"] for v in gs.values())
    g12 = gs[u"守り G1 期"][u"止めた"] + gs[u"守り G2 単位"][u"止めた"]
    no_diff = sum(1 for d in docs if d[u"決めたが違う"] == 0)
    high = sum(1 for d in docs if 100 * d[u"決めて全部同じ"] >= 95 * d[u"D"])
    return collections.OrderedDict([
        (u"XE0-1", (g[u"決めて全部同じ"], D)), (u"XE0-2", (g[u"決めたが違う"], D)), (u"XE0-3", (inner[u"符号だけ違う"], g[u"決めたが違う"])), (u"XE0-4", (g[u"止めた"], D)),
        (u"XE0-5", (g_ok, g_stop)), (u"XE0-6", (g12, D)), (u"XE0-7", (ex[EXC[2]] + ex[EXC[3]], g[u"行の中の数の fact"])), (u"XE0-8", (no_diff, len(docs))), (u"XE0-9", (high, len(docs)))])


def judge_nums(p):
    u"""封 §4 の境(整数のまま)。p は pred_numbers の形。値は (当たりか, 外れた向き)。"""
    O = collections.OrderedDict
    out = O()
    a, b = p[u"XE0-1"]
    ok = b > 0 and 1000 * a >= 740 * b
    out[u"XE0-1"] = (ok, u"" if ok else u"下")
    a, b = p[u"XE0-2"]
    lo, hi = a >= 1, b > 0 and 1000 * a <= 5 * b
    out[u"XE0-2"] = (lo and hi, u"" if lo and hi else u"下" if not lo else u"上")
    a, b = p[u"XE0-3"]
    out[u"XE0-3"] = (a <= 30, u"" if a <= 30 else u"上")
    a, b = p[u"XE0-4"]
    lo, hi = b > 0 and 1000 * a >= 160 * b, b > 0 and 1000 * a <= 260 * b
    out[u"XE0-4"] = (lo and hi, u"" if lo and hi else u"下" if not lo else u"上")
    a, b = p[u"XE0-5"]
    lo, hi = b > 0 and 100 * a >= 40 * b, b > 0 and 100 * a <= 65 * b
    out[u"XE0-5"] = (lo and hi, u"" if lo and hi else u"下" if not lo else u"上")
    a, b = p[u"XE0-6"]
    lo, hi = a >= 1, b > 0 and 1000 * a <= 20 * b
    out[u"XE0-6"] = (lo and hi, u"" if lo and hi else u"下" if not lo else u"上")
    a, b = p[u"XE0-7"]
    ok = b > 0 and 1000 * a <= 10 * b
    out[u"XE0-7"] = (ok, u"" if ok else u"上")
    out[u"XE0-8"] = (p[u"XE0-8"][0] >= 35, u"" if p[u"XE0-8"][0] >= 35 else u"下")
    out[u"XE0-9"] = (p[u"XE0-9"][0] <= 2, u"" if p[u"XE0-9"][0] <= 2 else u"上")
    return O((k, out[k]) for k in IDS)


def judge(rec):
    return judge_nums(pred_numbers(rec))


def miss_ids(j):
    return [k for k in IDS if not j[k][0]]


def pred_expected(rec):
    O = collections.OrderedDict
    out = O()
    j = judge(rec)
    for key, (id_, (a, b)) in zip(PK, pred_numbers(rec).items()):
        if id_ == u"XE0-3":
            out[key] = O([(u"fact", a), (u"決めたが違う", b), (u"当たり", j[id_][0])])
        elif id_ in (u"XE0-8", u"XE0-9"):
            out[key] = O([(u"書類", a), (u"分母", b), (u"当たり", j[id_][0])])
        else:
            out[key] = O([(u"率", O([(u"fact", a), (u"分母", b), (u"%", float(pct(a, b)) if b else None)])), (u"当たり", j[id_][0])])
    return out


def flags_expected(rec):
    u"""封 §3 の「§0 と違う」の旗: 訓練の 3 組の 4 つの数が封 §0 の字の数と違えば立つ。"""
    t = agg_of(split_docs(rec)[0])[u"数"]
    got = collections.OrderedDict((k, t[k]) for k in SEAL_TRAIN_PIN)
    return collections.OrderedDict([(FLAG_KEYS[0], got), (FLAG_KEYS[1], collections.OrderedDict(SEAL_TRAIN_PIN)), (FLAG_KEYS[2], dict(got) != dict(SEAL_TRAIN_PIN))])


def recount_problems(c):
    rec = c.rec
    out = []
    docs = rec[K_DOCS]
    m = rec[u"材料"]
    nums = [d[u"番号"] for d in docs]
    if len(docs) != PAIR_COUNT or nums != sorted(set(nums)) or nums[-1] != DOC67 or any(n < 1 for n in nums):
        return [u"組の番号が昇順の 63 個(最大 67)でない"]
    for k, v in MATERIAL_PIN.items():
        if m[k] != v:
            out.append(u"材料の欄が字で留めた値と違う: %s" % k)
    if list(m) != list(MATERIAL_PIN):
        out.append(u"材料の欄の並びが違う")
    if m[u"今年の側の書類の本数"] - m[u"組の数"] != m[u"除いた今年の書類の数"]:
        out.append(u"材料の書類の本数 − 組の数 が除いた書類の数と違う")
    train, judge_docs = split_docs(rec)
    if len(train) != TRAIN_COUNT or len(judge_docs) != JUDGE_COUNT:
        return out + [u"訓練の 3 組と判定の 60 組の分け(番号 3 / 4 の境)が違う"]
    for d in docs:
        out.extend(doc_problems(d))
    if list(rec[K_SUM]) != list(GROUPS):
        return out + [u"集計の欄の名が違う"]
    for key, ds in ((G_TRAIN, train), (G_JUDGE, judge_docs), (G_ALL, docs)):
        if norm(rec[K_SUM][key]) != norm(agg_of(ds)):
            out.append(u"%s の集計が組ごとの数から数え直した値と違う" % key)
    if list(rec[PRED_KEY]) != list(PK):
        return out + [u"予測の判定に要る数の欄の名が違う"]
    if norm(rec[PRED_KEY]) != norm(pred_expected(rec)):
        out.append(u"予測の判定に要る数・当たり外れが組ごとから作り直した値と違う")
    if list(rec[K_FLAG]) != list(FLAG_KEYS):
        return out + [u"旗の欄の名が違う"]
    if norm(rec[K_FLAG]) != norm(flags_expected(rec)):
        out.append(u"旗が組ごとから作り直した値と違う")
    if norm(rec[K_ORIGIN]) != norm(ORIGIN_PIN):
        out.append(u"型の欄ごとの出どころが字で留めた値と違う")
    if rec[K_SUM][G_JUDGE][u"組"] != JUDGE_COUNT or rec[K_SUM][G_TRAIN][u"組"] != TRAIN_COUNT or rec[K_SUM][G_ALL][u"組"] != PAIR_COUNT:
        out.append(u"集計の組の数が 3・60・63 でない")
    if [u"seal", u"封の commit", u"step", u"この script の sha256", u"材料", K_DOCS, K_SUM, PRED_KEY, K_ORIGIN, K_FLAG, u"限界"] != list(rec):
        out.append(u"記録の欄の並びが違う")
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
    if c.rec[u"step"] != u"XE0(会社が Excel で出すとしたら、XBRL の言葉を書かない欄だけで今年の型はどれだけ決まり・黙って違い・止まるか)(0 USD・engine は 0 行)":
        out.append(u"記録の step の欄が違う")
    return out


DATE_FORM = re.compile(r"(?<![0-9])(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?![0-9])|(?<![0-9])(?:19|20)\d{2}年\d{1,2}月")


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    out = []
    try:
        MS.check_clean(c.rec, text)
    except BaseException as exc:                    # noqa: BLE001
        out.append(u"記録の検査(欄・形・file の名・日付)が止める: %s" % type(exc).__name__)
    if WG.DOCID_FORM.search(re.sub(r"[0-9a-fA-F]{32,}", u"", text)) or WG.ECODE_FORM.search(text):
        out.append(u"記録に docid か EDINET コードの形が在る")
    if DATE_FORM.search(text.replace(SEAL_REL, u"")):
        out.append(u"記録に日付の形が在る(封 §3 は日付を持たないと決めた。門が見る)")
    return out


def seal_s6_text(seal):
    return section(seal, u"## §6 ", u"## §7 ")


def bound_problems(c):
    ps = plain(c.seal)
    out = [u"封に字が無い: %s" % p[:24] for p in BOUND_SEAL_PHRASES if p not in c.seal and plain(p) not in ps]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    rows = [ln for ln in sec4.splitlines() if re.match(r"^\| XE0-\d", ln)]
    if len(rows) != 9:
        out.append(u"封 §4 の表の行が 9 でない")
    sec7 = section(c.seal, u"## §7 ", None)
    if len([ln for ln in sec7.splitlines() if ln.startswith(u"- ")]) != 8:
        out.append(u"封 §7 の限界の行が 8 行でない")
    s6 = seal_s6_text(c.seal)
    marks = re.findall(u"^  - \\((i|ii|iii|iv)\\) ", s6, re.M)
    if marks != [u"i", u"ii", u"iii", u"iv"] or re.search(u"\\(v\\)", s6):
        out.append(u"封 §6 の次の便の候補が (i)〜(iv) の 4 つだけでない")
    cl = [ln for ln in s6.splitlines() if re.match(u"^  - \\((i|ii|iii|iv)\\) ", ln)]
    for ln, frags in zip(cl, CAND_SEAL_FRAGS):
        for fr in frags:
            if fr not in ln:
                out.append(u"封 §6 の候補の行に字が無い: %s" % fr[:16])
    return out


# ======================================================================================================
# c 当たり外れの決め直し(封 §4 の境。丸める前の整数。判定の 60 組)
PRED_TEXT = collections.OrderedDict([
    (u"XE0-1", u"決めて全部同じ ÷ D は 74.0% 以上"), (u"XE0-2", u"決めたが違う ÷ D は 0.5% 以下で、1 fact 以上"), (u"XE0-3", u"決めたが違うのうち「符号だけ違う」は 30 fact 以下"),
    (u"XE0-4", u"止めた ÷ D は 16.0% 以上 26.0% 以下"), (u"XE0-5", u"守りの止めのうち「正しかった止め」は 40% 以上 65% 以下"), (u"XE0-6", u"守り G1(期)と G2(単位)の止めは 1 fact 以上で、D の 2.0% 以下"),
    (u"XE0-7", u"「単位が書けない」と「15 桁を超える」は、行の中の数の fact の 1.0% 以下"), (u"XE0-8", u"決めたが違うが 0 の書類は 35 本以上"), (u"XE0-9", u"決めて全部同じが 95% 以上の書類は 2 本以下")])


def cell_text(rec, key):
    p = pred_numbers(rec)[key]
    if key == u"XE0-3":
        return u"%d fact" % p[0]
    if key in (u"XE0-8", u"XE0-9"):
        return u"%d 本(%d 本のうち)" % p
    return f(*p)


def expected_cells(c):
    out = collections.OrderedDict()
    for k, (ok, way) in judge(c.rec).items():
        out[k] = (cell_text(c.rec, k), u"当たり" if ok else u"外れ")
    return out


CAND_LINE_HEAD = u"- 封 §6 の次の便の候補は "
CAND_LINE = CAND_LINE_HEAD + u"・".join(u"(%s) %s" % (m, x) for m, x in zip((u"i", u"ii", u"iii", u"iv"), CAND_CORES)) + u"。"
DECIDE_LINE = u"- (i)(ii)(iv) は前からの委任の内側で司令塔が決める。(iii) と範囲の拡大は人間が決める。"


def sec5_problems(c):
    u"""封 §6(次の便の候補は (i)〜(iv) の 4 つだけ。(i)(ii)(iv) は司令塔・(iii) と範囲の拡大は人間)と文書 §5 が合う。5 つ目・封に無い候補を足すと赤。"""
    out = []
    sec5 = plain(section(c.doc, u"## §5 ", None))
    lines = [ln for ln in sec5.splitlines() if ln.strip()][1:]
    cand = [ln for ln in lines if CAND_LINE_HEAD in ln]
    if len(lines) != 4:
        out.append(u"§5 の行が 4 つでない(候補の 1 行を足す・引くと赤): %d" % len(lines))
    if cand != [CAND_LINE]:
        out.append(u"§5 の次の便の候補の行が、封 §6 の (i)〜(iv) の 4 つだけの形と違う")
    marks = re.findall(u"\\((i|ii|iii|iv|v|vi|vii)\\)", sec5)
    if marks != [u"i", u"ii", u"iii", u"iv", u"i", u"ii", u"iv", u"iii"]:
        out.append(u"§5 の候補の見出しが (i)(ii)(iii)(iv) の 4 つ(と決めの行の (i)(ii)(iv)・(iii))だけでない: %s" % u",".join(marks))
    if DECIDE_LINE not in lines:
        out.append(u"§5 に「(i)(ii)(iv) は前からの委任の内側で司令塔が決める。(iii) と範囲の拡大は人間が決める。」が無い")
    if sec5.count(u"候補") != 3 or sec5.count(u"次の便") != 1:
        out.append(u"§5 の「候補」「次の便」の字の数が違う(封に無い候補の字を足している)")
    for core in CAND_CORES:
        if sec5.count(core) != 1:
            out.append(u"§5 に封 §6 の候補の字が 1 つずつ無い: %s" % core[:12])
    s6 = seal_s6_text(c.seal)
    if sorted(re.findall(u"^  - \\((i|ii|iii|iv)\\) ", s6, re.M)) != sorted([u"i", u"ii", u"iii", u"iv"]):
        out.append(u"封 §6 の候補が 4 つでない")
    if u"続けるか・どれにするかは、前からの委任の内側((i)(ii)(iv))なら司令塔が決め、(iii) と範囲の拡大は人間が決める。" not in s6:
        out.append(u"封 §6 の決めの字が無い")
    return out


def verdict_problems(c):
    rec = c.rec
    j = judge(rec)
    want = expected_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XE0-\d+)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XE0-1〜XE0-9 でない"]
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
    if not re.search(r"^\| XE0-1\(主\) \|", c.doc, re.M):
        out.append(u"XE0-1 の行に「(主)」が無い(封 §4 の主の読み)")
    for k in IDS[1:]:
        if re.search(r"^\| %s\(主\) \|" % k, c.doc, re.M):
            out.append(u"%s の行に「(主)」が付いている(封 §4 の主は XE0-1 だけ)" % k)
    hits = sum(1 for v in j.values() if v[0])
    if u"- 当たり %d・外れ %d。" % (hits, len(j) - hits) not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = plain(c.doc.split(u"## §1")[0])
    miss = miss_ids(j)
    if u"判定した %d 本は 当たり %d・外れ %d。" % (len(j), hits, len(j) - hits) not in head:
        out.append(u"文書の頭の件数が決め直した値と違う")
    if miss:
        if u"予測 %d 本は外れ。 外れは %s。" % (len(miss), u" と ".join(miss) if len(miss) == 2 else u"・".join(miss)) not in head:
            out.append(u"外れた予測の言い切りが文書の頭に無い(%s)" % u"・".join(miss))
    elif re.search(u"予測 [0-9]+ 本は外れ", head):
        out.append(u"外れが無いのに文書の頭が外れと書いている")
    if u"XE0-1" in miss:
        if u"主の予測(XE0-1)は外れ" not in head:
            out.append(u"主の予測が外れなのに、文書の頭に「主の予測(XE0-1)は外れ」が無い")
    elif u"主の予測(XE0-1)は当たり" not in head or re.search(u"主の予測[^。]*は外れ", head):
        out.append(u"主の予測は当たりなのに文書の頭の書き方が合わない")
    # 記録の「当たり」の欄と決め直しが同じ(記録の側の整合は recount が見る)
    for key, (id_, (ok, way)) in zip(PK, j.items()):
        if rec[PRED_KEY][key][u"当たり"] != ok:
            out.append(u"記録の当たりの欄が決め直した判定と違う: %s" % id_)
    # 判定の表に 3 組・63 組の数が混ざらない(判定の 60 組の数だけ)
    only_other = set()
    for key in (G_TRAIN, G_ALL):
        ints_in(rec[K_SUM][key], only_other)
    only_judge = set()
    ints_in(rec[K_SUM][G_JUDGE], only_judge)
    ints_in(rec[PRED_KEY], only_judge)
    mixed = [t for ln in rows for t in doc_number_tokens(rows[ln][1]) if t in only_other and t not in only_judge and t not in STRUCTURAL]
    if mixed:
        out.append(u"判定の表に 3 組・63 組だけの数が混ざっている: %s" % u",".join(mixed))
    # 記録の決めたが違うが 1 以上なら「誤りなく受ける」を肯定しない(0 ならまず自分の欠陥を疑う旗)
    if rec[K_SUM][G_JUDGE][u"数"][u"決めたが違う"] >= 1:
        for i, ln in enumerate(c.doc.splitlines(), 1):
            if u"誤りなく受ける" in ln and not any(w in ln for w in (u"言えない", u"言わない")):
                out.append(u"記録の決めたが違うは 1 以上なのに、文書の %d 行目が「誤りなく受ける」を否定の外で書いている" % i)
    else:
        out.append(u"記録の決めたが違うが 0(封 §6: 先に自分の欠陥を疑う)")
    return out


# ======================================================================================================
# d 文書の数・主な主張の文(§3 以外の全部の行を記録と字から組み直す)
def cached(c, key, fn):
    if key not in c.cache:
        c.cache[key] = fn()
    return c.cache[key]


def inner_of(d, k):
    return d[u"決めたが違うの内訳"][u"欄ごと"][k]


def stat_values(rec):
    u"""組ごとから導く数(判定の 60 組)。"""
    train, judge_docs = split_docs(rec)
    same_r = sorted(Fraction(d[u"決めて全部同じ"], d[u"D"]) for d in judge_docs)
    stop_r = sorted(Fraction(d[u"止めた"], d[u"D"]) for d in judge_docs)
    diffs = [d[u"決めたが違う"] for d in judge_docs]
    outs = [d[u"xlsx に書かなかった fact"][EXC[1]] for d in judge_docs]
    nokey = [d[u"止めた理由ごと"][STOPS7[0]] for d in judge_docs]
    nonsign = [inner_of(d, u"名") + inner_of(d, u"個別か既定か") + inner_of(d, u"区分") for d in judge_docs]
    g = agg_of(judge_docs)[u"数"]
    return collections.OrderedDict([
        (u"same", (pct_fr(same_r[0]), pct_fr(median(same_r)), pct_fr(same_r[-1]), sum(1 for x in same_r if x * 100 >= 90), sum(1 for x in same_r if x * 100 >= 80),
                   sum(1 for x in same_r if x * 100 >= 70), sum(1 for x in same_r if x * 100 < 60))),
        (u"stop", (pct_fr(stop_r[0]), pct_fr(median(stop_r)), pct_fr(stop_r[-1]))),
        (u"diff", (sum(1 for x in diffs if x >= 1), max(diffs), sum(sorted(diffs, reverse=True)[:5]), sum(1 for x in diffs if x == 0))),
        (u"outs", (sum(1 for x in outs if x >= 1), max(outs))),
        (u"nokey", (sum(sorted(nokey, reverse=True)[:5]), max(nokey))),
        (u"nonsign", (sum(nonsign), sum(1 for x in nonsign if x >= 1), sum(1 for x in nonsign if x == 0), max(nonsign), max(inner_of(d, u"個別か既定か") for d in judge_docs))),
        (u"files", [d[u"突き合わせの外"][OUTSIDE[0]] for d in judge_docs]),
        (u"train", agg_of(train)[u"数"]), (u"all", agg_of(rec[K_DOCS])[u"数"]), (u"judge", g)])


def render_pre(c):
    u"""記録(と字で留めた文)から、文書の §3 より前の全部の行を組み直す。"""
    rec = c.rec
    Tr, Jd, Al = rec[K_SUM][G_TRAIN], rec[K_SUM][G_JUDGE], rec[K_SUM][G_ALL]
    PN, TN, AN = Jd[u"数"], Tr[u"数"], Al[u"数"]
    st = cached(c, u"st", lambda: stat_values(rec))
    j = cached(c, u"judge", lambda: judge(rec))
    hits = sum(1 for v in j.values() if v[0])
    miss = miss_ids(j)
    cells = cached(c, u"cells", lambda: expected_cells(c))
    m = rec[u"材料"]
    D = PN[u"D"]
    inner, gs, ex, fo = PN[u"決めたが違うの内訳"], PN[u"守りの止め"], PN[u"xlsx に書かなかった fact"], PN[u"決めたが違うの内訳"][u"欄ごと"]
    nsame, ndiff, nstop = PN[u"決めて全部同じ"], PN[u"決めたが違う"], PN[u"止めた"]
    g_stop = sum(v[u"止めた"] for v in gs.values())
    g_ok = sum(v[u"正しかった止め"] for v in gs.values())
    sm, sp = st[u"same"], st[u"stop"]
    flag = rec[K_FLAG]
    L = []
    w = L.append
    w(u"# 結果: 便 XE0 ― 会社が Excel で出すとしたら、XBRL の言葉を書かない欄だけで、今年の型はどれだけ決まり、どれだけ黙って違い、どれだけ止まったか ― 2026-11-23")
    w(u"")
    w(u"封 `%s`(commit %s)。script `%s` と封の門 `%s` は commit %s(独立監査 REVISE → 直し → REVISE → 直し → GO。REVISE は 2 回とも門の穴で、数え方は変えていない)。"
      u"記録 `%s` は commit %s(独立監査 GO。%d 組の全部を、Excel を通さない別の実装で数え直した)。費用は 0 USD。engine(`core/`・`adapters/`)は 0 行。XBRL は組んでいない。道具には掛けていない。人は Excel を書いていない。" % (
          SEAL_REL, SEAL_COMMIT_SHORT, SCRIPT_REL, SEAL_GATE_REL, SCRIPT_COMMIT_SHORT, RECORD_REL, RECORD_COMMIT_SHORT, Al[u"組"]))
    w(u"")
    w(u"この文書の §1・§2 の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録の数と字で同じことを見る)。§3 は記録に欄の無い読みで、出どころを書く。")
    w(u"")
    w(u"**先に負けと限界を書く。**")
    w(u"")
    miss_s = u" と ".join(miss) if len(miss) == 2 else u"・".join(miss)
    w(u"- **予測 %d 本は外れ。** 外れは %s。主の予測(XE0-1)は%s。判定した %d 本は 当たり %d・外れ %d。" % (len(miss), miss_s, u"外れ" if u"XE0-1" in miss else u"当たり", len(j), hits, len(j) - hits))
    w(u"- **黙って違う fact は 0 ではない。** 決めたが違う fact は %s。「誤りなく受ける」とは言えない。" % f(ndiff, D))
    w(u"- **%d のうち %d は、封を書く前の下調べの見落としから出た。** 負の印の付いた 0 は、Excel の整数のセルに書くと符号を失う。司令塔は封の前に頭の 3 組を数えたが、Excel を実際には通さなかった。封は直していない。外れは外れとして残す。" % (
        ndiff, fo[u"値"]))
    w(u"- **残りの %d は、去年から持ち越す決め方の負け。** 欄ごとには 名 %d・個別か既定か %d・区分 %d。同じ鍵の行が、去年と今年で別のものを指していた。止まらずに決めて違うので、この便の守りでは防げなかった。" % (
        ndiff - fo[u"値"], fo[u"名"], fo[u"個別か既定か"], fo[u"区分"]))
    w(u"- **守りは、止めなくても合っていた行を多く止めた。** 守りの止め %d のうち、止めずに決めていたら全部同じだったものは %d(%s%%)。予測(40%% 以上 65%% 以下)より多い側の外れ。" % (g_stop, g_ok, pct(g_ok, g_stop)))
    w(u"- **5 個に 1 個は止まる。** 止めた fact は %s。決めて全部同じが 95%% 以上の書類は %d 本。書類ごとの最大は %s%%・最小は %s%%。" % (f(nstop, D), pred_numbers(rec)[u"XE0-9"][0], sm[2], sm[0]))
    w(u"- **この Excel は、道具で作られ受理された書類から起こしたもの。会社の手元の原稿ではない。** 行の字・表の並び・列の番号は出来上がった書類のもので、経理の人が同じ字・同じ並びで書くかは測っていない。"
      u"**「会社が Excel で出せる」「経理の人が書ける」とは言わない。**")
    w(u"- 鍵の欄(見出し・表の番号・列の番号・表の頭の印)は「去年の書類と同じ並びの表に入れる」ことを会社に求める。会社の負担であり、この便は負担を測っていない。")
    w(u"- 単位の字は答えから表で作った字。会社が実際に書く単位の字は見ていない。期の日は答えの文脈の日をそのまま書いた。会社が期をどう書くかは見ていない。")
    w(u"- 期の日・期の種類・単位の形・表示の位・`decimals`・空かは、作る側が答えから書いた欄を受ける側が戻すだけなので、**合って当たり前**。この 6 つの欄の違いは 0 だったが、成果として読まない。"
      u"この便が測ったのは、名・個別か既定か・区分・符号の向き(去年からの持ち越し)と、止めの量。")
    w(u"- 「XBRL の知識が要る欄は 0」は Excel の欄の決めから作りでそうなる。測った数ではない。")
    w(u"- 去年の書類が在る会社の、続いた 2 年だけ。%d 組(判定は %d 組)。有報だけ。判定の %d 組も前の便で数えた書類で、未使用ではない。" % (Al[u"組"], Jd[u"組"], Jd[u"組"]))
    w(u"- 数の fact で行の中に在るものだけ。文の fact・隠しの fact・行の外の数の fact・行の字が空の fact は扱っていない。")
    w(u"- XBRL の側を組んでいない。決めた型の行から XBRL が作れるかは便 XM0 の範囲(型も対応表も答えから作った)。")
    w(u"- 答えは提出された書類そのもので、提出された書類の誤りは見ていない。")
    w(u"- 止めた行は会社へ問いとして返す行。返し方・答え方は測っていない。")
    w(u"- 予測は司令塔が立てた。盲検ではない。幅は頭の 3 組と前の便の数を見て書いた。当たった %d 本を「未見で当てた」とは言わない。" % hits)
    w(u"- **「XBRL を作れる」「専用の道具が要らない」「会社が Excel で出せる」「誤りなく受ける」は、この便からは言えない。**")
    w(u"")
    w(u"**日付つきの補足(2026-11-23。封は書き換えていない)。**")
    w(u"")
    sd, tt = flag[FLAG_KEYS[0]], flag[FLAG_KEYS[1]]
    w(u"- **封 §0 の申告の数と、訓練の 3 組の記録が %d fact 違う。** 封は 決めて全部同じ %d・決めたが違う %d と書いた。記録は %d・%d。違いの %d は、上の「負の印の付いた 0」。記録の旗「§0 と違う」は%s。" % (
        tt[u"決めて全部同じ"] - sd[u"決めて全部同じ"], tt[u"決めて全部同じ"], tt[u"決めたが違う"], sd[u"決めて全部同じ"], sd[u"決めたが違う"], sd[u"決めたが違う"] - tt[u"決めたが違う"], u"立っている" if flag[FLAG_KEYS[2]] else u"立っていない"))
    w(u"- **封 §2-2 の字と実装が合わない所。** 封は受ける側が「今年の書類も開かない」と書いた。受ける側の関数は今年の書類の中身も答えも読まないが、入口は、前の年の相手を探すために、今年の zip の提出者の番号と期末だけを開く。")
    w(u"- **XE0-3 の読み方。** 封は「符号だけ違う」に符号つきの 0 を含めて数える作りで、%d は全部それだった。封の字のとおり外れと判定する。" % inner[u"符号だけ違うのうち答えの値が符号つきの 0"])
    w(u"- **XE0-8 の当たりは境から 1 本。** 決めたが違うが 0 の書類は %d 本で、境は 35 本以上。" % pred_numbers(rec)[u"XE0-8"][0])
    w(u"- **XE0-7 の 0 は作りに寄る。** 単位の字の表(%d 行)は頭の 3 組から決めた。表に無い単位の fact は、先に「型の外」に入る。" % len(MS.UNIT_ROWS))
    w(u"- **封の門に、作りから黙る変異が %d 本在る。** 理由つきで別の試験が縛るか、判定の数に効かないもの。直していない。" % len(SG.SILENT_BY_DESIGN))
    w(u"")
    w(u"## §1 予測の当たり外れ(司令塔。盲検ではない)")
    w(u"")
    w(u"封 §4 の字の境と記録から、結果の門が XE0-1〜XE0-9 の当たり外れを決め直した(この表と同じ)。封も予測も結果を見てから書き換えていない。判定は丸める前の数でした。分母は判定の %d 組だけ。頭の %d 組の数は予測の判定には使わない。" % (Jd[u"組"], Tr[u"組"]))
    w(u"")
    w(u"| # | 予測(封の字の要約) | 実測(記録) | 判定 |")
    w(u"|---|---|---|---|")
    for k in IDS:
        w(u"| %s%s | %s | %s | %s |" % (k, u"(主)" if k == u"XE0-1" else u"", PRED_TEXT[k], cells[k][0], cells[k][1]))
    w(u"")
    w(u"- 当たり %d・外れ %d。" % (hits, len(j) - hits))
    w(u"")
    w(u"## §2 数(記録)")
    w(u"")
    w(u"材料: 今年の側の書類 %d 本のうち、前の年の相手が在る %d 組(除いた今年の書類は %d 本)。訓練の %d 組・判定の %d 組。下の数は、断らないかぎり判定の %d 組。" % (
        m[u"今年の側の書類の本数"], m[u"組の数"], m[u"除いた今年の書類の数"], Tr[u"組"], Jd[u"組"], Jd[u"組"]))
    w(u"")
    w(u"**Excel に書いた fact(分母 D)**:")
    w(u"")
    w(u"| | fact |")
    w(u"|---|---|")
    w(u"| 行の中の数の fact | %d |" % PN[u"行の中の数の fact"])
    for k in EXC:
        w(u"| 書かなかった: %s | %d |" % (k, ex[k]))
    w(u"| D(Excel に書いた行) | %d |" % D)
    w(u"")
    out_ = PN[u"突き合わせの外"]
    w(u"- 突き合わせの外の file は %d 本(各組 %d 本)で、その中の行の中の数の fact は %d。" % (out_[OUTSIDE[0]], st[u"files"][0], out_[OUTSIDE[2]]))
    w(u"- 型の外が 1 つ以上在る組は %d。1 組の最大は %d。" % st[u"outs"])
    w(u"")
    w(u"**受けた結果**:")
    w(u"")
    w(u"| 分け | fact | D に対して |")
    w(u"|---|---|---|")
    for k, v in ((u"決めて全部同じ", nsame), (u"決めたが違う", ndiff), (u"止めた", nstop)):
        w(u"| %s | %d | %s%% |" % (k, v, pct(v, D)))
    w(u"")
    w(u"**決めたが違う %d の欄ごと**(1 つの fact が 2 つ以上の欄で違うことは無かった。足すと %d):" % (ndiff, ndiff))
    w(u"")
    w(u"| 欄 | fact |")
    w(u"|---|---|")
    for k in (u"名", u"個別か既定か", u"区分", u"値"):
        w(u"| %s | %d |" % (k, fo[k]))
    w(u"| 期の日・期の種類・単位の形・表示の位・`decimals`・空か | どれも %d |" % max(fo[k] for k in (u"期の日", u"期の種類", u"単位の形", u"表示の位", u"精度", u"空か")))
    w(u"")
    w(u"- 値が違う %d は全部「符号だけ違う」で、全部、答えの値が符号つきの 0。" % fo[u"値"])
    w(u"- 去年が空で既定の「順」を使った fact のうち、決めたが違うに入ったのは %d。" % inner[u"去年が空で既定の順を使った"])
    w(u"")
    w(u"**止めた %d の理由ごと**:" % nstop)
    w(u"")
    w(u"| 理由 | 止めた | うち正しかった止め |")
    w(u"|---|---|---|")
    for r in STOPS7:
        n = PN[u"止めた理由ごと"][r]
        if r in GUARD_OF:
            ok = u"%d" % gs[GUARD_OF[r]][u"正しかった止め"]
        elif r in STOPS7[:2]:
            ok = u"(数えない)"
        else:
            ok = u"0" if n == 0 else u"(数えない)"
        w(u"| %s | %d | %s |" % (STOP_ROW.get(r, r), n, ok))
    w(u"")
    w(u"- 守りの止めは合わせて %d。うち正しかった止めは %d。" % (g_stop, g_ok))
    w(u"- 「去年に無い行」は、多い順の 5 組で %d。1 組の最大は %d。" % st[u"nokey"])
    w(u"")
    w(u"**書類ごと**(判定の %d 本):" % Jd[u"組"])
    w(u"")
    w(u"- 決めて全部同じ ÷ その書類の D は、最小 %s%%・中央 %s%%・最大 %s%%。90%% 以上の書類は %d・80%% 以上は %d・70%% 以上は %d・60%% 未満は %d。" % sm)
    w(u"- 止めた ÷ その書類の D は、最小 %s%%・中央 %s%%・最大 %s%%。" % sp)
    w(u"- 決めたが違うが 1 fact 以上在る書類は %d。1 本の最大は %d。多い順の 5 本で %d。" % st[u"diff"][:3])
    w(u"")
    sc = PN[u"場面"]
    s5 = sc[SCENE[-1]]
    w(u"**場面**(今年の側。予測は付けていない): 負の印あり %d・表示の数が 0 のもの %d・空 %d・符号の向きが逆 %d。去年の同じ鍵と表示の位が違う fact は %d で、%d つとも止めた。"
      u"去年の表の鍵のうち今年の Excel に 1 行も無いもの(無くなった行)は %d。" % (sc[SCENE[0]], sc[SCENE[1]], sc[SCENE[2]], sc[SCENE[3]], s5[u"件数"], s5[u"止めた"], PN[u"無くなった行"]))
    w(u"")
    w(u"**型の欄ごとの出どころ**(作りから決まる。数えた数ではない):")
    w(u"")
    w(u"| 型の欄 | 出どころ |")
    w(u"|---|---|")
    for k, v in rec[K_ORIGIN].items():
        w(u"| %s | %s |" % (k.replace(u"精度", u"`decimals`"), v))
    w(u"")
    w(u"**頭の 3 組(訓練。予測の判定には使わない)**: 行の中の数の fact %d・D %d・決めて全部同じ %d・決めたが違う %d・止めた %d。" % (TN[u"行の中の数の fact"], TN[u"D"], TN[u"決めて全部同じ"], TN[u"決めたが違う"], TN[u"止めた"]))
    w(u"")
    w(u"**全部の 63 組(予測の判定には使わない)**: D %d・決めて全部同じ %d・決めたが違う %d・止めた %d。" % (AN[u"D"], AN[u"決めて全部同じ"], AN[u"決めたが違う"], AN[u"止めた"]))
    w(u"")
    return L


STOP_ROW = {u"表の頭が違う": u"守り G 表の頭が違う", u"期が違う": u"守り G1 期が違う", u"番号つき": u"守り G3 番号つき", u"単位が違う": u"守り G2 単位が違う"}


def render_post(c):
    u"""文書の §4 以降(封の門の本数・記録の監査・§5)を、記録と封の門の本数から組み直す。"""
    rec = c.rec
    PN = rec[K_SUM][G_JUDGE][u"数"]
    TN, AN = rec[K_SUM][G_TRAIN][u"数"], rec[K_SUM][G_ALL][u"数"]
    D = PN[u"D"]
    L = []
    w = L.append
    w(u"## §4 門と監査")
    w(u"")
    w(u"- 封の門: 試験 %d 本。変異 %d 本が赤。作りから黙る変異 %d 本は理由つき。" % (seal_tests(), len(SG.MUTANTS), len(SG.SILENT_BY_DESIGN)))
    w(u"- 独立監査の 1 回目は REVISE(門が、記録の検査の配線と、本番だけが通る入口の配線を縛っていなかった)。2 回目は REVISE(旗の表示の向きを入れ替える変異が黙った)。直して GO。")
    w(u"- 記録の監査: %d 組の全部を、Excel を通さない別の実装で数え直した。差は「負の印の付いた 0 が符号を失う」%d fact(訓練 %d・判定 %d)だけで、ほかの項目は全部同じ。司令塔の途中の file からの数え直しも同じ数になった。" % (
        rec[K_SUM][G_ALL][u"組"], AN[u"決めたが違うの内訳"][u"符号だけ違う"], TN[u"決めたが違うの内訳"][u"符号だけ違う"], PN[u"決めたが違うの内訳"][u"符号だけ違う"]))
    w(u"- 実装の途中の事故: 実装の席が門の出力の file を木の根に 4 本残した。commit の前に木の外へ移した。commit した木には残っていない。")
    w(u"")
    w(u"## §5 読みと次(封 §6 の決めどおり)")
    w(u"")
    w(u"- 記録から言えること: **受理済みの書類から起こした Excel で、去年の書類が在る会社について**、Excel に書いた数の fact の %s%% が黙らず決まり、%s%% が黙って違い、%s%% が止まった。" % (
        pct(PN[u"決めて全部同じ"], D), pct(PN[u"決めたが違う"], D), pct(PN[u"止めた"], D)))
    w(u"- 記録から言えないこと: 会社がこの Excel を書けるか。止めた行に会社が答えられるか。去年の書類が無い会社でどうなるか。黙って違う %s%% を何で見つけるか。" % pct(PN[u"決めたが違う"], D))
    w(CAND_LINE)
    w(DECIDE_LINE)
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
    u"""記録から導ける数(文書の §3 以外の数はこの内か字で留めた境の数)。render_doc とは別に、記録の整数・組ごとから作る。"""
    rec = c.rec
    out = set()
    for k in GROUPS:
        ints_in(rec[K_SUM][k], out)
    ints_in(rec[PRED_KEY], out)
    ints_in(rec[K_FLAG], out)
    st = stat_values(rec)
    for key in (u"same", u"stop", u"diff", u"outs", u"nokey"):
        for x in st[key]:
            out.add(str(x))
    g = st[u"judge"]
    gs = g[u"守りの止め"]
    out |= set([str(sum(v[u"止めた"] for v in gs.values())), str(sum(v[u"正しかった止め"] for v in gs.values())), str(g[u"決めたが違う"] - g[u"決めたが違うの内訳"][u"欄ごと"][u"値"])])
    out |= set(pct(a, b) for a, b in pred_numbers(rec).values() if b)
    out |= set([pct(sum(v[u"正しかった止め"] for v in gs.values()), sum(v[u"止めた"] for v in gs.values()))])
    out |= set([str(rec[u"材料"][u"今年の側の書類の本数"]), str(rec[u"材料"][u"除いた今年の書類の数"])])
    out |= set(str(v) for v in (seal_tests(), len(SG.MUTANTS), len(SG.SILENT_BY_DESIGN), len(MS.UNIT_ROWS)))
    out |= set(DOC_COMMITS)
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
    allowed = RESIDUAL_OK | set(STRUCTURAL) | set(DOC_COMMITS)
    for ln in rest:
        for tok in doc_number_tokens(ln):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"組み直した行に無い行の数 %s が留めた境の数の外: %s" % (tok, ln[:24]))
    return out


def sanity_problems(c):
    u"""文書の静的な言い切り(組み直した行の数以外の字)が記録の数に合う。"""
    rec = c.rec
    st = stat_values(rec)
    g, ta = st[u"judge"], st[u"train"]
    out = []
    fo, inner, gs = g[u"決めたが違うの内訳"][u"欄ごと"], g[u"決めたが違うの内訳"], g[u"守りの止め"]
    if any(x != 1 for x in st[u"files"]):
        out.append(u"文書の「突き合わせの外の file は 60 本(各組 1 本)」が記録と合わない")
    if not (g[u"突き合わせの外"][OUTSIDE[2]] == 0):
        out.append(u"文書の「その中の行の中の数の fact は 0」が記録と合わない")
    if not (fo[u"値"] == inner[u"符号だけ違う"] == inner[u"符号だけ違うのうち答えの値が符号つきの 0"] > 0):
        out.append(u"文書の「値が違う 127 は全部「符号だけ違う」で、全部、答えの値が符号つきの 0」が記録と合わない")
    if any(fo[k] != 0 for k in (u"期の日", u"期の種類", u"単位の形", u"表示の位", u"精度", u"空か")):
        out.append(u"文書の「合って当たり前」の 6 つの欄の違いが 0 でない")
    if not (sum(fo.values()) == g[u"決めたが違う"]):
        out.append(u"文書の「1 つの fact が 2 つ以上の欄で違うことは無かった。足すと 245」が記録と合わない")
    s5 = g[u"場面"][SCENE[-1]]
    if not (s5[u"件数"] == s5[u"止めた"] and s5[u"決めて全部同じ"] == 0 and s5[u"決めたが違う"] == 0):
        out.append(u"文書の「去年の同じ鍵と表示の位が違う fact は 2 で、2 つとも止めた」が記録と合わない")
    if not (g[u"止めた理由ごと"][STOPS7[0]] > 0 and 6 * g[u"止めた"] >= g[u"D"] and 4 * g[u"止めた"] <= g[u"D"] * 1):
        if not (6 * g[u"止めた"] >= g[u"D"] and 4 * g[u"止めた"] <= g[u"D"]):
            out.append(u"文書の「5 個に 1 個は止まる」が記録と合わない(止めた ÷ D が 1/6 以上 1/4 以下でない)")
    j = judge(rec)
    if j[u"XE0-5"][1] != u"上":
        out.append(u"文書の「予測(40% 以上 65% 以下)より多い側の外れ」が記録と合わない")
    if not (all(100 * d[u"決めて全部同じ"] < 95 * d[u"D"] for d in split_docs(rec)[1])):
        out.append(u"文書の「決めて全部同じが 95% 以上の書類は 0 本」が記録と合わない")
    if not (j[u"XE0-8"][0] and pred_numbers(rec)[u"XE0-8"][0] - 35 == 1):
        out.append(u"文書の「XE0-8 の当たりは境から 1 本」が記録と合わない")
    if not (ta[u"決めたが違う"] == ta[u"決めたが違うの内訳"][u"符号だけ違う"] == ta[u"決めたが違うの内訳"][u"符号だけ違うのうち答えの値が符号つきの 0"]):
        out.append(u"文書の「違いの 3 は、上の「負の印の付いた 0」」が記録と合わない(訓練の 3 組の違いが符号つきの 0 だけでない)")
    fl = rec[K_FLAG]
    if not (fl[FLAG_KEYS[1]][u"決めて全部同じ"] - fl[FLAG_KEYS[0]][u"決めて全部同じ"] == fl[FLAG_KEYS[0]][u"決めたが違う"] - fl[FLAG_KEYS[1]][u"決めたが違う"] == ta[u"決めたが違う"]
            and fl[FLAG_KEYS[0]][u"止めた"] == fl[FLAG_KEYS[1]][u"止めた"] and fl[FLAG_KEYS[2]] is True):
        out.append(u"文書の補足(封 §0 と記録が 3 fact 違う・旗が立っている)が記録と合わない")
    if tuple(fl[FLAG_KEYS[1]].values()) != tuple(SEAL_TRAIN_PIN.values()) or tuple(MS.SEAL_TRAIN.values()) != tuple(SEAL_TRAIN_PIN.values()):
        out.append(u"封 §0 の数が script・字で留めた値と違う")
    if not (MS.SEEN_MAX_NO == 3 and u"番号 1・2・3 が訓練、番号 4〜63 が判定の 60 組" in c.seal):
        out.append(u"訓練の 3 組・判定の 60 組の分けが封・script と合わない")
    if len(MS.UNIT_ROWS) != 8 or len(SG.MUTANTS) != 479 or len(SG.SILENT_BY_DESIGN) != 7:
        out.append(u"文書の 8 行・479 本・7 本が封の門・script の長さと合わない")
    return out


def sec3_problems(c):
    u"""§3 は記録に欄の無い読み(監査の席の読み)の節。数は記録に縛らず、見出し・「測った数ではない」・字で留めた数の並び・記録から導ける数・
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
    st = stat_values(c.rec)
    g = st[u"judge"]
    fo, gs, ex = g[u"決めたが違うの内訳"][u"欄ごと"], g[u"守りの止め"], g[u"xlsx に書かなかった fact"]
    try:
        n = [[int(x) for x in toks[k]] for k, _ in SEC3_LINES]
        if n[0][1] != g[u"決めたが違う"] - fo[u"値"]:
            out.append(u"§3 の 118 が 決めたが違う − 値が違う(記録)と合わない")
        if n[1][0] != fo[u"個別か既定か"] or n[1][0] != st[u"nonsign"][4]:
            out.append(u"§3 の「個別か既定かが替わった 60」が記録(欄ごと・組ごとの最大)と合わない")
        if n[2][0] + n[3][0] + n[4][0] != fo[u"名"]:
            out.append(u"§3 の 32 + 20 + 2 が 名(記録)と合わない")
        if n[5][0] != fo[u"区分"]:
            out.append(u"§3 の「member が替わった 4」が 区分(記録)と合わない")
        if n[1][0] + n[2][0] + n[3][0] + n[4][0] + n[5][0] != n[0][1]:
            out.append(u"§3 の 118 の内訳の和が 118 と合わない")
        if n[6][0] != n[0][1] or n[6][1] != c.rec[K_SUM][G_JUDGE][u"組"] or n[6][2] != st[u"nonsign"][1] or 2 * st[u"nonsign"][3] < n[6][0]:
            out.append(u"§3 の「118 は判定の 60 本のうち 17 本に在り、半分は 1 本の書類」が記録の組ごとの数と合わない")
        if n[7][2] != st[u"nonsign"][2] or n[7][3] != pred_numbers(c.rec)[u"XE0-8"][0] or n[7][0] != 0 or n[7][1] != 0:
            out.append(u"§3 の 43・36 が記録の組ごとの数・XE0-8 と合わない")
        if n[8][0] != ex[EXC[1]] or n[8][1] + n[8][2] + n[8][3] != n[8][0] or n[8][5] != st[u"outs"][1]:
            out.append(u"§3 の型の外 537(516 + 20 + 1)・502 が記録と合わない")
        if (n[10][0], n[10][2]) != (ex[EXC[2]], ex[EXC[3]]) or n[10][1] != MS.MAX_DIGITS or n[10][3] != len(MS.UNIT_ROWS):
            out.append(u"§3 の「単位が書けない 0・15 桁を超える 0・表の 8 行」が記録・script と合わない")
        if (n[11][0], n[11][2]) != (gs[u"守り G2 単位"][u"止めた"], gs[u"守り G2 単位"][u"止めた"]):
            out.append(u"§3 の守り G2 の 0 が記録と合わない")
        if n[12][1] != g[u"止めた理由ごと"][STOPS7[6]]:
            out.append(u"§3 の符号の向きが 2 通り 0 が記録と合わない")
        if n[13][1] != gs[u"守り G1 期"][u"止めた"]:
            out.append(u"§3 の 229 が記録(守り G1 の止め)と合わない")
        if n[15][0] != c.rec[K_SUM][G_ALL][u"組"] or n[15][5] != len(MS.UNIT_ROWS):
            out.append(u"§3 の「63 本」「単位の字は 8 種」が記録・script と合わない")
    except (KeyError, ValueError, IndexError, TypeError):
        out.append(u"§3 の数が読めない")
    rest = outside_sec3(c)
    for p in SEC3_ONLY_PHRASES:
        if p in rest:
            out.append(u"記録に欄の無い §3 の主張「%s」が §3 の外に出ている" % p)
    derived = derived_numbers(c)
    only3 = [u"32", u"516", u"1028"]      # この 3 つは記録のどこにも無い(20・9 は別の意味で §2 にも在る数と重なるので、字の主張で見張る)
    rest_toks = [x for ln in rest.splitlines() for x in doc_number_tokens(ln)]
    for t in only3:
        if t in derived:
            out.append(u"§3 だけの数 %s が記録から導ける数と重なっている(門の留めが古い)" % t)
        if t in rest_toks:
            out.append(u"§3 だけの数 %s が §3 の外に出ている" % t)
    return out


def sec4_problems(c):
    u"""§4 の 35・479・7 は封の門の本数に縛る(render が組み直す)。130・3・127 は記録に縛る(render が組み直す)。"""
    out = []
    if (len(SG.MUTANTS), len(SG.SILENT_BY_DESIGN), seal_tests()) != (479, 7, 35):
        out.append(u"封の門の本数(変異 479・同値 7・試験 35)が文書の §4 の数と違う")
    if u"- 封の門: 試験 35 本。変異 479 本が赤。作りから黙る変異 7 本は理由つき。" not in sec4_text(c).splitlines():
        out.append(u"§4 の封の門の行が違う")
    st = stat_values(c.rec)
    if (st[u"all"][u"決めたが違うの内訳"][u"符号だけ違う"], st[u"train"][u"決めたが違うの内訳"][u"符号だけ違う"], st[u"judge"][u"決めたが違うの内訳"][u"符号だけ違う"]) != (130, 3, 127):
        out.append(u"§4 の 130(訓練 3・判定 127)が記録と合わない")
    if u"130 fact(訓練 3・判定 127)" not in sec4_text(c):
        out.append(u"§4 に「130 fact(訓練 3・判定 127)」が無い")
    return out


def affirm_problems(c):
    u"""「作れる」「専用の道具が要らない」「人が書ける」「Excel で出せる」「誤りなく受ける」「誤りが無くなる」「検査に通る」は、言えないことの引用(「…」の中)・否定の中にしか無い。引用の在る行には「言えない」「言わない」などが在る。"""
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
    if len(lim7) != 8:
        out.append(u"封 §7 の限界の行が 8 本でない")
        return out
    hlines = head.splitlines()
    for i, (lim, frags) in enumerate(zip(lim7, LIMIT_FRAGS), 1):
        for x in frags:
            if x not in lim:
                out.append(u"封 §7 の %d 本目の限界に門の断片が無い: %s" % (i, x[:12]))
        if not any(all(x in ln for x in frags) for ln in hlines):
            out.append(u"封 §7 の %d 本目の限界が文書の頭の 1 つの行に揃って無い: %s" % (i, lim[:16]))
    # 封 §6 の読み方(会社が出せる・誤りなく受ける・合って当たり前・XBRL の知識・返し方)
    for p in (u"「会社が Excel で出せる」「経理の人が書ける」とは言わない", u"「誤りなく受ける」とは言えない", u"合って当たり前", u"「XBRL の知識が要る欄は 0」は Excel の欄の決めから作りでそうなる。測った数ではない",
              u"返し方・答え方は測っていない", u"成果として読まない"):
        if p not in head:
            out.append(u"封 §6 の読み方の字が文書の頭に無い: %s" % p[:16])
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
    for w in DOC_COMMITS:
        if w not in c.doc:
            out.append(u"文書に commit の字が無い: %s" % w)
    if not set(re.findall(r"(?<![0-9A-Za-z])[0-9a-f]{8}(?![0-9A-Za-z])", c.doc)) <= set(DOC_COMMITS):
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


def commit_problems(root=REPO):
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は aec0496d・script と封の門は 7cc388be・記録は e59be6e6。commit の message が文書の言う「REVISE」「独立監査 GO」「差」を書いている。"""
    out = []
    for rel, want in HISTORY.items():
        r = subprocess.run(["git", "-C", root, "log", "--format=%H", "--reverse", "--", PREFIX + rel], stdout=subprocess.PIPE, universal_newlines=True)
        got = [x for x in r.stdout.split() if x]
        if len(got) != len(want) or any(not g.startswith(w) for g, w in zip(got, want)):
            out.append(u"%s の履歴が文書の書く commit %s と違う" % (rel, u"・".join(want)))
    for short, words in ((SCRIPT_COMMIT_SHORT, (u"独立監査 REVISE(門の穴: check の配線・本番だけの配線)→ 直し → REVISE(旗の表示の向き)→ 直し → GO", u"同値 7 本", u"変異 479 本が赤", u"封は直さず結果の文書に書く")),
                         (RECORD_COMMIT_SHORT, (u"独立監査 GO", u"63 組の全部を Excel を通さない別の実装で数え直し", u"負の印の付いた 0 が Excel の整数のセルで符号を失う 130 個だけ"))):
        r = subprocess.run(["git", "-C", root, "log", "-1", "--format=%B", short], stdout=subprocess.PIPE, universal_newlines=True)
        for w in words:
            if w not in r.stdout:
                out.append(u"commit %s の message に「%s」が無い" % (short, w))
    return out


def git_problems(root=REPO):
    out = []
    out.extend(SG.seal_history_problems(root))
    out.extend(SG.engine_zero_problems(root))
    out.extend(blob_problems(root, PREFIX, BLOB_AT))
    out.extend(commit_problems(root))
    return out


def order_problems_real(root=REPO):
    u"""封 ⊏ script と封の門 ⊏ 記録 ⊏ 結果の文書と門。未 commit は赤。"""
    out = list(PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL, SEAL_GATE_REL], [RECORD_REL, DOC_REL, GATE_REL]))
    for rel in (SCRIPT_REL, SEAL_GATE_REL):
        added = PR.added_commits(root, PREFIX + rel)
        if len(added) != 1 or not added[0].startswith(SCRIPT_COMMIT_SHORT):
            out.append(u"%s を足した commit が %s でない" % (rel, SCRIPT_COMMIT_SHORT))
        rc, last = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + rel)
        if not last.startswith(SCRIPT_COMMIT_SHORT):
            out.append(u"%s の最後の commit が %s でない(記録を書いた後に変わった)" % (rel, SCRIPT_COMMIT_SHORT))
    rec = PR.added_commits(root, PREFIX + RECORD_REL)
    if len(rec) != 1 or not rec[0].startswith(RECORD_COMMIT_SHORT):
        out.append(u"記録を足した commit が %s でない" % RECORD_COMMIT_SHORT)
    else:
        rc, lastrec = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + RECORD_REL)
        if not lastrec.startswith(RECORD_COMMIT_SHORT):
            out.append(u"記録の最後の commit が %s でない" % RECORD_COMMIT_SHORT)
        for rel in (SCRIPT_REL, SEAL_GATE_REL):
            added = PR.added_commits(root, PREFIX + rel)
            if added and not PR.is_anc(root, added[0], rec[0]):
                out.append(u"記録が %s より前" % rel)
    return out


# ======================================================================================================
PREDICT = u"""
(変異を実行する前に書いた予測。右 = 赤になるべき検査。「整合」= 組ごとの数から集計・予測・旗を作り直し、recount は緑のまま当たり外れ・向きだけが変わる)
固定の変異 F1〜: 記録・封・文書の 1 か所を替える。右の検査が赤。
F1  記録の sha256 の写しを違う値に                                                       -> sha
F2  記録の「この script の sha256」を 1 字替える                                         -> sha
F3  記録の限界の欄の 1 行を消す                                                          -> sha
F4  記録の封の commit の欄を 1 字替える                                                  -> sha
F5  記録の step の欄を 1 字替える                                                        -> sha
F6  封の写しの sha256 の写しを違う値に                                                    -> sha
F7  記録の材料の組の数 63 → 62                                                          -> recount
F8  記録の材料の file 名の並びの sha256 を 1 字替える                                       -> recount
F9  組 20 の「決めて全部同じ」を 1 増やす(集計は直さない)                                    -> recount
F10 集計の判定の 60 組の「決めたが違う」を 1 増やす(組ごとは直さない)                          -> recount
F11 組 6 の止めた理由(去年に無い行)を 1 増やす(止めたは直さない)                            -> recount
F12 組 5 の欄ごと(名)を 1 増やす(決めたが違うは直さない)                                    -> recount
F13 予測の欄 XE0-3 の fact を 1 増やす                                                    -> recount
F14 組の番号 5 を 99 にする                                                               -> recount
F15 集計の全部の D を 1 増やす                                                            -> recount
F16 集計の訓練の 3 組と判定の 60 組を入れ替える                                              -> recount
F17 旗の欄の「§0 と違う」を反転する                                                         -> recount
F18 型の欄ごとの出どころの 1 字を替える                                                    -> recount
F19 記録に docid の欄を足す                                                               -> clean
F20 記録に EDINET コードの形の字を足す                                                     -> clean
F21 記録に日付の形の字を足す                                                               -> clean
F22 封の写しから XE0-3 の境の字を消す                                                      -> bound
F23 封の写しから §6 の (iii) の候補の字を消す                                              -> bound
F24 封の写しから §7 の限界の 1 本を消す                                                    -> bound
F25 封の写しから §0 の頭の 3 組の数を消す                                                  -> bound
F26 封の写しの §6 に (v) の候補を足す                                                      -> bound
整合の変異 C1〜: recount は緑のまま、文書が合わなくなる(verdict・lines)。
C1  XE0-1 を外れにする(全部同じの 25% を止めに)                                              -> verdict
C2  XE0-2 を外れにする(上: 決めたが違うを D の 2% に)                                         -> verdict
C3  XE0-2 を外れにする(下: 決めたが違うを 0 に)                                               -> verdict
C4  XE0-3 を当たりにする(値が違うを全部同じに)                                               -> verdict
C5  XE0-4 を外れにする(下: 止めたを D の 1% に)                                               -> verdict
C6  XE0-4 を外れにする(上: 全部同じの 20% を止めに)                                            -> verdict
C7  XE0-5 を当たりにする(正しかった止めを半分に)                                              -> verdict
C8  XE0-5 を外れにする(下: 正しかった止めを 0 に)                                              -> verdict
C9  XE0-6 を外れにする(下: 守り G1 の止めを 0 に)                                              -> verdict
C10 XE0-6 を外れにする(上: 守り G1 の止めを D の 3% に)                                        -> verdict
C11 XE0-7 を外れにする(単位が書けないを 2% に)                                                -> verdict
C12 XE0-8 を外れにする(決めたが違うが 0 の書類 3 本に 1 fact ずつ違いを足す)                      -> verdict
C13 XE0-9 を外れにする(3 本を 100% に)                                                        -> verdict
C14 旗 §0 と違う: 訓練の 3 組の違いを全部同じにして封 §0 の数に揃える                              -> verdict・lines・sanity
文書の固定の変異 D1〜: 右の検査が赤。
D1  頭の「予測 2 本は外れ」を「3 本」に                                                       -> verdict・lines
D2  頭の「当たり 7・外れ 2」を「当たり 8・外れ 1」に                                           -> verdict・lines
D3  「黙って違う fact は 0 ではない」を「0」に                                               -> lines・phrases
D4  「Excel を実際には通さなかった」を「通した」に                                            -> lines・phrases
D5  「封は直していない」を「直した」に                                                        -> lines・phrases
D6  「「誤りなく受ける」とは言えない」を「誤りなく受ける」に(肯定)                              -> affirm・verdict・lines
D7  「守りの止め 4080」を 4081 に                                                             -> lines
D8  「5 個に 1 個は止まる」を「5 個に 2 個」に                                                  -> lines・phrases
D9  「去年から持ち越す決め方の負け」を「勝ち」に                                                -> lines・phrases
D10 「合って当たり前」を「合わなくて当たり前」に                                               -> lines・phrases
D11 §5 に (v) の候補を足す                                                                    -> sec5
D12 §5 に候補の見出しの無い案の 1 行を足す                                                      -> sec5
D13 §5 の「(iii) と範囲の拡大は人間が決める」を「司令塔が決める」に                                -> sec5
D14 §5 の「(i)(ii)(iv)」を「(i)(ii)(iii)(iv)」に                                              -> sec5
D15 §5 の候補の行から (iii) を落とす                                                          -> sec5
D16 §5 の候補の行の (iv) の後ろに封に無い候補の字を足す                                         -> sec5
D17 頭の限界の 1 本(型の外の…)を消す                                                          -> head
D18 「記録から言えないこと」を消す                                                             -> phrases・lines
D19 文書に「4999999%」の言い切りを足す                                                         -> numbers・resid
D20 引用の行から「言えない」「言わない」を全部消す                                              -> affirm
D21 文書に「保証」を足す・docID の形を足す                                                     -> forbidden
D22 文書の commit の字 7cc388be を 1 字替える・e59be6e6 を 1 字替える・知らない commit の字を足す  -> commits
D23 §3 の見出しの「記録に欄の無い読み」を消す・「測った数ではない」を消す・§3 の 32 → 33・「17 本」→「18 本」・43 → 44・516 → 517・1028 → 1029・502 → 503・229 → 230・36 → 37     -> sec3
D24 §3 の外に「別の区分の科目に替わった」を足す                                                -> sec3
D25 補足を 1 本消す(封 §0・封 §2-2・XE0-3・XE0-8・XE0-7・封の門の 6 本の全部)                     -> lines・head
D26 §4 の 35・479・7・130・127 を替える                                                        -> sec4・lines
D27 §2 の表のセル 1 つ(予測の行の入れ替え・欄ごとの 値 と 名の取り違え)を替える                    -> lines・verdict
掃き(SWEEPS。文書の全部に 1 か所ずつ当てる。1 つでも黙れば報告):
W1  文書の全部の数(§3 を含む)を、(a) 1 増やす (b) 同じ文書の別の所の数に替える (c) §3 の数に替える          -> 全部赤(lines か sec3)
W2  向きの語(以上/以下/未満・多い/少ない・全部/一部・当たり/外れ・在る/無い・今年/前の年・止めた/決めて全部同じ など)を、出た所ごとに反対に -> 全部赤
W3  「60 組」「63 組」「3 組」の数を互いに取り違える・58476/61100/61781/4080 を互いに取り違える              -> 全部赤
W4  §3 の数・主張を §2 に 1 行として足す(全部)                                              -> 全部赤(lines・numbers・sec3)
W5  表の 1 セルを、同じ表の別の行の同じ列のセルへ替える(§1 の表・§2 の表の全部のセル。当たり外れの行の入れ替えを含む。決めて全部同じ/決めたが違う/止めたの取り違え・止めた/正しかった止めの取り違えを含む)    -> 全部赤
W6  §3 の外の全部の行を 1 行ずつ消す・全部の文を 1 つずつ消す・「・」でつないだ節を 1 つずつ消す        -> 全部赤
W7  記録の全部の整数・小数・旗の葉(集計 3 つ・予測・旗・組の代表 8 つ分)を 1 増やす・旗を反転する          -> 全部赤(recount)
W8  §3 の文を 1 つずつ消す・向きの語を反対に                                                   -> 黙る所が在りうる(§3 の中の括弧の例示と、SEC3_PHRASES に無い言い回し)。黙った所は報告
実行後の追記(予測は書き換えない): C14 の「verdict」は予測が外れた。verdict は旗を見ないので黙るのが正しい(旗は頭の補足の字だけに出る)。C14 の右は lines・sanity に直した。
C8 は XE0-5 がもともと外れ(上)なので当たり外れは変わらず、外れの向き(下)と実測の字が変わる変異。当たり外れの反転の表からは外した。
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
    train, judge_docs = split_docs(rec)
    rec[K_SUM][G_TRAIN] = agg_of(train)
    rec[K_SUM][G_JUDGE] = agg_of(judge_docs)
    rec[K_SUM][G_ALL] = agg_of(rec[K_DOCS])
    rec[PRED_KEY] = pred_expected(rec)
    rec[K_FLAG] = flags_expected(rec)
    c.cache = {}


def each_judge(c, fn):
    for d in c.rec[K_DOCS]:
        if d[u"番号"] > TRAIN_COUNT:
            fn(d)
    rebuild(c)


def first_judge(c, n, pred, fn):
    u"""判定の 60 組のうち pred を満たす最初の n 組に fn を当てる。"""
    k = 0
    for d in c.rec[K_DOCS]:
        if d[u"番号"] > TRAIN_COUNT and pred(d) and k < n:
            fn(d)
            k += 1
    assert k == n, (k, n)
    rebuild(c)


def stop_remove(d, r, n):
    d[u"止めた理由ごと"][r] -= n
    if r in GUARD_OF:
        g = d[u"守りの止め"][GUARD_OF[r]]
        g[u"止めた"] -= n
        g[u"正しかった止め"] = min(g[u"正しかった止め"], g[u"止めた"])
    d[u"止めた"] -= n
    assert d[u"止めた理由ごと"][r] >= 0


def stop_reduce(d, n):
    left = n
    for r in STOPS7:
        take = min(left, d[u"止めた理由ごと"][r])
        if take:
            stop_remove(d, r, take)
        left -= take
        if not left:
            break
    assert left == 0


def stop_add(d, n, r=STOPS7[0]):
    d[u"止めた理由ごと"][r] += n
    d[u"止めた"] += n
    if r in GUARD_OF:
        d[u"守りの止め"][GUARD_OF[r]][u"止めた"] += n


def diff_remove(d, n, fields=(u"名", u"個別か既定か", u"区分", u"値")):
    fo, inner = d[u"決めたが違うの内訳"][u"欄ごと"], d[u"決めたが違うの内訳"]
    left = n
    for k in fields:
        take = min(left, fo[k])
        fo[k] -= take
        left -= take
        if k == u"値":
            inner[u"符号だけ違う"] = min(inner[u"符号だけ違う"], fo[u"値"])
            inner[u"符号だけ違うのうち答えの値が符号つきの 0"] = min(inner[u"符号だけ違うのうち答えの値が符号つきの 0"], inner[u"符号だけ違う"])
        if not left:
            break
    assert left == 0
    d[u"決めたが違う"] -= n
    inner[u"去年が空で既定の順を使った"] = min(inner[u"去年が空で既定の順を使った"], d[u"決めたが違う"])


def diff_add(d, n, field=u"名"):
    d[u"決めたが違うの内訳"][u"欄ごと"][field] += n
    d[u"決めたが違う"] += n


def same_to_stop(d, n, r=STOPS7[0]):
    d[u"決めて全部同じ"] -= n
    stop_add(d, n, r)


def same_to_diff(d, n):
    d[u"決めて全部同じ"] -= n
    diff_add(d, n)


def all_same(d):
    n1 = d[u"決めたが違う"]
    diff_remove(d, n1)
    n2 = d[u"止めた"]
    stop_reduce(d, n2)
    d[u"決めて全部同じ"] += n1 + n2


def m_x1_miss(c):
    each_judge(c, lambda d: same_to_stop(d, d[u"決めて全部同じ"] * 25 // 100))


def m_x2_high(c):
    each_judge(c, lambda d: same_to_diff(d, d[u"D"] // 50 + 1))


def m_x2_zero(c):
    each_judge(c, lambda d: (lambda n: (diff_remove(d, n), d.__setitem__(u"決めて全部同じ", d[u"決めて全部同じ"] + n)))(d[u"決めたが違う"]))


def m_x3_hit(c):
    def fn(d):
        n = d[u"決めたが違うの内訳"][u"欄ごと"][u"値"]
        diff_remove(d, n, (u"値",))
        d[u"決めて全部同じ"] += n
    each_judge(c, fn)


def m_x4_low(c):
    def fn(d):
        n = d[u"止めた"] - d[u"D"] // 100
        stop_reduce(d, n)
        d[u"決めて全部同じ"] += n
    each_judge(c, fn)


def m_x4_high(c):
    each_judge(c, lambda d: same_to_stop(d, d[u"決めて全部同じ"] * 20 // 100))


def m_x5_hit(c):
    def fn(d):
        for g in d[u"守りの止め"].values():
            g[u"正しかった止め"] = g[u"止めた"] // 2
    each_judge(c, fn)


def m_x5_low(c):
    def fn(d):
        for g in d[u"守りの止め"].values():
            g[u"正しかった止め"] = 0
    each_judge(c, fn)


def m_x6_zero(c):
    def fn(d):
        n = d[u"止めた理由ごと"][u"期が違う"]
        stop_remove(d, u"期が違う", n)
        d[u"決めて全部同じ"] += n
    each_judge(c, fn)


def m_x6_high(c):
    each_judge(c, lambda d: same_to_stop(d, d[u"D"] * 3 // 100 + 1, u"期が違う"))


def m_x7_miss(c):
    def fn(d):
        n = d[u"行の中の数の fact"] // 50 + 1
        d[u"xlsx に書かなかった fact"][EXC[2]] += n
        d[u"D"] -= n
        d[u"決めて全部同じ"] -= n
    each_judge(c, fn)


def m_x8_miss(c):
    first_judge(c, 3, lambda d: d[u"決めたが違う"] == 0, lambda d: same_to_diff(d, 1))


def m_x9_miss(c):
    first_judge(c, 3, lambda d: True, all_same)


def m_flag_off(c):
    def fn(d):
        n = d[u"決めたが違う"]
        diff_remove(d, n)
        d[u"決めて全部同じ"] += n
    for d in c.rec[K_DOCS]:
        if d[u"番号"] <= TRAIN_COUNT:
            fn(d)
    rebuild(c)


def inc(c, path, delta=1):
    o = c.rec
    for p in path[:-1]:
        o = o[p]
    o[path[-1]] += delta


def m_swap_groups(c):
    c.rec[K_SUM][G_TRAIN], c.rec[K_SUM][G_JUDGE] = c.rec[K_SUM][G_JUDGE], c.rec[K_SUM][G_TRAIN]


def m_flip_flag(c):
    c.rec[K_FLAG][FLAG_KEYS[2]] = not c.rec[K_FLAG][FLAG_KEYS[2]]


MUTATIONS = (
    (u"F1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"F2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"F3 記録の限界の欄の 1 行を消す", lambda c: c.rec.__setitem__(u"限界", c.rec[u"限界"][1:]), (u"sha",)),
    (u"F4 記録の封の commit の欄を 1 字替える", lambda c: c.rec.__setitem__(u"封の commit", u"0" + c.rec[u"封の commit"][1:]), (u"sha",)),
    (u"F5 記録の step の欄を 1 字替える", lambda c: c.rec.__setitem__(u"step", c.rec[u"step"].replace(u"XE0", u"XE1", 1)), (u"sha",)),
    (u"F6 封の写しの sha256 の写しを違う値に", lambda c: c.shas.__setitem__(SEAL_REL, u"0" * 64), (u"sha",)),
    (u"F7 記録の材料の組の数を 62 に", lambda c: c.rec[u"材料"].__setitem__(u"組の数", 62), (u"recount",)),
    (u"F8 記録の材料の file 名の並びの sha256 を 1 字替える", lambda c: c.rec[u"材料"].__setitem__(u"今年の側の書類の file 名の並びの sha256", u"0" + c.rec[u"材料"][u"今年の側の書類の file 名の並びの sha256"][1:]), (u"recount",)),
    (u"F9 組 20 の決めて全部同じを 1 増やす(集計は直さない)", lambda c: doc_at(c.rec, 20).__setitem__(u"決めて全部同じ", doc_at(c.rec, 20)[u"決めて全部同じ"] + 1), (u"recount",)),
    (u"F10 集計の判定の 60 組の決めたが違うを 1 増やす", lambda c: inc(c, (K_SUM, G_JUDGE, u"数", u"決めたが違う")), (u"recount",)),
    (u"F11 組 6 の止めた理由(去年に無い行)を 1 増やす", lambda c: doc_at(c.rec, 6)[u"止めた理由ごと"].__setitem__(STOPS7[0], doc_at(c.rec, 6)[u"止めた理由ごと"][STOPS7[0]] + 1), (u"recount",)),
    (u"F12 組 5 の欄ごと(名)を 1 増やす", lambda c: doc_at(c.rec, 5)[u"決めたが違うの内訳"][u"欄ごと"].__setitem__(u"名", doc_at(c.rec, 5)[u"決めたが違うの内訳"][u"欄ごと"][u"名"] + 1), (u"recount",)),
    (u"F13 予測の欄 XE0-3 の fact を 1 増やす", lambda c: inc(c, (PRED_KEY, PK[2], u"fact")), (u"recount",)),
    (u"F14 組の番号 5 を 99 にする", lambda c: doc_at(c.rec, 5).__setitem__(u"番号", 99), (u"recount",)),
    (u"F15 集計の全部の D を 1 増やす", lambda c: inc(c, (K_SUM, G_ALL, u"数", u"D")), (u"recount",)),
    (u"F16 集計の訓練の 3 組と判定の 60 組を入れ替える", m_swap_groups, (u"recount",)),
    (u"F17 旗の欄の「§0 と違う」を反転する", m_flip_flag, (u"recount",)),
    (u"F18 型の欄ごとの出どころの 1 字を替える", lambda c: c.rec[K_ORIGIN].__setitem__(u"期の日", u"会社が書いた欄から、そのまま"), (u"recount",)),
    (u"F19 記録に docid の欄を足す", lambda c: c.rec.__setitem__(u"docID", u"S100ABCD"), (u"clean",)),
    (u"F20 記録に EDINET コードの形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"E01234"), (u"clean",)),
    (u"F21 記録に日付の形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"2025-03-31"), (u"clean",)),
    (u"F22 封の写しから XE0-3 の境の字を消す", lambda c: drop_seal(c, u"「符号だけ違う」は **30 fact 以下**"), (u"bound",)),
    (u"F23 封の写しから §6 の (iii) の候補の字を消す", lambda c: drop_seal(c, u"人が実際にこの Excel を書く(外の人が要る。人間が決める)"), (u"bound",)),
    (u"F24 封の写しから §7 の限界の 1 本を消す", lambda c: rep(c, u"\n- 答えは提出された書類そのもので、", u"\n答えは提出された書類そのもので、", attr="seal"), (u"bound",)),
    (u"F25 封の写しから §0 の頭の 3 組の数を消す", lambda c: drop_seal(c, u"行の中の数の fact 3434・決めて全部同じ 2636・決めたが違う 0・止めた 669"), (u"bound",)),
    (u"F26 封の写しの §6 に (v) の候補を足す", lambda c: rep(c, u"  - (iv) ", u"  - (v) 別の案(0 USD)。\n  - (iv) ", attr="seal"), (u"bound",)),
    (u"C1 XE0-1 を外れにする", m_x1_miss, (u"verdict",)),
    (u"C2 XE0-2 を外れにする(上)", m_x2_high, (u"verdict",)),
    (u"C3 XE0-2 を外れにする(下: 0)", m_x2_zero, (u"verdict",)),
    (u"C4 XE0-3 を当たりにする", m_x3_hit, (u"verdict",)),
    (u"C5 XE0-4 を外れにする(下)", m_x4_low, (u"verdict",)),
    (u"C6 XE0-4 を外れにする(上)", m_x4_high, (u"verdict",)),
    (u"C7 XE0-5 を当たりにする", m_x5_hit, (u"verdict",)),
    (u"C8 XE0-5 の外れの向きを下にする(外れのまま。実測の字が変わる)", m_x5_low, (u"verdict",)),
    (u"C9 XE0-6 を外れにする(下)", m_x6_zero, (u"verdict",)),
    (u"C10 XE0-6 を外れにする(上)", m_x6_high, (u"verdict",)),
    (u"C11 XE0-7 を外れにする", m_x7_miss, (u"verdict",)),
    (u"C12 XE0-8 を外れにする", m_x8_miss, (u"verdict",)),
    (u"C13 XE0-9 を外れにする", m_x9_miss, (u"verdict",)),
    (u"C14 旗: 訓練の 3 組の違いを全部同じにして封 §0 の数に揃える", m_flag_off, (u"lines", u"sanity")),
    (u"D1 頭の「予測 2 本は外れ」を「3 本」に", lambda c: rep(c, u"**予測 2 本は外れ。**", u"**予測 3 本は外れ。**"), (u"verdict", u"lines")),
    (u"D2 頭の「当たり 7・外れ 2」を「当たり 8・外れ 1」に", lambda c: rep(c, u"判定した 9 本は 当たり 7・外れ 2", u"判定した 9 本は 当たり 8・外れ 1"), (u"verdict", u"lines")),
    (u"D3 「黙って違う fact は 0 ではない」を「0」に", lambda c: rep(c, u"**黙って違う fact は 0 ではない。**", u"**黙って違う fact は 0。**"), (u"lines", u"phrases")),
    (u"D4 「Excel を実際には通さなかった」を「通した」に", lambda c: rep(c, u"Excel を実際には通さなかった", u"Excel を実際に通した"), (u"lines", u"phrases")),
    (u"D5 「封は直していない」を「直した」に", lambda c: rep(c, u"封は直していない", u"封は直した"), (u"lines", u"phrases")),
    (u"D6 「「誤りなく受ける」とは言えない」を肯定に", lambda c: rep(c, u"「誤りなく受ける」とは言えない。", u"誤りなく受ける。"), (u"affirm", u"verdict", u"lines")),
    (u"D7 「守りの止め 4080」を 4081 に", lambda c: rep(c, u"守りの止め 4080 のうち", u"守りの止め 4081 のうち"), (u"lines",)),
    (u"D8 「5 個に 1 個は止まる」を「5 個に 2 個」に", lambda c: rep(c, u"5 個に 1 個は止まる", u"5 個に 2 個は止まる"), (u"lines", u"phrases")),
    (u"D9 「去年から持ち越す決め方の負け」を「勝ち」に", lambda c: rep(c, u"去年から持ち越す決め方の負け", u"去年から持ち越す決め方の勝ち"), (u"lines", u"phrases")),
    (u"D10 「合って当たり前」を「合わなくて当たり前」に", lambda c: rep(c, u"**合って当たり前**", u"**合わなくて当たり前**"), (u"lines", u"phrases")),
    (u"D11 §5 に (v) の候補を足す", lambda c: rep(c, u"・(iv) 文の fact", u"・(v) 別の案を数える・(iv) 文の fact"), (u"sec5",)),
    (u"D12 §5 に候補の見出しの無い案の 1 行を足す", lambda c: add_doc(c, u"- 次の便の候補は、道具に掛けること。"), (u"sec5",)),
    (u"D13 §5 の「(iii) と範囲の拡大は人間が決める」を「司令塔が決める」に", lambda c: rep(c, u"(iii) と範囲の拡大は人間が決める。", u"(iii) と範囲の拡大は司令塔が決める。"), (u"sec5",)),
    (u"D14 §5 の「(i)(ii)(iv)」を「(i)(ii)(iii)(iv)」に", lambda c: rep(c, u"(i)(ii)(iv) は前からの委任", u"(i)(ii)(iii)(iv) は前からの委任"), (u"sec5",)),
    (u"D15 §5 の候補の行から (iii) を落とす", lambda c: rep(c, u"・(iii) 人が実際にこの Excel を書く", u""), (u"sec5",)),
    (u"D16 §5 の候補の行の後ろに封に無い候補の字を足す", lambda c: rep(c, u"会社の側の欄に入れる。", u"会社の側の欄に入れる。道具に掛ける案も数える。"), (u"sec5",)),
    (u"D17 頭の限界(行の中の数の fact だけ)の文を消す", lambda c: rep(c, u"数の fact で行の中に在るものだけ。", u"X。"), (u"head", u"lines")),
    (u"D18 「記録から言えないこと」を消す", lambda c: rep(c, u"- 記録から言えないこと:", u"- X:"), (u"phrases", u"lines")),
    (u"D19 文書に「4999999%」の言い切りを足す", lambda c: add_doc(c, u"決まった fact は 4999999% だった。"), (u"numbers", u"resid")),
    (u"D20 引用の行から「言えない」「言わない」を全部消す", lambda c: setattr(c, "doc", u"\n".join((ln.replace(u"言えない", u"X").replace(u"言わない", u"X") if QUOTED.search(ln) else ln) for ln in c.doc.splitlines())), (u"affirm",)),
    (u"D21a 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"D21b 文書に docID の形を足す", lambda c: add_doc(c, u"S100ABCD"), (u"forbidden",)),
    (u"D22a 文書の commit の字 7cc388be を 1 字替える", lambda c: rep(c, u"7cc388be", u"7cc388bf", count=100), (u"commits",)),
    (u"D22b 文書の commit の字 e59be6e6 を 1 字替える", lambda c: rep(c, u"e59be6e6", u"e59be6e7", count=100), (u"commits",)),
    (u"D22c 文書に知らない commit の字を足す", lambda c: add_doc(c, u"commit 1a2b3c4d。"), (u"commits",)),
    (u"D23a §3 の見出しの「記録に欄の無い読み」を消す", lambda c: rep(c, u"## §3 記録に欄の無い読み(", u"## §3 X("), (u"sec3",)),
    (u"D23b §3 の見出しの「測った数ではない」を消す", lambda c: rep(c, u"測った数ではない。出どころは", u"X。出どころは"), (u"sec3",)),
    (u"D23c §3 の 32 を 33 に", lambda c: rep(c, u"科目に替わった 32(", u"科目に替わった 33("), (u"sec3",)),
    (u"D23d §3 の 17 本を 18 本に", lambda c: rep(c, u"のうち 17 本に在り", u"のうち 18 本に在り"), (u"sec3",)),
    (u"D23e §3 の 43 を 44 に", lambda c: rep(c, u"43 本になる", u"44 本になる"), (u"sec3",)),
    (u"D23f §3 の 516 を 517 に", lambda c: rep(c, u"文脈 516・", u"文脈 517・"), (u"sec3",)),
    (u"D23g §3 の 1028 を 1029 に", lambda c: rep(c, u"1028 に当たる", u"1029 に当たる"), (u"sec3",)),
    (u"D23h §3 の 502 を 503 に", lambda c: rep(c, u"502 を占める", u"503 を占める"), (u"sec3",)),
    (u"D23i §3 の 229 を 230 に", lambda c: rep(c, u"229 は先の止めの残り", u"230 は先の止めの残り"), (u"sec3",)),
    (u"D23j §3 の 36 を 37 に", lambda c: rep(c, u"記録の 36 本でした", u"記録の 37 本でした"), (u"sec3",)),
    (u"D23k §3 の 118 を 119 に", lambda c: rep(c, u"符号つきの 0 でない 118 の中身", u"符号つきの 0 でない 119 の中身"), (u"sec3",)),
    (u"D23l §3 の 8 行を 9 行に", lambda c: rep(c, u"表の 8 行だけだった", u"表の 9 行だけだった"), (u"sec3",)),
    (u"D24 §3 の外に「別の区分の科目に替わった」を足す", lambda c: add_doc(c, u"同じ行の字が別の区分の科目に替わった行が在った。"), (u"sec3",)),
    (u"D25a 補足を 1 本消す(封 §0)", lambda c: rep(c, u"- **封 §0 の申告の数と、", u"- **X、"), (u"lines", u"head")),
    (u"D25b 補足を 1 本消す(XE0-7)", lambda c: rep(c, u"- **XE0-7 の 0 は作りに寄る。**", u"- **X。**"), (u"lines", u"head")),
    (u"D26a §4 の 479 を 480 に", lambda c: rep(c, u"変異 479 本", u"変異 480 本"), (u"sec4", u"lines")),
    (u"D26b §4 の 130 を 131 に", lambda c: rep(c, u"130 fact(訓練 3・判定 127)", u"131 fact(訓練 3・判定 127)"), (u"sec4", u"lines")),
    (u"D27 §1 の XE0-3 の判定と XE0-4 の判定を入れ替える", lambda c: rep(c, u"| 127 fact | 外れ |", u"| 127 fact | 当たり |"), (u"lines", u"verdict")),
)
# 記録を替えて作り直す(整合)変異の名(recount が緑のまま当たり外れ・向きだけが変わることを別の試験で見る)
CONSISTENT = (m_x1_miss, m_x2_high, m_x2_zero, m_x3_hit, m_x4_low, m_x4_high, m_x5_hit, m_x5_low, m_x6_zero, m_x6_high, m_x7_miss, m_x8_miss, m_x9_miss, m_flag_off)


def run_mutations(base=None):
    base = base or Ctx()
    out = []
    for name, fn, checks in MUTATIONS:
        doc_only = name.startswith(u"D")
        c = base.with_doc(base.doc) if doc_only else base.copy()
        if doc_only:
            c.cache = {}          # 文書だけの変異でも、組み直しの記憶は記録だけに依るので共有してよいが、念のため別に持つ
        fn(c)
        res = [(k, bool(guard(CHECKS[k], c))) for k in checks]
        out.append((name, res))
    return out


# ======================================================================================================
# 掃き: 文書・記録の全部の所に 1 か所ずつ当てる
NUM_RE = WG.NUM_RE
FLIPS = ((u"以上", u"以下"), (u"以下", u"以上"), (u"未満", u"以上"), (u"多い", u"少ない"), (u"少ない", u"多い"), (u"多く", u"少なく"), (u"少なく", u"多く"), (u"増", u"減"), (u"減", u"増"), (u"高", u"低"), (u"低", u"高"),
         (u"最小", u"最大"), (u"最大", u"最小"), (u"超える", u"満たない"), (u"満たない", u"超える"), (u"大きい", u"小さい"), (u"小さい", u"大きい"), (u"全部", u"一部"), (u"一部", u"全部"),
         (u"前の年", u"今年"), (u"今年", u"前の年"), (u"当たり", u"外れ"), (u"外れ", u"当たり"), (u"同じ", u"違う"), (u"違う", u"同じ"),
         (u"在る", u"無い"), (u"無い", u"在る"), (u"通さなかった", u"通した"), (u"作った", u"作らなかった"), (u"止めた", u"決めた"), (u"決めた", u"止めた"), (u"黙って", u"止まって"), (u"止まる", u"決まる"),
         (u"できる", u"できない"), (u"言えない", u"言える"), (u"言わない", u"言う"), (u"測っていない", u"測った"), (u"負け", u"勝ち"), (u"防げなかった", u"防げた"),
         (u"より", u"と同じ"), (u"だけ", u"も"), (u"ない", u"ある"), (u"先", u"後"), (u"上限", u"下限"), (u"下限", u"上限"),
         (u"人間", u"司令塔"), (u"司令塔", u"人間"), (u"正しかった", u"誤っていた"), (u"符号", u"絶対値"), (u"去年", u"今年"), (u"個別", u"連結"))
DENOMS = (u"58476", u"61100", u"61781", u"4080")
GROUP_NUMS = (u"60", u"63", u"3")


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
        for m in re.finditer(r"(?<![0-9A-Za-z.\-])%s(?= ?組)" % g, doc):
            for h in GROUP_NUMS:
                if h != g:
                    out.append((u"W3 %s 組→%s 組 @%d" % (g, h, m.start()), doc[:m.start()] + h + doc[m.end():]))
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
    u"""表の 1 行の中で 2 つのセルを入れ替える(同じ字のときは飛ばす。「止めた」と「正しかった止め」・予測と実測・fact と率の取り違えなど)。"""
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
    u"""§5 の次の便の候補を足す・入れ替える・1 つ落とす(封 §6 の 4 つだけ)。全部赤になる。"""
    out = []
    for k, (old, new) in enumerate(((u"・(iv) 文の fact", u"・(v) 別の案を数える・(iv) 文の fact"), (u"(iv) 文の fact と行の中でない fact を会社の側の欄に入れる。", u"(iv) 文の fact と行の中でない fact を会社の側の欄に入れる・(v) 道具に掛ける。"),
                                    (u"・(iii) 人が実際にこの Excel を書く", u""), (u"・(ii) 去年の書類が無い会社の道を数える", u""), (u"(i) 止めた行を", u"(i) 止めた行を先に会社へ返し、(i) 止めた行を"),
                                    (u"(ii) 去年の書類が無い会社の道を数える・(iii) 人が実際にこの Excel を書く", u"(iii) 人が実際にこの Excel を書く・(ii) 去年の書類が無い会社の道を数える"))):
        assert old in doc, old
        out.append((u"W9 候補 %d: %s" % (k, new[:12]), doc.replace(old, new, 1)))
    for k, add in enumerate((u"- 次の便の候補は、道具に掛けること。", u"- (v) 別の案。", u"  - (i) 別の案。", u"- 次は有料の席を呼ぶ。", u"- 候補: 文の fact を先に数える。")):
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
    for p in (u"「会社が Excel で出せる」「経理の人が書ける」とは言わない", u"「誤りなく受ける」とは言えない", u"合って当たり前", u"返し方・答え方は測っていない", u"成果として読まない"):
        out.append((u"W6L 読み方「%s」を消す" % p[:10], c.doc.replace(p, u"X", 1)))
    for tok in sorted(set(sec3_number_tokens(c))):
        out.append((u"W4 §3 の数 %s を §2 に足す" % tok, c.doc.replace(u"\n## §3 ", u"\n- 足した行 %s 件。\n\n## §3 " % tok, 1)))
    for p in SEC3_ONLY_PHRASES:
        out.append((u"W4 §3 の主張「%s」を §2 に足す" % p[:6], c.doc.replace(u"\n## §3 ", u"\n- 足した行 %s。\n\n## §3 " % p, 1)))
    for w in (u"XBRL を作れる。", u"会社が Excel で出せる。", u"経理の人が書ける。", u"専用の道具が要らない。", u"誤りなく受ける。", u"誤りが無くなる。", u"EDINET の検査に通る。"):
        out.append((u"D14 引用の外に「%s」を足す" % w, c.doc + u"\n" + w + u"\n"))
    return out


def all_doc_cases(c):
    doc = c.doc
    s3n = sec3_number_tokens(c) or [u"901"]
    return span_cases(doc, s3n) + flip_cases(doc, c) + group_cases(doc) + table_cell_cases(doc) + row_swap_cases(doc) + candidate_cases(doc) + delete_cases(doc, c) + limit_cases(c)


def judge_rows_cases(c):
    u"""§1 の表の 9 行の 判定・実測・予測 のセルを、行どうしで入れ替える(全部の対)。"""
    lines = c.doc.split(u"\n")
    idx = [i for i, ln in enumerate(lines) if re.match(r"^\| XE0-\d", ln)]
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


REC_SWEEP_DOCS = (1, 3, 5, 6, 19, 20, 56, 67)


def record_sweep_cases(rec):
    u"""記録の整数・小数・旗の葉を 1 つずつ替える対象(集計 3 つ・予測・旗・組の代表 8 つ分)。"""
    out = []
    for key in GROUPS:
        for p in leaf_paths(rec[K_SUM][key]):
            out.append((K_SUM, key) + p)
    for p in leaf_paths(rec[PRED_KEY]):
        out.append((PRED_KEY,) + p)
    for p in leaf_paths(rec[K_FLAG]):
        out.append((K_FLAG,) + p)
    for n in REC_SWEEP_DOCS:
        d = doc_at(rec, n)
        for p in leaf_paths(d):
            if p[0] != u"番号":
                out.append((K_DOCS, n) + p)
    return out


def apply_leaf(c, path):
    if path[0] == K_DOCS:
        o = doc_at(c.rec, path[1])
        path = path[2:]
    else:
        o = c.rec
    for p in path[:-1]:
        o = o[p]
    v = o[path[-1]]
    o[path[-1]] = (not v) if isinstance(v, bool) else v + (0.1 if isinstance(v, float) else 1)


def run_record_sweep(base):
    out = []
    for path in record_sweep_cases(base.rec):
        c = base.copy()
        apply_leaf(c, path)
        out.append((u"W7 " + u"/".join(str(p)[:12] for p in path), first_red(c, ORDER_REC)))
    return out


# ======================================================================================================
EXPECTED_SILENT = ()         # 掃きで黙るのが設計どおりと確かめた名(理由は結果の報告と PREDICT の追記)。空 = 黙る所は無い
MIN_CASES = {u"W1a": 250, u"W1b": 250, u"W1c": 250, u"W2": 250, u"W3": 60, u"W5": 900, u"W5R": 100, u"W6": 300, u"W6L": 25, u"W4": 25, u"W9": 11, u"D14": 7}


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
        tr, jd, al = rec[K_SUM][G_TRAIN], rec[K_SUM][G_JUDGE], rec[K_SUM][G_ALL]
        PN = jd[u"数"]
        self.assertEqual((3, 60, 63), (tr[u"組"], jd[u"組"], al[u"組"]))
        self.assertEqual((61100, 2087, 537, 0, 0, 58476), (PN[u"行の中の数の fact"], PN[u"xlsx に書かなかった fact"][EXC[0]], PN[u"xlsx に書かなかった fact"][EXC[1]],
                                                              PN[u"xlsx に書かなかった fact"][EXC[2]], PN[u"xlsx に書かなかった fact"][EXC[3]], PN[u"D"]))
        self.assertEqual((60, 60, 0), tuple(PN[u"突き合わせの外"][k] for k in OUTSIDE))
        self.assertEqual((45475, 245, 12756), (PN[u"決めて全部同じ"], PN[u"決めたが違う"], PN[u"止めた"]))
        self.assertEqual(PN[u"D"], PN[u"決めて全部同じ"] + PN[u"決めたが違う"] + PN[u"止めた"])
        fo = PN[u"決めたが違うの内訳"]
        self.assertEqual((54, 60, 4, 0, 0, 127, 0, 0, 0, 0), tuple(fo[u"欄ごと"][k] for k in FIELDS10))
        self.assertEqual((127, 127, 17), (fo[u"符号だけ違う"], fo[u"符号だけ違うのうち答えの値が符号つきの 0"], fo[u"去年が空で既定の順を使った"]))
        self.assertEqual((6349, 2327, 2219, 229, 1632, 0, 0), tuple(PN[u"止めた理由ごと"][k] for k in STOPS7))
        self.assertEqual(((2219, 1669), (229, 221), (1632, 1230), (0, 0)), tuple((PN[u"守りの止め"][v][u"止めた"], PN[u"守りの止め"][v][u"正しかった止め"]) for v in GUARD_OF.values()))
        self.assertEqual((7499, 499, 6655, 72, 5394), (PN[u"場面"][SCENE[0]], PN[u"場面"][SCENE[1]], PN[u"場面"][SCENE[2]], PN[u"場面"][SCENE[3]], PN[u"無くなった行"]))
        self.assertEqual((2, 0, 0, 2), tuple(PN[u"場面"][SCENE[4]][k] for k in SCENE_SUB))
        t, a = tr[u"数"], al[u"数"]
        self.assertEqual((3434, 3305, 2633, 3, 669), (t[u"行の中の数の fact"], t[u"D"], t[u"決めて全部同じ"], t[u"決めたが違う"], t[u"止めた"]))
        self.assertEqual((61781, 48108, 248, 13425, 130), (a[u"D"], a[u"決めて全部同じ"], a[u"決めたが違う"], a[u"止めた"], a[u"決めたが違うの内訳"][u"欄ごと"][u"値"]))
        sv = stat_values(rec)
        self.assertEqual((u"4.4", u"83.6", u"92.8", 5, 40, 51, 6), sv[u"same"])
        self.assertEqual((u"7.2", u"16.4", u"95.6"), sv[u"stop"])
        self.assertEqual((24, 60, 145, 36), sv[u"diff"])
        self.assertEqual((6, 502), sv[u"outs"])
        self.assertEqual((2301, 924), sv[u"nokey"])
        self.assertEqual((118, 17, 43, 60, 60), sv[u"nonsign"])
        self.assertEqual((u"2636", u"0"), (str(rec[K_FLAG][FLAG_KEYS[1]][u"決めて全部同じ"]), str(rec[K_FLAG][FLAG_KEYS[1]][u"決めたが違う"])))
        self.assertEqual((67, 4), (rec[u"材料"][u"今年の側の書類の本数"], rec[u"材料"][u"除いた今年の書類の数"]))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(7, sum(1 for v in j.values() if v[0]))
        self.assertEqual([u"XE0-3", u"XE0-5"], miss_ids(j))
        self.assertEqual(list(IDS), list(j))
        # 当たり外れの判定は丸める前の数(境の数 74.0%・0.5%・30・16.0%・26.0%・40%・65%・2.0%・1.0%・35・95%・2)
        self.assertEqual((True, u""), j[u"XE0-1"])
        self.assertTrue(1000 * 45475 >= 740 * 58476)
        self.assertEqual((True, u""), j[u"XE0-2"])
        self.assertTrue(1000 * 245 <= 5 * 58476)
        self.assertEqual((False, u"上"), j[u"XE0-3"])
        self.assertEqual((True, u""), j[u"XE0-4"])
        self.assertEqual((False, u"上"), j[u"XE0-5"])
        self.assertTrue(100 * 3120 > 65 * 4080)
        self.assertEqual((True, u""), j[u"XE0-6"])
        self.assertEqual((True, u""), j[u"XE0-7"])
        self.assertEqual((True, u""), j[u"XE0-8"])
        self.assertEqual((True, u""), j[u"XE0-9"])

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
        self.assertEqual((479, 7, 35), (len(SG.MUTANTS), len(SG.SILENT_BY_DESIGN), seal_tests()))
        self.assertIn(u"試験 35 本。変異 479 本が赤。作りから黙る変異 7 本", self.c.doc)

    def test_d_5_the_date_supplement_follows_the_seal_and_the_record(self):
        self.assertIn(u"番号 1・2・3 が訓練、番号 4〜63 が判定の 60 組", self.c.seal)
        self.assertEqual(3, MS.SEEN_MAX_NO)
        self.assertEqual(67, self.c.rec[K_DOCS][-1][u"番号"])
        self.assertEqual(63, len(self.c.rec[K_DOCS]))
        self.assertEqual(8, len(MS.UNIT_ROWS))

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

    def test_f_3_the_blob_check_lists_the_four_frozen_files_at_their_commits(self):
        self.assertEqual([SEAL_REL, SCRIPT_REL, SEAL_GATE_REL, RECORD_REL], list(BLOB_AT))
        self.assertEqual([SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT], list(BLOB_AT.values()))
        self.assertEqual((SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT), DOC_COMMITS)
        self.assertEqual((u"aec0496d", u"7cc388be", u"e59be6e6"), DOC_COMMITS)

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
        self.assertGreaterEqual(len(MUTATIONS), 83)

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
        flips = ((m_x1_miss, u"XE0-1"), (m_x2_high, u"XE0-2"), (m_x2_zero, u"XE0-2"), (m_x3_hit, u"XE0-3"), (m_x4_low, u"XE0-4"), (m_x4_high, u"XE0-4"), (m_x5_hit, u"XE0-5"),
                 (m_x6_zero, u"XE0-6"), (m_x6_high, u"XE0-6"), (m_x7_miss, u"XE0-7"), (m_x8_miss, u"XE0-8"), (m_x9_miss, u"XE0-9"))
        for fn, key in flips:
            c = self.base.copy()
            fn(c)
            self.assertNotEqual(base_j[key][0], judge(c.rec)[key][0], (fn.__name__, key))
            self.assertNotEqual([], verdict_problems(c), (fn.__name__, key))
        # 外れの向き(XE0-2・XE0-4・XE0-5・XE0-6 の下と上)は別々に出る
        for fn, key, way in ((m_x2_high, u"XE0-2", u"上"), (m_x2_zero, u"XE0-2", u"下"), (m_x4_low, u"XE0-4", u"下"), (m_x4_high, u"XE0-4", u"上"), (m_x5_low, u"XE0-5", u"下"),
                             (m_x6_zero, u"XE0-6", u"下"), (m_x6_high, u"XE0-6", u"上")):
            c = self.base.copy()
            fn(c)
            self.assertEqual(way, judge(c.rec)[key][1], (fn.__name__, key))
        # 旗: 訓練の 3 組の数が封 §0 の数と同じになると旗は立たず、文書の「立っている」と合わない
        c = self.base.copy()
        m_flag_off(c)
        self.assertEqual([], recount_problems(c))
        self.assertFalse(c.rec[K_FLAG][FLAG_KEYS[2]])
        self.assertNotEqual([], lines_problems(c))
        self.assertNotEqual([], sanity_problems(c))

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)
        for k in (u"numbers", u"resid", u"sec5"):
            self.assertIn(k, ORDER_DOC)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数(丸める前の整数): 下限・上限とも含む/含まない。"""
        def j(**kw):
            p = collections.OrderedDict([(u"XE0-1", (75, 100)), (u"XE0-2", (1, 1000)), (u"XE0-3", (30, 100)), (u"XE0-4", (20, 100)), (u"XE0-5", (50, 100)),
                                         (u"XE0-6", (1, 100)), (u"XE0-7", (0, 100)), (u"XE0-8", (35, 60)), (u"XE0-9", (2, 60))])
            for k, v in kw.items():
                p[k.replace(u"_", u"-")] = v
            return judge_nums(p)
        self.assertTrue(j(XE0_1=(74, 100))[u"XE0-1"][0])
        self.assertFalse(j(XE0_1=(73, 100))[u"XE0-1"][0])
        self.assertFalse(j(XE0_1=(0, 0))[u"XE0-1"][0])
        self.assertTrue(j(XE0_2=(5, 1000))[u"XE0-2"][0])
        self.assertFalse(j(XE0_2=(6, 1000))[u"XE0-2"][0])
        self.assertEqual(u"上", j(XE0_2=(6, 1000))[u"XE0-2"][1])
        self.assertFalse(j(XE0_2=(0, 1000))[u"XE0-2"][0])
        self.assertEqual(u"下", j(XE0_2=(0, 1000))[u"XE0-2"][1])
        self.assertTrue(j(XE0_3=(30, 245))[u"XE0-3"][0])
        self.assertFalse(j(XE0_3=(31, 245))[u"XE0-3"][0])
        self.assertTrue(j(XE0_3=(0, 245))[u"XE0-3"][0])
        self.assertTrue(j(XE0_4=(16, 100))[u"XE0-4"][0])
        self.assertFalse(j(XE0_4=(15, 100))[u"XE0-4"][0])
        self.assertEqual(u"下", j(XE0_4=(15, 100))[u"XE0-4"][1])
        self.assertTrue(j(XE0_4=(26, 100))[u"XE0-4"][0])
        self.assertFalse(j(XE0_4=(27, 100))[u"XE0-4"][0])
        self.assertEqual(u"上", j(XE0_4=(27, 100))[u"XE0-4"][1])
        self.assertTrue(j(XE0_5=(40, 100))[u"XE0-5"][0])
        self.assertFalse(j(XE0_5=(39, 100))[u"XE0-5"][0])
        self.assertTrue(j(XE0_5=(65, 100))[u"XE0-5"][0])
        self.assertFalse(j(XE0_5=(66, 100))[u"XE0-5"][0])
        self.assertEqual(u"下", j(XE0_5=(39, 100))[u"XE0-5"][1])
        self.assertEqual(u"上", j(XE0_5=(66, 100))[u"XE0-5"][1])
        self.assertFalse(j(XE0_5=(0, 0))[u"XE0-5"][0])
        self.assertTrue(j(XE0_6=(2, 100))[u"XE0-6"][0])
        self.assertFalse(j(XE0_6=(3, 100))[u"XE0-6"][0])
        self.assertFalse(j(XE0_6=(0, 100))[u"XE0-6"][0])
        self.assertEqual(u"下", j(XE0_6=(0, 100))[u"XE0-6"][1])
        self.assertTrue(j(XE0_7=(1, 100))[u"XE0-7"][0])
        self.assertFalse(j(XE0_7=(2, 100))[u"XE0-7"][0])
        self.assertFalse(j(XE0_7=(0, 0))[u"XE0-7"][0])
        self.assertTrue(j(XE0_8=(35, 60))[u"XE0-8"][0])
        self.assertFalse(j(XE0_8=(34, 60))[u"XE0-8"][0])
        self.assertTrue(j(XE0_9=(2, 60))[u"XE0-9"][0])
        self.assertFalse(j(XE0_9=(3, 60))[u"XE0-9"][0])
        self.assertTrue(j(XE0_9=(0, 60))[u"XE0-9"][0])

    def test_g_6_the_section5_decision_follows_the_seal_section6(self):
        c = self.base
        s6 = seal_s6_text(c.seal)
        sec5 = section(c.doc, u"## §5 ", None)
        self.assertEqual([], sec5_problems(c))
        self.assertEqual(4, len(re.findall(u"^  - \\((?:i|ii|iii|iv)\\) ", s6, re.M)))
        # 文書の §5 に 5 つ目・封に無い候補の字・見出しの無い案を足す(全部赤)・(iii) を人間から動かす・決めの文を消すと赤
        for add in (u"- 次の便の候補は、別にある。\n", u"- (v) 別の案。\n", u"- 次は道具に掛ける。\n", u"- 候補 (vi) を数える。\n"):
            self.assertNotEqual([], sec5_problems(c.with_doc(c.doc.rstrip(u"\n") + u"\n" + add)), add)
        for old, new in ((u"(iii) と範囲の拡大は人間が決める。", u"(iii) と範囲の拡大は司令塔が決める。"), (u"(i)(ii)(iv) は前からの委任の内側で司令塔が決める。", u"(i)(ii)(iv) は人間が決める。"),
                         (u"・(iv) 文の fact", u"・(iv) 別の案・(v) 文の fact"), (u"・(iii) 人が実際にこの Excel を書く", u"")):
            self.assertIn(old, sec5, old)
            self.assertNotEqual([], sec5_problems(c.with_doc(c.doc.replace(old, new, 1))), old)
        # 封の §6 に (v) が増えたら封の側の検査が赤
        cc = c.copy()
        rep(cc, u"  - (iv) ", u"  - (v) 別の案(0 USD)。\n  - (iv) ", attr="seal")
        self.assertNotEqual([], bound_problems(cc))

    def test_g_7_the_group_sizes_and_the_numbers_are_not_confused(self):
        rec = self.base.rec
        train, judge_docs = split_docs(rec)
        self.assertEqual((3, 60, 63), (len(train), len(judge_docs), len(rec[K_DOCS])))
        self.assertEqual(len(set([3, 60, 63])), 3)
        c = self.base.copy()
        m_swap_groups(c)
        self.assertNotEqual([], recount_problems(c))

    def test_g_8_the_verdict_table_stays_the_60_group_numbers(self):
        for old, new in ((u"| 45475/58476(77.8%) | 当たり |", u"| 48108/61781(77.9%) | 当たり |"), (u"| 45475/58476(77.8%) | 当たり |", u"| 2633/3305(79.7%) | 当たり |"),
                         (u"| 245/58476(0.4%) | 当たり |", u"| 248/61781(0.4%) | 当たり |"), (u"| 12756/58476(21.8%) | 当たり |", u"| 13425/61781(21.7%) | 当たり |"),
                         (u"| 0/61100(0.0%) | 当たり |", u"| 0/64534(0.0%) | 当たり |"), (u"| 36 本(60 本のうち) | 当たり |", u"| 36 本(63 本のうち) | 当たり |"),
                         (u"| 0 本(60 本のうち) | 当たり |", u"| 0 本(3 本のうち) | 当たり |"), (u"| 127 fact | 外れ |", u"| 130 fact | 外れ |"), (u"| 3120/4080(76.5%) | 外れ |", u"| 3120/4080(76.5%) | 当たり |")):
            self.assertIn(old, self.base.doc, old)
            c = self.base.with_doc(self.base.doc.replace(old, new, 1))
            self.assertNotEqual([], verdict_problems(c), old)
        c = self.base.with_doc(self.base.doc.replace(u"| 127 fact | 外れ |", u"| 130 fact | 外れ |", 1))
        self.assertNotEqual([], verdict_problems(c))
        c = self.base.with_doc(self.base.doc.replace(u"| 45475/58476(77.8%) | 当たり |", u"| 2633/3305(79.7%) | 当たり |", 1))
        self.assertTrue(any(u"混ざっている" in x for x in verdict_problems(c)))

    def test_g_9_a_confirmation_of_no_error_is_red_when_the_record_has_a_wrong_one(self):
        u"""記録の決めたが違うが 1 以上なのに文書が「誤りなく受ける」を肯定すれば赤(否定の外)。記録を 0 にすると封 §6 の旗(自分の欠陥を疑う)で赤。"""
        c = self.base
        self.assertGreaterEqual(c.rec[K_SUM][G_JUDGE][u"数"][u"決めたが違う"], 1)
        cc = c.with_doc(c.doc.replace(u"「誤りなく受ける」とは言えない。", u"誤りなく受ける。", 1))
        self.assertNotEqual([], affirm_problems(cc))
        self.assertTrue(any(u"誤りなく受ける" in x for x in verdict_problems(cc)))
        c0 = c.copy()
        each_judge(c0, lambda d: (lambda n: (diff_remove(d, n), d.__setitem__(u"決めて全部同じ", d[u"決めて全部同じ"] + n)))(d[u"決めたが違う"]))
        self.assertTrue(any(u"先に自分の欠陥を疑う" in x for x in verdict_problems(c0)))

    def test_h_1_the_sweep_over_every_number_direction_word_group_swap_cell_and_line_stays_red(self):
        c = self.base
        cases = all_doc_cases(c) + judge_rows_cases(c)
        results = run_doc_cases(c, cases)
        silent = [n for n, k in results if k is None]
        by_kind = collections.Counter(n.split(u" ")[0] for n, _ in results)
        self.assertEqual(sorted(EXPECTED_SILENT), sorted(silent))
        for kind, lo in MIN_CASES.items():
            self.assertGreaterEqual(by_kind[kind], lo, kind)
        self.assertGreater(len(results), 2500)

    def test_h_2_the_record_leaf_sweep_stays_red(self):
        results = run_record_sweep(self.base)
        silent = [n for n, k in results if k is None]
        self.assertEqual([], silent)
        self.assertGreater(len(results), 500)

    def test_h_3_section3_prose_sweep_reports_what_stays_silent(self):
        u"""§3 は形で縛る(数の並び・記録との整合・語の留め)。§3 の中の文の削除・向きの語の反転で黙る所が在れば、それを数えて留める(増えたら赤)。"""
        c = self.base
        results = run_doc_cases(c, sec3_cases(c))
        silent = [n for n, k in results if k is None]
        self.assertEqual(sorted(SEC3_SILENT), sorted(silent))

    def test_h_4_every_added_or_dropped_next_candidate_is_red_in_the_section5_check_alone(self):
        u"""候補を足す・落とす・入れ替えるケース(W9)は、lines に頼らず §5 の検査だけで赤(封 §6 の (i)〜(iv) の 4 つだけ)。"""
        cases = candidate_cases(self.base.doc)
        self.assertEqual(11, len(cases))
        for name, text in cases:
            self.assertNotEqual([], sec5_problems(self.base.with_doc(text)), name)


SEC3_SILENT = ()


if __name__ == "__main__":
    unittest.main()
