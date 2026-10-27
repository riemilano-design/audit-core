# -*- coding: utf-8 -*-
"""封 docs/XBRL_P27_SEAL_2026-10-27.md §3-1・§3-3・§5 の**結果の門**(P27 段 2 の実装の便の測定。評価用の測定は別の便)。

**この門が縛るもの**(数は字で留めず、記録から計算する。幅は封の文書の太字から読む)

1. 手元の 97 書類の記録 ``fixtures/xbrl/p27/regress97_2026-10-27.json``: N-1(旗が偽の P22・P26 が封の時点の engine と byte 一致した書類の数)・N-2(P27 の 4 state と動いた行)・
   N-3(P27E の動いた行)の当否を、書類ごとの欄と「動いた行」から**ここで計算し直す**。記録の自前の集計とも照らす(実装を 2 つ持つ)。
2. 調整用 10 社の再現の記録 ``tune_p27_2026-10-27.json``(判定)・``tune_p27_inject_2026-10-27.json``(注入): U-1(旗が偽の P22・P26 が段 1 の記録と欄ごとに同じ)・
   U-2〜U-5 の当否を、行から計算し直す。
3. 記録の中身: 欄の名前に span・subject・value・recomputed が無い・鍵らしい字が無い・既存の cache(281・40)の前後で件数と名前の一覧の sha256 が変わっていない・
   記録が測った engine の指紋と script の sha256 が、いまの file と同じ(動いたら宣言された遷移が要る)。
4. 門の変異: 記録の写しを 1 欄ずつ壊すと、上の計算が変わる/赤になる(N-1 の byte 一致を 1 つ崩す・state を 1 つ動かす・動いた行の向きを変える・禁止欄を足す・鍵らしい字を足す・
   cache の前後を変える・注入の分類を 1 つ変える・段 1 の記録と違う行を作る、など)。

外れは外れとして記録する(予測の当否は計算するだけ。幅を直さない)。この file は docID の字を持たない(引きの門 test_xbrl_fresh_seal が追跡 file の docID を数える)。
評価用の文・評価用の DB の応答は開かない(読むのは repo の記録と封の文書だけ)。
"""
import collections
import copy
import hashlib
import importlib.util
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

SEAL_REL = "docs/XBRL_P27_SEAL_2026-10-27.md"
REGRESS_REL = "fixtures/xbrl/p27/regress97_2026-10-27.json"
TUNE_J_REL = "fixtures/xbrl/p27/tune_p27_2026-10-27.json"
TUNE_I_REL = "fixtures/xbrl/p27/tune_p27_inject_2026-10-27.json"
PREV_J_REL = "fixtures/xbrl/p27/tune_2026-10-27.json"
PREV_I_REL = "fixtures/xbrl/p27/tune_inject_2026-10-27.json"
REGRESS_SCRIPT_REL = "measure/xbrl_p27_regress97_2026-10-27.py"
RERUN_SCRIPT_REL = "measure/xbrl_p27_tune_rerun_2026-10-27.py"
TUNE_SCRIPT_REL = "measure/xbrl_p27_tune_2026-10-27.py"
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
P4 = ("P22", "P26", "P27", "P27E")
FORBIDDEN_KEYS = ("span", "subject", "value", "recomputed")
LABEL_PASS = u"通した"
LABEL_NAMED_ORIGINAL = u"名指して原本の値を返した"
NO_SAME_VALUE = "no_same_value"
OTHER_CONCEPT = "other_concept"
CACHE_KEYS = (u"edinet", u"edinet-fresh-2026-10-21")


def jload(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def text(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_file(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load_tune_script():
    spec = importlib.util.spec_from_file_location("p27_tune_for_engine_result", os.path.join(ROOT, TUNE_SCRIPT_REL))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ====================================================================================================
# 封の文書の太字(幅)
def seal_bounds():
    t = text(SEAL_REL)
    out = {}
    for line in t.splitlines():
        m = re.match(r"\| \*\*((?:U|N)-\d+)\*\* \|", line)
        if m:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            out[m.group(1)] = re.findall(r"\*\*([^*]+)\*\*", cells[1])
    return out


def num(s):
    return int(s.replace(",", ""))


def rng(s):
    a, b = s.split(u"〜")
    return num(a), num(b)


def inside(v, s):
    lo, hi = rng(s)
    return lo <= v <= hi


# ====================================================================================================
# 97 書類の記録(N-1〜N-3)
def regress_numbers(rec):
    u"""書類ごとの欄と動いた行から、N-1〜N-3 の数を計算し直す。"""
    out = {"N-1": {}, "pop": {}}
    docs = rec[u"書類"]
    for p in ("P22", "P26"):
        out["N-1"][p] = sum(1 for d in docs if d[u"出力の sha256(engine の欄を除く)"][p] == d[u"比べる側の engine の出力の sha256"][p])
    out["N-1"]["書類"] = len(docs)
    for pop in (u"手元の 67", u"新しい標本 30"):
        rows = [d for d in docs if d[u"標本"] == pop]
        st = dict((p, dict((s, sum(d[u"4 state"][p][s] for d in rows)) for s in STATES)) for p in ("P26", "P27", "P27E"))
        mv = rec[u"動いた行"][pop]
        a = mv[u"P26 → P27"]
        b = mv[u"P27 → P27E"]
        a_state = [m for m in a if m[u"前"][u"state"] != m[u"後"][u"state"]]
        a_ok = [m for m in a_state if (m[u"前"][u"state"], m[u"後"][u"state"]) in (("UNVERIFIABLE", "POINTER_NOT_FOUND"), ("POINTER_NOT_FOUND", "UNVERIFIABLE"))]
        b_vm = [m for m in b if m[u"前"][u"state"] == "POINTER_NOT_FOUND" and m[u"前"][u"reason"] == NO_SAME_VALUE and m[u"後"][u"state"] == "VALUE_MISMATCH"]
        b_oc = [m for m in b if m[u"前"][u"state"] == "POINTER_NOT_FOUND" and m[u"前"][u"reason"] == NO_SAME_VALUE
                and m[u"後"][u"state"] == "POINTER_NOT_FOUND" and m[u"後"][u"reason"] == OTHER_CONCEPT]
        out["pop"][pop] = {
            "docs": len(rows), "state": st,
            "a_moved": len(a), "a_state_moved": len(a_state), "a_between_unv_pnf": len(a_ok), "a_other_dir": len(a_state) - len(a_ok),
            "a_grounded_ptr": sum(1 for m in a if m[u"前"][u"state"] == "GROUNDED" and m[u"後"][u"state"] == "GROUNDED" and m[u"pointer だけ替わった"]),
            "a_to_vm": sum(1 for m in a if m[u"後"][u"state"] == "VALUE_MISMATCH" and m[u"前"][u"state"] != "VALUE_MISMATCH"),
            "a_new_grounded": sum(1 for m in a if m[u"後"][u"state"] == "GROUNDED" and m[u"前"][u"state"] != "GROUNDED"),
            "b_moved": len(b), "b_to_vm": len(b_vm), "b_to_other_concept": len(b_oc), "b_other_dir": len(b) - len(b_vm) - len(b_oc),
            "b_grounded_differs": sum(1 for m in b if m[u"前"][u"state"] == "GROUNDED" or m[u"後"][u"state"] == "GROUNDED"),
        }
    return out


def regress_judgments(rec, bounds):
    n = regress_numbers(rec)
    j = {}
    j["N-1"] = n["N-1"]["P22"] == n["N-1"]["P26"] == n["N-1"]["書類"] == num(bounds["N-1"][0].split("/")[0])
    p67, p30 = n["pop"][u"手元の 67"], n["pop"][u"新しい標本 30"]
    b = bounds["N-2"]        # ['4,371', '433', '2,194', '250', '0〜3', '20〜40', '10〜25']
    j["N-2"] = (p67["state"]["P27"]["GROUNDED"] == num(b[0]) and p67["state"]["P27"]["VALUE_MISMATCH"] == num(b[1])
                and p30["state"]["P27"]["GROUNDED"] == num(b[2]) and p30["state"]["P27"]["VALUE_MISMATCH"] == num(b[3])
                and p67["state"]["P26"]["GROUNDED"] == num(b[0]) and p67["state"]["P26"]["VALUE_MISMATCH"] == num(b[1])
                and p30["state"]["P26"]["GROUNDED"] == num(b[2]) and p30["state"]["P26"]["VALUE_MISMATCH"] == num(b[3])
                and inside(p67["a_grounded_ptr"], b[4]) and inside(p30["a_grounded_ptr"], b[4])
                and inside(p67["a_state_moved"], b[5]) and inside(p30["a_state_moved"], b[6])
                and p67["a_other_dir"] == 0 and p30["a_other_dir"] == 0
                and p67["a_to_vm"] == 0 and p30["a_to_vm"] == 0 and p67["a_new_grounded"] == 0 and p30["a_new_grounded"] == 0)
    c = bounds["N-3"]        # ['70〜95', '15〜35']
    j["N-3"] = (p67["state"]["P27E"]["GROUNDED"] == p67["state"]["P27"]["GROUNDED"] and p30["state"]["P27E"]["GROUNDED"] == p30["state"]["P27"]["GROUNDED"]
                and p67["b_grounded_differs"] == 0 and p30["b_grounded_differs"] == 0
                and p67["b_other_dir"] == 0 and p30["b_other_dir"] == 0
                and inside(p67["b_to_vm"], c[0]) and inside(p30["b_to_vm"], c[1]))
    return j, n


def check_regress_record(rec):
    u"""記録の自前の集計が、ここで計算し直した数と同じ(実装を 2 つ持つ)。"""
    n = regress_numbers(rec)
    assert rec[u"N-1"]["P22"][u"byte が同じ書類"] == n["N-1"]["P22"] and rec[u"N-1"]["P26"][u"byte が同じ書類"] == n["N-1"]["P26"], u"N-1 の自前の集計が違う"
    assert rec[u"N-1"]["P22"][u"書類"] == n["N-1"]["書類"] == rec[u"N-1"]["P26"][u"書類"]
    for pop, s in rec[u"集計"].items():
        mine = n["pop"][pop]
        assert s[u"書類"] == mine["docs"], u"書類の数が違う"
        for p in ("P22", "P26", "P27", "P27E"):
            if p == "P22":
                continue
            assert s[u"4 state"][p] == mine["state"][p], u"4 state の自前の集計が違う: %s %s" % (pop, p)
        assert s[u"P26 → P27"][u"動いた行(state か reason か pointer が違う)"] == mine["a_moved"]
        assert s[u"P26 → P27"][u"state が違う行"] == mine["a_state_moved"]
        assert s[u"P26 → P27"][u"UNVERIFIABLE と POINTER_NOT_FOUND の間だけの行"] == mine["a_between_unv_pnf"]
        assert s[u"P26 → P27"][u"他の向きの行"] == mine["a_other_dir"]
        assert s[u"P26 → P27"][u"GROUNDED のまま pointer が替わる行"] == mine["a_grounded_ptr"]
        assert s[u"P26 → P27"][u"VALUE_MISMATCH に入る行"] == mine["a_to_vm"]
        assert s[u"P26 → P27"][u"新しい GROUNDED"] == mine["a_new_grounded"]
        assert s[u"P27 → P27E"][u"動いた行"] == mine["b_moved"]
        assert s[u"P27 → P27E"][u"VALUE_MISMATCH に入る行(no_same_value → VALUE_MISMATCH)"] == mine["b_to_vm"]
        assert s[u"P27 → P27E"][u"名指した後に G1 で止まる行(no_same_value → other_concept)"] == mine["b_to_other_concept"]
        assert s[u"P27 → P27E"][u"他の向きの行"] == mine["b_other_dir"]
        assert s[u"P27 → P27E"][u"GROUNDED が P27 と違う行"] == mine["b_grounded_differs"]
    # 書類の数・claim の数の整合
    docs = rec[u"書類"]
    assert len(set(d[u"docID"] for d in docs)) == len(docs) == 97, u"書類が 97 でない"
    for d in docs:
        for p in ("P22", "P26", "P27", "P27E"):
            assert sum(d[u"4 state"][p].values()) == d[u"claims"], u"claim の数と 4 state の合計が違う"


# ====================================================================================================
# 調整用の再現(U-1〜U-5)
def row_fields(r):
    return dict((k, r[k]) for k in ("kind", "form", "unit", "state", "reason", "pointers"))


def tune_numbers(judge, inject, prev_judge, prev_inject):
    u"""U-1〜U-5 の数を、行から計算し直す。"""
    out = {}
    prev = dict(((r["docID"], r["id"]), r) for r in prev_judge["claim"])
    diff = 0
    n = 0
    for r in judge["claim"]:
        old = prev[(r["docID"], r["id"])]
        for p in ("P22", "P26"):
            n += 1
            if row_fields(r[p]) != row_fields(old[p]):
                diff += 1
    out["U-1_judge"] = {"照らした": n, "違う": diff, "集合が同じ": set(prev) == set((r["docID"], r["id"]) for r in judge["claim"])}
    pi = dict(((r["docID"], r["id"]), r) for r in prev_inject["行"])
    diff = 0
    for r in inject["行"]:
        old = pi.get((r["docID"], r["id"]))
        if old is None:
            diff += 1
            continue
        for p in ("P22", "P26"):
            if r[p] != old[p]:
                diff += 1
    out["U-1_inject"] = {"照らした": len(inject["行"]), "違う": diff, "集合が同じ": set(pi) == set((r["docID"], r["id"]) for r in inject["行"])}
    rows = judge["claim"]
    st = dict((p, dict((s, sum(1 for r in rows if r[p]["state"] == s) ) for s in STATES)) for p in P4)
    out["state"] = st
    out["claims"] = len(rows)
    out["U-2"] = {"G": st["P27"]["GROUNDED"], "VM": st["P27"]["VALUE_MISMATCH"],
                  "new_G": sum(1 for r in rows if r["P27"]["state"] == "GROUNDED" and r["P26"]["state"] != "GROUNDED"),
                  "to_VM": sum(1 for r in rows if r["P27"]["state"] == "VALUE_MISMATCH" and r["P26"]["state"] != "VALUE_MISMATCH")}
    out["U-3"] = {"same_state": sum(1 for r in rows if r["P27E"]["state"] == r["P27"]["state"])}
    for t in ("T1_VALUE", "T8_REL"):
        sel = [r for r in inject["行"] if r["型"] == t and all(r[p]["対応"] for p in P4)]
        out[t] = {"mapped": len(sel)}
        for p in P4:
            out[t][p] = {"pass": sum(1 for r in sel if r[p]["結果"] == LABEL_PASS), "named_original": sum(1 for r in sel if r[p]["結果"] == LABEL_NAMED_ORIGINAL)}
    return out


def tune_judgments(num_, bounds):
    j = {}
    j["U-1"] = (num_["U-1_judge"]["違う"] == 0 and num_["U-1_judge"]["集合が同じ"] and num_["U-1_inject"]["違う"] == 0 and num_["U-1_inject"]["集合が同じ"])
    b = bounds["U-2"]    # ['271〜275', '14〜18', '0', '0']
    j["U-2"] = inside(num_["U-2"]["G"], b[0]) and inside(num_["U-2"]["VM"], b[1]) and num_["U-2"]["new_G"] == num(b[2]) and num_["U-2"]["to_VM"] == num(b[3])
    j["U-3"] = num_["U-3"]["same_state"] == num(bounds["U-3"][0].split("/")[0]) == num_["claims"]
    b = bounds["U-4"]    # ['0〜1', '15〜24', '70〜80']
    t8 = num_["T8_REL"]
    j["U-4"] = (inside(t8["P27"]["pass"], b[0]) and inside(t8["P27E"]["pass"], b[0]) and inside(t8["P27"]["named_original"], b[1]) and inside(t8["P27E"]["named_original"], b[2]))
    b = bounds["U-5"]    # ['0', '6〜8']
    t1 = num_["T1_VALUE"]
    j["U-5"] = all(t1[p]["pass"] == num(b[0]) for p in P4) and inside(t1["P27E"]["named_original"], b[1])
    return j


def check_tune_records(judge, inject):
    u"""記録の自前の集計が、ここで計算し直した数と同じ。"""
    s = judge[u"集計"]
    rows = judge["claim"]
    for p in P4:
        assert s[u"state の数"][p] == dict((x, sum(1 for r in rows if r[p]["state"] == x)) for x in STATES), u"state の数の自前の集計が違う: " + p
    assert s[u"P26 → P27 で新しい GROUNDED"] == sum(1 for r in rows if r["P27"]["state"] == "GROUNDED" and r["P26"]["state"] != "GROUNDED")
    assert s[u"P26 → P27 で VALUE_MISMATCH に入る行"] == sum(1 for r in rows if r["P27"]["state"] == "VALUE_MISMATCH" and r["P26"]["state"] != "VALUE_MISMATCH")
    assert s[u"P27E の無改変が P27 と state が同じ行"] == sum(1 for r in rows if r["P27E"]["state"] == r["P27"]["state"])
    assert judge[u"U-1(旗が偽の P22・P26)"][u"段 1 の記録と欄(id・kind・form・unit・state・reason・pointers)が違う行"] == len(judge[u"U-1(旗が偽の P22・P26)"][u"違う行"])
    assert inject[u"注入の行の数"] == len(inject[u"行"])
    for t in ("T1_VALUE", "T8_REL"):
        for p in P4:
            agg = inject[u"集計"][t][p][u"全体"]
            sel = [r for r in inject[u"行"] if r[u"型"] == t and r[p][u"対応"]]
            assert agg[u"対応が付く"] == len(sel), u"対応が付く行の数の自前の集計が違う"
            assert agg[LABEL_PASS][u"件"] == sum(1 for r in sel if r[p][u"結果"] == LABEL_PASS)
            assert agg[LABEL_NAMED_ORIGINAL][u"件"] == sum(1 for r in sel if r[p][u"結果"] == LABEL_NAMED_ORIGINAL)


# ====================================================================================================
# 記録の中身(欄・鍵・cache・engine・script)
def check_record_clean(T, rec):
    bad = sorted(set(k for k in T.walk_keys(rec) if k in FORBIDDEN_KEYS))
    assert not bad, u"記録に repo へ入れない欄がある: %s" % ",".join(bad)
    leaks = T.record_key_leaks(rec)
    assert not leaks, u"鍵らしい字が記録に在る: %s" % " / ".join(sorted(set(leaks)))


def check_cache_unchanged(rec):
    c = rec[u"cache の前後"]
    assert c[u"変化なし"] is True and c[u"前"] == c[u"後"], u"既存の cache の前後が違う"
    snaps = c[u"前"]
    if u"edinet" in snaps:                                            # regress97 の形
        assert snaps[u"edinet"][u"件数"] == 281 and snaps[u"edinet-fresh-2026-10-21"][u"件数"] == 40, u"cache の件数が 281・40 でない"
    else:                                                             # tune の形
        assert snaps[u"既存の cache"][u"件数"] == 281 and snaps[u"ZIP の folder"][u"件数"] == 40, u"cache の件数が 281・40 でない"


def check_engine_and_script(rec, script_rel, engine_now):
    assert rec[u"この script の sha256"] == sha_file(script_rel), u"記録が測った script がいまの file と違う: " + script_rel
    fp = rec[u"engine の指紋"]
    assert fp[u"adapter_xbrl_py_sha256"] == engine_now[u"adapter_xbrl_py_sha256"], u"記録が測った engine がいまの engine と違う"
    assert fp[u"adapter_xbrl_py_files"] == engine_now[u"adapter_xbrl_py_files"] == 16
    assert fp[u"core_py_sha256"] == engine_now[u"core_py_sha256"] and fp[u"core_py_files"] == engine_now[u"core_py_files"]


class Records(object):
    pass


def engine_now():
    from adapters.xbrl import verify_document as VD
    return VD.engine_fingerprint()


class RegressRecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REGRESS_REL)
        cls.bounds = seal_bounds()
        cls.T = load_tune_script()

    def test_1_bounds_are_read_from_the_seal(self):
        b = self.bounds
        self.assertEqual(["97 / 97"], b["N-1"])
        self.assertEqual(["4,371", "433", "2,194", "250", u"0〜3", u"20〜40", u"10〜25"], b["N-2"])
        self.assertEqual([u"70〜95", u"15〜35"], b["N-3"])

    def test_2_the_numbers_are_recomputed_and_the_record_agrees(self):
        check_regress_record(self.rec)
        j, n = regress_judgments(self.rec, self.bounds)
        self.assertEqual(97, n["N-1"]["書類"])
        self.assertEqual({"N-1": True, "N-2": True, "N-3": True}, j)       # 外れたら外れのまま記録する(その時はこの期待を、外れた事実に直す = 封と結果を書き換えない)

    def test_3_n1_p22_and_p26_are_byte_equal_to_the_seal_time_engine(self):
        n = regress_numbers(self.rec)
        self.assertEqual((97, 97, 97), (n["N-1"]["P22"], n["N-1"]["P26"], n["N-1"]["書類"]))
        self.assertEqual([], self.rec[u"N-1"]["P22"][u"違った書類"])
        self.assertEqual([], self.rec[u"N-1"]["P26"][u"違った書類"])
        # 『差 0』が自分の欠陥でないことの確かめ: P27 の出力の sha256 は P26 と違う書類が在る(旗が真の profile は別の出力を作る)
        differs = sum(1 for d in self.rec[u"書類"] if d[u"出力の sha256(engine の欄を除く)"]["P27"] != d[u"出力の sha256(engine の欄を除く)"]["P26"])
        self.assertGreater(differs, 0)

    def test_4_the_baseline_is_the_seal_time_engine(self):
        base = self.rec[u"比べた engine"]
        self.assertEqual("29e6d0a", base[u"commit"])
        self.assertEqual(16, len(base[u"adapters/xbrl の file の sha256(commit の blob)"]))

    def test_5_the_97_documents_are_the_67_and_the_30(self):
        docs = self.rec[u"書類"]
        self.assertEqual(67, sum(1 for d in docs if d[u"標本"] == u"手元の 67"))
        self.assertEqual(30, sum(1 for d in docs if d[u"標本"] == u"新しい標本 30"))
        p26 = jload("fixtures/xbrl/p26_2026-10-21.json")
        self.assertEqual(sorted(p26[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"]), sorted(d[u"docID"] for d in docs if d[u"標本"] == u"手元の 67"))
        fetched = jload("fixtures/xbrl/fresh/fetched_2026-10-21.json")
        want30 = dict((r["docID"], r["sha256"]) for r in fetched[u"取得した書類"] if r.get(u"使う"))
        self.assertEqual(want30, dict((d[u"docID"], d[u"zip の sha256"]) for d in docs if d[u"標本"] == u"新しい標本 30"))
        for d in docs:
            if d[u"標本"] == u"手元の 67":
                self.assertEqual(p26[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"][d[u"docID"]], d[u"zip の sha256"])

    def test_6_p26_numbers_equal_the_recorded_default_p26_numbers(self):
        """P26 の 4 state は、既定を P26 にした測定の記録(default_p26_2026-10-23.json の S2・S3)と同じ(= この測定の P26 は測った当時の P26 と同じ)。"""
        d = jload("fixtures/xbrl/default_p26_2026-10-23.json")
        n = regress_numbers(self.rec)
        want67 = d[u"S2"][u"既定の 4 state"]
        want30 = d[u"S3"][u"既定の 4 state"]
        self.assertEqual(dict((s, want67[s]) for s in STATES), n["pop"][u"手元の 67"]["state"]["P26"])
        self.assertEqual(dict((s, want30[s]) for s in STATES), n["pop"][u"新しい標本 30"]["state"]["P26"])

    def test_7_clean_cache_engine_and_script(self):
        check_record_clean(self.T, self.rec)
        check_cache_unchanged(self.rec)
        check_engine_and_script(self.rec, REGRESS_SCRIPT_REL, engine_now())

    def test_8_the_rule_counts_are_in_the_record_and_match_the_moved_rows(self):
        """規則ごとに当たった claim の数(P27 の raw claim の印)は、動いた行の理由の数と整合する: C2 の行は P26 → P27 で理由が per_unit_counter になった行の数以上。"""
        for pop, s in self.rec[u"集計"].items():
            moved = self.rec[u"動いた行"][pop][u"P26 → P27"]
            c2_moved = sum(1 for m in moved if m[u"後"][u"reason"] == "per_unit_counter")
            c3_moved = sum(1 for m in moved if m[u"後"][u"reason"] == "target_or_plan")
            r = s[u"規則ごとに当たった claim の数"]
            self.assertGreaterEqual(r["P27"][u"C2 per_unit_counter"], c2_moved, pop)
            self.assertGreaterEqual(r["P27"][u"C3 future_period"], c3_moved, pop)
            self.assertEqual(r["P27"][u"C2 per_unit_counter"], r["P27E"][u"C2 per_unit_counter"])
            self.assertEqual(r["P27"][u"B relative_within_rho"], 0)
            self.assertGreater(r["P27E"][u"B relative_within_rho"], 0)


class TuneRecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.j = jload(TUNE_J_REL)
        cls.i = jload(TUNE_I_REL)
        cls.pj = jload(PREV_J_REL)
        cls.pi = jload(PREV_I_REL)
        cls.bounds = seal_bounds()
        cls.T = load_tune_script()

    def test_1_bounds_are_read_from_the_seal(self):
        b = self.bounds
        self.assertEqual([u"271〜275", u"14〜18", "0", "0"], b["U-2"])
        self.assertEqual(["534 / 534"], b["U-3"])
        self.assertEqual([u"0〜1", u"15〜24", u"70〜80"], b["U-4"])
        self.assertEqual(["0", u"6〜8"], b["U-5"])

    def test_2_u1_to_u5_are_recomputed_from_the_rows(self):
        check_tune_records(self.j, self.i)
        n = tune_numbers(self.j, self.i, self.pj, self.pi)
        self.assertEqual(534, n["claims"])
        self.assertEqual(1068, n["U-1_judge"]["照らした"])
        j = tune_judgments(n, self.bounds)
        self.assertEqual({"U-1": True, "U-2": True, "U-3": True, "U-4": True, "U-5": True}, j)

    def test_3_the_measured_values(self):
        u"""(外れても直さない値の確認ではなく)記録から計算した数を字で見えるようにしておく。"""
        n = tune_numbers(self.j, self.i, self.pj, self.pi)
        self.assertEqual({"G": 273, "VM": 16, "new_G": 0, "to_VM": 0}, n["U-2"])
        self.assertEqual(534, n["U-3"]["same_state"])
        t8 = n["T8_REL"]
        self.assertEqual(88, t8["mapped"])
        self.assertEqual((28, 28, 0, 0), (t8["P22"]["pass"], t8["P26"]["pass"], t8["P27"]["pass"], t8["P27E"]["pass"]))
        self.assertEqual((56, 19, 19, 75), (t8["P22"]["named_original"], t8["P26"]["named_original"], t8["P27"]["named_original"], t8["P27E"]["named_original"]))
        t1 = n["T1_VALUE"]
        self.assertEqual(10, t1["mapped"])
        self.assertEqual((0, 0, 0, 0), (t1["P22"]["pass"], t1["P26"]["pass"], t1["P27"]["pass"], t1["P27E"]["pass"]))
        self.assertEqual((10, 8, 5, 7), (t1["P22"]["named_original"], t1["P26"]["named_original"], t1["P27"]["named_original"], t1["P27E"]["named_original"]))

    def test_4_the_flag_false_profiles_equal_the_stage_1_record_and_the_site_set_is_the_same(self):
        self.assertEqual(0, self.j[u"U-1(旗が偽の P22・P26)"][u"段 1 の記録と欄(id・kind・form・unit・state・reason・pointers)が違う行"])
        self.assertEqual(0, self.i[u"U-1(旗が偽の P22・P26)"][u"段 1 の記録と分類(対応・結果・state・reason)が違う行"])
        self.assertEqual(101, self.i[u"注入の行の数"])
        self.assertEqual(self.pi[u"T8_REL の site"], self.i[u"T8_REL の site"])
        self.assertEqual(self.pi[u"書類別の数え"], self.i[u"書類別の数え"])

    def test_5_clean_cache_engine_and_script(self):
        for rec, script in ((self.j, RERUN_SCRIPT_REL), (self.i, RERUN_SCRIPT_REL)):
            check_record_clean(self.T, rec)
            check_cache_unchanged(rec)
            check_engine_and_script(rec, script, engine_now())
        self.assertEqual(sha_file(TUNE_SCRIPT_REL), self.j[u"段 1 の測定の script(読むだけ・1 行も変えない)の sha256"])
        self.assertEqual(sha_file(TUNE_SCRIPT_REL), self.i[u"段 1 の測定の script(読むだけ・1 行も変えない)の sha256"])
        self.assertEqual(self.pj[u"対象の docID"], self.j[u"対象の docID"])
        self.assertEqual(self.pj[u"使った文の sha256"], self.j[u"使った文の sha256"])
        self.assertTrue(self.j[u"対象は調整用の全部"])

    def test_6_only_tuning_documents_were_measured(self):
        w = jload("fixtures/xbrl/p27/reports_2026-10-27.json")
        tuning = sorted(c["docID"] for c in w["会社"] if c["区分"] == u"調整用")
        evalu = set(c["docID"] for c in w["会社"] if c["区分"] == u"評価用")
        self.assertEqual(tuning, sorted(self.j[u"対象の docID"]))
        self.assertEqual(tuning, sorted(self.i[u"対象の docID"]))
        for rec in (self.j, self.i):
            self.assertFalse(evalu & set(json.dumps(rec, ensure_ascii=False).split('"')), u"評価用の docID が調整用の記録に在る")
            self.assertEqual("real", rec["backend"])


# ====================================================================================================
class GateMutationTest(unittest.TestCase):
    u"""門自身が、壊した写しで赤くなる/計算が変わる(毎回走る)。"""

    @classmethod
    def setUpClass(cls):
        cls.rg = jload(REGRESS_REL)
        cls.j = jload(TUNE_J_REL)
        cls.i = jload(TUNE_I_REL)
        cls.pj = jload(PREV_J_REL)
        cls.pi = jload(PREV_I_REL)
        cls.bounds = seal_bounds()
        cls.T = load_tune_script()

    def _red(self, f, *a):
        with self.assertRaises(AssertionError):
            f(*a)

    # ---- 97 書類
    def test_m1_a_broken_byte_equality_turns_n1_false(self):
        r = copy.deepcopy(self.rg)
        r[u"書類"][3][u"比べる側の engine の出力の sha256"]["P22"] = "0" * 64
        j, n = regress_judgments(r, self.bounds)
        self.assertEqual(96, n["N-1"]["P22"])
        self.assertFalse(j["N-1"])
        self._red(check_regress_record, r)                      # 自前の集計(97)と食い違う

    def test_m2_a_moved_state_changes_the_numbers(self):
        r = copy.deepcopy(self.rg)
        r[u"書類"][0][u"4 state"]["P27"]["GROUNDED"] += 1
        r[u"書類"][0][u"4 state"]["P27"]["UNVERIFIABLE"] -= 1
        pop = r[u"書類"][0][u"標本"]
        j, n = regress_judgments(r, self.bounds)
        self.assertFalse(j["N-2"])
        self._red(check_regress_record, r)

    def test_m3_a_row_in_another_direction_turns_n2_false(self):
        r = copy.deepcopy(self.rg)
        pop = u"手元の 67"
        r[u"動いた行"][pop][u"P26 → P27"].append({u"docID": "x", u"id": "N001", u"前": {u"state": "GROUNDED", u"reason": None},
                                                u"後": {u"state": "VALUE_MISMATCH", u"reason": None}, u"pointer だけ替わった": False})
        j, n = regress_judgments(r, self.bounds)
        self.assertEqual(1, n["pop"][pop]["a_other_dir"])
        self.assertEqual(1, n["pop"][pop]["a_to_vm"])
        self.assertFalse(j["N-2"])
        r = copy.deepcopy(self.rg)
        r[u"動いた行"][pop][u"P27 → P27E"].append({u"docID": "x", u"id": "N001", u"前": {u"state": "UNVERIFIABLE", u"reason": "x"},
                                                 u"後": {u"state": "GROUNDED", u"reason": None}, u"pointer だけ替わった": False})
        j, n = regress_judgments(r, self.bounds)
        self.assertFalse(j["N-3"])
        self.assertEqual(1, n["pop"][pop]["b_other_dir"])

    def test_m4_a_pointer_change_on_a_grounded_row_is_counted(self):
        r = copy.deepcopy(self.rg)
        pop = u"新しい標本 30"
        for _ in range(4):
            r[u"動いた行"][pop][u"P26 → P27"].append({u"docID": "x", u"id": "N001", u"前": {u"state": "GROUNDED", u"reason": None},
                                                    u"後": {u"state": "GROUNDED", u"reason": None}, u"pointer だけ替わった": True})
        j, n = regress_judgments(r, self.bounds)
        self.assertEqual(4, n["pop"][pop]["a_grounded_ptr"])
        self.assertFalse(j["N-2"])                                  # 幅は 0〜3

    def test_m5_range_edges_of_n3(self):
        r = copy.deepcopy(self.rg)
        pop = u"手元の 67"
        vm = [m for m in r[u"動いた行"][pop][u"P27 → P27E"] if m[u"後"][u"state"] == "VALUE_MISMATCH"]
        n0 = len(vm)
        self.assertTrue(70 <= n0 <= 95)
        r[u"動いた行"][pop][u"P27 → P27E"] = [m for m in r[u"動いた行"][pop][u"P27 → P27E"] if m not in vm[:n0 - 69]]       # 69 行に減らす = 幅の外
        j, n = regress_judgments(r, self.bounds)
        self.assertEqual(69, n["pop"][pop]["b_to_vm"])
        self.assertFalse(j["N-3"])

    # ---- 調整用
    def test_m6_u2_u3_change_when_a_state_moves(self):
        j = copy.deepcopy(self.j)
        for r in j["claim"]:
            if r["P27"]["state"] == "UNVERIFIABLE":
                r["P27"]["state"] = "GROUNDED"
                break
        n = tune_numbers(j, self.i, self.pj, self.pi)
        self.assertEqual(274, n["U-2"]["G"])
        self.assertEqual(533, n["U-3"]["same_state"])
        self.assertFalse(tune_judgments(n, self.bounds)["U-3"])
        self._red(check_tune_records, j, self.i)
        j = copy.deepcopy(self.j)
        for r in j["claim"]:
            if r["P27"]["state"] == "UNVERIFIABLE" and r["P26"]["state"] != "GROUNDED":
                r["P27"]["state"] = "GROUNDED"
                break
        self.assertFalse(tune_judgments(tune_numbers(j, self.i, self.pj, self.pi), self.bounds)["U-2"])        # 新しい GROUNDED が 1 行

    def test_m7_u1_is_false_when_a_flag_false_row_differs_from_stage_1(self):
        j = copy.deepcopy(self.j)
        j["claim"][5]["P26"]["state"] = "GROUNDED" if j["claim"][5]["P26"]["state"] != "GROUNDED" else "VALUE_MISMATCH"
        n = tune_numbers(j, self.i, self.pj, self.pi)
        self.assertEqual(1, n["U-1_judge"]["違う"])
        self.assertFalse(tune_judgments(n, self.bounds)["U-1"])
        i = copy.deepcopy(self.i)
        i["行"][0]["P22"]["結果"] = u"通した" if i["行"][0]["P22"]["結果"] != u"通した" else u"名指したが別の値"
        n = tune_numbers(self.j, i, self.pj, self.pi)
        self.assertEqual(1, n["U-1_inject"]["違う"])
        self.assertFalse(tune_judgments(n, self.bounds)["U-1"])
        i = copy.deepcopy(self.i)
        i["行"] = i["行"][1:]
        self.assertFalse(tune_judgments(tune_numbers(self.j, i, self.pj, self.pi), self.bounds)["U-1"])        # 行の集合が違う

    def test_m8_u4_u5_change_when_an_injection_class_changes(self):
        i = copy.deepcopy(self.i)
        for r in i["行"]:
            if r["型"] == "T8_REL" and all(r[p]["対応"] for p in P4) and r["P27E"]["結果"] != LABEL_PASS:
                r["P27E"]["結果"] = LABEL_PASS
                break
        self.assertEqual(1, tune_numbers(self.j, i, self.pj, self.pi)["T8_REL"]["P27E"]["pass"])
        self.assertTrue(tune_judgments(tune_numbers(self.j, i, self.pj, self.pi), self.bounds)["U-4"])       # 幅は 0〜1 なので 1 行まで当たり
        for r in i["行"]:
            if r["型"] == "T8_REL" and all(r[p]["対応"] for p in P4) and r["P27E"]["結果"] != LABEL_PASS:
                r["P27E"]["結果"] = LABEL_PASS
                break
        self.assertFalse(tune_judgments(tune_numbers(self.j, i, self.pj, self.pi), self.bounds)["U-4"])      # 2 行で外れる
        i = copy.deepcopy(self.i)
        for r in i["行"]:
            if r["型"] == "T1_VALUE" and all(r[p]["対応"] for p in P4) and r["P27"]["結果"] != LABEL_PASS:
                r["P27"]["結果"] = LABEL_PASS
                break
        self.assertFalse(tune_judgments(tune_numbers(self.j, i, self.pj, self.pi), self.bounds)["U-5"])      # T1_VALUE の通した 1 行で外れる
        self._red(check_tune_records, self.j, i)

    # ---- 記録の中身
    def test_m9_forbidden_keys_and_key_like_strings_are_red(self):
        for rec in (self.rg, self.j, self.i):
            check_record_clean(self.T, rec)
        r = copy.deepcopy(self.j)
        r["claim"][0]["P22"]["span"] = "x"
        self._red(check_record_clean, self.T, r)
        for k in FORBIDDEN_KEYS:
            r = copy.deepcopy(self.i)
            r["行"][0][k] = "x"
            self._red(check_record_clean, self.T, r)
        r = copy.deepcopy(self.rg)
        r[u"書類"][0][u"メモ"] = "0123456789abcdef0123456789abcdef"            # 32 桁の 16 進(鍵らしい字)
        self._red(check_record_clean, self.T, r)
        r = copy.deepcopy(self.rg)
        r[u"書類"][0][u"メモ"] = self.T.DB.KEY_NAME + "=abcdefgh1234"          # 鍵の名前は段 1 の script が持つ。字では書かない
        self._red(check_record_clean, self.T, r)

    def test_m10_a_changed_cache_or_a_different_engine_or_script_is_red(self):
        for rec in (self.rg, self.j, self.i):
            check_cache_unchanged(rec)
        r = copy.deepcopy(self.rg)
        r[u"cache の前後"][u"変化なし"] = False
        self._red(check_cache_unchanged, r)
        r = copy.deepcopy(self.rg)
        r[u"cache の前後"][u"後"][u"edinet"][u"件数"] = 282
        self._red(check_cache_unchanged, r)
        r = copy.deepcopy(self.j)
        r[u"cache の前後"][u"前"][u"既存の cache"][u"件数"] = 280
        r[u"cache の前後"][u"後"][u"既存の cache"][u"件数"] = 280
        self._red(check_cache_unchanged, r)
        now = engine_now()
        check_engine_and_script(self.rg, REGRESS_SCRIPT_REL, now)
        r = copy.deepcopy(self.rg)
        r[u"engine の指紋"][u"adapter_xbrl_py_sha256"] = "0" * 64
        self._red(check_engine_and_script, r, REGRESS_SCRIPT_REL, now)
        r = copy.deepcopy(self.rg)
        r[u"この script の sha256"] = "0" * 64
        self._red(check_engine_and_script, r, REGRESS_SCRIPT_REL, now)

    def test_m11_a_changed_self_aggregate_is_red(self):
        r = copy.deepcopy(self.rg)
        r[u"集計"][u"手元の 67"][u"4 state"]["P27"]["GROUNDED"] += 1
        self._red(check_regress_record, r)
        r = copy.deepcopy(self.rg)
        r[u"集計"][u"新しい標本 30"][u"P27 → P27E"][u"動いた行"] += 1
        self._red(check_regress_record, r)
        j = copy.deepcopy(self.j)
        j[u"集計"][u"state の数"]["P27"]["GROUNDED"] += 1
        self._red(check_tune_records, j, self.i)
        i = copy.deepcopy(self.i)
        i[u"集計"]["T8_REL"]["P27E"][u"全体"][u"対応が付く"] += 1
        self._red(check_tune_records, self.j, i)

    def test_m12_the_bounds_are_read_from_the_seal_not_from_this_file(self):
        t = text(SEAL_REL)
        self.assertEqual(1, t.count(u"**271〜275**"))
        b = seal_bounds()
        self.assertEqual(u"271〜275", b["U-2"][0])


if __name__ == "__main__":
    unittest.main()
