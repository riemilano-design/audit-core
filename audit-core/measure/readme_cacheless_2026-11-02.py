# -*- coding: utf-8 -*-
u"""cache の無い clone で README.en.md の手順が字どおりに動くかを測る(封 docs/README_CACHELESS_SEAL_2026-11-02.md)。

README の 3 節(10 分再現・自分の書類の点検・Install)のコマンドを**字のまま**子 process で呼び、
rc・書き出された file・案内の字を記録 fixtures/readme_cacheless_2026-11-02.json に書く。
engine(core/・adapters/)は import しない(読むのは adapters/xbrl/instance.py の定数を ast で 1 つだけ)。
通信しない(pip には --no-index)。README・engine・儀式の script は変えない。

    python3 measure/readme_cacheless_2026-11-02.py --work <repo の外の空 dir> [--out fixtures/readme_cacheless_2026-11-02.json]

副作用の後始末: pip install を cwd=ROOT で呼ぶと setuptools が ROOT に audit_core.egg-info/ と build/ を書く。
走らせる前に無かったものは終わりに消し、消した名前を記録に残す。
"""
from __future__ import print_function

import argparse
import ast
import hashlib
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SEAL_REL = "docs/README_CACHELESS_SEAL_2026-11-02.md"
SEAL_COMMIT = "443a078"
OUT_REL = "fixtures/readme_cacheless_2026-11-02.json"
README_REL = "README.en.md"
RITUAL_REL = "measure/ritual_2026-10-20.py"
ZIP_REL = "fixtures/xbrl/ai_prose_instance_2026-10-09.zip"
LABELS_README_REL = "fixtures/xbrl/TAXONOMY_LABELS_README.md"
LABELS_SHA_REL = "fixtures/xbrl/taxonomy_labels_sha256.txt"
INSTANCE_REL = "adapters/xbrl/instance.py"
SETUP_CFG_REL = "setup.cfg"
README_LABEL_DIR = os.path.expanduser("~/.cache/audit-core/edinet-taxonomy/2025-11-01")   # README の字のまま
CACHE_DIR = os.path.expanduser("~/.cache/audit-core")

SENTENCE = u"当連結会計年度の売上高は 1,234 百万円となりました。"      # 封 §0 の 3 で固定
ELEMENT_RE = re.compile(r"(?:jp[a-z]+_cor|jp[a-z0-9]+-[a-z]+_E\d{5}-\d{3}):[A-Z][A-Za-z0-9]+")
COMBINED_IMPORT = "import audit_core, adapters.xbrl.verify_external"
CONSOLE_SCRIPTS = ("audit-core-verify-document", "audit-core-verify-external")
README_PHRASES = ("exit code 2", "Python >= 3.9", "zero runtime dependencies", "Two console scripts")

FORBIDDEN_RECORD_KEYS = (u"span", u"文", u"段落", u"窓", u"ラベル", u"理由の自由文", u"pointers", u"named")
KEY_PATTERNS = (r"sk-[A-Za-z0-9_\-]{10,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{20,}", r"xox[baprs]-[A-Za-z0-9\-]{10,}",
                r"-----BEGIN", r"Bearer [A-Za-z0-9._\-]{16,}", r"AIza[0-9A-Za-z_\-]{30,}")


class Stop(SystemExit):
    pass


def sha256_file(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def text(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def env_for_children():
    e = dict(os.environ)
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    e["PYTHONIOENCODING"] = "utf-8"
    e.pop("EDINET_TAXONOMY_DIR", None)        # 封: 未設定のまま(README の既定の置き場を見させる)
    return e


def run(cmd, cwd):
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env_for_children())
    dt = time.time() - t0
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace"), round(dt, 2)


def last_error_line(se):
    u"""stderr の中で例外の名前を持つ最後の行(無ければ None)。"""
    hits = [ln.strip() for ln in se.splitlines() if re.match(r"^\s*[A-Za-z_.]*(Error|Exception)\b", ln)]
    return hits[-1] if hits else None


def git_head():
    rc, out, _, _ = run(["git", "rev-parse", "HEAD"], ROOT)
    return out.strip() if rc == 0 else None


def setuptools_dir():
    rc, out, _, _ = run([sys.executable, "-c", "import setuptools, os; print(os.path.dirname(setuptools.__file__))"], ROOT)
    return out.strip() if rc == 0 else None


def tool_versions():
    rc, out, _, _ = run([sys.executable, "-m", "pip", "--version"], ROOT)
    pip_v = re.search(r"pip (\S+)", out).group(1) if rc == 0 and re.search(r"pip (\S+)", out) else None
    rc, out, _, _ = run([sys.executable, "-c", "import setuptools; print(setuptools.__version__)"], ROOT)
    st_v = out.strip() if rc == 0 else None
    os_name = None
    if os.path.isfile("/etc/os-release"):
        m = re.search(r'^PRETTY_NAME="([^"]*)"', text_abs("/etc/os-release"), re.M)
        os_name = m.group(1) if m else None
    return {u"python": platform.python_version(), u"pip": pip_v, u"setuptools": st_v, u"platform": platform.platform(),
            u"OS": os_name, u"setuptools の置き場": setuptools_dir(),
            u"cache dir が在る": os.path.isdir(CACHE_DIR), u"README の label dir が在る": os.path.isdir(README_LABEL_DIR),
            u"EDINET_TAXONOMY_DIR": os.environ.get("EDINET_TAXONOMY_DIR")}


# ---------------------------------------------------------------- 1 儀式(ラベル無し)

def item_1_ritual(work):
    out_dir = os.path.join(work, "ritual_out")
    os.makedirs(out_dir)
    rc, so, se, dt = run([sys.executable, RITUAL_REL, "--out", out_dir], ROOT)
    msg = so + se
    files = sorted(os.listdir(out_dir))
    return {u"rc": rc, u"案内に TAXONOMY_LABELS_README.md": "TAXONOMY_LABELS_README.md" in msg,
            u"案内に EDINET_TAXONOMY_DIR": "EDINET_TAXONOMY_DIR" in msg,
            u"out dir に書かれた file": files, u"out dir の file 数": len(files),
            u"案内(先頭 400 字)": msg[:400], u"秒": dt}


# ---------------------------------------------------------------- 2 ラベルの名簿(読むだけ)

def instance_label_files():
    u"""adapters/xbrl/instance.py の TAXONOMY_LABEL_FILES を ast で読む(import しない)。"""
    tree = ast.parse(text(INSTANCE_REL))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TAXONOMY_LABEL_FILES" for t in node.targets):
            return [tuple(x) for x in ast.literal_eval(node.value)]
    raise Stop(u"TAXONOMY_LABEL_FILES が instance.py に無い")


def item_2_labels():
    req = instance_label_files()                                 # (ns, filename, sha)
    roster = {}
    for line in text(LABELS_SHA_REL).splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            h, fn = line.split(None, 1)
            roster[fn.strip()] = h
    readme_rows = {}
    for m in re.finditer(r"^\| `([^`]+)` \| ([\d,]+) \| `([0-9a-f]{64})` \|", text(LABELS_README_REL), re.M):
        readme_rows[m.group(1)] = {u"bytes": int(m.group(2).replace(",", "")), u"sha256": m.group(3)}
    same = 0
    total_bytes = 0
    per_file = []
    for _ns, fn, sha in req:
        ok = roster.get(fn) == sha and readme_rows.get(fn, {}).get(u"sha256") == sha
        same += 1 if ok else 0
        b = readme_rows.get(fn, {}).get(u"bytes")
        total_bytes += b or 0
        per_file.append({u"file": fn, u"sha256 が 3 か所で同じ": ok, u"bytes(TAXONOMY_LABELS_README の表)": b})
    readme_en = text(README_REL)
    m = re.search(r"download the (\w+) standard-taxonomy label files .*? about (\d+) MB", readme_en)
    return {u"儀式が要求する本数": len(req), u"名簿の本数": len(roster), u"TAXONOMY_LABELS_README の表の本数": len(readme_rows),
            u"sha256 が 3 か所で同じ本数": same, u"要求 2 本のバイト数の合計": total_bytes, u"file ごと": per_file,
            u"README.en.md の字": {u"本数の語": m.group(1) if m else None, u"MB": int(m.group(2)) if m else None}}


# ---------------------------------------------------------------- 3 verify_document

def read_json(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def item_3_verify(work):
    zip_abs = os.path.join(ROOT, ZIP_REL)
    txt = os.path.join(work, "one_sentence.txt")
    with io.open(txt, "w", encoding="utf-8") as fh:
        fh.write(SENTENCE + u"\n")
    res = {}
    for label, extra, out_name in ((u"text あり", ["--text", txt], "out_text.json"), (u"text なし", [], "out_notext.json")):
        out = os.path.join(work, out_name)
        rc, so, se, dt = run([sys.executable, "-m", "adapters.xbrl.verify_document", "--zip", zip_abs] + extra + ["--out", out], ROOT)
        d = {u"rc": rc, u"out.json が在る": os.path.isfile(out), u"秒": dt, u"stderr(末尾 300 字)": se[-300:],
             u"例外の行": last_error_line(se)}
        if os.path.isfile(out):
            j = read_json(out)
            d[u"claims"] = j["document"]["claims"]
            d[u"states"] = j["document"]["states"]
            d[u"unverifiable"] = j["document"]["unverifiable"]
        res[label] = d
    return res, os.path.join(work, "out_notext.json")


# ---------------------------------------------------------------- 4 report_customer(ラベル dir 無し)

def item_4_report(work, inp):
    zip_abs = os.path.join(ROOT, ZIP_REL)
    out = os.path.join(work, "report.md")
    prov = os.path.join(work, "report.provenance.json")
    rc, so, se, dt = run([sys.executable, "-m", "adapters.xbrl.report_customer", "--in", inp, "--out", out,
                          "--labels", README_LABEL_DIR, "--zip", zip_abs, "--full"], ROOT)
    d = {u"rc": rc, u"labels dir が在る": os.path.isdir(README_LABEL_DIR), u"report.md が在る": os.path.isfile(out),
         u"report.provenance.json が在る": os.path.isfile(prov), u"秒": dt, u"stderr(末尾 300 字)": se[-300:],
             u"例外の行": last_error_line(se)}
    if os.path.isfile(out):
        lines = text_abs(out).splitlines()
        d[u"要素名の形が出る行の数"] = sum(1 for ln in lines if ELEMENT_RE.search(ln))
        d[u"report.md の行数"] = len(lines)
    return d


def text_abs(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 5 install

def make_venv(work, name):
    v = os.path.join(work, name)
    rc, so, se, dt = run([sys.executable, "-m", "venv", "--system-site-packages", v], ROOT)
    if rc != 0:
        raise Stop(u"venv が作れない: %s%s" % (so, se))
    py = os.path.join(v, "bin", "python3")
    rc, out, _, _ = run([py, "-m", "pip", "--version"], ROOT)
    pv = re.search(r"pip (\S+)", out)
    return v, py, (pv.group(1) if pv else None), dt


def item_5_install(work):
    outside = os.path.join(work, "outside_cwd")
    os.makedirs(outside)
    res = {}
    # 非 editable(README の字: pip install . --no-build-isolation。通信しないため --no-index を足す)
    v, py, pv, dt_venv = make_venv(work, "venv_noneditable")
    rc_i, so, se, dt_i = run([py, "-m", "pip", "install", ".", "--no-build-isolation", "--no-index"], ROOT)
    rc_imp, so2, se2, dt_imp = run([py, "-c", COMBINED_IMPORT], outside)
    helps = {}
    for name in CONSOLE_SCRIPTS:
        exe = os.path.join(v, "bin", name)
        rc_h, so_h, _, _ = run([exe, "--help"], outside) if os.path.isfile(exe) else (127, "", "", 0)
        helps[name] = {u"rc": rc_h, u"usage: が在る": "usage:" in so_h}
    res[u"非 editable"] = {u"venv の pip": pv, u"install rc": rc_i, u"install stderr(末尾 300 字)": se[-300:],
                          u"install の例外の行": last_error_line(se),
                          u"combined import rc": rc_imp, u"combined import stderr(末尾 300 字)": se2[-300:],
                          u"--help": helps, u"秒(venv + install + import + help)": round(dt_venv + dt_i + dt_imp, 2)}
    # editable(README が「older toolchain では失敗」と書く経路)
    v2, py2, pv2, dt_venv2 = make_venv(work, "venv_editable")
    rc_e, so, se, dt_e = run([py2, "-m", "pip", "install", "-e", ".", "--no-build-isolation", "--no-index"], ROOT)
    rc_eimp, so2, se2, dt_eimp = run([py2, "-c", COMBINED_IMPORT], outside)
    helps2 = {}
    for name in CONSOLE_SCRIPTS:                               # 追加の実測(封 R-5 の判定には使わない)
        exe = os.path.join(v2, "bin", name)
        rc_h, so_h, _, _ = run([exe, "--help"], outside) if os.path.isfile(exe) else (127, "", "", 0)
        helps2[name] = {u"rc": rc_h, u"usage: が在る": "usage:" in so_h}
    res[u"editable"] = {u"venv の pip": pv2, u"install rc": rc_e, u"install stderr(末尾 300 字)": se[-300:],
                       u"install の例外の行": last_error_line(se),
                       u"combined import rc": rc_eimp, u"combined import stderr(末尾 300 字)": se2[-300:],
                       u"--help(判定には使わない)": helps2,
                       u"秒(venv + install + import)": round(dt_venv2 + dt_e + dt_eimp, 2)}
    return res


# ---------------------------------------------------------------- 7 README の字

def setup_cfg_fields():
    cfg = text(SETUP_CFG_REL)
    # [ \t]* にする(\s* は改行を跨いで次の行を値として読む。2026-11-02 の最初の走らせで見つけた欠陥)
    pr = re.search(r"^python_requires[ \t]*=[ \t]*(.*)$", cfg, re.M)
    ir = re.search(r"^install_requires[ \t]*=[ \t]*(.*)$", cfg, re.M)
    ir_body = []
    if ir:
        after = cfg[ir.end():].splitlines()
        for ln in after:
            if ln.startswith((" ", "\t")) and ln.strip():
                ir_body.append(ln.strip())
            elif ln.strip():
                break
    cs = re.search(r"^console_scripts\s*=\s*\n((?:[ \t]+.*\n?)+)", cfg, re.M)
    cs_lines = [ln.strip() for ln in cs.group(1).splitlines() if ln.strip()] if cs else []
    return {u"python_requires": pr.group(1).strip() if pr else None,
            u"install_requires の行": ir_body + ([ir.group(1).strip()] if ir and ir.group(1).strip() else []),
            u"console_scripts の本数": len(cs_lines)}


def item_7_readme(rec1, rec5):
    readme = re.sub(r"\s+", " ", text(README_REL))        # 折り返し(ソフトラップ)を 1 つの空白に
    cfg = setup_cfg_fields()
    present = {p: (p in readme) for p in README_PHRASES}
    checks = {
        u"exit code 2": {u"README に在る": present["exit code 2"], u"実測の rc": rec1[u"rc"], u"一致": present["exit code 2"] and rec1[u"rc"] == 2},
        u"Python >= 3.9": {u"README に在る": present["Python >= 3.9"], u"setup.cfg python_requires": cfg[u"python_requires"],
                          u"一致": present["Python >= 3.9"] and cfg[u"python_requires"] == ">=3.9"},
        u"zero runtime dependencies": {u"README に在る": present["zero runtime dependencies"], u"setup.cfg install_requires の行": cfg[u"install_requires の行"],
                                       u"一致": present["zero runtime dependencies"] and cfg[u"install_requires の行"] == []},
        u"Two console scripts": {u"README に在る": present["Two console scripts"], u"setup.cfg console_scripts の本数": cfg[u"console_scripts の本数"],
                                 u"--help が rc=0 の本数": sum(1 for h in rec5[u"非 editable"][u"--help"].values() if h[u"rc"] == 0),
                                 u"一致": present["Two console scripts"] and cfg[u"console_scripts の本数"] == 2
                                 and sum(1 for h in rec5[u"非 editable"][u"--help"].values() if h[u"rc"] == 0) == 2},
    }
    checks[u"一致した数"] = sum(1 for k, v in checks.items() if isinstance(v, dict) and v[u"一致"])
    return checks


# ---------------------------------------------------------------- 予測の判定(封 §1 の字をそのまま規則にする)

def judge(rec):
    r1, r2, r3, r4, r5, r7 = (rec[u"1 儀式(ラベル無し)"], rec[u"2 ラベルの名簿"], rec[u"3 verify_document"],
                              rec[u"4 report_customer(ラベル dir 無し)"], rec[u"5 install"], rec[u"7 README の字"])
    j = {}
    j[u"R-1"] = r1[u"rc"] == 2 and r1[u"案内に TAXONOMY_LABELS_README.md"] and r1[u"案内に EDINET_TAXONOMY_DIR"] and r1[u"out dir の file 数"] == 0
    j[u"R-2"] = (r2[u"儀式が要求する本数"] == 2 and r2[u"README.en.md の字"][u"本数の語"] == "two" and r2[u"名簿の本数"] == 3
                 and r2[u"sha256 が 3 か所で同じ本数"] == 2 and 8000000 <= r2[u"要求 2 本のバイト数の合計"] < 9000000)
    a, b = r3[u"text あり"], r3[u"text なし"]
    j[u"R-3"] = a[u"rc"] == 0 and a.get(u"claims") == 1 and b[u"rc"] == 0 and (b.get(u"claims") or 0) >= 200
    j[u"R-4"] = (r4[u"rc"] == 0 and r4[u"report.md が在る"] and r4[u"report.provenance.json が在る"]
                 and r4.get(u"要素名の形が出る行の数", 0) >= 1)
    ne, ed = r5[u"非 editable"], r5[u"editable"]
    j[u"R-5"] = (ne[u"install rc"] == 0 and ne[u"combined import rc"] == 0 and all(h[u"rc"] == 0 for h in ne[u"--help"].values())
                 and ed[u"install rc"] == 0 and ed[u"combined import rc"] == 0)
    j[u"R-6"] = rec[u"6 壁時計の合計(秒)"] <= 600
    j[u"R-7"] = r7[u"一致した数"] == 4
    out = {k: (u"当たり" if v else u"外れ") for k, v in j.items()}
    out[u"当たり"] = sum(1 for v in j.values() if v)
    out[u"外れ"] = sum(1 for v in j.values() if not v)
    return out


# ---------------------------------------------------------------- 後始末・記録

def tree_side_effects(before):
    after = set(os.listdir(ROOT))
    new = sorted(n for n in after - before if n.endswith(".egg-info") or n == "build")
    for n in new:
        shutil.rmtree(os.path.join(ROOT, n), ignore_errors=True)
    return new


def redact(obj, work):
    u"""記録の字から --work の絶対パスを消す(機械ごとの置き場を fixtures に残さない)。"""
    if isinstance(obj, dict):
        return {k: redact(v, work) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v, work) for v in obj]
    if isinstance(obj, str):
        return obj.replace(work, "<work>")
    return obj


def record_key_leaks(obj):
    t = json.dumps(obj, ensure_ascii=False)
    return sorted(set(p for p in KEY_PATTERNS if re.search(p, t)))


def forbidden_keys(obj):
    bad = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in FORBIDDEN_RECORD_KEYS:
                    bad.add(k)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(obj)
    return sorted(bad)


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--work", required=True, help=u"書き出しの置き場(repo の外の空 dir。無ければ作る)")
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise Stop(u"記録が既に在る: %s(上書きしない)" % a.out)
    work = os.path.abspath(a.work)
    if os.path.commonpath([work, ROOT]) == ROOT:
        raise Stop(u"--work は repo の外に置く: %s" % work)
    os.makedirs(work, exist_ok=True)
    if os.listdir(work):
        raise Stop(u"--work は空の dir にする: %s" % work)
    before = set(os.listdir(ROOT))

    t0 = time.time()
    rec = {
        u"注意": u"README.en.md の 3 節のコマンドを字のまま走らせた rc・書き出し・案内の字の記録。ラベルの取得(Step 0)と"
                u"ラベル有りの儀式は測っていない。1 文の判定は正しさの判定に使わない。",
        u"封": {u"file": SEAL_REL, u"commit": SEAL_COMMIT},
        u"HEAD の commit": git_head(),
        u"この script の sha256": sha256_file(os.path.abspath(__file__)),
        u"環境": tool_versions(),
        u"固定した 1 文": SENTENCE,
    }
    rec[u"1 儀式(ラベル無し)"] = item_1_ritual(work)
    rec[u"2 ラベルの名簿"] = item_2_labels()
    rec[u"3 verify_document"], notext_out = item_3_verify(work)
    rec[u"4 report_customer(ラベル dir 無し)"] = item_4_report(work, notext_out)
    rec[u"5 install"] = item_5_install(work)
    rec[u"6 壁時計の合計(秒)"] = round(time.time() - t0, 1)
    rec[u"7 README の字"] = item_7_readme(rec[u"1 儀式(ラベル無し)"], rec[u"5 install"])
    rec[u"予測の判定"] = judge(rec)
    rec[u"木に出た生成物(消した)"] = tree_side_effects(before)
    rec = redact(rec, work)
    rec[u"key_leaks"] = record_key_leaks(rec)
    bad = forbidden_keys(rec)
    if bad:
        raise Stop(u"記録に禁じた key: %s" % bad)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(dumps(rec))
    print(u"written: %s" % a.out)
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
