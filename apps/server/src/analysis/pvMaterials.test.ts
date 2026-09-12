import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { DEFAULT_INITIAL_SFEN } from "./moveHistory.js";
import { computePvMaterials, type PvMaterialRules, type PvMaterialsResult } from "./pvMaterials.js";

// 期待値はすべて手で数えて書いている(tsxの使い捨て確認の出力を根拠にしない)。
// 盤の段は shogiops では a=0 … i=8。先手は段が減る向きが前。

const RULES: PvMaterialRules = {
  contact: "capture_available",
  kingNeighborhood: "eight_neighbors",
  advance: "rank_delta",
  reach: "sliding_attack_count",
};

/** measured であることを確かめてから中身を取り出す(insufficient のまま読み進めない)。 */
function measured(result: PvMaterialsResult) {
  if (result.kind !== "measured") {
    throw new Error(`measured を期待したが ${result.kind} だった(usablePlies=${result.usablePlies})`);
  }
  return result;
}

describe("computePvMaterials: 門番(短い読み筋)", () => {
  // multipv 2 が lowerbound で1手だけの読み筋を返すことがある(設計書 1.4)。
  it("読み筋が1手しかなければ材料を1つも立てない", () => {
    const result = computePvMaterials(DEFAULT_INITIAL_SFEN, ["7g7f"], RULES, 4);
    expect(result.kind).toBe("insufficient");
    expect(result.usablePlies).toBe(1);
    expect(result.pvLength).toBe(1);
    if (result.kind === "insufficient") expect(result.reason).toBe("pv_too_short");
  });

  // 境目の両側を必ず書く。
  it("minPlies ちょうどの長さなら材料を立てる", () => {
    const pv = ["7g7f", "3c3d", "2g2f", "8c8d"];
    const result = computePvMaterials(DEFAULT_INITIAL_SFEN, pv, RULES, 4);
    expect(result.kind).toBe("measured");
    expect(result.usablePlies).toBe(4);
  });

  it("minPlies に1手足りなければ材料を立てない", () => {
    const pv = ["7g7f", "3c3d", "2g2f", "8c8d"];
    const result = computePvMaterials(DEFAULT_INITIAL_SFEN, pv, RULES, 5);
    expect(result.kind).toBe("insufficient");
    expect(result.usablePlies).toBe(4);
  });
});

describe("computePvMaterials: 非合法手での打ち切り", () => {
  // 読み筋はエンジンの予想にすぎないので、例外を投げずに直前までを使う(計画 1.3)。
  const pv = ["7g7f", "3c3d", "1a1b", "2g2f"]; // 3手目は先手番なのに後手の香を動かしている

  it("例外を投げず、打ち切った位置を返す", () => {
    const result = measured(computePvMaterials(DEFAULT_INITIAL_SFEN, pv, RULES, 2));
    expect(result.usablePlies).toBe(2);
    expect(result.truncatedAtPly).toBe(3);
    expect(result.pvLength).toBe(4);
  });

  it("打ち切った結果が短ければ、門番が材料を止める", () => {
    const result = computePvMaterials(DEFAULT_INITIAL_SFEN, pv, RULES, 4);
    expect(result.kind).toBe("insufficient");
    expect(result.usablePlies).toBe(2);
  });

  it("最後まで再生できたときは truncatedAtPly が null", () => {
    const result = measured(computePvMaterials(DEFAULT_INITIAL_SFEN, ["7g7f", "3c3d", "2g2f", "8c8d"], RULES, 4));
    expect(result.truncatedAtPly).toBeNull();
  });
});

describe("computePvMaterials: 駒がぶつからない読み筋(材料が null になる側)", () => {
  const pv = ["7g7f", "3c3d", "2g2f", "8c8d"];

  it("取る手・王手・成り・打つ手が無ければ、すべて null になる", () => {
    const { materials } = measured(computePvMaterials(DEFAULT_INITIAL_SFEN, pv, RULES, 4));
    expect(materials.firstCapture).toBeNull();
    expect(materials.firstCheck).toBeNull();
    expect(materials.firstPromotion).toBeNull();
    expect(materials.firstDrop).toBeNull();
    expect(materials.bishopExchangePly).toBeNull();
    expect(materials.capturedRoles.us).toEqual(new Map());
    expect(materials.capturedRoles.opponent).toEqual(new Map());
    expect(materials.kingMovePlies).toEqual({ us: [], opponent: [] });
  });
});

describe("computePvMaterials: 角交換の読み筋", () => {
  // 1. ▲7六歩 2. △3四歩 3. ▲2二角成(後手の角を取って成る) 4. △同銀(成った馬を取る)
  const pv = ["7g7f", "3c3d", "8h2b+", "3a2b"];
  // describe 本体では計算しない。ここで投げると**ファイル全体が収集に失敗し、
  // 個々のテストが1件も走らない**ため、どの材料が壊れたのか分からなくなる
  // (5.2 の変異確認で実際にこれが起きた)。
  const load = () => measured(computePvMaterials(DEFAULT_INITIAL_SFEN, pv, RULES, 4)).materials;

  it("材料1: 最初に取ったのは3手目のこちら側で、取ったのは角", () => {
    const materials = load();
    expect(materials.firstCapture).toEqual({ ply: 3, byUs: true, role: "bishop" });
  });

  it("材料3: 取った駒を駒種ごとに両者ぶん数える(成った馬は角として数える。K-1)", () => {
    const materials = load();
    expect(materials.capturedRoles.us).toEqual(new Map([["bishop", 1]]));
    expect(materials.capturedRoles.opponent).toEqual(new Map([["bishop", 1]]));
  });

  it("材料4: 打つ手が無いので、持ち駒の増減は取った駒と一致する", () => {
    const materials = load();
    expect(materials.handDelta.us).toEqual(new Map([["bishop", 1]]));
    expect(materials.handDelta.opponent).toEqual(new Map([["bishop", 1]]));
  });

  it("材料7: 最初の成りは3手目で、成ったのは角", () => {
    const materials = load();
    expect(materials.firstPromotion).toEqual({ ply: 3, byUs: true, role: "bishop" });
  });

  it("材料8: 双方が角を取り終えた4手目が角交換の成立", () => {
    const materials = load();
    expect(materials.bishopExchangePly).toBe(4);
  });

  it("材料11: 4手ともすべて前へ出ている", () => {
    const materials = load();
    expect(materials.advanceRetreat.us).toEqual({ up: 2, down: 0, side: 0 });
    expect(materials.advanceRetreat.opponent).toEqual({ up: 2, down: 0, side: 0 });
  });

  it("材料2: 2手目の後に角の道が開き、こちらに取る手が生まれる", () => {
    const materials = load();
    // ▲7六歩 △3四歩 の後、先手の角(8八)から 2二 までの筋が通る。
    expect(materials.firstContactPly).toBe(2);
  });
});

describe("computePvMaterials: 材料2 が 0 になる場合(root で既にぶつかっている)", () => {
  // 先手の飛車(5八)の真ん前に後手の歩(5七)。root の時点で先手に取る手がある。
  const sfen = "4k4/9/9/9/9/9/4p4/4R4/4K4 b - 1";
  // 5八飛が5七歩を取ると、その飛車が5筋を抑えて後手玉に王手になる。
  // したがって後手の応手は5筋から外れる手でなければ非合法(5a5b は指せない)。
  const pv = ["5h5g", "5a4b"];

  it("root で既にぶつかっていれば 0 を返す(null ではない)", () => {
    const { materials } = measured(computePvMaterials(sfen, pv, RULES, 2));
    expect(materials.firstContactPly).toBe(0);
  });

  it("0 と null を取り違えない(0 は falsy なので下流で化けやすい)", () => {
    const { materials } = measured(computePvMaterials(sfen, pv, RULES, 2));
    // `if (firstContactPly)` と書くと 0 が「起きなかった」に化ける。=== null で判定すること。
    expect(materials.firstContactPly).not.toBeNull();
    expect(materials.firstContactPly === null).toBe(false);
  });
});

describe("computePvMaterials: 材料2 の定義を切り替えると値が変わる", () => {
  // 規則が効いていることの確認(選べるようにした意味があるか)。
  const pv = ["7g7f", "3c3d", "2g2f", "8c8d"];

  it("capture_available では2手目(先手に 8八角×2二 が生まれた時点)", () => {
    const { materials } = measured(computePvMaterials(DEFAULT_INITIAL_SFEN, pv, RULES, 4));
    expect(materials.firstContactPly).toBe(2);
  });

  it("mutual_attack では1手目(▲7六歩 で角が後手の3三歩を睨んだ時点)", () => {
    const rules: PvMaterialRules = { ...RULES, contact: "mutual_attack" };
    const { materials } = measured(computePvMaterials(DEFAULT_INITIAL_SFEN, pv, rules, 4));
    expect(materials.firstContactPly).toBe(1);
  });
});

describe("computePvMaterials: 打つ手と王手", () => {
  // 玉だけの盤に先手が金を1枚持っている局面。
  const sfen = "4k4/9/9/9/9/9/9/9/4K4 b G 1";
  // 1. ▲5二金打(王手) 2. △同玉(金を取る)
  const pv = ["G*5b", "5a5b"];
  const load = () => measured(computePvMaterials(sfen, pv, RULES, 2)).materials;

  it("材料9: 打つ手を数える", () => {
    const materials = load();
    expect(materials.firstDrop).toEqual({ ply: 1, byUs: true, role: "gold" });
  });

  it("材料1: 打つ手は捕獲に数えない(最初の捕獲は2手目の相手)", () => {
    const materials = load();
    expect(materials.firstCapture).toEqual({ ply: 2, byUs: false, role: "gold" });
  });

  it("材料6: 1手目で王手がかかる", () => {
    const materials = load();
    expect(materials.firstCheck).toEqual({ ply: 1, byUs: true });
  });

  it("材料4: 打てば持ち駒は減る(材料3とは別の量)", () => {
    const materials = load();
    expect(materials.handDelta.us).toEqual(new Map([["gold", -1]]));
    expect(materials.capturedRoles.us).toEqual(new Map());
    expect(materials.handDelta.opponent).toEqual(new Map([["gold", 1]]));
  });

  it("材料10: 玉が動いた手を数える", () => {
    const materials = load();
    expect(materials.kingMovePlies).toEqual({ us: [], opponent: [2] });
  });

  it("材料11: 打つ手は前後横に数えない", () => {
    const materials = load();
    expect(materials.advanceRetreat.us).toEqual({ up: 0, down: 0, side: 0 });
    expect(materials.advanceRetreat.opponent).toEqual({ up: 1, down: 0, side: 0 });
  });
});

describe("computePvMaterials: 材料5(玉の周りの駒)", () => {
  // 先手玉5九のとなりに金5八。その金が離れる。
  const sfen = "4k4/9/9/9/9/9/9/4G4/4K4 b - 1";
  const pv = ["5h5g", "5a5b"];

  it("玉の8近傍から自分の駒が1枚減ったことを数える", () => {
    const { materials } = measured(computePvMaterials(sfen, pv, RULES, 2));
    expect(materials.kingNeighborDelta.us).toBe(-1);
    expect(materials.kingNeighborDelta.opponent).toBe(0);
  });
});

describe("computePvMaterials: 材料12(線で利く駒の利き)", () => {
  // 先手の角が9九(隅)から8八へ出る。盤上は両玉と角だけで、利きを遮る駒が無い。
  // 9九の角の利きは 8八・7七・6六・5五・4四・3三・2二・1一 の8升。
  // 8八へ出ると 7七〜1一(7升)+ 9七 + 7九 + 9九 = 10升。差は +2。
  const sfen = "4k4/9/9/9/9/9/9/9/B3K4 b - 1";
  const pv = ["9i8h", "5a5b"];

  it("角が隅から出ると利きが2升増える", () => {
    const { materials } = measured(computePvMaterials(sfen, pv, RULES, 2));
    expect(materials.slidingReachDelta.us).toBe(2);
    expect(materials.slidingReachDelta.opponent).toBe(0);
  });
});

describe("computePvMaterials: 決定的であること", () => {
  it("同じ入力を2回呼ぶと完全に同じ結果になる(状態を持っていない)", () => {
    const pv = ["7g7f", "3c3d", "8h2b+", "3a2b"];
    const first = computePvMaterials(DEFAULT_INITIAL_SFEN, pv, RULES, 4);
    const second = computePvMaterials(DEFAULT_INITIAL_SFEN, pv, RULES, 4);
    expect(first).toEqual(second);
  });
});

describe("pvMaterials.ts の依存(計画 3.1 の契約)", () => {
  // 「どの読み筋を渡されたか」だけに依存させる。関数の中で探索を起こさない。
  // 同一性の問題は、読み筋を記録に載せる側(U6-L)に閉じ込める。
  // 行頭一致(/^import .*$/gm)で書いていたが、監査が実際に仕込んで確かめたところ
  // **複数行 import と動的 import では鳴らなかった**(26件中0件失敗)。
  // 複数行 import はこのリポジトリの既定の書き方(scripts/playtest/replay.ts:21-29 等)であり、
  // **いちばん起こりやすい違反で鳴らない見張りは、緑が「守られている」に見えるぶん無いより悪い。**
  // そのため行の形ではなく、**モジュール指定子を全部拾って**判定する。
  it("エンジンを import していない", () => {
    const source = readFileSync(new URL("./pvMaterials.ts", import.meta.url), "utf8");
    const specifiers = [
      ...source.matchAll(/from\s*["']([^"']+)["']/g), // 1行・複数行の import / re-export
      ...source.matchAll(/\bimport\s*\(\s*["']([^"']+)["']\s*\)/g), // 動的 import
      ...source.matchAll(/\bimport\s+["']([^"']+)["']/g), // 副作用だけの import
    ].flatMap((match) => match[1] ?? []);

    // 指定子が1つも取れないなら、正規表現が壊れている(この試験自体が何も見ていない)。
    expect(specifiers.length).toBeGreaterThan(0);
    expect(specifiers.filter((specifier) => specifier.includes("engine/"))).toEqual([]);
  });
});
