# -*- coding: utf-8 -*-
"""完走した run のログから**試験の本数を機械で取り出す**。通信しない。

なぜ要るか: 2026-10-14 に**同じ日に 2 回**、測った数を手で書き写す所で間違えた。
(1) 監査へ渡した依頼書に古い `pytest 1027` を残した。(2) 報告していた `1039` が
`tests/` だけの数で、`measure/tests/` の 96 本が入っていなかった。
C-1〜C-4 は json から読んでいるので 1 回も間違えていない。**間違えたのは手で書き写した
3 つの数だけ**なので、同じ仕組みを試験の本数にも掛ける。

使い方::  python3 -B measure/parse_suite_evidence.py <ログ> <出力の json>
出力の json を `tests/adapters/xbrl/test_p20.py` の `SuiteEvidenceTest` が文書と照合する。
"""

import io
import json
import os
import re
import sys

SECTION_RE = re.compile(r"^=== (.+?) ===$", re.M)
HEAD_RE = re.compile(r"^([0-9a-f]{7,40}) ", re.M)
PYTEST_RE = re.compile(r"^(\d+) passed in ", re.M)
RAN_RE = re.compile(r"^Ran (\d+) tests? in ", re.M)
PREDICTED_RE = re.compile(r"^predicted == actual: (\d+) 本 / 外れ: (\d+) 本", re.M)


def split_sections(text):
    """``=== 見出し ===`` で切った ``[(見出し, 本文)]``。見出しの前の分は ``""`` の鍵。"""

    marks = list(SECTION_RE.finditer(text))
    out = [("", text[: marks[0].start()] if marks else text)]
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((m.group(1), text[m.end():end]))
    return out


def _one(pattern, body, what, section):
    """**ちょうど 1 件**でなければ落ちる(0 件を「無い」で済ませず、2 件を黙って先勝ちにしない)。"""

    found = pattern.findall(body)
    if len(found) != 1:
        raise ValueError("%s が節 %r に %d 件(ちょうど 1 件であるべき)" % (what, section, len(found)))
    return found[0]


def parse(text):
    """ログ 1 本から数を取り出す。足りない・多い・赤が在れば**例外で落ちる**。"""

    if not text.strip():
        raise ValueError("ログが空")
    sections = dict(split_sections(text))
    titles = list(sections)

    def pick(keyword):
        hits = [t for t in titles if keyword in t]
        if len(hits) != 1:
            raise ValueError("見出しに %r を含む節が %d 件(ちょうど 1 件であるべき): %r"
                             % (keyword, len(hits), titles))
        return hits[0]

    if "FAILED" in text:
        raise ValueError("ログに FAILED が在る(赤を緑として記録しない)")

    head_title = pick("HEAD(この run の間")
    pytest_title = pick("pytest")
    discover_title = pick("discover")
    mut_title = pick("変異")

    head = _one(HEAD_RE, sections[head_title], "HEAD の sha", head_title)
    pytest_passed = int(_one(PYTEST_RE, sections[pytest_title], "pytest の passed", pytest_title))
    discover_ran = int(_one(RAN_RE, sections[discover_title], "discover の Ran", discover_title))
    mut_ran = int(_one(RAN_RE, sections[mut_title], "変異の Ran", mut_title))
    predicted, misses = _one(PREDICTED_RE, sections[mut_title], "変異の予測一致", mut_title)

    for title in (discover_title, mut_title):
        if not re.search(r"^OK$", sections[title], re.M):
            raise ValueError("節 %r に OK の行が無い" % (title,))

    return {
        "head": head,
        "pytest_passed": pytest_passed,
        "discover_ran": discover_ran,
        "mutation_test_methods": mut_ran,
        "mutation_predicted": int(predicted),
        "mutation_misses": int(misses),
    }


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    with io.open(argv[1], encoding="utf-8") as fh:
        out = parse(fh.read())
    os.makedirs(os.path.dirname(argv[2]), exist_ok=True)
    with io.open(argv[2], "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    for key in sorted(out):
        print("%-24s %s" % (key, out[key]))
    print("\n->", argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
