# -*- coding: utf-8 -*-
u"""候補の欄(``candidate``)の正しさを、読み手の席が無改変の 10 行で 1 回だけ見る便の script ― 2026-10-30。

封 ``docs/XBRL_CANDIDATE_EYES_SEAL_2026-10-30.md``(commit ``9d847c0``)§2-1〜§2-5・§6-3 のとおり。
**engine(``core/``・``adapters/``)は 0 行。** 既存の記録は書き換えない。0 USD・通信なし・鍵の値は読まない・LLM は呼ばない(読み手の席は司令塔が立てる)。
評価用・調整用(``~/.cache/audit-core/edinetdb-p27/``)は開かない。``~/.cache/audit-core/edinet/``(281)は読まず書かない。``edinet-fresh-2026-10-21/``(40)は読むだけ。

    cd audit-core
    python3 measure/xbrl_candidate_eyes_2026-10-30.py select  --out <scratch>/select.json
    python3 measure/xbrl_candidate_eyes_2026-10-30.py dossier --select <scratch>/select.json --out-dir <scratch>/dossier/ [--probe]
    python3 measure/xbrl_candidate_eyes_2026-10-30.py collect --select <scratch>/select.json --replies <scratch>/replies/ --out fixtures/xbrl/candidate_eyes_2026-10-30.json
                                                      [--dossier-dir <scratch>/dossier/] [--seat-facts <file>]

  select  封 §2-1: 296 行を (注入の書類の位置, id の昇順) で並べ、位置 0, 30, …, 270 の 10 行を scratchpad にだけ書く。
  dossier 封 §2-3 + §6-3: 位置ごとに ``row_<位置 3 桁>.txt``(束)と ``prompt_<位置 3 桁>.txt``(= READER_PROMPT + 束)、``reader_prompt.txt``、``index.json``。
          束に入れてはいけない字が 1 つでも在れば何も書かずに止める。配線の門 (1)〜(3) を読みの前に確かめ、(4) は書いた file を読み戻して照らす。
  collect 返事 ``reply_<位置 3 桁>_<席 1..3>.json`` を ``validate_reply`` で検査し ``combine3`` で合わせ、§2-5 の集計と配線の門を記録に書く。
          (1)〜(4) が外れたら記録を書かずに止める。(5)(6) は数える(止めない)。記録に理由の自由文・束・原文・span・value は入れない。
          ``--seat-facts`` は司令塔が席の会話の記録(JSONL)から機械で取り出した ``{"<位置 3 桁>_<席 1..3>": {"入力の照合": true|false, "道具の回数": n}}``。無ければ未確認として数える。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import time
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)


def _load(name, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CS = _load("xbrl_unnamed_candidate_2026-10-29.py", "cand_for_eyes")      # doc_lists・zip_path・load_labels・sha16_at・names_sha・jload(engine のパスもここで通る)
T = _load("xbrl_p27_tune_2026-10-27.py", "tune_for_eyes")                # paragraph_of・dumps・sha256_hex・read_json・write_record・assert_record_clean・record_key_leaks・Stop
from adapters.xbrl import instance as I            # noqa: E402
from adapters.xbrl import verify_document as VD    # noqa: E402
from adapters.xbrl import report_customer as RC    # noqa: E402

Stop = T.Stop

SEAL_REL = "docs/XBRL_CANDIDATE_EYES_SEAL_2026-10-30.md"
SEAL_COMMIT = "9d847c0"
IMPL_COMMIT = "cb8612f"
DECL_COMMIT = "f71a9a3"
REC_REL = "fixtures/xbrl/unnamed_candidate_2026-10-29.json"
UNNAMED_REL = "fixtures/xbrl/unnamed_fact_2026-10-29.json"
CAND_KEY = u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"
INJ_KEY = u"注入の書類(出てくる順)"
ENGINE_FILES = ("adapters/xbrl/extract.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py", "adapters/xbrl/resolve.py",
                "adapters/xbrl/comparators.py", "adapters/xbrl/verify_document.py", "adapters/xbrl/report_customer.py")
#: 封の頭の字(候補の測定の門の ENGINE_AT_MEASURE と同じ)。違えば別の木なので止める
ENGINE_SHA16 = {"adapters/xbrl/extract.py": "3cf55966f12919f0", "adapters/xbrl/vocabulary.py": "7fbcfbf0e472f366",
                "adapters/xbrl/recipes.py": "52d645e713c53c1c", "adapters/xbrl/resolve.py": "a41043763c1d4073",
                "adapters/xbrl/comparators.py": "d8706338325e725b", "adapters/xbrl/verify_document.py": "6c76c8ade6c7b1c8",
                "adapters/xbrl/report_customer.py": "bdbaa00a419219fe"}

#: 封 §2-1: 296 行の並びの中の位置(0 始まり、30 行おき)と、下調べ(本番で読まない)の 2 行
POSITIONS = (0, 30, 60, 90, 120, 150, 180, 210, 240, 270)
PROBE_POSITIONS = (15, 165)
READINGS = (u"出所として正しい", u"別の出所", u"文から判断できない")
EXPLANATIONS = (u"単位", u"丸め", u"符号", u"率", u"文の数が違う", u"その他")
SEATS = (u"席1", u"席2", u"席3")
SPLIT = u"割れた"
FAIL_KINDS = (u"JSON でない", u"読みの語が外", u"説明の語が外", u"理由が無い", u"入力の照合が外れた")
FAIL_MISSING = u"返事が無い"                  # 封の 5 種に無い(返事の file が無い席)。封にない判断として報告する
NORM = "NFKC"                                # 封 §6-3: 束の段落は NFKC に正規化した原文から

# 束の見出し(封 §2-3 の字)
H_ROW = u"# 読む行: 位置 %d"
H_PARA = u"## 1 文の段落"
H_NUM = u"## 2 文の数"
H_FACT = u"## 3 道具が示した fact"

#: 封 §2-4 の指示文(blockquote の各行の先頭の「> 」(空行は「>」)を外した字。末尾の改行なし)
READER_PROMPT = u"""あなたは、有価証券報告書の経営成績の分析の文の中の 1 つの数と、道具がその数に対して示した XBRL の fact(要素・期・区分・値)を、1 組だけ読む担当です。

問いは「示された fact は、文のその数が指している出所(概念・期・区分)として正しいか」です。値が同じかどうかではありません(同じ値でないことは分かっています)。

次の 3 つから 1 つを選んでください。
- 出所として正しい: 文の数が指す概念・期・区分と、示された fact の要素・期・区分が合う。値の違いは、文の側の表し方(単位・丸め・符号・率への換算)か、文の側の数の誤りで説明できる。
- 別の出所: 概念・期・区分のどれかが違う(文の数は別の項目・別の期・別の区分・2 つの数の差や和を指している、など)。
- 文から判断できない: 渡された材料では決められない。

「出所として正しい」を選んだときだけ、値の違いの説明を次の 1 語で付けてください: 単位 / 丸め / 符号 / 率 / 文の数が違う / その他。

決まり: 渡した材料(文の段落・文の数・示された fact)だけで読んでください。どちらとも決められないときは「文から判断できない」にしてください。ほかの読み手の返事は見ないでください。理由は 1〜2 文で書いてください。"""

#: 封 §2-4 の「各 subagent に渡す字」(包みの 1 文と path の 2 行。返事の形の欄を含む)
WRAPPER = u'''あなたへの依頼は次の 2 つの file にあります。Read の道具に allow_large を true にして、1 つ目の file(指示)と 2 つ目の file(読む材料)をそれぞれ 1 回だけ読み、指示のとおりにこの 1 組を読んでください。この 2 つの file を読むほかは、道具を使わないでください。返事は次の形の JSON 1 つだけにしてください(前置きや説明は書かない): {"読み": "出所として正しい か 別の出所 か 文から判断できない", "値の違いの説明": "読みが 出所として正しい のときだけ 単位・丸め・符号・率・文の数が違う・その他 のどれか 1 語。ほかは null", "理由": "1〜2 文"}'''

#: 束に入ってはいけない字(封 §2-2・§2-3)。docID・claim の id は束ごとに足す
FORBIDDEN_WORDS = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND", "no_same_value", u"候補", "P22", "P27", "P26")
FORBIDDEN_RE = re.compile(r"E-[1-9]\b")       # 封 §3 の予測の番号


# ======================================================================================================
# 小さい道具
def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()


def inside(path, folder):
    return T.inside(path, folder)


def read_bytes(path):
    with io.open(path, "rb") as fh:
        return fh.read()


def write_new(path, text):
    u"""repo の外に置く file。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop(u"**file が既に在る: %s。止める**" % os.path.basename(path))
    T.write_text(path, text)


def outside_repo(path):
    if inside(path, REPO) or inside(path, os.path.join(os.path.expanduser("~"), ".cache", "audit-core")):
        raise Stop(u"**repo の中か ~/.cache/audit-core の下には書かない: %s。止める**" % path)


def git_out(*a):
    r = subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True)
    return (r.returncode, r.stdout.strip())


def cache_names():
    return {u"edinet": CS.names_sha(CS.EXISTING_CACHE), u"edinet-fresh-2026-10-21": CS.names_sha(CS.FRESH_DIR)}


def pos3(p):
    return "%03d" % p


# ======================================================================================================
# §2-1 選び方
def select_rows(rec, positions=POSITIONS):
    u"""R の候補の行のうち注入の書類(30)の行を (書類の位置, id の昇順) で並べ、``positions`` の行を返す。(注入の書類, 位置の表, 並べた行, 選んだ行)。"""
    inj = rec[INJ_KEY]
    pos = dict((d, i) for i, d in enumerate(inj))
    rows = [r for r in rec[CAND_KEY] if r["doc"] in pos]
    srt = sorted(rows, key=lambda r: (pos[r["doc"]], r["id"]))
    if len(srt) != 296:
        raise Stop(u"**注入の書類の候補の行が 296 でない(%d)。止める**" % len(srt))
    if len(set((r["doc"], r["id"]) for r in srt)) != len(srt):
        raise Stop(u"**(doc, id) が重複している。止める**")
    sel = [dict(srt[p], **{u"位置": p, u"書類の位置": pos[srt[p]["doc"]]}) for p in positions]
    return inj, pos, srt, sel


def check_engine():
    u"""木の engine が封の頭の sha16 と同じで、HEAD と同じ(未 commit の変更なし)であることを確かめる。"""
    now = dict((f, CS.sha16_at(ROOT, f)) for f in ENGINE_FILES)
    if now != ENGINE_SHA16:
        raise Stop(u"**engine の sha16 が封の頭の字と違う: %s。止める**" % T.dumps(now))
    rc, out = git_out("status", "--porcelain", "--", "adapters", "core")
    if rc != 0 or out:
        raise Stop(u"**engine に未 commit の変更が在るか git が読めない。止める**")
    return now


# ======================================================================================================
# §2-3 束(自分で書く: 束の 3 節の字)
def render_dossier(position, paragraph, note, claim, cand, labels):
    name, ctx = RC.split_pointer(cand["pointer"])
    per, mem = RC.split_context(ctx)
    c2 = dict(claim)
    c2["recomputed"] = cand["value"]
    val_text, kind = RC.source_value_report(c2)
    parts = [H_ROW % position, u"",
             H_PARA + ((u"(" + note + u")") if note else u""), paragraph, u"",
             H_NUM, u"文の中の数の窓: %s" % claim.get("span"), u"道具が読んだ値と単位: %s %s" % (claim.get("value"), claim.get("unit")), u"",
             H_FACT, u"ラベル: %s" % RC.element_ja(name, labels), u"要素名: %s" % name, u"期: %s" % per,
             u"区分: %s" % (RC.member_ja(mem, labels) if mem else u"なし"),
             u"値(生の値): %s" % cand["value"], u"値(文の単位・桁に直した字): %s" % val_text, u""]
    return u"\n".join(parts), kind, val_text


def forbidden_in(text, doc, cid):
    u"""束に入ってはいけない字の一覧(0 件が正しい)。"""
    bad = [w for w in FORBIDDEN_WORDS if w in text]
    if doc in text:
        bad.append(u"docID")
    if cid in text:
        bad.append(u"claim の id")
    if FORBIDDEN_RE.search(text):
        bad.append(u"予測の番号")
    return bad


def build_row(sel_row, rec, sha30, labels):
    u"""1 行の材料を取り、配線 (1)(2)(3) を確かめ、束を組む。束と記録に使う事実を返す(file は書かない)。"""
    doc, cid, position = sel_row["doc"], sel_row["id"], sel_row[u"位置"]
    r_row = [r for r in rec[CAND_KEY] if r["doc"] == doc and r["id"] == cid]
    zp = CS.zip_path(doc, True)
    zb = read_bytes(zp)
    zsha = sha256_hex(zb)
    out = VD.verify_document(zb, "P27C", None)
    cl = [c for c in out["claims"] if c["id"] == cid]
    cand = (cl[0].get("candidate") if len(cl) == 1 else None) or {}
    wiring = {
        u"(1) (doc, id) が R の候補の行に在り claim がちょうど 1 つ": len(r_row) == 1 and len(cl) == 1,
        u"(2) 候補の pointer・value が R と同じ字(engine を P27C で走らせ直した出力)": bool(r_row) and len(cl) == 1
            and cand.get("pointer") == r_row[0]["candidate"]["pointer"] and cand.get("value") == r_row[0]["candidate"]["value"]
            and cand.get("pointer") == sel_row["candidate"]["pointer"] and cand.get("value") == sel_row["candidate"]["value"],
        u"(3) ZIP の sha256 が R・取得の記録と一致": zsha == rec[u"書類ごと"][doc][u"zip の sha256"] and zsha == sha30[doc],
    }
    if not all(wiring.values()):
        raise Stop(u"**配線の門が外れた(位置 %d): %s。止める**" % (position, T.dumps(wiring)))
    claim = cl[0]
    inst = I.load_instance(zb)
    tbs = inst["textblocks"]
    name = I.select_mdna(tbs)
    raw = I.strip_html(tbs[name]) if name else u""
    norm = unicodedata.normalize(NORM, raw)
    raw_para, raw_note = T.paragraph_of(raw, claim.get("span"))
    paragraph, note = T.paragraph_of(norm, claim.get("span"))
    blob, kind, val_text = render_dossier(position, paragraph, note, claim, cand, labels)
    cja = RC.candidate_ja(claim, labels)
    if not cja.endswith(val_text):
        raise Stop(u"**候補の字の末尾が値の字と合わない(位置 %d)。止める**" % position)
    bad = forbidden_in(blob, doc, cid)
    return {
        u"位置": position, u"書類の位置": sel_row[u"書類の位置"], "doc": doc, "id": cid, u"配線": wiring, u"束": blob, u"束の字数": len(blob),
        u"束の bytes": len(blob.encode("utf-8")), u"束の sha256": sha256_hex(blob.encode("utf-8")), u"束に入ってはいけない字": bad,
        u"段落の注": note, u"段落は全文": bool(note), u"原文のままの段落の注": raw_note, u"原文の字数": len(raw), u"原文の節に NFKC で変わる字がある": raw != norm,
        u"段落の区切りが変わった(原文のままの段落を NFKC にした字と、NFKC の原文から引いた段落が違う)": (not raw_note) and (not note) and unicodedata.normalize(NORM, raw_para) != paragraph,
        u"補いが効いた(原文のままは全文・NFKC では見つかる)": bool(raw_note) and not note,
        u"段落の字数": len(paragraph), u"原文のままの段落の字数": len(raw_para), u"値の字の種類": kind, u"候補の字": cja,
        u"ZIP の sha256": zsha, u"候補": {"pointers": [cand["pointer"]], u"値": cand["value"], "basis": cand.get("basis")},
    }


def prompt_of(blob):
    return READER_PROMPT + u"\n\n" + blob


# ======================================================================================================
# §2-4 返事の検査・§2-5 合わせ方(自分で書く)
def validate_reply(text):
    u"""``(読み, 説明, 理由)`` か ``(None, 失敗の種類)``。返事の字全体が JSON 1 つ。再試行しない。"""
    try:
        d = json.loads(text)
    except Exception:
        return None, u"JSON でない"
    if not isinstance(d, dict):
        return None, u"JSON でない"
    r = d.get(u"読み")
    if r not in READINGS:
        return None, u"読みの語が外"
    e = d.get(u"値の違いの説明")
    if r == READINGS[0]:
        if e not in EXPLANATIONS:
            return None, u"説明の語が外"
    elif e is not None:
        return None, u"説明の語が外"
    why = d.get(u"理由")
    if not isinstance(why, str) or not why.strip():
        return None, u"理由が無い"
    return (r, e if r == READINGS[0] else None, why), None


def combine3(readings):
    u"""3 席の読み(失敗は None)→ (多数決の読み or 「割れた」, 全員一致か)。失敗が 2 席以上なら割れた。"""
    ok = [r for r in readings if r is not None]
    if len(ok) < 2:
        return SPLIT, False
    c = collections.Counter(ok).most_common(1)[0]
    maj = c[0] if c[1] >= 2 else SPLIT
    return maj, (len(ok) == 3 and c[1] == 3)


# ======================================================================================================
# select
def cmd_select(a):
    outside_repo(a.out)
    rec = CS.jload(REC_REL)
    inj, pos, srt, sel = select_rows(rec)
    if [r["id"] for r in srt] != [r["id"] for r in rec[CAND_KEY] if r["doc"] in pos]:
        raise Stop(u"**記録の並びと封 §2-1 の並びが違う。止める**")
    if len(set(r["doc"] for r in sel)) != 10:
        raise Stop(u"**10 行が 10 の別の書類でない。止める**")
    obj = {u"規則": u"封 §2-1: (注入の書類の位置, id の昇順) の並びの位置 %s" % (list(POSITIONS),), u"296 行": len(srt), u"行": sel}
    write_new(a.out, T.dumps(obj))
    print(T.dumps([{u"位置": r[u"位置"], u"書類の位置": r[u"書類の位置"]} for r in sel]))


# ======================================================================================================
# dossier
def load_select(path):
    obj = T.read_json(path)
    rows = obj[u"行"]
    if [r[u"位置"] for r in rows] != list(POSITIONS):
        raise Stop(u"**select.json の位置が封の定数と違う。止める**")
    return rows


def cmd_dossier(a):
    outside_repo(a.out_dir)
    t0 = time.time()
    before = cache_names()
    check_engine()
    rec = CS.jload(REC_REL)
    rows = load_select(a.select)
    _p, _q, ids30, sha30 = CS.doc_lists()
    if ids30 != rec[INJ_KEY]:
        raise Stop(u"**doc_lists の 30 書類が記録の並びと違う。止める**")
    CS.load_labels()
    labels = CS.LABELS["labels"]
    built = [build_row(r, rec, sha30, labels) for r in rows]
    probe = []
    if a.probe:
        _i, _pp, _s, sel_probe = select_rows(rec, PROBE_POSITIONS)
        probe = [build_row(r, rec, sha30, labels) for r in sel_probe]
    for b in built + probe:
        if b[u"束に入ってはいけない字"]:
            raise Stop(u"**束に入ってはいけない字が在る(位置 %d): %s。何も書かずに止める**" % (b[u"位置"], ",".join(b[u"束に入ってはいけない字"])))
    bad_prompt = [w for w in FORBIDDEN_WORDS if w in READER_PROMPT] + ([u"予測の番号"] if FORBIDDEN_RE.search(READER_PROMPT) else [])
    if bad_prompt:
        raise Stop(u"**指示文に入ってはいけない字が在る。止める**")
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise Stop(u"**out-dir が空でない。止める**")
    index = collections.OrderedDict()
    for b in built:
        p = pos3(b[u"位置"])
        write_new(os.path.join(a.out_dir, "row_%s.txt" % p), b[u"束"])
        write_new(os.path.join(a.out_dir, "prompt_%s.txt" % p), prompt_of(b[u"束"]))
        index[p] = {"file": "row_%s.txt" % p, "bytes": b[u"束の bytes"], "sha256": b[u"束の sha256"],
                    "prompt_file": "prompt_%s.txt" % p, "prompt_sha256": sha256_hex(prompt_of(b[u"束"]).encode("utf-8"))}
    write_new(os.path.join(a.out_dir, "reader_prompt.txt"), READER_PROMPT)
    index["reader_prompt"] = {"file": "reader_prompt.txt", "bytes": len(READER_PROMPT.encode("utf-8")), "sha256": sha256_hex(READER_PROMPT.encode("utf-8"))}
    write_new(os.path.join(a.out_dir, "index.json"), T.dumps(index))
    if a.probe:
        for b in probe:
            write_new(os.path.join(a.out_dir, "probe", "row_%s.txt" % pos3(b[u"位置"])), b[u"束"])
    # (4) 書いた file を読み戻して index.json と照らす
    back = T.read_json(os.path.join(a.out_dir, "index.json"))
    ok4 = all(sha256_hex(read_bytes(os.path.join(a.out_dir, v["file"]))) == v["sha256"] for k, v in back.items() if k != "reader_prompt") \
        and len(back) == 11
    after = cache_names()
    if before != after:
        raise Stop(u"**既存の cache の件数か名前が変わった。止める**")
    if not ok4:
        raise Stop(u"**配線 (4) 束の sha256 が index.json と一致しない。止める**")
    report = collections.OrderedDict()
    report[u"配線の門"] = {u"(1)": [sum(1 for b in built if b[u"配線"][u"(1) (doc, id) が R の候補の行に在り claim がちょうど 1 つ"]), 10],
                      u"(2)": [sum(1 for b in built if b[u"配線"][u"(2) 候補の pointer・value が R と同じ字(engine を P27C で走らせ直した出力)"]), 10],
                      u"(3)": [sum(1 for b in built if b[u"配線"][u"(3) ZIP の sha256 が R・取得の記録と一致"]), 10],
                      u"(4) 束の sha256 が index.json と一致": [10 if ok4 else 0, 10]}
    keep = (u"位置", u"書類の位置", "doc", "id", u"束の字数", u"束の bytes", u"束の sha256", u"束に入ってはいけない字", u"段落の注", u"段落は全文", u"原文のままの段落の注",
            u"原文の字数", u"原文の節に NFKC で変わる字がある", u"段落の区切りが変わった(原文のままの段落を NFKC にした字と、NFKC の原文から引いた段落が違う)", u"補いが効いた(原文のままは全文・NFKC では見つかる)", u"段落の字数", u"原文のままの段落の字数", u"値の字の種類", u"ZIP の sha256")
    report[u"行"] = [dict((k, b[k]) for k in keep) for b in built]
    ch = [b[u"束の字数"] for b in built]
    report[u"束の字数"] = {u"最小": min(ch), u"最大": max(ch), u"300〜6,000 字の外": [b[u"位置"] for b in built if not 300 <= b[u"束の字数"] <= 6000]}
    report[u"段落が全文になった行(位置)"] = [b[u"位置"] for b in built if b[u"段落は全文"]]
    report[u"原文の節に NFKC で変わる字がある行(位置)"] = [b[u"位置"] for b in built if b[u"原文の節に NFKC で変わる字がある"]]
    report[u"段落の区切りが変わった行(位置)"] = [b[u"位置"] for b in built if b[u"段落の区切りが変わった(原文のままの段落を NFKC にした字と、NFKC の原文から引いた段落が違う)"]]
    report[u"補いが効いた行(位置)"] = [b[u"位置"] for b in built if b[u"補いが効いた(原文のままは全文・NFKC では見つかる)"]]
    report[u"原文のままでも全文になる行(位置)"] = [b[u"位置"] for b in built if b[u"原文のままの段落の注"]]
    if probe:
        report[u"下調べの 2 行"] = [dict((k, b[k]) for k in keep) for b in probe]
    report[u"束に入ってはいけない字の検査"] = u"10 本とも 0(" + u"・".join(FORBIDDEN_WORDS) + u"・docID・claim の id・予測の番号)"
    report[u"cache の前後"] = {u"前": before, u"後": after, u"変化なし": before == after}
    report[u"所要秒"] = round(time.time() - t0)
    rp = a.report or os.path.join(os.path.dirname(os.path.abspath(a.out_dir)), "dossier_report.json")
    outside_repo(rp)
    write_new(rp, T.dumps(report))
    print(T.dumps(dict((k, v) for k, v in report.items() if k != u"行")))


# ======================================================================================================
# collect
def reply_name(position, seat_no):
    return "reply_%s_%d.json" % (pos3(position), seat_no)


def read_reply(folder, position, seat_no):
    u"""(読み, 説明, 失敗の種類 or None, 返事の sha256 or None)。file が無ければ失敗 FAIL_MISSING。"""
    p = os.path.join(folder, reply_name(position, seat_no))
    if not os.path.isfile(p):
        return None, None, FAIL_MISSING, None
    b = read_bytes(p)
    try:
        text = b.decode("utf-8")
    except UnicodeDecodeError:
        return None, None, u"JSON でない", sha256_hex(b)
    res, kind = validate_reply(text)
    if res is None:
        return None, None, kind, sha256_hex(b)
    return res[0], res[1], None, sha256_hex(b)


def seat_record(folder, position, seat_no, facts):
    reading, expl, fail, rsha = read_reply(folder, position, seat_no)
    key = "%s_%d" % (pos3(position), seat_no)
    f = (facts or {}).get(key) or {}
    match = f.get(u"入力の照合")
    tools = f.get(u"道具の回数")
    fails = [fail] if fail else []
    if match is False:
        fails.append(u"入力の照合が外れた")
    first = fails[0] if fails else None
    if first:
        reading, expl = None, None
    return {u"読み": reading, u"値の違いの説明": expl, u"失敗": first, u"失敗の全種類": fails, u"入力の照合": match, u"道具の回数": tools, u"返事の sha256": rsha}


def reply_passed(seat):
    u"""返事が §2-4 の検査を通った席(入力の照合の外れは数えない。それは (6))。"""
    return not any(k in seat[u"失敗の全種類"] for k in (FAIL_MISSING,) + FAIL_KINDS[:4])


def band_of(unnamed):
    return dict(((r["doc"], r["id"]), r) for r in unnamed["plain_rows"])


def tally(rows):
    cnt = lambda it: collections.OrderedDict(sorted(collections.Counter(it).items(), key=lambda kv: str(kv[0])))
    seats = collections.OrderedDict((s, cnt(rows_r[u"席"][s][u"読み"] or u"失敗" for rows_r in rows)) for s in SEATS)
    expl = cnt(r[u"席"][s][u"値の違いの説明"] for r in rows for s in SEATS if r[u"席"][s][u"読み"] == READINGS[0])
    ok_by_seat = collections.OrderedDict((s, sum(1 for r in rows if r[u"席"][s][u"読み"] == READINGS[0])) for s in SEATS)
    fails = cnt(r[u"席"][s][u"失敗"] for r in rows for s in SEATS if r[u"席"][s][u"失敗"])
    all3_differ = [r[u"位置"] for r in rows if len(set(r[u"席"][s][u"読み"] for s in SEATS)) == 3 and all(r[u"席"][s][u"読み"] for s in SEATS)]
    maj_ok = [r for r in rows if r[u"多数決"] == READINGS[0]]
    near = [r for r in maj_ok if r[u"診断の帯"][u"帯"] == u"(15% 以内)" or r[u"診断の帯"][u"10 の冪に近い"]]
    return collections.OrderedDict([
        (u"多数決の読みごとの行数", cnt(r[u"多数決"] for r in rows)),
        (u"全員一致の読みごとの行数", cnt(r[u"全員一致の読み"] for r in rows if r[u"全員一致"])),
        (u"割れた行", sum(1 for r in rows if r[u"多数決"] == SPLIT)),
        (u"席ごとの読みの分布(失敗を含む)", seats),
        (u"席ごとの「出所として正しい」の数", ok_by_seat),
        (u"「出所として正しい」を選んだ席の値の違いの説明(席の数)", expl),
        (u"3 席の読みが 3 つとも違う行(位置)", all3_differ),
        (u"失敗の数(種類ごと)", fails),
        (u"失敗の数(全部。分母 %d)" % (len(rows) * 3), sum(fails.values())),
        (u"入力の照合が未確認の席", sum(1 for r in rows for s in SEATS if r[u"席"][s][u"入力の照合"] is None)),
        (u"入力の照合が外れた席", sum(1 for r in rows for s in SEATS if r[u"席"][s][u"入力の照合"] is False)),
        (u"道具を使った席", sum(1 for r in rows for s in SEATS if (r[u"席"][s][u"道具の回数"] or 0) > 0)),
        (u"段落が全文になった行(位置)", [r[u"位置"] for r in rows if r[u"束"][u"段落は全文"]]),
        (u"E-9 多数決が「出所として正しい」の行", {u"行数": len(maj_ok), u"帯が 15% 以内か 10 の冪に近い": len(near),
                                              u"過半": (len(near) * 2 > len(maj_ok)) if maj_ok else u"該当なし"}),
    ])


def cmd_collect(a):
    outside_repo(a.replies)
    t0 = time.time()
    before = cache_names()
    engine = check_engine()
    rec = CS.jload(REC_REL)
    unnamed = CS.jload(UNNAMED_REL)
    bands = band_of(unnamed)
    sel_rows = load_select(a.select)
    _p, _q, ids30, sha30 = CS.doc_lists()
    if ids30 != rec[INJ_KEY]:
        raise Stop(u"**doc_lists の 30 書類が記録の並びと違う。止める**")
    CS.load_labels()
    labels = CS.LABELS["labels"]
    ddir = a.dossier_dir or os.path.join(os.path.dirname(os.path.abspath(a.select)), "dossier")
    index = T.read_json(os.path.join(ddir, "index.json"))
    facts = T.read_json(a.seat_facts) if a.seat_facts else None
    rows = []
    gate = {u"(1)": 0, u"(2)": 0, u"(3)": 0, u"(4)": 0}
    for sr in sel_rows:
        b = build_row(sr, rec, sha30, labels)          # (1)(2)(3) が外れればここで止まる
        gate[u"(1)"] += 1
        gate[u"(2)"] += 1
        gate[u"(3)"] += 1
        p = pos3(sr[u"位置"])
        on_disk = sha256_hex(read_bytes(os.path.join(ddir, index[p]["file"])))
        if not (on_disk == index[p]["sha256"] == b[u"束の sha256"]):
            raise Stop(u"**配線 (4) 束の sha256 が index.json か組み直しと一致しない(位置 %d)。記録を書かずに止める**" % sr[u"位置"])
        gate[u"(4)"] += 1
        seats = collections.OrderedDict((s, seat_record(a.replies, sr[u"位置"], i + 1, facts)) for i, s in enumerate(SEATS))
        maj, unan = combine3([seats[s][u"読み"] for s in SEATS])
        band = bands.get((sr["doc"], sr["id"]))
        if band is None:
            raise Stop(u"**診断の記録に行が無い(位置 %d)。止める**" % sr[u"位置"])
        rows.append({
            u"位置": sr[u"位置"], u"書類の位置": sr[u"書類の位置"], "doc": sr["doc"], "id": sr["id"], u"候補": b[u"候補"], u"候補の字": b[u"候補の字"],
            u"束": {u"bytes": b[u"束の bytes"], u"字数": b[u"束の字数"], u"sha256": b[u"束の sha256"], u"段落の注": b[u"段落の注"], u"段落は全文": b[u"段落は全文"],
                   u"補いが効いた": b[u"補いが効いた(原文のままは全文・NFKC では見つかる)"]},
            u"席": seats, u"多数決": maj, u"全員一致": unan, u"全員一致の読み": maj if unan else None,
            u"診断の帯": {u"帯": band[u"帯"], u"10 の冪に近い": band[u"10 の冪に近い"]}})
    if not all(v == 10 for v in gate.values()):
        raise Stop(u"**配線の門が 10 / 10 でない。止める**")
    after = cache_names()
    if before != after:
        raise Stop(u"**既存の cache の件数か名前が変わった。記録を書かずに止める**")
    _rc, head = git_out("rev-parse", "HEAD")
    if git_out("merge-base", "--is-ancestor", SEAL_COMMIT, "HEAD")[0] != 0:
        raise Stop(u"**封の commit が HEAD の祖先でない。止める**")
    out = collections.OrderedDict()
    out[u"注意"] = (u"候補の正しさを読み手の席が無改変の 10 行で 1 回だけ見た記録(封 %s)。読みは subagent の読みで人間の読みではない。"
                  u"記録に理由の自由文・束・原文・span・claim の value は入れない(自由文は repo の外)。" % SEAL_REL)
    out[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT, u"実装の commit": IMPL_COMMIT, u"宣言の commit": DECL_COMMIT}
    out[u"HEAD の commit"] = head
    out[u"DEFAULT_PROFILE"] = VD.V.DEFAULT_PROFILE
    out[u"engine sha16"] = engine
    out[u"engine の指紋"] = VD.engine_fingerprint()
    with io.open(os.path.abspath(__file__), "rb") as fh:
        out[u"この script の sha256"] = sha256_hex(fh.read())
    inputs = [REC_REL, UNNAMED_REL, CS.FETCHED_REL, CS.ROSTER_REL]
    out[u"読んだ入力の sha256"] = dict((rel, CS.sha64(rel)) for rel in inputs)
    out[u"ラベル"] = {u"dir": u"~/.cache/audit-core/edinet-taxonomy/2025-11-01", u"名簿": CS.ROSTER_REL, u"読んだ file": CS.LABELS["meta"]}
    out[u"選び方の規則"] = {u"位置": list(POSITIONS), u"下調べの位置(本番で読まない)": list(PROBE_POSITIONS), u"並べ方": u"(注入の書類の位置, id の字の昇順)",
                       u"段落": u"NFKC に正規化した原文から paragraph_of(封 §6-3)"}
    out[u"指示文と包み"] = {u"指示文の sha256": sha256_hex(READER_PROMPT.encode("utf-8")), u"包みの sha256": sha256_hex(WRAPPER.encode("utf-8"))}
    out[u"配線の門"] = {u"(1) 行の一致": [gate[u"(1)"], 10], u"(2) 候補の pointer・value の一致": [gate[u"(2)"], 10], u"(3) ZIP の sha256": [gate[u"(3)"], 10],
                    u"(4) 束の sha256": [gate[u"(4)"], 10], u"(5) 返事の検査(§2-4)を通った席": [sum(1 for r in rows for s in SEATS if reply_passed(r[u"席"][s])), 30],
                    u"(6) 入力の照合": [sum(1 for r in rows for s in SEATS if r[u"席"][s][u"入力の照合"] is True), 30], u"(1)〜(4) が通った": True}
    out[u"行"] = rows
    out[u"集計"] = tally(rows)
    out[u"cache"] = {u"開始": before, u"終了": after, u"変化なし": before == after}
    out[u"所要秒"] = round(time.time() - t0)
    out[u"limits"] = [u"読み手は 1 つの model(3 席)。3 席が揃っても偏りの共有と見分けられない。", u"『正しい』は読み手の読みで正解集合ではない。人の目は入っていない。",
                      u"10 行は 296 行の標本。率を一般化しない。", u"対照なし。", u"道具が読んだ値と文の数の字が対応しない行は、候補の読みと切り分けられない(封 §6-3)。"]
    out[u"key_leaks"] = []
    T.assert_record_clean(out)
    if any(k == u"理由" for k in T.walk_keys(out)):
        raise Stop(u"**記録に理由の欄がある。止める**")
    leaks = T.record_key_leaks(out)
    if leaks:
        raise Stop(u"**鍵らしい字が記録に在る。止める**")
    T.write_record(a.out, out)
    print(T.dumps({u"集計": out[u"集計"], u"配線の門": out[u"配線の門"]}))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    s1 = sub.add_parser("select")
    s1.add_argument("--out", required=True)
    s2 = sub.add_parser("dossier")
    s2.add_argument("--select", required=True)
    s2.add_argument("--out-dir", required=True)
    s2.add_argument("--probe", action="store_true")
    s2.add_argument("--report", default=None)
    s3 = sub.add_parser("collect")
    s3.add_argument("--select", required=True)
    s3.add_argument("--replies", required=True)
    s3.add_argument("--out", required=True)
    s3.add_argument("--dossier-dir", default=None)
    s3.add_argument("--seat-facts", default=None)
    a = ap.parse_args()
    if a.cmd == "select":
        cmd_select(a)
    elif a.cmd == "dossier":
        cmd_dossier(a)
    elif a.cmd == "collect":
        cmd_collect(a)
    else:
        ap.print_help()
        raise SystemExit(2)


if __name__ == "__main__":
    main()
