# 結果: 10 分の再現の儀式(買い手が鍵なし・0 USD で「誤りを通さない」を自分の手で確かめる入口、2026-10-20)

封: `docs/XBRL_RITUAL_SEAL_2026-10-20.md`(本文 §0〜§3 と予測 R-1〜R-8 は 1 字も直していない。追記は封の側の日付つきの追記だけ)。測定: `measure/ritual_2026-10-20.py`。記録: `fixtures/xbrl/ritual_2026-10-20.json`。門: `tests/measure/test_xbrl_ritual_result.py`。**API 鍵なし・0 USD・初回のラベル取得を除き通信なし・engine(`core/`・`adapters/`)0 行。**

## 0. 結論

**予測 当たり 7(うち R-1 は条件つき)/ 外れ 1(R-7。機械依存)**(R-1〜R-8。判定は §1。数は記録から門が求め直す)。

- **通した 17 / 241 = 7.1%**(同梱の 1 書類の経営分析の文の数を 1 つずつわざと変え、書類が GROUNDED のまま通した数)。止めた 224 / 241 = 92.9%。
- 通した 17 の中身: 丸めの帯の中(±1 最小単位)16(率 12・金額ほか 4)・退化値 1・帯の外 0。**帯の外で通した 0 は、この 1 書類・この 2 型の注入での数で、engine 全体の性質ではない。**
- 通した 17 のうち、注入の前後で GROUNDED の参照先が別の期の fact に移ったのが 2 件(§2)。通した = 同じ参照先で値だけ通した、ではない。
- 所要 20.9 秒(ラベル 2 file が在る機械)。買い手は clone した直後に、**初回に 1 回だけラベル 2 file を取れば**、1 コマンドで同じ数を見られる(同梱 zip は git に追跡済み・sha256 を門が字で留める)。

## 0-1. 依存の見落とし(2026-10-20)

- 封は『この zip 以外の入力を読まない(`~/.cache` を見ない)』と書いたが、engine は書類の検証のたびに**標準タクソノミのラベル 2 file**(jppfs・jpcrp の 2025-11-01 版、約 8 MB。`adapters/xbrl/instance.py` の `TAXONOMY_DIR_DEFAULT`、環境変数 `EDINET_TAXONOMY_DIR` で変えられる)を `~/.cache/audit-core/edinet-taxonomy/2025-11-01/` から読む。無いと `FileNotFoundError` で落ちる。**clone 直後の機械では儀式は走らない。**独立監査の席が発見した(実装席の最初の版の門は `HOME` の差し替えを import の後に掛けていて、実 HOME のラベルを黙って読んで緑だった ― 偽の保証)。
- 司令塔の決定(選択肢 2): ラベルは repo の外のまま(2026-10-08 の人間の決定を動かさない。金融庁の著作権表示あり)。README の手順 0 に『初回に 1 回だけ EDINET から取る』を書き、`fixtures/xbrl/TAXONOMY_LABELS_README.md` に手順と sha256 がある。選択肢 1(8 MB の同梱)は人間が望めば後から。封には日付つきの追記を足した(本文・予測は不変)。
- 直した: (1) 儀式は起動時にラベル 2 file の存在と sha256 を確かめ、無ければ **10 行以内の案内を出して rc=2 で止まる**(`FileNotFoundError` を裸で出さない)。(2) 記録の『通信』の欄を、script 自身は通信の module を import しない・adapters は urllib を import するが接続は起きない・通信は初回のラベル取得だけ、に。(3) 走らせ直しの門を subprocess にし、`HOME=<空の dir>`・`EDINET_TAXONOMY_DIR=<実在のラベル dir>`・接続を潰した状態で走らせる。(4) 走らせ直しの門を `AUDIT_CORE_RITUAL=1` のときだけ走る形に分けた(R-7)。門の中でラベル dir を渡さない変異(門のコード)は `RerunHeavyTest` が赤。環境変数 `EDINET_TAXONOMY_DIR` を空の dir にすると、`AUDIT_CORE_RITUAL=1` のときは重い門が fail(『AUDIT_CORE_RITUAL=1 を指定したがラベル 2 file が無い。手順 0 を先に』)、環境変数なしの既定では理由つきで skip し、軽い門 `LabelTest.test_13`・`test_14`・`test_17` が rc=2 の案内を見る(§4)。

## 1. 予測 R-1〜R-8(封の字。実装の前に固定。判定は記録・封・git から門が求め直す)

**R-2・R-4・R-5 の幅は封 §0-1 の先に測った数の写しで、当たって当然の再現**(同じ道具・同じ既定で同じ数が出ることの確認であり、予測が難しかったのではない)。

| # | 予測(封の字) | 実測 | 判定 |
|---|---|---|---|
| **R-1** | 儀式の所要は clone 直後の機械で **60 秒以内**(司令塔の機械で 25〜40 秒。verify 1.3 秒 + 注入 241 件の再検証) | 儀式の所要は 20.9 秒(素の書類の検証 1.1・注入の再検証 19.7。記録を採った機械)。60 秒以内に収まった。封の括弧の見込み『25〜40 秒』より短かった(括弧は予測の外れ方に入っていない)。**ただし標準タクソノミのラベル 2 file が在る機械での所要で、ラベルの無い clone 直後の機械では走らない(§0-1)** | **当たり**(条件つき: ラベル 2 file が在る機械。clone 直後のラベル無しの機械では走らない) |
| **R-2** | 注入の対象 **241**、止めた **224**、通した **17**(§0-1 と同じ数。同じ道具・同じ既定なので差 0) | 注入の対象 241・止めた 224・通した 17(241 = 224 + 17)。封 §0-1 と差 0。同じ道具・同じ既定で、門が走らせ直しても記録と一致 | **当たり** |
| **R-3** | 通した 17 のうち **「値が変わっていない注入」(V1 の `0 → 00` 型)が 1 件**。これは注入道具の退化値で、儀式では「注入として数えない」のではなく **通した側に残したまま理由を書く**(隠さない) | 値が変わっていない通した 1 件(N096 `0百万円 → 00百万円`。値は 0 のまま)。注入として数えないのでなく、通した側に残して理由を §2 に書いた | **当たり** |
| **R-4** | 通した 17 を「丸めの帯の中(率 ±0.1 pt・金額 ±1 最小単位)」で分けると **16 件が帯の中**、帯の外で通した **0 件** | 丸めの帯の中 16(率 12・金額ほか 4)、退化値 1、帯の外 0。帯の外で通した 0 | **当たり** |
| **R-5** | 素の書類の state 分布は §0-1 と **全欄一致**(既定 P21) | 素の書類 claim 412、GROUNDED 330・POINTER_NOT_FOUND 16・UNVERIFIABLE 41・VALUE_MISMATCH 25(封 §0-1 と全欄一致。profile P21) | **当たり** |
| **R-6** | README の「10 分の再現」の節に書く数は 通した 17 / 241 = 7.1% を**先頭**に、止めた 224 / 241 = 92.9%。門が README と記録の 1 対 1 を縛り、**記録を 1 字変えると赤・README を 1 字変えると赤**(変異で確かめる) | README と README.en.md の節は 17 / 241 = 7.1% を先頭に、224 / 241 = 92.9%。門が節の全文を記録から作った字と完全一致で縛り、記録 1 字・README 1 字(日本語・英語)・通した 17 を 16 に・zip の変更・分け方の書き換えは全部赤(§4)。ラベルの手順 0 と N125・N199 の注記も節の全文一致で縛る | **当たり** |
| **R-7** | 門 (ii) の「走らせ直して一致」は pytest の既定で **30 秒以内**に収まり、`tests/measure` 全体の所要(2026-10-20 時点 約 106 秒)を **150 秒以内**に保つ | 司令塔の機械: 門の走らせ直し 21.5〜24.5 秒(30 秒以内)、`tests/measure` 全体 134.2〜140.9 秒(150 秒以内)で当たり。**監査席の機械: 全体 164〜168 秒で 150 秒超 → 外れの側。** 機械依存の外れで、封の外れ方どおり走らせ直しの門(20 秒超の本)を `AUDIT_CORE_RITUAL=1` のときだけ走る形に分けた。分けた後の既定の `tests/measure` は 109.4 秒、`AUDIT_CORE_RITUAL=1` では 131.2 秒(司令塔の機械)。他の席の機械の秒は門が字で留めている(再現はできない) | **外れ**(機械依存。外れ方どおり分けた) |
| **R-8** | engine(`core/`・`adapters/`)0 行。`measure/false_pass_2026-10-14.py` も 0 行(import して使う。`main` が cache からしか読めないので、儀式は zip のバイト列を自分で読んで `run_doc` に渡す) | 封の commit から `git diff --numstat -- core adapters measure/false_pass_2026-10-14.py` が空、`git status --porcelain` も空(門が毎回確かめる)。false_pass は import して使い、`main` は使っていない | **当たり** |

**当たり 7(R-1 は条件つき)/ 外れ 1(R-7)**。封も予測も直していない。

## 2. 通した 17 の一覧と読み

| id | 型 | 元の字 | 後の字 | 値(前 → 後) | 単位 | 参照先(前 → 後) | 分け方 |
|---|---|---|---|---|---|---|---|
| N033 | V2 | `67.5%` | `67.6%` | 67.5 → 67.6 | % | `xbrl:jppfs_cor:CostOfSales@Prior1YearDuration` → `xbrl:jppfs_cor:CostOfSales@Prior1YearDuration` | 丸めの帯の中(±1 最小単位) |
| N069 | V2 | `3.8%` | `3.9%` | 3.8 → 3.9 | % | `xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration` → `xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration` | 丸めの帯の中(±1 最小単位) |
| N011 | V2 | `61.7%` | `61.8%` | 61.7 → 61.8 | % | `xbrl:jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults@CurrentYearInstant` → `xbrl:jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults@CurrentYearInstant` | 丸めの帯の中(±1 最小単位) |
| N096 | V1 | `0百万円` | `00百万円` | 0.0 → 0.0 | 円 | `xbrl:jppfs_cor:ImpairmentLossEL@CurrentYearDuration` → `xbrl:jppfs_cor:ImpairmentLossEL@CurrentYearDuration` | 退化値(字は変わるが値が変わらない) |
| N017 | V2 | `2.9%` | `2.8%` | 2.9 → 2.8 | % | `xbrl:jppfs_cor:NetSales@CurrentYearDuration` → `xbrl:jppfs_cor:NetSales@CurrentYearDuration` | 丸めの帯の中(±1 最小単位) |
| N031 | V2 | `7.1%` | `7.2%` | 7.1 → 7.2 | % | `xbrl:jppfs_cor:CostOfSales@CurrentYearDuration` → `xbrl:jppfs_cor:CostOfSales@CurrentYearDuration` | 丸めの帯の中(±1 最小単位) |
| N037 | V2 | `29.8%` | `29.9%` | 29.8 → 29.9 | % | `xbrl:jppfs_cor:GrossProfit@CurrentYearDuration` → `xbrl:jppfs_cor:GrossProfit@CurrentYearDuration` | 丸めの帯の中(±1 最小単位) |
| N045 | V2 | `6.1%` | `6.2%` | 6.1 → 6.2 | % | `xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@CurrentYearDuration` → `xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@CurrentYearDuration` | 丸めの帯の中(±1 最小単位) |
| N113 | V2 | `13.3%` | `13.4%` | 13.3 → 13.4 | % | `xbrl:jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults@Prior1YearDuration` → `xbrl:jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults@Prior1YearDuration` | 丸めの帯の中(±1 最小単位) |
| N125 | V2 | `2百万円` | `3百万円` | 2000000.0 → 3000000.0 | 円 | `xbrl:jppfs_cor:ForeignCurrencyTranslationAdjustmentNetOfTaxOCI@CurrentYearDuration` → `xbrl:jppfs_cor:ForeignCurrencyTranslationAdjustmentNetOfTaxOCI@Prior1YearDuration`(動いた) | 丸めの帯の中(±1 最小単位) |
| N199 | V2 | `19百万円` | `18百万円` | 19000000.0 → 18000000.0 | 円 | `xbrl:jppfs_cor:ProvisionForLossOnOrderReceivedCL@CurrentYearInstant` → `xbrl:jppfs_cor:ProvisionForLossOnOrderReceivedCL@Prior1YearInstant`(動いた) | 丸めの帯の中(±1 最小単位) |
| N131 | V2 | `8.9%` | `8.8%` | 8.9 → 8.8 | % | `xbrl:jppfs_cor:Assets@CurrentYearInstant` → `xbrl:jppfs_cor:Assets@CurrentYearInstant` | 丸めの帯の中(±1 最小単位) |
| N177 | V2 | `6.1%` | `6.2%` | 6.1 → 6.2 | % | `xbrl:jppfs_cor:Liabilities@CurrentYearInstant` → `xbrl:jppfs_cor:Liabilities@CurrentYearInstant` | 丸めの帯の中(±1 最小単位) |
| N237 | V2 | `△22百万円` | `△23百万円` | -22000000.0 → -23000000.0 | 円 | `xbrl:jppfs_cor:TreasuryStock@Prior1YearInstant` → `xbrl:jppfs_cor:TreasuryStock@Prior1YearInstant` | 丸めの帯の中(±1 最小単位) |
| N251 | V2 | `61.7%` | `61.8%` | 61.7 → 61.8 | % | `xbrl:jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults@CurrentYearInstant` → `xbrl:jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults@CurrentYearInstant` | 丸めの帯の中(±1 最小単位) |
| N225 | V2 | `10.8%` | `10.9%` | 10.8 → 10.9 | % | `xbrl:jppfs_cor:NetAssets@CurrentYearInstant` → `xbrl:jppfs_cor:NetAssets@CurrentYearInstant` | 丸めの帯の中(±1 最小単位) |
| N277 | V2 | `△780百万円` | `△781百万円` | -780000000.0 → -781000000.0 | 円 | `xbrl:jppfs_cor:IncomeTaxesPaidOpeCF@CurrentYearDuration` → `xbrl:jppfs_cor:IncomeTaxesPaidOpeCF@CurrentYearDuration` | 丸めの帯の中(±1 最小単位) |

分け方は値の差だけで決めた機械の分け方(差 0 = 退化値、表記の最後の 1 桁以内 = 帯の中、それより大きい = 帯の外)。門は表記の字から独立に求め直して一致を見る。

- **型別**: V1(最小の桁の 1 字を変える)は対象 118・通した 1・止めた 117、V2(値を ±1 最小単位)は対象 123・通した 16・止めた 107(記録の `型別`)。
- **率 12 件**(帯の中): 小数 1 位の率の ±0.1(`67.5% → 67.6%` など)。engine が通した。
- **金額 4 件**(帯の中): `2百万円 → 3百万円`・`19百万円 → 18百万円`・`△22百万円 → △23百万円`・`△780百万円 → △781百万円`。百万円単位の ±1。封 §0-1 は『金額 5 件』と書いたが、V2 の 16 件は率 12 + 金額 4 で、5 は退化値 1 件を足した数。**封の字の数え違い(2026-10-20 の訂正。封は直さない。この注記が日付つきの訂正)。**
- **退化値 1 件**(N096): `0百万円 → 00百万円`。字は変わるが値は 0 のままで、注入として数える意味が無い。注入道具(`false_pass`)の欠陥。数えないのでなく通した側に残した。
- **参照先が動いた 2 件**(N125・N199。測った事実): 注入後の値が、元の参照先の当期でなく前期の fact の値に合ったため、GROUNDED のまま参照先が `CurrentYear...` から `Prior1Year...` に移った。±1 の差で、別の期の fact に当たって通った。
- **読み(人の読み。門で縛らない)**: 表記が小数 1 位の率や百万円単位の金額なので、±1 最小単位の差は書類の丸めの幅と区別できず、engine は同じ値として GROUNDED を返した。これを欠陥と読むか限界と読むかは買い手が決める。儀式は隠さず見せるだけで、どの参照先が正しいかは測っていない。

## 3. 限界

- この 1 書類は経営分析の節が AI の文(2026-10-09 の実験)に差し替わっていて、原文ではない。同梱できる書類はこれだけ(他の書類は `~/.cache` にしか無く、EDINET の鍵が要る)。**同梱書類で回すにもラベル 2 file が要る(初回 1 回の通信)。自分の書類には鍵が要る**(README に明記)。
- 出所: EDINET の公開の開示書類(書類 ID S100Z4Q1、提出者コード E36539 ＤＮホールディングス株式会社、提出日 2026-09-30)。同梱は人間の承認(2026-10-20。封の追記)。
- 注入は『最小の桁 1 字』と『±1 最小単位』の 2 型だけ(false_pass の型)。T2 単位・T3 不在・T5 偶然一致・T6 前期・T7 丸めは儀式に入れていない(別の封の数)。
- 分母 241 は『素の書類で GROUNDED だった数の site』で、書類の claim 412 全体ではない。注入の対象にならなかった site は 63(304 − 241。うち土台の不一致 8)。通した 17 / 241 = 7.1% は、その 241 に 2 型を 1 回ずつ当てた率。
- ラベル 2 file が無い機械では儀式は案内を出して止まる(rc=2)。ラベルの版が書類の `linkbaseRef` と違う書類は、その版を取り直す(`TAXONOMY_LABELS_README.md`)。
- 通した 17 は『丸めの帯』と『退化値』に分かれて見えるが、それが欠陥でないかは買い手が決める。
- 所要秒は記録を採った機械(python 3.9.6)の値。買い手の機械では変わる。
- **HUMAN の残り 1 点**: `adapters/xbrl/verify_document.py` の docstring『`--profile` を省くと P20』が既定 P21 と食い違う。engine の file なので触っていない(承認待ち)。

## 4. 変異(門が壊れた標本で赤くなること)

2 種類の変異を使った。毎回走る変異(`MutationTest`。壊した標本に本物と同じ検査関数を当てる)と、実物を一時的に壊して門を走らせた手作業の変異(各回、バイトを戻して sha256 の一致を確かめた。`measure/false_pass_2026-10-14.py` も戻して差 0)。A-1〜A-4・A-9・A-10 は subprocess 版の門(`AUDIT_CORE_RITUAL=1`)で測り直した。

| # | 壊したもの | 赤くなった門 |
|---|---|---|
| M-1 | 記録の `後の字` 1 字・`元の字` 1 字・入力の sha256 1 字(毎回) | `check_record`(`test_m1`) |
| M-2 | 記録の `止めた` の字 1 字を README と突き合わせ(毎回) | `check_readme`(`test_m1b`) |
| M-3 | README.md・README.en.md の数 1 字(`224 → 225`・`92.9 → 92.8`・`7.1 → 7.2`、毎回) | `check_readme`(`test_m2`) |
| M-4 | 通した 17 を 16 に(件・字・行の結果を 1 本書き換え。毎回) | `check_record`(`test_m3`) |
| M-5 | zip の 1 byte・末尾 1 byte・記録の sha256 の先頭を 1 字(毎回) | `check_input_bytes`・`check_record`(`test_m4`) |
| M-6 | 分け方の書き換え(退化値を帯の中に・帯の中の行の値を 10 倍)と、独立な分け方の関数が 5 種(帯の中・帯の外・退化値・△つき・桁違い)を言い分けること(毎回) | `check_record`・`indep_class`(`test_m5`・`test_m6`) |
| A-1 | `false_pass` の V2 を `+1` から `+2` に(実物。`AUDIT_CORE_RITUAL=1`) | 走らせ直しの一致(`RerunHeavyTest.test_4`)・R の判定表(`test_8`。R-8 が赤) |
| A-2 | script の帯の幅 `step × (1 + 1e-9)` を `step × 0.5` に(実物。同上) | `RerunHeavyTest.test_4` |
| A-3 | script の画面で `止めた` を `通した` より先に(実物。同上) | `InputTest.test_3`(script の字の順)・`RerunHeavyTest.test_4`(画面) |
| A-4 | script の profile を P20 に(実物。同上) | `RerunHeavyTest.test_4` |
| A-5 | script が `os.path.expanduser('~')` を使う(実物) | 通信・`~/.cache` を名指さない(`RerunTest.test_5`) |
| A-6 | script が `urllib.request` を import(実物) | 同上(`test_5`) |
| A-7 | README.md の `止めた 224 / 241` を `225 / 241` に(実物) | README の節(`test_7`)・R の判定表(`test_8`) |
| A-8 | 記録の `後の字 67.6%` を 1 か所だけ `67.7%` に(実物) | 記録の内部整合(`test_2`)・通した の表(`test_10`) |
| A-8b | 同じ字を 2 か所とも `67.7%` に(実物) | 同上 + `test_m1` |
| A-9 | script の通した の一覧を先頭 16 件に切る(実物。`AUDIT_CORE_RITUAL=1`) | `RerunHeavyTest.test_4` |
| A-10 | script の zip の sha256 の字を 1 字変える(実物。同上) | `RerunHeavyTest.test_4`・`test_6`・`LabelTest.test_13`・`test_14`(rc が 2 にならない) |
| A-11 | 同梱 zip の 1 byte(実物) | 入力の留め(`InputTest.test_1`)・封の門 `test_7`・`test_8` |

退化値の変異が 1 回黙った: M-5 の sha256 の変異を先頭を `0` に置き換えて作ったところ、先頭がもともと `0` で**恒等になり赤にならなかった**(`f` に直して赤を確かめた)。

**ラベル依存の直しの後の変異**(`AUDIT_CORE_RITUAL=1` で走らせた門。予測を走らせる前に固定し、実測と並べた。実物を一時的に壊し、byte を戻して sha256 の一致を確かめた):

| # | 壊したもの | 予測(赤) | 実測(赤) |
|---|---|---|---|
| V-1 | 走らせ直しの門のラベル dir を空の dir に(ラベル無しで本当に赤くなるか) | `RerunHeavyTest.test_4`・`test_6`(rc=2) | `test_4`・`test_6`(予測どおり) |
| V-2 | README.md の手順 0 の段落を消す | `ReadmeTest.test_7`・`PredictionTest.test_8`・`MutationTest.test_m0` | 3 本 + `MutationTest.test_m7`(予測漏れ。m7 は元の段落を切る変異で、既に無いと赤) |
| V-3 | README.md の N125・N199 の項目を消す | V-2 と同じ 3 本 | V-2 と同じ 4 本(同上) |
| V-4 | 封の追記から『選択肢 2』を消す | 封の門 `SealTest.test_10` | `test_10` のみ(予測どおり) |
| V-5 | script のラベル確認の呼び出しを外す | `LabelTest.test_13` | `test_13`・`test_14`(予測漏れ。sha256 違いも素通りする) |
| V-6 | script の sha256 比較を無効にする | `LabelTest.test_14` | `test_14` のみ(予測どおり) |
| V-7 | 門が `EDINET_TAXONOMY_DIR` を渡さない(`HOME` は空) | `RerunHeavyTest.test_4`・`test_6`(実 HOME の `~/.cache` を黙って読まない証拠) | `test_4`・`test_6` + `LabelTest.test_13`・`test_14`(予測漏れ。ラベル dir の指定が効かなくなる) |
| V-8 | 案内の字から README の名前を消す | `LabelTest.test_13` | `test_13` のみ(予測どおり) |

予測漏れは全部「予測より多く赤くなった」側で、予測した本が赤くならなかった変異は 0。

**再監査後の追加の変異**(予測を先に固定。`AUDIT_CORE_RITUAL=1` で走らせた門。script は戻して sha256 `67cf513632ae24f9…` のまま):

| # | 壊したもの | 予測(赤) | 実測(赤) |
|---|---|---|---|
| W-1 | script の案内の URL を 1 字変える(`jppfs` → `jppfz`) | `LabelTest.test_16` | `test_16` + `MutationTest.test_m9`(予測漏れ。m9 は本物の script にも同じ検査を当てる) |
| W-2 | script のラベル確認を 1 file 目だけに退化 | `LabelTest.test_17`(片方だけの dir) | `test_17` のみ(予測どおり) |
| W-3 | `AUDIT_CORE_RITUAL=1` かつ `EDINET_TAXONOMY_DIR` を空の dir に(環境) | `RerunHeavyTest` の 3 本が skip でなく fail | 3 本が fail(`test_4`・`test_6`・`test_6b`)、`test_17` は skip(予測どおり) |
| W-4 | `AUDIT_CORE_RITUAL` なしで `EDINET_TAXONOMY_DIR` を空の dir に(環境) | 重い門は skip・全体緑 | 25 passed, 4 skipped(予測どおり) |

**走らせ直しの門の限界**: script が記録を読んで書き出すだけに退化しても、走らせ直しの門は緑のままである。「走らせ直し」が縛るのは出力の一致まで(注入と再検証が本当に走ったことは、A-1・A-2 のように道具を壊して出力が変わることで確かめた)。

## 5. 再現

```
cd audit-core
python3 measure/ritual_2026-10-20.py --out <出力先>
python3 -m pytest -q tests/measure/test_xbrl_ritual_result.py                       # 既定: 記録・README・予測・変異・ラベル無しの案内
AUDIT_CORE_RITUAL=1 python3 -m pytest -q tests/measure/test_xbrl_ritual_result.py   # 走らせ直し(20 秒超。ラベル 2 file が要る)
```

- 環境: 鍵の名前の設定は `ANTHROPIC_BASE_URL` の名前だけ(値は読まない・記録しない。儀式は使わない)。ラベル 2 file の sha256 は起動時に照合し、記録に残した。HEAD 4fcde39(記録を採ったとき。作業木は未コミットの追加あり)。
- engine の留め: core/ と adapters/ の 36 file(`__pycache__` を除く)の束ねた sha256 `5b5f030071188864092d0fba8f655ee1f413c08ebbb1769190511bd8720ccbee`。
- 入力: `fixtures/xbrl/ai_prose_instance_2026-10-09.zip`(git に追跡済み)、sha256 `03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799`、580,260 bytes。
- 門が縛るもの: 入力の sha256・bytes(字で留める)、記録の行 241 本からの数え直し(通した・止めた・分け方・型別・参照先が動いた)、同梱 zip からの走らせ直しと記録の一致(所要秒と実行環境を除く。subprocess・`HOME` を空に・ラベルは `EDINET_TAXONOMY_DIR` で名指し・接続を潰して。`AUDIT_CORE_RITUAL=1` のとき)、ラベル無し・sha256 違いで案内を出して rc=2 で止まること、script が通信の module と `~/.cache` を名指さないこと、README の節の全文、予測 R-1〜R-8 の判定、通した 17 の表、文書の `a / b = x.x%` の分数の全部。
- **縛っていないもの**: 文書の本文の文章、§2 の読み(人の読み)、`tests/measure` 全体の所要、他の席の機械の秒(字で留めた値は R-7 の判定にだけ使う)、§4 の手作業の変異の結果。
