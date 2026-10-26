# -*- coding: utf-8 -*-
u"""顧客向けの日本語の報告形(``adapters/xbrl/report_customer.py``)の測定 ― 封 ``docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md`` §2(C-1・C-2・C-2b・C-3・C-4・C-5)。

    cd audit-core
    python3 measure/xbrl_customer_report_2026-10-21.py --customer-out <客 A の P22 の出力 JSON> --answer-key <答え合わせの表>   # 記録 fixtures/xbrl/customer_report_2026-10-21.json を書く
    python3 measure/xbrl_customer_report_2026-10-21.py --stage docs --docs S100YYK8,S100YZ7E --out <file>                    # 軽い走らせ直し(--out 必須)

**0 USD・通信なし・鍵の値は読まない。** 書類は ``~/.cache/audit-core/edinet/*.zip`` の手元の cache だけ(無い書類は取りに行かない)。標準ラベルは
``~/.cache/audit-core/edinet-taxonomy/2025-11-01``(repo の外。起動時に sha256 を照合)。engine(``core/``・``adapters/``)は測る側から 1 行も変えない。
客 A の出力と答え合わせの表は repo の外(客の日記は repo に入れない)。記録に置くのは在りかの名前と sha256 と、数だけの行(文の抜粋は置かない)。

  C-1  客 A の P22 の出力(39 claim)を新しい報告にして、答え合わせの 5 件(N001・N007・N010・N015・T009)が先頭の節「違う」に在るか、出典の値の単位が文と同じか。
  C-2  67 書類の無改変(既定 profile = P22)の節の件数。
  C-2b 同じ 67 書類を P25 明示で。
  C-3  理由の日本語表は登録簿の理由の全部(16)を網羅し、1 つ消すと網羅の検査が赤になる。実測の reason が表の外に出ていないか。
  C-4  同じ JSON から 2 回で同じバイト列(67 書類 × 2 profile)・``report.py`` の golden が不変。
  C-5  ``report.py``・``verify_document.py`` は 0 行。engine の指紋は module の分だけ動く(15 → 16 file)。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import io
import json
import os
import platform
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

from adapters.xbrl import instance as I            # noqa: E402
from adapters.xbrl import recipes as R             # noqa: E402
from adapters.xbrl import registry_setup as RS     # noqa: E402
from adapters.xbrl import report as RP             # noqa: E402
from adapters.xbrl import report_customer as RC    # noqa: E402
from adapters.xbrl import verify_document as VD    # noqa: E402
from adapters.xbrl import vocabulary as V          # noqa: E402

SEAL = "docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md"
OUT_REL = "fixtures/xbrl/customer_report_2026-10-21.json"
PP_REL = "fixtures/xbrl/point_prior_2026-10-20.json"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
BOTH = ("P22", "P25")           # 既定(P22)と P25 明示。既定は profile=None で呼ぶ(既定が動けば記録も動く = 既定の報告を測る)
ANSWER_IDS = ((u"E1 前期を当期", "N001"), (u"E2 末尾桁", "N007"), (u"E5 率", "N010"), (u"E3 単位", "N015"), (u"E4 向き", "T009"))
CASES = ("entry_output_S100Z4N9_original_2026-10-13.json", "entry_output_S100Z4Q1_ai_prose_2026-10-13.json")
GOLDENS = ("report_golden_S100Z4N9_original_2026-10-13.md", "report_golden_S100Z4Q1_ai_prose_2026-10-13.md")
UNTOUCHED = ("adapters/xbrl/report.py", "adapters/xbrl/verify_document.py", "adapters/xbrl/vocabulary.py",
             "adapters/xbrl/recipes.py", "adapters/xbrl/registry_setup.py")
SECTIONS = (u"違う", u"要確認", u"対象外", u"判断しない", u"一致")


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with io.open(p, "rb") as fh:
        return sha_bytes(fh.read())


def sha_text(s):
    return sha_bytes(s.encode("utf-8"))


#: 報告の末尾の指紋の行。`engine の指紋: adapters … / core … / git <HEAD>` ― git の欄は HEAD で変わり、adapters の欄は engine の file で変わる。
#: 報告の「本体」= この 1 行だけを除いた残り。除く行は字で 1 通り(この prefix で始まる行)で、ちょうど 1 行でなければ止まる。
ENGINE_LINE_PREFIX = u"<sub>engine の指紋:"


def body_of(md):
    lines = md.split("\n")
    hit = [i for i, l in enumerate(lines) if l.startswith(ENGINE_LINE_PREFIX)]
    if len(hit) != 1:
        raise SystemExit(u"報告の末尾の指紋の行が %d 行ある(ちょうど 1 行でなければならない)" % len(hit))
    return u"\n".join(lines[:hit[0]] + lines[hit[0] + 1:])


def body_sha(md):
    return sha_text(body_of(md))


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def kv(d):
    return dict(sorted(d.items()))


def labels_dir():
    return I.taxonomy_dir() if os.path.isdir(I.taxonomy_dir()) else os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-taxonomy", "2025-11-01")


def label_shas():
    """ラベル 2 file の sha256 を起動時に照合して返す(合わなければ止める)。"""
    d = labels_dir()
    out = {}
    for _ns, fn, want in I.TAXONOMY_LABEL_FILES:
        got = sha_file(os.path.join(d, fn))
        if got != want:
            raise SystemExit(u"ラベル %s の sha256 が違う: %s" % (fn, got))
        out[fn] = got
    return out


def docs67():
    fx = jload(os.path.join(ROOT, PP_REL))
    return [d for d in fx[u"書類"] if d[u"区分"] == u"文あり"]


def doc_row(d, profile, labels, zb):
    """1 書類・1 profile: verify → 報告 2 回 → 節の件数・内訳・reason・決定論。"""
    t0 = time.time()
    # 2026-10-23(既定を P22 -> P26 に切り替える 段 2。封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md §1-2): 記録は既定が P22 のときに測った。P22 は profile を渡さず(None)でなく**明示**して
    # 測った当時の値を再現する(None のままだと既定が P26 の今は P26 になる)。記録の字(「比べた profile」の P22(既定。profile を渡さない))は測った当時のもので直さない。
    out = VD.verify_document(zb, profile, None)
    t1 = time.time()
    md1 = RC.render_markdown(out, labels, False)
    md1f = RC.render_markdown(out, labels, True)
    md2 = RC.render_markdown(json.loads(json.dumps(out)), labels, False)
    md2f = RC.render_markdown(json.loads(json.dumps(out)), labels, True)
    sec = collections.Counter()
    kinds = collections.Counter()
    reasons = {s: collections.Counter() for s in SECTIONS}
    states = collections.Counter()
    unit_bad = 0
    yen_unit_words = collections.Counter()   # 文の字に百万円・千円・億円・兆円があるが claim の単位が円の行(span の字から数えた概数)
    unit_checked = 0
    pointer_raw = 0         # 日本語に直らず字のまま残った pointer(op の表に無い)
    label_missing = 0       # 「違う」「一致」の行のうち、標準ラベルが無く要素名のままの要素を持つ行
    label_missing_ns = collections.Counter()    # 同じ行を、ラベルの無い要素の名前空間(の接頭辞)ごとに(1 行が複数の名前空間を持てば複数に数える)
    for c in out["claims"]:
        s = RC.section_of(c)
        sec[s] += 1
        states[c["state"]] += 1
        if s == RC.SECTION_MATCH:
            kinds[RC.match_kind(c)] += 1
        if c.get("reason"):
            reasons[s][c["reason"]] += 1
        if c.get("unit") == u"円" and re.search(u"百万円|千円|億円|兆円", c.get("span") or u""):
            yen_unit_words[s] += 1
        if s == RC.SECTION_MISMATCH and c.get("unit") in RC.UNIT_SCALE and c.get("recomputed") is not None:
            unit_checked += 1
            if not RC.source_value_ja(c).endswith(" " + c["unit"]):
                unit_bad += 1
        if s in (RC.SECTION_MISMATCH, RC.SECTION_MATCH):
            miss = set()
            for p in c.get("pointers") or []:
                name, _ctx = RC.split_pointer(p)
                if name is None:
                    if p not in RC.OP_JA:
                        pointer_raw += 1
                elif not labels.get(name.replace(":", "_")):
                    miss.add(name.split(":")[0].split("-")[0] if name.split(":")[0].startswith("jp") else u"会社ごと")
            if miss:
                label_missing += 1
                label_missing_ns.update(miss)
    return out, md1, md1f, {
        u"doc": d[u"docID"], u"profile": out["profile"], u"claims": len(out["claims"]),
        u"節": dict((k, sec.get(k, 0)) for k in SECTIONS),
        u"一致の内訳": dict((k, kinds.get(k, 0)) for k in RC.MATCH_KINDS),
        u"state": kv(states),
        u"reason(要確認)": kv(reasons[RC.SECTION_CHECK]), u"reason(対象外)": kv(reasons[RC.SECTION_OUT]), u"reason(判断しない)": kv(reasons[RC.SECTION_NOT_JUDGED]),
        u"その他の節": sec.get(RC.SECTION_OTHER, 0),
        u"同じ byte(既定)": md1 == md2, u"同じ byte(--full)": md1f == md2f,
        u"報告の本体の sha256": body_sha(md1), u"報告 --full の本体の sha256": body_sha(md1f), u"報告の行数": md1.count("\n") + 1,
        u"単位の検査": {u"文が金額の単位で出典の値がある「違う」": unit_checked, u"出典の値の単位が文と違う": unit_bad},
        u"字のまま残った pointer": pointer_raw, u"ラベル無しの要素を持つ行(違う・一致)": label_missing,
        u"ラベル無しの名前空間別の行数": kv(label_missing_ns),
        u"文の字に百万円・千円・億円・兆円があるが claim の単位が円の行(span の字から数えた概数)": dict((k, yen_unit_words.get(k, 0)) for k in SECTIONS),
        u"verify 秒": round(t1 - t0, 2),
    }


def aggregate(rows):
    sec = collections.Counter()
    kinds = collections.Counter()
    reasons = {u"要確認": collections.Counter(), u"対象外": collections.Counter(), u"判断しない": collections.Counter()}
    states = collections.Counter()
    for r in rows:
        sec.update(r[u"節"])
        kinds.update(r[u"一致の内訳"])
        states.update(r[u"state"])
        for k in reasons:
            reasons[k].update(r[u"reason(%s)" % k])
    return {
        u"書類数": len(rows), u"claims": sum(r[u"claims"] for r in rows),
        u"節": dict((k, sec.get(k, 0)) for k in SECTIONS), u"節の和": sum(sec.get(k, 0) for k in SECTIONS),
        u"その他の節": sum(r[u"その他の節"] for r in rows),
        u"一致の内訳": dict((k, kinds.get(k, 0)) for k in RC.MATCH_KINDS),
        u"state": kv(states),
        u"reason(要確認)": kv(reasons[u"要確認"]), u"reason(対象外)": kv(reasons[u"対象外"]), u"reason(判断しない)": kv(reasons[u"判断しない"]),
        u"同じ byte(全部)": all(r[u"同じ byte(既定)"] and r[u"同じ byte(--full)"] for r in rows),
        u"単位の検査": {u"文が金額の単位で出典の値がある「違う」": sum(r[u"単位の検査"][u"文が金額の単位で出典の値がある「違う」"] for r in rows),
                      u"出典の値の単位が文と違う": sum(r[u"単位の検査"][u"出典の値の単位が文と違う"] for r in rows)},
        u"字のまま残った pointer": sum(r[u"字のまま残った pointer"] for r in rows),
        u"ラベル無しの要素を持つ行(違う・一致)": sum(r[u"ラベル無しの要素を持つ行(違う・一致)"] for r in rows),
        u"ラベル無しの名前空間別の行数": kv(sum((collections.Counter(r[u"ラベル無しの名前空間別の行数"]) for r in rows), collections.Counter())),
        u"文の字に百万円・千円・億円・兆円があるが claim の単位が円の行(span の字から数えた概数)": dict((k, sum(r[u"文の字に百万円・千円・億円・兆円があるが claim の単位が円の行(span の字から数えた概数)"][k] for r in rows)) for k in SECTIONS),
    }


def run_docs(only, labels):
    rows = {p: [] for p in BOTH}
    excerpt = None
    zips = {}
    for d in docs67():
        if only and d[u"docID"] not in only:
            continue
        zp = os.path.join(CACHE, d[u"docID"] + ".zip")
        with io.open(zp, "rb") as fh:
            zb = fh.read()
        if sha_bytes(zb) != d[u"sha256"]:
            raise SystemExit(u"書類 %s の sha256 が point_prior の記録と違う" % d[u"docID"])
        zips[d[u"docID"]] = d[u"sha256"]
        for p in BOTH:
            out, md, mdf, row = doc_row(d, p, labels, zb)
            rows[p].append(row)
            if p == "P25" and not only and excerpt is None and row[u"節"][u"違う"] >= 5 and row[u"節"][u"要確認"] >= 5:
                excerpt = (d[u"docID"], out, labels)
    return rows, excerpt, zips


def excerpt_block(doc, out, labels):
    """P25 明示の 1 書類の報告から、「違う」「要確認」の先頭 5 行ずつ(報告の行そのまま)。"""
    md = RC.render_markdown(out, labels, False)
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
    h1, r1 = rows_of(u"## 1. 違う")
    h2, r2 = rows_of(u"## 2. 要確認")
    return {u"doc": doc, u"profile": out["profile"], u"違う(先頭 5 行)": {u"見出し行": h1, u"行": r1[:5]},
            u"要確認(先頭 5 行)": {u"見出し行": h2, u"行": r2[:5]}, u"報告の本体の sha256": body_sha(md)}


def c1(customer_out, answer_key, labels):
    if not customer_out:
        return None
    out = jload(customer_out)
    md = RC.render_markdown(out, labels, False)
    md2 = RC.render_markdown(json.loads(json.dumps(out)), labels, False)
    by = dict((c["id"], c) for c in out["claims"])
    first = md[md.index(u"## 1. 違う"):md.index(u"## 2. 要確認")]
    rows = []
    for tag, cid in ANSWER_IDS:
        c = by[cid]
        sec = RC.section_of(c)
        rows.append({u"答え合わせ": tag, u"id": cid, u"節": sec, u"先頭の節に在る": (u"| %s |" % cid) in first,
                     u"文の値": RC.claim_value_ja(c), u"出典の値": RC.source_value_ja(c), u"文の単位": c.get("unit"),
                     u"出典の値の単位が文と同じ(語の主張は円)": RC.source_value_ja(c).endswith(" " + (c.get("unit") or u"円"))})
    sec = collections.Counter(RC.section_of(c) for c in out["claims"])
    return {
        u"入力": {u"在りか": u"repo の外(客の席の scratchpad)の客 A の P22 の出力 my_text.json。客の日記は repo に入れない", u"sha256": sha_file(customer_out),
                u"profile": out["profile"], u"claims": len(out["claims"]), u"git_commit(出力を作った engine)": out["engine"].get("git_commit")},
        u"答え合わせの表": {u"在りか": u"repo の外(客の席の answer_key.md)", u"sha256": sha_file(answer_key) if answer_key else None},
        u"行": rows, u"先頭の節に在る数": sum(1 for r in rows if r[u"先頭の節に在る"]), u"単位が文と同じ数": sum(1 for r in rows if r[u"出典の値の単位が文と同じ(語の主張は円)"]),
        u"節": dict((k, sec.get(k, 0)) for k in SECTIONS), u"同じ byte": md == md2, u"報告の sha256": sha_text(md),
    }


def c3(rows_by_profile):
    reg = sorted(set(RS._POINTER_NOT_FOUND_REASONS) | set(RS._UNVERIFIABLE_REASONS))
    table = sorted(RC.REASON_JA)
    miss_when_removed = {}
    for k in table:
        t = set(table) - {k}
        miss_when_removed[k] = sorted(set(reg) - t)
    seen = collections.Counter()
    for p, rows in rows_by_profile.items():
        for r in rows:
            for key in (u"reason(要確認)", u"reason(対象外)", u"reason(判断しない)"):
                for k, v in r[key].items():
                    seen[(p, k)] += v
    seen_names = sorted({k for (_p, k) in seen})
    return {
        u"登録簿の理由": {u"POINTER_NOT_FOUND": list(RS._POINTER_NOT_FOUND_REASONS), u"UNVERIFIABLE": list(RS._UNVERIFIABLE_REASONS), u"数": len(reg)},
        u"UNBOUND_REASON_STATE の key の数": len(R.UNBOUND_REASON_STATE),
        u"登録簿 − UNBOUND_REASON_STATE": sorted(set(reg) - set(R.UNBOUND_REASON_STATE)),
        u"UNBOUND_REASON_STATE − 登録簿": sorted(set(R.UNBOUND_REASON_STATE) - set(reg)),
        u"理由の表の key の数": len(table), u"理由の表 − 登録簿": sorted(set(table) - set(reg)), u"登録簿 − 理由の表": sorted(set(reg) - set(table)),
        u"1 つ消したときの網羅の検査(消した key → 表に無い登録簿の理由)": miss_when_removed,
        u"実測に出た reason": seen_names, u"実測に出た reason のうち表の外": sorted(set(seen_names) - set(table)),
        u"実測に出なかった登録簿の理由": sorted(set(reg) - set(seen_names)),
        u"profile 別の reason の件数": dict((p, dict((k, v) for (pp, k), v in sorted(seen.items()) if pp == p)) for p in rows_by_profile),
    }


def c4():
    res = []
    for js, md in zip(CASES, GOLDENS):
        out = jload(os.path.join(ROOT, "fixtures", "xbrl", js))
        with io.open(os.path.join(ROOT, "fixtures", "xbrl", md), "r", encoding="utf-8", newline="") as fh:
            want = fh.read()
        got = RP.render_markdown(out)
        a = RC.render_markdown(out, None, False)
        b = RC.render_markdown(json.loads(json.dumps(out)), None, False)
        res.append({u"入力": js, u"report.py の golden": md, u"report.py の出力が golden とバイト一致": got == want, u"golden の sha256": sha_text(want),
                    u"新しい報告の sha256": sha_text(a), u"新しい報告が 2 回で同じ": a == b})
    return res


def c5():
    fp = VD.engine_fingerprint()
    res = {u"sha256": {}, u"HEAD からの差分(git diff --numstat)": {}}
    for rel in UNTOUCHED:
        res[u"sha256"][rel] = sha_file(os.path.join(ROOT, rel))
        n = git("diff", "--numstat", "HEAD", "--", rel).stdout.strip()
        res[u"HEAD からの差分(git diff --numstat)"][rel] = n if n else u"0 行"
    res[u"engine の指紋"] = {k: fp[k] for k in ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files")}
    res[u"adapters/xbrl の .py の数"] = len([f for f in os.listdir(os.path.join(ROOT, "adapters", "xbrl")) if f.endswith(".py")])
    res[u"core/ の HEAD からの差分"] = git("diff", "--numstat", "HEAD", "--", "core").stdout.strip() or u"0 行"
    res[u"report_customer.py の sha256"] = sha_file(os.path.join(ROOT, "adapters", "xbrl", "report_customer.py"))
    res[u"report_customer.py の行数"] = sum(1 for _ in io.open(os.path.join(ROOT, "adapters", "xbrl", "report_customer.py"), encoding="utf-8"))
    return res


def run(stage, only, customer_out, answer_key):
    t0 = time.time()
    shas = label_shas()
    labels = RC.load_labels(labels_dir())
    rows, excerpt, zips = run_docs(only, labels)
    rec = {
        u"step": u"**顧客向けの日本語の報告形の測定。0 USD・通信なし・engine は測る側から 1 行も変えない**",
        u"環境": {
            u"封": SEAL, u"HEAD": git("rev-parse", "HEAD").stdout.strip(), u"python": platform.python_version(),
            u"DEFAULT_PROFILE": V.DEFAULT_PROFILE, u"比べた profile": [u"P22(既定。profile を渡さない)", u"P25(明示)"],
            u"ラベル 2 file の sha256(起動時に照合)": shas,
            u"cache": u"~/.cache/audit-core/edinet/*.zip(手元の file だけ。取りに行かない)",
            u"通信": u"この script は urllib・socket・http を import しない。adapters は urllib を import するが接続は起きない",
            u"費用": u"0 USD",
        },
        u"書類の数": {u"経営分析の文を持つ": len(rows["P22"])},
        u"書類別": rows,
        u"集計": dict((p, aggregate(rows[p])) for p in BOTH),
    }
    if stage == "all":
        rec[u"入力の sha256"] = {
            u"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)": zips,
            PP_REL: sha_file(os.path.join(ROOT, PP_REL)),
            u"seal": sha_file(os.path.join(ROOT, SEAL)),
        }
        rec[u"C1"] = c1(customer_out, answer_key, labels)
        rec[u"C3"] = c3(rows)
        rec[u"C4"] = c4()
        rec[u"C5"] = c5()
        rec[u"抜粋"] = excerpt_block(*excerpt) if excerpt else None
        rec[u"所要秒"] = {u"合計": round(time.time() - t0, 1), u"verify 合計": round(sum(r[u"verify 秒"] for p in BOTH for r in rows[p]), 1)}
        rec[u"予測の判定"] = judge(rec)
        rec[u"limits"] = [
            u"「違う」が正しい文に出る率は報告の形では減らない(既定 P22 で 違う の率は変わらない。P25 明示で減るのは P24・P25 の engine の直しの効き目で、この封の効き目ではない)",
            u"no_same_value の名指した当期の値は verify_document の出力に欄が無く、報告に出さない(理由の 1 行だけ)",
            u"標準ラベルは repo の外。IFRS(jpigp_cor)と会社ごとのセグメント member はラベル file に無く要素名のまま",
            u"語の主張の出典の値は単位が無いので円で出る。report.py 末尾の「率・差は文と同じ単位」は差については実物と違う(差も円)― report.py は触らない",
            u"--labels の dir の sha256 は報告の module では照合しない(照合はこの測定の起動時と instance.py)",
        ]
    return rec


def rng(seal_text, tag, label):
    """封の予測の表から ``**a〜b**`` を取り出す(判定に使う幅は封の字から読む)。"""
    row = next(l for l in seal_text.splitlines() if l.startswith(u"| **%s**" % tag))
    return row


def judge(rec):
    """封 §2 の判定。幅は封の字(C-2・C-2b)から取る。"""
    with io.open(os.path.join(ROOT, SEAL), encoding="utf-8") as fh:
        seal = fh.read()

    def ranges(tag):
        row = rng(seal, tag, None)
        nums = [int(x.replace(",", "")) for x in re.findall(r"\*\*([\d,]+)\*\*", row.split("|")[2])]
        spans = [(int(a.replace(",", "")), int(b.replace(",", ""))) for a, b in re.findall(r"\*\*([\d,]+)〜([\d,]+)\*\*", row.split("|")[2])]
        return nums, spans
    out = {}
    a = rec[u"集計"]["P22"]
    n, sp = ranges("C-2")
    s = a[u"節"]
    ok = (s[u"違う"] == n[0] and sp[0][0] <= s[u"要確認"] <= sp[0][1] and sp[1][0] <= s[u"対象外"] + s[u"判断しない"] <= sp[1][1]
          and s[u"一致"] == 4242 and a[u"節の和"] == a[u"claims"] == 7799)
    out["C-2"] = {u"実測": u"違う %d / 要確認 %d / 対象外 + 判断しない %d / 一致 %d / 和 %d" % (s[u"違う"], s[u"要確認"], s[u"対象外"] + s[u"判断しない"], s[u"一致"], a[u"節の和"]),
                  u"幅": {u"違う": n[0], u"要確認": list(sp[0]), u"対象外 + 判断しない": list(sp[1]), u"一致": 4242, u"和": 7799}, u"判定": u"当たり" if ok else u"外れ"}
    b = rec[u"集計"]["P25"]
    n, sp = ranges("C-2b")
    s = b[u"節"]
    ok = (s[u"違う"] == n[0] and s[u"一致"] == n[1] and sp[0][0] <= s[u"対象外"] + s[u"判断しない"] <= sp[0][1]
          and sp[1][0] <= s[u"要確認"] <= sp[1][1] and b[u"節の和"] == b[u"claims"] == 7799)
    out["C-2b"] = {u"実測": u"違う %d / 一致 %d / 対象外 + 判断しない %d / 要確認 %d / 和 %d" % (s[u"違う"], s[u"一致"], s[u"対象外"] + s[u"判断しない"], s[u"要確認"], b[u"節の和"]),
                   u"幅": {u"違う": n[0], u"一致": n[1], u"対象外 + 判断しない": list(sp[0]), u"要確認": list(sp[1]), u"和": 7799}, u"判定": u"当たり" if ok else u"外れ"}
    c = rec[u"C3"]
    ok = (c[u"登録簿の理由"][u"数"] == 16 and not c[u"登録簿 − 理由の表"] and not c[u"理由の表 − 登録簿"]
          and all(v == [k] for k, v in c[u"1 つ消したときの網羅の検査(消した key → 表に無い登録簿の理由)"].items())
          and not c[u"実測に出た reason のうち表の外"])
    out["C-3"] = {u"実測": u"登録簿 %d・表 %d・差 0・1 つ消すと 16 / 16 が赤・実測の reason の表の外 %d" % (c[u"登録簿の理由"][u"数"], c[u"理由の表の key の数"], len(c[u"実測に出た reason のうち表の外"])),
                  u"判定": u"当たり" if ok else u"外れ"}
    c4r = rec[u"C4"]
    ok = (rec[u"集計"]["P22"][u"同じ byte(全部)"] and rec[u"集計"]["P25"][u"同じ byte(全部)"]
          and all(x[u"report.py の出力が golden とバイト一致"] and x[u"新しい報告が 2 回で同じ"] for x in c4r))
    out["C-4"] = {u"実測": u"67 書類 × 2 profile で同じ byte・report.py の golden 2 本とバイト一致", u"判定": u"当たり" if ok else u"外れ"}
    if rec[u"C1"] is not None:
        k = rec[u"C1"]
        ok = k[u"先頭の節に在る数"] == 5 and k[u"単位が文と同じ数"] == 5
        out["C-1"] = {u"実測": u"先頭の節「違う」に %d / 5・出典の値の単位が文と同じ %d / 5" % (k[u"先頭の節に在る数"], k[u"単位が文と同じ数"]), u"判定": u"当たり" if ok else u"外れ"}
    else:
        out["C-1"] = {u"実測": u"客 A の出力が渡されなかった", u"判定": u"判定しない"}
    c5r = rec[u"C5"]
    zero = all(v == u"0 行" for v in c5r[u"HEAD からの差分(git diff --numstat)"].values())
    out["C-5"] = {u"実測": u"report.py・verify_document.py・vocabulary.py・recipes.py・registry_setup.py の HEAD からの差分 0 行は %s・engine の指紋 file 数 %d" % (zero, c5r[u"engine の指紋"][u"adapter_xbrl_py_files"]),
                  u"判定": u"当たり" if (zero and c5r[u"engine の指紋"][u"adapter_xbrl_py_files"] == 16) else u"外れ"}
    return out


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=u"顧客向け報告形の測定(0 USD・通信なし)")
    ap.add_argument("--stage", choices=["docs", "all"], default="all")
    ap.add_argument("--out", default=None, help=u"記録の出力先。--stage all の既定は " + OUT_REL)
    ap.add_argument("--docs", default=None, help=u"docID をコンマ区切りで絞る(軽い走らせ直し用)")
    ap.add_argument("--customer-out", default=None, help=u"客 A の P22 の出力 JSON(repo の外)")
    ap.add_argument("--answer-key", default=None, help=u"客 A の答え合わせの表(repo の外。sha256 だけ記録する)")
    a = ap.parse_args(argv)
    out = a.out
    if out is None:
        if a.stage != "all" or a.docs:
            raise SystemExit(u"--stage all 以外か --docs のときは --out を渡す(正本の記録を上書きしない)")
        out = os.path.join(ROOT, OUT_REL)
    rec = run(a.stage, set(a.docs.split(",")) if a.docs else None, a.customer_out, a.answer_key)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write(u"\n")
    print(u"=== 顧客向け報告形(手元の cache・鍵なし・0 USD)===")
    for k, v in sorted(rec.get(u"予測の判定", {}).items()):
        print(u"%s: %s → %s" % (k, v[u"実測"], v[u"判定"]))
    print(u"記録: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
