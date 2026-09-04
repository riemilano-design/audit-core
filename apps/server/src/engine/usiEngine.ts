// やねうら王などUSI(Universal Shogi Interface)準拠エンジンとの通信クライアント。
// spike/usi-client.mjs(Phase 0着手前の疎通確認スパイク)で検証済みのプロトコル実装を
// 本実装(apps/server)向けに型付けし直したもの。spike自体は変更していない。
//
// このモジュールの責任範囲は USI プロトコルでのやり取りに限定する。
// 候補手の安全確認(MultiPV等)・コーチングロジックはここでは扱わない
// (docs/ROLES.md・.claude/agents/engine-integration.md を参照)。

import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { createInterface, type Interface } from "node:readline";

export class UsiEngineTimeoutError extends Error {}

export interface GoOptions {
  movetimeMs?: number;
}

export interface GoResult {
  bestmove: string | undefined;
  ponder: string | undefined;
  scoreCp: number | undefined;
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

  async go({ movetimeMs = 2000 }: GoOptions = {}): Promise<GoResult> {
    this.send(`go movetime ${movetimeMs}`);
    const { collected } = await this.waitForLine((line) => line.startsWith("bestmove"), {
      timeoutMs: movetimeMs + 10_000,
    });

    const bestmoveLine = collected.find((l) => l.startsWith("bestmove"));
    const match = bestmoveLine?.match(/^bestmove (\S+)(\s+ponder\s+(\S+))?/);
    const bestmove = match?.[1];
    const ponder = match?.[3];

    let scoreCp: number | undefined;
    for (const line of collected) {
      const m = line.match(/\bscore cp (-?\d+)/);
      if (m) scoreCp = Number(m[1]);
    }

    return { bestmove, ponder, scoreCp, infoLines: collected };
  }

  quit(): void {
    this.send("quit");
  }

  close(): void {
    this.rl?.close();
    this.proc?.kill();
  }
}
