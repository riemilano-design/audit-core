# -*- coding: utf-8 -*-
"""A / C の席の答えを**凍結する**(封 docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md §8 の 5)。

**検査は段 11 の `check()` を import してそのまま使う。**
**ただし段 11 の `check()` は 6 欄しか写さない**ので、
**足した「不一致の種類」を生の答えから貼り直す**(`attach_kind`)。
**段 11 の file は 1 文字も触らない。**

**やり直しをしない** ― 機械検査に落ちた答えは**その件を「判定不能」として数える。**
費用は**席ごとの単価**で、**2 席の合計で 4 USD** を見る。

    python3 measure/sheet_errdet_freeze_2026-10-17.py <seat1|seat2> <answers.json> <トークン数>
"""
import datetime
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MATREC = os.path.join(FX, "errdet_material_2026-10-17.json")
MAKE = os.path.join(FX, "errdet_make_2026-10-17.json")
SEAL = "docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md"
USD_PER_M_OUTPUT = {"seat1": 15.0, "seat2": 5.0}
CAP_USD = 4.0
KIND_FIELD = "不一致の種類"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


FR11 = _mod("freeze11_for_errdet", "sheet_m11_freeze_answers_2026-10-16.py")
Q = _mod("q_for_errdet_freeze", "sheet_errdet_question_2026-10-17.py")
check = FR11.check                 # **段 11 の検査をそのまま使う**


def out_path(seat):
    return os.path.join(FX, "errdet_answers_%s_2026-10-17.json" % seat)


def attach_kind(ok, raw):
    """**足した欄を貼り直す。**語彙に無い字は `不明` に倒し、落ちた件を記録する。

    段 11 の `check()` は 6 欄しか写さないので、ここで足す。
    **判定を 1 か所に置く**(門が壊した答えで当てられるように)。
    """
    by = {a.get("id"): a for a in raw if isinstance(a, dict)}
    bad = []
    out = []
    for a in ok:
        got = (by.get(a["id"]) or {}).get(KIND_FIELD)
        if got is None:
            bad.append({"id": a["id"], "理由": "%s が無い(不明に倒した)" % KIND_FIELD})
            got = "不明"
        elif got not in Q.VOCAB:
            bad.append({"id": a["id"],
                        "理由": "%s が語彙に無い: %r(不明に倒した)"
                                % (KIND_FIELD, got)})
            got = "不明"
        b = dict(a)
        b[KIND_FIELD] = got
        out.append(b)
    return out, bad


def cost_upper_bound(seat, tokens):
    rate = USD_PER_M_OUTPUT[seat]
    return {"使ったトークン(実測)": tokens,
            "単価(出力・USD/1M)": rate,
            "費用の上限(全部が出力だと仮定)": round(tokens * rate / 1e6, 4)}


def running_total(seat, usd):
    other = "seat2" if seat == "seat1" else "seat1"
    p = out_path(other)
    prev = 0.0
    if os.path.exists(p):
        prev = json.load(io.open(p, encoding="utf-8"))["費用"][
            "費用の上限(全部が出力だと仮定)"]
    total = round(usd + prev, 4)
    return {"もう 1 席の上限": prev, "2 席の合計の上限": total,
            "人間が決めた上限": CAP_USD, "上限の中か": total <= CAP_USD,
            "判定": ("上限の中" if total <= CAP_USD
                   else "**打ち切り。超えた分を記録する**")}


def main():
    seat, path, tokens = sys.argv[1], sys.argv[2], int(sys.argv[3])
    p = out_path(seat)
    if os.path.exists(p):
        raise SystemExit("答えが既に在る: %s(**やり直さない**)" % p)
    mat = json.load(io.open(MATREC, encoding="utf-8"))
    meta = [f for f in mat["files"] if f["seat"] == seat][0]
    # **一覧の id は材料の task.txt から読む**(別の所から持ってこない)
    ids = [l.split("- id: ")[1].split(" /")[0]
           for l in io.open(meta["path"], encoding="utf-8").read().split("\n")
           if l.startswith("- id: ")]
    want = set(ids)
    if len(want) != 35:
        raise SystemExit("**材料の一覧が %d 件。35 件でない**" % len(want))
    raw = io.open(path, encoding="utf-8").read().strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    answers = json.loads(raw)
    if not isinstance(answers, list):
        raise SystemExit("JSON の配列でない")
    ok, bad = check(answers, want)
    ok, bad2 = attach_kind(ok, answers)
    cost = cost_upper_bound(seat, tokens)
    rec = {"seal": SEAL, "seat": seat, "model": meta["model"],
           "order": meta["order"], "runs": 1, "regenerated": False,
           "material": "fixtures/sheet/errdet_material_2026-10-17.json",
           "task_sha256": meta["sha256"],
           "盲検": ("**正解ラベル・誤りの件数・採点基準は渡していない。**"
                  "**問いが「不一致の種類」を訊くので、誤りの存在は示唆されている**"),
           "answered_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
           "費用": cost,
           "費用の累計": running_total(seat, cost["費用の上限(全部が出力だと仮定)"]),
           "機械検査に落ちた件": bad,
           "足した欄で落ちた件": bad2,
           "落ちた件の扱い": ("**その件を「判定不能」/「不明」に倒して数える。"
                      "再生成しない**(封 §6)"),
           "answers": sorted(ok, key=lambda a: a["id"])}
    json.dump(rec, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%s(%s / %s): %d 件(一覧 %d 件)/ 落ちた件 %d / 足した欄で落ちた件 %d"
          % (seat, rec["model"], rec["order"], len(ok), len(want), len(bad),
             len(bad2)))
    for b in bad + bad2:
        print("   ", json.dumps(b, ensure_ascii=False))
    print("費用: %s" % json.dumps(cost, ensure_ascii=False))
    print("累計: %s" % json.dumps(rec["費用の累計"], ensure_ascii=False))
    print("->", p)


if __name__ == "__main__":
    main()
