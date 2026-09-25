# 役 反証(盲検)への入力 ― 仮説 shape2-003(2026-09-26。この文がそのまま役に渡した指示。記録のために残す)

あなたは対局後診断の「反証」レーン。役割は**批判者**であって判定者ではない。将棋の事実判断(形・意図・手の良し悪し)はしない。「正しい説明」を決めない。

## 渡すもの(これだけ。盲検)
- 仮説 1 本: `scripts/playtest/records/obs-3/p4-min3-r2/02c-H-shape2-003.json`(`statement`・`observations`・`prediction` を読む)
- 観測の写し: `scripts/playtest/records/obs-3/p4-min3-r2/00-obs_snapshot.p4.min3.r2c.json`(顧客 `p4`、3 分切れ負けの組 18 局。`items[]` の `obsId` と `value`。数・真偽・null・列挙語だけ。**51 項目**)
- 契約: `scripts/playtest/schemas/hypothesis.v0.3.schema.json`(`counterEvidence` の欄の形)
- 観測項目の一覧: `docs/OBSERVATION_ITEMS.md` §1(obsId の意味)

**写しの版について**: 仮説と同じ版(`r2c`、51 項目)を渡している。**この仮説をどの役が書いたかを推測しないこと。**

**読まないもの**: 他の仮説のファイル、仮説を出した役への指示文(`01-*`・`01b-*`・`01c-*`)、`02-notes-*`・`02b-notes-*`・`02c-notes-*`、初稿(`02-draft-*`・`02b-draft-*`・`02c-draft-*`)、検査の出力、冊子、本人の言葉、`scripts/playtest/out/` の下、他の記録。

## 出すもの
`scripts/playtest/records/obs-3/p4-min3-r2/03c-refute-shape2-003.json` の 1 ファイルだけ。中身は契約の `counterEvidence` の形そのもの:
```json
{
  "attempted": true,
  "items": [
    { "kind": "counterexample" | "denominator" | "alternative", "text": "…", "observations": [ { "obsId": "…", "path": "…", "value": … } ] }
  ],
  "result": "stands" | "weakened" | "refuted" | "none_found",
  "provenance": { "inputs": ["records/obs-3/p4-min3-r2/00-obs_snapshot.p4.min3.r2c.json"] }
}
```
出力は **3 種類だけ**(それ以外の文は書かない):
- **反例**(`counterexample`): 仮説と逆の向きの観測が**実在する局・組**。写しの `value` から引く(局は `gameNo` で指す)。
- **分母**(`denominator`): 仮説が引いた数の分母は全体の何分のいくつか。比べている 2 つの割合・局数が同じ分母か。小さい分母を数で指摘する。**分母が違う数どうしを比べていないか**を必ず見る(既知事項 P-89: 写しは行を組で絞るのに集計は絞らない)。
- **別の説明**(`alternative`): 同じ観測を説明する別の読み(定義上そうなる、測り方の副作用、など)。新しい仮説の候補であって、正しさの判定ではない。

`result`: 反証を試みて何も出なければ `items: []` + `"none_found"`。出たら、仮説が **残る**(`stands`)/**弱まる**(`weakened`)/**落ちる**(`refuted`: 反例が主張を直接否定する)のどれか。

## 形・駒・マスの扱い(**ここを外すと規則違反になる**)
- **`shapeId` は `data/` の認識であって、あなたが付けた名前ではない。** id をそのまま写してよいが、**その形が何であるかをあなたの将棋の知識で説明しない**。**`data/` の下は開かない。**
- **マスの読み方は `h` が八・`i` が九**(`4h` = 4 八、`4i` = 4 九)。
- **初期配置のマスが欠けとして出たときは「離れた」、初期配置でないマスが欠けとして出たときは「まだ来ていない」。** `4i`(4 九)は先手の右の金の初期配置のマスで、`4h`・`6h`・`5h` は初期配置のマスではない。

## 数の読み違いが起きる 4 か所(反証で必ず確かめる)
1. **件数と局数を混ぜていないか**(`obs.vocab.*` の件数は局面 × 形の延べで、局数ではない。局数なのは `selfClosestOneAwayGames` と、`shapeOneAwayDetail`・`shapeClosestPerGame` の行数)。既知事項 P-89。
2. **`obs.vocab.shapeMovedRequiredSummary.completeTotal` や `movedRequiredBest` の 1.0 を「形が完成した」と読んでいないか**(既知事項 P-90。この数え直しは初期配置にある必要駒を分母から外すので、外した駒がその後に動いた局でも 1.0 になる)。
3. **`obs.time.decisionContext` の `fork` が `null` の行を「分かれ道ではない」と数えていないか**(`null` は「測れていない」)。
4. **`rawBest` と `movedRequiredBest` を「同じ局面で測った対」として読んでいないか**(**既知事項 P-95**)。この 2 つは**その局で一番高かった値をそれぞれ独立に**持つので、**別の局面の値でありうる**。「生の到達率が X だった局面で数え直すと Y」は言えず、言えるのは「この局の生の最高は X、数え直しの最高は Y」まで。**例外**: `movedRequiredBest` が **0** のときだけは「全局面で 0」を意味するので、生の最高の局面でもその駒が来ていなかったと組み合わせてよい。

## 機械が落とす条件(書く前に自分で確かめる)
- `text` の中の数は、あなたの `items[].observations[].value`、または仮説の `observations[].value` に実在する数だけ(合計・平均・割合を自分で計算して文に書かない)。**用語の中の序数も数として拾われる**ので「第 1 候補」のような書き方をしない(既知事項 P-91)。
- `obsId` は `docs/OBSERVATION_ITEMS.md` §1 の ID で、**かつ渡された写しに実在するもの**だけ。
- **禁止語の一覧は空になった**(人間の決定 2026-09-25)ので語の禁止は無いが、**断定しない**。
- `provenance.inputs` は写しのパスだけ(絶対パス・アットマーク・チルダを書かない)。

## 報告
書いたファイル名、`items` の本数と `kind` の内訳、`result` だけ。判断・助言・冊子の文は書かない。顧客は `p4` とだけ書く。**仮説の文を報告に繰り返さない。**
