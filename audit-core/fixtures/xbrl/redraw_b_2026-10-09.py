# -*- coding: utf-8 -*-
"""封B の材料を引き直す(2 件)。封 ``docs/XBRL_REDRAW_B_SEAL_2026-10-09.md``。

**通信しない。EDINET に触れない。ZIP を取らない。** 引くだけ。

再発条件を抽選器から消す設計(人間の裁定 2026-10-09):

1. 候補の一覧は**別の席の枝のファイルを読むだけ**で、本線へ複製しない。sha256 を照合する。
2. **キャッシュに在る docID を母集団から機械的に除く。** 「未取得」を後から確認する性質ではなく
   **引いた時点で定義上そうである**ようにする。
3. **キャッシュの一覧(マニフェスト)は封の前に生成して sha256 を封じる。** 抽選器は
   マニフェストの sha256 と、**実機のキャッシュがマニフェストと一致すること**を両方照合し、
   違えば **止まる**(抽選前後でキャッシュ除外の集合が変わっていないことを機械で保証する)。

  python3 fixtures/xbrl/redraw_b_2026-10-09.py --out <path>
"""
import argparse, glob, hashlib, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# --- 封じた値(字で書く。1 文字も変えない) ------------------------------------
CANDIDATES_SHA256 = "7117b8af4ef412b8b7220a95a09ea18d907e05293ccbd0e0c53ff89e62151568"
CANDIDATES_ROWS = 186
CANDIDATES_SOURCE_COMMIT = "bee2999"          # 枝 feature/audit-core-xbrl-fix5
CACHE_MANIFEST_SHA256 = "5ccbdebfd45bc8f4f0b490e5ce977296c30c38bf076c87fad4b52a353af01c0c"
SEED = "d427df6"                              # 別の席のコミット(本線が選べない値)
RNG_LABEL = "redraw-B-2026-10-09|sign-axis"
DRAW_N = 2
# 割当は引く順だけで決める。**2 件とも封B** なので選ぶ余地が無い。
ASSIGNMENT = ("封B(符号)", "封B(符号)")

DEVELOPMENT_DOCS = ("S100Z4Q1", "S100Z4B6", "S100YMFV", "S100Z37J")
READ_INDEPENDENT = ("S100Z3BW", "S100Z4DE")
SEALED_2026_10_08 = ("S100Z2S2", "S100Z359", "S100Z2RN", "S100Z3PT", "S100Z3T5",
                     "S100Z38M", "S100Z1T7", "S100Z3WK", "S100Z3CG", "S100Z2EI")
ROLELESS_FETCHED = ("S100Z1WR", "S100Z433", "S100Z39P", "S100Z4N9")
# 2026-10-09 に引いた 4 件。封A の 2 件は現役、封B の旧 2 件は非盲検になった。
DRAW_2026_10_09 = ("S100Z3JY", "S100Z35K", "S100Z3CO", "S100Z4PA")
EXCLUDE_NAMED = (DEVELOPMENT_DOCS + READ_INDEPENDENT + SEALED_2026_10_08
                 + ROLELESS_FETCHED + DRAW_2026_10_09)

CACHE_DIR = os.path.expanduser("~/.cache/audit-core/edinet")
MANIFEST = os.path.join(HERE, "cache_manifest_2026-10-09.json")
DEFAULT_CANDIDATES = os.path.expanduser(
    "~/Desktop/audit-core-xbrl-fix/audit-core/fixtures/xbrl/candidates_2026-09.json")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def live_cache():
    return sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(CACHE_DIR, "*.zip")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default=DEFAULT_CANDIDATES)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    # 1. 候補の一覧(別の席の枝。読むだけ)
    if not os.path.exists(a.candidates):
        print("候補の一覧が無い:", a.candidates); return 2
    got = sha(a.candidates)
    if got != CANDIDATES_SHA256:
        print("候補の一覧の sha が封と違う\n  封: %s\n  実: %s" % (CANDIDATES_SHA256, got)); return 2
    rows = json.load(open(a.candidates, encoding="utf-8"))["rows"]
    if len(rows) != CANDIDATES_ROWS:
        print("候補の件数が封と違う:", len(rows), "!=", CANDIDATES_ROWS); return 2

    # 2. キャッシュのマニフェスト ― 封じた sha と、実機との一致の両方
    if sha(MANIFEST) != CACHE_MANIFEST_SHA256:
        print("キャッシュのマニフェストの sha が封と違う"); return 3
    man = json.load(open(MANIFEST, encoding="utf-8"))["docIDs"]
    now = live_cache()
    if now != sorted(man):
        print("**実機のキャッシュがマニフェストと違う。止まる。**")
        print("  封じた時点に無く いま在る:", sorted(set(now) - set(man)))
        print("  封じた時点に在り いま無い:", sorted(set(man) - set(now)))
        return 3

    # 3. 母集団 = 候補 − 字で書いた除外 − キャッシュに在るもの
    exclude = set(EXCLUDE_NAMED) | set(man)
    pool = [r for r in rows if r["docID"] not in exclude]
    pool.sort(key=lambda r: (r["date"], r["docID"]))
    if len(pool) < DRAW_N:
        print("母集団が足りない:", len(pool)); return 3

    label = "%s|%s|%s|%s" % (SEED, RNG_LABEL, pool[0]["date"], pool[-1]["date"])
    picked = random.Random(label).sample(pool, DRAW_N)

    print("候補 %d / 字で書いた除外 %d / キャッシュ除外 %d / 母集団 %d"
          % (len(rows), len(EXCLUDE_NAMED), len(man), len(pool)))
    print("python3 %s" % sys.version.split()[0])
    print("rng label(種を除く): <種>|%s|%s|%s" % (RNG_LABEL, pool[0]["date"], pool[-1]["date"]))
    print()
    out = []
    for i, (r, role) in enumerate(zip(picked, ASSIGNMENT), 1):
        inc = r["docID"] in now
        print("  %d. %-10s %-32s %s -> %s%s"
              % (i, r["docID"], (r.get("filerName") or "")[:32], r["date"], role,
                 "  **キャッシュに在る(あってはならない)**" if inc else "  未取得"))
        if inc:
            print("引いた件がキャッシュに在る ― 定義に反する。止まる。"); return 4
        out.append({"order": i, "docID": r["docID"], "filerName": r.get("filerName"),
                    "date": r["date"], "seal": role, "in_cache_at_draw": False})

    rec = {"tool": "redraw_b_2026-10-09.py",
           "seal": "docs/XBRL_REDRAW_B_SEAL_2026-10-09.md",
           "reason": "封B の旧 2 件(S100Z3CO・S100Z4PA)が封印の 4 分前に別の席に取得され非盲検になったため(追記 862ce7a)。封B の予測 4f9bd14 は変更しない。",
           "candidate_source": {"path": "candidates_2026-09.json", "rows": len(rows),
                                "sha256": got, "source_commit": CANDIDATES_SOURCE_COMMIT},
           "seed_source": "別の席のコミット %s(本線が選べない値)" % SEED,
           "rng_label_without_the_seed": "<種>|%s|%s|%s" % (RNG_LABEL, pool[0]["date"], pool[-1]["date"]),
           "python": sys.version.split()[0],
           "excluded_named": len(EXCLUDE_NAMED), "excluded_by_cache": len(man),
           "cache_manifest_sha256": CACHE_MANIFEST_SHA256,
           "live_cache_equals_manifest": True,
           "pool": len(pool), "zips_fetched": False, "picked": out}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1); f.write("\n")
    print("\nwritten:", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
