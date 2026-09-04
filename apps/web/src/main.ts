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
  <h2>指し手履歴</h2>
  <ol id="history"></ol>
`;

const boardEl = document.querySelector<HTMLTableElement>("#board")!;
const handsEl = document.querySelector<HTMLDivElement>("#hands")!;
const statusEl = document.querySelector<HTMLDivElement>("#status")!;
const errorEl = document.querySelector<HTMLDivElement>("#error")!;
const historyEl = document.querySelector<HTMLOListElement>("#history")!;
const coachEl = document.querySelector<HTMLDivElement>("#coach")!;
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

function render(state: GameStateResponse): void {
  renderBoard(state.sfen);
  renderHands(state.sfen);
  renderStatus(state);
  renderHistory(state.moveHistory);
  renderCoach(state.coach);
}

function setError(message: string): void {
  errorEl.textContent = message;
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
