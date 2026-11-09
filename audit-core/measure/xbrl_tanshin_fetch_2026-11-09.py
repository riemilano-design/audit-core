# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TANSHIN_HUMAN_TEXT_SEAL_2026-11-09.md §0-2 の 5・§1・§2 の 1 ― TS(人が書いた有報の外の文で engine を測る)の材料の取得。**0 USD。外部への呼び出しは TDnet の ZIP の取得だけ。鍵は読まない。**

    python3 measure/xbrl_tanshin_fetch_2026-11-09.py                                   # 本番: 封 §1 の 17 本を取り、cache の新しい folder に置き、記録を書く
    python3 measure/xbrl_tanshin_fetch_2026-11-09.py --only <証券コード> --out PATH      # 使い捨て(本番の folder にも記録にも書かない)

やること(順序は封 §0-2 の 5 のとおり。**1 本でも sha256 が封の表と違えば、その場で止めて何も書かない**)
  1. 封 §1 の 17 行(証券コード・TDnet の番号・ZIP の sha256)を **字で** 持つ(この file の ``TABLE``。門が封の表と同じ字か照らす)
  2. 有報の側の対応(読むだけ): ``fixtures/xbrl/aiforms/gen_2026-11-03.json`` の ``会社の選び`` の書類の ZIP の jpdei の ``SecurityCodeDEI`` と 17 本の証券コードを 1 対 1 で結ぶ
     (結べない・2 つ以上に結べる・同じ書類に 2 つが結ぶ のどれかなら止める)。有報の ZIP の sha256 は 97 書類の記録と照らす
  3. ``https://www2.jpx.co.jp/disc/<証券コード>/<番号>.zip`` を urllib で取る(User-Agent に browser の字を付ける。付けないと 403)。1 本ごとに 1 秒待つ。
     置き場 ``~/.cache/audit-core/tanshin-2026-11-09/<証券コード>/<番号>.zip``。既に在れば取り直さず sha256 だけ照らす
  4. 全部の sha256 が表と一致してから、新しい folder にだけ書く。他の cache(edinet・edinet-fresh-2026-10-21・edinet-prior-2026-11-02・aiforms-*)は読むだけで、
     件数と名前の一覧の sha256 を前後で照らす(新しい folder は除く)
  5. 記録 ``fixtures/xbrl/tanshin/fetched_2026-11-09.json``(17 行 = 証券コード・番号・ZIP の sha256・HTTP の状態・byte 数・docID・有報の ZIP の sha256)。docID はこの記録の file だけに書く

``--only`` を付けた走らせ方は本番の記録・本番の folder を作らない: ``--out`` を必ず指定する(指定が無ければ止める)。``--out`` を付けて ``--cache`` を付けないときの置き場は ``<--out の folder>/cache``。

通信は ``default_fetcher`` の中の urllib だけ(試験は fetcher を差し替える)。
"""
from __future__ import print_function

import argparse
import collections
import datetime
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    u"""importlib で読み込む。読み込みの前に居た名前は、読み込みの後に元の object へ戻す(自分の名前だけ残す)。"""
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != mod_name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


GEN = load_module("xbrl_aiforms_gen_2026-11-03.py", "aiforms_gen_for_tanshin_fetch")
Stop = GEN.Stop

SEAL_REL = "docs/XBRL_TANSHIN_HUMAN_TEXT_SEAL_2026-11-09.md"
SEAL_COMMIT = "5bba61e"
SCRIPT_REL = "measure/xbrl_tanshin_fetch_2026-11-09.py"
REC_DIR_REL = "fixtures/xbrl/tanshin"
OUT_REL = REC_DIR_REL + "/fetched_2026-11-09.json"
CACHE_NAME = "tanshin-2026-11-09"
URL_FMT = "https://www2.jpx.co.jp/disc/%s/%s.zip"
#: browser の字(付けないと 403。封 §0-1 の 1)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
INTERVAL_SEC = 1.0
TIMEOUT_SEC = 120
N_ROWS = 17
#: 封 §1 の表の 17 行: (#, 証券コード 5 桁, TDnet の番号, ZIP の sha256, 概況の字数(下見), claim(下見・P32E))。門が封の表と同じ字か照らす
TABLE = (
    (1, "151A0", "081220260810517389", "f534e693f2fbb9769e4659b0facea8bd48c129a462809d4f36aa00415184c905", 3586, 64),
    (2, "192A0", "081220260629583893", "20810e54b3e96c408cf0fd42b43f94b5aa44ce144c73f31a183cbd5a1e9aded6", 3147, 56),
    (3, "21680", "081220260604562997", "58e660a41e12e52cf033daeb66dac6e91269639a29ca033626ae819fd4e87426", 10052, 211),
    (4, "24620", "081220260713591892", "d180d4b98652360f1313e2b49baf360694e71efa8e774f8d9ea1f249bb328880", 8225, 89),
    (5, "36450", "081220260715594011", "6acc040a02179827dc396f5d8f6a0a0a821b1827afaccb27d8cb827d2e8a8218", 1782, 12),
    (6, "40760", "081220260708589871", "895d288ce9dd87139132b18ceed433443200219f9535450a0c9c073397600d20", 4047, 57),
    (7, "42630", "081220260806512603", "292397e771136b4d62c3e4e87ab68ba7ebd9178825c3358a254011c5de351ed7", 5363, 77),
    (8, "44300", "081220260714593137", "36b5bb97f98a06b0d288962b8b6d835cf6c9d5ba44cf9fffeb4f6a790e118977", 6171, 51),
    (9, "58690", "081220260714593282", "083d2354d766bbe367d0b878efb02eef62bd2230e3d3411f3d912e40d38cc027", 3194, 62),
    (10, "62390", "081220260807513664", "96915244942b6b4f3ba2afa6b92ba584fe7df866a309f9ed59f196365bc406fe", 4202, 78),
    (11, "65050", "081220260714593677", "1df23ef70dae7c5f3944d78e2bd4d7bb3cc6b15f6209e66a1f5e438a70a9d2cf", 3822, 54),
    (12, "70630", "081220260814521341", "2ca5fd9e348e444717b1d69e6b33e71ffcd8a493a9fec87f03496d0a20f1812e", 6405, 66),
    (13, "76360", "081220260807514952", "eab5bf3d6fd077881a1733daf15724e98f01c34d72028a292ffab0b3df16072f", 2431, 58),
    (14, "76730", "081220260713591794", "4f74e49dd93dfed28daeb6489a900b48e8bf26c57139b7b87c3d0438b4645f79", 4961, 90),
    (15, "78130", "081220260612569502", "c21a9ccc818cf99ed808f84bf2ce5e71018288ac6415240d00ac9b3404db4251", 5562, 67),
    (16, "80570", "081220260901529425", "48c35d9a8921d977e37de64149d744fbfb434bd881cb9e0ae2c0726ecf84e971", 7369, 128),
    (17, "89450", "081220260810516204", "568d0d28284fc386d9d775536f4cad34938ae1df7914bff1286e0d32b8a32131", 4059, 63),
)
GEN_REL = GEN.GEN_REL
REGRESS97_REL = GEN.REGRESS97_REL
CODE_RE = re.compile(r"<jpdei_cor:SecurityCodeDEI[^>]*>\s*([0-9A-Z]+)\s*<")
ZIP_MAGIC = b"PK\x03\x04"


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def default_cache_dir():
    u"""本番の置き場 ``~/.cache/audit-core/tanshin-2026-11-09``。呼ぶ時に HOME を見る。"""
    return os.path.join(os.path.expanduser("~"), ".cache", "audit-core", CACHE_NAME)


def display_path(path):
    home = os.path.expanduser("~")
    if path == home or path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path


def zip_path(cache_dir, code, number):
    return os.path.join(cache_dir, code, number + ".zip")


def read_caches():
    u"""読むだけの folder(既存の cache 3 つ + 文の置き場所 2 つ)。新しい folder は含めない。"""
    c = collections.OrderedDict(GEN.EXISTING_CACHES)
    c[os.path.basename(GEN.NEW_CACHE)] = GEN.NEW_CACHE
    c["aiforms-f5-2026-11-03"] = os.path.join(GEN.CACHE_BASE, "aiforms-f5-2026-11-03")
    return c


def select_rows(only):
    u"""表の行(only = 証券コード 1 つ。表に無ければ止める)。"""
    rows = list(TABLE)
    if only is None:
        return rows
    sel = [r for r in rows if r[1] == only]
    if not sel:
        raise Stop(u"**--only の証券コードが封 §1 の表に無い。止める**")
    return sel


def default_fetcher(url, user_agent=USER_AGENT, timeout=TIMEOUT_SEC):
    u"""通信する唯一の所。(HTTP の状態, 本文の bytes)。404 などは例外にせず状態で返す。それ以外の例外は呼び出し側が止める。"""
    import urllib.error
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def security_code(zb):
    u"""有報の ZIP の PublicDoc の .xbrl の jpdei の SecurityCodeDEI(無ければ None)。"""
    import zipfile
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        for n in z.namelist():
            if n.startswith("XBRL/PublicDoc/") and n.endswith(".xbrl"):
                m = CODE_RE.search(z.read(n).decode("utf-8", "replace"))
                if m:
                    return m.group(1)
    return None


def company_rows(root):
    u"""生成の記録の 20 社の行(97 の記録の行)。(docID の列, {docID: 行})。"""
    gen = GEN.jload(os.path.join(root, GEN_REL))
    r97 = dict((r["docID"], r) for r in GEN.jload(os.path.join(root, REGRESS97_REL))[u"書類"])
    ids = list(gen[u"会社の選び"][u"docID"])
    for d in ids:
        if d not in r97:
            raise Stop(u"**選んだ会社が 97 の記録に無い。止める**")
    return ids, dict((d, r97[d]) for d in ids)


def map_docids(root, codes, caches=None):
    u"""{証券コード: (docID, 有報の ZIP の sha256)}。20 社の有報の ZIP の SecurityCodeDEI と codes を 1 対 1 で結ぶ(結べない・2 つ以上・同じ書類に 2 つ、は止める)。"""
    caches = caches or GEN.EXISTING_CACHES
    ids, by = company_rows(root)
    found = collections.OrderedDict()
    for d in ids:
        zb = GEN.read_zip(by[d], caches)                     # sha256 が 97 の記録と違えば止まる
        found[d] = (security_code(zb), sha256_bytes(zb))
    out = collections.OrderedDict()
    used = collections.Counter()
    for code in codes:
        hit = [d for d, (c, _s) in found.items() if c == code]
        if len(hit) != 1:
            raise Stop(u"**証券コード %s に結べる有報が %d 件(1 件でなければ止める)**" % (code, len(hit)))
        used[hit[0]] += 1
        out[code] = (hit[0], found[hit[0]][1])
    if any(v > 1 for v in used.values()):
        raise Stop(u"**同じ有報に 2 つ以上の証券コードが結んだ。止める**")
    return out


def check_zip_bytes(zb, expect_sha):
    if sha256_bytes(zb) != expect_sha:
        raise Stop(u"**ZIP の sha256 が封 §1 の表と違う。止める(何も書かない)**")


def run_fetch(root=ROOT, only=None, out=None, cache_dir=None, fetcher=None, sleep=None, say=print, now=None, caches=None):
    u"""取得して記録を作る(書き込みは全部の検証の後)。記録(OrderedDict)を返す。"""
    fetcher = fetcher or default_fetcher
    sleep = sleep or time.sleep
    now = now or _utcnow
    if only is not None and out is None:
        raise Stop(u"**--only を付けた走らせ方は本番の記録・folder を作らない。--out を指定する。止める**")
    if out is None:
        out = os.path.join(root, OUT_REL)
        cache_dir = cache_dir or default_cache_dir()
    else:
        out = os.path.abspath(out)
        cache_dir = os.path.abspath(cache_dir or os.path.join(os.path.dirname(out), "cache"))
    if only is not None and os.path.abspath(cache_dir) == os.path.abspath(default_cache_dir()):
        raise Stop(u"**--only は本番の置き場に書かない。止める**")
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    rows = select_rows(only)
    caches = caches or read_caches()
    before = GEN.caches_snapshot(caches)
    mapping = map_docids(root, [r[1] for r in rows])
    got = collections.OrderedDict()                        # 証券コード -> (取得の語, HTTP の状態, bytes)
    for (_n, code, number, sha, _chars, _claims) in rows:
        p = zip_path(cache_dir, code, number)
        if os.path.exists(p):
            with io.open(p, "rb") as fh:
                zb = fh.read()
            check_zip_bytes(zb, sha)
            got[code] = (u"cache に在った(取り直さず sha256 だけ照らした)", None, zb)
            continue
        status, zb = fetcher(URL_FMT % (code, number))
        sleep(INTERVAL_SEC)                                   # 1 本取るごとに 1 秒待つ
        if status != 200:
            raise Stop(u"**HTTP の状態が 200 でない(%s)。止める(何も書かない)**" % status)
        if not zb.startswith(ZIP_MAGIC):
            raise Stop(u"**応答が ZIP でない。止める(何も書かない)**")
        check_zip_bytes(zb, sha)
        got[code] = (u"取得", status, zb)
    # ここまで全部の sha256 が表と一致。記録を組み、鍵らしい字の検査を通してから書く(ZIP も記録もその後)
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**既存の cache の件数か名前が変わった。何も書かずに止める**")
    production = os.path.abspath(cache_dir) == os.path.abspath(default_cache_dir())
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"TS(人が書いた有報の外の文で engine を測る)― 決算短信の ZIP 17 本の取得(0 USD。外部への呼び出しは TDnet の ZIP の取得だけ)"
    rec[u"HEAD の commit"] = GEN.git_head(os.path.dirname(root))
    rec[u"この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    rec[u"取得日時(UTC)"] = now()
    rec[u"範囲"] = u"封 §1 の 17 本" if only is None else u"**--only(本番の記録ではない)**"
    rec[u"置き場"] = display_path(cache_dir) if production else u"使い捨ての置き場(本番の folder ではない)"
    rec[u"cache の前後"] = collections.OrderedDict([(u"前", before), (u"後", after), (u"変化なし", before == after)])
    rec[u"表と一致した ZIP"] = len(rows)
    rec[u"行"] = []
    for (n, code, number, sha, _chars, _claims) in rows:
        how, status, zb = got[code]
        docid, yuho_sha = mapping[code]
        rec[u"行"].append(collections.OrderedDict([
            (u"#", n), (u"証券コード", code), (u"番号", number), (u"ZIP の sha256", sha256_bytes(zb)), (u"取得", how), (u"HTTP の状態", status),
            (u"byte 数", len(zb)), (u"docID", docid), (u"有報の ZIP の sha256", yuho_sha)]))
    rec[u"key_leaks"] = []
    text = json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    leaks = GEN.key_leaks(text.replace(SEAL_REL, u""))               # 封の path は 32 字以上の _ - 英数字の連なり(前の便と同じく除いて検査する)
    if leaks:
        raise Stop(u"**鍵らしい字が記録に在る(%s)。書かずに止める**" % u" / ".join(sorted(set(leaks))))
    for (_n, code, number, _sha, _c, _cl) in rows:
        how, _st, zb = got[code]
        p = zip_path(cache_dir, code, number)
        if how == u"取得":
            os.makedirs(os.path.dirname(p), exist_ok=True)
            tmp = p + ".tmp"
            with io.open(tmp, "wb") as fh:
                fh.write(zb)
            os.replace(tmp, p)
    if GEN.caches_snapshot(caches) != before:
        raise Stop(u"**ZIP を書いたあとに既存の cache の件数か名前が変わった。記録を書かずに止める**")
    GEN.write_text(out, text)
    say(u"-> 記録 %s(%d 本)" % (os.path.basename(out), len(rows)))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--only", default=None, help="この証券コードの 1 本だけ(使い捨て。--out が要る)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--cache", default=None, help="ZIP の置き場(既定: 本番の folder。--out があれば <--out の folder>/cache)")
    a = ap.parse_args(argv)
    run_fetch(root=a.root, only=a.only, out=a.out, cache_dir=a.cache)


if __name__ == "__main__":
    main()
