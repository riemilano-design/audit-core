// 不変条件の一覧。STEP T-2(I-1〜I-5、すべて当初はstatus: "draft")・STEP T-6
// (I-6を追加。status: "draft")・STEP T-7(I-7を追加。status: "draft")。
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
import type { Invariant } from "./types.js";

export const invariants: Invariant[] = [
  i1SilentExclusion,
  i2PlayedCandidateMismatch,
  i3ShapePlanAfterEnd,
  i4CompletedShapeStillTargeted,
  i5AttackedWithoutUrgent,
  i6AdviceThenLoss,
  i7UrgentButOtherTalk,
];

export type { Finding, Invariant, InvariantStatus, InvariantType, MetaLine, RecordLine } from "./types.js";
