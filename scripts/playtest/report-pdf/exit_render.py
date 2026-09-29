# -*- coding: utf-8 -*-
# STEP CUSTOMER-EXIT の段 `exit-render` の**前半**: **付録のページ抜きと、索引の束ね。**
# (後半 ― 本編の md → 本人用・見本用の PDF と `<!-- pos: -->` への `Board` の差し込み ― は別に作る。)
#
# 【この道具がやること】
# 1. 本編の md から **`<!-- pos: 局/手 付録N [組] -->`** と **`<!-- sec: 付録N/節名 -->`** を読む
# 2. **組版が書いた索引**(`--source-index`)で、その印が**元の付録の何ページ**かを引く
# 3. **本編が指すページだけ**を `pypdf` で抜いて、付録 1 冊にする(表紙は `--cover` で渡されたときだけ先頭に置く)
# 4. **束ねた索引**を書く
#
# 【組版が書いた値は書き換えない】`付録N` の中身(`positions`・`sections`)は**組版の索引をそのまま写す**。
# **`check_structure.py` の `check_bundled_index` が鍵も値も突き合わせて落とす**(司令塔の条件 2026-09-28)。
# この道具が**新しく書く**のは `outputPositions`(束ねた後の 1 冊の中のページ)・`appendixPages`・
# `boardsDrawn`・`hasCover`・`sourcePages` の 5 つだけ。
#
# 【PDF の文字は検索しない】ページの決め方は**索引だけ**(仕様 §3 の 2)。
# 眉の書式を変えると黙って壊れる道を作らないため。
#
# 使い方:
#   python3 -X utf8 exit_render.py --honbun-md <本編.md> \
#     --source-index <付録1の索引.json>:<付録1.pdf> [--source-index <付録3の索引.json>:<付録3.pdf>]… \
#     [--cover <表紙.pdf>:<ページ番号>] \
#     --out-appendix <出力の付録.pdf> --out-index <page_index.json>
import json
import os
import re
import sys

import check_answer as CA
import exit_index as EI

# 本編が節を指す印(`<!-- pos: -->` は `check_answer.py` の `POS_TAG_RE` を使う ― 新しい文法を作らない)。
SEC_TAG_RE = re.compile(r"<!--\s*sec:\s*(付録\d+)\s*/\s*(.+?)\s*-->")

# **束ねた索引の上の階層に置いてよい鍵。**正本は `exit_index.py` の 1 か所
# (読む側の `check_structure.py` も同じものを import する ― 写しを 2 か所に持たない)。
OWN_KEYS = EI.EXIT_RENDER_KEYS


class ExitRenderError(Exception):
    pass


def parse_pair(value, what):
    """`<パス>:<もう 1 つ>` を割る(パスに `:` が入りうるので**右端**で割る)。"""
    if ":" not in value:
        raise ExitRenderError(f"{what} は <パス>:<値> の形で渡す: {value}")
    left, right = value.rsplit(":", 1)
    if not left or not right:
        raise ExitRenderError(f"{what} の左右どちらかが空: {value}")
    return left, right


def parse_args(argv):
    out = {"honbun_md": None, "sources": [], "cover": None, "out_appendix": None, "out_index": None}
    i = 0
    while i < len(argv):
        flag = argv[i]
        value = argv[i + 1] if i + 1 < len(argv) else None
        if value is None or value.startswith("--"):
            raise ExitRenderError(f"{flag} に値が無い")
        if flag == "--honbun-md":
            out["honbun_md"] = value
        elif flag == "--source-index":
            out["sources"].append(parse_pair(value, "--source-index"))
        elif flag == "--cover":
            path, page = parse_pair(value, "--cover")
            out["cover"] = (path, int(page))
        elif flag == "--out-appendix":
            out["out_appendix"] = value
        elif flag == "--out-index":
            out["out_index"] = value
        else:
            raise ExitRenderError(f"知らない引数: {flag}")
        i += 2
    missing = [k for k in ("honbun_md", "out_appendix", "out_index") if out[k] is None]
    if missing:
        raise ExitRenderError(f"足りない引数: {' '.join('--' + m.replace('_', '-') for m in missing)}")
    if not out["sources"]:
        raise ExitRenderError("--source-index を 1 本以上渡す(組版が書いた索引が無いとページを決められない)")
    return out


def load_sources(pairs):
    """`{付録名: {"index": …, "pdf": パス}}`。同じ付録が 2 本来たら落とす。"""
    sources = {}
    for index_path, pdf_path in pairs:
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)
        appendix = index.get("appendix")
        if appendix is None:
            raise ExitRenderError(f"{os.path.basename(index_path)} に appendix の欄が無い")
        if appendix not in EI.APPENDIX_SECTIONS:
            raise ExitRenderError(f"知らない付録: {appendix}(exit_index.py の APPENDIX_SECTIONS が正本)")
        if appendix in sources:
            raise ExitRenderError(f"付録「{appendix}」の索引が 2 本渡されている")
        if not os.path.exists(pdf_path):
            raise ExitRenderError(f"付録の PDF が無い: {pdf_path}")
        sources[appendix] = {"index": index, "pdf": pdf_path, "indexPath": index_path}
    return sources


def marks_of(md_text):
    """本編の印を、出てきた順に `(付録名, 種類, 鍵, 印の文字列)` で返す。**同じ順で付録に並べる。**"""
    marks = []
    for line in md_text.split("\n"):
        for m in CA.POS_TAG_RE.finditer(line):
            inner = m.group(1)
            inner_m = CA.POS_INNER_RE.match(inner)
            if inner_m is None:
                raise ExitRenderError(f"局面の印の形が崩れている: {inner}")
            g, p, n = int(inner_m.group(1)), int(inner_m.group(2)), int(inner_m.group(3))
            group = (inner_m.group(4) or "").strip() or None
            marks.append((f"付録{n}", "positions", (group, EI.pos_key(g, p)), inner))
        for m in SEC_TAG_RE.finditer(line):
            marks.append((m.group(1), "sections", (None, m.group(2)), f"{m.group(1)}/{m.group(2)}"))
    return marks


def appendix_number(appendix):
    """`付録3` → 3。**並べる順を決めるためだけ**に使う(名前の付け方に依存させない ―
    知らない形なら落ちる。`exit_index.APPENDIX_SECTIONS` の鍵はこの形で書かれている)。"""
    m = re.fullmatch(r"付録(\d+)", appendix)
    if m is None:
        raise ExitRenderError(f"付録の名前から番号が取れない: {appendix}(`付録N` の形で書く)")
    return int(m.group(1))


def source_page_of(sources, appendix, kind, key):
    """組版の索引から、元の付録の中のページを引く(**索引だけで決める。PDF の文字は見ない**)。"""
    src = sources.get(appendix)
    if src is None:
        raise ExitRenderError(f"本編が {appendix} を指しているが、その索引が渡されていない")
    table = src["index"].get(kind) or {}
    group, name = key
    if kind == "sections":
        if name not in table:
            raise ExitRenderError(f"{appendix} の索引に節「{name}」が無い")
        return table[name]
    if group is None:
        if name not in table:
            raise ExitRenderError(f"{appendix} の索引に局面 {name} が無い(組を書く付録なら組が要る)")
        return table[name]
    if group not in table or name not in table[group]:
        raise ExitRenderError(f"{appendix} の索引に、組 {group} の局面 {name} が無い")
    return table[group][name]


def check_neighbour_promises(sources, placed, problems):
    """**束ねたページが、束に入っていない隣のページを約束していないこと**(P-171。2026-09-29)。

    付録は本編が指したページだけを抜くので、**元の付録では本当だった「次のページから…」が、
    抜いた先で嘘になる。**顧客は在りもしないページを探す(3 周目の批評席 (a) が実物で挙げた)。

    見るのは **抜いた元のページの文字**(`fitz`)。**出力の PDF は見ない** ― 出力を見るには
    先に書かなければならず、**落ちたときに嘘のページを書いた PDF が残る。**
    語は `exit_index.NEIGHBOUR_PROMISES` の 1 か所(床であって天井ではない ― 上の注記)。

    改行は取り除いて探す ― `fitz` は「次のページか / ら 1 局ずつ」のように行で割る(実測)。
    """
    import fitz

    for appendix, page in sorted(placed):
        pdf_path = sources[appendix]["pdf"]
        with fitz.open(pdf_path) as doc:
            text = "".join(doc[page - 1].get_text().split())
        for phrase, step in EI.NEIGHBOUR_PROMISES.items():
            if phrase not in text:
                continue
            need = page + step
            if (appendix, need) in placed:
                continue
            problems.append(
                f"{appendix} の元の {page} ページ目が「{phrase}」と書いているが、"
                f"約束している {need} ページ目を束ねていない"
                f"(束ねたのは {sorted(p for a, p in placed if a == appendix)} ページ目)。"
                "直し方は 2 つ ― そのページを本編から指して束に入れるか、"
                f"組版の道具からその言い方を外す({appendix} の前文)")


def build(args):
    from pypdf import PdfReader, PdfWriter

    with open(args["honbun_md"], encoding="utf-8") as f:
        raw_md = f.read()
    # **「書いた側の記録(顧客には見せない)」の節を外す。**`check_answer.py` の `check_answer()` が
    # 同じ `POS_TAG_RE` を使う前に `strip_dev_section()` を通しているのと**同じ扱いに揃える**
    # (新しい判定は作らない ― 同じ関数をそのまま呼ぶ)。
    # **外さないと、顧客に見えない下書きのメモのために付録のページを抜く**
    # (2026-09-28 の監査が実際に再現。器の門の目的「顧客が読むものだけ」に反する)。
    md_text = CA.strip_dev_section(raw_md)
    sources = load_sources(args["sources"])
    marks = marks_of(md_text)

    writer = PdfWriter()
    readers = {}
    has_cover = False
    if args["cover"] is not None:
        cover_path, cover_page = args["cover"]
        readers[cover_path] = PdfReader(cover_path)
        writer.add_page(readers[cover_path].pages[cover_page - 1])
        has_cover = True

    # **付録番号 → 元のページ番号**の順に並べる(重複は除く。同じページを 2 回指しても 1 枚)。
    #
    # **「印の出た順」ではない**(2026-09-29 の直し。司令塔の ⑥ が実物で見つけた D7):
    # 本編が「局面で見る」で付録 3 を指し、あとの節で付録 1 を指すと、
    # **束ねた付録が 分かれ道 → 形勢の流れ → 最後の局面 の順**になり、
    # **表紙の表の順(付録 1 → 付録 3)と食い違った。**顧客は表紙の順でページを探す。
    # 実物(4 人目)は**付録番号順**(付録 1 → 3 → 4)である。
    # 並べ替えるのは**ページの順だけ**で、どのページを入れるかは変わらない(本編が指すページだけ)。
    def slot_key(mark):
        appendix, kind, key, _label = mark
        return (appendix_number(appendix), source_page_of(sources, appendix, kind, key))

    placed = {}          # (付録名, 元のページ) -> 出力のページ番号
    output_positions = {}  # 印の文字列 -> 出力のページ番号
    source_pages = {}      # 付録名 -> 抜いた元のページの一覧(入れた順)
    for appendix, kind, key, label in sorted(marks, key=slot_key):
        page = source_page_of(sources, appendix, kind, key)
        slot = (appendix, page)
        if slot not in placed:
            pdf_path = sources[appendix]["pdf"]
            if pdf_path not in readers:
                readers[pdf_path] = PdfReader(pdf_path)
            reader = readers[pdf_path]
            if page < 1 or page > len(reader.pages):
                raise ExitRenderError(f"{appendix} の索引が {page} ページを指しているが、PDF は {len(reader.pages)} ページ")
            writer.add_page(reader.pages[page - 1])
            placed[slot] = len(writer.pages)
            source_pages.setdefault(appendix, []).append(page)
        output_positions[label] = placed[slot]

    # **書く前に確かめる**(P-171)。落ちたら PDF は作らない ―
    # 嘘のページを約束した冊子が「できた」ことにならないようにする。
    problems = []
    check_neighbour_promises(sources, placed, problems)
    if problems:
        raise ExitRenderError("\n".join(problems))

    with open(args["out_appendix"], "wb") as f:
        writer.write(f)

    # **束ねた索引。**`付録N` は組版の索引をそのまま写す(書き換えない)。
    bundled = {
        "outputPositions": output_positions,
        "appendixPages": sorted(placed.values()),
        "boardsDrawn": sum(1 for _, kind, _, _ in marks if kind == "positions"),
        "hasCover": has_cover,
        "sourcePages": source_pages,
    }
    for appendix, src in sources.items():
        bundled[appendix] = {"positions": src["index"].get("positions") or {},
                             "sections": src["index"].get("sections") or {}}
    # **許可一覧で確かめる**(接頭辞では見ない ― 司令塔の指示)。知らない鍵が混ざる道を閉じる。
    allowed = set(OWN_KEYS) | set(sources)
    unknown = sorted(set(bundled) - allowed)
    if unknown:
        raise ExitRenderError(f"束ねた索引に知らない鍵が入った: {unknown}(許されるのは {sorted(allowed)})")

    with open(args["out_index"], "w", encoding="utf-8") as f:
        json.dump(bundled, f, ensure_ascii=False, indent=1, sort_keys=True)
    return bundled


def main(argv):
    args = parse_args(argv)
    bundled = build(args)
    print(f"wrote {args['out_appendix']}({len(bundled['appendixPages'])} ページ + 表紙 {1 if bundled['hasCover'] else 0})")
    print(f"wrote {args['out_index']}(盤 {bundled['boardsDrawn']} 件・付録 {sorted(k for k in bundled if k not in OWN_KEYS)})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (ExitRenderError, CA.CheckAnswerError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
