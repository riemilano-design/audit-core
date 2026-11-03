# -*- coding: utf-8 -*-
u"""封 docs/XBRL_AI_FORMS_SEAL_2026-11-03.md §0-2 の 6・§1・§4 ― 生成した 160 本の判定・注入・札付けの束。**0 USD・通信なし・鍵は読まない・LLM は呼ばない。**

    python3 measure/xbrl_aiforms_run_2026-11-03.py judge  [--procs N] [--only <docID>]   # 4 profile の判定 → claims_2026-11-03.json・札付けの束(repo の外)
    python3 measure/xbrl_aiforms_run_2026-11-03.py inject [--procs N] [--only <docID>]   # 注入(T1_VALUE・T8_REL。型ごと 1 本あたり 10)→ inject_2026-11-03.json

入力は生成の記録 ``fixtures/xbrl/aiforms/gen_2026-11-03.json``(本ごとの sha256)と、文 ``~/.cache/audit-core/aiforms-2026-11-03/texts/``(sha256 が記録と合わなければ止める)。
profile は P27・P27E・P28・P28E。各本を ``verify_document(zip, profile, text)`` で判定する(= MD&A の textBlock を text で差し替える入口そのもの)。
claim の欄(span・文・数の字・value は記録に入れない)は raw claim(``recipes.build_raw_claims`` を同じ差し替え済みの ZIP に当てたもの)から読む。
engine(``core/``・``adapters/``)は 1 行も変えない。前例 ``measure/xbrl_p27_tune_2026-10-27.py`` の関数(find_base_claim・claim_for_p27・classify・pick_r・RealBackend)と
``measure/inject.py``(select・apply_edits・revert・verify_seed_sealed)を importlib / import で使う(写さない・編集しない)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- 数の claim = ``kind == "num"``。claim の並びは 4 profile で同じ(id と (value, span, unit) が同じ位置で同じ)ことを本ごとに確かめ、違えば ``対応`` を偽にして記録する。
- 行頭の記号・1 行に数が 2 つ以上: claim の ``sentence`` を含む行(NFKC)を探し、行頭の最初の字が 「・」「|」「Q」「A」 ならその字、それ以外は「他」。行内の数(``lib.numbers.scan`` で単位が付き ``is_quantity`` の token)が 2 つ以上なら複数の数。行が見つからなければ None。
- 注入の土台 = 無改変の文で 4 profile 全部が GROUNDED の claim(P27 の claim に ``find_base_claim`` で 1 件に決まり、他の 3 profile の同じ位置の claim の (value, span, unit) が同じ)。
  T1_VALUE の上限は ``inject.select`` の採用に掛け(基準で絞る前)、T8_REL の上限は site に掛ける(前例 §6 と同じ)。``inject.select`` の docID の引数には本の名前を渡す(本ごとに引く)。
- 札付けの束の鍵は ``<docID>_<名前の sha256 先頭 10>``(form と model を席に見せない)。対応表 ``dossiers/index.json`` は repo の外。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
import random
import re
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def load_module(name_file, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GEN = load_module("xbrl_aiforms_gen_2026-11-03.py", "aiforms_gen_for_run")
TUNE = load_module("xbrl_p27_tune_2026-10-27.py", "p27_tune_for_aiforms")
import inject as IJ                                   # noqa: E402
from lib import numbers as N                         # noqa: E402

SEAL_REL = GEN.SEAL_REL
SEAL_COMMIT = GEN.SEAL_COMMIT
CLAIMS_REL = GEN.REC_DIR_REL + "/claims_2026-11-03.json"
INJECT_REL = GEN.REC_DIR_REL + "/inject_2026-11-03.json"
PROFILES = ("P27", "P27E", "P28", "P28E")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
INJECT_TYPES = ("T1_VALUE", "T8_REL")
INJECT_CAP = 10                                          # 封 §0-2 の 6 (b): 1 本あたり型ごと
LEADS = (u"・", u"|", u"Q", u"A")
LEAD_OTHER = u"他"
#: profile ごとの欄(claims の行の中の並び)。pointers は ``<要素>@<当期|前期|他>`` の字の列
PROFILE_COLS = (u"state", u"reason", u"pointers", u"subject", u"other_subject_2026_11_02", u"p27_gate", u"last_branch_evidence")
CLAIM_COLS = (u"id", u"kind", u"form", u"unit", u"multi_number_line", u"lead")
FORBIDDEN_KEYS = ("span", "value", "recomputed", u"文", u"sentence", u"text", u"数", u"元の字", u"後の字", u"新しい値")
POINTER_RE = re.compile(r"^xbrl:([A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+)@([A-Za-z0-9_\-]+)$")
SAFE_REASON = TUNE.SAFE_REASON

# ---- 札付けの席の指示文(字は固定し、封の門が照らす。2026-10-09 の札の作法: 真 / 偽 / 判定不能・根拠・誤りの型・確信)
LABELLER_PROMPT = u"""あなたは、AI が書いた財務レポートの数が正しいかを 1 つずつ札付けする担当です。

渡す束(JSON 1 つ)に、レポートの数の一覧(claims: id・文・数・単位・周り)と、その会社の XBRL の fact の表の file の道(facts)があります。fact の表を Read で読み、1 つずつ次の札を付けてください。

- 札: 真 / 偽 / 判定不能
  - 真: 文のこの数は、fact の表の値から(単位の換算・丸め・前期との差・比率の計算を含めて)正しく導ける。
  - 偽: 文のこの数は、表の値から導けない(数が違う・期が違う・項目が違う・単位や桁が違う・計算が違う)。
  - 判定不能: 表だけでは決められない(表に対応する項目が無い・文の意味が取れないなど)。
- 根拠: 1〜2 文。使った fact の要素名(表の「項目(要素名)」の字そのまま)・期・値を書く。
- 誤りの型(札が偽のときだけ。真・判定不能は null): 数値の違い / 期の取り違え / 項目の取り違え / 単位・桁の取り違え / 計算の誤り / その他
- 確信: 高 / 中 / 低

決まり:
1. 材料は束と fact の表だけです。ほかの file・ネットワーク・記憶の知識は使わないでください。特に ~/Desktop/sgogi-coach-handoff/ と ~/.cache/audit-core/edinetdb-p27/ は開かないでください。道具(engine)の出力は見ないでください。
2. 1 つの数ごとに、その数が文のどの項目の何の期の金額・比率を言っているかを読んでから、表と照らしてください。
3. どちらとも決められないときは判定不能にしてください。
4. 答えは次の JSON を 1 つだけ返してください(claims の id を 1 つも欠かさず、1 度ずつ): {"札": [{"id": "<id>", "札": "真|偽|判定不能", "根拠": "<1〜2 文>", "誤りの型": "<型>|null", "確信": "高|中|低"}, ...]}"""
LABELLER_PROMPT_SHA256 = hashlib.sha256(LABELLER_PROMPT.encode("utf-8")).hexdigest()
LABEL_WORDS = (u"真", u"偽", u"判定不能")
ERROR_TYPES = (u"数値の違い", u"期の取り違え", u"項目の取り違え", u"単位・桁の取り違え", u"計算の誤り", u"その他")
CONFIDENCE = (u"高", u"中", u"低")

Stop = GEN.Stop
sha256_text = GEN.sha256_text
sha256_file = GEN.sha256_file
jload = GEN.jload


# ======================================================================================================
# 材料(生成の記録と文)
def load_gen(root=ROOT, gen_path=None):
    gen_path = gen_path or os.path.join(root, GEN.GEN_REL)
    if not os.path.exists(gen_path):
        raise Stop(u"**生成の記録が無い: %s。止める**" % os.path.basename(gen_path))
    return jload(gen_path)


def gen_items(gen):
    u"""生成できた本(ok)の name → 記録の行。同じ name が複数あれば後の ok を採る(--resume の再試行)。"""
    out = collections.OrderedDict()
    for c in gen[u"呼び出し"]:
        if c[u"ok"]:
            out[c[u"name"]] = c
    return out


def read_text(name, item, new_cache):
    p = os.path.join(new_cache, "texts", name + ".txt")
    with io.open(p, "rb") as fh:
        b = fh.read()
    t = b.decode("utf-8")
    if GEN.sha256_text(t) != item[u"sha256"]:
        raise Stop(u"**文の sha256 が生成の記録と違う: %s。止める**" % name)
    return t


def company_rows(gen, root=ROOT):
    u"""生成の記録の 20 社の行({docID, 標本, zip の sha256, claims})。97 の記録の行と突き合わせる。"""
    r97 = dict((r["docID"], r) for r in jload(os.path.join(root, GEN.REGRESS97_REL))[u"書類"])
    ids = gen[u"会社の選び"][u"docID"]
    rows = []
    for d in ids:
        if d not in r97:
            raise Stop(u"**選んだ会社が 97 の記録に無い: %s。止める**" % d)
        rows.append(r97[d])
    return rows


def dossier_key(name):
    docid = name.split("_")[0]
    return u"%s_%s" % (docid, hashlib.sha256((u"aiforms|%s" % name).encode("utf-8")).hexdigest()[:10])


def seat2_names(names, seed):
    u"""2 席目を立てる本。名前の昇順に並べ、``random.Random("<seed>|AIFORMS_SEAT2").sample`` で GEN.SEAT2_N(32)本。昇順で返す。"""
    pool = sorted(names)
    k = min(GEN.SEAT2_N, len(pool))
    return sorted(random.Random("%s|AIFORMS_SEAT2" % seed).sample(pool, k))


# ======================================================================================================
# 1 本の判定
def period_kind(ctx):
    return u"当期" if ctx.startswith("CurrentYear") else (u"前期" if ctx.startswith("Prior1Year") else u"他")


def pointer_strings(pointers):
    u"""pointers のうち xbrl の fact を ``<要素>@<当期|前期|他>`` の字に。xbrl でない pointers は ``(xbrl 以外)`` 1 つ。形が合わないものは止める。"""
    out, other = [], False
    for p in pointers or []:
        m = POINTER_RE.match(p)
        if m:
            out.append(u"%s@%s" % (m.group(1), period_kind(m.group(2))))
        elif isinstance(p, str) and not p.startswith("xbrl:"):
            other = True
        else:
            raise Stop(u"**pointers の字が符号の形でない。止める**")
    if other:
        out.append(u"(xbrl 以外)")
    return out


def lines_nfkc(text):
    return [unicodedata.normalize("NFKC", ln).strip() for ln in text.split("\n")]


def line_info(lines, sentence, span):
    u"""claim の文を含む行 → (行頭の記号 or 他, 行内の数が 2 つ以上か)。行が見つからなければ (None, None)。"""
    for needle in (sentence, span):
        if not needle or not isinstance(needle, str):
            continue
        for ln in lines:
            if ln and needle in ln:
                head = ln[0]
                lead = head if head in LEADS else LEAD_OTHER
                toks = [t for t in N.scan(ln) if t.unit is not None and N.is_quantity(ln, t)]
                return lead, len(toks) >= 2
    return None, None


def other_subject_cell(raw):
    o = raw.get("other_subject_2026_11_02")
    if o is None:
        return None
    return [o.get(u"前期"), o.get(u"候補"), o.get(u"決まった")]


def safe_reason(r):
    if r is None:
        return None
    if not isinstance(r, str) or not SAFE_REASON.fullmatch(r):
        raise Stop(u"**reason の字が符号の形でない。止める**")
    return r


def sentence_list(zm, profile):
    u"""raw claim の ``sentence``(文の番号)が指す文の字の列。engine の ``build_raw_claims`` と同じ手順(MD&A の textBlock → strip_html → split_sentences)。"""
    from adapters.xbrl import extract as E
    from adapters.xbrl import instance as I
    inst = I.load_instance(zm)
    name = I.select_mdna(inst["textblocks"])
    body = I.strip_html(inst["textblocks"][name]) if name else ""
    return E.split_sentences(body, profile.paren_sentence)


SAME = u"="


def encode_cells(cells):
    u"""profile の欄の列。直前の profile と同じ欄は ``"="`` に縮める(記録を小さくする。``decode_row`` で戻る)。"""
    return [SAME if j > 0 and c == cells[j - 1] else c for j, c in enumerate(cells)]


def decode_row(row):
    u"""記録の 1 行 → {claim の欄: 値, profile: {欄: 値} or None}。"""
    d = dict(zip(CLAIM_COLS, row[:len(CLAIM_COLS)]))
    prev = None
    for p, cell in zip(PROFILES, row[len(CLAIM_COLS):]):
        cell = prev if cell == SAME else cell
        d[p] = dict(zip(PROFILE_COLS, cell)) if cell is not None else None
        prev = cell
    return d


def judge_text(zb, text):
    u"""1 本 → (記録の 本 の欄(名前などを除く), P27 の数の claim の dossier 用の行)。claim の並びが 4 profile で違えば 対応 = 偽。"""
    from adapters.xbrl import verify_document as VD
    from adapters.xbrl import prose as PR
    from adapters.xbrl import recipes as R
    from adapters.xbrl import vocabulary as V
    zm, _el, _mem = PR.build_modified_zip(zb, text)
    outs, raws = {}, {}
    for p in PROFILES:
        outs[p] = VD.verify_document(zb, p, text)
        nums, texts = R.build_raw_claims(zm, V.PROFILES[p])
        raws[p] = nums + texts
    base = outs["P27"]["claims"]
    same = True
    for p in PROFILES:
        cs, rs = outs[p]["claims"], raws[p]
        if len(cs) != len(base) or len(rs) != len(base):
            same = False
            continue
        for x, y, r in zip(base, cs, rs):
            if not (x["id"] == y["id"] == r["id"] and (x["value"], x["span"], x["unit"]) == (y["value"], y["span"], y["unit"])):
                same = False
    lines = lines_nfkc(text)
    sentences = sentence_list(zm, V.PROFILES["P27"])
    rows, dossier = [], []
    for i, x in enumerate(base):
        r0 = raws["P27"][i] if i < len(raws["P27"]) else {}
        si = r0.get("sentence")
        stext = sentences[si] if isinstance(si, int) and 0 <= si < len(sentences) else None
        lead, multi = line_info(lines, stext, x["span"])
        row = [x["id"], x["kind"], x["form"], x["unit"], multi, lead]
        cells = []
        for p in PROFILES:
            if i < len(outs[p]["claims"]):
                c = outs[p]["claims"][i]
                r = raws[p][i] if i < len(raws[p]) else {}
                cells.append([c["state"], safe_reason(c["reason"]), pointer_strings(c["pointers"]), bool(r.get("subject")),
                              other_subject_cell(r), r.get("p27_gate"), r.get("last_branch_evidence")])
            else:
                cells.append(None)
        rows.append(row + encode_cells(cells))
        if x["kind"] == "num":
            dossier.append({"id": x["id"], u"文": stext, u"数": x["value"], u"単位": x["unit"], u"周り": x["span"]})
    states = dict((p, dict((s, outs[p]["document"]["states"].get(s, 0)) for s in STATES)) for p in PROFILES)
    rec = collections.OrderedDict([(u"対応", same), (u"行数", len(lines)), (u"claim の数", len(base)),
                                   (u"数の claim の数(P27)", sum(1 for x in base if x["kind"] == "num")),
                                   (u"4 state", states), (u"行", rows)])
    return rec, dossier


def judge_job(args):
    name, item, row, text_path_dir, zip_caches = args
    zb = GEN.read_zip(row, zip_caches)
    text = read_text(name, item, text_path_dir)
    rec, dossier = judge_text(zb, text)
    rec = collections.OrderedDict([(u"name", name), (u"docID", item[u"docID"]), (u"form", item[u"form"]), (u"model", item[u"model"]),
                                   (u"writer", item[u"writer"]), (u"文の sha256", item[u"sha256"]), (u"字数", item[u"chars"])] + list(rec.items()))
    return name, rec, dossier


# ======================================================================================================
# 並列(fork)
_STATE = {}


def _worker(job):
    kind = _STATE["kind"]
    return (judge_job if kind == "judge" else inject_job)(job)


def map_jobs(kind, jobs_, procs, state=None):
    u"""jobs_ を kind の関数で処理した結果の列(jobs_ と同じ順)。procs > 1 は fork した process が queue から 1 本ずつ取る
    (関数を pickle しない = importlib で読んだ module でも動く。結果は plain data だけを queue に載せる)。"""
    _STATE.clear()
    _STATE.update(state or {})
    _STATE["kind"] = kind
    if procs <= 1 or len(jobs_) <= 1:
        return [_worker(j) for j in jobs_]
    ctx = multiprocessing.get_context("fork")
    todo, done = ctx.Queue(), ctx.Queue()
    for i in range(len(jobs_)):
        todo.put(i)
    n = min(procs, len(jobs_))
    for _ in range(n):
        todo.put(None)

    def loop():
        while True:
            i = todo.get()
            if i is None:
                return
            try:
                done.put((i, "ok", _worker(jobs_[i])))
            except BaseException as exc:                     # noqa: BLE001  Stop を含む。文言に値は入っていない
                done.put((i, "err", str(exc) if isinstance(exc, SystemExit) else type(exc).__name__))

    procs_ = [ctx.Process(target=loop) for _ in range(n)]
    for pr in procs_:
        pr.start()
    out = [None] * len(jobs_)
    try:
        for _ in range(len(jobs_)):
            i, st, val = done.get()
            if st == "err":
                raise Stop(u"%s" % (val or u"**worker が止まった。止める**"))
            out[i] = val
    finally:
        for pr in procs_:
            pr.terminate()
    return out


# ======================================================================================================
# 注入
_REFS = {}


def base_status4(base_claims, base_by_id, tok, text):
    u"""(状態, P27 の土台の claim)。土台 = 無改変で 4 profile 全部が GROUNDED。"""
    digits = text[tok.start:tok.end]
    bc = TUNE.find_base_claim(base_claims["P27"], tok.value, digits, tok.unit)
    if bc is None:
        return u"基準に対応が付かない", None
    key = (bc["value"], bc["span"], bc["unit"])
    for p in PROFILES[1:]:
        o = base_by_id[p].get(bc["id"])
        if o is None or (o["value"], o["span"], o["unit"]) != key:
            return u"profile 間で claim が合わない", None
    gs = [base_by_id[p][bc["id"]]["state"] == "GROUNDED" for p in PROFILES]
    if all(gs):
        return u"4 profile とも GROUNDED", bc
    if any(gs):
        return u"一部の profile だけ GROUNDED", None
    return u"どの profile も GROUNDED でない", None


def t8_candidates4(text, refs, base_claims, base_by_id, seed, key, cap):
    u"""前例 ``t8_candidates`` と同じ手順(token の並べ替え・r の選び・cap)を、土台の判定だけ 4 profile にしたもの。"""
    from lib import sites as S
    counts = collections.Counter()
    vindex = S._value_index(refs)
    toks = [t for t in N.scan(text) if t.unit in TUNE.MONEY_FAMILY and N.is_quantity(text, t)]
    random.Random("%s|%s|T8_REL" % (seed, key)).shuffle(toks)
    counts[u"円族の token"] = len(toks)
    valid = []
    for t in toks:
        status, bc = base_status4(base_claims, base_by_id, t, text)
        counts[status] += 1
        if bc is None:
            continue
        pick = TUNE.pick_r(seed, key, bc["id"], t, vindex)
        if pick is None:
            counts[u"r が決まらず site にしない"] += 1
            continue
        valid.append((t, bc, pick))
    counts[u"作れる site"] = len(valid)
    out = []
    for t, bc, (r, new, tries) in valid[:cap]:
        inj = {"type": "T8_REL", "id": "%s-T8-%02d" % (key, len(out) + 1), "new_value": new, "replacement": N.render_value(new, t),
               "span": [t.start, t.end], "detail": {"original_value": t.value, "relative": r, "tries": tries, "unit": t.unit}}
        out.append((inj, t, bc))
    counts[u"採った"] = len(out)
    return out, counts


def inject_text(zb, text, refs, seed, key, cap=INJECT_CAP, verify=None):
    u"""1 本の注入(T1_VALUE・T8_REL)。1 回に 1 件。round-trip を確かめ、違えば止める。(行, 数え)。"""
    if N.normalize_digits(text) != text:
        return [], {u"注入しない": u"文に全角の数字がある(select は半角の文を前提にする)"}
    if verify is None:
        from adapters.xbrl import verify_document as VD
        verify = VD.verify_document
    base_claims = dict((p, verify(zb, p, text)["claims"]) for p in PROFILES)
    base_by_id = dict((p, dict((c["id"], c) for c in base_claims[p])) for p in PROFILES)
    toks = dict(((t.start, t.end), t) for t in N.scan(text))
    counts, work_list = {}, []
    chosen, cat, _a, _w = IJ.select(text, refs, "xbrl", seed, key, cap, types=["T1_VALUE"])
    c1 = collections.Counter()
    c1[u"作れる site"], c1[u"採った"] = cat["T1_VALUE"], len(chosen)
    for inj in chosen:
        tok = toks[tuple(inj["span"])]
        status, bc = base_status4(base_claims, base_by_id, tok, text)
        c1[status] += 1
        work_list.append((inj, tok, bc))
    counts["T1_VALUE"] = dict(c1)
    t8, c8 = t8_candidates4(text, refs, base_claims, base_by_id, seed, key, cap)
    counts["T8_REL"] = dict(c8)
    work_list += t8
    rows = []
    for inj, tok, bc in work_list:
        tampered, placements = IJ.apply_edits(text, [inj])
        if IJ.revert(tampered, [inj], placements, text) != text:
            raise Stop(u"**round-trip が合わない: %s。止める**" % inj["id"])
        if bc is None:
            continue
        row = collections.OrderedDict([("id", inj["id"]), (u"型", inj["type"]), (u"基準の claim", bc["id"])])
        if inj["type"] == "T8_REL":
            row["r"], row[u"r を決めた回"] = inj["detail"]["relative"], inj["detail"]["tries"]
        for p in PROFILES:
            res = TUNE.claim_for_p27(verify(zb, p, tampered)["claims"], inj, tok.unit)
            row[p] = TUNE.classify(res, base_by_id[p][bc["id"]])
        rows.append(row)
    return rows, counts


def refs_for(row, zip_caches, work_root):
    doc = row["docID"]
    if doc not in _REFS:
        work = os.path.join(work_root, doc)
        os.makedirs(work, exist_ok=True)
        _REFS[doc] = TUNE.RealBackend().refs(GEN.zip_path(row, zip_caches), doc, work)
    return _REFS[doc]


def inject_job(args):
    name, item, row, text_dir, zip_caches, seed, work_root = args
    zb = GEN.read_zip(row, zip_caches)
    text = read_text(name, item, text_dir)
    refs = refs_for(row, zip_caches, work_root)
    rows, counts = inject_text(zb, text, refs, seed, name)
    base = {u"docID": item[u"docID"], u"form": item[u"form"], u"model": item[u"model"], u"writer": item[u"writer"]}
    return name, [collections.OrderedDict(list(base.items()) + list(r.items())) for r in rows], counts


# ---- 集計(inject 記録の 集計。tally も同じ関数を使う)
def inject_group(rows, key_fn):
    groups = collections.OrderedDict()
    for r in rows:
        groups.setdefault(key_fn(r), []).append(r)
    return groups


def inject_cell(sel, p):
    mapped = [r for r in sel if r[p][u"対応"]]
    lab = collections.Counter(r[p][u"結果"] for r in mapped)
    d = collections.OrderedDict([(u"注入の行", len(sel)), (u"対応が付く", len(mapped)), (u"対応が付かない", len(sel) - len(mapped))])
    for label in (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV):
        d[label] = TUNE.frac(lab.get(label, 0), len(mapped))
    return d


def inject_summary(rows):
    out = collections.OrderedDict()
    for t in INJECT_TYPES:
        out[t] = collections.OrderedDict()
        for p in PROFILES:
            tr = [r for r in rows if r[u"型"] == t]
            cell = collections.OrderedDict([(u"全体", inject_cell(tr, p))])
            cell[u"形別"] = collections.OrderedDict((k, inject_cell(v, p)) for k, v in sorted(inject_group(tr, lambda r: r["form"]).items()))
            cell[u"model 別"] = collections.OrderedDict((k, inject_cell(v, p)) for k, v in sorted(inject_group(tr, lambda r: r["writer"]).items()))
            cell[u"形 × model"] = collections.OrderedDict((u"%s×%s" % k, inject_cell(v, p)) for k, v in sorted(inject_group(tr, lambda r: (r["form"], r["writer"])).items()))
            out[t][p] = cell
    return out


# ======================================================================================================
# 記録の書き方
def dumps_compact_rows(rec):
    u"""``本`` の中の ``行`` だけ 1 行 1 claim にして書く(他は indent=1)。"""
    holders, rows_by_token = [], {}
    rec2 = json.loads(json.dumps(rec, ensure_ascii=False))
    for i, b in enumerate(rec2.get(u"本", [])):
        if isinstance(b.get(u"行"), list):
            tok = u"@@ROWS_%d@@" % i
            rows_by_token[tok] = b[u"行"]
            b[u"行"] = tok
    text = json.dumps(rec2, ensure_ascii=False, indent=1)
    for tok, rows in rows_by_token.items():
        body = u"[\n" + u",\n".join(u"  " + json.dumps(r, ensure_ascii=False) for r in rows) + u"\n  ]" if rows else u"[]"
        text = text.replace(json.dumps(tok), body)
    return text + u"\n"


def walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            for x in walk_keys(v):
                yield x
    elif isinstance(obj, list):
        for v in obj:
            for x in walk_keys(v):
                yield x


def assert_clean(rec, key_value=None):
    bad = sorted(set(k for k in walk_keys(rec) if k in FORBIDDEN_KEYS))
    if bad:
        raise Stop(u"**記録に repo へ入れない欄がある: %s。止める**" % u",".join(bad))
    # pointers の字(要素名は長い英字)は『32 字以上の英数字』では見ず、鍵の形・環境の鍵の値だけ当てる。それ以外の全部は完全に当てる
    rest = dict((k, v) for k, v in rec.items() if k not in (u"本", u"行"))
    leaks = GEN.key_leaks(json.dumps(rest, ensure_ascii=False), key_value)
    for b in rec.get(u"本", []):
        leaks += GEN.key_leaks(json.dumps(dict((k, v) for k, v in b.items() if k != u"行"), ensure_ascii=False), key_value)
        leaks += GEN.key_leaks(json.dumps(b.get(u"行"), ensure_ascii=False), key_value, long_alnum=False)
    leaks += GEN.key_leaks(json.dumps(rec.get(u"行"), ensure_ascii=False), key_value, long_alnum=False)
    if leaks:
        raise Stop(u"**鍵らしい字が記録に在る(%s)。書かずに止める**" % u" / ".join(sorted(set(leaks))))


def write_record(path, text, rec, key_value=None):
    assert_clean(rec, key_value)
    if os.path.exists(path):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(path))
    GEN.write_text(path, text)


def header(root, step, gen_path, seed_meta, before, after):
    return collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT), (u"step", step), (u"HEAD の commit", GEN.git_head(os.path.dirname(root))),
        (u"この script の sha256", sha256_file(os.path.abspath(__file__))), (u"生成の script の sha256", sha256_file(os.path.join(HERE, "xbrl_aiforms_gen_2026-11-03.py"))),
        (u"生成の記録の sha256", sha256_file(gen_path)), (u"engine の指紋", engine_fingerprint()),
        (u"種の確認", seed_meta), (u"profile", list(PROFILES)),
        (u"cache の前後", collections.OrderedDict([(u"前", before), (u"後", after), (u"変化なし", before == after)])),
    ])


def engine_fingerprint():
    from adapters.xbrl import verify_document as VD
    return VD.engine_fingerprint()


# ======================================================================================================
def prepare_run(root, only, gen_path, new_cache, caches):
    gen = load_gen(root, gen_path)
    items = gen_items(gen)
    companies = company_rows(gen, root)
    by_doc = dict((r["docID"], r) for r in companies)
    names = [GEN.text_key(d, f, m) for d in gen[u"会社の選び"][u"docID"] for f in GEN.FORMS for m in GEN.MODELS]
    if only is not None:
        if only not in by_doc:
            raise Stop(u"**--only の docID が選んだ 20 社に無い。止める**")
        names = [n for n in names if n.split("_")[0] == only]
    return gen, items, by_doc, names


def run_judge(root=ROOT, procs=1, only=None, gen_path=None, new_cache=None, caches=None, out=None, key_value=None, say=print, seed=None, seed_meta=None):
    new_cache = new_cache or GEN.NEW_CACHE
    caches = caches or GEN.EXISTING_CACHES
    out = out or os.path.join(root, CLAIMS_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    if seed is None:
        seed, seed_meta = GEN.seed_value(root)
    gen, items, by_doc, names = prepare_run(root, only, gen_path, new_cache, caches)
    before = GEN.caches_snapshot(caches)
    present = [n for n in names if n in items]
    jobs_ = [(n, items[n], by_doc[n.split("_")[0]], new_cache, caches) for n in present]
    say(u"判定 %d 本(欠け %d 本)× 4 profile ― procs %d" % (len(jobs_), len(names) - len(present), procs))
    results = map_jobs("judge", jobs_, procs)
    dossier_dir = os.path.join(new_cache, "dossiers")
    index, books = collections.OrderedDict(), []
    got = dict((r[0], r) for r in results)
    for n in names:
        if n not in items:
            books.append(collections.OrderedDict([(u"name", n), (u"docID", n.split("_")[0]), (u"欠け", True)]))
            continue
        _n, rec, dossier = got[n]
        key = dossier_key(n)
        index[key] = n
        GEN.write_text(os.path.join(dossier_dir, key + ".json"), GEN.dumps(collections.OrderedDict([
            (u"key", key), (u"facts", os.path.join(new_cache, "facts", n.split("_")[0] + ".md")), (u"claims", dossier)])))
        rec[u"札付けの束の鍵"] = key
        books.append(rec)
    GEN.write_text(os.path.join(dossier_dir, "index.json"), GEN.dumps(index))
    s2 = seat2_names([n for n in names if n in items], seed)
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**既存の cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header(root, u"AI の形 4 × model 2 ― 4 profile の判定(0 USD)", gen_path or os.path.join(root, GEN.GEN_REL), seed_meta, before, after)
    rec[u"欄"] = collections.OrderedDict([(u"claim", list(CLAIM_COLS)), (u"profile ごと", list(PROFILE_COLS)),
                                         (u"行の並び", u"claim の欄 → P27 → P27E → P28 → P28E の順(profile の欄は配列。直前の profile と同じなら \"=\")"),
                                         (u"pointers の字", u"<要素>@<当期|前期|他>(xbrl 以外は (xbrl 以外))"),
                                         (u"other_subject_2026_11_02", u"[前期, 候補, 決まった] か null")])
    rec[u"札付けの席の指示文の sha256"] = LABELLER_PROMPT_SHA256
    rec[u"2 席目を立てる本"] = s2
    rec[u"本"] = books
    rec[u"欠けた本"] = [b[u"name"] for b in books if b.get(u"欠け")]
    rec[u"repo の外に置いたもの"] = {u"folder": GEN.NEW_CACHE.replace(os.path.expanduser("~"), "~"), u"札付けの束": u"dossiers/<鍵>.json(対応表 dossiers/index.json)"}
    write_record(out, dumps_compact_rows(rec), rec, key_value)
    say(u"-> %s(本 %d・欠け %d)" % (out, len(books), len(rec[u"欠けた本"])))
    return rec


def run_inject(root=ROOT, procs=1, only=None, gen_path=None, new_cache=None, caches=None, out=None, key_value=None, say=print, seed=None, seed_meta=None, work_root=None):
    new_cache = new_cache or GEN.NEW_CACHE
    caches = caches or GEN.EXISTING_CACHES
    out = out or os.path.join(root, INJECT_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    if seed is None:
        seed, seed_meta = GEN.seed_value(root)
    gen, items, by_doc, names = prepare_run(root, only, gen_path, new_cache, caches)
    before = GEN.caches_snapshot(caches)
    work_root = work_root or tempfile.mkdtemp(prefix="aiforms_inject_", dir=os.environ.get("TMPDIR"))
    present = [n for n in names if n in items]
    jobs_ = [(n, items[n], by_doc[n.split("_")[0]], new_cache, caches, seed, work_root) for n in present]
    say(u"注入 %d 本 ― procs %d(本ごと 4 profile × 注入 1 件ごとに判定。時間がかかる)" % (len(jobs_), procs))
    results = map_jobs("inject", jobs_, procs)
    rows, per = [], collections.OrderedDict()
    for n, r, c in results:
        rows += r
        per[n] = c
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**既存の cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header(root, u"AI の形 4 × model 2 ― 注入(T1_VALUE・T8_REL。0 USD)", gen_path or os.path.join(root, GEN.GEN_REL), seed_meta, before, after)
    rec[u"種"] = {u"file": SEED_REL_STR, u"種の確認": seed_meta}
    rec[u"型"] = collections.OrderedDict([("T1_VALUE", u"inject.select(types=[T1_VALUE]) のまま。cap は採用に掛ける(基準で絞る前)"),
                                         ("T8_REL", u"円の単位族の token・r ∈ %s・%d 回まで。cap は site に掛ける" % (list(TUNE.T8_R_VALUES), TUNE.T8_TRIES)),
                                         (u"上限", u"型ごと・1 本あたり %d" % INJECT_CAP),
                                         (u"土台", u"無改変の文で 4 profile 全部が GROUNDED の claim"),
                                         (u"inject.select の docID の引数", u"本の名前(<docID>_<形>_<model>)")])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"] = inject_summary(rows)
    rec[u"行"] = rows
    rec[u"限界"] = [u"注入は 2 型だけ(値・相対のずれ)。期・単位・主語の取り違えは注入しない", u"T8_REL の r の 4 値は前例の決め打ち"]
    write_record(out, dumps_inject(rec), rec, key_value)
    say(u"-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


SEED_REL_STR = GEN.SEED_REL


def dumps_inject(rec):
    u"""``行`` を 1 行 1 注入にして書く。"""
    rec2 = json.loads(json.dumps(rec, ensure_ascii=False))
    rows = rec2.pop(u"行")
    rec2[u"行"] = u"@@ROWS@@"
    text = json.dumps(rec2, ensure_ascii=False, indent=1)
    body = u"[\n" + u",\n".join(u"  " + json.dumps(r, ensure_ascii=False) for r in rows) + u"\n ]" if rows else u"[]"
    return text.replace(json.dumps(u"@@ROWS@@"), body) + u"\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("judge", "inject"))
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--only", default=None, help="この docID の 8 本だけ(記録は書かれる ― 本番の記録を作らない確認用には --out を替える)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    fn = run_judge if a.cmd == "judge" else run_inject
    fn(root=a.root, procs=a.procs, only=a.only, out=a.out)


if __name__ == "__main__":
    main()
