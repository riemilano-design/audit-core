// STEP D3 の試験(docs/STEP_D3_PLAN_2026-09-14.md 4.1・8.1)。B・B2 の決め方を、手で作った局面と手で導いた期待値で見る。
// **期待値は、実装を書く前・試験を回す前に計画書 8.1 に手で書いたもの。** 出た手を期待値に置き換えない(規則 11.1)。
// **全部の固定例で、手と段の両方を比べる**(計画 8.3 の 3。手だけだと段のずれ V-9 を見逃す)。
// エンジンは呼ばない(B の関数は engine を受け取らない。F-B16 でソースを照合する)。

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { getLegalMoves } from "../../../apps/server/src/rules/legalMoves.js";
import { pickByBeginnerProfile } from "./beginnerProfile.js";

const SOURCE_PATH = join(dirname(fileURLToPath(import.meta.url)), "beginnerProfile.ts");

describe("pickByBeginnerProfile(B の決め方。計画 2.2)", () => {
  it("F-B1 5-i: 先手の香 5g が後手の歩 5c をただで取れる(5c に後手の利きが無い)→ 5g5c(不成が先)", () => {
    expect(pickByBeginnerProfile("8k/9/4p4/9/9/9/4L4/9/K8 b - 1", "B")).toEqual({ move: "5g5c", tier: "5-i" });
  });

  it("F-B2 5-i を飛ばす: 取れる 5c には後手の金 5b の利きがある。帯・金銀・飛角なし、進められる歩は端の 1g だけ → 端を進める(5-v に落とさない)", () => {
    expect(pickByBeginnerProfile("8k/4g4/4p4/9/9/9/4L3P/9/K8 b - 1", "B")).toEqual({ move: "1g1f", tier: "5-iv-b" });
  });

  it("F-B3 5-i が 5-ii より先: 金 5f が香 5a に当たられている(帯)が、別の駒の香 1g が歩 1c をただで取れる → 1g1c", () => {
    expect(pickByBeginnerProfile("4l3k/9/8p/9/9/4G4/8L/9/K8 b - 1", "B")).toEqual({ move: "1g1c", tier: "5-i" });
  });

  it("F-B4 5-ii: 桂 5e が香 5a に当たられている。行き先 4c は歩 4b の利き、6c は利き無し → 5e6c(不成が先)", () => {
    expect(pickByBeginnerProfile("4l3k/5p3/9/9/4N4/9/9/9/8K b - 1", "B")).toEqual({ move: "5e6c", tier: "5-ii" });
  });

  it("F-B4b 5-ii の先頭の駒: 桂 7e・3e がそれぞれ香 7a・3a に当たられている。同じ駒種は筋の大きい順で先頭は 7e。8c は歩 8b の利き、6c は利き無し → 7e6c(末尾の 3e なら 3e2c)", () => {
    expect(pickByBeginnerProfile("2l1k1l2/1p3p3/9/9/2N3N2/9/9/9/4K4 b - 1", "B")).toEqual({ move: "7e6c", tier: "5-ii" });
  });

  it("F-B5 5-ii を飛ばす: 桂 5e の行き先 4c・6c がどちらも歩の利き。進められる歩は端の 9g だけ → 9g9f", () => {
    expect(pickByBeginnerProfile("4l3k/3p1p3/9/9/4N4/9/P8/9/8K b - 1", "B")).toEqual({ move: "9g9f", tier: "5-iv-b" });
  });

  it("F-B6 5-iii: 玉 5i の隣でない金 5g を、隣の 5h へ寄せる(金の行き先で玉の隣は 5h だけ)", () => {
    expect(pickByBeginnerProfile("8k/9/9/9/9/9/4G3P/9/4K4 b - 1", "B")).toEqual({ move: "5g5h", tier: "5-iii" });
  });

  it("F-B6b 5-iii に成銀を含めない: 成銀 5g(玉 5i の隣でない)は 5h(玉の隣)へ動けるが、成銀は金銀に数えない → 端の歩 1g", () => {
    expect(pickByBeginnerProfile("8k/9/9/9/9/9/4+S3P/9/4K4 b - 1", "B")).toEqual({ move: "1g1f", tier: "5-iv-b" });
  });

  it("F-B7 5-iii を使わない: 銀 5h はすでに玉 5i の隣(隣の 4i・6i へ動けても、移動元が隣なので寄せない)→ 歩 1g", () => {
    expect(pickByBeginnerProfile("8k/9/9/9/9/9/8P/4S4/4K4 b - 1", "B")).toEqual({ move: "1g1f", tier: "5-iv-b" });
  });

  it("F-B8 5-iv-a: 飛車 2e の敵陣側で最初の駒は歩 2d、2c は空き → 2d2c(不成を選ぶ)", () => {
    expect(pickByBeginnerProfile("8k/9/9/7P1/7R1/9/9/9/4K4 b - 1", "B")).toEqual({ move: "2d2c", tier: "5-iv-a" });
  });

  it("F-B8d 飛車を先、角を後: 飛車 2h の前の歩 2g も角 8h の前の歩 8g も進められる → 飛車の歩 2g2f(角を先なら 8g8f)", () => {
    expect(pickByBeginnerProfile("4k4/9/9/9/9/9/1P5P1/1B5R1/4K4 b - 1", "B")).toEqual({ move: "2g2f", tier: "5-iv-a" });
  });

  it("F-B8e 飛車 2 枚(8.8 の A2): 飛車 8h・2h の前の歩 8g・2g がどちらも進められる → 筋の数字が小さい 2h の歩 2g2f(大きい方からなら 8g8f)", () => {
    expect(pickByBeginnerProfile("8k/9/9/9/9/9/1P5P1/1R5R1/4K4 b - 1", "B")).toEqual({ move: "2g2f", tier: "5-iv-a" });
  });

  it("F-B8b 注記 2: 飛車 2h の前の歩 2g は銀 2f で塞がれて進めない → 角 8h の前の歩 8g へ落ちる", () => {
    expect(pickByBeginnerProfile("4k4/9/9/9/9/7S1/1P5P1/1B5R1/4K4 b - 1", "B")).toEqual({ move: "8g8f", tier: "5-iv-a" });
  });

  it("F-B8c 注記 3: 飛車 2h の前で最初に当たる駒は銀 2g(歩ではない)→ 飛車に対象なし、角なし → 5-iv-b の歩 2f", () => {
    expect(pickByBeginnerProfile("8k/9/9/9/9/7P1/7S1/7R1/4K4 b - 1", "B")).toEqual({ move: "2f2e", tier: "5-iv-b" });
  });

  it("F-B9 5-iv-b: 飛車 2h の前は空きで対象なし、角なし、歩は 7g だけ → 7g7f", () => {
    expect(pickByBeginnerProfile("8k/9/9/9/9/9/2P6/7R1/4K4 b - 1", "B")).toEqual({ move: "7g7f", tier: "5-iv-b" });
  });

  it("F-B9b 注記 4 (i): 進められる歩 7g・4g・1g。端の 1g を除き、飛車の筋 2 に近い 4g(距離 2)", () => {
    expect(pickByBeginnerProfile("8k/9/9/9/9/9/2P2P2P/7R1/4K4 b - 1", "B")).toEqual({ move: "4g4f", tier: "5-iv-b" });
  });

  it("F-B9c 注記 4 (ii): 飛車 5h。端の 1g を除き、6g と 4g が同じ距離 1 → 筋の数字が小さい 4g", () => {
    expect(pickByBeginnerProfile("8k/9/9/9/9/9/3P1P2P/4R4/4K4 b - 1", "B")).toEqual({ move: "4g4f", tier: "5-iv-b" });
  });

  it("F-B9d 注記 4 (iii): 飛車が無い → 2 筋で代える。6g(距離 4)より 3g(距離 1)", () => {
    expect(pickByBeginnerProfile("8k/9/9/9/9/9/3P2P2/9/4K4 b - 1", "B")).toEqual({ move: "3g3f", tier: "5-iv-b" });
  });

  it("F-B9e 注記 4 (iii): 飛車が 8h と 2h の 2 枚 → 筋の数字が小さい 2 筋。7g(距離 5)より 3g(距離 1)", () => {
    expect(pickByBeginnerProfile("8k/9/9/9/9/9/2P3P2/1R5R1/4K4 b - 1", "B")).toEqual({ move: "3g3f", tier: "5-iv-b" });
  });

  it("F-B10 5-v: 先手は玉 9i だけで、後手の金 8g の利きで 8h・9h に行けない。合法手は 9i8i の 1 手だけ", () => {
    const sfen = "8k/9/9/9/9/9/1g7/9/K8 b - 1";
    expect(getLegalMoves(sfen)).toEqual(["9i8i"]);
    expect(pickByBeginnerProfile(sfen, "B")).toEqual({ move: "9i8i", tier: "5-v" });
  });

  it("F-B12 決定的: 同じ局面(F-B3)を 2 回渡すと、同じ手・同じ段", () => {
    const sfen = "4l3k/9/8p/9/9/4G4/8L/9/K8 b - 1";
    const first = pickByBeginnerProfile(sfen, "B");
    const second = pickByBeginnerProfile(sfen, "B");
    expect(first).toEqual({ move: "1g1c", tier: "5-i" });
    expect(second).toEqual(first);
  });
});

describe("pickByBeginnerProfile(B2 = B′。計画 2.3)", () => {
  it("F-B11 F-B6 の局面でも 5-iii(金 5g5h)を使わず、歩 1g を進める", () => {
    expect(pickByBeginnerProfile("8k/9/9/9/9/9/4G3P/9/4K4 b - 1", "B2")).toEqual({ move: "1g1f", tier: "5-iv-b" });
  });
});

/**
 * モジュール指定子を全部拾う(`from "…"`・`import("…")`・副作用の `import "…"`・`require("…")`)。
 * **行頭一致にしない**: `/^import .*$/gm` は複数行の import と動的 import を拾えない(U6-M の監査で判明)。
 */
function moduleSpecifiersOf(source: string): string[] {
  const patterns = [
    /\bfrom\s*["']([^"']+)["']/g,
    /\bimport\s*\(\s*["']([^"']+)["']\s*\)/g,
    /\bimport\s*["']([^"']+)["']/g,
    /\brequire\s*\(\s*["']([^"']+)["']\s*\)/g,
  ];
  return patterns.flatMap((pattern) => [...source.matchAll(pattern)].map((match) => match[1] ?? ""));
}

/**
 * B が読んでよいモジュールの**許す一覧**(計画 8.8 の A3)。shogiops・rules/・analysis/pieceThreatDetector.js だけ。
 * 禁止の一覧だと、一覧に書き忘れた経路(game/gameSession.js・./players.js など)が通ってしまう(f2 の監査)。
 */
function isAllowedSpecifier(specifier: string): boolean {
  return (
    specifier.startsWith("shogiops/") ||
    specifier.startsWith("../../../apps/server/src/rules/") ||
    specifier === "../../../apps/server/src/analysis/pieceThreatDetector.js"
  );
}

describe("F-B16 ソース照合(計画 8.4 の決定 12・13、8.8 の A3。一方向の見張り ― P-32)", () => {
  it("照合の関数は、複数行の import・動的 import・副作用の import をどれも拾う(先に校正する)", () => {
    const multiLine = 'import {\n  PrioritizedEngine,\n  type HighPriorityEngine,\n} from "../../../apps/server/src/engine/prioritizedEngine.js";\n';
    const dynamic = 'const loaded = await import("../../../apps/server/src/api/stateResponse.js");\n';
    const sideEffect = 'import "../../../apps/server/src/engine/usiEngine.js";\n';
    expect(moduleSpecifiersOf(multiLine)).toEqual(["../../../apps/server/src/engine/prioritizedEngine.js"]);
    expect(moduleSpecifiersOf(dynamic)).toEqual(["../../../apps/server/src/api/stateResponse.js"]);
    expect(moduleSpecifiersOf(sideEffect)).toEqual(["../../../apps/server/src/engine/usiEngine.js"]);
    for (const specifier of [...moduleSpecifiersOf(multiLine), ...moduleSpecifiersOf(dynamic), ...moduleSpecifiersOf(sideEffect)]) {
      expect(isAllowedSpecifier(specifier)).toBe(false);
    }
  });

  it("許す一覧は、許すものを通し、一覧の外(game/gameSession.js・./players.js・似た名前)を通さない(先に校正する)", () => {
    expect(isAllowedSpecifier("shogiops/util")).toBe(true);
    expect(isAllowedSpecifier("../../../apps/server/src/rules/legalMoves.js")).toBe(true);
    expect(isAllowedSpecifier("../../../apps/server/src/analysis/pieceThreatDetector.js")).toBe(true);
    expect(isAllowedSpecifier("../../../apps/server/src/game/gameSession.js")).toBe(false);
    expect(isAllowedSpecifier("./players.js")).toBe(false);
    expect(isAllowedSpecifier("../../../apps/server/src/analysis/pieceThreatExplanation.js")).toBe(false);
  });

  it("lib/beginnerProfile.ts のモジュール指定子に、許す一覧の外のものが 0 件", () => {
    const specifiers = moduleSpecifiersOf(readFileSync(SOURCE_PATH, "utf-8"));
    // 1 本も拾えていなければ照合は空振りである(0 件は「無い」ではなく「見ていない」)。
    expect(specifiers.length).toBeGreaterThan(0);
    expect(specifiers.filter((specifier) => !isAllowedSpecifier(specifier))).toEqual([]);
  });
});
