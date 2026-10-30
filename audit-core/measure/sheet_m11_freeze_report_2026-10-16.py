# -*- coding: utf-8 -*-
"""段 11 の報告文を**凍結する**(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §11 の 5・§7)。

**生成は 1 回だけ。作り直さない。**
席には `prompt.txt` だけを渡し、**席が自分で `report.txt` に書いた**(私は写していない)。

この script は書き出された `report.txt` を読み、**engine を当てる前に**記録として固める。
  * 記録が既に在れば**何もせずに止まる**(作り直しの事故を防ぐ)
  * 指示文の sha256 が材料の記録と一致することを確かめる
  * **1200 字の上限**を確かめる

    python3 measure/sheet_m11_freeze_report_2026-10-16.py <report.txt> <使ったトークン数>
"""
import datetime
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")
OUT = os.path.join(FX, "m11_report_2026-10-16.json")
SEAL = "docs/DOMAIN1_M11_SEAL_2026-10-16.md"
MODEL = "claude-sonnet-4-5"
# sonnet の出力の単価(2026-10 時点の USD/1M)。**全部が出力だと仮定した上限**を出す
USD_PER_M_OUTPUT = 15.0
CAP_USD = 4.0


def cost_upper_bound(tokens):
    """**費用の上限**を出す(全部が出力トークンだと仮定する)。

    入力は出力より安いので、これは**必ず実費以上**である。
    **推測した実費を書かない**(記憶 `count-lines-not-guesses`)。
    """
    usd = tokens * USD_PER_M_OUTPUT / 1e6
    return {"使ったトークン(実測)": tokens,
            "費用の上限(全部が出力だと仮定)": round(usd, 4),
            "上限の根拠": ("sonnet の出力 %.0f USD/1M。入力はこれより安いので"
                      "**実費はこの数より小さい**" % USD_PER_M_OUTPUT),
            "人間が決めた上限": CAP_USD,
            "上限の中か": usd <= CAP_USD}


def main():
    path, tokens = sys.argv[1], int(sys.argv[2])
    if os.path.exists(OUT):
        raise SystemExit("報告文が既に在る: %s(**作り直さない**)" % OUT)
    mat = json.load(io.open(MAT, encoding="utf-8"))
    prompt = mat["prompt"]
    report = io.open(path, encoding="utf-8").read().strip()
    psha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    limit = mat["limits"]["report_chars"]
    if len(report) > limit:
        raise SystemExit("**報告文が上限を超えた: %d > %d**" % (len(report), limit))
    commit = subprocess.run(["git", "log", "-1", "--format=%h", "--",
                             "fixtures/sheet/m11_material_2026-10-16.json"],
                            cwd=ROOT, capture_output=True, text=True).stdout.strip()
    rec = {"seal": SEAL,
           "purpose": ("段 11 の報告文。**1 回だけ生成し、engine を当てる前に凍結する**"
                       "(封 §7)"),
           "model": "%s(Agent, subagent_type=general-purpose, model=sonnet)" % MODEL,
           "runs": 1, "regenerated": False,
           "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
           "material_commit": commit,
           "engines": ["measure/sheet_m7_engine_2026-10-15.py(旧)",
                       "measure/sheet_sainyuu_engine_2026-10-16.py(新)"],
           "engine_changed_for_m11": False,
           "prompt_sha256": psha,
           "prompt_chars": len(prompt),
           "prompt_identical_to_stage4": mat["prompt_identical_to_stage4"],
           "report_chars": len(report),
           "limit_report_chars": limit,
           "within_limit": len(report) <= limit,
           "cost": cost_upper_bound(tokens),
           "handed_to_seat": ["prompt.txt のみ(他のファイルを読まないよう指示した)"],
           "written_by": "席が自分で report.txt に書いた(私は写していない)",
           "withheld": ["engine の判定", "範囲の同定結果", "照合結果", "合否ラベル",
                        "封の内容", "仕様", "段 3〜段 9 の結果", "診断(P-5)の結果",
                        "親の規則", "機会の件数(O-1〜O-8)", "裏づけの規則",
                        "③の存在", "別名の規則", "歳入側の資料の存在"],
           "report": report}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("報告文 %d 字(上限 %d)/ 指示文 %d 字 sha256 %s…"
          % (len(report), limit, len(prompt), psha[:16]))
    print("費用の上限: %s USD(人間の上限 %s)"
          % (rec["cost"]["費用の上限(全部が出力だと仮定)"], CAP_USD))
    print("->", OUT)


if __name__ == "__main__":
    main()
