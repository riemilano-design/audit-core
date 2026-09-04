import { test } from 'node:test';
import assert from 'node:assert/strict';

import { rotateSquare180, InvalidUsiSquareError } from './usi-coordinates.mjs';

test('180度回転: 筋はn->10-n、段はa<->i対称に変換される', () => {
  assert.equal(rotateSquare180('2b'), '8h');
  assert.equal(rotateSquare180('3b'), '7h');
  assert.equal(rotateSquare180('4a'), '6i');
  assert.equal(rotateSquare180('5b'), '5h');
  assert.equal(rotateSquare180('5e'), '5e'); // 中心のマスは回転しても不変
});

test('180度回転は自己逆変換(2回適用すると元に戻る)', () => {
  for (const square of ['1a', '9i', '5e', '2b', '8h']) {
    assert.equal(rotateSquare180(rotateSquare180(square)), square);
  }
});

test('不正なマス目表記は例外を投げる', () => {
  assert.throws(() => rotateSquare180('0a'), InvalidUsiSquareError);
  assert.throws(() => rotateSquare180('10a'), InvalidUsiSquareError);
  assert.throws(() => rotateSquare180('2j'), InvalidUsiSquareError);
  assert.throws(() => rotateSquare180('2二'), InvalidUsiSquareError);
});
