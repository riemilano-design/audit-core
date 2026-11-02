# -*- coding: utf-8 -*-
u"""段 1: 手元の有報 97 書類の前年の有報を取り、prev の当期欄と next の前期欄を要素ごとに突き合わせる(封 docs/XBRL_RESTATED_PRIOR_SEAL_2026-11-02.md §1)。

    python3 measure/xbrl_prior_pairs_2026-11-02.py                      # 実走(鍵 EDINET_API_KEY のある席。前年の有報を新しい folder に取る)
    python3 measure/xbrl_prior_pairs_2026-11-02.py --stub <dir> --out <path>   # 作り物の backend(dir/listing.json・dir/<docID>.zip)で走らせる(門が使う)

- engine は変えない。facts と contexts の読み取りは adapters.xbrl.instance.load_instance(儀式と同じ)。DEI は engine が持たないので
  この script が .xbrl から読む。
- 通信は EDINET API v2 だけ(日付一覧 documents.json type=2、ZIP documents/<docID> type=1)。鍵は環境変数 EDINET_API_KEY を
  そのまま渡すだけで、値を読まない・印字しない・記録しない。応答の中の会社名は記録に入れない。
- 既存の cache(edinet/・edinet-fresh-2026-10-21/)には 1 file も書かない。取った ZIP は edinet-prior-2026-11-02/ に置く。
- 止まる: 出力が既に在る / 97 書類の sha256 が記録と違う / engine(core/・adapters/)に未 commit の変更 / 鍵が無い(実走)。
  止まるときは何も書かない。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- 「当期の枠」は context id が CurrentYear で始まり members が空のもの、「前期の枠」は Prior1Year で始まり members が空のもの。
  期の型は context の instant の有無(Instant / Duration)。鍵は (要素名, 期の型, 単位)。同じ鍵に fact が 2 つ以上あれば最初の 1 つを使い、
  重なりの数を記録する。
- 「同じ」は float の等号。「違う」は等しくないこと。差の大きさは |next − prev| / |prev|(prev が 0 なら None で「比べられない」に数える)。
- 前年の有報の探し方: 当期の末日の 1 年前の日 E′ について、E′ + 60 日 〜 E′ + 110 日の各日を 1 回ずつ引き(会社をまたいで同じ日は 1 回)、
  edinetCode が同じ・ordinanceCode 010・docTypeCode 120・xbrlFlag 1 の書類。2 つ以上なら submitDateTime が最も遅い物。
- E01777(ソニーグループ)は 97 社の外。2025-03-31 と 2026-03-31 を当期の末日として 2 書類を同じ探し方で取り、同じ突き合わせをする。
"""
from __future__ import print_function

import argparse
import collections
import datetime
import hashlib
import importlib.util
import io
import json
import os
import re
import statistics
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SEAL_REL = "docs/XBRL_RESTATED_PRIOR_SEAL_2026-11-02.md"
SEAL_COMMIT = "3a099e7"
REGRESS_REL = "fixtures/xbrl/p27/regress97_2026-10-27.json"
OUT_REL = "fixtures/xbrl/prior_pairs_2026-11-02.json"
EXISTING_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
FRESH_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-fresh-2026-10-21")
PRIOR_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-prior-2026-11-02")
API = "https://api.edinet-fsa.go.jp/api/v2/"
KEY_NAME = "EDINET_API_KEY"
ORDINANCE, DOCTYPE = "010", "120"
WINDOW = (60, 110)
SAMPLE_DIR = {u"手元の 67": EXISTING_CACHE, u"新しい標本 30": FRESH_DIR}
EXTRA = {u"E01777": [u"2025-03-31", u"2026-03-31"]}               # 固定の確認(封 §1 の 6・§3 の F-10)
EXTRA_ELEMENTS = (u"jpigp_cor:OperatingProfitLossIFRS", u"jpigp_cor:DepreciationAndAmortizationOpeCFIFRS")
BOUNDS = {u"F-2": (75, 97), u"F-3": (150, 400), u"F-4": (1.0, 15.0), u"F-5": (30.0, 80.0), u"F-11": 50.0}
DEI_RE = {u"edinet_code": re.compile(r"<jpdei_cor:EDINETCodeDEI[^>]*>\s*([A-Z0-9]+)\s*<"),
          u"fy_end": re.compile(r"<jpdei_cor:CurrentFiscalYearEndDateDEI[^>]*>\s*(\d{4}-\d{2}-\d{2})\s*<"),
          u"period_end": re.compile(r"<jpdei_cor:CurrentPeriodEndDateDEI[^>]*>\s*(\d{4}-\d{2}-\d{2})\s*<"),
          u"standard": re.compile(r"<jpdei_cor:AccountingStandardsDEI[^>]*>\s*([^<\s][^<]*?)\s*<"),
          u"consolidated": re.compile(r"<jpdei_cor:WhetherConsolidatedFinancialStatementsArePreparedDEI[^>]*>\s*(true|false)\s*<")}
KEY_PATTERNS = (r"Subscription-Key=[^&\s\"]+", r"sk-[A-Za-z0-9_\-]{10,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{20,}", r"-----BEGIN")


class Stop(SystemExit):
    pass


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with io.open(p, "rb") as fh:
        return sha_bytes(fh.read())


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- DEI と枠

def read_dei(zbytes):
    z = zipfile.ZipFile(io.BytesIO(zbytes))
    xbrl = [n for n in z.namelist() if n.startswith("XBRL/PublicDoc/") and n.endswith(".xbrl")]
    out = collections.OrderedDict((k, None) for k in DEI_RE)
    out[u"xbrl"] = bool(xbrl)
    if not xbrl:
        return out
    raw = z.read(xbrl[0]).decode("utf-8", "replace")
    for k, rx in DEI_RE.items():
        m = rx.search(raw)
        out[k] = m.group(1) if m else None
    return out


def frame_of(cid, ctx):
    u"""当期 / 前期 / None(member あり・他の枠)。"""
    if ctx.get("members"):
        return None
    if cid.startswith("CurrentYear"):
        return u"当期"
    if cid.startswith("Prior1Year"):
        return u"前期"
    return None


def frame_values(inst, frame):
    u"""(要素名, 期の型, 単位) → 値。重なり(同じ鍵に 2 つ以上)の数も返す。"""
    vals, dup = collections.OrderedDict(), 0
    for f in inst["facts"]:
        ctx = inst["contexts"].get(f["context"])
        if ctx is None or frame_of(f["context"], ctx) != frame:
            continue
        kind = u"Instant" if ctx.get("instant") else u"Duration"
        key = (f["name"], kind, f.get("unit"))
        if key in vals:
            dup += 1
            continue
        vals[key] = f["value"]
    return vals, dup


def pair_elements(prev_inst, next_inst):
    u"""prev の当期欄 × next の前期欄。"""
    a, dup_a = frame_values(prev_inst, u"当期")
    b, dup_b = frame_values(next_inst, u"前期")
    keys = sorted(set(a) | set(b))
    rows, same, differ, only_a, only_b = [], 0, 0, 0, 0
    for k in keys:
        if k in a and k in b:
            if a[k] == b[k]:
                same += 1
            else:
                differ += 1
                rel = (abs(b[k] - a[k]) / abs(a[k])) if a[k] != 0 else None
                rows.append(collections.OrderedDict([(u"要素", k[0]), (u"期の型", k[1]), (u"単位", k[2]), (u"prev の当期", a[k]), (u"next の前期", b[k]),
                                                     (u"差の割合", None if rel is None else round(rel, 6))]))
        elif k in a:
            only_a += 1
        else:
            only_b += 1
    return collections.OrderedDict([(u"結べた要素", same + differ), (u"同じ", same), (u"違う", differ), (u"prev にだけ", only_a), (u"next にだけ", only_b),
                                    (u"重なり(prev)", dup_a), (u"重なり(next)", dup_b), (u"違う要素", rows)])


# ---------------------------------------------------------------- backend(実物と作り物)

class RealBackend(object):
    def __init__(self):
        if not os.environ.get(KEY_NAME):
            raise Stop(u"環境変数 %s が無い。鍵のある席で走らせること(値は読まない・印字しない)" % KEY_NAME)
        self.calls = []

    def _get(self, path, params):
        q = dict(params)
        q["Subscription-Key"] = os.environ[KEY_NAME]
        url = API + path + "?" + urllib.parse.urlencode(q)
        self.calls.append(API + path + "?" + urllib.parse.urlencode(params))
        with urllib.request.urlopen(url, timeout=120) as r:
            return r.read()

    def list_day(self, day):
        u"""失敗した日は ok=False で返し、呼び手が数える(「前年なし」に静かに化けさせない。監査 2026-11-02 の指摘)。"""
        try:
            body = self._get("documents.json", {"date": day, "type": 2})
        except urllib.error.HTTPError as e:
            return {u"status": e.code, u"results": [], u"ok": False}
        except urllib.error.URLError:
            return {u"status": -1, u"results": [], u"ok": False}
        try:
            data = json.loads(body.decode("utf-8", "replace"))
        except ValueError:
            return {u"status": -2, u"results": [], u"ok": False}
        meta = data.get("metadata") if isinstance(data, dict) else None
        if not isinstance(meta, dict):
            return {u"status": -3, u"results": [], u"ok": False}
        st = int(meta.get("status") or 0)
        return {u"status": st, u"results": (data.get("results") or []) if st == 200 else [], u"ok": st == 200}

    def fetch(self, doc_id):
        return self._get("documents/%s" % doc_id, {"type": 1})


class StubBackend(object):
    u"""作り物: dir/listing.json = {day: [entry, ...]}、dir/<docID>.zip。"""
    def __init__(self, d):
        self.dir = d
        self.listing = jload(os.path.join(d, "listing.json"))
        self.calls = []

    def list_day(self, day):
        self.calls.append("documents.json?date=%s&type=2" % day)
        v = self.listing.get(day, [])
        if v == "FAIL":                                            # 作り物の失敗の日
            return {u"status": 500, u"results": [], u"ok": False}
        return {u"status": 200, u"results": v, u"ok": True}

    def fetch(self, doc_id):
        self.calls.append("documents/%s?type=1" % doc_id)
        with io.open(os.path.join(self.dir, doc_id + ".zip"), "rb") as fh:
            return fh.read()


def days_for(fy_end):
    e = datetime.date.fromisoformat(fy_end)
    try:
        e1 = e.replace(year=e.year - 1)
    except ValueError:                      # 2 月 29 日
        e1 = e.replace(year=e.year - 1, day=28)
    return [(e1 + datetime.timedelta(days=d)).isoformat() for d in range(WINDOW[0], WINDOW[1] + 1)]


def find_prior(code, fy_end, backend, day_cache):
    u"""前年の有報の候補(窓の中の全日を引く。同じ日は 1 回)。返す: (候補, 失敗した日の数)。"""
    cands, failed = [], 0
    for day in days_for(fy_end):
        if day not in day_cache:
            day_cache[day] = backend.list_day(day)
        if not day_cache[day].get(u"ok", True):
            failed += 1
            continue
        for r in day_cache[day][u"results"]:
            if (r.get("edinetCode") == code and r.get("ordinanceCode") == ORDINANCE and r.get("docTypeCode") == DOCTYPE
                    and str(r.get("xbrlFlag")) == "1" and r.get("docID")):
                cands.append(collections.OrderedDict([(u"docID", r["docID"]), (u"periodEnd", r.get("periodEnd")), (u"submitDateTime", r.get("submitDateTime")), (u"day", day)]))
    cands.sort(key=lambda c: (c[u"submitDateTime"] or u"", c[u"docID"]))
    return cands, failed


def get_zip(doc_id, backend, prior_dir, fetched):
    u"""ZIP を取る。ZIP でない応答は書かずに None(監査 2026-11-02 の指摘: 次回「既に在った」として再利用されないように)。"""
    p = os.path.join(prior_dir, doc_id + ".zip")
    if os.path.exists(p):
        with io.open(p, "rb") as fh:
            b = fh.read()
        fetched.append(collections.OrderedDict([(u"docID", doc_id), (u"取得", u"既に在った"), (u"bytes", len(b)), (u"sha256", sha_bytes(b))]))
        return b
    b = backend.fetch(doc_id)
    if not zipfile.is_zipfile(io.BytesIO(b)):
        fetched.append(collections.OrderedDict([(u"docID", doc_id), (u"取得", u"ZIP でない応答(書かない)"), (u"bytes", len(b)), (u"sha256", sha_bytes(b))]))
        return None
    os.makedirs(prior_dir, exist_ok=True)
    with io.open(p, "wb") as fh:
        fh.write(b)
    fetched.append(collections.OrderedDict([(u"docID", doc_id), (u"取得", u"取った"), (u"bytes", len(b)), (u"sha256", sha_bytes(b))]))
    return b


# ---------------------------------------------------------------- 本体

def engine_bundle():
    fb = load_module(os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py"), "frozen_bundle_sha_for_prior_pairs")
    cwd = os.getcwd()
    try:
        os.chdir(REPO)
        sha, rows = fb.bundle()
        dirty = fb._dirty_count()
    finally:
        os.chdir(cwd)
    return sha, len(rows), dirty


def git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode().strip() if r.returncode == 0 else None


def docs97(regress, sample_dir):
    out = []
    for d in regress[u"書類"]:
        out.append(collections.OrderedDict([(u"docID", d["docID"]), (u"標本", d[u"標本"]), (u"sha256(記録)", d[u"zip の sha256"]),
                                            (u"path", os.path.join(sample_dir[d[u"標本"]], d["docID"] + ".zip"))]))
    return out


def judge(T):
    J = collections.OrderedDict()
    J[u"F-1"] = T[u"97 書類の sha256 が記録と一致"] == 97 and T[u"DEI が読めた"] == 97
    J[u"F-2"] = BOUNDS[u"F-2"][0] <= T[u"前年の有報が見つかった会社"] <= BOUNDS[u"F-2"][1]
    J[u"F-3"] = T[u"結べた要素の中央値"] is not None and BOUNDS[u"F-3"][0] <= T[u"結べた要素の中央値"] <= BOUNDS[u"F-3"][1]
    J[u"F-4"] = T[u"違う割合(%)"] is not None and BOUNDS[u"F-4"][0] <= T[u"違う割合(%)"] <= BOUNDS[u"F-4"][1]
    J[u"F-5"] = T[u"違う要素が 1 つ以上ある組の割合(%)"] is not None and BOUNDS[u"F-5"][0] <= T[u"違う要素が 1 つ以上ある組の割合(%)"] <= BOUNDS[u"F-5"][1]
    J[u"F-11"] = T[u"違う要素のうち差が 5% 未満の割合(%)"] is not None and T[u"違う要素のうち差が 5% 未満の割合(%)"] >= BOUNDS[u"F-11"]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"F-10(段 1 の部分)"] = T[u"E01777 の 2 要素が違うに入る"]
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


def run(backend, regress_path, out_path, sample_dir=None, prior_dir=PRIOR_DIR, extra=None, require_97=True):
    from adapters.xbrl import instance as I
    sample_dir = sample_dir or SAMPLE_DIR
    extra = EXTRA if extra is None else extra
    regress = jload(regress_path)
    docs = docs97(regress, sample_dir)
    bundle_sha, n_files, dirty = engine_bundle()
    if dirty:
        raise Stop(u"engine(core/・adapters/)に未 commit の変更が %d file ある。止める" % dirty)
    # (1) sha256 と DEI
    ok_sha, ok_dei = 0, 0
    for d in docs:
        if not os.path.exists(d[u"path"]):
            d[u"sha256 が一致"], d[u"DEI"] = False, None
            continue
        with io.open(d[u"path"], "rb") as fh:
            b = fh.read()
        d[u"sha256 が一致"] = sha_bytes(b) == d[u"sha256(記録)"]
        ok_sha += int(d[u"sha256 が一致"])
        dei = read_dei(b)
        d[u"DEI"] = dei
        ok_dei += int(bool(dei[u"edinet_code"] and dei[u"fy_end"]))
    if require_97 and ok_sha != len(docs):
        raise Stop(u"97 書類の sha256 が記録と一致しない(%d / %d)。止める" % (ok_sha, len(docs)))
    # (2)(3) 前年の有報
    day_cache, fetched, pairs = collections.OrderedDict(), [], []
    by_code = collections.OrderedDict()
    for d in docs:
        if d.get(u"DEI") and d[u"DEI"][u"edinet_code"] and d[u"DEI"][u"fy_end"]:
            by_code.setdefault(d[u"DEI"][u"edinet_code"], []).append(d)
    for code, ds in by_code.items():
        nxt = ds[0]                                      # 同じ会社の書類が 2 つあれば最初の 1 つ(数を記録)
        cands, failed = find_prior(code, nxt[u"DEI"][u"fy_end"], backend, day_cache)
        row = collections.OrderedDict([(u"EDINET コード", code), (u"next の docID", nxt["docID"]), (u"next の当期の末日", nxt[u"DEI"][u"fy_end"]),
                                       (u"同じ会社の手元の書類", len(ds)), (u"候補の数", len(cands)), (u"失敗した日", failed), (u"prev の docID", None)])
        if not cands:
            row[u"状態"] = u"前年なし(失敗の日あり)" if failed else u"前年なし"
            pairs.append(row)
            continue
        prev_id = cands[-1][u"docID"]
        if prev_id == nxt["docID"]:
            row[u"状態"] = u"候補が next 自身"
            pairs.append(row)
            continue
        row[u"prev の docID"] = prev_id
        row[u"prev の periodEnd"] = cands[-1][u"periodEnd"]
        pb = get_zip(prev_id, backend, prior_dir, fetched)
        if pb is None:
            row[u"状態"] = u"ZIP でない応答"
            pairs.append(row)
            continue
        with io.open(nxt[u"path"], "rb") as fh:
            nb = fh.read()
        prev_inst, next_inst = I.load_instance(pb), I.load_instance(nb)
        row[u"prev の DEI"] = read_dei(pb)
        row[u"突き合わせ"] = pair_elements(prev_inst, next_inst)
        row[u"状態"] = u"組"
        pairs.append(row)
    # (6) 固定の確認
    extra_rows = []
    for code, ends in extra.items():
        got = []
        for fy in ends:
            cands, failed = find_prior(code, (datetime.date.fromisoformat(fy).replace(year=datetime.date.fromisoformat(fy).year + 1)).isoformat(), backend, day_cache)
            got.append(collections.OrderedDict([(u"当期の末日", fy), (u"候補の数", len(cands)), (u"失敗した日", failed), (u"docID", cands[-1][u"docID"] if cands else None)]))
        row = collections.OrderedDict([(u"EDINET コード", code), (u"書類", got)])
        if all(g[u"docID"] for g in got) and len(got) == 2:
            pb = get_zip(got[0][u"docID"], backend, prior_dir, fetched)
            nb = get_zip(got[1][u"docID"], backend, prior_dir, fetched)
            if pb is not None and nb is not None:
                row[u"突き合わせ"] = pair_elements(I.load_instance(pb), I.load_instance(nb))
                names = set(r[u"要素"] for r in row[u"突き合わせ"][u"違う要素"])
                row[u"確認の要素"] = collections.OrderedDict((e, (u"違う" if e in names else u"違うに無い")) for e in EXTRA_ELEMENTS)
            else:
                row[u"状態"] = u"ZIP でない応答"
        extra_rows.append(row)
    # 集計
    T = collections.OrderedDict()
    T[u"書類"] = len(docs)
    T[u"97 書類の sha256 が記録と一致"] = ok_sha
    T[u"DEI が読めた"] = ok_dei
    T[u"会社(EDINET コードの数)"] = len(by_code)
    T[u"前年の有報が見つかった会社"] = sum(1 for p in pairs if p[u"状態"] == u"組")
    T[u"前年なし"] = sum(1 for p in pairs if p[u"状態"] == u"前年なし")
    T[u"前年なし(失敗の日あり)"] = sum(1 for p in pairs if p[u"状態"] == u"前年なし(失敗の日あり)")
    T[u"状態の内訳"] = collections.OrderedDict(collections.Counter(p[u"状態"] for p in pairs))
    got = [p for p in pairs if p[u"状態"] == u"組"]
    T[u"結べた要素の中央値"] = statistics.median([p[u"突き合わせ"][u"結べた要素"] for p in got]) if got else None
    T[u"結べた要素の合計"] = sum(p[u"突き合わせ"][u"結べた要素"] for p in got)
    T[u"同じの合計"] = sum(p[u"突き合わせ"][u"同じ"] for p in got)
    T[u"違うの合計"] = sum(p[u"突き合わせ"][u"違う"] for p in got)
    T[u"違う割合(%)"] = round(100.0 * T[u"違うの合計"] / T[u"結べた要素の合計"], 2) if T[u"結べた要素の合計"] else None
    T[u"違う要素が 1 つ以上ある組"] = sum(1 for p in got if p[u"突き合わせ"][u"違う"] > 0)
    T[u"違う要素が 1 つ以上ある組の割合(%)"] = round(100.0 * T[u"違う要素が 1 つ以上ある組"] / len(got), 1) if got else None
    rels = [r[u"差の割合"] for p in got for r in p[u"突き合わせ"][u"違う要素"] if r[u"差の割合"] is not None]
    T[u"違う要素のうち差が比べられる"] = len(rels)
    T[u"違う要素のうち差が 5% 未満"] = sum(1 for x in rels if x < 0.05)
    T[u"違う要素のうち差が 5% 未満の割合(%)"] = round(100.0 * T[u"違う要素のうち差が 5% 未満"] / len(rels), 1) if rels else None
    T[u"差の分布(件)"] = collections.OrderedDict([(u"1% 未満", sum(1 for x in rels if x < 0.01)), (u"1〜5% 未満", sum(1 for x in rels if 0.01 <= x < 0.05)),
                                              (u"5〜20% 未満", sum(1 for x in rels if 0.05 <= x < 0.2)), (u"20% 以上", sum(1 for x in rels if x >= 0.2))])
    T[u"違う要素の名の上位"] = collections.OrderedDict(collections.Counter(r[u"要素"] for p in got for r in p[u"突き合わせ"][u"違う要素"]).most_common(30))
    T[u"E01777 の 2 要素が違うに入る"] = (u"%d / 2" % sum(1 for r in extra_rows for v in r.get(u"確認の要素", {}).values() if v == u"違う")) if extra_rows and extra_rows[0].get(u"確認の要素") else u"判定しない(書類が揃わない)"
    T[u"呼び出し"] = collections.OrderedDict([(u"日付一覧の回数", sum(1 for c in backend.calls if "documents.json" in c)), (u"ZIP の取得の回数", sum(1 for c in backend.calls if "documents/" in c)),
                                           (u"取った bytes の合計", sum(f[u"bytes"] for f in fetched if f[u"取得"] == u"取った")),
                                           (u"失敗した日の数", sum(1 for v in day_cache.values() if not v.get(u"ok", True))),
                                           (u"日付一覧の status の内訳", collections.OrderedDict(sorted(collections.Counter(str(v.get(u"status")) for v in day_cache.values()).items()))),
                                           (u"ZIP でない応答", sum(1 for f in fetched if f[u"取得"].startswith(u"ZIP でない")))])
    rec = collections.OrderedDict()
    rec[u"注意"] = u"手元の有報 97 書類の前年の有報を取り、prev の当期欄と next の前期欄を要素ごとに突き合わせた記録(段 1)。会社名は書かない。鍵の値は記録しない。"
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT}
    rec[u"HEAD の commit"] = git_head()
    rec[u"この script の sha256"] = sha_file(os.path.abspath(__file__))
    rec[u"読んだ材料の sha256"] = {os.path.relpath(regress_path, ROOT): sha_file(regress_path)}
    rec[u"engine の bundle の sha256(core/・adapters/)"] = bundle_sha
    rec[u"engine の file の数"] = n_files
    rec[u"定数"] = collections.OrderedDict([(u"窓(当期の末日の 1 年前からの日数)", list(WINDOW)), (u"ordinanceCode", ORDINANCE), (u"docTypeCode", DOCTYPE), (u"xbrlFlag", u"1(封に無い絞り。XBRL の無い書類は突き合わせられない)"),
                                         (u"鍵", u"(要素名, 期の型, 単位)。member なし。同じは float の等号"), (u"予測の幅", BOUNDS), (u"固定の確認", extra), (u"確認の要素", list(EXTRA_ELEMENTS))])
    rec[u"配線の門"] = collections.OrderedDict([(u"(a) 97 書類の sha256 が記録と一致", ok_sha == len(docs)), (u"(b) DEI が読めた", ok_dei), (u"(c) engine の未 commit の file", dirty),
                                            (u"(d) 既存の cache に書いていない", True), (u"(e) 日付一覧に失敗した日", T[u"呼び出し"][u"失敗した日の数"]),
                                            (u"通った", ok_sha == len(docs) and dirty == 0 and T[u"呼び出し"][u"失敗した日の数"] == 0)])
    rec[u"書類(手元の 97)"] = [collections.OrderedDict([(k, v) for k, v in d.items() if k != u"path"]) for d in docs]
    rec[u"組"] = pairs
    rec[u"固定の確認"] = extra_rows
    rec[u"取得"] = fetched
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T)
    rec[u"limits"] = [u"97 社は 2026 年提出の有報に偏る", u"「違う」は修正再表示・表示の組替え・会計方針の変更・誤りを区別しない", u"前年の有報が無い会社は測れない",
                     u"同じ鍵に fact が 2 つ以上あるときは最初の 1 つ(重なりの数は記録)"]
    text = json.dumps(rec, ensure_ascii=False)
    rec[u"key_leaks"] = sorted(set(p for p in KEY_PATTERNS if re.search(p, text)))
    if os.environ.get(KEY_NAME) and os.environ[KEY_NAME] in text:
        raise Stop(u"記録に鍵の値が入った。書かない")
    with io.open(out_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--stub", default=None, help=u"作り物の backend の dir(listing.json と <docID>.zip)。門が使う")
    ap.add_argument("--regress", default=os.path.join(ROOT, REGRESS_REL))
    ap.add_argument("--sample-dir", default=None, help=u"作り物のとき: 97 書類の ZIP の dir(67 と 30 を同じ dir で)")
    ap.add_argument("--prior-dir", default=PRIOR_DIR)
    ap.add_argument("--no-extra", action="store_true", help=u"固定の確認(E01777)を省く(作り物の試験用)")
    ap.add_argument("--allow-missing", action="store_true", help=u"作り物のとき: 97 書類が揃わなくても止めない")
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % a.out)
    backend = StubBackend(a.stub) if a.stub else RealBackend()
    sample_dir = {u"手元の 67": a.sample_dir, u"新しい標本 30": a.sample_dir} if a.sample_dir else None
    rec = run(backend, a.regress, a.out, sample_dir=sample_dir, prior_dir=a.prior_dir, extra=({} if a.no_extra else None), require_97=not a.allow_missing)
    print(u"written: %s" % a.out)
    print(json.dumps(rec[u"集計"], ensure_ascii=False)[:1500])
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
