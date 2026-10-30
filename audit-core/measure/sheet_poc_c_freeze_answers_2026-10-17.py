# -*- coding: utf-8 -*-
"""方式 C の席の答えを**凍結する**(封 docs/DOMAIN1_POC_C_SEAL_2026-10-17.md §9 の 4)。

**席には `task.txt` だけを渡し、席が自分で `answers.json` に書いた。**
**やり直しをしない** ― 機械検査に落ちた答えは**その件を「判定不能」として数える。**

**検査は段 11 の `check()` を import してそのまま使う**(封 §9 の 4)。
**C 用に書き直さない** ― 書き直すと A と C で別の寛容さを当てることになる。

費用は**段 11 と同じ式**(全部が出力トークンだと仮定した上限)。
**単価は席ごとに違う**(sonnet 15 / haiku 5 USD/1M)。
**2 席の合計が 4 USD を超えたら打ち切りとして記録する。**

    python3 measure/sheet_poc_c_freeze_answers_2026-10-17.py <seat1|seat2> <answers.json> <トークン数>
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
MATREC = os.path.join(FX, "poc_c_material_2026-10-17.json")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")
SEAL = "docs/DOMAIN1_POC_C_SEAL_2026-10-17.md"
# **人が決めた数・公開の単価は字で留める**
USD_PER_M_OUTPUT = {"seat1": 15.0, "seat2": 5.0}
CAP_USD = 4.0


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


FR11 = _mod("freeze11_for_c", "sheet_m11_freeze_answers_2026-10-16.py")
check = FR11.check                 # **段 11 の検査をそのまま使う**
FIELDS = FR11.FIELDS


def out_path(seat):
    return os.path.join(FX, "poc_c_answers_%s_2026-10-17.json" % seat)


def cost_upper_bound(seat, tokens):
    """**費用の上限**(全部が出力トークンだと仮定する)。

    入力は出力より安いので**必ず実費以上**である。
    **推測した実費は書かない**(記憶 `count-lines-not-guesses`)。
    """
    rate = USD_PER_M_OUTPUT[seat]
    return {"使ったトークン(実測)": tokens,
            "単価(出力・USD/1M)": rate,
            "費用の上限(全部が出力だと仮定)": round(tokens * rate / 1e6, 4)}


def running_total(seat, usd):
    """**2 席の合計**を出す。もう 1 席が凍結済みならそれも足す。"""
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
    want = {c["id"] for c in json.load(io.open(BINDS, encoding="utf-8"))["claims"]
            if not c.get("skipped")}
    raw = io.open(path, encoding="utf-8").read().strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    answers = json.loads(raw)
    if not isinstance(answers, list):
        raise SystemExit("JSON の配列でない")
    ok, bad = check(answers, want)
    cost = cost_upper_bound(seat, tokens)
    rec = {"seal": SEAL, "seat": seat, "model": meta["model"],
           "order": meta["order"], "runs": 1, "regenerated": False,
           "盲検": ("**正解集合には盲検**(正解基準・採点の規則は渡していない)。"
                  "**道具の証拠は見ている**(それが方式 C である)"),
           "material": "fixtures/sheet/poc_c_material_2026-10-17.json",
           "task_sha256": meta["C の sha256"],
           "A が接頭": meta["A が接頭"],
           "answered_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
           "費用": cost, "費用の累計": running_total(seat, cost[
               "費用の上限(全部が出力だと仮定)"]),
           "機械検査に落ちた件": bad,
           "落ちた件の扱い": ("**その件を「判定不能」として数える。再生成しない**"
                      "(封 §5)"),
           "answers": sorted(ok, key=lambda a: a["id"])}
    json.dump(rec, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%s(%s / %s): %d 件(一覧 %d 件)/ 機械検査に落ちた件 %d"
          % (seat, rec["model"], rec["order"], len(ok), len(want), len(bad)))
    for b in bad:
        print("   ", json.dumps(b, ensure_ascii=False))
    print("費用: %s" % json.dumps(cost, ensure_ascii=False))
    print("累計: %s" % json.dumps(rec["費用の累計"], ensure_ascii=False))
    print("->", p)


if __name__ == "__main__":
    main()
