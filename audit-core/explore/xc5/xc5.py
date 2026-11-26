# -*- coding: utf-8 -*-
u"""便 XC5: 道具の出力の文から読んだ 4 つの原因を、今年の答えを見ずに直し、組んだ包みの鳴る符号がどう変わるかを見る。

F1 字の形: 文の fact は、範囲の中のタグが閉じている(開きと閉じが対になる)時だけ置く(xmlSchema:syntax の原因)。
F2 roleRef の版: 頭の部の roleRef の href の中のタクソノミの版の日付を、今年の提出者の xsd(持ち込み)が import する同じ名の版にそろえる
   (xbrl.3.5.2.4.5:roleRefMismatch の原因)。
F3 使う文脈だけ: 頭の部の文脈は、置いた fact と隠しの fact が使う物だけにする(EC5700W の原因)。
F6 表紙の項目: 始まりの印で置けなかった文の fact を、前の年の見出しの字(始まりより前の最後の見える字。同じ見出しが前の年と同じ数だけ在れば同じ何番目)と、その後と終わりの後のタグの並びで置く。
F7 提出日: 頭の部の提出日の文脈の日付を、今年の素の本文の表紙の【提出日】の字から入れる。
F5 無い要素: 提出者の独自の要素(名の前置きが提出者の xsd の物)は、今年の提出者の xsd(持ち込み)に定義が在る物だけ置く
   (ix10.11.1.2:missingReferences の原因)。
土台は便 XC4。便 XC0〜XC4 の file は読み込んで関数を呼ぶだけ。今年の答え(表 F・表 H)は採点でだけ読む。
"""
import collections
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_xc5_xc4", os.path.join(os.path.dirname(HERE), "xc4", "xc4.py"))
C4 = importlib.util.module_from_spec(spec)
sys.modules["_xc5_xc4"] = C4
spec.loader.exec_module(C4)
C3, C2, C1, C0, B, V = C4.C3, C4.C2, C4.C1, C4.C0, C4.B, C4.V
od = collections.OrderedDict
FIXES = ("F1", "F2", "F3", "F5", "F6", "F7")
TAG_TOK_RE = re.compile(r"<(/?)([A-Za-z][\w:.\-]*)\b[^>]*?(/?)>")
VOID = set("br img hr meta input col area base link param source wbr".split())
IMPORT_RE = re.compile(r'schemaLocation="(https?://disclosure\.edinet-fsa\.go\.jp/taxonomy/([A-Za-z_]+)/(\d{4}-\d{2}-\d{2})/[^"]+)"')
TAXO_RE = re.compile(r"(/taxonomy/([A-Za-z_]+)/)(\d{4}-\d{2}-\d{2})(/[^#\"]*?)(\d{4}-\d{2}-\d{2})")
ELEM_RE = re.compile(r'<(?:xsd:|xs:)?element\b[^>]*\bname="([^"]+)"')
TNS_RE = re.compile(r'targetNamespace="([^"]+)"')


def balanced(frag):
    u"""字の切れ端の中のタグが閉じているか(void の要素と自己閉じは数えない)。"""
    st = []
    for m in TAG_TOK_RE.finditer(frag):
        closing, name, selfc = m.group(1) == "/", m.group(2).lower(), m.group(3) == "/"
        if selfc or name in VOID:
            continue
        if closing:
            if not st or st[-1] != name:
                return False
            st.pop()
        else:
            st.append(name)
    return not st


def xsd_info(entries):
    u"""今年の提出者の xsd(持ち込み)→ (タクソノミの名 → 版の日付, 独自の要素の名の集まり)。"""
    names = [(i, d) for i, d in entries if i.filename.startswith(B.PUBLICDOC) and i.filename.endswith(".xsd")]
    text = names[0][1].decode("utf-8", "replace")
    vers = dict((m.group(2), m.group(3)) for m in IMPORT_RE.finditer(text))
    return vers, set(ELEM_RE.findall(text))


def fix_role_href(href, vers):
    def rep(m):
        v = vers.get(m.group(2))
        if not v:
            return m.group(0)
        return m.group(1) + v + m.group(4) + v
    return TAXO_RE.sub(rep, href)


def is_extension(name):
    u"""要素の名の前置きが標準(jp…_cor・jpdei_cor など)でなく提出者の物か。"""
    pre = (name or u"").split(":")[0]
    return not (pre.endswith("_cor") or pre.startswith("jpdei"))


TEXT_SEG_RE = re.compile(r">([^<]*)<")


def label_sig(plain, s, t):
    u"""前の年の文の fact の (start, end) → (見出しの字, 見出しの後から始まりまでの字, 終わりから次の見える字までの字) か None。
    見出しの字は、始まりより前の最後の空白でない字の並び(タグとタグの間)。間の字と後の字はタグと空白だけの時に限る。"""
    head = plain[max(0, s - 3000):s]
    segs = [(m.start(1), m.group(1)) for m in TEXT_SEG_RE.finditer(head) if m.group(1).strip()]
    if not segs:
        return None
    off, lab = segs[-1]
    lab_end = max(0, s - 3000) + off + len(lab)
    mid = plain[lab_end:s]
    if TAG_ONLY_RE.sub(u"", mid).strip():
        return None
    m = re.match(r"(?:\s|<[^>]*>)+", plain[t:t + 3000])
    tail = m.group(0) if m else u""
    if not tail:
        return None
    occ = C4.finds(plain, lab)
    nth = occ.index(lab_end - len(lab)) if (lab_end - len(lab)) in occ else -1
    return lab, mid, tail, nth, len(occ)


TAG_ONLY_RE = re.compile(r"<[^>]*>")


def place_texts6(plain, sigs, rels, labels):
    u"""F6: 便 XC4 の置き方で置けなかった文の fact を、見出しの字(1 か所だけ)の後の、前の年と同じタグの並びの後から、
    前の年と同じ閉じのタグの並びが最初に在る所までで置く(表紙の項目のように、中身の字が年ごとに替わる形)。軸のメンバーの在る文脈は置かない。"""
    put, _miss = C4.place_texts(plain, sigs, rels)
    got = set((a.get("name"), a.get("contextRef")) for _s, _e, a in put)
    for (_a, _b, _m, _eb, attrs), lab in zip(sigs, labels):
        if lab is None or (attrs.get("name"), attrs.get("contextRef")) in got or "_" in attrs.get("contextRef", ""):
            continue
        label, mid, tail, nth, total = lab
        cand = C4.finds(plain, label)
        if len(cand) == 1:
            s = cand[0] + len(label)
        elif len(cand) == total and 0 <= nth < total:          # 同じ見出しが前の年と同じ数だけ在れば、同じ何番目
            s = cand[nth] + len(label)
        else:
            continue
        if not plain.startswith(mid, s):
            continue
        s += len(mid)
        t = plain.find(tail, s)
        if t <= s:
            continue
        put.append((s, t, attrs))
    return put, 0


def label_sigs(prior_files):
    u"""前の年 → {file の頭の番号: [見出しの印か None]}(text_sigs と同じ並び)。"""
    out = collections.defaultdict(list)
    for name, plain, F, _H in prior_files:
        for e in F:
            if e["kind"] != "nonNumeric" or e["self"]:
                continue
            out[C4.code_of(name)].append(label_sig(plain, e["start"], e["end"]))
    return out


FILING_RE = re.compile(u"【提出日】")


def filing_date(plain):
    u"""F7: 表紙の【提出日】の後の最初の年月日(西暦か令和・平成)→ YYYY-MM-DD か None(今年の素の本文から)。"""
    import unicodedata
    m = FILING_RE.search(plain)
    if not m:
        return None
    seg = unicodedata.normalize("NFKC", C3.C0.TAG_RE.sub(u"", plain[m.end():m.end() + 2000]))[:200]
    d = C1.DATE_RE.search(seg)
    if not d:
        return None
    dt = C1.to_date(d)
    return dt.isoformat() if dt else None


def built_texts5(cur, prv, entries, fixes):
    u"""便 XC4 の ``built_texts`` を、F1〜F5 を当てて作り直す(同じ手順を、ここで並べ直す)。"""
    vers, own = xsd_info(entries)
    prior = C2.build_prior(prv, C3.RULES)
    prior_H = next((H for _n, _p, _F, H in prv if H is not None), None)
    res = C0.shift_resources(prior_H)
    sigs, rels = C4.text_sigs(prv), C4.text_sigs_rel(prv)
    labs = label_sigs(prv) if "F6" in fixes else {}
    stat = collections.Counter()
    built, used_ctx = [], set()
    for idx, (name, plain, _F, _H) in enumerate(cur):
        nums, _s, _k, _m = C2.place3(plain, prior, res, C3.RULES)
        if "F6" in fixes:
            tx, miss = place_texts6(plain, sigs.get(C4.code_of(name), []), rels.get(C4.code_of(name)), labs.get(C4.code_of(name), []))
        else:
            tx, miss = C4.place_texts(plain, sigs.get(C4.code_of(name), []), rels.get(C4.code_of(name)))
        if "F1" in fixes:
            keep = [x for x in tx if balanced(plain[x[0]:x[1]])]
            stat["F1 で置かなかった文の fact"] += len(tx) - len(keep)
            tx = keep
        if "F5" in fixes:
            n0, t0 = len(nums), len(tx)
            ok = lambda a: not is_extension(a.get("name")) or a.get("name", u"").split(":")[-1] in own
            nums = [x for x in nums if ok(x[2])]
            tx = [x for x in tx if ok(x[2])]
            stat["F5 で置かなかった数の fact"] += n0 - len(nums)
            stat["F5 で置かなかった文の fact"] += t0 - len(tx)
        F2_, dropped = C4.nest(nums, tx)
        stat["文の fact: 置いた"] += sum(1 for f in F2_ if f["kind"] == "nonNumeric")
        stat["数の fact: 置いた"] += sum(1 for f in F2_ if f["kind"] == "nonFraction")
        used_ctx.update(f["attrs"].get("contextRef") for f in F2_)
        built.append((name, plain, F2_))
    texts, placed_text = {}, {}
    for idx, (name, plain, F2_) in enumerate(built):
        placed_text[name] = [(f["start"], f["end"], dict(f["attrs"])) for f in F2_ if f["kind"] == "nonNumeric"]
        H2 = None
        if idx == 0:
            m = C3.BODY_RE.search(plain)
            b = m.end()
            plain = plain[:b] + C3.WRAP_OPEN + C3.WRAP_CLOSE + plain[b:]
            sh = len(C3.WRAP_OPEN) + len(C3.WRAP_CLOSE)
            for f in F2_:
                if f["start"] >= b:
                    f["start"] += sh
                    f["end"] += sh
            H2 = C3.header_from_prior(prior_H, C3.xsd_of_cur[0])
            if "F3" in fixes:
                keep = used_ctx | set(h["attrs"].get("contextRef") for h in H2["hidden"])
                n0 = len(H2["resources"])
                H2["resources"] = [r for r in H2["resources"] if r["type"] != "context" or r["id"] in keep]
                stat["F3 で除いた文脈"] += n0 - len(H2["resources"])
            if "F2" in fixes:
                for r in H2["resources"]:
                    if r["type"] == "ref" and "xlink:href" in r["attrs"]:
                        new = fix_role_href(r["attrs"]["xlink:href"], vers)
                        stat["F2 で直した roleRef"] += int(new != r["attrs"]["xlink:href"])
                        r["attrs"]["xlink:href"] = new
            if "F7" in fixes:
                fd = filing_date(cur[0][1])
                if fd:
                    for r in H2["resources"]:
                        if r["type"] == "context" and r["id"].startswith("FilingDateInstant"):
                            r["period"] = [("xbrli:instant", fd)]
                            stat["F7 で提出日を本文から入れた文脈"] += 1
            H2["pos"] = b + len(C3.WRAP_OPEN)
            H2["before"] = sum(1 for f in F2_ if f["start"] < b)
        texts[name] = B.build_text(plain, F2_, H2)
    return texts, stat, placed_text


def score_pair(cur_zip, prior_zip, workdir, fixes):
    entries = B.load_package(cur_zip)
    cur = B.build_files(entries)
    prv = B.build_files(B.load_package(prior_zip))
    C3.xsd_of_cur[0] = C3.filer_xsd(entries)
    texts, stat, placed_text = built_texts5(cur, prv, entries, fixes)
    acc = od(sorted(stat.items()))
    acc.update(("位置: " + k, v) for k, v in sorted(C4.score_text_positions(cur, placed_text).items()))
    ours = os.path.join(workdir, "ours.zip")
    orig = os.path.join(workdir, "orig.zip")
    B.write_package(B.package_with(entries, texts), ours)
    B.write_package(entries, orig)
    c_o, rows_o, _t = B.run_tool(C3.TOOL, orig, workdir, "orig")
    c_m, rows_m, _t2 = B.run_tool(C3.TOOL, ours, workdir, "ours")
    num_o, non_o = C3.facts_of(rows_o)
    num_m, non_m = C3.facts_of(rows_m)
    acc["道具が読んだ: 元の数の fact"] = sum(num_o.values())
    acc["道具が読んだ: 組んだ数の fact"] = sum(num_m.values())
    acc["数の fact: 元と同じ行"] = sum((num_o & num_m).values())
    co, cm = c_o[u"符号ごとの行"], c_m[u"符号ごとの行"]
    acc["組んだ側だけで鳴った符号"] = od(sorted((k, v) for k, v in cm.items() if k not in co))
    acc["組んだ側だけで鳴った E の符号の数"] = sum(1 for k in acc["組んだ側だけで鳴った符号"] if V.is_e_code(k))
    acc["道具の類: 元・組んだ"] = [c_o[u"類"], c_m[u"類"]]
    return acc


if __name__ == "__main__":
    which, fixes = sys.argv[1], tuple(f for f in sys.argv[2].split(",") if f and f != "none")
    dev, held = C1.split()
    group = {"train": [x for x in dev if x[0] <= C1.SEEN_MAX_NO], "dev": dev, "held": held}[which]
    out = []
    for n, p, pp in group:
        wd = tempfile.mkdtemp(prefix="xc5_")
        try:
            a = score_pair(p, pp, wd, fixes)
        finally:
            shutil.rmtree(wd, ignore_errors=True)
        out.append(od([("番号", n)] + list(a.items())))
        print(n, json.dumps(od((k, v) for k, v in a.items() if not isinstance(v, (dict, list))), ensure_ascii=False), flush=True)
    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
