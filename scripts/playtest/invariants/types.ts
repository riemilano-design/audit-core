// 不変条件(draft)の共通の型。docs/PLAYTEST_LOOP_PROPOSAL.md 4.3・4.4・4.5・STEP T-2計画書。
//
// 【このファイルがやること】
// - Invariant / Finding / RecordLine の型定義だけ。判定ロジックは各 i*.ts に置く。
// - statusは"draft" | "approved"のリテラル型を定義するが、本STEPで作る5件は
//   すべて"draft"。"approved"にする操作は人間承認事項であり、このファイル自体には
//   "approved"の値を一切書かない(4.5 規則1)。
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・評価・閾値・文言。
// - 本番の型(apps/server/src/api/stateResponse.ts)の複製・改変。ここでは import する
//   だけで、必要最小の追加型(RecordLine等、JSONLの入れ物)のみを新設する。

import type { StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import type { EngineReference } from "../lib/engineReference.js";
import type { SearchPvObservation } from "../../../apps/server/src/analysis/searchPv.js";

/** docs/PLAYTEST_LOOP_PROPOSAL.md 4.4 の6型。
 * STEP T-6(B-1、人間承認済み。docs/COVERAGE_AND_OUTCOME_PROPOSAL.md 7.1)で
 * 7型目「結果」を追加した(局面・エンジン評価に基づく損得の観測。他の6型と異なり、
 * 説明の言い方ではなく実際に起きた結果を対象にする)。 */
export type InvariantType = "沈黙" | "矛盾" | "断定" | "未説明用語" | "盤との不一致" | "陳腐化" | "結果";

/** 4.5の概念の境界: draft(AIが自由に追加してよい) / approved(人間だけが有効化する)。
 * 本STEP(T-2)で作る5件はすべてdraft(コードにapprovedの値は書かない)。
 * 【STEP 5-1(2026-09-11人間承認)】I-1・I-2はSTEP 5-1でapprovedになった
 * (i1-silent-exclusion.ts・i2-played-candidate-mismatch.ts参照)。approvedにする
 * 操作自体が人間承認事項であることは変わらない(このファイルの判定ロジックには
 * 影響しない)。 */
export type InvariantStatus = "draft" | "approved";

/** T-1のJSONLの"kind":"record"行(1行分)。replay.ts / scripts/playtest/README.md の
 * JSONL形式そのまま。responseはbuildStateResponseWithPlanの戻り値そのまま。 */
export interface RecordLine {
  kind: "record";
  ply: number;
  sfen: string;
  senteMove: string | null;
  goteMove: string | null;
  phase: "immediate" | "ready";
  elapsedMs: number;
  response: StateResponseBodyWithPlan;
  /** STEP T-7(A-2)。ready行のみに付く、エンジンの参考評価(ハーネスの観測)。
   * immediate行には付けない(optional)。測っていない・測れない場合はnull。
   * **これは③が使った探索ではない**(ハーネスが別に測ったもの。2026-09-12に
   * 両者を同一視して3行を誤読した)。 */
  engineReference?: EngineReference | null;
  /**
   * STEP U6-L。本番が③⑤を作るのに実際に使った探索の読み筋(1探索1本につき1件)。
   *
   * 【3つの状態を3つの値で表す。一つの値に二つの意味を持たせない】
   * - `undefined`(欄が無い) … **U6-L より前に取った記録**。ここが optional なのは
   *   書き手が忘れうるからではなく、過去のファイルにこの欄が無いからである
   *   (書き出す側 lib/recorder.ts では **ready行の必須欄**で、忘れればtscが止める)
   * - `null` … **本番の解析そのものが失敗した**(safeComputeReachablePlan が
   *   undefined を返した)。**測れなかったのであって、0本だったのではない**
   * - `[]` … **本番は解析を完了したが、読み筋が1本も載らなかった**
   *
   * 当初は解析の失敗も `[]` にしており、**「失敗した」と「測って0本」が同じ値だった**
   * (2026-09-13 の独立監査の指摘、必須3。既知事項 P-23 と同じ型)。
   * STEP 5-F の focusTextState と同じ理由で分けている。
   *
   * 【`[]` はまだ二つの意味を持っている(直していない。事実として書く)】
   * 解析が完了しても、`[]` になる経路が2つある。**記録からは区別できない。**
   * - **終局・王手中の行** … measureEngineReference が探索を1本も行わないと決めて
   *   いる局面(**測らないと決めた**)
   * - **③の探索が例外を投げた行** … computeFocusText が自前の try/catch で
   *   握りつぶし、集まった分(0本)を返す(**測れなかった**)
   * 前者は `response.status.isEnd` 等から推し量れるが、**推し量るのは区別ではない。**
   * 直すとしたら本番側(computeFocusText)であり、U6-L のスコープ外なので
   * **ここでは事実を書くにとどめる**(docs/STEP_U6-L_PLAN_2026-09-13.md 12.3)。
   */
  searchPvs?: SearchPvObservation[] | null;
}

/**
 * **このファイルに 2 か所ある「3 値の欄」は、同じ規約である**(2026-09-13、STEP U6-R)。
 *
 * 別々の STEP(U6-L の `searchPvs` と U6-R の `dirty`)が独立に同じ形へたどり着いた。
 * **3 値目の位置が違うのではなく、「測って無かった」を表す値の型が違うだけである。**
 *
 * | 「無い」の種類 | `searchPvs`(record 行) | `dirty`(meta 行) | `trailingMoveTruncated`(meta 行) | `mirrored`(meta 行) | `sideAlignmentChecked`(meta 行) |
 * |---|---|---|---|---|---|
 * | **測っていない**(欄が無い。その STEP より前の記録) | `undefined` | `undefined` | `undefined` | `undefined` | `undefined` |
 * | **測れなかった**(取ろうとして失敗した) | `null` | `null` | **無い**(落とすかどうかは手数だけで決まり、失敗しない) | **無い**(回すかどうかは固定棋譜の欄だけで決まり、失敗しない) | **無い**(照合が食い違えば replay.ts は記録を書かずに止まる) |
 * | **測って無かった**(取れて、中身が空だった) | `[]` | `false` | `false`(落とす手が無かった) | `false`(回していない) | `false`(照合していない。回していない局か、`originalMoves` の無い回した局) |
 *
 * `trailingMoveTruncated` は `dirty` と同じ形である(`true` / `false` / 欄が無い)。**`null` の例外は作らない**(STEP D0-SIDE 段 1。
 * 最初は「落とさない局は `null`」で実装したが、この表の `null`(測れなかった)とぶつかるので、司令塔の決定で直した)。
 * 落とした手 `truncatedTrailingMove` は `true` のときだけ書く欄で、3 値の欄ではない。
 * `mirrored` も同じ形である(STEP D0-SIDE 段 2)。`startSfen`・`plyOffset`・`originalUserSide` は `mirrored` が `true` のときだけ書く欄で、3 値の欄ではない。
 * `sideAlignmentChecked` も `true` / `false` / 欄が無い の形だが、**`false` は「照合していない」**である(「照合して何も無かった」ではない)。
 *
 * **読むときは 3 つに分ける。`?? []` や `?? false` と書かない**(欄が無い記録が
 * 「測って無かった」に化ける)。[AGENT_PROTOCOL.md](../../../docs/AGENT_PROTOCOL.md) 3. の 11.6。
 *
 * **新しく 3 値の欄を足すときは、この表に行を足す。** 表に載らない 3 値を作らない。
 */

/** T-1のJSONLの"kind":"meta"行(先頭行)。 */
export interface MetaLine {
  kind: "meta";
  kifuId: string;
  startedAt: string;
  gitHead: string | null;
  enginePath: string;
  /** STEP T-3(探索モード)がmeta行に追加したフィールド。固定棋譜(replay.ts)の
   * metaには無いためoptional。STEP T-5(T5-B)が分母のプロファイル別小計に使う。
   * このファイルの追加であり、固定棋譜のmeta自体は変えない。 */
  mode?: string;
  profile?: string;
  /** STEP T-6(A-3)が回帰モード(replay.ts)のmeta行に追加したフィールド。
   * 探索(explore.ts)のmetaには無いためoptional。"nodes"は`go nodes N`固定、
   * "movetime"は`--nodes 0`で本番条件(movetime)のまま再生した場合。
   * check.tsが「## 入力」の混在警告に使う(STEP T-6計画書2. A-4)。 */
  searchMode?: "nodes" | "movetime";
  nodes?: number;
  threads?: number;
  /**
   * STEP U6-R。**測ったとき作業ツリーが汚れていたか**(コミットされていない編集が
   * あったか)。`gitHead` はコミットされた状態しか指さないため、共有ツリーで測ると
   * 「そのコミット + 誰かの未コミットの編集」が動く。
   *
   * **値は 4 つある ―`true` と、上の表の規約に従う 3 種類の「無い」である。**
   * 読む側の `DirtyState`(lib/gitState.ts)も、この 4 つに 1 対 1 で対応する 4 つの状態を持つ。
   * - `true` … **測って、汚れていた**(→ `"dirty"`)
   * - `false` … **測って、汚れていなかった**(→ `"clean"`)
   * - `null` … `git status` が取れなかった。**測れなかったのであって、きれいだったのではない**(→ `"unmeasured"`)
   * - `undefined`(欄が無い) … **U6-R より前に取った記録**。汚れを記録していない(→ `"unrecorded"`)
   *
   * **`meta.dirty ?? false` と書いてはならない。** 読むときは `=== true` / `=== false` /
   * `=== null` / それ以外、の 4 つに分ける(lib/gitState.ts の `readDirtyState`)。
   */
  dirty?: boolean | null;
  /** 汚れていたパス(最大 20 件)。`docs/` と `node_modules` は数えない。 */
  dirtyPaths?: string[];
  /** 汚れていたパスの総数(`dirtyPaths` が 20 件で切れていても本当の件数)。 */
  dirtyCount?: number;
  /**
   * STEP D0-SIDE 段 1(R-8。replay.ts)。再生のために最後の先手の手を落としたか。**値は 3 つ**(上の表。`dirty` と同じ形):
   * - `true` … 手数が奇数で、最後の手を落として再生した(落とした手は `truncatedTrailingMove`)
   * - `false` … 落とす手が無かった(手数が偶数)
   * - `undefined`(欄が無い) … **R-8 より前の記録**。落としたかどうかを記録していない
   */
  trailingMoveTruncated?: boolean;
  /** STEP D0-SIDE 段 1(R-8)。落とした最後の先手の手(USI)。**`trailingMoveTruncated` が `true` のときだけ書く**(false のときは欄が無い。null は使わない)。 */
  truncatedTrailingMove?: string;
  /**
   * STEP D0-SIDE 段 2(replay.ts。lib/sideAlignment.ts)。本人が後手の棋譜を回して、本人が先手の形にそろえたか。**値は 3 つ**(上の表。`dirty` と同じ形):
   * - `true` … 回して 1 手目を開始局面に畳んだ(`startSfen`・`plyOffset`・`originalUserSide` がある)
   * - `false` … 回していない(本人が先手の局)。`startSfen` などの欄は無い
   * - `undefined`(欄が無い) … **D0-SIDE 段 2 より前の記録**。平手から再生している
   * 解析が読む開始局面は lib/sideAlignment.ts の `initialSfenOf` で 3 つに分けて読む。
   */
  mirrored?: boolean;
  /** STEP D0-SIDE 段 2。再生を始めた局面(回した 1 手目を平手・後手番の初期局面に当てた局面)。**`mirrored` が `true` のときだけ書く**。 */
  startSfen?: string;
  /** STEP D0-SIDE 段 2。元の棋譜の手数との差(元の ply = 記録の ply + plyOffset)。**`mirrored` が `true` のときだけ書く**(値は 1)。 */
  plyOffset?: number;
  /** STEP D0-SIDE 段 2。元の棋譜で本人がどちらだったか。**`mirrored` が `true` のときだけ書く**(値は "gote")。 */
  originalUserSide?: "gote";
  /**
   * STEP D0-SIDE 段 2(司令塔の決定、2026-09-15)。回した局の固定棋譜の欄(startSfen・moves・plyOffset)を、`originalMoves` から作り直して照合したか。**常に書く**:
   * - `true` … 照合して一致した(食い違えば replay.ts は記録を書かずに止まるので、`true` の記録は一致したものだけ)
   * - `false` … 照合していない(回していない局、または `originalMoves` の無い回した局)
   * - `undefined`(欄が無い) … この欄より前の記録
   */
  sideAlignmentChecked?: boolean;
}

/** 不変条件1件が検出した1件分。束ねる単位は(invariantId, condition)。 */
export interface Finding {
  invariantId: string;
  /** どの入力ファイル(run)由来か。check.ts が実際のkifuIdへ上書きする
   * (各invariantの check() はファイルをまたいだ文脈を持たないため)。 */
  kifuId: string;
  ply: number;
  phase: "immediate" | "ready";
  /** 束ねるための識別子。既存のkind / notReadyReason / shapeIdのような値だけを使い、
   * 新しい語は作らない(計画書「実装してよい範囲」の制約)。 */
  condition: string;
  /** 検出内容を人が読める形で1〜2文にしたもの。将棋の評価語は含めない。 */
  detail: string;
  sfen: string;
  senteMove: string | null;
  goteMove: string | null;
}

/**
 * STEP D0-SIDE 段 2(R-7)。check.ts が入力ごとに不変条件へ渡す文脈。
 * - `initialSfen` … 記録の meta から読んだ開始局面(lib/sideAlignment.ts の `initialSfenOf`)。指し手履歴を並べ直す不変条件(I-9)が使う
 * **check の第 2 引数を省略できるのは試験の呼び出しのため**(平手の記録だけを渡す既存の試験)。**check.ts は必ず渡す**(check.test.ts の子プロセスで見張る)。
 */
export interface InvariantContext {
  initialSfen: string;
}

/** 不変条件(draft)1件。真偽を返す決定的な関数(check)を持つだけで、
 * LLM・エンジンの新規呼び出しは行わない(既存の本番関数のimportのみ許可)。 */
export interface Invariant {
  id: string;
  title: string;
  type: InvariantType;
  status: InvariantStatus;
  /** この不変条件がどの観測・既知事項に由来するか(計画書の表の"source"列)。 */
  source: string;
  /** 1つのrun(1つのJSONLファイル由来のrecord行、ply昇順)に対して真偽判定を行い、
   * 検出をFinding[]で返す。kifuIdはcheck.ts側で確定させるため、ここでは
   * 空文字列を入れておく(check.ts が上書きする)。 */
  check(records: RecordLine[], context?: InvariantContext): Finding[];
}
