// UsiEngineは1プロセスあたり同時に1つのgo系コマンド(go/goMultiPv)しか安全に扱えない
// (USIプロトコルは1回のgoに対して1回のbestmoveしか想定しておらず、既存のUsiEngine自体には
// 複数go要求をさばくキュー・中断の仕組みが無い)。
//
// Phase2のMultiPV参考評価(低優先度・バックグラウンド、candidateMoveSafetyCheck.tsが使う)と、
// 対局進行のbestmove探索(高優先度、gameSession.tsのplayOpponentMoveが使う)が同じエンジン
// プロセスに同時にgoを送ると、waitForLine()がどちらのbestmove行を拾うか不定になり、
// 対局・解析の両方が壊れうる。
//
// 本モジュールは、同一UsiEngineインスタンスへのposition+go系呼び出しを直列化し、
// 高優先度が低優先度より常に先に実行されるようにする。低優先度の実行中に高優先度の
// 要求が来た場合は、USIプロトコル標準の`stop`コマンド(「できるだけ早くbestmoveを返す」)
// を送って低優先度側を早期終了させる。stopは独自解釈を加えていない標準コマンドである
// (usiEngine.ts参照)。
//
// 【position()/setMultiPv()の遅延送信について】
// candidateMoveSafetyCheck.ts / gameSession.tsのplayOpponentMoveは、いずれも
// 「position()(必要ならsetMultiPv()も)を呼んだ直後(間にawaitを挟まず)に対応する
// go系を呼ぶ」という同一のパターンで書かれている(既存コード確認済み、いずれも
// 変更していない)。JavaScriptは単一スレッドであり、同期文の間に他のコードが
// 割り込むことはないため、「go系が呼ばれた時点で、直前に渡された引数を使って
// setMultiPv送信・position送信・go系実行を1つの不可分な作業としてキューへ積む」
// という実装で、呼び出し側のコードを一切変更せずに安全な対応付けができる。
// setMultiPvを別ジョブとしてキューに積むと、その直後に高優先度ジョブが割り込んで
// position/goとの対応がズレる恐れがあるため、必ずgoMultiPvと同じジョブ内で
// (position送信の直前に)送信する。高優先度用・低優先度用でそれぞれ独立した
// クロージャ変数に引数を保持するため、優先度間の値の混線は起きない。
//
// 【go系呼び出し時点でのスナップショットについて(重要)】
// candidateMoveSafetyCheck.tsは、1回のcheckCandidateMovesSafety()呼び出しの中で
// awaitを挟みながら複数回position()+goMultiPv()を呼ぶ。しかし呼び出し元がawaitを
// 挟まずに(前のgoMultiPv()の解決を待たずに)複数回position()+goMultiPv()を呼んだ
// 場合、キュー内のジョブがまだ実行されていない間にクロージャ変数(pendingSfen等)が
// 次の呼び出しで上書きされてしまう恐れがある。これを避けるため、go()/goMultiPv()が
// 呼ばれた「その瞬間」に、保留中の値をローカル変数へスナップショットしてから
// キューへ積む(キュー内の非同期タスクの中で共有クロージャ変数を遅延参照しない)。

import type { GoOptions, GoResult, MultiPvGoResult, UsiEngine } from "./usiEngine.js";

type Priority = "high" | "low";

interface QueueEntry {
  priority: Priority;
  task: () => Promise<unknown>;
  resolve: (value: unknown) => void;
  reject: (err: unknown) => void;
}

class EngineJobQueue {
  private readonly queue: QueueEntry[] = [];
  private running: QueueEntry | undefined;

  constructor(private readonly engine: Pick<UsiEngine, "stop">) {}

  enqueue<T>(priority: Priority, task: () => Promise<T>): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const entry: QueueEntry = {
        priority,
        task: task as () => Promise<unknown>,
        resolve: resolve as (value: unknown) => void,
        reject,
      };

      if (priority === "high") {
        // 高優先度は、既存キュー中の他の高優先度より後ろ・低優先度より前に挿入する。
        const firstLowIndex = this.queue.findIndex((e) => e.priority === "low");
        if (firstLowIndex === -1) this.queue.push(entry);
        else this.queue.splice(firstLowIndex, 0, entry);

        // 低優先度が実行中なら、標準USIコマンドstopで早期終了させ、高優先度を先に回す。
        if (this.running?.priority === "low") this.engine.stop();
      } else {
        this.queue.push(entry);
      }

      this.pump();
    });
  }

  private pump(): void {
    if (this.running || this.queue.length === 0) return;
    const entry = this.queue.shift();
    if (!entry) return;
    this.running = entry;
    entry
      .task()
      .then((value) => entry.resolve(value))
      .catch((err: unknown) => entry.reject(err))
      .finally(() => {
        this.running = undefined;
        this.pump();
      });
  }
}

/** gameSession.tsのOpponentEngine(Pick<UsiEngine, "position" | "go">)と構造的に一致する。 */
export type HighPriorityEngine = Pick<UsiEngine, "position" | "go">;
/** candidateMoveSafetyCheck.tsのSafetyCheckEngineと構造的に一致する。 */
export type LowPriorityEngine = Pick<UsiEngine, "position" | "setMultiPv" | "goMultiPv">;

export class PrioritizedEngine {
  private readonly queue: EngineJobQueue;

  constructor(private readonly engine: UsiEngine) {
    this.queue = new EngineJobQueue(engine);
  }

  /**
   * 対局進行(playOpponentMoveのbestmove探索)向けの高優先度インターフェース。
   * gameSession.ts自体は変更せず、この戻り値をそのまま渡せる。
   */
  asHighPriority(): HighPriorityEngine {
    let pendingSfen: string | undefined;
    let pendingMoves: string[] | undefined;

    return {
      position: (sfen: string, moves: string[] = []) => {
        pendingSfen = sfen;
        pendingMoves = moves;
      },
      go: (options?: GoOptions): Promise<GoResult> => {
        // 呼ばれた瞬間にスナップショットする(ファイル冒頭コメント参照)。
        const sfen = pendingSfen ?? "startpos";
        const moves = pendingMoves;
        return this.queue.enqueue("high", async () => {
          this.engine.position(sfen, moves);
          return this.engine.go(options);
        });
      },
    };
  }

  /**
   * Phase2 MultiPV参考評価(candidateMoveSafetyCheck.ts)向けの低優先度インターフェース。
   * candidateMoveSafetyCheck.ts自体は変更せず、この戻り値をそのまま渡せる。
   */
  asLowPriority(): LowPriorityEngine {
    let pendingSfen: string | undefined;
    let pendingMoves: string[] | undefined;
    let pendingMultiPv = 1;

    return {
      position: (sfen: string, moves: string[] = []) => {
        pendingSfen = sfen;
        pendingMoves = moves;
      },

      setMultiPv: (multiPv: number) => {
        pendingMultiPv = multiPv;
      },

      goMultiPv: (options?: GoOptions): Promise<MultiPvGoResult> => {
        // 呼ばれた瞬間にスナップショットする(ファイル冒頭コメント参照。
        // awaitを挟まず連続してposition()+goMultiPv()が呼ばれても、各ジョブが
        // 呼び出し時点の正しい値を使うようにするため)。
        const sfen = pendingSfen ?? "startpos";
        const moves = pendingMoves;
        const multiPv = pendingMultiPv;
        return this.queue.enqueue("low", async () => {
          this.engine.setMultiPv(multiPv);
          this.engine.position(sfen, moves);
          return this.engine.goMultiPv(options);
        });
      },
    };
  }

  quit(): void {
    this.engine.quit();
  }

  close(): void {
    this.engine.close();
  }
}
