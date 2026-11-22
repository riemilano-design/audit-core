# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_PRIOR_YEAR_DRAFT_SEAL_2026-11-22.md(ce70f71f)の結果の文書 docs/XBRL_PRIOR_YEAR_DRAFT_RESULT_2026-11-22.md(便 XY0)。

封の門 ``test_xbrl_prior_year_draft_seal.py`` の次の段。**追跡されている記録・script・封・封の門・便 XG1 の記録・結果の文書と git の履歴だけを読む**(書類の置き場は読まない・通信しない・鍵は読まない)。
便 XA0 の結果の門 ``test_xbrl_sheet_wall_result.py`` の部品(読み・sha256・% の丸め・節の切り出し・数のトークン・禁止語・blob の道具)を読み込んで使う(門としては走らせない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封・封の門・便 XG1 の記録の sha256(字で留める)・記録の script の sha256・封の commit の欄・記録の限界の欄が script の字と同じ
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、集計の全部の欄を数え直す(段どうしの関係 P・PK・C と、集まり S ⊆ B の関係も)。予測の判定に要る数を集計から作り直した値と照らす
 c 予測 XY0-1〜XY0-7 の当たり外れを、封 §4 の字から取った境(丸める前の整数・分数で)と記録から決め直し、文書 §1 の表・件数と同じことを見る。
   封 §4 の「先に自分の欠陥を疑う」3 条件を封の字のまま決め直す(どれも発火しない)・封 §6 の決め(XY0-2 と XY0-3 が両方当たり → 次の便の候補 (i)(ii) を示す)と文書が合う
 d 結果の文書の数: 文書の主な主張の文(減る・増える・「9 割近く」「1000 行に 1 行ほど」「1 割前後」を含む)は、記録から組んだ字と断片で一致を見る。残りの数字は記録から組んだ数の内、
   記録から組んだ字を除いた残りの 3 桁以上の数は、字で留めた境の数だけ。書類ごとの率の最小・中央・最大と 80・85・90・95・98% 以上の本数・W1 の在る書類・集まり B から S を引いた類・2026 行・1490 行は書類ごとの数から導き直す。
   便 XG1 の 80.4% は便 XG1 の記録から読む
 e 文書の頭の負けと限界(封 §7 の 6 本・封 §0 の申告)・禁止語・「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」「人が書ける」を肯定で書かない・docID と EDINET コードの形
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


WG = load_module("tests/measure/test_xbrl_sheet_wall_result.py", "xbrl_sheet_wall_result_gate_for_prior_year_draft_result_gate")                # 便 XA0 の結果の門の部品。門としては走らせない
SG = load_module("tests/measure/test_xbrl_prior_year_draft_seal.py", "xbrl_prior_year_draft_seal_gate_for_result_gate")                # 封の門の部品。門としては走らせない
PR = SG.PR
MS = SG.MS

read, sha_file, guard, pct, section, rep = WG.read, WG.sha_file, WG.guard, WG.pct, WG.section, WG.rep
add_doc, drop_all = WG.add_doc, WG.drop_all

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
XG1_RECORD_REL = "fixtures/xbrl/cd8/tag_narrow_2026-11-21.json"
GATE_REL = "tests/measure/test_xbrl_prior_year_draft_result.py"
DOC_REL = "docs/XBRL_PRIOR_YEAR_DRAFT_RESULT_2026-11-22.md"
SCRIPT_COMMIT_SHORT = "150c7fe6"                  # script と封の門を足した commit
RECORD_COMMIT_SHORT = "4591db32"                  # 記録を足した commit(同じ commit で封の門の 1 か所を直した)
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, RECORD_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
HISTORY = collections.OrderedDict([
    (SEAL_REL, [SEAL_COMMIT_SHORT]), (SCRIPT_REL, [SCRIPT_COMMIT_SHORT]), (SEAL_GATE_REL, [SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT]), (RECORD_REL, [RECORD_COMMIT_SHORT])])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "9e7b32f6ec4ec0b8645213cc66b6df520319f5e6e6dd316fcc232d531d98fcfb"),
    (SCRIPT_REL, "e44238c3416dd07f201387972e5939fd50ee2129baf655b4d6d1601413c6a677"),
    (SEAL_GATE_REL, "4045e7f35c08217ea399d183cba108783b84d946d1b594bbc7cebb5476ddaab1"),
    (SEAL_REL, "89d54f6bfd1a34f3ef8d51f5a467f68d7ddd9927663be21788985115863e4e10"),
    (XG1_RECORD_REL, "f6873eeaab3eb2b51eaf89aac33dc708289cc8b5f91208ff947111443968d3ff")])

PAIRS = 63
DOC_COUNT = 67
DROPPED = 4
CLASSES = ("U", "A", "W1", "W2", "N")
AGG = u"集計"
PRED_KEY = u"予測の判定に要る数(XY0-1〜XY0-7。当たり・外れは結果の文書で)"
K_SSTAGE = u"集まり S の段ごとの類別"
K_BSTAGE = u"集まり B の段ごとの類別"
K_SROWS = u"集まり S の行の数"
K_BROWS = u"集まり B の行の数"
K_FALL = u"段 C で標準の表へ落ちた S の行の数"
K_FALLC = u"段 C で標準の表へ落ちた S の行の類別"
K_RATE = u"段 PK・集まり S の U の率(%)"
K_NONEMPTY = u"集まり S の行が 1 行以上在る書類の数"
IDS = (u"XY0-1", u"XY0-2", u"XY0-3", u"XY0-4", u"XY0-5", u"XY0-6", u"XY0-7")
PK_KEYS = (u"XY0-1 段 P・集まり S の類 U / 集まり S の行", u"XY0-2 段 PK・集まり S の類 U / 集まり S の行", u"XY0-3 段 PK・集まり S の類 W1 / 集まり S の行",
           u"XY0-3 段 PK・集まり S の類 W1 / (U + W1)", u"XY0-4 段 PK・集まり S の類 N / 集まり S の行", u"XY0-5 段 C・集まり S の類 U / 集まり S の行",
           u"XY0-5 段 C・集まり S の類 W1 / 集まり S の行", u"XY0-6 段 PK の類 U の率(集まり B と集まり S)", u"XY0-7 段 PK・集まり S の U の率が 95% 以上の書類 / 組の数")
THRESHOLDS = (80, 85, 90, 95, 98)

# 封の字(封の門が script と照らし、ここでは文書が引く字の在り処を縛る)
BOUND_SEAL_PHRASES = (u"段 P・集まり S の類 U は 72% 以上 88% 以下", u"段 PK・集まり S の類 U は 84% 以上 95% 以下", u"段 PK・集まり S の類 W1 は 1.5% 以下",
                      u"段 PK・集まり S の類 N は 3% 以上 12% 以下", u"段 C・集まり S の類 U は 86% 以上 97% 以下で、類 W1 は 2.5% 以下",
                      u"段 PK の類 U の率は、集まり B が集まり S より 5 ポイントを超えて低くはならない", u"段 PK・集まり S の U の率が 95% 以上の書類は 10 本以上 40 本以下",
                      u"段 PK・集まり S の U が 98% を超えたら、先に自分の欠陥を疑う", u"W1 が 5% を超えても同じ", u"N が 30% を超えても同じ",
                      u"XY0-2 と XY0-3 が両方当たりなら、次の便の候補を人間に示す", u"どちらかが外れたら、外れ方を書いて、作る側へ進む道を人間に返す",
                      u"「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」は、この便からは言えない",
                      u"並びの頭の 1 組だけ", u"ほかの 62 組は 1 行も数えていない")
# 封 §7 の限界 6 本の、文書の頭に在るべき字(どれも封 §7 にも在る)
LIMIT_HEAD = (u"前の年の書類も今年の書類も、専用の道具が組んだ後の字", u"この便の U は「上の限り」に近い読み", u"前の年の XBRL が在る会社にしか使えない",
              u"前の年に無かった行(N)は、道具がいちばん要る所", u"63 組は無作為ではない", u"年は 1 組(1 年の差)だけ", u"測るのは要素の名だけ",
              u"1 行に要素が 2 種類以上在る行・行の字が空の行は分母の外", u"「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」は、この便からは言えない")
HEAD_PHRASES = LIMIT_HEAD + (u"先に負けと限界を書く", u"記録から 1 つずつ読んだもの", u"予測は 63 組のうち並びの頭の 1 組を段 P で数えてから立てた(封 §0 の申告)", u"当たりやすい予測だった",
                             u"0 USD・LLM の席は呼んでいない・通信していない", u"engine は 0 行", u"黙って違う行(W1)は 0 ではない", u"XY0-7 は外れ",
                             u"書類を 1 本まるごと前の年の下書きだけで済ませられる会社は、この 63 組にはほぼ無い", u"この便の U は「上の限り」に近い読み")
PHRASES = (u"言えること", u"言えないこと", u"人間に示す次の便の候補", u"どちらにも別の封が先", u"盲検ではない", u"人間が決めること", u"相手の問いへの、この便からの答え",
           u"差をそのまま「前の年の表の効き」とは読まない", u"どの字が重なったかは記録に無い", u"封も予測も結果を見てから書き換えていない", u"記録は当たり外れを持たない",
           u"原稿の字(道具が組む前の字)での率", u"前の年の XBRL が無い会社での率", u"測ったのは道具が組んだ後の字どうしで、原稿からの率ではない", u"「1 本をまるごと済ませる」ものではない")
QUOTED = re.compile(u"「[^」]*(?:作れる|専用の道具が要らない|人が書ける|AI が書ける|検査に通る)[^」]*」")
AFFIRM_WORDS = (u"作れる(?!か)", u"作れます", u"専用の道具が要らない", u"人が書ける(?!か)", u"AI が書ける", u"検査に通る(?!こと|か)")
FORBIDDEN_WORDS = tuple(WG.FORBIDDEN_WORDS)
STRUCTURAL = WG.STRUCTURAL
# 記録から組んだ字を文書から除いた残りに在ってよい数(字で留める。どれも封の境か、文書の見出し・説明の数)
RESIDUAL_OK = set([u"72", u"88", u"84", u"95", u"1.5", u"3", u"12", u"86", u"97", u"2.5", u"5", u"10", u"40", u"98", u"80", u"85", u"90", u"30", u"1000", u"63", u"67", u"62", u"4", u"1"])
NUM_RE = WG.NUM_RE
doc_number_tokens = WG.doc_number_tokens


# ======================================================================================================
class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.xg1 = json.loads(read(XG1_RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.xg1 = copy.deepcopy(self.xg1)
        c.doc = self.doc
        c.seal = self.seal
        c.shas = collections.OrderedDict(self.shas)
        return c


def norm(o):
    return json.loads(json.dumps(o, ensure_ascii=False))


def cls_sum(a, b):
    return collections.OrderedDict((k, a[k] + b[k]) for k in CLASSES)


def zero_cls():
    return collections.OrderedDict((k, 0) for k in CLASSES)


def rate_row(n, d):
    return collections.OrderedDict([(u"行", n), (u"分母", d), (u"%", float(pct(n, d)) if d else 0.0)])


def xg1_pct(c):
    u"""便 XG1 の記録の「段 3 の類 U / 計算書の行」の %。"""
    key = [k for k in c.xg1[u"予測の判定に要る数(XG1-1〜XG1-7。当たり・外れは結果の文書で)"] if k.startswith(u"XG1-3 段 3 の類 U")][0]
    return c.xg1[u"予測の判定に要る数(XG1-1〜XG1-7。当たり・外れは結果の文書で)"][key][u"%"]


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def totals(docs):
    u"""書類ごとの数から、記録の集計の欄を数え直す。"""
    t = collections.OrderedDict()
    t[K_SROWS] = sum(d[K_SROWS] for d in docs)
    t[K_BROWS] = sum(d[K_BROWS] for d in docs)
    t[K_SSTAGE] = collections.OrderedDict((st, collections.OrderedDict((k, sum(d[K_SSTAGE][st][k] for d in docs)) for k in CLASSES)) for st in ("P", "PK", "C"))
    t[K_BSTAGE] = collections.OrderedDict((st, collections.OrderedDict((k, sum(d[K_BSTAGE][st][k] for d in docs)) for k in CLASSES)) for st in ("P", "PK"))
    t[K_FALL] = sum(d[K_FALL] for d in docs)
    t[K_FALLC] = collections.OrderedDict((k, sum(d[K_FALLC][k] for d in docs)) for k in CLASSES)
    t[K_NONEMPTY] = sum(1 for d in docs if d[K_SROWS] > 0)
    return t


def doc_problems(d):
    u"""書類 1 つの中の関係(段の和・段 C = 段 PK + 落ちた行・集まり S ⊆ B・段 PK は段 P を細かくする)。"""
    out = []
    n = d[u"番号"]
    sp, spk, sc = (d[K_SSTAGE][s] for s in ("P", "PK", "C"))
    bp, bpk = d[K_BSTAGE][u"P"], d[K_BSTAGE][u"PK"]
    fc = d[K_FALLC]
    for name, st, rows in (("S/P", sp, K_SROWS), ("S/PK", spk, K_SROWS), ("S/C", sc, K_SROWS), ("B/P", bp, K_BROWS), ("B/PK", bpk, K_BROWS)):
        if list(st) != list(CLASSES) or sum(st.values()) != d[rows]:
            out.append(u"書類 %d の %s の類の和が行の数と違う" % (n, name))
    if d[K_BROWS] < d[K_SROWS]:
        out.append(u"書類 %d の集まり B が集まり S より少ない" % n)
    for k in CLASSES:
        if bp[k] < sp[k] or bpk[k] < spk[k]:
            out.append(u"書類 %d の集まり B の類 %s が集まり S より少ない(S ⊆ B)" % (n, k))
    if list(fc) != list(CLASSES) or sum(fc.values()) != d[K_FALL] or d[K_FALL] != spk["N"]:
        out.append(u"書類 %d の落ちた行の類の和が落ちた行の数か段 PK の N と違う" % n)
    for k in (u"U", u"A", u"W1", u"W2"):
        if sc[k] != spk[k] + fc[k]:
            out.append(u"書類 %d の段 C の類 %s が段 PK + 落ちた行と違う" % (n, k))
    if sc["N"] != fc["N"]:
        out.append(u"書類 %d の段 C の N が落ちた行の N と違う" % n)
    if spk["N"] < sp["N"] or bpk["N"] < bp["N"]:
        out.append(u"書類 %d の段 PK の N が段 P の N より少ない(PK は P を細かくする)" % n)
    if d[K_SROWS] > 0 and d[K_RATE] != float(pct(spk["U"], d[K_SROWS])):
        out.append(u"書類 %d の U の率の欄が数え直した値と違う" % n)
    return out


def pred_expected(rec):
    s = rec[AGG]
    S, B = s[K_SSTAGE], s[K_BSTAGE]
    rs = s[K_SROWS]
    docs95 = sum(1 for d in rec[u"書類"] if d[K_SROWS] > 0 and 100 * d[K_SSTAGE]["PK"]["U"] >= 95 * d[K_SROWS])
    return collections.OrderedDict([
        (PK_KEYS[0], rate_row(S["P"]["U"], rs)),
        (PK_KEYS[1], rate_row(S["PK"]["U"], rs)),
        (PK_KEYS[2], rate_row(S["PK"]["W1"], rs)),
        (PK_KEYS[3], rate_row(S["PK"]["W1"], S["PK"]["U"] + S["PK"]["W1"])),
        (PK_KEYS[4], rate_row(S["PK"]["N"], rs)),
        (PK_KEYS[5], rate_row(S["C"]["U"], rs)),
        (PK_KEYS[6], rate_row(S["C"]["W1"], rs)),
        (PK_KEYS[7], collections.OrderedDict([
            (u"集まり B の U の行", B["PK"]["U"]), (u"集まり B の行", s[K_BROWS]), (u"集まり B の %", float(pct(B["PK"]["U"], s[K_BROWS]))),
            (u"集まり S の U の行", S["PK"]["U"]), (u"集まり S の行", rs), (u"集まり S の %", float(pct(S["PK"]["U"], rs))),
            (u"集まり B から集まり S を引いた差(ポイント)", round(float(pct(B["PK"]["U"], s[K_BROWS])) - float(pct(S["PK"]["U"], rs)), 1))])),
        (PK_KEYS[8], collections.OrderedDict([(u"書類", docs95), (u"分母", len(rec[u"書類"])), (u"集まり S の行が 1 行以上在る書類", s[K_NONEMPTY])]))])


def recount_problems(c):
    rec = c.rec
    out = []
    docs = rec[u"書類"]
    m = rec[u"材料"]
    nums = [d[u"番号"] for d in docs]
    if len(nums) != PAIRS or nums != sorted(set(nums)) or nums[0] < 1 or nums[-1] > DOC_COUNT or m[u"組の数"] != PAIRS or m[u"今年の側の書類の本数"] != DOC_COUNT or m[u"除いた今年の書類の数"] != DROPPED \
            or m[u"今年の側の書類の本数"] != m[u"組の数"] + m[u"除いた今年の書類の数"]:
        return [u"書類の番号(67 本の中の昇順の 63 個)・材料の組の数 63・今年の側 67・除いた 4 が違う"]
    for d in docs:
        out.extend(doc_problems(d))
    want, have = totals(docs), rec[AGG]
    if list(have) != list(want):
        return out + [u"集計の欄の名・並びが数え直しと違う"]
    for k in want:
        if norm(have[k]) != norm(want[k]):
            out.append(u"集計の「%s」が書類ごとの数から数え直した値と違う" % k)
    if norm(rec[PRED_KEY]) != norm(pred_expected(rec)):
        out.append(u"予測の判定に要る数が集計から作り直した値と違う")
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
    return out


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    out = []
    try:
        MS.check_clean(c.rec, text)
    except SystemExit:
        out.append(u"記録の検査(欄・形・file の名・日付)が止める")
    except Exception as exc:                    # noqa: BLE001
        out.append(u"記録の検査が止める: %s" % type(exc).__name__)
    if WG.DOCID_FORM.search(re.sub(r"[0-9a-fA-F]{32,}", u"", text)) or WG.ECODE_FORM.search(text):
        out.append(u"記録に docid か EDINET コードの形が在る")
    return out


def bound_problems(c):
    out = [u"封に字が無い: %s" % p for p in BOUND_SEAL_PHRASES if p not in c.seal]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    rows = [ln for ln in sec4.splitlines() if re.match(r"^\| XY0-\d", ln)]
    if len(rows) != 7:
        out.append(u"封 §4 の表の行が 7 つでない")
    sec7 = section(c.seal, u"## §7 ", None)
    for p in LIMIT_HEAD:
        if p not in sec7:
            out.append(u"封 §7 に限界の字が無い: %s" % p)
    return out


# ======================================================================================================
# c 当たり外れの決め直し(封 §4 の境。丸める前の整数)
def judge(rec):
    u"""封 §4 の境から XY0-1〜XY0-7 を決め直す。値は (当たりか, 外れた向き)。"""
    s = rec[AGG]
    S, B = s[K_SSTAGE], s[K_BSTAGE]
    rs = s[K_SROWS]
    rb = s[K_BROWS]
    out = collections.OrderedDict()

    def put(k, lo_ok, hi_ok):
        out[k] = (lo_ok and hi_ok, u"" if lo_ok and hi_ok else (u"下" if not lo_ok else u"上"))
    put(u"XY0-1", 100 * S["P"]["U"] >= 72 * rs, 100 * S["P"]["U"] <= 88 * rs)
    put(u"XY0-2", 100 * S["PK"]["U"] >= 84 * rs, 100 * S["PK"]["U"] <= 95 * rs)
    put(u"XY0-3", True, 1000 * S["PK"]["W1"] <= 15 * rs)
    put(u"XY0-4", 100 * S["PK"]["N"] >= 3 * rs, 100 * S["PK"]["N"] <= 12 * rs)
    u_ok = 100 * S["C"]["U"] >= 86 * rs and 100 * S["C"]["U"] <= 97 * rs
    w_ok = 1000 * S["C"]["W1"] <= 25 * rs
    out[u"XY0-5"] = (u_ok and w_ok, u"" if u_ok and w_ok else u"U か W1")
    diff = Fraction(100 * B["PK"]["U"], rb) - Fraction(100 * S["PK"]["U"], rs)
    put(u"XY0-6", diff >= -5, True)
    n95 = sum(1 for d in rec[u"書類"] if d[K_SROWS] > 0 and 100 * d[K_SSTAGE]["PK"]["U"] >= 95 * d[K_SROWS])
    put(u"XY0-7", n95 >= 10, n95 <= 40)
    return out


def suspects(c):
    u"""封 §4 の「先に自分の欠陥を疑う」3 条件(封の字のまま。U が 98% を超える・W1 が 5% を超える・N が 30% を超える)。"""
    s = c.rec[AGG]
    pk = s[K_SSTAGE]["PK"]
    rs = s[K_SROWS]
    return (100 * pk["U"] > 98 * rs, 100 * pk["W1"] > 5 * rs, 100 * pk["N"] > 30 * rs)


def cell_text(rec, key):
    s = rec[AGG]
    S, B = s[K_SSTAGE], s[K_BSTAGE]
    rs, rb = s[K_SROWS], s[K_BROWS]
    n95 = sum(1 for d in rec[u"書類"] if d[K_SROWS] > 0 and 100 * d[K_SSTAGE]["PK"]["U"] >= 95 * d[K_SROWS])

    def f(a, b):
        return u"%d/%d(%s%%)" % (a, b, pct(a, b))
    diff = round(float(pct(B["PK"]["U"], rb)) - float(pct(S["PK"]["U"], rs)), 1)
    return {u"XY0-1": f(S["P"]["U"], rs), u"XY0-2": f(S["PK"]["U"], rs), u"XY0-3": f(S["PK"]["W1"], rs), u"XY0-4": f(S["PK"]["N"], rs),
            u"XY0-5": u"U %s・W1 %s" % (f(S["C"]["U"], rs), f(S["C"]["W1"], rs)),
            u"XY0-6": u"B %s・S %s%%・差 %s%.1f ポイント" % (f(B["PK"]["U"], rb), pct(S["PK"]["U"], rs), u"−" if diff < 0 else u"", abs(diff)),
            u"XY0-7": u"%d/%d" % (n95, len(rec[u"書類"]))}[key]


def expected_cells(c):
    out = collections.OrderedDict()
    for k, (ok, way) in judge(c.rec).items():
        out[k] = (cell_text(c.rec, k), u"当たり" if ok else u"外れ")
    return out


def verdict_problems(c):
    rec = c.rec
    j = judge(rec)
    want = expected_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XY0-\d)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XY0-1〜XY0-7 でない"]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    for k, cells in rows.items():
        if len(cells) != 3:
            out.append(u"%s の行の欄の数が違う" % k)
            continue
        if cells[0] not in sec4:
            out.append(u"%s の予測の字が封 §4 の表に無い: %s" % (k, cells[0]))
        if cells[1] != want[k][0]:
            out.append(u"%s の実測の字が記録から組んだ字と違う: %s" % (k, cells[1]))
        if cells[2] != want[k][1]:
            out.append(u"%s の判定が決め直した判定と違う: %s(決め直し: %s)" % (k, cells[2], want[k][1]))
    for k in (u"XY0-2", u"XY0-3"):
        if not re.search(r"^\| %s\(主\) \|" % k, c.doc, re.M):
            out.append(u"%s の行に「(主)」が無い(封 §4 の主の読み)" % k)
    hits = sum(1 for v in j.values() if v[0])
    if u"- 当たり %d・外れ %d。" % (hits, len(j) - hits) not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = c.doc.split(u"## §1")[0]
    if u"判定した %d 本は 当たり %d・外れ %d。" % (len(j), hits, len(j) - hits) not in head:
        out.append(u"文書の頭の件数が決め直した値と違う")
    for k, (ok, way) in j.items():
        if not ok and not re.search(r"\*\*%s は外れ。\*\*" % k, head):
            out.append(u"外れた %s の言い切りが文書の頭に無い" % k)
        if ok and re.search(r"\*\*%s は外れ" % k, head):
            out.append(u"当たりの %s を文書の頭が外れと書いている" % k)
    sec1, sec5 = section(c.doc, u"## §1 ", u"## §2 "), section(c.doc, u"## §5 ", None)
    sus = suspects(c)
    if any(sus):
        out.append(u"封 §4 の「先に自分の欠陥を疑う」条件が発火している(U が 98%% を超える・W1 が 5%% を超える・N が 30%% を超える): %s" % (sus,))
    line = [ln for ln in sec1.splitlines() if u"「先に自分の欠陥を疑う」条件" in ln]
    if len(line) != 1 or u"(段 PK・集まり S の U が 98% を超える・W1 が 5% を超える・N が 30% を超える)は、どれも発火しない。" not in line[0]:
        out.append(u"文書 §1 の自己点検の言い切り(3 条件・どれも発火しない)が封の字と合わない")
    # 封 §6: XY0-2 と XY0-3 が両方当たりなら次の便の候補を示す
    cond = j[u"XY0-2"][0] and j[u"XY0-3"][0]
    shown = u"人間に示す次の便の候補(封 §6。XY0-2 と XY0-3 が両方当たりなので示す)" in sec5
    if cond != shown:
        out.append(u"封 §6 の決め(XY0-2 と XY0-3 が両方当たりなら次の便の候補を示す)と文書 §5 が合わない")
    if cond:
        s6 = section(c.seal, u"## §6 ", u"## §7 ")
        i6 = s6.index(u"(i) ")
        seg = s6[i6:s6.index(u"\n", i6)].strip()
        if seg not in sec5.replace(u"(0 USD)", u""):                # 文書は (i) の後に「(0 USD)」を足している(封の字はそれ以外同じ)
            out.append(u"§5 の次の便の候補 (i)(ii) が封 §6 の字と違う")
    if not cond and u"外れ方" not in sec5:
        out.append(u"外れたのに外れ方・人間に返す道が §5 に無い")
    return out


# ======================================================================================================
# d 文書の数・主な主張の文
def doc_rate_rows(rec):
    return [(d[K_SSTAGE]["PK"]["U"], d[K_SROWS]) for d in rec[u"書類"] if d[K_SROWS] > 0]


def doc_stats(rec):
    u"""書類ごとの率の最小・中央・最大・しきい値ごとの本数・W1 の在る書類と最大(分数で)。"""
    fr = sorted(Fraction(u, n) for u, n in doc_rate_rows(rec))
    mid = fr[len(fr) // 2] if len(fr) % 2 else (fr[len(fr) // 2 - 1] + fr[len(fr) // 2]) / 2
    cnt = [sum(1 for u, n in doc_rate_rows(rec) if 100 * u >= t * n) for t in THRESHOLDS]
    w1 = [d[K_SSTAGE]["PK"]["W1"] for d in rec[u"書類"]]
    return fr[0], mid, fr[-1], cnt, sum(1 for v in w1 if v > 0), max(w1)


def fpct(fr):
    return pct(fr.numerator, fr.denominator)


def tbl_line(label, cl, rows):
    return u"| %s | %s |" % (label, u" | ".join(u"%d(%s%%)" % (cl[k], pct(cl[k], rows)) for k in CLASSES))


def expected_lines(c):
    rec = c.rec
    s = rec[AGG]
    S, B = s[K_SSTAGE], s[K_BSTAGE]
    out = [tbl_line(u"段 P(鍵は行の字)", S["P"], s[K_SROWS]), tbl_line(u"段 PK(鍵は行の種類と行の字)", S["PK"], s[K_SROWS]), tbl_line(u"段 C(段 PK が空なら標準の表へ)", S["C"], s[K_SROWS]),
           tbl_line(u"段 P", B["P"], s[K_BROWS]), tbl_line(u"段 PK", B["PK"], s[K_BROWS])]
    return out


def expected_fragments(c):
    rec = c.rec
    s = rec[AGG]
    S, B, F = s[K_SSTAGE], s[K_BSTAGE], s[K_FALLC]
    rs, rb = s[K_SROWS], s[K_BROWS]
    pk, p, cc = S["PK"], S["P"], S["C"]
    j = judge(rec)
    hits = sum(1 for v in j.values() if v[0])
    lo, mid, hi, cnt, w1docs, w1max = doc_stats(rec)
    n95 = cnt[3]
    bs = collections.OrderedDict((k, B["PK"][k] - pk[k]) for k in CLASSES)           # 集まり B から集まり S を引いた 4543 行
    brows = sum(bs.values())
    left = pk["A"] + pk["W2"] + pk["N"]
    leftc = cc["A"] + cc["W2"] + cc["N"]
    f = []
    f.append(u"段 PK・集まり S の U の率が 95%% 以上の書類は %d 本のうち %d 本だけだった(予測は 10 本以上 40 本以下)" % (PAIRS, n95))
    f.append(u"行の合計では %s%% が決まる" % pct(pk["U"], rs))
    f.append(u"判定した %d 本は 当たり %d・外れ %d。" % (len(j), hits, len(j) - hits))
    f.append(u"今年の側 %d 本・組 %d・除いた今年の書類 %d(前の年の側に相手が無い)。集まり S(標準の計算書の行)は %d 本で %d 行・集まり B(1 行に要素が 1 種類の行の全部)は %d 行。集まり S の行が 1 行以上在る書類は %d。" % (
        rec[u"材料"][u"今年の側の書類の本数"], rec[u"材料"][u"組の数"], rec[u"材料"][u"除いた今年の書類の数"], PAIRS, rs, rb, s[K_NONEMPTY]))
    f.append(u"段 PK・集まり S で %d 行(%d 本の書類に在る)。集まり B では %d 行" % (pk["W1"], w1docs, B["PK"]["W1"]))
    f.append(u"U は減らず増えた(%d → %d)。N は %d → %d に増えた(行の種類を鍵に足すと当たらなくなった行が %d 行)" % (p["U"], pk["U"], p["N"], pk["N"], pk["N"] - p["N"]))
    f.append(u"下書きがそのまま通す行(U + W1)は %d 行で、そのうち W1 は %d 行(%s%%)。行の全部を分母にしても %d/%d(%s%%)。" % (pk["U"] + pk["W1"], pk["W1"], pct(pk["W1"], pk["U"] + pk["W1"]), pk["W1"], rs, pct(pk["W1"], rs)))
    f.append(u"集まり B から集まり S を引いた %d 行(標準の計算書の行でない側)" % brows)
    f.append(u"集まり S(%d 行)の段ごとの類:" % rs)
    f.append(u"集まり B(%d 行)の段ごとの類:" % rb)
    f.append(u"段 PK: U %d(%s%%)・A %d・W1 %d(%s%%)・W2 %d・N %d(%s%%)。" % (bs["U"], pct(bs["U"], brows), bs["A"], bs["W1"], pct(bs["W1"], brows), bs["W2"], bs["N"], pct(bs["N"], brows)))
    f.append(u"黙って違う行は、こちらの側で率が高い。")
    f.append(u"段 C で標準の表へ落ちた集まり S の行は %d 行(段 PK の N と同じ数)。その類は U %d(%s%%)・A %d・W1 %d・W2 %d・N %d。" % (s[K_FALL], F["U"], pct(F["U"], s[K_FALL]), F["A"], F["W1"], F["W2"], F["N"]))
    f.append(u"標準の表へ落とすと、N だった %d 行のうち %d 行が決まるが、黙って違う行も %d 行増える。" % (pk["N"], F["U"], F["W1"]))
    f.append(u"書類ごとの段 PK・集まり S の U の率(%d 本): 最小 %s%%・中央 %s%%・最大 %s%%。80%% 以上が %d 本・85%% 以上が %d 本・90%% 以上が %d 本・95%% 以上が %d 本・98%% 以上は %d 本。" % (
        PAIRS, fpct(lo), fpct(mid), fpct(hi), cnt[0], cnt[1], cnt[2], cnt[3], cnt[4]))
    f.append(u"段 PK・集まり S の W1 が 1 行以上在る書類は %d 本(1 本の中の最大は %d 行)。" % (w1docs, w1max))
    f.append(u"候補が 2 つ以上残る行(A)が %d → %d に減り、U が %d → %d に増える。" % (p["A"], pk["A"], p["U"], pk["U"]))
    f.append(u"段 PK・集まり S で A %d + W2 %d + N %d = %d 行(%s%%)。段 C まで使うと A %d + W2 %d + N %d = %d 行(%s%%)。" % (
        pk["A"], pk["W2"], pk["N"], left, pct(left, rs), cc["A"], cc["W2"], cc["N"], leftc, pct(leftc, rs)))
    f.append(u"便 XG1(行の字と標準の表だけ。67 本)で 1 つに決まった行は %.1f%% だった。この便の段 PK は %s%%・段 C は %s%%。" % (xg1_pct(c), pct(pk["U"], rs), pct(cc["U"], rs)))
    f.append(u"書類の集まりが違う(67 本と %d 本)ので" % PAIRS)
    f.append(u"要素が 1 つに決まり正しかった行は %s%%・1 つに決まって違った行は %s%%・前の年に無かった行は %s%% だった。" % (pct(pk["U"], rs), pct(pk["W1"], rs), pct(pk["N"], rs)))
    f.append(u"U の率が 95%% 以上の書類は %d 本のうち %d 本だった。" % (PAIRS, n95))
    f.append(u"要素を選ぶ仕事の 9 割近くは前の年の提出書類から機械で写せて、写したものが黙って違うことは標準の計算書の行では 1000 行に 1 行ほどだった。残る 1 割前後")
    f.append(u"公開済みの %d 組で" % PAIRS)
    return f


def sanity_problems(c):
    u"""文書の言い切りの向き(増える・減る・9 割近く・1000 行に 1 行ほど・1 割前後・ほぼ無い)が記録の数に合う。"""
    s = c.rec[AGG]
    S, B, F = s[K_SSTAGE], s[K_BSTAGE], s[K_FALLC]
    rs, rb = s[K_SROWS], s[K_BROWS]
    pk, p, cc = S["PK"], S["P"], S["C"]
    out = []
    if not (pk["U"] > p["U"] and pk["A"] < p["A"] and pk["N"] > p["N"]):
        out.append(u"文書の「U は増え・A は減り・N は増えた」が記録と合わない")
    if not (pk["N"] > p["N"] and pk["N"] - p["N"] == 42):
        out.append(u"文書の「当たらなくなった行が 42 行」が記録と合わない")
    if not (85 * rs <= 100 * pk["U"] < 90 * rs):
        out.append(u"文書の「9 割近く」が記録と合わない(段 PK の U が 85% 以上 90% 未満でない)")
    if pk["W1"] == 0 or not (900 * pk["W1"] <= rs <= 1100 * pk["W1"]):
        out.append(u"文書の「1000 行に 1 行ほど」が記録と合わない")
    left, leftc = pk["A"] + pk["W2"] + pk["N"], cc["A"] + cc["W2"] + cc["N"]
    if not (8 * rs <= 100 * leftc and 100 * left <= 13 * rs):
        out.append(u"文書の「1 割前後」が記録と合わない")
    n95 = doc_stats(c.rec)[3][3]
    if not (10 * n95 <= PAIRS):
        out.append(u"文書の「ほぼ無い」(95% 以上の書類)が記録と合わない")
    if not (B["PK"]["W1"] - pk["W1"]) * rs > pk["W1"] * (rb - rs):
        out.append(u"文書の「黙って違う行は、標準の計算書の行でない側で率が高い」が記録と合わない")
    if not (F["W1"] > 0 and cc["W1"] - pk["W1"] == F["W1"] and F["U"] < pk["N"]):
        out.append(u"文書の「標準の表へ落とすと決まるが、黙って違う行も増える」が記録と合わない")
    if s[K_FALL] != pk["N"] or 100 * F["U"] * 1 <= 0:
        out.append(u"落ちた行の数が段 PK の N と違う")
    if not (100 * cc["U"] > 100 * pk["U"] and cc["A"] > pk["A"]):
        out.append(u"段 C の U が段 PK の U より増えていない")
    if not (Fraction(100 * B["PK"]["U"], rb) < Fraction(100 * pk["U"], rs)):
        out.append(u"文書の「B が S より低い」が記録と合わない")
    return out


def fragment_problems(c):
    out = []
    lines = c.doc.splitlines()
    for want in expected_lines(c):
        if want not in lines:
            out.append(u"文書に記録から組んだ行が無い: %s" % want[:40])
    for frag in expected_fragments(c):
        if frag not in c.doc:
            out.append(u"文書に記録から組んだ字が無い: %s" % frag[:40])
    return out


def derived_numbers(c):
    rec = c.rec
    out = set()
    WG.ints_in(rec[AGG], out)
    WG.ints_in(rec[PRED_KEY], out)
    lo, mid, hi, cnt, w1docs, w1max = doc_stats(rec)
    for fr in (lo, mid, hi):
        out.add(fpct(fr))
    out |= set(str(v) for v in cnt)
    out |= set([str(w1docs), str(w1max), str(PAIRS), str(DOC_COUNT), str(DROPPED), u"%.1f" % xg1_pct(c)])
    s = rec[AGG]
    S, B = s[K_SSTAGE], s[K_BSTAGE]
    pk, p, cc = S["PK"], S["P"], S["C"]
    rs = s[K_SROWS]
    left, leftc = pk["A"] + pk["W2"] + pk["N"], cc["A"] + cc["W2"] + cc["N"]
    out |= set([str(left), str(leftc), pct(left, rs), pct(leftc, rs), str(pk["N"] - p["N"]), str(pk["U"] + pk["W1"]), pct(pk["W1"], pk["U"] + pk["W1"])])
    brows = B["PK"]["U"] + B["PK"]["A"] + B["PK"]["W1"] + B["PK"]["W2"] + B["PK"]["N"] - rs
    out.add(str(brows))
    for k in CLASSES:
        out.add(str(B["PK"][k] - pk[k]))
        out.add(pct(B["PK"][k] - pk[k], brows))
    for st in ("P", "PK", "C"):
        for k in CLASSES:
            out.add(pct(S[st][k], rs))
    for st in ("P", "PK"):
        for k in CLASSES:
            out.add(pct(B[st][k], s[K_BROWS]))
    for k in CLASSES:
        out.add(pct(s[K_FALLC][k], s[K_FALL]))
    out.add(u"%.1f" % abs(rec[PRED_KEY][PK_KEYS[7]][u"集まり B から集まり S を引いた差(ポイント)"]))
    out |= set(STRUCTURAL) | RESIDUAL_OK
    return out


def doc_number_problems(c):
    allowed = derived_numbers(c)
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        for tok in doc_number_tokens(re.sub(r"^\d+\. ", u"", ln)):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"文書の %d 行目の数 %s が記録から組んだ数の外: %s" % (i, tok, ln[:30]))
    return out


def residual_problems(c):
    u"""記録から組んだ字(行・断片・§1 の表の行・§3 の導いた字)を文書から除いた残りの数は、字で留めた境の数(RESIDUAL_OK)だけ。"""
    rest = c.doc
    for frag in expected_fragments(c) + expected_lines(c):
        rest = rest.replace(frag, u" ")
    rows = [ln for ln in rest.splitlines() if re.match(r"^\| XY0-\d", ln)]
    for ln in rows:
        rest = rest.replace(ln, u" ")
    out = []
    for i, ln in enumerate(rest.splitlines(), 1):
        for tok in doc_number_tokens(ln):
            t = tok.replace(u",", u"")
            if t not in RESIDUAL_OK and t not in STRUCTURAL:
                out.append(u"記録から組んだ字を除いた残りの数 %s(%s)が留めた境の数の外" % (t, ln[:24]))
    return out


def sec3_problems(c):
    u"""§3 は記録から導く読みの節(標題は「記録の数から。記録に欄の無い読みは書かない」)。字は導いた断片・数は記録から。"""
    s = section(c.doc, u"## §3 ", u"## §4 ")
    out = []
    if u"記録に欄の無い読みは書かない" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録に欄の無い読みは書かない」でない")
    frags = expected_fragments(c)
    keys = (u"候補が 2 つ以上残る行(A)が", u"A %d + W2" % c.rec[AGG][K_SSTAGE]["PK"]["A"], u"便 XG1(行の字", u"書類の集まりが違う")
    for k in keys:
        if not any(k in fr for fr in frags):
            out.append(u"§3 の鍵の字の断片が組めない: %s" % k)
        if k not in s:
            out.append(u"§3 に字が無い: %s" % k)
    for p in (u"同じ行の字が貸借対照表と損益計算書で別の要素を指す、という重なりを行の種類が分けている、と読める", u"人か別の手段が見る行は、標準の計算書の行の 1 割前後"):
        if p not in s:
            out.append(u"§3 に字が無い: %s" % p)
    keep = s
    for fr in frags:
        keep = keep.replace(fr, u" ")
    left = re.sub(r"`[^`]*`", u" ", keep)
    if re.search(r"\d{3}|%|％", left):
        out.append(u"§3 の導いた字の外に 3 桁以上の数か % が在る")
    return out


def affirm_problems(c):
    u"""「作れる」「専用の道具が要らない」「人が書ける」「AI が書ける」「検査に通る」は、言えないことの引用(「…」の中)にしか無い。引用の在る行には「言えない」か「読まない」が在る。"""
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        if QUOTED.search(ln) and not any(w in ln for w in (u"言えない", u"読まない", u"示していない")):
            out.append(u"文書の %d 行目が引用の主張を否定の外で書いている" % i)
        rest = QUOTED.sub(u"", ln)
        for w in AFFIRM_WORDS:
            if re.search(w, rest):
                out.append(u"文書の %d 行目に引用の外の字: %s" % (i, w))
    return out


def phrase_problems(c):
    return [u"文書に要点の字が無い: %s" % p for p in PHRASES if p not in c.doc]


def head_problems(c):
    head = c.doc.split(u"## §1")[0]
    return [u"文書の頭(§1 の前)に無い: %s" % p for p in HEAD_PHRASES if p not in head]


def forbidden_problems(c):
    out = [u"文書に禁止語: %s" % w for w in FORBIDDEN_WORDS if w in c.doc]
    scan = re.sub(r"\b(?=[0-9]*[a-f])[0-9a-f]{8}\b", u" ", c.doc)
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
    if not set(re.findall(r"\b(?=[0-9]*[a-f])[0-9a-f]{8}\b", c.doc)) <= set(DOC_COMMITS):
        out.append(u"文書が知らない commit の字を書いている")
    return out


CHECKS = collections.OrderedDict([
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", record_clean_problems), (u"bound", bound_problems),
    (u"verdict", verdict_problems), (u"numbers", doc_number_problems), (u"frag", fragment_problems), (u"resid", residual_problems), (u"sanity", sanity_problems),
    (u"sec3", sec3_problems), (u"affirm", affirm_problems), (u"phrases", phrase_problems), (u"head", head_problems), (u"forbidden", forbidden_problems), (u"commits", doc_commit_problems)])


# ======================================================================================================
def blob_problems(root, prefix, at):
    return WG.blob_problems(root, prefix, at)


def commit_problems(root=REPO):
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は ce70f71f・script は 150c7fe6・封の門は 150c7fe6 と 4591db32(直し)・記録は 4591db32。"""
    out = []
    for rel, want in HISTORY.items():
        r = subprocess.run(["git", "-C", root, "log", "--format=%H", "--reverse", "--", PREFIX + rel], stdout=subprocess.PIPE, universal_newlines=True)
        got = [x for x in r.stdout.split() if x]
        if len(got) != len(want) or any(not g.startswith(w) for g, w in zip(got, want)):
            out.append(u"%s の履歴が文書の書く commit %s と違う" % (rel, u"・".join(want)))
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
    rc, last = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + SCRIPT_REL)
    if not last.startswith(SCRIPT_COMMIT_SHORT):
        out.append(u"script の最後の commit が %s でない(記録を書いた後に変わった)" % SCRIPT_COMMIT_SHORT)
    rc, last = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + SEAL_GATE_REL)
    if not last.startswith(RECORD_COMMIT_SHORT):
        out.append(u"封の門の最後の commit が %s でない(結果の便で変わった)" % RECORD_COMMIT_SHORT)
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
(変異を実行する前に書いた予測。右 = 赤になるべき検査。「整合」= 書類ごとの数から集計・予測の欄を作り直し、recount は緑のまま当たり外れだけが変わる)
M1  記録の sha256 の写しを違う値に                                                       -> sha
M2  記録の「この script の sha256」を 1 字替える                                         -> sha
M3  記録の限界の欄の 1 行を消す                                                          -> sha
M4  記録の封の commit の欄を 1 字替える                                                  -> sha
M5  便 XG1 の記録の sha256 の写しを違う値に                                              -> sha
M6  書類 10 の集まり S の段 PK の U を 1 増やす(群・率は直さない)                          -> recount
M7  集計の集まり S の段 PK の W1 を 1 増やす(書類ごとは直さない)                            -> recount
M8  書類 10 の段 C の U を 1 減らす(PK + 落ちた行の関係が崩れる)                            -> recount
M9  書類 10 の集まり B の段 PK の U を、集まり S の U より小さくする(S ⊆ B が崩れる)         -> recount
M10 材料の組の数 63 → 64                                                                 -> recount
M11 書類 10 の U の率の欄を 0.1 ずらす                                                    -> recount
M12 予測の欄 XY0-2 の行を 1 増やす                                                        -> recount
M13 予測の欄 XY0-7 の書類を 1 増やす                                                      -> recount
M14 集計の落ちた行の数を 1 増やす                                                         -> recount
M15 書類 10 の段 PK の N を段 P の N より小さくする(PK は P を細かくする、が崩れる)           -> recount
M16 記録に docid の欄を足す                                                              -> clean
M17 記録に EDINET コードの形の字を足す                                                    -> clean
M18 記録に日付の形の字を足す                                                              -> clean
M19 封の写しから XY0-2 の境の字を消す                                                     -> bound
M20 封の写しから自己点検の「W1 が 5% を超えても同じ」を消す                                 -> bound
M21 封の写しから §6 の「XY0-2 と XY0-3 が両方当たりなら…」を消す                          -> bound
M22 封の写しから §7 の「測るのは要素の名だけ」を消す                                       -> bound
M23 文書の XY0-7 の判定「外れ」を「当たり」に                                              -> verdict
M24 文書の XY0-2 の判定「当たり」を「外れ」に                                              -> verdict
M25 文書の件数の行 当たり 6・外れ 1 → 当たり 7・外れ 0                                    -> verdict
M26 頭の「判定した 7 本は 当たり 6・外れ 1」を 当たり 7・外れ 0 に                          -> verdict
M27 文書の XY0-2 のセル 14021/16063(87.3%) → (87.4%)                                    -> verdict
M28 文書の XY0-1 の予測の字「72% 以上 88% 以下」を「72% 以上 89% 以下」に                  -> verdict
M29 §5 の「人間に示す次の便の候補」の見出しの字を消す                                      -> verdict・phrases
M30 §5 の次の便の候補の「(i) 前の年の書類から」を替える                                    -> verdict
M31 自己点検の「どれも発火しない」を「1 つ発火している」に                                  -> verdict
M32 自己点検の 3 条件の「N が 30% を超える」を「N が 20% を超える」に                       -> verdict
M33 XY0-7 の行から「外れ」を消して頭の「**XY0-7 は外れ。**」も消す                          -> verdict
M34 XY0-2 の行の「(主)」を消す                                                           -> verdict
M35 XY0-6 のセル「差 −1.2 ポイント」→「差 −1.3 ポイント」                                 -> verdict
M36 整合: XY0-1 が 72% 未満になるよう段 P の U を減らして A を増やす(下に外れ)              -> verdict
M37 整合: 段 PK の U を増やし 95% を超える(上に外れ。XY0-2)                               -> verdict
M38 整合: 段 PK の W1 を 1.5% 超にして XY0-3 が外れ                                        -> verdict
M39 整合: 段 PK の N を 12% 超にして XY0-4 が外れ                                           -> verdict
M40 整合: 段 C の W1 を 2.5% 超にして XY0-5 が外れ                                          -> verdict
M41 整合: 集まり B の U を減らして S より 5 ポイントを超えて低くして XY0-6 が外れ             -> verdict
M42 整合: 95% 以上の書類を 10 本にして XY0-7 が当たり                                      -> verdict
M43 整合: 段 PK の U を 98% 超にして自己点検が発火                                         -> verdict
M44 整合: 段 PK の W1 を 5% 超にして自己点検が発火                                         -> verdict
M45 整合: 段 PK の N を 30% 超にして自己点検が発火                                         -> verdict
M46 文書の「63 本のうち 1 本だけだった」を「63 本のうち 2 本だけだった」に                  -> frag・numbers(外れ: numbers は 2 が構造の数で黙る)
M47 文書の「行の合計では 87.3% が決まる」を 87.4% に                                      -> frag・numbers
M48 文書の「U は減らず増えた」を「U は減り増えた」に                                        -> frag
M49 文書の「A が 3344 → 1339 に減り」を「A が 3344 → 1339 に増え」に                       -> frag
M50 文書の「N は 627 → 669 に増えた」を「N は 627 → 669 に減った」に                       -> frag
M51 文書の「黙って違う行は、こちらの側で率が高い」を「率が低い」に                          -> frag
M52 文書の「9 割近く」を「5 割近く」に                                                    -> frag
M53 文書の「1000 行に 1 行ほど」を「100 行に 1 行ほど」に                                  -> frag・resid
M54 文書の「残る 1 割前後」を「残る 3 割前後」に                                           -> frag
M55 文書の「人か別の手段が見る行は、標準の計算書の行の 1 割前後」を「5 割前後」に            -> sec3
M56 文書の「最小 70.4%」を 70.5% に                                                       -> frag・numbers
M57 文書の「95% 以上が 1 本」を「95% 以上が 2 本」に                                       -> frag
M58 文書の「W1 が 1 行以上在る書類は 11 本」を 12 本に                                      -> frag・numbers
M59 文書の「N だった 669 行のうち 532 行が決まる」を 533 行に                              -> frag・numbers
M60 文書の「前の年に無かった行は 4.2%」を 4.3% に                                         -> frag・numbers
M61 文書の「便 XG1(…)で 1 つに決まった行は 80.4%」を 80.5% に                            -> frag・numbers
M62 文書の §2 の段 PK の行 14021(87.3%) を 14022(87.3%) に                              -> frag・numbers
M63 文書の「2026 行(12.6%)」を 2027 行に                                                  -> frag・numbers
M64 文書に 9999 の言い切りを足す                                                          -> numbers
M65 文書に「48%」の言い切りを足す                                                         -> resid
M66 §3 に 3 桁の数を足した行                                                              -> sec3
M67 §3 の「便 XG1(」の行を消す                                                           -> sec3
M68 文書に「XBRL を作れる。」を引用の外で足す                                              -> affirm
M69 文書に「専用の道具が要らない。」を足す                                                 -> affirm
M70 文書に「AI が書ける。」を足す                                                         -> affirm
M71 文書に「人が書ける。」を足す                                                          -> affirm
M72 文書に「EDINET の検査に通る。」を足す                                                  -> affirm
M73 引用の行から「言えない」「読まない」を全部消す                                          -> affirm
M74 §5 の「言えないこと」を消す                                                           -> phrases
M75 頭の限界「前の年の XBRL が在る会社にしか使えない」を消す                                -> head
M76 頭の限界「63 組は無作為ではない」を消す                                                -> head
M77 頭の限界「測るのは要素の名だけ」を消す                                                  -> head
M78 頭の限界「前の年に無かった行(N)は、道具がいちばん要る所」を消す                          -> head
M79 頭の「(封 §0 の申告)」の字を消す                                                      -> head
M80 頭の「先に負けと限界を書く」を消す                                                     -> head
M81 頭の「LLM の席は呼んでいない」を消す                                                   -> head
M82 頭の「この便の U は「上の限り」に近い読み」を消す                                       -> head
M83 文書に「保証」を足す                                                                  -> forbidden
M84 文書に docID の形を足す                                                               -> forbidden
M85 文書の commit の字 4591db32 を 1 字替える                                              -> commits
M86 文書に知らない commit の字を足す                                                       -> commits
M87 整合: 段 PK の U を増やし N を減らして「減らず増えた」の向きは保つが当たり外れが変わる(95% 超)   -> verdict
M88 整合: 段 P の U を段 PK の U より大きくして「増えた」の向きが崩れる(XY0-1 は当たりのまま)     -> sanity
M89 整合: 段 PK の W1 を 100 倍近くにして「1000 行に 1 行ほど」が崩れる(XY0-3 は外れ)           -> sanity・verdict
M90 整合: 95% 以上の書類を 0 本にして「ほぼ無い」「1 本」が崩れる                              -> frag・verdict

M91 文書の「黙って違う行も 4 行増える」を「黙って違う行も 4 行減る」に                        -> frag
M92 文書の「(予測は 10 本以上 40 本以下)」を「20 本以上 40 本以下」に                           -> frag
M93 文書の「「1 本をまるごと済ませる」ものではない」を消す                                     -> phrases
M94 文書の「差をそのまま「前の年の表の効き」とは読まない」を「前の年の表の効きと読む」に           -> phrases

(実行した後で予測と違った所は、この下に「実行後の追記」として日付つきで書く。予測の行は書き換えない)

実行後の追記(2026-11-22。1 回目の実行で、予測と違った所。変異の表は予測どおりに赤の検査を数えたが、次の 5 点で予測の行と表が違う):
- M46・M58: 予測は numbers も赤と書いたが、1 本ずつ見ると numbers は黙る(2 は構造の数・12 は記録の数と留めた境の数に在る)。表は frag だけを数える(書き換えは frag が記録から組んだ字と照らして赤にする)。
- M89: 予測は sanity・verdict と書いたが、W1 を 100 行に 1 行にしても XY0-3(1.5% 以下)は当たりのままなので verdict は緑。表は sanity だけを数える。
- M87: 作らなかった(M43 と M88 で足りるため欠番)。M33 は 2 つの書き換えを 1 つの変異に束ねた。
- 1 回目の実行で、整合の変異の作り(m_* 関数)が S ⊆ B・段 C = 段 PK + 落ちた行・段 PK の N は段 P の N 以上、の関係を崩して recount が赤になった。変異の側を直した(門は直していない)。
"""


def doc_at(rec, n):
    return rec[u"書類"][n - 1]


def rebuild(rec):
    u"""書類ごとの数から集計と予測の欄を作り直す(整合の変異用)。"""
    docs = rec[u"書類"]
    new = totals(docs)
    for k, v in new.items():
        rec[AGG][k] = copy.deepcopy(v)
    rec[PRED_KEY] = pred_expected(rec)


def recompute_c(d):
    u"""段 C を「段 PK + 落ちた行の類」から作り直す(関係 C = PK + 落ちた行を保つ)。"""
    pk, fc = d[K_SSTAGE]["PK"], d[K_FALLC]
    for k in (u"U", u"A", u"W1", u"W2"):
        d[K_SSTAGE]["C"][k] = pk[k] + fc[k]
    d[K_SSTAGE]["C"]["N"] = fc["N"]
    d[K_FALL] = sum(fc.values())
    fix_rate(d)


def fix_rate(d):
    d[K_RATE] = float(pct(d[K_SSTAGE]["PK"]["U"], d[K_SROWS])) if d[K_SROWS] > 0 else d[K_RATE]


def move(d, stage, a, b, n):
    u"""集まり S の段 stage で類 a から類 b へ n 行移す。集まり B の同じ段にも同じだけ移す(S ⊆ B を保つ)。PK への N の移しは落ちた行の N も増やす。"""
    d[K_SSTAGE][stage][a] -= n
    d[K_SSTAGE][stage][b] += n
    d[K_BSTAGE][stage][a] -= n
    d[K_BSTAGE][stage][b] += n
    if stage == "PK" and b == "N":
        d[K_FALLC]["N"] += n
    if stage == "PK" and a == "N":
        left = n
        for k in (u"N", u"U", u"A", u"W1", u"W2"):
            t = min(left, d[K_FALLC][k])
            d[K_FALLC][k] -= t
            left -= t
    if stage == "PK":
        recompute_c(d)


def m_p_low(c):
    u"""段 P の U を 72% 未満にする(整合)。U の一部を A へ(全部の書類)。"""
    for d in c.rec[u"書類"]:
        move(d, "P", "U", "A", d[K_SSTAGE]["P"]["U"] // 8)
    rebuild(c.rec)


def set_pk_u_high(c):
    u"""段 PK の U を 95% 超にする(整合。A・W1・W2 を U へ移す。N は段 P の N 以上でなければならないので動かさない)。"""
    for d in c.rec[u"書類"]:
        for k in (u"A", u"W1", u"W2"):
            move(d, "PK", k, "U", d[K_SSTAGE]["PK"][k])
    rebuild(c.rec)


def m_u98(c):
    u"""段 PK の U を 98% 超にする(整合。段 P の N を U へ移したうえで、段 PK の N も U へ移す)。"""
    set_pk_u_high(c)
    for d in c.rec[u"書類"]:
        move(d, "P", "N", "U", d[K_SSTAGE]["P"]["N"])
        move(d, "PK", "N", "U", d[K_SSTAGE]["PK"]["N"])
    rebuild(c.rec)


def m_pk_w1_high(c):
    u"""段 PK の W1 を 1.5% 超にする(整合。U から移す)。"""
    for d in c.rec[u"書類"]:
        move(d, "PK", "U", "W1", d[K_SROWS] // 40)
    rebuild(c.rec)


def m_suspect_w1(c):
    u"""段 PK の W1 を 5% 超にする(整合)。"""
    for d in c.rec[u"書類"]:
        move(d, "PK", "U", "W1", d[K_SROWS] // 12)
    rebuild(c.rec)


def m_pk_n_high(c):
    u"""段 PK の N を 12% 超にする(整合。U から移す)。"""
    for d in c.rec[u"書類"]:
        move(d, "PK", "U", "N", d[K_SROWS] // 6)
    rebuild(c.rec)


def m_suspect_n(c):
    u"""段 PK の N を 30% 超にする(整合)。"""
    for d in c.rec[u"書類"]:
        move(d, "PK", "U", "N", d[K_SROWS] // 3)
    rebuild(c.rec)


def m_c_w1_high(c):
    u"""段 C の W1 を 2.5% 超にする(整合。落ちた行の U を W1 へ。段 PK は変わらない)。"""
    for d in c.rec[u"書類"]:
        n = d[K_FALLC]["U"]
        d[K_FALLC]["U"] -= n
        d[K_FALLC]["W1"] += n
        recompute_c(d)
    rebuild(c.rec)


def m_b_low(c):
    u"""集まり B の段 PK の U を、集まり S の U まで減らして A へ(整合。B の率が S より 5 ポイント超低くなる)。"""
    for d in c.rec[u"書類"]:
        spare = d[K_BSTAGE]["PK"]["U"] - d[K_SSTAGE]["PK"]["U"]
        d[K_BSTAGE]["PK"]["U"] -= spare
        d[K_BSTAGE]["PK"]["A"] += spare
    rebuild(c.rec)


def m_u95_ten(c):
    u"""95% 以上の書類を 10 本にする(整合。足りない分は A を U へ移して 95% に届かせる)。"""
    docs = c.rec[u"書類"]
    have = sum(1 for d in docs if 100 * d[K_SSTAGE]["PK"]["U"] >= 95 * d[K_SROWS])
    for d in docs:
        if have >= 10:
            break
        if 100 * d[K_SSTAGE]["PK"]["U"] >= 95 * d[K_SROWS]:
            continue
        need = -(-(95 * d[K_SROWS]) // 100) - d[K_SSTAGE]["PK"]["U"]
        n = min(need, d[K_SSTAGE]["PK"]["A"])
        move(d, "PK", "A", "U", n)
        if 100 * d[K_SSTAGE]["PK"]["U"] >= 95 * d[K_SROWS]:
            have += 1
    rebuild(c.rec)


def m_u95_zero(c):
    u"""95% 以上の書類を 0 本にする(整合)。その書類の U の 1 割を A へ。"""
    for d in c.rec[u"書類"]:
        if 100 * d[K_SSTAGE]["PK"]["U"] >= 95 * d[K_SROWS]:
            move(d, "PK", "U", "A", d[K_SROWS] // 10)
    rebuild(c.rec)


def m_p_over_pk(c):
    u"""段 PK の U を減らして段 P の U より小さくする(整合)。「増えた」の向きが崩れる。"""
    for d in c.rec[u"書類"]:
        move(d, "PK", "U", "A", d[K_SSTAGE]["PK"]["U"] // 4)
    rebuild(c.rec)


def m_w1_many(c):
    u"""段 PK の W1 を 100 行に 1 行ほどにする(整合)。"""
    for d in c.rec[u"書類"]:
        move(d, "PK", "U", "W1", d[K_SROWS] // 100)
    rebuild(c.rec)


def m_b_not_superset(c):
    d = doc_at(c.rec, 10)
    d[K_BSTAGE]["PK"]["U"] = d[K_SSTAGE]["PK"]["U"] - 1


def m_drop_quote_negation(c):
    lines = []
    for ln in c.doc.splitlines():
        if QUOTED.search(ln):
            for w in (u"言えないこと", u"言えない", u"読まない", u"示していない"):
                ln = ln.replace(w, u"X")
        lines.append(ln)
    c.doc = u"\n".join(lines)


def m_drop_seal(c, phrase):
    assert phrase in c.seal, phrase
    c.seal = c.seal.replace(phrase, u"X")


def m_drop_line(c, key):
    lines = [ln for ln in c.doc.splitlines() if key not in ln]
    c.doc = u"\n".join(lines)


MUTATIONS = (
    (u"M1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"M3 記録の限界の欄の 1 行を消す", lambda c: c.rec.__setitem__(u"限界", c.rec[u"限界"][1:]), (u"sha",)),
    (u"M4 記録の封の commit の欄を 1 字替える", lambda c: c.rec.__setitem__(u"封の commit", u"0" + c.rec[u"封の commit"][1:]), (u"sha",)),
    (u"M5 便 XG1 の記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(XG1_RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M6 書類 10 の集まり S の段 PK の U を 1 増やす", lambda c: doc_at(c.rec, 10)[K_SSTAGE]["PK"].__setitem__("U", doc_at(c.rec, 10)[K_SSTAGE]["PK"]["U"] + 1), (u"recount",)),
    (u"M7 集計の集まり S の段 PK の W1 を 1 増やす", lambda c: c.rec[AGG][K_SSTAGE]["PK"].__setitem__("W1", c.rec[AGG][K_SSTAGE]["PK"]["W1"] + 1), (u"recount",)),
    (u"M8 書類 10 の段 C の U を 1 減らす", lambda c: doc_at(c.rec, 10)[K_SSTAGE]["C"].__setitem__("U", doc_at(c.rec, 10)[K_SSTAGE]["C"]["U"] - 1), (u"recount",)),
    (u"M9 書類 10 の集まり B の段 PK の U を S の U より小さくする", m_b_not_superset, (u"recount",)),
    (u"M10 材料の組の数を 64 に", lambda c: c.rec[u"材料"].__setitem__(u"組の数", 64), (u"recount",)),
    (u"M11 書類 10 の U の率の欄を 0.1 ずらす", lambda c: doc_at(c.rec, 10).__setitem__(K_RATE, doc_at(c.rec, 10)[K_RATE] + 0.1), (u"recount",)),
    (u"M12 予測の欄 XY0-2 の行を 1 増やす", lambda c: c.rec[PRED_KEY][PK_KEYS[1]].__setitem__(u"行", c.rec[PRED_KEY][PK_KEYS[1]][u"行"] + 1), (u"recount",)),
    (u"M13 予測の欄 XY0-7 の書類を 1 増やす", lambda c: c.rec[PRED_KEY][PK_KEYS[8]].__setitem__(u"書類", c.rec[PRED_KEY][PK_KEYS[8]][u"書類"] + 1), (u"recount",)),
    (u"M14 集計の落ちた行の数を 1 増やす", lambda c: c.rec[AGG].__setitem__(K_FALL, c.rec[AGG][K_FALL] + 1), (u"recount",)),
    (u"M15 書類 10 の段 PK の N を段 P の N より小さくする", lambda c: (doc_at(c.rec, 10)[K_SSTAGE]["PK"].__setitem__("N", doc_at(c.rec, 10)[K_SSTAGE]["P"]["N"] - 1), doc_at(c.rec, 10)[K_SSTAGE]["PK"].__setitem__("U", doc_at(c.rec, 10)[K_SSTAGE]["PK"]["U"] + 1)), (u"recount",)),
    (u"M16 記録に docid の欄を足す", lambda c: c.rec.__setitem__(u"docID", u"S100ABCD"), (u"clean",)),
    (u"M17 記録に EDINET コードの形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"E01234"), (u"clean",)),
    (u"M18 記録に日付の形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"2025-03-31"), (u"clean",)),
    (u"M19 封の写しから XY0-2 の境の字を消す", lambda c: m_drop_seal(c, u"段 PK・集まり S の類 U は 84% 以上 95% 以下"), (u"bound",)),
    (u"M20 封の写しから自己点検の「W1 が 5% を超えても同じ」を消す", lambda c: m_drop_seal(c, u"W1 が 5% を超えても同じ"), (u"bound",)),
    (u"M21 封の写しから §6 の「XY0-2 と XY0-3 が両方当たりなら…」を消す", lambda c: m_drop_seal(c, u"XY0-2 と XY0-3 が両方当たりなら、次の便の候補を人間に示す"), (u"bound",)),
    (u"M22 封の写しから §7 の「測るのは要素の名だけ」を消す", lambda c: m_drop_seal(c, u"測るのは要素の名だけ"), (u"bound",)),
    (u"M23 文書の XY0-7 の判定「外れ」を「当たり」に", lambda c: rep(c, u"| 1/63 | 外れ |", u"| 1/63 | 当たり |"), (u"verdict",)),
    (u"M24 文書の XY0-2 の判定「当たり」を「外れ」に", lambda c: rep(c, u"14021/16063(87.3%) | 当たり |", u"14021/16063(87.3%) | 外れ |"), (u"verdict",)),
    (u"M25 文書の件数の行を 当たり 7・外れ 0 に", lambda c: rep(c, u"- 当たり 6・外れ 1。", u"- 当たり 7・外れ 0。"), (u"verdict",)),
    (u"M26 頭の「判定した 7 本は 当たり 6・外れ 1」を 当たり 7・外れ 0 に", lambda c: rep(c, u"判定した 7 本は 当たり 6・外れ 1。", u"判定した 7 本は 当たり 7・外れ 0。"), (u"verdict",)),
    (u"M27 文書の XY0-2 のセル 87.3% → 87.4%", lambda c: rep(c, u"14021/16063(87.3%) | 当たり |", u"14021/16063(87.4%) | 当たり |"), (u"verdict",)),
    (u"M28 文書の XY0-1 の予測の字を「72% 以上 89% 以下」に", lambda c: rep(c, u"段 P・集まり S の類 U は 72% 以上 88% 以下", u"段 P・集まり S の類 U は 72% 以上 89% 以下"), (u"verdict",)),
    (u"M29 §5 の「人間に示す次の便の候補」を消す", lambda c: rep(c, u"人間に示す次の便の候補", u"X"), (u"verdict", u"phrases")),
    (u"M30 §5 の次の便の候補の「(i) 前の年の書類から」を替える", lambda c: rep(c, u"(i) 前の年の書類から今年の紙の下書き", u"(i) 前の年の書類から今年の紙の清書"), (u"verdict",)),
    (u"M31 自己点検の「どれも発火しない」を「1 つ発火している」に", lambda c: rep(c, u"は、どれも発火しない。", u"は、1 つ発火している。"), (u"verdict",)),
    (u"M32 自己点検の「N が 30% を超える」を 20% に", lambda c: rep(c, u"N が 30% を超える)は、どれも", u"N が 20% を超える)は、どれも"), (u"verdict",)),
    (u"M33 XY0-7 の行の「外れ」と頭の「**XY0-7 は外れ。**」を消す", lambda c: (rep(c, u"| 1/63 | 外れ |", u"| 1/63 | 当たり |"), rep(c, u"**XY0-7 は外れ。**", u"XY0-7")), (u"verdict",)),
    (u"M34 XY0-2 の行の「(主)」を消す", lambda c: rep(c, u"| XY0-2(主) |", u"| XY0-2 |"), (u"verdict",)),
    (u"M35 XY0-6 のセル「差 −1.2 ポイント」を −1.3 に", lambda c: rep(c, u"差 −1.2 ポイント", u"差 −1.3 ポイント"), (u"verdict",)),
    (u"M36 整合: 段 P の U を減らして XY0-1 が 72% 未満", m_p_low, (u"verdict",)),
    (u"M37 整合: 段 PK の U を増やして XY0-2 が 95% 超", set_pk_u_high, (u"verdict",)),
    (u"M38 整合: 段 PK の W1 を 1.5% 超にして XY0-3 が外れ", m_pk_w1_high, (u"verdict",)),
    (u"M39 整合: 段 PK の N を 12% 超にして XY0-4 が外れ", m_pk_n_high, (u"verdict",)),
    (u"M40 整合: 段 C の W1 を 2.5% 超にして XY0-5 が外れ", m_c_w1_high, (u"verdict",)),
    (u"M41 整合: 集まり B の U を減らして XY0-6 が外れ", m_b_low, (u"verdict",)),
    (u"M42 整合: 95% 以上の書類を 10 本にして XY0-7 が当たり", m_u95_ten, (u"verdict",)),
    (u"M43 整合: 段 PK の U を 98% 超にして自己点検が発火", m_u98, (u"verdict",)),
    (u"M44 整合: 段 PK の W1 を 5% 超にして自己点検が発火", m_suspect_w1, (u"verdict",)),
    (u"M45 整合: 段 PK の N を 30% 超にして自己点検が発火", m_suspect_n, (u"verdict",)),
    (u"M46 文書の「63 本のうち 1 本だけだった」を 2 本に", lambda c: rep(c, u"63 本のうち 1 本だけだった", u"63 本のうち 2 本だけだった"), (u"frag",)),
    (u"M47 文書の「行の合計では 87.3% が決まる」を 87.4% に", lambda c: rep(c, u"行の合計では 87.3% が決まる", u"行の合計では 87.4% が決まる"), (u"frag", u"numbers")),
    (u"M48 文書の「U は減らず増えた」を「U は減り増えた」に", lambda c: rep(c, u"U は減らず増えた", u"U は減り増えた"), (u"frag",)),
    (u"M49 文書の「A が 3344 → 1339 に減り」を「増え」に", lambda c: rep(c, u"(A)が 3344 → 1339 に減り", u"(A)が 3344 → 1339 に増え"), (u"frag",)),
    (u"M50 文書の「N は 627 → 669 に増えた」を「減った」に", lambda c: rep(c, u"N は 627 → 669 に増えた", u"N は 627 → 669 に減った"), (u"frag",)),
    (u"M51 文書の「率が高い」を「率が低い」に", lambda c: rep(c, u"こちらの側で率が高い", u"こちらの側で率が低い"), (u"frag",)),
    (u"M52 文書の「9 割近く」を「5 割近く」に", lambda c: rep(c, u"仕事の 9 割近くは", u"仕事の 5 割近くは"), (u"frag",)),
    (u"M53 文書の「1000 行に 1 行ほど」を「100 行に 1 行ほど」に", lambda c: rep(c, u"1000 行に 1 行ほど", u"100 行に 1 行ほど"), (u"frag", u"resid")),
    (u"M54 文書の「残る 1 割前後」を「残る 3 割前後」に", lambda c: rep(c, u"残る 1 割前後(候補が残る行と", u"残る 3 割前後(候補が残る行と"), (u"frag",)),
    (u"M55 §3 の「標準の計算書の行の 1 割前後」を「5 割前後」に", lambda c: rep(c, u"標準の計算書の行の 1 割前後", u"標準の計算書の行の 5 割前後"), (u"sec3",)),
    (u"M56 文書の「最小 70.4%」を 70.5% に", lambda c: rep(c, u"最小 70.4%", u"最小 70.5%"), (u"frag", u"numbers")),
    (u"M57 文書の「95% 以上が 1 本・」を「95% 以上が 2 本・」に", lambda c: rep(c, u"95% 以上が 1 本・", u"95% 以上が 2 本・"), (u"frag",)),
    (u"M58 文書の「W1 が 1 行以上在る書類は 11 本」を 12 本に", lambda c: rep(c, u"在る書類は 11 本", u"在る書類は 12 本"), (u"frag",)),
    (u"M59 文書の「N だった 669 行のうち 532 行」を 533 行に", lambda c: rep(c, u"のうち 532 行が決まる", u"のうち 533 行が決まる"), (u"frag", u"numbers")),
    (u"M60 文書の「前の年に無かった行は 4.2%」を 4.3% に", lambda c: rep(c, u"前の年に無かった行は 4.2% だった", u"前の年に無かった行は 4.3% だった"), (u"frag", u"numbers")),
    (u"M61 文書の XG1 の 80.4% を 80.5% に", lambda c: rep(c, u"1 つに決まった行は 80.4% だった", u"1 つに決まった行は 80.5% だった"), (u"frag", u"numbers")),
    (u"M62 文書の §2 の段 PK の行 14021 を 14022 に", lambda c: rep(c, u"| 14021(87.3%) |", u"| 14022(87.3%) |"), (u"frag", u"numbers")),
    (u"M63 文書の「2026 行(12.6%)」を 2027 行に", lambda c: rep(c, u"= 2026 行(12.6%)", u"= 2027 行(12.6%)"), (u"frag", u"numbers")),
    (u"M64 文書に 9999 の言い切りを足す", lambda c: add_doc(c, u"9999 行が決まった。"), (u"numbers",)),
    (u"M65 文書に「48%」の言い切りを足す", lambda c: add_doc(c, u"決まった行は 48% だった。"), (u"resid",)),
    (u"M66 §3 に 3 桁の数を足した行", lambda c: rep(c, u"## §4 ", u"- 足した行 321 行。\n\n## §4 "), (u"sec3",)),
    (u"M67 §3 の「便 XG1(」の行を消す", lambda c: rep(c, u"便 XG1(行の字と標準の表だけ。67 本)", u"便 X"), (u"sec3",)),
    (u"M68 文書に「XBRL を作れる。」を引用の外で足す", lambda c: add_doc(c, u"XBRL を作れる。"), (u"affirm",)),
    (u"M69 文書に「専用の道具が要らない。」を足す", lambda c: add_doc(c, u"専用の道具が要らない。"), (u"affirm",)),
    (u"M70 文書に「AI が書ける。」を足す", lambda c: add_doc(c, u"AI が書ける。"), (u"affirm",)),
    (u"M71 文書に「人が書ける。」を足す", lambda c: add_doc(c, u"人が書ける。"), (u"affirm",)),
    (u"M72 文書に「EDINET の検査に通る。」を足す", lambda c: add_doc(c, u"EDINET の検査に通る。"), (u"affirm",)),
    (u"M73 引用の行から「言えない」「読まない」を全部消す", m_drop_quote_negation, (u"affirm",)),
    (u"M74 §5 の「言えないこと」を消す", lambda c: drop_all(c, u"言えないこと"), (u"phrases",)),
    (u"M75 頭の限界「前の年の XBRL が在る会社にしか使えない」を消す", lambda c: drop_all(c, u"前の年の XBRL が在る会社にしか使えない"), (u"head",)),
    (u"M76 頭の限界「63 組は無作為ではない」を消す", lambda c: drop_all(c, u"63 組は無作為ではない"), (u"head",)),
    (u"M77 頭の限界「測るのは要素の名だけ」を消す", lambda c: drop_all(c, u"測るのは要素の名だけ"), (u"head",)),
    (u"M78 頭の限界「前の年に無かった行(N)は、道具がいちばん要る所」を消す", lambda c: drop_all(c, u"前の年に無かった行(N)は、道具がいちばん要る所"), (u"head",)),
    (u"M79 頭の「(封 §0 の申告)」を消す", lambda c: drop_all(c, u"(封 §0 の申告)"), (u"head",)),
    (u"M80 頭の「先に負けと限界を書く」を消す", lambda c: drop_all(c, u"先に負けと限界を書く"), (u"head",)),
    (u"M81 頭の「LLM の席は呼んでいない」を消す", lambda c: drop_all(c, u"LLM の席は呼んでいない"), (u"head",)),
    (u"M82 頭の「この便の U は「上の限り」に近い読み」を消す", lambda c: drop_all(c, u"この便の U は「上の限り」に近い読み"), (u"head",)),
    (u"M83 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"M84 文書に docID の形を足す", lambda c: add_doc(c, u"S100ABCD"), (u"forbidden",)),
    (u"M85 文書の commit の字 4591db32 を 1 字替える", lambda c: drop_all(c, u"4591db32"), (u"commits",)),
    (u"M86 文書に知らない commit の字を足す", lambda c: add_doc(c, u"commit 1a2b3c4d。"), (u"commits",)),
    (u"M91 文書の「黙って違う行も 4 行増える」を「4 行減る」に", lambda c: rep(c, u"黙って違う行も 4 行増える", u"黙って違う行も 4 行減る"), (u"frag",)),
    (u"M92 文書の「(予測は 10 本以上 40 本以下)」を「20 本以上 40 本以下」に", lambda c: rep(c, u"(予測は 10 本以上 40 本以下)", u"(予測は 20 本以上 40 本以下)"), (u"frag",)),
    (u"M93 文書の「「1 本をまるごと済ませる」ものではない」を消す", lambda c: drop_all(c, u"「1 本をまるごと済ませる」ものではない"), (u"phrases",)),
    (u"M94 文書の「差をそのまま「前の年の表の効き」とは読まない」を肯定に", lambda c: rep(c, u"差をそのまま「前の年の表の効き」とは読まない", u"差を「前の年の表の効き」と読む"), (u"phrases",)),
    (u"M88 整合: 段 PK の U を減らして段 P の U より小さくし「増えた」の向きを崩す", m_p_over_pk, (u"sanity",)),
    (u"M89 整合: 段 PK の W1 を 100 行に 1 行ほどにして「1000 行に 1 行ほど」を崩す", m_w1_many, (u"sanity",)),
    (u"M90 整合: 95% 以上の書類を 0 本にして「1 本」が崩れる", m_u95_zero, (u"frag", u"verdict")),
)


def run_mutations(base=None):
    base = base or Ctx()
    out = []
    for name, fn, checks in MUTATIONS:
        c = base.copy()
        fn(c)
        res = [(k, bool(guard(CHECKS[k], c))) for k in checks]
        out.append((name, res))
    return out


# ======================================================================================================
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
        s = self.c.rec[AGG]
        pk = s[K_SSTAGE]["PK"]
        self.assertEqual((16063, 20606, 63), (s[K_SROWS], s[K_BROWS], s[K_NONEMPTY]))
        self.assertEqual((14021, 1339, 16, 18, 669), tuple(pk[k] for k in CLASSES))
        self.assertEqual((12028, 3344, 38, 26, 627), tuple(s[K_SSTAGE]["P"][k] for k in CLASSES))
        self.assertEqual((14553, 1439, 20, 19, 32), tuple(s[K_SSTAGE]["C"][k] for k in CLASSES))
        self.assertEqual((17746, 1686, 101, 20, 1053), tuple(s[K_BSTAGE]["PK"][k] for k in CLASSES))
        self.assertEqual((669, 532, 100, 4, 1, 32), (s[K_FALL], s[K_FALLC]["U"], s[K_FALLC]["A"], s[K_FALLC]["W1"], s[K_FALLC]["W2"], s[K_FALLC]["N"]))
        lo, mid, hi, cnt, w1docs, w1max = doc_stats(self.c.rec)
        self.assertEqual((u"70.4", u"87.9", u"96.3", [60, 45, 21, 1, 0], 11, 3), (fpct(lo), fpct(mid), fpct(hi), cnt, w1docs, w1max))
        self.assertEqual(80.4, xg1_pct(self.c))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(6, sum(1 for v in j.values() if v[0]))
        self.assertEqual([u"XY0-7"], [k for k, v in j.items() if not v[0]])
        self.assertEqual(list(IDS), list(j))
        self.assertEqual((False, False, False), suspects(self.c))

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))
        self.assertEqual([], residual_problems(self.c))

    def test_d_2_the_table_rows_and_the_statements_equal_the_record(self):
        self.assertEqual([], fragment_problems(self.c))
        self.assertEqual([], sanity_problems(self.c))

    def test_d_3_section3_holds_only_the_derived_numbers(self):
        self.assertEqual([], sec3_problems(self.c))

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
        self.assertEqual([SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT, RECORD_COMMIT_SHORT], list(BLOB_AT.values()))
        self.assertEqual((SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT), DOC_COMMITS)
        self.assertEqual((u"ce70f71f", u"150c7fe6", u"4591db32"), DOC_COMMITS)

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
    def test_g_1_every_mutation_turns_its_checks_red_and_the_files_are_unchanged(self):
        files = list(SHA_PIN) + [DOC_REL]
        before = tuple(sha_file(r) for r in files)
        base = Ctx()
        results = run_mutations(base)
        self.assertEqual(before, tuple(sha_file(r) for r in files))
        self.assertEqual(len(MUTATIONS), len(results))
        silent = [(n, k) for n, res in results for k, red in res if not red]
        self.assertEqual([], silent)
        self.assertGreaterEqual(len(MUTATIONS), 85)

    def test_g_2_the_unmutated_copy_is_green_on_every_check(self):
        c = Ctx().copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_g_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_verdict_does_not(self):
        base = Ctx()
        for fn, key in ((m_p_low, u"XY0-1"), (set_pk_u_high, u"XY0-2"), (m_pk_w1_high, u"XY0-3"), (m_pk_n_high, u"XY0-4"), (m_c_w1_high, u"XY0-5"), (m_b_low, u"XY0-6"), (m_u95_ten, u"XY0-7")):
            c = base.copy()
            fn(c)
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
            self.assertNotEqual(judge(base.rec)[key][0], judge(c.rec)[key][0], (fn.__name__, key))

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数(丸める前の整数・分数): 下限・上限とも含む。XY0-6 は差が -5 ちょうどを含む。XY0-7 は 10 本・40 本を含む。"""
        def with_(**kw):
            c = Ctx().copy()
            s = c.rec[AGG]
            s[K_SROWS] = 1000
            s[K_BROWS] = 2000
            for st in ("P", "PK", "C"):
                s[K_SSTAGE][st] = collections.OrderedDict([("U", 900), ("A", 60), ("W1", 5), ("W2", 5), ("N", 30)])
            s[K_BSTAGE]["PK"] = collections.OrderedDict([("U", 1800), ("A", 100), ("W1", 20), ("W2", 10), ("N", 70)])
            for d in c.rec[u"書類"]:
                d[K_SROWS] = 1000
                d[K_SSTAGE]["PK"] = collections.OrderedDict([("U", 900), ("A", 60), ("W1", 5), ("W2", 5), ("N", 30)])
            for key, val in kw.items():
                if key == u"p":
                    s[K_SSTAGE]["P"]["U"] = val
                elif key == u"pk":
                    s[K_SSTAGE]["PK"]["U"] = val
                elif key == u"w1":
                    s[K_SSTAGE]["PK"]["W1"] = val
                elif key == u"n":
                    s[K_SSTAGE]["PK"]["N"] = val
                elif key == u"cu":
                    s[K_SSTAGE]["C"]["U"] = val
                elif key == u"cw":
                    s[K_SSTAGE]["C"]["W1"] = val
                elif key == u"bu":
                    s[K_BSTAGE]["PK"]["U"] = val
                elif key == u"docs95":
                    for i, d in enumerate(c.rec[u"書類"]):
                        d[K_SSTAGE]["PK"]["U"] = 950 if i < val else 949
            return judge(c.rec)
        self.assertTrue(with_(p=720)[u"XY0-1"][0])
        self.assertFalse(with_(p=719)[u"XY0-1"][0])
        self.assertTrue(with_(p=880)[u"XY0-1"][0])
        self.assertFalse(with_(p=881)[u"XY0-1"][0])
        self.assertTrue(with_(pk=840)[u"XY0-2"][0])
        self.assertFalse(with_(pk=839)[u"XY0-2"][0])
        self.assertTrue(with_(pk=950)[u"XY0-2"][0])
        self.assertFalse(with_(pk=951)[u"XY0-2"][0])
        self.assertTrue(with_(w1=15)[u"XY0-3"][0])
        self.assertFalse(with_(w1=16)[u"XY0-3"][0])
        self.assertTrue(with_(n=30)[u"XY0-4"][0])
        self.assertTrue(with_(n=120)[u"XY0-4"][0])
        self.assertFalse(with_(n=121)[u"XY0-4"][0])
        self.assertFalse(with_(n=29)[u"XY0-4"][0])
        self.assertTrue(with_(cu=860)[u"XY0-5"][0])
        self.assertFalse(with_(cu=859)[u"XY0-5"][0])
        self.assertTrue(with_(cu=970)[u"XY0-5"][0])
        self.assertFalse(with_(cu=971)[u"XY0-5"][0])
        self.assertTrue(with_(cw=25)[u"XY0-5"][0])
        self.assertFalse(with_(cw=26)[u"XY0-5"][0])
        # S の率 90.0%・B の率 = bu / 2000。差 -5 ちょうど(B 85.0% = 1700)は当たり・1699 は外れ
        self.assertTrue(with_(bu=1700)[u"XY0-6"][0])
        self.assertFalse(with_(bu=1699)[u"XY0-6"][0])
        self.assertTrue(with_(docs95=10)[u"XY0-7"][0])
        self.assertFalse(with_(docs95=9)[u"XY0-7"][0])
        self.assertTrue(with_(docs95=40)[u"XY0-7"][0])
        self.assertFalse(with_(docs95=41)[u"XY0-7"][0])

    def test_g_6_the_miss_direction_follows_the_bound(self):
        c = Ctx().copy()
        m_p_low(c)
        self.assertEqual(u"下", judge(c.rec)[u"XY0-1"][1])
        c = Ctx().copy()
        set_pk_u_high(c)
        self.assertEqual(u"上", judge(c.rec)[u"XY0-2"][1])

    def test_g_7_the_self_suspicion_conditions_fire_for_each_cause(self):
        base = Ctx()
        self.assertEqual((False, False, False), suspects(base))
        for fn, idx in ((m_u98, 0), (m_suspect_w1, 1), (m_suspect_n, 2)):
            c = base.copy()
            fn(c)
            f = suspects(c)
            self.assertTrue(f[idx], (fn.__name__, f))
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
        # ちょうど 98%・5%・30% は発火しない(「超える」)
        for key, sub, tot in ((0, u"U", 98), (1, u"W1", 5), (2, u"N", 30)):
            c = base.copy()
            s = c.rec[AGG]
            s[K_SROWS] = 1000
            s[K_SSTAGE]["PK"] = collections.OrderedDict([("U", 0), ("A", 0), ("W1", 0), ("W2", 0), ("N", 0)])
            s[K_SSTAGE]["PK"][sub] = 10 * tot
            self.assertFalse(suspects(c)[key], sub)
            s[K_SSTAGE]["PK"][sub] = 10 * tot + 1
            self.assertTrue(suspects(c)[key], sub)


if __name__ == "__main__":
    unittest.main()
