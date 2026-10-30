# -*- coding: utf-8 -*-
u"""(d)・P・U を製品の経路へ + 軸の保持 (e) ― 封 F-1〜F-12 の実測を 1 本の記録に書く。

封 `docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md`(commit `ae528a4`)。
記録 `fixtures/xbrl/cd8/holds_product_path_2026-10-19.json`(``--write`` のときだけ書く)。

測るもの(封 §3 の記号):
  F-1  core/py の差分(封の commit との diff の行数)
  F-2  instance.py の差分(numstat: 足した行・消した行)と engine 側の試験(変異を除く)の緑
  F-3  8 書類で枠の axes が members と 1:1 か(違反の枠数)
  F-4  192 行の再現(記録 period_unit_hold_2026-10-19.json の「合成の後」と一致した行数)
  F-5  (d) の 6 行の hold_axes の分類
  F-6  対照(期間・単位・次元の注入を 1 件ずつ)
  F-7  verify_document --doc S100YXMA の出力と実装前の保存(--baseline)の差(欄の名)
  F-8  新しい CLI を 2 回走らせた sha256
  F-9  変異 HOLD-R1〜R3 の赤・既存 89 本の行が封の commit と同じか
  F-10 保護面の本数(封の commit の実測 / 字で留めた値 / いま)
  F-11 run_tests.sh の rc(--run-tests-log を読む)
  F-12 独立監査の判定(--audit-verdict / --audit-revise。人が写す。出どころも書く)

engine は触らない。通信しない。0 USD。材料は手元のキャッシュ(~/.cache/audit-core/edinet)。

    cd audit-core
    python3 measure/xbrl_holds_product_path_2026-10-19.py \\
        --baseline <実装前の vd_S100YXMA.json> --run-tests-log <run_tests の log> \\
        --audit-verdict GO --audit-revise 0 --audit-source <監査の出どころ> --write
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                    # audit-core/
REPO = os.path.dirname(ROOT)                    # repo の根(保護面は repo 相対で数える)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

import audit_core as core  # noqa: E402

from adapters.xbrl import edinet as ED  # noqa: E402
from adapters.xbrl import holds as H  # noqa: E402
from adapters.xbrl import instance as I  # noqa: E402
from adapters.xbrl import registry_setup as RS  # noqa: E402
from adapters.xbrl import verify_external as VE  # noqa: E402

SEAL = "docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md"
SEAL_COMMIT = "ae528a4"
CD8 = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
REC_PU = os.path.join(CD8, "period_unit_hold_2026-10-19.json")
DIAG = os.path.join(CD8, "dim_diag_2026-10-17.json")
DRAW = os.path.join(CD8, "draw_2026-10-17.json")
OUT = os.path.join(CD8, "holds_product_path_2026-10-19.json")
BASELINE_DOC = "S100YXMA"
BASELINE_SHA_PREFIX = "2c2af15a"              # 封 §2
ENV = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "core", "py") + os.pathsep + ROOT)


def _load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _git(args, cwd=ROOT):
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("git %s: %s" % (" ".join(args), r.stderr))
    return r.stdout


def _sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- F-1 / F-2
def f1_core_diff():
    return len(_git(["diff", SEAL_COMMIT, "--", "core"]).splitlines())


def f2_instance_numstat():
    out = _git(["diff", "--numstat", SEAL_COMMIT, "--", "adapters/xbrl/instance.py"]).split()
    diff = _git(["diff", SEAL_COMMIT, "--", "adapters/xbrl/instance.py"]).splitlines()
    removed = [l[1:] for l in diff if l.startswith("-") and not l.startswith("---")]
    added = [l[1:] for l in diff if l.startswith("+") and not l.startswith("+++")]
    is_code = lambda s: s.strip() and not s.strip().startswith("#") and '"""' not in s
    if not out:
        return {"added": 0, "deleted": 0, u"消した行の中身": [], u"消したコード行": 0}
    return {"added": int(out[0]), "deleted": int(out[1]), u"消した行の中身": removed,
            u"消したコード行": sum(1 for s in removed if is_code(s)),
            u"足したコード行": sum(1 for s in added if is_code(s))}


def f2_engine_pytest(skip):
    """engine 側の試験(変異を除く)。``-q`` の末尾の行を記録する。"""
    if skip:
        return {"ran": False}
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                        "tests/adapters", "tests/golden", "tests/core",
                        "--ignore=tests/adapters/xbrl/test_mutations.py"],
                       cwd=ROOT, capture_output=True, text=True, env=ENV)
    tail = [l for l in r.stdout.splitlines() if "passed" in l or "failed" in l][-1:]
    m = re.search(r"(\d+) passed", tail[0]) if tail else None
    f = re.search(r"(\d+) failed", tail[0]) if tail else None
    return {"ran": True, "rc": r.returncode, "summary": tail[0] if tail else r.stdout[-300:],
            "passed": int(m.group(1)) if m else None, "failed": int(f.group(1)) if f else 0}


# ---------------------------------------------------------------- F-3
def f3_axes(docs):
    total, with_members, bad = 0, 0, []
    for d in docs:
        inst = I.load_instance(io.open(ED.cache_path(d), "rb").read())
        for cid, c in inst["contexts"].items():
            total += 1
            with_members += bool(c["members"])
            ok = (len(c["axes"]) == len(c["members"]) and [m for _a, m in c["axes"]] == c["members"]
                  and all(a for a, _m in c["axes"]))
            if not ok:
                bad.append([d, cid])
    return {u"書類": len(docs), u"枠": total, u"members を持つ枠": with_members,
            u"**違反**": len(bad), u"違反の明細": bad[:20]}


# ---------------------------------------------------------------- F-4 / F-5 / F-6
def _material_rows(docs, AT):
    """``tests/adapters/xbrl/test_verify_external.py`` と同じ材料の組み立て(注入後の 8 書類)。"""
    A1, MB, IJ, PR = AT.A1, AT.MB, AT.IJ, AT.PR
    seed, _m = IJ.verify_seed_sealed(MB.SEED_FILE)
    swap = _load(os.path.join(CD8, "role_swap_2026-10-17.json"))
    b_by = {(x[u"doc"], x[u"id"]): x for x in swap["rows"]}
    for doc in docs:
        zb = io.open(ED.cache_path(doc), "rb").read()
        old, A1.TMP = A1.TMP, MB.TMP
        try:
            text, refs = A1.material(doc)
        finally:
            A1.TMP = old
        chosen, _c = MB.pick_injections(text, refs, seed, doc)
        tampered, pl = IJ.apply_edits(text, chosen)
        mrows, _n = MB.build_rows(tampered, chosen, pl)
        zb2, _e, _mm = PR.build_modified_zip(zb, tampered)
        yield doc, I.load_instance(zb2), mrows, b_by


def f4_f5_f6(docs):
    AT = _mod("measure/xbrl_attr_inject_2026-10-17.py", "attr_for_hpp_measure")
    A1 = AT.A1
    rec_rows = {(x[u"doc"], x[u"id"]): x for x in _load(REC_PU)["rows"]}
    diag = {(x[u"doc"], x[u"id"]): x for x in _load(DIAG)["rows"]}
    registry = RS.register_all(core.Registry.default())
    n_rows, n_same, n_reason_same, n_reason_checked = 0, 0, 0, 0
    mism = []
    ctrl = {u"期間(注入)": [0, 0], u"単位": [0, 0], u"次元": [0, 0]}
    axes_by_row = {}
    states = {}
    for doc, inst, mrows, b_by in _material_rows(docs, AT):
        facts, contexts = inst["facts"], inst["contexts"]
        keys = {A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])): f for f in facts}
        for r in mrows:
            b = b_by[(doc, r["id"])]
            ptr, unit, val = b[u"席の参照先"], r[u"単位"], r[u"値"]
            want = rec_rows[(doc, r["id"])]
            n_rows += 1
            if ptr is None:
                same = want[u"**合成の後**"] is None
                n_same += same
                states[None] = states.get(None, 0) + 1
                if not same:
                    mism.append([doc, r["id"], None, want[u"**合成の後**"]])
                continue
            f = keys.get(A1.norm_pointer(ptr))
            loc = ("%s@%s" % (f["name"], f["context"])) if f else ptr
            spec = {"kind": "single_value", "value": val, "unit": unit, "pointers": [loc]}
            out = VE.verify_external(spec, facts, contexts, registry)
            states[out["state"]] = states.get(out["state"], 0) + 1
            same = out["state"] == want[u"**合成の後**"]
            n_same += same
            if not same:
                mism.append([doc, r["id"], out["state"], want[u"**合成の後**"]])
            if want.get(u"理由") and want[u"**合成の後**"] == "UNPROVABLE" and out["held"]:
                n_reason_checked += 1
                n_reason_same += (out["reason"] == want[u"理由"])
            if (doc, r["id"]) in diag:
                axes_by_row[(doc, r["id"])] = out["hold_axes"]
            if want[u"v1 の state"] == "GROUNDED":
                for branch, point_at_injected in ((u"期間(注入)", False), (u"単位", True), (u"次元", False)):
                    fs, key, _bad = AT.inject(facts, f, branch)
                    if key is None:
                        continue
                    ctrl[branch][0] += 1
                    o2 = VE.verify_external(dict(spec, pointers=[key if point_at_injected else loc]),
                                            fs, contexts, registry)
                    ctrl[branch][1] += (o2["state"] == "UNPROVABLE" and o2["held"])
    classes = {}
    for (doc, rid), axes in sorted(axes_by_row.items()):
        name = axes[0].split(":")[-1] if len(axes) == 1 else "|".join(a.split(":")[-1] for a in axes)
        classes[name] = classes.get(name, 0) + 1
    return (
        {u"行": n_rows, u"**一致**": n_same, u"不一致の明細": mism,
         u"(d) の理由を照合した行": n_reason_checked, u"理由も一致": n_reason_same,
         u"state の分布(入口)": {str(k): states[k] for k in sorted(states, key=str)}},
        {u"行": len(axes_by_row), u"分類": classes,
         u"明細": [{"doc": k[0], "id": k[1], "hold_axes": v} for k, v in sorted(axes_by_row.items())]},
        {k: {u"作れた": v[0], u"**保留**": v[1]} for k, v in ctrl.items()},
    )


# ---------------------------------------------------------------- F-7
def f7_verify_document(baseline):
    if not baseline or not os.path.exists(baseline):
        return {"ran": False, u"理由": u"--baseline が無い"}
    with open(baseline, "rb") as fh:
        bb = fh.read()
    tmp = tempfile.mkdtemp()
    outp = os.path.join(tmp, "vd.json")
    r = subprocess.run([sys.executable, "-m", "adapters.xbrl.verify_document", "--doc", BASELINE_DOC,
                        "--out", outp], cwd=ROOT, capture_output=True, text=True, env=ENV)
    if r.returncode != 0:
        return {"ran": True, "rc": r.returncode, "stderr": r.stderr[-500:]}
    with open(outp, "rb") as fh:
        ab = fh.read()
    before, after = json.loads(bb.decode("utf-8")), json.loads(ab.decode("utf-8"))
    diff_keys = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    engine_diff = []
    if "engine" in diff_keys and isinstance(before.get("engine"), dict):
        engine_diff = sorted(k for k in set(before["engine"]) | set(after["engine"])
                             if before["engine"].get(k) != after["engine"].get(k))
    return {"ran": True, "rc": 0, u"基準の sha256": _sha(bb), u"いまの sha256": _sha(ab),
            u"基準の sha256 の頭が封のとおり": _sha(bb).startswith(BASELINE_SHA_PREFIX),
            u"上の欄の並び": sorted(after), u"**動いた欄**": diff_keys, u"engine の中で動いた欄": engine_diff,
            u"claims の本数": len(after.get("claims", [])),
            u"claims の state": _count([c.get("state") for c in after.get("claims", [])])}


def _count(xs):
    d = {}
    for x in xs:
        d[str(x)] = d.get(str(x), 0) + 1
    return {k: d[k] for k in sorted(d)}


# ---------------------------------------------------------------- F-8
def f8_cli():
    inst = I.load_instance(io.open(ED.cache_path(BASELINE_DOC), "rb").read())
    f = [x for x in inst["facts"] if x["unit"] == "JPY" and x["context"] == "CurrentYearDuration"][0]
    claims = {"claims": [
        {"id": "C1", "kind": "single_value", "value": f["value"] / 1e6, "unit": u"百万円",
         "pointers": ["%s@%s" % (f["name"], f["context"])]},
        {"id": "C2", "kind": "single_value", "value": 1.0, "unit": u"百万円",
         "pointers": ["jppfs_cor:Nope@CurrentYearDuration"]},
        {"id": "C3", "kind": "ratio_change", "value": 1.0, "unit": u"％", "pointers": ["a@b"]},
    ]}
    tmp = tempfile.mkdtemp()
    cp = os.path.join(tmp, "claims.json")
    with io.open(cp, "w", encoding="utf-8") as fh:
        json.dump(claims, fh, ensure_ascii=False)
    shas, states = [], None
    for i in (1, 2):
        outp = os.path.join(tmp, "out%d.json" % i)
        r = subprocess.run([sys.executable, "-m", "adapters.xbrl.verify_external", "--doc", BASELINE_DOC,
                            "--claims", cp, "--out", outp], cwd=ROOT, capture_output=True, text=True, env=ENV)
        if r.returncode != 0:
            return {"rc": r.returncode, "stderr": r.stderr[-500:]}
        with open(outp, "rb") as fh:
            shas.append(_sha(fh.read()))
        states = _load(outp)["states"]
    return {"rc": 0, u"1 回目": shas[0], u"2 回目": shas[1], u"**同じ**": shas[0] == shas[1], u"states": states}


# ---------------------------------------------------------------- F-9
def f9_mutations(skip):
    now = _load(os.path.join(ROOT, "tests", "adapters", "xbrl", "mutations.json"))
    then = json.loads(_git(["show", "%s:./tests/adapters/xbrl/mutations.json" % SEAL_COMMIT]))
    key = lambda r: (r["id"], r["file"], r["old"], r["new"], r["predicted"], r.get("scope", "default"))
    old_ids = [r["id"] for r in then]
    now_by = {r["id"]: r for r in now}
    unchanged = sum(1 for r in then if r["id"] in now_by and key(now_by[r["id"]]) == key(r))
    new_rows = [r for r in now if r["id"] not in set(old_ids)]
    out = {u"封の commit の行数": len(then), u"いまの行数": len(now), u"**既存の行で字が同じ**": unchanged,
           u"足した行": [r["id"] for r in new_rows], u"足した行の予測": [r["predicted"] for r in new_rows]}
    if skip:
        out[u"走らせた"] = False
        return out
    TM = _mod("tests/adapters/xbrl/test_mutations.py", "test_mutations_for_hpp_measure")
    res = []
    for r in new_rows:
        rc, _txt = TM._run_mutation_fresh(r)
        res.append({"id": r["id"], "rc": rc, u"色": "red" if rc != 0 else "green", u"予測": r["predicted"]})
    out[u"走らせた"] = True
    out[u"結果"] = res
    out[u"**赤の本数**"] = sum(1 for x in res if x[u"色"] == "red")
    return out


# ---------------------------------------------------------------- F-10
def f10_frozen():
    paths = ["audit-core/core", "audit-core/adapters"]
    then = _git(["ls-tree", "-r", "--name-only", SEAL_COMMIT, "--"] + paths, cwd=REPO).split()
    now = _git(["ls-files", "--"] + paths, cwd=REPO).split()
    FB = _mod("fixtures/frozen_bundle_sha.py", "frozen_bundle_sha_for_hpp_measure")
    src_then = _git(["show", "%s:./fixtures/frozen_bundle_sha.py" % SEAL_COMMIT])
    lit_then = int(re.search(r"(?m)^FROZEN_COUNT = (\d+)", src_then).group(1))
    gens_then = src_then.count("\n    (\"")
    cwd0 = os.getcwd()
    os.chdir(REPO)
    try:
        sha_now, rows = FB.bundle(None)
        dirty = FB._dirty_count()
    finally:
        os.chdir(cwd0)
    return {u"封の commit の実測(git ls-tree)": len(then), u"封の commit の字(FROZEN_COUNT)": lit_then,
            u"いまの実測(git ls-files)": len(now), u"いまの字(FROZEN_COUNT)": FB.FROZEN_COUNT,
            u"束ねた本数": len(rows), u"世代の行(封の commit → いま)": [gens_then, len(FB.FROZEN_BUNDLE_GENERATIONS)],
            u"いまの束ねた sha": sha_now, u"字で留めた世代の値と一致": sha_now == FB.FROZEN_BUNDLE_SHA,
            u"足した file": sorted(set(now) - set(then)), u"消えた file": sorted(set(then) - set(now)),
            u"未コミット": dirty}


# ---------------------------------------------------------------- F-11
def _one_run(log):
    t = io.open(log, encoding="utf-8", errors="replace").read()
    rc = re.findall(r"(?m)^rc=(\d+)", t)
    done = u"--- 全部通った ---" in t
    lines = [l for l in t.splitlines() if re.search(r"passed|failed|^Ran |^OK|FAILED|漏れ|^---", l)]
    failed = sorted(set(re.findall(r"(?m)^FAILED (\S+)", t)))
    return {u"log": os.path.basename(log), u"rc": int(rc[-1]) if rc else None, u"**全部通った**": done,
            u"赤の試験": failed, u"要約の行": lines[-12:]}


def f11_run_tests(logs):
    """``run_tests.sh`` の log を**走らせた順に全部**読む(1 回目が赤なら、直した後の 2 回目も並べる)。"""
    logs = [l for l in (logs or []) if l and os.path.exists(l)]
    if not logs:
        return {"ran": False, u"理由": u"--run-tests-log が無い"}
    runs = [_one_run(l) for l in logs]
    return {"ran": True, u"回数": len(runs), u"1 回目の rc": runs[0][u"rc"], u"最後の rc": runs[-1][u"rc"],
            u"**全部通った**": runs[-1][u"**全部通った**"], u"走らせた順": runs,
            # 後方互換(門が読む欄)
            "rc": runs[-1][u"rc"]}


# ---------------------------------------------------------------- main
def tally(F, audit_verdict, audit_revise):
    P = []

    def row(sym, yosoku, jissoku, hit):
        P.append({u"記号": sym, u"予測": yosoku, u"実測": jissoku, u"当たり": bool(hit)})

    row("F-1", u"core/py の差分 0 行", F["F-1"], F["F-1"] == 0)
    f2, pt = F["F-2"][u"instance.py の numstat"], F["F-2"][u"engine 側の試験(変異を除く)"]
    row("F-2", u"instance.py は足すだけ(消す 0)・既存 786 本が全部緑",
        {u"足した": f2["added"], u"消した": f2["deleted"], u"消したコード行": f2.get(u"消したコード行"),
         u"試験": pt.get("summary")},
        f2["deleted"] == 0 and pt.get("ran") and pt.get("rc") == 0 and (pt.get("passed") or 0) >= 786)
    row("F-3", u"8 書類で axes と members が 1:1(違反 0)", F["F-3"][u"**違反**"], F["F-3"][u"**違反**"] == 0)
    row("F-4", u"192 / 192 一致(理由も (d) の 6 行で一致)",
        {u"一致": F["F-4"][u"**一致**"], u"理由": F["F-4"][u"理由も一致"]},
        F["F-4"][u"**一致**"] == 192 and F["F-4"][u"行"] == 192
        and F["F-4"][u"理由も一致"] == F["F-4"][u"(d) の理由を照合した行"] == 6)
    want5 = {"ConsolidatedOrNonConsolidatedAxis": 2, "OperatingSegmentsAxis": 2, "ComponentsOfEquityAxis": 2}
    row("F-5", u"連結・個別 2・セグメント 2・株主資本の内訳 2", F["F-5"][u"分類"], F["F-5"][u"分類"] == want5)
    c = F["F-6"]
    row("F-6", u"期間 18/18・単位 24/24・次元 24/24",
        {k: [v[u"**保留**"], v[u"作れた"]] for k, v in c.items()},
        all(c[k][u"作れた"] == c[k][u"**保留**"] == n for k, n in ((u"期間(注入)", 18), (u"単位", 24), (u"次元", 24))))
    row("F-7", u"engine の欄以外 byte 同一", F["F-7"].get(u"**動いた欄**"),
        F["F-7"].get("ran") and F["F-7"].get(u"**動いた欄**") == ["engine"]
        and F["F-7"].get(u"基準の sha256 の頭が封のとおり"))
    row("F-8", u"2 回の sha256 が同じ", F["F-8"].get(u"**同じ**"), F["F-8"].get(u"**同じ**") is True)
    m = F["F-9"]
    row("F-9", u"HOLD-R1〜R3 が 3 本とも red・既存 89 本は変わらない",
        {u"赤": m.get(u"**赤の本数**"), u"既存で同じ": m[u"**既存の行で字が同じ**"]},
        m.get(u"走らせた") and m.get(u"**赤の本数**") == 3 == len(m[u"足した行"])
        and m[u"**既存の行で字が同じ**"] == m[u"封の commit の行数"] == 89)
    fz = F["F-10"]
    row("F-10", u"保護面 22 → 24 本",
        {u"前(字)": fz[u"封の commit の字(FROZEN_COUNT)"], u"前(実測)": fz[u"封の commit の実測(git ls-tree)"],
         u"後(字)": fz[u"いまの字(FROZEN_COUNT)"], u"後(実測)": fz[u"いまの実測(git ls-files)"]},
        fz[u"封の commit の実測(git ls-tree)"] == 22 and fz[u"いまの実測(git ls-files)"] == 24)
    row("F-11", u"run_tests.sh rc=0",
        {u"1 回目": F["F-11"].get(u"1 回目の rc"), u"最後": F["F-11"].get(u"最後の rc"), u"回数": F["F-11"].get(u"回数")},
        # 予測は「走らせたら rc=0」。**1 回目**が赤なら外れ(直した後の 2 回目で緑になっても外れは外れ)
        F["F-11"].get("ran") and F["F-11"].get(u"1 回目の rc") == 0 and F["F-11"].get(u"**全部通った**"))
    row("F-12", u"REVISE 1 回 → GO", {u"判定": audit_verdict, u"REVISE": audit_revise},
        audit_verdict == "GO" and audit_revise == 1)
    return {u"当たり": sum(1 for p in P if p[u"当たり"]), u"外れ": sum(1 for p in P if not p[u"当たり"]),
            u"欄ごと": P}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--baseline", default=None)
    ap.add_argument("--run-tests-log", nargs="*", default=None, help=u"走らせた順に全部(1 回目が赤でも消さない)")
    ap.add_argument("--audit-verdict", default=None, choices=["GO", "REVISE", "HUMAN", None])
    ap.add_argument("--audit-revise", type=int, default=None, help=u"GO までの REVISE の回数")
    ap.add_argument("--audit-source", default=u"", help=u"監査の出どころ(席・日時・写した先)")
    ap.add_argument("--skip-pytest", action="store_true")
    ap.add_argument("--skip-mutations", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--out", default=OUT, help=u"記録の書き先(既定は正本。下見は scratchpad へ)")
    a = ap.parse_args(argv)

    docs = _load(DRAW)[u"引いた 8 件"]
    F = {}
    F["F-1"] = f1_core_diff()
    print("F-1 core diff lines:", F["F-1"])
    F["F-2"] = {u"instance.py の numstat": f2_instance_numstat(),
                u"engine 側の試験(変異を除く)": f2_engine_pytest(a.skip_pytest)}
    print("F-2:", F["F-2"])
    F["F-3"] = f3_axes(docs)
    print("F-3:", {k: v for k, v in F["F-3"].items() if k != u"違反の明細"})
    F["F-4"], F["F-5"], F["F-6"] = f4_f5_f6(docs)
    print("F-4:", {k: v for k, v in F["F-4"].items() if k != u"不一致の明細"}, "mismatches:", F["F-4"][u"不一致の明細"][:5])
    print("F-5:", F["F-5"][u"分類"])
    print("F-6:", F["F-6"])
    F["F-7"] = f7_verify_document(a.baseline)
    print("F-7:", {k: v for k, v in F["F-7"].items() if k != u"上の欄の並び"})
    F["F-8"] = f8_cli()
    print("F-8:", F["F-8"])
    F["F-9"] = f9_mutations(a.skip_mutations)
    print("F-9:", F["F-9"])
    F["F-10"] = f10_frozen()
    print("F-10:", F["F-10"])
    F["F-11"] = f11_run_tests(a.run_tests_log)
    print("F-11:", F["F-11"])
    F["F-12"] = {u"判定": a.audit_verdict, u"REVISE の回数": a.audit_revise, u"出どころ": a.audit_source,
                 u"注": u"機械が測った値ではない。監査の席の報告を人(司令塔)が写した"}
    rec = {
        "seal": SEAL, "seal_commit": SEAL_COMMIT, "step": u"(d)・P・U を製品の経路へ + 軸の保持 (e)",
        "head": _git(["rev-parse", "--short", "HEAD"]).strip(),
        u"未コミットの変更(adapters/ tests/ fixtures/)": _git(["status", "--porcelain", "--", "adapters", "tests", "fixtures"]).splitlines(),
        u"材料": {u"書類": docs, u"再現の記録": os.path.relpath(REC_PU, ROOT), u"(d) の 6 行": os.path.relpath(DIAG, ROOT)},
        u"**実測**": F,
        u"**予測との照合**": tally(F, a.audit_verdict, a.audit_revise),
        "limits": [u"精度は測っていない(封 §0・§4)", u"同じ 8 書類での再現",
                   u"hold_axes は違う軸を記録するだけで、不一致の規則ではない",
                   u"F-12 は機械の測定ではなく監査の席の報告の写し"],
    }
    print(u"予測との照合: 当たり %d / 外れ %d" % (rec[u"**予測との照合**"][u"当たり"], rec[u"**予測との照合**"][u"外れ"]))
    for p in rec[u"**予測との照合**"][u"欄ごと"]:
        print("  %s %s" % (p[u"記号"], u"当たり" if p[u"当たり"] else u"**外れ**"))
    if a.write:
        with io.open(a.out, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("written:", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
