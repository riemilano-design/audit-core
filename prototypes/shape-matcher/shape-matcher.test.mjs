import { test } from 'node:test';
import assert from 'node:assert/strict';

import { Board } from 'shogiops/board';
import { Hands } from 'shogiops/hands';
import { Shogi } from 'shogiops/variant/shogi';
import { makeSfen } from 'shogiops/sfen';
import { parseSquareName } from 'shogiops/util';

import { matchShape } from './shape-matcher.mjs';
import shapesExample from '../../data/examples/shapes.example.json' with { type: 'json' };

const honmino = shapesExample;
assert.equal(honmino.id, 'mino_honmino', 'このテストは data/examples/shapes.example.json の本美濃を対象にする');

// required_pieces の座標(2b/3b/4a/5b)は shape-matcher.mjs のコメントで検証した通り
// 後手側の絶対座標に一致するため、テストではperspectiveColor='gote'を仮定として使う。
const PERSPECTIVE = 'gote';

// テスト用のSFENを shogiops の Board API で組み立てる(手書きSFEN文字列のtypoを避けるため)。
// strict validationは使わない(玉のみ・駒不足などの局面もテストしたいため)。
function buildSfen(pieces) {
  let board = Board.empty();
  for (const { square, color, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square in test fixture: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn: 'sente', moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

const HONMINO_PIECES_GOTE = [
  { square: '2b', color: 'gote', role: 'king' },
  { square: '3b', color: 'gote', role: 'silver' },
  { square: '4a', color: 'gote', role: 'gold' },
  { square: '5b', color: 'gote', role: 'gold' },
];

test('1. 本美濃が完成しているSFEN -> matched', () => {
  const sfen = buildSfen(HONMINO_PIECES_GOTE);
  const result = matchShape(sfen, honmino, { perspectiveColor: PERSPECTIVE });

  assert.equal(result.status, 'matched');
  assert.equal(result.shapeId, 'mino_honmino');
  assert.equal(result.matchedRequiredPieces.length, 4);
  assert.equal(result.unmatchedRequiredPieces.length, 0);
});

test('2. 必須駒を1つ外したSFEN -> not_matched', () => {
  const withoutGold5b = HONMINO_PIECES_GOTE.filter((p) => p.square !== '5b');
  const sfen = buildSfen(withoutGold5b);
  const result = matchShape(sfen, honmino, { perspectiveColor: PERSPECTIVE });

  assert.equal(result.status, 'not_matched');
  assert.equal(result.matchedRequiredPieces.length, 3);
  assert.equal(result.unmatchedRequiredPieces.length, 1);
  assert.equal(result.unmatchedRequiredPieces[0].square, '5b');
});

test('3. optional駒がある場合/ない場合 -> matched/not_matchedには影響しない', () => {
  // data/examples/shapes.example.json の本美濃にはoptionalな駒が存在しないため、
  // 判定仕様確認用にこのテスト内だけで拡張したshapeオブジェクトを使う
  // (data/配下の実データやschemaは変更しない)。
  const honminoWithOptionalLance = {
    ...honmino,
    required_pieces: [...honmino.required_pieces, { piece: '香', square: '1b', optional: true }],
  };

  const sfenWithoutOptional = buildSfen(HONMINO_PIECES_GOTE);
  const resultWithoutOptional = matchShape(sfenWithoutOptional, honminoWithOptionalLance, {
    perspectiveColor: PERSPECTIVE,
  });
  assert.equal(resultWithoutOptional.status, 'matched', 'optional駒が無くても必須駒が揃っていればmatched');
  assert.equal(resultWithoutOptional.optionalPieces.length, 1);
  assert.equal(resultWithoutOptional.optionalPieces[0].present, false);

  const sfenWithOptional = buildSfen([
    ...HONMINO_PIECES_GOTE,
    { square: '1b', color: 'gote', role: 'lance' },
  ]);
  const resultWithOptional = matchShape(sfenWithOptional, honminoWithOptionalLance, {
    perspectiveColor: PERSPECTIVE,
  });
  assert.equal(resultWithOptional.status, 'matched', 'optional駒があってもmatched判定は変わらない');
  assert.equal(resultWithOptional.optionalPieces[0].present, true);
});

test('4. 駒種を間違えた場合(同じマスに別の駒) -> not_matched', () => {
  const wrongRoleAt3b = HONMINO_PIECES_GOTE.map((p) =>
    p.square === '3b' ? { ...p, role: 'gold' } : p, // 銀のはずが金
  );
  const sfen = buildSfen(wrongRoleAt3b);
  const result = matchShape(sfen, honmino, { perspectiveColor: PERSPECTIVE });

  assert.equal(result.status, 'not_matched');
  assert.equal(result.unmatchedRequiredPieces.some((p) => p.square === '3b'), true);
});

test('5. 別の場所に同じ駒があるだけではmatchedにならない', () => {
  // 3bの銀を欠いたまま、無関係の場所(7g)に銀を置く
  const misplacedSilver = [
    ...HONMINO_PIECES_GOTE.filter((p) => p.square !== '3b'),
    { square: '7g', color: 'gote', role: 'silver' },
  ];
  const sfen = buildSfen(misplacedSilver);
  const result = matchShape(sfen, honmino, { perspectiveColor: PERSPECTIVE });

  assert.equal(result.status, 'not_matched');
  assert.equal(result.unmatchedRequiredPieces.some((p) => p.square === '3b'), true);
});

test('perspectiveColorが未指定なら明示的に例外を投げる(座標視点を勝手に既定化しない)', () => {
  const sfen = buildSfen(HONMINO_PIECES_GOTE);
  assert.throws(() => matchShape(sfen, honmino, {}), /perspectiveColor/);
});
