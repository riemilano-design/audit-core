// 不変条件の一覧。STEP T-2(I-1〜I-5、すべて当初はstatus: "draft")・STEP T-6
// (I-6を追加。status: "draft")・STEP T-7(I-7を追加。status: "draft")・
// STEP T-8(I-8を追加。status: "draft")・STEP U6-0(I-9を追加。status: "draft")・
// STEP 5-E(I-10を追加。status: "draft"。docs/STEP_5-E_PLAN_2026-09-12.md A-4)・
// STEP 5-F(I-11を追加。status: "draft"。docs/STEP_5-F_PLAN_2026-09-12.md 14.)。
// (docs/PLAYTEST_LOOP_PROPOSAL.md 4.5 規則1: draftはAIが自由に追加してよいが、
// approvedへの変更は人間だけが行う。I-1・I-2はSTEP 5-1で人間承認によりapproved
// になった)。

import { i1SilentExclusion } from "./i1-silent-exclusion.js";
import { i2PlayedCandidateMismatch } from "./i2-played-candidate-mismatch.js";
import { i3ShapePlanAfterEnd } from "./i3-shape-plan-after-end.js";
import { i4CompletedShapeStillTargeted } from "./i4-completed-shape-still-targeted.js";
import { i5AttackedWithoutUrgent } from "./i5-attacked-without-urgent.js";
import { i6AdviceThenLoss } from "./i6-advice-then-loss.js";
import { i7UrgentButOtherTalk } from "./i7-urgent-but-other-talk.js";
import { i8BandPieceThenCaptured } from "./i8-band-piece-then-captured.js";
import { i9ShapeClaimWithoutEvidence } from "./i9-shape-claim-without-evidence.js";
import { i10EscapeSquareNotShown } from "./i10-escape-square-not-shown.js";
import { i11FocusNotStated } from "./i11-focus-not-stated.js";
import type { Invariant } from "./types.js";

export const invariants: Invariant[] = [
  i1SilentExclusion,
  i2PlayedCandidateMismatch,
  i3ShapePlanAfterEnd,
  i4CompletedShapeStillTargeted,
  i5AttackedWithoutUrgent,
  i6AdviceThenLoss,
  i7UrgentButOtherTalk,
  i8BandPieceThenCaptured,
  i9ShapeClaimWithoutEvidence,
  i10EscapeSquareNotShown,
  i11FocusNotStated,
];

export type { Finding, Invariant, InvariantStatus, InvariantType, MetaLine, RecordLine } from "./types.js";
