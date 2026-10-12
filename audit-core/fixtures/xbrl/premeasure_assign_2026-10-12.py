# -*- coding: utf-8 -*-
"""抽出の封 v2 の下ごしらえ。エンジンは変更せず、文の語だけで「差か・どの期間か」を決める純粋関数を
v1(失敗した封)と v2(この封の規則)の 2 通りで書き、独立判定の正解に当てて数える。
値(fact の値・target)は一切使わない。使い方:
  python3 premeasure_assign_2026-10-12.py <audit-core> <dump_numbers の出力 json> <出力 json>"""
import json, re, sys
HERE, NUMS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, HERE)
from adapters.xbrl import extract as E, vocabulary as V

N = json.load(open(NUMS))
TRUTH = json.load(open(HERE + "/fixtures/xbrl/independent_truth_2026-10-12.json"))
DOCTAG = {"S100Z4Q1": "1B", "S100Z4B6": "5F"}
MONEY = set(V.UNIT_SCALE)

# ---------------------------------------------------------------- 共通の部品
PRIOR_PAREN_RE = re.compile(r"[(（]\s*(前連結会計年度は|前期は|同)")
PRIOR_CUE_RE = re.compile(r"(前期末|前期|前連結会計年度)")

def spans_of(s):
    return [(a, b) for (a, b, _v, _u, _p) in E.iter_numbers(s)]

def inside_prior_paren(s, a):
    o = max(s.rfind("(", 0, a), s.rfind("（", 0, a))
    if o < 0:
        return False
    cl = [x for x in (s.find(")", o), s.find("）", o)) if x >= 0]
    c = min(cl) if cl else len(s)
    return o < a < c and bool(PRIOR_PAREN_RE.match(s, o))

# ---------------------------------------------------------------- 現行(main)
MAIN_AFTER = re.compile(r"(増加|減少|増|減)")
MAIN_BEFORE = re.compile(r"(増加額|減少額|比べて)")
def main_rule(s, a, b):
    return {"diff": bool(MAIN_AFTER.search(s[b:b + 4])) or bool(MAIN_BEFORE.search(s[max(0, a - 25):a])),
            "period": "Current"}

# ---------------------------------------------------------------- v1(失敗した封。再現用)
def v1_period(s, a, sp):
    if inside_prior_paren(s, a):
        return "Prior1"
    idx = next((i for i, (x, _y) in enumerate(sp) if x == a), None)
    base = max(0, a - 15); left = s[base:a]
    prev_end = sp[idx - 1][1] if (idx is not None and idx > 0) else -1
    for m in PRIOR_CUE_RE.finditer(left):
        if prev_end >= base + m.end():
            continue
        return "Prior1"
    if idx is not None and idx > 0:
        between = s[sp[idx - 1][1]:a]
        if "同" in between and not PRIOR_CUE_RE.search(between):
            return v1_period(s, sp[idx - 1][0], sp)
    return "Current"

def v1_rule(s, a, b):
    d = bool(MAIN_AFTER.search(s[b:b + 12])) or bool(MAIN_BEFORE.search(s[max(0, a - 25):a]))
    if d and inside_prior_paren(s, a):
        d = False
    return {"diff": d, "period": v1_period(s, a, spans_of(s))}

# ---------------------------------------------------------------- v2(この封の規則)
FLOW_BEFORE = re.compile(r"(増加額|減少額)$")                                  # 規則 F-flow
DIFFW = r"(?:(?:増加|減少)(?!額)|(?:増益|減益|増収|減収)額?)"                    # 増減語(額つきの 増加額・減少額 は含まない)
BARE = r"[増減](?![一-龥])"                                                    # 数の直後の「増」「減」(減価・減損などの複合語を除く)
F1 = re.compile(r"(?:" + DIFFW + r"|比べて?)$")                                 # 数の直前(隙間 0)
F2 = re.compile(r"^(?:の)?(?:" + DIFFW + r"|" + BARE + r")")                    # 数の直後(隙間 0・「の」1 つまで)
F3 = re.compile(r"^[(（][^()（）%％]*[)）]の?" + DIFFW)                          # 数 + (…)の増減語。括弧の中に % が無いもの
F5 = re.compile(r"^[、,]\s*[0-9.,]+[%％]の?(?:大幅な?)?" + DIFFW)                             # 数、P%の増減語(金額と率が並ぶ形)。「大幅」は N066 を見てから足した(封に開示)
BASELINE_AFTER_CUE = re.compile(r"^末?(?:に|と)?(?:比べ|比して|対し)")           # 「前期に比べ」= 比較の基準であって数の期間ではない
SAME_BEFORE = re.compile(r"[(（]同$|[(（]\s*同$")

def v2_period(s, a, sp):
    if inside_prior_paren(s, a):
        return "Prior1"
    idx = next((i for i, (x, _y) in enumerate(sp) if x == a), None)
    base = max(0, a - 15); left = s[base:a]
    prev_end = sp[idx - 1][1] if (idx is not None and idx > 0) else -1
    for m in PRIOR_CUE_RE.finditer(left):
        ce = base + m.end()
        if prev_end >= ce:                        # A-2: 手がかりと数の間に別の数 → その数のもの
            continue
        if BASELINE_AFTER_CUE.match(s[ce:ce + 6]) or s[ce:ce + 1] == "比":
            continue                              # 比較の基準 / 「前期比」
        return "Prior1"
    return "Current"

def v2_rule(s, a, b):
    sp = spans_of(s)
    period = v2_period(s, a, sp)
    left, right = s[max(0, a - 8):a], s[b:b + 40]
    flow = bool(FLOW_BEFORE.search(left))
    forms = [n for n, ok in (("F1", F1.search(left)), ("F2", F2.match(right)), ("F3", F3.match(right)),
                             ("F5", F5.match(right))) if ok]
    diff = bool(forms) and not flow and not inside_prior_paren(s, a)
    pair = diff and period == "Current"          # 対は 当期−前期 だけ。前期の数は単一(前期−前々期の対は作らない)
    return {"diff": diff, "period": period, "pair": pair, "forms": forms, "flow": flow}

RULES = {"main": main_rule, "v1": v1_rule, "v2": v2_rule}

def get(tag, i):
    r = N[tag][i]; return r["s"], r["ab"][0], r["ab"][1], r["unit"]

def mark(s, a, b, w=14):
    return s[max(0, a - w):a] + "【" + s[a:b] + "】" + s[b:b + w]

# ---------------------------------------------------------------- 正解との突き合わせ
out = {"rules": list(RULES), "rows": {}}
# (1) 1 巡目 57 行: 全部「単一」。期間は正解の context から
for r in TRUTH["決定済み"]:
    tag = DOCTAG[r["docID"]]; s, a, b, unit = get(tag, r["id"])
    if unit not in MONEY:
        continue
    want_period = "Prior1" if r["context"].startswith("Prior1") else "Current"
    out["rows"]["1st:%s:%s" % (tag, r["id"])] = {"want": {"form": "single", "period": want_period}, "text": mark(s, a, b),
        **{k: f(s, a, b) for k, f in RULES.items()}}
# (2) 2 巡目 16 行: 「差(当期−前期)」。% の行は率(区分 C)なので別に数える
for r in TRUTH["2巡目"]["決定済み"]:
    tag = DOCTAG[r["docID"]]; s, a, b, unit = get(tag, r["id"])
    out["rows"]["2nd:%s:%s" % (tag, r["id"])] = {"want": {"form": "pair", "period": "Current"}, "target": r["対象"],
        "money": unit in MONEY, "text": mark(s, a, b),
        **{k: f(s, a, b) for k, f in RULES.items()}}
json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1, sort_keys=True)

def verdict(rule, row):
    w = row["want"]; x = row[rule]
    if rule == "main":                       # main は期間を持たない(値で探す)ので形だけ
        return "ok" if (x["diff"] == (w["form"] == "pair")) else "NG"
    form = "pair" if (x.get("pair", x["diff"] and x["period"] == "Current")) else "single"
    return "ok" if (form == w["form"] and x["period"] == w["period"]) else "NG"

for grp in ("1st", "2nd"):
    print("==", grp)
    for k, row in sorted(out["rows"].items()):
        if not k.startswith(grp):
            continue
        if grp == "2nd" and not row["money"]:
            continue
        vs = {r: verdict(r, row) for r in RULES}
        print("%-12s %s main=%s v1=%s v2=%s  v2=%s  %s" % (k, "対象" if row.get("target") else "    ", vs["main"], vs["v1"], vs["v2"],
              (row["v2"]["period"], row["v2"]["forms"], "flow" if row["v2"]["flow"] else ""), row["text"]))
for r in RULES:
    for grp in ("1st", "2nd"):
        rows = [row for k, row in out["rows"].items() if k.startswith(grp) and (grp == "1st" or row["money"])]
        print("集計 %-4s %s: ok %d / %d" % (r, grp, sum(1 for row in rows if verdict(r, row) == "ok"), len(rows)))

# (3) P7 の 60 行: 監査が確かめた正しい pointer(grounded_binding_check)から 形・期間 を取る。
#     pointer が 1 つの fact なら single、context が "A | B" なら対。期間は先頭の context の接頭辞。
GB = json.load(open(HERE + "/fixtures/xbrl/grounded_binding_check_2026-10-12.json"))
p7 = {}
for r in GB["rows"]:
    i = r["id"]
    if i not in N["P7"]:
        continue                                 # T### は文の主張(数の主張でない)
    s, a, b, unit = get("P7", i)
    want_ctx = r["pointer_fact"]["context"] if r.get("pointer_fact") else None
    want_period = "Prior1" if (want_ctx or "").startswith("Prior1") else "Current"
    want_form = "pair" if " | " in (want_ctx or "") else "single"      # 監査の pointer が 2 fact なら対
    p7[i] = {"judge": r["判定"], "want": {"form": want_form, "period": want_period}, "ctx": want_ctx, "unit": unit,
             "text": mark(s, a, b), **{k: f(s, a, b) for k, f in RULES.items()}}
out["rows_p7"] = p7
json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1, sort_keys=True)
print("== P7-60(判定 correct の行のみ形・期間を採点。wrong_binding は参考表示)")
for rule in RULES:
    ok = ng = 0
    for i, row in sorted(p7.items()):
        if row["judge"] != "correct" or row["unit"] not in MONEY:
            continue
        if verdict(rule, row) == "ok": ok += 1
        else: ng += 1
    print("集計 %-4s P7: ok %d / ng %d" % (rule, ok, ng))
for i, row in sorted(p7.items()):
    odd = row["v2"]["diff"] or row["v2"]["period"] != "Current" or row["want"]["period"] != "Current" or row["judge"] != "correct"
    if odd:
        print("%s %-14s want=%s/%s ctx=%s | v2 diff=%s pair=%s per=%s forms=%s flow=%s | v1 diff=%s per=%s | %s" % (
            i, row["judge"], row["want"]["form"], row["want"]["period"], row["ctx"], row["v2"]["diff"], row["v2"]["pair"], row["v2"]["period"],
            row["v2"]["forms"], row["v2"]["flow"], row["v1"]["diff"], row["v1"]["period"], row["text"]))

# (4) main との差: 全金額の数(1B・5F・P7)で、main の割当(差=is_diff・期間=当期)と v2 が違う行。
import collections
delta = {}; cat = collections.Counter()
for tag in ("1B", "5F", "P7"):
    for i, r in N[tag].items():
        s, a, b, u = r["s"], r["ab"][0], r["ab"][1], r["unit"]
        if u not in MONEY:
            continue
        m, v = main_rule(s, a, b), v2_rule(s, a, b)
        kind = []
        if m["diff"] and not v["pair"]: kind.append("対をやめる")
        if (not m["diff"]) and v["pair"]: kind.append("対にする")
        if v["period"] == "Prior1": kind.append("前期の単一")
        if kind:
            delta["%s:%s" % (tag, i)] = {"main_diff": m["diff"], "v2_pair": v["pair"], "v2_period": v["period"], "forms": v["forms"], "kind": kind, "text": mark(s, a, b)}
            cat[(tag, "+".join(kind))] += 1
out["delta_vs_main"] = delta
json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1, sort_keys=True)
print("== main との差(金額の数)", len(delta))
for k, v in sorted(cat.items()): print(k, v)
bad = [i for i, row in p7.items() if row["judge"] == "correct" and row["unit"] in MONEY and verdict("v2", row) != "ok"]
print("P7 v2 NG(correct 行):", bad)
