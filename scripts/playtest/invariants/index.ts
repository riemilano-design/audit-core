// 不変条件(draft)5件の一覧。STEP T-2。すべて status: "draft"
// (docs/PLAYTEST_LOOP_PROPOSAL.md 4.5 規則1: draftはAIが自由に追加してよいが、
// approvedへの変更は人間だけが行う)。

import { i1SilentExclusion } from "./i1-silent-exclusion.js";
import { i2PlayedCandidateMismatch } from "./i2-played-candidate-mismatch.js";
import { i3ShapePlanAfterEnd } from "./i3-shape-plan-after-end.js";
import { i4CompletedShapeStillTargeted } from "./i4-completed-shape-still-targeted.js";
import { i5AttackedWithoutUrgent } from "./i5-attacked-without-urgent.js";
import type { Invariant } from "./types.js";

export const invariants: Invariant[] = [
  i1SilentExclusion,
  i2PlayedCandidateMismatch,
  i3ShapePlanAfterEnd,
  i4CompletedShapeStillTargeted,
  i5AttackedWithoutUrgent,
];

export type { Finding, Invariant, InvariantStatus, InvariantType, MetaLine, RecordLine } from "./types.js";
