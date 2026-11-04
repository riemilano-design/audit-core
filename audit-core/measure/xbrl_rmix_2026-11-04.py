# -*- coding: utf-8 -*-
u"""封 docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md §5 ― RB(丸め方の根拠が混ざる桁は両方の帯で照らす。P30E = P29E + RB)の AI の文 200 本の判定・注入と、結果の表(tally)。**0 USD・通信なし・鍵は読まない・LLM は呼ばない。**

    python3 measure/xbrl_rmix_2026-11-04.py judge  [--procs N] [--only <docID>] [--out PATH]   # P28E・P29E・P30E の判定。既存の行に前の便の札を当てる → fixtures/xbrl/rmix/ai200_2026-11-04.json
    python3 measure/xbrl_rmix_2026-11-04.py inject [--procs N] [--only <docID>] [--out PATH]   # P29E・P30E の注入(T1_VALUE・T8_REL。土台 = P30E が GROUNDED)→ fixtures/xbrl/rmix/inject_2026-11-04.json
    python3 measure/xbrl_rmix_2026-11-04.py tally  [--root DIR]                                 # 記録 3 つ(ai200・inject・regress97)から D-1〜D-10 と K-1〜K-5 の表を出す(file は書かない)

数の読み取り N の便の script ``xbrl_numfix_2026-11-04.py``(NF)は **1 byte も変えず**、importlib で読み込んで差し替える(F5 の駆動 script ``xbrl_aiforms_f5_2026-11-03.py`` と同じ作り)。
差し替える先: 封の名と commit・記録の path・header(step の字・この script の sha256)・鍵の検査から除く封の path・注入の入れ替え(``RUN.PROFILES``・``RUN.base_status4``)。
差し替えが届いていることは ``wiring_problems`` が見る(使う側の実体に届かないと黙って効かない)。文は前の便の記録 ``fixtures/xbrl/aiforms/{gen,f5_gen}_2026-11-03.json`` の 200 本を
**読むだけ**(cache に 1 file も足さない。件数と名前の一覧の sha256 を前後で記録し、変われば止める)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- 数の claim の鍵は N の便と同じ ``(文の番号, 位置)``(id は profile 間で替わる)。P30E は P29E と数の claim の数が同じ(RB は 3 周目で差し替えるだけ)なので鍵の集合も同じはず。違えば本の欄に出す。
- 札: 前の便の盲検の札(``labels_2026-11-03.json``・``f5_labels_2026-11-03.json`` の 1 席目)を、P27 の raw claim の並び(``R.build_raw_claims(zm, P27)`` と ``RUN.judge_text`` の行の index が対応)で
  鍵 → id に結んで引く。札のある行 = 前の便が札を付けた P27 の数の claim(= P28E にもある既存の行)。新しい行(P28E に鍵が無い行)には札が無い。
- 「既存の行」= P28E にも同じ鍵がある行。「GROUNDED になった行」= P29E で GROUNDED でなく P30E で GROUNDED の行。「GROUNDED を失った行」= 逆。
- D-1 の P29E 側: P29E の行から N の便の ``analyse_book``(NF の関数。P29E−O の席に P29E の行を置く = O の欄だけ使わない)で欄を作り直し、N の便の ``ai200`` の本の欄
  (数の claim の数 P28E・P29E・新しい行・置き換え・新しい行の state・既存の行・書類の丸め方・O の形の行・O が決めた行 ほか)と JSON に通して比べる。旗が偽の P27〜P28E は ``RUN.judge_text`` の 行・4 state・claim の数 を ``claims`` の記録と比べる(N の便と同じ)。
- 動いた行 = P29E と P30E の両方にある鍵のうち (state, reason, pointers) が違う行(state が違う行は別に数える)。
- K-2 の 8 行: N の便の ``ai200`` の ``同じ文に新しい行が無いのに変わった既存の行`` を鍵に、P30E の state を引く。「P29E で GROUNDED を失っていた」= N の便の記録の 前 state が GROUNDED で 後 state が GROUNDED でない行。
- 注入は N の便の ``RUN.inject_text`` 型の手順で、土台 = P30E が GROUNDED の claim。P29E の claim は (value, span, unit) が同じ 1 件で結ぶ(N の便の ``base_status_n`` を P30E 土台にした版をこの script に持つ。
  N の便の版は状態の字・行の欄の名前に P28E・P29E を書いているので使わない)。

engine(``core/``・``adapters/``)は 1 行も変えない。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


NF = load_module("xbrl_numfix_2026-11-04.py", "numfix_for_rmix")
GEN, RUN = NF.GEN, NF.RUN
TUNE, IJ = NF.TUNE, NF.IJ
Stop = GEN.Stop

from adapters.xbrl import prose as PR                # noqa: E402
from adapters.xbrl import recipes as R               # noqa: E402
from adapters.xbrl import verify_document as VD      # noqa: E402
from adapters.xbrl import vocabulary as V            # noqa: E402

SEAL_REL = "docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md"
SEAL_COMMIT = "de23edc"
DOC_REL = "docs/XBRL_ROUNDING_MIXED_ENGINE_RESULT_2026-11-04.md"
REC_DIR_REL = "fixtures/xbrl/rmix"
AI200_REL = REC_DIR_REL + "/ai200_2026-11-04.json"
INJECT_REL = REC_DIR_REL + "/inject_2026-11-04.json"
REGRESS97_REL = REC_DIR_REL + "/regress97_2026-11-04.json"
REC_REL = collections.OrderedDict([("ai200", AI200_REL), ("inject", INJECT_REL), ("regress97", REGRESS97_REL)])
#: 読むだけの前の便の記録(N の便の ai200・regress97。札の記録)
N_AI200_REL = "fixtures/xbrl/numfix/ai200_2026-11-04.json"
N_REGRESS97_REL = "fixtures/xbrl/numfix/regress97_2026-11-04.json"
N_SCRIPT_REL = "measure/xbrl_numfix_2026-11-04.py"
LABELS_REL = collections.OrderedDict([("aiforms", NF.PREV_AI_DIR + "/labels_2026-11-03.json"), ("f5", NF.PREV_AI_DIR + "/f5_labels_2026-11-03.json")])
SOURCES = NF.SOURCES
STATES = NF.STATES
PROFILES = ("P28E", "P29E", "P30E")
INJECT_PROFILES = ("P29E", "P30E")
COMPARE_KEY = u"集計(比較用: P29E にも対応が付く site だけ)"
BASE_WORD = u"無改変の文で P30E が GROUNDED の claim"
LINKED, UNLINKED = u"P30E が GROUNDED(P29E の claim と対応が付く)", u"P30E が GROUNDED(P29E の claim に対応なし)"
LINK_KEY = u"P29E の土台に対応"
LIMIT_SCAN = u"注入の仕掛け(N.scan)は万・億のコンマの数を断片に切るため、D-8・D-9 は万・億のコンマの数に注入した誤りを測っていない(封 §6 の 1)。測れるのは断片に切られない数の site だけ"
LABEL_WORDS = (u"真", u"偽", u"判定不能")
NO_LABEL = u"札なし"
SAME_FIELDS = (u"行", u"4 state", u"claim の数")
#: N の便の ``ai200`` の本の欄のうち、P29E の行から作り直して比べる欄(P29E−O の席を使う欄は比べない)
N_COMPARE_KEYS = (u"新しい行の数", u"置き換えの行の数", u"P28E にあって P29E に無い行", u"そのうち新しい行と範囲が交わらない行", u"新しい行の state", u"既存の行",
                  u"書類の丸め方", u"丸め方の決定が P28E と P29E で違う", u"同じ文に新しい行が無いのに変わった既存の行", u"O の形の行", u"O が決めた行")
HIT, MISS = NF.HIT, NF.MISS
STEP_FROM, STEP_TO = u"数の読み取り N", u"RB(丸め方の根拠が混ざる桁)"


def jround(x):
    return json.loads(json.dumps(x))


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


# ======================================================================================================
# NF の差し替え(F5 の駆動 script と同じ作り)
ORIG = {"header": NF.header, "write_json": NF.write_json}


def header_rb(root, step, seed_meta, before, after, profiles):
    h = ORIG["header"](root, step, seed_meta, before, after, profiles)
    h[u"この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    h[u"numfix script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_numfix_2026-11-04.py"))
    h[u"N の便の記録の sha256"] = collections.OrderedDict((k, GEN.sha256_file(os.path.join(ROOT, p))) for k, p in (("ai200", N_AI200_REL), ("regress97", N_REGRESS97_REL)))
    return h


#: (属性, 差し替えた先)。NF の module の属性
SWAP_TABLE = (
    ("SEAL_REL", SEAL_REL), ("SEAL_COMMIT", SEAL_COMMIT), ("DOC_REL", DOC_REL), ("REC_DIR_REL", REC_DIR_REL), ("AI200_REL", AI200_REL), ("INJECT_REL", INJECT_REL),
    ("REGRESS97_REL", REGRESS97_REL), ("header", header_rb), ("INJECT_PROFILES", INJECT_PROFILES), ("BASE_WORD", BASE_WORD), ("COMPARE_KEY", COMPARE_KEY))


def install():
    for name, v in SWAP_TABLE:
        setattr(NF, name, v)
    NF.REC_REL = collections.OrderedDict(REC_REL)


def wiring_problems():
    u"""NF の差し替えが全部届いているか(使う側の実体に届かないと黙って効かない)。問題の列。"""
    out = []
    for name, v in SWAP_TABLE:
        if getattr(NF, name) != v and getattr(NF, name) is not v:
            out.append(u"NF.%s が差し替えた先でない" % name)
    if dict(NF.REC_REL) != dict(REC_REL):
        out.append(u"NF.REC_REL が rmix の記録でない")
    if RUN.GEN is not GEN or NF.GEN is not GEN:
        out.append(u"RUN.GEN が同じ instance でない")
    # 使う側: NF.header が RUN.header を呼ぶ・key_leaks_n が NF.SEAL_REL を引く(module の globals の名前に届いているか)
    if NF.key_leaks_n.__globals__["SEAL_REL"] != SEAL_REL:
        out.append(u"NF.key_leaks_n が引く SEAL_REL が rmix の封でない")
    if GEN.key_leaks is not NF.key_leaks_n:
        out.append(u"GEN.key_leaks が NF.key_leaks_n でない")
    return out


install()


def caches_all():
    return NF.caches_all()


def write_json(out, rec, key_value=None, text=None):
    text = text if text is not None else json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    RUN.write_record(out, text, rec, key_value)


# ======================================================================================================
# 材料
def load_labels(root=ROOT):
    u"""{source: {本の name: {claim の id: 札の語}}}。1 席目の札(前の便の盲検)。"""
    out = {}
    for src, rel in LABELS_REL.items():
        rec = GEN.jload(os.path.join(root, rel))
        out[src] = dict((b[u"name"], dict((x[0], x[1]) for x in b[u"札"])) for b in rec[u"本"])
    return out


def load_n_books(root=ROOT):
    return dict((b[u"name"], b) for b in GEN.jload(os.path.join(root, N_AI200_REL))[u"本"])


def load_jobs(root=ROOT, only=None):
    books = NF.load_books(root, only)
    labels = load_labels(root)
    nb = load_n_books(root)
    jobs_ = []
    for (src, n, item, row, prior) in books:
        if n not in nb:
            raise Stop(u"**N の便の ai200 に本が無い: %s。止める**" % n)
        jobs_.append((src, n, item, row, SOURCES[src]["cache"], GEN.EXISTING_CACHES, prior, labels[src].get(n, {}), nb[n]))
    return jobs_


# ======================================================================================================
# judge: 1 本
def profile_view_rb(zb, text, zm, pname):
    u"""N の便の ``NF.profile_view`` と同じ行の作りで、``build_raw_claims`` に info を渡す(混ざる桁の列を読む)。
    (行の辞書 {(文の番号, 位置): 欄}, 対応が付いたか, 文書の states, 混ざる桁の列 or None)。"""
    prof = V.PROFILES[pname]
    out = VD.verify_document(zb, pname, text)
    info = {}
    nums, texts = R.build_raw_claims(zm, prof, info)
    raws = nums + texts
    cl = out["claims"]
    ok = len(cl) == len(raws) and all(c["id"] == r["id"] for c, r in zip(cl, raws))
    sents = RUN.sentence_list(zm, prof)
    ends = {}
    rows = collections.OrderedDict()
    for c, r in zip(cl, raws):
        if c["kind"] != "num":
            continue
        si, a = r["sentence"], r["pos"]
        if si not in ends:
            ends[si] = dict((a2, b2) for (a2, b2, _v, _u, _p) in R._numbers_of(prof, sents[si]))
        key = (si, a)
        if key in rows:
            ok = False
        rows[key] = {"b": ends[si][a], "state": c["state"], "reason": RUN.safe_reason(c["reason"]), "pointers": RUN.pointer_strings(c["pointers"]),
                     "o": RUN.other_subject_cell(r)}
    return rows, ok, out["document"]["states"], info.get("rounding_mixed_scales_2026_11_04")


def id_map(zm, old):
    u"""P27 の数の claim の {(文の番号, 位置): id}。``old`` = ``RUN.judge_text`` の記録(行の index が P27 の raw claim の並びと対応)。(辞書, 対応が付いたか)。"""
    nums, texts = R.build_raw_claims(zm, V.PROFILES["P27"])
    ids = [r[0] for r in old[u"行"]]
    ok = bool(old[u"対応"]) and len(ids) == len(nums) + len(texts)
    out, dup = {}, False
    for i, r in enumerate(nums):
        if i >= len(ids):
            ok = False
            break
        key = (r["sentence"], r["pos"])
        if key in out:
            dup = True
        out[key] = ids[i]
    if dup:
        ok = False
    return out, ok


def label_of(key, idmap, labels, in_p28e):
    u"""既存の行の札の語(札のある行 = P28E にも在る行)。無ければ None。"""
    if not in_p28e:
        return None
    i = idmap.get(key)
    return labels.get(i) if i is not None else None


def analyse_book_rb(rows, oks, mixed, idmap, labels, rounding, n_book):
    u"""3 profile の行から本の記録の欄(数だけ。文・span・値は持たない)。n_book = N の便の ai200 の同じ本。(欄の辞書, N の便との比較の欄)。"""
    r28, r29, r30 = rows["P28E"], rows["P29E"], rows["P30E"]
    common = [k for k in r29 if k in r30]
    keys_same = sorted(r29) == sorted(r30)
    moved = [k for k in common if (r29[k]["state"], r29[k]["reason"], r29[k]["pointers"]) != (r30[k]["state"], r30[k]["reason"], r30[k]["pointers"])]
    smoved = [k for k in moved if r29[k]["state"] != r30[k]["state"]]
    lost = [k for k in common if r29[k]["state"] == "GROUNDED" and r30[k]["state"] != "GROUNDED"]
    gained = [k for k in common if r29[k]["state"] != "GROUNDED" and r30[k]["state"] == "GROUNDED"]
    entries = []
    for k in smoved:
        entries.append([u"num", k[0], k[1], r29[k]["state"], r30[k]["state"], label_of(k, idmap, labels, k in r28), u"既存" if k in r28 else u"新"])
    kinds = collections.Counter()
    for k in gained:
        if k in r28:
            kinds[label_of(k, idmap, labels, True) or NO_LABEL] += 1
    gained_new = sum(1 for k in gained if k not in r28)
    dirs = collections.Counter(u"%s → %s" % (r29[k]["state"], r30[k]["state"]) for k in smoved)
    # N の便の K-2 の行(同じ文に新しい行が無いのに変わった既存の行)の P30E の state
    k2 = []
    for x in n_book[u"同じ文に新しい行が無いのに変わった既存の行"]:
        key = (x[1], x[2])
        k2.append([x[0], x[1], x[2], x[3], x[4], r29[key]["state"] if key in r29 else None, r30[key]["state"] if key in r30 else None])
    # N の便の記録との比較(旗が偽の P29E)
    rebuilt = NF.analyse_book({"P28E": r28, "P29E": r29, "P29E-O": r29}, {"P28E": oks["P28E"], "P29E": oks["P29E"], "P29E-O": oks["P29E"]},
                              {"P28E": rounding["P28E"], "P29E": rounding["P29E"]})
    diff = [k for k in N_COMPARE_KEYS if jround(rebuilt[k]) != n_book[k]]
    if jround(dict((p, rebuilt[u"数の claim の数"][p]) for p in ("P28E", "P29E"))) != dict((p, n_book[u"数の claim の数"][p]) for p in ("P28E", "P29E")):
        diff.append(u"数の claim の数")
    rec = collections.OrderedDict([
        (u"対応", collections.OrderedDict((p, oks[p]) for p in PROFILES)),
        (u"数の claim の数", collections.OrderedDict((p, len(rows[p])) for p in PROFILES)),
        (u"P29E と P30E で数の claim の鍵が同じ", keys_same),
        (u"GROUNDED の数", collections.OrderedDict([("P29E", sum(1 for v in r29.values() if v["state"] == "GROUNDED")), ("P30E", sum(1 for v in r30.values() if v["state"] == "GROUNDED"))])),
        (u"混ざる桁", jround(mixed) if mixed is not None else None),
        (u"動いた行", len(moved)), (u"state が変わった行", len(smoved)), (u"動いた行の向き別", collections.OrderedDict(sorted(dirs.items()))),
        (u"GROUNDED を失った行", len(lost)), (u"GROUNDED になった行", len(gained)),
        (u"GROUNDED になった既存の行の札", collections.OrderedDict((w, kinds.get(w, 0)) for w in LABEL_WORDS + (NO_LABEL,))),
        (u"GROUNDED になった新しい行", gained_new),
        (u"state が変わった行の中身", entries),
        (u"K-2 の行", k2)])
    return rec, diff


def assemble_book_rb(src, name, item, same, rec, diff, idok):
    u"""1 本の記録の欄(``旗が偽の byte 一致`` の欄 same・analyse_book_rb の欄 rec と N の便の記録と違った欄 diff・P27 の鍵が一意か)。門が小さい標本の記録を作るのにも使う。"""
    same = collections.OrderedDict(same)
    same[u"P29E が N の便の記録と一致"] = not diff
    same[u"一致"] = all(same.values())
    head = collections.OrderedDict([(u"name", name), (u"docID", item[u"docID"]), (u"form", item[u"form"]), (u"model", item[u"model"]), (u"writer", item[u"writer"]),
                                    (u"材料", src), (u"文の sha256", item[u"sha256"])])
    head[u"旗が偽の byte 一致"] = same
    head[u"N の便の記録と違った欄"] = list(diff)
    head.update(rec)
    head[u"P27 の鍵が一意"] = idok
    return head


def judge_book_rb(job):
    src, name, item, row, text_dir, zip_caches, prior, labels, n_book = job
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    zm = PR.build_modified_zip(zb, text)[0]
    rows, oks, rounding, mixed = {}, {}, {}, None
    for p in PROFILES:
        with NF.capture_rounding() as cap:
            rows[p], oks[p], _st, m = profile_view_rb(zb, text, zm, p)
        rounding[p] = cap.result()
        if p == "P30E":
            mixed = m
    old = RUN.judge_text(zb, text)[0]                       # 旗が偽の profile(前の便の 4 つ)のまま
    idmap, idok = id_map(zm, old)
    same = collections.OrderedDict([(f, jround(old[f]) == prior[f]) for f in SAME_FIELDS])
    rec, diff = analyse_book_rb(rows, oks, mixed, idmap, labels, rounding, n_book)
    return assemble_book_rb(src, name, item, same, rec, diff, idok)


# ---- 集計(門が記録の ``本`` から作り直して照らす)
def aggregate(books):
    u"""``本`` の列 → 集計。全体と形別・model 別。"""
    def block(bs):
        def s(fn):
            return sum(fn(b) for b in bs)
        g29, g30 = s(lambda b: b[u"GROUNDED の数"]["P29E"]), s(lambda b: b[u"GROUNDED の数"]["P30E"])
        lab = collections.OrderedDict((w, s(lambda b, w=w: b[u"GROUNDED になった既存の行の札"][w])) for w in LABEL_WORDS + (NO_LABEL,))
        dirs = collections.Counter()
        for b in bs:
            dirs.update(b[u"動いた行の向き別"])
        k2 = [x for b in bs for x in b[u"K-2 の行"]]
        lost_n = [x for x in k2 if x[3] == "GROUNDED" and x[4] != "GROUNDED"]
        return collections.OrderedDict([
            (u"本", len(bs)),
            (u"D-1 旗が偽の byte 一致", collections.OrderedDict([(u"一致した本", sum(1 for b in bs if b[u"旗が偽の byte 一致"][u"一致"])), (u"本", len(bs))])),
            (u"D-2 GROUNDED の数(数の claim)", collections.OrderedDict([("P29E", g29), ("P30E", g30), (u"差", g30 - g29)])),
            (u"数の claim の数", collections.OrderedDict((p, s(lambda b, p=p: b[u"数の claim の数"][p])) for p in PROFILES)),
            (u"D-3 P29E で GROUNDED・P30E で GROUNDED でない行", s(lambda b: b[u"GROUNDED を失った行"])),
            (u"D-4 GROUNDED になった既存の行の札", collections.OrderedDict(list(lab.items()) + [(u"合計", sum(lab.values()))])),
            (u"GROUNDED になった新しい行", s(lambda b: b[u"GROUNDED になった新しい行"])),
            (u"動いた行", collections.OrderedDict([(u"動いた行", s(lambda b: b[u"動いた行"])), (u"state が変わった行", s(lambda b: b[u"state が変わった行"])),
                                                  (u"向き別", collections.OrderedDict(sorted(dirs.items())))])),
            (u"D-5 N の便の K-2 の行", collections.OrderedDict([
                (u"行", len(k2)), (u"うち N の便で GROUNDED を失った行", len(lost_n)),
                (u"うち P30E で GROUNDED", sum(1 for x in lost_n if x[6] == "GROUNDED")),
                (u"P30E で GROUNDED", sum(1 for x in k2 if x[6] == "GROUNDED"))])),
            (u"D-6 混ざる桁がある本", collections.OrderedDict([(u"本", sum(1 for b in bs if b[u"混ざる桁"])), (u"混ざる桁の延べ数", s(lambda b: len(b[u"混ざる桁"] or [])))])),
            (u"対応が付かなかった本", sum(1 for b in bs if not all(b[u"対応"].values()))),
            (u"P29E と P30E で鍵が違う本", sum(1 for b in bs if not b[u"P29E と P30E で数の claim の鍵が同じ"])),
            (u"P27 の鍵が一意でない本", sum(1 for b in bs if not b[u"P27 の鍵が一意"]))])
    out = collections.OrderedDict([(u"全体", block(books))])
    out[u"形別"] = collections.OrderedDict((f, block([b for b in books if b[u"form"] == f])) for f in sorted(set(b[u"form"] for b in books)))
    out[u"model 別"] = collections.OrderedDict((m, block([b for b in books if b[u"model"] == m])) for m in sorted(set(b[u"model"] for b in books)))
    return out


def run_judge(root=ROOT, procs=1, only=None, out=None, key_value=None, say=print):
    out = out or os.path.join(root, AI200_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    if tuple(RUN.PROFILES) != NF.PREV_PROFILES:
        raise Stop(u"**RUN.PROFILES が前の便の 4 つでない(旗が偽の byte 一致を測れない)。止める**")
    bad = wiring_problems()
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    seed, seed_meta = GEN.seed_value(root)
    jobs_ = load_jobs(root, only)
    caches = caches_all()
    before = GEN.caches_snapshot(caches)
    say(u"判定 %d 本 × 3 profile(P28E・P29E・P30E)+ 旗が偽の byte 一致 ― procs %d" % (len(jobs_), procs))
    recs = NF.map_pool(judge_book_rb, jobs_, procs)
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = NF.header(root, u"RB(丸め方の根拠が混ざる桁)― AI の文 200 本の判定(P28E・P29E・P30E。0 USD)", seed_meta, before, after, PROFILES)
    rec[u"欄"] = collections.OrderedDict([
        (u"数の claim の鍵", u"(文の番号, 文の中の位置)。id は profile 間で替わるので使わない"),
        (u"札", u"前の便の盲検の 1 席目の札(labels・f5_labels)。鍵 → id は P27 の raw claim の並び(RUN.judge_text の行の index)で結ぶ。札のある行 = P28E にも在る行。新しい行には札が無い"),
        (u"動いた行", u"P29E と P30E の両方にある鍵のうち (state, reason, pointers) が違う行"),
        (u"state が変わった行の中身", u"[種類, 文の番号, 位置, P29E の state, P30E の state, 札 or null, 既存 / 新]。文・span・値は持たない"),
        (u"K-2 の行", u"N の便の ai200 の 同じ文に新しい行が無いのに変わった既存の行 に P30E の state を足した [種類, 文の番号, 位置, N の便の P28E の state, N の便の P29E の state, 今回の P29E の state, P30E の state]"),
        (u"混ざる桁", u"build_raw_claims(zm, P30E, info) の info の混ざる桁の欄(RB の旗の名前の欄)。昇順の列(桁 claim_scale)"),
        (u"旗が偽の byte 一致", u"RUN.judge_text(P27・P27E・P28・P28E) の 行・4 state・claim の数 が前の便の記録の同じ name の欄と等しい(JSON に通して比べた)。"
                           u"P29E が N の便の記録と一致 = P29E の行から NF.analyse_book で作り直した欄が N の便の ai200 の同じ本の欄と等しい")])
    rec[u"入力の記録の sha256"] = collections.OrderedDict(
        [(u"%s_%s" % (src, k), GEN.sha256_file(os.path.join(root, p[k]))) for src, p in SOURCES.items() for k in ("gen", "claims")] +
        [(u"%s_labels" % src, GEN.sha256_file(os.path.join(root, rel))) for src, rel in LABELS_REL.items()])
    rec[u"本"] = recs
    rec[u"集計"] = aggregate(recs)
    rec[u"repo の外に置いたもの"] = u"なし(この便は何も書かない。文は前の便の folder から読むだけ)"
    write_json(out, rec, key_value)
    say(u"-> %s(本 %d)" % (out, len(recs)))
    return rec


# ======================================================================================================
# inject(土台 = P30E が GROUNDED の claim。比較 = P29E)
def base_status_rb(base_claims, base_by_id, tok, text):
    u"""(状態, 土台)。土台 = 無改変の文で **P30E が GROUNDED** の claim。P30E の claim を ``find_base_claim`` で 1 件に決め、P29E の claim は (value, span, unit) が同じ 1 件があれば結ぶ
    (id は profile 間で同じはずだが、N の便と同じ作りで値と span で結ぶ)。無ければ ``ids`` の P29E を None にする(その行の P29E の欄は『対応なし』)。"""
    p0, p1 = INJECT_PROFILES
    digits = text[tok.start:tok.end]
    bc = TUNE.find_base_claim(base_claims[p1], tok.value, digits, tok.unit)
    if bc is None:
        return u"基準に対応が付かない", None
    if bc["state"] != "GROUNDED":
        return u"P30E が GROUNDED でない", None
    key = (bc["value"], bc["span"], bc["unit"])
    twin = [c for c in base_claims[p0] if (c["value"], c["span"], c["unit"]) == key]
    out = dict(bc)
    out["ids"] = {p0: twin[0]["id"] if len(twin) == 1 else None, p1: bc["id"]}
    return (LINKED if len(twin) == 1 else UNLINKED), out


def inject_text_rb(zb, text, refs, seed, key, cap=RUN.INJECT_CAP, verify=None):
    u"""``RUN.inject_text`` と同じ手順(1 回に 1 件・round-trip を確かめる)。土台は P30E が GROUNDED の claim。行の判定の引きは profile ごとの id で、P29E の claim が無い行の P29E の欄は『対応なし』(判定しない)。"""
    if RUN.N.normalize_digits(text) != text:
        return [], {u"注入しない": u"文に全角の数字がある(select は半角の文を前提にする)"}
    verify = verify or VD.verify_document
    profiles = tuple(RUN.PROFILES)
    base_claims = dict((p, verify(zb, p, text)["claims"]) for p in profiles)
    base_by_id = dict((p, dict((c["id"], c) for c in base_claims[p])) for p in profiles)
    toks = dict(((t.start, t.end), t) for t in RUN.N.scan(text))
    counts, work_list = {}, []
    chosen, cat, _a, _w = IJ.select(text, refs, "xbrl", seed, key, cap, types=["T1_VALUE"])
    c1 = collections.Counter()
    c1[u"作れる site"], c1[u"採った"] = cat["T1_VALUE"], len(chosen)
    for inj in chosen:
        tok = toks[tuple(inj["span"])]
        status, bc = RUN.base_status4(base_claims, base_by_id, tok, text)
        c1[status] += 1
        work_list.append((inj, tok, bc))
    counts["T1_VALUE"] = dict(c1)
    t8, c8 = RUN.t8_candidates4(text, refs, base_claims, base_by_id, seed, key, cap)
    counts["T8_REL"] = dict(c8)
    work_list += t8
    rows = []
    for inj, tok, bc in work_list:
        tampered, placements = IJ.apply_edits(text, [inj])
        if IJ.revert(tampered, [inj], placements, text) != text:
            raise Stop(u"**round-trip が合わない: %s。止める**" % inj["id"])
        if bc is None:
            continue
        row = collections.OrderedDict([("id", inj["id"]), (u"型", inj["type"]), (u"基準の claim", bc["id"]), (LINK_KEY, bc["ids"][profiles[0]] is not None)])
        if inj["type"] == "T8_REL":
            row["r"], row[u"r を決めた回"] = inj["detail"]["relative"], inj["detail"]["tries"]
        for p in profiles:
            if bc["ids"][p] is None:
                row[p] = TUNE.classify(None, None)                       # 土台に対応する claim が無い = 対応なし
                continue
            res = TUNE.claim_for_p27(verify(zb, p, tampered)["claims"], inj, tok.unit)
            row[p] = TUNE.classify(res, base_by_id[p][bc["ids"][p]])
        rows.append(row)
    return rows, counts


def inject_summaries(rows):
    u"""(集計 = 土台の全 site, 比較用 = P29E の claim にも対応が付く site だけ)。RUN.PROFILES が (P29E, P30E) のときに呼ぶ。"""
    return RUN.inject_summary(rows), RUN.inject_summary([r for r in rows if r[LINK_KEY]])


def unlinked_counts(rows):
    out = collections.OrderedDict([(u"全体", sum(1 for r in rows if not r[LINK_KEY]))])
    for t in RUN.INJECT_TYPES:
        out[t] = sum(1 for r in rows if r[u"型"] == t and not r[LINK_KEY])
    return out


def inject_job_rb(args):
    src, name, item, row, text_dir, zip_caches, seed, work_root = args
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    refs = RUN.refs_for(row, zip_caches, work_root)
    rows, counts = inject_text_rb(zb, text, refs, seed, name)
    base = {u"docID": item[u"docID"], u"form": item[u"form"], u"model": item[u"model"], u"writer": item[u"writer"]}
    return name, [collections.OrderedDict(list(base.items()) + list(r.items())) for r in rows], counts


def install_inject():
    u"""注入の入れ替え(inject の command のときだけ)。RUN.PROFILES と土台の判定を差し替える(使う側の ``RUN.t8_candidates4`` が引く名前 ``base_status4`` に届く)。"""
    RUN.PROFILES = INJECT_PROFILES
    RUN.base_status4 = base_status_rb


def inject_wiring_problems():
    out = list(wiring_problems())
    if tuple(RUN.PROFILES) != INJECT_PROFILES:
        out.append(u"RUN.PROFILES が (P29E, P30E) でない")
    if RUN.base_status4 is not base_status_rb:
        out.append(u"RUN.base_status4 が差し替えた先でない")
    if RUN.t8_candidates4.__globals__["base_status4"] is not base_status_rb:
        out.append(u"使う側 RUN.t8_candidates4 が引く base_status4 が差し替えた先でない")
    return out


def run_inject(root=ROOT, procs=1, only=None, out=None, key_value=None, say=print, work_root=None):
    out = out or os.path.join(root, INJECT_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    install_inject()
    bad = inject_wiring_problems()
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    seed, seed_meta = GEN.seed_value(root)
    books = NF.load_books(root, only)
    caches = caches_all()
    before = GEN.caches_snapshot(caches)
    work_root = work_root or tempfile.mkdtemp(prefix="rmix_inject_", dir=os.environ.get("TMPDIR"))
    jobs_ = [(src, n, item, row, SOURCES[src]["cache"], GEN.EXISTING_CACHES, seed, work_root) for (src, n, item, row, _prior) in books]
    say(u"注入 %d 本 × 2 profile(P29E・P30E)― procs %d(1 件ごとに判定。時間がかかる)" % (len(jobs_), procs))
    results = NF.map_pool(inject_job_rb, jobs_, procs)
    rows, per = [], collections.OrderedDict()
    for n, r, c in results:
        rows += r
        per[n] = c
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = NF.header(root, u"RB(丸め方の根拠が混ざる桁)― 注入(P29E・P30E の T1_VALUE・T8_REL。0 USD)", seed_meta, before, after, INJECT_PROFILES)
    rec[u"種"] = {u"file": RUN.SEED_REL_STR, u"種の確認": seed_meta}
    rec[u"型"] = collections.OrderedDict([
        ("T1_VALUE", u"inject.select(types=[T1_VALUE]) のまま。cap は採用に掛ける(基準で絞る前)"),
        ("T8_REL", u"円の単位族の token・r ∈ %s・%d 回まで。cap は site に掛ける" % (list(TUNE.T8_R_VALUES), TUNE.T8_TRIES)),
        (u"上限", u"型ごと・1 本あたり %d" % RUN.INJECT_CAP),
        (u"土台", BASE_WORD),
        (u"土台の結び方", u"P30E の claim を find_base_claim で 1 件に決め、P29E の claim は (value, span, unit) が同じ 1 件があれば結ぶ。無ければその行の P29E の欄は対応なし(判定しない)"),
        (u"集計の2本", u"集計 = 土台の全 site での P29E・P30E の率(D-8・D-9 は P30E のこちら)。" + COMPARE_KEY + u" = そのうち P29E の claim にも対応が付く site だけでの P29E と P30E の率(比較用)"),
        (u"inject.select の docID の引数", u"本の名前(<docID>_<形>_<model>)")])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"], rec[COMPARE_KEY] = inject_summaries(rows)
    rec[u"P29E に対応なしの行の数"] = unlinked_counts(rows)
    rec[u"行"] = rows
    rec[u"限界"] = [u"注入は 2 型だけ(値・相対のずれ)。期・単位・主語の取り違えは注入しない", u"T8_REL の r の 4 値は前例の決め打ち", LIMIT_SCAN,
                  u"土台は P30E が GROUNDED の claim。P29E の claim に結べない site の行は P29E の欄が対応なし(P29E との比較は " + COMPARE_KEY + u" の site だけ)"]
    write_json(out, rec, key_value, text=RUN.dumps_inject(rec))
    say(u"-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
# tally: 封の表(§3 の D-1〜D-10・§4 の K-1〜K-5)を読み、記録 3 つから判定する
def read_seal(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def seal_pred_rows(seal):
    u"""封 §3 の表の行 {D-n: (欄, 予測, 外れ方)}。"""
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| (D-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            out[m.group(1)] = (cells[0], cells[1], cells[2] if len(cells) > 2 else u"")
    return out


pair_of = NF.pair_of
within = NF.within


def seal_bounds(seal):
    u"""封の字から予測の幅と採用の基準の閾値を読む(字のコピーにしない)。{名前: 値}。"""
    P = seal_pred_rows(seal)
    b = collections.OrderedDict()
    m = re.match(r"(\d+) / (\d+)・(\d+) / (\d+) × (\d+)$", P["D-1"][1])
    b["D-1"] = tuple(int(x) for x in m.groups())
    b["D-2"] = pair_of(P["D-2"][1])
    b["D-3"] = int(re.match(r"(\d+)$", P["D-3"][1]).group(1))
    t = re.match(r"真 (\d+)〜(\d+)・偽 (\d+)〜(\d+)", P["D-4"][1])
    b["D-4"] = collections.OrderedDict([(u"真", (float(t.group(1)), float(t.group(2)))), (u"偽", (float(t.group(3)), float(t.group(4))))])
    m = re.match(r"(\d+) / (\d+)$", P["D-5"][1])
    b["D-5"] = (int(m.group(1)), int(m.group(2)))
    b["D-6"] = pair_of(P["D-6"][1])
    m = re.match(r"(\d+)〜(\d+) / (\d+)", P["D-7"][1])
    b["D-7"] = collections.OrderedDict([(u"動いた行", (float(m.group(1)), float(m.group(2)))), (u"失う行", int(m.group(3)))])
    t1 = re.search(r"T1 (\d+(?:\.\d+)?)〜(\d+(?:\.\d+)?)%", P["D-8"][1])
    t8 = re.search(r"T8 (\d+(?:\.\d+)?)〜(\d+(?:\.\d+)?)%", P["D-8"][1])
    b["D-8"] = collections.OrderedDict([("T1_VALUE", (float(t1.group(1)), float(t1.group(2)))), ("T8_REL", (float(t8.group(1)), float(t8.group(2))))])
    b["D-9"] = pair_of(P["D-9"][1])
    b["D-10"] = pair_of(P["D-10"][1])
    sec4 = seal[seal.index("## §4"):seal.index("## §5")]
    b["K-2"] = int(re.search(r"\*\*K-2\*\*\s*D-3 = (\d+)", sec4).group(1))
    m = re.search(r"\*\*K-3\*\*\s*D-4 の札 偽 ≤ (\d+) かつ札 真 ≥ (\d+)", sec4)
    b["K-3"] = collections.OrderedDict([(u"偽", float(m.group(1))), (u"真", float(m.group(2)))])
    m = re.search(r"\*\*K-4\*\*\s*D-8 の T1_VALUE ≤ (\d+(?:\.\d+)?)% かつ T8_REL ≤ (\d+(?:\.\d+)?)%", sec4)
    b["K-4"] = collections.OrderedDict([("T1_VALUE", float(m.group(1))), ("T8_REL", float(m.group(2)))])
    m = re.search(r"\*\*K-5\*\*\s*D-7 の失う行 = (\d+) かつ動いた行 ≤ (\d+)", sec4)
    b["K-5"] = collections.OrderedDict([(u"失う行", int(m.group(1))), (u"動いた行", float(m.group(2)))])
    return b


def inj_rate(rec, t, p, key, summary=u"集計"):
    return rec[summary][t][p][u"全体"][key][u"率"]


def build_J(R_, seal):
    u"""{D: {D-n: {判定, 値}}, K: ..., 採用}。R_ = {"ai200", "inject", "regress97"}(記録の JSON)。"""
    B = seal_bounds(seal)
    P = seal_pred_rows(seal)
    A = R_["ai200"][u"集計"][u"全体"]
    r97 = R_["regress97"][u"集計"]
    inj = R_["inject"]
    J = collections.OrderedDict()

    def put(k, ok, val):
        J[k] = {u"判定": HIT if ok else MISS, u"値": val}
    d1 = A[u"D-1 旗が偽の byte 一致"]
    c = r97[u"D-1 旗が偽の profile の byte 一致"]
    cn = collections.OrderedDict((p, v[u"byte が同じ書類"]) for p, v in c.items())
    cd = set(v[u"書類"] for v in c.values())
    ok1 = (d1[u"一致した本"], d1[u"本"]) == (B["D-1"][0], B["D-1"][1]) and len(c) == B["D-1"][4] and cd == {B["D-1"][3]} and all(n == B["D-1"][2] for n in cn.values())
    put("D-1", ok1, collections.OrderedDict([(u"AI 一致した本", d1[u"一致した本"]), (u"本", d1[u"本"]), (u"97 byte が同じ書類(profile 間の最小)", min(cn.values()) if cn else None),
                                           (u"書類", B["D-1"][3]), (u"profile", len(c))]))
    d2 = A[u"D-2 GROUNDED の数(数の claim)"]
    put("D-2", within(d2[u"差"], B["D-2"]), collections.OrderedDict([("P29E", d2["P29E"]), ("P30E", d2["P30E"]), (u"差", d2[u"差"])]))
    d3 = A[u"D-3 P29E で GROUNDED・P30E で GROUNDED でない行"]
    put("D-3", d3 == B["D-3"], d3)
    d4 = A[u"D-4 GROUNDED になった既存の行の札"]
    put("D-4", within(d4[u"真"], B["D-4"][u"真"]) and within(d4[u"偽"], B["D-4"][u"偽"]),
        collections.OrderedDict([(u"真", d4[u"真"]), (u"偽", d4[u"偽"]), (u"判定不能", d4[u"判定不能"]), (u"札なし", d4[NO_LABEL])]))
    d5 = A[u"D-5 N の便の K-2 の行"]
    put("D-5", (d5[u"うち P30E で GROUNDED"], d5[u"うち N の便で GROUNDED を失った行"]) == B["D-5"],
        collections.OrderedDict([(u"N の便で GROUNDED を失った行", d5[u"うち N の便で GROUNDED を失った行"]), (u"うち P30E で GROUNDED", d5[u"うち P30E で GROUNDED"])]))
    d6 = A[u"D-6 混ざる桁がある本"]
    put("D-6", within(d6[u"本"], B["D-6"]), collections.OrderedDict([(u"本", d6[u"本"])]))
    d7 = r97[u"D-7 P30E 対 P29E"]
    put("D-7", within(d7[u"動いた既存の行"], B["D-7"][u"動いた行"]) and d7[u"GROUNDED を失う行"] == B["D-7"][u"失う行"],
        collections.OrderedDict([(u"動いた行", d7[u"動いた既存の行"]), (u"失う行", d7[u"GROUNDED を失う行"])]))
    t1, t8 = inj_rate(inj, "T1_VALUE", "P30E", u"通した"), inj_rate(inj, "T8_REL", "P30E", u"通した")
    put("D-8", within(t1, B["D-8"]["T1_VALUE"]) and within(t8, B["D-8"]["T8_REL"]),
        collections.OrderedDict([(u"T1_VALUE 通した率 P30E", t1), (u"T8_REL 通した率 P30E", t8),
                                 (u"T1_VALUE 通した率 P29E(比較用)", inj_rate(inj, "T1_VALUE", "P29E", u"通した", COMPARE_KEY)),
                                 (u"T8_REL 通した率 P29E(比較用)", inj_rate(inj, "T8_REL", "P29E", u"通した", COMPARE_KEY))]))
    o30 = inj_rate(inj, "T8_REL", "P30E", u"名指して原本の値を返した")
    put("D-9", within(o30, B["D-9"]), collections.OrderedDict([(u"T8_REL 名指して原本 P30E", o30), (u"P29E(比較用)", inj_rate(inj, "T8_REL", "P29E", u"名指して原本の値を返した", COMPARE_KEY))]))
    d10 = r97[u"D-10 engine の留めの連動で直す試験 file"]
    put("D-10", within(d10[u"直した file(M)"], B["D-10"]),
        collections.OrderedDict([(u"直した file(M)", d10[u"直した file(M)"]), (u"新しい file(A)", d10[u"新しい file(A)"]), (u"engine の挿入の行数", d10[u"engine の挿入の行数"])]))
    K = collections.OrderedDict()
    K["K-1"] = {u"判定": J["D-1"][u"判定"], u"値": collections.OrderedDict([("D-1", J["D-1"][u"判定"])])}
    K["K-2"] = {u"判定": HIT if d3 == B["K-2"] else MISS, u"値": collections.OrderedDict([(u"P29E で GROUNDED・P30E で GROUNDED でない行", d3)])}
    K["K-3"] = {u"判定": HIT if d4[u"偽"] <= B["K-3"][u"偽"] and d4[u"真"] >= B["K-3"][u"真"] else MISS,
                u"値": collections.OrderedDict([(u"札 偽", d4[u"偽"]), (u"札 真", d4[u"真"])])}
    k4 = t1 is not None and t8 is not None and t1 <= B["K-4"]["T1_VALUE"] and t8 <= B["K-4"]["T8_REL"]
    K["K-4"] = {u"判定": HIT if k4 else MISS, u"値": collections.OrderedDict([(u"T1_VALUE", t1), (u"T8_REL", t8)])}
    k5 = d7[u"GROUNDED を失う行"] == B["K-5"][u"失う行"] and d7[u"動いた既存の行"] <= B["K-5"][u"動いた行"]
    K["K-5"] = {u"判定": HIT if k5 else MISS, u"値": collections.OrderedDict([(u"失う行", d7[u"GROUNDED を失う行"]), (u"動いた行", d7[u"動いた既存の行"])])}
    adopt = all(K[k][u"判定"] == HIT for k in K)
    return collections.OrderedDict([(u"D", J), (u"K", K), (u"採用", adopt), (u"欄", collections.OrderedDict((k, v[0]) for k, v in P.items()))])


def fmt(v):
    if isinstance(v, bool):
        return u"はい" if v else u"いいえ"
    if isinstance(v, float):
        return (u"%.1f" % v)
    if isinstance(v, int):
        return format(v, ",")
    if isinstance(v, dict):
        return u"・".join(u"%s %s" % (k, fmt(x)) for k, x in v.items())
    return u"%s" % (v,)


pred_cell = NF.pred_cell


def render_pred(J, seal=None):
    seal = seal if seal is not None else read_seal()
    P = seal_pred_rows(seal)
    lines = [u"| # | 欄 | 予測 | 測った値 | 判定 |", u"|---|---|---|---|---|"]
    for k, v in J[u"D"].items():
        lines.append(u"| %s | %s | %s | %s | %s |" % (k, P[k][0], pred_cell(P[k][1]), fmt(v[u"値"]), v[u"判定"]))
    return u"\n".join(lines)


def render_judge(J, seal=None):
    seal = seal if seal is not None else read_seal()
    sec4 = seal[seal.index("## §4"):seal.index("## §5")]
    names = collections.OrderedDict()
    for m in re.finditer(r"^- \*\*(K-\d)[^*]*\*\*:?\s*(.*)$", sec4, re.M):
        names[m.group(1)] = m.group(2)
    lines = [u"| # | 基準 | 測った値 | 判定 |", u"|---|---|---|---|"]
    for k, v in J[u"K"].items():
        lines.append(u"| %s | %s | %s | %s |" % (k, pred_cell(names[k]), fmt(v[u"値"]), v[u"判定"]))
    lines.append(u"")
    lines.append(u"採用の判定(K-1〜K-5 を全部満たす): **%s**。最後に決めるのは人間。" % (u"採用" if J[u"採用"] else u"採用しない(人間に返す)"))
    return u"\n".join(lines)


def load_records(root=ROOT):
    return collections.OrderedDict((k, GEN.jload(os.path.join(root, v))) for k, v in REC_REL.items())


def run_tally(root=ROOT, say=print):
    seal = read_seal(root)
    J = build_J(load_records(root), seal)
    say(render_pred(J, seal))
    say(u"")
    say(render_judge(J, seal))
    return J


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("judge", "inject", "tally"))
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", default=None, help="judge・inject: この docID の本だけ")
    ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args(argv)
    if a.cmd == "judge":
        run_judge(root=a.root, procs=a.procs, only=a.only, out=a.out)
    elif a.cmd == "inject":
        run_inject(root=a.root, procs=a.procs, only=a.only, out=a.out)
    else:
        run_tally(root=a.root)


if __name__ == "__main__":
    main()
