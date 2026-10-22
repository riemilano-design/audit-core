# 5 本の比較表

**取得状況: 5 本すべて原文全文を読んだ。取得できなかった論文は無い。**
ただし 2 番 FinTagging は **v4 を読み、最新の v5(2026-05-17 改訂)は未読**。

**比較の原則(指示 §6)**: 中心は「LLM を何個使うか」ではなく、**主張と証拠の意味的・構造的対応をどの段階で確定するか**。
**数値の比較可能性**: 以下の表に数を書くときは、どのデータ・どの指標かを必ず添える。**異なるベンチの数を直接比べてはいけない**(§5 に注意を集約)。

## 1. 一覧

| | 1 VeriFin | 2 FinTagging | 3 FinAuditing | 4 Risk Memos | 5 VERITYGATE |
|---|---|---|---|---|---|
| 種別 | **検証フレームワーク** | ベンチマーク | ベンチマーク | パイプライン + 評価 | **検証フレームワーク + ベンチ** |
| 公開 | arXiv 2608.10213v1, 2026-08-10 | arXiv 2505.20650v4, v1 2025-05-27 | arXiv 2510.08886v3, **SIGIR 2026 採録** | JACS 3(2) 60-76(査読未確認) | arXiv 2610.00833v1, **GroundLM 2026/EMNLP 採録** |
| 領域 | 米国 10-K / US-GAAP | 米国 10-K / US-GAAP | 米国 XBRL / US-GAAP | SEC 財務諸表データ(合成 fixture) | クレジットカード最適化 / MILP |
| 判定器 | **Z3(SMT)** | なし(測るだけ) | なし(測るだけ) | 決定論的 numeric verifier | **4 つの決定論的な門** |
| 公開コード | **あり(監査した)** | あり(未取得) | あり(未取得) | 論文内の記述のみ | あり(未取得) |

## 2. 第 6 節の比較軸

### 2.1 主張の構造化を誰が行うか

| | 担当 | 根拠 |
|---|---|---|
| VeriFin | **LLM**(Verification Planner が計画 C=(M,F,R,u,ρ,S) を作る)。主張値の抽出も LLM | 論文 p.3 §3.4 |
| FinTagging | LLM(測定対象) | §3.1 |
| FinAuditing | LLM(測定対象)。正解側は DQC + GPT-4o-mini を**パーサとしてのみ** | §3.3.1 |
| Risk Memos | **決定論的レンダラ**が claim(fact/ratio/risk-label)を出す | p.6 |
| VERITYGATE | **LLM が自己申告**(`citedEvidenceIds`/`citedEntities`/`citedNumbers` を strict JSON で宣言) | §3.2 |
| **Audit Core** | **機械**(正規表現で数の主張を抜く経路)+ LLM の自己申告を照合する経路の 2 系統 | `xbrl_probe.py` 系・営業資料 §形 B |

→ **Audit Core と Risk Memos だけが「構造化を LLM に任せない経路」を持つ。** VeriFin・VERITYGATE は構造化を LLM に委ね、**その後の判定だけを決定論にしている**。

### 2.2 証拠候補をどの情報から選ぶか

| | 選び方 |
|---|---|
| VeriFin | 文書 ID で 1 filing に限定 + ハイブリッド検索(dense cos + 字句)+ cross-encoder 再順位。**ただし実装は SEC EDGAR companyfacts API を第 1 の束縛源にしており、当該 filing の外に及ぶ**(コード監査 §5-2) |
| FinTagging | 埋め込み検索で 17,688 概念から上位 200 |
| FinAuditing | DQC の evidence pointer が XBRL 部分 filing と taxonomy chunk を指す |
| Risk Memos | Text RAG = TF-IDF 上位 30 / Structured = 正規 fact map を直接 |
| VERITYGATE | バックエンドが出した証拠グラフ(allowlist)。検索は無い |
| **Audit Core** | 証拠ポインタ + 契約。元データ(EDINET の fact)へ再照合 |

### 2.3 主張値が候補選択に影響するか ― **最重要の軸**

| | 影響するか | 根拠 |
|---|---|---|
| VeriFin(**論文**) | **しない**と明記。「the candidate claim never influences the authoritative filing facts or formulas used to check it」 | 論文 p.3 §3.1 |
| VeriFin(**公開コード**) | **既定経路では影響する。** UNSAT 後の再抽出プロンプトに `Claimed answer value` が入り、再抽出後に SAT なら VERIFIED を返す(`max_unsat_fact_retries=1` が「実験の既定」)。歯止めはプロンプトの禁止文・引用照合・filed value の上書き。加えて非 registry 経路の束縛は抽出値との丸め水準の一致を要求 | `agent/agent.py:352-404`、`fact_extractor.py:51-100`、`xbrl_linkbase.py:663-690`、`887-947` |
| FinTagging | 課題が値の検証でないため該当しない | ― |
| FinAuditing | モデルが報告値と計算値の両方を出す構造なので、モデル内部では影響しうる。**正解側は影響しない** | §3.1.3 |
| Risk Memos | 検証器は正規 fact table に対して**修復する**(保留しない)ので、値は上書きされる | p.6 |
| VERITYGATE | **しない**。門は宣言フィールドの集合所属/文字列一致のみ。「no LLM is involved」 | §3.2 |
| **Audit Core** | **しない**(現在の原則) | ― |

→ **論文の宣言だけで見れば 3 者(VeriFin・VERITYGATE・Audit Core)が同じ原則。コードまで見ると VeriFin は既定で破っている。**
→ **これは「VeriFin と同じことをやっている」と言えない根拠にもなり、「VeriFin が先にやった」と言われたときの応答にもなる。**

### 2.4 証拠を原データから再取得するか

| | 再取得 |
|---|---|
| VeriFin | **する**。filed XBRL fact から値を取り、LLM の抽出値を上書き(`_apply_authoritative_bindings`)。実装は `data.sec.gov` の companyfacts をキャッシュして引く |
| FinTagging / FinAuditing | 該当しない(ベンチ) |
| Risk Memos | **する**(canonical fact table) |
| VERITYGATE | バックエンド出力が唯一の真。外部データへの再取得は無い |
| **Audit Core** | **する**(EDINET の fact) |

### 2.5 概念・期間・単位・エンティティ・スコープを照合するか

| | 概念 | 期間 | 単位 | エンティティ | スコープ(連結/単体等) |
|---|---|---|---|---|---|
| VeriFin | ◯(3 段 + registry) | ◯ | ◯(尺度正規化) | ◯(文書 ID。実装は CIK) | 記述なし(**未確認**) |
| FinTagging | ◯(課題そのもの) | ✗ | △(5 型のみ) | ✗ | ✗ |
| FinAuditing | ◯(FinSM) | △(質問に期間が入る) | **未確認** | ✗ | ◯(次元データの有無が DQC 型に入る) |
| Risk Memos | △(15 tag に限定) | **未確認** | ◯(whole-entity USD に限定) | ◯(CIK/accession) | ✗ |
| VERITYGATE | ◯(claim 型規則) | ✗(領域に無い) | ✗ | ◯(allowlist) | ✗ |
| **Audit Core** | ◯(81 語彙 → 候補要素) | ◯ | ◯(`UNIT_SCALE`) | ◯ | ◯(`ctx_ok` のメンバー・`NonConsolidated` の除外) |

→ **5 軸すべてを照合しているのは VeriFin と Audit Core の 2 つ。** VERITYGATE は門の構造が最も近いが、期間・単位の軸を持たない(領域に無いため)。

### 2.6 計算関係や集計条件を検証するか

| | 検証 |
|---|---|
| VeriFin | **する**。calculation linkbase から f = Σ w_i x_i を作り、filing 自身の calc group を SMT の制約として注入(`_instantiate_constraints`)。許容差は子 fact の `decimals` から積み上げ |
| FinTagging | ✗ |
| FinAuditing | **測る**(FinMR = 報告値 vs calculation 関係からの計算値)。最良 accuracy 13.86%、CER が失敗の 70–83% |
| Risk Memos | **する**(比率を XBRL fact から再計算) |
| VERITYGATE | ✗(Gate 4 は型規則で、算術ではない) |
| **Audit Core** | 契約による照合。**calculation linkbase を使う設計は現在無い**(S100Z4Q1 には cal.xml が 176 arc で存在する ― `edinet_taxonomy_findings.md` §6) |

### 2.7 不明・曖昧な場合に保留できるか

| | 保留 | 形 |
|---|---|---|
| VeriFin | **できる** | **Abstain**。ソルバに到達する前に発生(オペランドが接地できない / 式を認可する出所が無い)。実装は `ambiguous_operation`・`untrusted_formula_source`・`facts_not_found`・`grounding_failed` 等 |
| FinTagging | **できない**(1 概念を必ず選ぶ) | ― |
| FinAuditing | できない。FinMR は「見つからなければ 0」 | ― |
| Risk Memos | **できない**。検証器は修復する | ― |
| VERITYGATE | **できる** | **permissive emission**。落ちた claim をユーザに見せない(出力を削る) |
| **Audit Core** | **できる** | **4 状態**。UNVERIFIABLE / POINTER_NOT_FOUND としてラベルを付けて**残す** |

→ **保留を持つのは VeriFin・VERITYGATE・Audit Core の 3 つ。** 形は 3 通り違う ― 判定を返さない / 出力から消す / **ラベルを付けて残す**。監査証跡としては Audit Core の形が最も情報を保つ(**独自推論**)。

### 2.8 検証結果がどの証拠に基づくか追跡できるか

| | 追跡 |
|---|---|
| VeriFin | **できる**。束縛ごとに concept・期間・単位・accession number・source fact id を記録。違反時は UNSAT core が矛盾する制約の部分集合を名前つきで返す |
| FinTagging / FinAuditing | 該当しない |
| Risk Memos | **できる**(evidence key) |
| VERITYGATE | **できる**。落ちた門と落ちた文字列を誤りメッセージに付ける。グラフは SHA-256 ダイジェストを持つ |
| **Audit Core** | **できる**(証拠ポインタ + 契約 + 4 状態の理由) |

### 2.9 検証の再現性と評価範囲

| | 再現性の担保 | 評価範囲 |
|---|---|---|
| VeriFin | 「接地と認可が決まった後は決定論」(**条件つき**)。temperature 0 | XBRLFiling 600(**calculation linkbase が宣言した計算から逆向きに構成**)+ FinanceBench 67 |
| FinTagging | zero-shot・LM Eval Harness | 142 社・2023–2025・261,457 entity |
| FinAuditing | zero-shot・LM Eval Harness | 1,102 インスタンス・DQC 9 型(DQC 全体の 60.33%)・2020–2024 |
| Risk Memos | **完全に決定論**(生成も検証も)。固定 seed 20230510 | **合成 fixture 1,280 filing / 19,200 fact / memo 300 本**。実物の SEC データでは測っていない |
| VERITYGATE | グラフの SHA-256 ダイジェスト。temperature 0。**事前登録**(共主指標・ペアリング・統計・明示的 non-claim)。クラスタブートストラップ 10,000 反復 seed 42 | 900 インスタンス × 2 設定・**単一領域・単一 seed・3 モデル** |
| **Audit Core** | 決定論。封・sha256・予測を先に書く | 実物の EDINET 書類 |

→ **Audit Core は「実物の材料で測っている」点で Risk Memos より強い。** 一方 **VERITYGATE の事前登録 + クラスタブートストラップ + 明示的 non-claim は、Audit Core の「予測を先に書く」をさらに形式化したもの**で、学ぶところがある(**独自推論**)。

### 2.10 誤受理・誤棄却・保留の測定方法

| | 測り方 |
|---|---|
| VeriFin | TA/FA/TR/FR/Abs を数え、FA・precision TA/(TA+FA)・accuracy (TA+TR)/(TA+FA+TR+FR)・abstention Abs/n・coverage 1−Abs/n。**同一候補プールを全手法で共有**して検証法の差だけを見る | 
| FinTagging | macro/micro P/R/F1、FinCL は accuracy。**誤受理の概念が無い** |
| FinAuditing | HR@k/R@k/Macro-F1(FinSM)、Acc/Macro-F1(FinRE)、**LLM-as-a-judge の accuracy + SER/EER/CER**(FinMR) |
| Risk Memos | numeric exactness・citation precision・ratio MAE / p95。**誤受理・保留の概念が無い** |
| VERITYGATE | **共主指標 2 本**: claim-survival rate と shipped verified claims per instance。門別の失敗件数。**「率だけでは足りない」ことを実測で示した**(mini の r=0 で ungrounded の率が高いのに出力量は少ない) |
| **Audit Core** | 4 状態の件数。**誤棄却(正しい主張を VALUE_MISMATCH にする)の測り方は本調査では確認していない(未確認)** |

→ **VeriFin の「同一候補プール」と VERITYGATE の「共主指標 2 本」は、どちらも Audit Core の測定に足せる形**(**独自推論**。採用・実装は行わない)。

## 3. 「どの段階で意味的・構造的対応を確定するか」のまとめ

```
                主張の構造化        証拠の選択        値の照合        判定
VeriFin         LLM                LLM+決定論        決定論          Z3(決定論)
                                   ↑ UNSAT 後は主張値を見た LLM の再抽出が入る(コード)
VERITYGATE      LLM(自己申告)      バックエンド      決定論          4 門(決定論)
Risk Memos      決定論的レンダラ    TF-IDF/直接       決定論          決定論
FinTagging      LLM(測定対象)      埋め込み検索      ―              ―
FinAuditing     LLM(測定対象)      DQC pointer       ―              LLM-as-judge(FinMR)
Audit Core      機械(正規表現)     契約+ポインタ     決定論          4 状態(決定論)
                 or LLM の自己申告
```

**独自推論**: 「構造化を誰がやるか」で 2 群に分かれる。
- **群 I(構造化も機械)**: Risk Memos・Audit Core の正規表現経路。対象が限定されるが、入力から出力まで決定論。
- **群 II(構造化は LLM、判定は決定論)**: VeriFin・VERITYGATE・Audit Core の自己申告経路。被覆が広いが、**「LLM が何を申告しなかったか」は門が見られない**(VERITYGATE Appendix A の「空の申告は検証器が何も検査できない」1 件が実証)。

## 4. 保留と被覆の交換(数で見る)

| 研究 | 保留の率 | 被覆 | 条件 |
|---|---|---|---|
| VeriFin / XBRLFiling | abstention 1.2% | coverage **98.8%** | ベンチが calculation linkbase から**構成上証明可能**に作られている |
| VeriFin / FinanceBench | abstention 19.4% | coverage **80.6%**(検証可能な 63 件に対する abstain は 14.3%) | 構成が linkbase 由来でない |
| VeriFin / 全 6 モデル FinanceBench | ― | coverage **49.3–82.1%** | モデル依存 |
| VERITYGATE / Sonnet grounded r=1 | ― | claim-survival **54.3%**(= 45.7% が落ちる) | 単一領域 |
| VERITYGATE / mini grounded r=0 | ― | claim-survival **19.7%** | 同上 |

→ **被覆の数は「ベンチの作り方」と「生成モデル」に強く依存する。** Audit Core の被覆の数を他方式の coverage と並べてはいけない(`sales_language_risks.md` にリスクとして記録)。

## 5. 数値の比較可能性についての注意(まとめ)

1. **VeriFin の FA=0 と Audit Core の件数は比べられない。** データ(米国 10-K / 日本 EDINET)・指標(FA/precision / 4 状態)・実験条件(固定候補プール / AI が書いた文)がすべて違う。
2. **Risk Memos の 100.0% は合成 fixture 上・生成も検証も決定論・会計等式が構成上成立。** 一般的な性能として引用すると誤り。
3. **FinAuditing の 13.86% は zero-shot LLM の FinMR accuracy で、LLM-as-a-judge 由来。** かつ最良モデルは SER 71%(形式に従えない)を抱える。「LLM は 14% しかできない」の形で引くと、形式の失敗と計算の失敗を混ぜた数を引くことになる。引くなら「計算誤りが失敗の 70–83%」。
4. **FinTagging の 0.19 は LLM による概念同定の accuracy。** Audit Core は概念同定を LLM にさせていないので、能力の比較対象にならない。引けるのは「この問題が難しい」という方向だけ。
5. **VERITYGATE の survival 率は「検証器の棄却率であって prose の hallucination 率ではない」**(論文の明記)。
6. **VeriFin 論文 Table 2 の数値のうち 4 行は公開 artifact と一致しない。** 引用するなら `results/paper_metrics.csv` 側を引く(`verifin_code_audit.md` §3)。
