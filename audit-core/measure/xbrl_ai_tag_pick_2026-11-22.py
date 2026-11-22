# -*- coding: utf-8 -*-
u"""封 docs/XBRL_AI_TAG_PICK_SEAL_2026-11-22.md(XD0 ― 行の字と標準の表だけでは要素が 1 つに決まらない行で、表の中の位置の字を渡した LLM の席は正しい要素を選べるか。2 つの席が一致した行だけを通すと、誤った選びはどれだけ止まるか)の測定。
**有料(LLM の席 = Anthropic の API を呼ぶ)。** 走らせるのは司令塔だけ。``--dry-run``・``--check`` は鍵を読まず通信しない(0 USD)。engine(``core/``・``adapters/``)は 1 行も変えない。
行の切り出し・見出し・計算書の種類・段 3 の候補・類は便 XG1 の script(``measure/xbrl_tag_narrow_2026-11-21.py``)を importlib で読んで呼ぶ(写さない)。

    python3 measure/xbrl_ai_tag_pick_2026-11-22.py --dry-run             # 0 USD。本番と同じ関数で全部の指示文を組み、行の数・字数・見積り・配線の確認を出す。記録は書かない
    ANTHROPIC_API_KEY=... python3 measure/xbrl_ai_tag_pick_2026-11-22.py --trial     # 有料。試しの 5 行 × 2 席に 1 回ずつ(10 回)。形だけ見る
    ANTHROPIC_API_KEY=... python3 measure/xbrl_ai_tag_pick_2026-11-22.py [--resume]  # 有料。本番(394 行 × 2 席)。試しが済んでいること。全部済んだときにだけ記録を書く
    python3 measure/xbrl_ai_tag_pick_2026-11-22.py --check               # 0 USD。記録を材料と置き場の途中の答えから数え直して照らす。通信しない

守り(封 §3):
  - 鍵は環境変数 ``ANTHROPIC_API_KEY`` だけから読む(.env は読まない)。値は印字・記録・例外の文に通さない。記録は書く前と書いた後に検査する。
  - 上限 ``COST_CAP_USD``(5 USD。試し・やり直し・中断した呼び出しを含む全部)を字で留める。走らせる前の見積り(試しの 10 回 + 本番の 788 回。やり直しは入れない)が上限を超えるなら 1 回も呼ばない。
    走っている間も、使った額(返った usage で。返らなかった呼び出しは見積りの額で)が上限に届くなら止まる。試しの額は本番に引き継ぐ。
  - 再試行は 429 / 5xx のときだけ最大 2 回(``xbrl_aiforms_gen_2026-11-03.py`` の ``call_with_retry`` をそのまま使う)。答えが読めないときは同じ指示文でもう 1 回だけ呼ぶ(封 §2-3。試しは 1 回だけ)。
  - 送った文と返った text は ``~/.cache/audit-core/ai_tag_pick_2026-11-22/``(試しは ``trial/``・本番は ``prod/``)にだけ置く(追跡しない)。記録 ``fixtures/xbrl/cd8/ai_tag_pick_2026-11-22.json`` は本番が全部済んだときにだけ書く。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 送る行の順(本番): 類 A の選ばれた行と類 W の行を混ぜ、書類の順 → file の順 → file の中の行の順の 1 本の並びにする。席ごとに行の順で呼び、1 行は主の席 → 副の席の順。
- 見出しは便 XG1 の ``file_rows`` が返した字のまま(正規化しない)。見出しが空の字(【】)でも「(なし)」にはしない(無いのは None のときだけ)。
- 「前の行」の字は、同じ file の中の全部の行(行の状態を問わない)の ``_row_label`` → ``norm_label`` のうち空でないものの後ろから 12 個。
- 試しと本番は別の途中の答え(``trial/``・``prod/``)。試しの答えは本番の数に入れない。本番は試しの 10 回(1 行 1 席に 1 回以上)が済んでいなければ止まる。
- 見積りは「まだ 1 回も呼んでいない(行, 席)」を 1 回ずつ数える(やり直しは入れない)。使った額は試し + 本番。
- 計算書の種類は 貸借・損益・キャッシュフロー・株主資本等変動(便 XG1 の ss)・種類なし の 5 つで数える(封は 4 つ。ss が在れば 1 つ増えるだけ)。XD0-8 の「種類の在る行」は貸借・損益・キャッシュフローだけ(封の字のとおり)。ss は別の行に並べる。
- 記録の行には、類・候補の数・種類・席ごとの札・2 席が同じ要素を選んだか・昇順の頭が書類の要素か・席ごとの指示文の sha256・席ごとの呼び出しの数だけを置く(席ごとに並びの向きが違うので指示文の sha256 は席ごとに 2 つ)。
- 番号は席に渡した並びで要素の名に戻す(主の席は昇順・副の席は降順)。答えの 0 は「札 0」で要素に戻さない。
- 答えの読み方: NFKC のあと最初の「答え」の直後の空白を飛ばして ``:`` と整数を読む(「答え」の後ろがそれ以外なら読めない)。
- HTTP 400・401・403 は設定の誤りなので全体を止める。呼んでいる間に中断した呼び出しは見積りの額で数える。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    u"""importlib で読み込む。読み込んだ file が中で読む前の便の script は決まった名前で ``sys.modules`` に登録し直すので、読み込みの前に居た名前は読み込みの後に元の object へ戻す(自分の名前 ``mod_name`` は残す)。"""
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


N = load_module("xbrl_tag_narrow_2026-11-21.py", "tag_narrow_for_ai_tag_pick")          # 便 XG1(中に便 XG0)。行・見出し・種類・候補・類
GEN = load_module("xbrl_aiforms_gen_2026-11-03.py", "aiforms_gen_for_ai_tag_pick")     # API の版・やり直し(call_with_retry)・鍵の検査の字
W = N.W
Stop = N.Stop

SEAL_REL = "docs/XBRL_AI_TAG_PICK_SEAL_2026-11-22.md"
SEAL_COMMIT = "7bb4fa24"
SCRIPT_REL = "measure/xbrl_ai_tag_pick_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/ai_tag_pick_2026-11-22.json"
XG1_SCRIPT_REL = "measure/xbrl_tag_narrow_2026-11-21.py"
XG1_SCRIPT_SHA256 = "24159344be6b2ecf6957339b1356d8049bfe90cab1f4660be5b2f7151a7d6a33"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "ai_tag_pick_2026-11-22")
STATE_NAME = "progress.json"

# ---- 封 §1・§2-1 の数(字で留める。違えば止める。封の門が封の字と照らす)
DEV_DOCS = 5                                                # 開発 = file 名の順の 1〜5 本目。本番 = 残り
CLASS_ORDER = ("U", "A", "N", "W")
EXPECT_WIRE = collections.OrderedDict([
    ("dev", collections.OrderedDict([("U", 1033), ("A", 208), ("N", 18), ("W", 2)])),
    ("prod", collections.OrderedDict([("U", 12444), ("A", 2603), ("N", 387), ("W", 68)]))])
PICK_STEP = 8                                               # 本番の類 A の行の番号が 8 で割り切れる行
EXPECT_A = 326
EXPECT_W = 68
EXPECT_ROWS = 394
TRIAL_ROWS = 5                                              # 開発の類 A の頭 5 行
PREV_N = 12                                                 # 前の行の字の数(後ろから)
PREV_SEP = u" / "

# ---- 封 §3 の決めごと(字で留める。門が封の字と照らす)
SEATS = ("claude-sonnet-5-5", "claude-haiku-5-5")           # 主の席・副の席
SEAT_TAG = collections.OrderedDict([("claude-sonnet-5-5", u"主"), ("claude-haiku-5-5", u"副")])
SEAT_FILE = {"claude-sonnet-5-5": "main", "claude-haiku-5-5": "sub"}
SEAT_REVERSE = {"claude-sonnet-5-5": False, "claude-haiku-5-5": True}      # 候補の並び: 主は昇順・副は降順
MAX_TOKENS = 100
TEMPERATURE = None                                          # temperature の欄は送らない(便 LX の実測: 送ると HTTP 400)
THINKING = {"claude-sonnet-5-5": {"type": "between_tools"}, "claude-haiku-5-5": {"type": "disabled"}}
COST_CAP_USD = 5.0
PRICE_IN = 5.0                                              # USD / M tokens(両席に当てる保守的な字)
PRICE_OUT = 25.0
MAX_ANSWER_ATTEMPTS = 2                                     # 封 §2-3: 読めなければもう 1 回だけ
KEY_ENV = GEN.KEY_ENV
STOP_HTTP = (400, 401, 403)

# ---- 封 §2-2 の指示文(字で留める。system は無し = user の 1 message)。封の門が封の文書の code block と 1 字ずつ照らす
PROMPT_TEMPLATE = u"""次は、日本の上場企業の有価証券報告書の中の表の 1 つの行です。この行に付ける XBRL の要素を、候補の中から 1 つ選んでください。渡した字だけで判断し、推測で埋めないでください。

表の見出し: {HEADING}
この行より前の行(上から順): {PREV}
この行: {ROW}
候補:
{CANDS}

答えは 1 行だけ、「答え: 3」の形で候補の番号を書いてください。候補の中に正しい要素が無いと考えるとき、または渡した字だけでは 1 つに決められないときは「答え: 0」と書いてください。説明は書かないでください。"""
PLACEHOLDERS = (u"{HEADING}", u"{PREV}", u"{ROW}", u"{CANDS}")
_PH_RE = re.compile("|".join(re.escape(p) for p in PLACEHOLDERS))
NO_HEADING = u"(なし)"
NO_PREV = u"(なし)"

NO_ANSWER = u"答えなし"
L_OK, L_BAD, L_ZERO = u"正", u"誤", u"0"
LABELS = (L_OK, L_BAD, L_ZERO, NO_ANSWER)
KIND_NAME = collections.OrderedDict([("bs", u"貸借"), ("pl", u"損益"), ("cf", u"キャッシュフロー"), ("ss", u"株主資本等変動"), (None, u"種類なし")])
KINDS_WITH = (u"貸借", u"損益", u"キャッシュフロー")        # XD0-8 の「種類の在る行」(封の字のとおり)
NO_KIND = u"種類なし"
BANDS = collections.OrderedDict([(u"候補 2", lambda n: n == 2), (u"候補 3〜6", lambda n: 3 <= n <= 6), (u"候補 7 以上", lambda n: n >= 7)])

K_WIRE = u"配線の確認(封 §1・§2-1。予測ではない。違えば止まる)"
K_TALLY = u"数えるもの(封 §2-5 の 1〜4)"
K_LINES = u"並べる 2 行(封 §2-5 の 5。類 A)"
K_CALLS = u"呼び出しの記録(封 §2-5 の 6)"
K_TRIAL = u"試しの 10 回(封 §3。本番の数に入れない)"
K_PRED = u"予測の判定に要る数(XD0-1〜XD0-11。当たり・外れは結果の文書で)"
K_SUSPECT = u"先に自分の欠陥を疑う条件の数(封 §5)"

ROW_COLUMNS = [u"書類の番号", u"類", u"候補の数", u"計算書の種類", u"主の席の札", u"副の席の札", u"2 席が同じ要素を選んだ", u"昇順の頭の候補が書類の要素と同じ",
               u"主の席の指示文の sha256", u"副の席の指示文の sha256", u"主の席の呼び出しの数", u"副の席の呼び出しの数"]
(C_DOC, C_CLS, C_NC, C_KIND, C_MLAB, C_SLAB, C_SAME, C_HEAD1, C_MSHA, C_SSHA, C_MCALL, C_SCALL) = range(12)
CALL_COLUMNS = [u"行の番号", u"席", u"答えの回", u"中断した呼び出し", u"HTTP の状態", u"HTTP の再試行の数", u"stop_reason", u"block の type の並び", u"入力 token", u"出力 token",
                u"返った usage の USD", u"見積りで数えた USD", u"返った text の字数", u"答えが読めた"]
(K_ROW, K_SEAT, K_ATT, K_ABORT, K_HTTP, K_RETRY, K_STOP, K_BLOCKS, K_TIN, K_TOUT, K_USD_U, K_USD_E, K_CHARS, K_OK) = range(14)

LIMITS = (
    u"行の字は提出済みの書類の字。AI や人がこれから書く紙の字ではない。候補は便 XG1 の絞りの結果で、絞りが答えを落とした行は類 W に入っている",
    u"「正」は「提出済みの書類の要素と同じ」の意味。書類の要素が正しいことは確かめていない",
    u"送る行は答えを使って選んだ(類 A = 候補の中に答えが在る・類 W = 無い)。8 行に 1 行。有報だけ・67 本は無作為でない。2 つの類を足した率は書かない。類 U・類 N は送らない",
    u"指示文は司令塔が書いた。盲検でない。別の指示文・別の渡す字なら数は変わる",
    u"席と司令塔は同じ系統の model。2 つの席も同じ系統で、一致には系統の癖の一致が混ざる",
    u"席の答えは呼ぶたびに変わりうる。数は 1 回の呼び出しの記録で、繰り返しの幅は測らない。model の版が変われば同じ数は出ない",
    u"測るのは要素の選びだけ。文脈(期・連結か単体か・member)・単位・符号・表の外の fact・文章の fact・提出者別タクソノミの要素を新しく作る判断は測らない",
    u"「AI が XBRL を作れる」「紙を AI が書ける」は、この便からは言えない(要素の選びの、候補が残る行の、8 行に 1 行だけ)",
    u"engine は変えていない",
    u"記録は行の字・見出しの字・前の行の字・要素の名・値・会社名・証券コード・EDINET コード・docID・file の名・席の返した text を持たない")

od = collections.OrderedDict


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def dumps(o):
    return json.dumps(o, ensure_ascii=False, indent=2) + u"\n"


def rate(n, d):
    return od([(u"行", n), (u"分母", d), (u"%", N.pct1(n, d))])


class CapStop(Exception):
    u"""上限で止める(1 回の transport の呼び出しの前)。文言に鍵・文を入れない。"""


# ======================================================================================================
# 行(材料から引く。封 §1・§2-1)。便 XG1 の関数を呼ぶ
def row_label(rowtext):
    u"""行の字(便 XG1 と同じ ``_row_label`` → ``norm_label``)。"""
    return N.norm_label(N.I._row_label(rowtext) or u"")


def previous_labels(nonempty):
    u"""前の行の字(後ろから ``PREV_N`` 個)。``nonempty`` は同じ file の中のそこまでの空でない行の字。"""
    return list(nonempty[-PREV_N:])


def note_label(nonempty, lab):
    u"""行の字が空でなければ「そこまでの空でない行の字」に足す(行の状態は問わない)。"""
    if lab:
        nonempty.append(lab)


def read_docs(docs_dir=None, taxonomy_dir=None, taxzip=None, dev_only=False, want=None, say=print):
    u"""置き場 → (候補の行の列, 書類の群ごとの類の数, 漏れの検査に使う材料, 材料の欄)。候補の行 = 類 A・W の行。
    書類の選び方・行の切り出し・見出し・種類・業種・段 3 の候補・類は便 XG1 の関数。``dev_only`` は開発の書類だけ読む(封の門の例の確かめ用)。"""
    docs = W.select_docs(docs_dir or N.DOCS_DIR, N.DOCS_WANT if want is None else want)
    label_data, label_sha = W.read_label_bytes(taxonomy_dir or N.TAXONOMY_DIR)
    l2 = W.label_tables(label_data)[0]
    tax, zip_sha, tmat = N.load_tax(taxzip or N.TAXZIP_PATH, True)
    ids = [d[0] for d in docs]
    ecodes = set()
    for _stem, _p, xs in docs:
        for x in xs:
            ecodes.update(re.findall(r"E\d{5}", x))
    rows = []
    counts = od((g, od((c, 0) for c in CLASS_ORDER)) for g in ("dev", "prod"))
    inds = set()
    for n, (_stem, p, _xs) in enumerate(docs, 1):
        group = "dev" if n <= DEV_DOCS else "prod"
        if dev_only and group == "prod":
            break
        with zipfile.ZipFile(p) as z:
            texts = sorted(N.doc_texts(z), key=lambda t: t[0])
        dei = N.dei_values(texts)
        inds.update(v for v in dei if v)
        for fi, (_fname, text) in enumerate(texts):
            nonempty = []
            for ri, (rowtext, head) in enumerate(N.file_rows(text)):
                lab = row_label(rowtext)
                st = W.row_status(rowtext)
                if st[0] == "ok":
                    _k, T, E = st
                    kind = N.kind_of(head)
                    ind = N.industry_of(head, dei, tax["folders"]) if kind is not None else None
                    c3 = N.narrow(set(l2.get(T, ())), kind, ind, tax)[2]
                    cls = N.classify_stage(T, E, c3)
                    counts[group][cls] += 1
                    if cls in ("A", "W"):
                        rows.append(od([("group", group), ("doc", n), ("ord", (n, fi, ri)), ("cls", cls), ("kind", kind), ("heading", head), ("prev", previous_labels(nonempty)),
                                        ("T", T), ("E", E), ("cands", sorted(c3))]))
                note_label(nonempty, lab)
    secret = [set(), set(), ids, ecodes, set(), inds]
    material = od([(u"書類の本数", len(docs)), (u"書類の file 名の並びの sha256", W.order_sha256(ids)), (u"標準ラベルの file の sha256", label_sha),
                   (u"標準タクソノミの zip の sha256", zip_sha), (u"便 XG1 の script の sha256", XG1_SCRIPT_SHA256)])
    material.update(tmat)
    return rows, counts, secret, material


def check_wire(counts, expect=None):
    u"""段 3 の類の数(開発・本番)が封の字と同じか。違えば止める。``counts`` に無い群は見ない(開発だけ読んだとき)。"""
    expect = EXPECT_WIRE if expect is None else expect
    for g, want in expect.items():
        got = counts.get(g)
        if got is None or sum(got.values()) == 0:
            continue
        if list(got.values()) != list(want.values()):
            raise Stop(u"**段 3 の類の数(%s)が封の字と違う。止める**" % ({"dev": u"開発", "prod": u"本番"}.get(g, g)))


def make_item(r, group, expect_tag=None):
    u"""候補の行 → 送る行(席ごとの候補の並び・指示文・sha256 つき)。"""
    cands = od()
    prompts = od()
    shas = od()
    for seat in SEATS:
        cl = sorted(r["cands"], reverse=SEAT_REVERSE[seat])
        cands[seat] = cl
        prompts[seat] = build_prompt(r["heading"], r["prev"], r["T"], cl)
        shas[seat] = sha256_text(prompts[seat])
    return od([("group", group), ("doc", r["doc"]), ("cls", r["cls"]), ("kind", r["kind"]), ("ncand", len(r["cands"])), ("E", r["E"]), ("T", r["T"]), ("heading", r["heading"]),
               ("prev", r["prev"]), ("cands", cands), ("prompt", prompts), ("sha", shas)])


def select_items(rows, counts, expect=None, expect_sel=None, step=PICK_STEP, trial_rows=TRIAL_ROWS):
    u"""候補の行 → (試しの行, 本番の行, 配線の確認の欄)。配線の確認(類の数・行の数)に違えば止める。
    本番 = 本番の類 A の行を書類・file・行の順に並べて番号が ``step`` で割り切れる行 + 本番の類 W の全部(書類・file・行の順の 1 本の並び)。試し = 開発の類 A の頭 ``trial_rows`` 行。"""
    check_wire(counts, expect)
    want_a, want_w, want_rows, want_trial = (EXPECT_A, EXPECT_W, EXPECT_ROWS, TRIAL_ROWS) if expect_sel is None else expect_sel
    ordered = sorted(rows, key=lambda r: r["ord"])
    prod_a = [r for r in ordered if r["group"] == "prod" and r["cls"] == "A"]
    picked_a = [r for i, r in enumerate(prod_a) if i % step == 0]
    prod_w = [r for r in ordered if r["group"] == "prod" and r["cls"] == "W"]
    if len(picked_a) != want_a or len(prod_w) != want_w or len(picked_a) + len(prod_w) != want_rows:
        raise Stop(u"**送る行の数が封の字(類 A %d・類 W %d・合わせて %d)と違う(類 A %d・類 W %d)。止める**" % (want_a, want_w, want_rows, len(picked_a), len(prod_w)))
    dev_a = [r for r in ordered if r["group"] == "dev" and r["cls"] == "A"]
    trial_sel = dev_a[:trial_rows]
    if len(trial_sel) != want_trial:
        raise Stop(u"**試しの行の数が %d でない(%d)。止める**" % (want_trial, len(trial_sel)))
    prod_sel = sorted(picked_a + prod_w, key=lambda r: r["ord"])
    t_items = [make_item(r, "trial") for r in trial_sel]
    p_items = [make_item(r, "prod") for r in prod_sel]
    if any(len(it["cands"][SEATS[0]]) < 1 or it["ncand"] < 1 for it in t_items + p_items):
        raise Stop(u"**候補が無い行を送ろうとした。止める**")
    wire = od([(u"段 3 の類の数(開発)", od(counts["dev"])), (u"段 3 の類の数(本番)", od(counts["prod"])),
               (u"本番の類 A の行(8 行に 1 行)", len(picked_a)), (u"本番の類 W の行", len(prod_w)), (u"送る行(本番)", len(p_items)), (u"試しの行", len(t_items)),
               (u"類 W のうち候補が 1 つの行", sum(1 for r in prod_w if len(r["cands"]) == 1)),
               (u"見出しが無い行(%s)" % NO_HEADING, sum(1 for it in p_items if it["heading"] is None)),
               (u"見出しが空の字の行(【】)", sum(1 for it in p_items if it["heading"] == u"")),
               (u"見出しに改行を含む行", sum(1 for it in p_items if it["heading"] and (u"\n" in it["heading"] or u"\r" in it["heading"]))),
               (u"前の行が無い行(%s)" % NO_PREV, sum(1 for it in p_items if not it["prev"])),
               (u"指示文の本数(本番 + 試し)", (len(p_items) + len(t_items)) * len(SEATS))])
    return t_items, p_items, wire


def secret_of(base, items):
    u"""記録に書かないもの(便 XG1 の check_clean の組)。行の字・前の行の字・見出しの字(正規化)・要素の名は送る行から足す。"""
    labels, elems, ids, ecodes, heads, inds = base
    labels, elems, heads = set(labels), set(elems), set(heads)
    for it in items:
        labels.add(it["T"])
        labels.update(it["prev"])
        elems.add(it["E"])
        elems.update(it["cands"][SEATS[0]])
        if it["heading"] is not None:
            heads.add(N.norm_label(it["heading"]))
    return (labels, elems, ids, ecodes, heads, inds)


def collect_all(root=ROOT, docs_dir=None, taxonomy_dir=None, taxzip=None, say=print):
    u"""便 XG1 の script の sha256 を確かめ、材料から送る行を作る。通信しない・鍵を読まない。"""
    p = os.path.join(root, XG1_SCRIPT_REL)
    if not os.path.isfile(p) or sha256_file(p) != XG1_SCRIPT_SHA256:
        raise Stop(u"**便 XG1 の script の sha256 が封の後に実測して留めた字と違う。止める**")
    rows, counts, secret, material = read_docs(docs_dir, taxonomy_dir, taxzip, say=say)
    t_items, p_items, wire = select_items(rows, counts)
    return od([("trial", t_items), ("prod", p_items), ("wire", wire), ("secret", secret_of(secret, t_items + p_items)), ("material", material)])


# ======================================================================================================
# 指示文(封 §2-1・§2-2)・答えの読み方(封 §2-3)・見積り(封 §3)
def build_prompt(heading, prev, row, cands):
    u"""指示文の全体。``{HEADING}`` ``{PREV}`` ``{ROW}`` ``{CANDS}`` だけを 1 回の走査で埋める(渡した字の中の ``{…}`` が再び置き換わらない)。
    ``heading`` が None なら ``(なし)``・``prev`` が空なら ``(なし)``・候補は 1 から番号を振って 1 行に 1 つ。"""
    values = {u"{HEADING}": NO_HEADING if heading is None else heading,
              u"{PREV}": PREV_SEP.join(prev) if prev else NO_PREV,
              u"{ROW}": row,
              u"{CANDS}": u"\n".join(u"%d. %s" % (i + 1, c) for i, c in enumerate(cands))}
    return _PH_RE.sub(lambda m: values[m.group(0)], PROMPT_TEMPLATE)


_ANS_RE = re.compile(r"\s*:\s*([0-9]+)")


def read_answer(text, stop_reason, ncand):
    u"""返った text → 候補の番号(0 以上 ``ncand`` 以下の整数)か None(読めない)。text を NFKC にかけ、最初の「答え」の後ろの空白を飛ばして ``:`` に続く最初の整数を読む。
    stop_reason が end_turn でない・text が 0 字・範囲の外は None。"""
    if stop_reason != "end_turn" or not isinstance(text, str) or not text:
        return None
    t = unicodedata.normalize("NFKC", text)
    i = t.find(u"答え")
    if i < 0:
        return None
    m = _ANS_RE.match(t, i + len(u"答え"))
    if m is None:
        return None
    v = int(m.group(1))
    return v if 0 <= v <= ncand else None


def pick_of(it, seat, num):
    u"""番号 → その席に渡した並びの要素の名。0・None は None。"""
    if not num:
        return None
    return it["cands"][seat][num - 1]


def seat_label(it, seat, num):
    u"""席の札(正・誤・0・答えなし)。類 W は候補の中に書類の要素が無いので「正」は出ない。"""
    if num is None:
        return NO_ANSWER
    if num == 0:
        return L_ZERO
    return L_OK if pick_of(it, seat, num) == it["E"] else L_BAD


def estimate_usd(prompt_chars):
    u"""1 回の見積り = 入力の字数 × 1.0 を token とみなす + 出力は MAX_TOKENS の全部(保守的な単価)。"""
    return (prompt_chars * PRICE_IN + MAX_TOKENS * PRICE_OUT) / 1e6


def cost_usd(input_tokens, output_tokens):
    return ((input_tokens or 0) * PRICE_IN + (output_tokens or 0) * PRICE_OUT) / 1e6


# ======================================================================================================
# API(通信する唯一の所)
def call_api(prompt, model, key):
    u"""(status, body)。HTTP の 4xx・5xx は例外にせず status で返す。例外の文には鍵を通さない(型だけ)。"""
    body = json.dumps({"model": model, "max_tokens": MAX_TOKENS, "thinking": THINKING[model],
                       "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    req = urllib.request.Request(GEN.API_URL, data=body, method="POST",
                                 headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": GEN.API_VERSION})
    try:
        with urllib.request.urlopen(req, timeout=GEN.TIMEOUT_SEC) as r:
            return r.getcode(), r.read()
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read()
        except Exception:                                # noqa: BLE001
            return e.code, b""
    except Exception as e:                               # noqa: BLE001  通信の失敗。文は捨てる
        return None, type(e).__name__.encode("ascii", "replace")


def get_key():
    key = os.environ.get(KEY_ENV)
    if not key:
        raise Stop(u"**環境変数 %s が無い。止める**" % KEY_ENV)
    return key


def parse_response(body):
    u"""HTTP 200 の返事の字 → {text, blocks, stop_reason, tin, tout} か None(形が読めない)。text は type が text の block の text だけをつなぐ。"""
    try:
        res = json.loads(body.decode("utf-8"))
        content = [b for b in res.get("content", []) if isinstance(b, dict)]
        text = u"".join(b.get("text") for b in content if b.get("type") == "text" and isinstance(b.get("text"), str))
        usage = res.get("usage") or {}
        return {u"text": text, u"blocks": [b.get("type") for b in content], u"stop_reason": res.get("stop_reason"),
                u"tin": usage.get("input_tokens"), u"tout": usage.get("output_tokens")}
    except Exception:                                    # noqa: BLE001  形が違う返事。文は捨てる
        return None


def usage_returned(status, body):
    u"""返った(usage まで読めた)呼び出しか。違えば見積りの額で数える。"""
    if status != 200:
        return False
    p = parse_response(body)
    return p is not None and isinstance(p[u"tin"], int) and isinstance(p[u"tout"], int)


def error_message_of(body, key=None, limit=300):
    u"""HTTP 4xx・5xx の本文の error.message(短く)。鍵らしい字が在れば残さない(型だけ)。読めなければ None。本文のほかの欄は残さない。"""
    try:
        m = json.loads(body.decode("utf-8"))["error"]["message"]
    except Exception:                                    # noqa: BLE001
        return None
    if not isinstance(m, str):
        return None
    m = m[:limit]
    if GEN.key_leaks(m, key, False):
        return u"(鍵らしい字が在るので残さない)"
    return m


def do_call(prompt, seat, key, transport, sleep, cum, cap, row, attempt, script_sha, ncand):
    u"""1 行 1 席 1 回の呼び出し(HTTP の再試行を含む)。(呼び出しの記録(OrderedDict), 返った text か None)。
    上限は transport を呼ぶ前に毎回見る(累計 + この呼び出しで見積りの額を数えた分 + 次の見積り > 上限 なら止める)。返らなかった呼び出しは 1 回ごとに見積りの額を数える。"""
    est = estimate_usd(len(prompt))
    meter = {"extra": 0.0}

    def metered(p, model, k):
        if cum + meter["extra"] + est > cap:
            raise CapStop()
        status, body = transport(p, model, k)
        if not usage_returned(status, body):
            meter["extra"] += est
        return status, body

    item = od([(u"row", row), (u"seat", seat), (u"attempt", attempt), (u"aborted", False), (u"prompt_sha256", sha256_text(prompt)), (u"est_usd", round(est, 6)),
               (u"script_sha256", script_sha[:16]), (u"retries", 0), (u"http_status", None), (u"stop_reason", None), (u"blocks", None), (u"tin", None), (u"tout", None),
               (u"chars", None), (u"reply_sha256", None), (u"answer", None), (u"usage_usd", 0.0), (u"est_counted_usd", 0.0), (u"cost_usd", 0.0)])
    try:
        status, body, retries = GEN.call_with_retry(prompt, seat, key, metered, sleep)
    except CapStop:
        item.update({u"attempt": None, u"aborted": True, u"capped": True, u"est_counted_usd": round(meter["extra"], 6), u"cost_usd": round(meter["extra"], 6)})
        return item, None
    item[u"retries"] = retries
    item[u"http_status"] = status
    text = None
    usable = usage_returned(status, body)
    p = parse_response(body) if status == 200 else None
    usage_cost = cost_usd(p[u"tin"], p[u"tout"]) if usable else 0.0
    if p is not None:
        text = p[u"text"]
        item.update({u"stop_reason": p[u"stop_reason"], u"blocks": p[u"blocks"], u"tin": p[u"tin"], u"tout": p[u"tout"], u"chars": len(text)})
        item[u"answer"] = read_answer(text, p[u"stop_reason"], ncand)
    if status is not None and status >= 400:
        item[u"error_message"] = error_message_of(body, key)
    item[u"usage_usd"] = round(usage_cost, 6)
    item[u"est_counted_usd"] = round(meter["extra"], 6)
    item[u"cost_usd"] = round(usage_cost + meter["extra"], 6)
    return item, text


# ======================================================================================================
# 途中の答え(``--resume`` 用。追跡しない置き場にだけ置く。試しと本番は別の置き場)
def new_state():
    return od([(u"seal", SEAL_REL), (u"calls", []), (u"in_flight", None), (u"stopped", None)])


def state_path(work):
    return os.path.join(work, STATE_NAME)


def load_state(work):
    p = state_path(work)
    if not os.path.exists(p):
        return None
    with io.open(p, encoding="utf-8") as fh:
        st = json.load(fh, object_pairs_hook=collections.OrderedDict)
    if st.get(u"seal") != SEAL_REL:
        raise Stop(u"**途中の答えの file が別の便のもの。止める**")
    return st


def save_state(work, state):
    GEN.write_text(state_path(work), json.dumps(state, ensure_ascii=False, indent=1) + u"\n")


def seat_attempts(state, row, seat):
    return [c for c in state[u"calls"] if c[u"row"] == row and c[u"seat"] == seat and not c[u"aborted"]]


def seat_answer(state, row, seat):
    u"""席の答え(番号。0 も答え)か None。"""
    for c in seat_attempts(state, row, seat):
        if c[u"answer"] is not None:
            return c[u"answer"]
    return None


def seat_done(state, row, seat, max_attempts=MAX_ANSWER_ATTEMPTS):
    return seat_answer(state, row, seat) is not None or len(seat_attempts(state, row, seat)) >= max_attempts


def state_cost(state):
    return round(sum(c[u"cost_usd"] for c in state[u"calls"]), 6)


def retire_config_failures(state):
    u"""前の走りが HTTP 400・401・403(設定の誤り)で止めた呼び出しは答えの回に数えない。額は残したまま中断した呼び出しの側へ移す(上限をすり抜けさせない)。"""
    n = 0
    for c in state[u"calls"]:
        if not c[u"aborted"] and c[u"http_status"] in STOP_HTTP:
            c[u"aborted"] = True
            c[u"attempt"] = None
            c[u"config_error"] = c[u"http_status"]
            n += 1
    return n


def resolve_in_flight(state):
    u"""前の走りが呼んでいる最中に止まっていたら、その呼び出しは見積りの額で数える(中断した呼び出しは上限をすり抜けさせない)。"""
    f = state.get(u"in_flight")
    if not f:
        return False
    state[u"calls"].append(od([(u"row", f[u"row"]), (u"seat", f[u"seat"]), (u"attempt", None), (u"aborted", True), (u"prompt_sha256", f[u"prompt_sha256"]), (u"est_usd", f[u"est_usd"]),
                               (u"script_sha256", None), (u"retries", 0), (u"http_status", None), (u"stop_reason", None), (u"blocks", None), (u"tin", None), (u"tout", None),
                               (u"chars", None), (u"reply_sha256", None), (u"answer", None), (u"usage_usd", 0.0), (u"est_counted_usd", f[u"est_usd"]), (u"cost_usd", f[u"est_usd"]),
                               (u"interrupted", True)]))
    state[u"in_flight"] = None
    return True


def reply_path(work, row, seat, attempt):
    return os.path.join(work, "replies", "%03d_%s_%d.txt" % (row, SEAT_FILE[seat], attempt))


def prompt_path(work, row, seat):
    return os.path.join(work, "prompts", "%03d_%s.txt" % (row, SEAT_FILE[seat]))


def write_prompts(items, work):
    u"""送る文を置き場に置く。既に在る file は同じ字でなければ止める。"""
    for i, it in enumerate(items):
        for seat in SEATS:
            p = prompt_path(work, i, seat)
            if os.path.exists(p):
                with io.open(p, encoding="utf-8") as fh:
                    if fh.read() != it["prompt"][seat]:
                        raise Stop(u"**置き場の送る文が今組んだ指示文と違う(行 %d)。止める**" % i)
            else:
                GEN.write_text(p, it["prompt"][seat])


def check_state(items, state, work):
    u"""途中の答えが今の指示文・今の置き場の返った text と合う(違えば止める)。"""
    for c in state[u"calls"]:
        i = c[u"row"]
        if not 0 <= i < len(items) or c[u"seat"] not in SEATS:
            raise Stop(u"**途中の答えの行の番号か席が今の行の列と合わない。止める**")
        if c[u"prompt_sha256"] != items[i]["sha"][c[u"seat"]]:
            raise Stop(u"**途中の答えの指示文の sha256 が今組んだ指示文と違う(行 %d)。止める**" % i)
        if c[u"reply_sha256"] is not None:
            p = reply_path(work, i, c[u"seat"], c[u"attempt"])
            if not os.path.exists(p):
                raise Stop(u"**途中の答えの返った text が置き場に無い(行 %d)。止める**" % i)
            with io.open(p, encoding="utf-8") as fh:
                if sha256_text(fh.read()) != c[u"reply_sha256"]:
                    raise Stop(u"**途中の答えの返った text の sha256 が記録と違う(行 %d)。止める**" % i)


def pending_estimate(items, state):
    u"""まだ 1 回も呼んでいない(行, 席)を 1 回ずつ見積った額と回数(封 §3: やり直しは見積りに入れない)。答えが在る・呼んだ(行, 席)は数えない。"""
    total, n = 0.0, 0
    for i, it in enumerate(items):
        for seat in SEATS:
            if seat_answer(state, i, seat) is None and not seat_attempts(state, i, seat):
                total += estimate_usd(len(it["prompt"][seat]))
                n += 1
    return total, n


def plan_problem(base, est, n, cap=COST_CAP_USD, say=print):
    u"""使った額 + 残りの見積り(試し + 本番。1 回ずつ)が上限を超えるなら理由の文、超えなければ None。"""
    say(u"走らせる前の確かめ: 使った額 %.4f USD + 残り %d 回の見積り %.4f USD = %.4f USD(上限 %.2f)" % (base, n, est, base + est, cap))
    if base + est > cap:
        return u"**使った額 %.4f + 残りの見積り %.4f = %.4f USD が上限 %.2f USD を超える。1 回も呼ばずに止める**" % (base, est, base + est, cap)
    return None


def run_calls(items, state, work, key, transport=call_api, sleep=None, say=print, one_attempt=False, cap=COST_CAP_USD, other_cost=0.0, other_est=0.0, other_n=0):
    u"""行の順に、行ごとに 主の席・副の席の順で呼ぶ。済んだ(行, 席)は飛ばす。一度に書く file は呼ぶたびに更新する(止まっても累計が残る)。
    ``other_cost``・``other_est`` は、もう 1 つの置き場(試しなら本番・本番なら試し)の使った額と残りの見積り(上限は全部の合計で見る)。
    ``one_attempt`` は試し(1 回だけ。読めなければ答えなし)。止める事情(上限・HTTP 400/401/403)は ``Stop``。"""
    sleep = sleep if sleep is not None else time.sleep
    this_sha = sha256_file(os.path.abspath(__file__))
    check_state(items, state, work)
    if resolve_in_flight(state) | bool(retire_config_failures(state)):
        save_state(work, state)
    est, n_pending = pending_estimate(items, state)
    problem = plan_problem(other_cost + state_cost(state), est + other_est, n_pending + other_n, cap, say)
    if problem:
        raise Stop(problem)
    write_prompts(items, work)
    max_attempts = 1 if one_attempt else MAX_ANSWER_ATTEMPTS
    n_new = 0
    for i, it in enumerate(items):
        for seat in SEATS:
            while True:
                att = seat_attempts(state, i, seat)
                if seat_answer(state, i, seat) is not None or len(att) >= max_attempts:
                    break
                attempt = len(att) + 1
                prompt = it["prompt"][seat]
                est_one = estimate_usd(len(prompt))
                state[u"in_flight"] = od([(u"row", i), (u"seat", seat), (u"prompt_sha256", it["sha"][seat]), (u"est_usd", round(est_one, 6))])
                save_state(work, state)
                item, text = do_call(prompt, seat, key, transport, sleep, other_cost + state_cost(state), cap, i, attempt, this_sha, it["ncand"])
                if text:
                    GEN.write_text(reply_path(work, i, seat, attempt), text)
                    item[u"reply_sha256"] = sha256_text(text)
                state[u"in_flight"] = None
                if item[u"cost_usd"] > 0 or not item.get(u"capped"):
                    state[u"calls"].append(item)
                n_new += 1
                if item.get(u"capped"):
                    state[u"stopped"] = u"累計 %.4f + 次の見積り %.4f が上限 %.2f USD を超える(行 %d・%s の前)" % (other_cost + state_cost(state), est_one, cap, i, SEAT_TAG[seat])
                    save_state(work, state)
                    raise Stop(u"**%s**" % state[u"stopped"])
                save_state(work, state)
                say(u"  行 %3d %s %d 回目 http=%s stop=%s block=%s 字数=%s %s 累計 %.4f USD" % (
                    i, SEAT_TAG[seat], attempt, item[u"http_status"], item[u"stop_reason"], u",".join(x or u"?" for x in (item[u"blocks"] or [])), item[u"chars"],
                    u"読めた" if item[u"answer"] is not None else u"読めない", other_cost + state_cost(state)))
                if item[u"http_status"] in STOP_HTTP:
                    say(u"  HTTP %s の断りの文: %s" % (item[u"http_status"], item.get(u"error_message")))
                    state[u"stopped"] = u"HTTP %s(設定の誤りか鍵の問題)" % item[u"http_status"]
                    save_state(work, state)
                    raise Stop(u"**HTTP %s。全体を止める**" % item[u"http_status"])
    return n_new


def all_done(items, state):
    return all(seat_done(state, i, seat) for i in range(len(items)) for seat in SEATS)


def trial_done(items, state):
    u"""試しの(行, 席)の全部が 1 回以上呼ばれている(答えが読めたかは問わない。形は司令塔が見る)。"""
    return state is not None and all(seat_attempts(state, i, seat) for i in range(len(items)) for seat in SEATS)


# ======================================================================================================
# 記録の行・呼び出しの欄
def same_pick(it, nm, ns):
    u"""2 席が(どちらも 1 以上の番号で)同じ要素の名を選んだか。席の並びが違うので要素の名に戻して比べる。"""
    if not nm or not ns:
        return False
    return pick_of(it, SEATS[0], nm) == pick_of(it, SEATS[1], ns)


def build_rows(items, state):
    u"""記録の行。1 行 = 送る行 1 つ。"""
    rows = []
    m, s = SEATS
    for i, it in enumerate(items):
        nm, ns = seat_answer(state, i, m), seat_answer(state, i, s)
        rows.append([it["doc"], it["cls"], it["ncand"], KIND_NAME[it["kind"]], seat_label(it, m, nm), seat_label(it, s, ns), same_pick(it, nm, ns),
                     it["cands"][m][0] == it["E"], it["sha"][m], it["sha"][s], len(seat_attempts(state, i, m)), len(seat_attempts(state, i, s))])
    return rows


def build_call_rows(state):
    out = []
    for c in state[u"calls"]:
        out.append([c[u"row"], SEAT_TAG[c[u"seat"]], c[u"attempt"], bool(c[u"aborted"]), c[u"http_status"], c[u"retries"], c[u"stop_reason"], u",".join(x or u"?" for x in (c[u"blocks"] or [])),
                    c[u"tin"], c[u"tout"], c[u"usage_usd"], c[u"est_counted_usd"], c[u"chars"], c[u"answer"] is not None])
    return out


# ======================================================================================================
# 数えるもの(封 §2-5)。記録の行・呼び出しの欄だけから作る(--check が同じ関数で作り直す)
def views_of(rows):
    out = []
    for r in rows:
        if r[C_CLS] not in ("A", "W") or r[C_MLAB] not in LABELS or r[C_SLAB] not in LABELS or r[C_KIND] not in KIND_NAME.values():
            raise Stop(u"**記録の行の類・札・種類が決めの字でない。止める**")
        out.append(od([("cls", r[C_CLS]), ("n", r[C_NC]), ("kind", r[C_KIND]), ("m", r[C_MLAB]), ("s", r[C_SLAB]), ("same", bool(r[C_SAME])), ("head1", bool(r[C_HEAD1]))]))
    return out


def p1_pass(v):
    return v["m"] in (L_OK, L_BAD)


def p1_wrong(v):
    return v["m"] == L_BAD


def p2_pass(v):
    return v["same"]


def rule_cell(vs, passed, wrong):
    ps = [v for v in vs if passed(v)]
    st = [v for v in vs if not passed(v)]
    return od([(u"通した行", len(ps)), (u"誤って通した行", sum(1 for v in ps if wrong(v))), (u"止めた行", len(st)), (u"止めた行のうち主の席が正", sum(1 for v in st if v["m"] == L_OK))])


def label_cell(vs, field):
    c = collections.Counter(v[field] for v in vs)
    return od((k, c.get(k, 0)) for k in LABELS)


def cell(vs):
    u"""行の集まり → 席ごとの札・P1・P2・主の席が誤の行のうち P2 が止めた数(封 §2-5 の 1〜3)。"""
    return od([(u"行", len(vs)), (u"主の席の札", label_cell(vs, "m")), (u"副の席の札", label_cell(vs, "s")),
               (u"P1(主の席だけ)", rule_cell(vs, p1_pass, p1_wrong)), (u"P2(2 席の一致)", rule_cell(vs, p2_pass, p1_wrong)),
               (u"主の席が誤の行", sum(1 for v in vs if v["m"] == L_BAD)), (u"主の席が誤の行のうち P2 が止めた行", sum(1 for v in vs if v["m"] == L_BAD and not v["same"]))])


def tally(views):
    a = [v for v in views if v["cls"] == "A"]
    w = [v for v in views if v["cls"] == "W"]
    out = od()
    out[u"類 A"] = cell(a)
    out[u"類 W"] = cell(w)
    out[u"類 A を候補の数の帯で分けた"] = od((name, cell([v for v in a if fn(v["n"])])) for name, fn in BANDS.items())
    out[u"類 A を計算書の種類で分けた"] = od((name, cell([v for v in a if v["kind"] == name])) for name in KIND_NAME.values())
    return out


def lines_of(views):
    u"""封 §2-5 の 5(類 A)。何もしなかったら = でたらめに 1 つ選ぶ期待の正の数・昇順の頭の候補を選ぶ正の数。完璧に動いたら = P2 が全部通して誤 0・類 W を全部止める。"""
    a = [v for v in views if v["cls"] == "A"]
    w = [v for v in views if v["cls"] == "W"]
    return od([(u"何もしなかったら: でたらめに 1 つ選んだときの正の数の期待(行ごとの 1 ÷ 候補の数の和)", round(sum(1.0 / v["n"] for v in a), 4)),
               (u"何もしなかったら: 昇順の頭の候補を選んだときの正の数", sum(1 for v in a if v["head1"])),
               (u"類 A の行", len(a)),
               (u"完璧に動いたら: P2 が通す類 A の行・誤って通す行・類 W で止める行", od([(u"類 A を通す", len(a)), (u"誤って通す", 0), (u"類 W を止める", len(w))])),
               (u"今: P2 が通した類 A の行・誤って通した行・類 W で止めた行", od([(u"類 A を通した", sum(1 for v in a if p2_pass(v))), (u"誤って通した", sum(1 for v in a if p2_pass(v) and v["m"] == L_BAD)),
                                                                      (u"類 W を止めた", sum(1 for v in w if not p2_pass(v)))]))])


def pairs_of(values):
    u"""API の返事の字(block の type・stop_reason・HTTP の状態)の種類 → [[字, 回数], ...](字の順)。字を dict の key にしない(``text`` などの禁止欄に当たるため)。"""
    return [[k, v] for k, v in sorted(collections.Counter(values).items())]


def call_tally(call_rows, n_rows):
    u"""呼び出しの欄 → 席ごとの数(封 §2-5 の 6)。"""
    out = od()
    total_usd = 0.0
    for seat, tag in SEAT_TAG.items():
        cs = [c for c in call_rows if c[K_SEAT] == tag]
        real = [c for c in cs if not c[K_ABORT]]
        none_rows = n_rows - len(set(c[K_ROW] for c in real if c[K_OK]))
        usd_u = round(sum(c[K_USD_U] for c in cs), 6)
        usd_e = round(sum(c[K_USD_E] for c in cs), 6)
        total_usd += usd_u + usd_e
        out[tag] = od([(u"model", seat), (u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)", len(real)), (u"うち 1 回目", sum(1 for c in real if c[K_ATT] == 1)),
                       (u"答えのやり直し(封 §2-3)", sum(1 for c in real if c[K_ATT] == 2)), (u"HTTP の再試行(429・5xx)の合計", sum(c[K_RETRY] for c in real)),
                       (u"中断した(次の走りで見つけた・上限で止めた)呼び出し", sum(1 for c in cs if c[K_ABORT])),
                       (u"答えなしの行", none_rows), (u"入力 token の合計", sum(c[K_TIN] or 0 for c in cs)), (u"出力 token の合計", sum(c[K_TOUT] or 0 for c in cs)),
                       (u"USD(返った usage で。§3 の単価)", usd_u), (u"USD(返らなかった呼び出しの見積りで数えた分)", usd_e), (u"USD 合計", round(usd_u + usd_e, 6)),
                       (u"返った block の type の並びの種類", pairs_of(c[K_BLOCKS] for c in real if c[K_BLOCKS] is not None)),
                       (u"stop_reason の種類", pairs_of(str(c[K_STOP]) for c in real)),
                       (u"HTTP の状態の種類", pairs_of(str(c[K_HTTP]) for c in real))])
    out[u"USD の全部"] = round(total_usd, 6)
    return out


def point_diff(n1, d1, n2, d2):
    u"""(n1/d1 − n2/d2)× 100 を小数 2 桁の字で。分母 0 があれば「分母 0」。"""
    if not d1 or not d2:
        return u"分母 0"
    return u"%.2f" % (100.0 * n1 / d1 - 100.0 * n2 / d2)


def usd_of(trial_call_rows, call_rows):
    return round(sum(c[K_USD_U] + c[K_USD_E] for c in list(trial_call_rows) + list(call_rows)), 6)


def predictions(views, usd_all):
    u"""封 §5 の XD0-1〜XD0-11 の判定に要る数(整数と率。当たり・外れは書かない。結果の文書で)。"""
    a = [v for v in views if v["cls"] == "A"]
    w = [v for v in views if v["cls"] == "W"]
    p2a = [v for v in a if p2_pass(v)]
    p2w = [v for v in w if p2_pass(v)]
    m_bad = [v for v in a if v["m"] == L_BAD]
    big = [v for v in a if v["n"] >= 7]
    nok = [v for v in a if v["kind"] == NO_KIND]
    wk = [v for v in a if v["kind"] in KINDS_WITH]
    ss = [v for v in a if v["kind"] not in KINDS_WITH and v["kind"] != NO_KIND]
    ok = lambda vs: sum(1 for v in vs if v["m"] == L_OK)                 # noqa: E731
    s_ok = lambda vs: sum(1 for v in vs if v["s"] == L_OK)               # noqa: E731
    out = od()
    out[u"XD0-1 類 A の主の席の正"] = od([(u"行", len(a)), (u"主の席の正", ok(a))])
    out[u"XD0-2 類 A で P2 が通した行"] = od([(u"行", len(a)), (u"P2 が通した行", len(p2a))])
    out[u"XD0-3 類 A で P2 が誤って通した行 / P2 が通した行"] = od([(u"P2 が通した行", len(p2a)), (u"誤って通した行", sum(1 for v in p2a if v["m"] == L_BAD)),
                                                       (u"誤って通した行 / 通した行", rate(sum(1 for v in p2a if v["m"] == L_BAD), len(p2a)))])
    out[u"XD0-4 類 A で主の席が誤の行のうち P2 が止めた行"] = od([(u"主の席が誤の行", len(m_bad)), (u"P2 が止めた行", sum(1 for v in m_bad if not p2_pass(v)))])
    out[u"XD0-5 類 W の主の席の 0"] = od([(u"行", len(w)), (u"主の席の 0", sum(1 for v in w if v["m"] == L_ZERO))])
    out[u"XD0-6 類 W で P2 が誤って通した行"] = od([(u"行", len(w)), (u"P2 が通した行(類 W は全部誤)", len(p2w))])
    out[u"XD0-7 類 A の候補が 7 以上の行の主の席の正"] = od([(u"行", len(big)), (u"主の席の正", ok(big)), (u"率", rate(ok(big), len(big)))])
    out[u"XD0-8 類 A の主の席の正の率(種類なし / 種類の在る行(貸借・損益・キャッシュフロー))"] = od([
        (u"種類なし", rate(ok(nok), len(nok))), (u"種類の在る行(貸借・損益・キャッシュフロー)", rate(ok(wk), len(wk))),
        (u"差(ポイント。種類なし − 種類の在る行)", point_diff(ok(nok), len(nok), ok(wk), len(wk))),
        (u"株主資本等変動の行(封の字の外。別に並べる)", rate(ok(ss), len(ss)))])
    out[u"XD0-9 類 A の副の席の正と主の席の正"] = od([(u"副の席の正", s_ok(a)), (u"主の席の正", ok(a)), (u"差(主 − 副)", ok(a) - s_ok(a))])
    out[u"XD0-10 主の席の答えなし(送った行の全部)"] = od([(u"行", len(views)), (u"主の席の答えなし", sum(1 for v in views if v["m"] == NO_ANSWER))])
    out[u"XD0-11 使った額 USD(試しを含む全部)"] = usd_all
    return out


def suspect_of(views):
    u"""封 §5「先に自分の欠陥を疑う条件」の数(類 A で主の席の正・席の 0・答えなし・P2 が通した行と誤)。条件に当たるかも字で並べる(数の判定。当たり・外れの判定ではない)。"""
    a = [v for v in views if v["cls"] == "A"]
    ok = sum(1 for v in a if v["m"] == L_OK)
    zero = sum(1 for v in a if v["m"] == L_ZERO)
    none = sum(1 for v in views if v["m"] == NO_ANSWER)
    p2 = [v for v in a if p2_pass(v)]
    p2_bad = sum(1 for v in p2 if v["m"] == L_BAD)
    return od([(u"類 A の主の席の正", ok), (u"類 A の主の席の 0", zero), (u"類 A の行", len(a)), (u"主の席の答えなし(送った行の全部)", none), (u"類 A で P2 が通した行", len(p2)), (u"うち誤", p2_bad),
               (u"条件に当たる(正が 130 行以下)", ok <= 130), (u"条件に当たる(0 が類 A の半分を超える)", 2 * zero > len(a)), (u"条件に当たる(答えなしが 40 行以上)", none >= 40),
               (u"条件に当たる(P2 が通した行が 300 行以上で誤 0)", len(p2) >= 300 and p2_bad == 0)])


def derived_sections(rows, call_rows, trial_call_rows, trial_n):
    u"""記録の行と呼び出しの欄から作る欄(§2-5 の 1〜6・予測の判定に要る数)。作る側(本番)と照らす側(--check)が同じ関数を使う。"""
    views = views_of(rows)
    usd_all = usd_of(trial_call_rows, call_rows)
    return od([(K_TALLY, tally(views)), (K_LINES, lines_of(views)), (K_CALLS, call_tally(call_rows, len(rows))), (K_TRIAL, od([(u"呼び出し", call_tally(trial_call_rows, trial_n))])),
               (K_PRED, predictions(views, usd_all)), (K_SUSPECT, suspect_of(views))])


# ======================================================================================================
# 記録
def check_text(rec, text, secret=None, key_value=None):
    u"""記録に書かないもの(欄・docID・EDINET コード・行の字・見出しの字・要素の名・業種の値・鍵らしい字)が無いか。在れば止める。"""
    scan = text
    for rel in (SEAL_REL, SCRIPT_REL, RECORD_REL, XG1_SCRIPT_REL):
        scan = scan.replace(rel, u"")
    N.check_clean(rec, scan, secret)
    if GEN.key_leaks(scan, key_value, False):
        raise Stop(u"**記録に鍵らしい字が在る。止める**")


def record_text(rec, secret=None, key_value=None):
    text = dumps(rec)
    check_text(rec, text, secret, key_value)
    return text


def build_record(col, t_state, p_state, fp, procs_note=None):
    u"""全部の(行, 席)が済んだ途中の答え(試し・本番)→ 記録(OrderedDict)。書かない。"""
    items, t_items = col["prod"], col["trial"]
    rows = build_rows(items, p_state)
    call_rows = build_call_rows(p_state)
    trial_rows = build_rows(t_items, t_state)
    trial_calls = build_call_rows(t_state)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XD0(候補が残る行の要素を LLM の席に選ばせ、2 席の一致で通す測定)(有料・engine は 0 行)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"便 XG1 の script の sha256"] = XG1_SCRIPT_SHA256
    rec[u"engine の指紋"] = fp
    rec[u"材料"] = col["material"]
    rec[u"席"] = od([(u"主の席", od([(u"model", SEATS[0]), (u"thinking", THINKING[SEATS[0]]), (u"候補の並び", u"昇順")])),
                    (u"副の席", od([(u"model", SEATS[1]), (u"thinking", THINKING[SEATS[1]]), (u"候補の並び", u"降順")]))])
    rec[u"呼び出しの形"] = od([(u"max_tokens", MAX_TOKENS), (u"temperature", u"送らない"), (u"API の版", GEN.API_VERSION), (u"送り先", GEN.API_URL),
                          (u"HTTP の再試行", u"429 / 5xx のときだけ最大 %d 回(待ち %s 秒)" % (len(GEN.RETRY_WAITS), list(GEN.RETRY_WAITS))),
                          (u"答えのやり直し", u"読めない答えは同じ指示文でもう 1 回だけ(封 §2-3)"), (u"system", u"無し(user の 1 message)")])
    rec[u"指示文の型(封 §2-2)"] = od([(u"字", PROMPT_TEMPLATE), (u"sha256", sha256_text(PROMPT_TEMPLATE)), (u"置き換える所", list(PLACEHOLDERS))])
    rec[u"回数"] = od([(u"行(本番)", len(items)), (u"席", len(SEATS)), (u"呼び出しの予定(本番)", len(items) * len(SEATS)), (u"試しの行", len(t_items)), (u"試しの呼び出し", len(t_items) * len(SEATS)),
                     (u"やり直しを入れた本番の最大", len(items) * len(SEATS) * MAX_ANSWER_ATTEMPTS)])
    rec[u"費用"] = od([(u"上限 USD", COST_CAP_USD), (u"単価 入力 USD / M tokens", PRICE_IN), (u"単価 出力 USD / M tokens", PRICE_OUT),
                     (u"見積りの規則", u"入力の字数 × 1.0 を token とみなし、出力は max_tokens の全部(保守的な単価を両席に当てる。やり直しは見積りに入れない)"),
                     (u"使った額 USD(試しを含む)", round(state_cost(t_state) + state_cost(p_state), 6))])
    rec[K_WIRE] = col["wire"]
    rec[u"行の欄"] = list(ROW_COLUMNS)
    rec[u"行"] = rows
    rec[u"呼び出しの欄"] = list(CALL_COLUMNS)
    rec[u"呼び出し"] = call_rows
    rec[u"試しの行"] = trial_rows
    rec[u"試しの呼び出し"] = trial_calls
    for k, v in derived_sections(rows, call_rows, trial_calls, len(t_items)).items():
        rec[k] = v
    rec[u"限界"] = list(LIMITS)
    rec[u"key_leaks"] = []
    return rec


def write_record(path, rec, secret=None, key_value=None):
    u"""書く前と書いた後に検査を当てる。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(path))
    text = record_text(rec, secret, key_value)
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "xb") as fh:
        fh.write(text.encode("utf-8"))
    with io.open(path, encoding="utf-8") as fh:
        back = fh.read()
    try:
        check_text(rec, back, secret, key_value)
    except SystemExit:
        os.remove(path)
        raise


# ======================================================================================================
# 入口
def inside_repo(path):
    u"""path が git の木の中なら真(送った文を repo に置かせない)。repo の外から上へ辿って ``.git`` が在る場所も中とみなす。"""
    real = os.path.realpath(path)
    top = os.path.realpath(os.path.dirname(ROOT))
    if real == top or real.startswith(top + os.sep):
        return True
    d = real
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return True
        nd = os.path.dirname(d)
        if nd == d:
            return False
        d = nd


def trial_report(items, state, say):
    u"""試しの形(HTTP の状態・stop_reason・返った block の type・text の字数・答えが読めたか)。答えの中身・文は出さない。"""
    for c in state[u"calls"]:
        if c[u"aborted"]:
            continue
        say(u"  試し 行 %d %s: http=%s stop_reason=%s block=%s 字数=%s 答えが読めた=%s" % (
            c[u"row"], SEAT_TAG[c[u"seat"]], c[u"http_status"], c[u"stop_reason"], u",".join(x or u"?" for x in (c[u"blocks"] or [])), c[u"chars"], c[u"answer"] is not None))


def work_dirs(work=None):
    base = os.path.abspath(work or CACHE_DIR)
    return os.path.join(base, "trial"), os.path.join(base, "prod")


def run(root=ROOT, trial=False, resume=False, work=None, out=None, key=None, key_value=None, transport=call_api, sleep=None, collected=None, fp=None, say=print, cap=COST_CAP_USD):
    u"""試し(``trial``)か本番。鍵は ``key``(試験用。無ければ環境変数)。本番は全部済んだときにだけ記録を書く。"""
    t_dir, p_dir = work_dirs(work)
    out = out or os.path.join(root, RECORD_REL)
    if not trial and os.path.exists(out):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(out))
    if inside_repo(t_dir) or inside_repo(p_dir):
        raise Stop(u"**送った文と返った text の置き場が repo の中。追跡しない場所に置く。止める**")
    t_exists, p_exists = os.path.exists(state_path(t_dir)), os.path.exists(state_path(p_dir))
    if trial:
        if p_exists:
            raise Stop(u"**本番の途中の答えが既に在る。試しは本番の前に 1 度だけ。止める**")
        if t_exists:
            prev = load_state(t_dir)
            if any(c[u"answer"] is not None or c[u"http_status"] == 200 for c in prev[u"calls"]):
                raise Stop(u"**試しの途中の答えが既に在る(試しは答えが 1 つも返っていない置き場でだけ)。止める**")
    col = collected if collected is not None else collect_all(root=root, say=say)
    t_items, p_items = col["trial"], col["prod"]
    t_state = load_state(t_dir) if t_exists else new_state()
    p_state = load_state(p_dir) if p_exists else new_state()
    if not trial:
        if not t_exists or not trial_done(t_items, t_state):
            raise Stop(u"**試しの 10 回が済んでいない。先に --trial を走らせる。止める**")
        if p_exists and not resume:
            raise Stop(u"**本番の途中の答えが既に在る。続きは --resume を付ける(有料の呼び出しを二度しない)。止める**")
    key = key if key is not None else get_key()
    if trial:
        other_est, other_n = pending_estimate(p_items, p_state)
        n = run_calls(t_items, t_state, t_dir, key, transport=transport, sleep=sleep, say=say, one_attempt=True, cap=cap, other_cost=state_cost(p_state), other_est=other_est, other_n=other_n)
        say(u"新しく呼んだ %d・累計 %.4f USD" % (n, state_cost(t_state) + state_cost(p_state)))
        trial_report(t_items, t_state, say)
        return t_state
    check_state(t_items, t_state, t_dir)
    resolve_in_flight(t_state)
    n = run_calls(p_items, p_state, p_dir, key, transport=transport, sleep=sleep, say=say, cap=cap, other_cost=state_cost(t_state), other_est=0.0, other_n=0)
    say(u"新しく呼んだ %d・累計 %.4f USD(試しを含む)" % (n, state_cost(t_state) + state_cost(p_state)))
    if not all_done(p_items, p_state):
        raise Stop(u"**まだ済んでいない(行, 席)が在る。止める**")
    rec = build_record(col, t_state, p_state, fp if fp is not None else od((k, v) for k, v in N.VD.engine_fingerprint().items() if k in ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files")))
    write_record(out, rec, col["secret"], key_value if key_value is not None else key)
    say(u"-> %s" % os.path.basename(out))
    return rec


def fake_body(text, tin=100, tout=20, stop="end_turn", blocks=("thinking", "text")):
    u"""実物の API の返事の形(content の block・usage・stop_reason)の作り物。"""
    content = [({"type": "thinking", "thinking": u"…"} if b == "thinking" else {"type": "text", "text": text}) for b in blocks]
    return json.dumps({"content": content, "usage": {"input_tokens": tin, "output_tokens": tout}, "stop_reason": stop}).encode("utf-8")


def fake_item(doc, cls, elems, E, kind=None, heading=u"損益計算書", prev=(u"甲", u"乙"), T=u"その他"):
    return make_item(od([("doc", doc), ("cls", cls), ("kind", kind), ("heading", heading), ("prev", list(prev)), ("T", T), ("E", E), ("cands", sorted(elems))]), "prod")


def self_test(say):
    u"""作り物の行と作り物の transport(実物の返事の形)で、答えの読み方・番号 → 要素の名の戻し(副の席は降順)・答えのやり直し・429 の再試行・上限での停止を本番と同じ道(``run_calls``)で通す。通信しない。違えば止める。"""
    names = [u"AAa", u"BBb", u"CCc"]
    items = [fake_item(1, "A", names, u"BBb"), fake_item(1, "W", names, u"ZZz")]

    def seat_number(prompt, target):
        for ln in prompt.split(u"\n"):
            m = re.match(r"^(\d+)\. (.+)$", ln)
            if m and m.group(2) == target:
                return int(m.group(1))
        return 0
    calls = []

    def transport(prompt, model, key):
        calls.append(model)
        if len(calls) == 3:
            return 200, fake_body(u"読めません")
        if len(calls) == 5:
            return 429, b""
        return 200, fake_body(u"答え: %d" % seat_number(prompt, u"CCc"))
    tmp = tempfile.mkdtemp(prefix="ai_tag_pick_dry_")
    results = od()
    try:
        w = os.path.join(tmp, "a")
        st = new_state()
        run_calls(items, st, w, u"fake", transport=transport, sleep=lambda s: None, say=lambda *a: None)
        picks = [pick_of(items[i], s, seat_answer(st, i, s)) for i in range(2) for s in SEATS]
        results[u"番号 → 要素の名(主は昇順・副は降順で番号が違っても同じ要素に戻る)"] = picks == [u"CCc"] * 4 and items[0]["cands"][SEATS[0]] != items[0]["cands"][SEATS[1]]
        results[u"答えのやり直し(読めない 1 回目の後にもう 1 回)"] = len(seat_attempts(st, 1, SEATS[0])) == 2 and len(seat_attempts(st, 0, SEATS[0])) == 1
        results[u"429 の再試行(待ちは作り物)"] = any(c[u"retries"] == 1 for c in st[u"calls"])
        results[u"札(正・誤・0・答えなし)"] = [seat_label(items[0], SEATS[0], 2), seat_label(items[0], SEATS[0], 3), seat_label(items[0], SEATS[0], 0), seat_label(items[0], SEATS[0], None)] == [L_OK, L_BAD, L_ZERO, NO_ANSWER]
        w2 = os.path.join(tmp, "b")
        st2 = new_state()
        n_before = len(calls)
        try:
            run_calls(items, st2, w2, u"fake", transport=transport, sleep=lambda s: None, say=lambda *a: None, cap=0.0001)
            results[u"上限で止まる"] = False
        except Stop:
            results[u"上限で止まる"] = len(calls) == n_before
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for k, v in results.items():
        say(u"  作り物の transport: %s ― %s" % (k, u"OK" if v else u"違う"))
    if not all(results.values()):
        raise Stop(u"**作り物の transport の検査に違いがある。止める**")
    return results


def dry_run(root=ROOT, say=print, collected=None):
    u"""0 USD。鍵を読まない・通信しない・記録を書かない。本番と同じ関数で全部の指示文を組み、数と配線の確認を出す。作り物の transport で答えの読み方・番号の戻し・やり直し・上限を通す。"""
    col = collected if collected is not None else collect_all(root=root, say=say)
    t_items, p_items, wire = col["trial"], col["prod"], col["wire"]
    allit = t_items + p_items
    chars = sum(len(it["prompt"][s]) for it in allit for s in SEATS)
    est_one = sum(estimate_usd(len(it["prompt"][s])) for it in allit for s in SEATS)
    est_max = est_one * MAX_ANSWER_ATTEMPTS
    cls = collections.Counter(it["cls"] for it in p_items)
    lens = [len(it["prompt"][s]) for it in allit for s in SEATS]
    say(u"行の数(本番): %d(封の行の数 %d)= 類 A %d(封 %d)+ 類 W %d(封 %d)・試しの行 %d(封 %d)" % (len(p_items), EXPECT_ROWS, cls["A"], EXPECT_A, cls["W"], EXPECT_W, len(t_items), TRIAL_ROWS))
    say(u"段 3 の類の数(配線の確認): 開発 %s・本番 %s" % (u"・".join(u"%s %d" % kv for kv in wire[u"段 3 の類の数(開発)"].items()), u"・".join(u"%s %d" % kv for kv in wire[u"段 3 の類の数(本番)"].items())))
    say(u"席ごとの本数: %s(本番 %d 回・試し %d 回)" % (u"・".join(u"%s(%s)" % (SEAT_TAG[s], s) for s in SEATS), len(p_items) * len(SEATS), len(t_items) * len(SEATS)))
    say(u"指示文: 全部で %d 本(本番 %d + 試し %d)・字数の合計 %d(1 本あたり最小 %d・最大 %d・平均 %.1f)" % (
        len(allit) * len(SEATS), len(p_items) * len(SEATS), len(t_items) * len(SEATS), chars, min(lens), max(lens), chars / float(len(lens))))
    say(u"見積り(保守的な単価 入力 %.1f / 出力 %.1f USD / M tokens・入力 = 字数 × 1.0・出力 = max_tokens %d): 試し + 本番 %d 回で %.4f USD(やり直しは入れない)・やり直しを全部入れた最大 %.4f USD(上限 %.2f)" % (
        PRICE_IN, PRICE_OUT, MAX_TOKENS, len(allit) * len(SEATS), est_one, est_max, COST_CAP_USD))
    say(u"走らせる前の見積り(封 §3 の決め: 試し + 本番・やり直しなし)が上限を超えるか: %s" % (u"超える(本番は 1 回も呼ばずに止まる)" if est_one > COST_CAP_USD else u"超えない"))
    say(u"配線の確認(数だけ): 類 W のうち候補が 1 つの行 %d・見出しが無い行 %d・見出しが空の字の行 %d・見出しに改行を含む行 %d・前の行が無い行 %d" % (
        wire[u"類 W のうち候補が 1 つの行"], wire[u"見出しが無い行(%s)" % NO_HEADING], wire[u"見出しが空の字の行(【】)"], wire[u"見出しに改行を含む行"], wire[u"前の行が無い行(%s)" % NO_PREV]))
    checks = self_test(say)
    say(u"--dry-run: 通信していない・鍵は読んでいない・記録は書いていない。")
    return od([(u"items", allit), (u"wire", wire), (u"chars", chars), (u"est_usd", est_one), (u"est_max_usd", est_max), (u"self_test", checks)])


def check(root=ROOT, say=print, rec=None, collected=None, work=None, fp=None):
    u"""0 USD。記録の行・呼び出しの欄から数を作り直して記録と照らし、材料と置き場の途中の答えから行・呼び出しの欄を組み直して照らす。鍵も通信も無い。"""
    if rec is None:
        p = os.path.join(root, RECORD_REL)
        if not os.path.isfile(p):
            raise Stop(u"**在る記録が無い。止める**")
        with io.open(p, encoding="utf-8") as fh:
            rec = json.load(fh, object_pairs_hook=collections.OrderedDict)
    if rec[u"行の欄"] != ROW_COLUMNS or rec[u"呼び出しの欄"] != CALL_COLUMNS:
        raise Stop(u"**記録の行の欄か呼び出しの欄が決めと違う。止める**")
    rows, call_rows, trial_calls = rec[u"行"], rec[u"呼び出し"], rec[u"試しの呼び出し"]
    now = derived_sections(rows, call_rows, trial_calls, len(rec[u"試しの行"]))
    for k, v in now.items():
        if dumps(rec[k]) != dumps(v):
            raise Stop(u"**記録の欄が行・呼び出しの欄から作り直した数と違う: %s。止める**" % k)
    for i, r in enumerate(rows):                              # 行と呼び出しの欄の対応(席ごとの呼び出しの数・答えが読めたか)
        for tag, cc in ((u"主", C_MCALL), (u"副", C_SCALL)):
            cs = [c for c in call_rows if c[K_ROW] == i and c[K_SEAT] == tag and not c[K_ABORT]]
            if len(cs) != r[cc] or any(c[K_ATT] != n + 1 for n, c in enumerate(cs)):
                raise Stop(u"**行の呼び出しの数が呼び出しの欄と合わない(行 %d)。止める**" % i)
            lab = r[C_MLAB] if tag == u"主" else r[C_SLAB]
            if (lab == NO_ANSWER) != (not any(c[K_OK] for c in cs)):
                raise Stop(u"**行の札と呼び出しの欄の「答えが読めた」が合わない(行 %d)。止める**" % i)
    for c in list(call_rows) + list(trial_calls):
        if c[K_TIN] is not None and c[K_USD_U] != round(cost_usd(c[K_TIN], c[K_TOUT]), 6):
            raise Stop(u"**呼び出しの欄の USD が token と §3 の単価から作り直した額と違う。止める**")
    col = collected if collected is not None else collect_all(root=root, say=say)
    t_dir, p_dir = work_dirs(work)
    t_state, p_state = load_state(t_dir), load_state(p_dir)
    if t_state is None or p_state is None:
        raise Stop(u"**置き場の途中の答え(試し・本番)が無い。止める**")
    check_state(col["trial"], t_state, t_dir)
    check_state(col["prod"], p_state, p_dir)
    if dumps(build_rows(col["prod"], p_state)) != dumps(rows) or dumps(build_rows(col["trial"], t_state)) != dumps(rec[u"試しの行"]):
        raise Stop(u"**材料と置き場の途中の答えから組み直した行が記録の行と違う(指示文の sha256・札・呼び出しの数)。止める**")
    if dumps(build_call_rows(p_state)) != dumps(call_rows) or dumps(build_call_rows(t_state)) != dumps(trial_calls):
        raise Stop(u"**置き場の途中の答えから組み直した呼び出しの欄が記録と違う。止める**")
    if rec[u"この script の sha256"] != sha256_file(os.path.abspath(__file__)) or dumps(rec[K_WIRE]) != dumps(col["wire"]) or rec[u"便 XG1 の script の sha256"] != XG1_SCRIPT_SHA256:
        raise Stop(u"**記録の script の sha256・配線の確認が今と違う。止める**")
    check_text(rec, dumps(rec), col["secret"])
    say(u"--check: 記録の数は行・呼び出しの欄から作り直した数と同じ・行と呼び出しは材料と置き場から組み直した %d 行と同じ" % len(col["prod"]))
    return now


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="0 USD。指示文を組み、数・見積り・配線の確認を出す。鍵は読まない・通信しない")
    ap.add_argument("--trial", action="store_true", help="有料。試しの 5 行 × 2 席に 1 回ずつ(10 回)。形だけ見る")
    ap.add_argument("--run", action="store_true", help="有料。本番(試しが済んでいること)。省くと --dry-run・--trial・--check のどれかが要る")
    ap.add_argument("--resume", action="store_true", help="本番の途中の答えの続きから")
    ap.add_argument("--check", action="store_true", help="0 USD。記録を作り直して照らす")
    ap.add_argument("--root", default=ROOT)
    a = ap.parse_args(argv)
    if sum(1 for x in (a.dry_run, a.trial, a.check, a.run) if x) != 1:
        raise Stop(u"**--dry-run・--trial・--run・--check のどれか 1 つだけを付ける。止める**")
    if a.dry_run:
        dry_run(root=a.root)
    elif a.check:
        check(root=a.root)
    else:
        run(root=a.root, trial=a.trial, resume=a.resume)


if __name__ == "__main__":
    main()
