# -*- coding: utf-8 -*-
u"""止まった数字の「見る順」の診断(2026-11-12)。**engine を呼ばない。既に在る記録だけを読んで数える。**

文書 ``docs/XBRL_STOP_TRIAGE_DIAG_2026-11-12.md``。封は無い(あと知恵の診断)。組の決め方は FX の全体の数を見たあとに決めた。
割った数(形・書き手・会社)と別の 2 組(F1〜F4・F5)は、数える前に予測を書いた(文書 §2)。

読む記録(札は盲検の AI の席 1 席目。人は付けていない):

- FX  = ``fixtures/xbrl/aiforms/fx_claims_2026-11-09.json`` × ``fx_labels_2026-11-09.json``(160 本・profile P33E)
- F14 = ``fixtures/xbrl/aiforms/claims_2026-11-03.json`` × ``labels_2026-11-03.json``(160 本・profile P28E)
- F5  = ``fixtures/xbrl/aiforms/f5_claims_2026-11-03.json`` × ``f5_labels_2026-11-03.json``(40 本・profile P28E)

組(state・reason・last_branch_evidence から決定論で引く。判定は足さず変えない):

- 赤 = VALUE_MISMATCH(last_branch_evidence が ``same_element:Prior`` で始まらない)+ POINTER_NOT_FOUND の ``no_element``・``no_same_value``
- 黄 = VALUE_MISMATCH で last_branch_evidence が ``same_element:Prior`` で始まる
- 灰 = 止まった残り
- 緑 = GROUNDED

    python3 measure/xbrl_stop_triage_2026-11-12.py            # 数えて記録と比べる(違えば rc=1)
    python3 measure/xbrl_stop_triage_2026-11-12.py --write    # 記録を書く
    python3 measure/xbrl_stop_triage_2026-11-12.py --doc      # 文書に貼る表を出す
"""
import collections
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AIF = os.path.join(ROOT, "fixtures", "xbrl", "aiforms")
OUT = os.path.join(AIF, "stop_triage_2026-11-12.json")

SETS = (
    ("FX", "fx_claims_2026-11-09.json", "fx_labels_2026-11-09.json", "P33E"),
    ("F14", "claims_2026-11-03.json", "labels_2026-11-03.json", "P28E"),
    ("F5", "f5_claims_2026-11-03.json", "f5_labels_2026-11-03.json", "P28E"),
)
TIERS = (u"赤", u"黄", u"灰", u"緑")
TAGS = (u"真", u"偽", u"判定不能")
RED_PNF_REASONS = ("no_element", "no_same_value")
PRIOR_EVIDENCE = "same_element:Prior"
# adapters/xbrl/report_customer.py の節の表と同じ字(門が同じであることを見る)
OUT_OF_SCOPE_REASONS = ("no_element(unit not in XBRL)", "no_prior_member_context")
NOT_JUDGED_REASONS = ("no_subject", "target_or_plan", "ambiguous(member)")
SECTIONS = (u"違う", u"要確認", u"対象外", u"判断しない", u"一致")


def _sha(path):
    with io.open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _load(name):
    with io.open(os.path.join(AIF, name), encoding="utf-8") as fh:
        return json.load(fh)


def tier_of(state, reason, evidence):
    if state == "GROUNDED":
        return u"緑"
    if state == "VALUE_MISMATCH":
        return u"黄" if (evidence or "").startswith(PRIOR_EVIDENCE) else u"赤"
    if state == "POINTER_NOT_FOUND" and reason in RED_PNF_REASONS:
        return u"赤"
    return u"灰"


def section_of(state, reason):
    if state == "VALUE_MISMATCH":
        return u"違う"
    if state == "GROUNDED":
        return u"一致"
    if reason in OUT_OF_SCOPE_REASONS:
        return u"対象外"
    if reason in NOT_JUDGED_REASONS:
        return u"判断しない"
    return u"要確認"


def rows_of(claims_name, labels_name, profile):
    u"""1 行 = (会社の鍵, 形, 書き手, 組, 節, 札, state, reason)。札の無い行は札 None。その profile に数の claim が無い行は数えない。"""
    c = _load(claims_name)
    lab = dict((b["name"], dict((r[0], r[1]) for r in b[u"札"])) for b in _load(labels_name)[u"本"])
    first = len(c[u"欄"]["claim"])
    pidx = c["profile"].index(profile)
    out = []
    for b in c[u"本"]:
        tags = lab.get(b["name"], {})
        for r in b[u"行"]:
            cur = None
            for x in r[first:first + pidx + 1]:
                if x != "=":
                    cur = x
            if cur is None:
                continue
            state, reason, evidence = cur[0], cur[1] or "", cur[6]
            out.append((b["docID"], b["form"], b["writer"], tier_of(state, reason, evidence),
                        section_of(state, reason), tags.get(r[0]), state, reason))
    return out


def table(rows, key):
    u"""札のある行だけ。key(行) ごとに 札 3 値の行数。"""
    t = collections.OrderedDict()
    for r in rows:
        if r[5] is None:
            continue
        k = key(r)
        t.setdefault(k, collections.OrderedDict((g, 0) for g in TAGS))
        t[k][r[5]] += 1
    return t


def tier_table(rows):
    t = table(rows, lambda r: r[3])
    out = collections.OrderedDict()
    for k in TIERS:
        d = t.get(k) or collections.OrderedDict((g, 0) for g in TAGS)
        out[k] = collections.OrderedDict(d)
    return out


def summary(rows):
    tt = tier_table(rows)
    n = sum(sum(v.values()) for v in tt.values())
    f = sum(v[u"偽"] for v in tt.values())
    return collections.OrderedDict((
        (u"札のある行", n), (u"札の無い行", sum(1 for r in rows if r[5] is None)), (u"偽", f), (u"組", tt)))


def three(s):
    u"""予測の 3 条件: 赤の偽率 ≥ 全体の偽率 × 3 / 赤が偽の 70% 以上 / 灰の偽率 ≤ 全体の偽率。整数の掛け算で比べる(割らない)。"""
    n, f = s[u"札のある行"], s[u"偽"]
    red, grey = s[u"組"][u"赤"], s[u"組"][u"灰"]
    rk, rf = sum(red.values()), red[u"偽"]
    gk, gf = sum(grey.values()), grey[u"偽"]
    return collections.OrderedDict((
        (u"赤の偽率が全体の 3 倍以上", rf * n >= 3 * f * rk and rk > 0),
        (u"赤が偽の 70% 以上", rf * 100 >= 70 * f and f > 0),
        (u"灰の偽率が全体以下", gf * n <= f * gk),
    ))


def build():
    rec = collections.OrderedDict()
    rec["step"] = u"止まった数字の「見る順」の診断(engine を呼ばない。既に在る記録の数え直し。0 USD)"
    rec[u"種類"] = u"あと知恵の診断(封なし)。組の決め方は FX の全体の数を見たあとに決めた"
    rec[u"札"] = u"盲検の AI の席 1 席目(人は付けていない)"
    rec[u"入力"] = collections.OrderedDict()
    rec[u"組の決め方"] = collections.OrderedDict((
        (u"赤", u"VALUE_MISMATCH(last_branch_evidence が same_element:Prior で始まらない)+ POINTER_NOT_FOUND の no_element・no_same_value"),
        (u"黄", u"VALUE_MISMATCH で last_branch_evidence が same_element:Prior で始まる"),
        (u"灰", u"止まった残り"),
        (u"緑", u"GROUNDED"),
    ))
    data = {}
    for sid, cn, ln, prof in SETS:
        rec[u"入力"][cn] = _sha(os.path.join(AIF, cn))
        rec[u"入力"][ln] = _sha(os.path.join(AIF, ln))
        data[sid] = rows_of(cn, ln, prof)
    sets = collections.OrderedDict()
    for sid, cn, ln, prof in SETS:
        rows = data[sid]
        d = collections.OrderedDict()
        d["profile"] = prof
        d[u"本"] = len(_load(cn)[u"本"])
        d[u"全体"] = summary(rows)
        d[u"形ごと"] = collections.OrderedDict(
            (f, summary([r for r in rows if r[1] == f])) for f in sorted(set(r[1] for r in rows)))
        d[u"書き手ごと"] = collections.OrderedDict(
            (w, summary([r for r in rows if r[2] == w])) for w in sorted(set(r[2] for r in rows)))
        sec = table(rows, lambda r: r[4])
        d[u"報告の節ごと"] = collections.OrderedDict((s, sec.get(s) or collections.OrderedDict((g, 0) for g in TAGS)) for s in SECTIONS)
        chk = table([r for r in rows if r[4] == u"要確認"], lambda r: r[6] + " / " + r[7])
        d[u"要確認の理由ごと"] = collections.OrderedDict(sorted(chk.items()))
        sets[sid] = d
    rec[u"組"] = sets
    # 会社ごと(FX だけ。会社の名・書類の番号は書かない。番号は鍵の並び順)
    fx = data["FX"]
    comp = []
    for i, k in enumerate(sorted(set(r[0] for r in fx))):
        s = summary([r for r in fx if r[0] == k])
        comp.append((k, collections.OrderedDict(((u"番号", i + 1), (u"札のある行", s[u"札のある行"]), (u"偽", s[u"偽"]),
                                                  (u"赤の行", sum(s[u"組"][u"赤"].values())), (u"赤の偽", s[u"組"][u"赤"][u"偽"])))))
    rec[u"FX の会社ごと"] = [c[1] for c in comp]
    top = max(comp, key=lambda c: (c[1][u"偽"], c[0]))
    rec[u"FX で偽が最も多い会社を除いた全体"] = collections.OrderedDict((
        (u"除いた会社の番号", top[1][u"番号"]), (u"数", summary([r for r in fx if r[0] != top[0]]))))
    # 予測(文書 §2)の当たり外れ
    p = collections.OrderedDict()
    fxs = sets["FX"]
    forms = fxs[u"形ごと"]
    p["P1"] = collections.OrderedDict((f, three(s)[u"赤の偽率が全体の 3 倍以上"]) for f, s in forms.items())
    p["P2"] = collections.OrderedDict((f, three(s)[u"赤が偽の 70% 以上"]) for f, s in forms.items())
    p["P3"] = collections.OrderedDict((f, three(s)[u"灰の偽率が全体以下"]) for f, s in forms.items())
    p["P4"] = collections.OrderedDict((w, s[u"組"][u"黄"][u"偽"] <= 1) for w, s in fxs[u"書き手ごと"].items())
    p["P5"] = three(sets["F14"][u"全体"])
    p["P6"] = three(sets["F5"][u"全体"])
    p7 = collections.OrderedDict()
    for c in rec[u"FX の会社ごと"]:
        if c[u"偽"] >= 5:
            p7[str(c[u"番号"])] = c[u"赤の偽"] * c[u"札のある行"] > c[u"偽"] * c[u"赤の行"] and c[u"赤の行"] > 0
    p["P7"] = p7
    rec[u"予測の当たり"] = p
    rec[u"予測に無かった割り方(書き手ごと)の 3 条件"] = collections.OrderedDict((w, three(s)) for w, s in fxs[u"書き手ごと"].items())
    rec[u"予測に無かった割り方(F1〜F4 の形ごと)の 3 条件"] = collections.OrderedDict((f, three(s)) for f, s in sets["F14"][u"形ごと"].items())
    rec[u"限界"] = [
        u"札は AI の席が付けた。人は確かめていない",
        u"文の書き手は Claude の 2 model だけ",
        u"組の決め方は FX の全体の数を見たあとに決めた(FX の全体の数は当てはめの結果で、検証ではない)",
        u"F1〜F4・F5 は profile P28E の判定で、札の無い行がある(数の読み取りの直しより後に増えた行)",
        u"客の実物の文では測っていない",
    ]
    return rec


def _pct(a, b):
    return u"%.1f%%" % (100.0 * a / b) if b else u"―"


def _line(name, s):
    n, f = s[u"札のある行"], s[u"偽"]
    cells = [name, "%d" % n, "%d" % f, _pct(f, n)]
    for k in TIERS:
        v = s[u"組"][k]
        rk = sum(v.values())
        cells.append(u"%d 行(%s)・偽 %d(偽率 %s・取り分 %s)" % (rk, _pct(rk, n), v[u"偽"], _pct(v[u"偽"], rk), _pct(v[u"偽"], f)))
    return u"| " + u" | ".join(cells) + u" |"


def _hit(d):
    return u"%d / %d" % (sum(1 for v in d.values() if v), len(d))


def render(rec):
    u"""文書に貼る塊(記録から機械で作る。門が文書の塊と byte で比べる)。"""
    L = []
    S = rec[u"組"]
    names = (("FX", u"FX(形 F6〜F9・P33E)"), ("F14", u"F1〜F4(P28E)"), ("F5", u"F5(P28E)"))
    L.append(u"**表 1 組ごとの行数と偽の数(札のある行だけ。取り分 = その組の偽 ÷ 偽の全部)**")
    L.append(u"")
    L.append(u"| 範囲 | 札のある行 | 偽 | 全体の偽率 | 赤 | 黄 | 灰 | 緑 |")
    L.append(u"|---|---|---|---|---|---|---|---|")
    for sid, nm in names:
        L.append(_line(nm + u" 全体・%d 本" % S[sid][u"本"], S[sid][u"全体"]))
        for f, s in S[sid][u"形ごと"].items():
            if len(S[sid][u"形ごと"]) > 1:
                L.append(_line(nm.split(u"(")[0] + u" の形 " + f, s))
        if sid == "FX":
            for w, s in S[sid][u"書き手ごと"].items():
                L.append(_line(u"FX の書き手 " + w, s))
            ex = rec[u"FX で偽が最も多い会社を除いた全体"]
            L.append(_line(u"FX 偽が最も多い会社(%d 番)を除く" % ex[u"除いた会社の番号"], ex[u"数"]))
    L.append(u"")
    L.append(u"**表 2 いまの報告の節ごと(札のある行だけ)**")
    L.append(u"")
    L.append(u"| 範囲 | " + u" | ".join(SECTIONS) + u" |")
    L.append(u"|---|" + u"---|" * len(SECTIONS))
    for sid, nm in names:
        cells = []
        for s in SECTIONS:
            v = S[sid][u"報告の節ごと"][s]
            k = sum(v.values())
            cells.append(u"%d 行・偽 %d(%s)" % (k, v[u"偽"], _pct(v[u"偽"], k)))
        L.append(u"| " + nm + u" | " + u" | ".join(cells) + u" |")
    L.append(u"")
    L.append(u"**表 3 「要確認」の節の中の理由ごと(FX。札のある行だけ)**")
    L.append(u"")
    L.append(u"| state / reason | 行 | 偽 | 偽率 | 組 |")
    L.append(u"|---|---|---|---|---|")
    for k, v in S["FX"][u"要確認の理由ごと"].items():
        st, rs = k.split(" / ", 1)
        n = sum(v.values())
        L.append(u"| `%s` | %d | %d | %s | %s |" % (k, n, v[u"偽"], _pct(v[u"偽"], n), tier_of(st, rs, None)))
    L.append(u"")
    L.append(u"**表 4 FX の会社ごと(偽が 5 以上の会社。番号は記録の鍵の並び順で、名は書かない)**")
    L.append(u"")
    L.append(u"| 番号 | 札のある行 | 偽 | 赤の行 | 赤の偽 | 赤の偽率 > その会社の全体の偽率 |")
    L.append(u"|---|---|---|---|---|---|")
    p7 = rec[u"予測の当たり"]["P7"]
    for c in rec[u"FX の会社ごと"]:
        if str(c[u"番号"]) in p7:
            L.append(u"| %d | %d | %d | %d | %d | %s |" % (c[u"番号"], c[u"札のある行"], c[u"偽"], c[u"赤の行"], c[u"赤の偽"],
                                                       u"はい" if p7[str(c[u"番号"])] else u"いいえ"))
    L.append(u"")
    L.append(u"**表 5 予測の当たり外れ(§2 の予測を記録の数から機械で判定)**")
    L.append(u"")
    L.append(u"| 予測 | 当たった数 / 見た数 | 外れたところ |")
    L.append(u"|---|---|---|")
    P = rec[u"予測の当たり"]
    for k in ("P1", "P2", "P3", "P4", "P5", "P6", "P7"):
        miss = [n for n, v in P[k].items() if not v]
        L.append(u"| %s | %s | %s |" % (k, _hit(P[k]), u"・".join(miss) if miss else u"なし"))
    L.append(u"")
    L.append(u"**表 6 予測に無かった割り方での 3 条件(当たり = はい)**")
    L.append(u"")
    L.append(u"| 範囲 | 赤の偽率が全体の 3 倍以上 | 赤が偽の 70% 以上 | 灰の偽率が全体以下 |")
    L.append(u"|---|---|---|---|")
    for title, key in ((u"FX の書き手 ", u"予測に無かった割り方(書き手ごと)の 3 条件"), (u"F1〜F4 の形 ", u"予測に無かった割り方(F1〜F4 の形ごと)の 3 条件")):
        for n, d in rec[key].items():
            L.append(u"| %s%s | %s |" % (title, n, u" | ".join(u"はい" if v else u"いいえ" for v in d.values())))
    return u"\n".join(L) + u"\n"


def dumps(rec):
    return json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"


def main(argv):
    rec = build()
    if "--doc" in argv:
        sys.stdout.buffer.write(render(rec).encode("utf-8"))
        return 0
    text = dumps(rec)
    if "--write" in argv:
        with io.open(OUT, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote", os.path.relpath(OUT, ROOT))
        return 0
    with io.open(OUT, encoding="utf-8") as fh:
        same = fh.read() == text
    print("record matches" if same else "RECORD DIFFERS")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
