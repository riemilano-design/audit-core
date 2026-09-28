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

**数**: 囲い N = 62(うち出典なし 10、埋まった 6 → 第 2 組の後 16 → 第 3 組の後 26 → 第 4 組の後 35。**第 4 組で保留 13・対象外 1 を確定したので、いま埋められる残りは 62 − 35 − 13 − 1 = 13 件**)/ 戦法 M = 184(うち出典なし 41、埋まった 7。駒落ちは対象外で数に入れない)。狙い(intents)の目録は戦法の目録から起こす(順は 囲い → 戦法 → 狙い)。

### 2.1 囲いの目録

| # | 名前 | 別名 | 系統 | 個別ページ | 一覧の出典 | 状態 |
|---|---|---|---|---|---|---|
| 1 | 矢倉囲い(金矢倉) | 矢倉 | 矢倉系 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(yagura_kinyagura) |
| 2 | 銀矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E9%8A%80%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(yagura_ginyagura) |
| 3 | 片矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E7%89%87%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(yagura_katayagura) |
| 4 | 総矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E7%B7%8F%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(yagura_souyagura) |
| 5 | 銀立ち矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E9%8A%80%E7%AB%8B%E3%81%A1%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(yagura_gindachi。第 28 組。図から) |
| 6 | 菱矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E8%8F%B1%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(yagura_hishi) |
| 7 | 土居矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E5%9C%9F%E5%B1%85%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(yagura_doi) |
| 8 | 天野矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E5%A4%A9%E9%87%8E%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 保留(記事にあるのは実戦の局面図だけで囲い単体の図が無い。局面図から起こすとその対局に固有の駒まで拾う。第 29 組) |
| 9 | 矢倉早囲い |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E6%97%A9%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 保留(本文に手順の言及のみで囲い単体の図が無い。第 29 組) |
| 10 | 矢倉穴熊 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(yagura_anaguma) |
| 11 | 右矢倉 |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E5%8F%B3%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(migi_yagura。第 28 組。図から) |
| 12 | カニ囲い |  | 矢倉系 | <https://ja.wikipedia.org/wiki/%E3%82%AB%E3%83%8B%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(kanigakoi) |
| 13 | 菊水矢倉 |  | 矢倉系 | <https://shogi-gym.com/kakoi/yagura/kikusui-yagura/> | <https://shogi-gym.com/kakoi/> | 下書き済み(yagura_kikusui) |
| 14 | 富士見矢倉 |  | 矢倉系 | **出典なし** | <https://www.shougi.jp/kakoi/> | 保留(記事に節も図も無く、一覧に名前があるだけ。第 29 組) |
| 15 | へこみ矢倉 |  | 矢倉系 | **出典なし** | <https://www.shougi.jp/kakoi/> | 下書き済み(yagura_hekomi。第 28 組。図から) |
| 16 | 流れ矢倉 |  | 矢倉系 | **出典なし** | <https://www.shougi.jp/kakoi/> | 下書き済み(yagura_nagare。第 28 組。図から) |
| 17 | 流線矢倉 |  | 矢倉系 | **出典なし** | <https://www.shougi.jp/kakoi/> | 下書き済み(yagura_ryusen。第 29 組。図から) |
| 18 | 角矢倉 |  | 矢倉系 | **出典なし** | <https://www.shougi.jp/kakoi/> | 保留(記事にあるのは「四角矢倉」で、同じものか出典から判断できない。第 29 組) |
| 19 | 本美濃囲い | 美濃囲い | 美濃系 | <https://ja.wikipedia.org/wiki/%E6%9C%AC%E7%BE%8E%E6%BF%83%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 既存(mino_honmino) |
| 20 | 高美濃囲い |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E9%AB%98%E7%BE%8E%E6%BF%83%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 既存(mino_takamino) |
| 21 | 銀冠 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E7%BE%8E%E6%BF%83%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 既存(mino_ginkanmuri) |
| 22 | 片美濃囲い |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E7%89%87%E7%BE%8E%E6%BF%83%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(mino_katamino) |
| 23 | 木村美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E6%9C%A8%E6%9D%91%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(mino_kimura。第 28 組。図から。§27 の保留を解消) |
| 24 | ダイヤモンド美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E3%83%80%E3%82%A4%E3%83%A4%E3%83%A2%E3%83%B3%E3%83%89%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(mino_diamond) |
| 25 | 金美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E9%87%91%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(mino_kinmino) |
| 26 | 銀美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E9%8A%80%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(mino_ginmino。第 28 組。図から) |
| 27 | ちょんまげ美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E3%81%A1%E3%82%87%E3%82%93%E3%81%BE%E3%81%92%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(mino_chonmage。第 28 組。図から。歩を入れた数少ない形) |
| 28 | 坊主美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E5%9D%8A%E4%B8%BB%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 保留(定義が「玉頭に歩が無い」という否定で、片美濃と駒の位置が同じ。第 28 組) |
| 29 | 四枚美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E5%9B%9B%E6%9E%9A%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 保留(図が無い。将棋ジムは「銀をもう 1 枚上げた形」とだけで座標が読めない。第 29 組) |
| 30 | 天守閣美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E5%A4%A9%E5%AE%88%E9%96%A3%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(tenshukaku_mino 自分、low。第 26 組。§5.1 の保留を解消) |
| 31 | 左美濃 |  | 美濃系 | <https://ja.wikipedia.org/wiki/%E5%B7%A6%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(hidarimino 自分。第 26 組。§5.1 の保留を解消) |
| 32 | 居飛車銀冠 |  | 美濃系(居飛車) | <https://shogi-gym.com/kakoi/mino/hidarimino/> | <https://shogi-gym.com/kakoi/> | 下書き済み(ibisha_ginkanmuri 自分。第 26 組) |
| 33 | 振り飛車早囲い | 早囲い | 美濃系 | <https://shogi-gym.com/kakoi/furibisha-hayagakoi/> | <https://shogi-gym.com/kakoi/> | 下書き済み(mino_hayagakoi) |
| 34 | 三手囲い |  | その他(振り飛車) | <https://www.shogi.or.jp/column/2019/04/kakoi_65.html> | <https://www.shougi.jp/kakoi/> | 保留(出典(shougi.jp)に座標の文も図も無い。第 29 組) |
| 35 | 穴熊囲い |  | 穴熊系 | <https://ja.wikipedia.org/wiki/%E7%A9%B4%E7%86%8A%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 既存と同じ(総称。基本形は anaguma_furibisha = 玉1九・香1八・銀2八・金3八・金3九 で、Wikipedia の「穴熊の基本形」の図と一致することを第 29 組で確認) |
| 36 | 居飛車穴熊 |  | 穴熊系 | <https://ja.wikipedia.org/wiki/%E5%B1%85%E9%A3%9B%E8%BB%8A%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(anaguma_ibisha) |
| 37 | 振り飛車穴熊 |  | 穴熊系 | <https://ja.wikipedia.org/wiki/%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(anaguma_furibisha) |
| 38 | 松尾流穴熊 |  | 穴熊系 | <https://ja.wikipedia.org/wiki/%E6%9D%BE%E5%B0%BE%E6%B5%81%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(anaguma_matsuo) |
| 39 | 一直線穴熊 |  | 穴熊系 | <https://ja.wikipedia.org/wiki/%E4%B8%80%E7%9B%B4%E7%B7%9A%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 保留(穴熊囲いの記事に該当の節が無い。第 29 組) |
| 40 | ビッグ4 |  | 穴熊系 | <https://ja.wikipedia.org/wiki/%E3%83%93%E3%83%83%E3%82%B04%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(anaguma_big4) |
| 41 | 銀冠穴熊 |  | 穴熊系 | <https://shogi-gym.com/kakoi/anaguma/ginkan-anaguma/> | <https://shogi-gym.com/kakoi/> | 下書き済み(anaguma_ginkanmuri) |
| 42 | 舟囲い |  | 舟囲い系 | <https://ja.wikipedia.org/wiki/%E8%88%9F%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(funagakoi) |
| 43 | 箱入り娘 |  | 舟囲い系 | <https://ja.wikipedia.org/wiki/%E7%AE%B1%E5%85%A5%E3%82%8A%E5%A8%98%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(hakoirimusume) |
| 44 | Elmo囲い | エルモ囲い | 舟囲い系 | <https://ja.wikipedia.org/wiki/Elmo%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(elmogakoi) |
| 45 | 串カツ囲い |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E4%B8%B2%E3%82%AB%E3%83%84%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 保留(出典が食い違い、ミレニアムの記事も「銀と桂で9筋を守る」とだけで座標が無い。第 29 組) |
| 46 | ミレニアム囲い | トーチカ | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E3%83%9F%E3%83%AC%E3%83%8B%E3%82%A2%E3%83%A0%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(millennium。第 29 組。2 つの図が一致した 4 枚だけ) |
| 47 | 振り飛車ミレニアム |  | その他(振り飛車) | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(記事は言及のみで図が無い。左右を反転させる推測になり、180 度回転とは別の操作で取り違えの元(P-12)。第 29 組) |
| 48 | 金無双 | 二枚金 | 相振り | <https://ja.wikipedia.org/wiki/%E9%87%91%E7%84%A1%E5%8F%8C> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(kinmusou) |
| 49 | 雁木囲い |  | その他 | <https://ja.wikipedia.org/wiki/%E9%9B%81%E6%9C%A8%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(gangi_nimaigin) |
| 50 | ツノ銀雁木 |  | 雁木系 | <https://ja.wikipedia.org/wiki/%E9%9B%81%E6%9C%A8%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category:%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(gangi_tsunogin) |
| 51 | 中住まい |  | その他 | <https://ja.wikipedia.org/wiki/%E4%B8%AD%E4%BD%8F%E3%81%BE%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(nakazumai) |
| 52 | 中原囲い |  | その他 | <https://ja.wikipedia.org/wiki/%E4%B8%AD%E5%8E%9F%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(nakaharagakoi) |
| 53 | ボナンザ囲い |  | その他 | <https://ja.wikipedia.org/wiki/%E3%83%9C%E3%83%8A%E3%83%B3%E3%82%B6%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(bonanzagakoi) |
| 54 | 金開き |  | その他 | <https://ja.wikipedia.org/wiki/%E9%87%91%E9%96%8B%E3%81%8D> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(kinbiraki) |
| 55 | 壁囲い |  | その他 | <https://ja.wikipedia.org/wiki/%E5%A3%81%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(kabegakoi) |
| 56 | いちご囲い | イチゴ囲い | その他 | <https://ja.wikipedia.org/wiki/%E3%81%84%E3%81%A1%E3%81%94%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(ichigogakoi) |
| 57 | アヒル囲い | 大阪囲い | その他 | <https://ja.wikipedia.org/wiki/%E3%82%A2%E3%83%92%E3%83%AB%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(ahirugakoi) |
| 58 | 無敵囲い |  | その他 | <https://ja.wikipedia.org/wiki/%E7%84%A1%E6%95%B5%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 下書き済み(mutekigakoi) |
| 59 | 多伝囲い |  | その他 | <https://ja.wikipedia.org/wiki/%E5%A4%9A%E4%BC%9D%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B0%86%E6%A3%8B%E3%81%AE%E5%9B%B2%E3%81%84> | 対象外(駒落ち専用) |
| 60 | 中段玉 |  | その他(居飛車) | **出典なし** | <https://www.shougi.jp/kakoi/> | 保留(同上。加えて「玉が中段にいる」状態の総称で形が定まらない。第 29 組) |
| 61 | 最強囲い |  | その他(居飛車) | **出典なし** | <https://www.shougi.jp/kakoi/> | 保留(出典に座標の文も図も無い。第 29 組) |
| 62 | トラック囲い |  | その他(居飛車) | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(出典が一覧のみで図も説明も無い。第 29 組) |
| 63 | カタ囲い |  | その他(居飛車) | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(同上。第 29 組) |
| 64 | 金象眼・銀象眼 |  | 駒落ち(対象外) | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 対象外(駒落ち) |

### 2.2 戦法の目録

| # | 名前 | 別名 | 分類 | 個別ページ | 一覧の出典 | 状態 |
|---|---|---|---|---|---|---|
| 1 | 居飛車 |  | 居飛車(総称) | <https://ja.wikipedia.org/wiki/%E5%B1%85%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(ibisha_self、自分側)。相手側は既存 ibisha |
| 2 | 相居飛車 |  | 居飛車(総称) | <https://ja.wikipedia.org/wiki/%E7%9B%B8%E5%B1%85%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 保留(対局の組み合わせの名前で side に当てはまらない。§7) |
| 3 | 対抗型 |  | 居飛車(総称) | <https://ja.wikipedia.org/wiki/%E5%AF%BE%E6%8A%97%E5%9E%8B> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 保留(対局の組み合わせの名前で side に当てはまらない。§7) |
| 4 | 矢倉 |  | 相居飛車 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(yagura_senpo 自分) |
| 5 | 角換わり |  | 相居飛車 | <https://ja.wikipedia.org/wiki/%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(kakugawari 自分) |
| 6 | 相掛かり |  | 相居飛車 | <https://ja.wikipedia.org/wiki/%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(aigakari 自分) |
| 7 | 横歩取り |  | 相居飛車 | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(yokofudori 自分) |
| 8 | 雁木戦法 | 雁木 | 相居飛車 | <https://ja.wikipedia.org/wiki/%E9%9B%81%E6%9C%A8%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(gangi_senpou 自分。第 17 組) |
| 9 | 矢倉棒銀 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E6%A3%92%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(yagura_bogin 自分) |
| 10 | 雀刺し |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E9%9B%80%E5%88%BA%E3%81%97> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(suzumesashi 自分) |
| 11 | 森下システム |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E6%A3%AE%E4%B8%8B%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(morishita_system 自分。recognition_pattern 無し) |
| 12 | 脇システム |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E8%84%87%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(wakisystem 自分) |
| 13 | 矢倉3七桂 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%893%E4%B8%83%E6%A1%82> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(yagura_37kei 自分。第 19 組) |
| 14 | 矢倉3七銀 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%893%E4%B8%83%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(yagura_37gin 自分) |
| 15 | 四手角 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E5%9B%9B%E6%89%8B%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(yontekaku 自分。第 19 組。目録に 2 行あるが同じもの) |
| 16 | 米長流急戦矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%B1%B3%E9%95%B7%E6%B5%81%E6%80%A5%E6%88%A6%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(yonenaga_kyusen_yagura 相手) |
| 17 | 阿久津流急戦矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E9%98%BF%E4%B9%85%E6%B4%A5%E6%B5%81%E6%80%A5%E6%88%A6%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(akutsu_kyusen_yagura 相手側。第 19 組) |
| 18 | 中原流急戦矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E4%B8%AD%E5%8E%9F%E6%B5%81%E6%80%A5%E6%88%A6%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 保留(出典 URL が矢倉囲いの一般説明に転送され、固有の駒組みが読めない。第 19 組) |
| 19 | 矢倉中飛車 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(yagura_nakabisha 自分。第 17 組) |
| 20 | 6二飛戦法 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/6%E4%BA%8C%E9%A3%9B%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 保留(出典 URL が戦法の一般説明に転送され、固有の駒組みが読めない。第 19 組) |
| 21 | カニカニ銀 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E3%82%AB%E3%83%8B%E3%82%AB%E3%83%8B%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(kanikanigin 自分) |
| 22 | 矢倉3五歩早仕掛け |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%893%E4%BA%94%E6%AD%A9%E6%97%A9%E4%BB%95%E6%8E%9B%E3%81%91> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(yagura_35fu_hayajikake 自分。第 19 組) |
| 23 | 無理矢理矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E7%84%A1%E7%90%86%E7%9F%A2%E7%90%86%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(muriyari_yagura 自分。第 19 組) |
| 24 | ウソ矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E3%82%A6%E3%82%BD%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(muriyari_yagura の別名。第 19 組。同じ記事) |
| 25 | 同型矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E5%90%8C%E5%9E%8B%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(douke_yagura 自分) |
| 26 | 飛車先不突矢倉 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E9%A3%9B%E8%BB%8A%E5%85%88%E4%B8%8D%E7%AA%81%E7%9F%A2%E5%80%89> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 保留(定義が「2六歩を突かない」という否定で、スキーマで表せない。第 19 組) |
| 27 | 金立ち戦法 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E9%87%91%E7%AB%8B%E3%81%A1%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(kintachi 自分。第 17 組) |
| 28 | 忍者銀 |  | 矢倉の指し方 | <https://ja.wikipedia.org/wiki/%E5%BF%8D%E8%80%85%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9F%A2%E5%80%89> | 下書き済み(ninja_gin 自分。第 17 組) |
| 29 | 加藤流(矢倉) |  | 矢倉の指し方 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 30 | 三手角 |  | 矢倉の指し方 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 31 | 右四間飛車(矢倉・腰掛け銀型) |  | 矢倉の指し方 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 32 | 角換わり腰掛け銀 |  | 角換わり | <https://ja.wikipedia.org/wiki/%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A%E8%85%B0%E6%8E%9B%E3%81%91%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | 下書き済み(kakugawari_koshikakegin 自分) |
| 33 | 角換わり棒銀 |  | 角換わり | <https://ja.wikipedia.org/wiki/%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A%E6%A3%92%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | 下書き済み(kakugawari_bogin 自分) |
| 34 | 筋違い角 |  | 角換わり | <https://ja.wikipedia.org/wiki/%E7%AD%8B%E9%81%95%E3%81%84%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | 下書き済み(sujichigai_kaku 自分) |
| 35 | 後手番一手損角換わり |  | 角換わり | <https://ja.wikipedia.org/wiki/%E5%BE%8C%E6%89%8B%E7%95%AA%E4%B8%80%E6%89%8B%E6%90%8D%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | 下書き済み(ittezon_kakugawari 相手) |
| 36 | 木村定跡 |  | 角換わり | <https://ja.wikipedia.org/wiki/%E6%9C%A8%E6%9D%91%E5%AE%9A%E8%B7%A1> | <https://ja.wikipedia.org/wiki/Category%3A%E8%A7%92%E6%8F%9B%E3%82%8F%E3%82%8A> | 保留(手順(定跡)の名前で、駒の配置として書けない。第 25 組) |
| 37 | 早繰り銀 |  | 角換わり・相掛かり | <https://ja.wikipedia.org/wiki/%E6%97%A9%E7%B9%B0%E3%82%8A%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(hayakurigin 自分。第 17 組) |
| 38 | 相掛かり棒銀 |  | 相掛かり | <https://ja.wikipedia.org/wiki/%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A%E6%A3%92%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 下書き済み(aigakari_bogin 自分。第 17 組) |
| 39 | 塚田スペシャル |  | 相掛かり | <https://ja.wikipedia.org/wiki/%E5%A1%9A%E7%94%B0%E3%82%B9%E3%83%9A%E3%82%B7%E3%83%A3%E3%83%AB> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 下書き済み(tsukada_special 自分) |
| 40 | 相掛かり腰掛け銀 |  | 相掛かり | <https://ja.wikipedia.org/wiki/%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A%E8%85%B0%E6%8E%9B%E3%81%91%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 下書き済み(aigakari_koshikakegin 自分。第 17 組) |
| 41 | 鎖鎌銀 |  | 相掛かり | <https://ja.wikipedia.org/wiki/%E9%8E%96%E9%8E%8C%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 下書き済み(kusarigamagin 自分) |
| 42 | ひねり飛車 |  | 相掛かり | <https://ja.wikipedia.org/wiki/%E3%81%B2%E3%81%AD%E3%82%8A%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 下書き済み(hineribisha 自分) |
| 43 | 縦歩取り |  | 相掛かり | <https://ja.wikipedia.org/wiki/%E7%B8%A6%E6%AD%A9%E5%8F%96%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 下書き済み(tatefudori 自分。第 17 組) |
| 44 | UFO銀 |  | 相掛かり | <https://ja.wikipedia.org/wiki/UFO%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E7%9B%B8%E6%8E%9B%E3%81%8B%E3%82%8A> | 下書き済み(ufo_gin 自分。第 17 組) |
| 45 | 中原流相掛かり |  | 相掛かり | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 46 | 新旧対抗型 |  | 相掛かり | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 47 | 飛車先交換早繰り銀 |  | 相掛かり | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 48 | 飛車先交換腰掛け銀 |  | 相掛かり | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 49 | 横歩取り3三角 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A3%E4%B8%89%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 下書き済み(yokofudori_33kaku 相手側。第 20 組) |
| 50 | 横歩取り3三桂 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A3%E4%B8%89%E6%A1%82> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 下書き済み(yokofudori_33kei 相手側。第 20 組) |
| 51 | 横歩取り2三歩 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A2%E4%B8%89%E6%AD%A9> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 下書き済み(yokofudori_23fu 相手側。第 20 組) |
| 52 | 横歩取り4五角 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A4%E4%BA%94%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 下書き済み(yokofudori_45kaku 相手側。第 20 組) |
| 53 | 横歩取り4四角 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A4%E5%9B%9B%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 下書き済み(yokofudori_44kaku 相手側。第 20 組) |
| 54 | 横歩取り8五飛 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A8%E4%BA%94%E9%A3%9B> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 下書き済み(yokofudori_85hi 相手) |
| 55 | 相横歩取り |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E7%9B%B8%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 下書き済み(ai_yokofudori 相手側。第 20 組) |
| 56 | ノーガード戦法 |  | 横歩取り | <https://ja.wikipedia.org/wiki/%E3%83%8E%E3%83%BC%E3%82%AC%E3%83%BC%E3%83%89%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A> | 保留(定義の核が「左金(3二金)を上がらない」という否定で、残る特徴の 3三角 は横歩取り3三角と同じマスになる。第 20 組) |
| 57 | 空中戦法(内藤流) |  | 横歩取り | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 下書き済み(yokofudori_33kaku の別名。第 20 組。出典が同じものと述べている) |
| 58 | 中座飛車 |  | 横歩取り | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 59 | 3三飛成戦法 |  | 横歩取り | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 60 | 棒銀 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E6%A3%92%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(boh_gin_self 自分。相手側は intent boh_gin) |
| 61 | 腰掛け銀 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E8%85%B0%E6%8E%9B%E3%81%91%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(koshikakegin 自分) |
| 62 | 右四間飛車 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E5%8F%B3%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(migi_shikenbisha 自分 / migi_shikenbisha_opponent 相手) |
| 63 | 袖飛車 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E8%A2%96%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(sodebisha 自分。第 18 組) |
| 64 | 一間飛車 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E4%B8%80%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(ikken_bisha 自分。第 20 組) |
| 65 | 一間飛車穴熊 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E4%B8%80%E9%96%93%E9%A3%9B%E8%BB%8A%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(ikken_bisha_anaguma 自分。第 22 組) |
| 66 | 引き角 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E5%BC%95%E3%81%8D%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(hikikaku 自分。第 18 組) |
| 67 | 右玉 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E5%8F%B3%E7%8E%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(migigyoku 自分。第 18 組) |
| 68 | 嬉野流 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E5%AC%89%E9%87%8E%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(ureshino 自分。第 20 組) |
| 69 | 村田システム |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E6%9D%91%E7%94%B0%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 保留(2 度の読みが一致したのは 5六歩 の 1 手だけで普通の手と区別にならず、定義の核「角道を開けず」は否定で書けない。第 25 組) |
| 70 | 二枚銀 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E4%BA%8C%E6%9E%9A%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(nimaigin 自分。第 18 組) |
| 71 | 3八飛戦法 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/3%E5%85%AB%E9%A3%9B%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(sanhachi_bisha 自分。第 22 組) |
| 72 | 4七銀型 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/4%E4%B8%83%E9%8A%80%E5%9E%8B> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 保留(出典 URL がゴキゲン中飛車の記事に転送され、この型固有の駒組みが読めない。第 22 組) |
| 73 | 3三角戦法 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/3%E4%B8%89%E8%A7%92%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(sansan_kaku_senpo 相手側、low。第 22 組。横歩取り3三角と機械では区別できない) |
| 74 | 原始棒銀 |  | 居飛車一般 | <https://ja.wikipedia.org/wiki/%E5%8E%9F%E5%A7%8B%E6%A3%92%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%B1%85%E9%A3%9B%E8%BB%8A> | 下書き済み(genshi_bogin 自分。第 18 組) |
| 75 | 4六銀左戦法 | 斜め棒銀 | 対振り急戦 | <https://ja.wikipedia.org/wiki/4%E5%85%AD%E9%8A%80%E5%B7%A6%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(naname_bogin_self 自分) |
| 76 | 4五歩早仕掛け |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/4%E4%BA%94%E6%AD%A9%E6%97%A9%E4%BB%95%E6%8E%9B%E3%81%91> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 既存 intent hayajikake(相手側) |
| 77 | 対振り棒銀 | 棒銀 | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E6%A3%92%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 既存 intent boh_gin(相手側) |
| 78 | 鷺宮定跡 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E9%B7%BA%E5%AE%AE%E5%AE%9A%E8%B7%A1> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(sagimiya_joseki 自分) |
| 79 | 山田定跡 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E5%B1%B1%E7%94%B0%E5%AE%9A%E8%B7%A1> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(yamada_joseki 自分) |
| 80 | 4六銀右戦法 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/4%E5%85%AD%E9%8A%80%E5%8F%B3%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(shirokugin_migi 自分。第 18 組) |
| 81 | 鳥刺し (将棋) |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E9%B3%A5%E5%88%BA%E3%81%97%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(torisashi 自分) |
| 82 | ポンポン桂 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E3%83%9D%E3%83%B3%E3%83%9D%E3%83%B3%E6%A1%82> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(ponpon_kei 自分。第 18 組) |
| 83 | 4六金戦法 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/4%E5%85%AD%E9%87%91%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(shiroku_kin 自分。第 18 組) |
| 84 | 加藤流袖飛車 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E5%8A%A0%E8%97%A4%E6%B5%81%E8%A2%96%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(kato_sodebisha 自分。第 22 組。個別ページは袖飛車の記事に転送) |
| 85 | 三歩突き捨て急戦 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E4%B8%89%E6%AD%A9%E7%AA%81%E3%81%8D%E6%8D%A8%E3%81%A6%E6%80%A5%E6%88%A6> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(sanpo_tsukisute 相手側。第 22 組) |
| 86 | 三間飛車破り |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A%E7%A0%B4%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 保留(出典が複数の指し方の総称で、固有の配置が無い。第 22 組) |
| 87 | 棒金 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E6%A3%92%E9%87%91> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(boukin 自分) |
| 88 | 超速3七銀 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E8%B6%85%E9%80%9F3%E4%B8%83%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(chousoku_37gin 自分) |
| 89 | 丸山ワクチン (将棋) |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E4%B8%B8%E5%B1%B1%E3%83%AF%E3%82%AF%E3%83%81%E3%83%B3%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 保留(出典が曖昧さ回避ページで、固有の定義も座標も無い。第 22 組) |
| 90 | 横歩取り (対中飛車) |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E6%A8%AA%E6%AD%A9%E5%8F%96%E3%82%8A%20%28%E5%AF%BE%E4%B8%AD%E9%A3%9B%E8%BB%8A%29> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 保留(自分側の指し手は普通の横歩取りと同じで、違いは「相手が中飛車であること」。相手の形を条件に書けない。第 25 組) |
| 91 | へなちょこ急戦 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E3%81%B8%E3%81%AA%E3%81%A1%E3%82%87%E3%81%93%E6%80%A5%E6%88%A6> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(henachoko_kyusen 自分。第 22 組) |
| 92 | 居飛車舟囲い急戦 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E5%B1%85%E9%A3%9B%E8%BB%8A%E8%88%9F%E5%9B%B2%E3%81%84%E6%80%A5%E6%88%A6> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 保留(総称。下位の 4六銀右戦法・4六金戦法・二枚銀・三歩突き捨て急戦は下書き済み。第 22 組) |
| 93 | 地下鉄飛車 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E5%9C%B0%E4%B8%8B%E9%89%84%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(狙い chikatetsu_bisha 相手側。第 14 組) |
| 94 | 四手角 |  | 対振り急戦 | <https://ja.wikipedia.org/wiki/%E5%9B%9B%E6%89%8B%E8%A7%92> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(yontekaku 自分。第 19 組。目録に 2 行あるが同じもの) |
| 95 | 5八金右超急戦 |  | 対振り急戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 96 | 英春流右四間 |  | 対振り急戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 97 | 5七金戦法(対玉頭銀) |  | 対振り急戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 98 | 二枚銀3八飛型 |  | 対振り急戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 99 | きmきm金 |  | 対振り急戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 100 | 居飛車穴熊(戦法) |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E5%B1%85%E9%A3%9B%E8%BB%8A%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(ibisha_anaguma_senpo 自分。第 21 組) |
| 101 | 左美濃(戦法) |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E5%B7%A6%E7%BE%8E%E6%BF%83> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(hidarimino_senpo 自分。第 21 組) |
| 102 | 玉頭位取り |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E7%8E%89%E9%A0%AD%E4%BD%8D%E5%8F%96%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(狙い gyokuto_kuraidori 相手側。第 14 組) |
| 103 | 5筋位取り |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/5%E7%AD%8B%E4%BD%8D%E5%8F%96%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(狙い gosuji_kuraidori_opponent 相手側。第 14 組) |
| 104 | 6筋位取り |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/6%E7%AD%8B%E4%BD%8D%E5%8F%96%E3%82%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(rokusuji_kuraidori 相手側、low。第 21 組。1 手では区別にならないことを source に明記) |
| 105 | 飯島流引き角戦法 |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E9%A3%AF%E5%B3%B6%E6%B5%81%E5%BC%95%E3%81%8D%E8%A7%92%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(iijima_hikikaku 自分。第 21 組) |
| 106 | 都成流 |  | 対振り持久戦 | <https://ja.wikipedia.org/wiki/%E9%83%BD%E6%88%90%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E5%AF%BE%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(tonari_ryu 相手側。第 21 組) |
| 107 | 位取り戦法 |  | 対振り持久戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 108 | 糸谷流右玉 |  | 対振り持久戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 109 | ホラ囲い |  | 対振り持久戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 110 | 端美濃・串カツ戦法 |  | 対振り持久戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 111 | トーチカ戦法 |  | 対振り持久戦 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 112 | 振り飛車 |  | 振り飛車(総称) | <https://ja.wikipedia.org/wiki/%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 保留(総称。飛車を左翼へ振る、とだけで到達マスが定まらない。下位の戦法は個別に下書き済み。第 23 組) |
| 113 | 相振り飛車 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E7%9B%B8%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 保留(対局の組み合わせの名前で side に当てはまらない。§7) |
| 114 | 角交換振り飛車 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E8%A7%92%E4%BA%A4%E6%8F%9B%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 保留(定義の核が角交換 = 盤上から駒が消えることで、recognition_pattern は「この駒がここに来た」しか書けない。第 21 組) |
| 115 | 角交換相振り飛車 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E8%A7%92%E4%BA%A4%E6%8F%9B%E7%9B%B8%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 保留(角交換 = 盤上から駒が消えることが定義の核。飛車の筋も 3 通り挙げられ定まらない。第 23 組) |
| 116 | 陽動振り飛車 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E9%99%BD%E5%8B%95%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 保留(定義が「いつ飛車を振るか」というタイミングで、スキーマは手順の前後を表せない。第 21 組) |
| 117 | 玉頭銀 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E7%8E%89%E9%A0%AD%E9%8A%80> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(gyokutogin_senpo 自分。第 21 組。相手側の狙いは intents の gyokutogin) |
| 118 | 左玉 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E5%B7%A6%E7%8E%89> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(hidarigyoku 自分、low。第 21 組) |
| 119 | 高田流左玉 |  | 振り飛車一般 | <https://ja.wikipedia.org/wiki/%E9%AB%98%E7%94%B0%E6%B5%81%E5%B7%A6%E7%8E%89> | <https://ja.wikipedia.org/wiki/Category%3A%E6%8C%AF%E3%82%8A%E9%A3%9B%E8%BB%8A> | 下書き済み(takada_ryu_hidarigyoku 自分。第 23 組。個別ページは左玉の記事に転送) |
| 120 | 中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 既存 nakabisha(相手)+ 下書き済み nakabisha_self(自分)、intent nakabisha_kuraidori |
| 121 | ゴキゲン中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E3%82%B4%E3%82%AD%E3%82%B2%E3%83%B3%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 下書き済み(gokigen_nakabisha 相手) |
| 122 | ツノ銀中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E3%83%84%E3%83%8E%E9%8A%80%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 下書き済み(tsunogin_nakabisha 自分) |
| 123 | 原始中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E5%8E%9F%E5%A7%8B%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 下書き済み(genshi_nakabisha 自分) |
| 124 | 先手中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E5%85%88%E6%89%8B%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 下書き済み(sente_nakabisha 自分) |
| 125 | 風車 (将棋) |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E9%A2%A8%E8%BB%8A%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 下書き済み(fuusha 自分) |
| 126 | 5筋位取り中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/5%E7%AD%8B%E4%BD%8D%E5%8F%96%E3%82%8A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 下書き済み(gosuji_kuraidori_nakabisha 自分) |
| 127 | 英ちゃん流中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E8%8B%B1%E3%81%A1%E3%82%83%E3%82%93%E6%B5%81%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 下書き済み(eichanryu_nakabisha 自分、low。第 23 組。骨格の「5筋を突かない」は書けない) |
| 128 | 平目 (将棋) |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E5%B9%B3%E7%9B%AE%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 下書き済み(hirame 自分。第 23 組) |
| 129 | 矢倉流中飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E7%9F%A2%E5%80%89%E6%B5%81%E4%B8%AD%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 下書き済み(yagura_ryu_nakabisha 相手側、low。第 23 組) |
| 130 | 中飛車左穴熊 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E4%B8%AD%E9%A3%9B%E8%BB%8A%E5%B7%A6%E7%A9%B4%E7%86%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 下書き済み(nakabisha_hidari_anaguma 自分) |
| 131 | 鬼六流ドッカン飛車 |  | 中飛車 | <https://ja.wikipedia.org/wiki/%E9%AC%BC%E5%85%AD%E6%B5%81%E3%83%89%E3%83%83%E3%82%AB%E3%83%B3%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%AD%E9%A3%9B%E8%BB%8A> | 下書き済み(onirokuryu_dokkan 自分。第 23 組) |
| 132 | 5五龍中飛車 |  | 中飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 133 | 中飛車早繰り銀 |  | 中飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 134 | 角交換型中飛車 |  | 中飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 135 | 四間飛車 |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 既存 shikenbisha(自分)+ 下書き済み shikenbisha_opponent(相手) |
| 136 | 藤井システム |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E8%97%A4%E4%BA%95%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 下書き済み(fujii_system 自分。recognition_pattern 無し) |
| 137 | 角交換四間飛車 |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E8%A7%92%E4%BA%A4%E6%8F%9B%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 保留(出典の読みが先手の飛車を 8筋 と述べ、四間飛車の定義 6筋 と食い違う。§11) |
| 138 | 立石流四間飛車 |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E7%AB%8B%E7%9F%B3%E6%B5%81%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 下書き済み(tateishiryu 自分) |
| 139 | レグスペ |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E3%83%AC%E3%82%B0%E3%82%B9%E3%83%9A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 下書き済み(regusupe 自分) |
| 140 | 耀龍四間飛車 |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E8%80%80%E9%BE%8D%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 下書き済み(youryuu_shikenbisha 自分) |
| 141 | 室岡システム |  | 四間飛車 | <https://ja.wikipedia.org/wiki/%E5%AE%A4%E5%B2%A1%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0> | <https://ja.wikipedia.org/wiki/Category%3A%E5%9B%9B%E9%96%93%E9%A3%9B%E8%BB%8A> | 保留(出典の要点が △6二金 の 1 手だけで囲いの普通の手と区別にならず、先後の記述も混ざる。第 23 組) |
| 142 | 錆刀戦法(宗歩四間飛車) |  | 四間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 143 | 4五歩ポン |  | 四間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 144 | 筋違い角四間飛車 |  | 四間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 145 | 三間飛車 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 下書き済み(sankenbisha 自分 / sankenbisha_opponent 相手) |
| 146 | 石田流 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E7%9F%B3%E7%94%B0%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 下書き済み(ishidaryu 自分) |
| 147 | 早石田 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E6%97%A9%E7%9F%B3%E7%94%B0> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 下書き済み(hayaishida 自分) |
| 148 | 升田式石田流 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E5%8D%87%E7%94%B0%E5%BC%8F%E7%9F%B3%E7%94%B0%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 下書き済み(masuda_ishida 自分) |
| 149 | 新石田流 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E6%96%B0%E7%9F%B3%E7%94%B0%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 保留(出典 URL が石田流の記事に転送され、固有の駒組みが読めない。本体は既存の ishidaryu。第 24 組) |
| 150 | 楠本式石田流 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E6%A5%A0%E6%9C%AC%E5%BC%8F%E7%9F%B3%E7%94%B0%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 保留(同上。出典が石田流の記事に転送される。第 24 組) |
| 151 | 鬼殺し (将棋) |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E9%AC%BC%E6%AE%BA%E3%81%97%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 下書き済み(onikoroshi 自分) |
| 152 | 新鬼殺し |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E6%96%B0%E9%AC%BC%E6%AE%BA%E3%81%97> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 保留(出典 URL が鬼殺しの記事に転送され、固有の駒組みが読めない。本体は既存の onikoroshi。第 24 組) |
| 153 | 真部流 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E7%9C%9F%E9%83%A8%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 保留(出典に定義が無い。§12) |
| 154 | 中田功XP |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E4%B8%AD%E7%94%B0%E5%8A%9FXP> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 下書き済み(nakata_xp 自分) |
| 155 | トマホーク (将棋) |  | 三間飛車 | <https://ja.wikipedia.org/wiki/%E3%83%88%E3%83%9E%E3%83%9B%E3%83%BC%E3%82%AF%20%28%E5%B0%86%E6%A3%8B%29> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 保留(端が 9筋 か 1筋 か読めない。§12) |
| 156 | 2手目△3二飛 |  | 三間飛車 | <https://ja.wikipedia.org/wiki/2%E6%89%8B%E7%9B%AE%E2%96%B33%E4%BA%8C%E9%A3%9B> | <https://ja.wikipedia.org/wiki/Category%3A%E4%B8%89%E9%96%93%E9%A3%9B%E8%BB%8A> | 下書き済み(nitemme_32hi 相手側、low。第 24 組。「2 手目」は書けない) |
| 157 | 大野流三間飛車 |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 158 | 下町流三間飛車 |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 159 | カナケンシステム |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 160 | 久保システム |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 161 | 菅井流 |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 162 | 阪田流三間飛車 |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 163 | 初手▲7八飛(猫だまし) |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 164 | 三間飛車藤井システム |  | 三間飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 165 | 向かい飛車 |  | 向かい飛車 | <https://ja.wikipedia.org/wiki/%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | 下書き済み(mukaibisha 自分 / mukaibisha_opponent 相手) |
| 166 | ダイレクト向かい飛車 |  | 向かい飛車 | <https://ja.wikipedia.org/wiki/%E3%83%80%E3%82%A4%E3%83%AC%E3%82%AF%E3%83%88%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | 下書き済み(direct_mukaibisha 相手) |
| 167 | メリケン向かい飛車 |  | 向かい飛車 | <https://ja.wikipedia.org/wiki/%E3%83%A1%E3%83%AA%E3%82%B1%E3%83%B3%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | 下書き済み(meriken_mukaibisha 自分) |
| 168 | 阪田流向かい飛車 |  | 向かい飛車 | <https://ja.wikipedia.org/wiki/%E9%98%AA%E7%94%B0%E6%B5%81%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | 下書き済み(sakataryu_mukaibisha 相手) |
| 169 | 鬼殺し向かい飛車 |  | 向かい飛車 | <https://ja.wikipedia.org/wiki/%E9%AC%BC%E6%AE%BA%E3%81%97%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | <https://ja.wikipedia.org/wiki/Category%3A%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | 保留(出典 URL が向かい飛車の記事に転送され、固有の駒組みが読めない。第 24 組) |
| 170 | 金沢流 |  | 向かい飛車 | <https://ja.wikipedia.org/wiki/%E9%87%91%E6%B2%A2%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E5%90%91%E3%81%8B%E3%81%84%E9%A3%9B%E8%BB%8A> | 下書き済み(kanazawaryu 自分。第 24 組) |
| 171 | 升田流向かい飛車 |  | 向かい飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 172 | 大野流向かい飛車 |  | 向かい飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 173 | 二手損向かい飛車 |  | 向かい飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 174 | 4手目△3三角戦法 |  | 向かい飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 175 | 筋違い角向かい飛車 |  | 向かい飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 176 | 里見流流れ金無双 |  | 向かい飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 177 | △3三桂戦法(相振り) |  | 相振り飛車 | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 保留(個別ページが無く、一覧(カテゴリ)に名前があるだけ。駒の配置を起こせない。第 25 組でまとめて) |
| 178 | 4四歩パックマン |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/4%E5%9B%9B%E6%AD%A9%E3%83%91%E3%83%83%E3%82%AF%E3%83%9E%E3%83%B3> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 下書き済み(yonyonfu_pacman 相手側、low。第 24 組。1 手では区別にならない) |
| 179 | 角頭歩戦法 |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/%E8%A7%92%E9%A0%AD%E6%AD%A9%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 下書き済み(kakutoufu 自分。第 24 組。後手側は未作成) |
| 180 | カメレオン戦法 |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/%E3%82%AB%E3%83%A1%E3%83%AC%E3%82%AA%E3%83%B3%E6%88%A6%E6%B3%95> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 下書き済み(kamereon_senpo 自分。第 25 組。2 度の読みが一致した 2 件) |
| 181 | 新米長玉 |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/%E6%96%B0%E7%B1%B3%E9%95%B7%E7%8E%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 保留(同じページに米長玉と新米長玉があり読み方で違う座標が出る。本体は「2 手目に指すこと」で書けない。第 25 組) |
| 182 | 珍玉 |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/%E7%8F%8D%E7%8E%89> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 保留(珍しい玉の位置の総称で、座標が定まらない。第 25 組) |
| 183 | 英春流 |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/%E8%8B%B1%E6%98%A5%E6%B5%81> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 下書き済み(eishunryu 自分。第 25 組。2 度の読みが一致した 3 件) |
| 184 | アヒル戦法 |  | 奇襲戦法 | <https://ja.wikipedia.org/wiki/%E3%82%A2%E3%83%92%E3%83%AB%E5%9B%B2%E3%81%84> | <https://ja.wikipedia.org/wiki/Category%3A%E5%A5%87%E8%A5%B2%E6%88%A6%E6%B3%95> | 下書き済み(ahiru_senpo 自分。第 24 組。出典どうしが食い違う銀は入れていない) |
| 185 | 駒落ちの戦法(下手棒銀・銀多伝ほか 30 余) |  | 駒落ち(対象外) | **出典なし** | <https://ja.wikipedia.org/wiki/%E5%B0%86%E6%A3%8B%E3%81%AE%E6%88%A6%E6%B3%95%E4%B8%80%E8%A6%A7> | 対象外(駒落ち。本アプリは平手) |

## 3. 第 2 組(2026-09-25): 囲い 10 件

**足した ID(すべて `review_status: draft`、`side: self`、置き場 `data/drafts/2026-09-25-knowledge/shapes/`)**: `yagura_ginyagura`(銀矢倉)・`yagura_katayagura`(片矢倉)・`yagura_souyagura`(総矢倉、parent 金矢倉)・`gangi_nimaigin`(雁木、二枚銀)・`anaguma_ibisha`(居飛車穴熊、confidence low: 本文の手順から起こした)・`anaguma_furibisha`(振り飛車穴熊)・`mino_katamino`(片美濃)・`mino_kinmino`(金美濃)・`kanigakoi`(カニ囲い)・`hakoirimusume`(箱入り娘)。出典は各レコードの `source`(URL + 参照日 2026-09-25。shogi-gym.com の各囲いのページと Wikipedia の本文。文は写さず座標だけ起こした)。**予告と違う点**: ダイヤモンド美濃は shogi-gym の本文に座標が無く次の組へ回し、代わりに本文に座標のある金美濃・カニ囲い・箱入り娘を入れた。
**あわせて直したもの**: 第 1 組の 5 件の `source` を「自分の言葉 + URL + 参照日」に書き直し、出典の文の引用(『 』)を残していない(司令塔の決まり 2026-09-25)。
**スキーマ検証**: 使い捨て worktree の `data/shapes|openings/` に既存 + 下書き 15 件を置いて `node scripts/validate-data.mjs` → 検証OK(既存 23 + 15 = 38 件)。共有ツリーの本体には入れていない(本体の挙動は変わらない)。

**前後の数**(前 = 既存 3 + 第 1 組 3 の 6 件、後 = 16 件。同じ棋譜・同じ道具。本体に入れたらどうなるかの測定で、本体の今の挙動ではない):

**30 手まで**

| 対象 | 局面数 | **形の沈黙(証拠 2 件以上か完成が無い) 前→後** | 形だけ沈黙(forming 含む) 前→後 | 狙いだけ沈黙 前→後 | どちらも無し 前→後 | I-9 型 前→後 |
|---|---|---|---|---|---|---|
| 固定棋譜 4 局 | 59 | **43 → 39(73% → 66%)** | 25 → 25 | 29 → 29 | 17 → 17 | 97 → 166 |
| round2 3 局(参考) | 48 | **46 → 46(96% → 96%)** | 20 → 12 | 9 → 9 | 8 → 6 | 26 → 98 |
| 1 人目(10 局) | 157 | **154 → 136(98% → 87%)** | 60 → 38 | 40 → 40 | 21 → 19 | 104 → 379 |
| 2 人目(20 局) | 312 | **237 → 221(76% → 71%)** | 104 → 92 | 75 → 75 | 54 → 50 | 492 → 1063 |
| 3 人目(20 局) | 320 | **256 → 209(80% → 65%)** | 160 → 103 | 111 → 111 | 92 → 74 | 341 → 889 |
| 4 人目(20 局) | 307 | **302 → 246(98% → 80%)** | 147 → 104 | 53 → 53 | 42 → 40 | 355 → 711 |
| **4 人合計(70 局)** | 1096 | **949 → 812(87% → 74%)** | 471 → 337 | 279 → 279 | 209 → 183 | 1292 → 3042 |

**全手**

| 対象 | 局面数 | **形の沈黙(証拠 2 件以上か完成が無い) 前→後** | 形だけ沈黙(forming 含む) 前→後 | 狙いだけ沈黙 前→後 | どちらも無し 前→後 | I-9 型 前→後 |
|---|---|---|---|---|---|---|
| 固定棋譜 4 局 | 59 | **43 → 39(73% → 66%)** | 25 → 25 | 29 → 29 | 17 → 17 | 97 → 166 |
| round2 3 局(参考) | 48 | **46 → 46(96% → 96%)** | 20 → 12 | 9 → 9 | 8 → 6 | 26 → 98 |
| 1 人目(10 局) | 331 | **262 → 233(79% → 70%)** | 112 → 87 | 47 → 47 | 22 → 20 | 344 → 1100 |
| 2 人目(20 局) | 754 | **483 → 346(64% → 46%)** | 135 → 103 | 75 → 75 | 54 → 50 | 1827 → 3848 |
| 3 人目(20 局) | 998 | **476 → 335(48% → 34%)** | 192 → 116 | 111 → 111 | 92 → 74 | 1729 → 4087 |
| 4 人目(20 局) | 652 | **594 → 460(91% → 71%)** | 257 → 166 | 53 → 53 | 42 → 40 | 841 → 1976 |
| **4 人合計(70 局)** | 2735 | **1815 → 1374(66% → 50%)** | 696 → 472 | 286 → 286 | 210 → 184 | 4741 → 11011 |

**足した 10 件が 4 人 70 局で完成した局 / 3/4 以上一致した局**: yagura_ginyagura 0/3、yagura_katayagura 0/1、yagura_souyagura 0/0、gangi_nimaigin 0/1、anaguma_ibisha 0/0、anaguma_furibisha 0/2、mino_katamino 6/6、mino_kinmino 5/5、kanigakoi 0/3、hakoirimusume 0/4。
**読み方**: 証拠 2 件以上か完成に限った形の沈黙は 30 手までで 949 → 812(87% → 74%)、全手で 1815 → 1374(66% → 50%)。動いたのは主に 3 人目(振り飛車穴熊・金美濃・片美濃)と 4 人目(カニ囲い・片美濃・箱入り娘の証拠)。I-9 型(証拠 1 件以下の forming の主張)は 30 手までで 1292 → 3042 と増え(コミット 99258f4 の本文と説明では 3208 と誤記した。正しくは表の値 3042)、これは誤認の側の数として扱う(形が増えるほど 1 手で複数の形が forming になる。判定の話であり、この席は触らない)。**埋まった数 ÷ 目録の数: 囲い 16 / 62**(既存 3 + 第 1 組 3 + 第 2 組 10)、戦法 7 / 184(変わらず)。

## 4. 第 3 組(2026-09-25): 囲い 10 件

**足した ID(すべて `draft`・`side: self`、置き場は同じ)**: `anaguma_matsuo`(松尾流穴熊、parent 居飛車穴熊)・`anaguma_big4`(ビッグ4、parent 居飛車穴熊)・`anaguma_ginkanmuri`(銀冠穴熊、parent 居飛車穴熊)・`nakazumai`(中住まい、基本形 3 手。confidence low: 金銀の位置が定まらない)・`mutekigakoi`(無敵囲い、5八飛は optional)・`ichigogakoi`(いちご囲い)・`ahirugakoi`(アヒル囲い)・`mino_hayagakoi`(振り飛車早囲い)・`elmogakoi`(Elmo囲い)・`nakaharagakoi`(中原囲い)。出典は各レコードの `source`(shogi-gym.com の各囲いのページの本文、URL + 参照日 2026-09-25。文は写していない)。
**スキーマ検証**: worktree の `data/shapes|openings/` に既存 + 下書き 25 件を置いて `validate-data.mjs` → 検証OK(48 件)。本体には入れていない。

**前後の数**(前 = 16 件、後 = 26 件。同じ棋譜・同じ道具。本体に入れたらどうなるかの測定で、本体の今の挙動ではない):

**30 手まで**

| 対象 | 局面数 | **形の沈黙(証拠 2 件以上か完成が無い) 前→後** | 形だけ沈黙(forming 含む) 前→後 | 狙いだけ沈黙 前→後 | どちらも無し 前→後 | I-9 型 前→後 |
|---|---|---|---|---|---|---|
| 固定棋譜 4 局 | 59 | **39 → 39(66% → 66%)** | 25 → 25 | 29 → 29 | 17 → 17 | 166 → 250 |
| round2 3 局(参考) | 48 | **46 → 16(96% → 33%)** | 12 → 12 | 9 → 9 | 6 → 6 | 98 → 174 |
| 1 人目(10 局) | 157 | **136 → 128(87% → 82%)** | 38 → 37 | 40 → 40 | 19 → 18 | 379 → 688 |
| 2 人目(20 局) | 312 | **221 → 219(71% → 70%)** | 92 → 91 | 75 → 75 | 50 → 50 | 1063 → 1722 |
| 3 人目(20 局) | 320 | **209 → 209(65% → 65%)** | 103 → 103 | 111 → 111 | 74 → 74 | 889 → 1423 |
| 4 人目(20 局) | 307 | **246 → 234(80% → 76%)** | 104 → 99 | 53 → 53 | 40 → 40 | 711 → 1283 |
| **4 人合計(70 局)** | 1096 | **812 → 790(74% → 72%)** | 337 → 330 | 279 → 279 | 183 → 182 | 3042 → 5116 |

**全手**

| 対象 | 局面数 | **形の沈黙(証拠 2 件以上か完成が無い) 前→後** | 形だけ沈黙(forming 含む) 前→後 | 狙いだけ沈黙 前→後 | どちらも無し 前→後 | I-9 型 前→後 |
|---|---|---|---|---|---|---|
| 固定棋譜 4 局 | 59 | **39 → 39(66% → 66%)** | 25 → 25 | 29 → 29 | 17 → 17 | 166 → 250 |
| round2 3 局(参考) | 48 | **46 → 16(96% → 33%)** | 12 → 12 | 9 → 9 | 6 → 6 | 98 → 174 |
| 1 人目(10 局) | 331 | **233 → 214(70% → 65%)** | 87 → 73 | 47 → 47 | 20 → 19 | 1100 → 1686 |
| 2 人目(20 局) | 754 | **346 → 337(46% → 45%)** | 103 → 102 | 75 → 75 | 50 → 50 | 3848 → 6138 |
| 3 人目(20 局) | 998 | **335 → 297(34% → 30%)** | 116 → 113 | 111 → 111 | 74 → 74 | 4087 → 6250 |
| 4 人目(20 局) | 652 | **460 → 427(71% → 65%)** | 166 → 135 | 53 → 53 | 40 → 40 | 1976 → 3539 |
| **4 人合計(70 局)** | 2735 | **1374 → 1275(50% → 47%)** | 472 → 423 | 286 → 286 | 184 → 183 | 11011 → 17613 |

**足した 10 件が 4 人 70 局で完成した局 / 3/4 以上一致した局**: anaguma_matsuo 0/0、anaguma_big4 0/0、anaguma_ginkanmuri 0/1、nakazumai 0/0、mutekigakoi 0/47、ichigogakoi 0/1、ahirugakoi 0/0、mino_hayagakoi 0/0、elmogakoi 0/0、nakaharagakoi 0/0。
**読み方**: 証拠 2 件以上か完成に限った形の沈黙は 30 手までで 812 → 790(74% → 72%)、全手で 1374 → 1275(50% → 47%)。この組は穴熊の発展形・奇襲の囲い・横歩取りの囲いが中心で、4 人の棋譜にはほとんど現れない(完成 0 局が多い)ため動きは小さい。I-9 型は 30 手までで 3042 → 5116(誤認の側の数。玉が初期位置のままの局で無敵囲い・中住まいの証拠が 1 件立つため)。**埋まった数 ÷ 目録の数: 囲い 26 / 62**、戦法 7 / 184。

**次の組に回すもの(本文に座標があるもの)**: ボナンザ囲い・ミレニアム囲い・ダイヤモンド美濃(Wikipedia 本文)・菊水矢倉・矢倉穴熊・金開き・壁囲い・ちょんまげ美濃。**本文に座標が無く図だけのもの(埋めない)**: 天守閣美濃(shogi-gym)・木村美濃・銀美濃・坊主美濃・串カツ囲い(Wikipedia は図のみ)・左美濃(Wikipedia の本文と shogi-gym の本文で銀の位置が食い違う: 6八 と 7八。確かめてから)。多伝囲いは駒落ち専用(対象外)。地下鉄飛車は shogi-gym が囲いに分類するが飛車の位置で決まる戦法なので形には入れない。

## 5. 第 4 組(2026-09-25): 囲い 9 件と、埋められなかった 13 件

**足した ID(すべて `draft`・`side: self`)**: `bonanzagakoi`(ボナンザ囲い)・`yagura_kikusui`(菊水矢倉)・`yagura_anaguma`(矢倉穴熊、6八角は optional)・`mino_diamond`(ダイヤモンド美濃、parent 本美濃)・`kinbiraki`(金開き、low)・`kabegakoi`(壁囲い、low)・`yagura_hishi`(菱矢倉、parent 金矢倉、low)・`yagura_doi`(土居矢倉)・`gangi_tsunogin`(ツノ銀雁木、parent 二枚銀雁木)。出典は各レコードの `source`(URL + 参照日 2026-09-25)。
**2 件は出典の座標を継ぎ足して作った**(`source` に明記): ダイヤモンド美濃は「美濃囲いの 4七 に左銀」という記述 1 行 + 既存の本美濃の 4 マス、菱矢倉は「右銀が 6六」+ 金矢倉の 7八金。**継ぎ足した部分は出典が述べていない**ので confidence を下げた。
**スキーマ検証**: worktree に既存 + 下書き 34 件を置いて `validate-data.mjs` → 検証OK(57 件)。本体には入れていない。

**前後の数**(前 = 26 件、後 = 35 件。本体に入れたらどうなるかの測定で、本体の今の挙動ではない):

**30 手まで**

| 対象 | 局面数 | **形の沈黙(証拠 2 件以上か完成が無い) 前→後** | 形だけ沈黙(forming 含む) 前→後 | 狙いだけ沈黙 前→後 | どちらも無し 前→後 | I-9 型 前→後 |
|---|---|---|---|---|---|---|
| 固定棋譜 4 局 | 59 | **39 → 39(66% → 66%)** | 25 → 24 | 29 → 29 | 17 → 16 | 250 → 395 |
| round2 3 局(参考) | 48 | **16 → 16(33% → 33%)** | 12 → 12 | 9 → 9 | 6 → 6 | 174 → 207 |
| 1 人目(10 局) | 157 | **128 → 128(82% → 82%)** | 37 → 37 | 40 → 40 | 18 → 18 | 688 → 922 |
| 2 人目(20 局) | 312 | **219 → 209(70% → 67%)** | 91 → 87 | 75 → 75 | 50 → 50 | 1722 → 2351 |
| 3 人目(20 局) | 320 | **209 → 209(65% → 65%)** | 103 → 103 | 111 → 111 | 74 → 74 | 1423 → 2130 |
| 4 人目(20 局) | 307 | **234 → 232(76% → 76%)** | 99 → 98 | 53 → 53 | 40 → 40 | 1283 → 1812 |
| **4 人合計(70 局)** | 1096 | **790 → 778(72% → 71%)** | 330 → 325 | 279 → 279 | 182 → 182 | 5116 → 7215 |

**全手**

| 対象 | 局面数 | **形の沈黙(証拠 2 件以上か完成が無い) 前→後** | 形だけ沈黙(forming 含む) 前→後 | 狙いだけ沈黙 前→後 | どちらも無し 前→後 | I-9 型 前→後 |
|---|---|---|---|---|---|---|
| 固定棋譜 4 局 | 59 | **39 → 39(66% → 66%)** | 25 → 24 | 29 → 29 | 17 → 16 | 250 → 395 |
| round2 3 局(参考) | 48 | **16 → 16(33% → 33%)** | 12 → 12 | 9 → 9 | 6 → 6 | 174 → 207 |
| 1 人目(10 局) | 331 | **214 → 210(65% → 63%)** | 73 → 73 | 47 → 47 | 19 → 19 | 1686 → 2356 |
| 2 人目(20 局) | 754 | **337 → 317(45% → 42%)** | 102 → 95 | 75 → 75 | 50 → 50 | 6138 → 8533 |
| 3 人目(20 局) | 998 | **297 → 293(30% → 29%)** | 113 → 113 | 111 → 111 | 74 → 74 | 6250 → 9177 |
| 4 人目(20 局) | 652 | **427 → 416(65% → 64%)** | 135 → 134 | 53 → 53 | 40 → 40 | 3539 → 5012 |
| **4 人合計(70 局)** | 2735 | **1275 → 1236(47% → 45%)** | 423 → 415 | 286 → 286 | 183 → 183 | 17613 → 25078 |

**足した 9 件が 4 人 70 局で完成した局 / 3/4 以上一致した局**: bonanzagakoi 0/5、yagura_kikusui 0/0、yagura_anaguma 0/0、mino_diamond 0/5、kinbiraki 2/2、kabegakoi 0/0、yagura_hishi 0/0、yagura_doi 0/5、gangi_tsunogin 1/2。
**読み方**: 証拠 2 件以上か完成に限った形の沈黙は 30 手までで 790 → 778(72% → 71%)、全手で 1275 → 1236(47% → 45%)。ほとんど動かない。この組は上級者向けの発展形が中心で、4 人の棋譜には完成形がほぼ現れない。I-9 型は 30 手までで 5116 → 7215(全手 17613 → 25078)と増え続けており、**形を足すほど「証拠 1 件で名乗る」件数が線形に増える**ことが 4 組を通して見えた。**沈黙を減らす効きは第 2 組(美濃・矢倉・舟囲い・穴熊の基本形)で尽きており、以後は誤認の側だけが増えている。** 判定(証拠 1 件で forming)の話なのでこの席は触らないが、**形をこれ以上足しても沈黙率は下がらない**という事実として記録する。

### 5.1 埋められなかった 13 件(出典が図だけ / 出典どうしが食い違う)

目録にあるが**埋めなかった**もの。理由を書き、次に確かめるべき点を残す。**数えるときは「埋まった」に入れない。**

| 名前 | 理由 | 次に確かめること |
|---|---|---|
| 左美濃 | Wikipedia の本文に完成形の座標が無く(同じページを 2 回読んで、1 回目は図から座標を拾い、2 回目は本文に無いと答えた)、shogi-gym の本文は銀 7八、1 回目に図から読んだ値は銀 6八 で**食い違う** | 銀が 6八 か 7八 か。図の実物を人が見るか、別の一次資料で確かめる |
| 天守閣美濃 | Wikipedia は玉 8七 だけ本文にあり、銀・金は図のみ。shogi-gym の本文にも座標が無い | 玉 8七 以外の 4 マス |
| 四枚美濃 | 本文に座標が無く図のみ | 玉・銀 2 枚・金 2 枚の 5 マス |
| 銀立ち矢倉 | 本文は「左銀が 7六 に移れば」だけで、残りは図のみ | 玉・金の位置(金矢倉から継ぎ足すかは人の判断) |
| 天野矢倉 | 本文に座標が無く図のみ | 5 マスすべて |
| 矢倉早囲い | 本文は玉の通り道だけで、完成形は図のみ | 完成形の金銀の位置 |
| 右矢倉 | 本文に座標が無く図のみ(1 回目の読みは座標を答えたが、同じ答えの中で「図のみ」とも書いており当てにならない) | 相振り飛車での完成形 5 マス |
| 木村美濃 | 本文に座標が無く図のみ | 玉 2八・銀 3八・金 5八 以外の駒 |
| 銀美濃 | 本文は「左金の代わりに左銀」だけで、座標は図のみ | 左銀の位置(5七 か) |
| 坊主美濃 | 本文に座標が無く図のみ。本美濃の説明から拾った値しか出てこない | 玉頭の歩が無いこと以外の違い |
| ちょんまげ美濃 | 本文に座標が無く図のみ | 歩が 2六 にあるかと、残る金銀 |
| 串カツ囲い | 本文の説明(玉と香の位置が穴熊と逆)と、図から読んだ値(玉 9九・香 9八)が**食い違う** | 玉が 9八 か 9九 か |
| ミレニアム囲い(トーチカ) | **出典どうしが食い違う**。Wikipedia の読みは玉 8八・桂 7七・銀 6八/7八・金 6七/7九、shogi-gym の読みは玉 8九・金 7九/7八 | 玉が 8八 か 8九 か。桂 7七 は両方に出る |

**あわせて目録の状態を直したもの**: 多伝囲いは駒落ち専用(Wikipedia が二枚落ち・四枚落ち用と述べている)なので**対象外**にした。地下鉄飛車は解説サイトが囲いに分類しているが、飛車の位置で決まる攻めの構えなので**形には入れない**(戦法の目録の側に置いたまま)。

**この 13 件で分かったこと(進め方の事実)**: 囲いの解説ページは**完成形を図で示し、本文には座標を書かない**ものが多い。文章から座標を起こせるのは、いま使っている 2 つの解説サイトのうち shogi-gym.com の「完成図は、○八の玉を…で囲った形」という書き方をするページと、Wikipedia のうち本文に座標を書いている記事だけである。**図を読む工程を人が担うか、別の出典(棋譜データベース・書籍)を使うかは司令塔の判断**。

## 6. 残った沈黙は「囲っていない局面」だった(司令塔の確認への答え、2026-09-25)

問い: 「沈黙を減らす効きは第 2 組で尽きた」は、残る沈黙が居玉などの囲っていない局面だからという読みで合っているか。

**合っている。** 形 35 件のときの**形の沈黙**(証拠 2 件以上か完成の形が 1 件も無い局面)のうち、**自玉が初期位置 5九 のままの局面**を数えた(同じ道具に 1 行足して `tsc` を通してから測った)。

| 対象 | 30 手まで: 形の沈黙 / うち玉 5九 | 全手: 形の沈黙 / うち玉 5九 |
|---|---|---|
| 1 人目(10 局) | 128 / 121(95%) | 210 / 199(95%) |
| 2 人目(20 局) | 209 / 151(72%) | 317 / 151(48%) |
| 3 人目(20 局) | 209 / 178(85%) | 293 / 179(61%) |
| 4 人目(20 局) | 232 / 212(91%) | 416 / 281(68%) |
| **4 人合計(70 局)** | 778 / 662(85%) | 1236 / 810(66%) |

**4 人目は 30 手までの形の沈黙 232 局面のうち 212 局面(91%)で玉が 5九 のまま**だった。形を 3 件だったときと比べると、4 人目の形の沈黙は 307 → 232(玉 5九 は 267 → 212)で、**減った 75 局面のうち 55 局面は玉が動いていた局面**である。**玉が動かない局面は、囲いをいくら足しても残る。** 2026-09-12 の U6-A の発見(玉が初期位置付近に留まる囲いは存在しない。[STEP_UNIT6_PLAN_2026-09-12.md](STEP_UNIT6_PLAN_2026-09-12.md) §9.6)を、35 件でもう一度確かめた形になる。

**この数が言わないこと**: 玉が 5九 のままであることを良し悪しとして述べていない。「その局面で言うことが無い」のは道具の側の事実であって、指した人の指し方の評価ではない。埋めるなら狙い(intents)か、形以外の材料(③)の側になる。

## 7. 第 5 組(2026-09-25): 戦型 10 件 ― **測れない(認識のコードが無い)**

**足した ID(すべて `draft`、置き場 `data/drafts/2026-09-25-knowledge/openings/`)**: `sankenbisha`(三間飛車・自分)・`sankenbisha_opponent`(同・相手)・`shikenbisha_opponent`(四間飛車・相手)・`mukaibisha_opponent`(向かい飛車・相手)・`nakabisha_self`(中飛車・自分)・`migi_shikenbisha`(右四間飛車・自分)・`migi_shikenbisha_opponent`(同・相手)・`ishidaryu`(石田流・自分)・`gokigen_nakabisha`(ゴキゲン中飛車・相手)・`fujii_system`(藤井システム・自分)。出典は各 `source`(Wikipedia の当該記事、URL + 参照日 2026-09-25)。
**選び方**: 4 人 70 局の 40 手目で飛車があった筋を数え、多い順に埋めた。自分側(先手)は 2 筋 21 局(居飛車、既存)・8 筋 12 局(向かい飛車、第 1 組)・7 筋 7 局(三間飛車)・5 筋 7 局(中飛車)・6 筋 6 局(四間飛車、既存)・4 筋 3 局(右四間飛車)。相手側(後手)は 8 筋 31 局(居飛車、既存)・4 筋 6 局(四間飛車)・6 筋 6 局(右四間飛車)・2 筋 5 局(向かい飛車)・5 筋 4 局(中飛車、既存)・3 筋 3 局(三間飛車)。
**測れない**: 戦型を認識するコードは `apps/server/src/analysis/` に無い(2026-09-25 司令塔の訂正)。したがって沈黙率・誤認は**この 10 件では動かない**。前後の測定は行っていない(動かないものを測っても数が同じになるだけなので、代わりに下の 2 つを確かめた)。

**確かめたこと 2 つ**:

1. **`data/openings/` は読まれていないわけではない。** 認識には使われないが、**相手 AI 制御(Kind 3)の読み込み口 `apps/server/src/engine/scenarioRepository.ts` が `data/openings/` の全 JSON を読む**(`loadApprovedScenarioVariants`)。形式が合わないファイルがあると例外を投げる。**本体へ移すときはここを通る**ので、使い捨て worktree に 15 件(既存 3 + 下書き 12)を置いて実際に呼び、**例外なく `variants = 0`** を確かめた(`scenario: null` の行は候補に入らない)。`loadShapes` 35・`loadIntents` 8 も同時に確かめた。
2. **スキーマ検証**: worktree で `validate-data.mjs` → 検証OK(67 件)。`leads_to_shape_ids` の参照先(`mino_honmino`・`mino_katamino`・`anaguma_furibisha`)も解決する。

**書けなかった条件(スキーマの限界。構造的知識なので直さない)**:

- `fujii_system` は `recognition_pattern` を書いていない。出典が述べる特徴が「玉を囲わない」「相手に美濃囲いを組ませない駒組み」という**駒が動かないこと・全体の配置**で、いまのスキーマ(駒種 + 移動先の並び)では表せないため。この欄を持たない戦型は認識の候補にならない。
- `gokigen_nakabisha` は「角道を開けたまま」という条件が書けないので、2 手(５四歩・５二飛)だけでは通常の中飛車と区別がつかない。`source` に明記した。
- 相手側の戦型 5 件は `leads_to_shape_ids` が空。**相手側の陣形(`side: opponent` の shapes)が data/ に 1 件も無い**ため(次のまとまりの候補)。

**側の書き分け**: 既存の `ibisha`(相手)・`nakabisha`(相手)・`shikenbisha`(自分)は side を id に持たない。今回からは、**もう一方の側が既にあるときだけ id に側を付けた**(`nakabisha_self`・`shikenbisha_opponent` など)。既存レコードの改名は司令塔の判断事項なので触っていない。

**埋まった数 ÷ 目録の数: 囲い 35 / 62、戦法 12 / 184。** 数えているのは**目録の行(名前)**で、レコードの数とは違う(戦法のレコードは 15 件 = 既存 3 + 下書き 12。同じ名前が自分側・相手側の 2 件になるため行より多い)。囲いは 1 行 1 レコードなので 35 で一致する。

**目録の側で分かったこと**: 相振り飛車・対抗型・相居飛車は**対局の組み合わせを表す名前**で、`openings.schema.json` の `side`(self / opponent)のどちらにも当てはまらない。埋めずに目録で保留にした(スキーマを変えるのは構造的知識 = 人間の承認事項)。

## 8. 第 6 組(2026-09-25): 戦型 7 件 ― **測れない(認識のコードが無い)**

**足した ID(すべて `draft`・`side: self`)**: `yagura_senpo`(矢倉)・`kakugawari`(角換わり)・`aigakari`(相掛かり)・`yokofudori`(横歩取り)・`boh_gin_self`(棒銀)・`hayaishida`(早石田)・`koshikakegin`(腰掛け銀)。相居飛車の 4 系統(4 人の棋譜で自分の飛車が 2 筋だった 21 局・相手が 8 筋だった 31 局が当たる)と、その中の指し方 3 つ。出典は各 `source`(Wikipedia の当該記事、URL + 参照日 2026-09-25)。スキーマ検証 OK。
**測れない**(認識のコードが無い)。前後の測定はしていない。

**書けなかった条件(`source` に明記)**:

- `kakugawari`: **角の交換そのもの**(相手の駒を取る・持ち駒になる)は駒種 + 移動先では書けないので、7七 に角が上がり、のちに銀が 7七 へ来た跡で代用した。
- `koshikakegin`: 「5七に歩がある」という**初期位置の駒を条件にすること**ができない(歩は最初から 5七 にいるので、そこへ動く手が存在しない)。
- `boh_gin_self`: 銀の進路が戦型ごとに違う(出典は相掛かり 3八→2七→2六、角換わりは 1 筋絡み、対振りは相手の角の頭)。**相掛かりの形だけ**を書いた。
- `yagura_senpo`: 7六歩・6八銀は他の戦型でも指される手なので、3 手がそろって初めて手がかりになる。**1 手の一致で forming が立つ作り**では序盤に他の戦型へも当たる。

**埋まった数(目録の行): 囲い 35 / 62、戦法 19 / 184。**

## 9. 第 7 組(2026-09-25): **相手側の陣形 10 件** ― ここは測れる

**足した ID(すべて `draft`・`side: opponent`)**: `mino_honmino_opponent`・`mino_takamino_opponent`・`mino_ginkanmuri_opponent`・`mino_katamino_opponent`・`funagakoi_opponent`・`yagura_kinyagura_opponent`・`kinmusou_opponent`・`anaguma_furibisha_opponent`・`anaguma_ibisha_opponent`・`elmogakoi_opponent`。

**作り方**: 自分側の同じ形の座標を**盤ごと 180 度回した**(筋 f → 10−f、段 r → 10−r の**両方**)。例: 本美濃 2八玉・3八銀・4九金・5八金 → 8二玉・7二銀・6一金・5二金。写像の式と写した組は各レコードの `source` に書いた。**出典そのものが後手の座標を述べているわけではない**(出典は自分側のレコードの `source`)。
**なぜ念を押すか**: 過去に「段だけを反転させて左右が入れ替わる」取り違えが起きている([PHASES.md](PHASES.md) の P-12、[STEP_UNIT6_PLAN_2026-09-12.md](STEP_UNIT6_PLAN_2026-09-12.md) §9.5 の決定 3「実際の盤と突き合わせて確かめる。理屈だけで直さない」)。そこで**実棋譜で当たるかを測ってから記録した**(下記)。判定は後手視点で行われる(`apps/server/src/analysis/shapeDetector.ts` の `perspectiveColorsForSide` が `side: opponent` を gote に固定する)。

**測った数**(4 人 70 局。**自分側と相手側を分けて**数えた。証拠 2 件以上か完成の形が 1 件以上ある局面の数):

| 対象 | 局面数(30 手まで / 全手) | 自分側 前→後 | **相手側 前→後** |
|---|---|---|---|
| 1 人目(10 局) | 157 / 331 | 29→29 / 121→121 | **0→33 / 0→130** |
| 2 人目(20 局) | 312 / 754 | 103→103 / 437→437 | **0→128 / 0→406** |
| 3 人目(20 局) | 320 / 998 | 111→111 / 705→705 | **0→142 / 0→556** |
| 4 人目(20 局) | 307 / 652 | 75→75 / 236→236 | **0→62 / 0→205** |
| **4 人合計(70 局)** | 1096 / 2735 | 318→318 / 1499→1499 | **0→365(33% の局面) / 0→1297(47%)** |

**自分側の数は 1 も動いていない**(29/103/111/75 のまま)。相手側の形を足しても自分側の判定に触っていないことの確かめになる。

**形ごとの当たり方**(4 人 70 局。完成した局 / 必須マスの 3/4 以上が一致した局):

| 相手側の形 | 完成した局 | 3/4 以上 |
|---|---|---|
| 片美濃 | 11 | 11 |
| 本美濃 | 5 | 11 |
| 舟囲い | 3 | 10 |
| 金無双 | 1 | 1 |
| 矢倉 | 0 | 8 |
| Elmo囲い | 0 | 1 |
| 居飛車穴熊 | 0 | 1 |
| 振り飛車穴熊 | 0 | 0 |
| 高美濃 | 0 | 0 |
| 銀冠 | 0 | 0 |

**読み方**: 相手の片美濃が 11 局・本美濃が 5 局・舟囲いが 3 局・金無双が 1 局で**完成まで**当たった。**段だけを反転していたらこれらは 1 局も完成しない**ので、180 度回転が正しく効いていることの実測の裏づけになる(それでも、個々の形の名前が将棋として正しいかは別の話で、確かめていない)。

**本体の挙動への影響(測っていないが、コードの作りから言えること)**: 目標形の経路(`rankReachableShapes`)は `side === "opponent"` を除くので、相手側の形は④「自分の目的」の候補には入らない。ただし**`data/shapes/` に置けば `detectShapes` は全件を判定する**ので、認識の一覧には現れる。本体へ移すかは司令塔の判断(このレーンは移さない)。

**埋まった数**: 目録の行は**名前**で数えているので、相手側を足しても行は増えない(囲い 35 / 62 のまま)。**レコードの数は 45 件**(自分側 35 + 相手側 10)。

## 10. 第 8 組(2026-09-25): 戦型 8 件 ― **測れない(認識のコードが無い)**

**足した ID(すべて `draft`・`side: self`)**: `yamada_joseki`(山田定跡)・`sagimiya_joseki`(鷺宮定跡)・`boukin`(棒金)・`chousoku_37gin`(超速3七銀)・`naname_bogin_self`(4六銀左戦法 = 斜め棒銀)・`torisashi`(鳥刺し)・`nakabisha_hidari_anaguma`(中飛車左穴熊)・`tsunogin_nakabisha`(ツノ銀中飛車)。相手が振り飛車のときの急戦と、振り飛車の中の形。出典は各 `source`(Wikipedia、URL + 参照日 2026-09-25)。スキーマ検証 OK。
**測れない**(認識のコードが無い)。前後の測定はしていない。相手側の形の数も自分側の数も動いていない(戦型は判定に使われないため)。

**手の並びでは分けられない組(記録として残す)**: 山田定跡・鷺宮定跡・4六銀左戦法は、いずれも **3五歩 + 4六銀**を含む。分かれ目は鷺宮の **3八飛**だけで、山田定跡と4六銀左戦法は手の並びだけでは分けられない(出典も 3 つを同じ定跡体系として説明している)。超速3七銀の **4六銀**も同じマスに来る(分かれ目は 3七 を通ることと、相手が中飛車であること)。**「相手がこの戦型のときだけ」という条件は、いまのスキーマでは書けない**(戦型どうしの組み合わせを表す欄が無い)。

**出典が書いていないマスは足していない**: 鳥刺しは角 7九 の 1 手だけ(銀の行き先を出典が書いていない)、中飛車左穴熊は飛車 5六 の 1 手だけ(玉の最終位置を 1 マスで述べていない)。

**埋まった数(目録の行): 囲い 35 / 62、戦法 26 / 184。** 足した 8 件のうち 4六銀左戦法の行は、既存の intent `naname_bogin`(相手側)で**すでに埋まったと数えていた**ため、行は 19 + 7 = 26 になる(8 ではなく 7 しか増えない)。レコード数は 囲い 45(自分側 35 + 相手側 10)・戦型 30(既存 3 + 下書き 27)。

## 11. 第 9 組(2026-09-25): 戦型 7 件と保留 1 件 ― **測れない(認識のコードが無い)**

**足した ID(すべて `draft`)**: `tateishiryu`(立石流四間飛車・自分)・`direct_mukaibisha`(ダイレクト向かい飛車・相手)・`sakataryu_mukaibisha`(阪田流向かい飛車・相手)・`meriken_mukaibisha`(メリケン向かい飛車・自分)・`youryuu_shikenbisha`(耀龍四間飛車・自分)・`regusupe`(レグスペ・自分)・`nakata_xp`(中田功XP・自分)。出典は各 `source`(Wikipedia、URL + 参照日 2026-09-25)。スキーマ検証 OK。**測れない**(認識のコードが無い)。

**保留 1 件: 角交換四間飛車**。出典(Wikipedia『角交換四間飛車』)の読みが **先手の飛車を 8筋 と述べている**ように取れ、四間飛車の定義(先手は 6筋。Wikipedia『四間飛車』)と食い違う。**どちらが正しいか確かめられないので埋めない**(振り直しの話なのか、最初から 8筋 なのかが読めない)。目録に理由を書いた。

**同じ 1 手になってしまう組(記録)**: `direct_mukaibisha` の 2二飛 は `mukaibisha_opponent` と同じ 1 手で、違いは「四間飛車に振り直す手順を省いた」という**手順の来歴**にある。いまのスキーマ(駒種 + 移動先の並び)は**来歴を書けない**ので、この 2 つは機械では分けられない。`regusupe` の 8八飛 は `mukaibisha` と、`youryuu_shikenbisha` の 3八玉 は `mino_hayagakoi`・`kinmusou` と同じマスで、分かれ目はもう 1 手の側にある。

**埋まった数(目録の行): 囲い 35 / 62、戦法 33 / 184。** レコード数は 囲い 45・戦型 37(既存 3 + 下書き 34)。

## 12. 第 10 組(2026-09-25): 戦型 6 件と保留 2 件 ― **測れない(認識のコードが無い)**

**足した ID(すべて `draft`・`side: self`)**: `masuda_ishida`(升田式石田流)・`onikoroshi`(鬼殺し)・`genshi_nakabisha`(原始中飛車)・`sente_nakabisha`(先手中飛車)・`gosuji_kuraidori_nakabisha`(5筋位取り中飛車)・`fuusha`(風車、low)。出典は各 `source`(Wikipedia、URL + 参照日 2026-09-25)。スキーマ検証 OK。**測れない**。

**保留 2 件**:

| 名前 | 理由 | 次に確かめること |
|---|---|---|
| トマホーク | 出典の本文が「端桂を 9筋 へ」と読めるが、この戦法が狙う相手(**後手の**居飛車穴熊)は盤の 1筋 側にいるため、先手が攻める端が 9筋 か 1筋 かが決められない | 端攻めの筋(先手基準で 1筋 か 9筋 か) |
| 真部流 | Wikipedia の当該ページに**定義が書かれていない**(棋士の記事で、飛車・銀・角の配置の説明が無い) | 別の出典(書籍・解説サイト)での定義 |

**スキーマに書けなかった条件(記録)**: `genshi_nakabisha` の「序盤の早い段階で」という**手数の早さ**(`order_hint` は並びの目安で何手目かではない)、`sente_nakabisha` の「先手だけが組める」という**手番の条件**(いまは `side: self` = 先手という仕様に頼っている)、`fuusha` の「玉と飛車が決まったマスに落ち着かない」(出典自身が行き来すると述べている)。

**埋まった数(目録の行): 囲い 35 / 62、戦法 39 / 184。** レコード数は 囲い 45・戦型 43(既存 3 + 下書き 40)。

## 13. 第 11 組(2026-09-25): 戦型 8 件(矢倉の中の指し方) ― **測れない(認識のコードが無い)**

**足した ID(すべて `draft`)**: `wakisystem`(脇システム・自分)・`suzumesashi`(雀刺し・自分)・`kanikanigin`(カニカニ銀・自分)・`morishita_system`(森下システム・自分、low、`recognition_pattern` 無し)・`yagura_bogin`(矢倉棒銀・自分)・`yagura_37gin`(矢倉3七銀・自分)・`douke_yagura`(同型矢倉・自分)・`yonenaga_kyusen_yagura`(米長流急戦矢倉・**相手**)。出典は各 `source`(Wikipedia、URL + 参照日 2026-09-25)。スキーマ検証 OK。**測れない**。

**この組で分かった、スキーマの限界の 4 つ目の型**: これまでに出た「否定の条件(飛車を動かさない)」「初期位置の駒を条件にすること(5七の歩)」「手順の来歴(振り直しを省いた)」「手数(何手目)」に加えて、

- **`morishita_system`**: 骨子が「**先に形を決めないこと**」。出典が挙げる 4八銀は「そこへ動く手」ではなく「**そこに留まること**」が特徴で、その後は相手次第で分かれる。`recognition_pattern` を書かずに置いた(認識の候補にならない戦型)。
- **`douke_yagura`・`wakisystem`**: 定義の半分が「**相手も同じ形であること**」「相手の角が 6四 にあること」。いまのスキーマは**片側の手しか書けない**ので、書いた手は同型でない矢倉にも当たる。
- **`kanikanigin`**: 「玉と金を動かさない(居玉)」が書けない。

**同じマスに集まる手(記録)**: **4六銀**は山田定跡・鷺宮定跡・4六銀左戦法・超速3七銀・カニカニ銀の 5 つに出る。**銀 2六**は相掛かりの棒銀と矢倉棒銀に出る(通り道が 3八→2七 か 4八→3七 かで分かれる)。**銀 3七**は矢倉3七銀と超速3七銀に出る。**1 手の一致で forming が立つ作り**では、序盤でこれらが同時に立つ。

**埋まった数(目録の行): 囲い 35 / 62、戦法 47 / 184。** レコード数は 囲い 45・戦型 51(既存 3 + 下書き 48)。

## 14. 第 12 組(2026-09-25): 戦型 8 件(角換わり・相掛かり・横歩取りの中の指し方)と、戦法の区切り

**足した ID(すべて `draft`)**: `kakugawari_koshikakegin`・`kakugawari_bogin`・`sujichigai_kaku`・`tsukada_special`・`hineribisha`・`kusarigamagin`(low)・`yokofudori_85hi`(**相手**)・`ittezon_kakugawari`(**相手**)。出典は各 `source`(Wikipedia、URL + 参照日 2026-09-25)。スキーマ検証 OK。**測れない**。

**打つ手・取る手の書き方(記録)**: `sujichigai_kaku` の 4五角は**打つ手**、`ittezon_kakugawari` の 8八角は**相手の駒を取って成る手**だが、スキーマは「駒種 + 移動先」しか持たないので、どちらも**移動先のマスだけ**で表している(既存の `data/intents/` も同じ書き方)。取る・打つ・成るの区別は書けない。

**戦法はここで一度区切る(司令塔の決定 2026-09-25、指示書 §1 2b `25ae7d7`)**: 順を **狙い(intents)→ 相手側の形 → 戦法の残り** に変える。理由は測った事実 3 つ ― 形は 35 件で沈黙が下げ止まり増えるのは誤認だけ / 戦型は測れない / 相手側の形は効いた(0 → 365 局面)。**狙いは測れる**(`intentDetector` が `data/intents` を読み、②③として画面に出る経路がある)うえ、**狙いだけの沈黙が 30 手までで 279 / 1096 局面**残っている。網羅の目標は変えず、狙いと相手側の形が尽きたら戦法に戻る。

**区切りの時点の数(目録の行): 囲い 35 / 62、戦法 55 / 184(保留 6、未 123。うち出典なし 41 なので、埋められる残りは約 82)。** レコード数は 囲い 45・戦型 59(既存 3 + 下書き 56)。

## 15. 狙い(intents)の目録(2026-09-25)

**順を変えた理由**は §14。狙いは**測れる**(`intentDetector` が `data/intents` を読む)。目録の作り方は司令塔の指示(2026-09-25): **4 人の棋譜で相手が実際に指した手筋から先、次に一般的な手筋**。

### 15.1 実測: 4 人 70 局で相手(後手)が指した手(駒種 × 移動先)

使い捨てスクリプト(`apps/server` の `replayMoveHistory` を呼ぶだけ)で、後手の手を「駒種 + 移動先」で数えた。**70 局中いくつの局に現れたか**の多い順。`tsc` を通してから回した。上位 30 を載せる(全体は scratchpad の JSON)。

| 駒と移動先 | 局数 / 70 | 回数 | いまの 8 件で当たるか |
|---|---|---|---|
| 歩4d | 40 | 50 | **当たらない** |
| 歩5d | 37 | 45 | **当たらない** |
| 歩3d | 36 | 45 | **当たらない** |
| 金3b | 35 | 39 | **当たらない** |
| 金5b | 34 | 46 | **当たらない** |
| 銀4b | 34 | 40 | naname_bogin |
| 歩7d | 33 | 42 | **当たらない** |
| 歩6d | 32 | 35 | hayajikake |
| 歩1d | 32 | 35 | **当たらない** |
| 銀6b | 31 | 40 | **当たらない** |
| 歩8d | 30 | 38 | hishasaki_fugokan |
| 歩8e | 29 | 38 | hishasaki_fugokan |
| 歩2d | 29 | 34 | **当たらない** |
| 歩9d | 28 | 33 | **当たらない** |
| 桂3c | 26 | 29 | **当たらない** |
| 歩8f | 25 | 27 | hishasaki_fugokan / hishasaki_toukin |
| 桂7c | 24 | 26 | **当たらない** |
| 歩5e | 23 | 30 | nakabisha_kuraidori |
| 玉6b | 22 | 28 | **当たらない** |
| 歩4e | 22 | 25 | nakabisha_kuraidori |
| 銀6c | 22 | 25 | **当たらない** |
| 銀5d | 21 | 28 | **当たらない** |
| 玉4b | 21 | 27 | **当たらない** |
| 歩6e | 20 | 25 | hayajikake |
| 歩3e | 20 | 24 | hisha_3suji_tenkan |
| 銀5c | 19 | 29 | naname_bogin |
| 銀3c | 19 | 23 | **当たらない** |
| 銀2b | 19 | 21 | **当たらない** |
| 角3c | 18 | 21 | **当たらない** |
| 銀4c | 18 | 20 | **当たらない** |

**読み方**: 上位 30 のうち、いまの 8 件で当たるのは 9 つだけ。**当たらない手のうち局数が多いもの**が、次に足す狙いの候補になる ― 桂3c(26 局)・桂7c(24 局)・飛8f(15 局)・角8h(15 局)・歩9e(14 局)・銀6e(14 局)・歩7e(14 局)・歩1e(13 局)・銀4e(12 局)・角4d(12 局)・歩4f(12 局)。玉と金銀の移動(玉6b・金3b・銀4b など)は**囲いの側**で扱う(shapes)。

### 15.2 一般の名前つき手筋(出典: Wikipedia『手筋 (将棋)』・『端攻め』)

`https://ja.wikipedia.org/wiki/手筋_(将棋)` (参照日 2026-09-25) が挙げる名前を駒別に写した(**55 件**。数え直した値。駒別の内訳は下の表のとおり)。**このうち大半は、いまのスキーマでは書けない。**

| 駒 | 名前 | いまのスキーマで書けるか |
|---|---|---|
| 歩 | 手裏剣の歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 焦点の歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 叩きの歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 垂れ歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | ダンスの歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 継ぎ歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 歩の連打 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 控えの歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 底歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 面打の歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 蓋歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 紐歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 単打の歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 合わせ歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 突き違いの歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | 突き越しの歩 | 筋が決まれば書ける(端攻めの入口) |
| 歩 | と金攻め | **既存 `hishasaki_toukin` が 8筋 の形で書いている** |
| 歩 | 銀ばさみ | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 歩 | バックの歩 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 香 | 2段ロケット | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 香 | 田楽刺し | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 香 | 歩の裏側に香打ち | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 桂 | ふんどしの桂 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 桂 | 歩頭の桂 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 桂 | つるし桂 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 桂 | 控えの桂 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 桂 | 継ぎ桂 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 桂 | 跳ね違いの桂 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 銀 | 割打ちの銀 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 銀 | 桂頭の銀 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 銀 | 腹銀 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 銀 | 銀をかける | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 金 | 頭金 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 金 | 尻金 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 金 | 腹金 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 金 | タコ金 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 金 | 金送りの手筋 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 角 | 筋違いの角打ち | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 角 | 角による両取り | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 角 | 攻防の角 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 角 | 自陣角 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 角 | 遠見の角 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 角 | 幽霊角 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 角 | 角交換 | 移動先のマス(8八)でなら書ける ― §17 で足す |
| 角 | 角のたすき掛け | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 角 | 角のコビン攻め | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 角 | 角切り | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 角 | 馬引き | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 飛 | 十字飛車 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 飛 | 自陣への飛車打ち | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 飛 | 一間龍 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 飛 | 送りの手筋 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 飛 | 飛車交換 | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 飛 | 飛車切り | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 飛 | 龍引き | **書けない**(相手の駒との位置関係で決まり、決まったマスが無い) |
| 端 | 端攻め | **筋が決まるので書ける**(9筋・1筋。`https://ja.wikipedia.org/wiki/端攻め` (参照日 2026-09-25): 盤の 9筋 か 1筋 から攻める手法。端歩を伸ばし、桂・香・飛車を絡める) |

**ここが狙いの目録のいちばん大事な事実**: 手筋 55 件のうち、**決まったマスの並びで書けるのは 3 件だけ**(突き越しの歩・と金攻め・角交換)。残りの 52 件は「相手の駒の頭」「両取りになる位置」のように**相手の駒との位置関係**で決まり、いまのスキーマ(`recognition_pattern` = 駒種 + 移動先の固定マス)では表せない。**狙いを増やすことで沈黙を減らせるのは、戦法由来の攻め筋(序盤〜中盤の、筋が決まった攻め)に限られる。**

### 15.3 目録の数

| 区分 | 数 | 出典 | 備考 |
|---|---|---|---|
| A. 実測で当たらない手(狙いの候補) | 11 | 実測(この記録 §15.1) | 桂3c・桂7c・飛8f・角8h・歩9e・銀6e・歩7e・歩1e・銀4e・角4d・歩4f |
| B. 一般の手筋のうち書けるもの | 4 | Wikipedia『手筋 (将棋)』『端攻め』 | 突き越しの歩・と金攻め(既存)・角交換・端攻め |
| C. 一般の手筋のうち**書けない**もの | 52 | 同上 | 位置関係で決まるため。**埋めない** |
| D. 戦法由来の攻め筋(§2.2 の戦法の目録から、相手側の攻めとして立つもの) | 約 30 | 戦法の目録 | 棒銀・斜め棒銀・早仕掛け・位取りなど。**うち 8 件は既存** |

**数**: **狙いの目録 N = 67**(A 11 + B 4 + C 52)。**うち書けない K = 52**(出典はあるが、スキーマで表せない)。**既存は 8 件**(`data/intents/`。`human_reviewed` 3・`draft` 5)。D の戦法由来は §2.2 の行と重なるので二重に数えない。

## 16. 第 13 組(2026-09-25): 狙い 5 件 ― **ここが一番効いた**

**足した ID(すべて `draft`・`side: opponent`、置き場 `data/drafts/2026-09-25-knowledge/intents/`)**: `kakukoukan`(角交換)・`hashizeme_9suji`(端攻め(9筋))・`hashizeme_1suji`(端攻め(1筋))・`gyokutogin`(玉頭銀)・`hashikaku`(端角、low)。

**司令塔の縛り(2026-09-25)に合わせて 6 件を捨てた**: 「**頻度から名前を作らない**。名前のある手筋に出典つきで対応づけられたものだけを下書きにする」。最初に §15.1 の実測 11 件から 10 件を書いたが、**名前のある手筋に対応づけられたのは 5 件だけ**だったので、残りは消して目録に「出典なし(手だけ)」として残した。

| 消した下書き | 実測 | なぜ名前に対応づけられなかったか |
|---|---|---|
| 7三への桂跳ね | 24 局 | 出典の手筋一覧(桂の手筋 6 件)にこの形の名前が無い。7三桂を含む名前つきの作戦は `yonenaga_kyusen_yagura`(米長流急戦矢倉、第 11 組)で戦型の側に入れた |
| 3三への桂跳ね | 26 局 | 同じ理由で名前が無い |
| 飛車が8六へ出る | 15 局 | 名前があるのは『飛車先の歩交換』(既存 `hishasaki_fugokan`)で、飛車が 8六 に出る手そのものの名前は無い |
| 銀が4五へ出る | 12 局 | 名前が無い(玉頭銀は後手側では 5四-6五-7六 の道で、4五 は通らない) |
| 角が4四へ出る | 12 局 | 名前が無い |
| 4筋の歩をぶつけてくる | 12 局 | 名前が無い(『合わせ歩』『突き違いの歩』は相手の駒との位置関係で決まる手筋で、筋が固定されない) |

**足した 5 件の出典**: 角交換 = Wikipedia『手筋 (将棋)』の角の手筋 / 端攻め(9筋・1筋) = Wikipedia『端攻め』(盤の 9筋 か 1筋 から攻める手法。美濃囲いや穴熊のように玉が端に寄る形には響きやすい) / 玉頭銀 = Wikipedia『玉頭銀』(振り飛車側の左銀を 5六-4五-3四 と進出。**後手の座標へ 180 度回して 5四-6五-7六 と写した**) / 端角 = Wikipedia『端角』(角を端 ― 先手 9七・後手 1三 ― へ動かす)。いずれも参照日 2026-09-25。

**測った数**(形は第 7 組の 45 件で固定し、**狙いだけを 8 件 → 13 件に増やした**。前後で同じ棋譜・同じ道具):

**30 手まで**

| 対象 | 局面数 | **狙いだけ沈黙(証拠 2 件以上か matched) 前→後** | 狙いだけ沈黙(証拠 1 件で立つ版) 前→後 |
|---|---|---|---|
| 1 人目(10 局) | 157 | **95 → 81(61% → 52%)** | 40 → 32 |
| 2 人目(20 局) | 312 | **231 → 174(74% → 56%)** | 75 → 59 |
| 3 人目(20 局) | 320 | **229 → 216(72% → 68%)** | 111 → 99 |
| 4 人目(20 局) | 307 | **178 → 149(58% → 49%)** | 53 → 51 |
| **4 人合計(70 局)** | 1096 | **733 → 620(67% → 57%)** | 279 → 241 |

**全手**

| 対象 | 局面数 | **狙いだけ沈黙(証拠 2 件以上か matched) 前→後** | 狙いだけ沈黙(証拠 1 件で立つ版) 前→後 |
|---|---|---|---|
| 1 人目(10 局) | 331 | **127 → 107(38% → 32%)** | 47 → 32 |
| 2 人目(20 局) | 754 | **381 → 217(51% → 29%)** | 75 → 59 |
| 3 人目(20 局) | 998 | **353 → 265(35% → 27%)** | 111 → 99 |
| 4 人目(20 局) | 652 | **219 → 166(34% → 25%)** | 53 → 51 |
| **4 人合計(70 局)** | 2735 | **1080 → 755(39% → 28%)** | 286 → 241 |

**読み方(この記録でいちばん大きい数)**: **5 件足しただけで、狙いだけの沈黙(証拠 2 件以上か matched)が 30 手までで 733 → 620(−113)、全手で 1080 → 755(−325)動いた。** 形は 10 件足しても 30 手までで 949 → 812(−137)、次の 10 件で −22、次の 9 件で −12 と落ちていったのに対し、**狙いは 1 件あたりの効きが桁で大きい**。2026-09-12 の U6-A の結論(「沈黙を動かすのは狙いの方」。[STEP_UNIT6_PLAN_2026-09-12.md](STEP_UNIT6_PLAN_2026-09-12.md) §9.6)を、実棋譜 70 局で裏づけた形になる。

**狙いごとの当たり方(4 人 70 局、全手。局面数 / 1 回以上当たった局数)**:

| 狙い | 局面数 | 当たった局 / 70 | 新旧 |
|---|---|---|---|
| `naname_bogin` | 1496 | 48 | 既存 |
| `hishasaki_fugokan` | 1447 | 45 | 既存 |
| `hashizeme_1suji` | 1143 | 35 | **新** |
| `nakabisha_kuraidori` | 1132 | 43 | 既存 |
| `hayajikake` | 1062 | 34 | 既存 |
| `hashizeme_9suji` | 964 | 32 | **新** |
| `gyokutogin` | 697 | 29 | **新** |
| `hishasaki_toukin` | 672 | 28 | 既存 |
| `hisha_3suji_tenkan` | 513 | 23 | 既存 |
| `kakukoukan` | 442 | 16 | **新** |
| `boh_gin` | 354 | 15 | 既存 |
| `hashikaku` | 218 | 6 | **新** |
| `gyokuto_gin_semari` | 59 | 5 | 既存 |

**新しい 5 件のうち効いたのは端攻めと玉頭銀**(1筋 35 局・9筋 32 局・玉頭銀 29 局)。**端角は 6 局**で、既存の `gyokuto_gin_semari`(5 局)と同じくらい少ない。

**注意(この数が言わないこと)**: 「狙いが当たった」= 相手が本当にその狙いを持っていた、ではない。`recognition_pattern` は**順不同の断片**なので、端の歩を 1 つ突いただけでも forming が立つ(だから証拠 2 件以上の列を見出しにしている)。**誤認の側は形の I-9 型と違って測る道具が無い**(狙いには I-9 に当たる不変条件が無い)。これは次に要るものとして記録する。**したがってこの節と以後の報告に出る狙いの数は、「沈黙が減った」であって「正しく認識した」ではない**(2026-09-25 司令塔の指示)。例えば端攻め(9筋・1筋)は 2 つのシグネチャがそろって matched になるが、そろったからといって相手が端攻めを狙っていたとは言えない ― 端の歩を 2 つ突いただけの局でも成立する。誤認の物差し(狙いの I-9 に当たるもの)は開発・診断レーンへの依頼として司令塔へ上げた。

**埋まった数**: 狙いの目録 13 / 67(既存 8 + 新 5)。**書けない 52 件は分母に入れたまま**にしている(名前はあるがスキーマで表せないため、分母から外すと「網羅した」に見えてしまう)。

## 17. 第 14 組(2026-09-25): 狙い 5 件 ― **証拠 2 件以上の沈黙は動かなかった(床に当たった)**

**足した ID(すべて `draft`・`side: opponent`、置き場 `data/drafts/2026-09-25-knowledge/intents/`)**: `gyokuto_kuraidori`(玉頭位取り)・`gosuji_kuraidori_opponent`(5筋位取り)・`chikatetsu_bisha`(地下鉄飛車)・`suzumesashi_opponent`(雀刺し、low)・`boukin_opponent`(棒金、low)。**スキーマ検証 18 件 OK**(既存 8 + 第 13 組 5 + 今回 5 を同じフォルダに集めて `scripts/validate-data.mjs`)。

**出典**(いずれも Wikipedia、参照日 2026-09-25。文は写さず要点だけを自分の言葉で書いた): 玉頭位取り(振り飛車に対して銀を 7六 に置き 7筋 の位を取る居飛車の戦法)・5筋位取り(5五 の位を取り 5六 に銀を置く)・地下鉄飛車(飛車を 1段目 に引いてから端の香を上げ、9筋 へ飛車を回す)・雀刺し(1筋 に香・飛・桂を集めて 1三 の一点を破る)・棒金(石田流やひねり飛車に対し金を 3八→2七→2六 と前へ出し、相手の飛車と角の動ける範囲を狭める)。**出典はすべて先手(居飛車)側の座標で述べているので、後手の座標へ盤ごと 180 度回して写した**(筋 f → 10−f、段 r → 10−r)。写した式は各レコードの `source` に書いてある。

**保留 1 件: 6筋位取り。** 出典(Wikipedia『6筋位取り』)が述べる ▲6六歩 を後手へ写すと 4四歩 になるが、**これは 70 局中 40 局に現れる普通の手**で、これだけを手がかりにすると常に立ってしまう。位のマスが 4五 か 4四 かも出典から読めない。目録には「出典あり・保留(手が普通すぎて区別にならない)」として残す。

**測った数**(形は第 7 組の 45 件で固定し、**狙いだけを 13 件 → 18 件に増やした**。前後で同じ棋譜・同じ道具):

| 範囲 | 狙いだけの沈黙(証拠 2 件以上か matched) | 狙いだけの沈黙(証拠 1 件で立つ版) | 分母(先手番の局面) |
|---|---|---|---|
| 30 手まで | 620 → **620**(変わらず) | 241 → **228**(−13) | 1096 |
| 全手 | 755 → **755**(変わらず) | 241 → **228**(−13) | 2735 |

**読み方**: **見出しの数(証拠 2 件以上)は 1 も動かなかった。** 新しい 5 件が 2 件目のシグネチャに届くのは遅く、そこまで来た局面では既存の狙いがもう立っている。つまり**狙いも、形と同じように床に当たった**(形は 35 件で下げ止まった。§3〜§5)。残った 755 局面がどこにあるかを ply ごとに数えると、床の中身がはっきりする。

| ply | 0 | 2 | 4 | 6 | 8 | 10 | 12〜20 | 22〜30 | 32 以降 |
|---|---|---|---|---|---|---|---|---|---|
| 沈黙 | 70 | 69 | 60 | 51 | 51 | 49 | 167 | 103 | 135 |
| 局面 | 70 | 70 | 70 | 70 | 70 | 70 | 343 | 333 | 1639 |

**残った沈黙の 6 割(755 のうち 471)は 20 手目まで**にある。**開始直後は、相手がまだ 2 手しか指していないので、駒種と移動先が 2 つそろうことが原理的に少ない。** ply 0 の 70 局面(沈黙率 100%)は相手が 1 手も指していない局面で、**どんな語彙を足しても埋まらない**(形の 居玉 と同じ型の床)。32 手以降は 1639 局面中 135(8%)まで下がっていて、ここは語彙の不足ではない。したがって**序盤の沈黙を埋めたいなら、狙いのレコードを増やすのではなく「シグネチャ 1 つで立つ狙いを、控えめな言い方で見せてよいか」の判断**(露出制御の側、このレーンの持ち物ではない)になる。

**狙いごとの当たり方(4 人 70 局、全手。1 回以上その段階に達した局数)**:

| 狙い | 証拠 1 件以上 | 証拠 2 件以上 | 全部そろった | シグネチャ数 |
|---|---|---|---|---|
| `hashizeme_1suji` 端攻め(1筋) | 35 | 15 | 15 | 2 |
| `hashizeme_9suji` 端攻め(9筋) | 32 | 15 | 15 | 2 |
| `gyokutogin` 玉頭銀 | 29 | 9 | 3 | 3 |
| `gyokuto_kuraidori` 玉頭位取り(新) | 26 | 3 | 3 | 2 |
| `gosuji_kuraidori_opponent` 5筋位取り(新) | 40 | 7 | 7 | 2 |
| `boukin_opponent` 棒金(新) | 14 | 1 | 1 | 3 |
| `suzumesashi_opponent` 雀刺し(新) | 8 | 0 | 0 | 3 |
| `chikatetsu_bisha` 地下鉄飛車(新) | 6 | 1 | 1 | 2 |
| `kakukoukan` 角交換 | 16 | ― | 16 | 1 |
| `hashikaku` 端角 | 6 | ― | 6 | 1 |
| (既存で多い順)`naname_bogin` | 48 | 21 | 5 | 3 |
| `hishasaki_fugokan` | 45 | 32 | 19 | 3 |
| `nakabisha_kuraidori` | 43 | 14 | 2 | 3 |
| `hayajikake` | 34 | 22 | 22 | 2 |

**重なりを承知で入れたもの**: 5筋位取り の 5五歩 は既存 `nakabisha_kuraidori` にも、5四銀 は `gyokutogin` にもある。玉頭位取り の 3五歩 は `hisha_3suji_tenkan` にもある。**同じ 1 手で 2〜3 件が同時に立つ**(どれも「その筋の高さを取る」形なので狙いとしては近い)。1 手で複数が立つこと自体は 2026-09-25 の開発・診断レーンが指摘済みの性質で、**見出しを証拠 2 件以上にしている理由**でもある。

**この数が言わないこと**(§16 と同じ縛り): 「当たった」は**沈黙が減ったこと**を意味するだけで、**相手が本当にその狙いを持っていたことではない。** 5筋位取り が証拠 1 件で 40 局に立つのは、5四歩 か 5五歩 か 5四銀 がただ指されただけの局を含むからである。**狙いの誤認を測る道具は無い**(形の I-9 型に当たるものが無い)。

**埋まった数**: 狙いの目録 **18 / 67**(既存 8 + 第 13 組 5 + 今回 5)。**書けない 52 件は分母に入れたまま**。囲い 35 / 62(うち相手側 10 件は別立て)・戦法 55 / 184。

## 18. 第 15 組(2026-09-25): 相手側の形 10 件 ― 相手側の沈黙 731 → 600(30 手まで)

**足した ID(すべて `draft`・`side: opponent`)**: `mino_kinmino_opponent`・`mino_diamond_opponent`・`mino_hayagakoi_opponent`・`kanigakoi_opponent`・`yagura_katayagura_opponent`・`yagura_ginyagura_opponent`・`yagura_souyagura_opponent`・`nakazumai_opponent`・`hakoirimusume_opponent`・`kabegakoi_opponent`。**選び方は司令塔の指示(2026-09-25)どおり、当たった系統(片美濃・本美濃・舟囲い・金無双)に近いものから**(美濃系 3 件)、次に相手が居飛車のときによく使う囲い(カニ・矢倉 3 種・中住まい・箱入り娘・壁)。

**作り方**: 自分側の同じレコードを**盤ごと 180 度回して写した**(筋 f → 10−f、段 r → 10−r)。写像は各レコードの `source` に書いた。出典は自分側のレコードのものをそのまま指し、**出典そのものが後手の座標を述べているわけではない**ことも書いた。**スキーマ検証 55 件 OK**(`data/shapes` 3 + 下書き 52 を同じフォルダに集めて `scripts/validate-data.mjs`)。

**測った数**(狙いは第 14 組の 18 件で固定。形を 45 件 → 55 件。司令塔の指定どおり**相手側の I-9 型は相手側だけで数え、自分側と混ぜていない**):

| 範囲 | 相手側の沈黙(証拠 2 件以上か完成) | 相手側の I-9 型 | 自分側の認識(不変のはず) | 分母 |
|---|---|---|---|---|
| 30 手まで | 731 → **600**(−131) | 2091 → **4745**(+2654) | 318 → **318**(不変) | 1096 |
| 全手 | 1438 → **1069**(−369) | 6384 → **14100**(+7716) | 1499 → **1499**(不変) | 2735 |

**読み方**: **相手側はまだ動く。** 30 手までで相手側の認識が 365 → 496 局面(+131)、全手で 1297 → 1666(+369)。**自分側は 1 も動いていない**(318 / 1499)ので、写した 10 件が自分側の判定に混ざっていないことも確かめられた。形全体の沈黙(自分側か相手側のどちらかが立てば沈黙でない)も 573 → 488(30 手まで)・844 → 677(全手)と下がった。

**ただし I-9 型の増え方が第 7 組より悪い。** 第 7 組(最初の相手側 10 件)は沈黙 −365 に対し I-9 型 +2091 で、**1 局面あたり 5.7 件**の「証拠の無い主張」だった。今回は −131 に対し +2654 で **1 局面あたり 20 件**。相手側も**次の組で止め時に近づく**見込みである(止め時の目安は司令塔の指示で「証拠 2 件以上の沈黙が動かず、I-9 型だけ増える」)。

**写した 10 件の当たり方(4 人 70 局、全手)**:

| 相手側の形 | 完成した局数 | 75% 以上そろった局数 |
|---|---|---|
| `hakoirimusume_opponent` 箱入り娘 | 0 | 9 |
| `kanigakoi_opponent` カニ囲い | 1 | 7 |
| `mino_diamond_opponent` ダイヤモンド美濃 | 0 | 5 |
| `yagura_ginyagura_opponent` 銀矢倉 | 0 | 5 |
| `yagura_katayagura_opponent` 片矢倉 | 0 | 4 |
| `mino_hayagakoi_opponent` 早囲い | 2 | 2 |
| `yagura_souyagura_opponent` 総矢倉 | 0 | 2 |
| `mino_kinmino_opponent` 金美濃 | 0 | 0 |
| `nakazumai_opponent` 中住まい | 0 | 0 |
| `kabegakoi_opponent` 壁囲い | 0 | 0 |

**完成はほとんど出ない(10 件で 3 局)。** 沈黙を下げているのは「75% 以上そろった」や証拠 2 件の段階であって、**相手が本当にその囲いに組み切った局はまれ**である。金美濃・中住まい・壁囲いは 1 局も 75% に届かなかったので、**次に写す分の優先は下げる**(壁囲いはそもそも「囲い損ねた形」なので、相手側で名前を出す意味も薄い)。

**この数が言わないこと**: 相手側の「認識できた」は**盤の駒の位置が一致したこと**であって、相手がその囲いを目指していたことではない。**相手側の I-9 型が 14100 件ある**ということは、全手で見ると 1 局面あたり 5 件以上の「証拠 1 件以下で欠けマス 2 つ以上」の主張が同時に立っているということで、**このまま画面に出す形ではない**(露出制御はコードの側の持ち物)。

**埋まった数**: 囲いの目録 35 / 62(**自分側 35・相手側 20**。相手側は目録の別立てで、35 件のうち 20 件を写し終えた)・戦法 55 / 184・狙い 18 / 67。

## 19. 第 16 組(2026-09-25): 相手側の形 残り 15 件 ― **床に当たった。相手側は打ち止め**

**足した ID(すべて `draft`・`side: opponent`)**: 穴熊系 4(`anaguma_matsuo`・`anaguma_ginkanmuri`・`anaguma_big4`・`yagura_anaguma`)・矢倉系 3(`yagura_kikusui`・`yagura_hishi`・`yagura_doi`)・雁木系 2(`gangi_nimaigin`・`gangi_tsunogin`)・その他 6(`kinbiraki`・`mutekigakoi`・`bonanzagakoi`・`ahirugakoi`・`nakaharagakoi`・`ichigogakoi`)、いずれも `_opponent` を付けた ID。**これで相手側は自分側と同じ 35 件すべてが揃った**(人間の決定 2026-09-25「網羅」に沿って、当たりにくい形も含めて写した)。作り方・出典の扱いは第 15 組と同じ(180 度回して写し、式を `source` に書く)。**スキーマ検証 70 件 OK**。

**測った数**(狙いは 18 件で固定。形を 55 件 → 70 件):

| 範囲 | 相手側の沈黙 | 相手側の I-9 型 | 自分側の認識 | 形全体の沈黙 | 分母 |
|---|---|---|---|---|---|
| 30 手まで | 600 → **554**(−46) | 4745 → **9520**(+4775) | 318 → **318**(不変) | 488 → 459 | 1096 |
| 全手 | 1069 → **931**(−138) | 14100 → **28198**(+14098) | 1499 → **1499**(不変) | 677 → 624 | 2735 |

**止め時の判定(司令塔の目安「証拠 2 件以上の沈黙が動かず、I-9 型だけ増える」)**: 沈黙 1 局面あたりの I-9 型は **5.7 件(第 7 組)→ 20 件(第 15 組)→ 104 件(今回)**。**沈黙はまだ少し動くが、代償が 1 桁ずつ増えている。相手側はここで打ち止めにする。**

**新しく見つかった誤認の型(これが今回いちばん大事)**: `mutekigakoi_opponent`(無敵囲い)が **70 局中 33 局で 75% 以上そろった**。中身を見ると、必要な駒 6 枚のうち **玉5a・金4a・金6a の 3 枚が後手の初期配置そのまま**である。つまり**相手が玉も金も動かしていない局面で、すでに半分そろっている**。`ichigogakoi_opponent`(一夜囲い、14 局)も銀3a が初期配置。**「定義が初期配置と重なるレコードは、相手が何もしていない局面で当たる」** ― これは I-9 型(証拠 1 件以下で欠けマス 2 つ以上)とは別の型で、**証拠が 2 件以上あっても起きる**(初期配置の駒は「動いた証拠」が無いのに一致する)。既存の不変条件では捕まらないので、**開発・診断レーンへの依頼として上げ、****P-85 として採番・登録された**(docs/PHASES.md の表。2026-09-25、開発・診断レーンからの連絡。状態は未着手で、判定側で扱うかは OBS-3 の後の候補 = 判断的なので監査つき)。とりあえずこのレーンでは、**無敵囲い・一夜囲いの相手側 2 件に「初期配置と重なるため当たりやすい」ことを記録に残す**(レコードは消さない。消すと網羅の数が合わなくなるうえ、問題は定義ではなく判定側の扱いにある)。

**写した 15 件の当たり方(4 人 70 局、全手。完成 / 75% 以上)**: 無敵囲い 1 / 33、一夜囲い 1 / 14、土居矢倉 0 / 4、ボナンザ囲い 1 / 4、角銀雁木 0 / 3、金開き 2 / 2、菊水矢倉 0 / 2、菱矢倉 0 / 1、二枚銀雁木 0 / 1。**穴熊系 4 件・アヒル囲い・中原囲いは 1 局も 75% に届かなかった**(相手が 70 局で穴熊に組んだ局は無い)。

**埋まった数**: 囲いの目録 **自分側 35 / 62・相手側 35 / 35(完了)**・戦法 55 / 184・狙い 18 / 67。**次は戦法の残り(出典あり約 90 件)に戻る**(司令塔の指示 3。認識のコードが無いので測れないまま増えることになり、報告は 3 行に縮める)。

## 20. 第 17 組(2026-09-25): 戦法 9 件 ― **測れない(認識のコードが無い)**

**足した ID(すべて `draft`・`side: self`、置き場 `data/drafts/2026-09-25-knowledge/openings/`)**: `gangi_senpou`(雁木戦法)・`hayakurigin`(早繰り銀)・`aigakari_bogin`(相掛かり棒銀)・`aigakari_koshikakegin`(相掛かり腰掛け銀)・`ufo_gin`(UFO銀、low)・`yagura_nakabisha`(矢倉中飛車、low)・`tatefudori`(縦歩取り)・`ninja_gin`(忍者銀、low)・`kintachi`(金立ち戦法、low)。出典はすべて Wikipedia の個別ページ(参照日 2026-09-25。文は写さず要点だけ自分の言葉で `source` に書いた)。**目録の 9 行を「未」から「下書き済み」に更新した。**

**測れない**: 戦型を認識するコードは `apps/server/src/analysis/` に無いので、**沈黙率も誤認も動かない**(2026-09-25 司令塔の訂正)。代わりに次の 2 つを確かめた。**スキーマ検証 68 件 OK**(`data/openings` 3 + 下書き 65)。**本体へ移すときの門も通した** ― Kind 3 の口 `loadApprovedScenarioVariants` に同じ 68 件のフォルダを読ませて**例外なし・承認済み変化 0 件**(全レコードの `scenario` が `null` なので 0 件が正しい)。

**出典から座標が読めた範囲だけを書いた**: 早繰り銀は出典が銀の全行程(3九→4八→3七→4六)を述べていないので、出典が挙げた 4六銀 と 3五歩 だけを `recognition_pattern` に置いた。UFO銀・金立ち戦法・忍者銀・矢倉中飛車は出典が挙げるマスが 1〜2 個しかないため `confidence_level` を low にした。

**重なりの記録**: 相掛かり腰掛け銀の銀の位置(5六)は既存の `koshikakegin`・`kakugawari_koshikakegin` と同じである。**戦型は認識に使われないので実害は無いが、将来コードを付けるときに区別が要る。** 今回は相掛かりであることを示す 2六飛 を先に置いて区別した。

**保留**: 木村定跡(目録 #36)は手順の名前(定跡)で、駒の配置として書けないため「未」のまま残した。

**埋まった数**: 戦法 **64 / 184**・囲い 自分側 35 / 62・相手側 35 / 35・狙い 18 / 67。

## 21. 第 18 組(2026-09-25): 戦法 8 件 ― **測れない(認識のコードが無い)**

**足した ID(すべて `draft`・`side: self`)**: `sodebisha`(袖飛車)・`genshi_bogin`(原始棒銀)・`migigyoku`(右玉、low)・`hikikaku`(引き角)・`nimaigin`(二枚銀)・`shirokugin_migi`(4六銀右戦法)・`shiroku_kin`(4六金戦法)・`ponpon_kei`(ポンポン桂、low)。出典はすべて Wikipedia の個別ページ(参照日 2026-09-25、要点だけ自分の言葉で `source` に)。**スキーマ検証 76 件 OK**・**Kind 3 の口で例外なし・承認済み変化 0 件**。**測れない**(戦型の認識コードが無い)。

**同じマスが重なる組み合わせを 4 つ見つけたので、区別できるところまで書いた**。戦型は認識に使われないので今は実害が無いが、**将来コードを付けるときにそのままでは区別できない**ので記録に残す。

| 重なる 2 件 | 同じマス | どこで区別したか |
|---|---|---|
| `genshi_bogin` / `aigakari_bogin` | 銀 2七・2六 | 原始棒銀は銀を 2五 まで出す(UFO銀の項の記述から) |
| `nimaigin` / `gangi_senpou` | 銀 5七・6七 | 出典が述べる舟囲い(玉 7八)を先に置いた。違いは本来は飛車と玉の側にある |
| `shirokugin_migi` / `hayakurigin` | 銀 4六・歩 3五 | 同じく舟囲い(玉 7八)を先に置いた |
| `shiroku_kin` / `kintachi` | 金 5七 | 4六金戦法は金を 4六 まで出す |

**目録の更新**: 上の 8 行を「未」→「下書き済み」に。あわせて、**第 14 組で狙いとして書いた 3 件(玉頭位取り・5筋位取り・地下鉄飛車)も戦法の目録に行があった**ので、「下書き済み(狙い側、相手側)」に更新した(戦法としてのレコードは作っていない。同じ名前が形・戦型・狙いのどこに置かれるかは 1 つに決まらない、という例として残す)。

**埋まった数**: 戦法 **75 / 184**・囲い 自分側 35 / 62・相手側 35 / 35・狙い 18 / 67。

## 22. 第 19 組(2026-09-25): 戦法 5 件 + 保留 3 件 ― **測れない(認識のコードが無い)**

**足した ID**: `yagura_37kei`(矢倉3七桂)・`yontekaku`(四手角)・`muriyari_yagura`(無理矢理矢倉。**ウソ矢倉は同じ記事の別名**)・`akutsu_kyusen_yagura`(阿久津流急戦矢倉。**出典が「後手の急戦戦法」と述べているので `side: opponent`**)・`yagura_35fu_hayajikake`(矢倉3五歩早仕掛け)。出典はすべて Wikipedia の個別ページ(参照日 2026-09-25)。**スキーマ検証 81 件 OK**・**Kind 3 の口で例外なし・承認済み変化 0 件**。

**保留 3 件(理由つきで目録に残した)**:

| 名前 | 保留の理由 |
|---|---|
| 飛車先不突矢倉 | **定義が「2六歩を突かない」という否定で、スキーマで表せない。** `recognition_pattern` は「この駒がここに来た」しか書けない。出典が代わりに挙げる ▲4八銀・▲5六歩 を置くと、それを指しただけの局に当たってしまう |
| 中原流急戦矢倉 | 出典 URL が矢倉囲いの一般説明に転送され、この戦法固有の駒組みが読めない |
| 6二飛戦法 | 出典 URL が戦法の一般説明に転送され、固有の駒組みが読めない |

**重なりの追記(第 18 組の表の続き)**: `yontekaku` の途中の 7九 は `hikikaku`(引き角)と同じマスで、四手角は 2六 まで進む点で区別する。`yagura_35fu_hayajikake` の 3六銀 は `ufo_gin` と同じマスで、こちらは 3五歩 を伴う。

**目録の更新**: 9 行(下書き 6・保留 3)。**目録に「四手角」の行が 2 つある**(矢倉の指し方と対振り急戦)が、出典は同じ記事なので 1 レコードにした。

**埋まった数**: 戦法 **84 / 184**(うち保留は 6 件)・囲い 自分側 35 / 62・相手側 35 / 35・狙い 18 / 67。

## 23. 第 20 組(2026-09-25): 戦法 8 件 + 保留 1 件 ― **測れない(認識のコードが無い)**

**足した ID**: 横歩取り 6 件 `yokofudori_33kaku`・`yokofudori_33kei`・`yokofudori_23fu`(low)・`yokofudori_45kaku`・`yokofudori_44kaku`(low)・`ai_yokofudori`、および `ikken_bisha`(一間飛車、low)・`ureshino`(嬉野流)。出典はすべて Wikipedia の個別ページ(参照日 2026-09-25)。**スキーマ検証 89 件 OK**・**Kind 3 の口で例外なし・承認済み変化 0 件**。

**横歩取りの 6 件はすべて `side: opponent`(後手)である。** 横歩取りは「先手が横歩を取ったあと、後手がどう応じるか」に名前が付いているものが多く、名前のマス(3三・2三・4五・4四・7六)はすべて後手の指し手である。**戦型の下書きで相手側が 6 件まとまって出たのはここが初めて**で、`side` は出典の「後手番の戦法」という記述からそのまま決めた。

**保留 1 件**: ノーガード戦法。**定義の核が「左金(3二金)を上がらない」という否定**で、飛車先不突矢倉(第 19 組)と同じ型である。残る特徴の △3三角 を書くと `yokofudori_33kaku` と同じマスになり区別できない。**否定で定義される戦型は、いまのスキーマでは 2 件目も書けなかった。**

**別名が 1 件解けた**: 出典(『横歩取り3三角』)が「横歩取り空中戦法」「内藤流」とも呼ばれると述べていたので、目録の「空中戦法(内藤流)」の行(出典なしだった)を `yokofudori_33kaku` の別名として埋めた。**出典なしの行が、別の行の出典で埋まることがある。**

**重なりの追記**: `ureshino` の 7九角 は `hikikaku`・`yontekaku` と同じマスで、初手の 6八銀 で区別する。`yokofudori_33kei` の 3三 は `yokofudori_33kaku` と同じマスで、駒種(桂と角)で区別する。

**埋まった数**: 戦法 **94 / 184**(うち保留 7 件)・囲い 自分側 35 / 62・相手側 35 / 35・狙い 18 / 67。**戦法は目録の半分を越えた。**

## 24. 第 21 組(2026-09-25): 戦法 7 件 + 保留 2 件 ― **測れない(認識のコードが無い)**

**足した ID**: `ibisha_anaguma_senpo`(居飛車穴熊)・`hidarimino_senpo`(左美濃)・`rokusuji_kuraidori`(6筋位取り、相手側・low)・`iijima_hikikaku`(飯島流引き角戦法)・`tonari_ryu`(都成流、相手側)・`gyokutogin_senpo`(玉頭銀)・`hidarigyoku`(左玉、low)。出典は Wikipedia の個別ページ(参照日 2026-09-25)。左美濃だけは将棋ジムの囲いページも併用した。**スキーマ検証 96 件 OK**・**Kind 3 の口で例外なし・承認済み変化 0 件**。

**保留 2 件 ― どちらも「スキーマで表せない」の新しい型**:

| 名前 | 保留の理由 |
|---|---|
| 角交換振り飛車 | **定義の核が角交換、つまり盤上から駒が消えること。** `recognition_pattern` は「この駒がここに来た」しか書けない(取る・打つ・成るを区別できない、は §5 の 13 件でも出た型) |
| 陽動振り飛車 | **定義が「いつ飛車を振るか」というタイミング。** 相居飛車の形から途中で振り飛車へ転じることが本体で、スキーマは手順の前後(どちらが先か)を表せない |

**第 14 組で見送った 6筋位取りを、戦型としては書いた。** 狙い(`data/intents`)としては「出典の ▲6六歩 を写した 4四歩 が 70 局中 40 局に出る普通の手で区別にならない」ため見送ったが、**戦型は認識に使われないので、区別にならないことを `source` に明記したうえでレコードにした**。同じ名前が、狙いとしては書けず戦型としては書ける例である。

**同じ名前が別の種類にもある例が 2 件目**: 玉頭銀は、自分側(先手)の戦型として 5六-4五-3四(この組)、相手側(後手)の狙いとして 5四-6五-7六(`data/intents` の `gyokutogin`、第 13 組)の 2 つのレコードになった。**同じ将棋用語が、どちら側から見るかで別のレコードになる**ことを記録に残す。

**左美濃の出典から囲いの座標も 3 つ取れた**(玉8八・銀7八 = 左美濃、玉8七 = 天守閣美濃、銀8七・金7八 = 居飛車銀冠)。**囲いの目録の「居飛車銀冠」の行(未)はこれで埋められる**が、囲いは測れる側なので、次に囲いをまとめて足すときに測定つきで入れる。

**埋まった数**: 戦法 **103 / 184**(うち保留 9 件)・囲い 自分側 35 / 62・相手側 35 / 35・狙い 18 / 67。

## 25. 第 22 組(2026-09-25): 戦法 6 件 + 保留 4 件 ― **測れない(認識のコードが無い)**

**足した ID**: `henachoko_kyusen`(へなちょこ急戦)・`kato_sodebisha`(加藤流袖飛車)・`sanhachi_bisha`(3八飛戦法)・`sanpo_tsukisute`(三歩突き捨て急戦、相手側)・`sansan_kaku_senpo`(3三角戦法、相手側・low)・`ikken_bisha_anaguma`(一間飛車穴熊)。出典は Wikipedia の個別ページ(参照日 2026-09-25)。**スキーマ検証 102 件 OK**・**Kind 3 の口で例外なし・承認済み変化 0 件**。

**保留 4 件 ― ここから先は「出典の側の問題」が増える**:

| 名前 | 保留の理由 |
|---|---|
| 丸山ワクチン | 出典が曖昧さ回避ページで、固有の定義も座標も無い |
| 三間飛車破り | 出典が複数の指し方の総称で、固有の配置が無い |
| 居飛車舟囲い急戦 | 同じく総称。**下位にあたる 4六銀右戦法・4六金戦法・二枚銀・三歩突き捨て急戦はすべて下書き済み**なので、親の行としては埋めない |
| 4七銀型 | 出典 URL がゴキゲン中飛車の記事に転送され、この型固有の駒組みが読めない |

**同じマスの重なりが 3 件に増えた例**: `sodebisha`(袖飛車)・`kato_sodebisha`(加藤流袖飛車)・`sanhachi_bisha`(3八飛戦法)は**3 件とも飛車が 3八**である。区別は加藤流が 5七銀 + 3五歩、3八飛戦法が 4七銀。**名前が 3 つあっても、盤の上の違いは銀 1 枚の位置しかない。**

**機械では区別できない 2 件を、区別できないと書いた**: `sansan_kaku_senpo`(3三角戦法)と `yokofudori_33kaku`(横歩取り3三角)は、どちらも後手の 3三角 である。違いは「横歩取りの局面かどうか」で、**いまのスキーマは『どの局面でその手が出たか』を書けない**(手順の前後を表せない、と同じ型)。片方を消すのではなく、両方の `source` に「機械では区別できない」と書いた。

**埋まった数**: 戦法 **113 / 184**(うち保留 13 件)・囲い 自分側 35 / 62・相手側 35 / 35・狙い 18 / 67。

## 26. 第 23 組(2026-09-25): 戦法 5 件 + 保留 3 件 + 既存 1 件の直し

**足した ID**: `takada_ryu_hidarigyoku`(高田流左玉)・`eichanryu_nakabisha`(英ちゃん流中飛車、low)・`hirame`(平目)・`yagura_ryu_nakabisha`(矢倉流中飛車、相手側・low)・`onirokuryu_dokkan`(鬼六流ドッカン飛車)。出典は Wikipedia の個別ページ(参照日 2026-09-25)。**スキーマ検証 107 件 OK**・**Kind 3 の口で例外なし・承認済み変化 0 件**。**測れない**(戦型の認識コードが無い)。

**既存 1 件を直した(`hidarigyoku`)**。同じ記事(『左玉』)を 2 度読んだところ、**金の位置が 7八 とも 3八 とも読めた**ので、金を外して 8八飛・7八玉 の 2 件にした。玉は出典が 7八 か 7九 の 2 通りを挙げており、2 度目の読みが 7八 だったので 7八 を採った。**同じページを 2 度読むと違う座標が出ることがある**ので、1 度の読みで座標を確定しないほうがよい(この組で得た教訓)。飛車 8九・銀 6七/5七 まで含む型は `takada_ryu_hidarigyoku` として別レコードにした。

**否定で定義される戦型の 3 例目**: 英ちゃん流中飛車の骨格は「**5筋の歩を突かない**」ことである(飛車先不突矢倉・ノーガード戦法と同じ型)。図から読める 5八飛・6八銀 だけを書いたが、**それでは普通の中飛車と区別できない**ので `source` にそう明記した。

**保留 3 件**: 室岡システム(出典の要点が △6二金 の 1 手だけで、囲いの普通の手と区別にならない。先後の記述も混ざる)・角交換相振り飛車(角交換 = 盤上から駒が消える。飛車の筋も 3 通りで定まらない)・振り飛車(総称。到達マスが定まらない。下位は個別に下書き済み)。

**順番が意味を持つ数少ない例**: `onirokuryu_dokkan` は 5八飛 → 3八金 → 2八玉 → 8八飛 と**飛車を 2 度振る**。`order_hint` には入れたが、**判定側(`intentDetector`)は順不同で見る**ので、この順番は今のところ使われない。

**埋まった数**: 戦法 **121 / 184**(うち保留 16 件)・囲い 自分側 35 / 62・相手側 35 / 35・狙い 18 / 67。**出典に個別ページがあって未のものは残り 16 件。**

## 27. 第 24 組(2026-09-25): 戦法 5 件 + 保留 4 件 ― **出典どうしの食い違いを 1 件見つけた**

**足した ID**: `nitemme_32hi`(2手目△3二飛、相手側・low)・`yonyonfu_pacman`(4四歩パックマン、相手側・low)・`kakutoufu`(角頭歩戦法)・`kanazawaryu`(金沢流)・`ahiru_senpo`(アヒル戦法)。**スキーマ検証 112 件 OK**・**Kind 3 の口で例外なし・承認済み変化 0 件**。**測れない**(戦型の認識コードが無い)。

**出典どうしの食い違い(司令塔の指示「2 度読んで一致したものだけ」を初めて適用した)**: アヒル戦法は、Wikipedia が銀を **3八・7八**、既存の囲い `ahirugakoi` が使った将棋ジムの手順が **4八・6八** と述べる。**一致したのは 玉5八・金7九・金3九 の 3 件だけ**だったので、戦型のレコードにはその 3 件だけを置き、銀を入れなかった。

**2 度目の読みで確かめ直す対象(測れる側)**: 囲い `ahirugakoi` の銀 2 枚(4八・6八)。**この 1 件が、いま分かっている「2 度目の読みが要る囲い」のすべて**である(他の囲いは出典が 1 つしかなく、まだ 2 度目を読んでいない)。実測では `ahirugakoi_opponent` は 70 局で完成 0・75% 以上 0 だったので、**この食い違いは測った数には影響していない**。

**保留 4 件 ― すべて「出典 URL が親の記事に転送される」型**: 新石田流・楠本式石田流(→ 石田流。本体は既存の `ishidaryu`)・新鬼殺し(→ 鬼殺し。本体は既存の `onikoroshi`)・鬼殺し向かい飛車(→ 向かい飛車)。**名前は別でも、出典が親の記事しか持たないものは書けない。**

**「何手目か」が書けない例が 2 件**: 2手目△3二飛(2 手目であることが名前の本体)・4四歩パックマン(2 手目に突くことが本体)。どちらも残る 1 手は普通の手で、**機械では普通の三間飛車・普通の 4四歩 と区別できない**。

**埋まった数**: 戦法 **130 / 184**(うち保留 20 件)・囲い 自分側 35 / 62・相手側 35 / 35・狙い 18 / 67。**出典に個別ページがあって未のものは残り 7 件**(木村定跡・村田システム・横歩取り(対中飛車)・カメレオン戦法・新米長玉・珍玉・英春流)。

## 28. 第 25 組(2026-09-25): 戦法 2 件 + 保留 5 件 + 名前だけの 40 行 ― **戦法はここで一区切り**

**足した ID**: `kamereon_senpo`(カメレオン戦法)・`eishunryu`(英春流)。**どちらも司令塔の指示どおり、同じページを 2 度、違う問いで読み、一致した駒だけを置いた**(カメレオン = 6七銀・6五歩 の 2 件、英春流 = 4八銀・5六歩・5七銀 の 3 件)。**スキーマ検証 114 件 OK**・**Kind 3 の口で例外なし・承認済み変化 0 件**。**測れない**。

**保留 5 件 ― 最後まで残ったのは「書けない理由」がはっきりしたものだった**:

| 名前 | 保留の理由 | 型 |
|---|---|---|
| 木村定跡 | 手順(定跡)の名前で、駒の配置として書けない | 手順 |
| 村田システム | 2 度の読みが一致したのは 5六歩 の 1 手だけ。定義の核「角道を開けず」は否定 | 否定 + 1 手 |
| 新米長玉 | 同じページに米長玉と新米長玉があり、読み方で違う座標が出る。本体は「2 手目に指すこと」 | 何手目か |
| 珍玉 | 珍しい玉の位置の総称で座標が定まらない | 総称 |
| 横歩取り (対中飛車) | **自分側の指し手は普通の横歩取りと同じで、違いは「相手が中飛車であること」** | **相手の形を条件にできない** |

**最後の 1 件は新しい型である**。`recognition_pattern` は自分(または相手)の指し手しか書けないので、「**相手がこういう形のときの、この指し方**」という名前は表せない。対抗型の戦法名にはこの型が多いはずで、**いま書けている戦型も、相手の形を前提にしている限り名前としては半分しか表せていない**。

**名前だけの 40 行をまとめて保留にした**。個別ページが無く、一覧(Wikipedia のカテゴリ)に名前があるだけの行は、**駒の配置を起こす材料が無い**ので埋められない。消さずに「保留(一覧に名前があるだけ)」として残す。**網羅の分母を減らさない**ため。

**戦法の最終の数(表を数え直した)**: 目録は **185 行**(「四手角」が 2 行あるため、これまで 184 と書いていたのは数え違い)。内訳は **下書き 112 行・保留 68 行・既存または対象外 5 行・未 0 行**(対象外 = 駒落ちの戦法。既存 = すでに `data/` にある 4 件)。**下書きのファイル数は 111 件**で、行数と一致しない。別名の 3 組(無理矢理矢倉／ウソ矢倉、空中戦法／横歩取り3三角、四手角の 2 行)は 2 行で 1 レコードを共有し、逆に目録に行の無いレコード(相手側に写した `*_opponent` など)もあるためで、**目録の行と `data/drafts` のファイルは 1 対 1 ではない**。個別ページのある行はすべて埋めたか、理由つきで保留にした。**ここで戦法は一区切りとし、次は囲い(測れる側)に戻る。**

**次の組(囲い 4 件、測定つき)**: 左美濃・天守閣美濃・居飛車銀冠の 3 件を足し、あわせて `ahirugakoi` の銀 2 枚(出典が食い違う)を外す直しを 1 件。測定は 4 件まとめて前後(証拠 2 件以上版・I-9 型・自分側/相手側を分けて)。司令塔の指示(2026-09-25)による。

## 29. 第 26 組(2026-09-25): 囲い 3 件 + 直し 1 件 ― **沈黙は動かず、証拠なしの主張が 273 件減った**

**足した ID**(すべて `draft`・`side: self`): `hidarimino`(左美濃)・`tenshukaku_mino`(天守閣美濃、low)・`ibisha_ginkanmuri`(居飛車銀冠)。**直した ID**: `ahirugakoi`(銀 2 枚を外した)。**スキーマ検証 73 件 OK**。

**出典と読み方**: 将棋ジム『左美濃』(https://shogi-gym.com/kakoi/mino/hidarimino/ 参照日 2026-09-25)。**司令塔の指示どおり、同じページを 2 度、違う問いで読み、一致した駒だけを required_pieces に入れた。** 一致したのは 左美濃 = 玉8八・銀7八、天守閣美濃 = 玉8七、居飛車銀冠 = 銀8七・金7八(玉8八 は 2 度目が明示・1 度目も発展形と述べる)。**1 度しか出てこなかった駒は入れないか optional にした**(左美濃の金 6八 は入れず、居飛車銀冠の金 6七 は optional)。天守閣美濃の銀 7八 だけは「左美濃の玉を 8七 に上げた形」という出典の説明から引き継いだ推測なので low。

**測った数**(狙いは 18 件で固定。形を 70 件 → 73 件、うち 1 件は required_pieces を減らす直し):

| 範囲 | 自分側の沈黙 | 自分側の I-9 型 | 相手側の沈黙 | 相手側の I-9 型 | 形全体の沈黙 |
|---|---|---|---|---|---|
| 30 手まで | 778 → **779**(+1) | 7215 → **6942**(−273) | 554 → 554(不変) | 9520 → 9520(不変) | 459 → 460 |
| 全手 | 1236 → **1232**(−4) | 25078 → **24795**(−283) | 931 → 931(不変) | 28198 → 28198(不変) | 624 → 628 |

**読み方 ― 沈黙は動かなかった。動いたのは誤認の側である。**

- **足した 3 件は沈黙をほとんど動かしていない**(全手で −4)。左美濃は 70 局中 4 局で完成し、居飛車銀冠も 1 局で完成しているので**当たってはいる**が、その局面は既に別の囲いで認識できていた。**自分側が 35 件で床に当たったという第 4 組の結論は、3 件足しても変わらない。**
- **直しの効果のほうが大きい**。`ahirugakoi` の required_pieces を 5 枚から 3 枚に減らしたことで、**証拠が 1 件以下で欠けマスが 2 つ以上ある主張(I-9 型)が 273 件(30 手まで)・283 件(全手)減った**。枚数が多いレコードは「まだほとんど揃っていないのに候補として立つ」局面を作る。**出典が食い違ったから駒を外した直しが、そのまま誤認を減らした。**
- 代償は沈黙が 30 手までで 1 局面、全手で形全体が 4 局面増えたこと(必要な駒が減ると、証拠として数えられる指し手も減るため)。**1 局面の沈黙と引き換えに 273 件の根拠なき主張が消えたので、この交換は割に合う。**
- 相手側は 1 も動いていない(554 / 9520 のまま)。直した `ahirugakoi` の相手側(`ahirugakoi_opponent`)は元々 70 局で完成 0・75% 以上 0 だったため。**なお相手側の写しは第 16 組のまま(銀 2 枚を含む古い定義)**で、次に相手側を触るときに合わせる必要がある(未処理として記録)。

**埋まった数**: 囲い 自分側 **38 / 62**・相手側 35 / 35・戦法 185 行(未 0)・狙い 18 / 67。

## 30. 第 27 組(2026-09-25): 相手側の `ahirugakoi_opponent` を自分側に合わせた直し 1 件

第 26 組で `ahirugakoi` の銀 2 枚を外したが、相手側の写しは古い定義(銀 4二・6二 を含む 5 枚)のままだった。**司令塔の指示(2026-09-25)により、相手側も 玉5一・金3一・金7一 の 3 枚に合わせた。** データの追加は無し。**スキーマ検証 73 件 OK**。

**測った数**(形 73 件のまま、required_pieces を 5 枚 → 3 枚に。狙いは 18 件で固定):

| 範囲 | 相手側の沈黙 | 相手側の I-9 型 | 自分側 |
|---|---|---|---|
| 30 手まで | 554 → **554**(不変) | 9520 → **9248**(−272) | 沈黙 779・I-9 6942 で不変 |
| 全手 | 931 → **947**(+16) | 28198 → **27804**(−394) | 沈黙 1232・I-9 24795 で不変 |

**「前後が同じ」ではなかったので、そのまま書く。** 30 手までは沈黙が動かなかったが、**全手では相手側の沈黙が 16 局面増えた**。銀 2 枚が required_pieces から消えたぶん、証拠として数えられる指し手も減り、終盤で「証拠 2 件以上」に届かなくなった局面があるためである(自分側で +4 だったのと同じ理屈で、相手側のほうが大きく出た)。**引き換えに証拠なしの主張が 272〜394 件減っている**ので、第 26 組と同じ交換として受け入れる。

**保留を 1 件足した(木村美濃)**。将棋ジムの木村美濃のページ(https://shogi-gym.com/kakoi/mino/kimuramino/ 参照日 2026-09-25)を 2 度読んだところ、**本文の座標が「5二」「6三」「7一」のように段が一〜三で、後手側の段だった**。同じサイトの左美濃・金美濃のページは先手の段(八・九)で書かれており、**ページによって図の向きが違う**。どちらの手番の図か確定できないので埋めない。**過去に「段だけを反転させて左右が入れ替わる」取り違え(P-12)が起きているので、向きが読めないものは書かない。**

**残りの囲いの行について**: 目録で未のまま残っているもの(富士見矢倉・へこみ矢倉・流れ矢倉・流線矢倉・角矢倉・三手囲い・中段玉・最強囲い など)は、**出典ページに座標の文が無い**(名前と概要だけ)。将棋ジムの個別ページがあるものは埋めたので、**残りは「人が図を読む工程」が要る**(司令塔が人間へ上げている判断の 1 つ)。

## 31. 整理(2026-09-25、待機中): 別名の統合と「スキーマで書けない型」の一覧

司令塔の指示(2026-09-25)により、床に当たって以降の待機中に記録を整理した。**`data/` は触っていない**(この節は文書だけ)。

### 31.1 別名の統合(目録の行と下書きファイルが 1 対 1 でない理由)

**行は消さない**(網羅の分母を変えないため)。同じ 1 レコードを指す行をここに集める。

| 目録の行(複数) | 1 つの下書き | 根拠 |
|---|---|---|
| 無理矢理矢倉 / ウソ矢倉 | `muriyari_yagura` | Wikipedia の同じ記事 |
| 横歩取り3三角 / 空中戦法(内藤流) | `yokofudori_33kaku` | 出典が「横歩取り空中戦法」「内藤流」とも呼ぶと述べている |
| 四手角(矢倉の指し方) / 四手角(対振り急戦) | `yontekaku` | 目録に同じ名前が 2 行ある(分類が違うだけ) |

**逆に、目録に行が無い下書き**もある: 相手側へ写した `*_opponent`(戦型 6 件・囲い 35 件)と、自分側として起こした `ibisha_self`・`nakabisha_self` 等。**目録は「名前の一覧」であって「レコードの一覧」ではない。**

### 31.2 スキーマで書けない型(6 つ。構造的知識 = 人間の承認事項なので、記録だけ)

`recognition_pattern`(駒種 + 到達マス)と `required_pieces`(駒種 + マス)は「**ある駒がこのマスに来た/ある**」しか書けない。そこから外れる定義を、出会った順に 6 つに整理する。

| # | 型 | 出会った例 | 記録した節 |
|---|---|---|---|
| 1 | **否定**(〜しない) | 飛車先不突矢倉(2六歩を突かない)・ノーガード戦法(3二金を上がらない)・英ちゃん流中飛車(5筋を突かない) | §22・§23・§26 |
| 2 | **手順の来歴・何手目か** | ダイレクト向かい飛車(角交換を経ずに向かい飛車)・2手目△3二飛・4四歩パックマン(2 手目に突く)・新米長玉(2 手目に指す) | §7・§27・§28 |
| 3 | **相手の戦型を条件にする** | 山田定跡(相手が四間飛車のとき)・横歩取り(対中飛車)(自分の手は普通の横歩取りと同じ) | §7・§28 |
| 4 | **相手の駒との位置関係** | 名前のある手筋 52 件(継ぎ歩・垂れ歩・十字飛車ほか。「相手の駒の前」「玉の逃げ道」が定義に要る) | §15.2 |
| 5 | **盤上から駒が消える/現れる** | 角交換振り飛車・角交換相振り飛車(角が盤から消える)・持ち駒を打つ手筋 | §24・§26 |
| 6 | **タイミング** | 陽動振り飛車(相居飛車から途中で振る)・「囲いをまだ決めない」こと自体を指す名前 | §24 |

**数の目安**: この 6 つで書けなかったのは、狙い 52 件(型 4 が大半)・戦法 28 件・囲い 0 件である。**囲いは駒の位置だけで決まるのでほとんど落ちない**(**訂正: 第 28 組で 1 件見つかった ― 坊主美濃は「玉頭に歩が無い」という否定で、駒の位置は片美濃と同じ。§32)。落ちるのは「動きの意味」を名前にしたもの ― つまり**このアプリが本当に言いたいこと**の側である。

### 31.3 誤認の側で分かった 2 つ(どちらも物差しが要る)

1. **P-85(初期配置と重なる形)**: 無敵囲いの相手側は、必要な 6 枚のうち 3 枚が後手の初期配置で、相手が何も動かしていない局面で半分そろう。**証拠 2 件以上でも起きるので I-9 型では捕まらない。** 開発・診断レーンが採番済み(状態は未着手)。
2. **狙いには誤認の物差しが無い**: 形の I-9 型に当たる不変条件が `data/intents` の側に無い。端攻めは端の歩を 2 つ突いただけで matched になる。**「沈黙が減った」は「正しく認識した」ではない**(§16・§17)。

### 31.4 逆向きの知見(足すより減らすほうが効いた場面)

必要な駒を 5 枚から 3 枚に減らした直し(アヒル囲い、自分側 §29・相手側 §30)は、**証拠なしの主張を 273 + 272 件(30 手まで)減らし、沈黙は 1 + 0 件しか増えなかった**(全手では沈黙 +4 + 16、主張 −283 + −394)。**ここから「枚数の多いレコードほど誤認を作る」と書いたが、**測ったらその一般化は間違っていた。訂正を §31.5 に書く。**

### 31.5 訂正: 「枚数が多いほど誤認が増える」は測ったら成り立たなかった

§31.4 で「枚数の多いレコードほど、まだ揃っていないのに立つ局面を作る」と書いた。**形 1 件ごとに数え直したところ、この一般化は成り立たない。**

**測り方**: 4 人 70 局・30 手まで(先手番 1096 局面)、形 73 件。各局面で `forming`/`completed` になった形ごとに、I-9 型(証拠 1 件以下かつ欠けマス 2 つ以上)かどうかを数えた。読み取りだけで `data/` は変えていない。

| required_pieces の枚数 | レコード数 | 立った延べ局面 | I-9 型 | 立ったうち I-9 の割合 | 1 レコードあたり立った数 |
|---|---|---|---|---|---|
| 2 枚 | 2 | 271 | **0** | **0%** | 136 |
| 3 枚 | 14 | 3269 | 2506 | 77% | 234 |
| 4 枚 | 23 | 6842 | 5519 | 81% | 297 |
| 5 枚 | 26 | 8010 | 6361 | 79% | 308 |
| 6 枚 | 8 | 2404 | 1804 | 75% | 300 |

**分かったこと**

1. **割合は枚数でほとんど変わらない**(3〜6 枚で 75〜81%)。**立った局面の 4 本に 3 本以上が「証拠 1 件以下で欠けマス 2 つ以上」である**ことのほうが、枚数より重い事実である。
2. **2 枚のレコードだけは構造的に I-9 型になりえない。** `forming` は証拠 1 件以上で立ち、I-9 型は欠けマス 2 つ以上を要求するので、必要な駒が 2 枚なら両方を同時に満たせない。**第 26 組で足した左美濃(玉8八・銀7八)が I-9 を 1 件も出していないのはこのため**で、「良いレコードだから」ではない。**2 枚の形は誤認の物差しから外れる**ので、むしろ注意が要る。
3. **アヒル囲いで減ったのは、割合ではなく「立つ局面そのもの」だった。** 必要なマスが 5 つから 3 つに減れば、「どれか 1 つが指された」局面が減る。1 レコードあたり立った数も 3 枚 234 に対し 4〜6 枚は 297〜308 で、同じ向きの差が出ている。
4. **上位は相手側に偏っている**(I-9 の多い 25 件のうち 20 件が `*_opponent`)。相手側は 35 件すべてを写したので、**同じ局面で多くの候補が同時に立つ**。1 位は一夜囲いの相手側(立った 558・I-9 467)で、これは P-85(初期配置と重なる)と同じ形の問題である。

**したがって、枚数を減らす直しは「誤認の割合」ではなく「候補として立つ回数」を減らす手段である。** 誤認の割合(4 本に 3 本)を下げるには、判定側の扱い(何をもって forming と呼ぶか、証拠 1 件で立った候補を見せるか)を変えるしかない。**それは判断的知識なので、このレーンの持ち物ではない。**

## 32. 第 28 組(2026-09-25 夜): 囲い 7 件 ― **図を自分で読んで埋めた。沈黙は動かない**

人間の決定(2026-09-25 夜、指示書 §7)により「図を人が読む工程」は入れず、**このレーンが図を読む**ことになった。対象は保留 11 + 未 13 = 24 行。この組はその最初のまとまり。

**読み方(司令塔の条件どおり)**。Wikipedia の囲いの記事の図は、`get_page_text` では要約されて落ちるが、**内蔵ブラウザで開くと筋 9→1・段 一→九 の表としてそのまま読める**。そこで次の手順にした。

1. **図の向きを先に確かめる。** 記事の先頭の図(本美濃)を読み、既に座標の分かっている 玉2八・銀3八・金5八・金4九 と一致することで、**この記事の図が先手側の向きである**ことを校正した。片美濃・金美濃も既存のレコードと一致した。
2. **同じ形を 2 度、違うもので読む。** 盤の図と、本文の説明(「左銀が7六に移れば銀立ち矢倉」など)の両方で読み、**一致した駒だけ**を `required_pieces` に入れた。木村美濃は、派生形の図と「木村美濃囲いの攻略」の図という**2 つの図が一致した**。
3. `confidence_level` はすべて **low**、`source` に「図から起こした・一次資料の確認はしていない」と明記。

**足した ID**: `mino_kimura`(木村美濃 = 玉2八・金3八・銀4七)・`mino_ginmino`(銀美濃 = 玉2八・銀3八・銀5八・金4九)・`mino_chonmage`(ちょんまげ美濃 = 片美濃 + 2六歩)・`yagura_hekomi`(へこみ矢倉 = 玉8八・銀7七・金7八・金6八)・`migi_yagura`(右矢倉 = 玉2八・金3八・銀3七・金4七)・`yagura_gindachi`(銀立ち矢倉 = 玉8八・金7八・金6七・銀7六)・`yagura_nagare`(流れ矢倉 = 玉8八・金7八・金6七・銀5七)。**スキーマ検証 80 件 OK**。

**第 27 組の保留を 1 件解消した**: 木村美濃は、将棋ジムのページの座標が後手側の段で向きが読めず保留にしていたが、**向きを校正できる図が見つかったので埋めた**。

**保留を 1 件足した**: 坊主美濃。**定義が「玉頭に歩が無い」という否定**で、駒の位置は片美濃とまったく同じである(図で確かめた)。**囲いで「書けない型」に当たったのはこれが初めて**(§31.2 では囲い 0 件と書いていたので、そこを 1 件に改める)。

**測った数**(狙いは 18 件で固定。形を 73 件 → 80 件):

| 範囲 | 自分側の沈黙 | 自分側の I-9 型 | 相手側 | 形全体の沈黙 |
|---|---|---|---|---|
| 30 手まで | 779 → **779**(不変) | 6942 → **7781**(+839) | 554・9248 で不変 | 460 → 460 |
| 全手 | 1232 → **1221**(−11) | 24795 → **28380**(+3585) | 947・27804 で不変 | 628 → 622 |

**読み方**: **30 手までは 1 局面も動かなかった。** 全手で 11 局面だけ減り、代価は証拠なしの主張 3585 件(**1 局面あたり 326 件**)である。相手側の 104 件/局面よりさらに悪い。**図を読んで語彙を増やしても、沈黙は動かない**という第 4 組以来の結論が、材料を変えても再現した。

**当たり方(4 人 70 局、全手)**: ちょんまげ美濃 53 局で立ち完成 1・75% 以上 7、へこみ矢倉 45 局、流れ矢倉 34 局、木村美濃 33 局(完成 2)、銀立ち矢倉 30 局、右矢倉 26 局、銀美濃 20 局。**歩を `required_pieces` に入れたちょんまげ美濃が問題なく動いた**ので、歩を含む形は書ける(片美濃との違いが歩 1 枚だけなので、当たる局面はほぼ片美濃と重なる)。

**埋まった数**: 囲い 自分側 **45 / 62**・相手側 35 / 35(相手側への写しはこの 7 件ぶん未処理)・戦法 185 行(未 0)・狙い 18 / 67。**残りの対象は 24 − 8 = 16 行。**

### 32.1 図を読む手順(次に図を読む人・セッションへ)

司令塔の指示(2026-09-25)により、第 28 組で踏んだ手順をそのまま残す。**この順でなければ、左右が入れ替わった座標を書いてしまう**(過去の取り違え P-12)。

1. **図がテキストとして読めるかを先に確かめる。** Wikipedia の囲いの記事は、`WebFetch` の要約では図が落ちるが、**内蔵ブラウザで開いて `get_page_text` か `javascript_tool` で `innerText` を取ると、筋 9→1(左→右)・段 一→九(上→下)の表として読める**。長い記事は `innerText` を節の見出しの位置で切り出す。
2. **向きを校正する。** その記事の中で**既に座標の分かっている形**(本美濃 = 玉2八・銀3八・金5八・金4九 など)の図を先に読み、一致するか確かめる。一致しなければ、その記事の図は後手向きか別の流儀なので**読まない**(将棋ジムの木村美濃のページは本文の座標が段 一〜三で、これに当たった)。
3. **同じ形を 2 度、違うもので読む。** 盤の図と本文の説明(「左銀が7六に移れば銀立ち矢倉」など)、あるいは同じ記事の別の図。**一致した駒だけ**を `required_pieces` に入れ、片方にしか出てこない駒は入れないか `optional` にする。
4. **`confidence_level` は low、`source` に「図から起こした・一次資料の確認はしていない」と書く。**
5. **足したら測る**(証拠 2 件以上版の沈黙・I-9 型・自分側/相手側を分けて)。

## 33. 書けなかった狙い 52 件の要件一覧(開発・診断レーン STEP 2 への入力)

人間の決定(2026-09-25 夜)の 2 番目「**狙いのスキーマを位置関係で書ける形に広げる**」の材料。**設計するのは開発・診断レーンで、このレーンは要件を渡すだけ。**

**対象**: §15.2 の名前つき手筋 55 件のうち、いまのスキーマ(`recognition_pattern` = 駒種 + 固定の移動先マス)で**書けなかった 52 件**。表の行から機械的に取り出し(56 行中「書けない」52 行)、**1 件も余らせず 6 つの型に割り当てた**(合計 52 = 15 + 7 + 15 + 8 + 3 + 4)。

| 型 | 件数 | 表せるようになるために要るもの | 例(すべて挙げる) |
|---|---|---|---|
| **A 相手の駒に接するマス** | **15** | 基準にする**相手の駒**と、そこからの**向き**(頭・尻・腹・斜め)。絶対マスではなく相対位置 | 叩きの歩・面打の歩・蓋歩・単打の歩・合わせ歩・突き違いの歩・銀ばさみ・バックの歩・歩頭の桂・桂頭の銀・腹銀・銀をかける・頭金・尻金・腹金 |
| **B 相手の駒 2 枚を同時に狙う** | **7** | その手を指した結果、**自分の駒の利きに相手の駒が 2 枚入る**こと(利きの計算) | ふんどしの桂・割打ちの銀・タコ金・筋違いの角打ち・角による両取り・角のたすき掛け・十字飛車 |
| **C 利きの線・交点・距離** | **15** | **離れたマスから相手の駒(や玉)への線**、自分の駒との上下関係(裏・下)、玉との**距離**(一間) | 焦点の歩・垂れ歩・控えの歩・底歩・紐歩・2段ロケット・田楽刺し・歩の裏側に香打ち・つるし桂・控えの桂・攻防の角・遠見の角・幽霊角・角のコビン攻め・一間龍 |
| **D 連続する複数手を 1 つの名前にする** | **8** | 2〜3 手の**まとまりと順序**(同じ筋に歩を 2 回、など)。いまの `recognition_pattern` は順不同の断片 | 手裏剣の歩・ダンスの歩・継ぎ歩・歩の連打・継ぎ桂・跳ね違いの桂・金送りの手筋・送りの手筋 |
| **E 盤から駒が消える** | **3** | **取る・取られる・持ち駒になる**ことの区別 | 角切り・飛車交換・飛車切り |
| **F 自分の陣に打つ・引く** | **4** | **持ち駒を打つ手**であることと、**自陣という領域**(マスの集合)の指定 | 自陣角・馬引き・自陣への飛車打ち・龍引き |

**読み方(設計の材料として)**

- **A と C で 30 件、全体の 58% を占める。** どちらも「**相手の駒(または自分の駒)を基準にした相対位置**」が書ければ表せる。**1 つの拡張でいちばん多く回収できるのはここ**である。
- **B は利きの計算が要る**(盤面から計算できるので、データではなくコードの仕事)。A・C が相対位置の**表記**の問題であるのに対し、B は**判定の**問題である。
- **D は順序**。いまの判定は順不同(`intentDetector` は各シグネチャを履歴のどこかで観測したかだけを見る)ので、**順序を要求する仕組みが無い**。第 23 組の鬼六流ドッカン飛車(飛車を 2 度振る)でも同じことが出ている。
- **E・F は 7 件と少ない**が、**戦型の側でも同じ型に当たっている**(角交換振り飛車・角交換相振り飛車 = E、§31.2 の型 5)。狙いと戦型で同じ拡張が効く。
- **どの型も「LLM に言い換えさせる」では解けない。** 盤面から機械が判定できる形にする必要があり、判定コード(`apps/server/src/analysis/`)の変更を伴う = 判断的知識。**このレーンの持ち物ではない。**

**あわせて渡す材料(狙いの側で見送った 5 件)**: §16 で「頻度から名前を作らない」の縛りにより捨てた 5 件と、§17 の 6筋位取り(1 手が普通すぎて区別にならない)は、**型 A〜F のどれでもなく「その 1 手だけでは区別にならない」**という別の問題である。**複数のシグネチャの組み合わせに重みを付けられるか**(1 件だけでは立てない、など)が要件になる。

**この一覧が言わないこと**: 件数は「名前の数」であって、**実際の対局でどれだけ出るかではない**。70 局の実測(§15.1)で相手が指した手の上位 30 は、ほとんどが駒組みの手であり、手筋の名前が付く手は稀である。**52 件すべてを書けるようにしても、沈黙がその分減るとは限らない。**

## 34. 第 29 組(2026-09-25 夜): 囲い 2 件 + 保留 13 件 ― **囲いの目録は未 0 行。埋め切った**

**足した ID**: `yagura_ryusen`(流線矢倉 = 玉8九・銀8八・金7八・金6七・銀5七)・`millennium`(ミレニアム囲い = 玉8九・銀7九・金7八・金6七)。どちらも §32.1 の手順で図から起こした(low)。**スキーマ検証 82 件 OK**。

- **流線矢倉**は、図と本文(「流れ矢倉と菊水矢倉をミックス」)が一致した。菊水矢倉の 玉8九・銀8八 と流れ矢倉の 銀5七 を合わせた形にちょうど当たる。
- **ミレニアム囲い**は、**2 つの図(6七金型の駒組み例と発展例)で一致した 4 枚だけ**を置いた。**もう 1 枚の銀は図によって 8八 と 8七 で違う**(発展例は上部に強くするため 8七)ので入れていない。§5.1 で「出典が食い違う」として保留していたのはこの行で、玉が 8八 か 8九 かで分かれていた。**図を直接読むと玉は 9 段目の 8 筋(8九)で、shogi-gym の読みと一致した**。食い違っていたのは出典ではなく、要約を通した読み方の側だった。

**1 行は「既存と同じ」で閉じた**: 目録の「穴熊囲い」は総称で、その基本形は既存の `anaguma_furibisha`(玉1九・香1八・銀2八・金3八・金3九)である。**Wikipedia の「穴熊の基本形」の図と 5 枚とも一致した**ので、新しいレコードは作らず、既存レコードの座標が図で裏づけられたことだけを記録する。

**保留 13 行 ― 埋められなかった理由は 4 つに分かれる**:

| 理由 | 行 |
|---|---|
| **囲い単体の図が無い**(実戦の局面図しかない / 本文の言及だけ) | 天野矢倉・矢倉早囲い・四枚美濃・一直線穴熊・振り飛車ミレニアム |
| **出典に座標の文も図も無い**(名前と概要だけ) | 富士見矢倉・三手囲い・中段玉・最強囲い・トラック囲い・カタ囲い |
| **同じものか判断できない** | 角矢倉(記事にあるのは「四角矢倉」) |
| **出典どうしが食い違う** | 串カツ囲い |

**振り飛車ミレニアムを書かなかった理由は、他と性質が違うので書き残す**。本文に「振り飛車側がミレニアムに組む戦法も考案されている」とあるので、居飛車のミレニアム(玉8九)を**左右に反転**すれば 玉2九 になりそうに見える。**しかしこれは 180 度回転(自分側 ↔ 相手側の写し)とは別の操作**で、出典が述べていない推測である。過去の取り違え(P-12)と同じ入口なので書かない。

**測った数**(狙いは 18 件で固定。形を 80 件 → 82 件):

| 範囲 | 自分側の沈黙 | 自分側の I-9 型 | 相手側の沈黙 |
|---|---|---|---|
| 30 手まで | 779 → **779**(不変) | 7781 → **8034**(+253) | 554(不変) |
| 全手 | 1221 → **1221**(不変) | 28380 → **29320**(+940) | 947(不変) |

**沈黙は 30 手までも全手も 1 局面すら動かなかった。** 流線矢倉は 70 局中 44 局で立つが完成 0・75% 以上 0、ミレニアム囲いは 20 局で立ち完成 0。**「語彙を増やしても沈黙は動かない」がもっとも純粋な形で出た組**である。

**囲いの目録の最終の数**: 64 行のうち **下書き 44・既存 4・保留 14・対象外 2・未 0**。人間の決定(2026-09-25、網羅)に対して、**出典から書けるものは書き切り、書けないものは理由をつけて残した**。

## 35. 戦型を初めて測った(2026-09-25 夜。§20〜§28 の「測れない」はここで終わる)

開発・診断レーンが戦型を認識する関数を入れた(`09cf6ff`、`apps/server/src/analysis/openingDetector.ts`。`recognition_pattern` の `{piece,to}` を形の `required_pieces` に写して既存の `analyzeShapeFormationFromEvents` を呼ぶ。新しい判定・閾値なし・本体の経路には未接続)。**これにより、第 17〜25 組で「測れない(認識のコードが無い)」と書いて足した戦型 111 件が、初めて測れるようになった。**

**レコードの `source` に書いた「測れない」の文はそのまま残す**(足した時点の事実であり、書き換えると経緯が消える)。**訂正はこの節に置く。**

**測り方**: 向こうの `loadOpeningsFromDir(dir)` と `analyzeOpeningFormationFromEvents(sfen, events, openings)` を、私の測る道具(scratchpad)から呼んだだけ。**判定は向こうの関数、こちらは数えるだけ**で、閾値も判定も書いていない。材料と分母は形・狙いのときと同じ(§1.1 の 4 人 70 局、先手番の局面 = 30 手まで 1096・全手 2735)。`I-9 相当は「申告している行(forming)」にだけ当てる`(開発・診断レーンの §12.7 の訂正に従う)。道具は typecheck 済み(rc=0)。

**測った数**(戦型の下書き 111 件。うち `recognition_pattern` を持つ候補 108 件):

| 範囲 | 戦型の沈黙 自分側 | 相手側 | **どちらか** | I-9 相当 自分/相手 | completed 延べ | **うち証拠 0** | forming 延べ |
|---|---|---|---|---|---|---|---|
| 30 手まで | 405 | 17 | **0** | 4745 / 322 | 3070 | **1021** | 10073 |
| 全手 | 835 | 154 | 33 | 14495 / 1204 | 7705 | 2043 | 30279 |

**読み方 ― 戦型では沈黙が物差しにならない。**

1. **30 手までの 1096 局面すべてで、何かの戦型が「証拠 2 件以上か完成」で立つ**(どちらかの沈黙 0)。形では 95% → 71%、狙いでは 67% → 57% と沈黙が動いたが、**戦型は最初から沈黙が無い**。言い換えると、**戦型は「言うことが無い」ではなく「言い過ぎる」側の問題**である。沈黙率は戦型の物差しには使えない。
2. **証拠 0 の completed 1021 件(30 手まで)は、すべて 1 レコードから出ている**: `yokofudori_23fu`(横歩取り2三歩、対 1、歩2三)。**2三の歩は後手の初期配置**なので、相手が 1 手も指していなくても「完成」になり、**70 局すべてで立つ**。これが開発・診断レーンの P-86 の実体である。**初期配置と重なる下書きは 111 件中この 1 件だけ**(駒種とマスの両方が初期配置と一致するものを機械で全件数えた。一部だけ重なるものは 0 件)。
3. **完成の上位は「1 マスだけのレコード」が占める**: 6筋位取り(歩4四)32 局・4四歩パックマン(歩4四)32 局・右玉(玉4八)22 局。**どれも `source` に「この 1 手では区別にならない」と書いて足したもの**(§24・§27)で、**書いたとおりの結果が数で出た**。対 1 のレコードは 35 件ある。
4. **立った局数の上位は駒組みの普通の手**: 横歩取り2三歩 70 局・矢倉 64 局・鬼殺し 63 局・英春流 53 局。英春流(4八銀・5六歩・5七銀)のように、**ありふれた 3 手の組み合わせが半分以上の局で立つ**。

**司令塔への提案(判断は司令塔。こちらでは直さない)**

- **(a) `yokofudori_23fu` は本来この形では書けないレコードだった。** 出典の定義は「△2三歩と**打つ**」ことで、「2三に歩がある」ことではない。**打った手かどうかはスキーマで区別できない**(§31.2 の型 5)。保留印に変えるか消すかは司令塔の判断。**ただし消すと `apps/server` の試験 1 本が落ちる**(`openingDetector.test.ts` が下書きの実ファイル数 111 に結合している。開発・診断レーンの連絡)。**数を変えるときは先に「111 → N」を伝える。**
- **(b) 対 1 のレコード 35 件は、名前を見せる側では使えない。** 消す必要はないが、露出制御(STEP 3)で「対 1 は名前を出さない」のような扱いが要る。これは判断的知識なのでこのレーンの持ち物ではない。

**この数が言わないこと**: 「完成した」= その戦型を指していた、ではない。戦型の判定は**盤の駒の位置と、そこへ動いた証拠**だけを見ており、**相手の形も手順の前後も見ていない**(§31.2 の型 2・3)。横歩取り3三角と 3三角戦法のように**機械では区別できない組**(§25)は、両方が同時に完成する。

## 36. 第 30 組(2026-09-25 夜): `yokofudori_23fu` の `recognition_pattern` を外した ― **相手側の「沈黙 0」は 1 件の作り物だった**

司令塔の判断(2026-09-25)により、`yokofudori_23fu`(横歩取り2三歩)の **`recognition_pattern` を外し、レコードは名前・出典・書けない理由とともに残した**(藤井システム・ゴキゲン中飛車と同じ扱い)。`confidence_level` は low。**ファイル数は 111 のまま**(消していない)。スキーマ検証 OK。

**外した理由(`source` にも書いた)**: 出典の定義は「△2三歩と**打つ**」ことであって「2三に歩がある」ことではない。**打った手かどうかは、いまのスキーマでは盤に駒があることと区別できない**(§31.2 の型 5)。2三 は後手の歩の初期配置なので、パターンを置いたままだと**相手が 1 手も指していない局面で completed** になる。

**測り直し**(同じ 70 局・同じ分母。**戦型の下書き 111 件、候補は 108 → 107**):

| 範囲 | 証拠 0 の completed | completed 延べ | 戦型の沈黙 相手側 | どちらかの沈黙 | 自分側 |
|---|---|---|---|---|---|
| 30 手まで | **1021 → 0** | 3070 → 2034 | **17 → 596** | **0 → 272** | 405(不変) |
| 全手 | 2043 → 0 | 7705 → 5544 | 154 → 1186 | 33 → 468 | 835(不変) |

**いちばん大事なのはここ**: §35 で「30 手までの全 1096 局面で何かの戦型が立つ(沈黙 0)」と書いたが、**その「沈黙 0」は、この 1 件の作り物だった**。外すと相手側の沈黙は 17 → 596(54%)、どちらかの沈黙は 0 → 272(25%)になる。**1 件の誤ったレコードが、全体の物差しを 1 つ丸ごと壊していた。** I-9 相当(forming 行)は 4745 / 322 のまま動かない ― **この壊れ方は I-9 では捕まらなかった**(completed には I-9 を当てないため)。§31.3 の「誤認の物差し」の話に、**3 つ目として「証拠 0 の completed を数える」を足す**。

**副作用(開発・診断レーンへ連絡済み)**: `apps/server/src/analysis/openingDetector.test.ts` は下書きの**候補数 108・null 3** にも結合しているため、この直しで 1 本落ちる(`107` / `4` になる)。**司令塔の判断の前提「ファイル数 111 は変わらないので試験は落ちない」は、ファイル数だけを見ていた。** 実測: `openingDetector.test.ts` は 8 passed / 1 failed(226 行 `expect(candidates).toBe(108)`)。試験側の直しは開発・診断レーン(OPEN-2 で固定 fixture にする予定)。

**P-86 の残り**: データを直しても、**判定側の「欠け 0 なら証拠を問わず completed」は残る**(`resolveStatus` の既存定義)。初期配置と重なる形が今後また入れば同じことが起きる。そちらは開発・診断レーンの STEP 3。

## 37. 測る道具が二本立てになった(2026-09-25 夜。以後の測定は本体側の道具で回す)

開発・診断レーンが測る道具をコミットした(`97734af`、`scripts/playtest/recognitionMeasure.ts`)。**向こうの報告を鵜呑みにせず、自分で回して突き合わせた。**

**やったこと**: 4 人 70 局の一覧(`{"games":[{group,id,path}]}`)を scratchpad に作り、本体側の道具を 30 手/全手の 2 回回して、**私の使い捨て台本(`measure.ts` + `openmeasure.ts`)の出力と 1 点ずつ比べた**。

**結果: 30 点すべて一致(不一致 0)**。比べたのは、分母・形の沈黙(自分側/相手側/全体)・狙いの沈黙・I-9 型(自分側/相手側)・戦型の沈黙(自分側/相手側/どちらか)・戦型の I-9 相当(自分側/相手側)・戦型の completed / 証拠 0 / forming の 15 項目 × 2 範囲。

| 範囲 | 形 自分/相手/全体 | 狙い | I-9 自分/相手 | 戦型 沈黙 自分/相手/どちらか | 戦型 I-9 自分/相手 | 戦型 completed / 証拠0 / forming |
|---|---|---|---|---|---|---|
| 30 手まで(1096) | 779 / 554 / 460 | 620 | 8034 / 9248 | 405 / 596 / 272 | 4745 / 322 | 2034 / 0 / 10073 |
| 全手(2735) | 1221 / 947 / 622 | 755 | 29320 / 27804 | 835 / 1186 / 468 | 14495 / 1204 | 5544 / 0 / 30279 |

**これで、この記録に載っている数はすべて 2 つの独立した実装で再現できる状態になった。** 以後の測定は本体側の道具(`recognitionMeasure.ts`)で回す。使い捨て台本は校正用に scratchpad へ残す。

**引き継ぎの注意(向こうからの連絡)**

- `--games` の一覧は**コミットしない**(3 人目の棋譜がブランチ外にあるため)。各自の scratchpad に置く。私の一覧は §1.1 の 4 組をそのまま並べたもので、70 局・組 4。
- `openingDetector.test.ts` は固定 fixture になったので、**戦型の下書きを足しても試験は落ちなくなった**。代わりに「**下書き全件が最後まで判定できる**」という見張りが server の試験から消え、**いまはこの道具を実行することだけが見張りになる**。新しい駒名やマス表記の誤りは実行時に落ちる。**下書きを足したら必ずこの道具を 1 回通す**(これまでの「増やしたら必ず測る」に、この意味が加わった)。
- **未実装**: レコード 1 件ごとの「立った局数 / 完成した局数」(`onGames`/`compGames`)。**この記録の各組の報告では毎回この数を使っている**(例: §32 の「ちょんまげ美濃 53 局で立ち完成 1」)ので、欄の追加を頼んだ。

## 38. レコード 1 件ごとの局数の欄(OPEN-2b)を校正した(2026-09-25 夜。**記録の 102 点すべてと一致**)

開発・診断レーンが §37 で頼んだ 6 欄をコミットした(`e1caccd`、記録 `1c248e8` §12.8)。`byGroup[].{shapeOnGames, shapeCompGames, intentOnGames, intentCompGames, openOnGames, openCompGames}`(id → 局数)と、局ごとの `rows[].{shape,intent,open}{On,Comp}Ids`。**向こうの校正を鵜呑みにせず、同じ 70 局で自分で回して 3 通りに突き合わせた。**

**(1) 戦型の 2 欄 ― 自分の保存ファイルと id ごとに一致(不一致 0)**

| 範囲 | `openOnGames` id 数 / 合計 | `openCompGames` id 数 / 合計 | 不一致 |
|---|---|---|---|
| 30 手まで | 99 / 1751 | 51 / 343 | **0** |
| 全手 | 107 / 2535 | 61 / 558 | **0** |

当て先は §35・§36 で使った私の使い捨て台本の出力(scratchpad `measure/open2-30.json`・`open2-0.json` の `onGames`/`compGames`)。**一度も立たなかった id は私の表に無い**ので、欠落を 0 として比べた。

**(2) 形・狙いの 4 欄 ― この記録に書いてある値 102 点すべてと一致(不一致 0)**

戦型と違って保存ファイルが無いので、**各組の報告で本文に書いた数**を当て先にした(すべて 4 人 70 局・全手)。

| 欄 | 当て先の数 | 出どころ | 一致 |
|---|---|---|---|
| `shapeOnGames` | 9 | §32(ちょんまげ美濃 53・へこみ矢倉 45 …)・§34(流線矢倉 44・ミレニアム 20) | 9 / 9 |
| `shapeCompGames` | 35 | §3・§4・§5 の「完成した局」各 10/10/9 件、§29(左美濃 4・居飛車銀冠 1)、§32(ちょんまげ美濃 1・木村美濃 2)、§34 | 35 / 35 |
| `gamesBest75`(既存の欄) | 32 | 同じ 3 組の「3/4 以上一致した局」(無敵囲い 47 など) | 32 / 32 |
| `intentOnGames` | 18 | §16 の表 13 件 + §17 の新 5 件の「証拠 1 件以上」 | 18 / 18 |
| `intentCompGames` | 8 | §17 の「全部そろった」 | 8 / 8 |

狙いは **18 件すべてに当て先がある**(合計 453 も一致)。**`ahirugakoi` は駒を 5 枚から 3 枚に減らした後でも完成 0 のままで、§29 に書いた「この直しは測った数に影響していない」が改めて確かめられた。**

**(3) 既存の欄 ― 出力全体が前回の実行と完全一致**

新しい 6 欄と `rows[].*Ids`、入力ディレクトリの一覧を除いて、`byGroup` も `rows` も **1 文字も違わなかった**(30 手・全手とも)。欄を足した変更が既存の数に触れていないことを、項目ごとではなく出力全体で確かめた。

**副産物(この校正で分かったこと)**: 今回は `--openings` に `data/openings` も渡したが、**結果が 1 も動かなかった**。既存の 3 件(`ibisha`・`nakabisha`・`shikenbisha`)は `recognition_pattern` が `null` で、**1 局面も立たない**ためである。つまり**いま測れている戦型の認識は、すべてこのレーンの下書き 111 件によるもの**で、本体の `data/openings` は認識に寄与していない(あれはシナリオ用のレコード)。これは §35 の「戦型を初めて測った」という言い方を裏づける。

**この節の意味**: §37 で「この記録に載っている数はすべて 2 つの独立した実装で再現できる」と書いたが、**レコード 1 件ごとの局数だけは私の台本にしか無かった**。それも本体側の道具で出せるようになり、**過去の組の報告に書いた 102 点が、別実装で後から検算できた**。以後の組では、この欄を使って報告する(私の台本は用済み。校正用に scratchpad へ残す)。

## 39. 行動の表の拡張案 28 件(2026-09-25 夜。**承認前の下書き。`ANSWER_MENU` には入れていない**)

人間の指示「**癖だけでなく、アドバイスも必要**」(DESIGN_BRIEF_OBSERVATION_LAYER_2026-09-25.md §5 #2b、`e7ffcfd`)を受けた割り当て。冊子で使える承認済みの行動は `lib/answerMenu.ts` の M1〜M9 の 9 件で**全部が時間と考える手順**であり、2 周目で増える読み(側・形・反応・分かれ道)に対応する行動が 0 件だった。その 4 領域の案を下書きした。

**置き場**: `data/drafts/2026-09-25-knowledge/actions/`(README + 領域ごとに 1 ファイル)。**`ANSWER_MENU` と `docs/DELIVER_GATES.md` には入れていない**(表に足すのは人間の承認。CLAUDE.md ルール 4 の判断的知識)。コミットは領域ごと: `2d6bff0`(側 + README)・`a2ac43a`(形)・`2f59b1c`(反応)・`cca2b28`(分かれ道)。

**数**

| 領域 | 案 | 出典の引用 | 別々の URL | 書籍への注つき |
|---|---|---|---|---|
| A 側 | 7 | 7 | 1 | 3 |
| B 形 | 7 | 9 | 2 | 3 |
| C 反応 | 7 | 7 | 2 | 4 |
| D 分かれ道 | 7 | 8 | 2 | 5 |
| **合計** | **28** | **31** | **3**(将棋の格言・居玉・王手) | **15** |

**観測の区分(司令塔の追加指示。延べ 30 = 28 件 + 2 件が 2 区分にまたがる)**: 値あり(§1)15・登録のみ(§2)5・未登録 9・語彙の列 1。

**守った形**(依頼のとおり): 条件(冊子が数から言えること)→ 合図(対局中に本人が気づけること)→ 行動の核(1 文)→ 答え合わせに使える数 → 出典 URL + 参照日 → 初心者向けの言葉。**28 件すべての「行動の核」が「候補に入れてから比べる」「1 つずつ並べてから比べる」の型**で、指すことを勧める形にしていない(機械で確かめた: 命令形・勧誘形 0 件)。**合図に評価値・エンジンの候補・「優勢かどうか」を使った項目は 0 件**(DELIVER_GATES §2.5 の教訓 ― 分析の条件を発動の合図に写さない)。

**この組で判断したこと 4 つ**

1. **出典の弱さを項目ごとに書いた。** 主な出典の Wikipedia『将棋の格言』には記事全体に「**出典がまったく示されていないか不十分**」「**独自研究が含まれているおそれ**」の注意書きがある(2014 年 6 月)。そこで各項目に、**その格言が記事の中で書籍への注を持つか**を書いた(15 件が持つ。青野照市『勝てる将棋格言36』創元社 2003 ほか)。人間が承認するときの材料になる。
2. **逆向きの格言を同じ項目に併記した。** 「居玉は避けよ」には「急戦は居玉」、「攻めは飛角銀桂」には「金なし将棋に攻め手なし」、「王手は追う手」には「終盤の王手は絶対的先手」がある。**片方だけ引くと、将棋の事実判断を私がしたことになる**(CLAUDE.md ルール 5)。
3. **否定型を 2 件入れた**(A-側-04・B-形-02)。承認済みの M3・M7・M8 と同じ使い方で、「やらなくていいこと」の節に置く。**数が「守りが少ない」と言っているとき、それを「攻めが多すぎる」と読み替えない**ための歯止めで、特に B-形-02 は B-形-01 と**対にして同じ節に並べる**想定である(数が「居玉が多い」と言っても「居玉はいつも悪い」にはならない)。
4. **顧客を評する言葉を外した。** A-側-07 の出典は格言「ヘボ将棋玉より飛車を可愛がる」だが、**冊子には格言の名前を出さず行動の文だけを使う**と本文に書いた。

**司令塔の前提の訂正(このレーンが正本で確かめた)**: 「`obs.side.*` は登録が無い」と伝えられたが、`docs/OBSERVATION_ITEMS.md` **§1.9 に `obs.side.{tags, of, top1, actual}` の 4 行があり、「既存の出力にある値」として登録されている**。そのため領域 A の 3 件は「登録のみ」ではなく**値あり**で書いた。司令塔は誤りを認めた(grep の見落とし)。逆に `obs.geo.*` がまだ値を持たないという指摘は正本のとおりで、**値としては別の id に既にある**(`kingNeighbors` → `obs.fe.kingSurroundings`、`kingEscapes` → `obs.cf.kingEscapesRoot/End`、`moveFacts` → `obs.cf.userMoveFacts`)。ただし**どれも全手では出ていない**(急落の手前だけ / 組の分かれ目と終点だけ)ので、各項目にその範囲を添えた。

**足りない欄(開発・診断レーンが条件の関数を書く段 #7 への申し送り)**: 未登録 9 件の中身は、(1) 相手の手の**駒種**、(2) 相手が**打った升**、(3) 1 手で **2 枚に当たっている**か、(4) 玉と飛車の**距離**、(5) 相手の**角の利きの線上に自玉があるか**、(6) 飛車が**取られる形**か、(7) 大駒 1 枚と小駒 2 枚の**交換**という組み合わせの名前。**相手の手については「種類の真偽」(`obs.timeSearch.col.oppPrev*`)はあるが駒種と場所が無い**のが、領域 C(反応)で未登録が 4 件と多い理由である。

**次にこの席がすること**: 司令塔が PDF の見本に「(承認待ちの案)」の印つきで載せ、人間に見せる。**承認された分だけ `ANSWER_MENU` に足る**(条件の関数は開発・診断レーン)。この席は承認の工程には入らない。

### 39.1 人間の決定 ― 28 件のうち 13 件が「正式なコーチング知識」として承認された(2026-09-25 夜、司令塔より伝聞。記録 DESIGN_BRIEF §5 `062f032`)

**承認された 13 件**: A-側-04・05・06、B-形-02・03、C-反応-01・02、D-分かれ道-01・02・04・05・06・07。承認の意味は「**知識として使用可能**」であり、**今回の顧客への掲載は別の門**(顧客の事実 → 提示する根拠 → 掲載)を通る。残る 15 件は下書きのまま(条件の欄を足してから第 2 陣)。`ANSWER_MENU` への追加は開発・診断レーン(§5 の順 #7)。**文言の正本は下書きの「行動の核」**なので、この席は 13 件に手を入れない(司令塔の指示)。

**人間の言葉**: 「28 個のアドバイス」ではなく「**今後使えるコーチング部品 28 個**」。否定型を対にする設計は良い。

**承認・不承認を機械で照合して分かったこと(この席が確かめた)**

| 観測の区分 | 承認 13 | 下書きのまま 15 |
|---|---|---|
| 値あり(§1)のみ | **12** | **1**(A-側-01) |
| 値あり + 別の区分 | 1(B-形-02) | 1(C-反応-07) |
| 登録のみ(§2) | 0 | 4 |
| 未登録 | 0 | 8 |
| 語彙の列 | 0 | 1 |

**承認された 13 件は、条件に使う数が既に出ている項目とほぼ完全に一致する。** 未登録 8 件・登録のみ 4 件・語彙 1 件は**1 つも承認されていない**。ただしこの対応の意味は、下の「来歴」を読まないと取り違える。

**来歴 ― この対応は人間が引いた線ではない(2026-09-25 夜、司令塔の補足)**

**13 件は司令塔が「値あり(§1)、かつ 出典に書籍への注があるか規則」で選んだ勧めであり、人間はその一覧をひとまとまりで承認した。** したがって上の表の「値あり ⇔ 承認」は、**人間の判断ではなく司令塔の選び方の写し**である。A-側-01 が外れたのも出典に注が無いためで、人間がその項目を退けたのではない。**人間が自分の言葉で示した基準は、表の承認ではなく掲載の門**(「この顧客の事実から、その行動を提示する根拠があるか」)のほうである。**この 1 段が無いと、上の表は「人間は数の出る行動だけを良しとした」と読めてしまう。そうは言えない。**

**自分の数の訂正(§39.1 の初版の誤り)**: 初版に「承認されたもののうち 4 件は注の無い格言」と書いたが、**正しくは 3 件**(A-側-04・B-形-02・D-分かれ道-01)。A-側-05 は出典に米長邦雄の書籍への注があり、私の検出が「への注が付いている」という言い回しだけを見ていたため取りこぼした。内訳は**注あり 9・規則 1・注なし 3**で、注なしの 1 件(B-形-02)は別の URL による 2 つ目の出典を持つ。**司令塔の選び方(注あり または 規則)に当てはまらないのは、厳密には A-側-04 と D-分かれ道-01 の 2 件**である。**その後の続き(司令塔、記録 DESIGN_BRIEF §5 `e15070d`)**: この指摘を受けて司令塔が承認用の一覧の検出を直したところ、**「注あり」の表示が反転していた項目が 28 件中 7 件**あった(B-形-01・04・07、C-反応-03・06、D-分かれ道-01・03。原因は「注は**付いていない**」という言い回しを検出が見ていなかったこと ― **私の検出の取りこぼしとはちょうど逆向きの誤り**で、7 件はいずれもこの記録で「注は付いていない」と書いた項目なので、直った後の値はこちらと一致する)。**2 件の内訳はこれで説明が付いた**: A-側-04 は否定型として型で選んだもので条件外は承知の上、D-分かれ道-01 は検出の誤りで入っており、**外すかどうかは人間の判断**(この席は動かない)。

**言えないこと(この席の歯止め)**: 出典の強さと承認の対応を、上の来歴抜きで因果のように読まない。**分子も小さい**(承認 10 / 13 対 下書き 7 / 15)ので、どちらにしても主張の柱にはしない(§2.2b と同じ型の誤りを避ける)。

**この席への含意**: 第 2 陣を書くときは、**先に「その数が出るか」を `docs/OBSERVATION_ITEMS.md` で確かめてから書く**。今回は 4 領域を均等に 7 件ずつ書いたが、未登録の数を条件にした 9 件は承認の対象にならなかった。**均等に配るより、値のある欄から書くほうが通る。**

### 39.2 第 2 陣は「分析が出した候補を部品に仕上げる」に変わった(2026-09-25 夜、司令塔より伝聞。記録 DESIGN_BRIEF §5 `9f8b923`)

人間が工程を 3 段のゲートに置き直した ― **分析は大胆に。検証は厳密に。顧客への表現は慎重に。** 2 周目の分析の役と統合役が、仮説ごとに「この仮説ならこういう行動が考えられる」という**行動候補(承認外・内部)**を出し、**その節がそのまま第 2 陣の入力になる**。

**この席の仕事の変わり方**: 第 1 陣(§39 の 28 件)は**候補が無い状態から書いた**。第 2 陣は**分析が出した候補に、出典を付け・合図と行動の核を型に整え・観測の区分を付ける**仕事で、**候補を自分で作り直さない**。同じことを `data/drafts/2026-09-25-knowledge/actions/README.md` にも書いた(次にあのフォルダを触る席が最初に読む場所のため)。

**これで §39.1 の教訓が効く形になった**: 「先に数が出るかを確かめてから書く」は、第 2 陣では**分析が出した候補のうちどれが仕上げられるかを見分ける**基準になる(数の出ない候補は、条件の欄を足すまで部品にならない)。着手は 2 周目の統合 md が出てからで、合図を待つ。

### 39.3 承認済みの D-分かれ道-07 の合図を人間の決定で変えた(2026-09-25 夜)

§39.1 で「承認済みの文言なので触らない」と書いた項目について、**人間が直接「変えて」と決めた**(司令塔が直接聞いた。伝聞)。

- **変えた所**: 合図を「同じ局面で手が決まらないまま、**時計だけ減っている**と気づいたとき」→「**手が決まらないまま迷っていると気づいたとき**」。
- **変えていない所**: 行動の核(いま見えている手のうち、簡単なほうを候補の先頭に置いてから比べる)・条件(`obs.time.forkAmongLongThink`)・出典・答え合わせに使える数。
- **理由**: 「**合図に時計を見ることを使わない**」 ― 時間管理そのものを顧客への処方箋にしない原則(§39.2 の置き直し)。**数は元から入っていなかったが、時計を見ること自体が合図になっていた。**
- **経緯**: この席が E-時間-01 を直したときに「承認済みの D-分かれ道-07 も同じ形では」と司令塔へ確認を上げ(`8304768` の報告)、司令塔は「原則には触れないと読むが人間に添えて報告する」と判断し、**人間が変更を決めた**。初版の文言と理由は下書きの本文に残した。
- **併せて直した所(司令塔の指示には無いが、放置すると食い違う)**: 項目の**見出し**が「手が決まらないまま**時間が減っていたら**…」で、変えた後の合図と食い違っていた。「手が決まらないまま**迷っていたら**…」に合わせた。**承認の対象は「行動の核」**(司令塔の言明)なので見出しは承認の対象外だが、**見出しは一覧を機械で当たるときの見出しになる**ため直した(報告済み)。
- **この席が触らないもの**: `ANSWER_MENU` への反映は開発・診断レーン(§5 の順 #7)。

**残る教訓**: 承認済みのものでも、**新しい原則が後から来たときに当たり直す**必要がある。今回は自分の下書き 31 件を機械で当て直したことで見つかった(§39.2 の「合図に使わないもの」を README に置いたのはそのため)。

### 39.4 人間が書いた行動の文を部品に整えた(B-形-08。2026-09-25 夜の人間の文、整えたのは 2026-09-26)

**ほかの 31 件と扱いが違う 1 件。** 行動の核「**飛車を動かして攻めを考える前に、玉まわりの形を一度確認する。**」は**人間が自分で書いた文**(記録 DESIGN_BRIEF §5 `4fbf074`)で、**そのまま承認済み**として扱う。合図「飛車を動かしたあと」も人間の指定。**この席が整えたのは行動の核以外の欄だけで、文には一字も手を入れていない**(機械で確認)。

- **条件**: `obs.vocab.shapeStatus` の自分側 `completed` が**全手でも 0**、`obs.vocab.shapeMissingSummary.selfClosestOneAwayGames`(あと 1 枚まで行った局。4 人目の 3 分の 18 局で 10)、`obs.time.rookMark`(飛車が動いたか。18 局中 17 局)。**3 つとも値あり(§1)** ― `obs.vocab.*` の 2 本は昨日の STEP OBS-5c・OBS-5e で §1.16 に実体化されたばかりである。
- **出典は「出典なし」と書いた。** 人間の言葉なので文献から起こしていない。**無いものを埋めない**(出典なしは出典なしと書く)。
- **写しの粒度の注意を本文に書いた**: `obs.vocab.shapeStatus` は**種類 × 側 × 状態の件数**で **id ごとの内訳を写さない**(白いリストの門)。したがって背景の「いちばん近づいた形は 16 局で同じ」「必要な 5 枚のうち 3 枚は初期配置のまま」は**写しからは言えない**(認識の道具の出力側にはある)。冊子に出すなら出どころが写しでないことを承知で引く必要がある。
- **人間が指定した禁止を本文に明示した**: 「30 手目までは銀を動かす」「銀を動かすまで仕掛けない」のような**具体的な制約は入れない**(データから導けない)。**この席が手を加えるとしたらそこが入り口なので、塞ぐ文を置いた。**

**これで下書きは 32 件**(A 7・B 8・C 7・D 7・E 3)。**合図に時計・残り時間・秒数・評価値・エンジン・優勢を使う項目は 0 件**(機械で確認)。司令塔より、冊子の「やってみること」は最終的に **2 本程度**(②の M4 と、この③の 1 本)になる見込み。**行動を増やすために根拠を曲げない**が人間の指示である。

### 39.5 B-形-08 の数の訂正と、自分で回した裏取り(2026-09-26)

司令塔から「下書きの `selfClosestOneAwayGames` = 10 は誤りで、**写しの実際の値は 13**。10 は『あと 1 枚だった 13 局のうち欠けていたのが銀だった局』」と指摘を受けた。**元の 10 は、司令塔が背景として送ってきた「片方だけ上げて止まった局が 10」をこの id に当てた私の当て違いである**(id に紐づく値ではなかった)。下書きを直した。

**鵜呑みにせず、道具を自分で回して確かめた**(`recognitionMeasure.ts`、4 人目の 20 局・全手、形 82・狙い 18・戦型 114)。

| 母集団 | `selfClosestOneAwayGames` | 欠けていた 1 枚の内訳 |
|---|---|---|
| **この席の実測: 4 人目 20 局** | **15** | 銀4八 7・銀6八 **4**・玉5八 2・金4九 1・**玉2八 1** |
| 司令塔の写し: 3 分の 18 局 | 13 | 銀4八 7・銀6八 3・玉5九 2・金4九 1 |

**差は 2 で、母集団の差(20 局 − 18 局)とちょうど合う。** 内訳も銀6八 が 1・玉2八 が 1 減るだけで、他は同じ。**司令塔の 13 は正しい**と確かめられた。銀の割合も、こちらの 11 / 15 と向こうの 10 / 13 で整合する。

**併せて確かめたこと**: 自分側の形の `completed` は **0**(`statusCounts.shape.self` = none 24169・forming 6475・completed 0)。B-形-08 の条件の芯は実測で裏づけられている。

**食い違い 1 件は解決した(2026-09-26、司令塔が誤りを認めた。記録 `c906e2c`)**: 向こうの内訳の「**玉5九** 2」は、こちらの実測の「**玉5八** 2」が正しかった。5九は先手玉の初期配置の升なので、**「欠けている駒が玉5九」では「玉が初期位置にいないから欠け」という逆の意味になる**。**原因は段の書き写し** ― 開発・診断レーンの報告はアルファベットの段で `玉5h` と書かれており(`h` = 八、`i` = 九)、司令塔が漢数字に直すときに 1 段ずれた。該当の 2 局はどちらも玉を 5八へ動かす形で、正しい読みは「**玉が 5八へ来ていない**」。**冊子に出る前に捕まえられた。**

**この型を覚えておく**: **アルファベットの段(`a`〜`i`)を漢数字に直すところは、1 段ずれても文として成立してしまう。** `h` = 八・`i` = 九。P-12(段だけ反転させて左右が入れ替わる取り違え)と同じ族の誤りで、**升の表記を人が写し替える工程があるたびに起きうる**。数字が初期配置の升(5九・5一)になったときは特に疑う。

**教訓**: **背景として口頭で渡された数を、id の値として書かない。** 同じ「10」でも母集団が違えば別の数である(§2.2b の「分母の出どころを書く」と同じ型)。今回は冊子に出る前に司令塔が捕まえた。

### 39.6 B-形-08 の条件欄を実在の id で書き直した(2026-09-26。OBS-5f が入ったため)

行動の文と合図は**人間のもので一字も触っていない**(機械で確認)。書き直したのは条件欄と観測の区分だけ。

**使った id(4 本とも写し `scripts/playtest/records/obs-3/p4-min3-r2/00-obs_snapshot.p4.min3.r2c.json`(51 項目)に実在。値はこの席が読んで数え直した)**

| id | 写しの `path` | 読んだ値 |
|---|---|---|
| `obs.vocab.shapeStatus` | `byGroup[group].statusCounts.shape.{self,opponent}` | 自分側 none 22558・forming 5360・**completed 0**(相手側 completed 33) |
| `obs.vocab.shapeClosestPerGame` | `rows[].{closestSelfShape.shapeId, shapeBest, shapeMovedRequiredBest}` | 18 局。形別 `mutekigakoi` **16**・`ahirugakoi` 1・`nakazumai` 1。`rawBest` の最大 **0.8**(`mutekigakoi` は 0.8 が 11 局・0.6 が 5 局) |
| `obs.vocab.shapeMissingSummary` | `byGroup[group].{shapeMissingTotal, selfClosestOneAwayGames}` | **13**(`shapeMissingTotal` 31804) |
| `obs.vocab.shapeOneAwayDetail` | `rows[].closestSelfShape`(`missing` が 1 件の行)→ `{gameNo,shapeId,square,piece}` | 13 件。駒別 **銀 10**(4八 7・6八 3)・玉 2・金 1。形別 `mutekigakoi` 11・`ahirugakoi` 1・`nakazumai` 1 |

**司令塔が指示した数の使い分けを、そのまま条件欄に固定した**: **13** = 欠けがちょうど 1 枚(駒を問わない)/**10** = そのうち欠けの 1 枚が銀/**12** = 銀 2 枚のうち片方だけ来た。`12 = 10 + 2`、分母はどれも 18 局・単位は局数。**使うときは同じ文か直前の文に条件を書く**ことも本文に書いた。

**「あと 1 枚で完成に近かった」とは書かない、を本文に明記した。** この形は**必須 5 枚のうち 3 枚が初期配置の升にある**ため、「欠けが 1 枚ならその 1 枚は銀」は**半ば定義から出る**(例外は金が動いた 1 局だけ)。**定義から出ないのは 16 局(82 の形の中で最も近づいた形が同じ 1 つ)と 1 / 12 / 3 の内訳**で、この 2 つだけが指し方の結果である。

**写しから読めないものを 1 つ報告した**: **1 / 12 / 3 の内訳は、写しだけでは決まらない。** 写しが持つのは到達率(0.8 が 11 局・0.6 が 5 局)と、欠けが 1 枚のときのその 1 枚だけで、**0.6 の 5 局のうちどれが「銀 1 枚だけ来ていた」かは写しに無い**。11 = 銀 10 + 金 1、5 = 2 + 3 で**整合はする**が、内訳そのものの出どころは認識の道具の側である。冊子で数の照合をする段で効く。

**その後(2026-09-26、司令塔)**: **写しに足す方で進むことになった**(開発・診断レーンへ STEP OBS-5g。最も近づいた形が要求する銀 2 枚のうち何枚が来ていたかを局ごとに写しへ載せる)。**内訳を使わずに書く案は採らない** ― `12` は p4 の柱の数(「もう 1 枚の銀が最後まで来ない」)で、落とすと節の中身が無くなるため。**この席は、OBS-5g が入って合図が来るまで今の条件欄のまま置く**(そのとき「出どころは認識の道具の側」の一文を「写しの `obs.vocab.*` に実在する」に書き直す)。

**同じ型を送付済みの冊子で一度踏んでいる**(司令塔の申告): 53/92・34/92 は**その場で数えた数をそのまま載せたもので、どの道具も出していなかった**(CLAUDE.md ルール 5 (1) 違反)。**組んでから気づけば書き直しになっていた。** **「写しから書けないもの」は、組む前に言う**。これがこの席の役に立ち方である。

## 40. 5 人目の 25 局に戦型の認識を回した(2026-09-29。**回ったが、局の戦型に名前は付けられない**)

人間の決定(顧客が待っている・このレポートで戦型に言及する)を受けた割り当て。**回した結果の数で報告する**(推定をしない)という指示だったので、先に回した。

**やったこと**: `scripts/playtest/out/c5/pipe-3min/report/sfens.json`(局ごとの `side`・`moves`・各手の SFEN)を読み、**本人が後手の 13 局は `lib/sideAlignment.ts` の `alignMovesToSente` で本人を先手にそろえ**、`replayMoveHistory` → `analyzeOpeningFormationFromEvents`(`apps/server/src/analysis/openingDetector.ts`)に通した。台本は scratchpad の `measure/c5open.ts`(型検査 rc=0)。**相手の名前は読んでいない**(`sfens.json` の 3 欄しか読まない)。出力は `out/c5/pipe-3min/report/opening_recognition.json`(`out/` は `.gitignore` なのでコミットされない)。**認識のコードには何も足していない**(新しい判断・閾値 0)。

**定義の側**: 114 件読み込み、**認識の型を持つのは 107 件**(`data/openings` の 3 件は `recognition_pattern` が `null`。§38 の副産物のとおり)。**107 件すべて `review_status: draft`** ― 自分側 84・相手側 23。

**数(自分側。25 局)**

| 範囲 | 1 局に立った件数(中央) | 完成(中央/合計) | 完成かつ型 2 手以上(中央/合計) | 認識できず |
|---|---|---|---|---|
| 全手 | **37** | 5 / 131 | 3 / 63 | 0 局 |
| 40 手まで | 27 | 3 / 85 | 2 / 44 | 0 局 |

**「認識できず 0 局」は成功ではない。** これは §31・§36 で見つけた **P-86 の兆候**(緩い定義が全局で立ち、沈黙を消してしまう)がそのまま出たものである。立った上位は 鬼殺し 25 / 25 局・矢倉 25 / 25・英春流 25 / 25・相掛かり 24 / 25 で、**ほぼ全局で立つ**。相手側では 6筋位取り と 4四歩パックマン が **20 / 25 局で「完成」**している。

**原因は測れた ― 認識の型が短い**: 107 件の型の手数は **1 手が 34 件・2 手が 37 件・3 手が 28 件・4 手が 6 件・5 手が 2 件**。つまり「完成」の多くは**特定の 1〜2 手が現れたこと**を意味する。**閾値では救えない**: 型 3 手以上の完成に限ると **25 局中 24 局が 0 件**になり、言えることが無くなる(型 4 手以上では 25 局すべて 0)。

**今日の材料として渡せるもの**: 「完成 かつ 型 2 手以上」の自分側 id の組を局の署名にすると、25 局に **18 通り**(40 手までなら 11 通り)。**多くの局は矢倉・相居飛車寄りの同じ核**(`douke_yagura`・`onikoroshi`・`yagura_37kei`)を共有し、**少数の局だけ別の核**を持つ ― 中飛車系 2 局(`eichanryu_nakabisha` + `gosuji_kuraidori_nakabisha`)・早石田 1 局(`hayaishida`)・早繰り銀と斜め棒銀 2 局(`hayakurigin`・`naname_bogin_self`)・忍者銀 1 局。**顧客の言う「何局かは普段指さない戦型」に当たる可能性のある固まりだが、1〜2 手の型に乗った数なので、名前ではなく確かめる先として渡す**(この席は「普段指さない」の判断をしない)。

**足りないもの(次に要るもの)**

1. **型の手数が足りない。** 局の戦型を名指すには、**その戦型だけが通る手の並び**が要る。いまは 107 件中 71 件が 2 手以下で、ありふれた駒組みと区別できない。
2. **107 件すべてが `draft`。** CLAUDE.md ルール 4 により、**名前を断定的に見せられるものが 1 件も無い**。冊子では良くて「〜のような形」になる。
3. **「どれを採るか」の規則が無い。** 1 局に 37 件立ち 5 件完成する状態では、**1 つ選ぶ規則**(型の手数の下限・証拠の数・排他の関係)が要る。これは閾値 = 判断的知識なので、**この席は決めない**(司令塔・人間の承認事項)。

### 40.1 署名の案を JSON に足した(2026-09-29)。**前便の「6 局」は私の書き方が誤りだった**

司令塔の依頼で、局ごとの署名と群の欄を `opening_recognition.json` に足した(**`proposal*` の名前を付け、上位の `proposal` 欄に「案(未承認)。判定・閾値としては使わない」と書いた**)。**署名の規則**: 自分側で「completed かつ 認識の型が 2 手以上」の id の組。**核の 3 件**(`douke_yagura`・`onikoroshi`・`yagura_37kei`)は **25 局の実測で最も多く共有されていた 3 件を並べただけで、将棋の判断ではない**(その旨も JSON に書いた)。

**自己訂正**: 前便(§40)で「中飛車系 2・早石田 1・早繰り銀と斜め棒銀 2・忍者銀 1 = **6 局**」と書いたが、**厳密に数えると違う**。早石田の局は同じ署名に `douke_yagura` を、早繰り銀の 1 局は `onikoroshi` を含んでいて、**核を共有する側に入る**。また「署名が空」の局を別に数えていなかった。**正しい内訳**:

| 区分(全手) | 局数 | 局番号 |
|---|---|---|
| 多数の核を共有 | **18** | 上の 7 局以外 |
| **それ以外** | **4** | **4・13・17・24** |
| **署名なし**(署名が空) | **3** | **9・10・18** |

**それ以外 4 局の中身**: 局 4 と 局 17 が同じ署名(英ちゃん流中飛車 + 5筋位取り中飛車 + 角換わり腰掛け銀。**すべて型 2 手**)、局 13 が 忍者銀(型 2 手)、局 24 が 早繰り銀 + 4六銀左戦法(型 2 手)。**どれも型 2 手の定義に乗った数なので、名前ではなく確かめる先である。**

**40 手までとの食い違い(依頼 2)**: 区分は 多数の核 18・それ以外 3・署名なし 4 で、**区分が変わる局は 1 局だけ ― 局 24**(40 手までは署名なし → 全手では「それ以外」)。署名そのものが同じ局は **14 / 25**(別々の署名は 全手 18 通り・40 手 11 通り)。**つまり「どの局が他と違うか」の顔ぶれは、手数を切っても 1 局しか動かない。**

**型 3 手以上の完成が残る 1 局(依頼 3)**: **局 7 の自分側 `henachoko_kyusen`(へなちょこ急戦)、型 3 手・証拠 3**。これが 25 局で唯一、型 3 手以上の定義が完成した例である。

**この節の限界**: 署名は draft の定義・型 2 手に乗っている。**顧客の冊子では「〜のような形」までしか書けない**(107 件すべて `draft`)。群として渡すのは、盲検で先に固定するため(司令塔の指示)。

### 40.2 人間の決定 ― 署名の分け方は顧客向けの分類として承認されず、**盲検候補として保持**(2026-09-29、司令塔より伝聞)

**承認されなかった**: 「完成 + 型 2 手以上の署名で分ける」を**顧客向けの分類規則としては使わない**。理由は 3 つ ― (1) 107 の定義がすべて下書きで**断定できる戦型が 0 件**、(2) 「型 2 手以上」「多数の核 vs それ以外」は**今回の 25 局を見て作った判断値**、(3) 「他と違う局 = 普段指さない戦型」は**まだ盲検前**。**顧客には戦型と断定しない。** 納品後に本人の答えと照合し、一致したら次回以降の定義の根拠にする。**既存指標の群ごとの再集計までは進めてよい。**

**この席がしたこと**: JSON に `useOfThisFile` の欄を 1 つ足した(「**これは顧客向けの分類ではなく盲検候補である**(人間の決定 2026-09-29)」+ 上の理由 3 つ + 使ってよい範囲)。数は変えていない。

**人間の評価**: この結果は「**戦型認識を今すぐ顧客向け分類に使うのはまだ早い**」ことを**機械的に確かめた**ものとして有用、とのこと。**沈黙 0 を成功と報告しなかったことが、そのまま役に立った。**

**Phase 2 ① としてこの席に与えられた方向(着手は人間の判断待ち)**: 「戦型を認識できるか」と「顧客向けの分類軸として使えるか」は**別問題**である。**どういう戦型定義なら 3 手以上のまとまりとして安定して認識できるかを、知識として育てる。** 材料は今回の 25 局と 4 人分の棋譜。§40 で測った型の手数の分布(1 手 34・2 手 37・3 手 28・4 手 6・5 手 2)が出発点になる。

**司令塔へ返した食い違い 1 件**: 決定の文が「**6 局**に分ける」「6 局は盲検候補」と言っているが、**§40.1 の訂正後の数に 6 という区分は無い** ― 「それ以外」**4 局**(4・13・17・24)と「署名なし」**3 局**(9・10・18)で、合わせると 7 局である。**6 は訂正前の私の誤った数**なので、再集計の群をどちらで組むかを確かめる必要がある(この席の推奨は、**4 局を候補とし、署名なしの 3 局は別に持つ** ― 署名が空なのは「普段と違う」ではなく「この語彙では何も言えない」であり、混ぜると突き合わせで解釈できなくなるため)。

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

