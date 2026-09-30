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
import { KNOWN_HYPOTHESIS_SCHEMA_VERSIONS } from "./schemaVersions.js";
import { H10_NON_PROSE_FIELDS, H10_PROSE_FIELDS, loadHypothesisSchema, loadObsRegistry, namesInText, recognitionNameCorpus, recognizedNames, stringsAtField, validateHypothesisLine, type CheckResult } from "./hypothesis.js";

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

// ==================== H-10: 名前がその顧客の局で認識されたものか(束 V-b) ====================
//
// 【材料の数をそろえない】定義 5 件・行 3 件・認識された名前 2 件と**全部違う件数**にする ―
// そろえると「別の列を返す変異」「件数を返す変異」が緑で通る(2026-09-29〜30 に 5 回踏んだ型)。
// 【最長一致を測るための組は 2 通り要る】(2026-09-30 実測: 1 通りでは変異が黙った)
// (a) **同じ位置で 2 語当たる**組 = `中飛車`(認識されていない)と `中飛車左穴熊`(認識されている)。
//     短い方を先に置く ― 「最初に当たった語を採る」変異はここで赤くなる。
//     最初は後方一致の組(`中飛車` ⊂ `ゴキゲン中飛車`)だけで測ろうとしたが、
//     `中飛車` は 0 文字目に当たらないので**最長一致の行を通っていなかった**(変異が緑で通った)。
// (b) **後方に入っている**組 = `中飛車` ⊂ `ゴキゲン中飛車`。
//     当たった語の長さだけ進む(`index += longest.length`)ことを固定する ―
//     1 文字ずつ進める変異なら、4 文字目の `中飛車` で苦情が出る。
function recognitionPacket(): Record<string, unknown> {
  return {
    facts: {
      recognition: {
        definitions: [
          { id: "nakabisha", name: "中飛車", nameKana: "なかびしゃ" },
          { id: "gokigen", name: "ゴキゲン中飛車", nameKana: "ごきげんなかびしゃ" },
          { id: "nakabisha_hidariana", name: "中飛車左穴熊", nameKana: "なかびしゃひだりあなぐま" },
          { id: "yagura", name: "矢倉", nameKana: "やぐら" },
          { id: "hirame", name: "平目", nameKana: "ひらめ" },
          // **同名の定義**(実物に 6 件あった)。名前から定義は 1 対 1 でない
          { id: "yagura2", name: "矢倉", nameKana: "やぐら" },
        ],
        rows: [
          { gameId: "g01", names: ["ゴキゲン中飛車"] },
          { gameId: "g02", names: ["矢倉", "中飛車左穴熊"] },
          { gameId: "g03", names: [] },
          { gameId: "g04", names: [] },
        ],
      },
    },
  };
}

function h10(line: unknown, packet?: unknown): { ok: boolean; messages: string[]; skipped?: boolean } {
  const results = validateHypothesisLine(line, {
    today: "2026-09-30",
    registry: new Set<string>(),
    packet,
  });
  return results.find((result) => result.check === "H-10")!;
}

describe("H-10 名前はその顧客の局で認識されたものか", () => {
  it("h1 名前の表と、この顧客の局で認識された名前を packet から作る", () => {
    const packet = recognitionPacket();
    const corpus = recognitionNameCorpus(packet);
    // 6 件の定義から 語 = name 5 種 + かな 5 種 + id 6 種 = 16(同名の 矢倉 は 1 つの語に合流)
    expect(corpus.size).toBe(16);
    expect([...(corpus.get("矢倉") ?? [])]).toEqual(["矢倉"]);
    expect([...(corpus.get("やぐら") ?? [])]).toEqual(["矢倉"]);
    const recognized = recognizedNames(packet);
    expect([...recognized].sort()).toEqual(["ゴキゲン中飛車", "中飛車左穴熊", "矢倉"]);
    // **件数をそろえない**(定義 6・行 4・認識された名前 3・語 16 と全部違う値にしてある。
    // そろえる直しが入ったら赤くする ― 件数を返す変異が緑で通らないため)
    expect(recognized.size).toBe(3);
    for (const other of [corpus.size, 4, 6]) expect(recognized.size).not.toBe(other);
  });

  it("h2 認識された名前は通り、認識されていない名前は落ちる(欄と語を出す)", () => {
    const packet = recognitionPacket();
    expect(h10({ statement: "矢倉の形でした。という読みです。" }, packet).ok).toBe(true);
    const bad = h10({ statement: "平目の形でした。という読みです。" }, packet);
    expect(bad.ok).toBe(false);
    expect(bad.messages).toHaveLength(1);
    expect(bad.messages[0]!).toContain("平目");
    expect(bad.messages[0]!).toContain("statement");
  });

  it("h3 各位置で最長一致(同じ位置で 2 語当たるとき長い方を採る)", () => {
    const packet = recognitionPacket();
    const corpus = recognitionNameCorpus(packet);
    // (a) **同じ 0 文字目に `中飛車` と `中飛車左穴熊` の両方が当たる。**長い方は認識されている
    expect(namesInText("中飛車左穴熊", corpus)).toEqual([{ at: 0, word: "中飛車左穴熊" }]);
    expect(h10({ statement: "中飛車左穴熊でした。という読みです。" }, packet).messages).toEqual([]);
    // (b) 後方に入っている短い名前を**別に数えない**(当たった語の長さだけ進む)
    expect(namesInText("ゴキゲン中飛車", corpus)).toEqual([{ at: 0, word: "ゴキゲン中飛車" }]);
    expect(h10({ statement: "ゴキゲン中飛車でした。という読みです。" }, packet).messages).toEqual([]);
    // 短い方を単独で書けば、今までどおり落ちる(緩めていないことの裏)
    expect(h10({ statement: "中飛車でした。という読みです。" }, packet).ok).toBe(false);
  });

  it("h4 かな と id でも当たる(名前の表は 3 つの欄の合併)", () => {
    const packet = recognitionPacket();
    expect(h10({ statement: "ひらめの形でした。" }, packet).ok).toBe(false);
    expect(h10({ statement: "hirame の形でした。" }, packet).ok).toBe(false);
    // 認識された名前の かな は通る(名前に写して判定している)
    expect(h10({ statement: "やぐらの形でした。" }, packet).ok).toBe(true);
  });

  it("h5 packet が無い・認識の定義が無いときは skip(緑にしない)", () => {
    const noPacket = h10({ statement: "平目の形でした。" });
    expect(noPacket.skipped).toBe(true);
    expect(noPacket.messages[0]!).toContain("未照合");
    const noDefinitions = h10({ statement: "平目の形でした。" }, { facts: { recognition: { definitions: [], rows: [] } } });
    expect(noDefinitions.skipped).toBe(true);
    expect(noDefinitions.messages[0]!).toContain("認識の定義が無い");
  });

  it("h6 見る欄は散文だけ(内部の欄・機械の欄の名前で落とさない)", () => {
    const packet = recognitionPacket();
    // 内部の自由分析は顧客の文へ流れない(規則 8 の (3))ので見ない
    expect(h10({ internal: { reasoning: "平目のように見える" } }, packet).ok).toBe(true);
    // 席の自己申告も証拠にしない(見ない)
    expect(h10({ internal: { reasoning: "あ", namesOutsideVocabulary: ["平目"] } }, packet).ok).toBe(true);
    // 反証の項目の文と行動の文は見る
    expect(h10({ counterEvidence: { items: [{ text: "平目の形でした。" }] } }, packet).ok).toBe(false);
    expect(h10({ actionCandidate: { text: "平目を試す" } }, packet).ok).toBe(false);
  });

  it("h7 欄の道をたどって文字列を集める(列の添字つきで場所を言う)", () => {
    const line = { counterEvidence: { items: [{ text: "あ" }, { text: "い" }, { noText: 1 }] } };
    expect(stringsAtField(line, "counterEvidence.items[].text")).toEqual([
      { at: "counterEvidence.items[0].text", text: "あ" },
      { at: "counterEvidence.items[1].text", text: "い" },
    ]);
    expect(stringsAtField({}, "statement")).toEqual([]);
    // 型が違っても落ちない(文字列でなければ集めない)
    expect(stringsAtField({ statement: 3 }, "statement")).toEqual([]);
  });

  it("h9 1 語が 2 つの名前に対応するとき、どちらかが認識されていれば通す", () => {
    // **どの定義かは決めない**のが H-10 の建て方(実測で同名の定義が 6 件あった)。
    // かな が同じで名前が違う定義が来ると、その かな は 2 つの名前を指す ―
    // **片方が認識されていれば、席が認識に無い名前を使ったとは言えない**(緩い側が正しい)。
    // 【実物の今の材料では 0 件】(2026-09-30 実測: 1 語が複数の名前に対応する語は 0)。
    // だから**ここだけの材料**で測る ― 実物が変わったとき(かなの重なる定義が入ったとき)に効く。
    const packet = {
      facts: {
        recognition: {
          definitions: [
            { id: "yagura", name: "矢倉", nameKana: "やぐら" },
            { id: "yagura_gakoi", name: "矢倉囲い", nameKana: "やぐら" },
          ],
          rows: [{ gameId: "g01", names: ["矢倉"] }],
        },
      },
    };
    // かな は {矢倉, 矢倉囲い} を指し、矢倉 だけが認識されている → 通す
    expect(h10({ statement: "やぐらの形でした。" }, packet).ok).toBe(true);
    // どちらも認識されていない packet なら落ちる(緩めきっていないことの裏)
    const other = {
      facts: {
        recognition: {
          definitions: packet.facts.recognition.definitions,
          rows: [{ gameId: "g01", names: ["中飛車"] }],
        },
      },
    };
    expect(h10({ statement: "やぐらの形でした。" }, other).ok).toBe(false);
  });

  it("h8 schema の文字列の欄が 2 つの表で全部分類されている(黙って見ない欄を増やせない)", () => {
    const leaves = new Set<string>();
    const walk = (node: unknown, path: string): void => {
      if (node === null || typeof node !== "object") return;
      const record = node as Record<string, unknown>;
      if (record.type === "string" && path !== "") leaves.add(path);
      const properties = record.properties as Record<string, unknown> | undefined;
      for (const [key, value] of Object.entries(properties ?? {})) walk(value, path === "" ? key : `${path}.${key}`);
      if (record.items !== undefined) walk(record.items, `${path}[]`);
      for (const key of ["oneOf", "anyOf", "allOf"] as const) {
        for (const branch of (record[key] as unknown[]) ?? []) walk(branch, path);
      }
    };
    for (const version of KNOWN_HYPOTHESIS_SCHEMA_VERSIONS) walk(loadHypothesisSchema(version), "");
    const classified = new Set<string>([...H10_PROSE_FIELDS, ...H10_NON_PROSE_FIELDS]);
    const unclassified = [...leaves].filter((leaf) => !classified.has(leaf)).sort();
    expect(unclassified, "schema に文字列の欄が増えている ― 散文か機械の欄かを表に足すこと").toEqual([]);
    // 表に在って schema に無い欄(消えた欄)も見る
    const gone = [...classified].filter((field) => !leaves.has(field)).sort();
    expect(gone, "表に在るのに schema に無い欄(消えた欄は表からも消す)").toEqual([]);
    // 分類が空でないこと(両方の表を消す変異を赤にする)
    expect(leaves.size).toBeGreaterThan(20);
  });
});
