# -*- coding: utf-8 -*-
u"""封 docs/XBRL_AI_FORMS_SEAL_2026-11-03.md §0-2・§4 ― AI の文の生成(会社の選び・fact の表・指示文・API・meta)。

20 社 × 形 4(F1 要約・F2 箇条書き・F3 表 + 注記・F4 Q&A)× model 2 = 160 本を Anthropic の API で書かせる。

    python3 measure/xbrl_aiforms_gen_2026-11-03.py --dry-run              # 本数・見積り(USD)・会社 20 の docID。鍵は読まない・通信しない
    ANTHROPIC_API_KEY=... python3 measure/xbrl_aiforms_gen_2026-11-03.py [--only <docID>] [--resume]   # 有料。司令塔だけが走らせる

守り(封 §0-2 の 4・§4):
  - 鍵は環境変数 ``ANTHROPIC_API_KEY`` だけから読む(.env は読まない)。値は印字・記録・例外の文に通さない(記録は ``key_leaks`` を書く前と書いた後に検査する)。
  - 上限 ``COST_CAP_USD`` を字で留める。走らせる前に 160 本の見積り(入力の字数 × 1.0 を token とみなし、出力は ``MAX_TOKENS`` の全部。単価は保守的な ``PRICE_IN``・``PRICE_OUT``)を出し、
    上限を超えるなら 1 回も呼ばない。呼ぶたびに API の返す usage と累計を記録に追記し、累計 + 次の見積りが上限を超えたら止める。
  - 再試行は 429 / 5xx のときだけ最大 2 回(待ち 2 秒・8 秒)。ほかの失敗は記録して次へ(401 / 403 は鍵の問題なので全体を止める)。
  - 文は ``~/.cache/audit-core/aiforms-2026-11-03/texts/``、fact の表は ``.../facts/``(repo の外。既存の cache 3 folder には 1 file も書かない。前後の件数と名前の一覧の sha256 を記録し、変われば止める)。
    repo に置く記録 ``fixtures/xbrl/aiforms/gen_2026-11-03.json`` は sha256・字数・usage・費用・stop_reason・再試行の数だけ(文なし)。
  - 既に在る文は ``--resume`` を付けたときだけ飛ばす(付けずに在れば止める。有料の呼び出しを二度しない)。

engine(``core/``・``adapters/``)は 1 行も変えない。他の script は ``load()`` でなく importlib でこの file を読み、会社の選び・fact の表・置き場を使う。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SEAL_REL = "docs/XBRL_AI_FORMS_SEAL_2026-11-03.md"
SEAL_COMMIT = "0b43a03"
REC_DIR_REL = "fixtures/xbrl/aiforms"
GEN_REL = REC_DIR_REL + "/gen_2026-11-03.json"
REGRESS97_REL = "fixtures/xbrl/p28/regress97_2026-11-02.json"
P27_REPORTS_REL = "fixtures/xbrl/p27/reports_2026-10-27.json"
SEED_REL = "measure/SEED.json"

HOME = os.path.expanduser("~")
CACHE_BASE = os.path.join(HOME, ".cache", "audit-core")
NEW_CACHE = os.path.join(CACHE_BASE, "aiforms-2026-11-03")           # 新しい置き場(この便の script だけが書く)
EXISTING_CACHES = collections.OrderedDict([("edinet", os.path.join(CACHE_BASE, "edinet")),
                                           ("edinet-fresh-2026-10-21", os.path.join(CACHE_BASE, "edinet-fresh-2026-10-21")),
                                           ("edinet-prior-2026-11-02", os.path.join(CACHE_BASE, "edinet-prior-2026-11-02"))])
SAMPLE_DIR = {u"手元の 67": "edinet", u"新しい標本 30": "edinet-fresh-2026-10-21"}      # 97 の標本 → ZIP の folder

# ---- 封 §0-2 の決めごと(字で留める)
N_COMPANIES = 20
MIN_CLAIMS = 60
FORMS = ("F1", "F2", "F3", "F4")
MODELS = ("claude-sonnet-5-5", "claude-haiku-5-5")            # W1・W2
MODEL_TAG = {"claude-sonnet-5-5": "W1", "claude-haiku-5-5": "W2"}
MAX_TOKENS = 4000
COST_CAP_USD = 50.0
PRICE_IN = 5.0                  # USD / M tokens(両 model に当てる保守的な字)
PRICE_OUT = 25.0
API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"                                   # 2026-10-09 の生成と同じ
RETRY_WAITS = (2, 8)                                         # 429 / 5xx のとき最大 2 回
TIMEOUT_SEC = 300
KEY_ENV = "ANTHROPIC_API_KEY"
NONCONSOLIDATED_FALLBACK = True                            # fact の表の「素の context」に engine の単体フォールバックを使う(封に無い決定。報告に書く)
SEAT2_N = 32                                                 # 2 席目を立てる本数(160 の 20%)

# ---- 指示文(封 §0-2 の 2。字は固定し、封の門が照らす。SYSTEM は無し = user の 1 message)
WRITER_COMMON = u"""あなたは上場企業の開示を担当しています。

以下は当社の当事業年度の財務数値です。会計システムから機械的に出力したものです。各行は、項目の要素名・標準ラベル(日本語名)・値・単位・期間です。

{FACTS}

この数値をもとに、当事業年度の経営成績・財政状態・キャッシュ・フローの状況を説明するレポートを、日本語で書いてください。読み手は個人投資家です。

決まり:
1. 材料は上の数値の表だけです。表に無い事実(会社の方針・見通し・外部の出来事など)は書かないでください。
2. 数は表の値から書いてください。読み手に分かりやすい単位に直し、丸め方は自分で決めてかまいません。前期からの増減率や比率など表に無い数は、表の値から自分で計算してかまいません。
3. 形は次の型で書いてください: {FORM}
4. 出力はレポートだけにしてください(前置き・材料の説明・計算の過程は書かない)。"""

WRITER_FORMS = collections.OrderedDict([
    ("F1", u"見出しつきの段落。経営成績・財政状態・キャッシュ・フローの状況の順に、見出しを立てて段落で書く。全体で 1,500〜2,500 字。"),
    ("F2", u"箇条書き。見出しは立てず、「・」で始まる項目を 12〜25 個書く。1 項目は 1 文。"),
    ("F3", u"表と注記。まず「|」区切りの表(列は 項目・当期・前期・増減)を 5〜12 行書き、その後に注記の文を 5〜10 文書く。注記の文には数を含める。"),
    ("F4", u"Q&A。投資家の問いと会社の答えを 6〜10 組書く。各組は「Q:」で始まる問いの行と「A:」で始まる答えの行にする。答えには数を含める。"),
])
PLACEHOLDERS = (u"{FACTS}", u"{FORM}")
_PH_RE = re.compile("|".join(re.escape(p) for p in PLACEHOLDERS))

KEY_PATTERNS = (r"sk-[A-Za-z0-9_\-]{10,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{20,}", r"xox[baprs]-[A-Za-z0-9\-]{10,}",
                r"-----BEGIN", r"Bearer [A-Za-z0-9._\-]{16,}", r"AIza[0-9A-Za-z_\-]{30,}", r"x-api-key",
                KEY_ENV + r"\s*=\s*['\"]?\w{8,}")
LONG_ALNUM = re.compile(r"[A-Za-z0-9_\-]{32,}")
SHA256_HEX = re.compile(r"[0-9a-f]{64}")
GIT_COMMIT = re.compile(r"[0-9a-f]{40}")


class Stop(SystemExit):
    u"""止める。文言に鍵・文・fact の値を入れない。"""


# ======================================================================================================
# 小さい道具
def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_text(s):
    return sha256_bytes(s.encode("utf-8"))


def sha256_file(p):
    with io.open(p, "rb") as fh:
        return sha256_bytes(fh.read())


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + u"\n"


def write_text(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    os.replace(tmp, path)


def names_snapshot(folder):
    u"""folder の件数と名前の一覧の sha256。無ければ 0 件。"""
    names = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
    return {u"存在": os.path.isdir(folder), u"件数": len(names), u"名前の一覧の sha256": sha256_text(u"\n".join(names))}


def caches_snapshot(existing=None):
    existing = existing or EXISTING_CACHES
    return collections.OrderedDict((k, names_snapshot(v)) for k, v in existing.items())


def key_leaks(text, key_value=None, long_alnum=True):
    u"""記録の文字列に鍵らしい字が在れば、その種類の一覧(値は返さない)。sha256・git の commit の 16 進は鍵に数えない。"""
    leaks = []
    for pat in KEY_PATTERNS:
        if re.search(pat, text):
            leaks.append(u"鍵の形(%s)" % pat[:12])
    for s in (LONG_ALNUM.findall(text) if long_alnum else []):      # 要素名(pointers)は長い英字なので、行の側は long_alnum=False で見る
        if SHA256_HEX.fullmatch(s) or GIT_COMMIT.fullmatch(s):
            continue
        leaks.append(u"32 字以上の英数字の連なり(長さ %d)" % len(s))
    if key_value and key_value in text:
        leaks.append(u"環境の鍵の値そのもの")
    return leaks


def git_head(root=REPO):
    r = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return r.stdout.decode("ascii", "replace").strip() or None


# ======================================================================================================
# 会社の選び(封 §0-2 の 1)
def seed_value(root=ROOT):
    u"""種は ``inject.verify_seed_sealed(measure/SEED.json)``(git に追跡され内容が一致していなければ止まる)。(種, meta)。"""
    import inject as IJ
    return IJ.verify_seed_sealed(os.path.join(root, SEED_REL))


def select_companies(root=ROOT, seed=None):
    u"""手元の 97 書類のうち P27 の調整用・評価用 20 社を除いた書類で、claims が MIN_CLAIMS 以上のものを docID の昇順に並べ、
    ``random.Random("<seed>|AIFORMS_COMPANIES").shuffle`` で混ぜた先頭 20。(選んだ行の列, 数え)。行 = 記録の ``書類`` の行(docID・標本・zip の sha256・claims)。"""
    r97 = jload(os.path.join(root, REGRESS97_REL))[u"書類"]
    p27 = jload(os.path.join(root, P27_REPORTS_REL))[u"会社"]
    excluded = set(c["docID"] for c in p27)
    counts = collections.OrderedDict()
    counts[u"手元の書類"] = len(r97)
    counts[u"P27 の調整用・評価用(除く)"] = len(excluded)
    rest = [r for r in r97 if r["docID"] not in excluded]
    counts[u"除いた後の書類"] = len(rest)
    counts[u"除いた理由 P27 の 20 社に当たる書類"] = len(r97) - len(rest)
    pool = sorted((r for r in rest if r["claims"] >= MIN_CLAIMS), key=lambda r: r["docID"])
    counts[u"claims %d 未満で除いた書類" % MIN_CLAIMS] = len(rest) - len(pool)
    counts[u"母集団(claims %d 以上・docID の昇順)" % MIN_CLAIMS] = len(pool)
    if len(pool) < N_COMPANIES:
        raise Stop(u"**母集団が %d 社に足りない。止める**" % N_COMPANIES)
    if seed is None:
        seed, _meta = seed_value(root)
    rng = random.Random("%s|AIFORMS_COMPANIES" % seed)
    shuffled = list(pool)
    rng.shuffle(shuffled)
    chosen = shuffled[:N_COMPANIES]
    counts[u"選んだ会社"] = len(chosen)
    return chosen, counts


def zip_path(row, caches=None):
    caches = caches or EXISTING_CACHES
    return os.path.join(caches[SAMPLE_DIR[row[u"標本"]]], row["docID"] + ".zip")


def read_zip(row, caches=None):
    p = zip_path(row, caches)
    with io.open(p, "rb") as fh:
        zb = fh.read()
    if sha256_bytes(zb) != row[u"zip の sha256"]:
        raise Stop(u"**ZIP の sha256 が記録と違う: %s。止める**" % row["docID"])
    return zb


# ======================================================================================================
# fact の表(2026-10-09 の作り + 標準ラベル)
def period_of(ctx):
    if ctx is None:
        return u"?"
    if ctx.get("instant"):
        return u"%s 時点" % ctx["instant"]
    if ctx.get("start") and ctx.get("end"):
        return u"%s〜%s" % (ctx["start"], ctx["end"])
    return u"?"


def build_facts_table(zb, label_map=None):
    u"""2026-10-09 の ``build_facts_table`` と同じ規則 ― member を持たない素の context の fact を全件・(要素名, context id) の昇順・間引かない ―
    に、**標準ラベル(日本語名)の列**を足した 5 欄(項目 = 要素名・標準ラベル・値・単位・期間)。
    標準ラベルは標準タクソノミ(jppfs・jpcrp)の局所名で引き、無ければ書類の ``_lab.xml``(会社拡張)、それも無ければ空。(表, 使った行数, 全 fact 数, 標準ラベルが付いた行数)"""
    from adapters.xbrl import instance as I
    inst = I.load_instance(zb)
    label_map = I.taxonomy_label_map(None) if label_map is None else label_map
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        id2label = I.labels_from_zip(z, inst["names"])
    # 連結の枠に財務の要素が 1 種も無い書類(単体だけの会社)では、engine の素の枠と同じく「単体の member だけの枠」を素として扱う
    # (P20 以後の engine の規則 ``with_nonconsolidated_fallback``。無いと表がほぼ空になる ― 封に無い決定。報告に書く)。
    contexts = I.with_nonconsolidated_fallback(inst["contexts"], inst["facts"], NONCONSOLIDATED_FALLBACK)
    rows = [f for f in inst["facts"] if I.plain_context(f["context"], contexts)]
    rows.sort(key=lambda f: (f["name"], f["context"]))
    lines = [u"| 項目(要素名) | 標準ラベル | 値 | 単位 | 期間 |", u"|---|---|---|---|---|"]
    labelled = 0
    for f in rows:
        local = f["name"].split(":")[-1]
        label = label_map.get(local) or id2label.get(f["name"].replace(":", "_")) or u""
        if label:
            labelled += 1
        v = f["value"]
        vs = (u"%d" % v) if float(v).is_integer() else (u"%s" % v)
        lines.append(u"| %s | %s | %s | %s | %s |" % (f["name"], label, vs, f["unit"], period_of(contexts.get(f["context"]))))
    return u"\n".join(lines), len(rows), len(inst["facts"]), labelled


def render_prompt(form, table):
    u"""指示文の全体。``{FACTS}`` と ``{FORM}`` だけを 1 回の走査で埋める(表の中の ``{…}`` が再び置き換わらない)。"""
    values = {u"{FACTS}": table, u"{FORM}": WRITER_FORMS[form]}
    return _PH_RE.sub(lambda m: values[m.group(0)], WRITER_COMMON)


def instruction_shas():
    return collections.OrderedDict([(u"WRITER_COMMON", sha256_text(WRITER_COMMON)),
                                    (u"WRITER_FORMS", collections.OrderedDict((k, sha256_text(v)) for k, v in WRITER_FORMS.items()))])


# ======================================================================================================
# 見積り・費用
def estimate_usd(prompt_chars):
    u"""1 本の見積り = 入力の字数 × 1.0 を token とみなす + 出力は MAX_TOKENS の全部(保守的な単価)。"""
    return (prompt_chars * PRICE_IN + MAX_TOKENS * PRICE_OUT) / 1e6


def cost_usd(input_tokens, output_tokens):
    return ((input_tokens or 0) * PRICE_IN + (output_tokens or 0) * PRICE_OUT) / 1e6


def text_key(doc, form, model):
    return u"%s_%s_%s" % (doc, form, model)


def jobs(docs):
    u"""160 本の列(docID → 形 → model の順。決めておく)。"""
    return [(d, f, m) for d in docs for f in FORMS for m in MODELS]


# ======================================================================================================
# API(通信する唯一の所)
def call_api(prompt, model, key):
    u"""(status, body)。HTTP の 4xx・5xx は例外にせず status で返す。例外の文には鍵を通さない(型だけ)。"""
    body = json.dumps({"model": model, "max_tokens": MAX_TOKENS, "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, method="POST",
                                 headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": API_VERSION})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as r:
            return r.getcode(), r.read()
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read()
        except Exception:                                # noqa: BLE001
            return e.code, b""
    except Exception as e:                               # noqa: BLE001  通信の失敗。文は捨てる
        return None, type(e).__name__.encode("ascii", "replace")


def call_with_retry(prompt, model, key, transport=call_api, sleep=time.sleep):
    u"""429 / 5xx のときだけ最大 2 回(待ち 2 秒・8 秒)。(status, body, 再試行の数)。通信の失敗(status None)は再試行しない。"""
    retries = 0
    while True:
        status, body = transport(prompt, model, key)
        if status is not None and (status == 429 or 500 <= status < 600) and retries < len(RETRY_WAITS):
            sleep(RETRY_WAITS[retries])
            retries += 1
            continue
        return status, body, retries


# ======================================================================================================
# 記録
def new_record(head, chosen, counts, seed_meta, tables, before):
    return collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT), (u"step", u"AI の形 4 × model 2 ― 生成(有料。0 USD の部分と記録で分ける)"),
        (u"HEAD の commit", head), (u"この script の sha256", sha256_file(os.path.abspath(__file__))),
        (u"会社の選び", collections.OrderedDict([
            (u"規則", u"手元の 97 書類のうち P27 の調整用・評価用 20 社を除き、regress97 の claims が %d 以上のものを docID の昇順に並べ、"
                     u"random.Random('<seed>|AIFORMS_COMPANIES').shuffle の先頭 %d(SEED.json の種)" % (MIN_CLAIMS, N_COMPANIES)),
            (u"種の確認", seed_meta), (u"数え", counts),
            (u"docID", [r["docID"] for r in chosen]),
            (u"標本", collections.OrderedDict((r["docID"], r[u"標本"]) for r in chosen)),
            (u"zip の sha256", collections.OrderedDict((r["docID"], r[u"zip の sha256"]) for r in chosen)),
        ])),
        (u"fact の表", collections.OrderedDict((d, t) for d, t in tables.items())),
        (u"指示文の sha256", instruction_shas()),
        (u"model", list(MODELS)), (u"max_tokens", MAX_TOKENS), (u"API の版", API_VERSION), (u"再試行", u"429 / 5xx のときだけ最大 %d 回(待ち %s 秒)" % (len(RETRY_WAITS), list(RETRY_WAITS))),
        (u"費用", collections.OrderedDict([(u"上限 USD", COST_CAP_USD), (u"単価 入力 USD / M tokens", PRICE_IN), (u"単価 出力 USD / M tokens", PRICE_OUT),
                                          (u"見積りの規則", u"入力の字数 × 1.0 を token とみなし、出力は max_tokens の全部(保守的な単価を両 model に当てる)")])),
        (u"cache の前後", collections.OrderedDict([(u"前", before), (u"後", None), (u"変化なし", None)])),
        (u"呼び出し", []),
        (u"累計", collections.OrderedDict([(u"呼び出しの数", 0), (u"成功", 0), (u"失敗", 0), (u"費用 USD", 0.0)])),
        (u"止めた理由", None),
        (u"key_leaks", []),
    ])


def refresh_totals(rec):
    calls = rec[u"呼び出し"]
    rec[u"累計"] = collections.OrderedDict([(u"呼び出しの数", len(calls)), (u"成功", sum(1 for c in calls if c[u"ok"])),
                                          (u"失敗", sum(1 for c in calls if not c[u"ok"])),
                                          (u"費用 USD", round(sum(c[u"cost_usd"] for c in calls), 6))])
    return rec


def write_record(path, rec, key_value=None):
    u"""書く前と書いた後に鍵の検査を当てる。"""
    text = dumps(refresh_totals(rec))
    leaks = key_leaks(text, key_value)
    if leaks:
        raise Stop(u"**鍵らしい字が記録に在る(%s)。書かずに止める**" % u" / ".join(sorted(set(leaks))))
    write_text(path, text)
    back = io.open(path, encoding="utf-8").read()
    if key_leaks(back, key_value):
        os.remove(path)
        raise Stop(u"**書いた後の記録に鍵らしい字が在った。消して止める**")


# ======================================================================================================
def prepare(root, caches, new_cache, say, check_replace=True):
    u"""会社の選び・fact の表・指示文・見積り。通信しない・鍵を読まない。(chosen, counts, seed_meta, tables, prompts, est)。"""
    seed, seed_meta = seed_value(root)
    chosen, counts = select_companies(root, seed)
    tables, prompts, est_rows = collections.OrderedDict(), collections.OrderedDict(), collections.OrderedDict()
    from adapters.xbrl import instance as I
    from adapters.xbrl import prose as PR
    label_map = I.taxonomy_label_map(None)
    for r in chosen:
        zb = read_zip(r, caches)
        table, used, total, labelled = build_facts_table(zb, label_map)
        if check_replace:
            try:
                PR.build_modified_zip(zb, u"確認の文。")
            except Exception as e:                       # noqa: BLE001
                raise Stop(u"**文の差し替えができない書類: %s(%s)。止める**" % (r["docID"], type(e).__name__))
        write_text(os.path.join(new_cache, "facts", r["docID"] + ".md"), table + u"\n")
        tables[r["docID"]] = collections.OrderedDict([(u"fact の数(素の context)", used), (u"instance の fact の数", total), (u"標準ラベルが付いた行", labelled),
                                                      (u"表の字数", len(table)), (u"表の sha256", sha256_text(table))])
        for form in FORMS:
            prompts[(r["docID"], form)] = render_prompt(form, table)
    for (d, f), p in prompts.items():
        est_rows[(d, f)] = estimate_usd(len(p))
    est_total = sum(est_rows[(d, f)] * len(MODELS) for (d, f) in est_rows)
    return chosen, counts, seed_meta, tables, prompts, est_total


def run(root=ROOT, dry_run=False, only=None, resume=False, caches=None, new_cache=None, out=None, key_value=None,
        transport=call_api, sleep=time.sleep, say=print, head=None):
    caches = caches or EXISTING_CACHES
    new_cache = new_cache or NEW_CACHE
    out = out or os.path.join(root, GEN_REL)
    before = caches_snapshot(caches)
    chosen, counts, seed_meta, tables, prompts, est_total = prepare(root, caches, new_cache, say)
    docs = [r["docID"] for r in chosen]
    all_jobs = jobs(docs)
    say(u"会社 %d・形 %d・model %d = %d 本" % (len(docs), len(FORMS), len(MODELS), len(all_jobs)))
    for k, v in counts.items():
        say(u"  %s: %d" % (k, v))
    for r in chosen:
        t = tables[r["docID"]]
        say(u"  %s %s claims=%d fact=%d/%d 標準ラベル付き=%d 表=%d字 見積り(model 2 本・形 4 つ)=%.4f USD" % (
            r["docID"], r[u"標本"], r["claims"], t[u"fact の数(素の context)"], t[u"instance の fact の数"], t[u"標準ラベルが付いた行"], t[u"表の字数"],
            sum(estimate_usd(len(prompts[(r["docID"], f)])) for f in FORMS) * len(MODELS)))
    say(u"見積り(保守的な単価 入力 %.1f / 出力 %.1f USD / M tokens・入力 = 字数 × 1.0・出力 = max_tokens %d): %.4f USD(上限 %.2f)" % (PRICE_IN, PRICE_OUT, MAX_TOKENS, est_total, COST_CAP_USD))
    if est_total > COST_CAP_USD:
        raise Stop(u"**見積り %.4f USD が上限 %.2f USD を超える。1 回も呼ばずに止める**" % (est_total, COST_CAP_USD))
    if dry_run:
        say(u"--dry-run: 見積りだけ。通信していない・鍵は読んでいない。fact の表は %s に書いた。" % os.path.join(new_cache, "facts"))
        return {"docs": docs, "jobs": len(all_jobs), "est_usd": est_total, "tables": tables, "counts": counts}

    key = os.environ.get(KEY_ENV)
    if not key:
        raise Stop(u"**環境変数 %s が無い。止める**" % KEY_ENV)
    if only is not None:
        if only not in docs:
            raise Stop(u"**--only の docID が選んだ 20 社に無い。止める**")
        all_jobs = [j for j in all_jobs if j[0] == only]
    rec_exists = os.path.exists(out)
    if rec_exists and not resume:
        raise Stop(u"**記録が既に在る。続きは --resume を付ける(有料の呼び出しを二度しない)。止める**")
    texts_dir = os.path.join(new_cache, "texts")
    if resume and rec_exists:
        rec = jload(out)
        if rec[u"会社の選び"][u"docID"] != docs:
            raise Stop(u"**記録の会社と今の選びが違う。止める**")
        rec[u"cache の前後"][u"前"] = rec[u"cache の前後"][u"前"] or before
    else:
        rec = new_record(head or git_head(), chosen, counts, seed_meta, tables, before)
        existing = [n for n in (os.listdir(texts_dir) if os.path.isdir(texts_dir) else []) if n.endswith(".txt")]
        if existing:
            raise Stop(u"**文の folder に文が在るが記録が無い。止める**")
    done = set(c[u"name"] for c in rec[u"呼び出し"] if c[u"ok"])
    cum = sum(c[u"cost_usd"] for c in rec[u"呼び出し"])
    n_new = 0
    for doc, form, model in all_jobs:
        k = text_key(doc, form, model)
        path = os.path.join(texts_dir, k + ".txt")
        if k in done:
            # 記録に ok で在る本は飛ばす。文の file が在り sha256 が記録と合うことを確かめる(合わなければ止める)
            if not os.path.exists(path) or sha256_file(path) != next(c[u"sha256"] for c in rec[u"呼び出し"] if c[u"ok"] and c[u"name"] == k):
                raise Stop(u"**記録に ok の本の文が無いか sha256 が記録と違う: %s。止める**" % k)
            continue
        if os.path.exists(path):
            raise Stop(u"**文が既に在るが記録に ok が無い: %s。二度呼ばない(記録を直してから)。止める**" % k)
        prompt = prompts[(doc, form)]
        est = estimate_usd(len(prompt))
        if cum + est > COST_CAP_USD:
            rec[u"止めた理由"] = u"累計 %.4f + 次の見積り %.4f が上限 %.2f USD を超える(%s の前)" % (cum, est, COST_CAP_USD, k)
            write_record(out, rec, key)
            raise Stop(u"**%s**" % rec[u"止めた理由"])
        status, body, retries = call_with_retry(prompt, model, key, transport, sleep)
        item = collections.OrderedDict([(u"name", k), (u"docID", doc), (u"form", form), (u"model", model), (u"writer", MODEL_TAG[model]),
                                        (u"prompt_chars", len(prompt)), (u"prompt_sha256", sha256_text(prompt)), (u"est_usd", round(est, 6)),
                                        (u"retries", retries), (u"http_status", status), (u"ok", False), (u"sha256", None), (u"chars", None),
                                        (u"usage", None), (u"cost_usd", 0.0), (u"stop_reason", None)])
        if status == 200:
            try:
                res = json.loads(body.decode("utf-8"))
                text = u"".join(b.get("text", u"") for b in res.get("content", []) if isinstance(b, dict))
                usage = res.get("usage", {}) or {}
                tin, tout = usage.get("input_tokens"), usage.get("output_tokens")
                item.update({u"ok": True, u"sha256": sha256_text(text), u"chars": len(text),
                             u"usage": {u"input_tokens": tin, u"output_tokens": tout}, u"cost_usd": round(cost_usd(tin, tout), 6),
                             u"stop_reason": res.get("stop_reason")})
                write_text(os.path.join(texts_dir, k + ".txt"), text)
            except Exception as e:                       # noqa: BLE001  形が違う返事。文は捨てる
                item[u"error"] = u"返事の形が読めない(%s)" % type(e).__name__
                item[u"ok"] = False
        else:
            item[u"error"] = u"HTTP %s" % status if status is not None else u"通信の失敗(%s)" % body.decode("ascii", "replace")
        rec[u"呼び出し"].append(item)
        cum = sum(c[u"cost_usd"] for c in rec[u"呼び出し"])
        write_record(out, rec, key)                     # 呼ぶたびに追記(止まっても累計が残る)
        n_new += 1
        say(u"  %s %s retries=%d %s 累計 %.4f USD" % (k, u"ok" if item[u"ok"] else item.get(u"error", u"失敗"), retries,
                                                    u"stop=%s" % item[u"stop_reason"] if item[u"ok"] else u"", cum))
        if status in (401, 403):
            rec[u"止めた理由"] = u"HTTP %s(鍵の問題)" % status
            write_record(out, rec, key)
            raise Stop(u"**HTTP %s。鍵の問題なので全体を止める**" % status)
    after = caches_snapshot(caches)
    rec[u"cache の前後"][u"後"] = after
    rec[u"cache の前後"][u"変化なし"] = bool(rec[u"cache の前後"][u"前"] == after)
    if not rec[u"cache の前後"][u"変化なし"]:
        write_record(out, rec, key)
        raise Stop(u"**既存の cache の件数か名前が変わった。止める**")
    write_record(out, rec, key)
    say(u"-> %s(新しく呼んだ %d・累計 %.4f USD)" % (out, n_new, cum))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="見積りと本数だけ(通信しない・鍵は読まない)")
    ap.add_argument("--only", default=None, help="この docID の 8 本だけ")
    ap.add_argument("--resume", action="store_true", help="既に在る文は飛ばして続ける")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    run(root=a.root, dry_run=a.dry_run, only=a.only, resume=a.resume, out=a.out)


if __name__ == "__main__":
    main()
