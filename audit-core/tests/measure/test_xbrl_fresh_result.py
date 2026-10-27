# -*- coding: utf-8 -*-
u"""新しい標本 30 書類で P22・P23・P24・P25・P26 を並べ、既定を決めた結果の門 ― 封 docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md §2〜§4 を縛る。

記録: ``fixtures/xbrl/fresh/fresh_2026-10-21.json``(``measure/xbrl_fresh_2026-10-21.py --stage all --readings … --out …`` の出力)。
文書: ``docs/XBRL_FRESH_SAMPLE_RESULT_2026-10-21.md``。

この門がやること(どれも、壊した標本で赤くなることを ``MutationTest`` が毎回確かめる):
  1. 入力を縛る: 取得の記録 ``fetched_2026-10-21.json``・引きの記録 ``draw_2026-10-21.json`` の sha256(字で留めた値)、使う 30 書類の順と ZIP の sha256(取得の記録と一致)、
     claim の数が取得の記録(既定の抽出)と書類ごとに一致すること、30 書類が既存の cache に無いこと(cache が在る機械で)、既存の cache の件数が測定の前後で同じこと。
  2. **script の関数を使わず**、記録の行から数え直す: (A) 4 state の数(claim の表から)、動いた行と (B) 新 GROUNDED・(C) 「違う」が弱まった行(候補ごと)、
     (D) 注入の通した・違う・要確認(profile ごと・型ごと)、F-4 の新 GROUNDED。記録の集計と一致させる。
  3. **読みと行の 1 対 1**: (B)(C)のどの行にも読みの語と根拠が付くこと、同じ鍵(候補の間で同じ行)は同じ読みであること。**読みの中身の正しさは門で縛れない**(エージェントの読み。
     縛るのは行と読みの対応・数・判定の算術だけ)。
  4. **判定を記録の数から、封の字から読んだ基準で門が自分で求める**: K-1・K-2・K-3 を候補ごとに、P26 → P25 → P24 の順に全部満たす最初を既定とする(P26 が候補かは
     git の commit の時刻と取得の時刻から門が求める)。予測 F-1〜F-5 の当たり外れも封の字の幅から門が求め、記録の判定と文書の表と一致させる。
  5. 文書の表・数のある文を記録から作った字と完全一致させる。散文に算用数字が在れば ``residual_numbers`` が見つけて赤にする(コード片・識別子・日付・節の番号は除く)。散文は漢数字で書く。
  6. engine の sha(測った時点)を字で留め、いまの engine が同じか宣言された遷移であること(遷移の表の名前は ``ENGINE_TRANSITIONS``)。``core/`` が封の commit から 0 行、
     ``DEFAULT_PROFILE`` が P22 のままであること(この結果の commit では既定を変えない。判定は段 2 の封で別に諮る)。封が封の commit から 1 字も変わっていないこと。
  7. 取得した ZIP と ラベルが在る機械では、軽い走らせ直し(無改変を 2 書類)を script で走らせて記録の該当行と一致。全部の走らせ直し(注入を含む)は
     ``AUDIT_CORE_FRESH=1`` のときだけ。走らせ直しは HOME の下の新しい folder と既存の cache を**読むだけ**で、何も書かない。
縛っていないもの: 読みの中身の正しさ(上の 3.)、限界の文の主張の中身、tests/measure 全体の所要、漢数字で書いた数(``residual_numbers`` は算用数字だけを探す。散文の数は記録から作った字で縛る約束)。
"""
import copy
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
REC = os.path.join(ROOT, "fixtures", "xbrl", "fresh", "fresh_2026-10-21.json")
DOC = os.path.join(ROOT, "docs", "XBRL_FRESH_SAMPLE_RESULT_2026-10-21.md")
SEAL_REL = "docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SEAL_COMMIT = "14cdd21"
FETCHED = os.path.join(ROOT, "fixtures", "xbrl", "fresh", "fetched_2026-10-21.json")
DRAW = os.path.join(ROOT, "fixtures", "xbrl", "fresh", "draw_2026-10-21.json")
SCRIPT = os.path.join(ROOT, "measure", "xbrl_fresh_2026-10-21.py")
FRESH_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-fresh-2026-10-21")
EXISTING_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
RUN_HEAVY = os.environ.get("AUDIT_CORE_FRESH") == "1"
LIGHT_DOCS = ("S100YZFP", "S100YYUS")
P26_COMMIT = "b778dd9"
FETCH_SCRIPT_COMMIT = "13575ab"
PROFILES = ("P22", "P23", "P24", "P25", "P26")
CANDIDATES = ("P26", "P25", "P24")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
INJECT_TYPES = ("T1_VALUE", "T2_UNIT", "T5_COINCIDENT", "T3_ABSENT")
READ_TRUE, READ_FALSE, READ_SEMI = u"正", u"偽", u"準偽"
READ_OK, READ_WRONG, READ_UNSURE = u"正しい文", u"文が本当に違う", u"分からない"
WORDS_B = (READ_TRUE, READ_FALSE, READ_SEMI)
WORDS_C = (READ_OK, READ_WRONG, READ_UNSURE)

#: **字で留める**(取得・引きの記録そのものの sha256。測った入力)。
FETCHED_SHA256 = "ff507345903cd7762e5a95f76d0a311243ac202f9a65db8d75ca726661196c12"
DRAW_SHA256 = "b4f0dae675b30610ae1ce20273ed20b2adb25d4213964eea457dcac114154f32"
SEED_SHA256 = "f74146592f68b88dab89869a185d9f69bc68e8b4fa0c4eee1400581354b19f80"
#: 測った時点の engine(sha256 の先頭 16 桁)。
ENGINE_AT_MEASURE = {"adapters/xbrl/extract.py": "9982599fc31cbab3", "adapters/xbrl/vocabulary.py": "83025e9c0525d08b", "adapters/xbrl/recipes.py": "181b370420ab751b",
                     "adapters/xbrl/registry_setup.py": "7f2cbded9c830211", "adapters/xbrl/report_customer.py": "141767d189b63733",
                     "adapters/xbrl/comparators.py": "d8706338325e725b"}
#: 宣言された遷移: {path: (後の sha16, 遷移を宣言した封の path)}。この結果の commit 時点では空。
#: 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md が宣言した遷移。vocabulary.py は DEFAULT_PROFILE の 1 行と決定の注記(+4 行・-1 行)だけ動いた。
#: 83025e9c0525d08b(P26 の段 1。ENGINE_AT_MEASURE に残す = 測った時点の値)から段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
# 2026-10-27(P27 の段 2): 封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3 が宣言した遷移。engine の 5 file(vocabulary・recipes・extract・registry_setup・report_customer)に挿入だけを足した(既存の行の書き換え 0)。直前の値は残す(測った時点の値)、P27 の段 2 で下の値。受け入れるのは、その封が履歴に在り、値が P27 の段 2 の後の値のときだけ。
ENGINE_TRANSITIONS = {"adapters/xbrl/vocabulary.py": ("85896a67913ce1e7", SEAL_P27),
                      "adapters/xbrl/recipes.py": ("52d645e713c53c1c", SEAL_P27),
                      "adapters/xbrl/extract.py": ("3cf55966f12919f0", SEAL_P27),
                      "adapters/xbrl/registry_setup.py": ("d6f25750bcd73c0a", SEAL_P27),
                      "adapters/xbrl/report_customer.py": ("6679138d350ec382", SEAL_P27)}
FILES_NOT_TOUCHED = ("adapters/xbrl/report.py", "adapters/xbrl/verify_document.py", "adapters/xbrl/comparators.py")


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    return json.loads(jtext(p))


def sha_path(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha16(rel):
    return sha_path(os.path.join(ROOT, rel))[:16]


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i + 1) if end else len(t)
    return t[i:j]


def cell(s):
    return (s if s is not None else u"").replace(u"|", u"｜").replace(u"\n", u" ")


def comma(n):
    return format(n, ",")


def pct1(a, b):
    return u"%.1f%%" % (100.0 * a / b) if b else u"―"


def F(a, b):
    return u"%d / %d = %s" % (a, b, pct1(a, b))


_D = u"零一二三四五六七八九"


def kan(n):
    u"""整数(0〜九万九千九百九十九)を漢数字で。"""
    assert isinstance(n, int) and 0 <= n < 100000, n
    if n == 0:
        return u"零"
    out = u""
    for unit, base in ((10000, u"万"), (1000, u"千"), (100, u"百"), (10, u"十")):
        q, n = divmod(n, unit)
        if q:
            out += (u"" if (q == 1 and unit != 10000) else _D[q]) + base
    if n:
        out += _D[n]
    return out


# ----------------------------------------------------------------------------------------------------------------
# 封の字から基準・幅を読む(数を見てから変えないので、封の字がそのまま基準)
def seal_params(seal):
    k = sec(seal, "## §3", "## §4")
    f = sec(seal, "## §4", "## §5")
    p = {}
    p["k2"] = float(re.search(r"\*\*偽\*\*が新 GROUNDED の \*\*(\d+)% 以下\*\*", k).group(1))
    p["k3"] = float(re.search(r"\*\*文が本当に違う\*\*が \*\*(\d+)% 以下\*\*", k).group(1))
    p["b67"] = tuple(int(x.replace(",", "")) for x in re.search(r"(\d[\d,]*) / (\d[\d,]*) = 1\.9%", f).groups())
    for tag in ("F-1", "F-2", "F-4", "F-5"):
        row = re.search(r"(?m)^\| \*\*%s\*\* \|(.*)$" % tag, f).group(1)
        p[tag] = [(float(a), float(b)) for a, b in re.findall(r"\*\*([\d.]+)〜([\d.]+)(?:%| 倍)?\*\*", row)]
    p["F-4倍"] = p["F-4"]
    return p


def inr(x, rng):
    return rng[0] <= x <= rng[1]


# ----------------------------------------------------------------------------------------------------------------
# 独立の数え直し(script の関数を使わない)
def recount_A(rec):
    claims = rec[u"claims"]
    out = {u"claim": sum(len(v) for v in claims.values())}
    for i, p in enumerate(PROFILES):
        out[p] = dict((s, sum(1 for rows in claims.values() for r in rows if r[u"states"][i] == s)) for s in STATES)
    return out


def _st(x, p):
    return x[u"結果"][p][0] if x[u"結果"][p] else None


def view_state(r, p):
    v = r[u"views"][p]
    return v[u"state"] if v else None


def recount_BC(rec):
    mv = rec[u"動いた行"]
    B, C = {}, {}
    for c in CANDIDATES:
        B[c] = [(r[u"doc"], r[u"id"]) for r in mv if view_state(r, "P22") != "GROUNDED" and view_state(r, c) == "GROUNDED"]
        C[c] = [(r[u"doc"], r[u"id"]) for r in mv if view_state(r, "P22") == "VALUE_MISMATCH" and view_state(r, c) in ("POINTER_NOT_FOUND", "UNVERIFIABLE")]
    return B, C


def key_b(r, c):
    return u"%s:%s:%s" % (r[u"doc"], r[u"id"], u",".join(r[u"views"][c][u"pointers"]))


def key_c(r):
    return u"%s:%s" % (r[u"doc"], r[u"id"])


def outcome(res):
    if res is None:
        return u"対応が付かない"
    return {"GROUNDED": u"通した", "VALUE_MISMATCH": u"違う", "POINTER_NOT_FOUND": u"要確認", "UNVERIFIABLE": u"要確認"}[res[0]]


def recount_D(rec):
    rows = rec[u"注入の行"]
    n = len(rows)
    out = {u"注入": n, u"型別の注入": dict(sorted((t, sum(1 for x in rows if x[u"型"] == t)) for t in INJECT_TYPES if any(x[u"型"] == t for x in rows)))}
    for p in PROFILES:
        c = {}
        for x in rows:
            o = outcome(x[u"結果"][p])
            c[o] = c.get(o, 0) + 1
        out[p] = {u"通した": c.get(u"通した", 0), u"違う": c.get(u"違う", 0), u"要確認": c.get(u"要確認", 0), u"対応が付かない": c.get(u"対応が付かない", 0),
                  u"通した(T3 を除く)": sum(1 for x in rows if x[u"型"] != "T3_ABSENT" and outcome(x[u"結果"][p]) == u"通した"),
                  u"型別": dict((t, dict(sorted(_cnt(outcome(x[u"結果"][p]) for x in rows if x[u"型"] == t).items()))) for t in INJECT_TYPES)}
    return out


def _cnt(it):
    c = {}
    for x in it:
        c[x] = c.get(x, 0) + 1
    return c


def recount_F4(rec, params):
    i23, i25 = PROFILES.index("P23"), PROFILES.index("P25")
    k = sum(1 for rows in rec[u"claims"].values() for r in rows if r[u"states"][i23] != "GROUNDED" and r[u"states"][i25] == "GROUNDED")
    n = sum(len(v) for v in rec[u"claims"].values())
    a, b = params["b67"]
    return {u"k": k, u"n": n, u"倍率": round((k / float(n)) / (a / float(b)), 3)}


def read_summary(rec):
    out = {}
    for c in CANDIDATES:
        B, C = rec[u"B"][c], rec[u"C"][c]
        out[c] = {u"B": dict([(u"行", len(B))] + [(w, sum(1 for r in B if r[u"読み"] == w)) for w in WORDS_B]),
                  u"C": dict([(u"行", len(C))] + [(w, sum(1 for r in C if r[u"読み"] == w)) for w in WORDS_C])}
    return out


def judge(rec, params):
    u"""封 §3(K-1・K-2・K-3)と順序。**記録の行から**求める。"""
    D = recount_D(rec)
    res = {}
    for c in CANDIDATES:
        B, C = rec[u"B"][c], rec[u"C"][c]
        nB, fB = len(B), sum(1 for r in B if r[u"読み"] == READ_FALSE)
        nC = len(C)
        eff = sum(1 for r in C if r[u"読み"] == READ_WRONG) + 0.5 * sum(1 for r in C if r[u"読み"] == READ_UNSURE)
        k1 = D[c][u"通した"] <= D["P22"][u"通した"]
        k2 = nB == 0 or 100.0 * fB / nB <= params["k2"]
        k3 = nC == 0 or 100.0 * eff / nC <= params["k3"]
        res[c] = {u"K-1": k1, u"K-2": k2, u"K-3": k3, u"全部": k1 and k2 and k3, u"満たさない": [k for k, ok in (("K-1", k1), ("K-2", k2), ("K-3", k3)) if not ok]}
    order = list(CANDIDATES) if p26_is_candidate(rec) else ["P25", "P24"]
    chosen = "P22"
    for c in order:
        if res[c][u"全部"]:
            chosen = c
            break
    return {u"候補": res, u"順": order, u"既定": chosen}


def p26_is_candidate(rec):
    u"""P26 の段 1 の commit が、取得(ZIP を置いた最初の時刻と取得の記録の時刻)より前か。git と取得の記録から門が求める。"""
    import datetime
    t_commit = datetime.datetime.fromisoformat(git("log", "-1", "--format=%cI", P26_COMMIT).stdout.strip())
    fetched = jload(FETCHED)
    t_rec = datetime.datetime.strptime(fetched[u"取得した時刻(UTC)"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    t_first = datetime.datetime.strptime(rec[u"順序"][u"最初に置いた ZIP の mtime(UTC)"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    return bool(git("merge-base", "--is-ancestor", P26_COMMIT, "HEAD").returncode == 0 and t_commit < t_first and t_commit < t_rec)


def predictions(rec, params):
    A = recount_A(rec)
    n = A[u"claim"]
    D = recount_D(rec)
    j = judge(rec, params)
    vm = lambda p: 100.0 * A[p]["VALUE_MISMATCH"] / n
    pnf = lambda p: 100.0 * A[p]["POINTER_NOT_FOUND"] / n
    f4 = recount_F4(rec, params)[u"倍率"]
    f5 = 100.0 * D["P25"][u"通した"] / D[u"注入"]
    r1, r2 = params["F-1"][0], params["F-1"][1]
    return {"F-1": inr(vm("P22"), r1) and inr(vm("P25"), r2), "F-2": inr(pnf("P25"), params["F-2"][0]),
            "F-3": j[u"候補"]["P25"][u"全部"], "F-4": inr(f4, params["F-4"][0]), "F-5": f5 <= params["F-5"][0][1] and f5 >= params["F-5"][0][0]}


# ----------------------------------------------------------------------------------------------------------------
# 文書の字(記録から作る)。散文の数は漢数字
def table(head, rows):
    L = [u"| " + u" | ".join(head) + u" |", u"|" + u"|".join(u"---" for _ in head) + u"|"]
    for r in rows:
        L.append(u"| " + u" | ".join(r) + u" |")
    return u"\n".join(L)


def render_blocks(rec, params):
    A, D, j = recount_A(rec), recount_D(rec), judge(rec, params)
    n = A[u"claim"]
    B = {}
    B["state"] = table([u"profile", u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND"],
                       [[p if p != "P22" else u"P22(いまの既定)"] + [F(A[p][s], n) for s in STATES] for p in PROFILES])
    rs = read_summary(rec)
    rows = []
    for c in CANDIDATES:
        b, cc = rs[c][u"B"], rs[c][u"C"]
        rows.append([c, comma(b[u"行"]), comma(b[READ_TRUE]), comma(b[READ_FALSE]), comma(b[READ_SEMI]), comma(cc[u"行"]), comma(cc[READ_OK]), comma(cc[READ_WRONG]), comma(cc[READ_UNSURE])])
    B["read"] = table([u"候補", u"新 GROUNDED(B)", u"正", u"偽", u"準偽", u"「違う」が弱まった行(C)", u"正しい文", u"文が本当に違う", u"分からない"], rows)
    rows = []
    for c in CANDIDATES:
        r = j[u"候補"][c]
        C = rec[u"C"][c]
        Bc = rec[u"B"][c]
        eff = sum(1 for x in C if x[u"読み"] == READ_WRONG) + 0.5 * sum(1 for x in C if x[u"読み"] == READ_UNSURE)
        rows.append([c, u"%d 対 %d(%s)" % (D[c][u"通した"], D["P22"][u"通した"], u"満たす" if r[u"K-1"] else u"満たさない"),
                     u"%d / %d(%s)" % (sum(1 for x in Bc if x[u"読み"] == READ_FALSE), len(Bc), u"満たす" if r[u"K-2"] else u"満たさない"),
                     u"%s / %d(%s)" % (("%g" % eff), len(C), u"満たす" if r[u"K-3"] else u"満たさない"), u"はい" if r[u"全部"] else u"いいえ"])
    B["judge"] = table([u"候補", u"K-1 候補が通した 対 P22 が通した", u"K-2 偽 / 新 GROUNDED", u"K-3 違うに数えた / 弱まった行", u"全部満たす"], rows)
    B["judge_note"] = u"候補の順: %s。既定: **%s**。" % (u" → ".join(j[u"順"]), j[u"既定"])
    rows = []
    for p in PROFILES:
        st = D[p][u"違う"] + D[p][u"要確認"]
        rows.append([p, comma(D[p][u"通した"]), comma(D[p][u"違う"]), comma(D[p][u"要確認"]), comma(D[p][u"対応が付かない"]), pct1(D[p][u"通した"], D[u"注入"]),
                     pct1(D[p][u"違う"], st), pct1(D[p][u"要確認"], st), comma(D[p][u"通した(T3 を除く)"])])
    B["inject"] = table([u"profile", u"通した(GROUNDED)", u"違う", u"要確認", u"対応が付かない", u"通した率(分母 %d)" % D[u"注入"], u"止めのうち違う", u"止めのうち要確認", u"通した(T3 を除く)"], rows)
    rows = []
    for x in rec[u"注入の行"]:
        if any(outcome(x[u"結果"][p]) == u"通した" for p in PROFILES):
            rows.append([x[u"doc"], x[u"id"], x[u"型"], cell(x[u"元の字"]) + u" → " + cell(x[u"後の字"]), x[u"基準の claim"] or u"―"] +
                        [u"通した" if outcome(x[u"結果"][p]) == u"通した" else outcome(x[u"結果"][p]) for p in PROFILES])
    B["inject_pass"] = table([u"書類", u"注入", u"型", u"元の字 → 後の字", u"基準の claim"] + list(PROFILES), rows)
    rows = []
    for p in PROFILES:
        for t in INJECT_TYPES:
            ct = D[p][u"型別"][t]
            rows.append([p, t, comma(D[u"型別の注入"].get(t, 0)), comma(ct.get(u"通した", 0)), comma(ct.get(u"違う", 0)), comma(ct.get(u"要確認", 0)), comma(ct.get(u"対応が付かない", 0))])
    B["inject_type"] = table([u"profile", u"型", u"注入", u"通した", u"違う", u"要確認", u"対応が付かない"], rows)
    f4 = recount_F4(rec, params)
    lost = {}
    for c in CANDIDATES:
        l = _cnt(r[u"views"][c][u"state"] for r in rec[u"動いた行"] if view_state(r, "P22") == "GROUNDED" and r[u"views"][c] and view_state(r, c) != "GROUNDED")
        lost[c] = l
    B["lost"] = table([u"候補", u"P22 が GROUNDED で候補が GROUNDED でない行", u"うち VALUE_MISMATCH", u"うち UNVERIFIABLE", u"うち POINTER_NOT_FOUND"],
                      [[c, comma(sum(lost[c].values())), comma(lost[c].get("VALUE_MISMATCH", 0)), comma(lost[c].get("UNVERIFIABLE", 0)), comma(lost[c].get("POINTER_NOT_FOUND", 0))] for c in CANDIDATES])
    rows = []
    for r in rec[u"動いた行"]:
        if view_state(r, "P22") == "GROUNDED" and view_state(r, "P24") == "VALUE_MISMATCH":
            rows.append([r[u"doc"], r[u"id"], cell(u"%s%s" % (r[u"value"], r[u"unit"] or u"")), u"%s → %s" % (view_state(r, "P22"), u"・".join(c + u" " + view_state(r, c) for c in ("P23", "P24", "P25", "P26"))),
                         u"%s" % r[u"views"]["P24"][u"recomputed"]])
    B["lost_vm"] = table([u"書類", u"id", u"文の数", u"向き(P22 → 各 profile)", u"P24 が再計算した値"], rows)
    margin = []
    for c in CANDIDATES:
        margin.append([c, comma(len(rec[u"B"][c])), u"%.2f" % (params["k2"] * len(rec[u"B"][c]) / 100.0), comma(len(rec[u"C"][c])), u"%.2f" % (params["k3"] * len(rec[u"C"][c]) / 100.0)])
    B["margin"] = table([u"候補", u"新 GROUNDED(B)", u"偽に数えてよい上限(%g%%)" % params["k2"], u"弱まった行(C)", u"違うに数えてよい上限(%g%%。分からないは半分)" % params["k3"]], margin)
    B["f4"] = table([u"項目", u"件数"], [[u"P23 → P25 の新 GROUNDED(P23 が GROUNDED でなく P25 が GROUNDED)", comma(f4[u"k"])], [u"claim", comma(f4[u"n"])],
                                       [u"claim あたりの率", pct1(f4[u"k"], f4[u"n"])], [u"67 書類の率(%d / %s)" % (params["b67"][0], comma(params["b67"][1])), pct1(params["b67"][0], params["b67"][1])],
                                       [u"倍率(30 書類の率 ÷ 67 書類の率)", u"%.2f" % f4[u"倍率"]]])
    pr = predictions(rec, params)
    seal = jtext(SEAL)
    f = sec(seal, "## §4", "## §5")
    forms = dict((tag, cells_of(re.search(r"(?m)^\| \*\*%s\*\* \|.*$" % tag, f).group(0))) for tag in ("F-1", "F-2", "F-3", "F-4", "F-5"))
    vm = lambda p: pct1(A[p]["VALUE_MISMATCH"], n)
    meas = {"F-1": u"P22 の違う率 %s・P25 の違う率 %s(参考 P26 %s)" % (vm("P22"), vm("P25"), vm("P26")),
            "F-2": u"P25 の PNF 率 %s(参考 P26 %s)" % (pct1(A["P25"]["POINTER_NOT_FOUND"], n), pct1(A["P26"]["POINTER_NOT_FOUND"], n)),
            "F-3": u"P25 の K-1・K-2・K-3: %s。既定は %s" % (u"全部満たす" if j[u"候補"]["P25"][u"全部"] else u"満たさない " + u"・".join(j[u"候補"]["P25"][u"満たさない"]), j[u"既定"]),
            "F-4": u"倍率 %.2f(%d / %d)" % (f4[u"倍率"], f4[u"k"], f4[u"n"]),
            "F-5": u"P25 が通した %s(参考 P26 %s)" % (pct1(D["P25"][u"通した"], D[u"注入"]), pct1(D["P26"][u"通した"], D[u"注入"]))}
    B["pred"] = table([u"#", u"封の予測", u"封の外れ方", u"実測", u"判定"],
                      [[u"**%s**" % t, cell(forms[t][1]), cell(forms[t][2]), meas[t], u"**当たり**" if pr[t] else u"**外れ**"] for t in ("F-1", "F-2", "F-3", "F-4", "F-5")])
    return B


def cells_of(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def prose_facts(rec, params):
    A, D, j = recount_A(rec), recount_D(rec), judge(rec, params)
    n = A[u"claim"]
    P = {}
    nd = len(rec[u"docs"])
    P["head"] = u"判定: 既定にするのは **%s**。候補の順は %s。" % (j[u"既定"], u"、".join(j[u"順"]))
    P["sample"] = u"測った書類の数は %s、claim の数は %s。" % (kan(nd), kan(n))
    rs = read_summary(rec)
    for c in CANDIDATES:
        b, cc = rs[c][u"B"], rs[c][u"C"]
        P["read_" + c] = u"%s: 新しい GROUNDED %s行、うち偽 %s・準偽 %s。「違う」が弱まった行 %s行、うち文が本当に違う %s・分からない %s。" % (
            c, kan(b[u"行"]), kan(b[READ_FALSE]), kan(b[READ_SEMI]), kan(cc[u"行"]), kan(cc[READ_WRONG]), kan(cc[READ_UNSURE]))
    P["inject_n"] = u"注入は %s回(P22 が GROUNDED の数の claim への T1_VALUE・T2_UNIT・T5_COINCIDENT と、挿入文 T3_ABSENT)。P22 が通した %s、P25 が通した %s、P26 が通した %s。" % (
        kan(D[u"注入"]), kan(D["P22"][u"通した"]), kan(D["P25"][u"通した"]), kan(D["P26"][u"通した"]))
    pr = predictions(rec, params)
    P["pred_n"] = u"予測 機械判定 当たり %s / 外れ %s(F-1〜F-5)。" % (kan(sum(1 for v in pr.values() if v)), kan(sum(1 for v in pr.values() if not v)))
    o = rec[u"順序"]
    P["order"] = u"P26 の段 1 の commit `%s` は取得より%s。候補の順は %s。" % (P26_COMMIT, u"前" if o[u"P26 は候補"] else u"後", u"、".join(j[u"順"]))
    t5 = D["P22"][u"型別"]["T5_COINCIDENT"]
    t5n = D["P26"][u"型別"]["T5_COINCIDENT"]
    P["t5"] = u"値が偶然別の fact と一致する注入(T5_COINCIDENT、%s回)では、P22 は %s回を「違う」で止め、P26 は %s回を「違う」・%s回を「要確認」で止めた(通した %s)。" % (
        kan(sum(t5.values())), kan(t5.get(u"違う", 0)), kan(t5n.get(u"違う", 0)), kan(t5n.get(u"要確認", 0)), kan(t5n.get(u"通した", 0)))
    sets = [frozenset((x[u"doc"], x[u"id"]) for x in rec[u"注入の行"] if outcome(x[u"結果"][p]) == u"通した") for p in PROFILES]
    P["same_pass"] = u"通した注入は五つの profile で%s一覧(%s回)。" % (u"同じ" if len(set(sets)) == 1 else u"違う", kan(len(sets[0])))
    lost = dict((c, sum(1 for r in rec[u"動いた行"] if view_state(r, "P22") == "GROUNDED" and r[u"views"][c] and view_state(r, c) != "GROUNDED")) for c in CANDIDATES)
    P["lost_n"] = u"P22 が GROUNDED で候補が GROUNDED でない行は、P26 が %s・P25 が %s・P24 が %s。" % (kan(lost["P26"]), kan(lost["P25"]), kan(lost["P24"]))
    P["moved"] = u"P22 と state か参照先が違う行(動いた行)は %s。" % kan(len(rec[u"動いた行"]))
    return P


#: 散文に残ってよい数字の並び(記録に縛られない構造上の字)。空にできるよう、散文は漢数字で書く。
ALLOWED_RESIDUAL = []


def residual_numbers(doc, rec, params):
    t = doc
    pieces = list(render_blocks(rec, params).values()) + list(prose_facts(rec, params).values())
    for v in sorted(pieces, key=len, reverse=True):
        t = t.replace(v, u"")
    t = re.sub(r"```.*?```", u"", t, flags=re.S)
    t = re.sub(r"`[^`]*`", u"", t)
    t = re.sub(r"[A-Za-z_][A-Za-z_0-9\-]*\d[A-Za-z_0-9\-]*", u"", t)      # S100YMFV・N076・K-1・P26・sha16 など
    t = re.sub(r"(?m)^#+ [\d\-]+\.?", u"", t)
    t = re.sub(r"段 \d", u"", t)
    t = t.replace(u"0 USD", u"")
    t = re.sub(r"§[\d\-]+", u"", t)
    t = re.sub(r"\d{4}-\d{2}-\d{2}", u"", t)
    return re.findall(r"\d[\d,\.]*", t)


# ----------------------------------------------------------------------------------------------------------------
def check_record(rec, params):
    u"""記録の集計を、行から数え直した値と突き合わせる。壊した記録で赤くなる。"""
    fetched = jload(FETCHED)
    assert rec[u"docs"] == fetched[u"使う書類"] and len(rec[u"docs"]) == fetched[u"使う件数"] == 30, u"使う書類"
    assert [d[u"doc"] for d in rec[u"書類別"]] == rec[u"docs"] and sorted(rec[u"claims"]) == sorted(rec[u"docs"])
    frow = dict((r["docID"], r) for r in fetched[u"取得した書類"])
    for d in rec[u"書類別"]:
        assert d[u"claims"] == len(rec[u"claims"][d[u"doc"]]) == frow[d[u"doc"]][u"claims"], (d[u"doc"], u"claim の数が取得の記録(既定の抽出)と違う")
        assert not d[u"id が合わない"], d[u"doc"]
        for i, p in enumerate(PROFILES):
            c = _cnt(r[u"states"][i] for r in rec[u"claims"][d[u"doc"]])
            assert d[u"states"][p] == c, (d[u"doc"], p)
    # (A)
    A = recount_A(rec)
    for p in PROFILES:
        for s in STATES:
            got = rec[u"A"][p][s]
            assert (got[u"件"], got[u"分母"]) == (A[p][s], A[u"claim"]), (p, s)
        assert sum(A[p].values()) == A[u"claim"], p
    assert rec[u"A"][u"claim"] == A[u"claim"] and rec[u"A"][u"書類"] == 30
    # 動いた行
    mv = rec[u"動いた行"]
    assert len({(r[u"doc"], r[u"id"]) for r in mv}) == len(mv), u"動いた行に重複"
    by = dict(((d, r[u"id"]), r) for d, rows in rec[u"claims"].items() for r in rows)
    for r in mv:
        c = by[(r[u"doc"], r[u"id"])]
        for i, p in enumerate(PROFILES):
            assert view_state(r, p) == c[u"states"][i], (r[u"doc"], r[u"id"], p)
    moved = {(r[u"doc"], r[u"id"]) for r in mv}
    for k, c in by.items():
        if len(set(c[u"states"])) > 1:
            assert k in moved, (k, u"state が profile で違う行が動いた行に無い")
    # (B)(C)
    Bk, Ck = recount_BC(rec)
    mvd = dict(((r[u"doc"], r[u"id"]), r) for r in mv)
    for c in CANDIDATES:
        assert [(r[u"doc"], r[u"id"]) for r in rec[u"B"][c]] == Bk[c], (u"B", c)
        assert [(r[u"doc"], r[u"id"]) for r in rec[u"C"][c]] == Ck[c], (u"C", c)
        for r in rec[u"B"][c]:
            m = mvd[(r[u"doc"], r[u"id"])]
            assert r[u"key"] == key_b(m, c) and r[u"P22"] == view_state(m, "P22") and r[c] == "GROUNDED", (c, r[u"key"])
            assert r[u"読み"] in WORDS_B and r[u"根拠"].strip(), (c, r[u"key"])
        for r in rec[u"C"][c]:
            m = mvd[(r[u"doc"], r[u"id"])]
            assert r[u"key"] == key_c(m) and r[u"P22"] == "VALUE_MISMATCH" and r[c] in ("POINTER_NOT_FOUND", "UNVERIFIABLE") and r[c] == view_state(m, c), (c, r[u"key"])
            assert r[u"読み"] in WORDS_C and r[u"根拠"].strip(), (c, r[u"key"])
    # 候補の間で同じ鍵は同じ読み
    for part in (u"B", u"C"):
        seen = {}
        for c in CANDIDATES:
            for r in rec[part][c]:
                x = (r[u"読み"], r[u"根拠"])
                assert seen.setdefault(r[u"key"], x) == x, (part, r[u"key"], u"同じ行が候補の間で別の読み")
    # 候補は P24 ⊂ P25 ⊂ P26 のとき以外は読みの整合のため、鍵の集合の包含は求めない(行が違えば鍵も違う)
    assert rec[u"読みの内訳"] == read_summary(rec)
    # (D)
    D = recount_D(rec)
    rd = rec[u"D"]
    assert rd[u"注入"] == D[u"注入"] == len(rec[u"注入の行"]) and rd[u"型別の注入"] == D[u"型別の注入"]
    ids = [(x[u"doc"], x[u"id"]) for x in rec[u"注入の行"]]
    assert len(set(ids)) == len(ids), u"注入の id に重複"
    for p in PROFILES:
        for k in (u"通した", u"違う", u"要確認", u"対応が付かない", u"通した(T3 を除く)"):
            assert rd[p][k] == D[p][k], (p, k)
        assert rd[p][u"型別"] == D[p][u"型別"], p
        assert D[p][u"通した"] + D[p][u"違う"] + D[p][u"要確認"] + D[p][u"対応が付かない"] == D[u"注入"], p
        assert rd[p][u"通した率"] == {u"件": D[p][u"通した"], u"分母": D[u"注入"], u"率": round(100.0 * D[p][u"通した"] / D[u"注入"], 1)}, p
        st = D[p][u"違う"] + D[p][u"要確認"]
        assert rd[p][u"止めのうち違う"][u"件"] == D[p][u"違う"] and rd[p][u"止めのうち違う"][u"分母"] == st
        assert rd[p][u"止めのうち要確認"][u"件"] == D[p][u"要確認"] and rd[p][u"止めのうち要確認"][u"分母"] == st
    for doc, cnt in rec[u"注入の件数(書類別)"].items():
        assert sum(v[u"注入の行になった"] for v in cnt.values()) == sum(1 for x in rec[u"注入の行"] if x[u"doc"] == doc), doc
    # 注入の対象: T1・T2・T5 は基準の claim が P22 の GROUNDED(無改変)
    for x in rec[u"注入の行"]:
        if x[u"型"] != "T3_ABSENT":
            assert x[u"基準の claim"] is not None and by[(x[u"doc"], x[u"基準の claim"])][u"states"][0] == "GROUNDED", (x[u"doc"], x[u"id"])
    # F-4
    f4 = recount_F4(rec, params)
    assert rec[u"F-4"][u"P23 → P25 の新 GROUNDED"] == f4[u"k"] and rec[u"F-4"][u"claim"] == f4[u"n"] and rec[u"F-4"][u"倍率"] == f4[u"倍率"]
    assert (rec[u"F-4"][u"67 書類の件"], rec[u"F-4"][u"67 書類の claim"]) == params["b67"]
    # 判定・予測
    j = judge(rec, params)
    rj = rec[u"判定"]
    assert rj[u"既定"] == j[u"既定"] and rj[u"候補の順"] == j[u"順"], u"既定が記録と違う"
    for c in CANDIDATES:
        a = rj[u"候補ごと"][c]
        assert (a[u"K-1"][u"満たす"], a[u"K-2"][u"満たす"], a[u"K-3"][u"満たす"], a[u"全部満たす"], a[u"満たさなかった基準"]) == (
            j[u"候補"][c][u"K-1"], j[u"候補"][c][u"K-2"], j[u"候補"][c][u"K-3"], j[u"候補"][c][u"全部"], j[u"候補"][c][u"満たさない"]), c
    pr = predictions(rec, params)
    assert dict((x[u"#"], x[u"当たり"]) for x in rec[u"予測"]) == pr, u"予測の当たり外れが記録と違う"
    # 順序
    o = rec[u"順序"]
    assert o[u"P26 は候補"] == p26_is_candidate(rec)
    assert o[u"取得した時刻(記録・UTC)"] == fetched[u"取得した時刻(UTC)"]
    # 環境
    env = rec[u"環境"]
    assert env[u"DEFAULT_PROFILE"] == "P22"
    for rel, want in ENGINE_AT_MEASURE.items():
        assert env[u"engine の sha256(先頭 16 桁)"][rel] == want, rel
    assert rec[u"読みの断り"].startswith(u"**読みは実装席のエージェントの読みで、人間の読みではない。**")


def check_inputs(rec):
    inp = rec[u"入力"]
    assert sha_path(FETCHED) == FETCHED_SHA256 == inp[u"取得の記録の sha256"], u"取得の記録が留めた sha256 と違う"
    assert sha_path(DRAW) == DRAW_SHA256 == inp[u"draw の sha256"], u"draw の記録が留めた sha256 と違う"
    fetched = jload(FETCHED)
    frow = dict((r["docID"], r) for r in fetched[u"取得した書類"])
    assert inp[u"書類の sha256"] == dict((d, frow[d]["sha256"]) for d in rec[u"docs"]), u"書類の sha256"
    assert inp[u"既存の cache の件数(開始時)"] == inp[u"既存の cache の件数(終了時)"], u"測定の間に既存の cache の件数が変わった"
    if os.path.isdir(EXISTING_CACHE):
        names = set(f[:-4] for f in os.listdir(EXISTING_CACHE) if f.endswith(".zip"))
        assert not (names & set(rec[u"docs"])), u"30 書類が既存の cache に在る(未使用でなくなる)"
    seed = rec[u"注入の種"]
    assert seed[u"file"] == "measure/SEED.json" and seed[u"seed_file_sha256"] == SEED_SHA256 == sha_path(os.path.join(ROOT, "measure", "SEED.json")), u"注入の種"


def check_doc(rec, doc, params):
    B = render_blocks(rec, params)
    for k, v in B.items():
        assert v in doc, u"文書に『%s』の表(記録から作った字)が無い" % k
    for k, v in prose_facts(rec, params).items():
        assert v in doc, u"文書に数のある文『%s』(記録から作った字)が無い" % k
    for lit in (u"読みはエージェントの読みで人間の読みではない", u"判定は覆さない", u"文が本当に違う", u"要確認", u"P25", u"P26", u"四型だけ", u"一つの母集団"):
        assert lit in doc, lit
    res = residual_numbers(doc, rec, params)
    assert res == ALLOWED_RESIDUAL, u"文書の散文に、記録に縛られない数が在る: %s" % res


def engine_ok():
    u"""いまの engine が、測った時点の sha か、宣言された遷移の値であること。"""
    for rel, want in sorted(ENGINE_AT_MEASURE.items()):
        got = sha16(rel)
        if got != want and rel in ENGINE_TRANSITIONS:
            later, seal_rel = ENGINE_TRANSITIONS[rel]
            assert git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(), seal_rel
            assert got == later, (rel, got, later)
            continue
        assert got == want, u"**%s が測った時点から動いている(宣言された遷移が要る)**: %s != %s" % (rel, got, want)


def labels_ok():
    try:
        from adapters.xbrl import instance as I
        for _ns, fn, _sha in I.TAXONOMY_LABEL_FILES:
            if not os.path.exists(os.path.join(I.taxonomy_dir(), fn)):
                return False
        return True
    except Exception:
        return False


def have_fresh(docs):
    if not os.path.isdir(FRESH_DIR):
        return False
    fr = dict((r["docID"], r) for r in jload(FETCHED)[u"取得した書類"])
    for d in docs:
        p = os.path.join(FRESH_DIR, d + ".zip")
        if not os.path.exists(p) or sha_path(p) != fr[d]["sha256"]:
            return False
    return True


class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.params = seal_params(cls.seal)

    def test_1_record_is_consistent(self):
        check_record(self.rec, self.params)

    def test_2_inputs_are_pinned(self):
        check_inputs(self.rec)

    def test_3_document_tables_equal_the_record(self):
        check_doc(self.rec, self.doc, self.params)

    def test_4_facts_as_measured(self):
        u"""この実行の事実を字で留める(行から数えた値。変えたら記録も文書も作り直す)。"""
        rec = self.rec
        A = recount_A(rec)
        self.assertEqual(A[u"claim"], 3923)
        self.assertEqual(dict((p, tuple(A[p][s] for s in STATES)) for p in PROFILES),
                         {"P22": (2142, 677, 690, 414), "P23": (2137, 682, 690, 414), "P24": (2196, 622, 696, 409), "P25": (2196, 325, 696, 706), "P26": (2194, 250, 774, 705)})
        B, C = recount_BC(rec)
        self.assertEqual(dict((c, (len(B[c]), len(C[c]))) for c in CANDIDATES), {"P26": (59, 436), "P25": (59, 361), "P24": (59, 64)})
        self.assertEqual(len(rec[u"動いた行"]), 507)
        for c in CANDIDATES:
            s = read_summary(rec)[c]
            self.assertEqual((s[u"B"][READ_TRUE], s[u"B"][READ_FALSE], s[u"B"][READ_SEMI]), (59, 0, 0), c)
            self.assertEqual((s[u"C"][READ_WRONG], s[u"C"][READ_UNSURE]), (0, 0), c)
        D = recount_D(rec)
        self.assertEqual(D[u"注入"], 741)
        self.assertEqual(D[u"型別の注入"], {"T1_VALUE": 195, "T2_UNIT": 263, "T3_ABSENT": 180, "T5_COINCIDENT": 103})
        self.assertEqual(dict((p, (D[p][u"通した"], D[p][u"違う"], D[p][u"要確認"], D[p][u"対応が付かない"])) for p in PROFILES),
                         {"P22": (5, 527, 205, 4), "P23": (5, 527, 205, 4), "P24": (5, 530, 202, 4), "P25": (5, 373, 359, 4), "P26": (5, 374, 358, 4)})
        f4 = recount_F4(rec, self.params)
        self.assertEqual((f4[u"k"], f4[u"n"], f4[u"倍率"]), (59, 3923, 0.793))
        j = judge(rec, self.params)
        self.assertEqual((j[u"既定"], j[u"順"]), ("P26", ["P26", "P25", "P24"]))
        for c in CANDIDATES:
            self.assertEqual(j[u"候補"][c][u"満たさない"], [], c)
        self.assertEqual(predictions(rec, self.params), {"F-1": True, "F-2": True, "F-3": True, "F-4": True, "F-5": True})

    def test_5_engine_is_the_one_measured_or_a_declared_transition(self):
        engine_ok()

    def test_6_core_untouched_default_unchanged_and_the_seal_not_edited(self):
        self.assertEqual(git("diff", "--numstat", SEAL_COMMIT, "--", "core").stdout, "")
        self.assertEqual(git("status", "--porcelain", "--", "core").stdout, "")
        for rel in FILES_NOT_TOUCHED:
            self.assertEqual(git("diff", "--numstat", SEAL_COMMIT, "--", rel).stdout, "", rel)
        from adapters.xbrl import vocabulary as V
        # この結果の commit では既定を変えない(判定は段 2 の封で別に諮る)。段 2 の遷移(vocabulary.py が宣言された値)の後は P26(封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)
        moved = sha16("adapters/xbrl/vocabulary.py") != ENGINE_AT_MEASURE["adapters/xbrl/vocabulary.py"]
        self.assertEqual(V.DEFAULT_PROFILE, "P26" if moved else "P22")
        self.assertEqual(git("diff", "--numstat", SEAL_COMMIT, "--", SEAL_REL).stdout, "")
        self.assertEqual(git("status", "--porcelain", "--", SEAL_REL).stdout, "")

    def test_7_p26_is_ordered_before_the_fetch_by_git(self):
        u"""封 §3: P26 の段 1 の commit が取得より前。取得の script の commit も P26 の後。"""
        self.assertEqual(git("merge-base", "--is-ancestor", P26_COMMIT, FETCH_SCRIPT_COMMIT).returncode, 0)
        t26 = git("log", "-1", "--format=%ct", P26_COMMIT).stdout.strip()
        tf = git("log", "-1", "--format=%ct", FETCH_SCRIPT_COMMIT).stdout.strip()
        self.assertTrue(int(t26) < int(tf))
        self.assertTrue(p26_is_candidate(self.rec))
        self.assertEqual(self.rec[u"順序"][u"P26 の commit"][:7], P26_COMMIT)

    def test_8_cache_inputs_match_the_record(self):
        docs = self.rec[u"docs"]
        if not have_fresh(docs):
            self.skipTest(u"取得した ZIP が手元に揃っていない")
        for d in docs:
            self.assertEqual(sha_path(os.path.join(FRESH_DIR, d + ".zip")), self.rec[u"入力"][u"書類の sha256"][d], d)

    def test_9_every_reading_is_one_to_one_with_its_row(self):
        for c in CANDIDATES:
            self.assertEqual(len({r[u"key"] for r in self.rec[u"B"][c]}), len(self.rec[u"B"][c]), c)
            self.assertEqual(len({r[u"key"] for r in self.rec[u"C"][c]}), len(self.rec[u"C"][c]), c)
        for r in self.rec[u"B"]["P26"] + self.rec[u"C"]["P26"]:
            self.assertTrue(r[u"根拠"].strip())


def run_script(args):
    return subprocess.run([sys.executable, SCRIPT] + args, cwd=ROOT, capture_output=True, text=True, env=dict(os.environ))


@unittest.skipUnless(have_fresh(LIGHT_DOCS) and labels_ok() if os.path.exists(FETCHED) else False, u"取得した ZIP とラベルが要る")
class RerunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)

    def test_light_plain_matches_the_record(self):
        import tempfile
        out = os.path.join(tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None), "plain.json")
        r = run_script(["--stage", "plain", "--docs", ",".join(LIGHT_DOCS), "--out", out, "--procs", "2"])
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        got = jload(out)
        for d in LIGHT_DOCS:
            self.assertEqual(got[u"claims"][d], self.rec[u"claims"][d], d)
        want = [x for x in self.rec[u"動いた行"] if x[u"doc"] in LIGHT_DOCS]
        self.assertEqual(json.dumps(got[u"動いた行"], sort_keys=True), json.dumps(want, sort_keys=True))
        wd = dict((x[u"doc"], x) for x in self.rec[u"書類別"] if x[u"doc"] in LIGHT_DOCS)
        for x in got[u"書類別"]:
            self.assertEqual(x, wd[x[u"doc"]])

    @unittest.skipUnless(RUN_HEAVY, u"AUDIT_CORE_FRESH=1 のときだけ走る(全書類の走らせ直し。注入を含み約 三十分)")
    def test_heavy_everything_matches_the_record(self):
        import tempfile
        tmp = tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None)
        rd = {u"B": {}, u"C": {}}
        for c in CANDIDATES:
            for r in self.rec[u"B"][c]:
                rd[u"B"][r[u"key"]] = {u"読み": r[u"読み"], u"根拠": r[u"根拠"]}
            for r in self.rec[u"C"][c]:
                rd[u"C"][r[u"key"]] = {u"読み": r[u"読み"], u"根拠": r[u"根拠"]}
        rp = os.path.join(tmp, "readings.json")
        with io.open(rp, "w", encoding="utf-8") as fh:
            json.dump(rd, fh, ensure_ascii=False)
        out = os.path.join(tmp, "all.json")
        r = run_script(["--stage", "all", "--readings", rp, "--out", out, "--work", os.path.join(tmp, "work"), "--procs", "4"])
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        got, want = jload(out), copy.deepcopy(self.rec)
        for part in (got, want):
            part[u"環境"].pop(u"所要秒", None)
        # 2026-10-23(既定を P22 -> P26 に切り替える 段 2)の宣言された遷移: 記録が測った時点の既定(P22)と vocabulary.py の sha16(P26 の段 1 の値)は、
        # 段 2 の後の値(既定 P26・ENGINE_TRANSITIONS の値)に読み替えて比べる。読み替えるのは、その封が履歴に在り、走らせ直しの値が段 2 の後の値のときだけ。ほかの欄は 1 字も読み替えない。
        # 2026-10-27(P27 の段 2): 遷移を宣言した file が vocabulary.py の 1 つから 5 つ(ENGINE_TRANSITIONS の全部)に増えた。どの file も、封が履歴に在り、走らせ直しの値が宣言の値のときだけ読み替える。
        for rel in sorted(ENGINE_TRANSITIONS):
            later, seal_rel = ENGINE_TRANSITIONS[rel]
            self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(), seal_rel)
            self.assertEqual((got[u"環境"][u"engine の sha256(先頭 16 桁)"][rel], want[u"環境"][u"engine の sha256(先頭 16 桁)"][rel]), (later, ENGINE_AT_MEASURE[rel]), rel)
            want[u"環境"][u"engine の sha256(先頭 16 桁)"][rel] = got[u"環境"][u"engine の sha256(先頭 16 桁)"][rel]
        self.assertEqual((got[u"環境"][u"DEFAULT_PROFILE"], want[u"環境"][u"DEFAULT_PROFILE"]), ("P26", "P22"))
        want[u"環境"][u"DEFAULT_PROFILE"] = got[u"環境"][u"DEFAULT_PROFILE"]
        self.assertEqual(json.dumps(got, sort_keys=True), json.dumps(want, sort_keys=True))


# ----------------------------------------------------------------------------------------------------------------
# 門自身の変異(壊した標本で赤くなること)
class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec0 = jload(REC)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.params = seal_params(cls.seal)

    def _mut(self):
        return copy.deepcopy(self.rec0)

    def _red(self, fn, *a):
        with self.assertRaises((AssertionError, KeyError, IndexError, TypeError, ValueError, ZeroDivisionError)):
            fn(*a)

    def test_baseline_is_green(self):
        check_record(self._mut(), self.params)
        check_inputs(self._mut())
        check_doc(self._mut(), self.doc, self.params)
        engine_ok()

    # ---- 記録の行を壊す
    def test_m1_drop_a_claim_row_or_flip_one_state_is_red(self):
        """claim の表の 1 行を落とす・state を 1 つ変えると、集計(A)・書類別・取得の記録の claim の数との突き合わせのどれかが赤。"""
        r = self._mut()
        r[u"claims"][r[u"docs"][0]].pop()
        self._red(check_record, r, self.params)
        r = self._mut()
        x = [x for x in r[u"claims"][r[u"docs"][0]] if x[u"states"][3] == "GROUNDED"][0]
        x[u"states"][3] = "VALUE_MISMATCH"
        self._red(check_record, r, self.params)

    def test_m2_drop_a_moved_row_is_red(self):
        r = self._mut()
        r[u"動いた行"].pop()
        self._red(check_record, r, self.params)

    def test_m3_a_moved_row_with_a_state_that_disagrees_with_the_claim_table_is_red(self):
        r = self._mut()
        r[u"動いた行"][0][u"views"]["P26"][u"state"] = "GROUNDED" if r[u"動いた行"][0][u"views"]["P26"][u"state"] != "GROUNDED" else "VALUE_MISMATCH"
        self._red(check_record, r, self.params)

    # ---- 読み
    def test_m4_a_reading_that_loses_its_row_or_its_word_or_its_reason_is_red(self):
        r = self._mut()
        r[u"B"]["P26"].pop()
        self._red(check_record, r, self.params)
        r = self._mut()
        r[u"C"]["P25"][0][u"読み"] = u"どちらとも"
        self._red(check_record, r, self.params)
        r = self._mut()
        r[u"C"]["P24"][0][u"根拠"] = u" "
        self._red(check_record, r, self.params)
        r = self._mut()
        r[u"B"]["P26"][0][u"読み"] = READ_OK            # (B) の語ではない
        self._red(check_record, r, self.params)

    def test_m5_the_same_row_must_have_the_same_reading_in_every_candidate(self):
        r = self._mut()
        r[u"B"]["P26"][0][u"読み"] = READ_FALSE
        self._red(check_record, r, self.params)
        r = self._mut()
        r[u"C"]["P24"][0][u"根拠"] = u"別の根拠"
        self._red(check_record, r, self.params)

    # ---- 判定の算術(読みを動かして境界を見る。記録の判定とは別に judge が動く)
    def _with_c_reading(self, cand, n_wrong, n_unsure=0):
        r = self._mut()
        keys = [x[u"key"] for x in r[u"C"][cand]]
        for c in CANDIDATES:
            for x in r[u"C"][c]:
                if x[u"key"] in keys[:n_wrong]:
                    x[u"読み"] = READ_WRONG
                elif x[u"key"] in keys[n_wrong:n_wrong + n_unsure]:
                    x[u"読み"] = READ_UNSURE
        return r

    def test_m6_k3_boundary_wrong_readings_move_the_default(self):
        """P26 の弱まった行は多いので、二%の境界は 8(満たす)と 9(満たさない)。九行目で既定は P25 に動く。P24 の 64 行では 1 行(1.56%)で満たし、2 行(3.1%)で満たさない。"""
        j8 = judge(self._with_c_reading("P26", 8), self.params)
        self.assertTrue(j8[u"候補"]["P26"][u"K-3"])
        self.assertEqual(j8[u"既定"], "P26")
        j9 = judge(self._with_c_reading("P26", 9), self.params)
        self.assertFalse(j9[u"候補"]["P26"][u"K-3"])
        self.assertEqual(j9[u"既定"], "P25")
        j = judge(self._with_c_reading("P24", 1), self.params)
        self.assertTrue(j[u"候補"]["P24"][u"K-3"])
        j = judge(self._with_c_reading("P24", 2), self.params)
        self.assertFalse(j[u"候補"]["P24"][u"K-3"])
        self.assertEqual(j[u"既定"], "P26")

    def test_m7_unsure_counts_half(self):
        """分からない 17 行 = 8.5(2% 以下 = 8.72)で満たし、18 行 = 9.0 で満たさない。"""
        self.assertTrue(judge(self._with_c_reading("P26", 0, 17), self.params)[u"候補"]["P26"][u"K-3"])
        self.assertFalse(judge(self._with_c_reading("P26", 0, 18), self.params)[u"候補"]["P26"][u"K-3"])
        self.assertTrue(judge(self._with_c_reading("P26", 4, 9), self.params)[u"候補"]["P26"][u"K-3"])       # 4 + 4.5 = 8.5
        self.assertFalse(judge(self._with_c_reading("P26", 5, 9), self.params)[u"候補"]["P26"][u"K-3"])      # 5 + 4.5 = 9.5

    def test_m8_k2_boundary_false_readings_move_the_default(self):
        """新 GROUNDED は 59 行で、3% 以下は偽 1 行(1.69%)まで。2 行(3.39%)で全候補が満たさず、既定は P22。"""
        def with_false(n):
            r = self._mut()
            keys = [x[u"key"] for x in r[u"B"]["P26"]][:n]
            for c in CANDIDATES:
                for x in r[u"B"][c]:
                    if x[u"key"] in keys:
                        x[u"読み"] = READ_FALSE
            return r
        self.assertEqual(judge(with_false(1), self.params)[u"既定"], "P26")
        j = judge(with_false(2), self.params)
        self.assertEqual(j[u"既定"], "P22")
        self.assertTrue(all(not j[u"候補"][c][u"K-2"] for c in CANDIDATES))
        self.assertEqual(judge(with_false(2), self.params)[u"候補"]["P26"][u"満たさない"], ["K-2"])
        # 準偽は偽に数えない(封の字は『偽が 3% 以下』)
        r = self._mut()
        for c in CANDIDATES:
            for x in r[u"B"][c][:5]:
                x[u"読み"] = READ_SEMI
        self.assertEqual(judge(r, self.params)[u"既定"], "P26")

    def test_m9_k1_a_candidate_pass_above_p22_moves_the_default(self):
        r = self._mut()
        x = [x for x in r[u"注入の行"] if _st(x, "P26") == "VALUE_MISMATCH" and _st(x, "P25") == "VALUE_MISMATCH"][0]
        x[u"結果"]["P26"] = ["GROUNDED", None]
        j = judge(r, self.params)
        self.assertFalse(j[u"候補"]["P26"][u"K-1"])
        self.assertEqual(j[u"既定"], "P25")
        self._red(check_record, r, self.params)          # 記録の判定・集計は元のまま
        r = self._mut()
        x = [x for x in r[u"注入の行"] if outcome(x[u"結果"]["P22"]) == u"通した"][0]
        x[u"結果"]["P22"] = ["VALUE_MISMATCH", None]       # P22 が通した数が 4 に減ると、通した 5 の候補は全部 K-1 を満たさない
        j = judge(r, self.params)
        self.assertTrue(all(not j[u"候補"][c][u"K-1"] for c in CANDIDATES))
        self.assertEqual(j[u"既定"], "P22")

    def test_m10_p26_is_not_a_candidate_when_the_commit_is_after_the_fetch(self):
        """P26 の commit が取得の後なら、候補は P25 → P24。門の p26_is_candidate を False に差し替えると既定は P25。"""
        global p26_is_candidate
        saved = p26_is_candidate
        try:
            p26_is_candidate = lambda rec: False
            j = judge(self._mut(), self.params)
            self.assertEqual((j[u"順"], j[u"既定"]), (["P25", "P24"], "P25"))
        finally:
            p26_is_candidate = saved
        self.assertEqual(judge(self._mut(), self.params)[u"既定"], "P26")

    def test_m11_a_recorded_default_or_order_that_disagrees_is_red(self):
        r = self._mut()
        r[u"判定"][u"既定"] = "P25"
        self._red(check_record, r, self.params)
        r = self._mut()
        r[u"順序"][u"P26 は候補"] = False
        self._red(check_record, r, self.params)
        r = self._mut()
        r[u"判定"][u"候補ごと"]["P24"][u"K-3"][u"満たす"] = False
        self._red(check_record, r, self.params)

    # ---- 注入
    def test_m12_injection_rows_must_add_up(self):
        r = self._mut()
        r[u"注入の行"].pop()
        self._red(check_record, r, self.params)
        r = self._mut()
        r[u"注入の行"].append(copy.deepcopy(r[u"注入の行"][0]))            # id の重複
        self._red(check_record, r, self.params)
        r = self._mut()
        x = [x for x in r[u"注入の行"] if x[u"型"] == "T1_VALUE"][0]
        x[u"基準の claim"] = [c[u"id"] for c in r[u"claims"][x[u"doc"]] if c[u"states"][0] != "GROUNDED"][0]     # 基準が P22 の GROUNDED でない
        self._red(check_record, r, self.params)

    def test_m13_a_changed_injection_outcome_is_seen_by_the_summary(self):
        r = self._mut()
        x = [x for x in r[u"注入の行"] if _st(x, "P25") == "POINTER_NOT_FOUND"][0]
        x[u"結果"]["P25"] = ["VALUE_MISMATCH", None]
        self._red(check_record, r, self.params)              # 違う と 要確認 の件数が集計と違う

    # ---- 予測の幅(封の字から読む)
    def test_m14_predictions_move_with_the_numbers(self):
        r = self._mut()
        for x in [x for x in r[u"注入の行"] if _st(x, "P25") == "VALUE_MISMATCH"][:30]:
            x[u"結果"]["P25"] = ["GROUNDED", None]            # P25 が通した 35 / 741 = 4.7% > 4%
        self.assertFalse(predictions(r, self.params)["F-5"])
        self.assertFalse(judge(r, self.params)[u"候補"]["P25"][u"K-1"])
        self.assertFalse(predictions(r, self.params)["F-3"])
        p = dict(self.params)
        p["F-1"] = [(18.0, 25.0), (5.0, 13.0)]                 # P22 の違う率 17.3% が幅の外
        self.assertFalse(predictions(self._mut(), p)["F-1"])
        p = dict(self.params)
        p["F-4"] = [(0.3, 0.7)]
        self.assertFalse(predictions(self._mut(), p)["F-4"])
        p = dict(self.params)
        p["F-2"] = [(19.0, 24.0)]
        self.assertFalse(predictions(self._mut(), p)["F-2"])

    def test_m15_seal_params_are_read_from_the_seal_text(self):
        p = seal_params(self.seal.replace(u"**2% 以下**", u"**1% 以下**"))
        self.assertEqual(p["k3"], 1.0)
        self.assertEqual(self.params["k3"], 2.0)
        self.assertEqual(self.params["k2"], 3.0)
        self.assertEqual(self.params["b67"], (148, 7799))
        self.assertEqual((self.params["F-1"], self.params["F-2"], self.params["F-4"], self.params["F-5"]),
                         ([(12.0, 25.0), (5.0, 13.0)], [(13.0, 24.0)], [(0.3, 1.5)], [(0.0, 4.0)]))

    # ---- 文書
    def test_m16_a_number_in_a_document_table_is_red(self):
        B = render_blocks(self.rec0, self.params)
        line = [l for l in B["state"].splitlines() if l.startswith(u"| P25 |")][0]
        self.assertIn(line, self.doc)
        self._red(check_doc, self.rec0, self.doc.replace(line, line.replace(u"2196", u"2197")), self.params)

    def test_m17_a_number_in_a_prose_sentence_is_red(self):
        P = prose_facts(self.rec0, self.params)
        self.assertIn(P["moved"], self.doc)
        self._red(check_doc, self.rec0, self.doc.replace(P["moved"], P["moved"].replace(u"五百七", u"五百八")), self.params)

    def test_m18_a_new_unbound_number_in_prose_is_red(self):
        self._red(check_doc, self.rec0, self.doc + u"\nなお本件は 99 件である。\n", self.params)

    def test_m19_the_reader_caveat_must_stay_in_the_document(self):
        self._red(check_doc, self.rec0, self.doc.replace(u"読みはエージェントの読みで人間の読みではない", u"読みは確かである"), self.params)

    # ---- 入力・engine・順序
    def test_m20_spoiled_inputs_are_red(self):
        r = self._mut()
        r[u"入力"][u"書類の sha256"][r[u"docs"][0]] = u"0" * 64
        self._red(check_inputs, r)
        r = self._mut()
        r[u"入力"][u"取得の記録の sha256"] = u"0" * 64
        self._red(check_inputs, r)
        r = self._mut()
        r[u"入力"][u"既存の cache の件数(終了時)"] += 1
        self._red(check_inputs, r)
        r = self._mut()
        r[u"注入の種"][u"seed_file_sha256"] = u"0" * 64
        self._red(check_inputs, r)

    def test_m21_a_wrong_engine_sha_is_red(self):
        global ENGINE_AT_MEASURE, ENGINE_TRANSITIONS
        old, old_t = dict(ENGINE_AT_MEASURE), dict(ENGINE_TRANSITIONS)
        try:
            for rel in sorted(old):
                ENGINE_TRANSITIONS = {}
                ENGINE_AT_MEASURE = dict(old, **{rel: "0" * 16})
                self._red(engine_ok)
                ENGINE_AT_MEASURE = dict(old)
        finally:
            ENGINE_AT_MEASURE, ENGINE_TRANSITIONS = old, old_t
        engine_ok()

    def test_m22_a_claim_count_that_disagrees_with_the_fetch_record_is_red(self):
        r = self._mut()
        r[u"書類別"][0][u"claims"] += 1
        self._red(check_record, r, self.params)

    def test_m23_the_untouched_cache_rule(self):
        r = self._mut()
        r[u"入力"][u"既存の cache の件数(開始時)"] -= 1
        self._red(check_inputs, r)

    def test_m24_key_leaks_catches_a_thirty_two_hex_string(self):
        import importlib.util
        sp = importlib.util.spec_from_file_location("fresh_script_for_gate", SCRIPT)
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        self.assertEqual(m.key_leaks(u"abc " + u"0123456789abcdef" * 2 + u" xyz"), [u"32 桁の 16 進"])
        self.assertEqual(m.key_leaks(u"0123456789abcdef" * 4), [])                                  # sha256 は通す
        self.assertEqual(m.key_leaks(u"ProvisionForDirectorsRetirementBenefitsCurrentYearInstant"), [])    # 長い要素の名前は通す
        self.assertTrue(m.key_leaks(u"Subscription-Key=x"))
        self.assertEqual(m.key_leaks(json.dumps(self.rec0, ensure_ascii=False)), [], u"記録に鍵らしい字が無い")


if __name__ == "__main__":
    unittest.main()
