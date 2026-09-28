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
#     --out <表紙.md>
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
    i = 0
    while i < len(argv):
        flag, value = argv[i], argv[i + 1] if i + 1 < len(argv) else None
        if value is None or value.startswith("--"):
            raise ExitCoverError(f"{flag} に値が無い")
        if flag == "--source-index":
            out["sources"].append(value)
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
    """束ねる付録を、組版の索引そのものから決める(引数で二重に指定させない)。"""
    names = []
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
    return names


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
        "finals": len(finals.get("entries", [])),
        "forks": len(direct.get("answers", [])),
    }


def honbun_refs(md_text):
    """本編の印を、**それが書かれた本編の見出しの下**に割り当てる(「本編との対応」の列)。

    **実物の対応の列より粗い。**実物は「「ひとことで」の 3 つ目(崩れ)」のように
    節の中の順番や仮説番号まで書いているが、**それは印からは機械で出せない**
    (印は付録と節を指すだけ)。出せないものを作らず、**指している本編の見出しだけ**を出す。
    """
    refs = {}
    heading = None
    for line in md_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            continue
        for appendix, name in ER.SEC_TAG_RE.findall(line):
            refs.setdefault((appendix, name), [])
            if heading and heading not in refs[(appendix, name)]:
                refs[(appendix, name)].append(heading)
    return refs


def build_rows(appendices, numbers, refs, problems):
    rows = []
    n = 0
    for appendix in appendices:
        for name in EI.COVER_SECTIONS[appendix]:
            n += 1
            title = EI.section_title(appendix, name, **numbers)
            content = EI.COVER_CONTENT[(appendix, name)].format(**numbers)
            where = refs.get((appendix, name))
            if not where:
                # **黙って空欄にしない。**本編が指していない節を表紙に載せると、
                # 顧客は本編から辿れないページを案内される。
                problems.append(f"表紙: 本編が指していない節を表に載せようとした: {appendix}/{name}")
                where = []
            rows.append({"no": n, "appendix": appendix, "section": name, "title": f"{n}. {title}",
                         "content": content,
                         "ref": "・".join(f"「{h}」" for h in where)})
    return rows


def build_md(args):
    problems = []
    appendices = bundled_appendices(args["sources"])
    numbers = numbers_of(args)
    with open(args["honbun_md"], encoding="utf-8") as f:
        md_text = f.read()
    # **開発用の節の印は読まない** ― `exit_render.py` と同じ扱い(`check_answer` の関数をそのまま呼ぶ)。
    refs = honbun_refs(CA.strip_dev_section(md_text))
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
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except ExitCoverError as e:
        print(f"表紙を作れない: {e}", file=sys.stderr)
        sys.exit(2)
