# ベストミックス設計検討 ― 決定論的 Core と AI の役割分担(第 2 段階、2026-10-13)

**この文書は調査・設計検討のみ。** コード・既存実験・採用試験・封印条件・Golden Master・既存の成果物は 1 字も変更していない。新しい実験は実行していない(§5 は設計案であり、実施の承認を求める段階に留める)。営業表現・ポジショニングは対象外。
**目的は論文の要約ではなく、どの工程を決定論的 Core に任せ、どこに AI を使い、どこを人間に回せば、誤受理を抑えながら検証可能な Claim の範囲を広げられるか、の判断材料を出すこと。**

## 0. 記法・材料・この文書の背骨

### 0.1 区分と確信度

主張ごとに次の **区分** と **確信度** を付ける。

| 区分 | 意味 |
|---|---|
| 論文記載 | 原文(全文読了済み 5 本)に書かれていること |
| 公開コード確認 | VeriFin の公開実装(commit `5c49943e8aa43f3dc03c1b2058a73469b22c5c5e`、読むだけ・未実行)で確認したこと |
| AC コード確認 | Audit Core の現行 `main`(保護面の束ね sha `490888d4…`)のコードを読んで確認したこと |
| AC 実測 | Audit Core の封じた測定記録(`audit-core/docs/*_RESULT_*.md`・台帳)に記録されている数 |
| 独自推論 | 上の材料から本文書が導いた推論 |
| 未確認 | 取得・読解・測定をしていないので確認できないこと |

確信度: **高** = 一次資料の字で確認できる / **中** = 一次資料から 1 段の推論 / **低** = 複数の仮定を含む推論。

### 0.2 材料(読んだもの・読んでいないもの)

| 材料 | 状態 |
|---|---|
| 論文 5 本(VeriFin / FinTagging v4 / FinAuditing v3 / Risk Memos / VERITYGATE)の原文 | 全文読了(`papers/SOURCES.md`。sha256 再測定一致) |
| VeriFin 公開実装 | `src/verifiqa/agent/agent.py`・`claim_classifier.py`・`fact_extractor.py`・`verification/xbrl_linkbase.py`・`smt_generator.py`・`answer_spec.py`・`policy/registry.py`・`policy/data/*.json` を読んだ。**実行していない** |
| VERITYGATE / FinTagging / FinAuditing の公開コード | **未取得・未読**(§6.3) |
| FinTagging **v5** | **未読**(読んだのは v4。§6.3 で差分調査の判断価値を書く) |
| Audit Core | `core/py/audit_core/{model,verify,registry}.py`・`adapters/xbrl/{recipes,instance,extract,vocabulary,comparators,resolve,registry_setup}.py`(main)、`docs/CLAIM_CONTRACT_SPEC_v0.2.md`、封と結果(`BINDING_ORDER_SEAL`・`CANDIDATE_DEFINITION_SEAL(+ADDENDUM)`・`GROUNDED_BINDING_RESULT`・`INDEPENDENT_JUDGEMENT_51`・`STOP_CAUSE_MAIN_RESULT`・`INTEGRATED_RESULT`・`ADOPTION_CONDITIONS`・`CONTRACT_READING`・`TR6_SPEC_JUDGMENT`)、`measure/README.md`・`measure/material/xbrl/observed_t5.json`、`docs/CLAIMS_LEDGER.md` L-001・L-018〜L-022 |
| 第 1 段階の成果物 | `docs/research/` の 11 本(本文書はそれらを再要約しない。引く数には出典を付ける) |
| EDINET 書類 | `S100Z4Q1` のみ。**`S100Z39P`・`S100Z4N9` は開いていない** |

### 0.3 背骨 ― 「誤受理」は 2 層ある

この文書の全体を貫く区別を先に置く(**独自推論・高**。根拠は §2.3)。

| 層 | 定義 | 誰が測っているか |
|---|---|---|
| **主張の層の誤受理** | **偽の主張**を GROUNDED(VeriFin の False Accept) | VeriFin(FA=0 はこの層)、VERITYGATE(claim-survival はこの層の補数) |
| **根拠の層の誤受理(誤根拠通過)** | **真の主張**を、文が指していない fact で GROUNDED(値が偶然一致した) | **Audit Core だけ**(`wrong_binding` 5/60、台帳 L-001「根拠まで正しい通過 41.4%」) |

VeriFin の公開コードは、引用の接地検査を「数字が証拠のどこかに在ればよい」まで緩めた理由を **「Z3 catches wrong values anyway」** と書いている(`agent.py:1286-1289`、公開コード確認)。つまり**値で守る設計は根拠の層を測らない**。Audit Core が測っている「誤根拠通過」は、5 本の論文のどれにも対応する指標が無い。**AI をどこに入れるかの判断は、この 2 層を分けて初めて意味を持つ**(§4)。

---

## 1. 処理の分解 ― 工程ごとの担当の比較と分類

### 1.1 分類の定義

| 分類 | 意味 |
|---|---|
| **決定論で十分** | 証拠の範囲で、決定論的処理が AI 無しで要件を満たす(AI を足す理由が証拠に無い) |
| **AI 候補生成が有効かもしれない** | 現在の決定論の限界が実測で見えていて、AI が候補を出せば被覆が広がる**可能性**がある(確定ではない) |
| **AI だけでは確定できない** | AI の出力を**そのまま**使うと誤受理が出ることが外部の数で示されている |
| **現状の証拠では未判断** | どちらの向きの証拠も無い |

### 1.2 8 工程の表

| # | 工程 | Audit Core 現行 main(AC コード確認) | VeriFin(論文 / 公開コード) | VERITYGATE(論文) | 分類 | 根拠・確信度 |
|---|---|---|---|---|---|---|
| 1 | Claim の抽出・構造化 | **機械**(正規表現 `NUM_RE`・`AMOUNT_JP_RE`・`DIRECTION_WORDS`、`extract.py`)。LLM 経路(v0.2 §6.2 形 B)は XBRL では**未測定**(停止原因分類 A5「構成上 0」) | **LLM**(Verification Planner。`claim_classifier.py` の JSON: metric / formula / roles / aliases / claim_unit / **formula_source を LLM が自己申告**) | **LLM が自己申告**(`citedEvidenceIds` 等を strict JSON で宣言) | 数の主張の切り出し: **決定論で十分**。形(aggregate / derived)と母集団の構造化: **AI 候補生成が有効かもしれない**(将棋側 LLM 分解: 文 33/37・値 34/37・form 29/37、aggregate 15 件が direct_value に潰れる) | AC 実測(`CLAIM_DECOMPOSITION_BOXES_RESULT`)・高。XBRL 散文での LLM 分解は**未判断** |
| 2 | 概念・対象期間・対象範囲の特定 | **概念**: 81 語の手書き語彙 + 最長一致(`extract.py:89-105`)+ 要素の家族(`instance.py:142-158`、完全一致→部分一致)。**期間**: context 接頭辞 + 既定「当期」。**範囲**: `ctx_ok`(member 置換・`NonConsolidated` 除外) | 概念: 3 段(calc linkbase → registry 58 policy / 61 concept → label 一致)。期間・単位: fact 選別で要求 | 概念に相当するのは「claim 型が要求する証拠型」(Gate 4)。期間・単位の軸は無い | **概念**: 決定論の限界が実測で見えている(停止 214 件中 A1「主語が取れていない」131 = 61%、うち 126 件に副次 B2「語彙が無い」)→ **AI 候補生成が有効かもしれない**。ただし **AI だけでは確定できない**(FinTagging: 17,688 概念への LLM 整合は最良 0.19、正解候補を与えても 0.21)。**期間・範囲**: **決定論で十分**(抽出 v2 の形(対/単一)と期間の手がかりの割当は、独立判定がある 30 件で 29 件が v2 側・旧が正しいのは 1 件) | AC 実測(`STOP_CAUSE_MAIN_RESULT` §2、`ADOPTION_CONDITIONS` §2-3)・論文記載(FinTagging Table 6・8)・高 |
| 3 | 根拠候補の探索 | 語彙の家族 ∩ context ∩ 単位 JPY(`facts_for`)。**値で候補を絞る**(`recipes.py:212-214`、§2.3) | 役ごとに registry / label / **EDGAR companyfacts API**(当該 filing の外に及ぶ)。非 registry 経路は**抽出値との丸め一致**で候補を落とす | 検索は無い(バックエンド出力の allowlist) | 語彙が当たる範囲では **決定論で十分**。当たらない範囲(行見出し 190 のうち語彙が当たるのは 76 = 40.0%)の被覆は **AI 候補生成が有効かもしれない**(閉じた候補集合に限る) | AC 実測(`edinet_taxonomy_findings.md` §4)・高 |
| 4 | 正規データの再取得 | **する**(`resolve.py` が `(name, context)` で instance の fact を引く。LLM の値は使わない) | **する**(filed value が抽出値を上書き `_apply_authoritative_bindings`) | バックエンド出力が唯一の真(外部への再取得は無い) | **決定論で十分**(3 系統とも一致。AI を入れる理由が無い) | AC コード確認・公開コード確認・論文記載・高 |
| 5 | 単位・正規化・演算関係の検証 | 比較器 9 種(`comparators.py`)。**単位の照合は未実装**(束縛の順序の封 §3 規則 2「単位は判定できない」) | Z3 + calc linkbase の制約(`_instantiate_constraints`)。許容差は **答えの表示精度から**(`answer_spec.py`) | Gate 3 は完全文字列一致(`2400.0`≠`2400.00`)。算術は無い | **決定論で十分**。LLM に計算させると FinAuditing FinMR 最良 13.86%・計算誤りが失敗の 70–83% | 論文記載(FinAuditing §4.3)・高。Audit Core の単位照合は**未実装**(AC 実測) |
| 6 | Claim と根拠の**意味的**対応の検証 | **保証する試験が 0 本**(`CONTRACT_READING` ③「概念の正しい束縛を守る試験は 0 本」)。`Pointer` は `scheme`・`locator` の 2 欄で概念・期間の欄を持たない(`model.py`、束縛の順序の封 §6) | 概念は registry の `xbrl_concepts` で束縛(value-blind)。**根拠の層の正しさは測っていない**(§0.3) | Gate 4 の型規則まで。「schema-level であって prose-level ではない」と明記 | **AI だけでは確定できない**(FinAuditing FinSM: 意味の不整合の検出は全モデル Hit@20 13% 未満)。決定論も**現状は保証していない**(概念違い 10 行は統合後も 8 行が停止しない → 人間へ)。**現状の証拠では未判断**(AI の助言が人の判断を速めるかの証拠が無い) | AC 実測(`INTEGRATED_RESULT` §3-5、台帳 L-019)・論文記載・高 |
| 7 | 最終判定 | **Core**(`verify.py`: 比較器の `match` だけで GROUNDED / VALUE_MISMATCH) | **Z3**(接地と認可の後は決定論) | **4 門**(集合所属・文字列一致・型規則) | **決定論で十分**。LLM judge は同一候補プールで FA 26/92、式と接地済み値を渡しても 75/92(VeriFin Figure 4)。judge の位置バイアス 83%(VERITYGATE §4.1) | 論文記載・高 |
| 8 | 判定不能時の人間への引き渡し | 4 状態 + `reason`(登録簿)。人間に回す**仕組み自体は未設計**(D-016 ①③「自動で通さない仕組みをどこに置くか」未決) | Abstain(理由つき)。人手確認の運用は**論文に記載なし** | permissive emission(落ちた claim を出さない)。人手確認の運用は無い | 経路の決定(どの状態・理由を人に回すか): **決定論で十分**。並べ順・要約の補助: **現状の証拠では未判断** | AC 実測(`INTEGRATED_RESULT` §4)・論文記載・中 |

### 1.3 表から読める設計上の事実(独自推論)

1. **AI を足す理由が実測で在るのは工程 1(形)・2(概念)・3(被覆)だけ**で、工程 4・5・7 は AI を足す理由が証拠に無く、むしろ外部の数が決定論を支持する。
2. **工程 6 は、決定論も AI も現状は保証していない。** Audit Core の「概念の一致」は語彙と値の一致に頼っており、それを守る試験が 0 本。ここは方式の選択以前に「何を保証と呼ぶか」の契約の問題(束縛の順序の封 §6 が Core 封へ送った事項)。
3. **Audit Core で「値に依存しない」のは Core(`verify.py`)であって Adapter の束縛ではない**(§2.3)。方式の比較は、この現状を基準線にして行う。

---

## 2. AI の影響経路 ― 候補選択・再抽出・再試行・Claim 値の提示・並び順・フォールバック

### 2.1 VeriFin(論文の説明と公開コードを分けて書く)

論文の主張(p.3): 候補主張は検証に使う事実・リンクベース・ソルバ制約に**一切影響しない**。LLM は「意味解析と検索計画」だけ。

| # | 経路 | 公開コードの場所 | 何に影響するか | 歯止め(コード) | 誤った候補 → VERIFIED の可否 | 論文の記述 |
|---|---|---|---|---|---|---|
| V1 | **検証計画を LLM が作る**(metric・式・役・alias・単位) | `claim_classifier.py:28-75`(プロンプト)、`:179-190`(JSON をそのまま `ClaimSpec` に) | 式そのもの・どの行を探すか | プロンプトに registry の索引を見せる(`:29-30`)。`answer` は渡さない(`agent.py:122`) | **可**。LLM が誤った式 f' を作り、答えも f' で計算されていれば、filed value で束縛しても SAT → VERIFIED。論文の「式の権限の階層」は**プロンプトの規則**で、コードは次の V2 の文字列だけを見る | 論文記載 §3.4(階層)。「LLM が計画を誤った場合の挙動」は記載なし(**未確認**) |
| V2 | **`formula_source` を LLM が自己申告** | `claim_classifier.py:41,179`、`agent.py:153`(`_TRUSTED_SOURCES` は**文字列の集合所属**だけ) | 「信頼できる出所か」の門 | `grep` の範囲で、`policy_registry` と申告された式が registry の template と一致するかを検証する箇所は**無い**(`find_policy` は direct-lookup 経路 `:591` のみ) | **可**(V1 と同じ。LLM が `policy_registry` と書けば門を通る) | 論文に記述なし |
| V3 | **calc linkbase による式の機械的認可** | `agent.py:876-940` `_maybe_authorize_xbrl_linkbase_claim` | V1・V2 を**上書き**して式・役・概念を linkbase から決める(LLM の計画を捨てる) | ― | **不可**(この経路に入れば LLM の式は使われない) | 論文 §3.4「filing の calculation linkbase」。**発火条件が `"[redacted]" in evidence_text`(`:893`)= ベンチの伏せ字の印**であることは論文に無い → **FinanceBench ではこの経路は一度も走らない**(公開コード確認・高) |
| V4 | **主張値の抽出を LLM が行う** | `agent.py:197-200`(`parse_claimed_answer`) | 比較される値 v_c | プロンプト「Ignore source facts, years, intermediate values」(`claim_classifier.py:86`) | **可**(答え文中の別の数を v_c と読めば、filed value から計算した値と一致しうる) | 論文に記述なし |
| V5 | **単位・許容差を答えの文から決める** | `claim_classifier.py:757-770` `_infer_claim_unit(question, answer, …)`、`answer_spec.py:56-91`、`agent.py:600-628` | 尺度(百万/十億)と τ。agent 経路は `reported_value` を渡さないので相対下限の錨は **`claimed_value`**(`answer_spec.py:80-83` のコメント「never the claimed value」と**矛盾**) | 相対下限 0.1% と小さい | **限定的に可**(尺度の読み違いは FA にも FR にもなる) | 論文 §3.6 τ = 表示精度の最終桁の半単位(整合)。錨の件は記述なし |
| V6 | **初回の fact 抽出を LLM が行う**(XBRL で束縛できない役) | `fact_extractor.py:16-49` `_PROMPT`(**主張値は入っていない**)、`agent.py:229-236` | 値・行ラベル・期間 | filed value の上書き(束縛できた役のみ)、引用の接地 `_quote_grounded` | 束縛できない役では **可** | 論文 §3.5(「filed fact からのみ値を取る」は束縛できた役に限って正しい) |
| V7 | **引用の接地検査の緩み** | `agent.py:1255-1292` Pass 4: 3 桁以上の数字列が証拠に在れば接地とみなす。「Label adjacency not required — Z3 catches wrong values anyway」 | V6・V8 の歯止めの強さ | ― | V6/V8 と組み合わせて **可** | 論文に記述なし |
| V8 | **UNSAT 後の再抽出に主張値を渡す**(第 1 段階の所見 A) | `agent.py:352-404`、`fact_extractor.py:51-100`(`Claimed answer value: {claimed_value}`)。既定で有効(`max_unsat_fact_retries=1`) | 再抽出後の fact → SAT なら VERIFIED | プロンプトの禁止文、`_quote_grounded`(V7 で緩い)、filed value の上書き(束縛できた役のみ) | **可**(束縛できない役)。論文の「一切影響しない」と**食い違う** | 論文に記述なし |
| V9 | **非 registry 経路の束縛は抽出値との丸め一致を要求** | `xbrl_linkbase.py:663-690`、`887-947`(`diff > display_tolerance → 捨てる`) | どの fact に束縛するか(**値が候補を選ぶ**) | registry 経路は `binding_tolerance=0.0` で値ブラインド | 候補が複数で**抽出値に一致する方が選ばれる** → 根拠の層の誤受理 **可** | 論文 p.4「plausibility check」(語感が緩い) |
| V10 | **符号反転を抽出値の符号で決める** | `xbrl_linkbase.py:1200-1229` | CF 系の符号 | 対象概念を限定 | 限定的に可 | 記述なし |
| V11 | **既定では SMT を LLM が書く** | `agent.py:63`、`smt_generator.py:181-204` | 証明義務そのもの | 論文経路に `SmtSanitizer` 無し(第 1 段階 所見 E)。正本の run は `det_smt` | 既定構成では **可**(コード自身が「valid-but-faithless obligation can false-accept」と記録) | 論文 §3.6 は誰がコンパイルするか述べない |
| V12 | **候補の並び順** | `xbrl_linkbase.py:_prefer_registry_priority`(registry の正規順序)、1 件に絞れなければ `None` | 曖昧時の選択 | 値ブラインド(コメントで明記) | **不可**(絞れなければ abstain) | 論文 §3.5 と整合(余剰トークン最少は未実装・所見 D) |
| V13 | Evidence Retriever(LLM の検索計画) | `retrieval/` **未読** | 証拠の集合 | ― | **未確認** | 論文 §3.2 |

**まとめ(公開コード確認・高)**: 論文の「候補主張は事実に影響しない」は、**XBRLFiling(V3 が発火し、式が linkbase で機械的に決まり、役が qname で直接束縛される)では概ね成り立ち、FinanceBench(V3 が発火せず、式・役・単位・許容差・再抽出が全部 LLM/答え由来)では成り立たない**。論文の FA=0 は 12 設定すべてで報告されているが、**FinanceBench の FA=0 は「LLM が決めた式に対して整合している」ことまでしか意味しない**(独自推論・中)。

### 2.2 VERITYGATE(論文のみ。コード未取得)

| 経路 | 論文の記述 | 誤った候補 → 通過の可否 | 区分 |
|---|---|---|---|
| **自己申告の空欄** | LLM が `citedEntities` 等を**空で**出すと「the verifier had nothing to check」→ 通る(Appendix A の 1 件、3 名の rater 全員 NO) | **可** | 論文記載・高 |
| allowlist を知るモデル | 「a model that knows the allowlist could craft outputs that pass verification while remaining semantically misleading」(Limitations 5) | **可**(敵対的) | 論文記載・高 |
| 修復ループ(r=1) | 落ちた claim の誤りメッセージを添えて 1 回再プロンプト。**落ちた claim が少ない方を採る**。capable なモデルは裏づけられない claim を**捨てる**(shipped −0.47〜−0.71) | 「捨てる」方向なので誤受理は増えにくいが、**出力量が減る**ことを率だけでは見落とす | 論文記載・高 |
| 4 門・グラフ構築・フィルタ | 「purely structural: no LLM is involved」、SHA-256 ダイジェスト | **不可**(宣言の範囲内) | 論文記載・高。**コードは未確認** |

「構造的検査と判定不能への退避がどこまで決定論か」への答え: **論文の記述では、宣言された構造化欄に対する検査・退避(permissive emission)は完全に決定論**。**決定論でないのは、何を宣言するかと、修復で何を捨てるか**(どちらも LLM)。Audit Core の「ラベルを付けて残す」形は、捨てた分を数えられる点で VERITYGATE より情報を保つ(第 1 段階の結論と同じ。独自推論・中)。

### 2.3 Audit Core 現行 main(AC コード確認 + AC 実測)

**Core(`verify.py`)は Claim の値を比較器にしか渡さない**(`verify.py` の `comparator_fn(tuple(evidence), claim, recipe.contract)` が唯一の接点。AC コード確認・高)。**しかし Adapter の束縛(`recipes.py`、main)は値で候補を選ぶ**。

| # | 経路 | 場所(main) | 何が起きるか | 実測された帰結 | 区分・確信度 |
|---|---|---|---|---|---|
| M1 | **値で候補を選ぶ**: 家族の fact のうち `match_value` が一致した `hits[0]` を pointer にする | `recipes.py:_direct_value_claim`(`:212-214`、`len(fams)` は `:237`) | 概念が違っても・期が違っても、値が一致すれば束縛・GROUNDED | `N219`(前期末の単独科目に、当期の 2 科目の合計が 1 円まで一致)。GROUNDED 60 件中 `wrong_binding` **5 件 = 8.3%**(95% [2.8, 18.4])。独立判定 57 行に対し旧エンジンの誤った束縛 **18 件** | AC コード確認・AC 実測(`GROUNDED_BINDING_RESULT` §1・`INDEPENDENT_JUDGEMENT_51` §2-C)・高 |
| M2 | **値で再探索する**: 単一 fact が一致しなければ `elif subj:` で当期−前期の対を**値で**探し、見つかれば GROUNDED、それも無ければ `hits[0]` を「diff phrase but value matched a fact」で束縛 | `recipes.py:214-262` | 別経路へ落ちて値が合う対を拾う | `N289`(直前の語彙語の差額に束縛)。規則 3(値での再探索禁止)で 8 件が停止、うち意図 1・巻き込み 7 | AC 実測(`BINDING_ORDER_SEAL` §2-A-3)・高 |
| M3 | **語彙の部分一致・最長一致が別概念を当てる** | `instance.py:155-156`(`e.lower() in local.lower()`)、`extract.py:89-105`(終わりが最も右・同点なら長い語) | 「売上総利益率」→ 語「売上総利益」→ 額の差の符号で通る(`T023`・`T038`)。「純資産」部分一致 → 総額(`T086`)。`業務未払金` が 2 概念を同時に拾う(`N181` 系 12 件) | VALUE_MISMATCH 33 件のうち B3「別の要素・期・member」**28 件**。B2「語彙が無い」25 件のうち部分一致で別語 **14 件** | AC 実測(`STOP_CAUSE_MAIN_RESULT` §2)・高 |
| M4 | **文書順で代表を取る**(`pairs[0]`・`cur[0]`・resolver の `matches[0]`) | `recipes.py`・`resolve.py:matches[0]` | 同値の fact が複数あるとき、どれを指すかは instance の順序で決まる | 5 年表(`jpcrp_cor:*SummaryOfBusinessResults`)が先に出る → 独立 3 席の規約(`jppfs_cor`)と逆。代表選択 patch で 27 行の pointer が移動 | AC 実測(`INTEGRATED_RESULT` §3-4、H-3)・高 |
| M5 | **方向だけの主張を符号で通す** | `recipes.py:_build_raw_text_claims` | 同方向の要素対が 40〜45 組あるので、符号の一致は束縛の証拠にならない | 人の盲検で型 5(値が偶然一致して参照先が違う)**3/22 = 14%**(`T008`・`T022`・`T031`) | AC 実測(`observed_t5.json`、`GROUNDED_BINDING_RESULT` §3)・高 |
| M6 | **LLM 経路(形 B)** | v0.2 §6.2(設計のみ)。将棋側は `CLAIM_DECOMPOSER_INSTRUCTION_v1` で測定済み | XBRL 散文では**走っていない**(停止原因分類 A5「構成上 0」) | 測定なし | AC 実測・高(「未測定」であること) |

**封じた patch(main 未採用)が M1・M2・M4 をどう変えたか**(AC 実測・高):

| 木 | 正答 / 誤った束縛 / 誤停止(独立判定 57 行) | 意味 |
|---|---|---|
| 旧(main) | 21 / **18** / 14 | 値が候補を選ぶ |
| 規則 4 あり(値ブラインド・複数なら停止) | 11 / **1** / **38** | 誤った束縛はほぼ消え、誤停止が 2.7 倍 |
| 設計 Y + 代表選択 + 抽出 v2(統合 RX2) | **37** / **2** / 17 | 残る 2 件は語彙の欠落(`N053`・`N054`) |

**答え(「AI が誤った候補を提案しても誤った根拠が GROUNDED になる経路が在るか」)**:
- **Audit Core main**: AI 以前に、**機械の候補(語彙)が誤っていて値が偶然一致すれば GROUNDED になる**(M1・M3・M5。実測 5/60 と 3/22)。これは AI を入れる前の基準線である。
- **封じた patch の木**: 値で候補を選ばないので、誤った候補は**値が違えば VALUE_MISMATCH(誤棄却)・値が同じなら GROUNDED(誤根拠通過)**になる。後者は設計 Y が自ら「偶然同じ値を持つ別概念が 1 候補に畳まれる」リスクとして封に書いた(`CANDIDATE_DEFINITION_SEAL` §2)。3 書類では別概念の混入 0 件だが、**未使用 2 書類では未確認**。
- **AI を候補生成に入れた場合(方式 B・C)**: 誤った候補が GROUNDED になる経路は、**上と同じ「値の偶然一致」だけ**になる ― ただし **Core が候補の id から正規データを再取得し、値で候補を選ばず、候補が複数なら止まる**という 3 条件を満たす限りにおいて(§3 の安全条件)。この 3 条件のどれかが欠けると、VeriFin の V8・V9 と同じ経路が開く。

---

## 3. 方式 A〜D の比較

**どの方式も最初から採用・棄却しない。** 各方式について、誰が何を決めるか・利点(証拠)・失敗経路・必要な安全条件・証拠の区分を並べる。

### 3.1 比較表

| | **A. 決定論的な語彙・規則・対応表だけを拡張** | **B. AI が Claim を構造化し、Core が正規データを再取得して契約・概念・期間・範囲・単位・演算・値を決定論で検証** | **C. AI が根拠候補・概念候補を提案し、Core が独立に再取得・照合して採否を決める** | **D. AI が検証結果そのものを判定** |
|---|---|---|---|---|
| 誰が何を決めるか | 人が語彙・規則を書き、機械が全部決める | AI: 何についての主張か(subject・form・期間・範囲・単位の**宣言**)。Core: 宣言の id から fact を引き、契約で判定 | AI: 候補の**追加**(主語の区間、要素の家族、期間の手がかり)。Core: 候補集合から一意に絞れたときだけ束縛・判定。**AI は Core が見つけた候補の間で選ばない** | AI: GROUNDED / VALUE_MISMATCH / UNVERIFIABLE を**判定** |
| 近い外部の例 | Risk Memos(決定論レンダラ + 検証器)、Audit Core main | **VeriFin の Verification Planner**、VERITYGATE の自己申告、v0.2 §6.2 形 B | VeriFin の alias 生成(役の行ラベル候補)の部分。FinTagging の「検索 → 再順位」の検索側 | VeriFin のベースライン「LLM judge」「Judge+formula」、FinAuditing の FinMR の採点側 |
| 利点(証拠) | 入力から出力まで決定論・再現可能。統合 RX2 で正答 37/57・誤った束縛 2・誤停止 17(AC 実測)。Risk Memos は合成 fixture 上で 100.0%(論文記載。**一般性能ではない**) | 構造化の被覆が広い(VeriFin XBRLFiling coverage 98.8%。**ただし式は機械認可 V3**)。将棋側の LLM 分解は文 33/37・値 34/37(AC 実測) | **A の停止の 61%(A1)が語彙の範囲外**で、ここだけが被覆を広げられる場所(AC 実測)。AI の出力が「候補」なので、Core の値ブラインド規則と保留がそのまま効く(独自推論・中) | 実装が最も軽い。**それ以外の利点は証拠に無い** |
| 失敗経路 | (i) 語彙の部分一致・最長一致が別概念を当てる(M3: B3 28 件)。(ii) 語彙を増やすと loose 一致の衝突が増える(`N181` 型)。(iii) 値ブラインドにすると誤停止が増える(11/38)。(iv) 被覆の天井は語彙(行見出しの 40.0%)。(v) 同値の別概念の偶然一致(5/60・3/22) | (i) AI が範囲・期間を誤って宣言 → Core が**別の正規 fact**を引く → 値が偶然一致すれば GROUNDED(根拠の層の誤受理)、違えば誤棄却。(ii) **空の宣言**は検査対象が無い(VERITYGATE App. A)。(iii) 自己申告の出所ラベルを文字列で信じる(VeriFin V2)。(iv) 形の潰れ(aggregate → direct_value 15 件、母集団の昇格 16 件。AC 実測)。(v) 主張値の読み違い(V4)。(vi) 再試行で主張値を見せると V8 と同じ | (i) 誤った候補 + 値の偶然一致 → GROUNDED(**A と同じ経路、母数が増える**)。(ii) 候補の並び順に AI の順序が入る(`hits[0]` 型)。(iii) AI が主張値を見て候補を作る(値への依存が候補生成の層に移るだけ)。(iv) フォールバックだけに使うと、測定が「難しい Claim だけ」に偏る。(v) 開放語彙で候補を出させると FinTagging の 0.19 の問題に戻る | (i) 直接の誤受理(同一候補プールで judge FA 26/92、式と接地値を渡しても 75/92。VeriFin Figure 4)。(ii) 位置バイアス(VERITYGATE: 83% でスロット A)。(iii) 計算を任せると CER 70–83%(FinAuditing)。(iv) 再現性なし・根拠の追跡不能。(v) 判定者が engine の状態を見ると漏れる(将棋側の盲検で実測済みの型) |
| 必要な安全条件 | a1 完全一致 > 部分一致、部分一致は候補生成までで束縛の根拠にしない。a2 候補が複数なら停止(規則 4)。a3 値で候補を選ばない・再探索しない(規則 3)。a4 代表の規約を字で決める(5 年表 / 財務諸表)。a5 **概念の一致を守る試験を 0 本から増やす**。a6 語彙を増やしたら必ず測る(CLAUDE.md の歯止め) | b1 Core は AI の**値を一切使わない**(id から再取得・再計算)。b2 AI の宣言(出所・id)は Core が登録簿で**検証**する(文字列を信じない)。b3 一意に絞れなければ停止。b4 **空・部分的な宣言は UNVERIFIABLE**(通過にしない)。b5 候補生成の入力から**主張値を伏せる**(数をプレースホルダに置換)か、少なくとも判定後に値を見せる再試行を作らない。b6 同じ入力に対する宣言の再現性を測る(temperature 0・複数回の一致率。VeriFin の consensus 旗、VERITYGATE のダイジェストに相当)。b7 宣言と結果の対応を Claim ごとに記録 | c1〜c3 = b1〜b3。c4 候補集合は**閉じた一覧**(81 語彙の家族、または当該書類の presentation/label linkbase の要素)に限る。c5 **AI は候補を足すだけで、Core が見つけた候補の間の選択に使わない**。c6 主張値を伏せる(b5)。c7 候補 id・プロンプトの sha・応答を Claim ごとに記録(c7 が無いと §4 の「頑健性」が測れない)。c8 反事実テスト(§5.3)を通過条件にする | d1 AI の出力は**状態を変えない**(GROUNDED に上げることも、VALUE_MISMATCH を下げることもしない)。d2 使うなら人間に回す行の**並べ順・注記**まで。d3 AI は engine の状態・pointer・理由を**見ない**(盲検)。d4 独立判定との一致率を先に測り、κ を記録する(VERITYGATE の rater 対検証器 κ 0.00–0.30 を参照) |
| 現状との距離 | main + 封じた patch 3 本(採用条件 T-R1〜6・T-E1〜4 のうち 6 本は patch で実装・main 未採用)。**単位の照合・概念の試験は未着手** | v0.2 §6.2 に設計のみ。XBRL では未測定。将棋側で分解器 v1 を測定済み | **設計も測定も無い**。`measure/` の注入器(T1/T2/T3)と独立判定 98 行が材料として使える | 無し(導入する理由が証拠に無い) |
| 証拠の区分・確信度 | AC 実測・高 | 論文記載 + 公開コード確認(VeriFin)+ AC 実測(将棋)・中(**EDINET 散文での数は無い**) | 論文記載(FinTagging)+ AC 実測(停止原因)+ **独自推論**・低〜中 | 論文記載・高(否定の向きの証拠) |

### 3.2 方式を横断して読めること(独自推論)

1. **B と C の違いは「AI が決めるものの大きさ」ではなく「Core が AI の出力をどう扱うか」にある。** B でも b1〜b4 を満たせば、AI の宣言は Core にとって「候補の束」になる ― つまり **安全条件を満たした B は C に収束する**(中)。逆に安全条件を欠いた C(AI が Core の候補の間で選ぶ、値を見て候補を作る)は、VeriFin の V8・V9 と同じ経路を持つ B より悪くなりうる。
2. **A の天井と C の入口は同じ場所にある。** 停止 214 件のうち A1 131 件は「主語が取れていない」であり、うち 126 件は語彙を足せば届く(AC 実測)。**語彙を人が足す(A)か、AI が候補として足す(C)か**の違いで、どちらも「足したら必ず測る」の対象になる。A で足すと loose 一致の衝突が増え(`N181` 型)、C で足すと候補 id の記録が要る。
3. **D は判定に使えないが、§1 工程 8(人間への引き渡し)の補助として測る価値は否定されていない**。ただし d1〜d4 を満たす形でしか測れず、効果の証拠は無い。
4. **どの方式でも「値の偶然一致」は残る。** これは方式の問題ではなく、根拠の層の照合(概念・期間・範囲・単位の一致を**値以外で**確かめること)の問題で、現状どの方式にも試験が無い(§1 工程 6)。

---

## 4. ベストミックスの評価軸 ― 分母と固定条件

**単純な正解率・受理件数だけでは評価しない。** 各指標に分母と、比較時に固定すべき条件を書く。現在の値は Audit Core の実測(1 書類 `S100Z4Q1`、1 母集団)であり**一般化しない**。VeriFin の値は参考であって**比較不可**(データ・指標・条件が違う。`paper_comparison.md` §5)。

| # | 指標 | 定義(分子 / 分母) | 固定すべき条件 | 現在の値(AC 実測) | 参考(論文記載・比較不可) |
|---|---|---|---|---|---|
| E1 | **誤受理(主張の層)** | 偽の主張で GROUNDED / 偽の主張 | 偽の主張の集合(注入器の T1/T2/T3、人が札付けした偽) | 偽 1 件(`T087`)で 0。**分母が 1 なので率にならない** | VeriFin FA 0/92(XBRLFiling)、Direct 92/92 |
| E2 | **誤受理(根拠の層)= 誤根拠通過** | 独立判定と pointer が違う GROUNDED / 独立判定のある GROUNDED | 独立判定の集合(`independent_truth_2026-10-12.json` 57 行 + 2 巡目 16 行)、採点の定義(`score_blind51` `7c8f67d`) | main **5/60 = 8.3%**、旧 18/57、RX2 **2/57** | **対応する指標が 5 本のどれにも無い** |
| E3 | **誤棄却** | 正しい根拠が在るのに停止または VALUE_MISMATCH / 独立判定が確定した真の主張 | 同上。「正しい根拠が在る」の判定は独立席(本線の読みだけで「曖昧だから停止」と言わない ― 封 c) | 旧 14/57、規則 4 あり 38/57、RX2 **17/57** | VeriFin FR 37〜73 / 600(「主要な残存コスト」) |
| E4 | **判定不能** | UNVERIFIABLE + POINTER_NOT_FOUND / 全 Claim | 全 Claim の集合(真 391) | 停止 214/391(UV 124・PNF 57・VM 33)。**判定不能 23 件は分母から除外した記録あり** | VeriFin abstention 1.2% / 19.4%、VERITYGATE は落ちた claim を出さない |
| E5 | **検証可能な Claim の割合** | 束縛された Claim / 全 Claim、および**根拠まで正しい GROUNDED / 全 Claim** | 全 Claim の集合 | 177/391 = 45.3%、**根拠まで正しい 162/391 = 41.4%**(95% [36.9, 44.0]) | VeriFin coverage 98.8% / 80.6%(ベンチの作り方に依存) |
| E6 | **入力 Claim 集合を固定した処理件数** | 方式ごとの 4 状態の件数と遷移行列(状態 × 状態) | **同じ Claim 集合・同じ正規データ・同じ契約**(VeriFin の「同一候補プール」と同じ原理) | 1B 91・5F 133・P7 415 で統合測定あり(X2 → RX2 の遷移 31 行) | VeriFin は候補生成を 1 回だけ行い全手法で使い回す |
| E7 | **AI 候補の誤りに対する最終判定の頑健性** | 候補を(正 / 誤 / 無関係)に差し替えたとき **GROUNDED が増えた Claim 数 / 差し替えた Claim 数**、および **誤候補で GROUNDED になった Claim の一覧(件数でなく id)** | 候補 id の記録(c7)、差し替えの種類の固定、値の摂動との分離 | **測定なし**(方式 B・C が無いため)。値非依存の不変試験は P-7 で 0/304(束縛に限った 0。reason 欄は 91 行変わる) | VERITYGATE の ungrounded 変種が近い(証拠を渡さない条件での survival) |
| E8 | **再実行時の再現性** | 同じ入力で同じ出力になった Claim / 全 Claim(状態・pointer・理由の 3 欄で) | 温度 0・同じ材料 sha・同じコード sha | 決定論経路は定義上 1.0(`SEED.json`・保護面 sha で担保)。**AI 経路は未測定** | VeriFin: 接地と認可の後は決定論(条件つき)。VERITYGATE: ダイジェスト |
| E9 | **根拠と判定理由の追跡可能性** | pointer・比較器・理由・候補 id・プロンプト sha が揃った Result / 全 Result | `Result` の欄(`model.py`)。AI 経路では c7 を足す | 決定論経路は全件(pointer・comparator・reason)。**候補 id・プロンプト sha の欄は無い** | VeriFin: concept・期間・単位・accession・fact id を記録 |
| E10 | **人間による確認が必要な割合** | HUMAN へ回した Claim / 全 Claim(理由別) | HUMAN へ回す条件を**先に**決める(D-016 ①③ の「仕組み」) | 概念違い 10 行 + 判定不能 2 行を HUMAN へ(**仕組みは未設計**) | VeriFin・VERITYGATE とも運用の記述なし |

**率と量を一緒に出す**(VERITYGATE §4.2 の逆転: 率が上がって量が減る)。E5 の率だけでなく「根拠まで正しい GROUNDED の**件数**」を同じ行に書く。

---

## 5. 比較実験の設計案(**提案のみ。実施の承認を求める段階**)

**既存の封印済み試験(unittest / pytest / Golden / `test_comparator_independence`)と混ぜない。** 使い捨ての worktree で行い、`main`・保護面(`490888d4…`)・Golden 期待値・封じた文書は触らない。未使用 2 書類(`S100Z39P`・`S100Z4N9`)は**この実験でも開かない**(それらは A の採用条件の held-out として人間が開封条件を決める)。

### 5.1 固定するもの

| 固定するもの | 中身 | 出どころ |
|---|---|---|
| Claim 集合 | (i) 独立判定の材料 **98 行**(対象 51 + おとり 47、確定 57 + 2 巡目 16)。(ii) P7 の真 **391 件**(停止 214 + GROUNDED 177)。(iii) 1B 91・5F 133 | `fixtures/xbrl/independent_truth_2026-10-12.json`・`stop_cause_main_material_2026-10-12.json`・Golden の材料 |
| 正規データ | `S100Z4Q1.zip`(`0731a291…`)、AI 散文版(`03521437…`)、`S100Z4B6.zip` | `~/.cache/audit-core/edinet/`・`fixtures/xbrl/` |
| 契約 | `register_all` の比較器 9・理由 13(main)。腕ごとの束縛規則は patch として固定 | `registry_setup.py`・`docs/patches/*.patch` |
| 正解と採点 | 独立判定(`correct` の保証範囲 = 「この pointer が正しい」であって他を排除しない ― `method_notes`)。採点の定義 `score_blind51_2026-10-12.py`(`7c8f67d`、変えない) | `INDEPENDENT_JUDGEMENT_51` |
| 予測 | 腕ごと・指標ごとに**帯つきで先に封じる**(値は実施時に書く。この文書は欄だけを置く) | `INTEGRATED_SEAL` の形 |

### 5.2 腕(arms)

| 腕 | 方式 | 中身 | 測る問い |
|---|---|---|---|
| A0 | A | `main`(値で候補を選ぶ) | 基準線 |
| A1 | A | 統合 RX2 の木(設計 Y + 代表選択 + 抽出 v2) | 値ブラインドの決定論の現在値 |
| B-m | B | LLM が Claim を構造化(subject の区間・要素の家族(81 語彙の id)・期間・member・form・単位)。**主張値はプレースホルダに置換して渡す**。Core は宣言 id から fact を引き、A1 の規則で束縛・判定 | 値を伏せた構造化で E2・E3・E5 がどう動くか |
| B-u | B | B-m と同じだが主張値を伏せない | 値を見せることの効果(B-m との差 = 値への依存の大きさ) |
| C-f | C | A1 が `no_subject` / `no_element` / `ambiguous(elements)` で止めた Claim **だけ**に、LLM が候補(主語の区間 + 家族 id、閉じた一覧から)を足す。Core は A1 の規則で判定。**A1 が束縛した Claim には触れない** | A の天井(A1 131 件)を C がどれだけ下げ、E2 を上げないか |
| D-a | D | LLM judge に(文、A1 の候補 fact の一覧、**engine の状態・pointer・理由は渡さない**)を与え 4 状態を答えさせる。**出力は記録のみ、状態に使わない** | 独立判定との一致率(κ)。E2 に相当する「誤った fact を正しいと言った率」 |

LLM の席は**記憶を持たない独立席**とし、材料に本線の札・engine の状態・差分の理由を**含めない**(`INDEPENDENT_JUDGEMENT_51` の手順と、「否定文も伏せた対象を漏らす」の教訓)。

### 5.3 反事実テスト(B・C の腕に対して)

AI の候補を機械的に差し替え、**Claim ごと**に状態と pointer の遷移を記録する。

| 差し替え | 作り方 | 通過条件(先に書く) |
|---|---|---|
| **正しい候補**(oracle) | 独立判定の fact を候補にする | 上限。GROUNDED(根拠まで正しい)の件数と id を記録 |
| **誤った候補・値が違う** | 同じ家族の別要素 / 同じ要素の別期間(instance に実在するもの) | **GROUNDED が oracle より増えない**。増えた Claim は id・fact・値を全部列挙 |
| **誤った候補・値が同じ(型 5)** | `reference_numbers.json` から同値の別 fact を選ぶ(`measure/README.md` の T5 の定義。XBRL では機械で作れない型なので**人が作る**) | **GROUNDED になった件数と id を全部記録**。これは「0 にできる」ではなく「何件漏れるか」を測る欄 |
| **無関係な候補** | 乱数(種は封じる)で選んだ要素 | GROUNDED 0 件を予測の欄に書く。1 件でも出たら個別に理由を書く |
| **値の摂動**(既存 P-7 の形) | Claim の値だけ変える | B-m・C-f で候補集合が変わらない(0/n)。B-u で変わる件数を記録 |

**件数だけでなく個々の Claim で確認する**: 遷移は `(腕, 差し替え, claim_id, before_state, after_state, before_pointer, after_pointer)` の行として全件保存し、「候補を誤らせたときに GROUNDED が増えない」と「誤った根拠が GROUNDED にならない」を**別の欄**で判定する(前者は件数、後者は id の集合が空か)。

### 5.4 事前登録の欄(値は実施時に封じる)

| 欄 | 腕 | 予測(帯) | 外れ方 |
|---|---|---|---|
| 正答(57 行) | A1 / B-m / B-u / C-f | ― | ― |
| 誤った束縛(E2) | 同上 | ― | ― |
| 誤停止(E3) | 同上 | ― | ― |
| 反事実: 誤候補(値違い)で GROUNDED が増えた件数 | B-m / C-f | **0 を予測の候補にする** | 1 件でも出れば、その経路を列挙 |
| 反事実: 型 5 で GROUNDED になった件数 | B-m / C-f | 人が作れた件数に対する率。基準は 3/22 と 5/60 | ― |
| 値の摂動で候補が動いた件数 | B-m / C-f | 0 / n | ― |
| D-a と独立判定の κ | D-a | ― | ― |
| 再現性(同じ入力 3 回で宣言が一致した率) | B-m / B-u / C-f | ― | ― |
| 費用(USD)と所要 | 全腕 | **未測定**(見積りの根拠が無い) | ― |

### 5.5 この設計が答えられること・答えられないこと

- 答えられる: **C-f が A の天井(A1)を下げるか**、**値を伏せた構造化が値への依存を本当に消すか**、**誤候補が GROUNDED に化ける経路の有無と件数**、**D が独立判定とどれだけ一致するか**。
- 答えられない: 別文書での振る舞い(1〜2 書類)、EDINET 以外、人間の確認コスト(E10 の仕組みが無い)、費用。

---

## 6. 判断と未解決点

### 6.1 現時点で証拠が支持する設計判断

| # | 判断 | 根拠 | 区分 | 確信度 |
|---|---|---|---|---|
| J1 | **工程 4・5・7(正規データの再取得・単位/演算・最終判定)は決定論に置いたまま変えない** | 3 系統が一致。LLM に計算・判定をさせた外部の数は全部否定の向き(judge FA 26/92、Judge+formula 75/92、FinMR 13.86%・CER 70–83%) | 論文記載 + AC コード確認 | 高 |
| J2 | **AI の出力は「候補の id」としてだけ Core に入れ、AI の値・計算結果・判定は一切使わない** | VeriFin の filed-value 上書き・Risk Memos の正規 fact map・Audit Core の resolver が同じ原則。VeriFin はこれを破る層(V8)を持ち、論文と食い違った | 公開コード確認 + 論文記載 + AC コード確認 | 高 |
| J3 | **誤受理は主張の層と根拠の層の両方で測る。主張の層の FA=0 を安全の証拠にしない** | Audit Core の 5/60・3/22 は主張が真のまま根拠が誤る。VeriFin のコードは根拠の層を値で代替している(Pass 4) | AC 実測 + 公開コード確認 | 高 |
| J4 | **値で候補を選ばない・値で再探索しない(規則 3・4)は、方式に関わらず必要条件**。現 main はこれを満たしていない | 旧 18 → 規則 4 あり 1 → RX2 2(誤った束縛)。VeriFin のコメント「値の近さで選ぶのは false verifications の源」 | AC 実測 + 公開コード確認 | 高 |
| J5 | **AI に開放語彙で概念を決めさせない。AI の役割は閉じた候補集合への「追加」まで** | FinTagging: 17,688 概念で 0.19、正解候補を与えても 0.21、全 taxonomy から 1 段で選ばせると 0。EDINET の行見出し 19.5% が複数要素 | 論文記載 + AC 実測 | 高(否定の向き)/ 追加の有効性は**中**(推論) |
| J6 | **空・部分的な AI の宣言は UNVERIFIABLE に落とす(通過にしない)** | VERITYGATE App. A の false accept 1 件は「空の申告で検査対象が無かった」 | 論文記載 | 高 |
| J7 | **判定後に主張値を見せて候補を作り直す再試行を作らない** | VeriFin V8(既定で有効、論文に記述なし) | 公開コード確認 | 高 |
| J8 | **AI の自己申告(出所・id・型)は Core が登録簿で検証する。文字列を信じない** | VeriFin V2(`_TRUSTED_SOURCES` は文字列の集合所属) | 公開コード確認 | 高 |
| J9 | **方式を選ぶ前に、概念の一致を値以外で確かめる契約と試験を作る**(`Pointer` に概念・期間の欄を持たせる Core 封は既に送られている) | 「概念の正しい束縛を守る試験は 0 本」。概念違い 10 行は統合後も 8 行が停止しない。どの方式でも値の偶然一致はここでしか止まらない | AC 実測 | 高 |
| J10 | **D を判定に使わない。使うなら d1〜d4 の下で工程 8 の補助として測るところまで** | §3.1 D の失敗経路 | 論文記載 | 高 |

### 6.2 証拠が足りず判断できないこと

| # | 問い | 足りない証拠 |
|---|---|---|
| U1 | **C(閉じた候補の追加)が A の天井を下げながら E2 を上げないか** | 方式 C の測定が 1 件も無い。§5 でしか答えられない |
| U2 | **B の EDINET 散文での誤りの型** | 将棋の冊子でしか測っていない(文 33/37・値 34/37・form 29/37)。有価証券報告書の文は和数字・単位の混在が違う |
| U3 | **値の偶然一致(型 5)の発生率が他の書類で同程度か** | 1 書類の 3/22・5/60。未使用 2 書類は未開封 |
| U4 | **期間・member の手がかりの規則(抽出 v2)が別文書でも 29/30 の向きに働くか** | 1 書類 |
| U5 | **VERITYGATE の 4 門が論文どおり決定論か** | コード未取得 |
| U6 | **VeriFin の FA=0 に UNSAT 再抽出(V8)がどれだけ寄与したか** | `first_pass_solver_status` の再集計をしていない |
| U7 | **人間に回す割合(E10)と、その仕組みの置き場所** | 仕組みが未設計(D-016) |
| U8 | **AI 経路の再現性(E8)** | 未測定 |

### 6.3 追加調査が必要な論点と、その判断価値

| # | 調査 | 何の判断を変え得るか | 判断価値 | 費用の目安 |
|---|---|---|---|---|
| R1 | **VeriFin 公開 `results/` の first-pass だけの FA/FR を再集計**(コードを実行せず jsonl を読む) | V8 が無くても FA=0 なら「B は再試行なしで成り立つ」の外部証拠になる。V8 が効いていれば J7 の重みが上がる | **高**(B の安全条件の重みを決める) | 読み取りのみ。実行可能性は**未確認**(jsonl に diagnostics が残っているか) |
| R2 | **VERITYGATE の公開コード**(`github.com/sachinkg12/yukti` タグ `veritygate-groundlm-2026-v1.0.0` / Zenodo `10.5281/zenodo.22668710`)を読む | 「宣言に対する決定論的な門」の実装の形(空の宣言の扱い・文字列正規化)が J6 の実装案を変える | 中 | 取得 + 読解 |
| R3 | **FinTagging v5 と v4 の差分** | v5 が検索の天井(表由来 <0.30)や rerank-only の数を更新していれば、J5 の「閉じた候補集合」の必要性の強さが変わる。**設計上の影響はこの 2 点に限る**(FinTagging は検証器を持たないので、工程 4〜8 の判断は変わらない) | 低〜中 | 取得 + 差分読解 |
| R4 | **日本に DQC 相当の決定論的誤り判定基盤が在るか** | 在れば「正解集合」と「概念の一致の試験」の作り方が変わる(J9) | 中 | 公開情報の調査 |
| R5 | **VeriFin の `policy/data` の出典構成**(本文書で初めて数えた: policy 58 / concept 61。source_type は `metric_convention_with_taxonomy_semantics` 23・`financebench_question_defined_metric` 19・`xbrl_taxonomy_or_question_defined_direct_lookup` 11 ほか。CFA への言及は 58 中 22) | 論文脚注 2「CFA 教材から編んだ」は部分的(FinanceBench の質問定義が 19 policy を占める)。registry を「人が承認した線」と見なす重さが変わる | 低 | 済(本文書) |

### 6.4 実験でしか答えられない問い

1. C-f が A1 の停止(`no_subject` / `no_element`)のうち何件を**根拠まで正しい GROUNDED**に変えるか(E5 の量)。
2. 値を伏せた B-m と伏せない B-u で、候補集合が動く Claim が何件あるか(値への依存の大きさ)。
3. 誤候補(値違い)で GROUNDED が増える Claim が **0 か**(J2・J4 の実証)。
4. 型 5 の候補で GROUNDED になる率が A1 の 2/57 を超えるか。
5. D-a と独立判定の κ。
6. AI 経路の 3 回一致率(E8)。
7. 人間に回す割合(E10)。

### 6.5 方式選択を誤ると生じる具体的な失敗

| 誤った選択 | 起きること(証拠) |
|---|---|
| **A だけで被覆を広げようとして語彙を機械的に増やす** | 部分一致の衝突が増えて B3(別の要素)が増える(`N181` 型は語彙の loose 一致が 2 概念を拾った)。根拠まで正しい通過 41.4% は、値ブラインド化で一時的に下がり(封の予測 32.4%)、語彙で戻るかは別の封。FinTagging の数は「語彙を広げれば解ける」を否定する |
| **B を安全条件なしで入れる(AI の宣言を信じる)** | 範囲・期間の誤宣言が**黙って**別の正規 fact に結ばれ、値が合えば GROUNDED(根拠の層の誤受理が増える)。空の宣言が通る(VERITYGATE App. A)。出所ラベルの文字列を信じる(VeriFin V2)。再現性が無く E8 が測れない |
| **C で AI に Core の候補の間を選ばせる、または値を見せる** | 値への依存が「束縛」から「候補生成」へ移るだけで、M1 と同じ偶然一致の経路が残る。測定では「AI が選んだから」と「値が合ったから」を分けられなくなる |
| **D を判定に使う** | 同一候補プールで FA 26〜75/92(VeriFin)。位置バイアス 83%(VERITYGATE)。判定理由が pointer に戻らない(E9 が崩れる) |
| **方式を決める前に J9(概念の契約と試験)を後回しにする** | どの方式でも型 5 の偶然一致を止める場所が無いまま、被覆だけが増える。概念違い 10 行の「自動で通さない仕組み」が無い現状がそのまま拡大する |

### 6.6 次に判断すべき事項(優先順位つき・最大 3 件)

| 順位 | 判断 | 誰が | なぜ先か |
|---|---|---|---|
| **1** | **E2(根拠の層の誤受理)を、方式に関わらず主要指標に据えるか**(E1 の FA と分けて台帳に持つ。独立判定の集合を固定分母にする) | 人間(指標の定義は契約) | これを決めないと §5 の腕を比べる物差しが無い。VeriFin の FA=0 と Audit Core の 41.4% が同じ土俵に乗らない理由でもある |
| **2** | **§5 の比較実験(A0 / A1 / B-m / B-u / C-f / D-a + 反事実)を、封じた予測つきで 1 回行うことを承認するか** | 人間(新規実験 + LLM 費用) | U1〜U3・6.4 の 1〜6 はこれでしか答えられない。既存の封・Golden・main には触れない設計にしてある |
| **3** | **J9: `Pointer` に概念・期間・範囲の欄を持たせ、値以外で一致を検査する Core 封を、方式の選択より先に立てるか** | 人間(Core の契約変更) | どの方式でも型 5 を止める唯一の場所。束縛の順序の封 §6 が既に送っている事項で、本文書はその優先度を上げる根拠(方式横断で必要)を足す |

---

## 7. 主張ごとの根拠一覧(主なもの)

| 主張 | 資料・確認箇所 | 区分 | 確信度 |
|---|---|---|---|
| Core は Claim の値を比較器にしか渡さない | `audit-core/core/py/audit_core/verify.py`(`comparator_fn(tuple(evidence), claim, recipe.contract)`) | AC コード確認 | 高 |
| main の Adapter は値で候補を選ぶ(`hits[0]`)・値で再探索する | `adapters/xbrl/recipes.py:_direct_value_claim`(`:212-214`・`:214-262`、`len(fams)` `:237`) | AC コード確認 | 高 |
| 部分一致・最長一致が別概念を当てる | `instance.py:155-156`、`extract.py:89-105`、`STOP_CAUSE_MAIN_RESULT` §2(B3 28・B2 14) | AC コード確認 + AC 実測 | 高 |
| 誤根拠通過 5/60 = 8.3%、根拠まで正しい通過 162/391 = 41.4% | `GROUNDED_BINDING_RESULT_2026-10-12.md` §1、台帳 L-001 | AC 実測 | 高 |
| 旧 21/18/14 → 規則 4 あり 11/1/38 → RX2 37/2/17 | `INDEPENDENT_JUDGEMENT_51` §2-C、`INTEGRATED_RESULT` §1・§3-1 | AC 実測 | 高 |
| 停止 214 件の原因 A1 131(副次 B2 126) | `STOP_CAUSE_MAIN_RESULT` §2 | AC 実測 | 高 |
| 型 5(値が偶然一致して参照先が違う)3/22 | `measure/material/xbrl/observed_t5.json` | AC 実測 | 高 |
| 概念の正しい束縛を守る試験は 0 本 | `CONTRACT_READING_2026-10-13.md` ③、`TR6_SPEC_JUDGMENT` ③ | AC 実測 | 高 |
| 将棋側 LLM 分解: 文 33/37・値 34/37・form 29/37、aggregate 15 件が潰れ、母集団の昇格 16 件 | `CLAIM_DECOMPOSITION_BOXES_RESULT_2026-10-08.md` §1・§2 | AC 実測 | 高 |
| XBRL 散文で LLM 分解は未測定 | `STOP_CAUSE_CRITERIA_2026-10-09.md`:62(A5) | AC 実測 | 高 |
| 81 語彙が行見出しの 40.0% に当たる・19.5% の見出しが複数要素 | `docs/research/edinet_taxonomy_findings.md` §3・§4 | AC 実測(第 1 段階) | 高 |
| VeriFin: 計画は question + evidence から(answer を渡さない) | `agent.py:90-92,122` | 公開コード確認 | 高 |
| VeriFin: `formula_source` は LLM の自己申告で、門は文字列の集合所属 | `claim_classifier.py:41,179-190`、`agent.py:153`、`find_policy` は `:591` のみ | 公開コード確認 | 高(「他で検証していない」は grep の範囲) |
| VeriFin: linkbase 認可は `"[redacted]"` が証拠に在るときだけ | `agent.py:876-940`(`:893`) | 公開コード確認 | 高 |
| VeriFin: 初回抽出プロンプトに主張値は無い / UNSAT 再抽出には在る | `fact_extractor.py:16-49` / `:51-100`、`agent.py:352-404` | 公開コード確認 | 高 |
| VeriFin: 接地検査 Pass 4 は数字列の存在だけ | `agent.py:1255-1292` | 公開コード確認 | 高 |
| VeriFin: 許容差の相対下限の錨が agent 経路では claimed_value | `answer_spec.py:56-91`、`agent.py:600-628`(`reported_value` を渡さない) | 公開コード確認 | 高 |
| VeriFin: registry は policy 58 / concept 61 | `policy/data/metric_policies.json`・`semantic_concepts.json`(読み取りのみ) | 公開コード確認 | 高 |
| VeriFin: judge FA 26/92・Judge+formula 75/92・PoT 6/92・VeriFin 0/92 | 論文 Figure 4 p.6 | 論文記載 | 高 |
| VeriFin: FR 37〜73 件 / 600 | 論文 §5.2 p.7 | 論文記載 | 高 |
| VERITYGATE: 門は純構造的・空の申告が通った 1 件・敵対的は未評価 | 論文 §3.2、Appendix A、Limitations 5 | 論文記載 | 高 |
| VERITYGATE: judge は 83% でスロット A | 論文 §4.1 | 論文記載 | 高 |
| FinTagging: FinCL 0.1889、rerank-only 0.2144、extreme classification で 0、表由来 Acc@200 <0.30 | 論文 Table 6・7・8、§4.2 | 論文記載(v4) | 高 |
| FinAuditing: FinSM Hit@20 <13%、FinMR 13.86%・CER 70–83%、GPT-4o-mini は「パーサであって決定者でない」 | 論文 §3.3.1、§4.1、§4.3 | 論文記載 | 高 |
| Risk Memos: 生成も検証も決定論・合成 fixture、「SEC-wide performance を主張しない」 | 論文 p.6、Limitations | 論文記載 | 高 |
| 「安全条件を満たした B は C に収束する」 | §3.2 | 独自推論 | 中 |
| 「C が A の天井を下げる」 | §3.1 C | 独自推論 | 低(未測定) |

---

## 8. この文書がしていないこと・Git の状態

- コードの変更 0・実験の実行 0・封の変更 0・Golden の変更 0・採用判断の確定 0。LLM の呼び出し 0(費用 0)。
- 未取得の資料(VERITYGATE / FinTagging / FinAuditing のコード、FinTagging v5)は読んだものとして扱っていない(§0.2・§6.3)。
- 公開コードの「検証していない」系の主張は `grep` の範囲で、**未確認**の可能性を残す(§7 に明記)。
- 本文書は `docs/research/best_mix_design_review.md` として**新規作成**。既存ファイルは変更していない。`git status` は作業前後とも `?? docs/research/` と `?? scratchpad/` の 2 行、`git diff` は空(作業後の確認は本文書の提出時に再実行して報告する)。

---

**追記 2026-10-13(同セッション)**: §6.3 の追加調査 R1〜R4 を実施し、結果と本文書の表への差分を [best_mix_followup_R1-R4.md](best_mix_followup_R1-R4.md) に置いた(本文書の本文は変えていない)。要点: V8 の救済は 3,268 行中 3 行(J7 の代償 ≈ 0)、VeriFin の repair 行で「内部整合だが gold と不一致」が FinanceBench 6/8(E2 の外部証拠)、VERITYGATE の 4 門は決定論だが申告配列のみを検査(U5 解消)、FinTagging v5 は数に変更なし、日本に官製の DQC 相当は見つからず(EC5611W は WARNING)。
