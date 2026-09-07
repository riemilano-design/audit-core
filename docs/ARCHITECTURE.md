# 構造と責務境界

## この文書の位置づけ

このアプリが**どういう構造でできていて、どのモジュールが何に責任を持つか**を固定する正本である。「何を実現しようとしているか」は [PROJECT_VISION.md](PROJECT_VISION.md)、開発の進め方は [PHASES.md](PHASES.md) が担当する。

AIエージェントは、この文書に書かれた責務境界を根拠に実装してよい。**新しい構造案を提案することは自由だが、人間の承認なしに責務境界を変更・確定してはならない。**

この文書は、既に実装され人間の承認を経た構造を記録したものである。未確定の事項は「9. 未確定事項」に明示し、確定しているかのように書かない。

---

## 1. 全体構造

```
apps/web/                     ブラウザ。表示と入力のみ
  ├ main.ts                   DOM描画・盤面クリック操作
  ├ gameApi.ts                サーバーとの通信・型定義・表示条件の純粋関数
  ├ sfenBoard.ts              SFEN → 盤面配列(表示用)
  └ style.css
        │  HTTP (JSON)
        ▼
apps/server/
  ├ server.ts                 HTTPルーティング・対局状態の保持(単一対局)
  ├ api/stateResponse.ts      レスポンスの組み立て(配線のみ)
  ├ analysis/                 コーチング判断のすべて。純粋関数が原則
  ├ notation/                 日本語表記への変換(マス目・棋譜)
  ├ game/gameSession.ts       1局分の対局進行
  ├ rules/                    将棋のルール(shogiopsへの薄い委譲)
  └ engine/                   USIエンジンとの通信
        │
        ▼
data/                         将棋知識の唯一のソース(shapes/openings/intents/explanations)
```

---

## 2. 9段階パイプラインとモジュールの対応

[PROJECT_VISION.md](PROJECT_VISION.md) 4.2 の9段階に対し、実装は次のように対応する。段階の詳細な意味は [DATA_MODEL.md](DATA_MODEL.md) を参照。

| 段階 | 主な担当 | 備考 |
|---|---|---|
| ① 局面 | `rules/sfenPosition.ts`(shogiops) | データとしては持たない |
| ② 戦型・形 | 形: `analysis/shapeDetector.ts` → `shapeFormationAnalyzer.ts` / 戦型: **未実装** | 形は静的一致に「実際にその形へ向かう動きが観測されたか」の証拠を足す。戦型の認識モジュールはまだ無い(`data/openings/` は実行時に読み込まれていない) |
| ③ 相手の意図 | `analysis/intentDetector.ts` | `data/intents/` を照合。断定できなければ申告しない |
| ④ 相手の次の狙い | `analysis/intentDetector.ts` + `explanationGenerator.ts` | |
| ⑤ 自分の目的 | `analysis/targetPurposeSelector.ts` | 静的データを持たず実行時に算出 |
| ⑥ 目指せる形 | `analysis/shapeGraphRanking.ts` | 上位3件をユーザーに提示し、1位を唯一の正解として強調しない |
| ⑦ 代表的な候補手 | `analysis/routePlanner.ts` | Phase 6 Unit 1 以降はこちらが本番経路 |
| ⑧ その手の目的 | `analysis/candidateMoveSafetyCheck.ts` → `candidateMoveExplanation.ts` | エンジンのMultiPVと突き合わせるのはここだけ |
| ⑨ 初心者向け説明 | `analysis/explanationGenerator.ts`、および Phase 6 の各 `*Explanation.ts` | |

補助モジュール: `shapeRepository.ts` / `intentRepository.ts`(`data/` の読み込みのみ)、`moveHistory.ts`(指し手履歴の再生)、`signatureEvidence.ts`(履歴内の一致判定)、`pieceMapping.ts`(日本語駒名 ⇔ shogiops の Role)。

### ②〜④は確定値ではなく「認識(仮説)」

戦型(②)・陣形(②)・狙い(③④)は、いずれも**その時点までの指し手から観測できた範囲の仮説**として、同じ形で扱う。持つ情報は `status`(`none` / `forming` / `matched`)・内部スコア・根拠(`evidence`: 何手目のどの指し手で観測されたか)である。`matched` は「そのパターンの全シグネチャが観測された」という**観測事実**であって、「相手の戦法はこれである」という断定ではない。**確定値としては扱わない。** 意味の定義は [DATA_MODEL.md](DATA_MODEL.md)。

認識の対象は自分・相手の両方とする。現状は陣形が自分側(`shapeFormationAnalyzer.ts`)、狙いが相手側(`intentDetector.ts` が相手の色を前提にしている)だけを扱い、戦型はどちらも扱っていない。`intentDetector.ts` の相手色の前提の解消と、戦型認識モジュールの新設が必要になる。着手時期は [PHASES.md](PHASES.md) を参照。

---

## 3. 将棋エンジンの位置づけ

```
routePlanner(⑦候補手を列挙)
        ↓
candidateMoveSafetyCheck(MultiPVと突き合わせ、悪手でないかを確認)
        ↓
candidateMoveExplanation(⑧その手の目的)
```

- エンジンに触れてよいのは `engine/` と、`analysis/candidateMoveSafetyCheck.ts` からの参照評価のみ。
- **エンジンの評価値を根拠に「この手が良い/悪い」とユーザーへ述べない。** 一方で、安全確認を経ていない候補手をユーザーに見せない([PROJECT_VISION.md](PROJECT_VISION.md) 4.3)。
- エンジン探索は対局進行(`bestmove`、高優先度)と参考評価(MultiPV、低優先度)が同一プロセスへ同時に `go` を送らないよう、`engine/prioritizedEngine.ts` で直列化する。
- 参考評価は `POST /api/game/move` のレスポンスをブロックせず、バックグラウンドで計算して `server.ts` のキャッシュへ入れる。完了前は `candidateMoveState: "pending"`。

---

## 4. 責務境界の原則

以下は既存実装が一貫して守っている約束であり、新しいモジュールもこれに従う。

### 4.1 将棋のルール判定は `rules/` に集約し、自作しない

合法手判定・局面遷移・終局判定・王手判定は `rules/` が shogiops へ委譲する。他の層はルールを再実装しない。局面遷移は必ず `rules/applyMove.ts` を通す(合法性確認込みの唯一の入口)。

### 4.2 将棋知識は `data/` が唯一のソース

`shapeRepository.ts` / `intentRepository.ts` は読み込みと最低限の形式チェックのみを行う。判定ロジックの中に将棋知識をハードコードしない。

### 4.3 「事実の抽出」と「文言」を分離する

Phase 6 以降のモジュールは必ず対になる。

```
*Detector.ts        機械的に確定できる事実だけを列挙する(純粋関数・決定的)
*Explanation.ts     事実 → 初心者向け文言への対応表。新しい判断をしない
```

文言側に判断を持ち込まない。判定側に文言を持ち込まない。

### 4.4 判定・文言生成はサーバー、web は表示のみ

web が持ってよいのは「表示するかしないか」程度の純粋な条件判定だけで(例: `gameApi.ts` の `shouldShowPlanChangedNotice` / `shouldShowNextConsiderations`)、文言の生成・加工・並び替え・フィルタ・将棋の判断は持たない。サーバーが確定した文字列をそのまま描画する。

### 4.5 日本語表記は `notation/` に集約する

内部データはUSI形式のまま扱い、表示のためのマス目表記(`8h`→`８八`)・棋譜表記(`7i7h`→`７八銀`)は `notation/` が担当する([DATA_MODEL.md](DATA_MODEL.md) の座標表記の規約)。棋譜表記の生成ロジックは自作せず shogiops へ委譲する。

### 4.6 コーチ機能の失敗で対局を止めない

説明生成・候補手計算が想定外の理由で失敗しても、盤面・指し手は動き続ける。`api/stateResponse.ts` の `safe*` ラッパーがこの境界を担う(失敗時は `console.error` と、空・`undefined` などの穏当な値へのフォールバック)。

### 4.7 断定できないことは断定しない

判定できない場合は「未分類」「表示しない」に落とす。推測で理由や駒種を補わない。

---

## 5. Phase 6 の Unit 責務境界

Phase 6 は「毎手説明」を4つの Unit に分けて実装した。**Unit をまたぐ変更は責務境界の変更にあたり、人間の承認が必要である。**

| Unit | 扱う情報 | 入力 | 代表モジュール |
|---|---|---|---|
| Unit 1 | 選んだ形への**経路**と、現在局面で指せる最初の一手・準備手 | 現在局面 | `routePlanner.ts`、`notation/japaneseSquare.ts` |
| Unit 2 | 直前の一手による**形・経路の変化**(差分) | 着手前の局面 + 現在局面 | `moveOutcomeDetector.ts` / `moveOutcomeExplanation.ts` |
| Unit 3 | 直前の一手で**盤面に起きたこと**(捕獲・王手・成り) | 着手前後の各局面遷移 | `boardEventDetector.ts` / `boardEventExplanation.ts` |
| Unit 4 | **現在局面の静的な状態**の整理(差分ではない) | 現在局面のみ | `nextConsiderationDetector.ts` / `nextConsiderationExplanation.ts`、`notation/japaneseMove.ts`、`rules/gameStatus.isInCheck` |
| 対局経過ブロック(新規・未実装) | **対局開始から現在までに認識(仮説)がどう変わってきたか**と、その根拠になった手 | 指し手履歴(および対応する各中間局面) | 未実装。Phase 6 の Unit ではない |

境界の要点:

- Unit 2・3 は差分を扱い、Unit 4 は差分を扱わない(着手前の局面・`lastMoveOutcome`・`lastBoardEvents` を使わない)。
- Unit 4 は Unit 1〜3 の出力を**読むだけ**で、変更しない。
- 同じ事実を複数の Unit が重ねて表示しない(重複が生じた場合は表示側で抑止し、判定ロジックは変更しない)。
- いずれの Unit もエンジン・LLM に依存しない。決定的な純粋関数である。
- **対局経過ブロックを Unit 4 に混ぜない。** Unit 4 は現在局面の静的な状態だけを扱い、対局全体の経過を扱わない。Unit 1〜4 の責務・文言・実装は、この新ブロックの追加によって変更しない。

### 対局経過ブロック(「ここまでの対局で分かってきたこと」)

Phase 6 の4 Unit とは別の新しい表示ブロックとして設ける。画面上の表示順は次で確定している。

```
直前の一手(Unit 2・3)
  → ここまでの対局で分かってきたこと(新規)
  → 今の局面で分かっていること(Unit 4)
  → 候補手
```

このブロックが述べてよいのは次の3種だけである。

1. 認識が変わった時点と、その根拠になった手
2. 現在の認識の `status` を、断定しない言い回しで述べたもの
3. 何も認識できていない場合の穏当な文

評価語・推奨・「だからこう指すべき」・エンジンの評価値・一致率などの数値・相手の心理は述べない(認識結果を根拠に手を勧めるロジックは導入しない)。

このブロックは**状態を持たない**。`server.ts` にモジュール変数を増やさず、指し手履歴から毎回再計算して認識の時系列を再構成する。決定的な純粋関数であり、エンジンにも LLM にも依存しない。

---

## 6. HTTP API とデータフロー

| メソッド | パス | 用途 |
|---|---|---|
| GET | `/api/game` | 現在の対局状態とコーチ表示一式。新たなエンジン解析は開始しない |
| POST | `/api/game/new` | 新規対局。`?scenario=` は検証用 |
| POST | `/api/game/move` | ユーザーの着手 → 相手の応手 → 解析 → 応答 |
| POST | `/api/game/target-shape` | 目標形の選択 |

`POST /api/game/move` の流れ:

```
ユーザーの着手(合法性確認)
  → 相手の応手(エンジン、高優先度)
  → Phase3 計画崩れの検知・理由分類
  → Unit 3 盤面イベント / Unit 2 直前の一手の変化
  → ②〜⑦ + Unit 1 経路 + Unit 4 現在の状態(いずれもエンジン不要)を組み立てて応答
  → 応答後にバックグラウンドで⑧(MultiPV参考評価)を計算しキャッシュ
```

対局状態・目標形の選択・直前の解析結果は `server.ts` のモジュール変数が保持する(同時に1対局のみ)。新規対局・目標形変更のときは、前の状態についての説明が残らないようにリセットする。

### 公開境界(内部状態とAPIレスポンスの分離)

`GameState`(`game/gameSession.ts`)は**サーバー内部の対局状態**であり、相手AIの制御に関わる情報を含む。Phase 7 Unit 1 では相手AIが選んだ狙いをユーザーに開示しないため([PHASES.md](PHASES.md) Phase 4「その後の変更」・[SCENARIOS.md](SCENARIOS.md))、内部状態をそのまま公開しない。

```
GameState(内部・非公開)
  → toPublicGameState()      ← 唯一の変換境界。許可リスト方式
  → PublicGameState
  → StateResponseBody(+ status / coach / legalMoves / moveHistoryJapanese / plan)
  → browser
```

- **公開してよい情報**: 盤面・指し手履歴・日本語棋譜・終局状態・合法手・コーチ出力(`coach`)・目標形と経路と候補手(`plan`)
- **公開しない情報**: 相手AIが選んだ狙い・制御手順・次に指す制御候補・選択理由・`openings.scenario`・`recognition_pattern` の生データ・`review_status`・`verification_*`・エンジン名やバージョンや探索条件・[KIND3_VERIFICATION.md](KIND3_VERIFICATION.md) の Phase A〜F の検証結果・エンジン評価値の生値
- **認識側と制御側を区別する**: `coach` が述べる戦法名・狙いの説明は**認識側**(指し手の観測から推定した仮説)の出力であり、[PHASES.md](PHASES.md) Phase 1 の完了条件により公開する。非公開にするのは**制御側**(相手AIが実際に選んだもの)である。同じ戦法名でも出所によって扱いが異なる
- `forcedPliesUsed` は内部制御寄りの情報だが、既存のAPIレスポンスに含まれており、最小変更のため公開のまま維持する(人間承認済み)。**狙いの選択手順が確定した時点で、選ばれた狙いの間接的な手がかりにならないかを改めて検討する**(Unit 1 の実装STEP)
- **クライアントが相手AIの制御状態を指定できる経路を作らない。** 現在の `POST /api/game/new?scenario=` は検証用の暫定経路であり、その扱いは Unit 1 の実装STEPで決める
- `verification_*` やエンジンの検証記録は、将来 [KIND3_VERIFICATION.md](KIND3_VERIFICATION.md) Phase F で人間が読む必要があるが、読み手は開発者であって対局中のユーザーではない。**通常のゲームAPI(`/api/game*`)では返さない。** 提示手段は別途決める

---

## 7. テストの方針

判定ロジックは SFEN を入力に取る純粋関数として実装し、局面を入力・判定結果を期待値とする単体テストで固定する。詳細は [TESTING_STRATEGY.md](TESTING_STRATEGY.md)。

**テストが通ったことは、仕様上の完成を意味しない**([PROJECT_VISION.md](PROJECT_VISION.md) 3.)。ブラウザでの実測が必要な変更は、実測を経ずに完了として扱わない。

---

## 8. 変えない構造上の約束

人間の承認なしに変更しない。

1. 将棋のルール判定を `rules/` の外で再実装しない
2. 将棋知識を `data/` の外にハードコードしない
3. エンジンを「最善手の提示」に使わない(安全確認に限る)
4. LLM に将棋の事実判断をさせない(役割は言い換えのみ)
5. 判定・文言生成を web 側に持ち込まない
6. 「事実の抽出」と「文言」を同じモジュールに混ぜない
7. コーチ機能の失敗を対局本体へ波及させない
8. Unit の責務境界をまたぐ変更を単独で行わない
9. 内部状態と公開状態の境界を**許可リスト方式**で保つ(公開してよいものを明示列挙し、除外リスト方式にしない)。`toPublicGameState()` を通らない公開経路を作らない

---

## 9. 未確定事項

以下は現時点で決まっていない。決まっているかのように扱わないこと。

- **Phase 7 以降の構造**: [PHASES.md](PHASES.md) の Phase としての計画は Phase 6 までであり、その先の構造は未定。戦法認識を対局経過から形成するという方針そのものは人間の承認を経て確定している([PHASES.md](PHASES.md))が、それを実現するモジュール構成・着手順は未確定である。
- **対局経過の再計算に必要な中間局面**: 指し手履歴を途中まで切り詰めて認識を再計算する際、対応する中間局面のSFENも同時に用意する必要がある(独立監査の指摘)。用意の方法は実装STEPで具体化する。
- **`analysis/pathPlanner.ts` の最終的な扱い**: Phase 6 Unit 1 で `routePlanner.ts` へ切り替えたため本番経路からは使われていないが、削除するかどうかは未決(現状は温存)。
- **複数対局の同時進行**: 現在は単一対局のみ。設計していない。
- **対局シナリオ(AI序盤制御)**: [SCENARIOS.md](SCENARIOS.md) に将来設計があるが未実装。`engine/scenarioOpponentOpening.ts` は検証用であり、本番機能ではない。相手AIに狙いを持たせる(ユーザーには開示しない)という方針は人間の判断により確定したが、実装方式は未確定([SCENARIOS.md](SCENARIOS.md))。制御方式(序盤の数手を `scenario` の手順で強制進行させ、以降はエンジンに任せる)とスキーマ構造は人間の承認を経て確定したが、**手順そのものの内容・毎局の選択方法・ランダム性の有無は引き続き未確定**である([DATA_MODEL.md](DATA_MODEL.md)・[KIND3_VERIFICATION.md](KIND3_VERIFICATION.md))。
- **shape座標の一次資料**: 一部が未検証。`data/` の `source` に経緯が記録されているため、勝手に修正しない。
- **将来拡張**(対局後の振り返り・学習履歴・複数戦型)の構造: [PROJECT_VISION.md](PROJECT_VISION.md) 5. のとおり MVP 対象外で、設計していない。
