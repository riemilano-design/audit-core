# 読解記録 5: VERITYGATE

**読解状況: 原文全文を読んだ**(PDF 16 ページ・抽出 66,508 字、空白ページ 0、**画像 0** ― 図は全てベクタ/テキストなので図中の文字も抽出できている)。
Appendix A〜E まで含む。

## 1. 書誌情報・公開日・バージョン

| 項目 | 値 | 区分 |
|---|---|---|
| 題 | VERITYGATE: A Four-Gate Schema-Level Faithfulness Framework and Paired Benchmark for Grounded LLM Narrations over Structured Evidence | 論文記載 |
| 著者 | Sachin Gupta(Independent Researcher, San Jose) | 論文記載 p.1 |
| arXiv | 2610.00833v1 [cs.CL]、**Submitted 30 Sep 2026** | arXiv abs |
| 採録 | **GroundLM 2026(EMNLP 2026 併設ワークショップ)採録** | 論文記載 p.1 脚注 |
| 公開物 | コード `github.com/sachinkg12/yukti`(タグ `veritygate-groundlm-2026-v1.0.0`)、補足 artifact Zenodo DOI `10.5281/zenodo.22668710`。**本調査では取得していない(未確認)** | arXiv abs から独自確認 |
| ファイル | `papers/p5_veritygate_2610.00833v1.pdf` sha256 `d5cf382c…` | 独自確認 |

**取得経路の記録**: researchgate は指示どおり試さず、arXiv API のタイトル検索(`all:VERITYGATE`、totalResults=1)で同定。

## 2. 研究目的・解こうとしている問題

**論文記載 p.1**: 「決定論的バックエンド(ソルバ・ルールエンジン・モデル)が答えを計算し、LLM が説明を書く」という 2 段構成が増えている。この構成で、**完全な証拠グラフを渡しても LLM は捏造する** ― 存在しないカードを引用し、意味を変える丸めをし、符号を反転し、もっともらしい事実を作る。
実害の引用: Moffatt v. Air Canada (2024 BCCRT 149)、NYC MyCity chatbot (2024-03)、法律事務所 3 名の制裁(2025-02、引用 9 件中 8 件が AI 捏造)、AI 捏造申立の判例データベース 1,400 件超(2026 年半ば時点)。

既存防御が足りない理由(p.1): 安全性アラインメントは「渡したデータだけを引用せよ」に対して訓練されていない。Outlines/JSON schema mode のような制約デコーディングは**構文**を強制するが外部バックエンドに対する**意味**の正しさを検査しない。LLM-as-judge は位置バイアスを示す(**この研究の judge は 83% の呼び出しでスロット A を選んだ**)。

## 3. システム構成と処理フロー

**論文記載 §3、3 段**:

1. **Stage 1: Evidence Graph Construction** ― バックエンド出力から証拠グラフを構築。各証拠ブロックがノード、論理的に関係するノード間に辺。グラフは 2 つの allowlist を持つ: **allowed entities**(バックエンド出力に現れる全 entity 文字列)と **allowed numbers**(各証拠ノードの構造化フィールドに現れる全数値 + 小整数 allowlist 0,1,2,3)。グラフは**正規形の SHA-256 ダイジェストを持ち、同じバックエンド出力に対する 2 回の実行は同じダイジェストを生む**(決定論性と監査可能性)。
2. **Stage 2: Four-Gate Verification** ― 語り手 LLM を strict JSON で呼び、prose と並行して `citedEvidenceIds` / `citedEntities` / `citedNumbers` を宣言した claim オブジェクトの配列を出させる。4 門はこの**宣言された構造化フィールド**をグラフに対して検査する。**「The check is purely structural: no LLM is involved.」** 1 門でも落ちれば claim を棄却。**棄却は流暢さと独立**。
3. **Stage 3: Repair Loop and Permissive Emission** ― 落ちた claim があれば、元の文脈 + 具体的な検証器の誤りを添えて 1 回だけ再プロンプト。初回と修復後のうち**落ちた claim が少ない方**を採る。最終出力は**検証を通った claim の部分集合だけ**(permissive emission: 通ったものを出し、落ちたものは捨てる)。**「the underlying LLM continues to fabricate; claim-survival measures what passes verification (what the user sees), not generator improvement.」**

## 4. 主張・証拠・概念・期間・単位・値の対応付け ― 4 門

| 門 | 検査するもの | 検出 | 実測の誤り幅(grounded・150 インスタンス/セル) |
|---|---|---|---|
| **Gate 1 Evidence Existence** | 引用した証拠 ID がグラフに在るか | **集合所属** | r=0: 1–6 / r=1: 0–4 |
| **Gate 2 Entity Allowlisting** | 引用した entity が allowed set に在るか | **集合所属** | r=0: 0–47 / r=1: 0–43 |
| **Gate 3 Number Binding** | 引用した数値**文字列**が allowed set に在るか | **完全文字列一致** | r=0: 0–388 / r=1: 1–97 |
| **Gate 4 Claim-Type Rules** | claim 型が要求する型の証拠を引用しているか | 型規則検査 | r=0: 885–985 / r=1: 652–841 |

- Gate 4 の例: comparison claim は winner-by-category の証拠ノードを、fee-justification claim は fee-break-even ノードを、cap-switch claim は cap-hit 証拠(そのノード型がグラフに在るときは cap-hit と allocation-segment の両方)を引用しなければならない。
- Gate 3 は **`2400.0` と `2400.00` の不一致を含む**(論文の明記)。小整数(0–3)は慣例で許す。
- **期間・単位の照合は門に無い**(この領域(クレジットカード最適化)に期間の概念が無いため)。Audit Core / VeriFin との構造差。

**最重要の限定(論文 §3.2 の明記)**:
> 「the guarantee is **schema-level structural correctness, not prose-level faithfulness**: an under-citing LLM can mention unverified entities or numbers in prose that the verifier never inspects (Appendix A).」

## 5. 決定論的処理と LLM が担う処理の境界

- 決定論: 証拠グラフ構築、4 門すべて、permissive emission のフィルタ。**「no LLM is involved」**(§3.2)。SHA-256 ダイジェストで再現性を担保。
- LLM: prose と claim 宣言の生成、修復パスでの再生成。
- **境界が明快で、Audit Core の「判定に LLM を使わない」と最も近い**。ただし **LLM が自分の引用を宣言する**(自己申告)ところが要。宣言が空なら門は何も検査できない(§9 の失敗例参照)。

## 6. 保留・棄却・人手確認の条件

- 保留に相当するのは **permissive emission**: 落ちた claim は**ユーザに見せない**(「The user never sees a failing claim」)。VeriFin の abstain(判定を返さない)とは違い、**出力を削る**形。
- 修復は 1 パス。Sonnet の 2 パス目は ∆ = +0.77 pts [−1.22, +2.81](CI がゼロを跨ぐ)なので r=1 で運用。
- 人手確認: **Appendix A の外部 rater 研究**(3 名 × 25 項目)。これは正解の再導出ではなく「同じ allowlist を見た人間が検証器の受理/棄却に同意するか」を測るもの(論文の明記)。
- **Ethical Considerations に運用上の義務が書かれている**: 「A "verified" label…does not warrant that the prose shown to the user is faithful in full… **Deployments must surface this scope to end users (e.g., via product copy and/or audit logs) and must not present the label as a guarantee of complete factual accuracy.**」

## 7. 評価データ・件数・比較対象・実験条件

- 事例研究: **クレジットカードのポートフォリオ最適化**。バックエンドは MILP(1–3 枚の最適ポートフォリオを計算)。6 つの task-facing 証拠型(cap-hit, winner-by-category, allocation-segment, fee-break-even, earn-rate, assumption)+ 4 つの support/container 型。
- バックエンドは別途 **米国 BLS 公開マイクロデータの実世界 1,000 世帯**で検証済み(25 調査波に対し Spearman ρ = 0.896)。**この検証は本論文では再導出していない**(論文の明記)。
- ベンチ: **50 のパラメトリック profile × 3 goal = 150 (profile, goal) インスタンス**、固定 seed 42、cap 境界事例を含むよう層化。r=0 と r=1 のそれぞれで 150 × 3 語り手 × 2 変種 = **900 インスタンス**、**450 の grounded–ungrounded 対**。Sonnet のみ r=2 で 300 追加。公開結果レコードは **16,180 の parsed-and-retained claim オブジェクト**。
- 語り手 3: GPT-4O-MINI-2024-07-18、LLAMA-3.3-70B-INSTRUCT-TURBO(Together AI)、CLAUDE SONNET 4.6。judge は GPT-4O-2024-08-06。全 API 呼び出しは temperature 0.0・プロバイダ側キャッシュなし、**2026-03-01〜2026-05-14** に実施。
- 変種: **Grounded**(完全な構造化証拠 + allowed entity/number リストをプロンプトに含む)vs **Ungrounded**(goal 名・カード一覧・top-line の内訳だけ)。
- 統計: インスタンス単位のクラスタブートストラップ、10,000 反復、seed 42。**共主指標 2 本を事前登録**(Appendix E)。
- **比較対象としないもの**: no-defense(全出し)baseline は実行していない(r=0 の survival の補数がユーザに見える失敗率を定量する)。**LLM-as-judge をフィルタの baseline として評価していない**(judge が ungrounded を好み 83% でスロット A を選ぶため)。

## 8. 報告された指標・結果とその適用範囲

| モデル | 変種 | survival r=0 | survival r=1 | shipped/inst r=0 | r=1 | Evid. | Ent. | Num. | Type |
|---|---|---|---|---|---|---|---|---|---|
| GPT-4O-MINI | Grounded | 19.7% | 28.0% | 1.60 | 1.74 | 4 | 43 | 97 | 652 |
| GPT-4O-MINI | Ungrounded | 26.1% | 25.6% | 1.29 | 1.31 | 4 | 27 | 263 | 486 |
| LLAMA-3.3-70B | Grounded | 40.1% | 41.3% | 4.29 | 3.58 | 0 | 3 | 84 | 753 |
| CLAUDE SONNET 4.6 | Grounded | 52.1% | 54.3% | 7.15 | 6.67 | 0 | 0 | 1 | 841 |

(Sonnet の r=0/r=1 の survival と shipped は Abstract と §4.2 の本文から。Table 2 の抽出は段組が途中で切れている。)

- **この構造的契約の下では、修復前に mini の claim の 80.3%、Sonnet の 47.9% が落ちる。これらは「検証器の棄却率であって、prose の hallucination 率ではない」**(Abstract の明記)。
- 修復 1 パスで survival は mini 19.7%→28.0%、Sonnet 52.1%→54.3%。
- **shipped verified claims は mini +0.14、Llama −0.71、Sonnet −0.47**。「survival と出力量は一緒に報告しなければならない」。capable なモデルは修復で保守的になり、裏づけられない claim を**捨てる**。
- モデル間の順序は CI が重ならない: Sonnet − mini = +26.4 pts [+22.6, +30.1]、Llama − mini = +13.3 [+9.2, +17.4]、Sonnet − Llama = +13.0 [+10.3, +15.7]。
- **率と量の逆転**: mini の r=0 で ungrounded の survival (26.1%) が grounded (19.7%) より高いが、shipped は 1.29 対 1.60。証拠グラフが無いとモデルは短く安全な語りを作り、個々の claim は門を落ちにくいが**ユーザが受け取る検証可能な内容は減る**。
- **Gate 4 が残余の支配的失敗**: r=1 で mini 652/672 (97.0%)、Llama 753/763 (98.7%)、**Sonnet 841/841 (100%)** の異なり失敗 claim が Gate 4 違反。Sonnet では Gates 1–3 がほぼ消える(証拠誤り 0・entity 誤り 0・数値誤り 1 / 150 インスタンス)。

**適用範囲**: 単一領域(クレジットカード最適化 + MILP)、3 モデル、単一 seed、非敵対的な脅威モデル。

## 9. 著者が明記した制約・失敗例

**Limitations 節(7 項目)**:
1. 3 モデルのみ。パターン(修復は小モデルに最も効き、Gate 4 が全層で支配)も絶対値も再現が必要。
2. **単一 seed (42)**。シード頑健性は評価していない。
3. rater 研究は小標本(3 名 × 25 項目、Gates 1–3 用と Gate 4 用で別々)。
4. judge は単一モデル(GPT-4O)。二次指標として扱い、faithfulness 指標ではないと明示タグ。
5. **敵対的頑健性は未評価**。「The verifier is sound against non-adversarial LLM hallucination, but **a model that knows the allowlist could craft outputs that pass verification while remaining semantically misleading.**」脅威モデルは意図しない捏造。
6. **単一応用領域**。医療意思決定支援・融資リスク評価への写像は §5 でスケッチしたのみで**実証していない**。
7. 決定論的な証拠グラフのテンプレートとの比較、Gate 4 の厳格/緩和の ablation、NLI/RAGAS/ALCE スコアラでの採点は**やっていない**。「The results therefore establish the behavior of the proposed structural audit-and-filter contract, **not superiority over template generation** or complementarity to neural faithfulness metrics.」

**Ethical Considerations にもう 1 つ**: 「Risk of false assurance from partial verification」。

**Appendix A の失敗例(Audit Core に直接効く 2 件)**:
- **false reject 方向(4 件)**: 3 名の rater 全員が prose の値を受理したのに検証器が棄却。主因は `2400.0` と `2400.00` が完全一致しないこと。→ 「exact-string canonicalization limitation」。
- **false accept 方向(1 件)**: 3 名全員が NO としたのに検証器は YES。「The claim's prose mentioned a phrase not in the allowed-entity list ("general purchases"), but **the LLM emitted empty cited fields and the verifier had nothing to check.**」
- 一致統計(Table 4): rater 間の平均一致 74%、Fleiss' κ = 0.48、pairwise Cohen's κ 0.35–0.70。**rater 対検証器の κ は 0.00–0.30、多数決対検証器の κ は 0.02**。
- 論文の解釈: 「We interpret these numbers as **supporting, not undermining**, the case for mechanical verification: human raters disagree both with each other and (more sharply) with the verifier, while the verifier is reproducibly self-consistent across runs.」
- **独自推論による別の読み**: κ ≒ 0 は「検証器が人間の言う『接地している』とは**別のもの**を測っている」とも読める。論文自身が 5 件(4+1)で多数決とのずれの大半を説明しており、どちらの読みも同じ事実から立つ。Audit Core にとっては「門の一致率を『正しさの一致率』として売らない」という歯止めの根拠になる。

## 10. Audit Core との共通点・相違点

**共通点(5 本の中で最も近い)**
- 決定論的な門だけで判定し、LLM を判定に入れない。
- 判定不能/不適合を隠さず、ユーザに出さない(permissive emission ↔ UNVERIFIABLE を隠さない)。
- 証拠を型つきで持ち、claim ごとに引用を要求する。
- **グラフの SHA-256 ダイジェストで再現性を担保**。Audit Core の封・sha256 と同じ発想。
- 事前登録(共主指標・ペアリング単位・統計・明示的な non-claim)。Audit Core の「予測を先に書く」と同形。

**相違点**
- VERITYGATE は **LLM 自身に引用を宣言させる**(自己申告の検証)。Audit Core は正規表現で機械が数の主張を抜く経路も持つ(`判定に LLM を使わない` の実装が 2 系統ある)。
- VERITYGATE の対象は MILP の出力の語り。Audit Core の対象は EDINET の fact。期間・単位・エンティティの照合が Audit Core にはあり、VERITYGATE には無い。
- VERITYGATE は**落ちた claim を出力から削る**。Audit Core は 4 状態のラベルを付けて**残す**。監査証跡としては Audit Core の方が情報を保つ(**独自推論**)。
- 状態数: VERITYGATE は通る/落ちる の 2 値(+ 門ごとの誤り理由)。Audit Core は 4 状態。

## 11. 現行設計に対する示唆(独自推論)

1. **「空の申告は門をすり抜ける」**(Appendix A の 1 件)。Audit Core でも「数の主張として抜けなかった行」は照合されない。VERITYGATE はこれを論文の限界として明記した。Audit Core の既知の型(門が審査していない文が送られる)と同じ穴で、**外部の独立な観測として記録する価値がある**。
2. **完全文字列一致は false reject を作る**(`2400.0` vs `2400.00`)。Audit Core は許容差(`tol_of`)を持つのでこの穴は同じ形では出ないが、**正規化を両側に掛ける**という既知の型と同じ領域。
3. **「verified ラベルを完全な事実正確性の保証として提示してはならない」という運用義務を、論文が倫理節に書いている。** これは Audit Core の営業表現に直接対応する(`sales_language_risks.md` に反映)。
4. **敵対的頑健性は未評価であることを論文が明記**。allowlist を知るモデルは門を通る誤誘導を作れる。Audit Core も同じ性質を持つ(照合は「証拠に在る数か」を見るが「その数を引いたことが適切か」は見ない)。
5. **率と量を一緒に報告せよ**という方法論の教訓。Audit Core で「GROUNDED 率が上がった」を単独で見せると、同じ逆転(安全だが中身が減る)を見落とす。
6. **「門は 4 つ」という構造が、Audit Core の 4 状態と偶然に近い形で揃っている**が、意味は違う。VERITYGATE の 4 は**検査の種類**、Audit Core の 4 は**結果の分類**。混同しないよう比較表で分けた。

## 12. 根拠箇所

| 内容 | 箇所 |
|---|---|
| 問題設定・実害の引用 | p.1 §1 |
| 4 門の定義と実測の誤り幅 | p.2–4 §2、Table 1 p.4 |
| 通過/棄却のトレース例 | Figure 1 p.3 |
| 3 段構成・SHA-256 ダイジェスト | p.4 §3.1–3.2、Figure 2 p.5 |
| **schema-level であって prose-level でない** | p.4 §3.2 |
| permissive emission・生成器は改善しない | p.4–5 §3.3 |
| 事例研究・ベンチ構成・事前登録 | p.4–5 §4.1 |
| LLM-as-judge をフィルタ baseline としない理由 | p.5 §4.1 |
| 主結果 | Table 2 p.7、§4.2 p.6、Figure 3 p.6 |
| Gate 4 の支配 | Figure 4 p.6、§4.2 |
| 率と量の逆転 | p.6 §4.2 |
| 偽の安心のリスク(運用義務) | p.9 Ethical Considerations |
| Limitations 7 項目 | p.9 Limitations |
| rater 研究・κ・2 方向の失敗例 | p.11–12 Appendix A、Table 4 p.12 |
