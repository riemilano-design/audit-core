# -*- coding: utf-8 -*-
"""方式 C の材料(封 docs/DOMAIN1_POC_C_SEAL_2026-10-17.md §1・§2)。

**A に渡した `task.txt` を 1 文字も変えずに接頭とし、末尾に (C) の節を足すだけ。**
A の側は**段 11 の材料作りの module をそのまま呼んで再生成する**(写さない)。
`c_text.startswith(a_text)` が偽なら**実験は無効**にする(封 §5)。

証拠の出どころは **段 11 の B(索引 4,209 行・凍結済み)**。
**候補範囲実験の B′(抜粋 76 行)は使わない**(封 §2-3)。
候補の列挙は **6 欄の鍵が 8 通り以下のときだけ**(封 §2-3)。

**(C) の節の指示の字は封から機械で取り出す**ので、封と材料が食い違うことがない。

    python3 measure/sheet_poc_c_material_2026-10-17.py <出力の親ディレクトリ>
"""
import collections
import hashlib
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")
REPORT = os.path.join(FX, "m11_report_2026-10-16.json")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")
LAB11REC = os.path.join(FX, "m11_label_material_2026-10-16.json")
OUT = os.path.join(FX, "poc_c_material_2026-10-17.json")
SEAL_REL = "docs/DOMAIN1_POC_C_SEAL_2026-10-17.md"
SEAL = os.path.join(ROOT, SEAL_REL)
# **人が決めた数は字で留める**(記憶 `pin-human-decided-numbers-literally`)
MAX_LISTED_KEYS = 8


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


LAB11 = _mod("lab11_for_c", "sheet_m11_label_material_2026-10-16.py")
RUN = _mod("run11_for_c", "sheet_m11_run_2026-10-16.py")
SE = RUN.NEW                       # 段 11 の B の engine
M7 = SE.M7
M2 = RUN.M2
norm = RUN.norm
BANNED = LAB11.BANNED              # **段 11 の禁じ語をそのまま当てる**


# ------------------------------------------------------------------ A の側
def regenerate_a(parent):
    """**A の `task.txt` を段 11 の module で作り直す。**写さない。

    `LAB11.OUT` を差し替えて**凍結した記録を汚さない**
    (段 11 で `M9.PREV` を戻したのと同じ型)。
    """
    tmp = os.path.join(parent, "a_rebuild")
    os.makedirs(tmp, exist_ok=True)
    old_out, old_argv = LAB11.OUT, sys.argv
    LAB11.OUT = os.path.join(tmp, "m11_label_material_rebuilt.json")
    sys.argv = ["sheet_m11_label_material_2026-10-16.py", tmp]
    try:
        LAB11.main()
    finally:
        LAB11.OUT, sys.argv = old_out, old_argv
    out = {}
    for seat in ("seat1", "seat2"):
        p = os.path.join(tmp, "m11_label_%s" % seat, "task.txt")
        out[seat] = io.open(p, encoding="utf-8").read()
    return out


def check_a_matches_frozen(a_texts):
    """**段 11 の記録と字数・先頭 / 末尾の id・問いが一致すること。**"""
    rec = json.load(io.open(LAB11REC, encoding="utf-8"))
    for f in rec["files"]:
        seat = f["seat"]
        if len(a_texts[seat]) != f["chars"]:
            raise AssertionError("**A の %s が段 11 と違う字数: %d != %d**"
                                 % (seat, len(a_texts[seat]), f["chars"]))
        if rec["question"] not in a_texts[seat]:
            raise AssertionError("**問いが段 11 の記録と違う(%s)**" % seat)
    return True


# ------------------------------------------------------------------ 封から取る
def instruction_from_seal(path=None):
    """**(C) の節の指示を封から機械で取り出す。**手で写さない。

    §2-4 の引用(`> ` で始まる行)から markdown の強調を外して返す。
    """
    t = io.open(path or SEAL, encoding="utf-8").read()
    i = t.index("\n### §2-4")
    j = t.index("\n### §2-5", i)
    lines = [l[2:] for l in t[i:j].split("\n") if l.startswith("> ")]
    if not lines:
        raise AssertionError("封 §2-4 に引用が無い")
    return "\n".join(l.replace("**", "") for l in lines)


# ------------------------------------------------------------------ 証拠
def derive(text, args):
    """段 11 の B と**同じ呼び出し順**で候補まで出す(鍵を並べるため)。"""
    raw = M7.fix_total_level(M7.build_index(*args))
    al = SE.alias_table(raw)
    entries = M7.canonicalize(raw, al)
    cues = M7.column_cues(entries)
    vocab = M7.vocabulary(entries)
    claims = M7.extract_claims(text, vocab, cues)
    binds = [M7.bind(c, entries) for c in claims]
    return claims, binds, entries


def keys_of(claim, entries):
    """その主張の候補を **6 欄の鍵ごと**にまとめる(`bind` と同じ数え方)。"""
    cands, _kind, blocked, _info = M7.candidates(claim, entries)
    if blocked:
        return []
    groups = collections.OrderedDict()
    for e in cands:
        groups.setdefault(M7.field_key(e), []).append(e)
    out = []
    for _k, rows in groups.items():
        e = rows[0]
        out.append({"会計": e["scope"], "階層": e["level"],
                    "親": e["parent"] or "", "科目名": e["name"],
                    "列": e["column"],
                    "値": sorted({r["value"] for r in rows}),
                    "位置": sorted({M7.pointer_of(r) for r in rows})})
    return out


def check_matches_frozen(binds):
    """**再現した結果が段 11 の記録と一致すること。**違えば証拠を作らない。"""
    fb = {b["claim_id"]: b for b in
          json.load(io.open(BINDS, encoding="utf-8"))["binds_new"]}
    diff = []
    for b in binds:
        f = fb[b["claim_id"]]
        for k in ("state", "hold_reason", "candidates"):
            if b.get(k) != f.get(k):
                diff.append({"id": b["claim_id"], "欄": k,
                             "再現": b.get(k), "記録": f.get(k)})
    if diff:
        raise AssertionError("**段 11 の記録と違う: %s**"
                             % json.dumps(diff[:5], ensure_ascii=False))
    return True


def say(b, keys):
    """**状態を言い換える**(封 §2-2)。(状態の字, 続きの行) を返す。

    判定を 1 か所に置く。**当てはまらない状態が来たら止める**
    (黙って既定の字を書くと、状態の取り違えが記録に残らない)。
    """
    st, why = b["state"], b.get("hold_reason") or ""
    if st == "GROUNDED":
        ev = b["evidence"]
        lines = [fields_line(ev["scope"], ev["level"], ev["parent"],
                             ev["name"], ev["column"], ev["value"])]
        lines.append("  原資料の位置: %s" % pos_line(b["pointer"],
                                               ev.get("duplicate_pointers")))
        return "参照先を 1 行に特定できた", lines
    if st == "VALUE_MISMATCH":
        if len(keys) != 1:
            raise AssertionError("値が合わない件の鍵が %d 通り" % len(keys))
        k = keys[0]
        lines = [fields_line(k["会計"], k["階層"], k["親"], k["科目名"],
                             k["列"], b["recomputed"])]
        lines.append("  原資料の位置: %s" % pos_line(b["pointer"], None))
        return ("6 欄は 1 行に特定できたが、その行の値は主張の金額と一致しない"
                "(その行の値: %d)" % b["recomputed"]), lines
    if st == "POINTER_NOT_FOUND":
        return "文から範囲を特定できなかった", []
    if st == "UNVERIFIABLE":
        if "の手がかりが 2 つ以上" in why:
            what = "列" if why.startswith("列") else "階層"
            got = why.split(": ", 1)[1]
            return ("文の中に%sの手がかりが 2 つ以上在り、どれを指すか"
                    "決められなかった: %s" % (what, got)), []
        if "会計が未確認" in why:
            return "会計名の対応が確認できなかった", []
        if "6 欄が一意でない" in why:
            n = int(why.split("(")[1].split(" 通り")[0])
            if n != len(keys):
                raise AssertionError("鍵の数が合わない: %d != %d" % (n, len(keys)))
            head = ("候補が %d 通り在り、1 行に絞れなかった"
                    "(この道具は値が合う行を選ぶことはしない)" % n)
            if n > MAX_LISTED_KEYS:
                return head, ["  候補は %d 通りあるので並べていない(上限 %d 通り)"
                              % (n, MAX_LISTED_KEYS)]
            lines = []
            for i, k in enumerate(keys, 1):
                lines.append("  候補%d: %s" % (i, fields_line(
                    k["会計"], k["階層"], k["親"], k["科目名"], k["列"],
                    k["値"][0] if len(k["値"]) == 1 else k["値"]).strip()))
                lines.append("        原資料の位置: %s" % "・".join(k["位置"]))
            return head, lines
        if "値が file 間で食い違う" in why:
            return "同じ欄の値が資料の間で食い違っていた", []
    raise AssertionError("**言い換えられない状態: %s / %s**" % (st, why))


def fields_line(scope, level, parent, name, column, value):
    return ("  参照先: 会計=%s / 階層=%s / 親=%s / 科目名=%s / 列=%s / 値=%s"
            % (scope, level, parent or "", name, column, value))


def pos_line(pointer, dups):
    others = [p for p in (dups or []) if p != pointer]
    if others:
        return "%s(同じ数が載っている別の位置: %s)" % (pointer, "・".join(others))
    return "%s" % pointer


def check_banned(text, banned=None):
    """**禁じ語を当てる。**判定を 1 か所に置く(門が壊した字で当てられるように)。"""
    for w in (BANNED if banned is None else banned):
        if w in text:
            raise AssertionError("**禁じた語が材料に在る: %s**" % w)
    return True


def check_prefix(c, a):
    """**A が 1 文字も変わらずに接頭になっていること**(封 §1。偽なら実験は無効)。"""
    if not c.startswith(a):
        raise AssertionError("**A が接頭になっていない。実験は無効**")
    return True


def evidence_block(order, binds, keys_by_id, instruction):
    body = ["", instruction, ""]
    for cid in order:
        b = binds[cid]
        head, lines = say(b, keys_by_id[cid])
        body.append("- id: %s / 道具の状態: %s" % (cid, head))
        body.extend(lines)
    return "\n".join(body)


def main():
    parent = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out")
    if os.path.exists(OUT):
        raise SystemExit("材料が既に在る: %s(作り直さない)" % OUT)
    os.makedirs(parent, exist_ok=True)
    shas = RUN.check_shas()
    a_texts = regenerate_a(parent)
    check_a_matches_frozen(a_texts)
    instruction = instruction_from_seal()

    report = json.load(io.open(REPORT, encoding="utf-8"))["report"]
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    args = (M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
            M2.parse_meisai(books[M2.MEISAI]))
    claims, binds, entries = derive(report, args)
    if len(claims) != 35:
        raise SystemExit("**主張が %d 件。35 件でないので実験は無効**" % len(claims))
    check_matches_frozen(binds)
    bd = {b["claim_id"]: b for b in binds}
    keys_by_id = {c["id"]: keys_of(c, entries) for c in claims}

    lab = json.load(io.open(LAB11REC, encoding="utf-8"))
    order1 = [c["id"] for c in
              json.load(io.open(BINDS, encoding="utf-8"))["claims"]
              if not c.get("skipped")]
    orders = {"seat1": order1, "seat2": list(reversed(order1))}
    made, states = [], collections.Counter(b["state"] for b in binds)
    for seat in ("seat1", "seat2"):
        a = a_texts[seat]
        block = evidence_block(orders[seat], bd, keys_by_id, instruction)
        c = a + "\n" + block + "\n"
        check_prefix(c, a)
        check_banned(c)
        d = os.path.join(parent, "poc_c_%s" % seat)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "task.txt")
        io.open(p, "w", encoding="utf-8").write(c)
        made.append({
            "seat": seat, "path": p,
            "model": [s["model"] for s in lab["seats"] if s["seat"] == seat][0],
            "order": [s["order"] for s in lab["seats"] if s["seat"] == seat][0],
            "A の字数": len(a), "C の字数": len(c),
            "足した字数": len(c) - len(a),
            "A が接頭": c.startswith(a),
            "A の sha256": hashlib.sha256(a.encode("utf-8")).hexdigest(),
            "C の sha256": hashlib.sha256(c.encode("utf-8")).hexdigest(),
            "先頭の id": orders[seat][0], "末尾の id": orders[seat][-1]})
        print("%s: A %d 字 + 証拠 %d 字 = %d 字 -> %s"
              % (seat, len(a), len(c) - len(a), len(c), p))

    listed = sorted(cid for cid, ks in keys_by_id.items()
                    if bd[cid]["state"] == "UNVERIFIABLE" and ks
                    and len(ks) <= MAX_LISTED_KEYS)
    not_listed = sorted(cid for cid, ks in keys_by_id.items()
                        if len(ks) > MAX_LISTED_KEYS)
    rec = {"seal": SEAL_REL,
           "step": "封 §9 の 2。**生成より先に commit する。費用 0 USD**",
           "engine_sha": shas, "min_independent": SE.MIN_INDEPENDENT,
           "証拠の出どころ": ("fixtures/sheet/m11_binds_2026-10-16.json の "
                       "`binds_new`(**段 11 の B。索引 4,209 行**)"),
           "**B′(抜粋 76 行)は使っていない**": True,
           "再現が段 11 の記録と一致": True,
           "索引の行": len(entries), "主張の数": len(claims),
           "状態の内訳": dict(states),
           "鍵を並べた件": {"件数": len(listed), "ids": listed},
           "鍵を並べなかった件(上限 %d 通り超え)" % MAX_LISTED_KEYS: {
               "件数": len(not_listed), "ids": not_listed},
           "上限": MAX_LISTED_KEYS,
           "(C) の指示": instruction,
           "指示の出どころ": "**封 §2-4 から機械で取り出した**(手で写していない)",
           "banned_checked": BANNED,
           "足していないもの": ["正解集合", "別枠", "G-独立-1〜4", "採点の規則",
                        "封の内容", "A の答え", "B の採点結果",
                        "候補範囲実験の結果", "Core の判定が正しいかどうか",
                        "段 3〜段 11 の結果"],
           "注": ("**候補は索引 4,209 行から来るので、抜粋 76 行の外の行も出る。**"
                 "だから C の入力は「A と同じ資料」ではなく"
                 "「**A の資料 + Core の証拠**」である(封 §2-3・§8 の 2)"),
           "files": made}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("状態の内訳: %s" % json.dumps(dict(states), ensure_ascii=False))
    print("鍵を並べた %d 件 / 並べなかった %d 件(上限 %d 通り)"
          % (len(listed), len(not_listed), MAX_LISTED_KEYS))
    print("->", OUT)


if __name__ == "__main__":
    main()
