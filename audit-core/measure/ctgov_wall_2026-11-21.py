# -*- coding: utf-8 -*-
u"""封 docs/CTGOV_WALL_SEAL_2026-11-21.md(CT0 ― 治験の公開データで、いまの engine の数の読み取りが英語の論文の要旨の数をどれだけ拾うか。壁の確かめ)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。** engine(``core/``・``adapters/``)は 1 行も変えない。数の読み取りは engine の関数(``adapters/xbrl/recipes.py`` の ``_numbers_of``)を既定の profile で呼ぶ(写さない)。

    python3 measure/ctgov_wall_2026-11-21.py --fetch     # 通信する(0 USD)。ClinicalTrials.gov の API v2 と NCBI の E-utilities から材料を取る。走らせるのは司令塔だけ
    python3 measure/ctgov_wall_2026-11-21.py             # 置き場から数えて記録を書く。通信しない
    python3 measure/ctgov_wall_2026-11-21.py --check     # 置き場から数え直して記録と照らす。通信しない

守り(封 §1・§5):
  - 材料(取った JSON・XML・対の表)は ``~/.cache/audit-core/ctgov_2026-11-21/`` にだけ置く。置き場が repo の中なら止まる。置き場に何かが在れば ``--fetch`` は止まる(取り直さない)。
  - 呼び出しの間は 1 回ごとに 1 秒以上あける(両方の出所)。E-utilities には ``tool`` を付ける。``email`` は付けない。断られたら(200 でない返事)そこで止まる。
  - 記録 ``fixtures/ctgov/wall_2026-11-21.json`` には、対の番号ごとの数・材料の sha256・取った日付・engine の指紋だけを書く。
    要旨の字・数の字・登録番号・PMID・題・薬の名・会社の名は書かない。書く前と書いた後に検査し、在れば止まる。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- API v2 の問い合わせ: ``/api/v2/studies?aggFilters=results:with,studyType:int,phase:3&pageSize=10&format=json``(並びの指定は付けない。仕様は「既定では並べない」= API が返す順のまま)。
  次のページは ``nextPageToken`` を ``pageToken`` に入れ、ほかの引数は変えない。仕様(``/api/oas/v2``)の ``aggFilters`` の例 ``results:with`` の書き方に合わせた。
  ``phase:3``・``studyType:int`` の key は ClinicalTrials.gov の検索画面の絞り込みの key(仕様の YAML の中には例が無い)。返った 1 試験ごとに、結果が在る・介入の試験・Phase 3 を JSON の欄(``hasResults``・``designModule.studyType``・``designModule.phases``)で
  もう 1 度確かめ、合わない試験は(見た試験の数に数えたうえで)飛ばす。
- 「見た試験」= 並びの頭から 1 つずつ取り出して調べた試験(飛ばした試験も数える)。400 本目を調べ終わった時点で対が 10 に届かなければ止める。10 対目ができたらその場で止める(それ以上は呼ばない)。
- 要旨の本文 = efetch の XML の ``Abstract`` の下の ``AbstractText`` 全部の字(入れ子の字を含む。``Label`` の字は含めない)を空白 1 つで連ねたもの。題は含めない。対にする条件の「そのまま」= NFKC にそろえる前の字に ``in``。
- 登録の側の値の読める行 = 評価項目の ``measurements[].value``(字が数として読める)・有害事象の ``seriousEvents[].stats[]``・``otherEvents[].stats[]`` の ``numAffected``(整数か、数として読める字)。1 つの値 = 1 行。
  数として読める = 符号つきの 10 進(桁の区切り「,」・小数を含んでよい)。
- 分母の類の判定: ``CI``・``HR``・``OR``・``RR``・``n =`` などの略語は字の大小を区別する。``confidence interval``・``hazard ratio`` などの語と ``patients`` などの語は大小を区別しない。直前の窓は字数のとおり(空白も 1 字)。
  類 R の窓は封 §8 の追記で 16 字(``hazard ratio`` に空白と記号をはさんでも当たる)。
  N の「直後」は空白 1 字以上をはさんだ語の終わりが語の切れ目(``\\b``)であること。
- 分母の正規表現の (b)「前後に英字が接した字」= 当たった字の直前か直後の 1 字が ASCII の英字。(a)「登録番号の字の中」= ``NCT`` と数字の連なり ``NCT\\d+`` の範囲に入る当たり。
- 位置の照らし: engine が返した ``(start, end)`` が分母の当たり ``(a, b)`` と 1 字でも重なる(``start < b`` かつ ``a < end``)とき、その分母の字を「拾った」と数える。どの分母の字とも重ならない engine の返りが「分母の外で拾った」。
  「含む」でなく「重なる」にした理由: 医学の文の負の数の符号は U+2212(−)が多く、分母の正規表現はこの符号を数の字に含めるが、engine の数の読み取りの符号の一覧(``△▲－-マイナス``)には U+2212 が無く、符号の手前から読み始めない。
  「含む」だと、同じ数を engine が読んでいるのに「拾わなかった」+「分母の外で拾った」と数えてしまう。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

from adapters.xbrl import recipes as R                  # noqa: E402
from adapters.xbrl import verify_document as VD         # noqa: E402
from adapters.xbrl import vocabulary as V               # noqa: E402

SEAL_REL = "docs/CTGOV_WALL_SEAL_2026-11-21.md"
SEAL_COMMIT = "9e41971b"
SEAL_ADDENDUM_COMMIT = "455c77a6"                # 封の §8 追記(類 R の窓を 12 字から 16 字に。実装の席が決めた所の控え)
SCRIPT_REL = "measure/ctgov_wall_2026-11-21.py"
RECORD_REL = "fixtures/ctgov/wall_2026-11-21.json"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "ctgov_2026-11-21")
PAIRS_NAME = "pairs.json"

# ---- 封 §1 の決めごと(字で留める。封の門が封の字と照らす)
PAIRS_WANT = 10                                 # 対の本数
STUDIES_STOP = 400                              # 見た試験がこの数に達したら止める
MIN_GAP_SECONDS = 1.0                           # 呼び出しの間(両方の出所)
TOOL = "audit-core-ct0"                         # E-utilities の tool。email は付けない
API_BASE = "https://clinicaltrials.gov/api/v2"
STUDIES_URL = API_BASE + "/studies"
VERSION_URL = API_BASE + "/version"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
AGG_FILTERS = "results:with,studyType:int,phase:3"
PAGE_SIZE = 10
PROFILE = "P27"                                 # 封 §2-2: いまの engine の既定の profile

# ---- 封 §2 の分母(字で留める)
DENOM_PATTERN = u"(?<![A-Za-z0-9.])[-−]?\\d{1,3}(?:,\\d{3})+(?:\\.\\d+)?|(?<![A-Za-z0-9.])[-−]?\\d+(?:\\.\\d+)?"
DENOM_RE = re.compile(DENOM_PATTERN)
NCT_RE = re.compile(r"NCT\d+")
ALPHA_RE = re.compile(r"[A-Za-z]")
CLASSES = ("P", "C", "N", "R", "V", "Y", "O")
C_WORDS = ("CI", "confidence interval")        # 直前 C_WINDOW 字
C_WINDOW = 20
N_BEFORE = ("n =", "n=", "N =", "N=")          # 直前 N_WINDOW 字
N_WINDOW = 8
N_AFTER = ("patients", "participants", "subjects", "women", "men", "children")   # 直後(空白をはさんで)
R_ABBR = ("HR", "OR", "RR")                     # 直前 R_WINDOW 字(大小を区別する)
R_WORDS = ("hazard ratio", "odds ratio", "risk ratio")
R_WINDOW = 16                                   # 封 §8 の追記: 12 字から 16 字に替えた(§2 の 12 より勝つ)
V_BEFORE_RE = re.compile(r"[pP]\s*[<=>]")      # 直前 V_WINDOW 字
V_WINDOW = 8
Y_RANGE = (1900, 2099)
N_AFTER_RE = re.compile(r"\s+(?:" + "|".join(N_AFTER) + r")\b", re.I)
LIMITS = [
    u"10 対だけ。並びは API の返す順で、無作為ではない。Phase 3・結果が在る・要旨に登録番号が在る、に寄る。",
    u"分母の正規表現と類分けは司令塔が書いた。数の字の分母であって、「主張している数」の分母ではない(年・用量・人数を全部含む)。",
    u"engine の読み取りは日本語の決算の文に合わせて作ってある。「英語を拾わない」は欠陥ではなく作りの範囲の外。この便が測るのは、その範囲の外の量。",
    u"結ぶ・値を比べる、は測っていない。"]

# ---- 記録の禁止(封 §5)。欄の名(小文字にして照らす)と、字の形
FORBIDDEN_KEYS = ("abstract", "title", "text", "sentence", "nct", "nctid", "nct_id", "pmid", "drug", "sponsor",
                  u"要旨", u"題", u"文", u"数の字", u"登録番号", u"薬の名", u"会社の名")
NCT_FORM_RE = re.compile(r"NCT\s*\d", re.I)
PMID_FORM_RE = re.compile(r"PMID|(?<![0-9])\d{7,8}(?![0-9])", re.I)
HEX_RE = re.compile(r"[0-9a-fA-F]{32,}")
LEAK_GRAM = 16


class Stop(SystemExit):
    pass


def od(pairs=()):
    return collections.OrderedDict(pairs)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    with open(path, "rb") as fh:
        return sha256_bytes(fh.read())


def nfkc(s):
    return unicodedata.normalize("NFKC", s)


def dumps(o):
    return json.dumps(o, ensure_ascii=False, indent=2) + u"\n"


def walk_keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            for x in walk_keys(v):
                yield x
    elif isinstance(o, list):
        for v in o:
            for x in walk_keys(v):
                yield x


def inside_repo(path):
    u"""path が repo の中(git の木)なら真。path から上へたどって ``.git`` が在る場所も「中」と数える。"""
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


# ======================================================================================================
# 分母(封 §2-1)と類分け
def is_p(text, a, b):
    return text[b:b + 1] == u"%"


def is_c(text, a, b):
    before = text[max(0, a - C_WINDOW):a]
    return C_WORDS[0] in before or C_WORDS[1] in before.lower()


def is_n(text, a, b):
    before = text[max(0, a - N_WINDOW):a]
    return any(t in before for t in N_BEFORE) or N_AFTER_RE.match(text, b) is not None


def is_r(text, a, b):
    before = text[max(0, a - R_WINDOW):a]
    return any(t in before for t in R_ABBR) or any(t in before.lower() for t in R_WORDS)


def is_v(text, a, b):
    return V_BEFORE_RE.search(text[max(0, a - V_WINDOW):a]) is not None


def is_y(text, a, b):
    s = text[a:b]
    return re.fullmatch(r"\d{4}", s) is not None and Y_RANGE[0] <= int(s) <= Y_RANGE[1]


#: 上から先に当たった類(封 §2-1)。O は残り
CLASS_TESTS = (("P", is_p), ("C", is_c), ("N", is_n), ("R", is_r), ("V", is_v), ("Y", is_y))


def classify(text, a, b):
    for name, test in CLASS_TESTS:
        if test(text, a, b):
            return name
    return "O"


def denominator(text):
    u"""NFKC にそろえた字 ``text`` の数の字の分母。(開始, 終わり, 類) の並び。"""
    nct = [m.span() for m in NCT_RE.finditer(text)]
    out = []
    for m in DENOM_RE.finditer(text):
        a, b = m.span()
        if any(x <= a and b <= y for x, y in nct):                                  # (a) 登録番号の字の中
            continue
        if (a > 0 and ALPHA_RE.match(text[a - 1])) or (b < len(text) and ALPHA_RE.match(text[b])):   # (b) 前後に英字が接した字
            continue
        out.append((a, b, classify(text, a, b)))
    return out


# ======================================================================================================
# engine の読み取り(封 §2-2)
def engine_picks(text, profile_name=None):
    u"""engine の数の読み取りの関数(profile から選ぶ道は engine の ``_numbers_of``)に字を渡して返った (start, end) の並び。"""
    prof = V.PROFILES[profile_name or PROFILE]
    return [(a, b) for (a, b, _v, _u, _p) in R._numbers_of(prof, text)]


def covers(engine_span, den_span):
    return engine_span[0] < den_span[1] and den_span[0] < engine_span[1]


def tally_text(raw):
    u"""要旨の字(NFKC にそろえる前)→ 類ごとの (分母, 拾った)・分母の外で拾った数。"""
    text = nfkc(raw)
    den = denominator(text)
    picks = engine_picks(text)
    per = od((c, od([(u"分母", 0), (u"拾った", 0)])) for c in CLASSES)
    for a, b, c in den:
        per[c][u"分母"] += 1
        if any(covers(p, (a, b)) for p in picks):
            per[c][u"拾った"] += 1
    outside = sum(1 for p in picks if not any(covers(p, (a, b)) for a, b, _c in den))
    return per, outside


# ======================================================================================================
# 登録の側(封 §2-3)
NUM_READABLE_RE = re.compile(r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")


def readable(v):
    if isinstance(v, bool):
        return False
    if isinstance(v, int):
        return True
    return isinstance(v, str) and NUM_READABLE_RE.fullmatch(v.strip()) is not None


def registry_rows(study):
    u"""登録の JSON の結果の欄から、値の字が数として読める行の数と、0 行のときの理由(欄の名)。"""
    rows = 0
    reasons = []
    rs = study.get("resultsSection")
    if not isinstance(rs, dict) or not rs:
        return 0, [u"resultsSection が無い"]
    om = (rs.get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []
    n_om = 0
    for m in om:
        for cl in m.get("classes") or []:
            for cat in cl.get("categories") or []:
                for me in cat.get("measurements") or []:
                    if readable(me.get("value")):
                        n_om += 1
    ae = rs.get("adverseEventsModule") or {}
    n_ae = 0
    for key in ("seriousEvents", "otherEvents"):
        for ev in ae.get(key) or []:
            for st in ev.get("stats") or []:
                if readable(st.get("numAffected")):
                    n_ae += 1
    rows = n_om + n_ae
    if rows == 0:
        reasons.append(u"outcomeMeasuresModule.outcomeMeasures の measurements.value が数として読める行が無い(outcomeMeasures %d 件)" % len(om))
        reasons.append(u"adverseEventsModule の seriousEvents・otherEvents の stats.numAffected が数として読める行が無い")
    return rows, reasons


# ======================================================================================================
# 取る(--fetch)
def urllib_transport(url):
    req = urllib.request.Request(url, headers={"User-Agent": TOOL})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


class Throttle(object):
    u"""呼び出しの間を ``MIN_GAP_SECONDS`` 以上あける(両方の出所をまとめて 1 本で)。"""

    def __init__(self, transport, sleep=time.sleep, clock=time.monotonic):
        self.transport = transport
        self.sleep = sleep
        self.clock = clock
        self.last = None
        self.calls = []

    def __call__(self, url):
        if self.last is not None:
            wait = MIN_GAP_SECONDS - (self.clock() - self.last)
            if wait > 0:
                self.sleep(wait)
        self.last = self.clock()
        self.calls.append(url)
        return self.transport(url)


def studies_url(token=None):
    q = [("aggFilters", AGG_FILTERS), ("pageSize", PAGE_SIZE), ("format", "json")]
    if token:
        q.append(("pageToken", token))
    return STUDIES_URL + "?" + urllib.parse.urlencode(q, safe=":,")


def efetch_url(pmid):
    return EFETCH_URL + "?" + urllib.parse.urlencode([("db", "pubmed"), ("id", pmid), ("retmode", "xml"), ("tool", TOOL)])


def get_json(th, url):
    status, body = th(url)
    if status != 200:
        raise Stop(u"**ClinicalTrials.gov が %s を返した。止める**" % status)
    try:
        return json.loads(body.decode("utf-8"))
    except ValueError:
        raise Stop(u"**ClinicalTrials.gov の返事が JSON でない。止める**")


def condition_ok(st):
    dm = (st.get("protocolSection") or {}).get("designModule") or {}
    return st.get("hasResults") is True and dm.get("studyType") == "INTERVENTIONAL" and "PHASE3" in (dm.get("phases") or [])


def pick_reference(st):
    u"""``referencesModule`` の文献のうち、型が RESULT で PMID が在るものを並びの頭から 1 つ。無ければ None。"""
    refs = ((st.get("protocolSection") or {}).get("referencesModule") or {}).get("references") or []
    for r in refs:
        if r.get("type") == "RESULT" and r.get("pmid"):
            return str(r["pmid"])
    return None


def abstract_text(xml_bytes):
    u"""efetch の XML → 要旨の本文(``AbstractText`` の字を空白 1 つで連ねる。題・Label は含めない)。無ければ None。"""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return None
    parts = []
    for el in root.iter("AbstractText"):
        t = u"".join(el.itertext()).strip()
        if t:
            parts.append(t)
    return u" ".join(parts) if parts else None


def write_exclusive(path, data):
    with open(path, "xb") as fh:
        fh.write(data)


def fetch(cache=None, transport=None, sleep=time.sleep, clock=time.monotonic, today=None, say=print):
    u"""封 §1 のとおり取る。置き場にだけ書く。置き場が repo の中・置き場に何かが在れば止まる。"""
    cache = os.path.abspath(cache or CACHE_DIR)
    if inside_repo(cache):
        raise Stop(u"**置き場が repo の中。止める**")
    if os.path.exists(cache) and os.listdir(cache):
        raise Stop(u"**置き場に既に何かが在る。取り直さない。止める**")
    os.makedirs(cache, exist_ok=True)
    th = Throttle(transport or urllib_transport, sleep=sleep, clock=clock)
    version = get_json(th, VERSION_URL)
    pairs = []
    seen = 0
    skips = collections.Counter()
    token = None
    why = None
    while why is None:
        page = get_json(th, studies_url(token))
        for st in page.get("studies") or []:
            seen += 1
            nct = (((st.get("protocolSection") or {}).get("identificationModule") or {}).get("nctId")) or u""
            pmid = None
            if not condition_ok(st):
                skips[u"条件(結果が在る・介入・Phase 3)に合わない"] += 1
            elif not nct:
                skips[u"登録番号が無い"] += 1
            else:
                pmid = pick_reference(st)
                if pmid is None:
                    skips[u"RESULT の文献(番号つき)が無い"] += 1
            if pmid is not None:
                status, xml_body = th(efetch_url(pmid))
                if status != 200:
                    raise Stop(u"**E-utilities が %s を返した(email を付けない形で断られた場合を含む)。止める**" % status)
                text = abstract_text(xml_body)
                if text is None:
                    if b"<ERROR" in xml_body or xml_body.lstrip().startswith(b"{"):
                        raise Stop(u"**E-utilities の返事がエラーの形。止める**")
                    skips[u"要旨が無い"] += 1
                elif nct not in text:
                    skips[u"要旨に登録番号が無い"] += 1
                else:
                    n = len(pairs) + 1
                    write_exclusive(os.path.join(cache, "study_%d.json" % n), dumps(st).encode("utf-8"))
                    write_exclusive(os.path.join(cache, "abstract_%d.xml" % n), xml_body)
                    pairs.append(od([(u"n", n), (u"nct", nct), (u"pmid", pmid)]))
            if len(pairs) >= PAIRS_WANT:
                why = u"10 対そろった"
                break
            if seen >= STUDIES_STOP:
                why = u"見た試験が %d に達した" % STUDIES_STOP
                break
        if why is None:
            token = page.get("nextPageToken")
            if not token:
                why = u"候補が尽きた"
    log = od([(u"date", today or time.strftime("%Y-%m-%d")), (u"api", version), (u"seen", seen), (u"skips", od(sorted(skips.items()))), (u"stop", why),
              (u"pairs", pairs), (u"calls", len(th.calls))])
    write_exclusive(os.path.join(cache, PAIRS_NAME), dumps(log).encode("utf-8"))
    say(u"対 %d・見た試験 %d・止めた理由: %s" % (len(pairs), seen, why))
    return log


# ======================================================================================================
# 数える(置き場から。通信しない)
def load_cache(cache):
    u"""置き場の表と材料を読む。(表, [(番号, 登録の JSON, 要旨の XML の bytes, 登録の JSON の bytes)])。形が違えば止まる。"""
    cache = os.path.abspath(cache or CACHE_DIR)
    p = os.path.join(cache, PAIRS_NAME)
    if not os.path.isfile(p):
        raise Stop(u"**置き場に対の表が無い(--fetch が済んでいない)。止める**")
    with io.open(p, encoding="utf-8") as fh:
        log = json.load(fh)
    pairs = log[u"pairs"]
    if not (1 <= len(pairs) <= PAIRS_WANT) or [x[u"n"] for x in pairs] != list(range(1, len(pairs) + 1)):
        raise Stop(u"**対の表の番号が 1 から順でないか、本数が 1〜%d でない。止める**" % PAIRS_WANT)
    mats = []
    for x in pairs:
        n = x[u"n"]
        with open(os.path.join(cache, "study_%d.json" % n), "rb") as fh:
            sbytes = fh.read()
        with open(os.path.join(cache, "abstract_%d.xml" % n), "rb") as fh:
            xbytes = fh.read()
        mats.append((n, json.loads(sbytes.decode("utf-8")), xbytes, sbytes))
    return log, mats


def ratio(n, d):
    return None if not d else round(100.0 * n / d, 1)


def record_skips(skips):
    u"""置き場の表の「飛ばした理由」の名を、記録に入れる名にする。記録の検査は PMID・NCT の語を止めるので、古い置き場の名(PMID の語を含む)の語を替える(数は変えない)。"""
    return od((k.replace(u"PMID つき", u"番号つき").replace(u"PMID", u"番号").replace(u"NCT", u"登録番号"), v) for k, v in skips.items())


def build_record(log, mats):
    u"""置き場の表と材料 → (記録, 漏れの検査に使う材料の字)。書かない。"""
    if V.DEFAULT_PROFILE != PROFILE:
        raise Stop(u"**engine の既定の profile が %s でない。止める**" % PROFILE)
    fp = VD.engine_fingerprint()
    secret = []
    rows = []
    total = od((c, [0, 0]) for c in CLASSES)
    out_all = 0
    zero_pairs = 0
    for (n, study, xbytes, sbytes), x in zip(mats, log[u"pairs"]):
        text = abstract_text(xbytes)
        if text is None or x[u"nct"] not in text:
            raise Stop(u"**対 %d の要旨に登録番号が無い(置き場が封の対の付け方と違う)。止める**" % n)
        secret.append((x[u"nct"], x[u"pmid"], text))
        per, outside = tally_text(text)
        reg, reasons = registry_rows(study)
        zero_pairs += 1 if reg == 0 else 0
        out_all += outside
        for c in CLASSES:
            total[c][0] += per[c][u"分母"]
            total[c][1] += per[c][u"拾った"]
        rows.append(od([
            (u"番号", n),
            (u"数の字の数", sum(per[c][u"分母"] for c in CLASSES)),
            (u"類別", per),
            (u"拾った数", sum(per[c][u"拾った"] for c in CLASSES)),
            (u"分母の外で拾った数", outside),
            (u"登録の側の値の読める行の数", reg),
            (u"登録の側が 0 行の理由(欄の名)", reasons),
            (u"材料の sha256", od([(u"登録の JSON", sha256_bytes(sbytes)), (u"要旨の XML", sha256_bytes(xbytes))]))]))
    den_all = sum(v[0] for v in total.values())
    pick_all = sum(v[1] for v in total.values())
    nrv = [sum(total[c][i] for c in ("N", "R", "V")) for i in (0, 1)]
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"封の追記の commit"] = SEAL_ADDENDUM_COMMIT
    rec[u"step"] = u"CT0(治験の公開データで、いまの engine の数の読み取りが英語の論文の要旨の数をどれだけ拾うか。壁の確かめ)(0 USD・engine は 0 行)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"engine の指紋"] = od((k, fp[k]) for k in ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files"))
    rec[u"profile"] = PROFILE
    rec[u"取った日付"] = log[u"date"]
    rec[u"出どころの版"] = od([(u"登録側の API の版", log[u"api"].get(u"apiVersion")), (u"登録側のデータの時刻", log[u"api"].get(u"dataTimestamp"))])
    rec[u"取り方の数"] = od([(u"見た試験", log[u"seen"]), (u"対", len(log[u"pairs"])), (u"止めた理由", log[u"stop"]), (u"飛ばした試験の理由別", record_skips(log[u"skips"])), (u"呼び出しの数", log[u"calls"])])
    rec[u"対"] = rows
    rec[u"集計"] = od([
        (u"対の数", len(rows)), (u"数の字の数", den_all), (u"拾った数", pick_all), (u"分母の外で拾った数", out_all),
        (u"類別", od((c, od([(u"分母", total[c][0]), (u"拾った", total[c][1])])) for c in CLASSES))])
    rec[u"予測の判定に要る数(CT0-1〜CT0-7。当たり・外れは結果の文書で)"] = od([
        (u"CT0-1 見た試験と対の数と止めた理由", od([(u"見た試験", log[u"seen"]), (u"対", len(rows)), (u"止めた理由", log[u"stop"])])),
        (u"CT0-2 拾った / 数の字の全部", od([(u"拾った", pick_all), (u"分母", den_all), (u"%", ratio(pick_all, den_all))])),
        (u"CT0-3 類 P で拾った / 類 P", od([(u"拾った", total["P"][1]), (u"分母", total["P"][0]), (u"%", ratio(total["P"][1], total["P"][0]))])),
        (u"CT0-4 類 N・R・V の合計で拾った / 合計", od([(u"拾った", nrv[1]), (u"分母", nrv[0]), (u"%", ratio(nrv[1], nrv[0]))])),
        (u"CT0-5 類 C で拾った / 類 C", od([(u"拾った", total["C"][1]), (u"分母", total["C"][0]), (u"%", ratio(total["C"][1], total["C"][0]))])),
        (u"CT0-6 分母の外で拾った(10 対の合計)", out_all),
        (u"CT0-7 登録の側の値の読める行が 0 の対の数", zero_pairs)])
    rec[u"限界"] = list(LIMITS)
    return rec, secret


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(欄・字の形・材料の字)が無いか。在れば止める。"""
    bad = sorted(set(str(k) for k in walk_keys(rec) if str(k).lower() in FORBIDDEN_KEYS))
    if bad:
        raise Stop(u"**記録に repo へ入れない欄がある: %s。止める**" % u",".join(bad))
    scan = HEX_RE.sub(u"", text)
    if NCT_FORM_RE.search(scan):
        raise Stop(u"**記録に登録番号の形の字が在る。止める**")
    if PMID_FORM_RE.search(scan):
        raise Stop(u"**記録に PMID の形の字が在る。止める**")
    for nct, pmid, abstract in (secret or ()):
        if nct in scan or re.search(r"(?<![0-9])%s(?![0-9])" % re.escape(pmid), scan):
            raise Stop(u"**記録に材料の登録番号か PMID が在る。止める**")
        flat = u" ".join(abstract.split())
        for i in range(0, max(0, len(flat) - LEAK_GRAM + 1)):
            g = flat[i:i + LEAK_GRAM]
            if g.strip() and g in scan:
                raise Stop(u"**記録に要旨の字が在る。止める**")


def record_text(rec, secret=None):
    text = dumps(rec)
    check_clean(rec, text, secret)
    return text


def write_record(path, rec, secret=None):
    u"""書く前と書いた後に検査する。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(path))
    text = record_text(rec, secret)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_exclusive(path, text.encode("utf-8"))
    with io.open(path, encoding="utf-8") as fh:
        back = fh.read()
    try:
        check_clean(rec, back, secret)
    except SystemExit:
        os.remove(path)
        raise


def run(root=ROOT, cache=None, out=None, say=print):
    log, mats = load_cache(cache)
    rec, secret = build_record(log, mats)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(対 %d)" % (os.path.basename(out), len(mats)))
    return rec


def check(root=ROOT, cache=None, rec_path=None, say=print):
    u"""置き場から数え直して記録と照らす。通信しない。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    log, mats = load_cache(cache)
    now, secret = build_record(log, mats)
    if dumps(now) != dumps(rec):
        raise Stop(u"**置き場から数え直した記録が、今の記録と違う。止める**")
    check_clean(rec, text, secret)
    say(u"--check: 記録は置き場から数え直した数と同じ(対 %d)" % len(mats))
    return now


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fetch", action="store_true", help="通信する(0 USD)。材料を置き場へ取る")
    ap.add_argument("--check", action="store_true", help="置き場から数え直して記録と照らす。通信しない")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--cache", default=None)
    a = ap.parse_args(argv)
    if a.fetch and a.check:
        raise Stop(u"**--fetch と --check は同時に使わない。止める**")
    if a.fetch:
        fetch(cache=a.cache)
    elif a.check:
        check(root=a.root, cache=a.cache)
    else:
        run(root=a.root, cache=a.cache)


if __name__ == "__main__":
    main()
