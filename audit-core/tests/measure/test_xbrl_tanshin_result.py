# -*- coding: utf-8 -*-
"""TS(人が書いた有報の外の文 = 決算短信「経営成績等の概況」17 社で engine を測る)の測定の結果の門。封 docs/XBRL_TANSHIN_HUMAN_TEXT_SEAL_2026-11-09.md §2・§3・§5。

記録 3 つ(``fixtures/xbrl/tanshin/{fetched,states,inject}_2026-11-09.json``)から、封 §3 の予測 H-1〜H-9 を**機械で求め**(予測の幅は封の字から読む。字のコピーにしない)、
結果の文書 ``docs/XBRL_TANSHIN_HUMAN_TEXT_RESULT_2026-11-09.md`` の表(``<!-- 門:start pred -->``・``<!-- 門:start states -->`` の中)を記録から作り直した表と一行も違わないことを見る。
**H-10(司令塔が VALUE_MISMATCH の全行を読んだ型)は門なし = 判定しない**(表に「司令塔が読む」と出る)。縛るもの:

  a  取得の記録: 17 行が封 §1 の表と一致(証券コード・番号・sha256)・docID が 1 対 1・HTTP の状態・cache の前後が同じ・key_leaks が空・script の sha256 が現物と一致。
  b  states の記録: header(封・commit・script と前の便の script の sha256・engine の指紋が今の engine の束ねた値・lib と仕掛けの sha256・profile・cache の前後)・
     **行から数え直した集計**(claim・4 state・reason・VALUE_MISMATCH の内訳・動いた行・H の欄の全部。欄を 0 に固定すると赤。行の state を 1 つ変えると該当の欄が動く)・行の形。
  c  inject の記録: header・切り替え 2 つの欄・cap(型ごと 1 本あたり 10 を超えない)・行の欄(対応の 3 条件と欠けた条件・id の形・型・形)・本ごとの数えと行の整合・集計と H の欄の数え直し。
  d  判定: 記録(の欄)を 1 つ変えると判定が変わる。境界の値(幅の端と端の外)で当たり ↔ 外れが替わる。分母 0 は外れ。H-10 は判定しない。**予測の幅は封の字から読み、門に literal で留めた値と照らす**。
  e  文書の表 = 記録から作り直した表。禁止語なし。docID なし。散文の 3 桁以上の数には【門なし】。
  f  順序: 封 5bba61e ⊏ 記録・結果の文書(script・門の順序は封の門が見る)。未 commit は赤(skip にしない)。
  g  変異: 小さい標本の記録と文書で同じ検査が緑 → 変異(記録の数・state・禁止欄・指紋・cache の前後・切り替え・cap・封の予測の 1 字)で赤。
  w  手順・行の欄: script の ``inject_text_ts`` を小さい入力(zip・判定は偽。lib は本物)で通し、4 型 × 2 profile の行・欄・cap・id が壊した差し替えで動く例で固定する。states の部品(単位の族・a−b・行の形)も同じ。

記録が無いときは (a)(b)(c)(e)(f) の本番の記録の試験を skip する(skip でも行が出ることを試験が確かめる)。標本の試験 (d)(g)(w) は記録が無くても走る。この file は docID の字を持たない。
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
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "measure"))


def load_module(rel, name):
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


SG = load_module("tests/measure/test_xbrl_tanshin_seal.py", "tanshin_seal_gate_for_result")        # 封の門の部品(封の表の読み・順序)。門としては走らせない
PSR = load_module("tests/measure/test_xbrl_pswap_result.py", "pswap_result_gate_for_tanshin_result")   # 標本の文・refs・偽の verify。門としては走らせない
PR = SG.PR
TS = SG.TS
FE = SG.FE
TY = TS.TY
PI, PS, NS = TS.PI, TS.PS, TS.NS
RUN, GEN, TUNE, IJ, S, N, VD, V = TS.RUN, TS.GEN, TS.TUNE, TS.IJ, TS.S, TS.N, TS.VD, TS.V

SEAL_REL = TS.SEAL_REL
DOC_REL = TS.DOC_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
REC_REL = collections.OrderedDict(TS.REC_REL)
NOT_GATED = PR.NOT_GATED
DOCID_RE = SG.DOCID_RE
STATES = TS.STATES
G, VM, UNV, PNF = STATES
TYPES = TS.TYPES
PERIODS5 = TS.PERIODS5
FAMILIES = (u"%", u"円族", u"他")
CAP = 10                                                    # 封の決め(型ごと 1 本あたり。RUN.INJECT_CAP と同じでなければ赤)
FORBIDDEN_KEYS = tuple(RUN.FORBIDDEN_KEYS) + (u"pointers", u"pointer", u"要素", u"element", u"context", u"label", u"会社名", u"subject")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
POINTER_TEXT_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:")
FOR_RESULT_WORDS = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")
HAVE_CACHE = all(os.path.isdir(p) for p in TS.caches_all().values())
Patch = PSR.Patch
norm = PSR.norm
walk = PSR.walk
walk_strings = PSR.walk_strings
#: 封 §3 の予測の幅(封の字を門が読み、ここに留めた値と照らす。留めた値が封の字と違えば赤)。単独の数は 1 つの値の列・幅は (下, 上) の列
BOUNDS_PIN = collections.OrderedDict([
    ("H-1", [17.0, 17.0]), ("H-2", [84378.0, 1283.0]), ("H-3", [541.0, 110.0, 344.0, 288.0]),
    ("H-4", [(85.0, 105.0), (0.0, 15.0)]), ("H-5", [26.0, 61.0, 19.0]),
    ("H-6", [(0.0, 5.0), (0.0, 5.0), (0.0, 5.0), (5.0, 30.0), (40.0, 200.0)]),
    ("H-7", [96.0, 110.0]), ("H-8", [158.0, 101.0]), ("H-9", [0.0]), ("H-10", None)])
FORCE = {"no_records": False}                  # 試験が『記録が無い』状態を作るための旗(SkipLineTest だけが立てる)
SEAL_TABLE = None


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha256_rel(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def records_exist():
    if FORCE["no_records"]:
        return False
    return all(os.path.exists(os.path.join(ROOT, v)) for v in REC_REL.values())


def load_records():
    return collections.OrderedDict((k, json.loads(read(v))) for k, v in REC_REL.items())


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def seal_table():
    return SG.seal_table(read(SEAL_REL))


# ---------------------------------------------------------------- d. 予測の幅(封の字から読んだ値 = 留めた値)
def bounds_problems(seal):
    out = []
    got = TS.seal_bounds(seal)
    if list(got) != list(BOUNDS_PIN):
        return [u"封から読んだ H の列が H-1〜H-10 でない"]
    for k, want in BOUNDS_PIN.items():
        g = got[k]
        if want is None:
            if g is not None:
                out.append(u"%s は門なし(幅を持たない)" % k)
        elif [tuple(x) if isinstance(x, (tuple, list)) else x for x in g] != [tuple(x) if isinstance(x, (tuple, list)) else x for x in want]:
            out.append(u"%s の幅が留めた値と違う: %s" % (k, g))
    return out


# ---------------------------------------------------------------- 独立の数え直し(script の関数を使わない)
def recount(fetch, states, inject):
    u"""H-1〜H-9 の実測の値を、記録の行だけから数え直す(script の ``states_columns``・``inject_columns`` を使わない)。"""
    tab = dict((r[1], r) for r in seal_table())
    h1 = sum(1 for r in fetch[u"行"] if r[u"証券コード"] in tab and tab[r[u"証券コード"]][2] == r[u"番号"] and tab[r[u"証券コード"]][3] == r[u"ZIP の sha256"])
    books = states[u"本"]
    p32 = [row for b in books for row in b[u"profile"][u"P32E"][u"行"]]
    p27 = [row for b in books for row in b[u"profile"][u"P27"][u"行"]]
    cnt = collections.Counter(r[2] for r in p32)
    g27, g32 = sum(1 for r in p27 if r[2] == G), cnt[G]
    vm = [r for r in p32 if r[2] == VM]
    unv = collections.Counter(r[3] for r in p32 if r[2] == UNV)
    pnf = collections.Counter(r[3] for r in p32 if r[2] == PNF)
    rows = inject[u"行"]

    def rate(t):
        sel = [r for r in rows if r[u"型"] == t]
        return pct(sum(1 for r in sel if r[u"P32E"][u"結果"] == TUNE.LABEL_PASS), len(sel))
    return collections.OrderedDict([
        ("H-1", (h1, len(fetch[u"行"]))),
        ("H-2", (sum(b[u"概況の字数"] for b in books), len(p32))),
        ("H-3", (cnt[G], cnt[VM], cnt[UNV], cnt[PNF])),
        ("H-4", (pct(g27, g32), sum(len(b[u"P30E から P32E で動いた行"]) for b in books))),
        ("H-5", (sum(1 for r in vm if r[5]), sum(1 for r in vm if r[8]), sum(1 for r in vm if r[7]))),
        ("H-6", tuple(rate(t) for t in TYPES) + (sum(1 for r in rows if r[u"型"] == TYPES[3]),)),
        ("H-7", (unv[u"target_or_plan"], unv[u"no_subject"])),
        ("H-8", (pnf[u"no_element"], pnf[u"no_same_value"])),
        ("H-9", (sum(b[u"行頭が | の文の数"] for b in books),))])


def expected_judge(cols):
    u"""封の幅(門に留めた値)から判定を独立に求める。"""
    out = collections.OrderedDict()
    for k, want in BOUNDS_PIN.items():
        v = cols.get(k)
        if want is None:
            out[k] = u"司令塔が読む"
        elif any(isinstance(x, tuple) for x in want):
            ok = v is not None and len(v) == len(want) and all(x is not None and lo <= x <= hi for x, (lo, hi) in zip(v, want))
            out[k] = u"当たり" if ok else u"外れ"
        else:
            ok = v is not None and len(v) == len(want) and all(x is not None and abs(x - w) < 1e-9 for x, w in zip(v, want))
            out[k] = u"当たり" if ok else u"外れ"
    return out


# ---------------------------------------------------------------- a・b・c. 記録の検査
def clean_problems(rec):
    out = []
    bad = sorted(set(x for x in walk(rec) if x in FORBIDDEN_KEYS))
    if bad:
        out.append(u"記録に repo へ入れない欄がある: %s" % u",".join(bad))
    text = json.dumps(rec, ensure_ascii=False)
    for w in COMPANY_WORDS:
        if w in text:
            out.append(u"会社名らしい字がある")
    if any(POINTER_TEXT_RE.search(s) for s in walk_strings(rec)):
        out.append(u"記録に pointer の字(要素名・context・式)がある")
    try:
        with TS.key_check_ts():
            RUN.assert_clean(copy.deepcopy(rec))
    except GEN.Stop:
        out.append(u"鍵らしい字が記録に在る")
    if rec.get(u"key_leaks", []) != []:
        out.append(u"key_leaks が空でない")
    return out


def cache_problems(rec):
    c = rec.get(u"cache の前後") or {}
    return [] if c and c.get(u"前") == c.get(u"後") and c.get(u"変化なし") is True and c.get(u"前") else [u"cache の前後が同じでない"]


def common_header_problems(rec, full, fetch_rec_exists):
    out = []
    if rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"封の path・commit が違う")
    if rec.get(u"この script の sha256") != sha256_rel(TS.SCRIPT_REL):
        out.append(u"script の sha256 が現物と違う(記録を作ったあとに script を変えた)")
    if rec.get(u"取得の script の sha256") != sha256_rel(TS.FETCH_SCRIPT_REL):
        out.append(u"取得の script の sha256 が現物と違う")
    if rec.get(u"前の便の script の sha256") != dict((rel, sha256_rel(rel)) for rel in TS.PREV_SCRIPT_RELS):
        out.append(u"前の便の script の sha256 が現物と違う")
    fp, now = rec.get(u"engine の指紋") or {}, VD.engine_fingerprint()
    if fp.get(u"adapter_xbrl_py_sha256") != now["adapter_xbrl_py_sha256"] or fp.get(u"core_py_sha256") != now["core_py_sha256"]:
        out.append(u"engine の指紋が今の engine と違う(記録を作ったあとに engine が変わった)")
    if rec.get(u"lib の指紋") != dict((rel, sha256_rel(rel)) for rel in TS.LIB_RELS) or rec.get(u"仕掛けの 2 file の sha256") != dict((rel, sha256_rel(rel)) for rel in TS.DEVICE_RELS):
        out.append(u"lib・仕掛けの sha256 が現物と違う")
    if full:
        want_fetch = sha256_rel(TS.FETCH_REL) if fetch_rec_exists else None
        if rec.get(u"取得の記録の sha256") != want_fetch or want_fetch is None:
            out.append(u"取得の記録の sha256 が現物と違う")
        if rec.get(u"範囲") != u"封 §1 の 17 社" or rec.get(u"材料の置き場") != u"~/.cache/audit-core/tanshin-2026-11-09":
            out.append(u"範囲・材料の置き場が本番でない")
    else:
        if rec.get(u"範囲") not in (u"封 §1 の 17 社", TS.SCOPE_ONLY):
            out.append(u"範囲の字が決まった 2 つのどちらでもない")
    out += cache_problems(rec)
    return out


def fetch_problems(rec, full=True):
    out = clean_problems(rec)
    tab = seal_table()
    rows = rec.get(u"行") or []
    if rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"封の path・commit が違う")
    if rec.get(u"この script の sha256") != sha256_rel(TS.FETCH_SCRIPT_REL):
        out.append(u"取得の script の sha256 が現物と違う")
    out += cache_problems(rec)
    if full:
        if len(rows) != 17:
            out.append(u"行が 17 でない")
        if [r.get(u"証券コード") for r in rows] != [t[1] for t in tab]:
            out.append(u"証券コードの並びが封 §1 の表と違う")
        if rec.get(u"範囲") != u"封 §1 の 17 本" or rec.get(u"置き場") != u"~/.cache/audit-core/tanshin-2026-11-09":
            out.append(u"範囲・置き場が本番でない")
    by = dict((t[1], t) for t in tab)
    for r in rows:
        t = by.get(r.get(u"証券コード"))
        if t is None:
            out.append(u"証券コードが封 §1 の表に無い")
            continue
        if r.get(u"番号") != t[2] or r.get(u"ZIP の sha256") != t[3] or r.get(u"#") != t[0]:
            out.append(u"%s: 番号・sha256 が封 §1 の表と違う" % t[1])
        if r.get(u"HTTP の状態") not in (200, None):
            out.append(u"%s: HTTP の状態が 200 でも cache でもない" % t[1])
        if (r.get(u"HTTP の状態") is None) != (u"cache" in (r.get(u"取得") or u"")):
            out.append(u"%s: HTTP の状態と取得の語が合わない" % t[1])
        if not isinstance(r.get(u"byte 数"), int) or r[u"byte 数"] <= 0:
            out.append(u"%s: byte 数が正の整数でない" % t[1])
        if not re.fullmatch(r"S[0-9A-Z]{7}", r.get(u"docID") or u""):
            out.append(u"%s: docID の形が違う" % t[1])
        if not re.fullmatch(r"[0-9a-f]{64}", r.get(u"有報の ZIP の sha256") or u""):
            out.append(u"%s: 有報の ZIP の sha256 の形が違う" % t[1])
    if len(set(r.get(u"docID") for r in rows)) != len(rows) or len(set(r.get(u"有報の ZIP の sha256") for r in rows)) != len(rows):
        out.append(u"docID か有報の ZIP の sha256 が 1 対 1 でない")
    if rec.get(u"表と一致した ZIP") != len(rows):
        out.append(u"表と一致した ZIP の数が行の数と違う")
    return out


def row_shape_problems(row):
    out = []
    if not (isinstance(row, list) and len(row) == 9):
        return [u"states の行が 9 つの欄でない"]
    s, pos, st, reason, per, formula, fam, ab, pspan = row
    if not (isinstance(s, int) and isinstance(pos, int) and not isinstance(s, bool)):
        out.append(u"文の番号・位置が整数でない")
    if st not in STATES:
        out.append(u"state が 4 つのどれでもない")
    if reason is not None and not RUN.reason_ok(reason):
        out.append(u"reason の字が符号の形でない")
    if per not in PERIODS5:
        out.append(u"pointer の期が 5 つのどれでもない")
    if not isinstance(formula, bool) or not isinstance(ab, bool) or not isinstance(pspan, bool):
        out.append(u"formula の有無・a−b・span に % を含むが真偽でない")
    if fam not in FAMILIES:
        out.append(u"単位の族が 3 つのどれでもない")
    if ab and not (formula and fam == u"円族"):
        out.append(u"a−b(円)が formula の有無・円族と合わない")
    return out


def block_problems(code, p, blk):
    out = []
    rows = blk.get(u"行") or []
    for r in rows:
        out += [u"%s %s: %s" % (code, p, x) for x in row_shape_problems(r)]
    keys = [(r[0], r[1]) for r in rows if isinstance(r, list) and len(r) >= 2]
    if keys != sorted(set(keys)):
        out.append(u"%s %s: 行が (文の番号, 位置) の昇順・重複なしでない" % (code, p))
    if blk.get(u"claim") != len(rows) or sum((blk.get(u"4 state") or {}).values()) != len(rows):
        out.append(u"%s %s: claim・4 state の合計が行の数と違う" % (code, p))
    if json.loads(json.dumps(blk.get(u"4 state"))) != dict((s, sum(1 for r in rows if r[2] == s)) for s in STATES):
        out.append(u"%s %s: 4 state が行から数え直した値と違う" % (code, p))
    want_reason = dict((s, {}) for s in STATES)
    for r in rows:
        k = r[3] if r[3] is not None else u"なし"
        want_reason[r[2]][k] = want_reason[r[2]].get(k, 0) + 1
    if json.loads(json.dumps(blk.get(u"reason"))) != dict((s, dict(sorted(c.items()))) for s, c in want_reason.items()):
        out.append(u"%s %s: reason が行から数え直した値と違う" % (code, p))
    vm = [r for r in rows if r[2] == VM]
    want_vm = {u"行": len(vm), u"導出(formula)": sum(1 for r in vm if r[5]), u"直接": sum(1 for r in vm if not r[5]), u"% の数": sum(1 for r in vm if r[8]),
               u"円族の数": sum(1 for r in vm if not r[8]), u"両期の fact を引く a−b(円)": sum(1 for r in vm if r[7]),
               u"単位の族が %": sum(1 for r in vm if r[6] == u"%"), u"単位の族が円族": sum(1 for r in vm if r[6] == u"円族"), u"単位の族が他": sum(1 for r in vm if r[6] == u"他"),
               u"pointer の期": dict((k, sum(1 for r in vm if r[4] == k)) for k in PERIODS5)}
    if json.loads(json.dumps(blk.get(u"VALUE_MISMATCH の内訳"))) != want_vm:
        out.append(u"%s %s: VALUE_MISMATCH の内訳が行から数え直した値と違う" % (code, p))
    return out


def moves_problems(code, b):
    out = []
    old = dict(((r[0], r[1]), r) for r in b[u"profile"][u"P30E"][u"行"])
    new = dict(((r[0], r[1]), r) for r in b[u"profile"][u"P32E"][u"行"])
    seen = set()
    for m in b[u"P30E から P32E で動いた行"]:
        if not (isinstance(m, list) and len(m) == 6):
            out.append(u"%s: 動いた行が 6 つの欄でない" % code)
            continue
        k = (m[0], m[1])
        seen.add(k)
        if k not in old or k not in new:
            out.append(u"%s: 動いた行が両方の profile に無い" % code)
            continue
        if (m[2], m[3], m[4], m[5]) != (old[k][2], new[k][2], old[k][4], new[k][4]):
            out.append(u"%s: 動いた行の state・期が行と違う" % code)
    for k in old:
        if k in new and (old[k][2] != new[k][2] or old[k][4] != new[k][4]) and k not in seen:
            out.append(u"%s: state か期が違う行が動いた行に無い" % code)
    return out


def states_problems(rec, full=True):
    out = clean_problems(rec)
    out += common_header_problems(rec, full, os.path.exists(os.path.join(ROOT, TS.FETCH_REL)))
    books = rec.get(u"本") or []
    tab = seal_table()
    profiles = list(TS.engine_profiles_now())
    if rec.get(u"profile") != profiles:
        out.append(u"profile が P27・P30E・P32E(engine に在れば P33E)でない")
    if rec.get(u"社の数") != len(books):
        out.append(u"社の数が本の数と違う")
    if full and [b.get(u"証券コード") for b in books] != [t[1] for t in tab]:
        out.append(u"本の並びが封 §1 の表と違う")
    by = dict((t[1], t) for t in tab)
    for b in books:
        code = b.get(u"証券コード")
        t = by.get(code)
        if t is None:
            out.append(u"証券コードが封 §1 の表に無い")
            continue
        if (b.get(u"#"), b.get(u"番号"), b.get(u"ZIP の sha256"), b.get(u"下見の字数"), b.get(u"下見の claim(P32E)")) != (t[0], t[2], t[3], t[4], t[5]):
            out.append(u"%s: 番号・sha256・下見の数が封 §1 の表と違う" % code)
        if list((b.get(u"profile") or {})) != profiles:
            out.append(u"%s: profile の欄が profile の列と違う" % code)
            continue
        if b.get(u"対応") != dict((p, True) for p in profiles):
            out.append(u"%s: claim の並びが raw claim と対応していない" % code)
        for p in profiles:
            out += block_problems(code, p, b[u"profile"][p])
        out += moves_problems(code, b)
        if not (0 <= b.get(u"行頭が | の文の数", -1) <= b.get(u"文の数", -2)):
            out.append(u"%s: 行頭が | の文の数が文の数を超える" % code)
        if b.get(u"P30E から P32E で reason だけが違う行") != b.get(u"P30E から P32E で reason だけが違う行") or not isinstance(b.get(u"P30E から P32E で reason だけが違う行"), int):
            out.append(u"%s: reason だけが違う行が整数でない" % code)
    if out and any(u"profile の欄" in x for x in out):
        return out
    cut = rec.get(u"切り出し") or {}
    if cut.get(u"NFKC") is not True or cut.get(u"字数の合計") != sum(b[u"概況の字数"] for b in books) or \
            cut.get(u"下見と字数が同じ社") != sum(1 for b in books if b[u"概況の字数"] == b[u"下見の字数"]):
        out.append(u"切り出しの欄(NFKC・字数の合計・下見と同じ社)が本から数え直した値と違う")
    if full and cut.get(u"下見の字数の合計") != 84378:
        out.append(u"下見の字数の合計が 84,378 でない")
    if json.loads(json.dumps(rec.get(u"集計"))) != json.loads(json.dumps(TS.states_totals(books, profiles))):
        out.append(u"集計が本から作り直した値と違う")
    out += totals_problems(rec)
    if json.loads(json.dumps(rec.get(u"H の欄"))) != json.loads(json.dumps(TS.states_columns(books, profiles))):
        out.append(u"H の欄が本から作り直した値と違う")
    return out


def totals_from_rows(books, profiles):
    u"""集計(profile ごとの claim・4 state・reason)を各ブロックの行から数え直す(``TS.states_totals`` を使わない)。"""
    out = {}
    for p in profiles:
        rows = [r for b in books for r in b[u"profile"][p][u"行"]]
        reason = dict((st, {}) for st in STATES)
        for r in rows:
            k = r[3] if r[3] is not None else u"なし"
            reason[r[2]][k] = reason[r[2]].get(k, 0) + 1
        out[p] = {u"claim": len(rows), u"4 state": dict((st, sum(1 for r in rows if r[2] == st)) for st in STATES),
                  u"reason": dict((st, dict(sorted(c.items()))) for st, c in reason.items())}
    return out


def totals_problems(rec):
    u"""記録の ``集計`` の claim・4 state・reason が、本の行から独立に数えた値と同じか。"""
    want = totals_from_rows(rec.get(u"本") or [], list(rec.get(u"profile") or []))
    got = rec.get(u"集計") or {}
    out = []
    for p, w in want.items():
        g = got.get(p) or {}
        for k in (u"claim", u"4 state", u"reason"):
            if json.loads(json.dumps(g.get(k))) != w[k]:
                out.append(u"集計 %s の %s が本の行から数えた値と違う" % (p, k))
    return out


def inject_problems(rec, full=True):
    out = clean_problems(rec)
    out += common_header_problems(rec, full, os.path.exists(os.path.join(ROOT, TS.FETCH_REL)))
    rows = rec.get(u"行") or []
    tab = seal_table()
    codes = [t[1] for t in tab]
    if rec.get(u"profile") != list(TS.INJECT_PROFILES):
        out.append(u"profile が P30E・P32E でない")
    sw = rec.get(u"切り替え") or {}
    if sw.get(u"inject の中の値") is not True or sw.get(u"出たあとの値") is not False or sw.get(u"T5 の切り替え inject の中の値") is not True or sw.get(u"T5 の切り替え 出たあとの値") is not False:
        out.append(u"切り替え 2 つが inject の中で真・出たあとで偽になっていない")
    if sw.get(u"配線の問題") != []:
        out.append(u"配線の問題が空でない")
    if sw.get(u"名前") != TY.FLAG or sw.get(u"T5 の切り替えの名前") != TY.FLAG2:
        out.append(u"切り替えの名前が違う")
    if rec.get(u"cap") != CAP or RUN.INJECT_CAP != CAP:
        out.append(u"cap が封の決め(型ごと 1 本あたり 10)でない")
    if rec.get(u"注入の行の数") != len(rows):
        out.append(u"注入の行の数が行の数と違う")
    per = rec.get(u"本ごとの数え") or {}
    if not set(per) <= set(codes) or (full and list(per) != codes):
        out.append(u"本ごとの数えの証券コードが封 §1 の表と合わない")
    seen = set()
    cells = collections.Counter()
    labels = (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
    for r in rows:
        code, typ = r.get(u"証券コード"), r.get(u"型")
        if code not in codes or typ not in TYPES:
            out.append(u"証券コード・型が表に無い")
            continue
        cells[(code, typ)] += 1
        short = TS.TYPE_SHORT[typ]
        if not re.fullmatch(r"%s_TS-%s-\d\d" % (re.escape(code), short), r.get(u"id") or u"") or r[u"id"] in seen:
            out.append(u"%s: id の形か重複: %s" % (code, r.get(u"id")))
        seen.add(r.get(u"id"))
        if r.get(u"形") not in TS.SHAPES:
            out.append(u"形が 3 つのどれでもない")
        for p in TS.INJECT_PROFILES:
            c = r.get(p) or {}
            if c.get(u"reason") is not None and not RUN.reason_ok(c.get(u"reason")):
                out.append(u"%s: %s の reason の字が符号の形でない" % (r.get(u"id"), p))
            if c.get(u"結果") not in labels or c.get(u"対応") != (c.get(u"結果") != TUNE.LABEL_UNMAPPED):
                out.append(u"%s: %s の結果・対応が合わない" % (r.get(u"id"), p))
            conds = r.get(PI.F_COND % p)
            miss = r.get(PI.F_MISS % p)
            if conds is None:
                if c.get(u"対応") or miss != [PI.NO_BASE]:
                    out.append(u"%s: %s の土台なしの行の欄が合わない" % (r.get(u"id"), p))
            else:
                if list(conds) != list(PI.CONDS) or miss != [k for k in PI.CONDS if not conds[k]] or c.get(u"対応") != (miss == []):
                    out.append(u"%s: %s の対応の条件・欠けた条件・対応が合わない" % (r.get(u"id"), p))
            if r.get(u"%s の注入後の pointer の期" % p) not in PERIODS5:
                out.append(u"%s: %s の注入後の pointer の期が 5 つのどれでもない" % (r.get(u"id"), p))
        if r.get(LINK_KEY) is not (r[u"P32E の欠けた条件"] != [PI.NO_BASE]):
            out.append(u"%s: P32E の土台に対応の欄が合わない" % r.get(u"id"))
        for k in (u"round-trip", u"読み直し", u"先頭の位が減った", u"届いた", u"engine の手がかり", u"文に前期の語"):
            if not isinstance(r.get(k), bool):
                out.append(u"%s: %s が真偽でない" % (r.get(u"id"), k))
        if typ == TYPES[1] and (r.get(u"相手の fact の期") not in TY.PARTNER_PERIODS or not isinstance(r.get(u"相手と同じ要素か"), bool)):
            out.append(u"%s: T5 の相手の欄が合わない" % r.get(u"id"))
        if typ == TYPES[2] and (r.get(u"r") not in TUNE.T8_R_VALUES or not isinstance(r.get(u"r を決めた回"), int)):
            out.append(u"%s: T8 の r の欄が合わない" % r.get(u"id"))
    if any(n > CAP for n in cells.values()):
        out.append(u"型ごと 1 本あたりの行が cap(10)を超える")
    for code, c in per.items():
        if u"注入しない" in c:
            continue
        for typ in TYPES:
            n = cells.get((code, typ), 0)
            taken = (c.get(typ) or {}).get(u"採った")
            if taken is None or taken > CAP or n > taken:
                out.append(u"%s %s: 採った(%s)と行(%d)・cap が合わない" % (code, typ, taken, n))
            if typ in (TYPES[1], TYPES[3]) and (n != taken or n != (c[typ].get(u"土台 P30E が GROUNDED の site") if c[typ].get(u"土台 P30E が GROUNDED の site", 0) < CAP else CAP)):
                out.append(u"%s %s: 行が土台 GROUNDED の site を先頭から cap 件でない" % (code, typ))
            if typ == TYPES[2] and n != taken:
                out.append(u"%s T8: 行と採ったが違う" % code)
    if json.loads(json.dumps(rec.get(u"集計"))) != json.loads(json.dumps(TS.inject_summary(rows))):
        out.append(u"集計が行から作り直した値と違う")
    if json.loads(json.dumps(rec.get(u"H の欄"))) != json.loads(json.dumps(TS.inject_columns(per, rows))):
        out.append(u"H の欄が行から作り直した値と違う")
    return out


LINK_KEY = TS.LINK_KEY


def states_problems_for_book(book):
    u"""1 社の本の整合(行・ブロック・動いた行)だけを見る。"""
    out = []
    for p, blk in book[u"profile"].items():
        out += block_problems(book[u"証券コード"], p, blk)
    return out + moves_problems(book[u"証券コード"], book)


def record_problems(R, full=True):
    out = [u"fetch: " + x for x in fetch_problems(R["fetch"], full)]
    out += [u"states: " + x for x in states_problems(R["states"], full)]
    out += [u"inject: " + x for x in inject_problems(R["inject"], full)]
    return out


def judge_problems(R, seal):
    u"""判定: script の ``columns_from_records`` が行の独立の数え直しと同じ・script の判定が封の幅(留めた値)から求めた判定と同じ・H-10 は判定しない。"""
    out = []
    cols = TS.columns_from_records(R["fetch"], R["states"], R["inject"])
    want = recount(R["fetch"], R["states"], R["inject"])
    for k in want:
        if tuple(cols[k]) != tuple(want[k]):
            out.append(u"%s: 実測の値が行から数え直した値と違う" % k)
    H = TS.build_H(R, seal)
    if dict(H["judge"]) != dict(expected_judge(want)):
        out.append(u"判定が封の幅から求めた判定と違う")
    if H["judge"]["H-10"] != u"司令塔が読む":
        out.append(u"H-10 を判定している")
    return out


def doc_problems(doc, R, seal):
    H = TS.build_H(R, seal)
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != TS.render_pred(H["cols"], H["judge"], seal).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if got.get("states") != TS.render_states(R["states"], R["inject"]).split(u"\n"):
        out.append(u"表 states が記録から作り直した表と違う")
    for k in got:
        if k not in ("pred", "states"):
            out.append(u"知らない表 %s" % k)
    if DOCID_RE.search(doc):
        out.append(u"docID が文書にある")
    for w in FOR_RESULT_WORDS:
        if w in doc:
            out.append(u"禁止語: " + w)
    out += [u"散文の数に【門なし】が無い: 行 %d %s" % x for x in PR.prose_problems(doc)]
    return out


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = (list(REC_REL.values()) + [DOC_REL]) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others)


# ================================================================ 小さい標本の記録(通信しない・cache を読まない)
CODE_A, CODE_B = u"151A0", u"192A0"
SAMPLE_DOCS = {CODE_A: u"S100" + u"AAAA", CODE_B: u"S100" + u"BBBB"}
CACHE_SNAP = collections.OrderedDict([(u"edinet", {u"存在": True, u"件数": 3, u"名前の一覧の sha256": u"0" * 64})])


def srow(s, pos, state, reason=None, per=u"なし", formula=False, fam=u"%", ab=False, pspan=None):
    u"""states の行(9 欄)。pspan(span に % を含む)の既定は 単位の族が % のとき真(標本の作りの既定)。"""
    return [s, pos, state, reason, per, formula, fam, ab, (fam == u"%") if pspan is None else pspan]


def sample_books(profiles=None):
    u"""2 社 × profile の本。profile の列は engine の今の profile(``TS.engine_profiles_now()``。P33E が在る木では 4 つ・無い木では 3 つ)。
    行は手で書き、集計・内訳は script の部品(profile_block)で作る(門は別に数え直す)。"""
    profiles = list(TS.engine_profiles_now()) if profiles is None else list(profiles)
    tab = dict((t[1], t) for t in seal_table())
    out = []
    for code, text_len in ((CODE_A, 3586), (CODE_B, 3000)):
        t = tab[code]
        p27 = [srow(1, 5, G, None, u"CurrentYear"), srow(2, 7, UNV, u"no_subject"), srow(3, 9, PNF, u"no_element"), srow(4, 3, UNV, u"target_or_plan"), srow(5, 1, VM, None, u"CurrentYear", False, u"%")]
        p30 = [list(r) for r in p27]
        p30[2] = srow(3, 9, G, None, u"CurrentYear")
        p32 = [list(r) for r in p30]
        p32[1] = srow(2, 7, VM, None, u"Prior1Year", True, u"円族", True)
        p33 = [list(r) for r in p32]
        p33[3] = srow(4, 3, G, None, u"CurrentYear")                                    # P33E の列は P32E の写しにしない(4 state が P32E と違う)
        rows_of = {u"P27": p27, u"P30E": p30, u"P32E": p32, u"P33E": p33}
        blocks = collections.OrderedDict((p, TS.profile_block(rows_of[p])) for p in profiles)
        moved = [[2, 7, UNV, VM, u"なし", u"Prior1Year"]]
        out.append(collections.OrderedDict([
            (u"#", t[0]), (u"証券コード", code), (u"番号", t[2]), (u"ZIP の sha256", t[3]), (u"概況の字数", text_len), (u"下見の字数", t[4]), (u"下見の claim(P32E)", t[5]),
            (u"文の数", 40), (u"行頭が | の文の数", 0), (u"対応", collections.OrderedDict((p, True) for p in profiles)),
            (u"profile", blocks), (u"P30E から P32E で動いた行", moved), (u"P30E から P32E で reason だけが違う行", 0)]))
    return out


def sample_states(profiles=None):
    profiles = list(TS.engine_profiles_now()) if profiles is None else list(profiles)
    books = sample_books(profiles)
    rec = TS.header_ts(ROOT, "states", u"s", CACHE_SNAP, CACHE_SNAP, profiles, FE.default_cache_dir(), u"x")
    rec[u"範囲"] = TS.SCOPE_ONLY
    rec[u"切り出し"] = collections.OrderedDict([(u"規則", u"r"), (u"NFKC", True), (u"下見の字数の合計", sum(b[u"下見の字数"] for b in books)),
                                              (u"字数の合計", sum(b[u"概況の字数"] for b in books)), (u"下見と字数が同じ社", sum(1 for b in books if b[u"概況の字数"] == b[u"下見の字数"]))])
    rec[u"社の数"] = len(books)
    rec[u"集計"] = TS.states_totals(books, profiles)
    rec[u"H の欄"] = TS.states_columns(books, profiles)
    rec[u"限界"] = list(TS.STATES_LIMITS)
    rec[u"key_leaks"] = []
    rec[u"本"] = books
    return rec


TEXT_T = PSR.TEXT_P + u"\n営業利益は700百万円でした。当期は1,234百万円でした。\n"
REFS_T = list(PSR.REFS_P) + [{"key": "jppfs:OperatingIncome@CurrentYearDuration", "value": 700000000.0, "unit": u"円", "label": u"営業利益"}]


def run_ts(text=TEXT_T, refs=REFS_T, patches=(), seed=u"sd", key=u"%s_TS" % CODE_A, verify=None, cap=None):
    with Patch() as pt, NS.yen_scan_on(), TY.t5_yen_on():
        for mod, name, v in patches:
            pt.set(mod, name, v)
        kw = {} if cap is None else {"cap": cap}
        return TS.inject_text_ts(b"zip", text, refs, seed, key, verify=verify or PSR.make_verify(text), **kw)


def sample_inject():
    rows, per = [], collections.OrderedDict()
    for code in (CODE_A, CODE_B):
        r, c = run_ts(key=u"%s_TS" % code, seed=u"sd-" + code)
        per[code] = c
        for x in r:
            d = collections.OrderedDict([(u"証券コード", code)])
            d.update(x)
            rows.append(d)
    # 2 つの profile で結果が違う行を作る(同じ標本の使い回しで『P30E を見る』ような取り違えの変異が黙るのを防ぐ)
    passed = {u"対応": True, u"結果": TUNE.LABEL_PASS, u"state": G, u"reason": None}
    t8 = [r for r in rows if r[u"型"] == TYPES[2]]
    t1 = [r for r in rows if r[u"型"] == TYPES[0]]
    t8[0][u"P32E"] = dict(passed)                                  # P32E だけ通した
    t8[1][u"P30E"] = dict(passed)                                  # P30E だけ通した
    t8[2][u"P30E"] = dict(passed)
    t1[0][u"P30E"] = dict(passed)
    rec = TS.header_ts(ROOT, "inject", u"s", CACHE_SNAP, CACHE_SNAP, TS.INJECT_PROFILES, FE.default_cache_dir(), u"x")
    rec[u"範囲"] = TS.SCOPE_ONLY
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", TY.FLAG), (u"inject の中の値", True), (u"出たあとの値", False), (u"T5 の切り替えの名前", TY.FLAG2),
                                              (u"T5 の切り替え inject の中の値", True), (u"T5 の切り替え 出たあとの値", False), (u"配線の問題", [])])
    rec[u"cap"] = CAP
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"] = TS.inject_summary(rows)
    rec[u"H の欄"] = TS.inject_columns(per, rows)
    rec[u"限界"] = list(TS.INJECT_LIMITS)
    rec[u"key_leaks"] = []
    rec[u"行"] = rows
    return rec


def sample_fetch():
    tab = seal_table()[:2]
    rows = [collections.OrderedDict([(u"#", t[0]), (u"証券コード", t[1]), (u"番号", t[2]), (u"ZIP の sha256", t[3]), (u"取得", u"取得"), (u"HTTP の状態", 200), (u"byte 数", 1234),
                                     (u"docID", SAMPLE_DOCS[t[1]]), (u"有報の ZIP の sha256", (u"%064x" % (i + 1)))]) for i, t in enumerate(tab)]
    return collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT_SHORT), (u"step", u"s"), (u"HEAD の commit", u"a" * 40), (u"この script の sha256", sha256_rel(TS.FETCH_SCRIPT_REL)),
        (u"取得日時(UTC)", u"2026-11-09T00:00:00Z"), (u"範囲", u"**--only(本番の記録ではない)**"), (u"置き場", u"使い捨ての置き場(本番の folder ではない)"),
        (u"cache の前後", collections.OrderedDict([(u"前", CACHE_SNAP), (u"後", CACHE_SNAP), (u"変化なし", True)])), (u"表と一致した ZIP", len(rows)),
        (u"行", rows), (u"key_leaks", [])])


_SAMPLE = {}


def sample_records():
    u"""標本の記録 3 つ(深いコピーを返す)。"""
    if not _SAMPLE:
        _SAMPLE["R"] = collections.OrderedDict([("fetch", sample_fetch()), ("states", sample_states()), ("inject", sample_inject())])
    return copy.deepcopy(_SAMPLE["R"])


def sample_doc(R, seal):
    H = TS.build_H(R, seal)
    return u"\n".join([
        u"# 結果(標本)", u"", u"人が書いた文の測定の表。", u"", u"<!-- 門:start pred -->", TS.render_pred(H["cols"], H["judge"], seal), u"<!-- 門:end -->", u"",
        u"<!-- 門:start states -->", TS.render_states(R["states"], R["inject"]), u"<!-- 門:end -->", u""])


def rebuild_states(rec):
    u"""行を書き換えたあとの記録の集計(各 profile の欄・集計・H の欄)を行から作り直す(行の変更が記録の欄に届いた版)。"""
    profiles = list(rec[u"profile"])
    for b in rec[u"本"]:
        for p in profiles:
            b[u"profile"][p] = json.loads(json.dumps(TS.profile_block(b[u"profile"][p][u"行"])))
    rec[u"集計"] = json.loads(json.dumps(TS.states_totals(rec[u"本"], profiles)))
    rec[u"H の欄"] = json.loads(json.dumps(TS.states_columns(rec[u"本"], profiles)))
    return rec


def mutate(R, path, value):
    u"""R の path(キーと index の列)の値を value にした深いコピー。"""
    R = copy.deepcopy(R)
    o = R
    for k in path[:-1]:
        o = o[k]
    o[path[-1]] = value
    return R


# ================================================================ 試験
class SealPinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_bounds_read_from_the_seal_equal_the_pinned_values(self):
        self.assertEqual([], bounds_problems(self.seal))

    def test_a_2_a_changed_character_in_the_seal_turns_the_pin_red(self):
        rows = TS.seal_pred_rows(self.seal)
        for k in BOUNDS_PIN:
            if BOUNDS_PIN[k] is None:
                continue
            cell = rows[k][1]
            digits = [i for i, ch in enumerate(cell) if ch.isdigit()]
            self.assertTrue(digits, k)
            i = (cell.index(u"〜") - 1) if u"〜" in cell else digits[0]                  # 幅の欄は 〜 の左の数(T1 などのラベルの数字は幅でない)
            self.assertTrue(cell[i].isdigit(), k)
            mutated_cell = cell[:i] + (u"9" if cell[i] != u"9" else u"8") + cell[i + 1:]
            mutated = self.seal.replace(u"| %s | %s | %s |" % (k, rows[k][0], cell), u"| %s | %s | %s |" % (k, rows[k][0], mutated_cell), 1)
            self.assertNotEqual(mutated, self.seal, k)
            self.assertNotEqual([], bounds_problems(mutated), k)

    def test_a_4_an_appended_addendum_section_does_not_change_the_bounds(self):
        addendum = (u"\n## §7 追記(2026-11-10)\n\nH-5 の定義の追記。\n\n| H-5 | 欄 | 1 / 2 / 3 | 外れ方 |\n\n| 99 | 99999 | 0812 | `" + u"0" * 64 + u"` | 1 | 1 |\n")
        self.assertEqual([], bounds_problems(self.seal + addendum))
        self.assertEqual(TS.seal_bounds(self.seal), TS.seal_bounds(self.seal + addendum))
        self.assertEqual(SG.seal_table(self.seal), SG.seal_table(self.seal + addendum))
        self.assertEqual([], SG.seal_problems(self.seal + addendum))
        self.assertEqual([], SG.script_problems(self.seal + addendum))

    def test_a_3_the_h3_width_is_read_exactly_and_one_off_turns_it_red(self):
        rows = TS.seal_pred_rows(self.seal)
        cell = rows["H-3"][1]
        self.assertEqual(u"541 / 110 / 344 / 288", cell)
        mutated = self.seal.replace(u"| H-3 | " + rows["H-3"][0] + u" | " + cell + u" |", u"| H-3 | " + rows["H-3"][0] + u" | 541 / 110 / 344 / 289 |", 1)
        self.assertNotEqual([], bounds_problems(mutated))
        self.assertEqual([(85.0, 105.0), (0.0, 15.0)], TS.seal_bounds(self.seal)["H-4"])
        self.assertEqual([(0.0, 5.0), (0.0, 5.0), (0.0, 5.0), (5.0, 30.0), (40.0, 200.0)], TS.seal_bounds(self.seal)["H-6"])
        self.assertIsNone(TS.seal_bounds(self.seal)["H-10"])


class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.bounds = TS.seal_bounds(cls.seal)

    def mid(self):
        return collections.OrderedDict([("H-1", (17, 17)), ("H-2", (84378, 1283)), ("H-3", (541, 110, 344, 288)), ("H-4", (95.0, 7)), ("H-5", (26, 61, 19)),
                                        ("H-6", (2.0, 2.0, 2.0, 15.0, 100)), ("H-7", (96, 110)), ("H-8", (158, 101)), ("H-9", (0,))])

    def test_c_1_the_middle_of_every_range_is_a_hit_and_h10_is_not_judged(self):
        j = TS.judge_from(self.mid(), self.bounds)
        self.assertEqual([u"当たり"] * 9 + [u"司令塔が読む"], [j["H-%d" % i] for i in range(1, 11)])
        self.assertEqual(expected_judge(self.mid()), j)

    def test_c_2_each_exact_prediction_flips_with_one_off(self):
        for k in ("H-1", "H-2", "H-3", "H-5", "H-7", "H-8", "H-9"):
            base = self.mid()[k]
            for i in range(len(base)):
                for d in (-1, 1):
                    cols = self.mid()
                    v = list(base)
                    v[i] = v[i] + d
                    cols[k] = tuple(v)
                    self.assertEqual(u"外れ", TS.judge_from(cols, self.bounds)[k], (k, i, d))
                    self.assertEqual(u"外れ", expected_judge(cols)[k], (k, i, d))

    def test_c_3_each_range_flips_at_its_edge(self):
        edges = {"H-4": [(85.0, 105.0), (0, 15)], "H-6": [(0, 5), (0, 5), (0, 5), (5, 30), (40, 200)]}
        for k, ranges in edges.items():
            for i, (lo, hi) in enumerate(ranges):
                for v, want in ((lo, u"当たり"), (hi, u"当たり"), (lo - 0.1, u"外れ"), (hi + 0.1, u"外れ")):
                    cols = self.mid()
                    vals = list(cols[k])
                    vals[i] = v
                    cols[k] = tuple(vals)
                    self.assertEqual(want, TS.judge_from(cols, self.bounds)[k], (k, i, v))
                    self.assertEqual(want, expected_judge(cols)[k], (k, i, v))

    def test_c_4_a_missing_value_is_a_miss_not_a_hit(self):
        cols = self.mid()
        cols["H-4"] = (None, 7)
        self.assertEqual(u"外れ", TS.judge_from(cols, self.bounds)["H-4"])
        cols = self.mid()
        cols["H-6"] = (None, 2.0, 2.0, 15.0, 100)                  # 分母 0 の率は None = 外れ
        self.assertEqual(u"外れ", TS.judge_from(cols, self.bounds)["H-6"])
        cols = self.mid()
        del cols["H-3"]
        self.assertEqual(u"外れ", TS.judge_from(cols, self.bounds)["H-3"])

    def test_c_5_the_t1_over_five_percent_is_a_miss(self):
        cols = self.mid()
        cols["H-6"] = (5.1, 2.0, 2.0, 15.0, 100)
        self.assertEqual(u"外れ", TS.judge_from(cols, self.bounds)["H-6"])

    def test_c_6_h10_stays_not_judged_whatever_the_columns(self):
        for cols in (self.mid(), collections.OrderedDict()):
            self.assertEqual(u"司令塔が読む", TS.judge_from(cols, self.bounds)["H-10"])


class SampleRecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_g_1_the_sample_records_are_green_and_the_judgment_is_rebuilt(self):
        R = sample_records()
        self.assertEqual([], record_problems(R, full=False))
        self.assertEqual([], judge_problems(R, self.seal))
        self.assertNotEqual([], record_problems(R, full=True))                      # 17 社の記録としては足りない

    def test_g_2_the_script_header_passes_the_header_check_and_each_field_turns_it_red(self):
        R = sample_records()
        for kind in ("states", "inject"):
            for path, bad in ((["seal"], u"x"), ([u"封の commit"], u"0000000"), ([u"この script の sha256"], u"0" * 64), ([u"取得の script の sha256"], u"0" * 64),
                              ([u"engine の指紋", u"adapter_xbrl_py_sha256"], u"0" * 64), ([u"engine の指紋", u"core_py_sha256"], u"0" * 64),
                              ([u"lib の指紋", TS.LIB_RELS[0]], u"0" * 64), ([u"仕掛けの 2 file の sha256", TS.DEVICE_RELS[0]], u"0" * 64),
                              ([u"前の便の script の sha256", TS.PB_SCRIPT_REL], u"0" * 64), ([u"範囲"], u"全部"), ([u"profile"], [u"P27"])):
                R2 = copy.deepcopy(R)
                o = R2[kind]
                for k in path[:-1]:
                    o = o[k]
                o[path[-1]] = bad
                prob = (states_problems if kind == "states" else inject_problems)(R2[kind], full=False)
                self.assertNotEqual([], prob, (kind, path))

    def test_g_3_cache_and_the_switches_and_the_cap_turn_it_red(self):
        R = sample_records()
        changed = collections.OrderedDict([(u"edinet", {u"存在": True, u"件数": 4, u"名前の一覧の sha256": u"1" * 64})])
        for kind, fn in (("states", states_problems), ("inject", inject_problems), ("fetch", fetch_problems)):
            R2 = mutate(R, [kind, u"cache の前後", u"後"], changed)
            self.assertNotEqual([], fn(R2[kind], full=False), kind)
            R3 = mutate(R, [kind, u"cache の前後", u"変化なし"], False)
            self.assertNotEqual([], fn(R3[kind], full=False), kind)
        for path in ([u"切り替え", u"出たあとの値"], [u"切り替え", u"T5 の切り替え 出たあとの値"]):
            self.assertNotEqual([], inject_problems(mutate(R, ["inject"] + path, True)["inject"], full=False))
        for path in ([u"切り替え", u"inject の中の値"], [u"切り替え", u"T5 の切り替え inject の中の値"]):
            self.assertNotEqual([], inject_problems(mutate(R, ["inject"] + path, False)["inject"], full=False))
        self.assertNotEqual([], inject_problems(mutate(R, ["inject", u"切り替え", u"配線の問題"], [u"x"])["inject"], full=False))
        self.assertNotEqual([], inject_problems(mutate(R, ["inject", u"cap"], 11)["inject"], full=False))
        self.assertNotEqual([], inject_problems(mutate(R, ["inject", u"cap"], 9)["inject"], full=False))

    def test_g_4_forbidden_keys_pointer_text_company_names_and_key_like_strings_turn_it_red(self):
        R = sample_records()
        for kind, fn in (("states", states_problems), ("inject", inject_problems), ("fetch", fetch_problems)):
            for bad in ({u"span": u"x"}, {u"文": u"x"}, {u"value": 1.0}, {u"pointers": []}, {u"label": u"x"}, {u"note": u"xbrl:jppfs_cor:NetSales@CurrentYearDuration"},
                        {u"note": u"株式会社テスト"}, {u"note": u"a" * 40 + u"Z" * 10}, {u"note": u"formula:a-b"}):
                R2 = copy.deepcopy(R)
                R2[kind].update(bad)
                self.assertNotEqual([], fn(R2[kind], full=False), (kind, bad))
            R3 = mutate(R, [kind, u"key_leaks"], [u"x"])
            self.assertNotEqual([], fn(R3[kind], full=False), kind)
        R4 = copy.deepcopy(R)
        R4["inject"][u"行"][0][u"span"] = u"x"
        self.assertNotEqual([], inject_problems(R4["inject"], full=False))
        R5 = copy.deepcopy(R)
        R5["states"][u"本"][0][u"profile"][u"P32E"][u"行"][0].append(u"x")
        self.assertNotEqual([], states_problems(R5["states"], full=False))

    def test_g_5_a_changed_state_row_or_count_turns_the_states_check_red(self):
        R = sample_records()
        base = R["states"]
        self.assertEqual([], states_problems(base, full=False))
        b = u"本"
        prof = lambda i, p: [b, i, u"profile", p]
        cases = [
            (prof(0, "P32E") + [u"行", 0, 2], UNV if base[b][0][u"profile"][u"P32E"][u"行"][0][2] != UNV else VM),       # 行の state を 1 つ変える
            (prof(0, "P32E") + [u"行", 0, 4], u"他の語"),
            (prof(0, "P32E") + [u"行", 0, 6], u"族"),
            (prof(0, "P32E") + [u"行", 0, 5], u"真"),
            (prof(0, "P32E") + [u"行", 1, 8], True),                                                              # VALUE_MISMATCH の行の span に % を含むの真偽(H-5 の % の数)
            (prof(0, "P32E") + [u"行", 1, 8], u"はい"),
            (prof(0, "P32E") + [u"行", 3, 3], u"reason(1)"),
            (prof(0, "P32E") + [u"claim"], 999),
            (prof(0, "P32E") + [u"4 state", G], 99),
            (prof(0, "P32E") + [u"4 state"], dict(base[b][0][u"profile"][u"P32E"][u"4 state"], **{G: base[b][0][u"profile"][u"P32E"][u"4 state"][G] - 1, VM: base[b][0][u"profile"][u"P32E"][u"4 state"][VM] + 1})),   # 合計は同じで内訳だけ違う
            (prof(0, "P27") + [u"reason", UNV], {u"no_subject": 99}),
            (prof(1, "P30E") + [u"VALUE_MISMATCH の内訳", u"導出(formula)"], 99),
            ([b, 0, u"概況の字数"], 1),
            ([b, 0, u"P30E から P32E で動いた行"], []),
            ([b, 0, u"P30E から P32E で動いた行", 0, 3], G),
            ([b, 0, u"対応", u"P32E"], False),
            ([b, 0, u"行頭が | の文の数"], 99),
            ([b, 1, u"番号"], u"0812" + u"0" * 14),
            ([b, 1, u"証券コード"], u"99999"),
            ([u"集計", u"P32E", u"claim"], 0),
            ([u"集計", u"P32E", u"4 state", G], 0),
            ([u"H の欄", u"H-3", G], 0),
            ([u"H の欄", u"H-9", u"文の数"], 0),
            ([u"切り出し", u"NFKC"], False),
            ([u"切り出し", u"字数の合計"], 1),
            ([u"社の数"], 5),
        ]
        for path, bad in cases:
            self.assertNotEqual([], states_problems(mutate(R, ["states"] + path, bad)["states"], full=False), path)

    def test_g_5b_a_block_that_disagrees_with_its_rows_turns_red_even_when_the_totals_follow_the_block(self):
        u"""ブロックの欄を替えて集計・H の欄をそのブロックから作り直しても、ブロックと行の食い違いで赤(行から数え直す検査を 1 つずつ固定する)。"""
        R = sample_records()
        for path, bad in (([u"4 state"], None), ([u"reason"], {G: {u"なし": 1}, VM: {}, UNV: {u"no_subject": 2}, PNF: {u"no_element": 1}}), ([u"VALUE_MISMATCH の内訳", u"導出(formula)"], 7), ([u"VALUE_MISMATCH の内訳", u"% の数"], 7), ([u"VALUE_MISMATCH の内訳", u"円族の数"], 7)):
            R2 = copy.deepcopy(R)
            blk = R2["states"][u"本"][0][u"profile"][u"P32E"]
            if bad is None:
                bad = dict(blk[u"4 state"], **{G: blk[u"4 state"][G] - 1, VM: blk[u"4 state"][VM] + 1})
            o = blk
            for k in path[:-1]:
                o = o[k]
            o[path[-1]] = bad
            profiles = list(R2["states"][u"profile"])
            R2["states"][u"集計"] = json.loads(json.dumps(TS.states_totals(R2["states"][u"本"], profiles)))
            R2["states"][u"H の欄"] = json.loads(json.dumps(TS.states_columns(R2["states"][u"本"], profiles)))
            self.assertNotEqual([], states_problems(R2["states"], full=False), path)

    def test_g_5c_the_totals_are_recounted_from_the_rows_without_the_script_function(self):
        u"""集計の 4 state・reason・claim を、各ブロックの行から独立に数える。P27・P30E・P32E の 4 state は標本で互いに違う(別の profile から取ると値が動く)。"""
        R = sample_records()
        rec = R["states"]
        self.assertEqual([], totals_problems(rec))
        fours = [tuple(rec[u"集計"][p][u"4 state"].values()) for p in (u"P27", u"P30E", u"P32E")]
        self.assertEqual(3, len(set(fours)))
        self.assertEqual(totals_from_rows(rec[u"本"], list(rec[u"profile"]))[u"P32E"][u"4 state"], dict(rec[u"集計"][u"P32E"][u"4 state"]))
        for p in (u"P27", u"P32E"):                                                   # 集計の欄を別の profile の値にすると赤
            R2 = copy.deepcopy(R)
            R2["states"][u"集計"][p] = copy.deepcopy(R2["states"][u"集計"][u"P30E"])
            self.assertNotEqual([], totals_problems(R2["states"]), p)
            self.assertNotEqual([], states_problems(R2["states"], full=False), p)
        R3 = copy.deepcopy(R)
        R3["states"][u"集計"][u"P32E"][u"reason"][UNV] = {u"no_subject": 9}
        self.assertNotEqual([], totals_problems(R3["states"]))
        R4 = copy.deepcopy(R)
        R4["states"][u"集計"][u"P32E"][u"claim"] += 1
        self.assertNotEqual([], totals_problems(R4["states"]))

    def test_g_6_a_dropped_book_or_row_turns_the_check_red(self):
        R = sample_records()
        R2 = copy.deepcopy(R)
        R2["states"][u"本"].pop()
        self.assertNotEqual([], states_problems(R2["states"], full=False))
        R3 = copy.deepcopy(R)
        R3["states"][u"本"][0][u"profile"][u"P32E"][u"行"].pop()
        self.assertNotEqual([], states_problems(R3["states"], full=False))
        R4 = copy.deepcopy(R)
        R4["states"][u"本"][0][u"profile"][u"P32E"][u"行"][1][2] = G                    # state が P30E と同じに戻る(動いた行の欄と合わない)
        self.assertNotEqual([], states_problems(R4["states"], full=False))

    def test_g_7_a_changed_inject_row_or_count_turns_the_inject_check_red(self):
        R = sample_records()
        base = R["inject"]
        self.assertEqual([], inject_problems(base, full=False))
        rows = base[u"行"]
        t8 = [i for i, r in enumerate(rows) if r[u"型"] == TYPES[2]][0]
        t5 = [i for i, r in enumerate(rows) if r[u"型"] == TYPES[1]][0]
        cases = [
            ([u"行", 0, u"P32E", u"結果"], TUNE.LABEL_PASS), ([u"行", 0, u"P32E", u"対応"], False), ([u"行", 0, u"型"], u"T9"), ([u"行", 0, u"型"], u"T0"),
            ([u"行", 0, u"id"], u"x"), ([u"行", 0, u"形"], u"形"), ([u"行", 0, u"証券コード"], u"99999"), ([u"行", 0, u"round-trip"], u"はい"),
            ([u"行", 0, PI.F_MISS % u"P32E"], [PI.NO_BASE]), ([u"行", 0, PI.F_COND % u"P30E", PI.COND_A], False), ([u"行", 0, u"P32E の注入後の pointer の期"], u"x"),
            ([u"行", t8, u"r"], 0.5), ([u"行", t5, u"相手の fact の期"], u"x"), ([u"行", 0, TS.LINK_KEY], False),
            ([u"注入の行の数"], 1), ([u"集計", TYPES[0], u"注入の行"], 99), ([u"集計", TYPES[0], u"P32E", TUNE.LABEL_PASS, u"件"], 99), ([u"H の欄", u"H-6", u"T9 の注入の行"], 0),
            ([u"H の欄", u"H-6", u"通した率 P32E", u"T1"], 50.0),
            ([u"本ごとの数え", CODE_A, TYPES[3], u"採った"], 11), ([u"本ごとの数え", CODE_A, TYPES[1], u"採った"], 0), ([u"本ごとの数え", CODE_B, TYPES[2], u"採った"], 0),
            ([u"profile"], [u"P30E", u"P30E"]),
        ]
        for path, bad in cases:
            self.assertNotEqual([], inject_problems(mutate(R, ["inject"] + path, bad)["inject"], full=False), path)

    def test_g_8_a_cap_overflow_turns_the_check_red(self):
        R = sample_records()
        rows = R["inject"][u"行"]
        extra = copy.deepcopy([r for r in rows if r[u"証券コード"] == CODE_A and r[u"型"] == TYPES[0]][0])
        for i in range(CAP):
            r = copy.deepcopy(extra)
            r[u"id"] = u"%s_TS-T1-%02d" % (CODE_A, 50 + i)
            rows.append(r)
        R["inject"][u"注入の行の数"] = len(rows)
        R["inject"][u"集計"] = TS.inject_summary(rows)
        R["inject"][u"H の欄"] = TS.inject_columns(R["inject"][u"本ごとの数え"], rows)
        self.assertNotEqual([], inject_problems(R["inject"], full=False))

    def test_g_9_the_fetch_record_check(self):
        R = sample_records()
        self.assertEqual([], fetch_problems(R["fetch"], full=False))
        for path, bad in (([u"行", 0, u"ZIP の sha256"], u"0" * 64), ([u"行", 0, u"番号"], u"0812" + u"1" * 14), ([u"行", 1, u"証券コード"], u"99999"), ([u"行", 0, u"HTTP の状態"], 404),
                          ([u"行", 0, u"HTTP の状態"], None), ([u"行", 0, u"docID"], u"x"), ([u"行", 1, u"docID"], SAMPLE_DOCS[CODE_A]), ([u"行", 0, u"有報の ZIP の sha256"], u"x"),
                          ([u"行", 0, u"byte 数"], 0), ([u"表と一致した ZIP"], 5), ([u"seal"], u"x"), ([u"封の commit"], u"0000000"), ([u"この script の sha256"], u"0" * 64), ([u"行", 0, u"#"], 9)):
            self.assertNotEqual([], fetch_problems(mutate(R, ["fetch"] + path, bad)["fetch"], full=False), path)

    def test_g_10_the_judgment_follows_the_records(self):
        R = sample_records()
        self.assertEqual([], judge_problems(R, self.seal))
        before = TS.build_H(R, self.seal)
        self.assertEqual(u"当たり", before["judge"]["H-9"])                                 # 標本は概況に | の文が無い
        R2 = copy.deepcopy(R)
        R2["states"][u"本"][0][u"行頭が | の文の数"] = 1
        after = TS.build_H(R2, self.seal)
        self.assertEqual(u"外れ", after["judge"]["H-9"])
        self.assertNotEqual(before["judge"], after["judge"])
        R3 = copy.deepcopy(R)
        R3["states"][u"本"][0][u"profile"][u"P32E"][u"行"][0][2] = VM
        rebuild_states(R3["states"])
        self.assertNotEqual(before["cols"]["H-3"], TS.build_H(R3, self.seal)["cols"]["H-3"])      # H-3 の実測が動く


class ColumnsRebuildTest(unittest.TestCase):
    def test_b_1_the_h_columns_are_counted_from_the_rows_and_a_zeroed_column_turns_red(self):
        R = sample_records()
        want = recount(R["fetch"], R["states"], R["inject"])
        got = TS.columns_from_records(R["fetch"], R["states"], R["inject"])
        for k in want:
            self.assertEqual(tuple(want[k]), tuple(got[k]), k)
        sc = TS.states_columns(R["states"][u"本"], list(R["states"][u"集計"]))
        for k in sc:
            for sub in sc[k]:
                R2 = copy.deepcopy(R)
                R2["states"][u"H の欄"][k][sub] = 0 if sc[k][sub] != 0 else 7
                self.assertNotEqual([], states_problems(R2["states"], full=False), (k, sub))

    def test_b_2_a_changed_row_moves_the_column_that_counts_it(self):
        R = sample_records()
        base = TS.columns_from_records(R["fetch"], R["states"], R["inject"])
        R2 = copy.deepcopy(R)
        R2["states"][u"本"][0][u"profile"][u"P32E"][u"行"][1][3] = u"target_or_plan"        # UNV から VM に動いた行の reason(H-7 は UNV の行だけ数える)
        self.assertEqual(tuple(base["H-7"]), tuple(TS.columns_from_records(R2["fetch"], R2["states"], R2["inject"])["H-7"]))
        R3 = copy.deepcopy(R)
        R3["states"][u"本"][0][u"profile"][u"P32E"][u"行"][3][3] = u"no_subject"             # UNV の reason を替える(欄を作り直さなければ、門の数え直しが先に動く)
        self.assertNotEqual(base["H-7"], recount(R3["fetch"], R3["states"], R3["inject"])["H-7"])
        self.assertNotEqual([], states_problems(R3["states"], full=False))
        rebuild_states(R3["states"])
        self.assertEqual([], states_problems(R3["states"], full=False))
        self.assertNotEqual(base["H-7"], TS.columns_from_records(R3["fetch"], R3["states"], R3["inject"])["H-7"])
        R4 = copy.deepcopy(R)
        R4["states"][u"本"][0][u"行頭が | の文の数"] = 3
        self.assertNotEqual(base["H-9"], TS.columns_from_records(R4["fetch"], R4["states"], R4["inject"])["H-9"])
        R5 = copy.deepcopy(R)
        t9 = [r for r in R5["inject"][u"行"] if r[u"型"] == TYPES[3]][0]
        t9[u"P32E"] = dict(t9[u"P32E"], 結果=TUNE.LABEL_PASS)
        self.assertNotEqual(base["H-6"], TS.columns_from_records(R5["fetch"], R5["states"], R5["inject"])["H-6"])
        R6 = copy.deepcopy(R)
        R6["fetch"][u"行"][0][u"ZIP の sha256"] = u"0" * 64
        self.assertNotEqual(base["H-1"], TS.columns_from_records(R6["fetch"], R6["states"], R6["inject"])["H-1"])

    def test_b_3_the_vm_breakdown_definitions(self):
        self.assertEqual(u"%", TS.unit_family(u"%"))
        self.assertEqual(u"%", TS.unit_family(u"ポイント"))
        for u in (u"円", u"千円", u"百万円", u"億円", u"兆円"):
            self.assertEqual(u"円族", TS.unit_family(u), u)
        self.assertEqual(u"他", TS.unit_family(u"人"))
        self.assertEqual(u"他", TS.unit_family(None))
        self.assertTrue(TS.is_formula(("xbrl:a@b", "formula:a-b")))
        self.assertFalse(TS.is_formula(("xbrl:a@b",)))
        self.assertFalse(TS.is_formula(()))
        self.assertTrue(TS.is_ab_yen(("x", "formula:a-b"), u"円族"))
        self.assertFalse(TS.is_ab_yen(("x", "formula:a-b"), u"%"))
        self.assertFalse(TS.is_ab_yen(("x", "formula:a-b(pure)"), u"円族"))      # ちょうど formula:a-b だけ
        self.assertFalse(TS.is_ab_yen(("x", "formula:a/b*100"), u"円族"))
        self.assertFalse(TS.is_ab_yen(("x",), u"円族"))
        rows = [srow(1, 1, VM, None, u"Prior1Year", True, u"円族", True, False), srow(1, 2, VM, None, u"CurrentYear", False, u"%", False, True), srow(1, 3, G), srow(1, 4, VM, None, u"なし", True, u"%", False, False),
                srow(1, 5, VM, None, u"他", False, u"他", False, True), srow(1, 6, VM, None, u"他", False, u"円族", False, True), srow(1, 7, VM, None, u"他", False, u"他", False, False)]
        d = TS.vm_breakdown(rows)
        # H-5 の % の数は span に % を含む行(単位の欄は見ない)・円族の数はそれ以外(2 値)。単位の族は参考の別の欄
        self.assertEqual((6, 2, 4, 3, 3, 1), (d[u"行"], d[u"導出(formula)"], d[u"直接"], d[u"% の数"], d[u"円族の数"], d[u"両期の fact を引く a−b(円)"]))
        self.assertEqual(d[u"% の数"] + d[u"円族の数"], d[u"行"])
        self.assertEqual((2, 2, 2), (d[u"単位の族が %"], d[u"単位の族が円族"], d[u"単位の族が他"]))                # span の定義の数(3 / 3)と単位の族の数(2 / 2 / 2)は別の値
        self.assertNotIn(u"他の単位", d)
        self.assertEqual({u"CurrentYear": 1, u"Prior1Year": 1, u"Prior2Year": 0, u"他": 3, u"なし": 1}, dict(d[u"pointer の期"]))

    def test_b_3b_the_pct_span_flag_comes_from_the_claim_span_and_the_record_keeps_no_span(self):
        u"""profile_rows は claim の span に % の字が在るかの真偽だけを行に持つ(単位の欄は見ない)。偽の verify・raw claim を差し替えて通す。"""
        late = u"売上高は" + u"あ" * 40 + u"(前期比3%増)"                                                    # % が span の先頭 40 字より後ろ(数の後ろの側)にある
        self.assertGreater(late.index(u"%"), 40)
        spans = [u"前年同期比9.6%減", u"売上高は100百万円", u"売上高は100百万円(前年比3%増)", u"増加率は3.0ポイント", u"自己資本比率は52.5％", None, late]
        units = [u"円", u"%", u"円", u"ポイント", u"%", u"円", u"円"]
        claims = [{"id": "N%03d" % (i + 1), "kind": "num", "state": G, "reason": None, "pointers": [], "span": sp, "unit": un} for i, (sp, un) in enumerate(zip(spans, units))]
        raws = [{"id": c["id"], "sentence": 1, "pos": i} for i, c in enumerate(claims)]
        with Patch() as pt:
            pt.set(TS.VD, "verify_document", lambda zb, p, t: {"claims": claims})
            pt.set(TS.R, "build_raw_claims", lambda zm, prof: (raws, []))
            rows, ok, n = TS.profile_rows(b"z", u"t", b"zm", u"P32E")
        self.assertTrue(ok)
        self.assertEqual(7, n)
        self.assertEqual([True, False, True, False, False, False, True], [v[4] for v in rows.values()])         # 先頭 40 字だけを見る版なら最後が偽になる       # 全角の ％ は NFKC の前の字でなく、切り出しの後の半角の % だけを見る(span は半角)
        entries = [TS.row_entry(k, v) for k, v in rows.items()]
        self.assertEqual([True, False, True, False, False, False, True], [e[8] for e in entries])
        self.assertEqual([u"円族", u"%", u"円族", u"%", u"%", u"円族", u"円族"], [e[6] for e in entries])      # 単位の族は別の欄(span の % と食い違っても別々)
        dumped = json.dumps(entries, ensure_ascii=False)
        for sp in [x for x in spans if x]:
            self.assertNotIn(sp, dumped)
        for e in entries:
            self.assertEqual([], row_shape_problems(e))

    def test_b_4_a_row_entry_has_nine_fields_and_no_text(self):
        v = (VM, u"no_subject", ("xbrl:jppfs_cor:NetSales@Prior1YearDuration", "formula:a-b"), u"円族", True)
        row = TS.row_entry((3, 9), v)
        self.assertEqual([3, 9, VM, u"no_subject", u"Prior1Year", True, u"円族", True, True], row)
        self.assertEqual([], row_shape_problems(row))
        for bad in (row[:8], row[:2] + [u"X"] + row[3:], row[:4] + [u"期"] + row[5:], row[:5] + [u"はい"] + row[6:], row[:6] + [u"族"] + row[7:], row[:3] + [u"reason 99"] + row[4:],
                    row[:8] + [u"はい"], row[:8] + [1], [3, 9, G, None, u"なし", False, u"%", True, True]):
            self.assertNotEqual([], row_shape_problems(bad), bad)


# ================================================================ w. 手順・行の欄(script の関数を小さい入力で通す。zip・判定は偽。lib は本物。通信なし)
class ProcedureTest(unittest.TestCase):
    def test_w_1_rows_come_from_the_four_types_and_carry_every_column(self):
        rows, c = run_ts()
        types = collections.Counter(r[u"型"] for r in rows)
        self.assertEqual(set(TYPES), set(types))
        self.assertEqual(list(TYPES), [t for t in TYPES if types[t]])
        self.assertEqual([], sorted(set(k for r in rows for k in RUN.walk_keys(r) if k in FORBIDDEN_KEYS)))
        base = [u"id", u"型", u"形", u"単位", u"基準の claim", TS.LINK_KEY, u"round-trip", u"読み直し", u"先頭の位が減った", u"engine の手がかり", u"文に前期の語", u"基準の pointer の期"]
        tail = [u"P30E", u"P32E", u"P30E の注入後の pointer の期", u"P32E の注入後の pointer の期", u"届いた", PI.F_COND % u"P30E", PI.F_COND % u"P32E", PI.F_MISS % u"P30E", PI.F_MISS % u"P32E",
                PI.F_OLD % u"P30E", PI.F_OLD % u"P32E", u"注入の前後で claim の数が同じ(P32E)"]
        extra = {TYPES[1]: [u"相手の fact の期", u"相手と同じ要素か"], TYPES[2]: [u"r", u"r を決めた回"]}
        for r in rows:
            self.assertEqual(base + extra.get(r[u"型"], []) + tail, list(r), r[u"型"])
        for t in TYPES:
            ids = [r[u"id"] for r in rows if r[u"型"] == t]
            self.assertEqual([u"%s_TS-%s-%02d" % (CODE_A, TS.TYPE_SHORT[t], i + 1) for i in range(len(ids))], ids)
        self.assertEqual(list(TYPES), list(c))
        self.assertEqual(len([r for r in rows if r[u"型"] == TYPES[3]]), c[TYPES[3]][u"採った"])
        self.assertEqual(len([r for r in rows if r[u"型"] == TYPES[1]]), c[TYPES[1]][u"採った"])
        self.assertEqual(len([r for r in rows if r[u"型"] == TYPES[2]]), c[TYPES[2]][u"採った"])
        for r in rows:
            for p in (u"P30E", u"P32E"):
                self.assertEqual({u"対応", u"結果", u"state", u"reason"}, set(r[p]))

    def test_w_2_the_columns_are_true_for_an_honest_injection_and_the_cells_follow_the_stub(self):
        rows, _c = run_ts()
        for r in rows:
            self.assertTrue(r[u"round-trip"], r[u"id"])
            self.assertTrue(r[u"読み直し"], r[u"id"])
            self.assertTrue(r[u"届いた"], r[u"id"])
            self.assertTrue(r[TS.LINK_KEY])
            self.assertEqual({PI.COND_A: True, PI.COND_I: True, PI.COND_U: True}, dict(r[PI.F_COND % u"P32E"]))
            self.assertEqual([], r[PI.F_MISS % u"P32E"])
            self.assertEqual(TUNE.LABEL_NAMED_ORIGINAL, r[u"P32E"][u"結果"])          # 偽の verify は注入した数に VALUE_MISMATCH を返す
        rows2, _ = run_ts(verify=PSR.make_verify(TEXT_T, inj_state=PSR.G))
        self.assertTrue(all(r[u"P32E"][u"結果"] == TUNE.LABEL_PASS for r in rows2))

    def test_w_3_the_two_profiles_asked_for_are_p30e_and_p32e_and_the_base_is_p30e_grounded(self):
        asked = []
        inner = PSR.make_verify(TEXT_T)

        def spy(zb, p, t):
            asked.append(p)
            return inner(zb, p, t)
        rows, _ = run_ts(verify=spy)
        self.assertEqual({u"P30E", u"P32E"}, set(asked))
        # 土台が P30E で GROUNDED でない数は行にならない
        rows2, c2 = run_ts(verify=PSR.make_verify(TEXT_T, base_ptr=PSR.PTR_PRIOR, inj_state=PSR.V_))
        self.assertTrue(rows2)

        def never_grounded(zb, p, t):
            out = inner(zb, p, t)
            for c in out["claims"]:
                c["state"] = PSR.V_
            return out
        rows3, c3 = run_ts(verify=never_grounded)
        self.assertEqual([], rows3)
        self.assertTrue(all(c3[t].get(u"採った", 0) >= 0 for t in TYPES))

    def test_w_4_the_cap_is_applied_per_type_and_follows_the_run_cap(self):
        rows, c = run_ts(cap=1)
        for t in TYPES:
            self.assertLessEqual(len([r for r in rows if r[u"型"] == t]), 1, t)
        rows10, _ = run_ts()
        for t in TYPES:
            self.assertLessEqual(len([r for r in rows10 if r[u"型"] == t]), RUN.INJECT_CAP)
        self.assertEqual(CAP, RUN.INJECT_CAP)
        rows2, _ = run_ts(patches=((RUN, "INJECT_CAP", 2),))                          # 既定の cap は呼ぶ時の RUN.INJECT_CAP
        for t in TYPES:
            self.assertLessEqual(len([r for r in rows2 if r[u"型"] == t]), 2, t)
        self.assertGreater(len(rows10), len(rows2))

    def test_w_4b_an_engine_declared_reason_with_a_digit_in_the_parentheses_passes_and_a_value_in_it_stops(self):
        declared = u"no_element(no prior2 for prior-year diff)"
        self.assertTrue(RUN.reason_ok(declared))
        with self.assertRaises(SystemExit):
            TUNE.safe_reason(declared)                                                   # TUNE の版は止まる(これが短信の文で出た)
        inner = PSR.make_verify(TEXT_T)

        def with_reason(reason):
            def verify(zb, p, t):
                out = inner(zb, p, t)
                for c in out["claims"]:
                    if c["state"] != PSR.G:
                        c["state"], c["reason"] = PSR.P_, reason
                return out
            return verify
        rows, _ = run_ts(verify=with_reason(declared))
        self.assertTrue(rows and all(r[u"P32E"][u"reason"] == declared and r[u"P32E"][u"結果"] == TUNE.LABEL_PNF for r in rows))
        with self.assertRaises(SystemExit):
            run_ts(verify=with_reason(u"no_element(12345 yen)"))                         # 数が混ざる字は RUN の版も止める
        self.assertIsNot(TUNE.safe_reason, RUN.safe_reason)                              # with を出たら戻っている

    def test_w_4c_the_t9_cap_is_applied_to_the_grounded_sites_not_before_the_base_filter(self):
        u"""並べ替えた T9 の site の先頭が土台 GROUNDED でないとき、cap=1 は GROUNDED の site を先頭から 1 件取る(cap を絞る前に掛けると 0 件)。"""
        with NS.yen_scan_on(), TY.t5_yen_on():
            _stages, sites = TS.PS.t9_all_sites(TEXT_T, REFS_T, u"sd", u"%s_TS" % CODE_A)
        self.assertGreaterEqual(len(sites), 2)
        tok = sites[0]["token"]
        first = TEXT_T[tok.start:tok.unit_end]
        inner = PSR.make_verify(TEXT_T)

        def first_not_grounded(zb, p, t):
            out = inner(zb, p, t)
            for c in out["claims"]:
                if c["span"] == first:
                    c["state"] = PSR.V_
            return out
        rows, c = run_ts(verify=first_not_grounded, cap=1)
        t9 = [r for r in rows if r[u"型"] == TYPES[3]]
        self.assertEqual(1, len(t9))
        self.assertEqual(1, c[TYPES[3]][u"採った"])
        self.assertEqual(len(sites) - 1, c[TYPES[3]][u"土台 P30E が GROUNDED の site"])                  # 先頭の 1 件は土台 GROUNDED でない
        self.assertEqual(1, c[TYPES[3]][u"cap を基準で絞る前に掛けた数"])
        rows_all, _ = run_ts(verify=first_not_grounded)
        self.assertEqual(len(sites) - 1, len([r for r in rows_all if r[u"型"] == TYPES[3]]))
        rows0, _ = run_ts(cap=1)                                                      # 全部 GROUNDED なら先頭の 1 件
        self.assertEqual(1, len([r for r in rows0 if r[u"型"] == TYPES[3]]))

    def test_w_5_a_fullwidth_digit_text_is_skipped(self):
        rows, c = run_ts(text=u"売上高は１２３百万円でした。\n")
        self.assertEqual([], rows)
        self.assertIn(u"注入しない", c)

    def test_w_6_the_switches_are_false_after_a_run_and_the_job_needs_both_true(self):
        run_ts()
        self.assertFalse(getattr(N, TY.FLAG))
        self.assertFalse(getattr(S, TY.FLAG2))
        with self.assertRaises(SystemExit):
            TS.inject_job_ts((1, CODE_A, u"x", u"y", {}, TEXT_T, {}, u"seed", u"w"))

    def test_w_7_the_base_pair_is_p32e_then_p30e_only_inside_the_with(self):
        old = TS.RM.INJECT_PROFILES
        with TS.base_pair():
            self.assertEqual((u"P32E", u"P30E"), TS.RM.INJECT_PROFILES)
        self.assertEqual(old, TS.RM.INJECT_PROFILES)
        with self.assertRaises(RuntimeError):
            with TS.base_pair():
                raise RuntimeError("x")
        self.assertEqual(old, TS.RM.INJECT_PROFILES)
        old4 = RUN.base_status4
        with TS.t8_base_status():
            self.assertIs(TS.base_status_ts, RUN.base_status4)
            self.assertIs(TS.base_status_ts, RUN.t8_candidates4.__globals__["base_status4"])
        self.assertIs(old4, RUN.base_status4)

    def test_w_8_each_row_column_turns_true_to_false_with_a_broken_replacement(self):
        rows, _ = run_ts()
        # round-trip: 戻しが元に返らない
        orig = IJ.revert
        rows_rt, _ = run_ts(patches=((IJ, "revert", lambda *a, **k: u"x"),))
        self.assertTrue(rows_rt and all(r[u"round-trip"] is False for r in rows_rt))
        self.assertIs(orig, IJ.revert)
        # 読み直し: 読み直す関数が別の値を返す
        rows_rr, _ = run_ts(patches=((TS.JT, "reread_j", lambda *a, **k: False),))
        self.assertTrue(all(r[u"読み直し"] is False for r in rows_rr))
        # 届いた: 基準の span に元の字が無い
        rows_rc, _ = run_ts(patches=((TS.PS, "reached_of", lambda *a, **k: False),))
        self.assertTrue(all(r[u"届いた"] is False for r in rows_rc))
        # 対応の条件: 注入後の claim の値が違う
        inner = PSR.make_verify(TEXT_T)

        def shifted(zb, p, t):
            out = inner(zb, p, t)
            for c in out["claims"]:
                if c["state"] != PSR.G:
                    c["value"] = c["value"] + 1.0
            return out
        rows_v, _ = run_ts(verify=shifted)
        self.assertTrue(rows_v and all(r[u"P32E"][u"対応"] is False and r[PI.F_MISS % u"P32E"] == [PI.COND_I] for r in rows_v), [r[PI.F_MISS % u"P32E"] for r in rows_v][:3])
        self.assertTrue(all(r[u"P32E"][u"結果"] == TUNE.LABEL_UNMAPPED for r in rows_v))

    def test_w_9_a_changed_cap_or_a_dropped_type_changes_the_rows(self):
        base, _ = run_ts()
        no_t9, _ = run_ts(patches=((TS.PS, "t9_all_sites", lambda text, refs, seed, key: ({}, [])),))
        self.assertEqual([], [r for r in no_t9 if r[u"型"] == TYPES[3]])
        self.assertLess(len(no_t9), len(base))
        no_t5, _ = run_ts(patches=((TS.TY, "t5_all_sites", lambda text, refs, seed, key: ([], __import__("random").Random(0))),))
        self.assertEqual([], [r for r in no_t5 if r[u"型"] == TYPES[1]])
        no_t8, _ = run_ts(patches=((RUN, "t8_candidates4", lambda *a, **k: ([], {})),))
        self.assertEqual([], [r for r in no_t8 if r[u"型"] == TYPES[2]])

    def test_w_10_the_t1_status_uses_the_p32e_p30e_pair(self):
        seen = []
        orig = TS.RM.base_status_rb

        def spy(base_claims, base_by_id, tok, text):
            seen.append(TS.RM.INJECT_PROFILES)
            return orig(base_claims, base_by_id, tok, text)
        run_ts(patches=((TS.RM, "base_status_rb", spy),))
        self.assertTrue(seen)
        self.assertEqual({(u"P32E", u"P30E")}, set(seen))


class RunFlowTest(unittest.TestCase):
    u"""``run_states``・``run_inject`` の流れ(材料の置き場・切り替え 2 つ・記録の頭と中身)を、job だけ差し替えて通す。通信・cache・ZIP を使わない。"""

    def _books_in(self, calls):
        def load_books(root=ROOT, only=None, cache_dir=None):
            calls.append((only, cache_dir))
            return [(1, CODE_A, u"n", u"s", 3586, 64, {}, u"t")]
        return load_books

    def test_w_16_run_inject_runs_the_jobs_with_both_switches_true_and_writes_a_record_that_passes_the_check(self):
        import tempfile as tf
        seen, calls = [], []
        rows_a = [r for r in sample_inject()[u"行"] if r[u"証券コード"] == CODE_A]
        per_a = sample_inject()[u"本ごとの数え"][CODE_A]

        def job(args):
            seen.append((bool(getattr(N, TY.FLAG)), bool(getattr(S, TY.FLAG2))))
            return CODE_A, copy.deepcopy(rows_a), copy.deepcopy(per_a)
        with tf.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            pt.set(TS, "load_books", self._books_in(calls))
            pt.set(TS, "inject_job_ts", job)
            pt.set(GEN, "seed_value", lambda root=ROOT: (u"seed", {}))
            pt.set(TS, "caches_all", lambda: collections.OrderedDict())
            out = os.path.join(d, "rec", "inject.json")
            rec = TS.run_inject(only=CODE_A, out=out, say=lambda *a: None, work_root=d)
            on_disk = json.load(open(out, encoding="utf-8"))
            self.assertEqual(json.loads(json.dumps(rec)), on_disk)
            self.assertEqual([(True, True)], seen)
            self.assertEqual([(CODE_A, os.path.join(d, "rec", "cache"))], [(a, b) for a, b in calls])      # --out の folder の cache を材料の置き場にする
            self.assertEqual([], inject_problems(on_disk, full=False))
            self.assertEqual({u"名前": TY.FLAG, u"inject の中の値": True, u"出たあとの値": False, u"T5 の切り替えの名前": TY.FLAG2, u"T5 の切り替え inject の中の値": True,
                              u"T5 の切り替え 出たあとの値": False, u"配線の問題": []}, dict(on_disk[u"切り替え"]))
            self.assertEqual(CAP, on_disk[u"cap"])
        self.assertFalse(getattr(N, TY.FLAG))
        self.assertFalse(getattr(S, TY.FLAG2))

    def test_w_17_run_inject_refuses_a_true_switch_at_the_start_and_restores_a_leaked_one(self):
        import tempfile as tf
        with tf.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            pt.set(TS, "load_books", self._books_in([]))
            pt.set(GEN, "seed_value", lambda root=ROOT: (u"seed", {}))
            pt.set(TS, "caches_all", lambda: collections.OrderedDict())
            with TS.NS.yen_scan_on():
                with self.assertRaises(SystemExit):
                    TS.run_inject(only=CODE_A, out=os.path.join(d, "a.json"), say=lambda *a: None, work_root=d)
            with TS.TY.t5_yen_on():
                with self.assertRaises(SystemExit):
                    TS.run_inject(only=CODE_A, out=os.path.join(d, "b.json"), say=lambda *a: None, work_root=d)
            self.assertFalse(os.path.exists(os.path.join(d, "a.json")))
            self.assertFalse(os.path.exists(os.path.join(d, "b.json")))

            def leaking(args):
                setattr(N, TY.FLAG, True)                                   # job が切り替えを戻さなくても、with を出るときに戻る(出たあとは偽)
                return CODE_A, [], {}
            pt.set(TS, "inject_job_ts", leaking)
            try:
                TS.run_inject(only=CODE_A, out=os.path.join(d, "c.json"), say=lambda *a: None, work_root=d)
                self.assertFalse(getattr(N, TY.FLAG))
                self.assertFalse(getattr(S, TY.FLAG2))
            finally:
                setattr(N, TY.FLAG, False)

    def test_w_18_run_states_writes_a_record_that_passes_the_check_and_follows_the_material_folder(self):
        import tempfile as tf
        calls = []
        books = sample_books()

        def job(args):
            return copy.deepcopy(books[0])
        with tf.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            pt.set(TS, "load_books", self._books_in(calls))
            pt.set(TS, "states_job", job)
            pt.set(TS, "caches_all", lambda: collections.OrderedDict())
            out = os.path.join(d, "states.json")
            rec = TS.run_states(only=CODE_A, out=out, cache=os.path.join(d, "mycache"), say=lambda *a: None)
            on_disk = json.load(open(out, encoding="utf-8"))
            self.assertEqual(json.loads(json.dumps(rec)), on_disk)
            self.assertEqual([(CODE_A, os.path.join(d, "mycache"))], calls)                       # --cache が先
            self.assertEqual([], states_problems(on_disk, full=False))
            self.assertEqual(list(TS.engine_profiles_now()), on_disk[u"profile"])
            self.assertEqual(1, on_disk[u"社の数"])
            with self.assertRaises(SystemExit):                                                   # 出力が既に在る
                TS.run_states(only=CODE_A, out=out, say=lambda *a: None)

    def test_w_19_the_cache_folder_is_checked_before_and_after_and_a_change_stops_without_a_record(self):
        import tempfile as tf
        snaps = iter([collections.OrderedDict([(u"edinet", {u"件数": 1})]), collections.OrderedDict([(u"edinet", {u"件数": 2})])])
        with tf.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            pt.set(TS, "load_books", self._books_in([]))
            pt.set(TS, "states_job", lambda args: copy.deepcopy(sample_books()[0]))
            pt.set(TS.GEN, "caches_snapshot", lambda existing=None: next(snaps))
            with self.assertRaises(SystemExit):
                TS.run_states(only=CODE_A, out=os.path.join(d, "s.json"), say=lambda *a: None)
            self.assertFalse(os.path.exists(os.path.join(d, "s.json")))


class with_p33e(object):
    u"""``V.PROFILES`` に P33E が無ければ(P32E の写しで)足し、出るときに元へ戻す。P33E が在る木では何もしない。"""

    def __enter__(self):
        self.added = u"P33E" not in V.PROFILES
        if self.added:
            V.PROFILES[u"P33E"] = V.PROFILES[u"P32E"]
        return self

    def __exit__(self, *a):
        if self.added:
            del V.PROFILES[u"P33E"]
        return False


class FourProfileTest(unittest.TestCase):
    u"""engine に P33E が在る木でも無い木でも、4 つ目の profile の列が記録・集計・H の欄・判定の全部に届く(P33E を足して通す)。"""

    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_p_1_a_four_profile_record_is_green_and_the_fourth_column_is_in_every_aggregate(self):
        with with_p33e():
            profiles = list(TS.engine_profiles_now())
            self.assertEqual([u"P27", u"P30E", u"P32E", u"P33E"], profiles)
            rec = sample_states(profiles)
            self.assertEqual(profiles, rec[u"profile"])
            self.assertEqual(profiles, list(rec[u"集計"]))
            self.assertEqual([], states_problems(rec, full=False))
            self.assertEqual([], totals_problems(rec))
            fours = [tuple(rec[u"集計"][p][u"4 state"].values()) for p in profiles]
            self.assertEqual(4, len(set(fours)))                                                  # P33E の列は P32E の写しでない
            for b in rec[u"本"]:
                self.assertEqual(profiles, list(b[u"profile"]))
                self.assertEqual(profiles, list(b[u"対応"]))
            R = collections.OrderedDict([("fetch", sample_fetch()), ("states", rec), ("inject", sample_inject())])
            self.assertEqual([], judge_problems(R, self.seal))

    def test_p_2_dropping_or_copying_the_fourth_column_turns_the_check_red(self):
        with with_p33e():
            profiles = list(TS.engine_profiles_now())
            rec = sample_states(profiles)
            R1 = copy.deepcopy(rec)
            R1[u"集計"].pop(u"P33E")                                                                # 集計から 4 つ目を落とす
            self.assertNotEqual([], states_problems(R1, full=False))
            self.assertNotEqual([], totals_problems(R1))
            R2 = copy.deepcopy(rec)
            R2[u"集計"][u"P33E"] = copy.deepcopy(R2[u"集計"][u"P32E"])                              # P33E の列を P32E の写しにする
            self.assertNotEqual([], totals_problems(R2))
            R3 = copy.deepcopy(rec)
            for b in R3[u"本"]:
                b[u"profile"][u"P33E"] = copy.deepcopy(b[u"profile"][u"P32E"])
            self.assertNotEqual([], states_problems(R3, full=False))                              # ブロックを写しにしても集計が合わない
            rebuild_states(R3)
            self.assertEqual([], states_problems(R3, full=False))                                 # 集計も作り直せば整合(写しという事実は別の試験が見る)
            R4 = copy.deepcopy(rec)
            for b in R4[u"本"]:
                b[u"profile"].pop(u"P33E")
            self.assertNotEqual([], states_problems(R4, full=False))                              # 本が 3 profile のまま(engine は 4 つを期待する)
            R5 = copy.deepcopy(rec)
            R5[u"profile"] = [u"P27", u"P30E", u"P32E"]
            self.assertNotEqual([], states_problems(R5, full=False))

    def test_p_3_states_job_gives_each_profile_its_own_rows_and_p33e_is_not_a_copy_of_p32e(self):
        sents = [u"文です。"]
        by_profile = {u"P27": (G, UNV), u"P30E": (G, VM), u"P32E": (VM, VM), u"P33E": (G, G)}

        def verify(zb, p, t):
            return {"claims": [{"id": "N00%d" % (i + 1), "kind": "num", "state": st, "reason": None, "pointers": [], "span": u"x", "unit": u"円"} for i, st in enumerate(by_profile[p])]}
        raws = [{"id": "N001", "sentence": 0, "pos": 1}, {"id": "N002", "sentence": 0, "pos": 5}]
        with with_p33e(), Patch() as pt:
            pt.set(TS.GEN, "read_zip", lambda row, caches=None: b"zip")
            pt.set(TS.PR, "build_modified_zip", lambda zb, text: (b"zm",))
            pt.set(TS.VD, "verify_document", verify)
            pt.set(TS.R, "build_raw_claims", lambda zm, prof: (raws, []))
            pt.set(TS.RUN, "sentence_list", lambda zm, prof: sents)
            profiles = (u"P27", u"P30E", u"P32E", u"P33E")
            book = TS.states_job((1, CODE_A, u"n", u"s", 3, 2, {}, u"abc", profiles))
        self.assertEqual(list(profiles), list(book[u"profile"]))
        got = dict((p, tuple(book[u"profile"][p][u"4 state"][st] for st in STATES)) for p in profiles)
        self.assertEqual({u"P27": (1, 0, 1, 0), u"P30E": (1, 1, 0, 0), u"P32E": (0, 2, 0, 0), u"P33E": (2, 0, 0, 0)}, got)
        self.assertNotEqual(got[u"P33E"], got[u"P32E"])
        self.assertEqual({u"P27": True, u"P30E": True, u"P32E": True, u"P33E": True}, dict(book[u"対応"]))
        self.assertEqual([[0, 1, G, VM, u"なし", u"なし"]], book[u"P30E から P32E で動いた行"])           # 動いた行は P30E → P32E だけ(P33E は入らない)
        self.assertEqual([], states_problems_for_book(book))


class StatesProcedureTest(unittest.TestCase):
    def test_w_11_the_state_counts_and_reason_counts_follow_the_rows(self):
        rows = [srow(1, 1, G), srow(1, 2, UNV, u"no_subject"), srow(1, 3, UNV, u"no_subject"), srow(1, 4, PNF, u"no_element")]
        self.assertEqual({G: 1, VM: 0, UNV: 2, PNF: 1}, dict(TS.state_counts(rows)))
        rc = TS.reason_counts(rows)
        self.assertEqual({u"no_subject": 2}, dict(rc[UNV]))
        self.assertEqual({u"なし": 1}, dict(rc[G]))
        blk = TS.profile_block(rows)
        self.assertEqual(4, blk[u"claim"])
        self.assertEqual(rows, blk[u"行"])

    def test_w_11b_h9_counts_the_sentences_that_start_with_a_pipe_not_those_that_contain_one(self):
        u"""states_job の ``行頭が | の文の数``。行頭でない位置に | を持つ文(行頭の空白の後ろ・文の途中・末尾)は数えない。"""
        sents = [u"| 見出し | 前期 | 当期 |", u"|売上|100|", u"売上高は | 区切り を含む文です。", u"通常の文です。", u" | 先頭に空白の後ろ", u"a|b", u"末尾の|"]
        claims = [{"id": "N001", "kind": "num", "state": G, "reason": None, "pointers": [], "span": u"x", "unit": u"円"}]
        raws = [{"id": "N001", "sentence": 0, "pos": 1}]
        with Patch() as pt:
            pt.set(TS.GEN, "read_zip", lambda row, caches=None: b"zip")
            pt.set(TS.PR, "build_modified_zip", lambda zb, text: (b"zm",))
            pt.set(TS.VD, "verify_document", lambda zb, p, t: {"claims": claims})
            pt.set(TS.R, "build_raw_claims", lambda zm, prof: (raws, []))
            pt.set(TS.RUN, "sentence_list", lambda zm, prof: sents)
            book = TS.states_job((1, CODE_A, u"n", u"s", 3, 1, {}, u"abc", (u"P27", u"P30E", u"P32E")))
        self.assertEqual(2, book[u"行頭が | の文の数"])
        self.assertEqual(7, book[u"文の数"])
        self.assertEqual(3, book[u"概況の字数"])
        self.assertEqual([], states_problems_for_book(book))

    def test_w_12_the_profiles_follow_the_engine(self):
        self.assertEqual((u"P27", u"P30E", u"P32E") + ((u"P33E",) if u"P33E" in V.PROFILES else ()), TS.engine_profiles_now())
        old = dict(V.PROFILES)
        try:
            V.PROFILES["P33E"] = V.PROFILES["P32E"]
            self.assertEqual((u"P27", u"P30E", u"P32E", u"P33E"), TS.engine_profiles_now())
        finally:
            V.PROFILES.clear()
            V.PROFILES.update(old)
        self.assertEqual(old.keys(), V.PROFILES.keys())

    def test_w_13_the_move_entry_and_the_diff_come_from_the_pb_functions(self):
        a = {(1, 1): (UNV, u"r", ("xbrl:x@CurrentYearInstant",), u"%"), (1, 2): (G, None, ("xbrl:y@CurrentYearInstant",), u"%"), (1, 3): (G, None, (), u"%")}
        b = {(1, 1): (VM, None, ("xbrl:x@Prior1YearInstant",), u"%"), (1, 2): (G, None, ("xbrl:z@CurrentYearInstant",), u"%"), (1, 3): (G, u"r2", (), u"%")}
        common, moved, reason_only = TS.PB.diff_rows(a, b)
        self.assertEqual([(1, 1), (1, 2)], moved)                                        # state か pointers が違う行
        self.assertEqual([(1, 3)], reason_only)
        self.assertEqual([1, 1, UNV, VM, u"CurrentYear", u"Prior1Year"], TS.move_entry((1, 1), a[(1, 1)], b[(1, 1)]))
        self.assertEqual([1, 2, G, G, u"CurrentYear", u"CurrentYear"], TS.move_entry((1, 2), a[(1, 2)], b[(1, 2)]))   # pointers だけが違う行は期も同じ

    def test_w_14_the_record_dump_puts_one_claim_per_line_and_round_trips(self):
        R = sample_records()
        text = TS.dumps_states(R["states"])
        self.assertEqual(json.loads(text), json.loads(json.dumps(R["states"], ensure_ascii=False)))
        row_lines = [ln for ln in text.splitlines() if ln.strip().startswith("[") and ln.strip().endswith(("],", "]")) and ln.count("[") == 1 and ln.strip().startswith('[')]
        self.assertTrue(any(ln.strip().startswith('[1, 5, "GROUNDED"') for ln in text.splitlines()))
        self.assertGreater(len(row_lines), 10)


class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_d_1_the_sample_document_is_green_and_a_changed_character_turns_it_red(self):
        R = norm(sample_records())
        doc = sample_doc(R, self.seal)
        self.assertEqual([], doc_problems(doc, R, self.seal))
        lines = doc.split(u"\n")
        for key in (u"| H-3 |", u"| H-9 |", u"| P32E |"):
            row = [i for i, ln in enumerate(lines) if ln.startswith(key)][0]
            mutated = lines[:]
            mutated[row] = mutated[row][:-3] + u"x" + mutated[row][-2:]
            self.assertNotEqual([], doc_problems(u"\n".join(mutated), R, self.seal), key)
        row = [i for i, ln in enumerate(lines) if ln.startswith(u"| H-2 |")][0]
        mutated = lines[:]
        mutated[row] = mutated[row].replace(u"当たり", u"外れ") if u"当たり" in mutated[row] else mutated[row].replace(u"外れ", u"当たり")
        self.assertNotEqual([], doc_problems(u"\n".join(mutated), R, self.seal))

    def test_d_2_a_forbidden_word_a_docid_a_foreign_table_or_an_ungated_number_turns_it_red(self):
        R = norm(sample_records())
        doc = sample_doc(R, self.seal)
        for w in FOR_RESULT_WORDS:
            self.assertNotEqual([], doc_problems(doc + u"\n" + w + u"\n", R, self.seal), w)
        self.assertNotEqual([], doc_problems(doc + u"\nS100" + u"ABCD\n", R, self.seal))
        self.assertNotEqual([], doc_problems(doc + u"\n<!-- 門:start other -->\nx\n<!-- 門:end -->\n", R, self.seal))
        self.assertNotEqual([], doc_problems(doc + u"\n通した行は 123 件でした。\n", R, self.seal))
        self.assertEqual([], doc_problems(doc + u"\n通した行は 123 件でした。" + NOT_GATED + u"\n", R, self.seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"<!-- 門:start pred -->", u"<!-- 門:start pred2 -->"), R, self.seal))

    def test_d_3_the_tables_follow_the_record_and_h10_reads_the_commander(self):
        R = norm(sample_records())
        doc = sample_doc(R, self.seal)
        self.assertIn(u"司令塔が読む", doc)
        R2 = norm(sample_records())
        R2["states"][u"本"][0][u"profile"][u"P32E"][u"行"][0][2] = VM
        rebuild_states(R2["states"])
        self.assertNotEqual([], doc_problems(doc, R2, self.seal))
        R3 = norm(sample_records())
        R3["inject"][u"行"][0][u"P32E"] = dict(R3["inject"][u"行"][0][u"P32E"], 結果=TUNE.LABEL_PASS)
        self.assertNotEqual([], doc_problems(doc, R3, self.seal))


# ================================================================ f. 順序
class OrderMutationTest(unittest.TestCase):
    def _repo(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        r.put("measure/s.py")
        r.commit("measure/s.py")
        return r, s

    def test_e_1_good_order_is_green(self):
        r, s = self._repo()
        r.put("rec.json")
        r.put("docs/doc.md")
        r.commit("rec.json", "docs/doc.md")
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], ["rec.json", "docs/doc.md"]))

    def test_e_2_records_before_the_seal_or_uncommitted_are_red(self):
        r, s = self._repo()
        r.put("rec.json")
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], ["rec.json"]))          # 未 commit
        r2 = PR.Repo()
        r2.put("rec.json")
        r2.commit("rec.json")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["rec.json"]))        # 封より前

    def test_e_3_a_wrong_seal_is_red(self):
        r, s = self._repo()
        r.put("rec.json")
        r.commit("rec.json")
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], ["rec.json"]))


# ================================================================ 本番の記録(無ければ skip。skip でも行が出る)
class RealRecordsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def setUp(self):
        if not records_exist():
            self.skipTest(u"本番の記録が無い(取得・states・inject を走らせたあとに緑になる)")

    def test_r_1_records_are_clean_and_consistent(self):
        self.assertEqual([], record_problems(load_records(), full=True))

    def test_r_2_judgment_is_rebuilt_from_the_records(self):
        R = load_records()
        self.assertEqual([], judge_problems(R, self.seal))
        self.assertEqual(u"司令塔が読む", TS.build_H(R, self.seal)["judge"]["H-10"])

    def test_r_3_the_result_document_follows_the_records(self):
        if not os.path.exists(os.path.join(ROOT, DOC_REL)):
            self.skipTest(u"結果の文書がまだ無い")
        self.assertEqual([], doc_problems(read(DOC_REL), load_records(), self.seal))

    def test_r_4_order_is_seal_then_records_and_document(self):
        self.assertEqual([], order_of())


class SkipLineTest(unittest.TestCase):
    def test_s_1_a_skipped_real_record_test_still_prints_a_line(self):
        FORCE["no_records"] = True
        try:
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(RealRecordsTest)
            stream = io.StringIO()
            res = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        finally:
            FORCE["no_records"] = False
        out = stream.getvalue()
        self.assertEqual(4, res.testsRun)
        self.assertEqual(4, len(res.skipped))
        self.assertEqual(4, len([ln for ln in out.splitlines() if "... skipped" in ln]))
        self.assertTrue(res.wasSuccessful())


if __name__ == "__main__":
    unittest.main()
