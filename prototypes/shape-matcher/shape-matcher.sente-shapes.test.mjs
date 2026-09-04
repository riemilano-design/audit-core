// data/shapes/mino_*.json はMVP座標規約(docs/DATA_MODEL.md: self=先手固定、座標は先手側絶対座標)
// に合わせて180度回転済み。本テストは、そのデータをperspectiveColor='sente'で
// shape-matcherに渡した場合に正しく認識されることを確認する
// (data/examples/shapes.example.json を使う既存テストとは別データ・別視点)。

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { Board } from 'shogiops/board';
import { Hands } from 'shogiops/hands';
import { Shogi } from 'shogiops/variant/shogi';
import { makeSfen } from 'shogiops/sfen';
import { parseSquareName } from 'shogiops/util';

import { matchShape } from './shape-matcher.mjs';
import { japaneseToRole } from './piece-mapping.mjs';
import honmino from '../../data/shapes/mino_honmino.json' with { type: 'json' };
import takamino from '../../data/shapes/mino_takamino.json' with { type: 'json' };
import ginkanmuri from '../../data/shapes/mino_ginkanmuri.json' with { type: 'json' };

const PERSPECTIVE = 'sente';

function buildSfenFromShape(shape, color) {
  let board = Board.empty();
  for (const { piece, square } of shape.required_pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square in shape fixture: ${square}`);
    board = board.clone();
    board.set(sq, { color, role: japaneseToRole(piece) });
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn: 'sente', moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

for (const shape of [honmino, takamino, ginkanmuri]) {
  test(`${shape.id}: 先手SFEN上の先手駒として required_pieces がそのまま matched になる`, () => {
    const sfen = buildSfenFromShape(shape, PERSPECTIVE);
    const result = matchShape(sfen, shape, { perspectiveColor: PERSPECTIVE });

    assert.equal(result.status, 'matched');
    assert.equal(result.matchedRequiredPieces.length, shape.required_pieces.length);
    assert.equal(result.unmatchedRequiredPieces.length, 0);
  });

  test(`${shape.id}: 同じ駒配置を後手として置いた場合はperspectiveColor='sente'ではmatchedにならない`, () => {
    const sfen = buildSfenFromShape(shape, 'gote');
    const result = matchShape(sfen, shape, { perspectiveColor: PERSPECTIVE });

    assert.equal(result.status, 'not_matched');
    assert.equal(result.matchedRequiredPieces.length, 0);
    assert.equal(result.unmatchedRequiredPieces.length, shape.required_pieces.length);
  });
}
