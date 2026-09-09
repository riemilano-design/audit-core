// Phase 0時点での仮の盤面UI。
// docs/PHASES.md Phase0の目的「盤面が表示され、対局が(仮のUIで良いので)成立する」を満たす
// 最小限の実装。
//
// 【Phase5: 盤面クリック操作】
// 駒・持ち駒をクリックして着手できるようにする(docs/PHASES.md Phase5、人間承認済み)。
// 合法手判定は一切ここで再実装せず、サーバーが返すlegalMoves(rules/legalMoves.tsの
// getLegalMovesをそのまま配線したもの、gameApi.ts参照)を文字列としてフィルタ・
// グルーピングするだけに留める。USI形式のテキスト入力欄・「指す」ボタンは
// フォールバックとしてそのまま残す。

import {
  fetchGameState,
  getPlanChangeReasonMessage,
  isMoveError,
  reviewNoteSuffix,
  groupCandidateExplanationsByReason,
  shouldShowPlanChangedNotice,
  shouldShowNextConsiderations,
  shouldRetryPlanRefresh,
  startNewGame,
  submitMove,
  type CoachExplanation,
  type CoachStage,
  type CoachStatus,
  type ConfidenceLevel,
  type GameStateResponse,
  type ReachablePlanBody,
} from "./gameApi.js";
import { PIECE_KANJI } from "./pieceKanji.js";
import { parseSfenBoardPart, parseSfenHands, parseSfenTurn } from "./sfenBoard.js";
import "./style.css";

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) throw new Error("#appが見つかりません");

// 【Phase5: レイアウト】
// #layout配下を#boardColumn(盤面・持ち駒・操作)と#infoColumn(説明・どう指すか・
// 指し手履歴)の2つにラップする。
// 【Unit 3(情報構造の整理)で変わった点】右カラムの構成を、説明カードを並べる
// #coach + #plan から、人間が承認した5ブロック(#urgent / #happened / #aim / #why /
// #howto)+ 折りたたんだ #historyDetails へ変えた。#board, #hands, #controls,
// #history のidは従来どおりで、盤面まわりのレンダリングは無変更である。
// PC等の十分な横幅ではCSS Grid(style.css参照)でこの2つを横並びにし、
// 狭い画面では通常のブロック要素として縦積みのままにする。
app.innerHTML = `
  <h1>将棋コーチ</h1>
  <div id="layout">
    <div id="boardColumn">
      <div id="status"></div>
      <table id="board"></table>
      <div id="hands"></div>
      <div id="controls">
        <input id="moveInput" type="text" placeholder="例: 7g7f" autocomplete="off" />
        <button id="submitMove">指す</button>
        <button id="newGame">新しい対局</button>
      </div>
      <div id="error"></div>
    </div>
    <div id="infoColumn">
      <h2>今の局面</h2>
      <div id="urgent"></div>
      <div id="happened"></div>
      <div id="aim"></div>
      <div id="why"></div>
      <h2>どう指すか</h2>
      <div id="howto"></div>
      <details id="referenceDetails">
        <summary>参考になる囲い</summary>
        <div id="reference"></div>
      </details>
      <details id="historyDetails">
        <summary>指し手履歴</summary>
        <ol id="history"></ol>
      </details>
    </div>
  </div>
`;

const boardEl = document.querySelector<HTMLTableElement>("#board")!;
const handsEl = document.querySelector<HTMLDivElement>("#hands")!;
const statusEl = document.querySelector<HTMLDivElement>("#status")!;
const errorEl = document.querySelector<HTMLDivElement>("#error")!;
const historyEl = document.querySelector<HTMLOListElement>("#history")!;
const urgentEl = document.querySelector<HTMLDivElement>("#urgent")!;
const happenedEl = document.querySelector<HTMLDivElement>("#happened")!;
const aimEl = document.querySelector<HTMLDivElement>("#aim")!;
const whyEl = document.querySelector<HTMLDivElement>("#why")!;
const planEl = document.querySelector<HTMLDivElement>("#howto")!;
const referenceEl = document.querySelector<HTMLDivElement>("#reference")!;
const moveInput = document.querySelector<HTMLInputElement>("#moveInput")!;
const submitButton = document.querySelector<HTMLButtonElement>("#submitMove")!;
const newGameButton = document.querySelector<HTMLButtonElement>("#newGame")!;

// 【Phase5: 盤面クリック操作の選択状態】
// selectedFrom: 移動元として選択中の盤上のマス(USI形式、例: "7g")。
// selectedDropRole: 打つ駒として選択中の持ち駒の駒種(例: "P")。
// 両方同時には選択されない(片方を選ぶともう片方は解除する)。
let selectedFrom: string | undefined;
let selectedDropRole: string | undefined;
// 直近にrender()した対局状態。renderInteractive()(選択状態の変更だけを反映する
// 再描画。ネットワーク通信は行わない)から参照するために保持する。
let currentState: GameStateResponse | undefined;

// 【Phase5】POST /api/game/moveの送信中(サーバーの応答待ち)かどうか。
// サーバー側(server.ts)のリクエスト直列化と対になるクライアント側の対策で、
// 送信中は盤面・持ち駒のクリックを受け付けない(=UI上「合法」に見えるマスへの
// 二重クリックによる想定外のリクエスト重複を防ぐ)。将棋ルールの判定条件ではない。
let moveInFlight = false;

// 【Phase5: 直前の相手の手のハイライト】
// currentHighlightedMove: 現在ハイライト表示中の、相手の直前の手の移動元・移動先
// (無ければundefined)。moveIndexForHighlight: その手がmoveHistoryの何番目か
// (同じ手に対してタイマーを何度も張り直さないための重複防止用)。
let currentHighlightedMove: { from: string | undefined; to: string } | undefined;
let moveIndexForHighlight = -1;
let highlightFadeTimer: ReturnType<typeof setTimeout> | undefined;

const LAST_OPPONENT_MOVE_HIGHLIGHT_MS = 1500;

function clearSelection(): void {
  selectedFrom = undefined;
  selectedDropRole = undefined;
}

// 盤面座標(0始まりの行・列)からUSI形式のマス表記(例: "7g")を求める。
// SFEN盤面部分は一段目(段a)を先頭行とし、各段は9筋から1筋の順で並ぶ
// (docs/DATA_MODEL.md「確定事項: 座標形式」の規約どおり。表示用のsfenBoard.tsの
// 解析結果(行=段、列=筋9→1の順)と対応させただけで、新しい座標規約は作らない)。
function squareNameAt(rowIndex: number, colIndex: number): string {
  const file = 9 - colIndex;
  const rank = String.fromCharCode("a".charCodeAt(0) + rowIndex);
  return `${file}${rank}`;
}

// 合法手一覧(USI形式)から、指定した移動元マスにある駒を動かす場合の、
// 移動先マスごとの候補USI一覧を求める(移動先が同じでも成り/不成りの両方が
// 合法な場合は2件になる)。合法手判定そのものはサーバー(rules/legalMoves.ts)の
// 結果をそのまま使い、ここでは文字列のフィルタ・グルーピングのみ行う。
function destinationsFromSquare(square: string, legalMoves: string[]): Map<string, string[]> {
  const map = new Map<string, string[]>();
  for (const usi of legalMoves) {
    if (usi.length < 4 || usi[2] === "*") continue; // 打つ手(P*5e等)は対象外
    if (usi.slice(0, 2) !== square) continue;
    const to = usi.slice(2, 4);
    const list = map.get(to) ?? [];
    list.push(usi);
    map.set(to, list);
  }
  return map;
}

// 合法手一覧(USI形式)から、指定した持ち駒(role、例: "P")を打つ場合の、
// 移動先マスごとの候補USI一覧を求める(打つ手に成り/不成りの区別はないため、
// 移動先1つにつき必ず1件)。
function destinationsFromDropRole(role: string, legalMoves: string[]): Map<string, string[]> {
  const map = new Map<string, string[]>();
  for (const usi of legalMoves) {
    if (usi.length !== 4 || usi[1] !== "*" || usi[0] !== role) continue;
    map.set(usi.slice(2, 4), [usi]);
  }
  return map;
}

// 【Phase5: 直前の相手の手のハイライト】
// moveHistory(既存データ)の最後の手を、移動元・移動先マスの単純な文字列解析だけで
// 求める。将棋の合法性・意味の判定は一切行わない(サーバーが既に確定させた
// 指し手をそのまま表示するだけ)。打つ手(例: "P*5e")には移動元が無いため
// fromはundefinedのまま返す。
function parseMoveSquares(usi: string): { from: string | undefined; to: string } {
  if (usi.length >= 4 && usi[1] === "*") {
    return { from: undefined, to: usi.slice(2, 4) };
  }
  return { from: usi.slice(0, 2), to: usi.slice(2, 4) };
}

// moveHistoryの最後の手が相手(後手)の手かどうかは、配列インデックスの偶奇だけで
// 機械的に決まる(CLAUDE.md「現在のスコープ」により自分=先手固定・先手から
// 指し始めるため、0始まりで偶数番目=先手(自分)、奇数番目=後手(相手))。
// これは将棋の事実判断ではなく、既存の固定スコープ前提に基づく配列演算のみ。
// 対局終了等で相手が応手しなかった場合(最後の手が自分の手のまま)はundefinedを返す。
function lastOpponentMoveSquares(moveHistory: string[]): { from: string | undefined; to: string } | undefined {
  const lastIndex = moveHistory.length - 1;
  if (lastIndex < 0 || lastIndex % 2 === 0) return undefined;
  return parseMoveSquares(moveHistory[lastIndex]!);
}

// 「棋譜解析結果を見る画面」ではなく「対局しながら意味を理解する画面」を意識し、
// 将棋用語を知らない初心者にも伝わる短い日本語ラベルに変換する
// (これらはUI表示上の見出し文言であり、将棋の事実そのものではない)。
// Unit 3(情報構造の整理): 段ごとに独立したカードの見出しを並べるのをやめ、
// [2]「狙い」・[3]「なぜそれが重要か」という2つの情報単位の中の小見出しにする。
// 見出しの文言は人間が承認した5ブロック構成のものをそのまま使う。
const STAGE_LABELS: Record<CoachStage, string> = {
  current_shape: "自分の狙い",
  opponent_intent: "相手の狙い",
  opponent_next_aim: "このあと起こりやすいこと",
};

/** [2]「狙い」に入れる段。[3]へ回すのは opponent_next_aim だけ。 */
/** [5] の導入文。人間が指示した思想(「どれを選びますか?」ではない)をそのまま文にしたもの。 */
const REFERENCE_INTRO_TEXT =
  "将棋にはこういう形があります。今の局面では、そのうちどの形に近い部分があるかをコーチが説明します。";

const AIM_STAGES: CoachStage[] = ["current_shape", "opponent_intent"];
const WHY_STAGES: CoachStage[] = ["opponent_next_aim"];

const STATUS_LABELS: Record<CoachStatus, string> = {
  none: "まだ判断できません",
  forming: "途中(まだ断定できません)",
  matched: "検出しました",
  completed: "完成しています",
};

const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
  high: "確信度: 高",
  medium: "確信度: 中",
  low: "確信度: 低(参考程度に)",
};

/**
 * 1件の説明を、[2]・[3] の中の1項目として描く。
 *
 * 【purposeについて(Unit 3・人間の承認済み)】
 * サーバーは以前から purpose(この情報を何のために見るのか)を返していたが、web側が
 * 一切描画していなかった。[../../../CLAUDE.md](../../../CLAUDE.md)「絶対に守るルール」
 * 1番(目的→手→理由の順で説明を構成する)を画面上でも満たすため、reasonの前に置く。
 * 文言はサーバーが返したものをそのまま表示するだけで、web側で作らない。
 */
function appendCoachItem(container: HTMLElement, item: CoachExplanation): void {
  const section = document.createElement("section");
  section.className = `coach-stage coach-status-${item.status}`;

  const title = document.createElement("h4");
  title.className = "coach-stage-title";
  title.textContent = STAGE_LABELS[item.stage] ?? item.stage;
  section.appendChild(title);

  const purpose = document.createElement("p");
  purpose.className = "coach-purpose";
  purpose.textContent = item.purpose;
  section.appendChild(purpose);

  const reason = document.createElement("p");
  reason.className = "coach-reason";
  reason.textContent = item.reason;
  section.appendChild(reason);

  container.appendChild(section);
}

/**
 * バッジ(判定状態と確信度)は、以前は説明カード3枚それぞれに付いていた。
 * 同じ意味の情報が3箇所に並ぶ重複だったため、[2]「狙い」に1つだけ出す。
 * 出すのは自分の形(current_shape)のものとし、無ければ表示しない。
 */
function appendAimBadge(container: HTMLElement, coach: CoachExplanation[]): void {
  const source = coach.find((item) => item.stage === "current_shape");
  if (!source) return;

  const badge = document.createElement("span");
  badge.className = "coach-badge";
  badge.textContent = `${STATUS_LABELS[source.status] ?? source.status}(${CONFIDENCE_LABELS[source.confidence_level]})`;
  container.appendChild(badge);
}

/** [2]「狙い」。自分の狙いと相手の狙いを、1つの情報単位として並べる。 */
function renderAim(coach: CoachExplanation[] | undefined): void {
  aimEl.innerHTML = "";

  if (!coach) {
    const p = document.createElement("p");
    p.className = "coach-unavailable";
    p.textContent = "この局面の説明を取得できませんでした。対局は続けられます。";
    aimEl.appendChild(p);
    return;
  }

  const items = coach.filter((item) => AIM_STAGES.includes(item.stage));
  if (items.length === 0) return;

  const heading = document.createElement("h3");
  heading.textContent = "狙い";
  aimEl.appendChild(heading);
  appendAimBadge(aimEl, coach);

  for (const item of items) {
    appendCoachItem(aimEl, item);
  }
}

/**
 * [3]「なぜそれが重要か」。このあと起こりやすいことと、完成した自分の形の弱点。
 * どちらも既存のデータ(intentのnext_aim_explanation / shapeのweak_against)で、
 * 新しい文言は作らない。該当が無ければブロックごと出さない。
 */
function renderWhy(coach: CoachExplanation[] | undefined, plan: ReachablePlanBody | undefined): void {
  whyEl.innerHTML = "";

  const items = (coach ?? []).filter((item) => WHY_STAGES.includes(item.stage));
  const weakness = plan?.shapeWeakness ?? null;
  if (items.length === 0 && !weakness) return;

  const heading = document.createElement("h3");
  heading.textContent = "なぜそれが重要か";
  whyEl.appendChild(heading);

  for (const item of items) {
    appendCoachItem(whyEl, item);
  }

  if (weakness) {
    const section = document.createElement("section");
    section.className = "shape-weakness";

    const title = document.createElement("h4");
    title.className = "coach-stage-title";
    // 人間が承認した文言(2026-09-09)。「弱いところ」は説明書的で、初心者には
    // 「どんな攻めに気をつけるか」の方が直感的であるため。形の名前は、[3] の上に
    // 別の形の話が並ぶことがあるので、どの囲いの話かが分かるよう残している。
    title.textContent = `「${weakness.name}」${reviewNoteSuffix(weakness.pendingReviewNote)}が苦手な攻め`;
    section.appendChild(title);

    const text = document.createElement("p");
    text.className = "coach-reason";
    text.textContent = weakness.text;
    section.appendChild(text);

    whyEl.appendChild(section);
  }
}

/**
 * [0]「今すぐ対処が必要なこと」。どのメッセージが該当するかはサーバー側
 * (api/stateResponse.tsのpartitionUrgentMessages)が決めており、web側は表示するだけ。
 * 該当が無ければ要素ごと出さない(空のカードを残さない)。
 */
function renderUrgent(plan: ReachablePlanBody | undefined): void {
  urgentEl.innerHTML = "";
  const messages = plan?.urgentMessages ?? [];
  if (messages.length === 0) return;

  const heading = document.createElement("h3");
  heading.textContent = "今すぐ対処が必要なこと";
  urgentEl.appendChild(heading);

  const list = document.createElement("ul");
  list.className = "urgent-messages";
  for (const message of messages) {
    const li = document.createElement("li");
    li.textContent = message.text;
    list.appendChild(li);
  }
  urgentEl.appendChild(list);
}

// ⑥「目指せる形」・⑧「その手の目的」の表示。
// 順位(1位/2位/3位等)は表示しない(shapeGraphRankingの1位を唯一の正解として
// 強調しないため)。候補手は「候補の一つ」「この手の目的」という中立な見出しに留め、
// 「おすすめ」「正解」「安全」等の断定語は使わない。
//
// 【Phase 7 Unit 3 で廃止した仕組み】目標形選択UI(候補をクリックして選ぶ、
// 選択中を「[選択中]」で示す)は廃止した。囲いは選択肢ではなく参考資料として
// [5]「参考になる囲い」(renderReferenceShapes)に置く。道のり・候補手の対象は、
// 選択ではなくサーバーが局面から認識した方向性(resolveRecognizedDirection)で決まる。
//
// 【Phase5 #7】「目指せる形」と候補手セクションの関係(見出しは Unit 3 で
// 「「◯◯」に近づく手の候補」に一本化し、未選択時のフォールバック見出しは廃止した)、および
// candidateMoveStateが"unavailable"の場合の状態を、ユーザーに明示する
// (人間承認済み、docs/PHASES.md Phase5の「実対局確認で判明した設計上の限界」参照)。
// 判定ロジック(pathPlanner.ts等)・データは一切変更しない。ここで追加するのは
// 既存フィールド(reachableShapes/resolvedTargetShapeId/candidateMoveState/
// candidateMove)をどう見せるかというUI表示のみ。
// 「この形は目指せない」「この形に近づく手が存在しない」等、将棋の事実を断定する
// 文言は使わない。「現在の機能では候補手を表示できない」という機能上の事実のみを伝える。
// 【Phase6 Unit2】「直前の一手で何が変わったか」。Unit 3 で [1]「今、盤で起きたこと」
// という独立したブロック(#happened)へ移した(以前は候補手ブロックの一番上にあった)。
// 文言・マス目の日本語表記はすべてサーバー側(moveOutcomeExplanation.ts /
// japaneseSquare.ts / japaneseMoveHistory.ts)で生成済みで、ここでは表示するだけ。
// 判定・文言生成はweb側に一切持たない。
function renderLastMoveOutcome(plan: ReachablePlanBody): void {
  const outcome = plan.lastMoveOutcome;
  if (!outcome) return;

  const section = document.createElement("div");
  section.className = "last-move-section";

  const heading = document.createElement("h3");
  heading.textContent = "今、盤で起きたこと";
  section.appendChild(heading);

  const moves = document.createElement("p");
  moves.className = "last-move-moves";
  moves.textContent = outcome.opponentMoveLabel
    ? `あなた: ${outcome.playedMoveLabel} / 相手: ${outcome.opponentMoveLabel}`
    : `あなた: ${outcome.playedMoveLabel}`;
  section.appendChild(moves);

  const list = document.createElement("ul");
  list.className = "last-move-messages";
  for (const message of outcome.messages) {
    const li = document.createElement("li");
    li.className = `last-move-message last-move-message-${message.kind}`;
    li.textContent = message.text;
    list.appendChild(li);
  }
  section.appendChild(list);

  happenedEl.appendChild(section);
}

/**
 * [1]「今、盤で起きたこと」。直前の一手と、その手で起きた事実をまとめる。
 * Phase3の「前回の計画が使えなくなりました」もここへ入れ、同じ事実を別ブロックで
 * もう一度述べないようにする(Unit 1 の実測で、同じ事実が4箇所に並んでいた)。
 */
function renderHappened(plan: ReachablePlanBody): void {
  happenedEl.innerHTML = "";
  renderLastMoveOutcome(plan);

  // Phase3 Unit1/Unit2: 断定的・評価的な表現は使わず、事実のみを短く伝える
  // (人間承認済み)。理由が事実として断定できない場合は追加の文言を出さない。
  // 【Phase6 Unit3 ⑦】Phase3の通知とUnit2のroute_lostは同じ事象を二重に述べることが
  // あるため、その場合はPhase3側を表示しない(判定はgameApi.tsに切り出してある)。
  if (shouldShowPlanChangedNotice(plan)) {
    const p = document.createElement("p");
    p.className = "plan-changed";
    p.textContent = "前回の計画が使えなくなりました。";
    happenedEl.appendChild(p);

    const reasonMessage = getPlanChangeReasonMessage(plan);
    if (reasonMessage) {
      const reasonP = document.createElement("p");
      reasonP.className = "plan-changed-reason";
      reasonP.textContent = reasonMessage;
      happenedEl.appendChild(reasonP);
    }
  }
}

// 【Phase6 Unit1】「選択した形 → その形に必要なマス → 今どこまで出来ているか →
// 未達成部分の経路 → その経路の最初の一手」という因果を画面に出す。
// ここで行うのは、サーバーが返した値(plan.targetShapeProgress / plan.routes、
// マス目は既に日本語表記に変換済み)の表示のみで、判定・計算は一切しない。
// 「この手が良いから表示している」と誤解させないため、候補手が「形に近づく経路の
// 一手」であることを言葉で明示し、強さ・良し悪しには一切触れない。
function renderRouteProgress(plan: ReachablePlanBody): void {
  const progress = plan.targetShapeProgress;
  if (!progress) return;

  const section = document.createElement("div");
  section.className = "route-section";

  const heading = document.createElement("h3");
  heading.textContent = `「${progress.name}」${reviewNoteSuffix(progress.pendingReviewNote)}の組み上がり`;
  section.appendChild(heading);

  // Unit 3(重複の除去): 形の説明(characteristics)はここには出さない。
  // 同じ文が [5]「参考になる囲い」にもあり、同じ内容を2箇所で述べることになるため
  // ([5] を「囲いを知る場所」、ここ [4] を「どう指すかを見る場所」と役割で分ける)。
  // progress.description 自体はサーバーから引き続き届く(表示をやめただけ)。

  const done = document.createElement("p");
  done.className = "route-progress-done";
  // 人間の指示⑥: 座標だけでなく「駒名：座標」で、どの駒のことか追えるようにする。
  // 駒名は現在の盤から読んだものがサーバーで解決済み(matchedPieceLabels)。
  const doneLabels =
    progress.matchedPieceLabels.length === progress.matchedSquareLabels.length
      ? progress.matchedPieceLabels
      : progress.matchedSquareLabels;
  done.textContent =
    doneLabels.length > 0 ? `できているマス: ${doneLabels.join("、")}` : "できているマス: まだありません";
  section.appendChild(done);

  if (plan.routes.length > 0) {
    const routesHeading = document.createElement("p");
    routesHeading.className = "route-list-heading";
    routesHeading.textContent = "これから作るマスと、そこまでの道のり:";
    section.appendChild(routesHeading);

    const list = document.createElement("ul");
    list.className = "route-list";
    for (const route of plan.routes) {
      const li = document.createElement("li");

      const main = document.createElement("span");
      main.className = "route-main";
      main.textContent =
        `${route.targetPiece}を${route.targetSquareLabel}へ ` +
        `… 残り${route.remainingSteps}手(${route.routeLabel})`;
      li.appendChild(main);

      // Unit 3(情報構造の整理): ここにあった2つの注記は出さない。
      // - 「◯◯には今、自分の駒があります。」は、下の候補手の理由文と完全に重複していた
      //   (Unit 1 の実測で同じ事実が画面に5回出ていた)。候補手側へ一本化する
      // - 「この道のりの一手目は、今の局面では指せません。」は、同じ画面の下に候補手が
      //   並ぶため矛盾して読める。サーバー側(filterContradictoryConsiderations)で
      //   同種の一文を出し分けており、ここでも繰り返さない
      // 判定・データは変えていない(route.blockingSquareLabel / hasPlayableFirstMove は
      // 引き続きサーバーから届く)。表示をやめただけである。

      list.appendChild(li);
    }
    section.appendChild(list);
  } else if (progress.missingSquareLabels.length > 0) {
    const note = document.createElement("p");
    note.className = "route-note";
    note.textContent = `これから作るマス: ${progress.missingSquareLabels.join("、")}(道のりは今の局面では計算できませんでした)`;
    section.appendChild(note);
  }

  planEl.appendChild(section);
}

// 【Phase6 Unit4】「今の局面で分かっていること」。直前の一手による差分(Unit2/Unit3)
// ではなく、現在の局面について既に確定している事実を並べる。
// 文言・マス目の日本語表記・指し手の棋譜表記・並び順はすべてサーバー側
// (nextConsiderationDetector.ts / nextConsiderationExplanation.ts)で確定済みで、
// ここでは受け取った文字列をそのまま表示するだけ。判定・文言生成・並び替え・
// フィルタはweb側に一切持たない。
// 表示位置は経路(.route-section)の直後・候補手(.candidate-section)の直前
// (人間承認済み)。
function renderNextConsiderations(plan: ReachablePlanBody): void {
  if (!shouldShowNextConsiderations(plan)) return;

  const section = document.createElement("div");
  section.className = "next-considerations-section";

  const heading = document.createElement("h3");
  heading.textContent = "今の局面で分かっていること";
  section.appendChild(heading);

  const list = document.createElement("ul");
  list.className = "next-considerations-messages";
  for (const message of plan.nextConsiderations) {
    const li = document.createElement("li");
    li.className = `next-consideration next-consideration-${message.kind}`;
    li.textContent = message.text;
    list.appendChild(li);
  }
  section.appendChild(list);

  planEl.appendChild(section);
}

/**
 * [5]「参考になる囲い」。
 *
 * 【これは操作UIではない(Phase 7 Unit 3 の基本仕様)】
 * ユーザーに「どの囲いを目指しますか?」と選ばせるためのものではなく、
 * 「将棋にはこういう完成形がある」を知るための学習用の参考資料である。
 * クリックできる要素は置かない。
 *
 * 【完成形の盤・駒名+座標を出していないことについて】
 * data/shapes/*.json の座標は、各ファイルの source 自身が一次資料で未確認と記しており、
 * mino_takamino は source が記す先手視点の記述と保存座標の左右が一致していない。
 * 人間による座標の確定を待つため、完成形の盤も駒名+座標の一覧も出さない(人間の指示)。
 * ここで出すのは名前・認識状態・特徴と、今の盤で既に成立しているマスだけである。
 */
function renderReferenceShapes(plan: ReachablePlanBody | undefined): void {
  referenceEl.innerHTML = "";
  const shapes = plan?.referenceShapes ?? [];
  if (shapes.length === 0) return;

  const intro = document.createElement("p");
  intro.className = "reference-intro";
  intro.textContent = REFERENCE_INTRO_TEXT;
  referenceEl.appendChild(intro);

  const list = document.createElement("ul");
  list.className = "reference-shapes";
  for (const shape of shapes) {
    const li = document.createElement("li");
    li.className = "reference-shape";

    const title = document.createElement("h3");
    title.className = "reference-shape-name";
    title.textContent = shape.name + reviewNoteSuffix(shape.pendingReviewNote);
    li.appendChild(title);

    // 認識状態は既存のラベル(STATUS_LABELS)をそのまま使い、新しい文言を作らない。
    if (shape.status !== "none") {
      const badge = document.createElement("span");
      badge.className = `coach-badge reference-shape-status-${shape.status}`;
      badge.textContent = STATUS_LABELS[shape.status] ?? shape.status;
      li.appendChild(badge);
    }

    const characteristics = document.createElement("p");
    characteristics.className = "reference-shape-characteristics";
    characteristics.textContent = shape.characteristics;
    li.appendChild(characteristics);

    // Unit 3(重複の除去): 「今できているマス」はここには出さない。
    // 同じ内容が [4]「どう指すか」の組み上がりにあり、役割としても現在の進捗は [4] 側。
    // [5] は「将棋にはこういう形がある」を知る場所に徹する。

    // ① 完成形の盤の置き場所(人間の指示により、DOM構造だけ先に用意する)。
    // data/shapes/*.json の座標は一次資料未確認のため、**中身はまだ描画しない**。
    // 人間による座標の確認が完了したら、この要素の中に完成形の盤を描画する。
    // 確認されていない座標を一般知識で補完してはいけない。
    const boardSlot = document.createElement("div");
    boardSlot.className = "reference-shape-board";
    boardSlot.dataset.shapeId = shape.shapeId;
    boardSlot.hidden = true;
    li.appendChild(boardSlot);

    list.appendChild(li);
  }
  referenceEl.appendChild(list);
}

/** [4]「どう指すか」。局面から認識できた方向性 → 組み上がり → 道のり → 候補手。 */
function renderPlan(plan: ReachablePlanBody): void {
  planEl.innerHTML = "";

  // 「前回の計画が使えなくなりました」は [1]「今、盤で起きたこと」へ移した
  // (renderHappened参照)。同じ事実を2つのブロックで述べないため、ここでは出さない。

  // Phase 7 Unit 3: 目標形をユーザーに選ばせるUIは廃止した。囲いは「選択肢」ではなく
  // 「参考資料」として [5]「参考になる囲い」に置く(renderReferenceShapes)。
  // ここで扱うのは、サーバーが局面から認識した方向性(plan.resolvedTargetShapeId)だけで、
  // web側は新しい判定を持たない。
  const recognized = plan.reachableShapes.find((shape) => shape.shapeId === plan.resolvedTargetShapeId);
  const selectedShapeName: string | null = recognized?.name ?? null;
  const selectedShapeNote: string | null = recognized?.pendingReviewNote ?? null;

  // 方向が1つに定まらないときは、サーバーが返した一文だけを出して候補手を出さない
  // (ranked[0] フォールバックを復活させないための仕様。文言は人間が指定したもの)。
  if (plan.directionNote) {
    const note = document.createElement("p");
    note.className = "direction-note";
    note.textContent = plan.directionNote;
    planEl.appendChild(note);
  }

  renderRouteProgress(plan);

  // 【Phase6 Unit4】経路(道のり)の直後、候補手セクションの直前に置く(人間承認済み)。
  renderNextConsiderations(plan);

  // 【Phase5 #7 要件2・4・6】候補手セクション本体。
  // reachableShapesが0件(=認識できた方向が無い)場合でも、候補手が
  // "ready"/"pending"/"unavailable"のいずれかであれば、その状態を伝える。
  // candidateMove.status: "not_ready"(candidateMoveStateは"ready")の場合のみ、
  // 既存仕様のまま何も表示しない(今回の変更対象外。実装後の報告で明記する)。
  const hasReadyExplanation = plan.candidateMoveState === "ready" && plan.candidateMove?.status === "ready";
  const shouldShowUnavailableMessage = plan.candidateMoveState === "unavailable";
  const shouldShowPendingMessage = plan.candidateMoveState === "pending";

  // Unit 3(既知事項 U0-1 の解消): 目標形が選ばれていない間は、候補手セクションを
  // まるごと出さない。以前は未選択でも「この形へ近づく手の候補」「この形に近づく
  // 候補手を表示できません。」という、指す対象の無い文言が常時出ていた。
  // 代わりの文言は新しく作らず、セクションごと出さないことで解消する。
  if (selectedShapeName === null) return;

  if (hasReadyExplanation || shouldShowUnavailableMessage || shouldShowPendingMessage) {
    // 【Phase5 #7 要件6】「認識できた形→その形に近づく候補手」という親子関係が
    // 視覚的にも分かるよう、見出し・説明・中身をひとつの枠(candidate-section)にまとめる。
    const candidateSection = document.createElement("div");
    candidateSection.className = "candidate-section";

    const moveHeading = document.createElement("h3");
    moveHeading.textContent = `「${selectedShapeName}」${reviewNoteSuffix(selectedShapeNote)}に近づく手の候補`;
    candidateSection.appendChild(moveHeading);

    // 【STEP ζ-5(経路6)】対象の形のreview_statusが"draft"の場合にだけ、
    // サーバー側(analysis/nameExposure.ts)が決めた注意書きをそのまま1行表示する。
    // 個々の候補手の説明文自体は変更しない(見出し名の表示がフォールバックしても
    // この注意書きは独立に出る)。
    if (plan.pendingReviewNote) {
      const reviewNote = document.createElement("p");
      reviewNote.className = "candidate-section-review-note";
      reviewNote.textContent = plan.pendingReviewNote;
      candidateSection.appendChild(reviewNote);
    }

    // 【Phase5 #7 要件2】この見出しの下の内容が「今選択している形に対する、
    // 今の局面から指せる候補手」であることを明示する。
    // 【Phase6 Unit1】さらに、これらが上の「道のり」の最初の一手であること、
    // および将棋としての強さで選んだ手ではないことを明示する
    // (「エンジンの最善手」と混同させないため)。
    const description = document.createElement("p");
    description.className = "candidate-section-description";
    description.textContent =
      "上の道のりのうち、今の局面で指せる最初の一手です。将棋として最も良い手を選んでいるわけではありません。";
    candidateSection.appendChild(description);

    if (hasReadyExplanation) {
      // Unit 3(情報構造の整理): 但し書き(「唯一の正解ではありません」等)は、
      // 以前は候補手ごとの理由文の末尾に繰り返し入っていた(候補手3件なら3回)。
      // サーバー側がセクション単位でまとめて返すようになったので、ここで1回だけ出す。
      // 文言はサーバーが返したものをそのまま表示する。
      for (const note of plan.candidateMove!.sharedNotes) {
        const noteP = document.createElement("p");
        noteP.className = "candidate-section-shared-note";
        noteP.textContent = note;
        candidateSection.appendChild(noteP);
      }

      // Unit 3: 理由文が同一の候補手(例: ７七→３三 と ７七→４四)は1行にまとめ、
      // 指し手のラベルを並記する。まとめ方はgameApi.tsの純粋関数に切り出してある。
      const groups = groupCandidateExplanationsByReason(
        plan.candidateMove!.explanations,
        plan.candidateMoveLabels,
      );
      for (const group of groups) {
        const section = document.createElement("section");
        section.className = "candidate-move";

        const moveLabel = document.createElement("p");
        moveLabel.className = "candidate-move-usi";
        // 【Phase6 Unit1】マス目はサーバー側(notation/japaneseSquare.ts)で変換済みの
        // 日本語表記を使う。対応表に無い場合(想定外)はUSI表記へフォールバックする。
        moveLabel.textContent = `候補手: ${group.moveLabels.join(" / ")}`;
        section.appendChild(moveLabel);

        const reason = document.createElement("p");
        reason.className = "candidate-move-reason";
        reason.textContent = group.reason;
        section.appendChild(reason);

        candidateSection.appendChild(section);
      }
    } else if (shouldShowPendingMessage) {
      const p = document.createElement("p");
      p.className = "plan-pending";
      p.textContent = "候補手を計算中です(しばらくすると表示されます)。";
      candidateSection.appendChild(p);
    } else if (shouldShowUnavailableMessage) {
      // 【Phase5 #7 要件4・5】「候補が無い」ことを将棋の事実として断定せず、
      // あくまで「現在の機能では表示できない」という事実だけを伝える。
      const p = document.createElement("p");
      p.className = "plan-unavailable";
      p.textContent = "現在の局面では、この形に近づく候補手を表示できません。";
      candidateSection.appendChild(p);
    }

    planEl.appendChild(candidateSection);
  }
}

// 【Phase5】盤面クリックで着手できるようにする。合法手判定はstate.legalMoves
// (サーバーのgetLegalMovesをそのまま配線したもの)をフィルタするだけで、
// ここでは将棋ルールを一切判定しない。
// interactive: 現在の手番が先手(人間側、CLAUDE.md「現在のスコープ」の先後固定)かつ
// 対局が終了しておらず、かつ着手リクエストが送信中でない場合のみ、
// 自分の駒・持ち駒をクリック可能にする(相手側の駒は選択できるようにしない)。
// moveInFlight中はクリックハンドラを一切付けない(destinationのハイライト自体は
// 見た目としてそのまま残し、二重送信だけを防ぐ)。
// 盤の目盛り。squareNameAt(rowIndex, colIndex) が返すマス名と対応させる
// (左端が9筋・上端が一段。盤の描画順そのものは変更していない)。
const BOARD_FILE_LABELS = ["９", "８", "７", "６", "５", "４", "３", "２", "１"];
const BOARD_RANK_LABELS = ["一", "二", "三", "四", "五", "六", "七", "八", "九"];

function renderBoard(state: GameStateResponse): void {
  const board = parseSfenBoardPart(state.sfen);
  const turn = parseSfenTurn(state.sfen);
  const interactive = turn === "sente" && !state.status.isEnd && !moveInFlight;
  const destinations = selectedFrom
    ? destinationsFromSquare(selectedFrom, state.legalMoves)
    : selectedDropRole
      ? destinationsFromDropRole(selectedDropRole, state.legalMoves)
      : new Map<string, string[]>();

  boardEl.innerHTML = "";

  // Phase 7 Unit 3: 盤の外側に筋(９〜１)と段(一〜九)を表示する。
  // 「６八って盤のどこ?」を盤を見ながら理解できるようにするための目盛りであり、
  // 盤の向き・駒の配置ロジックは一切変更していない(squareNameAtの結果に合わせるだけ)。
  const headRow = document.createElement("tr");
  headRow.className = "board-file-header";
  headRow.appendChild(document.createElement("th"));
  for (let colIndex = 0; colIndex < 9; colIndex += 1) {
    const th = document.createElement("th");
    // squareNameAtと同じ規則(左端が9筋)で筋の数字を出す。
    th.textContent = BOARD_FILE_LABELS[colIndex] ?? "";
    headRow.appendChild(th);
  }
  boardEl.appendChild(headRow);

  board.forEach((rank, rowIndex) => {
    const tr = document.createElement("tr");

    const rankTh = document.createElement("th");
    rankTh.className = "board-rank-label";
    rankTh.textContent = BOARD_RANK_LABELS[rowIndex] ?? "";
    tr.appendChild(rankTh);

    rank.forEach((square, colIndex) => {
      const squareName = squareNameAt(rowIndex, colIndex);
      const td = document.createElement("td");
      if (square) {
        const span = document.createElement("span");
        span.className = square.color === "sente" ? "piece-sente" : "piece-gote";
        span.textContent = PIECE_KANJI[square.piece] ?? square.piece;
        td.appendChild(span);
      }

      // 【Phase5】直前の相手の手のハイライト(装飾のみ、クリック挙動には関与しない)。
      // 選択中マス・移動先ハイライトと別のCSSプロパティ(枠線)を使うことで、
      // 同じマスに両方付いても見分けがつくようにする(自分の操作との混同防止)。
      if (currentHighlightedMove?.from === squareName) td.classList.add("square-last-move-from");
      if (currentHighlightedMove?.to === squareName) td.classList.add("square-last-move-to");

      const isSelected = squareName === selectedFrom;
      if (isSelected) td.classList.add("square-selected");

      const candidates = destinations.get(squareName);
      if (candidates && candidates.length > 0) {
        // 成り/不成りの両方が合法な場合のみcandidates.length===2になる
        // (強制成りの局面ではgetLegalMovesが不成り側を返さないため、自然に1件になる)。
        td.classList.add("square-destination");
        if (interactive) {
          td.addEventListener("click", () => {
            void handleBoardMoveClick(candidates);
          });
        }
      } else if (isSelected) {
        // 選択中のマスをもう一度クリックしたら選択解除する。
        if (interactive) {
          td.addEventListener("click", () => {
            clearSelection();
            renderInteractive();
          });
        }
      } else if (interactive && square?.color === "sente") {
        td.classList.add("square-selectable");
        td.addEventListener("click", () => {
          selectedFrom = squareName;
          selectedDropRole = undefined;
          renderInteractive();
        });
      }

      tr.appendChild(td);
    });
    boardEl.appendChild(tr);
  });
}

// 【Phase5】先手(人間)の持ち駒だけをクリック可能なボタンにする。後手の持ち駒は
// 従来通りテキスト表示のまま(選択できるようにしない)。moveInFlight中は
// renderBoardと同じ理由でクリック不可にする。
function renderHands(state: GameStateResponse): void {
  const hands = parseSfenHands(state.sfen);
  const turn = parseSfenTurn(state.sfen);
  const interactive = turn === "sente" && !state.status.isEnd && !moveInFlight;
  const format = (h: Record<string, number>) =>
    Object.entries(h)
      .map(([piece, count]) => `${PIECE_KANJI[piece] ?? piece}${count > 1 ? `x${count}` : ""}`)
      .join(" ") || "なし";

  handsEl.innerHTML = "";

  const senteLabel = document.createElement("span");
  senteLabel.textContent = "先手持ち駒: ";
  handsEl.appendChild(senteLabel);

  const senteEntries = Object.entries(hands.sente);
  if (senteEntries.length === 0) {
    handsEl.appendChild(document.createTextNode("なし"));
  } else {
    senteEntries.forEach(([piece, count], i) => {
      const label = `${PIECE_KANJI[piece] ?? piece}${count > 1 ? `x${count}` : ""}`;
      if (interactive) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = selectedDropRole === piece ? "hand-piece hand-piece-selected" : "hand-piece";
        button.textContent = label;
        button.addEventListener("click", () => {
          selectedDropRole = selectedDropRole === piece ? undefined : piece;
          selectedFrom = undefined;
          renderInteractive();
        });
        handsEl.appendChild(button);
      } else {
        handsEl.appendChild(document.createTextNode(label));
      }
      if (i < senteEntries.length - 1) handsEl.appendChild(document.createTextNode(" "));
    });
  }

  handsEl.appendChild(document.createTextNode(` / 後手持ち駒: ${format(hands.gote)}`));
}

// selectedFrom/selectedDropRoleの変更だけを画面へ反映する(サーバーへは問い合わせない)。
function renderInteractive(): void {
  if (!currentState) return;
  renderBoard(currentState);
  renderHands(currentState);
}

function renderStatus(state: GameStateResponse): void {
  if (state.status.isEnd) {
    const outcome = state.status.outcome;
    const winnerLabel = outcome?.winner === "sente" ? "あなた(先手)" : outcome?.winner === "gote" ? "相手(後手)" : "引き分け";
    statusEl.textContent = `対局終了: ${winnerLabel}${outcome?.result ? `(${outcome.result})` : ""}`;
    return;
  }
  const turn = parseSfenTurn(state.sfen);
  statusEl.textContent = turn === "sente" ? "手番: あなた(先手)" : "手番: 相手(後手・考えています...)";
}

// 【Phase5】指し手履歴を日本語棋譜表記(例: "７六歩")で表示する。
// 変換はサーバー側(notation/japaneseMoveHistory.ts、shogiops標準のmakeJapaneseMoveOrDrop)に
// 完全に委ねており、ここでは受け取った文字列をそのまま表示するだけ(変換できなかった
// 手=nullの場合のみ、既存のUSI表記へフォールバックする)。
// 「誰が」の部分は、指し手のインデックスの偶奇(CLAUDE.md「現在のスコープ」の
// 自分=先手固定・先手から指し始めるという既存の前提)から機械的に決まるだけで、
// 新しい将棋判断ではない(main.tsの他の箇所(直前の相手の手のハイライト)と同じ考え方)。
// 「何手目か」は既存の<ol>(historyEl)自体の連番表示にそのまま任せ、重複させない。
function renderHistory(moveHistory: string[], moveHistoryJapanese: (string | null)[]): void {
  historyEl.innerHTML = "";
  moveHistory.forEach((move, index) => {
    const li = document.createElement("li");
    const turnLabel = index % 2 === 0 ? "先手" : "後手";
    const label = moveHistoryJapanese[index] ?? move;
    li.textContent = `${turnLabel}: ${label}`;
    historyEl.appendChild(li);
  });
}

// 直近にrender()した局面のsfen。バックグラウンド解析の再取得結果を反映してよいか
// (=ユーザーが間にもう一手指していないか)を判定するために使う。
let lastRenderedSfen: string | undefined;

// 【Phase5】直前の相手の手のハイライトを、新しい手が指されたときだけ張り直す。
// render()はbackground poll(schedulePlanRefresh)等、同じmoveHistoryのまま
// 何度も呼ばれることがあるため、moveIndexForHighlightで「本当に新しい手か」を
// 判定し、同じ手に対してタイマーを何度もリセットしない(表示時間が不必要に
// 延びるのを防ぐ)。
function updateLastOpponentMoveHighlight(moveHistory: string[]): void {
  const currentMoveIndex = moveHistory.length - 1;
  if (currentMoveIndex === moveIndexForHighlight) return; // 同じ手のまま(新しい手ではない)

  moveIndexForHighlight = currentMoveIndex;
  if (highlightFadeTimer !== undefined) {
    clearTimeout(highlightFadeTimer);
    highlightFadeTimer = undefined;
  }

  currentHighlightedMove = lastOpponentMoveSquares(moveHistory);
  if (currentHighlightedMove) {
    highlightFadeTimer = setTimeout(() => {
      highlightFadeTimer = undefined;
      currentHighlightedMove = undefined;
      renderInteractive();
    }, LAST_OPPONENT_MOVE_HIGHLIGHT_MS);
  }
}

function render(state: GameStateResponse): void {
  currentState = state;
  clearSelection();
  updateLastOpponentMoveHighlight(state.moveHistory);
  lastRenderedSfen = state.sfen;
  renderBoard(state);
  renderHands(state);
  renderStatus(state);
  renderHistory(state.moveHistory, state.moveHistoryJapanese);
  // Unit 3(情報構造の整理): [0] 今すぐ対処が必要なこと → [1] 今、盤で起きたこと →
  // [2] 狙い → [3] なぜそれが重要か → [4] どう指すか の順に描く。
  renderUrgent(state.plan);
  renderHappened(state.plan);
  renderAim(state.coach);
  renderWhy(state.coach, state.plan);
  renderPlan(state.plan);
  renderReferenceShapes(state.plan);
}

function setError(message: string): void {
  errorEl.textContent = message;
}

// ⑧(MultiPV参考評価)はサーバー側でバックグラウンド計算されるため、着手直後の
// レスポンスではcandidateMoveState: "pending"のことがある。少し待って状態を取り直し、
// その間にユーザーが別の手を指していなければ再描画する
// (対局の進行そのものはこの再取得を待たない)。
//
// 【Phase6 通し確認で判明した問題への対応】
// 以前は1.5秒後に1回だけ再取得していたが、エンジンの解析は完了までに数秒かかる
// (実測で約8秒)ため常に空振りし、サーバー側が"ready"で候補手の説明を持っているのに
// 画面は「候補手を計算中です」のまま止まっていた。上限付きのリトライへ変更する
// (リトライしてよいかの判定はgameApi.tsのshouldRetryPlanRefresh。無限には回さない)。
//
// 【再描画を"pending"のうちは行わないことについて】
// render()はclearSelection()を呼ぶため、リトライのたびに再描画すると、盤面クリックで
// 駒を選択中のユーザーの選択が繰り返し解除されてしまう。再取得中は局面が進んでいない
// (lastRenderedSfenで保証)ので、まだ"pending"の間は画面の内容が変わらない。
// そのため、状態が"pending"でなくなったときだけ再描画する。
const PLAN_REFRESH_INTERVAL_MS = 1500;

function schedulePlanRefresh(sfenAtSubmit: string, attempt = 1): void {
  setTimeout(() => {
    if (lastRenderedSfen !== sfenAtSubmit) return; // 既に別の局面へ進んでいる
    fetchGameState()
      .then((state) => {
        if (lastRenderedSfen !== sfenAtSubmit) return; // 取得中にさらに進んでいた
        if (state.plan.candidateMoveState !== "pending") render(state);
        if (shouldRetryPlanRefresh(state.plan, attempt)) {
          schedulePlanRefresh(sfenAtSubmit, attempt + 1);
        }
      })
      .catch(() => {
        // 再取得の失敗は対局そのものに影響させない(静かに諦める)。
      });
  }, PLAN_REFRESH_INTERVAL_MS);
}

// テキスト入力欄からの着手・盤面クリックからの着手の両方が使う共通処理。
// 合法性の最終確認は既存通りサーバー(POST /api/game/move、applyMove.ts)側で行う
// (ここでは通信結果の反映のみ)。戻り値は着手が成功したかどうか。
//
// 【Phase5: 二重送信防止】
// moveInFlightをtrueにしてrenderInteractive()を呼ぶのは、必ず最初のawait(通信)より
// 前の同期的な行にする。これにより、盤面の「クリック可能」な見た目・クリックハンドラが
// ネットワーク待ちに入る前の時点で即座に外れる(=ユーザーが体感できるタイミングより
// 先に無効化が完了する)。サーバー側(server.ts)のリクエスト直列化と合わせて、
// 「合法に見えたマスをクリックしたのに非合法になる」問題への対策とする
// (合法手判定ロジック自体は変更していない)。
async function playMove(moveUsi: string): Promise<boolean> {
  if (moveInFlight) return false;
  moveInFlight = true;
  renderInteractive();
  setError("");
  try {
    const result = await submitMove(moveUsi);
    if (isMoveError(result)) {
      setError(result.error);
      return false;
    }
    render(result);
    if (result.plan.candidateMoveState === "pending") {
      schedulePlanRefresh(result.sfen);
    }
    return true;
  } catch (err) {
    setError(`通信エラー: ${err instanceof Error ? err.message : String(err)}`);
    return false;
  } finally {
    moveInFlight = false;
    renderInteractive();
  }
}

async function handleSubmitMove(): Promise<void> {
  const move = moveInput.value.trim();
  if (!move) return;
  submitButton.disabled = true;
  const succeeded = await playMove(move);
  if (succeeded) moveInput.value = "";
  submitButton.disabled = false;
}

// 【Phase5】盤面クリックで移動先マスを選んだときの着手。
// candidatesは同じ移動先に対応するUSI候補(1件、または成り/不成りの2件)。
// 2件の場合のみ、その場で成り/不成りを確認する(強制成りの場合はgetLegalMovesが
// 最初から1件しか返さないため、ここでは分岐しない=新しい成り判定ロジックを作らない)。
async function handleBoardMoveClick(candidates: string[]): Promise<void> {
  if (moveInFlight) return;
  let moveUsi = candidates[0];
  if (!moveUsi) return;
  if (candidates.length > 1) {
    const promote = window.confirm("成りますか?");
    moveUsi = candidates.find((usi) => usi.endsWith("+") === promote) ?? moveUsi;
  }
  await playMove(moveUsi);
}

// Phase 7 Unit 3: 目標形選択UI(reachableShapesの候補クリック)は廃止したため、
// その入口だったhandleSelectTargetShapeも削除した。囲いは選択肢ではなく参考資料として
// [5]「参考になる囲い」に置く。サーバー側の POST /api/game/target-shape 自体は
// 開発・検証用に残してある(api/stateResponse.ts の computeRankedPlanContext 参照)。

// 描画したうえで、⑧がまだ計算中なら完了を取りに行く。
// 着手時は playMove が個別に予約しているが、
// 「新しい対局」と初回ページロードにはこの予約が無く、⑧が計算中のまま画面が
// 「候補手を計算中です」で止まる経路になっていた(Phase6の通し確認で判明)。
// 両方をこのヘルパー経由にそろえる。
function renderAndScheduleRefresh(state: GameStateResponse): void {
  render(state);
  if (state.plan.candidateMoveState === "pending") {
    schedulePlanRefresh(state.sfen);
  }
}

async function handleNewGame(): Promise<void> {
  setError("");
  const state = await startNewGame();
  renderAndScheduleRefresh(state);
}

submitButton.addEventListener("click", () => {
  void handleSubmitMove();
});
moveInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") void handleSubmitMove();
});
newGameButton.addEventListener("click", () => {
  void handleNewGame();
});

fetchGameState()
  .then(renderAndScheduleRefresh)
  .catch((err) => setError(`初期状態の取得に失敗しました: ${err instanceof Error ? err.message : String(err)}`));
