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
  formatGameEndStatus,
  isMoveError,
  reviewNoteSuffix,
  candidateMoveUsisOnBoard,
  isCandidateMovesExcluded,
  groupCandidateExplanationsByReason,
  shouldRetryPlanRefresh,
  splitCoachByStage,
  partitionPieceThreatsForBoard,
  boardMarksFromState,
  firstSentence,
  summarizeHappened,
  summarizeOpponentAim,
  summarizeWhy,
  summarizeMyAim,
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
// 【STEP 5-2(構造。人間承認済み、docs/PHASES.md「見せ方の確定」決定2の1・2)で
// 変わった点】#infoColumnを「読む列」#readColumnと「操作する列」#actColumnの
// 2つに分けた。#readColumnは帯(いま注意する駒。中身が無ければhiddenにする)→
// ①〜④(何が起きているか/相手の狙い/何が重要か/自分の目的)。#actColumnは
// ⑤(候補手)→道のり(details、既定閉)→参考になる囲い→指し手履歴。
// 旧#aim(current_shape・opponent_intentの2カードを1つの箱にまとめていたもの)は
// #opponentAim(②)と#myAim(④)に分割した。旧#howtoは#candidatesに改名した
// (docs/STEP_5-2_PLAN_2026-09-11.md A-1のid指定どおり)。情報の内容・文言は
// 変えていない(置き場所と見出しだけの変更)。
// PC等の十分な横幅ではCSS Grid(style.css参照)で3列(盤|読む列|操作する列)にし、
// 狭い画面では通常のブロック要素として縦積みのままにする。
app.innerHTML = `
  <h1>将棋コーチ</h1>
  <div id="layout">
    <div id="boardColumn">
      <div id="status"></div>
      <div id="boardArea">
        <table id="board"></table>
        <svg id="boardOverlay" aria-hidden="true"></svg>
      </div>
      <div id="boardLegend"></div>
      <div id="hands"></div>
      <div id="controls">
        <input id="moveInput" type="text" placeholder="例: 7g7f" autocomplete="off" />
        <button id="submitMove">指す</button>
        <button id="newGame">新しい対局</button>
        <!-- STEP 4-7B(P-11。人間承認済みの文言): 盤クリックでも着手できることの案内。
             局面に依らず常時表示する(H-3: 入力欄直下の1行)。 -->
        <p id="moveHint" class="move-hint">盤の駒を押しても指せます</p>
      </div>
      <div id="error"></div>
    </div>
    <div id="infoColumn">
      <div id="readColumn">
        <div id="urgent"></div>
        <h2>① 何が起きているか</h2>
        <div id="happened"></div>
        <h2>② 相手の狙い</h2>
        <div id="opponentAim"></div>
        <h2>③ 何が重要か</h2>
        <div id="why"></div>
        <h2>④ 自分の目的</h2>
        <div id="myAim"></div>
      </div>
      <div id="actColumn">
        <h2>⑤ 候補手</h2>
        <div id="candidates"></div>
        <details id="routeDetails">
          <summary>道のり</summary>
          <div id="routeList"></div>
        </details>
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
  </div>
`;

const boardEl = document.querySelector<HTMLTableElement>("#board")!;
const boardAreaEl = document.querySelector<HTMLDivElement>("#boardArea")!;
const boardOverlayEl = document.querySelector<SVGSVGElement>("#boardOverlay")!;
const boardLegendEl = document.querySelector<HTMLDivElement>("#boardLegend")!;
const handsEl = document.querySelector<HTMLDivElement>("#hands")!;
const statusEl = document.querySelector<HTMLDivElement>("#status")!;
const errorEl = document.querySelector<HTMLDivElement>("#error")!;
const historyEl = document.querySelector<HTMLOListElement>("#history")!;
const urgentEl = document.querySelector<HTMLDivElement>("#urgent")!;
const happenedEl = document.querySelector<HTMLDivElement>("#happened")!;
const opponentAimEl = document.querySelector<HTMLDivElement>("#opponentAim")!;
const whyEl = document.querySelector<HTMLDivElement>("#why")!;
const myAimEl = document.querySelector<HTMLDivElement>("#myAim")!;
const planEl = document.querySelector<HTMLDivElement>("#candidates")!;
const routeListEl = document.querySelector<HTMLDivElement>("#routeList")!;
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
// Unit 3(情報構造の整理)で、段ごとに独立したカードの見出しを並べるのをやめ、
// 情報単位の中の小見出しにした。
// 【STEP 5-2】②(相手の狙い)・④(自分の目的)は、ブロックの見出し自体が
// 「② 相手の狙い」「④ 自分の目的」になったため、カード内の小見出しは重複するので
// 出さない(appendCoachItemのshowTitle:false)。③(なぜそれが重要か)は現行どおり
// このラベルをカード内の小見出しとして使う。
const STAGE_LABELS: Record<CoachStage, string> = {
  current_shape: "自分の狙い",
  opponent_intent: "相手の狙い",
  opponent_next_aim: "このあと起こりやすいこと",
};

/** [5] の導入文。人間が指示した思想(「どれを選びますか?」ではない)をそのまま文にしたもの。 */
const REFERENCE_INTRO_TEXT =
  "将棋にはこういう形があります。今の局面では、そのうちどの形に近い部分があるかをコーチが説明します。";

const WHY_STAGES: CoachStage[] = ["opponent_next_aim"];

/** coachがundefined(説明生成に失敗した場合)に②④で表示する既存の文言。
 * Unit 3の旧#aimで使っていたものと同じ文で、②④に分割しても両方に出す
 * (どちらのブロックも「この局面の説明」の一部であるため)。 */
const COACH_UNAVAILABLE_TEXT = "この局面の説明を取得できませんでした。対局は続けられます。";

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
 * 1件の説明を、情報単位の中の1項目として描く。
 *
 * 【purposeについて(Unit 3・人間の承認済み)】
 * サーバーは以前から purpose(この情報を何のために見るのか)を返していたが、web側が
 * 一切描画していなかった。[../../../CLAUDE.md](../../../CLAUDE.md)「絶対に守るルール」
 * 1番(目的→手→理由の順で説明を構成する)を画面上でも満たすため、reasonの前に置く。
 * 文言はサーバーが返したものをそのまま表示するだけで、web側で作らない。
 *
 * 【STEP 5-2】showTitle(既定true)をfalseにすると、カード内の小見出し(h4)を
 * 出さない。②「相手の狙い」④「自分の目的」は、ブロックの見出し自体が同じ意味を
 * 述べるため重複を避ける(呼び出し側で使い分ける。文はpurpose/reasonのみ変わらず出す)。
 */
function appendCoachItem(container: HTMLElement, item: CoachExplanation, options?: { showTitle?: boolean }): void {
  const section = document.createElement("section");
  section.className = `coach-stage coach-status-${item.status}`;

  if (options?.showTitle !== false) {
    const title = document.createElement("h4");
    title.className = "coach-stage-title";
    title.textContent = STAGE_LABELS[item.stage] ?? item.stage;
    section.appendChild(title);
  }

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
 *
 * STEP 4-6(G-1、人間承認済み): 直後の文「今、{形}の形ができています。」と同じ事実を
 * 述べており、「確信度」も未説明用語のため、この関数は呼び出さない(バッジを出さない)。
 * 判定は変えていないため、関数自体は残す。
 */
function appendAimBadge(container: HTMLElement, coach: CoachExplanation[]): void {
  const source = coach.find((item) => item.stage === "current_shape");
  if (!source) return;

  const badge = document.createElement("span");
  badge.className = "coach-badge";
  badge.textContent = `${STATUS_LABELS[source.status] ?? source.status}(${CONFIDENCE_LABELS[source.confidence_level]})`;
  container.appendChild(badge);
}

/**
 * STEP 5-3(A-2、人間承認済み): ①〜④の開閉の状態(モジュール変数)。
 * DOMに持つと1.5秒ごとの再取得・着手のたびの再描画で失われるため、
 * emphasizedCandidateUsi等と同じくモジュール変数に持つ(F-7)。
 * 既定は①開・②③④閉(人間の決定H-4 (a))。新しい対局でこの既定へ戻す
 * (handleNewGame参照)。②と④は排他(片方を開くともう片方を閉じる)。③は独立。
 */
interface ReadColumnOpenState {
  happened: boolean;
  opponentAim: boolean;
  why: boolean;
  myAim: boolean;
}

const DEFAULT_READ_COLUMN_OPEN: ReadColumnOpenState = {
  happened: true,
  opponentAim: false,
  why: false,
  myAim: false,
};

let readColumnOpen: ReadColumnOpenState = { ...DEFAULT_READ_COLUMN_OPEN };

/**
 * STEP 5-3(A-2): ①〜④共通の「要約行+本文」の描画。containerの中身をこの関数が
 * 丸ごと作り直す。buildBodyが何もbodyElに追加しなかった場合(本文が空)は、
 * 要約行だけを出し、開閉の印(button化・アイコン)を出さない
 * (押しても何も開かないボタンを置かないため)。
 */
function renderExpandableBlock(
  container: HTMLElement,
  bodyId: string,
  summaryText: string,
  isOpen: boolean,
  onToggle: () => void,
  buildBody: (bodyEl: HTMLElement) => void,
): void {
  container.innerHTML = "";

  const bodyEl = document.createElement("div");
  bodyEl.id = bodyId;
  bodyEl.className = "block-body";
  buildBody(bodyEl);

  const hasBody = bodyEl.childNodes.length > 0;
  container.classList.toggle("block-empty", !hasBody && summaryText.length === 0);

  const summaryRow = document.createElement(hasBody ? "button" : "div");
  summaryRow.className = "block-summary";
  if (hasBody) {
    (summaryRow as HTMLButtonElement).type = "button";
    summaryRow.setAttribute("aria-expanded", String(isOpen));
    summaryRow.setAttribute("aria-controls", bodyId);
    summaryRow.addEventListener("click", onToggle);
  }

  const textSpan = document.createElement("span");
  textSpan.className = "block-summary-text";
  textSpan.textContent = summaryText;
  summaryRow.appendChild(textSpan);

  if (hasBody) {
    const icon = document.createElement("span");
    icon.className = "block-summary-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = isOpen ? "▼" : "▶";
    summaryRow.appendChild(icon);
  }

  container.appendChild(summaryRow);

  bodyEl.hidden = !hasBody || !isOpen;
  container.appendChild(bodyEl);
}

/**
 * STEP 5-3(A-2): ①〜④の開閉状態を変えたあと、読む列4ブロックと盤(印の連動、A-3)を
 * 描き直す。renderBoard(currentState)を呼ぶのは、②④の根拠・できているマスのtd背景が
 * 開閉状態で変わるため(evidenceSquares/matchedSquaresの計算がreadColumnOpenを見る)。
 * render()全体ではなくこの4関数+盤だけを呼ぶのは、render()のclearSelection()で
 * 盤面クリックの選択状態を勝手に消さないため。
 */
function refreshReadColumnAndBoard(): void {
  if (!currentState) return;
  renderHappened(currentState.plan);
  renderOpponentAim(currentState.coach);
  renderWhy(currentState.coach, currentState.plan);
  renderMyAim(currentState.coach, currentState.plan);
  renderBoard(currentState);
}

function toggleHappened(): void {
  readColumnOpen = { ...readColumnOpen, happened: !readColumnOpen.happened };
  refreshReadColumnAndBoard();
}

/** ②と④は排他(決定2の5)。②を開くときは④を閉じる。 */
function toggleOpponentAim(): void {
  const opening = !readColumnOpen.opponentAim;
  readColumnOpen = {
    ...readColumnOpen,
    opponentAim: opening,
    myAim: opening ? false : readColumnOpen.myAim,
  };
  refreshReadColumnAndBoard();
}

function toggleWhy(): void {
  readColumnOpen = { ...readColumnOpen, why: !readColumnOpen.why };
  refreshReadColumnAndBoard();
}

/** ④と②は排他(決定2の5)。④を開くときは②を閉じる。 */
function toggleMyAim(): void {
  const opening = !readColumnOpen.myAim;
  readColumnOpen = {
    ...readColumnOpen,
    myAim: opening,
    opponentAim: opening ? false : readColumnOpen.opponentAim,
  };
  refreshReadColumnAndBoard();
}

/**
 * ②「相手の狙い」(STEP 5-2)。以前は[2]「狙い」の中でcurrent_shapeと1つの箱に
 * まとまっていたopponent_intentのカードを、独立したブロックとして置く。
 * カード内の小見出し(appendCoachItemのh4)は、ブロックの見出し「② 相手の狙い」と
 * 意味が重複するため出さない(showTitle:false)。purpose/reasonの文はそのまま。
 *
 * 【STEP 5-3(A-2)】要約行(summarizeOpponentAim)+本文(既存の全文)の開閉にした。
 * coachが無い場合の要約は、本文と同じCOACH_UNAVAILABLE_TEXTの1文目を使う
 * (新しい文は作らず、既存文からの抜粋という同じ規則を適用しただけ)。
 */
function renderOpponentAim(coach: CoachExplanation[] | undefined): void {
  const { opponentIntent } = splitCoachByStage(coach);
  const summaryText = !coach
    ? firstSentence(COACH_UNAVAILABLE_TEXT)
    : opponentIntent.length > 0
      ? summarizeOpponentAim(opponentIntent[0]!)
      : "";

  renderExpandableBlock(opponentAimEl, "opponentAim-body", summaryText, readColumnOpen.opponentAim, toggleOpponentAim, (body) => {
    if (!coach) {
      const p = document.createElement("p");
      p.className = "coach-unavailable";
      p.textContent = COACH_UNAVAILABLE_TEXT;
      body.appendChild(p);
      return;
    }

    // STEP 4-6(G-1、人間承認済み): appendAimBadgeを呼ばず、バッジを描画しない
    // (この方針はUnit 3から変えていない)。

    for (const item of opponentIntent) {
      appendCoachItem(body, item, { showTitle: false });
    }

    // STEP 5-4(W-5、人間承認済み。H-1 (a)): 根拠のマス(evidenceSquares)があるときは
    // 常に、承認済みの説明行を本文の末尾に置く。②の本文は開いたときだけ表示される
    // (bodyEl.hidden)ため、この説明行も自然に「開いたときだけ」見える(A-3)。
    const hasEvidence = opponentIntent.some((item) => (item.evidenceSquares?.length ?? 0) > 0);
    if (hasEvidence) {
      const note = document.createElement("p");
      note.className = "board-mark-explanation";
      note.textContent = "盤の淡い青灰の塗り＝この見立ての根拠になった相手の駒";
      body.appendChild(note);
    }
  });
}

/**
 * ④「自分の目的」(STEP 5-2)。directionNote(局面から認識できた方向が1つに
 * 定まらないときの一文。以前は[4]「どう指すか」renderPlanの先頭にあった)→
 * current_shapeのカード(②と同じ理由でshowTitle:false)→ 組み上がり
 * (renderShapeCompletion。できているマス・これから作るマス)の順に並べる。
 * 見せ方の確定(2026-09-11)決定2の1「directionNoteは④の先頭」のとおり。
 *
 * 【STEP 5-3(A-2)】要約行(summarizeMyAim)+本文(既存の全文)の開閉にした。
 */
function renderMyAim(coach: CoachExplanation[] | undefined, plan: ReachablePlanBody): void {
  const { currentShape } = splitCoachByStage(coach);
  const progress = plan.targetShapeProgress;
  const summaryText = !coach
    ? firstSentence(COACH_UNAVAILABLE_TEXT)
    : currentShape.length > 0
      ? summarizeMyAim(currentShape[0]!, progress)
      : "";

  renderExpandableBlock(myAimEl, "myAim-body", summaryText, readColumnOpen.myAim, toggleMyAim, (body) => {
    if (plan.directionNote) {
      const note = document.createElement("p");
      note.className = "direction-note";
      note.textContent = plan.directionNote;
      body.appendChild(note);
    }

    if (!coach) {
      const p = document.createElement("p");
      p.className = "coach-unavailable";
      p.textContent = COACH_UNAVAILABLE_TEXT;
      body.appendChild(p);
    } else {
      for (const item of currentShape) {
        appendCoachItem(body, item, { showTitle: false });
      }
    }

    renderShapeCompletion(body, plan);
  });
}

/**
 * [3]「なぜそれが重要か」。このあと起こりやすいことと、完成した自分の形の弱点。
 * どちらも既存のデータ(intentのnext_aim_explanation / shapeのweak_against)で、
 * 新しい文言は作らない。該当が無ければブロックごと出さない。
 *
 * 【STEP 5-3(A-2)】要約行(summarizeWhy)+本文(既存の全文)の開閉にした。③は②④と
 * 独立(排他の対象ではない)。weaknessだけがあってitemsが無い場合(通常は起こらない。
 * opponent_next_aimはcoachが定義されていれば常に1件生成されるため)、要約は
 * weakness.textの1文目にする(新しい文は作らず、既存の抜粋規則を適用しただけ)。
 */
function renderWhy(coach: CoachExplanation[] | undefined, plan: ReachablePlanBody | undefined): void {
  const items = (coach ?? []).filter((item) => WHY_STAGES.includes(item.stage));
  const weakness = plan?.shapeWeakness ?? null;
  const summaryText = items.length > 0 ? summarizeWhy(items[0]!) : weakness ? firstSentence(weakness.text) : "";

  renderExpandableBlock(whyEl, "why-body", summaryText, readColumnOpen.why, toggleWhy, (body) => {
    if (items.length === 0 && !weakness) return;

    const heading = document.createElement("h3");
    heading.textContent = "なぜそれが重要か";
    body.appendChild(heading);

    for (const item of items) {
      appendCoachItem(body, item);
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

      body.appendChild(section);
    }
  });
}

/**
 * 帯「いま注意する駒」。どのメッセージが該当するかはサーバー側
 * (api/stateResponse.tsのpartitionUrgentMessages)が決めており、web側は表示するだけ。
 * 行の文言(当たり・王手・詰み)は既存のまま変えていない。
 *
 * 【STEP 5-2(見せ方の確定 決定2の2、人間承認済み)】見出しを「今すぐ対処が必要なこと」
 * から「いま注意する駒」へ変える(中身が非評価の事実である利きの有無であることに
 * 見出しを合わせた、承認済みの新しい文言)。該当が無ければ要素ごとhiddenにする
 * (読む列の最上部から帯自体を消し、①が最上段になる)。
 *
 * 【STEP 5-4(W-4、人間承認済み)】当たり(kind === "piece_attacked")の行が4件以上のとき、
 * partitionPieceThreatsForBoardが返す上位3件(盤に描く駒と同じ3件)はそのままの文で出し、
 * 4件目以降は出さず、代わりに「ほかN駒」の1行を置く(承認済み文言)。並び順を保ったまま
 * 挿入するため、超過分の最初の位置に1回だけ置く。王手・詰みの行(kindが違う)・
 * squareの無い旧応答の行は対象外で、従来どおり全件出す(壊れない)。
 */
function renderUrgent(plan: ReachablePlanBody | undefined): void {
  urgentEl.innerHTML = "";
  const messages = plan?.urgentMessages ?? [];
  urgentEl.hidden = messages.length === 0;
  if (messages.length === 0) return;

  const heading = document.createElement("h3");
  heading.textContent = "いま注意する駒";
  urgentEl.appendChild(heading);

  const { drawn, othersCount } = partitionPieceThreatsForBoard(messages);
  const drawnSet = new Set(drawn);

  const list = document.createElement("ul");
  list.className = "urgent-messages";
  let othersInserted = false;
  for (const message of messages) {
    const isTruncatedThreat = message.kind === "piece_attacked" && message.square !== undefined && !drawnSet.has(message);
    if (isTruncatedThreat) {
      if (!othersInserted && othersCount > 0) {
        const othersLi = document.createElement("li");
        othersLi.className = "urgent-others";
        othersLi.textContent = `ほか${othersCount}駒`;
        list.appendChild(othersLi);
        othersInserted = true;
      }
      continue;
    }
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
// 【STEP 4-1】resolveRecognizedDirectionは、現在のstatus(forming/completed)だけでなく、
// 対局のこれまでの指し手履歴の中で一度でもcompletedになった形の集合も見る(一度進んだ
// 認識が、駒が動いて崩れたときに手前の形へ後退しないようにするため)。ranked(順位・
// matchScore)は使わない。この判断はサーバー側のみで行い、web側では判定しない。
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
function renderLastMoveOutcome(target: HTMLElement, plan: ReachablePlanBody): void {
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

  target.appendChild(section);
}

/**
 * [1]「今、盤で起きたこと」。直前の一手と、その手で起きた事実をまとめる。
 * Phase3の「前回の計画が使えなくなりました」もここへ入れ、同じ事実を別ブロックで
 * もう一度述べないようにする(Unit 1 の実測で、同じ事実が4箇所に並んでいた)。
 *
 * 【STEP 5-3(A-2)】要約行(summarizeHappened)+本文(既存の全文)の開閉にした。
 * lastMoveOutcomeが無い(初期局面)場合は要約行が空文字になり、本文も空になる
 * (renderExpandableBlockが開閉の印を出さない)。
 */
function renderHappened(plan: ReachablePlanBody): void {
  const summaryText = summarizeHappened(plan.lastMoveOutcome);

  renderExpandableBlock(happenedEl, "happened-body", summaryText, readColumnOpen.happened, toggleHappened, (body) => {
    renderLastMoveOutcome(body, plan);

    // STEP 4-6(C、人間承認済み): 「前回の計画が使えなくなりました。」と理由文3種は、
    // 理由文がrenderLastMoveOutcome([1]の「〜が取られました」等)と同じ事実を述べており、
    // 「前回の計画」も未説明用語だったため、描画をやめる(shouldShowPlanChangedNotice /
    // getPlanChangeReasonMessageの経路を呼ばない)。gameApi.tsの関数とサーバーの
    // planChangedはAPI互換のため残す。
  });
}

// 【Phase6 Unit1】「選択した形 → その形に必要なマス → 今どこまで出来ているか →
// 未達成部分の経路 → その経路の最初の一手」という因果を画面に出す。
// ここで行うのは、サーバーが返した値(plan.targetShapeProgress / plan.routes、
// マス目は既に日本語表記に変換済み)の表示のみで、判定・計算は一切しない。
// 「この手が良いから表示している」と誤解させないため、候補手が「形に近づく経路の
// 一手」であることを言葉で明示し、強さ・良し悪しには一切触れない。
//
// 【STEP 5-2(構造。人間承認済み)】以前は1つの関数(renderRouteProgress)が
// 「組み上がり」(見出し・できているマス・これから作るマス)と「道のりの一覧」
// (各目標マスへの残り手数・塞がり)を1つの.route-sectionにまとめて[4]「どう指すか」
// (旧planEl)へ描いていたが、見せ方の確定(決定2の1)により組み上がりは④「自分の目的」
// (myAimEl)へ、道のりの一覧は操作する列の折りたたみ(#routeList)へ分かれた。
// そのため関数を renderShapeCompletion(組み上がり) と renderRouteList(道のりの一覧)
// の2つに分ける。文言・判定は変えていない。
function renderShapeCompletion(target: HTMLElement, plan: ReachablePlanBody): void {
  const progress = plan.targetShapeProgress;
  if (!progress) return;

  const section = document.createElement("div");
  section.className = "route-section";

  const heading = document.createElement("h3");
  heading.textContent = `「${progress.name}」${reviewNoteSuffix(progress.pendingReviewNote)}の組み上がり`;
  section.appendChild(heading);

  // Unit 3(重複の除去): 形の説明(characteristics)はここには出さない。
  // 同じ文が [5]「参考になる囲い」にもあり、同じ内容を2箇所で述べることになるため
  // ([5] を「囲いを知る場所」、ここ ④ を「どう指すかを見る場所」と役割で分ける)。
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

  // 【STEP 5-2(A-2、人間承認済み)】以前は「これから作るマス: X、Y」という行は、
  // routesが空(道のりが無い)場合にだけ出ていた(routesがあるときは、この文言の
  // 代わりに下の道のり一覧の見出し「これから作るマスと、そこまでの道のり:」の中に
  // しか現れていなかった)。道のり一覧を④の外(操作する列の折りたたみ)へ移したため、
  // ④単独でも「これから作るマスは何か」が分かるよう、routesの有無に関わらず
  // このマス目一覧の行を常に出す(0件なら行自体を出さない)。これは新しい文ではなく、
  // 既存文(下のroutes.length===0の分岐と同じ文言)をroutesがある場合にも広げた
  // 派生表示であり、括弧書き「(道のりは今の局面では計算できませんでした)」は
  // routesが実際に計算できている場合には付けない(routesが0件かつ除外でない場合の
  // 5-1の出し分けはそのまま維持する)。
  if (progress.missingSquareLabels.length > 0) {
    const note = document.createElement("p");
    note.className = "route-note";
    if (plan.routes.length > 0) {
      note.textContent = `これから作るマス: ${progress.missingSquareLabels.join("、")}`;
    } else {
      // STEP 5-1(A-4、人間承認済み。LP-1): 候補手が除外された結果routesが空のときは、
      // 「道のりは今の局面では計算できませんでした」という括弧書きが事実に反する
      // (道のりは計算できたが、候補手を表示していないだけ)。isCandidateMovesExcludedは
      // A-1と同一条件をサーバーの確定値から読むだけの純粋関数で、web側で新しい判定は
      // 持たない。既存文から括弧書きを外すだけで、新しい文は作らない。
      note.textContent = isCandidateMovesExcluded(plan)
        ? `これから作るマス: ${progress.missingSquareLabels.join("、")}`
        : `これから作るマス: ${progress.missingSquareLabels.join("、")}(道のりは今の局面では計算できませんでした)`;
    }
    section.appendChild(note);
  }

  // STEP 5-4(W-5、人間承認済み。H-1 (a)): matchedSquares・missingSquaresの
  // どちらかがあるときは常に、承認済みの説明行を本文の末尾に置く(開閉・排他は5-3)。
  // 文言は一字も変えない。
  if ((progress.matchedSquares?.length ?? 0) > 0 || (progress.missingSquares?.length ?? 0) > 0) {
    const explanation = document.createElement("p");
    explanation.className = "board-mark-explanation";
    explanation.textContent = "盤の淡い緑の塗り＝できているマス、破線の輪＝これから作るマス";
    section.appendChild(explanation);
  }

  target.appendChild(section);
}

/** 操作する列の折りたたみ「道のり」。各目標マスへの残り手数・塞がりの一覧
 * (renderShapeCompletionから分離。文言・判定は変えていない)。 */
function renderRouteList(plan: ReachablePlanBody): void {
  routeListEl.innerHTML = "";
  if (plan.routes.length === 0) return;

  const routesHeading = document.createElement("p");
  routesHeading.className = "route-list-heading";
  routesHeading.textContent = "これから作るマスと、そこまでの道のり:";
  routeListEl.appendChild(routesHeading);

  const list = document.createElement("ul");
  list.className = "route-list";
  for (const route of plan.routes) {
    const li = document.createElement("li");

    // 【Phase 7 Unit 3(詰まりの可視化)。人間承認済み】
    // 以前は「玉を８八へ … 残り1手(７八→８八)」の1行だけで、初心者には
    // 「玉を８八へ動かせばいい」としか読めなかった(なぜ進めないのかが画面に無い)。
    // 目標・残り手数・塞がりの事実を行で分け、道のりの中で完結させる。
    const target = document.createElement("span");
    target.className = "route-main";
    target.textContent = `${route.targetPiece}を${route.targetSquareLabel}へ`;
    li.appendChild(target);

    const steps = document.createElement("span");
    steps.className = "route-steps";
    steps.textContent = `残り${route.remainingSteps}手(${route.routeLabel})`;
    li.appendChild(steps);

    // 「どのマスを、何の駒が塞いでいるか」は現在の盤のそのマスを読むだけ、
    // 「その駒に指せる手があるか」は合法手を移動元で絞るだけの機械的な事実で、
    // どちらもサーバー側(routePlanner.ts / stateResponse.ts)で確定済み。
    // ここでは受け取った値を並べるだけで、将棋の判断は一切しない。
    if (route.blockingSquareLabel !== null && route.blockingPieceName !== null) {
      const blocked = document.createElement("span");
      blocked.className = "route-blocked";
      blocked.textContent = `${route.blockingSquareLabel}が${route.blockingPieceName}で塞がっています。`;
      li.appendChild(blocked);

      // その駒に合法手が1つも無い場合だけ添える(合法手がある場合は、その手が
      // 下の候補手に「次の一歩」として並ぶため、ここで重ねて述べない)。
      if (route.blockingSquareHasLegalMove === false) {
        const stuck = document.createElement("span");
        stuck.className = "route-blocked";
        stuck.textContent = `その${route.blockingPieceName}から指せる手はありません。`;
        li.appendChild(stuck);
      }
    }

    // Unit 3(情報構造の整理): ここにあった2つの注記は今も出さない。
    // - 「この道のりの一手目は、今の局面では指せません。」は、同じ画面の下に候補手が
    //   並ぶため矛盾して読める。サーバー側(filterContradictoryConsiderations)で
    //   同種の一文を出し分けており、ここでも繰り返さない
    // 一方「◯◯には今、自分の駒があります。」に相当する事実は、Phase 7 Unit 3 で
    // 候補手の理由文から外し、上の .route-blocked へ一本化した(置き場所の変更であり、
    // 判定・データは変えていない)。

    list.appendChild(li);
  }
  routeListEl.appendChild(list);
}

/**
 * STEP 5-3(A-4、人間承認済み。H-1〜H-3): 候補手のボタンが0件のとき、⑤に出す
 * 「候補手が出ない理由の文」を決める。
 *
 * - 除外(isCandidateMovesExcluded): 5-1の一文(サーバー側stateResponse.tsが
 *   candidatesExcluded時にplan.nextConsiderationsの先頭へ必ず入れる契約
 *   (kind: "candidate_moves_excluded")なので、先頭の要素の文をそのまま使う。
 * - unavailable: nextConsiderationsの理由文(先頭の要素。あれば)。無ければ既存の
 *   「現在の局面では、この形に近づく候補手を表示できません。」の文。
 * - pending: 既存の「候補手を計算中です(しばらくすると表示されます)。」の文。
 * - それ以外(候補手が0件の理由が上記いずれでもない、既存仕様で元々何も表示して
 *   いなかった状態): null(何も表示しない。今回の変更対象外)。
 *
 * 文言はすべて既存のもの(サーバーの値、または元からある固定文)で、混ぜて
 * 新しい文は作らない。以前あった小見出し「今の局面で分かっていること」
 * (旧renderNextConsiderations)は出さない(H-2)。
 */
function candidateAbsenceReasonText(plan: ReachablePlanBody): string | null {
  if (isCandidateMovesExcluded(plan)) {
    return plan.nextConsiderations[0]?.text ?? null;
  }
  if (plan.candidateMoveState === "unavailable") {
    return plan.nextConsiderations[0]?.text ?? "現在の局面では、この形に近づく候補手を表示できません。";
  }
  if (plan.candidateMoveState === "pending") {
    return "候補手を計算中です(しばらくすると表示されます)。";
  }
  return null;
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

  // 【STEP 5-2(構造。人間承認済み)】directionNoteは④「自分の目的」(renderMyAim)の
  // 先頭へ移した(見せ方の確定 決定2の1)。組み上がり(renderShapeCompletion)も④へ、
  // 道のりの一覧(renderRouteList)は操作する列の折りたたみへ移り、ここでは呼ばない。
  // 【STEP 5-3(A-4、人間承認済み)】以前ここにあった「今の局面で分かっていること」
  // (旧renderNextConsiderations)の小見出しは出さない(H-2)。候補手が0件のときの
  // 理由文はcandidateAbsenceReasonTextに一本化した(下記)。

  // Unit 3(既知事項 U0-1 の解消): 目標形が選ばれていない間は、候補手セクションを
  // まるごと出さない。以前は未選択でも「この形へ近づく手の候補」「この形に近づく
  // 候補手を表示できません。」という、指す対象の無い文言が常時出ていた。
  // 代わりの文言は新しく作らず、セクションごと出さないことで解消する。
  if (selectedShapeName === null) return;

  // 【Phase5 #7 要件2・4・6】候補手セクション本体。
  // reachableShapesが0件(=認識できた方向が無い)場合でも、候補手が
  // "ready"/"pending"/"unavailable"のいずれかであれば、その状態を伝える。
  // candidateMove.status: "not_ready"(candidateMoveStateは"ready")の場合のみ、
  // 既存仕様のまま何も表示しない(今回の変更対象外)。
  const hasReadyExplanation =
    plan.candidateMoveState === "ready" &&
    plan.candidateMove?.status === "ready" &&
    (plan.candidateMove?.explanations.length ?? 0) > 0;

  // 【STEP 5-3(A-4、人間承認済み。H-1〜H-3)】候補手のボタンが0件のときは、
  // 見出し「「{形}」に近づく手の候補」・説明文・「次の一歩」「この先」の小見出しを
  // 一切出さず、理由の文だけを⑤に出す(決定2の4の⑤)。
  if (!hasReadyExplanation) {
    const reasonText = candidateAbsenceReasonText(plan);
    if (reasonText === null) return;

    const p = document.createElement("p");
    p.className =
      plan.candidateMoveState === "pending"
        ? "plan-pending"
        : isCandidateMovesExcluded(plan)
          ? "plan-excluded"
          : "plan-unavailable";
    p.textContent = reasonText;
    planEl.appendChild(p);
    return;
  }

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
  // 【STEP 5-3(H-1、人間承認済み)】「上の」を削除した(道のりは④の折りたたみへ
  // 移り、この位置と合わなくなっていたため。既存文からの削除のみ、新しい文は
  // 作らない)。
  const description = document.createElement("p");
  description.className = "candidate-section-description";
  description.textContent =
    "道のりのうち、今の局面で指せる最初の一手です。将棋として最も良い手を選んでいるわけではありません。";
  candidateSection.appendChild(description);

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
  const groups = groupCandidateExplanationsByReason(plan.candidateMove!.explanations, plan.candidateMoveLabels);
  for (const group of groups) {
    const section = document.createElement("section");
    section.className = "candidate-move";

    // 【Phase 7 Unit 3。人間承認済み】候補手を「次の一歩」(今この局面で指せる手)と
    // 「この先」(その手のあと何ができるようになるか)の2段に分ける。以前は
    // 「候補手: ◯◯」の1行に、経路の1手目も準備手も区別なく横並びになっていた。
    // どちらに属するかの区別はサーバー側の kind / clearingSquare / targetPiece /
    // targetSquare から既に決まっており(reasonの文面がそれを反映する)、
    // web側で新しい判定はしない。「この手を指せば囲いが完成に近づく」のような
    // 意味付けは足さない。
    const nextStepHeading = document.createElement("p");
    nextStepHeading.className = "candidate-move-subheading";
    nextStepHeading.textContent = "次の一歩";
    section.appendChild(nextStepHeading);

    const moveLabel = document.createElement("p");
    moveLabel.className = "candidate-move-usi";
    // 【Phase6 Unit1】マス目はサーバー側(notation/japaneseSquare.ts)で変換済みの
    // 日本語表記を使う。対応表に無い場合(想定外)はUSI表記へフォールバックする。
    // 【Phase 7】1手ずつ独立したボタンにして、押した手だけを盤上で濃くする
    // (人間承認済み)。押しても対局は進まない ― 指す操作は従来どおり盤のクリックだけで、
    // ここは盤のどこを指しているかを見るためのものである。
    group.moves.forEach((move, index) => {
      if (index > 0) moveLabel.appendChild(document.createTextNode(" / "));
      const button = document.createElement("button");
      button.type = "button";
      button.className =
        move.usi === emphasizedCandidateUsi
          ? "candidate-move-button candidate-move-button-emphasized"
          : "candidate-move-button";
      button.textContent = move.label;
      button.setAttribute("aria-pressed", String(move.usi === emphasizedCandidateUsi));
      button.addEventListener("click", () => {
        // もう一度押したら強調をやめる(既定の「全件を薄く」へ戻る)。
        emphasizedCandidateUsi = move.usi === emphasizedCandidateUsi ? null : move.usi;
        if (currentState) {
          renderBoard(currentState);
          renderPlan(currentState.plan);
        }
      });
      moveLabel.appendChild(button);
    });
    section.appendChild(moveLabel);

    const aheadHeading = document.createElement("p");
    aheadHeading.className = "candidate-move-subheading";
    aheadHeading.textContent = "この先";
    section.appendChild(aheadHeading);

    const reason = document.createElement("p");
    reason.className = "candidate-move-reason";
    reason.textContent = group.reason;
    section.appendChild(reason);

    candidateSection.appendChild(section);
  }

  planEl.appendChild(candidateSection);
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

// 【Phase 7: 候補手の盤上表示(人間承認済み)】
//
// docs/PHASES.md の Unit 3 は「盤面上の対象駒 → 移動元を強調 → 移動先を矢印で表示」を
// 基本UIとして掲げているが、これまで盤に出ていたのは相手の直前の手だけで、候補手は
// 右カラムの文字情報にとどまっていた。ここでその不足を埋める。
//
// 【この描画が絶対にしないこと】
// 将棋の判断は一切しない。描くマスは候補手のUSIから機械的に決まる。順位付け・強調による
// おすすめの表明もしない(既定では全件を同じ薄さで描く)。描く対象は
// candidateMove.explanations にある手だけであり、これは CLAUDE.md「絶対に守るルール」3番
// (安全確認を経ていない候補手を見せない)に従って既に画面に出ている手と同一である
// (盤にだけ余分な手が出ることはない)。
//
// 【視覚言語(人間承認済み)】
// 既存のハイライトは、背景色(選択中・移動先)と青の実線枠(相手の直前の手)を使っている。
// 候補手はそれらより弱い「灰色の細い破線」にして、最善手と読めないようにする。
// 既定は全件を薄く、候補手の行を押したときだけその1件を濃くする(濃くしても青の実線より弱い)。
let emphasizedCandidateUsi: string | null = null;

/** 描画中の盤で、マス名 -> そのマスの td を引くための表(renderBoardが毎回作り直す)。 */
let squareCells = new Map<string, HTMLTableCellElement>();

const SVG_NS = "http://www.w3.org/2000/svg";

/**
 * STEP 5-4(W-2・W-3・W-4、人間承認済み): 盤に重ねたSVGへ、候補手の破線矢印(既存のまま)と、
 * 盤の印(事実の印。常時)をまとめて描く。
 *
 * - 候補手の破線矢印: 従来どおり(変更なし)。
 * - 事実の印(常時): 当たっている自分の駒 = 実線の赤い輪、当てている相手の駒 = 細い赤枠。
 *   マスはboardMarksFromState(サーバーの既存結果から取り出すだけの純粋関数)から取り、
 *   web側で利きを判定しない。当たりが4駒以上の場合はpartitionPieceThreatsForBoardにより
 *   上位3件しか渡ってこない(boardMarksFromStateの内部でも同じ関数を使う)。
 * - ④のこれから作るマス = 破線の輪(できているマスの淡い緑・②の根拠の淡い青灰の塗りは
 *   tdの背景で表すため、ここでは描かない。renderBoard側でクラスを付ける)。
 *
 * マスの位置は描画済みの td の実寸(getBoundingClientRect)から求めるため、盤のサイズや
 * 段・筋の目盛りの有無に依存しない。盤がまだレイアウトされていない場合は何も描かない。
 *
 * 凡例(#boardLegend)は「当たり / 直前の手 / 次の一歩」の3項目を、印の有無にかかわらず
 * 常時出す(H-2、人間の決定)。
 *
 * 【STEP 5-3(A-3、人間承認済み)】openStateを受け取り、④のこれから作るマスの破線の輪は
 * openState.myAimが開いているときだけ描く(決定2の5)。事実の印(当たり・攻め駒)は
 * 開閉に関わらず常時描く(F-5・5-4のまま)。
 */
function renderBoardMarks(
  plan: ReachablePlanBody,
  coach: CoachExplanation[] | undefined,
  openState: Pick<ReadColumnOpenState, "myAim">,
): void {
  boardOverlayEl.replaceChildren();
  boardLegendEl.replaceChildren();

  const areaRect = boardAreaEl.getBoundingClientRect();
  if (areaRect.width === 0 || areaRect.height === 0) return;

  boardOverlayEl.setAttribute("viewBox", `0 0 ${areaRect.width} ${areaRect.height}`);
  boardOverlayEl.setAttribute("width", String(areaRect.width));
  boardOverlayEl.setAttribute("height", String(areaRect.height));

  // 矢じり。薄い線用と濃い線用で色が違うため2つ用意する(形は同じ)。
  const defs = document.createElementNS(SVG_NS, "defs");
  for (const [id, color] of [["candidateArrowHead", "#8a8a8a"], ["candidateArrowHeadEmphasized", "#4a4a4a"]]) {
    const marker = document.createElementNS(SVG_NS, "marker");
    marker.setAttribute("id", id!);
    marker.setAttribute("viewBox", "0 0 10 10");
    marker.setAttribute("refX", "9");
    marker.setAttribute("refY", "5");
    marker.setAttribute("markerWidth", "5");
    marker.setAttribute("markerHeight", "5");
    marker.setAttribute("orient", "auto-start-reverse");
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", "M 0 1 L 10 5 L 0 9 z");
    path.setAttribute("fill", color!);
    marker.appendChild(path);
    defs.appendChild(marker);
  }
  boardOverlayEl.appendChild(defs);

  const rectOf = (squareName: string): DOMRect | null => {
    const cell = squareCells.get(squareName);
    return cell ? cell.getBoundingClientRect() : null;
  };

  const centerOf = (squareName: string): { x: number; y: number } | null => {
    const rect = rectOf(squareName);
    if (!rect) return null;
    return { x: rect.left - areaRect.left + rect.width / 2, y: rect.top - areaRect.top + rect.height / 2 };
  };

  // 候補手の破線矢印(既存のまま。変更なし)。
  const moveUsis = candidateMoveUsisOnBoard(plan);
  for (const moveUsi of moveUsis) {
    // 移動元・移動先の解釈は、相手の直前の手のハイライトと同じ既存関数を使う
    // (同じことを2つの関数で書かない)。打つ手には移動元が無いため描かない
    // ― routePlanner.tsは打つ手を候補にしないので通常は起こらないが、
    // 描けないものを推測で描かない。
    const squares = parseMoveSquares(moveUsi);
    if (squares.from === undefined) continue;

    const from = centerOf(squares.from);
    const to = centerOf(squares.to);
    if (!from || !to) continue;

    const emphasized = moveUsi === emphasizedCandidateUsi;
    const line = document.createElementNS(SVG_NS, "line");
    line.setAttribute("x1", String(from.x));
    line.setAttribute("y1", String(from.y));
    line.setAttribute("x2", String(to.x));
    line.setAttribute("y2", String(to.y));
    line.setAttribute("class", emphasized ? "candidate-arrow candidate-arrow-emphasized" : "candidate-arrow");
    line.setAttribute(
      "marker-end",
      emphasized ? "url(#candidateArrowHeadEmphasized)" : "url(#candidateArrowHead)",
    );
    boardOverlayEl.appendChild(line);

    const origin = document.createElementNS(SVG_NS, "circle");
    origin.setAttribute("cx", String(from.x));
    origin.setAttribute("cy", String(from.y));
    origin.setAttribute("r", "4");
    origin.setAttribute("class", emphasized ? "candidate-origin candidate-origin-emphasized" : "candidate-origin");
    boardOverlayEl.appendChild(origin);
  }

  // STEP 5-4(W-2・W-4): 事実の印(常時)。当たっている自分の駒 = 実線の赤い輪、
  // 当てている相手の駒 = 細い赤枠。青枠(直前の手)と同じマスに重なっても両方描く。
  const marks = boardMarksFromState(plan, coach);

  for (const squareName of marks.attacked) {
    const rect = rectOf(squareName);
    const center = centerOf(squareName);
    if (!rect || !center) continue;
    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("cx", String(center.x));
    circle.setAttribute("cy", String(center.y));
    circle.setAttribute("r", String(rect.width * 0.44));
    circle.setAttribute("class", "board-mark-attacked");
    boardOverlayEl.appendChild(circle);
  }

  for (const squareName of marks.attackers) {
    const rect = rectOf(squareName);
    const center = centerOf(squareName);
    if (!rect || !center) continue;
    const side = rect.width * 0.85;
    const square = document.createElementNS(SVG_NS, "rect");
    square.setAttribute("x", String(center.x - side / 2));
    square.setAttribute("y", String(center.y - side / 2));
    square.setAttribute("width", String(side));
    square.setAttribute("height", String(side));
    square.setAttribute("class", "board-mark-attacker");
    boardOverlayEl.appendChild(square);
  }

  // STEP 5-4(W-5)→5-3(A-3、人間承認済み): ④これから作るマスの破線の輪は、
  // ④が開いているときだけ描く(決定2の5)。できているマス(淡い緑)・②の根拠
  // (淡い青灰)はtdの背景で表す(renderBoard側。同じくopenStateで開閉に連動)。
  if (openState.myAim) {
    for (const squareName of marks.missing) {
      const rect = rectOf(squareName);
      const center = centerOf(squareName);
      if (!rect || !center) continue;
      const circle = document.createElementNS(SVG_NS, "circle");
      circle.setAttribute("cx", String(center.x));
      circle.setAttribute("cy", String(center.y));
      circle.setAttribute("r", String(rect.width * 0.38));
      circle.setAttribute("class", "board-mark-missing");
      boardOverlayEl.appendChild(circle);
    }
  }

  // STEP 5-4(W-3、人間承認済み。H-2): 凡例「当たり / 直前の手 / 次の一歩」の3項目を、
  // 印の有無にかかわらず常時出す(注記なし)。
  const legend = document.createElement("ul");
  legend.className = "board-legend-list";

  const attackedItem = document.createElement("li");
  attackedItem.className = "board-legend-item";
  const ringIcon = document.createElement("span");
  ringIcon.className = "board-legend-icon board-legend-icon-ring";
  const squareIcon = document.createElement("span");
  squareIcon.className = "board-legend-icon board-legend-icon-square";
  attackedItem.append(ringIcon, squareIcon, document.createTextNode("当たり"));

  const lastMoveItem = document.createElement("li");
  lastMoveItem.className = "board-legend-item";
  const frameIcon = document.createElement("span");
  frameIcon.className = "board-legend-icon board-legend-icon-frame";
  lastMoveItem.append(frameIcon, document.createTextNode("直前の手"));

  const candidateItem = document.createElement("li");
  candidateItem.className = "board-legend-item";
  const arrowIcon = document.createElement("span");
  arrowIcon.className = "board-legend-icon board-legend-icon-arrow";
  candidateItem.append(arrowIcon, document.createTextNode("次の一歩"));

  legend.append(attackedItem, lastMoveItem, candidateItem);
  boardLegendEl.appendChild(legend);
}

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
  // Phase 7: 盤上に候補手を描くための、マス名 -> td の対応表を作り直す。
  squareCells = new Map<string, HTMLTableCellElement>();

  // STEP 5-4(W-5、人間承認済み。H-1 (a))→5-3(A-3、人間承認済み): ②の根拠のマス
  // (淡い青灰)・④のできているマス(淡い緑)のtd背景は、印の座標をサーバーの既存結果
  // から取り出すだけの純粋関数(boardMarksFromState)から取る(web側で判定しない)。
  // 5-3で②④に開閉を付けたため、その列が開いているときだけ塗る(決定2の5)。
  const boardMarks = boardMarksFromState(state.plan, state.coach);
  const evidenceSquares = new Set(readColumnOpen.opponentAim ? boardMarks.evidence : []);
  const matchedSquares = new Set(readColumnOpen.myAim ? boardMarks.matched : []);

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
      squareCells.set(squareName, td);
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

      // STEP 5-4(W-5、人間承認済み。H-1 (a)): 根拠があるときは常に塗る。選択中・移動先の
      // 背景(!important)が付く場合はそちらが勝つ(操作中の見え方を優先、style.css参照)。
      if (evidenceSquares.has(squareName)) td.classList.add("square-opponent-evidence");
      if (matchedSquares.has(squareName)) td.classList.add("square-shape-matched");

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

  // 盤の描画が終わってから、その実寸を使って候補手・盤の印を重ね描きする。
  renderBoardMarks(state.plan, state.coach, readColumnOpen);
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
    // STEP 4-5(Y-1、人間承認済み): 文字列の組み立てはgameApi.tsの純粋関数に切り出した
    // (結果種別の英語の括弧書きを削除しただけで、勝者の表記は変えていない)。
    statusEl.textContent = formatGameEndStatus(state.status);
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
  // Phase 7: 局面が変わったら候補手の強調を解除する(前の局面で押した手を残さない)。
  // render()は同じ局面のまま何度も呼ばれる(バックグラウンド解析の再取得)ため、
  // sfenが変わったときだけ解除する。
  if (state.sfen !== lastRenderedSfen) emphasizedCandidateUsi = null;
  currentState = state;
  clearSelection();
  updateLastOpponentMoveHighlight(state.moveHistory);
  lastRenderedSfen = state.sfen;
  renderBoard(state);
  renderHands(state);
  renderStatus(state);
  renderHistory(state.moveHistory, state.moveHistoryJapanese);
  // 【STEP 5-2(構造。人間承認済み)】読む列(帯 → ① → ② → ③ → ④)→
  // 操作する列(⑤ → 道のり → 参考になる囲い)の順に描く。
  renderUrgent(state.plan);
  renderHappened(state.plan);
  renderOpponentAim(state.coach);
  renderWhy(state.coach, state.plan);
  renderMyAim(state.coach, state.plan);
  renderRouteList(state.plan);
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
  await playMove(move);
  // STEP 4-7B(P-11。人間承認済み): 成功・失敗(非合法・通信エラー)にかかわらず
  // 入力欄をクリアする。
  moveInput.value = "";
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
  // STEP 4-7B(P-11。人間承認済み): 「新しい対局」時も入力欄をクリアする。
  moveInput.value = "";
  // STEP 5-3(A-2、人間承認済み。H-4 (a)): 新しい対局では①〜④の開閉を既定
  // (①開・②③④閉)へ戻す(手が進んでも維持する開閉と違い、対局そのものが
  // 変わるため)。
  readColumnOpen = { ...DEFAULT_READ_COLUMN_OPEN };
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
