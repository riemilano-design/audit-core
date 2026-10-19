# ベストミックス研究・第 2 段階の追加調査(R1〜R4)― 結果と判断への影響

作成: 2026-10-13(「将棋コーチ|ベストミックス研究・第2段階」セッション。人間の「任せる・どんどん進めて」を受けて、[best_mix_design_review.md](best_mix_design_review.md) §6.3 の追加調査 R1〜R4 を実施)
性格: **調査のみ**。コード・実験・封・Golden・既存成果物の変更 0。LLM 呼び出し 0。公開コードは**読むだけで実行していない**(VeriFin の `results/*.jsonl` は自前の 30 行の python で読み、VeriFin の採点スクリプトは実行していない)。
区分の記法は本体 §0.1 と同じ: **[論文]** 論文の主張 / **[公開コード]** 公開実装で確認した事実 / **[公開結果]** 公開リポジトリの結果ファイルを自前で集計した数 / **[AC 実測]** Audit Core の実測 / **[推論]** 今回の推論 / **[仮説]** 未検証。

---

## 0. 先に結論(何が決まり、何が決まらないか)

| # | 追加調査 | 結果の一行 | 本体の判断への影響 |
|---|---|---|---|
| R1 | VeriFin 公開結果の first-pass 再集計 | **UNSAT 再抽出(V8)が VERIFIED を救ったのは 3,268 行中 3 行**(全部正解)。3 件とも「単位 ×1/1000」「符号反転」で fact が主張値の側へ動いた | **J7(再試行を作らない)の代償 ≈ 0、機構の実在は確認** → J7 を上げる |
| R1' | 同・`repair` 経路(本体未記載の新しい AI 経路 V14) | 検証器の fact と式を渡して LLM に答えを作り直させる経路が最新 run に在る。**答えが Z3 を通っても見出しの状態は VIOLATED のまま**(保守的)。通った答えを gold と比べると **XBRLFiling 217/217 正解、FinanceBench 8 件中 6 件が誤り** | **E2(根拠の層の誤受理)が VeriFin 自身のデータにも在る**ことの外部証拠。「契約が機械由来か LLM 自己申告か」で根拠の層の誤りが変わる(§1.4) |
| R1'' | 同・`formula_source` の実分布 | XBRLFiling は 600 行中 592〜600 行が `xbrl_linkbase`(機械認可)、FinanceBench は 0 行。FinanceBench の VERIFIED は `policy_registry` と `document_derived`(全 run 合計 3 行) | 本体 V3「linkbase 認可は FinanceBench で走らない」を**数で確認**。VeriFin の 2 ベンチは「契約の出所が違う 2 つの体制」として読むべき |
| R2 | VERITYGATE 公開コード | 4 門は**集合所属の決定論**(コード確認)。ただし門が見るのは **LLM が申告した `citedNumbers` 等の配列**であり、顧客に見える文(`text` / `normalizedFields`)は検査しない。これは**論文自身が明記**している限界 | **U5 解消**(決定論)。J8(自己申告を信じない)の外部事例が 2 件目。J6(空の宣言)はコードで経路を特定 |
| R3 | FinTagging v5 | v4 と**小数の数 385 個が完全一致**(差は組版・所属のみ) | **J5 に変更なし** |
| R4 | 日本に DQC 相当の決定論的誤り判定基盤が在るか | 金融庁の EDINET バリデーションは 206 コード(ERROR 114 / WARNING 92)。計算リンクの合計不一致は **WARNING(EC5611W)**。期間跨ぎの値の比較・要素選択の意味的検査は**無い**。官製の DQC 相当は**見つからず**(第三者の EDINET DB に 10 本の整合性検査があるが、誤りデータの公開は無い) | **J9 の「正解集合」は自前で作るしかない**(現状どおり)。計算リンクは「値に依存しない追加の証拠」になりうる(§4.2 [推論])が、VeriFin の FR がその過剰棄却の危険を示す |

**決まらなかったこと(実験でしか答えられない)**: 本体 §6.4 の 1〜7 は変わらない。R1〜R4 はいずれも「外部の数」であり、Audit Core の方式 C の E2 は 1 件も測れていない。

---

## 1. R1: VeriFin 公開結果の再集計 [公開結果]

### 1.1 方法と自己検算

- 材料: `docs/research/papers/verifin_code/results/`(クローン `5c49943`)の正準 12 run(XBRLFiling 6 × 600 行、FinanceBench 6 × 67 行 = 3,268 行)と `results/onepool/`(基準線)。読んだ欄: `status`・`claimed_value`・`gold_answer`・`diagnostics.first_pass_solver_status`・`diagnostics.unsat_fact_retries[]`(`facts`・`changed`・`computed_value_before/after`・`solver_status`)・`formula_source`・`failure_reason`・`repair{}`。
- 採点は `results/scoring_policy.json` の規則(`abs(abs(claimed) - abs(gold)) <= max(1.0, 0.01*abs(gold))`、gold の数字トークンのいずれか、`manual_adjudications.json` の 6 問は許容目標だけ)を自前で実装した。
- **自己検算**: 12 run すべてで TA/FA/TR/FR/AB が `results/paper_metrics.csv` と一致(例: XBRLFiling GPT-5.5 560/0/3/37/0、FinanceBench Haiku 28/0/17/9/13)。以下の数はこの採点器で出した。

### 1.2 first-pass と UNSAT 再抽出(V8)の寄与

| run | 行 | TA/FA/TR/FR/AB | first-pass UNSAT(=再抽出が走った行) | 再抽出で値が動いた行 | **VERIFIED になった行(= V8 の救済)** |
|---|---|---|---|---|---|
| XBRLFiling GPT-5.5 | 600 | 560/0/3/37/0 | 40 | 35 | **0** |
| XBRLFiling Haiku 4.5 | 600 | 455/0/92/46/7 | 138 | 37 | **0** |
| XBRLFiling Fin-o1 | 600 | 436/0/107/49/8 | 156 | 41 | **0** |
| XBRLFiling Qwen3-30B | 600 | 304/0/231/63/2 | 294 | 69 | **0** |
| XBRLFiling Llama-3.1-8B | 600 | 74/0/460/50/16 | 510 | 119 | **0** |
| XBRLFiling Qwen2.5-7B | 600 | 35/0/482/73/10 | 555 | 61 | **0** |
| FinanceBench Haiku 4.5 | 67 | 28/0/17/9/13 | 26 | 2 | **0** |
| FinanceBench Fin-o1 | 67 | 32/0/14/9/12 | 25 | 4 | **2**(両方 TA) |
| FinanceBench Qwen3-30B | 67 | 24/0/20/8/15 | 29 | 5 | **1**(TA) |
| FinanceBench Llama-3.1-8B | 67 | 10/0/17/12/28 | 29 | 1 | **0** |
| FinanceBench Qwen2.5-7B | 67 | 10/0/16/7/34 | 23 | 7 | **0** |
| FinanceBench Haiku(retrieved evidence) | 67 | 30/0/8/7/22 | 15 | 4 | **0** |

救済された 3 行の中身(`unsat_fact_retries[0]`):

| id | 式 | 再抽出前 → 後 | 主張値 | gold | 動き方 |
|---|---|---|---|---|---|
| `financebench_id_04171` | `accounts_payable` | 302,578 → 302.578 | 302.578 | $303.00 | **×1/1000(千 → 百万)** |
| `financebench_id_03282` | `total_current_liabilities` | 5,466,312 → 5,466.312 | 5,466.312 | $5,466.00 | ×1/1000 |
| `financebench_id_03029` | `capex` | 1,577 → −1,577 | −1,577 | $1,577.00 | **符号反転**(採点は絶対値) |

読み方 [推論]:
- V8 の**実利は 3/3,268 行(0.09%)**、FA への寄与は 0。本体 §6.1 J7「判定後に主張値を見せて候補を作り直す再試行を作らない」の**代償がほぼ無い**ことの外部証拠になる。
- 一方、3 件とも「主張値に合うように fact の単位・符号が動いた」形で、**本体 V8 で懸念した機構(再抽出が主張へ収束する)がそのまま観測された**。3 件は主張が正しかったので TA になったが、主張が誤っていて単位が主張側へ動く場合を止めるものは無い(今回のデータでは起きていない = 「起きない」ではない)。
- 「再抽出で値が動いた行」が多いのに VERIFIED に至らない(例: GPT-5.5 35/40)のは、UNSAT の原因が主張値ではないため(§1.3)。

### 1.3 「主張値 ≈ 計算値なのに UNSAT」の原因(XBRLFiling)

| run | VIOLATED | うち `claimed_value` と `computed_value` が**採点の許容(1%)内** | `repair.unsat_core` に主張の assertion(`claim_upper/lower`)を含む | 同・計算リンク(`xbrl_calc_`)を含む | 空 |
|---|---|---|---|---|---|
| GPT-5.5 | 40 | **39** | 0 | 0 | 40(core 未記録) |
| Fin-o1 | 156 | 48 | 144 | 3 | 9 |
| Qwen3-30B | 294 | 61 | 285 | 0 | 9 |
| FinanceBench Fin-o1 | 23 | 5 | 23 | 0 | 0 |

- 1 行は個別に原因を特定した: `mc_calc_00097`(主張 1,073 = 計算 1,073、gold $1,073 million、`failure_reason=claim_inconsistent_with_evidence`)の `smtlib` 末尾の UNSAT は **`xbrl_calc_…AccumulatedOtherComprehensiveIncomeLossNetOfTax` の計算リンク整合(子要素の和が親 ±2.5 以内)**で、主張の式とは無関係 [公開コード/公開結果]。
- 残りの原因は 2 つが混ざっていて、行ごとには**未確認**: (a) 計算リンク整合の破れ(上の 1 行の型。Fin-o1 で core に `xbrl_calc_` が 3 行)、(b) **検証器の許容差が採点の許容差より厳しい**(本体 V9 の `effective_tolerance_from_answer`。Fin-o1 48 行・Qwen3 61 行は 1% 内なのに core に主張の assertion が入る)。GPT-5.5 の 40 行は core が空で記録されていないため分類できない。

読み方 [推論]: VeriFin の XBRLFiling の FR(GPT-5.5 37、Haiku 46、…)には、(a) **正準データ自身の内部整合(計算リンク)の破れで主張ごと棄却する**決定論的な過剰棄却(本体の E3 に相当)と、(b) **判定の許容差と採点の許容差の不一致**が含まれる。(b) は「FR」の数が採点規則に依存することを意味し、本体 §4 で E3 の分母・許容差を固定条件に書いた理由そのもの。(a) は、方式 B の安全条件 b(契約を Core が持つ)を満たしても**契約に「正準データの整合」を含めると誤棄却が増える**ことを示す。R4 の EC5611W(EDINET では計算リンク不一致は WARNING)と合わせ、計算リンクを「門」にするか「追加の証拠」にするかは別の設計判断になる(§4.2)。

### 1.4 `repair` 経路(本体未記載。V14 として追加) [公開コード/公開結果]

最新 run(`results/latest/*`)の行には `repair` 辞書が在る(`repair_mode = "dedicated_unsat_core_feedback_same_verifier_side_channel"`)。中身は、UNSAT のとき **検証器が束縛した fact と式を LLM に渡し、「前の答えは失敗した。これらの fact だけで計算し直せ」と答えを再生成させ、再生成した答えを同じ検証器で再検証**する経路。`src/verifiqa/pipeline.py` 743 行付近の `REPAIRED_VERIFIED` とは別物で、見出しの `status` は **VIOLATED のまま**(repair が SAT でも TA に数えない。保守的)。

| run | repair 行 | 再生成が SAT(通った) | うち gold と一致 | うち gold と不一致 | 不一致のうち元の主張が正しかった |
|---|---|---|---|---|---|
| XBRLFiling Fin-o1 | 156 | 79 | **79** | 0 | 0 |
| XBRLFiling Qwen3-30B | 294 | 138 | **138** | 0 | 0 |
| XBRLFiling GPT-5.5 | 40 | 1 | 0 | **1**(`mc_calc_00117`: 元 141,450=gold、再生成 132,540) | 1 |
| FinanceBench Fin-o1 | 23 | 8 | 2 | **6**(`00394` 8,649→3,100、`01911` 7→1.61、`03620` 9,068→19,482 ほか) | 2 |

読み方 [推論]:
- 「再生成が SAT なのに gold と不一致」は、**検証器が持つ fact・式の側が誤っている(内部では整合している)**ことの直接の観測であり、本体 §0.3 の**根拠の層の誤り(E2)に相当する数が VeriFin 自身のデータに在る**。FinanceBench では **6/8**、XBRLFiling では **1/218**。
- 2 ベンチの差は契約の出所の差と一致する(§1.5): XBRLFiling は式が計算リンク由来(機械認可)、FinanceBench は式が LLM 申告の `policy_registry` / `document_derived` と抽出 fact 由来。**ただし XBRLFiling の設問は計算リンクから生成されている**(README)ので、同じ源で問いと答えを作った循環があり、0/217 を「機械認可なら誤らない」と読んではいけない [推論]。
- この経路は本体 §3.1 の方式 B の失敗経路「AI に Core の fact を見せて値を作り直させる」の実物。見出しに数えない運用は正しいが、**再生成した答えを製品の出力にしない**ことがコード上で保証されているかは**未確認**。

### 1.5 `formula_source` の実分布(本体 V2・V3 の数による確認)

| ベンチ | run | `xbrl_linkbase` | `policy_registry` | `document_derived` | `generic_operation` | `direct_lookup` | `no_formula`/空 |
|---|---|---|---|---|---|---|---|
| XBRLFiling | GPT-5.5 / Haiku / Fin-o1 / Qwen3 / Llama / Qwen2.5 | 600 / 593 / 592 / 598 / 584 / 590 | 0 | 0 | 0 | 0 | 0 / 7 / 8 / 2 / 16 / 10 |
| FinanceBench | Haiku | 0 | 48 | 6 | 4 | 3 | 6 |
| FinanceBench | Fin-o1 | 0 | 59 | 0 | 1 | 2 | 5 |
| FinanceBench | Qwen3 | 0 | 51 | 1 | 1 | 3 | 11 |
| FinanceBench(VERIFIED のみ、全 6 run) | ― | 0 | 131 | **3**(Haiku 2、retrieved 1) | 0 | 0 | ― |

読み方: 本体 V3「linkbase の機械認可は `"[redacted]"` の印で発火し FinanceBench では走らない」は数でそのとおり(FinanceBench 0 行)。**FinanceBench の FA=0 は「LLM が申告した出所(policy_registry)の式で 131 件通し、document_derived の式で 3 件通した」結果**であり、「Core が契約を持つ」体制の数ではない。方式 B の安全条件 b を VeriFin から支持するなら、引ける数は XBRLFiling 側(循環の但し書きつき)だけ。

---

## 2. R2: VERITYGATE 公開コード [公開コード]

取得: `github.com/sachinkg12/yukti` のタグ `veritygate-groundlm-2026-v1.0.0` の tar.gz(sha256 `9455824d…7b1e`、519 ファイル、Java/Kotlin + Python eval)→ `docs/research/papers/veritygate_code/`。**ビルド・実行していない**。

### 2.1 門は決定論か(U5)

`yukti-explain-core/.../claims/ClaimVerifier.java`(124 行):

- 門 1: `citedEvidenceIds` の各 id が graph のノード集合に在る(`validEvidenceIds.contains`)。
- 門 2: `citedEntities` ⊆ `graph.getAllowedEntities()`(**null または空文字は検査を飛ばす**)。
- 門 3: `citedNumbers` ⊆ `graph.getAllowedNumbers()` ∪ {"0","1","2","3"}(**文字列の完全一致**、同じく空は飛ばす)。
- 門 4: `ClaimTypeRules`(型ごとの必須 evidence 型。`COMPARISON→WINNER_BY_CATEGORY` など 5 型、`CAP_SWITCH` は 2 型の「全部」)。
- **`claims` が null または空なら `VerificationReport.pass()`**(論文 App. A の「空の申告で検査対象が無かった」経路のコード上の位置)。
- 乱数・LLM・閾値は無い。**U5 は「決定論」で解消**。

### 2.2 門が見ているもの(本体 J8 の 2 件目の事例)

- 門が検査するのは **LLM が JSON で申告した 3 つの配列**(`citedEvidenceIds`・`citedEntities`・`citedNumbers`)だけ。顧客に見える文は検査しない:
  - ベンチ経路(`PairedNarratorRunner`)の `text` は LLM の自由文で、門にも評価側の `RuleBasedFailureClassifier` にも掛からない(後者が `text` を見るのは `looksOutOfScope` の語彙一致だけ)。
  - 製品経路(`ExplanationServiceV1` → `ClaimRenderer`)の文は `normalizedFields`(`deltaUsd`・`capAmountUsd`・`feeUsd` …)から組まれるが、**`normalizedFields` と `citedNumbers` の突き合わせは無い**(`grep normalizedFields` で検査箇所 0)。
- これは**論文が自ら明記**している(要旨「It checks a fixed schema; it does not verify every fact in the prose.」、§「Risk of false assurance from partial verification」、App. A の 4 + 1 件)[論文]。本文書はそれをコードの位置で確認しただけで、新しい欠陥の発見ではない。
- 本体との対応: VeriFin の `formula_source`(V2)と同じ「**自己申告の配列を集合で検査する門**」。J8「AI の自己申告は Core が登録簿で検証する。文字列を信じない」は、2 系統の公開実装で同じ形の穴が在ることで重みが上がる。Audit Core への含意は「**Core が検査した対象(pointer)と、顧客に出す対象が同一であること**を契約で留める」(本体 J9 の欄の追加候補、§4.1)。

### 2.3 修復(r=1)と寛容な出力

- `maybeRepair`: 初回が不合格のとき、**門のエラー文(「citedNumber not allowed: 2400.0」のように違反した文字列つき)を最大 10 件そのまま付けて**再プロンプトし、最大 r 回。全試行のうち失敗 claim 数が最少のものを採用(「最後の試行」ではない)。空の出力・schema 失敗は修復しない。
- 評価側の `hallucination_rates.py` は、schema 失敗の行を「合格」に数えない旨をコメントで明記(`VerifierReport.allPass(0)` の空合格を集計から外す)。
- **製品経路は LLM 経路が既定で無効**(`NARRATION_LLM_ENABLED`)、LLM の claim が門を通らなければ決定論の claim に落ち、決定論の claim も門を通す(fail closed、`IllegalStateException`)。論文の「permissive emission(通った claim だけ出す)」はベンチの指標であり、製品コードは「全部通るか、決定論に戻る」の二値 [公開コード]。
- 読み方 [推論]: 修復のプロンプトは「どの文字列が許されないか」を教えるので、**配列から外す**ことで門を通せる(文からは外さなくてよい)。論文の指標では修復で Llama の shipped claims が −0.71/instance(より保守的に)という向きで、「外して通した」かどうかは論文の表からは分からない(**未確認**)。方式 B/C で「門の理由を AI に返す再試行」を作るなら、本体 §3.1 の c7「再試行は候補の id だけ、理由の文字列は返さない」を安全条件に入れる根拠になる。

---

## 3. R3: FinTagging v5 [論文]

- 取得: arXiv `2505.20650v5`(2026-05-17、17 頁、sha256 `1925c71b…86d8`)。
- v4 との差分: 行単位の類似度 0.943。差は著者所属・脚注番号・段落の組版の移動のみ。**本文中の小数(385 個)の多重集合が v4 と完全一致**。表 6・7 の数(FinCL 0.1889、rerank-only 0.2144、extreme classification 0)は変わらない。
- **J5 に変更なし**。本体 §6.3 R3「設計上の影響は 2 点に限る」の 2 点とも動かない。

---

## 4. R4: 日本に DQC 相当の決定論的誤り判定基盤が在るか

### 4.1 見つかったもの [公開資料]

| 資料 | 内容 | 設計への含意 |
|---|---|---|
| 金融庁『バリデーションガイドライン』2025 年 9 月(ESE140119、75 頁)・『バリデーションメッセージ一覧』2025 年 9 月(ESE140121、53 頁)。本文を `papers/ref_edinet_validation_*.txt` に抽出 | 提出時の検証は 206 コード(**ERROR 114 / WARNING 92**)。計算リンクは 3-6-1 の 2 項目だけで、合計科目の不一致 **EC5611W は WARNING**(「合計科目の「xxx(yyy)」の値「n」が、計算リンクの計算値「m」(項目数:l)と一致しません」)。検証対象のコンテキストは連結/個別の軸で限定(図表 3-6-2)。コンテキスト ID と DEI の日付の整合(EC8018W など)は在るが、**期間を跨いだ値の比較・前回提出との比較・要素選択の意味的な検査は無い** | EDINET の提出検証は「構文 + 計算リンクの警告」まで。**正解集合の源にはならない** |
| 米国 XBRL US DQC(本体で参照) | 承認済み規則集 + 誤りの公開 | 日本側に対応物は**見つからず**(金融庁・XBRL Japan の公開資料の範囲。網羅的でない = **未確認**) |
| 第三者「EDINET DB」(Cabocia Inc.。金融庁と無関係と明記) | 約 2,000 要素 → 156 項目の標準化、10 本の内部整合性検査(純利益 ≈ EPS × 株数 ±5%、BS 恒等式 ±1% など)、外れ値検出。規則は公開、**誤りデータ・規則一覧のダウンロードは無い** | 「決定論的な整合性検査を後段に置く」事例としては参考。正解集合にはならない |
| JICPA IT 委員会研究報告第 44 号(2014)、IFRS Foundation ITCG 2025-10 JICPA 資料 | 監査人の留意事項・活動概要(**本文未読**。検索結果の題名のみ) | ― |

### 4.2 判断への影響 [推論]

- **J9(概念の一致を値以外で確かめる契約と試験)は、官製の正解集合に頼れない**。現状の独立判定(98 行)を増やす以外に正解の源が無い。これは本体 §6.6 の 3 番の優先度を下げない(上げも下げもしない)。
- 計算リンク(`cal` linkbase、EDINET の zip に在る)は**値に依存しない追加の証拠**になりうる: 束縛した fact が親子関係のどこに居るかは主張値と独立に決まる。ただし §1.3 の VeriFin の例(整合の破れで主張ごと棄却)と、EDINET 自身がそれを WARNING に留めていることから、**門ではなく「理由」の欄に出す**のが安全側 [仮説。S100Z4Q1 の計算リンクの整合率は未測定]。
- 方式 A の語彙(81 語)を機械的に増やす材料として EDINET DB の「2,000 → 156 の対応表」は**公開されていない**ので使えない(本体 §6.5 の 1 行目の警告はそのまま)。

---

## 5. 本体の表への差分(本体は変更せず、ここに差分だけ置く)

### 5.1 §2.1 VeriFin 影響経路の表に足す行

| # | 経路 | 論文 | コード | 守り | 誤候補が VERIFIED になりうるか |
|---|---|---|---|---|---|
| V14 | **repair**: UNSAT 後に検証器の fact・式を LLM に渡して答えを再生成し再検証 | 記述なし(`Nrepair` は run 名のみ) | `results/latest/*` の `repair{}`(`repair_mode=dedicated_unsat_core_feedback_same_verifier_side_channel`)。実装位置は**未確認**(`src/` の grep では `pipeline.py` の `REPAIRED_VERIFIED` 経路しか見つからず、これは `first_pass_solver_status` を持たない別経路) | 見出しの `status` は VIOLATED のまま(TA に数えない) | 見出しでは**ならない**。再生成した答えだけ見れば FinanceBench で 6/8 が gold と不一致のまま SAT |

### 5.2 §2.2 VERITYGATE の表の更新(論文のみ → コード確認)

| 項目 | 本体の記述 | 今回の確認 |
|---|---|---|
| 4 門の決定論 | 論文のみ | **コードで確認**(集合所属・文字列完全一致・型規則。乱数・LLM・閾値なし) |
| 空の宣言の通過 | 論文 App. A | `ClaimVerifier.verifyInternal` の冒頭 `claims.isEmpty() → pass()`、および各配列の `null/空文字` は検査を飛ばす |
| 修復 r=1 | 論文 | `maybeRepair`: エラー文(違反文字列つき)を最大 10 件返す、best-of、空出力は修復しない |
| 門が見る対象 | ― | **申告した配列のみ**。`text` / `normalizedFields` は検査しない(論文が明記) |
| 製品経路 | ― | LLM 経路は既定で無効、不合格なら決定論に戻る、決定論も門を通す(fail closed) |

### 5.3 §4 評価軸への追加候補

| 軸 | 定義 | 分母 | 出どころ |
|---|---|---|---|
| **E2'(内部整合だが誤り)** | 検証器が SAT/GROUNDED にできる根拠のうち、独立判定と不一致のもの | 検証器が束縛した根拠の件数 | VeriFin の repair 行(FB 6/8)。Audit Core では E2 と同じもの(`wrong_binding`)だが、**AI の候補が無い A でも測れる**のが利点 |
| **E11(出力と検査対象の同一性)** | 顧客に出した数・id のうち、Core が検査した pointer に由来しないもの | 出力した数・id の件数 | VERITYGATE の `normalizedFields` 未検査。Audit Core では Result = state + pointer のみなので**構造上 0 のはず**(試験は**未確認**) |

### 5.4 §5 実験設計への追加

- 事前登録の欄に「**再試行による救済件数**」を置き、予測は 0(再試行を持たない設計なので同語反復になる。置く理由は、将来 c7 を破る変更が入ったときに赤くなる欄を先に作るため)。
- 反事実「誤った候補・値が同じ(型 5)」に、**VeriFin の 3 件の形(単位 ×1000・符号反転で主張に一致)**を人が作る候補の型として追加する。EDINET の `scale` と符号規約(`flow_convention`)は Audit Core の既存の弱点(本体 §2.3 M4)と重なる。
- 腕の追加候補 **A1-cal**: A1 に計算リンクの親子整合を「理由」として付ける(状態は変えない)。測るのは「誤った束縛 2 件・型 5 の 3/22 のうち、計算リンクの不整合が理由欄に出る件数」。**費用 0(LLM なし)**で、§4.2 の仮説を 1 書類で測れる。

### 5.5 §6.2 未判断事項の更新

| # | 本体 | 今回 |
|---|---|---|
| U5 VERITYGATE の 4 門が決定論か | コード未取得 | **解消**(決定論) |
| U6 VeriFin の FA=0 に V8 がどれだけ寄与したか | 未集計 | **解消**(VERIFIED への寄与 3/3,268、FA への寄与 0) |
| U1〜U4・U7・U8 | ― | 変わらず(実験でしか答えられない) |
| **U9(新)** VeriFin の XBRLFiling の FR の原因分布 | ― | 1 行で計算リンク整合の破れを確認。許容差の不一致(§1.3 (b))との割合は行ごとに未読(GPT-5.5 は core が空) |
| **U10(新)** VeriFin の repair 経路の実装位置と、再生成した答えが製品出力に出ないことの保証 | ― | `results/` からの逆算のみ。`src/` の該当箇所は未確認 |

---

## 6. 次に判断すべき事項(本体 §6.6 の 3 件を再評価)

| 順位 | 判断 | 今回の変化 |
|---|---|---|
| 1 | E2 を方式横断の主要指標に据える | **根拠が増えた**: VeriFin 自身のデータで「内部整合だが gold と不一致」が FB 6/8 在る(§1.4)。E2 を持たない指標体系は VeriFin の FA=0 と同じ盲点を持つ |
| 2 | §5 の比較実験を 1 回行う | **分割を提案**: (2a) **LLM を使わない腕と反事実(A0 / A1 / A1-cal + 型 5 の人手候補)**は費用 0 で、本体 §6.4 の 3・4 の一部に答える。(2b) LLM の腕(B-m / B-u / C-f / D-a)は従来どおり費用の承認が要る。2a を先に行えば 2b の予測の帯を狭く書ける |
| 3 | `Pointer` に概念・期間・範囲の欄を持たせる Core 封を先に立てる | **変わらず**。R4 で官製の正解集合が無いと分かったので、欄を持たせた後の試験の正解は独立判定を増やして作るしかない(人間の工数が要る)点を封に書く |

**今回も採用・棄却は決めていない。** 2a は「新規実験」なので、本文書は設計(§5.4)までで止め、実行は承認を待つ。

---

## 7. 取得物と Git の状態

| 取得物 | 場所 | 同定 |
|---|---|---|
| FinTagging v5 PDF/TXT | `docs/research/papers/p2_fintagging_2505.20650v5.{pdf,txt}` | sha256 `1925c71b14cce095013ac988638bf1b741829b23f495e936780b1aec79c786d8` |
| VERITYGATE コード | `docs/research/papers/veritygate_code/src.tar.gz` + 展開 `yukti-veritygate-groundlm-2026-v1.0.0/` | sha256 `9455824d8ba6e575b8521be458304933f13f1b48cf43b0908d8c7b0da2fc7b1e`、519 ファイル |
| EDINET バリデーション 2 文書の本文 | `docs/research/papers/ref_edinet_validation_guideline_ESE140119_2025-09.txt`、`ref_edinet_validation_messages_ESE140121_2025-09.txt` | 出典 URL は `papers/SOURCES.md` |

- `git status` は作業前後とも `?? docs/research/` と `?? scratchpad/`、`git diff` は空(作業終了時に再測定して報告)。VeriFin クローン・VERITYGATE 展開物とも**未実行・未改変**(自前の python で jsonl/テキストを読んだだけ)。
- 未開封指定の 2 書類(`S100Z39P`・`S100Z4N9`)は開いていない。
