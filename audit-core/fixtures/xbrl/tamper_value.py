# -*- coding: utf-8 -*-
"""型 1(数字の置換): swap exactly one number's *digits* inside a document's
MD&A text block, leaving the unit word and every other byte of the ZIP
untouched.

Built for the 封 ``audit-core/docs/DETECTION_T1_T3_PLAN_2026-10-08.md`` 第 2
部(型 1). Sibling of ``tamper_unit.py`` (型 2), reusing its ZIP/MD&A
machinery rather than re-deriving it:

- :func:`tamper_unit.locate_mdna_raw` -- find the MD&A text block's raw
  (undecoded) bytes.
- :func:`tamper_unit._replace_zip_entry` -- rebuild the ZIP with one entry's
  bytes replaced, every other entry byte-identical.
- :data:`tamper_unit._NUM_LEFT_BOUNDARY_SRC` / :data:`tamper_unit._SEP_RE_SRC`
  / :func:`tamper_unit._number_text_variants` -- the same left-boundary and
  full-width/half-width matching discipline 段 4's independent monitor
  REVISE already fixed once (独立監査 1 回目). 型 1 is not re-deriving those
  fixes; it imports them.

What is new here (not in ``tamper_unit.py``):

1. :func:`is_plain_number_unit` / :func:`parse_plain_number_unit` -- decide
   whether a Claim's matched text (``digits``, from
   ``run_detection_t2.num_claim_sites``) is a plain "数字 + 単位" span
   (``adapters.xbrl.extract.NUM_RE``) or a kanji-mixed amount
   (``adapters.xbrl.extract.AMOUNT_JP_RE``, e.g. ``22億8千1百万円``). The
   latter cannot be built by a single-digit/arithmetic substitution without
   reading the kanji grouping the way the extractor does, which this module
   may not do (封 §2-2: "平文の「数字+単位」の形でない主張は混ぜられません")。
2. :func:`find_number_site` -- the number-text analogue of
   ``tamper_unit.find_unit_site``: locates the *number*'s own span (not the
   unit's), so the unit can be left untouched while the digits are replaced.
3. :func:`tamper_value` -- replace exactly that number span.
4. Layer construction (許容のすぐ外 / 1 桁だけ違う / 桁違い / 許容の内側),
   reading the real ``Contract.params`` the registered comparators
   (``adapters/xbrl/comparators.py``) use at verify time, rather than
   guessing a distance (封 §2-2).
"""

import io
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if os.path.join(ROOT, "measure") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "measure"))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from adapters.xbrl import extract as Ex  # noqa: E402
from lib import numbers as N  # noqa: E402
from lib import scales as SC  # noqa: E402

import tamper_unit as TU  # noqa: E402
from tamper_unit import (  # noqa: E402,F401
    TamperError, NoInstance, NoMdnaTextblock, AmbiguousSite,
    locate_mdna_raw, _replace_zip_entry,
)
# run_detection_t2._unit_text_variants: NFKC の両形(％/%)を試す(``digits``
# は Adapter 自身の NFKC 済みの文から取るので unit="%" でも raw HTML は
# "％" のままかもしれない -- 読むだけ、書き換えない)。
import run_detection_t2 as T2  # noqa: E402

# 参照一覧との偶然一致を調べるときの許容(浮動小数の丸め誤差だけを吸収する)。
_COLLIDE_TOL = 1e-6

# run_detection_t2._unit_text_variants は NFKC(全角 -> 半角)しかできない。
# 「％」は NFKC で「%」に畳まれる(unicodedata.normalize("NFKC","％")=="%")
# ので、半角の unit="%" から逆に全角形を作る写像が無いと、raw HTML がまだ
# 全角「％」のままの場所を見失う(実測 2026-10-08: S100Z4B6 の「0.3％増」等、
# ％ を使うサイトが全件 0 件になった)。tamper_unit.py の数字側の
# ``_HALF_TO_FULLWIDTH`` と対になる、単位側の最小の逆写像。
_UNIT_HALF_TO_FULLWIDTH = {"%": "％"}


class CannotClassify(TamperError):
    """``digits`` is neither a plain NUM_RE span nor something this module
    recognises (should not happen if ``digits`` really came from
    ``run_detection_t2.num_claim_sites``; raised instead of guessing)."""


def is_plain_number_unit(digits):
    """True when ``digits`` (the full matched text of a 数の Claim, as
    ``run_detection_t2.num_claim_sites`` records it) is a plain "数字 + 単位"
    span -- i.e. ``adapters.xbrl.extract.NUM_RE`` matches the *whole* string,
    not just a prefix. A kanji-mixed amount (``AMOUNT_JP_RE``, e.g.
    ``22億8千1百万円``) never fullmatches ``NUM_RE`` (it carries 億/千/百/万
    characters NUM_RE's unit alternation does not contain), so this is
    sufficient to tell the two apart without importing ``AMOUNT_JP_RE``
    itself."""

    return Ex.NUM_RE.fullmatch(digits) is not None


def parse_plain_number_unit(digits):
    """Split a plain ``digits`` span into ``(sign, number_text, unit)``.

    ``number_text`` excludes the sign (``△``/``▲``/``－``/``-``/``マイナス``)
    -- the same convention ``measure/lib/numbers.py``'s own scanner uses, and
    the one :func:`find_number_site` / :func:`tamper_unit.find_unit_site`
    both search for. Raises :class:`CannotClassify` if ``digits`` is not a
    plain span (call :func:`is_plain_number_unit` first)."""

    m = Ex.NUM_RE.fullmatch(digits)
    if m is None:
        raise CannotClassify("not a plain number+unit span: %r" % (digits,))
    sign = m.group(1)
    number_text = m.group(2) + (m.group(3) or "")
    unit = m.group(4)
    return sign, number_text, unit


def find_number_site(inner, number_text, unit):
    """Locate the single occurrence of ``number_text`` immediately (modulo a
    run of spaces) followed by ``unit`` inside ``inner`` (raw, undecoded
    bytes of the MD&A text block) -- the number-text analogue of
    :func:`tamper_unit.find_unit_site`.

    Reuses ``tamper_unit``'s left-boundary regex source
    (``_NUM_LEFT_BOUNDARY_SRC``) and separator (``_SEP_RE_SRC``) and its
    half-width/full-width expansion (``_number_text_variants``) so the two
    modules' notion of "the same number, however written" never drifts
    apart.

    Returns ``(num_start, num_end, unit_start, unit_end)``. Raises
    :class:`tamper_unit.AmbiguousSite` (carrying ``match_count``) when the
    pairing occurs 0 or 2+ times (counting both width forms together)."""

    num_alt = "|".join(re.escape(v) for v in TU._number_text_variants(number_text))
    unit_variants = sorted(set(T2._unit_text_variants(unit)) | {_UNIT_HALF_TO_FULLWIDTH.get(unit, unit)})
    unit_alt = "|".join(re.escape(v) for v in unit_variants)
    pat = re.compile(
        TU._NUM_LEFT_BOUNDARY_SRC + r"(" + num_alt + r")" + TU._SEP_RE_SRC + r"(" + unit_alt + r")"
    )
    matches = list(pat.finditer(inner))
    if len(matches) != 1:
        raise AmbiguousSite(
            "expected exactly 1 occurrence of %r + unit %r (variants %r) inside the MD&A text block, found %d"
            % (number_text, unit, unit_variants, len(matches)),
            len(matches),
        )
    m = matches[0]
    num_start, num_end = m.start(1), m.end(1)
    unit_start, unit_end = m.start(2), m.end(2)
    return num_start, num_end, unit_start, unit_end


def tamper_value(zb, number_text, unit, new_number_text):
    """Return new ZIP bytes where, inside the MD&A text block only, the one
    occurrence of ``number_text`` + ``unit`` has its *number* replaced by
    ``new_number_text``. The unit word is copied through byte-for-byte
    unchanged. Every other byte of every other ZIP entry is unchanged.

    Raises :class:`NoInstance` / :class:`NoMdnaTextblock` / :class:`AmbiguousSite`
    instead of guessing."""

    entry, raw, start, end, _local = locate_mdna_raw(zb)
    inner = raw[start:end]
    num_start, num_end, _unit_start, _unit_end = find_number_site(inner, number_text, unit)
    new_inner = inner[:num_start] + new_number_text + inner[num_end:]
    new_raw = raw[:start] + new_inner + raw[end:]
    return _replace_zip_entry(zb, entry, new_raw.encode("utf-8"))


# ---------------------------------------------------------------------------
# 許容を params から読む(封 §2-2: 推測しない)。
# ---------------------------------------------------------------------------

def tolerance_base_of(params):
    """``(tolerance_base, source)`` from a Contract's ``params`` (see
    ``adapters/xbrl/comparators.py``):

    - ``abs_tolerance`` present (名/人 の equals_within 分岐):
      ``tolerance_base = abs_tolerance``。
    - ``claim_scale`` present(金額の equals_within / diff(a-b) equals_within):
      ``tolerance_base = 0.5 * claim_scale``(``vocabulary.tol_of`` と同じ式。
      ``equals_within``/``diff_ab_equals_within`` 自身は ``_match_value`` の
      round 分岐 ``abs(fv-t) <= claim_scale/2`` で実装されている -- 同じ数)。
    - ``tolerance`` present(割合: ``equals_within(pure*100)`` /
      ``ratio*100`` / ``pct_change`` / ``diff(a-b)(pure*100)``):
      ``tolerance_base = tolerance``(0.15、``recipes.py:659/671``)。
    - どれも無ければ ``(None, "unreadable")``(主張を落とす。推測しない)。
    """

    if not params:
        return None, "unreadable"
    if params.get("abs_tolerance") is not None:
        return float(params["abs_tolerance"]), "abs_tolerance"
    if params.get("claim_scale") is not None:
        return 0.5 * float(params["claim_scale"]), "claim_scale"
    if params.get("tolerance") is not None:
        return float(params["tolerance"]), "tolerance"
    return None, "unreadable"


def doc_to_base_scale(params):
    """書かれた数の 1 単位が、許容と同じ単位系(金額なら円)で何に当たるか。

    ``claim_scale``(あれば)がそのまま倍率になる -- 金額の NUM_RE 経路
    (千円/百万円/億円/兆円)では ``claim_scale == unit_scale`` なので
    一致するが、**漢数字混じりの「百万」1 区切りだけの書き方**(例:
    「149百万円」のようにカンマが無いせいで ``extract.AMOUNT_JP_RE`` の
    百+万の組で読まれる場合、``claim.unit`` は内部で「円」、``value`` は
    既に base 円 ― 149000000 ― になっている。このとき ``params`` の
    ``unit_scale`` は 1.0 のまま(円の直接指定と区別が無い)だが
    ``claim_scale`` は正しい倍率(1000000.0)を持つ(実測 2026-10-08:
    S100YMFV の N035 等。``unit_scale`` で割る前の版は、層 (a')/(a) の
    書き戻しが「149」を「149500000」のような桁違いの文字列に壊した)。
    割合(``tolerance`` のみ)・abs_tolerance(名/人)には ``claim_scale``
    が無く、書かれた値がそのまま base なので 1.0。"""

    if not params:
        return 1.0
    v = params.get("claim_scale")
    return float(v) if v is not None else 1.0


def written_value_of(number_text):
    """``number_text``(カンマ・小数点はそのまま、符号は無し)が表す、
    **原文の単位での**値(符号なし)。``Claim.value``(型によっては既に
    base 単位へ変換済み ― :func:`doc_to_base_scale` の docstring 参照)
    ではなく、必ず「書かれた文字」から読む。層の加算・レンダリングは
    常にこちらを使う(``Claim.value`` を使うと、漢数字混じりの「百万」
    1 区切りの現場で桁が壊れる)。"""

    return float(number_text.replace(",", ""))


def ndecimals_of(number_text):
    """``number_text`` の小数点以下の桁数(無ければ 0)。"""

    if "." in number_text:
        return len(number_text.split(".", 1)[1])
    return 0


def step_base_of(number_text, params):
    """原文で書き換えられる最小の幅(許容と同じ単位系 -- 金額なら円)。

    最後の書かれた桁を 1 変える(= 10**-ndecimals、原文の単位での 1 ステップ)
    を、:func:`doc_to_base_scale` で base 側に変換したもの。"""

    nd = ndecimals_of(number_text)
    return (10.0 ** (-nd)) * doc_to_base_scale(params)


def layer_a_delta_doc(number_text, params):
    """層 (a) 許容のすぐ外: 許容を**ちょうど超える**最小の幅を、原文の単位
    で返す(正の数、常に加算)。許容・step が読めなければ ``None``。"""

    tol, _src = tolerance_base_of(params)
    if tol is None:
        return None
    step = step_base_of(number_text, params)
    if step <= 0:
        return None
    n = math.floor(tol / step) + 1
    return n * (10.0 ** (-ndecimals_of(number_text)))


def layer_aprime_delta_doc(number_text, params):
    """層 (a') 許容の内側: 許容を**超えない**、かつ 0 でない最小の幅を、
    原文の単位で返す。作れなければ ``None``(件数で報告する -- 推測しない)。"""

    tol, _src = tolerance_base_of(params)
    if tol is None:
        return None
    step = step_base_of(number_text, params)
    if step <= 0:
        return None
    m = math.floor(tol / step)
    if m < 1:
        return None
    return m * (10.0 ** (-ndecimals_of(number_text)))


LAYER_C_MULTIPLIER = 10.0


class _Like(object):
    """``measure/lib/numbers.py: render_value`` が読む最小の形(``.text``・
    ``.has_frac``・``.has_comma``)。本物の ``NumberToken`` を作らずに済ませる
    ための、この計器限りの軽い代わり。"""

    __slots__ = ("text", "has_frac", "has_comma")

    def __init__(self, text, has_frac, has_comma):
        self.text = text
        self.has_frac = has_frac
        self.has_comma = has_comma


def render_like(value, number_text):
    """``value`` を ``number_text`` と同じ見た目(カンマ・小数桁数)で書き起こす。
    ``measure/lib/numbers.py: render_value`` を使い回す(作り直さない)。"""

    like = _Like(number_text, has_frac=("." in number_text), has_comma=("," in number_text))
    return N.render_value(value, like)


def layer_b_new_text(number_text, rng):
    """層 (b) 1 桁だけ違う: 数字の 1 桁を、種で決めた別の数字に替える。

    カンマ・小数点はそのまま、数字の文字だけを対象にする。先頭の桁(整数部が
    2 桁以上のときに限る)を「0」に変えることは選ばない(「029,331」のような
    不自然な先頭 0 を避ける)。候補が尽きたら ``None``(作れない -- 件数で
    報告する)。"""

    digit_positions = [i for i, ch in enumerate(number_text) if ch.isdigit()]
    if not digit_positions:
        return None
    int_part = number_text.split(".", 1)[0]
    multi_digit_int = len(int_part.replace(",", "")) > 1

    order = list(digit_positions)
    rng.shuffle(order)
    for pos in order:
        orig = number_text[pos]
        cands = [d for d in "0123456789" if d != orig]
        if pos == 0 and multi_digit_int:
            cands = [d for d in cands if d != "0"]
        if not cands:
            continue
        new_digit = cands[rng.randrange(len(cands))]
        return number_text[:pos] + new_digit + number_text[pos + 1:]
    return None


def collides_with_reference(signed_value, unit, refs, tol=_COLLIDE_TOL):
    """True when ``signed_value``(``unit`` で書かれた、原文の単位のまま)が、
    桁を掛けた値(``lib.scales.scaled_value``、金額は円へ。割合・名/人 は
    素通し)で参照一覧のどれかと一致する(= 型 5 になってしまう置換値)。"""

    target = SC.scaled_value(signed_value, unit)
    for r in refs:
        rv = SC.scaled_value(r.get("value"), r.get("unit"))
        if rv is None:
            continue
        if abs(rv - target) <= tol:
            return True
    return False
