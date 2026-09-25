import { describe, expect, it } from "vitest";
import {
  decideNameExposure,
  exposeName,
  NAME_EXPOSURE_VALUES,
  type NameExposureInput,
  type NameExposureValues,
  type ReviewStatus,
} from "./nameExposure.js";

describe("exposeName", () => {
  it("draftの場合、siteに応じた注記(pendingNote)を返す", () => {
    expect(exposeName("銀冠", "draft", "shape").pendingNote).toBe("内容を確認中の形");
    expect(exposeName("銀冠", "draft", "squares").pendingNote).toBe("内容を確認中");
    expect(exposeName("銀冠", "draft", "section").pendingNote).toBe(
      "この形の説明は内容を確認中のため、参考程度に見てください。",
    );
  });

  it("human_reviewedの場合、pendingNoteは常にnull", () => {
    expect(exposeName("本美濃囲い", "human_reviewed", "shape").pendingNote).toBeNull();
    expect(exposeName("本美濃囲い", "human_reviewed", "squares").pendingNote).toBeNull();
    expect(exposeName("本美濃囲い", "human_reviewed", "section").pendingNote).toBeNull();
  });

  it("expert_verifiedの場合、pendingNoteは常にnull(human_reviewedと区別しない)", () => {
    expect(exposeName("本美濃囲い", "expert_verified", "shape").pendingNote).toBeNull();
    expect(exposeName("本美濃囲い", "expert_verified", "squares").pendingNote).toBeNull();
    expect(exposeName("本美濃囲い", "expert_verified", "section").pendingNote).toBeNull();
  });

  it("nameはそのまま返す(内容を書き換えない)", () => {
    expect(exposeName("銀冠", "draft", "shape").name).toBe("銀冠");
    expect(exposeName("本美濃囲い", "human_reviewed", "shape").name).toBe("本美濃囲い");
  });
});

// ---------------------------------------------------------------------------
// STEP EXPO-1(docs/LANE_DIAG_LOG_2026-09.md §12.9): decideNameExposure の規則 R0〜R5。
// **この関数はまだ本体から呼ばれていない**(画面の見え方は変わらない)。ここで見るのは
// 「規則がそのとおりに当たること」「先に当たった規則が勝つこと」「expired が draft と同じこと」。
// ---------------------------------------------------------------------------

/** exposeName の site="shape" と同じ注記(STEP ζ-5 で人間承認済みの文言)。 */
const PENDING_NOTE = "内容を確認中の形";

/** 「今日の規則」を values で表した組(doc コメントの対応。測る側の A と同じ値)。 */
const TODAY_VALUES: NameExposureValues = {
  minRequiredForName: 0,
  minEvidenceForHedged: Number.POSITIVE_INFINITY,
  hideCompletedWithoutEvidence: false,
  // STEP EXPO-1b で足した2欄。今日の規則では R5'・R6 は当てない。
  hedgeOneEvidenceIfMissingLe1: false,
  minEvidenceForCompleted: 0,
};

function input(overrides: Partial<NameExposureInput> = {}): NameExposureInput {
  return {
    kind: "shape",
    status: "forming",
    evidenceCount: 0,
    missingCount: 0,
    requiredCount: 4,
    reviewStatus: "human_reviewed",
    ...overrides,
  };
}

describe("decideNameExposure R0(何も立っていない)", () => {
  it("status none は、証拠・必要な数・review_status によらず hidden(注記も付かない)", () => {
    for (const reviewStatus of ["draft", "human_reviewed", "expert_verified", "expired"] as const) {
      const decision = decideNameExposure(input({ status: "none", evidenceCount: 5, reviewStatus }));
      expect(decision.level).toBe("hidden");
      expect(decision.rule).toBe("R0");
      expect(decision.pendingNote).toBeNull();
    }
  });
});

describe("decideNameExposure R1(draft / expired は named にしない)", () => {
  it("draft の completed は named ではなく hedged になり、注記が付く(expired も同じ)", () => {
    for (const reviewStatus of ["draft", "expired"] as const) {
      const decision = decideNameExposure(input({ status: "completed", evidenceCount: 2, reviewStatus }));
      expect(decision.level).toBe("hedged");
      expect(decision.rule).toBe("R1");
      expect(decision.pendingNote).toBe(PENDING_NOTE);
    }
    // 狙いの matched も同じ(completed と区別しない)。
    const intent = decideNameExposure(
      input({ kind: "intent", status: "matched", evidenceCount: 2, reviewStatus: "draft" }),
    );
    expect(intent.level).toBe("hedged");
    expect(intent.rule).toBe("R1");
  });
});

describe("decideNameExposure R2(証拠0件の completed)", () => {
  it("既定では hidden、hideCompletedWithoutEvidence が false なら通って named / hedged になる", () => {
    const hidden = decideNameExposure(input({ status: "completed", evidenceCount: 0 }));
    expect(hidden.level).toBe("hidden");
    expect(hidden.rule).toBe("R2");

    const off: NameExposureValues = { ...NAME_EXPOSURE_VALUES, hideCompletedWithoutEvidence: false };
    const reviewed = decideNameExposure(input({ status: "completed", evidenceCount: 0 }), off);
    expect(reviewed.level).toBe("named");
    expect(reviewed.rule).toBe("R4");
    const draft = decideNameExposure(input({ status: "completed", evidenceCount: 0, reviewStatus: "draft" }), off);
    expect(draft.level).toBe("hedged");
    expect(draft.rule).toBe("R1");

    // 狙いの matched にも同じように当たる。
    expect(decideNameExposure(input({ kind: "intent", status: "matched", evidenceCount: 0 })).rule).toBe("R2");
  });
});

describe("decideNameExposure R3(必要な数が少なすぎる)", () => {
  it("requiredCount 1 は hidden、2 なら通る(minRequiredForName を変えると境目が動く)", () => {
    const one = decideNameExposure(input({ status: "completed", evidenceCount: 1, requiredCount: 1 }));
    expect(one.level).toBe("hidden");
    expect(one.rule).toBe("R3");

    const two = decideNameExposure(input({ status: "completed", evidenceCount: 1, requiredCount: 2 }));
    expect(two.level).toBe("named");
    expect(two.rule).toBe("R4");

    // 値を 2 にすると requiredCount 2 も落ちる(閾値は values だけで決まる)。
    const stricter: NameExposureValues = { ...NAME_EXPOSURE_VALUES, minRequiredForName: 2 };
    expect(decideNameExposure(input({ status: "completed", evidenceCount: 1, requiredCount: 2 }), stricter).rule).toBe(
      "R3",
    );
  });
});

describe("decideNameExposure R4(レビュー済みの completed)", () => {
  it("human_reviewed / expert_verified の completed は named で、注記は付かない", () => {
    for (const reviewStatus of ["human_reviewed", "expert_verified"] as const) {
      const decision = decideNameExposure(input({ status: "completed", evidenceCount: 1, reviewStatus }));
      expect(decision.level).toBe("named");
      expect(decision.rule).toBe("R4");
      expect(decision.pendingNote).toBeNull();
    }
  });
});

describe("decideNameExposure R5(forming)", () => {
  it("証拠1件は hedged、0件は hidden。minEvidenceForHedged を 2 にすると1件も hidden", () => {
    const one = decideNameExposure(input({ status: "forming", evidenceCount: 1 }));
    expect(one.level).toBe("hedged");
    expect(one.rule).toBe("R5");

    const zero = decideNameExposure(input({ status: "forming", evidenceCount: 0 }));
    expect(zero.level).toBe("hidden");
    expect(zero.rule).toBe("R5");

    const stricter: NameExposureValues = { ...NAME_EXPOSURE_VALUES, minEvidenceForHedged: 2 };
    expect(decideNameExposure(input({ status: "forming", evidenceCount: 1 }), stricter).level).toBe("hidden");
    expect(decideNameExposure(input({ status: "forming", evidenceCount: 2 }), stricter).level).toBe("hedged");

    // forming は reviewed でも named にはならない(最大で hedged)。
    expect(decideNameExposure(input({ status: "forming", evidenceCount: 3 })).level).toBe("hedged");
  });
});

describe("decideNameExposure 規則の優先順(先に当たったものが勝つ)", () => {
  it("R2 は R4 より先に当たり、R3 は R5 より先に当たる", () => {
    // レビュー済みの completed(R4 なら named)でも、証拠0件なら R2 が先に当たって hidden。
    const r2First = decideNameExposure(
      input({ status: "completed", evidenceCount: 0, requiredCount: 4, reviewStatus: "expert_verified" }),
    );
    expect(r2First.rule).toBe("R2");
    expect(r2First.level).toBe("hidden");

    // 証拠が足りている forming(R5 なら hedged)でも、必要な数が1なら R3 が先に当たって hidden。
    const r3First = decideNameExposure(input({ status: "forming", evidenceCount: 2, requiredCount: 1 }));
    expect(r3First.rule).toBe("R3");
    expect(r3First.level).toBe("hidden");

    // R0 は R2・R3 より先(none は他の値を見ずに hidden)。
    expect(decideNameExposure(input({ status: "none", evidenceCount: 0, requiredCount: 1 })).rule).toBe("R0");
  });
});

describe("decideNameExposure expired は draft と同じ", () => {
  it("すべての入力の組(値の組 3 × 状態 4 × 証拠 3 × 欠け 2 × 必要な数 4 = 288 通り)で決定が一致する", () => {
    const valueSets: NameExposureValues[] = [
      NAME_EXPOSURE_VALUES,
      TODAY_VALUES,
      { ...NAME_EXPOSURE_VALUES, minEvidenceForHedged: 2 },
    ];
    const statuses: Array<NameExposureInput["status"]> = ["none", "forming", "completed", "matched"];
    const kinds: Array<NameExposureInput["kind"]> = ["shape", "intent", "opening"];

    let compared = 0;
    for (const values of valueSets) {
      for (const kind of kinds) {
        for (const status of statuses) {
          for (const evidenceCount of [0, 1, 2]) {
            for (const missingCount of [0, 3]) {
              for (const requiredCount of [0, 1, 2, 4]) {
                const base = { kind, status, evidenceCount, missingCount, requiredCount };
                const asDraft = decideNameExposure({ ...base, reviewStatus: "draft" }, values);
                const asExpired = decideNameExposure({ ...base, reviewStatus: "expired" }, values);
                expect(asExpired, JSON.stringify(base)).toEqual(asDraft);
                compared += 1;
              }
            }
          }
        }
      }
    }
    expect(compared).toBe(3 * 3 * 4 * 3 * 2 * 4);
    // 「全部 hidden で一致していた」ではないことを示す(hedged / named も出ている)。
    expect(decideNameExposure(input({ status: "completed", evidenceCount: 1, reviewStatus: "expired" })).level).toBe(
      "hedged",
    );

    // 既存の exposeName でも expired は draft と同じ(site の 3 つとも注記が付く)。
    for (const site of ["shape", "squares", "section"] as const) {
      expect(exposeName("検証用の失効した形", "expired", site)).toEqual(exposeName("検証用の失効した形", "draft", site));
      expect(exposeName("検証用の失効した形", "expired", site).pendingNote).not.toBeNull();
    }
  });
});

describe("decideNameExposure 今日の規則を values で表す", () => {
  it("A の値の組では forming が必ず hidden になり、completed は今日と同じ(reviewed=named / draft=hedged)", () => {
    for (const evidenceCount of [0, 1, 2, 5]) {
      for (const requiredCount of [1, 2, 4]) {
        for (const reviewStatus of ["draft", "human_reviewed", "expert_verified", "expired"] as const) {
          const decision = decideNameExposure(
            input({ status: "forming", evidenceCount, requiredCount, missingCount: 1, reviewStatus }),
            TODAY_VALUES,
          );
          expect(decision.level, `forming 証拠${evidenceCount} 必要${requiredCount} ${reviewStatus}`).toBe("hidden");
        }
      }
    }
    // R2・R3 は当たらないので、証拠0件・必要な数1の completed も通る。
    const noEvidence = decideNameExposure(input({ status: "completed", evidenceCount: 0, requiredCount: 1 }), TODAY_VALUES);
    expect(noEvidence.level).toBe("named");
    expect(noEvidence.rule).toBe("R4");
    const draft = decideNameExposure(
      input({ status: "completed", evidenceCount: 0, requiredCount: 1, reviewStatus: "draft" }),
      TODAY_VALUES,
    );
    expect(draft.level).toBe("hedged");
    expect(draft.rule).toBe("R1");
  });
});

describe("NAME_EXPOSURE_VALUES", () => {
  it("閾値は1か所だけで、値は案のとおり(1 / 1 / true。EXPO-1b の2欄は決定を変えない値)", () => {
    expect(NAME_EXPOSURE_VALUES).toEqual({
      minRequiredForName: 1,
      minEvidenceForHedged: 1,
      hideCompletedWithoutEvidence: true,
      // STEP EXPO-1b で足した2欄。既定は「R5' を当てない」「R6 が何も落とさない」= 既定の決定は不変。
      hedgeOneEvidenceIfMissingLe1: false,
      minEvidenceForCompleted: 0,
    });
    // 既定の引数は NAME_EXPOSURE_VALUES(明示して渡したときと同じ結果になる)。
    const line: NameExposureInput = input({ status: "forming", evidenceCount: 1 });
    expect(decideNameExposure(line)).toEqual(decideNameExposure(line, NAME_EXPOSURE_VALUES));
    // ReviewStatus は4値(expired を含む)。
    const all: ReviewStatus[] = ["draft", "human_reviewed", "expert_verified", "expired"];
    expect(all).toHaveLength(4);
  });
});

// ---------------------------------------------------------------------------
// STEP EXPO-1b(§12.9 の追記): R5'(証拠1件でも欠け ≤ 1 なら hedged)と
// R6(completed / matched に証拠の下限を要求する)。**既定の値では両方とも当たらない**
// ことも、ここで固定する(既定の決定は EXPO-1 と同じ)。
// ---------------------------------------------------------------------------

/** 測る側(scripts/playtest の EXPOSURE_VALUE_SETS)の D。比較のためだけの組(採用候補ではない)。 */
const D_VALUES: NameExposureValues = {
  minRequiredForName: 1,
  minEvidenceForHedged: 2,
  hideCompletedWithoutEvidence: true,
  hedgeOneEvidenceIfMissingLe1: true,
  minEvidenceForCompleted: "all",
};
/** 同 D'(R6 の下限を 2 にした組)。 */
const D_PRIME_VALUES: NameExposureValues = { ...D_VALUES, minEvidenceForCompleted: 2 };
/** 同 D''(R6 の下限を「初期位置と違うマスにある必要な駒の数」にした組)。 */
const D_PRIME2_VALUES: NameExposureValues = { ...D_VALUES, minEvidenceForCompleted: "movedRequired" };

describe("decideNameExposure R5'(証拠1件で、あと1つで完成)", () => {
  it("証拠1件・欠け1件の forming を hedged にする(rule は R5p。既定の値では当たらない)", () => {
    const decision = decideNameExposure(
      input({ status: "forming", evidenceCount: 1, missingCount: 1, requiredCount: 4 }),
      D_VALUES,
    );
    expect(decision.level).toBe("hedged");
    expect(decision.rule).toBe("R5p");

    // 同じ行は、R5' を当てない値(既定・C 相当)では hidden(証拠が下限 2 に届かない)。
    const off: NameExposureValues = { ...D_VALUES, hedgeOneEvidenceIfMissingLe1: false };
    const hidden = decideNameExposure(
      input({ status: "forming", evidenceCount: 1, missingCount: 1, requiredCount: 4 }),
      off,
    );
    expect(hidden.level).toBe("hidden");
    expect(hidden.rule).toBe("R5");

    // 証拠が 2 件あれば R5' ではなく R5 で hedged(R5' は「証拠1件」だけを拾う)。
    expect(
      decideNameExposure(input({ status: "forming", evidenceCount: 2, missingCount: 1 }), D_VALUES).rule,
    ).toBe("R5");
  });

  it("欠けが2件以上の行は拾わない(hidden のまま)", () => {
    for (const missingCount of [2, 3, 5]) {
      const decision = decideNameExposure(
        input({ status: "forming", evidenceCount: 1, missingCount, requiredCount: 6 }),
        D_VALUES,
      );
      expect(decision.level, `欠け ${missingCount}`).toBe("hidden");
      expect(decision.rule, `欠け ${missingCount}`).toBe("R5");
    }
    // 欠け 0 は forming では起きないが、値の上では拾う側に入る(境目は「≤ 1」)。
    expect(
      decideNameExposure(input({ status: "forming", evidenceCount: 1, missingCount: 0 }), D_VALUES).rule,
    ).toBe("R5p");
  });
});

describe("decideNameExposure R6(completed / matched に要求する証拠の下限)", () => {
  it('"all" は「必要4・証拠3」の completed を hidden にする(本美濃の型)', () => {
    // 本美濃の型: 必要な駒 4 のうち 1 つ(金4i)は初期位置なので、動いた証拠は 3 件までしか出ない。
    const line = input({
      status: "completed",
      evidenceCount: 3,
      missingCount: 0,
      requiredCount: 4,
      movedRequiredCount: 3,
    });

    const dropped = decideNameExposure(line, D_VALUES);
    expect(dropped.level).toBe("hidden");
    expect(dropped.rule).toBe("R6");
    expect(dropped.pendingNote).toBeNull();

    // 必要な駒が全部動いた形(必要4・証拠4)は "all" でも落ちない。
    expect(
      decideNameExposure(input({ status: "completed", evidenceCount: 4, requiredCount: 4 }), D_VALUES).rule,
    ).toBe("R4");
    // 狙いの matched にも同じように当たる。
    expect(
      decideNameExposure(input({ kind: "intent", status: "matched", evidenceCount: 1, requiredCount: 3 }), D_VALUES)
        .rule,
    ).toBe("R6");
  });

  it('"movedRequired" は「必要4・うち初期位置1・証拠3」の completed を落とさない', () => {
    const line = input({
      status: "completed",
      evidenceCount: 3,
      missingCount: 0,
      requiredCount: 4,
      movedRequiredCount: 3,
    });
    // D'(下限 2)・D''(下限 = 動くべき駒 3)では落ちない(D では上の試験のとおり落ちる)。
    expect(decideNameExposure(line, D_PRIME_VALUES).level).toBe("named");
    expect(decideNameExposure(line, D_PRIME_VALUES).rule).toBe("R4");
    expect(decideNameExposure(line, D_PRIME2_VALUES).level).toBe("named");
    expect(decideNameExposure(line, D_PRIME2_VALUES).rule).toBe("R4");
    // 下書きなら R1 で hedged(R6 を通った後の扱いは今までどおり)。
    expect(decideNameExposure({ ...line, reviewStatus: "draft" }, D_PRIME2_VALUES).rule).toBe("R1");
    // 動くべき駒の数に証拠が足りなければ、D'' でも落ちる(下限の出どころが違うだけ)。
    expect(decideNameExposure({ ...line, evidenceCount: 2 }, D_PRIME2_VALUES).rule).toBe("R6");
  });

  it('"movedRequired" は「動くべき必要な駒が0」の completed を hidden にする(渡されなければ例外)', () => {
    // P-85 の型: 必要な駒が全部初期位置 → 動いた証拠を持ちようがない。
    const line = input({
      status: "completed",
      evidenceCount: 1,
      missingCount: 0,
      requiredCount: 3,
      movedRequiredCount: 0,
      reviewStatus: "expert_verified",
    });
    const decision = decideNameExposure(line, D_PRIME2_VALUES);
    expect(decision.level).toBe("hidden");
    expect(decision.rule).toBe("R6");
    // 証拠0件なら R2 のほうが先に当たる(同じ hidden だが内訳が別)。
    expect(decideNameExposure({ ...line, evidenceCount: 0 }, D_PRIME2_VALUES).rule).toBe("R2");
    // D'(下限 2)では、この行は証拠1件なので落ちる理由が R6 のまま(下限の出どころだけが違う)。
    expect(decideNameExposure(line, D_PRIME_VALUES).rule).toBe("R6");

    // movedRequiredCount を渡さずに "movedRequired" を指定したら例外(黙って 0 や requiredCount で代用しない)。
    expect(() =>
      decideNameExposure(input({ status: "completed", evidenceCount: 2, requiredCount: 3 }), D_PRIME2_VALUES),
    ).toThrow(/movedRequiredCount/);
    // forming の行は R6 を通らないので、渡さなくても例外にならない。
    expect(
      decideNameExposure(input({ status: "forming", evidenceCount: 2, missingCount: 2 }), D_PRIME2_VALUES).rule,
    ).toBe("R5");
  });
});

describe("decideNameExposure EXPO-1b の2欄の既定値は決定を変えない", () => {
  it("A・B・C の値の組では R5p・R6 が1度も当たらず、EXPO-1 の規則表どおりの結果になる", () => {
    /** EXPO-1(R0〜R5)の規則を、この試験の中に書き写した参照実装(実装を import しない)。 */
    const expo1 = (line: NameExposureInput, values: NameExposureValues): { level: string; rule: string } => {
      const pending = line.reviewStatus === "draft" || line.reviewStatus === "expired";
      const complete = line.status === "completed" || line.status === "matched";
      if (line.status === "none") return { level: "hidden", rule: "R0" };
      if (values.hideCompletedWithoutEvidence && complete && line.evidenceCount === 0) {
        return { level: "hidden", rule: "R2" };
      }
      if (line.requiredCount <= values.minRequiredForName) return { level: "hidden", rule: "R3" };
      if (complete) return pending ? { level: "hedged", rule: "R1" } : { level: "named", rule: "R4" };
      return {
        level: line.evidenceCount >= values.minEvidenceForHedged ? "hedged" : "hidden",
        rule: "R5",
      };
    };

    // 測る側の A(今日の規則)・B(案)・C(案。forming の下限だけ 2)と同じ値。
    const sets: NameExposureValues[] = [
      TODAY_VALUES,
      NAME_EXPOSURE_VALUES,
      { ...NAME_EXPOSURE_VALUES, minEvidenceForHedged: 2 },
    ];
    const statuses: Array<NameExposureInput["status"]> = ["none", "forming", "completed", "matched"];
    let compared = 0;
    for (const values of sets) {
      for (const status of statuses) {
        for (const evidenceCount of [0, 1, 2, 4]) {
          for (const missingCount of [0, 1, 2]) {
            for (const requiredCount of [1, 2, 4]) {
              for (const reviewStatus of ["draft", "human_reviewed"] as const) {
                const line = input({ status, evidenceCount, missingCount, requiredCount, reviewStatus });
                const decision = decideNameExposure(line, values);
                const expected = expo1(line, values);
                expect({ level: decision.level, rule: decision.rule }, JSON.stringify(line)).toEqual(expected);
                compared += 1;
              }
            }
          }
        }
      }
    }
    expect(compared).toBe(3 * 4 * 4 * 3 * 3 * 2);
    // 「全部 hidden で一致していた」ではないことを示す(3段階とも出ている)。
    expect(decideNameExposure(input({ status: "completed", evidenceCount: 2 }))).toMatchObject({ level: "named" });
    expect(decideNameExposure(input({ status: "forming", evidenceCount: 1 }))).toMatchObject({ level: "hedged" });
  });
});
