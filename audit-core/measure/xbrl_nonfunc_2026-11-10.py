# -*- coding: utf-8 -*-
u"""封 docs/XBRL_NONFUNCTIONAL_SEAL_2026-11-10.md §1・§2・§4 ― engine の非機能の実測 NF(verify_document 1 回の時間とメモリ)の測定と、結果の表(tally)。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。** engine(``core/``・``adapters/``)・``measure/lib``・前の便の script・記録・門は 1 行も変えない。

    python3 measure/xbrl_nonfunc_2026-11-10.py run   [--only <docID>] [--out PATH] [--reps N]   # 全部の回を測り fixtures/xbrl/nonfunc/timing_2026-11-10.json に書く(出力が既に在れば止まる)
    python3 measure/xbrl_nonfunc_2026-11-10.py tally [--root DIR]                               # 記録から N-1〜N-9 の表と、材料 × profile の数の表を出す(file は書かない)

``--only`` か ``--reps`` が 3 でない走らせ方は本番の記録ではない: ``--out`` を必ず指定する(指定が無ければ止める)。
本番の記録は、同じ機械で他の重い仕事(門・監査・生成)を止めて 1 回だけ走らせる(封 §0-2 の 3)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- 1 回 = ``multiprocessing`` の fork の ``Pool(1, maxtasksperchild=1)`` が起こす子 process 1 つ。並行なし(Pool は 1 本だけ・``map`` の chunksize 1)。
  子の中で入力(ZIP の bytes・AI の文)を読み(時計の外)、``measure_call`` が ``verify_document(zb, profile, text)`` の前後で ``time.perf_counter``・``time.process_time``・``resource.getrusage(RUSAGE_SELF).ru_maxrss`` を読む。
  時計の内側は ``verify_document`` の呼び出し 1 つだけ(門が ast と振る舞いで見る)。
- 順は (回, 材料の種類, 本, profile)。回 → 97 書類(原文・text なし。``R97.make_jobs`` の順)→ AI の文 200 本(``RM.load_jobs`` の順)。本ごとに P27 → P33E。
- ``ru_maxrss`` の単位: macOS は byte、それ以外は KB なので ``RSS_UNIT``(darwin 1・他 1024)を掛けて byte にして記録する。MB は 2 の 20 乗 byte(= MiB)で、封の「MB」の字をこう読む(下見と同じ)。
- 1 claim あたりの時間 = 1 回の時間 ÷ ``out["claims"]`` の長さ。1 行でも claim が 0 なら N-4 は値なし = 外れ(分母 0 は外れ)。
- N-4 の中央値 = 行ごとの (時間 ÷ claim の数 × 1000) の中央値。N-7 の揺れ = 同じ (材料の種類, 本, profile) の回の (最大 − 最小) ÷ 中央値。その中央値は全部の (本, profile) の揺れの中央値。
- N-9 は 回 1 の行だけを足す(claim の数は回で変わらない。門が回の間の一致を見る)。97 書類は ``out["claims"]`` の長さ(原文は全部が数の claim)、AI の文は数の claim(kind が num)。
- 判定は丸めない値で幅と比べ、表には桁を決めて(秒 3 桁・ms 2 桁・MB 1 桁・比 3 桁・% 1 桁)出す。幅の外が 1 つでも在る欄は外れ。値が無い(分母 0・材料の穴)欄は外れ。
- import の時間(§1 の 4)= 親が ``subprocess`` で新しい python を 5 回起こし、起動の直前から終わりまでの ``perf_counter`` の差(秒)。5 回の中央値を N-8 に使う。測るのは主の測定の前(親が先に読み込んで pyc が在る状態)。
- 記録は文・要素名・会社名を持たない。行は 材料の種類・本の id・profile・回・時間・CPU 時間・ru_maxrss の前後・claim の数・入力の byte 数だけ。docID(97 書類・AI の本の名)は ``LATER_NAMING_FILES`` に宣言された記録だけ。
"""
from __future__ import print_function

import argparse
import collections
import contextlib
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
import platform
import re
import resource
import statistics
import subprocess
import sys
import time

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


PB = load_module("xbrl_pbind_2026-11-06.py", "pbind_for_nonfunc")
RM, R97, D = PB.RM, PB.R97, PB.D
NF, GEN, RUN = PB.NF, PB.GEN, PB.RUN
Stop = GEN.Stop

from adapters.xbrl import verify_document as VD       # noqa: E402

SEAL_REL = "docs/XBRL_NONFUNCTIONAL_SEAL_2026-11-10.md"
SEAL_COMMIT = "abe8f4d"
DOC_REL = "docs/XBRL_NONFUNCTIONAL_RESULT_2026-11-10.md"
SCRIPT_REL = "measure/xbrl_nonfunc_2026-11-10.py"
REC_REL = "fixtures/xbrl/nonfunc/timing_2026-11-10.json"
PROFILES = ("P27", "P33E")
KIND_DOC, KIND_AI = u"書類", u"AI の文"
KINDS = (KIND_DOC, KIND_AI)
#: 本番の記録の回数(封 §0-2 の 3)。import の時間を測る回数(封 §1 の 4)
REPS_PROD = 3
IMPORT_REPS = 5
#: ru_maxrss を byte にする掛け率(macOS は byte、他は KB)。MB = 2 の 20 乗 byte
RSS_UNIT = 1 if sys.platform == "darwin" else 1024
MB = 1048576
HIT, MISS = PB.HIT, PB.MISS
ROW_KEYS = (u"材料の種類", u"本の id", u"profile", u"回", u"時間", u"CPU 時間", u"ru_maxrss の前", u"ru_maxrss の後", u"claim の数", u"数の claim の数", u"zip の byte 数", u"文の byte 数")
LIMITS = (
    u"数はこの 1 台(Apple M2・macOS 13.4・Python 3.9.6)の、この日の 1 回の走り。他の機械・OS・python・負荷では測っていない",
    u"並行の処理(何書類を同時に回せるか・throughput)は測っていない。1 process ずつ直列で測った",
    u"材料は手元の 97 書類と AI の文 200 本だけ。これより大きい書類・PDF・他の形式は測っていない",
    u"ru_maxrss は子 process の最大の常駐の量で、fork の親と共有する頁の数え方は OS に依る。呼び出し 1 回だけのメモリを切り出した量ではない",
    u"有料の API・通信は使っていない。LLM の席の時間・費用は含まない",
    u"import の時間は親が先に engine を読み込んだ後(pyc が在る状態)に新しい python を 5 回起こして測った")


def key_leaks_nf(gen):
    u"""``gen.key_leaks`` の版: この便の封の path(32 字以上の英数字・_・- の連なり)を除いて元の検査に渡す。"""
    orig = gen.key_leaks

    def fn(text, key_value=None, long_alnum=True):
        return orig(text.replace(SEAL_REL, u""), key_value, long_alnum)
    return fn


@contextlib.contextmanager
def key_check_nf(gen):
    u"""``gen.key_leaks`` を with の中だけこの便の封の path を除く版にする。出るときは必ず戻す(PB の便の ``key_check_pb`` と同じ形。PB の版は PB の封の path を除く)。"""
    old = gen.key_leaks
    gen.key_leaks = key_leaks_nf(gen)
    try:
        yield
    finally:
        gen.key_leaks = old


def median(xs):
    return statistics.median(xs) if xs else None


# ======================================================================================================
# 1 回の測定(子 process の中)
def rss_bytes():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * RSS_UNIT


def measure_call(zb, text, prof):
    u"""verify_document 1 回の時間・CPU 時間・ru_maxrss の前後・claim の数。**時計の内側は verify_document の呼び出し 1 つだけ**(入力は呼ぶ側が先に読む)。"""
    r0 = rss_bytes()
    t0 = time.perf_counter()
    c0 = time.process_time()
    out = VD.verify_document(zb, prof, text)
    c1 = time.process_time()
    t1 = time.perf_counter()
    r1 = rss_bytes()
    claims = out["claims"]
    return {"wall": t1 - t0, "cpu": c1 - c0, "rss_before": r0, "rss_after": r1, "claims": len(claims), "num": sum(1 for c in claims if c["kind"] == "num")}


def read_input(kind, ref):
    u"""時計の外で入力を読む。(zb, text)。書類は原文(text なし)、AI の文は text つき。"""
    if kind == KIND_DOC:
        _doc, zpath, expect = ref
        with io.open(zpath, "rb") as fh:
            zb = fh.read()
        if hashlib.sha256(zb).hexdigest() != expect:
            raise Stop(u"**ZIP の sha256 が記録と違う。止める**")
        return zb, None
    name, item, row, text_dir, zip_caches = ref
    zb = GEN.read_zip(row, zip_caches)
    return zb, RUN.read_text(name, item, text_dir)


def child_job(arg):
    u"""fork した子 process 1 つの中で呼ばれる 1 回。入力を読み(時計の外)、測って、plain data を返す。"""
    kind, ref, prof = arg
    zb, text = read_input(kind, ref)
    res = measure_call(zb, text, prof)
    res["zip_bytes"] = len(zb)
    res["text_bytes"] = len(text.encode("utf-8")) if text is not None else None
    return res


def run_pool(args):
    u"""全部の回を 1 本の Pool(1, maxtasksperchild=1) で直列に測る(1 回 = 子 process 1 つ。並行なし)。"""
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(1, maxtasksperchild=1) as pool:
        return pool.map(child_job, args, chunksize=1)


# ======================================================================================================
# 材料・機械・import
def doc_items(only=None):
    u"""97 書類(``R97.make_jobs`` の順)。[(docID, zip の path, 期待の sha256)]。"""
    jobs, _ids67, _ids30 = R97.make_jobs(PROFILES[:1])
    out = [(j[0], j[4], j[2]) for j in jobs]
    if only is not None:
        out = [x for x in out if x[0] == only]
        if not out:
            raise Stop(u"**--only の docID が 97 書類に無い。止める**")
    return out


def book_items(root=ROOT, only=None):
    u"""AI の文 200 本(``RM.load_jobs`` の順)。[(本の名, (名, item, row, 文の folder, zip の cache))]。"""
    out = []
    for j in RM.load_jobs(root, only):
        _src, name, item, row, text_dir, zip_caches = j[:6]
        out.append((name, (name, item, row, text_dir, zip_caches)))
    return out


def sysctl(key):
    try:
        r = subprocess.run(["sysctl", "-n", key], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return r.stdout.decode("utf-8", "replace").strip() if r.returncode == 0 else None
    except OSError:
        return None


def machine():
    mem = sysctl("hw.memsize")
    return collections.OrderedDict([(u"CPU の名", sysctl("machdep.cpu.brand_string")), (u"コア数", os.cpu_count()), (u"メモリ(byte)", int(mem) if mem and mem.isdigit() else None),
                                    (u"OS", platform.platform()), (u"python", platform.python_version()), (u"ru_maxrss の単位", u"byte(macOS)" if sys.platform == "darwin" else u"KB を 1024 倍して byte にした")])


def import_times(root=ROOT, reps=IMPORT_REPS):
    u"""``import adapters.xbrl.verify_document`` だけを新しい python で ``reps`` 回。子 process の起動の直前から終わりまでの perf_counter の差(秒)。"""
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([root, os.path.join(root, "core", "py")]))
    out = []
    for _ in range(reps):
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, "-c", "import adapters.xbrl.verify_document"], cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t1 = time.perf_counter()
        if r.returncode != 0:
            raise Stop(u"**import の測定の子が失敗した(rc %d)。止める**" % r.returncode)
        out.append(round(t1 - t0, 6))
    return out


def job_args(docs, books, reps):
    u"""全部の回の引数と行の頭(材料の種類・本の id・profile・回)。順は (回, 材料の種類, 本, profile)。"""
    args, heads = [], []
    for rep in range(1, reps + 1):
        for doc, zpath, expect in docs:
            for p in PROFILES:
                args.append((KIND_DOC, (doc, zpath, expect), p))
                heads.append((KIND_DOC, doc, p, rep))
        for name, ref in books:
            for p in PROFILES:
                args.append((KIND_AI, ref, p))
                heads.append((KIND_AI, name, p, rep))
    return args, heads


def make_row(head, res):
    kind, ident, prof, rep = head
    return collections.OrderedDict([
        (u"材料の種類", kind), (u"本の id", ident), (u"profile", prof), (u"回", rep), (u"時間", round(res["wall"], 6)), (u"CPU 時間", round(res["cpu"], 6)),
        (u"ru_maxrss の前", res["rss_before"]), (u"ru_maxrss の後", res["rss_after"]), (u"claim の数", res["claims"]), (u"数の claim の数", res["num"]),
        (u"zip の byte 数", res["zip_bytes"]), (u"文の byte 数", res["text_bytes"])])


def run(root=ROOT, only=None, out=None, reps=REPS_PROD, say=print):
    production = out is None
    if production:
        if only is not None or reps != REPS_PROD:
            raise Stop(u"**--only か --reps 3 以外を付けた走らせ方は本番の記録を作らない。--out を指定する。止める**")
        out = os.path.join(root, REC_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    if not isinstance(reps, int) or reps < 1:
        raise Stop(u"**--reps は 1 以上の整数。止める**")
    docs = doc_items(only)
    books = book_items(root, only)
    caches = RM.caches_all()
    before = GEN.caches_snapshot(caches)
    say(u"書類 %d・AI の文 %d 本 × profile %d × %d 回 = %d 回(子 process 1 つずつ・並行なし)" % (len(docs), len(books), len(PROFILES), reps, (len(docs) + len(books)) * len(PROFILES) * reps))
    imports = import_times(root)
    args, heads = job_args(docs, books, reps)
    res = run_pool(args)
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rows = [make_row(h, r) for h, r in zip(heads, res)]
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"非機能の実測 NF ― verify_document 1 回の時間とメモリ(0 USD)"
    rec[u"HEAD の commit"] = GEN.git_head(os.path.dirname(root))
    rec[u"この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    rec[u"engine の指紋"] = VD.engine_fingerprint()
    rec[u"機械"] = machine()
    rec[u"範囲"] = u"全部(97 書類・AI の文 200 本)" if only is None else u"**--only の docID だけ(本番の記録ではない)**"
    rec[u"回数"] = reps
    rec[u"profile"] = list(PROFILES)
    rec[u"cache の前後"] = collections.OrderedDict([(u"前", before), (u"後", after), (u"変化なし", before == after)])
    rec[u"import の時間"] = collections.OrderedDict([(u"回数", IMPORT_REPS), (u"秒", imports)])
    rec[u"欄"] = collections.OrderedDict([
        (u"時間", u"verify_document 1 回の perf_counter の差(秒)。入力の読み込みは時計の外"), (u"CPU 時間", u"同じ区間の process_time の差(秒)"),
        (u"ru_maxrss の前・後", u"呼び出しの前と後の子 process の ru_maxrss(byte)。macOS は byte で、他の OS は KB を 1024 倍した"),
        (u"claim の数", u"out[\"claims\"] の長さ(全部)。数の claim の数は kind が num のもの"), (u"入力の byte 数", u"zip の byte 数と文の byte 数(書類は文なし = null)"),
        (u"順", u"(回, 材料の種類, 本, profile)。回 → 97 書類 → AI の文 200 本。本ごとに P27 → P33E")])
    rec[u"行"] = rows
    rec[u"限界"] = list(LIMITS)
    rec[u"key_leaks"] = D.record_key_leaks(rec)
    if rec[u"key_leaks"]:
        raise Stop(u"記録に鍵が入った")
    with key_check_nf(GEN):
        RUN.write_record(out, json.dumps(rec, ensure_ascii=False, indent=1) + u"\n", rec, None)
    say(u"-> %s(行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
# tally: 封の字から幅を読み、記録から N-1〜N-9 を判定する
def read_seal(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def seal_pred_rows(seal):
    u"""封 §2 の表の行 {N-n: (欄, 予測, 外れ方)}。"""
    sec = seal[seal.index("## §2"):seal.index("## §3")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| (N-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            out[m.group(1)] = (cells[0], cells[1], cells[2] if len(cells) > 2 else u"")
    return out


def _f(s):
    return float(s.replace(",", ""))


def seal_bounds(seal):
    u"""封の字から予測の幅を読む(字のコピーにしない)。形が違えば例外 = 赤。"""
    P = seal_pred_rows(seal)
    b = collections.OrderedDict()
    m = re.match(r"^([\d.]+)〜([\d.]+) 秒$", P["N-1"][1].strip())
    b["N-1"] = (_f(m.group(1)), _f(m.group(2)))
    m = re.match(r"^([\d.]+)〜([\d.]+)$", P["N-2"][1].strip())
    b["N-2"] = (_f(m.group(1)), _f(m.group(2)))
    m = re.match(r"^([\d.]+) 秒以下$", P["N-3"][1].strip())
    b["N-3"] = _f(m.group(1))
    m = re.match(r"^([\d.]+)〜([\d.]+) ms$", P["N-4"][1].strip())
    b["N-4"] = (_f(m.group(1)), _f(m.group(2)))
    m = re.match(r"^([\d.]+)〜([\d.]+) 秒 / ([\d.]+) 秒以下$", P["N-5"][1].strip())
    b["N-5"] = collections.OrderedDict([(u"中央値", (_f(m.group(1)), _f(m.group(2)))), (u"最大", _f(m.group(3)))])
    m = re.match(r"^([\d.]+)〜([\d.]+) MB / ([\d.]+) MB 以下$", P["N-6"][1].strip())
    b["N-6"] = collections.OrderedDict([(u"中央値", (_f(m.group(1)), _f(m.group(2)))), (u"最大", _f(m.group(3)))])
    m = re.match(r"^([\d.]+)% 以下$", P["N-7"][1].strip())
    b["N-7"] = _f(m.group(1))
    m = re.match(r"^([\d.]+) 秒以下$", P["N-8"][1].strip())
    b["N-8"] = _f(m.group(1))
    m = re.match(r"^([\d,]+) / ([\d,]+)", P["N-9"][1].strip())
    b["N-9"] = collections.OrderedDict([(u"書類", int(m.group(1).replace(",", ""))), (u"AI の文", int(m.group(2).replace(",", "")))])
    return b


def within(x, lo_hi):
    return x is not None and lo_hi[0] <= x <= lo_hi[1]


def atmost(x, hi):
    return x is not None and x <= hi


def select(rows, kind, prof):
    return [r for r in rows if r[u"材料の種類"] == kind and r[u"profile"] == prof]


def spreads(rows):
    u"""同じ (材料の種類, 本, profile) の回の (最大 − 最小) ÷ 中央値。中央値が 0 の群があれば None(分母 0)。"""
    g = collections.OrderedDict()
    for r in rows:
        g.setdefault((r[u"材料の種類"], r[u"本の id"], r[u"profile"]), []).append(r[u"時間"])
    out = []
    for ts in g.values():
        m = median(ts)
        if not m:
            return None
        out.append((max(ts) - min(ts)) / m)
    return out


def columns_from_rows(rows, imports):
    u"""記録の行から判定に使う数を数え直す(丸めない)。値が無い欄は None。"""
    d27, d33 = select(rows, KIND_DOC, "P27"), select(rows, KIND_DOC, "P33E")
    a33 = select(rows, KIND_AI, "P33E")
    t27, t33 = [r[u"時間"] for r in d27], [r[u"時間"] for r in d33]
    m27, m33 = median(t27), median(t33)
    per = [r[u"時間"] / r[u"claim の数"] * 1000.0 for r in d27] if d27 and all(r[u"claim の数"] > 0 for r in d27) else None
    ta = [r[u"時間"] for r in a33]
    rss = [r[u"ru_maxrss の後"] / float(MB) for r in rows]
    sp = spreads(rows)
    c = collections.OrderedDict()
    c["N-1"] = m27
    c["N-2"] = (m33 / m27) if m27 and m33 is not None else None
    c["N-3"] = max(t27) if t27 else None
    c["N-4"] = median(per) if per else None
    c["N-5"] = collections.OrderedDict([(u"中央値", median(ta)), (u"最大", max(ta) if ta else None)])
    c["N-6"] = collections.OrderedDict([(u"中央値", median(rss)), (u"最大", max(rss) if rss else None)])
    c["N-7"] = (median(sp) * 100.0) if sp else None
    c["N-8"] = median(imports) if imports else None
    c["N-9"] = collections.OrderedDict([(u"書類", sum(r[u"claim の数"] for r in d27 if r[u"回"] == 1) if d27 else None),
                                        (u"AI の文", sum(r[u"数の claim の数"] for r in a33 if r[u"回"] == 1) if a33 else None)])
    return c


def judge_from(cols, seal):
    u"""cols = ``columns_from_rows`` の値。{N-n: {判定, 値}}。"""
    B = seal_bounds(seal)
    E = collections.OrderedDict()

    def put(k, ok, val):
        E[k] = {u"判定": HIT if ok else MISS, u"値": val}
    put("N-1", within(cols["N-1"], B["N-1"]), cols["N-1"])
    put("N-2", within(cols["N-2"], B["N-2"]), cols["N-2"])
    put("N-3", atmost(cols["N-3"], B["N-3"]), cols["N-3"])
    put("N-4", within(cols["N-4"], B["N-4"]), cols["N-4"])
    v5, b5 = cols["N-5"], B["N-5"]
    put("N-5", within(v5[u"中央値"], b5[u"中央値"]) and atmost(v5[u"最大"], b5[u"最大"]), v5)
    v6, b6 = cols["N-6"], B["N-6"]
    put("N-6", within(v6[u"中央値"], b6[u"中央値"]) and atmost(v6[u"最大"], b6[u"最大"]), v6)
    put("N-7", atmost(cols["N-7"], B["N-7"]), cols["N-7"])
    put("N-8", atmost(cols["N-8"], B["N-8"]), cols["N-8"])
    v9, b9 = cols["N-9"], B["N-9"]
    put("N-9", v9[u"書類"] == b9[u"書類"] and v9[u"AI の文"] == b9[u"AI の文"], v9)
    return collections.OrderedDict([(u"E", E), (u"欄", collections.OrderedDict((k, v[0]) for k, v in seal_pred_rows(seal).items()))])


def build_E(rec, seal):
    return judge_from(columns_from_rows(rec[u"行"], rec[u"import の時間"][u"秒"]), seal)


def _num(v, nd):
    return u"None" if v is None else (u"%." + str(nd) + u"f") % v


def fmt_value(k, v):
    u"""表の『測った値』の字(桁は固定。判定は丸めない値で行う)。"""
    if k in ("N-1", "N-3", "N-8"):
        return u"%s 秒" % _num(v, 3)
    if k == "N-2":
        return _num(v, 3)
    if k == "N-4":
        return u"%s ms" % _num(v, 2)
    if k == "N-5":
        return u"%s 秒 / %s 秒" % (_num(v[u"中央値"], 3), _num(v[u"最大"], 3))
    if k == "N-6":
        return u"%s MB / %s MB" % (_num(v[u"中央値"], 1), _num(v[u"最大"], 1))
    if k == "N-7":
        return u"%s%%" % _num(v, 1)
    return u"%s / %s" % tuple(u"なし" if v[x] is None else u"{:,}".format(v[x]) for x in (u"書類", u"AI の文"))


def render_pred(J, seal=None):
    seal = seal if seal is not None else read_seal()
    P = seal_pred_rows(seal)
    lines = [u"| # | 欄 | 予測 | 測った値 | 判定 |", u"|---|---|---|---|---|"]
    for k, v in J[u"E"].items():
        lines.append(u"| %s | %s | %s | %s | %s |" % (k, P[k][0], P[k][1], fmt_value(k, v[u"値"]), v[u"判定"]))
    return u"\n".join(lines)


def stats_rows(rows):
    u"""材料 × profile ごとの数。[(材料の種類, profile, 回の数, 時間の中央値, 最大, 1 claim の中央値 ms, ru_maxrss の後の中央値 MB, 最大 MB, 後 − 前の中央値 MB)]。"""
    out = []
    for kind in KINDS:
        for p in PROFILES:
            rs = select(rows, kind, p)
            ts = [r[u"時間"] for r in rs]
            per = [r[u"時間"] / r[u"claim の数"] * 1000.0 for r in rs] if rs and all(r[u"claim の数"] > 0 for r in rs) else None
            after = [r[u"ru_maxrss の後"] / float(MB) for r in rs]
            diff = [(r[u"ru_maxrss の後"] - r[u"ru_maxrss の前"]) / float(MB) for r in rs]
            out.append((kind, p, len(rs), median(ts), max(ts) if ts else None, median(per) if per else None, median(after), max(after) if after else None, median(diff)))
    return out


def render_stats(rows):
    lines = [u"| 材料 | profile | 回の数 | 時間の中央値(秒) | 時間の最大(秒) | 1 claim あたりの中央値(ms) | 後の ru_maxrss の中央値(MB) | 後の ru_maxrss の最大(MB) | 後 − 前の中央値(MB) |",
             u"|---|---|---|---|---|---|---|---|---|"]
    for kind, p, n, med, mx, per, am, ax, dm in stats_rows(rows):
        lines.append(u"| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (kind, p, u"{:,}".format(n), _num(med, 3), _num(mx, 3), _num(per, 2), _num(am, 1), _num(ax, 1), _num(dm, 1)))
    return u"\n".join(lines)


def load_record(root=ROOT):
    return GEN.jload(os.path.join(root, REC_REL))


def run_tally(root=ROOT, say=print, rec=None):
    seal = read_seal(root)
    rec = rec if rec is not None else load_record(root)
    J = build_E(rec, seal)
    say(render_pred(J, seal))
    say(u"")
    say(render_stats(rec[u"行"]))
    return J


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("run", "tally"))
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", default=None, help="この docID の書類と本だけ(--out が要る)")
    ap.add_argument("--reps", type=int, default=REPS_PROD)
    a = ap.parse_args(argv)
    if a.cmd == "run":
        run(root=a.root, only=a.only, out=a.out, reps=a.reps)
    else:
        run_tally(root=a.root)


if __name__ == "__main__":
    main()
