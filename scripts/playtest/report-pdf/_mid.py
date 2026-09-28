
# ===================== 第 5 版: 盤面図・短縮・言い換え =====================
PROSE = json.load(open(os.path.join(_data_dir, "prose.json"), encoding="utf-8"))
def fill(g, text, ply=None):
    def rep(mo):
        kind, n = mo.group(1), mo.group(2); p = int(n) if n else ply; e = EV.get((g["no"], p))
        if kind == "m": return "<b>" + disp_move(g, p, e["played"]) + "</b>"
        if kind == "b": return disp_move(g, p, e["best"])
        if kind == "o": return disp_move(g, p + 1, REP[(g["no"], p)]["opponentMove"])
    return _re.sub(r"\{([mbo])(\d*)\}", rep, text)
# ---- 言い換えた文の照合: 文に出る数は、その局の事実に無ければ止める ----
def allowed_numbers(g):
    # STEP FILL 作業 Y(H4-1)。固定の 20 を、このお客さんの局数(s["games"])にした(allowed_numbers の照合は変えない)。
    f = F[g["no"]]; A = {g["total"], g["no"], s["games"], 300, len(la), len(wb), len(wins), len(losses), n_la_collapsed, n_la_resigned_ahead}
    # STEP ENDING_CLOCK §3 の (2)。この局の本人の累計消費時間・持ち時間の秒を許す数に足す(`lib/reportData.ts` の
    # `allowedNumbersOf` の双子。片方だけ直すと、判定は変わるのに言い換えの文には秒を書けない)。
    if f.get("used_sec") is not None: A.add(f["used_sec"])
    if f.get("time_limit_sec") is not None: A.add(f["time_limit_sec"])
    for p, sc in f["pts"]: A.add(p); A.add(abs(sc))
    for p, _, _ in f["trans"]: A.add(p)
    for e in m["events"]:
        if e["gameNo"] == g["no"]:
            A.add(e["ply"])
            A |= {abs(v) for v in (e["before"], e["after"]) if v is not None}
            A |= {int(x) for x in _re.findall(r"\d+", e["after5"])}
    for r in c["reps"]:
        if r["gameNo"] == g["no"]: A |= {r["displayPly"], r["escRoot"], r["escEnd"], r["pvEscEnd"]}
    A.add(sum(1 for _, _, to in f["trans"] if to == "ahead")); A.add(sum(1 for _, _, to in f["trans"] if to == "behind"))
    A.add(len(PROSE[str(g["no"])]["scenes"]))
    return A
problems = []
for key, pz in PROSE.items():
    g = next(x for x in m["games"] if x["no"] == int(key)); A = allowed_numbers(g)
    texts = [pz["summary"], pz["takeaway"]] + [s_["text"] for s_ in pz["scenes"]]
    for t in texts:
        plain = _re.sub(r"[０-９][一二三四五六七八九]", "", _re.sub(r"\{[mbo]\d*\}", "", t)).translate(str.maketrans(ZEN, "0123456789"))
        for num in _re.findall(r"\d+", plain):
            if int(num) not in A: problems.append(f"第 {key} 局: 文の数 {num} が事実に無い → {t[:30]}…")
    if g in la and "優勢" not in pz["summary"]: problems.append(f"第 {key} 局: 優勢から負けた局なのに概要に「優勢」が無い")
    for s_ in pz["scenes"]:
        if s_["type"] == "move" and (g["no"], s_["ply"]) not in EV: problems.append(f"第 {key} 局: {s_['ply']} 手目の場面が記録に無い")
# 2026-09-25 の人間の決定で空にした(凍結の例外 14 件目 ― 冊子の禁止語はすべて使ってよい)。下のループは残す。
BANNED = []
for key, pz in PROSE.items():
    for t in [pz["summary"], pz["takeaway"]] + [s_["text"] for s_ in pz["scenes"]]:
        for w in BANNED:
            if w in t: problems.append(f"第 {key} 局: 使わない語「{w}」")
if problems:
    print("\n".join(problems)); sys.exit(1)

featured = [g for g in la] + [g for g in wb if str(g["no"]) in PROSE]
assert all(str(g["no"]) in PROSE for g in featured), "言い換えの無い局がある"
rest = [g for g in m["games"] if g not in featured]
n_time_ahead = sum(1 for g in la if F[g["no"]]["time_loss"])
# STEP FILL 作業 Y(H4-2)。la は 3 つ(持ち時間に到達・優勢のまま投了・崩れた)に分かれる(_head.py の n_la_resigned_ahead)。
# STEP ENDING_CLOCK §4 の 19。n_time_ahead は F[no]["time_loss"](= 語 `切れ負け` と 時計の一致の和)で数える。
# 局をまたぐ数は via が混ざるので、和に対して真である中立の呼び名だけを使う(「持ち時間切れ」は via == "word" の
# 局にしか言えない)。局ごとの題・文は via が分かるので _head.py 側で書き分けている。
assert n_la_collapsed + n_time_ahead + n_la_resigned_ahead == len(la)
person = m["person"]
S_BIG = st("big5", font=FONT_B, fontSize=22, leading=28, spaceAfter=1.5 * mm)
S_L = st("l5", fontSize=11.5, leading=18)
S_LB = st("lb5", font=FONT_B, fontSize=12.5, leading=18, color=INK)

mc = m["overview"]["moveCheck"]
# ===== 1 ページ目 =====
story.append(P(f"対局後診断・途中報告(第 6 版)", S_TAG))
story.append(P(f"{person}の {s['games']} 局を調べました", S_BIG))
story.append(P(f"{len(wins)} 勝 {len(losses)} 敗の {s['games']} 局を、将棋エンジンで 1 手ずつ調べました。分かったことは 3 つです。", S_LEAD))
def big_item(no, head, body):
    t = Table([[P(str(no), S_NUM2), [P(head, S_LB), P(body, S_B2)]]], colWidths=[12 * mm, W - 12 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.6, LINE), ("BACKGROUND", (0, 0), (-1, -1), BG), ("LINEBEFORE", (0, 0), (0, -1), 2.6, ACCENT), ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 3.5 * mm)]))
    return t
# STEP FILL 作業 Y(H4-2)。n_la_resigned_ahead が 0 のとき(第 6 版の 20 局を含む)は元の文と 1 バイトも変わらない
# (空の節を挟むだけ)。0 でないときだけ、承認済みの題の語(盤上・優勢のまま・投了)をそのまま使って件数を足す。
resigned_ahead_clause = f"、{n_la_resigned_ahead} 局は優勢のまま投了しています" if n_la_resigned_ahead > 0 else ""
story.append(big_item(1, f"負けた {len(losses)} 局のうち {len(la)} 局は、途中まで{person}が優勢でした。", f"{n_la_collapsed} 局は優勢になった後に形勢が崩れ、{n_time_ahead} 局は優勢のまま、時計上、持ち時間に到達しています{resigned_ahead_clause}。最初から押されて負けた将棋は {n_never_ahead_loss} 局だけです。"))
story.append(Spacer(1, 2 * mm))
story.append(big_item(2, f"勝った {len(wins)} 局のうち {len(wb)} 局は、一度劣勢になってから勝っています。", f"良くなってから崩れる将棋と、悪くなってから勝つ将棋が、同じ {s['games']} 局の中に両方あります。"))
story.append(Spacer(1, 2 * mm))
story.append(big_item(3, "形勢が動いたのは、ほとんどが中盤と終盤です。", f"形勢がはっきり崩れた場面は {s['games']} 局で {pr['fell']} か所。そのうち序盤は {ph.get('early','—')} か所だけでした。"))
story.append(Spacer(1, 3.5 * mm))
story.append(boxflow([P("まだ分かっていないこと", S_BOXH), P(f"崩れた場面に共通する条件は、まだ見つかっていません。「数手のうちに玉の逃げ場が減る」場面が {len(c['reps'])} か所ありましたが、エンジン同士の進め方でも同じことが起きるため、{person}だけに当てはまることとは言えませんでした。次に、{person}が選んだ手そのものも数えました。「優勢のときに、自分の玉のすぐそばへ駒を動かす手」は {s['games']} 局で {mc['n']} 回あり、そのうち {mc['fell']} 回で直後に形勢が崩れていました。ただ、比較対象の 10 局では同じ種類の手が {mc['otherN']} 回あって、崩れたのは {mc['otherFell']} 回でした。これも、{person}だけに当てはまることとは、まだ言えません。", S_B2)], colors.white))
story.append(Spacer(1, 3.5 * mm))
story.append(P("このレポートの読み方", S_K))
story.append(notebox([
    "グラフは、上に行くほど" + person + "が良く、下に行くほど相手が良いことを表します。真ん中の点線が互角です。",
    "エンジンの評価が +300 以上を「優勢」、−300 以下を「劣勢」、その間を「互角」と呼んでいます(仮の目安です)。",
    "盤面図は、" + person + "の側を下にしています。茶色の実線が実戦の手、青緑の破線が比べるためのエンジンの候補です。",
    "指し手の良し悪しは書いていません。エンジンの候補は「正解」ではなく、比べるための材料として載せています。",
    "「比較対象」は、" + person + "とは別の方の対局 10 局です(お名前は載せていません)。",
]))
story.append(Spacer(1, 3 * mm))
story.append(P(f"次のページから、形勢が大きく動いた {len(featured)} 局を 1 局ずつ見ていきます(負けた {len(la)} 局と、劣勢から勝った {len(featured) - len(la)} 局)。残りの {len(rest)} 局は、その後の一覧にまとめました。", S_BODY))
story.append(PageBreak())

# ===== 局の俯瞰(STEP FILL 作業 Y、H4-1: 見出しは s["games"] を使う) =====
story.append(P(f"{s['games']} 局の形勢の流れ", S_BIG))
story.append(P("上に行くほど" + person + "が良く、下に行くほど相手が良いことを表します。色のついた枠は、次のページから 1 局ずつ見ていく局です。", S_LEAD))
fset = {g["no"] for g in featured}; cells = []
for g in m["games"]:
    lab = P(f"<b>第 {g['no']} 局</b>　{g['side']}・{g['total']} 手　<font color='{'#2d6a8a' if g['result'] == '勝ち' else '#c9473f'}'><b>{g['result']}</b></font>", S_K)
    cells.append([lab, Spark(g["scores"], [], w=(W / 4) - 5 * mm, h=17 * mm), P(F[g["no"]]["title"], st("ovt", fontSize=7.6, leading=10, color=MUTED))])
grid = [cells[i:i + 4] for i in range(0, len(cells), 4)]
ot = Table(grid, colWidths=[W / 4] * 4)
sty = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.4, LINE), ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE), ("TOPPADDING", (0, 0), (-1, -1), 2 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm)]
for i, g in enumerate(m["games"]):
    if g["no"] in fset: sty.append(("BACKGROUND", (i % 4, i // 4), (i % 4, i // 4), BG_RED if g["result"] == "負け" else BG))
ot.setStyle(TableStyle(sty)); story.append(ot); story.append(PageBreak())

# ===== 一局ずつ(大きく動いた局だけ)=====
class SparkWide(Spark):
    def __init__(self, scores, marks, w, h, plies=None, labels=None):
        super().__init__(scores, marks, w=w, h=h); self.ply_list = plies or []; self.labels = labels or {}
    def draw(self):
        cv = self.canv; n = len(self.scores); pad = 2
        xi = lambda i: pad + i * (self.w - 2 * pad) / (n - 1)
        super().draw()
        cv.setFont(FONT, 6.5)
        if self.ply_list and n > 1:
            last = self.ply_list[-1]; step = 10 if last <= 60 else 20 if last <= 130 else 30
            for t in range(step, last, step):
                i = min(range(n), key=lambda j: abs(self.ply_list[j] - t)); x = xi(i)
                cv.setStrokeColor(colors.HexColor("#c3ced5")); cv.setLineWidth(0.4); cv.setDash(1.5, 2); cv.line(x, 0, x, self.h); cv.setDash()
                cv.setFillColor(MUTED); cv.drawCentredString(x, -7, f"{t} 手")
            for i, lab in self.labels.items():  # 場面の番号
                v = self.scores[i] if self.scores[i] is not None else 0
                y = self.h / 2 + (max(-2000, min(2000, v)) / 2000) * (self.h / 2 - pad)
                cv.setFillColor(RED); cv.setFont(FONT, 7.5); cv.drawCentredString(xi(i) + 6, (y - 9) if y > self.h - 14 else (y + 3), lab); cv.setFont(FONT, 6.5)
S_GH = st("gh", font=FONT_B, fontSize=14, leading=18, color=INK)
S_GSUB = st("gsub", fontSize=10, leading=13, color=MUTED)
S_SEC = st("sec", font=FONT_B, fontSize=10.5, leading=14, color=ACCENT, spaceBefore=2.5 * mm, spaceAfter=1 * mm)
S_SC = st("sc5", fontSize=10.8, leading=16.5)
for g in featured:
    no = g["no"]; f = F[no]; pz = PROSE[str(no)]; us = g["side"] == "先手"; k = SF[g["id"]]
    # STEP ENDING_CLOCK §4 の 10(計画の直し、904d317)。ここが g["ending"](= 「投了」)を実際に印字している。
    # (3) の併記: 終局の語は投了・本人が負け・時計は一致しなかった局(resigned_ahead。第 16 局のような形)に、
    # 判定はしない・数だけの観測を添える。
    obs_suffix = (
        f"　｜　本人の累計消費時間は {f['used_sec']} 秒(持ち時間は {f['time_limit_sec']} 秒)"
        if g["result"] == "負け" and f["resigned_ahead"] and f["used_sec"] is not None and f["time_limit_sec"] is not None
        else ""
    )
    head_tbl = Table([[P(f"第 {no} 局　<font size='12'>「{f['title']}」</font>", S_GH)], [P(f"結果: {g['result']}　｜　{g['side']}　｜　{g['total']} 手" + (f"　｜　{g['ending']}" if g.get("ending") else "") + obs_suffix, S_GSUB)]], colWidths=[W])
    head_tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BG), ("LINEBELOW", (0, -1), (-1, -1), 1.0, ACCENT), ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm), ("TOPPADDING", (0, 0), (0, 0), 2 * mm), ("BOTTOMPADDING", (0, -1), (-1, -1), 1.8 * mm)]))
    marks = [min(range(len(g["plies"])), key=lambda i: abs((g["plies"][i] + f["off"]) - s_["ply"])) for s_ in pz["scenes"]]
    story += [head_tbl, Spacer(1, 1.5 * mm), P("どんな将棋だったか", S_SEC), P(fill(g, pz["summary"]), S_SC), P("形勢の変化(赤い点と番号が、下の場面です。縦の点線は手数の目安)", S_SEC), SparkWide(g["scores"], marks, w=W, h=20 * mm, plies=[p + f["off"] for p in g["plies"]], labels={mi: "①②③"[j] for j, mi in enumerate(marks)}), Spacer(1, 4.5 * mm), P("形勢が動いた場面", S_SEC)]
    BSZ = (42 if len(pz["scenes"]) > 1 else 56) * mm
    for s_ in pz["scenes"]:
        ply = min(s_["ply"], len(k["sfens"]) - 1)
        if s_["type"] == "move":
            e = EV[(no, s_["ply"])]; same = e["sameBest"] or not e.get("bestUsi") or e["bestUsi"] == e["playedUsi"]
            arrows = [(e["playedUsi"], COL_PLAYED, False, 0 if same else 1.3)] + ([] if same else [(e["bestUsi"], COL_CAND, True, -1.3)])
            bd = Board(k["sfens"][ply - 1], us, usi=None, person=person, arrows=arrows, size=BSZ)
            cap = f"{disp_move(g, s_['ply'], e['played'])} を指す前の局面"
            cell = [P(cap, S_CARDH), Spacer(1, 1.5 * mm), P(fill(g, s_["text"], s_["ply"]), S_SC), Spacer(1, 2 * mm), Legend(same)]
        else:
            bd = Board(k["sfens"][ply], us, usi=k["moves"][ply - 1], person=person, size=BSZ)
            cell = [P("相手が指した後の局面(赤い升が相手の手)", S_CARDH), Spacer(1, 1.5 * mm), P(fill(g, s_["text"], s_["ply"]), S_SC)]
        sidx = pz["scenes"].index(s_); band = P(f"<font color='#c9473f'><b>場面 {'①②③'[sidx]}</b></font>　{s_['ply']} 手目", S_CARDH)
        row = Table([[band, ""], [bd, cell]], colWidths=[66 * mm, W - 66 * mm])
        row.setStyle(TableStyle([("SPAN", (0, 0), (1, 0)), ("BACKGROUND", (0, 0), (-1, 0), BG), ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#b8c4cb")), ("TOPPADDING", (0, 1), (-1, 1), 2.5 * mm), ("BOTTOMPADDING", (0, 1), (-1, 1), 2 * mm), ("TOPPADDING", (0, 0), (-1, 0), 1.2 * mm), ("BOTTOMPADDING", (0, 0), (-1, 0), 1.2 * mm), ("LEFTPADDING", (0, 0), (0, -1), 3 * mm)]))
        story += [KeepTogether([row]), Spacer(1, 2 * mm)]
    story += [P("この一局から見えたこと", S_SEC), P(fill(g, pz["takeaway"]) + f" この一局だけから、{person}の決まった特徴とは判断しません。", S_SC), PageBreak()]

# ===== 残りの局 =====
story.append(P("そのほかの 10 局", S_BIG) if len(rest) == 10 else P(f"そのほかの {len(rest)} 局", S_BIG))
story.append(P("一局ずつのページに載せなかった局の一覧です。グラフの見方は同じです。", S_LEAD))
rows = [[P(x, S_K) for x in ["局", "先後", "結果", "手数", "どんな将棋だったか", "形勢の変化"]]]
for g in rest:
    rows.append([P(str(g["no"]), S_V), P(g["side"], S_V), P(g["result"], S_V), P(str(g["total"]), S_V), P(F[g["no"]]["title"], S_V), Spark(g["scores"], [], w=50 * mm, h=11 * mm)])
gt = Table(rows, colWidths=[12 * mm, 13 * mm, 13 * mm, 13 * mm, W - 51 * mm - 54 * mm, 54 * mm], repeatRows=1)
gt.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT), ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE), ("BACKGROUND", (0, 0), (-1, 0), BG), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1.2 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2 * mm)]))
story.append(gt)
story.append(PageBreak())

# ===== まとめ =====
story.append(P(f"{s['games']} 局を通して見えたこと", S_BIG))
story.append(P(f"<b>勝ち負けは序盤で決まっておらず、形勢が良くなった後、そして悪くなった後の数手で動いています。</b>", S_LEAD))
story.append(boxes([(len(la), f"負けた {len(losses)} 局のうち、<br/>途中で優勢だった局"), (len(wb), f"勝った {len(wins)} 局のうち、<br/>劣勢になってから勝った局"), (pr["fell"], f"形勢がはっきり崩れた場面<br/>(序盤 {ph.get('early','—')}・中盤 {ph.get('mid','—')}・終盤 {ph.get('late','—')})"), (len(c["reps"]), "そのうち、直前に<br/>玉の逃げ場が減っていた場面")]))
story.append(Spacer(1, 3 * mm))
for items, bgc in ((
    [P("分かったこと", S_BOXH),
     P(f"・負けた {len(losses)} 局のうち {len(la)} 局で、途中に優勢の場面がありました。{n_la_collapsed} 局はその後に崩れ、{n_time_ahead} 局は優勢のまま、時計上、持ち時間に到達しています{resigned_ahead_clause}。", S_B2),
     P(f"・勝った {len(wins)} 局のうち {len(wb)} 局は、一度劣勢になっています。", S_B2),
     P(f"・形勢が崩れた {pr['fell']} か所のうち、優勢から崩れたのは {ph.get('fromAhead','—')} か所。そのうち {ph.get('fromAheadLoss','—')} か所が負けた局のものでした。", S_B2)], BG),
    ([P("まだ言えないこと", S_BOXH),
      P(f"・崩れた場面に共通する条件として「数手のうちに玉の逃げ場が減る」を調べましたが、エンジンの進め方でも同じくらい起き、比較対象の対局では確かめられませんでした。", S_B2),
      P(f"・{person}が選んだ手そのもの(動かした駒、打つ手、玉のそばへの手など)も数えました。「優勢のときに自分の玉のすぐそばへ駒を動かす手」は {mc['n']} 回のうち {mc['fell']} 回で直後に崩れていましたが、比較対象の 10 局では {mc['otherN']} 回のうち {mc['otherFell']} 回でした。どちらも、{person}に特有のこととは、まだ言えません(細かい数は別冊の技術資料にあります)。", S_B2)], colors.white),
    ([P("次に調べること", S_BOXH),
      P(f"・{person}の次の {s['games']} 局で、今回見えたこと(優勢の後の崩れ、玉のそばへの手)がもう一度見えるかを確かめます。同じ人の新しい対局で確かめるのが、いちばん確かな方法です。", S_B2),
      P("・比べる相手の対局を増やします(今回の比較対象は 10 局だけでした)。", S_B2)], colors.white)):
    story.append(boxflow(items, bgc)); story.append(Spacer(1, 2 * mm))

story.append(Spacer(1, 4 * mm))
story.append(P(f"作成 {m['today']} / 将棋エンジン(やねうら王)で 1 手ずつ評価 / 試作版につき、有段者による確認はまだ受けていません。数の内訳と判定の詳細は、別冊「技術資料」にまとめています。", st("foot", fontSize=8, leading=11, color=MUTED)))
doc.build(story)
print("wrote", out)

