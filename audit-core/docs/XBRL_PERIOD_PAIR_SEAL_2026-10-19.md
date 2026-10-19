# 封: 期間の対を engine が引く(PP)― **率の主張を参照先 1 本で検算する。実装より先に封じる**

2026-10-19。人間の指示(2026-10-19、原文): 「**システムの価値そのものを向上させてね**」。
価値の定義は売却戦略 §1 の読み(「誤りを通さない・保留を返す・全件に理由と記録・測った道具」)に従い、
**この封は「実証できる行の割合」を上げる**(いま contract v1 は率の主張を**参照先 2 本**でしか検算できず、
席が当期の fact 1 本を名指した率の主張 17 行は全部 `UNPROVABLE` のまま。`docs/XBRL_PERIOD_UNIT_HOLD_RESULT_2026-10-19.md` §2-1)。
**0 USD・席は呼ばない。**段 1 は `measure/`(engine 不変)、段 2 は製品の経路(engine 変更。独立監査 GO の後に commit)。

---

## §0 規則(**実装者が 1 通りに書ける字で**)

**PP(period pair)**: 主張の種類が率(`ratio_change`。単位 `％`/`%`)で、参照先が **1 本**、それが解けた fact `f` の枠の
期間の札(`context` の `_` より前)が `CurrentYear*` のとき:

1. **前期の兄弟** = 同じ `name`、同じ `dim_of(context)`(`_` より後)、期間の札が `CurrentYear` → `Prior1Year` に置き換わった枠の fact。
2. 兄弟が **ちょうど 1 本**なら、参照先を `(f, 兄弟)` の 2 本に**機械で補い**、既存の比較器 `pct_change(cur,prior)`(許容 `PCT_TOLERANCE_DEFAULT = 0.15`。新しい閾値は作らない)で検算する。
   **0 本・2 本以上なら `UNPROVABLE`、理由 `prior_sibling:<本数>`**(どれを選ぶかを機械で決めない)。
3. **符号**: 主張の数の直後(字面の 8 字以内)に **増・伸・上回** が在れば `+`、**減・下回・落ち** が在れば `−`、どちらも無ければ**符号不明**。
   符号が在れば符号つきで比較(`pct_change` は符号つき)。符号不明なら**絶対値**で比較し、応答の `unchecked` に「方向」を足す。
4. PP が補った 2 本目は応答の `derived_pointers` に**別欄で**書く(席が名指した参照先 `pointers` は変えない)。
5. 既存の保留規則 (d)・P・U は **PP の後に**当期の fact `f` に対して従来どおり当てる。

当たる例: `netsales@CurrentYearDuration` を名指した「前期比 3.7％減」 → 兄弟 `netsales@Prior1YearDuration` 1 本 → `pct_change` → 符号 `−`。
当たらない例: 兄弟が `Prior1YearDuration` と `Prior1YearDuration_XMember` の 2 本(次元が違う) → `dim_of` が違うので 1 本。
当たらない例: 期間の札が `Prior1YearDuration` の fact を名指した主張 → PP は当てない(当期でない)。

**触らないもの**: 率の主張で参照先 2 本の経路(v1 のまま)・金額の主張・方向だけの主張(数が付かない。別の封)。

## §1 材料と分母(**字で留める**。下見で形だけ見た数は「下見」と明記)

| | 数 | 出どころ |
|---|---|---|
| 192 行(8 書類、注入後) | 192 | `fixtures/xbrl/cd8/period_unit_hold_2026-10-19.json` の `rows` |
| うち率の主張(`％`/`%`) | **37** | 同(下見 2026-10-19: 単位で数えた) |
| 率で席が参照先を 1 本名指した行 | **17** | `docs/XBRL_PERIOD_UNIT_HOLD_RESULT_2026-10-19.md` §2-1(全部 `UNPROVABLE`) |
| 率で参照先なし | 20 | 下見 |
| 17 行の前期の兄弟の本数(下見) | 1 本: **13**・2 本: **4**・0 本: 0 | 下見 2026-10-19(形だけ。検算はしていない) |
| 許容 | 0.15 pt | `adapters/xbrl/recipes.py` `PCT_TOLERANCE_DEFAULT` |

**下見で見たのは兄弟の本数だけ**。符号の字・検算の一致・対照はこの封の後に測る。

## §2 対照(**故障を作って当てる。1 回に 1 件**。兄弟 1 本の 13 行すべて)

| 注入 | 作り方 | 期待 |
|---|---|---|
| 値 | 主張の値に +1.0 pt | `VALUE_MISMATCH` |
| 符号 | 増 ↔ 減 を入れ替える | `VALUE_MISMATCH`(符号つき比較が効く) |
| 前期を消す | 前期の兄弟 fact を材料から除く | `UNPROVABLE` `prior_sibling:0` |
| 前期を増やす | 同じ名・同じ次元・前期の枠にもう 1 本(値を +1)足す | `UNPROVABLE` `prior_sibling:2` |

## §3 事前予測(**実装前に固定。外れは外れとして残す**)

| | 予測 | **外れ方** |
|---|---|---|
| **H-1** | 17 行のうち PP が兄弟 1 本で検算に進むのは **13**、`prior_sibling:2` で止まるのは **4**、`prior_sibling:0` は **0** | 1 行でも違う(下見の数え間違い) |
| **H-2** | 13 行の符号の字: 増/減 のどちらかが **13 / 13** で取れる(符号不明 0) | 1 行でも符号不明 |
| **H-3** | 13 行の検算: `GROUNDED` **12**・`VALUE_MISMATCH` **1**(`S100YWGX` R017「セグメント利益 258.0％増」。席の参照先は `OrdinaryIncome` のセグメント枠で、再計算は 263.6 付近) | 数が違う |
| **H-4** | R017 の不一致の原因: 文の「セグメント利益」に当たる**別の要素**(`SegmentProfit…`/`OperatingIncome…` の同じセグメント枠)が instance に在り、そちらで 258.0 が再現する | 別の要素が無い / 在っても 258.0 にならない |
| **H-5** | 対照 値 **13 / 13** が `VALUE_MISMATCH` | 1 件でも通す |
| **H-6** | 対照 符号 **13 / 13** が `VALUE_MISMATCH` | 1 件でも通す(= 符号を見ていない) |
| **H-7** | 対照 前期を消す **13 / 13** が `UNPROVABLE` `prior_sibling:0` | 1 件でも違う |
| **H-8** | 対照 前期を増やす **13 / 13** が `UNPROVABLE` `prior_sibling:2` | 1 件でも違う |
| **H-9** | 率で参照先なしの 20 行と、金額の主張 155 行の state は **1 行も動かない** | 1 行でも動く |
| **H-10** | 13 行で (d)・P・U の発火は **0**(前期の兄弟は P の「同額」ではない) | 1 行でも発火 |
| **H-11** | 実証できた行(`GROUNDED` + `VALUE_MISMATCH`)は 192 行で **62 → 75**(v1 の 18 + 44 = 62 に 13 を足す) | 数が違う |
| **H-12** | 段 2(製品の経路)の 192 行再現は段 1 の記録と **192 / 192** 一致、既存 `verify_document` の出力は `engine` の欄以外 byte 同一 | 1 行でも違う / 他の欄が動く |
| **H-13** | 変異(段 2): PP-R1 符号を見ない / PP-R2 兄弟 2 本でも先頭を選ぶ / PP-R3 次元違いの前期も兄弟に数える ― **3 本とも red** | 1 本でも沈黙 |
| **H-14** | 独立監査は **REVISE 1 回 → GO** | 0 回 / 2 回以上 / HUMAN |
| **H-15** | 段 2 の commit の後の `run_tests.sh` 1 回目で赤くなる過去の門は **`test_xbrl_axis3_decision.py` test_9 の 1 本だけ**(§5 で列挙済み)。追記の後 2 回目 rc=0 | 他の門が赤 / 2 回目も赤 |

**本当に測っているのは H-3〜H-8 である。**H-1 は下見の確認。

## §4 言えないこと

1. **同じ 8 書類である。**規則 × 標本の積で、新しい書類で 13 が 13 である保証は無い(`memory: diagnosis-does-not-transfer-to-a-new-sample`)。
2. **「前期比」の字は見ない。**前年同期比(四半期)・2 期前比は annual の有報に出ないとして扱い、出たら誤って `Prior1Year` と対にしうる(限界として記録)。
3. **方向だけの主張(数が付かない 52 行の型)は触らない。**PP の符号の規則はそちらの土台になるが、測るのは別の封。
4. **PP は「席が当期を正しく名指した」ことを前提にする。**名指しの誤り(要素の取り違え T5)は PP では検出できない(R017 が示す型)。

## §5 変更する file

段 1(engine 不変): `measure/xbrl_period_pair_rule_2026-10-19.py`(規則)・`measure/xbrl_period_pair_2026-10-19.py`(測定)・
記録 `fixtures/xbrl/cd8/period_pair_2026-10-19.json`・`docs/XBRL_PERIOD_PAIR_RESULT_2026-10-19.md`・
門 `tests/measure/test_period_pair_rule.py`・`tests/measure/test_xbrl_period_pair_result.py`・覆いの記録 2 本。
段 2(engine): `adapters/xbrl/holds.py` に `prior_siblings`、`adapters/xbrl/verify_external.py` に PP(`derived_pointers`・`unchecked` の「方向」)、
`tests/adapters/xbrl/test_holds.py`・`test_verify_external.py`・`mutations.json`(PP-R1〜R3)・`test_mutations.py`(scope は `holds` のまま)・
`fixtures/frozen_bundle_sha.py`(世代 +1)・覆いの記録 2 本・結果の追記。**これ以外に触らない。**
`core/py/` は 0 行。
**過去の門との衝突(封の時点で列挙。③ で 4 本が後から赤くなった型を繰り返さない)**: 段 2 の commit が履歴に乗ると
`tests/measure/test_xbrl_axis3_decision.py` の `LATER_ENGINE_COMMITS` に**その commit を 1 行足す**(10-14 の値は消さない)。
`test_xbrl_cd_seal.py` の `FROZEN`(`instance.py` の sha)・`test_verify_external_v1.py` test_25/26 は段 2 が `instance.py`・境界一覧を触らないので動かない(予測 H-15: 段 2 の `run_tests.sh` 1 回目で赤くなるのは axis3 の test_9 だけ。他が赤なら外れ)。

## §6 やること(順)

1. 段 1 の規則と測定・記録・結果 → 2. 門(変異で赤を確認) → 3. 段 2 の実装・変異 3 本 → 4. `run_tests.sh` → 5. 独立監査 → 6. commit(GO の後。段 1・段 2 は別 commit)。

---

## 追記 1(2026-10-19、段 1 の結果の後。**本文は書き換えない**)

段 1(`docs/XBRL_PERIOD_PAIR_RESULT_2026-10-19.md`)で、H-1 の「兄弟 2 本」の 4 行は**次元違いではなく instance 内の重複**
(同じ `name`・同じ `context` の fact が 2 回出る。`S100YWGX` R004 など)だった。§0 の字は「fact の本数」なので 4 行は `prior_sibling:2` で止まった。
これは「どれを選ぶかを機械で決めない」の趣旨(値が違う候補から選ばない)とは別の形で、③ の `verify_external._fact_of` が
重複を「instance の並びで先頭」と扱うのとも揃っていない。

**段 2 で足す規則(PP-2)**: 前期の兄弟のうち **同じ `context` の fact は、値が全部同じなら 1 本に数える**(値が 1 つでも違えば本数のまま。理由は `prior_sibling:<本数>` に加えて `duplicate_values` を付ける)。
当期側の重複は ③ と同じく先頭(席が名指した枠)。

| | 予測(段 2) | **外れ方** |
|---|---|---|
| **H-16** | 重複の 4 行は値が全部同じで、PP-2 の後は兄弟 **1 本**になる(4 / 4) | 値が違う行が在る |
| **H-17** | その 4 行の検算は `GROUNDED` **3〜4**・`VALUE_MISMATCH` **0〜1**。実証できた行は 75 → **79** | 幅の外 |
| **H-18** | 段 1 の 13 行の state・reason・recomputed は PP-2 で **1 行も変わらない** | 1 行でも変わる |
| **H-19** | 対照「前期を増やす」(値 +1 の複製)は PP-2 の後も **13 / 13** が `UNPROVABLE`(値が違うので 2 本のまま) | 1 件でも通す |

段 2 の変異に **PP-R4: 値が違う重複も 1 本に数える** を足す(予測 red)。H-13 は 3 本 → **4 本とも red**。
