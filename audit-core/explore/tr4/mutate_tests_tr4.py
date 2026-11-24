# -*- coding: utf-8 -*-
"""便 TR4: 単体試験 test_tr4 が、判定と数の拾い方をわざと壊すと赤くなるかを見る(門は変異で赤くなることを確かめてから門と呼ぶ)。

使い方: python3 -I mutate_tests_tr4.py <作業用の空の folder>
tr4 の 3 file を作業用の folder に写し、1 か所ずつ壊して test_tr4 を走らせる。repo の file は書き換えない。
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = sys.argv[1]
MUTS = [
    ("judge_tr4.py", '                if got in _shown(d / s, k):\n                    out.append((item, per, "増減額"))', "                pass", "M1 増減額を見ない"),
    ("judge_tr4.py", "    return {int(round(y)), int(math.floor(y + 1e-9))}", "    return {int(round(y))}", "M2 切り捨てを見ない"),
    ("judge_tr4.py", '            if got in _shown(v / s, k):\n                out.append((item, per, "値"))',
     '            if (item, per) == ("売上高", "当期") and got in _shown(v / s, k):\n                out.append((item, per, "値"))', "M3 1 つの読みだけと比べる(TR0-1・TR3-1 の形)"),
    ("judge_tr4.py", "    got = int(round(abs(value) * 10 ** k))", "    got = int(round(value * 10 ** k))", "M4 符号を見る"),
    ("numbers_tr4.py", '            if "比" in seg[m.end():m.end() + 2]:\n                continue', "            pass", "M5 比べる字を期の字とする"),
    ("numbers_tr4.py", "            if any(s <= m.start() and m.end() <= e for s, e in spans):\n                continue", "            pass", "M6 当期純利益の当期を期の字とする"),
    ("numbers_tr4.py", 'NUM = re.compile(r"(?P<sign>[△▲+＋\\-−]?)', 'NUM = re.compile(r"(?P<sign>[△▲\\-−]?)', "M7 + の付いた数を拾わない"),
    ("numbers_tr4.py", 'unit = u.group(1) if u else (_paren_unit(head[j] if j < len(head) else "") or _paren_unit(label) or tunit)',
     "unit = u.group(1) if u else tunit", "M9 行の見出しの(人)を見ない"),
    ("numbers_tr4.py", '    if m.group("sign") in ("-", "−") and re.search(r"\\d$", before):\n        return True', "    pass", "M10 日付の -01 を数とする"),
    ("numbers_tr4.py", '        if k and k != want:\n            out.append(("期の字", w))', "        pass", "M11 期の食い違いを出さない"),
    ("numbers_tr4.py", '    if it and it != tag.get("項目"):\n        out.append(("項目の字", w))', "    pass", "M12 項目の食い違いを出さない"),
]


def main():
    red = 0
    for f, a, b, name in MUTS:
        d = os.path.join(WORK, "m")
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        for x in ("judge_tr4.py", "numbers_tr4.py", "test_tr4.py"):
            shutil.copy(os.path.join(HERE, x), d)
        p = os.path.join(d, f)
        with open(p, encoding="utf-8") as fh:
            t = fh.read()
        assert a in t, name
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(t.replace(a, b))
        r = subprocess.run([sys.executable, "-I", os.path.join(d, "test_tr4.py")], capture_output=True, text=True,
                           env={"PYTHONDONTWRITEBYTECODE": "1"})
        last = [l for l in r.stderr.strip().split("\n") if l.startswith(("OK", "FAILED"))]
        res = last[-1] if last else "形が読めない"
        red += res.startswith("FAILED")
        print(name, "→", res)
    print("赤", red, "/", len(MUTS))


if __name__ == "__main__":
    main()
