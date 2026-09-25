# 役 L-分かれ道(2 周目・第 2 陣。回し直し)への入力(2026-09-26)

共通の指示は `01b-input-common.md`。**先にそれを読むこと**。ここには、あなたの役に固有のことだけを書く。

## あなたの役
- `lane`: `"fork"`。ファイル名の `<レーン>` は `fork`。

## なぜ回し直すか(事実)
第 1 陣に渡した写しでは、**あなたの中心の材料である `obs.time.decisionContext` の `fork` の列が 182 行すべて `null`** だった(レーン長が道具に `--whatif-v2-dir` を渡していなかったため。レーン長の手落ち)。作り直した写し `…r2b.json` では **真 107・偽 56・null 19**。他の列と `obs.geo.moveCombination`(580 行)は**すべて同一**(機械で照合済み)。

## 問い

> **「攻めと守りのどちらへ行くかで分かれる局面」で、この人はどちらを選んでいるか。選び方は、崩れ・評価の帯・段・相手の直前の手と関係があるか。**

## 「分かれ道」の決め方(道具の定義。あなたが決めるのではない)
**正本の定義**: **実戦の手が第 1 候補との差が大きい(600cp 以上)か、候補 5 つに入らなかった局面**(`docs/OBSERVATION_ITEMS.md` §1 の `obs.fork.representative`。顧客に送付済みの冊子の「数え方」にもこの読みで書いてある)。
- 第 1 陣の指示文はここを「第 1 候補と実戦の手の**側**が違う局面」と書いていたが、**これは誤り**(レーン長の書き間違い。統括が正本を確かめた)。側が違うかどうかは**分かれ道の中で何が起きたか**の話で、分かれ道そのものの定義ではない。
- 側の定義は別の欄にある(**自玉から 2 マス以内に利く手 = 自玉側、相手玉から 3 マス以内・取る・王手 = 攻め**。`obs.fork.values` に道具の定義が入っている)。**どちらの定義も言い換えたり、別の基準を持ち込んだりしない。**

## 使ってよい観測
- **中心**: `obs.fork.values`・`obs.fork.game`・`obs.fork.representative`・`obs.fork.scene`・`obs.fork.summary`、および **`obs.time.decisionContext` の `fork` の列**(5〜9 秒・10 秒以上の手について、分かれ道だったかが `collapse`・`phase`・`evalBand` と同じ行に並んでいる)
- 併せて: `obs.geo.moveCombination`(`side`・`facts`)、`obs.geo.replyToCapture`・`obs.geo.replyToCheck`、`obs.direct.*`、`obs.eval.*`、`obs.report.event`・`obs.report.escapeScene`
- `obs.menu.*` は読んでよいが仮説の根拠にしない

## 分母に気をつける(P-89。2026-09-26)
写しの **`obs.direct.answer` は 161 行(3 分の組だけ)だが、`obs.direct.counts` の集計は組で絞られていない**(納品の 20 局ぶん = 3 分 161 + 10 分 6 = `totalCount` 167、`gamesCount` 18、`totalForkCount` 277 は別の数え方)。**この 2 つを同じ分母として並べないこと。** 組で絞った数が要るときは `obs.direct.answer` の行から数え、その旨を `observations[].path` に残すこと。

## この周の材料について(事実。ここから数を読むこと)
`decisionContext` は **182 行**、`fork` は **真 107・偽 56・null 19**。**`null` を「分かれ道ではない」と数えない**(「測れていない」と扱う)。分母が小さい値で強い読みを立ててもよいが、`prediction.alsoRequires` に確かめるのに要る局数・件数を必ず書くこと。**この前書きの数をそのまま文に書かず、写しの `value` から引き直すこと**(`observations[].path` を付ける必要がある)。
