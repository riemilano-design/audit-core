# VeriFin 公開実装の監査(論文との照合)

**原則: 論文に書かれていることと、公開コードで実際に確認できたことを分けて書く。一致を前提にしていない。**
**コードは読むだけで、実行・変更・依存のインストールはしていない。**

## 0. 監査の対象

| 項目 | 値 |
|---|---|
| URL | `https://github.com/verifiedfinance/anon`(論文 p.2 脚注 1) |
| commit | `5c49943e8aa43f3dc03c1b2058a73469b22c5c5e` |
| committer date | 2026-08-02T22:40:34-04:00(論文の arXiv 投稿 2026-08-10 の 8 日前) |
| commit message | `Initial anonymous artifact release` |
| default branch | `main`(`--depth 1` の浅いクローン) |
| 保存先 | `docs/research/papers/verifin_code/` |
| 規模 | 5,611 ファイル(`.git` 除く)、**162MB**(`results/` 140MB、`data/` 4.2MB、`figures/` 2.8MB、`src/` 1.5MB、`.git` 9.7MB) |
| Python ファイル | `src/` に 87 本。パッケージ名は歴史的に `verifiqa` |
| 実行の有無 | **していない**。`pytest`・`scripts/paper_scoring.py`・`build_publication_artifacts.py` のいずれも走らせていない |

**エントリポイントが 2 つある**(README): `verifiqa`(一般の pipeline)と **`verifiqa-agent`(論文の pipeline)**。以下「論文経路」は `src/verifiqa/agent/` を指す。

## 1. 論文の 5 段とコードの対応

| 論文 §(p.) | コードの場所 | 対応 |
|---|---|---|
| §3.2 Evidence Retriever | `src/verifiqa/retrieval/evidence_retriever.py`・`planner.py`・`table_rows.py` | 存在する(本監査では詳細未読。**未確認**) |
| §3.3 Answer Generator | `src/verifiqa/generation/answer_generator.py`・`answerers/{cot,pot}.py` | 存在する |
| §3.4 Verification Planner | `agent/agent.py:90-192`(`decompose_question` / `decompose_question_consensus`)・`agent/claim_classifier.py` | 存在する |
| §3.5 Provenance Verifier | `verification/xbrl_linkbase.py`(1,748 行)・`agent/agent.py:629-717` | 存在する |
| §3.6 Claim Verifier | `verification/smt_generator.py`・`z3_runner.py`・`agent/agent.py:518-556` | 存在する |

## 2. 論文の中心的主張とコードの照合 ― 主張値への依存

論文の主張(p.3 §3.1・§3.3):
> 「Crucially, the candidate claim **never influences** the authoritative filing facts or formulas used to check it.」
> 「candidate 𝑎 is passed forward strictly as a target for formal verification and **exerts no influence** on the authoritative facts, linkbases, or solver constraints used to check it.」

### 2.1 支持する所見(公開コード確認)

**(a) 処理の順序がコードで固定されている** ― `agent/agent.py:90-204`

```
# 1. Resolve the verification target from question+evidence only. The
# generated answer must not be allowed to choose or reinterpret formula.
```
検証計画(`claim_spec`)は **question + evidence だけ**から作られ、主張値の抽出(`parse_claimed_answer`)は `agent.py:199` ― **計画が確定した後**に行われる。コメントも「2. Extract only the claimed final value from the generated answer. The parser sees the fixed ClaimSpec but **cannot modify it**」。

**(b) XBRL linkbase 経路の束縛は、値を 0 に潰して実行される** ― `agent/agent.py:655-683`

`_bind_xbrl_role_facts` は役ごとに `VerificationFact(value=0.0, source_quote="")` の placeholder を作り、`claimed_value=0.0` の仮 IR を組んで `_bind_ir_facts` を呼ぶ。**束縛の判断に申告値が物理的に入らない構造**。論文の「value-blind」より強い実装上の保証。

**(c) 曖昧性解消が registry の正規順序で行われる** ― `verification/xbrl_linkbase.py:681-690`、`_prefer_registry_priority` (1166-1193)

```
# Disambiguate by the registry's canonical concept order (e.g. NetIncomeLoss
# before ProfitLoss), NOT by closeness to the LLM-extracted value. Picking the
# candidate nearest the LLM number makes the binding agree with the answer it is
# supposed to check — the source of false verifications.
```
`_ordered_concept_locals` の docstring も「Value-blind: derived only from the fact's name」。候補が 2 つ以上残れば `_prefer_fiscal_period`(「Value-blind.」と明記)を適用し、**それでも 1 件に絞れなければ `return None`**(= 束縛せず abstain)。

**(d) filed value が抽出値を上書きする** ― `_apply_authoritative_bindings` (572-590)
docstring が理由まで書いている: 抽出が filing のタグ値と食い違うと `evidence_<role>` と束縛の 2 つの assertion が矛盾して主張と無関係に UNSAT になり、正答の false reject を生む。だから filed value で上書きする。「Soundness is preserved: a wrong claim still fails against the true XBRL value.」

### 2.2 論文の記述と食い違う所見(公開コード確認)

#### 【所見 A】UNSAT 後の再抽出に主張値が渡される ― 論文の「never influences」と食い違う

`agent/agent.py:352-404`。Z3 が UNSAT を返したとき、UNSAT core に名前が出た fact を**再抽出**する。その呼び出しは

```
retried = extract_fact_with_feedback(
    role, evidence_text, claim_spec.formula, self.llm,
    claimed_value=claimed_value,          # ← 主張値
    computed_value=computed_value,
    tolerance=latest_ir.tolerance,
    ... unsat_core=latest_result.unsat_core,
)
```

`agent/fact_extractor.py:51-100` の `_FEEDBACK_PROMPT` に **`Claimed answer value: {claimed_value}`** が入る。
再抽出で fact が変わると IR を組み直して **ソルバを再実行し、SAT なら `status="VERIFIED"` を返す**(`agent.py:485-493`)。

- **既定で有効**: `AgentConfig.max_unsat_fact_retries: int = 1`(`agent.py:52`)。コメントは「A single fact-repair pass is **the experimental default**」。
- **歯止め 3 つ**(コードで確認):
  1. プロンプトの禁止文(`fact_extractor.py`): 「Use the mismatch only as a diagnostic signal. **Do NOT solve backwards from the claimed value, and do NOT choose a number merely because it would make the formula pass.**」 ― これは**機械的な保証ではなく指示文**。
  2. 再抽出した fact も `_quote_grounded` を通る(引用が証拠本文に在ること)。
  3. 再抽出後も `attach_xbrl_calculations` → `_apply_authoritative_bindings` が走るので、**XBRL/EDGAR に束縛できる役は filed value で上書きされる**。
- **残る経路**: 束縛できない役(registry に無く、label 一致も決まらない役)は、再抽出した LLM の値がそのまま SMT のオペランドになる。また束縛できる役でも、再抽出は `fact.concept` / `row_label` / `fact.value` を変えるので、**どの fact が束縛されるかが主張値を見た後の抽出に左右されうる**。
- **評価への影響**: 論文 §5 は「first-pass」と「retry 後」を区別して報告していない。コードは `first_pass_solver_status` を diagnostics に残している(`agent.py:338-341`)ので、**公開データから first-pass だけの FA/FR を再集計することは原理的に可能**だが、**本監査では実行していない(未確認)**。

> **判定: 論文の「候補主張は検証に使う事実に一切影響しない」は、公開コードの既定経路では成り立たない。**影響は限定的(filed value の上書きがある)が、主張値を見た LLM の再抽出が検証結果を VERIFIED に変えうる経路が存在する。論文はこの再抽出ループに触れていない。

#### 【所見 B】heuristic 経路の「plausibility check」は、実際には丸め水準の一致要求

論文 p.4: 「Only the heuristic third stage is guarded by a **plausibility check** against the extracted value.」

コード `xbrl_linkbase.py:663-690` のコメントは **「Reject if the bound XBRL value is implausibly far from the IR fact value (> 3x)」** と書くが、実際に使う閾値は `_display_binding_tolerance`(1588-1600)で、
- percent/ratio で整数なら **0.5**
- 小数なら **0.5 × 10^(−小数桁数)**
- それ以外 **0.5**

つまり **「3 倍以内」ではなく「開示精度の最終桁の半単位以内」= ほぼ完全一致**。registry 経路では `binding_tolerance = 0.0` にして値ブラインドに上書きするが、**非 registry(filing label linkbase 由来)経路では `diff > display_tolerance` で束縛を捨てる**。

> **判定: 論文の「plausibility check」という語は、コードの実装(丸め水準の一致要求)より緩く聞こえる。**方向は論文と同じ(値に依存するのは heuristic 段だけ)だが、**依存の強さが論文の語感と違う**。
> **コード内部の不整合も 1 件**: `_bind_fact_edgar`(887-895)の docstring は「Resolution is value-blind…**No use of the LLM-extracted value for selection, sign, or plausibility.**」と書くが、同じ関数の 941-947 行が `diff = abs(xbrl_check - float(fact.value))` を計算し、非 registry 分岐で `if diff > display_tolerance: continue` としている。docstring が強すぎる。

#### 【所見 C】符号の反転が抽出値によって決まる経路がある

`_exact_binding_multiplier`(1200-1219)は、|XBRL 値| と |抽出値| が許容差内で一致し**符号が逆**のとき `-1.0` を返し、束縈乗数に掛ける。適用範囲は `_allows_outflow_magnitude_binding`(1220-1229)で制限される ― `_OUTFLOW_MAGNITUDE_CONCEPT_LOCALS`(`PaymentsToAcquirePropertyPlantAndEquipment`・`PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities` の 2 件)、`PaymentsToAcquire` 接頭辞、`CapitalExpenditure` を含む名前、または `PurchaseOf` 接頭辞かつ fact 名に `capex`/`capitalexpenditure` を含む場合。

> **判定: 論文に符号規約の扱いの記述が無い。**キャッシュフロー系の符号を抽出値の符号に合わせる逃げ道がコードに在る。論文 §5.2 が「cash-flow subtotals remain difficult」と書いている領域と重なる。

#### 【所見 D】論文 §3.5 の「余剰トークン最少」の同点処理が、概念解決の経路に無い

論文 p.3: label-matching heuristic は「breaks ties by selecting the candidate with the **fewest surplus tokens**」。

- `xbrl_linkbase.py:_candidate_concept_locals`(1032-1063)は filing の label linkbase に対し `row_tokens <= label_tokens`(行トークンが概念ラベルトークンの部分集合)で**一致した概念をすべて集合に入れる**。余剰トークン最少による選択は**この関数に無い**。同点は後段の registry 優先・会計期間優先で絞り、**1 件に絞れなければ束縛しない**。
- 「余剰トークンの上限」に相当する実装は**別のモジュール**に在る: `agent/table_fact_extractor.py:204` の `_MAX_EXTRA_LABEL_TOKENS = 2`(表の行ラベル抽出側。`_row_label_matches`)。
- `src/` 全体を `surplus|fewest` で検索して該当 0 件(`table_fact_extractor.py` の `_MAX_EXTRA_LABEL_TOKENS` の 2 行のみ)。
- 論文に記述の無い制約がコードに在る: `_candidate_concept_locals` は **行ラベルのトークンが 2 つ以上**ないと label linkbase のフォールバックを試みない(「require at least 2 meaningful tokens to avoid broad matches」)。

> **判定: 論文の同点処理の記述は、概念解決の経路には実装されていない。**近い規則が別の層(表の行抽出)に在る。**論文とコードの対応を仮定していれば見落とす差**。

#### 【所見 E】既定では SMT を LLM が書く。論文はそれを述べていない

- `AgentConfig.deterministic_smt: bool = False`(`agent.py:63`)。既定では `self.smt_gen.generate_ir(ir)` = **`SmtGenerator`(`verification/smt_generator.py:181-204`)が LLM に SMT-LIB を書かせる**。
- 決定論的レンダラ `render_ir_smt`(`smt_generator.py:442`)は存在するが**既定で無効**。コメントは「Always well-formed and faithful, so it removes solver_INVALID abstentions entirely; **no LLM in the SMT step**」。
- 論文 §3.6 は「The constraints are compiled into quantifier-free real arithmetic and evaluated by Z3」と書くだけで、**誰がコンパイルするかを述べていない**。論文 p.7 の「verification requires 4–6 LLM calls」は LLM が SMT 段に居ることと整合はするが、明言は無い。
- **コードが自分で健全性の穴を記録している** ― `agent.py:530-533`:
  > 「No retry on an invalid SMT: an invalid obligation abstains. Regenerating it with the LLM **was found to break soundness (a valid-but-faithless obligation can false-accept)**, so that retry is removed.」
- **論文経路に SMT の構造検査が無い**: `SmtSanitizer`(`verification/smt_sanitizer.py`、53 行、「Minimal structural check」で検査は 2 つだけ ― 必要な fact ごとに named evidence assertion が在るか、named formula assertion が在るか)は `pipeline.py:50,124,141` から使われるが、**`src/verifiqa/agent/` から `SmtSanitizer`・`validate_ir` を呼ぶ箇所は 0 件**(grep で確認)。論文経路では LLM が書いた SMT が Z3 の構文妥当性だけを通って判定に使われる。

> **判定: 論文の主結果が「LLM が書いた証明義務」の上で得られたのかは、論文からは判定できない。**次節の通り、**公開された正本の run はすべて `det_smt` だった**。

### 2.3 公開結果の設定(公開コード確認) ― 主結果は決定論 SMT の run

`results/scoring_policy.json` の `canonical_runs` が各セルの `source_path` を記録している。

| データ | モデル | source_path | 設定 |
|---|---|---|---|
| XBRLFiling | gpt-5.5 | `results/latest/mc_calc_gpt5.5_codex_**det_smt**_Nrepair_run1` | 決定論 SMT |
| XBRLFiling | claude-haiku-4.5 | `results/mc_calc_**detsmt**_v2_haiku` | 決定論 SMT |
| XBRLFiling | fino1-identity-pending | `results/latest/mc-fino-30b-latest` | 名前から判定不能(**未確認**) |
| XBRLFiling | qwen3-30b | `results/latest/mc-qwen-30b-latest` | 同上(**未確認**) |
| XBRLFiling | llama-3.1-8b / qwen2.5-7b | `results/mc_calc_**detsmt**_v2_*` | 決定論 SMT |
| FinanceBench | claude-haiku-4.5 ほか | `results/fb_**detsmt**_v2_*` / `fb_qwen3-30b_updated2_**det_smt**_run3_new` | 決定論 SMT |

`docs/EXPERIMENTS.md` は **§1 を「Main VeriFin runs (the method)」として `--deterministic-smt` **なし**のコマンドで示し、§2 を「Deterministic-SMT **ablation**」として別立てにしている。しかし §3 のベースラインが使う固定答えプールは `ANS=results/mc_calc_**detsmt**_v2_haiku/results.jsonl`。

> **判定: 文書(EXPERIMENTS.md)は決定論 SMT を ablation と呼び、コードは既定を LLM-SMT にしているが、公開された正本の計測はほぼすべて決定論 SMT の run である。**
> これは論文の健全性にとって**良い方向の食い違い**(主結果は LLM が SMT を書かない設定で得られた)。ただし**論文はこの設定を述べておらず、読者は既定の構成で同じ数が出ると誤解しうる**。
> 公開された非 detsmt の run は `results/mc_calc_qwen2.5-7b` と `results/mc_calc_llama3.1-8b` の 2 本だけで、**正本に採られていない**。

## 3. 論文の数値と公開結果の突き合わせ

`results/paper_metrics.csv` と `results/scoring_policy.json` を論文 Table 2(p.8)・Figure 4(p.6)と比べた。

### 3.1 一致した行

claude-haiku-4.5 の XBRLFiling(TA 455 / FA 0 / TR 92 / FR 46 / AB 7、precision 100・accuracy 92.2・coverage 98.8)と FinanceBench(28/0/17/9/13、83.3/80.6)、qwen2.5-7b・llama-3.1-8b の XBRLFiling、fino1 の両データ、gpt-5.5 の XBRLFiling(560/0/3/37/0)は**論文と公開値が一致**。
データセット構成も一致(XBRLFiling 600 行・28 社・86 文書、FinanceBench 67 行)。

### 3.2 一致しなかった行

| 行 | 論文 Table 2 | `paper_metrics.csv` | 公開 artifact 側の説明 |
|---|---|---|---|
| **Qwen3-30B / XBRLFiling** | TA 245・FR 69・AB 0・acc 88.5・cov 100.0 | TA **304**・FR **63**・AB **2**・acc **89.5**・cov **99.7** | `noncanonical_conflicts.xbrlfiling_qwen3_older_table_run` が **論文の数と完全一致**(TA 245/FA 0/TR 286/FR 69/AB 0)。source は `results/mc_calc_qwen3-30b_updated_schema_det_smt_schema_fixed_run1`、`reason_not_selected: "Final figure code uses the newer results/latest/mc-qwen-30b-latest run."` → **論文の表は、artifact が正本に採らなかった古い run の数を載せている** |
| **Qwen3-30B / FinanceBench** | TA 24・FR 10・AB 15・acc 80.8 | TA 24・FR **8**・AB 15・acc **84.6** | 別の非正本 run(`finbench-qwen-30b-latest`)は 25/0/18/9/15 で**これも論文と一致しない**。論文の行は**公開されたどの run とも一致しない** |
| **Llama-3.1-8B / FinanceBench** | TA 10・FR 13・AB 28・acc 66.7 | TA 10・FR **12**・AB 28・acc **69.2** | 説明なし。**1 件のずれ** |
| **GPT-5.5 / FinanceBench** | TA 35・FA 0・FR 10・AB 12・acc 81.8・cov 82.1 | **行が空** | `scoring_policy.json`: `"status": "missing", "reason": "**No FinanceBench GPT-5.5 result directory exists in the audited repository.**"` → **論文が報告した数の裏づけが公開 artifact に無い** |
| **Direct LLM / FinanceBench** | Figure 4: FA **21**・precision 68.7 | FA **18**・precision 71.9・AB 3 | 68.7% = 46/67、71.9% = 46/64。**論文の図は 3 件の abstention を accept 側に数えている**(= 分母を 67 に取る)。`scoring_policy.json` の `outcome_mapping` は `claimed_value is null` を AB に分類する。**方法の差であって矛盾ではないが、論文 Abstract の「baselines accept between 4 and 21 incorrect claims on FinanceBench's 67 claims」は artifact の数え方では最大 18** |

### 3.3 artifact が自分で記録している注意書き(論文に無いもの)

1. **`results/MODEL_IDENTITY_CAVEAT.md`** ― Fin-o1 の答え生成チェックポイントが result ファイルから特定できない。ディレクトリ名は `30b`、歴史的なプロット用コードのラベルは `Fino1-8B`、smoke テストは `TheFinAI/Fino1-8B` を指す。`results.jsonl`・`summary.json` のどちらにも model identifier・revision・推論プロバイダ・デコード設定が記録されていない。「A directory name or plot label is not sufficient provenance.」「Do not silently choose 8B or 30B from the conflicting filenames.」
   → **論文 Table 2 と §4.2 は "Fin-o1-8B" と書いているが、artifact は 8B と断定しないよう求めている。**
2. **`results/manual_adjudications.json`** ― FinanceBench の **6 問**(67 問中 9.0%)の正解を手で裁定している。理由は単位の正規化(USD 8.70 billion → 8,700 USD millions など 3 件)、合成答え(1,097 + 862 = 1,959 の合計を要求 1 件)、散文の正解の正規化(「flat」→ 0 percent)など。`scoring_policy.json` の `manual_adjudication_rule` は「ID が載っているだけで任意の候補を correct に分類してはならない」と縛っている。
   → **論文に手裁定の記述が無い。**正解ラベルは TA/FA の分母を決めるので、**FA=0 の FinanceBench 側の数はこの 6 件の裁定を含む**。
3. **`stale_smt_files_ignored: 54`** ― FinanceBench の haiku 正本 run は source SMT 121 ファイルのうち 67 を採り **54 を「stale」として無視**している(`smt_selection.ignore_stale_status_named_files: true`)。
4. **`summary_file_warning`** ― 「Run summary.json files use internal expected-solver-status scoring and **must not be treated as paper headline metrics**」。

### 3.4 良い方向の所見

- `scoring_policy.json` は**分母を固定し `excluded_ids: []` を明記**(「Both headline denominators are fixed; no question is silently removed during paper scoring」README)。
- `noncanonical_conflicts` を**自分から記録している**。論文と artifact の食い違いを、artifact 側が可視化している。
- `ARTIFACT_MANIFEST.json`・`SHA256SUMS`・`publication_manifest.json` でファイル単位の checksum を持つ(**本監査では照合していない。未確認**)。

## 4. 論文で説明された機能の実装有無(まとめ)

| 論文の記述 | 実装 | 場所 |
|---|---|---|
| 候補は untrusted、計画が先に確定 | **あり** | `agent/agent.py:90-204` |
| calculation linkbase からの式 f = Σ w_i x_i | **あり** | `xbrl_linkbase.py:_instantiate_constraints` (1234-1292)、`_weighted_sum` (1726) |
| 概念 registry(CFA 教材由来) | **あり**(`policy/registry.py`・`DEFAULT_POLICY_REGISTRY`)。**件数・出典の照合は未確認** | `policy/` |
| label 一致(行トークン ⊆ 概念ラベルトークン) | **あり** | `xbrl_linkbase.py:1050-1061` |
| 余剰トークン最少の同点処理 | **概念解決の経路に無い**(所見 D) | ― |
| 期間・単位の一致要求 | **あり** | `_years_for_fact`・`_context_matches_year`・`_unit_kind_compatible_for_fact`・`_prefer_fiscal_period` |
| filed value が抽出値を上書き | **あり** | `_apply_authoritative_bindings` (572-590) |
| 4 つの信頼できる式の出所 | **あり**。`_TRUSTED_SOURCES = {"policy_registry","generic_operation","document_derived","xbrl_linkbase"}` 以外は abstain | `agent.py:153` |
| 一意でなければ abstain | **あり**。`ambiguous_operation`・`untrusted_formula_source`・`no_roles_identified`・`formula_role_mismatch`・`facts_not_found`・`grounding_failed`・`solver_<status>` | `agent.py` 全体 |
| Z3 と UNSAT core | **あり** | `z3_runner.py`・`agent.py:363-371` |
| 許容差 τ = 最終桁の半単位 | **あり**(`_prepare_inputs` / `tolerance_source`)。**式の照合は未確認** | `agent.py:600-628` |
| 3 状態(Verified/Violated/Abstain) | **コードは 4 状態**。`UNVERIFIED_FORMULA` が別に在る(`agent.py:146,288,300,437`)。`scoring_policy.json` は `VERIFIED`/`VIOLATED` 以外を AB に畳むので、**集計では 3 状態に戻る** | ― |

## 5. 実装に在るが論文で明確に説明されていない機能

| # | 機能 | 場所 | 重さ |
|---|---|---|---|
| 1 | **UNSAT 後の fact 再抽出(主張値をプロンプトに渡す)** | `agent.py:352-404`、`fact_extractor.py:51-100` | **重い**(所見 A) |
| 2 | **SEC EDGAR companyfacts API を第 1 の束縛源にする** ― `_bind_fact` は local XBRL instance より先に `data.sec.gov/api/xbrl/companyfacts/CIK{...}.json` のキャッシュを引く。論文 §3.5 は filing 内の linkbase / registry / label の 3 段しか述べていない | `xbrl_linkbase.py:591-620`、`887-975`、`EdgarCompanyFactsCache` (976-1031) | **重い**(証拠の出どころが「当該 filing」より広い。論文 §3.2 の「cross-filing contamination を防ぐため 1 文書に限定」と緊張する。docstring は「This spans **every filing the company submitted**, so it resolves the right year even when the loaded 10-K does not contain it」) |
| 3 | 既定で SMT を LLM が書く / 決定論レンダラは既定で無効 | `agent.py:63,526`、`smt_generator.py` | **重い**(所見 E) |
| 4 | 符号反転の逃げ道(抽出値の符号で −1 倍) | `_exact_binding_multiplier` (1200-1219) | 中(所見 C) |
| 5 | `require_claimspec_consensus` / `require_smt_consensus`(3 回生成して一致を要求) | `agent.py:49-55,536-553` | 小(既定 off) |
| 6 | `repair_invalid_smt`(既定 off、健全性のため削除されたと同じ場所にコメント) | `agent.py:57-59` | 小 |
| 7 | 行ラベル一致の余剰トークン上限 2 | `table_fact_extractor.py:204` | 小(所見 D) |
| 8 | label linkbase フォールバックの「有意トークン 2 個以上」要件 | `xbrl_linkbase.py:1053` | 小 |
| 9 | 計算制約の剪定(束縛と繋がらない制約を落とす) | `_constraints_connected_to_bindings` (1294-1307)・`_prune_constraints` (1349) | 小 |
| 10 | 制約の許容差を子 fact の `decimals` から積み上げる | `_instantiate_constraints` (1254-1258) | 小 |

## 6. 論文とコードで一致しない点・未実装・確認不能(一覧)

**一致しない**
- A: 「候補主張は検証に使う事実に一切影響しない」 ↔ UNSAT 再抽出に主張値が入る。
- B: 「plausibility check」の語感 ↔ 丸め水準の一致要求。加えて `_bind_fact_edgar` の docstring が「No use of the LLM-extracted value for…plausibility」と書くのに同関数が使っている(**コード内部の不整合**)。
- D: 「余剰トークン最少で同点処理」 ↔ 概念解決の経路に無い。
- 論文 Table 2 の Qwen3-30B(両データ)・Llama-3.1-8B(FinanceBench)の行が公開値と一致しない。Qwen3-30B/XBRLFiling は artifact が「正本に採らなかった古い run」と自ら記録している数。
- 論文 Table 2 の GPT-5.5 / FinanceBench は**公開 artifact に対応する run が無い**。
- 論文 "Fin-o1-8B" ↔ artifact は 8B/30B を断定しないよう求めている。

**論文に記述が無い(実装に在る)**
- 上の §5 の 10 件。特に EDGAR companyfacts を第 1 の束縛源にすること、SMT を LLM が書く既定、UNSAT 再抽出、FinanceBench 正解の手裁定 6 件、stale SMT 54 件の除外。

**確認不能(本監査では見ていない / 公開物から決まらない)**
- Evidence Retriever(§3.2)の実装の忠実性。
- `policy/registry.py` の概念登録件数と CFA 教材との対応。
- 許容差の式(τ)の実装がすべての型で論文どおりか。
- `fino1`・`qwen3` の正本 run が `det_smt` だったか(ディレクトリ名に印が無い)。
- `ARTIFACT_MANIFEST.json` / `SHA256SUMS` の照合(スクリプトを実行していない)。
- 論文の修復実験(Table 3)が UNSAT 再抽出と重複していないか ― 「verifier-guided repair」と「`max_unsat_fact_retries`」は別の層に見えるが、**公開データで切り分けていない**。
- first-pass のみの FA/FR(diagnostics に `first_pass_solver_status` が在るので再集計は可能だが、やっていない)。

## 7. Audit Core への含意(独自推論。採用・実装・実験は行わない)

1. **「値に依存しない」は、設計の宣言では守れない。** VeriFin は論文で宣言し、コードの 4 か所でコメントまで書いて守りながら、**修復ループという別の層で破っている**。Audit Core が同じ原則を掲げるなら、守りたい性質を**層ごとに数える**(どの関数が主張値を引数に取れるか)方が、宣言より強い。
2. **「決定論的」は構成の選択に依存する。** VeriFin の既定は LLM が SMT を書く。主結果は決定論レンダラの run。**「決定論的」と名乗るときは、既定の構成でそうなのかを言わないと誤解される。**
3. **公開 artifact が自分の食い違いを記録する形式は、模倣する価値が高い。** `noncanonical_conflicts`・`MODEL_IDENTITY_CAVEAT.md`・`summary_file_warning`・`manual_adjudications.json` はいずれも「自分に不利な事実を機械可読に残す」形。Audit Core の台帳と同じ思想で、より細かい。
4. **正解の手裁定は FA=0 の分母を動かす。** Audit Core が正解集合を作るとき、裁定した件数と理由を機械可読に残す必要がある(VeriFin は 6 件を JSON で残している)。
5. **論文の数をそのまま引用してはいけない。** Qwen3-30B の行は、公開 artifact 自身が「正本でない run」と記録している。**営業資料・比較表で VeriFin の数を引くなら、`results/paper_metrics.csv` と `scoring_policy.json` の値を引き、論文 Table 2 との差を注記する。**
