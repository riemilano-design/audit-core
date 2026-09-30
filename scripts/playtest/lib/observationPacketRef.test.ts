// 束 V-a の試験(計画 docs/PLAN_VERIFIER_PACKET_2026-09-30.md §6 の 1・3)。
//
// 【何を固定するか】(1) packet の中の場所の**引き当て**(`resolvePacketPath`)、
// (2) 集計 1 行の**数え直し**(`recountRowProblems`)、(3) 検査 **H-9**(実在と値の一致)。
// 【試験を別のファイルにした理由】`lib/hypothesis.test.ts` は実験席も同じ日に触っている(R2)。
// **並行しているファイルへの書き込みを最小にする**(あちらには検査の本数の 2 行だけ直した)。
// 【文法は見ない】path の文法は `lib/packetRef.ts`(実験席の module)が持ち、H-2 が見る。
// ここが見るのは**実在と値**だけ ― 同じ規則を 2 か所に置かない(司令塔の条件 2026-09-30)。
import { describe, expect, it } from "vitest";
import { recountRowProblems } from "./observationAggregates.js";
import { resolvePacketPath } from "./observationPacket.js";
import { packetRefPathProblems } from "./packetRef.js";
import { loadObsRegistry, validateHypothesisLine, type CheckResult } from "./hypothesis.js";

/**
 * 最小の packet(**数は facts から数えた値**にしてある ― 数え直しが通る形)。
 * 分かれ道 2 行のうち第 1 候補が攻めは 2 件、実戦も攻めは 1 件 → `sideMatch.attack` = 1 / 2。
 */
function packet(): Record<string, unknown> {
  return {
    contract: "observation-packet",
    schemaVersion: "0.1",
    packetId: "0".repeat(16),
    customerRef: "c5",
    facts: {
      games: [{ gameId: "g01", no: 1, side: "先手", result: "負け", ownPlyCount: 1, totalPlyCount: 2, timeLimitSec: 180, aheadAtAnyPoint: true, src: "m1" }],
      moves: [{ gameId: "g01", ply: 1, side: "own", usi: "7g7f", collapsed: true, spentSec: 1, src: "m1" }],
      engine: [{ gameId: "g01", ply: 1, sfen: "(合成)", src: "e1" }],
      time: [{ gameId: "g01", longThinkCount: 5, src: "m1" }],
      branches: [
        { gameId: "g01", ply: 1, displayPly: 1, top1Side: "attack", actualSide: "attack", topGapCp: 120, src: "e2" },
        { gameId: "g01", ply: 1, displayPly: 3, top1Side: "attack", actualSide: "defense", topGapCp: 80, src: "e2" },
      ],
      collapse: [{ gameId: "g01", ply: 1, src: "m1" }],
      recognition: { rows: [{ gameId: "g01", signatureClass: "多数の核", names: ["鬼殺し"], src: "r1" }], definitions: [{ id: "onikoroshi", name: "鬼殺し", src: "r1" }] },
    },
    aggregates: [
      {
        id: "sideMatch.attack", name: "第 1 候補の側が攻めだった分かれ道のうち、実戦も攻めの側だった局面",
        unit: "positions", population: { from: "branches", where: [{ field: "top1Side", op: "==", value: "attack" }], unit: "positions" },
        numeratorWhere: [{ field: "actualSide", op: "in", value: ["attack", "both"] }],
        numerator: 1, denominator: 2, derivedFrom: ["g01"], src: "e1", recountable: true, timeDependent: false,
      },
      {
        id: "branches.total", name: "分かれ道として読んだ局面", unit: "positions",
        population: { from: "branches", where: [], unit: "positions" },
        value: 2, derivedFrom: ["g01"], src: "e2", recountable: true, timeDependent: false,
      },
      {
        id: "time.bySpent0to1", name: "0〜1 秒で指した手のうち、評価の区分が下がった手", unit: "moves",
        population: { from: "moves", where: [{ field: "spentSec", op: "<=", value: 1 }], unit: "moves" },
        numeratorWhere: [{ field: "collapsed", op: "==", value: true }],
        numerator: 22, denominator: 531, derivedFrom: ["g01"], src: "m1", recountable: false,
        recountNote: "材料の秒は中盤の手だけで、facts で秒が付いた手は一部しか無い。数は材料の写し(束 C の記録)",
        timeDependent: true,
      },
    ],
    provenance: {
      pipelineVersion: "0", generatedAt: "2026-09-30T00:00:00Z",
      sources: [{ id: "m1", type: "material", inputPaths: ["x.json"] }],
      inputs: [{ path: "x.json", sha256: "a".repeat(64), bytes: 1 }],
      thresholds: [{ id: "ahead_cp", value: 300, unit: "centipawns", from: "x" }],
    },
  };
}

/** H-9 が読む欄だけを持つ行(他の検査の結果はここでは見ない) */
function lineWith(observations: unknown[]): Record<string, unknown> {
  return {
    schemaVersion: "0.4",
    hypothesisId: "V-001",
    subject: { customer: "c5", groups: ["3 分"], gamesCount: 25 },
    scope: "this_user",
    lane: "side",
    statement: "第 1 候補が攻めの手だった分かれ道で、実戦も攻めだったのは 1 / 2 という読みです",
    observations,
    counterEvidence: { attempted: true, items: [], result: "none_found", provenance: { inputs: [] } },
    prediction: { writtenAt: "2026-09-30", window: "次の 25 局", metric: "sideMatch.attack", comparator: ">=", value: 1, alsoRequires: [] },
    status: "proposed",
    knowledge: { kind: "discovered", reviewStatus: "draft", origin: { kifu: "c5", lane: "side" }, range: "this_user" },
    provenance: { gitHead: null, inputs: [], excludedInputs: [] },
  };
}

function h9Of(line: unknown, packetValue?: unknown): CheckResult {
  const results = validateHypothesisLine(line, { today: "2026-09-30", registry: new Set<string>(), packet: packetValue });
  return results.find((result) => result.check === "H-9")!;
}

describe("packet の中の場所を引き当てる", () => {
  it("m1 集計の行は数の欄まで書けば引ける", () => {
    const p = packet();
    expect(resolvePacketPath(p, "aggregates.sideMatch.attack.numerator")).toEqual({ ok: true, value: 1 });
    expect(resolvePacketPath(p, "aggregates.sideMatch.attack.denominator")).toEqual({ ok: true, value: 2 });
    expect(resolvePacketPath(p, "aggregates.branches.total.value")).toEqual({ ok: true, value: 2 });
  });

  it("m2 集計の行を id だけで指すと引かない(文法は packetRef.ts の 1 か所が落とす)", () => {
    // **理由の文は実験席の module のもの** ― こちらで書き直さない(2 か所に増やさない)。
    // 文法が単独形を受けるように変わったら、ここは「引けた」に変わって赤になる。
    const resolved = resolvePacketPath(packet(), "aggregates.sideMatch.attack");
    expect(resolved.ok).toBe(false);
    expect(resolved.ok === false && resolved.reason).toEqual(
      packetRefPathProblems("aggregates.sideMatch.attack")[0],
    );
    expect(packetRefPathProblems("aggregates.sideMatch.attack.numerator")).toEqual([]);
  });

  it("m3 無い行・無い欄は理由を返す(黙って undefined を返さない)", () => {
    const p = packet();
    const noRow = resolvePacketPath(p, "aggregates.nazono.gyou.value");
    expect(noRow.ok === false && noRow.reason).toContain("集計に nazono.gyou の行が無い");
    // 分数の行に `.value` は無い(取り違えをそのまま通さない)
    const wrongField = resolvePacketPath(p, "aggregates.sideMatch.attack.value");
    expect(wrongField.ok === false && wrongField.reason).toContain("value が無い");
    // 単独の数の行に `.numerator` も無い
    const wrongField2 = resolvePacketPath(p, "aggregates.branches.total.numerator");
    expect(wrongField2.ok === false && wrongField2.reason).toContain("numerator が無い");
  });

  it("m4 事実の行は列と添字と欄で引ける(外・無い欄・読めない形は理由を返す)", () => {
    const p = packet();
    expect(resolvePacketPath(p, "facts.branches[1].topGapCp")).toEqual({ ok: true, value: 80 });
    expect(resolvePacketPath(p, "facts.games[0].result")).toEqual({ ok: true, value: "負け" });
    expect(resolvePacketPath(p, "facts.recognition.rows[0].names")).toEqual({ ok: true, value: ["鬼殺し"] });
    const outOfRange = resolvePacketPath(p, "facts.branches[9].topGapCp");
    expect(outOfRange.ok === false && outOfRange.reason).toContain("列の外");
    const noField = resolvePacketPath(p, "facts.branches[0].nazonoRan");
    expect(noField.ok === false && noField.reason).toContain("packet に無い");
    // packet の外・読めない形も**文法の 1 か所**が落とす(こちらに 2 本目の判定を置かない)
    const outside = resolvePacketPath(p, "out.c5.packet");
    expect(outside.ok === false && outside.reason).toEqual(packetRefPathProblems("out.c5.packet")[0]);
    const broken = resolvePacketPath(p, "facts..branches");
    expect(broken.ok === false && broken.reason).toEqual(packetRefPathProblems("facts..branches")[0]);
    // **文法を通った path でだけ、実在の理由(列の外・欄が無い)が出る**ことの裏
    expect(packetRefPathProblems("facts.branches[9].topGapCp")).toEqual([]);
    expect(packetRefPathProblems("facts.branches[0].nazonoRan")).toEqual([]);
    // packet が無ければそう言う
    const noPacket = resolvePacketPath(undefined, "facts.games[0].result");
    expect(noPacket.ok === false && noPacket.reason).toContain("packet が無い");
  });
});

describe("集計 1 行の数え直し", () => {
  it("m5 数え直せる行は通り、数をずらせば落ちる。数え直せない行は印だけ", () => {
    const p = packet();
    expect(recountRowProblems(p, "sideMatch.attack")).toEqual({ problems: [], notes: [] });
    const shifted = packet();
    (shifted.aggregates as Record<string, unknown>[])[0]!.numerator = 2;
    expect(recountRowProblems(shifted, "sideMatch.attack").problems.join("\n")).toContain("分子が 2");
    // **数え直せない行は落とさず、採る側(⑤)に見せる印を返す**(司令塔の決定 2026-09-30)
    const copied = recountRowProblems(p, "time.bySpent0to1");
    expect(copied.problems).toEqual([]);
    expect(copied.notes.join("\n")).toContain("数え直せない行");
    expect(recountRowProblems(p, "nazono.gyou").problems.join("\n")).toContain("行が無い");
  });
});

describe("H-9(packetRef の実在と値の一致)", () => {
  it("m6 packet を渡さなければ回さない(未照合の印。緑にしない)", () => {
    const result = h9Of(lineWith([{ obsId: "packet.aggregates.sideMatch.attack.numerator", value: 1, packetRef: { path: "aggregates.sideMatch.attack.numerator" } }]));
    expect(result.ok).toBe(true);
    expect(result.skipped).toBe(true);
    expect(result.messages.join("\n")).toContain("未照合");
    expect(result.messages.join("\n")).toContain("1 件");
  });

  it("m7 packet の値と合えば通り、ずれれば落ちる", () => {
    const p = packet();
    const good = h9Of(lineWith([
      { obsId: "packet.aggregates.sideMatch.attack.numerator", value: 1, packetRef: { path: "aggregates.sideMatch.attack.numerator" } },
      { obsId: "packet.facts.branches[1].topGapCp", value: 80, packetRef: { path: "facts.branches[1].topGapCp" } },
    ]), p);
    expect(good).toMatchObject({ ok: true });
    expect(good.skipped).toBeUndefined();
    // 席が書いた値が packet と違う
    const wrongValue = h9Of(lineWith([{ obsId: "packet.aggregates.sideMatch.attack.numerator", value: 65, packetRef: { path: "aggregates.sideMatch.attack.numerator" } }]), p);
    expect(wrongValue.ok).toBe(false);
    expect(wrongValue.messages.join("\n")).toContain("value が packet と違う");
    // 在らない場所
    const noPath = h9Of(lineWith([{ obsId: "packet.facts.branches[9].topGapCp", value: 80, packetRef: { path: "facts.branches[9].topGapCp" } }]), p);
    expect(noPath.ok).toBe(false);
    expect(noPath.messages.join("\n")).toContain("列の外");
    // 列(配列)の値も比べられる
    const listValue = h9Of(lineWith([{ obsId: "packet.facts.recognition.rows[0].names", value: ["鬼殺し"], packetRef: { path: "facts.recognition.rows[0].names" } }]), p);
    expect(listValue).toMatchObject({ ok: true });
  });

  it("m8 集計の行を根拠にしたら、その行を数え直す(数え直せない行は印だけ)", () => {
    const shifted = packet();
    (shifted.aggregates as Record<string, unknown>[])[0]!.numerator = 2;
    const result = h9Of(lineWith([{ obsId: "packet.aggregates.sideMatch.attack.numerator", value: 2, packetRef: { path: "aggregates.sideMatch.attack.numerator" } }]), shifted);
    // 値は packet と合っているが、**packet の数そのものが母集団と合っていない**
    expect(result.ok).toBe(false);
    expect(result.messages.join("\n")).toContain("数え直し");
    const copied = h9Of(lineWith([{ obsId: "packet.aggregates.time.bySpent0to1.numerator", value: 22, packetRef: { path: "aggregates.time.bySpent0to1.numerator" } }]), packet());
    expect(copied.ok).toBe(true);
    expect(copied.notes?.join("\n")).toContain("数え直せない行");
  });

  it("m9 packetRef を持たない行(版 0.3 まで)は H-9 が何も言わない", () => {
    const result = h9Of(lineWith([{ obsId: "obs.time.longThinkTotal", path: "time_cause games[].longThinkTotal", value: 5 }]), packet());
    expect(result).toEqual({ check: "H-9", ok: true, messages: [] });
  });

  it("m10 反証の項目の観測も見る(本体だけ見て終わりにしない)", () => {
    const line = lineWith([]);
    line.counterEvidence = {
      attempted: true,
      items: [{ kind: "denominator", text: "分母が小さい", observations: [{ obsId: "packet.aggregates.branches.total.value", value: 99, packetRef: { path: "aggregates.branches.total.value" } }] }],
      result: "weakened",
      provenance: { inputs: [] },
    };
    const result = h9Of(line, packet());
    expect(result.ok).toBe(false);
    expect(result.messages.join("\n")).toContain("counterEvidence.items[0].observations[0]");
  });

  it("m11 登録簿を読む口は前と同じ(H-9 を足しても他の検査の入口は変わらない)", () => {
    // `loadObsRegistry` は既存の入口(H-2 が使う)。H-9 を足しても引数の形は変えていない
    expect(typeof loadObsRegistry).toBe("function");
  });
});
