# -*- coding: utf-8 -*-
"""封 docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md §1・§2 ― **外部の DB(EDINET DB)の `/financials` で候補の会社を照らし、使う会社 U と
調整用・評価用・文体の型を決め、U の会社の `/companies` と `/ratios` を取る。費用 0 USD(Free プラン・1 日 JST 95 回まで)。**

**鍵は環境変数 `EDINETDB_API_KEY` からだけ受ける。値は読まない(中身を見ない)・印字しない・記録しない・例外の文に出さない。**
script は鍵を引数に取らない。応答を保存する前に、保存する全部の byte に鍵の値が無いことを確かめ、在れば保存せず止める(値は印字しない)。
repo の記録は、書く前と書いた後に `key_leaks`(32 字以上の英数字の連なり・環境の鍵の値そのもの)で確かめる。

置き場: 応答は repo の外 `~/.cache/audit-core/edinetdb-p27/<docID>/{financials,companies,ratios}.json` に、受け取った byte のまま置く
(HTTP 200 のものだけ)。**`~/.cache/audit-core/edinet/` と `~/.cache/audit-core/edinet-fresh-2026-10-21/` には 1 file も足さない**
(後者は ZIP を読むだけ。既存の門が数える)。走る前と後に両 folder の件数と名前の一覧の sha256 を記録し、変わっていたら記録を書かずに止める。
応答の置き場がその 2 folder の中なら、何も呼ばずに止める。

やること(封 §1-1〜§1-7)
  1. 候補の並び: `fixtures/xbrl/fresh/fetched_2026-10-21.json` の `取得した書類` を `位置(引いた順)` の昇順に。主 = 位置 1〜30、予備の候補 = 位置 31〜40
  2. 使う前に ZIP の sha256 が記録と同じか(違えば止める)。EDINET コードは `XBRL/PublicDoc/` の `.xbrl` の file 名の `E` + 5 桁(1 つでなければ止める)
  3. 3 本の会社の EDINET コード(トヨタ・ソニー・任天堂)は除く
  4. `/financials` の応答で、fiscal_year が最大の行がちょうど 1 行で、その doc_id が ZIP の docID と同じなら残る。違えば理由を付けて除く。
     **欄(fiscal_year・doc_id)が無ければ、その会社で止める(欄の名前を推測して進まない)**
  5. 差し替えの節: `adapters.xbrl.prose.build_modified_zip` が例外を出さないか(固定の 1 文。engine の判定は見ない)
  6. K → U(先頭 20)→ 調整用(先頭 ⌊|U|/2⌋)・評価用(残り)・予備。|K| < 20 のときだけ予備の候補 10 件を照らす。|U| < 12 は止める(記録は書く)
  7. 型 = ("A", "B", "C")[i % 3](U の中の位置 i)
  U の会社だけ `/companies` と `/ratios` を取る。回数は再試行を含めて 1 日(JST)95 回まで。**封 §11-0 の下見 2 回は 2026-10-27(JST)に既に使った数**として数える。
  429・5xx・通信の失敗だけ 60 秒待って 2 回まで再試行し、それでも駄目なら `応答なし`(引き直さない)。上限に達したら止め、翌日に同じ順で続ける。

    EDINETDB_API_KEY=<鍵> python3 measure/xbrl_p27_dbfetch_2026-10-27.py
    (鍵はキーチェーンから取り、その場で環境変数に入れる。字で書かない。値を持たない動作確認は `--dry-run --fake-dir <folder> --out <file> --cache-root <folder>`。
     通信せず、`<folder>/<EDINETコード>/{financials,companies,ratios}.json` を応答の代わりに読む)

通信は `default_transport` の中の urllib だけ(試験は transport を差し替える)。**repo に置く記録に応答の値(数・会社名・業種の字)は入れない。**
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import re
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)

SEAL = "docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md"
FETCHED_REL = os.path.join("fixtures", "xbrl", "fresh", "fetched_2026-10-21.json")
OUT_REL = os.path.join("fixtures", "xbrl", "p27", "dbfetch_2026-10-27.json")
KEY_NAME = "EDINETDB_API_KEY"
BASE_URL = "https://edinetdb.jp/v1"
FINANCIALS_QUERY = "years=3&include_nulls=true&include_null_reasons=true"
ENDPOINT_PATHS = {
    "financials": "/companies/%s/financials?" + FINANCIALS_QUERY,
    "companies": "/companies/%s",
    "ratios": "/companies/%s/ratios",
}

FRESH_ZIP_DIR_NAME = "edinet-fresh-2026-10-21"
EXISTING_CACHE_DIR_NAME = "edinet"
P27_CACHE_DIR_NAME = "edinetdb-p27"

# 封 §1-3: 3 本の会社(トヨタ自動車・ソニーグループ・任天堂)。コードは 3 本の provenance の instance_source の字から
EXCLUDED_CODES = ("E02144", "E01777", "E02367")
N_PRIMARY = 30          # 位置 1〜30
N_RESERVE = 10          # 位置 31〜40(予備の候補)
U_SIZE = 20             # 封 §1-6
U_MIN = 12              # |U| < 12 なら止める
STYLES = ("A", "B", "C")
PROBE_SENTENCE = u"当期の業績を記載する。"    # 封 §1-5

DAILY_LIMIT = 95                       # 封 §2-1(JST の 1 日。再試行を含む)
PRIOR_USES = {"2026-10-27": 2}         # 封 §11-0: 下見の 2 回(位置 1 と 2 の /financials)。この日(JST)の分として数える
MAX_RETRIES = 2                        # 429・5xx・通信の失敗だけ
RETRY_WAIT_SEC = 60.0
INTERVAL_SEC = 1.0                     # 呼び出しの間(封に値は無い。礼儀の待ち)
TIMEOUT_SEC = 30

JST = datetime.timezone(datetime.timedelta(hours=9))

# 鍵らしい字: 32 字以上の英数字の連なり。sha256 の 64 桁 16 進だけは通す(前例 xbrl_fresh_fetch_2026-10-21.py と同じ型)
KEYISH = re.compile(r"[A-Za-z0-9]{32,}")
SHA256_HEX = re.compile(r"[0-9a-f]{64}")
DOC_ID = re.compile(r"S[0-9A-Z]{7}")
CODE_IN_NAME = re.compile(r"_(E[0-9]{5})-[0-9]{3}_")


class Stop(SystemExit):
    """止める(最終の記録は書かない)。"""


class LimitStop(Stop):
    """1 日の上限に達した(進みは残す。翌日に同じ順で続ける)。"""


class FieldMissing(Exception):
    """`/financials` の応答に fiscal_year か doc_id の欄が無い(封 §1-4。1 社目で止める)。"""


# ---------------------------------------------------------------- 小さい道具
def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt):
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _jst_date(dt):
    return dt.astimezone(JST).strftime("%Y-%m-%d")


def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()


def key_leaks(text, key_value=None):
    """記録の文字列に鍵らしい字が在れば、その種類の一覧(値は返さない)。"""
    leaks = []
    for s in KEYISH.findall(text):
        if not SHA256_HEX.fullmatch(s):
            leaks.append("32 字以上の英数字の連なり(長さ %d)" % len(s))
    if re.search(KEY_NAME + r"\s*=\s*['\"]?\w{8,}", text):
        leaks.append("%s=値" % KEY_NAME)
    if key_value and key_value in text:
        leaks.append("環境の鍵の値そのもの")
    return leaks


def bytes_leak_key(blob, key_value):
    """保存する byte に環境の鍵の値が在るか(値は返さない)。"""
    return bool(key_value) and key_value.encode("utf-8") in blob


def _error_note(exc):
    """例外の文(str)は記録しない(鍵が混ざりうる)。型と HTTP の符号だけ。"""
    note = type(exc).__name__
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        note += " %d" % code
    return note


def display_path(path):
    home = os.path.expanduser("~")
    if path == home or path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path


def default_cache_base():
    """`~/.cache/audit-core`(呼ぶ時に HOME を見る)。"""
    return os.path.join(os.path.expanduser("~"), ".cache", "audit-core")


def default_zip_dir():
    return os.path.join(default_cache_base(), FRESH_ZIP_DIR_NAME)


def default_existing_cache_dir():
    return os.path.join(default_cache_base(), EXISTING_CACHE_DIR_NAME)


def default_cache_root():
    return os.path.join(default_cache_base(), P27_CACHE_DIR_NAME)


def snapshot(folder):
    """folder の件数と名前の一覧の sha256(封 §2-3)。無ければ 0 件。"""
    names = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
    return {"folder": display_path(os.path.abspath(folder)), "存在": os.path.isdir(folder),
            "件数": len(names), "名前の一覧の sha256": sha256_hex("\n".join(names).encode("utf-8"))}


def _inside(path, folder):
    a, b = os.path.realpath(path), os.path.realpath(folder)
    return a == b or a.startswith(b + os.sep)


# ---------------------------------------------------------------- §1-1 候補の並び
def load_candidates(fetched_path):
    """(主の候補 30 件, 予備の候補 10 件)。各行 {docID, 位置, 区分, sha256, bytes}。記録が封の字と合わなければ止める。"""
    with io.open(fetched_path, encoding="utf-8") as fh:
        rec = json.load(fh)
    rows = sorted(rec["取得した書類"], key=lambda r: r["位置(引いた順)"])
    if [r["位置(引いた順)"] for r in rows] != list(range(1, N_PRIMARY + N_RESERVE + 1)):
        raise Stop("**候補の位置が 1〜%d の連番でない。止める**" % (N_PRIMARY + N_RESERVE))
    primary, reserve = rows[:N_PRIMARY], rows[N_PRIMARY:]
    if [r["docID"] for r in primary] != list(rec["使う書類"]):
        raise Stop("**位置 1〜%d が `使う書類` と同じでない。止める**" % N_PRIMARY)
    if not all(r.get("取得") == "成功" and r.get("使う") is True for r in primary):
        raise Stop("**主の候補に取得に失敗か『使う』でないものが在る。止める**")
    if not all(r.get("取得") == "成功" and r.get("使う") is False and isinstance(r.get("claims"), int)
               and r["claims"] >= 1 for r in reserve):
        raise Stop("**予備の候補が『取得済み・claim 1 以上・使うが false』の 10 件でない。止める**")
    ids = [r["docID"] for r in rows]
    if len(set(ids)) != len(ids) or not all(DOC_ID.fullmatch(d) for d in ids):
        raise Stop("**候補の docID の形が不正か重複。止める**")

    def cand(r, kind):
        return {"docID": r["docID"], "位置": r["位置(引いた順)"], "区分": kind,
                "sha256": r["sha256"], "bytes": r["bytes"]}
    return [cand(r, "主") for r in primary], [cand(r, "予備の候補") for r in reserve]


# ---------------------------------------------------------------- §1-2 ZIP の確かめ・EDINET コード
def edinet_code_from_zip(zip_bytes):
    """`XBRL/PublicDoc/` の `.xbrl` の file 名の `E` + 5 桁。`.xbrl` がちょうど 1 つでなければ止める。"""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        names = [n for n in z.namelist() if n.startswith("XBRL/PublicDoc/") and n.endswith(".xbrl")]
    if len(names) != 1:
        raise Stop("**ZIP の XBRL/PublicDoc/ の .xbrl が %d 個(1 個でない)。止める**" % len(names))
    m = CODE_IN_NAME.search(os.path.basename(names[0]))
    if not m:
        raise Stop("**.xbrl の file 名から EDINET コード(E + 5 桁)が読めない。止める**")
    return m.group(1)


def read_verified_zip(zip_dir, cand):
    """ZIP を読み、sha256 が記録と同じか確かめる(違えば止める)。(bytes, EDINET コード)。"""
    path = os.path.join(zip_dir, cand["docID"] + ".zip")
    if not os.path.exists(path):
        raise Stop("**ZIP が無い: %s。止める**" % cand["docID"])
    with io.open(path, "rb") as fh:
        zb = fh.read()
    if sha256_hex(zb) != cand["sha256"]:
        raise Stop("**ZIP の sha256 が記録と違う: %s。止める**" % cand["docID"])
    return zb, edinet_code_from_zip(zb)


# ---------------------------------------------------------------- §1-4 DB の当期の doc_id で照らす
def extract_rows(body):
    """`/financials` の応答(JSON を読んだもの)から行の列を取る。**欄の名前を推測しない**(名前によらない規則):
    トップが列ならそれ。辞書なら、値のうち「列で、要素が全部辞書」のものがちょうど 1 つ(空でないものを優先。
    空の列だけがちょうど 1 つなら行なし)。辞書の中の辞書は 1 段だけ降りる。決まらなければ止める。"""
    def lists_of_dicts(d):
        return [v for v in d.values() if isinstance(v, list) and all(isinstance(x, dict) for x in v)]
    if isinstance(body, list):
        if all(isinstance(x, dict) for x in body):
            return body
        raise Stop("**/financials の応答が辞書の列でない。止める**")
    if isinstance(body, dict):
        scopes = [body] + [v for v in body.values() if isinstance(v, dict)]
        for scope in scopes:
            found = lists_of_dicts(scope)
            nonempty = [v for v in found if v]
            if len(nonempty) == 1:
                return nonempty[0]
            if len(nonempty) == 0 and len(found) == 1:
                return found[0]
            if len(nonempty) > 1:
                break
    raise Stop("**/financials の応答から行の列が 1 つに決まらない(形が前提と違う)。止める**")


def _fy_int(v):
    if isinstance(v, bool):
        raise FieldMissing("fiscal_year")
    if isinstance(v, int):
        return v
    if isinstance(v, str) and re.fullmatch(r"[0-9]{4}", v):
        return int(v)
    raise FieldMissing("fiscal_year")


def judge_financials(rows, doc_id):
    """(判定, 理由, DB の当期の doc_id)。判定は `残る` か `除く`。**欄が無ければ FieldMissing**(呼び出し側が止める)。
    DB の doc_id の字は、`当期の doc_id が違う` のときだけ返す(EDINET の公の識別子の形のときだけ)。"""
    if not rows:
        return "除く", "行なし", None
    for r in rows:
        if "fiscal_year" not in r:
            raise FieldMissing("fiscal_year")
        if "doc_id" not in r:
            raise FieldMissing("doc_id")
    years = [_fy_int(r["fiscal_year"]) for r in rows]
    top = [r for r, y in zip(rows, years) if y == max(years)]
    if len(top) != 1:
        return "除く", "当期が 1 行でない", None
    got = top[0]["doc_id"]
    if got == doc_id:
        return "残る", None, got
    shown = got if isinstance(got, str) and DOC_ID.fullmatch(got) else None
    return "除く", "当期の doc_id が違う", shown


# ---------------------------------------------------------------- §1-5 差し替えの節
def default_replacer(zip_bytes, text):
    """`verify_document --text` と同じ経路(`prose.build_modified_zip`)。例外を出すかだけを見る。"""
    from adapters.xbrl import prose as PR
    return PR.build_modified_zip(zip_bytes, text)


def check_replace(zip_bytes, replacer):
    """(通った?, 例外の型 or None)。"""
    try:
        replacer(zip_bytes, PROBE_SENTENCE)
    except Exception as exc:    # noqa: BLE001  文は捨てる
        return False, type(exc).__name__
    return True, None


# ---------------------------------------------------------------- §1-6・§1-7 分け方・型
def partition(k):
    """K(位置の順の docID の列)から U・予備・調整用・評価用・型。|U| < 12 は 停止 = True。"""
    k = list(k)
    u = k[:U_SIZE]
    half = len(u) // 2
    return {"U": u, "予備": k[U_SIZE:], "調整用": u[:half], "評価用": u[half:],
            "型": assign_styles(u), "停止": len(u) < U_MIN}


def assign_styles(u):
    """U の中の位置 i(0 から)に対し、型 = ("A", "B", "C")[i % 3]。"""
    return dict((d, STYLES[i % 3]) for i, d in enumerate(u))


# ---------------------------------------------------------------- 通信
def default_transport(path, key):
    """通信する唯一の所。(status, body bytes)。HTTP の 4xx・5xx は例外にせず status で返す。通信の失敗は例外のまま。"""
    import urllib.error
    import urllib.request
    req = urllib.request.Request(BASE_URL + path, headers={"X-API-Key": key, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as r:
            return r.getcode(), r.read()
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:    # noqa: BLE001
            body = b""
        return e.code, body


def fake_transport(fake_dir):
    """`--dry-run` の transport(通信しない)。`<fake_dir>/<EDINETコード>/<種類>.json` を読む。無ければ 404。"""
    def tr(path, key):
        m = re.match(r"/companies/(E[0-9]{5})(?:/(financials|ratios))?(?:\?|$)", path)
        if not m:
            return 404, b""
        kind = m.group(2) or "companies"
        p = os.path.join(fake_dir, m.group(1), kind + ".json")
        if not os.path.exists(p):
            return 404, b""
        with io.open(p, "rb") as fh:
            return 200, fh.read()
    return tr


class Api(object):
    """呼び出しの記録・1 日の上限・再試行・応答の保存。"""

    def __init__(self, key_value, transport, sleep, now, cache_root, limit, prior_uses, interval, log, say):
        self.key_value, self.transport, self.sleep, self.now = key_value, transport, sleep, now
        self.cache_root, self.limit, self.prior_uses, self.interval = cache_root, limit, dict(prior_uses), interval
        self.log = log                  # 呼び出しの行(完了も未完も。呼んだ順。試行の数は未完の行の分も数える)
        self.say = say
        self.done = {}                  # (docID, 種類) -> 完了した行
        self.called_this_run = 0
        for r in log:
            if r.get("完了"):
                self.done[(r["docID"], r["種類"])] = r

    def used_on(self, date):
        n = self.prior_uses.get(date, 0)
        for r in self.log:
            for a in r["試行"]:
                if a["JST の日付"] == date:
                    n += 1
        return n

    def attempts_by_date(self):
        dates = {}
        for r in self.log:
            for a in r["試行"]:
                dates[a["JST の日付"]] = dates.get(a["JST の日付"], 0) + 1
        return dates

    def response_path(self, doc_id, kind):
        return os.path.join(self.cache_root, doc_id, kind + ".json")

    def stored(self, doc_id, kind):
        """完了済みの行の応答の byte(sha256 が記録と同じことを確かめて返す)。失敗の行なら None。"""
        row = self.done[(doc_id, kind)]
        if row["status"] != 200:
            return None
        with io.open(self.response_path(doc_id, kind), "rb") as fh:
            blob = fh.read()
        if sha256_hex(blob) != row["sha256"]:
            raise Stop("**置いた応答が記録と違う: %s %s。止める**" % (doc_id, kind))
        return blob

    def get(self, doc_id, code, kind, on_progress):
        """1 つの応答。(行, 応答の byte or None)。完了済みなら呼ばない。"""
        if (doc_id, kind) in self.done:
            row = self.done[(doc_id, kind)]
            return row, self.stored(doc_id, kind)
        target = self.response_path(doc_id, kind)
        if os.path.exists(target):
            raise Stop("**応答の置き場に記録の無い file が在る: %s %s。何も呼ばず止める**" % (doc_id, kind))
        path = ENDPOINT_PATHS[kind] % code
        row = {"順": len(self.log) + 1, "docID": doc_id, "EDINET コード": code, "種類": kind, "path": path,
               "試行": [], "完了": False}
        self.log.append(row)
        if self.called_this_run and self.interval:
            self.sleep(self.interval)
        body, status = None, None
        for n in range(MAX_RETRIES + 1):
            t = self.now()
            date = _jst_date(t)
            if self.used_on(date) >= self.limit:
                if not row["試行"]:
                    self.log.remove(row)        # 1 回も試していない行は残さない
                on_progress(stop={"docID": doc_id, "種類": kind, "理由": "1 日(JST %s)の上限 %d 回に達した" % (date, self.limit),
                                  "時刻(UTC)": _iso(t)})
                raise LimitStop("**1 日(JST %s)の上限 %d 回に達した。ここで止める(翌日に同じ順で続ける)。止まった所: %s %s**"
                                % (date, self.limit, doc_id, kind))
            att = {"時刻(UTC)": _iso(t), "JST の日付": date}
            row["試行"].append(att)
            self.called_this_run += 1
            retryable = False
            try:
                status, body = self.transport(path, self.key_value)
                att["status"] = status
                retryable = status == 429 or status >= 500
            except Exception as exc:    # noqa: BLE001  文は捨てる
                status, body = None, None
                att["status"] = None
                att["失敗の型"] = _error_note(exc)
                retryable = True
            on_progress()
            if status in (401, 403):
                # 鍵の誤りとして 1 回目で止める(封に無い安全弁)。この行は未完のまま(完了にせず done に入れず、応答なしにも回さない)。
                # 鍵を直して続けると、この行が最初から呼び直される。送った 1 回は試行として残る(1 日の上限の数に入る)
                raise Stop("**HTTP %d。鍵の値を確かめる(この行は未完のまま残る。進みは残り、続きでこの行から呼び直す)**" % status)
            if status == 200 or not (retryable and n < MAX_RETRIES):
                break
            self.sleep(RETRY_WAIT_SEC)
        row["status"] = status
        row["再試行の回数"] = len(row["試行"]) - 1
        row["時刻(UTC)"] = row["試行"][-1]["時刻(UTC)"]
        if status is None:
            row["失敗の型"] = row["試行"][-1].get("失敗の型")
        if body is not None:
            row["bytes"] = len(body)
        if status == 200:
            if bytes_leak_key(body, self.key_value):
                raise Stop("**応答の byte に環境の鍵の値が在る(%s %s)。保存せず止める**" % (doc_id, kind))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with io.open(target, "xb") as fh:
                fh.write(body)
            row["sha256"] = sha256_hex(body)
            try:
                json.loads(body.decode("utf-8"))
                row["JSON として読める"] = True
            except (UnicodeDecodeError, ValueError):
                row["JSON として読める"] = False
        row["完了"] = True
        self.done[(doc_id, kind)] = row
        on_progress()
        self.say("  %-8s %-9s %-6s status=%s 試行 %d" % (doc_id, code, kind, status, len(row["試行"])))
        return row, (body if status == 200 else None)


# ---------------------------------------------------------------- 本体
def run(root=DEFAULT_ROOT, fetched=None, out=None, env=None, transport=None, replacer=None, sleep=time.sleep,
        now=_utcnow, zip_dir=None, cache_root=None, existing_cache_dir=None, limit=DAILY_LIMIT, prior_uses=None,
        interval=INTERVAL_SEC, dry_run=False, say=print):
    env = os.environ if env is None else env
    if root not in sys.path:
        sys.path.insert(0, root)
    replacer = replacer or default_replacer
    fetched = fetched or os.path.join(root, FETCHED_REL)
    out = out or os.path.join(root, OUT_REL)
    partial = out + ".partial"
    zip_dir = os.path.abspath(zip_dir) if zip_dir else default_zip_dir()
    existing_cache_dir = os.path.abspath(existing_cache_dir) if existing_cache_dir else default_existing_cache_dir()
    cache_root = os.path.abspath(cache_root) if cache_root else default_cache_root()
    prior_uses = PRIOR_USES if prior_uses is None else prior_uses

    if os.path.exists(out):
        raise Stop("既に在る: %s(取り直さない)" % out)
    key_value = None if dry_run else env.get(KEY_NAME)
    if not dry_run and not key_value:
        raise Stop("**%s が無い。呼ぶ前に止まる**" % KEY_NAME)
    if transport is None:
        if dry_run:
            raise Stop("**--dry-run には --fake-dir が要る**")
        transport = default_transport
    for guard in (existing_cache_dir, zip_dir):
        if _inside(cache_root, guard):
            raise Stop("**応答の置き場が既存の cache の中(%s)。何も呼ばずに止める**" % display_path(guard))

    primary, reserve = load_candidates(fetched)

    prior = {}
    if os.path.exists(partial):
        with io.open(partial, encoding="utf-8") as fh:
            prior = json.load(fh)
    before = prior.get("cache の前") or {"既存の cache": snapshot(existing_cache_dir), "ZIP の folder": snapshot(zip_dir)}
    stops = list(prior.get("停止の履歴", []))
    log = list(prior.get("呼び出し", []))

    state = {"stop": None}

    def save_partial(stop=None):
        if stop is not None:
            stops.append(stop)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with io.open(partial, "w", encoding="utf-8") as fh:
            json.dump({"呼び出し": log, "cache の前": before, "停止の履歴": stops}, fh, ensure_ascii=False, indent=1)

    api = Api(key_value, transport, sleep, now, cache_root, limit, prior_uses, interval, log, say)

    def progress(stop=None):
        save_partial(stop)

    # --- §1-4・§1-5: 候補を位置の順に照らす
    judged = []          # 照らしの行(処理した順)
    k = []

    def examine(c):
        zb, code = read_verified_zip(zip_dir, c)
        row = {"docID": c["docID"], "位置": c["位置"], "区分": c["区分"], "EDINET コード": code,
               "ZIP の sha256 が記録と一致": True}
        if any(j["EDINET コード"] == code for j in judged if "EDINET コード" in j):
            raise Stop("**候補の EDINET コードが重複(%s)。封に無い場合。止める**" % c["docID"])
        if code in EXCLUDED_CODES:
            row.update({"判定": "除く", "理由": "3 本の会社"})
            judged.append(row)
            return
        frow, blob = api.get(c["docID"], code, "financials", progress)
        row["financials の応答"] = {"status": frow["status"], "試行": len(frow["試行"])}
        if blob is None:
            row.update({"判定": "除く", "理由": "応答なし"})
            judged.append(row)
            return
        try:
            body = json.loads(blob.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise Stop("**/financials の応答が JSON として読めない(%s)。形が前提と違う。止める**" % c["docID"])
        try:
            verdict, reason, db_doc = judge_financials(extract_rows(body), c["docID"])
        except FieldMissing as exc:
            raise Stop("**/financials の応答に欄 %s が無い(%s)。欄の名前の前提が崩れている。名前を推測せず止める**"
                       % (exc.args[0], c["docID"]))
        row["判定"], row["理由"] = verdict, reason
        if db_doc is not None and verdict == "除く":
            row["DB の当期の doc_id"] = db_doc
        if verdict == "残る":
            ok, etype = check_replace(zb, replacer)
            row["差し替え"] = "通った" if ok else "差し替えの節なし"
            if not ok:
                row.update({"判定": "除く", "理由": "差し替えの節なし", "差し替えの例外の型": etype})
        judged.append(row)
        if row["判定"] == "残る":
            k.append(c["docID"])

    try:
        for c in primary:
            examine(c)
        reserve_examined = len(k) < U_SIZE
        if reserve_examined:
            for c in reserve:
                examine(c)

        parts = partition(k)
        not_examined = [] if reserve_examined else [{"docID": c["docID"], "位置": c["位置"], "区分": c["区分"],
                                                     "判定": "照らさなかった(主の候補で K が %d 以上)" % U_SIZE}
                                                    for c in reserve]
        reasons = {}
        for j in judged:
            if j["判定"] == "除く":
                reasons[j["理由"]] = reasons.get(j["理由"], 0) + 1

        # --- U の会社だけ /companies と /ratios
        material = []
        code_of = dict((j["docID"], j["EDINET コード"]) for j in judged)
        if not parts["停止"]:
            for d in parts["U"]:
                m = {"docID": d}
                for kind in ("companies", "ratios"):
                    r, blob = api.get(d, code_of[d], kind, progress)
                    m[kind] = {"status": r["status"], "JSON として読める": r.get("JSON として読める", False)}
                material.append(m)
        missing = [m["docID"] for m in material
                   if not all(m[kk]["status"] == 200 and m[kk]["JSON として読める"] for kk in ("companies", "ratios"))]
    except LimitStop:
        raise
    except Stop:
        save_partial()
        raise

    after = {"既存の cache": snapshot(existing_cache_dir), "ZIP の folder": snapshot(zip_dir)}
    if after != before:
        save_partial()
        raise Stop("**既存の cache か ZIP の folder の件数か名前の一覧が、走る前と後で違う。記録を書かずに止める(進みは残る)**")

    by_date = api.attempts_by_date()
    rec = {
        "seal": SEAL,
        "step": "**P27 段 1 §1・§2。候補の照らしと U の決定、U の /companies と /ratios の取得。費用 0 USD(Free プラン)**",
        "dry_run": bool(dry_run),
        "鍵": {"環境変数の名前": KEY_NAME, "値": "**読まない・印字しない・記録しない**"},
        "応答の値の扱い": "**この記録に応答の値(数・会社名・業種の字)は入れない。** 応答は repo の外に受け取った byte のまま置き、sha256 だけを記録する",
        "除いた 3 コード": {"コード": list(EXCLUDED_CODES), "除かれた件数": sum(1 for j in judged if j.get("理由") == "3 本の会社")},
        "照らし": judged + not_examined,
        "予備の候補を照らしたか": reserve_examined,
        "除いた理由の内訳": reasons,
        "K": list(k),
        "|K|": len(k),
        "U": parts["U"],
        "|U|": len(parts["U"]),
        "調整用": parts["調整用"],
        "評価用": parts["評価用"],
        "予備": parts["予備"],
        "型の割り当て": parts["型"],
        "止め": ("|U| < %d。レポートを書かず、追補の封が書かれるまで進まない(引き直さない)" % U_MIN) if parts["停止"] else None,
        "U の材料": material,
        "材料が欠けた U の会社": missing,
        "呼び出し": [dict((kk, vv) for kk, vv in r.items() if kk != "完了") for r in log],
        "回数": {
            "上限(1 日 JST・再試行を含む)": limit,
            "既に使った数として数えた分(封 §11-0 の下見)": dict(prior_uses),
            "この script の試行の合計": sum(by_date.values()),
            "試行の日別(JST)": by_date,
            "最大の 1 日(下見の分を含む)": max([by_date.get(dd, 0) + prior_uses.get(dd, 0) for dd in set(by_date) | set(prior_uses)] or [0]),
            "呼び出し(応答の最終の行)の数": sum(1 for r in log if r.get("完了")),       # 完了した行だけ(再試行の途中で止まった未完の行は数えない)
            "応答なしの数": sum(1 for r in log if r.get("完了") and r.get("status") != 200),
        },
        "上限で止まった履歴": stops,
        "置いた場所": {"応答": display_path(cache_root) + "/<docID>/{financials,companies,ratios}.json",
                    "既存の cache": "**`~/.cache/audit-core/edinet/` と `~/.cache/audit-core/edinet-fresh-2026-10-21/` には 1 file も書かない**。repo に応答は入れない"},
        "cache の前後": {"前": before, "後": after, "変化なし": True},
        "取得した時刻(UTC)": _iso(now()),
        "引き直さない": "封 §1-6・§2-1。応答なしの会社は引き直さない。U の後ろの会社(予備)は取らない・書かない",
        "limits": ["**照らしと取得だけである。**レポートは書いていない・engine は通していない",
                   "応答の値は読んだが記録していない(doc_id の字は、当期の doc_id が違う会社の分だけ記録した)",
                   "U の会社の /companies と /ratios は JSON として読めるかだけ確かめた(中身は見ていない)"],
    }
    text = json.dumps(rec, ensure_ascii=False, indent=1)
    leaks = key_leaks(text, key_value)
    if leaks:
        save_partial()
        raise Stop("**鍵らしい字が記録に在る(%s)。書かずに止める**" % ", ".join(leaks))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
    with io.open(out, encoding="utf-8") as fh:
        written = fh.read()
    leaks = key_leaks(written, key_value)
    if leaks:
        os.remove(out)
        raise Stop("**書いた file に鍵らしい字(%s)。file を消して止める**" % ", ".join(leaks))
    if os.path.exists(partial):
        os.remove(partial)
    say("=== K %d・U %d(調整用 %d・評価用 %d)・予備 %d・除いた %s・試行 %d 回 ==="
        % (len(k), len(parts["U"]), len(parts["調整用"]), len(parts["評価用"]), len(parts["予備"]),
           json.dumps(reasons, ensure_ascii=False), rec["回数"]["この script の試行の合計"]))
    if parts["停止"]:
        say("**|U| < %d。止める(記録は書いた)**" % U_MIN)
    say("-> " + out)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=DEFAULT_ROOT, help="audit-core の folder(既定: この script の親)")
    ap.add_argument("--fetched", default=None, help="候補の記録(既定: fixtures/xbrl/fresh/fetched_2026-10-21.json)")
    ap.add_argument("--out", default=None, help="記録の出力先(既定: fixtures/xbrl/p27/dbfetch_2026-10-27.json)")
    ap.add_argument("--zip-dir", default=None, help="ZIP を読む folder(既定: ~/.cache/audit-core/%s/。読むだけ)" % FRESH_ZIP_DIR_NAME)
    ap.add_argument("--cache-root", default=None, help="応答の置き場(既定: ~/.cache/audit-core/%s/)" % P27_CACHE_DIR_NAME)
    ap.add_argument("--existing-cache-dir", default=None, help="件数を数えるだけの既存の cache(既定: ~/.cache/audit-core/edinet/)")
    ap.add_argument("--limit", type=int, default=DAILY_LIMIT)
    ap.add_argument("--already-used", type=int, default=None,
                    help="今日(JST)に既に使った回数(既定: 封 §11-0 の下見 2 回を 2026-10-27 の分として数える)")
    ap.add_argument("--interval", type=float, default=INTERVAL_SEC)
    ap.add_argument("--dry-run", action="store_true", help="通信しない。--fake-dir の file を応答の代わりに読む。--out と --cache-root が要る")
    ap.add_argument("--fake-dir", default=None)
    a = ap.parse_args(argv)
    transport = None
    if a.dry_run:
        if not (a.fake_dir and a.out and a.cache_root):
            raise Stop("**--dry-run には --fake-dir・--out・--cache-root が要る(本物の記録・置き場に書かないため)**")
        transport = fake_transport(a.fake_dir)
    prior = None
    if a.already_used is not None:
        prior = {_jst_date(_utcnow()): a.already_used}
    rec = run(root=os.path.abspath(a.root), fetched=a.fetched, out=a.out, transport=transport, zip_dir=a.zip_dir,
              cache_root=a.cache_root, existing_cache_dir=a.existing_cache_dir, limit=a.limit, prior_uses=prior,
              interval=0.0 if a.dry_run else a.interval, dry_run=a.dry_run)
    return 3 if rec["止め"] else 0


if __name__ == "__main__":
    sys.exit(main())
