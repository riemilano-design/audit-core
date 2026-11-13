# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TANSHIN_SELF_SEAL_2026-11-14.md §0-2 の 6・§1・§2 の 1 ― TSS(決算短信の概況の文を、同じ短信の添付の財務諸表で確かめる)の材料 400 本を、新しい置き場へ写す。
**0 USD・通信なし(通信の module を import もしない)・鍵は読まない・LLM は呼ばない。この script の仕事は、手元の ZIP を新しい folder に写すことだけ。**

    python3 measure/xbrl_tanshin_self_stage_2026-11-14.py --src DIR [--src DIR ...]                              # 本番: 400 本を ~/.cache/audit-core/tanshin-self-2026-11-14/<sha256>.zip に置き、
                                                                                                                   # fixtures/xbrl/tanshin_self/population_2026-11-14.json に記録を書く
    python3 measure/xbrl_tanshin_self_stage_2026-11-14.py --src DIR --out DIR2 --record PATH                    # 使い捨て(本番の folder にも記録にも書かない)

やること(順序。**1 つでも合わなければ、何も書かずに止める**)
  1. 母集団 = 封 §1 の表の 400 行を **封の file から読む**(この script に 400 行を写さない)。読んだ行が 400・番号が 1 から続く・sha256 の重なりが 0・群が 甲 50 / 乙 200 / 丙 150 でなければ止める
  2. ``--src`` の下の ``*.zip`` を歩き、byte を読んで sha256 を取り、母集団に在るものだけを選ぶ(ZIP は展開しない。表に無い ZIP は写さない)。400 本そろわなければ止める
  3. 選んだ ZIP ごとに、サマリーの file 名 ``XBRLData/Summary/tse-<8 字>-…`` の 8 字が封の「様式の種類」と同じかを見る(違えば止める。2 種類以上在っても止める)
  4. 置き先は既定で ``~/.cache/audit-core/tanshin-self-2026-11-14/<sha256>.zip``。``--out DIR`` なら DIR の下(本番の folder には書かない)。在る file は sha256 が同じなら触らず、違えば止める
  5. ほかの cache folder(置き先を除く ``~/.cache/audit-core`` の直下の folder。``SKIP_CACHES`` は開かない)の一覧(件数と名前の sha256)が前後で同じでなければ、記録を書かずに止める
  6. 記録: 400 行 [#, 群, 様式の種類, sha256, byte 数] と前後の cache の照合。**証券コード・会社名・TDnet の番号・元の path は書かない。** 本番の記録の path へは ``--out`` なしのときだけ・在れば止める

通信する所は 1 つも無い。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SEAL_REL = "docs/XBRL_TANSHIN_SELF_SEAL_2026-11-14.md"
SEAL_COMMIT = "e56d6782"
SCRIPT_REL = "measure/xbrl_tanshin_self_stage_2026-11-14.py"
REC_DIR_REL = "fixtures/xbrl/tanshin_self"
POPULATION_REL = REC_DIR_REL + "/population_2026-11-14.json"
CACHE_NAME = "tanshin-self-2026-11-14"
#: 封 §1 の 400 本・群の本数(封 §0-1 の 2)
N_ROWS = 400
GROUP_COUNTS = collections.OrderedDict([(u"甲", 50), (u"乙", 200), (u"丙", 150)])
#: 開かない cache folder(人間の指示。件数も名前も見ない)
SKIP_CACHES = ("edinetdb-p27",)
#: 様式の種類を読む member(封 §0-1 の 3)
SUMMARY_PREFIX = "XBRLData/Summary/"
SUMMARY_FILE_PREFIX = "tse-"
SUMMARY_FILE_SUFFIX = "-ixbrl.htm"
KIND_LEN = 8

#: 記録に鍵らしい字が無いかの検査(2026-11-09 の取得の script と同じ型。門が ``GEN.KEY_PATTERNS`` と同じ字か照らす)
KEY_PATTERNS = (r"sk-[A-Za-z0-9_\-]{10,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{20,}", r"xox[baprs]-[A-Za-z0-9\-]{10,}",
                r"-----BEGIN", r"Bearer [A-Za-z0-9._\-]{16,}", r"AIza[0-9A-Za-z_\-]{30,}", r"x-api-key",
                r"ANTHROPIC_API_KEY" + r"\s*=\s*['\"]?\w{8,}")
LONG_ALNUM = re.compile(r"[A-Za-z0-9_\-]{32,}")
SHA256_HEX = re.compile(r"[0-9a-f]{64}")
GIT_COMMIT = re.compile(r"[0-9a-f]{40}")

SEAL_ROW = re.compile(r"^\| (\d+) \| (甲|乙|丙) \| (\w+) \| `([0-9a-f]{64})` \| (?:切れた|切れない) \| (?:\d+|-) \|$", re.M)


class Stop(SystemExit):
    u"""止める。文言に材料の字・会社の名を入れない。"""


# ======================================================================================================
# 小さい道具
def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_text(s):
    return sha256_bytes(s.encode("utf-8"))


def sha256_file(p):
    with io.open(p, "rb") as fh:
        return sha256_bytes(fh.read())


def git_head(root=ROOT):
    try:
        r = subprocess.run(["git", "-C", os.path.dirname(os.path.abspath(root)), "rev-parse", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return None
    return r.stdout.decode("ascii", "replace").strip() or None


def key_leaks(text, key_value=None):
    u"""記録の文字列に鍵らしい字が在れば、その種類の一覧(値は返さない)。sha256・git の commit の 16 進は鍵に数えない。"""
    leaks = []
    for pat in KEY_PATTERNS:
        if re.search(pat, text):
            leaks.append(u"鍵の形(%s)" % pat[:12])
    for s in LONG_ALNUM.findall(text):
        if SHA256_HEX.fullmatch(s) or GIT_COMMIT.fullmatch(s):
            continue
        leaks.append(u"32 字以上の英数字の連なり(長さ %d)" % len(s))
    if key_value and key_value in text:
        leaks.append(u"環境の鍵の値そのもの")
    return leaks


def cache_base():
    u"""``~/.cache/audit-core``。呼ぶ時に HOME を見る。"""
    return os.path.join(os.path.expanduser("~"), ".cache", "audit-core")


def default_cache_dir():
    return os.path.join(cache_base(), CACHE_NAME)


def display_path(path):
    home = os.path.expanduser("~")
    if path == home or path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path


# ======================================================================================================
# 母集団(封 §1。封の file から読む)
def seal_text(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def population_from_text(seal):
    u"""封 §1 の表 [(#, 群, 様式の種類, sha256)]。"""
    try:
        sec = seal[seal.index(u"## §1"):seal.index(u"## §2")]
    except ValueError:
        raise Stop(u"**封の節(§1・§2)が読めない。止める**")
    return [(int(m[0]), m[1], m[2], m[3]) for m in SEAL_ROW.findall(sec)]


def validate_population(rows, n=N_ROWS, groups=GROUP_COUNTS):
    u"""400 行・番号が 1 から続く・sha256 の重なり 0・群が 甲 50 / 乙 200 / 丙 150。違えば止める。(n・groups は試験が小さい表で試すための引数。本番は既定のまま)"""
    if len(rows) != n:
        raise Stop(u"**母集団の行が %d(%d でない)。止める**" % (len(rows), n))
    if [r[0] for r in rows] != list(range(1, len(rows) + 1)):
        raise Stop(u"**母集団の番号が 1 から続いていない。止める**")
    if len(set(r[3] for r in rows)) != len(rows):
        raise Stop(u"**母集団の sha256 に重なりがある。止める**")
    c = collections.Counter(r[1] for r in rows)
    if [(g, c.get(g, 0)) for g in groups] != list(groups.items()) or sum(c.values()) != len(rows):
        raise Stop(u"**母集団の群が 甲 50 / 乙 200 / 丙 150 でない。止める**")
    return rows


def read_population(root=ROOT):
    return validate_population(population_from_text(seal_text(root)))


# ======================================================================================================
# 材料を探す・様式の種類を読む
def summary_kinds(zb):
    u"""ZIP のサマリーの file 名 ``XBRLData/Summary/tse-<8 字>-…-ixbrl.htm`` の 8 字(2 番目の ``-`` の前の字の先頭 8 字)の集合。"""
    kinds = set()
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        for m in z.namelist():
            b = os.path.basename(m)
            if m.startswith(SUMMARY_PREFIX) and b.startswith(SUMMARY_FILE_PREFIX) and b.endswith(SUMMARY_FILE_SUFFIX):
                kinds.add(b.split("-")[1][:KIND_LEN])
    return kinds


def scan_sources(dirs, wanted):
    u"""``dirs`` の下の ``*.zip`` を歩き(path の順)、byte の sha256 が ``wanted`` に在るものを選ぶ。{sha256: (path, byte 数)}。
    表に無い ZIP は選ばない。同じ sha256 が 2 か所以上に在れば path の順で先のものを使う。"""
    found = collections.OrderedDict()
    for d in dirs:
        if not os.path.isdir(d):
            raise Stop(u"**--src が folder でない。止める**")
        for dp, dn, fn in os.walk(d):
            dn.sort()
            for f in sorted(fn):
                if not f.endswith(".zip"):
                    continue
                p = os.path.join(dp, f)
                with io.open(p, "rb") as fh:
                    b = fh.read()
                s = sha256_bytes(b)
                if s in wanted and s not in found:
                    found[s] = (p, len(b))
    return found


# ======================================================================================================
# ほかの cache の一覧(前後)
def names_snapshot(folder):
    names = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
    return (len(names), sha256_text(u"\n".join(names)))


def others_snapshot(base=None, skip=SKIP_CACHES, names=None):
    u"""``base`` の直下の folder(置き先と ``skip`` を除く)の (名前, 件数, 名前の一覧の sha256)。``names`` を渡せばその folder だけ(後の照合用 = 前に居た folder)。"""
    base = base or cache_base()
    if names is None:
        names = sorted(n for n in os.listdir(base) if n != CACHE_NAME and n not in skip) if os.path.isdir(base) else []      # skip の folder は stat もしない
        names = [n for n in names if os.path.isdir(os.path.join(base, n))]
    return [(n,) + names_snapshot(os.path.join(base, n)) for n in names]


def snapshot_digest(snap):
    u"""(比べた folder の数, 一覧の sha256)。folder の名前は記録に書かず、sha256 だけにする。"""
    return len(snap), sha256_text(u"\n".join(u"%s\t%d\t%s" % t for t in snap))


# ======================================================================================================
# 置く・記録
def check_out_dir(out, base=None):
    u"""置き先が既存の cache folder の中(置き先の名前以外)なら止める。"""
    base = os.path.realpath(base or cache_base())
    real = os.path.realpath(out)
    if real == base:
        raise Stop(u"**置き先が cache の根そのもの。止める**")
    if real.startswith(base + os.sep) and real[len(base) + 1:].split(os.sep)[0] != CACHE_NAME:
        raise Stop(u"**置き先が既に在る cache folder の中。止める**")


def dumps_record(rec):
    u"""``行`` を 1 行 1 本にして書く。"""
    rows = rec.get(u"行") or []
    rec2 = collections.OrderedDict((k, (u"@@ROWS@@" if k == u"行" else v)) for k, v in rec.items())
    text = json.dumps(rec2, ensure_ascii=False, indent=1)
    body = u"[\n" + u",\n".join(u"  " + json.dumps(r, ensure_ascii=False) for r in rows) + u"\n ]"
    return text.replace(json.dumps(u"@@ROWS@@"), body) + u"\n"


def write_text_exclusive(path, text):
    if os.path.exists(path):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(path))
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    os.replace(tmp, path)


def run_stage(root=ROOT, srcs=(), out=None, record=None, population=None, cache_base_dir=None, say=print, key_value=None, shape=None):
    u"""400 本を置き、記録(OrderedDict)を返す。書き込みは全部の検証の後。"""
    production = out is None
    prod_record = os.path.join(root, POPULATION_REL)
    base = cache_base_dir or cache_base()
    if production:
        if record is not None and os.path.abspath(record) != os.path.abspath(prod_record):
            raise Stop(u"**--out なしの記録は本番の path だけ。止める**")
        record = prod_record
        dest = os.path.join(base, CACHE_NAME)
    else:
        if record is None:
            raise Stop(u"**--out を付けたら --record も指定する(本番の記録には書かない)。止める**")
        if os.path.abspath(record) == os.path.abspath(prod_record):
            raise Stop(u"**--out を付けた走らせ方は本番の記録に書かない。止める**")
        dest = os.path.abspath(out)
        check_out_dir(dest, base)
    if os.path.exists(record):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(record))
    if not srcs:
        raise Stop(u"**--src が 1 つも無い。止める**")
    n_rows, groups = shape or (N_ROWS, GROUP_COUNTS)               # 試験が小さい表で試すときだけ shape を渡す
    rows = validate_population(population if population is not None else read_population(root), n_rows, groups)
    by_sha = dict((r[3], r) for r in rows)
    before = others_snapshot(base)
    found = scan_sources(list(srcs), by_sha)
    if len(found) != len(rows):
        raise Stop(u"**表の ZIP が %d 本しかそろわない(%d 本要る)。何も書かずに止める**" % (len(found), len(rows)))
    sizes = collections.OrderedDict()
    for (n, grp, kind, sha) in rows:
        path, size = found[sha]
        with io.open(path, "rb") as fh:
            zb = fh.read()
        if sha256_bytes(zb) != sha:
            raise Stop(u"**ZIP の sha256 が読んでいる間に変わった。止める**")
        kinds = summary_kinds(zb)
        if kinds != set([kind]):
            raise Stop(u"**ZIP の様式の種類が封の表と違う(# %d)。止める**" % n)
        sizes[sha] = len(zb)
    # 置き先に在る file は sha256 が名前と同じでなければ止める(何も書く前に全部見る)
    existing = set()
    for (_n, _g, _k, sha) in rows:
        p = os.path.join(dest, sha + ".zip")
        if os.path.exists(p):
            if sha256_file(p) != sha:
                raise Stop(u"**置き先に在る file の sha256 が名前と違う。止める**")
            existing.add(sha)
    out_rows = [[n, grp, kind, sha, sizes[sha]] for (n, grp, kind, sha) in rows]

    def compose(snap_before, snap_after):
        n_before, d_before = snapshot_digest(snap_before)
        n_after, d_after = snapshot_digest(snap_after)
        rec = collections.OrderedDict()
        rec[u"seal"] = SEAL_REL
        rec[u"封の commit"] = SEAL_COMMIT
        rec[u"step"] = u"TSS(決算短信の概況の文を同じ短信の添付の財務諸表で確かめる)― 材料 400 本の置き場への写し(0 USD・通信なし)"
        rec[u"HEAD の commit"] = git_head(root)
        rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
        rec[u"範囲"] = u"封 §1 の 400 本"
        rec[u"置き場"] = display_path(dest) if production else u"使い捨ての置き場(本番の folder ではない)"
        rec[u"ほかの cache の前後"] = collections.OrderedDict([
            (u"比べた folder の数", n_before), (u"前の一覧の sha256", d_before), (u"後の一覧の sha256", d_after), (u"変化なし", n_before == n_after and d_before == d_after)])
        rec[u"表と一致した ZIP"] = len(rows)
        rec[u"新しく置いた ZIP"] = len(rows) - len(existing)
        rec[u"在って触らなかった ZIP(sha256 が同じ)"] = len(existing)
        rec[u"群"] = collections.OrderedDict((g, sum(1 for r in rows if r[1] == g)) for g in groups)
        rec[u"様式の種類"] = collections.OrderedDict(sorted(collections.Counter(r[2] for r in rows).items()))
        rec[u"行の欄"] = [u"#", u"群", u"様式の種類", u"ZIP の sha256", u"byte 数"]
        rec[u"行"] = out_rows
        rec[u"key_leaks"] = []
        text = dumps_record(rec)
        leaks = key_leaks(text.replace(SEAL_REL, u""), key_value)       # 封の path は 32 字以上の _ - 英数字の連なり(前の便の取得と同じく除いて検査する)
        if leaks:
            raise Stop(u"**鍵らしい字が記録に在る(%s)。書かずに止める**" % u" / ".join(sorted(set(leaks))))
        return rec, text
    compose(before, before)                                             # 置く前に、記録の字の検査だけ通す(通らなければ何も書かない)
    # ここまで全部の検証が通った。置く
    os.makedirs(dest, exist_ok=True)
    for (_n, _g, _k, sha) in rows:
        if sha in existing:
            continue
        with io.open(found[sha][0], "rb") as fh:
            zb = fh.read()
        if sha256_bytes(zb) != sha:
            raise Stop(u"**ZIP の sha256 が写す前に変わった。止める**")
        p = os.path.join(dest, sha + ".zip")
        tmp = p + ".tmp"
        with io.open(tmp, "wb") as fh:
            fh.write(zb)
        os.replace(tmp, p)
    after = others_snapshot(base, names=[t[0] for t in before])
    if before != after:
        raise Stop(u"**ほかの cache の件数か名前が変わった。記録を書かずに止める**")
    rec, text = compose(before, after)
    write_text_exclusive(record, text)
    say(u"-> 記録 %s(%d 本)" % (os.path.basename(record), len(rows)))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--src", action="append", default=[], help="ZIP を探す folder(何個でも)")
    ap.add_argument("--out", default=None, help="置き先(既定: 本番の folder。付けたら --record が要る)")
    ap.add_argument("--record", default=None, help="記録の path(既定: 本番の path。--out なしのときだけ)")
    a = ap.parse_args(argv)
    run_stage(root=a.root, srcs=a.src, out=a.out, record=a.record)


if __name__ == "__main__":
    main()
