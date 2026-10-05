# -*- coding: utf-8 -*-
# STEP ANSWER 作業(docs/STEP_ANSWER_PLAN_2026-09-23.md §2.1)。B(「どうしたら」の冊子)の markdown を検査する道具。
# 司令塔の事前監査 REVISE(2026-09-23・2026-09-24)の指示を反映済み(下の各節のコメントを参照)。
#
# 【追加作業 ANSWER-MENU2(2026-09-24、docs §8)を反映した点】
# - 検査 4 に、メニューの答え合わせの下限(`verifyGate`。§8.1)の判定を足した。`<!-- menu: Mx -->` の行は、
#   条件(menuConditionHoldsOf 相当)・minN(検査 5)に加えて、`answer_menu.json` の該当項目に `verifyGate` が
#   あれば、その下限も満たさなければ落とす(理由「答え合わせの数が下限に届かない(検査 4)」)。M1 だけが持つ
#   (`midOver.overAndTimeUpLoss / midOver.over ≥ 1/2`)。
# - `answer_menu.json` の項目に `foundInSameData: true`(M9 だけ)があれば、その印の行に
#   「今回の対局から見つけた読みです」の句が無ければ落とす(理由「今回の対局から見つけた読みの句が無い
#   (検査 4)」)。
# - M9(中盤の消費の合計。§8.2)の材料を patient の `time.phaseSpent.perGame`・`otherGames.mid` から作る
#   (`lib/answerMenu.ts` 冒頭のコメントと同じ実装担当の判断: 同じタグの patient が複数あるときは
#   `timeUpLossMidSecs` を連結、`otherGamesMidMedian` は代表ファイル(primary。既存の `phase_spent_other_mid` と
#   同じ)の中央値)。古い patient(`perGame` が無い)は `timeUpLossMidSecs` が空になるため M9 は不成立。
# - 検査 1 の登録済みの組に「時間負けのうち中央値超え / 時間負け」を足した(両方向)。
#
# 使い方:
#   python3 -X utf8 check_answer.py <B.md>
#     [--patient <patient_report_data.json> --time-limit-sec <秒>]…(組ごとに 1 対。180 秒 = 3 分の組、
#       600 秒 = 10 分の組、他の秒数/省略はタグ無し ― タグ無しは M1/M2/M8 の組の判定には使わない)
#     [--whatif-data <whatif_report_data.json>]…(複数可。**数の照合(検査 1)だけ**の材料。全組を渡す)
#     [--whatif-data-now <whatif_report_data.json>](0 本または 1 本だけ ― 2 本以上は落ちる。付録 2(検査 7)の
#       材料は**これだけ**から作る。局番号は組ごとに 1 から振られ、納品される付録 2〈`DELIVER_OUT_NAMES.whatif`〉
#       は今回の組のデータだけなので、材料も今回の組の 1 本に限る〈2026-09-25〉。`--whatif-data` に他の組を
#       混ぜても、検査 7 は `--whatif-data-now` の 1 本しか見ない)
#     [--whatif-v2-dir <whatif-v2 jsonl のフォルダ>]…(複数可。M4「側の一致」の材料。組をまたいで合算する)
#     [--read-dir <read.ts の jsonl のフォルダ>]…(複数可。summary 行を合算する。組をまたいで合算する)
#     [--type-summary <summary.json>]…(複数可。数の照合の材料)
#     [--whatif-pdf <whatif.pdf>]…(複数可。fitz で印字を読み、指し手の答え合わせに使う)
#     [--direct <json>]…(複数可。付録 3(ANSWER-DIRECT)の `direct_answers.json`・`final_positions.json` の
#       どちらも受け付ける ― 中身の `kind` で見分ける。docs/STEP_ANSWER_PLAN_2026-09-23.md §9.2「数の照合」。
#       検査 1 の単独の数の材料に足すほか、下の「登録済みの組」に (i)〜(v) を足す)
#     [--time-cause <json>]…(複数可。付録 4(STEP TIME-CAUSE)の `time_cause.json`(`lib/timeCause.ts` の
#       `TimeCauseFile`)。中身の `kind`(`"time_cause"`)で確かめる。検査 1 の単独の数の材料に足すほか、
#       下の「登録済みの組」に (i)〜(iv) を足す ― `--direct` と同じ流儀)
#     [--time-search <json>]…(複数可。付録 4 の探索(STEP TIME-CAUSE-2・STEP TIME-CAUSE-3・CAUSE-SEARCH-1)の
#       `time_cause_search.json`(`scripts/playtest/timeSearch.ts` の出力、`lib/timeSearch.ts` の
#       `SearchResult`)。中身の `kind`(`"time_cause_search"`)で確かめる。検査 1 の単独の数の材料に足すほか、
#       下の「登録済みの組」に (i)〜(x) を足す ― `--direct`・`--time-cause` と同じ流儀。(iv)〜(vii) は
#       STEP TIME-CAUSE-3(崩れ q・共通因子・偶然の目安)、(viii)〜(x) は CAUSE-SEARCH-1(`searches.*`・
#       `byOutcome.decisionGap` の単独の分数)で足した)
#     [--prose <prose.json>](0 本または 1 本だけ ― 2 本以上は落ちる。付録 1(検査 7)の材料。局番号は組ごとに
#       1 から振られ、納品される付録 1 は今回の組の本編だけなので、材料も今回の組の 1 本に限る〈2026-09-25〉。
#       `render_main.py`〈`_mid.py`〉が `prose.json` の `scenes[]` から盤を描く局面。中身の形は
#       `{"<局番号>": {"scenes": [{"ply": …}, …], …}, …}`)
#     --menu <answer_menu.json>
#
# 出力: rc=0 なら通過。rc=1 なら、落ちた文と理由の一覧(1 行 1 件)を標準エラーへ。
#
# 【検査 7(局面の参照。docs/STEP_DELIVER1_PLAN_2026-09-25.md §11.7、2026-09-24 の人間の委任)】
# 書き手が `<!-- pos: G/P 付録N -->`(G = 局番号、P = 手目、N = 1〜4)を局面を指す行に置くと、宣言された
# (G, P) が付録 N の材料に実在するかを確かめる(本文は解析しない。宣言の無い参照は検査しない ― 既知の限界)。
# 付録ごとの材料: 付録 1(納品される「2_付録1_形勢が動いた対局」= `render_main.py`〈`_head.py + _util.py +
# _mid.py` の連結〉が作る)= `--prose` の `prose.json` の `scenes[]`(gameNo は局番号のキー〈文字列 → int〉、
# ply = `scenes[].ply`。`_mid.py` 133〜143 行が `scenes[]` の各要素〈`type` が "move" でもそれ以外でも〉から
# 盤を描く)。付録 2(「3_付録2_分かれ道」= `render_whatif.py`)= `--whatif-data-now` の `whatif_report_data.json`
# の `games[].representative`(gameNo・displayPly。`render_whatif.py` 687〜743 行が盤を描く)。**`--whatif-data`
# ではない** ― `--whatif-data` は検査 1(数の照合)のために全組を受け取るが、納品される付録 2
# (`DELIVER_OUT_NAMES.whatif`。`lib/deliver.ts` が `thisGroup.whatifPdf` の 1 本だけを `out.whatif` に
# コピーする)は今回の組のデータだけであり、局番号は組ごとに 1 から振られるため、`--whatif-data` を材料に
# すると他の組の局面が「付録 2 にある」と誤って通ってしまう(2026-09-25 の直し)。付録 3
# (「5_付録3_直接の答え」= `render_direct.py`)= `--direct` の `direct_answers.json` の `answers[]`
# (gameNo・displayPly。`render_direct.py` 464〜606 行が盤を描く)と `final_positions.json` の `entries[]`
# (gameNo・moves。同ファイル 531〜545 行が盤を描く)。**付録 3 だけは 1 冊に全組(3 分の組・10 分の組…)を
# 載せる設計であり、局番号は組ごとに 1 から振られるため、(G, P) だけでは組の取り違えを検査できない
# (基準 44 局で 3 分 21 件・10 分 9 件、重なりは 0 件だが潜在。2026-09-25 の直し、凍結の例外 7b)。このため
# 付録 3 の印だけ `<!-- pos: G/P 付録3 <組> -->` の形で組(`answers[].group`/`entries[].group` と同じ値。
# 例: 「3 分」「10 分」)を持たせられる。材料の組の種類が 2 つ以上なら、組の無い宣言は「付録 3 の宣言に組が
# 無い」で落とす(使える組の値をメッセージに並べる)。組がある宣言は (組, G, P) で照合し、無ければ
# (未知の組を含む)「局面 {G}/{P} は付録 3 の組 {組} の材料に無い」で落とす。材料の組が 1 種類だけなら、
# 組の無い宣言は従来どおり (G, P) だけで照合し、組がある宣言はその 1 種類と一致しなければ同じ理由で落とす。
# 付録 1・2・4 の印に組を書くと「付録 {N} の宣言に組は書かない」で落とす(その 3 つは付録ごとに閉じており、
# 組は意味を持たない)。付録 4(「6_付録4_時間の使い方」= `render_time_cause.py`)には盤が 1 枚も無い
# (表と帯グラフだけ。`Board(` も sfen も出てこない)ため、`<!-- pos: G/P 付録4 -->` は組の有無にかかわらず
# 常に「付録 4 には盤が無い(検査 7)」で落とす(司令塔の指示、2026-09-24。ただし組が書かれていれば
# 「組は書かない」を先に返す)。
# 材料が渡されていない付録・形の崩れ・1〜4 以外の N も落とす(黙って通さない)。印の中の数字は検査 1 の
# 対象から外す(`menu` の印と同じ扱い)。
#
# 【この道具が絶対にやらないこと】B の文を直すこと(落ちた文の一覧を返すだけ)。将棋の判断。エンジンを回すこと。
import glob
import json
import os
import re
import sys

# ==================== 禁止語・表現(司令塔の指示。2026-09-23 REVISE 5・2026-09-24 の再監査 1) ====================
# 2026-09-25 の人間の決定(凍結の例外 14 件目)で空にした。それまでの 26 語(18 語+「すべき」「した方が
# よい」「すれば直る」「間違いなく」「危ない」「確実」「絶対」「安い」)は、冊子ですべて使ってよい。
# `check_line_banned` と検査 3 の枠は残す(語が無いので何も落とさない)。「断定しない」は機械では見ず、
# 監査が読む。
BANNED_WORDS = []

# 検査 4(司令塔の指示。2026-09-23 REVISE 4・2026-09-24 の再監査 3)。`<!-- menu: -->`/`<!-- priority: -->` の
# 外で、行動・優先順位を表す言い回しが見つかったら落とす。
ACTION_PHRASES = ["してみては", "を目安に", "を選ぶ", "選ぶなら", "1つだけ", "先に", "で指す", "を混ぜる", "候補に入れ"]

MENU_TAG_RE = re.compile(r"<!--\s*menu:\s*(M\d+)\s*-->")
PRIORITY_TAG_RE = re.compile(r"<!--\s*priority:\s*(M\d+)\s*-->")

# 検査 7(局面の参照)。`<!-- pos: G/P 付録N -->` の印。POS_TAG_RE は印全体(中身を素通りで拾う)、
# POS_INNER_RE は中身が「G/P 付録N」(または付録 3 だけの「G/P 付録N <組>」。2026-09-25、凍結の例外 7b)の
# 形かどうかを見る(空白は MENU_TAG_RE と同程度に寛容: `/` の前後・「付録」の前後の空白を許す)。第 4 群
# (`<組>`)は「付録N」の後に 1 個以上の空白を挟んだ残り全部(組のラベル自体に空白を含みうる ― 「3 分」
# 「10 分」等。前後の空白は POS_TAG_RE 側の `\s*` と `\s+` の消費で既に落ちているが、`check_pos_tags` 側でも
# 念のため strip する)で、無ければ None。中身が POS_INNER_RE に合わなければ「形が崩れている」として落とす。
POS_TAG_RE = re.compile(r"<!--\s*pos:\s*(.*?)\s*-->")

# 検査 (x)(本編の数の id 照合。段 `exit-gate`。2026-09-30)の印 `<!-- agg: <集計の id> -->`。
# **印の文法はこの 1 か所**(`menu`・`pos`・`sec` と同じ家族。同じ規則を 2 か所に置かない ― P-185 の教訓)。
# **この定数を足しただけで、検査 1〜7 の判定は変えていない。**
# ただし下の `scan_numbers` で**印の中の数字を数の主張として見ない**ようにする ―
# 集計の id は数字を含みうる(`repo.top1Drop…` の「1」)。いまの id の数字は 1 桁で
# `SMALL_NUMBER_MAX = 9` の床に隠れるが、**2 桁を含む id が来たら偽の苦情になる**(実測で確かめた)。
AGG_TAG_RE = re.compile(r"<!--\s*agg:\s*(.*?)\s*-->")
# **顧客の問いの答えの印**(⑧ の検査 (x)。2026-10-01)。`<!-- ans: qN status -->`。
# **印の文法はこのファイルの 1 か所**(`exit_gate_test.test_x11` が門の側に写しが無いことを見る)。
# `q12` のような 2 桁の id が来ると数の主張として拾われるので、`scan_numbers` で覆う。
ANS_TAG_RE = re.compile(r"<!--\s*ans:\s*(q\d+)\s+(\S+?)\s*-->")
# **本編の印の家族の一覧**(門の数え方の束。2026-10-05。`docs/PLAN_GATE_COUNTING_2026-10-05.md` G-1)。
# 印は**印字されない**(reportlab が知らないタグとして捨てる。P-123)。だから「顧客に出る字の数」を
# 数える門は、この家族を剥いてから数える。**一覧は文法と同じこのファイルの 1 か所**。
# `scan_numbers` の 3 行(pos・agg・ans を空白に置き換える)は触っていない ― 2 か所に並ぶことは既知事項(計画 §5)。
MARK_TAG_RES = (MENU_TAG_RE, PRIORITY_TAG_RE, POS_TAG_RE, AGG_TAG_RE, ANS_TAG_RE)


def strip_marks(text):
    """本編の印(`MARK_TAG_RES` の家族)を**全部取り除いた**字。顧客に出る字の数を数える側が使う。"""
    for tag_re in MARK_TAG_RES:
        text = tag_re.sub("", text)
    return text


POS_INNER_RE = re.compile(r"^(\d+)\s*/\s*(\d+)\s*付録\s*(\d+)(?:\s+(.+))?$")

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
        self.whatif_data_now_paths = []
        self.whatif_v2_dirs = []
        self.read_dirs = []
        self.type_summary_paths = []
        self.whatif_pdf_paths = []
        self.direct_paths = []
        self.time_cause_paths = []
        self.time_search_paths = []
        self.prose_paths = []
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
        if flag == "--whatif-data-now":
            args.whatif_data_now_paths.append(argv[i + 1])
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
        if flag == "--direct":
            args.direct_paths.append(argv[i + 1])
            i += 2
            continue
        if flag == "--time-cause":
            args.time_cause_paths.append(argv[i + 1])
            i += 2
            continue
        if flag == "--time-search":
            args.time_search_paths.append(argv[i + 1])
            i += 2
            continue
        if flag == "--prose":
            args.prose_paths.append(argv[i + 1])
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
    # 局番号は組ごとに 1 から振られる(組をまたいで衝突しうる)ため、`--prose` は今回の組の 1 本だけ
    # (付録 1 は今回の組の本編だけが納品される)。2 本以上渡すと衝突する局面まで検査 7 を通してしまう
    # (2026-09-25 の直し)。
    if len(args.prose_paths) > 1:
        raise CheckAnswerError("--prose は今回の組の 1 本だけ(付録 1 は今回の組の本編だけが納品される)")
    # 局番号は組ごとに 1 から振られる(組をまたいで衝突しうる)ため、`--whatif-data-now`(検査 7・付録 2 の
    # 材料)は今回の組の 1 本だけ(付録 2 は今回の組のデータだけが納品される)。`--prose` と同じ流儀
    # (2026-09-25、凍結の例外 7a)。
    if len(args.whatif_data_now_paths) > 1:
        raise CheckAnswerError("--whatif-data-now は今回の組の 1 本だけ(付録 2 は今回の組のデータだけが納品される)")
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
        # ANSWER-M1(docs/STEP_ANSWER_PLAN_2026-09-23.md §7.2)。古い patient(欄が無い)は 0 として扱う
        # (M1 の条件は「≥」判定なので、0 なら不成立のまま。他の検査には影響しない)。
        mid_over = phase_spent.get("midOver") or {}
        self.mid_over_games = mid_over.get("games", 0)
        self.mid_over_over = mid_over.get("over", 0)
        self.mid_over_over_and_time_up_loss = mid_over.get("overAndTimeUpLoss", 0)
        self.ahead_loss = ahead_loss_numbers(self.raw.get("findings") or [])
        # M9(docs §8.2、ANSWER-MENU2)。`perGame` が無い古い patient は空のまま(M9 は不成立になる)。
        per_game = phase_spent.get("perGame") or []
        self.time_up_loss_mid_secs = [g["midSec"] for g in per_game if g.get("timeUpLoss") and g.get("midSec") is not None]


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
        # ANSWER-M1(§7.2)。分子・分母を別々に合算する(他の欄と同じ)。
        self.mid_over_games = sum(f.mid_over_games for f in files)
        self.mid_over_over = sum(f.mid_over_over for f in files)
        self.mid_over_over_and_time_up_loss = sum(f.mid_over_over_and_time_up_loss for f in files)
        # M9(docs §8.2、ANSWER-MENU2)。`lib/answerMenu.ts` 冒頭のコメントと同じ実装担当の判断:
        # `time_up_loss_mid_secs` はファイルの順に連結、`other_games_mid_median` は代表ファイル(primary。
        # 上の phase_spent_other_mid と同じファイル)の中央値を使う。
        self.time_up_loss_mid_secs = [sec for f in files for sec in f.time_up_loss_mid_secs]
        self.other_games_mid_median = primary.phase_spent_other_mid


def combined_groups_of(patient_files):
    by_tag = {}
    for f in patient_files:
        if f.tag is None:
            continue
        by_tag.setdefault(f.tag, []).append(f)
    return {tag: CombinedGroup(tag, files) for tag, files in by_tag.items()}


# ==================== M4: 側の一致(司令塔の指示。2026-09-23 REVISE 2・2026-09-24 の再監査 2) ====================


# **「側が逆」の定義**(`lib/type.ts` の `sideBucketOf` と同じ。2026-09-29)。
# `sideBucketOf` は (1) どちらかが `none` なら `eitherNone`、(2) 交われば `same`、
# (3) top1 攻め × 実戦 自玉側 → `top1AttackActualDefense`、(4) その逆 → `top1DefenseActualAttack`。
# `isOppositeSide` は (3)(4) だけを真とする。**`both` は必ず交わるので逆にならない。**
# だから真になる組は**ちょうど 2 通り**である。
OPPOSITE_SIDE_PAIRS = (("attack", "defense"), ("defense", "attack"))


def is_opposite_side(top1_side, actual_side):
    """第 1 候補と実戦の側が逆か(`lib/timeCause.ts` の `isOppositeSide` と同じ判定)。"""
    return (top1_side, actual_side) in OPPOSITE_SIDE_PAIRS


def side_match_of(whatif_v2_dirs):
    """whatif-v2 jsonl(複数フォルダ)の position 行(kind="position", scenes.fork が true)から、
    第 1 候補の側(candidates[0].side)が「攻め」「守り」ちょうど 1 つだった局面だけを分母にし
    (「両方」は分母に入れない。非対称)、実戦の側(actualSide)が同じ側(both を含む)なら分子に数える。"""
    attack_n = attack_collapsed = 0
    defense_n = defense_collapsed = 0
    fork_total = 0
    # **側が逆だった局面(長考の絞りなし)**(2026-09-29。③ の比べる相手)。
    # **同じ走査の中で数える** ― 別の関数で数え直せば、同じ言葉に 2 つの分母が付く(P-156 の家族)。
    opposite = 0
    # **局面ごとの側**(2026-09-29。P-164 の項目 3 ― 盤の候補に「どの分数に入るか」の印を付ける)。
    # **鍵は `(kifuId, displayPly)`。`sfen` では結合しない** ― 実物の 404 行で `sfen` の一意は 403 で、
    # **重複した 1 件は第 1 候補の側が `defense` と `none` で食い違う**(実測)。
    # `sfen` で結合すると**印が 2 通りになる局面**ができ、どちらを書いても断定になる。
    # `kifuId` は `whatif-v2` のファイル名の語幹(実物で `direct_answers` の `kifuId` と 25 / 25 一致)。
    #
    # **数え直さない。****同じ走査の中で集めるので、合算と局面ごとが食い違う道が無い**
    # (別の関数で数え直せば、同じ言葉に 2 つの分母が付く。P-156 の家族)。
    rows = {}
    for d in whatif_v2_dirs:
        for path in sorted(glob.glob(os.path.join(d, "*.jsonl"))):
            kifu_id = os.path.splitext(os.path.basename(path))[0]
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
                    key = (kifu_id, row.get("displayPly"))
                    # **同じ鍵が 2 度来たら、その鍵の印を捨てる**(断定しない)。
                    # 実物では起きない(404 行 → 404 個の鍵)が、起きたときに黙って片方を採らない。
                    rows[key] = None if key in rows else {"top1Side": top1_side,
                                                          "actualSide": actual_side}
                    if is_opposite_side(top1_side, actual_side):
                        opposite += 1
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
        # **側が逆だった分かれ道(全部)**。分母は**第 1 候補の側が 1 つだった分かれ道**
        # (攻め + 自玉側)― 「両方」「どちらでもない」は逆になりえないので分母にも入れない。
        # **長考で絞った 5 / 33 とは分母の出どころが違う**(33 は「両方」「どちらでもない」も含む
        # 「長考かつ分かれ道」の数)。**率で並べない。**
        "opposite": {"numerator": opposite, "denominator": attack_n + defense_n},
        "rows": rows,
    }


# ==================== 側の語(P-185。2026-09-29) ====================
# **同じ側が冊子の中で 2 通りの語になっていた**(批評席 (a) が 6 周目に実物で挙げた) ―
# 本編は「自玉側」20 件・「守り」0 件、付録 3 は「守り」3 件・「自玉側」0 件。
# 本編と付録を見比べる作りなので、**同じものが違う語で出ると同じものと思えない**(P-176 の家族)。
# **測った(`ast` で「表の中」と「文の中」を分けた)**: 鍵 → 語の**対応表**は **5 か所**あった ―
# ここ(本編)・`render_direct.SIDE_JP`(付録 3)・`render_time_cause.VALUE_LABELS` の 2 欄(付録 4)・
# `fig1.SIDE_SHORT`(本編の図)・`exit_candidates.REPRO_KINDS` の 2 行(候補一覧の言い方)。**5 つとも寄せた。**
#
# **文の中の「守り」は残っている**(独立監査の REVISE (c)。2026-09-29)―
# `render_whatif.py`(付録 2)は**顧客に出うる文字列が 5 か所**(ほかに docstring 1・`#` コメント 2 ―
# 行で grep すると 8 行になる。監査と数が違ったので `ast` で内訳を出した)、`answer_facts.py`(8_B)は 3 か所。
# **触らない理由**: (1) どちらも**却下済みの 6 冊形の材料**で、
# 承認済みの 30p 形(`exit_index.COVER_SECTIONS` = 付録 1・付録 3)には束ねられない。
# (2) **文の中の語は表では覆えない** ― 同じ理由で `fig1.STEPS`・承認済みの行動の文・`OPPOSITE_ALL_NAME` も触らない。
# **線は「表は寄せる・文は触らない」**。残りは既知事項 P-185 の行に書いた(次に 6 冊形を使うなら、そこから始める)。
#
# **語は「自玉側」に統一**(司令塔の決定 2026-09-29)。理由: **承認済みの行動の文**
# (`lib/answerMenu.ts` の `actionCore`)が「攻めの候補と自玉側の候補を…」と持っているので、
# 承認済みの文を変えるのではなく、**付録の側を寄せる**。
#
# **ここが 1 か所。**4 つの鍵を持ち、**2 鍵しか要らない側は下の view を引く**
# (`SIDE_LABEL_JP` ― M4 の分数は「両方」「どちらでもない」を分母に入れないので 2 鍵で足りる)。
# `both`・`none` の語も 1 か所にある(別に書くと、片側だけ直して 2 通りに戻る)。
SIDE_JP = {"attack": "攻め", "defense": "自玉側",
           "both": "攻め・自玉側両方", "none": "どちらでもない"}

# M4 の分数の側(`m4_fractions` の `label` と同じ語)。**写しを作らない** ― 上の表の 2 鍵の view。
SIDE_LABEL_JP = {k: SIDE_JP[k] for k in ("attack", "defense")}


def side_match_mark_of(side_match, kifu_id, display_ply):
    """その局面が **M4 の分数のどこに入るか**。入らなければ `None`。

    返り値 = `{"label": "攻め" | "自玉側", "inNumerator": bool}`。

    **分母に入らない局面には印を付けない**(第 1 候補の側が「両方」または「どちらでもない」もの ―
    実物の 103 局面のうち 35 件)。**「分母に入らない」と書くと、読者は「関係が無い」と読む**が、
    その局面は分かれ道としては在る。**言えることだけを言う。**
    """
    if side_match is None:
        return None
    row = (side_match.get("rows") or {}).get((kifu_id, display_ply))
    if not row:
        return None
    label = SIDE_LABEL_JP.get(row["top1Side"])
    if label is None:
        return None
    same = row["actualSide"] in (row["top1Side"], "both")
    return {"label": label, "inNumerator": bool(same)}


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


# ==================== 付録 3(ANSWER-DIRECT): direct_answers.json・final_positions.json(司令塔の指示。
#   docs/STEP_ANSWER_PLAN_2026-09-23.md §9.2「数の照合」) ====================


def direct_answers_group_counts(answers):
    """`direct_answers.json` の `answers` 配列(局面ごと 1 件)から、組(`group`。「3 分」「10 分」等)ごとの
    件数を数える(検査 1 の登録済みの組 (v))。"""
    counts = {}
    for a in answers:
        g = a.get("group")
        counts[g] = counts.get(g, 0) + 1
    return counts


def direct_materials_of(direct_paths):
    """`--direct` で渡した JSON(`direct_answers.json`・`final_positions.json`、どちらも可。複数可)から、
    検査 1 の材料を作る。渡された JSON の中身の `kind`(`directAnswers.ts`/`finalPositions.ts` の出力そのまま:
    `"direct_answers"`/`"final_positions"`)で見分ける。1 つも無ければ None(既存の材料は増えない)。"""
    direct_answers_list = []
    final_positions_list = []
    for path in direct_paths:
        data = load_json(path)
        kind = data.get("kind")
        if kind == "direct_answers":
            direct_answers_list.append(data)
        elif kind == "final_positions":
            final_positions_list.append(data)
        else:
            raise CheckAnswerError(f"--direct に渡した JSON の kind が分からない({path})")
    if not direct_answers_list and not final_positions_list:
        return None

    total_count = sum(d["counts"]["totalCount"] for d in direct_answers_list)
    total_fork_count = sum(d["counts"]["totalForkCount"] for d in direct_answers_list)
    top1_tag_counts = {}
    actual_tag_counts = {}
    top1_side_counts = {}
    group_counts = {}
    for d in direct_answers_list:
        for k, v in d["counts"]["top1TagCounts"].items():
            top1_tag_counts[k] = top1_tag_counts.get(k, 0) + v
        for k, v in d["counts"]["actualTagCounts"].items():
            actual_tag_counts[k] = actual_tag_counts.get(k, 0) + v
        for k, v in d["counts"]["top1SideCounts"].items():
            top1_side_counts[k] = top1_side_counts.get(k, 0) + v
        for g, n in direct_answers_group_counts(d["answers"]).items():
            group_counts[g] = group_counts.get(g, 0) + n

    return {
        # 単独の数(検査 1)の材料に足すための元データ(collect_numbers の再帰走査にかける)。
        "raw": direct_answers_list + final_positions_list,
        # 登録済みの組(i)〜(v)を作るための集計(直接ここで組む ― materials["direct"] としてそのまま使う)。
        "totalCount": total_count,
        "totalForkCount": total_fork_count,
        "top1TagCounts": top1_tag_counts,
        "actualTagCounts": actual_tag_counts,
        "top1SideCounts": top1_side_counts,
        # (v) 組ごとの数。(vi) 組ごとの「局数」はここに置かない(patient の games と混ざるため。登録しない)。
        "groupCounts": group_counts,
    }


# ==================== 付録 4(STEP TIME-CAUSE): time_cause.json(司令塔の指示。`--direct` と同じ流儀。
#   `lib/timeCause.ts` の `TimeCauseFile`) ====================


def fraction_or_zero(fraction):
    """`TimeCauseFraction | null` を `{numerator, denominator}` にする(無ければ 0/0)。"""
    if fraction is None:
        return {"numerator": 0, "denominator": 0}
    return {"numerator": fraction["numerator"], "denominator": fraction["denominator"]}


def add_fractions(a, b):
    return {"numerator": a["numerator"] + b["numerator"], "denominator": a["denominator"] + b["denominator"]}


class TimeCauseCombinedGroup:
    """同じ `group`(「3 分」「10 分」等)の time_cause グループ(1 つ以上の `--time-cause` ファイルの
    `groups[]` の該当項目)をまとめたもの。`--time-cause` は複数可のため(`--direct` と同じ流儀)、C7・C8 は
    `timeUpLoss`/`other` の分数を、ファイルをまたいでも分子・分母をすべて合算する(司令塔の指示 3(i)
    「合算も」の実装担当の読み: 1 つのグループの中の 2 段〈timeUpLoss/other〉の合算と、複数ファイルの合算の
    どちらも指す)。C9(`rookMarkBreakdown`)は (own, opponent) の組ごとに局数を合算する。"""

    def __init__(self, tag, raw_groups):
        self.tag = tag
        self.games = sum(g["games"] for g in raw_groups)
        self.time_up_loss_games = sum(g["timeUpLoss"]["games"] for g in raw_groups)
        fork = {"numerator": 0, "denominator": 0}
        opposite = {"numerator": 0, "denominator": 0}
        rook_mark_games = {}
        for g in raw_groups:
            fork = add_fractions(fork, fraction_or_zero(g["timeUpLoss"].get("forkFraction")))
            fork = add_fractions(fork, fraction_or_zero(g["other"].get("forkFraction")))
            opposite = add_fractions(opposite, fraction_or_zero(g["timeUpLoss"].get("oppositeSideFraction")))
            opposite = add_fractions(opposite, fraction_or_zero(g["other"].get("oppositeSideFraction")))
            for cell in g["rookMarkBreakdown"]:
                key = (cell["own"], cell["opponent"])
                rook_mark_games[key] = rook_mark_games.get(key, 0) + cell["games"]
        self.fork_fraction = fork  # C7: 長考のうち分かれ道 / 長考の総数
        self.opposite_side_fraction = opposite  # C8: 側が逆 / 長考かつ分かれ道
        self.rook_mark_games = rook_mark_games  # C9: (own, opponent) -> 局数


def time_cause_materials_of(time_cause_paths):
    """`--time-cause` で渡した `time_cause.json`(複数可)から、検査 1 の材料を作る(`direct_materials_of`
    と同じ流儀)。1 つも無ければ None(既存の材料は増えない)。"""
    if not time_cause_paths:
        return None
    raw_list = []
    for path in time_cause_paths:
        data = load_json(path)
        if data.get("kind") != "time_cause":
            raise CheckAnswerError(f"--time-cause に渡した JSON の kind が time_cause でない({path})")
        raw_list.append(data)

    order = []
    by_tag = {}
    for data in raw_list:
        for g in data["groups"]:
            tag = g["group"]
            if tag not in by_tag:
                by_tag[tag] = []
                order.append(tag)
            by_tag[tag].append(g)
    groups = {tag: TimeCauseCombinedGroup(tag, by_tag[tag]) for tag in order}

    return {
        # 単独の数(検査 1)の材料に足すための元データ(collect_numbers の再帰走査にかける)。
        "raw": raw_list,
        # 登録済みの組(i)〜(iv)を作るための集計。
        "groups": groups,
    }


# ==================== 付録 4 の探索(STEP TIME-CAUSE-2): time_cause_search.json(司令塔の指示。`--direct`・
#   `--time-cause` と同じ流儀。`lib/timeSearch.ts` の `SearchResult`) ====================


def rounded_count_of(moves, rate):
    """`moves × rate`(浮動小数点)を四捨五入した整数を返す ― `round(moves × rate)` が `moves × rate` 自身と
    1e-6 以内で一致するときだけ(司令塔の指示 3。一致しなければ None ― 呼び出し側は登録しない)。"""
    raw = moves * rate
    rounded = round(raw)
    if abs(raw - rounded) > 1e-6:
        return None
    return rounded


# ==================== 10 秒以上考えた手のうち分かれ道だった数(2026-09-29。③) ====================
# **なぜ要ったか**: 行動 1 の条件は「10 秒以上考える局面では」なのに、根拠の分数(攻め 65 / 107・
# 自玉側 76 / 132)は**全部の分かれ道**で数えたものだった。批評席は **2・3・4 周目と 3 周続けて**
# 「条件と根拠の母集団が違う」と書いた(人間の判断待ちの項目)。
# **その橋にあたる数は材料に在った** ― `time_cause.json` の per-game の
# `forkAmongLongThink`・`oppositeSideAmongForkLongThink`。**観測として出す**(行動にはしない ―
# 承認済みの表に無い項目を行動にすれば、表の外から行動を作ることになる)。
#
# 【「10 秒以上考えた手」の数は 2 通りある(2026-09-29 に実測)】
# - `time_cause` の `longThinkTotal` の和 = **全部の手**
# - `patient.time.bySpent[3].n` = **崩れを判定できた手だけ**(`countedPairsOf` の手に限る)
# **同じ言い方で並べると、分母の出どころが違う数を比べることになる**(2026-09-24 の教訓)。
# だから下の `name` は**どちらの数かを言う**。
LONG_THINK_NAME = "10 秒以上考えた手(全部)"
LONG_THINK_FORK_NAME = "10 秒以上考えた手のうち、分かれ道だった手"
LONG_THINK_OPPOSITE_NAME = "その分かれ道のうち、第 1 候補と実戦の側が逆だった手"
# **長考で絞らない「側が逆」**(2026-09-29。③ の比べる相手 ― 司令塔の依頼)。
# 5 / 33 だけでは高いか低いかが読めない(M5 で 22 / 531 を出したのと同じ話)。
# **分母の出どころが違う**ので、名前で「長考で絞らない」と言う。
# **単位は「局面」**(この数は攻めの分かれ道と自玉側の分かれ道の合計 ― M4 の 2 つの分母の和なので、
# あちらと同じ単位で言う)。長考の側の数は**棋譜の手**を数えたものなので「手」である。**混ぜない。**
OPPOSITE_ALL_NAME = "第 1 候補の側が 1 つだった分かれ道(長考で絞らない。攻めと自玉側の分かれ道の合計)"
OPPOSITE_ALL_NUMERATOR_NAME = "そのうち実戦が逆の側だった分かれ道"
OPPOSITE_ALL_UNIT = "局面"


def long_think_fork_of(time_cause, group):
    """`time_cause.json` の per-game を**組の中で足す**(組をまたがない)。

    返り値 = `{"longThink": 61, "fork": 33, "oppositeSide": 5}`(実物の値)。
    組に 1 局も無ければ `None`。

    **足した数どうしの筋が通ることを確かめる**(通らなければ落とす。`exit_groups` の総和の見張りと同じ形):
    - `forkAmongLongThink` の分母の和 == `longThinkTotal` の和(どちらも「10 秒以上考えた手」)
    - `oppositeSideAmongForkLongThink` の分母の和 == `forkAmongLongThink` の分子の和(どちらも「分かれ道だった手」)
    **この見張りが無いと、材料の作りが変わったときに黙って別の数を出す。**
    """
    if time_cause is None:
        return None
    games = [g for data in time_cause["raw"] for g in data["games"] if g["group"] == group]
    if not games:
        return None
    long_think = sum(g["longThinkTotal"] for g in games)
    fork_d = sum(g["forkAmongLongThink"]["denominator"] for g in games)
    fork_n = sum(g["forkAmongLongThink"]["numerator"] for g in games)
    opp_d = sum(g["oppositeSideAmongForkLongThink"]["denominator"] for g in games)
    opp_n = sum(g["oppositeSideAmongForkLongThink"]["numerator"] for g in games)
    if fork_d != long_think:
        raise CheckAnswerError(
            f"10 秒以上考えた手の数が合わない(longThinkTotal の和 {long_think} と "
            f"forkAmongLongThink の分母の和 {fork_d})")
    if opp_d != fork_n:
        raise CheckAnswerError(
            f"分かれ道だった手の数が合わない(forkAmongLongThink の分子の和 {fork_n} と "
            f"oppositeSideAmongForkLongThink の分母の和 {opp_d})")
    return {"longThink": long_think, "fork": fork_n, "oppositeSide": opp_n}


def time_search_materials_of(time_search_paths):
    """`--time-search` で渡した `time_cause_search.json`(`timeSearch.ts` の出力。複数可)から、検査 1 の材料を
    作る(`direct_materials_of`・`time_cause_materials_of` と同じ流儀)。1 つも無ければ None(既存の材料は
    増えない)。"""
    if not time_search_paths:
        return None
    raw_list = []
    for path in time_search_paths:
        data = load_json(path)
        if data.get("kind") != "time_cause_search":
            raise CheckAnswerError(f"--time-search に渡した JSON の kind が time_cause_search でない({path})")
        raw_list.append(data)
    return {
        # 単独の数(検査 1)の材料に足すための元データ(collect_numbers の再帰走査にかける。p・longThinkRate は
        # 小数なので round() で 0 になり、単独の数としては実質拾われない ― それでよい〈司令塔の指示 2〉)。
        # 登録済みの組(i)〜(iii)は registered_pairs_of がこの raw を直接読んで作る(`--direct` と同じ流儀:
        # ここでは集計を組まない)。
        "raw": raw_list,
    }


# ==================== 検査 7 の材料: 局面の参照(付録 1〜3。司令塔の指示。docs/STEP_DELIVER1_PLAN_2026-09-25.md
#   §11.7、2026-09-24 の人間の委任。付録 4 は盤が無いため材料を持たない ― 下の `check_pos_tags` を参照) ====================
#   各 `*_positions_of` は、渡されたパスが 1 つも無ければ None を返す(=「材料が渡されていない」。
#   `direct_materials_of`・`time_cause_materials_of` と同じ流儀)。渡されていれば `{(gameNo, ply/手目), …}` の
#   集合を返す(空集合もありうる)。


def prose_positions_of(prose_paths):
    """付録 1(`--prose` の `prose.json`。納品される「2_付録1_形勢が動いた対局」= `render_main.py`
    〈`_head.py + _util.py + _mid.py` の連結、`report-pdf/build.sh` 参照〉が作る)。`--prose` は今回の組の
    1 本だけ(`parse_args` が 2 本以上を拒む)― 局番号は組ごとに 1 から振られ、納品される付録 1 は今回の組の
    本編だけなので、材料も今回の組の 1 本に限る(2026-09-25 の直し。前の組の `prose.json` は今回の納品には
    書かれないため、複数渡す設計だと存在しないファイルを読みに行って落ちる・かつ局番号が衝突していた)。
    `prose.json` の形は `{"<局番号>": {"scenes": [{"type", "ply", "text"}, …], …}, …}`(鍵は文字列 → int に直す)。
    `_mid.py` 133〜143 行は `scenes[]` の各要素を `type == "move"` かそれ以外かで場合分けするが、どちらでも
    盤(`Board(...)`)を描く(133 行 `for s_ in pz["scenes"]:` 以下、135 行 `if s_["type"] == "move":` の
    分岐と、else 側の 141〜142 行の両方に `Board(...)` がある)ため、`type` を問わず `scenes[]` の全件を
    材料にする(`events[]`・`escapeScenes[]` からは作らない ― どちらも `_mid.py` では局面つきで印字されない。
    `escapeScenes` は `allowed_numbers`〈言い換えの数の照合〉でしか読まれない)。"""
    if not prose_paths:
        return None
    positions = set()
    for path in prose_paths:
        try:
            data = load_json(path)
        except FileNotFoundError:
            raise CheckAnswerError(f"--prose のファイルが無い: {path}")
        for key, pz in data.items():
            game_no = int(key)
            for s in pz.get("scenes") or []:
                positions.add((game_no, s["ply"]))
    return positions


def whatif_positions_of(whatif_data_now_paths):
    """付録 2(`--whatif-data-now` の `whatif_report_data.json`)。`games[].representative.displayPly`
    (`render_whatif.py` が `rep["displayPly"]`・`g["gameNo"]` として印字する局面。`representative` が
    無い局〈読み筋が無い等〉はスキップ)。`--whatif-data-now` は今回の組の 1 本だけ(`parse_args` が 2 本以上を
    拒む)― 局番号は組ごとに 1 から振られ、納品される付録 2 は今回の組のデータだけなので、材料も今回の組の
    1 本に限る(2026-09-25 の直し、凍結の例外 7a。全組を受け取る `--whatif-data` は検査 1〈数の照合〉専用で、
    ここでは使わない)。"""
    if not whatif_data_now_paths:
        return None
    positions = set()
    for path in whatif_data_now_paths:
        try:
            data = load_json(path)
        except FileNotFoundError:
            raise CheckAnswerError(f"--whatif-data-now のファイルが無い: {path}")
        for g in data.get("games") or []:
            rep = g.get("representative")
            if rep is not None:
                positions.add((g["gameNo"], rep["displayPly"]))
    return positions


def direct_positions_of(direct):
    """付録 3(`--direct` の `direct_answers.json`・`final_positions.json`)。`direct_materials_of` が既に
    読み込んだ `raw`(渡された JSON そのもの)から、`answers[].gameNo`/`displayPly`(浅い読みの局面)と
    `entries[].gameNo`/`moves`(`render_direct.py` が「{moves} 手で時間切れ」と印字する最終局面)を拾う。
    `direct` が None(`--direct` が 1 つも無い)なら None。

    2026-09-25 の直し(凍結の例外 7b)。付録 3 は 1 冊に全組(3 分の組・10 分の組…)を載せる設計であり、
    「局」の番号は組ごとに 1 から振られるため、単一の `{(gameNo, ply), …}` 集合では組の取り違えを検査できない
    (基準 44 局で 3 分 21 件・10 分 9 件、重なりは 0 件だが潜在)。`answers[].group`/`entries[].group`
    (`lib/directAnswers.ts` の `DirectAnswer.group`・`finalPositions.ts` の生成する `entries[].group`。
    どちらも CLI が決めた組のラベル、例: 「3 分」「10 分」)をキーにした
    `{"<組のラベル>": {(gameNo, ply), …}, …}` を返す。`check_pos_tags` はこの辞書で組の有無・一致を見る。"""
    if direct is None:
        return None
    positions_by_group = {}
    for raw in direct["raw"]:
        if raw.get("kind") == "direct_answers":
            for a in raw.get("answers") or []:
                positions_by_group.setdefault(a["group"], set()).add((a["gameNo"], a["displayPly"]))
        elif raw.get("kind") == "final_positions":
            for e in raw.get("entries") or []:
                positions_by_group.setdefault(e["group"], set()).add((e["gameNo"], e["moves"]))
    return positions_by_group


# 付録 4(`render_time_cause.py`)は盤が 1 枚も無い(表と帯グラフだけ ― `Board(` も sfen も出てこない)ため、
# `*_positions_of` を持たない。`<!-- pos: G/P 付録4 -->` は `check_pos_tags` が常に「付録 4 には盤が無い
# (検査 7)」で落とす(司令塔の指示、2026-09-24)。


# ==================== 行動のメニューの条件判定(`lib/answerMenu.ts` の menuConditionHoldsOf の写し。
#   python は TS を import できないので手で合わせる ― render_front.py の GLOBAL_ALLOWED_NUMBERS と同じ流儀) ====================


def rate_of(bucket):
    if bucket is None or bucket["n"] == 0:
        return None
    return bucket["collapsed"] / bucket["n"]


def m1_holds(materials):
    # ANSWER-M1(docs/STEP_ANSWER_PLAN_2026-09-23.md §7.2)。3 分の組(min3)で timeUpLosses.n ≥ 2 かつ
    # 中盤 1 手あたり 4 秒超の局(midOverOver) ≥ 5。
    min3 = materials["groups"].get("min3")
    if min3 is None or min3.time_up_losses["n"] < 2:
        return False
    return min3.mid_over_over >= 5


def m1_denominator(materials):
    min3 = materials["groups"].get("min3")
    return min3.mid_over_over if min3 is not None else None


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


# ==================== 判定の線(2026-09-29。人間の決定「7 割の線を出す・道具上の仮置きと明記」) ====================
# **値は 1 バイトも変えていない。**リテラルを名前つきの 1 か所へ移しただけである
# (P-152 と同じ型 ― **「判定だけが知っている数」を無くす**)。判定・印字・検査が同じここを読む。
#
# 【なぜ要ったか】批評席 (a) が 3 周続けて「一致率が高いのか低いのか、比べる相手が無い」と書いた。
# **比べる相手は道具の中に在った** ― `m4_holds` の `0.7`、`m5_holds` の「2 つぶん」である。
# 冊子に出ていなかったのは、値が関数の中のリテラルだったからで、材料に無いので印字もできなかった。
#
# 【冊子に出る形の制約(2026-09-29 に実測)】
# - **「7 割」「2 倍」とは書けない。**検査 1 は `RATIO_WORD_RE`(数字 + 倍|割)を
#   「『倍』『割』は使わない」で落とす。だから**線は `0.7`、倍率は「2 つぶん」**と書く。
# - **小数は冊子で初めて出る**(4 周目まで本編・付録に小数は 0 件。fitz で数えた)。
#   検査 1 は小数の**小数点以下を整数として読む**(`0.61` → 61)ので、**`0.7` は両方の桁が
#   `SMALL_NUMBER_MAX`(9)以下だから黙って通る**。**`0.75` のような線に変えると
#   検査 1 が「75 が材料に無い」と言って落ちる**(P-177)。`check_answer_test.py` の
#   `MenuThresholdsTest` がこれを見張る。
MENU_THRESHOLDS = {
    "M4": {"kind": "rate_below", "line": 0.7,
           "what": "攻めと自玉側のどちらの一致率も、この線を下回ること"},
    "M5": {"kind": "times_of_other_rate", "times": 2,
           "what": "長考の直後の崩れ率が、0〜1 秒の崩れ率の 2 つぶん以上であること"},
}
# M5 の線の「比べる相手」。**`m5_holds` が見ている `by_spent[0]` そのもの**。
THRESHOLD_OTHER_RATE_NAME = "0〜1 秒で指した手のうち崩れた手"


def menu_threshold_of(item_id, materials):
    """**判定の線と、線と並べる「比べる相手」**(2026-09-29)。

    `MENU_THRESHOLDS` に無い項目は `None`(線を冊子に出さない項目)。
    **判定と同じ表・同じ材料から作る** ― 別に書けば、冊子の線と判定の線がずれる。
    """
    spec = MENU_THRESHOLDS.get(item_id)
    if spec is None:
        return None
    out = dict(spec)
    if spec["kind"] == "times_of_other_rate":
        g = primary_group(materials)
        if g is None or not g.by_spent:
            return None
        other = g.by_spent[0]
        if other is None or other["n"] == 0:
            return None
        out["other"] = {"name": THRESHOLD_OTHER_RATE_NAME, "unit": "手",
                        "numerator": other["collapsed"], "denominator": other["n"]}
    return out


def m4_holds(materials):
    sm = materials["sideMatch"]
    if sm is None:
        return False
    attack_rate = rate_of(sm["attack"])
    defense_rate = rate_of(sm["defense"])
    if attack_rate is None or defense_rate is None:
        return False
    line = MENU_THRESHOLDS["M4"]["line"]
    return attack_rate < line and defense_rate < line


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
    return quick_rate >= zero_to_one_rate * MENU_THRESHOLDS["M5"]["times"]


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


def m9_holds(materials):
    # M9(docs §8.2、ANSWER-MENU2)。3 分の組(min3)で timeUpLosses.n ≥ 2 かつ、時間で負けた局のすべての
    # midSec が otherGamesMidMedian を超える(lib/answerMenu.ts の m9Holds と同じ実装担当の判断)。
    g = materials["groups"].get("min3")
    if g is None or g.time_up_losses["n"] < 2:
        return False
    if g.other_games_mid_median is None or not g.time_up_loss_mid_secs:
        return False
    return all(sec > g.other_games_mid_median for sec in g.time_up_loss_mid_secs)


def m9_denominator(materials):
    g = materials["groups"].get("min3")
    return g.time_up_losses["n"] if g is not None else None


MENU_HOLDS = {"M1": m1_holds, "M2": m2_holds, "M3": m3_holds, "M4": m4_holds, "M5": m5_holds, "M6": m6_holds, "M7": m7_holds, "M8": m8_holds, "M9": m9_holds}
# ==================== 分数の定義(判定・根拠の 1 行・答え合わせの表が同じ 1 か所を読む) ====================
# **写しを 2 か所に持たない。**判定(`MENU_HOLDS`)が見る分数と冊子に印字する分数がずれると、
# **「いまの値」として判定が見ていない数が出る** ― 2026-09-29 の実物で起きた
# (`M4` の行が `forkTotal` = 404 を出していたが、判定は `attack`・`defense` の分数で見ていた。P-152)。
#
# **名前は判定関数が数えている中身をそのまま日本語にしたもの。**将棋の言葉を足していない。
# `M5` の言い方は `answer_facts.bullet_8` の承認済みの文から取った(「直前の自分の手が 10 秒以上で、この手は 4 秒以内」)。
# **`answerMenu.ts` の `verifyName` は触らない**(承認済みの表の文を変えない)。
# M4/M5/M6 はここから文を作り、他の項目は `verifyName` をそのまま使う(2026-09-29 の司令塔の判断 (A))。
#
# `label` は値を並べるときの短い見出し(1 項目が 2 本の分数を持つとき要る)。1 本だけなら空。


# 分数の欄(2026-09-29 に `unit` と `unitMismatch` を足した)。
#
# - `unit`: **分子と分母が何を数えたものか**(「局面」「手」)。分母の出どころの表に出す行の単位。
# - `unitMismatch`: **分子と分母の単位が違うとき、その理由**(無ければ鍵ごと無い)。
#   **P-165 を測ってここに書いた** ― 「その数は何を数えたものか」は分子と分母の**両方**について
#   測らなければならない。同じ行に並んでいても単位は同じとは限らない。
def m4_fractions(materials):
    sm = materials["sideMatch"]
    if sm is None:
        return None
    return [
        {"label": "攻め", "unit": "局面",
         "name": "第 1 候補が攻めの手だった分かれ道のうち、実戦も攻めの手だった局面",
         "numerator": sm["attack"]["collapsed"], "denominator": sm["attack"]["n"]},
        {"label": "自玉側", "unit": "局面",
         "name": "第 1 候補が自玉側の手だった分かれ道のうち、実戦も自玉側の手だった局面",
         "numerator": sm["defense"]["collapsed"], "denominator": sm["defense"]["n"]},
    ]


def m5_fractions(materials):
    g = primary_group(materials)
    if g is None:
        return None
    q = g.after_long_think_quick
    return [{"label": "", "unit": "手",
             "name": "直前の自分の手が 10 秒以上で、この手は 4 秒以内だった手のうち、崩れた手",
             "numerator": q["collapsed"], "denominator": q["n"]}]


def m6_fractions(materials):
    r = materials["readCombined"]
    if r is None:
        return None
    # **分子は局面の数・分母は印の組の数**(P-165。2026-09-29 に `read` の局面行から数え直して分かった)。
    # `sacrificeRowTotal` は `tagCrossTable["sacrifice"]` の**行の合計**で、
    # **第 1 候補が捨て駒だった局面は 107**、137 はその 107 局面の「実戦の手に付いた印」の総数である
    # (印が 2 つ以上の局面は何度も数えられ、印が 1 つも無い 18 局面は分母に入っていない)。
    # **分母を局面数に直すと判定が変わる**(50/137 = 0.365 は閾値 0.4 を通るが 50/107 = 0.467 は通らない)ので、
    # **判定は動かさない**(判断的知識 ― 人間の承認事項として上げた)。
    # ここには**測った事実だけを置く** ― 分母の出どころの表には出さない(単位の違う数を
    # 「局面」として並べることになるため)。
    return [{"label": "", "unit": "印の組",
             # **既知事項の番号(P-165)をこの文に書かない。**この文は候補の md の
             # **書き手への注に入る**ので、`165` が「データに無い数」として検査 1 に当たる
             # (実測 2026-09-29。**消せば消える苦情を書き手の一覧に混ぜない**)。
             "unitMismatch": "分子は局面の数・分母は印の組の数(人間の承認待ち)",
             "name": "第 1 候補が駒を捨てる手だった分かれ道のうち、実戦も駒を捨てる手だった局面",
             "numerator": r["sacrificeDiagonal"], "denominator": r["sacrificeRowTotal"]}]


MENU_FRACTIONS = {"M4": m4_fractions, "M5": m5_fractions, "M6": m6_fractions}


def menu_fractions(item_id, materials):
    """その項目の分数(無ければ `None`)。**`MENU_FRACTIONS` に無い項目は `None`** ― 呼ぶ側が `verifyName` に落ちる。"""
    fn = MENU_FRACTIONS.get(item_id)
    return None if fn is None else fn(materials)


MENU_DENOMINATOR = {"M1": m1_denominator, "M2": m2_denominator, "M3": m3_denominator, "M4": m4_denominator, "M5": m5_denominator, "M6": m6_denominator, "M7": m7_denominator, "M8": m8_denominator, "M9": m9_denominator}


# ==================== 答え合わせの下限(verifyGate。docs §8.1、ANSWER-MENU2) ====================


def m1_verify_gate_holds(materials):
    min3 = materials["groups"].get("min3")
    if min3 is None or not min3.mid_over_over:
        return False
    return min3.mid_over_over_and_time_up_loss / min3.mid_over_over >= 0.5


MENU_VERIFY_GATE_HOLDS = {"M1": m1_verify_gate_holds}


def menu_verify_gate_holds(item_id, materials, menu_items_by_id):
    """`answer_menu.json` の該当項目に `verifyGate` が無ければ true(§8.4 の指示どおり)。"""
    item = menu_items_by_id[item_id]
    if item.get("verifyGate") is None:
        return True
    fn = MENU_VERIFY_GATE_HOLDS.get(item_id)
    if fn is None:
        raise CheckAnswerError(f"verifyGate はあるが判定関数が無い: {item_id}")
    return fn(materials)


# ==================== 検査 1: 数の照合(登録済みの組。司令塔の指示 2026-09-23 REVISE 6) ====================


def direct_answers_of(direct):
    """材料の `direct` から `answers[]` を引く(組をまたいで全部)。**取り出し方は 1 か所**
    ― `exit_candidates.answers_of` はここへ委譲する(2026-09-29。写しを持たない)。"""
    out = []
    for raw in (direct or {}).get("raw") or []:
        if raw.get("kind") == "direct_answers":
            out.extend(raw.get("answers") or [])
    return out


def top1_actual_cross(direct, tag):
    """**第 1 候補の印が `tag` だった分かれ道**と、そのうち**実戦の手も同じ印だった / そうでなかった**数。

    局面と局の両方を返す。**材料は `direct`**(= 本編 p1 の数と同じ出どころ)なので、
    分母は p1 の「第 1 候補が駒を打つ手だった局面が 54(22 局)」と同じ数になる。
    **`read` の `tagCrossTable` は使わない** ― あちらの分母は読んだ局面の数(実物で 170)で、
    **p1 の 54 と並べると同じ言葉に 2 つの分母が付く**(2026-09-29 に測って避けた。「分母の出どころを書く」の家族)。

    **数えるだけで、目的を書かない**(規則 8 (3))。「打たない」「見落とし」「候補に入れない」は言わない。
    """
    answers = direct_answers_of(direct)
    hit = [a for a in answers if (a.get("top1Tags") or {}).get(tag)]
    both = [a for a in hit if (a.get("actualTags") or {}).get(tag)]
    other = [a for a in hit if not (a.get("actualTags") or {}).get(tag)]

    def games(rows):
        return len({a["gameNo"] for a in rows})

    return {"positions": len(hit), "games": games(hit),
            "bothPositions": len(both), "bothGames": games(both),
            "otherPositions": len(other), "otherGames": games(other)}


# **`drop` だけ**(2026-09-29。測って決めた)。
# `sacrifice` も同じ形で数えられるが、**`M6` の答え合わせの分数と分母が違う** ―
# `direct` から数えると「第 1 候補が捨てる手 41 局面のうち実戦も捨てる手 22」、
# `read` の `tagCrossTable` から数えると「137 のうち 50」。**同じ言葉に 2 つの分母が付く。**
# 「分母の出どころを書く」の家族(`compare-rates-need-same-base`)なので、**並べない。**
# `drop` は承認済みの表に対応する行動が無いので、**答え合わせの分数と衝突しない。**
CROSS_TAGS = ("drop",)


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
        # ANSWER-M1(§7.2)。
        add(f.mid_over_over, f.mid_over_games)
        add(f.mid_over_over_and_time_up_loss, f.mid_over_over)

    for g in materials["groups"].values():
        add(g.time_up_losses["n"], g.time_up_losses["m"])
        for bucket in g.by_spent:
            add(bucket["n"], bucket["collapsed"])
        add(g.by_spent_total["n"], g.by_spent_total["collapsed"])
        add(g.after_long_think_any["n"], g.after_long_think_any["collapsed"])
        add(g.after_long_think_quick["n"], g.after_long_think_quick["collapsed"])
        add(g.mid_over_over, g.mid_over_games)
        add(g.mid_over_over_and_time_up_loss, g.mid_over_over)
        # M9(docs §8.2、ANSWER-MENU2)。「時間負けのうち中央値超え / 時間負け」。
        if g.other_games_mid_median is not None:
            exceed_count = sum(1 for sec in g.time_up_loss_mid_secs if sec > g.other_games_mid_median)
            add(exceed_count, g.time_up_losses["n"])

    r = materials["readCombined"]
    if r is not None:
        add(r["forkPositionsRead"], r["forkPositionsRead"] - r["firstVisibleNodesNoneCount"])
        add(r["sacrificeRowTotal"], r["sacrificeDiagonal"])
        add(r["opponentReplyMatchesPv"]["matched"], r["opponentReplyMatchesPv"]["measured"])

    # **第 1 候補の印 × 実戦の印の組**(2026-09-29。観測 1 行を印字するために足した)。
    # 分母は「第 1 候補がその印だった局面(局)」、分子は「実戦も同じ印だった / そうでなかった」。
    # **`direct` から数えるので p1 の数と同じ出どころ**(`top1_actual_cross` の docstring)。
    direct_material = materials.get("direct")
    if direct_material:
        for tag in CROSS_TAGS:
            c = top1_actual_cross(direct_material, tag)
            add(c["bothPositions"], c["positions"])
            add(c["otherPositions"], c["positions"])
            add(c["bothGames"], c["games"])
            add(c["otherGames"], c["games"])

    sm = materials["sideMatch"]
    if sm is not None:
        add(sm["attack"]["n"], sm["attack"]["collapsed"])
        add(sm["defense"]["n"], sm["defense"]["collapsed"])

    # 付録 3(ANSWER-DIRECT。§9.2「数の照合」)。(i)〜(v)。(vi) 組ごとの局数は登録しない(patient の games と
    # 混ざるため ― `direct_materials_of` の docstring と同じ判断)。
    direct = materials.get("direct")
    if direct is not None:
        add(direct["totalCount"], direct["totalForkCount"])  # (i) 浅い読みで見えた分かれ道 / 分かれ道
        for n in direct["top1TagCounts"].values():
            add(n, direct["totalCount"])  # (ii) 第 1 候補の印ごとの n / 総数
        for n in direct["actualTagCounts"].values():
            add(n, direct["totalCount"])  # (iii) 実戦の印ごとの n / 総数
        for n in direct["top1SideCounts"].values():
            add(n, direct["totalCount"])  # (iv) 第 1 候補の側ごとの n / 総数
        for n in direct["groupCounts"].values():
            add(n, direct["totalCount"])  # (v) 組ごとの数 / 総数

    # 付録 4(STEP TIME-CAUSE)。(i)〜(iv)。(v) 局ごとの「時期ごとの長考の回数 / 長考の総数」は登録しない
    # (小さい数の偶然一致が増えるため。司令塔の指示)。
    time_cause = materials.get("timeCause")
    if time_cause is not None:
        for g in time_cause["groups"].values():
            add(g.fork_fraction["numerator"], g.fork_fraction["denominator"])  # (i) C7
            add(g.opposite_side_fraction["numerator"], g.opposite_side_fraction["denominator"])  # (ii) C8
            for cell_games in g.rook_mark_games.values():
                add(cell_games, g.games)  # (iii) C9 の 2×2 の各局数 / 組の局数
            add(g.time_up_loss_games, g.games)  # (iv) 時間負けの局数 / 組の局数

    # 付録 4 の探索(STEP TIME-CAUSE-2)。(i)〜(iii)。`--time-search` を複数渡した場合は、ファイルごと(1 回の
    # 探索の実行ごと)に別々の集計として登録する(`--time-cause` の `group` のような合算先の鍵が無いため)。
    time_search = materials.get("timeSearch")
    if time_search is not None:
        for data in time_search["raw"]:
            for cond in list(data["reproduced"]) + list(data["notReproduced"]):
                # (i) 採用候補(再現した組・しなかった組)ごとの discover.longThink/discover.n、
                # validate.longThink/validate.n。
                add(cond["discover"]["longThink"], cond["discover"]["n"])
                add(cond["validate"]["longThink"], cond["validate"]["n"])
            for d in data["depths"]:
                # (ii) 深さごとの adopted/tried・reproduced/adopted・reproduced/tried。
                add(d["adopted"], d["tried"])
                add(d["reproduced"], d["adopted"])
                add(d["reproduced"], d["tried"])
            # (iii) 発見用・検証用それぞれの「長考の数 / 手の数」(長考の数は round(moves × longThinkRate)。
            # 一致しなければ登録しない)。
            add(rounded_count_of(data["discover"]["moves"], data["discover"]["longThinkRate"]), data["discover"]["moves"])
            add(rounded_count_of(data["validate"]["moves"], data["validate"]["longThinkRate"]), data["validate"]["moves"])

            # STEP TIME-CAUSE-3(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §9.1)。崩れ(collapse)の数。
            # 司令塔の指示どおり 4 種類だけを登録する(局ごとの分数のような小さい数は登録しない)。
            all_conditions = list(data["reproduced"]) + list(data["notReproduced"]) + list(data["collapseSearch"]["reproduced"]) + list(data["collapseSearch"]["notReproduced"])
            for cond in all_conditions:
                # (iv) 各条件(長考の探索・崩れの探索の両方)の discover.collapsed/discover.collapseCounted、
                # validate.collapsed/validate.collapseCounted。
                add(cond["discover"]["collapsed"], cond["discover"]["collapseCounted"])
                add(cond["validate"]["collapsed"], cond["validate"]["collapseCounted"])
            # (v) 全体の崩れ discover.collapsed/discover.collapseCounted、validate.collapsed/validate.collapseCounted。
            add(data["discover"]["collapsed"], data["discover"]["collapseCounted"])
            add(data["validate"]["collapsed"], data["validate"]["collapseCounted"])
            for f in data["factors"]:
                # (vi) 共通因子(部品)ごとの single の分数(発見用・検証用とも。長考の p・崩れの q の両方)。
                add(f["single"]["discover"]["longThink"], f["single"]["discover"]["n"])
                add(f["single"]["validate"]["longThink"], f["single"]["validate"]["n"])
                add(f["single"]["discover"]["collapsed"], f["single"]["discover"]["collapseCounted"])
                add(f["single"]["validate"]["collapsed"], f["single"]["validate"]["collapseCounted"])
                # (vii) inReproduced.depthN / depths[N].reproduced(N = 1・2・3。長考の探索の再現の数)。
                for depth_index, key in ((0, "depth1"), (1, "depth2"), (2, "depth3")):
                    add(f["inReproduced"][key], data["depths"][depth_index]["reproduced"])

            # STEP CAUSE-SEARCH-1(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §11.1 の 6.)。`searches.*`
            # (アウトカムごとの探索。`--outcomes` で絞った場合は渡された鍵だけ)。無ければ(古い形式の
            # JSON)スキップする ― `--time-cause` と同じ「無ければ増えない」流儀。
            searches = data.get("searches", {})
            for outcome, outcome_result in searches.items():
                for cond in list(outcome_result["reproduced"]) + list(outcome_result["notReproduced"]):
                    # (viii) `searches.<outcome>` の各条件の分数(longThink/n・collapsed/collapseCounted・
                    # decisionGap の matched/n)。
                    if outcome == "longThink":
                        add(cond["discover"]["longThink"], cond["discover"]["n"])
                        add(cond["validate"]["longThink"], cond["validate"]["n"])
                    elif outcome == "collapse":
                        add(cond["discover"]["collapsed"], cond["discover"]["collapseCounted"])
                        add(cond["validate"]["collapsed"], cond["validate"]["collapseCounted"])
                    elif outcome == "decisionGap":
                        add(cond["discover"]["matched"], cond["discover"]["n"])
                        add(cond["validate"]["matched"], cond["validate"]["n"])
                for d in outcome_result["depths"]:
                    # (ix) `searches.<outcome>` の深さごとの adopted/tried・reproduced/adopted。
                    add(d["adopted"], d["tried"])
                    add(d["reproduced"], d["adopted"])

            if "decisionGap" in searches:
                for f in data["factors"]:
                    # (x) `byOutcome.decisionGap` の判定に使った、部品単独の decisionGap の分数
                    # (`singleDecisionGap`。発見用・検証用とも)。`longThink`・`collapse` の単独の分数は
                    # 既存の (vi)(`f["single"]`)で登録済み。
                    sdg = f["singleDecisionGap"]
                    add(sdg["discover"]["matched"], sdg["discover"]["n"])
                    add(sdg["validate"]["matched"], sdg["validate"]["n"])

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
    direct = direct_materials_of(args.direct_paths)
    time_cause = time_cause_materials_of(args.time_cause_paths)
    time_search = time_search_materials_of(args.time_search_paths)

    allowed_numbers = set()
    for f in patient_files:
        collect_numbers(f.raw, allowed_numbers)
    for path in args.whatif_data_paths:
        collect_numbers(load_json(path), allowed_numbers)
    for path in args.type_summary_paths:
        collect_numbers(load_json(path), allowed_numbers)
    if direct is not None:
        for raw in direct["raw"]:
            collect_numbers(raw, allowed_numbers)
    if time_cause is not None:
        for raw in time_cause["raw"]:
            collect_numbers(raw, allowed_numbers)
        # 組ごとに合算した数も、単独の数として許す(`--time-cause` を複数渡したときの合算値。
        # patient の CombinedGroup と同じ考え方)。
        for g in time_cause["groups"].values():
            collect_numbers(
                {
                    "games": g.games,
                    "timeUpLossGames": g.time_up_loss_games,
                    "forkFraction": g.fork_fraction,
                    "oppositeSideFraction": g.opposite_side_fraction,
                    "rookMarkGames": list(g.rook_mark_games.values()),
                },
                allowed_numbers,
            )
    if time_search is not None:
        for raw in time_search["raw"]:
            collect_numbers(raw, allowed_numbers)
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
                # ANSWER-M1(§7.2)。
                "midOverGames": g.mid_over_games,
                "midOverOver": g.mid_over_over,
                "midOverOverAndTimeUpLoss": g.mid_over_over_and_time_up_loss,
                # M9(§8.2、ANSWER-MENU2)。
                "timeUpLossMidSecs": g.time_up_loss_mid_secs,
                "otherGamesMidMedian": g.other_games_mid_median,
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

    materials = {"groups": groups, "readCombined": read_combined, "sideMatch": side_match, "direct": direct, "timeCause": time_cause, "timeSearch": time_search}
    pairs = registered_pairs_of(patient_files, materials)
    allowed_numbers |= percent_pool_of(pairs)

    # 検査 7(局面の参照)の材料。渡されなかった付録は鍵が無い(= None。`positions.get(N)` で「材料が渡されて
    # いない」を見分ける)。付録 4 は盤が無いので鍵を持たない(`check_pos_tags` が N==4 を先に特別扱いする)。
    positions = {
        1: prose_positions_of(args.prose_paths),
        2: whatif_positions_of(args.whatif_data_now_paths),
        3: direct_positions_of(direct),
    }

    menu_ids = {item["id"] for item in menu["items"]}
    menu_minn = {item["id"]: item["minN"] for item in menu["items"]}
    menu_items_by_id = {item["id"]: item for item in menu["items"]}

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
        "menuItemsById": menu_items_by_id,
        "reviewedNames": reviewed_shape_names(repo_root),
        "whatifPdfText": whatif_pdf_text,
        "positions": positions,
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


# 単位の無い小さな数は検査 1 の対象外(§2.1 検査 1。実装担当の判断: しきい値 9 で近似)。
SMALL_NUMBER_MAX = 9


def scan_numbers(line, small_max=None):
    """1 行から「文中の数の主張」を拾う。**検査 1 が見るものと同じ規則の 1 か所。**

    `small_max` は「単位の無い小さな数」として単独では見ない上限。既定は `SMALL_NUMBER_MAX`
    (検査 1 の値。**検査 1 の動きは変わらない**)。段 `exit-gate` は **0** を渡す ―
    あちらは「書き手が選んだ数がちょうど 3 つか」を数えるので、**1 桁の数も数に入る**
    (実物の p1 は「6 局」のような 1 桁を含む)。**見落とす側に倒すと、材料に無い 4 つ目の数が
    門をすり抜ける**ので、数える側は上限を持たない。

    切り出した理由(2026-09-29): 段 `exit-gate` が「P1 の数はちょうど 3 つ」を数えるのに、
    **同じ規則が要る**。別に書けば、**門が数える数と検査 1 が見る数が食い違う**道ができる
    (`Board` が 4 実装に散った P-111 と同じ病気)。**判定は 1 つも変えていない** ―
    `check_line_numbers` はこの関数の結果を材料と突き合わせるだけになった。

    返り値 = `(倍割の語があるか, 分数の組 [(a, b, span)], 割合の数 [n], 単独の数 [n])`。
    `倍割の語` が True のときは残りを空で返す(元の `return` と同じ ― その行は数を見ない)。
    """
    # `<!-- pos: G/P 付録N -->` の印の中の数字(検査 7)は、検査 1 の対象から外す(`menu` の印と同じ扱い。
    # 印の全体を空白に置き換えるので、G・P・N のどれも「文中の数の主張」としては見ない)。
    scan_line = POS_TAG_RE.sub(lambda m: " " * len(m.group(0)), line)
    # `<!-- agg: <id> -->` の印(検査 (x))も同じ扱い ― **id の中の数字を文中の数の主張として見ない**
    scan_line = AGG_TAG_RE.sub(lambda m: " " * len(m.group(0)), scan_line)
    scan_line = ANS_TAG_RE.sub(lambda m: " " * len(m.group(0)), scan_line)
    # 日付(YYYY-MM-DD。見出し・作成日の表記)は「文中の数の主張」ではないので対象から外す
    # (実装担当の判断。表題行の「2026-09-24」等が「データに無い数」として誤検知するのを防ぐ。
    # 報告する原文(line)はそのまま、数を探す側だけ日付を消す)。
    scan_line = ISO_DATE_RE.sub(" ", scan_line)
    if RATIO_WORD_RE.search(scan_line):
        return True, [], [], []
    fractions = find_fraction_pairs(scan_line)
    masked = mask_spans(scan_line, [span for _, _, span in fractions])
    percents = [int(m.group(1)) for m in re.finditer(r"(\d+)\s*%", masked)]
    masked_no_percent = re.sub(r"(\d+)\s*%", " ", masked)
    limit = SMALL_NUMBER_MAX if small_max is None else small_max
    plains = [int(m.group(0)) for m in re.finditer(r"\d+", masked_no_percent)
              if int(m.group(0)) > limit]
    return False, fractions, percents, plains


def check_line_numbers(line, ctx, problems, line_no):
    ratio, fractions, percents, plains = scan_numbers(line)
    if ratio:
        problems.append((line_no, "「倍」「割」は使わない(検査 1)", line))
        return
    for a, b, _span in fractions:
        if (a, b) not in ctx["pairs"]:
            problems.append((line_no, f"数の組み合わせが登録済みの組に無い({a}/{b}。検査 1)", line))
    for n in percents:
        if n not in ctx["allowedNumbers"]:
            problems.append((line_no, f"データに無い割合 {n}% が文に出ている(検査 1)", line))
    for n in plains:
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


# ANSWER-MENU2(docs §8.2)。foundInSameData の項目の印の行に必須の句。
FOUND_IN_SAME_DATA_PHRASE = "今回の対局から見つけた読みです"


def check_menu_tags(line, ctx, problems, line_no):
    """検査 4(メニューの印・答え合わせの下限・foundInSameData の句)・検査 5(数が足りなければ言わない)。
    印が成立しているかを返す(検査 4 の除外判定用)。"""
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
            continue
        # ANSWER-MENU2(§8.1)。条件・minN に加えて答え合わせの下限(verifyGate)も満たさなければ落とす。
        if not menu_verify_gate_holds(tag_id, ctx["materials"], ctx["menuItemsById"]):
            problems.append((line_no, f"メニュー {tag_id} の答え合わせの数が下限に届かない(検査 4)", line))
            all_hold = False
            continue
        # ANSWER-MENU2(§8.2)。foundInSameData の項目は、印の行に句が必須。
        item = ctx["menuItemsById"][tag_id]
        if item.get("foundInSameData") and FOUND_IN_SAME_DATA_PHRASE not in line:
            problems.append((line_no, f"メニュー {tag_id} は今回の対局から見つけた読みの句が無い(検査 4)", line))
            all_hold = False
    return all_hold


def check_appendix3_position(g, p, group, positions_by_group, problems, line_no, line):
    """検査 7・付録 3 だけの判定(2026-09-25、凍結の例外 7b)。`positions_by_group` は `direct_positions_of`
    が返す `{"<組>": {(gameNo, ply), …}, …}`(材料が渡されていなければ呼び出し側で None を弾く)。
    材料の組が 2 種類以上なら組の宣言を必須にし(無ければ使える組を並べて落とす)、組ありは (組, G, P) で
    照合する(知らない組の値もここで落ちる)。材料の組が 1 種類(または 0 種類)なら、組の無い宣言は従来どおり
    (G, P) だけで照合し、組がある宣言はその組と一致しなければ同じ理由で落とす。"""
    known_groups = list(positions_by_group.keys())
    if group is None:
        if len(known_groups) >= 2:
            groups_str = " / ".join(known_groups)
            problems.append((line_no, f"付録 3 の宣言に組が無い。材料の組: {groups_str}(検査 7)", line))
            return
        if not any((g, p) in positions for positions in positions_by_group.values()):
            problems.append((line_no, f"局面 {g}/{p} は付録 3 の材料に無い(検査 7)", line))
        return
    if group not in positions_by_group or (g, p) not in positions_by_group[group]:
        problems.append((line_no, f"局面 {g}/{p} は付録 3 の組 {group} の材料に無い(検査 7)", line))


def check_pos_tags(line, ctx, problems, line_no):
    """検査 7(局面の参照)。`<!-- pos: G/P 付録N -->`(付録 3 だけは `<!-- pos: G/P 付録3 <組> -->` も可。
    2026-09-25、凍結の例外 7b)の印(1 行に複数あってよい)ごとに、宣言された (G, P)(・付録 3 は組も)が
    付録 N の材料に実在するかを確かめる。本文は解析しない(印だけを見る)。"""
    for m in POS_TAG_RE.finditer(line):
        inner = m.group(1)
        inner_m = POS_INNER_RE.match(inner)
        if inner_m is None:
            problems.append((line_no, f"局面の参照の形が崩れている({inner}。検査 7)", line))
            continue
        g, p, n = int(inner_m.group(1)), int(inner_m.group(2)), int(inner_m.group(3))
        group = inner_m.group(4)
        if group is not None:
            group = group.strip()  # 前後の空白を除いて比べる(実装担当の判断。POS_TAG_RE 側で既に落ちているはずだが念のため)
        # 付録 4(render_time_cause.py)には盤が 1 枚も無い(表と帯グラフだけ)ため、材料の有無にかかわらず
        # 常に落とす(司令塔の指示、2026-09-24。形の崩れ・知らない付録番号とは別のメッセージにする)。組が
        # 書かれていれば「組は書かない」を先に返す(付録 1・2・4 は組を持たない。2026-09-25、凍結の例外 7b)。
        if n == 4:
            if group is not None:
                problems.append((line_no, "付録 4 の宣言に組は書かない(検査 7)", line))
            else:
                problems.append((line_no, "付録 4 には盤が無い(検査 7)", line))
            continue
        if n not in (1, 2, 3):
            problems.append((line_no, f"局面 {g}/{p} は知らない付録 {n} を指している(検査 7)", line))
            continue
        if n in (1, 2):
            if group is not None:
                problems.append((line_no, f"付録 {n} の宣言に組は書かない(検査 7)", line))
                continue
            positions = ctx["positions"].get(n)
            if positions is None:
                problems.append((line_no, f"付録 {n} の材料が渡されていない(検査 7)", line))
                continue
            if (g, p) not in positions:
                problems.append((line_no, f"局面 {g}/{p} は付録 {n} の材料に無い(検査 7)", line))
            continue
        # n == 3(付録 3。2026-09-25 の直し、凍結の例外 7b)。
        positions_by_group = ctx["positions"].get(3)
        if positions_by_group is None:
            problems.append((line_no, "付録 3 の材料が渡されていない(検査 7)", line))
            continue
        check_appendix3_position(g, p, group, positions_by_group, problems, line_no, line)


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
        check_pos_tags(line, ctx, problems, line_no)
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
