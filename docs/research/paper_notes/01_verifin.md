# 読解記録 1: VeriFin

**読解状況: 原文全文を読んだ**(PDF 9 ページ・抽出 44,914 字、空白ページ 0、保存 `.txt` は再抽出と完全一致)。
図の中の文字(Figure 1・2・5)は画像で、テキスト抽出に含まれない。図の内容は本文とキャプションから読める範囲に限る。

## 1. 書誌情報・公開日・バージョン

| 項目 | 値 | 区分 |
|---|---|---|
| 題 | VeriFin: A Neurosymbolic Framework for Verifying LLM-Generated Financial Claims | 論文記載 |
| 著者 | Bethel Hall, Sachi Shome, William Eiers(Stevens Institute of Technology) | 論文記載 p.1 |
| arXiv | 2608.10213v1 [cs.CE]、**Submitted 10 Aug 2026**、単一版(改訂なし) | 論文記載 p.1 脚注 + arXiv abs |
| PDF 生成 | 2026-08-12(PDF メタデータ) | 独自確認 |
| 査読 | **確認できず**(会議・ジャーナル名の記載なし。arXiv comments は "9 pages" のみ) | 未確認 |
| ファイル | `papers/p1_verifin_2608.10213.pdf` sha256 `5d3f9f9b…` | 独自確認 |

## 2. 研究目的・解こうとしている問題

**論文記載 p.1-2**: 中心の問いは「LLM が出した固定の数値主張を、金融の業務が受け入れてよいか」(p.2 太字: "given a fixed numerical claim produced by an LLM, should a financial workflow accept it?")。
誤った数値主張を受け入れることを **false accept** と定義し(p.2)、これを制御対象の中心に置く。算術の再計算だけでは足りず、(a) 事実の接地、(b) 認可された計算の確立、(c) 候補値が両者から従うかの判定、の 3 つが必要と主張(Abstract)。

## 3. システム構成と処理フロー

**論文記載 p.3-4、5 構成要素**:

1. **Evidence Retriever** (§3.2): 文書 ID で候補を厳密に 1 文書へ限定(cross-filing contamination 防止)。必要な行項目 R を同定し拡張クエリ `q_i = [q || r_i || period || statement]` を作る。密ベクトル cos + 字句スコア S_lex(表の行ラベルの完全一致を加点)のハイブリッド、cross-encoder で再順位付け。
2. **Answer Generator** (§3.3): 候補主張 a を起草。**a は untrusted claim として扱い、検証に使う事実・リンクベース・ソルバ制約には影響を与えない**(論文の明記)。
3. **Verification Planner** (§3.4): LLM が q と E から検証計画 C = (M, F, R, u, ρ, S) を作る。**式の権限は非生成的な出所の厳格な階層**: q 中の明示的演算 → filing の calculation linkbase → curated metric registry → 開示文中の定義。どれも完全かつ一意でなければ **abstain**。
4. **Provenance Verifier** (§3.5): 各オペランド役について 4 性質(taxonomy concept・報告期間・単位・申告値)を独立に確立。
5. **Claim Verifier** (§3.6): Φ = ∧(x_i = m*_i) ∧ (v̂ = f(x)) ∧ (|v̂ − v_c| ≤ τ) を量化子なし実算術にコンパイルし Z3 で判定。

## 4. 主張・証拠・概念・期間・単位・値の対応付け

**論文記載 §3.5(p.3-4)。概念の解決は 3 段**:

| 段 | 入力 | 規則 | 値への依存 |
|---|---|---|---|
| 1 | calculation linkbase | 要求された小計の下の子概念が役に対応すれば直接束縛 | なし |
| 2 | curated concept registry | 正規化した財務概念 → 候補 taxonomy 要素(例 `us-gaap:AccountsPayableCurrent`) | なし(**value-blind**。申告値を filed value が上書きする) |
| 3 | symbolic label-matching heuristic | 行ラベルと概念ラベルをトークン化し、**行のトークンが概念ラベルの部分集合**のときだけ受理。同点は**余剰トークンが最少**のものを選ぶ | **あり** ― 論文 p.4: 「Only the heuristic third stage is guarded by a plausibility check against the extracted value」 |

- **期間と単位**: 概念だけでは fact は一意に定まらない。報告期間が問いと一致し、単位が期待する尺度と一致する fact にだけ束縛する。filing に概念が在っても必要な期間・単位の fact が無ければ**束縛しない**(p.3)。
- **値と来歴**: オペランド値は filed fact からのみ取る。registry 解決の概念は value-blind に束縛され、**filed value がモデルの抽出値を上書きする**。したがって構造的な取り違え(認可された方針が `NetIncomeLoss` を要求するのに `ProfitLoss` を束縛する等)は接地では濾されず、後段でソルバ制約違反として現れる(p.3-4)。
- **来歴の記録**: すべての束縛が concept・報告期間・単位・accession number・source fact identifier を記録する(p.4)。
- **式の来歴**: linkbase 由来の小計は発行者が宣言した子概念と arc weight w_i ∈ {−1,+1} から f(x) = Σ w_i x_i。linkbase が無ければ質問テンプレート・registry(脚注 2: **CFA Institute のカリキュラム教材から編んだ**)・filing 本文の明示的定義。

## 5. 決定論的処理と LLM が担う処理の境界

**論文記載 §3.1 p.3**: 「We leverage language models solely for semantic parsing and retrieval planning, while delegating arithmetic enforcement, context binding, and consistency checking to deterministic XBRL linkbases and an SMT solver.」

- LLM が担う: 候補答えの起草、検証計画(意味解析)、検索計画。
- 決定論が担う: 算術の強制、文脈の束縛、整合性検査。
- p.3: 「Crucially, the candidate claim never influences the authoritative filing facts or formulas used to check it.」
- p.4: 「The final solver decision is deterministic conditional on the grounded facts and authorized computation.」(**条件つきの決定論** ― 接地と認可が決まった後での決定論であることを論文自身が条件づけている)

→ **この境界が公開コードと一致するかは別ファイル `verifin_code_audit.md` に分けて記録した。一致を前提にしていない。**

## 6. 保留・棄却・人手確認の条件

**論文記載**:
- Verified = 制約系が充足可能、Violated = 充足不能、**Abstain** = 必要なオペランドか認可された式を確立できない、またはソルバが unknown を返す(§3.6 p.4)。
- abstain の発生箇所: 「Abstentions arise **before the solver is reached**, when a required operand cannot be grounded, or no source authorizes a formula, rather than from an inability to decide the generated constraints」(p.7)。評価した全事例で Z3 は unknown を返していない(p.7)。
- 棄却時は UNSAT core が、矛盾する filing・式・主張の制約の部分集合を名前つきで示す。主張の境界からは過大申告か過小申告かも分かる(p.4)。
- abstain 時は「確立できなかった要件そのもの」を返す(p.4)。
- **人手確認の条件は論文に記載がない**(未確認)。abstain を人が見る運用の記述なし。修復は LLM に戻す自動化のみ。

## 7. 評価データ・件数・比較対象・実験条件

**論文記載 §4(p.4-6)**:

- **XBRLFiling**(新規): EDGAR の 10-K 提出 **86 件 / 28 社**(Apple・Microsoft・Amazon・Nvidia・Exxon Mobil を含む)、会計年度 **2021–2026**。calculation linkbase が宣言する小計 **15 種**を的に固定し、`p = Σ w_i c_i` を正解として記録してから質問を生成(逆向き構成)。**600 問**(内訳 Table 1 p.5: Income 5 metrics/226 問、Balance 7/279、Cash flow 3/95)。証拠は的の年と前 2 年の 3 列。的のセルのみ `[redacted]`、隣の前年値は「もっともらしいが誤り」の候補として残す。
  - 独自確認: 公開データ `data/multicompany_provable/data/provable_calcrequired.jsonl` は 600 行・company 28・doc_name 86 で一致。
- **FinanceBench**: 公開ベンチの数値部分 **67 問**(独自確認: `data/numerical_questions.jsonl` 67 行)。
- **答えモデル 6 種**: GPT-5.5、Claude Haiku-4.5、Qwen3-30B、Llama-3.1-8B、Qwen2.5-7B、Fin-o1-8B。温度 0・応答上限 2048 トークン。open-weight は vLLM。
- **比較対象(同一候補プール)**: Direct LLM(無検証)、LLM judge、Judge+formula(VeriFin が使う式と接地済みオペランドを judge に与える)、Program-of-Thought。検証の backbone は全て Claude Haiku 4.5。
- **実験条件の肝**: 候補生成は Claude Haiku 4.5 で**一度だけ**行い、同じ候補答えを全手法が使い回す。したがって差は検証法の差を反映する(p.4)。
- **許容差**: VeriFin は τ = 開示された精度の最終桁の半単位(百万単位なら 0.5 百万、1 桁%なら 0.05pt)。ベースラインは `|y − ŷ| ≤ max(0.01|ŷ|, 1.0)`(**両者で許容差の定義が違う**)。
- **指標**: FA 件数、accepted claim precision TA/(TA+FA)、accuracy (TA+TR)/(TA+FA+TR+FR)、abstention Abs/n、coverage 1 − Abs/n。

## 8. 報告された指標・結果とその適用範囲

**論文記載(Figure 4 p.6、Table 2 p.8、§5)**:

| 手法 | XBRLFiling (n=600) FA | precision | accuracy | abstention |
|---|---|---|---|---|
| Direct LLM | 92 | 84.7 | 84.7 | 0 |
| LLM judge | 26 | 88.2 | 43.5 | 0 |
| Judge+formula | 75 | 86.5 | 82.8 | 0 |
| PoT | 6 | 98.7 | 90.5 | 3.7 |
| **VeriFin** | **0** | **100** | **92.2** | **1.2** |

- XBRLFiling: 600 候補のうち 92 が誤り。VeriFin は 593 問で決定を返し、正しい主張 455 を受理・正しい主張 46 を棄却・**誤った 92 を全て棄却**・7 問で abstain。coverage 98.8%。
- FinanceBench (n=67): 決定 54 問、正 28 受理・正 9 棄却・誤 17 棄却、abstain 13。precision 100、accuracy 83.3、**coverage 80.6%**。67 件のうち 4 件は生成出力に有効な数値主張が無く検証前に abstain。検証可能な 63 件に対する abstain 率は 14.3%。
- 6 モデル × 2 データの 12 設定すべてで FA 0・precision 100。XBRLFiling の coverage 97.3–100.0%、**FinanceBench は 49.3–82.1%**。
- 残るコスト: 「正しい主張の保守的な扱い」。モデルによって **正しい主張 37〜73 件を棄却**(p.7)。
- 修復: UNSAT core を使った誘導修復で pass@1 は Qwen3-30B 6.5%→46.3%、Fin-o1-8B 26.1%→57.0%、Haiku 23.1%→40.5%。pass@3 最大 69.9%(Fin-o1-8B/XBRLFiling)。FinanceBench では Fin-o1-8B は pass@1 で 0.0%。
- 速度・費用: 1 問あたり LLM 呼び出し 4〜6 回・12k〜17k トークン・平均 3〜9 秒。Z3 は中央値 5ms(全処理の 0.2% 未満)。

**適用範囲の限定(論文自身の言葉)**:
- 「zero **observed** false accepts **in our evaluations**」(Abstract・§6)と、観測であって保証ではない書き方を一貫して使っている。
- XBRLFiling は「calculation linkbase が宣言した計算」から逆向きに作られている。FinanceBench は「XBRL calculation-linkbase relationships から構成されていない、より広い計算の集合」で、そこでは coverage が落ちる(p.7)。
- 「whenever VeriFin establishes the required computation, none of the incorrect candidate claims in our evaluations are accepted」(p.7)— **必要な計算を確立できたときに限る**条件つきの主張。

## 9. 著者が明記した制約・失敗例

- **独自確認: この論文に Limitations 節は無い。** 本文中の "limitation" という語の出現は **0 回**(抽出テキストで機械的に確認)。制約は §5 の本文に散在する形でしか書かれていない。
- 本文に書かれた制約: (a) coverage のコスト ― 正しい主張 37〜73 件の棄却、FinanceBench の coverage 49.3–82.1%、(b) 「Improving correct-claim retention without weakening false-accept control remains the main coverage challenge we will address in future work」(p.7)。
- 失敗例として挙げられたもの: Judge+Formula は VeriFin と同じ式を与えられても 92 件中 75 件の誤りを受理 → 「providing financial context during prompting as linguistic context is not equivalent to enforcing it」(p.7)。PoT は残り 6 件を受理 → 実行可能な算術だけでは意図した財務仕様への適合を保証しない(p.7)。
- **記載が無い(未確認)**: label-matching heuristic の誤り率、registry(CFA 教材由来)の件数・構成・誤りの可能性、retriever の失敗が abstain にどう寄与するか、LLM が検証計画を誤って作った場合の挙動、SMT 生成の忠実性。

## 10. Audit Core との共通点・相違点

**共通点(論文記載 vs Audit Core 実測の対比ではなく、設計原則の対比)**

| 点 | VeriFin(論文記載) | Audit Core |
|---|---|---|
| 主張と判定の分離 | 候補主張は untrusted、判定に影響しない | 判定は主張の値にも AI の提案にも依存しない |
| 保留の明示 | Abstain を「明示的な財務統制の決定」と位置づける | UNVERIFIABLE を隠さない |
| 判定の決定論 | 接地と認可が決まった後は Z3 で決定論 | 4 状態への決定論的照合 |
| 証拠の再取得 | filed XBRL fact から値を取る(抽出値を上書き) | 元データへ再照合 |
| 来歴の記録 | concept・期間・単位・accession・fact id | 証拠ポインタ |

**相違点**

| 点 | VeriFin | Audit Core |
|---|---|---|
| 判定器 | SMT ソルバ(Z3)。制約充足で判定 | 契約(比べ方)による照合。ソルバを使わない |
| 状態数 | 3(Verified / Violated / Abstain) | 4(GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND / UNVERIFIABLE) |
| 検証計画の作成者 | **LLM**(Verification Planner) | 機械(契約)。**ここが最大の設計差** |
| 式の出どころ | 4 つの非生成的出所の階層 | 契約に書かれた比べ方 |
| 行動の提示 | 修復のため LLM に戻す | 人が承認した表(条件→行動)から選ぶ |
| 対象 | 数値 QA の 1 主張 | 文書中の複数 Claim |
| 言語・制度 | 米国 US-GAAP / EDGAR | 日本 EDINET |

## 11. 現行設計に対する示唆(独自推論)

1. **「主張値が判定に影響しない」という原則は、独立に同じ結論へ到達した設計がある**。VeriFin はこれを「false verifications の源」と呼び、同じ理由で値による曖昧性解消を避けている。Audit Core の原則は孤立した選択ではない。
2. **保留と被覆の交換は避けられない**。VeriFin は「構成上証明可能」なベンチで coverage 98.8%、そうでないベンチで 80.6%(検証可能分に対する abstain 14.3%)。Audit Core が被覆を上げようとすると同じ壁に当たる。被覆の数は**ベンチの作り方に強く依存する**ので、他方式の coverage と自分の数を並べてはいけない。
3. **LLM に検証計画を作らせる設計は、Audit Core が現在置いていない点**。論文は「式の権限を非生成的な出所の階層に限る」ことで歯止めを掛けている。将来 Audit Core が構造化候補を AI に出させるなら、この「出所の階層 + どれも一意でなければ保留」の形が参照になる。ただし**採用・実装・実験は本調査の範囲外**。
4. **「正しい主張の棄却」(FR)が最大の実コスト**。VeriFin は 600 問で 37〜73 件。Audit Core も VALUE_MISMATCH の誤検出を測る必要がある(現在の測り方は未確認)。
5. **文脈に式を与えるだけでは強制にならない**という結果(Judge+Formula が 75/92 を受理)は、「LLM に根拠を持たせれば十分では」という想定問答への外部の証拠になる。ただし**これは VeriFin のベンチでの数で、Audit Core の実測ではない**。

## 12. 根拠箇所

| 内容 | 箇所 |
|---|---|
| 中心の問い・false accept の定義 | p.2 §1 |
| 5 構成要素 | p.3 §3.2–§3.6 |
| LLM と決定論の境界 | p.3 §3.1 |
| 概念解決 3 段・label matching | p.3 §3.5 |
| 値ブラインド束縛・heuristic 段の plausibility check | p.3–4 §3.5 |
| 式の権限の階層・abstain | p.3 §3.4、p.4 §3.5 |
| Φ と τ の定義 | p.4 §3.6 |
| XBRLFiling 構成 | p.4–5 §4.1、Table 1 p.5 |
| ベースライン・許容差 | p.5 §4.2 |
| 主結果 | Figure 4 p.6、§5.1 p.7 |
| モデル横断 | Table 2 p.8、§5.2 p.7 |
| 修復 | Table 3 p.8、§5.3 p.7 |
| 公開コードの脚注 | p.2 脚注 1 |
| registry の出どころ | p.4 脚注 2 |
