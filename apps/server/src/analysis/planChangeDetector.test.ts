import { describe, expect, it } from "vitest";
import { detectPlanChange, type PlanSnapshot } from "./planChangeDetector.js";

describe("detectPlanChange", () => {
  it("previous snapshotが無い場合はfalse", () => {
    expect(detectPlanChange(undefined, "7g7f", "mino_honmino", ["7g7f"])).toBe(false);
  });

  it("targetShapeIdが前回と異なる場合はfalse(目標形変更・フォールバック変化を崩れと混同しない)", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["7i8h"] };
    expect(detectPlanChange(previous, "1g1f", "mino_takamino", [])).toBe(false);
  });

  it("提案手をそのまま指した(候補が1件のみ)場合、除外後の残存候補が0件になりfalse", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["7i8h"] };
    // プレイした手自体は現在局面にはもう存在しない(駒が既に動いた)ことが通常だが、
    // 除外によって比較対象自体が無くなるため、legalMovesの中身に関わらずfalseになる。
    expect(detectPlanChange(previous, "7i8h", "mino_honmino", [])).toBe(false);
  });

  // 【兄弟候補の除外(既知課題の修正、人間承認済み)】
  // pathPlanner.tsは1回のPathPlanResultで常に同じtargetSquare(移動先マス)を
  // 共有するcandidateMovesを返す。ユーザーがそのうち1つを実際に指すと、
  // targetSquareが自分の駒で埋まり、残りの兄弟候補(同じtargetSquareを持つ候補)は
  // 相手の着手と無関係に非合法化される。これは相手による計画崩壊ではなく、
  // 計画を正常に実行した結果であるため、falseと判定する。
  it("複数候補のうち1つを指した場合、同じ移動先マスを持つ兄弟候補も除外され、残存候補が無くfalse", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["6g7h", "8g7h"] };
    // 8g7hは6g7hと同じ移動先マス(7h)を持つ兄弟候補のため、legalMovesの中身に
    // 関わらず除外される(実際にはユーザー自身の着手で7hが埋まり非合法化される)。
    expect(detectPlanChange(previous, "6g7h", "mino_honmino", ["1f1e"])).toBe(false);
  });

  it("異なる移動先マスを持つ候補は兄弟候補として除外されない(残りが合法ならfalse)", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["6g7h", "8g8h"] };
    // 8g8hは6g7hと異なる移動先マス(8h)を持つため、除外されず比較対象に残る。
    // 現在も合法手に含まれているためfalse。
    expect(detectPlanChange(previous, "6g7h", "mino_honmino", ["8g8h"])).toBe(false);
  });

  it("異なる移動先マスを持つ候補が現在すべて非合法な場合は、引き続きtrueになる(兄弟候補除外の副作用で見逃さない)", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["6g7h", "8g8h"] };
    // 8g8hは兄弟候補ではないため除外されないが、現在の合法手には含まれていない。
    expect(detectPlanChange(previous, "6g7h", "mino_honmino", ["1f1e"])).toBe(true);
  });

  it("ユーザーが提案手以外を指し、残存候補がすべて現在非合法な場合はtrue", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["7i8h"] };
    expect(detectPlanChange(previous, "1g1f", "mino_honmino", ["1f1e"])).toBe(true);
  });

  it("ユーザーが提案手以外を指し、残存候補が現在も合法な場合はfalse", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["7i8h"] };
    expect(detectPlanChange(previous, "1g1f", "mino_honmino", ["7i8h", "1f1e"])).toBe(false);
  });

  it("playedMoveUsiのパースに失敗する場合、兄弟候補としての除外は行わない(安全側)", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["6g7h", "8g7h"] };
    // "invalid"はUSIとしてパースできないため、isSiblingCandidateはfalseを返す
    // (誤って除外せず、remainingに残す。falseに倒すよりtrue側に残す方針)。
    // playedMoveUsi自体との完全一致でも除外されないため、両方の候補が
    // remainingに残り、いずれも現在の合法手に含まれていなければtrueになる。
    expect(detectPlanChange(previous, "invalid", "mino_honmino", ["1f1e"])).toBe(true);
  });

  it("候補側(USI)のパースに失敗する場合も、兄弟候補としての除外は行わない(安全側)", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["invalid", "8g7h"] };
    // "invalid"はplayedMoveUsi("6g7h")と完全一致もしないため除外されず、
    // 現在の合法手にも含まれていないためtrueになる
    // ("8g7h"は6g7hの兄弟候補として正しく除外される)。
    expect(detectPlanChange(previous, "6g7h", "mino_honmino", ["1f1e"])).toBe(true);
  });

  it("ドロップ手にも移動先マス(to)比較が適用される(兄弟候補として除外される)", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["P*5e"] };
    // "5e5d"(通常手、移動先5e...ではなく5d)ではなく、同じ移動先(5e)を持つ
    // 別のドロップ候補との組み合わせで確認する。
    const previousWithSiblingDrop: PlanSnapshot = {
      targetShapeId: "mino_honmino",
      candidateMoveUsis: ["P*5e", "S*5e"],
    };
    // P*5eを指した後、同じ5eへのドロップであるS*5eも兄弟候補として除外される。
    expect(detectPlanChange(previousWithSiblingDrop, "P*5e", "mino_honmino", ["1f1e"])).toBe(false);
    // 参考: 単独のドロップ候補をそのまま指した場合は、従来通り完全一致除外でfalse。
    expect(detectPlanChange(previous, "P*5e", "mino_honmino", [])).toBe(false);
  });

  // 【Phase6 Unit1で追加した判定基準(移動元が同じ場合)】
  // routePlanner.tsは「経路を塞ぐ自駒をどかす準備手」を候補にすることがあり、
  // それらは同じ駒(同じ移動元)を別々の移動先へ動かす候補の集まりになる。
  // ユーザーがそのうち1つを指すと、その駒は移動元から居なくなるため残りは
  // 相手の着手と無関係に非合法化する(計画を実行した結果であり、崩れではない)。
  it("同じ移動元マスを持つ候補(準備手の兄弟)は、1つを指すと残りも除外されfalseになる", () => {
    const previous: PlanSnapshot = {
      targetShapeId: "mino_takamino",
      // 7gの歩をどかす準備手が複数あった、という想定(移動先は異なる)。
      candidateMoveUsis: ["7g7f", "7g6f"],
    };
    // 7g7fを指した後、7g6fは移動元(7g)が同じ兄弟候補として除外されるため、
    // 残存候補が無くなりfalse(相手のせいで崩れた、とは判定しない)。
    expect(detectPlanChange(previous, "7g7f", "mino_takamino", ["1g1f"])).toBe(false);
  });

  it("移動元も移動先も異なる候補は兄弟候補として除外しない(従来の判定を維持する)", () => {
    const previous: PlanSnapshot = {
      targetShapeId: "mino_honmino",
      candidateMoveUsis: ["7i7h", "5i6h"],
    };
    // 7i7hを指した後も5i6hは別の駒・別の移動先なので残存する。
    // 残存候補が合法なら従来通りfalse。
    expect(detectPlanChange(previous, "7i7h", "mino_honmino", ["5i6h"])).toBe(false);
    // 残存候補が非合法になっていればtrue(相手の手による崩れの検知)。
    expect(detectPlanChange(previous, "7i7h", "mino_honmino", ["1g1f"])).toBe(true);
  });
});
