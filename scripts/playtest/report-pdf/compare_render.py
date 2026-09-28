# -*- coding: utf-8 -*-
# **2 つの PDF を「組版が変わったか」で比べる道具。**バイトでは比べない。
#
# 【なぜバイトで比べられないか】reportlab の `invariant` を立てている場所は 1 つも無い
# (`grep -n invariant *.py` → 0 件。2026-09-28 実測)ので、**コードを 1 バイトも変えずに 2 回作っても
# `/CreationDate`・`/ModDate`・`/ID` が変わる**(実測: 付録 1 で 64 バイト・0.028% 違う)。
# **それを知らずにバイトで比べると、日時の差を「変更のせい」だと読む。**
#
# 【なぜ `get_images()` では駄目か】**盤は埋め込み画像ではなくベクタ描画**なので、
# `page.get_images()` は **0 を返す**(実測: 付録 1 の 21 ページで 0 個)。
# 画像の数で比べる道具は、**盤が変わっても何も言わない。**
#
# 【比べ方】(1) ページ数 (2) ページごとの文字(NFKC)(3) **`get_drawings()` のベクタを、
# 座標を丸めて形の指紋にする**。3 つが一致すれば「組版は変わっていない」と言う。
#
# 使い方: `python3 -X utf8 compare_render.py <PDF A> <PDF B>`
#   rc=0 なら組版は変わっていない。rc=1 なら変わった(どのページが違うかを出す)。
#
# 出どころ: STEP CUSTOMER-EXIT (A)(索引の hook を入れても組版が変わらないことを測るために作った)。
# **scratchpad の使い捨てから格上げした**(司令塔の判断 2026-09-28)― 人間が Phase 2 で名指しした
# 「**出力再現性**」の道具になるため。**格上げの条件として変異試験をつけた**(`compare_render_test.py`)。
import hashlib
import sys
import unicodedata

# 座標を丸める桁。**丸めすぎると小さなずれを見落とす**ので、**0.5pt のずれが鳴ること**を
# `compare_render_test.py` で測ってから決めている(小数 2 桁)。
ROUND_DIGITS = 2


def norm(text):
    """P-112 と同じ流儀(抽出した文字は NFKC を通す)。"""
    return unicodedata.normalize("NFKC", text)


def drawing_signature(page):
    """ページのベクタ描画を、座標を丸めた文字列の指紋にする(盤の線・矢印が変われば変わる)。"""
    import fitz

    parts = []
    for d in page.get_drawings():
        for item in d["items"]:
            kind = item[0]
            nums = []
            for obj in item[1:]:
                if isinstance(obj, fitz.Point):
                    nums += [round(float(obj.x), ROUND_DIGITS), round(float(obj.y), ROUND_DIGITS)]
                elif isinstance(obj, fitz.Rect):
                    nums += [round(float(obj.x0), ROUND_DIGITS), round(float(obj.y0), ROUND_DIGITS),
                             round(float(obj.x1), ROUND_DIGITS), round(float(obj.y1), ROUND_DIGITS)]
                elif isinstance(obj, (int, float)):
                    nums.append(round(float(obj), ROUND_DIGITS))
            parts.append(f"{kind}:{','.join(map(str, nums))}")
    return len(parts), hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def profile(path):
    """ページごとの (文字, ベクタの本数, ベクタの指紋)。"""
    import fitz

    doc = fitz.open(path)
    try:
        return [(norm(page.get_text()),) + drawing_signature(page) for page in doc]
    finally:
        doc.close()


def differences(path_a, path_b):
    """違いの一覧(空なら組版は変わっていない)。1 行 1 件の文字列で返す。"""
    pa, pb = profile(path_a), profile(path_b)
    out = []
    if len(pa) != len(pb):
        out.append(f"ページ数が違う: {len(pa)} / {len(pb)}")
    text_diff = [i + 1 for i, (x, y) in enumerate(zip(pa, pb)) if x[0] != y[0]]
    if text_diff:
        out.append(f"文字が違うページ: {text_diff}")
    draw_diff = [i + 1 for i, (x, y) in enumerate(zip(pa, pb)) if (x[1], x[2]) != (y[1], y[2])]
    if draw_diff:
        out.append(f"ベクタ描画が違うページ: {draw_diff}")
    return out


def main(argv):
    if len(argv) != 2:
        print("使い方: python3 -X utf8 compare_render.py <PDF A> <PDF B>", file=sys.stderr)
        return 1
    diffs = differences(argv[0], argv[1])
    pa = profile(argv[0])
    if diffs:
        print(f"★組版が変わった({len(diffs)} 件):", file=sys.stderr)
        for d in diffs:
            print(f"- {d}", file=sys.stderr)
        return 1
    print(f"組版は変わっていない(ページ数 {len(pa)}・ベクタ {sum(p[1] for p in pa)} 本)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
