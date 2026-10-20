# 結果: 名指しの直し(P21)段 1 ― **値が合わなかったときの最後の枝に、期の手がかり・セグメント・増減の語を見せた**

2026-10-20。封 `docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md`(commit 5c267df)に対する段 1 の実装と実測。
記録: `fixtures/xbrl/naming_fix/p21_2026-10-20.json`(`measure/xbrl_naming_fix_2026-10-20.py` の出力、完走した 1 本、全体 606.2 秒)。門: `tests/measure/test_xbrl_naming_fix_result.py`。実装の試験: `tests/adapters/xbrl/test_recipes_p21.py`。
**封は 1 文字も直していない。**予測の幅も、材料(gen_c 8 書類・cd8 8 書類・無改変 40 書類)も、採点(`measure/xbrl_a_core_vs_grep_2026-10-17.py` の実物)も、数を見てから直していない。C0・C1・cd8 の記録と席の答えは読むだけで、sha256 は前後で一致した(記録 `入力の sha256`)。**外れは外れのまま書く。**
**席(LLM API)は 1 回も呼んでいない。**通信していない。API key は 4 つとも未設定(0)(記録 `環境`)。**0 USD。**
**既定の profile は P20 のまま**(`DEFAULT_PROFILE = "P20"`)。製品の経路は変わっていない。段 2(既定を P21 に)はこの文書では決めない。
engine の差分は `adapters/xbrl/recipes.py` と `adapters/xbrl/vocabulary.py` の 2 本だけ(記録 `engine の差分`)。`core/` は 0 行、`instance.py`・`extract.py` も 0 行。

---

## 今回新しく分かったこと(先頭に置く)

1. **診断席の数を、実装がそのまま再現した。**gen_c の T5 50 件で Core-P の特定は P21 で 26 / 50 = 52.0%(P20 は 21 / 50 = 42.0%)、T5 の誤認定は 3 件(P20 は 19 件)。増えた特定はちょうど S100Z4GF-T5-02・07・12・16・23 の 5 件で、減った特定は 0 件(N-1)。cd8 の T5 64 件では特定が 46 / 64 = 71.9% のまま、誤認定が 12 件から 6 件になった(N-2)。T1 の通しは gen_c も cd8 も 0 / 38 = 0.0%、T3 の名指しは gen_c 7 / 40 = 17.5%・cd8 6 / 40 = 15.0% で P20 から 1 件も動かなかった(N-3)。
2. **特定が増えたのは 5 件だけで、誤認定が減った 16 件の大半は『誤った 1 本の名指しをやめた』ことによる。**gen_c の T5 の誤認定 19 件のうち、5 件は特定に変わり(F1′)、11 件は誤った 1 本の名指しをやめ(F2′ の 4 件は参照先を出さない、F3b の 7 件は残高の対にした。Core-P の読みでは参照先 1 本ではないので特定にも誤認定にも入らない)、残った 3 件は P20 と同じ(S100YYT4-T5-09・S100Z4GF-T5-04・S100Z4GF-T5-21。この 3 件の型は科目違いで、この直しの外)。cd8 の誤認定 12 件のうち 6 件が名指しをやめた。名指しをやめた T5 は gen_c 11 件・cd8 6 件で、特定率は動かない。**Core-P の特定率は 26 / 50 = 52.0% 止まり**(席 A は同じ 8 書類の K-4 の 20 行で 16 / 20 = 80.0%)。
3. **誤認定率(分母 = 参照先を出した全型の件)は gen_c で 26 / 55 = 47.3% から 10 / 43 = 23.3% に、cd8 で 18 / 76 = 23.7% から 12 / 70 = 17.1% に下がった。**分母は gen_c で 12 件・cd8 で 6 件減り(名指しをやめた件の分)、分子は gen_c で 16 件・cd8 で 6 件減った。
4. **無改変の 40 書類(4,665 主張)で GROUNDED の行が動いた数は 0。**動いたのは 170 主張で、全部 VALUE_MISMATCH か POINTER_NOT_FOUND の間(VM → VM 144・VM → PNF 26)。型の読みは F3b 131・F2′ 26・F1′ 13(N-4)。**N-4 は当たったので、段 2 の条件の 1 つは満たした。**ただし GROUNDED の不動は『退行なし』であって正しさの証明ではない(無改変の書類に正解の参照先は無い)。
5. **実装の最初の置き場所が、人間が決めた止めを壊した。**3 つの直しを最初は §1b の止め(前々期が無い『前連結会計年度は…』の主張は代用せず止める。2026-10-08 の人間の決定)の**前**に置いたところ、無改変の 40 書類の試行で、止めていた 2 行(S100YYN7 N054・S100Z4Q1 N025)が名指しに戻った(PNF → VM。動いた合計は 172 だった)。止めの**後ろ**に置き直して測り直した(動いた合計 170、PNF → VM は 0)。試行の記録は scratchpad にあり、repo の記録は置き直したあとの完走した 1 本。
6. **N-6 は幅の下端と上端にぴったり当たった。**K-4 の 20 行で Core-P(P21)は 9 / 20 = 45.0%(幅は 9〜12)、席 A との差は +35.0 pt(幅は +20〜+35)。特定が増えた K-4 の行は S100Z4GF-T5-02 と -07 の 2 行だけで、残りの増分 3 件(-12・-16・-23)は K-4 の 20 行に入っていない。**幅の端で当たったので、1 件違えば外れだった。**

---

## 予測 N-1〜N-12 の照合(封は書き換えない)

分母は行ごとに書いた。率は `a / b = x.x%` の形。

| | 予測 | 実測 | 判定 |
|---|---|---|---|
| **N-1** | gen_c T5 50 件: Core-P(P21)の特定 **26 / 50**(P20 21)、誤認定 **3**(P20 19)。増えた特定はちょうど Z4GF-T5-02・07・12・16・23 | P21 の特定 26 / 50 = 52.0%(P20 は 21 / 50 = 42.0%)・誤認定 3 件(P20 は 19 件)・増えた特定は S100Z4GF-T5-02・S100Z4GF-T5-07・S100Z4GF-T5-12・S100Z4GF-T5-16・S100Z4GF-T5-23 | **当たり** |
| **N-2** | cd8 (ア) T5 64 件: 特定 **46 / 64 のまま**、誤認定 **12 → 6** | cd8 の T5 64 件で P21 の特定 46 / 64 = 71.9%(P20 の記録は 46 / 64 = 71.9%)・誤認定 6 件(P20 の記録は 12 件) | **当たり** |
| **N-3** | T1 の通し gen_c **0 / 38**・cd8 **0 / 38**。T3 の名指し gen_c **7 / 40**・cd8 **6 / 40**(どちらも不変) | T1 の通し gen_c 0 / 38 = 0.0%・cd8 0 / 38 = 0.0%、T3 の名指し gen_c 7 / 40 = 17.5%・cd8 6 / 40 = 15.0%(P20 の記録と同じ) | **当たり** |
| **N-4** | 無改変 40 書類: **GROUNDED の行で state か参照先が動いた数 0**。動いた行は VALUE_MISMATCH / POINTER_NOT_FOUND の参照先の移動だけで、合計 **120〜220 行** | 無改変 40 書類・主張 4,665 本のうち、動いた 170 本(うち GROUNDED の行 0 本)。VM → VM 144・VM → PNF 26・PNF → VM 0。型は F1′ 13・F2′ 26・F3b 131 | **当たり** |
| **N-5** | gen_c 8 書類の C0-1(製品の経路)の state の合計は P20 と P21 で **同じ**(GROUNDED 443・VM 194・UNVERIFIABLE 165・PNF 111)。F2′ で VM → PNF に動く行があれば、その数だけ VM が減り PNF が増える(**0〜10 行**) | P20 の合計 GROUNDED 443・VM 194・UNVERIFIABLE 165・PNF 111、P21 は GROUNDED 443・VM 187・UNVERIFIABLE 165・PNF 118。gen_c 8 書類で VM → PNF に動いた行 7 | **当たり** |
| **N-6** | K-4 の 20 行: Core-P(P21)**9〜12 / 20**(P20 7)、席 A 16 / 20 との差 **+20〜+35 pt** | 席 A 16 / 20 = 80.0%・Core-P(P21)9 / 20 = 45.0%(P20 は 7 / 20 = 35.0%)・差 +35.0 pt | **当たり** |
| **N-7** | C0-3: Core-P(P21)の参照先で engine が GROUNDED にする件数 **0**(独立した証拠ではない。C0 と同じ) | GROUNDED 0 / 43 = 0.0%(Core-P が名指した注入の行 43 本を engine に通した) | **当たり** |
| **N-8** | 対照 M-C1 全欄一致・M-C2 緑・M-C3 赤 | M-C1 全欄一致(gen_c の (ア) を P20 で回すと `c0_p20` の記録と一致。補助で cd8 の (ア) も一致)・M-C2 緑(`pytest -q tests/adapters tests/core tests/golden tests/fixtures measure/tests` が 1242 passed・1 skipped・失敗 0)・M-C3 赤(旗を P20 でも真にすると gen_c の rows が記録と 18 件違う) | **当たり** |
| **N-9** | engine の差分: `adapters/xbrl/recipes.py` は `_direct_value_claim` の最後の枝の中だけ(**+40 行以下**)、`adapters/xbrl/vocabulary.py` は field 1 つ + P21 の 1 行 + `PROFILES` の登録(段 2 で DEFAULT_PROFILE)。`core/py/` **0 行**。`instance.py`・`extract.py` **0 行** | recipes.py は 30 行追加・0 行削除(`_direct_value_claim` の最後の枝の中の 1 か所)、vocabulary.py は 8 行追加・1 行削除、core/ は 0 行、instance.py・extract.py は 0 行 | **当たり** |
| **N-10** | `tests/adapters/xbrl/mutations.json` の old の字は全部そのまま file に 1 回在る(test_mutations 緑) | M-C2 の run に `tests/adapters/xbrl/test_mutations.py` が入っていて緑(1242 passed の中)。`tests/adapters/xbrl/mutations.json` は 1 文字も変えていない(`git status` に出ない) | **当たり** |
| **N-11** | §1 の 7 本の門に遷移の字を足し、`pytest -q tests/measure` の赤は **axis3 の test_9 だけ**(結果の commit で宣言して消える) | 遷移の字を足した門は 7 本(axis3 の vocabulary の sha・cd_seal・branch_a・p20_result・pnf_diag・role_swap_result・a_core_vs_grep_seal)と `frozen_bundle_sha.py` の新しい世代。作業木(engine は未 commit)で `pytest -q tests/measure` の赤は 0 本。axis3 の test_9 は commit 済みの engine の commit を数える試験で、engine を commit すると宣言が無いので赤になる(宣言する sha は commit のあとにしか無い) | **判定しない(commit 後)** |
| **N-12** | 段 2(既定 = P21): `test_p16_matches_the_holdout_dumps` で動く行は §1 の **5 行だけ**、全部 VALUE_MISMATCH の参照先の移動 | 段 2 の予測なので段 1 では判定しない。参考: P21 を同じ照合に当てると S100Z4N9 の 4 行(H-067・H-120・H-122・H-124。全部 F1′ の形で OperatingIncome・OrdinaryIncome の Prior1YearDuration)と S100Z39P の 1 行(H-075。F3b の形で残高の対)の 5 行、全部 VALUE_MISMATCH のまま。P20 は 0 行 | **判定しない(段 2)** |

**当たり 10 / 外れ 0 / 判定しない 2。**

---

## 外れの読みと、当たりのうち読んでおくこと

**外れは 1 つも無かった。**N-1〜N-7・N-9・N-8・N-10 の 10 本が当たり。N-11 は engine の commit の後でないと測れず、N-12 は段 2 の予測なので、この段では判定しない。ただし次の 3 点は『当たり』の強さを下げて読むこと。

- **N-1〜N-3 の数は診断席の差し替え実測から写した予測で、実装がそれを再現しただけ**(封 §4)。新しい標本での特定の増減を予言したものではない。
- **N-4 の字(GROUNDED が動かない・動いた行は VM / PNF の間・合計 120〜220)は、止めを壊した最初の実装でも当たっていた**(172 本。『今回新しく分かったこと』5.)。この予測は止めの破壊を検知できない。置き直しを促したのは予測ではなく、動いた主張を 1 件ずつ読んだこと。
- **N-6 は幅の両端で当たった**(下の『当たりのうち』)。

### 当たりのうち、読んでおくこと

- **N-6 は幅の両端で当たった(9 / 20 と +35.0 pt)。**封の幅は診断席の差し替え実測(K-4 の増分 2 件)から写したもので、1 件でも K-4 の増分が違えば外れだった。この当たりを『幅の中央で当たった』とは読まない。
- **N-5 の幅(0〜10 行)の中で VM → PNF は 7 行。**全部 F2′(セグメント利益・損失の枠が取れていない主張。名指さず止める)。S100Z4GF が 4 行(N021・N022・N025・N026。『前年同期は…』の括弧の入った『セグメント利益は…』の文)、S100YYN7 が 3 行(N013・N017・N022。『セグメント利益…(前連結会計年度比…)』の文)で、どれも無改変の本文の主張(注入の行ではない)。
- **N-4 の当たりは『GROUNDED が動かない』という最小の安全の確認である。**動いた 170 主張のうち正しい名指しに変わったか、誤った名指しをやめたかは、無改変の書類に正解が無いので測っていない。F3b が 131 行と最も多い(増減の文が当期の残高を選んでいた主張を残高の対に変える直し)が、この 131 行の『残高の対』が主張の言う差と合っているかは測っていない(VALUE_MISMATCH のまま、Core の状態は変わらない)。
- **特定が増えたのは gen_c の S100Z4GF だけ(5 件)で、cd8 の特定は 1 件も増えていない**(46 / 64 のまま)。cd8 で動いた 6 件は全部『名指しをやめた』で、増えた特定は 0。

---

## P20 の数と P21 の数を並べる(**同じ 128 件の注入・同じ種・同じ 8 書類**)

| | P20 | P21 |
|---|---|---|
| gen_c の T5 50 件の Core-P の特定 | 21 / 50 = 42.0% | 26 / 50 = 52.0% |
| gen_c の T5 の誤認定(別の参照先を名指した件) | 19 件 | 3 件 |
| S100Z4GF の T5 24 件の特定 | 8 / 24 = 33.3% | 13 / 24 = 54.2% |
| gen_c の誤認定率(分母 = 参照先を出した全型の件) | 26 / 55 = 47.3% | 10 / 43 = 23.3% |
| gen_c の T1 の通し | 0 / 38 = 0.0% | 0 / 38 = 0.0% |
| gen_c の T3 の名指し | 7 / 40 = 17.5% | 7 / 40 = 17.5% |
| cd8 の T5 64 件の Core-P の特定 | 46 / 64 = 71.9% | 46 / 64 = 71.9% |
| cd8 の T5 の誤認定(別の参照先を名指した件) | 12 件 | 6 件 |
| cd8 の誤認定率(分母 = 参照先を出した全型の件) | 18 / 76 = 23.7% | 12 / 70 = 17.1% |
| cd8 の T1 の通し | 0 / 38 = 0.0% | 0 / 38 = 0.0% |
| cd8 の T3 の名指し | 6 / 40 = 15.0% | 6 / 40 = 15.0% |
| K-4 の 20 行の Core-P の特定 | 7 / 20 = 35.0% | 9 / 20 = 45.0% |
| C0-3 で engine が GROUNDED にした件数 | 0 / 55 = 0.0% | 0 / 43 = 0.0% |
| C0-3 の (d) 保留の露出 | 3 / 55 = 5.5% | 3 / 43 = 7.0% |
| C0-1(gen_c 8 書類)の GROUNDED の合計 | 443 | 443 |
| C0-1(gen_c 8 書類)の VALUE_MISMATCH の合計 | 194 | 187 |
| C0-1(gen_c 8 書類)の POINTER_NOT_FOUND の合計 | 111 | 118 |
| C0-1(gen_c 8 書類)の UNVERIFIABLE の合計 | 165 | 165 |

---

## 変わった注入 1 件ずつ(P20 → P21。Core-P の参照先)

### gen_c(8 書類・注入 128 件のうち変わったのは 18 件)

| 注入 | 型 | gold | P20 の参照先 | P21 の参照先 |
|---|---|---|---|---|
| S100YYT4-T5-01 | T5 | `totalchangesofitemsduringtheperiod@currentyearduration` | `netassets@currentyearinstant` | (なし) |
| S100YYT4-T5-05 | T5 | `totalchangesofitemsduringtheperiod@currentyearduration` | `netassets@currentyearinstant` | (なし) |
| S100YYT4-T5-15 | T5 | `currentportionoflongtermloanspayable@currentyearinstant` | `longtermloanspayable@currentyearinstant` | (なし) |
| S100YYT4-T5-16 | T5 | `totalchangesofitemsduringtheperiod@currentyearduration_retainedearningsmember` | `retainedearnings@currentyearinstant` | (なし) |
| S100Z4GF-T5-01 | T5 | `operatingincome@currentyearduration_nonconsolidatedmember_jpcrp030000-asr_e37207-000dtxproductbusinessreportablesegmentmember` | `operatingincome@currentyearduration_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-02 | T5 | `researchanddevelopmentexpensessga@prior1yearduration_nonconsolidatedmember` | `researchanddevelopmentexpensessga@currentyearduration_nonconsolidatedmember` | `researchanddevelopmentexpensessga@prior1yearduration_nonconsolidatedmember` |
| S100Z4GF-T5-07 | T5 | `extraordinaryloss@prior1yearduration_nonconsolidatedmember` | `extraordinaryloss@currentyearduration_nonconsolidatedmember` | `extraordinaryloss@prior1yearduration_nonconsolidatedmember` |
| S100Z4GF-T5-10 | T5 | `operatingincome@prior1yearduration_nonconsolidatedmember_jpcrp030000-asr_e37207-000dtxproductbusinessreportablesegmentmember` | `operatingincome@currentyearduration_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-12 | T5 | `nonoperatingincome@prior1yearduration_nonconsolidatedmember` | `nonoperatingincome@currentyearduration_nonconsolidatedmember` | `nonoperatingincome@prior1yearduration_nonconsolidatedmember` |
| S100Z4GF-T5-13 | T5 | `operatingincome@prior1yearduration_nonconsolidatedmember_jpcrp030000-asr_e37207-000dtxplatformbusinessreportablesegmentmember` | `operatingincome@currentyearduration_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-16 | T5 | `sellinggeneralandadministrativeexpenses@prior1yearduration_nonconsolidatedmember` | `sellinggeneralandadministrativeexpenses@currentyearduration_nonconsolidatedmember` | `sellinggeneralandadministrativeexpenses@prior1yearduration_nonconsolidatedmember` |
| S100Z4GF-T5-17 | T5 | `operatingincome@currentyearduration_nonconsolidatedmember_jpcrp030000-asr_e37207-000dtxplatformbusinessreportablesegmentmember` | `operatingincome@currentyearduration_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-23 | T5 | `nonoperatingexpenses@prior1yearduration_nonconsolidatedmember` | `nonoperatingexpenses@currentyearduration_nonconsolidatedmember` | `nonoperatingexpenses@prior1yearduration_nonconsolidatedmember` |
| S100Z4GF-T5-24 | T5 | `increasedecreaseincontractliabilitiesopecf@currentyearduration_nonconsolidatedmember` | `contractliabilities@currentyearinstant_nonconsolidatedmember` | (なし) |
| S100Z4GF-T1-04 | T1 | (なし) | `nonoperatingincome@currentyearduration_nonconsolidatedmember` | `nonoperatingincome@prior1yearduration_nonconsolidatedmember` |
| S100YYUD-T5-02 | T5 | `totalchangesofitemsduringtheperiod@currentyearduration` | `netassets@currentyearinstant` | (なし) |
| S100YYUD-T5-03 | T5 | `amortizationofgoodwillopecf@currentyearduration` | `goodwill@currentyearinstant` | (なし) |
| S100YYUD-T1-03 | T1 | (なし) | `retainedearnings@currentyearinstant` | (なし) |

### cd8(8 書類・注入 142 件のうち変わったのは 6 件)

| 注入 | 型 | gold | P20 の参照先 | P21 の参照先 |
|---|---|---|---|---|
| S100Z4LC-T5-03 | T5 | `totalchangesofitemsduringtheperiod@currentyearduration` | `netassets@currentyearinstant` | (なし) |
| S100Z4LC-T5-09 | T5 | `operatingincome@currentyearduration_jpcrp030000-asr_e34748-000renewableenergybusinessreportablesegmentsmember` | `operatingincome@currentyearduration` | (なし) |
| S100Z3CI-T5-06 | T5 | `currentportionoflongtermloanspayable@currentyearinstant` | `longtermloanspayable@currentyearinstant` | (なし) |
| S100Z3CI-T5-18 | T5 | `increasedecreaseinprovisionforbonusesopecf@currentyearduration` | `provisionforbonuses@currentyearinstant` | (なし) |
| S100Z3CI-T5-29 | T5 | `totalchangesofitemsduringtheperiod@currentyearduration` | `netassets@currentyearinstant` | (なし) |
| S100Z461-T5-06 | T5 | `netincreasedecreaseincashandcashequivalents@currentyearduration` | `cashanddeposits@currentyearinstant` | (なし) |

誤った名指しを止めた T5 は gen_c 11 件・cd8 6 件(P20 で誤認定、P21 で参照先なし)。gen_c の T1(値がどこにも無い)2 件も名指しが変わった(S100Z4GF-T1-04 は当期の fact から前期の fact へ、S100YYUD-T1-03 は名指しをやめた)が、どちらも『確認済み』とは言っていない(T1 の通しは 0 / 38 = 0.0% のまま)。

---

## 無改変の 40 書類(P20 と P21 の行ごとの差)

書類は 5 群: gen_c 8・(ア)/final8 8・cd8 の引いた 8・開発 14・未使用 2(id の一覧は記録 `無改変の 40 書類`)。`verify_document` を書類自身の本文(製品の経路)で P20 と P21 で回し、主張の `(state, pointers, reason, recomputed, form)` を比べた。

| 群 | 書類 | 主張 | 動いた主張 |
|---|---|---|---|
| gen_c 8 | 8 | 913 | 53 |
| (ア)/final8 8 | 8 | 924 | 39 |
| cd8 の引いた 8 | 8 | 919 | 34 |
| 開発 14 | 14 | 1,620 | 38 |
| 未使用 2 | 2 | 289 | 6 |
| 合計 | 40 | 4,665 | 170 |

- **GROUNDED の行で動いたのは 0。**P20 でも P21 でも GROUNDED の主張(40 書類の合計)は書類ごとに同じ数のまま(記録 `書類ごと`)。
- 動いた 170 主張の state の組は VM → VM 144・VM → PNF 26・PNF → VM 0。型(pointer の字から機械的に読んだ): F3b(残高の対)131・F2′(名指さず止めた)26・F1′(前期の fact)13。
- 補助(封の外): C-2(注入した本文で、無改変の主張の判定が動いたか)は一意に対になった主張 9,864 本(延べ)で判定が動いた 0。
- 未使用 2 書類(S100Z39P・S100Z4N9)で動いたのは S100Z39P が 1 主張・S100Z4N9 が 5 主張。

---

## 対照(道具の故障を作って当てた)

- **M-C1(旗の後ろに置いた証拠)**: `--profile P20` で gen_c の (ア) を回し、`c0_p20_2026-10-20.json` の記録と全欄一致した(main() の出力の rows 以外・rows・Recorder 再走・C0-3 の行と集計・注入の件数・各注入の claim・C0-1 の claims と states が書類ごと)。補助で cd8 の (ア) を P20 で回しても `a_core_vs_grep_P20_2026-10-17.json` と全欄一致。
- **M-C3(変異)**: `V.PROFILES["P20"]` を `last_branch_cues=True` にして gen_c の (ア) を回すと、c0_p20 の記録と一致しなくなる(違った注入 18 件。P21 の run で動いた 18 件と同じ id)。旗が効いている証拠で、旗を外すと 18 件が戻る。変異は終わったら戻した。
- **M-C2(既存の試験)**: 下の『既存の試験』。

---

## 既存の試験

- **M-C2**: `python3 -m pytest -q -p no:cacheprovider tests/adapters tests/core tests/golden tests/fixtures measure/tests` は **1242 passed・1 skipped・失敗 0**(19 分 27 秒。`test_mutations.py` の 96 行を含む)。P16 の golden・P20 の決定・`mutations.json` はそのまま緑。
- **`tests/measure`**: `python3 -m pytest -q -p no:cacheprovider tests/measure` は **2272 passed・9 skipped・失敗 0**(1 分 38 秒。engine が未 commit なので axis3 の test_9 も緑。engine を commit すると test_9 は『宣言されていない commit』で赤になる ― N-11)。
- **実装の試験** `tests/adapters/xbrl/test_recipes_p21.py` は 21 本。3 つの直しを 1 つずつ消す変異(F1′ の条件を `False and …`・F2′ の条件を `False and …`・F3b の条件を `False and …`)で、F1′ は 1 本・F2′ は 2 本・F3b は 1 本が赤、旗を常に真にする変異で P20 側の 3 本が赤、§1b の止めを外す変異で止めの試験 2 本が赤になった。どの変異も戻して `recipes.py` の sha256 が一致するのを確かめた。
- **結果の門** `tests/measure/test_xbrl_naming_fix_result.py` は 12 本。5 通りの変異(記録の N-6 の判定を反転 → test_4 が赤、文書の N-1 の特定の分子を 26 から 27 に → test_7 と test_8 が赤、記録の gen_c の行の参照先を 1 件書き換え(集計は据え置き)→ 7 本が赤、記録の動いた行 1 件を GROUNDED に → test_4・test_5・test_8 が赤、文書の『段 2 はこの文書では決めない』を消す → test_11 が赤)で赤になることを確かめ、`cp` で戻して sha256 が一致するのを確かめた。
- 試験 file 数: 186 → 188(`tests/adapters/xbrl` 25 → 26・`tests/measure` 128 → 129。`docs/SUITE_COVERAGE_2026-10-16.md` §2-1 と `README.en.md` を直した)。

---

## 手順の正直な記録

1. 診断席が関数の差し替えで測った数(封 §3 の出どころ)を、実装が再現するかを先に測った(gen_c の (ア) を P21 で。scratchpad)。N-1 は最初の実装で再現した(26 / 50・誤認定 3・増えた id)。
2. 無改変の 40 書類の試行(scratchpad)で、動いた主張に『前連結会計年度は…』の止めの行 2 つが入っているのを見つけ、置き場所を止めの後ろに直した(『今回新しく分かったこと』5.)。**この直しは数を見てからの実装の修正**であり、封の字・予測は直していない。直す前の差分は scratchpad に残してある。直したあと、実装の試験に『止めを保つ』試験を 2 本足し、その試験が止めを外す変異で赤くなることを確かめた。
3. 実装の試験(`test_recipes_p21.py`)は 3 つの直しを 1 つずつ消す変異で赤くなることを実行して確かめた(F1′ を消すと 1 本・F2′ を消すと 2 本・F3b を消すと 1 本。旗を常に真にすると P20 側の 3 本が赤。止めを外すと止めの試験 2 本が赤)。いずれも戻して sha256 が一致するのを確かめた。
4. 測定 script は 1 回だけ走らせ、repo の記録 `p21_2026-10-20.json` はその完走した 1 本(全体 606.2 秒)。scratchpad に向けた予行(最初の実装)は別に 1 回走らせた。その予行で N-9 が外れと出たのは、挿入が 1 か所かを difflib で判定した script の欠陥(挿入が複数の op に分かれた)で、git の hunk の数で見る判定に直した。置き場所を直したあとは、直前の HEAD の行の字(§1b の止めの理由と `return`)も直した。
5. 過去の門の留め(封 §1)は 7 本に遷移の字を足した(`test_xbrl_cd_seal`・`test_xbrl_branch_a`・`test_xbrl_p20_result`・`test_xbrl_pnf_diag`・`test_xbrl_role_swap_result`・`test_xbrl_a_core_vs_grep_seal`、`fixtures/frozen_bundle_sha.py` の新しい世代)。`test_xbrl_axis3_decision.py` は封が『`LATER_ENGINE_COMMITS` を宣言する』としたが、同じ試験が vocabulary.py の sha も留めていたので、その sha の遷移の字も足した(commit の宣言は engine の commit のあと)。

---

## 迷った点(封の字で 1 通りに決まらなかった所)

1. **置き場所(止めの前か後ろか)。**依頼は『分岐を前に足す』と書いていたが、字どおり止めの前に足すと、人間が決めた止めを壊す行が 2 つ出た。止めの後ろ(`if cur:` の中)に置いた。`mutations.json` の old の字は 1 本も変えていない。止めの前に置く案に戻すなら、記録の N-4(動いた 172)と 40 書類の PNF → VM 2 行が変わる。『前に足す』の出どころは依頼の字と、封 §1 の mutations.json の行『これらの字は変えず、分岐を前に足す』の 2 つ(封は直さない。独立監査 2026-10-20 の非ブロック指摘 1)。
2. **F2′ の理由の字。**依頼は `no_element(segment member missing)` を例示したが、その字は理由の登録簿(`recipes.UNBOUND_REASON_STATE`・`registry_setup.py`)に無く、足すと engine の別の file(N-9 の外)を変えるので、**登録済みの `no_element`(状態は POINTER_NOT_FOUND)**を使った。細かい理由の区別が要るなら別の封で登録簿を変える。
3. **『誤認定 3』の数え方。**封 N-1 の『誤認定 3(P20 19)』は T5 50 件のうち Core-P が別の参照先を名指した件数と読んだ(P20 で 19 と一致する数え方はこれだけ)。参照先を出した全型の件を分母にした率(T3 の名指し 7 件を含む)は別の欄に並べた。
4. **F2′ の主語の字。**`subj` が『セグメント利益』『セグメント損失』のどちらかのときだけ(字で 2 語)。ラベル由来で足された『〇〇セグメント利益』のような主語には当てていない(測った 40 書類で当たるかは測っていない)。
5. **F3b の『当期の残高』の字。**選んだ fact の context が `CurrentYearInstant` で始まり、同じ要素・同じ枠の `Prior1YearInstant` があるときだけ。前期の残高が無ければ従来どおり 1 本(P20 と同じ)。
6. **開発 14 書類・未使用 2 書類の出どころ。**開発 14 は `tests/adapters/xbrl/test_verify_entry.py` の `ROBUSTNESS_P16` の key、未使用 2 は `HOLDOUT_DOCS`。40 書類は互いに重ならず、全部キャッシュに在った(記録 `キャッシュに無い書類` は空)。
7. **profile の字の一覧。**`test_vocabulary.py` の 2 か所に P21 を足した。`test_p20.py` の『他の profile は連結の無い書類の旗を偽にする』試験は P21 が P20 を土台にするので P21 を除いた。`test_run.py`・`test_p17.py` は既定 = P20 の字だけで、P21 を足す一覧は無かった。

---

## 限界

- 8 書類 1 回である。合格線は作らない。新しい標本での汎化は測っていない(封 §4)。次の未使用書類で測る。
- 無改変 40 書類に正解の参照先は無い。GROUNDED の不動は『退行なし』であって『正しい』の証明ではない。動いた 170 主張のうち、名指しが正しくなったか誤りが止まったかは分けていない。
- 特定が増えるのは F1′ の 5 件だけ。F2′・F3b は誤った 1 本の名指しをやめる直しで、Core-P の特定率は 26 / 50 = 52.0% 止まり。残りは参照先を出さない 21 件(F4・表のセル)、セグメントの枠(F2 本体)、科目違いの 3 件。
- N-6 は幅の両端で当たった。診断席の差し替え実測(2 件)から写した幅の端に実測が乗ったので、『予測が当たった』ことの強さは弱い。
- (ア) の脚注: 正解は identified_sites(値の一意性 + 単位・ラベル)で作られ、正解そのものが誤りうる。
- 段 2 はこの文書では決めない。N-4・N-5 は当たったが、既定を P21 にするのは人間の決定(`vocabulary.py` の決定の注記に日付と根拠を足す)で、独立監査 GO の後。
