# 結果: 汎化 C 追記 2(改善 1)段 P-B ― **C0-2・C0-3 を製品の既定 profile(P20)で測り直した**

2026-10-20。封 `docs/XBRL_GENERALITY_SEAL_2026-10-20.md` 追記 2(段 P-A)に対する段 P-B の実測。
記録: `fixtures/xbrl/gen_c/c0_p20_2026-10-20.json`(`measure/xbrl_gen_c_p20_2026-10-20.py` の出力、全体 387.8 秒)。門: `tests/measure/test_xbrl_generality_p20_result.py`。
**封は 1 文字も直していない。**予測の幅も、材料(8 書類)も、採点(`measure/xbrl_a_core_vs_grep_2026-10-17.py` の実物)も、数を見てから直していない。C0 の結果文書・C0 の記録・C1 の記録・席の答えは読むだけで、sha256 は前後で一致した(記録 `入力の sha256`)。**外れは外れのまま書く。**
**席(LLM API)は 1 回も呼んでいない。**通信していない。API key は 4 つとも未設定(0)(記録 `環境`)。**0 USD。**
`core/`・`adapters/` は 0 行(記録 `engine の留め`: ac8c3ff と sha256 が違う file 0、`git diff HEAD --numstat` も `git status --porcelain` も空)。C0 の script `measure/xbrl_gen_c_2026-10-20.py` も 0 行(import して `CD8_PROFILE` を差し替えて呼び、戻した)。

---

## 今回新しく分かったこと(先頭に置く)

1. **R-4 は外れた。T5 50 件の Core-P の特定は P20 で 21 / 50 = 42.0%(P16 は 13 / 50 = 26.0%、cd8 は 46 / 64 = 71.9%)。profile を製品の既定に合わせても cd8 の水準には戻らなかった。**増えた 8 件は全部 S100Z4GF(0 / 24 = 0.0% から 8 / 24 = 33.3%)で、それ以外の 26 件は P16 でも P20 でも 13 / 26 = 50.0% で同じ。連結のある 6 書類の注入 84 件は P16 と P20 で全行一致(R-C2)で、連結の無い 2 書類の注入 44 件のうち 27 / 44 = 61.4% が変わった。したがって『G-5 の外れの大半は測定の profile の側』という見立て(封 B-0)は、**特定の件数では支持されなかった**(profile が効いたのは S100Z4GF の 8 件だけ)。
2. **S100Z4GF の 24 件は『参照先を出さない』から『参照先を出すが違う』に移った。**P16 は参照先を出さない 23 件・誤認定 1 件・特定 0 件、P20 は特定 8 件・誤認定 12 件・参照先を出さない 4 件。誤認定 12 件を 1 件ずつ読むと、科目が違う 3 件、期間だけ違う 5 件(文は『(前事業年度は N千円)』の括弧内の数で、gold は前期の枠、Core-P の名指しは当期の枠)、枠(次元)だけ違う 2 件と期間と枠が両方違う 2 件(セグメント利益の文で、Core-P の名指しはセグメントを外した単体の `OperatingIncome`)。
3. **名指しが増えた分、誤認定も増えた。**Core-P の誤認定率は 26 / 55 = 47.3%(P16 は 13 / 32 = 40.6%)で R-5 の幅(15〜40%)を上に出た。T1 の通しは 0 / 38 = 0.0%、T3 の名指しは 7 / 40 = 17.5%(P16 は 5 / 40 = 12.5%)。増えた T3 の名指し 2 件は連結の無い 2 書類の作り話の文(S100Z4GF-T3-01・S100Z4J8-T3-04。どちらも『海外関連会社売上高は N百万円となりました。』の文)で、どちらも単体の枠の科目を名指して VALUE_MISMATCH で止めている。
4. **K-4 の差は縮んだが、封の幅(+25 pt まで)には入らなかった。**同じ T5 の 20 行で、席 A は 16 / 20 = 80.0%(C1 の答えのまま)、Core-P は P16 の 5 / 20 = 25.0% から P20 の 7 / 20 = 35.0% になり、差は +55.0 pt から +45.0 pt(R-6 は外れ)。次元つきの 10 行は席 A 10 / 10 = 100.0%、Core-P は P16 の 0 / 10 = 0.0% から P20 の 2 / 10 = 20.0%(R-7 は外れ)。S100Z4GF を除く 12 行は P16 も P20 も Core-P 5 / 12 = 41.7%・席 A 8 / 12 = 66.7%(差 +25.0 pt)で動いていない。
5. **R-8(誤りを通した件数)は 0 / 55 = 0.0%。ただし R-8 の 0 は engine の独立した証拠ではない。**Core-P が名指した注入の行 55 本(T5 40・T1 8・T3 7)は、Core 自身がすべて VALUE_MISMATCH で止めており、engine も同じ 55 本を VALUE_MISMATCH にした(55 / 55 = 100.0%)。保留規則 (d)・P・U は GROUNDED にしか当たらないので製品の経路の held は 0。T5 の偶然一致する側を engine に直接渡した補助確認(封の外)も 50 / 50 = 100.0% が VALUE_MISMATCH で、単位込みで値が一致する行は 0。

---

## 予測 R-1〜R-11 の照合(封は書き換えない)

分母は行ごとに書いた。率は `a / b = x.x%` の形。

| | 予測 | 実測 | 判定 |
|---|---|---|---|
| **R-1** | 注入の id・件数は P16 と P20 で同じ(128。T5 50・T1 38・T3 40) | 件数 128・T5 50・T1 38・T3 40・id の並びも gold も改変後の値も P16(C0 の記録)と同じ | **当たり** |
| **R-2** | `S100Z4GF` の T5 24 件で Core-P(P20)の特定 **14〜22 / 24**(P16 は 0) | 8 / 24 = 33.3%(P16 は 0 / 24 = 0.0%) | **外れ** |
| **R-3** | 次元つき gold 30 件で Core-P(P20)の特定 **14〜24 / 30**(Z4GF 以外の 6 件は 0〜2) | 8 / 30 = 26.7%(P16 は 0 / 30 = 0.0%)。括弧内: Z4GF 以外の 6 件は 0 / 6 = 0.0% | **外れ** |
| **R-4** | T5 50 件で Core-P(P20)の特定 **27〜37 / 50**(54〜74%。cd8 71.9%) | 21 / 50 = 42.0%(P16 は 13 / 50 = 26.0%) | **外れ** |
| **R-5** | Core-P(P20)の誤認定率 **15〜40%**(分母 = 参照先を出した件)、T1 の通し **0 / 38**、T3 の名指し **25% 以下** | 誤認定率 26 / 55 = 47.3%・T1 の通し 0 / 38 = 0.0%・T3 の名指し 7 / 40 = 17.5% | **外れ** |
| **R-6** | K-4 の再計算: 同じ 20 行で Core-P(P20)**11〜16 / 20**、席 A 16 / 20 との差 **0〜+25 pt**(C1 の +55.0 から縮む) | 席 A 16 / 20 = 80.0%・Core-P(P20)7 / 20 = 35.0%・差 +45.0 pt | **外れ** |
| **R-7** | 次元つき 10 行(K-5 の行)で Core-P(P20)**6〜10 / 10**(P16 は 0) | 2 / 10 = 20.0%(P16 は 0 / 10 = 0.0%) | **外れ** |
| **R-8** | C0-3(P20 の参照先): engine が GROUNDED にする件数 **0**(C0 と同じ理由で、これも engine の独立した証拠ではない) | 0 / 55 = 0.0%(分母 = Core-P(P20)が名指した注入の行) | **当たり** |
| **R-9** | `S100Z4J8`(T5 0)の T3 の名指しは P20 で **0〜3 / 5**、T1 の通し 0 / 5 | T5 の注入 0・T3 の名指し 1 / 5 = 20.0%・T1 の通し 0 / 5 = 0.0% | **当たり** |
| **R-10** | 対照 R-C1〜R-C3 が全部期待どおり | R-C1・R-C2・R-C3 とも期待どおり | **当たり** |
| **R-11** | 木: `core/`・`adapters/` 差分 0 行。覆い +1(結果の門) | core/・adapters/ 差分 0 行(記録 engine の留め)。`pytest -q tests/measure` 2239 passed / 9 skipped(赤 0)・`pytest -q tests/adapters tests/core tests/golden tests/fixtures measure/tests` 1221 passed / 1 skipped(赤 0)。合計 3,470 本は覆いの記録の pytest 収集 3,470 本と一致。覆い 183 → 184 file(P20 の結果の門で +1)。`run_tests.sh`(全部・約 40 分)は走らせていない | **当たり** |

**当たり 5 / 外れ 6。**

封の『本当に測っているのは R-2〜R-4・R-6』は 4 つとも外れた。封の読み(B-3)では、R-4 が外れれば『P20 でも Core の名指しが落ちる(書類の側か名指しの規則の側)』。この 8 書類 1 回の数から言えるのは、profile を P20 にしても T5 50 件の特定が cd8 の水準に戻らなかったことまで。書類の側か規則の側かは分けていない。

---

## 外れの読み(1 件ずつ読んだ事実だけ。原因の断定はしない)

### R-4・R-2・R-3(外れ): 特定 21 / 50 = 42.0%・S100Z4GF 8 / 24 = 33.3%・次元つき 8 / 30 = 26.7%

T5 50 件のうち、P20 で特定しなかった 29 件を 1 件ずつ並べた(記録 `P20 で特定しなかった T5 の行`。分類は gold と Core-P の参照先の字から、科目 → 期間 → 枠の順に比べた)。

| 注入 | 分類 | gold | P20 の参照先 | P16 の参照先 |
|---|---|---|---|---|
| S100YYT4-T5-01 | 科目が違う | `totalchangesofitemsduringtheperiod@currentyearduration` | `netassets@currentyearinstant` | `netassets@currentyearinstant` |
| S100YYT4-T5-02 | 参照先を出さない | `operatingincome@currentyearduration_jpcrp030000-asr_e31379-000mentenansreportablesegmentmember` | (なし) | (なし) |
| S100YYT4-T5-04 | 参照先を出さない | `netsales@currentyearduration_jpcrp030000-asr_e31379-000mentenansreportablesegmentmember` | (なし) | (なし) |
| S100YYT4-T5-05 | 科目が違う | `totalchangesofitemsduringtheperiod@currentyearduration` | `netassets@currentyearinstant` | `netassets@currentyearinstant` |
| S100YYT4-T5-08 | 参照先を出さない | `sellinggeneralandadministrativeexpenses@currentyearduration` | (なし) | (なし) |
| S100YYT4-T5-09 | 科目が違う | `currentportionoflongtermloanspayable@prior1yearinstant` | `repaymentoflongtermloanspayablefincf@currentyearduration` | `repaymentoflongtermloanspayablefincf@currentyearduration` |
| S100YYT4-T5-11 | 参照先を出さない | `netsales@currentyearduration_jpcrp030000-asr_e31379-000servisereportablesegmentmember` | (なし) | (なし) |
| S100YYT4-T5-12 | 参照先を出さない | `operatingincome@currentyearduration_jpcrp030000-asr_e31379-000servisereportablesegmentmember` | (なし) | (なし) |
| S100YYT4-T5-15 | 科目が違う | `currentportionoflongtermloanspayable@currentyearinstant` | `longtermloanspayable@currentyearinstant` | `longtermloanspayable@currentyearinstant` |
| S100YYT4-T5-16 | 科目が違う | `totalchangesofitemsduringtheperiod@currentyearduration_retainedearningsmember` | `retainedearnings@currentyearinstant` | `retainedearnings@currentyearinstant` |
| S100YYT4-T5-20 | 参照先を出さない | `transactionswithothersegments@currentyearduration_totalofreportablesegmentsandothersmember` | (なし) | (なし) |
| S100Z4GF-T5-01 | 枠(次元)だけ違う | `operatingincome@currentyearduration_nonconsolidatedmember_jpcrp030000-asr_e37207-000dtxproductbusinessreportablesegmentmember` | `operatingincome@currentyearduration_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-02 | 期間だけ違う | `researchanddevelopmentexpensessga@prior1yearduration_nonconsolidatedmember` | `researchanddevelopmentexpensessga@currentyearduration_nonconsolidatedmember` | `researchanddevelopmentexpensesresearchanddevelopmentactivities@currentyearduration` |
| S100Z4GF-T5-04 | 科目が違う | `noncurrentassets@currentyearinstant_nonconsolidatedmember` | `assets@currentyearinstant_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-05 | 参照先を出さない | `subsidyincomeetcnoi@currentyearduration_nonconsolidatedmember` | (なし) | (なし) |
| S100Z4GF-T5-06 | 参照先を出さない | `subsidyincomeetcnoi@currentyearduration_nonconsolidatedmember` | (なし) | (なし) |
| S100Z4GF-T5-07 | 期間だけ違う | `extraordinaryloss@prior1yearduration_nonconsolidatedmember` | `extraordinaryloss@currentyearduration_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-09 | 参照先を出さない | `costofbusinessrevenue@prior1yearduration_nonconsolidatedmember` | (なし) | (なし) |
| S100Z4GF-T5-10 | 期間と枠が違う | `operatingincome@prior1yearduration_nonconsolidatedmember_jpcrp030000-asr_e37207-000dtxproductbusinessreportablesegmentmember` | `operatingincome@currentyearduration_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-12 | 期間だけ違う | `nonoperatingincome@prior1yearduration_nonconsolidatedmember` | `nonoperatingincome@currentyearduration_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-13 | 期間と枠が違う | `operatingincome@prior1yearduration_nonconsolidatedmember_jpcrp030000-asr_e37207-000dtxplatformbusinessreportablesegmentmember` | `operatingincome@currentyearduration_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-16 | 期間だけ違う | `sellinggeneralandadministrativeexpenses@prior1yearduration_nonconsolidatedmember` | `sellinggeneralandadministrativeexpenses@currentyearduration_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-17 | 枠(次元)だけ違う | `operatingincome@currentyearduration_nonconsolidatedmember_jpcrp030000-asr_e37207-000dtxplatformbusinessreportablesegmentmember` | `operatingincome@currentyearduration_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-20 | 参照先を出さない | `costofbusinessrevenue@currentyearduration_nonconsolidatedmember` | (なし) | (なし) |
| S100Z4GF-T5-21 | 科目が違う | `currentassets@currentyearinstant_nonconsolidatedmember` | `assets@currentyearinstant_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-23 | 期間だけ違う | `nonoperatingexpenses@prior1yearduration_nonconsolidatedmember` | `nonoperatingexpenses@currentyearduration_nonconsolidatedmember` | (なし) |
| S100Z4GF-T5-24 | 科目が違う | `increasedecreaseincontractliabilitiesopecf@currentyearduration_nonconsolidatedmember` | `contractliabilities@currentyearinstant_nonconsolidatedmember` | (なし) |
| S100YYUD-T5-02 | 科目が違う | `totalchangesofitemsduringtheperiod@currentyearduration` | `netassets@currentyearinstant` | `netassets@currentyearinstant` |
| S100YYUD-T5-03 | 科目が違う | `amortizationofgoodwillopecf@currentyearduration` | `goodwill@currentyearinstant` | `goodwill@currentyearinstant` |

分類の内訳(29 件): 科目が違う 10 件(S100YYT4 5・S100YYUD 2・S100Z4GF 3)、期間だけ違う 5 件(すべて S100Z4GF)、枠(次元)だけ違う 2 件(S100Z4GF)、期間と枠が違う 2 件(S100Z4GF)、参照先を出さない 10 件(S100YYT4 6・S100Z4GF 4)。特定 21 件は S100YYT4 11・S100Z4GF 8・S100YYUD 2。

- **S100Z4GF の期間だけ違う 5 件**(T5-02・07・12・16・23)の Core の claim の span は、いずれも『当事業年度の○○は N千円(前事業年度は M千円)』の M(注入した数)を含む。claim の value は M で、pointers は当期の枠(`…@CurrentYearDuration_NonConsolidatedMember`)、gold は前期の枠(`…@Prior1YearDuration_NonConsolidatedMember`)。
- **S100Z4GF の枠(次元)が違う 4 件**(T5-01・17 が枠だけ、T5-10・13 が期間と枠)は『セグメント利益は N千円(前年同期は M千円)』の文で、gold は `…_NonConsolidatedMember_…ReportableSegmentMember`(セグメント別の枠)。Core-P の名指しはセグメントを外した `OperatingIncome@CurrentYearDuration_NonConsolidatedMember` の 1 つで、4 件とも同じ参照先。
- **S100Z4GF の科目が違う 3 件**: T5-04 は gold `NoncurrentAssets`(span は『固定資産合計は、960,000千円』)に対し Core-P は `Assets`、T5-21 は gold `CurrentAssets`(span は『流動資産合計は、18,210,000千円』)に対し `Assets`、T5-24 は gold `IncreaseDecreaseInContractLiabilitiesOpeCF`(契約負債が増加した文)に対し `ContractLiabilities`(残高)。C1 の読み(増減額の文で残高の科目を名指す型)と同じ形は T5-24 の 1 件。
- **S100Z4GF の参照先を出さない 4 件**(T5-05・06・09・20): Core の claim は 4 件とも `POINTER_NOT_FOUND`・reason `no_element`・subject なし(『助成金等収入26,000千円』『事業原価については17,387千円(前事業年度は26,000千円)』など)。P16 では同じ 4 件も参照先を出していない。
- **S100YYT4・S100YYUD の 13 件は P16 と P20 で参照先が同じ**(連結あり。R-C2)。科目が違う 7 件のうち 4 件は C1 の読みと同じ『増減額の文 → 残高の科目』(`NetAssets@CurrentYearInstant` が 3 件・`Goodwill@CurrentYearInstant` が 1 件、うち S100YYT4-T5-01・05 と S100YYUD-T5-02・03)。S100YYT4 の参照先を出さない 6 件は、`POINTER_NOT_FOUND`・reason `no_element` が 5 件(うち 4 件は claim の subject が null で span が『2,044,000千円』のような数だけ、1 件は subject『従業員』)、対応の付かなかった注入が 1 件(T5-20)。gold はセグメント別の枠が 5 件と `SellingGeneralAndAdministrativeExpenses` が 1 件。
- 次元なしの gold 20 件は P16 も P20 も 13 / 20 = 65.0%(同じ書類・同じ行)。次元つきの gold 30 件のうち S100Z4GF 以外の 6 件は P16 も P20 も 0 / 6 = 0.0%(S100YYT4 の 6 件。1 件は誤認定、4 件は参照先なし、1 件は対応が付かない)。

### R-5(外れ、誤認定率の上側): 26 / 55 = 47.3%

分母は Core-P が参照先を出した件 55(T5 40・T1 8・T3 7)で、P16 の 32(T5 21・T1 6・T3 5)から 23 増えた。誤認定 26 件の内訳は T5 の誤認定 19 件と T3 の名指し 7 件。T1 の 8 件は参照先を名指したが『確認済み』と言った件は 0(T1 の通し 0 / 38 = 0.0%)。幅(15〜40%)を上に出たのは、S100Z4GF の T5 で名指しが 1 件から 20 件に増え、そのうち 12 件が違ったため(上の表)。T1 の通しと T3 の名指しは幅の中。

### R-6・R-7(外れ): K-4 の 20 行で Core-P(P20)7 / 20 = 35.0%・次元つき 10 行で 2 / 10 = 20.0%

| 行 | 席 A | Core-P(P16) | Core-P(P20) |
|---|---|---|---|
| 同じ T5 の 20 行 | 16 / 20 = 80.0% | 5 / 20 = 25.0% | 7 / 20 = 35.0% |
| 次元つき 10 行 | 10 / 10 = 100.0% | 0 / 10 = 0.0% | 2 / 10 = 20.0% |
| 次元なし 10 行 | 6 / 10 = 60.0% | 5 / 10 = 50.0% | 5 / 10 = 50.0% |
| S100Z4GF の 8 行 | 8 / 8 = 100.0% | 0 / 8 = 0.0% | 2 / 8 = 25.0% |
| S100Z4GF を除く 12 行 | 8 / 12 = 66.7% | 5 / 12 = 41.7% | 5 / 12 = 41.7% |

- 席 A は C1 の記録の答えのまま(再生成していない)。Core-P(P20)が当てて席 A が外した行は 0。席 A が外した 4 行(S100YYT4-T5-01・05、S100YYUD-T5-02・03)は、Core-P(P20)も同じ参照先を名指していた(4 行とも一致)。
- 席 A が当てて Core-P(P20)が当てなかった行は 9(S100YYT4 が 3、S100Z4GF が 6)。
- 差 +45.0 pt は封の幅(0〜+25 pt)の外。S100Z4GF を除く 12 行の差 +25.0 pt は、C1 の文書にある数と同じ。

### 当たりのうち、読んでおくこと

- **R-1**: 注入の id・件数・gold・改変後の値は P16 と P20 で同じ(注入は本文と refs だけから作られ、profile に依らない)。
- **R-9**: S100Z4J8 は T5 の注入が 0。T3 の名指し 1 / 5 = 20.0% は S100Z4J8-T3-04(『…売上高は N百万円となりました』の作り話の文に対し `NetSales@CurrentYearDuration_NonConsolidatedMember` を名指して VALUE_MISMATCH)。P16 は 0 / 5 = 0.0% だった。S100Z4GF-T3-01 も同じ形の文(『海外関連会社売上高は37百万円となりました。』)で、Core-P は `BusinessRevenueKeyFinancialData@CurrentYearDuration_NonConsolidatedMember` を名指した。
- **R-8**: 先頭の 5. のとおり。(d) の露出は 3 / 55 = 5.5%(S100YYT8-T3-04・S100Z42X-T3-02・S100YYT4-T1-04。state は VALUE_MISMATCH のまま)、U と P の露出は 0。製品の経路の held は 0 / 55 = 0.0%。
- **R-C1〜R-C3**: 先頭の道具が動いていることの対照。下の節。

---

## P16 の数(C0)と P20 の数(今回)を並べる(**同じ 128 件の注入・同じ種・同じ 8 書類**)

C0 の数は `c0_2026-10-20.json` から読んだ(今回の P16 の run も C0 の記録と全欄一致。R-C1)。

| 欄 | P16(C0) | P20(今回) | 分母の出どころ |
|---|---|---|---|
| T5 50 件の Core-P の特定 | 13 / 50 = 26.0% | 21 / 50 = 42.0% | T5 の注入の件数 |
| (参考)cd8 の Core-P の特定 | 46 / 64 = 71.9% | | cd8 の 8 書類の T5 の注入 |
| S100Z4GF の T5 24 件の特定 | 0 / 24 = 0.0% | 8 / 24 = 33.3% | S100Z4GF の T5 の注入 |
| 次元つき gold 30 件の特定 | 0 / 30 = 0.0% | 8 / 30 = 26.7% | gold の枠が `_…Member` つきの T5 |
| うち S100Z4GF 以外の 6 件 | 0 / 6 = 0.0% | 0 / 6 = 0.0% | 同上 |
| 次元なし gold 20 件の特定 | 13 / 20 = 65.0% | 13 / 20 = 65.0% | gold の枠が素の T5 |
| Core-P の誤認定率 | 13 / 32 = 40.6% | 26 / 55 = 47.3% | 参照先を出した件 |
| T1 の通し | 0 / 38 = 0.0% | 0 / 38 = 0.0% | T1 の注入 |
| T3 の名指し | 5 / 40 = 12.5% | 7 / 40 = 17.5% | T3 の注入 |
| S100Z4J8 の T3 の名指し | 0 / 5 = 0.0% | 1 / 5 = 20.0% | S100Z4J8 の T3 の注入 |
| K-4 の 20 行の Core-P の特定 | 5 / 20 = 25.0% | 7 / 20 = 35.0% | C1 の T5 の行(同じ注入の id) |
| 席 A − Core-P の差 | +55.0 pt | +45.0 pt | 席 A は 16 / 20 = 80.0%(C1 の記録) |
| 次元つき 10 行の Core-P の特定 | 0 / 10 = 0.0% | 2 / 10 = 20.0% | K-5 の行 |
| C0-3 で engine が GROUNDED にした件数 | 0 / 32 = 0.0% | 0 / 55 = 0.0% | Core-P が名指した注入の行 |
| C0-3 の (d) 保留の露出 | 3 / 32 = 9.4% | 3 / 55 = 5.5% | 同上 |
| C0-1 の GROUNDED(S100Z4GF) | 1 / 128(claims) | 61 / 128(claims) | 製品の経路の claims(P20 が既定) |
| C0-1 の GROUNDED(S100Z4J8) | 0 / 110(claims) | 78 / 110(claims) | 同上 |

分母は表の右の列。P16 と P20 で分母が違うのは誤認定率と C0-3 だけ(参照先を出した件・名指した行が増えたため)。

---

## 対照 R-C1〜R-C3(道具の故障を作って当てた)

- **R-C1**: 同じ script を P16 で回し、C0 の記録と全欄一致した。(ア) の main() の出力(rows 以外)の違った欄 0、rows 一致(128 行)、C0-3 の rows・集計一致、注入の件数一致、各注入に対応が付いた claim 一致。**期待どおり。**この一致が、`CD8_PROFILE` の差し替えが効いていること(P16 の run が C0 を再現し、P20 の run は連結の無い 2 書類だけが変わる)の根拠になる。
- **R-C2**: 連結のある 6 書類(S100Z0OS・S100YYN7・S100YYT8・S100Z42X・S100YYT4・S100YYUD)の注入 84 件の rows が P16 と P20 で全行一致(84 / 84 = 100.0%)。補助で C0-3 の行も一致。**期待どおり。**連結の無い 2 書類の注入 44 件のうち 27 件が変わった(S100Z4GF が 25 件・S100Z4J8 が 2 件)。
- **R-C3**: cd8 の (ア) を P20 で回し(142 件)、`a_core_vs_grep_P20_2026-10-17.json` と全欄一致(違った欄 0)。**期待どおり。**
- **(ア) の採点と今回の数え直しの照合**(記録 `(ア) の採点と数え直しの照合`): P20 の特定・誤認定率・T1・T3 と P16 の特定が、(ア) の `tally` の出力と数え直した値で一致した。
- 補助(封の外): P20 の run の C-2(無改変の主張の state が動いたか)は、一意に対になった主張 9864 本(延べ)で判定が動いた 0。

---

## 次の改善の封の候補(**事実から。ここでは「改善する」とは書かない。封は別に書く**)

1. **Core の名指しが、括弧内の前期の数に対して当期の枠を指す。**S100Z4GF の期間だけ違う 5 件と、期間と枠が両方違う 2 件(合わせて 7 / 24 件)で、span は『(前事業年度は N千円)』『(前年同期は N千円)』の N を含み、pointers は当期の枠。cd8 の 8 書類でこの型が出ていたかは読んでいない。
2. **セグメント別の文でセグメントを外した単体の科目を名指す。**S100Z4GF の 4 件(枠だけ 2・期間と枠 2)が同じ参照先 `OperatingIncome@CurrentYearDuration_NonConsolidatedMember` を名指した。
3. **増減額の文で残高の科目を名指す型**は連結の 2 書類(S100YYT4・S100YYUD)で 4 件、S100Z4GF で 1 件(T5-24)。C1 の候補 4 と同じ型。標本はまだ薄い。
4. **subject が付かない金額の文(『助成金等収入26,000千円』『2,044,000千円』など)は `no_element`**。参照先を出さない 10 件のうち、S100Z4GF の 4 件と S100YYT4 の 4 件は claim の subject が null。
5. **保留規則 (d)・P・U が誤りを止めるかは、まだ測れていない。**R-8 の 0 も C0 の G-8 の 0・C1 の K-8 の 0 と同じ理由で説明できる(Core が先に止める・T5 の注入は単位込みで一致しない)。C1 の候補 1 のまま。
6. **T5 の標本が千円で書く 3 書類にしか無い**(C0 の G-4)。K-4 の分母は 20 行・3 書類のまま。

---

## 手順の正直な記録

- 実測 script は 1 回だけ走らせ、repo の記録 `c0_p20_2026-10-20.json` はその完走した 1 本(全体 387.8 秒)。scratchpad に向けた予行は走らせていない。**数を初めて見たのはこの 1 回の出力。**
- 予測 R-1〜R-11 は封の追記 2(commit 2b76cc7)のまま。判定の式と幅は script と門に字で書き、数を見てから変えていない。
- 『分類』(科目 → 期間 → 枠)・『S100Z4GF の期間だけ違う 5 件』などの読みは、この script が出した参照先と gold の字から読んだ(分類は門が記録から再計算して縛る)。span の読みは C0-2 の claim の記録(`C0-2 各注入に対応が付いた Core の claim`)から読んだ。
- 『差し替え』: C0 の関数 `c01`・`c02_and_c03_c2` は profile を module 変数 `CD8_PROFILE` から読むため、この script が `C0.CD8_PROFILE` を P20(対照では P16)に差し替えて呼び、`finally` で P16 に戻した。C0 の module は変えていない。

## 迷った点(封の字で 1 通りに決まらなかった所)

1. **R-3 の括弧『(Z4GF 以外の 6 件は 0〜2)』**: 外れ方の欄は『幅の外』なので、判定は 14〜24 / 30 で行い、括弧内の数(0 / 6 = 0.0%、幅の中)は別欄に並べた。
2. **R-6**: 『Core-P(P20)11〜16 / 20』と『差 0〜+25 pt』の両方が成り立つとき当たりと読んだ。実測は両方とも外。
3. **R-5 の分母**: 誤認定率の分母は C0 の G-6 と同じ『参照先を出した件』。P16 の分母 32 と P20 の分母 55 は違うので、表に分母を書いた。
4. **R-8 の分母**: Core-P(P20)が名指した注入の行 55(engine を通せなかった行 0)。
5. **K-4**: 席 A の答えは C1 の記録(`K-4・K-5 の数` の rows)から読み、Core-P(P20)は同じ注入の id の P20 の rows から読んだ。gold が 20 / 20 一致することを確かめた。
6. **R-C2 の『全行一致』**: C0-2 の rows の全欄の json 一致。補助で C0-3 の行も比べた。
7. **R-11 の覆い**: 183 → 184 file と読んだ(封の『覆い +1』)。

## 限界

- **8 書類 1 回**。合格線は作らない。K-4 の分母は 20 行・3 書類。
- 席の答えは再生成していない。席が見た本文は 8 件同時注入の本文で、Core-P の本文は 1 件ずつの注入(C1 と同じ並べ方)。
- **R-8 の 0 は engine の独立した証拠ではない**。
- T5 の site 規則(C0 の G-4)・増減額の文で残高を名指す型には触っていない(封 B-4)。
- T5 の正解は (ア) の `identified_sites` で作られ、正解そのものが誤りうる。S100Z4GF の期間だけ違う 5 件の gold(前期の枠)は、注入が置いた数(『前事業年度は M千円』の M)の持ち主として作られたもの。
- この文書の R-11 の行は、実行した出力を写したので門で縛れない。縛っているのは次のとおり(`tests/measure/test_xbrl_generality_p20_result.py`): (1) 文書の `a / b = x.x%` の分数の全部、(2) 予測表 R-1〜R-10 の実測欄の数(記録の行から数え直した値と順序つきで一致)と予測欄の字(封の同じ行と同じ字)、(3) 判定の当たり/外れ、(4) 『当たり N / 外れ M』、(5) 29 件の表の分類と内訳の件数、(6) R-4・R-6 の判定(記録の行から再計算)、(7) C0・C1 の記録と席の答えの sha256。**縛っていない数**: R-11 の行、span の読みの文面、文章中の ids と日付。
