# -*- coding: utf-8 -*-
"""封A・封B の材料 4 件を、**封じた記録に書いてある docID だけ**取る。

**この道具は人間が回す。** 本線の席(司令塔・実装・監査)は EDINET API に
触れない規定なので、ここを実行するのは人間だけである。

なぜ ``measure/fetch_material.py`` ではないのか: あちらは **種で選び直す**口
(``--pick N``)しか持たない。4 件は既に封じた抽選で確定している
(``4116ca3`` の再割当と ``0fc7ec1`` の引き直し)ので、選び直す道具を使うと
**封じた抽選が無意味になる。** ここは「名前で、封じた 4 件だけを取る」専用。

**費用.** EDINET API は無償。従量課金は無い(``measure/fetch_material.py``
の注記と同じ)。

**鍵.** ``EDINET_API_KEY`` から読むだけで、**値を印字も記録も保存もしない。**

**盲検.** 中身は読まない。記録するのは ZIP の sha256 と**目録(ファイル名と
サイズ)から作った印**だけで、本文は 1 文字も読まない・印字しない。

機械の門(どれか 1 つでも破れたら 1 件も取らずに止まる):
  門① 出典 2 本が git に追跡され、HEAD と一致している(封じた後に書き換えていない)
  門② 封じた記録から読んだ 4 件が、**この file に字で書いた一覧と完全一致**する
  門③ 字の一覧に無い docID は取らない(引数で渡しても取らない)
  門④ 旧 封B 材料(S100Z3CO・S100Z4PA)は**取らない・上書きしない**
       ― 非盲検として保存する材料であり、取り直す対象ではない
  門⑤ 応答が ZIP でなければ止まる(EDINET は鍵が無効でも HTTP 200 で
       JSON を返すので、HTTP の番号だけでは判定できない)
  門⑥ 記録が既に在れば**上書きしない**(2 回目以降の実行は定義上いつでも
       「すでに手元に在った」になるので、回し直すほど「取った」が消える)

使い方::

    export EDINET_API_KEY=...        # 人間が設定する。この道具は値を見ない
    python3 fixtures/xbrl/fetch_sealed_material_2026-10-09.py --dry-run
    python3 fixtures/xbrl/fetch_sealed_material_2026-10-09.py
    python3 fixtures/xbrl/fetch_sealed_material_2026-10-09.py --seal A
"""

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))   # audit-core/fixtures/xbrl
ROOT = os.path.dirname(os.path.dirname(HERE))       # audit-core/
REPO = os.path.dirname(ROOT)                        # repo の根

API = "https://api.edinet-fsa.go.jp/api/v2/documents/%s"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

# --------------------------------------------------------------------------
# **封じた 4 件。字で書く。**(門②で封じた記録と照合する)
#
# 出どころ:
#   封A = docs/XBRL_REALLOCATION_SEAL_2026-10-09.md の割当表(4116ca3)
#   封B = fixtures/xbrl/redraw_b_2026-10-09.json の picked(0fc7ec1)
# **結果を見てから割当を変えない。**この表を書き換えるのは人間の裁定だけ。
SEALED = (
    ("S100Z3JY", "封A", "株式会社総医研ホールディングス", "2026-09-24"),
    ("S100Z35K", "封A", "株式会社オープンアップグループ", "2026-09-18"),
    ("S100Z3V1", "封B", "サンネクスタグループ株式会社", "2026-09-25"),
    ("S100Z3HP", "封B", "株式会社ハンズマン", "2026-09-24"),
)

# **門④ 取らない・上書きしない。** 封印の 4 分前に別の席に取得され、封B が
# 非盲検になった材料(追記 862ce7a)。捨てずに保存するが、取り直さない。
NEVER_FETCH = {
    "S100Z3CO": "旧 封B 材料(非盲検として保存。取り直さない)",
    "S100Z4PA": "旧 封B 材料(非盲検として保存。取り直さない)",
}

REALLOC_SEAL = os.path.join(ROOT, "docs", "XBRL_REALLOCATION_SEAL_2026-10-09.md")
REDRAW_RECORD = os.path.join(HERE, "redraw_b_2026-10-09.json")
OUT_RECORD = os.path.join(HERE, "fetched_sealed_2026-10-09.json")
# --------------------------------------------------------------------------


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=REPO,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def gate1_sources_unmodified():
    """門① 出典 2 本が追跡され、HEAD と一致している。"""
    bad = []
    for p in (REALLOC_SEAL, REDRAW_RECORD):
        rel = os.path.relpath(p, REPO)
        if git("ls-files", "--error-unmatch", "--", rel).returncode != 0:
            bad.append("%s は git に追跡されていない" % rel); continue
        if git("diff", "--quiet", "HEAD", "--", rel).returncode != 0:
            bad.append("%s が HEAD と違う(封じた後に書き換えられている)" % rel)
    return bad


def parse_seal_a():
    """再割当の封の割当表から、封A の docID を読む。"""
    with io.open(REALLOC_SEAL, encoding="utf-8") as fh:
        text = fh.read()
    found = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        m = re.match(r"^`(S100[0-9A-Z]+)`$", cells[0])
        if m and "封A" in cells[1]:
            found.append(m.group(1))
    return found


def parse_seal_b():
    with io.open(REDRAW_RECORD, encoding="utf-8") as fh:
        rec = json.load(fh)
    return [r["docID"] for r in rec["picked"] if "封B" in r.get("seal", "")]


def gate2_records_match_literal():
    """門② 封じた記録から読んだ 4 件 == 字で書いた一覧。"""
    want_a = sorted(d for d, s, _f, _dt in SEALED if s == "封A")
    want_b = sorted(d for d, s, _f, _dt in SEALED if s == "封B")
    got_a, got_b = sorted(set(parse_seal_a())), sorted(set(parse_seal_b()))
    bad = []
    if got_a != want_a:
        bad.append("封A: 記録 %s / 字の一覧 %s" % (got_a, want_a))
    if got_b != want_b:
        bad.append("封B: 記録 %s / 字の一覧 %s" % (got_b, want_b))
    return bad


def cache_path(doc_id):
    return os.path.join(CACHE_DIR, "%s.zip" % doc_id)


def listing_digest(zb):
    """**中身を読まない印。** 目録(名前とサイズ)だけから作る。"""
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        rows = sorted((i.filename, i.file_size) for i in z.infolist())
    blob = "\n".join("%s\t%d" % r for r in rows).encode("utf-8")
    return hashlib.sha256(blob).hexdigest(), len(rows)


def fetch_zip(doc_id):
    """門③④⑤ を通ったものだけ取る。"""
    if doc_id in NEVER_FETCH:
        raise SystemExit("門④: %s は取らない ― %s" % (doc_id, NEVER_FETCH[doc_id]))
    if doc_id not in {d for d, _s, _f, _dt in SEALED}:
        raise SystemExit("門③: %s は封じた一覧に無い ― 取らない" % doc_id)
    key = os.environ.get("EDINET_API_KEY")
    if not key:
        raise SystemExit("環境変数 EDINET_API_KEY が無い。鍵の値はこの道具に書かない。")
    url = (API % urllib.parse.quote(doc_id)) + "?" + urllib.parse.urlencode(
        {"type": 1, "Subscription-Key": key})
    try:
        with urllib.request.urlopen(url, timeout=300) as r:
            body = r.read()
    except urllib.error.HTTPError as e:
        raise SystemExit("門⑤: %s は HTTP %s で返った" % (doc_id, e.code))
    # 門⑤ EDINET は鍵が無効でも HTTP 200 + JSON を返す。ZIP かどうかで判定する。
    if not body.startswith(b"PK"):
        msg = ""
        try:
            j = json.loads(body.decode("utf-8", "replace"))
            msg = " StatusCode=%s message=%s" % (j.get("StatusCode"), j.get("message"))
        except Exception:
            msg = " 先頭 %r" % body[:40]
        # **鍵の値は印字しない。**url も出さない。
        raise SystemExit("門⑤: %s の応答が ZIP ではない。%s" % (doc_id, msg))
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path(doc_id), "wb") as fh:
        fh.write(body)
    return body


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seal", choices=["A", "B"], default=None,
                    help="片方だけ取る(既定は封じた 4 件すべて)")
    ap.add_argument("--dry-run", action="store_true",
                    help="門だけ当てて、在不在を印字して終わる。**取らない**")
    a = ap.parse_args(argv)

    for name, bad in (("門①", gate1_sources_unmodified()),
                      ("門②", gate2_records_match_literal())):
        if bad:
            print("止まる %s:" % name)
            for b in bad:
                print("  " + b)
            print("  1 件も取っていない。記録の側を直してから回すこと。")
            return 3
    print("門①② 通過 ― 出典 2 本は HEAD と一致、封じた 4 件は記録と字の一覧で一致")

    rows = [r for r in SEALED if a.seal is None or r[1] == "封" + a.seal]
    print("対象 %d 件%s" % (len(rows), "" if a.seal is None else "(封%s のみ)" % a.seal))

    if a.dry_run:
        for doc, seal, filer, date in rows:
            print("  %-10s %-4s %-22s %s  キャッシュ: %s"
                  % (doc, seal, filer[:22], date,
                     "在る" if os.path.exists(cache_path(doc)) else "無い"))
        print("--dry-run なので 1 件も取っていない。")
        return 0

    out = []
    for doc, seal, filer, date in rows:
        p = cache_path(doc)
        had = os.path.exists(p)
        if had:
            with open(p, "rb") as fh:
                body = fh.read()
        else:
            body = fetch_zip(doc)
        digest, members = listing_digest(body)
        how = "すでに手元に在った" if had else "取った"
        out.append({"docID": doc, "seal": seal, "filerName": filer, "date": date,
                    "bytes": len(body),
                    "zip_sha256": hashlib.sha256(body).hexdigest(),
                    "listing_digest": digest, "listing_members": members,
                    "how": how})
        print("  %-10s %-4s %9d bytes  zip=%s…  目録の印=%s…(%d 本)  (%s)"
              % (doc, seal, len(body), out[-1]["zip_sha256"][:12],
                 digest[:12], members, how))

    # 門⑥ 記録は上書きしない。
    if os.path.exists(OUT_RECORD):
        print("記録は既にある -> %s(**上書きしない**)" % OUT_RECORD)
        print("  今回の実行で取った件数: %d(0 なら全部すでに手元に在った)"
              % sum(1 for r in out if r["how"] == "取った"))
        print("  作り直すなら、先に古い記録を自分で退避すること。")
        return 0
    with io.open(OUT_RECORD, "w", encoding="utf-8") as fh:
        json.dump({"tool": os.path.basename(__file__),
                   "seals": {"A": "docs/NORMALIZATION_SEAL_A_2026-10-09.md",
                             "B": "docs/SIGN_SEAL_B_2026-10-09.md"},
                   "sources": {"封A": "docs/XBRL_REALLOCATION_SEAL_2026-10-09.md",
                               "封B": "fixtures/xbrl/redraw_b_2026-10-09.json"},
                   "note": "中身は読んでいない。目録の印は ZIP のファイル名とサイズだけから作っている。",
                   "fetched": out}, fh, ensure_ascii=False, indent=1)
        fh.write(u"\n")
    print("記録 -> %s  **中身は読んでいない**" % OUT_RECORD)
    return 0


if __name__ == "__main__":
    sys.exit(main())
