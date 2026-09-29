# -*- coding: utf-8 -*-
# STEP CUSTOMER-EXIT。**付録の表紙の md を作る。**
# (md → PDF は `exit-render` の後半。この道具は md までを作る。)
#
# 【形の正本】`docs/GOLDEN_MASTER_CUSTOMER_EXIT.md` §8。**実物 2 件を fitz で読んだ形**で、4 要素:
#   1. 見出し / 2. 段落 / 3. 表「この冊子に入っているもの」(節・中身・本編との対応) / 4. 末尾の段落
# **表は付録ごとに 1 行ではない** ― 実物はどちらも 4 行で、付録 3 が 2 行出す(実測 2026-09-28)。
# 束ねるのは付録 1 + 付録 3 なので **3 行**になる。並びは `exit_index.COVER_SECTIONS` が正本。
#
# 【実物から写してよいもの・写せないもの】(正本 §9。**実物は「正しい形」ではなく「ある時点の形」**)
# - **枠**(見出し・段落・末尾)は **4 人目の実物から写した固定文**。改名の一覧を通してある。
#   3 人目からは写さない ― 廃止済みの免責 2 文が付き、顧客の名前が入っている。
# - **中身の欄は実物から写せない。**4 人目は「時計で終わった」(いまの道具に 0 件)、
#   3 人目は「時間切れ」(2026-09-27 に断定をやめた語)を使っている。
#   だから**語は道具に実在する行から採り**、**数は材料から入れる**(新しい数を作らない)。
#
# 【数はどこから来るか】**本編が使うのと同じ材料**から読む(2 つ目の出どころを作らない):
#   局数 = `patient_report_data.json` の `summary.games` / 形勢が動いた局 = `prose.json` の件数
#   最後の局面 = `final_positions.json` の `entries` / 分かれ道 = `direct_answers.json` の `answers`
# **顧客の名前は読まない**(`patient_report_data.json` の `person` は触らない ― 表紙に名前は入れない)。
#
# 使い方:
#   python3 -X utf8 exit_cover.py --honbun-md <本編.md> \
#     --source-index <付録1の索引.json> [--source-index <付録3の索引.json>]… \
#     --patient <patient_report_data.json> --group <組のラベル> \
#     --prose <prose.json> --final-positions <final_positions.json> --direct <direct_answers.json> \
#     --out <表紙.md> [--out-pdf <表紙.pdf>]
#
# `--out-pdf` を渡すと、**同じ実行で** md を PDF に組む(組版は `exit_body.render_plain`)。
# md と PDF を別の実行に分けると、md を直して PDF を組み忘れた 2 つの版が並ぶ。
import json
import sys

import check_answer as CA
import exit_index as EI

# 本編が節を指す印の文法は **`exit_render.py` が正本**(印の読み方を 2 か所に持たない ―
# 片方だけ直ると、表紙の表と束ねた中身が食い違う)。
import exit_render as ER


class ExitCoverError(Exception):
    pass


def parse_args(argv):
    single = {"--honbun-md": "honbun_md", "--patient": "patient", "--group": "group",
              "--prose": "prose", "--final-positions": "finals", "--direct": "direct",
              "--out": "out"}
    out = {v: None for v in single.values()}
    out["sources"] = []
    # 表紙の PDF(任意)。渡されたら md と**同じ実行で**組む ―
    # 別の道具に分けると、md を直してから PDF を組み忘れる道ができる(2 つの版が並ぶ)。
    out["out_pdf"] = None
    i = 0
    while i < len(argv):
        flag, value = argv[i], argv[i + 1] if i + 1 < len(argv) else None
        if value is None or value.startswith("--"):
            raise ExitCoverError(f"{flag} に値が無い")
        if flag == "--source-index":
            out["sources"].append(value)
        elif flag == "--out-pdf":
            out["out_pdf"] = value
        elif flag in single:
            out[single[flag]] = value
        else:
            raise ExitCoverError(f"知らない引数: {flag}")
        i += 2
    missing = [f for f, k in single.items() if out[k] is None]
    if missing:
        raise ExitCoverError(f"足りない引数: {' '.join(missing)}")
    if not out["sources"]:
        raise ExitCoverError("--source-index を 1 本以上渡す(束ねる付録が決まらないと表が作れない)")
    return out


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def bundled_appendices(source_paths):
    """束ねる付録と、その索引を、組版の索引そのものから決める(引数で二重に指定させない)。

    返り値 = `(付録名の一覧〈順序つき〉, {付録名: 索引})`。
    索引も返すのは、**局面の印がどの節に属するかを索引から決める**ため(D2)。
    """
    names, indexes = [], {}
    for path in source_paths:
        idx = load(path)
        name = idx.get("appendix")
        if not name:
            raise ExitCoverError(f"索引に appendix が無い: {path}")
        if name not in EI.COVER_SECTIONS:
            raise ExitCoverError(f"表紙に出す節を持っていない付録: {name}(COVER_SECTIONS が正本)")
        if name in names:
            raise ExitCoverError(f"同じ付録の索引が 2 回渡された: {name}")
        names.append(name)
        indexes[name] = idx
    return names, indexes


def section_of_position(index, group, key):
    """その局面が**どの節のページに在るか**を、組版の索引だけから決める(D2)。

    節の開始ページ以下で**最も後ろの節**を返す(流し込みなので、節はページの途中から始まる)。
    **PDF の文字は見ない** ― 索引が正本(`exit_render.py` と同じ流儀)。
    引けなければ `None`(黙って別の節に混ぜない)。
    """
    positions = index.get("positions") or {}
    page = positions.get(group, {}).get(key) if group else positions.get(key)
    if page is None:
        return None
    best = None
    for name, start in (index.get("sections") or {}).items():
        if start <= page and (best is None or start > best[1]):
            best = (name, start)
    return best[0] if best else None


def bundled_forks_of(args, indexes):
    """**この冊子に載る「分かれ道」の局面の数**(P-179。2026-09-29)。

    表紙は「103 局面ありました。この冊子に載せているのは… N 局面です」と言うので、
    **N は束に入る数**でなければならない(材料の全部ではない)。
    **段の順は変えない** ― 束ねる前に、本編の md と組版の索引だけから出る(実測で 9 と一致)。
    判定は 2 か所とも借りもの: 束に入るページは `exit_render.bundled_source_pages`、
    節の中の数え方は `exit_index.positions_in_section`。**写しをここに作らない。**

    その付録を束ねていない・節が索引に無いときは `None`(表紙はその行を出さない)。
    """
    if "付録3" not in indexes:
        return None
    with open(args["honbun_md"], encoding="utf-8") as f:
        md_text = CA.strip_dev_section(f.read())
    pages = ER.bundled_source_pages(md_text, indexes, appendix="付録3", strict=False).get("付録3") or []
    if not pages:
        # **束に入るページが 0 枚なら、その上に乗る局面も 0。**節を引かずに 0 と言える
        # (節が索引に無い材料でも落ちない ― 落とすのは束ねる側の仕事)。
        return 0
    return EI.positions_in_section(indexes["付録3"], pages, "分かれ道")


def numbers_of(args):
    """数は材料から。**新しい数を作らない。**"""
    patient = load(args["patient"])
    if "summary" not in patient or "games" not in patient["summary"]:
        raise ExitCoverError("patient_report_data.json に summary.games が無い")
    finals = load(args["finals"])
    direct = load(args["direct"])
    return {
        "games": int(patient["summary"]["games"]),
        "group": args["group"],
        "featured": len(load(args["prose"])),
        # `rest` = 1 局ずつ見た局を除いた残り。**`_mid.py` の `len(rest)` と同じ数でなければならない。**
        # **引き算は `exit_index.rest_count` の 1 本だけ**(2026-09-29。以前は 3 か所が同じ形を持ち、
        # `_mid.py` の `assert` は自分の一覧と自分の引き算しか比べていなかった ― 独立監査が実測)。
        # ここで別に数えると、**表紙の題と付録の中の題が食い違う**(顧客がページを探せない)。
        "rest": EI.rest_count(patient["summary"]["games"], len(load(args["prose"]))),
        "finals": len(finals.get("entries", [])),
        "forks": len(direct.get("answers", [])),
    }


def honbun_refs(md_text, indexes):
    """本編の印を、**それが書かれた本編の見出しの下**に割り当てる(「本編との対応」の列)。

    **実物の対応の列より粗い。**実物は「「ひとことで」の 3 つ目(崩れ)」のように
    節の中の順番や仮説番号まで書いているが、**それは印からは機械で出せない**
    (印は付録と節を指すだけ)。出せないものを作らず、**指している本編の見出しだけ**を出す。

    **2 種類の印を両方読む**(2026-09-29。司令塔の ⑥ が実物で見つけた D2):
    - **節の印**(`<!-- sec: 付録N/節 -->`)― その節への参照
    - **局面の印**(`<!-- pos: 局/手 付録N [組] -->`)― **その局面が在る節**への参照。
      どの節かは `section_of_position` が組版の索引から決める

    局面の印を読まないと、**節の印を置いた 1 か所の見出しが 3 行とも並ぶ**(実物で出た) ―
    顧客は「どの節から引ける付録か」が分からない。盤を載せた「局面で見る」が出るのが正しい。
    """
    refs = {}
    heading = None
    for line in md_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            continue

        def add(appendix, name):
            refs.setdefault((appendix, name), [])
            if heading and heading not in refs[(appendix, name)]:
                refs[(appendix, name)].append(heading)

        for appendix, name in ER.SEC_TAG_RE.findall(line):
            add(appendix, name)
        for m in CA.POS_TAG_RE.finditer(line):
            inner = CA.POS_INNER_RE.match(m.group(1))
            if inner is None:
                raise ExitCoverError(f"局面の印の形が崩れている: {m.group(1)}")
            appendix = f"付録{int(inner.group(3))}"
            index = indexes.get(appendix)
            if index is None:
                continue  # その付録を束ねていない(束ねの側が落とす)
            group = (inner.group(4) or "").strip() or None
            name = section_of_position(index, group, EI.pos_key(int(inner.group(1)), int(inner.group(2))))
            if name is not None and name in EI.COVER_SECTIONS.get(appendix, ()):
                add(appendix, name)
    return refs


def build_rows(appendices, numbers, refs, problems):
    """表紙の表の行。**本編が指した節だけ**を載せる。

    【なぜ「指していない節は載せない」か】束ねた付録に入るのは**本編が指すページだけ**である
    (`exit_render.py`)。指していない節のページはそもそも冊子に無いので、
    **表に載せれば顧客は在りもしないページを案内される。**
    はじめは「指していないなら落とす」にしていたが、**それでは書き手が節を 1 つ使わなかっただけで
    工程が止まる**(実測 2026-09-29: 書き手が「最後の局面」〈標本 1 局〉を使わないことにして止まった)。
    **使う節の数を書き手が決められること**が正しい ― 表はそれに合わせて 2 行になる。

    【それでも落とす場合】**索引を渡した付録が 1 行も持たないとき。**
    その付録は束ねられないのに `--source-index` で渡されている = 呼ぶ側の引数が食い違っている。
    """
    rows = []
    n = 0
    for appendix in appendices:
        before = n
        for name in EI.COVER_SECTIONS[appendix]:
            where = refs.get((appendix, name))
            if not where:
                continue  # 本編が指していない節 ― 束ねた付録にそのページは無い
            n += 1
            title = EI.section_title(appendix, name, **numbers)
            content = EI.COVER_CONTENT[(appendix, name)].format(**numbers)
            rows.append({"no": n, "appendix": appendix, "section": name, "title": f"{n}. {title}",
                         "content": content,
                         "ref": "・".join(f"「{h}」" for h in where)})
        if n == before:
            problems.append(
                f"表紙: {appendix} の索引を渡されたが、本編がこの付録の節を 1 つも指していない"
                "(束ねられない付録の索引が渡されている)")
    return rows


def build_md(args):
    problems = []
    appendices, indexes = bundled_appendices(args["sources"])
    numbers = numbers_of(args)
    # **束に入る局面の数**(P-179)。`None` なら型に無いので鍵を足さない
    # (`format` が落ちるのは型がその鍵を使っているときだけ)。
    bundled = bundled_forks_of(args, indexes)
    if bundled is not None:
        # **鍵は 1 つ**(2 つ持つと、型がどちらを使っているか分からなくなる)。
        numbers["bundled_forks"] = bundled
    with open(args["honbun_md"], encoding="utf-8") as f:
        md_text = f.read()
    # **開発用の節の印は読まない** ― `exit_render.py` と同じ扱い(`check_answer` の関数をそのまま呼ぶ)。
    refs = honbun_refs(CA.strip_dev_section(md_text), indexes)
    rows = build_rows(appendices, numbers, refs, problems)
    if problems:
        raise ExitCoverError("\n".join(problems))

    out = [f"# {EI.COVER_HEADING}", "", EI.COVER_LEAD.format(**numbers), "",
           f"## {EI.COVER_TABLE_HEADING}", "",
           "| " + " | ".join(EI.COVER_TABLE_COLUMNS) + " |",
           "|" + "---|" * len(EI.COVER_TABLE_COLUMNS)]
    for r in rows:
        out.append(f"| {r['title']} | {r['content']} | {r['ref']} |")
    out += ["", EI.COVER_TAIL, ""]
    return "\n".join(out), rows


def main(argv):
    args = parse_args(argv)
    text, rows = build_md(args)
    with open(args["out"], "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {args['out']}({len(rows)} 行: "
          + "・".join(f"{r['appendix']}/{r['section']}" for r in rows) + ")")
    if args["out_pdf"] is not None:
        # 組版は `exit_body.render_plain`(`render_answer.py` の作り)の 1 か所。
        # **表紙は 1 ページのはず** ― 増えたら黙らない(`exit_render.py` は `--cover` に
        # ページ番号を 1 つしか受け取らないので、2 ページ目は束から落ちる)。
        import exit_body as EB

        pages = EB.render_plain(text, args["out_pdf"], "対局後診断・付録の表紙")
        if pages != 1:
            raise ExitCoverError(f"表紙が {pages} ページになった(束に入るのは 1 ページだけ)")
        print(f"wrote {args['out_pdf']}(1 ページ)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except ExitCoverError as e:
        print(f"表紙を作れない: {e}", file=sys.stderr)
        sys.exit(2)
