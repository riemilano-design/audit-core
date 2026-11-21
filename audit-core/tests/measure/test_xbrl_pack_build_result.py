# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_PACK_BUILD_SEAL_2026-11-22.md(c03a3348)・封への追記(465d0bc7)の結果の文書 docs/XBRL_PACK_BUILD_RESULT_2026-11-22.md。

封の門 ``test_xbrl_pack_build_seal.py`` の次の段。**追跡されている記録・script・封・追記・結果の文書と git の履歴だけを読む**(道具(Arelle)も置き場も読まない・通信しない・鍵は読まない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封の門・封・追記の sha256(字で留める)と、記録の script の sha256・封の commit の欄・記録の限界の欄
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、3 群の集計・混ぜ物・混ぜ物の種類ごと・予測の判定に要る数を数え直して記録と同じことを見る。
   書類ごとの「鳴り方が同じ」の旗は、元と組み直しの符号ごとの行から、「全部同じ」「タクソノミが同じ」は書き出し 7 つの旗から、「原稿が元より大きい」は bytes から数え直す。
   「fact が同じ」の旗は、行の数が同じ(必要条件)までを数え直す
 c 予測 XP0-1〜XP0-7 の当たり外れを、封 §4 の字から取った境(封の文書にその字が在ることも見る)と記録から決め直し、文書 §1 の表・件数と同じことを見る。
   封 §4 の自己点検の条・封 §6 の 2 つの決め(XP0-6 が外れたら・XP0-1 と XP0-6 がどちらも当たりなら)と文書が合う
 d 結果の文書の数: 数字を含む行は全部、記録から組んだ数の並びの内。表の行・言い切りは記録から組んだ字とそのまま照らす。
   §3 は記録に欄の無い読みの節で、数は字で留めた小さい集合だけ(その外の節に記録に無い数が漏れていない。§3 に 3 桁以上の数・% が無い)
 e 文書の要点の字・頭の負けと限界・禁止語・「作れる」「通る」を肯定で書かない・docID と EDINET コードの形
 f 封・追記・script・記録・封の門が commit の blob と一致(結果の便で 0 行)・engine は封の commit から 0 行・順序・文書が書く commit の字が実の履歴と合う
この file は docID の字を持たない。
"""
import collections
import copy
import hashlib
import importlib.util
import io
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


SG = load_module("tests/measure/test_xbrl_pack_build_seal.py", "xbrl_pack_build_seal_gate_for_result_gate")        # 封の門の部品。門としては走らせない
PR = SG.X.load_helpers()
MS = SG.MS

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
ADD_REL = "docs/XBRL_PACK_BUILD_SEAL_ADDENDUM_2026-11-22.md"
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_pack_build_result.py"
DOC_REL = "docs/XBRL_PACK_BUILD_RESULT_2026-11-22.md"
SCRIPT_COMMIT_SHORT = "465d0bc7"                  # 追記・script・封の門を足した commit
RECORD_COMMIT_SHORT = "13b277e9"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (ADD_REL, SCRIPT_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "6c592fdf947a430789de14d181983c024b54b7eb9a3bfe739ed2d5ed19463293"),
    (SCRIPT_REL, "ea399ec447b44a4611ef3ca8e549ecfac017ef108ed454db00f439e3979083b7"),
    (SEAL_GATE_REL, "d7d84b19a059eb92f0153d940ad938cf05842089ed143793d440603151b051e7"),
    (SEAL_REL, "55fc586f1f482a3566ba52c76ac9c429e4a77904143472f0afade5389be30aca"),
    (ADD_REL, "b4971534de61d1bf67ef25cdfea4d06a676480d03ac444172643fd30516eaf1c")])

DEV_COUNT = 5
DOC_COUNT = 67
CLASSES = (u"走った", u"止まった", u"走らなかった")
OUT_KEYS = (u"概念", u"役割型", u"表示", u"計算", u"次元", u"ラベルの関係", u"一般特殊")
FOLDER_KINDS = (u"素の本文", u"本文の表", u"タクソノミの表", u"目次")
MIX_KINDS = (u"本文の数を変える", u"fact を抜く", u"ラベルを変える", u"計算の向きを返す")
PRED_KEY = u"予測の判定に要る数(XP0-1〜XP0-7。当たり・外れは結果の文書で)"
PK = (u"XP0-1 全部同じ書類", u"XP0-2 断った書類", u"XP0-3 鳴り方が同じ書類", u"XP0-4 2 度が同じ書類", u"XP0-5 道筋が同じ書類",
      u"XP0-6 作れた混ぜ物のうち違いを見つけたもの", u"XP0-7 原稿の folder の bytes の合計が元の bytes の合計より大きい書類", u"補 作れた混ぜ物の数・混ぜ物の数")
GROUPS = (u"開発の 5 本", u"本番だけの 62 本", u"全部")
# 封 §4 の字(封の文書にその字が在ることを見る)
BOUND_SEAL_PHRASES = (u"全部同じ書類は 58 本以上", u"断った書類は 2 本以下", u"鳴り方が同じ書類は 58 本以上", u"2 度が同じ書類は、断らなかった書類の全部", u"道筋が同じ書類は、断らなかった書類の全部",
                      u"作れた混ぜ物の全部で、違いを見つける", u"より大きい書類は 50 本以上",
                      u"全部同じ書類が 62 本だったら、先に自分の欠陥を疑う",
                      u"XP0-6 が外れたら、XP0-1・XP0-3 は当たり外れを書いたうえで「比べ方が効いていない」と結果の頭に書く",
                      u"XP0-1 と XP0-6 がどちらも当たりなら、次の便の候補を人間に示す",
                      u"(i) 本文の表を、字の位置でなく人が書ける印(表の行と列・見出しの字)で場所を指す形に替え、そこから組む",
                      u"(ii) 提出者別タクソノミの表を元の file から読まず、本文で使う要素の並びと標準のタクソノミから導き、元の表とどれだけ重なるかを測る",
                      u"(iii) マニフェストも folder から組む")
SEAL7_PHRASES = (u"原稿の folder は元の包みから作っている", u"マニフェスト・画像・AuditDoc は元のまま", u"司令塔が 1 行を直したもの", u"EDINET の本物の検査とは照らしていない", u"無作為ではない。有報だけ",
                 u"「EDINET の検査に通る」「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない")
HEAD_PHRASES = (u"先に負けと限界を書く", u"当たり 6・外れ 1", u"外れは XP0-7", u"全部ではない(60/62)", u"端の数が 5 つ在る", u"予測は当たりやすかった",
                u"「XBRL を作れる」「専用の道具が要らない」を示していない", u"元の書類から読んだ答えをそのまま渡した", u"人が書ける形ではない",
                u"repo の外へ持ち出せる 1 つの file ではない", u"別の算法との突き合わせではない", u"混ぜ物は開発の 5 本だけで作った", u"封の門の変異 2 つは門で黙る",
                u"公開の道具 1 つ(道具 P。司令塔が 1 行を直したもので、本家の版ではない)", u"追記 4 の門の穴は、この便にもそのまま在る", u"マニフェスト・画像・監査報告書の包みは元のまま",
                u"EDINET の本物の検査とは照らしていない", u"67 本は無作為ではない。有報だけ", u"この便からは言えない", u"0 USD・LLM の席は呼んでいない", u"本番は 1 回だけ走らせた",
                u"掛け直していない", u"字は元と違う", u"直していない")
PHRASES = (u"言えること", u"言えないこと", u"人間に示す次の便の候補", u"別の封が先", u"盲検ではない", u"記録に欄の無い読み", u"人間が決めること",
           u"残っているのは folder の中身を誰がどう決めるかで", u"この便はそこを測っていない", u"「軽い原稿で済む」とは読まない", u"直接掛けていない", u"便 XT0 と同じ",
           u"封も予測も結果を見てから書き換えていない", u"予測は書き換えていない")
FORBIDDEN_WORDS = (u"精度", u"世界で 1 社", u"LLM より正確", u"保証", u"完璧")
DOCID_FORM = re.compile(r"(?<![0-9A-Za-z])S[0-9A-Z]{7}(?![0-9A-Za-z])")
ECODE_FORM = re.compile(r"(?<![0-9A-Za-z])E\d{5}(?![0-9A-Za-z])")
# 記録に欄の無い読み(§3)の、行ごとの数の並び。記録から導けない監査の席の読みなので、正本は文書の字そのもの = ここに字で留める(留め)。
# 行の鍵になる句 → その行に在るべき数の並び(文書の左から右の順。docID・commit・`` ` `` の中は数えない)。
# §3 の行(箇条)がこの表と 1 対 1 でなければ赤。数の入れ替え・別の行への移し替えも赤。
SEC3_LINES = (
    (u"**同じでない 2 本の理由は", (u"2", u"1")),
    (u"**組む命令は folder のほかを材料に読んでいない。**", (u"5", u"0")),
    (u"同じ 5 本で、別の process で 2 回組んだ", (u"5", u"2")),
    (u"**比べる元は", ()),
    (u"原稿の folder の bytes は、書類ごとに元の", (u"0.88", u"0.93")),
    (u"混ぜ物のうち 3 個を監査の席が", (u"3", u"5", u"5")),
)
STRUCTURAL = set([u"0", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"10"])


# ======================================================================================================
def read(rel, root=ROOT):
    with io.open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_file(rel, root=ROOT):
    with open(os.path.join(root, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except BaseException as exc:                   # noqa: BLE001  変異で落ちた検査は「問題」として数える
        return [u"例外: %s" % type(exc).__name__]


class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.add = read(ADD_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.doc = self.doc
        c.seal = self.seal
        c.add = self.add
        c.shas = collections.OrderedDict(self.shas)
        return c


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def sound_of(d):
    u"""元と組み直しの 1 回の類と符号ごとの行が同じか(断った書類は同じでない)。"""
    a, b = d[u"元の 1 回"], d[u"組み直しの 1 回"]
    if d[u"断った"] or b is None:
        return False
    return a[u"類"] == b[u"類"] and dict(a[u"符号ごとの行"]) == dict(b[u"符号ごとの行"])


def folder_total(d):
    return sum(d[u"原稿の folder"][k][u"bytes"] for k in FOLDER_KINDS)


def orig_total(d):
    return d[u"元の包みの bytes"][u"htm"][u"bytes"] + d[u"元の包みの bytes"][u"タクソノミ"][u"bytes"]


def group_recount(docs):
    cls = collections.OrderedDict((c, 0) for c in CLASSES)
    dec = allsame = taxsame = fs = ss = twice = path = big = low = 0
    secs = 0.0
    reasons = collections.Counter()
    out_same = collections.OrderedDict((k, 0) for k in OUT_KEYS)
    rows = collections.OrderedDict((k, 0) for k in OUT_KEYS)
    fold = collections.OrderedDict((k, collections.OrderedDict([(u"file", 0), (u"bytes", 0)])) for k in FOLDER_KINDS)
    fbytes = obytes = hf = tf = hb = tb = 0
    for d in docs:
        if d[u"断った"]:
            dec += 1
            reasons[d[u"断った理由"]] += 1
        else:
            cls[d[u"組み直しの 1 回"][u"類"]] += 1
        taxsame += 1 if d[u"タクソノミが同じ"] else 0
        allsame += 1 if d[u"全部同じ"] else 0
        fs += 1 if d[u"fact が同じ"] else 0
        ss += 1 if d[u"鳴り方が同じ"] else 0
        twice += 1 if d[u"2 度が同じ"] else 0
        path += 1 if d[u"道筋が同じ"] else 0
        big += 1 if d[u"原稿が元より大きい"] else 0
        low += 1 if d[u"元の書き出しの行の数"][u"概念"] <= 1 else 0
        secs += d[u"組む命令の秒"]
        for k in OUT_KEYS:
            out_same[k] += 1 if d[u"書き出しが同じ"][k] else 0
            rows[k] += d[u"元の書き出しの行の数"][k]
        for k in FOLDER_KINDS:
            fold[k][u"file"] += d[u"原稿の folder"][k][u"file"]
            fold[k][u"bytes"] += d[u"原稿の folder"][k][u"bytes"]
        fbytes += d[u"原稿の folder"][u"合計 bytes"]
        obytes += d[u"元の包みの bytes"][u"合計 bytes"]
        hf += d[u"元の包みの bytes"][u"htm"][u"file"]
        tf += d[u"元の包みの bytes"][u"タクソノミ"][u"file"]
        hb += d[u"元の包みの bytes"][u"htm"][u"bytes"]
        tb += d[u"元の包みの bytes"][u"タクソノミ"][u"bytes"]
    return collections.OrderedDict([
        (u"書類", len(docs)), (u"断った書類", dec), (u"断った理由ごと", collections.OrderedDict(sorted(reasons.items()))), (u"断らなかった書類", len(docs) - dec),
        (u"全部同じ書類", allsame), (u"タクソノミが同じ書類", taxsame), (u"fact が同じ書類", fs), (u"鳴り方が同じ書類", ss), (u"書き出しごとに同じ書類", out_same),
        (u"組み直した包みの 1 回の類ごと", cls), (u"2 度が同じ書類", twice), (u"道筋が同じ書類", path),
        (u"原稿の folder の合計", collections.OrderedDict([(u"種類ごと", fold), (u"bytes の合計", fbytes)])),
        (u"元の包みの合計", collections.OrderedDict([(u"file", collections.OrderedDict([(u"htm", hf), (u"タクソノミ", tf)])), (u"htm の bytes", hb), (u"タクソノミの bytes", tb), (u"bytes の合計", obytes)])),
        (u"原稿が元より大きい書類", big), (u"組む命令の秒の合計", round(secs, 1)), (u"元の書き出しの行の数の合計", rows), (u"元の概念の行が 1 以下の書類", low)])


def mix_recount(docs):
    n = made = found = sd = 0
    for d in docs:
        for m in d[u"混ぜ物"]:
            n += 1
            if m[u"作った"]:
                made += 1
                found += 1 if m[u"違いを見つけた"] else 0
                sd += 1 if m[u"鳴り方が違う"] else 0
    return collections.OrderedDict([(u"混ぜ物の数", n), (u"作れた数", made), (u"違いを見つけた数", found), (u"鳴り方が違う数", sd)])


def mix_by_kind(docs):
    out = collections.OrderedDict((k, collections.OrderedDict([(u"作れた", 0), (u"違いを見つけた", 0), (u"鳴り方が違う", 0)])) for k in MIX_KINDS)
    for d in docs:
        for m in d[u"混ぜ物"]:
            if m[u"作った"]:
                r = out[m[u"種類"]]
                r[u"作れた"] += 1
                r[u"違いを見つけた"] += 1 if m[u"違いを見つけた"] else 0
                r[u"鳴り方が違う"] += 1 if m[u"鳴り方が違う"] else 0
    return out


def totals(rec):
    docs = rec[u"書類"]
    dev, prod = docs[:DEV_COUNT], docs[DEV_COUNT:]
    return collections.OrderedDict([
        (GROUPS[0], group_recount(dev)), (GROUPS[1], group_recount(prod)), (GROUPS[2], group_recount(docs)), (u"混ぜ物", mix_recount(dev)), (u"混ぜ物の種類ごと", mix_by_kind(dev))])


def pred_expected(tot):
    prod, mx = tot[GROUPS[1]], tot[u"混ぜ物"]
    return collections.OrderedDict([
        (PK[0], collections.OrderedDict([(u"書類", prod[u"全部同じ書類"]), (u"分母", prod[u"書類"])])),
        (PK[1], collections.OrderedDict([(u"書類", prod[u"断った書類"]), (u"分母", prod[u"書類"])])),
        (PK[2], collections.OrderedDict([(u"書類", prod[u"鳴り方が同じ書類"]), (u"分母", prod[u"書類"])])),
        (PK[3], collections.OrderedDict([(u"書類", prod[u"2 度が同じ書類"]), (u"分母(断らなかった書類)", prod[u"断らなかった書類"])])),
        (PK[4], collections.OrderedDict([(u"書類", prod[u"道筋が同じ書類"]), (u"分母(断らなかった書類)", prod[u"断らなかった書類"])])),
        (PK[5], collections.OrderedDict([(u"個", mx[u"違いを見つけた数"]), (u"分母", mx[u"作れた数"])])),
        (PK[6], collections.OrderedDict([(u"書類", prod[u"原稿が元より大きい書類"]), (u"分母", prod[u"書類"])])),
        (PK[7], collections.OrderedDict([(u"作れた", mx[u"作れた数"]), (u"分母", mx[u"混ぜ物の数"])]))])


def judge(tot):
    u"""封 §4 の境と記録から XP0-1〜XP0-7 の当たり外れを決め直す。"""
    prod, mx = tot[GROUPS[1]], tot[u"混ぜ物"]
    out = collections.OrderedDict()
    out[u"XP0-1"] = prod[u"全部同じ書類"] >= 58
    out[u"XP0-2"] = prod[u"断った書類"] <= 2
    out[u"XP0-3"] = prod[u"鳴り方が同じ書類"] >= 58
    out[u"XP0-4"] = prod[u"2 度が同じ書類"] == prod[u"断らなかった書類"]
    out[u"XP0-5"] = prod[u"道筋が同じ書類"] == prod[u"断らなかった書類"]
    out[u"XP0-6"] = mx[u"違いを見つけた数"] == mx[u"作れた数"]
    out[u"XP0-7"] = prod[u"原稿が元より大きい書類"] >= 50
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


def recount_problems(c):
    rec = c.rec
    out = []
    docs = rec[u"書類"]
    if [d[u"番号"] for d in docs] != list(range(1, DOC_COUNT + 1)) or rec[u"材料"][u"書類の本数"] != DOC_COUNT or rec[u"材料"][u"開発の 5 本の番号"] != list(range(1, DEV_COUNT + 1)):
        out.append(u"書類の番号・材料の書類の本数・開発の 5 本の番号が違う")
    if rec[u"材料"][u"混ぜ物の種類"] != list(MIX_KINDS):
        out.append(u"混ぜ物の種類が違う")
    for d in docs:
        n = d[u"番号"]
        if d[u"断った"] or d[u"組み直しの 1 回"] is None:
            out.append(u"書類 %d が断った" % n)
            continue
        for k in (u"元の 1 回", u"組み直しの 1 回"):
            e = d[k]
            nl = e[u"出力の行の数"]
            if e[u"類"] not in CLASSES or e[u"時間の上限を超えた"]:
                out.append(u"書類 %d の %s の類・時間の上限が違う" % (n, k))
            if not isinstance(nl, int) or isinstance(nl, bool) or nl < sum(e[u"符号ごとの行"].values()):
                out.append(u"書類 %d の %s の出力の行の数が指摘の行の数より少ない" % (n, k))
        if d[u"鳴り方が同じ"] != sound_of(d):
            out.append(u"書類 %d の鳴り方が同じの旗が符号ごとの行から数え直した値と違う" % n)
        if list(d[u"書き出しが同じ"]) != list(OUT_KEYS) or list(d[u"原稿の folder"]) != list(FOLDER_KINDS) + [u"合計 bytes"]:
            out.append(u"書類 %d の書き出し・原稿の folder の欄が違う" % n)
            continue
        if d[u"タクソノミが同じ"] != all(d[u"書き出しが同じ"].values()) or d[u"全部同じ"] != (d[u"タクソノミが同じ"] and d[u"fact が同じ"]):
            out.append(u"書類 %d のタクソノミが同じ・全部同じの旗が書き出しの旗から数え直した値と違う" % n)
        for k in OUT_KEYS:
            a, b = d[u"元の書き出しの行の数"][k], d[u"組み直しの書き出しの行の数"][k]
            if d[u"書き出しが同じ"][k] and k != u"概念" and a != b:
                out.append(u"書類 %d の %s は同じなのに行の数が違う" % (n, k))
        if d[u"fact が同じ"] and (d[u"元の fact の行の数"] == 0 or d[u"元の fact の行の数"] != d[u"組み直しの fact の行の数"]):
            out.append(u"書類 %d は fact が同じなのに fact の行の数が違う・0 行" % n)
        if folder_total(d) != d[u"原稿の folder"][u"合計 bytes"]:
            out.append(u"書類 %d の原稿の folder の bytes の合計が種類ごとの和と違う" % n)
        if orig_total(d) != d[u"元の包みの bytes"][u"合計 bytes"]:
            out.append(u"書類 %d の元の包みの bytes の合計が htm とタクソノミの和と違う" % n)
        if d[u"原稿が元より大きい"] != (d[u"原稿の folder"][u"合計 bytes"] > d[u"元の包みの bytes"][u"合計 bytes"]):
            out.append(u"書類 %d の原稿が元より大きいの旗が bytes から数え直した値と違う" % n)
        if n <= DEV_COUNT and [m[u"種類"] for m in d[u"混ぜ物"]] != list(MIX_KINDS):
            out.append(u"書類 %d の混ぜ物の種類が違う" % n)
        if n > DEV_COUNT and d[u"混ぜ物"]:
            out.append(u"書類 %d に混ぜ物が在る(本番だけの書類は混ぜ物を持たない)" % n)
        for m in d[u"混ぜ物"]:
            if not m[u"作った"] and (m[u"違いを見つけた"] or m[u"鳴り方が違う"]):
                out.append(u"書類 %d の作れなかった混ぜ物に違い・鳴り方が付いている" % n)
    tot = totals(rec)
    if json.loads(json.dumps(rec[u"集計"])) != json.loads(json.dumps(tot)):
        out.append(u"集計が書類ごとの数から数え直した値と違う")
    if json.loads(json.dumps(rec[PRED_KEY])) != json.loads(json.dumps(pred_expected(tot))):
        out.append(u"予測の判定に要る数が数え直しと違う")
    return out


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    out = []
    try:
        MS.check_clean(c.rec, text)
    except SystemExit:
        out.append(u"記録の検査(欄・形・file の名)が止める")
    if DOCID_FORM.search(re.sub(r"[0-9a-fA-F]{32,}", u"", text)) or ECODE_FORM.search(text):
        out.append(u"記録に docid か EDINET コードの形が在る")
    return out


def section(doc, head, nxt):
    i = doc.index(head)
    j = doc.index(nxt, i + len(head)) if nxt else len(doc)
    return doc[i:j]


def bound_problems(c):
    out = [u"封に境の字が無い: %s" % p for p in BOUND_SEAL_PHRASES if p not in c.seal]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    rows = [ln for ln in sec4.splitlines() if re.match(r"^\| XP0-\d", ln)]
    if len(rows) != 7:
        out.append(u"封 §4 の表の行が 7 つでない")
    return out


def addendum_problems(c):
    u"""追記の頭の申告(開発の 5 本の数)が記録の開発の 5 本と同じ。追記の「封の門の変異 2 つ」。原稿の folder が元より小さい(開発の 5 本)。"""
    tot = totals(c.rec)
    dev, mx = tot[GROUPS[0]], tot[u"混ぜ物"]
    want = u"断った %d・全部同じ %d・fact が同じ %d・鳴り方が同じ %d・2 度が同じ %d・道筋が同じ %d" % (
        dev[u"断った書類"], dev[u"全部同じ書類"], dev[u"fact が同じ書類"], dev[u"鳴り方が同じ書類"], dev[u"2 度が同じ書類"], dev[u"道筋が同じ書類"])
    want2 = u"作れた %d・違いを見つけた %d。鳴り方が元と違ったのは N4 の %d 個だけ" % (mx[u"作れた数"], mx[u"違いを見つけた数"], mx[u"鳴り方が違う数"])
    out = []
    if want not in c.add:
        out.append(u"追記の申告の数が記録の開発の 5 本と違う")
    if want2 not in c.add:
        out.append(u"追記の混ぜ物の申告の数が記録の開発の 5 本と違う")
    if dev[u"原稿が元より大きい書類"] != 0 or u"5 本とも元の bytes より小さかった" not in c.add:
        out.append(u"追記の「5 本とも元の bytes より小さかった」が記録の開発の 5 本と合わない")
    if u"封の門の変異 2 つ" not in c.add:
        out.append(u"追記に「封の門の変異 2 つ」が無い")
    return out


# ======================================================================================================
def odd_docs(c):
    u"""本番だけの 62 本のうち、全部同じでない書類の (番号, 同じでない書き出し, fact が同じ, 鳴り方が同じ)。"""
    out = []
    for d in c.rec[u"書類"][DEV_COUNT:]:
        if not d[u"全部同じ"]:
            out.append((d[u"番号"], tuple(k for k in OUT_KEYS if not d[u"書き出しが同じ"][k]), d[u"fact が同じ"], d[u"鳴り方が同じ"]))
    return out


def expected_verdict_cells(c):
    tot = totals(c.rec)
    j = judge(tot)
    prod, mx = tot[GROUPS[1]], tot[u"混ぜ物"]
    nd = prod[u"断らなかった書類"]
    actual = {u"XP0-1": u"%d/%d" % (prod[u"全部同じ書類"], prod[u"書類"]), u"XP0-2": u"%d/%d" % (prod[u"断った書類"], prod[u"書類"]),
              u"XP0-3": u"%d/%d" % (prod[u"鳴り方が同じ書類"], prod[u"書類"]), u"XP0-4": u"%d/%d" % (prod[u"2 度が同じ書類"], nd),
              u"XP0-5": u"%d/%d" % (prod[u"道筋が同じ書類"], nd), u"XP0-6": u"%d/%d" % (mx[u"違いを見つけた数"], mx[u"作れた数"]),
              u"XP0-7": u"%d/%d" % (prod[u"原稿が元より大きい書類"], prod[u"書類"])}
    edge = {u"XP0-2": prod[u"断った書類"] == 0, u"XP0-3": prod[u"鳴り方が同じ書類"] == prod[u"書類"],             # 文書が「端の数」と書く 4 つ
            u"XP0-4": prod[u"2 度が同じ書類"] == nd and nd == prod[u"書類"], u"XP0-5": prod[u"道筋が同じ書類"] == nd and nd == prod[u"書類"]}
    cells = collections.OrderedDict()
    for k in j:
        if j[k]:
            cell = u"当たり(端の数)" if edge.get(k) else u"当たり"
        else:
            cell = u"**外れ**(%s)" % (u"上に外れた" if k == u"XP0-2" else u"下に外れた")      # 「以下」の境だけ上に外れる。ほかは「以上」「全部」の境で下に外れる
        cells[k] = (actual[k], cell)
    return cells


def verdict_problems(c):
    tot = totals(c.rec)
    j = judge(tot)
    want = expected_verdict_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XP0-\d)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XP0-1〜XP0-7 でない"]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    seal_rows = dict((ln.split(u"|")[1].strip().replace(u"(主)", u""), ln) for ln in sec4.splitlines() if re.match(r"^\| XP0-\d", ln))
    for k, cells in rows.items():
        if len(cells) != 3:
            out.append(u"%s の行の欄の数が違う" % k)
            continue
        if k == u"XP0-7":                                   # 文書の予測の字は封の字の要約。境の「50 本以上」が文書の欄と封の行の両方に在る
            if u"50 本以上" not in cells[0] or u"50 本以上" not in seal_rows[k]:
                out.append(u"XP0-7 の境の字(50 本以上)が文書の欄か封の行に無い")
        elif cells[0] not in sec4:
            out.append(u"%s の予測の字が封 §4 の表に無い: %s" % (k, cells[0]))
        if cells[1] != want[k][0]:
            out.append(u"%s の実測の字が記録から組んだ字と違う: %s" % (k, cells[1]))
        if cells[2] != want[k][1]:
            out.append(u"%s の判定が決め直した判定と違う: %s(決め直し: %s)" % (k, cells[2], want[k][1]))
    hits = sum(1 for v in j.values() if v)
    if u"- 当たり %d・外れ %d。" % (hits, len(j) - hits) not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = c.doc.split(u"## §1")[0]
    if u"当たり %d・外れ %d" % (hits, len(j) - hits) not in head:
        out.append(u"文書の頭の件数が決め直した件数と違う")
    misses = u"・".join(k for k, v in j.items() if not v)
    if u"外れは %s:" % misses not in head:
        out.append(u"文書の頭の外れの名が決め直した外れと違う")
    sec1, sec4doc = section(c.doc, u"## §1 ", u"## §2 "), section(c.doc, u"## §4 ", None)
    # 封 §6: XP0-6 が外れたら「比べ方が効いていない」を頭に書く / 当たりなら書かない
    if j[u"XP0-6"]:
        if u"比べ方が効いていない" in head or u"XP0-6 が当たりなので、封 §6 の「比べ方が効いていない」は書かない" not in sec1:
            out.append(u"XP0-6 が当たりなのに、封 §6 の「比べ方が効いていない」の扱いが文書と合わない")
    elif u"比べ方が効いていない" not in head:
        out.append(u"XP0-6 が外れたのに、頭に「比べ方が効いていない」が無い")
    # 封 §6: XP0-1 と XP0-6 がどちらも当たりなら次の便の候補を示す
    both = j[u"XP0-1"] and j[u"XP0-6"]
    if both != (u"人間に示す次の便の候補(封 §6。XP0-1 と XP0-6 がどちらも当たりなので示す)" in sec4doc):
        out.append(u"封 §6 の決め(XP0-1 と XP0-6 がどちらも当たりなら次の便の候補を示す)と文書 §4 が合わない")
    if both:
        s6 = section(c.seal, u"## §6 ", u"## §7 ")
        seg = s6[s6.index(u"(i) "):s6.index(u"どれにも")].strip()
        if seg not in sec4doc:
            out.append(u"§4 の次の便の候補 (i)(ii)(iii) が封 §6 の字と違う")
    # 封 §4 の自己点検の条: 全部同じ書類が 62 本 / 元の包みの概念の行が 1 以下の書類
    prod = tot[GROUPS[1]]
    fired = prod[u"全部同じ書類"] == prod[u"書類"] or prod[u"元の概念の行が 1 以下の書類"] > 0
    if fired:
        out.append(u"封 §4 の自己点検の条(全部同じ書類が 62 本・概念の行が 1 以下の書類)が発火している")
    if u"は、%d 本なので発火しない" % prod[u"全部同じ書類"] not in c.doc:
        out.append(u"文書の自己点検の言い切り(60 本なので発火しない)が記録の数と合わない")
    # 主の予測の「全部ではない」の中身: 同じでなかった書類は、概念の書き出しだけが同じでなく、fact と鳴り方は同じ
    odd = odd_docs(c)
    if len(odd) != prod[u"書類"] - prod[u"全部同じ書類"] or any(o[1] != (u"概念",) or not o[2] or not o[3] for o in odd):
        out.append(u"同じでなかった書類が、概念の書き出しだけが同じでなく fact と鳴り方は同じ、になっていない")
    return out


# ======================================================================================================
def expected_lines(c):
    tot = totals(c.rec)
    prod = tot[GROUPS[1]]
    out = [u"| 断った | %d |" % prod[u"断った書類"],
           u"| 全部同じ(タクソノミが同じ かつ fact が同じ) | %d |" % prod[u"全部同じ書類"],
           u"| タクソノミが同じ(書き出し 7 つが全部同じ) | %d |" % prod[u"タクソノミが同じ書類"],
           u"| fact が同じ | %d |" % prod[u"fact が同じ書類"],
           u"| 鳴り方が同じ | %d |" % prod[u"鳴り方が同じ書類"],
           u"| 組み直した包みで道具が最後まで走った | %d |" % prod[u"組み直した包みの 1 回の類ごと"][u"走った"],
           u"| 2 度組んで同じ | %d |" % prod[u"2 度が同じ書類"],
           u"| 道筋が同じ | %d |" % prod[u"道筋が同じ書類"],
           u"| 原稿の folder が元より大きい | %d |" % prod[u"原稿が元より大きい書類"]]
    kinds = tot[u"混ぜ物の種類ごと"]
    for k, label in zip(MIX_KINDS, (u"本文の数を変える", u"fact を抜く", u"ラベルを変える", u"計算の向きを返す")):
        r = kinds[k]
        out.append(u"| %s | %d | %d | %d |" % (label, r[u"作れた"], r[u"違いを見つけた"], r[u"鳴り方が違う"]))
    mx = tot[u"混ぜ物"]
    out.append(u"- 合計: 作れた %d・違いを見つけた %d・鳴り方が違う %d。" % (mx[u"作れた数"], mx[u"違いを見つけた数"], mx[u"鳴り方が違う数"]))
    return out


def rows_text(r):
    return u"・".join(u"%s %d" % (k, r[k]) for k in OUT_KEYS)


def expected_fragments(c):
    rec = c.rec
    tot = totals(rec)
    prod, dev, mx = tot[GROUPS[1]], tot[GROUPS[0]], tot[u"混ぜ物"]
    j = judge(tot)
    hits = sum(1 for v in j.values() if v)
    fo, og = prod[u"原稿の folder の合計"], prod[u"元の包みの合計"]
    f = []
    f.append(u"**予測 %d 本のうち %d 本が外れ(当たり %d・外れ %d)。**" % (len(j), len(j) - hits, hits, len(j) - hits))
    f.append(u"外れは XP0-7: 原稿の folder の bytes の合計が元より大きい書類は %d/%d" % (prod[u"原稿が元より大きい書類"], prod[u"書類"]))
    f.append(u"**主の予測 XP0-1 は当たりだが、全部ではない(%d/%d)。** 同じでなかった %d 本は" % (prod[u"全部同じ書類"], prod[u"書類"], prod[u"書類"] - prod[u"全部同じ書類"]))
    f.append(u"**端の数が 5 つ在る**: fact が同じ %d/%d・鳴り方が同じ %d/%d・2 度が同じ %d/%d・道筋が同じ %d/%d・断った %d/%d。" % (
        prod[u"fact が同じ書類"], prod[u"書類"], prod[u"鳴り方が同じ書類"], prod[u"書類"], prod[u"2 度が同じ書類"], prod[u"書類"], prod[u"道筋が同じ書類"], prod[u"書類"],
        prod[u"断った書類"], prod[u"書類"]))
    f.append(u"書類は便 XG0 と同じ %d 本" % rec[u"材料"][u"書類の本数"])
    f.append(u"本番は 1 回だけ走らせた")
    f.append(u"監査の席が全 %d 本の集計を数え直し" % rec[u"材料"][u"書類の本数"])
    f.append(u"- 書き出しごとに同じ書類: %s。" % u"・".join(u"%s %d" % (k, prod[u"書き出しごとに同じ書類"][k]) for k in OUT_KEYS))
    f.append(u"- 元の包みの file: `.htm` %d・タクソノミ %d。bytes は `.htm` %d・タクソノミ %d・合計 %d。" % (
        og[u"file"][u"htm"], og[u"file"][u"タクソノミ"], og[u"htm の bytes"], og[u"タクソノミの bytes"], og[u"bytes の合計"]))
    f.append(u"- 原稿の folder: 素の本文 %d file・%d bytes。本文の表 %d file・%d bytes。タクソノミの表 %d file・%d bytes。目次 %d file・%d bytes。合計 %d bytes。" % (
        fo[u"種類ごと"][u"素の本文"][u"file"], fo[u"種類ごと"][u"素の本文"][u"bytes"], fo[u"種類ごと"][u"本文の表"][u"file"], fo[u"種類ごと"][u"本文の表"][u"bytes"],
        fo[u"種類ごと"][u"タクソノミの表"][u"file"], fo[u"種類ごと"][u"タクソノミの表"][u"bytes"], fo[u"種類ごと"][u"目次"][u"file"], fo[u"種類ごと"][u"目次"][u"bytes"], fo[u"bytes の合計"]))
    f.append(u"- 組む命令の秒の合計: %.1f(%d 本)。" % (prod[u"組む命令の秒の合計"], prod[u"書類"]))
    f.append(u"- 元の包みの書き出しの行の数の合計(%d 本): %s。" % (prod[u"書類"], rows_text(prod[u"元の書き出しの行の数の合計"])))
    f.append(u"開発の 5 本: 断った %d・全部同じ %d・fact が同じ %d・鳴り方が同じ %d・2 度が同じ %d・道筋が同じ %d・原稿の folder が元より大きい %d。" % (
        dev[u"断った書類"], dev[u"全部同じ書類"], dev[u"fact が同じ書類"], dev[u"鳴り方が同じ書類"], dev[u"2 度が同じ書類"], dev[u"道筋が同じ書類"], dev[u"原稿が元より大きい書類"]))
    f.append(u"混ぜ物(開発の 5 本 × %d 種類 = %d 個):" % (len(MIX_KINDS), mx[u"混ぜ物の数"]))
    f.append(u"公開の道具が読むタクソノミの書き出しと fact が元と同じだった書類は %d 本・検査の鳴り方が同じだった書類は %d 本" % (prod[u"全部同じ書類"], prod[u"鳴り方が同じ書類"]))
    return f


def sanity_problems(c):
    u"""文書の言い切りが書類ごとの数に合う: 全部同じでない書類の中身・混ぜ物の種類ごと・端の数・時間の上限を超えた回・原稿の比。"""
    rec = c.rec
    tot = totals(rec)
    prod = tot[GROUPS[1]]
    out = []
    kinds = tot[u"混ぜ物の種類ごと"]
    if [[kinds[k][u"作れた"], kinds[k][u"違いを見つけた"], kinds[k][u"鳴り方が違う"]] for k in MIX_KINDS] != [[5, 5, 0], [5, 5, 0], [5, 5, 0], [5, 5, 5]]:
        out.append(u"混ぜ物の種類ごとの数が文書の表(5/5/0・5/5/0・5/5/0・5/5/5)と違う")
    if [d for d in rec[u"書類"] if any(d[k][u"時間の上限を超えた"] for k in (u"元の 1 回", u"組み直しの 1 回"))]:
        out.append(u"時間の上限を超えた回が在る")
    if [d[u"番号"] for d in rec[u"書類"] if d[u"断った"]]:
        out.append(u"断った書類が在る")
    if any(d[u"混ぜ物"] and not all(m[u"作った"] for m in d[u"混ぜ物"]) for d in rec[u"書類"]):
        out.append(u"作れなかった混ぜ物が在る(文書は作れた 20/20)")
    if tot[u"混ぜ物"][u"鳴り方が違う数"] != 5 or prod[u"全部同じ書類"] != 60:
        out.append(u"5 個・60 本が文書の言う数と違う")
    if prod[u"原稿が元より大きい書類"] != 0 or tot[GROUPS[0]][u"原稿が元より大きい書類"] != 0:
        out.append(u"原稿が元より大きい書類が在る(文書は 0)")
    ratios = [folder_total(d) / float(orig_total(d)) for d in rec[u"書類"][DEV_COUNT:]]
    if (round(min(ratios), 2), round(max(ratios), 2)) != (0.88, 0.93):
        out.append(u"書類ごとの原稿の folder の bytes の比が §3 の 0.88〜0.93 倍と違う")
    if [d[u"番号"] for d in rec[u"書類"] if not d[u"2 度が同じ"] or not d[u"道筋が同じ"]]:
        out.append(u"2 度が同じ・道筋が同じでない書類が在る(文書は 62/62)")
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


NUM_RE = re.compile(r"(?<![A-Za-z0-9_\-.])(\d[\d,]*(?:\.\d+)?)(?![A-Za-z0-9_])")


def doc_number_tokens(line):
    s = re.sub(r"`[^`]*`", u" ", line)
    s = re.sub(r"\b(?=[0-9]*[a-f])[0-9a-f]{8}\b", u" ", s)
    s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
    s = re.sub(r"XP0-\d", u" ", s)
    s = re.sub(r"XB0|XG0|XG1|XV0|XT0|XA0|XP0", u" ", s)
    s = re.sub(r"EC\d{4}[A-Z]", u" ", s)
    s = re.sub(r"§\d(?:-\d)?", u" ", s)
    return [m.group(1) for m in NUM_RE.finditer(s)]


def ints_in(o, acc):
    if isinstance(o, dict):
        for v in o.values():
            ints_in(v, acc)
    elif isinstance(o, list):
        for v in o:
            ints_in(v, acc)
    elif isinstance(o, float):
        acc.add(u"%.1f" % o)
    elif isinstance(o, int) and not isinstance(o, bool):
        acc.add(str(o))


def derived_numbers(c):
    tot = totals(c.rec)
    out = set()
    ints_in(tot, out)
    ints_in(pred_expected(tot), out)
    out |= set(str(x) for x in (58, 2, 50, 62, 67))                       # 封 §4 の境・分母
    prod = tot[GROUPS[1]]
    out.add(str(prod[u"書類"] - prod[u"全部同じ書類"]))
    return out


def doc_number_problems(c):
    allowed = set(STRUCTURAL) | derived_numbers(c)
    sec3 = section(c.doc, u"## §3 ", u"## §4 ")
    sec3_lines = sec3.splitlines()
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        if ln in sec3_lines:
            continue                                       # §3 は sec3_problems が小さい集合で見る
        for tok in doc_number_tokens(ln):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"文書の %d 行目の数 %s が記録から組んだ数の外: %s" % (i, tok, ln[:30]))
    return out


def sec3_problems(c):
    u"""§3 は記録に欄の無い読みの節。行(箇条)ごとの数の並びを SEC3_LINES(字で留めた)と照らす。3 桁以上の数・% が無い。"""
    s = section(c.doc, u"## §3 ", u"## §4 ")
    out = []
    bullets = [ln for ln in s.splitlines()[1:] if ln.strip()]
    if len(bullets) != len(SEC3_LINES):
        out.append(u"§3 の箇条の数 %d が留めた行の数 %d と違う" % (len(bullets), len(SEC3_LINES)))
    for key, nums in SEC3_LINES:
        hit = [ln for ln in bullets if key in ln]
        if len(hit) != 1:
            out.append(u"§3 に鍵の句の行が 1 つでない(%d 行): %s" % (len(hit), key))
            continue
        got = tuple(doc_number_tokens(hit[0]))
        if got != tuple(nums):
            out.append(u"§3 の行 %s の数の並び %s が留めた並び %s と違う" % (key, u",".join(got), u",".join(nums)))
    for ln in bullets:
        if not any(key in ln for key, _ in SEC3_LINES):
            out.append(u"§3 に留めていない行: %s" % ln[:20])
    if u"記録に欄の無い読み" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録に欄の無い読み」でない")
    if re.search(r"\d{3}|%|％", re.sub(r"`[^`]*`|\b(?=[0-9]*[a-f])[0-9a-f]{8}\b", u" ", s)):
        out.append(u"§3 に 3 桁以上の数か % が在る(記録に欄の無い読みに記録に無い数を書かない)")
    for p in (u"「軽い原稿で済む」とは読まない", u"直接掛けていない", u"便 XT0 と同じ"):
        if p not in s:
            out.append(u"§3 に字が無い: %s" % p)
    return out


QUOTED_CLAIM = re.compile(u"「[^」]*(?:作れる|検査に通る|専用の道具が要らない)[^」]*」")


def affirm_problems(c):
    u"""「作れる」「検査に通る」は、言えないことの引用(「…」の中)にしか無い。引用の在る行には「言えない」か「示していない」が在る。"""
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        if QUOTED_CLAIM.search(ln) and u"言えない" not in ln and u"示していない" not in ln:
            out.append(u"文書の %d 行目が引用の主張を否定の外で書いている" % i)
        rest = QUOTED_CLAIM.sub(u"", ln)
        for w in (u"作れる", u"作れます", u"検査に通る(?!こと|か)", u"検査に通ります", u"専用の道具が要らない"):
            if re.search(w, rest):
                out.append(u"文書の %d 行目に引用の外の字: %s" % (i, w))
    return out


# ======================================================================================================
def phrase_problems(c):
    out = [u"文書に要点の字が無い: %s" % p for p in PHRASES if p not in c.doc]
    out += [u"封 §7 に字が無い: %s" % p for p in SEAL7_PHRASES if p not in c.seal.split(u"## §7", 1)[-1]]
    return out


def head_problems(c):
    head = c.doc.split(u"## §1")[0]
    return [u"文書の頭(§1 の前)に無い: %s" % p for p in HEAD_PHRASES if p not in head]


def forbidden_problems(c):
    out = [u"文書に禁止語: %s" % w for w in FORBIDDEN_WORDS if w in c.doc]
    scan = re.sub(r"\b(?=[0-9]*[a-f])[0-9a-f]{8}\b", u" ", c.doc)
    if DOCID_FORM.search(scan):
        out.append(u"文書に docID の形が在る")
    if ECODE_FORM.search(scan):
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
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", record_clean_problems), (u"bound", bound_problems), (u"addendum", addendum_problems),
    (u"verdict", verdict_problems), (u"numbers", doc_number_problems), (u"frag", fragment_problems), (u"sanity", sanity_problems), (u"sec3", sec3_problems),
    (u"affirm", affirm_problems), (u"phrases", phrase_problems), (u"head", head_problems), (u"forbidden", forbidden_problems), (u"commits", doc_commit_problems)])


# ======================================================================================================
def blob_problems(root, prefix, at):
    out = []
    for rel, commit in at.items():
        r = subprocess.run(["git", "-C", root, "show", "%s:%s" % (commit, prefix + rel)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0:
            out.append(u"commit %s に %s が無い" % (commit, rel))
            continue
        with open(os.path.join(root, prefix, rel), "rb") as fh:
            if fh.read() != r.stdout:
                out.append(u"%s が commit %s の blob と違う" % (rel, commit))
    return out


def commit_problems(root=REPO):
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は c03a3348 が足し(1 commit)・追記と script と封の門は 465d0bc7 が足し・記録は 13b277e9 が足した。"""
    out = []
    for rel, want in ((SEAL_REL, [SEAL_COMMIT_SHORT]), (ADD_REL, [SCRIPT_COMMIT_SHORT]), (SCRIPT_REL, [SCRIPT_COMMIT_SHORT]), (SEAL_GATE_REL, [SCRIPT_COMMIT_SHORT]),
                      (RECORD_REL, [RECORD_COMMIT_SHORT])):
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
    u"""封 ⊏ script と封の門と追記 ⊏ 記録 ⊏ 結果の文書と門。未 commit は赤。"""
    out = list(PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL, SEAL_GATE_REL, ADD_REL], [RECORD_REL, DOC_REL, GATE_REL]))
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
(変異を実行する前に書いた予測。右 = 赤になるべき検査)
M1  記録の sha256 の写しを違う値に                                                    -> sha
M2  記録の「この script の sha256」を 1 字替える                                      -> sha
M3  記録の限界の欄の 1 行を消す                                                       -> sha
M4  書類 10 の元の fact の行の数を 1 増やす(集計は直さない)                            -> recount
M5  集計の本番だけの 62 本の全部同じ書類 60 → 59                                       -> recount
M6  予測の欄 XP0-1 の分母 62 → 61                                                     -> recount
M7  材料の書類の本数 67 → 68                                                          -> recount
M8  書類 10 の鳴り方が同じの旗を False に(符号は同じのまま・集計は直さない)             -> recount
M9  書類 20 の「タクソノミが同じ」の旗を False に(書き出しの旗は全部 True のまま)       -> recount
M10 書類 20 を断ったに(組み直しの 1 回を None・旗を False・集計は直さない)              -> recount
M10b 書類 20 の「2 度が同じ」を False に(集計は直さない)                               -> recount
M10c 書類 20 の「道筋が同じ」を False に(集計は直さない)                               -> recount
M10d 書類 20 の「原稿が元より大きい」を True に(bytes・集計は直さない)                  -> recount
M10e 書類 20 の原稿の folder の素の本文の bytes を 1 増やす(合計・集計は直さない)        -> recount
M11 記録に docid の欄を足す                                                           -> clean
M12 封の写しから「全部同じ書類は 58 本以上」を消す                                      -> bound
M13 封の写しから「XP0-1 と XP0-6 がどちらも当たりなら…」の字を消す                      -> bound
M14 封の写しから「全部同じ書類が 62 本だったら、先に自分の欠陥を疑う」を消す             -> bound
M15 追記の写しの「作れた 20・違いを見つけた 20」を 19 に                                 -> addendum
M16 文書の XP0-7 の判定「**外れ**(下に外れた)」を「当たり」に                           -> verdict
M17 文書の件数の行 当たり 6・外れ 1 → 当たり 7・外れ 0                                  -> verdict
M18 文書の XP0-3 のセルの「当たり(端の数)」を「当たり」に                                -> verdict
M19 文書の XP0-1 のセル 60/62 → 61/62                                                  -> verdict
M20 文書の XP0-7 のセルの「下に外れた」を「上に外れた」に                                -> verdict
M21 §4 の「人間に示す次の便の候補」の見出しの字を消す                                   -> verdict・phrases
M22 文書の自己点検の言い切り「60 本なので発火しない」の 60 を 61 に                      -> verdict
M23 本番の 9 書類の鳴り方を False にして整合(XP0-3 が外れ)                               -> verdict(recount は緑)
M24 開発の 5 本の混ぜ物 1 個の違いを見つけたを False にして整合(XP0-6 が外れ)            -> verdict(recount は緑)
M25 本番の 50 書類の「原稿が元より大きい」を True にして bytes も整合(XP0-7 が当たり)     -> verdict(recount は緑)
M26 同じでなかった書類を 1 本ふやす(書類 30 の役割型を同じでないにして整合)             -> verdict(recount は緑)
M26b 本番の書類 30 の「2 度が同じ」を False にして整合(XP0-4 が外れ)                      -> verdict(recount は緑)
M26c 本番の書類 30 の「道筋が同じ」を False にして整合(XP0-5 が外れ)                      -> verdict(recount は緑)
M26d 本番の書類 30・31・32 を断ったにして整合(XP0-2 が外れ・断った 3 本)                  -> verdict
M27 §2 の本番の行の fact が同じ 62 → 61                                                 -> frag
M28 文書の「概念 411621」を 411622 に                                                   -> frag・numbers
M29 文書の「合計 224798854 bytes」を 224798855 に                                       -> frag・numbers
M30 混ぜ物の表の「| 計算の向きを返す | 5 | 5 | 5 |」を「| 5 | 5 | 4 |」に                  -> frag
M31 文書に 9999 という数の言い切りを足す                                                -> numbers
M32 文書の「67 本の...」でなく「元の包みの file: `.htm` 927」を 928 に                    -> frag
M33 §2 の「組む命令の秒の合計: 22.7」を 22.8 に                                         -> frag・numbers
M34 書類 40 の「原稿が元より大きい」を True にして整合(文書は直さない)                   -> verdict・frag
M35 書類 40 の時間の上限を超えたを True に                                              -> sanity・recount
M36 混ぜ物の鳴り方が違うを種類の間で入れ替えて整合(N4 の 1 → 0、N1 の 1 つ → 1)         -> sanity(recount は緑)
M37 §3 に「7 本」を足す                                                               -> sec3
M38 §3 の「5 本を選び」の 5 を 4 に                                                    -> sec3
M39 §3 の「2 回組んだ」の 2 を 3 に                                                     -> sec3
M40 §3 の行を 1 つ丸ごと消す(「比べる元は」)                                             -> sec3
M41 §3 に 3 桁の数「100 本」を足す                                                      -> sec3
M42 §3 の「直接掛けていない」を消す                                                     -> sec3
M43 文書に「XBRL を作れる。」を引用の外で足す                                            -> affirm
M44 文書に「この道具は EDINET の検査に通る。」を足す                                      -> affirm
M45 §4 の「言えないこと」を消す                                                         -> phrases
M46 頭の「この便からは言えない」を消す                                                  -> head
M47 頭の「先に負けと限界を書く」を消す                                                  -> head
M48 頭の「封の門の変異 2 つは門で黙る」を消す                                           -> head
M49 頭の「LLM の席は呼んでいない」を消す                                               -> head
M50 文書に「保証」を足す                                                               -> forbidden
M51 文書に docID の形を足す                                                            -> forbidden
M52 文書の commit の字 13b277e9 を 13b277e8 に                                         -> commits
M53 文書の頭の「(60/62)」を「(59/62)」に                                                 -> frag
M54 頭の「予測 7 本のうち 1 本が外れ」を 2 本に                                          -> frag
M55 §4 の「残っているのは folder の中身を誰がどう決めるかで」を消す                       -> phrases
M56 §1 の予測の字「58 本以上」(XP0-1)を「59 本以上」に                                   -> verdict(封 §4 の表に無い)
M57 §1 の XP0-7 の予測の字の「50 本以上」を「40 本以上」に                                -> verdict
M58 §3 の「0.88〜0.93」の 0.93 を 0.95 に                                              -> sec3
M59 書類 41 の原稿の folder の bytes を元の bytes より大きくして整合(比の範囲が変わる)     -> sanity
"""


def rebuild(rec):
    u"""書類ごとの数はそのままに、集計と予測の判定に要る数を作り直す(整合した変更)。"""
    tot = totals(rec)
    rec[u"集計"] = tot
    rec[PRED_KEY] = pred_expected(tot)


def rep(c, old, new, attr="doc", count=1):
    s = getattr(c, attr)
    assert old in s, old
    setattr(c, attr, s.replace(old, new, count))


def drop_all(c, phrase):
    assert phrase in c.doc, phrase
    c.doc = c.doc.replace(phrase, u"X")


def add_doc(c, text):
    c.doc = c.doc + u"\n" + text + u"\n"


def add_sec3(c, text):
    rep(c, u"## §4 ", text + u"\n\n## §4 ")


def make_big(d):
    u"""原稿の folder の素の本文の bytes を増やして、元より大きくする(合計・旗を整合させる)。"""
    extra = orig_total(d) - folder_total(d) + 1
    d[u"原稿の folder"][u"素の本文"][u"bytes"] += extra
    d[u"原稿の folder"][u"合計 bytes"] += extra
    d[u"原稿が元より大きい"] = True


def m_8(c):
    c.rec[u"書類"][9][u"鳴り方が同じ"] = False


def m_9(c):
    c.rec[u"書類"][19][u"タクソノミが同じ"] = False


def m_10(c):
    d = c.rec[u"書類"][19]
    d[u"断った"] = True
    d[u"断った理由"] = u"x"
    d[u"組み直しの 1 回"] = None
    d[u"fact が同じ"] = False
    d[u"鳴り方が同じ"] = False


def m_10e(c):
    c.rec[u"書類"][19][u"原稿の folder"][u"素の本文"][u"bytes"] += 1


def m_23(c):
    for d in c.rec[u"書類"][DEV_COUNT:DEV_COUNT + 9]:
        d[u"鳴り方が同じ"] = False
        d[u"組み直しの 1 回"][u"符号ごとの行"] = collections.OrderedDict(list(d[u"組み直しの 1 回"][u"符号ごとの行"].items())[1:])
    rebuild(c.rec)


def m_24(c):
    c.rec[u"書類"][0][u"混ぜ物"][0][u"違いを見つけた"] = False
    c.rec[u"書類"][0][u"混ぜ物"][0][u"鳴り方が違う"] = False
    rebuild(c.rec)


def m_25(c):
    for d in c.rec[u"書類"][DEV_COUNT:DEV_COUNT + 50]:
        make_big(d)
    rebuild(c.rec)


def m_26(c):
    d = c.rec[u"書類"][29]
    d[u"書き出しが同じ"][u"役割型"] = False
    d[u"タクソノミが同じ"] = False
    d[u"全部同じ"] = False
    rebuild(c.rec)


def m_26b(c):
    c.rec[u"書類"][29][u"2 度が同じ"] = False
    rebuild(c.rec)


def m_26c(c):
    c.rec[u"書類"][29][u"道筋が同じ"] = False
    rebuild(c.rec)


def m_26d(c):
    for i in (29, 30, 31):
        d = c.rec[u"書類"][i]
        d[u"断った"] = True
        d[u"断った理由"] = u"x"
    rebuild(c.rec)


def m_34(c):
    make_big(c.rec[u"書類"][39])
    rebuild(c.rec)


def m_35(c):
    c.rec[u"書類"][39][u"組み直しの 1 回"][u"時間の上限を超えた"] = True


def m_36(c):
    docs = c.rec[u"書類"][:DEV_COUNT]
    a = [m for d in docs for m in d[u"混ぜ物"] if m[u"種類"] == MIX_KINDS[3] and m[u"鳴り方が違う"]][0]
    b = [m for d in docs for m in d[u"混ぜ物"] if m[u"種類"] == MIX_KINDS[0] and not m[u"鳴り方が違う"]][0]
    a[u"鳴り方が違う"] = False
    b[u"鳴り方が違う"] = True
    rebuild(c.rec)


def m_59(c):
    make_big(c.rec[u"書類"][40])
    rebuild(c.rec)


def m_40(c):
    lines = c.doc.splitlines()
    i = [k for k, ln in enumerate(lines) if u"**比べる元は" in ln][0]
    del lines[i]
    c.doc = u"\n".join(lines)


MUTATIONS = (
    (u"M1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"M3 記録の限界の欄の 1 行を消す", lambda c: c.rec.__setitem__(u"限界", c.rec[u"限界"][1:]), (u"sha",)),
    (u"M4 書類 10 の元の fact の行の数を 1 増やす", lambda c: c.rec[u"書類"][9].__setitem__(u"元の fact の行の数", c.rec[u"書類"][9][u"元の fact の行の数"] + 1), (u"recount",)),
    (u"M5 集計の全部同じ書類 60 → 59", lambda c: c.rec[u"集計"][GROUPS[1]].__setitem__(u"全部同じ書類", 59), (u"recount",)),
    (u"M6 予測の欄 XP0-1 の分母 62 → 61", lambda c: c.rec[PRED_KEY][PK[0]].__setitem__(u"分母", 61), (u"recount",)),
    (u"M7 材料の書類の本数を 68 に", lambda c: c.rec[u"材料"].__setitem__(u"書類の本数", 68), (u"recount",)),
    (u"M8 書類 10 の鳴り方が同じの旗を False に", m_8, (u"recount",)),
    (u"M9 書類 20 のタクソノミが同じの旗を False に", m_9, (u"recount",)),
    (u"M10 書類 20 を断ったに", m_10, (u"recount",)),
    (u"M10b 書類 20 の 2 度が同じを False に", lambda c: c.rec[u"書類"][19].__setitem__(u"2 度が同じ", False), (u"recount",)),
    (u"M10c 書類 20 の道筋が同じを False に", lambda c: c.rec[u"書類"][19].__setitem__(u"道筋が同じ", False), (u"recount",)),
    (u"M10d 書類 20 の原稿が元より大きいを True に", lambda c: c.rec[u"書類"][19].__setitem__(u"原稿が元より大きい", True), (u"recount",)),
    (u"M10e 書類 20 の素の本文の bytes を 1 増やす", m_10e, (u"recount",)),
    (u"M11 記録に docid の欄を足す", lambda c: c.rec[u"書類"][0].__setitem__(u"docid", u"x"), (u"clean",)),
    (u"M12 封の写しから「全部同じ書類は 58 本以上」を消す", lambda c: rep(c, u"全部同じ書類は 58 本以上", u"X", attr="seal"), (u"bound",)),
    (u"M13 封の写しから「XP0-1 と XP0-6 がどちらも当たりなら」の字を消す", lambda c: rep(c, u"XP0-1 と XP0-6 がどちらも当たりなら、次の便の候補を人間に示す", u"X", attr="seal"), (u"bound",)),
    (u"M14 封の写しから自己点検の条を消す", lambda c: rep(c, u"全部同じ書類が 62 本だったら、先に自分の欠陥を疑う", u"X", attr="seal"), (u"bound",)),
    (u"M15 追記の写しの「作れた 20・違いを見つけた 20」を 19 に", lambda c: rep(c, u"作れた 20・違いを見つけた 20", u"作れた 20・違いを見つけた 19", attr="add"), (u"addendum",)),
    (u"M16 XP0-7 の判定を当たりに", lambda c: rep(c, u"**外れ**(下に外れた)", u"当たり"), (u"verdict",)),
    (u"M17 件数の行を当たり 7・外れ 0 に", lambda c: rep(c, u"- 当たり 6・外れ 1。", u"- 当たり 7・外れ 0。"), (u"verdict",)),
    (u"M18 XP0-3 のセルの(端の数)を消す", lambda c: rep(c, u"| 62/62 | 当たり(端の数) |", u"| 62/62 | 当たり |"), (u"verdict",)),
    (u"M19 XP0-1 のセル 60/62 → 61/62", lambda c: rep(c, u"| 60/62 | 当たり |", u"| 61/62 | 当たり |"), (u"verdict",)),
    (u"M20 XP0-7 のセルの「下に外れた」を「上に外れた」に", lambda c: rep(c, u"**外れ**(下に外れた)", u"**外れ**(上に外れた)"), (u"verdict",)),
    (u"M21 §4 の次の便の候補の見出しの字を消す", lambda c: rep(c, u"人間に示す次の便の候補(封 §6。XP0-1 と XP0-6 がどちらも当たりなので示す)", u"X"), (u"verdict", u"phrases")),
    (u"M22 自己点検の言い切り「60 本なので発火しない」の 60 を 61 に", lambda c: rep(c, u"は、60 本なので発火しない", u"は、61 本なので発火しない"), (u"verdict",)),
    (u"M23 本番の 9 書類の鳴り方を False にして整合(XP0-3 が外れ)", m_23, (u"verdict",)),
    (u"M24 混ぜ物 1 個の違いを見つけたを False にして整合(XP0-6 が外れ)", m_24, (u"verdict",)),
    (u"M25 本番の 50 書類を元より大きくして整合(XP0-7 が当たり)", m_25, (u"verdict",)),
    (u"M26 同じでなかった書類を 1 本ふやして整合", m_26, (u"verdict",)),
    (u"M26b 書類 30 の 2 度が同じを False にして整合(XP0-4 が外れ)", m_26b, (u"verdict",)),
    (u"M26c 書類 30 の道筋が同じを False にして整合(XP0-5 が外れ)", m_26c, (u"verdict",)),
    (u"M26d 書類 30・31・32 を断ったにして整合(XP0-2 が外れ)", m_26d, (u"verdict",)),
    (u"M27 §2 の本番の行の fact が同じ 62 → 61", lambda c: rep(c, u"| fact が同じ | 62 |", u"| fact が同じ | 61 |"), (u"frag",)),
    (u"M28 「概念 411621」を 411622 に", lambda c: rep(c, u"概念 411621", u"概念 411622"), (u"frag", u"numbers")),
    (u"M29 「合計 224798854 bytes」を 224798855 に", lambda c: rep(c, u"合計 224798854 bytes", u"合計 224798855 bytes"), (u"frag", u"numbers")),
    (u"M30 混ぜ物の表の計算の向きを返すの行を 5 | 5 | 4 に", lambda c: rep(c, u"| 計算の向きを返す | 5 | 5 | 5 |", u"| 計算の向きを返す | 5 | 5 | 4 |"), (u"frag",)),
    (u"M31 文書に 9999 の言い切りを足す", lambda c: add_doc(c, u"fact の行は 9999 本に近い。"), (u"numbers",)),
    (u"M32 元の包みの file の `.htm` 927 を 928 に", lambda c: rep(c, u"`.htm` 927・", u"`.htm` 928・"), (u"frag",)),
    (u"M33 「組む命令の秒の合計: 22.7」を 22.8 に", lambda c: rep(c, u"組む命令の秒の合計: 22.7", u"組む命令の秒の合計: 22.8"), (u"frag", u"numbers")),
    (u"M34 書類 40 の原稿が元より大きいを True にして整合", m_34, (u"verdict", u"frag")),
    (u"M35 書類 40 の時間の上限を超えたを True に", m_35, (u"sanity", u"recount")),
    (u"M36 混ぜ物の鳴り方が違うを種類の間で入れ替えて整合", m_36, (u"sanity",)),
    (u"M37 §3 に「7 本」を足す", lambda c: add_sec3(c, u"- 別に 7 本で確かめた。"), (u"sec3",)),
    (u"M38 §3 の「5 本を選び」の 5 を 4 に", lambda c: rep(c, u"から 5 本を選び", u"から 4 本を選び"), (u"sec3",)),
    (u"M39 §3 の「2 回組んだ」の 2 を 3 に", lambda c: rep(c, u"別の process で 2 回組んだ", u"別の process で 3 回組んだ"), (u"sec3",)),
    (u"M40 §3 の行を 1 つ丸ごと消す", m_40, (u"sec3",)),
    (u"M41 §3 に 3 桁の数「100 本」を足す", lambda c: add_sec3(c, u"- 別の確かめは 100 本。"), (u"sec3",)),
    (u"M42 §3 の「直接掛けていない」を消す", lambda c: rep(c, u"直接掛けていない", u"X"), (u"sec3",)),
    (u"M43 文書に「XBRL を作れる。」を引用の外で足す", lambda c: add_doc(c, u"XBRL を作れる。"), (u"affirm",)),
    (u"M44 文書に「EDINET の検査に通る」を肯定で足す", lambda c: add_doc(c, u"この道具は EDINET の検査に通る。"), (u"affirm",)),
    (u"M45 §4 の「言えないこと」を消す", lambda c: drop_all(c, u"言えないこと"), (u"phrases",)),
    (u"M46 頭の「この便からは言えない」を消す", lambda c: rep(c, u"この便からは言えない", u"X"), (u"head",)),
    (u"M47 頭の「先に負けと限界を書く」を消す", lambda c: drop_all(c, u"先に負けと限界を書く"), (u"head",)),
    (u"M48 頭の「封の門の変異 2 つは門で黙る」を消す", lambda c: rep(c, u"封の門の変異 2 つは門で黙る", u"X"), (u"head",)),
    (u"M49 頭の「LLM の席は呼んでいない」を消す", lambda c: rep(c, u"LLM の席は呼んでいない", u"X"), (u"head",)),
    (u"M50 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"M51 文書に docID の形を足す", lambda c: add_doc(c, u"書類 S100ABCD。"), (u"forbidden",)),
    (u"M52 文書の commit の字 13b277e9 を 1 字替える", lambda c: rep(c, u"13b277e9", u"13b277e8", count=9), (u"commits",)),
    (u"M53 頭の「(60/62)」を「(59/62)」に", lambda c: rep(c, u"全部ではない(60/62)", u"全部ではない(59/62)"), (u"frag",)),
    (u"M54 頭の「予測 7 本のうち 1 本が外れ」を 2 本に", lambda c: rep(c, u"予測 7 本のうち 1 本が外れ", u"予測 7 本のうち 2 本が外れ"), (u"frag",)),
    (u"M55 §4 の「残っているのは folder の中身を誰がどう決めるかで」を消す", lambda c: rep(c, u"残っているのは folder の中身を誰がどう決めるかで", u"X"), (u"phrases",)),
    (u"M56 XP0-1 の予測の字「58 本以上」を「59 本以上」に", lambda c: rep(c, u"全部同じ書類は 58 本以上 |", u"全部同じ書類は 59 本以上 |"), (u"verdict",)),
    (u"M57 XP0-7 の予測の字の「50 本以上」を「40 本以上」に", lambda c: rep(c, u"元より大きい書類は 50 本以上 |", u"元より大きい書類は 40 本以上 |"), (u"verdict",)),
    (u"M58 §3 の「0.88〜0.93」の 0.93 を 0.95 に", lambda c: rep(c, u"0.93 倍", u"0.95 倍"), (u"sec3",)),
    (u"M59 書類 41 の原稿の folder を元より大きくして整合(比の範囲が変わる)", m_59, (u"sanity",)),
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
        tot = totals(self.c.rec)
        prod = tot[GROUPS[1]]
        self.assertEqual((62, 0, 60, 60, 62, 62, 62, 62, 0), (prod[u"書類"], prod[u"断った書類"], prod[u"全部同じ書類"], prod[u"タクソノミが同じ書類"], prod[u"fact が同じ書類"], prod[u"鳴り方が同じ書類"],
                                                           prod[u"2 度が同じ書類"], prod[u"道筋が同じ書類"], prod[u"原稿が元より大きい書類"]))
        self.assertEqual([((u"概念",), True, True)] * 2, [o[1:] for o in odd_docs(self.c)])
        self.assertEqual(collections.OrderedDict([(u"混ぜ物の数", 20), (u"作れた数", 20), (u"違いを見つけた数", 20), (u"鳴り方が違う数", 5)]), tot[u"混ぜ物"])
        self.assertEqual((5, 5, 5, 5, 5, 5, 0), (tot[GROUPS[0]][u"全部同じ書類"], tot[GROUPS[0]][u"fact が同じ書類"], tot[GROUPS[0]][u"鳴り方が同じ書類"], tot[GROUPS[0]][u"書類"],
                                                  tot[GROUPS[0]][u"2 度が同じ書類"], tot[GROUPS[0]][u"道筋が同じ書類"], tot[GROUPS[0]][u"原稿が元より大きい書類"]))
        self.assertEqual((65, 67, 67), (tot[GROUPS[2]][u"全部同じ書類"], tot[GROUPS[2]][u"fact が同じ書類"], tot[GROUPS[2]][u"鳴り方が同じ書類"]))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))
        self.assertEqual([], addendum_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(totals(self.c.rec))
        self.assertEqual(6, sum(1 for v in j.values() if v))
        self.assertEqual([u"XP0-7"], [k for k, v in j.items() if not v])

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))

    def test_d_2_the_table_rows_and_the_statements_equal_the_record(self):
        self.assertEqual([], fragment_problems(self.c))
        self.assertEqual([], sanity_problems(self.c))

    def test_d_3_section3_holds_only_the_pinned_small_numbers(self):
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

    def test_f_3_the_order_check_is_green_for_good_history_and_red_for_bad(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        r.put("measure/s.py")
        r.commit("measure/s.py")
        others = ["fix/r.json", "docs/d.md", "tests/g.py"]
        for f in others:
            r.put(f)
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py"], others))
        r.put("docs/new.md")
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py"], others + ["docs/new.md"]))

    def test_f_4_the_blob_check_is_green_for_an_untouched_file_and_red_for_a_changed_one(self):
        r = PR.Repo()
        r.put("measure/s.py")
        c1 = r.commit("measure/s.py")
        at = {"measure/s.py": c1[:8]}
        self.assertEqual([], blob_problems(r.d, PREFIX, at))
        with open(os.path.join(r.d, PREFIX, "measure/s.py"), "a", encoding="utf-8") as fh:
            fh.write(u"# 結果の便で足した 1 行\n")
        self.assertNotEqual([], blob_problems(r.d, PREFIX, at))
        self.assertNotEqual([], blob_problems(r.d, PREFIX, {"measure/s.py": "0000000"}))

    def test_f_5_the_blob_check_lists_the_five_frozen_files_at_their_commits(self):
        self.assertEqual([SEAL_REL, ADD_REL, SCRIPT_REL, SEAL_GATE_REL, RECORD_REL], list(BLOB_AT))
        self.assertEqual([SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT], list(BLOB_AT.values()))
        self.assertEqual((SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT), DOC_COMMITS)

    def test_f_6_the_commit_history_check_matches_the_real_history(self):
        self.assertEqual([], commit_problems())


class MutationTest(unittest.TestCase):
    def test_g_1_every_mutation_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = tuple(sha_file(r) for r in list(SHA_PIN) + [DOC_REL])
        base = Ctx()
        results = run_mutations(base)
        self.assertEqual(before, tuple(sha_file(r) for r in list(SHA_PIN) + [DOC_REL]))
        self.assertEqual(len(MUTATIONS), len(results))
        silent = [(n, k) for n, res in results for k, red in res if not red]
        self.assertEqual([], silent)
        self.assertGreaterEqual(len(MUTATIONS), 40)

    def test_g_2_the_unmutated_copy_is_green_on_every_check(self):
        c = Ctx().copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_g_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_verdict_does_not(self):
        for fn, key in ((m_23, u"XP0-3"), (m_24, u"XP0-6"), (m_25, u"XP0-7"), (m_26b, u"XP0-4"), (m_26c, u"XP0-5")):
            c = Ctx().copy()
            fn(c)
            self.assertEqual([], recount_problems(c))
            self.assertNotEqual([], verdict_problems(c))
            self.assertNotEqual(judge(totals(Ctx().rec))[key], judge(totals(c.rec))[key])

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数: XP0-1・XP0-3 は 58 本が当たり・57 本が外れ。XP0-2 は 2 本が当たり・3 本が外れ。XP0-7 は 50 本が当たり・49 本が外れ。XP0-4・XP0-5 は断らなかった書類の全部が当たり・1 本欠けたら外れ。XP0-6 は全部見つけたら当たり・1 個欠けたら外れ。"""
        for key, field in ((u"XP0-1", u"全部同じ"), (u"XP0-3", u"鳴り方が同じ")):
            for n, want in ((58, True), (57, False)):
                c = Ctx().copy()
                for i, d in enumerate(c.rec[u"書類"][DEV_COUNT:]):
                    d[field] = i < n
                rebuild(c.rec)
                self.assertEqual(want, judge(totals(c.rec))[key], (key, n))
        for n, want in ((2, True), (3, False)):
            c = Ctx().copy()
            for i, d in enumerate(c.rec[u"書類"][DEV_COUNT:]):
                d[u"断った"] = i < n
            rebuild(c.rec)
            self.assertEqual(want, judge(totals(c.rec))[u"XP0-2"], n)
        for n, want in ((50, True), (49, False)):
            c = Ctx().copy()
            for i, d in enumerate(c.rec[u"書類"][DEV_COUNT:]):
                d[u"原稿が元より大きい"] = i < n
            rebuild(c.rec)
            self.assertEqual(n, totals(c.rec)[GROUPS[1]][u"原稿が元より大きい書類"])
            self.assertEqual(want, judge(totals(c.rec))[u"XP0-7"], n)
        for key, field in ((u"XP0-4", u"2 度が同じ"), (u"XP0-5", u"道筋が同じ")):
            for lack, want in ((0, True), (1, False)):
                c = Ctx().copy()
                for i, d in enumerate(c.rec[u"書類"][DEV_COUNT:]):
                    d[field] = i >= lack
                rebuild(c.rec)
                self.assertEqual(want, judge(totals(c.rec))[key], (key, lack))
        for lack, want in ((0, True), (1, False)):
            c = Ctx().copy()
            flat = [m for d in c.rec[u"書類"][:DEV_COUNT] for m in d[u"混ぜ物"]]
            self.assertEqual(20, len(flat))
            for i, m in enumerate(flat):
                m[u"違いを見つけた"] = i >= lack
            rebuild(c.rec)
            self.assertEqual(want, judge(totals(c.rec))[u"XP0-6"], lack)

    def test_g_6_the_edge_cell_follows_the_record(self):
        u"""XP0-3 が 61/62 になれば「(端の数)」を期待しない。XP0-2 が 1 本でも断れば同じ。"""
        c = Ctx().copy()
        c.rec[u"書類"][DEV_COUNT][u"鳴り方が同じ"] = False
        rebuild(c.rec)
        self.assertEqual(u"当たり", expected_verdict_cells(c)[u"XP0-3"][1])
        c = Ctx().copy()
        c.rec[u"書類"][DEV_COUNT][u"断った"] = True
        rebuild(c.rec)
        self.assertEqual(u"当たり", expected_verdict_cells(c)[u"XP0-2"][1])

    def test_g_7_the_miss_direction_follows_the_bound(self):
        u"""XP0-2(「以下」の境)は 3 本断れば上に外れた。XP0-7(「以上」の境)は 49 本なら下に外れた。"""
        c = Ctx().copy()
        for i, d in enumerate(c.rec[u"書類"][DEV_COUNT:]):
            d[u"断った"] = i < 3
        rebuild(c.rec)
        self.assertEqual(u"**外れ**(上に外れた)", expected_verdict_cells(c)[u"XP0-2"][1])
        c = Ctx().copy()
        for i, d in enumerate(c.rec[u"書類"][DEV_COUNT:]):
            d[u"原稿が元より大きい"] = i < 49
        rebuild(c.rec)
        self.assertEqual(u"**外れ**(下に外れた)", expected_verdict_cells(c)[u"XP0-7"][1])


if __name__ == "__main__":
    unittest.main()
