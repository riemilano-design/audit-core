# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PACK_BUILD_SEAL_2026-11-22.md(XP0 ― 受理済みの有報の PublicDoc を「原稿の folder」(素の本文と表の file)に落とし、その folder だけを読む別の process の組む命令で htm・xsd・linkbase を丸ごと組むと、公開の道具が読むタクソノミ・fact・検査の鳴り方は元と同じになるか)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。** engine(``core/``・``adapters/``)は読まない・変えない。剥がす・組む・書き出しの比べ・道具の掛け方・書類の選び方・包みの写しの関数は、前の便(XB0・XT0。XT0 が呼ぶ XV0・XG0 を含む)の script の関数を importlib で呼ぶ(写さない)。

    python3 measure/xbrl_pack_build_2026-11-22.py --tool-p <venv の場所>           # 道具を確かめて 67 本(+ 開発の 5 本の混ぜ物 20 個)を掛け、記録を書く(本番は 1 回)
    python3 measure/xbrl_pack_build_2026-11-22.py --check                         # 記録の形・合計・禁止のものを検査する。道具は呼ばない・掛け直さない
    python3 measure/xbrl_pack_build_2026-11-22.py --dev --tool-p <venv の場所>     # 開発の 5 本だけ(置き場の並びの頭の 5 本の zip だけ開く)。記録は書かない
    python3 measure/xbrl_pack_build_2026-11-22.py peel <zip> <原稿の folder>       # 落とす(zip → 原稿の folder)
    python3 -I measure/xbrl_pack_build_2026-11-22.py build <原稿の folder> <出す folder>   # 組む(別の process で呼ぶ。引数は folder 2 つだけ。原稿の folder のほかを読まない)

原稿の folder の中身(書類 1 本に 1 つ。元の htm・xsd・linkbase の字・元の包み・マニフェスト・画像・AuditDoc は置かない):
``index.json``(目次: 組む file の名の並びと、どの file がどの素の本文・表に当たるか)・``t0000.txt``…(素の本文。UTF-8)・``t0000.json``…(本文の表 F・H)・``taxonomy.json``(表 S・K 5 つ)。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- JSON の書き方: ``ensure_ascii=False``・``separators=(",", ":")``・UTF-8・順序つき辞書の並びのまま。読み戻すときは順序つき辞書で読む(tuple は list になる。組む部品は添字と展開だけで使うので同じ字が出る)。素の本文は bytes のまま書き読む(改行を変えない)。
- 目次: ``htm``(file の名の昇順。1 つは ``name``(PublicDoc の直下からの相対の名)・``text``・``tables``)・``taxonomy``(``file``・``names``(kind → 相対の名))。出す folder には相対の名で書く。相対の名に ``..``・``\\``・先頭の ``/`` が在れば断る。
- 組む命令の入口: 引数が ``build`` + folder 2 つでなければ使い方を出して 64 で終わる。知らない形は 2(標準のエラーに ``DECLINE: <固定の理由>`` の行)・それ以外の例外は 1。時間の上限は 600 秒(便 XT0 と同じ)。
  書類ごとに、組む命令は別の作業の folder(元の包みを置いていない)を cwd にして ``python3 -I`` で走らせる。出す folder の file の名の集まりが目次と違うときは断ったに数える。
- 断った: 落とす側の断り(``Refuse``)・組む命令の 0 でない終わりの値・時間の上限・出力が目次と合わないこと。理由は固定の字だけ(材料の字を入れない)。1 回目の組む命令が成功した後の 2 回目が失敗したときは、断ったには数えず ``2 度が同じ`` を偽にする。
- 道筋が同じ: 同じ process の中で、元の包みから剥がした表を ``B.rebuilt_texts``(便 XB0)・``T.build_tables``(便 XT0)に直接渡して組んだ bytes が、組む命令の出す folder の bytes と file の名の集まりまで同じこと。
- 組み直した包み: 出す folder の file を PublicDoc の直下からの相対の名で元の包みの同じ名の file に置き換える(便 XT0 の ``package_with`` に、名 → 名の写しと名 → bytes を渡す)。ほかの file は元のまま。
- 比べる: 書き出し 7 つ・fact・鳴り方・全部同じは便 XT0 の ``compare_into`` をそのまま呼ぶ(概念だけ同じ先頭の欄の行の中の並びを問わない、という便 XT0 の決めのまま)。
- 混ぜ物 N1〜N4: 開発の 5 本それぞれで、元の原稿の folder を複製した folder の file を disk の上で 1 か所だけ変えてから、別の process の組む命令を掛ける。作れたかは「当て先が在って、組む命令が成功して、出力が目次と合う」こと。
  N1 の当て先: 便 XB0 の ``num_pool``(``xsi:nil`` の無い ``nonFraction``。file の名の昇順・表 F の順)で最初の、素の本文の中の字が 0 だけでなく(便 XB0 の ``is_zero_content``)、1〜9 の数字(ASCII)を含むもの。封の字だけでは「中の字が 0 だけでない」が数字を持たない行を含むか決まらないので、数字を持つ行だけを当て先にした。変え方は、その中の字の最初の 1〜9 を 9 なら 1 に、ほかは 1 つ大きい数字に替える(素の本文の file を書き換える)。
  N2: 便 XB0 の ``mix_tables``(抜く)を読み戻した表に掛けて表の file を書き戻す。N3: 便 XT0 の ``mix_tables`` の 2(日本語のラベル)・N4: 同じく 1(計算の向き)を読み戻したタクソノミの表に掛けて書き戻す。
  混ぜ物の「違いを見つけた」は 全部同じ でないこと・「鳴り方が違う」は鳴り方が同じでないこと。数えるのは作れた混ぜ物だけ。
- 原稿の folder の bytes: 素の本文・本文の表・タクソノミの表・目次の file ごとの数と bytes。元の包みの bytes は PublicDoc の htm と xsd・linkbase 5 つの bytes の合計。XP0-7 は folder の bytes の合計 > 元の bytes の合計。
- 時間: 組む命令 1 回目の秒(小数 1 桁)。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT_PATH = os.path.abspath(__file__)

TAXONOMY_NAME = "_xp0_taxonomy_build_2026_11_22"


def _load_sibling(name, fname):
    u"""前の便の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


T = _load_sibling(TAXONOMY_NAME, "xbrl_taxonomy_build_2026-11-22.py")
B = T.B                                            # 便 XB0 の script(便 XT0 の script が一意の名で読んだもの)
V = T.V                                            # 便 XV0 の script
W = T.W                                            # 便 XG0 の script(Stop の型を 1 つにするため同じ object を使う)

SEAL_REL = "docs/XBRL_PACK_BUILD_SEAL_2026-11-22.md"
SEAL_COMMIT = "c03a3348"
SCRIPT_REL = "measure/xbrl_pack_build_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/pack_build_2026-11-22.json"
DOCS_DIR = W.DOCS_DIR
DOCS_WANT = W.DOCS_WANT

# ---- 封 §1 の決めごと(道具・掛け方・時間の上限・書き出しは便 XT0 の封 §1 と同じ。便 XT0 の script の字をそのまま受ける)
TOOL_VERSION = T.TOOL_VERSION
SHA_P = T.SHA_P
PLUGINS = T.PLUGINS
YEAR = T.YEAR
FACT_COLS = T.FACT_COLS
TIMEOUT_SEC = T.TIMEOUT_SEC
DEV_COUNT = T.DEV_COUNT
PUBLICDOC = B.PUBLICDOC
OUTPUT_KEYS = T.OUTPUT_KEYS
FILE_KINDS = T.FILE_KINDS
SEED_PREFIX = T.SEED_PREFIX
MIX_KINDS = (u"本文の数を変える", u"fact を抜く", u"ラベルを変える", u"計算の向きを返す")
MIX_IDS = ("N1", "N2", "N3", "N4")
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 上限) か None。XP0-4・XP0-5 は「断らなかった書類の数に等しい」・XP0-6 は「作れた数に等しい」
BOUNDS = collections.OrderedDict([
    ("XP0-1", (58, None)), ("XP0-2", (None, 2)), ("XP0-3", (58, None)), ("XP0-4", (u"断らなかった書類の数", None)), ("XP0-5", (u"断らなかった書類の数", None)), ("XP0-6", (u"作れた数", None)), ("XP0-7", (50, None))])
LIMITS = [
    u"原稿の folder は元の包みから作っている。folder の中身(タグを付ける場所・要素・文脈・単位・桁・符号・どの要素を作るか・木・ラベル・計算の向き)を決める力は測っていない。",
    u"マニフェスト・画像・監査報告書の包みは元のまま。",
    u"比べたのは公開の道具 1 つ(道具 P。司令塔が 1 行を直したもの)の書き出しで、道具が書き出さない性質の違いは見えない。便 XT0 の封への追記 1(概念の書き出しの比べ方の緩め)と追記 4 の門の穴は、この便にもそのまま在る。",
    u"EDINET の本物の検査とは照らしていない。",
    u"落とし方・組み方は開発の 5 本で決めた。62 本は便 XB0・便 XT0 で既に組み直した書類で、見ていない書類ではない。67 本は無作為ではない。有報だけ。",
    u"「EDINET の検査に通る」「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない。"]

Stop = W.Stop
od = collections.OrderedDict
sha256_bytes = W.sha256_bytes
sha256_file = W.sha256_file
dumps = W.dumps

# ---- 原稿の folder の file の名
INDEX_FILE = "index.json"
TAXONOMY_FILE = "taxonomy.json"
TEXT_FMT = "t%04d.txt"
TABLES_FMT = "t%04d.json"
FOLDER_GROUPS = (u"素の本文", u"本文の表", u"タクソノミの表", u"目次")
EXIT_USAGE, EXIT_DECLINE, EXIT_ERROR = 64, 2, 1
DECLINE_PREFIX = "DECLINE: "
REASON_MAX = 80


class Refuse(Exception):
    u"""落とす側・組む側の断り。``reason`` は固定の字(材料の字を入れない)。"""

    def __init__(self, reason):
        Exception.__init__(self, reason)
        self.reason = reason


# ======================================================================================================
# JSON(原稿の folder の表の書き方)
def jdump(o):
    return json.dumps(o, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def jload(data):
    return json.loads(data.decode("utf-8"), object_pairs_hook=collections.OrderedDict)


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def write_bytes(path, data):
    with open(path, "wb") as fh:
        fh.write(data)


def rel_of(name):
    u"""PublicDoc の file の名 → PublicDoc の直下からの相対の名。"""
    return name[len(PUBLICDOC):]


def safe_rel(rel):
    u"""目次の相対の名が安全か(``..``・``\\``・先頭の ``/``・空を断る)。"""
    if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel or "\x00" in rel or any(p in ("", "..", ".") for p in rel.split("/")):
        raise Refuse(u"目次の名が知らない形")
    return rel


def safe_local(name):
    u"""folder の中の file の名(下の folder を持たない)。"""
    if not isinstance(name, str) or not name or "/" in name or "\\" in name or name in (".", "..") or "\x00" in name:
        raise Refuse(u"目次の名が知らない形")
    return name


# ======================================================================================================
# 落とす(便 XB0 の剥がす・便 XT0 の剥がすを呼ぶ)
def peel_tables(entries):
    u"""元の包み([(ZipInfo, bytes)]) → (htm の並び [(名, 素の本文, 表 F, 表 H)] を名の昇順で, kind → 名, kind → 表)。知らない形・例外は ``Refuse``。"""
    try:
        files = B.build_files(entries)
        found = T.find_files(entries)
        names = od((k, found[k][0]) for k in FILE_KINDS)
        tables = T.strip_tables(od((k, found[k][1]) for k in FILE_KINDS))
    except (B.Decline, T.Decline) as exc:
        raise Refuse(exc.reason)
    except Exception:                                      # noqa: BLE001  知らない形は断る
        raise Refuse(u"落とす途中の例外")
    return files, names, tables


def write_folder(folder, files, names, tables):
    u"""原稿の folder を書く(元の字は置かない)。素の本文は bytes のまま。"""
    os.makedirs(folder)
    index = od([("htm", []), ("taxonomy", od([("file", TAXONOMY_FILE), ("names", od((k, rel_of(names[k])) for k in FILE_KINDS))]))])
    for i, (name, plain, F, H) in enumerate(files):
        write_bytes(os.path.join(folder, TEXT_FMT % i), plain.encode("utf-8"))
        write_bytes(os.path.join(folder, TABLES_FMT % i), jdump(od([("F", F), ("H", H)])))
        index["htm"].append(od([("name", rel_of(name)), ("text", TEXT_FMT % i), ("tables", TABLES_FMT % i)]))
    write_bytes(os.path.join(folder, TAXONOMY_FILE), jdump(od([("tables", tables)])))
    write_bytes(os.path.join(folder, INDEX_FILE), jdump(index))
    return index


def peel_folder(entries, folder):
    u"""元の包みから原稿の folder を作る。目次を返す。"""
    files, names, tables = peel_tables(entries)
    try:
        return write_folder(folder, files, names, tables)
    except Exception:                                      # noqa: BLE001  JSON に書けない形は断る
        shutil.rmtree(folder, ignore_errors=True)
        raise Refuse(u"folder に書けない形")


# ======================================================================================================
# 組む(原稿の folder だけを読む。別の process の命令の中身)
def render_folder(folder):
    u"""原稿の folder → {相対の名: bytes}。folder の中の目次・表・素の本文のほかを読まない。知らない形・例外は ``Refuse``。"""
    try:
        index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))
        out = od()
        for item in index["htm"]:
            rel = safe_rel(item["name"])
            plain = read_bytes(os.path.join(folder, safe_local(item["text"]))).decode("utf-8")
            tab = jload(read_bytes(os.path.join(folder, safe_local(item["tables"]))))
            if rel in out:
                raise Refuse(u"目次の名が重なる")
            out[rel] = B.build_text(plain, tab["F"], tab["H"]).encode("utf-8")
        tax = index["taxonomy"]
        tables = jload(read_bytes(os.path.join(folder, safe_local(tax["file"]))))["tables"]
        built = T.build_tables(tables)
        for k in FILE_KINDS:
            rel = safe_rel(tax["names"][k])
            if rel in out:
                raise Refuse(u"目次の名が重なる")
            out[rel] = built[k]
        return out
    except Refuse:
        raise
    except (B.Decline, T.Decline) as exc:
        raise Refuse(exc.reason)
    except Exception:                                      # noqa: BLE001  知らない形は断る
        raise Refuse(u"組む途中の例外")


def write_out(out, rendered):
    u"""出す folder に相対の名で書く。"""
    os.makedirs(out)
    for rel, data in rendered.items():
        path = os.path.join(out, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_bytes(path, data)


def build_main(args):
    u"""組む命令。引数は folder 2 つだけ。終わりの値: 0・64(使い方)・2(断り)・1(例外)。"""
    if len(args) != 2:
        print(u"使い方: build <原稿の folder> <出す folder>", file=sys.stderr)
        return EXIT_USAGE
    try:
        write_out(args[1], render_folder(args[0]))
    except Refuse as exc:
        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)
        return EXIT_DECLINE
    except Exception:                                      # noqa: BLE001
        print(u"ERROR", file=sys.stderr)
        return EXIT_ERROR
    return 0


def peel_main(args):
    u"""落とす命令。引数は zip と folder。"""
    if len(args) != 2:
        print(u"使い方: peel <zip> <原稿の folder>", file=sys.stderr)
        return EXIT_USAGE
    try:
        peel_folder(B.load_package(args[0]), args[1])
    except Refuse as exc:
        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)
        return EXIT_DECLINE
    except Exception:                                      # noqa: BLE001
        print(u"ERROR", file=sys.stderr)
        return EXIT_ERROR
    return 0


# ======================================================================================================
# 別の process で組む
def build_command(folder, out):
    u"""組む命令の引数の並び(引数は folder 2 つだけ)。"""
    return [sys.executable, "-I", SCRIPT_PATH, "build", folder, out]


def run_process(cmd, cwd, timeout):
    u"""(終わりの値, 標準のエラーの字, 時間の上限を超えたか)。shell を通さない。"""
    try:
        p = subprocess.run(list(cmd), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, shell=False)
    except subprocess.TimeoutExpired:
        return None, u"", True
    return p.returncode, p.stderr.decode("utf-8", "replace"), False


def decline_reason(stderr_text):
    u"""標準のエラーの字から固定の理由の行だけを読む。無ければ ``None``。"""
    for line in stderr_text.splitlines():
        if line.startswith(DECLINE_PREFIX):
            return line[len(DECLINE_PREFIX):][:REASON_MAX]
    return None


def exec_build(folder, out, cwd, proc=None):
    u"""組む命令を別の process で 1 回。(成功か, 断りの理由, 秒)。"""
    proc = proc or run_process
    t0 = time.time()
    rc, err, timed_out = proc(build_command(folder, out), cwd, TIMEOUT_SEC)
    secs = time.time() - t0
    if timed_out:
        return False, u"組む命令が時間の上限を超えた", secs
    if rc != 0:
        reason = decline_reason(err)
        return False, (reason if reason is not None else u"組む命令が 0 でない終わりの値で終わった"), secs
    return True, u"", secs


def read_tree(root):
    u"""folder の中の file の全部 → {相対の名: bytes}。"""
    out = {}
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            out[os.path.relpath(p, root).replace(os.sep, "/")] = read_bytes(p)
    return out


def expected_names(index):
    return set(item["name"] for item in index["htm"]) | set(index["taxonomy"]["names"].values())


def pack_replacements(tree):
    u"""出す folder の bytes({相対の名: bytes}) → {元の包みの中の名: bytes}。"""
    return dict((PUBLICDOC + rel, data) for rel, data in tree.items())


def rebuilt_pack(entries, tree):
    u"""元の包みの PublicDoc の htm・xsd・linkbase を出す folder の bytes に置き換えた包み(便 XT0 の ``package_with``)。ほかの file は元のまま。"""
    repl = pack_replacements(tree)
    return T.package_with(entries, od((n, n) for n in repl), repl)


def same_process_tree(files, names, tables):
    u"""同じ process の中で、表から直接組んだ bytes({相対の名: bytes})。例外は ``None``。"""
    try:
        out = dict((rel_of(n), t.encode("utf-8")) for n, t in B.rebuilt_texts(files))
        built = T.build_tables(tables)
        for k in FILE_KINDS:
            out[rel_of(names[k])] = built[k]
    except Exception:                                      # noqa: BLE001
        return None
    return out


# ======================================================================================================
# 混ぜ物(原稿の folder の file を disk の上で 1 か所だけ変える)
def load_htm_tables(folder, index):
    u"""[(名, 素の本文, 表 F, 表 H)] を目次の並びで。"""
    out = []
    for item in index["htm"]:
        plain = read_bytes(os.path.join(folder, item["text"])).decode("utf-8")
        tab = jload(read_bytes(os.path.join(folder, item["tables"])))
        out.append((item["name"], plain, tab["F"], tab["H"]))
    return out


def first_nonzero_digit(plain, e):
    u"""表 F の 1 行の中の字の、最初の 1〜9(ASCII)の位置。0 だけの字・数字の無い字は ``None``。"""
    content = plain[e["start"]:e["end"]]
    if B.is_zero_content(content):
        return None
    m = re.search(r"[1-9]", content)
    return e["start"] + m.start() if m else None


def bump_digit(ch):
    return "1" if ch == "9" else chr(ord(ch) + 1)


def change_number(folder, index):
    u"""N1: 当て先の素の本文の数字を 1 つ変える。変えたら ``True``。"""
    files = load_htm_tables(folder, index)
    for fi, i in B.num_pool(files):
        _n, plain, F, _h = files[fi]
        at = first_nonzero_digit(plain, F[i])
        if at is not None:
            write_bytes(os.path.join(folder, index["htm"][fi]["text"]), (plain[:at] + bump_digit(plain[at]) + plain[at + 1:]).encode("utf-8"))
            return True
    return False


def change_fact_row(folder, index):
    u"""N2: 表 F の最初の nonFraction の行を除いて書き戻す。"""
    files = load_htm_tables(folder, index)
    try:
        m = B.mix_tables(files, B.MIX_KINDS[0])
    except B.Decline:
        m = None
    if m is None:
        return False
    fi, F2, H2 = m
    write_bytes(os.path.join(folder, index["htm"][fi]["tables"]), jdump(od([("F", F2), ("H", H2)])))
    return True


def change_taxonomy(folder, index, idx):
    u"""N3(idx = 2)・N4(idx = 1): 読み戻したタクソノミの表に便 XT0 の混ぜ物を掛けて書き戻す。"""
    path = os.path.join(folder, index["taxonomy"]["file"])
    tables = jload(read_bytes(path))["tables"]
    m = T.mix_tables(tables, idx)
    if m is None:
        return False
    kind, T2 = m
    tables[kind] = T2
    write_bytes(path, jdump(od([("tables", tables)])))
    return True


def change_folder(folder, n):
    u"""混ぜ物 ``n``(0〜3)を folder に掛ける。変えたら ``True``(当て先が無ければ ``False``)。"""
    index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))
    if n == 0:
        return change_number(folder, index)
    if n == 1:
        return change_fact_row(folder, index)
    return change_taxonomy(folder, index, 2 if n == 2 else 1)


def empty_mixes(mixtures):
    return [od([(u"種類", k), (u"作った", False), (u"違いを見つけた", False), (u"鳴り方が違う", False)]) for k in MIX_KINDS] if mixtures else []


# ======================================================================================================
# 書類 1 本
def folder_stats(folder, index):
    u"""原稿の folder の file の数と bytes(素の本文・本文の表・タクソノミの表・目次)。"""
    sizes = od((g, od([(u"file", 0), (u"bytes", 0)])) for g in FOLDER_GROUPS)

    def add(g, name):
        sizes[g][u"file"] += 1
        sizes[g][u"bytes"] += os.path.getsize(os.path.join(folder, name))
    for item in index["htm"]:
        add(u"素の本文", item["text"])
        add(u"本文の表", item["tables"])
    add(u"タクソノミの表", index["taxonomy"]["file"])
    add(u"目次", INDEX_FILE)
    sizes[u"合計 bytes"] = sum(v[u"bytes"] for v in sizes.values())
    return sizes


def zero_stats():
    sizes = od((g, od([(u"file", 0), (u"bytes", 0)])) for g in FOLDER_GROUPS)
    sizes[u"合計 bytes"] = 0
    return sizes


def orig_stats(entries):
    u"""元の包みの PublicDoc の htm と xsd・linkbase 5 つの file の数と bytes。"""
    htm = od([(u"file", 0), (u"bytes", 0)])
    tax = od([(u"file", 0), (u"bytes", 0)])
    for info, data in entries:
        n = info.filename
        if B.is_public_htm(n):
            htm[u"file"] += 1
            htm[u"bytes"] += len(data)
        elif n.startswith(PUBLICDOC) and "/" not in n[len(PUBLICDOC):] and any(n.endswith(T.FILE_SUFFIX[k]) for k in FILE_KINDS):
            tax[u"file"] += 1
            tax[u"bytes"] += len(data)
    return od([(u"htm", htm), (u"タクソノミ", tax), (u"合計 bytes", htm[u"bytes"] + tax[u"bytes"])])


def declined_rec(rec, reason, mixtures):
    rec[u"断った"], rec[u"断った理由"] = True, reason
    rec[u"組む命令の秒"] = rec.get(u"組む命令の秒")
    rec[u"組み直しの書き出しの行の数"] = None
    rec[u"組み直しの fact の行の数"] = None
    rec[u"組み直しの 1 回"] = None
    rec[u"書き出しが同じ"] = od((k, False) for k in OUTPUT_KEYS)
    rec[u"タクソノミが同じ"] = rec[u"fact が同じ"] = rec[u"鳴り方が同じ"] = rec[u"全部同じ"] = False
    rec[u"2 度が同じ"] = rec[u"道筋が同じ"] = False
    rec[u"混ぜ物"] = empty_mixes(mixtures)
    return rec


def process_doc(tool, zip_path, tmp_root=None, runner=None, mixtures=False, proc=None):
    u"""書類 1 本。書類ごとの数。元の包みと組み直した包みを同じ掛け方で 1 回ずつ(掛け方 A・B)。"""
    entries = B.load_package(zip_path)
    rec = od([(u"断った", False), (u"断った理由", u"")])
    d = tempfile.mkdtemp(prefix="xp0_", dir=tmp_root)
    try:
        orig_zip = os.path.join(d, "orig.zip")
        B.write_package(entries, orig_zip)
        orig, orig_outs, orig_facts = T.run_package(tool, orig_zip, d, "orig", runner)
        rec[u"元の書き出しの行の数"] = od((k, len(orig_outs[k])) for k in OUTPUT_KEYS)
        rec[u"元の fact の行の数"] = len(orig_facts)
        rec[u"元の 1 回"] = orig
        rec[u"元の包みの bytes"] = orig_stats(entries)
        rec[u"原稿の folder"] = zero_stats()
        rec[u"原稿が元より大きい"] = False
        rec[u"組む命令の秒"] = None
        cwd = os.path.join(d, "cwd")
        os.makedirs(cwd)
        folder = os.path.join(d, "manuscript")
        try:
            files, names, tables = peel_tables(entries)
            index = write_folder(folder, files, names, tables)
        except Refuse as exc:
            return declined_rec(rec, exc.reason, mixtures)
        except Exception:                                  # noqa: BLE001
            return declined_rec(rec, u"folder に書けない形", mixtures)
        rec[u"原稿の folder"] = folder_stats(folder, index)
        rec[u"原稿が元より大きい"] = rec[u"原稿の folder"][u"合計 bytes"] > rec[u"元の包みの bytes"][u"合計 bytes"]
        out1 = os.path.join(d, "out1")
        ok, reason, secs = exec_build(folder, out1, cwd, proc)
        rec[u"組む命令の秒"] = round(secs, 1)
        if not ok:
            return declined_rec(rec, reason, mixtures)
        tree = read_tree(out1)
        if set(tree) != expected_names(index):
            return declined_rec(rec, u"出す folder の file の名が目次と合わない", mixtures)
        out2 = os.path.join(d, "out2")
        ok2, _r2, _s2 = exec_build(folder, out2, cwd, proc)
        rec[u"2 度が同じ"] = bool(ok2 and read_tree(out2) == tree)
        same_tree = same_process_tree(files, names, tables)
        rec[u"道筋が同じ"] = bool(same_tree is not None and same_tree == tree)
        new_zip = os.path.join(d, "new.zip")
        B.write_package(rebuilt_pack(entries, tree), new_zip)
        new, new_outs, new_facts = T.run_package(tool, new_zip, d, "new", runner)
        rec[u"組み直しの書き出しの行の数"] = od((k, len(new_outs[k])) for k in OUTPUT_KEYS)
        rec[u"組み直しの fact の行の数"] = len(new_facts)
        rec[u"組み直しの 1 回"] = new
        T.compare_into(rec, orig_outs, orig_facts, orig, new_outs, new_facts, new)
        mixes = empty_mixes(mixtures)
        for i, item in enumerate(mixes):
            mf = os.path.join(d, "mixf%d" % i)
            shutil.copytree(folder, mf)
            try:
                changed = change_folder(mf, i)
            except Exception:                              # noqa: BLE001
                changed = False
            if not changed:
                continue
            mo = os.path.join(d, "mixo%d" % i)
            okm, _rm, _sm = exec_build(mf, mo, cwd, proc)
            if not okm:
                continue
            mtree = read_tree(mo)
            if set(mtree) != expected_names(index):
                continue
            mz = os.path.join(d, "mix%d.zip" % i)
            B.write_package(rebuilt_pack(entries, mtree), mz)
            mone, mouts, mfacts = T.run_package(tool, mz, d, "mix%d" % i, runner)
            item[u"作った"] = True
            tax = all(T.outputs_same(orig_outs, mouts).values())
            item[u"違いを見つけた"] = not (tax and B.facts_same(orig_facts, mfacts))
            item[u"鳴り方が違う"] = not B.sounds_same(orig, mone)
        rec[u"混ぜ物"] = mixes
        return rec
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ======================================================================================================
# 数える(封 §2)
def group_totals(entries):
    u"""書類ごとの数の並び → §2 の 1・2。"""
    cls = od((c, 0) for c in V.CLASSES)
    declined = same_all = same_tax = same_facts = same_sound = twice = path = bigger = low_concepts = 0
    reasons = collections.Counter()
    same_out = od((k, 0) for k in OUTPUT_KEYS)
    rows = od((k, 0) for k in OUTPUT_KEYS)
    folder = od((g, od([(u"file", 0), (u"bytes", 0)])) for g in FOLDER_GROUPS)
    folder_total = orig_htm = orig_tax = 0
    orig_files = od([(u"htm", 0), (u"タクソノミ", 0)])
    secs = 0.0
    for e in entries:
        if e[u"断った"]:
            declined += 1
            reasons[e[u"断った理由"]] += 1
        else:
            cls[e[u"組み直しの 1 回"][u"類"]] += 1
        same_all += 1 if e[u"全部同じ"] else 0
        same_tax += 1 if e[u"タクソノミが同じ"] else 0
        same_facts += 1 if e[u"fact が同じ"] else 0
        same_sound += 1 if e[u"鳴り方が同じ"] else 0
        twice += 1 if e[u"2 度が同じ"] else 0
        path += 1 if e[u"道筋が同じ"] else 0
        bigger += 1 if e[u"原稿が元より大きい"] else 0
        low_concepts += 1 if e[u"元の書き出しの行の数"][OUTPUT_KEYS[0]] <= 1 else 0
        for k in OUTPUT_KEYS:
            same_out[k] += 1 if e[u"書き出しが同じ"][k] else 0
            rows[k] += e[u"元の書き出しの行の数"][k]
        for g in FOLDER_GROUPS:
            for f in (u"file", u"bytes"):
                folder[g][f] += e[u"原稿の folder"][g][f]
        folder_total += e[u"原稿の folder"][u"合計 bytes"]
        orig_htm += e[u"元の包みの bytes"][u"htm"][u"bytes"]
        orig_tax += e[u"元の包みの bytes"][u"タクソノミ"][u"bytes"]
        orig_files[u"htm"] += e[u"元の包みの bytes"][u"htm"][u"file"]
        orig_files[u"タクソノミ"] += e[u"元の包みの bytes"][u"タクソノミ"][u"file"]
        if e[u"組む命令の秒"] is not None:
            secs += e[u"組む命令の秒"]
    return od([
        (u"書類", len(entries)), (u"断った書類", declined), (u"断った理由ごと", od(sorted(reasons.items()))), (u"断らなかった書類", len(entries) - declined),
        (u"全部同じ書類", same_all), (u"タクソノミが同じ書類", same_tax), (u"fact が同じ書類", same_facts), (u"鳴り方が同じ書類", same_sound),
        (u"書き出しごとに同じ書類", same_out), (u"組み直した包みの 1 回の類ごと", cls), (u"2 度が同じ書類", twice), (u"道筋が同じ書類", path),
        (u"原稿の folder の合計", od([(u"種類ごと", folder), (u"bytes の合計", folder_total)])),
        (u"元の包みの合計", od([(u"file", orig_files), (u"htm の bytes", orig_htm), (u"タクソノミの bytes", orig_tax), (u"bytes の合計", orig_htm + orig_tax)])),
        (u"原稿が元より大きい書類", bigger), (u"組む命令の秒の合計", round(secs, 1)),
        (u"元の書き出しの行の数の合計", rows), (u"元の概念の行が 1 以下の書類", low_concepts)])


def mix_totals(per_doc):
    made = found = sound = 0
    for e in per_doc:
        for m in e[u"混ぜ物"]:
            if m[u"作った"]:
                made += 1
                found += 1 if m[u"違いを見つけた"] else 0
                sound += 1 if m[u"鳴り方が違う"] else 0
    return od([(u"混ぜ物の数", sum(len(e[u"混ぜ物"]) for e in per_doc)), (u"作れた数", made), (u"違いを見つけた数", found), (u"鳴り方が違う数", sound)])


def mix_kinds_totals(per_doc):
    u"""混ぜ物の種類ごとの (作れた・違いを見つけた・鳴り方が違う)。"""
    out = od()
    for i, k in enumerate(MIX_KINDS):
        items = [e[u"混ぜ物"][i] for e in per_doc if len(e[u"混ぜ物"]) > i]
        out[k] = od([(u"作れた", sum(1 for m in items if m[u"作った"])), (u"違いを見つけた", sum(1 for m in items if m[u"作った"] and m[u"違いを見つけた"])),
                     (u"鳴り方が違う", sum(1 for m in items if m[u"作った"] and m[u"鳴り方が違う"]))])
    return out


def totals_of(per_doc, dev_count=DEV_COUNT):
    dev, prod = per_doc[:dev_count], per_doc[dev_count:]
    return od([(u"開発の 5 本", group_totals(dev)), (u"本番だけの %d 本" % (len(per_doc) - dev_count), group_totals(prod)), (u"全部", group_totals(per_doc)),
               (u"混ぜ物", mix_totals(dev)), (u"混ぜ物の種類ごと", mix_kinds_totals(dev))])


def judged(tot, n=DOCS_WANT):
    u"""封 §4 の判定に要る数(当たり・外れは書かない)。"""
    prod = tot[[k for k in tot if k.startswith(u"本番だけの")][0]]
    mx = tot[u"混ぜ物"]
    kept = prod[u"断らなかった書類"]
    return od([
        (u"XP0-1 全部同じ書類", od([(u"書類", prod[u"全部同じ書類"]), (u"分母", prod[u"書類"])])),
        (u"XP0-2 断った書類", od([(u"書類", prod[u"断った書類"]), (u"分母", prod[u"書類"])])),
        (u"XP0-3 鳴り方が同じ書類", od([(u"書類", prod[u"鳴り方が同じ書類"]), (u"分母", prod[u"書類"])])),
        (u"XP0-4 2 度が同じ書類", od([(u"書類", prod[u"2 度が同じ書類"]), (u"分母(断らなかった書類)", kept)])),
        (u"XP0-5 道筋が同じ書類", od([(u"書類", prod[u"道筋が同じ書類"]), (u"分母(断らなかった書類)", kept)])),
        (u"XP0-6 作れた混ぜ物のうち違いを見つけたもの", od([(u"個", mx[u"違いを見つけた数"]), (u"分母", mx[u"作れた数"])])),
        (u"XP0-7 原稿の folder の bytes の合計が元の bytes の合計より大きい書類", od([(u"書類", prod[u"原稿が元より大きい書類"]), (u"分母", prod[u"書類"])])),
        (u"補 作れた混ぜ物の数・混ぜ物の数", od([(u"作れた", mx[u"作れた数"]), (u"分母", mx[u"混ぜ物の数"])]))])


# ======================================================================================================
# 道具の確かめ・記録
def check_tool(tool, runner=None, sha_reader=sha256_file, want_version=TOOL_VERSION, want_sha=SHA_P):
    return T.check_tool(tool, runner, sha_reader, want_version, want_sha)


def dev_docs(docs_dir, count=DEV_COUNT):
    u"""置き場の並びの頭から ``count`` 本だけを選ぶ(便 XB0 の関数。残りの zip は開かない)。"""
    return B.dev_docs(docs_dir, count)


def build_record(tool_p, docs_dir=None, want=DOCS_WANT, runner=None, sha_reader=sha256_file, tmp_root=None, want_version=TOOL_VERSION, want_sha=SHA_P, dev_count=DEV_COUNT, proc=None, progress=None):
    u"""道具を確かめてから、書類を 1 本ずつ掛ける。(記録, secret)。書かない。"""
    docs = W.select_docs(docs_dir or DOCS_DIR, want)
    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)
    per_doc = []
    elems, labels = set(), set()
    for n, (_stem, p, _xs) in enumerate(docs, 1):
        t0 = time.time()
        r = process_doc(tool_p, p, tmp_root, runner, mixtures=(n <= dev_count), proc=proc)
        per_doc.append(od([(u"番号", n)] + list(r.items())))
        el, lb = T.secret_of([B.load_package(p)])
        elems |= el
        labels |= lb
        if progress is not None:
            progress(u"doc %d/%d(%.0f 秒)" % (n, len(docs), time.time() - t0))
    ecodes = set()
    for _stem, _p, xs in docs:
        for x in xs:
            ecodes.update(re.findall(r"E\d{5}", x))
    secret = (labels, elems, [d[0] for d in docs], ecodes, set())
    return assemble(per_doc, W.order_sha256([d[0] for d in docs]), info, dev_count), secret


def assemble(per_doc, order_sha, info, dev_count=DEV_COUNT):
    tot = totals_of(per_doc, dev_count)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XP0(受理済みの有報の公開用の file を原稿の folder に落とし、folder だけを読む別の process の命令で htm・xsd・linkbase を組み直すと、公開の道具が読むタクソノミ・fact・検査の鳴り方は元と同じになるか)(0 USD・engine は読まない)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"材料"] = od([
        (u"書類の本数", len(per_doc)), (u"書類の file 名の並びの sha256", order_sha), (u"開発の 5 本の番号", list(range(1, dev_count + 1))),
        (u"道具の版", info[u"版"]), (u"道具 P の ModelValue.py の sha256", info[u"ModelValue.py の sha256"]), (u"道具 P の package の一覧の sha256", info[u"package の一覧の sha256"]),
        (u"Python の版(道具 P)", info[u"Python の版"]), (u"規則の年", YEAR), (u"混ぜ物の種類", list(MIX_KINDS)), (u"時間の上限(秒)", TIMEOUT_SEC)])
    rec[u"書類"] = per_doc
    rec[u"集計"] = tot
    rec[u"予測の判定に要る数(XP0-1〜XP0-7。当たり・外れは結果の文書で)"] = judged(tot, len(per_doc))
    rec[u"限界"] = list(LIMITS)
    return rec


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(docID・EDINET コード・file の名・要素の名・ラベルの字・role の URI・指摘の行の本文)が無いか。在れば止める。"""
    T.check_clean(rec, text, secret)


def verify_record(rec, text=None, want=DOCS_WANT, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査する(道具は呼ばない・掛け直さない)。違えば止まる。"""
    docs = rec.get(u"書類")
    if not isinstance(docs, list) or len(docs) != want or rec[u"材料"][u"書類の本数"] != want:
        raise Stop(u"**記録の書類が 67 本でない。止める**")
    for i, d in enumerate(docs, 1):
        if d.get(u"番号") != i:
            raise Stop(u"**記録の書類の番号が違う。止める**")
        for k in (u"断った", u"断った理由", u"元の書き出しの行の数", u"元の fact の行の数", u"元の 1 回", u"元の包みの bytes", u"原稿の folder", u"原稿が元より大きい", u"組む命令の秒", u"書き出しが同じ",
                  u"タクソノミが同じ", u"fact が同じ", u"鳴り方が同じ", u"全部同じ", u"2 度が同じ", u"道筋が同じ", u"混ぜ物", u"組み直しの 1 回"):
            if k not in d:
                raise Stop(u"**記録の書類の形が違う。止める**")
        if d[u"断った"] != (d[u"組み直しの 1 回"] is None) or (d[u"断った"] and (d[u"全部同じ"] or d[u"タクソノミが同じ"] or d[u"fact が同じ"] or d[u"鳴り方が同じ"] or d[u"2 度が同じ"] or d[u"道筋が同じ"])) or (not d[u"断った"] and d[u"断った理由"]) or (d[u"断った"] and not d[u"断った理由"]):
            raise Stop(u"**断った書類の形が違う。止める**")
        if d[u"全部同じ"] != (d[u"タクソノミが同じ"] and d[u"fact が同じ"]) or d[u"タクソノミが同じ"] != all(d[u"書き出しが同じ"].values()):
            raise Stop(u"**全部同じ・タクソノミが同じの導き方が違う。止める**")
        if list(d[u"書き出しが同じ"]) != list(OUTPUT_KEYS) or list(d[u"元の書き出しの行の数"]) != list(OUTPUT_KEYS) or list(d[u"原稿の folder"]) != list(FOLDER_GROUPS) + [u"合計 bytes"]:
            raise Stop(u"**書き出し・folder の欄が違う。止める**")
        if d[u"原稿が元より大きい"] != (d[u"原稿の folder"][u"合計 bytes"] > d[u"元の包みの bytes"][u"合計 bytes"]):
            raise Stop(u"**原稿が元より大きいの導き方が違う。止める**")
        if d[u"元の 1 回"][u"類"] not in V.CLASSES or (d[u"組み直しの 1 回"] is not None and d[u"組み直しの 1 回"][u"類"] not in V.CLASSES):
            raise Stop(u"**1 回の類が違う。止める**")
        if len(d[u"混ぜ物"]) != (len(MIX_KINDS) if i <= dev_count else 0) or [m[u"種類"] for m in d[u"混ぜ物"]] != (list(MIX_KINDS) if i <= dev_count else []):
            raise Stop(u"**混ぜ物の形が違う。止める**")
        for m in d[u"混ぜ物"]:
            if not m[u"作った"] and (m[u"違いを見つけた"] or m[u"鳴り方が違う"]):
                raise Stop(u"**作れなかった混ぜ物の形が違う。止める**")
    tot = totals_of(docs, dev_count)
    if dumps(tot) != dumps(rec[u"集計"]) or dumps(judged(tot, len(docs))) != dumps(rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]]):
        raise Stop(u"**記録の合計が書類ごとの数と合わない。止める**")
    check_clean(rec, text if text is not None else dumps(rec))


def record_text(rec, secret=None):
    text = dumps(rec)
    check_clean(rec, text, secret)
    return text


def write_exclusive(path, data):
    with open(path, "xb") as fh:
        fh.write(data)


def write_record(path, rec, secret=None):
    u"""書く前と書いた後に検査する。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(path))
    text = record_text(rec, secret)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_exclusive(path, text.encode("utf-8"))
    with io.open(path, encoding="utf-8") as fh:
        back = fh.read()
    try:
        check_clean(rec, back, secret)
    except SystemExit:
        os.remove(path)
        raise


def run(tool_p, root=ROOT, docs=None, out=None, want=DOCS_WANT, runner=None, sha_reader=sha256_file, tmp_root=None, want_version=TOOL_VERSION, want_sha=SHA_P, say=print, dev_count=DEV_COUNT, proc=None, progress=None):
    rec, secret = build_record(tool_p, docs, want, runner, sha_reader, tmp_root, want_version, want_sha, dev_count, proc, progress)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(書類 %d)" % (os.path.basename(out), rec[u"材料"][u"書類の本数"]))
    return rec


def check(root=ROOT, rec_path=None, say=print, want=DOCS_WANT, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査する。置き場も道具も読まない。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    verify_record(rec, text, want, dev_count)
    say(u"--check: 記録の形・合計・禁止のものの検査は通った(書類 %d)" % len(rec[u"書類"]))
    return rec


def dev_run(tool_p, docs_dir=None, runner=None, tmp_root=None, say=print, proc=None):
    u"""開発の 5 本だけ(記録は書かない)。(書類ごとの数の並び)。"""
    docs = dev_docs(docs_dir or DOCS_DIR, DEV_COUNT)
    check_tool(tool_p, runner)
    per = []
    t_all = time.time()
    for n, (_s, p, _x) in enumerate(docs, 1):
        t0 = time.time()
        r = process_doc(tool_p, p, tmp_root, runner, mixtures=True, proc=proc)
        per.append(od([(u"番号", n)] + list(r.items())))
        say(u"doc %d(%.0f 秒): 断った=%s(%s) 全部同じ=%s タクソノミ=%s fact=%s 鳴り方=%s 2度=%s 道筋=%s 書き出し=%s 組む命令=%s秒 folder=%s 元=%s 混ぜ物=%s" % (
            n, time.time() - t0, r[u"断った"], r[u"断った理由"], r[u"全部同じ"], r[u"タクソノミが同じ"], r[u"fact が同じ"], r[u"鳴り方が同じ"], r[u"2 度が同じ"], r[u"道筋が同じ"],
            json.dumps(r[u"書き出しが同じ"], ensure_ascii=False), r[u"組む命令の秒"], r[u"原稿の folder"][u"合計 bytes"], r[u"元の包みの bytes"][u"合計 bytes"],
            [(m[u"種類"], m[u"作った"], m[u"違いを見つけた"], m[u"鳴り方が違う"]) for m in r[u"混ぜ物"]]))
    say(u"開発の 5 本の合計: %.0f 秒" % (time.time() - t_all))
    return per


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "build":
        sys.exit(build_main(argv[1:]))
    if argv and argv[0] == "peel":
        sys.exit(peel_main(argv[1:]))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="記録の形・合計・禁止のものを検査する。道具は呼ばない")
    ap.add_argument("--dev", action="store_true", help="開発の 5 本だけ掛ける。記録は書かない")
    ap.add_argument("--tool-p", default=None, help="道具 P(1 行の直し)の venv の場所")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="書類の置き場(既定は封の字)")
    a = ap.parse_args(argv)
    if a.check:
        check(root=a.root)
        return
    if not a.tool_p:
        raise Stop(u"**--tool-p が要る。止める**")
    if a.dev:
        dev_run(a.tool_p, docs_dir=a.docs)
        return
    run(a.tool_p, root=a.root, docs=a.docs, progress=lambda s: print(s, file=sys.stderr))


if __name__ == "__main__":
    main()
