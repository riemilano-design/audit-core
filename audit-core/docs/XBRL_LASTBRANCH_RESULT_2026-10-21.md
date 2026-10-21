# 最後の枝の名指しは証拠があるときだけ「違う」と言う P25 ― 段 1 の結果(2026-10-21)

封: `docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md`(commit `80ca08d`。**本文と予測は一字も直していない**。外れは外れとして残す)。
記録: `fixtures/xbrl/lastbranch_2026-10-21.json`(`measure/xbrl_lastbranch_2026-10-21.py --stage all --readings … --mutations … --run-tests` の出力。手で走らせた二つの入力 ― 人の読みと engine の変異の表 ― の sha256 は記録の入力の欄に残してある)。
門: `tests/measure/test_xbrl_lastbranch_result.py`(表と数のある文を記録から作った字で縛り、それ以外の散文に算用数字が在れば赤にする。散文は漢数字で書く)。
**0 USD・通信なし。engine の直しは人間の事前承認(2026-10-21)の範囲。既定は P22 のまま(段 1)。**

**予測 機械判定 当たり 8 / 外れ 0 / 測れない 0**(L-1〜L-8。L-9 は段 2 なので判定しない)。
engine の直し: `adapters/xbrl/vocabulary.py` 挿入 7・削除 0、`adapters/xbrl/recipes.py` 挿入 72・削除 0、`adapters/xbrl/registry_setup.py` 挿入 2・削除 0、`adapters/xbrl/comparators.py` 挿入 0・削除 0、`core/` 0 行。

## 1. 予測と実測

| # | 封の予測 | 封の外れ方 | 実測 | 判定 |
|---|---|---|---|---|
| **L-1** | 67 書類の無改変で VALUE_MISMATCH **620〜632**(P24 1,203)。動く行は全部 VM → POINTER_NOT_FOUND `no_same_value` で **570〜584**、GROUNDED と UNVERIFIABLE の数は P24 と同じ | 幅の外 / 他の向きが 1 行以上 | 67 書類(実数 67)・claim 7,799: VALUE_MISMATCH P24 1,203 → P25 626、動いた 577 行(VM → PNF no_same_value 577・それ以外の向き 0)、GROUNDED 4,382 → 4,382・UNVERIFIABLE 1,397 → 1,397 | **当たり** |
| **L-2** | 最後の枝で VM に残る行 **4〜8**、全部読んで「文が本当に違う」**0〜1** | 幅の外 | 最後の枝に入って証拠があり VALUE_MISMATCH に残る行 6(証拠 {"digit_within_k": 2, "same_element": 2, "scale_10^-2": 2})。読み: 正しい文 6・文が本当に違う 0・分からない 0・未読 0 | **当たり** |
| **L-3** | **試作で読んでいない VM → PNF の行を全部読み、「文が本当に違う」が読んだ行の 2% 以下**。読んでいない行 = 段 1 で動いた行 − 試作で読んだ集合(試作 v1 の記録 `scratchpad/lastbranch/proto.json` の読み 228 行と v3 の 13 行の (doc, id)。実装席はこの (doc, id) の一覧を記録に写す)。試作では 337 行に当たる | 2% 超 | 試作で読んでいない行(動いた 577 - 試作で読んだ集合のうち動いた 240)337 行の読み: 正しい文 335・文が本当に違う 1・分からない 1・未読 0(違う 1 / 337 = 0.3%) | **当たり** |
| **L-4** | 穴 B の 485 件を P25 で通す **0**、止め(P24 で VALUE_MISMATCH の 483)のうち → 要確認 **0〜4** | 通す 1 以上 / 5 以上 | 通した 0 / 485・P24 の止め 483 のうち要確認に移る 2(対照 P24 の通した 0) | **当たり** |
| **L-5** | 儀式を P25 で: 通した **2〜3**、注入の止め → 要確認 **26〜34**(素の書類の VM の動きは含めない) | 幅の外 | 通した 2 / 247(N069・N096)・注入の止め(P24 の VALUE_MISMATCH)が要確認に移った 30(型 {"V1": 19, "V2": 11})。対照 P24 の通した 2 / 247 | **当たり** |
| **L-6** | 段 2 の材料: 注入の GROUNDED **0 / 64**、注入の止め → 要確認 **0〜2** | 幅の外 | 注入の GROUNDED 0 / 64・P24 の止め 27 のうち要確認に移る 1(型 {"T2_UNIT": 1})・Core 自身が動いた行 8 | **当たり** |
| **L-7** | 67 書類で P24 → P25 に動いた全行への注入(1 回に 1 件、末尾の桁 ±3・10 倍、試作と同じ作り方)で P25 が GROUNDED にする **0** 回 | 1 回以上 | 対象 577 行・注入 1154 回(有効 1118)で P25 が GROUNDED 0・VALUE_MISMATCH 9・POINTER_NOT_FOUND 1108(対照 P24 は GROUNDED 0)。P24 の VALUE_MISMATCH が P25 で要確認に移った有効な注入 1108 | **当たり** |
| **L-8** | engine の差分 `recipes.py` **+60〜+90 / −0**、`vocabulary.py` **≤ 10 行**、`registry_setup.py` **≤ 5 行**(行数は挿入 + 削除)、`comparators.py`・`core/` 0 行。既存試験の赤は登録の一覧・旗の形・sha の留め・diff の門だけ(数 / state の門 0、人間の決定の字の門 0) | 超える / `recipes.py` の削除 1 行以上 / 種類の外の赤 | vocabulary.py 挿入 7・削除 0、recipes.py 挿入 72・削除 0、registry_setup.py 挿入 2・削除 0、comparators.py 0/0、core/ 0 行。既存試験の赤(直す前)42 本、種類 {"diff の門": 5, "sha の留め": 19, "旗の形": 13, "登録の一覧": 5} | **当たり** |
| **L-9** | 段 2(既定 P22 → P25 をまとめて 1 回)は人間に 3 つの率(誤りを通す率・無改変で「違う」と言う率・結べない率)と、「違う」が「要確認」に移る注入の数を見せてから | ― | 段 2(既定 P22 → P25 を P23・P24 とまとめて 1 回)は人間に 3 つの率と「違う」が「要確認」に移る注入の数を見せてから。この実行では何も変えていない(DEFAULT_PROFILE = P22) | **判定しない(段 2)** |

**L-1・L-2・L-4 から L-7 は封 §0 の試作 `v3` の再現で、外れるなら実装が試作と違うことを示す予測である。** 実装は試作の差分(`git apply`)を入れ、封 §1 の字と一行ずつ照らした(第十二節に食い違い)。動いた行の全部が `VALUE_MISMATCH` から `POINTER_NOT_FOUND`(`no_same_value`)へ動き、`GROUNDED` と `UNVERIFIABLE` は一行も動かなかった(第二節)。

**本当に外れうる L-3(試作で読んでいない行)は、全部読んで当たった。** ただしその読みは実装席の人(エージェント)の読みで、**門で縛れない**(縛るのは行と読みの一対一の対応と、数と、判定の算術だけ)。人間が読み直す余地を第四節に残してある。**新しい標本は手元に無い**(手元の cache の六十七の外は全部 `jpsps` で、P24 の W-7 で claim が零と確かめた)ので、六十七書類で「違う」が零でも新しい標本で零とは言えない。

## 2. L-1 無改変の六十七書類

67 書類(claim 7,799)の無改変で、P24 から P25 に動いた行は 577(全部 VALUE_MISMATCH から POINTER_NOT_FOUND の `no_same_value`。それ以外の向き 0)。VALUE_MISMATCH は P24 が 1,203、P25 が 626(差 -577)。GROUNDED は 4,382 のまま、UNVERIFIABLE は 1,397 のまま。

| 項目 | 件数 |
|---|---:|
| 書類 | 67 |
| claim の総数 | 7,799 |
| 動いた行(全 state) | 577 |
| VALUE_MISMATCH → POINTER_NOT_FOUND(`no_same_value`) | 577 |
| それ以外の向き | 0 |
| 最後の枝に入った行(P25) | 583 |
| うち 名指しに残った行(証拠あり) | 6 |
| P25 の動いた行で pointer の在る行 | 0 |

| 無改変 67 書類 | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND |
|---|---:|---:|---:|---:|
| P24(対照) | 4,382 | 1,203 | 1,397 | 817 |
| **P25** | **4,382** | **626** | **1,397** | **1,394** |

遷移の全部(P24 の state から P25 の state):

| 向き(P24 の state(reason) → P25 の state(reason)) | 行 |
|---|---:|
| VALUE_MISMATCH(None) → POINTER_NOT_FOUND(no_same_value) | 577 |

最後の枝に入った行の証拠別(P25 の旗が真のとき、証拠の判定まで来た行):

| 最後の枝に入った行の証拠 | 行 |
|---|---:|
| 証拠なし(名指さず要確認へ) | 577 |
| digit_within_k | 2 |
| same_element | 2 |
| scale_10^-2 | 2 |

動いた行は全部、`no_same_value` の Recipe に `provenance["no_same_value"]` が付き(名指した要素・期・値)、pointer は付かない:

| `no_same_value` の Recipe | 件数 |
|---|---:|
| no_same_value の Recipe | 577 |
| provenance に名指しあり | 577 |

## 3. L-2 証拠があって名指しに残った行

最後の枝に入った行 583 のうち、証拠があって名指しに残った行は 6。全部読んで、正しい文 6・文が本当に違う 0・分からない 0(未読 0)。

| doc | id | 証拠 | 名指した fact | 読み | 根拠 |
|---|---|---|---|---|---|
| S100YYK8 | N041 | scale_10^-2 | xbrl:jppfs_cor:LongTermLoansPayable@CurrentYearInstant | 正しい文 | 文の数は社債の減少(20,000千円)で、名指した fact は長期借入金の残高。社債の fact(BondsPayable 60,000 → 40,000 千円の差 20,000、実測)に同じ値がある。(iii) n = -2 は偶然の近さ(末尾の 0 が 4 つで精度が粗くなり帯が広がった) |
| S100YYK8 | N058 | same_element:Prior1YearDuration | xbrl:jppfs_cor:NetCashProvidedByUsedInFinancingActivities@CurrentYearDuration | 正しい文 | 文の数は前期の財務活動による資金の減少(623,129千円、『前期同期』は誤字)で、同じ要素の Prior1Year の fact に合う。名指した fact は当期の 758,178千円。文は前期の数を正しく書いている |
| S100YZ7E | N050 | digit_within_k | xbrl:jpcrp_cor:DividendPaidPerShareSummaryOfBusinessResults@CurrentYearDuration_NonConsolidatedMember | 正しい文 | 文の数はその他の収入等(1百万円)で、名指した fact は 1 株当たり配当(400円、JPY の fact)。1 単位以内は偶然の近さ((ii))。文と名指しの参照先が違う |
| S100YZ7E | N060 | digit_within_k | xbrl:jppfs_cor:PurchaseOfIntangibleAssetsInvCF@CurrentYearDuration_NonConsolidatedMember | 正しい文 | 文の数は有形・無形固定資産の取得による支出(112百万円)で、名指した fact は無形固定資産だけの 111.15百万円。有形 1.233 + 無形 111.15 = 112.38百万円で文と一致(実測)。(ii) は偶然の近さ |
| S100Z3JY | N084 | same_element:Prior1YearDuration | xbrl:jppfs_cor:NetCashProvidedByUsedInFinancingActivities@CurrentYearDuration | 正しい文 | 文の数は前連結会計年度の財務活動に使用した資金(0百万円)で、同じ要素の Prior1Year の fact に合う。名指した fact は当期の 139.8百万円の使用。文は前期の数を正しく書いている |
| S100Z42X | N020 | scale_10^-2 | xbrl:jppfs_cor:NetSales@CurrentYearDuration_jpcrp030000-asr_E02100-000EntrustedDevelopmentReportableSegmentMember | 正しい文 | 文の数は前年同期のセグメント損失(1百万円)で、名指した fact は当期のセグメントの売上高 168百万円。前期のセグメント損益(△1.712百万円、百万円未満切り捨てで 1)に合う。(iii) n = -2 は偶然の近さ |

三つの証拠((i) 同じ要素の別の期・(ii) 差が二単位以内・(iii) 桁の取り違え)が一つずつ二行ずつ当たっている。(ii) の二行は読みが「正しい文」(文の数と名指した fact が別の項目で、差が偶然に二単位以内に入った)。偶然の近さは封 §3 の限界に書いた型である。

## 4. L-3 試作で読んでいない行(本当に外れうる予測)

| 項目 | 件数 |
|---|---:|
| 段 1 で動いた行 | 577 |
| 試作で読んだ集合 (doc, id) | 241 |
| うち 段 1 で動いた行 | 240 |
| 試作で読んでいない行(動いた行 − 試作で読んだ集合。全部読んだ) | 337 |

試作で読んでいない行(動いた行 577 から試作で読んだ集合のうち動いた 240 を引いた 337 行)を全部読んで、正しい文 335・文が本当に違う 1・分からない 1(未読 0)。文が本当に違う 1 / 337 = 0.3%。

読みの語は「正しい文」(名指した fact が文の参照先でない、または参照先と文が帯の中で合い、`VALUE_MISMATCH` が偽だった)・「文が本当に違う」(名指した fact が文の参照先で、値が帯の外。`VALUE_MISMATCH` が正しかった = 弱めた代価)・「分からない」の三つ。「分からない」は「分からない」のまま数えた。行ごとの根拠は記録の `L3.未読の行`(読みと根拠が行に付いている)にある。

| 行の型(読むための材料の分け方) | 読み | 行 |
|---|---|---:|
| A 同じ要素の当期 - 前期と 2 単位以内 | 正しい文 | 56 |
| B 別の要素に同じ値 | 正しい文 | 166 |
| C 名指す要素に前期なし | 正しい文 | 33 |
| D 同じ値なし | 分からない | 1 |
| D 同じ値なし | 文が本当に違う | 1 |
| D 同じ値なし | 正しい文 | 80 |

「文が本当に違う」と「分からない」の全部(一件ずつ):

| doc | id | 読み | 文 | 名指した fact | 名指した値 | 根拠 |
|---|---|---|---|---|---|---|
| S100YYN7 | N008 | 分からない | また、固定資産売却などによる特別利益87億8百万円、及び中東情勢の影響を受けたアルミ地金高騰に起因する建材事業に係る固定資産の減損損失162億19百万円などを特別損失に計上したことにより、親会社株主に帰属する当期純損失は134億98百万円(前連結会計年度は23億36百万円の親会社株主に帰属する当期純損失)となりました。 | xbrl:jppfs_cor:ImpairmentLossEL@CurrentYearDuration_jpcrp030000-asr_E26831-000BuildingMaterialsReportableSegmentsMember | 16428000000.0 | 文の数は建材事業に係る固定資産の減損損失 162億19百万円。名指した fact は建材事業(セグメント)の減損損失 164億28百万円(文と 209 百万円差)。文は『アルミ地金高騰に起因する』減損だけを指す内数とも読め、セグメントの減損損失全体を指すなら文が違う。決められない |
| S100YZ7E | N071 | 文が本当に違う | また、当事業年度末現在において、有価証券及び投資有価証券の残高は937億円となっております。 | xbrl:jppfs_cor:InvestmentSecurities@CurrentYearInstant_NonConsolidatedMember | 86127523000.0 | 文の数は『当事業年度末現在の有価証券及び投資有価証券の残高 937億円』。当期末の有価証券 5,591百万円 + 投資有価証券 86,128百万円 = 917億円(実測)で、937億円は前期末の 93,526 + 240 = 93,766百万円に近い。文が当期の数と食い違う(前期末の数を当期末と書いたか)。名指した fact は投資有価証券だけだが、VALUE_MISMATCH の判定は結果として正しかった |

- 「文が本当に違う」の一件(`S100YZ7E` の `N071`): 文は「有価証券及び投資有価証券の残高」を当事業年度末と書くが、当期末の実測の合計と合わず、文の数は前期末の数に近い。つまり文が当期の数と食い違っていて、`VALUE_MISMATCH` が結果として正しかった。名指した fact は投資有価証券だけで、証拠(同じ要素の別の期・二単位以内・桁の取り違え)のどれにも当たらないため、P25 は「違う」を言わず「要確認」にした。**これが封 §3 に書いた代価の実物である**(誤りを通した、ではなく、「違う」が「要確認」に弱まった)。
- 「分からない」の一件(`S100YYN7` の `N008`): 文の数は建材事業に係る固定資産の減損損失の内数にも、セグメントの減損損失全体にも読め、名指したのは後者。前者なら文が正しく、後者なら文が違う。決められなかった。

**読みは門で縛れない。** 記録は、読みを行に写し、読みの語が三つの語のどれかであること、根拠が空でないこと、行の集合が「動いた行 − 試作で読んだ集合」と一致することだけを門が縛る。読みが正しいかは、人間が記録の行(文・名指した fact・根拠)を読んで確かめる。

## 5. L-4 穴 B(前期の値への置き換え)

穴 B の注入 485 件を P25 で再検証すると、通した 0 / 485 = 0.0%・止めた 481 / 485 = 99.2%(P24 は通した 0 / 485 = 0.0%・止めた 483 / 485 = 99.6%)。P24 の止め 483 のうち要確認に移った行は 2。

| 穴 B の注入 485 件 | 通した | 止めた | その他 |
|---|---:|---:|---:|
| P24(対照) | 0 | 483 | 2 |
| **P25** | **0** | **481** | **4** |
| P24 の止めのうち要確認に移る | | | 2 |

要確認に移った二行:

| 書類 | id | 元の字 | 後の字 | 文脈 |
|---|---|---|---|---|
| S100YYQX | N008 | 4,384,403千円 | 3,389,337千円 | 当連結会計年度末における負債合計は4,384,403千円となり、前連結会計年度末に比べ995,065千円増加いたしま |
| S100Z4LC | N071 | 81,102千円 | 1,935千円 | 9,561千円、給与手当84,555千円及び貸倒引当金繰入額81,102千円であります。 |

## 6. L-5 儀式

儀式を P25 で回すと、通した 2 / 247 = 0.8%・止めた 215 / 247 = 87.0%・要確認 30 / 247 = 12.1%(P24 は通した 2 / 247 = 0.8%・止めた 245 / 247 = 99.2%)。通した id: N069・N096。注入の止めが要確認に移った行は 30(素の書類の VALUE_MISMATCH の動きは含めない)。

| 儀式 | 注入の行 | 通した | 止めた | 要確認 |
|---|---:|---:|---:|---:|
| P24(対照) | 247 | 2 | 245 | 0 |
| **P25** | **247** | **2** | **215** | **30** |
| 素の書類 GROUNDED(P24 → P25) | 340 → 340 | | | |
| 注入の止めが要確認に移った(型) | 30(V1 19・V2 11) | | | |

P25 でも通した行の中身(P24 と同じ二行。丸めの帯の中と、字は変わるが値が変わらない退化値で、誤りを通したのではない):

| id | 分類 | 値の差 | 1 最小単位 | 文脈 |
|---|---|---|---|---|
| N069 | 丸めの帯の中(±1 最小単位) | 0.10000000000000009 | 0.1 | 売上高営業利益率は前期の7.3%から3.8%へと3.5ポイント低 |
| N096 | 退化値(字は変わるが値が変わらない) | 0.0 | None | で、内訳は関係会社株式売却損6百万円および減損損失0百万円です。 |

## 7. L-6 段 2 の材料

段 2 の材料 192 行(注入 64)の Core 自身は、注入で P25 が GROUNDED にした 0・P24 の止め 27 のうち要確認に移った 1。P24 から P25 で動いた行は 8。

| 段 2 の材料 192 行の Core 自身 | 件数 |
|---|---:|
| 行 | 192 |
| 注入 | 64 |
| P24 → P25 で動いた行 | 8 |
| 注入で Core 自身 P24 が GROUNDED | 0 |
| 注入で Core 自身 P25 が GROUNDED | 0 |
| 注入の P24 の止め(VALUE_MISMATCH) | 27 |
| うち 要確認に移る | 1 |
| 無改変で VALUE_MISMATCH(P24 → P25) | 15 → 8 |

## 8. L-7 動いた行への注入

動いた 577 行に注入 1154 回(作れなかった 0・有効 1118・有効でない 36)。P25 が GROUNDED にした 0 回(P24 の対照も 0 回)。有効な注入のうち VALUE_MISMATCH が要確認に移ったのは 1108、VALUE_MISMATCH のまま 9、UNVERIFIABLE 1。

| 変え方・結果(有効な注入) | P25 | P24(対照) |
|---|---:|---:|
| 10 倍:POINTER_NOT_FOUND | 553 | 0 |
| 10 倍:UNVERIFIABLE | 1 | 1 |
| 10 倍:VALUE_MISMATCH | 5 | 558 |
| 末尾の桁 ±3:POINTER_NOT_FOUND | 555 | 0 |
| 末尾の桁 ±3:VALUE_MISMATCH | 4 | 559 |

注入しても P25 が要確認にならなかった有効な注入の全部(「違う」のまま残った行と、P24 の枠の取り直しで UNVERIFIABLE になった行):

| doc | id | 変え方 | 元の字 → 後の字 | P25 の state | reason |
|---|---|---|---|---|---|
| S100YWGX | N053 | 10 倍 | 1,200百万円 → 12,000百万円 | VALUE_MISMATCH | value differs(segment/other period?) |
| S100YYRV | N062 | 10 倍 | 100,000千円 → 1,000,000千円 | VALUE_MISMATCH | value differs(segment/other period?) |
| S100Z35K | N081 | 10 倍 | 20,000百万円 → 200,000百万円 | VALUE_MISMATCH | value differs(segment/other period?) |
| S100Z3IZ | N010 | 末尾の桁 ±3 | 5億80百万円 → 5億83百万円 | VALUE_MISMATCH | value differs(segment/other period?) |
| S100Z3LJ | N029 | 末尾の桁 ±3 | 19百万円 → 16百万円 | VALUE_MISMATCH | value differs(segment/other period?) |
| S100Z3V1 | N022 | 末尾の桁 ±3 | 40億62百万円 → 40億65百万円 | VALUE_MISMATCH | value differs(segment/other period?) |
| S100Z40H | N039 | 10 倍 | 58,110百万円 → 581,100百万円 | VALUE_MISMATCH | value differs(segment/other period?) |
| S100Z42X | N019 | 10 倍 | 11百万円 → 110百万円 | UNVERIFIABLE | other_frame(CurrentYearDuration_jpcrp030000-asr_E02100-000EntrustedManufacturingReportableSegmentMember) |
| S100Z42X | N027 | 末尾の桁 ±3 | 19百万円 → 16百万円 | VALUE_MISMATCH | value differs(segment/other period?) |
| S100Z6XO | N098 | 10 倍 | 4,000億円 → 40,000億円 | VALUE_MISMATCH | value differs(segment/other period?) |

注入は動いた行の文の数を一回に一件だけ、末尾の桁を三つ動かす・十倍にする、の二型で、P24 と P25 の両方で再検証した。**P25 が GROUNDED にした注入は零**(P24 の対照も零)。ほとんどの注入では P24 が言っていた「違う」が P25 で「要確認」に弱まった(これも封 §3 の代価で、段 2 に人間へ見せる数である)。

## 9. 段 2 に人間へ見せる数(L-9。判定しない)

段 2 に人間へ見せる数(この実行では何も変えず、判定もしない): 無改変 67 書類・claim 7,799 のうち「違う」(VALUE_MISMATCH)は P24 1203 / 7799 = 15.4% → P25 626 / 7799 = 8.0%、結べない(POINTER_NOT_FOUND)は P24 817 / 7799 = 10.5% → P25 1394 / 7799 = 17.9%。誤りを通す数は穴 B 0 / 485 = 0.0%・儀式 2 / 247 = 0.8%・段 2 の材料の注入 0 / 64・動いた行への注入 0 / 1154。「違う」が「要確認」に移った注入の数は穴 B 2・儀式 30・段 2 の材料 1・動いた行への注入(有効)1108。

段 2(既定 P22 から P25 へ。P23 と P24 を含めてまとめて一回)は、人間が上の数を見てから決める。この実行では何も変えていない(`DEFAULT_PROFILE` は `P22` のまま)。

## 10. L-8 engine の差分と既存試験

| file | 挿入 | 削除 |
|---|---:|---:|
| `adapters/xbrl/vocabulary.py` | 7 | 0 |
| `adapters/xbrl/comparators.py` | 0 | 0 |
| `adapters/xbrl/recipes.py` | 72 | 0 |
| `adapters/xbrl/registry_setup.py` | 2 | 0 |
| `core/` | 0 | |

既存試験の赤(直す前): 42 本。覆いの門の赤(新しい試験 file を足したため): 3 本。直した後の既存試験: python3 -m pytest -q tests/adapters/xbrl → 992 passed, 1 skipped in 1123.14s (0:18:43)。

直す前に赤になった既存試験(種類は封の字の中だけ。数 / state の門と人間の決定の字の門は零):

| 試験 | 種類 | 直し |
|---|---|---|
| tests/adapters/xbrl/test_mutations.py::MutationTwoWayTest::test_all_mutations_match_their_prediction | 登録の一覧 | 変異の部分木に写された test_vocabulary の登録の一覧に P25 が無く、変異が予測と逆に赤になった。test_vocabulary の一覧 2 本を直して解消(この試験自体は直していない) |
| tests/adapters/xbrl/test_p17.py::PctToleranceTest::test_p18_is_p17_plus_the_tolerance_flag | 旗の形 | 率の旗 pct_tolerance_from_decimals を持つ profile の一覧に P25 を足した(P25 は P24 から作る) |
| tests/adapters/xbrl/test_p20.py::ProfileShapeTest::test_every_other_profile_keeps_the_flag_off | 旗の形 | 除外の一覧に P25 を足した(nonconsolidated_fallback を引き継ぐ) |
| tests/adapters/xbrl/test_recipes_p21.py::FlagShapeTest::test_only_p21_has_the_flag_on | 旗の形 | last_branch_cues を持つ profile の一覧を P21〜P24 から P21〜P25 に |
| tests/adapters/xbrl/test_recipes_p22.py::FlagShapeTest::test_only_p22_has_the_flag_on | 旗の形 | period_bind を持つ profile の一覧を P22〜P24 から P22〜P25 に |
| tests/adapters/xbrl/test_recipes_p22.py::WithoutCueTest::test_every_profile_before_p22_keeps_grounding_the_prior_fact | 旗の形 | 除外を P22〜P24 から P22〜P25 に |
| tests/adapters/xbrl/test_recipes_p23.py::FlagShapeTest::test_only_p23_has_the_new_flag_on | 旗の形 | truncate_abs_band を持つ profile の一覧を P23・P24 から P23〜P25 に |
| tests/adapters/xbrl/test_recipes_p23.py::P22UnchangedTest::test_every_profile_but_p23_keeps_the_signed_band_under_truncate | 旗の形 | 除外を P19・P23・P24 から P19・P23〜P25 に |
| tests/adapters/xbrl/test_recipes_p24.py::FlagShapeTest::test_the_flags_are_false_by_default_and_for_every_other_profile | 旗の形 | P24 の旗 2 つが真の profile の一覧を P24 から P24・P25 に(P25 は P24 から作る) |
| tests/adapters/xbrl/test_registry_setup.py::RegisterAllTest::test_register_all_registration_counts_from_registry | 登録の一覧 | POINTER_NOT_FOUND の理由の数を 8 から 9、登録の総数を 31 から 32 に(no_same_value を足したため) |
| tests/adapters/xbrl/test_vocabulary.py::ProfileListPinsAreSelfCheckedTest::test_every_registry_pin_matches_the_registry | 登録の一覧 | この試験自体は直していない: 下の 2 本の一覧に P25 を足すと緑になる(登録表と字の一覧の食い違いを見つける守りが効いた) |
| tests/adapters/xbrl/test_vocabulary.py::P7ProfileTest::test_p7_in_profiles_registry | 登録の一覧 | PROFILES の一覧に P25 を足した |
| tests/adapters/xbrl/test_vocabulary.py::P12P13P14ProfileTest::test_profiles_registry_lists_every_profile | 登録の一覧 | PROFILES の一覧に P25 を足した |
| tests/measure/test_xbrl_a_core_vs_grep_seal.py::FrozenTest::test_9_tools_have_not_moved | sha の留め | ENGINE_LATER の vocabulary.py の遷移を P25 の段 1 の値に(測った時点の値は注記に残す) |
| tests/measure/test_xbrl_axis3_decision.py::Axis3Test::test_9_the_engine_was_not_touched | sha の留め | ENGINE_LATER の vocabulary.py の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_branch_a.py::PredictionTest::test_14_engine_files_are_untouched | sha の留め | ENGINE_LATER の recipes.py・vocabulary.py の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_cd_seal.py::FrozenToolsTest::test_12_engine_and_tools_have_not_moved | sha の留め | FROZEN_LATER の vocabulary.py の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_p20_result.py::DisciplineTest::test_11_engine_is_untouched | sha の留め | ENGINE_LATER の recipes.py・vocabulary.py の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_period_bind_result.py::RecordTest::test_16_frozen_bundle_last_generation_is_the_working_tree_and_declares_step_2 | sha の留め | fixtures/frozen_bundle_sha.py の FROZEN_BUNDLE_GENERATIONS に世代を 1 つ足した(門は P24 のとき直した『最新から後の封の宣言を飛ばして読む』形のまま) |
| tests/measure/test_xbrl_period_bind_result.py::RecordTest::test_8_engine_is_the_one_measured_or_a_declared_transition | sha の留め | ENGINE_LATER の recipes.py・vocabulary.py の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_period_bind_seal.py::EngineAtSealTest::test_12_engine_sha_is_the_one_at_the_seal_or_a_declared_transition | sha の留め | ENGINE_LATER の recipes.py・vocabulary.py の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_pnf_diag.py::DisciplineTest::test_7_engine_files_are_untouched | sha の留め | ENGINE_LATER の recipes.py・vocabulary.py の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_role_swap_result.py::DisciplineTest::test_11_engine_untouched | sha の留め | ENGINE_LATER の recipes.py の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_rounding_result.py::RecordTest::test_6_engine_is_the_one_measured_or_a_declared_transition | sha の留め | ENGINE_LATER の vocabulary.py・recipes.py の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_rounding_result.py::MutationTest::test_baseline_is_green | sha の留め | 上と同じ(基準線が engine_ok を呼ぶ) |
| tests/measure/test_xbrl_rounding_result.py::MutationTest::test_m16_a_wrong_engine_sha_is_red | sha の留め | 上と同じ(この変異は ENGINE_LATER を空にして確かめる形のままで、遷移の値が変わっただけ) |
| tests/measure/test_xbrl_rounding_seal.py::EngineAtSealTest::test_11_engine_sha_is_the_one_at_the_seal_or_a_declared_transition | sha の留め | ENGINE_LATER の vocabulary.py・recipes.py の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_vocab_result.py::RecordTest::test_6_engine_is_the_one_measured_or_a_declared_transition | sha の留め | ENGINE_LATER(空だった)に 3 file の遷移を P25 の段 1 の値で宣言 |
| tests/measure/test_xbrl_vocab_result.py::MutationTest::test_baseline_is_green | sha の留め | 上と同じ(基準線が engine_ok を呼ぶ) |
| tests/measure/test_xbrl_vocab_result.py::MutationTest::test_m16_a_wrong_engine_sha_is_red | sha の留め | 変異『測った時点の sha を壊すと赤』が、宣言された遷移の受け入れで赤にならなくなったので、この変異の中だけ ENGINE_LATER を空にして確かめる(変異の意図は不変。rounding_result と同じ直し) |
| tests/measure/test_xbrl_vocab_seal.py::EngineAtSealTest::test_13_engine_sha_is_the_one_at_the_seal_or_a_declared_transition | sha の留め | ENGINE_LATER の 3 file の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_lastbranch_seal.py::EngineAtSealTest::test_13_engine_sha_is_the_one_at_the_seal_or_a_declared_transition | sha の留め | ENGINE_LATER(空)に 3 file の遷移を宣言(docstring のとおり) |
| tests/measure/test_xbrl_point_prior_result.py::RecordTest::test_3_judgments_recomputed_equal_the_script_and_the_record | diff の門 | ENGINE_LATER の recipes.py・vocabulary.py・registry_setup.py の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_point_prior_result.py::DocTest::test_6_the_document_equals_what_the_record_says | diff の門 | 上と同じ |
| tests/measure/test_xbrl_point_prior_result.py::DocTest::test_7_seal_and_engine_are_untouched_since_the_seal_commit | diff の門 | 上と同じ |
| tests/measure/test_xbrl_point_prior_result.py::MutationTest::test_m0_the_genuine_samples_pass | diff の門 | 上と同じ |
| tests/measure/test_xbrl_ritual_result.py::PredictionTest::test_8_judgments_recomputed_equal_the_document_table | diff の門 | ENGINE_LATER の recipes.py・vocabulary.py・registry_setup.py の遷移を P25 の段 1 の値に |
| tests/measure/test_xbrl_period_bind_seal.py::EngineAtSealTest::test_13_default_is_p22_from_step_2_and_p22_is_registered_with_the_flag | 旗の形 | period_bind を持つ profile の一覧を P22〜P24 から P22〜P25 に |
| tests/measure/test_xbrl_rounding_seal.py::EngineAtSealTest::test_12_flags_exist_default_is_p22_and_p23_is_p22_plus_the_two_flags | 旗の形 | truncate_abs_band・pct_tolerance_from_decimals を持つ profile の一覧に P25 を足した |
| tests/measure/test_xbrl_vocab_seal.py::EngineAtSealTest::test_14_new_flags_p24_and_other_frame_exist_now_default_is_p22 | 旗の形 | 旗 vocab_2026_10_21・frame_rebind が真の profile の一覧を P24 から P24・P25 に |
| tests/measure/test_xbrl_vocab_seal.py::EngineAtSealTest::test_15_p23_flags_are_unchanged | 旗の形 | 最後の assert『truncate_abs_band が真なのは P23・P24 だけ』は P25 = P24 + 旗 1 つが引き継ぐので成り立たない。P23〜P25 に直した(封の門の食い違い。封の字は不変) |
| tests/measure/test_xbrl_lastbranch_seal.py::EngineAtSealTest::test_14_new_flag_p25_and_no_same_value_do_not_exist_yet | 旗の形 | docstring のとおり『まだ無い』を『在る(旗は Profile に在って既定は偽・真なのは P25 だけ・no_same_value は registry_setup.py に在る・core/ に無い)』に直した |

新しい試験 file を足したことで赤になった覆いの門(engine と無関係。覆いの記録を測り直して直した):

| 試験 | 直し |
|---|---|
| tests/measure/test_facts_for_buyers.py::AssetNumbersTest::test_22_record_is_the_live_disk_count | 覆いの記録を測り直して 1 冊の A-06〜A-09 を直す |
| tests/measure/test_suite_coverage.py::CountTest::test_1_recount_the_files_on_disk | 覆いの記録を測り直す(--write) |
| tests/measure/test_suite_coverage.py::RecordIsStableAndReadOnlyTest::test_37_the_default_run_does_not_write_the_record | 覆いの記録を測り直す(--write) |

人間の決定の字(案ア・§1b の止め・C2 `period_cue`・C-1g `_build_point_diff_claim`・P21 の最後の枝・P22 の `period_bind`・P23 の `_mag_trunc`・P24 の旗二つ)を探す既存の門は、一本も直さずに緑である。comparators.py は零行、`core/` は零行。

## 11. engine の変異(手で走らせた)

| # | 変異 | 予測 | 実測 |
|---|---|---|---|
| M1 | recipes.py: 最後の枝の旗のガード `getattr(profile, "last_branch_names_only_if_evidence", False) and` を外す(旗が偽の profile も証拠を見る) | DocumentLevel::test_only_value_mismatch_moves_and_only_to_no_same_value・DocumentLevel::test_real_moved_rows・FlagsOffIsP24::test_no_other_profile_is_touched_by_the_branch・FlagsOffIsP24::test_the_cases_do_change_with_the_flag_on_only_where_there_is_no_evidence・HumanDecisions::test_5_p21_last_branch_names_the_current_year_fact_when_there_is_evidence・NoEvidence::test_p24_names_and_p25_does_not | 赤 6 本(DocumentLevel::test_only_value_mismatch_moves_and_only_to_no_same_value・DocumentLevel::test_real_moved_rows・FlagsOffIsP24::test_no_other_profile_is_touched_by_the_branch・FlagsOffIsP24::test_the_cases_do_change_with_the_flag_on_only_where_there_is_no_evidence・HumanDecisions::test_5_p21_last_branch_names_the_current_year_fact_when_there_is_evidence・NoEvidence::test_p24_names_and_p25_does_not)。予測どおり |
| M2 | recipes.py: 証拠 (i) の『同じ枠』の条件を外す(別の枠の fact も証拠にする) | EvidenceI::test_a_different_frame_is_not_evidence・EvidenceI::test_a_plain_frame_vs_a_member_frame_of_the_same_period_is_not_evidence・EvidenceI::test_the_frame_is_compared_after_removing_the_period_prefix | 赤 3 本(EvidenceI::test_a_different_frame_is_not_evidence・EvidenceI::test_a_plain_frame_vs_a_member_frame_of_the_same_period_is_not_evidence・EvidenceI::test_the_frame_is_compared_after_removing_the_period_prefix)。予測どおり |
| M3 | recipes.py: 証拠 (i) の『JPY の fact だけ』の条件を外す | EvidenceI::test_a_non_jpy_fact_is_not_evidence | 赤 1 本(EvidenceI::test_a_non_jpy_fact_is_not_evidence)。予測どおり |
| M4 | recipes.py: 証拠 (i) の『同じ要素名』の条件を外す(同じ枠の別の要素も証拠にする) | EvidenceI::test_a_different_element_is_not_evidence | 赤 1 本(EvidenceI::test_a_different_element_is_not_evidence)。予測どおり |
| M5 | recipes.py: 証拠 (i) の『context が違う』の条件を外す(名指す fact 自身も証拠になる) | EvidenceI::test_the_named_fact_itself_is_not_evidence | 赤 1 本(EvidenceI::test_the_named_fact_itself_is_not_evidence)。予測どおり |
| M6 | recipes.py: LAST_BRANCH_DIGIT_K を 2 から 3 に | EvidenceII::test_the_sign_is_ignored_through_the_absolute_value・EvidenceII::test_the_two_unit_line_is_inclusive・EvidenceII::test_the_unit_is_the_claim_digit_not_a_yen・EvidenceII::test_within_two_units_is_evidence_and_three_units_is_not・FlagShape::test_the_constants_are_pinned_in_letters | 赤 5 本(EvidenceII::test_the_sign_is_ignored_through_the_absolute_value・EvidenceII::test_the_two_unit_line_is_inclusive・EvidenceII::test_the_unit_is_the_claim_digit_not_a_yen・EvidenceII::test_within_two_units_is_evidence_and_three_units_is_not・FlagShape::test_the_constants_are_pinned_in_letters)。予測どおり |
| M7 | recipes.py: 証拠 (ii) の `<=` を `<` に(2 単位ちょうどを含めない) | EvidenceII::test_the_two_unit_line_is_inclusive・EvidenceII::test_the_unit_is_the_claim_digit_not_a_yen・EvidenceII::test_within_two_units_is_evidence_and_three_units_is_not | 赤 4 本(EvidenceII::test_the_two_unit_line_is_inclusive・EvidenceII::test_the_unit_is_the_claim_digit_not_a_yen・EvidenceII::test_within_two_units_is_evidence_and_three_units_is_not・HumanDecisions::test_5_p21_last_branch_names_the_current_year_fact_when_there_is_evidence)。予測は外れ。+1: HumanDecisions::test_5_p21_last_branch_names_the_current_year_fact_when_there_is_evidence |
| M8 | recipes.py: 証拠 (ii) の絶対値どうしの差の項を外す(符号が逆の近さを証拠にしない) | DocumentLevel::test_real_rows_that_stay_value_mismatch・EvidenceII::test_real_documents・EvidenceII::test_the_sign_is_ignored_through_the_absolute_value | 赤 4 本(DocumentLevel::test_real_rows_that_stay_value_mismatch・EvidenceII::test_real_documents・EvidenceII::test_the_sign_is_ignored_through_the_absolute_value・HumanDecisions::test_7_p23_truncation_band_is_kept)。予測は外れ。+1: HumanDecisions::test_7_p23_truncation_band_is_kept |
| M9 | recipes.py: 証拠 (iii) の n から ±9 を外す | EvidenceIII::test_each_exponent_end_to_end・EvidenceIII::test_each_exponent_is_evidence・EvidenceIII::test_plus_and_minus_nine_are_evidence・EvidenceIII::test_the_sign_is_not_asked・FlagShape::test_the_constants_are_pinned_in_letters | 赤 2 本(EvidenceIII::test_plus_and_minus_nine_are_evidence・FlagShape::test_the_constants_are_pinned_in_letters)。予測は外れ。-3: EvidenceIII::test_each_exponent_end_to_end・EvidenceIII::test_each_exponent_is_evidence・EvidenceIII::test_the_sign_is_not_asked 試験を強めた後の再実測: 赤 5 本(予測と一致) |
| M10 | recipes.py: 証拠 (iii) で n が負のときも帯を 精度 × 10^-｜n｜ に狭める(広げない) | DocumentLevel::test_real_rows_that_stay_value_mismatch・EvidenceIII::test_for_a_negative_n_the_band_is_the_precision_times_ten_to_the_abs_n・EvidenceIII::test_real_documents_keep_value_mismatch_by_coincidence | 赤 3 本(DocumentLevel::test_real_rows_that_stay_value_mismatch・EvidenceIII::test_for_a_negative_n_the_band_is_the_precision_times_ten_to_the_abs_n・EvidenceIII::test_real_documents_keep_value_mismatch_by_coincidence)。予測どおり |
| M11 | recipes.py: _written_precision が末尾の 0 を数えず主張の桁をそのまま返す | DocumentLevel::test_real_rows_that_stay_value_mismatch・EvidenceIII::test_for_a_negative_n_the_band_is_the_precision_times_ten_to_the_abs_n・EvidenceIII::test_real_documents_keep_value_mismatch_by_coincidence・EvidenceIII::test_the_band_widens_with_trailing_zeros_of_the_written_number・EvidenceIII::test_written_precision_is_scale_times_ten_to_the_trailing_zero_count・EvidenceIII::test_written_precision_rounds_half_to_even_like_python_round | 赤 6 本(DocumentLevel::test_real_rows_that_stay_value_mismatch・EvidenceIII::test_for_a_negative_n_the_band_is_the_precision_times_ten_to_the_abs_n・EvidenceIII::test_real_documents_keep_value_mismatch_by_coincidence・EvidenceIII::test_the_band_widens_with_trailing_zeros_of_the_written_number・EvidenceIII::test_written_precision_is_scale_times_ten_to_the_trailing_zero_count・EvidenceIII::test_written_precision_rounds_half_to_even_like_python_round)。予測どおり |
| M12 | recipes.py: _written_precision の round を四捨五入(偶数丸めでない)に | EvidenceIII::test_written_precision_rounds_half_to_even_like_python_round | 赤 1 本(EvidenceIII::test_written_precision_rounds_half_to_even_like_python_round)。予測どおり |
| M13 | recipes.py: 証拠 (i) の照合に P23 の _mag_trunc を渡さない(False 固定) | EvidenceI::test_the_truncation_band_is_by_magnitude_when_the_flag_says_so | 赤 1 本(EvidenceI::test_the_truncation_band_is_by_magnitude_when_the_flag_says_so)。予測どおり |
| M14 | recipes.py: 証拠 (i) の照合に書類の丸め方を渡さない(None 固定) | EvidenceI::test_the_matching_band_follows_the_document_rounding | 赤 2 本(EvidenceI::test_the_matching_band_follows_the_document_rounding・EvidenceI::test_the_truncation_band_is_by_magnitude_when_the_flag_says_so)。予測は外れ。+1: EvidenceI::test_the_truncation_band_is_by_magnitude_when_the_flag_says_so |
| M15 | recipes.py: claim_to_recipe が名指した fact を provenance に残さない | DocumentLevel::test_a_real_document_through_the_recipe_keeps_the_named_fact_in_provenance・NoEvidence::test_core_turns_it_into_pointer_not_found_with_the_registered_reason_and_no_pointer・NoEvidence::test_the_unnamed_claim_keeps_the_named_fact_in_provenance_through_the_recipe | 赤 3 本(DocumentLevel::test_a_real_document_through_the_recipe_keeps_the_named_fact_in_provenance・NoEvidence::test_core_turns_it_into_pointer_not_found_with_the_registered_reason_and_no_pointer・NoEvidence::test_the_unnamed_claim_keeps_the_named_fact_in_provenance_through_the_recipe)。予測どおり |
| M16 | recipes.py: 証拠が無いとき no_same_value にするが pointer を残す(名指しを消さない) | 8 本(DocumentLevel::test_only_value_mismatch_moves_and_only_to_no_same_value・DocumentLevel::test_real_moved_rows・EvidenceI::test_a_different_element_is_not_evidence ほか) | 赤 9 本。予測は外れ。+1: EvidenceII::test_the_unit_is_the_claim_digit_not_a_yen |
| M17 | recipes.py: 理由の名 NO_SAME_VALUE を別の字に(登録簿に無い名前) | 9 本(DocumentLevel::test_only_value_mismatch_moves_and_only_to_no_same_value・DocumentLevel::test_real_moved_rows・EvidenceI::test_a_different_element_is_not_evidence ほか) | 赤 20 本。予測は外れ。+11: DocumentLevel::test_a_real_document_through_the_recipe_keeps_the_named_fact_in_provenance・DocumentLevel::test_grounded_and_unverifiable_never_move・DocumentLevel::test_real_rows_that_stay_value_mismatch・EvidenceIII::test_real_documents_keep_value_mismatch_by_coincidence・EvidenceII::test_real_document |
| M18 | recipes.py: _state_of から no_same_value の行を消す(登録の 2 か所のうち片方) | 10 本(DocumentLevel::test_a_real_document_through_the_recipe_keeps_the_named_fact_in_provenance・DocumentLevel::test_grounded_and_unverifiable_never_move・DocumentLevel::test_only_value_mismatch_moves_and_only_to_no_same_value ほか) | 赤 11 本。予測は外れ。+1: NoEvidence::test_the_unnamed_claim_keeps_the_named_fact_in_provenance_through_the_recipe |
| M19 | registry_setup.py: 理由 no_same_value を POINTER_NOT_FOUND の登録から外す(登録の 2 か所のうち片方) | FlagShape::test_no_same_value_is_registered_in_the_two_places・NoEvidence::test_core_turns_it_into_pointer_not_found_with_the_registered_reason_and_no_pointer | 赤 9 本。予測は外れ。+7: DocumentLevel::test_grounded_and_unverifiable_never_move・DocumentLevel::test_only_value_mismatch_moves_and_only_to_no_same_value・DocumentLevel::test_real_moved_rows・DocumentLevel::test_real_rows_that_stay_value_mismatch・EvidenceIII::test_real_documents_keep_value_mismatch_by_coincidence・EvidenceII:: |
| M20 | vocabulary.py: 旗 last_branch_names_only_if_evidence の既定を真に(全 profile が証拠を見る) | FlagShape::test_the_flag_is_false_by_default_and_true_only_for_p25・FlagShape::test_with_the_flag_false_p25_is_p24・FlagsOffIsP24::test_no_other_profile_is_touched_by_the_branch・FlagsOffIsP24::test_the_cases_do_change_with_the_flag_on_only_where_there_is_no_evidence・HumanDecisions::test_5_p21_last_branch_names_the_current_year_fact_when_there_is_evidence・NoEvidence::test_p24_names_and_p25_does_not | 赤 10 本。予測は外れ。+4: DocumentLevel::test_only_value_mismatch_moves_and_only_to_no_same_value・DocumentLevel::test_real_moved_rows・FlagShape::test_the_default_profile_is_still_p22_in_step_1・FlagsOffIsP24::test_every_case_is_identical_to_p24_with_the_flag_off |
| M21 | vocabulary.py: PROFILES への P25 の登録を外す | DocumentLevel::test_only_value_mismatch_moves_and_only_to_no_same_value・FlagShape::test_p25_is_p24_plus_exactly_the_one_flag・FlagShape::test_the_flag_is_false_by_default_and_true_only_for_p25・FlagShape::test_the_profiles_literal_line_is_not_touched・HumanDecisions::test_5_p21_last_branch_names_the_current_year_fact_when_there_is_evidence・NoEvidence::test_p24_names_and_p25_does_not | 赤 34 本。予測は外れ。+28: DocumentLevel::test_a_real_document_through_the_recipe_keeps_the_named_fact_in_provenance・DocumentLevel::test_grounded_and_unverifiable_never_move・DocumentLevel::test_real_moved_rows・DocumentLevel::test_real_rows_that_stay_value_mismatch・EvidenceIII::test_each_exponent_end_to_end・EvidenceIII::test_r |
| M22 | recipes.py: 証拠があっても名指さない(証拠の判定の結果を捨てて常に no_same_value) | 15 本(DocumentLevel::test_real_rows_that_stay_value_mismatch・EvidenceIII::test_each_exponent_end_to_end・EvidenceIII::test_real_documents_keep_value_mismatch_by_coincidence ほか) | 赤 12 本。予測は外れ。-3: EvidenceII::test_a_loss_sentence_uses_the_signed_target・EvidenceII::test_the_sign_is_ignored_through_the_absolute_value・EvidenceII::test_the_unit_is_the_claim_digit_not_a_yen 試験を強めた後の再実測: 赤 15 本(予測と一致) |
| M23 | recipes.py(P24 の率の枠の取り直し (ii))の比の型: 旗 frame_rebind のガードを外す | FrameRebind::test_the_flag_off_keeps_value_mismatch_for_the_pct_forms | 赤 1 本(FrameRebind::test_the_flag_off_keeps_value_mismatch_for_the_pct_forms)。予測どおり |
| M24 | recipes.py(P24 の率の枠の取り直し (ii))の変化率の型: 旗 frame_rebind のガードを外す | FrameRebind::test_the_flag_off_keeps_value_mismatch_for_the_pct_forms | 赤 1 本(FrameRebind::test_the_flag_off_keeps_value_mismatch_for_the_pct_forms)。予測どおり |

engine の変異 24 通りは、作業木とは別のコピー(scratchpad の使い捨ての木。adapters/・core/・tests/adapters/ を写した)の recipes.py・vocabulary.py・registry_setup.py に 1 つずつ入れ、tests/adapters/xbrl/test_recipes_p25.py(M23・M24 は tests/adapters/xbrl/test_recipes_p24.py の率の型の 1 本)だけを走らせ、毎回コピーを作り直して戻した(木は最後に消した。実木の engine 3 file は走らせの前後で sha256 が同じ)。予測は実走の前に固定した(impl1/mut_predictions.json)。手で走らせた。この表は記録の写しを門が縛るだけで、変異そのものを毎回走らせてはいない。基準線は P25 の試験 63 本・P24 の率の型の 1 本(どちらも全緑)。全部赤: 黙った変異は 0。予測の当たり 13・外れ 11(外れのうち『赤が多かった』が 9・『少なかった』が 2)。『少なかった』2 件(M9・M22)は試験の弱さが原因だった: 試験が engine の定数 LAST_BRANCH_SCALE_EXPONENTS から n の表を作っていたこと(M9)と、証拠の種類の欄だけを見て名指したかを見ていなかったこと(M22)。試験を直して(n を字で留め、名指しの結果も見る)再実測したら予測と一致した。

## 12. 封と実物の食い違い

- 封 §0 の試作の既存試験の赤は三十三本(登録の一覧十三・`test_mutations` 一・sha 十四・diff の門五)。実測は第十節の表の本数で、種類の数え方も違う(旗の形を別の種類にした)。**種類は封 §2 の L-8 の字の中**に収まっていて、L-8 は本数でなく種類を予測しているので判定に響かない。本数の差の内訳は一件ずつは調べていない。
- 封 §1 の規則(i)(ii)(iii)・偶数丸め・n が負のときの帯・`JPY` の fact・`no_same_value` の登録先二か所は、実装の字と一行ずつ照らして一致した。試作の差分(`engine_diff_v3.patch`)と実装の差分は、**コメントの字を除いてコードの行が同じ**(挿入と削除の行数も同じ)。コメントは封の path に書き換えた。
- **記録の一行の「直し」の欄は後で不正確と分かった(2026-10-21 の追記。記録は直していない)**: 第十節の赤の表の `test_xbrl_period_bind_result.py` の `test_16_frozen_bundle_last_generation_is_the_working_tree_and_declares_step_2` の「直し」は「門は P24 のとき直した形のまま」と書いたが、全部を走らせ直すと、`fixtures/frozen_bundle_sha.py` に世代を足しただけでは緑にならなかった。この門の中の『後の封の宣言を新しい順に飛ばして読む』ための封の名の一覧(`XBRL_VOCAB_SEAL_2026-10-21`・`XBRL_ROUNDING_SEAL_2026-10-21`)の先頭に `XBRL_LASTBRANCH_SEAL_2026-10-21` を足した(P23・P24 の段 1 で同じ形に直した型。人間の決定の字の門ではない。種類は「sha の留め」のまま)。赤の本数は変わらない。
- 封に無い実装の判断(仕様を変えない範囲): 証拠が在って名指したときの理由の字(`last_branch_evidence`)を claim の内部の欄に残した(顧客の出力には出ない)。

## 13. 限界

- 手元の cache の 67 書類(経営分析の文を持つ)。規則はこの 67 書類を読んで作った(試作 3 回)。無作為ではない。67 書類での違う 0 は新しい標本での違う 0 を意味しない。
- 新しい標本は手元に無い: 手元の cache の 67 の外 214 書類は全部 jpsps(特定有価証券)で、67 と同じ抽出は経営分析の文を取れず claim は 0(P24 の W-7 で確かめた)。
- L-1・L-2・L-4〜L-7 は試作の再現で、外れるなら実装が試作と違う。本当に外れうるのは L-3(試作で読んでいない行)。
- 読み(L-2・L-3)は実装席の人(エージェント)の読みで、門では縛れない(数と行の対応だけ縛る)。『分からない』は『分からない』のまま数えた。
- L-7 の注入は『末尾の桁 ±3・10 倍』の 2 型で、1 回に 1 件。向きの語の反転・ほかの誤りの作り方では未測定。
- L-5 の儀式は同梱 1 書類(S100Z4Q1)。注入は型 V1・V2 だけ。
- 『違う』を『要確認』に弱める代価がある(封 §3): 増減の数・前期の数で、注入前に結んだ fact と名指す fact が別物の誤りは、どの証拠にも当たらず要確認になる。誤りを通す数は変わらない。
- 増減の数で、表示桁の fact の当期 - 前期と 1 単位違う正しい文は要確認になる(丸めた値の差の帯の問題。この封では直さない)。
- 顧客の出力(verify_document)には provenance の欄が無い。名指した当期の値を見せるのは日本語の報告形の封で決める。

## 14. 迷った点

- 「分からない」の扱い: 「違う」にも「正しい文」にも寄せず、そのまま数えた。判定の二%の分子には「文が本当に違う」だけを入れた。「分からない」を全部「違う」に数えても分子は二件で、読んだ行の一%に届かない。
- L-2 の「全部読んで」: 残る行は全部読んだ(読みは第三節)。
- 読みの担い手: 読みは実装席の人(エージェント)の読みで、人間の読みではない。封は読みの担い手を指定していない。人間が読み直すときは、記録の `L3.未読の行` と `L2.残る行` の行(文・名指した fact・根拠)から入れる。

## 15. 再現

```
cd audit-core
python3 measure/xbrl_lastbranch_2026-10-21.py --stage all --readings <読みの file> --mutations <変異の表の file> --run-tests   # 記録を書く(約 三十分)
python3 -m pytest -q tests/measure/test_xbrl_lastbranch_result.py                       # 門(軽い走らせ直しを含む)
AUDIT_CORE_LASTBRANCH=1 python3 -m pytest -q tests/measure/test_xbrl_lastbranch_result.py  # 全部の走らせ直し(約 十五分)
```

記録の所要秒: {"L1 L2 L3": 25.6, "L4": 81.8, "L5": 68.6, "L6": 0.0, "L7": 625.5, "L8": 1123.4, "provenance": 0.0, "全体": 1933.8}。
