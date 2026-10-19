# 読解記録 3: FinAuditing

**読解状況: 原文全文を読んだ**(PDF 12 ページ・抽出 72,437 字、空白ページ 0)。
図(Figure 1〜4)は画像で抽出に含まれない。**Figure 4 の FinMR 棒グラフの個別の値は読めていない**(本文が挙げた最良値 13.86% と誤り率の帯 70–83% / 10–27% のみ本文から確認)。

## 1. 書誌情報・公開日・バージョン

| 項目 | 値 | 区分 |
|---|---|---|
| 題 | FINAUDITING: A Financial Taxonomy-Structured Multi-Document Benchmark for Evaluating LLMs | 論文記載 |
| 著者 | Yan Wang ほか(The Fin AI・Columbia・Stevens・RPI・Cardiff・McGill・Manchester ほか)。**2 番 FinTagging と筆頭著者・所属が重なる** | 論文記載 p.1 |
| arXiv | 2510.08886**v3** [cs.CL]、v1 = 10 Oct 2025、v3 = 17 May 2026(取得したのは v3。PDF メタ 2026-05-19) | 論文記載 + arXiv abs |
| 採録 | **SIGIR 2026 Resource Track 採録**(arXiv comments: "Accepted by SIGIR 2026 Resource Track. Pre-camera-ready version") | arXiv abs |
| 公開物 | `github.com/The-FinAI/FinAuditing`、`huggingface.co/collections/TheFinAI/finauditing`、公開評価コンテストの公式ベンチ | 論文記載 p.1 脚注 1–3 |
| ファイル | `papers/p3_finauditing_2510.08886.pdf` sha256 `a27bd3d8…` | 独自確認 |
| 参考記事 | beancount.io「FinAuditing: LLMs Score Under 14% on SEC XBRL Tasks」(解説。原論文ではない)。`papers/ref_beancount_finauditing_article.html` | 独自確認 |

## 2. 研究目的・解こうとしている問題

**論文記載 p.1-2**: 財務監査を「構造化情報の推論問題」として定式化し、LLM が専門水準の監査を支えられるかを測る。既存ベンチの 3 つの限界 ― (1) Contextual Isolation(孤立した断片)、(2) Surface-Level Evaluation(局所的な正しさのみ)、(3) Taxonomy Underutilization ― を埋める。
導入の例: 高位の要約で「Total Cash」$100M、下位の開示の合計は $95M(Figure 1)。

## 3. システム構成と処理フロー

**論文記載 §3.1**: `f: (D, T) → E`。D は相互接続した **6 つの XML 文書**(instance / schema / calculation linkbase / presentation linkbase / definition linkbase / label linkbase、Table 3)、T は参照 US-GAAP taxonomy、E は見つかった誤りの記述。
3 つのサブタスク:
- **FinSM**(Financial Semantic Matching): 情報検索のパラダイム。filing 中の、taxonomy と意味的に整合しない US-GAAP タグの集合を返す。指標は HR@k・R@k・Macro-F1@k(k ∈ {1,5,10,20})。
- **FinRE**(Financial Relationship Extraction): 2 概念間の誤り関係型を 3 値分類 ― **Reversal**(親子が逆)/ **Inappropriateness**(子が不適切な親に付く)/ **CombinationErr**(axis と member の無効な組み合わせ)。指標は Acc・Macro P/R/F1。
- **FinMR**(Financial Mathematical Reasoning): `extracted_value`(instance に報告された値)と `calculated_value`(calculation 関係から計算した値)を JSON で両方出させ、比較して報告値の正しさを判定。指標は **LLM-as-a-judge による accuracy** + SER(構造誤り率)・EER(抽出誤り率)・CER(計算誤り率)。

**文書の分割**: 完全な filing は長すぎるため、schema の `roleType` 識別子で財務諸表を切り出し、presentation linkbase で階層配置を instance の fact に対応づける **statement-level segmentation**。schema・linkbase・instance の元の XML 依存を保つ。

## 4. 主張・証拠・概念・期間・単位・値の対応付け

- **正解は DQC(Data Quality Committee)の誤りメッセージから決定論的に導く**(§3.2.1・§3.3.1)。DQC US rule が「曖昧さのないラベル」を与える。
- FinMR では **DQC メッセージが報告値と calculation linkbase が含意する正しい値の両方を含む**。対象概念と報告期間で入力質問を作る。
- 概念の対応は「filing 中のタグ ↔ 標準 US-GAAP 概念」の整合判定として扱う。**値の単位の照合は明示されていない**(未確認)。
- taxonomy の digitalization: 公式 taxonomy ファイル(GAAP Taxonomy 2024.xlsx)の Concepts・Presentation・Calculation・Definition・Reference・Enumeration シートを解析し、**core chunk**(label・type・balance・period type・documentation)と **relation chunk**(presentation 経路・親子 calculation 関係・definition arc・外部参照)の 2 種に分ける(§3.2.3)。

## 5. 決定論的処理と LLM が担う処理の境界

- **正解側**: DQC ルールが決定論。**GPT-4o-mini は「決定者ではなく高効率のパーサとしてのみ」使う**(§3.3.1 の明記: "We employ GPT-4o-mini solely as a high-efficiency parser, rather than a decision-maker")。DQC rule ID → 関係ラベルの対応も決定論(DQC_0081→Reversal、DQC_0001→CombinationErr、DQC_0145→Inappropriateness)。
- **評価対象側**: 3 タスクすべて LLM が解く。
- **ただし FinMR の accuracy は LLM-as-a-judge で測っている**(§3.1.3)。正解自体は決定論だが、**正解との一致判定に LLM が入る**。これは論文が §3.3.1 で立てた「LLM は決定者ではない」という線を、評価の側で一部越えている(**独自推論**)。

## 6. 保留・棄却・人手確認の条件

- モデル側の保留の仕組みは無い。FinMR は「見つからなければ 0」と答えさせる(プロンプトの指示)ので、**0 が「無い」と「見落とし」を区別しない**(独自推論)。
- 人手確認(§3.3.2 の 3 段):
  1. **Structural Verification**: 無作為 50 filing を手で検査し、切り出した statement が roleType と対応し階層を保つか確認。
  2. **Annotation Validation**: **全インスタンスの 50%** を二重検証(GPT-4o-mini 出力 vs 独立の人のレビュー)、不一致はすべて修正。
  3. **Referential Integrity**: relation chunk がすべて有効な core 概念を参照することを検証。

## 7. 評価データ・件数・比較対象・実験条件

**論文記載 §3.2–3.4**:
- DQC 誤りメッセージ **4,545 件 / 372 社 / 2020–2024** を XBRL US ポータルから収集(pre-screening)。
- 最頻の **9 誤り型**(全体の **60.33%** = 2,743 件)を選び、対応する **218 の XBRL filing** を EDGAR から取得(Table 2)。
  - 意味系: DQC_0099 (386)・DQC_0109 (217)・DQC_0137 (208)
  - 関係系: DQC_0081 (570)・DQC_0001 (313)・DQC_0145 (219)
  - 計算系: DQC_0126 (260)・DQC_0015 (368)・DQC_0117 (202)
- 注釈済みインスタンス **1,102 件**。平均 **34,338 トークン**、最大 65,030(Table 4)。FinSM 330 / FinRE 440 / FinMR 332。総 37,834,906 トークン。
- モデル 13: GPT-4o、DeepSeek-V3、Qwen3-235B-A22B-Instruct-2507、Llama-4-Scout-17B、Qwen2.5-72B、Llama-3.3-70B、Qwen3-32B、gemma-3-27b/12b、Llama-3.1-8B、Llama-3.2-3B、Fin-o1-14B、Fin-R1。
- 条件: **zero-shot**、LM Evaluation Harness、4×H200、**入力上限 81,920 トークン・生成上限 512 トークン**。

## 8. 報告された指標・結果とその適用範囲

| タスク | 最良モデル | 値 |
|---|---|---|
| FinSM Hit Rate@20 | DeepSeek-V3 | **12.42%**(全モデル **13% 未満**) |
| FinSM Macro-F1@20 | DeepSeek-V3 | 10.17% |
| FinRE Acc | **GPT-4o** | **91.82%**(Macro-F1 90.09) |
| FinRE 2 位 | DeepSeek-V3 | 82.73% |
| **FinMR Acc** | Fin-o1-14B | **13.86%** |

- FinSM: 「retrieval performance remains uniformly low across models, with no consistent advantage from larger parameter scales or domain-specific financial pretraining」。**Qwen3-32B と Fin-o1-14B は全指標 0.00**。誤りの質的分析: モデルは「表層の意味的類似に頼り、文脈上の妥当性と taxonomy が定める粒度を推論しない」。例: `Cash` のみ許される文脈で `CashAndCashEquivalentsAtCarryingValue` が報告されていても見逃す。
- FinRE: 関係型別では Reversal と Inappropriateness は上位モデルが扱えるが、**CombinationErr はほとんどのモデルが F1 ほぼ 0 に崩壊**(Figure 3)。axis–member の組み合わせの検証には複数 linkbase 横断の推論が要る。
- FinMR: **CER(計算誤り)が失敗の 70–83%** を占める。EER(抽出誤り)は 10–27%。「モデルは関連する財務の fact を同定できても、taxonomy に接地した計算関係を実行・検証できない」。Qwen3-32B と Fin-R1 は SER が極端に高い。**Fin-o1-14B は最良 accuracy かつ CER 9% だが SER 71%** ― 出力形式に従えないことが正答の表出を妨げている。

**適用範囲**: 米国 10-K/XBRL、2020–2024、DQC が検出した 9 誤り型のみ(DQC 全体の 60.33%)、zero-shot、長文脈。**FinMR の accuracy は LLM-as-a-judge 由来**。

## 9. 著者が明記した制約・失敗例

- **独自確認: Limitations 節は無い。** 本文に自分の研究の制約を節立てした箇所が無い("limitations" の語は §1 で**既存ベンチの限界**を指す形でのみ使われる)。
- 本文に書かれた失敗例は豊富(上記 §8)。
- **記載が無い(未確認)**: DQC の 9 型に絞ったことの偏り(残り 39.67% の誤り型が何か)、`roleType` 分割が取りこぼす誤り、LLM-as-a-judge の信頼性、Fin-o1-14B の SER 71% を抱えた「最良」の扱い方、GPT-4o-mini パーサの誤りが正解に残った可能性(50% 二重検証なので残り 50% は未検証)。

## 10. Audit Core との共通点・相違点

**共通点**
- 正解・判定の基準を**決定論的な規則**(DQC)に置き、LLM を「パーサ」に限る宣言。Audit Core の「判定に LLM を使わない」と同じ方向の線引き。
- FinMR の構造(報告値 vs calculation 関係からの計算値を両方出して比べる)は Audit Core の GROUNDED / VALUE_MISMATCH の判別と**ほぼ同形**。
- 複数文書・複数 linkbase 横断の整合という問題設定。

**相違点**
- FinAuditing は**ベンチマーク**。検証器を提案していない。測っているのは LLM の能力で、Audit Core は決定論的な照合器。
- 対象が「提出書類そのものの誤り」(発行者の誤タグ・誤関係)。Audit Core の対象は「AI が書いた主張の誤り」。**監査の向きが逆**。
- FinAuditing の正解は DQC が既に検出した誤り。Audit Core は検出する側。
- 日本 EDINET には DQC 相当の公開誤りメッセージ基盤が在るかを**本調査では確認していない**(未確認。重要な差になりうる)。

## 11. 現行設計に対する示唆(独自推論)

1. **「値 vs 計算関係から導いた値」の比較は、独立に 2 つの研究が中核に置いている**(FinAuditing の FinMR、VeriFin の Φ)。Audit Core の VALUE_MISMATCH はこの系列に属する。
2. **LLM にこの照合をさせると accuracy 13.86%**。CER が 70–83% を占めることは、「計算の実行を決定論に渡す」設計の根拠になる外部の数である。ただし**これは zero-shot の LLM の数で、Audit Core の実測ではない**。
3. **「報告値 ≠ 計算値」の検出には calculation linkbase が要る**。EDINET の調査で、S100Z4Q1 の cal.xml は **loc 186 / 異なり要素 144 / arc 176**(独自確認)。計算関係が存在することは確かめた。これを使う設計は技術的に可能だが、**本調査では提案に留める**。
4. **DQC 型の「外部の決定論的な誤り基盤」が日本に在るかは、Audit Core の将来の正解集合づくりに直接効く**。追加の証拠が必要な事項として `roadmap_impact.md` に記録した。
5. **「最良モデル」の扱いに注意**: Fin-o1-14B が最良 accuracy だが SER 71%。この種の数を営業資料で「LLM は 14% しかできない」と引くと、**SER(形式に従えない)と CER(計算を誤る)を混ぜた数**を引くことになる。引くなら「計算誤りが失敗の 70〜83%」の方が主張に対応している。

## 12. 根拠箇所

| 内容 | 箇所 |
|---|---|
| 3 つの既存ベンチの限界 | p.2 §1 |
| `f: (D,T) → E`・6 文書 | p.2–3 §3.1、Table 3 p.5 |
| FinSM/FinRE/FinMR の定義とプロンプト | p.3–4 §3.1.1–3.1.3 |
| DQC 4,545 件・9 型 60.33%・218 filing | p.4 §3.2.1、Table 2 p.5 |
| statement-level segmentation | p.4–5 §3.2.2 |
| taxonomy digitalization(core/relation chunk) | p.5 §3.2.3 |
| 1,102 インスタンス・34k トークン | Table 4 p.5 |
| GPT-4o-mini は「パーサであって決定者でない」 | p.5 §3.3.1 |
| 品質管理 3 段(50 filing・50% 二重検証) | p.5 §3.3.2 |
| モデル一覧・81,920 トークン上限 | p.5–6 §3.4 |
| FinSM 結果 | Table 5 p.5–6、§4.1 p.6 |
| FinRE 結果・CombinationErr の崩壊 | Table 6 p.6、Figure 3、§4.2 |
| FinMR 13.86%・CER 70–83% | Figure 4、§4.3 p.6 |
