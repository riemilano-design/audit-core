# -*- coding: utf-8 -*-
"""封 docs/XBRL_P27_SEAL_2026-10-27.md §7(評価用の測定の script)・§6(順序の門の commit の求め方)・§3-2(V-1〜V-7)・§4(K-1〜K-5)・§9-4(前半)
― **評価用の 10 社の文を 4 profile(P22・P26・P27・P27E)に通す測定の script。**
費用 0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(core/・adapters/)は 1 字も変えない。
段 1 の script ``measure/xbrl_p27_tune_2026-10-27.py`` と 97 書類の script ``measure/xbrl_p27_regress97_2026-10-27.py`` は **1 字も変えず**、importlib で読んで使う
(``Ctx``・``StubBackend``・``write_record``・``render_dossier``・``inject_doc``・``t8_candidates``・``base_status``・``claim_for_p27``・``classify``・
``load_seat``・``combine``・``rule_counts`` は写さず、同じ関数 object を使う)。

3 つの subcommand(段 1 と同じ)::

    python3 measure/xbrl_p27_eval_2026-10-27.py judge     [--docs A,B] [--out <file>]       # 判定(4 profile)・読む行・dossier
    python3 measure/xbrl_p27_eval_2026-10-27.py inject    [--docs A,B] [--procs N]          # 注入(T1_VALUE・T8_REL)
    python3 measure/xbrl_p27_eval_2026-10-27.py reconcile --seat-a <file> --seat-b <file>   # 読み(2 席)の合わせ

共通: ``--dry-run`` は engine と ZIP の中身を作り物(``StubBackend4``)に替えて同じ経路を通す(``--out`` と置き場を全部明示する。試験・下見は使い捨ての folder を渡す)。
置き場: ``--zip-dir``(原本の ZIP)・``--cache-root``(既定の外の置き場の親)・``--reports-dir``(評価用の文。既定 ``<cache-root>/reports``)・
``--db-dir``(DB の応答。``<db-dir>/<docID>/{financials,companies,ratios}.json``。既定 ``<cache-root>``)・``--outside-dir``(既定 ``<cache-root>/eval``)。

**評価用の文を開く条件**(すべて満たすときだけ。1 つでも違えば下の止めになる)
  1. 走る前の確かめ(封 §7 の (a)(b)): (a) 封の file が HEAD で追跡され(``git ls-files --error-unmatch``)作業木と同じ(``git diff --quiet HEAD``)。
     (b) 封 §6 の求め方(``git log --diff-filter=A``、E は ``-S'PROFILES["P27E"]'`` の最も古い commit)で W・T・S2・E を git から求め(字で留めない)、
     ``merge-base --is-ancestor`` で W ⊑ S2・S2 ⊏ E・E ⊑ HEAD、``git diff --quiet E HEAD -- audit-core/adapters audit-core/core``、
     ``V.PROFILES`` に P22・P26・P27・P27E が在り ``V.DEFAULT_PROFILE == "P26"``。
  2. 対象は W の記録(``fixtures/xbrl/p27/reports_2026-10-27.json``)の ``区分`` が評価用の 10 件だけ。
  3. (c) 文を開いた直後に、文の sha256 が W の記録の ``文の sha256`` と全部同じ(ZIP は取得の記録 ``fixtures/xbrl/fresh/fetched_2026-10-21.json``、
     DB の応答は ``fixtures/xbrl/p27/dbfetch_2026-10-27.json`` と照らす)。この照合は判定・注入の前に 10 書類の全部に当て、記録も外の file も書く前に止まる。

**開かずに止める条件**(``Stop``。文・ZIP・DB の応答のどの file も開かない)
  - 走る前の確かめの (a)(b) のどれか 1 つでも違う。
  - 調整用の docID(段 1 の ``Ctx.guard`` の逆)・W の記録の区分の外の docID が ``--docs`` に在る。
  - 外の置き場が既存の cache・ZIP の folder・repo の中、または段 1 の置き場(``tune``・``tune_p27``)。出力が既に在る(測り直さない)。
  止めた後に cache の件数・名前の一覧が変わっていれば、記録を書かずに止める。

**repo に入れない欄**: ``span``・``subject``・``value``・``recomputed`` と、評価用の文の字・DB の値・理由の文・道5の形・注入の字。
全部の欄は repo の外 ``~/.cache/audit-core/edinetdb-p27/eval/`` に置き、その sha256 を記録に持たせる(段 1 の ``write_record`` が禁止欄と鍵らしい字を検査する)。
``~/.cache/audit-core/edinet/`` と ``edinet-fresh-2026-10-21/`` には 1 file も足さない(前後の件数と名前の一覧の sha256 を記録する)。
標準出力は件数・率・sha256・path だけ(文の字・claim の span・DB の値・理由の字は印字しない)。

読み手の札の file(``reconcile`` の入力)の形は段 1 と同じ(JSON)::

    {"席": "席1", "札": [{"行": "<docID>:<claim id>", "側": "文|道具|分からない", "細目": "文1〜文4|道1〜道5|null",
                          "道5の形": "10〜40 字(細目が道5のときだけ)", "理由": "1〜2 文"}, ...]}
"""
import argparse
import collections
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)
for _p in (HERE, DEFAULT_ROOT, os.path.join(DEFAULT_ROOT, "core", "py")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _load(name, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T = _load("xbrl_p27_tune_2026-10-27.py", "p27_tune_for_eval")             # 段 1 の測定の script(1 字も変えない)
R97 = _load("xbrl_p27_regress97_2026-10-27.py", "p27_regress97_for_eval")  # 97 書類の測定の script(rule_counts を読む。1 字も変えない)
DB = T.DB
PR = T.PR
V = R97.V                                                                  # adapters.xbrl.vocabulary(走る前の確かめで profile の一覧を見る)
Stop = T.Stop

SEAL = "audit-core/docs/XBRL_P27_SEAL_2026-10-27.md"
FIX = "audit-core/fixtures/xbrl/p27/"
W_PATH = FIX + "reports_2026-10-27.json"
T_PATHS = (FIX + "tune_2026-10-27.json", FIX + "tune_inject_2026-10-27.json", FIX + "tune_readings_2026-10-27.json")
VOCAB_PATH = "audit-core/adapters/xbrl/vocabulary.py"
ENGINE_PATHS = ("audit-core/adapters", "audit-core/core")
E_PICKAXE = 'PROFILES["P27E"]'
HEX40 = re.compile(r"[0-9a-f]{40}")

JUDGE_REL = os.path.join("fixtures", "xbrl", "p27", "eval_2026-10-27.json")
INJECT_REL = os.path.join("fixtures", "xbrl", "p27", "eval_inject_2026-10-27.json")
READINGS_REL = os.path.join("fixtures", "xbrl", "p27", "eval_readings_2026-10-27.json")
OUTSIDE_NAME = "eval"                                                      # 外の置き場の既定: <cache-root>/eval(段 1 の tune/・tune_p27/ には書かない)
STAGE1_OUTSIDE_NAMES = ("tune", "tune_p27")

PROFILES = ("P22", "P26", "P27", "P27E")                                   # 封 §7: この順
BASE_PROFILES = ("P22", "P26")                                             # 土台 = 無改変で P22 と P26 の両方が GROUNDED
STATES = T.STATES
INJECT_TYPES = T.INJECT_TYPES
INJECT_CAP = T.INJECT_CAP
RULE_KEYS = ("C2 per_unit_counter", "C3 future_period", "C1 の窓に入った claim", "C1 の窓に入って other_concept になった claim", "B relative_within_rho")

# 読む行の条件の名前(封 §7: (P27E で VALUE_MISMATCH かつ P26 で VALUE_MISMATCH でない)∪(P26 で GROUNDED かつ P27 で GROUNDED でない))
COND_K3 = "P27E_VALUE_MISMATCH_and_P26_not_VALUE_MISMATCH"
COND_K4 = "P26_GROUNDED_and_P27_not_GROUNDED"
CONDITIONS = (COND_K3, COND_K4)

# 束(dossier)の P22・P26 の欄の後ろに P27・P27E の欄を足す形(字で固定。結果の門が script の定数と束を照らす)
DOSSIER_P27_PROFILES = ("P27", "P27E")
RULE_PROFILES = ("P27", "P27E")                                                # 規則ごとの数(provenance)を持つ profile(束に足す profile とは別の定数)
DOSSIER_P27_BLOCK = "## 2 claim の全部の欄({profile})\n{body}\n\n"
DOSSIER_NO_CLAIM = "(この profile に同じ id の claim が無い)"
DOSSIER_P27_FACTS_HEAD = "## 3b P27・P27E だけが名指した pointers の XBRL の fact"
DOSSIER_MARK3 = "## 3 pointers の XBRL の fact"                            # 段 1 の render_dossier の節の頭(この間に差し込む)
DOSSIER_MARK4 = "## 4 DB の応答(companies)"

# 段 1 の測定の script の関数をそのまま使う(写さない。試験は ``is`` で見る)
select_t1_value = T.IJ.select
t8_candidates = T.t8_candidates
base_status = T.base_status
claim_for_p27 = T.claim_for_p27
classify = T.classify
inject_doc = T.inject_doc
claim_record = T.claim_record
render_dossier = T.render_dossier
load_seat = T.load_seat
combine = T.combine
validate_label = T.validate_label
write_record = T.write_record
rule_counts = R97.rule_counts

T.PROFILES = PROFILES                                                      # 段 1 の関数(inject_doc・inject_summary)が見る profile の一覧を 4 つにする(E の再現の script と同じ形)
T.COMMIT_KEYS = tuple(T.COMMIT_KEYS) + ("T の commit", "S2 の commit", "E の commit")   # 40 桁の小文字 16 進(git の commit)を持つ欄を鍵の検査から外す(段 1 は HEAD・W だけ)


# ======================================================================================================
# 小さい道具
sha256_hex = T.sha256_hex
read_bytes = T.read_bytes
read_json = T.read_json
frac = T.frac
dumps = T.dumps


def write_new(path, text):
    """repo の外に置く file。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop("**外の置き場に file が既に在る: %s。止める**" % os.path.basename(path))
    T.write_text(path, text)


# ======================================================================================================
# 走る前の確かめ(封 §7 の (a)(b))
def git_runner(git_dir):
    """``run(*args) -> (returncode, stdout)``。試験は同じ形の関数に差し替える。"""
    def run(*args):
        r = subprocess.run(["git", "-C", git_dir] + list(args), capture_output=True, text=True)
        return r.returncode, r.stdout.strip()
    return run


def _added_commit(run, path):
    """``git log --diff-filter=A --format=%H -- <path>`` の行がちょうど 1 つ(0 か 2 以上なら止める。封 §6)。"""
    rc, out = run("log", "--diff-filter=A", "--format=%H", "--", path)
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if rc != 0 or len(lines) != 1 or not HEX40.fullmatch(lines[0]):
        raise Stop("**%s を足した commit がちょうど 1 つに決まらない(%d 行)。止める**" % (os.path.basename(path), len(lines)))
    return lines[0]


def _oldest_engine_commit(run):
    """E = ``git log --format=%H -S'PROFILES["P27E"]' -- audit-core/adapters/xbrl/vocabulary.py`` の最も古い commit(出力は新しい順なので最後の行)。"""
    rc, out = run("log", "--format=%H", "-S" + E_PICKAXE, "--", VOCAB_PATH)
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if rc != 0 or not lines or not HEX40.fullmatch(lines[-1]):
        raise Stop("**P27E を足した engine の commit(E)が git から求まらない。止める**")
    return lines[-1]


def _is_ancestor(run, a, b):
    return run("merge-base", "--is-ancestor", a, b)[0] == 0


def preflight(run, vocab=None):
    """(a)(b)。1 つでも違えば ``Stop``(評価用のどの file も開かずに止める)。(W・T・S2・E・HEAD の commit と確かめた事実)。"""
    vocab = vocab if vocab is not None else V
    if run("ls-files", "--error-unmatch", "--", SEAL)[0] != 0:                               # (a)
        raise Stop("**封の file が git で追跡されていない。止める**")
    if run("diff", "--quiet", "HEAD", "--", SEAL)[0] != 0:
        raise Stop("**封の file が HEAD と作業木で違う。止める**")
    rc, head = run("rev-parse", "HEAD")                                                       # (b)
    if rc != 0 or not HEX40.fullmatch(head):
        raise Stop("**HEAD が読めない。止める**")
    w = _added_commit(run, W_PATH)
    ts = [_added_commit(run, p) for p in T_PATHS]
    if len(set(ts)) != 1:
        raise Stop("**T の 3 つの記録が同じ commit でない。止める**")
    s2 = _added_commit(run, SEAL)
    e = _oldest_engine_commit(run)
    if not _is_ancestor(run, w, s2):
        raise Stop("**W が S2 の祖先でない(W ⊑ S2)。止める**")
    if s2 == e or not _is_ancestor(run, s2, e):
        raise Stop("**S2 が E の真の祖先でない(S2 ⊏ E)。止める**")
    if not _is_ancestor(run, e, head):
        raise Stop("**E が HEAD の祖先でない(E ⊑ HEAD)。止める**")
    if run("diff", "--quiet", e, "HEAD", "--", *ENGINE_PATHS)[0] != 0:
        raise Stop("**engine(adapters・core)が E から動いている。止める**")
    profiles = getattr(vocab, "PROFILES", {})
    if any(p not in profiles for p in PROFILES):
        raise Stop("**V.PROFILES に P22・P26・P27・P27E の全部が無い。止める**")
    if getattr(vocab, "DEFAULT_PROFILE", None) != "P26":
        raise Stop("**V.DEFAULT_PROFILE が P26 でない。止める**")
    return {"HEAD": head, "W": w, "T": ts[0], "S2": s2, "E": e}


# ======================================================================================================
# 材料の在りか(評価用の件だけ。段 1 の Ctx.guard の逆)
class EvalCtx(T.Ctx):
    """段 1 の ``Ctx`` を継ぎ、``guard`` だけ逆にする。W の記録の区分が評価用の docID だけを通す(調整用・区分の外は、どの file も開く前に止める)。
    文は ``reports_dir``、DB の応答は ``db_dir`` から読む(sha256 は W の記録・取得の記録・dbfetch の記録と照らす)。"""

    def __init__(self, root, zip_dir, cache_root, existing_dir, outside_dir, work_root, docs=None, reports_dir=None, db_dir=None):
        self.reports_dir = reports_dir or os.path.join(cache_root, "reports")
        self.db_dir = db_dir or cache_root
        w = read_json(os.path.join(root, T.REPORTS_REL))
        self.eval_list = [c["docID"] for c in w["会社"] if c.get("区分") == "評価用"]
        T.Ctx.__init__(self, root, zip_dir, cache_root, existing_dir, outside_dir, work_root, self.eval_list if docs is None else docs)
        if outside_dir is not None:
            for name in STAGE1_OUTSIDE_NAMES:
                if T.inside(outside_dir, os.path.join(cache_root, name)):
                    raise Stop("**外の置き場が段 1 の置き場(%s)の中。止める**" % name)

    def guard(self, doc):
        if doc in self.tuning:
            raise Stop("**調整用の docID が渡された。文・ZIP・DB の応答のどの file も開かずに止める(評価用だけを測る)**")
        if doc not in self.eval_ids:
            raise Stop("**W の記録の区分が評価用でない docID が渡された。止める**")

    def read_report(self, doc):
        self.guard(doc)
        b = read_bytes(os.path.join(self.reports_dir, doc + ".txt"))
        if sha256_hex(b) != self.report_sha[doc]:                      # (c) 文を開いた直後
            raise Stop("**文の sha256 が W の記録と違う: %s。止める**" % doc)
        return b.decode("utf-8"), b

    def read_db(self, doc):
        self.guard(doc)
        out = {}
        for kind in ("financials", "companies", "ratios"):
            b = read_bytes(os.path.join(self.db_dir, doc, kind + ".json"))
            if self.db_sha.get((doc, kind)) != sha256_hex(b):
                raise Stop("**DB の応答の sha256 が取得の記録と違う: %s %s。止める**" % (doc, kind))
            out[kind] = b
        return out

    def load_materials(self, db=True):
        """文・ZIP(・DB の応答)を 10 書類の全部について読み、sha256 を照らす。違えばその場で止める(まだ何も書いていない)。"""
        mats = dict((d, {}) for d in self.docs)
        for d in self.docs:
            mats[d]["text"], mats[d]["text_bytes"] = self.read_report(d)
        for d in self.docs:
            mats[d]["zip"] = self.read_zip(d)
        if db:
            for d in self.docs:
                mats[d]["db"] = self.read_db(d)
        return mats


# ======================================================================================================
# engine への入口(試験・dry-run は StubBackend4)
class RealBackend4(T.RealBackend):
    """段 1 の ``RealBackend`` に、P27・P27E の provenance を数える ``rule_counts`` を足す。"""

    def rule_counts(self, zb, text):
        """``build_raw_claims`` を ``verify_document`` と同じ入力(文を差し込んだ ZIP)で呼んで数える(V-6)。97 書類の script の関数を使う。"""
        modified, _element, _member = R97.VD.PR.build_modified_zip(zb, text)
        return R97.rule_counts(modified, PROFILES)


class StubBackend4(T.StubBackend):
    """作り物。P22・P26 は段 1 の ``StubBackend``。P27: 数の前 8 字に「来期」が在る claim を UNVERIFIABLE(target_or_plan)にする(C3 の真似)。
    P27E: P27 の no_same_value の行で、最も近い当期の fact との差が 15% 以内なら名指して VALUE_MISMATCH にする(B の真似)。"""
    name = "stub"
    FUTURE_MARK = "来期"
    RHO = 0.15

    def verify(self, zb, profile, text):
        out = T.StubBackend.verify(self, zb, "P22" if profile == "P22" else "P26", text)
        out["profile"] = profile
        if profile in ("P22", "P26"):
            return out
        facts = self._facts(zb)
        for c in out["claims"]:
            if self.FUTURE_MARK in (c.get("span") or ""):
                c.update(state="UNVERIFIABLE", reason="target_or_plan", pointers=[], recomputed=None)
            elif profile == "P27E" and c["state"] == "POINTER_NOT_FOUND" and c["reason"] == T.NO_SAME_VALUE and facts:
                near = min(facts, key=lambda f: abs(float(f["value"]) - c["value"]))
                if float(near["value"]) and abs(abs(float(near["value"])) - abs(c["value"])) <= self.RHO * abs(float(near["value"])):
                    c.update(state="VALUE_MISMATCH", reason=None, pointers=["xbrl:%s@%s" % (near["name"], near["context"])], recomputed=float(near["value"]))
        return out

    def rule_counts(self, zb, text):
        c27 = self.verify(zb, "P27", text)["claims"]
        n27 = dict((c["id"], c) for c in c27)
        b = sum(1 for c in self.verify(zb, "P27E", text)["claims"] if c["state"] == "VALUE_MISMATCH" and n27[c["id"]]["state"] != "VALUE_MISMATCH")
        base = {RULE_KEYS[0]: text.count("当たり"), RULE_KEYS[1]: sum(1 for c in c27 if c["reason"] == "target_or_plan"),
                RULE_KEYS[2]: text.count("株当たり"), RULE_KEYS[3]: 0}
        return {"P27": dict(base, **{RULE_KEYS[4]: 0}), "P27E": dict(base, **{RULE_KEYS[4]: b})}


# ======================================================================================================
# 記録の頭
def header(ctx, step, git, dry_run, backend, before, after):
    if before != after:
        raise Stop("**既存の cache か ZIP の folder の件数か名前が変わった。記録を書かずに止める**")
    here = os.path.abspath(__file__)
    return {"seal": SEAL, "step": step, "dry_run": bool(dry_run), "backend": backend.name,
            "HEAD の commit": git["HEAD"], "W の commit": git["W"], "T の commit": git["T"],
            "S2 の commit": git["S2"], "E の commit": git["E"],
            "走る前の確かめ": {"封の file は HEAD で追跡され作業木と同じ": True, "W ⊑ S2": True, "S2 ⊏ E": True, "E ⊑ HEAD": True,
                          "E と HEAD の間で adapters・core に差が無い": True, "profile の一覧": list(PROFILES), "既定の profile": "P26"},
            "この script の sha256": sha256_hex(read_bytes(here)),
            "段 1 の測定の script(読むだけ・1 字も変えない)の sha256": sha256_hex(read_bytes(os.path.join(HERE, "xbrl_p27_tune_2026-10-27.py"))),
            "97 書類の測定の script(rule_counts を読むだけ・1 字も変えない)の sha256": sha256_hex(read_bytes(os.path.join(HERE, "xbrl_p27_regress97_2026-10-27.py"))),
            "対象の docID": list(ctx.docs), "対象は評価用の全部": list(ctx.docs) == list(ctx.eval_list), "評価用の件数": len(ctx.eval_list),
            "使った文の sha256": dict((d, ctx.report_sha[d]) for d in ctx.docs),
            "engine の指紋": backend.fingerprint(),
            "cache の前後": {"前": before, "後": after, "変化なし": before == after}}


def _places(root, out, rel, outside_dir, zip_dir, cache_root, existing_dir, reports_dir, db_dir, dry_run):
    base = DB.default_cache_base() if dry_run is False else None
    zip_dir = zip_dir or (DB.default_zip_dir() if base else None)
    cache_root = cache_root or (DB.default_cache_root() if base else None)
    existing_dir = existing_dir or (DB.default_existing_cache_dir() if base else None)
    outside_dir = outside_dir or (os.path.join(cache_root, OUTSIDE_NAME) if cache_root else None)
    if None in (zip_dir, cache_root, existing_dir, outside_dir):
        raise Stop("**--dry-run では置き場を全部明示する。止める**")
    if dry_run and out is None:
        raise Stop("**--dry-run では --out を明示する(作り物の記録を本物の path に書かない)。止める**")
    return os.path.join(root, rel) if out is None else out, outside_dir, zip_dir, cache_root, existing_dir


def _git(git_run, git_dir, root):
    return git_run or git_runner(git_dir or os.path.dirname(os.path.abspath(root)))


# ======================================================================================================
# 判定(4 profile)
def pair_claims(outs):
    """4 profile の claim を id で対にする。(id の並び, profile ごとの {id: claim}, P22 に無い/P22 だけに在る id, 値・span・単位が P22 と違う id)。
    同じ profile の中で id が重複していれば止める(多対一にしない)。"""
    per = {}
    for p in PROFILES:
        ids = [c["id"] for c in outs[p]["claims"]]
        if len(set(ids)) != len(ids):
            raise Stop("**同じ profile の中で claim の id が重複している(%s)。止める**" % p)
        per[p] = dict((c["id"], c) for c in outs[p]["claims"])
    ids = [c["id"] for c in outs["P22"]["claims"]]
    for p in PROFILES[1:]:
        ids += [i for i in (c["id"] for c in outs[p]["claims"]) if i not in set(ids)]
    key = lambda c: (c["value"], c["span"], c["unit"])                       # noqa: E731
    only = dict((p, sorted(set(per["P22"]) ^ set(per[p]))) for p in PROFILES[1:])
    differ = dict((p, [i for i in ids if i in per["P22"] and i in per[p] and key(per["P22"][i]) != key(per[p][i])]) for p in PROFILES[1:])
    return ids, per, only, differ


def _state(c):
    return None if c is None else c["state"]


def read_row_conditions(claims):
    """封 §7 の読む行 = (P27E で VALUE_MISMATCH かつ P26 で VALUE_MISMATCH でない)∪(P26 で GROUNDED かつ P27 で GROUNDED でない)。
    ``claims`` は profile → claim(無ければ None)。該当した条件の名前の一覧(空なら読まない)。"""
    conds = []
    if _state(claims.get("P27E")) == "VALUE_MISMATCH" and _state(claims.get("P26")) != "VALUE_MISMATCH":
        conds.append(COND_K3)
    if _state(claims.get("P26")) == "GROUNDED" and _state(claims.get("P27")) != "GROUNDED":
        conds.append(COND_K4)
    return conds


def render_dossier4(doc, style, claim_id, paragraph, note, claims, facts, db):
    """段 1 の ``render_dossier``(P22・P26 の欄)の出力に、P26 の欄の後ろへ P27・P27E の欄を、字を固定した定数で差し込む。
    P27・P27E だけが名指した pointers の fact は、節 3 の後ろに足す。差し込みを除くと段 1 の出力と byte 一致する。"""
    base = render_dossier(doc, style, claim_id, paragraph, note, claims.get("P22"), claims.get("P26"), facts, db)
    i3, i4 = base.find(DOSSIER_MARK3), base.find(DOSSIER_MARK4)
    if i3 < 0 or i4 < i3:
        raise Stop("**段 1 の束の節の頭が見つからない。止める**")
    block = "".join(DOSSIER_P27_BLOCK.format(profile=p, body=T.dumps(claims[p]).rstrip("\n") if claims.get(p) is not None else DOSSIER_NO_CLAIM)
                    for p in DOSSIER_P27_PROFILES)
    seen = set(x for p in BASE_PROFILES for x in ((claims.get(p) or {}).get("pointers") or []))
    extra = []
    for p in DOSSIER_P27_PROFILES:
        for x in (claims.get(p) or {}).get("pointers") or []:
            if x not in seen and x not in extra:
                extra.append(x)
    tail = (DOSSIER_P27_FACTS_HEAD + "\n" + "\n".join(T.fact_lines(facts, extra)) + "\n\n") if extra else ""
    return base[:i3] + block + base[i3:i4] + tail + base[i4:]


def judge_summary(rows, per_doc, read_rows):
    n = dict((p, sum(1 for r in rows if r[p] is not None)) for p in PROFILES)
    st = dict((p, dict((s, sum(1 for r in rows if _state(r[p]) == s)) for s in STATES)) for p in PROFILES)
    out = {"claim": n, "state の数": st, "VALUE_MISMATCH の率": dict((p, frac(st[p]["VALUE_MISMATCH"], n[p])) for p in PROFILES)}
    out["P27E の VALUE_MISMATCH の行 − P27 の VALUE_MISMATCH の行"] = st["P27E"]["VALUE_MISMATCH"] - st["P27"]["VALUE_MISMATCH"]
    out["P26 → P27 で GROUNDED を離れた行"] = sum(1 for r in rows if _state(r["P26"]) == "GROUNDED" and _state(r["P27"]) != "GROUNDED")
    out["P26 → P27 で新しい GROUNDED"] = sum(1 for r in rows if _state(r["P27"]) == "GROUNDED" and _state(r["P26"]) != "GROUNDED")
    out["P26 → P27 で VALUE_MISMATCH に入る行"] = sum(1 for r in rows if _state(r["P27"]) == "VALUE_MISMATCH" and _state(r["P26"]) != "VALUE_MISMATCH")
    out["P27 → P27E で state が動いた行"] = sum(1 for r in rows if _state(r["P27E"]) != _state(r["P27"]))
    out["P27 と P27E で GROUNDED の行が同じ"] = all((_state(r["P27"]) == "GROUNDED") == (_state(r["P27E"]) == "GROUNDED") for r in rows)
    out["P27E で VALUE_MISMATCH かつ P26 で VALUE_MISMATCH でない行"] = sum(1 for r in rows if COND_K3 in read_row_conditions(dict((p, r[p]) for p in PROFILES)))
    v6 = {"C2 で止めた claim(P27)": sum(d["規則ごと(build_raw_claims の provenance)"]["P27"][RULE_KEYS[0]] for d in per_doc),
          "C3 で target_or_plan にした claim(P27)": sum(d["規則ごと(build_raw_claims の provenance)"]["P27"][RULE_KEYS[1]] for d in per_doc),
          "C1 で other_concept になった行(P27)": sum(d["規則ごと(build_raw_claims の provenance)"]["P27"][RULE_KEYS[3]] for d in per_doc),
          "B で名指した行(P27E の無改変)": sum(d["規則ごと(build_raw_claims の provenance)"]["P27E"][RULE_KEYS[4]] for d in per_doc)}
    out["規則ごとに当たった claim(V-6。build_raw_claims の provenance)"] = v6
    conds = collections.Counter(c for r in read_rows for c in r["条件"])
    out["読む行"] = {"数": len(read_rows), "条件ごと(重なる)": dict((c, conds.get(c, 0)) for c in CONDITIONS)}
    return out


def run_judge(root=DEFAULT_ROOT, docs=None, out=None, outside_dir=None, backend=None, dry_run=False, zip_dir=None, cache_root=None,
              existing_dir=None, reports_dir=None, db_dir=None, git_dir=None, git_run=None, vocab=None, key_value=None, say=print):
    """封 §7。4 profile の判定・読む行・dossier。"""
    T.PROFILES = PROFILES
    out, outside_dir, zip_dir, cache_root, existing_dir = _places(root, out, JUDGE_REL, outside_dir, zip_dir, cache_root, existing_dir, reports_dir, db_dir, dry_run)
    ctx = EvalCtx(root, zip_dir, cache_root, existing_dir, outside_dir, None, docs, reports_dir, db_dir)       # 調整用・区分の外はここで止まる
    git = preflight(_git(git_run, git_dir, root), vocab)                                                       # (a)(b)。文はまだ 1 つも開いていない
    if os.path.exists(out):
        raise Stop("**出力が既に在る: %s。止める**" % os.path.basename(out))
    backend = backend or RealBackend4()
    before = T.cache_snapshot(ctx)
    mats = ctx.load_materials(db=True)                                                                         # (c) 10 本の sha256 を全部照らす

    per_doc, rows, read_rows, full, blobs = [], [], [], {}, {}
    for doc in ctx.docs:
        text, zb = mats[doc]["text"], mats[doc]["zip"]
        outs = dict((p, backend.verify(zb, p, text)) for p in PROFILES)
        rules = backend.rule_counts(zb, text)
        if set(rules) != set(RULE_PROFILES) or any(set(rules[p]) != set(RULE_KEYS) for p in rules):
            raise Stop("**規則ごとの数の欄が封の形でない。止める**")
        ids, per, only, differ = pair_claims(outs)
        full[doc] = {"claims": dict((p, outs[p]["claims"]) for p in PROFILES), "規則ごと": rules}
        states = dict((p, collections.Counter(c["state"] for c in outs[p]["claims"])) for p in PROFILES)
        per_doc.append({"docID": doc, "型": ctx.styles[doc], "文の sha256": ctx.report_sha[doc],
                        "claim の数": dict((p, len(outs[p]["claims"])) for p in PROFILES),
                        "state の数": dict((p, dict((s, states[p].get(s, 0)) for s in STATES)) for p in PROFILES),
                        "片方の profile にしか無い id": only, "値・span・単位が profile 間で違う id": differ,
                        "規則ごと(build_raw_claims の provenance)": rules})
        facts = None
        for cid in ids:
            claims = dict((p, per[p].get(cid)) for p in PROFILES)
            rows.append(dict([("docID", doc), ("id", cid)] + [(p, None if claims[p] is None else claim_record(claims[p])) for p in PROFILES]))
            conds = read_row_conditions(claims)
            if not conds:
                continue
            read_rows.append({"行": "%s:%s" % (doc, cid), "docID": doc, "id": cid, "条件": conds})
            facts = backend.facts(zb) if facts is None else facts
            first = [claims[p] for p in PROFILES if claims[p] is not None][0]
            paragraph, note = T.paragraph_of(text, first.get("span"))
            blobs["%s__%s.txt" % (doc, cid)] = render_dossier4(doc, ctx.styles[doc], cid, paragraph, note, claims, facts, mats[doc]["db"]).encode("utf-8")
        say("  %s %s claim %s" % (doc, ctx.styles[doc], " / ".join("%d(%s)" % (len(outs[p]["claims"]), p) for p in PROFILES)))

    full_blob = dumps({"docs": full}).encode("utf-8")
    index = [{"行": r["行"], "file": "%s__%s.txt" % (r["docID"], r["id"]), "bytes": len(blobs["%s__%s.txt" % (r["docID"], r["id"])]),
              "sha256": sha256_hex(blobs["%s__%s.txt" % (r["docID"], r["id"])])} for r in read_rows]
    index_blob = dumps({"rows": index}).encode("utf-8")
    reader_blob = PR.READER_PROMPT.encode("utf-8")
    rec = header(ctx, "P27 段 2 §7 ― 評価用の判定(P22・P26・P27・P27E)・読む行・dossier", git, dry_run, backend, before, T.cache_snapshot(ctx))
    rec["claim の対の付け方"] = "id で対にする。同じ profile の中の id の重複は止める。P22 に無い id・P22 にだけ在る id と、値・span・単位が P22 と違う id は profile ごと・会社ごとに記録する"
    rec["会社"] = per_doc
    rec["claim"] = rows
    rec["集計"] = judge_summary(rows, per_doc, read_rows)
    rec["読む行"] = read_rows
    rec["束の P27・P27E の欄を足す形(script の定数)"] = {"DOSSIER_P27_BLOCK": DOSSIER_P27_BLOCK, "DOSSIER_NO_CLAIM": DOSSIER_NO_CLAIM,
                                              "DOSSIER_P27_FACTS_HEAD": DOSSIER_P27_FACTS_HEAD, "profile": list(DOSSIER_P27_PROFILES)}
    rec["repo の外に置いたもの"] = {
        "folder": DB.display_path(outside_dir),
        "全部の欄(span・subject・value・recomputed を含む)": {"file": "judge_full.json", "sha256": sha256_hex(full_blob), "bytes": len(full_blob)},
        "dossier": {"folder": "dossier/", "件数": len(index), "index.json の sha256": sha256_hex(index_blob),
                    "各 file の sha256": dict((x["行"], x["sha256"]) for x in index),
                    "読み手の指示文 reader_prompt.txt の sha256": sha256_hex(reader_blob),
                    "読み手の指示文は封 §5-6 の字(prompts の READER_PROMPT)と同じ": reader_blob.decode("utf-8") == PR.READER_PROMPT}}
    rec["限界"] = ["読みはエージェントの読みで人間の読みではない(この記録は読む行を選ぶだけ。読みは reconcile の記録)",
                 "span・subject・value・recomputed は repo の外。claim の対は id で付け、値・span・単位の食い違いは会社ごとに数えた"]
    T.assert_record_clean(rec, key_value)                                                                      # 外の file を置く前に、記録が通ることを確かめる
    dossier_dir = os.path.join(outside_dir, "dossier")
    targets = [os.path.join(outside_dir, "judge_full.json")] + [os.path.join(dossier_dir, n) for n in list(blobs) + ["index.json", "reader_prompt.txt"]]
    if any(os.path.exists(t) for t in targets):
        raise Stop("**外の置き場に file が既に在る。止める**")
    write_new(targets[0], full_blob.decode("utf-8"))
    for name, blob in blobs.items():
        write_new(os.path.join(dossier_dir, name), blob.decode("utf-8"))
    write_new(os.path.join(dossier_dir, "index.json"), index_blob.decode("utf-8"))
    write_new(os.path.join(dossier_dir, "reader_prompt.txt"), reader_blob.decode("utf-8"))
    write_record(out, rec, key_value)
    say("-> %s(読む行 %d)" % (out, len(read_rows)))
    return rec


# ======================================================================================================
# 読みの合わせ(2 席)
def readings_summary(rows):
    n = len(rows)
    agree = sum(1 for r in rows if r["席1"]["側"] == r["席2"]["側"])
    side = lambda sel: collections.Counter(r["合わせた"]["側"] for r in sel)        # noqa: E731
    tool = [r for r in rows if r["合わせた"]["側"] == "道具" and r["合わせた"]["細目"] != T.UNSURE]
    det = collections.Counter(r["合わせた"]["細目"] for r in tool)
    n_b = sum(det.get(k, 0) for k in ("道1", "道2", "道3", "道4"))
    out = {"読む行": n, "2 席の側が一致した行": frac(agree, n),
           "合わせた側の内訳": dict((s, side(rows).get(s, 0)) for s in T.SIDES),
           "合わせた側が道具の行": sum(1 for r in rows if r["合わせた"]["側"] == "道具"),
           "合わせた細目が付いた道具の行": {"行": len(tool), "細目の内訳": dict(sorted(det.items())),
                                    "道1〜道4": frac(n_b, len(tool)), "道5": frac(det.get("道5", 0), len(tool))},
           "合わせた札が文2の行": sum(1 for r in rows if r["合わせた"]["側"] == "文" and r["合わせた"]["細目"] == "文2")}
    by = {}
    for c in CONDITIONS:
        sel = [r for r in rows if c in r["条件"]]
        by[c] = {"行": len(sel), "合わせた側の内訳": dict((s, side(sel).get(s, 0)) for s in T.SIDES),
                 "合わせた側が道具の行": sum(1 for r in sel if r["合わせた"]["側"] == "道具")}
    out["条件ごと(重なる)"] = by
    return out


def run_reconcile(root=DEFAULT_ROOT, seat_a=None, seat_b=None, judge_record=None, out=None, outside_dir=None, backend=None, dry_run=False,
                  zip_dir=None, cache_root=None, existing_dir=None, reports_dir=None, db_dir=None, git_dir=None, git_run=None, vocab=None,
                  key_value=None, say=print):
    """札の file の検査(``load_seat``)・合わせ方(``combine``)は段 1 のまま。記録の頭と集計は 4 profile・条件ごと。"""
    out, outside_dir, zip_dir, cache_root, existing_dir = _places(root, out, READINGS_REL, outside_dir, zip_dir, cache_root, existing_dir, reports_dir, db_dir, dry_run)
    judge_record = judge_record or os.path.join(root, JUDGE_REL)
    if not seat_a or not seat_b:
        raise Stop("**2 席の札の file が足りない。止める**")
    ctx = EvalCtx(root, zip_dir, cache_root, existing_dir, outside_dir, None, None, reports_dir, db_dir)
    git = preflight(_git(git_run, git_dir, root), vocab)
    if os.path.exists(out):
        raise Stop("**出力が既に在る: %s。止める**" % os.path.basename(out))
    backend = backend or T.NullBackend()
    before = T.cache_snapshot(ctx)
    jr = read_json(judge_record)
    want = [r["行"] for r in jr["読む行"]]
    name_a, la, sha_a = load_seat(seat_a, want)
    name_b, lb, sha_b = load_seat(seat_b, want)
    rows, free = [], {"席1": {}, "席2": {}}
    for r in jr["読む行"]:
        k = r["行"]
        (sa, da, shape_a, why_a), (sb, db, shape_b, why_b) = la[k], lb[k]
        side, det = combine((sa, da), (sb, db))
        rows.append({"行": k, "docID": r["docID"], "id": r["id"], "条件": list(r["条件"]), "席1": {"側": sa, "細目": da}, "席2": {"側": sb, "細目": db},
                     "合わせた": {"側": side, "細目": det}})
        free["席1"][k] = {"理由": why_a, "道5の形": shape_a}
        free["席2"][k] = {"理由": why_b, "道5の形": shape_b}
    free_blob = dumps(free).encode("utf-8")
    rec = header(ctx, "P27 段 2 §7 ― 評価用の読みの合わせ(2 席・人の目なし)", git, dry_run, backend, before, T.cache_snapshot(ctx))
    rec["読みは"] = "エージェントの読み(2 席。互いの読みを見ない)で、人間の読みではない"
    rec["合わせ方(段 1 の封 §5-5)"] = "側が割れたら 分からない(細目なし)。側が同じで細目が割れたら 側はその側・細目は 分からない"
    rec["入力"] = {"判定の記録": os.path.relpath(judge_record, root) if T.inside(judge_record, root) else "(repo の外)",
                 "判定の記録の sha256": sha256_hex(read_bytes(judge_record)),
                 "席1 の札の file の sha256": sha_a, "席2 の札の file の sha256": sha_b}
    rec["行"] = rows
    rec["集計"] = readings_summary(rows)
    rec["repo の外に置いたもの"] = {"folder": DB.display_path(outside_dir),
                              "道5 の形と各席の理由の文": {"file": "readings_free_text.json", "sha256": sha256_hex(free_blob), "bytes": len(free_blob)}}
    T.assert_record_clean(rec, key_value)
    write_new(os.path.join(outside_dir, "readings_free_text.json"), free_blob.decode("utf-8"))
    write_record(out, rec, key_value)
    say("-> %s(読む行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
# 注入(段 1 の関数をそのまま使う。profile だけ 4 つ)
def run_inject(root=DEFAULT_ROOT, docs=None, out=None, outside_dir=None, backend=None, dry_run=False, zip_dir=None, cache_root=None,
               existing_dir=None, reports_dir=None, db_dir=None, work_root=None, git_dir=None, git_run=None, vocab=None, procs=1,
               seed_fn=None, cap=INJECT_CAP, key_value=None, say=print):
    T.PROFILES = PROFILES
    out, outside_dir, zip_dir, cache_root, existing_dir = _places(root, out, INJECT_REL, outside_dir, zip_dir, cache_root, existing_dir, reports_dir, db_dir, dry_run)
    ctx = EvalCtx(root, zip_dir, cache_root, existing_dir, outside_dir, work_root, docs, reports_dir, db_dir)
    git = preflight(_git(git_run, git_dir, root), vocab)
    if os.path.exists(out):
        raise Stop("**出力が既に在る: %s。止める**" % os.path.basename(out))
    inject_full = os.path.join(outside_dir, "inject_full.json")
    if os.path.exists(inject_full):
        raise Stop("**外の置き場に file が既に在る。止める**")
    if work_root is None:
        work_root = tempfile.mkdtemp(prefix="p27_eval_", dir=os.environ.get("TMPDIR"))
        for prot in (existing_dir, zip_dir):
            if T.inside(work_root, prot):
                raise Stop("**作業 folder が既存の cache か ZIP の folder の中。止める**")
    backend = backend or RealBackend4()
    seed, seed_meta = (seed_fn or (lambda path: T.IJ.verify_seed_sealed(path)))(T.SEED_FILE)      # git に追跡され内容が一致していなければ止まる
    before = T.cache_snapshot(ctx)
    ctx.load_materials(db=False)                                                                    # (c) 文の sha256・ZIP の sha256 を 10 書類の全部で先に照らす
    T._STATE.update(ctx=ctx, backend=backend, seed=seed, work=work_root, cap=cap)
    if procs > 1:
        results = T.run_parallel(ctx.docs, procs)
    else:
        results = dict((d, T._inject_worker(d)) for d in ctx.docs)
    rows, full, per_doc = [], [], {}
    for d in ctx.docs:
        r, f, c = results[d]
        rows += r
        full += f
        per_doc[d] = c
        say("  %s 注入 %d 件" % (d, len(r)))
    full_blob = dumps({"seed 以外の注入の字": full}).encode("utf-8")
    rec = header(ctx, "P27 段 2 §7 ― 評価用の注入(T1_VALUE・T8_REL。4 profile)", git, dry_run, backend, before, T.cache_snapshot(ctx))
    rec["種"] = {"file": "measure/SEED.json", "sealed_in_commit": seed_meta.get("sealed_in_commit"), "seed_file_sha256": seed_meta.get("seed_file_sha256")}
    rec["型"] = {"T1_VALUE": "inject.select(types=[T1_VALUE]) のまま", "T8_REL": "円の単位族の token・r ∈ %s・%d 回まで" % (list(T.T8_R_VALUES), T.T8_TRIES),
               "上限": "型ごと・1 書類あたり %d 件" % cap, "土台": "無改変で P22 と P26 の両方が GROUNDED(段 1 と同じ)。分類の土台は各 profile の同じ id の無改変の claim",
               "率の分母": "4 profile の全部で対応が付く注入の行(封 §3-2)"}
    adopted = sum(per_doc[d][t].get("採った", 0) for d in per_doc for t in INJECT_TYPES)
    rec["round-trip"] = {"確かめた注入の数": adopted, "注入した字を元に戻すと無改変の文と byte 一致": True,
                       "確かめ方": "段 1 の inject_doc が採った注入の 1 件ずつに IJ.apply_edits → IJ.revert の結果が無改変の文と同じかを見て、違えば Stop(記録は書かれない)"}
    rec["書類別の数え"] = per_doc
    rec["注入の行の数"] = len(rows)
    rec["集計(各 profile で対応が付く行が分母)"] = T.inject_summary(rows)
    all4 = [r for r in rows if all(r[p]["対応"] for p in PROFILES)]
    rec["集計(4 profile の全部で対応が付く行が分母。V-1〜V-3)"] = T.inject_summary(all4)
    rec["4 profile の全部で対応が付く行"] = dict((t, sum(1 for r in all4 if r["型"] == t)) for t in INJECT_TYPES)
    rec["T8_REL の site"] = {"注入の行": sum(1 for r in rows if r["型"] == "T8_REL"),
                          "作れる site(上限の前)": sum(per_doc[d]["T8_REL"].get("作れる site", 0) for d in per_doc)}
    rec["行"] = rows
    rec["repo の外に置いたもの"] = {"folder": DB.display_path(outside_dir),
                              "注入の字・新しい値": {"file": "inject_full.json", "sha256": sha256_hex(full_blob), "bytes": len(full_blob)}}
    rec["限界"] = ["注入は 2 型だけ。DB と原本の差の実際の分布ではない(T8_REL の r の 4 値は 3 本の差の大きさに寄せた決め打ち)",
                 "ρ = 0.15 は T8_REL の変え幅(±10%)を包むように決めたので、同じ T8_REL で測る P27E の『名指す率』は作りから当たりやすい(封 §10-2)",
                 "T1_VALUE の cap は inject.select の採用に掛け(基準で絞る前)、T8_REL の cap は site に掛けた"]
    T.assert_record_clean(rec, key_value)
    write_new(inject_full, full_blob.decode("utf-8"))
    write_record(out, rec, key_value)
    say("-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("judge", "reconcile", "inject"))
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--git-dir", default=None, help="走る前の確かめの git の folder(既定: --root の親 = repo の最上位)")
    ap.add_argument("--docs", default=None, help="コンマ区切り(既定: 評価用の全部)。調整用・区分の外は止める")
    ap.add_argument("--out", default=None)
    ap.add_argument("--outside-dir", default=None, help="既定: <cache-root>/eval(~/.cache/audit-core/edinetdb-p27/eval/)")
    ap.add_argument("--zip-dir", default=None)
    ap.add_argument("--cache-root", default=None)
    ap.add_argument("--reports-dir", default=None, help="評価用の文の置き場(既定: <cache-root>/reports)")
    ap.add_argument("--db-dir", default=None, help="DB の応答の置き場 <db-dir>/<docID>/*.json(既定: <cache-root>)")
    ap.add_argument("--existing-cache-dir", default=None)
    ap.add_argument("--work-dir", default=None, help="prepare_xbrl の作業 folder の親(既定: TMPDIR の下に作る)")
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--seat-a", default=None)
    ap.add_argument("--seat-b", default=None)
    ap.add_argument("--judge-record", default=None)
    ap.add_argument("--dry-run", action="store_true", help="engine と ZIP の中身を作り物にして同じ経路を通す。--out と置き場を全部明示する")
    a = ap.parse_args(argv)
    docs = a.docs.split(",") if a.docs else None
    common = dict(root=a.root, out=a.out, outside_dir=a.outside_dir, zip_dir=a.zip_dir, cache_root=a.cache_root, existing_dir=a.existing_cache_dir,
                  reports_dir=a.reports_dir, db_dir=a.db_dir, git_dir=a.git_dir, dry_run=a.dry_run)
    backend = StubBackend4() if a.dry_run else None
    if a.cmd == "reconcile":
        run_reconcile(seat_a=a.seat_a, seat_b=a.seat_b, judge_record=a.judge_record, backend=None, **common)
    elif a.cmd == "judge":
        run_judge(docs=docs, backend=backend, **common)
    else:
        run_inject(docs=docs, backend=backend, work_root=a.work_dir, procs=a.procs, **common)


if __name__ == "__main__":
    main()
