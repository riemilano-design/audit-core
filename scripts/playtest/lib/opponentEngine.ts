// STEP D3b(docs/STEP_D3b_PLAN_2026-09-15.md 2.2)。探索モード(explore.ts)で、相手のエンジンだけを
// 検証用に弱くするための包み。**開発・検証専用の設定であり、本番の挙動は変えない。**
//
// 【このファイルがやること】
// - 相手に渡す HighPriorityEngine の go に nodes を足す(go nodes N になる ― usiEngine.ts の buildGoCommand)
// - --opponent-nodes を読む(正の整数でなければ止める。黙って本番どおりの相手にしない)
// - 相手と先手(E 読み)のハンドルを別々に作り、**相手のハンドルだけを包む**
// - 相手の go に nodes を付けて渡した回数を数える(f2 の事前読みの勧め。meta の値は「読んだ値」しか示さないので、
//   「相手の go に nodes が届いた」ことを 1 局の終わりの出力で見えるようにする ― 計画 10.4)
//
// 【このファイルが絶対にやらないこと】
// - 本番の gameSession.ts の go({ movetimeMs: 1000 }) を変えること(包むのは explore.ts が渡すハンドルだけ)
// - 候補手・③・engineReference(LowPriorityEngine の goMultiPv)に nodes を渡すこと。包みは HighPriorityEngine の形
//   (position と go)しか持たないので、LowPriorityEngine を包めない(型で守る)
// - Threads を変えること(エンジン 1 本の全体に効き、相手以外の探索の条件まで変わる ― 計画 3.2・Q-3)

import type { HighPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import type { GoOptions, GoResult } from "../../../apps/server/src/engine/usiEngine.js";

/** 相手の go に nodes を付けて渡した回数の入れ物。 */
export interface OpponentGoCounter {
  nodesGoCalls: number;
}

/**
 * nodes が undefined なら engine をそのまま返す(従来どおり。counter も数えない)。
 * そうでなければ、go に渡る options に nodes を足した包みを返し、go のたびに counter を 1 増やす。
 * nodes があると buildGoCommand が go nodes N を送り、movetime は送らない。
 */
export function withOpponentNodes(
  engine: HighPriorityEngine,
  nodes: number | undefined,
  counter?: OpponentGoCounter,
): HighPriorityEngine {
  if (nodes === undefined) return engine;
  return {
    position: (...args: Parameters<HighPriorityEngine["position"]>) => engine.position(...args),
    go: (options?: GoOptions): Promise<GoResult> => {
      if (counter) counter.nodesGoCalls += 1;
      return engine.go({ ...options, nodes });
    },
  };
}

/**
 * --opponent-nodes を読む。無ければ undefined(相手は本番どおり)。
 * **値が正の整数(先頭が 0 でない数字だけ。"2e3"・"+2000"・" 2000" は通さない)でない・値が無いときはエラーで止める**(計画 2.2・F-O5)。
 */
export function parseOpponentNodesOption(argv: readonly string[]): number | undefined {
  const index = argv.indexOf("--opponent-nodes");
  if (index === -1) return undefined;
  const value = argv[index + 1];
  if (value === undefined || !/^[1-9][0-9]*$/.test(value) || !Number.isSafeInteger(Number(value))) {
    throw new Error(`--opponent-nodes の値は正の整数: ${value === undefined ? "(値が無い)" : `"${value}"`}`);
  }
  return Number(value);
}

/**
 * 相手と先手(E 読み)の HighPriorityEngine を別々に作り、**相手のハンドルだけを** withOpponentNodes で包む(計画 2.2・F-O3)。
 * asHighPriority() は呼ぶたびに独立したハンドルを返す(prioritizedEngine.ts)ので、2 回呼ぶ。
 * opponentNodesGoCalls() は、相手の go に nodes を付けて渡した回数(opponentNodes が undefined なら 0 のまま)。
 */
export function buildHighPriorityHandles(
  engine: { asHighPriority(): HighPriorityEngine },
  opponentNodes: number | undefined,
): { opponent: HighPriorityEngine; sente: HighPriorityEngine; opponentNodesGoCalls: () => number } {
  const counter: OpponentGoCounter = { nodesGoCalls: 0 };
  return {
    opponent: withOpponentNodes(engine.asHighPriority(), opponentNodes, counter),
    sente: engine.asHighPriority(),
    opponentNodesGoCalls: () => counter.nodesGoCalls,
  };
}
