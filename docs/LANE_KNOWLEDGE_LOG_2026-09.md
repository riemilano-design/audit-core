# 知識レーンの記録(2026-09)

知識レーン(2026-09-25 新設。指示書 [KNOWLEDGE_LANE_BRIEF_2026-09-25.md](KNOWLEDGE_LANE_BRIEF_2026-09-25.md))が書く記録。**このファイルに書くのはこの席だけ**([COMMAND_STRUCTURE.md](COMMAND_STRUCTURE.md) §2.1「1 ファイル 1 席」)。報告先は司令塔(統括)。書くのは、何を足したか・出典・測った数・認識できなかった場面の一覧。コード・閾値・露出制御・スキーマは触らない。

## 1. 最初の 1 まとまり(2026-09-25)

### 1.1 数えた範囲(先に書く)

| 対象 | 局数 | 固定棋譜のフォルダ | 後手の局 |
|---|---|---|---|
| 固定棋譜 4 局 | 4 | `scripts/playtest/kifu/`(`2026-09-10-claude-10moves`・`2026-09-12-live-30moves-claude-1〜3`) | 無し |
| 固定棋譜 round2(参考) | 3 | 同上の `-round2` 3 本。基準値 [BASELINE_2026-09-12.md](BASELINE_2026-09-12.md) には入っていない | 無し |
| 1 人目 | 10 | `scripts/playtest/records/real-01/kifu/`(先手 6)+ `records/real-03/kifu/kifu-01・04・07・09`(後手 4) | 4 局 |
| 2 人目 | 20 | `records/real-02/kifu/`(先手 9)+ `records/real-03/kifu/kifu2-*`(後手 11) | 11 局 |
| 3 人目 | 20 | 3 人目の作業ツリー(別ツリー、`feature/honeymint-report`)の納品 work の `p2/kifu/*.fixed.json`(顧客名を含むフォルダ名は書かない) | 11 局 |
| 4 人目 | 20 | 共有ツリーの `scripts/playtest/out/<4 人目>/pipe-3min/p2/kifu/`(18)+ `pipe-10min/p2/kifu/`(2)(同上) | 12 局 |

**後手の局のそろえ方**: 上の固定棋譜はすべて納品の道具(`kifu-import-check.ts --fixed`、`lib/sideAlignment.ts`)が作ったもので、本人が後手の局は**既に 180 度回して本人の手を先手にそろえてある**(`mirrored: true`・`originalUserSide: "gote"`・`plyOffset: 1`・`startSfen` の 4 欄を 38 局すべてで機械的に確かめた。1 人目 4・2 人目 11・3 人目 11・4 人目 12)。測定は `startSfen` を `initialSfen` に渡して回した(`replay.ts` と同じ)。**回し直しはしていない**(司令塔の確認 2026-09-25 への答え)。**相手の名前・元の KIF は読んでいない**(固定棋譜には `id`・`source`・`ending`・`moves`(+ `moveSeconds`)しか無い)。

`scripts/playtest/out/kiou-p1/`(棋桜から取った 16 局。2026-09-21 の人間の指示「評価はしない」)は**数えていない**(4 人のどれに当たるかが記録に無い)。

### 1.2 測り方(開発・診断レーンの回答 2026-09-25 に従う)

- **道具**: 既存の道具にエンジン無しで ply ごとの認識を出すものは無い(開発・診断レーンの回答)。scratchpad の使い捨てスクリプト(`measure.ts`。`apps/server/src/analysis/` の `analyzeShapeFormationFromEvents`・`detectIntentsFromEvents`・`replayMoveHistory` を `recognitionTimeline.ts:139-140` と同じ呼び方で呼ぶだけ。判定・閾値は書いていない。`tsc --noEmit` を通してから回した)。`apps/`・`scripts/` は変えていない。
- **渡す集合**: `data/shapes`・`data/intents` の全件(`draft` を含む)。前後で同じ集合。`review_status` は §1.5 の表に別欄で書く。
- **分母**: 先手番の局面(ply 0, 2, 4, …。ready 行と同じ数え方)。「30 手まで」と「全手」の 2 通り。
- **沈黙率(3 つに分ける)**: 形だけ(forming/completed の形が 1 件も無い)/狙いだけ(forming/matched の狙いが 1 件も無い)/どちらも無し。**check.ts の 6 列(道のり・候補手を含む)とは別の数**。加えて、形は「証拠(formationEvidence)2 件以上か完成」に限った数も出す(1 件の証拠で forming が立つため。[STEP_UNIT6_PLAN_2026-09-12.md](STEP_UNIT6_PLAN_2026-09-12.md) F-1)。
- **I-9 型**: I-9 と同じ条件(証拠 1 件以下かつ欠け 2 件以上)を、`targetShapeProgress` ではなく forming/completed の**形すべて**に当てた件数(局面 × 形)。**「誤認が n 件」とは書かない**(盤面との食い違いそのものは正解が無いので測れない)。
- **校正(既知の正解)**: 固定棋譜 4 局の「形あり」34/59 が [BASELINE_2026-09-12.md](BASELINE_2026-09-12.md) §2 の「認識あり」34 と一致、2 局目は形 0、3 局目は本美濃 forming 15 局面(I-9 の 14 件 + ply 30)。3 つとも通った。

### 1.3 前の数と「認識できなかった場面」(形 3・狙い 8 のとき)

| 対象 | 局面数(30 手まで / 全手) | 形だけ沈黙 | 形の沈黙(証拠 2 件以上か完成が無い) | 狙いだけ沈黙 | どちらも無し |
|---|---|---|---|---|---|
| 固定棋譜 4 局 | 59 / 59 | 25(42%) / 25(42%) | 45(76%) / 45(76%) | 29 / 29 | 17(29%) / 17(29%) |
| 固定棋譜 round2 3 局(参考) | 48 / 48 | 48(100%) / 48(100%) | 48(100%) / 48(100%) | 9 / 9 | 9(19%) / 9(19%) |
| 1 人目(10 局) | 157 / 331 | 155(99%) / 257(78%) | 157(100%) / 297(90%) | 40 / 47 | 40(25%) / 42(13%) |
| 2 人目(20 局) | 312 / 754 | 183(59%) / 257(34%) | 296(95%) / 674(89%) | 75 / 75 | 69(22%) / 69(9%) |
| 3 人目(20 局) | 320 / 998 | 210(66%) / 327(33%) | 279(87%) / 621(62%) | 111 / 111 | 93(29%) / 93(9%) |
| 4 人目(20 局) | 307 / 652 | 209(68%) / 426(65%) | 307(100%) / 652(100%) | 53 / 53 | 46(15%) / 46(7%) |

**読み方**: 狙いは 8 件のうち「飛車先の歩交換」(8四歩)・「早仕掛け」(6四歩)・「斜め棒銀」(5三銀)が相手の 1 手で forming になるため、狙いの側はほぼ常時立つ(狙いだけ沈黙が 30 手までで 279/1096)。これは判定の話であり、この席は触らない(司令塔が開発・診断レーンへ事実として渡す)。**形の側は美濃 3 件しか無いため、居飛車で玉を 7八・8八へ寄せた局と、玉を動かさない局(居玉)が形の沈黙になっていた。**

**40 手目(それより短い局は終局)の自玉・自飛の筋・相手玉・相手飛の筋の分布(4 人 70 局)**:

- 自玉: 5i 20、2h 11、4h 7、8h 6、3h 6、6i 5、7h 4、7i 3、5h 2、1i 2、3i 1、4g 1、6h 1、4i 1
- 自飛の筋: 2 21、8 12、- 10、7 7、5 7、6 6、4 3、3 3、46 1
- 相手玉: 5a 18、8b 11、3b 8、7b 7、3a 5、2b 5、6b 3、4a 3、4b 3、5b 2、2a 1、1a 1、3c 1、4e 1、7a 1
- 相手飛の筋: 8 31、- 8、6 6、4 6、2 5、5 4、3 3、7 3、9 2、68 1、48 1

読み方: 自玉が 5九のまま(居玉)の局が 20/70 で最多(1 人目 7/10・4 人目 12/20)。2026-09-12 の U6-A の発見「玉が初形付近に留まる囲いは存在しない」([STEP_UNIT6_PLAN_2026-09-12.md](STEP_UNIT6_PLAN_2026-09-12.md) §9.6)のとおり、この 20 局の形の沈黙は形を足しても埋まらない。次に多いのは 2八(11。美濃で既に認識できる)、4八・3八(13。相振りの金無双か美濃の途中)、8八・7八・7九(13。居飛車の矢倉・舟囲い)。自飛の筋は 2 筋(居飛車)21・8 筋(向かい飛車)12・7 筋 7・5 筋 7・6 筋 6。相手飛の筋は 8 筋(居飛車)31 が最多。局ごとの一覧は付録 A。

### 1.4 候補の数え上げ(どの形を足すか)

出典が本文の座標として確かめられた候補 5 件(矢倉・舟囲い・金無双・居飛車穴熊・二枚銀雁木)を仮に足して 4 人 70 局を回し、**完成した局の数**と**必須マスの 3/4 以上が一致した局の数**で並べた(1 件の証拠で立つ forming は数えない):

| 候補 | 完成した局 | 3/4 以上一致した局 | 採否 |
|---|---|---|---|
| 舟囲い | 2 | 6 | 足す |
| 金無双 | 4 | 4 | 足す |
| 矢倉(金矢倉) | 0 | 2 | 足す |
| 雁木(二枚銀) | 0 | 1 | 今回は足さない |
| 居飛車穴熊 | 0 | 0 | 今回は足さない |
| (参考)本美濃 | 5 | 8 | 既存 |
| (参考)高美濃 | 0 | 3 | 既存 |
| (参考)銀冠 | 0 | 1 | 既存 |

### 1.5 足した下書き(5 件。すべて `review_status: draft`、`side: self`)

| 種類 | id | 名前 | 出典(一次資料の本文の座標。**座標の一次資料確認は行っていない**(ROLES.md の保留)) | confidence | review_status |
|---|---|---|---|---|---|
| shape | `funagakoi` | 舟囲い | Wikipedia『舟囲い』「囲いの形は、8八角、7八玉、7九銀、6九金、5八金、4八銀型であり」→ 玉7h・銀7i・金6i・金5h・銀4h | medium | draft |
| shape | `kinmusou` | 金無双 | Wikipedia『金無双』「玉を3八に、左金を5八に、右金を4八に動かして作られる」→ 玉3h・金5h・金4h(2h 銀は図からの読み取りなので optional) | medium | draft |
| shape | `yagura_kinyagura` | 矢倉囲い(金矢倉) | Wikipedia『矢倉囲い』「玉を8八に、左金を7八、右金を6七に、左銀を7七に移動させたもの」→ 玉8h・金7h・銀7g・金6g | medium | draft |
| opening | `ibisha_self` | 居飛車(自分側) | Wikipedia『居飛車』「初形で右翼にある飛車を定位置(先手は2筋、後手は8筋)のまま据えて戦うこと」。recognition_pattern 無し(否定の条件は書けない) | high | draft |
| opening | `mukaibisha` | 向かい飛車(自分側) | Wikipedia『向かい飛車』「先手ならば飛車を八筋に」→ recognition_pattern 飛 8h | medium | draft |

**戦型 2 件は測れない**(認識のコードが `apps/server/src/analysis/` に無い。2026-09-25 司令塔の訂正)。`ibisha_self` の id は既存 `ibisha`(side: opponent)との衝突を避けた暫定で、既存 2 件(`ibisha`・`shikenbisha`)との揃え方は司令塔の判断事項。`typical_build_order` の並びと `beginner_friendliness` の点は出典に無く、書いた側の推測(各レコードの `source` に明記)。

### 1.6 後の数(形 6・狙い 8。同じ棋譜・同じ道具)

**30 手まで**

| 対象 | 局面数 | 形だけ沈黙 前→後 | 形の沈黙(証拠 2 件以上か完成が無い) 前→後 | 狙いだけ沈黙 前→後 | どちらも無し 前→後 | I-9 型 前→後 |
|---|---|---|---|---|---|---|
| 固定棋譜 4 局 | 59 | 25 → 25(42% → 42%) | 45 → 43(76% → 73%) | 29 → 29 | 17 → 17(29% → 29%) | 37 → 97 |
| 固定棋譜 round2 3 局(参考) | 48 | 48 → 20(100% → 42%) | 48 → 46(100% → 96%) | 9 → 9 | 9 → 8(19% → 17%) | 0 → 26 |
| 1 人目(10 局) | 157 | 155 → 60(99% → 38%) | 157 → 154(100% → 98%) | 40 → 40 | 40 → 21(25% → 13%) | 4 → 104 |
| 2 人目(20 局) | 312 | 183 → 104(59% → 33%) | 296 → 237(95% → 76%) | 75 → 75 | 69 → 54(22% → 17%) | 243 → 492 |
| 3 人目(20 局) | 320 | 210 → 160(66% → 50%) | 279 → 256(87% → 80%) | 111 → 111 | 93 → 92(29% → 29%) | 128 → 341 |
| 4 人目(20 局) | 307 | 209 → 147(68% → 48%) | 307 → 302(100% → 98%) | 53 → 53 | 46 → 42(15% → 14%) | 156 → 355 |
| **4 人合計(70 局)** | 1096 | 757 → 471(69% → 43%) | 1039 → 949(95% → 87%) | 279 → 279 | 248 → 209(23% → 19%) | 531 → 1292 |

**全手**

| 対象 | 局面数 | 形だけ沈黙 前→後 | 形の沈黙(証拠 2 件以上か完成が無い) 前→後 | 狙いだけ沈黙 前→後 | どちらも無し 前→後 | I-9 型 前→後 |
|---|---|---|---|---|---|---|
| 固定棋譜 4 局 | 59 | 25 → 25(42% → 42%) | 45 → 43(76% → 73%) | 29 → 29 | 17 → 17(29% → 29%) | 37 → 97 |
| 固定棋譜 round2 3 局(参考) | 48 | 48 → 20(100% → 42%) | 48 → 46(100% → 96%) | 9 → 9 | 9 → 8(19% → 17%) | 0 → 26 |
| 1 人目(10 局) | 331 | 257 → 112(78% → 34%) | 297 → 262(90% → 79%) | 47 → 47 | 42 → 22(13% → 7%) | 84 → 344 |
| 2 人目(20 局) | 754 | 257 → 135(34% → 18%) | 674 → 483(89% → 64%) | 75 → 75 | 69 → 54(9% → 7%) | 876 → 1827 |
| 3 人目(20 局) | 998 | 327 → 192(33% → 19%) | 621 → 476(62% → 48%) | 111 → 111 | 93 → 92(9% → 9%) | 911 → 1729 |
| 4 人目(20 局) | 652 | 426 → 257(65% → 39%) | 652 → 594(100% → 91%) | 53 → 53 | 46 → 42(7% → 6%) | 308 → 841 |
| **4 人合計(70 局)** | 2735 | 1267 → 696(46% → 25%) | 2244 → 1815(82% → 66%) | 286 → 286 | 250 → 210(9% → 8%) | 2179 → 4741 |

**この前後の数は「本体に入れたらどうなるか」の測定であり、本体の今の挙動ではない**(下書きは `data/drafts/` にあり、本体は読まない。測定は渡す集合を明示して回しているので置き場に依存しない)。

**読み方(過大にも過小にも読まない)**:

- 「形だけ沈黙」の減り(30 手まで 757 → 471)の大半は、**証拠 1 件で立つ forming**による(舟囲いは 5八金 1 手、矢倉は 7八金か 7七銀 1 手で forming になる。1 人目は玉が 5九のままの局で矢倉 forming が 155 局面)。それは I-9 型が 531 → 1292 に増えていることと同じ事実である。
- 証拠 2 件以上か完成に限ると、形の沈黙は 30 手までで 1039 → 949(94.8% → 86.6%)、全手で 2244 → 1815(82.0% → 66.4%)。**動いたのは主に 2 人目(居飛車で 7八・8八へ寄せる)と 3 人目(相振りで 3八・4八)**で、1 人目・4 人目(居玉が多い)はほぼ動かない(予測どおり。§1.3)。
- 固定棋譜 4 局は形の沈黙 25 → 25 で不変(2026-09-12 の予-1「形を増やしても 2 局目の沈黙は動かない」と同じ)。
- 狙いの数は前後で同じ(狙いは足していない)。

### 1.7 分かったこと・司令塔の判断待ち

1. **形 3 件を `data/shapes/` に足すと `apps/server` の vitest が 5 本落ちる**(使い捨て worktree で実測。前 731 passed / 0 failed、後 726 / 5。`shapeGraphRanking.test.ts` 1 本・`stateResponse.test.ts` 4 本)。2026-09-12 の U6-A §9.4「`reachableShapes` は上位 3 件だけで、形が増えると銀冠が押し出される」と同じ 5 本。試験が実データを読むため、直すのは `apps/`(開発・診断レーンの持ち物)。**司令塔の判断(2026-09-25、指示書 §5 に反映 `ef07183`): (a) 本体が読まない `data/drafts/2026-09-25-knowledge/{shapes,openings}/` に置く。** 理由は試験が赤くなるだけでなく、本体が読んで対局中の「目指せる形」上位 3 件から銀冠が押し出される(挙動の変更)ため。`data/shapes|openings/` へ移すのは司令塔の判断で、この席は移さない。`data/drafts/` は `validate:data` の対象外なので、使い捨て worktree の `data/shapes|openings/` に 5 件を置いて `node scripts/validate-data.mjs` を回し **28 件 検証OK**(既存 23 + 5。`leads_to_shape_ids` の参照先を含む)。共有ツリーでは 23 件 検証OK(drafts は読まれない。`shapeRepository.ts` の `DEFAULT_SHAPES_DIR` は `data/shapes` 固定)。
2. 狙い 3 件が相手の 1 手で forming になる(§1.3)。判定の話なので触らない。
3. 居玉(玉 5九のまま)に当たる形は無く、20/70 局の形の沈黙は形では埋まらない(U6-A §9.6 の再確認)。埋めるなら狙いか③の側。
4. 相手側の陣形(`side: opponent` の shapes)は 0 件のまま。相手玉は 8二(11)・3二(8)・7二(7)に多く、相手の美濃・矢倉を足せば相手の陣形も認識できるが、`side: opponent` の形は `rankReachableShapes` が除外するので④には影響しない見込み(未測定)。次のまとまりの候補。
5. openings の id に側が入っていない(`ibisha` は opponent、`shikenbisha` は self)。自分側の居飛車を足すには id の衝突を避ける必要があり `ibisha_self` とした。**司令塔の判断(2026-09-25): openings スキーマの side(self/opponent)の設計どおりなので暫定ではなく、そのままでよい。**
6. 2026-09-12 に退避した下書き 4 件(金無双・舟囲い・矢倉・雁木)は scratchpad にあったため**もう残っていない**(検索して 0 件)。今回は出典から書き直した。**scratchpad は消える**ので、下書きは記録に写す(付録 B)。

### 1.8 使った道具と置き場

- scratchpad `measure/measure.ts`(前後の JSON: `before-30/0.json`・`after-30/0.json`・候補 `cand2-0.json`)。消えたら付録 B の JSON と §1.2 の呼び方から作り直せる。
- 下書き 5 件の JSON の置き場は `data/drafts/2026-09-25-knowledge/{shapes,openings}/`(最終の置き場と同じ階層。移すときは `git mv` だけで済む)。付録 B は同じ内容の写し。


## 2. 目録(網羅の物差し。2026-09-25 の人間の決定「すべてを網羅」を受けて)

**出どころ**: Wikipedia「Category:将棋の囲い」(49 記事 + 下位「矢倉」32 記事)・「Category:将棋の戦法」の下位(居飛車 26 + 相掛かり 11・角換わり 6・対振り飛車 33・矢倉 32・横歩取り 10 / 振り飛車 11 + 中飛車 15・四間飛車 7・三間飛車 12・向かい飛車 10 / 奇襲戦法 20)・「将棋の戦法一覧」、解説サイト shogi-gym.com(囲い 37 種)・shougi.jp(囲い一覧)。**日本将棋連盟の公開ページは一覧・個別とも取得できなかった(HTTP 404。検索経由で個別コラムの URL は分かるが本文を読めない)ので、目録の出典には使っていない**(参照日 2026-09-25)。
**列の意味**: 「個別ページ」= 座標・手順を起こせる解説ページの URL。無いものは**出典なし**(一覧に名前があるだけ)で、**埋めない**。「状態」= 未 / 下書き済み(id) / 既存(id) / 対象外。別名は 1 行にまとめる。

**数**: 囲い N = 62(うち出典なし 10、埋まった 6)/ 戦法 M = 184(うち出典なし 41、埋まった 7。駒落ちは対象外で数に入れない)。狙い(intents)の目録は戦法の目録から起こす(順は 囲い → 戦法 → 狙い)。

### 2.1 囲いの目録

| # | 名前 | 別名 | 系統 | 個別ページ | 一覧の出典 | 状態 |
|---|---|---|---|---|---|---|
| 1 | 矢倉囲い(金矢倉) | 矢倉 | 矢倉系 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(yagura_kinyagura) |
| 2 | 銀矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E9%8A%80%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 3 | 片矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E7%89%87%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 4 | 総矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E7%B7%8F%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 5 | 銀立ち矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E9%8A%80%E7%AB%8B%E3%81%A1%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 6 | 菱矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E8%8F%B1%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 7 | 土居矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E5%9C%9F%E5%B1%85%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 8 | 天野矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E5%A4%A9%E9%87%8E%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 9 | 矢倉早囲い |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E6%97%A9%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 10 | 矢倉穴熊 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 11 | 右矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E5%8F%B3%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 12 | カニ囲い |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E3%82%AB%E3%83%8B%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 13 | 菊水矢倉 |  | 矢倉系 | <https://shogi-gym.com/kakoi/yagura/kikusui-yagura/> | <https://shogi-gym.com/kakoi/> | 未 |
| 14 | 富士見矢倉 |  | 矢倉系 | **出典なし** | <https://www.shougi.jp/kakoi/> | 未 |
| 15 | へこみ矢倉 |  | 矢倉系 | **出典なし** | <https://www.shougi.jp/kakoi/> | 未 |
| 16 | 流れ矢倉 |  | 矢倉系 | **出典なし** | <https://www.shougi.jp/kakoi/> | 未 |
| 17 | 流線矢倉 |  | 矢倉系 | **出典なし** | <https://www.shougi.jp/kakoi/> | 未 |
| 18 | 角矢倉 |  | 矢倉系 | **出典なし** | <https://www.shougi.jp/kakoi/> | 未 |
| 19 | 本美濃囲い | 美濃囲い | 美濃系 | <https://ja.wikipedia.org/wiki/%E6%9C%AC%E7%BE%8E%E6%BF%83%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 既存(mino_honmino) |
| 20 | 高美濃囲い |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E9%AB%98%E7%BE%8E%E6%BF%83%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 既存(mino_takamino) |
| 21 | 銀冠 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E7%BE%8E%E6%BF%83%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 既存(mino_ginkanmuri) |
| 22 | 片美濃囲い |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E7%89%87%E7%BE%8E%E6%BF%83%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 23 | 木村美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E6%9C%A8%E6%9D%91%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 24 | ダイヤモンド美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E3%83%80%E3%82%A4%E3%83%A4%E3%83%A2%E3%83%B3%E3%83%89%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 25 | 金美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E9%87%91%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 26 | 銀美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E9%8A%80%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 27 | ちょんまげ美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E3%81%A1%E3%82%87%E3%82%93%E3%81%BE%E3%81%92%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 28 | 坊主美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E5%9D%8A%E4%B8%BB%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 29 | 四枚美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E5%9B%9B%E6%9E%9A%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 30 | 天守閣美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E5%A4%A9%E5%AE%88%E9%96%A3%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 31 | 左美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E5%B7%A6%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 32 | 居飛車銀冠 |  | 美濃系(居飛車) | <https://shogi-gym.com/kakoi/mino/hidarimino/> | <https://shogi-gym.com/kakoi/> | 未 |
| 33 | 振り飛車早囲い | 早囲い | 美濃系 | <https://shogi-gym.com/kakoi/furibisha-hayagakoi/> | <https://shogi-gym.com/kakoi/> | 未 |
| 34 | 三手囲い |  | その他(振り飛車) | <https://www.shogi.or.jp/column/2019/04/kakoi_65.html> | <https://www.shougi.jp/kakoi/> | 未 |
| 35 | 穴熊囲い |  | 穴熊系 | <https://ja.wikipedia.org/wiki/%E7%A9%B4%E7%86%8A%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 36 | 居飛車穴熊 |  | 穴熊系 | <https://ja.wikipedia.org/wiki/%E5%B1%85%E9%A3%9B%E8%BB%8A%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 37 | 振り飛車穴熊 |  | 穴熊系 | <https://ja.wikipedia.org/wiki/%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 38 | 松尾流穴熊 |  | 穴熊系 | <https://ja.wikipedia.org/wiki/%E6%9D%BE%E5%B0%BE%E6%B5%81%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 39 | 一直線穴熊 |  | 穴熊系 | <https://ja.wikipedia.org/wiki/%E4%B8%80%E7%9B%B4%E7%B7%9A%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 40 | ビッグ4 |  | 穴熊系 | <https://ja.wikipedia.org/wiki/%E3%83%93%E3%83%83%E3%82%B04%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 41 | 銀冠穴熊 |  | 穴熊系 | <https://shogi-gym.com/kakoi/anaguma/ginkan-anaguma/> | <https://shogi-gym.com/kakoi/> | 未 |
| 42 | 舟囲い |  | 舟囲い系 | <https://ja.wikipedia.org/wiki/%E8%88%9F%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(funagakoi) |
| 43 | 箱入り娘 |  | 舟囲い系 | <https://ja.wikipedia.org/wiki/%E7%AE%B1%E5%85%A5%E3%82%8A%E5%A8%98%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 44 | Elmo囲い | エルモ囲い | 舟囲い系 | <https://ja.wikipedia.org/wiki/Elmo%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 45 | 串カツ囲い |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E4%B8%B2%E3%82%AB%E3%83%84%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 46 | ミレニアム囲い | トーチカ | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E3%83%9F%E3%83%AC%E3%83%8B%E3%82%A2%E3%83%A0%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 47 | 振り飛車ミレニアム |  | その他(振り飛車) | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 48 | 金無双 | 二枚金 | 相振り | <https://ja.wikipedia.org/wiki/%E9%87%91%E7%84%A1%E5%8F%8C> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(kinmusou) |
| 49 | 雁木囲い |  | その他 | <https://ja.wikipedia.org/wiki/%E9%9B%81%E6%9C%A8%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 50 | 中住まい |  | その他 | <https://ja.wikipedia.org/wiki/%E4%B8%AD%E4%BD%8F%E3%81%BE%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 51 | 中原囲い |  | その他 | <https://ja.wikipedia.org/wiki/%E4%B8%AD%E5%8E%9F%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 52 | ボナンザ囲い |  | その他 | <https://ja.wikipedia.org/wiki/%E3%83%9C%E3%83%8A%E3%83%B3%E3%82%B6%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 53 | 金開き |  | その他 | <https://ja.wikipedia.org/wiki/%E9%87%91%E9%96%8B%E3%81%8D> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 54 | 壁囲い |  | その他 | <https://ja.wikipedia.org/wiki/%E5%A3%81%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 55 | いちご囲い | イチゴ囲い | その他 | <https://ja.wikipedia.org/wiki/%E3%81%84%E3%81%A1%E3%81%94%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 56 | アヒル囲い | 大阪囲い | その他 | <https://ja.wikipedia.org/wiki/%E3%82%A2%E3%83%92%E3%83%AB%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 57 | 無敵囲い |  | その他 | <https://ja.wikipedia.org/wiki/%E7%84%A1%E6%95%B5%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 58 | 多伝囲い |  | その他 | <https://ja.wikipedia.org/wiki/%E5%A4%9A%E4%BC%9D%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 未 |
| 59 | 中段玉 |  | その他(居飛車) | **出典なし** | <https://www.shougi.jp/kakoi/> | 未 |
| 60 | 最強囲い |  | その他(居飛車) | **出典なし** | <https://www.shougi.jp/kakoi/> | 未 |
| 61 | トラック囲い |  | その他(居飛車) | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 62 | カタ囲い |  | その他(居飛車) | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 63 | 金象眼・銀象眼 |  | 駒落ち(対象外) | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 対象外(駒落ち) |

### 2.2 戦法の目録

| # | 名前 | 別名 | 分類 | 個別ページ | 一覧の出典 | 状態 |
|---|---|---|---|---|---|---|
| 1 | 居飛車 |  | 居飛車(総称) | <https://ja.wikipedia.org/wiki/%E5%B1%85%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(ibisha_self、自分側)。相手側は既存 ibisha |
| 2 | 相居飛車 |  | 居飛車(総称) | <https://ja.wikipedia.org/wiki/%E7%9B%B8%E5%B1%85%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 3 | 対抗型 |  | 居飛車(総称) | <https://ja.wikipedia.org/wiki/%E5%AF%BE%E6%8A%97%E5%9E%8B> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 4 | 矢倉 |  | 相居飛車 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 5 | 角換わり |  | 相居飛車 | <https://ja.wikipedia.org/wiki/%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 6 | 相掛かり |  | 相居飛車 | <https://ja.wikipedia.org/wiki/%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 7 | 横歩取り |  | 相居飛車 | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 8 | 雁木戦法 | 雁木 | 相居飛車 | <https://ja.wikipedia.org/wiki/%E9%9B%81%E6%9C%A8%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 9 | 矢倉棒銀 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E6%A3%92%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 10 | 雀刺し |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E9%9B%80%E5%88%BA%E3%81%97> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 11 | 森下システム |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E6%A3%AE%E4%B8%8B%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 12 | 脇システム |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E8%84%87%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 13 | 矢倉3七桂 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%893%E4%B8%83%E6%A1%82> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 14 | 矢倉3七銀 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%893%E4%B8%83%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 15 | 四手角 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E5%9B%9B%E6%89%8B%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 16 | 米長流急戦矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%B1%B3%E9%95%B7%E6%B5%81%E6%80%A5%E6%88%A6%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 17 | 阿久津流急戦矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E9%98%BF%E4%B9%85%E6%B4%A5%E6%B5%81%E6%80%A5%E6%88%A6%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 18 | 中原流急戦矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E4%B8%AD%E5%8E%9F%E6%B5%81%E6%80%A5%E6%88%A6%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 19 | 矢倉中飛車 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 20 | 6二飛戦法 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/6%E4%BA%8C%E9%A3%9B%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 21 | カニカニ銀 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E3%82%AB%E3%83%8B%E3%82%AB%E3%83%8B%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 22 | 矢倉3五歩早仕掛け |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%893%E4%BA%94%E6%AD%A9%E6%97%A9%E4%BB%95%E6%8E%9B%E3%81%91> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 23 | 無理矢理矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%84%A1%E7%90%86%E7%9F%A2%E7%90%86%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 24 | ウソ矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E3%82%A6%E3%82%BD%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 25 | 同型矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E5%90%8C%E5%9E%8B%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 26 | 飛車先不突矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E9%A3%9B%E8%BB%8A%E5%85%88%E4%B8%8D%E7%AA%81%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 27 | 金立ち戦法 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E9%87%91%E7%AB%8B%E3%81%A1%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 28 | 忍者銀 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E5%BF%8D%E8%80%85%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 未 |
| 29 | 加藤流(矢倉) |  | 矢倉の指し方 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 30 | 三手角 |  | 矢倉の指し方 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 31 | 右四間飛車(矢倉・腰掛け銀型) |  | 矢倉の指し方 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 32 | 角換わり腰掛け銀 |  | 角換わり | <https://ja.wikipedia.org/wiki/%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A%E8%85%B0%E6%8E%9B%E3%81%91%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | 未 |
| 33 | 角換わり棒銀 |  | 角換わり | <https://ja.wikipedia.org/wiki/%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A%E6%A3%92%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | 未 |
| 34 | 筋違い角 |  | 角換わり | <https://ja.wikipedia.org/wiki/%E7%AD%8B%E9%81%95%E3%81%84%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | 未 |
| 35 | 後手番一手損角換わり |  | 角換わり | <https://ja.wikipedia.org/wiki/%E5%BE%8C%E6%89%8B%E7%95%AA%E4%B8%80%E6%89%8B%E6%90%8D%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | 未 |
| 36 | 木村定跡 |  | 角換わり | <https://ja.wikipedia.org/wiki/%E6%9C%A8%E6%9D%91%E5%AE%9A%E8%B7%A1> | <https://ja.wikipedia.org/wiki/Category%3A%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | 未 |
| 37 | 早繰り銀 |  | 角換わり・相掛かり | <https://ja.wikipedia.org/wiki/%E6%97%A9%E7%B9%B0%E3%82%8A%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 38 | 相掛かり棒銀 |  | 相掛かり | <https://ja.wikipedia.org/wiki/%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A%E6%A3%92%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 未 |
| 39 | 塚田スペシャル |  | 相掛かり | <https://ja.wikipedia.org/wiki/%E5%A1%9A%E7%94%B0%E3%82%B9%E3%83%9A%E3%82%B7%E3%83%A3%E3%83%AB> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 未 |
| 40 | 相掛かり腰掛け銀 |  | 相掛かり | <https://ja.wikipedia.org/wiki/%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A%E8%85%B0%E6%8E%9B%E3%81%91%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 未 |
| 41 | 鎖鎌銀 |  | 相掛かり | <https://ja.wikipedia.org/wiki/%E9%8E%96%E9%8E%8C%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 未 |
| 42 | ひねり飛車 |  | 相掛かり | <https://ja.wikipedia.org/wiki/%E3%81%B2%E3%81%AD%E3%82%8A%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 未 |
| 43 | 縦歩取り |  | 相掛かり | <https://ja.wikipedia.org/wiki/%E7%B8%A6%E6%AD%A9%E5%8F%96%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 未 |
| 44 | UFO銀 |  | 相掛かり | <https://ja.wikipedia.org/wiki/UFO%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 未 |
| 45 | 中原流相掛かり |  | 相掛かり | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 46 | 新旧対抗型 |  | 相掛かり | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 47 | 飛車先交換早繰り銀 |  | 相掛かり | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 48 | 飛車先交換腰掛け銀 |  | 相掛かり | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 49 | 横歩取り3三角 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A3%E4%B8%89%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 未 |
| 50 | 横歩取り3三桂 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A3%E4%B8%89%E6%A1%82> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 未 |
| 51 | 横歩取り2三歩 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A2%E4%B8%89%E6%AD%A9> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 未 |
| 52 | 横歩取り4五角 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A4%E4%BA%94%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 未 |
| 53 | 横歩取り4四角 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A4%E5%9B%9B%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 未 |
| 54 | 横歩取り8五飛 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A8%E4%BA%94%E9%A3%9B> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 未 |
| 55 | 相横歩取り |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E7%9B%B8%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 未 |
| 56 | ノーガード戦法 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E3%83%8E%E3%83%BC%E3%82%AC%E3%83%BC%E3%83%89%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 未 |
| 57 | 空中戦法(内藤流) |  | 横歩取り | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 58 | 中座飛車 |  | 横歩取り | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 59 | 3三飛成戦法 |  | 横歩取り | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 60 | 棒銀 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E6%A3%92%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 61 | 腰掛け銀 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E8%85%B0%E6%8E%9B%E3%81%91%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 62 | 右四間飛車 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E5%8F%B3%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 63 | 袖飛車 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E8%A2%96%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 64 | 一間飛車 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E4%B8%80%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 65 | 一間飛車穴熊 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E4%B8%80%E9%96%93%E9%A3%9B%E8%BB%8A%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 66 | 引き角 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E5%BC%95%E3%81%8D%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 67 | 右玉 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E5%8F%B3%E7%8E%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 68 | 嬉野流 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E5%AC%89%E9%87%8E%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 69 | 村田システム |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E6%9D%91%E7%94%B0%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 70 | 二枚銀 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E4%BA%8C%E6%9E%9A%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 71 | 3八飛戦法 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/3%E5%85%AB%E9%A3%9B%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 72 | 4七銀型 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/4%E4%B8%83%E9%8A%80%E5%9E%8B> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 73 | 3三角戦法 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/3%E4%B8%89%E8%A7%92%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 74 | 原始棒銀 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E5%8E%9F%E5%A7%8B%E6%A3%92%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 未 |
| 75 | 4六銀左戦法 | 斜め棒銀 | 対振り急戦 | <https://ja.wikipedia.org/wiki/4%E5%85%AD%E9%8A%80%E5%B7%A6%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 既存 intent naname_bogin(相手側) |
| 76 | 4五歩早仕掛け |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/4%E4%BA%94%E6%AD%A9%E6%97%A9%E4%BB%95%E6%8E%9B%E3%81%91> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 既存 intent hayajikake(相手側) |
| 77 | 対振り棒銀 | 棒銀 | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E6%A3%92%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 既存 intent boh_gin(相手側) |
| 78 | 鷺宮定跡 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E9%B7%BA%E5%AE%AE%E5%AE%9A%E8%B7%A1> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 79 | 山田定跡 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E5%B1%B1%E7%94%B0%E5%AE%9A%E8%B7%A1> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 80 | 4六銀右戦法 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/4%E5%85%AD%E9%8A%80%E5%8F%B3%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 81 | 鳥刺し (将棋) |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E9%B3%A5%E5%88%BA%E3%81%97%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 82 | ポンポン桂 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E3%83%9D%E3%83%B3%E3%83%9D%E3%83%B3%E6%A1%82> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 83 | 4六金戦法 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/4%E5%85%AD%E9%87%91%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 84 | 加藤流袖飛車 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E5%8A%A0%E8%97%A4%E6%B5%81%E8%A2%96%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 85 | 三歩突き捨て急戦 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E4%B8%89%E6%AD%A9%E7%AA%81%E3%81%8D%E6%8D%A8%E3%81%A6%E6%80%A5%E6%88%A6> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 86 | 三間飛車破り |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A%E7%A0%B4%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 87 | 棒金 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E6%A3%92%E9%87%91> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 88 | 超速3七銀 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E8%B6%85%E9%80%9F3%E4%B8%83%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 89 | 丸山ワクチン (将棋) |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E4%B8%B8%E5%B1%B1%E3%83%AF%E3%82%AF%E3%83%81%E3%83%B3%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 90 | 横歩取り (対中飛車) |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A%20%28%E5%AF%BE%E4%B8%AD%E9%A3%9B%E8%BB%8A%29> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 91 | へなちょこ急戦 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E3%81%B8%E3%81%AA%E3%81%A1%E3%82%87%E3%81%93%E6%80%A5%E6%88%A6> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 92 | 居飛車舟囲い急戦 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E5%B1%85%E9%A3%9B%E8%BB%8A%E8%88%9F%E5%9B%B2%E3%81%84%E6%80%A5%E6%88%A6> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 93 | 地下鉄飛車 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E5%9C%B0%E4%B8%8B%E9%89%84%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 94 | 四手角 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E5%9B%9B%E6%89%8B%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 95 | 5八金右超急戦 |  | 対振り急戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 96 | 英春流右四間 |  | 対振り急戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 97 | 5七金戦法(対玉頭銀) |  | 対振り急戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 98 | 二枚銀3八飛型 |  | 対振り急戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 99 | きmきm金 |  | 対振り急戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 100 | 居飛車穴熊(戦法) |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E5%B1%85%E9%A3%9B%E8%BB%8A%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 101 | 左美濃(戦法) |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E5%B7%A6%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 102 | 玉頭位取り |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E7%8E%89%E9%A0%AD%E4%BD%8D%E5%8F%96%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 103 | 5筋位取り |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/5%E7%AD%8B%E4%BD%8D%E5%8F%96%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 104 | 6筋位取り |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/6%E7%AD%8B%E4%BD%8D%E5%8F%96%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 105 | 飯島流引き角戦法 |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E9%A3%AF%E5%B3%B6%E6%B5%81%E5%BC%95%E3%81%8D%E8%A7%92%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 106 | 都成流 |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E9%83%BD%E6%88%90%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 107 | 位取り戦法 |  | 対振り持久戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 108 | 糸谷流右玉 |  | 対振り持久戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 109 | ホラ囲い |  | 対振り持久戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 110 | 端美濃・串カツ戦法 |  | 対振り持久戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 111 | トーチカ戦法 |  | 対振り持久戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 112 | 振り飛車 |  | 振り飛車(総称) | <https://ja.wikipedia.org/wiki/%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 113 | 相振り飛車 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E7%9B%B8%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 114 | 角交換振り飛車 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E8%A7%92%E4%BA%A4%E6%8F%9B%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 115 | 角交換相振り飛車 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E8%A7%92%E4%BA%A4%E6%8F%9B%E7%9B%B8%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 116 | 陽動振り飛車 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E9%99%BD%E5%8B%95%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 117 | 玉頭銀 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E7%8E%89%E9%A0%AD%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 118 | 左玉 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E5%B7%A6%E7%8E%89> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 119 | 高田流左玉 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E9%AB%98%E7%94%B0%E6%B5%81%E5%B7%A6%E7%8E%89> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 未 |
| 120 | 中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 既存 opening nakabisha(相手側)+ intent nakabisha_kuraidori |
| 121 | ゴキゲン中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E3%82%B4%E3%82%AD%E3%82%B2%E3%83%B3%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 未 |
| 122 | ツノ銀中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E3%83%84%E3%83%8E%E9%8A%80%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 未 |
| 123 | 原始中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E5%8E%9F%E5%A7%8B%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 未 |
| 124 | 先手中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E5%85%88%E6%89%8B%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 未 |
| 125 | 風車 (将棋) |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E9%A2%A8%E8%BB%8A%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 未 |
| 126 | 5筋位取り中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/5%E7%AD%8B%E4%BD%8D%E5%8F%96%E3%82%8A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 未 |
| 127 | 英ちゃん流中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E8%8B%B1%E3%81%A1%E3%82%83%E3%82%93%E6%B5%81%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 未 |
| 128 | 平目 (将棋) |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E5%B9%B3%E7%9B%AE%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 未 |
| 129 | 矢倉流中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E6%B5%81%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 未 |
| 130 | 中飛車左穴熊 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E4%B8%AD%E9%A3%9B%E8%BB%8A%E5%B7%A6%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 未 |
| 131 | 鬼六流ドッカン飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E9%AC%BC%E5%85%AD%E6%B5%81%E3%83%89%E3%83%83%E3%82%AB%E3%83%B3%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 未 |
| 132 | 5五龍中飛車 |  | 中飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 133 | 中飛車早繰り銀 |  | 中飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 134 | 角交換型中飛車 |  | 中飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 135 | 四間飛車 |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 既存 opening shikenbisha(自分側) |
| 136 | 藤井システム |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E8%97%A4%E4%BA%95%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 137 | 角交換四間飛車 |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E8%A7%92%E4%BA%A4%E6%8F%9B%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 138 | 立石流四間飛車 |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E7%AB%8B%E7%9F%B3%E6%B5%81%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 139 | レグスペ |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E3%83%AC%E3%82%B0%E3%82%B9%E3%83%9A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 140 | 耀龍四間飛車 |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E8%80%80%E9%BE%8D%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 141 | 室岡システム |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E5%AE%A4%E5%B2%A1%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 142 | 錆刀戦法(宗歩四間飛車) |  | 四間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 143 | 4五歩ポン |  | 四間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 144 | 筋違い角四間飛車 |  | 四間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 145 | 三間飛車 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 146 | 石田流 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E7%9F%B3%E7%94%B0%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 147 | 早石田 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E6%97%A9%E7%9F%B3%E7%94%B0> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 148 | 升田式石田流 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E5%8D%87%E7%94%B0%E5%BC%8F%E7%9F%B3%E7%94%B0%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 149 | 新石田流 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E6%96%B0%E7%9F%B3%E7%94%B0%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 150 | 楠本式石田流 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E6%A5%A0%E6%9C%AC%E5%BC%8F%E7%9F%B3%E7%94%B0%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 151 | 鬼殺し (将棋) |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E9%AC%BC%E6%AE%BA%E3%81%97%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 152 | 新鬼殺し |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E6%96%B0%E9%AC%BC%E6%AE%BA%E3%81%97> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 153 | 真部流 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E7%9C%9F%E9%83%A8%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 154 | 中田功XP |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E4%B8%AD%E7%94%B0%E5%8A%9FXP> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 155 | トマホーク (将棋) |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E3%83%88%E3%83%9E%E3%83%9B%E3%83%BC%E3%82%AF%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 156 | 2手目△3二飛 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/2%E6%89%8B%E7%9B%AE%E2%96%B33%E4%BA%8C%E9%A3%9B> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 未 |
| 157 | 大野流三間飛車 |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 158 | 下町流三間飛車 |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 159 | カナケンシステム |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 160 | 久保システム |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 161 | 菅井流 |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 162 | 阪田流三間飛車 |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 163 | 初手▲7八飛(猫だまし) |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 164 | 三間飛車藤井システム |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 165 | 向かい飛車 |  | 向かい飛車 | <https://ja.wikipedia.org/wiki/%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | 下書き済み(mukaibisha、自分側) |
| 166 | ダイレクト向かい飛車 |  | 向かい飛車 | <https://ja.wikipedia.org/wiki/%E3%83%80%E3%82%A4%E3%83%AC%E3%82%AF%E3%83%88%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | 未 |
| 167 | メリケン向かい飛車 |  | 向かい飛車 | <https://ja.wikipedia.org/wiki/%E3%83%A1%E3%83%AA%E3%82%B1%E3%83%B3%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | 未 |
| 168 | 阪田流向かい飛車 |  | 向かい飛車 | <https://ja.wikipedia.org/wiki/%E9%98%AA%E7%94%B0%E6%B5%81%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | 未 |
| 169 | 鬼殺し向かい飛車 |  | 向かい飛車 | <https://ja.wikipedia.org/wiki/%E9%AC%BC%E6%AE%BA%E3%81%97%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | 未 |
| 170 | 金沢流 |  | 向かい飛車 | <https://ja.wikipedia.org/wiki/%E9%87%91%E6%B2%A2%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | 未 |
| 171 | 升田流向かい飛車 |  | 向かい飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 172 | 大野流向かい飛車 |  | 向かい飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 173 | 二手損向かい飛車 |  | 向かい飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 174 | 4手目△3三角戦法 |  | 向かい飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 175 | 筋違い角向かい飛車 |  | 向かい飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 176 | 里見流流れ金無双 |  | 向かい飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 177 | △3三桂戦法(相振り) |  | 相振り飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 未 |
| 178 | 4四歩パックマン |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/4%E5%9B%9B%E6%AD%A9%E3%83%91%E3%83%83%E3%82%AF%E3%83%9E%E3%83%B3> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 未 |
| 179 | 角頭歩戦法 |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/%E8%A7%92%E9%A0%AD%E6%AD%A9%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 未 |
| 180 | カメレオン戦法 |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/%E3%82%AB%E3%83%A1%E3%83%AC%E3%82%AA%E3%83%B3%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 未 |
| 181 | 新米長玉 |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/%E6%96%B0%E7%B1%B3%E9%95%B7%E7%8E%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 未 |
| 182 | 珍玉 |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/%E7%8F%8D%E7%8E%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 未 |
| 183 | 英春流 |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/%E8%8B%B1%E6%98%A5%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 未 |
| 184 | アヒル戦法 |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/%E3%82%A2%E3%83%92%E3%83%AB%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 未 |
| 185 | 駒落ちの戦法(下手棒銀・銀多伝ほか 30 余) |  | 駒落ち(対象外) | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 対象外(駒落ち。本アプリは平手) |

## 付録 A. 局ごとの一覧(4 人 70 局。40 手目と終局時の自玉・自飛の筋・相手玉・相手飛の筋、形の認識の前後)

`S玉`=自玉、`S飛`=自飛の筋(複数なら並べる、無ければ -)、`G玉`=相手玉、`G飛`=相手飛の筋。「形(証拠2+)」= その局の先手番の局面のうち、証拠 2 件以上か完成の形があった局面の数(前 → 後)。

| 対象 | id | 手数 | 40 手目 | 終局時 | 局面数 | 形あり 前→後 | 形(証拠2+) 前→後 |
|---|---|---|---|---|---|---|---|
| 1 人目 | kifu-01 | 51 | S玉5i/S飛4/G玉5a/G飛8 | S玉5i/S飛-/G玉5a/G飛9 | 26 | 0 → 5 | 0 → 0 |
| 1 人目 | kifu-02 | 37 | S玉5i/S飛8/G玉6b/G飛8 | S玉5i/S飛8/G玉6b/G飛8 | 19 | 0 → 5 | 0 → 0 |
| 1 人目 | kifu-03 | 69 | S玉5i/S飛8/G玉3b/G飛- | S玉5i/S飛-/G玉3b/G飛- | 35 | 0 → 26 | 0 → 0 |
| 1 人目 | kifu-04 | 49 | S玉6i/S飛2/G玉3b/G飛6 | S玉6i/S飛2/G玉3a/G飛4 | 25 | 0 → 24 | 0 → 0 |
| 1 人目 | kifu-05 | 107 | S玉8h/S飛2/G玉8b/G飛2 | S玉8h/S飛-/G玉9b/G飛- | 54 | 36 → 42 | 34 → 34 |
| 1 人目 | kifu-06 | 107 | S玉8h/S飛2/G玉8b/G飛5 | S玉8h/S飛-/G玉8b/G飛1 | 54 | 32 → 53 | 0 → 35 |
| 1 人目 | kifu-07 | 89 | S玉5i/S飛7/G玉5a/G飛8 | S玉5i/S飛-/G玉5d/G飛- | 45 | 0 → 22 | 0 → 0 |
| 1 人目 | kifu-08 | 43 | S玉5i/S飛3/G玉4a/G飛8 | S玉5i/S飛-/G玉3b/G飛8 | 22 | 5 → 16 | 0 → 0 |
| 1 人目 | kifu-09 | 25 | S玉5i/S飛3/G玉3b/G飛8 | S玉5i/S飛3/G玉3b/G飛8 | 13 | 0 → 4 | 0 → 0 |
| 1 人目 | kifu-10 | 75 | S玉5i/S飛2/G玉5a/G飛5 | S玉5i/S飛3/G玉7b/G飛- | 38 | 1 → 22 | 0 → 0 |
| 2 人目 | kifu2-01 | 66 | S玉5h/S飛2/G玉5b/G飛8 | S玉5h/S飛-/G玉4a/G飛8 | 34 | 28 → 31 | 16 → 16 |
| 2 人目 | kifu2-02 | 64 | S玉3h/S飛8/G玉8b/G飛3 | S玉3h/S飛-/G玉8b/G飛8 | 33 | 17 → 23 | 0 → 15 |
| 2 人目 | kifu2-03 | 52 | S玉7i/S飛4/G玉3a/G飛8 | S玉7i/S飛4/G玉3a/G飛8 | 27 | 20 → 24 | 0 → 0 |
| 2 人目 | kifu2-04 | 126 | S玉8h/S飛2/G玉7b/G飛8 | S玉8h/S飛1/G玉7b/G飛8 | 64 | 54 → 59 | 2 → 12 |
| 2 人目 | kifu2-05 | 86 | S玉2h/S飛7/G玉2a/G飛8 | S玉2h/S飛-/G玉2a/G飛- | 44 | 34 → 36 | 26 → 26 |
| 2 人目 | kifu2-06 | 72 | S玉7i/S飛5/G玉3a/G飛8 | S玉7i/S飛2/G玉3a/G飛8 | 37 | 26 → 30 | 0 → 0 |
| 2 人目 | kifu2-07 | 94 | S玉7h/S飛2/G玉7b/G飛4 | S玉7h/S飛6/G玉7b/G飛3 | 48 | 39 → 42 | 0 → 41 |
| 2 人目 | kifu2-08 | 98 | S玉6i/S飛2/G玉5a/G飛7 | S玉6h/S飛-/G玉4d/G飛6 | 50 | 40 → 43 | 0 → 3 |
| 2 人目 | kifu2-09 | 50 | S玉8h/S飛2/G玉3a/G飛8 | S玉8h/S飛2/G玉3a/G飛8 | 26 | 15 → 21 | 0 → 0 |
| 2 人目 | kifu2-10 | 150 | S玉4h/S飛2/G玉3b/G飛6 | S玉5g/S飛8/G玉3c/G飛8 | 76 | 45 → 56 | 0 → 9 |
| 2 人目 | kifu2-11 | 41 | S玉4h/S飛2/G玉5a/G飛7 | S玉4h/S飛2/G玉5a/G飛7 | 21 | 11 → 16 | 0 → 0 |
| 2 人目 | kifu2-12 | 67 | S玉8h/S飛2/G玉7b/G飛2 | S玉8h/S飛4/G玉7b/G飛2 | 34 | 17 → 31 | 0 → 26 |
| 2 人目 | kifu2-13 | 57 | S玉2h/S飛6/G玉1a/G飛6 | S玉2h/S飛6/G玉1a/G飛6 | 29 | 19 → 20 | 18 → 18 |
| 2 人目 | kifu2-14 | 43 | S玉5i/S飛2/G玉5a/G飛8 | S玉5i/S飛2/G玉5a/G飛8 | 22 | 15 → 15 | 0 → 12 |
| 2 人目 | kifu2-15 | 127 | S玉7h/S飛2/G玉8b/G飛4 | S玉8e/S飛5/G玉8b/G飛6 | 64 | 25 → 49 | 0 → 21 |
| 2 人目 | kifu2-16 | 15 | S玉5i/S飛2/G玉5a/G飛8 | S玉5i/S飛2/G玉5a/G飛8 | 8 | 0 → 3 | 0 → 0 |
| 2 人目 | kifu2-17 | 83 | S玉8h/S飛2/G玉8b/G飛2 | S玉9i/S飛-/G玉8d/G飛5 | 42 | 32 → 39 | 0 → 9 |
| 2 人目 | kifu2-18 | 39 | S玉7h/S飛4/G玉8b/G飛- | S玉7h/S飛4/G玉8b/G飛- | 20 | 1 → 16 | 0 → 4 |
| 2 人目 | kifu2-19 | 93 | S玉7h/S飛2/G玉8b/G飛- | S玉8h/S飛-/G玉6d/G飛- | 47 | 39 → 43 | 0 → 41 |
| 2 人目 | kifu2-20 | 55 | S玉4h/S飛2/G玉8b/G飛5 | S玉4h/S飛-/G玉8b/G飛5 | 28 | 20 → 22 | 18 → 18 |
| 3 人目 | g01 | 63 | S玉1i/S飛6/G玉2b/G飛8 | S玉1i/S飛8/G玉2b/G飛- | 32 | 15 → 25 | 0 → 0 |
| 3 人目 | g02 | 82 | S玉4h/S飛-/G玉7b/G飛6 | S玉3h/S飛-/G玉7b/G飛9 | 42 | 31 → 32 | 13 → 13 |
| 3 人目 | g03 | 98 | S玉3h/S飛8/G玉8b/G飛7 | S玉2h/S飛-/G玉7e/G飛- | 50 | 38 → 39 | 27 → 38 |
| 3 人目 | g04 | 116 | S玉3h/S飛8/G玉7b/G飛2 | S玉7g/S飛-/G玉7b/G飛- | 59 | 55 → 55 | 0 → 43 |
| 3 人目 | g05 | 64 | S玉2h/S飛6/G玉2b/G飛6 | S玉2h/S飛8/G玉2b/G飛8 | 33 | 21 → 25 | 20 → 20 |
| 3 人目 | g06 | 108 | S玉2h/S飛8/G玉5a/G飛8 | S玉2h/S飛5/G玉4b/G飛8 | 55 | 47 → 47 | 40 → 40 |
| 3 人目 | g07 | 129 | S玉2h/S飛8/G玉2b/G飛8 | S玉2f/S飛-/G玉4c/G飛- | 65 | 57 → 57 | 36 → 36 |
| 3 人目 | g08 | 89 | S玉2h/S飛6/G玉3b/G飛8 | S玉2h/S飛-/G玉4d/G飛- | 45 | 32 → 32 | 27 → 27 |
| 3 人目 | g09 | 109 | S玉2h/S飛8/G玉5b/G飛2 | S玉4e/S飛-/G玉4c/G飛- | 55 | 51 → 51 | 39 → 39 |
| 3 人目 | g10 | 107 | S玉6i/S飛2/G玉2b/G飛8 | S玉7h/S飛-/G玉4c/G飛2 | 54 | 24 → 42 | 0 → 9 |
| 3 人目 | g11 | 110 | S玉2h/S飛8/G玉3b/G飛9 | S玉2h/S飛-/G玉3d/G飛8 | 56 | 47 → 48 | 43 → 43 |
| 3 人目 | g12 | 98 | S玉3i/S飛7/G玉3a/G飛8 | S玉2h/S飛-/G玉3a/G飛37 | 50 | 42 → 42 | 40 → 40 |
| 3 人目 | g13 | 109 | S玉3h/S飛6/G玉3c/G飛6 | S玉3h/S飛-/G玉1b/G飛- | 55 | 0 → 47 | 0 → 19 |
| 3 人目 | g14 | 128 | S玉1i/S飛8/G玉4b/G飛8 | S玉1i/S飛-/G玉2d/G飛- | 65 | 33 → 42 | 1 → 1 |
| 3 人目 | g15 | 96 | S玉2h/S飛8/G玉5a/G飛4 | S玉1g/S飛-/G玉4b/G飛2 | 49 | 34 → 42 | 23 → 23 |
| 3 人目 | g16 | 89 | S玉5h/S飛-/G玉5a/G飛8 | S玉5h/S飛-/G玉6b/G飛5 | 45 | 28 → 39 | 0 → 35 |
| 3 人目 | g17 | 98 | S玉3h/S飛7/G玉8b/G飛3 | S玉4h/S飛-/G玉8b/G飛4 | 50 | 35 → 38 | 0 → 28 |
| 3 人目 | g18 | 117 | S玉2h/S飛7/G玉2b/G飛8 | S玉3g/S飛-/G玉1e/G飛- | 59 | 49 → 49 | 39 → 39 |
| 3 人目 | g19 | 78 | S玉2h/S飛7/G玉6b/G飛4 | S玉2h/S飛8/G玉6b/G飛- | 40 | 32 → 32 | 29 → 29 |
| 3 人目 | g20 | 77 | S玉4h/S飛6/G玉5a/G飛9 | S玉5h/S飛-/G玉2b/G飛7 | 39 | 0 → 22 | 0 → 0 |
| 4 人目 | g01 | 46 | S玉5i/S飛-/G玉5a/G飛8 | S玉4h/S飛-/G玉5a/G飛- | 24 | 0 → 1 | 0 → 0 |
| 4 人目 | g02 | 82 | S玉5i/S飛5/G玉4a/G飛8 | S玉5i/S飛7/G玉4a/G飛- | 42 | 26 → 30 | 0 → 0 |
| 4 人目 | g03 | 76 | S玉5i/S飛2/G玉8b/G飛4 | S玉1e/S飛-/G玉8b/G飛1 | 39 | 25 → 26 | 0 → 10 |
| 4 人目 | g04 | 71 | S玉4g/S飛-/G玉7b/G飛5 | S玉5i/S飛-/G玉7b/G飛- | 36 | 2 → 13 | 0 → 0 |
| 4 人目 | g05 | 53 | S玉5i/S飛46/G玉4e/G飛- | S玉5i/S飛4/G玉4e/G飛- | 27 | 3 → 18 | 0 → 0 |
| 4 人目 | g06 | 114 | S玉5i/S飛-/G玉5a/G飛8 | S玉8h/S飛-/G玉5a/G飛- | 58 | 4 → 25 | 0 → 0 |
| 4 人目 | g07 | 34 | S玉6i/S飛-/G玉5a/G飛- | S玉6i/S飛-/G玉5a/G飛- | 18 | 0 → 0 | 0 → 0 |
| 4 人目 | g08 | 42 | S玉3h/S飛-/G玉5a/G飛68 | S玉3h/S飛-/G玉5a/G飛68 | 22 | 7 → 7 | 0 → 5 |
| 4 人目 | g09 | 62 | S玉5i/S飛8/G玉7a/G飛4 | S玉5i/S飛-/G玉7a/G飛34 | 32 | 27 → 27 | 0 → 0 |
| 4 人目 | g10 | 72 | S玉5i/S飛5/G玉3b/G飛8 | S玉5i/S飛-/G玉3b/G飛- | 37 | 19 → 34 | 0 → 11 |
| 4 人目 | g11 | 68 | S玉6h/S飛-/G玉5a/G飛48 | S玉5h/S飛-/G玉4e/G飛8 | 35 | 10 → 10 | 0 → 0 |
| 4 人目 | g12 | 70 | S玉4h/S飛-/G玉5a/G飛- | S玉1h/S飛-/G玉8c/G飛- | 36 | 20 → 22 | 0 → 0 |
| 4 人目 | g13 | 58 | S玉4i/S飛5/G玉4b/G飛- | S玉3f/S飛5/G玉4b/G飛7 | 30 | 22 → 25 | 0 → 0 |
| 4 人目 | g14 | 84 | S玉5i/S飛3/G玉4b/G飛8 | S玉5i/S飛-/G玉7b/G飛8 | 43 | 30 → 38 | 0 → 30 |
| 4 人目 | g15 | 74 | S玉5i/S飛5/G玉7b/G飛8 | S玉5g/S飛-/G玉7b/G飛29 | 38 | 1 → 14 | 0 → 0 |
| 4 人目 | g16 | 96 | S玉7i/S飛7/G玉3a/G飛8 | S玉9i/S飛7/G玉3c/G飛8 | 49 | 3 → 39 | 0 → 2 |
| 4 人目 | g17 | 23 | S玉4h/S飛5/G玉6b/G飛3 | S玉4h/S飛5/G玉6b/G飛3 | 12 | 0 → 6 | 0 → 0 |
| 4 人目 | g18 | 31 | S玉5i/S飛-/G玉3b/G飛8 | S玉5i/S飛-/G玉3b/G飛8 | 16 | 8 → 8 | 0 → 0 |
| 4 人目 | gl-01 | 13 | S玉5i/S飛2/G玉5a/G飛- | S玉5i/S飛2/G玉5a/G飛- | 7 | 6 → 6 | 0 → 0 |
| 4 人目 | gl-02 | 100 | S玉6i/S飛5/G玉4a/G飛8 | S玉5i/S飛-/G玉3a/G飛- | 51 | 13 → 46 | 0 → 0 |

## 付録 B. 下書き 5 件の JSON(全文の写し。正本は `data/drafts/2026-09-25-knowledge/`)

### `data/drafts/2026-09-25-knowledge/shapes/funagakoi.json`(最終の置き場は `data/shapes|openings/`。移すのは司令塔)

```json
{
  "id": "funagakoi",
  "name": "舟囲い",
  "name_kana": "ふながこい",
  "side": "self",
  "family": "舟囲い系",
  "parent_shape_id": null,
  "required_pieces": [
    {
      "piece": "玉",
      "square": "7h",
      "optional": false
    },
    {
      "piece": "銀",
      "square": "7i",
      "optional": false
    },
    {
      "piece": "金",
      "square": "6i",
      "optional": false
    },
    {
      "piece": "金",
      "square": "5h",
      "optional": false
    },
    {
      "piece": "銀",
      "square": "4h",
      "optional": false
    }
  ],
  "typical_build_order": [
    "7h",
    "5h",
    "4h",
    "7i",
    "6i"
  ],
  "characteristics": "居飛車(飛車を右側に置いたまま戦う指し方)で、相手が振り飛車(飛車を左側へ動かす指し方)のときによく使われる、短い手数でできる囲いです。玉を7八へ寄せ、右の金を5八へ上げ、右の銀を4八へ上げます。左の銀(7九)と左の金(6九)は最初の位置のままです。横から見た形が舟に似ていることからこの名前で呼ばれます。",
  "beginner_friendliness": {
    "score": 5,
    "reason": "動かす駒が玉・金・銀の3枚だけで手数が短く、序盤の早い段階で形になります。固さより速さを優先した囲いで、急戦(早く戦いを起こす作戦)と組み合わせて使われます(暫定評価。将棋知識としての最終確認は人間のレビューが必要)。"
  },
  "weak_against": "手数が短いぶん固さは控えめで、玉のまわりの守りの駒が少ないため、相手の攻めが玉の近くまで届くと受けにくくなりやすいです。長い戦いになると、より固い囲い(矢倉・穴熊など)に比べて頼りない場面が出やすいです。",
  "source": "【AI起草 / 出典は下記。座標の一次資料確認は行っていない(docs/ROLES.md の保留事項)】先手基準の完成形座標(7八玉・7九銀・6九金・5八金・4八銀)は、Wikipedia『舟囲い』の『名称の由来』の文『囲いの形は、8八角、7八玉、7九銀、6九金、5八金、4八銀型であり』(https://ja.wikipedia.org/wiki/舟囲い、2026-09-25 取得)をそのまま写した(8八角は囲いの駒ではなく初期位置の角なので required_pieces に入れていない)。7九銀・6九金は初期位置と同じマスであるため、指し手による証拠(formationEvidence)は玉・5八金・4八銀の 3 マスからしか生じない(apps/server/src/analysis/shapeFormationAnalyzer.ts の仕組み上の注記)。typical_build_order の並びは出典に無く、書いた側が置いたもの(推測)。追加の経緯: 2026-09-25 の知識レーン(docs/KNOWLEDGE_LANE_BRIEF_2026-09-25.md)。",
  "confidence_level": "medium",
  "review_status": "draft"
}
```

### `data/drafts/2026-09-25-knowledge/shapes/kinmusou.json`(最終の置き場は `data/shapes|openings/`。移すのは司令塔)

```json
{
  "id": "kinmusou",
  "name": "金無双",
  "name_kana": "きんむそう",
  "side": "self",
  "family": "金無双系",
  "parent_shape_id": null,
  "required_pieces": [
    {
      "piece": "玉",
      "square": "3h",
      "optional": false
    },
    {
      "piece": "金",
      "square": "4h",
      "optional": false
    },
    {
      "piece": "金",
      "square": "5h",
      "optional": false
    },
    {
      "piece": "銀",
      "square": "2h",
      "optional": true
    }
  ],
  "typical_build_order": [
    "3h",
    "5h",
    "4h",
    "2h"
  ],
  "characteristics": "金を2枚横に並べる囲いで、自分も相手も振り飛車(飛車を左側へ動かす指し方)にする対局(相振り飛車と呼びます)でよく使われます。玉を3八へ寄せ、左の金を5八、右の金を4八へ動かして、玉の横に金が2枚並びます。上からの攻めを2枚の金で受け止める形で、美濃囲いより上に厚いのが特徴です。",
  "beginner_friendliness": {
    "score": 4,
    "reason": "動かす駒が少なく形も覚えやすいですが、どの対局でも使える囲いではなく、相手も振り飛車のときに向いた囲いです(暫定評価。将棋知識としての最終確認は人間のレビューが必要)。"
  },
  "weak_against": "上からの攻めには厚い一方、横から(玉の横の段を通って)攻められることには弱さが残りやすいです。金が2枚とも玉のそばにあるため、金を攻められて動かされると玉の守りが薄くなります。",
  "source": "【AI起草 / 出典は下記。座標の一次資料確認は行っていない(docs/ROLES.md の保留事項)】先手基準の座標(3八玉・5八金・4八金)は、Wikipedia『金無双』の文『玉を3八に、左金を5八に、右金を4八に動かして作られる』(https://ja.wikipedia.org/wiki/金無双、2026-09-25 取得)をそのまま写した。2八銀は同記事の図から読み取ったもので本文の座標記述ではないため optional: true とした(推測)。typical_build_order は出典の文の順(玉→左金→右金)に optional の銀を最後に足したもの。追加の経緯: 2026-09-25 の知識レーン(docs/KNOWLEDGE_LANE_BRIEF_2026-09-25.md)。3 人目の実棋譜に、自分も相手も振り飛車で玉を 3八・4八へ寄せた局が複数あった。",
  "confidence_level": "medium",
  "review_status": "draft"
}
```

### `data/drafts/2026-09-25-knowledge/shapes/yagura_kinyagura.json`(最終の置き場は `data/shapes|openings/`。移すのは司令塔)

```json
{
  "id": "yagura_kinyagura",
  "name": "矢倉囲い(金矢倉)",
  "name_kana": "やぐらがこい(きんやぐら)",
  "side": "self",
  "family": "矢倉系",
  "parent_shape_id": null,
  "required_pieces": [
    {
      "piece": "玉",
      "square": "8h",
      "optional": false
    },
    {
      "piece": "金",
      "square": "7h",
      "optional": false
    },
    {
      "piece": "銀",
      "square": "7g",
      "optional": false
    },
    {
      "piece": "金",
      "square": "6g",
      "optional": false
    }
  ],
  "typical_build_order": [
    "7g",
    "7h",
    "8h",
    "6g"
  ],
  "characteristics": "飛車を右側(2筋)に置いたまま戦う居飛車で、玉を盤の左側(自分から見て左)へ移し、金2枚と銀1枚を玉の前に縦に並べて固める囲いです。相手の飛車が前に進んでくる筋(相手の飛車先)を金銀で受け止める形になっていて、上から攻められることに強いのが特徴です。組み上がるまでに動かす駒が多く、完成には手数がかかります。",
  "beginner_friendliness": {
    "score": 3,
    "reason": "玉・金・銀の4枚を動かすため手数がかかり、途中で攻められると形が崩れやすいです。ただし形そのものは覚えやすく、居飛車を指す人の基本の囲いとして広く紹介されています(暫定評価。将棋知識としての最終確認は人間のレビューが必要)。"
  },
  "weak_against": "上からの攻めには強い一方、横から(玉の横の段を通って)攻められることや、囲いの端(9筋・8筋の歩の上)を攻められることには弱さが残りやすいです。組み上がる前に速く攻められると、金銀が玉から離れたまま戦うことになります。",
  "source": "【AI起草 / 出典は下記。座標の一次資料確認は行っていない(docs/ROLES.md の保留事項)】先手基準の完成形座標(8八玉・7八金・7七銀・6七金)は、Wikipedia『矢倉囲い』の概要の文『玉を8八に、左金を7八、右金を6七に、左銀を7七に移動させたもの』(https://ja.wikipedia.org/wiki/矢倉囲い、2026-09-25 取得)をそのまま写した。同記事は派生形として銀矢倉(6七の金が銀)・総矢倉(右銀を5七に加える)を挙げるが、本レコードは金矢倉だけを扱う。typical_build_order の並びは出典に無く、本レコードを書いた側が一般的な組み方として置いたもの(推測)。追加の経緯: 2026-09-25 の知識レーン(docs/KNOWLEDGE_LANE_BRIEF_2026-09-25.md)。4 人分の実棋譜で、居飛車のまま玉を 7八・8八へ寄せた局が認識できていなかった(docs/LANE_KNOWLEDGE_LOG_2026-09.md)。",
  "confidence_level": "medium",
  "review_status": "draft"
}
```

### `data/drafts/2026-09-25-knowledge/openings/ibisha_self.json`(最終の置き場は `data/shapes|openings/`。移すのは司令塔)

```json
{
  "id": "ibisha_self",
  "name": "居飛車",
  "name_kana": "いびしゃ",
  "side": "self",
  "family": "居飛車系",
  "leads_to_shape_ids": [
    "yagura_kinyagura",
    "funagakoi"
  ],
  "scenario": null,
  "source": "【AI起草 / 出典は下記】自分側(先手)の戦型としての居飛車。定義は Wikipedia『居飛車』の文『序盤において、初形で右翼にある飛車を定位置(先手は2筋、後手は8筋)のまま据えて戦うこと』(https://ja.wikipedia.org/wiki/居飛車、2026-09-25 取得)による。leads_to_shape_ids は同記事の『矢倉戦や角換わりでは、銀将金将を縦に並べて相手の飛車先をしっかり受け止める矢倉囲い系統の囲いを左翼に構築』『急戦ならば固くはないが短手数で囲える舟囲い系統の囲い』『持久戦ならば手数はかかるが固い穴熊系統の囲いが選択されることが多い』のうち、data/shapes に存在する矢倉・舟囲いだけを書いた(穴熊は data/shapes に無いので書いていない)。id を ibisha_self としたのは、既存の ibisha(side: opponent)と id が衝突するため(openings スキーマの side の設計どおり。2026-09-25 司令塔の確認)。recognition_pattern は書いていない(『飛車を動かさない』という否定の条件は現在のスキーマの表現では書けない。openings.schema.json の recognition_pattern の説明)。戦型を認識するコードは apps/server/src/analysis/ に無いため、このレコードを足しても認識の数は動かない(2026-09-25 司令塔の訂正、KNOWLEDGE_LANE_BRIEF §5.1)。追加の経緯: 2026-09-25 の知識レーン。4 人分の実棋譜 70 局のうち 40 手目時点で自分の飛車が 2 筋にある局が 21 局で最多だった。",
  "confidence_level": "high",
  "review_status": "draft"
}
```

### `data/drafts/2026-09-25-knowledge/openings/mukaibisha.json`(最終の置き場は `data/shapes|openings/`。移すのは司令塔)

```json
{
  "id": "mukaibisha",
  "name": "向かい飛車",
  "name_kana": "むかいびしゃ",
  "side": "self",
  "family": "振り飛車系",
  "leads_to_shape_ids": [
    "mino_honmino",
    "kinmusou"
  ],
  "scenario": null,
  "recognition_pattern": [
    {
      "piece": "飛",
      "to": "8h",
      "order_hint": 1
    }
  ],
  "source": "【AI起草 / 出典は下記】自分側(先手)の戦型としての向かい飛車。定義は Wikipedia『向かい飛車』の文『先手ならば飛車を八筋に、後手ならば飛車を2筋に振る』『相振り飛車になった場合には飛車は向き合わないが、この場合であっても向かい飛車と呼ぶ』(https://ja.wikipedia.org/wiki/向かい飛車、2026-09-25 取得)による。recognition_pattern の 8h(８八飛)はこの『飛車を八筋に』を先手の絶対座標に写したもので、段(八)は初期位置の飛車が同じ段を横に動くことから置いた(推測。出典は筋しか述べていない)。leads_to_shape_ids は、相振り飛車で金無双が使われること(Wikipedia『金無双』)と、振り飛車一般で美濃囲いが使われること(data/shapes/mino_honmino.json の characteristics)から置いたもので、向かい飛車に固有の出典ではない(推測)。戦型を認識するコードは apps/server/src/analysis/ に無いため、このレコードを足しても認識の数は動かない(2026-09-25 司令塔の訂正、KNOWLEDGE_LANE_BRIEF §5.1)。追加の経緯: 2026-09-25 の知識レーン。4 人分の実棋譜 70 局のうち 40 手目時点で自分の飛車が 8 筋にある局が 12 局で、居飛車に次いで多かった(主に 3 人目)。",
  "confidence_level": "medium",
  "review_status": "draft"
}
```

