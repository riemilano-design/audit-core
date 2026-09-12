// UsiEngine.go()/setMultiPv()/goMultiPv() の決定的な単体テスト。
// 実エンジンバイナリは使わない(usiEngine.smoke.test.tsとは別に、プロセスなしで検証する)。
//
// UsiEngineのgo()/goMultiPv()は内部で send() → waitForLine() という順で動く。
// send()は実プロセス(this.proc)が無いと例外を投げるため、send()自体をスタブ化し、
// dispatch()(readlineの"line"イベントで呼ばれる、実際はprivateだがテストからは
// ブラケットアクセスで到達可能)を直接呼んでエンジン出力を模擬する。
// これにより、プロセスを一切起動せずに「送ったコマンド」「受け取った行の解析結果」を
// 決定的に検証できる。

import { describe, expect, it, vi } from "vitest";
import { buildGoCommand, parseBestmoveLine, UsiEngine } from "./usiEngine.js";

function dispatchLine(engine: UsiEngine, line: string): void {
  // dispatch()はprivateだが、テストからの直接呼び出しのためブラケットアクセスする
  // (実プロセスを起動せずにreadlineの"line"イベントを模擬する唯一の方法)。
  (engine as unknown as { dispatch(line: string): void }).dispatch(line);
}

describe("parseBestmoveLine", () => {
  it("bestmove行からbestmove/ponderを取り出す", () => {
    expect(parseBestmoveLine(["info depth 1", "bestmove 7g7f ponder 3c3d"])).toEqual({
      bestmove: "7g7f",
      ponder: "3c3d",
    });
  });

  it("ponderが無いbestmove行も扱える", () => {
    expect(parseBestmoveLine(["bestmove 7g7f"])).toEqual({ bestmove: "7g7f", ponder: undefined });
  });

  it("bestmove行が無い場合は両方undefined", () => {
    expect(parseBestmoveLine(["info depth 1"])).toEqual({ bestmove: undefined, ponder: undefined });
  });
});

describe("UsiEngine.setMultiPv", () => {
  it("setoption name MultiPV value <N> を送信する", () => {
    const engine = new UsiEngine("dummy-path");
    const sendSpy = vi.spyOn(engine, "send").mockImplementation(() => {});

    engine.setMultiPv(3);

    expect(sendSpy).toHaveBeenCalledWith("setoption name MultiPV value 3");
  });
});

describe("UsiEngine.setThreads", () => {
  it("setoption name Threads value <N> を送信する", () => {
    const engine = new UsiEngine("dummy-path");
    const sendSpy = vi.spyOn(engine, "send").mockImplementation(() => {});

    engine.setThreads(1);

    expect(sendSpy).toHaveBeenCalledWith("setoption name Threads value 1");
  });
});

describe("buildGoCommand", () => {
  it("nodes指定時は`go nodes N`を送り、movetimeは送らない", () => {
    expect(buildGoCommand({ nodes: 4_000_000 })).toEqual({
      command: "go nodes 4000000",
      timeoutMs: 60_000,
    });
  });

  it("nodes未指定時は従来どおり`go movetime 2000`(既定)", () => {
    expect(buildGoCommand()).toEqual({ command: "go movetime 2000", timeoutMs: 12_000 });
  });

  it("movetimeMs指定時は従来どおり`go movetime N`", () => {
    expect(buildGoCommand({ movetimeMs: 500 })).toEqual({ command: "go movetime 500", timeoutMs: 10_500 });
  });

  it("nodesが0のときはmovetime扱い(既定条件のままの逃げ道)", () => {
    expect(buildGoCommand({ nodes: 0 })).toEqual({ command: "go movetime 2000", timeoutMs: 12_000 });
  });
});

describe("UsiEngine.go (8. 既存single-bestmove APIが従来どおり動く)", () => {
  it("bestmove/ponder/scoreCp(最後に観測されたscore cp)を返す", async () => {
    const engine = new UsiEngine("dummy-path");
    vi.spyOn(engine, "send").mockImplementation(() => {});

    const goPromise = engine.go({ movetimeMs: 10 });
    dispatchLine(engine, "info depth 1 score cp 10 pv 7g7f");
    dispatchLine(engine, "info depth 2 score cp 42 pv 7g7f 3c3d");
    dispatchLine(engine, "bestmove 7g7f ponder 3c3d");

    await expect(goPromise).resolves.toEqual({
      bestmove: "7g7f",
      ponder: "3c3d",
      scoreCp: 42,
      infoLines: [
        "info depth 1 score cp 10 pv 7g7f",
        "info depth 2 score cp 42 pv 7g7f 3c3d",
        "bestmove 7g7f ponder 3c3d",
      ],
    });
  });
});

describe("UsiEngine.go (nodes指定)", () => {
  it("nodes指定時は`go nodes N`を送信する(movetimeは送らない)", async () => {
    const engine = new UsiEngine("dummy-path");
    const sendSpy = vi.spyOn(engine, "send").mockImplementation(() => {});

    const goPromise = engine.go({ nodes: 20_000 });
    dispatchLine(engine, "bestmove 7g7f");
    await goPromise;

    expect(sendSpy).toHaveBeenCalledWith("go nodes 20000");
    expect(sendSpy).not.toHaveBeenCalledWith(expect.stringContaining("movetime"));
  });
});

describe("UsiEngine.goMultiPv (nodes指定)", () => {
  it("nodes指定時は`go nodes N`を送信する(movetimeは送らない)", async () => {
    const engine = new UsiEngine("dummy-path");
    const sendSpy = vi.spyOn(engine, "send").mockImplementation(() => {});

    const goPromise = engine.goMultiPv({ nodes: 20_000 });
    dispatchLine(engine, "bestmove 7g7f");
    await goPromise;

    expect(sendSpy).toHaveBeenCalledWith("go nodes 20000");
    expect(sendSpy).not.toHaveBeenCalledWith(expect.stringContaining("movetime"));
  });
});

describe("UsiEngine.goMultiPv", () => {
  it("6. 複数のmultipv行を、multipv番号昇順の決定的な順序で返す", async () => {
    const engine = new UsiEngine("dummy-path");
    vi.spyOn(engine, "send").mockImplementation(() => {});

    const goPromise = engine.goMultiPv({ movetimeMs: 10 });
    // わざと2番→1番の順で観測させ、出力側でmultipv昇順に並び替えられることを確認する。
    dispatchLine(engine, "info depth 5 multipv 2 score cp 30 pv 3c3d");
    dispatchLine(engine, "info depth 5 multipv 1 score cp 50 pv 7g7f");
    dispatchLine(engine, "bestmove 7g7f");

    const result = await goPromise;
    expect(result.lines.map((l) => l.multipv)).toEqual([1, 2]);
    expect(result.lines[0]).toEqual({
      multipv: 1,
      score: { type: "cp", value: 50 },
      pv: ["7g7f"],
      lowerbound: false,
      upperbound: false,
    });
    expect(result.lines[1]).toEqual({
      multipv: 2,
      score: { type: "cp", value: 30 },
      pv: ["3c3d"],
      lowerbound: false,
      upperbound: false,
    });
  });

  it("同じmultipv番号のinfo行が複数回来た場合、最後に観測された内容を採用する", async () => {
    const engine = new UsiEngine("dummy-path");
    vi.spyOn(engine, "send").mockImplementation(() => {});

    const goPromise = engine.goMultiPv({ movetimeMs: 10 });
    dispatchLine(engine, "info depth 1 multipv 1 score cp 5 pv 7g7f");
    dispatchLine(engine, "info depth 3 multipv 1 score cp 55 pv 7g7f 8c8d");
    dispatchLine(engine, "bestmove 7g7f");

    const result = await goPromise;
    expect(result.lines).toEqual([
      { multipv: 1, score: { type: "cp", value: 55 }, pv: ["7g7f", "8c8d"], lowerbound: false, upperbound: false },
    ]);
  });

  it("bestmove/ponderを返す(単一bestmove APIと同じ解析)", async () => {
    const engine = new UsiEngine("dummy-path");
    vi.spyOn(engine, "send").mockImplementation(() => {});

    const goPromise = engine.goMultiPv({ movetimeMs: 10 });
    dispatchLine(engine, "info multipv 1 score cp 10 pv 7g7f");
    dispatchLine(engine, "bestmove 7g7f ponder 3c3d");

    const result = await goPromise;
    expect(result.bestmove).toBe("7g7f");
    expect(result.ponder).toBe("3c3d");
  });

  it("malformedなinfo行が混ざっていても安全に無視し、bestmoveの解析には影響しない", async () => {
    const engine = new UsiEngine("dummy-path");
    vi.spyOn(engine, "send").mockImplementation(() => {});

    const goPromise = engine.goMultiPv({ movetimeMs: 10 });
    dispatchLine(engine, "info string this is a debug message with no score");
    dispatchLine(engine, "info multipv 1 score cp 10 pv 7g7f");
    dispatchLine(engine, "bestmove 7g7f");

    const result = await goPromise;
    expect(result.bestmove).toBe("7g7f");
    expect(result.lines).toEqual([
      { multipv: 1, score: { type: "cp", value: 10 }, pv: ["7g7f"], lowerbound: false, upperbound: false },
    ]);
  });

  // STEP U6-L(docs/STEP_U6-L_PLAN_2026-09-13.md 2.2)。**挙動の観測であり、要求ではない。**
  // goMultiPvは「同じmultipv番号のinfo行は最後に観測されたものを採用する」規則で
  // 組み立てる(上のテストが定める既存の挙動)。この規則は、scoreもpvも持たない
  // info行(`info string ...`等)が**後に**来た場合、それまでの読み筋と評価値を
  // 空で上書きする。上の「malformedなinfo行が混ざっていても〜」は`info string`を
  // **先に**流しているため、この上書きは起きない。順序が逆のときに何が起きるかを
  // 固定しておく。
  //
  // 【本STEPでは直さない(人間・司令塔の判断を経た決定)】
  // 直すとscoreの採用規則も変わり、candidateMoveReferenceFilter.ts:104が読む
  // multiPv[0].scoreが変わって、除外される候補手が変わる = 本番の挙動が変わる。
  // U6-Lは「本番の挙動を変えない」STEPなので、ここでは**起きることを記録するだけ**に
  // とどめ、実際に対局記録で起きるかどうかを測る(計画書 予測P6)。
  it("STEP U6-L(観測): pvを持たないinfo行が後に来ると、読み筋も評価値も空で上書きされる", async () => {
    const engine = new UsiEngine("dummy-path");
    vi.spyOn(engine, "send").mockImplementation(() => {});

    const goPromise = engine.goMultiPv({ movetimeMs: 10 });
    dispatchLine(engine, "info multipv 1 score cp 10 pv 7g7f");
    dispatchLine(engine, "info string this is a debug message with no score");
    dispatchLine(engine, "bestmove 7g7f");

    const result = await goPromise;
    // `info string`はmultipv未指定なので1として扱われ、同じ番号を上書きする。
    expect(result.lines).toEqual([
      { multipv: 1, score: undefined, pv: [], lowerbound: false, upperbound: false },
    ]);
    // bestmoveの解析には影響しない(bestmove行から別に読むため)。
    expect(result.bestmove).toBe("7g7f");
  });

  it("10. 同一の観測入力に対して常に同じ結果になる(決定的)", async () => {
    async function run(): Promise<unknown> {
      const engine = new UsiEngine("dummy-path");
      vi.spyOn(engine, "send").mockImplementation(() => {});
      const goPromise = engine.goMultiPv({ movetimeMs: 10 });
      dispatchLine(engine, "info depth 5 multipv 2 score cp 30 pv 3c3d");
      dispatchLine(engine, "info depth 5 multipv 1 score cp 50 pv 7g7f");
      dispatchLine(engine, "bestmove 7g7f");
      return goPromise;
    }

    expect(await run()).toEqual(await run());
  });
});
