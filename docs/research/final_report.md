# 最終報告: 関連論文・公開実装・EDINET タクソノミの調査

実施日: 2026-10-13 / 調査・読解・比較・記録のみ。コード・テスト・台帳・封印・営業資料の変更なし。Git コミットなし。

## 1. 原文を読めた資料 / 読めなかった資料

**5 本すべて原文全文を読んだ。取得失敗・本文抽出不可は 0 件。**

| # | 論文 | 頁 | 抽出字数 | 全文読了の確認 | 版の注意 |
|---|---|---|---|---|---|
| 1 | VeriFin (arXiv 2608.10213v1) | 9 | 44,914 | 空白ページ 0・保存 `.txt` は再抽出と**完全一致** | 単一版 |
| 2 | FinTagging (arXiv 2505.20650**v4**) | 17 | 79,647 | 同上 | **最新は v5(2026-05-17)。v5 は未読・差分未確認** |
| 3 | FinAuditing (arXiv 2510.08886**v3**) | 12 | 72,437 | 同上 | SIGIR 2026 Resource Track 採録 |
| 4 | Risk Memos (JACS 3(2) 60-76) | 17 | 45,070 | 同上 | 査読の質は**未確認** |
| 5 | VERITYGATE (arXiv 2610.00833v1) | 16 | 66,508 | 同上・**画像 0**(図中の文字も抽出できている) | GroundLM 2026 / EMNLP 2026 採録 |

- sha256 は `papers/SOURCES.md` の記録と**再測定で一致**(6 ファイル全件)。
- 参考として beancount.io の FinAuditing 解説記事(HTML、本文 9,939 字)を別ファイルで保存。**原論文と混同していない。**
- **全文読了扱いにしていないもの**: 1〜4 の**図の中の文字**(画像のため抽出不可。1 は p.1/2/6、2 は 7 ページ、3 は p.1/3/6、4 は 7 ページに画像がある)。本文とキャプションから読める範囲に限って記録した。4 番は表の段組が崩れており、**Table 1・5・7 の一部の数は列対応が読み取れないため引いていない**。

## 2. 論文記載の事実 / 独自推論 / 未確認事項

各読解記録に区分を付けて記録した(`paper_notes/01`〜`05`)。要点だけ:

**論文記載(主なもの)**
- VeriFin: 同一候補プール上で FA は Direct 92・judge 26・Judge+formula 75・PoT 6 に対し **VeriFin 0**、precision 100・accuracy 92.2・coverage 98.8(XBRLFiling n=600)。FinanceBench は coverage 80.6%、全 6 モデルで 49.3–82.1%。正しい主張の棄却(FR)は 37〜73 件。
- FinTagging: FinCL accuracy 最良 **0.1889**(上位 200 候補からの再順位付け)。検索の天井 Acc@200 は表由来 **<0.30**。全 taxonomy からの 1 段分類は**全モデル 0 に崩壊**。
- FinAuditing: FinSM Hit Rate@20 **全モデル 13% 未満**、FinRE は GPT-4o 91.82%、FinMR 最良 **13.86%** で **CER が失敗の 70–83%**。正解は DQC ルール由来で GPT-4o-mini は「パーサであって決定者でない」。
- Risk Memos: Structured XBRL RAG で numeric exactness **100.0%**・citation precision 100.0%。**ただし合成 fixture 上で、生成器も決定論的レンダラ**(論文が自ら開示)。
- VERITYGATE: 修復前に mini の claim の **80.3%**、Sonnet の **47.9%** が門を落ちる。Gate 4 が残余の支配(Sonnet で 841/841)。**「schema-level structural correctness, not prose-level faithfulness」**と明記。倫理節に「verified ラベルを完全な事実正確性の保証として提示してはならない」という運用義務。

**独自推論(主なもの)**
- 5 本は「構造化を誰がやるか」で 2 群に分かれ、群 II(構造化は LLM・判定は決定論)は**LLM が申告しなかったものを門が見られない**という共通の穴を持つ。
- 保留の形が 3 通りある(判定を返さない / 出力から消す / **ラベルを付けて残す**)。Audit Core の形が監査証跡として最も情報を保つ。
- 被覆の数はベンチの作り方に強く依存するので、他方式の coverage と並べてはいけない。
- FinAuditing の「最良 13.86%」は SER 71% を抱えた数なので、引くなら「計算誤りが失敗の 70–83%」。

**未確認(主なもの)**
- 標準 EDINET タクソノミ(jpcrp_cor / jppfs_cor / jpdei_cor)の要素数・ラベル数・ラベル役割の種類。zip に無く、外部から取得していない。
- Audit Core を S100Z4Q1 に流したときの実際の束縛結果。
- VeriFin の Evidence Retriever 実装の忠実性、`policy/registry.py` の件数と CFA 教材との対応、`ARTIFACT_MANIFEST.json` の checksum 照合。
- VERITYGATE / FinTagging / FinAuditing の公開コード(取得していない)。
- 日本に DQC 相当の公開された決定論的誤り判定基盤が在るか。
- Audit Core の誤棄却(FR)の現在値。

## 3. 論文と公開コードの一致点・相違点(VeriFin)

対象: `github.com/verifiedfinance/anon` commit `5c49943e8aa43f3dc03c1b2058a73469b22c5c5e`(2026-08-02、"Initial anonymous artifact release")。5,611 ファイル / 162MB / `src/` に Python 87 本。**実行していない。** 詳細は `verifin_code_audit.md`。

**一致した(公開コード確認)**
- 計画は question + evidence だけから作られ、主張値の抽出は計画確定後(`agent/agent.py:90-204`、コメントも明記)。
- XBRL linkbase 経路の束縛は **placeholder の `value=0.0` / `claimed_value=0.0` で実行される**(`agent.py:655-683`)。論文の「value-blind」より強い実装上の保証。
- 曖昧性解消は registry の正規順序で行い、**値の近さで選ばない**(`xbrl_linkbase.py:681-690` にコメントで理由まで書かれている)。1 件に絞れなければ束縛しない。
- filed value が抽出値を上書きする(`_apply_authoritative_bindings` 572-590)。
- 式の信頼できる出所 4 つ以外は abstain(`agent.py:153`)。期間・単位の一致要求、calculation linkbase からの制約注入、Z3 と UNSAT core。

**一致しなかった(公開コード確認)**

| 所見 | 内容 |
|---|---|
| **A(重い)** | 論文「候補主張は検証に使う事実に**一切**影響しない」↔ **UNSAT 後の再抽出プロンプトに `Claimed answer value` が入る**(`agent.py:352-404`、`fact_extractor.py:51-100`)。既定で有効(`max_unsat_fact_retries=1`、コメント「実験の既定」)。再抽出後に SAT なら VERIFIED。歯止めは**プロンプトの禁止文**・引用照合・filed value の上書き。**論文はこのループに触れていない** |
| **B** | 論文の「plausibility check」↔ 実際は**丸め水準の一致要求**(`_display_binding_tolerance` は 0.5 または 0.5×10^−桁)。コメントは「> 3x」と書くが使っていない。加えて `_bind_fact_edgar` の docstring が「No use of the LLM-extracted value for…plausibility」と書くのに同関数が使っている(**コード内部の不整合**) |
| **C** | 符号反転の逃げ道(抽出値の符号で −1 倍)が特定の CF 概念に在る。**論文に符号規約の記述が無い** |
| **D** | 論文「余剰トークン最少で同点処理」↔ **概念解決の経路に実装が無い**(`src/` 全体で該当 0 件)。近い規則(上限 2 トークン)は別モジュール `table_fact_extractor.py:204` に在る |
| **E** | **既定では SMT を LLM が書く**(`deterministic_smt: bool = False`)。決定論レンダラは既定で無効。論文 §3.6 は「誰がコンパイルするか」を述べていない。**論文経路に SMT の構造検査が無い**(`SmtSanitizer` は `pipeline.py` だけが使い、`agent/` から呼ぶ箇所 0 件)。コード自身が「LLM で SMT を再生成すると健全性が壊れる(valid-but-faithless obligation can false-accept)」と記録 |

**論文に記述が無い実装(主なもの)**: **SEC EDGAR companyfacts API を第 1 の束縛源にする**(論文 §3.2 の「1 文書に限定」と緊張する。docstring は「every filing the company submitted に及ぶ」)。FinanceBench 正解の**手裁定 6 件**。FinanceBench haiku run の **stale SMT 54 件の除外**。consensus 系の旗。

**数値の突き合わせ**: claude-haiku・qwen2.5-7b・llama-3.1-8b(XBRLFiling)・fino1・gpt-5.5(XBRLFiling)は一致。**一致しなかったのは 4 行**:
- Qwen3-30B/XBRLFiling: 論文 TA 245 ↔ 正本 TA 304。論文の数は artifact が `noncanonical_conflicts` に「正本に採らなかった古い run」として**自ら記録している値**と完全一致。
- Qwen3-30B/FinanceBench: 論文 FR 10 ↔ 正本 FR 8。**公開されたどの run とも一致しない**。
- Llama-3.1-8B/FinanceBench: 論文 FR 13 ↔ 正本 FR 12。
- GPT-5.5/FinanceBench: 論文は 35/0/10/12 を報告 ↔ `scoring_policy.json` は **"status": "missing", "No FinanceBench GPT-5.5 result directory exists"**。
- Direct LLM/FinanceBench の FA 21(論文図)↔ 18(正本)は、**3 件の abstention を accept 側に数えるかの方法差**。

**重要**: 公開された正本の run の source_path はほぼすべて `det_smt` / `detsmt`。つまり**論文の主結果は「LLM が SMT を書かない」設定で得られている**。これは健全性にとって良い方向の食い違いだが、**論文はその設定を述べていない**。

**一致を前提にしていない**: 上記はすべて「論文記載」と「公開コード確認」を分けて記録した。確認できなかった項目は `verifin_code_audit.md` §6 に「確認不能」として列挙した。

## 4. EDINET タクソノミ調査の結果と未確認事項

対象は `S100Z4Q1.zip`(sha256 `0731a291…`、580,494 bytes)のみ。詳細は `edinet_taxonomy_findings.md`。

**最も重要な範囲の事実**: **zip に入っているタクソノミは提出者の拡張タクソノミだけで、要素宣言は 15 件。** 標準タクソノミは `xsd:import` 10 件で URL 参照されるのみで zip に無い。**外部から取得していない**ので、「EDINET 全体で何語あるか」はこの範囲では答えられない。

母数を 3 つに分けて測った:

| 母数 | 件数 |
|---|---|
| (α) 提出者拡張の要素宣言 | **15**(型: domainItemType 6・monetaryItemType 5・stringItemType 2・textBlockItemType 1・percentItemType 1。abstract true 8 / false 7) |
| (β) linkbase が参照する異なり要素 | pre **736** / cal **144** / def **519** |
| (γ) instance の fact | 出現 **1,220** / 異なり要素 **461** / context **162** / unit **4** |

**ラベル(母数 α)**: `_lab.xml` は役割 2 種のみ ― 標準ラベル(`label`)15・冗長ラベル(`verboseLabel`)15。ラベルを持つ要素 15/15(100%)。**1 要素が複数ラベルを持つのは 15 件全部(最大 2 個)**。ラベル文字列 30 / 異なり 29、2 回現れるもの 1 件(「人材戦略に関する基本方針等」)。`terseLabel`・`totalLabel` 等はこの zip に現れない。英語は `loc` 17 / `label` 31。

**同一ラベル・類似ラベル(母数 γ・iXBRL の行見出し)**: 行見出しつき fact 出現 **880**(全 1,220 の 72.1% ― 残りは私の抽出器が取れなかった分で、**文書の性質ではない**)。異なり行見出し 190 / 異なり要素 255 / 組 284。
- **同じ行見出しが複数要素に対応: 37 / 190(19.5%)**。「計」→ **14 要素**、「その他」→ **12 要素**、「所有株式数(単元)」→ 9、「株主数(人)」→ 8。
- 同じ要素が複数行見出しに対応: 17 / 255(6.7%)。`NumberOfSharesIssuedSharesVotingRights` → 7 見出し、`jppfs_cor:NetAssets` → 当期首残高/当期末残高/純資産合計。

**最長一致の範囲と限界**(本番の `extract.py:subject_of` を読み込んで呼び、`instance.py:facts_for` の述語を写して測った)
- 現行 81 項目(`SUBJECTS_P6`)= 異なり語 78・候補要素名 77・**1 語が複数候補 28 件(最大 3)**。→ **設計上すでに候補生成であって一意の確定ではない。**
- 190 見出しに当てて **語が当たったのは 76(40.0%)**、覆う出現 344/880(39.1%)。当たり 76 の内訳は **exact 34 / loose(部分一致)29 / どちらも当たらない 13**。
- **一意に確定できない型が 2 つ実測できた**:
  1. **部分一致が親子関係の別概念を当たりにする** ― 「流動資産合計」「固定資産合計」「無形固定資産合計」「投資その他の資産合計」がすべて語「資産合計」に当たり、`"Assets" ⊂ "CurrentAssets"` 等で loose も通る。「流動負債合計」「固定負債合計」「負債純資産合計」も同型。**ただし本番は `exact or loose` + `ctx_ok` なので、同じ context に exact が在れば発火しない。これは語彙の弁別力の測定であって束縛結果ではない。**
  2. **より長い見出しが短い語を拾い、別概念になる** ― 「潜在株式調整後１株当たり当期純利益」(希薄化後)が語「１株当たり当期純利益」(基本)を拾う。この書類では要素名が一致せず**保留に落ちる(安全側)**。
- **自分の誤りの記録**: 最初に集合の完全一致だけで測り「不一致 47 件」と出したが、`facts_for` の `SummaryOfBusinessResults` 補正と部分一致を無視した**私の計器の欠陥**で、本番規則では 13 件だった。

**81 項目への追加候補**: 当たらなかった 114 見出しのうち、候補になりそうなのは **9 語前後**(当期変動額合計・自己株式の処分・自己株式の取得・株主資本以外の項目の当期変動額(純額)・株価収益率・資本金・平均臨時雇用者数・潜在株式調整後１株当たり当期純利益・配当性向)。
**足してはいけないものが明確に分かれた**: 「計」「その他」「提出会社」「連結子会社」「所有株式数(単元)」「株主数(人)」「当期首残高」「当期末残高」のような**区分語・期間語**(合計 200 出現超だが概念を決めない)。
**これは 1 書類の観測であり、81 項目は変更していない。**

**calculation linkbase の存在確認**: `_cal.xml` は **loc 186 / 異なり要素 144 / arc 176 / link 役割 8**。VeriFin が式の第 1 の出所に使い FinAuditing の FinMR が正解に使うものが、EDINET の書類にも在る。**使う設計・実装・実験は行っていない。**

**未開封指定の 2 書類**: `S100Z39P.zip`・`S100Z4N9.zip` は同じキャッシュに存在するが、**ファイル名の存在確認以外のアクセスをしていない**(展開・Fact・文章・抽出のいずれも行っていない)。

**未確認事項**: 標準タクソノミの要素数・ラベル数・ラベル役割の種類 / ラベル役割 `terseLabel` 等の有無 / 行見出しが取れなかった 27.9%(340 出現)の中身 / Audit Core の実際の束縛結果 / 語彙の要素名の taxonomy 版の対応(「退職給付に係る資産」で語彙 `RetirementBenefitAsset` ↔ EDINET 2025-11-01 `NetDefinedBenefitAsset`)/ 他書類での再現 / 日本に DQC 相当の基盤が在るか / `_def.xml` の 699 arc で次元メンバーによる曖昧性解消がどこまでできるか。

## 5. 現行の封印済みロードマップへの影響

詳細は `roadmap_impact.md`。

**影響しない(7 項目)**: 判定が主張値に依存しない原則 / 4 状態 / 保留を隠さない / 81 項目の手書き語彙の方針 / 封・sha256・予測を先に書く工程 / Core/Adapter 分離 / 未開封書類の保護。いずれも変更の根拠が出ていない。むしろ**原則 1 は外部の裏づけが増えた**(独立に同じ結論へ到達した設計が 2 件)。

**影響する(文言のレベル・人間の判断)**: 営業表現の空白の主張「決定的な照合 + 判定不能を判定不能として出す + 人が承認した表から行動を選ぶ の 3 つ揃いが無い」のうち、**前 2 本は VeriFin(2026-08)と VERITYGATE(2026-09)が両方持っている**。空白として残るのは **3 本目 + 領域(日本 EDINET)**。これは設計変更ではなく外部に出す文言の変更。

**将来の検討候補(提案のみ。実行していない)**: FR の測定 / 率と量の共主指標 / 同一入力プールでの比較 / 「空の申告」の計数 / calculation linkbase の利用 / 次元メンバーによる曖昧性解消 / AI が構造化候補を出す方式の安全条件 4 つの整理 / 記録の形式(`noncanonical_conflicts` 型)。

**提案しないもの**: AI が構造化候補を提案する方式の**採用**(証拠不足。かつ指示 §6 が採用・実装・実験を禁じている)。**81 項目の変更**(1 書類の観測で「測らずに増やさない」を満たさない)。

## 6. 営業表現上のリスク

詳細は `sales_language_risks.md`。重いものだけ:

| R | リスク |
|---|---|
| **R5** | **「1 + 2 の組み合わせが無い」はもう言えない。** VeriFin・VERITYGATE はどちらも「AI の出力を見て・決定的に判定し・判定不能を出す」。営業資料が根拠にした 3 分類(形式手法/監査系/評価系)のどれにも入らない |
| **R1** | **「判定に AI を使わない」の「判定」の範囲が伝わらない。** 形 B では**どの数を主張として立て、どの証拠を指すかを LLM が決めている** |
| **R2** | **LLM が申告しなかったものは照合されない。** VERITYGATE が同じ性質を論文の限界として明記し、「申告が空で検証器に検査対象が無かった」実例を挙げている |
| **R4** | **決定論は再現性の主張であって正しさの主張ではない。** VERITYGATE は倫理節で「verified ラベルを完全な事実正確性の保証として提示してはならない」を運用義務にしている |
| **R6** | **GROUNDED は「正しい」ではなく「提出された XBRL の fact と一致した」。** Risk Memos Limitations が「XBRL fact を gold として扱うのは実験の都合。実運用では訂正報告や taxonomy の選択の余地がある」と明記 |
| **R11** | **「決定的」が敵対的入力への強さと読まれる。** VERITYGATE は「allowlist を知るモデルは検証を通る誤誘導を作れる」と明記し敵対的頑健性を未評価としている。Audit Core も同じ性質 |

**論文を根拠に言ってはいけない表現**: 「世界初」「他方式より優れている」「誤受理ゼロが保証される」「論文でも 100% が出ている」「LLM は財務監査が 14% しかできない」「VeriFin は Qwen3 で TA 245」(**公開 artifact が正本でないと自ら記録している数**)「Fin-o1-8B」(artifact が 8B/30B の断定を禁じている)。

**今回の調査で裏付けが増えた唯一の差別化点**: **実物の開示書類に対して決定論的な照合を回している実装を持っていること。** Risk Memos は環境の制約で合成 fixture に落ち、VERITYGATE は単一領域・単一 seed、FinTagging/FinAuditing は検証器を持たないベンチ。ただし **Audit Core の書類数は 3 件**であり「実物で広く測った」とは言えない。

## 7. 作成・変更したファイル一覧

**新規作成(すべて `docs/research/` 配下。既存ファイルの上書きは 0 件)**

| ファイル | 内容 |
|---|---|
| `docs/research/paper_notes/01_verifin.md` | 読解記録 1(12 項目 + 根拠箇所表) |
| `docs/research/paper_notes/02_fintagging.md` | 読解記録 2 |
| `docs/research/paper_notes/03_finauditing.md` | 読解記録 3 |
| `docs/research/paper_notes/04_risk_memos.md` | 読解記録 4(前セッションの疑義 3 点の照合を冒頭に置いた) |
| `docs/research/paper_notes/05_veritygate.md` | 読解記録 5 |
| `docs/research/paper_comparison.md` | 5 本の比較表(第 6 節の 10 軸) |
| `docs/research/verifin_code_audit.md` | 公開実装の監査(所見 A〜E + 数値突き合わせ) |
| `docs/research/edinet_taxonomy_findings.md` | EDINET 限定調査 |
| `docs/research/roadmap_impact.md` | ロードマップへの影響(4 区分) |
| `docs/research/sales_language_risks.md` | 営業表現のリスク |
| `docs/research/final_report.md` | この文書 |

**前セッションが作成し、本セッションでは変更していない**: `docs/research/papers/`(PDF 5 + HTML 1 + 抽出テキスト 6 + `SOURCES.md`)、`docs/research/papers/verifin_code/`(クローン)。

**変更したファイル: 0 件。** `docs/research/` の外に書き込みをしていない。

## 8. 調査以外の変更がないことの最終確認

| 確認項目 | 結果 |
|---|---|
| 調査前の `git status --porcelain` | `?? docs/research/` / `?? scratchpad/`(どちらも調査開始時点で既に未追跡で存在) |
| 調査後の `git status --porcelain` | **同じ 2 行**。新しい行は出ていない |
| `docs/research/` と `scratchpad/` 以外の変更 | **0 件**(`git status --porcelain` から両者を除くと空) |
| 追跡ファイルの変更(`git diff --stat`) | **空** |
| ステージ(`git diff --cached --stat`) | **空** |
| **私が作った Git コミット** | **0 件**(`git log` の直近 5 件はすべて別セッションの採用条件・監査の作業。時刻 08:51〜09:18 JST) |
| HEAD の移動 | 調査開始時 `375419ba` → 終了時 `6582864`。**これは並行セッションのコミットによる移動で、私の作業ではない**(コミットメッセージは「採用条件の試験 patch の独立監査」系) |
| プロジェクトの `scratchpad/` | 調査前と**同じ 5 ファイル**(他セッションの blind 回答、mtime 2026-10-12)。**私は書いていない**(作業は `/private/tmp/.../scratchpad` で行った) |
| `verifin_code/` の改変 | `git -C docs/research/papers/verifin_code status --porcelain` が**空** = 公開コードは無改変 |
| 公開コードの実行 | **していない**(`pytest`・`paper_scoring.py`・`build_publication_artifacts.py` のいずれも未実行) |
| 依存関係のインストール | **していない** |
| 未開封指定 `S100Z39P` / `S100Z4N9` | **触れていない**(ファイル名の存在確認のみ。展開・Fact・文章・抽出のいずれも行っていない) |
| 既存テスト・性能実験・Golden・予測・封印の変更 | **0 件** |
| 新規実験・再現実験・ベンチマーク実行 | **0 件** |
| 既存台帳・仕様書・営業資料の変更 | **0 件**(`~/Desktop/sgogi-coach-handoff/` は読み取りのみ) |
| 論文の記述と独自推論と Audit Core 実測の混同 | 各文書で「論文記載 / 公開コード確認 / Audit Core 実測 / 独自推論 / 未確認」の区分を付けた |

## 9. 完了条件の自己点検(満たせなかった項目を含む)

| 完了条件 | 判定 |
|---|---|
| 原文の読解状況が資料ごとに明示されている | **満たした**(§1。図中の文字・4 番の表の段組は読めていないことを明記) |
| 論文の主張と実験条件が原文の根拠箇所に結び付いている | **満たした**(各読解記録の §12 に根拠箇所表) |
| 公開コードの確認範囲がファイルパス・コミット付きで記録されている | **満たした**(`verifin_code_audit.md`。commit `5c49943e…`) |
| 論文とコードの一致を仮定していない | **満たした**(一致/不一致/確認不能を分けた。所見 A〜E) |
| EDINET 調査が指定書類のタクソノミファイル内に限定されている | **満たした**。ただし**指示が想定した「標準タクソノミの語彙の棚卸し」は、zip に標準タクソノミが無いため実施できなかった**(§4 に明記)。代わりに文書内の 3 母数で測った |
| 未開封指定の 2 書類に触れていない | **満たした** |
| Audit Core の既存実測値と論文の報告値を混同していない | **満たした**(`paper_comparison.md` §5 に比較可能性の注意を集約) |
| 封印済みロードマップの変更・実装・新規実験を行っていない | **満たした** |
| `docs/research/` 以外に変更がない | **満たした**(§8) |
| Git コミットを作成していない | **満たした**(§8) |

**未完了・未確認として明記するもの**
1. **標準 EDINET タクソノミの語彙の棚卸しは未実施**(zip に無く、外部取得を禁じられているため)。指示 §5 の項目 2・3 は母数 α(15 件)でしか答えられていない。
2. **FinTagging v5 未読**(v4 を読んだ)。
3. **VeriFin の公開コードのうち Evidence Retriever・`policy/registry.py`・checksum 照合は未確認。**
4. **VERITYGATE / FinTagging / FinAuditing の公開コードは未取得。** 3 本については**論文とコードの一致を検証していない**。
5. **Audit Core の FR(誤棄却)の現在値は確認していない。**
6. **4 番の査読の質は未確認。**

## 10. 人間の判断を仰ぐ点

1. **営業表現 E5 の空白の主張を狭めるか**(`sales_language_risks.md` §2、`roadmap_impact.md` P1)。外部へ公開する判断。
2. **E1〜E4 に形 B の 1 文を添えるか**(P2)。
3. **「合っている」を「提出された XBRL の fact と一致している」に替えるか**(P3)。
4. **約束の表に「敵対的な誘導の対策ではない」を足すか**(P4)。
5. **`docs/research/papers/verifin_code/` の 162MB をどうするか**(次節)。

## 11. VeriFin コードの保管場所について(指示 §1.3 への回答)

**移動していない。既存状態を維持した。** 理由:

1. **既存の保管ルールが確認できなかった。** `.gitignore` は `node_modules/`・`dist/`・`build/`・`.DS_Store`・`*.log`・`.env`・`.env.local`・`scripts/playtest/out/` の 8 行で、研究材料や大きな外部クローンに関する規則は無い。`docs/` 配下に `docs/research` を扱う既存の記述も無い(今回新設)。
2. **プロジェクトの `scratchpad/` へ移すと、2 つの規定に触れる。** (a) 指示 §2 が「`docs/research/` 以外は読み取り専用」と定めており、`scratchpad/` への書き込みはその外。(b) `scratchpad/` は**他セッションが使用中**(2026-10-12 22:34〜23:05 の blind 回答 5 ファイル)で、162MB を置くと並行作業に影響しうる。加えてプロジェクトの記録は「scratchpad は消える」と明記している。
3. したがって指示 §1.3 の「移動先が不明、または移動が他のファイルに影響する可能性がある場合は、移動せずに停止して報告する」に該当する。**`results/` も削除していない。**

**現状**: `docs/research/papers/verifin_code/` に 162MB(`results/` 140MB・`.git` 9.7MB)。親リポジトリでは `?? docs/research/` として未追跡。**コミットしていない。** 読解に必要なのは `src/`(1.5MB)・`tests/`(508KB)・`RUNBOOK.md`・`ARTIFACT_MANIFEST.json` と、数値突き合わせに使った `results/paper_metrics.csv`・`results/scoring_policy.json`・`results/MODEL_IDENTITY_CAVEAT.md`・`results/manual_adjudications.json`(いずれも小さい)。**`results/` の 140MB の大半(per-question の SMT トレース等)は本調査では読んでいない。**

人間の判断を仰ぐ選択肢: (a) そのまま置く、(b) `.gitignore` に追加する、(c) `results/` の大きい部分を削る、(d) リポジトリの外へ移す。**どれも本セッションでは実行しない。**
