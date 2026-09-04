// Minimal USI (Universal Shogi Interface) client for the Phase 0 spike.
// Spawns a USI-compliant engine (YaneuraOu) and speaks the line-based
// USI protocol over stdin/stdout.
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';

export class UsiEngine {
  constructor(enginePath) {
    this.enginePath = enginePath;
    this.proc = null;
    this.rl = null;
    this.lineWaiters = [];
  }

  start() {
    this.proc = spawn(this.enginePath, [], { stdio: ['pipe', 'pipe', 'pipe'] });
    this.rl = createInterface({ input: this.proc.stdout });
    this.rl.on('line', (line) => this.#dispatch(line));
    this.proc.stderr.on('data', (chunk) => {
      process.stderr.write(`[engine stderr] ${chunk}`);
    });
  }

  #dispatch(line) {
    for (const waiter of [...this.lineWaiters]) {
      waiter.onLine(line);
    }
  }

  send(command) {
    this.proc.stdin.write(`${command}\n`);
  }

  // Resolves once a line matching `predicate` is seen. Collects every line
  // observed while waiting into `collected` (useful for `go`, which streams
  // `info ...` lines before the final `bestmove ...`).
  waitForLine(predicate, { timeoutMs = 10_000 } = {}) {
    return new Promise((resolve, reject) => {
      const collected = [];
      const timer = setTimeout(() => {
        this.lineWaiters = this.lineWaiters.filter((w) => w !== waiter);
        reject(new Error(`Timed out waiting for line matching ${predicate} after ${timeoutMs}ms`));
      }, timeoutMs);

      const waiter = {
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

  async usiHandshake() {
    this.send('usi');
    return this.waitForLine((line) => line === 'usiok');
  }

  async isReady() {
    this.send('isready');
    return this.waitForLine((line) => line === 'readyok');
  }

  // sfen: either 'startpos' or a full SFEN board string.
  // moves: array of USI move strings already played from that sfen.
  position(sfen, moves = []) {
    const base = sfen === 'startpos' ? 'startpos' : `sfen ${sfen}`;
    const movesPart = moves.length > 0 ? ` moves ${moves.join(' ')}` : '';
    this.send(`position ${base}${movesPart}`);
  }

  // Runs `go` and returns { bestmove, ponder, scoreCp, infoLines }.
  async go({ movetimeMs = 2000 } = {}) {
    this.send(`go movetime ${movetimeMs}`);
    const { collected } = await this.waitForLine(
      (line) => line.startsWith('bestmove'),
      { timeoutMs: movetimeMs + 10_000 },
    );

    const bestmoveLine = collected.find((l) => l.startsWith('bestmove'));
    const [, bestmove, , ponder] = bestmoveLine?.match(/^bestmove (\S+)(\s+ponder\s+(\S+))?/) ?? [];

    let scoreCp;
    for (const line of collected) {
      const match = line.match(/\bscore cp (-?\d+)/);
      if (match) scoreCp = Number(match[1]);
    }

    return { bestmove, ponder, scoreCp, infoLines: collected };
  }

  quit() {
    this.send('quit');
  }

  close() {
    this.rl?.close();
    this.proc?.kill();
  }
}
