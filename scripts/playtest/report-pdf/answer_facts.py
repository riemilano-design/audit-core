# -*- coding: utf-8 -*-
# STEP DELIVER-1(docs/STEP_DELIVER1_PLAN_2026-09-25.md §3 の 4)。B「どうしたら」の**「分かっている事実」の
# 箇条書きだけ**を、既存の JSON から機械で組む道具。出力は v7 と同じ見出し構造の md の下書き。
#
# 使い方:
#   python3 -X utf8 answer_facts.py --name <表示名> \
#     --patient <patient_report_data.json> --time-limit-sec <秒> [--patient … --time-limit-sec … …] \
#     [--whatif-v2-dir <dir>]… [--read-dir <dir>]… \
#     --direct <direct_answers.json> --direct <final_positions.json> \
#     --time-cause <time_cause.json> [--time-search <time_cause_search.json>] \
#     --out <md>
#
# 【最重要の設計(司令塔の指示)】**数を自分で計算しない。** 同じフォルダの `check_answer.py` を import して、
# その `PatientFile`・`combined_groups_of`(`CombinedGroup`)・`read_combined_of`・`side_match_of`・
# `direct_materials_of`・`time_cause_materials_of`・`tag_of_time_limit_sec`・`primary_group` が既に作っている
# 材料から数を**引くだけ**にする。`check_answer.py` は 1 バイトも変えない。新しい集計・新しい中央値・
# 新しい分数をここで作ったら、この STEP の制約違反である。
#
# 【文の形】v7(`18_B_…_v7_…_送付用.md`)の「分かっている事実」4 ブロック・14 個の箇条書きを**テンプレート**に
# し、差し替えるのは数だけ(文の形は変えない)。数が材料から引けない箇条書きは、その 1 行だけを
# `<!-- TODO: 読み -->` に落とし、標準エラーへ「どの数が出せなかったか」を出す(黙って省かない)。
#
# 事実の箇条書きは数だけ。比較・解釈・因果・程度(「多い」「ずっと」「〜と言えません」「〜ことが多い」)は
# 書き手が数を見て書く(2026-09-24 の人間の決定)。
#
# 【この道具が絶対にやらないこと】将棋の判断・評価・閾値。数の再計算・中央値の計算・分数の合算。
# 「読み」の文(考えられること)・「こうしてみては」の行・「例」の節を書くこと(= 人と LLM の仕事。
# プレースホルダで空ける)。名前を自分の中に持つこと(表示名は `--name` で受け取る)。
import os
import sys

import check_answer as CA

TODO = "<!-- TODO: 読み -->"

USAGE = "使い方: python3 -X utf8 answer_facts.py --name <表示名> --patient <path> --time-limit-sec <秒> … --direct <path> --direct <path> --time-cause <path> [--time-search <path>] --out <md>"


class AnswerFactsError(Exception):
    pass


# ==================== 引数 ====================


def parse_args(argv):
    """`check_answer.CliArgs` をそのまま使い(材料の組み立てを共有するため)、この道具だけの
    `--name`・`--out` を足す。`check_answer.parse_args` は markdown の positional と `--menu` を必須に
    するため、ここでは同じ形の小さな読み取りを置く(数の計算は一切しない)。"""
    args = CA.CliArgs()
    name = None
    out = None
    i = 0
    while i < len(argv):
        flag = argv[i]
        value = argv[i + 1] if i + 1 < len(argv) else None
        if flag in ("--name", "--out"):
            if value is None or value.startswith("--"):
                raise AnswerFactsError(f"{flag} に値が無い")
            if flag == "--name":
                name = value
            else:
                out = value
            i += 2
            continue
        if flag == "--patient":
            if value is None or value.startswith("--"):
                raise AnswerFactsError("--patient に値が無い")
            # `check_answer.py` と同じ形(`--time-limit-sec` は patient の直後に置く)。
            if i + 2 >= len(argv) or argv[i + 2] != "--time-limit-sec":
                raise AnswerFactsError(f"--patient {value} の直後に --time-limit-sec が無い(組の見分けに使う)")
            sec_raw = argv[i + 3] if i + 3 < len(argv) else None
            if sec_raw is None or sec_raw.startswith("--"):
                raise AnswerFactsError("--time-limit-sec に値が無い")
            args.patients.append((value, CA.tag_of_time_limit_sec(int(sec_raw))))
            i += 4
            continue
        targets = {
            "--whatif-v2-dir": args.whatif_v2_dirs,
            "--read-dir": args.read_dirs,
            "--direct": args.direct_paths,
            "--time-cause": args.time_cause_paths,
            "--time-search": args.time_search_paths,
        }
        if flag in targets:
            if value is None or value.startswith("--"):
                raise AnswerFactsError(f"{flag} に値が無い")
            targets[flag].append(value)
            i += 2
            continue
        raise AnswerFactsError(f"知らない引数: {flag}。{USAGE}")
    if name is None or out is None:
        raise AnswerFactsError(f"--name と --out は必須。{USAGE}")
    return args, name, out


# ==================== 材料(check_answer.py の組み立てをそのまま使う) ====================


def build(args):
    patient_files = [CA.PatientFile(path, tag) for path, tag in args.patients]
    return {
        "patientFiles": patient_files,
        "groups": CA.combined_groups_of(patient_files),
        "readCombined": CA.read_combined_of(args.read_dirs),
        "sideMatch": CA.side_match_of(args.whatif_v2_dirs),
        "direct": CA.direct_materials_of(args.direct_paths),
        "timeCause": CA.time_cause_materials_of(args.time_cause_paths),
        "readDirs": args.read_dirs,
    }


def joined(values):
    """v7 の「84・77・84」の並べ方(値を「・」でつなぐだけ。並べ替えない・計算しない)。"""
    return "・".join(str(v) for v in values)


def all_same(values):
    return len(values) > 0 and all(v == values[0] for v in values)


def raw_time_cause_group(materials, time_limit_sec):
    """`time_cause.json` の `groups[]` のうち、その持ち時間の組の**生の辞書**(中央値の欄を引くため)。
    合算はしない(`--time-cause` を 1 本渡す前提。複数あれば最初の 1 本を使い、呼び出し側が TODO に落とす)。"""
    tc = materials["timeCause"]
    if tc is None:
        return None
    for data in tc["raw"]:
        for g in data["groups"]:
            if g.get("timeLimitSec") == time_limit_sec:
                return g
    return None


def time_cause_games(materials, group_label, time_up_loss):
    """`time_cause.json` の `games[]` から、その組・その条件の局を**ファイルの順のまま**返す(選ぶだけ)。"""
    tc = materials["timeCause"]
    if tc is None:
        return []
    rows = []
    for data in tc["raw"]:
        for g in data["games"]:
            if g.get("group") == group_label and bool(g.get("timeUpLoss")) == time_up_loss:
                rows.append(g)
    return rows


def final_position_entries(materials):
    direct = materials["direct"]
    if direct is None:
        return []
    entries = []
    for raw in direct["raw"]:
        if raw.get("kind") == "final_positions":
            entries.extend(raw["entries"])
    return entries


def current_patient(materials, tag):
    """「今回」の組 = その tag の `--patient` のうち**最後に渡されたもの**(`deliver.ts` は組を
    前回 → 今回 の順に渡す。実装担当の判断。報告に明記)。"""
    files = [f for f in materials["patientFiles"] if f.tag == tag]
    return files[-1] if files else None


def read_game_count(materials):
    """READ を回した局の数 = `--read-dir` の `*.jsonl` の**ファイル数**(局ごとに 1 本)。
    数の集計ではなく入力の数え上げ(実装担当の判断。報告に明記)。"""
    import glob

    total = 0
    for d in materials["readDirs"]:
        total += len(glob.glob(os.path.join(d, "*.jsonl")))
    return total


# ==================== 「分かっている事実」の 14 個(v7 の文をテンプレートにする) ====================


class Missing(Exception):
    """その箇条書きに要る数が材料から引けない(呼び出し側が TODO に落とし、報告する)。"""


def need(value, what):
    if value is None:
        raise Missing(what)
    return value


def bullet_1(m, name):
    g3 = need(m["groups"].get("min3"), "3 分の組(min3)の patient")
    g10 = need(m["groups"].get("min10"), "10 分の組(min10)の patient")
    cur = current_patient(m, "min3")
    entries = final_position_entries(m)
    if not entries:
        raise Missing("final_positions.json の entries")
    cur_ids = set()
    if cur is not None:
        cur_ids = {game["id"] for game in cur.raw.get("games", [])}
    parts = []
    for e in entries:
        prefix = "今回の " if e.get("kifuId") in cur_ids else ""
        head = f"{prefix}{e['gameNo']} 局目({e['moves']} 手で時間切れ)は"
        if e.get("mate") is not None:
            parts.append(f"{head}**ここから {e['mate']} 手で{name}の勝ちの詰み**")
        elif e.get("scoreCp") is not None:
            # 正のときだけ + を付ける(負なら「+-」にならないよう、符号は数字自身に任せる)。
            score = e["scoreCp"]
            sign = "+" if score > 0 else ""
            parts.append(f"{head} {sign}{score}")
        else:
            raise Missing(f"final_positions の {e.get('kifuId')} の評価(scoreCp も mate も無い)")
    return (
        f"- 時間で負けた {g3.time_up_losses['n']} 局の最後の局面をエンジンで読むと(付録 3 の 3 ページ)、"
        f"{'、'.join(parts)}。"
        f"10 分 + 30 秒の {g10.games} 局では、時間で負けた局は {g10.time_up_losses['n']} 局。"
    )


def bullet_2(m, name):
    g3 = need(m["groups"].get("min3"), "3 分の組(min3)の patient")
    tc3 = need(raw_time_cause_group(m, 180), "time_cause.json の 3 分の組")
    tul = time_cause_games(m, tc3["group"], True)
    if not tul:
        raise Missing("time_cause.json の 3 分の組の時間切れ負けの局")
    mids = [g["phaseSpentSec"]["mid"] for g in tul]
    remains = [g["remainingSec"] for g in tul]
    if any(r is None for r in remains):
        raise Missing("time_cause.json の remainingSec")
    return (
        f"- 中盤の消費(付録 4 の 4 ページ): "
        f"時間で負けた {g3.time_up_losses['n']} 局の中盤の消費は {joined(mids)} 秒。"
        f"他の {tc3['other']['games']} 局の中央値は {tc3['other']['medianMidSec']} 秒。"
        f"中盤が終わった時点の残り時間は {joined(remains)} 秒でした。"
    )


def bullet_3(m, name):
    tc3 = need(raw_time_cause_group(m, 180), "time_cause.json の 3 分の組")
    tul = time_cause_games(m, tc3["group"], True)
    if not tul:
        raise Missing("time_cause.json の 3 分の組の時間切れ負けの局")
    # この箇条書きは「**中盤** N 秒の中身」なので、長考の回数は**中盤の**回数(`longThinkCountByPhase.mid`)。
    # 局ぜんたいの `longThinkTotal` ではない(v7 の「3 回ずつ」は中盤の回数と一致する。全局の合計は 3・3・5)。
    long_counts = [g["longThinkCountByPhase"]["mid"] for g in tul]
    if not all_same(long_counts):
        raise Missing(f"中盤の長考の回数が局ごとに違う({joined(long_counts)})ので v7 の「… 回ずつ」の形にできない")
    streaks = [g["longThinkStreakCount"] for g in tul]
    if not all(s == 0 for s in streaks):
        raise Missing(f"長考が続いた局がある({joined(streaks)})ので v7 の「長考が 2 手続いた局はありません」が使えない")
    longests = [g["longestMove"]["sec"] for g in tul]
    mid_thinks = [g["midThinkTotal"]["sec"] for g in tul]
    return (
        f"- **中盤 {tc3['timeUpLoss']['medianMidSec']} 秒の中身**は、10 秒以上の長考が {long_counts[0]} 回ずつ"
        f"(最長は {joined(longests)} 秒。長考が 2 手続いた局はありません)と、"
        f"5〜9 秒の中考の積み重なり(合計 {joined(mid_thinks)} 秒。"
        f"他の局の中央値は {tc3['other']['medianMidThinkSec']} 秒)です。"
    )


def bullet_4(m, name):
    tc = need(m["timeCause"], "time_cause.json")
    tc3 = need(raw_time_cause_group(m, 180), "time_cause.json の 3 分の組")
    combined = need(tc["groups"].get(tc3["group"]), "time_cause の 3 分の組(合算)")
    fork = combined.fork_fraction
    opposite = combined.opposite_side_fraction
    if fork["denominator"] == 0 or opposite["denominator"] == 0:
        raise Missing("C7・C8 の分母が 0")
    return (
        f"- 分かれ道(エンジンの第 1 候補と差が開く局面)との重なり: "
        f"{tc3['group']}の組では、長考 {fork['denominator']} 回のうち分かれ道に当たったのは {fork['numerator']} 回"
        f"({fork['numerator']} / {fork['denominator']})。"
        f"そのうち攻め・守りの側が逆だったのは {opposite['numerator']} 回({opposite['numerator']} / {opposite['denominator']})。"
    )


def bullet_5(m, name):
    g3 = need(m["groups"].get("min3"), "3 分の組(min3)の patient")
    tc3 = need(raw_time_cause_group(m, 180), "time_cause.json の 3 分の組")
    tul = time_cause_games(m, tc3["group"], True)
    if not tul:
        raise Missing("time_cause.json の 3 分の組の時間切れ負けの局")
    earlies = [g["phaseSpentSec"]["early"] for g in tul]
    return (
        f"- 序盤の消費: 時間で負けた {g3.time_up_losses['n']} 局は {joined(earlies)} 秒、"
        f"他の局の中央値は {tc3['other']['medianEarlySec']} 秒。"
        f"時間で負けた局の中央値は序盤 {tc3['timeUpLoss']['medianEarlySec']} 秒・"
        f"中盤 {tc3['timeUpLoss']['medianMidSec']} 秒。"
    )


def bullet_6(m, name):
    need(m["groups"].get("min3"), "3 分の組(min3)の patient")
    need(raw_time_cause_group(m, 180), "time_cause.json の 3 分の組(C9 の表)")
    return "- 飛車の筋(振り飛車か居飛車のような形か)は付録 4 の 4 ページの表。"


def bullet_7(m, name):
    g3 = need(m["groups"].get("min3"), "3 分の組(min3)の patient")
    tc3 = need(raw_time_cause_group(m, 180), "time_cause.json の 3 分の組(組の名前)")
    ge10_g, le1_g = g3.by_spent[3], g3.by_spent[0]
    # min3 の --patient が 1 つだけ(= 前回の組が無い初回の顧客)なら、「今回の…局だけなら」を
    # 重ねて書かない(cur と g3 が必ず同じ組になり、同じ分数が 2 回並ぶため)。数が偶然一致したかで
    # 判定しない(材料の形=min3 の patient の本数で判定する。実装担当の判断。指示書 1-B)。
    min3_patient_count = len([f for f in m["patientFiles"] if f.tag == "min3"])
    if min3_patient_count == 1:
        return (
            f"- 10 秒以上考えた手の崩れ: {tc3['group']} {g3.games} 局で {ge10_g['collapsed']} / {ge10_g['n']}。"
            f"1 秒以内の手は {le1_g['collapsed']} / {le1_g['n']}({g3.games} 局)。"
        )
    cur = need(current_patient(m, "min3"), "今回の組(min3 の最後の patient)")
    ge10_c, le1_c = cur.by_spent[3], cur.by_spent[0]
    return (
        f"- 10 秒以上考えた手の崩れ: {tc3['group']} {g3.games} 局で {ge10_g['collapsed']} / {ge10_g['n']}、"
        f"今回の {cur.games} 局だけなら {ge10_c['collapsed']} / {ge10_c['n']}。"
        f"1 秒以内の手は {le1_g['collapsed']} / {le1_g['n']}({g3.games} 局)、"
        f"{le1_c['collapsed']} / {le1_c['n']}({cur.games} 局)。"
    )


def bullet_8(m, name):
    g3 = need(m["groups"].get("min3"), "3 分の組(min3)の patient")
    quick = g3.after_long_think_quick
    if quick["n"] == 0:
        raise Missing("長考の次の速い手(quickAfterLongThink)の分母が 0")
    return (
        f"- **長く考えた「次の」速い手も** {quick['collapsed']} / {quick['n']} が崩れています"
        f"({g3.games} 局。直前の自分の手が 10 秒以上で、この手は 4 秒以内)。"
    )


def bullet_9(m, name):
    g3 = need(m["groups"].get("min3"), "3 分の組(min3)の patient")
    return (
        f"- {g3.games} 局の崩れの数は、1 秒以内の手で {g3.by_spent[0]['collapsed']}、"
        f"10 秒以上の手で {g3.by_spent[3]['collapsed']}。"
    )


def bullet_10(m, name):
    r = need(m["readCombined"], "read/ の summary(--read-dir)")
    games = read_game_count(m)
    if games == 0:
        raise Missing("--read-dir の *.jsonl が 0 本")
    measured = r["forkPositionsRead"] - r["firstVisibleNodesNoneCount"]
    return (
        f"- 分かれ道(第 1 候補との差が大きい、または候補 5 つに入らなかった手)は {games} 局で {r['forkPositionsRead']}。"
        f"そのうち、100 万ノードまで読んで差が 600 以上と測れたものは {measured} / {r['forkPositionsRead']}。"
        f"残りは「少しずつ低い手」です。"
    )


def bullet_11(m, name):
    d = need(m["direct"], "direct_answers.json(--direct)")
    t1, ac, sd = d["top1TagCounts"], d["actualTagCounts"], d["top1SideCounts"]
    return (
        f"- 長く読まなくても実戦の手と第 1 候補の差が見えた分かれ道は {d['totalCount']} 局面"
        f"(付録 3 の 4 ページから、局面つき)。"
        f"その {d['totalCount']} 局面の第 1 候補の性質は、打つ {t1['drop']}・捨て駒 {t1['sacrifice']}・"
        f"取る {t1['capture']}・王手 {t1['givesCheck']}。"
        f"側は攻め {sd['attack']}・守り {sd['defense']}。"
        f"実戦の手は、打つ {ac['drop']}・捨て駒 {ac['sacrifice']}。"
    )


def bullet_12(m, name):
    r = need(m["readCombined"], "read/ の summary(--read-dir)")
    return (
        f"- エンジンの第 1 候補が**駒を捨てる手**だった分かれ道は {r['sacrificeRowTotal']}。"
        f"そのうち実戦も駒を捨てたのは {r['sacrificeDiagonal']}"
        f"({r['sacrificeRowTotal']} のうち {r['sacrificeDiagonal']})。"
    )


def bullet_13(m, name):
    sm = need(m["sideMatch"], "whatif-v2 の側の一致(--whatif-v2-dir)")
    if sm["attack"]["n"] == 0 or sm["defense"]["n"] == 0:
        raise Missing("側の一致の分母が 0")
    return (
        f"- 分かれ道で、エンジンが攻めの手を選んだとき実戦も攻めたのは {sm['attack']['collapsed']} / {sm['attack']['n']}、"
        f"守りのとき守ったのは {sm['defense']['collapsed']} / {sm['defense']['n']}。"
    )


def bullet_14(m, name):
    r = need(m["readCombined"], "read/ の summary(--read-dir)")
    reply = r["opponentReplyMatchesPv"]
    if reply["measured"] == 0:
        raise Missing("相手の返しの分母が 0")
    return f"- 相手の実際の返しが、エンジンの読み筋と同じだったのは {reply['matched']} / {reply['measured']}。"


# ブロックごとの箇条書き(v7 の 29〜34 行・62〜63 行・66 行・69〜73 行の計 14 個)。
BLOCKS = [
    ("**分かっている事実**", [bullet_1, bullet_2, bullet_3, bullet_4, bullet_5, bullet_6]),
    ("**分かっている事実 (a): 長く考えた手の崩れ**", [bullet_7, bullet_8]),
    ("**分かっている事実 (b): 速く指した手の崩れ**", [bullet_9]),
    ("**分かっている事実 (c): 分かれ道で何が起きているか**", [bullet_10, bullet_11, bullet_12, bullet_13, bullet_14]),
]

# v7 の「この冊子の約束(読み手向け)」。数を含まないので、v7 の文をそのまま固定文として置く(司令塔の指示)。
PROMISE = """1. ここに出る秒数・回数・評価は、すべて事実の冊子と付録 1〜4 にあるものです。付録で確かめられないことは書きません。
2. 指し手は、付録 2・付録 3 に印字されているエンジンの候補と読み筋だけを引きます。「この局面ではこの手」を新しく作りません。
3. 「これで直る」とは書きません。「事実から見て、試す価値の高い順」に並べます。当たり外れは、次の 20 局が来れば確かめます。来なくても、この 1 冊で使えるように書きます。
4. 「やらなくていいこと」も書きます。事実から効果を予測できない処方は、今回の優先候補には入れません(将来も効かない、という意味ではありません)。"""


def render(materials, name, has_time_search):
    """v7 と同じ見出し構造の md を組む。事実の箇条書き以外はすべて `<!-- TODO: 読み -->`。
    `has_time_search`(= `--time-search` が渡されたか)で、存在しない付録 4 の 8〜11 ページを
    案内しないように見出しを切り替える(指示書 1-A。初回の顧客は探索を回していないため
    8〜11 ページが無い)。`materials` に `hasTimeSearch` を足す(将来の箇条書きが同じ値を見られるように、
    見出しの切り替えと同じ場所に置いておく。2026-09-24 時点では bullet_9 はこの値を読まない ―
    探索の有無に触れる読みの文を落としたため)。"""
    materials["hasTimeSearch"] = has_time_search
    missing = []
    rendered_blocks = []
    for heading, builders in BLOCKS:
        lines = []
        for index, builder in enumerate(builders):
            try:
                lines.append(builder(materials, name))
            except Missing as e:
                lines.append(TODO)
                missing.append((heading, index + 1, str(e)))
        rendered_blocks.append((heading, lines))

    def block(index):
        heading, lines = rendered_blocks[index]
        return heading + "\n" + "\n".join(lines)

    if has_time_search:
        time_search_heading_1 = "**何がその局を遅くするのか ― 機械に探させた結果(付録 4 の 8〜11 ページ)**"
        time_search_heading_2 = "**機械に探させた結果(問題 2 にも同じ探索を当てました。付録 4 の 8〜11 ページ)**"
    else:
        time_search_heading_1 = "**何がその局を遅くするのか ― 今回は機械に探させていません(発見用と検証用の 2 組が要るため、2 回目の納品から出ます)**"
        time_search_heading_2 = "**今回は機械に探させていません(問題 2 も同じです。2 回目の納品から出ます)**"

    md = f"""# 「どうしたら」への答え

{TODO}

## この冊子の約束(読み手向け)

{PROMISE}

---

## ひとことで

{TODO}

---

## 問題 1: 時間で負ける

{block(0)}

{time_search_heading_1}

{TODO}

**こうしてみては**

{TODO}

---

## 問題 2: 考えた手で崩れる

{TODO}

{block(1)}

{block(2)}

{block(3)}

{time_search_heading_2}

{TODO}

**こうしてみては**

{TODO}

---

## 例: 付録 2・付録 3 の局面で、上の手順をなぞると(手と評価は付録の印字のまま)

{TODO}

---

## 数を見て取り下げたこと

{TODO}

## やらなくていいこと(事実から出ていない処方)

{TODO}

---

## 次の 20 局が来たら、何で答え合わせをするか

{TODO}
"""
    return md, missing


def main(argv):
    args, name, out = parse_args(argv)
    materials = build(args)
    md, missing = render(materials, name, bool(args.time_search_paths))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    total = sum(len(builders) for _, builders in BLOCKS)
    print(f"書き込み: {out}(事実の箇条書き {total - len(missing)} / {total})")
    if missing:
        print(f"材料から出せなかった箇条書き {len(missing)} 件(その行は {TODO} に落とした):", file=sys.stderr)
        for heading, index, reason in missing:
            print(f"- {heading} の {index} 個目: {reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (AnswerFactsError, CA.CheckAnswerError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
