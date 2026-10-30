# -*- coding: utf-8 -*-
"""封 docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md §4-2・§5・§6・§10-4(前半) ― **調整用の 10 社の文を engine に通す測定の script。**
費用 0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(core/・adapters/)は 1 字も変えない。

3 つの subcommand(記録は repo の外の全部の欄と、repo に置く欄だけの記録に分ける)::

    python3 measure/xbrl_p27_tune_2026-10-27.py judge     [--docs A,B] [--out <file>]       # §5-1〜§5-3 判定・読む行・dossier
    python3 measure/xbrl_p27_tune_2026-10-27.py reconcile --seat-a <file> --seat-b <file>   # §5-4・§5-5 読みの合わせ
    python3 measure/xbrl_p27_tune_2026-10-27.py inject    [--docs A,B] [--procs N]          # §6 注入(T1_VALUE・T8_REL)

共通: ``--dry-run`` は engine と ZIP の中身を作り物(``StubBackend``)に替えて同じ経路を通す(``--out``・``--outside-dir`` を明示する)。
ZIP の置き場・DB の応答の置き場・文の置き場は引数で替えられる(試験は使い捨ての folder を渡す)。

**評価用の文は開かない(封 §4-2)。** 評価用の一覧は W の記録(``fixtures/xbrl/p27/reports_2026-10-27.json``)の ``区分`` から読む。
評価用の docID(と、調整用でない docID)を渡されたら、文・ZIP・DB の応答のどの file も開く前に止める。

repo に置く記録に ``span``・``subject``・``value``・``recomputed`` は入れない(文の字と DB の値の写しになるため)。全部の欄は
repo の外 ``~/.cache/audit-core/edinetdb-p27/tune/`` に置き、その sha256 を記録に持たせる。
``~/.cache/audit-core/edinet/`` と ``~/.cache/audit-core/edinet-fresh-2026-10-21/`` には 1 file も足さない(前後の件数と名前の一覧の sha256 を記録し、
変わっていれば記録を書かずに止める)。ZIP は読むだけ。``prepare_xbrl`` の作業 folder は TMPDIR の下。

読み手の札の file(``reconcile`` の入力)の形(JSON)::

    {"席": "席1", "札": [{"行": "<docID>:<claim id>", "側": "文|道具|分からない", "細目": "文1〜文4|道1〜道5|null",
                          "道5の形": "10〜40 字(細目が道5のときだけ)", "理由": "1〜2 文"}, ...]}
"""
import argparse
import collections
import contextlib
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
import random
import re
import statistics
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)
for _p in (HERE, DEFAULT_ROOT, os.path.join(DEFAULT_ROOT, "core", "py")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import inject as IJ                                  # noqa: E402
from lib import numbers as N                         # noqa: E402
from lib import scales as SC                         # noqa: E402
from lib import sites as S                           # noqa: E402


def _load(name, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DB = _load("xbrl_p27_dbfetch_2026-10-27.py", "p27_dbfetch_for_tune")        # key_leaks・snapshot・sha256_hex の在りか
PR = _load("xbrl_p27_prompts_2026-10-27.py", "p27_prompts_for_tune")        # READER_PROMPT(封 §5-6 の字)

SEAL = "audit-core/docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md"
W_COMMIT = "c48f464"                      # 封 §4-1 の commit W(評価用の凍結)
REPORTS_REL = os.path.join("fixtures", "xbrl", "p27", "reports_2026-10-27.json")
DBFETCH_REL = os.path.join("fixtures", "xbrl", "p27", "dbfetch_2026-10-27.json")
FETCHED_REL = os.path.join("fixtures", "xbrl", "fresh", "fetched_2026-10-21.json")
JUDGE_REL = os.path.join("fixtures", "xbrl", "p27", "tune_2026-10-27.json")
READINGS_REL = os.path.join("fixtures", "xbrl", "p27", "tune_readings_2026-10-27.json")
INJECT_REL = os.path.join("fixtures", "xbrl", "p27", "tune_inject_2026-10-27.json")
SEED_FILE = os.path.join(HERE, "SEED.json")

PROFILES = ("P22", "P26")
STYLES = ("A", "B", "C")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
RECORD_CLAIM_FIELDS = ("kind", "form", "unit", "state", "reason", "pointers")     # 封 §5-1: id に加えて repo に置く欄
FORBIDDEN_RECORD_KEYS = ("span", "subject", "value", "recomputed")              # 封 §5-1: repo に入れない欄
NO_SAME_VALUE = "no_same_value"

# 封 §5-4 の札の語
SIDES = ("文", "道具", "分からない")
DETAILS = {"文": ("文1", "文2", "文3", "文4"), "道具": ("道1", "道2", "道3", "道4", "道5")}
UNSURE = "分からない"
SHAPE_MIN, SHAPE_MAX = 10, 40                                                  # 道5 の形の字数

# 封 §6-3
INJECT_TYPES = ("T1_VALUE", "T8_REL")
INJECT_CAP = 40
T8_R_VALUES = (-0.10, -0.03, 0.03, 0.10)
T8_TRIES = 4
MONEY_FAMILY = tuple(N.UNIT_FAMILIES["money"])                                 # 円・千円・百万円・億円・兆円
TOL = 1e-9

LABEL_PASS = "通した"
LABEL_NAMED_ORIGINAL = "名指して原本の値を返した"
LABEL_NAMED_OTHER = "名指したが別の値"
LABEL_PNF = "止めたが名指さない(POINTER_NOT_FOUND)"
LABEL_UNV = "止めたが名指さない(UNVERIFIABLE)"
LABEL_UNMAPPED = "対応が付かない"

SAFE_REASON = re.compile(r"[A-Za-z_]+(?:\([A-Za-z_ ;,:\-]*\))?")               # 符号の形。数や文の字が混ざるものは通さない
SAFE_POINTER = re.compile(r"[A-Za-z_]+:[A-Za-z0-9_:@/*+\-().=<>]*")
HEX32 = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{32}(?![0-9A-Fa-f])")
COMMIT_KEYS = ("HEAD の commit", "W の commit", "sealed_in_commit", "git_commit")        # 値が 40 桁の小文字 16 進(git の commit)なら鍵の検査から外す
GIT_COMMIT = re.compile(r"[0-9a-f]{40}")


class Stop(SystemExit):
    """止める(記録は書かない)。文言に文・DB の値・鍵を入れない。"""


# ======================================================================================================
# 小さい道具
def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def frac(a, b):
    return {"件": a, "分母": b, "率": pct(a, b)}


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def read_bytes(path):
    with io.open(path, "rb") as fh:
        return fh.read()


def read_json(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_text(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def inside(path, folder):
    a, b = os.path.realpath(path), os.path.realpath(folder)
    return a == b or a.startswith(b + os.sep)


def same_number(a, b):
    return abs(a - b) <= max(TOL, 1e-9 * max(abs(a), abs(b)))


def scaled(value, unit):
    """書かれた単位の数を円に直す(円族だけ。それ以外はそのまま)。"""
    return SC.scaled_value(value, unit)


def claim_scaled(c):
    return scaled(c["value"], c.get("unit"))


# ======================================================================================================
# 材料の在りか(評価用の止めはここ)
class Ctx(object):
    """材料の置き場と、W の記録から読んだ区分。**評価用の docID(と、調整用でない docID)は、どの file も開く前に止める。**"""

    def __init__(self, root, zip_dir, cache_root, existing_dir, outside_dir, work_root, docs=None):
        self.root = root
        w = read_json(os.path.join(root, REPORTS_REL))
        companies = w["会社"]
        for c in companies:
            if c.get("区分") not in ("調整用", "評価用"):
                raise Stop("**W の記録に区分が調整用でも評価用でもない会社がある。止める**")
        self.w = w
        self.tuning = [c["docID"] for c in companies if c["区分"] == "調整用"]
        self.eval_ids = frozenset(c["docID"] for c in companies if c["区分"] == "評価用")
        self.styles = dict((c["docID"], c["型"]) for c in companies)
        self.report_sha = dict((c["docID"], c["文の sha256"]) for c in companies)
        # **ここで docs を確かめる。以降の file はまだ 1 つも開いていない**
        self.docs = list(self.tuning) if docs is None else list(docs)
        for d in self.docs:
            self.guard(d)
        if len(set(self.docs)) != len(self.docs) or not self.docs:
            raise Stop("**docs が空か重複している。止める**")
        self.zip_dir, self.cache_root, self.existing_dir = zip_dir, cache_root, existing_dir
        self.outside_dir, self.work_root = outside_dir, work_root
        for name, folder in (("外の置き場", outside_dir), ("作業 folder", work_root)):
            if folder is None:
                continue
            for prot in (existing_dir, zip_dir):
                if inside(folder, prot):
                    raise Stop("**%s が既存の cache か ZIP の folder の中。止める**" % name)
        if outside_dir is not None and inside(outside_dir, root):
            raise Stop("**外の置き場が repo の中。止める**")
        fetched = read_json(os.path.join(root, FETCHED_REL))
        self.zip_rows = dict((r["docID"], r) for r in fetched["取得した書類"])
        dbrec = read_json(os.path.join(root, DBFETCH_REL))
        self.db_sha = dict(((r["docID"], r["種類"]), r["sha256"]) for r in dbrec["呼び出し"] if r.get("sha256"))

    def guard(self, doc):
        if doc in self.eval_ids:
            raise Stop("**評価用の docID が渡された。文・ZIP・DB の応答のどの file も開かずに止める(封 §4-2)**")
        if doc not in self.tuning:
            raise Stop("**調整用でない docID が渡された。止める**")

    def zip_path(self, doc):
        self.guard(doc)
        return os.path.join(self.zip_dir, doc + ".zip")

    def read_report(self, doc):
        self.guard(doc)
        b = read_bytes(os.path.join(self.cache_root, "reports", doc + ".txt"))
        if sha256_hex(b) != self.report_sha[doc]:
            raise Stop("**文の sha256 が W の記録と違う: %s。止める**" % doc)
        return b.decode("utf-8"), b

    def read_zip(self, doc):
        self.guard(doc)
        b = read_bytes(self.zip_path(doc))
        if sha256_hex(b) != self.zip_rows[doc]["sha256"]:
            raise Stop("**ZIP の sha256 が取得の記録と違う: %s。止める**" % doc)
        return b

    def read_db(self, doc):
        self.guard(doc)
        out = {}
        for kind in ("financials", "companies", "ratios"):
            b = read_bytes(os.path.join(self.cache_root, doc, kind + ".json"))
            if self.db_sha.get((doc, kind)) != sha256_hex(b):
                raise Stop("**DB の応答の sha256 が取得の記録と違う: %s %s。止める**" % (doc, kind))
            out[kind] = b
        return out


# ======================================================================================================
# engine への入口(試験・dry-run は StubBackend)
class RealBackend(object):
    name = "real"

    def __init__(self):
        from adapters.xbrl import instance as I
        from adapters.xbrl import verify_document as VD
        import prepare_material as PM
        self._I, self._VD, self._PM = I, VD, PM

    def verify(self, zb, profile, text):
        return self._VD.verify_document(zb, profile, text)

    def facts(self, zb):
        return self._I.load_instance(zb)["facts"]

    def refs(self, zip_path, doc, work):
        """``prepare_xbrl`` の reference_numbers(書類の fact から作る)。作業 folder は work(TMPDIR の下)。"""
        a = argparse.Namespace(zip=zip_path, doc=doc, out=work)
        with contextlib.redirect_stdout(io.StringIO()):
            self._PM.prepare_xbrl(a)
        d = read_json(os.path.join(work, "%s.reference_numbers.json" % doc))
        return d["refs"]

    def fingerprint(self):
        return self._VD.engine_fingerprint()


class NullBackend(object):
    """engine を使わない subcommand(reconcile)の記録の欄を埋めるだけ。"""
    name = "なし"

    def fingerprint(self):
        return {}


class StubBackend(object):
    """作り物。ZIP の中身を ``{"facts": [{"name", "context", "unit", "value"}]}`` の JSON とみなす。
    P22: 値が合う fact が無ければ最も近い fact を名指して VALUE_MISMATCH。P26: 同じ行を POINTER_NOT_FOUND(no_same_value)で止める。"""
    name = "stub"

    @staticmethod
    def _facts(zb):
        return json.loads(zb.decode("utf-8"))["facts"]

    def facts(self, zb):
        return self._facts(zb)

    def refs(self, zip_path, doc, work):
        return [{"key": "%s@%s" % (f["name"], f["context"]), "source_key": f["name"], "label": f["name"], "unit": "円" if str(f.get("unit", "JPY")).upper().startswith("JPY") else f.get("unit"),
                 "value": float(f["value"]), "role": "value", "context": f["context"]} for f in self._facts(read_bytes(zip_path))]

    def fingerprint(self):
        return {"stub": True}

    def verify(self, zb, profile, text):
        facts = self._facts(zb)
        claims = []
        for t in N.scan(text):
            if t.unit is None or not N.is_quantity(text, t):
                continue
            yen = scaled(t.value, t.unit)
            unit = "円" if t.unit in MONEY_FAMILY else t.unit
            hit = [f for f in facts if same_number(float(f["value"]), yen)]
            named = hit[0] if hit else (min(facts, key=lambda f: abs(float(f["value"]) - yen)) if facts else None)
            pointers = ["xbrl:%s@%s" % (named["name"], named["context"])] if named else []
            if hit:
                state, reason, rec = "GROUNDED", None, float(named["value"])
            elif profile == "P22" and named:
                state, reason, rec = "VALUE_MISMATCH", None, float(named["value"])
            else:
                state, reason, rec, pointers = "POINTER_NOT_FOUND", NO_SAME_VALUE, None, []
            claims.append({"id": "N%03d" % (len(claims) + 1), "kind": "num", "form": "direct_value", "subject": "科目", "value": yen,
                           "unit": unit, "word": None, "span": text[max(0, t.start - 8):t.unit_end + 4], "state": state,
                           "pointers": pointers, "reason": reason, "recomputed": rec})
        return {"profile": profile, "claims": claims}


# ======================================================================================================
# git・cache の前後・鍵
def git_facts(git_dir):
    def g(*a):
        r = subprocess.run(["git", "-C", git_dir] + list(a), capture_output=True, text=True)
        return r.returncode, r.stdout.strip()
    rc, head = g("rev-parse", "HEAD")
    rc2, w = g("rev-parse", "--verify", W_COMMIT + "^{commit}")
    if rc or rc2 or not head or not w:
        raise Stop("**git の HEAD か W の commit が読めない。止める**")
    if g("merge-base", "--is-ancestor", w, head)[0] != 0:
        raise Stop("**W の commit が HEAD の祖先でない(封 §4-3)。止める**")
    return {"HEAD": head, "W": w, "W は HEAD の祖先": True}


def cache_snapshot(ctx):
    return {"既存の cache": DB.snapshot(ctx.existing_dir), "ZIP の folder": DB.snapshot(ctx.zip_dir)}


def pointer_leaks(strings, key_value=None):
    """pointers の字(要素の名前は長い英字なので『32 字以上の英数字』では見ない。32 桁の 16 進・KEY=値・環境の鍵の値だけ当てる)。"""
    leaks = []
    for s in strings:
        if HEX32.search(s):
            leaks.append("pointers に 32 桁の 16 進")
        if re.search(DB.KEY_NAME + r"\s*=\s*['\"]?\w{8,}", s):
            leaks.append("pointers に %s=値" % DB.KEY_NAME)
        if key_value and key_value in s:
            leaks.append("pointers に環境の鍵の値そのもの")
    return leaks


def _mask_pointers(obj, bag):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k == "pointers" and isinstance(v, list):
                bag.extend(x for x in v if isinstance(x, str))
                out[k] = []
            elif k in COMMIT_KEYS and isinstance(v, str) and GIT_COMMIT.fullmatch(v):
                out[k] = ""
            else:
                out[k] = _mask_pointers(v, bag)
        return out
    if isinstance(obj, list):
        return [_mask_pointers(x, bag) for x in obj]
    return obj


def record_key_leaks(obj, key_value=None):
    """repo に置く記録に鍵らしい字が在れば、その種類の一覧(値は返さない)。前例 ``key_leaks`` を pointers 以外の全部に当てる。"""
    bag = []
    text = json.dumps(_mask_pointers(obj, bag), ensure_ascii=False)
    leaks = DB.key_leaks(text, key_value) + pointer_leaks(bag, key_value)
    if key_value and key_value in json.dumps(obj, ensure_ascii=False) and "環境の鍵の値そのもの" not in leaks:
        leaks.append("環境の鍵の値そのもの")                         # commit の欄に隠れた分も、環境の鍵の値は全体で当てる
    return leaks


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


def assert_record_clean(obj, key_value=None):
    bad = sorted(set(k for k in walk_keys(obj) if k in FORBIDDEN_RECORD_KEYS))
    if bad:
        raise Stop("**記録に repo へ入れない欄がある: %s。止める**" % ",".join(bad))
    leaks = record_key_leaks(obj, key_value)
    if leaks:
        raise Stop("**鍵らしい字が記録に在る(%s)。書かずに止める**" % " / ".join(sorted(set(leaks))))


def write_record(path, obj, key_value=None):
    """書く前と書いた後に鍵の検査を当てる。出力が既に在れば止める(測り直さない)。"""
    assert_record_clean(obj, key_value)
    if os.path.exists(path):
        raise Stop("**出力が既に在る: %s。止める**" % os.path.basename(path))
    write_text(path, dumps(obj))
    back = read_json(path)
    leaks = record_key_leaks(back, key_value)
    if leaks:
        os.remove(path)
        raise Stop("**書いた後の記録に鍵らしい字が在った。消して止める**")


def header(ctx, step, git, dry_run, backend, before, after):
    script = read_bytes(os.path.abspath(__file__))
    if before != after:
        raise Stop("**既存の cache か ZIP の folder の件数か名前が変わった。記録を書かずに止める**")
    return {"seal": SEAL, "step": step, "dry_run": bool(dry_run), "backend": backend.name,
            "HEAD の commit": git["HEAD"], "W の commit": git["W"], "W は HEAD の祖先": git["W は HEAD の祖先"],
            "この script の sha256": sha256_hex(script),
            "対象の docID": list(ctx.docs), "対象は調整用の全部": list(ctx.docs) == list(ctx.tuning),
            "使った文の sha256": dict((d, ctx.report_sha[d]) for d in ctx.docs),
            "engine の指紋": backend.fingerprint(),
            "cache の前後": {"前": before, "後": after, "変化なし": before == after}}


# ======================================================================================================
# §5-1 判定
def safe_reason(reason):
    if reason is None:
        return None
    if not isinstance(reason, str) or not SAFE_REASON.fullmatch(reason):
        raise Stop("**reason の字が符号の形でない(文か値が混ざりうる)。止める**")
    return reason


def safe_pointers(pointers):
    out = []
    for p in pointers or []:
        if not isinstance(p, str) or not SAFE_POINTER.fullmatch(p):
            raise Stop("**pointers の字が符号の形でない。止める**")
        out.append(p)
    return out


def claim_record(c):
    """repo に置く欄だけ(kind・form・unit・state・reason・pointers)。span・subject・value・recomputed は持たない。"""
    if c["state"] not in STATES:
        raise Stop("**state が 4 つの語でない。止める**")
    return {"kind": c.get("kind"), "form": c.get("form"), "unit": c.get("unit"), "state": c["state"],
            "reason": safe_reason(c.get("reason")), "pointers": safe_pointers(c.get("pointers"))}


def read_row_conditions(p22, p26):
    """封 §5-2 の読む行 = (P26 で VALUE_MISMATCH)∪(P22 で VALUE_MISMATCH)∪(P26 で POINTER_NOT_FOUND かつ reason が no_same_value)。
    該当した条件の名前の一覧(空なら読まない)。profile の側に claim が無ければその条件は偽。"""
    conds = []
    if p26 is not None and p26["state"] == "VALUE_MISMATCH":
        conds.append("P26_VALUE_MISMATCH")
    if p22 is not None and p22["state"] == "VALUE_MISMATCH":
        conds.append("P22_VALUE_MISMATCH")
    if p26 is not None and p26["state"] == "POINTER_NOT_FOUND" and p26.get("reason") == NO_SAME_VALUE:
        conds.append("P26_POINTER_NOT_FOUND_no_same_value")
    return conds


def pair_claims(outs):
    """P22 と P26 の claim を id で対にする(前例 xbrl_fresh_2026-10-21.py の ``id が合わない``)。
    (id の並び, P22 の辞書, P26 の辞書, 片方にしか無い id, 値・span・単位が違う id)。"""
    per = dict((p, dict((c["id"], c) for c in outs[p]["claims"])) for p in PROFILES)
    ids = [c["id"] for c in outs["P22"]["claims"]]
    ids += [c["id"] for c in outs["P26"]["claims"] if c["id"] not in per["P22"]]
    only = sorted(set(per["P22"]) ^ set(per["P26"]))
    differ = [i for i in ids if i in per["P22"] and i in per["P26"] and
              (per["P22"][i]["value"], per["P22"][i]["span"], per["P22"][i]["unit"]) !=
              (per["P26"][i]["value"], per["P26"][i]["span"], per["P26"][i]["unit"])]
    return ids, per["P22"], per["P26"], only, differ


def _blocks(text):
    cuts, last = [], 0
    for m in re.finditer(r"\n[ \t　]*\n", text):
        cuts.append((last, m.start()))
        last = m.end()
    cuts.append((last, len(text)))
    return [(a, b) for a, b in cuts if b > a]


def paragraph_of(text, span):
    """claim の span(文の窓)がある段落。(段落の字, 注)。見つからなければ全文。
    段落 = 空行で区切った塊。塊が「・」で始まる行を 2 行以上持つ(箇条書き)ときは、span にかかる行だけ。"""
    if not span:
        return text, "span が無いので全文"
    pos = text.find(span)
    if pos < 0:
        pos = N.normalize_digits(text).find(N.normalize_digits(span))
    if pos < 0:
        return text, "span が文の中に見つからないので全文"
    end = pos + len(span)
    out = []
    for a, b in _blocks(text):
        if b <= pos or a >= end:
            continue
        block = text[a:b]
        lines = block.split("\n")
        if sum(1 for ln in lines if ln.lstrip().startswith("・")) >= 2:
            off, picked = a, []
            for ln in lines:
                if off + len(ln) > pos and off < end:
                    picked.append(ln)
                off += len(ln) + 1
            out.append("\n".join(picked))
        else:
            out.append(block)
    return "\n\n".join(out), ""


def fact_lines(facts, pointers):
    """pointers の xbrl の fact と、同じ要素の別の context の fact(読むための材料。判定ではない)。"""
    names, named = [], set()
    for p in pointers:
        if p.startswith("xbrl:") and "@" in p:
            name, ctx = p[len("xbrl:"):].split("@", 1)
            if name not in names:
                names.append(name)
            named.add((name, ctx))
    lines = []
    for name in names:
        lines.append("要素 %s" % name)
        seen = set()
        for f in sorted((f for f in facts if f["name"] == name), key=lambda f: f["context"]):
            mark = "  ◀ 名指し" if (name, f["context"]) in named else ""
            line = "  context=%s unit=%s decimals=%s value=%s%s" % (f["context"], f.get("unit"), f.get("decimals"), f["value"], mark)
            if line not in seen:                  # 同じ fact が書類に 2 度出る(同じ字の行は 1 度だけ)
                seen.add(line)
                lines.append(line)
    others = [p for p in pointers if not p.startswith("xbrl:")]
    if others:
        lines.append("fact でない pointers: " + " / ".join(others))
    return lines or ["(xbrl の pointers なし)"]


def render_dossier(doc, style, claim_id, paragraph, note, p22, p26, facts, db):
    """読み手の席が Read で読む束(1 行ぶん)。文の段落・claim の全部の欄(P22 と P26)・pointers の fact・DB の応答 3 つ。"""
    pointers = []
    for c in (p22, p26):
        for p in (c or {}).get("pointers") or []:
            if p not in pointers:
                pointers.append(p)
    parts = ["# 読む行: %s / %s(文体の型 %s)" % (doc, claim_id, style), "",
             "## 1 文の段落" + ("(" + note + ")" if note else ""), paragraph, ""]
    for name, c in (("P22", p22), ("P26", p26)):
        parts += ["## 2 claim の全部の欄(%s)" % name, dumps(c).rstrip("\n") if c is not None else "(この profile に同じ id の claim が無い)", ""]
    parts += ["## 3 pointers の XBRL の fact"] + fact_lines(facts, pointers) + [""]
    for kind in ("companies", "financials", "ratios"):
        parts += ["## 4 DB の応答(%s)" % kind, db[kind].decode("utf-8"), ""]
    return "\n".join(parts)


def run_judge(root=DEFAULT_ROOT, docs=None, out=None, outside_dir=None, backend=None, dry_run=False, zip_dir=None, cache_root=None,
              existing_dir=None, git_dir=None, key_value=None, say=print):
    """封 §5-1〜§5-3。判定・読む行・dossier。"""
    base = DB.default_cache_base() if dry_run is False else None
    zip_dir = zip_dir or (DB.default_zip_dir() if base else None)
    cache_root = cache_root or (DB.default_cache_root() if base else None)
    existing_dir = existing_dir or (DB.default_existing_cache_dir() if base else None)
    outside_dir = outside_dir or (os.path.join(cache_root, "tune") if base else None)
    out = out or os.path.join(root, JUDGE_REL)
    if None in (zip_dir, cache_root, existing_dir, outside_dir):
        raise Stop("**--dry-run では置き場を全部明示する。止める**")
    ctx = Ctx(root, zip_dir, cache_root, existing_dir, outside_dir, None, docs)            # 評価用はここで止まる
    git = git_facts(git_dir or root)
    backend = backend or RealBackend()
    before = cache_snapshot(ctx)

    per_doc, rows, read_rows, full, blobs = [], [], [], {}, {}
    for doc in ctx.docs:
        text, _tb = ctx.read_report(doc)
        zb = ctx.read_zip(doc)
        outs = dict((p, backend.verify(zb, p, text)) for p in PROFILES)
        ids, c22, c26, only, differ = pair_claims(outs)
        full[doc] = dict((p, outs[p]["claims"]) for p in PROFILES)
        states = dict((p, dict(collections.Counter(c["state"] for c in outs[p]["claims"]))) for p in PROFILES)
        per_doc.append({"docID": doc, "型": ctx.styles[doc], "文の sha256": ctx.report_sha[doc],
                        "claim の数": dict((p, len(outs[p]["claims"])) for p in PROFILES),
                        "state の数": dict((p, dict((s, states[p].get(s, 0)) for s in STATES)) for p in PROFILES),
                        "片方の profile にしか無い id": only, "値・span・単位が profile 間で違う id": differ})
        facts = db = None
        for cid in ids:
            a, b = c22.get(cid), c26.get(cid)
            rows.append({"docID": doc, "id": cid,
                         "P22": None if a is None else claim_record(a), "P26": None if b is None else claim_record(b)})
            conds = read_row_conditions(a, b)
            if not conds:
                continue
            read_rows.append({"行": "%s:%s" % (doc, cid), "docID": doc, "id": cid, "条件": conds})
            if facts is None:
                facts, db = backend.facts(zb), ctx.read_db(doc)
            paragraph, note = paragraph_of(text, (a or b).get("span"))
            blobs["%s__%s.txt" % (doc, cid)] = render_dossier(doc, ctx.styles[doc], cid, paragraph, note, a, b, facts, db).encode("utf-8")
        say("  %s %s claim %d(P22) / %d(P26)" % (doc, ctx.styles[doc], len(c22), len(c26)))

    full_blob = dumps({"docs": full}).encode("utf-8")
    index = [{"行": r["行"], "file": "%s__%s.txt" % (r["docID"], r["id"]), "bytes": len(blobs["%s__%s.txt" % (r["docID"], r["id"])]),
              "sha256": sha256_hex(blobs["%s__%s.txt" % (r["docID"], r["id"])])} for r in read_rows]
    index_blob = dumps({"rows": index}).encode("utf-8")
    reader_blob = PR.READER_PROMPT.encode("utf-8")
    dossier_dir = os.path.join(outside_dir, "dossier")
    for name, blob in (("judge_full.json", full_blob),):
        write_text(os.path.join(outside_dir, name), blob.decode("utf-8"))
    for name, blob in blobs.items():
        write_text(os.path.join(dossier_dir, name), blob.decode("utf-8"))
    write_text(os.path.join(dossier_dir, "index.json"), index_blob.decode("utf-8"))
    write_text(os.path.join(dossier_dir, "reader_prompt.txt"), reader_blob.decode("utf-8"))

    rec = header(ctx, "P27 段 1 §5-1〜§5-3 ― 調整用の判定(P22・P26)・読む行・dossier", git, dry_run, backend, before, cache_snapshot(ctx))
    rec["claim の対の付け方"] = "id で対にする(前例 xbrl_fresh_2026-10-21.py)。片方にしか無い id と、値・span・単位が違う id は会社ごとに記録する"
    rec["会社"] = per_doc
    rec["claim"] = rows
    rec["集計"] = judge_summary(per_doc, read_rows)
    rec["読む行"] = read_rows
    rec["repo の外に置いたもの"] = {
        "folder": DB.display_path(outside_dir),
        "全部の欄(span・subject・value・recomputed を含む)": {"file": "judge_full.json", "sha256": sha256_hex(full_blob), "bytes": len(full_blob)},
        "dossier": {"folder": "dossier/", "件数": len(index), "index.json の sha256": sha256_hex(index_blob),
                    "各 file の sha256": dict((x["行"], x["sha256"]) for x in index),
                    "読み手の指示文 reader_prompt.txt の sha256": sha256_hex(reader_blob),
                    "読み手の指示文は封 §5-6 の字(prompts の READER_PROMPT)と同じ": reader_blob.decode("utf-8") == PR.READER_PROMPT}}
    rec["限界"] = ["読みはエージェントの読みで人間の読みではない(この記録は読む行を選ぶだけ。読みは reconcile の記録)",
                 "span・subject・value・recomputed は repo の外。claim の対は id で付け、値・span・単位の食い違いは会社ごとに数えた"]
    write_record(out, rec, key_value)
    say("-> %s(読む行 %d)" % (out, len(read_rows)))
    return rec


def judge_summary(per_doc, read_rows):
    out = {"claim": dict((p, sum(d["claim の数"][p] for d in per_doc)) for p in PROFILES)}
    out["state の数"] = dict((p, dict((s, sum(d["state の数"][p][s] for d in per_doc)) for s in STATES)) for p in PROFILES)
    out["VALUE_MISMATCH の率"] = dict((p, frac(out["state の数"][p]["VALUE_MISMATCH"], out["claim"][p])) for p in PROFILES)
    med = {}
    for st in STYLES:
        vals = [d["claim の数"]["P26"] for d in per_doc if d["型"] == st]
        med[st] = {"文の数": len(vals), "文あたりの claim の数(P26)": vals, "中央値": statistics.median(vals) if vals else None}
    out["文あたりの claim の数(P26)の型ごと"] = med
    conds = collections.Counter(c for r in read_rows for c in r["条件"])
    out["読む行"] = {"数": len(read_rows), "条件ごと(重なる)": dict(sorted(conds.items()))}
    return out


# ======================================================================================================
# §5-4・§5-5 読みの合わせ
def validate_label(lab):
    """札の字が封 §5-4 の語でなければ止める(語は出さない)。(側, 細目, 道5の形, 理由)。"""
    side, det = lab.get("側"), lab.get("細目")
    shape, why = lab.get("道5の形"), lab.get("理由")
    if side not in SIDES:
        raise Stop("**側の札が封 §5-4 の語でない。止める**")
    if side == UNSURE:
        if det is not None:
            raise Stop("**側が分からないなのに細目がある。止める**")
    elif det not in DETAILS[side]:
        raise Stop("**細目の札が封 §5-4 の語でない(側との組み合わせを含む)。止める**")
    if det == "道5":
        if not isinstance(shape, str) or not (SHAPE_MIN <= len(shape) <= SHAPE_MAX):
            raise Stop("**道5 の形が %d〜%d 字でない。止める**" % (SHAPE_MIN, SHAPE_MAX))
    elif shape not in (None, ""):
        raise Stop("**道5 でないのに道5の形がある。止める**")
    if not isinstance(why, str) or not why.strip():
        raise Stop("**理由が無い。止める**")
    return side, det, shape if det == "道5" else None, why


def combine(a, b):
    """封 §5-5。側が割れたら分からない(細目なし)。側が同じで細目が割れたら、側はその側・細目は分からない。"""
    (sa, da), (sb, db) = a, b
    if sa != sb:
        return UNSURE, None
    if sa == UNSURE:
        return UNSURE, None
    return sa, (da if da == db else UNSURE)


def load_seat(path, want_keys):
    d = read_json(path)
    labels = d.get("札")
    if not isinstance(labels, list):
        raise Stop("**札の file に 札 の列が無い。止める**")
    out = {}
    for lab in labels:
        key = lab.get("行")
        if key in out:
            raise Stop("**札の file に同じ行が 2 回ある。止める**")
        out[key] = validate_label(lab)
    if set(out) != set(want_keys):
        raise Stop("**行と札が 1 対 1 でない(行 %d・札 %d・足りない %d・余り %d)。止める**" % (
            len(want_keys), len(out), len(set(want_keys) - set(out)), len(set(out) - set(want_keys))))
    return d.get("席"), out, sha256_hex(read_bytes(path))


def readings_summary(rows, judge_rows):
    n = len(rows)
    agree = sum(1 for r in rows if r["席1"]["側"] == r["席2"]["側"])
    side = collections.Counter(r["合わせた"]["側"] for r in rows)
    p26 = [r for r in rows if judge_rows.get(r["行"], {}).get("P26") == "VALUE_MISMATCH"]
    p26_side = collections.Counter(r["合わせた"]["側"] for r in p26)
    tool = [r for r in rows if r["合わせた"]["側"] == "道具" and r["合わせた"]["細目"] != UNSURE]
    det = collections.Counter(r["合わせた"]["細目"] for r in tool)
    n_b = sum(det.get(k, 0) for k in ("道1", "道2", "道3", "道4"))
    return {"読む行": n, "2 席の側が一致した行": frac(agree, n),
            "合わせた側の内訳": dict((s, side.get(s, 0)) for s in SIDES),
            "P26 で VALUE_MISMATCH の行": {"行": len(p26), "合わせた側の内訳": dict((s, p26_side.get(s, 0)) for s in SIDES),
                                      "道具の率": frac(p26_side.get("道具", 0), len(p26)), "分からないの率": frac(p26_side.get(UNSURE, 0), len(p26))},
            "合わせた細目が付いた道具の行": {"行": len(tool), "細目の内訳": dict(sorted(det.items())),
                                      "道1〜道4": frac(n_b, len(tool)), "道5": frac(det.get("道5", 0), len(tool))},
            "合わせた札が文2の行": sum(1 for r in rows if r["合わせた"]["側"] == "文" and r["合わせた"]["細目"] == "文2")}


def run_reconcile(root=DEFAULT_ROOT, seat_a=None, seat_b=None, judge_record=None, out=None, outside_dir=None, backend=None, dry_run=False,
                  zip_dir=None, cache_root=None, existing_dir=None, git_dir=None, key_value=None, say=print):
    base = DB.default_cache_base() if dry_run is False else None
    zip_dir = zip_dir or (DB.default_zip_dir() if base else None)
    cache_root = cache_root or (DB.default_cache_root() if base else None)
    existing_dir = existing_dir or (DB.default_existing_cache_dir() if base else None)
    outside_dir = outside_dir or (os.path.join(cache_root, "tune") if base else None)
    out = out or os.path.join(root, READINGS_REL)
    judge_record = judge_record or os.path.join(root, JUDGE_REL)
    if None in (zip_dir, cache_root, existing_dir, outside_dir) or not seat_a or not seat_b:
        raise Stop("**置き場か 2 席の札の file が足りない。止める**")
    ctx = Ctx(root, zip_dir, cache_root, existing_dir, outside_dir, None, None)
    git = git_facts(git_dir or root)
    backend = backend or NullBackend()
    before = cache_snapshot(ctx)
    jr = read_json(judge_record)
    want = [r["行"] for r in jr["読む行"]]
    by_key = dict((r["docID"] + ":" + r["id"], r) for r in jr["claim"])
    judge_rows = dict((k, {"P22": (v["P22"] or {}).get("state"), "P26": (v["P26"] or {}).get("state")}) for k, v in by_key.items() if k in want)
    name_a, la, sha_a = load_seat(seat_a, want)
    name_b, lb, sha_b = load_seat(seat_b, want)
    rows, free = [], {"席1": {}, "席2": {}}
    for r in jr["読む行"]:
        k = r["行"]
        (sa, da, shape_a, why_a), (sb, db, shape_b, why_b) = la[k], lb[k]
        side, det = combine((sa, da), (sb, db))
        rows.append({"行": k, "docID": r["docID"], "id": r["id"], "席1": {"側": sa, "細目": da}, "席2": {"側": sb, "細目": db},
                     "合わせた": {"側": side, "細目": det}})
        free["席1"][k] = {"理由": why_a, "道5の形": shape_a}
        free["席2"][k] = {"理由": why_b, "道5の形": shape_b}
    free_blob = dumps(free).encode("utf-8")
    write_text(os.path.join(outside_dir, "readings_free_text.json"), free_blob.decode("utf-8"))
    rec = header(ctx, "P27 段 1 §5-4・§5-5 ― 読みの合わせ(2 席・人の目なし)", git, dry_run, backend, before, cache_snapshot(ctx))
    rec["読みは"] = "エージェントの読み(2 席。互いの読みを見ない)で、人間の読みではない"
    rec["合わせ方(封 §5-5)"] = "側が割れたら 分からない(細目なし)。側が同じで細目が割れたら 側はその側・細目は 分からない"
    rec["入力"] = {"判定の記録": os.path.relpath(judge_record, root) if inside(judge_record, root) else "(repo の外)",
                 "判定の記録の sha256": sha256_hex(read_bytes(judge_record)),
                 "席1 の札の file の sha256": sha_a, "席2 の札の file の sha256": sha_b}
    rec["行"] = rows
    rec["集計"] = readings_summary(rows, judge_rows)
    rec["repo の外に置いたもの"] = {"folder": DB.display_path(outside_dir),
                              "道5 の形と各席の理由の文": {"file": "readings_free_text.json", "sha256": sha256_hex(free_blob), "bytes": len(free_blob)}}
    write_record(out, rec, key_value)
    say("-> %s(読む行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
# §6 注入
def find_base_claim(claims, value, digits, unit):
    """注入の元の数に当たる、無改変の claim(1 件に決まるときだけ)。前例 xbrl_fresh_2026-10-21.py の ``_find_base_claim`` と同じ手順
    (値が合い、書かれた桁の字が span にある → 1 件でなければ値だけ → 1 件でなければ None)。値は円に直して比べる。"""
    target = scaled(value, unit)
    hit = [c for c in claims if c.get("value") is not None and same_number(claim_scaled(c), target)]
    cands = [c for c in hit if c.get("span") and digits in c["span"]]
    if len(cands) != 1:
        cands = hit
    return cands[0] if len(cands) == 1 else None


def claim_for_p27(claims, inj, unit):
    """注入した場所の claim(1 件に決まるときだけ。前例 ``claim_for`` と同じ手順で、値は円に直して比べる)。"""
    target = scaled(inj["new_value"], unit)
    hit = [c for c in claims if c.get("value") is not None and same_number(claim_scaled(c), target)]
    cands = [c for c in hit if c.get("span") and inj["replacement"] in c["span"]]
    if len(cands) != 1:
        cands = hit
    return cands[0] if len(cands) == 1 else None


def base_status(base_claims, base_by_id, tok, text):
    """(状態, P22 の土台の claim)。土台 = 無改変で P22 と P26 の両方が GROUNDED。"""
    digits = text[tok.start:tok.end]
    bc = find_base_claim(base_claims["P22"], tok.value, digits, tok.unit)
    if bc is None:
        return "基準に対応が付かない", None
    other = base_by_id["P26"].get(bc["id"])
    if other is None or (other["value"], other["span"], other["unit"]) != (bc["value"], bc["span"], bc["unit"]):
        return "profile 間で claim が合わない", None
    g22, g26 = bc["state"] == "GROUNDED", other["state"] == "GROUNDED"
    if g22 and g26:
        return "両方 GROUNDED", bc
    if g22 or g26:
        return "P22 のみ GROUNDED" if g22 else "P26 のみ GROUNDED", None
    return "どちらも GROUNDED でない", None


def pick_r(seed, doc, claim_id, tok, vindex, rng=None):
    """封 §6-3 の T8_REL。r を ``random.Random("<seed>:<docID>:<claim id>")`` で (-0.10, -0.03, +0.03, +0.10) から 1 つ選び、
    新しい値 = 書かれた値 × (1 + r) を書かれた桁(小数の桁数は元の字のまま)に丸める。元の値と同じ・refs のどれかの値と同じなら、
    同じ乱数列の次の値で 4 回まで。全部駄目なら None(site にしない)。(r, 新しい値, 何回目で決まったか)。"""
    rng = rng if rng is not None else random.Random("%s:%s:%s" % (seed, doc, claim_id))
    places = len(tok.text.split(".")[1]) if tok.has_frac else 0
    for i in range(T8_TRIES):
        r = rng.choice(T8_R_VALUES)
        new = round(tok.value * (1 + r), places)
        if abs(new - tok.value) <= TOL:
            continue
        if S._matches(new, tok.unit, vindex):
            continue
        return r, new, i + 1
    return None


def t8_candidates(text, refs, base_claims, base_by_id, seed, doc, cap, rng_for_r=None):
    """T8_REL の site。円族の token のうち、土台に 1 件で対応し(両 profile で GROUNDED)、r が決まるもの。
    token を ``Random("<seed>|<docID>|T8_REL")`` で並べ替え、先頭から cap 件を採る。(採った inj の列, 数え)。"""
    counts = collections.Counter()
    vindex = S._value_index(refs)
    toks = [t for t in N.scan(text) if t.unit in MONEY_FAMILY and N.is_quantity(text, t)]
    random.Random("%s|%s|T8_REL" % (seed, doc)).shuffle(toks)
    counts["円族の token"] = len(toks)
    valid = []
    for t in toks:
        status, bc = base_status(base_claims, base_by_id, t, text)
        counts[status] += 1
        if bc is None:
            continue
        pick = pick_r(seed, doc, bc["id"], t, vindex, None if rng_for_r is None else rng_for_r(t))
        if pick is None:
            counts["r が決まらず site にしない"] += 1
            continue
        valid.append((t, bc, pick))
    counts["作れる site"] = len(valid)
    out = []
    for t, bc, (r, new, tries) in valid[:cap]:
        inj = {"type": "T8_REL", "id": "%s-T8-%02d" % (doc, len(out) + 1), "new_value": new,
               "replacement": N.render_value(new, t), "span": [t.start, t.end],
               "detail": {"original_value": t.value, "relative": r, "tries": tries, "unit": t.unit}}
        out.append((inj, t, bc))
    counts["採った"] = len(out)
    return out, counts


def named_original(res, base):
    """封 §6-4 の「名指して原本の値を返した」: VALUE_MISMATCH で、pointers の先頭が土台(同じ profile の無改変)の先頭と同じで、
    recomputed が土台の recomputed と同じ。(pointers が空のときは名指しに数えない。)"""
    if res["state"] != "VALUE_MISMATCH":
        return False
    rp, bp = res.get("pointers") or [], base.get("pointers") or []
    return bool(rp) and bool(bp) and rp[0] == bp[0] and res.get("recomputed") == base.get("recomputed")


def classify(res, base):
    if res is None:
        return {"対応": False, "結果": LABEL_UNMAPPED, "state": None, "reason": None}
    s = res["state"]
    if s == "GROUNDED":
        label = LABEL_PASS
    elif s == "VALUE_MISMATCH":
        label = LABEL_NAMED_ORIGINAL if named_original(res, base) else LABEL_NAMED_OTHER
    elif s == "POINTER_NOT_FOUND":
        label = LABEL_PNF
    elif s == "UNVERIFIABLE":
        label = LABEL_UNV
    else:
        raise Stop("**state が 4 つの語でない。止める**")
    return {"対応": True, "結果": label, "state": s, "reason": safe_reason(res.get("reason"))}


def inject_doc(ctx, backend, doc, seed, work, cap=INJECT_CAP):
    """1 書類の注入(T1_VALUE・T8_REL)。1 回に 1 件。round-trip を確かめ、違えば止める。(行, 外に置く行, 数え)。"""
    text, _tb = ctx.read_report(doc)
    if N.normalize_digits(text) != text:
        raise Stop("**文に全角の数字がある(select は半角の文を前提にする)。止める**")
    zb = ctx.read_zip(doc)
    refs = backend.refs(ctx.zip_path(doc), doc, work)
    base_claims = dict((p, backend.verify(zb, p, text)["claims"]) for p in PROFILES)
    base_by_id = dict((p, dict((c["id"], c) for c in base_claims[p])) for p in PROFILES)
    toks = dict(((t.start, t.end), t) for t in N.scan(text))
    style = ctx.styles[doc]
    counts, work_list = {}, []

    chosen, cat, _a, _w = IJ.select(text, refs, "xbrl", seed, doc, cap, types=["T1_VALUE"])
    c1 = collections.Counter()
    c1["作れる site"], c1["採った"] = cat["T1_VALUE"], len(chosen)
    for inj in chosen:
        tok = toks[tuple(inj["span"])]
        status, bc = base_status(base_claims, base_by_id, tok, text)
        c1[status] += 1
        work_list.append((inj, tok, bc))
    counts["T1_VALUE"] = c1
    t8, c8 = t8_candidates(text, refs, base_claims, base_by_id, seed, doc, cap)
    counts["T8_REL"] = c8
    work_list += t8

    rows, full = [], []
    for inj, tok, bc in work_list:
        tampered, placements = IJ.apply_edits(text, [inj])
        if IJ.revert(tampered, [inj], placements, text) != text:
            raise Stop("**round-trip が合わない: %s %s。止める**" % (doc, inj["id"]))
        if bc is None:
            continue
        row = {"docID": doc, "id": inj["id"], "型": inj["type"], "文体": style, "基準の claim": bc["id"]}
        if inj["type"] == "T8_REL":
            row["r"], row["r を決めた回"] = inj["detail"]["relative"], inj["detail"]["tries"]
        for p in PROFILES:
            res = claim_for_p27(backend.verify(zb, p, tampered)["claims"], inj, tok.unit)
            row[p] = classify(res, base_by_id[p][bc["id"]])
        rows.append(row)
        full.append({"docID": doc, "id": inj["id"], "元の字": text[inj["span"][0]:inj["span"][1]], "後の字": inj["replacement"],
                     "新しい値": inj["new_value"], "単位": tok.unit})
    return rows, full, dict((t, dict(c)) for t, c in counts.items())


_STATE = {}


def _inject_worker(doc):
    st = _STATE
    work = os.path.join(st["work"], doc)
    os.makedirs(work, exist_ok=True)
    return inject_doc(st["ctx"], st["backend"], doc, st["seed"], work, st["cap"])


def _proc_main(doc, conn):
    try:
        conn.send(("ok", _inject_worker(doc)))
    except BaseException as exc:                    # Stop を含む。文言に値は入っていない
        conn.send(("err", type(exc).__name__, str(exc) if isinstance(exc, SystemExit) else ""))
    finally:
        conn.close()


def run_parallel(docs, procs):
    """書類ごとの注入を fork した process で並べて走らせる(関数を pickle しないので、importlib で読んだ module でも動く)。"""
    mp = multiprocessing.get_context("fork")
    pending, running, results = list(docs), {}, {}
    try:
        while pending or running:
            while pending and len(running) < procs:
                d = pending.pop(0)
                parent, child = mp.Pipe(duplex=False)
                proc = mp.Process(target=_proc_main, args=(d, child))
                proc.start()
                child.close()
                running[d] = (proc, parent)
            for d, (proc, conn) in list(running.items()):
                if conn.poll(0.05):
                    msg = conn.recv()
                    proc.join()
                    del running[d]
                    if msg[0] == "err":
                        raise Stop(msg[2] or "**注入の worker が止まった(%s)。止める**" % msg[1])
                    results[d] = msg[1]
                elif not proc.is_alive() and not conn.poll():
                    raise Stop("**注入の worker が結果を返さずに終わった。止める**")
    finally:
        for proc, _conn in running.values():
            proc.terminate()
    return results


def inject_summary(rows):
    out = {}
    for t in INJECT_TYPES:
        out[t] = {}
        for p in PROFILES:
            out[t][p] = {}
            for st in STYLES + ("全体",):
                sel = [r for r in rows if r["型"] == t and (st == "全体" or r["文体"] == st)]
                mapped = [r for r in sel if r[p]["対応"]]
                lab = collections.Counter(r[p]["結果"] for r in mapped)
                rs = lambda label: collections.Counter(r[p]["reason"] or "(reason なし)" for r in mapped if r[p]["結果"] == label)   # noqa: E731
                d = {"注入の行": len(sel), "対応が付く": len(mapped), "対応が付かない": len(sel) - len(mapped)}
                for label in (LABEL_PASS, LABEL_NAMED_ORIGINAL, LABEL_NAMED_OTHER, LABEL_PNF, LABEL_UNV):
                    d[label] = frac(lab.get(label, 0), len(mapped))
                d["POINTER_NOT_FOUND の reason の内訳"] = dict(sorted(rs(LABEL_PNF).items()))
                d["UNVERIFIABLE の reason の内訳"] = dict(sorted(rs(LABEL_UNV).items()))
                out[t][p][st] = d
        both = [r for r in rows if r["型"] == t and all(r[p]["対応"] for p in PROFILES)]
        out[t]["両方の profile で対応が付く"] = len(both)
    return out


def run_inject(root=DEFAULT_ROOT, docs=None, out=None, outside_dir=None, backend=None, dry_run=False, zip_dir=None, cache_root=None,
               existing_dir=None, work_root=None, git_dir=None, procs=1, seed_fn=None, cap=INJECT_CAP, key_value=None, say=print):
    """封 §6。土台・site・T1_VALUE(inject.select のまま)・T8_REL・round-trip・数え方。"""
    base = DB.default_cache_base() if dry_run is False else None
    zip_dir = zip_dir or (DB.default_zip_dir() if base else None)
    cache_root = cache_root or (DB.default_cache_root() if base else None)
    existing_dir = existing_dir or (DB.default_existing_cache_dir() if base else None)
    outside_dir = outside_dir or (os.path.join(cache_root, "tune") if base else None)
    out = out or os.path.join(root, INJECT_REL)
    if None in (zip_dir, cache_root, existing_dir, outside_dir):
        raise Stop("**--dry-run では置き場を全部明示する。止める**")
    work_root = work_root or tempfile.mkdtemp(prefix="p27_tune_", dir=os.environ.get("TMPDIR"))
    ctx = Ctx(root, zip_dir, cache_root, existing_dir, outside_dir, work_root, docs)            # 評価用はここで止まる
    git = git_facts(git_dir or root)
    backend = backend or RealBackend()
    seed, seed_meta = (seed_fn or (lambda path: IJ.verify_seed_sealed(path)))(SEED_FILE)      # git に追跡され内容が一致していなければ止まる
    before = cache_snapshot(ctx)
    _STATE.update(ctx=ctx, backend=backend, seed=seed, work=work_root, cap=cap)
    if procs > 1:
        results = run_parallel(ctx.docs, procs)
    else:
        results = dict((d, _inject_worker(d)) for d in ctx.docs)
    rows, full, per_doc = [], [], {}
    for d in ctx.docs:
        r, f, c = results[d]
        rows += r
        full += f
        per_doc[d] = c
        say("  %s 注入 %d 件" % (d, len(r)))
    full_blob = dumps({"seed 以外の注入の字": full}).encode("utf-8")
    write_text(os.path.join(outside_dir, "inject_full.json"), full_blob.decode("utf-8"))
    rec = header(ctx, "P27 段 1 §6 ― 調整用の注入(T1_VALUE・T8_REL)", git, dry_run, backend, before, cache_snapshot(ctx))
    rec["種"] = {"file": "measure/SEED.json", "sealed_in_commit": seed_meta.get("sealed_in_commit"), "seed_file_sha256": seed_meta.get("seed_file_sha256")}
    rec["型"] = {"T1_VALUE": "inject.select(types=[T1_VALUE]) のまま", "T8_REL": "円の単位族の token・r ∈ %s・%d 回まで" % (list(T8_R_VALUES), T8_TRIES),
               "上限": "型ごと・1 書類あたり %d 件" % cap}
    rec["書類別の数え"] = per_doc
    rec["注入の行の数"] = len(rows)
    rec["集計"] = inject_summary(rows)
    rec["T8_REL の site"] = {"注入の行": sum(1 for r in rows if r["型"] == "T8_REL"),
                          "作れる site(上限の前)": sum(per_doc[d]["T8_REL"].get("作れる site", 0) for d in per_doc)}
    rec["行"] = rows
    rec["repo の外に置いたもの"] = {"folder": DB.display_path(outside_dir),
                              "注入の字・新しい値": {"file": "inject_full.json", "sha256": sha256_hex(full_blob), "bytes": len(full_blob)}}
    rec["限界"] = ["注入は 2 型だけ。DB と原本の差の実際の分布ではない(T8_REL の r の 4 値は 3 本の差の大きさに寄せた決め打ち)",
                 "T1_VALUE の cap は inject.select の採用に掛け(基準で絞る前)、T8_REL の cap は site に掛けた"]
    write_record(out, rec, key_value)
    say("-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("judge", "reconcile", "inject"))
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--git-dir", default=None, help="HEAD と W を読む git の folder(既定: --root)")
    ap.add_argument("--docs", default=None, help="コンマ区切り(既定: 調整用の全部)。評価用は止める")
    ap.add_argument("--out", default=None)
    ap.add_argument("--outside-dir", default=None, help="既定: ~/.cache/audit-core/edinetdb-p27/tune/")
    ap.add_argument("--zip-dir", default=None)
    ap.add_argument("--cache-root", default=None)
    ap.add_argument("--existing-cache-dir", default=None)
    ap.add_argument("--work-dir", default=None, help="prepare_xbrl の作業 folder の親(既定: TMPDIR)")
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--seat-a", default=None)
    ap.add_argument("--seat-b", default=None)
    ap.add_argument("--judge-record", default=None)
    ap.add_argument("--dry-run", action="store_true", help="engine と ZIP の中身を作り物にして同じ経路を通す。置き場を全部明示する")
    a = ap.parse_args(argv)
    docs = a.docs.split(",") if a.docs else None
    common = dict(root=a.root, out=a.out, outside_dir=a.outside_dir, zip_dir=a.zip_dir, cache_root=a.cache_root,
                  existing_dir=a.existing_cache_dir, git_dir=a.git_dir, dry_run=a.dry_run)
    backend = StubBackend() if a.dry_run else None
    if a.cmd == "reconcile":
        backend = None
    if a.cmd == "judge":
        run_judge(docs=docs, backend=backend, **common)
    elif a.cmd == "reconcile":
        run_reconcile(seat_a=a.seat_a, seat_b=a.seat_b, judge_record=a.judge_record, backend=backend, **common)
    else:
        run_inject(docs=docs, backend=backend, work_root=a.work_dir, procs=a.procs, **common)


if __name__ == "__main__":
    main()
