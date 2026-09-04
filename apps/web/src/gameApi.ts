// apps/serverの最小HTTP APIへのフェッチラッパー。
// 開発時はvite.config.tsのプロキシ設定により、相対パス"/api/..."がapps/serverへ転送される。

export interface GameOutcome {
  result: string;
  winner: "sente" | "gote" | undefined;
}

export interface GameStatus {
  isEnd: boolean;
  outcome: GameOutcome | undefined;
}

// apps/server/src/analysis/explanationGenerator.ts の CoachExplanation に対応する型。
// data/schemas/explanations.schema.json 準拠のフィールド(purpose/reason等)に、
// UI側でforming/matched/completed/noneを出し分けるためのstatusを加えたもの。
export type CoachStage = "current_shape" | "opponent_intent" | "opponent_next_aim";
export type CoachStatus = "none" | "forming" | "matched" | "completed";
export type ConfidenceLevel = "high" | "medium" | "low";

export interface CoachExplanation {
  id: string;
  stage: CoachStage;
  purpose: string;
  reason: string;
  refers_to_shape_id: string | null;
  refers_to_intent_id: string | null;
  confidence_level: ConfidenceLevel;
  glossary_terms: string[];
  template_id: string;
  status: CoachStatus;
}

export interface GameStateResponse {
  sfen: string;
  moveHistory: string[];
  forcedPliesUsed: number;
  status: GameStatus;
  // 説明生成に失敗した場合(想定外の不整合等)はundefined(対局自体は継続する)。
  coach: CoachExplanation[] | undefined;
}

export interface MoveErrorResponse {
  error: string;
}

export function isMoveError(body: GameStateResponse | MoveErrorResponse): body is MoveErrorResponse {
  return "error" in body;
}

async function parseJson<T>(res: Response): Promise<T> {
  return (await res.json()) as T;
}

export async function fetchGameState(): Promise<GameStateResponse> {
  const res = await fetch("/api/game");
  return parseJson<GameStateResponse>(res);
}

export async function startNewGame(): Promise<GameStateResponse> {
  const res = await fetch("/api/game/new", { method: "POST" });
  return parseJson<GameStateResponse>(res);
}

export async function submitMove(move: string): Promise<GameStateResponse | MoveErrorResponse> {
  const res = await fetch("/api/game/move", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ move }),
  });
  return parseJson<GameStateResponse | MoveErrorResponse>(res);
}
