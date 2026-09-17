# STEP D2.6 計画: 物差しを足す ― 本人の手そのものの事実(2026-09-17)

**状態**: 計画(下書き。司令塔 e3 の依頼)。**スコープの追加は人間が 2026-09-17 に承認**(D3-COND 計画 §14 の「人間の決定」(2)、§13 の (c))。司令塔の決定 1〜7(依頼の文)を写した。**司令塔の決定(版 `8c111855`): Q-1〜Q-9 はすべて推奨どおり**。**事前読み B(sgogi-coach-ed)の REVISE(版 `8c111855`、R-1〜R-5 と軽微 3 点)を司令塔の決定(R-2・R-5)で取り込んだ**(§11)。**実装しない。エンジンは使わない。**
**書いた人**: A(sgogi-coach-64)。基点 HEAD `a8e8bd7`。根拠は `docs/STEP_D3-COND_PLAN_2026-09-15.md` §13・§14、`docs/STEP_D2.5_PLAN_2026-09-15.md`(区域の定義)、`docs/STEP_D4_PLAN_2026-09-15.md` §3 の Q-4(読み筋の側の置き換え)と §5 の G-3。
**言葉**: 欄の名前と値は事実だけ(「良い・悪い」「攻め・守り」「緩い・急ぐ」を入れない)。解釈の欄は、あとで条件式(D3)が事実の欄から作る。

## 0. 実物から分かった前提

| # | 事実 | 場所 |
|---|---|---|
| E-1 | **反事実の 2 本は同じ根から同じ関数で作られる**: `counterfactualOf` は直前の ready 行の `sfen` を根にし、実戦は `moves[branchPly − 1 …]`、読み筋は `focus_baseline`・multipv 1 の `pv` を、どちらも先頭から `comparedPlies` 手だけ `sequenceFacts(rootSfen, 手順, branchPly)` に渡す。`state: "compared"` になるのは読み筋の使える手数が 1 以上のときだけなので、**compared の組では読み筋の 1 手目(`pvFirstMove` = `pv[0]`)は根で指せる手**。実戦の 1 手目は棋譜の手(= 組の `moves.userMove`)。`pvFirstMoveIsPlayedMove` が既にある | `scripts/playtest/lib/counterfactual.ts` の `counterfactualOf`・`sequenceFacts` |
| E-2 | 根は本人の手番(記録は本人 = 先手に回してある。後手の局は `mirrored`)。したがって「自玉」= 先手玉、「相手玉」= 後手玉で、D2.5 の `ownKingZone`・`opponentKingZone` と同じ向き | `lib/sideAlignment.ts`・D2.5 計画 §1 |
| E-3 | **区域の定義は `positionFacts.ts` の `zoneOf`(玉の升 + 盤の中の 8 近傍)で、関数は export されていない**。利きは shogiops の `attacks(piece, square, occupied)`。**線の駒は `occupied` で止まり、止めた升を含む**。歩・金などの利きは占有に依らず、駒のある升も含む。玉の利きは数えない(D2.5 Q-7、人間承認) | `scripts/playtest/lib/positionFacts.ts` の `zoneOf`・`reachesOf` |
| E-4 | 条件式の読める欄の表は `sequenceFields("actual")`・`sequenceFields("pv")` が同じ葉を 2 回並べ、門はどちらも `counterfactual.state = compared`。**読み筋の側の判定は `counterfactual.actual.` を `counterfactual.pv.` に置き換えて同じ `evaluate` を当てる**(D4 §3 の Q-4)。したがって `SequenceFacts` に足した欄は、表に葉を足せば両側で自動で比べられる | `scripts/playtest/lib/condition.ts` の `sequenceFields`・`judgeConditionPvSide` |
| E-5 | **C-1「逃げ道が減る」は G-3 で根拠不足**: 揃えた集合 706 組で実戦の側 110・読み筋の側 66(0.60)。見た欄の族(王手・取った駒・玉の周り・逃げ道・区域の駒と利き)は、どれも**実戦・読み筋の手順を N 手進めた後の盤**の事実で、単独で G-3 を満たすものは無かった。N の内訳は 2 が 401・4 が 12・6 が 293 | D3-COND 計画 §13 の 1.・§14 の D-1 |
| E-6 | 反事実を持つスキーマは Failure Event v0.4〜v0.6 と diagnosis-moment v0.1〜v0.3。diagnosis-condition・diagnosis-gate・diagnosis-report は反事実の欄を持たない(`kingEscapesEnd` の出現数で確かめた) | `scripts/playtest/schemas/` |
| E-7 | USI の手は `shogiops/util` の `parseUsi`(`apps/server` で使っている)。打つ手は `P*5e` の形、成る手は末尾 `+` | `apps/server/src/analysis/boardEventDetector.ts`・`captureSummary.ts` |
| E-8 | D2 の `capturedRoles` の駒種は**元の駒種**(成駒は成る前の駒種で数える) | `lib/counterfactual.ts` の `RoleCounts` |
| E-9 | 版の規則: 任意の欄を足す = MINOR、既存の列挙に値を足す = MAJOR。古い版のスキーマと検証器は残す。今の版は Failure Event 0.6・diagnosis-moment 0.3(`lib/schemaVersions.ts` の 1 か所) | JSON v0 計画 §3.2・`lib/schemaVersions.ts` |

## 1. 足す欄(`userMoveFacts`。**根の局面で指す手 1 つについての事実**)

局面 → 事実の純粋関数 `moveFactsOf(sfen, moveUsi, rules): UserMoveFacts`(新しい `scripts/playtest/lib/moveFacts.ts`)。`sfen` は手を指す前の局面(根)、`moveUsi` は USI の手。区域は `positionFacts.ts` の区域の関数をそのまま使う(§2)。**合法でない手は例外**(compared の組では起きない ― E-1)。

| # | 欄 | 型 | 定義 | null・門 |
|---|---|---|---|---|
| U-1 | `role` | 駒種(shogiops の `Role`) | 動かした駒の、**指す前の**駒種(成る手でも成る前。打つ手は打った駒種) | null なし |
| U-2 | `drop` | boolean | 持ち駒を打った手か | null なし |
| U-3 | `capturedRole` | 駒種 \| null | 取った駒の、**取られる前の盤の上の**駒種(成駒は成駒のまま。Q-2)。**null = 取っていない**(値の null) | null は値 |
| U-4 | `promotion` | boolean | 成った手か(USI の末尾 `+`)。「成れるのに成らなかった」は数えない | null なし |
| U-5 | `kingMove` | boolean | 玉を動かした手か(`role === "king"` と同じ値。条件式が 1 つの欄で読めるように置く) | null なし |
| U-6 | `fromInOwnKingZone` | boolean \| null | 動かす前の升が、**指す前の盤**の自玉の区域にあるか | **null = 値を決められない**(打つ手 = 動かす前の升が無い / 指す前の盤に自玉が無い。どちらかは同じ行の `drop` で読める)。表では**門 `drop` が false** を先に見る(§5) |
| U-7 | `toInOwnKingZone` | boolean \| null | 動かした後の升が、**指した後の盤**の自玉の区域にあるか(玉を動かした手は新しい玉の位置で区域を作る) | null = 指した後の盤に自玉が無い(判定不能) |
| U-8 | `toInOpponentKingZone` | boolean \| null | 動かした後の升が、指した後の盤の相手玉の区域にあるか | null = 指した後の盤に相手玉が無い(判定不能) |
| U-9 | `ownKingZoneReachBeforeMinusAfter` | 整数 \| null | **動かした駒 1 枚だけ**について、自玉の区域の升のうち利きが届く升の数の「指す前 − 指した後」。指す前は指す前の盤(占有・区域)で元の升から、指した後は指した後の盤(占有・区域・成った後の駒種)で行き先の升から数える。**打つ手の「指す前」は 0**(持ち駒は利かない ― D2.5 の「持ち駒を数えない」と同じ。Q-3)。正の値 = 届く升が減った | **null = 値を決められない**(玉の手 = 玉の利きは数えない ― D2.5 Q-7 / 指す前か指した後の盤に自玉が無い。どちらかは同じ行の `kingMove` で読める)。表では**門 `kingMove` が false** を先に見る(§5) |

- **門で判定不能にする欄の行の値(R-2、司令塔の決定)**: U-6・U-9 は、打つ手・玉の手でも行に **null** を置く(スキーマは `boolean | null`・`integer | null` のまま)。null が 2 つの意味を持つが、同じ行の `drop`・`kingMove` で区別できる。条件式の判定は表の門で先に落ちる(判定不能の理由の種類は gate)。自玉が無いときは門を通って null に当たる(理由の種類は null)
- **この STEP で数えないもの**: 動かした駒のほかの駒の利きの変化(線を開けた・塞いだ)は U-9 に入れない(盤全体の変化は D2.5 の `positionFacts` の差で読める)。王手の有無は D2 の `checks` にある。「攻め・守り・逃げ・受け」のような役割の欄は作らない(§9)

## 2. どこに足すか

- **`scripts/playtest/lib/moveFacts.ts`(新規)**: `moveFactsOf(sfen, moveUsi, rules)`。`rules` は `PositionFactsRules` を受ける(区域の形・利きを当てる駒の規則を D2.5 と共有し、既定値を置かない)
- **`scripts/playtest/lib/positionFacts.ts`(既存)**: 区域の関数を export する(名前は `kingZoneOf(pos, color, rule)` の形。中身は今の `zoneOf` のまま、`positionFactsOf` の出力は変えない)。利きは同じ `attacks` を使う
- **`scripts/playtest/lib/counterfactual.ts`(既存)**: `SequenceFacts` に `userMoveFacts: UserMoveFacts` を足し、`sequenceFacts(rootSfen, moves, branchPly)` の中で `moveFactsOf(rootSfen, moves[0], POSITION_FACTS_RULES)` を 1 回呼ぶ(**渡された手順が空なら例外**。compared の組では実戦・読み筋とも 1 手以上ある ― E-1)。**実戦の側と読み筋の側はどちらも `sequenceFacts` を通るので、同じ関数が両方に当たる**(司令塔の決定 1)。`pvMinusActual` には差を足さない(真偽と駒種は差が取れない。比べは G-3 の置き換えで行う)
- **Failure Event・diagnosis-moment・全ての手の組(D4)**: `counterfactual` を共有しているので、`compared` の行すべてに入る(組の行は `allPairsOf` がそのまま運ぶ)。**`compared` でない組(材料の側で 734 − 706 = 28 組)には無い**(§9 の限界)
- **`scripts/playtest/lib/condition.ts`(骨組みの変更 = 監査)**: `sequenceFields(side)` に U-1〜U-9 の葉を足す(§5)。置き換えの規則(`counterfactual.actual.` → `counterfactual.pv.`)は変えない
- **記録(4M の JSONL)は変えない**。欄は局面と手から計算するので、古い記録から作れる。エンジンは要らない
- **Markdown**(`counterfactualLines`)と D6 の文は変えない(Q-7)

## 3. この物差しで G-3 が効く理由

- G-3 は、同じ条件式を「実戦の側」と「読み筋の側」に当て、読み筋の側で真になる組が実戦の側の半分以下であることを求める(`2·p ≤ a`、揃えた集合 n で)。**読み筋の側も同じくらい真になる事実は、本人の選択に固有とは言えない**、という歯止めである
- 今までの欄(E-5)は、**手順を N 手進めた後の盤**の事実だった。N 手には相手の手と、その後の手が入る。実戦の側も読み筋の側も、根の局面の性質(玉の形・相手の駒)に強く引っ張られるので、両側で似た率になった(C-1 は 110 と 66)
- `userMoveFacts` は、**根の局面で指した手 1 つ**だけの事実である。実戦の側は本人の手、読み筋の側は探索の 1 手目で、**根も関数も同じで、違うのは手だけ**。したがって両側の率の違いは、そのまま「本人が選んだ手」と「探索が選んだ手」の違いになる。窓の長さ N にも依らない(E-5 の N の違いの問題が起きない)
- **本人の手と読み筋の 1 手目が同じ組**(`pvFirstMoveIsPlayedMove` が真)では、`userMoveFacts` の値は両側で必ず等しい。揃えた集合 n のうち、同じ手の組の中で条件式が真になる組の数を s、手が違う組の中で実戦の側・読み筋の側が真になる数を a′・p′ とすると、a = s + a′、p = s + p′ で、**G-3(`2·p ≤ a`)は `a′ ≥ s + 2·p′`** と書ける。つまり G-3 を満たすには、条件式が「本人が探索と違う手を選んだ組」で真になる数が、読み筋の側の 2 倍に、同じ手の組で真になる数 s を足した数**以上**でなければならない。この物差しの G-3 は、「本人が探索と違う手を選ぶときの手の性質」を問う形になる
- **この分解が成り立つ範囲(R-3)**: 条件式の `uses` が、`counterfactual.actual.userMoveFacts.*` と、読み筋の側でもそのまま読む欄(`trigger.*`・`moves.*`・`standingPair.before` など D4 §3 の Q-4 の表)**だけ**のとき。**N 手後の欄(`positionFactsEnd`・`kingEscapesEnd`・`checks` など)を混ぜると、1 手目が同じでも 2 手目以降で両側が違いうるので、同じ手の組で両側が等しいとは言えず、分解は崩れる**
- **門で片側だけ落ちる組(K-3)があっても分解は崩れない**: 同じ手の組では門の値(`drop`・`kingMove`)も両側で等しいので、落ちるときは両側とも落ち、n から外れるのは手が違う組だけである
- 限界: 読み筋の 1 手目は軽い探索(材料の記録では 400 万ノード)の手で、`action.bestmoveAtBefore`(同じ行の別の探索)と食い違いうる(`pvFirstMoveIsBestmoveAtBefore`)。深い探索の組(D-SCREEN)では `pvSource` で出どころが変わる。D4 の Gate は軽い値だけを使う(D4 §2 の Q-2)

## 4. 契約と版(司令塔の決定 4)

- **任意の欄を足すだけ = MINOR**(E-9)。`role`・`capturedRole` の駒種の列挙は**新しい欄の列挙**で、既存の列挙に値を足すのではない
- **Failure Event v0.6 → v0.7、diagnosis-moment v0.3 → v0.4**(`lib/schemaVersions.ts` の今の版と `KNOWN_*` の並びを 1 か所で上げる)。`counterfactual.actual`・`counterfactual.pv`(compared の変種)に `userMoveFacts` を足す。**古い版のスキーマのファイルと検証器は残す**。スキーマは v0.6・v0.3 から道具で生成し、足した欄を外すと元のファイルとバイト一致に戻ることを道具の中で確かめる(D2.5・D-SCREEN-2 と同じ手順)
- diagnosis-condition・diagnosis-gate・diagnosis-report は反事実の欄を持たないので版を上げない(E-6)。ただし条件式が新しい欄を読むと `--events-cond` の `usedValues` に値が入る(形は自由な object なので契約は変わらない ― 実装のときに確かめる)
- **旧版の出力との比べ**: 新しい欄(`userMoveFacts`)を外すと、`schemaVersion` と `provenance.analysis` を除いてバイト一致(Failure Event・rise・maxDrop、材料 20 局 + 1 人目の先手 6 局)。D4 の `gate.ts` の基準値(条件式 0 本)の Markdown はバイト一致
- 出どころ(`provenance.analysis.rule`)には新しい規則の値を足さない(区域と利きの規則は既に `positionFacts` として写している。U-3・U-9 の選び方は Q の決定として計画に残す)

## 5. 読める欄の表に足す行(`condition.ts`、骨組みの変更)

`sequenceFields(side)` に、`side` = `actual`・`pv` のそれぞれで次の葉を足す(持つ行の種類はすべて、門は先頭に `counterfactual.state = compared`)。

| パス(`counterfactual.<side>.userMoveFacts.` の後) | 追加の門 | null の意味 |
|---|---|---|
| `role`・`drop`・`promotion`・`kingMove` | なし | notNullable |
| `capturedRole` | なし | value(取っていない) |
| `fromInOwnKingZone` | `…userMoveFacts.drop` が false | undecidable(門を通った後の null = 自玉が無い。打つ手の null は門で先に落ちる) |
| `toInOwnKingZone`・`toInOpponentKingZone` | なし | undecidable(指した後の盤に自玉 / 相手玉が無い) |
| `ownKingZoneReachBeforeMinusAfter` | `…userMoveFacts.kingMove` が false | undecidable(門を通った後の null = 自玉が無い。玉の手の null は門で先に落ちる) |

- **読み筋の側の門も読み筋の側のパスで見る**(今の `judgeConditionPvSide` の決まり ― 1e の D3-COND §12.2 の J-6)。したがって実戦の手が打つ手で読み筋の 1 手目が盤上の手の組では、`fromInOwnKingZone` を使う条件式は実戦の側だけ判定不能になり、揃えた集合 n から外れる
- `afterRow`・`actualKept` の印は付けない(`userMoveFacts` は組の直後の評価から作らず、読み筋の側では pv の値に置き換わる)。`pair` を含む定義でも読める
- 既存の試験(表の各行が、その種類の行で読めること)の固定の行に `userMoveFacts` を足す

## 6. 固定例と変異(期待は手で導いた。実装のときに盤の図を実装の節に残し、図で確かめ直す)

区域: 自玉 5i なら {4h, 5h, 6h, 4i, 5i, 6i}(6 升)、相手玉 5a なら {4a, 5a, 6a, 4b, 5b, 6b}。

| # | 局面と手 | 期待(U-1〜U-9) |
|---|---|---|
| F-1 | 平手の初期局面、`7g7f` | pawn / false / null / false / false / false(7g は区域の外)/ false / false / **0**(歩は 7g で 7f、7f で 7e に利く。どちらも区域の外) |
| F-2 | 平手の初期局面、`6i7h`(金が斜め前へ) | gold / false / null / false / false / **true**(6i)/ **false**(7h)/ false / **+2**(前: 6i の金は 5h・6h・7h・5i・7i に利き、区域と交わるのは 5h・6h・5i の 3。後: 7h の金は 6g・7g・8g・6h・8h・7i に利き、区域と交わるのは 6h の 1。3 − 1)。**前後を取り違えると −2**。区域と交わらせないと値が変わる(盤の外の升が数に入るかは shogiops の表し方に依るので、数は実装で図と一緒に書く) |
| F-3 | 平手の初期局面、`5i4h`(玉) | king / false / null / false / **true** / true / true(区域は 4h を中心に作り直す)/ false / **null**(玉の手。条件式では門 `kingMove` で判定不能) |
| F-4 | `4k4/9/9/9/9/9/9/9/4K4 b G 1`、`G*4h` | gold / **true** / null / false / false / **null**(打つ手。条件式では門 `drop` で判定不能)/ **true**(4h)/ false / **−2**(前 0。後: 4h の金は 3g・4g・5g・3h・5h・4i に利き、区域と交わるのは 5h・4i の 2) |
| F-5 | `2k6/1s7/9/9/9/9/9/7B1/4K4 b - 1`(後手玉 7a・後手銀 8b・先手角 2h)、`2h8b+` | **bishop**(成る前)/ false / **silver** / **true** / false / false / false / **true**(相手玉 7a の区域 {6a, 7a, 8a, 6b, 7b, 8b})/ 0(2h の角も 8b の馬も自玉の区域に届かない) |
| F-6 | `4k2+r1/9/9/9/9/9/9/9/7R1 b - 1`(後手玉 5a・後手竜 2a・先手飛 2i。先手玉なし)、`2i2a` | rook / false / **dragon**(Q-2 の推奨。元の駒種にする案なら rook)/ false / false / **null**(自玉が無い)/ **null** / false(2a は相手玉の区域の外)/ **null**。**自玉の無い局面を shogiops が読み・指せるかを実装で先に確かめ、指せなければ先手玉を 9i に置いた局面に替える**(そのときは U-6・U-7 は false、U-9 は **+2**: 前は 2i の飛が 8i・9i(玉で止まり 9i を含む)に届き、区域 {8h, 9h, 8i, 9i} と交わるのは 2。後は 2a の飛が届かない) |
| F-7 | `4k4/9/9/4P4/9/9/9/9/4K4 b - 1`、`5d5c+` と `5d5c` | pawn / false / null / **true** と **false** / false / false / false / false(5c は相手玉 5a の区域の外)/ 0 |
| F-8 | `3k5/9/9/9/4R4/9/9/9/4K4 b - 1`(後手玉 6a。R-1: 後手玉を筋 5 に置くと手番でない側が王手の局面になり読めない)、`5e3e` | rook / false / null / false / false / false / false / false / **+2**(前: 5e の飛は下へ 5f・5g・5h・5i(玉で止まり、5i を含む)。区域と交わるのは 5h・5i。後: 3e の飛は区域に届かない) |
| F-9 | F-8 の局面、`5e5c` | rook / false / null / false / false / false / false / false(5c は相手玉 6a の区域 {5a, 6a, 7a, 5b, 6b, 7b} の外)/ **0**(後: 5c の飛は下へ 5d・**5e(空いた升)**・5f・5g・5h・5i に届き、区域と交わるのは 2)。**指した後の占有を指す前のまま使うと、5e で止まって後が 0 になり +2** |
| F-10 | 反事実の組: 記録の 1 行に `focus_baseline` の読み筋を植え、1 手目を実戦の手と違う手にする(実戦は盤上の手、読み筋は打つ手) | `actual.userMoveFacts` は実戦の手、`pv.userMoveFacts` は読み筋の 1 手目の値。**`pvFirstMoveIsPlayedMove` が真の組では 2 つが等しい** |
| F-10b | 反事実の組: 読み筋の 1 手目を実戦の手と同じにする(R-4 (a)) | `pvFirstMoveIsPlayedMove` が真、`actual.userMoveFacts` と `pv.userMoveFacts` が深く等しい。F-11・F-12 の条件式を当てると、両側の判定(状態と判定不能の理由)が同じ |
| F-11 | 条件式(試験だけの定義)`uses: ["counterfactual.actual.userMoveFacts.drop"]`、`appliesTo: ["pair"]` を F-10 の組に当てる | 実戦の側 noMatch(盤上の手)、読み筋の側 match(打つ手)。読み筋の側の view は `pv.userMoveFacts.drop` を元のパスの名前で読む |
| F-12 | 条件式 `uses: ["counterfactual.actual.userMoveFacts.fromInOwnKingZone"]` を F-10 の組に当てる | 実戦の側は判定できる、読み筋の側は判定不能で、**理由の種類は gate**(`counterfactual.pv.userMoveFacts.drop` = true)。揃えた集合 n に入らない |
| F-12b | 条件式 `uses: ["counterfactual.actual.userMoveFacts.ownKingZoneReachBeforeMinusAfter"]`、`appliesTo: ["pair"]` を、実戦の手が玉の手で読み筋の 1 手目が玉以外の手の組に当てる(R-4 (b)) | 実戦の側は判定不能で、**理由の種類は gate**(`counterfactual.actual.userMoveFacts.kingMove` = true)。読み筋の側は判定できる |
| F-13 | 旧版と同じ入力(材料 20 局・1 人目の先手 6 局・GAME01) | §4 の比べ(新しい欄を外してバイト一致、`gate.ts` の基準値の Markdown はバイト一致) |
| F-14 | F-8 の局面、`5e5g`(監査 f2 の N-1。実装の後に足した) | U-9 = **0**(前: 5e の飛は 5h・5i に届き 2。後: 5g の飛も 5h・5i に届き 2)。**指す前の利きを指した後の占有で数えると、5g の自分で止まって前が 0 になり −2** |

**変異(中心)**: 区域の判定を外す(利きの升を全部数える → F-2・F-4・F-8)/ 前後を取り違える(後 − 前 → F-2・F-4・F-8)/ **読み筋の側に当てない**(`pv.userMoveFacts` を実戦の手で作る → F-10・F-11。F-10b は鳴らない)/ 指した後の占有を指す前のまま使う(F-9)/ 指す前の利きを指した後の占有で数える(F-14)/ 指した後の区域を指す前の盤で作る(**等価と読む**: 自玉は玉の手でしか動かず、玉の手の行き先は元の区域に入るので U-7 は変わらない。相手玉は本人の手では動かない。実装のときに等価を確かめ、既知事項の候補 K-1 にする)/ 相手玉の区域と取り違える(F-2・F-5)/ `role` を成った後の駒種にする(F-5)/ `capturedRole` を元の駒種にする(F-6)/ 打つ手の門を外す(F-12: 判定不能の理由の種類が gate から null に変わる)/ 玉の手の門を外す(F-12b: 同じく gate から null に)/ 門で落ちる欄に null でなく値を置く(F-3・F-4)/ 表に `pv` の葉を足さない(F-11 が読み筋の側を当てられなくなる)。**周辺**: `promotion` を駒種の変化で決める(F-7 の成らずは同じ)/ 玉が無い側を false にする(F-6)。**予測は実装の後、当てる前に試験の単位で書く。**

## 7. 予測(**測る前に書く。書いた人 A。記入 2026-09-17T10:57:50Z**)

**見たもの**: D3-COND 計画 §13・§14 の表と文(揃えた集合 706 組、C-1 の 110・66、N の内訳)、D4 の基準値(材料 734 組・崩れ 32/604・直前 ahead 170・level 434、pairKind の compared 672・mateAfter 5・notCompared 57)。**見ていないもの**: 材料の側の手(`moves`)・読み筋の 1 手目・盤・`pvFirstMoveIsPlayedMove` の分布。1 人目の局(g3 を含む)は見ていない。**確信はどれも弱い**(本人の棋力と戦型を数で見ていない。2 人目は 20 局で 10 勝 10 敗、1 局あたりの本人の手は約 37)。

**測り方(R-5、司令塔の決定)**: 実装のコミットの後に、gitignore の `scripts/playtest/out/` の下に使い捨ての数える道具を置き、`gate.ts` と同じ関数(`diagnoseRecords`・`allPairsOf`、軽い値)で材料の側の組を平らに書き出して数える(D3-COND §13 の下見と同じ型)。**道具と出力の sha256 を記録してから回す**。道具はコミットしない。予-9 の G-3 もこの道具で数え、`gate.ts` には当てない。**この下見は棄却の記録(D4 §11)に入れない**(棄却の記録に入るのは、人間が承認した定義を `gate.ts` に当てたときだけ ― D3-COND §13・§14 と同じ扱い)

**材料の側(2 人目 20 局)。分母は欄ごとに書く。基本は `userMoveFacts` を持つ組 = compared の組 706(§13 の数)**

| # | 予測 | 外れたと言える条件 |
|---|---|---|
| 予-1 | (分母 706)実戦の側の `role`: 歩 22〜38%・銀 8〜16%・金 6〜14%・玉 4〜12%・飛 5〜13%・角 3〜10%・桂 2〜8%・香 1〜5%・成駒(と・成香・成桂・成銀・馬・竜の計)3〜12% | 3 つ以上が範囲外 |
| 予-2 | (分母 706)実戦の側の `drop` 8〜20% | 範囲外 |
| 予-3 | (分母 706)実戦の側の `capturedRole` が null でない(取った手)18〜32% | 範囲外 |
| 予-4 | (分母 706)実戦の側の `promotion` 2〜8% | 範囲外 |
| 予-5 | (分母 = 706 のうち実戦の手が打つ手でない組。自玉・相手玉が無い組があれば除いて数を書く)実戦の側の `fromInOwnKingZone` が true 15〜35%、`toInOwnKingZone` が true 15〜35%、`toInOpponentKingZone` が true 3〜12% | 2 つ以上が範囲外 |
| 予-6 | (分母 = 706 のうち実戦の手が玉の手でない組)実戦の側の `ownKingZoneReachBeforeMinusAfter` が 0 でない 15〜35%、そのうち正(届く升が減った)40〜60% | どちらかが範囲外 |
| 予-7 | (分母 706)`pvFirstMoveIsPlayedMove` が真 25〜45%(同じ手の組の割合) | 範囲外 |
| 予-8 | (分母 706)読み筋の側 − 実戦の側の率の差: `capturedRole` が null でない −3〜+8 pt、`drop` −6〜+4 pt、`kingMove` −6〜+2 pt、`promotion` −2〜+3 pt | 2 つ以上が範囲外 |
| 予-9 | **候補 23 個**(`role` の値ごと 14 = 盤上の駒種 8(玉・飛・角・金・銀・桂・香・歩)+ 成駒 6(と・成香・成桂・成銀・馬・竜)/ `drop` / `capturedRole` ≠ null / `promotion` / `kingMove` / `fromInOwnKingZone` / `toInOwnKingZone` / `toInOpponentKingZone` / U-9 > 0 / U-9 < 0。それぞれ「実戦の側でその値なら真」)を単独で当てたとき、G-3(揃えた集合 n で `2·p ≤ a`)を満たすものは **0〜3 個**(§3 の `a′ ≥ s + 2·p′` は s が大きいと満たしにくい)。数えるのは上の下見の道具 | 4 個以上 |

条件式ごとの予測は、D3 で定義が承認されたときに D3-COND 計画 §11 に足す(この計画では書かない)。

## 8. 決定が要る点

| # | 点 | 推奨 | ほかの案 |
|---|---|---|---|
| Q-1 | 置き場 | `counterfactual.{actual,pv}.userMoveFacts`(司令塔の決定 1。`sequenceFacts` が 1 手目に当てる) | 実戦の側だけ組の欄(`moves.userMoveFacts`)にも置き、compared でない 28 組でも読めるようにする(読み筋の側が無いので G-3 は判定不能のまま) |
| Q-2 | `capturedRole` の駒種 | **盤の上の駒種のまま**(成駒は成駒。取った瞬間の事実) | D2 の `capturedRoles` に合わせて元の駒種(E-8。竜を取っても飛) |
| Q-3 | 打つ手の U-9 の「指す前」 | **0**(持ち駒は利かない。D2.5 の「持ち駒を数えない」と同じ扱い) | 打つ手は判定不能(門 `drop` を足す) |
| Q-4 | 玉の手の U-9 | **判定不能**(門 `kingMove`。玉の利きは数えない ― D2.5 Q-7) | 玉の利きを数える(D2.5 と食い違う) |
| Q-5 | 玉の手の U-6・U-7 | **値のまま**(区域は玉の升を含むので常に true。条件式は `kingMove` と組み合わせる) | 玉の手は判定不能 |
| Q-6 | U-9 の範囲 | **動かした駒 1 枚だけ**(司令塔の決定 2 の文) | 盤全体の自玉の区域の利きの差(D2.5 の `zoneControl` の 1 手の差。線を開けた・塞いだを含む) |
| Q-7 | Markdown と D6 の文 | **変えない**(この STEP は欄だけ。文にするかは条件式が承認されてから) | 反事実の節に 1 行足す |
| Q-8 | 区域の関数の共有 | `positionFacts.ts` の区域の関数を export して使う(司令塔の決定 2) | `moveFacts.ts` に写す(2 か所になる) |
| Q-9 | 成る手の判定 | USI の末尾 `+` | 指す前と後の駒種の違い(同じ値になるが、成らずを区別できない点は同じ) |

## 9. やらないこと・限界

- **やらない**: 条件式の定義(D3 で司令塔と人間)・評価の言葉・「攻め・守り・受け・逃げ」のような解釈の欄(事実の欄から後で作れる)・エンジン・記録の測り直し・`apps/` の変更・D6 の文の変更・Gate の値の変更
- **限界**:
  - 事実は compared の組にしか無い(材料の側で 706 / 734)。compared でない組の本人の手は読めない
  - 読み筋の 1 手目は 1 つの探索(軽い値)の手で、別の探索の最善手と食い違いうる(§3)。同じ手の組では両側が等しいので、G-3 は「違う手を選んだ組」の性質を問う形になる(§3)
  - U-9 は動かした駒 1 枚の幾何だけで、ピン・取り返し・ほかの駒の線の開閉を見ない(D2.5 の E-1 と同じ方針)
  - 20 局は探索で、欄を増やすほど偶然 Gate を満たす候補が出やすい(D4 §11。当てた条件式の数は棄却の記録で数える)。**§7 の下見(単独の欄 23 個)は棄却の記録に入れない**。棄却の記録に入るのは、人間が承認した定義を `gate.ts` に当てたときだけ(D3-COND §13・§14 と同じ扱い)。下見で見た欄の数は、定義を起こすときに計画に書く

**既知事項の候補(登録と番号は司令塔)**
- **K-1** 指した後の区域を指す前の盤で作る変異は等価(§6。U-7・U-8 を区域の作り方で守る試験は置けない)
- **K-2** F-6 の「自玉が無い局面」を shogiops が指せない場合、U-6〜U-9 の null の経路は実データでも固定例でも通らない(型の上だけの null になる)
- **K-3** 実戦の手が打つ手で読み筋の 1 手目が盤上の手の組(またはその逆)では、`fromInOwnKingZone` を使う条件式は片側だけ判定不能になり、揃えた集合 n から外れる(§5)

## 10. 実装の記録(実装担当 A、2026-09-17。監査 f2 の前)

**基点**: `b8d81eb`(この計画のコミット)。worktree で実装した。**エンジンは使っていない。g3 は開いていない**(旧版との比べと予測の測定は、材料 20 局と 1 人目の先手 6 局だけ)。

### 10.1 変えた・足したファイル

| ファイル | 中身 |
|---|---|
| `scripts/playtest/lib/moveFacts.ts`(新規) | `moveFactsOf(sfen, moveUsi, rules)`・`UserMoveFacts`・`STANDARD_ROLES`(14 種)・`MoveFactsError` |
| `scripts/playtest/lib/moveFacts.test.ts`(新規) | 固定例 F-1〜F-12b、空の手順、例外、スキーマ 0.7 = 0.6 + userMoveFacts・0.4 = 0.3 + userMoveFacts |
| `scripts/playtest/lib/positionFacts.ts` | 区域の関数を `kingZoneOf` として export(中身と `positionFactsOf` の出力は変えていない) |
| `scripts/playtest/lib/counterfactual.ts` | `SequenceFacts.userMoveFacts` を足し、`sequenceFacts` の 1 手目に `moveFactsOf` を当てる。空の手順は例外 |
| `scripts/playtest/lib/condition.ts` | `sequenceFields` に §5 の葉(門 `drop`・`kingMove` を含む)を足した |
| `scripts/playtest/lib/schemaVersions.ts` | Failure Event 0.7・diagnosis-moment 0.4。基の版の定数 `FAILURE_EVENT_MOVE_FACTS_BASE_VERSION`(0.6)・`DIAGNOSIS_MOMENT_MOVE_FACTS_BASE_VERSION`(0.3) |
| `scripts/playtest/schemas/failure-event.v0.7.schema.json`・`diagnosis-moment.v0.4.schema.json`(新規) | 道具 `scratchpad(7b19a5fe)/d26impl/gen-d26-schemas.py`(`15805520…`)で 0.6・0.3 から作った。足した欄を外すと基の版に戻ること、古い版のファイル 12 本の sha が前後で変わらないことを道具の中で確かめた |
| 既存の試験 | `screenDiagnosis.test.ts`(下の J-5)・`condition.test.ts`(固定の行に userMoveFacts、C-2 の一覧に §5 の葉と門)・`gate.test.ts`・`conditions.test.ts`(固定の行に userMoveFacts)・`counterfactual.test.ts`(D2 の固定例の比べから userMoveFacts を外す)・`failureEventSchema.test.ts`(T-5 の数 210 → 230 = actual・pv の userMoveFacts 各 1 と中身 9、P-7 に 0.7 → 0.6 の段) |

### 10.2 計画に書いていなかった判断

- **J-1** `moveFactsOf` の「自玉」は手番の側の玉(根は本人 = 先手の手番なので、D2.5 の `ownKingZone` と同じ)
- **J-2** `moveFactsOf` は `rules.reach = non_king_pieces`・`rules.control = squares` だけを受け、ほかは例外(数え方が食い違わないように)
- **J-3** 合法かは `apps/server/src/rules/legalMoves.ts` の `isLegalMove` で見る。読めない手・合法でない手・本将棋でない駒種は `MoveFactsError`
- **J-4** スキーマの駒種の列挙は `STANDARD_ROLES` の並び(盤上の駒種 8 → 成駒 6)。`capturedRole` はその列挙に null を足した
- **J-5(監査 f2 の W-1)** `screenDiagnosis.test.ts` の「D-SCREEN の欄の版 = 基の版 + D-SCREEN の欄」の 2 本は、**今の版でなく 0.6・0.3 のファイルを名指しで読んで比べる**形にした(題も「D-SCREEN の版(0.6)」「(0.3)」に)。**0.7 = 0.6 + userMoveFacts・0.4 = 0.3 + userMoveFacts は `moveFacts.test.ts` の別の試験**が見る
- **J-6** F-10・F-10b・F-12b の組は、`counterfactualOf` に持ち駒のある根(`4k4/9/9/9/9/9/4P4/9/4K4 b G 1`)を直接渡して作った(計画の「記録の 1 行に読み筋を植える」と同じ入力の形。`branchPly` 1)
- **J-7** F-6(先手玉の無い局面)は shogiops で読め、指せた。計画の差し替え案は使っていない(K-2 は起きない)
- **J-8** F-10b の比べは、判定の状態・判定不能の理由の種類・欄の名前(view 側)で行い、gatePath の文字列は比べない(事前読み B の N-1)

### 10.3 測った結果

- 型検査 `typecheck:scripts` rc 0。試験 `b8d81eb` の 891 → **912**(+21、61 ファイル)。`check-docs` rc 0。**監査 f2 の GO の後、F-14 を足して 913**(`moveFacts.test.ts` は 22)
- **旧版との比べ(F-13)**: 材料 20 局 + 1 人目の先手 6 局で `diagnose.ts` の `--events`(44 行)・`--events-rise`(83 行)・`--events-maxdrop`(26 行)は、`schemaVersion`・`provenance.analysis`・`counterfactual.{actual,pv}.userMoveFacts` を外すと、キーの並びまで一致(差 0)。userMoveFacts を持つ行は 42・83・26(compared の行)。Markdown と `gate.ts` の基準値(条件式 0 本)の Markdown はバイト一致
- **変異**: 17 本(計画 §6 の中心・周辺と、空の手順・合法でない手)。**当てた 17・鳴った 15・沈黙 2、予測と 17/17 一致**、毎回戻して sha 一致。沈黙は予測どおり等価の 2 本(V-05 指した後の自玉の区域を指す前の盤で作る = K-1、V-14 成りを駒種の変化で決める = Q-9)。予測 `scratchpad(7b19a5fe)/d26impl/mutation-predictions.txt`(`ca500e83…`、道具 `mutate_d26.py` `ba06212d…`、実行の前 2026-09-17T12:47:03Z に sha を取った)。結果の行に `applied` の欄を書いた。**F-14 を足した後に V-18「指す前の利きを指した後の占有で数える」を 1 本当てた**: 予測(`d26impl/mutation-v18-prediction.txt` `51c277b9…`、2026-09-17T13:03:04Z)は「F-14 だけで鳴る」、結果は F-14 の 1 本が落ちて鳴った(適用あり・戻して sha 一致)
- **§7 の予測の測定**: 道具 `scripts/playtest/out/d26-measure/measure.ts`(gitignore。sha `c6109b7f…` を 2026-09-17T12:47:52Z に記録してから回した)。出力 `result.json` の sha `5a3a6f63…`。**手順の記録(監査 f2 の N-6)**: 測定はコミットの前に回ったが、lib のコードの最後の更新は測定より前で、`final-shas.txt` の版と同じ。測定に渡したファイルの一覧は記録していない(出力の局の数 20・組 734・compared 706 で代えた)。材料 20 局・組 734・compared 706(§13 の数と一致)。**単独の欄の下見は棄却の記録に入れていない**

| # | 予測 | 実際 | |
|---|---|---|---|
| 予-1 | 歩 22〜38・銀 8〜16・金 6〜14・玉 4〜12・飛 5〜13・角 3〜10・桂 2〜8・香 1〜5・成駒 3〜12(%) | 歩 37.7・銀 13.6・金 7.5・玉 5.2・飛 10.3・**角 10.1**・**桂 9.5**・香 2.5・成駒 3.5 | 当たり(範囲外 2 つ。外れの条件は 3 つ以上) |
| 予-2 | 打つ手 8〜20% | 12.6%(89) | 当たり |
| 予-3 | 取った手 18〜32% | 20.7%(146) | 当たり |
| 予-4 | 成った手 2〜8% | 5.8%(41) | 当たり |
| 予-5 | 打つ手でない組 617 で fromInOwnKingZone 15〜35・toInOwnKingZone 15〜35・toInOpponentKingZone 3〜12(%) | 17.5・15.1・**1.1** | 当たり(範囲外 1 つ。外れの条件は 2 つ以上)。**分母の注(B の N-2)**: to の 2 欄は打つ手でも値が入る。706 を分母にすると 14.2・1.6 で範囲外 2 つ(外れ)になる。計画の分母(打つ手でない組)で判定した |
| 予-6 | 玉の手でない組 669 で U-9 ≠ 0 が 15〜35%、そのうち正 40〜60% | 19.0%(127)・44.9%(57) | 当たり |
| 予-7 | 同じ手の組 25〜45% | 35.6%(251) | 当たり |
| 予-8 | 読み筋 − 実戦: 取った −3〜+8・打つ −6〜+4・玉 −6〜+2・成る −2〜+3(pt) | +0.6・−2.3・−1.3・+1.7 | 当たり |
| 予-9 | 候補 23 個で G-3 を満たすもの 0〜3 | **2**(香 a 18・p 9 は境ちょうど、成香 a 0・p 0 は式の上だけ) | 当たり |

- 予-9 の内訳(揃えた集合 n・実戦 a・読み筋 p): 玉 706・37・28 / 飛 73・58 / 角 71・72 / 金 53・56 / 銀 96・90 / 桂 67・70 / 香 18・9 / 歩 266・298 / 竜 9・9 / 馬 2・3 / 成銀 3・3 / 成桂 3・2 / 成香 0・0 / と 8・8 / 打つ 89・73 / 取る 146・150 / 成る 41・53 / 玉の手 37・28 / fromInOwnKingZone(n 593)106・100 / toInOwnKingZone 100・71 / toInOpponentKingZone 11・20 / U-9 > 0(n 650)57・70 / U-9 < 0(n 650)67・50。**見た欄の数は 23**(定義を起こすときに書く ― §9)

### 10.4 既知事項の候補(登録と番号は司令塔)

- **K-1**(確認) 変異 V-05 は等価だった(沈黙)。U-7・U-8 を区域の作り方で守る試験は置けない
- **K-2**(閉じる候補) 自玉の無い局面は shogiops で読め、指せた(F-6)
- **K-4** 変異 V-14(成りを駒種の変化で決める)は等価。成らずは USI にも駒種にも残らないので、「成れたのに成らなかった」は数えられない(Q-9)
- **K-5** G-3 の式 `2·p ≤ a` は a = p = 0 でも満たす(予-9 の成香)。**G-1 が先に満たさないと言えるのは、真の組の数が a と同じときだけ**。K-3 の型(実戦の側で真でも読み筋の側が判定不能な組が n から外れる)の定義では、真の組 12(3 局)で a = p = 0 でも G-1・G-3 が met になりうる(監査 f2 の N-4、探りで確認)。下見で数えるときは式の上だけの候補を分けて書く
- **K-6** 落ちる試験が 1 本だけの変異: V-04・V-08・V-11・V-12・V-15・V-16・V-17
- **K-7** 予-5 の to の 2 欄は、分母の取り方(打つ手を含めるか)で予測の当たり外れが変わった(B の N-2)
- **K-8**(監査 f2 の N-2、司令塔の決定でコードの見張りは入れない) `moveFactsOf` の自玉は「手番の側の玉」、`positionFactsOf` の自玉(`ownKingZone`)は「先手の玉」に固定。回した記録では根はすべて先手番で一致する(f2 が材料 20 局と real-01 の 6 局で確認)。根が後手番の行が来ると両者が食い違う

## 11. 事前読み B(版 `8c111855`、REVISE)の取り込み

- **R-1** F-8・F-9 の局面は先手の飛が後手玉に利き、手番でない側が王手の局面として読めない → 後手玉を 6a に移した(期待値 +2・0 と U-8 の false は変わらない)
- **R-2** 門で判定不能にする欄の行の値 → **司令塔の決定: null を置く**。U-6・U-9 の null の意味を「値を決められない(打つ手 / 玉の手 / 自玉なし)」に広げ、§1 に行の値の決まりを足した。F-3・F-4 の期待を null に。変異「門を外す」は判定不能の理由の種類(gate → null)で見る(F-12・F-12b)
- **R-3** §3 の分解が成り立つ範囲(`userMoveFacts` と読み筋の側でそのまま読む欄だけ)を書き、式を `a′ ≥ s + 2·p′`(「以上」、s は同じ手の組の中で真になる数)に直し、K-3 で分解が崩れない理由を足した
- **R-4** 固定例 F-10b(同じ手の組で両側が等しい)と F-12b(玉の手の門を条件式の水準で見る)を足した
- **R-5** §7 に測り方(out/ の使い捨ての道具・sha を記録してから回す・`gate.ts` の関数)と欄ごとの分母、予-9 の候補 23 個を書いた。**司令塔の決定: 下見は棄却の記録に入れない**(§7・§9)
- 軽微: U-8 の null の文、§2 の空の手順は例外、ヘッダの事前読みを B に
