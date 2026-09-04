// Phase 0 spike (spike/) で確認した shogiops との疎通を踏まえ、
// 「SFEN + shapes 1件 -> required_pieces との一致判定」を返す純粋関数のプロトタイプ。
//
// 目的は本美濃判定機能を完成させることではなく、
//   data(将棋知識) -> shogiops(局面) -> 判定結果
// という接続が成立することを確認すること。将棋の事実判断(この形が本美濃かどうか等)
// は data/shapes 側が既に確定した required_pieces に委ねており、本関数はそれと
// shogiops の盤面を機械的に突き合わせるだけの役割に限定する。
//
// === 座標視点についての注記 ===
// docs/DATA_MODEL.md は現在、MVPスコープにおける座標視点を確定している:
// self(自分側)=先手固定、opponent(相手側)=後手固定であり、self側の形
// (data/shapes/*.json)は先手側絶対座標で記録される(data/shapes/mino_honmino.json
// 等を参照。180度回転による変換済み)。
//
// なお data/examples/shapes.example.json はスキーマ検証用の最小サンプルであり、
// 本番データではない(docs/DATA_MODEL.md参照)。そこに含まれる座標は上記の確定
// 仕様とは無関係な旧いサンプル値であり、本ファイルの結論の根拠には使わない。
//
// 本関数は上記の確定仕様に依存させず、引き続き呼び出し側に
// perspectiveColor('sente' | 'gote': 盤面上のどちらの色の駒として
// required_pieces の座標を解釈するか)を必須で指定させる設計を維持する
// (関数を汎用に保ち、既定値を持たせないため。self側=先手固定のケースの確認は
// shape-matcher.sente-shapes.test.mjs で行っている)。

import { parseSfen } from 'shogiops/sfen';
import { parseSquareName } from 'shogiops/util';
import { japaneseToRole } from './piece-mapping.mjs';

export class ShapeMatcherError extends Error {}

/**
 * @param {string} sfen - shogiops が解釈できるSFEN文字列('startpos'可)
 * @param {object} shape - data/schemas/shapes.schema.json に準拠したshapeオブジェクト1件
 * @param {{ perspectiveColor: 'sente' | 'gote' }} options - 座標視点の明示指定(必須)
 */
export function matchShape(sfen, shape, options = {}) {
  const { perspectiveColor } = options;
  if (perspectiveColor !== 'sente' && perspectiveColor !== 'gote') {
    throw new ShapeMatcherError(
      'perspectiveColor には "sente" か "gote" を明示的に指定してください。' +
        '座標視点はdocs/DATA_MODEL.mdで未確定のため、本関数は既定値を持ちません。',
    );
  }

  const parsed = parseSfen('standard', sfen);
  if (parsed.isErr) {
    throw new ShapeMatcherError(`SFENの解析に失敗しました: "${sfen}" (${parsed.error?.message ?? 'unknown error'})`);
  }
  const pos = parsed.value;

  const matchedRequiredPieces = [];
  const unmatchedRequiredPieces = [];
  const optionalPieces = [];

  for (const requiredPiece of shape.required_pieces) {
    const square = parseSquareName(requiredPiece.square);
    if (square === undefined) {
      throw new ShapeMatcherError(`不正なマス目表記です: "${requiredPiece.square}"`);
    }
    const expectedRole = japaneseToRole(requiredPiece.piece);
    const actual = pos.board.get(square);
    const present = actual !== undefined && actual.color === perspectiveColor && actual.role === expectedRole;

    const entry = {
      piece: requiredPiece.piece,
      square: requiredPiece.square,
      expectedRole,
      actual: actual ? { color: actual.color, role: actual.role } : null,
    };

    if (requiredPiece.optional) {
      optionalPieces.push({ ...entry, present });
    } else if (present) {
      matchedRequiredPieces.push(entry);
    } else {
      unmatchedRequiredPieces.push(entry);
    }
  }

  const status = unmatchedRequiredPieces.length === 0 ? 'matched' : 'not_matched';

  return {
    status,
    shapeId: shape.id,
    matchedRequiredPieces,
    unmatchedRequiredPieces,
    optionalPieces,
    assumptions: {
      perspectiveColor,
      note: 'perspectiveColorは呼び出し側が明示した仮定であり、本関数が座標視点の仕様を確定したものではない。',
    },
  };
}
