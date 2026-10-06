# XBRL(EDINET)の実物調査と、封じた予測との照合(2026-10-06、司令塔)

予測の封: [XBRL_ADAPTER_PREDICTION_2026-10-06.md](XBRL_ADAPTER_PREDICTION_2026-10-06.md)、コミット `9d50738`(2026-10-06 08:26:46 +0900)、sha256 `0b82eeb297bd30a892c0d5e0efc05769cd536e1b3ea9773c0279ee5265b13777`。この文書はその後に書いた。**Adapter は作っていない。API の鍵も作っていない(アカウント作成は人間の操作)。** 調べたのは「仕様 v0.2 の前提が実物に在るか」まで。

## 1. 何を、どこで確かめたか

| 項目 | 確かめ方 | 結果 |
|---|---|---|
| API の鍵 | `https://api.edinet-fsa.go.jp/api/v2/documents.json?date=2026-10-01&type=2` を鍵なしで取得 | **401** `Access denied due to invalid subscription key`。鍵(Subscription-Key)が要る |
| 鍵の取得・費用 | 解説記事(複数) | アカウント作成 → API キー発行。無料(第三者の記述。公式の規約ページに料金の記述は無い) |
| 利用規約 | 公式 [利用規約](https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/WZEK0030.html)(令和 7 年 4 月 25 日改訂) | **PDL1.0 準拠。出典の記載が要る**(「出典:EDINET閲覧(提出)サイト(URL)、PDL1.0(URL)」)。**編集・加工したことと主体の記載が要る**(国の未加工のものに見せない)。**スクレイピング禁止だが API 機能の利用は例外**。短時間の大量アクセスは禁止、違反時は予告なく停止。国・金融庁は API の停止・性能低下の損害を賠償しない。PDL1.0 の本文は読んでいない(営利利用の可否は PDL1.0 と第三者の解説に拠る) |
| 書類取得 API の type | 解説記事 | 1 = XBRL(ZIP)、2 = PDF、3 = 添付、5 = CSV(XBRL を CSV に変換。**utf-16**)。4 = 英文は記事に無し |
| ZIP の中身 | 解説記事 2 本 | `XBRL/PublicDoc/*.xbrl`(インライン XBRL の htm と共に) |
| タクソノミの種類 | 金融庁 [EDINET タクソノミの概要説明(2023-12)](https://www.fsa.go.jp/search/20231211/1b-1_GaiyoSetsumei.pdf)(PDF 75 ページを fitz で抽出) | `jpcrp`(開示府令)・`jppfs`(財務諸表本表)・`jpigp`・`jpdei`(DEI) |
| コンテキスト ID の命名 | 金融庁 [報告書インスタンス作成ガイドライン(2025-11)](https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/download/ESE140112.pdf)(PDF 101 ページを fitz で抽出)図表 5-4-2・5-4-3 | **`{相対期間又は時点}{期間又は時点}((_{メンバーの要素名})×n)(_{連番 3 桁})`**。例: `CurrentYearDuration`、`Prior1YearInstant`、`CurrentYearDuration_NonConsolidatedMember`。**コンテキスト ID が重複したら 2 つ目から `_002`** |
| 同一要素の複数の値 | 同ガイドライン 図表 5-6-3 | **同一の要素・コンテキスト・ユニットで異なる値のタグ付けは禁止。** 同じ値が複数回出るときは全部にタグ付け |
| 金額の桁 | 同ガイドライン 図表 5-6(iXBRL の例) | `<ix:nonFraction name="jpcrp_cor:NetSalesSummaryOfBusinessResults" contextRef="Prior4YearDuration" unitRef="JPY" decimals="-6" scale="6" format="ixt:numdotdecimal">231,282</ix:nonFraction>` → 表示は百万円、実値は × 10^6。**精度(`decimals`)がデータ自身に宣言されている** |
| MD&A の文章 | 概要説明 2-5-2-4(「経営者による財政状態、経営成績及びキャッシュ・フローの状況の分析」は様式ツリーのテキストブロック)+ Web 検索で要素名 `jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock` | **文章の節は textBlock としてタグ付けされる。中身は HTML**(解説記事は BeautifulSoup で剥いている)。要素名は実インスタンスで未確認 |
| 文章の中の「前年同期比 x%」 | 未確認 | **実インスタンスを取っていない**(鍵が要る)。予測 §3 の「丸めが普通」は未検証 |
| 関連データセット | Web 検索 | [chABSA-dataset](https://github.com/chakki-works/chABSA-dataset)(有報の文から業績の文を抽出したデータ)。中身は読んでいない |

## 2. 封じた予測との照合

### 2.1 予測 §1(仕様 v0.2 への当たり)

| 数 | 予測 | 実物で分かったこと | 判定 |
|---|---|---|---|
| 層の数 | 4 のまま | contextRef・unitRef・decimals・scale は全部 **Evidence Pointer の locator と normalization の中身**で、新しい層は要らない。ただし **Adapter を繋いでいないので「増えなかった」とは言えない** | 設計上は一致。**未測定** |
| scheme | +2 まで | `xbrl:`(要素名 + contextRef + unitRef)と `filing:`(docID・提出日・会社・期)で足りる。CSV(type=5)を使うなら同じ `xbrl:` の別の解決器 | 設計上は一致。未測定 |
| form | +0 | 金額は `direct_value`、前年比は `derived_value`、文章の数は span。足りない形は見つからない | 一致(設計上) |
| modifier | +0、`time_range` 初出 | **`time_range` は contextRef の相対期間(`CurrentYearDuration` / `Prior1YearDuration`)に写る。** 基準日は `filing:` の期末日。修飾の定義で足りる | 一致 |
| `tolerance` 初出 | 人が承認した幅 | **半分外れ。** 構造化された数の精度は `decimals="-6"` として**データ自身が宣言している**。契約の許容幅は、文章側の「約 15%」「百万円未満切捨て」にだけ人の承認が要る。→ v0.2 §4 の `tolerance` に「データ宣言の精度を既定とし、文章側の丸めだけ人が承認」を足す | **外れ(良い方向)** |
| Core 変更の分類 | 登録追加のみ | Adapter を繋いでいない | **未測定** |
| F-2 の再来(鍵の約束) | 再来する | **再来する。** 同じ要素名が contextRef(相対期間 × 時点/期間 × 連結/個別 × メンバー × 連番)で何通りにもなる。鍵の正規化なしに「売上高」は 1 つに決まらない | 一致 |
| F-3 の再来(正規化の重なり) | 再来する | **再来する。** 1 つの数に `scale`(桁)・`format`(カンマ)・`unitRef`(JPY)・`decimals`(精度)・符号(損失)が重なる | 一致 |

### 2.2 予測 §2(例 4 つ)

| 例 | 予測 | 実物 | 判定 |
|---|---|---|---|
| 売上高 1,280 百万円 | A | `xbrl:jppfs_cor:NetSales@CurrentYearDuration`(要素名は `jpcrp_cor:NetSalesSummaryOfBusinessResults` の例で形を確認)。桁は `scale` で解決 | 一致(設計上。実インスタンス未取得) |
| 前年同期比 15% 増 | A(tolerance 要) | `Prior1YearDuration` が命名規約に在る。式の入力は 2 つの contextRef。精度は `decimals` | 一致 |
| 堅調に推移 | B | 線の登録簿は無い | 一致(作りから) |
| 来期は増収を見込む | C | 予測台帳の descriptive | 一致(作りから) |

### 2.3 予測 §3(調査そのもの)

| 項目 | 予測 | 実物 | 判定 |
|---|---|---|---|
| 鍵 | 要る・無料 | 401 で要ることを確認。無料は第三者の記述 | 一致(無料は未確認) |
| 取得 | 一覧 API + 取得 API(ZIP) | type=1 ZIP、type=5 CSV もある | 一致 + CSV |
| 数の形 | 要素名 + contextRef + unitRef | その通り + `decimals` + `scale` + `format` | 一致(足りなかった属性 3 つ) |
| 文章 | textBlock に MD&A | 概要説明 2-5-2-4 で確認。HTML | 一致 |
| 利用条件 | 予測を置かない | PDL1.0・出典・加工の明記・API は例外 | ― |
| 丸め | 百万円・約・小数 1 桁 | 構造化側は `decimals` で宣言。文章側は未確認 | 半分未確認 |

**予測に無かった事実(X-1〜X-4)**

| # | 事実 | 仕様への影響 |
|---|---|---|
| X-1 | **データ自身が精度を宣言する**(`decimals`) | `tolerance` の既定をデータの宣言から取り、人の承認は文章側の丸めにだけ要求する(v0.2 §4 の修正候補) |
| X-2 | **同一要素・同一コンテキスト・同一ユニットで異なる値は仕様で禁止** | Q-6 の「正準データ自体が決められない」は、タグ付けされた数には起きない(起きれば提出側の規約違反)。文章と数の矛盾だけが残る |
| X-3 | **コンテキスト ID に連番 `_002`** | 鍵の正規化に「連番は同じ鍵の別の出現」の規則が要る(F-2 の XBRL 版) |
| X-4 | **出典と加工の明記が規約の条件** | 顧客向けの出力に「出典: EDINET、加工: 当方」を固定文で置く = 生成側束縛の固定文(門 (vii) と同じ型) |

## 3. 採用の判定(予測 §4 の表に当てる)

| 条件 | 結果 |
|---|---|
| 層 4・scheme ≤ +2・意味変更 0 | 層と scheme は設計上満たす。**意味変更は Adapter を繋ぐまで測れない** |
| 例 1・2 が A | 設計上 A。実インスタンスで未確認 |
| 利用条件が実演を許す | **許す**(PDL1.0・出典・加工の明記・API 経由) |
| 外れ | `tolerance` の 1 件(良い方向)。残りは未測定 |

**司令塔の提案(人間の判断)**: XBRL を 2 つ目の Adapter 候補として**採用の検討に進めてよい**。ただし次の順で、どれも小さく。

1. **人間が EDINET の API アカウントを作る**(司令塔・席は作らない)。鍵は env に置き、repo に入れない。
2. **使い捨ての探り 1 本**(Adapter ではない): 有報 1 件を取り、MD&A の textBlock から「前年同期比」「増加」「減少」を含む文を数え、同じ書類の `jppfs`/`jpcrp` の数に `xbrl:` ポインタで束縛できた割合(束縛率)と、`decimals` を既定の許容幅にして再計算が一致した割合を出す。**繋ぐ前に数を予測して封じる**(層・scheme・Core 変更の分類・束縛率)。
3. その数で、v0.2 が「将棋の門の整理」か「仕様候補」かを判定する。

## 4. この調査が見ていないもの

- 実インスタンス(鍵が要る)。MD&A の文章に数がどの頻度で入るか、丸めの実態、要素名の実名。
- CSV(type=5)の列の構成。レート制限の実数。
- PDL1.0 の本文(営利利用の条件の原文)。
- chABSA-dataset の中身とライセンス。
