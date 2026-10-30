# EDINET タクソノミの限定調査(S100Z4Q1 のみ)

## 0. 範囲と遵守の確認

- **対象は `S100Z4Q1` のみ。** 未開封指定の `S100Z39P` と `S100Z4N9` には触れていない(同じキャッシュ `~/.cache/audit-core/edinet/` に 16 件の zip が在るが、**S100Z4Q1.zip のみを copy して展開した**。他の 2 件はファイル名の存在確認以外のアクセスをしていない)。
- **外部のインスタンス・外部の taxonomy で補完していない。** 標準タクソノミ(`jpcrp_cor`・`jppfs_cor`・`jpdei_cor`)は URL で import されているだけで zip に入っていないが、**FSA のサイトから取得していない**。
- 測定は **scratchpad に取ったコピー**の上で行った(原本 zip に `mv`・`rm` をしていない)。
- 材料: `~/.cache/audit-core/edinet/S100Z4Q1.zip`、sha256 `0731a291f10af5dd207e05d54df8e2b5dc34e79a84de94af1c1a5d4e207228f6`、580,494 bytes、mtime 2026-10-06 13:29。
- **これは語彙としての利用可能性の調査のみ。** 実装・抽出規則の変更・性能実験・81 項目の変更は行っていない。

## 1. zip に含まれるタクソノミファイル(母数の確定)

展開すると 24 htm / 11 xml / 3 xsd / 3 xbrl / 2 gif。タクソノミ関連は 12 ファイル。

```
XBRL/PublicDoc/jpcrp030000-asr-001_E36539-000_2026-06-30_01_2026-09-30.xsd       10,414 B
                                        ..._lab.xml     20,521 B   (日本語ラベル)
                                        ..._lab-en.xml  21,620 B   (英語ラベル)
                                        ..._cal.xml     84,904 B
                                        ..._def.xml    377,213 B
                                        ..._pre.xml    500,143 B
                                        ....xbrl     3,388,617 B   (instance)
XBRL/AuditDoc/jpaud-aai-cc-001_... .xsd / _def.xml / _pre.xml
XBRL/AuditDoc/jpaud-aar-cn-001_... .xsd / _def.xml / _pre.xml
```

**最も重要な範囲の事実**:

> **zip に入っているタクソノミは、提出者の拡張タクソノミだけである。要素宣言は 15 件。**
> `targetNamespace = http://disclosure.edinet-fsa.go.jp/jpcrp030000/asr/001/E36539-000/2026-06-30/01/2026-09-30`
> 標準タクソノミは `xsd:import` 10 件で URL 参照されるのみ(`jpcrp_cor_2025-11-01.xsd`・`jpcrp_rt`・`jppfs_cor_2025-11-01.xsd`・`jppfs_rt`・`jpdei_cor_2013-08-31.xsd`・`jpdei_rt`・`iod`・`xbrl-instance` ほか)。**本体は zip に無い。**

したがって、指示の §5 が求める「要素数とラベルを持つ要素数」「標準ラベル・冗長ラベル等の役割の違い」を**標準タクソノミ全体について答えることは、この範囲ではできない**。以下は 3 つの母数に分けて書く。

| 母数 | 内容 | 件数 |
|---|---|---|
| **(α) 提出者拡張タクソノミ** | zip 内の `.xsd` が宣言する要素 | **15** |
| **(β) filing の linkbase が参照する要素** | `_pre.xml` / `_cal.xml` / `_def.xml` の `loc` が指す要素名(標準タクソノミの要素名が**名前として**取れる) | pre **736** / cal **144** / def **519** の異なり |
| **(γ) instance に実際に現れた fact の要素** | `.xbrl` の fact 要素 | 出現 **1,220** / 異なり **461** |

## 2. 日本語ラベルの有無と種類(母数 α のみ)

`_lab.xml`(日本語):

| 項目 | 値 |
|---|---|
| `loc`(要素参照) | 15 |
| `labelArc` | 30 |
| `label` | 30 |
| role `.../label`(標準ラベル) | **15** |
| role `.../verboseLabel`(冗長ラベル) | **15** |
| ラベルを持つ要素 | **15 / 15(100%)** |
| **1 要素が複数ラベルを持つ** | **15 件(全要素)。最大 2 個**(標準 1 + 冗長 1) |
| ラベル文字列 総数 30 / 異なり 29 | 2 回現れる文字列 **1 件**:「人材戦略に関する基本方針等」(標準ラベルと冗長ラベルが同一文字列) |

`_lab-en.xml`(英語): `loc` 17 / `labelArc` 32 / `label` 31、role は `label` 15 + `verboseLabel` 16。ラベルを持つ要素 16、複数ラベル 15 件。異なり 30 / 重複 1 件。

**役割の違い(観測)**: この filing では標準ラベル(`label`)と冗長ラベル(`verboseLabel`)の 2 役のみ。`terseLabel`・`totalLabel`・`periodStartLabel`・`periodEndLabel` 等は**この zip には現れない**(標準タクソノミ側に在るかは未確認)。
要素の型内訳(α): `nonnum:domainItemType` 6・`xbrli:monetaryItemType` 5・`xbrli:stringItemType` 2・`nonnum:textBlockItemType` 1・`num:percentItemType` 1。`abstract=true` が 8、`false` が 7。

> **母数 α は 15 件しかなく、「81 項目への追加候補」を語るには小さすぎる。** 以下は母数 γ(instance に現れた 461 要素)と、**文書自身がレンダリングしている日本語の行見出し**で測る。

## 3. 文書内の「日本語の見出し ↔ 要素」の対応(母数 γ)

標準要素の日本語ラベルは zip に無いが、**iXBRL の htm に人が読む日本語が描かれている**。これは S100Z4Q1 に含まれる情報なので範囲内。

### 3.1 測り方(自分の計器の限界を先に書く)

22 本の `*_ixbrl.htm` を正規表現で走査し、`<ix:nonFraction>` / `<ix:nonNumeric>` の `name` 属性を取り、同じ `<tr>` の中で**タグを含まない最初のセルのテキスト**を「行見出し」とした。

| 段 | 件数 | 全体比 |
|---|---|---|
| fact 出現 合計 | **1,220**(nonFraction 948 / nonNumeric 272) | 100% |
| `<tr>` の中に在る | 1,026 | 84.1% |
| **うち行見出しが取れた** | **880** | **72.1%** |
| 表の行の外(見出し行・段落・記述ブロック等) | 194 | 15.9% |

> **この 72.1% は私の抽出器の被覆率であって、文書の性質ではない。** 残り 27.9%(340 出現)は、見出しセルがタグを含む行・結合セル・段落中のタグなどで取れなかった。以下の数はすべて **880 出現 / 異なり行見出し 190 / 異なり要素 255** を母数とする。

### 3.2 同一ラベル・類似ラベルの存在(指示 §5-4)

| 項目 | 値 |
|---|---|
| (行見出し, 要素) の組 | **284** |
| 異なり行見出し | **190** |
| 異なり要素 | **255** |
| **同じ行見出しが複数の要素に対応** | **37 / 190 見出し(19.5%)** |
| **同じ要素が複数の行見出しに対応** | **17 / 255 要素(6.7%)** |

**1 見出し → 複数要素(上位)**

| 行見出し | 要素数 | 例 |
|---|---|---|
| 「計」 | **14** | `AuditFeesTotal`・`AuditFeesTotalNetworkFirms`・`NonAuditFeesTotal`・`NotesAndAccountsReceivableTrade` … |
| 「その他」 | **12** | `OtherCA`・`OtherCL`・`OtherIA`・`OtherIOA`・`OtherNCL` … |
| 「所有株式数(単元)」 | 9 | `NumberOfSharesHeldNumberOfUnits{FinancialInstitutions,ForeignIndividualInvestors,…}` |
| 「株主数(人)」 | 8 | `NumberOfShareholders{…}` |
| 「所有株式数の割合(％)」 | 7 | `PercentageOfShareholdings{…}` |
| 「取締役(監査等委員を除く。)(社外取締役を除く。)」 | 5 | `FixedRemuneration…`・`TotalAmountOfRemunerationEtc…`・`NumberOfDirectorsAndOtherOfficers…` |
| 「社外役員」 | 5 | 同上 |
| 「提出会社」 | 4 | `AuditFeesReportingCompany`・`NonAuditFeesReportingCompany` … |

**1 要素 → 複数見出し(上位)**

| 要素 | 見出し数 | 見出し |
|---|---|---|
| `jpcrp_cor:NumberOfSharesIssuedSharesVotingRights` | 7 | 単元未満株式・完全議決権株式(その他)・完全議決権株式(自己株式等)・無議決権株式・発行済株式総数 … |
| `jppfs_cor:NetAssets` | 3 | 当期末残高・当期首残高・純資産合計 |
| 役員報酬系 5 要素 | 各 3 | 取締役(監査等委員)…・取締役(監査等委員を除く。)…・社外役員 |

**観測の読み(独自推論)**: 曖昧さの出どころは 2 系統に分かれる。
1. **列・区分が意味を持つ表**(株主構成・役員報酬・監査報酬):行見出しは「区分」で、要素名は「区分 × 指標」。**行見出しだけでは原理的に決まらない**。決めているのは列(または次元メンバー)。
2. **期間が意味を持つ行**(`NetAssets` の当期首/当期末/合計):要素は同じで、**context(期間)が違う**。これは行見出しが要素を一意に決めないのではなく、**要素だけでは fact を一意に決めない**ことの現れ。VeriFin 論文 §3.5 の「概念だけでは fact は一意に定まらない ― 期間と単位が要る」という記述と同じ現象。

## 4. 最長一致で候補生成できる範囲と、その限界(指示 §5-6,7)

### 4.1 本番の規則をそのまま使って測った

本番の `audit-core/adapters/xbrl/extract.py:subject_of` を**読み込んで呼んだ**(実装は変えていない)。規則は「数の手前で終わり位置が最も右の語、同じなら長い語」。
要素名の照合は `audit-core/adapters/xbrl/instance.py:facts_for`(142-158)の述語をそのまま写した:
- **exact**: `local == e` または `local == e + "SummaryOfBusinessResults"` または `local == e.replace("Income","IncomeLoss") + "SummaryOfBusinessResults"`
- **loose**(exact が無いときだけ): `e.lower() in local.lower()`(部分一致)

> **注意(自分の誤りの記録)**: 最初に集合の完全一致だけで測り「候補が実際の要素を含まない 47 件」と出した。これは `facts_for` の `SummaryOfBusinessResults` 補正と部分一致フォールバックを無視した**私の計器の欠陥**で、本番規則で測り直すと 13 件だった。以下は測り直した数。

### 4.2 現行 81 項目(`SUBJECTS_P6`)の素性

| 項目 | 値 |
|---|---|
| 件数 | **81**(= `SUBJECTS_P6_EXTRA_7` 7 + `SUBJECTS_74` 74。`SUBJECTS_74` = `SUBJECTS_BASE_39` 39 + `SUBJECTS_RUN_B_EXTRA_34` 34 + 1) |
| 異なり語 | **78**(3 語が重複エントリ) |
| 候補要素名の異なり | **77** |
| **1 語が複数の候補要素を持つ** | **28 件。最大 3 個** |

→ **設計上すでに「候補生成」であって「一意の確定」ではない。** 指示の「最長一致は候補生成方法として評価するだけ」という扱いは、現行実装の実際と一致している。

### 4.3 S100Z4Q1 の行見出しに当てた結果

| 段 | 件数 | 比 |
|---|---|---|
| 異なり行見出し(母数) | 190 | 100% |
| **最長一致で語が当たった見出し** | **76** | **40.0%** |
| 当たった見出しが覆う fact 出現 | 344 / 880 | **39.1%** |
| 当たらなかった見出し | 114 | 60.0%(覆う出現 536) |

**当たった 76 件の内訳(本番述語)**

| 分類 | 件数 |
|---|---|
| **exact**(完全一致 or `SummaryOfBusinessResults` 補正で一致) | **34** |
| **loose**(部分一致でのみ当たる) | **29** |
| **どちらも当たらない** | **13** |

### 4.4 最長一致だけでは概念を一意に確定できないケース(実測)

**(a) loose の部分一致が、親子関係にある別概念を「当たり」にする** ― 最も重い型

| 行見出し | 当たった語 | 候補 | 実際の要素 | 判定 |
|---|---|---|---|---|
| 流動資産合計 | 資産合計 | `Assets` | `CurrentAssets` | exact✗ loose✓ |
| 固定資産合計 | 資産合計 | `Assets` | `NoncurrentAssets` | exact✗ loose✓ |
| 無形固定資産合計 | 資産合計 | `Assets` | `IntangibleAssets` | exact✗ loose✓ |
| 投資その他の資産合計 | 資産合計 | `Assets` | `InvestmentsAndOtherAssets` | exact✗ loose✓ |
| 流動負債合計 | 負債合計 | `Liabilities` | `CurrentLiabilities` | exact✗ loose✓ |
| 固定負債合計 | 負債合計 | `Liabilities` | `NoncurrentLiabilities` | exact✗ loose✓ |
| 負債純資産合計 | 純資産合計 | `NetAssets` | `LiabilitiesAndNetAssets` | exact✗ loose✓ |
| 自己資本利益率 | 自己資本 | `Equity`,`NetAssets` | `RateOfReturnOnEquitySummaryOfBusinessResults` | exact✗ loose✓ |
| １株当たり純資産 | 純資産 | `NetAssets`,`Equity` | `NetAssetsPerShareSummaryOfBusinessResults` | exact✗ loose✓ |
| １年内返済予定の長期借入金 | 長期借入金 | ― | `CurrentPortionOfLongTermLoansPayable` | exact✗ loose✓ |

`"Assets".lower() in "CurrentAssets".lower()` は真。**「資産合計」と「流動資産合計」は違う概念だが、語の最長一致は後者の中の前者を拾い、要素名の部分一致も通る。**
**ただし本番の挙動はこれより安全**: `facts_for` は `return exact or loose` なので、**同じ context に exact の fact が在れば loose は発火しない**。加えて `ctx_ok`(期間・メンバー)で絞られる。したがってこの表は「語彙の弁別力」の測定であって、**Audit Core をこの書類に流したときの束縛結果ではない**(この経路の実測は本調査では行っていない。**未確認**)。

**(b) 語が当たるのに概念が別で、exact も loose も当たらない(= 保留になる)** ― 13 件

| 行見出し | 語 | 候補 | 実際 |
|---|---|---|---|
| 潜在株式調整後１株当たり当期純利益 | １株当たり当期純利益 | `BasicEarningsLossPerShare` | `DilutedEarningsPerShareSummaryOfBusinessResults` |
| 配当性向 | 配当 | `DividendPaidPerShare` | `PayoutRatioSummaryOfBusinessResults` |
| (比較指標:配当込み TOPIX) | 配当 | `DividendPaidPerShare` | `TotalReturnOnSharePriceIndex` |
| 受取配当金 | 配当 | `DividendPaidPerShare` | `DividendsIncomeNOI` |
| 受取利息及び受取配当金 | 配当 | `DividendPaidPerShare` | `InterestAndDividendsIncomeOpeCF` |
| 有形固定資産合計 | 資産合計 | `Assets` | `PropertyPlantAndEquipment` |
| 従業員給料及び手当 | 従業員 | `NumberOfEmployees` | `EmployeesSalariesAndAllowancesSGA` |
| 退職給付に係る資産 / 負債 | 同名 | `RetirementBenefitAsset` / `Liability` | `NetDefinedBenefitAsset` / `Liability` |
| 退職給付に係る資産/負債の増減額 | 同名 | 同上 | `IncreaseDecreaseInNetDefinedBenefit*OpeCF` |

**「潜在株式調整後１株当たり当期純利益」(希薄化後 EPS)が「１株当たり当期純利益」(基本 EPS)の語を拾う**のは、最長一致の典型的な失敗。幸い要素名が一致しないので**この書類では保留に落ちる**(安全側)。しかし **語彙に `潜在株式調整後１株当たり当期純利益` を足さずに `DilutedEarningsPerShare` を足すと、基本 EPS の語が希薄化後の要素に部分一致して当たりに化ける危険がある**(独自推論)。

**(c) 「退職給付に係る資産/負債」は語が完全一致するのに要素名の世代が違う** ― 語彙の `RetirementBenefitAsset/Liability` に対し EDINET 2025-11-01 は `NetDefinedBenefitAsset/Liability`。**語彙の要素名が taxonomy の版と合っていない可能性**を示す 1 例(他の版での確認は未実施。**未確認**)。

## 5. 現行 81 項目と比べた追加候補になり得る語彙(指示 §5-8)

**当たらなかった 114 見出しのうち出現の多いもの**(出現 = 行見出しつき fact の数)

| 出現 | 行見出し | 対応する要素 | 追加候補としての見立て(独自推論) |
|---|---|---|---|
| 44 | 当期首残高 | `NetAssets` ほか | **語彙に足すべきでない。** 期間を表す語で、概念を決めない。これは context で解くもの |
| 44 | 当期末残高 | `NetAssets` ほか | 同上 |
| 44 | 当期変動額合計 | `TotalChangesOfItemsDuringThePeriod` | 候補になる(株主資本等変動計算書) |
| 28 | その他 | `OtherCA`/`OtherCL`/… | **足すべきでない**(12 要素に対応) |
| 19 | 計 | 14 要素 | **足すべきでない** |
| 18 | 自己株式の処分 | `DisposalOfTreasuryStock` | 候補になる |
| 17 | 株主資本以外の項目の当期変動額(純額) | `NetChangesOfItemsOtherThanShareholdersEquity` | 候補になる |
| 12 | 自己株式の取得 | `PurchaseOfTreasuryStock` | 候補になる |
| 10 | 株価収益率 | `PriceEarningsRatioSummaryOfBusinessResults` | 候補になる(PER) |
| 10 | [外、平均臨時雇用者数] | `AverageNumberOfTemporaryWorkers` | 候補になる。**現行の「従業員数」と衝突しうる**(従業員数(人)の行で `AverageNumberOfTemporaryWorkers` と `NumberOfEmployees` の 2 要素が同一見出しに対応している実測あり) |
| 9 | 資本金 | `CapitalStock` | 候補になる |
| 9 | 所有株式数(単元) | 9 要素 | **足すべきでない** |
| 8 | 株主数(人) | 8 要素 | **足すべきでない** |
| 8 | 提出会社 / 連結子会社 | 監査報酬系 4 要素ずつ | **足すべきでない**(区分語) |

**追加候補として形になりそうなもの(この 1 書類の観測から)**: 当期変動額合計・自己株式の処分・自己株式の取得・株主資本以外の項目の当期変動額(純額)・株価収益率・資本金・平均臨時雇用者数・潜在株式調整後１株当たり当期純利益・配当性向 の **9 語前後**。
**足してはいけないものが明確に分かれた**: 「計」「その他」「提出会社」「連結子会社」「所有株式数(単元)」「株主数(人)」「当期首残高」「当期末残高」のような**区分語・期間語**。これらは行見出しとしては頻出(合計 200 出現超)だが、**概念を決めない**。

> **重要な留保**: これは **1 書類の観測**である。CLAUDE.md の歯止め「増やしたら必ず測る・測らずに増やさない」に従えば、語彙の追加は(a)複数書類で出現を確認し、(b)追加前に沈黙率と誤認を測る予測を書き、(c)追加後に測る、という手順が要る。**本調査は提案に留め、81 項目は変更していない。**

## 6. 計算関係の存在確認(FinAuditing / VeriFin との関係)

| linkbase | loc | 異なり要素 | arc | link 役割 | 参照先 |
|---|---|---|---|---|---|
| `_pre.xml` | 965 | 736 | 918 | 47 | jpcrp_cor 605 / jppfs_cor 345 / 拡張 15 |
| `_cal.xml` | **186** | **144** | **176** | 8 | jppfs_cor 182 / 拡張 4 |
| `_def.xml` | 742 | 519 | 699 | 43 | jpcrp_cor 372 / jppfs_cor 354 / 拡張 16 |

instance: fact 出現 1,220 / 異なり要素 461 / **context 162** / **unit 4**。名前空間別の fact 出現は jpcrp_cor 605・jppfs_cor 575・jpdei_cor 27・拡張 13。

> **calculation linkbase は存在し、176 の arc を持つ。** VeriFin が式の権限の第 1 の出所に使い、FinAuditing の FinMR が正解に使っているものが、EDINET の書類にも在ることを確認した。**ただし、これを Audit Core の契約に使う設計・実装・実験は本調査の範囲外。**
> context が 162 件あることは、「要素 + 期間 + 単位 + 次元メンバー」の組で初めて fact が決まることを数で示している(461 要素に対し 1,220 fact)。

## 7. 未確認事項

1. **標準タクソノミ(jpcrp_cor / jppfs_cor / jpdei_cor 2025-11-01)の要素数・ラベル数・ラベル役割の種類。** zip に無く、外部から取得していないため。「EDINET 全体で何語あるか」はこの調査では答えられない。
2. `terseLabel`・`totalLabel`・`periodStartLabel`・`periodEndLabel` 等の役割が標準タクソノミに在るか。
3. 行見出しが取れなかった 340 出現(27.9%)の中身。私の抽出器の限界。
4. **Audit Core を S100Z4Q1 に流したときの実際の束縛結果**(`facts_for` の `exact or loose` と `ctx_ok` を通した後の数)。本調査は語彙の弁別力だけを測った。
5. 語彙の要素名(`RetirementBenefitAsset` 等)がどの taxonomy 版に対応しているか。
6. 他の書類での再現(1 書類の観測である)。
7. 日本に DQC(米国 Data Quality Committee)相当の、公開された決定論的な誤り判定基盤が在るか。
8. 次元メンバー(axis/member)による曖昧性解消が `_def.xml` の 699 arc からどこまで機械的にできるか。
