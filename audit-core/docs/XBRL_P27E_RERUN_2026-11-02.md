# AI の文(1 書類)を P27E と P27 で再判定 ― 止めた真の文 53 行のうち GROUNDED になるのは 7 行(P27E も P27 も同じ行・全部「指せず」T1)、残り 23 行の VALUE_MISMATCH は 12 が VALUE_MISMATCH のまま・11 が POINTER_NOT_FOUND に変わり、GROUNDED は 0。期の取り違え 8 行と「その他」の VALUE_MISMATCH 9 行も GROUNDED は 0 ― **予測 当たり 7 / 外れ 2(M-2・M-9)**

2026-11-02。封 `docs/XBRL_P27E_RERUN_SEAL_2026-11-02.md`(commit `35f624c`。実装より先。この文書の作成でも 1 字も変えていない)。
記録 `fixtures/xbrl/rerun_p27e_2026-11-02.json`(数の正本)と、claim ごとの entry 2 つ(`fixtures/xbrl/entry_output_ai_prose_p27e_2026-11-02.json`・`fixtures/xbrl/entry_output_ai_prose_p27_2026-11-02.json`)。script `measure/xbrl_rerun_p27e_2026-11-02.py`(engine を import して走らせる。engine の字は変えていない)。
材料は封 §0 の 8 file。**engine(`core/`・`adapters/`)は 1 行も変えていない。通信していない(ラベル file は cache から読んだだけ)。0 USD。LLM を呼んでいない。**
この文書の表の数と散文の 3 桁以上の数は門 `tests/measure/test_xbrl_rerun_p27e.py` が記録に縛る。散文の 2 桁以下の数は門が縛らない(記録と目で照らした。【門なし】の印は 3 桁以上で記録に無い数と、目で読んだ分類・数え直しに付けた)。

---

## 1. 欄ごとの当たり / 外れ(封 §3 の字。外れは外れのまま)

| | 予測(封 §3) | 実測(記録) | 判定 |
|---|---|---|---|
| **M-1** | 配線: P27 の 412 claim の state の分布が儀式の記録の素の書類(340・25・33・14)と一致 | 340・25・33・14(GROUNDED・POINTER_NOT_FOUND・UNVERIFIABLE・VALUE_MISMATCH の順。一致) | **当たり** |
| **M-2** | 配線: P16・P27E・P27 の claim は id の順で (span, value, unit) が 412 / 412 対応 | 408 / 412(P27E)、408 / 412(P27)。対応しない P16 の行 4(N110・N111・N255・N256) | **外れ** |
| **M-3** | P16 の 53 行のうち P27E で GROUNDED になるのは 5〜15 | 7 / 53(P27 も 7。型は全部 T1) | **当たり** |
| **M-4** | P16 で GROUNDED の 札 真・num 249 行のうち P27E で GROUNDED でなくなるのは 0〜12 | 1 / 249(N219。ほかに記録で対応しない行 4 は数えない) | **当たり** |
| **M-5** | 期の取り違え 8 行のうち P27E で GROUNDED になるのは 0〜3 | 0 / 8(P27 も 0。全部 VALUE_MISMATCH のまま) | **当たり** |
| **M-6** | 「その他」の VALUE_MISMATCH 9 行のうち P27E で GROUNDED になるのは 0〜2 | 0 / 9(P27 も 0) | **当たり** |
| **M-7** | P27E と P27 で state が違う行は 0〜10 | 1(N213。P27E VALUE_MISMATCH・P27 POINTER_NOT_FOUND) | **当たり** |
| **M-8** | 札 偽 1 行は P27E・P27 とも GROUNDED でない | P27E POINTER_NOT_FOUND・P27 POINTER_NOT_FOUND(T087) | **当たり** |
| **M-9** | P27E で GROUNDED の 札 真・num の行のうち pointers の要素が札の根拠に無いのは 0〜10 | 108 / 251(P27 も 108) | **外れ** |
| **M-10** | 判定不能の行、P16 の entry に無い行、対応しない行の中身は判定しない。数だけ | 判定不能 22(札 415 行のうち記録の 412 行に在る数)。対応しない行 4。P16 の entry に無い札の行 3 | 判定しない |

外れの向き:

- **M-2 は下に外れた**(408 / 412。封の予測 412 / 412)。4 行は行のずれではなく、同じ id が同じ位置に在るが (span, value, unit) の value が変わった(§2)。外れた原因は engine の数の読み取りの変更(P16 の記録のあと、2026-10-21 に入った)で、P27E・P27 の判定の質ではない。封 §2 は「対応しない行は数だけ」。
- **M-9 は上に外れた**(108。予測の上限 10)。封の照らし(pointers の要素の local name が札の根拠の字に在るか)は、根拠が「同」と略された行と数式で書かれた行では当たらない。108 のうち 同(略した根拠) 39・数式(導出の文) 65、要素名を書きうる根拠は 4。**判定は封の定義のまま 外れ**。内訳は §7 の参考の欄で、判定を変えない。
- 当たった 7 のうち、**M-5 は幅(0〜3)には入ったが、封の括弧の中の見立て(「P27 は期を留めるので前期の値は当期と合わないまま」)は当たっていない**: 8 行のうち 5 行は pointers の期が前期に動いた(§6)。それでも state は VALUE_MISMATCH のまま。判定は幅(GROUNDED になる行の数)のまま 当たり。

## 2. 配線(記録の「配線の門」)

- 材料 8 file の sha256 は封 §0 の値と一致(`(a)`)。標準ラベルの 3 file(cache。repo の外)は在り、sha256 が名簿 `fixtures/xbrl/taxonomy_labels_sha256.txt` と合う(`(b)`):

| file | sha256(名簿) |
|---|---|
| `jppfs_2025-11-01_lab.xml` | `bf56ea1585afe426b398a9053ec4de4dbeafc211a53675b5d6d19453e4e04bf4` |
| `jpcrp_2025-11-01_lab.xml` | `df9c23764ec9a63cb65b5ef62e79a2907c590523797421442ea2a60e334cd684` |
| `jpigp_2025-11-01_lab.xml` | `d45c95cc634202973557f5ed935d747ba25e751b7386c5269fe3e7bdb2c82d09` |

- engine の bundle の sha256(`core/`・`adapters/`。`fixtures/frozen_bundle_sha.py` の `bundle()`)は `864b1f96292f1615c7e5b7e3bbd6924ebd9955b8354b3c5d51400ba9a01fb054`、file の数 37、未 commit の file 0(`(c)`)。走らせた HEAD は `d49b46d60aa5b51fae8b8b1836d0b27ce9cb0f34`。script の sha256 は記録の「この script の sha256」(門が木の script と照らす)。
- 53 行・12 行・8 行の数は 53・12・8(`(d)`)。
- **行の対応(`(e)`)**: P16・P27E・P27 の claim は 412 で、id の順で同じ位置の (span, value, unit) が一致したのは P27E・P27 とも 408、探し直して対応したのは 0、対応しない P16 の行は 4(id は N110・N111・N255・N256)。**M-2 は外れ**(§1)。
- 4 行の中身: engine は 2026-10-21 から「円と銭」を 1 つの数に読む(`adapters/xbrl/extract.py` の `_YEN_SEN_RE_2026_10_21`、`adapters/xbrl/vocabulary.py` の G5)。P16(2026-10-13)は円だけを読み、銭を落とした数(115.0 円など)になっていた。いまの P27E・P27 は円と銭を足した数(115.43 円など)で、同じ id が同じ位置に在る。

| id | 文の字 | P16 の value | P27E・P27 の value | P16 の state | P27E・P27 の state | pointers の期 |
|---|---|---|---|---|---|---|
| N110 | 115円43銭 | 115.0 円 | 115.43 円 | GROUNDED | GROUNDED | 当期 |
| N111 | 前期236円28銭 | 236.0 円 | 236.28 円 | GROUNDED | GROUNDED | 前期 |
| N255 | 2,096円83銭 | 2096.0 円 | 2096.83 円 | GROUNDED | GROUNDED | 当期 |
| N256 | 同1,897円74銭 | 1897.0 円 | 1897.74 円 | GROUNDED | GROUNDED | 前期 |

  - 表の新しい方の value・state・期は entry 2 つの字から写した(記録の `行` は対応しない行の新しい側を持たない)。4 行とも P27E・P27 で同じ。【門なし】(entry から写した)
  - 記録の `(e) 対応しない P16 の行と同じ位置の新しい行の id が同じ` は P27E・P27 とも true。**対応しない 4 行は、記録の `行` では新しい側の state が空(None)**になる。記録の `249 行で P27E で対応しない` と `249 行で P27 で対応しない` に分けて数え、「GROUNDED でなくなった」には数えない(§3)。
- `(f)` P27 の state の分布は儀式の記録の素の書類と一致(M-1)。配線の門の `通った` は true。
- 配線の門の `通った` は 3 回目の走らせから true(1 回目・2 回目は false。理由は §9)。4 回目の記録も true。

## 3. 動き(札 真・num 302 行。P16 の state → 新しい state)

全 claim の state の分布(列は GROUNDED・VALUE_MISMATCH・UNVERIFIABLE・POINTER_NOT_FOUND の順):

| profile | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND |
|---|---|---|---|---|
| **P16** | 330 | 25 | 41 | 16 |
| **P27E** | 340 | 15 | 33 | 24 |
| **P27** | 340 | 14 | 33 | 25 |

動きの表(行 = P16 の state、列 = 新しい state。札 真・num のうち記録で対応した行。対応しない 4 行は入らない):

| profile | P16 の state | → GROUNDED | → VALUE_MISMATCH | → UNVERIFIABLE | → POINTER_NOT_FOUND |
|---|---|---|---|---|---|
| P27E | **GROUNDED** | 244 | 1 | 0 | 0 |
| P27E | **VALUE_MISMATCH** | 0 | 12 | 0 | 11 |
| P27E | **UNVERIFIABLE** | 6 | 0 | 12 | 0 |
| P27E | **POINTER_NOT_FOUND** | 1 | 0 | 0 | 11 |
| P27 | **GROUNDED** | 244 | 1 | 0 | 0 |
| P27 | **VALUE_MISMATCH** | 0 | 11 | 0 | 12 |
| P27 | **UNVERIFIABLE** | 6 | 0 | 12 | 0 |
| P27 | **POINTER_NOT_FOUND** | 1 | 0 | 0 | 11 |

- GROUNDED に動いたのは 7 行(UNVERIFIABLE から 6・POINTER_NOT_FOUND から 1)で、P27E と P27 で同じ。VALUE_MISMATCH から GROUNDED に動いた行は 0。
- VALUE_MISMATCH 23 行は P27E で 12 が VALUE_MISMATCH のまま・11 が POINTER_NOT_FOUND(11 行とも reason は `no_same_value`)。P27 は 11 が VALUE_MISMATCH のまま・12 が POINTER_NOT_FOUND。P27E と P27 の差は N213 の 1 行(§3 の最後)。
- 句(門が記録に縛る):
  - 53 行で P27E で GROUNDED 7
  - 53 行で P27 で GROUNDED 7
  - 249 行で P27E で GROUNDED でなくなった 1
  - 249 行で P27 で GROUNDED でなくなった 1
  - 249 行で P27E で対応しない 4
  - 249 行で P27 で対応しない 4
  - P27E と P27 で state が違う行 1
  - 12 行で R1 が決まった 8 行のうち P27E で GROUNDED 1

### GROUNDED でなくなった 1 行(N219)と、対応しない 4 行

- 記録の字: `249 行で P27E で GROUNDED でなくなった 1`(id は N219)、`249 行で P27E で対応しない 4`。P27 も同じ(1 と 4)。M-4 の実測は 1 / 249 で 当たり(幅 0〜12)。
- **対応しない 4 行(N110・N111・N255・N256)は新しい側の state が空なので、「GROUNDED でなくなった」には数えない**(封 §2「対応しない行は数だけ」)。この 4 行は entry では P27E・P27 とも GROUNDED のまま(§2 の表)。【門なし】(entry から写した)
- **N219**(GROUNDED でなくなった 1 行): P16 は前期末の `LongTermLoansPayable` を指して GROUNDED。P27E・P27 は当期末の同じ要素を指して VALUE_MISMATCH。期の印の便(`docs/XBRL_PERIOD_MARK_2026-11-02.md` §2-3)の読みでは、札の根拠は当期の 2 つの fact の和で、P16 の GROUNDED は前期の値が偶然同じだったもの。いまは期を当期に留めるので、その偶然の GROUNDED が消えた。【門なし】(読み)
- 期の印の便が「値が両期で同じ」と読んだ N229(`CapitalStock`)と N266(`AmortizationOfGoodwillOpeCF`)は、P16 では前期の fact を指していたが、P27E・P27 では当期の fact を指して GROUNDED のまま。【門なし】(行の pointers の期を目で読んだ)

### P27E と P27 で state が違う 1 行(N213)

- N213(「その他 242 百万円」。「その他」の便・止めた真の文の便の T5): P27E は `AssetRetirementObligationsNCL` の当期末を指して VALUE_MISMATCH(P16 と同じ要素)。P27 は同じ値の fact が見つからず POINTER_NOT_FOUND(reason は `no_same_value`)。どちらも札の根拠(`OtherNCL`)には届かない。P27E に足された B が効いた行は、この書類ではこの 1 行。B の中身はこの文書では扱わない(封の冒頭の語)。【門なし】(読み)

## 4. 53 行(止めた真の文。型 T1〜T6 は `docs/XBRL_DERIVATION_STOPPED_2026-11-02.md` の型)

| 型 | 行数 | P27E で GROUNDED | P27 で GROUNDED |
|---|---|---|---|
| **T1 指せず** | 30 | 7 | 7 |
| **T2 同じ fact** | 1 | 0 | 0 |
| **T3 導出の量** | 3 | 0 | 0 |
| **T4 同じ要素・別の期** | 1 | 0 | 0 |
| **T5 別の要素** | 7 | 0 | 0 |
| **T6 導出も決めない** | 11 | 0 | 0 |

- 53 行の state の分布(P16 は VALUE_MISMATCH 23・UNVERIFIABLE 18・POINTER_NOT_FOUND 12): P27E は GROUNDED 7・VALUE_MISMATCH 12・UNVERIFIABLE 12・POINTER_NOT_FOUND 22。P27 は GROUNDED 7・VALUE_MISMATCH 11・UNVERIFIABLE 12・POINTER_NOT_FOUND 23。
- **GROUNDED になった 7 行(N261・N262・N263・N285・N286・N295・N296)は全部 T1(指せず)**: 営業 CF・投資 CF・財務 CF の当期・前期の行(N263 は営業 CF の 2 期の差)。P16 では主語を fact に結べなかった(UNVERIFIABLE 6・POINTER_NOT_FOUND 1)行で、P27E・P27 は結べた。T2〜T6(P16 で engine が別の fact と比べて止めた 23 行)は GROUNDED 0。
- 7 行の pointers の要素が札の根拠に在るか(封の照らし): 在る 2(N261・N295)、無い 5(N262・N263・N285・N286・N296)。無い 5 のうち N262・N286・N296 は根拠が「同」と略された行、N263 は根拠が数式、N285 は根拠の要素名の綴り(`…InvestmentActivities`)が engine の要素名(`…InvestingActivitiesSummaryOfBusinessResults`)と違う。【門なし】(根拠の字を目で読んだ)
- **VALUE_MISMATCH 23 行の行き先**(型ごと。目で数え直した): T2 の 1 は VALUE_MISMATCH のまま、T3 の 3 は VALUE_MISMATCH 1・POINTER_NOT_FOUND 2、T4 の 1 は VALUE_MISMATCH のまま、T5 の 7 は VALUE_MISMATCH 4・POINTER_NOT_FOUND 3、T6 の 11 は VALUE_MISMATCH 5・POINTER_NOT_FOUND 6。POINTER_NOT_FOUND に変わった 11 行は pointers が空で、reason は全部 `no_same_value`(その文の値と同じ値の fact が見つからない)。【門なし】(型ごとの数え直し)
- 読み: 止めた真の文の便は「直す場所は帯ではなく主語の結びつき」と読んだ(P16 の判定)。**P27E・P27 でも、別の要素や別の期を比べて止めた 23 行は GROUNDED に戻らない**。変わったのは止め方(別の要素と比べて値が合わない → 同じ値の fact が無い)が 11 行で、12 行は P16 と同じく何かの fact と比べて値が合わず VALUE_MISMATCH のまま。主語の結びつきは、この書類では P27・P27E でも未解決。【門なし】(読み)

## 5. 「その他」の 12 行(`docs/XBRL_OTHER_RULE_2026-11-02.md` の 12 行。R1 が決まった 8 行)

- 12 行の state: P27E は GROUNDED 3(N118・N162・N163)・VALUE_MISMATCH 4・POINTER_NOT_FOUND 5。P27 は GROUNDED 3・VALUE_MISMATCH 3・POINTER_NOT_FOUND 6。GROUNDED の 3 行は P16 でも GROUNDED。
- P16 が VALUE_MISMATCH の 9 行のうち P27E で GROUNDED になった行は 0(P27 も 0)。R1 が決まった 8 行のうち GROUNDED は N118 の 1 行だけ(P16 でも GROUNDED。engine が既に `OtherComprehensiveIncome` に結んでいた行)。
- R1 が決まった 8 行の行き先: N080・N144・N290・N299 は POINTER_NOT_FOUND(P27E・P27 とも)、N081・N145 は VALUE_MISMATCH で pointers の期が前期、N213 は P27E で VALUE_MISMATCH・P27 で POINTER_NOT_FOUND。**R1 は engine に入っていない**(その他の便は engine を走らせていない)ので、P27E・P27 の state は R1 の効果を含まない。R1 が候補に決めた 8 行のうち、engine の pointers が R1 の候補と同じ fact なのは N118 の 1 行だけで、残る 7 行は P27・P27E の既存の主語の結びつきでは選ばれていない(pointers が空か別の要素)。【門なし】(読み)

## 6. 期の取り違えの 8 行(`docs/XBRL_PERIOD_MARK_2026-11-02.md` の 8 行)

8 行の state と pointers の期(P27E | P27):

| id | P27E の state / 期 | P27 の state / 期 |
|---|---|---|
| N039 | VALUE_MISMATCH / 当期 | VALUE_MISMATCH / 当期 |
| N041 | VALUE_MISMATCH / 当期 | VALUE_MISMATCH / 当期 |
| N081 | VALUE_MISMATCH / 前期 | VALUE_MISMATCH / 前期 |
| N124 | VALUE_MISMATCH / 前期 | VALUE_MISMATCH / 前期 |
| N145 | VALUE_MISMATCH / 前期 | VALUE_MISMATCH / 前期 |
| N220 | VALUE_MISMATCH / 当期 | VALUE_MISMATCH / 当期 |
| N239 | VALUE_MISMATCH / 前期 | VALUE_MISMATCH / 前期 |
| N294 | VALUE_MISMATCH / 前期 | VALUE_MISMATCH / 前期 |

- 8 行で GROUNDED になった行は P27E・P27 とも 0。pointers の期は、P16 では 8 行とも当期だったのに対し、P27E・P27 では当期 3(N039・N041・N220)・前期 5(N081・N124・N145・N239・N294)。**期は文の期に動いたが、state は 8 行とも VALUE_MISMATCH のまま。**
- 前期に動いた 5 行のうち 4 行は、指している要素が札の根拠の要素と違う(N081 は `RealEstateRentNOI`、根拠は `OtherNOI`。N145 は `CurrentAssets`、根拠は `OtherCA`。N239 は `OtherComprehensiveIncome`、根拠は `ValuationAndTranslationAdjustments`(「その他」の便の読み)。N294 は投資 CF の要約の要素で、文は営業 CF と投資 CF の和)。残る N124 は根拠が「同」と略されていて要素を照らせない(止めた真の文の便 §4 と同じ限界)。期を直しても要素の取り違え(§4・§5)が残るので値が合わない、と読める。【門なし】(根拠の字を目で読んだ)
- 当期のまま残った 3 行: N039(従業員数。根拠は前期末の値。当期末の `NumberOfEmployees` を指す)・N041(臨時従業員)・N220(借入金の合計。根拠は前期末の 2 つの項目の和。pointers は当期・前期の同じ要素と a − b の式)。【門なし】(根拠の字を目で読んだ)
- 期の印の便が挙げた「期を留める」の見込み(同便 §6 の 3)は、値が両期で同じ行(N229・N266)では §3 のとおり当期に動いて GROUNDED のまま。

## 7. M-9 の読み方(参考の欄。判定を変えない)

封の照らし(local name の部分文字列)は、「同」で略した根拠と数式の根拠では当たらない。**M-9 の判定は封の定義のまま 外れ(108)**。記録の「根拠の形(参考)」の内訳は次のとおり。この欄は封の予測の対象ではなく、**判定を変えない**:

| profile | 根拠に無い数 | 同(略した根拠) | 数式(導出の文) | 要素名を書きうる |
|---|---|---|---|---|
| **P27E** | 108 | 39 | 65 | 4 |
| **P27** | 108 | 39 | 65 | 4 |

- 要素名を書きうる根拠の行に限った数は 4(判定の定義で幅 0〜10 に入る数だが、判定は変えない)。4 行は N240・N251・N263・N285。N240・N263 は根拠が数値の式だけで要素名を書かない。N251 と N285 は根拠の要素名の綴りが engine の要素名(`…SummaryOfBusinessResults` つき)と違う。【門なし】(根拠の字を目で読んだ)
- 108 行のうち 103 行は P16 でも GROUNDED の行で、P27E・P27 で新しく GROUNDED になった行ではない。新しく GROUNDED になった 7 行(§4)のうち 5 行が 108 に入る。【門なし】(行から数え直した)
- 読み: M-9 の 外れ(108)は「engine が別の要素で GROUNDED にした向き」の数ではなく、**封の照らしが略した根拠・数式の根拠に当たらない分を多く含む**。ただし、略した根拠・数式の根拠の行で engine の要素が本当に札の要素と同じかは、この文書では言えない(§8)。

## 8. 言えないこと

- 1 書類(1 社)・1 model の AI の文。P27 / P27E の数はこの書類の数で、engine 全体の性質ではない。
- 札の根拠との照らしは local name の部分文字列で、根拠が「同」と略された行・数式の行は照らせない(§7)。108 のうち engine の要素が本当に札の要素と同じ行の数は言えない。
- engine の変更はこの便にない。R1(「その他」の規則)も期の印の規則も engine に入っていない。P27E を外部の文の既定にするかは人間が決める。
- P27E に足された B が何を変えたかは、この書類では N213 の 1 行でしか現れず、他の書類は見ていない。
- 判定不能の行(22)・P16 の entry に無い札の行(3)・対応しない行(4)の中身は判定していない(M-10)。
- 封 §5 にある「cloud の 93 本の赤い門がラベル file で緑になるか」は、この文書を書いた席では測っていない。【門なし】

## 9. 作法

- **走らせた回数: 4 回**(記録は 4 回目。1 回目から 3 回目の副本は scratchpad で、木には無い)。止まった回数 0(出力が既に在る・材料の sha256 の違い・ラベル file の欠け・engine の未 commit・docID 残りのどれでも止まっていない)。
  - **1 回目**: 欠陥が 2 つ同時に在った。(ア) state の分布が GROUNDED 340・他 0 と出て、(f) が false・M-1 が外れになった(1 回目の判定は当たり 6 / 外れ 3)。原因は script の `_dist` が生成器を 1 回で使い切る欠陥(cloud で engine を走らせていなかった script の欠陥)。entry の中身を直接数えると P27 は 340・14・33・25 で儀式の記録と一致していた。`_dist` で list に写す直しを入れた(直し 1)。(イ) 配線の門の `通った` が false。これは `_dist` の欠陥によるものではなく(直し前の `通った` は (f) を含まない)、原因は 2 回目と同じ (e) の対応しない 4 行(1 回目の記録でも (e) は 4 行)。
  - **2 回目**: 分布は正しくなり (f) は true・M-1 は当たりになったが、`通った` はまだ false。理由は 1 回目と同じ (e) の行の対応で、P16 の 4 行(N110・N111・N255・N256)が (span, value, unit) で対応しなかったこと(§2。engine の円と銭の読みの変更)。script の `通った` は「対応しない行 0」を求めていたが、封 §2 は「対応しない行は数だけ」なので、封の字に合わせて「対応しない P16 の行と同じ位置の新しい行の id が同じ・新しい方の余りがその数と等しい」に直した(直し 2。記録に `(e) 対応しない P16 の行と同じ位置の新しい行の id が同じ` の欄が増えた)。**M-2 は外れのまま**(封の予測 412 / 412 に対し 408 / 412。外れは外れ)。
  - **3 回目**: `通った` が true。予測 当たり 7 / 外れ 2。M-10 は判定しない(記録の 249 行の数え方は 4 回目で直した)。
  - **4 回目**: 門 `tests/measure/test_xbrl_rerun_p27e.py` の `_d` にも script の `_dist` と同じ生成器の欠陥(1 回で使い切る)があり、script だけ直ったため門の集計(`ref_tally`)と食い違って赤になった。門の `_d` を list に写す形に直した(直し 3)。あわせて 249 行の「GROUNDED でなくなった」が、対応しない 4 行(新しい state が無い)を数えていた(5 のうち 4 は実際には GROUNDED のまま)ので、script と門の両方で「新しい state が在って GROUNDED でない」に直し、`249 行で P27E で対応しない`・`249 行で P27 で対応しない` の欄を足した(直し 4。封 §2「対応しない行は数だけ」)。249 行で GROUNDED でなくなったのは 1(N219)、対応しないのは 4。**M-4 は当たりのまま**。予測 当たり 7 / 外れ 2 は不変。
  - 直しは script と門の未 commit の変更で、独立監査の対象。封・予測・規則は変えていない。
- 独立監査(`step-auditor`)の REVISE の中身: 監査の結果はこの文書の末尾に追記。
- **cloud で測れなかった理由**: 標準タクソノミのラベル file 3 本(`fixtures/xbrl/taxonomy_labels_sha256.txt` の名簿)の配布元 `disclosure.edinet-fsa.go.jp` が、cloud の送信元(国外のデータセンター)からの要求を遮断した(HTTP 403、本文「Service unavailable. The request is blocked.」。許可ドメインを正しく設定しても同じ。ラベル file の URL もトップページも同じ)。環境の設定では直らず、desktop の folder は cloud から使えなかった。そのため封・script・門まで cloud で進め、測定(engine を走らせる)だけをラベル file のある席に引き継いだ(`docs/XBRL_P27E_RERUN_HANDOVER_2026-11-02.md`)。
- 記録 3 つ(`fixtures/xbrl/rerun_p27e_2026-11-02.json`・上の entry 2 つ)に docID は書いていない(門 `test_a_2` が縛る)。
