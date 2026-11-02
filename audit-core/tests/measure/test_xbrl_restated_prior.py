# -*- coding: utf-8 -*-
u"""門: 出所のずれの名指しの便(封 docs/XBRL_RESTATED_PRIOR_SEAL_2026-11-02.md)の段 1 の script と記録。

縛る物:
- 封 §3 の幅(F-2〜F-5・F-11)と script の BOUNDS が一致する。script は engine を adapters.xbrl.instance でしか import せず、
  通信先は EDINET API v2 の定数 1 つ、鍵は環境変数の名前だけ(値を print・記録しない)、書く先は新しい folder と出力の記録だけ。
- 作り物の有報(合成の .xbrl の ZIP)と作り物の backend で段 1 を走らせ、突き合わせ(同じ / 違う / 片方に無い・member の枠を除く・
  重なり)・前年の探し方(窓・docTypeCode の絞り・提出の遅い方)・DEI の読み取り・記録の形・key_leaks を確かめる。
- 記録 fixtures/xbrl/prior_pairs_2026-11-02.json が在るとき: 形、97 書類、集計の数え直し、封の幅からの判定の求め直し。無ければ skip。
- 順序(封 < script・記録・門)。変異で赤くなる。
"""
from __future__ import print_function

import ast
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
SEAL_REL = "docs/XBRL_RESTATED_PRIOR_SEAL_2026-11-02.md"
REC_REL = "fixtures/xbrl/prior_pairs_2026-11-02.json"
SCRIPT_REL = "measure/xbrl_prior_pairs_2026-11-02.py"
GATE_REL = "tests/measure/test_xbrl_restated_prior.py"
SEAL_COMMIT_SHORT = "3a099e7"
SEAL, REC, SCRIPT = (os.path.join(ROOT, r) for r in (SEAL_REL, REC_REL, SCRIPT_REL))
HEX40 = re.compile(r"^[0-9a-f]{40}$")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
ALLOWED_IMPORTS = {"argparse", "collections", "datetime", "hashlib", "importlib", "io", "json", "os", "re", "statistics", "subprocess", "sys",
                   "urllib", "zipfile", "__future__", "adapters"}
ALLOWED_ENGINE = {"adapters.xbrl", "adapters.xbrl.instance"}


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout.decode("utf-8", "replace").strip()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 封の字

def seal_rows(seal):
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(F-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            out[m.group(1)] = tuple(c.strip() for c in body.split(u" | "))
    return out


def seal_bounds(seal):
    rows = seal_rows(seal)
    b = collections.OrderedDict()
    m = re.search(r"\*\*(\d+)〜(\d+)\*\*", rows[u"F-2"][0])
    b[u"F-2"] = (int(m.group(1)), int(m.group(2)))
    m = re.search(r"\*\*(\d+)〜(\d+)\*\*", rows[u"F-3"][0])
    b[u"F-3"] = (int(m.group(1)), int(m.group(2)))
    m = re.search(r"\*\*(\d+)〜(\d+)%\*\*", rows[u"F-4"][0])
    b[u"F-4"] = (float(m.group(1)), float(m.group(2)))
    m = re.search(r"\*\*(\d+)〜(\d+)%\*\*", rows[u"F-5"][0])
    b[u"F-5"] = (float(m.group(1)), float(m.group(2)))
    b[u"F-11"] = 50.0 if u"半数以上" in rows[u"F-11"][0] else None
    return b


# ---------------------------------------------------------------- 作り物の有報

XBRL_HEAD = (u'<?xml version="1.0" encoding="UTF-8"?><xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:xbrldi="http://xbrl.org/2006/xbrldi" '
             u'xmlns:jppfs_cor="http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor" xmlns:jpdei_cor="http://disclosure.edinet-fsa.go.jp/taxonomy/jpdei/2013-08-31/jpdei_cor" '
             u'xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink"><xbrli:unit id="JPY"><xbrli:measure>iso4217:JPY</xbrli:measure></xbrli:unit>')


def _ctx(cid, code, instant=None, start=None, end=None, member=None):
    seg = (u'<xbrli:segment><xbrldi:explicitMember dimension="jppfs_cor:SegAxis">%s</xbrldi:explicitMember></xbrli:segment>' % member) if member else u""
    per = (u"<xbrli:instant>%s</xbrli:instant>" % instant) if instant else (u"<xbrli:startDate>%s</xbrli:startDate><xbrli:endDate>%s</xbrli:endDate>" % (start, end))
    return u'<xbrli:context id="%s"><xbrli:entity><xbrli:identifier scheme="x">%s</xbrli:identifier>%s</xbrli:entity><xbrli:period>%s</xbrli:period></xbrli:context>' % (cid, code, seg, per)


def make_zip(code, fy_end, facts, dup=None):
    u"""facts: [(要素, 枠の id, 値)]。枠は CurrentYearDuration / CurrentYearInstant / Prior1YearDuration / Prior1YearInstant / CurrentYearDuration_Seg。"""
    ctxs = (_ctx(u"CurrentYearDuration", code, start=u"S", end=fy_end) + _ctx(u"CurrentYearInstant", code, instant=fy_end)
            + _ctx(u"Prior1YearDuration", code, start=u"P", end=u"P") + _ctx(u"Prior1YearInstant", code, instant=u"P")
            + _ctx(u"CurrentYearDuration_Seg", code, start=u"S", end=fy_end, member=u"jppfs_cor:SegMember"))
    body = u"".join(u'<%s contextRef="%s" unitRef="JPY" decimals="-6">%s</%s>' % (n, c, v, n) for n, c, v in facts)
    dei = (u'<jpdei_cor:EDINETCodeDEI contextRef="CurrentYearDuration">%s</jpdei_cor:EDINETCodeDEI><jpdei_cor:CurrentFiscalYearEndDateDEI contextRef="CurrentYearDuration">%s</jpdei_cor:CurrentFiscalYearEndDateDEI>'
           u'<jpdei_cor:AccountingStandardsDEI contextRef="CurrentYearDuration">Japan GAAP</jpdei_cor:AccountingStandardsDEI>' % (code, fy_end))
    xml = XBRL_HEAD + ctxs + dei + body + u"</xbrli:xbrl>"
    bio = io.BytesIO()
    z = zipfile.ZipFile(bio, "w")
    z.writestr("XBRL/PublicDoc/jpcrp030000-asr-001_%s-000_%s_01.xbrl" % (code, fy_end), xml)
    z.close()
    return bio.getvalue()


def build_stub(d):
    u"""3 社: A は組ができ(違う 1・同じ 2・prev にだけ 1・member の枠は除く)、B は窓の中に 140 だけ + 失敗の日が 1 日 → 前年なし(失敗の日あり)、
    C は候補はあるが ZIP でない応答 → 書かずに「ZIP でない応答」。候補には docTypeCode 140 と提出の早い 120 を混ぜる。"""
    os.makedirs(os.path.join(d, "docs"))
    os.makedirs(os.path.join(d, "prior"))
    nextA = make_zip(u"E00001", u"2026-03-31", [(u"jppfs_cor:NetSales", u"CurrentYearDuration", u"150"), (u"jppfs_cor:OperatingIncome", u"CurrentYearDuration", u"250"),
                                               (u"jppfs_cor:Assets", u"CurrentYearInstant", u"350"), (u"jppfs_cor:NetSales", u"Prior1YearDuration", u"100"),
                                               (u"jppfs_cor:OperatingIncome", u"Prior1YearDuration", u"210"), (u"jppfs_cor:Assets", u"Prior1YearInstant", u"300"),
                                               (u"jppfs_cor:NetSales", u"CurrentYearDuration_Seg", u"70"), (u"jppfs_cor:NetSales", u"Prior1YearDuration", u"999")])
    prevA = make_zip(u"E00001", u"2025-03-31", [(u"jppfs_cor:NetSales", u"CurrentYearDuration", u"100"), (u"jppfs_cor:OperatingIncome", u"CurrentYearDuration", u"200"),
                                               (u"jppfs_cor:Assets", u"CurrentYearInstant", u"300"), (u"jppfs_cor:Liabilities", u"CurrentYearInstant", u"50")])
    prevA_old = make_zip(u"E00001", u"2025-03-31", [(u"jppfs_cor:NetSales", u"CurrentYearDuration", u"1")])      # 提出の早い方(選ばれない)
    nextB = make_zip(u"E00002", u"2026-06-30", [(u"jppfs_cor:NetSales", u"CurrentYearDuration", u"1"), (u"jppfs_cor:NetSales", u"Prior1YearDuration", u"1")])
    nextC = make_zip(u"E00003", u"2026-03-31", [(u"jppfs_cor:NetSales", u"CurrentYearDuration", u"5"), (u"jppfs_cor:NetSales", u"Prior1YearDuration", u"4")])
    for name, b in ((u"docs/X100AAAA.zip", nextA), (u"docs/X100BBBB.zip", nextB), (u"docs/X100CCCC.zip", nextC), (u"X100PPPP.zip", prevA), (u"X100OOOO.zip", prevA_old),
                    (u"X100SSSS.zip", b"<html>Access denied</html>")):
        with io.open(os.path.join(d, name), "wb") as fh:
            fh.write(b)
    reg = {u"書類": [{u"docID": u"X100AAAA", u"標本": u"手元の 67", u"zip の sha256": hashlib.sha256(nextA).hexdigest()},
                   {u"docID": u"X100BBBB", u"標本": u"新しい標本 30", u"zip の sha256": hashlib.sha256(nextB).hexdigest()},
                   {u"docID": u"X100CCCC", u"標本": u"手元の 67", u"zip の sha256": hashlib.sha256(nextC).hexdigest()}]}
    with io.open(os.path.join(d, "regress.json"), "w", encoding="utf-8") as fh:
        json.dump(reg, fh, ensure_ascii=False)
    listing = {u"2025-06-25": [{u"docID": u"X100PPPP", u"edinetCode": u"E00001", u"ordinanceCode": u"010", u"docTypeCode": u"120", u"xbrlFlag": u"1", u"periodEnd": u"2025-03-31", u"submitDateTime": u"2025-06-25 15:00"},
                               {u"docID": u"X100QQQQ", u"edinetCode": u"E00001", u"ordinanceCode": u"010", u"docTypeCode": u"140", u"xbrlFlag": u"1", u"submitDateTime": u"2025-06-25 16:00"}],
               u"2025-06-20": [{u"docID": u"X100OOOO", u"edinetCode": u"E00001", u"ordinanceCode": u"010", u"docTypeCode": u"120", u"xbrlFlag": u"1", u"periodEnd": u"2025-03-31", u"submitDateTime": u"2025-06-20 10:00"}],
               u"2025-09-01": [{u"docID": u"X100RRRR", u"edinetCode": u"E00002", u"ordinanceCode": u"010", u"docTypeCode": u"140", u"xbrlFlag": u"1", u"submitDateTime": u"2025-09-01 10:00"}],   # E00002 は窓の中に 140(四半期)だけ
               u"2025-09-10": u"FAIL",                                                                                                                                            # E00002 の窓の中の失敗の日
               u"2025-06-27": [{u"docID": u"X100SSSS", u"edinetCode": u"E00003", u"ordinanceCode": u"010", u"docTypeCode": u"120", u"xbrlFlag": u"1", u"periodEnd": u"2025-03-31", u"submitDateTime": u"2025-06-27 10:00"}]}   # C の候補(ZIP でない応答)
    with io.open(os.path.join(d, "listing.json"), "w", encoding="utf-8") as fh:
        json.dump(listing, fh, ensure_ascii=False)
    return d


def script_problems(src):
    p = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS or (a.name.startswith("adapters") and a.name not in ALLOWED_ENGINE):
                    p.append(u"import %s" % a.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[0] not in ALLOWED_IMPORTS or (mod.startswith("adapters") and mod not in ALLOWED_ENGINE):
                p.append(u"from %s import" % mod)
            elif mod.startswith("adapters"):
                for a in node.names:
                    if "%s.%s" % (mod, a.name) not in ALLOWED_ENGINE:
                        p.append(u"from %s import %s" % (mod, a.name))
    for bad in ("core", "audit_core", "requests", "socket", "http"):
        if re.search(r"^\s*(import|from)\s+%s\b" % bad, src, re.M):
            p.append(u"%s を import" % bad)
    hosts = set(re.findall(r"https?://([A-Za-z0-9.\-]+)", src))
    if hosts != {"api.edinet-fsa.go.jp"}:
        p.append(u"通信先が EDINET API 以外: %s" % sorted(hosts))
    if re.search(r"print\([^)]*environ", src) or re.search(r"environ\[KEY_NAME\]\s*\)", src.replace(" ", "")) and False:
        p.append(u"鍵の値を print")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        is_open = (isinstance(node.func, ast.Attribute) and node.func.attr == "open") or (isinstance(node.func, ast.Name) and node.func.id == "open")
        if not is_open or not node.args:
            continue
        modes = [a.value for a in node.args[1:2] if isinstance(a, ast.Constant)] + [k.value.value for k in node.keywords if k.arg == "mode" and isinstance(k.value, ast.Constant)]
        if any(str(m).startswith(("w", "a", "x")) or "+" in str(m) for m in modes):
            target = ast.get_source_segment(src, node.args[0])
            if target not in ("p", "out_path"):
                p.append(u"決めた出力の外に書く: %s" % target)
    if "EXISTING_CACHE" in src and re.search(r"os\.makedirs\((EXISTING_CACHE|FRESH_DIR)", src):
        p.append(u"既存の cache を作る")
    return p


def added_commits(path):
    rc, out = git("log", "--diff-filter=A", "--format=%H", "--", path)
    return [l for l in out.splitlines() if l.strip()] if rc == 0 else []


def is_anc(a, b):
    return a is not None and b is not None and git("merge-base", "--is-ancestor", a, b)[0] == 0


def order_problems():
    p = []
    s = added_commits(PREFIX + SEAL_REL)
    if len(s) != 1 or not HEX40.match(s[0]):
        return [u"封を足した commit がちょうど 1 つに決まらない(%d)" % len(s)]
    S = s[0]
    if not S.startswith(SEAL_COMMIT_SHORT):
        p.append(u"封の commit が %s でない" % SEAL_COMMIT_SHORT)
    if not is_anc(S, "HEAD"):
        p.append(u"封の commit が HEAD の祖先でない")
    for rel in (SCRIPT_REL, REC_REL, GATE_REL):
        if not os.path.exists(os.path.join(ROOT, rel)):
            continue
        a = added_commits(PREFIX + rel)
        if not a:
            p.append(u"%s を足した commit が無い(未 commit)" % rel)
            continue
        if a[-1] == S or not is_anc(S, a[-1]):
            p.append(u"%s が封の後でない" % rel)
    return p


# ================================================================ tests

class ScriptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load(SCRIPT, "prior_pairs_under_test")
        cls.seal = jtext(SEAL)
        cls.bounds = seal_bounds(cls.seal)
        cls.tmp = tempfile.mkdtemp(prefix="prior_stub_")
        build_stub(cls.tmp)
        cls.out = os.path.join(cls.tmp, "prior_pairs.json")
        cls.rec = cls.mod.run(cls.mod.StubBackend(cls.tmp), os.path.join(cls.tmp, "regress.json"), cls.out,
                              sample_dir={u"手元の 67": os.path.join(cls.tmp, "docs"), u"新しい標本 30": os.path.join(cls.tmp, "docs")},
                              prior_dir=os.path.join(cls.tmp, "prior"), extra={}, require_97=False)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_a_1_seal_widths_and_script_constants(self):
        self.assertEqual(dict(self.bounds), {u"F-2": (75, 97), u"F-3": (150, 400), u"F-4": (1.0, 15.0), u"F-5": (30.0, 80.0), u"F-11": 50.0})
        m = self.mod
        self.assertEqual(dict(m.BOUNDS), dict(self.bounds))
        self.assertEqual(m.SEAL_COMMIT, SEAL_COMMIT_SHORT)
        self.assertEqual(m.SEAL_REL, SEAL_REL)
        self.assertEqual(m.OUT_REL, REC_REL)
        self.assertEqual(tuple(m.WINDOW), (60, 110))
        self.assertEqual((m.ORDINANCE, m.DOCTYPE), ("010", "120"))
        self.assertEqual(dict(m.EXTRA), {u"E01777": [u"2025-03-31", u"2026-03-31"]})
        self.assertIn(u"`~/.cache/audit-core/edinet-prior-2026-11-02/`", self.seal)
        self.assertTrue(m.PRIOR_DIR.endswith("edinet-prior-2026-11-02"))
        self.assertNotEqual(m.PRIOR_DIR, m.EXISTING_CACHE)
        self.assertNotEqual(m.PRIOR_DIR, m.FRESH_DIR)

    def test_a_2_script_imports_hosts_and_writes(self):
        src = jtext(SCRIPT)
        self.assertEqual(script_problems(src), [])
        self.assertNotIn(u"print(os.environ", src)
        self.assertEqual(DOCID_RE.findall(src), [])

    def test_b_1_dei_from_the_real_filing_and_the_synthetic_one(self):
        with io.open(os.path.join(ROOT, "fixtures/xbrl/ai_prose_instance_2026-10-09.zip"), "rb") as fh:
            dei = self.mod.read_dei(fh.read())
        self.assertEqual((dei[u"edinet_code"], dei[u"fy_end"], dei[u"standard"], dei[u"consolidated"], dei[u"xbrl"]), (u"E36539", u"2026-06-30", u"Japan GAAP", u"true", True))
        d2 = self.mod.read_dei(make_zip(u"E00009", u"2026-12-31", []))
        self.assertEqual((d2[u"edinet_code"], d2[u"fy_end"]), (u"E00009", u"2026-12-31"))

    def test_b_2_days_window_and_prior_selection(self):
        days = self.mod.days_for(u"2026-03-31")
        self.assertEqual((days[0], days[-1], len(days)), (u"2025-05-30", u"2025-07-19", 51))
        self.assertEqual(self.mod.days_for(u"2024-02-29")[0], u"2023-04-29")
        pair = [p for p in self.rec[u"組"] if p[u"EDINET コード"] == u"E00001"][0]
        self.assertEqual((pair[u"状態"], pair[u"prev の docID"], pair[u"候補の数"]), (u"組", u"X100PPPP", 2))     # 140 は除き、提出の遅い 120 を選ぶ
        other = [p for p in self.rec[u"組"] if p[u"EDINET コード"] == u"E00002"][0]
        self.assertEqual((other[u"状態"], other[u"候補の数"], other[u"失敗した日"]), (u"前年なし(失敗の日あり)", 0, 1))   # 窓の中は 140 だけ + 失敗の日 1
        self.assertEqual(self.rec[u"集計"][u"呼び出し"][u"日付一覧の回数"], 102)                                 # 51 日 × 2 種の末日(A と C は同じ末日で日を共有)

    def test_b_5_failed_days_and_non_zip_responses_are_counted_not_hidden(self):
        u"""監査 2026-11-02 の指摘: 失敗した日が「前年なし」に静かに化けない。ZIP でない応答は書かない。"""
        T = self.rec[u"集計"]
        self.assertEqual((T[u"呼び出し"][u"失敗した日の数"], T[u"呼び出し"][u"ZIP でない応答"]), (1, 1))
        self.assertEqual(T[u"呼び出し"][u"日付一覧の status の内訳"].get(u"500"), 1)
        self.assertEqual((T[u"前年なし"], T[u"前年なし(失敗の日あり)"]), (0, 1))
        c = [p for p in self.rec[u"組"] if p[u"EDINET コード"] == u"E00003"][0]
        self.assertEqual((c[u"状態"], c[u"prev の docID"]), (u"ZIP でない応答", u"X100SSSS"))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "prior", "X100SSSS.zip")))                    # 書かない(次回「既に在った」にならない)
        self.assertEqual([f[u"取得"] for f in self.rec[u"取得"] if f[u"docID"] == u"X100SSSS"], [u"ZIP でない応答(書かない)"])
        self.assertFalse(self.rec[u"配線の門"][u"通った"])                                                      # 失敗の日があるので配線は通らない
        self.assertEqual(self.rec[u"配線の門"][u"(e) 日付一覧に失敗した日"], 1)
        self.assertEqual(dict(self.rec[u"状態の内訳"] if u"状態の内訳" in self.rec else T[u"状態の内訳"]), {u"組": 1, u"前年なし(失敗の日あり)": 1, u"ZIP でない応答": 1})

    def test_b_3_pairing_rules(self):
        pair = [p for p in self.rec[u"組"] if p[u"EDINET コード"] == u"E00001"][0][u"突き合わせ"]
        self.assertEqual((pair[u"結べた要素"], pair[u"同じ"], pair[u"違う"], pair[u"prev にだけ"], pair[u"next にだけ"]), (3, 2, 1, 1, 0))
        self.assertEqual(pair[u"重なり(next)"], 1)                                   # Prior1YearDuration の NetSales が 2 つ → 最初の 1 つ
        self.assertEqual(pair[u"違う要素"][0][u"要素"], u"jppfs_cor:OperatingIncome")
        self.assertEqual(pair[u"違う要素"][0][u"差の割合"], 0.05)
        T = self.rec[u"集計"]
        self.assertEqual((T[u"違うの合計"], T[u"結べた要素の合計"], T[u"違う割合(%)"]), (1, 3, 33.33))
        self.assertEqual(self.rec[u"key_leaks"], [])
        self.assertEqual(self.rec[u"配線の門"][u"(c) engine の未 commit の file"], 0)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "prior", "X100PPPP.zip")))
        self.assertEqual(sorted(os.listdir(os.path.join(self.tmp, "docs"))), [u"X100AAAA.zip", u"X100BBBB.zip", u"X100CCCC.zip"])   # 手元の dir には書かない

    def test_b_4_record_shape_and_judge(self):
        for k in (u"注意", u"封", u"HEAD の commit", u"この script の sha256", u"読んだ材料の sha256", u"engine の bundle の sha256(core/・adapters/)", u"定数", u"配線の門",
                  u"書類(手元の 97)", u"組", u"固定の確認", u"取得", u"集計", u"予測の判定", u"limits", u"key_leaks"):
            self.assertIn(k, self.rec)
        self.assertEqual(self.rec[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        J = self.rec[u"予測の判定"]
        self.assertEqual(J[u"当たり"] + J[u"外れ"], 6)
        self.assertEqual(J[u"F-10(段 1 の部分)"], u"判定しない(書類が揃わない)")
        T = dict(self.rec[u"集計"])
        T.update({u"97 書類の sha256 が記録と一致": 97, u"DEI が読めた": 97, u"前年の有報が見つかった会社": 80, u"結べた要素の中央値": 200, u"違う割合(%)": 3.0,
                  u"違う要素が 1 つ以上ある組の割合(%)": 50.0, u"違う要素のうち差が 5% 未満の割合(%)": 60.0})
        self.assertEqual([self.mod.judge(T)[k] for k in (u"F-1", u"F-2", u"F-3", u"F-4", u"F-5", u"F-11")], [u"当たり"] * 6)
        T[u"違う割合(%)"] = 0.5
        self.assertEqual(self.mod.judge(T)[u"F-4"], u"外れ")

    def test_c_1_seal_unchanged_since_its_commit(self):
        rc, committed = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL))
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(committed.rstrip(u"\n"), self.seal.rstrip(u"\n"), u"**封が結果の後で変わっている**")

    def test_c_2_order(self):
        rc, _ = git("cat-file", "-e", SEAL_COMMIT_SHORT + "^{commit}")
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(order_problems(), [])


class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(REC):
            raise unittest.SkipTest(u"記録 %s が無い(鍵のある席で段 1 を走らせると出来る)" % REC_REL)
        cls.rec = jload(REC)
        cls.mod = load(SCRIPT, "prior_pairs_under_test_rec")
        cls.bounds = seal_bounds(jtext(SEAL))

    def test_a_1_shape(self):
        self.assertEqual(self.rec[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertTrue(HEX40.match(self.rec[u"HEAD の commit"] or u""))
        with io.open(SCRIPT, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), self.rec[u"この script の sha256"])
        self.assertEqual(self.rec[u"key_leaks"], [])
        self.assertTrue(self.rec[u"配線の門"][u"通った"])
        self.assertEqual(len(self.rec[u"書類(手元の 97)"]), 97)
        self.assertEqual(self.rec[u"集計"][u"97 書類の sha256 が記録と一致"], 97)
        fb = load(os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py"), "frozen_bundle_sha_for_prior_gate")
        self.assertEqual(self.rec[u"engine の bundle の sha256(core/・adapters/)"], "864b1f96292f1615c7e5b7e3bbd6924ebd9955b8354b3c5d51400ba9a01fb054")   # 2026-11-02: 測った時点の世代(候補の欄を足した世代)を字で留める。最新の世代は「その他」の主語の結び直し(封 XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02)で動いた
        self.assertIn("864b1f96292f1615c7e5b7e3bbd6924ebd9955b8354b3c5d51400ba9a01fb054", [g[0] for g in fb.FROZEN_BUNDLE_GENERATIONS])
        self.assertNotIn(u"Subscription-Key", json.dumps(self.rec, ensure_ascii=False))

    def test_b_1_tally_recomputed(self):
        got = [p for p in self.rec[u"組"] if p[u"状態"] == u"組"]
        T = self.rec[u"集計"]
        self.assertEqual(T[u"前年の有報が見つかった会社"], len(got))
        self.assertEqual(T[u"結べた要素の合計"], sum(p[u"突き合わせ"][u"結べた要素"] for p in got))
        self.assertEqual(T[u"違うの合計"], sum(p[u"突き合わせ"][u"違う"] for p in got))
        self.assertEqual(T[u"同じの合計"] + T[u"違うの合計"], T[u"結べた要素の合計"])
        for p in got:
            x = p[u"突き合わせ"]
            self.assertEqual(x[u"違う"], len(x[u"違う要素"]))
        rels = [r[u"差の割合"] for p in got for r in p[u"突き合わせ"][u"違う要素"] if r[u"差の割合"] is not None]
        self.assertEqual(T[u"違う要素のうち差が 5% 未満"], sum(1 for x in rels if x < 0.05))
        self.assertEqual(dict(self.mod.judge(T)), dict(self.rec[u"予測の判定"]))


class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load(SCRIPT, "prior_pairs_under_test_mut")
        cls.seal = jtext(SEAL)

    def test_m_1_changed_value_changes_pairing(self):
        from adapters.xbrl import instance as I
        prev = I.load_instance(make_zip(u"E1", u"2025-03-31", [(u"jppfs_cor:NetSales", u"CurrentYearDuration", u"100")]))
        same = I.load_instance(make_zip(u"E1", u"2026-03-31", [(u"jppfs_cor:NetSales", u"Prior1YearDuration", u"100")]))
        diff = I.load_instance(make_zip(u"E1", u"2026-03-31", [(u"jppfs_cor:NetSales", u"Prior1YearDuration", u"101")]))
        self.assertEqual((self.mod.pair_elements(prev, same)[u"同じ"], self.mod.pair_elements(prev, same)[u"違う"]), (1, 0))
        self.assertEqual((self.mod.pair_elements(prev, diff)[u"同じ"], self.mod.pair_elements(prev, diff)[u"違う"]), (0, 1))
        cur = I.load_instance(make_zip(u"E1", u"2026-03-31", [(u"jppfs_cor:NetSales", u"CurrentYearDuration", u"100")]))     # next の当期欄は見ない
        self.assertEqual(self.mod.pair_elements(prev, cur)[u"結べた要素"], 0)
        seg = I.load_instance(make_zip(u"E1", u"2025-03-31", [(u"jppfs_cor:NetSales", u"CurrentYearDuration_Seg", u"100")]))   # member の枠は除く
        self.assertEqual(self.mod.pair_elements(seg, same)[u"結べた要素"], 0)

    def test_m_2_seal_width_change_changes_bounds(self):
        bad = self.seal.replace(u"**1〜15%**", u"**1〜50%**")
        self.assertNotEqual(bad, self.seal)
        self.assertNotEqual(seal_bounds(bad)[u"F-4"], seal_bounds(self.seal)[u"F-4"])

    def test_m_3_bad_imports_hosts_and_writes_are_caught(self):
        src = jtext(SCRIPT)
        self.assertNotEqual(script_problems(src + u"\nfrom adapters.xbrl import verify_document\n"), [])
        self.assertNotEqual(script_problems(src + u"\nimport requests\n"), [])
        self.assertNotEqual(script_problems(src + u'\nX = "https://example.com/x"\n'), [])
        self.assertNotEqual(script_problems(src + u'\nio.open(os.path.join(EXISTING_CACHE, "x.zip"), "wb")\n'), [])
        self.assertNotEqual(script_problems(src + u'\nos.makedirs(EXISTING_CACHE)\n'), [])

    def test_m_4_prior_selection_prefers_later_and_filters_type(self):
        class B(object):
            calls = []
            def list_day(self, day):
                return {u"status": 200, u"results": [
                    {u"docID": u"X100AAAA", u"edinetCode": u"E1", u"ordinanceCode": u"010", u"docTypeCode": u"120", u"xbrlFlag": u"1", u"submitDateTime": u"2025-06-20 10:00"},
                    {u"docID": u"X100BBBB", u"edinetCode": u"E1", u"ordinanceCode": u"010", u"docTypeCode": u"120", u"xbrlFlag": u"1", u"submitDateTime": u"2025-06-25 10:00"},
                    {u"docID": u"X100CCCC", u"edinetCode": u"E1", u"ordinanceCode": u"010", u"docTypeCode": u"130", u"xbrlFlag": u"1", u"submitDateTime": u"2025-06-30 10:00"},
                    {u"docID": u"X100DDDD", u"edinetCode": u"E2", u"ordinanceCode": u"010", u"docTypeCode": u"120", u"xbrlFlag": u"1", u"submitDateTime": u"2025-06-30 10:00"}] if day == u"2025-06-25" else []}
        cands, failed = self.mod.find_prior(u"E1", u"2026-03-31", B(), {})
        self.assertEqual(([c[u"docID"] for c in cands], failed), ([u"X100AAAA", u"X100BBBB"], 0))
        self.assertEqual(self.mod.find_prior(u"E3", u"2026-03-31", B(), {}), ([], 0))

        class Down(object):
            calls = []
            def list_day(self, day):
                return {u"status": 429, u"results": [], u"ok": False}
        self.assertEqual(self.mod.find_prior(u"E1", u"2026-03-31", Down(), {}), ([], 51))                     # 全日失敗 → 候補 0・失敗 51(前年なしと区別)


# ================================================================ 段 2(注入と規則 R。封 §2・§3 の F-6〜F-10)

S2_SCRIPT_REL = "measure/xbrl_restated_naming_2026-11-02.py"
S2_REC_REL = "fixtures/xbrl/restated_naming_2026-11-02.json"
RESULT_REL = "docs/XBRL_RESTATED_PRIOR_RESULT_2026-11-02.md"
S2_SCRIPT, S2_REC, RESULT = (os.path.join(ROOT, r) for r in (S2_SCRIPT_REL, S2_REC_REL, RESULT_REL))
S2_ALLOWED_IMPORTS = {"argparse", "collections", "decimal", "hashlib", "importlib", "io", "json", "multiprocessing", "os", "re", "sys", "time", "types", "unicodedata", "__future__", "adapters"}
S2_ALLOWED_ENGINE = {"adapters.xbrl", "adapters.xbrl.comparators", "adapters.xbrl.extract", "adapters.xbrl.instance", "adapters.xbrl.prose", "adapters.xbrl.recipes",
                     "adapters.xbrl.verify_document", "adapters.xbrl.vocabulary"}
S2_BANNED_NAMES = {"ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS"}
FORBIDDEN_WORDS = (u"精度", u"ハルシネーション", u"証明", u"LLM より正確", u"世界で 1 社", u"唯一", u"正確", u"保証", u"貴社の DB の誤り")
COMPANY_NAMES = (u"ソニー", u"Sony", u"SONY", u"Cabocia", u"カボシア")


def seal_bounds_s2(seal):
    rows = seal_rows(seal)
    b = collections.OrderedDict()
    m = re.search(r"\*\*(\d+)〜(\d+)\*\*", rows[u"F-6"][0])
    b[u"F-6"] = (int(m.group(1)), int(m.group(2)))
    for k, w in ((u"F-7", u"以上"), (u"F-8", u"以上"), (u"F-9", u"以下")):
        m = re.search(r"\*\*(\d+)%% %s\*\*" % w, rows[k][0])
        b[k] = int(m.group(1))
    return b


def script2_problems(src):
    u"""段 2 の script の import・通信・書く先。"""
    p = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in S2_ALLOWED_IMPORTS or (a.name.startswith("adapters") and a.name not in S2_ALLOWED_ENGINE):
                    p.append(u"import %s" % a.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[0] not in S2_ALLOWED_IMPORTS or (mod.startswith("adapters") and mod not in S2_ALLOWED_ENGINE):
                p.append(u"from %s import" % mod)
            elif mod.startswith("adapters"):
                for a in node.names:
                    if "%s.%s" % (mod, a.name) not in S2_ALLOWED_ENGINE:
                        p.append(u"from %s import %s" % (mod, a.name))
    for bad in ("core", "audit_core", "requests", "socket", "http", "urllib", "shutil"):
        if re.search(r"^\s*(import|from)\s+%s\b" % bad, src, re.M):
            p.append(u"%s を import" % bad)
    if re.findall(r"https?://", src):
        p.append(u"通信先の字")
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Call):
            continue
        is_open = (isinstance(node.func, ast.Attribute) and node.func.attr == "open") or (isinstance(node.func, ast.Name) and node.func.id == "open")
        if is_open and node.args:
            modes = [a.value for a in node.args[1:2] if isinstance(a, ast.Constant)] + [k.value.value for k in node.keywords if k.arg == "mode" and isinstance(k.value, ast.Constant)]
            if any(str(m).startswith(("w", "a", "x")) or "+" in str(m) for m in modes):
                target = ast.get_source_segment(src, node.args[0])
                if target != "out_path":
                    p.append(u"決めた出力の外に書く: %s" % target)
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("makedirs", "mkdir", "remove", "unlink", "rename", "rmtree", "write_text", "write_bytes"):
            p.append(u"file を作る・消す呼び出し: %s" % node.func.attr)
    return p


def make_doc2(fy_end, lines, facts):
    u"""作り物の有報: MD&A の文(lines)と facts([(要素, 枠の id, 値)])。"""
    from xml.sax.saxutils import escape
    head = XBRL_HEAD.replace(u'xmlns:link=', u'xmlns:jpcrp_cor="http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/jpcrp_cor" xmlns:link=')
    ctxs = (_ctx(u"CurrentYearDuration", u"E1", start=u"2024-04-01", end=fy_end) + _ctx(u"CurrentYearInstant", u"E1", instant=fy_end)
            + _ctx(u"Prior1YearDuration", u"E1", start=u"2023-04-01", end=u"2024-03-31") + _ctx(u"Prior1YearInstant", u"E1", instant=u"2024-03-31"))
    body = u"".join(u'<%s contextRef="%s" unitRef="JPY" decimals="-6">%s</%s>' % (n, c, v, n) for n, c, v in facts)
    tb = escape(u"\n".join(u"<p>%s</p>" % escape(l) for l in lines))
    name = u"jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock"
    xml = head + ctxs + u'<%s contextRef="CurrentYearDuration">%s</%s>' % (name, tb, name) + body + u"</xbrli:xbrl>"
    bio = io.BytesIO()
    z = zipfile.ZipFile(bio, "w")
    z.writestr("XBRL/PublicDoc/jpcrp030000-asr-001_E1-000_%s_01.xbrl" % fy_end, xml)
    z.close()
    return bio.getvalue()


STUB_LINES = [u"当連結会計年度の売上高は309,240百万円となりました。", u"営業利益は1,159百万円となりました。", u"経常利益は2,000百万円となりました。",
              u"売上総利益は5,000百万円となりました。", u"当期純利益は9,999百万円となりました。"]


def build_stub2(d, mod):
    u"""prev 1 書類・next 1 書類。営業利益は next で値が違い(site)、経常利益は違うが百万円の桁では同じ(差が桁の中)、売上総利益は文が prev の値と合わず(止まる)
    next の前期の値と合う(対照で名指す)、当期純利益は止まるが next とも合わない(対照で名指さない)。next の file の先頭に要約の要素(jpcrp_cor)を置く(並びの確認)。"""
    os.makedirs(os.path.join(d, "prev"))
    os.makedirs(os.path.join(d, "next"))
    D = u"jppfs_cor:"
    prevb = make_doc2(u"2025-03-31", STUB_LINES, [(D + u"NetSales", u"CurrentYearDuration", u"309240000000"), (D + u"OperatingIncome", u"CurrentYearDuration", u"1159040000"),
                                                (D + u"OrdinaryIncome", u"CurrentYearDuration", u"2000300000"), (D + u"GrossProfit", u"CurrentYearDuration", u"4000000000"),
                                                (D + u"ProfitLoss", u"CurrentYearDuration", u"1000000000")])
    nextb = make_doc2(u"2026-03-31", [u"本文は使わない。"], [(u"jpcrp_cor:OperatingIncomeSummaryOfBusinessResults", u"Prior1YearDuration", u"1157006000"),
                                                       (D + u"NetSales", u"Prior1YearDuration", u"309240000000"), (D + u"OperatingIncome", u"Prior1YearDuration", u"1157006000"),
                                                       (D + u"OrdinaryIncome", u"Prior1YearDuration", u"2000400000"), (D + u"GrossProfit", u"Prior1YearDuration", u"5000000000"),
                                                       (D + u"ProfitLoss", u"Prior1YearDuration", u"1000000000")])
    for name, b in ((u"prev/X200PREV.zip", prevb), (u"next/X200NEXT.zip", nextb)):
        with io.open(os.path.join(d, name), "wb") as fh:
            fh.write(b)
    from adapters.xbrl import instance as I
    pair = mod.P1.pair_elements(I.load_instance(prevb), I.load_instance(nextb))
    stage1 = {u"配線の門": {u"通った": True}, u"engine の bundle の sha256(core/・adapters/)": mod.P1.engine_bundle()[0],
              u"取得": [{u"docID": u"X200PREV", u"sha256": hashlib.sha256(prevb).hexdigest()}],
              u"書類(手元の 97)": [{u"docID": u"X200NEXT", u"標本": u"手元の 67", u"sha256(記録)": hashlib.sha256(nextb).hexdigest()}],
              u"組": [{u"状態": u"組", u"prev の docID": u"X200PREV", u"next の docID": u"X200NEXT", u"突き合わせ": pair}], u"固定の確認": []}
    with io.open(os.path.join(d, "stage1.json"), "w", encoding="utf-8") as fh:
        json.dump(stage1, fh, ensure_ascii=False)
    return d


def labels_missing(mod):
    return bool(mod.check_labels(os.path.join(ROOT, "fixtures/xbrl/taxonomy_labels_sha256.txt"))[1])


def walk_numbers(obj, ints, decs):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        if float(obj).is_integer():
            ints.add(int(obj))
        if isinstance(obj, float):
            decs.add(repr(obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            walk_numbers(v, ints, decs)
    elif isinstance(obj, list):
        for v in obj:
            walk_numbers(v, ints, decs)


def doc_cells(doc):
    u"""2 列の表の行: ラベル → 値の字。"""
    out = collections.OrderedDict()
    for l in doc.splitlines():
        m = re.match(r"^\| ([^|]+?) \| ([^|]+?) \|$", l)
        if m and not set(m.group(1)) <= set(u"-") and m.group(1) not in (u"項目",):
            out[m.group(1)] = m.group(2)
    return out


def doc_keyrows(r1, r2):
    u"""文書の 2 列の表のうち、記録の字と照らす行(ラベル → 記録の字)。"""
    T1, T2 = r1[u"集計"], r2[u"集計"]
    C, SG, G2, F10 = T2[u"対照"], T2[u"site の絞り込み"], r2[u"配線の門"], r2[u"固定の確認 F-10"][u"項目"]
    D = T1[u"差の分布(件)"]
    sit_docs = len(set(s[u"prev の docID"] for s in r2[u"site の行"]))
    inb_docs = sum(1 for d in r2[u"書類ごと"] if d[u"site の絞り込み"].get(u"差が桁の中"))
    g = G2[u"(b) prev・next の ZIP の sha256 が段 1 の記録と一致した本数"]
    return collections.OrderedDict([
        (u"prev の ZIP の sha256 が段 1 の記録と一致した本数(92 + E01777 の 1)", g[u"prev"]),
        (u"next の ZIP の sha256 が段 1 の記録と一致した本数(92 + E01777 の 1)", g[u"next"]),
        (u"ラベル file が名簿と一致", G2[u"(c) ラベル file が名簿と一致(取り出しの場所は記録しない)"]),
        (u"engine の未 commit の file", G2[u"(d) engine の未 commit の file"]),
        (u"engine の bundle の sha256 が段 1 の記録と同じ", G2[u"(d') engine の bundle の sha256 が段 1 の記録と同じ"]),
        (u"文を渡した結果が渡さない結果と一致しなかった書類", G2[u"(e) 文を渡した結果が渡さない結果と一致しなかった書類"]),
        (u"本文 W が不動点に届かなかった書類", G2[u"(e') W が不動点に届かなかった書類"]),
        (u"戻して W と一致しなかった site", G2[u"(f) 戻して W と一致しなかった site"]),
        (u"R の params を engine の欄と照らした回数", G2[u"(g) R の params を照らした回数"]),
        (u"R の params が engine の欄と一致しなかった回数", G2[u"(g) R の params が engine の欄と一致しなかった回数"]),
        (u"既存の cache の件数が前後で同じ", G2[u"(h) 既存の cache の件数が前後で同じ"]),
        (u"通った", G2[u"通った"]),
        (u"前年の有報が見つかった会社(組)", T1[u"前年の有報が見つかった会社"]), (u"前年なし", T1[u"前年なし"]), (u"結べた要素の中央値(組ごと)", T1[u"結べた要素の中央値"]),
        (u"結べた要素の合計", T1[u"結べた要素の合計"]), (u"同じの合計", T1[u"同じの合計"]), (u"違うの合計", T1[u"違うの合計"]), (u"違う割合(%)", T1[u"違う割合(%)"]),
        (u"違う要素が 1 つ以上ある組", T1[u"違う要素が 1 つ以上ある組"]), (u"違う要素が 1 つ以上ある組の割合(%)", T1[u"違う要素が 1 つ以上ある組の割合(%)"]),
        (u"違う要素のうち差が比べられる", T1[u"違う要素のうち差が比べられる"]), (u"違う要素のうち差が 5% 未満", T1[u"違う要素のうち差が 5% 未満"]),
        (u"違う要素のうち差が 5% 未満の割合(%)", T1[u"違う要素のうち差が 5% 未満の割合(%)"]),
        (u"差 1% 未満", D[u"1% 未満"]), (u"差 1〜5% 未満", D[u"1〜5% 未満"]), (u"差 5〜20% 未満", D[u"5〜20% 未満"]), (u"差 20% 以上", D[u"20% 以上"]),
        (u"数の claim", SG[u"数の claim"]), (u"GROUNDED の数の claim", SG[u"GROUNDED の数の claim"]), (u"形・単位・pointer の本数が条件外", SG[u"形・単位・pointer の本数が条件外"]),
        (u"pointer の枠が当期(member なし)でない", SG[u"pointer の枠が当期(member なし)でない"]), (u"要素が段 1 の違うに入らない", SG[u"要素が段 1 の違うに入らない"]),
        (u"差が桁の中で除いた", T2[u"差が桁の中で除いた"]), (u"字の形を保てない", SG[u"字の形を保てない"]), (u"注入した site", T2[u"注入した site"]),
        (u"site が出た書類", sit_docs), (u"差が桁の中が出た書類", inb_docs),
        (u"対応が付かない", T2[u"対応が付かない"]), (u"通した(GROUNDED)", T2[u"通した(GROUNDED)"]), (u"止めた", T2[u"止めた"]), (u"止めた割合(%)", T2[u"止めた割合(%)"]),
        (u"止めた VALUE_MISMATCH", T2[u"止めた state の内訳"][u"VALUE_MISMATCH"]), (u"止めた UNVERIFIABLE", T2[u"止めた state の内訳"][u"UNVERIFIABLE"]),
        (u"止めた POINTER_NOT_FOUND", T2[u"止めた state の内訳"][u"POINTER_NOT_FOUND"]), (u"R が名指した", T2[u"R が名指した"]), (u"名指しの割合(%)", T2[u"名指しの割合(%)"]),
        (u"名指しの要素が注入した要素と同じ", T2[u"名指しの要素が注入した要素と同じ"]), (u"R が名指さなかった(手書きの主語の行に無い)", T2[u"止めた"] - T2[u"R が名指した"]),
        (u"対照: 止めた行", C[u"止めた行"]), (u"対照: VALUE_MISMATCH", C[u"止めた行の state"][u"VALUE_MISMATCH"]), (u"対照: UNVERIFIABLE", C[u"止めた行の state"][u"UNVERIFIABLE"]),
        (u"対照: POINTER_NOT_FOUND", C[u"止めた行の state"][u"POINTER_NOT_FOUND"]), (u"対照: R が名指した", C[u"R が名指した"]), (u"対照: 名指しの割合(%)", C[u"名指しの割合(%)"]),
        (u"対照: R が言える形の行", C[u"R が言える形の行"]), (u"対照: 言える形の行での名指しの割合(%)(参考)", C[u"言える形の行での名指しの割合(%)(参考)"]),
    ])


def doc_judgments(r1, r2):
    J1, J2 = r1[u"予測の判定"], r2[u"予測の判定"]
    return collections.OrderedDict([(u"F-1", J1[u"F-1"]), (u"F-2", J1[u"F-2"]), (u"F-3", J1[u"F-3"]), (u"F-4", J1[u"F-4"]), (u"F-5", J1[u"F-5"]), (u"F-6", J2[u"F-6"]),
                                    (u"F-7", J2[u"F-7"]), (u"F-8", J2[u"F-8"]), (u"F-9", J2[u"F-9"]), (u"F-11", J1[u"F-11"])])


def doc_problems(doc, r1, r2, seal):
    u"""結果の文書の数・判定・禁止語。問題の列。"""
    p = []
    for w in FORBIDDEN_WORDS + COMPANY_NAMES:
        if w in doc:
            p.append(u"禁止語・会社名: %s" % w)
    for h in (u"## §1 ", u"## §2 ", u"## §3 ", u"## §4 ", u"## §5 ", u"## §6 ", u"## §7 ", u"### 独立監査の結果"):
        if h not in doc:
            p.append(u"見出し %s が無い" % h)
    cells = doc_cells(doc)
    for label, want in doc_keyrows(r1, r2).items():
        got = cells.get(label)
        if got is None:
            p.append(u"表の行が無い: %s" % label)
            continue
        if isinstance(want, bool):
            ok = got == str(want)
        else:
            try:
                ok = float(got.replace(",", "")) == float(want)
            except ValueError:
                ok = False
        if not ok:
            p.append(u"表の数が記録と違う: %s = %s(記録 %s)" % (label, got, want))
    for k, w in doc_judgments(r1, r2).items():
        m = re.search(r"^\| %s \|.*\| ([^|]+) \|$" % re.escape(k), doc, re.M)
        if not m or m.group(1).strip() != w:
            p.append(u"判定が記録と違う: %s" % k)
    ints, decs = set(), set()
    for src in (r1, r2):
        walk_numbers(src, ints, decs)
    for tok in re.findall(r"(?<![A-Za-z0-9_.])\d[\d,]*(?:\.\d+)?", seal):
        n = tok.replace(",", "")
        (decs.add(n) if "." in n else ints.add(int(n)))
    t = doc
    t = re.sub(r"\bS100[0-9A-Z]{4}\b", " ", t)
    t = re.sub(r"\bE\d{5}\b", " ", t)
    t = re.sub(r"\b(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b", " ", t)
    t = re.sub(r"\d{4}-\d{2}-\d{2}", " ", t)
    t = re.sub(r"\b20\d\d\b", " ", t)
    for line in t.splitlines():
        if u"【門なし】" in line:
            continue
        for tok in re.findall(r"(?<![A-Za-z0-9_.])\d[\d,]*(?:\.\d+)?", line):
            n = tok.replace(",", "")
            if "." in n:
                if n not in decs:
                    p.append(u"記録に無い小数: %s" % tok)
            elif len(n.lstrip("0")) >= 3 and int(n) not in ints:
                p.append(u"記録に無い 3 桁以上の数: %s" % tok)
    return p


def order_problems_s2():
    p = []
    s = added_commits(PREFIX + SEAL_REL)
    if len(s) != 1 or not HEX40.match(s[0]):
        return [u"封を足した commit がちょうど 1 つに決まらない(%d)" % len(s)]
    S = s[0]
    prev = None
    for rel in (REC_REL, S2_SCRIPT_REL, S2_REC_REL, RESULT_REL):
        if not os.path.exists(os.path.join(ROOT, rel)):
            prev = None
            continue
        a = added_commits(PREFIX + rel)
        if not a:
            p.append(u"%s を足した commit が無い(未 commit)" % rel)
            prev = None
            continue
        c = a[-1]
        if c == S or not is_anc(S, c):
            p.append(u"%s が封の後でない" % rel)
        # 2026-11-02: script・記録・文書は同じ commit でよい(封 §5 の順は作る順で、commit の順ではない。封より後は厳密に求める)。前の file より前の commit なら赤
        if prev is not None and c != prev[1] and not is_anc(prev[1], c):
            p.append(u"%s が %s の後でない" % (rel, prev[0]))
        prev = (rel, c)
    return p


class Stage2ScriptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load(S2_SCRIPT, "restated_naming_under_test")
        if labels_missing(cls.mod):
            raise unittest.SkipTest(u"ラベル file が無いか名簿と違う(P27 は走らない)")
        cls.seal = jtext(SEAL)
        cls.tmp = tempfile.mkdtemp(prefix="restated_stub_")
        build_stub2(cls.tmp, cls.mod)
        cls.stage1 = os.path.join(cls.tmp, "stage1.json")
        cls.out = os.path.join(cls.tmp, "out1.json")
        cls.rec = cls.mod.run(cls.out, cls.stage1, 1, prev_dir=os.path.join(cls.tmp, "prev"), next_dir=os.path.join(cls.tmp, "next"), cache_dirs={}, say=lambda *a: None)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def stop_without_output(self, out, **kw):
        args = dict(prev_dir=os.path.join(self.tmp, "prev"), next_dir=os.path.join(self.tmp, "next"), cache_dirs={}, say=lambda *a: None)
        args.update(kw)
        existed = os.path.exists(out)
        before = hashlib.sha256(open(out, "rb").read()).hexdigest() if existed else None
        with self.assertRaises(self.mod.Stop):
            self.mod.run(out, args.pop("stage1", self.stage1), args.pop("procs", 1), **args)
        if existed:
            self.assertEqual(hashlib.sha256(open(out, "rb").read()).hexdigest(), before, u"既に在る出力は書き換えない")
        else:
            self.assertFalse(os.path.exists(out), u"止めるときは何も書かない")

    def test_a_1_seal_widths_and_script_constants(self):
        m = self.mod
        self.assertEqual(dict(seal_bounds_s2(self.seal)), {u"F-6": (50, 600), u"F-7": 95, u"F-8": 85, u"F-9": 5})
        self.assertEqual(dict(m.BOUNDS), dict(seal_bounds_s2(self.seal)))
        self.assertEqual((m.SEAL_COMMIT, m.SEAL_REL, m.OUT_REL, m.STAGE1_REL, m.PROFILE, m.MAX_PROCS), (SEAL_COMMIT_SHORT, SEAL_REL, S2_REC_REL, REC_REL, "P27", 4))
        self.assertIn(u"1 兆 2,766 億円", self.seal)
        self.assertIn(u"1,125,588 百万円", self.seal)
        self.assertEqual([(k, v[u"要素"], v[u"書面の桁"], v[u"書面の値(その桁の整数)"]) for k, v in m.ITEMS.items()],
                         [(u"営業利益", u"jpigp_cor:OperatingProfitLossIFRS", u"億円", 12766), (u"減価償却費及び償却費", u"jpigp_cor:DepreciationAndAmortizationOpeCFIFRS", u"百万円", 1125588)])
        self.assertEqual(list(m.P1.EXTRA_ELEMENTS), [v[u"要素"] for v in m.ITEMS.values()])
        self.assertEqual(m.P1.EXTRA, {u"E01777": [u"2025-03-31", u"2026-03-31"]})

    def test_a_2_script_imports_writes_and_banned_names(self):
        src = jtext(S2_SCRIPT)
        self.assertEqual(script2_problems(src), [])
        self.assertEqual(DOCID_RE.findall(src), [])
        self.assertNotIn(u"print(os.environ", src)
        tree = ast.parse(jtext(os.path.join(ROOT, GATE_REL)))
        names = set(t.id for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name))
        names |= set(t.id for n in tree.body if isinstance(n, ast.Assign) for tt in n.targets if isinstance(tt, ast.Tuple) for t in tt.elts if isinstance(t, ast.Name))
        self.assertEqual(names & S2_BANNED_NAMES, set())

    def test_b_1_token_forms_and_rounding(self):
        m = self.mod
        f = m.parse_token(u"1,159百万円")
        self.assertEqual((f[u"形"], f[u"桁区切り"], f[u"小数の桁数"], f[u"単位語"], f[u"body"]), (u"simple", True, 0, u"百万円", (0, 5)))
        self.assertEqual(m.render_body(f, 1157006000.0), u"1,157")                                    # 桁区切りを保つ
        self.assertEqual(m.new_token(u"1,159百万円", f, u"1,157"), u"1,157百万円")
        g = m.parse_token(u"△1,237百万円")
        self.assertEqual(g[u"body"], (1, 6))                                                              # 符号の字は body の外(動かさない)
        self.assertEqual(m.new_token(u"△1,237百万円", g, m.render_body(g, -1500000000.0)), u"△1,500百万円")
        h = m.parse_token(u"951百万円")
        self.assertEqual(m.render_body(h, 1234567000.0), u"1235")                                      # 元に桁区切りが無ければ付けない
        k = m.parse_token(u"12.5億円")
        self.assertEqual((k[u"小数の桁数"], m.render_body(k, 1234567890.0)), (1, u"12.3"))
        self.assertEqual(m.render_body(k, 125000000.0), u"1.3")                                         # 1.25 → 四捨五入(0.5 は上へ)
        c = m.parse_token(u"1兆4,072億円")
        self.assertEqual((c[u"形"], c[u"body"]), (u"cho_oku", (0, 8)))
        self.assertEqual(m.new_token(u"1兆4,072億円", c, m.render_body(c, 1276635000000.0)), u"1兆2,766億円")
        self.assertEqual(m.render_body(c, 53000000000.0), u"530億")                                    # 兆が 0 になれば兆を落とす
        self.assertEqual(m.render_body(m.parse_token(u"2億円"), 450000000.0), u"5")                    # 4.5 → 5(0.5 は上へ。偶数丸めなら 4)
        self.assertEqual(m.render_body(m.parse_token(u"1兆4億円"), 450000000.0), u"5億")
        for bad in (u"19億49百万円", u"5千万円", u"3.5ポイント", u"abc"):
            self.assertIsNone(m.parse_token(bad), bad)
        self.assertEqual(m.render_body(f, 1159040000.0), u"1,159")                                    # 同じ値は同じ字(差が桁の中)

    def test_b_2_rule_r_band_rounding_and_vocabulary(self):
        m = self.mod
        fact = lambda n, v: {"name": n, "value": v, "context": "Prior1YearDuration", "unit": "JPY"}
        nv = {u"docID": u"X200NEXT", u"prior": [fact(u"jppfs_cor:OperatingIncome", 1157800000.0)], u"contexts": {"Prior1YearDuration": {"members": []}}}
        claim = {"form": "direct_value", "unit": u"百万円", "value": 1157.0, "pointers": ["xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration"], "subject": u"営業利益"}
        tup = (0, 7, 1157.0, u"百万円", 1e6)
        r, params = m.rule_r(claim, tup, "round", nv)                                                      # 差 8e5 > 5e5: 四捨五入では外れ
        self.assertEqual((r[u"言う"], r[u"理由"]), (False, u"帯の外"))
        self.assertEqual(params, (1e6, 1e6, False))
        r, _ = m.rule_r(claim, tup, "truncate", nv)                                                        # 切り捨てなら 0 <= 8e5 < 1e6 で帯の中
        self.assertEqual((r[u"言う"], r[u"要素"], r[u"帯"]), (True, u"jppfs_cor:OperatingIncome", u"truncate"))
        nv[u"prior"] = [fact(u"jppfs_cor:OperatingIncome", 1157006000.0)]
        r, _ = m.rule_r(claim, tup, "round", nv)
        self.assertEqual((r[u"言う"], r[u"理由"], r[u"帯"]), (True, u"翌期の有報の前期欄と一致", u"round"))
        nv[u"prior"] = [fact(u"jppfs_cor:OperatingIncome", 1158600000.0)]                                  # 差 1.6e6: どの丸めでも帯の外
        for rounding in ("round", "truncate"):
            self.assertFalse(m.rule_r(claim, tup, rounding, nv)[0][u"言う"])
        nv[u"prior"] = [fact(u"jppfs_cor:OrdinaryIncome", 1157006000.0)]                                  # 別の要素の同じ値では名指さない
        r, _ = m.rule_r(claim, tup, "round", nv)
        self.assertEqual((r[u"言う"], r[u"理由"]), (False, u"next の前期欄に同じ要素の fact なし"))
        nv[u"prior"] = [fact(u"jppfs_cor:OperatingIncome", 1157006000.0)]
        self.assertEqual(m.rule_r(dict(claim, pointers=["xbrl:jppfs_cor:A@CurrentYearDuration", "xbrl:jppfs_cor:B@CurrentYearDuration"]), tup, "round", nv)[0][u"理由"], u"pointer が 2 本以上")
        for bad in (dict(claim, form="derived_value"), dict(claim, unit=u"%")):
            self.assertEqual(m.rule_r(bad, tup, "round", nv)[0][u"理由"], u"対象外(形・単位・精度)")
        self.assertEqual(m.rule_r(claim, None, "round", nv)[0][u"理由"], u"対象外(形・単位・精度)")
        sub = dict(claim, pointers=[])                                                                       # pointer が無ければ主語から(手書きの行)
        r, _ = m.rule_r(sub, tup, "round", nv)
        self.assertEqual((r[u"言う"], r[u"要素"]), (True, u"jppfs_cor:OperatingIncome"))
        self.assertEqual(m.rule_r(dict(sub, subject=u"存在しない主語"), tup, "round", nv)[0][u"理由"], u"語彙で引けず(手書きの行に無い)")
        self.assertEqual(m.rule_r(dict(sub, subject=None), tup, "round", nv)[0][u"理由"], u"語彙で引けず(主語なし)")
        # 円の単位(prec が単位より細かい)・負の値(abs の梯子)
        yen = {"form": "direct_value", "unit": u"円", "value": 1157006000.0, "pointers": ["xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration"], "subject": u"営業利益"}
        self.assertEqual(m.rule_r(yen, (0, 9, 1157006000.0, u"円", 1e6), "round", nv)[1], (1.0, 1e6, False))
        nv[u"prior"] = [fact(u"jppfs_cor:OperatingIncome", -1157006000.0)]
        self.assertTrue(m.rule_r(claim, tup, "round", nv)[0][u"言う"])

    def test_b_3_stub_run_sites_rule_r_and_control(self):
        r = self.rec
        rows = r[u"site の行"]
        self.assertEqual(len(rows), 1)                                                                     # 営業利益だけ(経常利益は桁の中で除く)
        s = rows[0]
        self.assertEqual((s[u"要素"], s[u"枠"], s[u"期の型"], s[u"対応"], s[u"元の値"], s[u"差し替えた値"]), (u"jppfs_cor:OperatingIncome", u"CurrentYearDuration", u"Duration", u"付いた", 1159040000.0, 1157006000.0))
        self.assertIn(s[u"state"], (u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND"))
        self.assertEqual((s[u"R"][u"言う"], s[u"R"][u"要素"], s[u"名指しの要素が注入した要素と同じ"]), (True, u"jppfs_cor:OperatingIncome", True))     # 要約の要素ではなく計算書の要素
        self.assertEqual(s[u"字の形"], {u"形": u"simple", u"桁区切り": True, u"小数の桁数": 0, u"単位語": u"百万円"})
        T = r[u"集計"]
        self.assertEqual((T[u"注入した site"], T[u"差が桁の中で除いた"], T[u"止めた"], T[u"R が名指した"], T[u"名指しの要素が注入した要素と同じ"], T[u"対応が付かない"], T[u"通した(GROUNDED)"]), (1, 1, 1, 1, 1, 0, 0))
        self.assertEqual(dict(T[u"site の絞り込み"]), {u"数の claim": 5, u"GROUNDED の数の claim": 3, u"要素が段 1 の違うに入らない": 1, u"差が桁の中": 1, u"注入した": 1})
        C = T[u"対照"]
        self.assertEqual((C[u"止めた行"], C[u"R が名指した"], C[u"R が言える形の行"], C[u"名指しの割合(%)"], dict(C[u"言えない理由"])), (2, 1, 2, 50.0, {u"帯の外": 1}))
        named = r[u"対照の行"][0][u"名指した行"]
        self.assertEqual([(x[u"claim の id"], x[u"R の要素"]) for x in named], [(u"N004", u"jppfs_cor:GrossProfit")])
        G = r[u"配線の門"]
        self.assertTrue(G[u"通った"])
        self.assertEqual((G[u"(e) 文を渡した結果が渡さない結果と一致しなかった書類"], G[u"(f) 戻して W と一致しなかった site"], G[u"(g) R の params が engine の欄と一致しなかった回数"]), (0, 0, 0))
        self.assertGreater(G[u"(g) R の params を照らした回数"], 0)
        self.assertEqual(r[u"key_leaks"], [])
        self.assertEqual(r[u"予測の判定"][u"F-6"], u"外れ")                                              # 1 件は幅 50〜600 の外
        self.assertEqual(r[u"予測の判定"][u"F-7"], u"当たり")
        self.assertEqual(r[u"予測の判定"][u"F-10(段 2 の部分)"][:5], u"判定しない")                      # 固定の確認の組が無い
        for k in (u"封", u"HEAD の commit", u"この script の sha256", u"読んだ材料の sha256", u"engine の bundle の sha256(core/・adapters/)", u"定数", u"配線の門", u"site の行", u"書類ごと",
                  u"対照の行", u"固定の確認 F-10", u"集計", u"予測の判定", u"limits", u"key_leaks"):
            self.assertIn(k, r)
        self.assertEqual(r[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertNotIn(u"。", json.dumps(r[u"site の行"] + r[u"対照の行"], ensure_ascii=False))          # 原文の字を持たない

    def test_b_4_text_is_replaced_by_the_rendered_digits_only(self):
        m = self.mod
        with io.open(os.path.join(self.tmp, "prev", "X200PREV.zip"), "rb") as fh:
            zb = fh.read()
        W, fixed = m.canonical_text(zb)
        self.assertTrue(fixed)
        self.assertIn(u"営業利益は1,159百万円となりました。", W)
        out, raw, info, sents = m.prep_run(zb, W)
        self.assertEqual(info["rounding"], "round")
        offs = m.sentence_offsets(W, sents)
        self.assertTrue(all(o >= 0 for o in offs))
        si = [i for i, s in enumerate(sents) if s.startswith(u"営業利益")][0]
        a, b = m.tuple_at(sents, raw["N002"]["sentence"], raw["N002"]["pos"])[:2]
        self.assertEqual(si, raw["N002"]["sentence"])
        self.assertEqual(W[offs[si] + a:offs[si] + b], u"1,159百万円")
        inj = {"id": "x", "span": [offs[si] + a, offs[si] + a + 5], "replacement": u"1,157"}
        tampered, pl = m.IJ.apply_edits(W, [inj])
        self.assertEqual(tampered, W.replace(u"営業利益は1,159百万円", u"営業利益は1,157百万円"))
        self.assertEqual(m.IJ.revert(tampered, [inj], pl, W), W)

    def test_b_5_stop_conditions_write_nothing(self):
        m = self.mod
        self.stop_without_output(self.out)                                                                  # 出力が既に在る(上書きしない)
        self.stop_without_output(os.path.join(self.tmp, "o2.json"), stage1=os.path.join(self.tmp, "none.json"))
        self.stop_without_output(os.path.join(self.tmp, "o3.json"), procs=5)
        self.stop_without_output(os.path.join(self.tmp, "o3b.json"), procs=0)
        d2 = tempfile.mkdtemp(prefix="restated_stub2_")
        try:
            shutil.copytree(os.path.join(self.tmp, "next"), os.path.join(d2, "next"))
            with io.open(os.path.join(d2, "next", "X200NEXT.zip"), "ab") as fh:
                fh.write(b"x")                                                                              # next の ZIP の sha256 が段 1 の記録と違う
            self.stop_without_output(os.path.join(self.tmp, "o4.json"), next_dir=os.path.join(d2, "next"))
        finally:
            shutil.rmtree(d2, ignore_errors=True)
        orig_bundle, orig_labels = m.P1.engine_bundle, m.check_labels
        try:
            m.P1.engine_bundle = lambda: ("0" * 64, 1, 3)                                                    # engine に未 commit の変更
            self.stop_without_output(os.path.join(self.tmp, "o5.json"))
            m.P1.engine_bundle = orig_bundle
            m.check_labels = lambda p: ("x", ["a.xml"])                                                      # ラベル file が名簿と違う
            self.stop_without_output(os.path.join(self.tmp, "o6.json"))
        finally:
            m.P1.engine_bundle, m.check_labels = orig_bundle, orig_labels

    def test_b_6_parallel_run_gives_the_same_rows(self):
        out2 = os.path.join(self.tmp, "out_p2.json")
        rec2 = self.mod.run(out2, self.stage1, 2, prev_dir=os.path.join(self.tmp, "prev"), next_dir=os.path.join(self.tmp, "next"), cache_dirs={}, say=lambda *a: None)
        for k in (u"site の行", u"集計", u"対照の行", u"予測の判定"):
            self.assertEqual(json.dumps(rec2[k], sort_keys=True), json.dumps(self.rec[k], sort_keys=True), k)

    def run_patched(self, name, **patches):
        u"""門が発火することを、故障を作って確かめる(正常な入力では発火しない守りは、故障を作って当てる)。"""
        m = self.mod
        saved = dict((k, getattr(m if k != "revert" else m.IJ, k)) for k in patches)
        try:
            for k, v in patches.items():
                setattr(m if k != "revert" else m.IJ, k, v)
            return m.run(os.path.join(self.tmp, name), self.stage1, 1, prev_dir=os.path.join(self.tmp, "prev"), next_dir=os.path.join(self.tmp, "next"), cache_dirs={}, say=lambda *a: None)
        finally:
            for k, v in saved.items():
                setattr(m if k != "revert" else m.IJ, k, v)

    def test_b_8_unmapped_when_the_injected_digits_are_not_where_expected(self):
        orig = self.mod.prep_run

        def fake(zb, text):
            out, raw, info, sents = orig(zb, text)
            if text is not None and u"1,157百万円" in text:
                sents = [x.replace(u"1,157百万円", u"9,999百万円") for x in sents]                        # 注入後の文の字が「差し替えた字」と違う
            return out, raw, info, sents
        rec = self.run_patched("o_b8.json", prep_run=fake)
        s = rec[u"site の行"][0]
        self.assertEqual((s[u"対応"], s[u"state"], s[u"R"]), (u"付かない", None, None))
        T = rec[u"集計"]
        self.assertEqual((T[u"注入した site"], T[u"対応が付かない"], T[u"止めた"], T[u"通した(GROUNDED)"], T[u"R が名指した"]), (1, 1, 0, 0, 0))     # 分母には入り、止めた数にも通した数にも入らない
        self.assertEqual(rec[u"予測の判定"][u"F-7"], u"外れ")

    def test_b_9_wiring_gate_goes_red_when_the_checks_fail(self):
        rec = self.run_patched("o_b9.json", revert=lambda *a, **k: u"x")                                      # 戻しが W と合わない
        G = rec[u"配線の門"]
        self.assertEqual(G[u"(f) 戻して W と一致しなかった site"], 1)
        self.assertFalse(G[u"通った"])
        self.assertIn(u"配線の門が通っていない", rec[u"注意"])
        rec = self.run_patched("o_b9b.json", claim_keys=lambda out: [id(out)])                                  # 文を渡した結果が渡さない結果と合わない
        G = rec[u"配線の門"]
        self.assertEqual(G[u"(e) 文を渡した結果が渡さない結果と一致しなかった書類"], 1)
        self.assertFalse(G[u"通った"])
        self.assertTrue(self.rec[u"配線の門"][u"通った"])

    def test_b_10_member_or_prior_frame_pointer_is_not_a_site(self):
        orig = self.mod.P1.frame_of
        try:
            self.mod.P1.frame_of = lambda cid, ctx: u"前期"                                                     # pointer の枠が全部「当期でない」
            rec = self.run_patched("o_b10.json")
        finally:
            self.mod.P1.frame_of = orig
        T = rec[u"集計"]
        self.assertEqual((T[u"注入した site"], T[u"site の絞り込み"].get(u"pointer の枠が当期(member なし)でない")), (0, 3))

    def test_b_7_judge_boundaries_tally_and_f10(self):
        m = self.mod

        def T(n, st, nm, cs, cn):
            return {u"注入した site": n, u"止めた": st, u"R が名指した": nm, u"対照": {u"止めた行": cs, u"R が名指した": cn}}
        F10 = {u"営業利益": {u"結果": u"止め・名指した"}, u"減価償却費及び償却費": {u"結果": u"止め・名指した"}}
        j = lambda *a, **kw: m.judge(T(*a), kw.get("f10", F10))
        self.assertEqual([j(50, 50, 50, 100, 5)[k] for k in (u"F-6", u"F-7", u"F-8", u"F-9")], [u"当たり"] * 4)
        self.assertEqual(j(600, 600, 600, 100, 5)[u"F-6"], u"当たり")
        self.assertEqual((j(49, 49, 49, 100, 5)[u"F-6"], j(601, 601, 601, 100, 5)[u"F-6"]), (u"外れ", u"外れ"))
        self.assertEqual((j(20, 19, 0, 100, 5)[u"F-7"], j(20, 18, 0, 100, 5)[u"F-7"]), (u"当たり", u"外れ"))              # 95% ちょうどは当たり
        self.assertEqual((j(20, 20, 17, 100, 5)[u"F-8"], j(20, 20, 16, 100, 5)[u"F-8"]), (u"当たり", u"外れ"))          # 85% ちょうどは当たり
        self.assertEqual((j(20, 20, 20, 100, 5)[u"F-9"], j(20, 20, 20, 100, 6)[u"F-9"]), (u"当たり", u"外れ"))          # 5% ちょうどは当たり
        self.assertTrue(j(0, 0, 0, 0, 0)[u"F-7"].startswith(u"判定できず"))
        self.assertEqual(j(50, 50, 50, 100, 5)[u"F-10(段 2 の部分)"], u"2 / 2")
        nos = {u"営業利益": {u"結果": u"止め・名指した"}, u"減価償却費及び償却費": {u"結果": u"site なし"}}
        self.assertEqual(j(50, 50, 50, 100, 5, f10=nos)[u"F-10(段 2 の部分)"], u"判定しない(site なし: 減価償却費及び償却費)")
        self.assertEqual(j(50, 50, 50, 100, 5)[u"当たり"] + j(49, 49, 49, 100, 5)[u"外れ"], 4 + 1)
        # 集計: 対照の分母は止めた行の全部(R が言える形の行ではない)
        ctrl = lambda stopped, named, able, states: {u"止めた行": stopped, u"止めた行の state": collections.Counter(states), u"名指した": named, u"R が言える形の行": able, u"言えない理由": collections.Counter({u"x": stopped - named}), u"名指した行": []}
        srow = lambda st, said, same: {u"対応": u"付いた", u"state": st, u"R": {u"言う": said, u"理由": u"x"} if st != u"GROUNDED" else None, u"名指しの要素が注入した要素と同じ": same}
        res = [{u"違う要素の数": 1, u"site の絞り込み": {u"差が桁の中": 2, u"注入した": 2}, u"sites": [srow(u"VALUE_MISMATCH", True, True), srow(u"GROUNDED", False, None)],
                u"control": ctrl(40, 3, 10, {u"UNVERIFIABLE": 30, u"POINTER_NOT_FOUND": 10})},
               {u"違う要素の数": 0, u"site の絞り込み": {u"差が桁の中": 1}, u"sites": [{u"対応": u"付かない", u"state": None, u"R": None, u"名指しの要素が注入した要素と同じ": None}],
                u"control": ctrl(60, 2, 20, {u"VALUE_MISMATCH": 60})}]
        t = m.tally(res)
        self.assertEqual((t[u"注入した site"], t[u"差が桁の中で除いた"], t[u"対応が付かない"], t[u"通した(GROUNDED)"], t[u"止めた"], t[u"R が名指した"], t[u"名指しの要素が注入した要素と同じ"], t[u"違う要素が 1 つ以上ある組"]),
                         (3, 3, 1, 1, 1, 1, 1, 1))
        self.assertEqual((t[u"止めた割合(%)"], t[u"名指しの割合(%)"]), (33.3, 100.0))
        self.assertEqual((t[u"対照"][u"止めた行"], t[u"対照"][u"R が名指した"], t[u"対照"][u"名指しの割合(%)"], t[u"対照"][u"R が言える形の行"], t[u"対照"][u"言える形の行での名指しの割合(%)(参考)"]), (100, 5, 5.0, 30, 16.7))
        self.assertEqual(dict(t[u"対照"][u"止めた行の state"]), {u"VALUE_MISMATCH": 60, u"UNVERIFIABLE": 30, u"POINTER_NOT_FOUND": 10})
        # F-10: 項目ごと(site の元の値・差し替えた値を段 1 の違う要素の値と照らす)
        ex = {u"突き合わせ": {u"違う要素": [{u"要素": u"jpigp_cor:OperatingProfitLossIFRS", u"prev の当期": 1407163000000.0, u"next の前期": 1276635000000.0},
                                          {u"要素": u"jpigp_cor:DepreciationAndAmortizationOpeCFIFRS", u"prev の当期": 1152987000000.0, u"next の前期": 1125588000000.0}]}}
        site = {u"元の値": 1407163000000.0, u"差し替えた値": 1276635000000.0, u"基準の claim の id": u"N032", u"対応": u"付いた", u"state": u"POINTER_NOT_FOUND",
                u"R": {u"言う": True}, u"名指しの要素が注入した要素と同じ": True}
        f = m.f10_eval([{u"sites": [site]}], ex)
        self.assertEqual((f[u"営業利益"][u"結果"], f[u"営業利益"][u"書面の値と一致"], f[u"営業利益"][u"next の前期の値を書面の桁に丸めた整数"], f[u"減価償却費及び償却費"][u"結果"], f[u"減価償却費及び償却費"][u"書面の値と一致"]),
                         (u"止め・名指した", True, 12766, u"site なし", True))
        f2 = m.f10_eval([{u"sites": [dict(site, state=u"GROUNDED", R=None)]}], ex)
        self.assertEqual(f2[u"営業利益"][u"結果"], u"外れ")


class Stage2RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(S2_REC):
            raise unittest.SkipTest(u"記録 %s が無い" % S2_REC_REL)
        cls.rec = jload(S2_REC)
        cls.r1 = jload(REC)
        cls.mod = load(S2_SCRIPT, "restated_naming_under_test_rec")
        cls.seal = jtext(SEAL)

    def test_a_1_shape_and_wiring(self):
        r = self.rec
        self.assertEqual(r[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertTrue(HEX40.match(r[u"HEAD の commit"] or u""))
        sha = lambda rel: hashlib.sha256(open(os.path.join(ROOT, rel), "rb").read()).hexdigest()
        self.assertEqual(r[u"この script の sha256"], sha(S2_SCRIPT_REL))
        self.assertEqual(dict(r[u"読んだ材料の sha256"]), {REC_REL: sha(REC_REL), SCRIPT_REL: sha(SCRIPT_REL), u"measure/inject.py": sha(u"measure/inject.py"),
                                                       u"fixtures/xbrl/taxonomy_labels_sha256.txt": sha(u"fixtures/xbrl/taxonomy_labels_sha256.txt")})
        self.assertEqual(r[u"key_leaks"], [])
        self.assertTrue(r[u"配線の門"][u"通った"])
        self.assertNotIn(u"配線の門が通っていない", r[u"注意"])
        fb = load(os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py"), "frozen_bundle_sha_for_restated_gate")
        self.assertEqual(r[u"engine の bundle の sha256(core/・adapters/)"], "864b1f96292f1615c7e5b7e3bbd6924ebd9955b8354b3c5d51400ba9a01fb054")   # 2026-11-02: 同上(測った時点の世代を字で留める)
        self.assertIn("864b1f96292f1615c7e5b7e3bbd6924ebd9955b8354b3c5d51400ba9a01fb054", [g[0] for g in fb.FROZEN_BUNDLE_GENERATIONS])
        self.assertEqual(r[u"engine の bundle の sha256(core/・adapters/)"], self.r1[u"engine の bundle の sha256(core/・adapters/)"])
        self.assertEqual((r[u"profile"], r[u"procs"] <= 4), (u"P27", True))
        G = r[u"配線の門"]
        self.assertEqual((G[u"(e) 文を渡した結果が渡さない結果と一致しなかった書類"], G[u"(e') W が不動点に届かなかった書類"], G[u"(f) 戻して W と一致しなかった site"],
                          G[u"(g) R の params が engine の欄と一致しなかった回数"], G[u"(d) engine の未 commit の file"]), (0, 0, 0, 0, 0))
        self.assertGreater(G[u"(g) R の params を照らした回数"], 0)
        self.assertEqual(r[u"既存の cache の件数"][u"前"], r[u"既存の cache の件数"][u"後"])
        self.assertEqual(dict(r[u"定数"][u"予測の幅"]), {u"F-6": [50, 600], u"F-7": 95, u"F-8": 85, u"F-9": 5})
        self.assertNotIn(u"Subscription-Key", json.dumps(r, ensure_ascii=False))

    def test_b_1_tally_recomputed_from_rows_and_judgment_rederived(self):
        r = self.rec
        rows, T = r[u"site の行"], r[u"集計"]
        stopped = (u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
        mapped = [s for s in rows if s[u"対応"] == u"付いた"]
        self.assertEqual(T[u"注入した site"], len(rows))
        self.assertEqual(T[u"対応が付かない"], len(rows) - len(mapped))
        self.assertEqual(T[u"通した(GROUNDED)"], sum(1 for s in mapped if s[u"state"] == u"GROUNDED"))
        self.assertEqual(T[u"止めた"], sum(1 for s in mapped if s[u"state"] in stopped))
        self.assertEqual(T[u"止めた"] + T[u"通した(GROUNDED)"] + T[u"対応が付かない"], T[u"注入した site"])
        self.assertEqual(dict(T[u"止めた state の内訳"]), dict((k, sum(1 for s in mapped if s[u"state"] == k)) for k in stopped))
        self.assertEqual(T[u"R が名指した"], sum(1 for s in mapped if s[u"R"] and s[u"R"][u"言う"]))
        self.assertEqual(T[u"名指しの要素が注入した要素と同じ"], sum(1 for s in mapped if s[u"R"] and s[u"R"][u"言う"] and s[u"R"][u"要素"] == s[u"要素"]))
        self.assertEqual(T[u"名指しの割合(%)"], round(100.0 * T[u"R が名指した"] / T[u"止めた"], 1))
        self.assertEqual(T[u"止めた割合(%)"], round(100.0 * T[u"止めた"] / T[u"注入した site"], 1))
        ct = r[u"対照の行"]
        C = T[u"対照"]
        self.assertEqual(C[u"止めた行"], sum(c[u"止めた行"] for c in ct))
        self.assertEqual(C[u"R が名指した"], sum(c[u"名指した"] for c in ct))
        self.assertEqual(C[u"R が名指した"], sum(len(c[u"名指した行"]) for c in ct))
        self.assertEqual(C[u"R が言える形の行"], sum(c[u"R が言える形の行"] for c in ct))
        for st in (u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND"):
            self.assertEqual(C[u"止めた行の state"][st], sum(c[u"止めた行の state"].get(st, 0) for c in ct))
        for c in ct:
            self.assertEqual(c[u"止めた行"], sum(c[u"止めた行の state"].values()))
            self.assertEqual(c[u"止めた行"], c[u"名指した"] + sum(c[u"言えない理由"].values()))
        self.assertEqual(C[u"名指しの割合(%)"], round(100.0 * C[u"R が名指した"] / C[u"止めた行"], 1))
        self.assertEqual(sum(d[u"site の絞り込み"].get(u"差が桁の中", 0) for d in r[u"書類ごと"]), T[u"差が桁の中で除いた"])
        self.assertEqual(sum(d[u"site の絞り込み"].get(u"注入した", 0) for d in r[u"書類ごと"]), T[u"注入した site"])
        self.assertEqual(dict(self.mod.judge(T, r[u"固定の確認 F-10"][u"項目"])), dict(r[u"予測の判定"]))
        self.assertEqual(dict(seal_bounds_s2(self.seal)), dict((k, tuple(v) if isinstance(v, list) else v) for k, v in r[u"定数"][u"予測の幅"].items()))

    def test_b_2_rows_agree_with_stage1_and_have_no_prose(self):
        r, r1 = self.rec, self.r1
        pairs = dict((p[u"prev の docID"], p) for p in r1[u"組"] if p[u"状態"] == u"組")
        self.assertEqual([d[u"prev の docID"] for d in r[u"書類ごと"]], [p[u"prev の docID"] for p in r1[u"組"] if p[u"状態"] == u"組"])
        self.assertEqual([d[u"next の docID"] for d in r[u"書類ごと"]], [p[u"next の docID"] for p in r1[u"組"] if p[u"状態"] == u"組"])
        seen = set()
        for s in r[u"site の行"]:
            key = (s[u"prev の docID"], s[u"基準の claim の id"])
            self.assertNotIn(key, seen)
            seen.add(key)
            p = pairs[s[u"prev の docID"]]
            self.assertEqual(s[u"next の docID"], p[u"next の docID"])
            row = [x for x in p[u"突き合わせ"][u"違う要素"] if x[u"要素"] == s[u"要素"] and x[u"期の型"] == s[u"期の型"] and x[u"単位"] == s[u"単位"]]
            self.assertEqual(len(row), 1)
            self.assertEqual((s[u"元の値"], s[u"差し替えた値"]), (row[0][u"prev の当期"], row[0][u"next の前期"]))
            self.assertTrue(s[u"枠"].startswith(u"CurrentYear"))
            self.assertNotEqual(s[u"元の値"], s[u"差し替えた値"])
            if s[u"R"] and s[u"R"][u"言う"]:
                self.assertIn(s[u"state"], (u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND"))
                self.assertEqual(s[u"名指しの要素が注入した要素と同じ"], s[u"R"][u"要素"] == s[u"要素"])
            if s[u"state"] == u"GROUNDED":
                self.assertIsNone(s[u"R"])
        text = json.dumps([r[u"site の行"], r[u"対照の行"], r[u"書類ごと"], r[u"固定の確認 F-10"]], ensure_ascii=False)
        self.assertNotIn(u"。", text)
        self.assertTrue(set(DOCID_RE.findall(json.dumps(r[u"対照の行"], ensure_ascii=False))) <= set(pairs))
        for rows in (r[u"site の行"], r[u"対照の行"]):
            for x in rows:
                for v in x.values():
                    if isinstance(v, str):
                        self.assertLess(len(v), 120)

    def test_b_3_fixed_check_f10_recomputed(self):
        r, r1 = self.rec, self.r1
        ex = r1[u"固定の確認"][0]
        f10 = r[u"固定の確認 F-10"]
        self.assertEqual((f10[u"EDINET コード"], f10[u"prev の docID"], f10[u"next の docID"]), (ex[u"EDINET コード"], ex[u"書類"][0][u"docID"], ex[u"書類"][1][u"docID"]))
        res = self.mod.f10_eval([{u"sites": f10[u"site の行"]}], ex)
        self.assertEqual(json.dumps(res, sort_keys=True), json.dumps(f10[u"項目"], sort_keys=True))
        for k, it in self.mod.ITEMS.items():
            self.assertEqual(f10[u"項目"][k][u"書面の値と一致"], True)

    def test_b_4_every_case_shown_in_the_record_is_in_the_stage1_difference_set_only(self):
        # 段 1 の「違う」に入る要素から外れた site は 1 つも無い(site の要素は段 1 の違う要素の中から)。上の b_2 が値まで照らす。ここでは site の数が絞り込みの数と合う。
        r = self.rec
        by_doc = collections.Counter(s[u"prev の docID"] for s in r[u"site の行"])
        for d in r[u"書類ごと"]:
            self.assertEqual(by_doc.get(d[u"prev の docID"], 0), d[u"site の絞り込み"].get(u"注入した", 0))


class Stage2OrderAndDocTest(unittest.TestCase):
    def test_order_seal_stage1_script_record_doc(self):
        rc, _ = git("cat-file", "-e", SEAL_COMMIT_SHORT + "^{commit}")
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(order_problems_s2(), [])

    def test_result_document_numbers_judgments_and_words(self):
        if not (os.path.exists(S2_REC) and os.path.exists(RESULT)):
            self.skipTest(u"段 2 の記録か結果の文書が無い")
        self.assertEqual(doc_problems(jtext(RESULT), jload(REC), jload(S2_REC), jtext(SEAL)), [])


class Stage2MutationTest(unittest.TestCase):
    u"""門そのものが赤くなること(入力の側の変異)。ファイルを書き換える変異は実行者が別に走らせて返事に書く。"""

    @classmethod
    def setUpClass(cls):
        cls.seal = jtext(SEAL)

    def test_m_1_seal_width_change_changes_bounds(self):
        for old, new, k in ((u"**50〜600**", u"**50〜900**", u"F-6"), (u"**95% 以上**", u"**90% 以上**", u"F-7"), (u"**85% 以上**", u"**80% 以上**", u"F-8"), (u"**5% 以下**", u"**9% 以下**", u"F-9")):
            bad = self.seal.replace(old, new)
            self.assertNotEqual(bad, self.seal)
            self.assertNotEqual(seal_bounds_s2(bad)[k], seal_bounds_s2(self.seal)[k], k)

    def test_m_2_bad_imports_hosts_and_writes_are_caught(self):
        src = jtext(S2_SCRIPT)
        for extra in (u"\nimport urllib.request\n", u"\nimport requests\n", u"\nfrom adapters.xbrl import edinet\n", u"\nfrom adapters.xbrl.edinet import fetch\n", u'\nX = "https://example.com/x"\n',
                      u'\nio.open(os.path.join(ROOT, "x"), "wb")\n', u"\nos.makedirs(ROOT)\n", u"\nimport shutil\n", u"\nimport socket\n"):
            self.assertNotEqual(script2_problems(src + extra), [], extra)

    def test_m_3_doc_problems_catch_changed_numbers_judgments_and_words(self):
        if not (os.path.exists(S2_REC) and os.path.exists(RESULT)):
            self.skipTest(u"段 2 の記録か結果の文書が無い")
        doc, r1, r2 = jtext(RESULT), jload(REC), jload(S2_REC)
        self.assertEqual(doc_problems(doc, r1, r2, self.seal), [])
        T2 = r2[u"集計"]
        muts = [doc.replace(u"| 注入した site | %d |" % T2[u"注入した site"], u"| 注入した site | %d |" % (T2[u"注入した site"] + 1)),
                doc.replace(u"| 対照: 止めた行 | 4809 |", u"| 対照: 止めた行 | 4808 |"),
                doc.replace(u"| 通った | True |", u"| 通った | False |"),
                re.sub(r"(\| F-6 \|.*\| )外れ( \|)", r"\1当たり\2", doc),
                doc + u"\n精度が高い。\n", doc + u"\nソニーグループ\n", doc + u"\n3,333 件。\n", doc.replace(u"## §5 ", u"## 5 ")]
        for i, mut in enumerate(muts):
            self.assertNotEqual(mut, doc, i)
            self.assertNotEqual(doc_problems(mut, r1, r2, self.seal), [], i)
        self.assertEqual(doc_problems(doc + u"\n3,333 件。【門なし】\n", r1, r2, self.seal), [])


if __name__ == "__main__":
    unittest.main()
