# -*- coding: utf-8 -*-
u"""10 分の再現の儀式 ― 封 ``docs/XBRL_RITUAL_SEAL_2026-10-20.md``。

買い手が clone した直後に、**API 鍵なし・0 USD・初回のラベル取得を除き通信なし** で、誤りを入れたとき何を通し何を止めるかを自分の手で見る入口。

    cd audit-core
    python3 measure/ritual_2026-10-20.py --out <dir>

引数は出力先だけ。既定の profile は ``vocabulary.DEFAULT_PROFILE``。入力は repo に同梱した 1 書類
``fixtures/xbrl/ai_prose_instance_2026-10-09.zip`` だけ(書類の取得と鍵は使わない)。ただし engine が読む
**標準タクソノミのラベル 2 file(jppfs・jpcrp の 2025-11-01 版、約 8 MB)は要る** ― repo の外の
``~/.cache/audit-core/edinet-taxonomy/2025-11-01/``(``EDINET_TAXONOMY_DIR`` で変えられる)。取り方と sha256 は
``fixtures/xbrl/TAXONOMY_LABELS_README.md``。起動時に存在と sha256 を確かめ、無ければ案内を出して rc=2 で止まる。engine(``core/``・``adapters/``)は
1 行も変えず、``measure/false_pass_2026-10-14.py`` の ``run_doc`` を import して使う(同じ注入・同じ判定)。

手順
  (a) ``verify_document(zb, profile, None)`` で素の書類を検証し、claim の数と state の分布を出す。
  (b) 経営分析の文の数を 1 文に 1 つずつ変えて(V1 = 最小の桁の 1 字 / V2 = 値を ±1 最小単位。25 件ずつの束)
      ``verify_document(zb, profile, text)`` で検証し直し、注入 1 件ごとに 止めた(VALUE_MISMATCH)/ 通した(GROUNDED のまま)を数える。
  (c) 通した件数を先頭に ``<dir>/ritual.json`` と ``<dir>/ritual.md`` へ書く。
  (d) 画面には 10 行以内の要約を出す。

注入の道具は 2 型(最小の桁の 1 字 / ±1 最小単位)だけ。通した件数の分け方(退化値 / 丸めの帯の中 / 帯の外)は
値の差だけで決める: 差が 0 = 退化値(字は変わるが値が変わらない)、差が表記の最後の 1 桁(``±1 最小単位``)以内 = 帯の中、
それより大きい = 帯の外。
"""
from __future__ import print_function

import argparse
import hashlib
import importlib.util
import io
import json
import os
import platform
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

from adapters.xbrl import instance as I  # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V  # noqa: E402

SEAL = "docs/XBRL_RITUAL_SEAL_2026-10-20.md"
ZIP_REL = "fixtures/xbrl/ai_prose_instance_2026-10-09.zip"
ZIP_SHA256 = "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799"
ZIP_BYTES = 580260
DOC_ID = "S100Z4Q1"
LABEL_SHA_REL = "fixtures/xbrl/taxonomy_labels_sha256.txt"
#: 画面に出さないが記録に残す、鍵の「名前」(値は読まない・書かない)
KEY_NAMES = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "EDINET_API_KEY", "OPENAI_API_KEY")

CLASS_DEGENERATE = u"退化値(字は変わるが値が変わらない)"
CLASS_IN_BAND = u"丸めの帯の中(±1 最小単位)"
CLASS_OUT_BAND = u"帯の外(±1 最小単位より大きい)"


def _load_false_pass():
    sp = importlib.util.spec_from_file_location("false_pass_for_ritual", os.path.join(HERE, "false_pass_2026-10-14.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def check_labels():
    u"""標準タクソノミのラベル 2 file の存在と sha256(``taxonomy_labels_sha256.txt`` と engine の字の両方)を確かめる。
    返り値は ``({file: sha256}, None)`` か ``(None, 理由)``。"""
    d = I.taxonomy_dir()
    listed = {}
    with io.open(os.path.join(ROOT, LABEL_SHA_REL), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                h, fn = line.split(None, 1)
                listed[fn.strip()] = h
    got = {}
    for _ns, fn, sha in I.TAXONOMY_LABEL_FILES:
        p = os.path.join(d, fn)
        if not os.path.exists(p):
            return None, u"%s が %s に無い" % (fn, d)
        with io.open(p, "rb") as fh:
            h = hashlib.sha256(fh.read()).hexdigest()
        if h != sha or listed.get(fn) != sha:
            return None, u"%s の sha256 が違う(%s)" % (fn, h)
        got[fn] = h
    return got, None


def label_guidance(reason):
    d = I.taxonomy_dir()
    return u"\n".join([
        u"儀式を始められない: 標準タクソノミのラベル(jppfs・jpcrp の 2025-11-01 版、約 8 MB)が使えない ― %s。" % reason,
        u"初回に 1 回だけ EDINET から取る(通信はこの 1 回だけ。鍵は要らない):",
        u"  mkdir -p %s && cd %s" % (d, d),
        u"  curl -sS -O http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/label/jppfs_2025-11-01_lab.xml",
        u"  curl -sS -O http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/label/jpcrp_2025-11-01_lab.xml",
        u"照合: shasum -a 256 -c %s" % os.path.join(ROOT, LABEL_SHA_REL),
        u"手順と sha256: fixtures/xbrl/TAXONOMY_LABELS_README.md(置き場は環境変数 EDINET_TAXONOMY_DIR で変えられる)"])


def pct(a, b):
    return round(100.0 * a / b, 1)


def frac_text(a, b):
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b)


def engine_bundle_sha256():
    u"""``core/`` と ``adapters/`` の file(``__pycache__`` を除く)の sha256 を、repo 相対の path 順に束ねた値。"""
    rows = []
    for top in ("adapters", "core"):
        for dp, dns, fns in os.walk(os.path.join(ROOT, top)):
            dns[:] = [d for d in dns if d != "__pycache__"]
            for fn in fns:
                if fn.endswith(".pyc"):
                    continue
                p = os.path.join(dp, fn)
                with io.open(p, "rb") as fh:
                    rows.append("%s\t%s" % (os.path.relpath(p, ROOT).replace(os.sep, "/"), hashlib.sha256(fh.read()).hexdigest()))
    return hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest(), len(rows)


def git_head():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def step_of(fp, raw, new_raw, value, expected):
    u"""``±1 最小単位`` の大きさ(``値の尺度`` での 1 桁)。表記の小数桁と単位の倍率から。0 のとき倍率は後の値から取る。"""
    _pre, num, _post = fp._digits_part(raw)
    _pre2, num2, _post2 = fp._digits_part(new_raw)
    dec = len(num.split(".", 1)[1]) if "." in num else 0
    n1, n2 = float(num.replace(",", "")), float(num2.replace(",", ""))
    if n1 != 0:
        mult = abs(value) / n1
    elif n2 != 0 and expected is not None:
        mult = abs(expected) / n2
    else:
        return None
    return mult * (10.0 ** (-dec))


def classify(fp, raw, new_raw, value, expected):
    if expected is None:
        raise SystemExit(u"**注入の後の値が 1 つに決まらない行が 通した に在る: %r → %r。止める**" % (raw, new_raw))
    delta = abs(expected - value)
    if delta <= 1e-9 * max(1.0, abs(value)):
        return CLASS_DEGENERATE, 0.0, None
    step = step_of(fp, raw, new_raw, value, expected)
    if step is not None and delta <= step * (1.0 + 1e-9):
        return CLASS_IN_BAND, delta, step
    return CLASS_OUT_BAND, delta, step


def build(zb, profile_name, label_shas=None):
    fp = _load_false_pass()
    t0 = time.time()
    # ---- (a) 素の書類
    ta = time.time()
    plain = VD.verify_document(zb, profile_name, None)
    t_plain = time.time() - ta
    text0 = fp.mdna_text(zb)
    # ---- (b) 注入
    tb = time.time()
    r = fp.run_doc(DOC_ID, profile_name, zb, text0)
    t_inject = time.time() - tb
    if r["original_states"] != plain["document"]["states"] or r["original_claims"] != plain["document"]["claims"]:
        raise SystemExit(u"**素の書類の state が run_doc の素の検証と違う。止める**")
    _sents, sites = fp.number_sites(text0, V.PROFILES[profile_name])
    by = {s["id"]: s for s in sites}

    rows = []
    for x in r["rows"]:
        s = by[x["id"]]
        row = {u"id": x["id"], u"型": x["how"], u"元の字": x["raw"], u"後の字": x.get("new"),
               u"元の値": s["value"], u"単位": s["unit"], u"結果": x["outcome"]}
        if x["outcome"] in ("PASSED",) or x["outcome"].startswith("detected:"):
            row[u"後の値"] = fp.expected_value(s, x["new"])
            row[u"参照先(注入前)"] = (x["base_pointer"] or [None])[0]
            row[u"参照先(注入後)"] = (x["after_pointer"] or [None])[0]
            row[u"文脈"] = x["span"]
        if x["outcome"] == "PASSED":
            cls, delta, step = classify(fp, x["raw"], x["new"], s["value"], row[u"後の値"])
            row[u"分類"] = cls
            row[u"値の差"] = delta
            row[u"1 最小単位"] = step
            row[u"参照先が動いた"] = row[u"参照先(注入前)"] != row[u"参照先(注入後)"]
        rows.append(row)

    passed = [x for x in rows if x[u"結果"] == "PASSED"]
    detected = [x for x in rows if x[u"結果"] == "detected:VALUE_MISMATCH"]
    n_t = r["targets"]
    if len(rows) != n_t:
        raise SystemExit(u"**注入の行の数が対象と違う: %d != %d。止める**" % (len(rows), n_t))
    other = {k: v for k, v in r["counts"].items() if k not in ("PASSED", "detected:VALUE_MISMATCH")}

    def by_class(c):
        return sum(1 for x in passed if x[u"分類"] == c)

    def by_how(how):
        m = [x for x in rows if x[u"型"] == how]
        return {u"対象": len(m), u"通した": sum(1 for x in m if x[u"結果"] == "PASSED"),
                u"止めた": sum(1 for x in m if x[u"結果"] == "detected:VALUE_MISMATCH")}

    total = time.time() - t0
    bundle, n_files = engine_bundle_sha256()
    rec = {
        u"step": u"**10 分の再現の儀式。API 鍵なし・0 USD・初回のラベル取得を除き通信なし・engine 0 行**",
        u"通した": {u"件": len(passed), u"分母": n_t, u"率": pct(len(passed), n_t), u"字": frac_text(len(passed), n_t)},
        u"止めた": {u"件": len(detected), u"分母": n_t, u"率": pct(len(detected), n_t), u"字": frac_text(len(detected), n_t)},
        u"止めた でも 通した でもない結果": other,
        u"通した の分け方": {
            c: {u"件": by_class(c),
                u"うち率(単位が %)": sum(1 for x in passed if x[u"分類"] == c and x[u"単位"] == u"%"),
                u"うち金額ほか(単位が % でない)": sum(1 for x in passed if x[u"分類"] == c and x[u"単位"] != u"%")}
            for c in (CLASS_IN_BAND, CLASS_DEGENERATE, CLASS_OUT_BAND)},
        u"通した のうち参照先が動いた(注入の前後で GROUNDED の参照先が違う)": sum(1 for x in passed if x[u"参照先が動いた"]),
        u"型別": {u"V1(最小の桁の 1 字を変える)": by_how("V1"), u"V2(値を ±1 最小単位)": by_how("V2")},
        u"通した の一覧": passed,
        u"素の書類": {u"claim": plain["document"]["claims"], u"state の分布": plain["document"]["states"]},
        u"注入": {u"数の site": r["sites"], u"土台の不一致": r["id_mismatch_in_baseline"], u"注入の対象(GROUNDED の site)": n_t,
                u"束の大きさ": r["batch"], u"土台(経営分析の文のまま)の state の分布": r["baseline_states"]},
        u"入力": {u"path": ZIP_REL, u"sha256": hashlib.sha256(zb).hexdigest(), u"bytes": len(zb), u"書類ID": DOC_ID,
                u"profile": profile_name},
        u"注入の一覧": rows,
        u"所要秒": {u"素の書類の検証": round(t_plain, 1), u"注入の再検証": round(t_inject, 1), u"全体": round(total, 1)},
        u"実行環境": {
            u"封": SEAL, u"HEAD": git_head(), u"python": platform.python_version(),
            u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)": bundle,
            u"engine の file 数": n_files,
            u"鍵の名前の有無(値は読まない)": {k: (k in os.environ) for k in KEY_NAMES},
            u"通信": u"儀式 script 自身は urllib・socket・http を import しない。adapters は urllib を import するが接続は起きない(門は接続を潰して完走させる)。通信は初回のラベル取得だけ",
            u"ラベル 2 file の sha256(起動時に照合)": label_shas,
            u"費用": u"0 USD"}}
    return rec


def render_md(rec):
    p, d = rec[u"通した"], rec[u"止めた"]
    ib = rec[u"入力"]
    L = [u"# 10 分の再現の儀式 ― 記録", u"",
         u"**通した %s**(誤りを入れた文が GROUNDED のまま通った数)" % p[u"字"], u"",
         u"- 止めた(VALUE_MISMATCH): %s" % d[u"字"],
         u"- 通した の分け方: %s" % u"・".join(u"%s %d(率 %d・金額ほか %d)" % (
             k, v[u"件"], v[u"うち率(単位が %)"], v[u"うち金額ほか(単位が % でない)"]) for k, v in rec[u"通した の分け方"].items()),
         u"- 通した のうち参照先が動いた: %d" % rec[u"通した のうち参照先が動いた(注入の前後で GROUNDED の参照先が違う)"],
         u"- 型別: %s" % u"・".join(u"%s 対象 %d・通した %d・止めた %d" % (k, v[u"対象"], v[u"通した"], v[u"止めた"])
                                  for k, v in rec[u"型別"].items()),
         u"- 素の書類: claim %d、state の分布 %s" % (rec[u"素の書類"][u"claim"], json.dumps(rec[u"素の書類"][u"state の分布"], ensure_ascii=False, sort_keys=True)),
         u"- 注入: 数の site %d・土台の不一致 %d・注入の対象 %d" % (rec[u"注入"][u"数の site"], rec[u"注入"][u"土台の不一致"], rec[u"注入"][u"注入の対象(GROUNDED の site)"]),
         u"- 入力: `%s`(sha256 `%s`、%d bytes、profile %s)" % (ib[u"path"], ib[u"sha256"], ib[u"bytes"], ib[u"profile"]),
         u"- engine の束ねた sha256: `%s`" % rec[u"実行環境"][u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)"],
         u"- 所要秒: 全体 %s(素の書類の検証 %s・注入の再検証 %s)" % (rec[u"所要秒"][u"全体"], rec[u"所要秒"][u"素の書類の検証"], rec[u"所要秒"][u"注入の再検証"]),
         u"", u"## 通した の一覧", u"",
         u"| id | 型 | 元の字 | 後の字 | 値(前 → 後) | 単位 | 参照先(前 → 後) | 分け方 |", u"|---|---|---|---|---|---|---|---|"]
    for x in rec[u"通した の一覧"]:
        mv = u"" if not x[u"参照先が動いた"] else u"(動いた)"
        L.append(u"| %s | %s | `%s` | `%s` | %s → %s | %s | `%s` → `%s`%s | %s |" % (
            x[u"id"], x[u"型"], x[u"元の字"], x[u"後の字"], x[u"元の値"], x[u"後の値"], x[u"単位"],
            x[u"参照先(注入前)"], x[u"参照先(注入後)"], mv, x[u"分類"]))
    L += [u"", u"## 言えないこと", u"",
          u"- この 1 書類は経営分析の節が AI の文(2026-10-09 の実験)に差し替わっていて、原文ではない。",
          u"- 注入は『最小の桁 1 字』と『±1 最小単位』の 2 型だけ。",
          u"- 通した は『丸めの帯』と『退化値』に分かれて見えるだけで、それが欠陥でないかは読む人が決める。", u""]
    return u"\n".join(L)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=u"10 分の再現の儀式(通信なし・鍵なし・0 USD)")
    ap.add_argument("--out", required=True, help=u"出力先の directory(ritual.json と ritual.md を書く)")
    a = ap.parse_args(argv)
    zp = os.path.join(ROOT, ZIP_REL)
    if not os.path.exists(zp):
        raise SystemExit(u"入力が無い: %s(clone した repo の fixtures/xbrl/ に在るはず)" % ZIP_REL)
    with io.open(zp, "rb") as fh:
        zb = fh.read()
    if hashlib.sha256(zb).hexdigest() != ZIP_SHA256 or len(zb) != ZIP_BYTES:
        raise SystemExit(u"入力の sha256 が封の字と違う: %s。止める" % hashlib.sha256(zb).hexdigest())
    # 2026-10-20(期を縛る P22 の段 2): 既定は P21 -> P22。買い手が今の既定で走らせるものなので、記録(ritual_2026-10-20.json)は
    # P22 で採り直した。P21 のときの記録(17 / 241 = 7.1%)は fixtures/xbrl/ritual_2026-10-20_p21.json と git の履歴(3320c8c まで)に残してある。
    if V.DEFAULT_PROFILE != "P22":
        raise SystemExit(u"既定 profile が P22 でない: %r。止める" % V.DEFAULT_PROFILE)
    label_shas, why = check_labels()
    if why:
        print(label_guidance(why), file=sys.stderr)
        return 2
    rec = build(zb, V.DEFAULT_PROFILE, label_shas)
    os.makedirs(a.out, exist_ok=True)
    jp, mp = os.path.join(a.out, "ritual.json"), os.path.join(a.out, "ritual.md")
    with io.open(jp, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write(u"\n")
    with io.open(mp, "w", encoding="utf-8") as fh:
        fh.write(render_md(rec))
    p, d, c = rec[u"通した"], rec[u"止めた"], rec[u"通した の分け方"]
    print(u"=== 10 分の再現の儀式(%s・同梱の 1 書類・鍵なし・0 USD)===" % rec[u"入力"][u"profile"])
    print(u"通した %s" % p[u"字"])
    print(u"止めた %s" % d[u"字"])
    print(u"通した の分け方: %s" % u"・".join(u"%s %d" % (k, c[k][u"件"]) for k in (CLASS_IN_BAND, CLASS_DEGENERATE, CLASS_OUT_BAND)))
    print(u"素の書類: claim %d・state %s" % (rec[u"素の書類"][u"claim"], json.dumps(rec[u"素の書類"][u"state の分布"], ensure_ascii=False, sort_keys=True)))
    print(u"入力 sha256 %s" % rec[u"入力"][u"sha256"])
    print(u"所要 %s 秒" % rec[u"所要秒"][u"全体"])
    print(u"記録: %s / %s" % (jp, mp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
