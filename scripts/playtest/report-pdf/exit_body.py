# -*- coding: utf-8 -*-
# STEP CUSTOMER-EXIT の段 `exit-render` の**後半**: **本編の md → 本人用・見本用の PDF。**
# (前半 ― 付録のページ抜きと索引の束ね ― は `exit_render.py`。)
#
# 【この道具がやること】
# 1. `check_answer.check_answer()` を先に通す(落ちた文があれば描かない ― `render_answer.py` と同じ順)
# 2. 本編の `<!-- pos: 局/手 付録N [組] -->` の印を読み、**その場所に盤を差し込む**
# 3. **本人用**の PDF を作る
# 4. **見本用** = 本人用から**対応表の節が載ったページを抜いたもの**(正本 §1・§7)
#
# 【新しい判定・新しい文法を 1 つも作らない】
# - 印の文法: `check_answer.POS_TAG_RE` / `POS_INNER_RE`(`exit_render.py` と同じものを使う)
# - 印が材料に実在するかの照合: **`check_answer.check_answer()` の検査 7 がすでにやっている。**
#   この道具は照合を持たず、**検査 7 が通した印を引けなかったら落ちる**(食い違ったら道具の不具合なので黙らない)
# - 盤に渡す値の判断: `board_spec.py`(`_mid.py`・`render_direct.py` と同じ 1 か所)
# - 対応表の節の見分け: `check_structure.py` の `SECTIONS`・`MAPPING_ROLE`(門と同じ定数)
# - 組版(見出し・箇条書き・表・太字): `render_answer.build_story()` をそのまま呼ぶ
#
# 【印を明示的に取り除く(P-123)】`<!-- pos: -->` が PDF に出ないのは**偶然**である。
# `render_answer.build_story` は `inline_markup` で `MENU_TAG_RE`・`PRIORITY_TAG_RE` だけを取り除き、
# `pos` の印は `re.split(r"(<[^>]*>)")` を通って**reportlab が知らないタグとして黙って捨てられている**。
# 書式が変わればそのまま顧客の文に出る。**だからこの道具は自分で取り除く。**
#
# 使い方:
#   REPORT_DATA_DIR=<sfens.json・prose.json・patient_report_data.json のあるフォルダ>[,…] \
#     python3 -X utf8 exit_body.py <本編.md> --out-person <本人用.pdf> --out-sample <見本用.pdf> \
#     [check_answer.py と同じ引数…]
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import board_spec as BS          # noqa: E402  ― 盤に渡す値の判断は 1 か所
import check_answer as CA        # noqa: E402
import check_structure as CS     # noqa: E402


class ExitBodyError(Exception):
    pass


# **目印。**制御文字 `\x00` を使うのは、**顧客の文に絶対に出ない**から
# (md にも、`check_answer.py` が通す文にも現れない)。
# `render_answer.build_story` を素通りし `Paragraph.text` にそのまま残ることを実測している(2026-09-29)。
SENTINEL_RE = re.compile("\x00board:(\\d+)\x00")


def sentinel(n):
    return f"\x00board:{n}\x00"


class Mark:
    """本編の 1 つの印。**`check_answer.py` の印の文法をそのまま読んだもの**(新しい文法を作らない)。"""

    def __init__(self, line_index, appendix, game_no, ply, group, inner):
        self.line_index = line_index
        self.appendix = appendix      # 付録の番号(int)
        self.game_no = game_no
        self.ply = ply
        self.group = group            # 付録 3 だけ持つ(組をまたいで局番号が衝突する)
        self.inner = inner            # `局/手 付録N [組]` の生の文字列(索引の鍵に使う)

    def __repr__(self):
        return f"<Mark 付録{self.appendix} {self.inner} 行{self.line_index}>"


def marks_of(md_text):
    """印を**出てきた順**に返す。行番号は 0 起点(`md_text.split("\\n")` の添字)。

    **形の崩れはここで落とす** ― 検査 7 も同じ形で落とすので、ここに来る時点では崩れていないはずだが、
    **「はず」で通さない**(黙って印を 1 つ落とすと、盤が 1 枚足りない PDF が「できた」ことになる)。
    """
    marks = []
    for idx, line in enumerate(md_text.split("\n")):
        for m in CA.POS_TAG_RE.finditer(line):
            inner = m.group(1)
            inner_m = CA.POS_INNER_RE.match(inner)
            if inner_m is None:
                raise ExitBodyError(f"{idx + 1} 行目: 局面の印の形が崩れている({inner})")
            group = inner_m.group(4)
            marks.append(Mark(idx, int(inner_m.group(3)), int(inner_m.group(1)),
                              int(inner_m.group(2)), group.strip() if group else None, inner))
    return marks


def strip_and_insert(md_text, marks):
    """印を**取り除き**(P-123)、その行の**直後**に目印だけの行を入れる。

    返り値: 目印を入れた md。**印 1 つに目印 1 つ**で、番号は `marks` の並びと同じ。

    【なぜ「その行の直後」か】`build_story` は 1 行を 1 つの `Paragraph` にするので、
    目印だけの行は**目印だけの `Paragraph`** になり、そこを `Board` に入れ替えられる。
    **表の行・箇条書きの途中には入れられない**(表は連続する行をまとめて 1 つの `Table` にするので、
    間に行を挟むと表が割れる)。だから**表の行に印があれば落とす**。
    """
    lines = md_text.split("\n")
    by_line = {}
    for n, mark in enumerate(marks):
        by_line.setdefault(mark.line_index, []).append(n)
    out = []
    for idx, line in enumerate(lines):
        stripped = CA.POS_TAG_RE.sub("", line)
        out.append(stripped)
        if idx not in by_line:
            continue
        from render_answer import is_table_row
        if is_table_row(stripped.strip()):
            raise ExitBodyError(
                f"{idx + 1} 行目: 表の行に局面の印がある(表は連続する行を 1 つにまとめるので、"
                "間に盤を入れると表が割れる。印は表の外の段落に置く)")
        for n in by_line[idx]:
            out.append("")
            out.append(sentinel(n))
    return "\n".join(out)


def swap_boards(story, boards):
    """目印の `Paragraph` を `Board` に入れ替える。**数が合わなければ落ちる**(印 1 つに盤 1 つ)。

    引数 `boards`: `{番号: Flowable}`。番号は `marks` の並び。
    """
    out = []
    seen = []
    for flowable in story:
        text = getattr(flowable, "text", None)
        m = SENTINEL_RE.fullmatch(text.strip()) if isinstance(text, str) else None
        if m is None:
            if isinstance(text, str) and SENTINEL_RE.search(text):
                raise ExitBodyError(f"目印が他の文と同じ段落に入った: {text[:60]!r}")
            out.append(flowable)
            continue
        n = int(m.group(1))
        if n not in boards:
            # **ここで落とす。**下の数の照合だけに頼ると、**余分な目印が黙って捨てられ**、
            # 番号がたまたま揃ったときに通ってしまう(変異試験で実測 2026-09-29)。
            raise ExitBodyError(f"{n} 番の目印に対応する盤が無い")
        seen.append(n)
        out.append(boards[n])
    if sorted(seen) != sorted(boards):
        raise ExitBodyError(
            f"差し替えた目印 {sorted(seen)} と盤 {sorted(boards)} の数が合わない(印 1 つに盤 1 つ)")
    return out


# ==================== 見本用(対応表のページを抜く) ====================
# **正本 §1・§7**: 対応表は**本人用だけ**。**見本用はそのページを抜く。**
# 見分けは `check_structure.py` の `SECTIONS`・`MAPPING_ROLE`(**門と同じ定数**。写しを作らない)。
# **ページ数では決めない** ― 「最後の 1 ページを抜く」にすると、対応表が最後でなくなった日に黙って別の
# ページを抜く。`afterFlowable` で**節が載ったページ**を記録して、そのページを抜く。


def is_section_heading(flowable):
    """節の見出しの `Paragraph` か。**様式の名前は `render_answer.py` の `S_H2` から引く**
    (`"ah2"` と書き写さない ― 写すと片方だけ直る)。
    """
    import render_answer as RA

    style = getattr(flowable, "style", None)
    return getattr(style, "name", None) == RA.S_H2.name


def mapping_heading_matches(text):
    """`## 対応表 …` の見出しか。**`check_structure.py` の役割の表から引く**(文字列を写さない)。"""
    head, contains = next((h, c) for role, h, c in CS.SECTIONS if role == CS.MAPPING_ROLE)
    body = text.strip()
    if not body.startswith(head):
        return False
    return contains is None or contains in body


def drop_page(src_pdf, out_pdf, page_no):
    """`src_pdf` から `page_no`(1 起点)を抜いたものを `out_pdf` に書く。"""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(src_pdf)
    if not 1 <= page_no <= len(reader.pages):
        raise ExitBodyError(f"抜くページ {page_no} が範囲外(PDF は {len(reader.pages)} ページ)")
    writer = PdfWriter()
    for i, page in enumerate(reader.pages, start=1):
        if i != page_no:
            writer.add_page(page)
    with open(out_pdf, "wb") as f:
        writer.write(f)
    return len(reader.pages) - 1


# ==================== 材料(REPORT_DATA_DIR の流儀。新しい渡し方を作らない) ====================
# `render_main.py`(= `_head.py`)・`render_direct.py` と**同じ**: `REPORT_DATA_DIR` にカンマ区切りで
# フォルダを渡し、その中の `sfens.json`・`prose.json`・`patient_report_data.json` を読む。
# 同じ `kifuId` が複数のフォルダに出たら**最初に読んだもの**(`render_direct.py` と同じ)。
HERE = os.path.dirname(os.path.abspath(__file__))


def report_dirs():
    return [d for d in os.environ.get("REPORT_DATA_DIR", HERE).split(",") if d]


def load_sfens(dirs):
    """`{kifuId: {"sfens": […], "moves": […], "side": …}}`(`render_direct.py` と同じ読み方)。"""
    out = {}
    for d in dirs:
        path = os.path.join(d, "sfens.json")
        if not os.path.exists(path):
            continue
        for kifu_id, v in CA.load_json(path).items():
            out.setdefault(kifu_id, v)
    return out


def prose_partner(prose_path, patients):
    """付録 1 の局番号 → 棋譜を解く相手(`patient_report_data.json`)を**明示的に決める**。

    付録 1 の印は `局/手` だけで**組を持たない**(`--prose` は今回の組の 1 本だけ)。局番号から
    `kifuId` と先後を引くには `patient_report_data.json` が要るが、`--patient` は組ごとに複数来る。
    **同じフォルダに置かれているものが同じ組**(`render_main.py` が `prose.json` を
    `REPORT_DATA_DIR` から、`patient_report_data.json` を引数から取り、両方が同じ report フォルダに
    並んでいるのが既存の置き方)。**推測で選ばず、一致しなければ落とす。**
    """
    want = os.path.abspath(os.path.dirname(prose_path))
    hits = [p for p, _tag in patients if os.path.abspath(os.path.dirname(p)) == want]
    if len(hits) != 1:
        raise ExitBodyError(
            f"付録 1 の局番号を解く patient_report_data.json が決まらない("
            f"{os.path.basename(prose_path)} と同じフォルダのものが {len(hits)} 件)。"
            "同じ組の --patient を 1 つ渡す")
    return CA.load_json(hits[0])


# ==================== 印 → 盤 ====================
# **付録 1 と付録 3 で、盤の出どころは同じ `sfens.json`**(本人が指した実際の向き)。
# 材料の `sfen`(本人 = 先手に畳んだ向き)は**使わない** ― 2026-09-29 の実測で、非 mirrored の 34 件は
# `sfens[dply-1]` と完全一致し、違った 69 件は mirrored のちょうど 69 件だった。つまり 2 つの経路は
# mirror の分だけ違う。**両方を使うと「1 手ずれても両方緑」になる**ので、経路は 1 本にする
# (司令塔の判断 A・2026-09-29)。門は `board_spec_test.py` の `test_20`。


def board_style():
    """盤の色・書体は**本編の組版から借りる**(`render_answer.py`。新しい色を決めない)。"""
    import board_draw
    import render_answer as RA

    return board_draw.BoardStyle(ink=RA.INK, red=colors_red(), bg=RA.BG,
                                 line=RA.LINE, muted=RA.MUTED, font=RA.FONT)


def colors_red():
    """相手の手の升を塗る赤。`_util.py` の `RED` と同じ値(付録と同じ見え方にする)。"""
    from reportlab.lib import colors

    return colors.HexColor("#c9473f")


def appendix1_board(mark, prose, patient, sfens, style, person):
    """付録 1 の印 → `Board`。**`_mid.py` と同じ判断**(`board_spec.scene_spec`)。"""
    pz = prose.get(str(mark.game_no))
    if pz is None:
        raise ExitBodyError(f"付録 1 の材料に第 {mark.game_no} 局が無い(検査 7 は通っているので道具の不具合)")
    scenes = [s for s in (pz.get("scenes") or []) if s.get("ply") == mark.ply]
    if len(scenes) != 1:
        raise ExitBodyError(
            f"第 {mark.game_no} 局 {mark.ply} 手目の場面が {len(scenes)} 件(1 件でなければ盤を決められない)")
    games = {g["no"]: g for g in patient["games"]}
    game = games.get(mark.game_no)
    if game is None:
        raise ExitBodyError(f"patient_report_data.json に第 {mark.game_no} 局が無い")
    record = sfens.get(game["id"])
    if record is None:
        raise ExitBodyError(f"sfens.json に {game['id']} が無い")
    spec = BS.scene_spec(scenes[0], record["sfens"], record["moves"])
    arrows = ()
    if spec["wants_arrows"]:
        import board_draw

        events = {(e["gameNo"], e["ply"]): e for e in patient["events"]}
        e = events.get((mark.game_no, mark.ply))
        if e is None:
            raise ExitBodyError(f"第 {mark.game_no} 局 {mark.ply} 手目の記録(events)が無い")
        # **`_mid.py` 168〜169 行と同じ矢印**(実戦の手 = 茶の実線、第 1 候補 = 青緑の破線)。
        same = e["sameBest"] or not e.get("bestUsi") or e["bestUsi"] == e["playedUsi"]
        arrows = [(e["playedUsi"], board_draw.COL_PLAYED, False, 0 if same else 1.3)]
        if not same:
            arrows.append((e["bestUsi"], board_draw.COL_CAND, True, -1.3))
    return make_board(spec["sfen"], BS.user_sente(game["side"]), style, person,
                      usi=spec["usi"], arrows=arrows)


def appendix3_records(direct):
    """`{(組, 局, 手): ("fork"|"final", 材料の 1 件)}`。**検査 7 が受ける鍵と同じ形**。"""
    out = {}
    for raw in direct["raw"]:
        if raw.get("kind") == "direct_answers":
            for a in raw.get("answers") or []:
                out.setdefault((a["group"], a["gameNo"], a["displayPly"]), ("fork", a))
        elif raw.get("kind") == "final_positions":
            for e in raw.get("entries") or []:
                out.setdefault((e["group"], e["gameNo"], e["moves"]), ("final", e))
    return out


def appendix3_board(mark, records, sfens, style, person):
    """付録 3 の印 → `Board`。**`render_direct.py` と同じ判断**(`board_spec.fork_spec`/`final_spec`)。"""
    import board_draw

    key = (mark.group, mark.game_no, mark.ply)
    if key not in records:
        raise ExitBodyError(f"付録 3 の材料に {mark.inner} が無い(検査 7 は通っているので道具の不具合)")
    kind, record = records[key]
    sfens_record = sfens.get(record["kifuId"])
    if sfens_record is None:
        raise ExitBodyError(f"sfens.json に {record['kifuId']} が無い")
    if kind == "fork":
        spec = BS.fork_spec(record, sfens_record)
        actual = BS.genuine_move(record.get("actualMove"), spec["mirrored"])
        top1 = BS.genuine_move(record.get("top1Move"), spec["mirrored"])
        same = actual == top1
        arrows = [(actual, board_draw.COL_PLAYED, False, 0 if same else 1.3)] if actual else []
        if top1 and not same:
            arrows.append((top1, board_draw.COL_CAND, True, -1.3))
    else:
        spec = BS.final_spec(record, sfens_record)
        top1 = BS.genuine_move(record.get("top1Move"), spec["mirrored"])
        arrows = [(top1, board_draw.COL_CAND, True, 0)] if top1 else []
    return make_board(spec["sfen"], spec["user_sente"], style, person, arrows=arrows)


def make_board(sfen, user_sente, style, person, usi=None, arrows=()):
    """盤 1 枚。大きさは本編の幅に収まる 62mm(付録の 42〜56mm より大きい ― 本編は 2 枚だけなので)。"""
    from reportlab.lib.units import mm

    import board_draw

    return board_draw.Board(sfen, user_sente, style, usi=usi, size=62 * mm,
                            person=person, arrows=tuple(arrows))


# ==================== 対応表のページを記録する ====================
class MappingPageRecorder:
    """**対応表の節が載ったページ**を `doc.afterFlowable` で記録する。

    **ページ数では決めない** ― 「最後の 1 ページを抜く」にすると、対応表が最後でなくなった日に
    黙って別のページを抜く。**節が載ったページ**を見て、**2 ページにまたがれば落とす**
    (差が 1 ページでなくなるので、黙って 1 枚だけ抜かない)。

    `exit_index.PageIndexRecorder` と**同じ流儀**: flowable を 1 つも足さない(足すと組版が変わる)。
    """

    def __init__(self, doc):
        self.doc = doc
        self.pages = []          # 対応表の節に属する flowable が載ったページ(重複あり)
        self._in_mapping = False
        doc.afterFlowable = self._record

    def _record(self, flowable):
        # **節の見出しの様式のものだけを見出しとみなす。**変異試験で見つけた穴(2026-09-29):
        # 本文の段落が「対応表は本人用だけです」のように始まっていると、**そこから対応表の節が
        # 始まったことになり、抜くページが前にずれる。**`build_story` は `## ` の行だけを
        # `S_H2` にするので、**様式の名前**で絞る(`render_answer.py` の 1 か所から引く)。
        if not is_section_heading(flowable):
            if self._in_mapping:
                self.pages.append(self.doc.page)
            return
        text = getattr(flowable, "text", None)
        if isinstance(text, str) and mapping_heading_matches(text):
            self._in_mapping = True
        if self._in_mapping:
            self.pages.append(self.doc.page)

    def page_to_drop(self):
        if not self.pages:
            raise ExitBodyError(
                "対応表の節が本編に無い(正本 §1: 対応表は本人用だけ・見本用はそのページを抜く)")
        first, last = min(self.pages), max(self.pages)
        if first != last:
            raise ExitBodyError(
                f"対応表の節が {first}〜{last} ページにまたがっている"
                "(見本用との差が 1 ページでなくなるので、黙って 1 枚だけ抜かない)")
        return first


# ==================== 本体 ====================
def parse_own_args(argv):
    """この道具だけの引数を抜き、残りは `check_answer.py` にそのまま渡す。"""
    own = {"out_person": None, "out_sample": None, "person": "本人"}
    rest = []
    i = 0
    while i < len(argv):
        flag = argv[i]
        if flag in ("--out-person", "--out-sample", "--person"):
            value = argv[i + 1] if i + 1 < len(argv) else None
            if value is None or value.startswith("--"):
                raise ExitBodyError(f"{flag} に値が無い")
            own[flag[2:].replace("-", "_")] = value
            i += 2
            continue
        rest.append(flag)
        i += 1
    missing = [k for k in ("out_person", "out_sample") if own[k] is None]
    if missing:
        raise ExitBodyError(f"足りない引数: {' '.join('--' + m.replace('_', '-') for m in missing)}")
    return own, rest


def build(own, rest):
    import functools

    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate

    import render_answer as RA

    args = CA.parse_args(rest)
    repo_root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    ctx = CA.build_materials(args, repo_root)
    with open(args.markdown_path, encoding="utf-8") as f:
        raw_md = f.read()

    # **検査を先に通す。**落ちた文があれば描かない(`render_answer.py` と同じ順)。
    # **印が材料に実在するかの照合は検査 7 がここでやっている** ― この道具は照合を持たない。
    problems = CA.check_answer(raw_md, ctx)
    if problems:
        raise ExitBodyError("\n".join(f"{ln}: {why}: {line.strip()[:100]}" for ln, why, line in problems))

    body = CA.strip_dev_section(raw_md)
    marks = marks_of(body)
    for mark in marks:
        if mark.appendix not in (1, 3):
            raise ExitBodyError(
                f"{mark.inner}: 正本の束に入っているのは付録 1 と付録 3 だけ"
                "(付録 2 のページは両実物で 0 枚・付録 4 に盤は無い)")

    dirs = report_dirs()
    sfens = load_sfens(dirs)
    style = board_style()
    # 付録 3 の材料は `ctx["materials"]["direct"]`(`build_materials` の返り値の形。`ctx` の直下ではない)。
    direct = ctx["materials"]["direct"]
    records3 = appendix3_records(direct) if direct is not None else {}
    prose = patient = None
    if any(m.appendix == 1 for m in marks):
        if not args.prose_paths:
            raise ExitBodyError("本編が付録 1 を指しているのに --prose が無い")
        prose = CA.load_json(args.prose_paths[0])
        patient = prose_partner(args.prose_paths[0], args.patients)

    boards = {}
    for n, mark in enumerate(marks):
        if mark.appendix == 1:
            boards[n] = appendix1_board(mark, prose, patient, sfens, style, own["person"])
        else:
            boards[n] = appendix3_board(mark, records3, sfens, style, own["person"])

    with_sentinels = strip_and_insert(body, marks)
    if CA.POS_TAG_RE.search(with_sentinels):
        raise ExitBodyError("印が取り除けていない(P-123: 印は reportlab が黙って捨てるだけなので自分で外す)")

    title = RA._find_doc_title(with_sentinels)
    doc = SimpleDocTemplate(
        own["out_person"], pagesize=A4,
        leftMargin=RA.LEFT_MARGIN, rightMargin=RA.RIGHT_MARGIN,
        topMargin=RA.TOP_MARGIN, bottomMargin=RA.BOTTOM_MARGIN,
        title="対局後診断・本編", author="将棋コーチ(試作)",
    )
    recorder = MappingPageRecorder(doc)
    story = swap_boards(RA.build_story(with_sentinels, title), boards)
    doc.build(story, canvasmaker=functools.partial(RA._ReportCanvas, report_title=title))

    dropped = drop_page(own["out_person"], own["out_sample"], recorder.page_to_drop())
    return {"marks": len(marks), "boards": len(boards),
            "mappingPage": recorder.page_to_drop(), "samplePages": dropped}


def main(argv):
    own, rest = parse_own_args(argv)
    out = build(own, rest)
    print(f"wrote {own['out_person']}(盤 {out['boards']} 枚・対応表は {out['mappingPage']} ページ)")
    print(f"wrote {own['out_sample']}({out['samplePages']} ページ ― 対応表を抜いた)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (ExitBodyError, BS.BoardSpecError, CA.CheckAnswerError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
