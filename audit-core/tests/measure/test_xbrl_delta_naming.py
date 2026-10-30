# -*- coding: utf-8 -*-
u"""候補の要素の「当期末 − 前期末」が文中の金額と一致するかを、無改変の 296 行で機械で測った便の門。封 docs/XBRL_DELTA_NAMING_DIAG_SEAL_2026-10-30.md §2-1〜§2-6・§3(D-1〜D-12)・§5 の 5。

記録 ``fixtures/xbrl/delta_naming_2026-10-30.json``(``measure/xbrl_delta_naming_2026-10-30.py`` の出力)・文書 ``docs/XBRL_DELTA_NAMING_DIAG_2026-10-30.md``。
**この便の一致は『差分候補として機械的に名指せた』までで、出所として正しいとは判定しない(封 §4 の 1)。** 門もその言い方だけを許す。
封への日付つき追記 2(commit 31808fa。人間 2026-10-30): 先頭 2 書類の 38 行(位置 0〜37)は探索データ、残り 258 行(位置 38〜295)は未探索の検証データ。表は 全体・探索・検証 の 3 本。D-1〜D-12 の当否は封の字どおり 296 で判定し、探索と検証の実測を横に並べる(258 への予測は封に無い)。

  (a) 記録が在り、鍵が揃う(行 296・書類 30・配線の門・集計 3 本)。
  (b) 配線の門 (i)〜(vi) を、記録・``unnamed_fact``・``unnamed_candidate``・``fetched`` から数え直す。
  (c) 文書の表(``<!-- 門:start 名前 -->``)を記録から作り直して 1 行も違わない。門の外の散文の数には【門なし】の印が要る。
  (d) D-1〜D-12 の当否を、封の字(幅)と記録から求め直す。封の字(欄・予測・外れ方)と文書の当否の表の字が一致する。
  (e) 段・型・対照の段・前期残高の段・集計(全体・探索・検証)を、行の値から別実装で求め直して記録と一致させる。探索/検証の旗は位置から機械で決まり、38 + 258 = 296。
  (f) engine の sha16(``ENGINE_AT_MEASURE``・``ENGINE_DECLARED``)。
  (g) 偽物で赤(記録の段・型・対照の段・差・文書の当否と表の 1 字・封の幅の 1 字・文書に docID・語の一覧の 1 字・LATER_NAMING_FILES から外す・script の段の変異)。
  (h) docID・claim の id が封と文書に無い。
  (i) 順序: 実装 ``cb8612f`` < 封 ``68c0a3b`` < 封への追記の commit < script・記録・文書・門の commit。追跡されていない file は『足した commit が無い』で赤(skip にしない)。
  (j) 記録に原文・span・段落・窓の字・ラベルの字・理由の自由文が無い。
  (k) 296 行の (doc, id) が ``unnamed_fact`` の plain_rows と一致。
  (l) 語の一覧の正規表現・帯・窓・型の優先順が封 §2-3・§2-4 の字と script の定数で同じ(ast)。

**(i) は、script・記録・文書・門のどれかが commit される前は赤になる**(順序の門の「未 commit」分。skip にしない)。前例 ``test_xbrl_candidate_eyes.py`` と同じ扱い。
**変数名について**: 過去の門が tests/measure の行頭の名前を数えるので、この門は ``ENGINE_AT_MEASURE``・``ENGINE_DECLARED`` 以外の engine の留めの名前を行頭に置かない。この file は docID の字を持たない。
"""
import ast
import collections
import copy
import hashlib
import io
import json
import os
import re
import subprocess
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"

SEAL_REL = "docs/XBRL_DELTA_NAMING_DIAG_SEAL_2026-10-30.md"
DOC_REL = "docs/XBRL_DELTA_NAMING_DIAG_2026-10-30.md"
REC_REL = "fixtures/xbrl/delta_naming_2026-10-30.json"
SCRIPT_REL = "measure/xbrl_delta_naming_2026-10-30.py"
GATE_REL = "tests/measure/test_xbrl_delta_naming.py"
CAND_REL = "fixtures/xbrl/unnamed_candidate_2026-10-29.json"
UNNAMED_REL = "fixtures/xbrl/unnamed_fact_2026-10-29.json"
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
FRESH_REC_REL = "fixtures/xbrl/fresh/fresh_2026-10-21.json"
FRESH_SEAL_REL = "tests/measure/test_xbrl_fresh_seal.py"
INPUT_RELS = [UNNAMED_REL, CAND_REL, FETCHED_REL, FRESH_REC_REL]
SEAL, DOC, REC, SCRIPT = [os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL)]
SEAL_COMMIT_SHORT = "68c0a3b"
ADDENDUM_COMMIT_SHORT = "31808fa"
IMPL_COMMIT_SHORT = "cb8612f"
NOT_GATED = u"【門なし】"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
FORBIDDEN = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社", u"貴社の DB の誤り", u"取り戻す", u"勧め")
#: 文書に書いてはいけない言い方(一致を出所の正しさと言う)。封 §4 の 1
OVERCLAIM = (u"出所として正しい", u"正しい出所", u"出所と判定", u"出所を特定", u"出所を突き止め", u"仮説は正しかった", u"仮説が正しい", u"仮説は裏づけ", u"検証された")

NROWS = 296
NDOCS = 30
N_EXPLORE = 38
N_VERIFY = 258
EXPLORE_MAX_POS = 37
EXPLORE, VERIFY = u"探索", u"検証"
GROUPS = (u"全体", EXPLORE, VERIFY)
TYPE_ORDER = (u"増減の型", u"流量の型", u"区分の型", u"その他")
STAGES = (u"完全一致", u"許容差内", u"符号不一致", u"不一致", u"比較不能")
REASONS = (u"当期の値が一意でない", u"前期の枠なし", u"前期の枠の次元が違う", u"前期の fact なし", u"前期の値が一意でない", u"単位が違う", u"整数でない")
CONTROLS = (u"候補だけが一致", u"候補以外にも在る", u"候補は一致せず別の要素が一致", u"どれも一致しない", u"候補が比較不能")
PRIORS = (u"前期残高と完全一致", u"前期残高と許容差内", u"不一致", u"比較不能")
DIRECTIONS = (u"増", u"減", u"不明", u"なし")
UNIT_SCALE = {u"円": 1, u"千円": 1000, u"百万円": 1000000}
STD_PREFIXES = ("jppfs_cor", "jpcrp_cor", "jpigp_cor", "jpdei_cor")
POSITIONS = (0, 30, 60, 90, 120, 150, 180, 210, 240, 270)
TABLE_NAMES = ["pred", "wiring", "types", "stages", "sign", "control", "prior", "ten", "decimals", "engine_window", "elements"]

#: engine の sha16(測った時点の値。字で留める ― 測った事実。封 §0 の頭の字。engine は 0 行)。変えるなら宣言された遷移として下の ENGINE_DECLARED に足す。
ENGINE_AT_MEASURE = {
    "adapters/xbrl/extract.py": "3cf55966f12919f0", "adapters/xbrl/vocabulary.py": "7fbcfbf0e472f366", "adapters/xbrl/recipes.py": "52d645e713c53c1c",
    "adapters/xbrl/resolve.py": "a41043763c1d4073", "adapters/xbrl/comparators.py": "d8706338325e725b", "adapters/xbrl/verify_document.py": "6c76c8ade6c7b1c8",
    "adapters/xbrl/report_customer.py": "bdbaa00a419219fe",
}
#: 宣言された遷移 {file: (遷移の後の sha16, その遷移を宣言した封)}。今は 0 件。足すときは、封が履歴に在り、値が宣言の値のときだけ受け入れる。測った時点の値は消さない。
ENGINE_DECLARED = {}

#: 行頭に置いてはいけない名前(過去の門が数える)。この file の中で行頭に出る字を f の試験が見る
RESERVED_HEADS = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS", "LATER_FINGERPRINT", "FINGERPRINT_",
                  "LATER_TARGET", "LATER_FROZEN", "FROZEN_BUNDLE_AT_SEAL", "TARGET_AT_SEAL", "ENGINE_AT_SEAL")

REC_KEYS = [u"注意", u"封", u"全書類", u"HEAD の commit", u"DEFAULT_PROFILE", u"測る profile", u"engine sha16", u"engine の指紋", u"この script の sha256",
            u"読んだ入力の sha256", u"定数", u"書類の並び", u"書類ごと", u"配線の門", u"cache", u"所要秒", u"limits", u"行", u"集計", u"key_leaks"]
ROW_KEYS = [u"位置", u"書類の位置", u"doc", u"id", u"pointers", u"named の value", u"期", u"member", u"単位", u"帯の幅", u"文の値", u"当期の値", u"前期の値", u"差", u"差の符号",
            u"当期の decimals", u"前期の decimals", u"当期の unit", u"前期の unit", u"前期の fact 在り", u"比較不能の理由", u"大きさの段", u"段", u"型", u"旗",
            u"区分の語に当たった", u"区分のラベルに当たった", u"向き", u"両方在る", u"後の窓の先頭 4 字に engine の語", u"窓なし", u"文の全体に増減の語",
            u"対照 m", u"対照の分母", u"対照の段", u"前期残高の段", u"decimals が文の単位より粗い", u"10 行", u"探索/検証", u"配線"]
TALLY_KEYS = [u"types", u"stages", u"sign", u"control", u"prior", u"ten", u"decimals", u"engine_window", u"elements"]
BAD_KEYS = (u"理由", u"span", u"原文", u"subject", u"text", u"value", u"recomputed", u"窓", u"段落", u"文", u"ラベル", u"claim の value")


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    return json.loads(jtext(p))


def rload(rel):
    return jload(os.path.join(ROOT, rel))


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def sha64(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def yesno(b):
    return u"はい" if b else u"いいえ"


def n_of(n, d):
    return u"%d / %d" % (n, d)


def table(head, rows):
    lines = [u"| " + u" | ".join(head) + u" |", u"|" + u"|".join(u"---" for _ in head) + u"|"]
    for r in rows:
        lines.append(u"| " + u" | ".join(str(c) for c in r) + u" |")
    return lines


def inputs():
    u"""門が読む入力(記録以外)。"""
    return {"cand": rload(CAND_REL), "unn": rload(UNNAMED_REL), "fetched": rload(FETCHED_REL)}


# ----------------------------------------------------------------------------------------------------------------
# 封の字を読む
def seal_predictions(seal):
    u"""封 §3 の表の行 {名前: (欄, 予測, 外れ方)}(封の字のまま)。"""
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(D-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            cells = [c.strip() for c in body.split(u" | ")]
            assert len(cells) == 3, l
            out[m.group(1)] = tuple(cells)
    return out


def num(s):
    return int(s.replace(u",", u""))


def rng(s):
    m = re.match(r"^\s*(\d[\d,]*)(?:〜(\d[\d,]*))?", s)
    lo = num(m.group(1))
    return (lo, num(m.group(2)) if m.group(2) else lo)


def within(v, r):
    return r[0] <= v <= r[1]


def bolds(pred):
    return [rng(x) for x in re.findall(r"\*\*(\d[^*]*)\*\*", pred)]


def after_label(pred, label):
    m = re.search(re.escape(label) + r"\s*(\d+〜\d+)", pred)
    return rng(m.group(1))


def span_text(r):
    return u"%d〜%d" % r


def seal_regexes(seal):
    u"""封 §2-3 の表の語 {(型, 当てる所): 正規表現の字}。セルの 3 つ目の最初のバッククォートの中(``\\|`` は ``|`` に戻す)。"""
    out = {}
    for l in seal.splitlines():
        m = re.match(r"^\| (増減の型|流量の型|区分の型) \| ([^|]+?) \| `([^`]+)` ", l)
        if m:
            out[(m.group(1), m.group(2).strip())] = m.group(3).replace(u"\\|", u"|")
    return out


def seal_type_order(seal):
    m = re.search(r"`TYPE_ORDER = (\([^`]+\))`", seal)
    return ast.literal_eval(m.group(1))


def seal_direction_words(seal):
    m = re.search(r"後の窓の最初の一致が `([^`]+)` なら \*\*増\*\*、`([^`]+)` なら \*\*減\*\*", seal)
    return tuple(m.group(1).split(u"|")), tuple(m.group(2).split(u"|"))


# ----------------------------------------------------------------------------------------------------------------
# 別実装(記録の段・型・集計を読まず、行の値から求める)
def ref_sign(d):
    if d is None:
        return None
    return u"正" if d > 0 else (u"負" if d < 0 else u"0")


def ref_stage(d, t, w, direction):
    if d is None:
        return u"比較不能"
    e = abs(abs(d) - t)
    if e > w:
        return u"不一致"
    if d != 0:
        if direction == u"増" and d < 0:
            return u"符号不一致"
        if direction == u"減" and d > 0:
            return u"符号不一致"
    return u"完全一致" if e == 0 else u"許容差内"


def ref_mag(d, t, w):
    if d is None:
        return None
    e = abs(abs(d) - t)
    return u"完全一致" if e == 0 else (u"許容差内" if e <= w else u"不一致")


def ref_type(flags):
    if flags[u"増減"]:
        return TYPE_ORDER[0]
    if flags[u"流量"]:
        return TYPE_ORDER[1]
    if flags[u"区分"]:
        return TYPE_ORDER[2]
    return TYPE_ORDER[3]


def ref_control(reason, stage, m):
    if reason is not None:
        return CONTROLS[4]
    if stage in (u"完全一致", u"許容差内"):
        return CONTROLS[0] if m == 0 else CONTROLS[1]
    return CONTROLS[2] if m >= 1 else CONTROLS[3]


def ref_prior(pv, t, w):
    if pv is None:
        return PRIORS[3]
    e = abs(abs(pv) - t)
    return PRIORS[0] if e == 0 else (PRIORS[1] if e <= w else PRIORS[2])


def ref_coarse(dec, w):
    try:
        return 10.0 ** (-int(dec)) > w
    except (TypeError, ValueError):
        return False


def ref_split(pos):
    return EXPLORE if pos <= EXPLORE_MAX_POS else VERIFY


def d_of(row):
    return row[u"差"]


def row_problems(r):
    u"""1 行の内部整合(行の値から段・型・対照の段・前期残高の段などを求め直して記録と比べる)。問題の列。"""
    out = []
    p = r[u"位置"]
    t, w, d, unit = r[u"文の値"], r[u"帯の幅"], r[u"差"], r[u"単位"]
    if UNIT_SCALE.get(unit) != w:
        out.append(u"位置 %d の帯の幅が文の単位の 1 単位でない" % p)
    if r[u"比較不能の理由"] is not None and r[u"比較不能の理由"] not in REASONS:
        out.append(u"位置 %d の比較不能の理由が封の語でない" % p)
    if (r[u"比較不能の理由"] is None) != (d is not None):
        out.append(u"位置 %d の差と比較不能の理由が排他でない" % p)
    if d is not None:
        if r[u"当期の値"] is None or r[u"前期の値"] is None or r[u"当期の値"] - r[u"前期の値"] != d:
            out.append(u"位置 %d の差が 当期 − 前期 でない" % p)
    if r[u"差の符号"] != ref_sign(d):
        out.append(u"位置 %d の差の符号が差と食い違う" % p)
    if r[u"大きさの段"] != ref_mag(d, t, w):
        out.append(u"位置 %d の大きさの段が差・文の値・帯から求めた値と違う" % p)
    if r[u"向き"] not in DIRECTIONS:
        out.append(u"位置 %d の向きが封の語でない" % p)
    if r[u"段"] != ref_stage(d, t, w, r[u"向き"]):
        out.append(u"位置 %d の段が差・文の値・帯・向きから求めた値と違う" % p)
    if r[u"型"] != ref_type(r[u"旗"]):
        out.append(u"位置 %d の型が 3 つの旗の優先順から求めた値と違う" % p)
    if r[u"向き"] in (u"増", u"減") and not r[u"旗"][u"増減"]:
        out.append(u"位置 %d の向きが決まっているのに増減の旗が無い" % p)
    if r[u"旗"][u"区分"] and r[u"member"] not in (u"なし", u"単体"):
        out.append(u"位置 %d の区分の旗が member つきの枠に立っている" % p)
    if r[u"旗"][u"区分"] and not (r[u"区分の語に当たった"] or r[u"区分のラベルに当たった"]):
        out.append(u"位置 %d の区分の旗に語もラベルも当たっていない" % p)
    if r[u"窓なし"] and (r[u"区分の語に当たった"] or r[u"区分のラベルに当たった"] or r[u"文の全体に増減の語"]):
        out.append(u"位置 %d は窓なしなのに文の旗が立っている" % p)
    if r[u"対照の段"] != ref_control(r[u"比較不能の理由"], r[u"段"], r[u"対照 m"]):
        out.append(u"位置 %d の対照の段が候補の段と m から求めた値と違う" % p)
    if r[u"対照 m"] is not None and not (0 <= r[u"対照 m"] <= r[u"対照の分母"]):
        out.append(u"位置 %d の m が分母の外" % p)
    if r[u"前期残高の段"] != ref_prior(r[u"前期の値"], t, w):
        out.append(u"位置 %d の前期残高の段が前期の値・文の値・帯から求めた値と違う" % p)
    if r[u"decimals が文の単位より粗い"] != (ref_coarse(r[u"当期の decimals"], w) or ref_coarse(r[u"前期の decimals"], w)):
        out.append(u"位置 %d の『decimals が文の単位より粗い』が decimals から求めた値と違う" % p)
    if r[u"探索/検証"] != ref_split(p):
        out.append(u"位置 %d の探索/検証の旗が位置から決まる値と違う" % p)
    if r[u"10 行"] != (p in POSITIONS):
        out.append(u"位置 %d の 10 行の旗が封 9d847c0 の位置と違う" % p)
    # 枠の期と named の字
    ptr = r[u"pointers"]
    if not (isinstance(ptr, list) and len(ptr) == 1 and re.match(r"^xbrl:[^:@\s]+:[^@\s]+@CurrentYear(Instant|Duration)\S*$", ptr[0])):
        out.append(u"位置 %d の pointers の形が違う" % p)
    else:
        ctx = ptr[0].split(u"@", 1)[1]
        if (u"Instant" if ctx.startswith("CurrentYearInstant") else u"Duration") != r[u"期"]:
            out.append(u"位置 %d の期が枠の字と違う" % p)
        mem = u"なし" if u"_" not in ctx else (u"単体" if ctx.split(u"_", 1)[1] == u"NonConsolidatedMember" else u"それ以外")
        if mem != r[u"member"]:
            out.append(u"位置 %d の member が枠の字と違う" % p)
    return out


def rows_problems(rows):
    out = []
    for r in rows:
        out += row_problems(r)
    return out


def groups_of(rows):
    return collections.OrderedDict([(u"全体", list(rows)), (EXPLORE, [r for r in rows if r[u"位置"] <= EXPLORE_MAX_POS]),
                                    (VERIFY, [r for r in rows if r[u"位置"] > EXPLORE_MAX_POS])])


def med(xs):
    xs = sorted(xs)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def cntd(it):
    return dict(collections.Counter(it))


def ref_member(r):
    return u"なし" if r[u"member"] == u"なし" else u"あり"


def ref_element(r):
    name = r[u"pointers"][0].split(u"@", 1)[0][len(u"xbrl:"):]
    return name if name.split(u":", 1)[0] in STD_PREFIXES else u"(提出者別の要素)"


def ref_tally(rows):
    u"""script の ``tally`` を読まず、行から集計を求め直す(別実装)。"""
    def full(keys, it):
        c = collections.Counter(it)
        return dict((k, c.get(k, 0)) for k in keys)
    ms = [r for r in rows if r[u"段"] in (u"完全一致", u"許容差内")]
    ctl = [r for r in rows if r[u"対照 m"] is not None]
    dn = [r[u"対照の分母"] for r in ctl]
    ud = [r for r in rows if r[u"向き"] in (u"増", u"減")]
    ot = [r for r in rows if r[u"向き"] not in (u"増", u"減")]
    co = [r for r in rows if r[u"decimals が文の単位より粗い"]]
    ew = [r for r in rows if r[u"型"] == TYPE_ORDER[0]]

    def mbin(r):
        m = r[u"対照 m"]
        if m is None:
            return u"(対照なし)"
        return u"0" if m == 0 else (u"1" if m == 1 else (u"2〜5" if m <= 5 else u"6 以上"))
    return {
        u"types": {
            u"型の行数": full(TYPE_ORDER, (r[u"型"] for r in rows)),
            u"旗の組": cntd(u"増減%d 流量%d 区分%d" % (r[u"旗"][u"増減"], r[u"旗"][u"流量"], r[u"旗"][u"区分"]) for r in rows),
            u"向き": full(DIRECTIONS, (r[u"向き"] for r in rows)),
            u"両方在る": sum(1 for r in rows if r[u"両方在る"]),
            u"窓の外の旗": {u"窓なし(span が文の中に見つからない)": sum(1 for r in rows if r[u"窓なし"]),
                        u"文の全体に増減の語が在る": sum(1 for r in rows if r[u"文の全体に増減の語"]),
                        u"窓の中に増減の語が在る(増減の型)": sum(1 for r in rows if r[u"旗"][u"増減"]),
                        u"文の全体に在るが窓の中に無い": sum(1 for r in rows if r[u"文の全体に増減の語"] and not r[u"旗"][u"増減"])},
            u"型×期×member": cntd(u"%s / %s / member %s" % (r[u"型"], r[u"期"], ref_member(r)) for r in rows)},
        u"stages": {
            u"段": full(STAGES, (r[u"段"] for r in rows)),
            u"比較不能の理由": full(REASONS, (r[u"比較不能の理由"] for r in rows if r[u"比較不能の理由"])),
            u"型×段": cntd(u"%s / %s" % (r[u"型"], r[u"段"]) for r in rows),
            u"期×段": cntd(u"%s / %s" % (r[u"期"], r[u"段"]) for r in rows),
            u"単位×段": cntd(u"%s / %s" % (r[u"単位"], r[u"段"]) for r in rows),
            u"member×段": cntd(u"member %s / %s" % (ref_member(r), r[u"段"]) for r in rows)},
        u"sign": {
            u"向きが増・減の行の向きと差の符号": cntd(u"%s / %s" % (r[u"向き"], ref_sign(r[u"差"]) or u"比較不能") for r in ud),
            u"向きが不明・なしの行の差の符号": full((u"正", u"負", u"0", u"比較不能"), (ref_sign(r[u"差"]) or u"比較不能" for r in ot)),
            u"符号不一致": sum(1 for r in rows if r[u"段"] == u"符号不一致")},
        u"control": {
            u"対照の段": full(CONTROLS, (r[u"対照の段"] for r in rows)),
            u"型×対照の段": cntd(u"%s / %s" % (r[u"型"], r[u"対照の段"]) for r in rows),
            u"対照の分母": {u"最小": min(dn) if dn else None, u"最大": max(dn) if dn else None, u"中央値": med(dn)},
            u"m の分布": full((u"0", u"1", u"2〜5", u"6 以上", u"(対照なし)"), (mbin(r) for r in rows)),
            u"m が 6 以上の行": sum(1 for r in ctl if r[u"対照 m"] >= 6),
            u"m が 1 以上で単位が円の行": sum(1 for r in ctl if r[u"対照 m"] >= 1 and r[u"単位"] == u"円")},
        u"prior": {
            u"前期残高の段": full(PRIORS, (r[u"前期残高の段"] for r in rows)),
            u"差の段×前期残高の段": cntd(u"%s / %s" % (r[u"段"], r[u"前期残高の段"]) for r in rows),
            u"両方に一致": sum(1 for r in ms if r[u"前期残高の段"] in (PRIORS[0], PRIORS[1]))},
        u"ten": [[r[u"位置"], r[u"型"], r[u"段"], r[u"対照の段"], r[u"前期残高の段"]] for r in rows if r[u"10 行"]],
        u"decimals": {
            u"組": cntd(u"%s / %s" % (r[u"当期の decimals"], r[u"前期の decimals"]) for r in rows),
            u"文の単位より粗い行": len(co),
            u"文の単位より粗い行の段": cntd(r[u"段"] for r in co)},
        u"engine_window": {
            u"増減の型の行": cntd(u"後の窓の先頭 4 字に engine の語 %s / %s / 前期の fact %s" % (u"あり" if r[u"後の窓の先頭 4 字に engine の語"] else u"なし", r[u"期"],
                                                                                       u"あり" if r[u"前期の fact 在り"] else u"なし") for r in ew),
            u"D-7 の行(Instant・増減の型・後の窓の先頭 4 字に engine の語・前期の fact あり)":
                sum(1 for r in ew if r[u"期"] == u"Instant" and r[u"後の窓の先頭 4 字に engine の語"] and r[u"前期の fact 在り"])},
        u"elements": [{u"位置": r[u"位置"], u"pointers": [ref_element(r)], u"期": r[u"期"], u"member": ref_member(r), u"単位": r[u"単位"], u"段": r[u"段"]} for r in ms],
    }


#: 封の追記 2 の 5: 探索 38 行の数(封 §6-2 で見た数。字で留める ― 一致しなければ赤)
EXPLORE_PIN = {
    u"型": {u"増減の型": 10, u"流量の型": 13, u"区分の型": 0, u"その他": 15},
    u"段": {u"完全一致": 0, u"許容差内": 4, u"符号不一致": 1, u"不一致": 33, u"比較不能": 0},
    u"対照の段": {u"候補だけが一致": 4, u"候補以外にも在る": 0, u"候補は一致せず別の要素が一致": 1, u"どれも一致しない": 33, u"候補が比較不能": 0},
    u"前期残高の段": {u"前期残高と完全一致": 0, u"前期残高と許容差内": 0, u"不一致": 38, u"比較不能": 0},
}


def explore_problems(rec):
    ex = groups_of(rec[u"行"])[EXPLORE]
    got = {u"型": cntd(r[u"型"] for r in ex), u"段": cntd(r[u"段"] for r in ex), u"対照の段": cntd(r[u"対照の段"] for r in ex), u"前期残高の段": cntd(r[u"前期残高の段"] for r in ex)}
    out = []
    for k, want in EXPLORE_PIN.items():
        have = dict((x, got[k].get(x, 0)) for x in want)
        if have != want or sum(got[k].values()) != N_EXPLORE:
            out.append(u"探索 38 行の『%s』が封 §6 の数と違う: %s" % (k, have))
    if rec[u"配線の門"].get(u"探索 38 行の数が封 §6 の数と一致(追記 2 の 5)") is not True:
        out.append(u"記録の配線の門に探索 38 行の一致が無いか偽")
    return out


def tally_problems(rec):
    out = []
    got = json.loads(json.dumps(rec[u"集計"]))
    if list(got) != list(GROUPS):
        return [u"集計の鍵が 全体・探索・検証 でない: %s" % list(got)]
    for g, rows in groups_of(rec[u"行"]).items():
        want = json.loads(json.dumps(ref_tally(rows)))
        if sorted(got[g]) != sorted(TALLY_KEYS):
            out.append(u"集計『%s』の節が違う" % g)
            continue
        for k in want:
            if got[g][k] != want[k]:
                out.append(u"集計『%s』の『%s』が行から数え直した値と違う" % (g, k))
    return out


# ----------------------------------------------------------------------------------------------------------------
# (a)(b)(j)(k)
def check_a(rec):
    out = []
    if list(rec) != REC_KEYS:
        return [u"記録の鍵が違う: %s" % list(rec)]
    rows = rec[u"行"]
    if len(rows) != NROWS:
        out.append(u"行が %d でない" % NROWS)
    if [r[u"位置"] for r in rows] != list(range(NROWS)):
        out.append(u"行の位置が 0〜295 の昇順でない")
    for r in rows:
        if list(r) != ROW_KEYS:
            out.append(u"行の鍵が違う(位置 %s)" % r.get(u"位置"))
            break
    if rec[u"全書類"] is not True:
        out.append(u"全書類の記録でない(試走の出力)")
    if len(rec[u"書類の並び"]) != NDOCS or list(rec[u"書類ごと"]) != rec[u"書類の並び"]:
        out.append(u"書類が 30 でないか並びが書類ごとと違う")
    g = rec[u"配線の門"]
    if g.get(u"通った") is not True:
        out.append(u"記録の配線の門が通っていない")
    if rec[u"key_leaks"] != []:
        out.append(u"key_leaks が空でない")
    c = rec[u"cache"]
    if not (c[u"変化なし"] and c[u"開始"] == c[u"終了"] and c[u"開始"][u"edinet"][u"件数"] == 281 and c[u"開始"][u"edinet-fresh-2026-10-21"][u"件数"] == 40):
        out.append(u"cache の前後が 281 / 40 で不変でない")
    if rec[u"DEFAULT_PROFILE"] != "P27" or rec[u"測る profile"] != "P27C":
        out.append(u"DEFAULT_PROFILE が P27 でないか、測る profile が P27C でない")
    if rec[u"封"] != {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT, u"追記 2 の commit": ADDENDUM_COMMIT_SHORT}:
        out.append(u"記録の封の欄が封の file・commit・追記 2 の commit と違う")
    if rec[u"engine sha16"] != ENGINE_AT_MEASURE:
        out.append(u"記録の engine sha16 が留めと違う")
    return out


def check_k(rec, inp):
    u"""296 行の (doc, id) と順序が unnamed_fact の plain_rows と一致する。"""
    out = []
    unn = inp["unn"]
    order = unn[u"書類(出てくる順)"]
    pos = dict((d, i) for i, d in enumerate(order))
    want = sorted(unn["plain_rows"], key=lambda r: (pos[r["doc"]], r["id"]))
    rows = rec[u"行"]
    if len(want) != NROWS or len(rows) != NROWS:
        return [u"行が 296 でない"]
    for i, (w_, r) in enumerate(zip(want, rows)):
        if (r["doc"], r["id"], r[u"pointers"][0], r[u"named の value"], r[u"単位"], r[u"文の値"], r[u"位置"], r[u"書類の位置"]) != \
           (w_["doc"], w_["id"], w_["named"], w_[u"named の value"], w_["unit"], w_[u"文の値"], i, pos[w_["doc"]]):
            out.append(u"位置 %d の行が plain_rows の並びの行と違う" % i)
    if len(set((r["doc"], r["id"]) for r in rows)) != NROWS:
        out.append(u"(doc, id) が重複している")
    if rec[u"書類の並び"] != order:
        out.append(u"書類の並びが plain_rows の並びと違う")
    return out


def check_b(rec, inp):
    u"""配線の門 (i)〜(vi) を門が自分で数え直す。"""
    out = []
    cand = inp["cand"]
    cand_rows = dict(((r["doc"], r["id"]), r["candidate"]) for r in cand[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"] if r["doc"] in set(cand[u"注入の書類(出てくる順)"]))
    unn = inp["unn"]
    plain = dict(((r["doc"], r["id"]), r) for r in unn["plain_rows"])
    sha30 = dict((r["docID"], r["sha256"]) for r in inp["fetched"][u"取得した書類"] if r.get(u"使う"))
    rows = rec[u"行"]
    n1 = sum(1 for r in rows if (r["doc"], r["id"]) in plain and (r["doc"], r["id"]) in cand_rows
             and plain[(r["doc"], r["id"])]["named"] == r[u"pointers"][0] == cand_rows[(r["doc"], r["id"])]["pointer"]
             and plain[(r["doc"], r["id"])][u"named の value"] == r[u"named の value"] == cand_rows[(r["doc"], r["id"])]["value"])
    n2 = sum(1 for d in rec[u"書類の並び"] if rec[u"書類ごと"][d][u"zip の sha256"] == sha30.get(d) == unn[u"書類ごと"][d][u"材料の sha256"])
    n3 = sum(1 for r in rows if r[u"配線"][u"(iii) 当期の値の集合に named の value"] is True)
    n4 = sum(1 for r in rows if all(r[u"配線"][k] is True for k in (u"(iv) claim がちょうど 1 つ", u"(iv) 候補の pointer・value が記録と同じ", u"(iv) 文の値と unit が記録と同じ")))
    g = rec[u"配線の門"]
    want = {u"(i) 296 行の (doc, id, named, named の value) が記録と候補の記録の両方と一致": [n1, NROWS],
            u"(ii) ZIP の sha256 が取得の記録と材料の記録の両方と一致": [n2, NDOCS],
            u"(iii) instance の named の値の集合に named の value": [n3, NROWS],
            u"(iv) claim 1 つ・候補一致・文の値と unit 一致": [n4, NROWS]}
    for k, v in want.items():
        if g.get(k) != v:
            out.append(u"配線の門『%s』の記録 %s が数え直し %s と違う" % (k, g.get(k), v))
        if v[0] != v[1]:
            out.append(u"配線の門『%s』が全部通っていない(%s)" % (k, v))
    if g.get(u"(v) engine の sha16 7 本が封の頭の字と一致・adapters と core に未 commit の変更なし") is not True:
        out.append(u"(v) が通っていない")
    if g.get(u"(vi) cache の件数と名前の一覧の sha256 が開始時と終了時で同じ") is not True:
        out.append(u"(vi) が通っていない")
    if g.get(u"窓なしの行数(止めない)") != sum(1 for r in rows if r[u"窓なし"]):
        out.append(u"窓なしの行数が行から数え直した値と違う")
    if g.get(u"当期の値が一意でない行数(止めない)") != sum(1 for r in rows if r[u"比較不能の理由"] == REASONS[0]):
        out.append(u"当期の値が一意でない行数が行から数え直した値と違う")
    # 行の claim の単位が文の単位で、文の値 = 記録の文の値
    for r in rows:
        if plain[(r["doc"], r["id"])]["unit"] != r[u"単位"] or plain[(r["doc"], r["id"])][u"文の値"] != r[u"文の値"]:
            out.append(u"位置 %d の単位か文の値が plain_rows と違う" % r[u"位置"])
            break
    return out


def walk_keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            for x in walk_keys(v):
                yield x
    elif isinstance(o, list):
        for v in o:
            for x in walk_keys(v):
                yield x


def walk_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            for x in walk_strings(v):
                yield x
    elif isinstance(o, list):
        for v in o:
            for x in walk_strings(v):
                yield x


def check_j(rec):
    u"""記録に原文・span・段落・窓の字・ラベルの字・理由の自由文が無い。"""
    out = []
    keys = set(k for k in walk_keys(rec) if isinstance(k, str))
    for k in BAD_KEYS:
        if k in keys:
            out.append(u"記録に鍵『%s』がある" % k)
    for s in walk_strings(rec):
        if len(s) > 400:
            out.append(u"記録に 400 字を超える字がある(自由文の疑い)")
    for r in rec[u"行"]:
        for s in walk_strings(dict((k, v) for k, v in r.items() if k != u"pointers")):
            if u"。" in s or len(s) > 60:
                out.append(u"行に文の字らしいものがある(位置 %d)" % r[u"位置"])
                break
    got = rec[u"読んだ入力の sha256"]
    if sorted(got) != sorted(INPUT_RELS):
        out.append(u"読んだ入力の sha256 の file が %d 個でない" % len(INPUT_RELS))
    for rel in INPUT_RELS:
        if got.get(rel) != sha64(rel):
            out.append(u"%s の sha256 が記録の写しと違う(読み直しの元が動いた)" % rel)
    return out


# ----------------------------------------------------------------------------------------------------------------
# (l) 語の一覧・帯・窓・型の優先順
def script_consts(src):
    tree = ast.parse(src)
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            v = n.value
            try:
                if isinstance(v, ast.Call) and ast.unparse(v.func) == "re.compile":
                    out[n.targets[0].id] = ast.literal_eval(v.args[0])
                else:
                    out[n.targets[0].id] = ast.literal_eval(v)
            except Exception:
                pass
    return out


def words_problems(src, seal):
    out = []
    k = script_consts(src)
    sr = seal_regexes(seal)
    pairs = (("UPDOWN_AFTER_RE", (u"増減の型", u"後の窓")), ("UPDOWN_BEFORE_RE", (u"増減の型", u"前の窓")), ("FLOW_RE", (u"流量の型", u"前の窓・後の窓")),
             ("SEGMENT_WORD_RE", (u"区分の型", u"文")))
    for name, key in pairs:
        if sr.get(key) is None:
            out.append(u"封 §2-3 の表に %s の語が見つからない" % (key,))
        elif k.get(name) != sr[key]:
            out.append(u"%s が封 §2-3 の語の一覧と違う" % name)
    if tuple(k.get("TYPE_ORDER", ())) != seal_type_order(seal):
        out.append(u"TYPE_ORDER が封 §5 の字と違う")
    up, down = seal_direction_words(seal)
    if tuple(k.get("UP_WORDS", ())) != up or tuple(k.get("DOWN_WORDS", ())) != down:
        out.append(u"UP_WORDS・DOWN_WORDS が封 §2-3 の向きの語と違う")
    if k.get("TOL_UNITS") != 1:
        out.append(u"TOL_UNITS が 1(文の単位の 1 単位)でない")
    if k.get("AFTER_WINDOW") != 10:
        out.append(u"AFTER_WINDOW が封 §2-3 の末尾 10 字でない")
    if k.get("EXPLORE_MAX_POS") != EXPLORE_MAX_POS:
        out.append(u"EXPLORE_MAX_POS が 37 でない")
    if list(k.get("POSITIONS", ())) != list(POSITIONS):
        out.append(u"POSITIONS が封 9d847c0 の位置と違う")
    if k.get("ENGINE_AFTER4_RE") != u"増加|減少|増|減":
        out.append(u"ENGINE_AFTER4_RE が封 §2-6 の 10 の語と違う")
    if k.get("NROWS") != NROWS or k.get("NDOCS") != NDOCS:
        out.append(u"NROWS・NDOCS が 296・30 でない")
    for need in (u"文の単位の 1 単位", u"末尾 10 字", u"増減 → 流量 → 区分 → その他"):
        if need not in seal:
            out.append(u"封に『%s』の字が無い(門の前提が動いた)" % need)
    return out


def load_script_funcs(src):
    u"""script の定数と純関数(``tol_of_unit``・``magnitude_of``・``stage_of`` ほか)だけを取り出して実行する(重い import をしない)。"""
    tree = ast.parse(src)
    allow = re.compile(r"^(TOL_UNITS|S_[A-Z]+|C_[A-Z]+|P_[A-Z]+|D_[A-Z]+|R_[A-Z_]+|TYPE_ORDER|STAGES|MAGS|CONTROLS|PRIORS|REASONS|DIRECTIONS)$")
    funcs = ("tol_of_unit", "sign_of", "magnitude_of", "stage_of", "prior_stage_of", "control_stage_of", "type_of", "coarse_of", "split_of")
    body = []
    for n in tree.body:
        if isinstance(n, ast.Assign):
            names = []
            for t in n.targets:
                names += [x.id for x in ast.walk(t) if isinstance(x, ast.Name)]
            if names and all(allow.match(x) for x in names):
                body.append(n)
            elif names and all(x in ("EXPLORE_MAX_POS", "EXPLORE_VERIFY") for x in names):
                body.append(n)
            elif len(names) == 2 and names == ["EXPLORE", "VERIFY"]:
                body.append(n)
        elif isinstance(n, ast.FunctionDef) and n.name in funcs:
            body.append(n)
    mod = ast.Module(body=body, type_ignores=[])
    ns = {"V": types.SimpleNamespace(UNIT_SCALE={u"百万円": 1e6, u"千円": 1e3, u"億円": 1e8, u"兆円": 1e12, u"円": 1}), "re": re}
    ns.update({"EXPLORE_MAX_POS": EXPLORE_MAX_POS})
    exec(compile(mod, "<script-funcs>", "exec"), ns)
    return ns


def behaviour_problems(ns):
    u"""段・前期残高・対照の段・型・帯・粗さの振る舞いの表(封 §2-3〜§2-5)。外れた行の説明の列。"""
    out = []

    def call(f, *a):
        try:
            return f(*a)
        except Exception as e:
            return ("EXC", repr(e))
    st = ns["stage_of"]
    cases = [((None, 5000, 1000, u"なし"), u"比較不能"), ((5000, 5000, 1000, u"なし"), u"完全一致"), ((-5000, 5000, 1000, u"なし"), u"完全一致"),
             ((5001, 5000, 1000, u"なし"), u"許容差内"), ((4999, 5000, 1000, u"なし"), u"許容差内"), ((5500, 5000, 1000, u"なし"), u"許容差内"), ((6000, 5000, 1000, u"なし"), u"許容差内"), ((6001, 5000, 1000, u"なし"), u"不一致"),
             ((6500, 5000, 1000, u"なし"), u"不一致"), ((4000, 5000, 1000, u"なし"), u"許容差内"), ((3999, 5000, 1000, u"なし"), u"不一致"),
             ((-5000, 5000, 1000, u"増"), u"符号不一致"), ((5000, 5000, 1000, u"減"), u"符号不一致"), ((5000, 5000, 1000, u"増"), u"完全一致"),
             ((-5000, 5000, 1000, u"減"), u"完全一致"), ((5500, 5000, 1000, u"減"), u"符号不一致"), ((-6500, 5000, 1000, u"増"), u"不一致"),
             ((-5000, 5000, 1000, u"不明"), u"完全一致"), ((5000, 5000, 1000, u"不明"), u"完全一致"), ((0, 5000, 1000, u"増"), u"不一致"),
             ((-5500, 5000, 1000, u"増"), u"符号不一致")]
    for a, want in cases:
        if call(st, *a) != want:
            out.append(u"stage_of%s が %s でない" % (a, want))
    pr = ns["prior_stage_of"]
    for a, want in (((None, 5000, 1000), u"比較不能"), ((5000, 5000, 1000), u"前期残高と完全一致"), ((-5000, 5000, 1000), u"前期残高と完全一致"),
                    ((6000, 5000, 1000), u"前期残高と許容差内"), ((6001, 5000, 1000), u"不一致"), ((4000, 5000, 1000), u"前期残高と許容差内"), ((3999, 5000, 1000), u"不一致")):
        if call(pr, *a) != want:
            out.append(u"prior_stage_of%s が %s でない" % (a, want))
    cs = ns["control_stage_of"]
    for a, want in (((False, u"比較不能", None), u"候補が比較不能"), ((False, u"不一致", 3), u"候補が比較不能"), ((True, u"完全一致", 0), u"候補だけが一致"),
                    ((True, u"許容差内", 2), u"候補以外にも在る"), ((True, u"符号不一致", 0), u"どれも一致しない"), ((True, u"符号不一致", 1), u"候補は一致せず別の要素が一致"),
                    ((True, u"不一致", 3), u"候補は一致せず別の要素が一致"), ((True, u"不一致", 0), u"どれも一致しない"), ((True, u"許容差内", 0), u"候補だけが一致")):
        if call(cs, *a) != want:
            out.append(u"control_stage_of%s が %s でない" % (a, want))
    ty = ns["type_of"]
    for a, want in (((True, True, True), u"増減の型"), ((True, False, False), u"増減の型"), ((False, True, True), u"流量の型"), ((False, True, False), u"流量の型"),
                    ((False, False, True), u"区分の型"), ((False, False, False), u"その他")):
        if call(ty, *a) != want:
            out.append(u"type_of%s が %s でない" % (a, want))
    tol = ns["tol_of_unit"]
    for a, want in (((u"円",), 1), ((u"千円",), 1000), ((u"百万円",), 1000000)):
        if call(tol, *a) != want:
            out.append(u"tol_of_unit%s が %s でない" % (a, want))
    co = ns["coarse_of"]
    for a, want in (((u"-6", 1000), True), ((u"-3", 1000), False), ((u"-3", 1), True), ((u"INF", 1), False), ((None, 1), False), ((u"0", 1), False), ((u"-6", 1000000), False)):
        if call(co, *a) != want:
            out.append(u"coarse_of%s が %s でない" % (a, want))
    sp = ns["split_of"]
    for a, want in (((0,), u"探索"), ((37,), u"探索"), ((38,), u"検証"), ((295,), u"検証")):
        if call(sp, *a) != want:
            out.append(u"split_of%s が %s でない" % (a, want))
    return out


def script_rows_problems(rows, ns):
    u"""script の純関数を記録の行に当てて、記録の段・型・対照の段・前期残高の段・大きさの段と一致するか。"""
    out = []
    for r in rows:
        d, t, w = r[u"差"], r[u"文の値"], r[u"帯の幅"]
        if ns["tol_of_unit"](r[u"単位"]) != w:
            out.append(u"位置 %d: tol_of_unit が記録の帯の幅と違う" % r[u"位置"])
        if ns["stage_of"](d, t, w, r[u"向き"]) != r[u"段"]:
            out.append(u"位置 %d: script の stage_of が記録の段と違う" % r[u"位置"])
        if d is not None and ns["magnitude_of"](d, t, w) != r[u"大きさの段"]:
            out.append(u"位置 %d: script の magnitude_of が記録の大きさの段と違う" % r[u"位置"])
        if ns["prior_stage_of"](r[u"前期の値"], t, w) != r[u"前期残高の段"]:
            out.append(u"位置 %d: script の prior_stage_of が記録と違う" % r[u"位置"])
        if ns["control_stage_of"](r[u"比較不能の理由"] is None, r[u"段"], r[u"対照 m"]) != r[u"対照の段"]:
            out.append(u"位置 %d: script の control_stage_of が記録と違う" % r[u"位置"])
        if ns["type_of"](r[u"旗"][u"増減"], r[u"旗"][u"流量"], r[u"旗"][u"区分"]) != r[u"型"]:
            out.append(u"位置 %d: script の type_of が記録と違う" % r[u"位置"])
        if ns["split_of"](r[u"位置"]) != r[u"探索/検証"]:
            out.append(u"位置 %d: script の split_of が記録と違う" % r[u"位置"])
    return out


# ----------------------------------------------------------------------------------------------------------------
# (d) D-1〜D-12 の当否
def measures(rows):
    u"""行の集合から、D-1〜D-12 の判定と文に使う量(全体でも探索でも検証でも同じ関数)。"""
    ms = [r for r in rows if r[u"段"] in (u"完全一致", u"許容差内")]
    q = {}
    q["n"] = len(rows)
    q["nowin"] = sum(1 for r in rows if r[u"窓なし"])
    q["found"] = len(rows) - q["nowin"]
    q["types"] = dict((t_, sum(1 for r in rows if r[u"型"] == t_)) for t_ in TYPE_ORDER)
    na = [r for r in rows if r[u"段"] == u"比較不能"]
    q["na"] = len(na)
    q["na_inst"] = sum(1 for r in na if r[u"期"] == u"Instant")
    q["na_dur"] = sum(1 for r in na if r[u"期"] == u"Duration")
    q["reasons"] = dict((k, sum(1 for r in rows if r[u"比較不能の理由"] == k)) for k in REASONS)
    q["exact"] = sum(1 for r in rows if r[u"段"] == u"完全一致")
    q["tol"] = sum(1 for r in rows if r[u"段"] == u"許容差内")
    q["match"] = len(ms)
    q["match_type"] = dict((t_, sum(1 for r in ms if r[u"型"] == t_)) for t_ in TYPE_ORDER)
    q["sign"] = sum(1 for r in rows if r[u"段"] == u"符号不一致")
    q["d7"] = sum(1 for r in rows if r[u"型"] == TYPE_ORDER[0] and r[u"期"] == u"Instant" and r[u"後の窓の先頭 4 字に engine の語"] and r[u"前期の fact 在り"])
    q["ctl"] = dict((c, sum(1 for r in rows if r[u"対照の段"] == c)) for c in CONTROLS)
    q["median_den"] = med([r[u"対照の分母"] for r in rows if r[u"対照の分母"] is not None])
    q["prior_exact"] = sum(1 for r in rows if r[u"前期残高の段"] == PRIORS[0])
    q["prior_tol"] = sum(1 for r in rows if r[u"前期残高の段"] == PRIORS[1])
    q["both"] = sum(1 for r in ms if r[u"前期残高の段"] in (PRIORS[0], PRIORS[1]))
    ten = [r for r in rows if r[u"10 行"]]
    q["ten_n"] = len(ten)
    q["ten_updown"] = sum(1 for r in ten if r[u"型"] == TYPE_ORDER[0])
    q["ten_match"] = sum(1 for r in ten if r[u"段"] in (u"完全一致", u"許容差内"))
    q["ten_na"] = sum(1 for r in ten if r[u"段"] == u"比較不能")
    q["unit_match"] = dict((u, sum(1 for r in ms if r[u"単位"] == u)) for u in (u"円", u"千円", u"百万円"))
    tols = [r for r in rows if r[u"段"] == u"許容差内"]
    q["tol_coarse"] = sum(1 for r in tols if r[u"decimals が文の単位より粗い"])
    q["m6"] = sum(1 for r in rows if r[u"対照 m"] is not None and r[u"対照 m"] >= 6)
    q["m1yen"] = sum(1 for r in rows if r[u"対照 m"] is not None and r[u"対照 m"] >= 1 and r[u"単位"] == u"円")
    return q


def judge_text(k, q):
    u"""D-k の実測の字(行の集合 ``q`` から。全体・探索・検証で同じ形)。"""
    if k == "D-1":
        return u"span が文の中に見つかる行 %d(窓なし %d)" % (q["found"], q["nowin"])
    if k == "D-2":
        t_ = q["types"]
        return u"増減の型 %d・流量の型 %d・区分の型 %d・その他 %d" % tuple(t_[x] for x in TYPE_ORDER)
    if k == "D-3":
        r_ = q["reasons"]
        return (u"比較不能 %d(Instant %d・Duration %d)。理由別: 前期の枠なし %d・前期の枠の次元が違う %d・前期の fact なし %d・値が一意でない(当期・前期)%d・単位が違う %d・整数でない %d"
                % (q["na"], q["na_inst"], q["na_dur"], r_[REASONS[1]], r_[REASONS[2]], r_[REASONS[3]], r_[REASONS[0]] + r_[REASONS[4]], r_[REASONS[5]], r_[REASONS[6]]))
    if k == "D-4":
        return u"完全一致 %d・許容差内 %d(合計 %d)" % (q["exact"], q["tol"], q["match"])
    if k == "D-5":
        m_ = q["match_type"]
        return u"完全一致 + 許容差内の型別: 増減の型 %d・流量の型 %d・区分の型 %d・その他 %d" % tuple(m_[x] for x in TYPE_ORDER)
    if k == "D-6":
        return u"符号不一致 %d" % q["sign"]
    if k == "D-7":
        return u"Instant・増減の型・後の窓の先頭 4 字に engine の語・前期の fact あり %d" % q["d7"]
    if k == "D-8":
        c_ = q["ctl"]
        md = q["median_den"]
        return (u"対照: 候補だけが一致 %d・候補以外にも在る %d・候補は一致せず別の要素が一致 %d・どれも一致しない %d・候補が比較不能 %d。対照の分母の中央値 %s"
                % (c_[CONTROLS[0]], c_[CONTROLS[1]], c_[CONTROLS[2]], c_[CONTROLS[3]], c_[CONTROLS[4]], u"なし" if md is None else (u"%d" % md if float(md).is_integer() else u"%.1f" % md)))
    if k == "D-9":
        return u"前期残高との一致: 完全一致 %d・許容差内 %d。差と前期残高の両方に一致 %d" % (q["prior_exact"], q["prior_tol"], q["both"])
    if k == "D-10":
        return u"人の目の便の 10 行のうちこの集合の %d 行: 増減の型 %d・一致(完全 + 許容)%d・比較不能 %d" % (q["ten_n"], q["ten_updown"], q["ten_match"], q["ten_na"])
    if k == "D-11":
        u_ = q["unit_match"]
        return (u"一致(完全 + 許容)の単位: 円 %d・千円 %d・百万円 %d。許容差内 %d 行のうち decimals が文の単位より粗い行 %d"
                % (u_[u"円"], u_[u"千円"], u_[u"百万円"], q["tol"], q["tol_coarse"]))
    if k == "D-12":
        return u"m が 6 以上の行 %d・m が 1 以上で単位が円の行 %d" % (q["m6"], q["m1yen"])
    raise AssertionError(k)


def judge(rec, seal):
    u"""{名前: (実測の字(296)、当たりか)}。当たりか: True / False / None(判定しない)。296 行で封の字どおりに判定する。"""
    P = seal_predictions(seal)
    rows = rec[u"行"]
    q = measures(rows)
    g = rec[u"配線の門"]
    out = collections.OrderedDict()
    b = bolds(P["D-1"][1])
    wiring_ok = g.get(u"通った") is True
    out["D-1"] = (judge_text("D-1", q), wiring_ok and within(q["found"], b[0]))
    b = [after_label(P["D-2"][1], x) for x in (u"増減の型 **", u"流量の型 **", u"区分の型 **", u"その他 **")] if False else bolds(P["D-2"][1])
    t_ = q["types"]
    top = max(t_.values())
    ok = all(within(t_[x], b[i]) for i, x in enumerate(TYPE_ORDER)) and t_[TYPE_ORDER[0]] == top and sum(1 for v in t_.values() if v == top) == 1
    out["D-2"] = (judge_text("D-2", q), ok)
    b = bolds(P["D-3"][1])
    r_ = q["reasons"]
    w_nofact = r_[REASONS[3]]
    others = [v for kk, v in r_.items() if kk != REASONS[3]]
    ok = (within(q["na"], b[0]) and within(q["na_inst"], b[1]) and within(q["na_dur"], b[2])
          and within(r_[REASONS[1]], after_label(P["D-3"][1], u"前期の枠なし")) and within(r_[REASONS[0]] + r_[REASONS[4]], after_label(P["D-3"][1], u"一意でない(当期・前期)"))
          and within(r_[REASONS[5]], after_label(P["D-3"][1], u"単位が違う")) and within(r_[REASONS[6]], b[3])
          and all(w_nofact > v for v in others))
    out["D-3"] = (judge_text("D-3", q), ok)
    b = bolds(P["D-4"][1])
    out["D-4"] = (judge_text("D-4", q), within(q["match"], b[0]) and within(q["exact"], b[1]) and within(q["tol"], b[2]))
    b = bolds(P["D-5"][1])
    m_ = q["match_type"]
    ok = all(within(m_[x], b[i]) for i, x in enumerate(TYPE_ORDER)) and m_[TYPE_ORDER[0]] >= max(m_.values())
    out["D-5"] = (judge_text("D-5", q), ok)
    b = bolds(P["D-6"][1])
    out["D-6"] = (judge_text("D-6", q), within(q["sign"], b[0]))
    b = bolds(P["D-7"][1])
    out["D-7"] = (judge_text("D-7", q), within(q["d7"], b[0]))
    b = bolds(P["D-8"][1])
    c_ = q["ctl"]
    md = q["median_den"]
    ok = (within(c_[CONTROLS[0]], b[0]) and within(c_[CONTROLS[1]], b[1]) and within(c_[CONTROLS[2]], b[2]) and within(c_[CONTROLS[3]], b[3])
          and c_[CONTROLS[4]] == q["na"] and c_[CONTROLS[0]] <= c_[CONTROLS[2]] and md is not None and b[4][0] <= md <= b[4][1])
    out["D-8"] = (judge_text("D-8", q), ok)
    b = bolds(P["D-9"][1])
    out["D-9"] = (judge_text("D-9", q), within(q["prior_exact"], b[0]) and within(q["prior_tol"], b[1]) and within(q["both"], b[2]))
    b = bolds(P["D-10"][1])
    out["D-10"] = (judge_text("D-10", q), within(q["ten_updown"], b[0]) and within(q["ten_match"], b[1]) and within(q["ten_na"], b[2]))
    b = bolds(P["D-11"][1])
    u_ = q["unit_match"]
    if q["tol"] == 0:
        coarse_ok = None
    else:
        coarse_ok = q["tol_coarse"] * 2 > q["tol"]
    ok = within(u_[u"円"], b[0]) and within(u_[u"千円"], b[1]) and within(u_[u"百万円"], b[2]) and (coarse_ok is not False)
    out["D-11"] = (judge_text("D-11", q), ok)
    b = bolds(P["D-12"][1])
    out["D-12"] = (judge_text("D-12", q), within(q["m6"], b[0]) and within(q["m1yen"], b[1]))
    return out


def hit_word(b):
    return u"**判定しない**" if b is None else (u"**当たり**" if b else u"**外れ**")


def judge_group_texts(rec):
    u"""探索 38・検証 258 の実測の字 {名前: (探索の字, 検証の字)}。当否は付けない(258 への予測は封に無い)。"""
    gr = groups_of(rec[u"行"])
    qe, qv = measures(gr[EXPLORE]), measures(gr[VERIFY])
    return dict((k, (judge_text(k, qe), judge_text(k, qv))) for k in ["D-%d" % i for i in range(1, 13)])


# ----------------------------------------------------------------------------------------------------------------
# (c) 文書の表
def flatten(sec):
    u"""集計の節を [(項目, 値)] に平らにする(辞書は『親 / 子』)。"""
    out = []
    for k, v in sec.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                out.append((u"%s / %s" % (k, k2), v2))
        else:
            out.append((k, v))
    return out


def fmt(v):
    if v is None:
        return u"なし"
    if isinstance(v, float):
        return u"%d" % v if v.is_integer() else u"%.1f" % v
    return str(v)


def three_cols(tal, name, scalar_keys=None):
    u"""集計 3 本(全体・探索・検証)の節 ``name`` を 1 つの表にする。"""
    flats = [collections.OrderedDict(flatten(tal[g][name])) for g in GROUPS]
    labels = []
    for f in flats:
        for k in f:
            if k not in labels:
                labels.append(k)
    rows = []
    for k in labels:
        rows.append([k] + [fmt(f.get(k, 0)) for f in flats])
    return table([u"項目", u"全体 (%d)" % NROWS, u"探索 (%d)" % N_EXPLORE, u"検証 (%d)" % N_VERIFY], rows)


def render_blocks(rec, seal):
    u"""文書の門の表 {名前: 行の列}。記録と封から作る。"""
    B = collections.OrderedDict()
    P = seal_predictions(seal)
    J = judge(rec, seal)
    G = judge_group_texts(rec)
    rows = []
    for k, (field, pred, miss) in P.items():
        text, hit = J[k]
        rows.append([u"**%s**" % k, field, pred, miss, text, hit_word(hit), G[k][0], G[k][1]])
    B["pred"] = table([u"#", u"欄", u"予測(封の字)", u"外れ方(封の字)", u"実測 全体 296(記録から)", u"当たり外れ(296 で判定)", u"探索 38 の実測(当否なし)", u"検証 258 の実測(当否なし)"], rows)
    g = rec[u"配線の門"]
    cc = rec[u"cache"]
    gr = groups_of(rec[u"行"])
    rows = [[k, n_of(*g[k])] for k in (u"(i) 296 行の (doc, id, named, named の value) が記録と候補の記録の両方と一致", u"(ii) ZIP の sha256 が取得の記録と材料の記録の両方と一致",
                                      u"(iii) instance の named の値の集合に named の value", u"(iv) claim 1 つ・候補一致・文の値と unit 一致")]
    rows.append([u"(v) engine の sha16 7 本が封の頭の字と一致・adapters と core に未 commit の変更なし", yesno(g[u"(v) engine の sha16 7 本が封の頭の字と一致・adapters と core に未 commit の変更なし"])])
    rows.append([u"(vi) cache の件数と名前の一覧の sha256 が開始時と終了時で同じ", yesno(g[u"(vi) cache の件数と名前の一覧の sha256 が開始時と終了時で同じ"])])
    rows.append([u"窓なしの行数(止めない)", g[u"窓なしの行数(止めない)"]])
    rows.append([u"当期の値が一意でない行数(止めない)", g[u"当期の値が一意でない行数(止めない)"]])
    rows.append([u"探索 38 行の数が封 §6 の数と一致(追記 2 の 5)", yesno(g[u"探索 38 行の数が封 §6 の数と一致(追記 2 の 5)"])])
    rows.append([u"配線の門が通って script は記録を書いた", yesno(g[u"通った"])])
    rows.append([u"cache の前後(edinet・edinet-fresh-2026-10-21)", u"%d・%d から %d・%d(変化なし: %s)" % (cc[u"開始"][u"edinet"][u"件数"], cc[u"開始"][u"edinet-fresh-2026-10-21"][u"件数"],
                                                                                        cc[u"終了"][u"edinet"][u"件数"], cc[u"終了"][u"edinet-fresh-2026-10-21"][u"件数"], yesno(cc[u"変化なし"]))])
    rows.append([u"DEFAULT_PROFILE・測る profile", u"%s・%s" % (rec[u"DEFAULT_PROFILE"], rec[u"測る profile"])])
    rows.append([u"行の数(全体・探索・検証)", u"%d・%d・%d(探索 + 検証 = 全体: %s)" % (len(gr[u"全体"]), len(gr[EXPLORE]), len(gr[VERIFY]), yesno(len(gr[EXPLORE]) + len(gr[VERIFY]) == len(gr[u"全体"])))])
    for rel in ENGINE_AT_MEASURE:
        rows.append([u"`%s` の sha16" % rel, u"`%s`" % rec[u"engine sha16"][rel]])
    B["wiring"] = table([u"配線の門", u"値"], rows)
    for name in ("types", "stages", "sign", "control", "prior"):
        B[name] = three_cols(rec[u"集計"], name)
    ten = rec[u"集計"][u"全体"][u"ten"]
    B["ten"] = table([u"位置", u"型", u"段", u"対照の段", u"前期残高の段", u"探索/検証"], [r + [ref_split(r[0])] for r in ten])
    for name in ("decimals", "engine_window"):
        B[name] = three_cols(rec[u"集計"], name)
    el = rec[u"集計"][u"全体"][u"elements"]
    B["elements"] = table([u"位置", u"要素", u"期", u"member", u"単位", u"段", u"探索/検証"],
                          [[e[u"位置"], e[u"pointers"][0], e[u"期"], e[u"member"], e[u"単位"], e[u"段"], ref_split(e[u"位置"])] for e in el])
    assert list(B) == TABLE_NAMES
    return B


BLOCK_RE = re.compile(r"<!-- 門:start (\S+) -->\n(.*?)\n<!-- 門:end -->", re.S)


def doc_blocks(doc):
    out = collections.OrderedDict()
    for m in BLOCK_RE.finditer(doc):
        if m.group(1) in out:
            raise AssertionError(u"同じ名前の門の表が 2 つ: " + m.group(1))
        out[m.group(1)] = m.group(2).split(u"\n")
    return out


def check_c(rec, seal, doc):
    u"""文書の表を記録から作り直して比べる。問題の列。"""
    out = []
    try:
        B = render_blocks(rec, seal)
    except Exception as e:      # 記録が壊れていれば作り直せない(それも赤)
        return [u"記録から表を作れない: %r" % (e,)]
    got = doc_blocks(doc)
    if list(got) != list(B):
        return [u"文書の門の表の名前と順が違う: %s" % list(got)]
    for k, lines in B.items():
        if got[k] != lines:
            out.append(u"文書の表『%s』が記録から作った表と違う" % k)
    return out


DOC_LITERALS = (u"差分候補として機械的に名指せた", u"為替換算", u"売却", u"除却", u"組替え", u"連結範囲の変更", u"探索データ", u"未探索検証データ", u"258 行への予測は封に無い",
                u"人間の条件 (7)", u"次の封の候補", u"2026-10-30", u"edinetdb-p27", u"engine は 0 行", u"追記", NOT_GATED)


def unit_off(rec, k):
    u"""一致(完全一致 + 許容差内)の行のうち、|差| − 文の値 がちょうど k 単位(k = ±1)の行の数。"""
    return sum(1 for r in rec[u"行"] if r[u"段"] in (u"完全一致", u"許容差内") and abs(r[u"差"]) - r[u"文の値"] == k * r[u"帯の幅"])


def fact_lines(rec):
    u"""文書に 1 つずつ在るべき、記録から求めた事実の行(散文。数は【門なし】だが、門が字面で照らす)。"""
    gr = groups_of(rec[u"行"])
    qa, qe, qv = measures(gr[u"全体"]), measures(gr[EXPLORE]), measures(gr[VERIFY])
    return [
        u"一致(完全一致 + 許容差内)の行は 全体 %d・探索 %d・検証 %d。符号不一致は 全体 %d・探索 %d・検証 %d。比較不能は 全体 %d・探索 %d・検証 %d。"
        % (qa["match"], qe["match"], qv["match"], qa["sign"], qe["sign"], qv["sign"], qa["na"], qe["na"], qv["na"]) + NOT_GATED,
        u"対照で『候補だけが一致』の行は 全体 %d・探索 %d・検証 %d。" % (qa["ctl"][CONTROLS[0]], qe["ctl"][CONTROLS[0]], qv["ctl"][CONTROLS[0]]) + NOT_GATED,
        u"一致(完全一致 + 許容差内)の行のうち、|差| − 文の値 がちょうど +1 単位の行は %d、ちょうど −1 単位の行は %d、それ以外は %d(全体)。"
        % (unit_off(rec, 1), unit_off(rec, -1), qa["match"] - unit_off(rec, 1) - unit_off(rec, -1)) + NOT_GATED,
    ]


def check_doc_prose(rec, seal, doc):
    out = []
    stripped = BLOCK_RE.sub(u"", doc)
    if [l for l in stripped.split(u"\n") if l.lstrip().startswith(u"|")]:
        out.append(u"門の外に表の行がある")
    bad = [l[:40] for l in stripped.split(u"\n") if re.search(r"\d+(?:\.\d+)?\s*(?:%|行|件|社|席|書類|試行|回|本|ポイント|USD|file|倍|桁|字|組|つ)", l) and NOT_GATED not in l]
    if bad:
        out.append(u"散文の数に【門なし】の印が無い: %s" % bad)
    heads = re.findall(r"^## (\d+)\.", doc, re.M)
    if heads != [str(i) for i in range(1, len(heads) + 1)] or len(heads) < 6:
        out.append(u"節の番号が 1 から続いていない・6 節に足りない: %s" % heads)
    if u"<!-- 門:start pred -->" not in doc or not (doc.index(u"<!-- 門:start pred -->") < doc.index(u"## 2.")):
        out.append(u"予測の当否が先頭(第 2 節より前)にない")
    J = judge(rec, seal)
    for label, pick, tail in ((u"外れた予測", lambda v: v is False, u"。外れは外れのまま残す(封も予測も直さない)。"),
                              (u"判定しない予測", lambda v: v is None, u"。母数が 0 の予測は、当たりにも外れにも数えない。"),
                              (u"当たった予測", lambda v: v is True, u"。当たりの数を予測の良さの証拠にしない。")):
        names = [k for k, v in J.items() if pick(v[1])]
        want = label + u": " + (u"・".join(names) if names else u"なし") + tail + NOT_GATED
        if sum(1 for l in doc.split(u"\n") if l.strip() == want) != 1:
            out.append(u"『%s』の行が記録から求めた当否と違う(期待: %s)" % (label, want))
    for want in fact_lines(rec):
        if sum(1 for l in doc.split(u"\n") if l.strip() == want) != 1:
            out.append(u"記録から求めた事実の行が文書に 1 つだけ無い(期待: %s)" % want)
    for lit in DOC_LITERALS:
        if lit not in doc:
            out.append(u"必要な字が無い: %s" % lit)
    for w in FORBIDDEN:
        if w in doc:
            out.append(u"禁止語: %s" % w)
    for w in OVERCLAIM:
        if w in doc:
            out.append(u"言い過ぎ: %s" % w)
    if u"```" in doc:
        out.append(u"code fence がある")
    return out


# ----------------------------------------------------------------------------------------------------------------
# (h) docID・claim の id
def check_h(text, rec, fetched, cand=None, fence=True):
    out = []
    docs = list(fetched[u"使う書類"]) + [r["doc"] for r in rec[u"行"]]
    cids = set(r["id"] for r in rec[u"行"])
    if cand is not None:
        docs += list(cand[u"書類(出てくる順)"])
        cids |= set(r["id"] for r in cand[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"])
    for d in set(docs):
        if d in text:
            out.append(u"docID の字がある: %s" % d)
    if re.findall(r"S100[0-9A-Z]{4}", text):
        out.append(u"docID らしい字がある")
    if re.findall(r"\b[NT]\d{3}\b", text):
        out.append(u"claim の id らしい字がある")
    for cid in cids:
        if re.search(r"(?<![0-9A-Za-z])%s(?![0-9A-Za-z])" % re.escape(cid), text):
            out.append(u"記録の claim の id の字がある: %s" % cid)
            break
    if fence and u"```" in text:
        out.append(u"code fence がある")
    return out


# ----------------------------------------------------------------------------------------------------------------
# (i) 順序
def make_run(repo_dir):
    def run(*args):
        r = subprocess.run(["git", "-C", repo_dir] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r.returncode, r.stdout.decode("utf-8", "replace").strip()
    return run


def added_commits(run, path):
    rc, out = run("log", "--diff-filter=A", "--format=%H", "--", path)
    return [l for l in out.splitlines() if l.strip()] if rc == 0 else []


def is_anc(run, a, b):
    return a is not None and b is not None and run("merge-base", "--is-ancestor", a, b)[0] == 0


def order_problems(run, prefix, impl, addendum, head="HEAD"):
    u"""(i) 実装 ``impl`` < 封の commit < 封への追記の commit ``addendum`` < script・記録・文書・門の commit。問題の列 [(符号, 文)]。
    追跡されていない file は『足した commit が無い』で赤(skip にしない)。封への commit は全部、行を消さない(追記だけ)。"""
    problems = []
    seal = prefix + SEAL_REL
    s_list = added_commits(run, seal)
    if len(s_list) != 1 or not HEX40.match(s_list[0]):
        return [("SEAL_ONCE", u"封を足した commit がちょうど 1 つに決まらない(%d 行)" % len(s_list))]
    S = s_list[0]
    if not is_anc(run, S, head):
        problems.append(("SEAL<=HEAD", u"封の commit が HEAD の祖先でない"))
    if impl is None:
        problems.append(("IMPL_MISSING", u"実装の commit が無い"))
    elif not (impl != S and is_anc(run, impl, S)):
        problems.append(("IMPL_NOT_BEFORE_SEAL", u"封の commit が実装の commit の子孫でない"))
    if addendum is None:
        problems.append(("ADDENDUM_MISSING", u"封への追記の commit が無い"))
        A = None
    else:
        A = addendum
        if not (A != S and is_anc(run, S, A)):
            problems.append(("ADDENDUM_NOT_AFTER_SEAL", u"追記の commit が封の commit の子孫でない"))
        rc, txt = run("log", "--format=%H", "-1", A, "--", seal)
        if rc != 0 or txt.strip() != A:
            problems.append(("ADDENDUM_NOT_ON_SEAL", u"追記の commit が封の file を変えていない"))
    for name, rel in (("SCRIPT", SCRIPT_REL), ("RECORD", REC_REL), ("DOC", DOC_REL), ("GATE", GATE_REL)):
        lst = added_commits(run, prefix + rel)
        if len(lst) == 0:
            problems.append((name + "_UNCOMMITTED", u"%s がまだ commit されていない(足した commit が無い)" % rel))
        elif len(lst) != 1 or not HEX40.match(lst[0]):
            problems.append((name + "_ONCE", u"%s を足した commit がちょうど 1 つに決まらない(%d 行)" % (rel, len(lst))))
        else:
            if not (lst[0] != S and is_anc(run, S, lst[0])):
                problems.append((name + "_BEFORE_SEAL", u"%s の commit が封の commit より前か同じ" % rel))
            if A is not None and not (lst[0] != A and is_anc(run, A, lst[0])):
                problems.append((name + "_BEFORE_ADDENDUM", u"%s の commit が封への追記の commit より前か同じ" % rel))
    rc, txt = run("log", "--format=%H", "%s..%s" % (S, head), "--", seal)
    for h in [l for l in txt.splitlines() if l.strip()]:
        rc2, parent = run("rev-parse", h + "^")
        base = parent if rc2 == 0 else EMPTY_TREE
        rc3, numstat = run("diff", "--numstat", base, h, "--", seal)
        for line in numstat.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1] != "0":
                problems.append(("SEAL_REWRITE", u"封の commit より後の commit %s が封の行を消している" % h[:7]))
    return problems


def codes(problems):
    return sorted(set(c for c, _m in problems))


class Tmp(object):
    def __init__(self, base):
        self.dir = tempfile.mkdtemp(prefix="deltanaming_", dir=base)
        self.run = make_run(self.dir)
        self.impl = None
        self.addendum = None
        self._g("init", "-q")

    def _g(self, *args):
        r = subprocess.run(["git", "-C", self.dir, "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"] + list(args),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert r.returncode == 0, (args, r.stderr[:300])
        return r.stdout.decode("utf-8").strip()

    def write(self, rel, text):
        p = os.path.join(self.dir, rel)
        if os.path.dirname(p) and not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)

    def commit(self, msg, *paths):
        self._g("add", "--", *paths)
        self._g("commit", "-q", "-m", msg)
        return self._g("rev-parse", "HEAD")


FILES = {"SEAL": SEAL_REL, "IMPL": "adapters/xbrl/verify_document.py", "SCRIPT": SCRIPT_REL, "RECORD": REC_REL, "DOC": DOC_REL, "GATE": GATE_REL}


def build(base, steps):
    u"""steps は 'IMPL' 'SEAL' 'SCRIPT' 'RECORD' 'DOC' 'GATE'(その file を 1 つの commit で足す)・'ADDENDUM'(封に追記する commit)・変異の手 'SEAL_REWRITE' 'SEAL_APPEND' 'SEAL_TWICE' 'ALL4'(script・記録・文書・門を 1 commit)。"""
    t = Tmp(base)
    for s in steps:
        if s in FILES:
            t.write(FILES[s], u"# %s\n\n行 1\n行 2\n行 3\n" % s)
            h = t.commit(s, FILES[s])
            if s == "IMPL" and t.impl is None:
                t.impl = h
        elif s == "ADDENDUM":
            with open(os.path.join(t.dir, FILES["SEAL"]), "a", encoding="utf-8") as f:
                f.write(u"\n## 追記(探索と検証)\n行 5\n")
            t.addendum = t.commit("封に追記(探索と検証)", FILES["SEAL"])
        elif s == "ALL4":
            for k in ("SCRIPT", "RECORD", "DOC", "GATE"):
                t.write(FILES[k], u"# %s\n" % k)
            t.commit("ALL4", *[FILES[k] for k in ("SCRIPT", "RECORD", "DOC", "GATE")])
        elif s == "SEAL_REWRITE":
            t.write(FILES["SEAL"], u"# SEAL\n\n行 1\n行 3\n")
            t.commit("封を書き換える", FILES["SEAL"])
        elif s == "SEAL_APPEND":
            with open(os.path.join(t.dir, FILES["SEAL"]), "a", encoding="utf-8") as f:
                f.write(u"\n## 追記\n行 4\n")
            t.commit("封に追記", FILES["SEAL"])
        elif s == "SEAL_TWICE":
            t._g("rm", "-q", "--", FILES["SEAL"])
            t._g("commit", "-q", "-m", "封を消す")
            t.write(FILES["SEAL"], u"# SEAL\n")
            t.commit("封を足し直す", FILES["SEAL"])
        else:
            raise AssertionError(s)
    return t


# ----------------------------------------------------------------------------------------------------------------
# LATER_NAMING_FILES(fresh_seal の字から読む)
def later_naming_files(src):
    tree = ast.parse(src)
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "LATER_NAMING_FILES":
            return list(ast.literal_eval(n.value))
    return None


def naming_problems(src):
    got = later_naming_files(src)
    if got is None:
        return [u"LATER_NAMING_FILES が読めない"]
    return [u"LATER_NAMING_FILES に %s が無い" % rel for rel in (REC_REL, SCRIPT_REL, GATE_REL) if rel not in got]


def engine_problem(rel, got, want, declared, added_seal_commits=None):
    u"""sha16 が留めと同じか、宣言された遷移の値であれば None。"""
    if got == want:
        return None
    if rel in declared:
        later, seal_rel = declared[rel]
        if added_seal_commits is not None and not added_seal_commits:
            return u"遷移を宣言した封が履歴に無い"
        return None if got == later else u"宣言された遷移の値とも違う"
    return u"動いている"


def seal_addendum_problems(seal):
    u"""封への日付つき追記(探索 / 検証)の字が在る。数は script の定数と同じ。"""
    out = []
    for need in (u"## 追記 2(2026-10-30", u"探索データ", u"未探索検証データ", u"位置 0〜37", u"位置 38〜295", u"38 + 258 = 296", u"当否は付けない", u"順序の門の「封の commit」はこの追記の commit"):
        if need not in seal:
            out.append(u"封の追記に『%s』が無い" % need)
    return out


# ----------------------------------------------------------------------------------------------------------------
class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)

    def test_a_1_the_record_has_the_keys_and_the_296_rows(self):
        self.assertEqual(check_a(self.rec), [])
        self.assertEqual(len(self.rec[u"行"]), NROWS)

    def test_b_1_the_wiring_gates_are_recounted(self):
        self.assertEqual(check_b(self.rec, self.inp), [])

    def test_b_2_the_cache_is_untouched(self):
        self.assertEqual(self.rec[u"cache"][u"開始"], self.rec[u"cache"][u"終了"])

    def test_e_1_every_row_is_consistent_with_its_own_values(self):
        self.assertEqual(rows_problems(self.rec[u"行"]), [])

    def test_e_2_the_tallies_of_the_three_groups_are_recounted_from_the_rows(self):
        self.assertEqual(tally_problems(self.rec), [])

    def test_e_3_explore_plus_verify_is_the_whole_and_the_flag_follows_the_position(self):
        gr = groups_of(self.rec[u"行"])
        self.assertEqual(len(gr[EXPLORE]), N_EXPLORE)
        self.assertEqual(len(gr[VERIFY]), N_VERIFY)
        self.assertEqual(len(gr[EXPLORE]) + len(gr[VERIFY]), len(gr[u"全体"]))
        self.assertEqual([r[u"探索/検証"] for r in self.rec[u"行"]], [EXPLORE] * N_EXPLORE + [VERIFY] * N_VERIFY)
        self.assertEqual(set(r[u"doc"] for r in gr[EXPLORE]), set(self.inp["unn"][u"書類(出てくる順)"][:2]))

    def test_e_3b_the_explore_38_rows_have_the_numbers_seen_in_the_seal_section_6(self):
        self.assertEqual(explore_problems(self.rec), [])

    def test_e_4_the_script_pure_functions_agree_with_every_row(self):
        ns = load_script_funcs(jtext(SCRIPT))
        self.assertEqual(script_rows_problems(self.rec[u"行"], ns), [])

    def test_e_5_stage_counts_add_up(self):
        t_ = self.rec[u"集計"][u"全体"]
        self.assertEqual(sum(t_[u"stages"][u"段"].values()), NROWS)
        self.assertEqual(sum(t_[u"types"][u"型の行数"].values()), NROWS)
        self.assertEqual(sum(t_[u"control"][u"対照の段"].values()), NROWS)
        self.assertEqual(sum(t_[u"prior"][u"前期残高の段"].values()), NROWS)

    def test_j_1_the_inputs_read_are_unchanged_and_the_record_has_no_text(self):
        self.assertEqual(check_j(self.rec), [])
        blob = jtext(REC)
        for key in (u'"理由":', u'"span":', u'"原文":'):
            self.assertNotIn(key, blob)

    def test_j_2_the_record_names_documents_so_it_is_declared(self):
        self.assertTrue(re.search(r"S100[0-9A-Z]{4}", jtext(REC)))

    def test_k_1_the_rows_are_those_of_unnamed_fact_plain_rows(self):
        self.assertEqual(check_k(self.rec, self.inp), [])

    def test_l_1_the_words_the_band_the_window_and_the_order_are_those_of_the_seal(self):
        self.assertEqual(words_problems(jtext(SCRIPT), self.seal), [])

    def test_l_2_the_record_carries_the_constants_of_the_script(self):
        k = script_consts(jtext(SCRIPT))
        c = self.rec[u"定数"]
        self.assertEqual(c[u"UPDOWN_AFTER_RE"], k["UPDOWN_AFTER_RE"])
        self.assertEqual(c[u"UPDOWN_BEFORE_RE"], k["UPDOWN_BEFORE_RE"])
        self.assertEqual(c[u"FLOW_RE"], k["FLOW_RE"])
        self.assertEqual(c[u"SEGMENT_WORD_RE"], k["SEGMENT_WORD_RE"])
        self.assertEqual(c[u"TYPE_ORDER"], list(k["TYPE_ORDER"]))
        self.assertEqual(c[u"帯の単位数 TOL_UNITS"], 1)
        self.assertEqual(c[u"探索の最後の位置 EXPLORE_MAX_POS"], EXPLORE_MAX_POS)

    def test_the_seal_has_the_dated_addendum_on_explore_and_verify(self):
        self.assertEqual(seal_addendum_problems(self.seal), [])


class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.seal = jtext(SEAL)

    def test_d_1_judgments_cover_the_twelve_predictions(self):
        J = judge(self.rec, self.seal)
        self.assertEqual(list(J), ["D-%d" % i for i in range(1, 13)])
        self.assertEqual(list(seal_predictions(self.seal)), list(J))

    def test_d_2_the_number_of_widths_read_from_each_row_is_what_judge_uses(self):
        P = seal_predictions(self.seal)
        want = {"D-1": 1, "D-2": 4, "D-3": 4, "D-4": 3, "D-5": 4, "D-6": 1, "D-7": 1, "D-8": 5, "D-9": 3, "D-10": 3, "D-11": 3, "D-12": 2}
        for k, n in want.items():
            self.assertEqual(len(bolds(P[k][1])), n, k)

    def test_d_3_the_judge_is_not_a_constant(self):
        J0 = judge(self.rec, self.seal)
        rec = copy.deepcopy(self.rec)
        for r in rec[u"行"][:40]:
            r[u"窓なし"] = True
        self.assertFalse(judge(rec, self.seal)["D-1"][1])
        self.assertNotEqual(judge(rec, self.seal)["D-1"][0], J0["D-1"][0])
        rec = copy.deepcopy(self.rec)
        for r in rec[u"行"][:200]:
            r[u"型"] = TYPE_ORDER[3]
        self.assertFalse(judge(rec, self.seal)["D-2"][1])
        rec = copy.deepcopy(self.rec)
        for r in rec[u"行"]:
            if r[u"段"] == u"不一致":
                r[u"段"] = u"完全一致"
        self.assertFalse(judge(rec, self.seal)["D-4"][1])
        rec = copy.deepcopy(self.rec)
        for r in rec[u"行"][:10]:
            r[u"段"] = u"符号不一致"
        self.assertFalse(judge(rec, self.seal)["D-6"][1])
        rec = copy.deepcopy(self.rec)
        for r in rec[u"行"][:12]:
            r[u"型"], r[u"期"], r[u"後の窓の先頭 4 字に engine の語"], r[u"前期の fact 在り"] = TYPE_ORDER[0], u"Instant", True, True
        self.assertFalse(judge(rec, self.seal)["D-7"][1])
        rec = copy.deepcopy(self.rec)
        for r in rec[u"行"][:10]:
            r[u"前期残高の段"] = PRIORS[0]
        self.assertFalse(judge(rec, self.seal)["D-9"][1])
        rec = copy.deepcopy(self.rec)
        for r in rec[u"行"][:12]:
            r[u"対照 m"], r[u"対照の分母"] = 7, 50
        self.assertFalse(judge(rec, self.seal)["D-12"][1])
        rec = copy.deepcopy(self.rec)
        for r in rec[u"行"]:
            r[u"対照の分母"] = None if r[u"対照の分母"] is None else 1
        self.assertFalse(judge(rec, self.seal)["D-8"][1])

    def test_d_4_the_group_texts_do_not_judge_and_the_widths_are_for_296_only(self):
        G = judge_group_texts(self.rec)
        self.assertEqual(list(G), ["D-%d" % i for i in range(1, 13)])
        for k, (a, b) in G.items():
            self.assertTrue(isinstance(a, str) and isinstance(b, str) and a and b, k)
        qe = measures(groups_of(self.rec[u"行"])[EXPLORE])
        self.assertEqual(qe["n"], N_EXPLORE)

    def test_d_5_the_widths_are_read_from_the_seal_text(self):
        seal = self.seal.replace(u"**290〜296**", u"**200〜296**", 1)
        self.assertNotEqual(seal, self.seal)
        self.assertEqual(bolds(seal_predictions(seal)["D-1"][1])[0], (200, 296))
        seal = self.seal.replace(u"**150〜240**", u"**0〜240**", 1)
        self.assertNotEqual(seal, self.seal)
        self.assertEqual(bolds(seal_predictions(seal)["D-8"][1])[3], (0, 240))


class EngineTest(unittest.TestCase):
    def test_f_1_engine_sha16_are_pinned_or_declared(self):
        rec = jload(REC)
        self.assertEqual(rec[u"engine sha16"], ENGINE_AT_MEASURE)
        for rel, want in ENGINE_AT_MEASURE.items():
            added = None
            if rel in ENGINE_DECLARED:
                added = git("log", "--diff-filter=A", "--format=%H", "--", ENGINE_DECLARED[rel][1]).stdout.split()
            self.assertIsNone(engine_problem(rel, sha16(rel), want, ENGINE_DECLARED, added), rel)

    def test_f_2_the_declared_transition_form_is_red_for_an_unknown_value(self):
        rel = "adapters/xbrl/vocabulary.py"
        want = ENGINE_AT_MEASURE[rel]
        self.assertIsNone(engine_problem(rel, want, want, {}))
        self.assertIsNotNone(engine_problem(rel, "0" * 16, want, {}))
        self.assertIsNone(engine_problem(rel, "1" * 16, want, {rel: ("1" * 16, "x")}, ["abc"]))
        self.assertIsNotNone(engine_problem(rel, "2" * 16, want, {rel: ("1" * 16, "x")}, ["abc"]))
        self.assertIsNotNone(engine_problem(rel, "1" * 16, want, {rel: ("1" * 16, "x")}, []))

    def test_f_3_the_values_are_what_git_shows_for_the_seal_commit(self):
        for rel, want in ENGINE_AT_MEASURE.items():
            r = subprocess.run(["git", "show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, rel)], cwd=REPO, stdout=subprocess.PIPE)
            self.assertEqual(r.returncode, 0, rel)
            self.assertEqual(hashlib.sha256(r.stdout).hexdigest()[:16], want, rel)

    def test_f_4_no_reserved_engine_pin_name_starts_a_line_of_this_file(self):
        src = jtext(os.path.join(ROOT, GATE_REL))
        for line in src.splitlines():
            for name in RESERVED_HEADS:
                self.assertFalse(line.startswith(name), line[:40])
        heads = [l.split(u" = ")[0] for l in src.splitlines() if re.match(r"^[A-Z][A-Z_0-9]* = ", l)]
        self.assertIn("ENGINE_AT_MEASURE", heads)
        self.assertIn("ENGINE_DECLARED", heads)

    def test_f_5_the_registered_profiles_are_as_the_seal_says(self):
        import sys
        sys.path.insert(0, ROOT)
        sys.path.insert(0, os.path.join(ROOT, "core", "py"))
        from adapters.xbrl import vocabulary as V
        self.assertEqual(V.DEFAULT_PROFILE, "P27")
        self.assertTrue(V.PROFILES["P27C"].unnamed_candidate_2026_10_29)
        self.assertEqual(dict((k, int(v)) for k, v in V.UNIT_SCALE.items() if k in UNIT_SCALE), UNIT_SCALE)

    def test_f_6_the_record_engine_fields_are_the_engine_ones(self):
        rec = jload(REC)
        self.assertEqual(rec[u"engine の指紋"][u"adapter_xbrl_py_sha256"][:16], "dc7e35fbfb0f56ca")
        self.assertEqual(rec[u"engine の指紋"][u"adapter_xbrl_py_files"], 16)


class SealAndDocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def test_c_1_the_tables_equal_the_ones_rebuilt_from_the_record(self):
        self.assertEqual(check_c(self.rec, self.seal, self.doc), [])

    def test_c_2_the_prose_outside_the_tables_is_in_order(self):
        self.assertEqual(check_doc_prose(self.rec, self.seal, self.doc), [])

    def test_d_6_the_prediction_table_copies_the_seal_and_the_judgments(self):
        P = seal_predictions(self.seal)
        J = judge(self.rec, self.seal)
        got = doc_blocks(self.doc)["pred"][2:]
        self.assertEqual(len(got), 12)
        for line, (k, (field, pred, miss)) in zip(got, P.items()):
            cells = [c.strip() for c in line.strip(u"|").split(u" | ")]
            self.assertEqual(cells[0], u"**%s**" % k)
            self.assertEqual(cells[1], field)
            self.assertEqual(cells[2], pred)
            self.assertEqual(cells[3], miss)
            self.assertEqual(cells[5], hit_word(J[k][1]))
        self.assertEqual(render_blocks(self.rec, self.seal)["pred"][2:], got)

    def test_d_7_the_document_says_no_prediction_exists_for_the_258_rows(self):
        self.assertIn(u"258 行への予測は封に無い", self.doc)
        self.assertIn(u"当否を付けない", self.doc)

    def test_h_1_no_docid_and_no_claim_id_in_the_document_and_the_seal(self):
        self.assertEqual(check_h(self.doc, self.rec, self.inp["fetched"], self.inp["cand"]), [])
        self.assertEqual(check_h(self.seal, self.rec, self.inp["fetched"], self.inp["cand"]), [])

    def test_h_2_the_gate_file_has_no_docid(self):
        self.assertEqual(check_h(jtext(os.path.join(ROOT, GATE_REL)), self.rec, self.inp["fetched"], None, fence=False), [])

    def test_doc_names_the_seal_and_says_a_match_is_not_a_source(self):
        self.assertIn(u"XBRL_DELTA_NAMING_DIAG_SEAL_2026-10-30.md", self.doc)
        self.assertIn(SEAL_COMMIT_SHORT, self.doc)
        self.assertIn(ADDENDUM_COMMIT_SHORT, self.doc)
        for w in OVERCLAIM:
            self.assertNotIn(w, self.doc)


class ScriptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = jtext(SCRIPT)

    def test_script_sha_in_the_record_is_the_script_that_measured(self):
        self.assertEqual(jload(REC)[u"この script の sha256"], sha64(SCRIPT_REL))

    def test_script_imports_no_network_module_and_reads_no_key(self):
        tree = ast.parse(self.src)
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods |= set(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        self.assertEqual(mods, set(["__future__", "argparse", "collections", "hashlib", "importlib", "io", "json", "multiprocessing", "os", "re", "subprocess", "sys", "time", "zipfile", "adapters"]))
        self.assertFalse([n for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) in ("os.getenv", "os.environ.get", "os.environ.__getitem__")])
        self.assertFalse([n for n in ast.walk(tree) if isinstance(n, ast.Subscript) and ast.unparse(n.value) == "os.environ"])

    def test_script_does_not_call_the_raw_injection_harness(self):
        self.assertNotIn(u"work_doc", self.src)

    def test_script_does_not_write_the_text_of_a_sentence_into_a_row(self):
        tree = ast.parse(self.src)
        fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "doc_job"][0]
        keys = set()
        for n in ast.walk(fn):
            if isinstance(n, ast.Dict):
                for k in n.keys:
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        keys.add(k.value)
        for bad in (u"span", u"文", u"段落", u"ラベル", u"窓の字"):
            self.assertNotIn(bad, keys)

    def test_script_pure_functions_behave_as_the_seal_says(self):
        self.assertEqual(behaviour_problems(load_script_funcs(self.src)), [])

    def test_script_pure_function_mutations_are_red(self):
        muts = [
            (u"TOL_UNITS = 1", u"TOL_UNITS = 2"),
            (u"    if e <= w:\n        return S_TOL", u"    if e < w:\n        return S_TOL"),
            (u"    if e == 0:\n        return S_EXACT", u"    if e <= 1:\n        return S_EXACT"),
            (u"    if d != 0 and ((direction == D_UP and d < 0) or (direction == D_DOWN and d > 0)):", u"    if False and ((direction == D_UP and d < 0) or (direction == D_DOWN and d > 0)):"),
            (u"(direction == D_UP and d < 0) or (direction == D_DOWN and d > 0)", u"(direction == D_UP and d < 0)"),
            (u"(direction == D_UP and d < 0) or (direction == D_DOWN and d > 0)", u"(direction == D_UP and d > 0) or (direction == D_DOWN and d < 0)"),
            (u"    if d is None:\n        return S_NA", u"    if d is None:\n        return S_MISMATCH"),
            (u"    if prior_value is None:\n        return P_NA", u"    if prior_value is None:\n        return P_MISMATCH"),
            (u"        return C_ONLY if m == 0 else C_ALSO", u"        return C_ALSO if m == 0 else C_ONLY"),
            (u"    return C_OTHER if m >= 1 else C_NONE", u"    return C_OTHER if m >= 2 else C_NONE"),
            (u"    if not comparable:\n        return C_NA", u"    if False:\n        return C_NA"),
            (u"    if f_updown:\n        return TYPE_ORDER[0]\n    if f_flow:\n        return TYPE_ORDER[1]", u"    if f_flow:\n        return TYPE_ORDER[1]\n    if f_updown:\n        return TYPE_ORDER[0]"),
            (u"10.0 ** (-int(decimals)) > w", u"10.0 ** (-int(decimals)) >= w"),
            (u"EXPLORE_MAX_POS = 37", u"EXPLORE_MAX_POS = 38"),
        ]
        for old, new in muts:
            self.assertIn(old, self.src, old)
            mutated = self.src.replace(old, new, 1)
            self.assertNotEqual(behaviour_problems(load_script_funcs(mutated)), [], old)


class FalseRecordsAreRedTest(unittest.TestCase):
    u"""(g) 偽物で赤: 記録の写し・文書・封の写し・script の定数を 1 か所変えると赤になる。"""

    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def c(self, rec=None, doc=None, seal=None):
        return check_c(rec or self.rec, seal or self.seal, doc or self.doc)

    def test_g_0_baseline_is_green(self):
        self.assertEqual(check_a(self.rec), [])
        self.assertEqual(check_b(self.rec, self.inp), [])
        self.assertEqual(rows_problems(self.rec[u"行"]), [])
        self.assertEqual(tally_problems(self.rec), [])
        self.assertEqual(self.c(), [])
        self.assertEqual(check_j(self.rec), [])
        self.assertEqual(check_k(self.rec, self.inp), [])

    def test_g_1_one_stage_turned_turns_e_c_and_the_tally_red(self):
        rec = copy.deepcopy(self.rec)
        i = [k for k, r in enumerate(rec[u"行"]) if r[u"段"] == u"不一致"][0]
        rec[u"行"][i][u"段"] = u"完全一致"
        self.assertNotEqual(rows_problems(rec[u"行"]), [])
        self.assertNotEqual(tally_problems(rec), [])
        self.assertNotEqual(self.c(rec=rec), [])

    def test_g_2_one_type_turned_turns_e_red(self):
        rec = copy.deepcopy(self.rec)
        r = rec[u"行"][0]
        r[u"型"] = TYPE_ORDER[3] if r[u"型"] != TYPE_ORDER[3] else TYPE_ORDER[0]
        self.assertNotEqual(rows_problems(rec[u"行"]), [])
        rec = copy.deepcopy(self.rec)
        r = rec[u"行"][1]
        r[u"旗"][u"増減"] = not r[u"旗"][u"増減"]
        self.assertNotEqual(rows_problems(rec[u"行"]), [])

    def test_g_3_one_control_stage_turned_turns_e_red(self):
        rec = copy.deepcopy(self.rec)
        r = rec[u"行"][2]
        r[u"対照の段"] = CONTROLS[0] if r[u"対照の段"] != CONTROLS[0] else CONTROLS[3]
        self.assertNotEqual(rows_problems(rec[u"行"]), [])
        rec = copy.deepcopy(self.rec)
        r = rec[u"行"][2]
        r[u"対照 m"] = (r[u"対照 m"] or 0) + 1
        self.assertNotEqual(rows_problems(rec[u"行"]), [])

    def test_g_4_a_difference_that_disagrees_with_the_stage_turns_e_red(self):
        rec = copy.deepcopy(self.rec)
        i = [k for k, r in enumerate(rec[u"行"]) if r[u"差"] is not None][0]
        rec[u"行"][i][u"差"] += 12345678
        self.assertNotEqual(rows_problems(rec[u"行"]), [])
        rec = copy.deepcopy(self.rec)
        i = [k for k, r in enumerate(rec[u"行"]) if r[u"差"] is not None][0]
        rec[u"行"][i][u"差の符号"] = u"負" if rec[u"行"][i][u"差の符号"] == u"正" else u"正"
        self.assertNotEqual(rows_problems(rec[u"行"]), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][i][u"帯の幅"] *= 2
        self.assertNotEqual(rows_problems(rec[u"行"]), [])

    def test_g_5_the_split_flag_turned_or_a_row_moved_turns_e_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"探索/検証"] = VERIFY
        self.assertNotEqual(rows_problems(rec[u"行"]), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][N_EXPLORE][u"探索/検証"] = EXPLORE
        self.assertNotEqual(rows_problems(rec[u"行"]), [])
        rec = copy.deepcopy(self.rec)
        rec[u"集計"][EXPLORE][u"stages"][u"段"][u"不一致"] += 1
        self.assertNotEqual(tally_problems(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"集計"][VERIFY][u"control"][u"対照の段"][CONTROLS[0]] += 1
        self.assertNotEqual(tally_problems(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"集計"][u"全体"][u"prior"][u"両方に一致"] += 1
        self.assertNotEqual(tally_problems(rec), [])

    def test_g_5b_an_explore_row_turned_turns_the_explore_pin_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"段"] = u"不一致"
        self.assertNotEqual(explore_problems(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][5][u"型"] = TYPE_ORDER[2] if rec[u"行"][5][u"型"] != TYPE_ORDER[2] else TYPE_ORDER[3]
        self.assertNotEqual(explore_problems(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][5][u"前期残高の段"] = PRIORS[0]
        self.assertNotEqual(explore_problems(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"探索 38 行の数が封 §6 の数と一致(追記 2 の 5)"] = False
        self.assertNotEqual(explore_problems(rec), [])

    def test_g_6_wiring_changes_turn_b_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"(ii) ZIP の sha256 が取得の記録と材料の記録の両方と一致"] = [29, 30]
        self.assertNotEqual(check_b(rec, self.inp), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][3][u"配線"][u"(iv) claim がちょうど 1 つ"] = False
        self.assertNotEqual(check_b(rec, self.inp), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][3][u"named の value"] += 1
        self.assertNotEqual(check_b(rec, self.inp), [])
        self.assertNotEqual(check_k(rec, self.inp), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][5][u"pointers"] = [rec[u"行"][6][u"pointers"][0]]
        self.assertNotEqual(check_b(rec, self.inp), [])
        rec = copy.deepcopy(self.rec)
        d0 = rec[u"書類の並び"][0]
        rec[u"書類ごと"][d0][u"zip の sha256"] = u"0" * 64
        self.assertNotEqual(check_b(rec, self.inp), [])

    def test_g_7_one_character_of_the_prediction_judgment_turns_c_red(self):
        doc = self.doc.replace(u"| **外れ** |", u"| **当たり** |", 1) if u"| **外れ** |" in self.doc else self.doc.replace(u"| **当たり** |", u"| **外れ** |", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(self.c(doc=doc), [])
        J = judge(self.rec, self.seal)
        missed = u"・".join(k for k, v in J.items() if v[1] is False)
        if missed:
            self.assertNotEqual(check_doc_prose(self.rec, self.seal, self.doc.replace(u"外れた予測: " + missed, u"外れた予測: " + missed + u"・D-99")), [])

    def test_g_8_one_character_of_a_table_turns_c_red(self):
        for name in ("wiring", "types", "stages", "control", "prior", "ten", "elements"):
            doc = self.doc
            i = doc.index(u"<!-- 門:start %s -->" % name)
            j = doc.index(u"|", doc.index(u"\n|", i) + 1)
            k = [m.start() for m in re.finditer(r"\d", doc[j:])][0] + j
            bad = doc[:k] + (u"9" if doc[k] != u"9" else u"8") + doc[k + 1:]
            self.assertNotEqual(self.c(doc=bad), [], name)

    def test_g_9_one_character_of_a_seal_width_turns_d_and_c_red(self):
        seal = self.seal.replace(u"**1〜14**", u"**0〜14**", 1)
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(self.c(seal=seal), [])
        seal = self.seal.replace(u"| **D-8** ", u"| **D-8** x", 1)
        self.assertNotEqual(self.c(seal=seal), [])

    def test_g_10_a_docid_or_a_claim_id_in_the_document_turns_h_red(self):
        d0 = self.rec[u"行"][0]["doc"]
        c0 = self.rec[u"行"][0]["id"]
        self.assertNotEqual(check_h(self.doc + u"\n" + d0 + u"\n", self.rec, self.inp["fetched"], self.inp["cand"]), [])
        self.assertNotEqual(check_h(self.doc + u"\n" + c0 + u"\n", self.rec, self.inp["fetched"], self.inp["cand"]), [])
        self.assertNotEqual(check_h(self.doc + u"\n```\n", self.rec, self.inp["fetched"], self.inp["cand"]), [])
        self.assertNotEqual(check_h(self.doc + u"\nS100" + u"ABCD\n", self.rec, self.inp["fetched"], self.inp["cand"]), [])

    def test_g_11_one_character_of_a_word_list_turns_l_red(self):
        src = jtext(SCRIPT)
        for old, new in ((u'u"増加|減少|増収|減収|増益|減益|上回|下回|増|減"', u'u"増加|減少|増収|減収|増益|減益|上回|下回|増"'),
                         (u'u"増加額|減少額|増加分|減少分|増減額|比べ|比較し"', u'u"増加額|減少額|増加分|減少分|増減額|比べ|比較"'),
                         (u"取得|売却|支出|収入|計上|投資|返済|借入|調達|償還|配当|支払|受取|償却|引当|除却|出資|貸付|回収", u"取得|売却|支出|収入|計上|投資|返済|借入|調達|償還|配当|支払|受取|償却|引当|除却|出資|貸付|回"),
                         (u"セグメント|事業別|所在地別|地域別|部門|区分別", u"セグメント|事業別|所在地別|地域別|部門|区分"),
                         (u"AFTER_WINDOW = 10", u"AFTER_WINDOW = 12"), (u"TOL_UNITS = 1", u"TOL_UNITS = 2"),
                         (u'TYPE_ORDER = (u"増減の型", u"流量の型", u"区分の型", u"その他")', u'TYPE_ORDER = (u"流量の型", u"増減の型", u"区分の型", u"その他")'),
                         (u"EXPLORE_MAX_POS = 37", u"EXPLORE_MAX_POS = 36")):
            self.assertIn(old, src, old)
            self.assertNotEqual(words_problems(src.replace(old, new, 1), self.seal), [], old)
        seal = self.seal.replace(u"`増加\\|減少\\|増収\\|減収\\|増益\\|減益\\|上回\\|下回\\|増\\|減`", u"`増加\\|減少\\|増収\\|減収\\|増益\\|減益\\|上回\\|下回\\|増`", 1)
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(words_problems(src, seal), [])

    def test_g_12_a_reason_key_text_or_span_in_the_record_turns_j_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"理由"] = u"x"
        self.assertNotEqual(check_j(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"span"] = u"x"
        self.assertNotEqual(check_j(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"型"] = u"これは文の字です。"
        self.assertNotEqual(check_j(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"注意"] = u"あ" * 401
        self.assertNotEqual(check_j(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"読んだ入力の sha256"][UNNAMED_REL] = u"0" * 64
        self.assertNotEqual(check_j(rec), [])

    def test_g_13_removing_the_record_from_the_naming_declaration_is_red(self):
        src = jtext(os.path.join(ROOT, FRESH_SEAL_REL))
        self.assertEqual(naming_problems(src), [])
        for rel in (REC_REL, SCRIPT_REL, GATE_REL):
            bad = src.replace(u'"%s"' % rel, u'"x/%s"' % os.path.basename(rel), 1)
            self.assertNotEqual(bad, src, rel)
            self.assertNotEqual(naming_problems(bad), [], rel)

    def test_g_14_an_unmarked_number_or_a_forbidden_phrase_in_prose_turns_the_prose_check_red(self):
        for add in (u"\n行は 30 行だった。\n", u"\n一致は出所として正しい。【門なし】\n", u"\n次の封を勧めする。【門なし】\n", u"\n精度が高い。【門なし】\n", u"\n| 表 | 行 |\n"):
            self.assertNotEqual(check_doc_prose(self.rec, self.seal, self.doc + add), [], add)

    def test_g_15_the_engine_pin_is_red_for_one_character(self):
        rec = copy.deepcopy(self.rec)
        rel = "adapters/xbrl/recipes.py"
        rec[u"engine sha16"][rel] = rec[u"engine sha16"][rel][:-1] + (u"0" if rec[u"engine sha16"][rel][-1] != u"0" else u"1")
        self.assertNotEqual(check_a(rec), [])
        self.assertIsNotNone(engine_problem(rel, rec[u"engine sha16"][rel], ENGINE_AT_MEASURE[rel], {}))

    def test_g_16_a_script_stage_function_mutated_disagrees_with_the_record(self):
        src = jtext(SCRIPT)
        old = u"    if e <= w:\n        return S_TOL"
        self.assertIn(old, src)
        ns = load_script_funcs(src.replace(old, u"    if e < w:\n        return S_TOL", 1))
        self.assertNotEqual(script_rows_problems(self.rec[u"行"], ns), [])
        ns = load_script_funcs(src.replace(u"TOL_UNITS = 1", u"TOL_UNITS = 2", 1))
        self.assertNotEqual(script_rows_problems(self.rec[u"行"], ns), [])


class OrderTest(unittest.TestCase):
    u"""(i) 実装 < 封の commit < 封への追記の commit < script・記録・文書・門の commit。"""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="deltanaming_root_")
        cls.grun = staticmethod(make_run(REPO))

    def _p(self, steps):
        t = build(self.base, steps)
        return order_problems(t.run, "", t.impl, t.addendum)

    def test_i_1_the_real_history_has_the_implementation_before_the_seal_before_the_addendum_before_the_files(self):
        u"""script・記録・文書・門のどれかが未 commit なら赤(足した commit が無い)。全部 commit された後で初めて緑。"""
        rc, impl = self.grun("rev-parse", IMPL_COMMIT_SHORT + "^{commit}")
        self.assertEqual(rc, 0)
        rc, add = self.grun("rev-parse", ADDENDUM_COMMIT_SHORT + "^{commit}")
        self.assertEqual(rc, 0)
        self.assertEqual(order_problems(self.grun, PREFIX, impl, add), [])

    def test_i_2_the_real_seal_is_one_commit_after_the_implementation_and_an_ancestor_of_head(self):
        lst = added_commits(self.grun, PREFIX + SEAL_REL)
        self.assertEqual(len(lst), 1)
        self.assertTrue(lst[0].startswith(SEAL_COMMIT_SHORT))
        self.assertTrue(is_anc(self.grun, lst[0], "HEAD"))
        rc, impl = self.grun("rev-parse", IMPL_COMMIT_SHORT + "^{commit}")
        self.assertTrue(is_anc(self.grun, impl, lst[0]))
        rc, add = self.grun("rev-parse", ADDENDUM_COMMIT_SHORT + "^{commit}")
        self.assertEqual(rc, 0)
        self.assertTrue(add.startswith(ADDENDUM_COMMIT_SHORT))
        self.assertTrue(is_anc(self.grun, lst[0], add) and lst[0] != add)
        self.assertTrue(is_anc(self.grun, add, "HEAD"))

    def test_i_3_a_correct_order_is_green(self):
        self.assertEqual(self._p(["IMPL", "SEAL", "ADDENDUM", "SCRIPT", "RECORD", "DOC", "GATE"]), [])
        self.assertEqual(self._p(["IMPL", "SEAL", "ADDENDUM", "ALL4"]), [])
        self.assertEqual(self._p(["IMPL", "SEAL", "ADDENDUM", "ALL4", "SEAL_APPEND"]), [])

    def test_i_4_a_file_before_the_seal_or_before_the_addendum_is_red(self):
        for first in ("SCRIPT", "RECORD", "DOC", "GATE"):
            steps = ["IMPL", first, "SEAL", "ADDENDUM"] + [k for k in ("SCRIPT", "RECORD", "DOC", "GATE") if k != first]
            self.assertIn(first + "_BEFORE_SEAL", codes(self._p(steps)), first)
            steps = ["IMPL", "SEAL", first, "ADDENDUM"] + [k for k in ("SCRIPT", "RECORD", "DOC", "GATE") if k != first]
            self.assertIn(first + "_BEFORE_ADDENDUM", codes(self._p(steps)), first)

    def test_i_5_an_uncommitted_file_is_red_not_skipped(self):
        self.assertIn("GATE_UNCOMMITTED", codes(self._p(["IMPL", "SEAL", "ADDENDUM", "SCRIPT", "RECORD", "DOC"])))
        self.assertIn("SCRIPT_UNCOMMITTED", codes(self._p(["IMPL", "SEAL", "ADDENDUM"])))
        self.assertIn("RECORD_UNCOMMITTED", codes(self._p(["IMPL", "SEAL", "ADDENDUM", "SCRIPT", "DOC", "GATE"])))
        self.assertIn("DOC_UNCOMMITTED", codes(self._p(["IMPL", "SEAL", "ADDENDUM", "SCRIPT", "RECORD", "GATE"])))

    def test_i_6_the_seal_missing_or_added_twice_is_red(self):
        self.assertIn("SEAL_ONCE", codes(self._p(["IMPL", "ALL4"])))
        self.assertIn("SEAL_ONCE", codes(self._p(["IMPL", "SEAL", "ADDENDUM", "ALL4", "SEAL_TWICE"])))

    def test_i_7_rewriting_the_seal_after_the_fact_is_red(self):
        self.assertIn("SEAL_REWRITE", codes(self._p(["IMPL", "SEAL", "ADDENDUM", "ALL4", "SEAL_REWRITE"])))

    def test_i_8_the_same_commit_as_the_seal_is_red(self):
        t = Tmp(self.base)
        t.write(FILES["IMPL"], u"# IMPL\n")
        t.impl = t.commit("impl", FILES["IMPL"])
        for k in ("SEAL", "SCRIPT", "RECORD", "DOC", "GATE"):
            t.write(FILES[k], u"# %s\n" % k)
        t.commit("all", *[FILES[k] for k in ("SEAL", "SCRIPT", "RECORD", "DOC", "GATE")])
        self.assertIn("SCRIPT_BEFORE_SEAL", codes(order_problems(t.run, "", t.impl, None)))

    def test_i_9_the_seal_before_the_implementation_is_red(self):
        self.assertIn("IMPL_NOT_BEFORE_SEAL", codes(self._p(["SEAL", "IMPL", "ADDENDUM", "ALL4"])))
        t = build(self.base, ["IMPL", "SEAL", "ADDENDUM", "ALL4"])
        self.assertIn("IMPL_MISSING", codes(order_problems(t.run, "", None, t.addendum)))

    def test_i_10_a_missing_addendum_or_an_addendum_that_is_not_on_the_seal_is_red(self):
        self.assertIn("ADDENDUM_MISSING", codes(self._p(["IMPL", "SEAL", "ALL4"])))
        t = build(self.base, ["IMPL", "SEAL", "ALL4"])
        rc, head = t.run("rev-parse", "HEAD")
        self.assertIn("ADDENDUM_NOT_ON_SEAL", codes(order_problems(t.run, "", t.impl, head)))

    def test_i_11_an_addendum_that_deletes_a_line_of_the_seal_is_red(self):
        t = build(self.base, ["IMPL", "SEAL"])
        t.write(FILES["SEAL"], u"# SEAL\n\n行 1\n行 3\n")
        t.addendum = t.commit("追記のふりをした書き換え", FILES["SEAL"])
        for k in ("SCRIPT", "RECORD", "DOC", "GATE"):
            t.write(FILES[k], u"# %s\n" % k)
        t.commit("ALL4", *[FILES[k] for k in ("SCRIPT", "RECORD", "DOC", "GATE")])
        self.assertIn("SEAL_REWRITE", codes(order_problems(t.run, "", t.impl, t.addendum)))


if __name__ == "__main__":
    unittest.main()
