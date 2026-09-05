import { describe, expect, it, vi } from "vitest";
import { PrioritizedEngine } from "./prioritizedEngine.js";
import type { GoResult, MultiPvGoResult, UsiEngine } from "./usiEngine.js";

function deferred<T>(): { promise: Promise<T>; resolve: (value: T) => void } {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}

const GO_RESULT: GoResult = { bestmove: "7g7f", ponder: undefined, scoreCp: undefined, infoLines: [] };
const MULTIPV_RESULT: MultiPvGoResult = { bestmove: "7g7f", ponder: undefined, lines: [], infoLines: [] };

/** テスト用のモックUsiEngine。go/goMultiPvは呼び出しごとに新しいdeferred Promiseを返す
 * (テスト側でresolveタイミングを制御し、実行中/未実行を区別できるようにする)。
 * 複数回呼ばれた場合に備え、resolve関数をFIFOキューで管理する。 */
function makeMockEngine() {
  const goCalls: string[] = [];
  const goMultiPvCalls: string[] = [];
  const positionCalls: string[] = [];
  const setMultiPvCalls: number[] = [];
  let stopCallCount = 0;

  const pendingGoResolvers: Array<(v: GoResult) => void> = [];
  const pendingGoMultiPvResolvers: Array<(v: MultiPvGoResult) => void> = [];

  const engine = {
    position: vi.fn((sfen: string) => {
      positionCalls.push(sfen);
    }),
    setMultiPv: vi.fn((n: number) => {
      setMultiPvCalls.push(n);
    }),
    go: vi.fn(() => {
      goCalls.push("go");
      const d = deferred<GoResult>();
      pendingGoResolvers.push(d.resolve);
      return d.promise;
    }),
    goMultiPv: vi.fn(() => {
      goMultiPvCalls.push("goMultiPv");
      const d = deferred<MultiPvGoResult>();
      pendingGoMultiPvResolvers.push(d.resolve);
      return d.promise;
    }),
    stop: vi.fn(() => {
      stopCallCount += 1;
    }),
  } as unknown as UsiEngine;

  return {
    engine,
    goCalls,
    goMultiPvCalls,
    positionCalls,
    setMultiPvCalls,
    getStopCallCount: () => stopCallCount,
    resolveGo: (value: GoResult = GO_RESULT) => {
      const resolve = pendingGoResolvers.shift();
      if (!resolve) throw new Error("goがまだ呼ばれていません");
      resolve(value);
    },
    resolveGoMultiPv: (value: MultiPvGoResult = MULTIPV_RESULT) => {
      const resolve = pendingGoMultiPvResolvers.shift();
      if (!resolve) throw new Error("goMultiPvがまだ呼ばれていません");
      resolve(value);
    },
  };
}

// task().then().catch().finally()というPromiseチェーン+task内部のawaitが複数の
// マイクロタスクを挟むため、余裕を持って複数回awaitする。
async function flushMicrotasks(): Promise<void> {
  for (let i = 0; i < 10; i++) {
    await Promise.resolve();
  }
}

describe("PrioritizedEngine", () => {
  it("低優先度(goMultiPv)実行中に高優先度(go)が来たらstop()を送り、高優先度を先に完了させる", async () => {
    const mock = makeMockEngine();
    const prioritized = new PrioritizedEngine(mock.engine);
    const low = prioritized.asLowPriority();
    const high = prioritized.asHighPriority();

    low.position("sfen-low");
    const lowPromise = low.goMultiPv();
    await flushMicrotasks();
    expect(mock.goMultiPvCalls).toHaveLength(1);

    high.position("sfen-high");
    const highPromise = high.go();
    await flushMicrotasks();

    // 低優先度が実行中のままhigh要求が来たので、stopが送られているはず。
    expect(mock.getStopCallCount()).toBe(1);
    // しかしgo自体はまだ実行されていない(低優先度がまだ終わっていないため)。
    expect(mock.goCalls).toHaveLength(0);

    // stopに応じて低優先度がbestmoveを返してきた、という状況を模擬する。
    mock.resolveGoMultiPv();
    await flushMicrotasks();

    // 低優先度が終わったので、高優先度が実行されるはず。
    expect(mock.goCalls).toHaveLength(1);
    mock.resolveGo();

    await expect(highPromise).resolves.toEqual(GO_RESULT);
    await expect(lowPromise).resolves.toEqual(MULTIPV_RESULT);
  });

  it("高優先度(go)実行中に低優先度(goMultiPv)が来ても割り込まず、高優先度完了後に実行される", async () => {
    const mock = makeMockEngine();
    const prioritized = new PrioritizedEngine(mock.engine);
    const low = prioritized.asLowPriority();
    const high = prioritized.asHighPriority();

    high.position("sfen-high");
    const highPromise = high.go();
    await flushMicrotasks();
    expect(mock.goCalls).toHaveLength(1);

    low.position("sfen-low");
    const lowPromise = low.goMultiPv();
    await flushMicrotasks();

    // 高優先度実行中は低優先度を割り込ませない。stopも送らない。
    expect(mock.getStopCallCount()).toBe(0);
    expect(mock.goMultiPvCalls).toHaveLength(0);

    mock.resolveGo();
    await flushMicrotasks();

    expect(mock.goMultiPvCalls).toHaveLength(1);
    mock.resolveGoMultiPv();

    await expect(highPromise).resolves.toEqual(GO_RESULT);
    await expect(lowPromise).resolves.toEqual(MULTIPV_RESULT);
  });

  it("同一優先度は到着順に直列実行される", async () => {
    const mock = makeMockEngine();
    const prioritized = new PrioritizedEngine(mock.engine);
    const high = prioritized.asHighPriority();

    high.position("sfen-1");
    const first = high.go();
    await flushMicrotasks();
    expect(mock.goCalls).toHaveLength(1);

    high.position("sfen-2");
    const second = high.go();
    await flushMicrotasks();
    // 1件目が終わるまで2件目は実行されない。
    expect(mock.goCalls).toHaveLength(1);

    mock.resolveGo();
    await flushMicrotasks();
    expect(mock.goCalls).toHaveLength(2);
    mock.resolveGo();

    await expect(first).resolves.toEqual(GO_RESULT);
    await expect(second).resolves.toEqual(GO_RESULT);
  });

  it("同一エンジンインスタンスに対してgo系が同時に2つ実行されない(実行中フラグで検証)", async () => {
    const mock = makeMockEngine();
    const prioritized = new PrioritizedEngine(mock.engine);
    const low = prioritized.asLowPriority();
    const high = prioritized.asHighPriority();

    low.position("sfen-low");
    void low.goMultiPv();
    await flushMicrotasks();

    high.position("sfen-high");
    void high.go();
    await flushMicrotasks();

    // stopが送られた直後も、まだgoは呼ばれていない(goMultiPvの解決待ち)。
    expect(mock.goCalls).toHaveLength(0);
    expect(mock.goMultiPvCalls).toHaveLength(1);

    mock.resolveGoMultiPv();
    await flushMicrotasks();

    // goMultiPvが解決された後、初めてgoが呼ばれる(同時に2つ実行された形跡がない)。
    expect(mock.goCalls).toHaveLength(1);
    expect(mock.goMultiPvCalls).toHaveLength(1);
    mock.resolveGo();
  });

  it("低優先度はsetMultiPv/positionをgoMultiPvと同じジョブ内でposition送信の直前に送る", async () => {
    const mock = makeMockEngine();
    const prioritized = new PrioritizedEngine(mock.engine);
    const low = prioritized.asLowPriority();

    low.setMultiPv(3);
    low.position("sfen-low");
    void low.goMultiPv();
    await flushMicrotasks();

    expect(mock.setMultiPvCalls).toEqual([3]);
    expect(mock.positionCalls).toEqual(["sfen-low"]);
    mock.resolveGoMultiPv();
  });

  it("キュー待ちのジョブ同士でposition/setMultiPvの値が混線しない", async () => {
    const mock = makeMockEngine();
    const prioritized = new PrioritizedEngine(mock.engine);
    const low = prioritized.asLowPriority();
    const high = prioritized.asHighPriority();

    // 高優先度を実行中にして、低優先度をキューに溜める
    high.position("sfen-high");
    const highPromise = high.go();
    await flushMicrotasks();

    low.setMultiPv(3);
    low.position("sfen-low-1");
    const firstLow = low.goMultiPv();

    low.setMultiPv(5);
    low.position("sfen-low-2");
    const secondLow = low.goMultiPv();

    // まだ低優先度は実行されない
    expect(mock.goMultiPvCalls).toHaveLength(0);

    mock.resolveGo();
    await flushMicrotasks();

    // 1件目は3 / sfen-low-1でなければならない
    expect(mock.setMultiPvCalls).toEqual([3]);
    expect(mock.positionCalls).toContain("sfen-low-1");

    mock.resolveGoMultiPv();
    await flushMicrotasks();

    // 2件目は5 / sfen-low-2
    expect(mock.setMultiPvCalls).toEqual([3, 5]);
    expect(mock.positionCalls).toEqual(["sfen-high", "sfen-low-1", "sfen-low-2"]);

    mock.resolveGoMultiPv();

    await expect(highPromise).resolves.toEqual(GO_RESULT);
    await expect(firstLow).resolves.toEqual(MULTIPV_RESULT);
    await expect(secondLow).resolves.toEqual(MULTIPV_RESULT);
  });
});
