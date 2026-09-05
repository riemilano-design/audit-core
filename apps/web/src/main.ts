// Phase 0時点での仮の盤面UI。
// docs/PHASES.md Phase0の目的「盤面が表示され、対局が(仮のUIで良いので)成立する」を満たす
// 最小限の実装。着手はUSI形式のテキスト入力で行う(盤面上のクリック操作は未実装)。

import {
  fetchGameState,
  isMoveError,
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
function renderPlan(plan: ReachablePlanBody): void {
  planEl.innerHTML = "";

  if (plan.reachableShapes.length > 0) {
    const heading = document.createElement("h3");
    heading.textContent = "目指せる形の候補";
    planEl.appendChild(heading);

    const list = document.createElement("ul");
    list.className = "reachable-shapes";
    for (const shape of plan.reachableShapes) {
      const li = document.createElement("li");
      li.textContent = shape.status === "completed" ? `${shape.name}(完成しています)` : shape.name;
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

function renderBoard(sfen: string): void {
  const board = parseSfenBoardPart(sfen);
  boardEl.innerHTML = "";
  for (const rank of board) {
    const tr = document.createElement("tr");
    for (const square of rank) {
      const td = document.createElement("td");
      if (square) {
        const span = document.createElement("span");
        span.className = square.color === "sente" ? "piece-sente" : "piece-gote";
        span.textContent = PIECE_KANJI[square.piece] ?? square.piece;
        td.appendChild(span);
      }
      tr.appendChild(td);
    }
    boardEl.appendChild(tr);
  }
}

function renderHands(sfen: string): void {
  const hands = parseSfenHands(sfen);
  const format = (h: Record<string, number>) =>
    Object.entries(h)
      .map(([piece, count]) => `${PIECE_KANJI[piece] ?? piece}${count > 1 ? `x${count}` : ""}`)
      .join(" ") || "なし";
  handsEl.textContent = `先手持ち駒: ${format(hands.sente)} / 後手持ち駒: ${format(hands.gote)}`;
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
  lastRenderedSfen = state.sfen;
  renderBoard(state.sfen);
  renderHands(state.sfen);
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

async function handleSubmitMove(): Promise<void> {
  const move = moveInput.value.trim();
  if (!move) return;
  submitButton.disabled = true;
  setError("");
  try {
    const result = await submitMove(move);
    if (isMoveError(result)) {
      setError(result.error);
      return;
    }
    moveInput.value = "";
    render(result);
    if (result.plan.candidateMoveState === "pending") {
      schedulePlanRefresh(result.sfen);
    }
  } catch (err) {
    setError(`通信エラー: ${err instanceof Error ? err.message : String(err)}`);
  } finally {
    submitButton.disabled = false;
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
