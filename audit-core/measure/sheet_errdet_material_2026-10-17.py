# -*- coding: utf-8 -*-
"""A / C の材料(封 docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md §5-2)。

**A と C は同じ 1 回の生成を共有する。**だから材料は 1 つで、入力差は**ゼロ**である。
渡すのは **束ねた変種の報告文から切り出した金額の一覧 + 抜粋 76 行**。
**Core の候補一覧・状態・正解ラベル・誤りの件数は渡さない。**

**抜粋の節は段 11 の材料と 1 文字も同じであることを機械で確かめる。**
**問いは段 11 の問いを接頭とする**(`sheet_errdet_question_2026-10-17.py` が作る)。

    python3 measure/sheet_errdet_material_2026-10-17.py <出力の親ディレクトリ>
"""
import hashlib
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT11 = os.path.join(FX, "m11_material_2026-10-16.json")
LAB11REC = os.path.join(FX, "m11_label_material_2026-10-16.json")
MAKE = os.path.join(FX, "errdet_make_2026-10-17.json")
OUT = os.path.join(FX, "errdet_material_2026-10-17.json")
SEAL = "docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


Q = _mod("q_for_errdet", "sheet_errdet_question_2026-10-17.py")
LAB11 = _mod("lab11_for_errdet", "sheet_m11_label_material_2026-10-16.py")
CO = _mod("core_for_errdet_mat", "sheet_errdet_core_2026-10-17.py")
BANNED = LAB11.BANNED              # **段 11 の禁じ語をそのまま当てる**


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def extract_block():
    """抜粋の節を**段 11 の材料から取り出す**(LAB11 と同じ切り方)。"""
    mat = load(MAT11)
    return (mat["prompt"].split("----- 表(ここから) -----")[1]
            .split("----- 表(ここまで) -----")[0].strip())


def check_banned(text, banned=None):
    for w in (BANNED if banned is None else banned):
        if w in text:
            raise AssertionError("**禁じた語が材料に在る: %s**" % w)
    return True


def body_of(question, extract, rows):
    """**段 11 と同じ並び**(問い / (A) 抜粋 / (B) 金額の一覧)。"""
    out = [question, "", "(A) 表の抜粋", extract, "",
           "(B) 金額の一覧(%d 件)" % len(rows)]
    for r in rows:
        out.append("- id: %s / 金額: %s / 文: %s"
                   % (r["id"], r["金額の表記"], r["文"]))
    return "\n".join(out)


def main():
    parent = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out")
    if os.path.exists(OUT):
        raise SystemExit("材料が既に在る: %s(作り直さない)" % OUT)
    os.makedirs(parent, exist_ok=True)
    mk = load(MAKE)
    bundle = mk["束ねた変種"]["本文"]
    planted = {p["id"]: p for p in mk["植えた誤り"]}

    question = Q.question_text()
    Q.check(question)
    # **抜粋は段 11 と 1 文字も同じ**
    extract = extract_block()
    lab = load(LAB11REC)
    if lab["question"] != Q.base_question():
        raise SystemExit("**段 11 の問いが記録と違う。接頭に使えない**")

    claims, _binds = CO.run_core(bundle)
    if len(claims) != 35:
        raise SystemExit("**主張が %d 件。35 件でないので実験は無効**" % len(claims))
    for cid, p in planted.items():
        c = [x for x in claims if x["id"] == cid][0]
        if c["value"] != p["植えた値"]:
            raise SystemExit("**%s に誤りが入っていない**" % cid)
    rows = [{"id": c["id"], "金額の表記": c["text"], "文": c["sentence"]}
            for c in claims]

    made = []
    for seat, order in (("seat1", rows), ("seat2", list(reversed(rows)))):
        text = body_of(question, extract, order)
        check_banned(text)
        if not text.startswith(Q.base_question()):
            raise SystemExit("**段 11 の問いが接頭になっていない**")
        d = os.path.join(parent, "errdet_%s" % seat)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "task.txt")
        io.open(p, "w", encoding="utf-8").write(text)
        meta = [s for s in lab["seats"] if s["seat"] == seat][0]
        made.append({"seat": seat, "path": p, "model": meta["model"],
                     "order": meta["order"], "字数": len(text),
                     "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                     "段 11 の問いが接頭": True,
                     "先頭の id": order[0]["id"], "末尾の id": order[-1]["id"]})
        print("%s: %d 字 / 先頭 %s / 末尾 %s -> %s"
              % (seat, len(text), order[0]["id"], order[-1]["id"], p))

    rec = {"seal": SEAL,
           "step": "封 §8 の 5。**生成より先に commit する**",
           "**A と C は同じ材料・同じ生成を共有する(入力差ゼロ)**": True,
           "報告文": {"どれ": "束ねた変種(誤り 8 件)", "字数": len(bundle),
                   "誤りの id": sorted(planted)},
           "問い": {"段 11 の問いの字数": len(Q.base_question()),
                  "足した字数": len(question) - len(Q.base_question()),
                  "全体の字数": len(question),
                  "sha256": hashlib.sha256(question.encode("utf-8")).hexdigest(),
                  "固定語彙": list(Q.VOCAB),
                  "注": ("**この欄を足すことは席に誤りの存在を示唆しうる。**"
                        "**測れるのは「誤りを示唆する問いの下での検出性能」であり、"
                        "通常の報告文を自然に読む場面のものとは区別する**")},
           "抜粋": {"字数": len(extract), "段 11 と同一": True},
           "渡していないもの": ["Core の候補一覧", "Core の状態", "正解ラベル",
                        "誤りの件数", "誤りの型の割り当て", "採点基準", "封の内容",
                        "候補範囲実験の結果", "方式 C の結果"],
           "banned_checked": BANNED,
           "files": made}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("問い: 段 11 の %d 字 + 足した %d 字 / 抜粋 %d 字"
          % (len(Q.base_question()), len(question) - len(Q.base_question()),
             len(extract)))
    print("->", OUT)


if __name__ == "__main__":
    main()
