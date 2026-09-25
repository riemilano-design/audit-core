# L-分かれ道(`lane: "fork"`)の覚書 ― 2 周目・第 2 陣(回し直し。2026-09-26)

材料は `records/obs-3/p4-min3-r2/00-obs_snapshot.p4.min3.r2b.json`(顧客 `<p4>`、3 分の組、18 局、48 項目)だけ。
第 1 陣の出力(`02-H-*`・`02-draft-*`・`02-notes-*`)と 1 周目の記録は読んでいない。

**この覚書で使う言葉の出どころ**(自分で言い換えていない):

- **分かれ道** = 実戦の手が第 1 候補との差が大きい(`obs.fork.values.minLossCp` = 600)か、候補 5 つに入らなかった局面(`obs.fork.representative` の正本の定義)。
- **側** = 自玉から 2 マス以内に利く手が自玉側(守り)、相手玉から 3 マス以内・取る・王手が攻め(`obs.fork.values` の `sideZoneRadius` = 2・`attackZoneRadius` = 3、`sideVersion` = 2)。`both`・`none` は側の分母に入らない。
- `obs.time.decisionContext` の `fork` が **`null` の行は「分かれ道ではない」ではなく「測れていない」**。182 行のうち 19 行がこれ。

**分母の注意(P-89)**: `obs.direct.answer` は 3 分の組で絞った 161 行(17 局にまたがる)。`obs.direct.counts` の集計(`totalCount` 167・`totalForkCount` 277)は組で絞られていないので、同じ分母として並べていない。以下の数はすべて `obs.direct.answer` の行、または `obs.time.decisionContext` の行を数え直したもので、どの絞り込みで数えたかは各仮説の `observations[].path` に書いた。

---

## 仮説 001(`02b-H-fork-001.json`)

### 1. 観測した事実

| 数 | obsId | パス(絞り込み) |
|---|---|---|
| 182 | `obs.time.decisionContext` | `decisionContext[]` の行数(5〜9 秒・10 秒以上の帯の手) |
| 107 / 56 / 19 | `obs.time.decisionContext` | `fork === true` / `=== false` / `=== null` の行数 |
| 51 | `obs.geo.moveCombination` | `(gameNo, kifPly)` で突き合わせ、`fork === true` かつ `side === "attack"` |
| 23 | `obs.geo.moveCombination` | 同上で `side === "defense"` |
| 29 / 4 | `obs.geo.moveCombination` | 同上で `side === "none"` / `"both"`(側の分母に入らない) |
| 25 / 17 | `obs.geo.moveCombination` | `fork === false` の側の内訳(attack / defense) |
| 161 | `obs.direct.answer` | 3 分の組で絞った行数 |
| 38 / 11 | `obs.direct.answer` | `top1Side === "attack"` × `actualSide === "attack"` / `"defense"` |
| 21 / 17 | `obs.direct.answer` | `top1Side === "defense"` × `actualSide === "attack"` / `"defense"` |
| 8 | `obs.geo.moveCombination` | `fork === true` かつ `collapse === true` |
| 6 / 0 / 1 | `obs.geo.moveCombination` | そのうち `side === "attack"` / `"defense"` / `"both"` |
| 84 | `obs.time.decisionContext` | `fork === true` かつ `collapse === null`(崩れが測れていない) |
| 2・3・600 | `obs.fork.values` | 側と分かれ道の定義に使われた値 |

### 2. そこからの推論

側が付いた分かれ道の行は 51 + 23 = 74 行で、そのうち攻め側が 51。分かれ道でない行(25 対 17)より攻め側へ寄りが大きい。
さらに `obs.direct.answer` の突き合わせでは、第 1 候補が攻め側のときに攻め側を選んだのが 38・守り側を選んだのが 11 なのに対し、第 1 候補が**守り側**のときも攻め側 21・守り側 17 で、選んだ側が第 1 候補の側にあまり追随していない。
つまり「どちらへ行くか」の選択は、そのときの第 1 候補が示す向きではなく、この人の側への寄りで説明できる余地がある、と読んだ。
崩れの旗が真だった 8 行の側の内訳(攻め 6・守り 0)も同じ向きだが、これは 107 行のうち 84 行で崩れが測れていない中の 8 行にすぎない。

### 3. 仮説

`02b-H-fork-001.json` の `statement` と同じ(ここには繰り返さない)。

### 4. 不確実性

- **「攻め側」は幾何の定義で、取る手・王手・相手玉から 3 マス以内をすべて含む。** 攻め側 51 行の内訳は取る手 14・王手 3・打つ手 22。取り返しが攻め側に流れ込んで数を膨らませている筋は残るが、51 のうち取る手は 14 なので、それだけでは説明しきれない。
- `fork === true` の 107 行のうち 33 行(`none` 29・`both` 4)は側が付かず分母から外れている。**「攻め寄り」は側が付いた手の中の話**で、分かれ道全体の話ではない。
- `fork` が `null` の 19 行は測れていない。19 行すべてが守り側だった場合、寄りは今より小さく見える。
- `obs.direct.answer` は分かれ道のうち差が測れて局面つきで見える行だけ(161 行・17 局)で、分かれ道の全体ではない。`obs.direct.answer` と `obs.time.decisionContext` は**別の数え方の別の母集団**なので、2 つの一致率を並べて比べていない。
- 崩れの 8 行は小さすぎる。守り側 0 は「守り側では崩れない」ではなく「そもそも崩れの旗が真の行が 8 しかない」。
- 足りない観測: 分かれ道 1 行ごとの「そのとき守り側に合法手があったか」。`obs.fork.summary.sideCompare` は代表局面の集計で `attackNoLegalMove` 26・`defenseNoLegalMove` 0(`scenesRead` 288)しか持たず、行ごとには引けない。攻め側の手が選べない場面が 26 あることは、逆向きの偏りの材料になりうる。

---

## 仮説 002(`02b-H-fork-002.json`)

### 1. 観測した事実

| 数 | obsId | パス(絞り込み) |
|---|---|---|
| 107 | `obs.time.decisionContext` | `fork === true` の行数 |
| 11 / 59 / 37 | `obs.time.decisionContext` | `fork === true` かつ `phase === "early"` / `"mid"` / `"late"` |
| 3 / 4 | `obs.geo.moveCombination` | `fork === true`・`phase === "early"` の `side === "attack"` / `"defense"` |
| 26 / 15 | `obs.geo.moveCombination` | 同 `phase === "mid"` |
| 22 / 4 | `obs.geo.moveCombination` | 同 `phase === "late"` |
| 33 | `obs.geo.moveCombination` | `fork === true` で `side` が `none` か `both`(側の分母に入らない) |
| 16 / 19 | `obs.time.decisionContext` | `fork === null` のうち `phase === "early"` / `fork === null` の全体 |

### 2. そこからの推論

側が付いた分かれ道を段で割ると、序盤は 3 対 4(守り側がわずかに多い)、中盤は 26 対 15、終盤は 22 対 4。段が進むほど攻め側の比が上がっている。
段が進むと相手玉に近い升へ手が届くようになるので、**同じ指し方でも幾何の定義上「攻め側」に数えられやすくなる**可能性と、**選び方そのものが変わっている**可能性の両方がある。この材料だけではどちらとも決められない。ただし数の向きははっきりしている。

### 3. 仮説

`02b-H-fork-002.json` の `statement` と同じ。

### 4. 不確実性

- **序盤の分母が小さい**(3 + 4 = 7 行)。`fork === null` の 19 行のうち 16 行が序盤に集まっており、序盤はそもそも測れていない行が多い。序盤の比は次の 20 局で簡単に動く。
- 段(`phase`)の切り方は道具が決めたもので、この覚書では言い換えていない。段の切り方が変われば内訳も変わる。
- 上の「幾何の定義上、終盤ほど攻め側に数えられやすい」という交絡は、この写しの中では切り分けられない。切り分けるには、段ごとに「相手玉から 3 マス以内に届く合法手の数」が要るが、写しにその欄は無い。
- `decisionContext` は 5〜9 秒・10 秒以上の帯の手だけで、4 秒以下の手は入っていない。速く指した手は段によらず数えられていない。

---

## 仮説 003(`02b-H-fork-003.json`)

### 1. 観測した事実

| 数 | obsId | パス(絞り込み) |
|---|---|---|
| 182 | `obs.time.decisionContext` | 行数 |
| 16 | `obs.time.decisionContext` | `oppPrevGivesCheck === true`(`inCheck === true` も同じ 16 行) |
| 2 / 14 | `obs.time.decisionContext` | そのうち `fork === true` / `=== false`(`null` は 0) |
| 14 / 19 | `obs.time.decisionContext` | `oppPrevDrop === true` の `fork === true` / `=== false` |
| 93 / 37 | `obs.time.decisionContext` | `oppPrevDrop === false` の `fork === true` / `=== false` |
| 42 / 21 | `obs.time.decisionContext` | `oppPrevCapture === true` の `fork === true` / `=== false` |
| 65 / 35 | `obs.time.decisionContext` | `oppPrevCapture === false` の `fork === true` / `=== false` |
| 19 / 17 | `obs.time.decisionContext` | `fork === null` の全体 / そのうち `oppPrevDrop === false` |
| 58 / 46 | `obs.geo.replyToCheck` | `replyToCheck` が「王手ではない」以外の行数 / そのうち「玉を動かす」 |

### 2. そこからの推論

相手の直前の手が王手だった 16 行では、分かれ道は 2 しかない(`fork === null` は 0 なので、この 16 行は全部測れている)。
相手が駒を打った直後も、分かれ道 14 対 分かれ道でない 19 で、打っていないとき(93 対 37)と向きが逆になっている。
一方、相手が駒を取った直後(42 対 21)と取っていないとき(65 対 35)は向きが変わらない。
`obs.geo.replyToCheck` では、王手がかかった 58 行のうち 46 行が玉を動かす手。**選べる手が絞られている場面では、そもそも「第 1 候補と 600 以上離れた手」や「候補 5 つに入らない手」になりにくい**、と読んだ。
これは「この人がどちらを選ぶか」ではなく「そもそも分かれ道が立つ場面がどこか」の話なので、仮説 001・002 の分母の性質を説明する側の読みになる。

### 3. 仮説

`02b-H-fork-003.json` の `statement` と同じ。

### 4. 不確実性

- 王手の 16 行・打ちの 33 行(14 + 19)はどちらも小さい。次の 20 局で入れ替わりうる。
- 「選べる手が絞られている」は**合法手の数を測っていない**読み。写しに合法手の数の欄は無く、`obs.geo.replyToCheck` の「玉を動かす」46 行から間接に読んでいるだけ。
- `replyToCheck` は 580 行(帯で絞っていない全手)で数えており、`decisionContext` の 182 行とは母集団が違う。**この 2 つの割合を並べて比べていない。**
- `fork === null` の 19 行のうち 17 行は `oppPrevDrop === false` の側にある。打っていないときの比(93 対 37)は、測れていない行がどちらに転ぶかで動く。
- 逆の読み: 王手のあとに分かれ道が少ないのは「選べる手が少ない」からではなく、**エンジンの候補 5 つの中に実戦の手が入りやすい**からかもしれない。切り分けるには王手中の行の `actualGapCp` が要るが、`obs.direct.answer` に `inCheck` の欄が無く、行ごとに突き合わせられない。

---

## 行動候補(承認外・内部)

> ここに書くのは**本人がこれから試せる手順**だけ。承認済みの行動の表(`answer_menu`)には当てはめていない(それは後段の別の役の仕事)。

- `[承認外]` 仮説 001: 分かれ道で手を決める前に、**相手玉から 3 マス以内へ行く手を 1 つと、自玉から 2 マス以内へ行く手を 1 つ、両方を口に出してから**どちらを指すかを決める、を 20 局続けてみる。数としては `obs.geo.moveCombination` の `side === "defense"` の行数が増えるかを見る。
- `[承認外]` 仮説 001: 対局後に、第 1 候補が守り側だった分かれ道(`obs.direct.answer` で `top1Side === "defense"`)の局面だけを並べて、自分の手と候補の手の**行き先の升**を見比べる。
- `[承認外]` 仮説 002: 終盤(`phase === "late"`)に入ったと自分で思った手から、**自玉から 2 マス以内の升に利いている自分の駒の数を数えてから指す**、を 20 局続けてみる。数としては終盤の `side === "defense"` の行数を見る。
- `[承認外]` 仮説 003: 相手に王手をかけられた手・駒を打たれた手は**分かれ道として数えられにくい**ので、振り返りのときはその直後の手ではなく、**その 1 つ手前の自分の手**を見る。

---

## 機械の検査(`npx tsx scripts/playtest/hypothesisCheck.ts <ファイル> --today 2026-09-26`)

3 本とも `schema`・H-1・H-2・H-4〜H-8 は ok、**H-3 だけ NG**(`counterEvidence.attempted` が true でない)。
これは共通の指示のとおり**この段では NG が正しい**(反証は別の役が盲検で行う)ので直していない。
