# -*- coding: utf-8 -*-
u"""段 2: 前年の有報(prev)の文の数を「翌期の有報(next)の前期欄の値」に差し替えた注入と、名指しの規則 R(封 docs/XBRL_RESTATED_PRIOR_SEAL_2026-11-02.md §2)。

    cd audit-core
    python3 measure/xbrl_restated_naming_2026-11-02.py --procs 4                                # 実走(段 1 の記録・ZIP は手元。通信しない)
    python3 measure/xbrl_restated_naming_2026-11-02.py --stub <dir> --out <file> --procs 1      # 作り物の材料(dir/stage1.json・dir/prev/・dir/next/)で走らせる(門が使う)

**0 USD・通信なし・鍵は読まない・席(LLM)は呼ばない。** engine(``core/``・``adapters/``)は 1 行も変えない(P27 のまま)。段 1 の script と記録は読むだけで書かない。
既存の cache(``edinet/``・``edinet-fresh-2026-10-21/``・``edinet-prior-2026-11-02/``)には 1 file も書かない(前後の件数を記録する)。
止まる: 出力が既に在る / 段 1 の記録が無い / prev・next の ZIP の sha256 が段 1 の記録と違う / ラベル file が無いか sha256 が名簿と違う /
engine(core/・adapters/)に未 commit の変更 / 記録に鍵の値が残った / ``--procs`` が 4 を超える。止まるときは何も書かない。

実装の注(封の字の解釈。**走らせる前に決め、結果を見て変えない**):
 1. 本文 W: engine と同じ取り方(``instance.select_mdna`` + ``instance.strip_html``)の文を NFKC にし、``prose.build_modified_zip`` に渡して取り直した本文が元と同じ(不動点)になるまで回したもの
    (最大 3 回。届かなければ門 (e') が赤)。W を ``verify_document(zip, "P27", W)`` に渡した結果が、文を渡さない結果と claim ごとに(id・state・reason・pointers・value・unit)一致することを書類ごとに
    確かめる(配線の門 (e))。**site を探す基準の判定・位置・文の一覧は W を渡した経路のもの**(注入後の判定と同じ経路なので位置がずれない)。対照は文を渡さない経路(engine の既定の入口)のもの。
    3 回目の走らせ直し(判定のコードは 2 回目と同じ): 未使用の import を消し、この注の字を直しただけ。2 回目の出力は退避した。
    2 回目の走らせ直し: 1 回目は W を「元の本文を NFKC にしたもの」とし、基準の位置を文を渡さない経路の文の一覧から取ったため、文の一覧が 22 書類で食い違い(確かめた 3 書類では空白の畳み込みと山括弧を含む文の扱いの差。残りの原因は確かめていない)、
    門 (e) が赤だった(その出力は退避し予測を判定していない)。W を不動点にし、基準を W の経路に揃えて走らせ直した。
 2. 注入の site(封 §2-1): prev の文を P27 で判定し、次を全部満たす claim。(i) state が GROUNDED (ii) form が direct_value で単位が円族(``V.UNIT_SCALE``)
    (iii) pointer が 1 本 (iv) pointer の枠が prev の当期(``xbrl_prior_pairs`` の ``frame_of`` が「当期」= CurrentYear*・member なし)
    (v) (要素, 期の型, 単位)(期の型は pointer の枠の instant の有無、単位は prev のその fact の単位)が段 1 の記録の「違う要素」に在る。
    同じ文の同じ位置は 1 回だけ数える。条件を外れる数は理由ごとに数えて記録する(``site の絞り込み``)。
 3. 位置: engine の文(W を渡した経路の文の一覧)を W の中で前から順に ``find`` して文の始まりを求め、claim の ``sentence`` と ``pos`` と、
    ``extract.iter_numbers_2026_10_27``(P27 が使う数の読み。``recipes._numbers_of`` と同じ分岐)の (開始, 終わり) で W の中の字を決める。
    W の中の字が文の中の字と一致しない・文が見つからない site は「位置が決まらない」として除き数える。
 4. 字の作り方(封 §2-2「文の単位と桁に丸めて書く」): 字の形は 2 つだけ読む。(a) ``[符号]数[.小数] 単位語``(単位語 = 百万円・千円・億円・兆円・円。桁区切りの有無と小数の桁数を保つ)、
    (b) ``[符号]N兆M億円``(N は整数、M は桁区切りの有無を保つ)。値は next の前期欄の fact の絶対値を単位語の大きさで割り、小数の桁数(b は億の整数)に
    **四捨五入(0.5 は上へ)**した字。符号の字・単位語・空白は元のまま(符号は next の値に合わせない)。(b) で兆が 0 になるときは兆を落として ``M億円`` と書く。
    他の字の形(千・百・万を混ぜた複合など)は「字の形を保てない」として除き数える。作った字が元の字と同じなら「差が桁の中」として除き数える。
    差し替えるのは数の字(符号・単位語は動かさない)だけで、``measure/inject.py`` の ``apply_edits`` と ``revert`` で差し替え、戻して W と一致することを確かめる(配線の門 (f))。
 5. 差し替えた claim の同定(位置): 注入後の本文を ``prose.build_modified_zip`` の ZIP にして ``recipes.build_raw_claims`` を呼び(engine が使う文・位置と同じ)、
    **基準と同じ (sentence, pos)** の数の claim を取る。文の数が基準と違う・その位置の claim が無い・位置の字が「元の字の数だけ差し替えた字」と一致しない・単位が違う
    ときは「対応が付かない」(止めた数にも通した数にも入れない。分母には入れる)。state・reason・pointers は同じ id の ``verify_document`` の出力から取る。
 6. 規則 R(封 §2-3): 止めた claim(state が GROUNDED でない)について、(1) form が direct_value で単位が円族で、数の読みの精度が在る。(2) pointer が 1 本ならその要素、
    pointer が無ければ claim の subject を ``V.PROFILES["P27"].subjects``(手書きの主語の行。ラベルから足される行は使わない)の最初の同じ語の行の要素列に引き、
    ``instance.facts_for(要素列, next の前期欄の fact, ..., want_ctx="Prior1Year")``(engine と同じ選び方)で fact を引く。pointer が 2 本以上、subject が無い・行が無い、
    fact が無いときは R は何も言わない(理由を数える)。(3) next の前期欄の fact: 枠が Prior1Year* で member なし・単位が JPY で始まるもの(段 1 の ``frame_of`` が「前期」)。
    (4) 帯: ``comparators.equals_within``(evidence に fact の値、claim に claim の値、contract に ``unit_scale``・``claim_scale``・``rounding``・``magnitude_truncate``)を
    **そのまま呼ぶ**。``unit_scale``・``claim_scale`` は engine と同じ式(円なら 1.0、書かれた精度)、``rounding`` は注入後の書類で engine が ``vocabulary.decide_rounding`` で決めた値
    (``build_raw_claims`` の ``info["rounding"]``)、``magnitude_truncate`` は profile の旗と ``rounding`` から。engine が raw claim に持つ同じ欄と一致することを毎回確かめる(配線の門 (g))。
    (5) 候補が複数あれば、engine と同じ並び(profile の ``statement_facts_first`` が真なら ``recipes.statement_facts_first`` = 計算書 jppfs_cor の fact を先に置く安定な並べ替え。
    試走の 1 書類で file の順だと要約の要素が先に名指されると気づき、走らせる前に足した)で最初に帯の中に入る fact を名指す。名指しの文言は「翌期の有報 <next の docID> の前期欄と一致」(記録には名指した要素と帯の結果を持つ)。
 7. 「名指しの要素が注入した要素と同じ」: R が名指した fact の要素名 == 基準の claim の pointer の要素名。
 8. 対照(封 §2-5): prev の**無改変**の文(``verify_document(zip, "P27", None)``)の止めた行の**全部**(VALUE_MISMATCH・UNVERIFIABLE・POINTER_NOT_FOUND。段 1 の組 92 書類ぜんぶ。
    違う要素が無い書類も入れる)に R を当てる。分母は止めた行の全部(R が何も言わない行を含む)。R が言える形の行だけの率も参考に別に書く。
 9. F-10(封 §2-6): E01777 の prev(2025 年 3 月期)・next(2026 年 3 月期)に、同じ site の規則(2.)を当て、項目ごとに「site の元の値 == 項目の要素の prev の当期の値 かつ
    差し替えた値 == その要素の next の前期の値」の site を探す(= 項目の数に GROUNDED で結ばれた数。項目の要素と pointer の要素は別名でもよい)。
    項目は 営業利益(``jpigp_cor:OperatingProfitLossIFRS``・書面の値 1 兆 2,766 億円 = 億の整数で 12,766)、減価償却費及び償却費(``jpigp_cor:DepreciationAndAmortizationOpeCFIFRS``・
    書面の値 1,125,588 百万円)。next の値を書面の桁に丸めて書面の値と一致するかも記録する。1 項目でも site が無ければ F-10 の段 2 の部分は「判定しない」(項目ごとの結果は記録)。
10. 集計の分母: 率は ``人が決めた数``(幅)との比較を整数の積で行う(``100 * 分子 >= 幅 * 分母``)。表示の率は小数 1 桁に丸めるが判定には使わない。
    F-6 の site 数は E01777 を含まない 97 書類(段 1 の組 92)の注入した site(差が桁の中・字の形・位置・対応を除く前の数も別に記録)。
11. 並行: 書類(prev)ごとに fork した process で ``--procs`` 本まで(4 まで)。結果は書類の順に戻す。
"""
from __future__ import print_function

import argparse
import collections
import decimal
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
import re
import sys
import time
import types
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
for _d in (ROOT, os.path.join(ROOT, "core", "py")):
    if _d not in sys.path:
        sys.path.insert(0, _d)

from adapters.xbrl import comparators as CMP        # noqa: E402
from adapters.xbrl import extract as E              # noqa: E402
from adapters.xbrl import instance as I             # noqa: E402
from adapters.xbrl import prose as PR               # noqa: E402
from adapters.xbrl import recipes as RC             # noqa: E402
from adapters.xbrl import verify_document as VD     # noqa: E402
from adapters.xbrl import vocabulary as V           # noqa: E402

SEAL_REL = "docs/XBRL_RESTATED_PRIOR_SEAL_2026-11-02.md"
SEAL_COMMIT = "3a099e7"
STAGE1_REL = "fixtures/xbrl/prior_pairs_2026-11-02.json"
STAGE1_SCRIPT_REL = "measure/xbrl_prior_pairs_2026-11-02.py"
INJECT_REL = "measure/inject.py"
LABEL_LIST_REL = "fixtures/xbrl/taxonomy_labels_sha256.txt"
OUT_REL = "fixtures/xbrl/restated_naming_2026-11-02.json"
CACHE_BASE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core")
CACHE_DIRS = collections.OrderedDict([(u"edinet", os.path.join(CACHE_BASE, "edinet")), (u"edinet-fresh-2026-10-21", os.path.join(CACHE_BASE, "edinet-fresh-2026-10-21")),
                                      (u"edinet-prior-2026-11-02", os.path.join(CACHE_BASE, "edinet-prior-2026-11-02"))])
SAMPLE_DIR = {u"手元の 67": CACHE_DIRS[u"edinet"], u"新しい標本 30": CACHE_DIRS[u"edinet-fresh-2026-10-21"]}
PRIOR_DIR = CACHE_DIRS[u"edinet-prior-2026-11-02"]
PROFILE = "P27"
MAX_PROCS = 4
#: 封 §3 の幅(F-6〜F-9)。script の定数と封の字は門が照らす。
BOUNDS = {u"F-6": (50, 600), u"F-7": 95, u"F-8": 85, u"F-9": 5}
MONEY_WORD_SCALE = collections.OrderedDict([(u"百万円", 1e6), (u"千円", 1e3), (u"億円", 1e8), (u"兆円", 1e12), (u"円", 1.0)])
SIGN_RE = r"(?:△|▲|－|-|マイナス)?\s*"
SIMPLE_RE = re.compile(r"^(?P<pre>" + SIGN_RE + r")(?P<num>\d{1,3}(?:,\d{3})+|\d+)(?P<frac>\.\d+)?(?P<gap>\s*)(?P<word>百万円|千円|億円|兆円|円)$")
CHO_OKU_RE = re.compile(r"^(?P<pre>" + SIGN_RE + r")(?P<cho>\d+)兆(?P<oku>\d{1,3}(?:,\d{3})+|\d+)億円$")
POINTER_RE = re.compile(r"^xbrl:([A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+)@([A-Za-z0-9_\-]+)$")
ITEMS = collections.OrderedDict([
    (u"営業利益", collections.OrderedDict([(u"要素", u"jpigp_cor:OperatingProfitLossIFRS"), (u"書面の桁", u"億円"), (u"書面の値(その桁の整数)", 12766)])),
    (u"減価償却費及び償却費", collections.OrderedDict([(u"要素", u"jpigp_cor:DepreciationAndAmortizationOpeCFIFRS"), (u"書面の桁", u"百万円"), (u"書面の値(その桁の整数)", 1125588)]))])
STOPPED_STATES = (u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
KEY_PATTERNS = (r"Subscription-Key=[^&\s\"]+", r"sk-[A-Za-z0-9_\-]{10,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{20,}", r"-----BEGIN")
KEY_ENV_NAMES = ("EDINET_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "EDINETDB_API_KEY")


class Stop(SystemExit):
    pass


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with io.open(p, "rb") as fh:
        return sha_bytes(fh.read())


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def load_module(p, name):
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P1 = load_module(os.path.join(HERE, "xbrl_prior_pairs_2026-11-02.py"), "prior_pairs_for_restated_naming")     # 段 1(frame_of・engine_bundle・git_head だけ使う。変えない)
IJ = load_module(os.path.join(HERE, "inject.py"), "inject_for_restated_naming")                              # apply_edits・revert
P = V.PROFILES[PROFILE]


# ---------------------------------------------------------------- 字の作り方(実装の注 4)

def parse_token(tok):
    u"""数の字(符号から単位語まで)を読む。形 (a) simple / (b) cho_oku。読めなければ None。返すのは body の位置(tok の中の [開始, 終わり))と形の記述。"""
    m = SIMPLE_RE.match(tok)
    if m:
        return collections.OrderedDict([(u"形", u"simple"), (u"body", (m.end("pre"), m.end("frac") if m.group("frac") else m.end("num"))), (u"桁区切り", u"," in m.group("num")),
                                        (u"小数の桁数", len(m.group("frac")) - 1 if m.group("frac") else 0), (u"単位語", m.group("word"))])
    m = CHO_OKU_RE.match(tok)
    if m:
        return collections.OrderedDict([(u"形", u"cho_oku"), (u"body", (m.end("pre"), m.end("oku") + 1)), (u"桁区切り", u"," in m.group("oku")), (u"小数の桁数", 0), (u"単位語", u"億円")])
    return None


def half_up(x, places):
    q = decimal.Decimal(1).scaleb(-places)
    return decimal.Decimal(repr(float(x))).quantize(q, rounding=decimal.ROUND_HALF_UP)


def render_body(form, value):
    u"""next の fact の値(円)を、形 form の body の字に。符号の字は動かさない(絶対値)。"""
    v = abs(float(value))
    if form[u"形"] == u"simple":
        q = half_up(v / MONEY_WORD_SCALE[form[u"単位語"]], form[u"小数の桁数"])
        return format(q, (u",." if form[u"桁区切り"] else u".") + u"%df" % form[u"小数の桁数"])
    n = int(half_up(v / 1e8, 0))
    cho, oku = n // 10000, n % 10000
    oku_s = format(oku, u",d") if form[u"桁区切り"] else u"%d" % oku
    return (u"%d兆%s億" % (cho, oku_s)) if cho else (u"%s億" % oku_s)


def new_token(tok, form, body):
    return tok[:form[u"body"][0]] + body + tok[form[u"body"][1]:]


# ---------------------------------------------------------------- 規則 R(実装の注 6)

def numbers_of(profile, s):
    u"""``recipes._numbers_of`` と同じ分岐。"""
    if getattr(profile, "written_precision_2026_10_27", False):
        return E.iter_numbers_2026_10_27(s)
    if getattr(profile, "numbers_2026_10_21", False):
        return E.iter_numbers_2026_10_21(s)
    return E.iter_numbers(s)


def tuple_at(sentences, si, pos):
    if si is None or si >= len(sentences):
        return None
    for t in numbers_of(P, sentences[si]):
        if t[0] == pos:
            return t
    return None


def engine_params(unit, prec, rounding):
    u"""``recipes._direct_value_claim`` の ``scale``・``unit_scale``・``mag_trunc`` と同じ式。"""
    unit_scale = 1.0 if unit == u"円" else V.UNIT_SCALE[unit]
    scale = prec if unit == u"円" else V.UNIT_SCALE[unit]
    if getattr(P, "written_precision_2026_10_27", False) and unit in V.UNIT_SCALE and prec is not None:
        scale = prec
    mt = bool(getattr(P, "truncate_on_magnitude", False) or (getattr(P, "truncate_abs_band", False) and rounding == "truncate"))
    return unit_scale, scale, mt


def next_view(next_zip_bytes, next_id):
    inst = I.load_instance(next_zip_bytes)
    ctxs = inst["contexts"]
    facts = RC.statement_facts_first(inst["facts"]) if getattr(P, "statement_facts_first", False) else inst["facts"]       # engine と同じ並び(実装の注 6 の (5))
    prior = [f for f in facts if P1.frame_of(f["context"], ctxs.get(f["context"]) or {}) == u"前期" and (f.get("unit") or u"").upper().startswith("JPY")]
    return {u"docID": next_id, u"prior": prior, u"contexts": ctxs}


def rule_r(claim, tup, rounding, nview):
    u"""止めた claim 1 行に R を当てる。返す: (言う, 理由, 名指した fact の要素, 帯の結果, engine の欄との不一致の有無を見るための params)。"""
    out = collections.OrderedDict([(u"言う", False), (u"理由", None), (u"要素", None), (u"帯", None)])
    if claim["form"] != "direct_value" or claim["unit"] not in V.UNIT_SCALE or tup is None or tup[4] is None:
        out[u"理由"] = u"対象外(形・単位・精度)"
        return out, None
    params = engine_params(claim["unit"], tup[4], rounding)
    ptrs = claim["pointers"]
    if len(ptrs) > 1:
        out[u"理由"] = u"pointer が 2 本以上"
        return out, params
    if len(ptrs) == 1:
        m = POINTER_RE.match(ptrs[0])
        if not m:
            out[u"理由"] = u"pointer の字が読めない"
            return out, params
        cands = [f for f in nview[u"prior"] if f["name"] == m.group(1)]
        if not cands:
            out[u"理由"] = u"next の前期欄に同じ要素の fact なし"
            return out, params
    else:
        subj = claim["subject"]
        if not subj:
            out[u"理由"] = u"語彙で引けず(主語なし)"
            return out, params
        rows = [elems for w, elems in P.subjects if w == subj]
        if not rows:
            out[u"理由"] = u"語彙で引けず(手書きの行に無い)"
            return out, params
        cands = I.facts_for(rows[0], nview[u"prior"], nview[u"contexts"], None, want_ctx="Prior1Year")
        if not cands:
            out[u"理由"] = u"next の前期欄に主語の要素の fact なし"
            return out, params
    contract = types.SimpleNamespace(params={"unit_scale": params[0], "claim_scale": params[1], "rounding": rounding, "magnitude_truncate": params[2]})
    cl = types.SimpleNamespace(value=claim["value"])
    for f in cands:
        cmp_ = CMP.equals_within((types.SimpleNamespace(value=f["value"]),), cl, contract)
        if cmp_.match:
            out[u"言う"], out[u"理由"], out[u"要素"], out[u"帯"] = True, u"翌期の有報の前期欄と一致", f["name"], cmp_.detail.get("normalization")
            return out, params
    out[u"理由"] = u"帯の外"
    return out, params


# ---------------------------------------------------------------- 1 回の判定

def prep_run(zb, text):
    u"""(verify_document の出力, raw claim の id → 辞書, raw の (id, sentence, pos) の列, info, engine の文の一覧)。text が None なら文を差し替えない。"""
    mz = zb if text is None else PR.build_modified_zip(zb, text)[0]
    out = VD.verify_document(zb, PROFILE, text)
    info = {}
    nc, tc = RC.build_raw_claims(mz, P, info)
    inst = I.load_instance(mz)
    name = I.select_mdna(inst["textblocks"])
    sentences = E.split_sentences(I.strip_html(inst["textblocks"][name]) if name else u"", P.paren_sentence)
    raw = collections.OrderedDict((c["id"], c) for c in nc + tc)
    if [c["id"] for c in out["claims"]] != list(raw):
        raise Stop(u"verify_document の claim の id と build_raw_claims の id が合わない。止める")
    return out, raw, info, sentences


def claim_keys(out):
    return [(c["id"], c["state"], c["reason"], tuple(c["pointers"]), c["value"], c["unit"]) for c in out["claims"]]


def canonical_text(zb):
    u"""W(実装の注 1): engine の本文を NFKC にし、``prose.build_modified_zip`` に渡して取り直した本文が元と同じになる(不動点)まで回した本文。(W, 不動点に届いたか)。"""
    inst = I.load_instance(zb)
    name = I.select_mdna(inst["textblocks"])
    w = unicodedata.normalize("NFKC", I.strip_html(inst["textblocks"][name]) if name else u"")
    for _ in range(3):
        mi = I.load_instance(PR.build_modified_zip(zb, w)[0])
        w2 = unicodedata.normalize("NFKC", I.strip_html(mi["textblocks"][I.select_mdna(mi["textblocks"])]))
        if w2 == w:
            return w, True
        w = w2
    return w, False


def sentence_offsets(W, sentences):
    offs, cur = [], 0
    for s in sentences:
        o = W.find(s, cur)
        offs.append(o)
        if o >= 0:
            cur = o + len(s)
    return offs


def pointer_parts(p):
    m = POINTER_RE.match(p) if p else None
    return (m.group(1), m.group(2)) if m else (None, None)


def process_pair(job):
    u"""prev 1 書類の段 2。返すのは数と行だけ(原文の字・span の字は持たない)。"""
    t0 = time.time()
    with io.open(job["prev_zip"], "rb") as fh:
        zb = fh.read()
    with io.open(job["next_zip"], "rb") as fh:
        nb = fh.read()
    prev_inst = I.load_instance(zb)
    nview = next_view(nb, job["next_id"])
    # 違う要素の表((要素, 期の型, 単位) → 行)
    diff = dict(((r[u"要素"], r[u"期の型"], r[u"単位"]), r) for r in job["diff_rows"])
    # 無改変(engine の既定の入口 = 文を渡さない)
    out0, raw0, info0, sents0 = prep_run(zb, None)
    W, fixed = canonical_text(zb)
    out1, raw1, info1, sents1 = prep_run(zb, W)
    gates = collections.OrderedDict()
    gates[u"文を渡した結果が渡さない結果と一致"] = claim_keys(out0) == claim_keys(out1)
    gates[u"W が不動点"] = fixed
    gates[u"文の切り方が渡さない経路と違う(参考。門に入れない)"] = sents0 != sents1
    gates[u"R の params が engine の欄と一致しない回数"] = 0
    gates[u"R の params を照らした回数"] = 0
    gates[u"戻して W と一致しない site"] = 0
    gates[u"配線の確認に使った書類の claim の数"] = len(out0["claims"])
    offs = sentence_offsets(W, sents1)
    cnt = collections.Counter()
    sites, ctrl_named = [], []
    ctrl = collections.OrderedDict([(u"止めた行", 0), (u"止めた行の state", collections.Counter()), (u"名指した", 0), (u"R が言える形の行", 0), (u"言えない理由", collections.Counter()), (u"名指した行", [])])

    def check_params(rr, raw_claim, params, rounding):
        if params is None or raw_claim.get("unit_scale") is None:
            return
        gates[u"R の params を照らした回数"] += 1
        if (params[0], params[1], rounding, params[2]) != (raw_claim["unit_scale"], raw_claim["claim_scale"], raw_claim.get("rounding"), bool(raw_claim.get("magnitude_truncate"))):
            gates[u"R の params が engine の欄と一致しない回数"] += 1

    num_ids0 = [cid for cid, c in raw0.items() if c.get("sentence") is not None and c.get("pos") is not None and cid.startswith("N")]
    num_ids = [cid for cid, c in raw1.items() if c.get("sentence") is not None and c.get("pos") is not None and cid.startswith("N")]
    by_id1 = dict((c["id"], c) for c in out1["claims"])
    # 対照: 無改変の止めた行の全部
    if job["control"]:
        for c in out0["claims"]:
            if c["state"] not in STOPPED_STATES:
                continue
            ctrl[u"止めた行"] += 1
            ctrl[u"止めた行の state"][c["state"]] += 1
            rc = raw0[c["id"]]
            tup = tuple_at(sents0, rc.get("sentence"), rc.get("pos")) if c["id"] in num_ids0 else None
            rr, params = rule_r(c, tup, info0.get("rounding"), nview)
            check_params(rr, rc, params, info0.get("rounding"))
            if rr[u"理由"] and rr[u"理由"].startswith((u"対象外", u"語彙で引けず", u"pointer が 2 本以上", u"pointer の字が読めない")):
                ctrl[u"言えない理由"][rr[u"理由"]] += 1
            else:
                ctrl[u"R が言える形の行"] += 1
                if not rr[u"言う"]:
                    ctrl[u"言えない理由"][rr[u"理由"]] += 1
            if rr[u"言う"]:
                ctrl[u"名指した"] += 1
                ctrl[u"名指した行"].append(collections.OrderedDict([(u"claim の id", c["id"]), (u"state", c["state"]), (u"pointers の要素", pointer_parts(c["pointers"][0])[0] if c["pointers"] else None), (u"R の要素", rr[u"要素"])]))
    # site
    for cid in num_ids:
        c = by_id1[cid]
        cnt[u"数の claim"] += 1
        if c["state"] != u"GROUNDED":
            continue
        cnt[u"GROUNDED の数の claim"] += 1
        if c["form"] != "direct_value" or c["unit"] not in V.UNIT_SCALE or len(c["pointers"]) != 1:
            cnt[u"形・単位・pointer の本数が条件外"] += 1
            continue
        name_, ctx_id = pointer_parts(c["pointers"][0])
        ctx = prev_inst["contexts"].get(ctx_id) if ctx_id else None
        if name_ is None or ctx is None or P1.frame_of(ctx_id, ctx) != u"当期":
            cnt[u"pointer の枠が当期(member なし)でない"] += 1
            continue
        kind = u"Instant" if ctx.get("instant") else u"Duration"
        unit_f = next((f.get("unit") for f in prev_inst["facts"] if f["name"] == name_ and f["context"] == ctx_id), None)
        row = diff.get((name_, kind, unit_f))
        if row is None:
            cnt[u"要素が段 1 の違うに入らない"] += 1
            continue
        rc = raw1[cid]
        si, pos = rc["sentence"], rc["pos"]
        tup = tuple_at(sents1, si, pos)
        if tup is None or offs[si] < 0:
            cnt[u"位置が決まらない"] += 1
            continue
        a, b = tup[0], tup[1]
        tok = sents1[si][a:b]
        if W[offs[si] + a:offs[si] + b] != tok:
            cnt[u"位置が決まらない"] += 1
            continue
        form = parse_token(tok)
        if form is None:
            cnt[u"字の形を保てない"] += 1
            continue
        body_old = tok[form[u"body"][0]:form[u"body"][1]]
        body_new = render_body(form, row[u"next の前期"])
        if body_new == body_old:
            cnt[u"差が桁の中"] += 1
            continue
        cnt[u"注入した"] += 1
        s0 = offs[si] + a + form[u"body"][0]
        inj = {"id": "%s-R-%s" % (job["prev_id"], cid), "span": [s0, s0 + len(body_old)], "replacement": body_new}
        tampered, placements = IJ.apply_edits(W, [inj])
        if IJ.revert(tampered, [inj], placements, W) != W:
            gates[u"戻して W と一致しない site"] += 1
        outT, rawT, infoT, sentsT = prep_run(zb, tampered)
        srow = collections.OrderedDict([(u"prev の docID", job["prev_id"]), (u"next の docID", job["next_id"]), (u"基準の claim の id", cid), (u"注入後の claim の id", None),
                                        (u"要素", name_), (u"枠", ctx_id), (u"期の型", kind), (u"単位", unit_f), (u"元の値", row[u"prev の当期"]), (u"差し替えた値", row[u"next の前期"]),
                                        (u"字の形", collections.OrderedDict([(u"形", form[u"形"]), (u"桁区切り", form[u"桁区切り"]), (u"小数の桁数", form[u"小数の桁数"]), (u"単位語", form[u"単位語"])])),
                                        (u"対応", u"付いた"), (u"state", None), (u"reason", None), (u"注入後の pointer の要素", None),
                                        (u"R", None), (u"名指しの要素が注入した要素と同じ", None)])
        rcT = next((c for c in rawT.values() if c["id"].startswith("N") and c.get("sentence") == si and c.get("pos") == pos), None)
        tupT = tuple_at(sentsT, si, pos) if rcT is not None else None
        want_tok = new_token(tok, form, body_new)
        if rcT is None or len(sentsT) != len(sents1) or tupT is None or sentsT[si][tupT[0]:tupT[1]] != want_tok or tupT[3] != tup[3]:
            srow[u"対応"] = u"付かない"
            sites.append(srow)
            continue
        cT = next(c for c in outT["claims"] if c["id"] == rcT["id"])
        srow[u"注入後の claim の id"] = cT["id"]
        srow[u"state"], srow[u"reason"] = cT["state"], cT["reason"]
        srow[u"注入後の pointer の要素"] = pointer_parts(cT["pointers"][0])[0] if cT["pointers"] else None
        if cT["state"] in STOPPED_STATES:
            rr, params = rule_r(cT, tupT, infoT.get("rounding"), nview)
            check_params(rr, rcT, params, infoT.get("rounding"))
            srow[u"R"] = rr
            srow[u"名指しの要素が注入した要素と同じ"] = bool(rr[u"言う"] and rr[u"要素"] == name_)
        sites.append(srow)
    return collections.OrderedDict([(u"prev の docID", job["prev_id"]), (u"next の docID", job["next_id"]), (u"gates", gates), (u"違う要素の数", len(job["diff_rows"])), (u"site の絞り込み", dict(cnt)), (u"sites", sites),
                                    (u"control", ctrl if job["control"] else None), (u"秒", round(time.time() - t0, 1))])


# ---------------------------------------------------------------- 並行

_JOBS = []


def _child(i, conn):
    try:
        conn.send(("ok", process_pair(_JOBS[i])))
    except BaseException as exc:        # Stop を含む。文言に原文は入っていない
        conn.send(("err", type(exc).__name__, str(exc) if isinstance(exc, SystemExit) else u""))
    finally:
        conn.close()


def run_jobs(jobs, procs):
    global _JOBS
    _JOBS = jobs
    if procs <= 1:
        return [process_pair(j) for j in jobs]
    mp = multiprocessing.get_context("fork")
    pending, running, results = list(range(len(jobs))), {}, {}
    while pending or running:
        while pending and len(running) < procs:
            i = pending.pop(0)
            parent, child = mp.Pipe(duplex=False)
            proc = mp.Process(target=_child, args=(i, child))
            proc.start()
            child.close()
            running[i] = (proc, parent)
        for i, (proc, conn) in list(running.items()):
            if conn.poll(0.05):
                msg = conn.recv()
                proc.join()
                del running[i]
                if msg[0] == "err":
                    for _j, (p2, _c2) in running.items():
                        p2.terminate()
                    raise Stop(msg[2] or u"書類の worker が止まった(%s)。止める" % msg[1])
                results[i] = msg[1]
            elif not proc.is_alive():
                for _j, (p2, _c2) in running.items():
                    p2.terminate()
                raise Stop(u"書類の worker が結果を返さずに終わった。止める")
    return [results[i] for i in range(len(jobs))]


# ---------------------------------------------------------------- 集計と判定

def rate(a, b):
    return round(100.0 * a / b, 1) if b else None


def tally(results):
    u"""97 書類(段 1 の組)の結果から集計。site の行から数え直せる数だけを持つ。"""
    rows = [s for r in results for s in r[u"sites"]]
    T = collections.OrderedDict()
    T[u"prev の書類"] = len(results)
    T[u"違う要素が 1 つ以上ある組"] = sum(1 for r in results if r[u"違う要素の数"] > 0)
    cnt = collections.Counter()
    for r in results:
        cnt.update(r[u"site の絞り込み"])
    T[u"site の絞り込み"] = collections.OrderedDict(sorted(cnt.items()))
    T[u"注入した site"] = len(rows)
    T[u"差が桁の中で除いた"] = cnt.get(u"差が桁の中", 0)
    T[u"対応が付かない"] = sum(1 for s in rows if s[u"対応"] != u"付いた")
    mapped = [s for s in rows if s[u"対応"] == u"付いた"]
    T[u"通した(GROUNDED)"] = sum(1 for s in mapped if s[u"state"] == u"GROUNDED")
    T[u"止めた"] = sum(1 for s in mapped if s[u"state"] in STOPPED_STATES)
    T[u"止めた割合(%)"] = rate(T[u"止めた"], T[u"注入した site"])
    T[u"止めた state の内訳"] = collections.OrderedDict((k, sum(1 for s in mapped if s[u"state"] == k)) for k in STOPPED_STATES)
    T[u"R が名指した"] = sum(1 for s in mapped if s[u"R"] and s[u"R"][u"言う"])
    T[u"名指しの割合(%)"] = rate(T[u"R が名指した"], T[u"止めた"])
    T[u"名指しの要素が注入した要素と同じ"] = sum(1 for s in mapped if s[u"名指しの要素が注入した要素と同じ"])
    T[u"R が名指さなかった理由"] = collections.OrderedDict(sorted(collections.Counter(s[u"R"][u"理由"] for s in mapped if s[u"R"] and not s[u"R"][u"言う"]).items()))
    cs = [r[u"control"] for r in results if r[u"control"]]
    C = collections.OrderedDict()
    C[u"止めた行"] = sum(c[u"止めた行"] for c in cs)
    C[u"止めた行の state"] = collections.OrderedDict((k, sum(c[u"止めた行の state"].get(k, 0) for c in cs)) for k in STOPPED_STATES)
    C[u"R が名指した"] = sum(c[u"名指した"] for c in cs)
    C[u"名指しの割合(%)"] = rate(C[u"R が名指した"], C[u"止めた行"])
    C[u"R が言える形の行"] = sum(c[u"R が言える形の行"] for c in cs)
    C[u"言える形の行での名指しの割合(%)(参考)"] = rate(C[u"R が名指した"], C[u"R が言える形の行"])
    lw = collections.Counter()
    for c in cs:
        lw.update(c[u"言えない理由"])
    C[u"言えない理由"] = collections.OrderedDict(sorted(lw.items()))
    T[u"対照"] = C
    return T


def f10_eval(results, stage1_extra):
    u"""E01777 の結果(results は 1 本)と段 1 の確認の行から項目ごとの結果。"""
    r = results[0]
    rows = [s for s in r[u"sites"]]
    diff = dict((x[u"要素"], x) for x in stage1_extra[u"突き合わせ"][u"違う要素"])
    out = collections.OrderedDict()
    for label, it in ITEMS.items():
        d = diff.get(it[u"要素"])
        item = collections.OrderedDict([(u"要素", it[u"要素"]), (u"段 1 で違うに入る", d is not None)])
        if d is None:
            item[u"結果"] = u"site なし(段 1 の違うに無い)"
            out[label] = item
            continue
        scale = MONEY_WORD_SCALE[it[u"書面の桁"]]
        item[u"next の前期の値を書面の桁に丸めた整数"] = int(half_up(abs(d[u"next の前期"]) / scale, 0))
        item[u"書面の値と一致"] = item[u"next の前期の値を書面の桁に丸めた整数"] == it[u"書面の値(その桁の整数)"]
        hit = [s for s in rows if s[u"元の値"] == d[u"prev の当期"] and s[u"差し替えた値"] == d[u"next の前期"]]
        item[u"site の数"] = len(hit)
        if not hit:
            item[u"結果"] = u"site なし"
            out[label] = item
            continue
        s = hit[0]
        item[u"基準の claim の id"] = s[u"基準の claim の id"]
        item[u"対応"], item[u"state"] = s[u"対応"], s[u"state"]
        item[u"止めた"] = s[u"state"] in STOPPED_STATES
        item[u"R が名指した"] = bool(s[u"R"] and s[u"R"][u"言う"])
        item[u"名指した要素が注入した要素と同じ"] = bool(s[u"名指しの要素が注入した要素と同じ"])
        item[u"結果"] = u"止め・名指した" if (item[u"止めた"] and item[u"R が名指した"]) else u"外れ"
        out[label] = item
    return out


def judge(T, F10):
    J = collections.OrderedDict()
    n, st, nm = T[u"注入した site"], T[u"止めた"], T[u"R が名指した"]
    lo, hi = BOUNDS[u"F-6"]
    J[u"F-6"] = u"当たり" if lo <= n <= hi else u"外れ"
    J[u"F-7"] = (u"当たり" if 100 * st >= BOUNDS[u"F-7"] * n else u"外れ") if n else u"判定できず(site 0)"
    J[u"F-8"] = (u"当たり" if 100 * nm >= BOUNDS[u"F-8"] * st else u"外れ") if st else u"判定できず(止めた 0)"
    C = T[u"対照"]
    J[u"F-9"] = (u"当たり" if 100 * C[u"R が名指した"] <= BOUNDS[u"F-9"] * C[u"止めた行"] else u"外れ") if C[u"止めた行"] else u"判定できず(止めた 0)"
    items = list(F10.values())
    if any(i[u"結果"].startswith(u"site なし") for i in items):
        J[u"F-10(段 2 の部分)"] = u"判定しない(site なし: %s)" % u"・".join(k for k, i in F10.items() if i[u"結果"].startswith(u"site なし"))
    else:
        k = sum(1 for i in items if i[u"結果"] == u"止め・名指した")
        J[u"F-10(段 2 の部分)"] = u"%d / %d" % (k, len(items))
    J[u"当たり"] = sum(1 for k in (u"F-6", u"F-7", u"F-8", u"F-9") if J[k] == u"当たり")
    J[u"外れ"] = sum(1 for k in (u"F-6", u"F-7", u"F-8", u"F-9") if J[k] == u"外れ")
    return J


# ---------------------------------------------------------------- 配線・走らせ方

def count_dir(d):
    return len(os.listdir(d)) if os.path.isdir(d) else None


def check_labels(list_path):
    d = I.taxonomy_dir()
    bad = []
    with io.open(list_path, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            want, name = ln.split()
            p = os.path.join(d, name)
            if not os.path.exists(p) or sha_file(p) != want:
                bad.append(name)
    return d, bad


def build_jobs(stage1, next_dirs, prior_dir, prev_dir, next_dir):
    u"""段 1 の記録から job の列と、sha256 の照合。返す: (jobs, extra_job, 照合の数)。"""
    fetched = dict((f[u"docID"], f[u"sha256"]) for f in stage1[u"取得"])
    docs = dict((d["docID"], d) for d in stage1[u"書類(手元の 97)"])

    def prev_path(doc):
        return os.path.join(prev_dir or prior_dir, doc + ".zip")

    def next_path(doc):
        if next_dir:
            return os.path.join(next_dir, doc + ".zip")
        return os.path.join(next_dirs[docs[doc][u"標本"]], doc + ".zip")

    sha_ok = collections.OrderedDict([(u"prev", 0), (u"next", 0)])
    jobs = []
    for p in stage1[u"組"]:
        if p[u"状態"] != u"組":
            continue
        pp, npth = prev_path(p[u"prev の docID"]), next_path(p[u"next の docID"])
        for lab, pth, want in ((u"prev", pp, fetched.get(p[u"prev の docID"])), (u"next", npth, docs[p[u"next の docID"]][u"sha256(記録)"])):
            if not os.path.exists(pth) or want is None or sha_file(pth) != want:
                raise Stop(u"%s の ZIP の sha256 が段 1 の記録と違う(または無い): %s。止める" % (lab, os.path.basename(pth)))
            sha_ok[lab] += 1
        jobs.append({"prev_id": p[u"prev の docID"], "next_id": p[u"next の docID"], "prev_zip": pp, "next_zip": npth, "diff_rows": p[u"突き合わせ"][u"違う要素"], "control": True})
    extra_job, extra_row = None, None
    for ex in stage1.get(u"固定の確認") or []:
        if ex.get(u"突き合わせ") and len(ex[u"書類"]) == 2 and all(g[u"docID"] for g in ex[u"書類"]):
            pd, nd = ex[u"書類"][0][u"docID"], ex[u"書類"][1][u"docID"]
            pp, npth = prev_path(pd), prev_path(nd)
            for lab, pth, doc in ((u"prev", pp, pd), (u"next", npth, nd)):
                if not os.path.exists(pth) or fetched.get(doc) is None or sha_file(pth) != fetched[doc]:
                    raise Stop(u"固定の確認の ZIP の sha256 が段 1 の記録と違う(または無い): %s。止める" % doc)
                sha_ok[lab] += 1
            extra_job = {"prev_id": pd, "next_id": nd, "prev_zip": pp, "next_zip": npth, "diff_rows": ex[u"突き合わせ"][u"違う要素"], "control": False}
            extra_row = ex
    return jobs, extra_job, extra_row, sha_ok


def run(out_path, stage1_path, procs, next_dirs=None, prior_dir=PRIOR_DIR, prev_dir=None, next_dir=None, cache_dirs=None, say=print):
    if procs < 1 or procs > MAX_PROCS:
        raise Stop(u"--procs は 1〜%d。止める" % MAX_PROCS)
    if os.path.exists(out_path):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % out_path)
    if not os.path.exists(stage1_path):
        raise Stop(u"段 1 の記録が無い: %s。止める" % stage1_path)
    t0 = time.time()
    stage1 = jload(stage1_path)
    bundle_sha, n_files, dirty = P1.engine_bundle()
    if dirty:
        raise Stop(u"engine(core/・adapters/)に未 commit の変更が %d file ある。止める" % dirty)
    lab_dir, lab_bad = check_labels(os.path.join(ROOT, LABEL_LIST_REL))
    if lab_bad:
        raise Stop(u"ラベル file が無いか sha256 が名簿と違う(%d 本)。止める" % len(lab_bad))
    cache_dirs = cache_dirs if cache_dirs is not None else CACHE_DIRS
    before = collections.OrderedDict((k, count_dir(v)) for k, v in cache_dirs.items())
    jobs, extra_job, extra_row, sha_ok = build_jobs(stage1, next_dirs or SAMPLE_DIR, prior_dir, prev_dir, next_dir)
    say(u"jobs %d(+固定の確認 %d)procs %d" % (len(jobs), 1 if extra_job else 0, procs))
    results = run_jobs(jobs + ([extra_job] if extra_job else []), procs)
    res97, res_extra = results[:len(jobs)], (results[len(jobs):] or [None])[0]
    after = collections.OrderedDict((k, count_dir(v)) for k, v in cache_dirs.items())
    T = tally(res97)
    F10 = f10_eval([res_extra], extra_row) if res_extra else collections.OrderedDict((k, collections.OrderedDict([(u"結果", u"site なし(固定の確認の組が段 1 に無い)")])) for k in ITEMS)
    all_res = res97 + ([res_extra] if res_extra else [])
    G = collections.OrderedDict()
    G[u"(a) 段 1 の記録の配線の門が通った"] = bool(stage1[u"配線の門"][u"通った"])
    G[u"(b) prev・next の ZIP の sha256 が段 1 の記録と一致した本数"] = collections.OrderedDict(sha_ok)
    G[u"(c) ラベル file が名簿と一致(取り出しの場所は記録しない)"] = not lab_bad
    G[u"(d) engine の未 commit の file"] = dirty
    G[u"(d') engine の bundle の sha256 が段 1 の記録と同じ"] = bundle_sha == stage1[u"engine の bundle の sha256(core/・adapters/)"]
    G[u"(e) 文を渡した結果が渡さない結果と一致しなかった書類"] = sum(1 for r in all_res if not r[u"gates"][u"文を渡した結果が渡さない結果と一致"])
    G[u"(e') W が不動点に届かなかった書類"] = sum(1 for r in all_res if not r[u"gates"][u"W が不動点"])
    G[u"(参考) 文の切り方が渡さない経路と違う書類(門に入れない)"] = sum(1 for r in all_res if r[u"gates"][u"文の切り方が渡さない経路と違う(参考。門に入れない)"])
    G[u"(f) 戻して W と一致しなかった site"] = sum(r[u"gates"][u"戻して W と一致しない site"] for r in all_res)
    G[u"(g) R の params を照らした回数"] = sum(r[u"gates"][u"R の params を照らした回数"] for r in all_res)
    G[u"(g) R の params が engine の欄と一致しなかった回数"] = sum(r[u"gates"][u"R の params が engine の欄と一致しない回数"] for r in all_res)
    G[u"(h) 既存の cache の件数が前後で同じ"] = before == after
    G[u"通った"] = bool(G[u"(a) 段 1 の記録の配線の門が通った"] and G[u"(c) ラベル file が名簿と一致(取り出しの場所は記録しない)"] and dirty == 0 and G[u"(d') engine の bundle の sha256 が段 1 の記録と同じ"]
                       and G[u"(e) 文を渡した結果が渡さない結果と一致しなかった書類"] == 0 and G[u"(e') W が不動点に届かなかった書類"] == 0 and G[u"(f) 戻して W と一致しなかった site"] == 0
                       and G[u"(g) R の params が engine の欄と一致しなかった回数"] == 0 and G[u"(h) 既存の cache の件数が前後で同じ"])
    rec = collections.OrderedDict()
    rec[u"注意"] = u"前年の有報の文の数を翌期の前期欄の値に差し替えた注入(段 2)と、名指しの規則 R の記録。会社名・原文の字・span の字は書かない。鍵の値は記録しない。engine は P27 のまま変えない。"
    rec[u"封"] = collections.OrderedDict([(u"file", SEAL_REL), (u"commit", SEAL_COMMIT)])
    rec[u"HEAD の commit"] = P1.git_head()
    rec[u"この script の sha256"] = sha_file(os.path.abspath(__file__))
    rec[u"読んだ材料の sha256"] = collections.OrderedDict([(STAGE1_REL, sha_file(stage1_path)), (STAGE1_SCRIPT_REL, sha_file(os.path.join(HERE, "xbrl_prior_pairs_2026-11-02.py"))),
                                                         (INJECT_REL, sha_file(os.path.join(HERE, "inject.py"))), (LABEL_LIST_REL, sha_file(os.path.join(ROOT, LABEL_LIST_REL)))])
    rec[u"engine の bundle の sha256(core/・adapters/)"] = bundle_sha
    rec[u"engine の file の数"] = n_files
    rec[u"profile"] = PROFILE
    rec[u"定数"] = collections.OrderedDict([(u"予測の幅", collections.OrderedDict((k, list(v) if isinstance(v, tuple) else v) for k, v in BOUNDS.items())), (u"procs の上限", MAX_PROCS),
                                         (u"字の形", [u"[符号]数[.小数] 単位語", u"[符号]N兆M億円"]), (u"丸め", u"四捨五入(0.5 は上へ)"), (u"項目", ITEMS)])
    rec[u"procs"] = procs
    rec[u"配線の門"] = G
    rec[u"site の行"] = [s for r in res97 for s in r[u"sites"]]
    rec[u"書類ごと"] = [collections.OrderedDict([(u"prev の docID", r[u"prev の docID"]), (u"next の docID", r[u"next の docID"]), (u"site の絞り込み", r[u"site の絞り込み"]), (u"秒", r[u"秒"])]) for r in res97]
    rec[u"対照の行"] = [collections.OrderedDict([(u"prev の docID", r[u"prev の docID"]), (u"止めた行", r[u"control"][u"止めた行"]), (u"止めた行の state", dict(r[u"control"][u"止めた行の state"])),
                                               (u"R が言える形の行", r[u"control"][u"R が言える形の行"]), (u"言えない理由", dict(r[u"control"][u"言えない理由"])),
                                               (u"名指した", r[u"control"][u"名指した"]), (u"名指した行", r[u"control"][u"名指した行"])]) for r in res97]
    rec[u"固定の確認 F-10"] = collections.OrderedDict([(u"EDINET コード", extra_row[u"EDINET コード"] if extra_row else None), (u"prev の docID", res_extra[u"prev の docID"] if res_extra else None),
                                                   (u"next の docID", res_extra[u"next の docID"] if res_extra else None), (u"site の絞り込み", res_extra[u"site の絞り込み"] if res_extra else None),
                                                   (u"site の行", res_extra[u"sites"] if res_extra else []), (u"項目", F10)])
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T, F10)
    rec[u"既存の cache の件数"] = collections.OrderedDict([(u"前", before), (u"後", after)])
    rec[u"所要秒"] = round(time.time() - t0, 1)
    rec[u"limits"] = [u"97 社は 2026 年提出の有報に偏る", u"「違う」は修正再表示・表示の組替え・会計方針の変更・誤りを区別しない",
                     u"注入は翌期の前期欄の値を文の単位と桁に丸めて書く 1 型で、DB の値の実際の出方ではない", u"R は measure 側の規則で engine には入っていない",
                     u"名指しは「翌期の前期欄と一致」までで、なぜ翌期で値が変わったかは言わない", u"字の形は 2 種だけ読む(千・百・万を混ぜた複合は site にしない)",
                     u"R は direct_value で円族の単位の止めた行にしか言わない(対照の分母は止めた行の全部)", u"主語から要素を引くのは手書きの主語の行だけ(ラベルから足される行は使わない)"]
    text = json.dumps(rec, ensure_ascii=False)
    rec[u"key_leaks"] = sorted(set(p for p in KEY_PATTERNS if re.search(p, text)))
    for k in KEY_ENV_NAMES:
        if os.environ.get(k) and os.environ[k] in text:
            raise Stop(u"記録に鍵の値が入った。書かない")
    if not G[u"通った"]:
        rec[u"注意"] += u" **配線の門が通っていない。予測を判定しない。**"
    with io.open(out_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--stage1", default=os.path.join(ROOT, STAGE1_REL))
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--stub", default=None, help=u"作り物の材料の dir(stage1.json・prev/・next/)。門が使う")
    a = ap.parse_args(argv)
    if a.stub:
        rec = run(a.out, os.path.join(a.stub, "stage1.json"), a.procs, prev_dir=os.path.join(a.stub, "prev"), next_dir=os.path.join(a.stub, "next"), cache_dirs={})
    else:
        rec = run(a.out, a.stage1, a.procs)
    print(u"written: %s" % a.out)
    print(json.dumps(rec[u"配線の門"], ensure_ascii=False))
    print(json.dumps(rec[u"集計"], ensure_ascii=False)[:2000])
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
