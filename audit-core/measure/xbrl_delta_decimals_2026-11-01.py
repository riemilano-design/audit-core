# -*- coding: utf-8 -*-
u"""診断: 候補の要素の「当期末 − 前期末」と文の数の照合で、帯を fact の ``decimals`` の粒度にした版 ― 前の便の記録だけで測る(2026-11-01)。

封 ``docs/XBRL_DELTA_DECIMALS_SEAL_2026-11-01.md``(commit ``777003b``)§1・§2 のとおり。
**engine(``core/``・``adapters/``)は import しない。ZIP・instance・cache は開かない。読むのは
``fixtures/xbrl/delta_naming_2026-10-30.json`` 1 本だけ(sha256 を封の値と照合し、違えば書かずに止める)。**
席(LLM)は立てない。0 円・通信なし。標準 library だけ。

    cd audit-core
    python3 measure/xbrl_delta_decimals_2026-11-01.py                 # 既に出力が在れば測り直さない(止める)
    python3 measure/xbrl_delta_decimals_2026-11-01.py --out <scratch>  # 試走

**帯の中に入っても出所と判定しない。** 記録と文書は「丸めの帯の中に入った」とだけ書く(封 §4 の 1)。
帯の式(§2-1)・段(§2-2)は 296 行の数を見てから変えない。変えるなら別の封(人間の条件 (7))。
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SEAL_REL = "docs/XBRL_DELTA_DECIMALS_SEAL_2026-11-01.md"
SEAL_COMMIT = "777003b"
INPUT_REL = "fixtures/xbrl/delta_naming_2026-10-30.json"
INPUT_SHA256 = "27aca660570ddb37e8d9d1bc4826d8d2cfef931e0120c2484d688a4fe449b78f"
OUT_REL = "fixtures/xbrl/delta_decimals_2026-11-01.json"

NROWS = 296
N_UNCOMPARABLE = 16
N_PREV_IN_BAND = 39            # 前の便の 完全一致 0 + 許容差内 38 + 符号不一致 1
PREV_IN_BAND = (u"完全一致", u"許容差内", u"符号不一致")
STAGES = (u"完全一致", u"丸めの帯 H", u"丸めの帯 F", u"不一致", u"比較不能")
IN_BAND = (u"完全一致", u"丸めの帯 H", u"丸めの帯 F")
EXPLORE, VERIFY = u"探索", u"検証"
GROUPS = (u"全体", EXPLORE, VERIFY)
K_LOW, K_HIGH = u"-3 以下", u"3 以上"
COPIED = (u"位置", u"doc", u"id", u"期", u"member", u"単位", u"型", u"向き", u"差の符号", u"探索/検証", u"10 行",
          u"decimals が文の単位より粗い", u"比較不能の理由")
FORBIDDEN_RECORD_KEYS = (u"span", u"文", u"段落", u"窓", u"ラベル", u"理由の自由文", u"pointers", u"named")
KEY_PATTERNS = (r"sk-[A-Za-z0-9_\-]{10,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{20,}", r"xox[baprs]-[A-Za-z0-9\-]{10,}",
                r"-----BEGIN", r"Bearer [A-Za-z0-9._\-]{16,}", r"AIza[0-9A-Za-z_\-]{30,}")


class Stop(SystemExit):
    pass


# ---------------------------------------------------------------- 封 §2-1・§2-2・§2-3(純関数。門が別実装と照らす)

def g_of(dec):
    u"""丸めの幅 g(dec) = 10 の (−dec) 乗 円。dec が無ければ None。"""
    if dec is None:
        return None
    return float(10) ** (-int(dec))


def band_of(g_c, g_p, u):
    u"""(G, H) = (g_c + g_p + u, G / 2)。"""
    G = g_c + g_p + u
    return G, G / 2.0


def stage_of(prev_stage, d, t, G, H):
    u"""封 §2-2。比較不能は前の便の段を写す。それ以外は e = | |d| − t | と帯で 1 つ。"""
    if prev_stage == u"比較不能":
        return u"比較不能", None
    e = abs(abs(d) - t)
    if e == 0:
        return u"完全一致", e
    if e <= H:
        return u"丸めの帯 H", e
    if e <= G:
        return u"丸めの帯 F", e
    return u"不一致", e


def k_of(d, t, g_max):
    u"""k = (|d| − t) / g_max(符号つき。小数 6 桁で丸める)。"""
    return round((abs(d) - t) / g_max, 6)


def k_bucket(k):
    if k <= -3:
        return K_LOW
    if k >= 3:
        return K_HIGH
    return (u"%g" % k) if k != 0 else u"0"


def sign_check(direction, d, in_band):
    u"""封 §2-3。向きが 増/減 で帯の中の行だけ 期待どおり/不一致。d == 0 は問わない。"""
    if not in_band or direction not in (u"増", u"減") or d == 0:
        return None
    ok = (d > 0) if direction == u"増" else (d < 0)
    return u"期待どおり" if ok else u"符号不一致"


# ---------------------------------------------------------------- 入力・配線

def sha256_file(path):
    with io.open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def git_out(*a):
    r = subprocess.run(["git"] + list(a), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout.decode("utf-8", "replace").strip()


def load_input():
    path = os.path.join(ROOT, INPUT_REL)
    got = sha256_file(path)
    if got != INPUT_SHA256:
        raise Stop(u"**(a) 入力の sha256 が封の値と違う(%s…)。書かずに止める**" % got[:16])
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh), got


def build_rows(src_rows):
    out = []
    for r in src_rows:
        d, t, u = r[u"差"], r[u"文の値"], r[u"帯の幅"]
        g_c, g_p = g_of(r[u"当期の decimals"]), g_of(r[u"前期の decimals"])
        prev = r[u"段"]
        row = collections.OrderedDict()
        for k in COPIED:
            row[k] = r[k]
        row[u"文の値"] = t
        row[u"差"] = d
        row[u"帯の幅"] = u
        row[u"当期の decimals"] = r[u"当期の decimals"]
        row[u"前期の decimals"] = r[u"前期の decimals"]
        row[u"前の段"] = prev
        if prev == u"比較不能" or d is None or t is None or g_c is None or g_p is None:
            row.update({u"g_c": g_c, u"g_p": g_p, u"G": None, u"H": None, u"e": None, u"k": None,
                        u"段": u"比較不能", u"符号の照合": None})
            out.append(row)
            continue
        G, H = band_of(g_c, g_p, u)
        stage, e = stage_of(prev, d, t, G, H)
        g_max = max(g_c, g_p)
        row.update({u"g_c": g_c, u"g_p": g_p, u"G": G, u"H": H, u"e": e, u"k": k_of(d, t, g_max), u"段": stage,
                    u"符号の照合": sign_check(r[u"向き"], d, stage in IN_BAND)})
        out.append(row)
    return out


def wiring(rows, src_rows, sha):
    g = collections.OrderedDict()
    g[u"(a) 入力の sha256 が封の値と一致"] = (sha == INPUT_SHA256)
    pos = sorted(r[u"位置"] for r in rows)
    g[u"(b) 行 296・位置 0〜295 が 1 回ずつ・比較不能 16"] = [len(rows) == NROWS and pos == list(range(NROWS)),
                                                           sum(1 for r in rows if r[u"段"] == u"比較不能") == N_UNCOMPARABLE]
    prev_band = [r for r in rows if r[u"前の段"] in PREV_IN_BAND]
    g[u"(c) 前の便の帯の中 39 行が全部この便の帯の中"] = [sum(1 for r in prev_band if r[u"段"] in IN_BAND), len(prev_band)]
    same = sum(1 for r, s in zip(sorted(rows, key=lambda x: x[u"位置"]), sorted(src_rows, key=lambda x: x[u"位置"]))
               if (r[u"文の値"], r[u"差"], r[u"帯の幅"]) == (s[u"文の値"], s[u"差"], s[u"帯の幅"]))
    g[u"(d) 行ごとの t・d・u が前の記録と同じ"] = [same, len(rows)]
    rc, st = git_out("status", "--porcelain", "--", "adapters", "core", INPUT_REL)
    g[u"(e) adapters・core・入力の記録に未 commit の変更なし"] = (rc == 0 and st == u"")
    g[u"(e) 封の commit が HEAD の祖先"] = (git_out("merge-base", "--is-ancestor", SEAL_COMMIT, "HEAD")[0] == 0)
    g[u"通った"] = bool(g[u"(a) 入力の sha256 が封の値と一致"] and all(g[u"(b) 行 296・位置 0〜295 が 1 回ずつ・比較不能 16"])
                       and g[u"(c) 前の便の帯の中 39 行が全部この便の帯の中"][0] == len(prev_band) == N_PREV_IN_BAND
                       and same == len(rows) == NROWS
                       and g[u"(e) adapters・core・入力の記録に未 commit の変更なし"] and g[u"(e) 封の commit が HEAD の祖先"])
    return g


# ---------------------------------------------------------------- 集計(封 §2-4)

def _cnt(it):
    c = collections.Counter(it)
    return collections.OrderedDict((k, c[k]) for k in sorted(c, key=lambda x: (str(type(x)), x)))


def _full(keys, it):
    c = collections.Counter(it)
    return collections.OrderedDict((k, c.get(k, 0)) for k in keys)


def tally(rows):
    T = collections.OrderedDict()
    st = collections.OrderedDict()
    st[u"段"] = _full(STAGES, (r[u"段"] for r in rows))
    st[u"帯の中"] = sum(1 for r in rows if r[u"段"] in IN_BAND)
    st[u"前の段 × 新の段"] = _cnt(u"%s / %s" % (r[u"前の段"], r[u"段"]) for r in rows)
    st[u"単位 × 段"] = _cnt(u"%s / %s" % (r[u"単位"], r[u"段"]) for r in rows)
    st[u"decimals(当期, 前期)× 単位 × 段"] = _cnt(u"(%s, %s) / %s / %s" % (r[u"当期の decimals"], r[u"前期の decimals"], r[u"単位"], r[u"段"]) for r in rows)
    st[u"型 × 段"] = _cnt(u"%s / %s" % (r[u"型"], r[u"段"]) for r in rows)
    st[u"期 × 段"] = _cnt(u"%s / %s" % (r[u"期"], r[u"段"]) for r in rows)
    st[u"粗い × 段"] = _cnt(u"%s / %s" % (u"粗い" if r[u"decimals が文の単位より粗い"] else u"粗くない", r[u"段"]) for r in rows)
    st[u"member × 段"] = _cnt(u"%s / %s" % (r[u"member"], r[u"段"]) for r in rows)     # member は前の記録の字(「member あり」/「member なし」)を写す
    st[u"型 × 帯の中"] = _cnt(r[u"型"] for r in rows if r[u"段"] in IN_BAND)
    st[u"単位 × 帯の中"] = _cnt(r[u"単位"] for r in rows if r[u"段"] in IN_BAND)
    st[u"粗い × 帯の中"] = _cnt((u"粗い" if r[u"decimals が文の単位より粗い"] else u"粗くない") for r in rows if r[u"段"] in IN_BAND)
    st[u"粗い × 帯の中 × 段"] = _cnt(r[u"段"] for r in rows if r[u"段"] in IN_BAND and r[u"decimals が文の単位より粗い"])
    T["stages"] = st
    K = collections.OrderedDict()
    inb = [r for r in rows if r[u"段"] in IN_BAND]
    K[u"帯の中の k"] = _cnt(k_bucket(r[u"k"]) for r in inb)
    K[u"k がちょうど +1"] = sum(1 for r in inb if r[u"k"] == 1)
    K[u"k がちょうど -1"] = sum(1 for r in inb if r[u"k"] == -1)
    K[u"k が負"] = sum(1 for r in inb if r[u"k"] < 0)
    K[u"|k| が 2 以上"] = sum(1 for r in inb if abs(r[u"k"]) >= 2)
    K[u"前の段が不一致で帯の中に入った行の k"] = _cnt(k_bucket(r[u"k"]) for r in inb if r[u"前の段"] == u"不一致")
    K[u"前の段が不一致で帯の中に入った行"] = sum(1 for r in inb if r[u"前の段"] == u"不一致")
    T["k"] = K
    S = collections.OrderedDict()
    S[u"帯の中の符号の照合"] = _full((u"期待どおり", u"符号不一致"), (r[u"符号の照合"] for r in inb if r[u"符号の照合"]))
    S[u"帯の中の向き"] = _full((u"増", u"減", u"不明", u"なし"), (r[u"向き"] for r in inb))
    T["sign"] = S
    W = collections.OrderedDict()
    W[u"G の値 × 行数"] = _cnt(u"%g" % r[u"G"] for r in rows if r[u"G"] is not None)
    W[u"G の値 × 帯の中"] = _cnt(u"%g" % r[u"G"] for r in inb)
    T["width"] = W
    T["ten"] = [[r[u"位置"], r[u"前の段"], r[u"段"]] for r in sorted(rows, key=lambda x: x[u"位置"]) if r[u"10 行"]]
    return T


def record_key_leaks(obj):
    text = json.dumps(obj, ensure_ascii=False)
    return sorted(set(p for p in KEY_PATTERNS if re.search(p, text)))


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


def dumps(rec):
    parts = []
    for k, v in rec.items():
        if k == u"行":
            body = u"[\n" + u",\n".join(u"  " + json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in v) + u"\n ]"
        else:
            body = json.dumps(v, ensure_ascii=False, indent=1).replace(u"\n", u"\n ")
        parts.append(u" %s: %s" % (json.dumps(k, ensure_ascii=False), body))
    return u"{\n" + u",\n".join(parts) + u"\n}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % a.out)
    src, sha = load_input()
    rows = build_rows(src[u"行"])
    g = wiring(rows, src[u"行"], sha)
    if not g[u"通った"]:
        raise Stop(u"**配線の門が通らない: %s。記録を書かずに止める**" % json.dumps(g, ensure_ascii=False))
    groups = collections.OrderedDict()
    groups[u"全体"] = rows
    groups[EXPLORE] = [r for r in rows if r[u"探索/検証"] == EXPLORE]
    groups[VERIFY] = [r for r in rows if r[u"探索/検証"] == VERIFY]
    rec = collections.OrderedDict()
    rec[u"注意"] = u"帯の中に入っても出所と判定しない(封 §4 の 1)。帯は前の便の 1.5〜3 倍の幅で、入る行が増えたこと自体は仮説の根拠にならない。"
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT}
    rec[u"HEAD の commit"] = git_out("rev-parse", "HEAD")[1]
    with io.open(os.path.abspath(__file__), "rb") as fh:
        rec[u"この script の sha256"] = hashlib.sha256(fh.read()).hexdigest()
    rec[u"読んだ入力の sha256"] = {INPUT_REL: sha}
    rec[u"定数"] = collections.OrderedDict([
        (u"g(dec)", u"10 の (−dec) 乗 円"), (u"G", u"g_c + g_p + u(切り捨ての帯)"), (u"H", u"G / 2(四捨五入の帯)"),
        (u"e", u"| |d| − t |"), (u"k", u"(|d| − t) / max(g_c, g_p)"),
        (u"段", list(STAGES)), (u"帯の中", list(IN_BAND)), (u"前の便の帯の中", list(PREV_IN_BAND)),
        (u"行", NROWS), (u"比較不能", N_UNCOMPARABLE), (u"前の便の帯の中の行", N_PREV_IN_BAND)])
    rec[u"配線の門"] = g
    rec[u"行"] = rows
    rec[u"集計"] = collections.OrderedDict((k, tally(v)) for k, v in groups.items())
    rec[u"limits"] = [
        u"帯の中は出所の判定ではない。対照(偶然の一致)は instance が要るのでこの便では作れない(封 §4 の 2)。",
        u"比較不能・型・向き・期・member は前の便の判定を写した。文は読んでいない(前の記録に無い)。",
        u"F は 3 つの丸めが同じ向きに最大で出たときの上限で、書類の丸め方(四捨五入か切り捨てか)は読んでいない。",
    ]
    bad = forbidden_keys(rec)
    if bad:
        raise Stop(u"**記録に repo へ入れない欄がある: %s。止める**" % u",".join(bad))
    rec[u"key_leaks"] = record_key_leaks(rec)
    if rec[u"key_leaks"]:
        raise Stop(u"**鍵らしい字が記録に在る。書かずに止める**")
    text = dumps(rec)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    with io.open(a.out, encoding="utf-8") as fh:
        back = json.load(fh)
    if record_key_leaks(back) or forbidden_keys(back):
        os.remove(a.out)
        raise Stop(u"**書いた記録に鍵らしい字か禁じた欄が在る。消して止める**")
    T = rec[u"集計"][u"全体"]
    print(u"行 %d / 段 %s / 帯の中 %d / 前の段 不一致 → 帯の中 %d / 書いた: %s" % (
        len(rows), json.dumps(T["stages"][u"段"], ensure_ascii=False), T["stages"][u"帯の中"], T["k"][u"前の段が不一致で帯の中に入った行"], a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
