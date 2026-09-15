// I-9(盤との不一致、draft): ④が特定の形(targetShapeProgress)の組み上がりを
// 出しているのに、指し手で作られたことが確認できる証拠(formationEvidence)が
// ほとんど無い状態を検出する。
//
// 出典: docs/PHASES.md「Unit 6 の再定義と決定」H-5(2026-09-12 人間承認)。
// 背景: docs/OBSERVATION_BEGINNER_CLAUDE_2026-09-12.md 3.(縛った初心者の3局目で、
// 玉を初形から一度も動かしていないのに④が「本美濃囲いに近づいている」と
// 言い続けた)。原因は apps/server/src/analysis/shapeFormationAnalyzer.ts の
// resolveStatus が「一致1件以上 + 指し手で作られた証拠1件以上」でforming/status
// を決めており、証拠がわずか1件(他の駒)でも、要の駒(玉)がたまたま初期配置と
// 一致しているだけで形の組み上がりを言えてしまう点にある。
// H-3(2026-09-12人間決定)により、この構造自体は本STEPでは直さない(閾値と量を
// 同時に変えると効果を分離できないため。順番は「(i) 本ファイルで誤認を測れる
// ようにする → (ii) 量だけ増やす → (iii) 同じ4局で再測定 → (iv) それから閾値を
// 判断」)。
//
// 【この不変条件が言うこと・言わないこと(必ず読むこと)】
// - 形の名前が間違っていると主張しない。data/shapes/*.jsonの内容の正誤は判定しない。
// - ユーザーがその形を目指していたかどうかは判定しない(targetShapeProgressが
//   出ているという画面の事実だけを見る)。
// - 因果(この一致が原因で誤認した、等)は主張しない。
// - 言えるのは「④が組み上がりを出している局面で、指し手で作られたことが確認できる
//   証拠が n 件・欠けているマスが m 件だった」という記録上の事実だけである。
//
// 【本番関数の使い方について】
// 判定(resolveStatus・formationEvidenceの算出)は複製せず、本番関数
// analyzeShapeFormation(apps/server/src/analysis/shapeFormationAnalyzer.ts)を
// そのままimportして呼ぶ(i5-attacked-without-urgent.tsと同じ方針)。
// 記録(JSONL)にはformationEvidenceが入っていないため、sfenとmoveHistoryから
// 本番関数を呼び直して再計算している。同じsfen・moveHistoryに対する決定的な
// 関数のため、記録時点の応答(targetShapeProgress)と矛盾する結果にはならない
// (sfenとmoveHistoryの不整合はanalyzeShapeFormation自身が例外で検出する)。
//
// 【閾値についての注記(draftの初期値であり、将棋一般の閾値ではない)】
// I9_MAX_EVIDENCE(証拠1件以下)・I9_MIN_MISSING(欠け2件以上)は、
// docs/PHASES.md「Unit 6 の再定義と決定」H-5で人間が決めたdraftの初期値である。
// approved化の前に、量産したdata(U6-A)での再測定を踏まえて人間が再判断する
// (H-3の(iv))。
// 「<=」にしている理由: forming状態は構造上formationEvidence.length >= 1を
// 満たすため証拠0件はforming単独では起きないが、resolveStatusの定義
// (「1件以上の証拠があればforming」)をそのまま素直に写すため、
// 「証拠がごくわずか(0件または1件)」という書き方にしている。

import { analyzeShapeFormation } from "../../../apps/server/src/analysis/shapeFormationAnalyzer.js";
import type { Finding, Invariant, InvariantContext, RecordLine } from "./types.js";

const ID = "I-9";

/** draftの初期値(docs/PHASES.md「Unit 6の再定義と決定」H-5)。将棋一般の閾値ではない。 */
const I9_MAX_EVIDENCE = 1;
const I9_MIN_MISSING = 2;

export const i9ShapeClaimWithoutEvidence: Invariant = {
  id: ID,
  title: "④が形の組み上がりを出しているが、指し手で作られた証拠がほとんど無い",
  type: "盤との不一致",
  status: "draft",
  source: "docs/PHASES.md「Unit 6 の再定義と決定」H-5(2026-09-12 人間承認。閾値は draft の初期値)",
  check(records: RecordLine[], context?: InvariantContext): Finding[] {
    const findings: Finding[] = [];

    for (const record of records) {
      if (record.phase !== "ready") continue;

      const targetShapeProgress = record.response.plan.targetShapeProgress;
      if (targetShapeProgress === null) continue;

      let results;
      try {
        // STEP D0-SIDE 段 2(R-7): 開始局面は check.ts が meta から読んで渡す(回して畳んだ記録は平手から並べ直せない。
        // 渡さないと下の catch に飲まれて所見が黙って消える)。文脈の無い呼び出し(既存の試験)は analyzeShapeFormation の既定に任せる
        results = analyzeShapeFormation(record.sfen, record.response.moveHistory, context === undefined ? {} : { initialSfen: context.initialSfen });
      } catch {
        continue;
      }

      const matched = results.find((r) => r.shapeId === targetShapeProgress.shapeId);
      if (!matched) continue;

      const evidenceCount = matched.formationEvidence.length;
      const missingSquares = targetShapeProgress.missingSquares;
      if (evidenceCount > I9_MAX_EVIDENCE) continue;
      if (missingSquares.length < I9_MIN_MISSING) continue;

      const evidenceSquares = matched.formationEvidence.map((e) => e.square).join(", ");
      const missingSquaresText = missingSquares.join(", ");

      findings.push({
        invariantId: ID,
        kifuId: "",
        ply: record.ply,
        phase: record.phase,
        condition: matched.status,
        detail: `④が「${targetShapeProgress.name}」の組み上がりを出している局面で、指し手で作られたことが確認できるマスは ${evidenceCount} 件(${evidenceSquares})、まだ欠けたマスは ${missingSquares.length} 件(${missingSquaresText})です。`,
        sfen: record.sfen,
        senteMove: record.senteMove,
        goteMove: record.goteMove,
      });
    }

    return findings;
  },
};
