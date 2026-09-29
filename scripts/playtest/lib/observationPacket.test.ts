// 束 A の試験(計画 docs/PLAN_OBSERVATION_PACKET_2026-09-30.md §5 の 1・§9 の 1)。
//
// 【この試験の要点】「通った」は証拠にならない ― **壊した packet が落ちることを校正する**(§68 の教訓)。
// だから 1 本ずつ「どこを壊したら、どの誤りが出るか」を書く。
// 【器だけを見る】facts・aggregates の中身を材料から組むのは束 B・C。ここは契約の形と封の符号だけ。
import { readFileSync, readdirSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  OBSERVATION_PACKET_CONTRACT,
  aggregateFormProblems,
  observationPacketProblems,
  OBSERVATION_PACKET_SCHEMA_VERSION,
  OBSERVATION_REQUEST_CONTRACT,
  canonicalJson,
  loadObservationPacketSchema,
  loadObservationRequestSchema,
  packetIdOf,
  packetIdProblems,
  validateObservationPacket,
  validateObservationRequest,
} from "./observationPacket.js";

/** 最小の packet(欄をすべて 1 行ずつ持つ。数は器の検査のための仮の値で、材料から来た値ではない) */
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
        // **実データの形**(2026-09-30 の独立監査 REVISE 2)。定義 114 本の要素 226 件は例外なく orderHint・piece・to の 3 つ。
        // ここに実在しない形(ply・usi)を書いていたので、schema と実データの食い違いが試験から見えなかった。
        { id: "onikoroshi", name: "鬼殺し", side: "self", reviewStatus: "draft", recognitionPattern: [{ orderHint: 1, piece: "桂", to: "77" }], src: "r1" },
      ],
    },
  };
}

function minimalAggregates() {
  return [
    {
      id: "side_match.attack",
      numerator: 1,
      denominator: 1,
      unit: "positions",
      name: "第 1 候補が攻めの手だった分かれ道のうち、実戦も攻めの手だった局面",
      population: { from: "branches", where: [{ field: "top1Side", op: "==", value: "attack" }], unit: "positions" },
      derivedFrom: ["g01"],
      src: "e1",
    },
    {
      id: "branches.total",
      value: 1,
      unit: "positions",
      name: "分かれ道の総数",
      population: { from: "branches", where: [], unit: "positions" },
      derivedFrom: ["g01"],
      src: "e1",
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
        { id: "e1", type: "engine", engineVersion: "(仮)", nodesLimit: 2000, multipv: 5, generatedAt: "2026-09-30T00:00:00Z" },
        { id: "e2", type: "engine", engineVersion: "(仮)", nodesLimit: 10000, multipv: 5 },
        { id: "m1", type: "material", path: "scripts/playtest/out/c5/pipe-3min/report/patient_report_data.json", sha256: "a".repeat(64), kind: "patient-report-data", gitHead: "0000000" },
        { id: "r1", type: "recognition", definitionsDirs: ["data/openings"], reviewStatus: "draft" },
      ],
      inputs: [{ path: "scripts/playtest/out/c5/pipe-3min/report/patient_report_data.json", sha256: "a".repeat(64), bytes: 104857 }],
    },
  };
}

function minimalRequest() {
  return {
    contract: OBSERVATION_REQUEST_CONTRACT,
    schemaVersion: "0.1",
    customerRef: "c5",
    customerQuestions: [{ id: "q1", text: "普段指さない戦型のときに何が変わるか", askedAt: "2026-09-29", via: "relayed" }],
    requestedScope: { games: 25, timeLimitSec: 180, note: "3 分切れ負け" },
  };
}

describe("Observation Packet v0.1 の契約", () => {
  it("a1 スキーマが読める(知らないキーワードで例外にならない)", () => {
    expect(() => loadObservationPacketSchema()).not.toThrow();
    expect(() => loadObservationRequestSchema()).not.toThrow();
  });

  it("a2 最小の packet が通る", () => {
    expect(validateObservationPacket(minimalPacket())).toEqual([]);
  });

  it("a3 最小の request が通る", () => {
    expect(validateObservationRequest(minimalRequest())).toEqual([]);
  });

  // ---- 校正: 壊したら落ちること(「通った」を証拠にするための対照) ----

  it("a4 必須の欄を落とすと落ちる(facts の 7 つそれぞれ)", () => {
    for (const key of ["games", "moves", "engine", "time", "branches", "collapse", "recognition"]) {
      const packet = minimalPacket() as unknown as { facts: Record<string, unknown> };
      delete packet.facts[key];
      const problems = validateObservationPacket(packet);
      expect(problems.join("\n"), `facts.${key} を落としても通った`).toContain(key);
    }
  });

  it("a5 知らない欄を足すと落ちる(additionalProperties: false)", () => {
    const packet = minimalPacket() as unknown as Record<string, unknown>;
    packet.customerName = "(実名のような欄)";
    expect(validateObservationPacket(packet).join("\n")).toContain("customerName");
  });

  it("a6 実名のような customerRef は落ちる(半角小文字の符号だけ)", () => {
    for (const bad of ["山田太郎", "Yamada", "c5 さん", "C5"]) {
      const packet = { ...minimalPacket(), customerRef: bad };
      expect(validateObservationPacket(packet).join("\n"), `customerRef=${bad} が通った`).toContain(bad);
    }
    expect(validateObservationPacket({ ...minimalPacket(), customerRef: "c5" })).toEqual([]);
  });

  it("a7 単位が表に無い語だと落ちる(局と局面を混ぜられないようにする)", () => {
    const packet = minimalPacket();
    packet.aggregates[0]!.unit = "局面" as never;
    // **誤りが「単位の欄」を名指しすること**まで見る(別の理由で落ちても緑になるのを防ぐ)
    expect(validateObservationPacket(packet).join("\n")).toMatch(/unit|局面/);
  });

  it("a8 分数と単独の数を同じ行に書くと落ちる(形の検査。誤りが行の id を名指しする)", () => {
    const packet = minimalPacket() as unknown as { aggregates: Record<string, unknown>[] };
    packet.aggregates[0]!.value = 1;
    // **schema は平らなので通る** ― 形を見るのは道具の側(oneOf にすると誤りの文が中身を隠す)
    expect(validateObservationPacket(packet)).toEqual([]);
    const problems = aggregateFormProblems(packet.aggregates);
    expect(problems.join("\n")).toContain("side_match.attack");
    expect(problems.join("\n")).toContain("同じ行に在る");
    expect(observationPacketProblems(packet).join("\n")).toContain("同じ行に在る");
  });

  it("a8b 数が無い行・分数の片方だけの行も落ちる", () => {
    const noNumber = minimalPacket() as unknown as { aggregates: Record<string, unknown>[] };
    delete noNumber.aggregates[1]!.value;
    expect(aggregateFormProblems(noNumber.aggregates).join("\n")).toContain("数が無い");
    const half = minimalPacket() as unknown as { aggregates: Record<string, unknown>[] };
    delete half.aggregates[0]!.denominator;
    expect(aggregateFormProblems(half.aggregates).join("\n")).toContain("片方だけ");
  });

  it("a9 population の where の欄名が facts に無い名前だと落ちる", () => {
    const packet = minimalPacket();
    packet.aggregates[0]!.population.where[0]!.field = "attackScore" as never;
    expect(validateObservationPacket(packet).join("\n")).toContain("attackScore");
  });

  it("a10 derivedFrom が空だと落ちる(集計は局の列を必ず持つ ― 司令塔の条件 1)", () => {
    const packet = minimalPacket();
    packet.aggregates[0]!.derivedFrom = [];
    expect(validateObservationPacket(packet).join("\n")).toContain("derivedFrom");
  });

  it("a11 src を落とすと落ちる(provenance の参照が切れる)", () => {
    const packet = minimalPacket() as unknown as { facts: { branches: Record<string, unknown>[] } };
    delete packet.facts.branches[0]!.src;
    expect(validateObservationPacket(packet).join("\n")).toContain("src");
  });

  it("a12 provenance の sha256 が 64 桁でないと落ちる(材料の差し替えを見る封)", () => {
    const packet = minimalPacket();
    packet.provenance.inputs[0]!.sha256 = "abc";
    expect(validateObservationPacket(packet).join("\n")).toContain("abc");
  });

  it("a13 駒の字が表に無い字だと落ちる(実験 2 の B2 = 駒種の取り違え)", () => {
    const packet = minimalPacket();
    packet.facts.moves[0]!.piece = "p" as never; // SFEN の字は別の語彙(この契約は STANDARD_ROLES)
    expect(validateObservationPacket(packet).join("\n")).toContain('"p"');
    const ok = minimalPacket();
    ok.facts.moves[0]!.piece = "tokin";
    ok.packetId = packetIdOf(ok.facts, ok.aggregates);
    expect(validateObservationPacket(ok)).toEqual([]);
  });

  it("a14 契約の名前と版が違う packet は落ちる(違う版は通らないのが正しい)", () => {
    expect(validateObservationPacket({ ...minimalPacket(), contract: "observation-request" }).length).toBeGreaterThan(0);
    expect(validateObservationPacket({ ...minimalPacket(), schemaVersion: "0.2" }).length).toBeGreaterThan(0);
  });

  it("a15 request に顧客の問いを入れても packet の schema では通らない(層を分ける)", () => {
    const packet = minimalPacket() as unknown as Record<string, unknown>;
    packet.customerQuestions = [{ id: "q1", text: "…" }];
    expect(validateObservationPacket(packet).join("\n")).toContain("customerQuestions");
  });
});

describe("封の符号(packetId)", () => {
  it("b1 同じ中身なら同じ符号", () => {
    expect(packetIdOf(minimalFacts(), minimalAggregates())).toBe(packetIdOf(minimalFacts(), minimalAggregates()));
  });

  it("b2 鍵の並びが違っても同じ符号(正規形にそろえる)", () => {
    const facts = minimalFacts();
    const shuffled = JSON.parse(JSON.stringify({ ...facts })) as typeof facts;
    // 1 行の鍵を逆順に積み直す(値は同じ)
    shuffled.games = facts.games.map((row) => Object.fromEntries(Object.entries(row).reverse()) as typeof row);
    expect(packetIdOf(shuffled, minimalAggregates())).toBe(packetIdOf(facts, minimalAggregates()));
  });

  it("b3 数が 1 つ変われば符号が変わる", () => {
    const facts = minimalFacts();
    facts.branches[0]!.topGapCp = 81;
    expect(packetIdOf(facts, minimalAggregates())).not.toBe(packetIdOf(minimalFacts(), minimalAggregates()));
  });

  it("b4 行の並びが変われば符号が変わる(並びは事実の一部)", () => {
    const facts = minimalFacts();
    facts.moves = [facts.moves[1]!, facts.moves[0]!];
    expect(packetIdOf(facts, minimalAggregates())).not.toBe(packetIdOf(minimalFacts(), minimalAggregates()));
  });

  it("b5 provenance は符号に入らない(generatedAt が変わっても符号は同じ)", () => {
    const one = minimalPacket();
    const other = minimalPacket();
    other.provenance.generatedAt = "2026-10-01T00:00:00Z";
    expect(other.packetId).toBe(one.packetId);
  });

  it("b6 packetIdProblems が食い違いを 1 行で言う", () => {
    expect(packetIdProblems(minimalPacket())).toEqual([]);
    const broken = { ...minimalPacket(), packetId: "0".repeat(16) };
    expect(packetIdProblems(broken)).toHaveLength(1);
    expect(packetIdProblems(broken)[0] ?? "").toContain("packetId");
  });

  it("b6b observationPacketProblems が 3 つの検査を束ねる(封の食い違いも出る)", () => {
    expect(observationPacketProblems(minimalPacket())).toEqual([]);
    const broken = { ...minimalPacket(), packetId: "0".repeat(16) };
    expect(observationPacketProblems(broken).join("\n")).toContain("packetId");
  });

  it("b3b 集計の数が 1 つ変われば符号が変わる(**aggregates 側**)", () => {
    // **独立監査が見つけた穴**(2026-09-30): b1〜b5 は facts 側の変異だけで、
    // `packetIdOf` を「facts だけを見る」に書き換えても 24 本とも緑だった。
    const aggregates = minimalAggregates();
    aggregates[0]!.numerator = 2;
    expect(packetIdOf(minimalFacts(), aggregates)).not.toBe(packetIdOf(minimalFacts(), minimalAggregates()));
    const dropped = minimalAggregates().slice(0, 1);
    expect(packetIdOf(minimalFacts(), dropped)).not.toBe(packetIdOf(minimalFacts(), minimalAggregates()));
  });

  it("b7 canonicalJson は鍵を並べ、配列の順は変えない", () => {
    expect(canonicalJson({ b: 1, a: [2, 1] })).toBe('{"a":[2,1],"b":1}');
    expect(canonicalJson(null)).toBe("null");
    expect(canonicalJson([{ b: 1, a: 2 }])).toBe('[{"a":2,"b":1}]');
  });
});

describe("schema と実データの形(束 B が写す前に食い違いを捕まえる)", () => {
  // **この試験が要る理由**(2026-09-30 の独立監査 REVISE 2): schema を書くときに
  // `recognition_pattern` の欄を実データから数えず、在りそうな名前(ply・usi・note)で書いた。
  // 実データは 226 件すべて `order_hint`・`piece`・`to` なので、**束 B が写した瞬間に全部違反**になる形だった。
  // 試験の仮の値も同じ思い込みで書いていたので、24 本のどれからも見えなかった。
  // **だから実データの鍵を読んで、schema が許す鍵と突き合わせる。**
  const DEFINITION_DIRS = ["data/openings", "data/drafts/2026-09-25-knowledge/openings"];

  /** 材料の snake_case を camelCase に直す(束 B も同じ直し方を使う) */
  function camel(key: string): string {
    return key.replace(/_([a-z])/g, (_all, letter: string) => letter.toUpperCase());
  }

  function definitionFiles(): string[] {
    const files: string[] = [];
    for (const dir of DEFINITION_DIRS) {
      const full = new URL(`../../../${dir}/`, import.meta.url);
      for (const name of readdirSync(full)) if (name.endsWith(".json")) files.push(new URL(name, full).pathname);
    }
    return files;
  }

  it("c1 定義の recognitionPattern の鍵が、schema が許す鍵と同じ", () => {
    const schema = loadObservationPacketSchema() as never as {
      properties: { facts: { properties: { recognition: { properties: { definitions: { items: { properties: Record<string, { items?: { properties: Record<string, unknown> } }> } } } } } } };
    };
    const allowed = new Set(Object.keys(schema.properties.facts.properties.recognition.properties.definitions.items.properties.recognitionPattern!.items!.properties));
    const files = definitionFiles();
    expect(files.length, "定義のファイルが読めていない").toBeGreaterThan(100);
    let elements = 0;
    for (const file of files) {
      const definition = JSON.parse(readFileSync(file, "utf-8")) as { recognition_pattern?: Record<string, unknown>[] };
      for (const element of definition.recognition_pattern ?? []) {
        elements += 1;
        for (const key of Object.keys(element)) {
          expect(allowed.has(camel(key)), `${file} の recognition_pattern に schema が許さない欄「${camel(key)}」(許すのは ${[...allowed].join("・")})`).toBe(true);
        }
      }
    }
    expect(elements, "recognition_pattern の要素を 1 つも読めていない").toBeGreaterThan(200);
  });

  it("c2 定義の上位の欄も、schema が許す欄に収まる(写せない欄が在れば落ちる)", () => {
    const schema = loadObservationPacketSchema() as never as {
      properties: { facts: { properties: { recognition: { properties: { definitions: { items: { properties: Record<string, unknown> } } } } } } };
    };
    const allowed = new Set(Object.keys(schema.properties.facts.properties.recognition.properties.definitions.items.properties));
    // **写さないと決めた欄**(scenario・source)は許す側に無くてよい ― ここに名前を書いて、決めたことを残す
    const notCopied = new Set(["scenario", "source"]);
    for (const file of definitionFiles()) {
      const definition = JSON.parse(readFileSync(file, "utf-8")) as Record<string, unknown>;
      for (const key of Object.keys(definition)) {
        const camelKey = camel(key);
        expect(allowed.has(camelKey) || notCopied.has(key), `${file} の欄「${camelKey}」が schema にも「写さない」の表にも無い`).toBe(true);
      }
    }
  });
});
