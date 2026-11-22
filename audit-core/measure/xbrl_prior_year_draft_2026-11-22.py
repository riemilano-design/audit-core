# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PRIOR_YEAR_DRAFT_SEAL_2026-11-22.md(XY0 ― 同じ会社の前の年の提出書類の「行の字 → 要素」を今年の行に当てると、今年の行の要素はどれだけ決まり、どれだけ黙って違うか)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。通信しない。** engine(``core/``・``adapters/``)は 1 行も変えない。行の切り方(``_TR_RE``・``_row_label``)は engine の関数を呼ぶ。
便 XG0 の script の関数(行の状態の読み取りの部品・表 L2・書類の選び方・記録の検査)と便 XG1 の script の関数(見出しつきの行の切り方・種類 K・業種・段 3・標準タクソノミ)は importlib で読んで呼ぶ(写さない)。

    python3 measure/xbrl_prior_year_draft_2026-11-22.py            # 置き場から数えて記録 fixtures/xbrl/cd8/prior_year_draft_2026-11-22.json を排他で書く。通信しない
    python3 measure/xbrl_prior_year_draft_2026-11-22.py --check    # 置き場から数え直して記録と照らす。通信しない
    python3 measure/xbrl_prior_year_draft_2026-11-22.py --dry-run  # 記録を書かず、数も出さず、組の数と「止まらない」だけを言う(止まる条件は本番と同じ)

置き場の既定は封の字(今年の側 ``~/.cache/audit-core/edinet/``・前の年の側 ``~/.cache/audit-core/edinet-prior-2026-11-02/``・標準ラベルと標準タクソノミは便 XG1 と同じ)。
**前の年の側は ``_ixbrl.htm`` だけを読む。今年の側の E は、類分けにだけ使い、候補(表 P・表 PK・段 C)の作りには渡さない。**

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 組の作り方の file 名の形: ``jpcrp030000-asr-ddd_<提出者のコード>-ddd_<YYYY-MM-DD>`` を file 名(basename)の頭に持つもの(後ろは問わない)。PublicDoc の中の全 file の名を昇順に見て最初に当たるもの。
  提出者のコードは ``-`` と ``_`` を含まない字。今年の側でこの形が読めない書類が在れば止まる(除かない)。前の年の側でこの形が読めない zip は有価証券報告書でないものとして飛ばす。
- 期末の照合: 今年の期末の年から 1 を引いた年・月日が同じ。違えば止まる(2 月 29 日は考えない: 同じ月日の比較だけ)。
- 行: ``<tr>`` のうち ix:nonFraction の name がちょうど 1 種類で、行の字(engine の ``_row_label`` → ``norm_label``)が空でないもの。要素 E は name の字そのまま。
  集まり S は E の接頭辞が ``jppfs_cor`` のもの(便 XG0 と同じ判定)。集まり B は接頭辞を問わない(S を含む)。
- 見出し・種類 K は便 XG1 の ``file_rows``・``kind_of`` を使う(見出しは行を持つ file の中だけ・行より前の最後)。前の年の側にも今年の側にも同じ関数を掛ける。
- 表 PK の鍵の K が決まらない行は ``None`` 同士でだけ当たる。段 PK は表 PK の (K, T)。段 P は表 P の T。
- 段 C: 段 PK の候補が空でなければ段 PK。空なら便 XG1 の ``narrow`` の第 3 の候補(cand0 = 表 L2 の T の集まり・I は便 XG1 の ``industry_of``。K が決まらなければ I は None)に ``jppfs_cor:`` を付けた集まり。
  「標準の表へ落ちた行」= 段 C を段 PK でなく標準の表で決めた行(段 PK の候補が空の行)。
- 類: U・A・W1・W2・N(封 §2-5)。W1 = 候補がちょうど 1 つで E でない。W2 = 候補が 2 つ以上で E を含まない。
- 書類の「番号」は便 XG0 の記録と同じ番号(今年の側の 67 本の昇順の位置。除いた書類の番号は飛ぶ)。S の行の合計の照合は、組になった番号どうしで便 XG0 の記録の同じ番号の行の数の合計と照らす。
- 材料の並びの sha256: 今年の側は便 XG0 と同じ(``order_sha256``)。前の年の側は、組の相手の zip の file 名(拡張子を除く)を、今年の側の番号の順に並べ ``\\n`` でつないだ字の sha256。
- 率は四捨五入(0.5 は上げる)で小数第 1 位。判定に要る数は丸める前の整数も書く。
"""
from __future__ import print_function

import argparse
import collections
import glob
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

from adapters.xbrl import instance as I                 # noqa: E402
from adapters.xbrl import verify_document as VD         # noqa: E402


def _load_narrow():
    u"""便 XG1 の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。便 XG1 の script が便 XG0 の script を読む。"""
    name = "_xy0_tag_narrow_2026_11_21"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "xbrl_tag_narrow_2026-11-21.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


N = _load_narrow()
W = N.W

SEAL_REL = "docs/XBRL_PRIOR_YEAR_DRAFT_SEAL_2026-11-22.md"
SEAL_COMMIT = "ce70f71f"
SCRIPT_REL = "measure/xbrl_prior_year_draft_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/prior_year_draft_2026-11-22.json"
WALL_RECORD_REL = "fixtures/xbrl/cd8/tag_wall_2026-11-21.json"
DOCS_DIR = W.DOCS_DIR
PRIOR_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-prior-2026-11-02")
TAXONOMY_DIR = N.TAXONOMY_DIR
TAXZIP_PATH = N.TAXZIP_PATH

# ---- 封 §1・§2・§4 の決めごと(字で留める。封の門が封の字と照らす)
DOCS_WANT = W.DOCS_WANT
PAIRS_WANT = 63
FILE_RE = re.compile(r"^jpcrp030000-asr-\d{3}_([^_\-]+)-\d{3}_(\d{4})-(\d{2})-(\d{2})")
STATEMENT_PREFIX = W.STATEMENT_PREFIX
STD_PREFIX_COLON = "jppfs_cor:"
CLASSES = ("U", "A", "W1", "W2", "N")
STAGES_S = ("P", "PK", "C")
STAGES_B = ("P", "PK")
U_DOC_THRESHOLD_PCT = 95                       # XY0-7: 段 PK・S の U の率がこれ以上の書類
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 上限) の %(XY0-5 は U と W1 の 2 つ・XY0-6 は B の率から S の率を引いた差のポイント・XY0-7 は本数)
BOUNDS = collections.OrderedDict([
    ("XY0-1", (72, 88)), ("XY0-2", (84, 95)), ("XY0-3", (None, 1.5)), ("XY0-4", (3, 12)),
    ("XY0-5", ((86, 97), (None, 2.5))), ("XY0-6", (-5, None)), ("XY0-7", (10, 40))])
LIMITS = [
    u"前の年の書類も今年の書類も、専用の道具が組んだ後の字。同じ道具・同じ会社が 2 年続けて組んだものなので、行の字も要素も揃いやすい。原稿の字での率は測れない。この便の U は「上の限り」に近い読み。",
    u"前の年の XBRL が在る会社にしか使えない。初めて出す会社・様式が変わった年・科目を組み替えた年は、この便の外か、N・W1 の側に出る。",
    u"前の年に無かった行(N)は、道具がいちばん要る所。この便はそこを決めない。",
    u"63 組は無作為ではない。業種はほぼ一般商工業。年は 1 組(1 年の差)だけ。標準タクソノミの版の変わり目で要素の名が変わった所は W1・N の側に出る(分けて数えない)。",
    u"測るのは要素の名だけ。期・連結か個別か・単位・桁・値・表示の並び・計算の関係・提出者別タクソノミの file は測っていない。1 行に要素が 2 種類以上在る行・行の字が空の行は分母の外。",
    u"「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」は、この便からは言えない。"]

Stop = W.Stop
od = collections.OrderedDict
sha256_bytes = W.sha256_bytes
sha256_file = W.sha256_file
dumps = W.dumps
pct1 = W.pct1
norm_label = W.norm_label
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


# ======================================================================================================
# 組の作り方(封 §1)
def code_and_end(names):
    u"""zip の中の名の並び → (提出者のコード, (年, 月, 日)) か None。PublicDoc の中の file の名(basename)を昇順に見て、形に最初に当たるもの。"""
    base = sorted(os.path.basename(n) for n in names if n.startswith(W.PUBLICDOC) and os.path.basename(n))
    for b in base:
        m = FILE_RE.match(b)
        if m:
            return m.group(1), (int(m.group(2)), m.group(3), m.group(4))
    return None


def zip_code_end(path):
    try:
        with zipfile.ZipFile(path) as z:
            return code_and_end(z.namelist())
    except zipfile.BadZipFile:
        raise Stop(u"**zip が読めない。止める**")


def prior_index(prior_dir):
    u"""前の年の側の置き場 → {提出者のコード: [(file 名の stem, path, 期末)]}。形が読めない zip は飛ぶ。"""
    out = {}
    for p in sorted(glob.glob(os.path.join(prior_dir, "*.zip"))):
        ce = zip_code_end(p)
        if ce is None:
            continue
        out.setdefault(ce[0], []).append((os.path.basename(p)[:-4], p, ce[1]))
    return out


def make_pairs(docs_dir, prior_dir, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT):
    u"""(docs, pairs, 除いた数)。pairs = [(番号, 今年の stem, 今年の path, 前の年の stem, 前の年の path, 提出者のコード)]。
    当たる zip が無い → 除く。2 本以上 → 止まる。期末が合わない → 止まる。組の数が ``want_pairs`` でなければ止まる。"""
    docs = W.select_docs(docs_dir, want_docs)
    idx = prior_index(prior_dir)
    pairs = []
    for n, (stem, p, _xs) in enumerate(docs, 1):
        ce = zip_code_end(p)
        if ce is None:
            raise Stop(u"**今年の側の書類で提出者のコードと期末が読めない。止める**")
        code, (y, m, d) = ce
        cands = idx.get(code, [])
        if not cands:
            continue
        if len(cands) != 1:
            raise Stop(u"**前の年の側に提出者のコードが同じ zip が 2 本以上在る。止める**")
        pstem, pp, (py, pm, pd) = cands[0]
        if (py, pm, pd) != (y - 1, m, d):
            raise Stop(u"**前の年の側の期末が、今年の期末の 1 年前の同じ月日でない。止める**")
        pairs.append((n, stem, p, pstem, pp, code))
    if len(pairs) != want_pairs:
        raise Stop(u"**組の数が %d でない(%d)。止める**" % (want_pairs, len(pairs)))
    return docs, pairs, len(docs) - len(pairs)


# ======================================================================================================
# 行・表・段・類(封 §2)
def row_info(rowtext):
    u"""``<tr>`` 1 行 → (行の字 T, 要素 E) か None。ix:nonFraction の name がちょうど 1 種類で、行の字が空でない行。"""
    names = W.NF_RE.findall(rowtext)
    if not names or len(set(names)) != 1:
        return None
    label = I._row_label(rowtext)
    if not label:
        return None
    t = norm_label(label)
    if not t:
        return None
    return t, names[0]


def file_row_list(text):
    u"""file の字 → [(T, E, 見出し, 種類 K)]。見出しと K は便 XG1 の ``file_rows``・``kind_of``。"""
    out = []
    for rowtext, head in N.file_rows(text):
        info = row_info(rowtext)
        if info is not None:
            out.append((info[0], info[1], head, N.kind_of(head)))
    return out


def is_s(E):
    u"""集まり S(標準の計算書の行): 接頭辞が ``jppfs_cor``。"""
    return E.split(":")[0] == STATEMENT_PREFIX


def build_tables(prior_texts, secret=None):
    u"""前の年の側の [(file 名, 字)] → (表 P, 表 PK)。集まり B の行の全部から作る。"""
    p, pk = {}, {}
    for _n, text in sorted(prior_texts, key=lambda q: q[0]):
        for T, E, head, K in file_row_list(text):
            p.setdefault(T, set()).add(E)
            pk.setdefault((K, T), set()).add(E)
            if secret is not None:
                secret[0].add(T)
                secret[1].add(E.split(":")[-1])
                if head is not None:
                    secret[4].add(norm_label(head))
    return p, pk


def stage_p(tab_p, T):
    return set(tab_p.get(T, ()))


def stage_pk(tab_pk, K, T):
    return set(tab_pk.get((K, T), ()))


def stage_c(cand_pk, cand_std):
    u"""段 C(集まり S だけ): 段 PK の候補が 1 つ以上なら段 PK。空なら標準の表の候補(``jppfs_cor:`` つき)。"""
    if cand_pk:
        return set(cand_pk)
    return set(cand_std)


def std_cands(T, K, ind, l2, tax):
    u"""便 XG1 の段 3 の候補(cand0 = 表 L2 の T)に ``jppfs_cor:`` を付けた集まり。"""
    return set(STD_PREFIX_COLON + x for x in N.narrow(set(l2.get(T, ())), K, ind, tax)[2])


def classify5(E, cands):
    u"""類 U・A・W1・W2・N(封 §2-5)。"""
    if not cands:
        return "N"
    if E not in cands:
        return "W1" if len(cands) == 1 else "W2"
    return "U" if len(cands) == 1 else "A"


def new_doc():
    return od([("s", 0), ("b", 0),
               ("S", od((s, od((c, 0) for c in CLASSES)) for s in STAGES_S)),
               ("B", od((s, od((c, 0) for c in CLASSES)) for s in STAGES_B)),
               ("fall", 0), ("fallc", od((c, 0) for c in CLASSES))])


def count_pair(cur_texts, prior_texts, l2, tax, secret=None):
    u"""組 1 つ(今年の側・前の年の側の [(file 名, 字)])を数える。E は類分けにだけ使い、候補の作りには渡さない。"""
    cur_texts = sorted(cur_texts, key=lambda q: q[0])
    tab_p, tab_pk = build_tables(prior_texts, secret)
    dei = N.dei_values(cur_texts)
    acc = new_doc()
    for _n, text in cur_texts:
        for T, E, head, K in file_row_list(text):
            c_p = stage_p(tab_p, T)
            c_pk = stage_pk(tab_pk, K, T)
            acc["b"] += 1
            acc["B"]["P"][classify5(E, c_p)] += 1
            acc["B"]["PK"][classify5(E, c_pk)] += 1
            if is_s(E):
                ind = N.industry_of(head, dei, tax["folders"]) if K is not None else None
                c_c = stage_c(c_pk, std_cands(T, K, ind, l2, tax))
                acc["s"] += 1
                acc["S"]["P"][classify5(E, c_p)] += 1
                acc["S"]["PK"][classify5(E, c_pk)] += 1
                acc["S"]["C"][classify5(E, c_c)] += 1
                if not c_pk:
                    acc["fall"] += 1
                    acc["fallc"][classify5(E, c_c)] += 1
            if secret is not None:
                secret[0].add(T)
                secret[1].add(E.split(":")[-1])
                if head is not None:
                    secret[4].add(norm_label(head))
    if secret is not None:
        secret[5].update(v for v in dei if v)
    return acc


def add_into(tot, acc):
    for k in ("s", "b", "fall"):
        tot[k] += acc[k]
    for s in STAGES_S:
        for c in CLASSES:
            tot["S"][s][c] += acc["S"][s][c]
    for s in STAGES_B:
        for c in CLASSES:
            tot["B"][s][c] += acc["B"][s][c]
    for c in CLASSES:
        tot["fallc"][c] += acc["fallc"][c]


def totals(accs):
    tot = new_doc()
    for a in accs:
        add_into(tot, a)
    return tot


def check_expected(rows_by_number, wall, pairs_want=PAIRS_WANT):
    u"""63 本の S の行の合計が、便 XG0 の記録の同じ書類の番号の行の数の合計と違えば止まる。``wall`` は便 XG0 の記録(None なら照らさない)。"""
    if wall is None:
        return
    docs = wall[u"書類"]
    want = 0
    for n in rows_by_number:
        if n < 1 or n > len(docs) or docs[n - 1][u"番号"] != n:
            raise Stop(u"**便 XG0 の記録に同じ番号が無い。止める**")
        want += docs[n - 1][u"計算書の行の数"]
    if sum(rows_by_number.values()) != want:
        raise Stop(u"**S の行の合計が便 XG0 の記録の同じ番号の行の数の合計と違う。止める**")


def rate_of(n, d):
    return od([(u"行", n), (u"分母", d), (u"%", pct1(n, d))])


# ======================================================================================================
# 記録
def build_record(docs_dir=None, prior_dir=None, taxonomy_dir=None, taxzip=None, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT, expect=True, wall_path=None, check_sha=True):
    u"""置き場 → (記録, 漏れの検査に使う材料)。書かない。``expect`` が False なら便 XG0 の記録との行の合計の照合を掛けない(封の門の作り物の置き場だけ)。"""
    docs, pairs, excluded = make_pairs(docs_dir or DOCS_DIR, prior_dir or PRIOR_DIR, want_docs, want_pairs)
    label_data, label_sha = W.read_label_bytes(taxonomy_dir or TAXONOMY_DIR)
    l2 = W.label_tables(label_data)[0]
    tax, zip_sha, tmat = N.load_tax(taxzip or TAXZIP_PATH, check_sha)
    fp = VD.engine_fingerprint()
    secret = (set(), set(), [d[0] for d in docs] + [p[3] for p in pairs], set(p[5] for p in pairs), set(), set())
    for _stem, _p, xs in docs:
        for x in xs:
            secret[3].update(re.findall(r"E\d{5}", x))
    accs, rows_out, rows_by_number = [], [], {}
    docs_with_rows = docs_u95 = 0
    for n, stem, p, pstem, pp, code in pairs:
        with zipfile.ZipFile(p) as z:
            cur = N.doc_texts(z)
        with zipfile.ZipFile(pp) as z:
            prv = N.doc_texts(z)
        acc = count_pair(cur, prv, l2, tax, secret)
        accs.append(acc)
        rows_by_number[n] = acc["s"]
        r = acc["s"]
        u_pk = acc["S"]["PK"]["U"]
        if r:
            docs_with_rows += 1
            if 100 * u_pk >= U_DOC_THRESHOLD_PCT * r:
                docs_u95 += 1
        rows_out.append(od([
            (u"番号", n), (u"集まり S の行の数", acc["s"]), (u"集まり B の行の数", acc["b"]),
            (u"集まり S の段ごとの類別", od((s, od(acc["S"][s])) for s in STAGES_S)),
            (u"集まり B の段ごとの類別", od((s, od(acc["B"][s])) for s in STAGES_B)),
            (u"段 C で標準の表へ落ちた S の行の数", acc["fall"]),
            (u"段 C で標準の表へ落ちた S の行の類別", od(acc["fallc"])),
            (u"段 PK・集まり S の U の率(%)", pct1(u_pk, r))]))
    wall = None
    if expect:
        wp = wall_path or os.path.join(ROOT, WALL_RECORD_REL)
        if not os.path.isfile(wp):
            raise Stop(u"**便 XG0 の記録が無い。止める**")
        with io.open(wp, encoding="utf-8") as fh:
            wall = json.load(fh, object_pairs_hook=collections.OrderedDict)
    check_expected(rows_by_number, wall, want_pairs)
    tot = totals(accs)
    rs, rb = tot["s"], tot["b"]
    spk, bpk, sc, sp = tot["S"]["PK"], tot["B"]["PK"], tot["S"]["C"], tot["S"]["P"]
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XY0(同じ会社の前の年の提出書類の「行の字 → 要素」を今年の行に当てると、今年の行の要素はどれだけ決まり、どれだけ黙って違うか)(0 USD・engine は 0 行)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"engine の指紋"] = od((k, fp[k]) for k in ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files"))
    mat = od([
        (u"今年の側の書類の本数", len(docs)),
        (u"今年の側の書類の file 名の並びの sha256", W.order_sha256([d[0] for d in docs])),
        (u"組の数", len(pairs)),
        (u"除いた今年の書類の数", excluded),
        (u"前の年の側の組の相手の file 名の並びの sha256", sha256_bytes(u"\n".join(p[3] for p in pairs).encode("utf-8"))),
        (u"標準ラベルの file の sha256", label_sha),
        (u"表 L2 のラベルの字の数", len(l2)),
        (u"標準タクソノミの zip の sha256", zip_sha)])
    mat.update(tmat)
    rec[u"材料"] = mat
    rec[u"書類"] = rows_out
    rec[u"集計"] = od([
        (u"集まり S の行の数", rs), (u"集まり B の行の数", rb),
        (u"集まり S の段ごとの類別", od((s, od(tot["S"][s])) for s in STAGES_S)),
        (u"集まり B の段ごとの類別", od((s, od(tot["B"][s])) for s in STAGES_B)),
        (u"段 C で標準の表へ落ちた S の行の数", tot["fall"]),
        (u"段 C で標準の表へ落ちた S の行の類別", od(tot["fallc"])),
        (u"集まり S の行が 1 行以上在る書類の数", docs_with_rows)])
    u_s_b = pct1(bpk["U"] * rs - spk["U"] * rb, rb * rs)
    rec[u"予測の判定に要る数(XY0-1〜XY0-7。当たり・外れは結果の文書で)"] = od([
        (u"XY0-1 段 P・集まり S の類 U / 集まり S の行", rate_of(sp["U"], rs)),
        (u"XY0-2 段 PK・集まり S の類 U / 集まり S の行", rate_of(spk["U"], rs)),
        (u"XY0-3 段 PK・集まり S の類 W1 / 集まり S の行", rate_of(spk["W1"], rs)),
        (u"XY0-3 段 PK・集まり S の類 W1 / (U + W1)", rate_of(spk["W1"], spk["U"] + spk["W1"])),
        (u"XY0-4 段 PK・集まり S の類 N / 集まり S の行", rate_of(spk["N"], rs)),
        (u"XY0-5 段 C・集まり S の類 U / 集まり S の行", rate_of(sc["U"], rs)),
        (u"XY0-5 段 C・集まり S の類 W1 / 集まり S の行", rate_of(sc["W1"], rs)),
        (u"XY0-6 段 PK の類 U の率(集まり B と集まり S)", od([
            (u"集まり B の U の行", bpk["U"]), (u"集まり B の行", rb), (u"集まり B の %", pct1(bpk["U"], rb)),
            (u"集まり S の U の行", spk["U"]), (u"集まり S の行", rs), (u"集まり S の %", pct1(spk["U"], rs)),
            (u"集まり B から集まり S を引いた差(ポイント)", u_s_b)])),
        (u"XY0-7 段 PK・集まり S の U の率が %d%% 以上の書類 / 組の数" % U_DOC_THRESHOLD_PCT, od([
            (u"書類", docs_u95), (u"分母", len(pairs)), (u"集まり S の行が 1 行以上在る書類", docs_with_rows)]))])
    rec[u"限界"] = list(LIMITS)
    return rec, secret


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(便 XG1 の検査 + 日付の形)が無いか。在れば止める。secret = (行の字, 要素の局所名, docID(前の年の側を含む), 提出者のコード, 見出しの字, 業種の値)。"""
    N.check_clean(rec, text, secret)
    if DATE_RE.search(W.HEX_RE.sub(u"", text).replace(SEAL_REL, u"")):
        raise Stop(u"**記録に日付の形の字が在る。止める**")


def record_text(rec, secret=None):
    text = dumps(rec)
    check_clean(rec, text, secret)
    return text


def write_exclusive(path, data):
    with open(path, "xb") as fh:
        fh.write(data)


def write_record(path, rec, secret=None):
    u"""書く前と書いた後に検査する。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(path))
    text = record_text(rec, secret)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_exclusive(path, text.encode("utf-8"))
    with io.open(path, encoding="utf-8") as fh:
        back = fh.read()
    try:
        check_clean(rec, back, secret)
    except SystemExit:
        os.remove(path)
        raise


def run(root=ROOT, docs=None, prior=None, taxonomy=None, taxzip=None, out=None, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT, expect=True, wall_path=None, check_sha=True, say=print):
    rec, secret = build_record(docs, prior, taxonomy, taxzip, want_docs, want_pairs, expect, wall_path, check_sha)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(組 %d)" % (os.path.basename(out), rec[u"材料"][u"組の数"]))
    return rec


def dry_run(docs=None, prior=None, taxonomy=None, taxzip=None, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT, expect=True, wall_path=None, check_sha=True, say=print):
    u"""記録を書かず、数も出さない。本番と同じ道(組・数え・行の合計の照合・記録の検査)を通って止まらなければ、組の数と「止まらない」だけを言う。"""
    rec, secret = build_record(docs, prior, taxonomy, taxzip, want_docs, want_pairs, expect, wall_path, check_sha)
    record_text(rec, secret)
    say(u"--dry-run: %d 組・止まらない(記録は書かない)" % rec[u"材料"][u"組の数"])


def check(root=ROOT, docs=None, prior=None, taxonomy=None, taxzip=None, rec_path=None, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT, expect=True, wall_path=None, check_sha=True, say=print):
    u"""置き場から数え直して記録と照らす。通信しない。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    now, secret = build_record(docs, prior, taxonomy, taxzip, want_docs, want_pairs, expect, wall_path, check_sha)
    if dumps(now) != dumps(rec):
        raise Stop(u"**置き場から数え直した記録が、今の記録と違う。止める**")
    check_clean(rec, text, secret)
    say(u"--check: 記録は置き場から数え直した数と同じ(組 %d)" % now[u"材料"][u"組の数"])
    return now


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="置き場から数え直して記録と照らす。通信しない")
    ap.add_argument("--dry-run", action="store_true", help="記録を書かず数も出さず、組の数と止まらないことだけを言う")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="今年の側の置き場(既定は封の字)")
    ap.add_argument("--prior", default=None, help="前の年の側の置き場(既定は封の字)")
    ap.add_argument("--taxonomy", default=None, help="標準ラベルの置き場(既定は封の字)")
    ap.add_argument("--taxzip", default=None, help="標準タクソノミの zip(既定は封の字)")
    a = ap.parse_args(argv)
    kw = dict(docs=a.docs, prior=a.prior, taxonomy=a.taxonomy, taxzip=a.taxzip)
    if a.check:
        check(root=a.root, **kw)
    elif a.dry_run:
        dry_run(**kw)
    else:
        run(root=a.root, **kw)


if __name__ == "__main__":
    main()
