
# 付録 6: 急落の場面の一覧(1 行ずつ)
story.append(P(f"付録 6. 2 手で評価が 400 以上下がった場面の一覧", S_H2))
erows = [[P(x, S_K) for x in ["局", "手数", "指した手", "エンジンの候補", "評価(前 → 後)"]]]
GID = {g["no"]: g for g in m["games"]}
for e in sorted([e for e in m["events"] if e.get("kind") == "drop"], key=lambda e: (e["gameNo"], e["ply"])):
    g = GID[e["gameNo"]]
    erows.append([P(f"第 {e['gameNo']} 局", S_V), P(str(e["ply"]), S_V), P(disp_move(g, e["ply"], e["played"]), S_V), P("同じ手" if e["sameBest"] else disp_move(g, e["ply"], e["best"]), S_V), P(f"{fmt(e['before'])} → {fmt(e['after'])}", S_V)])
et = Table(erows, colWidths=[18 * mm, 14 * mm, 40 * mm, 40 * mm, W - 112 * mm], repeatRows=1)
et.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT), ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE), ("BACKGROUND", (0, 0), (-1, 0), BG), ("TOPPADDING", (0, 0), (-1, -1), 0.9 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 0.9 * mm)]))
story.append(et)

story.append(P("付録 7. 読み方の補足", S_H2))
notes = [
    f"<b>評価値</b>は将棋エンジン(やねうら王・NNUE)が見た形勢の数字です。プラスは{m['person']}が良い、マイナスは相手が良いことを表します。数字が大きいほど差が大きい、とだけ読んでください。",
    "+300 以上を「優勢」、−300 以下を「劣勢」とする境は仮の値で、今後の検証で変わります。",
    "「エンジンの候補」は、その局面でエンジンが最も良いとした手です。<b>良し悪しの判断ではなく、比べるための材料</b>です。評価が下がるのは、自分の手だけでなく相手の応手が良かったために起きることもあります(この報告では分けていません)。",
    "一局ずつのページの文は、解析の道具が出した事実(手数・評価・指し手)を、読みやすい日本語に言い換えたものです。文に出てくる数と指し手は、元の記録と機械的に照合しています。",
    "相手の名前と対局日時は載せていません。",
]
nt = Table([[P("・" + n, S_SMALL)] for n in notes], colWidths=[W])
nt.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("BACKGROUND", (0, 0), (-1, -1), BG), ("LEFTPADDING", (0, 0), (-1, -1), 3.5 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5 * mm), ("TOPPADDING", (0, 0), (-1, -1), 1.2 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2 * mm)]))
story.append(nt)
story.append(Spacer(1, 5 * mm))
story.append(P(f"作成 {m['today']} / 評価: NNUE 版やねうら王、1 局面あたり {m['engine']['nodes']} ノード / 解析コード {m['engine']['gitHead']} / 条件 {m['candidate']['id']}({m['candidate']['sha']}) / 試作版につき、有段者による確認はまだ受けていません。", st("foot", fontSize=8, leading=11, color=MUTED)))
doc.build(story)
print("wrote", out)

