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

app.innerHTML = `
  <h1>将棋コーチ (Phase 0 仮UI)</h1>
  <div id="status"></div>
  <table id="board"></table>
  <div id="hands"></div>
  <div id="controls">
    <input id="moveInput" type="text" placeholder="例: 7g7f" autocomplete="off" />
    <button id="submitMove">指す(四間飛車側)</button>
    <button id="newGame">新しい対局</button>
  </div>
  <div id="error"></div>
  <h2>将棋の意味を読む</h2>
  <div id="coach"></div>
  <h2>目指せる形</h2>
  <div id="plan"></div>
  <h2>指し手履歴</h2>
  <ol id="history"></ol>
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
// 「唯一の正解」等の断定はしない)、新しい色・装飾は追加しない(既存style.cssは
// 変更しない)。未選択の候補も引き続きすべて表示し続ける。
function renderPlan(plan: ReachablePlanBody): void {
  planEl.innerHTML = "";

  // Phase3 Unit1/Unit2: 断定的・評価的な表現は使わず、事実のみを短く伝える
  // (人間承認済み)。理由が事実として断定できない場合(unknown・将来の未知の値を
  // 含む、getPlanChangeReasonMessage参照)は追加の文言を出さない。新しい候補手
  // そのものは既存のPhase2表示(下記)をそのまま使う。
  if (plan.planChanged) {
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

  if (plan.reachableShapes.length > 0) {
    const heading = document.createElement("h3");
    heading.textContent = "目指せる形の候補";
    planEl.appendChild(heading);

    const list = document.createElement("ul");
    list.className = "reachable-shapes";
    for (const shape of plan.reachableShapes) {
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      const completedSuffix = shape.status === "completed" ? "(完成しています)" : "";
      const selectedSuffix = shape.shapeId === plan.resolvedTargetShapeId ? "[選択中]" : "";
      button.textContent = [shape.name + completedSuffix, selectedSuffix].filter(Boolean).join(" ");
      button.addEventListener("click", () => {
        void handleSelectTargetShape(shape.shapeId);
      });
      li.appendChild(button);
      list.appendChild(li);
    }
    planEl.appendChild(list);
  }

  if (plan.candidateMoveState === "ready" && plan.candidateMove?.status === "ready") {
    const moveHeading = document.createElement("h3");
    moveHeading.textContent = "この形へ近づく手の候補";
    planEl.appendChild(moveHeading);

    for (const explanation of plan.candidateMove.explanations) {
      const section = document.createElement("section");
      section.className = "candidate-move";

      const moveLabel = document.createElement("p");
      moveLabel.className = "candidate-move-usi";
      moveLabel.textContent = `候補手: ${explanation.move ?? ""}`;
      section.appendChild(moveLabel);

      const reason = document.createElement("p");
      reason.className = "candidate-move-reason";
      reason.textContent = explanation.reason;
      section.appendChild(reason);

      planEl.appendChild(section);
    }
  } else if (plan.candidateMoveState === "pending") {
    const p = document.createElement("p");
    p.className = "plan-pending";
    p.textContent = "候補手を計算中です(しばらくすると表示されます)。";
    planEl.appendChild(p);
  }
  // candidateMoveState: "unavailable"、またはcandidateMove.status: "not_ready"の場合は、
  // 候補手セクションを無理に表示しない(既存のPhase1表示のみを維持する)。
}

// 【Phase5】盤面クリックで着手できるようにする。合法手判定はstate.legalMoves
// (サーバーのgetLegalMovesをそのまま配線したもの)をフィルタするだけで、
// ここでは将棋ルールを一切判定しない。
// canSelect: 現在の手番が先手(人間側、CLAUDE.md「現在のスコープ」の先後固定)かつ
// 対局が終了していない場合のみ、自分の駒・持ち駒をクリック可能にする
// (相手側の駒は選択できるようにしない)。
function renderBoard(state: GameStateResponse): void {
  const board = parseSfenBoardPart(state.sfen);
  const turn = parseSfenTurn(state.sfen);
  const canSelect = turn === "sente" && !state.status.isEnd;
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

      const isSelected = squareName === selectedFrom;
      if (isSelected) td.classList.add("square-selected");

      const candidates = destinations.get(squareName);
      if (candidates && candidates.length > 0) {
        // 成り/不成りの両方が合法な場合のみcandidates.length===2になる
        // (強制成りの局面ではgetLegalMovesが不成り側を返さないため、自然に1件になる)。
        td.classList.add("square-destination");
        td.addEventListener("click", () => {
          void handleBoardMoveClick(candidates);
        });
      } else if (isSelected) {
        // 選択中のマスをもう一度クリックしたら選択解除する。
        td.addEventListener("click", () => {
          clearSelection();
          renderInteractive();
        });
      } else if (canSelect && square?.color === "sente") {
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
// 従来通りテキスト表示のまま(選択できるようにしない)。
function renderHands(state: GameStateResponse): void {
  const hands = parseSfenHands(state.sfen);
  const turn = parseSfenTurn(state.sfen);
  const canSelect = turn === "sente" && !state.status.isEnd;
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
      if (canSelect) {
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

function renderHistory(moveHistory: string[]): void {
  historyEl.innerHTML = "";
  moveHistory.forEach((move) => {
    const li = document.createElement("li");
    li.textContent = move;
    historyEl.appendChild(li);
  });
}

// 直近にrender()した局面のsfen。バックグラウンド解析の再取得結果を反映してよいか
// (=ユーザーが間にもう一手指していないか)を判定するために使う。
let lastRenderedSfen: string | undefined;

function render(state: GameStateResponse): void {
  currentState = state;
  clearSelection();
  lastRenderedSfen = state.sfen;
  renderBoard(state);
  renderHands(state);
  renderStatus(state);
  renderHistory(state.moveHistory);
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
async function playMove(moveUsi: string): Promise<boolean> {
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
