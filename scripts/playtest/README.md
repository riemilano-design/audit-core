# scripts/playtest/

対局ハーネス(docs/PLAYTEST_LOOP_PROPOSAL.md の外側のループ)。**開発補助であり、本番導線(apps/)には含めない。**

現在実装済みなのは STEP T-1(固定棋譜モード)のみ。不変条件(T-2)・探索モード(T-3)・対局者の多様化はまだ無い。

## 位置づけ

- 本番関数(`apps/server/src/` の既存export)を import して呼ぶだけで、複製・改変はしない。
- 将棋の判断・評価・閾値・文言はここでは一切書かない。
- 出力(JSONL)は記録用。**コミットするかどうかは人間の指示による**(`scripts/playtest/out/` は `.gitignore` 済み)。

## 使い方

```
npx tsx scripts/playtest/replay.ts scripts/playtest/kifu/2026-09-10-claude-10moves.json
npx tsx scripts/playtest/replay.ts scripts/playtest/kifu/2026-09-10-claude-10moves.json --out /path/to/out.jsonl
```

エンジン(`apps/server/engine/YaneuraOu-by-gcc`、`resolveEnginePath()` が解決)を実際に起動する。`--out` を省略すると `scripts/playtest/out/<kifuId>-<timestamp>.jsonl` に書く。

## 固定棋譜(kifu.json)の形式

```json
{
  "id": "任意のID",
  "source": "出典(自由記述)",
  "moves": ["先手の手", "後手の手", "先手の手", "後手の手", ...]
}
```

先手(自分)から始まり交互。相手側の手は本物のエンジンに問い合わせず、記録済みの手をそのまま返す偽エンジンで適用する(`playOpponentMove` へは承認済みvariantを渡さず空配列 `[]` を渡す。将来variantが承認されても再生が変わらないための防御)。

## JSONL の形式

- 先頭行: `{"kind":"meta", "kifuId", "startedAt", "gitHead", "enginePath"}`
- 各記録行: `{"kind":"record", "ply", "sfen", "senteMove", "goteMove", "phase":"immediate"|"ready", "elapsedMs", "response"}`(`response` は `buildStateResponseWithPlan` の戻り値そのまま。web が受け取るのと同じ形)
- 想定内エラー(非合法手・相手の手の不一致)の場合: `{"kind":"error", ...}` を書いて exit 1
- 末尾行(正常終了時のみ): `{"kind":"summary", "plies", "totalMs", "readyMsPerPly"}`

## typecheck

```
npx tsc --noEmit -p scripts/playtest/tsconfig.json
```
