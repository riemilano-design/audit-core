# scripts/playtest/

対局ハーネス(docs/PLAYTEST_LOOP_PROPOSAL.md の外側のループ)。**開発補助であり、本番導線(apps/)には含めない。**

現在実装済みなのは STEP T-1(固定棋譜モード)・STEP T-2(不変条件 I-1〜I-5・draft と集約報告)・STEP T-3(探索モードと対局者の多様化)。

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

## 探索モード(STEP T-3)

固定棋譜モード(replay.ts)は**回帰**用(一度記録した局面列を再生し、変更前後の検出数を比べる)。探索モードは**発見**用で、相手を本番と同一(素のエンジン、`movetime 1000`)に戻し、自分側は5プロファイル(`scripts/playtest/lib/players.ts`)のいずれかで指させることで未知の局面列を作る。

```
npx tsx scripts/playtest/explore.ts --games 10 --seed 1
npx tsx scripts/playtest/explore.ts --games 10 --seed 1 --plies 60 --out-dir /path/to/out
```

- `--games`(既定10)・`--seed`(既定1)・`--plies`(既定60。1局あたりの手数の上限)・`--out-dir`(既定 `scripts/playtest/out/explore-<startedAt>/`)
- 10局の既定の内訳: S1×2、S2×2、S3×2、E×2、R×2(`--games` が10以外の場合はこの順を繰り返す)。局ごとの種は `seed + 局番号` から決定的に導出する
- 対局者(自分側)の5プロファイル(台本はテストの入力であり、ユーザーに見せる知識でも本番の判断でもない。将棋の良し悪しを判断する規則は無い):
  - **S1(文どおり)**: 候補手が `ready` ならその最初の説明の手。無ければ道のりの最初の一手。どちらも無ければ E
  - **S2(逃げる)**: 駒が当たっている(`piece_attacked`)なら、その駒の合法手のうち移動先に相手の利きが無い手。無ければ S1
  - **S3(振り飛車定型)**: 定型序盤列を先頭から合法な手だけ消費。使い切ったら S1
  - **E(浅い読み)**: 同じエンジンプロセスに `movetime 100` で指させる
  - **R(乱択混合)**: 既定 `randomRate 0.3` で合法手から乱択、それ以外は E
- 出力: 局ごとに `game-NN.jsonl`(T-1 と同じ形式。`meta` に `mode: "explore"`・`profile`・`seed`・`randomRate`・`pliesCap` を追加)と `game-NN.kifu.json`(`{ id, source: "explore", profile, seed, moves }`。`replay.ts` でそのまま再生できる形式)。最後に `check.ts`(変更なし)を10局へ実行した結果を `report.md`・`report.json` として同じディレクトリへ書く
- 終了条件: 終局(`isGameOver`)・相手または自分のエンジンが手を返さない・`--plies` 到達。理由は各 `game-NN.jsonl` の末尾付近の `{"kind":"end","reason",...}` 行に書く

**この出力の意味について**: 探索の出力(JSONL・kifu JSON)は**観測**であり、何も拘束しない。`check.ts` の検出(=候補事象)も、既知事項・仕様・`kifu/` への登録に自動では昇格しない(docs/AGENT_PROTOCOL.md 11.)。局面列を固定棋譜として `scripts/playtest/kifu/` へ登録するかどうかは、人間の判断による。

## 不変条件チェック(STEP T-2)

T-1 が保存した JSONL(1件以上)に対して、不変条件 I-1〜I-5(`scripts/playtest/invariants/`、すべて `status: "draft"`)を適用し、検出を「型 × 発生条件」で束ねた報告を標準出力(Markdown)へ書く。常に exit 0(draft は何もブロックしない。docs/AGENT_PROTOCOL.md 11.)。

```
npx tsx scripts/playtest/check.ts scripts/playtest/out/run1.jsonl scripts/playtest/out/run2.jsonl
npx tsx scripts/playtest/check.ts scripts/playtest/out/run1.jsonl --json scripts/playtest/out/check.json
```

`--json` を指定すると、機械可読の結果(`{ inputs, invariants, findings, groups }`)も同じ内容で書き出す。

**この報告の意味について**: draft の不変条件による検出であり、仕様・既知事項・異常の有無を確定するものではない。0件は「有効な不変条件が捉える範囲では検出されない」ことを意味する(docs/AGENT_PROTOCOL.md 11. 規則5)。有効化(`approved`)・既知事項への追加・仕様変更は、この報告からは自動で起きない(人間の判断が要る)。

不変条件を追加する場合は `scripts/playtest/invariants/i*.ts` を1件追加し、`index.ts` の一覧に加える。`status` は draft のまま追加してよいが、`approved` にする操作(=STEP の完了条件に入れる)は人間承認事項(docs/AGENT_PROTOCOL.md 11.)。

## reports/(探索の集約報告の保管)

`scripts/playtest/reports/` は追跡対象(`out/` と異なり `.gitignore` されない)。探索モードの集約報告(`report.md`・`report.json`)のうち、検証材料として保持すると人間が判断したものをコピーして置く。ここに置いた候補事象は仕分け(直す/受容/持ち越す)待ちであり、既知事項・仕様への登録を意味しない。

## typecheck

```
npx tsc --noEmit -p scripts/playtest/tsconfig.json
```

## 不変条件のテスト

```
npx vitest run scripts/playtest
```
