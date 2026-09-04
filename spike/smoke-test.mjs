// Phase 0 technical spike: minimal end-to-end check that
//   shogiops (board/rules) -> USI -> YaneuraOu (engine)
// can talk to each other. This intentionally does nothing else:
// no coach logic, no UI, no opening/shape data.
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { parseSfen, makeSfen } from 'shogiops/sfen';
import { makeUsi } from 'shogiops/util';
import { UsiEngine } from './usi-client.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ENGINE_PATH = path.join(__dirname, 'engine', 'YaneuraOu-by-gcc');

function step(label) {
  console.log(`\n=== ${label} ===`);
}

// 1. Initial position via shogiops
step('1. shogiops: initial position');
const rules = 'standard';
const pos = parseSfen(rules, 'startpos').unwrap();
console.log('initial SFEN:', makeSfen(pos));

// 2. Legal move generation + a few plies of play, picking the first
//    legal destination shogiops offers each turn (no strategy intended).
step('2. shogiops: legal move generation + a few plies');
const playedUsiMoves = [];
const PLIES = 4;
for (let i = 0; i < PLIES; i++) {
  const dests = pos.allMoveDests();
  let chosen;
  for (const [from, toSquares] of dests) {
    if (toSquares.nonEmpty()) {
      const to = toSquares.first();
      chosen = { from, to };
      break;
    }
  }
  if (!chosen) throw new Error(`No legal moves found at ply ${i} (turn=${pos.turn})`);

  const usi = makeUsi(chosen);
  pos.play(chosen);
  playedUsiMoves.push(usi);
  console.log(`ply ${i + 1}: turn was ${pos.turn === 'sente' ? 'gote' : 'sente'}, played ${usi}`);
}
console.log('SFEN after plies:', makeSfen(pos));
console.log('USI move list:', playedUsiMoves.join(' '));

// 3. Start YaneuraOu and run the USI handshake
step('3. USI: engine startup + handshake');
console.log('engine path:', ENGINE_PATH);
const engine = new UsiEngine(ENGINE_PATH);
engine.start();

try {
  await engine.usiHandshake();
  console.log('usi -> usiok: OK');

  await engine.isReady();
  console.log('isready -> readyok: OK');

  // 4. Send the position shogiops produced, ask for a move
  step('4. USI: position + go + bestmove');
  engine.position('startpos', playedUsiMoves);
  console.log('sent: position startpos moves', playedUsiMoves.join(' '));

  const { bestmove, scoreCp, infoLines } = await engine.go({ movetimeMs: 1000 });
  console.log('bestmove:', bestmove);
  console.log('score cp:', scoreCp ?? '(not reported)');
  console.log('raw info/bestmove lines:');
  for (const line of infoLines) console.log(' ', line);

  // 5. Feed the engine's move back into shogiops, just to prove the
  //    round trip (shogiops -> engine -> shogiops) is coherent.
  if (bestmove && bestmove !== 'resign' && bestmove !== 'win') {
    step('5. shogiops: apply engine bestmove back onto the position');
    const { parseUsi } = await import('shogiops/util');
    const md = parseUsi(bestmove);
    if (!md) throw new Error(`shogiops could not parse engine bestmove: ${bestmove}`);
    pos.play(md);
    console.log('SFEN after engine move:', makeSfen(pos));
  }

  console.log('\n=== smoke test: PASSED ===');
} finally {
  engine.quit();
  engine.close();
}
