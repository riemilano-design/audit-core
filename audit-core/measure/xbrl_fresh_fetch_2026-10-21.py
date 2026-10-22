# -*- coding: utf-8 -*-
"""封 docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md §1-3・§1-4 ― **新しい標本 40 件を取得し、claim が 1 以上の先頭 30 件を「使う」と決める。費用 0 USD(EDINET は無料)。**

**鍵は環境変数 `EDINET_API_KEY` からだけ取る。値は読まない(中身を見ない)・印字しない・記録しない・例外の文に出さない。**
URL は印字しない(鍵が付く)。生 ZIP は **既存の cache `~/.cache/audit-core/edinet/` には 1 file も書かず**、`~/.cache/audit-core/edinet-fresh-2026-10-21/`
(`--fetch-dir` で変えられる)にだけ置く(repo に入れない)。理由: 既存の門のうち 4 本は共有の cache の folder を入力として数える
(281 件・全 zip と記録の一致)ので、そこに 40 件を足すと赤くなる。置き場所を分ければ既存の門は 1 本も触らずに済む。

やること
  1. 引いた 40 件を `fixtures/xbrl/fresh/draw_2026-10-21.json` から読む(**引き直さない**)
  2. **取得前に 40 件とも cache に無いことを確かめる**(既存の cache に 1 件でも在れば何も取得せず止める ― 封では cache に在るものは引きの時点で飛ばしてある。
     新しい folder に在るものは、`.partial` に成功と記録され sha256 が一致するときだけ前回の続きとして使い、それ以外は止める)
  3. 引いた順に取得し、**応答が ZIP であることを確かめる**(ZIP でなければ cache を消し、その書類は失敗として記録する。
     応答の本文は記録しない。長さと先頭 2 bytes だけ)。バイト数と sha256 を記録する
  4. `verify_document` の**既定の抽出**で claim の数を数え、claim が 1 以上の書類を**引いた順に先頭 30 件**「使う」。
     30 に届かなければ届いた数で測る(**引き直さない**)
  5. **記録に鍵らしい字が無いことを確かめてから書く**(書いた後にもう一度 file を読んで確かめる)

    EDINET_API_KEY="$(security find-generic-password -s EDINET_API_KEY -w)" python3 measure/xbrl_fresh_fetch_2026-10-21.py

通信は `fetch_one` の中の `adapters.xbrl.edinet.fetch` だけ(試験は fetcher を差し替える)。
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)

SEAL = "docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md"
DRAW_REL = os.path.join("fixtures", "xbrl", "fresh", "draw_2026-10-21.json")
OUT_REL = os.path.join("fixtures", "xbrl", "fresh", "fetched_2026-10-21.json")
DRAW_KEY = "引いた 40 件"
KEY_NAME = "EDINET_API_KEY"
WANT_DRAWN = 40
WANT_USED = 30          # 封 §1-3
ZIP_MAGIC = b"PK\x03\x04"

INTERVAL_SEC = 3.0      # 書類と書類の間(前例には待ちが無い。40 件なので下書きで足した値)
MAX_ATTEMPTS = 3        # 1 書類あたり(最初の 1 回を含む)
BACKOFF_SEC = (10.0, 30.0)   # 1 回目の失敗の後・2 回目の失敗の後
STOP_AFTER_CONSECUTIVE_NON_ZIP = 3   # 鍵の誤りなら全件が非 ZIP になる(2026-10-20 の前例)。続けて 3 件で止める

# 鍵らしい字: 32 字以上の英数字の連なり。**sha256 の 64 桁 16 進だけは通す**(32 桁の 16 進は鍵の形でもあるので通さない)。
KEYISH = re.compile(r"[A-Za-z0-9]{32,}")
SHA256_HEX = re.compile(r"[0-9a-f]{64}")


class Stop(SystemExit):
    """止める(記録は書かない)。"""


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def key_leaks(text, key_value=None):
    """記録の文字列に鍵らしい字が在れば、その種類の一覧(値は返さない)。"""
    leaks = []
    for s in KEYISH.findall(text):
        if not SHA256_HEX.fullmatch(s):
            leaks.append("32 字以上の英数字の連なり(長さ %d)" % len(s))
    if "Subscription-Key" in text or "subscription-key" in text:
        leaks.append("Subscription-Key")
    if re.search(KEY_NAME + r"\s*=\s*['\"]?\w{8,}", text):
        leaks.append("%s=値" % KEY_NAME)
    if key_value and key_value in text:
        leaks.append("環境の鍵の値そのもの")
    return leaks


def load_draw(path):
    with io.open(path, encoding="utf-8") as fh:
        docs = json.load(fh)[DRAW_KEY]
    if len(docs) != WANT_DRAWN:
        raise Stop("**引いた件数が %d でない(%d)。止める**" % (WANT_DRAWN, len(docs)))
    if len(set(docs)) != len(docs) or not all(re.fullmatch(r"S[0-9A-Z]{7}", d) for d in docs):
        raise Stop("**draw の docID の形が不正か重複。止める**")
    return docs


FRESH_DIR_NAME = "edinet-fresh-2026-10-21"


def default_fetch_dir():
    """新しい folder の既定(`~/.cache/audit-core/edinet-fresh-2026-10-21/`)。呼ぶ時に HOME を見る。"""
    return os.path.join(os.path.expanduser("~"), ".cache", "audit-core", FRESH_DIR_NAME)


def display_path(path):
    """記録に書く path(HOME 配下なら ~ に畳む)。"""
    home = os.path.expanduser("~")
    if path == home or path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path


def default_fetcher(doc_id, fetch_dir):
    """通信する唯一の所。**新しい folder に書く**(書いた path を返す)。例外の文は呼び出し側が捨てる。
    `adapters.xbrl.edinet.fetch` は書き先を module の `CACHE_DIR` から取るので、呼んでいる間だけ新しい folder に向ける
    (engine は変えない。終われば必ず元に戻す)。"""
    from adapters.xbrl import edinet as ED
    saved = ED.CACHE_DIR
    ED.CACHE_DIR = fetch_dir
    try:
        return ED.fetch(doc_id)
    finally:
        ED.CACHE_DIR = saved


def default_counter(zip_bytes):
    """`verify_document` の既定の抽出で (claim の数, 使った profile)。通信しない。
    渡す zip_bytes は run が**新しい folder の file から読んだもの**(既存の cache は読まない)。"""
    from adapters.xbrl.verify_document import verify_document
    out = verify_document(zip_bytes)
    return out["document"]["claims"], out["profile"]


def _error_note(exc):
    """**例外の文(str)は記録しない**(URL に鍵が付きうる)。型と HTTP の符号だけ。"""
    note = type(exc).__name__
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        note += " %d" % code
    return note


def _retryable(exc):
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        return code == 429 or code >= 500
    return True      # 通信の失敗・時間切れ


def fetch_one(doc_id, cache_path, fetcher, sleep, max_attempts, backoff):
    """1 書類。(行の一部, blob or None)。ZIP でなければ cache を消す。"""
    attempts = 0
    note = None
    while attempts < max_attempts:
        attempts += 1
        try:
            fetcher(doc_id)
        except Exception as exc:    # noqa: BLE001  文は捨てる
            note = _error_note(exc)
            if os.path.exists(cache_path):     # 途中までの file は残さない
                os.remove(cache_path)
            if attempts < max_attempts and _retryable(exc):
                sleep(backoff[min(attempts - 1, len(backoff) - 1)])
                continue
            return {"取得": "失敗", "失敗の型": note, "試行回数": attempts}, None
        if not os.path.exists(cache_path):
            return {"取得": "失敗", "失敗の型": "cache に書かれていない", "試行回数": attempts}, None
        with io.open(cache_path, "rb") as fh:
            blob = fh.read()
        if not blob.startswith(ZIP_MAGIC):
            # 応答が ZIP でない(2026-10-20 の前例: 鍵の誤りで 401 の JSON が ZIP として保存された)。
            # cache を消し、本文は記録しない。長さと先頭 2 bytes だけ。再試行しない(4xx の応答の本文であって通信の失敗ではない)
            os.remove(cache_path)
            return {"取得": "失敗", "失敗の型": "応答が ZIP でない",
                    "応答の長さ": len(blob), "応答の先頭 2 bytes": blob[:2].hex(),
                    "試行回数": attempts}, None
        return {"取得": "成功", "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                "試行回数": attempts}, blob
    return {"取得": "失敗", "失敗の型": note, "試行回数": attempts}, None


def run(root=DEFAULT_ROOT, draw=None, out=None, env=None, fetcher=None, counter=None,
        sleep=time.sleep, interval=INTERVAL_SEC, max_attempts=MAX_ATTEMPTS,
        backoff=BACKOFF_SEC, fetch_dir=None, fresh_path_of=None, existing_path_of=None, say=print):
    env = os.environ if env is None else env
    counter = counter or default_counter
    if root not in sys.path:
        sys.path.insert(0, root)
    fetch_dir = os.path.abspath(fetch_dir) if fetch_dir else default_fetch_dir()
    if fetcher is None:
        fetcher = lambda d: default_fetcher(d, fetch_dir)       # noqa: E731
    if fresh_path_of is None:
        fresh_path_of = lambda d: os.path.join(fetch_dir, "%s.zip" % d)       # noqa: E731
    if existing_path_of is None:
        from adapters.xbrl import edinet as ED
        existing_path_of = ED.cache_path       # 既存の cache(読むだけ・書かない)
    draw = draw or os.path.join(root, DRAW_REL)
    out = out or os.path.join(root, OUT_REL)
    partial = out + ".partial"

    if os.path.exists(out):
        raise Stop("既に在る: %s(取り直さない)" % out)
    key_value = env.get(KEY_NAME)
    if not key_value:
        raise Stop("**%s が無い。取得の前に止まる**" % KEY_NAME)
    docs = load_draw(draw)

    # 途中で止まった前回の続き: partial に成功と記録され、cache の sha256 が一致する書類だけ取り直さない
    prior = {}
    if os.path.exists(partial):
        with io.open(partial, encoding="utf-8") as fh:
            for r in json.load(fh).get("取得した書類", []):
                prior[r["docID"]] = r
    # 既存の cache に 1 件でも在れば何も取得せず止める(未使用でなくなる)
    in_existing = [d for d in docs if os.path.exists(existing_path_of(d))]
    if in_existing:
        raise Stop("**取得前に既存の cache に在る: %s。未使用でなくなるので何も取得せず止める**" % ", ".join(in_existing))
    reuse = {}
    for d in docs:
        p = fresh_path_of(d)
        if not os.path.exists(p):
            continue
        r = prior.get(d)
        if r and r.get("取得") == "成功":
            with io.open(p, "rb") as fh:
                blob = fh.read()
            if hashlib.sha256(blob).hexdigest() == r["sha256"]:
                reuse[d] = (r, blob)
                continue
        raise Stop("**取得前に新しい folder に在る(前回の続きでもない): %s。何も取得せず止める**" % d)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    rows, blobs, consecutive_non_zip = [], {}, 0
    for i, d in enumerate(docs):
        if d in reuse:
            part, blob = reuse[d]
            part = dict(part)
            part["前回の続き"] = True
        else:
            if i and interval:
                sleep(interval)
            part, blob = fetch_one(d, fresh_path_of(d), fetcher, sleep, max_attempts, backoff)
        row = {"docID": d, "位置(引いた順)": i + 1}
        row.update(part)
        if blob is not None:
            row["置いた file"] = "%s/%s.zip" % (display_path(fetch_dir), d)
            blobs[d] = blob
        rows.append(row)
        say("  %2d %s %s%s" % (i + 1, d, row["取得"],
                              ("  %10d bytes  %s" % (row["bytes"], row["sha256"][:16])) if blob is not None
                              else "  (%s)" % row["失敗の型"]))
        # 進みを残す(中断しても cache の取りこぼしを次の走りで見分けられる)
        with io.open(partial, "w", encoding="utf-8") as fh:
            json.dump({"取得した書類": rows}, fh, ensure_ascii=False, indent=1)
        consecutive_non_zip = consecutive_non_zip + 1 if row.get("失敗の型") == "応答が ZIP でない" else 0
        if consecutive_non_zip >= STOP_AFTER_CONSECUTIVE_NON_ZIP:
            raise Stop("**応答が ZIP でない件が続けて %d 件。鍵の値を確かめる(%s は残る)**"
                       % (consecutive_non_zip, partial))

    # claim を数える(取得に成功した書類を引いた順に)
    profile = None
    for row in rows:
        d = row["docID"]
        if d not in blobs:
            row["claims"] = None
            row["使う"] = False
            continue
        try:
            n, profile = counter(blobs[d])
            row["claims"] = n
        except Exception as exc:    # noqa: BLE001
            row["claims"] = None
            row["抽出の失敗"] = _error_note(exc)
    used = 0
    for row in rows:
        ok = isinstance(row.get("claims"), int) and row["claims"] >= 1 and used < WANT_USED
        row["使う"] = bool(ok)
        if ok:
            used += 1
            row["使う順"] = used
    used_docs = [r["docID"] for r in rows if r["使う"]]

    rec = {
        "seal": SEAL,
        "step": "**新しい標本の封 §1-3・§1-4。取得と使う書類の決定。費用 0 USD(EDINET は無料)**",
        "鍵": {"環境変数の名前": KEY_NAME, "値": "**読まない・印字しない・記録しない**"},
        "引いた件数": len(docs),
        "取得に成功": sum(1 for r in rows if r["取得"] == "成功"),
        "取得に失敗": sum(1 for r in rows if r["取得"] != "成功"),
        "取得した書類": rows,
        "合計バイト": sum(r.get("bytes", 0) for r in rows),
        "claim を数えた抽出": {"関数": "adapters.xbrl.verify_document.verify_document(既定の profile)",
                          "profile": profile},
        "使う書類": used_docs,
        "使う件数": len(used_docs),
        "足りない件数": max(0, WANT_USED - len(used_docs)),
        "取得した時刻(UTC)": _utcnow(),
        "置いた場所": {"folder": display_path(fetch_dir),
                    "既存の cache": "**`~/.cache/audit-core/edinet/` には 1 file も書かない**(既存の門が共有の cache の folder を数えるため)。repo に生 ZIP は入れない"},
        "引き直さない": "封 §1-3。30 に届かなければ届いた数で測る",
        "limits": ["**取得して claim の数を数えただけである。**state も reason も読んでいない",
                   "**席は 1 回も呼んでいない**",
                   "ZIP でない応答の本文は記録していない(長さと先頭 2 bytes だけ)"],
    }
    blob = json.dumps(rec, ensure_ascii=False, indent=1)
    leaks = key_leaks(blob, key_value)
    if leaks:
        raise Stop("**鍵らしい字が記録に在る(%s)。書かずに止める**" % ", ".join(leaks))
    with io.open(out, "w", encoding="utf-8") as fh:
        fh.write(blob)
    # 書いた後にもう一度、file を読んで確かめる(消す手は rc に直接つなぐ)
    with io.open(out, encoding="utf-8") as fh:
        after = fh.read()
    leaks = key_leaks(after, key_value)
    if leaks:
        os.remove(out)
        raise Stop("**書いた file に鍵らしい字(%s)。file を消して止める**" % ", ".join(leaks))
    if os.path.exists(partial):
        os.remove(partial)
    say("=== 新しい標本: 取得 %d / %d 件・使う %d 件(足りない %d)・合計 %d bytes ==="
        % (rec["取得に成功"], len(docs), rec["使う件数"], rec["足りない件数"], rec["合計バイト"]))
    say("-> " + out)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=DEFAULT_ROOT, help="audit-core の folder(既定: この script の親)")
    ap.add_argument("--draw", default=None)
    ap.add_argument("--out", default=None, help="記録の出力先(既定: fixtures/xbrl/fresh/fetched_2026-10-21.json)")
    ap.add_argument("--fetch-dir", default=None, help="取得した ZIP の置き場所(既定: ~/.cache/audit-core/%s/)" % FRESH_DIR_NAME)
    ap.add_argument("--interval", type=float, default=INTERVAL_SEC)
    ap.add_argument("--max-attempts", type=int, default=MAX_ATTEMPTS)
    a = ap.parse_args(argv)
    run(root=os.path.abspath(a.root), draw=a.draw, out=a.out, fetch_dir=a.fetch_dir,
        interval=a.interval, max_attempts=a.max_attempts)


if __name__ == "__main__":
    main()
