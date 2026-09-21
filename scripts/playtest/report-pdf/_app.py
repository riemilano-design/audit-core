# ===== 付録 =====

story.append(P("技術資料: 数の内訳と判定の詳細", S_TITLE))
story.append(P("本編(本人向け)の数がどう出ているかを示す資料です。開発・監査のための項目を含みます。", S_LEAD))
# 2. 候補
story.append(P("付録 1. 崩れた場面に共通する条件の候補と、その判定", S_H2))
story.append(P(f"{s['games']} 局のすべての手の組を、いくつかの事実(取った駒・王手・玉のまわりの味方・玉の逃げ道・玉のまわりに届く利き)で見て、<b>直後に形勢が下がった組に多く現れる条件</b>を探しました。候補として残ったのは次の 1 つです。ただし、下の判定のとおり、<b>現時点では「くり返し現れる条件」と言える根拠は足りていません</b>。", S_BODY))
card_h = Table([[P(f"候補: {c['label']}", S_CARDH)]], colWidths=[W])
card_h.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BG), ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm), ("TOPPADDING", (0, 0), (-1, -1), 1.8 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8 * mm)]))
story.append(card_h)
story.append(kv([
    ["何を見ているか", c["readableText"]],
    ["当てはまった組", f"{c['tTotal']} 組({c['tnGames']} 局)。そのうち、直後の区分の変化を確かめられた {c['tn']} 組の中で、1 段以上下がったのは <b>{c['tc']} 組({c['tPct']}%)</b>"],
    ["当てはまらなかった組", f"{c['fn']} 組の中で、1 段以上下がったのは <b>{c['fc']} 組({c['fPct']}%)</b>"],
    ["直前の区分ごと", f"優勢のとき: 当てはまる組 {c['byBefore']['ahead']['collapsed']} / {c['byBefore']['ahead']['denominator']}、当てはまらない組 {c['fByBefore']['ahead']['collapsed']} / {c['fByBefore']['ahead']['denominator']}。互角のとき: {c['byBefore']['level']['collapsed']} / {c['byBefore']['level']['denominator']}、{c['fByBefore']['level']['collapsed']} / {c['fByBefore']['level']['denominator']}"],
    ["エンジンの読み筋との比べ", f"同じ {c['pv']['n']} 組で、実戦の手順ではこの条件が {c['pv']['actualTrue']} 組で起き、エンジンの読み筋を進めた手順でも {c['pv']['pvTrue']} 組で起きました"],
    ["別の棋譜での確かめ", f"条件を作った {s['games']} 局とは別の {c['test']['games']} 局(別の方の対局)では、当てはまる組 {c['test']['tn']} 組のうち下がったのは {c['test']['tc']} 組、当てはまらない組では {c['test']['fc']} / {c['test']['fn']} 組でした"],
]))
story.append(Spacer(1, 2 * mm))
story.append(P("判定(4 つの物差し。すべて満たしたときだけ「追加検証する価値のある候補」とします)", S_K))
grows = [[P("項目", S_K), P("見ること", S_K), P("今回の値", S_K), P("基準", S_K), P("結果", S_K)]]
for gi in c["gate"]:
    mark = "<font color='#2d6a8a'>○ 満たした</font>" if gi["met"] else f"<font color='#c9473f'>× 満たさず</font><br/><font size='8.5'>{gi['reason']}</font>"
    grows.append([P(gi["id"], S_V), P(gi["name"], S_V), P(gi["value"], S_V), P(gi["threshold"], S_V), P(mark, S_V)])
gtab = Table(grows, colWidths=[12 * mm, 40 * mm, W - 12 * mm - 40 * mm - 40 * mm - 34 * mm, 40 * mm, 34 * mm], repeatRows=1)
gtab.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT), ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINE), ("BACKGROUND", (0, 0), (-1, 0), BG), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.6 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6 * mm)]))
story.append(gtab)
story.append(Spacer(1, 2 * mm))
vt = Table([[P(f"<b>{c['verdict']}</b>", S_BODY)]], colWidths=[W])
vt.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("LINEBEFORE", (0, 0), (0, -1), 2.2, ACCENT), ("LEFTPADDING", (0, 0), (-1, -1), 3.5 * mm), ("TOPPADDING", (0, 0), (-1, -1), 2 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm)]))
story.append(vt)
story.append(Spacer(1, 1.5 * mm))
story.append(P(f"上の一文は、判定の道具が出した文をそのまま載せています。「根拠が不足」は「この条件は関係ない」という意味ではなく、{s['games']} 局と別の {c['test']['games']} 局では差を確かめられなかった、という意味です。", S_SMALL))

# 3. 代表局面
story.append(P(f"付録 2. 候補に当てはまり、直後に形勢が下がった場面({len(c['reps'])} 組すべて)", S_H2))
story.append(P("候補に当てはまった組のうち、直後に形勢の区分が 1 段以上下がった組を全部並べます。指し手は本人が指した向きの表記です。「逃げ道」は玉が動ける先の数(駒を取る手を含む)で、「前 → 後」は自分の手の前と、読み筋と比べられた手数を進めた後の値です。", S_BODY))
rrows = [[P(x, S_K) for x in ["局", "手数", "自分の手 → 相手の手", "評価値(前 → 後)", "区分", "逃げ道(前 → 後)", "読み筋なら", "その間に取られた駒 / 取った駒"]]]
for r in c["reps"]:
    rrows.append([P(f"第 {r['gameNo']} 局<br/><font size='8.5' color='#5a6a74'>{r['side']}・{r['result']}</font>", S_V), P(f"{r['displayPly']}", S_V), P(f"{r['userMove']} → {r['opponentMove']}", S_V), P(f"{fmt(r['before'])} → {fmt(r['after'])}", S_V), P(r["transitionJp"], S_V), P(f"{r['escRoot']} → {r['escEnd']}", S_V), P(f"{r['pvEscEnd']}", S_V), P(f"{r['capOppJp']} / {r['capUsJp']}", S_V)])
rt = Table(rrows, colWidths=[20 * mm, 11 * mm, 34 * mm, 28 * mm, 22 * mm, 22 * mm, 16 * mm, W - 153 * mm], repeatRows=1)
rt.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT), ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINE), ("BACKGROUND", (0, 0), (-1, 0), BG), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.6 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6 * mm)]))
story.append(rt)
story.append(Spacer(1, 1.5 * mm))
story.append(P("「読み筋なら」は、同じ局面からエンジンの読み筋を同じ手数だけ進めたときの逃げ道の数です。実戦と同じく減っている組もあり、「逃げ道が減ること」自体は両者が最善を尽くしても起きる、という比べの材料になります。第 5 局 68 手目・第 6 局 62 手目・70 手目は急落の場面でもあり、実戦と読み筋の続きは「6. 詳細データ」の該当の場面に載せています。", S_SMALL))

# 4. なぜ
story.append(P("付録 3. なぜこの候補が残ったのか、なぜ根拠不足なのか", S_H2))
story.append(notebox([
    f"探し方: {s['games']} 局の手の組すべてについて、自分の手のあと数手で起きた事実(取った駒、王手、玉のまわりの味方の数、玉の逃げ道、両方の玉のまわりに届く利き)を、その手の前と比べました。事実 1 つずつと、2 つの組み合わせを機械的に総当たりし、「当てはまる組の方が下がりやすい」ものを探しました。",
    f"残った理由: 「逃げ道が減る」は、当てはまる組で {c['tPct']}%、当てはまらない組で {c['fPct']}% と差が見え、{s['games']} 局すべてに現れました(G-1 は満たしました)。",
    f"根拠不足の理由 1(G-2): 差はありますが、基準の「2 倍以上かつ 10 ポイント以上」には届きません。",
    f"根拠不足の理由 2(G-3): エンジンの読み筋を同じ手数だけ進めても、{c['pv']['n']} 組中 {c['pv']['pvTrue']} 組で逃げ道が減ります(実戦は {c['pv']['actualTrue']} 組)。つまり、逃げ道が減ること自体は「ふつうの将棋の進み方」でもよく起きることで、本人の手に特有とは言えません。",
    f"根拠不足の理由 3(G-4): 別の方の {c['test']['games']} 局では、当てはまる組 {c['test']['tn']} 組で下がった組は {c['test']['tc']} 組でした。{s['games']} 局で見えた向きが、別の棋譜では確かめられませんでした。",
    f"注意: 総当たりで探した候補なので、{s['games']} 局での差は実際より良く見えている可能性があります。だからこそ、別の棋譜での確かめ(G-4)を判定に入れています。",
]))

# 5. 次
story.append(P(f"付録 4. 次の {s['games']} 局で確かめたいこと", S_H2))
story.append(notebox([
    "同じ条件「逃げ道が減る」で、当てはまる組の下がりやすさが、当てはまらない組の 2 倍以上・10 ポイント以上の差になるか(G-2)。",
    "逃げ道が減る場面で、実戦とエンジンの読み筋の違いがどこにあるか。逃げ道の数そのものより、「どの手で減ったか」(自分の手か、相手の手か)を分けて数える物差しを足すかどうかを、次版までに決めます。",
    "本人の手そのもの(動かした駒の種類、玉のそばから離れたか、持ち駒を打ったか)を事実として数える物差しは、この版ではまだありません。候補が「くり返し」と言えるかは、その物差しを足してから改めて探します。",
    f"この報告は、{s['games']} 局で確かめられたことと、確かめられなかったことを分けて書いています。本人の決まった特徴のような言い切りは、判定が基準を満たすまで書きません。",
]))

# 第 3 版: 全ての手の組(自分の手 → 相手の手)を対照群として見た結果(STEP D4 の gate.ts の出力。条件式 0 本)
pr = m.get("pairs")
if pr:
    story.append(P("付録 5. 手の組ぜんぶを見た結果(対照群)", S_H2))
    fell_pct = (200 * pr["fell"] + pr["den"]) // (2 * pr["den"])
    ah, ahd = pr["fromAhead"]; lv, lvd = pr["fromLevel"]
    ah_pct = (200 * ah + ahd) // (2 * ahd); lv_pct = (200 * lv + lvd) // (2 * lvd)
    story.append(P(f"急落の場面だけでなく、<b>{pr['games']} 局の「自分の手 → 相手の手」の組 {pr['total']} 組すべて</b>について、その直後に形勢の区分(優勢・互角・劣勢)が 1 段以上下がったかを数えました。急落(2 手で 400 以上)とは別の物差しで、下がり幅の大小は問いません。", S_BODY))
    pboxes = [(pr["total"], "手の組の数<br/>(自分の手 → 相手の手)"), (pr["den"], "そのうち、下がりうる組<br/>(直前が優勢か互角で、前後とも区分あり)"), (pr["fell"], f"直後に区分が 1 段以上<br/>下がった組({fell_pct}%)"), (pr["gamesWithFall"], f"下がった組のある局<br/>({pr['games']} 局中)")]
    pcells = [[[P(str(n), S_NUM), P(l, S_LBL)] for n, l in pboxes]]
    pt = Table(pcells, colWidths=[W / 4] * 4)
    pt.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("INNERGRID", (0, 0), (-1, -1), 0.6, LINE), ("BACKGROUND", (0, 0), (-1, -1), BG), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 3.5 * mm)]))
    story.append(pt)
    story.append(Spacer(1, 2.5 * mm))
    prow = [
        ["下がり方の内訳", f"優勢 → 互角 {pr['aheadToLevel']} 組・互角 → 劣勢 {pr['levelToBehind']} 組・優勢 → 劣勢 {pr['aheadToBehind']} 組(合計 {pr['fell']} 組)"],
        ["直前の区分ごと", f"直前が優勢の組 {ahd} 組のうち {ah} 組({ah_pct}%)・直前が互角の組 {lvd} 組のうち {lv} 組({lv_pct}%)"],
        ["数に入れなかった組", f"直前が劣勢で下がりようがない {pr['behindExcluded']} 組・直前の区分が決められない {pr['beforeUndet']} 組・直後の区分が決められない {pr['afterUndet']} 組(詰みの値や王手中など)"],
        ["参考: 5 手以内", f"相手の手のあと 5 手以内のどこかで 1 段以上下がった組 {pr['win5'][0]} / {pr['win5'][1]} 組(棋譜の終わりが近く 5 手ぶん見られない {pr['windowShort']} 組は除く)"],
    ]
    ptab = Table([[P(k, S_K), P(v, S_V)] for k, v in prow], colWidths=[34 * mm, W - 34 * mm])
    ptab.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.6 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm)]))
    story.append(ptab)
    story.append(Spacer(1, 1.5 * mm))
    story.append(P(f"この数は、候補(条件式)を比べるときの土台(対照群)です。この版で調べた条件は {pr['conditions']} 本で、結果は「2. 今回調べた候補」のとおりです。候補が基準を満たしても「確定したもの」ではなく「追加の棋譜で確かめる価値のある候補」として扱います。", S_SMALL))

