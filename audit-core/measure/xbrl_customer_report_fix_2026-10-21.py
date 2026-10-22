# -*- coding: utf-8 -*-
"""顧客向けの日本語の報告形の直し(``adapters/xbrl/report_customer.py``)の測定 ― 封 ``docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md`` §2(R2-1〜R2-7)。

    cd audit-core
    python3 measure/xbrl_customer_report_fix_2026-10-21.py --customer-out <客 A の P22 の出力 JSON>      # 記録 fixtures/xbrl/customer_report_fix_2026-10-21.json を書く
    python3 measure/xbrl_customer_report_fix_2026-10-21.py --stage docs --docs S100YYK8,S100YZ7E --out <file>   # 軽い走らせ直し(--out 必須)

**0 USD・通信なし・鍵の値は読まない。** 書類は ``~/.cache/audit-core/edinet/*.zip`` の手元の cache だけ(無い書類は取りに行かない)。標準ラベルは
``~/.cache/audit-core/edinet-taxonomy/2025-11-01``(repo の外。名簿 ``fixtures/xbrl/taxonomy_labels_sha256.txt`` の 3 file を起動時に sha256 で照合)。
engine(``core/``・``adapters/`` の module 以外)は測る側から 1 行も変えない。

「前」= commit c13a746 の module(``git show`` で取り出し、記録 ``customer_report_2026-10-21.json`` の C5 の sha256 と一致することを確かめてから ``exec``)と、
その当時のラベル(jpcrp・jppfs の 2 file)。「後」= いまの module と名簿の 3 file と書類の ZIP のラベル(CLI ``--labels … --zip …`` と同じ組み方)。

  R2-1  節の件数が c13a746 の記録と同じ。**行ごとの節の割り当て**(報告の中の id の並び)が「前」と全行同じ。
  R2-2  P25 明示で (a) 単位の食い違い(前 → 後)と、読み取れない行。
  R2-3  (c) ラベルが引けず要素名・区分名の字のまま出た行(違う・一致)。
  R2-4  (e) 本文の 64 桁の hex。同じ入力から同じバイト列(本文・json)× 67 書類 × 2 profile。
  R2-5  名簿の外の file を置いても本文が変わらない。sha256 違いの名簿の file は使わない。
  R2-6  客 A の 5 件。
  R2-7  触らない file の sha256。engine の指紋。
"""
import argparse
import collections
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
import types
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

from adapters.xbrl import instance as I            # noqa: E402
from adapters.xbrl import report_customer as RC    # noqa: E402
from adapters.xbrl import verify_document as VD    # noqa: E402

SEAL = "docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md"
OUT_REL = "fixtures/xbrl/customer_report_fix_2026-10-21.json"
OLD_REC_REL = "fixtures/xbrl/customer_report_2026-10-21.json"
PP_REL = "fixtures/xbrl/point_prior_2026-10-20.json"
ROSTER_REL = "fixtures/xbrl/taxonomy_labels_sha256.txt"
OLD_COMMIT = "c13a746"
MODULE_REL = "adapters/xbrl/report_customer.py"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
BOTH = ("P22", "P25")
SECTIONS = ("違う", "要確認", "対象外", "判断しない", "一致")
MONEY = ("百万円", "千円", "億円", "兆円", "円")
UNTOUCHED = ("adapters/xbrl/report.py", "adapters/xbrl/verify_document.py", "adapters/xbrl/vocabulary.py",
             "adapters/xbrl/recipes.py", "adapters/xbrl/registry_setup.py", "adapters/xbrl/comparators.py")
#: 封の commit 時点(14cdd21 の木)の sha256 先頭 16 桁。R2-7 の比べ先(封の門 test_xbrl_customer_report_fix_seal.py の UNTOUCHED と同じ値)。
UNTOUCHED_SHA16 = {"adapters/xbrl/report.py": "0d2854e659a5d8e0", "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad",
                   "adapters/xbrl/vocabulary.py": "27e71e9861fc5aad", "adapters/xbrl/recipes.py": "bff243f13429b553",
                   "adapters/xbrl/registry_setup.py": "f42ffe23aaa7673b", "adapters/xbrl/comparators.py": "d8706338325e725b"}
ANSWER_IDS = (("E1 前期を当期", "N001"), ("E2 末尾桁", "N007"), ("E5 率", "N010"), ("E3 単位", "N015"), ("E4 向き", "T009"))
CUSTOMER_OUT_SHA = "60e5fbdf2efffd0e81b4f4bf61aa857f8afa1a60e57c5036b27e68e8cac471b6"   # 客 A の P22 の出力 my_text.json(c13a746 の記録の C1 と同じ)

#: 要素名・区分名の字(キャメルケース・Member・_cor)。会社のラベル自体に入る英字(IT・IoT・BtoB)は数えない(試作の数え方。封 R2-3 の正規表現の 7 はこれ)。
ASCII_NAME_RE = re.compile(r"[A-Za-z0-9-]*[a-z][A-Z][A-Za-z0-9-]*|Member\b|[a-z]+_cor\b")
HEX64_RE = re.compile(r"\b[0-9a-f]{64}\b")
ID_ROW_RE = re.compile(r"^\| ([A-Z]\d{3,}) \|")
ID_BULLET_RE = re.compile(r"^- ([A-Z]\d{3,}): ")
HEADS = (("## 1. 違う", "違う"), ("## 2. 要確認", "要確認"), ("### 対象外", "対象外"), ("### 判断しない", "判断しない"), ("## 4. 一致", "一致"))


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with io.open(p, "rb") as fh:
        return sha_bytes(fh.read())


def sha_text(s):
    return sha_bytes(s.encode("utf-8"))


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def git(*args, **kw):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, **kw)


def kv(d):
    return dict(sorted(d.items()))


def labels_dir():
    return I.taxonomy_dir() if os.path.isdir(I.taxonomy_dir()) else os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-taxonomy", "2025-11-01")


def load_old_module(old_rec):
    """c13a746 の module を git から取り出し、記録の C5 の sha256 と一致することを確かめて exec する。"""
    r = git("show", "%s:audit-core/%s" % (OLD_COMMIT, MODULE_REL))
    if r.returncode != 0:
        raise SystemExit("c13a746 の module を git から取り出せない: " + r.stderr.decode("utf-8", "replace")[-300:])
    want = old_rec["C5"]["report_customer.py の sha256"]
    if sha_bytes(r.stdout) != want:
        raise SystemExit("c13a746 の module の sha256 が記録(%s)と違う" % want)
    src = r.stdout.decode("utf-8").replace("from .report import cell, fmt_num", "from adapters.xbrl.report import cell, fmt_num")
    mod = types.ModuleType("report_customer_c13a746")
    exec(compile(src, "report_customer_c13a746", "exec"), mod.__dict__)
    return mod


def old_labels(old_mod, d):
    """c13a746 の当時のラベル(jpcrp・jppfs の 2 file)。"""
    lab = {}
    for fn in ("jpcrp_2025-11-01_lab.xml", "jppfs_2025-11-01_lab.xml"):
        with io.open(os.path.join(d, fn), "rb") as fh:
            lab.update(old_mod.parse_label_linkbase(fh.read()))
    return lab


def ids_by_section(md):
    """報告(--full)の本文から、節ごとの id の並び。"""
    out = dict((s, []) for s in SECTIONS)
    cur = None
    for line in md.split("\n"):
        hit = [s for h, s in HEADS if line.startswith(h)]
        if hit:
            cur = hit[0]
            continue
        if line.startswith("## "):
            cur = None
            continue
        m = ID_ROW_RE.match(line) or ID_BULLET_RE.match(line)
        if m and cur:
            out[cur].append(m.group(1))
    return out


def heading_counts(md):
    out = {}
    for pat, s in ((r"^## 1\. 違う ― ([\d,]+) 件", "違う"), (r"^## 2\. 要確認 ― ([\d,]+) 件", "要確認"), (r"^### 対象外 ― ([\d,]+) 件", "対象外"),
                   (r"^### 判断しない ― ([\d,]+) 件", "判断しない"), (r"^## 4\. 一致 ― ([\d,]+) 件", "一致")):
        m = re.search(pat, md, re.M)
        out[s] = int(m.group(1).replace(",", "")) if m else None
    return out


UNIT_END_RE = re.compile(r"(百万円|千円|億円|兆円|万円|円)$")
SIGN_CHARS = "△▲-"
_MULT = {"兆": 1e12, "億": 1e8, "千万": 1e7, "百万": 1e6, "万": 1e4, "千": 1e3, "百": 1e2, "": 1}


def table_rows(md):
    """報告(--full)の本文から ``(節, 列の字の並び)``。module の関数は使わず、表の字だけを読む。"""
    cur = None
    for line in md.split("\n"):
        hit = [sname for h, sname in HEADS if line.startswith(h)]
        if hit:
            cur = hit[0]
            continue
        if line.startswith("## "):
            cur = None
            continue
        if cur and ID_ROW_RE.match(line):
            yield cur, [x.strip() for x in line.strip().strip("|").split(" | ")]


def _norm(t):
    return unicodedata.normalize("NFKC", t).replace(" ", "")


def audit_units(md):
    """**module の `written_amount_of` に頼らず**、報告の本文の列の字だけから単位の食い違いを数える(監査の指摘 2026-10-21)。

    金額の行 = 『文の値』の列が金額の単位(円・千円・百万円・億円・兆円・万円)で終わる行。食い違い = 次のどちらか:
      (i) 『文の値』の字が『文の抜粋』の中に(空白を除いて)無い、
      (ii) 『出典の値』の列(括弧の前)の末尾の単位が『文の値』の末尾の単位と違う(兆・億を前に書く複合の字どうしは、割り直しで単位の書き方が変わるので同じと見る)。
    返すのは ``(金額の行, 食い違い, (i) の数, (ii) の数)`` の節別。"""
    rows, bad, notin, unitbad = (collections.Counter() for _ in range(4))
    for sec, cols in table_rows(md):
        if len(cols) < 4:
            continue
        cv = cols[2]
        m = UNIT_END_RE.search(cv.strip())
        if not m:
            continue
        rows[sec] += 1
        nb = False
        if _norm(cv) not in _norm(cols[1]):
            notin[sec] += 1
            nb = True
        if len(cols) == 5 and cols[3] not in ("―", ""):
            main = cols[3].split("(")[0].strip()
            mu = UNIT_END_RE.search(main)
            ok = mu is not None and (mu.group(1) == m.group(1) or (re.search("[億兆]", cv) and re.search("[億兆]", main)))
            if not ok:
                unitbad[sec] += 1
                nb = True
        if nb:
            bad[sec] += 1
    return rows, bad, notin, unitbad


def parse_shown(text):
    """表の字(金額・率・ポイント)→ 絶対値(円または率の数)。読めなければ None。括弧の前だけを読む。"""
    t = unicodedata.normalize("NFKC", text).split("(")[0].strip().replace(",", "").replace(" ", "")
    t = t.lstrip(SIGN_CHARS).replace("マイナス", "")
    m = re.match(r"^(\d+(?:\.\d+)?)(%|ポイント)$", t)
    if m:
        return float(m.group(1))
    if not t.endswith("円"):
        return None
    t = t[:-1]
    m = re.match(r"^(?:(\d+(?:\.\d+)?)兆)?(?:(\d+(?:\.\d+)?)億)?(.*)$", t)
    head = (float(m.group(1)) * 1e12 if m.group(1) else 0.0) + (float(m.group(2)) * 1e8 if m.group(2) else 0.0)
    rest = m.group(3)
    if rest == "":
        return head
    # 「6千4百万」= 6400 万(千・百は万の位の係数)
    k = re.match(r"^(?:(\d+)千)?(?:(\d+)百)?(\d+)?万$", rest)
    if k:
        return head + (int(k.group(1) or 0) * 1000 + int(k.group(2) or 0) * 100 + int(k.group(3) or 0)) * 1e4
    toks = re.findall(r"(\d+(?:\.\d+)?)(千万|百万|万|千|百|)", rest)
    if not toks or "".join(a + b for a, b in toks) != rest:
        return None
    return head + sum(float(a) * _MULT[b] for a, b in toks)


def differs_in_value(a, b):
    return abs(a - b) > 1e-6 * max(1.0, abs(a), abs(b))


def audit_match_display(md):
    """『一致』の節の表で、『出典の値』の主表示(括弧の前)が『文の値』と同じ数に見えない行を、字だけから数える。(比べた行, 違って見える行)。"""
    n = bad = 0
    for sec, cols in table_rows(md):
        if sec != "一致" or len(cols) != 5 or cols[3] in ("―", ""):
            continue
        x, y = parse_shown(cols[2]), parse_shown(cols[3])
        if x is None or y is None:
            continue
        n += 1
        if differs_in_value(x, y):
            bad += 1
    return n, bad


def match_display_before(claims, doc_unit):
    """同じ『一致』の行を、四捨五入だけの主表示(前)で並べたときの (比べた行, 違って見える行)。"""
    n = bad = 0
    for c in claims:
        if RC.section_of(c) != "一致" or c.get("recomputed") is None:
            continue
        x = parse_shown(RC.claim_value_written(c))
        y = parse_shown(RC.source_value_report(c, doc_unit, False)[0])
        if x is None or y is None:
            continue
        n += 1
        if differs_in_value(x, y):
            bad += 1
    return n, bad


def docs67():
    fx = jload(os.path.join(ROOT, PP_REL))
    return [d for d in fx["書類"] if d["区分"] == "文あり"]


def source_unit_ok(shown, amt):
    """報告の出典の値の字が、文の字の単位で終わるか(括弧の前まで)。兆・億を前に書く形で余りが 0 のときは「円」で終わる。"""
    main = shown.split("(", 1)[0].strip()
    return main.endswith(amt.unit) or (amt.compound and main.endswith("円"))


def compose(std_labels, std_meta, zip_path):
    """標準ラベル(名簿の 3 file。読み込み済み)+ 書類の ZIP のラベル。``load_labels_with_meta(std_dir, zip_path)`` と同じ結果(標準が先)。"""
    zl, zmeta = RC.load_labels_with_meta(None, zip_path)
    merged = dict(zl)
    merged.update(std_labels)
    return merged, list(std_meta) + list(zmeta)


def doc_row(d, profile, labels, meta, lab_old, old_mod, zb, zip_path):
    t0 = time.time()
    out = VD.verify_document(zb, None if profile == "P22" else profile, None)
    t1 = time.time()
    claims = out["claims"]
    dei = RC.dei_from_zip(zip_path, (out.get("input") or {}).get("instance_source"))
    out2 = json.loads(json.dumps(out))
    md_new = RC.render_markdown(out, labels, False, dei)
    md_new_f = RC.render_markdown(out, labels, True, dei)
    md_new2 = RC.render_markdown(out2, labels, False, dei)
    md_new2_f = RC.render_markdown(out2, labels, True, dei)
    pv = RC.render_provenance(out, md_new, meta, dei, sha_bytes(zb))
    pv2 = RC.render_provenance(out2, md_new2, meta, dei, sha_bytes(zb))
    md_old = old_mod.render_markdown(out, lab_old, False)
    md_old_f = old_mod.render_markdown(out, lab_old, True)

    # R2-1: 節の件数と行ごとの割り当て
    sec_new = collections.Counter(RC.section_of(c) for c in claims)
    sec_old = collections.Counter(old_mod.section_of(c) for c in claims)
    ids_new = ids_by_section(md_new_f)
    ids_old = ids_by_section(md_old_f)
    want_ids = dict((s, [c["id"] for c in claims if RC.section_of(c) == s]) for s in SECTIONS)
    assign_diff = sum(1 for s in SECTIONS for a, b in zip(ids_new[s], ids_old[s]) if a != b) + sum(abs(len(ids_new[s]) - len(ids_old[s])) for s in SECTIONS)
    lines_new = ["%s\t%s\t%s\t%s" % (d["docID"], profile, cid, s) for s in SECTIONS for cid in ids_new[s]]
    lines_old = ["%s\t%s\t%s\t%s" % (d["docID"], profile, cid, s) for s in SECTIONS for cid in ids_old[s]]
    hc = heading_counts(md_new_f)

    # R2-2: 単位
    money = collections.Counter()
    unread = collections.Counter()
    read = collections.Counter()
    before_mis = collections.Counter()
    after_mis = collections.Counter()
    word_kind = collections.Counter()
    word_unit_changed = collections.Counter()
    doc_unit = RC.doc_unit_of(claims)
    for c in claims:
        s = RC.section_of(c)
        unit = c.get("unit")
        if unit in RC.UNIT_SCALE and c.get("value") is not None and not isinstance(c.get("value"), bool):
            money[s] += 1
            a = RC.written_amount_of(c)
            if a is None:
                unread[s] += 1
                continue
            read[s] += 1
            if a.unit != unit:
                before_mis[s] += 1
            bad = RC.claim_value_written(c) != a.text
            if s in ("違う", "一致") and c.get("recomputed") is not None:
                shown, kind = RC.source_value_report(c, doc_unit)
                if kind != "written" or not source_unit_ok(shown, a):
                    bad = True
            if bad:
                after_mis[s] += 1
        elif c.get("value") is None and not unit and c.get("recomputed") is not None and s in ("違う", "一致"):
            shown, kind = RC.source_value_report(c, doc_unit)
            word_kind[kind] += 1
            if not shown.split("(", 1)[0].strip().endswith(" 円"):
                word_unit_changed[kind] += 1

    # R2-2(独立): 報告の本文の列の字だけから数える。前 = c13a746 の module の本文、後 = いまの本文
    ia_rows, ia_bad, ia_notin, ia_unit = audit_units(md_new_f)
    ib_rows, ib_bad, ib_notin, ib_unit = audit_units(md_old_f)
    md_n, md_bad_after = audit_match_display(md_new_f)
    md_n_b, md_bad_before = match_display_before(claims, doc_unit)

    # R2-3: ラベルが引けず要素名・区分名の字のまま出た行(違う・一致)
    unres_new = collections.Counter()
    unres_old = collections.Counter()
    ascii_new = collections.Counter()
    ascii_old = collections.Counter()
    ascii_ex = []
    for c in claims:
        s = RC.section_of(c)
        if s not in ("違う", "一致"):
            continue
        if RC.unresolved_names(c.get("pointers"), labels):
            unres_new[s] += 1
        if RC.unresolved_names(c.get("pointers"), lab_old):
            unres_old[s] += 1
        txt_new = RC.source_ja(c.get("pointers"), labels)
        txt_old = old_mod.source_ja(c.get("pointers"), lab_old)
        if ASCII_NAME_RE.search(txt_new):
            ascii_new[s] += 1
            ascii_ex.append({"id": c["id"], "出典": txt_new})
        if ASCII_NAME_RE.search(txt_old):
            ascii_old[s] += 1

    return out, md_new, md_new_f, {
        "doc": d["docID"], "profile": out["profile"], "claims": len(claims),
        "節": dict((k, sec_new.get(k, 0)) for k in SECTIONS),
        "節(c13a746 の module)": dict((k, sec_old.get(k, 0)) for k in SECTIONS),
        "節の件数が報告の見出しと同じ": all(hc[s] == len(want_ids[s]) for s in SECTIONS),
        "報告の中の id の並びが section_of と同じ": all(ids_new[s] == want_ids[s] for s in SECTIONS),
        "行の節の割り当ての違い(前 → 後)": assign_diff,
        "割り当ての sha256(後)": sha_text("\n".join(lines_new)), "割り当ての sha256(前)": sha_text("\n".join(lines_old)),
        "金額の claim": dict((k, money.get(k, 0)) for k in SECTIONS),
        "金額の claim で文の字が読めた": dict((k, read.get(k, 0)) for k in SECTIONS),
        "読み取れない(金額の claim で span に同じ金額の字が無い)": dict((k, unread.get(k, 0)) for k in SECTIONS),
        "単位の食い違い 前(文の字の単位 ≠ 表に出した単位)": dict((k, before_mis.get(k, 0)) for k in SECTIONS),
        "単位の食い違い 後": dict((k, after_mis.get(k, 0)) for k in SECTIONS),
        "独立: 金額の行(『文の値』の列が金額の単位で終わる)": dict((k, ia_rows.get(k, 0)) for k in SECTIONS),
        "独立: 単位の食い違い 前(c13a746 の本文)": dict((k, ib_bad.get(k, 0)) for k in SECTIONS),
        "独立: 単位の食い違い 後": dict((k, ia_bad.get(k, 0)) for k in SECTIONS),
        "独立: 後のうち文の値が抜粋に無い": dict((k, ia_notin.get(k, 0)) for k in SECTIONS),
        "独立: 後のうち出典の値の単位が違う": dict((k, ia_unit.get(k, 0)) for k in SECTIONS),
        "一致の主表示を比べた行": md_n, "一致の主表示を比べた行(四捨五入だけ・前)": md_n_b,
        "一致の主表示が文と違って見える行 前": md_bad_before, "一致の主表示が文と違って見える行 後": md_bad_after,
        "語の主張(出典の値あり。違う・一致)の単位の出どころ": kv(word_kind),
        "語の主張で円以外の単位に直った行": kv(word_unit_changed),
        "ラベルが引けず名前のまま出た行 前(違う・一致)": dict((k, unres_old.get(k, 0)) for k in ("違う", "一致")),
        "ラベルが引けず名前のまま出た行 後(違う・一致)": dict((k, unres_new.get(k, 0)) for k in ("違う", "一致")),
        "英字の正規表現に当たる行 前(違う・一致)": dict((k, ascii_old.get(k, 0)) for k in ("違う", "一致")),
        "英字の正規表現に当たる行 後(違う・一致)": dict((k, ascii_new.get(k, 0)) for k in ("違う", "一致")),
        "英字の正規表現に当たる行 後の例": ascii_ex[:5],
        "本文の 64 桁の hex 前(c13a746・既定)": len(HEX64_RE.findall(md_old)),
        "本文の 64 桁の hex 後(既定)": len(HEX64_RE.findall(md_new)), "本文の 64 桁の hex 後(--full)": len(HEX64_RE.findall(md_new_f)),
        "本文の『engine の指紋』の行 後": md_new.count("engine の指紋") + md_new_f.count("engine の指紋"),
        "同じ byte(本文 既定)": md_new == md_new2, "同じ byte(本文 --full)": md_new_f == md_new2_f, "同じ byte(provenance)": pv == pv2,
        "provenance の body_sha256 が本文と一致": json.loads(pv)["report"]["body_sha256"] == sha_text(md_new),
        "本文の sha256(既定)": sha_text(md_new), "本文の sha256(--full)": sha_text(md_new_f),
        "ラベルの file(後)": [{"file": m["file"], "status": m["status"]} for m in meta],
        "表題": md_new.split("\n", 1)[0],
        "本文の行数": md_new.count("\n") + 1,
        "verify 秒": round(t1 - t0, 2),
    }


def add_cnt(rows, key):
    t = collections.Counter()
    for r in rows:
        t.update(r[key])
    return t


def aggregate(rows):
    def by(key, ks=SECTIONS):
        t = add_cnt(rows, key)
        d = dict((k, t.get(k, 0)) for k in ks)
        d["計"] = sum(d.values())
        return d
    word = collections.Counter()
    for r in rows:
        word.update(r["語の主張(出典の値あり。違う・一致)の単位の出どころ"])
    wchg = collections.Counter()
    for r in rows:
        wchg.update(r["語の主張で円以外の単位に直った行"])
    sec = add_cnt(rows, "節")
    return {
        "書類数": len(rows), "claims": sum(r["claims"] for r in rows),
        "節": dict((k, sec.get(k, 0)) for k in SECTIONS), "節の和": sum(sec.values()),
        "節(c13a746 の module)": by("節(c13a746 の module)"),
        "金額の claim": by("金額の claim"), "金額の claim で文の字が読めた": by("金額の claim で文の字が読めた"),
        "読み取れない(金額の claim で span に同じ金額の字が無い)": by("読み取れない(金額の claim で span に同じ金額の字が無い)"),
        "単位の食い違い 前(文の字の単位 ≠ 表に出した単位)": by("単位の食い違い 前(文の字の単位 ≠ 表に出した単位)"),
        "単位の食い違い 後": by("単位の食い違い 後"),
        "独立: 金額の行(『文の値』の列が金額の単位で終わる)": by("独立: 金額の行(『文の値』の列が金額の単位で終わる)"),
        "独立: 単位の食い違い 前(c13a746 の本文)": by("独立: 単位の食い違い 前(c13a746 の本文)"),
        "独立: 単位の食い違い 後": by("独立: 単位の食い違い 後"),
        "独立: 後のうち文の値が抜粋に無い": by("独立: 後のうち文の値が抜粋に無い"),
        "独立: 後のうち出典の値の単位が違う": by("独立: 後のうち出典の値の単位が違う"),
        "一致の主表示を比べた行": sum(r["一致の主表示を比べた行"] for r in rows),
        "一致の主表示を比べた行(四捨五入だけ・前)": sum(r["一致の主表示を比べた行(四捨五入だけ・前)"] for r in rows),
        "一致の主表示が文と違って見える行 前": sum(r["一致の主表示が文と違って見える行 前"] for r in rows),
        "一致の主表示が文と違って見える行 後": sum(r["一致の主表示が文と違って見える行 後"] for r in rows),
        "語の主張(出典の値あり。違う・一致)の単位の出どころ": kv(word), "語の主張で円以外の単位に直った行": kv(wchg),
        "ラベルが引けず名前のまま出た行 前(違う・一致)": by("ラベルが引けず名前のまま出た行 前(違う・一致)", ("違う", "一致")),
        "ラベルが引けず名前のまま出た行 後(違う・一致)": by("ラベルが引けず名前のまま出た行 後(違う・一致)", ("違う", "一致")),
        "英字の正規表現に当たる行 前(違う・一致)": by("英字の正規表現に当たる行 前(違う・一致)", ("違う", "一致")),
        "英字の正規表現に当たる行 後(違う・一致)": by("英字の正規表現に当たる行 後(違う・一致)", ("違う", "一致")),
        "本文の 64 桁の hex 前(c13a746・既定)": sum(r["本文の 64 桁の hex 前(c13a746・既定)"] for r in rows),
        "本文の 64 桁の hex 後(既定)": sum(r["本文の 64 桁の hex 後(既定)"] for r in rows),
        "本文の 64 桁の hex 後(--full)": sum(r["本文の 64 桁の hex 後(--full)"] for r in rows),
        "本文の『engine の指紋』の行 後": sum(r["本文の『engine の指紋』の行 後"] for r in rows),
        "同じ byte の書類数(本文 既定)": sum(1 for r in rows if r["同じ byte(本文 既定)"]),
        "同じ byte の書類数(本文 --full)": sum(1 for r in rows if r["同じ byte(本文 --full)"]),
        "同じ byte の書類数(provenance)": sum(1 for r in rows if r["同じ byte(provenance)"]),
        "provenance の body_sha256 が本文と一致した書類数": sum(1 for r in rows if r["provenance の body_sha256 が本文と一致"]),
        "行の節の割り当ての違い(前 → 後)": sum(r["行の節の割り当ての違い(前 → 後)"] for r in rows),
        "割り当てが section_of と同じ書類数": sum(1 for r in rows if r["報告の中の id の並びが section_of と同じ"]),
        "見出しの件数が section_of と同じ書類数": sum(1 for r in rows if r["節の件数が報告の見出しと同じ"]),
        "割り当ての sha256(後)": sha_text("\n".join(r["割り当ての sha256(後)"] for r in rows)),
        "割り当ての sha256(前)": sha_text("\n".join(r["割り当ての sha256(前)"] for r in rows)),
        "表題が DEI 形の書類数": sum(1 for r in rows if r["表題"].endswith("の数の点検")),
    }


def run_docs(only, std_dir, old_mod):
    lab_old = old_labels(old_mod, std_dir)
    std_labels, std_meta = RC.load_labels_with_meta(std_dir, None)
    rows = dict((p, []) for p in BOTH)
    zips = {}
    keep = {}
    excerpt = None
    checked = False
    for d in docs67():
        if only and d["docID"] not in only:
            continue
        zp = os.path.join(CACHE, d["docID"] + ".zip")
        with io.open(zp, "rb") as fh:
            zb = fh.read()
        if sha_bytes(zb) != d["sha256"]:
            raise SystemExit("書類 %s の sha256 が point_prior の記録と違う" % d["docID"])
        zips[d["docID"]] = d["sha256"]
        labels, meta = compose(std_labels, std_meta, zp)
        if not checked:
            whole = RC.load_labels_with_meta(std_dir, zp)       # CLI の --labels と --zip と同じ呼び方と、組み合わせが同じ結果になること(1 回だけ確かめる)
            if whole[0] != labels or sorted(whole[1], key=lambda m: m["file"]) != sorted(meta, key=lambda m: m["file"]):
                raise SystemExit("ラベルの組み合わせが load_labels_with_meta と違う")
            checked = True
        for p in BOTH:
            out, md, mdf, row = doc_row(d, p, labels, meta, lab_old, old_mod, zb, zp)
            rows[p].append(row)
            if p == "P25":
                keep[d["docID"]] = (out, zp)
                if not only and excerpt is None and row["節"]["違う"] >= 3 and row["節"]["要確認"] >= 3:
                    excerpt = (d["docID"], md)
    return rows, excerpt, zips, keep


def excerpt_block(doc, md):
    lines = md.split("\n")

    def rows_of(head):
        i = next(k for k, l in enumerate(lines) if l.startswith(head))
        j = next(k for k in range(i, len(lines)) if lines[k].startswith("|---"))
        k = j + 1
        got = []
        while k < len(lines) and lines[k].startswith("| "):
            got.append(lines[k])
            k += 1
        return lines[j - 1], got
    h1, r1 = rows_of("## 1. 違う")
    h2, r2 = rows_of("## 2. 要確認")
    return {"doc": doc, "profile": "P25", "表題": lines[0], "違う(先頭 3 行)": {"見出し行": h1, "行": r1[:3]},
            "要確認(先頭 3 行)": {"見出し行": h2, "行": r2[:3]}, "末尾の 2 行": lines[-3:-1], "本文の sha256": sha_text(md)}


def r2_5(keep, std_dir):
    """名簿の外の file を置いても本文が変わらない。sha256 違いの名簿の file は使わない。"""
    scratch = tempfile.mkdtemp(prefix="fix_r25_")
    roster = RC.load_roster()
    dirs = {}
    for tag in ("A", "B", "C", "D", "E"):
        dirs[tag] = os.path.join(scratch, tag)
        os.makedirs(dirs[tag])
    for name in sorted(roster):
        with io.open(os.path.join(std_dir, name), "rb") as fh:
            data = fh.read()
        for tag in ("A", "B"):                       # A = 名簿の 3 file / B = A + 名簿の外の file
            with io.open(os.path.join(dirs[tag], name), "wb") as fh:
                fh.write(data)
        if name == "jpigp_2025-11-01_lab.xml":
            with io.open(os.path.join(dirs["C"], name), "wb") as fh:    # C = jpigp だけ sha256 違い(1 byte 足した)
                fh.write(data + b" ")
        else:
            for tag in ("C", "D"):                   # D = jpigp が無い
                with io.open(os.path.join(dirs[tag], name), "wb") as fh:
                    fh.write(data)
    for tag in ("E",):                               # E = jpigp が在る標準 3 file(C・D と対にして、jpigp を使うと本文が変わる書類が在ることを見る)
        for name in sorted(roster):
            with io.open(os.path.join(std_dir, name), "rb") as fh:
                with io.open(os.path.join(dirs[tag], name), "wb") as fo:
                    fo.write(fh.read())
    extra = ('<?xml version="1.0" encoding="UTF-8"?><link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" '
             'xmlns:xlink="http://www.w3.org/1999/xlink"><link:labelLink>'
             '<link:loc xlink:type="locator" xlink:href="x.xsd#jppfs_cor_NetSales" xlink:label="loc1"/>'
             '<link:label xlink:label="lab1" xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="ja">名簿の外の売上高</link:label>'
             '<link:labelArc xlink:from="loc1" xlink:to="lab1"/></link:labelLink></link:linkbase>').encode("utf-8")
    with io.open(os.path.join(dirs["B"], "zz_extra_lab.xml"), "wb") as fh:
        fh.write(extra)
    with io.open(os.path.join(dirs["B"], "jppfs_2025-11-01_lab.xml.orig"), "wb") as fh:
        fh.write(b"not a label")
    same_ab = same_cd = changed_by_jpigp = 0
    status_c = status_d = None
    n = 0
    std = dict((tag, RC.load_labels_with_meta(dirs[tag], None)) for tag in dirs)
    for doc, (out, zp) in sorted(keep.items()):
        bodies = {}
        dei = RC.dei_from_zip(zp, out["input"]["instance_source"])
        for tag in dirs:
            labels, meta = compose(std[tag][0], std[tag][1], zp)
            bodies[tag] = (RC.render_markdown(out, labels, True, dei), meta)
        same_ab += int(bodies["A"][0] == bodies["B"][0])
        same_cd += int(bodies["C"][0] == bodies["D"][0])
        changed_by_jpigp += int(bodies["E"][0] != bodies["D"][0])
        status_c = [[m["file"], m["status"]] for m in bodies["C"][1] if m["file"].startswith("jpigp")]
        status_d = [[m["file"], m["status"]] for m in bodies["D"][1] if m["file"].startswith("jpigp")]
        n += 1
    shutil.rmtree(scratch, ignore_errors=True)
    return {"書類数": n, "名簿の外の file(zz_extra_lab.xml・jppfs_2025-11-01_lab.xml.orig)を置いても本文が同じ書類数": same_ab,
            "jpigp が sha256 違いの dir と jpigp が無い dir で本文が同じ書類数": same_cd,
            "jpigp が在ると本文が変わる書類数(歯)": changed_by_jpigp,
            "sha256 違いの dir の jpigp の状態": status_c, "jpigp が無い dir の jpigp の状態": status_d}


def r2_6(customer_out, std_dir):
    if not customer_out:
        return None
    with io.open(customer_out, "rb") as fh:
        raw = fh.read()
    out = json.loads(raw.decode("utf-8"))
    labels, _meta = RC.load_labels_with_meta(std_dir, None)
    md = RC.render_markdown(out, labels, False, None)
    md2 = RC.render_markdown(json.loads(json.dumps(out)), labels, False, None)
    by = dict((c["id"], c) for c in out["claims"])
    first = md[md.index("## 1. 違う"):md.index("## 2. 要確認")]
    doc_unit = RC.doc_unit_of(out["claims"])
    rows = []
    for tag, cid in ANSWER_IDS:
        c = by[cid]
        line = next(l for l in first.split("\n") if l.startswith("| %s |" % cid)) if ("| %s |" % cid) in first else None
        cells = [x.strip() for x in line.strip().strip("|").split(" | ")] if line else None
        shown_claim = RC.claim_value_written(c)
        shown_src, kind = RC.source_value_report(c, doc_unit)
        span = unicodedata_nfkc(c.get("span") or "")
        main_src = shown_src.split("(", 1)[0].strip()
        if kind == "written":
            a = RC.written_amount_of(c)
            same_text = shown_claim in span
            same_unit = source_unit_ok(shown_src, a)
        elif kind.startswith("word_"):
            wunit = RC.word_amount_of(c, doc_unit)[0]
            same_text = (c.get("word") or "") in span
            same_unit = main_src.endswith(wunit)
        else:
            same_text = shown_claim.replace(" ", "") in span
            same_unit = main_src.endswith(" " + (c.get("unit") or ""))
        rows.append({"答え合わせ": tag, "id": cid, "節": RC.section_of(c), "先頭の節に在る": line is not None,
                     "文の値": shown_claim, "出典の値": shown_src, "種類": kind,
                     "文の値の字が文(span)の中にそのまま在る(率は空白を除いて)": same_text,
                     "表の『文の値』の欄と一致": bool(cells) and cells[2] == shown_claim,
                     "出典の値の単位が文と同じ(語の主張は文の中でいちばん近い金額の単位)": same_unit})
    return {"入力": {"在りか": "repo の外(客の席の scratchpad)の客 A の P22 の出力 my_text.json。客の日記は repo に入れない", "sha256": sha_bytes(raw),
                   "sha256 が c13a746 の記録の C1 と同じ": sha_bytes(raw) == CUSTOMER_OUT_SHA, "claims": len(out["claims"])},
            "行": rows, "先頭の節に在る数": sum(1 for r in rows if r["先頭の節に在る"]),
            "文の値の字が文の中にそのまま在る数": sum(1 for r in rows if r["文の値の字が文(span)の中にそのまま在る(率は空白を除いて)"]),
            "単位が同じ数": sum(1 for r in rows if r["出典の値の単位が文と同じ(語の主張は文の中でいちばん近い金額の単位)"]),
            "節": dict((k, collections.Counter(RC.section_of(c) for c in out["claims"]).get(k, 0)) for k in SECTIONS),
            "同じ byte": md == md2, "報告の sha256": sha_text(md)}


def unicodedata_nfkc(s):
    return unicodedata.normalize("NFKC", s)


def r2_7():
    fp = VD.engine_fingerprint()
    res = {"sha256": {}, "sha16": {}, "HEAD からの差分(git diff --numstat)": {}}
    for rel in UNTOUCHED:
        res["sha256"][rel] = sha_file(os.path.join(ROOT, rel))
        res["sha16"][rel] = res["sha256"][rel][:16]
        n = git("diff", "--numstat", "HEAD", "--", rel, text=True).stdout.strip()
        res["HEAD からの差分(git diff --numstat)"][rel] = n if n else "0 行"
    res["封の commit 時点の sha16 と同じ"] = dict((rel, res["sha16"][rel] == UNTOUCHED_SHA16[rel]) for rel in UNTOUCHED)
    res["engine の指紋"] = dict((k, fp[k]) for k in ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files"))
    res["core/ の HEAD からの差分"] = git("diff", "--numstat", "HEAD", "--", "core", text=True).stdout.strip() or "0 行"
    res["report_customer.py の sha256"] = sha_file(os.path.join(ROOT, MODULE_REL))
    res["report_customer.py の行数"] = sum(1 for _ in io.open(os.path.join(ROOT, MODULE_REL), encoding="utf-8"))
    res["adapters/xbrl の .py の数"] = len([f for f in os.listdir(os.path.join(ROOT, "adapters", "xbrl")) if f.endswith(".py")])
    return res


def seal_numbers():
    """封 R2-1 の行から、P22 と P25 の節の件数(違う / 要確認 / 対象外 / 判断しない / 一致)を字から読む。"""
    with io.open(os.path.join(ROOT, SEAL), encoding="utf-8") as fh:
        t = fh.read()
    row = next(l for l in t.splitlines() if l.startswith("| **R2-1**"))
    out = {}
    for p in BOTH:
        m = re.search(p + r": ([\d,]+) / ([\d,]+) / ([\d,]+) / ([\d,]+) / ([\d,]+)", row)
        out[p] = dict(zip(SECTIONS, [int(x.replace(",", "")) for x in m.groups()]))
    m = {}
    for tag in ("R2-2", "R2-3"):
        r = next(l for l in t.splitlines() if l.startswith("| **%s**" % tag))
        m[tag] = r
    rng2 = re.search(r"読み取れない \*\*(\d+)〜(\d+) / ([\d,]+)\*\*", m["R2-2"])
    rng3 = re.search(r"\*\*(\d+)〜(\d+)\*\*", m["R2-3"])
    return out, (int(rng2.group(1)), int(rng2.group(2)), int(rng2.group(3).replace(",", ""))), (int(rng3.group(1)), int(rng3.group(2)))


def judge(rec, old_rec):
    seal_sec, (r2lo, r2hi, r2den), (r3lo, r3hi) = seal_numbers()
    out = {}
    agg = rec["集計"]
    # R2-1
    ok = True
    parts = []
    for p in BOTH:
        a = agg[p]
        rec_old = old_rec["集計"][p]["節"]
        same_rec = a["節"] == rec_old == seal_sec[p]
        same_old_mod = all(a["節"][k] == a["節(c13a746 の module)"][k] for k in SECTIONS)
        assign = (a["行の節の割り当ての違い(前 → 後)"] == 0 and a["割り当ての sha256(後)"] == a["割り当ての sha256(前)"]
                  and a["割り当てが section_of と同じ書類数"] == a["書類数"] == a["見出しの件数が section_of と同じ書類数"])
        ok = ok and same_rec and same_old_mod and assign
        parts.append("%s: 節 %s・記録と封と一致 %s・前の module と一致 %s・割り当ての違い %d" % (
            p, " / ".join(str(a["節"][k]) for k in SECTIONS), same_rec, same_old_mod, a["行の節の割り当ての違い(前 → 後)"]))
    out["R2-1"] = {"実測": "; ".join(parts), "判定": "当たり" if ok else "外れ"}
    # R2-2 (P25)
    b = agg["P25"]
    mis = b["単位の食い違い 後"]["計"]
    unread = b["読み取れない(金額の claim で span に同じ金額の字が無い)"]["計"]
    ind = b["独立: 単位の食い違い 後"]["計"]
    ok = mis == 0 and ind == 0 and r2lo <= unread <= r2hi
    out["R2-2"] = {"実測": "P25 の単位の食い違い 前 %d → 後 %d(試作の数え方。module の読み取りを使う)・独立に数えた食い違い 前 %d → 後 %d(金額の行 %d)・読み取れない %d / %d(金額の claim %d)" % (
        b["単位の食い違い 前(文の字の単位 ≠ 表に出した単位)"]["計"], mis, b["独立: 単位の食い違い 前(c13a746 の本文)"]["計"], ind, b["独立: 金額の行(『文の値』の列が金額の単位で終わる)"]["計"],
        unread, b["金額の claim で文の字が読めた"]["計"], b["金額の claim"]["計"]),
        "幅": {"読み取れない": [r2lo, r2hi], "分母(封)": r2den}, "判定": "当たり" if ok else "外れ"}
    # R2-3 (P25)
    n3 = b["ラベルが引けず名前のまま出た行 後(違う・一致)"]["計"]
    out["R2-3"] = {"実測": "P25 の名前のまま出た行 前 %d → 後 %d(違う %d・一致 %d)。英字の正規表現に当たる行 前 %d → 後 %d" % (
        b["ラベルが引けず名前のまま出た行 前(違う・一致)"]["計"], n3, b["ラベルが引けず名前のまま出た行 後(違う・一致)"]["違う"], b["ラベルが引けず名前のまま出た行 後(違う・一致)"]["一致"],
        b["英字の正規表現に当たる行 前(違う・一致)"]["計"], b["英字の正規表現に当たる行 後(違う・一致)"]["計"]),
        "幅": [r3lo, r3hi], "判定": "当たり" if r3lo <= n3 <= r3hi else "外れ"}
    # R2-4
    ok = True
    for p in BOTH:
        a = agg[p]
        ok = ok and a["本文の 64 桁の hex 後(既定)"] == 0 and a["本文の 64 桁の hex 後(--full)"] == 0 and a["本文の『engine の指紋』の行 後"] == 0
        ok = ok and a["同じ byte の書類数(本文 既定)"] == a["同じ byte の書類数(本文 --full)"] == a["同じ byte の書類数(provenance)"] == a["書類数"] == a["provenance の body_sha256 が本文と一致した書類数"]
    out["R2-4"] = {"実測": "hex 前(P25 既定)%d → 後 %d・同じ byte(本文・json)%d / %d × 2 profile" % (
        agg["P25"]["本文の 64 桁の hex 前(c13a746・既定)"], agg["P25"]["本文の 64 桁の hex 後(既定)"], agg["P25"]["同じ byte の書類数(provenance)"], agg["P25"]["書類数"]),
        "判定": "当たり" if ok else "外れ"}
    # R2-5
    r5 = rec.get("R2-5")
    if r5:
        ok = (r5["名簿の外の file(zz_extra_lab.xml・jppfs_2025-11-01_lab.xml.orig)を置いても本文が同じ書類数"] == r5["書類数"]
              and r5["jpigp が sha256 違いの dir と jpigp が無い dir で本文が同じ書類数"] == r5["書類数"]
              and r5["sha256 違いの dir の jpigp の状態"] == [["jpigp_2025-11-01_lab.xml", "sha256_mismatch"]]
              and r5["jpigp が無い dir の jpigp の状態"] == [["jpigp_2025-11-01_lab.xml", "missing"]]
              and r5["jpigp が在ると本文が変わる書類数(歯)"] >= 1)
        out["R2-5"] = {"実測": "名簿の外の file を置いても本文が同じ %d / %d・sha256 違いは使われない %d / %d・jpigp が在ると本文が変わる書類 %d(歯)" % (
            r5["名簿の外の file(zz_extra_lab.xml・jppfs_2025-11-01_lab.xml.orig)を置いても本文が同じ書類数"], r5["書類数"],
            r5["jpigp が sha256 違いの dir と jpigp が無い dir で本文が同じ書類数"], r5["書類数"], r5["jpigp が在ると本文が変わる書類数(歯)"]),
            "判定": "当たり" if ok else "外れ"}
    # R2-6
    c6 = rec.get("R2-6")
    if c6:
        ok = c6["先頭の節に在る数"] == 5 and c6["文の値の字が文の中にそのまま在る数"] == 5 and c6["単位が同じ数"] == 5 and c6["同じ byte"] and c6["入力"]["sha256 が c13a746 の記録の C1 と同じ"]
        out["R2-6"] = {"実測": "先頭の節「違う」に %d / 5・文の値の字が文の中にそのまま在る %d / 5・単位が同じ %d / 5" % (
            c6["先頭の節に在る数"], c6["文の値の字が文の中にそのまま在る数"], c6["単位が同じ数"]), "判定": "当たり" if ok else "外れ"}
    else:
        out["R2-6"] = {"実測": "客 A の出力が渡されなかった", "判定": "判定しない"}
    # R2-7
    c7 = rec["R2-7"]
    zero = all(v == "0 行" for v in c7["HEAD からの差分(git diff --numstat)"].values()) and c7["core/ の HEAD からの差分"] == "0 行"
    same = all(c7["封の commit 時点の sha16 と同じ"].values())
    moved = c7["engine の指紋"]["adapter_xbrl_py_sha256"] != old_rec["C5"]["engine の指紋"]["adapter_xbrl_py_sha256"]
    ok = zero and same and moved and c7["engine の指紋"]["adapter_xbrl_py_files"] == 16 and c7["engine の指紋"]["core_py_sha256"] == old_rec["C5"]["engine の指紋"]["core_py_sha256"]
    out["R2-7"] = {"実測": "report.py ほか 6 file の HEAD からの差分 0 行は %s・sha16 が封の commit 時点と同じ %s・core/ 0 行・engine の指紋は module の分だけ動いた %s(%d file)" % (
        zero, same, moved, c7["engine の指紋"]["adapter_xbrl_py_files"]), "判定": "当たり" if ok else "外れ"}
    return out


def run(stage, only, customer_out):
    t0 = time.time()
    old_rec = jload(os.path.join(ROOT, OLD_REC_REL))
    old_mod = load_old_module(old_rec)
    std_dir = labels_dir()
    roster = RC.load_roster()
    label_status = {}
    for name in sorted(roster):
        p = os.path.join(std_dir, name)
        got = sha_file(p) if os.path.isfile(p) else None
        if got != roster[name]:
            raise SystemExit("ラベル %s が名簿と合わない(%s)" % (name, got))
        label_status[name] = got
    rows, excerpt, zips, keep = run_docs(only, std_dir, old_mod)
    rec = {
        "step": "**顧客向けの日本語の報告形の直しの測定。0 USD・通信なし・engine は測る側から 1 行も変えない**",
        "環境": {
            "封": SEAL, "HEAD": git("rev-parse", "HEAD", text=True).stdout.strip(), "python": platform.python_version(),
            "比べた profile": ["P22(既定。profile を渡さない)", "P25(明示)"],
            "名簿": ROSTER_REL, "名簿の file の sha256(起動時に照合)": label_status,
            "前の module": "commit %s の %s(git show で取り出し、c13a746 の記録の C5 の sha256 %s と一致を確かめた)" % (OLD_COMMIT, MODULE_REL, old_rec["C5"]["report_customer.py の sha256"][:16]),
            "前のラベル": "jpcrp・jppfs の 2 file(c13a746 当時)", "後のラベル": "名簿の 3 file(jpcrp・jppfs・jpigp)+ 書類の ZIP の XBRL/PublicDoc/*_lab.xml(CLI の --labels と --zip と同じ組み方)",
            "cache": "~/.cache/audit-core/edinet/*.zip(手元の file だけ。取りに行かない)",
            "通信": "この script は urllib・socket・http を import しない。adapters は urllib を import するが接続は起きない",
            "費用": "0 USD",
        },
        "書類の数": {"経営分析の文を持つ": len(rows["P22"])},
        "書類別": rows,
        "集計": dict((p, aggregate(rows[p])) for p in BOTH),
    }
    if stage == "all":
        rec["入力の sha256"] = {"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)": zips,
                              PP_REL: sha_file(os.path.join(ROOT, PP_REL)), OLD_REC_REL: sha_file(os.path.join(ROOT, OLD_REC_REL)),
                              "seal": sha_file(os.path.join(ROOT, SEAL))}
        rec["R2-5"] = r2_5(keep, std_dir)
        rec["R2-6"] = r2_6(customer_out, std_dir)
        rec["R2-7"] = r2_7()
        rec["抜粋"] = excerpt_block(*excerpt) if excerpt else None
        rec["所要秒"] = {"合計": round(time.time() - t0, 1), "verify 合計": round(sum(r["verify 秒"] for p in BOTH for r in rows[p]), 1)}
        rec["予測の判定"] = judge(rec, old_rec)
        rec["limits"] = [
            "判定(state・reason・pointer)と節の割り当ては変えていない。『違う』が正しい文に出る率は報告の形では減らない",
            "文の数の読み取りの崩れ(『2兆3,471億円』が 3,471億円になる等)は engine(extract)の側で、報告では直せない",
            "語の主張の単位を書類の単位に落とした行は、文から読み取っていない(単位の出どころが doc の行)",
            "『表題』の書類の種類は DEI の DocumentTypeDEI(第三号様式 等)。書類の題名(有価証券報告書)ではない",
            "数の字の途中で切れた抜粋は、末尾の数と先頭が小数点で始まる数だけ落とす。先頭が桁の途中で切れた数(『26年』が『2026年』の途中)は見分けられず落とさない",
        ]
    return rec


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="顧客向け報告形の直しの測定(0 USD・通信なし)")
    ap.add_argument("--stage", choices=["docs", "all"], default="all")
    ap.add_argument("--out", default=None, help="記録の出力先。--stage all の既定は " + OUT_REL)
    ap.add_argument("--docs", default=None, help="docID をコンマ区切りで絞る(軽い走らせ直し用)")
    ap.add_argument("--customer-out", default=None, help="客 A の P22 の出力 JSON(repo の外)")
    a = ap.parse_args(argv)
    out = a.out
    if out is None:
        if a.stage != "all" or a.docs:
            raise SystemExit("--stage all 以外か --docs のときは --out を渡す(正本の記録を上書きしない)")
        out = os.path.join(ROOT, OUT_REL)
    rec = run(a.stage, set(a.docs.split(",")) if a.docs else None, a.customer_out)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("=== 顧客向け報告形の直し(手元の cache・鍵なし・0 USD)===")
    for k, v in sorted(rec.get("予測の判定", {}).items()):
        print("%s: %s → %s" % (k, v["実測"], v["判定"]))
    print("記録: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
