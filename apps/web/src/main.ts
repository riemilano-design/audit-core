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
  selectTargetShape,
  shouldShowPlanChangedNotice,
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
// #layout配下を#boardColumn(盤面・持ち駒・操作)と#infoColumn(説明・目指せる形・
// 指し手履歴)の2つにラップする。既存の各要素のid(#board, #hands, #controls,
// #coach, #plan, #history等)は一切変更していないため、以降のquerySelector・
// レンダリング処理(renderBoard/renderHands等)は無変更のまま動作する。
// PC等の十分な横幅ではCSS Grid(style.css参照)でこの2つを横並びにし、
// 狭い画面では通常のブロック要素として縦積みのままにする。
app.innerHTML = `
  <h1>将棋コーチ (Phase 0 仮UI)</h1>
  <div id="layout">
    <div id="boardColumn">
      <div id="status"></div>
      <table id="board"></table>
      <div id="hands"></div>
      <div id="controls">
        <input id="moveInput" type="text" placeholder="例: 7g7f" autocomplete="off" />
        <button id="submitMove">指す(四間飛車側)</button>
        <button id="newGame">新しい対局</button>
      </div>
      <div id="error"></div>
    </div>
    <div id="infoColumn">
      <h2>将棋の意味を読む</h2>
      <div id="coach"></div>
      <h2>目指せる形</h2>
      <div id="plan"></div>
      <h2>指し手履歴</h2>
      <ol id="history"></ol>
    </div>
  </div>
`;

const boardEl = document.querySelector<HTMLTableElement>("#board")!;
const handsEl = document.querySelector<HTMLDivElement>("#hands")!;
const statusEl = document.querySelector<HTMLDivElement>("#status")!;
const errorEl = document.querySelector<HTMLDivElement>("#error")!;
const historyEl = document.querySelector<HTMLOListElement>("#history")!;
const coachEl = document.querySelector<HTMLDivElement>("#coach")!;
const planEl = document.querySelector<HTMLDivElement>("#plan")!;
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
const STAGE_LABELS: Record<CoachStage, string> = {
  current_shape: "【今の局面】自分の形",
  opponent_intent: "【相手は何をしている？】",
  opponent_next_aim: "【このあと何を狙っている？】",
};

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

function renderCoach(coach: CoachExplanation[] | undefined): void {
  coachEl.innerHTML = "";

  if (!coach) {
    const p = document.createElement("p");
    p.className = "coach-unavailable";
    p.textContent = "この局面の説明を取得できませんでした。対局は続けられます。";
    coachEl.appendChild(p);
    return;
  }

  for (const item of coach) {
    const section = document.createElement("section");
    section.className = `coach-stage coach-status-${item.status}`;

    const title = document.createElement("h3");
    title.textContent = STAGE_LABELS[item.stage] ?? item.stage;
    section.appendChild(title);

    const badge = document.createElement("span");
    badge.className = "coach-badge";
    badge.textContent = `${STATUS_LABELS[item.status] ?? item.status}(${CONFIDENCE_LABELS[item.confidence_level]})`;
    section.appendChild(badge);

    const reason = document.createElement("p");
    reason.className = "coach-reason";
    reason.textContent = item.reason;
    section.appendChild(reason);

    coachEl.appendChild(section);
  }
}

// ⑥「目指せる形」・⑧「その手の目的」の表示。
// 順位(1位/2位/3位等)は表示しない(shapeGraphRankingの1位を唯一の正解として
// 強調しないため)。候補手は「候補の一つ」「この手の目的」という中立な見出しに留め、
// 「おすすめ」「正解」「安全」等の断定語は使わない。
//
// 目標形選択UI(docs/PHASES.md Phase2完了条件): 各候補はクリックして選択できる。
// 選択中の候補は「[選択中]」という中立なテキストで示すのみとし(「おすすめ」
// 「唯一の正解」等の断定はしない)。未選択の候補も引き続きすべて表示し続ける。
//
// 【Phase5 #7】「目指せる形」と「この形へ近づく手の候補」の関係、および
// candidateMoveStateが"unavailable"の場合の状態を、ユーザーに明示する
// (人間承認済み、docs/PHASES.md Phase5の「実対局確認で判明した設計上の限界」参照)。
// 判定ロジック(pathPlanner.ts等)・データは一切変更しない。ここで追加するのは
// 既存フィールド(reachableShapes/resolvedTargetShapeId/candidateMoveState/
// candidateMove)をどう見せるかというUI表示のみ。
// 「この形は目指せない」「この形に近づく手が存在しない」等、将棋の事実を断定する
// 文言は使わない。「現在の機能では候補手を表示できない」という機能上の事実のみを伝える。
// 【Phase6 Unit2】「直前の一手で何が変わったか」を、既存の表示の一番上に足す。
// 文言・マス目の日本語表記はすべてサーバー側(moveOutcomeExplanation.ts /
// japaneseSquare.ts / japaneseMoveHistory.ts)で生成済みで、ここでは表示するだけ。
// 判定・文言生成はweb側に一切持たない。
function renderLastMoveOutcome(plan: ReachablePlanBody): void {
  const outcome = plan.lastMoveOutcome;
  if (!outcome) return;

  const section = document.createElement("div");
  section.className = "last-move-section";

  const heading = document.createElement("h3");
  heading.textContent = "直前の一手";
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

  planEl.appendChild(section);
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
  heading.textContent = `「${progress.name}」の組み上がり`;
  section.appendChild(heading);

  const done = document.createElement("p");
  done.className = "route-progress-done";
  done.textContent =
    progress.matchedSquareLabels.length > 0
      ? `できているマス: ${progress.matchedSquareLabels.join("、")}`
      : "できているマス: まだありません";
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

      if (route.blockingSquareLabel) {
        const note = document.createElement("span");
        note.className = "route-note";
        note.textContent = `${route.blockingSquareLabel}には今、自分の駒があります。`;
        li.appendChild(note);
      }
      if (!route.hasPlayableFirstMove) {
        const note = document.createElement("span");
        note.className = "route-note";
        note.textContent = "この道のりの一手目は、今の局面では指せません。";
        li.appendChild(note);
      }

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

function renderPlan(plan: ReachablePlanBody): void {
  planEl.innerHTML = "";

  // 【Phase6 Unit2】既存の「形 → 未達成マス → 経路 → 残り手数 → 候補手」の表示は
  // 変更せず、その上に「直前の一手」を足す。
  renderLastMoveOutcome(plan);

  // Phase3 Unit1/Unit2: 断定的・評価的な表現は使わず、事実のみを短く伝える
  // (人間承認済み)。理由が事実として断定できない場合(unknown・将来の未知の値を
  // 含む、getPlanChangeReasonMessage参照)は追加の文言を出さない。新しい候補手
  // そのものは既存のPhase2表示(下記)をそのまま使う。
  // 【Phase6 Unit3 ⑦】Phase3の通知と、Unit2の「道のりが続けられなくなりました」
  // (route_lost)は同じ事象を二重に述べることがある。その場合はPhase3側の通知を
  // 表示しない(判定ロジックは一切変更せず、表示の抑止のみ。判断はgameApi.tsの
  // shouldShowPlanChangedNoticeに切り出してテスト可能にしてある)。
  if (shouldShowPlanChangedNotice(plan)) {
    const p = document.createElement("p");
    p.className = "plan-changed";
    p.textContent = "前回の計画が使えなくなりました。";
    planEl.appendChild(p);

    const reasonMessage = getPlanChangeReasonMessage(plan);
    if (reasonMessage) {
      const reasonP = document.createElement("p");
      reasonP.className = "plan-changed-reason";
      reasonP.textContent = reasonMessage;
      planEl.appendChild(reasonP);
    }
  }

  // 選択中の形の名前(候補手セクションの見出し・親子関係の表示に使う)。
  // reachableShapesの中からresolvedTargetShapeIdと一致するものを探すだけで、
  // 新しい判定は行わない(既存フィールドの参照のみ)。
  let selectedShapeName: string | null = null;

  if (plan.reachableShapes.length > 0) {
    const heading = document.createElement("h3");
    heading.textContent = "目指せる形の候補";
    planEl.appendChild(heading);

    // 【Phase5 #7 要件1】「目指せる形」と下の候補手の関係を一目で分かるようにする。
    const intro = document.createElement("p");
    intro.className = "plan-intro";
    intro.textContent = "ここで形を選ぶと、その形に近づくための候補手が下に表示されます。";
    planEl.appendChild(intro);

    const list = document.createElement("ul");
    list.className = "reachable-shapes";
    for (const shape of plan.reachableShapes) {
      const li = document.createElement("li");
      const isSelected = shape.shapeId === plan.resolvedTargetShapeId;
      if (isSelected) {
        // 【Phase5 #7 要件3】選択中の形を視覚的にも分かるようにする(文言の
        // 「[選択中]」表示に加えて、CSSクラスで背景色等の見た目を変えるのみ)。
        li.classList.add("reachable-shape-selected");
        selectedShapeName = shape.name;
      }
      const button = document.createElement("button");
      button.type = "button";
      const completedSuffix = shape.status === "completed" ? "(完成しています)" : "";
      const selectedSuffix = isSelected ? "[選択中]" : "";
      button.textContent = [shape.name + completedSuffix, selectedSuffix].filter(Boolean).join(" ");
      button.addEventListener("click", () => {
        void handleSelectTargetShape(shape.shapeId);
      });
      li.appendChild(button);
      list.appendChild(li);
    }
    planEl.appendChild(list);
  }

  renderRouteProgress(plan);

  // 【Phase5 #7 要件2・4・6】候補手セクション本体。
  // reachableShapesが0件(=選択中の形が特定できない)場合でも、候補手が
  // "ready"/"pending"/"unavailable"のいずれかであれば、その状態を伝える。
  // candidateMove.status: "not_ready"(candidateMoveStateは"ready")の場合のみ、
  // 既存仕様のまま何も表示しない(今回の変更対象外。実装後の報告で明記する)。
  const hasReadyExplanation = plan.candidateMoveState === "ready" && plan.candidateMove?.status === "ready";
  const shouldShowUnavailableMessage = plan.candidateMoveState === "unavailable";
  const shouldShowPendingMessage = plan.candidateMoveState === "pending";

  if (hasReadyExplanation || shouldShowUnavailableMessage || shouldShowPendingMessage) {
    // 【Phase5 #7 要件6】「選択中の形→その形に近づく候補手」という親子関係が
    // 視覚的にも分かるよう、見出し・説明・中身をひとつの枠(candidate-section)にまとめる。
    const candidateSection = document.createElement("div");
    candidateSection.className = "candidate-section";

    const moveHeading = document.createElement("h3");
    moveHeading.textContent = selectedShapeName ? `「${selectedShapeName}」に近づく手の候補` : "この形へ近づく手の候補";
    candidateSection.appendChild(moveHeading);

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
      for (const explanation of plan.candidateMove!.explanations) {
        const section = document.createElement("section");
        section.className = "candidate-move";

        const moveLabel = document.createElement("p");
        moveLabel.className = "candidate-move-usi";
        // 【Phase6 Unit1】マス目はサーバー側(notation/japaneseSquare.ts)で変換済みの
        // 日本語表記を使う。対応表に無い場合(想定外)はUSI表記へフォールバックする。
        const moveUsi = explanation.move ?? "";
        moveLabel.textContent = `候補手: ${plan.candidateMoveLabels[moveUsi] ?? moveUsi}`;
        section.appendChild(moveLabel);

        const reason = document.createElement("p");
        reason.className = "candidate-move-reason";
        reason.textContent = explanation.reason;
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
  board.forEach((rank, rowIndex) => {
    const tr = document.createElement("tr");
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
    const winnerLabel = outcome?.winner === "sente" ? "先手(四間飛車側)" : outcome?.winner === "gote" ? "後手(居飛車側)" : "引き分け";
    statusEl.textContent = `対局終了: ${winnerLabel}${outcome?.result ? `(${outcome.result})` : ""}`;
    return;
  }
  const turn = parseSfenTurn(state.sfen);
  statusEl.textContent = turn === "sente" ? "手番: 先手(あなた・四間飛車側)" : "手番: 後手(AI・居飛車側、思考中...)";
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
  renderCoach(state.coach);
  renderPlan(state.plan);
}

function setError(message: string): void {
  errorEl.textContent = message;
}

// ⑧(MultiPV参考評価)はサーバー側でバックグラウンド計算されるため、着手直後の
// レスポンスではcandidateMoveState: "pending"のことがある。少し待って1回だけ
// 状態を取り直し、その間にユーザーが別の手を指していなければ再描画する
// (対局の進行そのものはこの再取得を待たない)。
function schedulePlanRefresh(sfenAtSubmit: string): void {
  setTimeout(() => {
    if (lastRenderedSfen !== sfenAtSubmit) return; // 既に別の局面へ進んでいる
    fetchGameState()
      .then((state) => {
        if (lastRenderedSfen !== sfenAtSubmit) return; // 取得中にさらに進んでいた
        render(state);
      })
      .catch(() => {
        // 再取得の失敗は対局そのものに影響させない(静かに諦める)。
      });
  }, 1500);
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

// 目標形選択UI: reachableShapesの候補クリックから呼ばれる。
// 局面(sfen)自体は変わらないため、submitMoveと同じ非同期(pending→ready)の
// 流れを流用する(既存のschedulePlanRefreshによるポーリングをそのまま使う)。
async function handleSelectTargetShape(shapeId: string): Promise<void> {
  setError("");
  try {
    const result = await selectTargetShape(shapeId);
    if (isMoveError(result)) {
      setError(result.error);
      return;
    }
    render(result);
    if (result.plan.candidateMoveState === "pending") {
      schedulePlanRefresh(result.sfen);
    }
  } catch (err) {
    setError(`通信エラー: ${err instanceof Error ? err.message : String(err)}`);
  }
}

async function handleNewGame(): Promise<void> {
  setError("");
  const state = await startNewGame();
  render(state);
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
  .then(render)
  .catch((err) => setError(`初期状態の取得に失敗しました: ${err instanceof Error ? err.message : String(err)}`));
