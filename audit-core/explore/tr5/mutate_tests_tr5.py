# -*- coding: utf-8 -*-
"""便 TR5: 単体試験 test_tr5 が、新しい規則をわざと壊すと赤くなるかを見る。

使い方: python3 -I mutate_tests_tr5.py <作業用の空の folder>
tr5 の file と tr4 の file を作業用の folder に写し(tr4 は ../tr4 の形で)、1 か所ずつ壊して試験を走らせる。repo は書き換えない。
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TR4 = os.path.join(HERE, "..", "tr4")
WORK = sys.argv[1]
MUTS = [
    ("rules_tr5.py", "    if k is None:\n        return True, \"前期の数の札なのに、数の近くに前期の字が無い\"", "    pass", "R2 を消す"),
    ("rules_tr5.py", "    return {rid for ids in groups.values() if len(ids) >= 2 for rid in ids}", "    return set()", "R1 を消す"),
    ("rules_tr5.py", "        key = (rec[\"行\"], sentence_of(md, rec[\"行\"], rec[\"始め\"]), tag.get(\"項目\"), tag.get(\"期\"))",
     "        key = (rec[\"行\"], tag.get(\"項目\"), tag.get(\"期\"))", "R1 で文を分けない"),
    ("rules_tr5.py", "    if tag.get(\"種類\") != \"金額\" or tag.get(\"期\") not in (\"前期\", \"前期末\"):\n        return False, None",
     "    if tag.get(\"期\") not in (\"前期\", \"前期末\"):\n        return False, None", "R2 を増減の札にも当てる"),
    ("rules_tr5.py", "            return r[\"単位\"]\n    for r", "            return \"百万円\"\n    for r", "単位を本文から取らない"),
]


def main():
    red = 0
    for f, a, b, name in MUTS:
        root = os.path.join(WORK, "m")
        shutil.rmtree(root, ignore_errors=True)
        os.makedirs(os.path.join(root, "tr5"))
        shutil.copytree(TR4, os.path.join(root, "tr4"), ignore=shutil.ignore_patterns("__pycache__"))
        for x in ("rules_tr5.py", "test_tr5.py"):
            shutil.copy(os.path.join(HERE, x), os.path.join(root, "tr5"))
        p = os.path.join(root, "tr5", f)
        with open(p, encoding="utf-8") as fh:
            t = fh.read()
        assert a in t, name
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(t.replace(a, b))
        r = subprocess.run([sys.executable, "-I", os.path.join(root, "tr5", "test_tr5.py")], capture_output=True, text=True,
                           env={"PYTHONDONTWRITEBYTECODE": "1"})
        last = [l for l in r.stderr.strip().split("\n") if l.startswith(("OK", "FAILED"))]
        res = last[-1] if last else "形が読めない"
        red += res.startswith("FAILED")
        print(name, "→", res)
    print("赤", red, "/", len(MUTS))


if __name__ == "__main__":
    main()
