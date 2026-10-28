# -*- coding: utf-8 -*-
u"""既定の profile を P26 から P27 に切り替える(段 2)の封の門 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md を固定する。
型は P22 -> P26 の段 2 の封の門 tests/measure/test_xbrl_default_p26_seal.py に倣う(前例では封の門を封の次の便で足した。今回は封の commit は文書だけで、実装の便で足す)。

縛るもの: 人間の言葉(2026-10-27 と 2026-10-28)と「この封の commit 時点では DEFAULT_PROFILE = "P26" のまま」(封の commit の blob を git show で読む)・
判定の根拠(結果の門の別の関数で D の 9 小項目を記録 4 つから数え直しても『P27 を既定の候補として記録する』)・§0 の数(結果 docs/XBRL_P27_RESULT_2026-10-27.md の
門の中の表と、記録 regress97 の行から数え直した値に一致。新しく測った記録 default_p27 とも一致)・§1-2 の区分表(``git grep -c DEFAULT_PROFILE aeae608`` を門が数え直す)・
予測 S-1〜S-12 の行と外れ方と幅の算術・§4 の pin の遷移の一覧(``git grep -l -F <sha16> aeae608 -- tests`` を門が数え直す)・§5 の file と順序・
**封が実装より先であること**(封の commit の木で DEFAULT_PROFILE が P26 のまま・新しい file が無い、順序は git の commit の順で)・
評価用・調整用の docID と claim の id(N\\d{3}・T\\d{3})が封にも結果の文書にも 0 件・新しい門が過去の門の行頭の名前と P26 の段 2 の封の時点の sha16 を使わないこと。
**数は commit aeae608 の木から読む**(``git show aeae608:...`` / ``git grep ... aeae608``)。作業木の記録は段 2 の便で動かす(儀式の記録など)ので、封の数を作業木の
file に結ぶと段 2 の便で赤くなる。
**変数名について**: 過去の門が tests/measure の行頭の名前を数えるので、この門は engine の留めを定義する名前(P27 の封の門の ``RESERVED_PREFIXES`` の一覧)を行頭で定義しない。
"""
import glob
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

SEAL_REL = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SEAL_COMMIT = "87f83fd"
BASE = "aeae608"              # 評価用の結果の commit(R)。封の数はこの木の記録と文書
RESULT_P27_REL = "docs/XBRL_P27_RESULT_2026-10-27.md"
REGRESS_REL = "fixtures/xbrl/p27/regress97_2026-10-27.json"
DEFAULT_REC_REL = "fixtures/xbrl/default_p27_2026-10-28.json"
DEFAULT_DOC_REL = "docs/XBRL_DEFAULT_P27_RESULT_2026-10-28.md"
GATE_REL = "tests/measure/test_xbrl_default_p27_seal.py"
RESULT_GATE_REL = "tests/measure/test_xbrl_default_p27_result.py"
NEW_FILES = ("measure/xbrl_default_p27_2026-10-28.py", DEFAULT_REC_REL, DEFAULT_DOC_REL, RESULT_GATE_REL, GATE_REL, "fixtures/xbrl/ritual_2026-10-20_p26.json")
HEADINGS = (u"## §0 ", u"## §1 ", u"## §2 ", u"## §3 ", u"## §4 ", u"## §5 ")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS", "LATER_FINGERPRINT", "FINGERPRINT_",
                     "LATER_TARGET", "LATER_FROZEN", "FROZEN_BUNDLE_AT_SEAL", "TARGET_AT_SEAL", "ENGINE_AT_SEAL")
OLD_STAGE_SHA16 = "83025e9c" + "0525d08b"          # P26 の段 2 の封の時点の vocabulary.py の sha16。新しい門は持たない(P26 の段 2 の封の門 test_17)
STEP_NAMES = tuple(u"S-%d" % i for i in range(1, 13))


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def base_text(rel):
    return git("show", "%s:./%s" % (BASE, rel)).stdout


def seal_text(rel):
    return git("show", "%s:./%s" % (SEAL_COMMIT, rel)).stdout


def sec(t, start, end=None):
    i = t.index(start)
    j = t.index(end, i + len(start)) if end else len(t)
    return t[i:j]


def cells(line):
    return [c.strip() for c in line.strip().strip(u"|").split(u"|")]


def tokens(cell):
    return re.findall(r"\*\*([^*]+)\*\*", cell)


def num(s):
    return int(s.replace(u",", u"").replace(u"−", u"-"))


def rows_of(t):
    rows = {}
    for l in t.splitlines():
        m = re.match(r"\| \*\*(S-\d+)\*\* \| (.*) \| ([^|]*) \|$", l)
        if m:
            rows[m.group(1)] = (m.group(2), m.group(3).strip())
    return rows


def load_module(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def jload(p):
    return json.loads(text(p))


def grep_base(lit, pathspec):
    out = git("grep", "-l", "-F", lit, BASE, "--", pathspec).stdout.splitlines()
    return set(x[len(BASE) + 1:] for x in out)


def paths_after(block, start, end):
    i = block.index(start)
    j = block.index(end, i + 1) if end else len(block)
    return set(re.findall(r"`(tests/[A-Za-z0-9_./-]+\.py)`", block[i:j]))


# ---------------------------------------------------------------------------------------------------------------- 検査(封の字 t を受けて、壊した t で赤くなる)
def check_head(t):
    head = t.split(u"\n## §0 ")[0]
    for s in (u"**人間(2026-10-27)「価値を上げるためにも君に任せる 進めよう」", u"人間(2026-10-28)「君に任せるよ」", u"既定を P27 に替える(P27E ではない)。", u"commit `aeae608`",
              u"**この封の commit 時点では `DEFAULT_PROFILE = \"P26\"` のまま、`verify_document.py` の docstring も「= P20」のまま。**", u"0 USD・通信なし・鍵の値は読まない・席(LLM)は呼ばない。",
              u"評価用・調整用の AI の文・DB の応答(`~/.cache/audit-core/edinetdb-p27/` の下)を開いていない"):
        assert s in head, s
    for m in re.finditer(r"(?<![A-Za-z0-9])(S100[0-9A-Z]{4})(?![A-Za-z0-9])", t):
        raise AssertionError(u"封に docID の字が在る: " + m.group(1))
    assert not re.findall(r"(?<![A-Za-z0-9_-])[NT]\d{3}(?![0-9])", t), u"封に claim の id の字が在る"
    # 封の commit 時点の木で既定が P26 のまま
    voc = seal_text("adapters/xbrl/vocabulary.py")
    assert len(re.findall(r'(?m)^DEFAULT_PROFILE = "P26"$', voc)) == 1 and u'DEFAULT_PROFILE = "P27"' not in voc, u"封の commit 時点で既定が P26 でない"
    vd = seal_text("adapters/xbrl/verify_document.py")
    assert u"``--profile`` を省くと ``vocabulary.DEFAULT_PROFILE``(= P20。2026-10-14 の人間の決定)。" in vd, u"封の commit 時点で docstring が『= P20』でない"


def check_headings(t):
    pos = [t.index(h) for h in HEADINGS]
    assert pos == sorted(pos), u"章の順が違う"
    assert len(re.findall(r"(?m)^## ", t)) == 6, u"章が 6 つでない"
    for h in (u"### §0-1 ", u"### §0-2 ", u"### §0-3 ", u"### §0-4 ", u"### §1-1 ", u"### §1-2 ", u"### §1-3 ", u"### §1-4 "):
        assert h in t, h


def check_basis(t, sentences):
    u"""§0-1: 判定の根拠。結果の門の別の関数で D の 9 小項目を数え直した判定の字がそのまま封に在る。"""
    b = sec(t, u"### §0-1 ", u"### §0-2 ")
    assert u"「P27 を『既定の候補』として 記録する」" in b, u"封の判定の字が結果の表の字と違う"
    assert sentences[1] == u"判定(P27): P27 を「既定の候補」として記録する。", sentences
    assert sentences[0] == u"判定(P27E): P27E を「外部の数の文に使う profile」として採用する。", sentences
    assert u"**P27E は既定の候補にしない**" in b


def check_d_numbers(t, drows):
    u"""§0-1 の D の 9 小項目の数を、結果の門が求めた行(drows)から。"""
    b = sec(t, u"### §0-1 ", u"### §0-2 ")
    vals = [cells(r)[3] for r in drows]
    want = [u"0.0%", u"0", u"−4", u"1", u"97 / 97", u"4,371", u"433", u"2,194", u"250"]
    assert [v.replace(u"-", u"−") for v in vals] == want, (vals, want)
    for s in (u"D-1a T8_REL の通した率 P27 **0.0%**(≤ 2%)", u"D-1b T1_VALUE の通した行 P27 **0**", u"D-3 無改変の VALUE_MISMATCH の行 P27 − P26 **−4**(≤ 0)",
              u"合わせた側が道具の行 **1**(≤ 3)", u"D-5 旗が偽の P22・P26 の byte 一致 **97 / 97**", u"手元の 67 の P27 の GROUNDED **4,371**・VALUE_MISMATCH **433**",
              u"新しい標本 30 の **2,194**・**250**(P26 と同じ)"):
        assert s in b, s


def parse_blocks(doc):
    return dict((m.group(1), m.group(2).split(u"\n")) for m in re.finditer(r"<!-- 門:start (\S+) -->\n(.*?)\n<!-- 門:end -->", doc, re.S))


def check_eval_table(t, blocks):
    u"""§0-2 の評価用の表を、結果の文書の門の中の表(記録から作られ、結果の門が縛る)から。"""
    b = sec(t, u"### §0-2 ", u"### §0-3 ")
    state = [cells(l) for l in blocks["state"][2:]]
    by = dict((r[0], r) for r in state)
    exp = u"| GROUNDED / VALUE_MISMATCH / UNVERIFIABLE / POINTER_NOT_FOUND | " + u" | ".join(
        (u"**%s**" if p == "P27" else u"%s") % u" / ".join(by[p][1:5]) for p in ("P22", "P26", "P27", "P27E")) + u" |"
    assert exp in b, exp
    exp = u"| VALUE_MISMATCH の率 | " + u" | ".join((u"**%s**" if p == "P27" else u"%s") % by[p][6] for p in ("P22", "P26", "P27", "P27E")) + u" |"
    assert exp in b, exp
    dist = [cells(l) for l in blocks["注入-分布"][2:]]
    allrows = dict(((r[0], r[1]), r) for r in dist if r[2] == u"全体")

    def pct(s):
        return u"%g%%" % float(s.rstrip(u"%"))
    prof = ("P22", "P26", "P27", "P27E")
    t8 = [allrows[("T8_REL", p)] for p in prof]
    t1 = [allrows[("T1_VALUE", p)] for p in prof]
    assert [r[3] for r in t8] == [u"87"] * 4 and [r[3] for r in t1] == [u"7"] * 4
    assert u"T8_REL(4 profile で対応が付く 87): 通した | 27(31.0%) | 27(31.0%) | **0(0.0%)** | 0 |" in b
    assert [(r[4], r[9 + 1]) for r in t8] == [(u"27", u"31.0%"), (u"27", u"31.0%"), (u"0", u"0.0%"), (u"0", u"0.0%")], t8
    exp = u"| T8_REL: 名指して原本の値を返した | " + u" | ".join((u"**%s(%s)**" if p == "P27" else u"%s(%s)") % (r[5], r[9]) for p, r in zip(prof, t8)) + u" |"
    assert exp in b, exp
    exp = u"| T8_REL: 名指したが別の値 / 止めたが名指さない | " + u" | ".join((u"**%s / %s**" if p == "P27" else u"%s / %s") % (r[6], r[7]) for p, r in zip(prof, t8)) + u" |"
    assert exp in b, exp
    exp = u"| T1_VALUE(対応 7): 通した / 名指して原本の値 | " + u" | ".join(
        (u"**%s / %s(%s)**" if p == "P27" else u"%s / %s(%s)") % (r[4], r[5], pct(r[9])) for p, r in zip(prof, t1)) + u" |"
    exp = exp.replace(u" | 0 / 5(71.4%) |", u" | 0 / 5 |")
    assert exp in b or exp.replace(u"| 0 / 5(71.4%)", u"| 0 / 5") in b, exp
    moved = [cells(l) for l in blocks["動いた行"][2:] if cells(l)[0] == u"P26 → P27"]
    assert sum(int(r[4]) for r in moved if r[1] == u"state か reason") == 23 and sum(int(r[4]) for r in moved if r[1] == u"pointer だけ") == 2, moved
    for s in (u"GROUNDED → UNVERIFIABLE / other_frame **1**・GROUNDED のまま pointer だけ **2**", u"POINTER_NOT_FOUND / no_element → UNVERIFIABLE / per_unit_counter **7**",
              u"UNVERIFIABLE / ambiguous(elements) → POINTER_NOT_FOUND / no_element **4**", u"UNVERIFIABLE / ambiguous(elements) → UNVERIFIABLE / no_subject **7**",
              u"VALUE_MISMATCH → POINTER_NOT_FOUND / no_same_value **1**・VALUE_MISMATCH → POINTER_NOT_FOUND / other_concept **1**・VALUE_MISMATCH → UNVERIFIABLE / per_unit_counter **2**"):
        assert s in b, s
    # 動いた行の表の数は結果の文書の表の行(7 = 1 + 6 など)と合う
    d = dict(((r[2], r[3]), int(r[4])) for r in moved)
    assert d[(u"GROUNDED", u"UNVERIFIABLE / other_frame")] == 1 and d[(u"UNVERIFIABLE / ambiguous(elements)", u"POINTER_NOT_FOUND / no_element")] == 4
    assert d[(u"POINTER_NOT_FOUND / no_element", u"UNVERIFIABLE / per_unit_counter")] + d[(u"POINTER_NOT_FOUND / no_element(unit not in XBRL)", u"UNVERIFIABLE / per_unit_counter")] == 7
    assert d[(u"UNVERIFIABLE / ambiguous(elements)", u"UNVERIFIABLE / no_subject")] == 7


def regress_numbers(reg):
    u"""regress97 の記録の行から §0-3 の数を数え直す(記録の集計の欄は読まない)。"""
    out = {}
    for pop in (u"手元の 67", u"新しい標本 30"):
        docs = [d for d in reg[u"書類"] if d[u"標本"] == pop]
        p26 = [0, 0, 0, 0]
        p27 = [0, 0, 0, 0]
        for d in docs:
            for i, s in enumerate(("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")):
                p26[i] += d[u"4 state"]["P26"][s]
                p27[i] += d[u"4 state"]["P27"][s]
        moved = reg[u"動いた行"][pop][u"P26 → P27"]
        dirs = {}
        reasons = {}
        for m in moved:
            k = u"%s → %s" % (m[u"前"]["state"], m[u"後"]["state"])
            dirs[k] = dirs.get(k, 0) + 1
            r = (m[u"前"]["reason"], m[u"後"]["reason"])
            reasons[r] = reasons.get(r, 0) + 1
        out[pop] = {"docs": len(docs), "claims": sum(sum(d[u"4 state"]["P27"].values()) for d in docs), "p26": p26, "p27": p27, "moved": len(moved), "dirs": dirs, "reasons": reasons,
                    "moved_docs": len(set(m["docID"] for m in moved))}
    return out


def check_regress(t, reg):
    b = sec(t, u"### §0-3 ", u"### §0-4 ")
    R = regress_numbers(reg)
    a, c = R[u"手元の 67"], R[u"新しい標本 30"]
    assert (a["docs"], a["claims"], c["docs"], c["claims"]) == (67, 7799, 30, 3923)
    f = lambda x: format(x, ",")
    for s in (u"手元の 67 書類(claim 7,799)の 4 state、P26 → **P27**: GROUNDED %s → **%s**・VALUE_MISMATCH %s → **%s**・UNVERIFIABLE %s → **%s**・POINTER_NOT_FOUND %s → **%s**" % (
            f(a["p26"][0]), f(a["p27"][0]), f(a["p26"][1]), f(a["p27"][1]), f(a["p26"][2]), f(a["p27"][2]), f(a["p26"][3]), f(a["p27"][3])),
              u"動いた行 **%d**" % a["moved"],
              u"POINTER_NOT_FOUND → UNVERIFIABLE **%d**・UNVERIFIABLE → POINTER_NOT_FOUND **%d**" % (a["dirs"]["POINTER_NOT_FOUND → UNVERIFIABLE"], a["dirs"]["UNVERIFIABLE → POINTER_NOT_FOUND"]),
              u"新しい標本 30 書類(claim 3,923)、P26 → **P27**: GROUNDED %s → **%s**・VALUE_MISMATCH %s → **%s**・UNVERIFIABLE %s → **%s**・POINTER_NOT_FOUND %s → **%s**" % (
                  f(c["p26"][0]), f(c["p27"][0]), f(c["p26"][1]), f(c["p27"][1]), f(c["p26"][2]), f(c["p27"][2]), f(c["p26"][3]), f(c["p27"][3])),
              u"動いた行 **%d**(POINTER_NOT_FOUND → UNVERIFIABLE **%d**・UNVERIFIABLE → POINTER_NOT_FOUND **%d**)" % (
                  c["moved"], c["dirs"]["POINTER_NOT_FOUND → UNVERIFIABLE"], c["dirs"]["UNVERIFIABLE → POINTER_NOT_FOUND"])):
        assert s in b, s
    assert set(a["dirs"]) == set(c["dirs"]) == {"POINTER_NOT_FOUND → UNVERIFIABLE", "UNVERIFIABLE → POINTER_NOT_FOUND"}
    # reason の内訳(67 書類の行)
    r67 = a["reasons"]
    g = lambda x, y: sum(v for (p, q), v in r67.items() if p == x and q == y)
    assert (g("no_element", "per_unit_counter"), g("no_element(unit not in XBRL)", "per_unit_counter"), g("no_same_value", "target_or_plan"),
            g("no_element(ratio without fact)", "target_or_plan"), g("no_element", "target_or_plan"), g("ambiguous(elements)", "no_element")) == (11, 6, 3, 3, 2, 3), r67
    for s in (u"`no_element` → `per_unit_counter` 11・`no_element(unit not in XBRL)` → `per_unit_counter` 6・`no_same_value` → `target_or_plan` 3・`no_element(ratio without fact)` → `target_or_plan` 3・"
              u"`no_element` → `target_or_plan` 2・`ambiguous(elements)` → `no_element` 3(書類は %d)" % a["moved_docs"],
              u"(書類は %d)" % c["moved_docs"]):
        assert s in b, s
    # 規則ごとに当たった claim と P27E を既定にしない数(81・24)
    p27e = reg[u"動いた行"]
    for pop, n in ((u"手元の 67", 81), (u"新しい標本 30", 24)):
        rows = p27e[pop][u"P27 → P27E"]
        assert sum(1 for m in rows if m[u"前"]["reason"] == "no_same_value" and m[u"後"]["state"] == "VALUE_MISMATCH") == n, pop
    assert u"67 書類で **81**・30 書類で **24**" in b
    assert u"旗が偽の P22・P26 は封の時点の engine(`29e6d0a`)と byte 一致 **97 / 97**" in b
    return R


def check_prototype_arithmetic(t):
    b = sec(t, u"### §0-4 ", u"## §1 ")
    assert u"**81 failed, 3228 passed, 34 skipped**(赤 81 本・**29 file**)" in b and u"**16 failed, 1487 passed, 1 skipped**" in b and u"合計 **97**" in b
    assert 37 + 17 + 9 + 18 == 81 and 81 + 16 == 97, u"試作の赤の内訳の足し算"
    assert u"37 + 17 + 9 + 18 = 81" in b
    for s in (u"**増えた赤は 7 本**", u"`PACKAGING` 30 passed", u"`CUSTOMER_REPORT` 3 failed / 33 passed", u"`RITUAL` 6 failed / 31 passed"):
        assert s in b, s
    assert u"cache(`~/.cache/audit-core/edinet/` 281・`edinet-fresh-2026-10-21/` 40)" in b


def check_engine_section(t):
    b = sec(t, u"### §1-1 ", u"### §1-2 ")
    for s in (u"`DEFAULT_PROFILE = \"P26\"` を `DEFAULT_PROFILE = \"P27\"` に(1 行)", u"**+≤ 8/−1**", u"**P16・P20・P21・P22・P26 の注記は 1 字も消さない。**",
              u"`PROFILES` の行・P27・P27E の定義の行は変えない", u"**+1/−1**", u"**実行の字(`profile_name or V.DEFAULT_PROFILE`・argparse の help)は変えない**",
              u"**他の engine の行は 0。**", u"P27E の定義・旗の既定値(全部 `False`)・P16〜P27E を明示した呼び出しと試験の数は 1 つも変えない。"):
        assert s in b, s
    assert u"いまは P27。P20 → P21 → P22 → P26 → P27 の履歴と根拠は vocabulary.py の注記。この行は 2026-10-28 の人間の委任「君に任せるよ」で直した" in b


def grep_groups(per):
    groups = {"engine": ("adapters/xbrl/",), "frozen_bundle": ("fixtures/frozen_bundle_sha.py",), "tests/adapters/xbrl": ("tests/adapters/xbrl/",),
              "tests/measure": ("tests/measure/",), "measure": ("measure/",), "fixtures/xbrl": ("fixtures/xbrl/",), "docs": ("docs/",)}
    got = {}
    for name, prefixes in groups.items():
        files = [p for p in per if any(p.startswith(x) for x in prefixes)]
        got[name] = (len(files), sum(per[p] for p in files))
    return got


def check_table_1_2(t, per):
    b = sec(t, u"### §1-2 ", u"### §1-3")
    got = grep_groups(per)
    assert sum(v[0] for v in got.values()) == len(per)
    assert u"`git grep -c DEFAULT_PROFILE aeae608 -- .` で **%d file・%d か所**を数えた" % (len(per), sum(per.values())) in t, (len(per), sum(per.values()))
    rows = [cells(l) for l in re.findall(r"(?m)^\|(?!---)(?! 区分).*$", b)]
    assert len(rows) == 7, len(rows)
    names = {u"engine": "engine", u"frozen_bundle": "frozen_bundle", u"tests/adapters/xbrl": "tests/adapters/xbrl", u"tests/measure": "tests/measure",
             u"measure": "measure", u"fixtures/xbrl": "fixtures/xbrl", u"docs": "docs"}
    for row in rows:
        nfile = int(re.match(r"(\d+) file", row[1].replace(u"`fixtures/frozen_bundle_sha.py` ", u"")).group(1))
        assert (nfile, int(row[2])) == got[names[row[0]]], (row[0], nfile, row[2], got[names[row[0]]])
    assert (per["adapters/xbrl/vocabulary.py"], per["adapters/xbrl/verify_document.py"], per["adapters/xbrl/run.py"]) == (3, 3, 3)
    for s in (u"`vocabulary.py`(3)の 1 行と注記を**直す**", u"`verify_document.py`(3)の docstring の 1 行を**直す**、実行の字 2 は残す", u"`run.py`(3)は `V.DEFAULT_PROFILE` を引く字で名前を書かない = 残す"):
        assert s in b, s
    for rel in ("README.md", "README.en.md"):
        assert "DEFAULT_PROFILE" not in base_text(rel) and "P26" in base_text(rel)
    facts = base_text("docs/FACTS_FOR_BUYERS_2026-10-20.md")
    assert (facts.count("P26"), facts.count("P27")) == (0, 0)
    assert u"`docs/FACTS_FOR_BUYERS_2026-10-20.md` は P26・P27 の字が 0 = **触らない**" in b
    assert u'if V.DEFAULT_PROFILE != "P26":' in base_text("measure/ritual_2026-10-20.py")
    assert git("cat-file", "-e", "%s:./fixtures/xbrl/ritual_2026-10-20_p22.json" % BASE).returncode == 0
    assert git("cat-file", "-e", "%s:./fixtures/xbrl/ritual_2026-10-20_p26.json" % BASE).returncode != 0


def per_file_counts():
    per = {}
    for line in git("grep", "-c", "DEFAULT_PROFILE", BASE, "--", ".").stdout.splitlines():
        path, _, cnt = line.rpartition(":")
        per[path[len(BASE) + 1:]] = int(cnt)
    return per


def check_predictions(t):
    rows = rows_of(t)
    assert list(rows) == list(STEP_NAMES), list(rows)
    for k, (pred, fail) in rows.items():
        assert len(fail.strip()) >= 2, (k, u"外れ方が空")
        assert len(tokens(u"| " + pred)) >= 1, (k, u"太字の数が無い")
    s = dict((k, tokens(v[0])) for k, v in rows.items())
    assert s["S-1"] == [u"0 / 67", u"0 / 30", u"97 / 97"]
    assert s["S-2"][:7] == [u"4,371", u"433", u"1,601", u"1,394", u"28", u"25", u"3"] and 4371 + 433 + 1601 + 1394 == 7799 and 25 + 3 == 28
    assert s["S-3"][:7] == [u"2,194", u"250", u"787", u"692", u"15", u"14", u"1"] and 2194 + 250 + 787 + 692 == 3923 and 14 + 1 == 15
    assert s["S-4"][:3] == [u"2 / 243 = 0.8%", u"210 / 243 = 86.4%", u"31"] and 2 + 210 + 31 == 243 and 340 + 25 + 33 + 14 == 412
    assert s["S-5"] == [u"433", u"1,773", u"145", u"1,077", u"4,371"] and 433 + 1773 + 145 + 1077 + 4371 == 7799
    assert (1773 - 1775, 145 - 151, 1077 - 1069) == (-2, -6, 8), u"S-5 の増減(−2・−6・+8)"
    assert s["S-6"] == [u"0 / 485", u"480", u"5", u"0 / 64", u"0", u"0"] and 480 + 5 == 485
    assert s["S-7"] == [u"≤ 8", u"1", u"1", u"1", u"16", u"37"]
    assert s["S-8"][:6] == [u"81 本", u"29 file", u"16 本", u"11 file", u"97", u"98〜105"] and 98 > 97
    assert s["S-9"] == [u"7 本"] and s["S-10"] == [u"0"] and s["S-11"] == [u"232", u"232", u"234", u"0"]
    assert s["S-12"] == [u"「P27 を既定の候補として記録する」"]
    assert [x for x in s["S-8"][-5:]] == [u"2", u"7", u"3", u"0", u"0"], s["S-8"]


def check_pin_lists(t):
    b = sec(t, u"## §4 ", u"## §5")
    a_set = paths_after(b, u"**(a) ", u"**(a′) ")
    a2_set = paths_after(b, u"**(a′) ", u"**(b) ")
    b_set = paths_after(b, u"**(b) ", u"**(c) ")
    c_set = paths_after(b, u"**(c) ", u"**(d) ")
    e_set = paths_after(b, u"**(e) ", u"**(f) ")
    assert a_set == grep_base("85896a67913ce1e7", "tests"), u"(a) の一覧が git grep と違う"
    assert a2_set == grep_base("67e7639de3f5f2ad", "tests"), u"(a′) の一覧が git grep と違う"
    assert b_set == grep_base("0e51211a8aed2151", "tests"), u"(b) の一覧が git grep と違う"
    assert c_set == grep_base("29fd733c8988164a", "tests"), u"(c) の一覧が git grep と違う"
    assert grep_base("29fd733c8988164a", ".") == c_set | set(["fixtures/frozen_bundle_sha.py"])
    assert (len(a_set), len(a2_set), len(b_set), len(c_set)) == (26, 14, 6, 4)
    assert b_set <= a_set and c_set <= a_set
    assert len(a_set & a2_set) == 12 and a2_set - a_set == set(["tests/measure/test_xbrl_role_swap_result.py", "tests/measure/test_xbrl_verify_inventory.py"]), sorted(a2_set - a_set)
    assert all(p.startswith("tests/measure/") for p in a_set | a2_set)
    assert e_set == grep_base("DEFAULT_PROFILE", "tests/adapters/xbrl") and len(e_set) == 11
    for s in (u"**(a) `adapters/xbrl/vocabulary.py` の sha16 `85896a67913ce1e7` を字で留める門 26 本**", u"**(a′) `adapters/xbrl/verify_document.py` の sha16 `67e7639de3f5f2ad` を字で留める門 14 本**",
              u"`measure/xbrl_customer_report_fix_2026-10-21.py` の `UNTOUCHED_SHA16`", u"**(b) 束ねた指紋 `adapter_xbrl_py_sha256` の `0e51211a8aed2151…` を字で留める門 6 本**",
              u"**(c) frozen_bundle の世代 `29fd733c8988164a…` を字で留める所**", u"**(d) 既定の字だけで赤になる `tests/measure`**", u"**(e) 既定の字を見る `tests/adapters/xbrl` 11 file**",
              u"**(f) 重い走らせ直しだけで赤になる 7 本**", u"**(g) 軽い門で赤になる「既定を前提に走らせ直す」所**", u"**(h) 新しい門の名前**",
              u"**(i) axis3** の `LATER_ENGINE_COMMITS` に段 2 の commit を宣言するのは次の便", u"**(j) P27 の段 2 の門 5 本**"):
        assert s in b, s
    # (d) は sha の字を持たず既定の字を持つ。(a)(a′) の外
    nf = "tests/measure/test_xbrl_naming_fix_result.py"
    assert nf not in a_set and "DEFAULT_PROFILE" in base_text(nf)
    # (f) の 7 本の file と環境変数(実物)
    f = sec(b, u"**(f) ", u"**(g) ")
    for rel in ("test_xbrl_customer_report_result", "test_xbrl_customer_report_fix_result", "test_xbrl_default_p26_result", "test_xbrl_fresh_result", "test_xbrl_period_bind_result", "test_xbrl_ritual_result"):
        assert rel + ".py" in f, rel
        assert git("cat-file", "-e", "%s:./tests/measure/%s.py" % (BASE, rel)).returncode == 0, rel
    for var in ("AUDIT_CORE_CUSTOMER_REPORT", "AUDIT_CORE_CUSTOMER_REPORT_FIX", "AUDIT_CORE_DEFAULT_P26", "AUDIT_CORE_FRESH", "AUDIT_CORE_PERIOD_BIND", "AUDIT_CORE_RITUAL"):
        assert u"`%s=1`" % var in f or u"`%s=1`" % var in f.replace(u"RITUAL=1`", u"RITUAL=1`"), var
        assert grep_base(var, "tests/measure"), var
    assert f.count(u"の同名") == 3 and f.count(u"`RerunTest.test_heavy_everything_matches_the_record`") == 1 and u"`RerunTest.test_heavy_stage2_default_matches_the_record`" in f
    assert u"`RerunHeavyTest.test_4`・`test_6`" in f and 1 + 3 + 1 + 2 == 7
    # 既存の門が行頭の名前を数えること(新しい門の名前の制約)の根拠
    assert re.search(r"(?m)^ENGINE_LATER = \{", base_text("tests/measure/test_xbrl_lastbranch_seal.py"))
    assert u"RESERVED_PREFIXES" in base_text("tests/measure/test_xbrl_p27_seal.py")
    assert OLD_STAGE_SHA16 in b


def check_order_text(t):
    b = sec(t, u"## §5 ")
    first = b[:b.index(u"\n順序:")]
    toks = [u"`adapters/xbrl/vocabulary.py`", u"`adapters/xbrl/verify_document.py`", u"`measure/ritual_2026-10-20.py`", u"`fixtures/xbrl/ritual_2026-10-20.json`", u"`fixtures/xbrl/ritual_2026-10-20_p26.json`",
            u"`README.md`", u"`README.en.md`", u"`docs/XBRL_RITUAL_RESULT_2026-10-20.md`", u"`measure/xbrl_default_p26_2026-10-23.py`", u"`measure/xbrl_default_p27_2026-10-28.py`",
            u"`fixtures/xbrl/default_p27_2026-10-28.json`", u"`docs/XBRL_DEFAULT_P27_RESULT_2026-10-28.md`", u"`tests/measure/test_xbrl_default_p27_seal.py`",
            u"`tests/measure/test_xbrl_default_p27_result.py`", u"`tests/measure/test_xbrl_fresh_seal.py`", u"`measure/suite_coverage_2026-10-16.py --write`", u"`fixtures/frozen_bundle_sha.py`"]
    pos = []
    for tk in toks:
        assert first.count(tk) >= 1, tk
        pos.append(first.index(tk))
    assert pos == sorted(pos), u"file 一覧の順が変わった"
    order = b[b.index(u"\n順序:"):]
    assert u"評価用の結果の commit(`aeae608` = R)→ **この封を commit(文書だけ。封の門は実装の便)** → 段 2 実装(別席。`measure/` と試験と記録と文書)→ 凍結(sha256 の一覧)→ 独立監査(`step-auditor`)GO → commit → "\
           u"axis3 の `LATER_ENGINE_COMMITS` に段 2 の commit を宣言(次の便)" in order
    assert u"`281 → 281`" not in order and u"**281 → 281**" in order and u"**40 → 40**" in order


def rows_ok(t):
    check_head(t)
    check_headings(t)
    check_predictions(t)
    check_engine_section(t)
    check_pin_lists(t)
    check_order_text(t)
    check_prototype_arithmetic(t)


# ---------------------------------------------------------------------------------------------------------------- 試験
class SealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)
        cls.reg = jload(os.path.join(ROOT, REGRESS_REL))
        cls.per = per_file_counts()
        cls.rd = load_module("tests/measure/test_xbrl_default_p27_result.py", "default_p27_result_gate_for_seal_gate")
        cls.dec, cls.sentences = cls.rd.eval_decision()
        cls.p27doc_blocks = parse_blocks(base_text(RESULT_P27_REL))

    def test_1_head_quotes_the_human_and_does_not_switch_yet(self):
        check_head(self.t)

    def test_2_section_headings_are_the_six_in_order(self):
        check_headings(self.t)

    def test_3_the_judgement_is_recomputed_from_the_records_and_is_p27(self):
        self.assertTrue(self.dec["default_P27"] and self.dec["adopt_P27E"])
        check_basis(self.t, self.sentences)
        self.assertEqual(len(self.dec["drows"]), 9)

    def test_4_section_0_numbers_equal_the_records(self):
        check_d_numbers(self.t, self.dec["drows"])
        check_eval_table(self.t, self.p27doc_blocks)
        R = check_regress(self.t, self.reg)
        # 新しく測った記録(default_p27)があれば、97 書類の 4 state と動いた行の数が封と同じ
        p = os.path.join(ROOT, DEFAULT_REC_REL)
        if os.path.exists(p):
            rec = jload(p)
            for pop, key in ((u"手元の 67", u"S2"), (u"新しい標本 30", u"S3")):
                self.assertEqual(rec[key][u"既定の 4 state"], dict(zip(("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"), R[pop]["p27"])))
                self.assertEqual(rec[key][u"P26 の 4 state"], dict(zip(("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"), R[pop]["p26"])))
                self.assertEqual(rec[key][u"既定と P26 で state の違う行"], R[pop]["moved"])

    def test_5_section_1_engine_is_one_line_and_a_docstring_line(self):
        check_engine_section(self.t)
        # 封の commit の木で、run.py は V.DEFAULT_PROFILE を引き、名前を書かない
        run = seal_text("adapters/xbrl/run.py")
        self.assertIn("V.DEFAULT_PROFILE", run)
        self.assertNotIn('"P26"', run)

    def test_6_section_1_2_table_equals_the_grep_at_the_base_commit(self):
        check_table_1_2(self.t, self.per)

    def test_7_hum_no_human_item_remains_and_the_docstring_was_p20_at_the_seal(self):
        b = sec(self.t, u"### §1-3 ", u"### §1-4 ")
        self.assertIn(u"**無い。**", b)
        vd = seal_text("adapters/xbrl/verify_document.py")
        self.assertEqual(vd.count(u"= P20。2026-10-14 の人間の決定"), 1)
        # 作業木の docstring は封の字に直った行(宣言された遷移)か、まだ P20 のまま(封の commit 直後)
        now = text(os.path.join(ROOT, "adapters", "xbrl", "verify_document.py"))
        later = u"いまは P27。P20 → P21 → P22 → P26 → P27 の履歴と根拠は vocabulary.py の注記。この行は 2026-10-28 の人間の委任「君に任せるよ」で直した"
        self.assertTrue(later in now or u"= P20。2026-10-14 の人間の決定" in now)

    def test_8_the_human_confirmation_points_are_listed(self):
        b = sec(self.t, u"### §1-4 ", u"## §2 ")
        for s in (u"**承認の範囲(「君に任せるよ」の読み)**", u"**DECISION_LOG**", u"**`verify_document.py` の docstring**", u"**P27E を既定にしない理由**", u"**読み手の限界**",
                  u"D-025", u"D-024"):
            self.assertIn(s, b, s)
        self.assertEqual(len(re.findall(r"(?m)^\d+\. \*\*", b)), 5)
        # D-024 は作業木の未 commit の差分(封の commit 時点)。aeae608 の木に D-024 は無い
        self.assertNotIn("D-024", git("show", "%s:./../docs/DECISION_LOG.md" % BASE).stdout)

    def test_9_twelve_predictions_each_with_a_way_to_fail(self):
        check_predictions(self.t)
        rows = rows_of(self.t)
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(v[1] for v in rows.values()))

    def test_10_prediction_numbers_equal_the_records(self):
        u"""S-1〜S-7・S-10・S-11 の数を、封の commit の木の記録・文書から(新しい記録が在れば、それとも)。"""
        reg = regress_numbers(self.reg)
        rows = rows_of(self.t)
        s2, s3 = tokens(rows["S-2"][0]), tokens(rows["S-3"][0])
        self.assertEqual([num(x) for x in s2[:4]], reg[u"手元の 67"]["p27"])
        self.assertEqual([num(x) for x in s3[:4]], reg[u"新しい標本 30"]["p27"])
        self.assertEqual(num(s2[4]), reg[u"手元の 67"]["moved"])
        self.assertEqual(num(s3[4]), reg[u"新しい標本 30"]["moved"])
        # S-4: 儀式の P26 の記録(aeae608)の数
        r26 = json.loads(git("show", "%s:./fixtures/xbrl/ritual_2026-10-20.json" % BASE).stdout)
        self.assertEqual((r26[u"通した"][u"字"], r26[u"止めた"][u"字"]), (u"2 / 243 = 0.8%", u"210 / 243 = 86.4%"))
        st = r26[u"素の書類"][u"state の分布"]
        self.assertEqual((st["GROUNDED"], st["POINTER_NOT_FOUND"], st["UNVERIFIABLE"], st["VALUE_MISMATCH"]), (340, 27, 31, 14))
        self.assertIn(u"P26 の記録 340 / 27 / 31 / 14", rows["S-4"][0])
        # S-5: P26 の報告形は customer_report の記録(段 2 の便で動かさない記録)の数でなく、封が試作から書いた字(433 / 1,775 / 151 / 1,069 / 4,371)
        self.assertIn(u"P26 の節は 433 / 1,775 / 151 / 1,069 / 4,371", rows["S-5"][0])
        # S-6: P26 の記録 p26_2026-10-21.json の Q3 の P26 の欄(穴 B 485 行・段 2 192 行)
        q3 = json.loads(git("show", "%s:./fixtures/xbrl/p26_2026-10-21.json" % BASE).stdout)[u"Q3"]
        self.assertEqual((len(q3[u"穴 B"][u"行"]), len(q3[u"段 2"][u"行"])), (485, 192))
        self.assertEqual(q3[u"穴 B"][u"集計"][u"P26 で通した(GROUNDED のまま)"][u"件"], 0)
        # S-7 の「束ねた指紋が動く」前の値(封の commit 時点)
        fz = base_text("fixtures/frozen_bundle_sha.py")
        self.assertEqual(re.findall(r"(?m)^FROZEN_COUNT = (\d+)$", fz), ["37"])
        self.assertEqual(re.findall(r'\("([0-9a-f]{64})",\n', fz)[-1][:16], "29fd733c8988164a")
        # S-11: aeae608 の木の試験 file の数
        n = sum(1 for p in git("ls-tree", "-r", "--name-only", BASE).stdout.splitlines() if os.path.basename(p).startswith("test_") and p.endswith(".py")
                and not any(x in p for x in (".git/", "node_modules", "__pycache__", ".pytest_cache")))
        self.assertEqual(n, 232)

    def test_11_limits_are_written(self):
        b = sec(self.t, u"## §3 ", u"## §4 ")
        for s in (u"**C1(1 株当たりの窓)の当たってしまう例**", u"**C3(先の決算期)の当たってしまう例**", u"**A(書かれた桁で照合する)の代価**", u"**評価用で P26 → P27 で GROUNDED を離れた 1 行**",
                  u"**読む行は 2 行・1 社**", u"**97 書類では GROUNDED・VALUE_MISMATCH の数が P26 と 1 行も変わらない**", u"**文2(DB の値 = 翌期の有報の前期の欄)はこの標本で起きえない**",
                  u"書き手も読み手も同じ model。", u"試作の赤の数(S-8)と重い走らせ直し(S-9)は試作の clone の実測で、記録に無い。"):
            self.assertIn(s, b, s)
        # 限界の数: C1 の窓に入った claim 12(67 で 5・30 で 7)は regress97 の記録から
        self.assertTrue(u"**5**・**7**" in sec(self.t, u"### §0-3 ", u"### §0-4 "))

    def test_12_new_gates_follow_the_naming_rules(self):
        for rel in (GATE_REL, RESULT_GATE_REL):
            p = os.path.join(ROOT, rel)
            if not os.path.exists(p):
                continue
            body = text(p)
            for name in RESERVED_PREFIXES:
                self.assertNotRegex(body, r"(?m)^%s" % re.escape(name), u"%s が行頭で %s を定義している" % (rel, name))
            self.assertNotIn(OLD_STAGE_SHA16, body, rel)

    def test_13_old_pin_set_only_grows_by_the_named_new_gates(self):
        u"""作業木で vocabulary.py の封の commit 時点の sha16 を字で持つ tests の file は、aeae608 の 26 本 + 結果の門が引用するだけの file だけ。"""
        base = grep_base("85896a67913ce1e7", "tests")
        live = set()
        for p in glob.glob(os.path.join(ROOT, "tests", "**", "*.py"), recursive=True):
            if "85896a67913ce1e7" in text(p):
                live.add(os.path.relpath(p, ROOT))
        self.assertTrue(base <= live, sorted(base - live))
        self.assertTrue(live - base <= set([GATE_REL]), sorted(live - base))

    def test_14_file_list_and_order(self):
        check_order_text(self.t)

    def test_15_pin_lists_equal_the_git_grep_at_the_base_commit(self):
        check_pin_lists(self.t)


class OrderTest(unittest.TestCase):
    u"""順序は git の commit の順で(file の有無でなく)。"""

    def test_20_the_seal_follows_the_base_commit_and_precedes_every_later_file(self):
        base = git("log", "--diff-filter=A", "--format=%H", "--", SEAL_REL).stdout.split()
        self.assertTrue(base, u"封が履歴に無い")
        seal = base[-1]
        self.assertTrue(seal.startswith(SEAL_COMMIT))
        self.assertEqual(git("merge-base", "--is-ancestor", BASE, seal).returncode, 0, u"封が評価用の結果の commit の後でない")
        self.assertNotEqual(git("rev-parse", BASE).stdout.strip(), seal)
        for rel in NEW_FILES:
            added = git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split()
            if added:
                self.assertEqual(git("merge-base", "--is-ancestor", seal, added[-1]).returncode, 0, rel)
                self.assertNotEqual(seal, added[-1], rel)
        # 封は封の commit から 1 字も直していない(数を見てから封を直さない)
        self.assertEqual(git("diff", "--numstat", SEAL_COMMIT, "--", SEAL_REL).stdout, "")
        self.assertEqual(git("status", "--porcelain", "--", SEAL_REL).stdout, "")
        log = git("log", "--format=%H", "%s..HEAD" % seal, "--", SEAL_REL).stdout.split()
        self.assertEqual(log, [], u"封を封の commit の後に直した commit が在る")

    def test_21_the_seal_commit_changed_only_documents(self):
        files = git("show", "--name-only", "--format=", SEAL_COMMIT).stdout.split()
        self.assertTrue(files)
        self.assertTrue(all(f.startswith("audit-core/docs/") or f.startswith("docs/") for f in files), files)
        self.assertTrue(any(f.endswith("XBRL_DEFAULT_P27_SEAL_2026-10-28.md") for f in files))

    def test_22_the_docs_and_the_result_doc_do_not_name_documents(self):
        for rel in (SEAL_REL, DEFAULT_DOC_REL):
            p = os.path.join(ROOT, rel)
            if not os.path.exists(p):
                continue
            t = text(p)
            self.assertEqual(re.findall(r"S100[0-9A-Z]{4}", t), [], rel)
            self.assertEqual(re.findall(r"(?<![A-Za-z0-9_-])[NT]\d{3}(?![0-9])", t), [], rel)


class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)
        cls.reg = jload(os.path.join(ROOT, REGRESS_REL))
        cls.per = per_file_counts()
        cls.rd = load_module("tests/measure/test_xbrl_default_p27_result.py", "default_p27_result_gate_for_seal_gate_m")
        cls.dec, cls.sentences = cls.rd.eval_decision()
        cls.blocks = parse_blocks(base_text(RESULT_P27_REL))

    def _red(self, fn, *a):
        with self.assertRaises((AssertionError, KeyError, IndexError, ValueError, TypeError)):
            fn(*a)

    def _swap(self, old, new, count=1):
        self.assertIn(old, self.t, old)
        return self.t.replace(old, new, count)

    def _swap_in_row(self, row, old, new):
        lines = self.t.split(u"\n")
        i = [j for j, l in enumerate(lines) if l.startswith(u"| **%s** |" % row)][0]
        self.assertIn(old, lines[i], old)
        lines[i] = lines[i].replace(old, new, 1)
        return u"\n".join(lines)

    def test_baseline_is_green(self):
        rows_ok(self.t)
        check_basis(self.t, self.sentences)
        check_d_numbers(self.t, self.dec["drows"])
        check_eval_table(self.t, self.blocks)
        check_regress(self.t, self.reg)
        check_table_1_2(self.t, self.per)

    def test_m1_a_changed_human_word_is_red(self):
        self._red(check_head, self._swap(u"「君に任せるよ」", u"「君に任せない」"))
        self._red(check_head, self._swap(u"人間(2026-10-27)", u"人間(2026-10-26)"))

    def test_m2_a_seal_that_claims_the_default_is_already_p27_is_red(self):
        self._red(check_head, self._swap(u"**この封の commit 時点では `DEFAULT_PROFILE = \"P26\"` のまま、", u"**この封の commit 時点で `DEFAULT_PROFILE = \"P27\"` に替わっていて、"))

    def test_m3_a_changed_number_in_section_0_is_red(self):
        self._red(check_regress, self._swap(u"UNVERIFIABLE 1,579 → **1,601**", u"UNVERIFIABLE 1,579 → **1,602**"), self.reg)
        self._red(check_regress, self._swap(u"動いた行 **28**", u"動いた行 **29**"), self.reg)
        self._red(check_regress, self._swap(u"67 書類で **81**", u"67 書類で **80**"), self.reg)
        self._red(check_d_numbers, self._swap(u"D-3 無改変の VALUE_MISMATCH の行 P27 − P26 **−4**", u"D-3 無改変の VALUE_MISMATCH の行 P27 − P26 **−3**"), self.dec["drows"])
        self._red(check_eval_table, self._swap(u"**254 / 22 / 106 / 141**", u"**254 / 22 / 106 / 140**"), self.blocks)

    def test_m4_a_prediction_without_a_way_to_fail_is_red(self):
        rows = rows_of(self.t)
        old = rows[u"S-6"][1]
        self._red(check_predictions, self.t.replace(u"| " + old + u" |\n| **S-7**", u"|  |\n| **S-7**", 1))
        self._red(check_predictions, self._swap_in_row(u"S-6", u"**0 / 485**", u"**1 / 485**"))
        self._red(check_predictions, self._swap_in_row(u"S-8", u"**98〜105**", u"**90〜105**"))

    def test_m5_a_pin_list_that_misses_a_file_is_red(self):
        self._red(check_pin_lists, self._swap(u"  - `tests/measure/test_xbrl_vocab_seal.py`\n", u"", 1))
        self._red(check_pin_lists, self._swap(u"門 26 本**", u"門 25 本**"))

    def test_m6_a_changed_group_count_in_section_1_2_is_red(self):
        self._red(check_table_1_2, self._swap(u"**111 file・424 か所**", u"**111 file・423 か所**"), self.per)
        self.assertEqual(sorted(grep_groups(self.per).items())[0][0], "docs")
        per = dict(self.per)
        per["adapters/xbrl/vocabulary.py"] += 1
        self._red(check_table_1_2, self.t, per)

    def test_m7_a_docid_or_claim_id_in_the_seal_is_red(self):
        self._red(check_head, self.t + u"\n評価用の S100ABCD。\n")
        self._red(check_head, self.t + u"\nclaim N076 の読み。\n")

    def test_m8_a_wrong_verdict_sentence_is_red(self):
        self._red(check_basis, self.t, (self.sentences[0], u"判定(P27): P27 を「既定の候補」として記録しない。"))
        self._red(check_basis, self._swap(u"**P27E は既定の候補にしない**", u"P27E も既定の候補にする"), self.sentences)

    def test_m9_the_order_text_must_keep_the_audit_before_the_commit(self):
        self._red(check_order_text, self._swap(u"凍結(sha256 の一覧)→ 独立監査(`step-auditor`)GO → commit", u"commit → 凍結(sha256 の一覧)→ 独立監査(`step-auditor`)GO"))

    def test_m10_a_wrong_prototype_arithmetic_is_red(self):
        self._red(check_prototype_arithmetic, self._swap(u"合計 **97**", u"合計 **98**"))
        self._red(check_prototype_arithmetic, self._swap(u"**増えた赤は 7 本**", u"**増えた赤は 8 本**"))


if __name__ == "__main__":
    unittest.main()
