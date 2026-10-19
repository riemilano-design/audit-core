# 読解記録 4: Evidence-Grounded Trading Desk Risk Memos over SEC Filings

**読解状況: 原文全文を読んだ**(PDF 17 ページ・抽出 45,070 字、空白ページ 0)。
図(Figure 3・4・5 ほか)は画像で抽出に含まれない。表は抽出されるが**段組の崩れがあり、Table 1・5・7 の一部の数は列の対応が読み取れない**。本記録では本文が文章で述べている数だけを引く。

## 0. 前セッションの疑義 3 点の照合結果(先に置く)

前セッションは読解前に 3 点を報告していた。原文で照合した結果は次のとおり。

| 疑義 | 原文での照合 | 判定 |
|---|---|---|
| 掲載年月と対象データ期間に内部矛盾 | 「Vol. 3(2), pp. 60-76, **February 2023**」は**各ページのヘッダ/フッタ(出版社のマストヘッド)に 15 回繰り返される**だけで、著者が執筆時点を 2023 年 2 月と主張する記述は本文に無い。対象コーパスは本文 p.4 で「SEC Financial Statement Data Sets for **2023 Q1-Q4**」。PDF 生成日は **2026-06-04**(メタデータ)。 | **矛盾は確認できた。ただし出どころは出版社の巻号・日付スタンプであり、著者の主張ではない。**著者の過失として扱うべき根拠は無い |
| 100.0% は実物の SEC データでなく fixture 上の測定 | **原文が明記している。**p.4: 「The local sandbox run used a deterministic SEC-schema fixture **because the environment blocked binary ZIP retrieval**」。p.2: 「The reported local results are empirical measurements from that fixture…they are not illustrative placeholders」。p.6: fixture は **固定 seed 20230510** で生成され、「values are sampled from industry-specific financial priors and **constrained so that accounting identities and ratios remain coherent**…liabilities and equity sum to assets **by construction**」。p.6: 「This construction is not used to claim SEC-wide performance」 | **確認できた。かつ著者が自ら開示している。**隠された欠陥ではない |
| 査読の質は未確認 | Journal of Advanced Computing Systems (JACS), ISSN 3066-3962, SciPublication, DOI 10.69987/JACS.2023.30205。**査読過程の記述は本文・誌面のどこにも無い** | **依然として未確認** |

**読解で新たに判明した、より重い事実(原文記載)**

> **測定された pipeline に LLM は入っていない。** p.6: 「Generation is implemented as a **deterministic memo renderer** in the executable artifact. This choice removes vendor API variability and makes all reported numbers exactly reproducible.… The code also supports replacing the renderer with an external LLM output adapter while preserving the same verification and evaluation layer.」

つまり「No-RAG / Text RAG / Verifier RAG / Structured+Verifier」の 4 系列はすべて**決定論的レンダラ**が生成した memo に対する測定であり、LLM の振る舞いの測定ではない。これも著者が開示している。

## 1. 書誌情報・公開日・バージョン

| 項目 | 値 | 区分 |
|---|---|---|
| 題 | Evidence-Grounded Trading Desk Risk Memos over SEC Filings: **Retrieval-Augmented Generation with XBRL Numeric Verification** | 論文記載 p.1 |
| 著者 | Kai Zhang(Financial Engineering, Baruch College)、Siquan Meng(Applied Business Analytics, Boston Univ.)、Eric Zhou(CS, Columbia) | 論文記載 p.1 |
| 掲載 | Journal of Advanced Computing Systems (JACS), ISSN 3066-3962, Vol. 3(2), pp. 60-76, February 2023, DOI 10.69987/JACS.2023.30205(SciPublication) | 論文記載 |
| PDF 生成 | 2026-06-04(メタデータ) | 独自確認 |
| 取得元 | `pdfs.semanticscholar.org/9d57/…` / sha256 `2ad0a528…` | 独自確認 |
| arXiv 版 | **確認できず** | 未確認 |

## 2. 研究目的・解こうとしている問題

**論文記載**: トレーディングデスクが使う短い risk memo を、SEC の XBRL 数値 fact に接地させ、**報告された数と導出した比率のすべてを証拠基盤に対して検証する** pipeline。問題は「流暢な要約は作れるが、裏付けのない主張・引用のずれ・算術誤りが、検証なしの生成を金融の意思決定支援に使えないものにする」(Abstract)。

## 3. システム構成と処理フロー

**論文記載 p.6(Table 4 の 4 系列)**

| 系列 | 証拠の出どころ | 生成 | 検証器 | 測る失敗 |
|---|---|---|---|---|
| No-RAG | なし | prior-only memo renderer | なし | 誤った fact・裏付けのない主張・引用欠落 |
| Text RAG | TF-IDF 上位 30 証拠文 | cited memo renderer | 引用の検査のみ | 古い/誤った数の写し |
| Verifier RAG | 同上 | 同上 | **XBRL numeric verifier** | 残余の検索/引用の誤り |
| Structured+Verifier | 正規の filing fact map(テキスト検索を迂回) | 同上 | 同上 | ― |

- パーサは accession number で submission identity と numeric fact を結合し、**whole-entity USD の正規 fact** だけを残し、presentation フィールドを付けて「その fact が損益計算書・貸借対照表・CF 計算書のどこから来たか」を述べられるようにする(p.4)。
- memo は**不透明な prose ではなく claim として内部表現**される(p.6): fact claim = (tag, value, citation, support flag)、ratio claim = (ratio name, computed value, component tags, citation policy)、risk-label claim = (desk-risk category)。prose は claim からレンダリングできるが、**評価は claim レコードを直接使う**。
- 「This representation makes the audit log precise and prevents the evaluation from depending on sentence segmentation or wording choices」(p.6)。

## 4. 主張・証拠・概念・期間・単位・値の対応付け

- 対応づけの鍵は **XBRL の evidence key**(accession number + tag + presentation 位置)。
- 比率は**成分 fact を名指しし、検証済みの入力から計算し、各成分を支える evidence key を引用する**ことが要求される(p.13 の拡張方針)。
- 期間・単位: 「canonical whole-entity USD facts」に限定することで単位を固定。**期間の照合規則の記述は見つからなかった**(未確認)。
- 概念の同定: **15 の canonical financial tag** に限定(p.4 Table 1 の列に `StockholdersEquity` 等)。概念同定の曖昧性は扱っていない。

## 5. 決定論的処理と LLM が担う処理の境界

- **測定された構成では、生成も検証も決定論**(§0 の新事実)。LLM はコード上の差し替え口としてのみ存在する。
- したがって「LLM と決定論の境界」はこの論文では**実験的に測られていない**。
- p.6: 「Verifier RAG keeps the same retriever and generator but adds a deterministic check after generation. Structured+Verifier gives the generator the canonical fact map before generation and still checks the output afterward.」 → 測っているのは **(a) 証拠へのアクセス・(b) 数の正しい写し・(c) 写した数の上での正しい算術** の 3 効果の分離(p.6)。

## 6. 保留・棄却・人手確認の条件

- **保留(abstain)の仕組みは記述されていない。** 検証器は「修復する」(p.6: 「repairs numeric facts and ratios against the canonical fact table」)。VeriFin の abstain や Audit Core の UNVERIFIABLE に相当する状態が無い。
- 人手確認: **記述なし**(未確認)。評価は claim レコードから機械生成した誤り分類(p.7: 「The error taxonomy in the results section is therefore generated directly from claim records, not from manual inspection after the fact」)。

## 7. 評価データ・件数・比較対象・実験条件

- 対象データセット(名目): SEC Financial Statement Data Sets 2023 Q1–Q4。公式 manifest は 4 本の URL とサイズを記録(Q1 108.69MB・Q2 111.50MB・Q3 112.32MB・Q4 114.70MB)。
- **実際に測ったもの**: 決定論的 SEC-schema fixture。**320 issuer/四半期 × 4 = 1,280 filing、19,200 numeric fact、15 canonical tag**。固定 seed 20230510。各 filing は CIK・accession number・form type・SIC code・reporting period・filed date・statement code・line number・tag・unit・value を持つ。
- 生成した memo **300 本**(Abstract)。
- fixture の issuer は**匿名**(p.13: 「The fixture contains anonymized issuers rather than public company names and therefore cannot support issuer-specific economic conclusions」)。

## 8. 報告された指標・結果とその適用範囲

**論文記載(Abstract・§Results)**

| 系列 | numeric exactness | citation precision |
|---|---|---|
| No-RAG | 53.8% | 0.0% |
| Text RAG | 88.1% | 63.4% |
| Verifier RAG | 98.4% | 91.5% |
| Structured XBRL RAG | **100.0%** | **100.0%** |

- 検索: Recall@5 52.9%、Recall@10 80.7%、**k=20 と k=30 で 100.0%**(Table 5)。precision は k が増えると下がる。
- 比率精度(Table 7): No-RAG の MAE 0.138–0.144、Text RAG 0.042–0.045、**検証ありの 2 系列は決定論的 run で比率誤差 0**。
- p.9 の結び: 「Desk users do not need a more eloquent explanation of leverage; they need the leverage number to equal Liabilities divided by Assets for the cited filing.」

**適用範囲(独自推論を含む)**
- **100.0% / 比率誤差 0 は、(a) 決定論的レンダラが (b) 正規 fact map を直接与えられ (c) 会計等式が構成上成り立つ合成 fixture 上で、(d) 決定論的検証器に照合された結果**である。4 条件のうち 3 つが構成上の必然に近いので、この 100% は手法の一般的な性能ではない。論文自身も「This construction is not used to claim SEC-wide performance」と書いている。
- Recall@20 = 100.0% も同様に fixture 上の値。

## 9. 著者が明記した制約・失敗例

**Limitations 節がある**(p.13、4 段落)。内容:
1. 面の財務諸表の数値 fact に限定。トレーディングのリスクは脚注・MD&A・セグメント開示・訴訟・オフバランス債務・市場文脈にも依存する。「The SEC flat files used here are therefore a strong evidence base for numeric claims but **not a substitute for full filing review**」。
2. **「the verifier treats XBRL facts as gold for experimental purposes. In production, XBRL facts still require filing-level review because registrants can file amendments or use taxonomy choices that require domain judgment」**。
3. 厳密な算術等式とコンパクトな比率集合のみ。実運用のデスクなら covenant 固有の計算・セクター固有の指標・満期スケジュール・株数の影響・時系列比較が加わる。
4. fixture は匿名 issuer なので issuer 固有の経済的結論は支えられない。

さらに p.3: 「The local execution environment did not permit direct binary download of the four official SEC quarterly ZIP files, so the package contains the official URL manifest and a downloader, and the manuscript reports the locally executed SEC-schema fixture results. **This scope is stated in the method and limitations so that the data, methods, and claims remain logically coherent.**」

## 10. Audit Core との共通点・相違点

**共通点**
- **memo を claim の集合として内部表現し、claim レコードを直接評価する**(prose の文分割や語の選び方に評価が依存しないようにする)。Audit Core の Claim 分解と同じ発想。
- 検証を生成の後段に置く決定論的な層。
- 「すべての数が証拠キーを引用する」ことを要求する。

**相違点**
- **保留の状態が無い**(検証器は修復する)。Audit Core の 4 状態のうち UNVERIFIABLE / POINTER_NOT_FOUND に相当するものが設計に無い。
- 測定が合成 fixture 上。Audit Core は実物の EDINET 書類で測っている(**この対比は、Audit Core の測り方が強い点**)。
- LLM を入れた測定が無い。Audit Core は AI が書いた文を入力に測っている。

## 11. 現行設計に対する示唆(独自推論)

1. **この論文の数値は Audit Core の比較基準として使えない。** 生成も検証も決定論・材料は合成 fixture・会計等式は構成上成立。営業資料で「他方式は 88%、我々は…」の形に引用すると誤りになる。
2. 一方、**claim レコードを評価の単位に置く設計**は Audit Core と同じで、独立な到達点として記録する価値がある。
3. **limitations 2 の指摘は Audit Core にそのまま効く**: 「XBRL fact を gold として扱うのは実験の都合。実運用では訂正報告や taxonomy の選択の余地があるので filing レベルのレビューが要る」。Audit Core の GROUNDED は「EDINET の fact と一致した」の意味であって「正しい」の意味ではない。この区別は営業表現のリスクとして `sales_language_risks.md` に記録した。
4. **検索は Recall@20 で 100% に達しても足りない**という論旨(「retrieval must be paired with exact structured lookup」)は、Audit Core が検索でなく構造化ポインタで照合する設計の方向と一致する。ただし根拠は fixture 上の数。

## 12. 根拠箇所

| 内容 | 箇所 |
|---|---|
| Abstract(4 系列・100.0%・fixture 1,280/19,200) | p.1(抽出 48–55 行) |
| ZIP 取得不可とスコープ宣言 | p.3(抽出 150–161 行) |
| データセット・fixture 構成 | p.4(抽出 225–247 行) |
| fixture の生成(seed 20230510・構成上の等式) | p.6(抽出 425–445 行) |
| 決定論的 memo renderer | p.6(抽出 482–495 行) |
| 4 系列の梯子・3 効果の分離 | p.6(抽出 496–520 行) |
| claim としての内部表現 | p.6(抽出 521–540 行) |
| 検索結果 Recall@k | p.8 §Results(抽出 685–705 行) |
| 比率誤差 0 | p.9(抽出 805–825 行) |
| Limitations(4 段落) | p.13(抽出 1305–1345 行) |
| マストヘッド「February 2023」 | 全 15 ページのヘッダ |
