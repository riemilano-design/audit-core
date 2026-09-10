import { describe, expect, it } from "vitest";
import { detectIntents, type IntentDetectionResult } from "./intentDetector.js";
import { getShapes } from "./shapeRepository.js";
import { analyzeShapeFormation, type ShapeFormationResult } from "./shapeFormationAnalyzer.js";
import { getIntents, type IntentDefinition } from "./intentRepository.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "./moveHistory.js";
import {
  explainPosition,
  generateCoachExplanations,
  generateExplanations,
  type Explanation,
} from "./explanationGenerator.js";

const SENTE_FILLERS = ["1g1f", "2g2f", "3g3f", "4g4f", "5g5f", "6g6f", "9g9f", "8g8f"];

function interleaveWithSenteFillers(goteMoves: string[]): string[] {
  const moves: string[] = [];
  goteMoves.forEach((goteMove, i) => {
    const filler = SENTE_FILLERS[i];
    if (!filler) throw new Error("SENTE_FILLERSが不足しています");
    moves.push(filler, goteMove);
  });
  return moves;
}

function sfenAfter(moveHistory: string[]): string {
  return replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN).finalSfen;
}

function findStage(explanations: Explanation[], stage: Explanation["stage"]): Explanation {
  const found = explanations.find((e) => e.stage === stage);
  if (!found) throw new Error(`stage not found: ${stage}`);
  return found;
}

// data/intents/hayajikake.json: 歩 6d(1) -> 6e(2)
const HAYAJIKAKE_GOTE_MOVES_FULL = ["6c6d", "6d6e"];

// 本美濃(mino_honmino)の必須駒配置(8h玉・7h銀・6i金・5h金)そのもの。
// completedはUnit5の設計上、shape_formation_evidenceの有無を問わない
// (物理的に形が完成していれば経緯を問わず完成として良いため)。
const TEST_HONMINO: ShapeFormationResult = {
  shapeId: "mino_honmino",
  name: "本美濃囲い",
  side: "self",
  family: "美濃系",
  parentShapeId: null,
  perspectiveColor: "sente",
  status: "completed",
  matchScore: 1,
  matchedSquares: ["8h", "7h", "6i", "5h"],
  missingSquares: [],
  optionalMatchedSquares: [],
  formationEvidence: [],
  dataConfidenceLevel: "medium",
  reviewStatus: "human_reviewed",
  characteristics: "四間飛車でよく使われる、完成が早くバランスの良い囲い。",
  weakAgainst: undefined,
};

const NO_SHAPE_RESULTS: ShapeFormationResult[] = getShapes().map((shape) => ({
  shapeId: shape.id,
  name: shape.name,
  side: shape.side,
  family: shape.family,
  parentShapeId: shape.parent_shape_id ?? null,
  perspectiveColor: "sente",
  status: "none",
  matchScore: 0,
  matchedSquares: [],
  missingSquares: shape.required_pieces.filter((p) => !p.optional).map((p) => p.square),
  optionalMatchedSquares: [],
  formationEvidence: [],
  dataConfidenceLevel: shape.confidence_level,
  reviewStatus: shape.review_status,
  characteristics: shape.characteristics,
  weakAgainst: undefined,
}));

const NO_INTENT_RESULTS = getIntents().map((intent) => ({
  intentId: intent.id,
  name: intent.name,
  openingId: intent.opening_id,
  dataConfidenceLevel: intent.confidence_level,
  reviewStatus: intent.review_status,
  matchStatus: "none" as const,
  matchScore: 0,
  matchedSignatures: [],
  unmatchedSignatures: intent.recognition_pattern,
  currentAimExplanation: intent.current_aim_explanation,
  nextAimExplanation: intent.next_aim_explanation,
  affectsTargetShapes: intent.affects_target_shapes,
}));

describe("generateExplanations", () => {
  it("常に3件(current_shape/opponent_intent/opponent_next_aim)を、その順序で返す", () => {
    const explanations = generateExplanations(NO_SHAPE_RESULTS, NO_INTENT_RESULTS);
    expect(explanations.map((e) => e.stage)).toEqual(["current_shape", "opponent_intent", "opponent_next_aim"]);
  });

  it("current_shape: Shapeがcompletedの場合、名称を含む説明を返す", () => {
    const explanations = generateExplanations([TEST_HONMINO], NO_INTENT_RESULTS);
    const currentShape = findStage(explanations, "current_shape");

    expect(currentShape.refers_to_shape_id).toBe("mino_honmino");
    expect(currentShape.reason).toContain("本美濃囲い");
    // STEP 4-6(H-1、人間承認済み): completedのreasonはlead(1文)のみとし、
    // characteristicsは連結しない(同じ文が[5]「参考になる囲い」にあるため)。
    expect(currentShape.reason).not.toContain(TEST_HONMINO.characteristics);
    expect(currentShape.confidence_level).not.toBe("low");
    expect(currentShape.purpose).toBeTruthy();
    expect(currentShape.move).toBeNull();
  });

  it("current_shape: Shapeがforming(未完成だが、実際に駒が動いた証拠がある)の場合、断定しない言い回しになる", () => {
    const forming: ShapeFormationResult = {
      ...TEST_HONMINO,
      status: "forming",
      matchScore: 0.5,
      missingSquares: ["5h"],
      // shape_formation_evidence: 玉が実際に8hへ動いたという指し手履歴上の根拠がある状態を模す。
      formationEvidence: [{ square: "8h", piece: "玉", evidence: { ply: 2, moveUsi: "5i6h" } }],
    };
    const explanations = generateExplanations([forming], NO_INTENT_RESULTS);
    const currentShape = findStage(explanations, "current_shape");

    // 論点1(甲、STEP ζ-5): formingの段階では戦法・陣形の名前を一切出さない。
    expect(currentShape.reason).toContain("まだ完成していません");
    expect(currentShape.reason).not.toContain("完成しています");
    for (const shape of getShapes()) {
      expect(currentShape.reason).not.toContain(shape.name);
    }
  });

  it("current_shape: forming時、characteristicsが他の形の名前を含む形(高美濃囲い/銀冠)でも名前が漏れない(指摘A回帰テスト)", () => {
    // mino_takamino.characteristicsは「本美濃囲いで5八にあった金を…」と本美濃囲いの
    // 名前を含み、mino_ginkanmuri.characteristicsは「高美濃囲いからさらに銀を…」と
    // 高美濃囲いの名前を含む。TEST_HONMINOのcharacteristics(他形名を含まない)だけでは
    // この漏れを検出できない(成果物監査REVISE指摘A)ため、実データからこの2件を使う。
    const takamino = getShapes().find((s) => s.id === "mino_takamino")!;
    const ginkanmuri = getShapes().find((s) => s.id === "mino_ginkanmuri")!;

    for (const shapeDef of [takamino, ginkanmuri]) {
      const forming: ShapeFormationResult = {
        shapeId: shapeDef.id,
        name: shapeDef.name,
        side: shapeDef.side,
        family: shapeDef.family,
        parentShapeId: shapeDef.parent_shape_id ?? null,
        perspectiveColor: "sente",
        status: "forming",
        matchScore: 0.5,
        matchedSquares: [],
        missingSquares: ["7g"],
        optionalMatchedSquares: [],
        formationEvidence: [{ square: "8h", piece: "玉", evidence: { ply: 2, moveUsi: "5i6h" } }],
        dataConfidenceLevel: shapeDef.confidence_level,
        reviewStatus: shapeDef.review_status,
        characteristics: shapeDef.characteristics,
        weakAgainst: undefined,
      };

      const explanations = generateExplanations([forming], NO_INTENT_RESULTS);
      const currentShape = findStage(explanations, "current_shape");

      expect(currentShape.reason).toBe(
        "今の陣形は、あらかじめ用意されている形のどれかに近づいてきているように見えますが、まだ完成していません。",
      );
      for (const shape of getShapes()) {
        expect(currentShape.reason).not.toContain(shape.name);
      }
    }
  });

  it("current_shape: 全shapeがnone(matchScore 0)の場合、特定の形を断定せず『未分類』の説明になる", () => {
    const explanations = generateExplanations(NO_SHAPE_RESULTS, NO_INTENT_RESULTS);
    const currentShape = findStage(explanations, "current_shape");

    expect(currentShape.refers_to_shape_id).toBeNull();
    expect(currentShape.confidence_level).toBe("low");
    // data/shapes/に存在する形の名称を、根拠なく断定的に名指ししていないこと
    for (const shape of getShapes()) {
      expect(currentShape.reason).not.toContain(shape.name);
    }
  });

  it("opponent_intent / opponent_next_aim: Unit1/Unit2と統合し、早仕掛けmatched局面で一貫した説明になる", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    const sfen = sfenAfter(moveHistory);
    const shapeResults = analyzeShapeFormation(sfen, moveHistory);
    const intentResults = detectIntents(sfen, moveHistory);
    const explanations = generateExplanations(shapeResults, intentResults);

    const opponentIntent = findStage(explanations, "opponent_intent");
    expect(opponentIntent.refers_to_intent_id).toBe("hayajikake");
    expect(opponentIntent.reason).toContain("早仕掛け");
    // intents.current_aim_explanation(既存の人間レビュー済みテキスト)がそのまま含まれること
    const hayajikake = getIntents().find((i) => i.id === "hayajikake")!;
    expect(opponentIntent.reason).toContain(hayajikake.current_aim_explanation);
    expect(opponentIntent.confidence_level).not.toBe("low");

    const nextAim = findStage(explanations, "opponent_next_aim");
    expect(nextAim.refers_to_intent_id).toBe("hayajikake");
    expect(nextAim.reason).toContain(hayajikake.next_aim_explanation);
  });

  it("opponent_intent: Intentがforming(途中段階)の場合、断定しない言い回しになる", () => {
    const moveHistory = interleaveWithSenteFillers([HAYAJIKAKE_GOTE_MOVES_FULL[0]!]);
    const sfen = sfenAfter(moveHistory);
    const shapeResults = analyzeShapeFormation(sfen, moveHistory);
    const intentResults = detectIntents(sfen, moveHistory);
    const explanations = generateExplanations(shapeResults, intentResults);

    const opponentIntent = findStage(explanations, "opponent_intent");
    // 論点1(甲、STEP ζ-5): formingの段階では戦法名・current_aim_explanationを一切出さず、
    // 観測できている事実(手数・駒・マス・大まかな方向)だけを機械的に述べる。
    expect(opponentIntent.reason).toContain("ように見えます");
    expect(opponentIntent.reason).toContain("まだ決まっていません");
    const hayajikake = getIntents().find((i) => i.id === "hayajikake")!;
    for (const intent of getIntents()) {
      expect(opponentIntent.reason).not.toContain(intent.name);
    }
    expect(opponentIntent.reason).not.toContain(hayajikake.current_aim_explanation);

    // opponent_next_aim(STEP 4-4、人間承認R-1、2026-09-10): formingの段階でも
    // ステージは落とさず、noneと同じ既存の汎用文(戦法名を含まない)を出す。
    // ζ-5が禁止したのは戦法名を含むnext_aim_explanationの表示であり、この汎用文は
    // 禁止範囲に含まれない。
    const nextAim = findStage(explanations, "opponent_next_aim");
    expect(nextAim.reason).toBe("相手の狙いがまだ定まっていないため、次に何をしてきそうかも現時点では判断できません。");
    expect(nextAim.refers_to_intent_id).toBeNull();
    expect(nextAim.glossary_terms).toEqual([]);
    for (const intent of getIntents()) {
      expect(nextAim.reason).not.toContain(intent.name);
    }
  });

  it("opponent_intent / opponent_next_aim: 全intentがnoneの場合、特定の意図を断定しない", () => {
    const explanations = generateExplanations(NO_SHAPE_RESULTS, NO_INTENT_RESULTS);
    const opponentIntent = findStage(explanations, "opponent_intent");
    const nextAim = findStage(explanations, "opponent_next_aim");

    expect(opponentIntent.refers_to_intent_id).toBeNull();
    expect(opponentIntent.confidence_level).toBe("low");
    expect(nextAim.refers_to_intent_id).toBeNull();
    expect(nextAim.confidence_level).toBe("low");
    for (const intent of getIntents()) {
      expect(opponentIntent.reason).not.toContain(intent.name);
    }
  });

  // Phase4: scenarioOpponentOpening(開発モード)/承認済みvariantの強制進行フェーズでは、
  // 全く検出されない(=data/intents/*.jsonの3件全てnone)場合に限り、将棋上の意図を
  // 推測するのではなく「直近の相手の手はシステムの決まった手順によるものである」
  // という事実だけを説明する。intentが検出されている場合はこの新文言を一切使わず、
  // 既存のintent説明を必ず優先する。
  const FORCED_OPENING_FACT_REASON = "相手の今の手は、対局序盤の決まった手順によるものです。";

  it("opponent_intent / opponent_next_aim (Phase4-A): 全intentがnone かつ 強制進行中の場合、事実ベースの新文言になる", () => {
    const explanations = generateExplanations(NO_SHAPE_RESULTS, NO_INTENT_RESULTS, true);
    const opponentIntent = findStage(explanations, "opponent_intent");
    const nextAim = findStage(explanations, "opponent_next_aim");

    expect(opponentIntent.reason).toBe(FORCED_OPENING_FACT_REASON);
    expect(nextAim.reason).toBe(FORCED_OPENING_FACT_REASON);
    // 将棋上の推測(戦法名・「〜を狙っている」等)を含まないこと
    for (const intent of getIntents()) {
      expect(opponentIntent.reason).not.toContain(intent.name);
      expect(nextAim.reason).not.toContain(intent.name);
    }
    expect(opponentIntent.refers_to_intent_id).toBeNull();
    expect(opponentIntent.confidence_level).toBe("low");
  });

  it("opponent_intent / opponent_next_aim (Phase4-B): 全intentがnone かつ 強制進行中でない場合、従来の文言のまま", () => {
    const explanations = generateExplanations(NO_SHAPE_RESULTS, NO_INTENT_RESULTS, false);
    const opponentIntent = findStage(explanations, "opponent_intent");
    const nextAim = findStage(explanations, "opponent_next_aim");

    expect(opponentIntent.reason).toBe(
      "相手の狙いは、まだはっきりとは分かりません。特定の作戦を決めつけず、もう少し様子を見てみましょう。",
    );
    expect(nextAim.reason).toBe("相手の狙いがまだ定まっていないため、次に何をしてきそうかも現時点では判断できません。");
  });

  it("opponent_intent / opponent_next_aim (Phase4-C): intentが一致していれば、強制進行中でも既存のintent説明を優先する", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    const sfen = sfenAfter(moveHistory);
    const shapeResults = analyzeShapeFormation(sfen, moveHistory);
    const intentResults = detectIntents(sfen, moveHistory);

    const forced = generateExplanations(shapeResults, intentResults, true);
    const notForced = generateExplanations(shapeResults, intentResults, false);

    // wasLastOpponentMoveForcedの値に関わらず、intent一致時の結果は完全に同一(既存挙動を絶対に変えない)。
    expect(forced).toEqual(notForced);

    const opponentIntent = findStage(forced, "opponent_intent");
    expect(opponentIntent.refers_to_intent_id).toBe("hayajikake");
    expect(opponentIntent.reason).not.toBe(FORCED_OPENING_FACT_REASON);
  });

  it("opponent_intent / opponent_next_aim (Phase4-D): 強制進行中でなくintentが一致していれば、従来通りの結果になる", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    const sfen = sfenAfter(moveHistory);
    const shapeResults = analyzeShapeFormation(sfen, moveHistory);
    const intentResults = detectIntents(sfen, moveHistory);

    const withDefaultArg = generateExplanations(shapeResults, intentResults);
    const withExplicitFalse = generateExplanations(shapeResults, intentResults, false);
    expect(withExplicitFalse).toEqual(withDefaultArg);
  });

  it("同じ入力に対して常に同じ結果を返す(決定的。LLM等の非決定的な作文をしない)", () => {
    const first = generateExplanations([TEST_HONMINO], NO_INTENT_RESULTS);
    const second = generateExplanations([TEST_HONMINO], NO_INTENT_RESULTS);
    expect(second).toEqual(first);
  });

  it("すべてのExplanationがdata/schemas/explanations.schema.jsonの必須フィールドを満たす", () => {
    const explanations = generateExplanations([TEST_HONMINO], NO_INTENT_RESULTS);
    for (const explanation of explanations) {
      expect(explanation.id).toMatch(/^[a-z0-9_]+$/);
      expect(["current_shape", "opponent_intent", "opponent_next_aim"]).toContain(explanation.stage);
      expect(explanation.purpose.length).toBeGreaterThan(0);
      expect(explanation.reason.length).toBeGreaterThan(0);
      expect(["high", "medium", "low"]).toContain(explanation.confidence_level);
    }
  });

  // STEP ζ-5: review_statusによる名前の露出制御(analysis/nameExposure.ts)。
  describe("review_statusによる名前の露出制御(STEP ζ-5)", () => {
    it("current_shape completed: draftのshapeの場合、名前に注記付きの文言になる(露出経路1)", () => {
      const draftHonmino: ShapeFormationResult = { ...TEST_HONMINO, reviewStatus: "draft" };
      const explanations = generateExplanations([draftHonmino], NO_INTENT_RESULTS);
      const currentShape = findStage(explanations, "current_shape");

      // STEP 4-6(H-1、人間承認済み): completedのreasonはlead(1文)のみ。characteristicsは
      // 連結しない([5]「参考になる囲い」に説明を任せる)。
      expect(currentShape.reason).toBe(
        "今、本美濃囲いと呼ばれる並びに近い形になっています。ただし、この形の説明は内容を確認中のため、参考程度に見てください。",
      );
    });

    it("current_shape completed: human_reviewedのshapeの場合、注記は付かない(従来どおり)", () => {
      const explanations = generateExplanations([TEST_HONMINO], NO_INTENT_RESULTS);
      const currentShape = findStage(explanations, "current_shape");

      // STEP 4-6(H-1、人間承認済み): characteristicsは連結せずlead(1文)のみ残す。
      expect(currentShape.reason).toBe("今、本美濃囲いの形ができています。");
    });

    it("opponent_intent matched: draftのintentの場合、名前を出さず既存のunclassified文言に落ちる(露出経路2)", () => {
      const draftMatchedIntent: IntentDetectionResult = {
        intentId: "boh_gin",
        name: "棒銀",
        openingId: "ibisha",
        dataConfidenceLevel: "medium",
        reviewStatus: "draft",
        matchStatus: "matched",
        matchScore: 1,
        matchedSignatures: [
          { piece: "銀", to: "7c", evidence: { ply: 2, moveUsi: "7c7d" } },
          { piece: "銀", to: "7d", evidence: { ply: 4, moveUsi: "7d7e" } },
        ],
        unmatchedSignatures: [],
        currentAimExplanation: "テスト用の説明文",
        nextAimExplanation: "テスト用の次の狙い",
      };

      const explanations = generateExplanations(NO_SHAPE_RESULTS, [draftMatchedIntent]);
      const opponentIntent = findStage(explanations, "opponent_intent");

      // 新しい文言は作らず、既存のunclassified(全intentがnoneの場合)と完全に同じ文言に落ちる。
      const unclassified = findStage(generateExplanations(NO_SHAPE_RESULTS, NO_INTENT_RESULTS), "opponent_intent");
      expect(opponentIntent).toEqual(unclassified);
      expect(opponentIntent.reason).not.toContain("棒銀");
    });

    it("opponent_intent matched: human_reviewedのintentの場合、名前を出す(従来どおり)", () => {
      const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
      const sfen = sfenAfter(moveHistory);
      const shapeResults = analyzeShapeFormation(sfen, moveHistory);
      const intentResults = detectIntents(sfen, moveHistory);
      const explanations = generateExplanations(shapeResults, intentResults);

      const opponentIntent = findStage(explanations, "opponent_intent");
      expect(opponentIntent.reason).toContain("早仕掛けの形になっています");
    });
  });

  // STEP 4-4(人間承認R-1、2026-09-10): opponent_next_aimがforming状態でも
  // ステージ自体は落とさず、既存の汎用文(戦法名を含まない)を出す。
  describe("opponent_next_aim: formingでもステージを落とさない(STEP 4-4)", () => {
    it("狙いがformingのとき、opponent_next_aimの段がstatus forming・汎用文・refers_to_intent_id null・glossary_terms空で含まれる", () => {
      const moveHistory = interleaveWithSenteFillers([HAYAJIKAKE_GOTE_MOVES_FULL[0]!]);
      const sfen = sfenAfter(moveHistory);
      const shapeResults = analyzeShapeFormation(sfen, moveHistory);
      const intentResults = detectIntents(sfen, moveHistory);
      const coachExplanations = generateCoachExplanations(shapeResults, intentResults);

      const nextAim = coachExplanations.find((e) => e.stage === "opponent_next_aim");
      expect(nextAim).toBeDefined();
      expect(nextAim!.status).toBe("forming");
      expect(nextAim!.reason).toBe(
        "相手の狙いがまだ定まっていないため、次に何をしてきそうかも現時点では判断できません。",
      );
      expect(nextAim!.refers_to_intent_id).toBeNull();
      expect(nextAim!.glossary_terms).toEqual([]);
    });

    it("狙いがforming、かつwasLastOpponentMoveForcedがtrueのとき、既存のforced文言になる", () => {
      const moveHistory = interleaveWithSenteFillers([HAYAJIKAKE_GOTE_MOVES_FULL[0]!]);
      const sfen = sfenAfter(moveHistory);
      const shapeResults = analyzeShapeFormation(sfen, moveHistory);
      const intentResults = detectIntents(sfen, moveHistory);
      const coachExplanations = generateCoachExplanations(shapeResults, intentResults, true);

      const nextAim = coachExplanations.find((e) => e.stage === "opponent_next_aim");
      expect(nextAim).toBeDefined();
      expect(nextAim!.status).toBe("forming");
      expect(nextAim!.reason).toBe("相手の今の手は、対局序盤の決まった手順によるものです。");
    });

    it("formingのopponent_next_aimのreasonに、いずれの作戦名(棒銀・斜め棒銀・早仕掛け)も含まれない", () => {
      const moveHistory = interleaveWithSenteFillers([HAYAJIKAKE_GOTE_MOVES_FULL[0]!]);
      const sfen = sfenAfter(moveHistory);
      const shapeResults = analyzeShapeFormation(sfen, moveHistory);
      const intentResults = detectIntents(sfen, moveHistory);
      const explanations = generateExplanations(shapeResults, intentResults);

      const nextAim = findStage(explanations, "opponent_next_aim");
      for (const intent of getIntents()) {
        expect(nextAim.reason).not.toContain(intent.name);
      }
    });

    it("狙いがnoneのとき、opponent_next_aimは従来どおりstatus none・同じ汎用文になる", () => {
      const coachExplanations = generateCoachExplanations(NO_SHAPE_RESULTS, NO_INTENT_RESULTS);
      const nextAim = coachExplanations.find((e) => e.stage === "opponent_next_aim");
      expect(nextAim).toBeDefined();
      expect(nextAim!.status).toBe("none");
      expect(nextAim!.reason).toBe(
        "相手の狙いがまだ定まっていないため、次に何をしてきそうかも現時点では判断できません。",
      );
    });

    it("狙いがmatchedのとき、opponent_next_aimは従来どおりstatus matched・next_aim_explanationになる", () => {
      const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
      const sfen = sfenAfter(moveHistory);
      const shapeResults = analyzeShapeFormation(sfen, moveHistory);
      const intentResults = detectIntents(sfen, moveHistory);
      const coachExplanations = generateCoachExplanations(shapeResults, intentResults);

      const nextAim = coachExplanations.find((e) => e.stage === "opponent_next_aim");
      const hayajikake = getIntents().find((i) => i.id === "hayajikake")!;
      expect(nextAim).toBeDefined();
      expect(nextAim!.status).toBe("matched");
      expect(nextAim!.reason).toBe(hayajikake.next_aim_explanation);
    });
  });
});

describe("explainPosition: Unit5(shape_formation_evidence)の統合確認", () => {
  it("初期局面(1手も指していない)では、偶然一致した駒だけを根拠に特定の形を『作ろうとしている』と説明しない", () => {
    // 初期局面は本美濃囲いの必須マスの1つ(6九金)にたまたま金が置かれているが、
    // 一度も動いていないため、これを「作ろうとしている可能性があります」と
    // 説明するのは誤り(Unit4のブラウザ実地確認で発見された問題)。
    const explanations = explainPosition(DEFAULT_INITIAL_SFEN, []);
    const currentShape = findStage(explanations, "current_shape");

    expect(currentShape.refers_to_shape_id).toBeNull();
    expect(currentShape.template_id).toBe("current_shape_unclassified");
    for (const shape of getShapes()) {
      expect(currentShape.reason).not.toContain(shape.name);
    }
  });
});

describe("explainPosition (Unit1/Unit2との統合)", () => {
  it("SFEN+moveHistoryから直接、Unit1(detectShapes)・Unit2(detectIntents)を経由して説明を生成する", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    const sfen = sfenAfter(moveHistory);

    const viaIntegration = explainPosition(sfen, moveHistory);
    const viaManual = generateExplanations(analyzeShapeFormation(sfen, moveHistory), detectIntents(sfen, moveHistory));

    expect(viaIntegration).toEqual(viaManual);
  });

  it("不正な入力(sfenとmoveHistoryの不整合)はdetectIntents由来のエラーがそのまま伝播する", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    expect(() => explainPosition(DEFAULT_INITIAL_SFEN, moveHistory)).toThrow();
  });

  it("不正なSFENに対してエラーを投げる", () => {
    expect(() => explainPosition("not-a-valid-sfen", [])).toThrow();
  });
});
