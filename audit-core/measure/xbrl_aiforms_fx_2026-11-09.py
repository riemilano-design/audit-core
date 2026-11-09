# -*- coding: utf-8 -*-
u"""封 docs/XBRL_AI_FORMS_FX_SEAL_2026-11-09.md §0-2 の 9 ― FX(AI の文の形を増やす: F6 社長メッセージ・F7 ニュース記事・F8 百万円単位・F9 前期を主語にした対比)の駆動 script。

前の便の script 4 本(``xbrl_aiforms_{gen,run,labels,tally}_2026-11-03.py``)と F5 の駆動 script は **1 byte も変えず**、この 1 本が importlib で読み込んで差し替える
(形の表・置き場所・記録の path・2 席目の本数・費用の上限と見積り・profile・判定の入口)。差し替えた先は記録の ``差し替え`` の欄に名前と sha256 で書く。
注入の段だけは T5Y の便(``xbrl_t5y_2026-11-06.py``)・T9 の便(``xbrl_pbind_2026-11-06.py`` の ``inject_text_pb`` = T9 第 2 便の id の対応付けを P30E・P32E に当てた関数)・
H の便の T1/T8(``xbrl_rmix_2026-11-04.py`` の ``inject_text_rb``)の関数を importlib で読み込んで呼ぶ(写さない)。

    python3 measure/xbrl_aiforms_fx_2026-11-09.py --dry-run [--only DOC] [--new-cache DIR]   # 本数・見積り 2 つ(USD)。鍵は読まない・通信しない
    ANTHROPIC_API_KEY=... python3 measure/xbrl_aiforms_fx_2026-11-09.py gen [--only DOC] [--resume]   # 有料。司令塔だけが走らせる(160 本)
    python3 measure/xbrl_aiforms_fx_2026-11-09.py judge  [--procs N] [--only DOC]   # 0 USD。4 profile の判定 → fx_claims_2026-11-09.json・札付けの束
    python3 measure/xbrl_aiforms_fx_2026-11-09.py inject [--procs N] [--only DOC]   # 0 USD。T1・T5・T8・T9 の注入(P30E・P32E)→ fx_inject_2026-11-09.json
    python3 measure/xbrl_aiforms_fx_2026-11-09.py labels                            # 0 USD。盲検の席の札 → fx_labels_2026-11-09.json
    python3 measure/xbrl_aiforms_fx_2026-11-09.py tally                             # 0 USD。集計と封 §2 の X-1〜X-10 の判定 → fx_tally_2026-11-09.json

守り(前の便と同じ。差し替えても落ちない):
  - 鍵は環境変数 ``ANTHROPIC_API_KEY`` だけから読む(``gen`` の有料の呼び出しのときだけ)。記録は書く前と書いた後に ``key_leaks`` を検査する(封の path の字だけを検査の前に除く)。
  - 費用の上限 40 USD はこの便の実費の累計だけ(前の便の累計は加えない)。走らせる前の止め = 残りの本の実測の平均(sonnet 0.178・haiku 0.166)の和が上限以下であること。
    呼ぶたびの止め = 実費の累計 + 次の 1 本の実測の平均 × 1.5 が上限を超えたら止める。保守的な単価の見積りは並べて出し・記録に書くが、止めには使わない。
  - 会社の列は前の便の ``会社の選び.docID`` と一致しなければ止める。置き場は新しい folder(``NEW_CACHE``)。既存の cache 3 folder と前の便の 2 folder は 1 file も書かず、前後を記録して変われば止める。

engine(``core/``・``adapters/``)・``measure/lib``・``measure/inject.py`` は 1 行も変えない。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import inspect
import io
import json
import os
import re
import statistics
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    u"""importlib で読み込む。``sys.modules`` にも登録する(``--procs`` 2 以上の fork で pickle に落ちないため)。"""
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


GEN = load_module("xbrl_aiforms_gen_2026-11-03.py", "aiforms_gen_for_fx")
RUN = load_module("xbrl_aiforms_run_2026-11-03.py", "aiforms_run_for_fx")
LAB = load_module("xbrl_aiforms_labels_2026-11-03.py", "aiforms_labels_for_fx")
TAL = load_module("xbrl_aiforms_tally_2026-11-03.py", "aiforms_tally_for_fx")
TY = load_module("xbrl_t5y_2026-11-06.py", "t5y_for_fx")                 # 注入の段: T5(と、その連なりの H・T9 第 2 便・RB の関数)
PB = load_module("xbrl_pbind_2026-11-06.py", "pbind_for_fx")             # 注入の段: T9(P30E・P32E の id の対応付け)

from adapters.xbrl import prose as PR                       # noqa: E402
from adapters.xbrl import recipes as R                      # noqa: E402
from adapters.xbrl import verify_document as VD             # noqa: E402
from adapters.xbrl import vocabulary as V                   # noqa: E402

Stop = GEN.Stop
SEAL_REL = "docs/XBRL_AI_FORMS_FX_SEAL_2026-11-09.md"
SEAL_COMMIT = "ad65426"
SCRIPT_REL = "measure/xbrl_aiforms_fx_2026-11-09.py"
FX_GEN_REL = GEN.REC_DIR_REL + "/fx_gen_2026-11-09.json"
FX_CLAIMS_REL = GEN.REC_DIR_REL + "/fx_claims_2026-11-09.json"
FX_LABELS_REL = GEN.REC_DIR_REL + "/fx_labels_2026-11-09.json"
FX_INJECT_REL = GEN.REC_DIR_REL + "/fx_inject_2026-11-09.json"
FX_TALLY_REL = GEN.REC_DIR_REL + "/fx_tally_2026-11-09.json"
FX_REC_REL = collections.OrderedDict([("gen", FX_GEN_REL), ("claims", FX_CLAIMS_REL), ("labels", FX_LABELS_REL), ("inject", FX_INJECT_REL)])
PREV_GEN_REL = GEN.GEN_REL                                   # 差し替える前の値(前の便の記録。会社の列と実測の平均の出どころ)
MOVES_REL = "fixtures/xbrl/pbind/moves_200_2026-11-06.json"  # F1〜F5 の並べる数(P30E → P32E の動いた行・P32E の数の claim と GROUNDED)
PREV_TALLY_REL = TAL.TALLY_REL                               # F1〜F4 の札の率(差し替える前の値。読むだけ)
PREV_CACHE_NAME = "aiforms-2026-11-03"                       # 前の便の folder(この便は 1 file も書かない。前後を記録して照らす)
PREV_CACHE = GEN.NEW_CACHE
F5_CACHE_NAME = "aiforms-f5-2026-11-03"
F5_CACHE = os.path.join(GEN.CACHE_BASE, F5_CACHE_NAME)
FX_NEW_CACHE = os.path.join(GEN.CACHE_BASE, "aiforms-fx-2026-11-09")
assert os.path.basename(PREV_CACHE) == PREV_CACHE_NAME

# ---- 封 §0-2 の決めごと(字で留める)
FX_FORMS = ("F6", "F7", "F8", "F9")
FX_SEAT2_N = 32                                              # 封 §0-2 の 6: 2 席目は種で引いた 32 本(20%)
FX_N_BOOKS = 20 * len(FX_FORMS) * 2
COST_CAP_USD = 40.0                                          # 封 §0-2 の 4: この便の実費の累計だけ(前の便の累計は含めない)
#: 封 §0-1 の 1・§0-2 の 4: 前の便の記録 ``gen_2026-11-03.json`` の ok の呼び出しの cost_usd の model ごとの平均(小数 3 桁)。門が記録から引き直して照らす
AVG_COST_USD = collections.OrderedDict([("claude-sonnet-5-5", 0.178), ("claude-haiku-5-5", 0.166)])
AVG_SOURCE = u"fixtures/xbrl/aiforms/gen_2026-11-03.json の ok の呼び出しの cost_usd の model ごとの平均(小数 3 桁)"
NEXT_FACTOR = 1.5                                            # 呼ぶたびの止め: 累計 + 次の 1 本の実測の平均 × 1.5 が上限を超えたら止める
FX_PROFILES = ("P27", "P30E", "P32E", "P33E" if "P33E" in V.PROFILES else "P27E")     # 封 §0-2 の 5
AXIS = "P32E"                                                # 行の軸 = P32E の数の claim(予測を置く profile)
INJECT_PAIR = ("P32E", "P30E")                               # 注入の (比較, 土台)。土台 = 無改変の文で P30E が GROUNDED の claim。結果は両 profile を持つ
INJECT_PROFILES = ("P30E", "P32E")                           # 記録の並び
FX_INJECT_TYPES = ("T1_VALUE", "T5_COINCIDENT", "T8_REL", "T9_PRIOR_TO_CURRENT")
PRIOR = u"前期"

# ---- 形の 1 文(封 §0-2 の 2。字は固定し、門が封の字と照らす。共通の指示文 WRITER_COMMON は前の便のまま)
F6_TEXT = u"社長から株主への手紙。一人称(私・私ども)で、見出しを立てず、段落で書く。全体で 1,000〜1,800 字。数は必要なところだけに入れる(6 個以上)。"
F7_TEXT = u"経済紙の記事。会社を『同社』と呼び、第三者の立場で書く。見出し 1 行、要約の段落 1 つ、本文の段落 3〜5 つ。全体で 800〜1,500 字。数を 10 個以上入れる。"
F8_ADD = u"ただし金額は百万円単位で『8,294百万円』の形に統一し、率は小数 1 桁で書く。"
F9_TEXT = u"見出しつきの段落。各項目について、前期の数を先に『前期は …』で書き、続けて当期の数を『当期は …』で書く対比の形にする。経営成績・財政状態・キャッシュ・フローの順。全体で 1,500〜2,500 字。"

# ---- 差し替える前の値(門が照らす)
ORIG = {
    "WRITER_COMMON": GEN.WRITER_COMMON,
    "WRITER_FORMS": GEN.WRITER_FORMS,
    "F1_FORM_TEXT": GEN.WRITER_FORMS["F1"],
    "select_companies": GEN.select_companies,
    "new_record": GEN.new_record,
    "key_leaks": GEN.key_leaks,
    "estimate_usd": GEN.estimate_usd,
    "plan_problem": GEN.plan_problem,
    "prepare": GEN.prepare,
    "outside_calls": GEN.outside_calls,
    "outside_cost": GEN.outside_cost,
    "header": RUN.header,
    "write_record": RUN.write_record,
    "judge_text": RUN.judge_text,
    "PROFILES": RUN.PROFILES,
    "CLAIM_COLS": RUN.CLAIM_COLS,
}
F1_FORM_TEXT = ORIG["F1_FORM_TEXT"]
WRITER_FORMS_FX = collections.OrderedDict([("F6", F6_TEXT), ("F7", F7_TEXT), ("F8", F1_FORM_TEXT + F8_ADD), ("F9", F9_TEXT)])
CLAIM_COLS_FX = tuple(ORIG["CLAIM_COLS"]) + (u"窓の手がかり", u"節の手がかり")
STEP_FROM = u"AI の形 4 × model 2"
STEP_TO = u"AI の形 F6〜F9(社長メッセージ・ニュース記事・百万円単位・前期を主語にした対比)× model 2"
ROW_ORDER_TEXT = (u"claim の欄 → " + u" → ".join(FX_PROFILES) + u" の順(行の軸 = %s の数の claim。ほかの profile の欄は (文の番号, 位置) の鍵で引き、"
                  u"その profile に同じ鍵の数の claim が無ければ null。profile の欄は配列。直前の profile と同じなら \"=\")" % AXIS)
CUE_TEXT = (u"窓の手がかり・節の手がかり = 行の軸(%s)の文の字 s と数の位置 a に recipes._prior_cue_window_2026_11_06(s, a)・recipes._prior_cue_clause(s, a) を"
            u"呼んだ真偽(engine の関数を読むだけ。文の字が取れない行は null)" % AXIS)

# ======================================================================================================
# 見積り・費用(封 §0-2 の 4)
LAST_PLAN = {}


def est_book_usd(model):
    u"""1 本の見積り = 前の便の実測の平均(model ごと)。走らせる前の止めと記録の見積りに使う。"""
    return AVG_COST_USD[model]


def estimate_usd_fx(prompt_chars):
    u"""呼ぶたびの止めの余裕(``GEN.run`` の ``cum + est > COST_CAP_USD``)= 実測の平均 × 1.5。``GEN.run`` は次の本の model を渡さないので、2 model の平均の大きい方を使う
    (sonnet は封の字のとおり 0.178 × 1.5・haiku は 0.166 × 1.5 より 0.018 USD 大きい = わずかに早く止まる側。封に無い決め)。入力の字数は使わない。"""
    return NEXT_FACTOR * max(AVG_COST_USD.values())


def conservative_usd(prompt_chars):
    u"""保守的な単価の見積り(前の便の ``estimate_usd`` そのまま)。並べて出し・記録に書くだけで、止めには使わない。"""
    return ORIG["estimate_usd"](prompt_chars)


def plan_problem_fx(rec, all_jobs, prompts, say):
    u"""走らせる前の止め。記録の累計(この便の呼び出しだけ)+ まだ「済み」でない本の実測の平均の和が上限を超えるなら理由の文、超えなければ None。
    保守的な単価の見積りも並べて出し(止めには使わない)、記録があれば ``費用`` の欄に書く。"""
    cur = GEN.current_ok_by_name(rec[u"呼び出し"]) if rec is not None else {}
    base = GEN.recorded_cost(rec) if rec is not None else GEN.outside_cost()
    rest = [(d, f, m) for d, f, m in all_jobs if GEN.text_key(d, f, m) not in cur]
    est = round(sum(est_book_usd(m) for d, f, m in rest), 6)
    cons = round(sum(conservative_usd(len(prompts[(d, f)])) for d, f, m in rest), 6)
    LAST_PLAN.clear()
    LAST_PLAN.update({u"残りの本数": len(rest), u"見積り(実測の平均)USD": est, u"見積り(保守的な単価。止めには使わない)USD": cons, u"記録の累計 USD": base})
    say(u"走らせる前の確かめ: 本数 %d・記録の累計 %.4f USD + 残り %d 本の見積り(実測の平均 sonnet %.3f・haiku %.3f)%.4f USD = %.4f USD(上限 %.2f)" % (
        len(all_jobs), base, len(rest), AVG_COST_USD["claude-sonnet-5-5"], AVG_COST_USD["claude-haiku-5-5"], est, base + est, GEN.COST_CAP_USD))
    say(u"見積りの 2 つ: 実測の平均 %.4f USD(止めに使う)・保守的な単価(入力 %.1f / 出力 %.1f USD / M tokens・出力は max_tokens の全部)%.4f USD(止めには使わない)" % (
        est, GEN.PRICE_IN, GEN.PRICE_OUT, cons))
    if rec is not None:
        rec[u"費用"][u"見積り(実測の平均)USD"] = est
        rec[u"費用"][u"見積り(保守的な単価。止めには使わない)USD"] = cons
        rec[u"費用"][u"見積りの本数"] = len(rest)
    if base + est > GEN.COST_CAP_USD:
        return u"**記録の累計 %.4f + 残りの見積り %.4f = %.4f USD が上限 %.2f USD を超える。1 回も呼ばずに止める**" % (base, est, base + est, GEN.COST_CAP_USD)
    return None


def prepare_fx(root, caches, new_cache, say, check_replace=True):
    u"""``GEN.prepare`` を呼び(fact の表・指示文は前の便のまま)、返す見積りの合計だけ実測の平均の合計に替える
    (``GEN.run`` が見積り > 上限で止める入口。前の便の保守的な見積りの合計 = 47 USD 台は上限を超えるので、そのまま渡すと 1 回も呼べない)。"""
    chosen, counts, seed_meta, tables, prompts, cons_total = ORIG["prepare"](root, caches, new_cache, say, check_replace)
    est_total = sum(est_book_usd(m) for _ in chosen for _f in FX_FORMS for m in GEN.MODELS)
    LAST_PLAN[u"見積りの合計(実測の平均)USD"] = round(est_total, 6)
    return chosen, counts, seed_meta, tables, prompts, est_total


def outside_calls_fx():
    u"""この便は記録の外の呼び出しも前の便の累計も持たない(封 §0-2 の 4: この便の実費の累計だけ)。"""
    return []


def outside_cost_fx():
    return 0.0


_COMPANY_EST_RE = re.compile(r"見積り\(model 2 本・形 4 つ\)=[0-9.]+ USD")
_SKIP_SAY = (u"見積り(保守的な単価",)


def say_fx(say):
    u"""``GEN.run`` の印字のうち、前の便の保守的な見積りの行(上限と比べる意味が替わった)は出さず、会社ごとの見積りは実測の平均の字に直す。
    見積りの 2 つは ``plan_problem_fx`` が出す。"""
    per_company = round(len(FX_FORMS) * sum(AVG_COST_USD.values()), 4)

    def out(line):
        if line.startswith(_SKIP_SAY):
            return
        say(_COMPANY_EST_RE.sub(u"見積り(model 2 本・形 4 つ・実測の平均)=%.4f USD" % per_company, line))
    return out


# ======================================================================================================
# 鍵の検査: 封の path「docs/XBRL_AI_FORMS_FX_SEAL_2026-11-09.md」は英数字・_・- が 32 字続くので、前の便の ``key_leaks`` の「32 字以上の英数字の連なり」に当たってしまう。
# 封の path そのものの字だけを検査の前に除く(ほかの字は前の便の検査のまま)。
def key_leaks_fx(text, key_value=None, long_alnum=True):
    return ORIG["key_leaks"](text.replace(SEAL_REL, u""), key_value, long_alnum)


# ======================================================================================================
# 前の便の記録(読むだけ)
def prev_gen(root=ROOT):
    return GEN.jload(os.path.join(root, PREV_GEN_REL))


def prev_avg_costs(root=ROOT):
    u"""前の便の gen の記録の ok の呼び出しの cost_usd の model ごとの平均(小数 3 桁)。"""
    by = collections.OrderedDict((m, []) for m in AVG_COST_USD)
    for c in prev_gen(root)[u"呼び出し"]:
        if c.get(u"ok") and c.get(u"model") in by:
            by[c[u"model"]].append(c[u"cost_usd"])
    return collections.OrderedDict((m, round(sum(v) / len(v), 3) if v else None) for m, v in by.items())


def prev_problems(root=ROOT):
    u"""AVG_COST_USD が前の便の gen の記録の実測の平均と一致するか。問題の列。"""
    out = []
    got = prev_avg_costs(root)
    for m, v in AVG_COST_USD.items():
        if got.get(m) != v:
            out.append(u"AVG_COST_USD の %s が前の便の gen の記録の実測の平均と違う" % m)
    return out


def select_companies_fx(root=ROOT, seed=None):
    u"""前の便と同じ選び(同じ種・同じ規則)。前の便の記録の 会社の選び.docID と列が一致しなければ止める。"""
    chosen, counts = ORIG["select_companies"](root, seed)
    want = prev_gen(root)[u"会社の選び"][u"docID"]
    if [r["docID"] for r in chosen] != want:
        raise Stop(u"**会社の列が前の便の gen の記録の 会社の選び.docID と違う。止める**")
    return chosen, counts


# ======================================================================================================
# 判定の入口(1 本の判定。行の軸は P32E の数の claim。他の profile は (文の番号, 位置) の鍵で引く)
def profile_view_fx(zb, text, zm, pname):
    u"""1 profile の数の claim を (文の番号, 位置) の鍵で引ける形に。{rows: {鍵: (claim, raw claim)}, ok, states, sents}。ok = claim と raw claim の並びが合い鍵が一意。"""
    prof = V.PROFILES[pname]
    out = VD.verify_document(zb, pname, text)
    nums, texts = R.build_raw_claims(zm, prof)
    raws = nums + texts
    cl = out["claims"]
    ok = len(cl) == len(raws) and all(c["id"] == r["id"] for c, r in zip(cl, raws))
    rows = collections.OrderedDict()
    for c, r in zip(cl, raws):
        if c["kind"] != "num":
            continue
        key = (r["sentence"], r["pos"])
        if key in rows:
            ok = False
        rows[key] = (c, r)
    return {"rows": rows, "ok": ok, "states": out["document"]["states"], "sents": RUN.sentence_list(zm, prof)}


def cell_fx(pair):
    u"""profile の欄(``RUN.PROFILE_COLS`` の順)。その profile に同じ鍵の claim が無ければ None。"""
    if pair is None:
        return None
    c, r = pair
    return [c["state"], RUN.safe_reason(c["reason"]), RUN.pointer_strings(c["pointers"]), bool(r.get("subject")),
            RUN.other_subject_cell(r), r.get("p27_gate"), r.get("last_branch_evidence")]


def judge_text_fx(zb, text):
    u"""1 本 → (記録の 本 の欄(名前などを除く), 札付けの束の行)。行 = 行の軸(P32E)の数の claim ごとに、claim の欄 + 手がかり 2 つ + profile ごとの欄。"""
    zm, _el, _mem = PR.build_modified_zip(zb, text)
    views = collections.OrderedDict((p, profile_view_fx(zb, text, zm, p)) for p in FX_PROFILES)
    axis = views[AXIS]
    lines = RUN.lines_nfkc(text)
    rows, dossier = [], []
    for key, (c, r) in axis["rows"].items():
        si = r.get("sentence")
        sents = axis["sents"]
        stext = sents[si] if isinstance(si, int) and 0 <= si < len(sents) else None
        lead, multi = RUN.line_info(lines, stext, c["span"])
        win = bool(R._prior_cue_window_2026_11_06(stext, r["pos"])) if stext is not None else None
        clause = bool(R._prior_cue_clause(stext, r["pos"])) if stext is not None else None
        cells = [cell_fx(views[p]["rows"].get(key)) for p in FX_PROFILES]
        rows.append([c["id"], c["kind"], c["form"], c["unit"], multi, lead, win, clause] + RUN.encode_cells(cells))
        dossier.append({"id": c["id"], u"文": stext, u"数": c["value"], u"単位": c["unit"], u"周り": c["span"]})
    axis_keys = set(axis["rows"])
    off_axis = collections.OrderedDict((p, len(set(views[p]["rows"]) - axis_keys)) for p in FX_PROFILES)
    same = all(v["ok"] for v in views.values()) and not any(off_axis.values())
    rec = collections.OrderedDict([
        (u"対応", same), (u"行数", len(lines)), (u"claim の数", len(rows)),
        (u"数の claim の数", collections.OrderedDict((p, len(views[p]["rows"])) for p in FX_PROFILES)),
        (u"行の軸に無い鍵の数", off_axis),
        (u"4 state", collections.OrderedDict((p, collections.OrderedDict((s, views[p]["states"].get(s, 0)) for s in RUN.STATES)) for p in FX_PROFILES)),
        (u"行", rows)])
    return rec, dossier


def write_record_fx(path, text, rec, key_value=None):
    u"""``RUN.run_judge`` が呼ぶ書き込み(使う側の名前 ``write_record`` に届くよう module の属性を差し替える)。判定の記録の ``欄`` の 行の並び の字を F6〜F9 の行の作りに直し、
    手がかりの欄の説明を足してから前の便の書き込み(禁止欄・鍵の検査)に渡す。注入の記録など ``欄`` が無い記録はそのまま通す。"""
    if isinstance(rec.get(u"欄"), dict) and u"行の並び" in rec[u"欄"]:
        rec[u"欄"][u"行の並び"] = ROW_ORDER_TEXT
        rec[u"欄"][u"手がかりの欄"] = CUE_TEXT
        text = RUN.dumps_compact_rows(rec)
    return ORIG["write_record"](path, text, rec, key_value)


# ======================================================================================================
# 差し替え
SWAP_TABLE = (
    ("GEN", "FORMS", FX_FORMS), ("GEN", "WRITER_FORMS", WRITER_FORMS_FX), ("GEN", "NEW_CACHE", FX_NEW_CACHE), ("GEN", "GEN_REL", FX_GEN_REL),
    ("GEN", "SEAL_REL", SEAL_REL), ("GEN", "SEAL_COMMIT", SEAL_COMMIT), ("GEN", "SEAT2_N", FX_SEAT2_N), ("GEN", "COST_CAP_USD", COST_CAP_USD),
    ("GEN", "key_leaks", key_leaks_fx), ("GEN", "outside_calls", outside_calls_fx), ("GEN", "outside_cost", outside_cost_fx),
    ("GEN", "select_companies", select_companies_fx), ("GEN", "estimate_usd", estimate_usd_fx), ("GEN", "plan_problem", plan_problem_fx),
    ("GEN", "prepare", prepare_fx),
    ("RUN", "CLAIMS_REL", FX_CLAIMS_REL), ("RUN", "INJECT_REL", FX_INJECT_REL), ("RUN", "SEAL_REL", SEAL_REL), ("RUN", "SEAL_COMMIT", SEAL_COMMIT),
    ("RUN", "PROFILES", FX_PROFILES), ("RUN", "CLAIM_COLS", CLAIM_COLS_FX), ("RUN", "judge_text", judge_text_fx), ("RUN", "write_record", write_record_fx),
    ("LAB", "LABELS_REL", FX_LABELS_REL),
    ("TAL", "TALLY_REL", FX_TALLY_REL), ("TAL", "FORMS", FX_FORMS), ("TAL", "PROFILES", FX_PROFILES),
)
MODS = {"GEN": GEN, "RUN": RUN, "LAB": LAB, "TAL": TAL}
#: 同じ GEN の instance を他の module に差し込む(別 instance に patch が届かない罠。``X.GEN is GEN`` を門が見る)
SHARE_TABLE = (("RUN", "GEN", GEN), ("RUN", "Stop", GEN.Stop), ("LAB", "GEN", GEN), ("LAB", "RUN", RUN), ("LAB", "Stop", GEN.Stop),
               ("TAL", "GEN", GEN), ("TAL", "RUN", RUN), ("TAL", "LAB", LAB), ("TAL", "Stop", GEN.Stop))
#: 差し替えた先の関数(記録の ``差し替え`` に名前と sha256 を書く)
SWAPPED_FUNCS = collections.OrderedDict([
    ("GEN.estimate_usd", estimate_usd_fx), ("GEN.plan_problem", plan_problem_fx), ("GEN.prepare", prepare_fx), ("GEN.select_companies", select_companies_fx),
    ("GEN.key_leaks", key_leaks_fx), ("GEN.outside_calls", outside_calls_fx), ("GEN.outside_cost", outside_cost_fx),
    ("RUN.judge_text", judge_text_fx), ("RUN.write_record", write_record_fx)])


def swapped_names():
    return [u"%s.%s" % (m, a) for m, a, _v in SWAP_TABLE] + [u"%s.%s" % (m, a) for m, a, _v in SHARE_TABLE] + \
        [u"GEN.EXISTING_CACHES", u"GEN.new_record", u"RUN.header", u"TAL.REC_REL"]


def func_shas():
    out = collections.OrderedDict((k, GEN.sha256_text(inspect.getsource(f))) for k, f in SWAPPED_FUNCS.items())
    out[u"GEN.new_record"] = GEN.sha256_text(inspect.getsource(new_record_fx))
    out[u"RUN.header"] = GEN.sha256_text(inspect.getsource(header_fx))
    return out


def swap_shas():
    return collections.OrderedDict([
        (u"WRITER_COMMON(前の便のまま)", GEN.sha256_text(GEN.WRITER_COMMON)),
        (u"WRITER_FORMS", collections.OrderedDict((k, GEN.sha256_text(v)) for k, v in WRITER_FORMS_FX.items())),
        (u"差し替えた関数", func_shas())])


def swap_field():
    u"""記録の ``差し替え`` の欄。名前の一覧・指示文と差し替えた関数の sha256・前の便の gen script の sha256・この駆動 script の sha256・費用の決めごと・profile。"""
    return collections.OrderedDict([
        (u"差し替えた名前", swapped_names()), (u"sha256", swap_shas()),
        (u"前の便の gen script の sha256", GEN.sha256_file(os.path.join(HERE, "xbrl_aiforms_gen_2026-11-03.py"))),
        (u"駆動 script の sha256", GEN.sha256_file(os.path.abspath(__file__))),
        (u"費用", collections.OrderedDict([(u"上限 USD", COST_CAP_USD), (u"実測の平均 USD", AVG_COST_USD), (u"平均の出どころ", AVG_SOURCE),
                                          (u"呼ぶたびの止め", u"実費の累計 + 次の 1 本の実測の平均 × %s > 上限(2 model の平均の大きい方を使う)" % NEXT_FACTOR)])),
        (u"profile", list(FX_PROFILES)), (u"行の軸", AXIS), (u"注入の対", list(INJECT_PAIR))])


def restep(step):
    if STEP_FROM not in step:
        raise AssertionError(u"step の字が前の便の形でない")
    return step.replace(STEP_FROM, STEP_TO)


def new_record_fx(*a, **k):
    rec = ORIG["new_record"](*a, **k)
    rec[u"step"] = restep(rec[u"step"])
    rec[u"差し替え"] = swap_field()
    cost = rec[u"費用"]
    cost[u"見積りの規則"] = (u"走らせる前の止め = 残りの本の実測の平均(model ごと)の和が上限以下。呼ぶたびの止め = 実費の累計 + 次の 1 本の実測の平均 × %s が上限を超えたら止める。"
                         u"保守的な単価の見積り(入力の字数 × 1.0 を token とみなし出力は max_tokens の全部)は並べて記録するが、止めには使わない" % NEXT_FACTOR)
    cost[u"実測の平均 USD"] = collections.OrderedDict(AVG_COST_USD)
    cost[u"実測の平均の出どころ"] = AVG_SOURCE
    return rec


def header_fx(*a, **k):
    h = ORIG["header"](*a, **k)
    h[u"step"] = restep(h[u"step"])
    h[u"差し替え"] = swap_field()
    return h


def install():
    u"""差し替えを入れる(import 時に 1 回)。同じ GEN の instance を RUN・LAB・TAL の ``GEN`` に差し込む。"""
    for m, a, v in SHARE_TABLE:
        setattr(MODS[m], a, v)
    for m, a, v in SWAP_TABLE:
        setattr(MODS[m], a, v)
    GEN.EXISTING_CACHES = collections.OrderedDict(list(GEN.EXISTING_CACHES.items()) + [(PREV_CACHE_NAME, PREV_CACHE), (F5_CACHE_NAME, F5_CACHE)])
    GEN.new_record = new_record_fx
    RUN.header = header_fx
    TAL.REC_REL = collections.OrderedDict(FX_REC_REL)


#: gen 以外の command(judge・inject・labels・tally)は会社の選び直しも見積りもしないので、この差し替えは見ない(試験が選びを絞るために差し替えても通る)
NOT_NEEDED_AFTER_GEN = ("GEN.select_companies",)


def wiring_problems(skip=()):
    u"""差し替えが全部届いているか(使う側の実体に届かないと黙って効かない)。問題の列。skip = 見ない名前(``module.属性``)。"""
    out = []
    for m, a, v in SHARE_TABLE:
        if getattr(MODS[m], a) is not v:
            out.append(u"%s.%s が同じ instance でない" % (m, a))
    for m, a, v in SWAP_TABLE:
        cur = getattr(MODS[m], a)
        if u"%s.%s" % (m, a) in skip:
            continue
        if not (cur is v or (isinstance(v, (str, int, float, tuple, dict)) and cur == v)):
            out.append(u"%s.%s が差し替えた先でない" % (m, a))
    names = list(GEN.EXISTING_CACHES)
    if names[-2:] != [PREV_CACHE_NAME, F5_CACHE_NAME] or GEN.EXISTING_CACHES[PREV_CACHE_NAME] != PREV_CACHE or GEN.EXISTING_CACHES[F5_CACHE_NAME] != F5_CACHE:
        out.append(u"GEN.EXISTING_CACHES に前の便の 2 つの folder が無い")
    if GEN.new_record is not new_record_fx:
        out.append(u"GEN.new_record が差し替えた先でない")
    if RUN.header is not header_fx:
        out.append(u"RUN.header が差し替えた先でない")
    if dict(TAL.REC_REL) != dict(FX_REC_REL):
        out.append(u"TAL.REC_REL が FX の記録でない")
    if GEN.WRITER_COMMON != ORIG["WRITER_COMMON"]:
        out.append(u"WRITER_COMMON が前の便の字でない")
    if list(GEN.WRITER_FORMS) != list(FX_FORMS):
        out.append(u"形の指示が F6〜F9 の 4 つでない")
    if tuple(RUN.PROFILES) != tuple(FX_PROFILES):
        out.append(u"RUN.PROFILES が FX の 4 profile でない")
    # 使う側の globals の名前に届いているか(関数の中で引かれる名前)
    if GEN.run.__globals__["plan_problem"] is not plan_problem_fx or GEN.run.__globals__["prepare"] is not prepare_fx:
        out.append(u"GEN.run が引く plan_problem・prepare が差し替えた先でない")
    if GEN.run.__globals__["estimate_usd"] is not estimate_usd_fx or GEN.run.__globals__["COST_CAP_USD"] != COST_CAP_USD:
        out.append(u"GEN.run が引く estimate_usd・COST_CAP_USD が差し替えた先でない")
    if RUN.judge_job.__globals__["judge_text"] is not judge_text_fx or RUN.run_judge.__globals__["write_record"] is not write_record_fx:
        out.append(u"RUN の judge_job・run_judge が引く judge_text・write_record が差し替えた先でない")
    if RUN.decode_row.__globals__["CLAIM_COLS"] != CLAIM_COLS_FX or RUN.decode_row.__globals__["PROFILES"] != FX_PROFILES:
        out.append(u"RUN.decode_row が引く CLAIM_COLS・PROFILES が FX の字でない")
    return out


install()


# ======================================================================================================
# 注入(T1・T8 = H の便の RB の関数・T5 = T5Y の関数・T9 = PB の関数。いずれも切り替え 2 つ 真の中で呼ぶ。profile の対は (P32E, P30E))
def install_inject():
    u"""注入の連なり(T5Y の chain)の入れ替え: ``RM.INJECT_PROFILES`` を (P32E, P30E) にしてから ``RM.install_inject()``(``RUN.PROFILES`` と ``RUN.base_status4`` が届く)。"""
    TY.RM.INJECT_PROFILES = INJECT_PAIR
    TY.RM.install_inject()


def inject_wiring_problems():
    u"""注入の前の確かめ。問題の列。"""
    out = list(TY.NS.wiring_problems()) + list(TY.wiring_problems()) + list(PB.wiring_problems()) + list(PB.PI.wiring_problems())
    if tuple(TY.RUN.PROFILES) != INJECT_PAIR or tuple(TY.RM.INJECT_PROFILES) != INJECT_PAIR:
        out.append(u"注入の連なりの RUN.PROFILES・RM.INJECT_PROFILES が (P32E, P30E) でない")
    if TY.RUN.base_status4 is not TY.RM.base_status_rb or TY.RUN.t8_candidates4.__globals__["base_status4"] is not TY.RM.base_status_rb:
        out.append(u"注入の連なりの base_status4 が RM.base_status_rb でない")
    if TY.RUN.INJECT_CAP != RUN.INJECT_CAP or PB.RUN.INJECT_CAP != RUN.INJECT_CAP:
        out.append(u"注入の cap(RUN.INJECT_CAP)が連なりの間で違う")
    if TY.T5 != FX_INJECT_TYPES[1] or PB.T9 != FX_INJECT_TYPES[3]:
        out.append(u"注入の型の名前が FX_INJECT_TYPES と違う")
    return out


def inject_job_fx(args):
    u"""1 本 → (名前, 注入の行(T1・T8・T5・T9 の順), 本ごとの数え)。切り替え 2 つが真でなければ止める。"""
    name, item, row, text_dir, zip_caches, seed, work_root = args
    if not getattr(TY.N, TY.FLAG) or not getattr(TY.S, TY.FLAG2):
        raise Stop(u"**切り替えが偽のまま inject を走らせた。止める**")
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    refs = TY.RUN.refs_for(row, zip_caches, work_root)
    base = collections.OrderedDict([(u"docID", item[u"docID"]), (u"form", item[u"form"]), (u"model", item[u"model"]), (u"writer", item[u"writer"])])
    out, per = [], collections.OrderedDict()
    for tag, fn in ((u"T1・T8", TY.RM.inject_text_rb), (u"T5", TY.inject_text_ty), (u"T9", PB.inject_text_pb)):
        rows, counts = fn(zb, text, refs, seed, name)
        per[tag] = counts
        for r in rows:
            d = collections.OrderedDict(base)
            d.update(r)
            out.append(d)
    return name, out, per


def inject_summary_fx(rows):
    u"""型 × profile(P30E・P32E)× {全体・形別・model 別・形 × model}。分母は対応が付いた注入(``RUN.inject_cell``)。"""
    out = collections.OrderedDict()
    for t in FX_INJECT_TYPES:
        tr = [r for r in rows if r[u"型"] == t]
        out[t] = collections.OrderedDict()
        for p in INJECT_PROFILES:
            cell = collections.OrderedDict([(u"全体", RUN.inject_cell(tr, p))])
            cell[u"形別"] = collections.OrderedDict((f, RUN.inject_cell([r for r in tr if r["form"] == f], p)) for f in FX_FORMS)
            cell[u"model 別"] = collections.OrderedDict((w, RUN.inject_cell([r for r in tr if r["writer"] == w], p)) for w in TAL.WRITERS)
            cell[u"形 × model"] = collections.OrderedDict((u"%s×%s" % (f, w), RUN.inject_cell([r for r in tr if r["form"] == f and r["writer"] == w], p))
                                                         for f in FX_FORMS for w in TAL.WRITERS)
            out[t][p] = cell
    return out


def run_inject_fx(root=ROOT, procs=1, only=None, gen_path=None, new_cache=None, caches=None, out=None, key_value=None, say=print, seed=None, seed_meta=None, work_root=None):
    u"""注入(0 USD)。切り替え 2 つ(``yen_scan_2026_11_05``・``t5_yen_2026_11_06``)を with の中だけ真にして 160 本に T1・T5・T8・T9 を 1 本あたり型ごと RUN.INJECT_CAP 件。"""
    new_cache = new_cache or GEN.NEW_CACHE
    caches = caches or GEN.EXISTING_CACHES
    out = out or os.path.join(root, RUN.INJECT_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    bad = wiring_problems(NOT_NEEDED_AFTER_GEN)
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    if getattr(TY.N, TY.FLAG) or getattr(TY.S, TY.FLAG2):
        raise Stop(u"**切り替えが真のまま inject を始めた。止める**")
    install_inject()
    bad = inject_wiring_problems()
    if bad:
        raise Stop(u"**注入の差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    if seed is None:
        seed, seed_meta = GEN.seed_value(root)
    gen, items, by_doc, names = RUN.prepare_run(root, only, gen_path, new_cache, caches)
    before = GEN.caches_snapshot(caches)
    work_root = work_root or tempfile.mkdtemp(prefix="aiforms_fx_inject_", dir=os.environ.get("TMPDIR"))
    present = [n for n in names if n in items]
    jobs_ = [(n, items[n], by_doc[n.split("_")[0]], new_cache, caches, seed, work_root) for n in present]
    say(u"注入 %d 本(欠け %d 本)× T1・T5・T8・T9 × 2 profile(P30E・P32E)。切り替え 2 つ 真 ― procs %d(1 件ごとに判定。時間がかかる)" % (len(jobs_), len(names) - len(present), procs))
    with TY.yen_scan_on():
        with TY.t5_yen_on():
            if not getattr(TY.N, TY.FLAG) or not getattr(TY.S, TY.FLAG2) or TY.wiring_problems():
                raise Stop(u"**切り替えを真にできない・配線が崩れた。止める**")
            results = TY.NF.map_pool(inject_job_fx, jobs_, procs)
    if getattr(TY.N, TY.FLAG) or getattr(TY.S, TY.FLAG2):
        raise Stop(u"**with を出ても切り替えが真のまま。止める**")
    rows, per = [], collections.OrderedDict()
    for n, r, c in results:
        rows += r
        per[n] = c
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**既存の cache の件数か名前が変わった。記録を書かずに止める**")
    rec = RUN.header(root, u"AI の形 4 × model 2 ― 注入(T1_VALUE・T5_COINCIDENT・T8_REL・T9_PRIOR_TO_CURRENT。0 USD)", gen_path or os.path.join(root, GEN.GEN_REL), seed_meta, before, after)
    rec[u"profile"] = list(INJECT_PROFILES)
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", [TY.FLAG, TY.FLAG2]), (u"inject の中の値", True), (u"出たあとの値", False)])
    rec[u"種"] = {u"file": RUN.SEED_REL_STR, u"種の確認": seed_meta}
    rec[u"型"] = collections.OrderedDict([
        ("T1_VALUE", u"H の便の RB の関数 ``RM.inject_text_rb``(``inject.select(types=[T1_VALUE])`` のまま。cap は採用に掛ける)"),
        ("T8_REL", u"同 ``RM.inject_text_rb``(円族の token・r ∈ %s・%d 回まで。cap は site に掛ける)" % (list(RUN.TUNE.T8_R_VALUES), RUN.TUNE.T8_TRIES)),
        ("T5_COINCIDENT", u"T5Y の便の ``inject_text_ty``(値が偶然一致して参照先が違う誤りを円族の数に作る)"),
        ("T9_PRIOR_TO_CURRENT", u"T9 第 2 便の id の対応付けを P30E・P32E に当てた PB の便の ``inject_text_pb``(前期の fact に結ばれた数に当期の値を入れる。窓の手がかりの欄を持つ)"),
        (u"上限", u"型ごと・1 本あたり %d" % RUN.INJECT_CAP),
        (u"土台", u"無改変の文で P30E が GROUNDED の claim。P32E の claim は (value, span, unit) が同じ 1 件があれば結ぶ(無ければその行の P32E の欄は対応なし)"),
        (u"profile の対", u"(比較, 土台) = (P32E, P30E)。T1・T8・T5 の行にある ``P29E の土台に対応`` の欄の名前は RB の便の字のまま = 比較の profile(P32E)の claim に結べたか"),
        (u"inject の docID の引数", u"本の名前(<docID>_<形>_<model>)")])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"] = inject_summary_fx(rows)
    rec[u"限界"] = [u"注入は 4 型(値・相対のずれ・値が偶然一致・期の入れ替え)。主語・単位の取り違えは注入しない",
                  u"T1・T8・T5 の行の ``注入後の pointer の期``・``届いた`` は土台の profile(P30E)の claim で決める(T9 の行は P32E の期も持つ)",
                  u"通した・止めたは engine の state で、札(人の目)は無い"]
    rec[u"行"] = rows
    text = RUN.dumps_inject(rec)
    RUN.write_record(out, text, rec, key_value)
    say(u"-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
# labels の記録: labels の script は step を持つ記録を自分で書くので、書いた後に step と 差し替え の 2 欄だけを FX に直す(他の欄・並び・書式は変えない)
def restamp_json(path, key_value=None):
    with io.open(path, encoding="utf-8") as fh:
        rec = json.load(fh, object_pairs_hook=collections.OrderedDict)
    rec[u"step"] = restep(rec[u"step"])
    rec[u"差し替え"] = swap_field()
    text = json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    if GEN.key_leaks(text, key_value, long_alnum=False):
        os.remove(path)
        raise Stop(u"**記録に鍵らしい字が在る。消して止める**")
    GEN.write_text(path, text)
    return rec


# ======================================================================================================
# 封 §2 の X-1〜X-10(幅は字で留める。門が封の文書の字と照らす)
X1_MIN_BOOKS, X1_MIN_CLAIMS, X1_COST = 150, 6, (18.0, 35.0)
X2_BOUNDS = collections.OrderedDict([("F6", (8, 25)), ("F7", (10, 35)), ("F8", (30, 80)), ("F9", (30, 90))])
X3_BOUNDS = collections.OrderedDict([("F6", (55, 80)), ("F7", (50, 78)), ("F8", (68, 85)), ("F9", (55, 80))])
X4_MIN = 80.0
X5_PRIOR, X5_WINDOW, X5_CLAUSE = (30.0, 55.0), (50.0, 85.0), (10.0, 40.0)
X6_F9, X6_OTHER = (5.0, 25.0), (3.0, 20.0)
X7_BOUNDS = collections.OrderedDict([("F6", (2.0, 10.0)), ("F7", (2.0, 8.0)), ("F8", (1.0, 5.0)), ("F9", (1.0, 6.0))])
X7_TRUE_MIN = 80.0
X8_PASS_MAX = 5.0
X9_PAIR_MAX, X9_SPREAD_MIN = 12.0, 10.0
X10_RATIO = 2
HIT, MISS, NOJ = TAL.HIT, TAL.MISS, TAL.NOJ
LABEL_TRUE, LABEL_FALSE = u"真", u"偽"
PASS = RUN.TUNE.LABEL_PASS
STATE_G = "GROUNDED"


def pct(a, b):
    return TAL.pct(a, b)


def frac(a, b):
    return TAL.frac(a, b)


def between(x, lo_hi):
    return TAL.between(x, lo_hi)


def load_refs(root=ROOT):
    u"""F1〜F5 の並べる数の元(読むだけ): P30E → P32E の動いた行の記録と、前の便の tally(F1〜F4 の札の分布)。"""
    return collections.OrderedDict([("moves", GEN.jload(os.path.join(root, MOVES_REL))), ("prev_tally", GEN.jload(os.path.join(root, PREV_TALLY_REL)))])


def period_of_cell(cell):
    u"""profile の欄の pointers の先頭の期: 当期 / 前期 / 他 / なし(``RUN.pointer_strings`` の字。欄が無い行は None)。"""
    if cell is None:
        return None
    ptrs = cell[u"pointers"]
    if not ptrs:
        return u"なし"
    last = ptrs[0].rpartition("@")[2]
    return last if last in (u"当期", u"前期", u"他") else u"他"


def moved(a, b):
    u"""封 E-4 の字: 両方の profile に在る行のうち state か pointers が違う行。"""
    return a is not None and b is not None and (a[u"state"] != b[u"state"] or a[u"pointers"] != b[u"pointers"])


def group_books(books):
    u"""全体 / 形別 / model 別 / 形 × model の本の組(欠けていない本)。"""
    return TAL.groups_books([b for b in books if not b.get(u"欠け")])


def dist(vals):
    if not vals:
        return None
    return collections.OrderedDict([(u"本", len(vals)), (u"最小", min(vals)), (u"中央値", statistics.median(vals)), (u"最大", max(vals))])


def sec_wiring_fx(records):
    gen, claims = records["gen"], records["claims"]
    ok = dict(GEN.current_ok_by_name(gen[u"呼び出し"]))
    books = [b for b in claims[u"本"] if not b.get(u"欠け")]
    out = collections.OrderedDict()
    out[u"本数(予定)"] = len(GEN.FORMS) * len(GEN.MODELS) * len(gen[u"会社の選び"][u"docID"])
    out[u"生成できた本"] = len(ok)
    out[u"生成できて %s の数の claim が %d 以上ある本" % (AXIS, X1_MIN_CLAIMS)] = sum(1 for b in books if b[u"数の claim の数"][AXIS] >= X1_MIN_CLAIMS)
    out[u"費用 USD(実費。記録の cost_usd の合計)"] = round(sum(c[u"cost_usd"] for c in gen[u"呼び出し"]), 4)
    out[u"見積り USD(実測の平均)"] = gen[u"費用"].get(u"見積り(実測の平均)USD")
    out[u"見積り USD(保守的な単価。止めには使わない)"] = gen[u"費用"].get(u"見積り(保守的な単価。止めには使わない)USD")
    out[u"呼び出しの数"] = len(gen[u"呼び出し"])
    out[u"失敗した呼び出し"] = sum(1 for c in gen[u"呼び出し"] if not c[u"ok"])
    out[u"再試行の合計"] = sum(c[u"retries"] for c in gen[u"呼び出し"])
    out[u"止めた理由"] = gen.get(u"止めた理由")
    out[u"上限で止まった"] = TAL.is_cap_stop(gen.get(u"止めた理由"))
    out[u"上限でない停止(字)"] = gen.get(u"止めた理由") if gen.get(u"止めた理由") and not TAL.is_cap_stop(gen.get(u"止めた理由")) else None
    out[u"max_tokens で打ち切られた本"] = sum(1 for c in ok.values() if c[u"stop_reason"] == "max_tokens")
    per = collections.OrderedDict()
    for key, sel in group_books(books).items():
        names = [b[u"name"] for b in sel]
        per[key] = collections.OrderedDict([
            (u"本", len(sel)), (u"%s の数の claim の数" % AXIS, dist([b[u"数の claim の数"][AXIS] for b in sel])),
            (u"文の字数", dist([ok[n][u"chars"] for n in names if n in ok])), (u"費用 USD", round(sum(ok[n][u"cost_usd"] for n in names if n in ok), 4))])
    out[u"形 × model"] = per
    return out


def sec_engine_fx(rows):
    u"""4 state の分布(全 claim)と、札 真・札 偽の行の扱い。形 × model × profile。その profile に欄が無い行は ``対応が付かない行`` に数えて率の分母に入れない。"""
    out = collections.OrderedDict()
    for p in FX_PROFILES:
        pcell = collections.OrderedDict()
        for k, sel in TAL.groups(rows).items():
            present = [r for r in sel if r[p] is not None]
            states = collections.Counter(r[p][u"state"] for r in present)
            lr = [r for r in TAL.labelled(present)]
            true_rows = [r for r in lr if r[u"label"][0] == LABEL_TRUE]
            false_rows = [r for r in lr if r[u"label"][0] == LABEL_FALSE]
            t_stop = [r for r in true_rows if r[p][u"state"] != STATE_G]
            f_stop = [r for r in false_rows if r[p][u"state"] != STATE_G]
            reasons = collections.Counter((r[p][u"reason"] or u"(reason なし)") + u"/" + r[p][u"state"] for r in t_stop)
            pcell[k] = collections.OrderedDict([
                (u"claim", len(sel)), (u"対応が付かない行", len(sel) - len(present)),
                (u"4 state", collections.OrderedDict((s, states.get(s, 0)) for s in RUN.STATES)),
                (u"札 真の行の GROUNDED 率", frac(len(true_rows) - len(t_stop), len(true_rows))),
                (u"札 真で止めた率", frac(len(t_stop), len(true_rows))),
                (u"札 真で止めた行の reason/state の内訳", collections.OrderedDict(sorted(reasons.items()))),
                (u"札 偽の行で止めた率", frac(len(f_stop), len(false_rows))),
                (u"札 偽の行で通した数", len(false_rows) - len(f_stop))])
        out[p] = pcell
    return out


def sec_moves_fx(rows, books):
    u"""profile の対の動いた行(封 E-4 の字: state か pointers が違う行)。向き別・1 本あたり。対 = (P30E, P32E)(X-10)と (P32E, 4 番目の profile)。"""
    out = collections.OrderedDict()
    bg = group_books(books)
    for pa, pb in ((u"P30E", u"P32E"), (u"P32E", FX_PROFILES[3])):
        cell = collections.OrderedDict()
        for k, sel in TAL.groups(rows).items():
            mv = [r for r in sel if moved(r[pa], r[pb])]
            sc = [r for r in mv if r[pa][u"state"] != r[pb][u"state"]]
            dirs = collections.Counter(u"%s → %s" % (r[pa][u"state"], r[pb][u"state"]) for r in sc)
            n_books = len(bg[k])
            cell[k] = collections.OrderedDict([
                (u"本", n_books), (u"動いた行", len(mv)), (u"state が変わった行", len(sc)), (u"1 本あたりの動いた行", round(float(len(mv)) / n_books, 4) if n_books else None),
                (u"向き別", collections.OrderedDict(sorted(dirs.items())))])
        out[u"%s → %s" % (pa, pb)] = cell
    return out


def sec_shape_fx(rows):
    u"""形の性質(P32E の数の claim)。円族の数のうち百万円の書き方・pointer の期・前期を名指す claim の手がかり(窓 / 節だけ / どちらも偽)。"""
    money = tuple(RUN.N.UNIT_FAMILIES["money"])
    out = collections.OrderedDict()
    for k, sel in TAL.groups(rows).items():
        n = len(sel)
        yen = [r for r in sel if r[u"unit"] in money]
        per = collections.Counter(period_of_cell(r[AXIS]) for r in sel)
        prior = [r for r in sel if period_of_cell(r[AXIS]) == PRIOR]
        win = [r for r in prior if r[u"窓の手がかり"] is True]
        clause_only = [r for r in prior if r[u"窓の手がかり"] is not True and r[u"節の手がかり"] is True]
        neither = [r for r in prior if r[u"窓の手がかり"] is False and r[u"節の手がかり"] is False]
        unknown = [r for r in prior if r[u"窓の手がかり"] is None or r[u"節の手がかり"] is None]
        out[k] = collections.OrderedDict([
            (u"数の claim", n), (u"円族の数", len(yen)), (u"うち百万円の書き方", frac(sum(1 for r in yen if r[u"unit"] == u"百万円"), len(yen))),
            (u"pointer の期(%s の先頭)" % AXIS, collections.OrderedDict((w, per.get(w, 0)) for w in (u"当期", PRIOR, u"他", u"なし"))),
            (u"前期を名指す数の割合", frac(len(prior), n)),
            (u"前期を名指す数の手がかり", collections.OrderedDict([
                (u"前期の数", len(prior)), (u"窓の手がかりが真", frac(len(win), len(prior))), (u"節の手がかりだけが真", frac(len(clause_only), len(prior))),
                (u"どちらも偽", frac(len(neither), len(prior))), (u"手がかりが取れない行", len(unknown))]))])
    return out


def sec_inject_period(rows):
    u"""T9 の通した行の窓の手がかり(X-6)。形別。"""
    out = collections.OrderedDict()
    for f in FX_FORMS:
        t9 = [r for r in rows if r[u"型"] == FX_INJECT_TYPES[3] and r["form"] == f]
        passed = [r for r in t9 if r[AXIS][u"結果"] == PASS]
        out[f] = collections.OrderedDict([(u"T9 の行", len(t9)), (u"通した行", len(passed)),
                                          (u"通した行のうち窓の手がかり偽", sum(1 for r in passed if r[u"窓の手がかり"] is False)),
                                          (u"通した行のうち窓の手がかり真", sum(1 for r in passed if r[u"窓の手がかり"] is True))])
    return out


def sec_refs(refs):
    u"""F1〜F5 の並べる数(読むだけ)。P32E の数の claim と GROUNDED(札を問わない全部の行)・動いた行・F1〜F4 の札の率。"""
    mv = refs["moves"][u"集計"]
    forms = collections.OrderedDict()
    for f in (u"F1", u"F2", u"F3", u"F4", u"F5"):
        b = mv[u"形別"][f]
        n, g = b[u"数の claim の数"][u"P32E"], b[u"GROUNDED の数"][u"P32E"]
        forms[f] = collections.OrderedDict([(u"本", b[u"本"]), (u"P32E の数の claim", n), (u"P32E の GROUNDED", g), (u"GROUNDED 率", pct(g, n)),
                                            (u"動いた行", b[u"E-4 動いた行"]), (u"1 本あたりの動いた行", round(float(b[u"E-4 動いた行"]) / b[u"本"], 4))])
    allf = mv[u"全体"]
    labels = collections.OrderedDict()
    for f in (u"F1", u"F2", u"F3", u"F4"):
        c = refs["prev_tally"][u"集計"][u"2 札"][u"札の分布"][f]
        labels[f] = collections.OrderedDict([(u"数の claim", c[u"数の claim"]), (u"真の率", c[u"真"][u"率"]), (u"偽の率", c[u"偽"][u"率"])])
    return collections.OrderedDict([
        (u"F1〜F5(P30E → P32E の動いた行・P32E の数の claim と GROUNDED)", forms),
        (u"F1〜F5 全体の 1 本あたりの動いた行", collections.OrderedDict([
            (u"動いた行", allf[u"E-4 動いた行"]), (u"本", allf[u"本"]), (u"1 本あたり", round(float(allf[u"E-4 動いた行"]) / allf[u"本"], 4))])),
        (u"F1〜F4 の札(前の便の tally)", labels),
        (u"F1〜F5 の前期を名指す数の割合", u"並べられない(前の便の記録は P32E の pointer を持たない)")])


def sec_a11(records, rows):
    u"""判定しない(X-11): 会社ごと・札 判定不能の中身・打ち切り・4 番目の profile の列(``sec_engine_fx`` の中。ここでは並べない)。"""
    out = collections.OrderedDict()
    comp = collections.OrderedDict()
    for d in records["gen"][u"会社の選び"][u"docID"]:
        sel = [r for r in rows if r[u"docID"] == d]
        lr = TAL.labelled(sel)
        true_rows = [r for r in lr if r[u"label"][0] == LABEL_TRUE]
        comp[d] = collections.OrderedDict([
            (u"本", len(set(r[u"name"] for r in sel))), (u"claim", len(sel)), (u"札のある数の claim", len(lr)),
            (u"札 偽", sum(1 for r in lr if r[u"label"][0] == LABEL_FALSE)), (u"札 判定不能", sum(1 for r in lr if r[u"label"][0] == u"判定不能")),
            (u"札 真の行の GROUNDED 率(%s)" % AXIS, frac(sum(1 for r in true_rows if r[AXIS][u"state"] == STATE_G), len(true_rows)))])
    out[u"会社ごと"] = comp
    ok = list(GEN.current_ok_by_name(records["gen"][u"呼び出し"]).values())
    out[u"max_tokens で打ち切られた本"] = sum(1 for c in ok if c[u"stop_reason"] == "max_tokens")
    nj = [r for r in TAL.labelled(rows) if r[u"label"][0] == u"判定不能"]
    out[u"札 判定不能の中身"] = collections.OrderedDict([
        (u"件", len(nj)), (u"確信の内訳", collections.OrderedDict(sorted(collections.Counter(r[u"label"][2] for r in nj).items()))),
        (u"形別", collections.OrderedDict((f, sum(1 for r in nj if r[u"form"] == f)) for f in FX_FORMS)),
        (u"%s の state" % AXIS, collections.OrderedDict(sorted(collections.Counter(r[AXIS][u"state"] for r in nj).items())))])
    out[u"行の軸に無い鍵(他の profile にだけ在る数の claim)"] = sum(sum(b[u"行の軸に無い鍵の数"].values()) for b in records["claims"][u"本"] if not b.get(u"欠け"))
    out[u"対応が付かなかった本(並びが合わない・鍵が一意でない・軸に無い鍵)"] = sum(1 for b in records["claims"][u"本"] if not b.get(u"欠け") and not b[u"対応"])
    return out


def build_fx(records, refs=None):
    u"""記録 4 つ(gen・claims・labels・inject)から §1 の全部を 形 × model × profile で集計する(refs = F1〜F5 の並べる数の元。None なら repo の記録を読む)。"""
    refs = load_refs() if refs is None else refs
    rows = TAL.claim_rows(records)
    books = records["claims"][u"本"]
    T = collections.OrderedDict()
    T[u"1 配線"] = sec_wiring_fx(records)
    T[u"2 札"] = TAL.sec_labels(records, rows)
    T[u"3 engine の判定(無改変)"] = sec_engine_fx(rows)
    T[u"4 profile の差"] = sec_moves_fx(rows, books)
    T[u"5 注入"] = inject_summary_fx(records["inject"][u"行"])
    T[u"5-1 T9 の通した行の窓の手がかり"] = sec_inject_period(records["inject"][u"行"])
    T[u"6 形の性質"] = sec_shape_fx(rows)
    T[u"7 F1〜F5 との並べ"] = sec_refs(refs)
    T[u"X-11 判定しない"] = sec_a11(records, rows)
    return T


def judge_fx(T):
    u"""{X-n: {判定, 値}}。値は判定の根拠にした数(門が結果の文書の表と照らす)。分母 0 の率は None = 外れ。"""
    J = collections.OrderedDict()
    w = T[u"1 配線"]
    n_books = w[u"生成できて %s の数の claim が %d 以上ある本" % (AXIS, X1_MIN_CLAIMS)]
    cost = w[u"費用 USD(実費。記録の cost_usd の合計)"]
    capped = TAL.is_cap_stop(w[u"止めた理由"])
    ok1 = n_books >= X1_MIN_BOOKS and between(cost, X1_COST) and not capped
    J["X-1"] = {u"判定": HIT if ok1 else MISS, u"値": collections.OrderedDict([
        (u"生成できた本", w[u"生成できた本"]), (u"数の claim が %d 以上の本" % X1_MIN_CLAIMS, n_books), (u"費用 USD", cost), (u"上限で止まった", capped),
        (u"上限でない停止(字)", w[u"上限でない停止(字)"])])}
    med = collections.OrderedDict((f, (w[u"形 × model"][f][u"%s の数の claim の数" % AXIS] or {}).get(u"中央値")) for f in FX_FORMS)
    J["X-2"] = {u"判定": HIT if all(between(med[f], X2_BOUNDS[f]) for f in FX_FORMS) else MISS, u"値": med}
    E = T[u"3 engine の判定(無改変)"][AXIS]
    g = collections.OrderedDict((f, E[f][u"札 真の行の GROUNDED 率"][u"率"]) for f in FX_FORMS)
    f8_top = g["F8"] is not None and all(g[f] is not None and g["F8"] > g[f] for f in FX_FORMS if f != "F8")
    J["X-3"] = {u"判定": HIT if all(between(g[f], X3_BOUNDS[f]) for f in FX_FORMS) and f8_top else MISS,
                u"値": collections.OrderedDict(list(g.items()) + [(u"F8 が最高", f8_top)])}
    S = T[u"6 形の性質"]
    yen_rate = S["F8"][u"うち百万円の書き方"][u"率"]
    J["X-4"] = {u"判定": HIT if yen_rate is not None and yen_rate >= X4_MIN else MISS,
                u"値": collections.OrderedDict([(u"F8 の円族の数", S["F8"][u"円族の数"]), (u"百万円の書き方の率", yen_rate)])}
    f9 = S["F9"]
    share = f9[u"前期を名指す数の割合"][u"率"]
    cues = f9[u"前期を名指す数の手がかり"]
    win, clause = cues[u"窓の手がかりが真"][u"率"], cues[u"節の手がかりだけが真"][u"率"]
    ok5 = between(share, X5_PRIOR) and between(win, X5_WINDOW) and between(clause, X5_CLAUSE)
    J["X-5"] = {u"判定": HIT if ok5 else MISS, u"値": collections.OrderedDict([
        (u"F9 の前期を名指す数の割合", share), (u"窓の手がかりが真", win), (u"節の手がかりだけが真", clause), (u"どちらも偽", cues[u"どちらも偽"][u"率"]),
        (u"全形の前期を名指す数の割合", collections.OrderedDict((f, S[f][u"前期を名指す数の割合"][u"率"]) for f in FX_FORMS))])}
    I = T[u"5 注入"]
    t9 = collections.OrderedDict((f, I[FX_INJECT_TYPES[3]][AXIS][u"形別"][f][PASS][u"率"]) for f in FX_FORMS)
    P = T[u"5-1 T9 の通した行の窓の手がかり"]["F9"]
    major = P[u"通した行"] > 0 and P[u"通した行のうち窓の手がかり偽"] * 2 > P[u"通した行"]
    ok6 = between(t9["F9"], X6_F9) and all(between(t9[f], X6_OTHER) for f in ("F6", "F7", "F8")) and major
    J["X-6"] = {u"判定": HIT if ok6 else MISS, u"値": collections.OrderedDict(list(t9.items()) + [
        (u"F9 の通した行", P[u"通した行"]), (u"うち窓の手がかり偽", P[u"通した行のうち窓の手がかり偽"]), (u"過半が窓の手がかり偽", major)])}
    L = T[u"2 札"][u"札の分布"]
    f_rate = collections.OrderedDict((f, L[f][LABEL_FALSE][u"率"]) for f in FX_FORMS)
    t_rate = L[u"全体"][LABEL_TRUE][u"率"]
    ok7 = all(between(f_rate[f], X7_BOUNDS[f]) for f in FX_FORMS) and t_rate is not None and t_rate >= X7_TRUE_MIN
    J["X-7"] = {u"判定": HIT if ok7 else MISS, u"値": collections.OrderedDict(list(f_rate.items()) + [(u"全体の札 真の率", t_rate)])}
    passes = collections.OrderedDict()
    for t in ("T1_VALUE", "T5_COINCIDENT", "T8_REL"):
        for f in FX_FORMS:
            passes[u"%s %s 通した率" % (t, f)] = I[t][AXIS][u"形別"][f][PASS][u"率"]
    ok8 = all(v is not None and v <= X8_PASS_MAX for v in passes.values())
    J["X-8"] = {u"判定": HIT if ok8 else MISS, u"値": passes}
    gw = collections.OrderedDict()
    for f in FX_FORMS:
        for wr in TAL.WRITERS:
            gw[(f, wr)] = E[TAL.cell_key(f, wr)][u"札 真の行の GROUNDED 率"][u"率"]
    pair = collections.OrderedDict((f, (abs(gw[(f, "W1")] - gw[(f, "W2")]) if gw[(f, "W1")] is not None and gw[(f, "W2")] is not None else None)) for f in FX_FORMS)
    spread = collections.OrderedDict()
    for wr in TAL.WRITERS:
        vals = [gw[(f, wr)] for f in FX_FORMS]
        spread[wr] = (max(vals) - min(vals)) if all(v is not None for v in vals) else None
    pair_max = max(pair.values()) if all(v is not None for v in pair.values()) else None
    ok9 = pair_max is not None and pair_max <= X9_PAIR_MAX and all(v is not None and v >= X9_SPREAD_MIN for v in spread.values())
    J["X-9"] = {u"判定": HIT if ok9 else MISS, u"値": collections.OrderedDict([
        (u"形ごとの W1 と W2 の差の絶対値", collections.OrderedDict((f, round(v, 1) if v is not None else None) for f, v in pair.items())),
        (u"model ごとの形の幅", collections.OrderedDict((k, round(v, 1) if v is not None else None) for k, v in spread.items()))])}
    M = T[u"4 profile の差"][u"P30E → P32E"]
    R_ = T[u"7 F1〜F5 との並べ"][u"F1〜F5 全体の 1 本あたりの動いた行"]
    f9_per, ref_per = M["F9"][u"1 本あたりの動いた行"], R_[u"1 本あたり"]
    ok10 = f9_per is not None and ref_per is not None and f9_per >= X10_RATIO * ref_per
    J["X-10"] = {u"判定": HIT if ok10 else MISS, u"値": collections.OrderedDict([
        (u"F9 の動いた行", M["F9"][u"動いた行"]), (u"F9 の本", M["F9"][u"本"]), (u"F9 の 1 本あたり", f9_per), (u"F1〜F5 の 1 本あたり", ref_per)])}
    J["X-11"] = {u"判定": NOJ, u"値": collections.OrderedDict([
        (u"打ち切り", T[u"X-11 判定しない"][u"max_tokens で打ち切られた本"]), (u"札 判定不能", T[u"X-11 判定しない"][u"札 判定不能の中身"][u"件"]),
        (u"%s の列(並べるだけ)" % FX_PROFILES[3], T[u"3 engine の判定(無改変)"][FX_PROFILES[3]][u"全体"][u"4 state"])])}
    return J


def render_table(J):
    u"""結果の文書に貼る表(``<!-- 門:start pred -->`` の中。門が文書の表と一行も違わないことを見る)。"""
    return TAL.render_table(J)


def tally_record(records, input_sha, prev_sha, head, refs=None):
    u"""tally の記録(``fx_tally``)。records = gen・claims・labels・inject の 4 つ。input_sha・prev_sha = それぞれ記録の sha256 の欄(試験は {} を渡す)。"""
    T = build_fx(records, refs)
    J = judge_fx(T)
    return collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT), (u"step", restep(u"AI の形 4 × model 2 ― 集計と封 §2 の X-1〜X-10 の判定(0 USD)")),
        (u"HEAD の commit", head), (u"この script の sha256", GEN.sha256_file(os.path.abspath(__file__))),
        (u"差し替え", swap_field()),
        (u"入力の記録の sha256", input_sha), (u"前の便の記録の sha256", prev_sha),
        (u"集計", T), (u"予測の判定", J),
        (u"当たり", sum(1 for v in J.values() if v[u"判定"] == HIT)), (u"外れ", sum(1 for v in J.values() if v[u"判定"] == MISS)),
        (u"判定しない", sum(1 for v in J.values() if v[u"判定"] == NOJ)), (u"key_leaks", [])])


# ======================================================================================================
def run_gen(root=ROOT, say=print, **kw):
    bad = wiring_problems() + prev_problems(root)
    if bad:
        raise Stop(u"**差し替えか前の便の実測の平均が合わない: %s。止める**" % u" / ".join(bad))
    return GEN.run(root=root, say=say_fx(say), **kw)


def run_labels(root=ROOT, out=None, **kw):
    bad = wiring_problems(NOT_NEEDED_AFTER_GEN)
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    out = out or os.path.join(root, LAB.LABELS_REL)
    LAB.run(root=root, out=out, **kw)
    return restamp_json(out, kw.get("key_value"))


def run_tally(root=ROOT, out=None, say=print):
    bad = wiring_problems(NOT_NEEDED_AFTER_GEN)
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    out = out or os.path.join(root, TAL.TALLY_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    records = TAL.load_records(root)
    refs = load_refs(root)
    rec = tally_record(records, collections.OrderedDict((k, GEN.sha256_file(os.path.join(root, v))) for k, v in TAL.REC_REL.items()),
                       collections.OrderedDict([("moves_200", GEN.sha256_file(os.path.join(root, MOVES_REL))), ("tally_2026-11-03", GEN.sha256_file(os.path.join(root, PREV_TALLY_REL)))]),
                       GEN.git_head(os.path.dirname(root)), refs)
    text = json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    if GEN.key_leaks(text, None, long_alnum=False):
        raise Stop(u"**記録に鍵らしい字が在る。書かずに止める**")
    GEN.write_text(out, text)
    say(render_table(rec[u"予測の判定"]))
    say(u"-> %s" % out)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", default="gen", choices=("gen", "judge", "inject", "labels", "tally"))
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true", help="gen: 見積りと本数だけ(通信しない・鍵は読まない)")
    ap.add_argument("--only", default=None, help="gen・judge・inject: この docID の本だけ")
    ap.add_argument("--resume", action="store_true", help="gen: 既に在る文は飛ばして続ける")
    ap.add_argument("--procs", type=int, default=1, help="judge・inject の並列数")
    ap.add_argument("--new-cache", default=None, help="置き場所を替える(使い捨ての確かめ用。本番は替えない)")
    a = ap.parse_args(argv)
    if a.cmd == "gen":
        run_gen(root=a.root, dry_run=a.dry_run, only=a.only, resume=a.resume, out=a.out, new_cache=a.new_cache)
    elif a.cmd == "judge":
        bad = wiring_problems(NOT_NEEDED_AFTER_GEN)
        if bad:
            raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
        RUN.run_judge(root=a.root, procs=a.procs, only=a.only, out=a.out, new_cache=a.new_cache)
    elif a.cmd == "inject":
        run_inject_fx(root=a.root, procs=a.procs, only=a.only, out=a.out, new_cache=a.new_cache)
    elif a.cmd == "labels":
        run_labels(root=a.root, out=a.out, new_cache=a.new_cache)
    else:
        run_tally(root=a.root, out=a.out)


if __name__ == "__main__":
    main()
