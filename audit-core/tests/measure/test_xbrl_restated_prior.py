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
        self.assertEqual(self.rec[u"engine の bundle の sha256(core/・adapters/)"], fb.FROZEN_BUNDLE_SHA)
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


if __name__ == "__main__":
    unittest.main()
