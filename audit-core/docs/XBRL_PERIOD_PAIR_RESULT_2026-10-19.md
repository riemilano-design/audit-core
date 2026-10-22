# 期間の対(PP)の実測 ― **予測 当たり 9 / 外れ 2(段 1の 11 欄)**

2026-10-19。封 `docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md`(commit `790a5c5`。実装より先)。
**段 1(engine 不変)。0 USD・席は呼んでいない。**正本は `fixtures/xbrl/cd8/period_pair_2026-10-19.json`。

---

## §1 判定

192 行のうち率の主張(単位 `％`/`%`)は **37 行**。席が参照先を**1 本**名指した行は **17 行**、
参照先なしは **20 行**。17 行に PP(前期の兄弟)を当てた結果:

| 兄弟の本数 | 行数 |
|---|---|
| 1 本 | **13** |
| 2 本 | **4** |
| 0 本 | 0 |

**2 本の 4 行は、次元の違う兄弟が 2 つあるのではなく、instance 内の重複
(同じ `name`・同じ `context` の fact が 2 回出る)である**(例 `S100YWGX` R004。
`jppfs_cor:NetSales@Prior1YearDuration` が同じ値で 2 回出現する)。PP は重複の判定をしない
(どれを選ぶかを機械で決めないので、2 本も `UNPROVABLE` になる)。

13 行の符号は**全部**抜粋の数の直後 8 字以内から取れた(符号不明 0)。

| doc | id | 値 | 符号 | state | recomputed |
|---|---|---|---|---|---|
| S100YWGX | R011 | 8.0 | 増 | GROUNDED | 8.01 |
| S100YWGX | R013 | 19.1 | 増 | GROUNDED | 19.11 |
| S100YWGX | R015 | 18.8 | 増 | GROUNDED | 18.81 |
| **S100YWGX** | **R017** | **258.0** | 増 | **VALUE_MISMATCH** | **263.64** |
| S100YZCT | R003 | 8.0 | 増 | GROUNDED | 7.99 |
| S100YZCT | R007 | 4.9 | 増 | GROUNDED | 4.86 |
| S100YZCT | R009 | 11.0 | 増 | GROUNDED | 11.03 |
| S100YYRV | R014 | 3.7 | 減 | GROUNDED | -3.66 |
| S100YYRV | R016 | 35.2 | 減 | GROUNDED | -35.21 |
| S100YZEV | R010 | 17.7 | 減 | GROUNDED | -17.66 |
| S100YZEV | R012 | 75.9 | 減 | GROUNDED | -75.88 |
| S100YZEV | R014 | 73.8 | 減 | GROUNDED | -73.75 |
| S100YZEV | R016 | 72.4 | 減 | GROUNDED | -72.41 |

**12 / 13 が検算一致(`GROUNDED`)。**残り 1 行(`S100YWGX` R017)は `VALUE_MISMATCH`
(主張 258.0 に対し再計算 263.64)。

### §1-1 `S100YWGX` R017 の明細(H-4)

席の参照先は `jppfs_cor:OrdinaryIncome`(セグメント枠。値 160,000,000 円。前期 44,000,000 円。
再計算 263.64)。文は「セグメント利益160百万円(前連結会計年度比258.0％増)」で、
**160百万円は `OrdinaryIncome` の当期値と一致する**。**同じセグメント枠(`dim_of` が同じ)で
`name` に `SegmentProfit` か `OperatingIncome` を含む fact は 0 件。**
「セグメント利益」はこの書類の taxonomy では別名でなく `OrdinaryIncome` そのもので表現されており、
**258.0 と 263.64 の食い違いは要素の取り違えではない**(原因は測っていない。限界として記録)。

---

## §2 対照(**13 行すべて。故障を作って当てた**)

| 注入 | 13 行の結果 |
|---|---|
| 値 +1.0 pt | **`VALUE_MISMATCH` 13 / 13** |
| 符号の入替(増 ↔ 減) | **`VALUE_MISMATCH` 13 / 13** |
| 前期を消す | **`UNPROVABLE` `prior_sibling:0` 13 / 13** |
| 前期を増やす | **`UNPROVABLE` `prior_sibling:2` 13 / 13** |

**4 種どれも 13/13 で期待どおり**(封 §2)。

---

## §3 当てた行数(H-9)・保留規則との関係(H-10)・実証できた行(H-11)

- **率で参照先なし 20 行・金額の主張 155 行は PP を当てていない**(当てた行数 0)。
- **13 行の当期 fact に `adapters.xbrl.holds.apply_holds` を当てると、発火は `d` 1・`P` 0・`U` 0。**
  `d` が発火したのは `S100YYRV` R014 の `jppfs_cor:NetSales@CurrentYearDuration`
  (`jppfs_cor:NetSales@CurrentYearDuration_TotalOfReportableSegmentsAndOthersMember` と同額)。
  **`P` が 0 件なのは予測どおり**(前期の兄弟は値が違うので「同額の期間兄弟」ではない)。
- **実証できた行(`GROUNDED` + `VALUE_MISMATCH`)は 192 行で 62 → 75。**
  (`fixtures/xbrl/cd8/period_unit_hold_2026-10-19.json` の `**合成の後**` の `GROUNDED` 18 +
  `VALUE_MISMATCH` 44 = 62 に、13 行(`GROUNDED` 12 + `VALUE_MISMATCH` 1)を足す。)

---

## §4 予測との照合(**封は書き換えない**)

| | 予測 | 実測 | |
|---|---|---|---|
| H-1 | 13・4・0 | 1 本: 13・2 本: 4・0 本: 0 | **当たり** |
| H-2 | 13 / 13 で符号が取れる | 13 / 13 | **当たり** |
| H-3 | GROUNDED 12・VALUE_MISMATCH 1(S100YWGX R017) | GROUNDED 12・VALUE_MISMATCH 1 | **当たり** |
| **H-4** | 別の要素(SegmentProfit/OperatingIncome)が在り 258.0 が再現する | **同じセグメント枠に該当する別の要素 0 件** | **外れ** |
| H-5 | 対照 値 13/13 が VALUE_MISMATCH | 13/13 | **当たり** |
| H-6 | 対照 符号 13/13 が VALUE_MISMATCH | 13/13 | **当たり** |
| H-7 | 対照 前期を消す 13/13 が UNPROVABLE prior_sibling:0 | 13/13 | **当たり** |
| H-8 | 対照 前期を増やす 13/13 が UNPROVABLE prior_sibling:2 | 13/13 | **当たり** |
| H-9 | 参照先なし 20 行・金額の主張 155 行は 1 行も動かない | 当てた行数 0(20 行・155 行とも) | **当たり** |
| **H-10** | 13 行で (d)・P・U の発火は 0 | **d 1・P 0・U 0** | **外れ** |
| H-11 | 実証できた行(GROUNDED + VALUE_MISMATCH)は 192 行で 62 → 75 | 62 → 75 | **当たり** |
| H-12 | 段 2 の 192 行再現は段 1 の記録と 192/192 一致・engine の欄以外 byte 同一 | ― | **段 2 で測る** |
| H-13 | PP-R1〜R3 の 3 本とも red | ― | **段 2 で測る** |
| H-14 | 独立監査は REVISE 1 回 → GO | ― | **段 2 で測る** |
| H-15 | run_tests.sh 1 回目で赤くなるのは `test_xbrl_axis3_decision.py` test_9 だけ | ― | **段 2 で測る** |

**当たり 9 / 外れ 2(段 1 の 11 欄。H-12〜H-15 は段 2 で測る)。**

- **H-4 外れ**: 「別の要素が在り 258.0 が再現する」と書いたが、同じセグメント枠に
  `SegmentProfit`/`OperatingIncome` を含む要素は 0 件だった。**「セグメント利益」はこの
  taxonomy では `OrdinaryIncome` 自身で表現されており、別名の要素は存在しない。**
  258.0 と再計算 263.64 の食い違いの原因(丸め・報告書側の計算方法など)は測っていない。
  **封は直さない。**
- **H-10 外れ**: 「発火は 0」と書いたが、13 行のうち 1 行(`S100YYRV` R014)で
  (d) が発火した(次元兄弟に同額の fact が実在した)。**P が 0・U が 0 は予測どおり**で、
  外れたのは (d) の本数だけ。**封は直さない。**

---

## §5 言えないこと

1. **同じ 8 書類である。**規則 × 標本の積で、新しい書類で 13 が 13 である保証は無い。
2. **「前期比」の字は見ない。**前年同期比(四半期)・2 期前比は annual の有報に出ないとして扱い、
   出たら誤って `Prior1Year` と対にしうる。
3. **方向だけの主張(数が付かない 52 行の型)は触らない。**PP の符号の規則はそちらの土台になるが、
   測るのは別の封。
4. **PP は「席が当期を正しく名指した」ことを前提にする。**名指しの誤り(要素の取り違え T5)は
   PP では検出できない(R017 が示す型)。
5. **精度は上げていない。**実証できる行が増えただけで、**誤りを通す率は対照でしか測っていない**
   (13 行すべてで値・符号の注入が `VALUE_MISMATCH` になることは確かめたが、実データで PP が
   誤った参照先を通した件数は測っていない)。

---

## 段 2(engine。2026-10-20)

段 2 の engine 変更そのものは commit `ac8c3ff`(独立監査 GO。報告 `scratchpad/step5/audit_stage2.md`)で
既に commit 済み。**この節は、その commit の後に行った測定の追記であり、段 1 の本文(上)は 1 字も書き換えない。**
測定 script `measure/xbrl_period_pair_stage2_2026-10-19.py`、記録 `fixtures/xbrl/cd8/period_pair_stage2_2026-10-19.json`。
製品の経路(`adapters.xbrl.verify_external.verify_external(..., period_pair=True)`、既定)に ③ と同じ材料の
組み立て(192 行)を通し、段 1 の記録(13 行・重複 4 行)と ③ の記録(残り 175 行)に突き合わせた。
**engine は 1 行も変えていない(読むだけ)。**0 USD・席は呼ばない。

### §6 判定(実測)

- **段 1 の 13 行(兄弟 1 本)**: 段 1 の記録(state・reason・recomputed・derived_pointers・sign_checked)
  との一致は **12 / 13**。不一致の 1 行は `S100YYRV` `R014`
  (段 1: `GROUNDED`・`recomputed -3.66` → 段 2: `UNPROVABLE`・理由 `ambiguous_dimension:1`)。
  **原因は段 1 自身が既に記録していた発火** ― §3「13 行で (d)・P・U の発火」で
  「`d` が発火したのは `S100YYRV R014`」と書かれており、段 1 の測定(`apply_pp` のみ)は
  その発火を `state` に反映していなかった。段 2(製品の経路)は PP の後に `holds.apply_holds` を
  当てるため、**同じ発火がそのまま `state` に出た。**挙動の後退ではなく、段 1 が測っていなかった
  (d) の効果が、engine に統合されて初めて `state` に反映された。
- **重複 4 行(段 1 で兄弟 2 本。PP-2 の対象)**: 4 / 4 が `holds.prior_siblings` で兄弟 1 本に
  (`duplicate_values: false`)。検算の `state` は **`GROUNDED` 3・`UNPROVABLE` 1**
  (`S100YWGX` `R008`、理由 `ambiguous_dimension:2`。(d) の発火)。
- **他 175 行**(率で参照先なし 20 行 + 金額 155 行): ③ の記録 `period_unit_hold_2026-10-19.json` の
  `**合成の後**` と **175 / 175 一致**。
- **対照(13 行すべて。1 回に 1 件)**: 値 +1.0 pt → `VALUE_MISMATCH` 13/13。符号の入替 → `VALUE_MISMATCH` 13/13。
  前期を消す → `UNPROVABLE` `prior_sibling:0` 13/13。前期を増やす(値 +1 の複製)→
  `UNPROVABLE` `prior_sibling:2;duplicate_values` 13/13。
- **実証できた行**(段 1 と同じ定義。`GROUNDED` + `VALUE_MISMATCH`): 175 行で 62、17 行(PP、段 2)で 15
  (13 行グループ 12 + 重複 4 行グループ 3)。合計 **62 + 15 = 77**(段 1 の 75 から +2。
  §3 の H-17 が見込んだ +4 ではなく、重複 4 行のうち 1 行が (d) で `UNPROVABLE` になった分だけ少ない)。
- **変異**: `PP-R1`(符号を見ない)・`PP-R2`(兄弟 2 本でも先頭を選ぶ)・`PP-R3`(次元違いの前期も数える)・
  `PP-R4`(値の違う重複も 1 本に数める)の **4 本とも red**。
- **独立監査**: `ac8c3ff` の trailer は `独立監査: GO`。**REVISE の回数は機械で測った数ではなく、
  司令塔からの引き継ぎの字 `REVISE 0 回 → GO` をそのまま写した。**
- **`run_tests.sh` 1 回目**: `scratchpad/step5/run_tests_step5.log`(session-local。1,923 行。
  このSTEPの直し(`LATER_ENGINE_COMMITS` への追記)より前に走らせたもの)で
  `pytest -q` は `3327 passed, 5 skipped in 1685.15s`、`unittest discover` は
  `Ran 3236 tests`・`FAILED (failures=1, skipped=5)`、その 1 件は
  `FAIL: test_9_the_engine_was_not_touched (tests.measure.test_xbrl_axis3_decision.Axis3Test)`
  だけだった(ログの `grep` で確認)。**このSTEPで `LATER_ENGINE_COMMITS` に `ac8c3ff` を足した後、
  `tests/measure/test_xbrl_axis3_decision.py` は 11 passed**(2 回目に相当する確認。
  全数の `run_tests.sh` を 2 回目として回し直してはいない)。

### §7 予測との照合(H-12〜H-19。**封は書き換えない**)

| | 封・追記1 の字 | 実測 | |
|---|---|---|---|
| H-12 | 段 2 の 192 行再現は段 1 の記録と 192/192 一致・byte 同一 | 段 1 の 13 行との一致 **12 / 13**(不一致: S100YYRV R014)。commit `ac8c3ff` 自身の報告は 192 行全体で **191 / 192** | **外れ** |
| H-13 | PP-R1〜R3 の 3 本 red(追記 1 で PP-R4 を足し 4 本) | **4 / 4 red** | 当たり |
| H-14 | 独立監査は REVISE 1 回 → GO | **REVISE 0 回 → GO**(引き継ぎの字。機械測定ではない) | **外れ** |
| H-15 | run_tests.sh 1 回目で赤くなるのは test_9 だけ。2 回目 rc=0 | 全数ログで FAIL は test_9 の 1 本だけ。追記後 `test_xbrl_axis3_decision.py` は 11 passed | 当たり |
| H-16 | 重複の 4 行は値が全部同じで PP-2 の後は兄弟 1 本(4/4) | **4 / 4** | 当たり |
| H-17 | 4 行の検算は GROUNDED 3〜4・VALUE_MISMATCH 0〜1。実証できた行は 75 → 79 | GROUNDED **3**・**UNPROVABLE 1**(VALUE_MISMATCH ではない)。実証できた行 75 → **77** | **外れ** |
| H-18 | 段 1 の 13 行の state・reason・recomputed は PP-2 で 1 行も変わらない | **13 / 13**(PP-2 固有の効果だけで見れば不変。(d) の効果は別) | 当たり |
| H-19 | 対照「前期を増やす」は PP-2 の後も 13/13 が UNPROVABLE | **13 / 13**(理由は `prior_sibling:2;duplicate_values`) | 当たり |

**当たり 5 / 外れ 3(H-12・H-14・H-17)。**

- **H-12 外れ**: 段 1 の 13 行のうち 1 行(S100YYRV R014)が `GROUNDED` から `UNPROVABLE` に変わった。
  原因は段 1 自身が §3 で記録していた (d) の発火(「13 行で (d)・P・U の発火」の `d` 1 件)が、
  段 2 で初めて `state` に反映されたこと。**封は直さない。**
- **H-14 外れ**: 「REVISE 1 回 → GO」と書いたが、実測(引き継ぎの字)は「REVISE 0 回 → GO」。
  **封は直さない。**
- **H-17 外れ**: 「GROUNDED 3〜4・VALUE_MISMATCH 0〜1」と書いたが、重複 4 行の 1 行(S100YWGX R008)は
  `VALUE_MISMATCH` ではなく (d) による `UNPROVABLE` だった。「実証できた行 75 → 79」も外れ(実測 77。
  +4 ではなく +2。R008 が UNPROVABLE になった分だけ少ない)。**封は直さない。**
  (※ ac8c3ff の commit 文が「予測の外れ」として先に自己申告していた 3 点
  (H-12=191/192・H-14=REVISE0回・H-17=UNPROVABLE1を数えていない)と、この節の実測は一致する。)

### §8 言えないこと(追加)

6. **段 1 の「13 行で (d)・P・U の発火は 0」(§3)の H-10 外れは、段 1 の時点では `state` に出ていなかった。**
   段 2(engine)で PP の後に保留規則を当てたことで、その発火が初めて `state` を変えた。
   **段 1 と段 2 で「実証できた行」の数え方(GROUNDED+VALUE_MISMATCH)が指す母集団の性質が違う**
   (段 1 は保留規則を無視した数、段 2 は保留規則を含む数)。75 → 77 の「+2」はこの違いを含む。
