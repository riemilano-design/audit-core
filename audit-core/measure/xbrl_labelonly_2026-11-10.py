# -*- coding: utf-8 -*-
u"""封 docs/XBRL_LABEL_ONLY_RATES_SEAL_2026-11-10.md §0-2・§1・§2・§4 ― 札のある行だけの率 LB(AI の文 200 本の数の claim で、GROUNDED の率と札ごとの率を「全部の行」と「札のある行だけ」で並べる)の測定と、結果の表(tally)。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない・新しい札付けはしない。** engine(``core/``・``adapters/``)・``measure/lib``・前の便の script・記録・門は 1 行も変えない。

    python3 measure/xbrl_labelonly_2026-11-10.py run   [--only <docID>] [--out PATH] [--procs N]   # 200 本 × P28E・P29E・P30E・P32E・P33E → fixtures/xbrl/labelonly/rates_2026-11-10.json(出力が既に在れば止まる)
    python3 measure/xbrl_labelonly_2026-11-10.py tally [--root DIR]                                 # 記録から封 §1 の表と §2 の L-0〜L-2 の照合を出す(file は書かない)

``--only`` を付けた走らせ方は本番の記録ではない: ``--out`` を必ず指定する(指定が無ければ止める)。時間は測らないので ``--procs`` で並行してよい。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- 材料は PB の便の ``RM.load_jobs``(200 本。順は N の便と同じ 160 本 → 40 本)を importlib で読む。前から在る ``sys.modules`` の名前は戻す(前の便の script が決まった名前で登録し直すため)。
- 数の claim = ``R.build_raw_claims`` が返す 2 つの列のうち num の列(raw 自身は ``kind`` の欄を持たない。``verify_document`` の ``claims`` と id の並びが同じで、num の列の位置の claim の ``kind`` が num・text の列の位置が text。違う本は ``対応`` が偽)。鍵は ``(文の番号, 文の中の位置)`` = (raw の ``sentence``, ``pos``)。
- 札は P28E の (本, claim の id)。P28E の行は自分の id で札を引く(札の記録に無ければ「なし」= L-0 の差に数える)。
  P29E 以降の行は、同じ鍵の P28E の数の claim が在れば「既存」でその P28E の行の札を持ち、無ければ「新」で札は「なし」(N の便の ``measure/xbrl_numfix_2026-11-04.py`` の docstring の定義の字のまま。関数としては切り出されていないのでここに書く)。
- 鍵が重複する本は ``対応`` を偽にして記録する(行は全部残す)。重複した鍵の P28E の札は最初の行のものを使う。
- L-0 は本ごとに ``P28E のみ`` = 今回の P28E の数の claim の id で札の記録に無いもの・``札のみ`` = 札の記録の id で今回の P28E の数の claim に無いもの、を数えて記録する(``L-0 の差``)。
- 率は百分率の小数 1 桁。整数だけで四捨五入(0.5 は切り上げ)して出す(float の丸めを使わない)。分母 0 は「なし」。
- 記録は 1 行 1 行を JSON の配列(``行の欄`` の順)で 1 行ずつに書く(全部で 7 万行を超えるため)。文・要素名・会社名・pointer の字・値は持たない。docID を含む本の名は ``LATER_NAMING_FILES`` に宣言された記録だけ。
"""
from __future__ import print_function

import argparse
import collections
import contextlib
import importlib.util
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    u"""importlib で読み込む。``sys.modules`` にも登録する(子 process が名前で引けるように)。読み込みの前に居た名前は、読み込みの後に元の object へ戻す
    (PB の script が中で読む前の便の script は決まった名前で登録し直して先に居た module を上書きするため。2026-11-06 の 7109c97 の直しと同じ)。読み込んだ module 自身の名前は残す。"""
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


PB = load_module("xbrl_pbind_2026-11-06.py", "pbind_for_labelonly")
RM, D = PB.RM, PB.D
NF, GEN, RUN = PB.NF, PB.GEN, PB.RUN
Stop = GEN.Stop

from adapters.xbrl import prose as PR                # noqa: E402
from adapters.xbrl import recipes as R               # noqa: E402
from adapters.xbrl import verify_document as VD      # noqa: E402
from adapters.xbrl import vocabulary as V            # noqa: E402

SEAL_REL = "docs/XBRL_LABEL_ONLY_RATES_SEAL_2026-11-10.md"
SEAL_COMMIT = "9ad2c7d0"
DOC_REL = "docs/XBRL_LABEL_ONLY_RATES_RESULT_2026-11-10.md"
SCRIPT_REL = "measure/xbrl_labelonly_2026-11-10.py"
REC_REL = "fixtures/xbrl/labelonly/rates_2026-11-10.json"
PROFILES = ("P28E", "P29E", "P30E", "P32E", "P33E")
BASE = "P28E"
G = "GROUNDED"
MATCH, DIFF = u"**一致**", u"**不一致**"
STATES = NF.STATES
EXISTING, NEWROW = u"既存", u"新"
L_TRUE, L_FALSE, L_UNKNOWN = u"真", u"偽", u"判定不能"
L_NONE = u"なし"
LABEL_WORDS = (L_TRUE, L_FALSE, L_UNKNOWN)
FORMS = ("F1", "F2", "F3", "F4", "F5")
#: 表の『範囲』(行の札の語でくくる)。(名前, 札の語の組)
GROUP_ALL, GROUP_LABELLED, GROUP_TRUE, GROUP_FALSE, GROUP_UNKNOWN, GROUP_NONE = u"全部の行", u"札のある行", u"札 真", u"札 偽", u"札 判定不能", u"札の無い行"
GROUPS = collections.OrderedDict([
    (GROUP_ALL, (L_TRUE, L_FALSE, L_UNKNOWN, L_NONE)), (GROUP_LABELLED, (L_TRUE, L_FALSE, L_UNKNOWN)), (GROUP_TRUE, (L_TRUE,)), (GROUP_FALSE, (L_FALSE,)),
    (GROUP_UNKNOWN, (L_UNKNOWN,)), (GROUP_NONE, (L_NONE,))])
FORM_GROUPS = (GROUP_LABELLED, GROUP_TRUE, GROUP_FALSE, GROUP_UNKNOWN)
ROW_FIELDS = (u"本の id", u"形", u"profile", u"文の番号", u"文の中の位置", u"state", u"札", u"既存か新か")
BOOK_KEYS = (u"本の id", u"形", u"model", u"材料", u"対応", u"数の claim の数", u"L-0 の差")
LIMITS = (
    u"札は盲検の LLM の席(1 本 1 席の 1 席目)の読みで、人の目でも正解でもない。席が誤りうる",
    u"札の無い行(P29E 以降に新しく claim になった行)の正しさは測らない。札のある行だけの率は、札の無い行の率の代わりにならない",
    u"材料は AI の文 200 本(Claude の model 2 つが書いた 5 つの形)の数の claim だけ。人が書いた文・他の書き手の文・文の claim は含まない",
    u"注入の率・97 書類の原文の率には札という考えが無く、この記録の外",
    u"有料の API・通信は使っていない。新しい札付けはしていない")


def key_leaks_lb(gen):
    u"""``gen.key_leaks`` の版: この便の封の path(32 字以上の英数字・_・- の連なり)を除いて元の検査に渡す。"""
    orig = gen.key_leaks

    def fn(text, key_value=None, long_alnum=True):
        return orig(text.replace(SEAL_REL, u""), key_value, long_alnum)
    return fn


@contextlib.contextmanager
def key_check_lb(gen):
    u"""``gen.key_leaks`` を with の中だけこの便の封の path を除く版にする。出るときは必ず戻す(NF の便の ``key_check_nf`` と同じ形)。"""
    old = gen.key_leaks
    gen.key_leaks = key_leaks_lb(gen)
    try:
        yield
    finally:
        gen.key_leaks = old


# ======================================================================================================
# 率(整数だけで四捨五入)
def rate_tenths(g, n):
    u"""g / n の百分率を 0.1 刻みに四捨五入した整数(0.5 は切り上げ)。n が 0 なら None。"""
    if not n:
        return None
    return (g * 2000 + n) // (2 * n)


def rate_str(g, n):
    t = rate_tenths(g, n)
    return u"なし" if t is None else u"%d.%d" % divmod(t, 10)


# ======================================================================================================
# 1 本
def num_view(zb, text, pname):
    u"""1 profile の数の claim の列 [(id, (文の番号, 位置), state)] と、対応が付いたか(id の並び・kind が verify_document と同じ・鍵が一意)。"""
    prof = V.PROFILES[pname]
    out = VD.verify_document(zb, pname, text)
    zm = PR.build_modified_zip(zb, text)[0]
    nums, texts = R.build_raw_claims(zm, prof)
    raws = nums + texts
    cl = out["claims"]
    n_num = len(nums)
    ok = len(cl) == len(raws) and all(c["id"] == r["id"] and c["kind"] == (u"num" if i < n_num else u"text") for i, (c, r) in enumerate(zip(cl, raws)))
    rows, seen = [], set()
    for c, r in zip(cl[:n_num], nums):
        key = (r["sentence"], r["pos"])
        if key in seen:
            ok = False
        seen.add(key)
        rows.append((c["id"], key, c["state"]))
    return rows, ok


def label_word(labels, cid):
    u"""札の記録 ``{id: 札の語}`` から語。無ければ「なし」。"""
    w = labels.get(cid)
    return w if w in LABEL_WORDS else L_NONE


def assemble_book(name, form, model, src, views, labels):
    u"""1 本の (本の欄, 行の列)。views = {profile: (num_view の rows, ok)}・labels = 札の記録の {id: 札の語}。
    P28E の行は自分の id で札を引く。他の profile の行は、同じ鍵の P28E の行が在れば「既存」でその札、無ければ「新」で札なし。"""
    base_rows, _ok = views[BASE]
    by_key = collections.OrderedDict()
    for cid, key, _state in base_rows:
        if key not in by_key:
            by_key[key] = label_word(labels, cid)
    run_ids = set(cid for cid, _k, _s in base_rows)
    rows = []
    for p in PROFILES:
        for cid, key, state in views[p][0]:
            if p == BASE:
                rows.append([name, form, p, key[0], key[1], state, label_word(labels, cid), EXISTING])
            elif key in by_key:
                rows.append([name, form, p, key[0], key[1], state, by_key[key], EXISTING])
            else:
                rows.append([name, form, p, key[0], key[1], state, L_NONE, NEWROW])
    book = collections.OrderedDict([
        (u"本の id", name), (u"形", form), (u"model", model), (u"材料", src),
        (u"対応", collections.OrderedDict((p, bool(views[p][1])) for p in PROFILES)),
        (u"数の claim の数", collections.OrderedDict((p, len(views[p][0])) for p in PROFILES)),
        (u"L-0 の差", collections.OrderedDict([(u"P28E のみ", len(run_ids - set(labels))), (u"札のみ", len(set(labels) - run_ids)), (u"札の記録の id の数", len(labels))]))])
    return book, rows


def judge_book_lb(job):
    u"""``RM.load_jobs`` の job 1 本 → (本の欄, 行の列)。5 profile を 1 回ずつ走らせる(plain data だけを返す)。"""
    src, name, item, row, text_dir, zip_caches, _prior, labels, _n_book = job
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    views = collections.OrderedDict((p, num_view(zb, text, p)) for p in PROFILES)
    return assemble_book(name, item[u"form"], item[u"model"], src, views, labels)


# ======================================================================================================
# run
def render_record(rec):
    u"""記録の JSON の字。``行`` だけ 1 行ずつの配列にする(他は indent 1)。"""
    rows = rec[u"行"]
    body = collections.OrderedDict((k, v) for k, v in rec.items() if k != u"行")
    body[u"行"] = u"@@ROWS@@"
    text = json.dumps(body, ensure_ascii=False, indent=1)
    lines = [json.dumps(r, ensure_ascii=False) for r in rows]
    rows_text = u"[\n" + u",\n".join(u"  " + x for x in lines) + u"\n ]" if lines else u"[]"
    return text.replace(u'"@@ROWS@@"', rows_text) + u"\n"


def run(root=ROOT, only=None, out=None, procs=1, say=print):
    production = out is None
    if production:
        if only is not None:
            raise Stop(u"**--only を付けた走らせ方は本番の記録を作らない。--out を指定する。止める**")
        out = os.path.join(root, REC_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    if not isinstance(procs, int) or procs < 1:
        raise Stop(u"**--procs は 1 以上の整数。止める**")
    jobs_ = RM.load_jobs(root, only)
    caches = RM.caches_all()
    before = GEN.caches_snapshot(caches)
    say(u"%d 本 × profile %d(%s)― procs %d" % (len(jobs_), len(PROFILES), u"・".join(PROFILES), procs))
    res = NF.map_pool(judge_book_lb, jobs_, procs)
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    books = [b for b, _r in res]
    rows = [x for _b, r in res for x in r]
    label_ids = sum(len(v) for per in RM.load_labels(root).values() for v in per.values())
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"札のある行だけの率 LB ― AI の文 200 本の数の claim(0 USD)"
    rec[u"HEAD の commit"] = GEN.git_head(os.path.dirname(root))
    rec[u"この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    rec[u"engine の指紋"] = VD.engine_fingerprint()
    rec[u"範囲"] = u"全部(AI の文 200 本)" if only is None else u"**--only の docID だけ(本番の記録ではない)**"
    rec[u"profile"] = list(PROFILES)
    rec[u"cache の前後"] = collections.OrderedDict([(u"前", before), (u"後", after), (u"変化なし", before == after)])
    rec[u"札の記録の sha256"] = collections.OrderedDict((k, GEN.sha256_file(os.path.join(root, rel))) for k, rel in RM.LABELS_REL.items())
    rec[u"札の記録の (本, id) の数"] = label_ids
    rec[u"欄"] = collections.OrderedDict([
        (u"行の欄", list(ROW_FIELDS)),
        (u"数の claim の鍵", u"(文の番号, 文の中の位置)。id は profile 間で替わるので使わない"),
        (u"札", u"盲検の LLM の席の読み(1 席目)。真 / 偽 / 判定不能 / なし。P28E の行は P28E の (本, id)、他の profile の行は同じ鍵の P28E の行の札"),
        (u"既存か新か", u"同じ鍵の P28E の数の claim が在れば既存、無ければ新(P28E の行は全部既存)"),
        (u"L-0 の差", u"P28E のみ = 今回の P28E の数の claim の id で札の記録に無いもの・札のみ = 札の記録の id で今回の P28E の数の claim に無いもの")])
    rec[u"本"] = books
    rec[u"行"] = rows
    rec[u"限界"] = list(LIMITS)
    rec[u"key_leaks"] = D.record_key_leaks(rec)
    if rec[u"key_leaks"]:
        raise Stop(u"記録に鍵が入った")
    with key_check_lb(GEN):
        RUN.write_record(out, render_record(rec), rec, None)
    say(u"-> %s(本 %d・行 %d)" % (out, len(books), len(rows)))
    return rec


# ======================================================================================================
# tally: 封の字から照合の数を読み、記録から表と L-0〜L-2 を作る
def read_seal(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def seal_pred_rows(seal):
    u"""封 §2 の表の行 {L-n: (欄, 照合 / 予測, 外れ方)}。"""
    sec = seal[seal.index("## §2"):seal.index("## §3")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| (L-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            out[m.group(1)] = (cells[0], cells[1], cells[2] if len(cells) > 2 else u"")
    return out


def _i(s):
    return int(s.replace(",", ""))


def seal_expect(seal):
    u"""封 §2 の L-0〜L-2 の字から照合の数を読む(字のコピーにしない)。形が違えば例外 = 赤。
    {"L-0": 数の claim の行数, "L-1": {profile: (数の claim の行数, 札のある行数)}, "L-2": {profile: (全部の行の GROUNDED, 札のある行の GROUNDED)}}。P28E の L-2 は札のある行だけ(全部の行は L-1 の行数と同じで、封は P28E の全部の行の GROUNDED を書いていない = None)。"""
    P = seal_pred_rows(seal)
    out = collections.OrderedDict()
    m = re.match(r"^同じ\(差 0\)。数の claim の行数 ([\d,]+)$", P["L-0"][1].strip())
    out["L-0"] = _i(m.group(1))
    m = re.match(r"^P28E ([\d,]+) / ([\d,]+)、P29E〜P33E ([\d,]+) / ([\d,]+)\(", P["L-1"][1].strip())
    l1 = collections.OrderedDict([("P28E", (_i(m.group(1)), _i(m.group(2))))])
    for p in PROFILES[1:]:
        l1[p] = (_i(m.group(3)), _i(m.group(4)))
    out["L-1"] = l1
    t = P["L-2"][1].strip()
    l2 = collections.OrderedDict()
    for p in PROFILES[1:]:
        m = re.search(r"%s ([\d,]+) / ([\d,]+)" % p, t)
        l2[p] = (_i(m.group(1)), _i(m.group(2)))
    m = re.search(r"P28E の札のある行 ([\d,]+)", t)
    l2["P28E"] = (None, _i(m.group(1)))
    out["L-2"] = collections.OrderedDict((p, l2[p]) for p in PROFILES)
    return out


def row_group_counts(rows):
    u"""{(profile, 範囲): [行数, GROUNDED]}。範囲は ``GROUPS`` の 6 つ。"""
    c = collections.OrderedDict(((p, g), [0, 0]) for p in PROFILES for g in GROUPS)
    for r in rows:
        p, st, lab = r[2], r[5], r[6]
        for g, words in GROUPS.items():
            if lab in words:
                c[(p, g)][0] += 1
                if st == G:
                    c[(p, g)][1] += 1
    return c


def form_group_counts(rows):
    u"""{(形, profile, 範囲): [行数, GROUNDED]}。範囲は ``FORM_GROUPS`` の 4 つ。"""
    c = collections.OrderedDict(((f, p, g), [0, 0]) for f in FORMS for p in PROFILES for g in FORM_GROUPS)
    for r in rows:
        f, p, st, lab = r[1], r[2], r[5], r[6]
        for g in FORM_GROUPS:
            if lab in GROUPS[g] and (f, p, g) in c:
                c[(f, p, g)][0] += 1
                if st == G:
                    c[(f, p, g)][1] += 1
    return c


def build_L(rec, seal):
    u"""L-0〜L-2 の照合。{L-n: {判定, 値, 期待}}。判定は 一致 / 不一致。"""
    E = seal_expect(seal)
    books, rows = rec[u"本"], rec[u"行"]
    gc = row_group_counts(rows)
    only_run = sum(b[u"L-0 の差"][u"P28E のみ"] for b in books)
    only_lab = sum(b[u"L-0 の差"][u"札のみ"] for b in books)
    n28 = gc[(BASE, GROUP_ALL)][0]
    out = collections.OrderedDict()
    v0 = collections.OrderedDict([(u"P28E のみ", only_run), (u"札のみ", only_lab), (u"数の claim の行数", n28), (u"札の記録の (本, id) の数", rec[u"札の記録の (本, id) の数"])])
    ok0 = only_run == 0 and only_lab == 0 and n28 == E["L-0"] and rec[u"札の記録の (本, id) の数"] == n28
    out["L-0"] = collections.OrderedDict([(u"判定", MATCH if ok0 else DIFF), (u"値", v0), (u"期待", E["L-0"])])
    v1 = collections.OrderedDict((p, (gc[(p, GROUP_ALL)][0], gc[(p, GROUP_LABELLED)][0])) for p in PROFILES)
    out["L-1"] = collections.OrderedDict([(u"判定", MATCH if all(tuple(v1[p]) == tuple(E["L-1"][p]) for p in PROFILES) else DIFF), (u"値", v1), (u"期待", E["L-1"])])
    v2 = collections.OrderedDict((p, (gc[(p, GROUP_ALL)][1], gc[(p, GROUP_LABELLED)][1])) for p in PROFILES)
    ok2 = all((E["L-2"][p][0] is None or v2[p][0] == E["L-2"][p][0]) and v2[p][1] == E["L-2"][p][1] for p in PROFILES)
    out["L-2"] = collections.OrderedDict([(u"判定", MATCH if ok2 else DIFF), (u"値", v2), (u"期待", E["L-2"])])
    return out


def _n(x):
    return u"{:,}".format(x)


def fmt_L(k, v):
    u"""表の『測った値』の字。"""
    val = v[u"値"]
    if k == "L-0":
        return u"P28E のみ %s・札のみ %s・数の claim の行数 %s・札の記録の (本, id) %s" % (_n(val[u"P28E のみ"]), _n(val[u"札のみ"]), _n(val[u"数の claim の行数"]), _n(val[u"札の記録の (本, id) の数"]))
    if k == "L-1":
        return u"、".join(u"%s %s / %s" % (p, _n(a), _n(b)) for p, (a, b) in val.items())
    return u"・".join(u"%s %s / %s" % (p, _n(a), _n(b)) for p, (a, b) in val.items())


def render_pred(J, seal=None):
    seal = seal if seal is not None else read_seal()
    P = seal_pred_rows(seal)
    lines = [u"| # | 欄 | 照合 | 測った値 | 判定 |", u"|---|---|---|---|---|"]
    for k, v in J.items():
        lines.append(u"| %s | %s | %s | %s | %s |" % (k, P[k][0], P[k][1], fmt_L(k, v), v[u"判定"]))
    return u"\n".join(lines)


def render_rates(rows):
    lines = [u"| profile | 範囲 | 行数 | GROUNDED | 率(%) |", u"|---|---|---|---|---|"]
    for (p, g), (n, gr) in row_group_counts(rows).items():
        lines.append(u"| %s | %s | %s | %s | %s |" % (p, g, _n(n), _n(gr), rate_str(gr, n)))
    return u"\n".join(lines)


def render_forms(rows):
    lines = [u"| 形 | profile | 範囲 | 行数 | GROUNDED | 率(%) |", u"|---|---|---|---|---|---|"]
    for (f, p, g), (n, gr) in form_group_counts(rows).items():
        lines.append(u"| %s | %s | %s | %s | %s | %s |" % (f, p, g, _n(n), _n(gr), rate_str(gr, n)))
    return u"\n".join(lines)


def load_record(root=ROOT):
    return GEN.jload(os.path.join(root, REC_REL))


def run_tally(root=ROOT, say=print, rec=None):
    seal = read_seal(root)
    rec = rec if rec is not None else load_record(root)
    J = build_L(rec, seal)
    say(render_pred(J, seal))
    say(u"")
    say(render_rates(rec[u"行"]))
    say(u"")
    say(render_forms(rec[u"行"]))
    return J


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("run", "tally"))
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", default=None, help="この docID の本だけ(--out が要る)")
    ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args(argv)
    if a.cmd == "run":
        run(root=a.root, only=a.only, out=a.out, procs=a.procs)
    else:
        run_tally(root=a.root)


if __name__ == "__main__":
    main()
