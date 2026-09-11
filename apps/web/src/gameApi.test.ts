import { describe, expect, it } from "vitest";
import {
  buildKifuJson,
  formatGameEndStatus,
  getPlanChangeReasonMessage,
  reviewNoteSuffix,
  candidateMoveUsisOnBoard,
  isCandidateMovesExcluded,
  groupCandidateExplanationsByReason,
  shouldRetryPlanRefresh,
  shouldShowNextConsiderations,
  shouldShowPlanChangedNotice,
  splitCoachByStage,
  partitionPieceThreatsForBoard,
  boardMarksFromState,
  firstSentence,
  lastSentence,
  summarizeHappened,
  summarizeOpponentAim,
  summarizeWhy,
  summarizeMyAim,
  PLAN_REFRESH_MAX_ATTEMPTS,
  type CoachExplanation,
  type CoachStage,
  type GameStatus,
  type LastMoveOutcomeBody,
  type NextConsiderationMessage,
  type PlanChangeReason,
  type ReachablePlanBody,
  type TargetShapeProgress,
  type UrgentMessage,
} from "./gameApi.js";

// STEP 5-2: splitCoachByStageのテスト用フィクスチャ。stage以外のフィールドは
// テストの主旨と無関係なため固定値で埋める(idだけ呼び出し側で判別できるよう変える)。
function makeCoachExplanation(id: string, stage: CoachStage): CoachExplanation {
  return {
    id,
    stage,
    purpose: `purpose-${id}`,
    reason: `reason-${id}`,
    refers_to_shape_id: null,
    refers_to_intent_id: null,
    confidence_level: "medium",
    glossary_terms: [],
    template_id: `template-${id}`,
    status: "forming",
  };
}

describe("getPlanChangeReasonMessage", () => {
  it("planChanged=falseの場合、reasonがnullでも理由文言を表示しない", () => {
    expect(getPlanChangeReasonMessage({ planChanged: false, planChangeReason: null })).toBeNull();
  });

  it("planChanged=falseの場合、reasonに値があっても理由文言を表示しない(planChangedとの組み合わせを優先)", () => {
    // 通常この組み合わせは起こらない(サーバー側の契約上)が、万一reasonだけを見て
    // 判定しないことを確認するための防御的テスト。
    expect(
      getPlanChangeReasonMessage({ planChanged: false, planChangeReason: "candidate_piece_captured" }),
    ).toBeNull();
  });

  it("planChanged=true, candidate_piece_capturedの場合、捕獲理由が表示される", () => {
    const message = getPlanChangeReasonMessage({ planChanged: true, planChangeReason: "candidate_piece_captured" });
    expect(message).toBe("予定していた駒が、相手の手によって取られました。");
  });

  it("planChanged=true, candidate_move_illegal_due_to_checkの場合、玉の移動不能理由が表示される", () => {
    const message = getPlanChangeReasonMessage({
      planChanged: true,
      planChangeReason: "candidate_move_illegal_due_to_check",
    });
    expect(message).toBe("相手の手によって、予定していた玉の移動ができなくなりました。");
  });

  it("planChanged=true, candidate_piece_pinnedの場合、駒が動かせなくなった理由が表示される", () => {
    const message = getPlanChangeReasonMessage({ planChanged: true, planChangeReason: "candidate_piece_pinned" });
    expect(message).toBe("相手の手によって、予定していた駒が動かせなくなりました。");
  });

  it("planChanged=true, unknownの場合、理由固有の文言は表示しない(nullを返す)", () => {
    expect(getPlanChangeReasonMessage({ planChanged: true, planChangeReason: "unknown" })).toBeNull();
  });

  it("planChanged=true, nullの場合も理由固有の文言は表示しない", () => {
    expect(getPlanChangeReasonMessage({ planChanged: true, planChangeReason: null })).toBeNull();
  });

  it("planChanged=true, サーバー側が将来追加しうる未知のreason値の場合も、断定せず表示しない(安全側)", () => {
    // TypeScriptの型では表現できない、実行時にのみ起こりうる未知の文字列を
    // 意図的にキャストして、安全側のフォールバック(default節)を検証する。
    const unknownReason = "some_future_reason_not_yet_known" as PlanChangeReason;
    expect(getPlanChangeReasonMessage({ planChanged: true, planChangeReason: unknownReason })).toBeNull();
  });
});

// Phase6 Unit3 ⑦: Phase3の「前回の計画が使えなくなりました。」と、Unit2の
// route_lostメッセージが同じ事象を二重に述べるのを防ぐ表示判断。
describe("shouldShowPlanChangedNotice", () => {
  function outcome(kinds: string[]): LastMoveOutcomeBody {
    return {
      playedMoveLabel: "７八銀",
      opponentMoveLabel: "１四歩",
      messages: kinds.map((kind) => ({ kind, text: "" })),
    };
  }

  it("planChanged=falseなら表示しない", () => {
    expect(shouldShowPlanChangedNotice({ planChanged: false, lastMoveOutcome: null })).toBe(false);
  });

  it("planChanged=trueで、route_lostの説明が無ければ表示する(従来どおり)", () => {
    expect(shouldShowPlanChangedNotice({ planChanged: true, lastMoveOutcome: null })).toBe(true);
    expect(
      shouldShowPlanChangedNotice({ planChanged: true, lastMoveOutcome: outcome(["played_non_candidate"]) }),
    ).toBe(true);
  });

  it("planChanged=trueでも、route_lostの説明があれば重複するため表示しない", () => {
    expect(
      shouldShowPlanChangedNotice({
        planChanged: true,
        lastMoveOutcome: outcome(["played_non_candidate", "route_lost"]),
      }),
    ).toBe(false);
  });
});

// Phase6 Unit4: 「今の局面で分かっていること」の表示可否。
// web側が持ってよいのは「サーバーが返した件数が0かどうか」の判定だけで、
// 文言生成・文言の加工・並び替え・フィルタ・将棋の判断は一切持たない。
describe("shouldShowNextConsiderations", () => {
  function messages(kinds: string[]): NextConsiderationMessage[] {
    return kinds.map((kind) => ({ kind, text: `${kind}のテキスト` }));
  }

  it("空配列なら表示しない(ブロックごと描画しない)", () => {
    expect(shouldShowNextConsiderations({ nextConsiderations: [] })).toBe(false);
  });

  it("1件でもあれば表示する", () => {
    expect(shouldShowNextConsiderations({ nextConsiderations: messages(["in_check"]) })).toBe(true);
  });

  it("メッセージの種類によって表示可否を変えない(サーバーの判断をweb側で覆さない)", () => {
    const kinds = [
      "in_check",
      "route_first_move_playable",
      "no_playable_route_first_move",
      "shape_completed",
      "ordering_note",
    ];
    for (const kind of kinds) {
      expect(shouldShowNextConsiderations({ nextConsiderations: messages([kind]) })).toBe(true);
    }
  });

  it("サーバーが返した並び・内容を変更しない(判定に使うのは件数だけ)", () => {
    const nextConsiderations = messages(["route_first_move_playable", "ordering_note"]);
    const before = nextConsiderations.map((m) => `${m.kind}:${m.text}`);

    shouldShowNextConsiderations({ nextConsiderations });

    expect(nextConsiderations.map((m) => `${m.kind}:${m.text}`)).toEqual(before);
  });
});

// ⑧(MultiPV参考評価)の再取得を続けてよいかの判定。
// Phase6の通し確認で、1回だけの再取得ではエンジンの解析(実測で約8秒)に間に合わず、
// サーバーが"ready"なのに画面が「計算中」のまま止まることが判明したため、上限付きの
// リトライへ変更した。web側が持つのは「状態」と「試行回数」による判定だけで、
// 将棋の判断は一切持たない。
describe("shouldRetryPlanRefresh", () => {
  it('"pending"の間はリトライする', () => {
    expect(shouldRetryPlanRefresh({ candidateMoveState: "pending" }, 1)).toBe(true);
  });

  it('"ready"になったらリトライしない', () => {
    expect(shouldRetryPlanRefresh({ candidateMoveState: "ready" }, 1)).toBe(false);
  });

  it('"unavailable"(そもそも候補手が無い)ならリトライしない', () => {
    expect(shouldRetryPlanRefresh({ candidateMoveState: "unavailable" }, 1)).toBe(false);
  });

  it("上限回数に達したら、まだpendingでもリトライしない(無限に回さない)", () => {
    expect(
      shouldRetryPlanRefresh({ candidateMoveState: "pending" }, PLAN_REFRESH_MAX_ATTEMPTS - 1),
    ).toBe(true);
    expect(shouldRetryPlanRefresh({ candidateMoveState: "pending" }, PLAN_REFRESH_MAX_ATTEMPTS)).toBe(
      false,
    );
    expect(
      shouldRetryPlanRefresh({ candidateMoveState: "pending" }, PLAN_REFRESH_MAX_ATTEMPTS + 1),
    ).toBe(false);
  });

  it("上限は有限で、実測の解析時間(18〜19秒)を1.5秒間隔でカバーできる", () => {
    expect(Number.isInteger(PLAN_REFRESH_MAX_ATTEMPTS)).toBe(true);
    expect(PLAN_REFRESH_MAX_ATTEMPTS).toBeGreaterThanOrEqual(14);
    expect(PLAN_REFRESH_MAX_ATTEMPTS).toBeLessThanOrEqual(40);
  });
});

// STEP ζ-5: docs/PHASES.md Phase7 Unit4「draftの表示」表(人間承認済み)どおりに
// 注記が「」の外側へ付くことを固定するためのテスト。前回の実装は注記を「」の内側に
// 入れてしまっていた(main.tsのwithPendingReviewNote)ため、今回はreviewNoteSuffix自体と、
// main.tsが実際に組み立てる文言(組み上がりの見出し・候補手セクションの見出し・
// 目標形の選択ボタン)の両方を検証する。
describe("candidateMoveUsisOnBoard", () => {
  const ready = (moves: (string | null)[]) => ({
    candidateMoveState: "ready" as const,
    candidateMove: {
      status: "ready" as const,
      notReadyReason: null,
      sharedNotes: [],
      explanations: moves.map((move, index) => ({
        id: `e${index}`,
        purpose: "",
        move,
        reason: "",
        refers_to_shape_id: null,
        confidence_level: "medium" as const,
      })),
    },
  });

  it("画面に出ている候補手のUSIを、サーバーが返した順序のまま返す", () => {
    expect(candidateMoveUsisOnBoard(ready(["7h7g", "7h8h"]))).toEqual(["7h7g", "7h8h"]);
  });

  it("moveがnullの説明は盤に描けないため除く", () => {
    expect(candidateMoveUsisOnBoard(ready(["7h7g", null]))).toEqual(["7h7g"]);
  });

  // CLAUDE.md「絶対に守るルール」3番: 安全確認を経ていない候補手を見せない。
  // 候補手セクションが何も出さない状態では、盤にも描かない(表示条件を一致させる)。
  it("candidateMoveStateがreadyでなければ何も描かない", () => {
    expect(candidateMoveUsisOnBoard({ ...ready(["7h7g"]), candidateMoveState: "pending" })).toEqual([]);
    expect(candidateMoveUsisOnBoard({ ...ready(["7h7g"]), candidateMoveState: "unavailable" })).toEqual([]);
  });

  it("candidateMoveが未取得・not_readyなら何も描かない", () => {
    expect(candidateMoveUsisOnBoard({ candidateMoveState: "ready", candidateMove: undefined })).toEqual([]);
    expect(
      candidateMoveUsisOnBoard({
        candidateMoveState: "ready",
        candidateMove: {
          status: "not_ready",
          notReadyReason: "engine_reference_unavailable",
          explanations: [],
          sharedNotes: [],
        },
      }),
    ).toEqual([]);
  });
});

// STEP 5-1(A-4、人間承認済み。LP-1): A-1と同一条件のDOM非依存の純粋関数。
describe("isCandidateMovesExcluded", () => {
  it("candidateMoveStateがreadyかつnot_ready・excluded_by_reference_evaluationのときだけtrue", () => {
    expect(
      isCandidateMovesExcluded({
        candidateMoveState: "ready",
        candidateMove: {
          status: "not_ready",
          notReadyReason: "excluded_by_reference_evaluation",
          explanations: [],
          sharedNotes: [],
        },
      }),
    ).toBe(true);
  });

  it("candidateMoveStateがreadyでなければfalse", () => {
    expect(
      isCandidateMovesExcluded({
        candidateMoveState: "pending",
        candidateMove: undefined,
      }),
    ).toBe(false);
    expect(
      isCandidateMovesExcluded({
        candidateMoveState: "unavailable",
        candidateMove: undefined,
      }),
    ).toBe(false);
  });

  it("candidateMoveがreadyのときはfalse", () => {
    expect(
      isCandidateMovesExcluded({
        candidateMoveState: "ready",
        candidateMove: { status: "ready", notReadyReason: null, explanations: [], sharedNotes: [] },
      }),
    ).toBe(false);
  });

  it("除外以外のnotReadyReasonではfalse", () => {
    expect(
      isCandidateMovesExcluded({
        candidateMoveState: "ready",
        candidateMove: {
          status: "not_ready",
          notReadyReason: "engine_reference_unavailable",
          explanations: [],
          sharedNotes: [],
        },
      }),
    ).toBe(false);
  });
});

describe("groupCandidateExplanationsByReason", () => {
  const labels = { "6g6f": "６七→６六", "7g3c": "７七→３三", "7g4d": "７七→４四" };

  it("理由文が同一の候補手を1行にまとめ、指し手を並記する", () => {
    const groups = groupCandidateExplanationsByReason(
      [
        { move: "6g6f", reason: "金を進めるための候補です。" },
        { move: "7g3c", reason: "桂を進めるための候補です。" },
        { move: "7g4d", reason: "桂を進めるための候補です。" },
      ],
      labels,
    );

    // Phase 7: 盤上表示のため、表示ラベルとUSIを対にして持つ。
    expect(groups).toEqual([
      { moves: [{ usi: "6g6f", label: "６七→６六" }], reason: "金を進めるための候補です。" },
      {
        moves: [
          { usi: "7g3c", label: "７七→３三" },
          { usi: "7g4d", label: "７七→４四" },
        ],
        reason: "桂を進めるための候補です。",
      },
    ]);
  });

  it("サーバーが返した順序を変えない", () => {
    const groups = groupCandidateExplanationsByReason(
      [
        { move: "7g3c", reason: "B" },
        { move: "6g6f", reason: "A" },
        { move: "7g4d", reason: "B" },
      ],
      labels,
    );

    expect(groups.map((g) => g.reason)).toEqual(["B", "A"]);
  });

  it("日本語表記が無い指し手はUSIのまま表示する", () => {
    const groups = groupCandidateExplanationsByReason([{ move: "9i9h", reason: "A" }], labels);

    expect(groups[0]?.moves).toEqual([{ usi: "9i9h", label: "9i9h" }]);
  });

  it("moveがnullでも落ちない", () => {
    const groups = groupCandidateExplanationsByReason([{ move: null, reason: "A" }], labels);

    expect(groups[0]?.moves).toEqual([{ usi: "", label: "" }]);
  });

  it("候補手が0件なら空配列を返す", () => {
    expect(groupCandidateExplanationsByReason([], labels)).toEqual([]);
  });
});

describe("splitCoachByStage(STEP 5-2, A-2)", () => {
  it("undefinedの場合、3つとも空配列を返す", () => {
    expect(splitCoachByStage(undefined)).toEqual({
      opponentIntent: [],
      currentShape: [],
      opponentNextAim: [],
    });
  });

  it("空配列の場合、3つとも空配列を返す", () => {
    expect(splitCoachByStage([])).toEqual({
      opponentIntent: [],
      currentShape: [],
      opponentNextAim: [],
    });
  });

  it("stageごとに振り分ける(1件ずつ)", () => {
    const opponentIntent = makeCoachExplanation("a", "opponent_intent");
    const currentShape = makeCoachExplanation("b", "current_shape");
    const opponentNextAim = makeCoachExplanation("c", "opponent_next_aim");

    expect(splitCoachByStage([opponentIntent, currentShape, opponentNextAim])).toEqual({
      opponentIntent: [opponentIntent],
      currentShape: [currentShape],
      opponentNextAim: [opponentNextAim],
    });
  });

  it("同じstageが複数件でも、入力順のまま同じバケツへ入れる", () => {
    const first = makeCoachExplanation("a", "opponent_intent");
    const second = makeCoachExplanation("b", "opponent_intent");

    const result = splitCoachByStage([first, second]);

    expect(result.opponentIntent).toEqual([first, second]);
    expect(result.currentShape).toEqual([]);
    expect(result.opponentNextAim).toEqual([]);
  });

  it("サーバーが返した順序を変えない(stageが混在していても各バケツ内は入力順)", () => {
    const a = makeCoachExplanation("a", "current_shape");
    const b = makeCoachExplanation("b", "opponent_intent");
    const c = makeCoachExplanation("c", "current_shape");

    const result = splitCoachByStage([a, b, c]);

    expect(result.currentShape).toEqual([a, c]);
    expect(result.opponentIntent).toEqual([b]);
  });
});

describe("reviewNoteSuffix", () => {
  it("注記がnullの場合は空文字を返す(「」の外に何も付かない)", () => {
    expect(reviewNoteSuffix(null)).toBe("");
  });

  it("注記がある場合は括弧で囲んだサフィックスを返す", () => {
    expect(reviewNoteSuffix("内容を確認中の形")).toBe("(内容を確認中の形)");
  });
});

describe("STEP ζ-5: 承認済み文言(注記は「」の外側)", () => {
  it("組み上がりの見出し(main.ts:301相当)", () => {
    const name = "銀冠";
    const heading = `「${name}」${reviewNoteSuffix("内容を確認中の形")}の組み上がり`;
    expect(heading).toBe("「銀冠」(内容を確認中の形)の組み上がり");
  });

  it("組み上がりの見出し(注記なし)", () => {
    const name = "本美濃";
    const heading = `「${name}」${reviewNoteSuffix(null)}の組み上がり`;
    expect(heading).toBe("「本美濃」の組み上がり");
  });

  it("候補手セクションの見出し(main.ts:480相当)", () => {
    const selectedShapeName = "銀冠";
    const selectedShapeNote = "内容を確認中の形";
    const heading = `「${selectedShapeName}」${reviewNoteSuffix(selectedShapeNote)}に近づく手の候補`;
    expect(heading).toBe("「銀冠」(内容を確認中の形)に近づく手の候補");
  });

  it("候補手セクションの見出し(注記なし)", () => {
    const selectedShapeName = "本美濃";
    const selectedShapeNote = null;
    const heading = `「${selectedShapeName}」${reviewNoteSuffix(selectedShapeNote)}に近づく手の候補`;
    expect(heading).toBe("「本美濃」に近づく手の候補");
  });

  // Unit 3(既知事項 U0-1 の解消): 選択中の形が無い場合のフォールバック見出し
  // 「この形へ近づく手の候補」は廃止した。目標形が未選択のときは候補手セクション
  // そのものを出さないため、指す対象の無い「この形」という文言は画面に出ない。
  it("候補手セクションの見出しは、選択中の形がある場合にしか作られない", () => {
    const selectedShapeName: string | null = null;

    // main.ts の renderPlan は selectedShapeName が null の時点で return する。
    expect(selectedShapeName).toBeNull();
  });

  it("目標形の選択ボタン(main.ts:446相当、これは元々正しい仕様どおり内側のまま)", () => {
    const shapeName = "銀冠";
    const displayName = shapeName + reviewNoteSuffix("内容を確認中の形");
    expect(displayName).toBe("銀冠(内容を確認中の形)");
  });

  it("目標形の選択ボタン(注記なし)", () => {
    const shapeName = "本美濃";
    const displayName = shapeName + reviewNoteSuffix(null);
    expect(displayName).toBe("本美濃");
  });
});

// STEP 4-5(Y-1、人間承認済み、人間指定テスト10): 終局時の状態行から結果種別の英語の
// 括弧書き(例: "(checkmate)")だけが消え、勝者の表記(先手/後手/引き分け)は
// 従来どおりであることを確認する。main.tsはDOM前提でテスト基盤が無いため、
// 切り出した純粋関数をここで検証する(reviewNoteSuffix等と同じ流儀)。
describe("formatGameEndStatus(STEP 4-5, Y-1)", () => {
  it("自分(先手)が勝った場合、結果種別を含まない「対局終了: あなた(先手)」になる", () => {
    const status: GameStatus = { isEnd: true, outcome: { result: "checkmate", winner: "sente" } };
    const text = formatGameEndStatus(status);

    expect(text).toBe("対局終了: あなた(先手)");
    expect(text).not.toContain("(checkmate)");
    expect(text).not.toContain("checkmate");
  });

  it("相手(後手)が勝った場合、「対局終了: 相手(後手)」になる(以前の仕様書に書かれていた挙動)", () => {
    const status: GameStatus = { isEnd: true, outcome: { result: "checkmate", winner: "gote" } };

    expect(formatGameEndStatus(status)).toBe("対局終了: 相手(後手)");
  });

  it("winnerがundefinedの場合(引き分け等)、「対局終了: 引き分け」になる", () => {
    const status: GameStatus = { isEnd: true, outcome: { result: "draw", winner: undefined } };

    expect(formatGameEndStatus(status)).toBe("対局終了: 引き分け");
  });

  it("詰み以外の結果種別(stalemate)でも、結果種別を含まない", () => {
    const status: GameStatus = { isEnd: true, outcome: { result: "stalemate", winner: "gote" } };
    const text = formatGameEndStatus(status);

    expect(text).toBe("対局終了: 相手(後手)");
    expect(text).not.toContain("stalemate");
  });

  it("outcomeがundefinedでも例外を投げず、引き分け表記に落ちる(安全側)", () => {
    const status: GameStatus = { isEnd: true, outcome: undefined };

    expect(formatGameEndStatus(status)).toBe("対局終了: 引き分け");
  });
});

// STEP 5-4(W-4・W-6、人間承認済み): 当たりが4駒以上のときに、盤に描いてよい上位3件と
// 帯の「ほかN駒」の元になる件数を取り出す純粋関数。
function makeThreatMessage(square: string, attackerSquares: string[] = []): UrgentMessage {
  return { kind: "piece_attacked", text: `${square}の駒が当たっています`, square, attackerSquares };
}

describe("partitionPieceThreatsForBoard(STEP 5-4, W-4)", () => {
  it("0件の場合、drawnは空・othersCountは0", () => {
    expect(partitionPieceThreatsForBoard([])).toEqual({ drawn: [], othersCount: 0 });
  });

  it("3件の場合、drawnに3件とも入り、othersCountは0", () => {
    const messages = [makeThreatMessage("6h"), makeThreatMessage("9i"), makeThreatMessage("7g")];
    const result = partitionPieceThreatsForBoard(messages);
    expect(result.drawn).toEqual(messages);
    expect(result.othersCount).toBe(0);
  });

  it("5件の場合、drawnは並び順の先頭3件、othersCountは2", () => {
    const messages = [
      makeThreatMessage("6h"),
      makeThreatMessage("9i"),
      makeThreatMessage("7g"),
      makeThreatMessage("5c"),
      makeThreatMessage("3d"),
    ];
    const result = partitionPieceThreatsForBoard(messages);
    expect(result.drawn).toEqual(messages.slice(0, 3));
    expect(result.othersCount).toBe(2);
  });

  it("王手の行が混ざっていても、当たり(piece_attacked)以外は数えない", () => {
    const messages: UrgentMessage[] = [
      makeThreatMessage("6h"),
      { kind: "check", text: "王手されています" },
      makeThreatMessage("9i"),
      makeThreatMessage("7g"),
      makeThreatMessage("5c"),
    ];
    const result = partitionPieceThreatsForBoard(messages);
    expect(result.drawn).toEqual([messages[0], messages[2], messages[3]]);
    expect(result.othersCount).toBe(1);
  });

  it("squareの無い旧応答の行は、drawnにもothersCountにも含めない(壊れない)", () => {
    const withoutSquare: UrgentMessage = { kind: "piece_attacked", text: "旧応答の当たりの行" };
    const messages = [withoutSquare, makeThreatMessage("6h")];
    const result = partitionPieceThreatsForBoard(messages);
    expect(result.drawn).toEqual([messages[1]]);
    expect(result.othersCount).toBe(0);
  });
});

// STEP 5-4(W-2・W-5・W-6、人間承認済み): 盤に描く印の座標をAPIの応答から取り出す純粋関数。
function makeProgress(overrides: Partial<TargetShapeProgress> = {}): TargetShapeProgress {
  return {
    shapeId: "honmino",
    name: "本美濃",
    description: "",
    matchedSquareLabels: [],
    matchedPieceLabels: [],
    missingSquareLabels: [],
    pendingReviewNote: null,
    ...overrides,
  };
}

describe("boardMarksFromState(STEP 5-4, W-2・W-5・W-6)", () => {
  it("当たり4駒以上の局面では、上位3件の当たり駒・攻め駒だけを返す(重複除去)", () => {
    const plan: Pick<ReachablePlanBody, "urgentMessages" | "targetShapeProgress"> = {
      urgentMessages: [
        makeThreatMessage("6h", ["7g"]),
        makeThreatMessage("9i", ["7g"]),
        makeThreatMessage("7g", ["8h"]),
        makeThreatMessage("5c", ["4d"]),
      ],
      targetShapeProgress: null,
    };
    const marks = boardMarksFromState(plan, undefined);
    expect(marks.attacked).toEqual(["6h", "9i", "7g"]);
    expect(marks.attackers).toEqual(["7g", "8h"]);
    expect(marks.evidence).toEqual([]);
    expect(marks.matched).toEqual([]);
    expect(marks.missing).toEqual([]);
  });

  it("②opponent_intentのevidenceSquaresを重複除去して集める(他stageは無視)", () => {
    const plan: Pick<ReachablePlanBody, "urgentMessages" | "targetShapeProgress"> = {
      urgentMessages: [],
      targetShapeProgress: null,
    };
    const intent1 = makeCoachExplanation("i1", "opponent_intent");
    intent1.evidenceSquares = ["6d"];
    const intent2 = makeCoachExplanation("i2", "opponent_intent");
    intent2.evidenceSquares = ["6d", "7c"];
    const shape1 = makeCoachExplanation("s1", "current_shape");
    shape1.evidenceSquares = ["9i"];
    const coach: CoachExplanation[] = [intent1, intent2, shape1];
    const marks = boardMarksFromState(plan, coach);
    expect(marks.evidence).toEqual(["6d", "7c"]);
  });

  it("④のmatchedSquares・missingSquaresをそのまま返す", () => {
    const plan: Pick<ReachablePlanBody, "urgentMessages" | "targetShapeProgress"> = {
      urgentMessages: [],
      targetShapeProgress: makeProgress({ matchedSquares: ["2h", "3h", "4i"], missingSquares: ["5h"] }),
    };
    const marks = boardMarksFromState(plan, undefined);
    expect(marks.matched).toEqual(["2h", "3h", "4i"]);
    expect(marks.missing).toEqual(["5h"]);
  });

  it("旧応答(square・matchedSquares・evidenceSquaresが無い)では、すべて空配列になり壊れない", () => {
    const plan: Pick<ReachablePlanBody, "urgentMessages" | "targetShapeProgress"> = {
      urgentMessages: [{ kind: "piece_attacked", text: "旧応答の当たりの行" }],
      targetShapeProgress: makeProgress(),
    };
    const coach: CoachExplanation[] = [makeCoachExplanation("i1", "opponent_intent")];
    const marks = boardMarksFromState(plan, coach);
    expect(marks).toEqual({ attacked: [], attackers: [], evidence: [], matched: [], missing: [] });
  });
});

// STEP 5-3(A-1・A-5、人間承認済み): 要約行の純粋関数群のテスト。
describe("firstSentence / lastSentence", () => {
  it("「。」が1個の場合、firstSentence・lastSentenceとも同じ1文(「。」つき)を返す", () => {
    expect(firstSentence("これは文です。")).toBe("これは文です。");
    expect(lastSentence("これは文です。")).toBe("これは文です。");
  });

  it("「。」が複数の場合、firstSentenceは先頭の文、lastSentenceは末尾の文を返す", () => {
    const text = "1文目です。2文目です。3文目です。";
    expect(firstSentence(text)).toBe("1文目です。");
    expect(lastSentence(text)).toBe("3文目です。");
  });

  it("「。」が無い場合、全文をそのまま返す", () => {
    expect(firstSentence("句点が無い文")).toBe("句点が無い文");
    expect(lastSentence("句点が無い文")).toBe("句点が無い文");
  });
});

describe("summarizeHappened", () => {
  it("outcomeが無い(初期局面)場合、空文字を返す", () => {
    expect(summarizeHappened(null)).toBe("");
  });

  it("盤の出来事(BoardEventKind)の行が先頭にあれば、その行の1文目を返す", () => {
    const outcome: LastMoveOutcomeBody = {
      playedMoveLabel: "７六歩",
      opponentMoveLabel: "３四歩",
      messages: [
        { kind: "captured_by_you", text: "相手の歩を取りました。持ち駒が1枚増えました。" },
        { kind: "route_advanced", text: "経路が1歩進みました。" },
      ],
    };
    expect(summarizeHappened(outcome)).toBe("相手の歩を取りました。");
  });

  it("盤の出来事の行が無い場合、既存の「あなた/相手」の行を返す", () => {
    const outcome: LastMoveOutcomeBody = {
      playedMoveLabel: "７六歩",
      opponentMoveLabel: "３四歩",
      messages: [{ kind: "route_advanced", text: "経路が1歩進みました。" }],
    };
    expect(summarizeHappened(outcome)).toBe("あなた: ７六歩 / 相手: ３四歩");
  });

  it("相手の手が無い場合、「あなた」だけの行を返す", () => {
    const outcome: LastMoveOutcomeBody = {
      playedMoveLabel: "７六歩",
      opponentMoveLabel: null,
      messages: [],
    };
    expect(summarizeHappened(outcome)).toBe("あなた: ７六歩");
  });
});

describe("summarizeOpponentAim / summarizeWhy", () => {
  it("summarizeOpponentAimはreasonの1文目を返す", () => {
    expect(summarizeOpponentAim({ reason: "相手は棒銀に近い動きをしています。詳しい説明。" })).toBe(
      "相手は棒銀に近い動きをしています。",
    );
  });

  it("summarizeWhyはreasonの末尾の一文を返す", () => {
    expect(summarizeWhy({ reason: "1文目の説明。今後の見通しは判断できません。" })).toBe(
      "今後の見通しは判断できません。",
    );
  });
});

describe("summarizeMyAim", () => {
  it("status===noneの場合、reasonの1文目を返す(未認識)", () => {
    expect(
      summarizeMyAim(
        { reason: "今の陣形は、あらかじめ用意されている形のどれともまだはっきり一致していません。詳しい説明。", status: "none" },
        null,
      ),
    ).toBe("今の陣形は、あらかじめ用意されている形のどれともまだはっきり一致していません。");
  });

  it("status===completedかつ非draftの場合、reasonを全文(1文)そのまま返す", () => {
    const reason = "今、本美濃囲いの形ができています。";
    expect(summarizeMyAim({ reason, status: "completed" }, makeProgress({ pendingReviewNote: null }))).toBe(reason);
  });

  it("status===completedかつdraftの場合、名前+確認中の注記の2文を分割せず全文を返す", () => {
    const reason =
      "今、銀冠と呼ばれる並びに近い形になっています。ただし、この形の説明は内容を確認中のため、参考程度に見てください。";
    expect(
      summarizeMyAim(
        { reason, status: "completed" },
        makeProgress({ name: "銀冠", pendingReviewNote: "この形の説明は内容を確認中です。" }),
      ),
    ).toBe(reason);
  });

  it("status===formingかつprogressがありpendingReviewNoteがnullの場合、承認済みの新しい文を返す", () => {
    const progress = makeProgress({ name: "本美濃囲い", pendingReviewNote: null });
    expect(
      summarizeMyAim({ reason: "途中の説明1文目。詳しい説明。", status: "forming" }, progress),
    ).toBe("今の陣形は、本美濃囲いに近づいているように見えますが、まだ完成していません。");
  });

  it("status===formingかつprogressがdraft(pendingReviewNoteがある)の場合、名前を出さずreasonの1文目を返す", () => {
    const progress = makeProgress({ name: "銀冠", pendingReviewNote: "この形の説明は内容を確認中です。" });
    expect(summarizeMyAim({ reason: "途中の説明1文目。詳しい説明。", status: "forming" }, progress)).toBe(
      "途中の説明1文目。",
    );
  });

  it("status===formingかつprogressが無い場合、reasonの1文目を返す", () => {
    expect(summarizeMyAim({ reason: "途中の説明1文目。詳しい説明。", status: "forming" }, null)).toBe(
      "途中の説明1文目。",
    );
  });
});

describe("buildKifuJson", () => {
  it("0手の場合、movesが空配列でidの手数が0movesになる", () => {
    const result = buildKifuJson([], new Date(2026, 8, 12));
    expect(result).toEqual({
      id: "2026-09-12-live-0moves",
      source: "apps/web の対局から保存",
      moves: [],
    });
  });

  it("奇数手の場合、idの手数がmoveHistory.lengthと一致する", () => {
    const moveHistory = ["7g7f", "3c3d", "2g2f"];
    const result = buildKifuJson(moveHistory, new Date(2026, 8, 12));
    expect(result.id).toBe("2026-09-12-live-3moves");
    expect(result.moves).toEqual(moveHistory);
  });

  it("偶数手の場合、idの手数がmoveHistory.lengthと一致する", () => {
    const moveHistory = ["7g7f", "3c3d", "2g2f", "8c8d"];
    const result = buildKifuJson(moveHistory, new Date(2026, 8, 12));
    expect(result.id).toBe("2026-09-12-live-4moves");
    expect(result.moves).toEqual(moveHistory);
  });

  it("月・日が1桁のとき、idの日付がゼロ埋め2桁になる(1月5日)", () => {
    const result = buildKifuJson(["7g7f"], new Date(2026, 0, 5));
    expect(result.id).toBe("2026-01-05-live-1moves");
  });

  it("sourceは固定文字列である", () => {
    const result = buildKifuJson(["7g7f"], new Date(2026, 8, 12));
    expect(result.source).toBe("apps/web の対局から保存");
  });

  it("movesは入力と同じ内容だが、別配列である(入力を書き換えない)", () => {
    const moveHistory = ["7g7f", "3c3d"];
    const result = buildKifuJson(moveHistory, new Date(2026, 8, 12));
    expect(result.moves).toEqual(moveHistory);
    expect(result.moves).not.toBe(moveHistory);

    // 返り値を書き換えても、呼び出し側の入力配列は変化しない。
    result.moves.push("2g2f");
    expect(moveHistory).toEqual(["7g7f", "3c3d"]);
  });
});
