# -*- coding: utf-8 -*-
# STEP ANSWER 作業(docs/STEP_ANSWER_PLAN_2026-09-23.md §2.1)。B(「どうしたら」の冊子)の markdown を検査する道具。
# 司令塔の事前監査 REVISE(2026-09-23・2026-09-24)の指示を反映済み(下の各節のコメントを参照)。
#
# 使い方:
#   python3 -X utf8 check_answer.py <B.md>
#     [--patient <patient_report_data.json> --time-limit-sec <秒>]…(組ごとに 1 対。180 秒 = 3 分の組、
#       600 秒 = 10 分の組、他の秒数/省略はタグ無し ― タグ無しは M1/M2/M8 の組の判定には使わない)
#     [--whatif-data <whatif_report_data.json>]…(複数可。数の照合の材料)
#     [--whatif-v2-dir <whatif-v2 jsonl のフォルダ>]…(複数可。M4「側の一致」の材料。組をまたいで合算する)
#     [--read-dir <read.ts の jsonl のフォルダ>]…(複数可。summary 行を合算する。組をまたいで合算する)
#     [--type-summary <summary.json>]…(複数可。数の照合の材料)
#     [--whatif-pdf <whatif.pdf>]…(複数可。fitz で印字を読み、指し手の答え合わせに使う)
#     --menu <answer_menu.json>
#
# 出力: rc=0 なら通過。rc=1 なら、落ちた文と理由の一覧(1 行 1 件)を標準エラーへ。
#
# 【この道具が絶対にやらないこと】B の文を直すこと(落ちた文の一覧を返すだけ)。将棋の判断。エンジンを回すこと。
import glob
import json
import os
import re
import sys

# ==================== 禁止語・表現(司令塔の指示。2026-09-23 REVISE 5・2026-09-24 の再監査 1) ====================
# 18 語(docs §2.1 検査 3 と同じ 18 語)+「すべき」「した方がよい」「すれば直る」「間違いなく」+
# 「危ない」「確実」「絶対」「安い」= 26 語。
BANNED_WORDS = [
    "悪手", "弱点", "癖", "型", "傾向", "原因", "ミス", "見落とし", "改善", "練習",
    "必ず", "明らか", "あなた", "ご自身", "いつも", "がち", "クセ", "パターン",
    "すべき", "した方がよい", "すれば直る", "間違いなく",
    "危ない", "確実", "絶対", "安い",
]

# 検査 4(司令塔の指示。2026-09-23 REVISE 4・2026-09-24 の再監査 3)。`<!-- menu: -->`/`<!-- priority: -->` の
# 外で、行動・優先順位を表す言い回しが見つかったら落とす。
ACTION_PHRASES = ["してみては", "を目安に", "選ぶなら", "1つだけ", "先に", "で指す", "を混ぜる", "候補に入れ"]

MENU_TAG_RE = re.compile(r"<!--\s*menu:\s*(M\d+)\s*-->")
PRIORITY_TAG_RE = re.compile(r"<!--\s*priority:\s*(M\d+)\s*-->")

# 指し手の表記(report-pdf/render_whatif.py の move_kanji と同じ形)。▲/△ + (同 or マス) + 駒 + (成/打)?
PIECE_CHARS = "歩香桂銀金角飛玉と杏圭全馬竜"
MOVE_RE = re.compile(rf"[▲△](?:同[\s　]*|[０-９][一二三四五六七八九])[{PIECE_CHARS}](?:成|打)?")

FIRST_CANDIDATE_WA_RE = re.compile(r"第\s*1\s*候補は")
GAME_PLY_REF_RE = re.compile(r"\d+\s*局目.*?\d+\s*手目", re.S)

RATIO_WORD_RE = re.compile(r"[0-9０-９]+\s*(倍|割)")


class CheckAnswerError(Exception):
    pass


# ==================== 引数 ====================


class CliArgs:
    def __init__(self):
        self.markdown_path = None
        self.patients = []  # list of (path, tag)
        self.whatif_data_paths = []
        self.whatif_v2_dirs = []
        self.read_dirs = []
        self.type_summary_paths = []
        self.whatif_pdf_paths = []
        self.menu_path = None


def tag_of_time_limit_sec(sec):
    if sec == 180:
        return "min3"
    if sec == 600:
        return "min10"
    return None


def parse_args(argv):
    args = CliArgs()
    positionals = []
    i = 0
    while i < len(argv):
        flag = argv[i]
        if flag == "--patient":
            path = argv[i + 1] if i + 1 < len(argv) else None
            if path is None or path.startswith("--"):
                raise CheckAnswerError("--patient に値が無い")
            # 司令塔の指示(2026-09-23 REVISE 1): `--time-limit-sec` は patient ごと(直後に置く)。
            if i + 2 >= len(argv) or argv[i + 2] != "--time-limit-sec":
                raise CheckAnswerError(f"--patient {path} の直後に --time-limit-sec が無い(組の見分けに使う)")
            sec_raw = argv[i + 3] if i + 3 < len(argv) else None
            if sec_raw is None or sec_raw.startswith("--"):
                raise CheckAnswerError("--time-limit-sec に値が無い")
            args.patients.append((path, tag_of_time_limit_sec(int(sec_raw))))
            i += 4
            continue
        if flag == "--whatif-data":
            args.whatif_data_paths.append(argv[i + 1])
            i += 2
            continue
        if flag == "--whatif-v2-dir":
            args.whatif_v2_dirs.append(argv[i + 1])
            i += 2
            continue
        if flag == "--read-dir":
            args.read_dirs.append(argv[i + 1])
            i += 2
            continue
        if flag == "--type-summary":
            args.type_summary_paths.append(argv[i + 1])
            i += 2
            continue
        if flag == "--whatif-pdf":
            args.whatif_pdf_paths.append(argv[i + 1])
            i += 2
            continue
        if flag == "--menu":
            args.menu_path = argv[i + 1]
            i += 2
            continue
        if flag.startswith("--"):
            raise CheckAnswerError(f"知らない引数: {flag}")
        positionals.append(flag)
        i += 1
    if len(positionals) != 1:
        raise CheckAnswerError("B の markdown ファイルを 1 つだけ指定する")
    args.markdown_path = positionals[0]
    if args.menu_path is None:
        raise CheckAnswerError("--menu が無い")
    return args


# ==================== JSON の読み込み・材料の組み立て ====================


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def collect_numbers(obj, out):
    """JSON の値を再帰的にたどり、数値(整数化・絶対値)をすべて集める(検査 1 の許す集合。bool は int の
    サブクラスなので除外する)。"""
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        out.add(abs(round(obj)))
        return
    if isinstance(obj, dict):
        for v in obj.values():
            collect_numbers(v, out)
        return
    if isinstance(obj, list):
        for v in obj:
            collect_numbers(v, out)


def bucket_or_zero(bucket):
    return bucket if bucket is not None else {"n": 0, "collapsed": 0}


def time_up_losses_facts(time_up_losses):
    """`time.timeUpLosses`(配列。無ければ None)から n・m(+300 以上の数)を出す。"""
    if time_up_losses is None:
        return {"n": 0, "m": 0}
    n = len(time_up_losses)
    m = sum(1 for g in time_up_losses if g.get("finalScore") is not None and g["finalScore"] >= 300)
    return {"n": n, "m": m}


def after_long_think_facts(after_long_think):
    if after_long_think is None:
        return {"any": {"n": 0, "collapsed": 0}, "quick": {"n": 0, "collapsed": 0}}
    return {
        "any": bucket_or_zero(after_long_think.get("afterLongThinkAny")),
        "quick": bucket_or_zero(after_long_think.get("quickAfterLongThink")),
    }


def ahead_loss_numbers(findings):
    for f in findings:
        if f.get("kind") == "aheadLoss":
            return f.get("numbers") or {}
    return {}


def by_spent_or_empty(time_data):
    by_spent = time_data.get("bySpent")
    if by_spent is None:
        return [{"n": 0, "collapsed": 0}] * 4
    return by_spent


class PatientFile:
    """1 本の patient_report_data.json から、検査に要る事実だけを抜いたもの。"""

    def __init__(self, path, tag):
        self.path = path
        self.tag = tag
        self.raw = load_json(path)
        time_data = self.raw.get("time") or {}
        self.games = self.raw["summary"]["games"]
        self.by_spent = by_spent_or_empty(time_data)
        self.time_up_losses = time_up_losses_facts(time_data.get("timeUpLosses"))
        self.after_long_think = after_long_think_facts(time_data.get("afterLongThink"))
        overview = self.raw.get("overview") or {}
        self.overview_fell = overview.get("fell", 0)
        self.overview_early = overview.get("early", 0)
        phase_spent = time_data.get("phaseSpent") or {}
        other_games = phase_spent.get("otherGames") or {}
        self.phase_spent_other_early = other_games.get("early")
        self.phase_spent_other_mid = other_games.get("mid")
        self.ahead_loss = ahead_loss_numbers(self.raw.get("findings") or [])


def by_spent_total(by_spent):
    n = sum(b["n"] for b in by_spent)
    collapsed = sum(b["collapsed"] for b in by_spent)
    return {"n": n, "collapsed": collapsed}


class CombinedGroup:
    """同じタグ(min3/min10)の patient を複数まとめたもの(司令塔の指示 2026-09-23 REVISE 1)。
    分子・分母はすべて別々に足す。中央値(phaseSpent)は合算しない ― 先頭の(games が最小の)ファイルを使う
    (実装担当の判断。複数局をまたいだ中央値の再計算はしない)。"""

    def __init__(self, tag, files):
        self.tag = tag
        self.files = files
        self.games = sum(f.games for f in files)
        self.time_up_losses = {
            "n": sum(f.time_up_losses["n"] for f in files),
            "m": sum(f.time_up_losses["m"] for f in files),
        }
        self.by_spent = [
            {"n": sum(f.by_spent[i]["n"] for f in files), "collapsed": sum(f.by_spent[i]["collapsed"] for f in files)}
            for i in range(4)
        ]
        self.by_spent_total = by_spent_total(self.by_spent)
        self.overview_fell = sum(f.overview_fell for f in files)
        self.overview_early = sum(f.overview_early for f in files)
        self.after_long_think_any = {
            "n": sum(f.after_long_think["any"]["n"] for f in files),
            "collapsed": sum(f.after_long_think["any"]["collapsed"] for f in files),
        }
        self.after_long_think_quick = {
            "n": sum(f.after_long_think["quick"]["n"] for f in files),
            "collapsed": sum(f.after_long_think["quick"]["collapsed"] for f in files),
        }
        primary = min(files, key=lambda f: f.games)
        self.phase_spent_other_early = primary.phase_spent_other_early
        self.phase_spent_other_mid = primary.phase_spent_other_mid


def combined_groups_of(patient_files):
    by_tag = {}
    for f in patient_files:
        if f.tag is None:
            continue
        by_tag.setdefault(f.tag, []).append(f)
    return {tag: CombinedGroup(tag, files) for tag, files in by_tag.items()}


# ==================== M4: 側の一致(司令塔の指示。2026-09-23 REVISE 2・2026-09-24 の再監査 2) ====================


def side_match_of(whatif_v2_dirs):
    """whatif-v2 jsonl(複数フォルダ)の position 行(kind="position", scenes.fork が true)から、
    第 1 候補の側(candidates[0].side)が「攻め」「守り」ちょうど 1 つだった局面だけを分母にし
    (「両方」は分母に入れない。非対称)、実戦の側(actualSide)が同じ側(both を含む)なら分子に数える。"""
    attack_n = attack_collapsed = 0
    defense_n = defense_collapsed = 0
    fork_total = 0
    for d in whatif_v2_dirs:
        for path in sorted(glob.glob(os.path.join(d, "*.jsonl"))):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    if row.get("kind") != "position":
                        continue
                    if not row.get("scenes", {}).get("fork"):
                        continue
                    fork_total += 1
                    candidates = row.get("candidates") or []
                    if not candidates:
                        continue
                    top1_side = candidates[0].get("side")
                    actual_side = row.get("actualSide")
                    if top1_side == "attack":
                        attack_n += 1
                        if actual_side in ("attack", "both"):
                            attack_collapsed += 1
                    elif top1_side == "defense":
                        defense_n += 1
                        if actual_side in ("defense", "both"):
                            defense_collapsed += 1
    if fork_total == 0:
        return None
    return {
        "attack": {"n": attack_n, "collapsed": attack_collapsed},
        "defense": {"n": defense_n, "collapsed": defense_collapsed},
        "forkTotal": fork_total,
    }


# ==================== READ 合算(司令塔の指示。2026-09-23 REVISE 1・2026-09-24 の再監査(M6)) ====================


def read_combined_of(read_dirs):
    fork_positions_read = 0
    first_visible_none = 0
    tag_cross_table_sacrifice = {}
    opponent_reply = {"matched": 0, "measured": 0}
    found_any = False
    for d in read_dirs:
        for path in sorted(glob.glob(os.path.join(d, "*.jsonl"))):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    if row.get("kind") != "summary":
                        continue
                    found_any = True
                    fork_positions_read += row.get("forkPositionsRead", 0)
                    buckets = row.get("firstVisibleNodesBuckets") or {}
                    first_visible_none += buckets.get("none", 0)
                    reply = row.get("opponentReplyMatchesPv") or {}
                    opponent_reply["matched"] += reply.get("matched", 0)
                    opponent_reply["measured"] += reply.get("measured", 0)
                    table = row.get("tagCrossTable") or {}
                    sac_row = table.get("sacrifice") or {}
                    for k, v in sac_row.items():
                        tag_cross_table_sacrifice[k] = tag_cross_table_sacrifice.get(k, 0) + v
    if not found_any:
        return None
    sacrifice_row_total = sum(tag_cross_table_sacrifice.values())
    sacrifice_diagonal = tag_cross_table_sacrifice.get("sacrifice", 0)
    return {
        "forkPositionsRead": fork_positions_read,
        "firstVisibleNodesNoneCount": first_visible_none,
        "sacrificeRowTotal": sacrifice_row_total,
        "sacrificeDiagonal": sacrifice_diagonal,
        "opponentReplyMatchesPv": opponent_reply,
    }


# ==================== 行動のメニューの条件判定(`lib/answerMenu.ts` の menuConditionHoldsOf の写し。
#   python は TS を import できないので手で合わせる ― render_front.py の GLOBAL_ALLOWED_NUMBERS と同じ流儀) ====================


def rate_of(bucket):
    if bucket is None or bucket["n"] == 0:
        return None
    return bucket["collapsed"] / bucket["n"]


def m1_holds(materials):
    # needsData(司令塔の指示 2026-09-23 REVISE 3)。
    return False


def m1_denominator(materials):
    return None


def m2_holds(materials):
    min3 = materials["groups"].get("min3")
    min10 = materials["groups"].get("min10")
    if min3 is not None and min3.time_up_losses["n"] >= 1:
        return True
    if min3 is None or min10 is None:
        return False
    rate3 = rate_of(min3.by_spent_total)
    rate10 = rate_of(min10.by_spent_total)
    if rate3 is None or rate10 is None:
        return False
    return rate3 > rate10 * 1.5


def m2_denominator(materials):
    min10 = materials["groups"].get("min10")
    return min10.games if min10 is not None else None


def primary_group(materials):
    return materials["groups"].get("min3") or (next(iter(materials["groups"].values()), None))


def m3_holds(materials):
    g = primary_group(materials)
    if g is None or g.overview_fell == 0:
        return False
    early_share_ok = g.overview_early / g.overview_fell <= 0.15
    if g.phase_spent_other_early is None or g.phase_spent_other_mid is None:
        return False
    return early_share_ok and g.phase_spent_other_early < g.phase_spent_other_mid


def m3_denominator(materials):
    g = primary_group(materials)
    return g.overview_fell if g is not None else None


def m4_holds(materials):
    sm = materials["sideMatch"]
    if sm is None:
        return False
    attack_rate = rate_of(sm["attack"])
    defense_rate = rate_of(sm["defense"])
    if attack_rate is None or defense_rate is None:
        return False
    return attack_rate < 0.7 and defense_rate < 0.7


def m4_denominator(materials):
    sm = materials["sideMatch"]
    return sm["forkTotal"] if sm is not None else None


def m5_holds(materials):
    g = primary_group(materials)
    if g is None:
        return False
    quick_rate = rate_of(g.after_long_think_quick)
    zero_to_one_rate = rate_of(g.by_spent[0])
    if quick_rate is None or zero_to_one_rate is None:
        return False
    return quick_rate >= zero_to_one_rate * 2


def m5_denominator(materials):
    g = primary_group(materials)
    return g.after_long_think_quick["n"] if g is not None else None


def m6_holds(materials):
    r = materials["readCombined"]
    if r is None or r["sacrificeRowTotal"] < 20:
        return False
    return r["sacrificeDiagonal"] / r["sacrificeRowTotal"] < 0.4


def m6_denominator(materials):
    r = materials["readCombined"]
    return r["sacrificeRowTotal"] if r is not None else None


def m7_holds(materials):
    r = materials["readCombined"]
    if r is None or r["forkPositionsRead"] == 0:
        return False
    at_least_600 = r["forkPositionsRead"] - r["firstVisibleNodesNoneCount"]
    return at_least_600 <= 0.4 * r["forkPositionsRead"]


def m7_denominator(materials):
    r = materials["readCombined"]
    return r["forkPositionsRead"] if r is not None else None


def m8_holds(materials):
    g = materials["groups"].get("min3") or primary_group(materials)
    if g is None or g.time_up_losses["n"] < 1:
        return False
    return g.time_up_losses["m"] == g.time_up_losses["n"]


def m8_denominator(materials):
    g = materials["groups"].get("min3") or primary_group(materials)
    return g.time_up_losses["n"] if g is not None else None


MENU_HOLDS = {"M1": m1_holds, "M2": m2_holds, "M3": m3_holds, "M4": m4_holds, "M5": m5_holds, "M6": m6_holds, "M7": m7_holds, "M8": m8_holds}
MENU_DENOMINATOR = {"M1": m1_denominator, "M2": m2_denominator, "M3": m3_denominator, "M4": m4_denominator, "M5": m5_denominator, "M6": m6_denominator, "M7": m7_denominator, "M8": m8_denominator}


# ==================== 検査 1: 数の照合(登録済みの組。司令塔の指示 2026-09-23 REVISE 6) ====================


def registered_pairs_of(patient_files, materials):
    """「a / b」「n のうち m」「n 局のうち m 局」の形が許される、既知の組の一覧(両方向)。
    README(scripts/playtest/report-pdf/README.md)にも同じ一覧を書く。"""
    pairs = set()

    def add(a, b):
        if a is None or b is None:
            return
        pairs.add((a, b))
        pairs.add((b, a))

    for f in patient_files:
        add(f.time_up_losses["n"], f.time_up_losses["m"])
        for bucket in f.by_spent:
            add(bucket["n"], bucket["collapsed"])
        add(f.after_long_think["any"]["n"], f.after_long_think["any"]["collapsed"])
        add(f.after_long_think["quick"]["n"], f.after_long_think["quick"]["collapsed"])
        add(f.ahead_loss.get("aheadGames"), f.ahead_loss.get("aheadLossGames"))

    for g in materials["groups"].values():
        add(g.time_up_losses["n"], g.time_up_losses["m"])
        for bucket in g.by_spent:
            add(bucket["n"], bucket["collapsed"])
        add(g.by_spent_total["n"], g.by_spent_total["collapsed"])
        add(g.after_long_think_any["n"], g.after_long_think_any["collapsed"])
        add(g.after_long_think_quick["n"], g.after_long_think_quick["collapsed"])

    r = materials["readCombined"]
    if r is not None:
        add(r["forkPositionsRead"], r["forkPositionsRead"] - r["firstVisibleNodesNoneCount"])
        add(r["sacrificeRowTotal"], r["sacrificeDiagonal"])
        add(r["opponentReplyMatchesPv"]["matched"], r["opponentReplyMatchesPv"]["measured"])

    sm = materials["sideMatch"]
    if sm is not None:
        add(sm["attack"]["n"], sm["attack"]["collapsed"])
        add(sm["defense"]["n"], sm["defense"]["collapsed"])

    return pairs


def percent_pool_of(pairs):
    """登録済みの組から、四捨五入した整数 % を作る(検査 1 の「JSON の分数から計算した割合」)。"""
    percents = set()
    for a, b in pairs:
        if b > 0 and a <= b:
            percents.add(round(100 * a / b))
    return percents


# ==================== data/ のレビュー済みの名前(検査 6。司令塔の指示 2026-09-23 REVISE 7) ====================


def reviewed_shape_names(repo_root):
    names = set()
    for folder in ("shapes", "openings", "intents"):
        for path in glob.glob(os.path.join(repo_root, "data", folder, "*.json")):
            d = load_json(path)
            if d.get("review_status") in ("human_reviewed", "expert_verified"):
                names.add(d.get("name"))
    return names


NAME_LIKE_RE = re.compile(r"[一-龥ァ-ヶー]{2,}(戦法|囲い|飛車|銀)")


# ==================== 全体の材料 ====================


def build_materials(args, repo_root):
    patient_files = [PatientFile(path, tag) for path, tag in args.patients]
    groups = combined_groups_of(patient_files)
    read_combined = read_combined_of(args.read_dirs)
    side_match = side_match_of(args.whatif_v2_dirs)

    allowed_numbers = set()
    for f in patient_files:
        collect_numbers(f.raw, allowed_numbers)
    for path in args.whatif_data_paths:
        collect_numbers(load_json(path), allowed_numbers)
    for path in args.type_summary_paths:
        collect_numbers(load_json(path), allowed_numbers)
    # 組ごとに合算した数も、単独の数として許す(例: 「34 局」「1134」)。
    for g in groups.values():
        collect_numbers(
            {
                "games": g.games,
                "timeUpLosses": g.time_up_losses,
                "bySpent": g.by_spent,
                "bySpentTotal": g.by_spent_total,
                "overviewFell": g.overview_fell,
                "overviewEarly": g.overview_early,
                "afterLongThinkAny": g.after_long_think_any,
                "afterLongThinkQuick": g.after_long_think_quick,
            },
            allowed_numbers,
        )
    if read_combined is not None:
        collect_numbers(read_combined, allowed_numbers)
    if side_match is not None:
        collect_numbers(side_match, allowed_numbers)
    # 構造そのものを表す数(minN・node ladder 等)は、判断的知識として個々の局面の事実ではないが、
    # メニューの文に出ることがあるので許す(render_front.py の GLOBAL_ALLOWED_NUMBERS と同じ考え方)。
    menu = load_json(args.menu_path)
    for item in menu["items"]:
        allowed_numbers.add(item["minN"])
    allowed_numbers |= {1, 2, 3, 4, 5, 600, 300, 15, 40, 70}

    materials = {"groups": groups, "readCombined": read_combined, "sideMatch": side_match}
    pairs = registered_pairs_of(patient_files, materials)
    allowed_numbers |= percent_pool_of(pairs)

    menu_ids = {item["id"] for item in menu["items"]}
    menu_minn = {item["id"]: item["minN"] for item in menu["items"]}

    whatif_pdf_text = ""
    if args.whatif_pdf_paths:
        import fitz  # pymupdf

        parts = []
        for path in args.whatif_pdf_paths:
            doc = fitz.open(path)
            try:
                for page in doc:
                    parts.append(page.get_text())
            finally:
                doc.close()
        whatif_pdf_text = re.sub(r"\s+", "", "".join(parts))

    return {
        "materials": materials,
        "allowedNumbers": allowed_numbers,
        "pairs": pairs,
        "menuIds": menu_ids,
        "menuMinN": menu_minn,
        "reviewedNames": reviewed_shape_names(repo_root),
        "whatifPdfText": whatif_pdf_text,
    }


# ==================== markdown の下ごしらえ ====================

DEV_SECTION_RE = re.compile(r"^##\s*書いた側の記録.*$", re.M)


def strip_dev_section(markdown_text):
    """「書いた側の記録(顧客には見せない)」の節(見出しから末尾まで)を検査の対象から外す。"""
    m = DEV_SECTION_RE.search(markdown_text)
    return markdown_text if m is None else markdown_text[: m.start()]


# ==================== 検査 ====================


def find_fraction_pairs(line):
    """「a / b」「n のうち m」「n 局のうち m 局」の形をすべて見つける(検査 1 の登録済みの組チェック用)。
    見つかった位置は返り値の span も返す(その数を単独チェックの対象から除くため)。"""
    found = []
    for m in re.finditer(r"(\d+)\s*/\s*(\d+)", line):
        found.append((int(m.group(1)), int(m.group(2)), m.span()))
    for m in re.finditer(r"(\d+)\s*局?\s*のうち\s*(\d+)\s*局?", line):
        found.append((int(m.group(1)), int(m.group(2)), m.span()))
    return found


def mask_spans(line, spans):
    chars = list(line)
    for start, end in spans:
        for i in range(start, end):
            chars[i] = " "
    return "".join(chars)


ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def check_line_numbers(line, ctx, problems, line_no):
    # 日付(YYYY-MM-DD。見出し・作成日の表記)は「文中の数の主張」ではないので対象から外す
    # (実装担当の判断。表題行の「2026-09-24」等が「データに無い数」として誤検知するのを防ぐ。
    # 報告する原文(line)はそのまま、数を探す側だけ日付を消す)。
    scan_line = ISO_DATE_RE.sub(" ", line)
    if RATIO_WORD_RE.search(scan_line):
        problems.append((line_no, "「倍」「割」は使わない(検査 1)", line))
        return
    fraction_matches = find_fraction_pairs(scan_line)
    for a, b, span in fraction_matches:
        if (a, b) not in ctx["pairs"]:
            problems.append((line_no, f"数の組み合わせが登録済みの組に無い({a}/{b}。検査 1)", line))
    masked = mask_spans(scan_line, [span for _, _, span in fraction_matches])
    for token_m in re.finditer(r"(\d+)\s*%", masked):
        n = int(token_m.group(1))
        if n not in ctx["allowedNumbers"]:
            problems.append((line_no, f"データに無い割合 {n}% が文に出ている(検査 1)", line))
    masked_no_percent = re.sub(r"(\d+)\s*%", " ", masked)
    for token_m in re.finditer(r"\d+", masked_no_percent):
        n = int(token_m.group(0))
        if n <= 9:
            continue  # 単位の無い小さな数は対象外(§2.1 検査 1。実装担当の判断: しきい値 9 で近似)
        if n not in ctx["allowedNumbers"]:
            problems.append((line_no, f"データに無い数 {n} が文に出ている(検査 1)", line))


def check_line_moves(line, ctx, problems, line_no, block_text):
    for m in MOVE_RE.finditer(line):
        move = m.group(0)
        move_normalized = re.sub(r"\s+", "", move)
        if ctx["whatifPdfText"] == "":
            continue  # --whatif-pdf が無ければ答え合わせをしない(実装担当の判断。データが無い時は検査を飛ばす)
        if move_normalized not in ctx["whatifPdfText"]:
            problems.append((line_no, f"指し手 {move} が付録 2 の印字に無い(検査 2)", line))
    if FIRST_CANDIDATE_WA_RE.search(line) and GAME_PLY_REF_RE.search(block_text) is None:
        problems.append((line_no, "「第 1 候補は」の形に「n 局目 m 手目」が無い(検査 2)", line))


def check_line_banned(line, problems, line_no):
    for w in BANNED_WORDS:
        if w in line:
            problems.append((line_no, f"使わない語「{w}」(検査 3)", line))


HEADING_ONLY_RE = re.compile(r"^\*\*[^*]+\*\*$")


def is_heading_only(line):
    """行の中身が太字だけの見出し(例: 「**こうしてみては**」)。見出しは行動の提案文そのものではないので、
    検査 4(行動・優先順位の表現)の対象から外す(実装担当の判断)。"""
    return HEADING_ONLY_RE.match(line.strip()) is not None


def check_line_action_phrases(line, ctx, problems, line_no, exempt):
    if exempt or is_heading_only(line):
        return
    for phrase in ACTION_PHRASES:
        if phrase in line:
            problems.append((line_no, f"行動/優先順位の表現「{phrase}」がメニューの印の外にある(検査 4)", line))


def check_line_names(line, problems, line_no, ctx):
    masked = MOVE_RE.sub(" ", line)
    for m in NAME_LIKE_RE.finditer(masked):
        name_like = m.group(0)
        if name_like not in ctx["reviewedNames"] and "のような形" not in line:
            problems.append((line_no, f"戦法・陣形らしき語「{name_like}」がレビュー済みの名前に無い(検査 6)", line))


def menu_tags_of(line):
    return MENU_TAG_RE.findall(line) + PRIORITY_TAG_RE.findall(line)


def check_menu_tags(line, ctx, problems, line_no):
    """検査 4(メニューの印)・検査 5(数が足りなければ言わない)。印が成立しているかを返す(検査 4 の除外判定用)。"""
    tags = menu_tags_of(line)
    if not tags:
        return False
    all_hold = True
    for tag_id in tags:
        if tag_id not in ctx["menuIds"]:
            problems.append((line_no, f"知らないメニュー id: {tag_id}(検査 4)", line))
            all_hold = False
            continue
        holds = MENU_HOLDS[tag_id](ctx["materials"])
        if not holds:
            problems.append((line_no, f"メニュー {tag_id} の条件が成り立たない(検査 4)", line))
            all_hold = False
            continue
        denominator = MENU_DENOMINATOR[tag_id](ctx["materials"])
        min_n = ctx["menuMinN"][tag_id]
        if denominator is None or denominator < min_n:
            problems.append((line_no, f"メニュー {tag_id} の根拠の数が minN({min_n})未満(検査 5。今の分母: {denominator})", line))
            all_hold = False
    return all_hold


def check_answer(markdown_text, ctx):
    body = strip_dev_section(markdown_text)
    lines = body.split("\n")
    blocks = re.split(r"\n\s*\n", body)
    block_of_line_no = {}
    idx = 0
    running = 0
    for block in blocks:
        block_line_count = block.count("\n") + 1
        for j in range(block_line_count):
            block_of_line_no[running + j] = block
        running += block_line_count + 1  # +1: 区切りの空行ぶん
    problems = []
    for line_no, line in enumerate(lines, start=1):
        if line.strip() == "":
            continue
        exempt = check_menu_tags(line, ctx, problems, line_no)
        check_line_numbers(line, ctx, problems, line_no)
        check_line_moves(line, ctx, problems, line_no, block_of_line_no.get(line_no - 1, line))
        check_line_banned(line, problems, line_no)
        check_line_action_phrases(line, ctx, problems, line_no, exempt)
        check_line_names(line, problems, line_no, ctx)
    return problems


def main(argv):
    args = parse_args(argv)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    ctx = build_materials(args, repo_root)
    with open(args.markdown_path, encoding="utf-8") as f:
        markdown_text = f.read()
    problems = check_answer(markdown_text, ctx)
    if problems:
        for line_no, reason, line in problems:
            print(f"{line_no}: {reason}: {line.strip()[:100]}", file=sys.stderr)
        return 1
    print("通過(落ちた文なし)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except CheckAnswerError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
