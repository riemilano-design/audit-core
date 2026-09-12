// やねうら王などUSI(Universal Shogi Interface)準拠エンジンとの通信クライアント。
// spike/usi-client.mjs(Phase 0着手前の疎通確認スパイク)で検証済みのプロトコル実装を
// 本実装(apps/server)向けに型付けし直したもの。spike自体は変更していない。
//
// このモジュールの責任範囲は USI プロトコルでのやり取りに限定する。
// 候補手の安全確認(MultiPV結果とcandidateMovesの突き合わせ、閾値判定等)・
// コーチングロジックはここでは扱わない(docs/ROLES.md・
// .claude/agents/engine-integration.md を参照。安全確認自体は
// apps/server/src/analysis/candidateMoveSafetyCheck.ts の責務)。
//
// 【Phase2 Unit3で追加したMultiPV対応について】
// 既存の go()/GoResult(単一bestmove API)は一切変更していない
// (呼び出し側・既存の挙動を壊さないため)。MultiPV対応は setMultiPv() /
// goMultiPv() という新規メソッドとして追加し、bestmove行の解析だけを
// parseBestmoveLine() として共通化した(go()もこれを使うよう内部実装を
// 差し替えたが、go()が返すGoResultの形・値は従来と完全に同じ)。
// info行のmultipv/score/pvの解析は usiInfoParser.ts (新規, 決定的な純粋関数)に
// 委譲し、ここでは重複するパーサーを作らない。

import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { createInterface, type Interface } from "node:readline";
import { parseInfoLine, type UsiScore } from "./usiInfoParser.js";

export class UsiEngineTimeoutError extends Error {}

export interface GoOptions {
  movetimeMs?: number;
  /** 指定時は`go nodes N`を送る(movetimeは送らない)。回帰用の探索量固定に使う。 */
  nodes?: number;
}

export interface GoResult {
  bestmove: string | undefined;
  ponder: string | undefined;
  scoreCp: number | undefined;
  infoLines: string[];
}

// ノード数指定(`go nodes N`)のgoコマンド待ちのタイムアウト。
// ノード数を固定しても、実際にそのノード数を読み切るまでの所要時間は
// 実行環境の負荷(CPU使用率等)で変動するため、movetimeベースの
// タイムアウト(movetimeMs + 10_000)とは別に、十分な余裕を持つ固定値とする。
const NODES_GO_TIMEOUT_MS = 60_000;

/**
 * go()/goMultiPv()共通: GoOptionsから実際に送るgoコマンド文字列と
 * bestmove待ちのタイムアウトを決める純粋関数。
 * nodesが指定されていれば`go nodes N`(タイムアウトはNODES_GO_TIMEOUT_MS固定)、
 * 無ければ従来どおり`go movetime N`(タイムアウトはmovetimeMs + 10_000)。
 */
export function buildGoCommand({ movetimeMs = 2000, nodes }: GoOptions = {}): {
  command: string;
  timeoutMs: number;
} {
  if (nodes !== undefined && nodes > 0) {
    return { command: `go nodes ${nodes}`, timeoutMs: NODES_GO_TIMEOUT_MS };
  }
  return { command: `go movetime ${movetimeMs}`, timeoutMs: movetimeMs + 10_000 };
}

/** collected行群からbestmove/ponderを取り出す(go()/goMultiPv()共通)。 */
export function parseBestmoveLine(collected: string[]): { bestmove: string | undefined; ponder: string | undefined } {
  const bestmoveLine = collected.find((l) => l.startsWith("bestmove"));
  const match = bestmoveLine?.match(/^bestmove (\S+)(\s+ponder\s+(\S+))?/);
  return { bestmove: match?.[1], ponder: match?.[3] };
}

/** MultiPVの1本の読み筋。usiInfoParser.tsのUsiInfoLineから、安全確認が必要とする分だけを持つ。 */
export interface MultiPvLine {
  multipv: number;
  score: UsiScore | undefined;
  pv: string[];
  /** STEP U6-L: 採用したinfo行に`lowerbound`/`upperbound`が付いていたか
   * (usiInfoParser.tsのUsiInfoLineからそのまま写す。必須にする理由は同ファイル参照)。 */
  lowerbound: boolean;
  upperbound: boolean;
}

export interface MultiPvGoResult {
  bestmove: string | undefined;
  ponder: string | undefined;
  /** multipv番号昇順・重複はcollected内で最後に観測された内容を採用した、決定的な順序の一覧。 */
  lines: MultiPvLine[];
  infoLines: string[];
}

interface LineWaiter {
  onLine(line: string): void;
}

export class UsiEngine {
  private readonly enginePath: string;
  private proc: ChildProcessWithoutNullStreams | undefined;
  private rl: Interface | undefined;
  private lineWaiters: LineWaiter[] = [];

  constructor(enginePath: string) {
    this.enginePath = enginePath;
  }

  start(): void {
    this.proc = spawn(this.enginePath, [], { stdio: ["pipe", "pipe", "pipe"] });
    this.rl = createInterface({ input: this.proc.stdout });
    this.rl.on("line", (line) => this.dispatch(line));
    this.proc.stderr.on("data", (chunk: Buffer) => {
      process.stderr.write(`[engine stderr] ${chunk}`);
    });
  }

  private dispatch(line: string): void {
    for (const waiter of [...this.lineWaiters]) {
      waiter.onLine(line);
    }
  }

  send(command: string): void {
    if (!this.proc) {
      throw new Error("エンジンプロセスが起動していません(先にstart()を呼んでください)");
    }
    this.proc.stdin.write(`${command}\n`);
  }

  // `predicate` に一致する行が来るまで待つ。待っている間に観測した全行を
  // `collected` に集める(`go` が bestmove の前に info行を複数返すため)。
  waitForLine(
    predicate: (line: string) => boolean,
    { timeoutMs = 10_000 }: { timeoutMs?: number } = {},
  ): Promise<{ line: string; collected: string[] }> {
    return new Promise((resolve, reject) => {
      const collected: string[] = [];
      const timer = setTimeout(() => {
        this.lineWaiters = this.lineWaiters.filter((w) => w !== waiter);
        reject(new UsiEngineTimeoutError(`${timeoutMs}ms以内に条件に一致する行が来ませんでした`));
      }, timeoutMs);

      const waiter: LineWaiter = {
        onLine: (line) => {
          collected.push(line);
          if (predicate(line)) {
            clearTimeout(timer);
            this.lineWaiters = this.lineWaiters.filter((w) => w !== waiter);
            resolve({ line, collected });
          }
        },
      };
      this.lineWaiters.push(waiter);
    });
  }

  async usiHandshake(): Promise<void> {
    this.send("usi");
    await this.waitForLine((line) => line === "usiok");
  }

  async isReady(): Promise<void> {
    this.send("isready");
    await this.waitForLine((line) => line === "readyok");
  }

  // sfen: 'startpos' または完全なSFEN文字列。
  // moves: そのsfenから指した手のUSI文字列の配列。
  position(sfen: string, moves: string[] = []): void {
    const base = sfen === "startpos" ? "startpos" : `sfen ${sfen}`;
    const movesPart = moves.length > 0 ? ` moves ${moves.join(" ")}` : "";
    this.send(`position ${base}${movesPart}`);
  }

  async go(options: GoOptions = {}): Promise<GoResult> {
    const { command, timeoutMs } = buildGoCommand(options);
    this.send(command);
    const { collected } = await this.waitForLine((line) => line.startsWith("bestmove"), {
      timeoutMs,
    });

    const { bestmove, ponder } = parseBestmoveLine(collected);

    // 挙動は変更前と完全に同じ(collected内で最後に見つかった`score cp`を採用する)。
    // multipvを区別しない単純な走査のため、MultiPV設定時の解釈にはgoMultiPv()を使うこと。
    let scoreCp: number | undefined;
    for (const line of collected) {
      const m = line.match(/\bscore cp (-?\d+)/);
      if (m) scoreCp = Number(m[1]);
    }

    return { bestmove, ponder, scoreCp, infoLines: collected };
  }

  /**
   * エンジンにMultiPV(複数の候補読み筋)を設定する。
   * `setoption`はUSIプロトコル上、通常`isready`より前(usiok受信後)に送るものだが、
   * 実際にいつ送るか(対局中に何度でも変更可能か等)はエンジン実装依存であり、
   * その呼び出しタイミングの管理は呼び出し側の責務とする(本メソッドはコマンド送信のみ)。
   */
  setMultiPv(multiPv: number): void {
    this.send(`setoption name MultiPV value ${multiPv}`);
  }

  /**
   * エンジンに探索スレッド数を設定する。
   * `setMultiPv()`と同様、いつ送るか(対局中に変更可能か等)はエンジン実装依存であり、
   * その呼び出しタイミングの管理は呼び出し側の責務とする(本メソッドはコマンド送信のみ)。
   */
  setThreads(threads: number): void {
    this.send(`setoption name Threads value ${threads}`);
  }

  /**
   * go()と同じく`go movetime`でエンジンに読ませ、bestmoveに加えて、
   * info行のmultipv/score/pvをusiInfoParser.ts経由で構造化して返す。
   * 同じmultipv番号のinfo行が複数回出力された場合(探索が深くなるにつれて更新される)は、
   * collected内で最後に観測された内容を採用する(go()のscoreCpが「最後に見つかった値」を
   * 採用しているのと同じ考え方)。返すlinesはmultipv番号昇順の決定的な順序に並べる。
   *
   * MultiPVを何本読ませるかはsetMultiPv()で事前に設定しておく(本メソッド自体は
   * setoptionを送らない。責務を分離するため)。
   */
  async goMultiPv(options: GoOptions = {}): Promise<MultiPvGoResult> {
    const { command, timeoutMs } = buildGoCommand(options);
    this.send(command);
    const { collected } = await this.waitForLine((line) => line.startsWith("bestmove"), {
      timeoutMs,
    });

    const { bestmove, ponder } = parseBestmoveLine(collected);

    const linesByMultipv = new Map<number, MultiPvLine>();
    for (const line of collected) {
      const parsed = parseInfoLine(line);
      if (!parsed) continue;
      linesByMultipv.set(parsed.multipv, {
        multipv: parsed.multipv,
        score: parsed.score,
        pv: parsed.pv,
        lowerbound: parsed.lowerbound,
        upperbound: parsed.upperbound,
      });
    }
    const lines = [...linesByMultipv.values()].sort((a, b) => a.multipv - b.multipv);

    return { bestmove, ponder, lines, infoLines: collected };
  }

  /**
   * 実行中の探索(go/goMultiPv)に、できるだけ早くbestmoveを返すよう指示する
   * USIプロトコル標準コマンド。本メソッドはコマンド送信のみを行い、実際にいつ
   * bestmove行が来るかはエンジン実装依存(既存のgo()/goMultiPv()のwaitForLineが
   * そのまま拾う。呼び出しタイミングの管理・優先度制御はengine/prioritizedEngine.tsの責務)。
   */
  stop(): void {
    this.send("stop");
  }

  quit(): void {
    this.send("quit");
  }

  close(): void {
    this.rl?.close();
    this.proc?.kill();
  }
}
