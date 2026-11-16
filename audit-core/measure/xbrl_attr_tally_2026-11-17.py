# -*- coding: utf-8 -*-
u"""封 docs/XBRL_ATTR_TALLY_SEAL_2026-11-17.md ― AT(便をまたいだ集計。「値が違う」と「結べたが別のもの」の行のうち、数の身元の 5 つの属性の取り違えに写る行の割合を、
既に在る型の読みの記録だけで数える)の集計。**取得 0・0 USD・通信なし・鍵は読まない・LLM は呼ばない。標準ライブラリだけ。engine(``core/``・``adapters/``)は import しない・呼ばない。材料の本は開かない。**

    python3 measure/xbrl_attr_tally_2026-11-17.py --write    # 記録 fixtures/xbrl/attr_tally/tally_2026-11-17.json を書く(在れば止まる)
    python3 measure/xbrl_attr_tally_2026-11-17.py --check    # 書かずに同じ内容を作り、在る記録と byte で比べる(--write が無ければ同じ)

実装の注(封の字の解釈。封に無い決めはここに書き、報告にも書いた):
- 入力は封 §1 の 5 つの記録。sha256 が封の表と違えば止まる。各記録の**行**から数え直し、記録の中の集計の欄(型の集計・b の違うものの集計・読む行の数・細目の集計)と違えば止まる。
  近い行(5 の記録)は ``型の集計(A)``・``型の集計(B)`` の欄が行から数え直せない(行に A・B の別が無い)ので、この 2 つは確かめない。
- 写しの表(封 §2-1)は字で持つ(``TABLE``。門が封の表と 1 行ずつ比べる)。表に無い型の字・細目が要るのに無い行・細目の字が型と合わない行は止まる。
  TSS の型 ケ は、細目が在ることを確かめたうえで細目の字によらず ケ の行(外(分けられない))に写す(封 §2-1 の「ケ(ケ1 を含む)」)。
- 1 株あたり(封 §2-1 の末の注): 写す先の無い属性。数は作りで 0。記録にも「測った 0 ではない」と書く。
- KAM の本の片寄り(封 §3 の 7)は V 連結と V 単体の行を足して数える(本の # は同じ states の本の番号で、連結と単体で同じ本を指す)。YS は 3 つの節を足す。封は足し方を決めていない。
- 率は分子と分母の整数を並べ、率の字は小数 1 桁の %(四捨五入は切り上げ側。整数だけで計算する)。分母が 0 のときは率の字を「分母 0」にする。
- 記録は行・文・値・本の # を持たない。数だけ。HEAD の commit は書かない(組み直しが byte で同じになるように)。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SEAL_REL = "docs/XBRL_ATTR_TALLY_SEAL_2026-11-17.md"
SEAL_COMMIT = "52f3a228"
SCRIPT_REL = "measure/xbrl_attr_tally_2026-11-17.py"
OUT_REL = "fixtures/xbrl/attr_tally/tally_2026-11-17.json"

#: 封 §1 の入力(# , 便, 記録, sha256)。違えば止まる
INPUTS = (
    (1, u"KAM", "fixtures/xbrl/kam/read_types_2026-11-15.json", "8c9fe6b8def7430908bf925f697ea5a1b1d634dd754933aab7c71b0a913c964a"),
    (2, u"YS", "fixtures/xbrl/yuho_sections/read_types_2026-11-16.json", "9087a95d0f51e559012b72a9f5f2af7c9575e57589120b50b7ba1d93f46fd3bb"),
    (3, u"TSS", "fixtures/xbrl/tanshin_self/vm_types_2026-11-14.json", "d1392722f345c408372ec644e15170463554683c3c7ff3951a51d9f66a1f5183"),
    (4, u"TSS", "fixtures/xbrl/tanshin_self/vm_types_subreading_2026-11-14.json", "d5d336bf3eeda37b36db41c02f8a84142257c22921daeb56b5818b262b3235bb"),
    (5, u"TSS", "fixtures/xbrl/tanshin_self/near_types_2026-11-14.json", "f59cfc68a6ddf98b9a713efdda52f8bf04d183bc9b415964bb724812810f779f"))

#: 封 §2-1 の写しの表(便, 型・細目, 写す先(太字の ** を外した字), 理由)。封の表と 1 行ずつ同じ
TABLE = (
    (u"KAM・YS", u"ア", u"範囲", u"一部分の数を全体の fact と比べた"),
    (u"KAM・YS", u"ウ", u"範囲", u"連結と単体の取り違え"),
    (u"KAM・YS", u"エ", u"期", u"期の取り違え"),
    (u"KAM・YS", u"オ", u"項目", u"定義の違い"),
    (u"KAM・YS", u"カ", u"単位", u"丸め・単位(細目が無いので全部を内に写す。§5)"),
    (u"KAM・YS", u"イ", u"外(見積り・計画)", u"実績の数でない。5 つの属性に無い"),
    (u"KAM・YS", u"キ", u"外(符号)", u"5 つの属性に無い"),
    (u"KAM・YS", u"ケ", u"外(分けられない)", u""),
    (u"KAM・YS", u"ク", u"分母から除く", u"本当の差の候補。警報が正しいかもしれない行で、偽の警報と呼べない"),
    (u"TSS", u"ア", u"範囲", u"セグメント等の数を全社の fact と比べた"),
    (u"TSS", u"イ1・イ2", u"範囲", u"部分と全体(イ2 は向きが逆)"),
    (u"TSS", u"イ3", u"項目", u"となりの内訳・別の表の要素"),
    (u"TSS", u"オ1・オ2", u"項目", u"定義・別の表の同じ名前"),
    (u"TSS", u"カ3", u"単位", u"率の丸め"),
    (u"TSS", u"カ1", u"外(数の読み取り)", u"続けて書いた数の後ろだけを読んだ。属性でなく読み取りの欠陥"),
    (u"TSS", u"カ2", u"外(計算の形)", u"増減率と比率の違い"),
    (u"TSS", u"ウ", u"外(見積り・計画)", u""),
    (u"TSS", u"エ", u"外(向き・増減の書き方)", u""),
    (u"TSS", u"キ", u"外(符号)", u""),
    (u"TSS", u"ケ(ケ1 を含む)", u"外(分けられない)", u"ケ1 は「関係のない別の要素」だが、元の型が ケ なので内に写さない"),
    (u"TSS", u"ク", u"分母から除く", u""))

ATTRS = (u"項目", u"期", u"範囲", u"単位", u"1 株あたり")
NO_MAPPING_ATTR = u"1 株あたり"
EXCLUDE = u"分母から除く"
KIND_IN, KIND_OUT, KIND_DROP = u"内", u"外", u"除く"
#: G の b の「違うもの」→ 属性(封 §2-2。側は範囲)
DIFF_TO_ATTR = collections.OrderedDict([(u"項目", u"項目"), (u"範囲", u"範囲"), (u"側", u"範囲"), (u"期", u"期")])
DIFFS = tuple(DIFF_TO_ATTR)

V_TYPES = tuple(u"アイウエオカキクケ")
G_TYPES = (u"a", u"b", u"c")
DETAIL_TYPES = tuple(u"イオカケ")          # TSS で細目を持つはずの型
NEAR_TYPES = tuple(u"あいうえお")
GROUPS = {
    u"KAM": (u"V 連結", u"V 単体", u"G 連結", u"G 単体"),
    u"YS": (u"V 研究", u"V 設備", u"V 配当", u"G 研究", u"G 設備", u"G 配当")}
ROW_FIELDS = [u"読みの組", u"本の #", u"文の番号", u"位置", u"型", u"違うもの"]
VM_FIELDS = [u"標本の番号", u"本の #", u"文の番号", u"位置", u"型"]
SUB_FIELDS = [u"標本の番号", u"型", u"細目"]

LIMITS = (
    u"型は AI の席(司令塔)1 席が付けた。盲検でなく、人は読んでいない。この集計はその字を数え直すだけで、型の正しさは 1 つも確かめない",
    u"写しの表は、YS と TSS の型の集計を見たあとに書いたあと知恵。写しの決め方しだいで率は動く。外の理由ごとの数を必ず並べる",
    u"語彙が便で違う。TSS は細目で割ったが KAM・YS には細目が無い。同じ字(カ・オ)が同じ中身とは限らない",
    u"行が少ない(YS の V は 18 行、KAM の V は 37 行)。1〜2 行で率が数ポイント動く",
    u"「属性の取り違えに写る」は「属性を条件に入れれば止まる」ではない。属性を足したときに正しい結びがどれだけ減るかは測っていない",
    u"G の側は反証できない作り(b の字が項目・範囲・側・期のどれかが違う、なので全部が属性の内に入る)",
    u"3 つの便は有報・監査報告書・短信で、上場会社の開示だけ。「あらゆる文書」の根拠にならない")


class Stop(SystemExit):
    u"""止める。"""


# ---------------------------------------------------------------- 小さい道具
def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    with io.open(p, "rb") as fh:
        return sha256_bytes(fh.read())


def pct(n, d):
    u"""小数 1 桁の %(整数だけで計算。四捨五入は切り上げ側)。分母 0 は「分母 0」。"""
    if d == 0:
        return u"分母 0"
    tenths = (n * 2000 + d) // (2 * d)
    return u"%d.%d%%" % (tenths // 10, tenths % 10)


def rate(n, d):
    return collections.OrderedDict([(u"分子", n), (u"分母", d), (u"率", pct(n, d))])


def od(pairs=()):
    return collections.OrderedDict(pairs)


# ---------------------------------------------------------------- 写しの表
def table_lookup(batch):
    u"""便("KAM"・"YS"・"TSS")の写しの表を {型または細目: (種別, 先の字)} にする。先の字: 内なら属性、外なら理由、除くなら空。"""
    out = {}
    for b, keys, dest, _why in TABLE:
        if batch not in b.split(u"・"):
            continue
        if dest == EXCLUDE:
            kind, name = KIND_DROP, u""
        elif dest.startswith(u"外(") and dest.endswith(u")"):
            kind, name = KIND_OUT, dest[2:-1]
        elif dest in ATTRS and dest != NO_MAPPING_ATTR:
            kind, name = KIND_IN, dest
        else:
            raise Stop(u"**写しの表の先の字が決まらない: %s。止める**" % dest)
        for k in keys.split(u"(")[0].split(u"・"):
            if k in out:
                raise Stop(u"**写しの表に同じ型・細目が 2 度出る: %s。止める**" % k)
            out[k] = (kind, name)
    return out


def out_reasons(batch):
    seen = []                                                       # 表の並びの順に理由を集める
    for b, _keys, dest, _why in TABLE:
        if batch in b.split(u"・") and dest.startswith(u"外(") and dest[2:-1] not in seen:
            seen.append(dest[2:-1])
    return seen


# ---------------------------------------------------------------- 入力
def load_inputs(root=ROOT):
    u"""5 つの記録を sha256 で確かめて読む。{#: 記録}。"""
    out = {}
    for no, _batch, rel, want in INPUTS:
        p = os.path.join(root, rel)
        if not os.path.isfile(p):
            raise Stop(u"**入力が無い: %s。止める**" % rel)
        if sha256_file(p) != want:
            raise Stop(u"**入力の sha256 が封と違う: %s。止める**" % rel)
        with io.open(p, encoding="utf-8") as fh:
            out[no] = json.load(fh)
    return out


def _counter_eq(label, got, want):
    if dict(got) != dict(want):
        raise Stop(u"**行から数え直した数が記録の集計の欄と違う(%s)。止める**" % label)


def read_ys_kam_rows(rec, batch):
    u"""KAM・YS の記録の行を検査して返す。組ごとの型の数・b の違うものの数・読む行の数を、記録の集計の欄と照らす。"""
    groups = GROUPS[batch]
    if rec.get(u"行の欄") != ROW_FIELDS:
        raise Stop(u"**%s の行の欄が決めと違う。止める**" % batch)
    rows = rec.get(u"行")
    if not isinstance(rows, list):
        raise Stop(u"**%s の行が無い。止める**" % batch)
    for r in rows:
        if len(r) != len(ROW_FIELDS) or r[0] not in groups or not isinstance(r[1], int):
            raise Stop(u"**%s の行の形が決めと違う。止める**" % batch)
        types = G_TYPES if r[0].startswith(u"G") else V_TYPES
        if r[4] not in types:
            raise Stop(u"**%s の行の型の字が決めの外: %s。止める**" % (batch, r[4]))
        if (r[4] == u"b") != (r[5] is not None) or (r[5] is not None and r[5] not in DIFFS):
            raise Stop(u"**%s の行の「違うもの」が型 b と合わない。止める**" % batch)
    by = collections.OrderedDict((g, [r for r in rows if r[0] == g]) for g in groups)
    for g, grows in by.items():
        types = G_TYPES if g.startswith(u"G") else V_TYPES
        c = collections.Counter(r[4] for r in grows)
        _counter_eq(u"%s 型の集計 %s" % (batch, g), od((t, c.get(t, 0)) for t in types), rec[u"型の集計"][g])
        if g.startswith(u"G"):
            d = collections.Counter(r[5] for r in grows if r[4] == u"b")
            _counter_eq(u"%s b の違うもの %s" % (batch, g), od((x, d.get(x, 0)) for x in DIFFS), rec[u"b の違うものの集計"][g])
        if rec[u"読む行の規則"][u"読む行の数"][g] != len(grows):
            raise Stop(u"**%s の読む行の数が行と違う(%s)。止める**" % (batch, g))
    if rec[u"読む行の規則"][u"読む行の数の合計"] != len(rows):
        raise Stop(u"**%s の読む行の数の合計が行と違う。止める**" % batch)
    return by


def read_tss(vm, sub, near):
    u"""TSS の 3 つの記録を検査する。標本の行(型・細目)と、近い行の型の数を返す。"""
    if vm.get(u"行の欄") != VM_FIELDS or sub.get(u"行の欄") != SUB_FIELDS:
        raise Stop(u"**TSS の行の欄が決めと違う。止める**")
    rows = vm[u"行"]
    if len(rows) != vm[u"標本の規則"][u"標本の数"]:
        raise Stop(u"**TSS の標本の数が行と違う。止める**")
    ids = [r[0] for r in rows]
    if len(set(ids)) != len(ids):
        raise Stop(u"**TSS の標本の番号が重なる。止める**")
    for r in rows:
        if len(r) != len(VM_FIELDS) or r[4] not in V_TYPES or not isinstance(r[1], int):
            raise Stop(u"**TSS の標本の行の形か型の字が決めの外。止める**")
    c = collections.Counter(r[4] for r in rows)
    _counter_eq(u"TSS 型の集計", od((t, c.get(t, 0)) for t in V_TYPES), vm[u"型の集計"])
    type_of = {r[0]: r[4] for r in rows}
    detail_of = {}
    for r in sub[u"行"]:
        if len(r) != len(SUB_FIELDS) or r[0] not in type_of or r[0] in detail_of:
            raise Stop(u"**TSS の細目の行の形が決めと違う(標本に無い・重なる)。止める**")
        if r[1] != type_of[r[0]] or r[1] not in DETAIL_TYPES or r[2] not in sub[u"細目の字"] or not r[2].startswith(r[1]):
            raise Stop(u"**TSS の細目の字が型と合わない。止める**")
        detail_of[r[0]] = r[2]
    need = set(i for i, t in type_of.items() if t in DETAIL_TYPES)
    if need != set(detail_of):
        raise Stop(u"**細目を持つはずの型の行に細目が無い(または余る)。止める**")
    cd = collections.Counter(detail_of.values())
    _counter_eq(u"TSS 細目の集計", od((k, cd.get(k, 0)) for k in sub[u"細目の字"]), sub[u"細目の集計"])
    # 近い行
    if near.get(u"行の欄") != VM_FIELDS:
        raise Stop(u"**近い行の欄が決めと違う。止める**")
    nrows = near[u"行"]
    for r in nrows:
        if len(r) != len(VM_FIELDS) or r[4] not in NEAR_TYPES:
            raise Stop(u"**近い行の形か型の字が決めの外。止める**")
    cn = collections.Counter(r[4] for r in nrows)
    _counter_eq(u"近い行の型の集計", od((t, cn.get(t, 0)) for t in NEAR_TYPES), near[u"型の集計"])
    if near[u"読む行の規則"][u"読む行の数"] != len(nrows):
        raise Stop(u"**近い行の読む行の数が行と違う。止める**")
    return [(r[1], r[4], detail_of.get(r[0])) for r in rows], cn, near[u"読む行の規則"][u"近い行の数"], len(nrows)


# ---------------------------------------------------------------- 数える
def classify(items, lookup, label):
    u"""items = [(本の #, 型または細目の字)]。{行の数, 内, 外, 除く, 属性ごと, 外の理由ごと, 型・細目ごと, 本ごとの内の行}。表に無い字は止まる。"""
    attrs = collections.Counter()
    reasons = collections.Counter()
    keys = collections.Counter()
    drop = 0
    per_book = collections.Counter()
    for book, key in items:
        if key not in lookup:
            raise Stop(u"**写しの表に無い型・細目の字(%s)。止める**" % label)
        kind, name = lookup[key]
        keys[key] += 1
        if kind == KIND_IN:
            attrs[name] += 1
            per_book[book] += 1
        elif kind == KIND_OUT:
            reasons[name] += 1
        else:
            drop += 1
    return {"n": len(items), "in": sum(attrs.values()), "out": sum(reasons.values()), "drop": drop,
            "attrs": attrs, "reasons": reasons, "keys": keys, "books": per_book}


def v_block(cl, reason_order, key_order, with_rates=True):
    n_in, n_out, n_drop, n = cl["in"], cl["out"], cl["drop"], cl["n"]
    b = od([(u"読んだ行の数", n), (u"属性の内の行", n_in), (u"外の行", n_out), (u"ク の行(分母から除く)", n_drop)])
    if with_rates:
        b[u"率(主。分母は ク を除く)"] = rate(n_in, n - n_drop)
        b[u"率(2 本目。分母に ク を入れる)"] = rate(n_in, n)
    b[u"属性ごとの行の数"] = od([(a, cl["attrs"].get(a, 0)) for a in ATTRS])
    b[u"1 株あたりについて"] = u"この属性に写る型は表に無い。0 は作りで、測った 0 ではない"
    b[u"外の理由ごとの行の数"] = od([(r, cl["reasons"].get(r, 0)) for r in reason_order])
    b[u"型・細目ごとの行の数"] = od([(k, cl["keys"].get(k, 0)) for k in key_order])
    return b


def book_spread(cl):
    per = cl["books"]
    n_in = cl["in"]
    mx = max(per.values()) if per else 0
    return od([(u"属性の内の行を持つ本の数", len(per)), (u"いちばん多い 1 本が持つ内の行の数", mx),
               (u"その本の行の割合", rate(mx, n_in)), (u"属性の内の行の数", n_in)])


def g_block(rows):
    u"""rows = [型, 違うもの]。a・b・c の数、b の属性ごと(側は範囲)、c / (b + c)。"""
    c = collections.Counter(t for t, _ in rows)
    a, b, cc = c.get(u"a", 0), c.get(u"b", 0), c.get(u"c", 0)
    raw = collections.Counter(d for t, d in rows if t == u"b")
    attr = collections.Counter()
    for d, k in raw.items():
        attr[DIFF_TO_ATTR[d]] += k
    return od([
        (u"読んだ行の数", len(rows)), (u"a(合う)", a), (u"b(違うもの)", b), (u"c(分けられない)", cc),
        (u"b の違うもの(記録の字のまま)", od((d, raw.get(d, 0)) for d in DIFFS)),
        (u"b の属性ごと(側は範囲に写す)", od((x, attr.get(x, 0)) for x in ATTRS)),
        (u"b のうち範囲に写る行(範囲 + 側)", rate(attr.get(u"範囲", 0), b)),
        (u"c /(b + c)", rate(cc, b + cc))])


def tally(inputs):
    u"""入力(5 つの記録を読んだもの)から数だけの OrderedDict を作る。記録の集計の欄と違えば止まる。"""
    res = od()
    sums = []                                                       # 参考の合計用 (内, ク を除く分母, ク を入れた分母)
    for no, batch in ((1, u"KAM"), (2, u"YS")):
        by = read_ys_kam_rows(inputs[no], batch)
        lookup = table_lookup(batch)
        reasons = out_reasons(batch)
        keys = [k for _b, ks, _d, _w in TABLE if batch in _b.split(u"・") for k in ks.split(u"(")[0].split(u"・")]
        v_groups = [g for g in GROUPS[batch] if g.startswith(u"V")]
        g_groups = [g for g in GROUPS[batch] if g.startswith(u"G")]
        all_v = [(r[1], r[4]) for g in v_groups for r in by[g]]
        cl = classify(all_v, lookup, batch)
        v = v_block(cl, reasons, keys)
        v[u"組別"] = od((g, v_block(classify([(r[1], r[4]) for r in by[g]], lookup, batch), reasons, keys, with_rates=False)) for g in v_groups)
        v[u"本の片寄り"] = book_spread(cl)
        g = od((gg, g_block([(r[4], r[5]) for r in by[gg]])) for gg in g_groups)
        g[u"合計"] = g_block([(r[4], r[5]) for gg in g_groups for r in by[gg]])
        res[batch] = od([(u"V", v), (u"G", g)])
        sums.append((cl["in"], cl["n"] - cl["drop"], cl["n"]))
    items, near_counts, near_pop, near_read = read_tss(inputs[3], inputs[4], inputs[5])
    lookup = table_lookup(u"TSS")
    reasons = out_reasons(u"TSS")
    keys = [k for b, ks, _d, _w in TABLE if u"TSS" in b.split(u"・") for k in ks.split(u"(")[0].split(u"・")]
    # 型の字 → 表の字(細目を持つ型は細目の字。ケ は細目の字によらず ケ)
    pairs = []
    for book, t, d in items:
        if t in DETAIL_TYPES:
            if d is None:
                raise Stop(u"**細目を持つはずの型の行に細目が無い。止める**")
            pairs.append((book, u"ケ" if t == u"ケ" else d))
        else:
            pairs.append((book, t))
    cl = classify(pairs, lookup, u"TSS")
    v = v_block(cl, reasons, keys)
    v[u"本の片寄り"] = book_spread(cl)
    res[u"TSS"] = od([(u"V", v), (u"近い行の型(並べるだけ。率に入れない。写さない)", od([
        (u"近い行の数(母)", near_pop), (u"読む行の数", near_read), (u"型ごとの行の数", od((t, near_counts.get(t, 0)) for t in NEAR_TYPES))]))])
    sums.append((cl["in"], cl["n"] - cl["drop"], cl["n"]))
    n_in = sum(s[0] for s in sums)
    d_main = sum(s[1] for s in sums)
    d_all = sum(s[2] for s in sums)
    res[u"参考の合計"] = od([
        (u"V の行の単純な合計(KAM + YS + TSS。分母は ク を除く)", rate(n_in, d_main)),
        (u"分母に ク を入れた場合", rate(n_in, d_all)),
        (u"注", u"母集団の率ではない。引き方が違う(KAM・YS は全部の行、TSS は標本 120)。主にしない")])
    return res


def build(root=ROOT, inputs=None):
    u"""記録(OrderedDict)を組む。``inputs`` を渡さなければ 5 つの記録を sha256 で確かめて読む(試験が小さい入力で試すときだけ渡す)。"""
    inputs = inputs if inputs is not None else load_inputs(root)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"AT ― 便をまたいだ集計(既に在る型の読みの記録だけ。取得 0・0 USD)"
    rec[u"この script の sha256"] = sha256_file(os.path.join(root, SCRIPT_REL))
    rec[u"入力"] = [od([(u"#", no), (u"便", batch), (u"記録", rel), (u"sha256", want)]) for no, batch, rel, want in INPUTS]
    rec[u"写しの表"] = [list(row) for row in TABLE]
    rec[u"1 株あたりについて"] = u"写す先の型が表に無い。この属性の数は作りで 0。測った 0 ではない"
    rec[u"便ごとの数"] = tally(inputs)
    rec[u"限界"] = list(LIMITS)
    rec[u"注"] = u"近い行の記録の型の集計(A)・(B)は行から数え直せないので確かめていない。記録は行・文・値・本の番号を持たず、数だけ"
    return rec


def dumps(rec):
    return json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.write and a.check:
        raise Stop(u"**--write と --check は同時に使わない。止める**")
    out = os.path.join(a.root, OUT_REL)
    text = dumps(build(a.root))
    if a.write:
        if os.path.exists(out):
            raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        tmp = out + ".tmp"
        with io.open(tmp, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        os.replace(tmp, out)
        print(u"-> %s" % os.path.basename(out))
        return
    if not os.path.isfile(out):
        raise Stop(u"**記録が無い。止める**")
    with io.open(out, encoding="utf-8", newline="") as fh:
        have = fh.read()
    if have != text:
        raise Stop(u"**在る記録が組み直した内容と違う。止める**")
    print(u"OK: 在る記録は組み直した内容と byte で同じ")


if __name__ == "__main__":
    main()
