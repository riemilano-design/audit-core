// 束 R1 の試験(計画 docs/STEP_LLM_SEATS_R1_RENDER_2026-09-30.md §5)。
//
// 【要点】「通った」は証拠にならない ― 止まる条件はそれぞれ止まること、校正の道具はわざとずらした写しで捕まることを見る。
// 【最小の packet は隣の束(observationPacket.test.ts)と同じ形】試験の中で組み、契約を通ることを先に確かめる。
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { OBSERVATION_PACKET_CONTRACT, OBSERVATION_PACKET_SCHEMA_VERSION, OBSERVATION_REQUEST_CONTRACT, observationPacketProblems, packetIdOf, validateObservationRequest } from "./observationPacket.js";
import { AGGREGATE_REF_RE } from "./packetRef.js";
import {
  INSTRUCTION_V1_SHA256, READING_GUIDE, SeatInputError, dataLinesOf, identifierProblems, numberInclusionProblems, numberTokens, renderSeatInput,
} from "./seatInput.js";

const INSTRUCTION = readFileSync(new URL("../../../docs/LLM_SEATS_INSTRUCTION_v1_2026-09-30.md", import.meta.url));
const RUN_ID = "run20260930abc";

function minimalFacts() {
  return {
    games: [
      { gameId: "g01", no: 1, side: "先手", result: "負け", ending: "投了", ownPlyCount: 62, totalPlyCount: 123, timeLimitSec: 180, mirrored: false, src: "m1" },
    ],
    moves: [
      { gameId: "g01", ply: 48, side: "own", usi: "P*4d", piece: "pawn", drop: true, spentSec: 12.5, phase: "mid", isFork: true, tags: ["drop"], collapsed: false, src: "m1" },
      { gameId: "g01", ply: 50, side: "own", usi: "8g8f", piece: "pawn", drop: false, spentSec: 3, phase: "mid", isFork: false, tags: [], collapsed: true, src: "m1" },
    ],
    engine: [
      { gameId: "g01", ply: 48, sfen: "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1", scoreCp: 120, top1Usi: "8g8f", actualUsi: "P*4d", candidates: [{ usi: "8g8f", scoreCp: 120, pv: ["8g8f", "3c3d"] }], nodes: 2000, multipv: 5, src: "e1" },
    ],
    time: [
      { gameId: "g01", earlySpentSec: 30, midSpentSec: 90, lateSpentSec: 40, longThinkCount: 3, longThinkForkCount: 2, longThinkOppositeCount: 1, remainingSec: 0, timeUpLoss: false, src: "m1" },
    ],
    branches: [
      { gameId: "g01", ply: 48, displayPly: 48, top1Usi: "8g8f", actualUsi: "P*4d", top1Side: "attack", actualSide: "defense", top1Tags: ["capture"], actualTags: ["drop"], topGapCp: 80, firstVisibleNodes: 2000, shallowVisible: true, src: "e1", srcFirstVisibleNodes: "e2" },
    ],
    collapse: [
      { gameId: "g01", ply: 50, beforeCp: 320, afterCp: -140, bandBefore: "ahead", bandAfter: "level", kind: "drop", src: "m1" },
    ],
    recognition: {
      rows: [
        { gameId: "g01", selfSignature: ["onikoroshi"], opponentSignature: ["sansan_kaku_senpo"], signatureClass: "多数の核", names: ["鬼殺し"], selfRecognized: true, opponentRecognized: true, selfStrongRecognized: true, opponentStrongRecognized: false, reviewStatus: "draft", src: "r1" },
      ],
      definitions: [
        { id: "onikoroshi", name: "鬼殺し", side: "self", reviewStatus: "draft", recognitionPattern: [{ orderHint: 1, piece: "桂", to: "77" }], src: "r1" },
      ],
    },
  };
}

function minimalAggregates() {
  return [
    {
      id: "side_match.attack", numerator: 1, denominator: 1, unit: "positions",
      name: "第 1 候補が攻めの手だった分かれ道のうち、実戦も攻めの手だった局面",
      population: { from: "branches", where: [{ field: "top1Side", op: "==", value: "attack" }], unit: "positions" },
      derivedFrom: ["g01"], src: "e1", recountable: true, timeDependent: false,
    },
    {
      id: "branches.total", value: 1, unit: "positions", name: "分かれ道の総数",
      population: { from: "branches", where: [], unit: "positions" }, derivedFrom: ["g01"], src: "e1", recountable: true, timeDependent: false,
    },
  ];
}

function minimalPacket() {
  const facts = minimalFacts();
  const aggregates = minimalAggregates();
  return {
    contract: OBSERVATION_PACKET_CONTRACT,
    schemaVersion: OBSERVATION_PACKET_SCHEMA_VERSION,
    packetId: packetIdOf(facts, aggregates),
    customerRef: "c5",
    facts,
    aggregates,
    provenance: {
      pipelineVersion: "0000000",
      generatedAt: "2026-09-30T00:00:00Z",
      sources: [
        { id: "e1", type: "engine", engineVersion: "(仮)", nodesLimit: 2000, multipv: 5, generatedAt: "2026-09-30T00:00:00Z", inputPaths: ["scripts/playtest/out/c5/pipe-3min/report/patient_report_data.json"] },
        { id: "m1", type: "material", kind: "patient-report-data", gitHead: "0000000", inputPaths: ["scripts/playtest/out/c5/pipe-3min/report/patient_report_data.json"] },
        { id: "r1", type: "recognition", definitionsDirs: ["data/openings"], reviewStatus: "draft", inputPaths: ["scripts/playtest/out/c5/pipe-3min/report/patient_report_data.json"] },
      ],
      inputs: [{ path: "scripts/playtest/out/c5/pipe-3min/report/patient_report_data.json", sha256: "a".repeat(64), bytes: 104857 }],
      thresholds: [{ id: "ahead_cp", value: 300, unit: "centipawns", from: "scripts/playtest/report-pdf/exit_groups.py AHEAD_CP" }],
    },
  };
}

function minimalRequest() {
  return {
    contract: OBSERVATION_REQUEST_CONTRACT,
    schemaVersion: "0.1",
    customerRef: "c5",
    customerQuestions: [{ id: "q1", text: "普段指さない戦型のときに何が変わるか", askedAt: "2026-09-29", via: "relayed" }],
    requestedScope: { games: 1, timeLimitSec: 180, note: "3 分切れ負け" },
  };
}

function render(overrides: Partial<Parameters<typeof renderSeatInput>[0]> = {}) {
  return renderSeatInput({ packet: minimalPacket(), request: minimalRequest(), instruction: INSTRUCTION, runId: RUN_ID, ...overrides });
}

describe("最小の packet / request は契約を通る(通らない fixture で試験しない)", () => {
  it("packet", () => expect(observationPacketProblems(minimalPacket())).toEqual([]));
  it("request", () => expect(validateObservationRequest(minimalRequest())).toEqual([]));
  it("指示文 v1 の sha は固定値", () => {
    const { meta } = render();
    expect(meta.instructionSha256).toBe(INSTRUCTION_V1_SHA256);
  });
});

describe("本文の形(節の順・行数・packetRef の文法)", () => {
  it("節は A → 0.3 → 1 … 8 の順で、行数は packet の配列の長さ", () => {
    const { meta } = render();
    expect(meta.sections.map((s) => s.section)).toEqual(["A", "0.3", "1", "2", "3", "4", "5", "6", "6.1", "7", "8"]);
    expect(meta.sections.map((s) => s.rows)).toEqual([1, 3, 1, 3, 1, 1, 1, 1, 1, 2, 1]); // 集計 2 本 = 分数 1(2 行)+ 単独 1(1 行)
    expect(meta.games).toBe(1);
  });
  it("見出しの行数と data 行の数が一致し、lastKey は最後の data 行の先頭 2 トークン", () => {
    const { text, meta } = render();
    for (const s of meta.sections) expect(text).toContain(`(${s.packetPath}、${s.rows} 行)`);
    expect(meta.sections.find((s) => s.section === "8")?.lastKey).toBe("g01 48");
    expect(meta.sections.find((s) => s.section === "2")?.lastKey).toBe("aggregates.branches.total.value 値");
    expect([...meta.sections.find((s) => s.section === "A")!.lastKey].length).toBeLessThanOrEqual(60);
  });
  it("lastKey は 60 字で切る", () => {
    const request = minimalRequest();
    request.customerQuestions[0]!.text = "あ".repeat(100);
    const { meta } = render({ request });
    expect([...meta.sections.find((s) => s.section === "A")!.lastKey].length).toBe(60);
  });
  it("1 行目に符号・持ち時間・局数・線の組(S-2)、指示文はバイト列そのまま、(A) が (B) より前", () => {
    const { text } = render();
    const first = text.split("\n")[0]!;
    expect(first).toBe("対象: 〇〇さん(符号 c5)。持ち時間 180 秒の組・1 局。線の組: ahead_cp=300 centipawns");
    expect(text).toContain(INSTRUCTION.toString("utf-8").replace(/\n$/, ""));
    expect(text.indexOf("# (A) ")).toBeLessThan(text.indexOf("# (B) "));
  });
  it("集計は数ごと 1 行(aggregates.<id>.numerator / .denominator / .value)で写され、名前・母集団・分子の条件は分子の行にだけ", () => {
    const { text } = render();
    expect(text).toContain("| aggregates.side_match.attack.numerator | 分子 | 1 | 第 1 候補が攻めの手だった分かれ道のうち、実戦も攻めの手だった局面 | positions | branches / top1Side == \"attack\" / positions | - | null | false | true | null | g01 |");
    expect(text).toContain("| aggregates.side_match.attack.denominator | 分母 | 1 | - | positions | - | - | - | - | - | - | - |");
    expect(text).toContain("| aggregates.branches.total.value | 値 | 1 | 分かれ道の総数 | positions | branches / - / positions | - | null | false | true | null | g01 |");
  });
  it("集計の列は packetRef の文法(1 か所の定数)に合う", () => {
    const { text } = render();
    const rows = text.split("\n").filter((line) => line.startsWith("| aggregates."));
    expect(rows).toHaveLength(3);
    for (const row of rows) expect(AGGREGATE_REF_RE.test(row.split("|")[1]!.trim()), row).toBe(true);
  });
  it("本人の手は局ごと 1 行、候補は局面ごと 1 行", () => {
    const { text } = render();
    expect(text).toContain("g01: 48:P*4d pawn 12.5 null mid FD; 50:8g8f pawn 3 null mid C");
    expect(text).toContain("g01 48 8g8f P*4d 120 | 8g8f 120");
  });
  it("省いたもの: 読み筋の手と sfen は本文に出ない", () => {
    const { text, meta } = render();
    expect(text).not.toContain("3c3d");
    expect(text).not.toContain("lnsgkgsnl");
    expect(meta.omitted.some((line) => line.includes("pv"))).toBe(true);
  });
  it("合言葉は末尾の 1 行にだけ出る", () => {
    const { text, meta } = render();
    const lines = text.trimEnd().split("\n");
    expect(lines[lines.length - 1]).toBe(`(束はここまで。合言葉: ${meta.passphrase})`);
    expect(text.split(meta.passphrase).length - 1).toBe(1);
    expect(meta.passphrase).toBe(RUN_ID.slice(0, 8));
  });
  it("固定文は全行が data 行から除かれる(欄名の数字が抽出の証拠を汚さない)", () => {
    const { text } = render();
    const data = dataLinesOf(text, INSTRUCTION.toString("utf-8")).split("\n");
    for (const line of READING_GUIDE) expect(data, line).not.toContain(line);
    expect(READING_GUIDE.some((line) => numberTokens(line).size > 0)).toBe(true); // 欄名の数字は在る ― だから除く
  });
});

describe("決定性", () => {
  it("同じ入力で 2 回 → バイト一致。runId を変えると末尾の 1 行だけ変わる", () => {
    const a = render();
    const b = render();
    expect(a.text).toBe(b.text);
    expect(a.meta).toEqual(b.meta);
    const c = render({ runId: "xyz20260930run" });
    const la = a.text.trimEnd().split("\n");
    const lc = c.text.trimEnd().split("\n");
    expect(la.slice(0, -1)).toEqual(lc.slice(0, -1));
    expect(la[la.length - 1]).not.toBe(lc[lc.length - 1]);
  });
});

describe("抽出の証拠(数の包含)― 校正の道具はわざとずらした写しで捕まる", () => {
  it("render の本文は通る(ファイルから読み直す口でも)", () => {
    const { text } = render();
    expect(numberInclusionProblems(dataLinesOf(text, INSTRUCTION.toString("utf-8")), minimalPacket(), minimalRequest())).toEqual([]);
  });
  it("本文の 1 つの数を +1 すると、その数が挙がる", () => {
    const { text } = render();
    const bent = text.replace("| 320 | -140 |", "| 321 | -140 |");
    expect(bent).not.toBe(text);
    const problems = numberInclusionProblems(dataLinesOf(bent, INSTRUCTION.toString("utf-8")), minimalPacket(), minimalRequest());
    expect(problems).toEqual(["数「321」が本文に 1 回、packet + request には 0 回"]);
  });
  it("1 行目(線の組の値・持ち時間)も読み直しの口の検査に入る(独立監査 2026-09-30 の指摘)", () => {
    const { text } = render();
    const first = text.split("\n")[0]!;
    expect(dataLinesOf(text, INSTRUCTION.toString("utf-8")).split("\n")[0]).toBe(first);
    const bent = text.replace(first, first.replace("持ち時間 180 秒", "持ち時間 999999 秒").replace("ahead_cp=300", "ahead_cp=301"));
    expect(bent).not.toBe(text);
    expect(numberInclusionProblems(dataLinesOf(bent, INSTRUCTION.toString("utf-8")), minimalPacket(), minimalRequest()))
      .toEqual(["数「999999」が本文に 1 回、packet + request には 0 回", "数「301」が本文に 1 回、packet + request には 0 回"]);
  });
  it("data 行に無い数(見出し・固定文・指示文・合言葉)は検査に掛からない", () => {
    const { text } = render();
    const data = dataLinesOf(text, INSTRUCTION.toString("utf-8"));
    expect(data).not.toContain("## ");
    expect(data).not.toContain("合言葉");
    expect(data).not.toContain(READING_GUIDE[0]!);
  });
});

describe("止まる条件(それぞれ止まり、書かない)", () => {
  function problemsOf(fn: () => unknown): string[] {
    try {
      fn();
    } catch (err) {
      if (err instanceof SeatInputError) return [...err.problems];
      throw err;
    }
    return [];
  }
  it("packet の封が中身と合わない", () => {
    const packet = minimalPacket();
    (packet.aggregates[0] as { numerator: number }).numerator = 2;
    const problems = problemsOf(() => render({ packet }));
    expect(problems.some((p) => p.includes("packetId が中身と合わない"))).toBe(true);
  });
  it("request の持ち時間が packet と違う", () => {
    const request = minimalRequest();
    request.requestedScope.timeLimitSec = 600;
    expect(problemsOf(() => render({ request }))).toEqual(["範囲: request の持ち時間が 600 秒(packet の局は 180 秒)"]);
  });
  it("線の組が空", () => {
    const packet = minimalPacket();
    packet.provenance.thresholds = [];
    const problems = problemsOf(() => render({ packet }));
    expect(problems.length).toBeGreaterThan(0);
    expect(problems.every((p) => p.startsWith("packet: "))).toBe(true);
  });
  it("指示文の 1 バイトが違う", () => {
    const bent = Buffer.concat([INSTRUCTION, Buffer.from("x")]);
    const problems = problemsOf(() => render({ instruction: bent }));
    expect(problems.some((p) => p.includes("指示文の sha256 が固定値と違う"))).toBe(true);
  });
  it("問いの文にメールの記号", () => {
    const request = minimalRequest();
    request.customerQuestions[0]!.text = "x@y に送った";
    expect(problemsOf(() => render({ request }))).toEqual(["request.customerQuestions[0].text にメールの記号を含む"]);
  });
  it("禁止の語(語はメッセージに出ない)", () => {
    const request = minimalRequest();
    request.requestedScope.note = "山田太郎の 3 分";
    const problems = problemsOf(() => render({ request, forbid: ["山田太郎"] }));
    expect(problems).toEqual(["request.requestedScope.note に禁止の語を含む"]);
    expect(problems.join("\n")).not.toContain("山田");
  });
  it("runId が短い", () => {
    expect(problemsOf(() => render({ runId: "abc" })).some((p) => p.includes("runId"))).toBe(true);
  });
  it("識別子の検査は値の型で見る(sfen の中の / や USI は通る)", () => {
    expect(identifierProblems(minimalPacket(), "packet")).toEqual([]);
    expect(identifierProblems({ a: "/Users/x" }, "p")).toEqual(["p.a が絶対パス"]);
    expect(identifierProblems({ a: ["see https://x.example"] }, "p")).toEqual(["p.a[0] に URL を含む"]);
  });
});
