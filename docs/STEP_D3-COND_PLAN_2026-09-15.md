# STEP D3-COND 計画(骨組み): 事実から、名前つきの条件式で死因候補を「該当 / 非該当 / 判定不能」と判定し、局をまたいで数える(2026-09-15)

**状態**: 骨組みの計画(**司令塔の決定(版 `1c72f9c0`): Q-1〜Q-6 はすべて推奨どおり。Q-4 は「材料 / 試す / 3 人目で確定」の 3 段で確定**(4.))。**事前読み f2 の REVISE(版 `864fdaef`、必須 R-1〜R-4・推奨 S-1〜S-5)を司令塔の決定で取り込んだ。f2 の判定は版 `6c07d1d1` で GO(条件 C-1 = K-9 の向き、取り込み済み)**(往復は 1 回。残った点 N-1〜N-5 は既知事項の候補として 9. に。N-5 は司令塔の決定つき ― 取り込み先は 10.)。コミットは 20 局版の前後どちらでもよい。
**書いた人**: A(sgogi-coach-64、司令塔の依頼)。**エンジンは使っていない。**基点 HEAD `58b540a`。
**経緯**: 人間「D3 の計画は D2 の結果を見てから?」→ 司令塔「条件式の中身は見てから、骨組みは先に」→ 人間「任せます」。**この計画は条件式の中身(定義の文・閾値)を 1 つも決めない。**中身は 5. の手順で、20 局版レポートの後に人間が承認する。
**番号**: `D3-COND`(司令塔の命名)。`STEP D3`(仮想人間 20 局)とは別。上位構想 8. のロードマップの「D3」の中身にあたる。

## 0. 実物から分かった前提

| # | 事実 | 場所 |
|---|---|---|
| E-1 | **判断の 4 つの層**(1 測る事実 / **2 事実から条件式で導ける死因候補** / 3 反事実の差 / 4 人間の判断)。2 は「条件に該当」とだけ言い、「この人は〜した」とは言わない。人間の役割は定義の承認と低信頼の代表例の判定 | `docs/DIAGNOSIS_CONCEPT_2026-09-14.md` §7.3 |
| E-2 | **調査価値の数の基準**: 実在の 1 人の 20 局以上で、同じ発症条件の**急落**が 3 件以上、うち 2 件以上で本人が「危ないと思っていなかった」と答え、その局を落としたか 5 手以内に自玉へ王手か詰み。結果を見てから基準を選ばない | 同 §7.2 |
| E-3 | 今ある死因の規則は `candidateModes` の `mate_threat`(draft)だけ。スキーマは `mode` を const、`matchedBy` を列挙で固定 | `scripts/playtest/lib/failureEvent.ts:315`・`:410`、`scripts/playtest/schemas/failure-event.v0.4.schema.json` |
| E-4 | **`BranchKind` のうち急落は `cpDrop`・`mateDrop` だけ。`matedIfPass` は「急落」と呼ばない**。rise・maxDrop の行も急落ではない | `lib/failureEvent.ts:289-290`・`lib/diagnosisMoment.ts` |
| E-5 | **欄の「無い」は欄ごとに意味が違う**: 状態の語は `Evaluation`(measured と 5 つ)・`FocusState`(stated・nothingToSay は値、pending・unrecorded)・`ShapeState`(recorded / unrecorded)・`Counterfactual`(compared と 7 つ)・`KingEscapes`(counted / noKing・opponentInCheck)。**null が「無かった」という値の欄**(`consequences.mate`・`actual/pv.mate`・`gameEnd`・`pvTruncatedAtPly`・`failureEventBranchPly`・`trigger.kingSurroundings`)と、**「数えられない」の欄**(`pvMinusActual.kingEscapes`・`kingSurroundingsOwn`・`kingEscapesChangeFromRoot`)がある。**`consequences.windowShort: true` のとき `checks: []`・`mate: null` は「起きなかった」ではない** | `lib/failureEvent.ts:60-88`・`:228-258`・`lib/counterfactual.ts:45-123`・`lib/diagnosisMoment.ts:37-78` |
| E-6 | §7.3 の「今後追加」の物差し(攻撃駒数・守備駒数・利き・速度・脅威)は**まだ記録にも Event にも無い** | §7.3 の 1. |
| E-7 | 実棋譜: **1 人目** 10 局のうち先手 6 局を評価済み(`records/real-01`)。**その評価値・急落 5 件・Event は、REAL-01 計画 §6・D1b 計画 E-11・コミット済みの試験にあり、司令塔・C・f2・A が見ている**。後手 4 局は未評価。**2 人目** 20 局のうち先手 9 局を評価済み(`records/real-02`)、後手 11 局は REAL-03 | 各 `records/*/README.md`・`docs/STEP_REAL-02_PLAN_2026-09-15.md` |
| E-8 | 終局は STEP D0-KIFU3 で固定棋譜 JSON に `ending { kind, ply }` だけを残す(**勝った側・手番の側は持たない**)。`records/*/README.md` の勝ち負けは、棋譜を用意した側の一覧 | `docs/STEP_D0-KIFU3_PLAN_2026-09-15.md` E-1・`records/real-02/README.md` |

## 1. 位置づけと範囲

- §7.3 の **2.** を実装する形と、§7.2 の数の基準に渡す**入力**を作る。**§7.2 の判定そのもの(本人の回答を含む)はしない**(回答は D4)
- 範囲: 読める欄の表・定義の読み込み・判定・集計・出力の契約・見張りの型・過学習の歯止め・手順。**条件式の中身・閾値は範囲外**(承認後に別 STEP で 1 定義ずつ足す)
- `apps/`・`data/` に触らない。LLM を判定に使わない。評価語を書かない(「該当」「非該当」「判定不能」だけ)

## 2. 条件式の型(純粋関数)

**定義**(1 件 = 1 ファイル。**draft の判断的知識**。CLAUDE.md ルール 4): `id`(例の形だけ `example_condition_v1`)・`label`(必ず「(仮)」)・`status: "draft" | "approved"`・`definitionText`・`uses`(読む欄のパス)・`thresholds`・`appliesTo`(`failureEvent` / `rise` / `maxDropPair` の部分集合)・`approval`(`approvedBy`・`date`・`record`。draft は null)・`evaluate(view) → boolean`。**`definitionSha256` = 定義のファイルのバイト列の sha256**。

**読み込み(`loadCondition`)で止める**(R-4): approved なのに approval が null / draft なのに approval がある / label に「(仮)」が無い / `uses` に**下の表に無いパス**がある / `appliesTo` が空。

**読める欄の表 `READABLE_FIELDS`(R-1。骨組みで決める。行を足すのは骨組みの変更 = 監査を経る)**: パスごとに (1) **門**(値を読む前に満たすべき祖先の状態) (2) **null の意味**(値 / 判定不能)を持つ。最初の行:

| パス(の群) | 門(満たさなければ判定不能。理由 = 門の実際の状態) | null の意味 |
|---|---|---|
| `trigger.evaluationBefore.*`(`scoreCp`・`mate`・`bestmove`・`afterPassScoreCp`・`afterPassMate`・`dropCp`) | `evaluationBefore.state === "measured"` | 値(cp が null なら詰みの読み、`dropCp` の null は「両方 cp でない」) |
| `trigger.focus.state` | `state` が `stated`・`nothingToSay`(**nothingToSay は値**) | ― |
| `trigger.shape.status` | `shape.state === "recorded"` | ― |
| `trigger.opponentIntent.classification`・`trigger.kingSurroundings.*` | ― | `kingSurroundings` の null は値(玉が無い) |
| `branch.kinds`・`branch.diffCp`・`branch.mateAfter` | ― | `diffCp`・`mateAfter` の null は判定不能(その組は差・詰みを取っていない) |
| `consequences.checks`・`consequences.mate` | **`consequences.windowShort === false`** | `mate` の null は値(窓に詰み無し) |
| `counterfactual.*`(`actual`・`pv`・`pvFirstMove*`・`pvBounded`・`comparedPlies`) | `counterfactual.state === "compared"` | `actual/pv.mate`・`gameEnd`・`kingSurroundingsEnd`・`pvTruncatedAtPly` の null は値 |
| `counterfactual.*.kingEscapes*.count` | 上の門 **かつ** その `KingEscapes.state === "counted"` | ― |
| `counterfactual.pvMinusActual.*`・`kingEscapesChangeFromRoot.*` | `counterfactual.state === "compared"` | **判定不能**(数えられない) |
| `failureEventBranchPly`(rise・maxDropPair) | ― | 値(同じ組の Failure Event が無い) |

`opponentBestmove`(いつも notInRecord)・`provenance` は表に入れない(読めない)。

**判定 `judgeCondition(definition, input)`**:
- `appliesTo` に無い種類の入力 → **判定しない**(行を作らない)。**maxDrop の状態の行(noDrop・noComparedPair)は判定せず、「判定しない行」として数だけ出す**(R-4)
- lib が `uses` の各パスを表で読む。門を満たさない・null が判定不能の欄 → `{ state: "undecidable", missing: [{ path, reason }] }`
- すべて読めたら、**`uses` のパスだけを持つ写し(view)を作って `evaluate` に渡す**(入力を丸ごと渡さない。外の欄は `undefined`)→ `{ state: "match" | "noMatch", usedValues: view }`

## 3. 集計(1 人ぶん)

- 入力: 1 人ぶんの記録の一覧。**人は呼び出し側が `--person <ラベル>` で渡す**(推測しない)。**入力の局の数と先手 / 後手の内訳**(meta の `mirrored`)を先に出す(§7.2 の「20 局以上」はこの数)
- 条件ごとの**全体の列**: 該当・分母(該当 + 非該当)・判定不能(理由の内訳。分母に入れない)・判定しない行の数・該当の一覧・該当があった局の数
- **§7.2 用の列(別に出す ― R-3)**: 入力を **`kinds` に `cpDrop` か `mateDrop` がある Failure Event に限る**(`matedIfPass` だけの Event・rise・maxDrop は入れない)。同じ条件の該当の件数と、並べるだけの 2 項目:
  - **5 手以内の王手・詰み**: `consequences` から「あり / なし / 窓が足りない(windowShort)」
  - **その局を本人が落としたか**(D0-KIFU3 の後): `ending` が `resign`・`timeUp`・`mate` なら、`ending.ply` の手番(奇数 = 先手)と meta の `originalUserSide`(無ければ先手)から「落とした / 落としていない」。**ほかの種類は「決まらない」、`ending` が無ければ「記録に無い」**。README の勝ち負け(用意した側の一覧)は**別の列として並べ、食い違えば「食い違い」と出す**(どちらかに寄せない)
  - 「3 件以上か」「20 局以上か」は数として出すだけで判定語にしない
- **重なり(R-3)**: 同じ定義の中で、同じ組 **(kifuId, branchPly)** は 1 回だけ数える(maxDropPair の行の `failureEventBranchPly` が null でなければ、Failure Event と同じ組)。数えた入力の種類を一覧に書く
- 同じ `--person` の中に同じ kifuId が 2 本なら止める

## 4. 過学習の歯止め(**先に決めて書く**)

**3 段(司令塔の決定)**:
1. **材料の側 = 2 人目の 20 局**(見た側)。§7.2 の数は材料の側の数として出し、**「調整した側の数」と必ず併記**
2. **試す側 = 1 人目の 10 局**。**先手 6 局(もう見た局。E-7)と後手 4 局(未評価 = 盲検)を分けて、予測も集計も別々に出す**(R-2・司令塔の決定)。6 局は歯止めとして弱いと表に書く
3. **§7.2 を汚れていない側で満たす最初の機会は 3 人目の 20 局**。来たら試す側を移し、1 人目は材料に戻してよい。それまでの §7.2 の判定は仮で、人間には「材料の側の数」と明記する

- 条件式を材料の側で作る・調整するたびに、試す側の件数(該当・分母・判定不能)を 6 局と 4 局で別々に**予測として先に書く**。予測は **`definitionSha256` と組**にし、**書いた人と、その人がそれまでに見たもの**(記録・レポート・計画の節)を書く
- **置き場は、この計画書の 11.(コミットされる場所。司令塔の決定)**。定義を変えたら、その予測の行は消さずに「捨てた」と書き、新しい行を足す
- 3 人目が来るまでの歯止めは (1) 試す側の予測の当たり外れ (2) **D4 の本人の回答**(最終)。後手 4 局は、定義を作る前に誰も開かない

## 5. 手順(この順を飛ばさない)

1. 20 局版レポート(real-02・real-03)
2. D2 の「どの物差しに差が出たか」の表を人間に見せる
3. 物差しの追加(E-6)の要否を**人間が決める**(足すなら別 STEP で、記録・Event・2. の表の行を先に)
4. 条件式の候補を司令塔が起こす(定義の文・`uses`・閾値・材料の側での件数)→ **人間が 1 件ずつ承認**(承認前は draft のまま集計してよいが、出力に draft を必ず出す)
5. 実装(骨組み + 承認された定義)→ 監査 → 11. に予測をコミット → 試す側で測る

## 6. 出力の契約

- **別ファイル `--events-cond <out.jsonl>`**、契約 `diagnosis-condition` v0.1、スキーマ `scripts/playtest/schemas/diagnosis-condition.v0.1.schema.json`(S-4)。1 行 = (入力 1 件 × 定義 1 件)の判定。欄: `contract`・`schemaVersion`・`kifuId`・`eventClass`・`branchPly`・`condition { id, label, status, definitionSha256 }`・`result`(2. の形)・`provenance`(Failure Event と同じ)
- **集計 `--cond-summary <out.json>`** にも `contract: "diagnosis-condition-summary"`・`schemaVersion` を必須で置く(S-5)。**Markdown の節と要約の両方に、条件ごとの `status` と「(仮)」を必ず出す**(S-3)
- Failure Event の列挙・`candidateModes` は変えない

## 7. 見張りの型(骨組みの分はここで決め、定義ごとの分は承認後に埋める)

**骨組みの固定例**(試験だけの架空の定義 `test_only_*`。将棋の判断を含めない):
- K-1 読める入力 → match / noMatch、`usedValues` は `uses` のパスだけ
- K-2 門と null: `evaluationBefore` が notMeasurable → 判定不能(理由つき)/ `focus` が nothingToSay → 値として読める / `consequences.mate` null かつ windowShort false → 値 / **windowShort true → 判定不能** / `failureEventBranchPly` null → 値 / `kingEscapesEnd` が noKing で `.count` を使う → 判定不能 / `pvMinusActual.kingEscapes` null → 判定不能
- K-3 集計: match 2・noMatch 1・undecidable 4 → 分母 3・局の一覧
- K-4 `appliesTo` に無い入力・maxDrop の状態の行 → 判定しない(数だけ)
- K-5 読み込みで止める: approved で approval null / draft で approval あり / label に(仮)が無い / `uses` が表に無い
- K-6 同じ `--person` に同じ kifuId の 2 本 → 止める
- K-7 `uses` の外を読む架空の定義(外の欄が `undefined` なら真を返す)→ match
- K-8 `definitionSha256`: 定義のファイルを 1 バイト変えると変わる
- K-9 §7.2 用の列: `matedIfPass` だけの Event・rise は入らない / maxDropPair と Event が同じ組なら 1 回 / 終局 resign・ply 奇数・先手の局 → 「落とした」(ply 偶数・先手の局 → 「落としていない」)、`abort` → 「決まらない」、`ending` 無し → 「記録に無い」、README と食い違い → 「食い違い」
- K-10 試す側の集計: 先手 6 局と後手 4 局が別の列に出る(混ぜた合計だけにしない)

**骨組みの変異(中心)**: 判定不能を noMatch に畳む(K-2・K-3)/ **門を外す(windowShort を見ない)**(K-2)/ **null を一律に判定不能にする・一律に値にする**(K-2)/ 分母に判定不能を入れる(K-3)/ **`evaluate` に入力を丸ごと渡す**(K-7)/ 読み込みの確かめを外す(K-5)/ **`definitionSha256` を id から作る**(K-8)/ §7.2 用の列に `matedIfPass` だけの Event を入れる・同じ組を 2 回数える(K-9)/ 二重の kifuId を通す(K-6)/ 6 局と 4 局を合わせて 1 列にする(K-10)。

**定義ごと(承認後に埋める。この表の中身は空欄のまま)**: 固定例 = 該当の境目・非該当の境目・判定不能 各 1 以上 / 変異 = 閾値の向き・`uses` の欄を 1 つ外す / 予測 = 11. の行。

| 定義 id | 承認の記録 | 固定例 | 変異 | 11. の予測の行 |
|---|---|---|---|---|
| (承認後に埋める) | | | | |

## 8. 決定(司令塔、2026-09-15: Q-1〜Q-6 は推奨どおり。R-2 の置き場も司令塔の決定。表は決定の前の選択肢)

| # | 点 | 決定 | ほかの案 |
|---|---|---|---|
| Q-1 | 番号 | `D3-COND` | `D3` を名乗る |
| Q-2 | 出力 | 別ファイル・別契約 `diagnosis-condition` v0.1 | Event に欄を足す(v0.5) |
| Q-3 | 定義の置き場 | `scripts/playtest/lib/conditions/`(1 件 1 ファイル) | `data/conditions/` |
| Q-4 | 材料と試す側 | 4. の 3 段(試す側は先手 6 局と後手 4 局を分ける。判定は 3 人目の 20 局まで仮) | 逆 |
| Q-5 | 分母 | 該当 + 非該当。判定不能は内訳つき | 全件 |
| Q-6 | 人の区別 | `--person` で渡す | フォルダ名から推す |
| Q-7 | 予測の置き場 | この計画書の 11.(捨てた行も残す) | 別のフォルダ |

## 9. やらないこと・限界

- 条件式の中身をこの計画で決めること。例として書いた id・パスを定義に使うこと。LLM による判定。評価語と「この人は〜した」
- 本人への質問(D4)・§7.2 の判定そのもの。`candidateModes` と Failure Event の列挙を変えること。エンジンを回すこと
- **限界**: `--person` に 2 人を混ぜて渡しても検出できない(S-2)。1 人目の先手 6 局は見た局なので、試す側としては弱い(4.)。「落とした」は終局の 3 種類からしか決まらない(E-8)
- **既知事項の候補(f2 の判定、版 `6c07d1d1`。登録と番号は司令塔)**
  - N-1 読める欄の表に「そのパスを持つ行の種類」が無い(rise・maxDropPair は branch・action を持たない)。`appliesTo` に複数の種類を持つ定義で、無いパスをどう扱うかは未定
  - N-2 `counterfactual` の門は `compared` だけ。`comparedPlies` が窓より短い(棋譜の終わり・短い読み筋)と、mate・gameEnd の null は「その手数の中で無かった」で、窓の中ではない(windowShort と同じ型)
  - N-3 `trigger.opponentIntent.classification` の undetermined(理由つき)に門が無く、値として読まれる
  - N-4 §7.2 の「落としたか」の入力(固定棋譜 JSON の `ending`・README の表)を集計へどう渡すかが書かれていない
  - N-5 **決定(司令塔)**: 1 人目の後手 4 局(real-03 g3)の Failure Event・rise・maxDrop の中身は、D3-COND の定義が人間に承認されるまで、C(状態の数だけ)と f2(監査)以外は見ない(司令塔・A・人間も)。ミサカさんの 10 局版レポートは定義の承認の後。records/real-03 のコミットと README は g3 の件数(急落・優勢・王手・死因①)までは載せてよい

## 10. 事前読み f2(版 `864fdaef` の REVISE)と司令塔の決定の取り込み

| 指摘 | 取り込み先 |
|---|---|
| **R-1(必須)** 判定不能の規則が状態の語・null の意味・windowShort に合わない | E-5・2. の読める欄の表と判定・K-2・変異(門を外す・null を一律に) |
| **R-2(必須)** 試す側の先手 6 局はもう汚れている | E-7・4. の 2(6 局と 4 局を分けて予測・集計)・予測を書いた人と見たもの・置き場 = 11.(司令塔の決定)・K-10 |
| **R-3(必須)** §7.2 への入力が文と合わない | E-4・E-8・3. の §7.2 用の列(急落に限る・20 局は入力の局数・窓が足りない・落としたかは KIFU3 の後で決め方と README の列)・重なりの規則・K-9 |
| **R-4(必須)** 骨組みの見張りが中心を覆わない | 2. の view を渡す・`definitionSha256` の対象・読み込みの確かめ・maxDrop の状態の行・K-4・K-5・K-7・K-8 と変異 |
| S-1 例の id・パスが攻め急ぎに近い | 2. の例を `example_condition_v1` に |
| S-2 2 人を混ぜる | 9. の限界 |
| S-3 Markdown に status と(仮) | 6. |
| S-4 スキーマの場所 | 6. |
| S-5 要約の契約 | 6. |

## 11. 予測の記録(**定義ごとに、測る前に足す。消さない**)

| 日付 | 定義 id | definitionSha256 | 書いた人 | その人が見たもの | 先手 6 局の予測(該当・分母・判定不能) | 後手 4 局の予測 | 状態(有効 / 捨てた) |
|---|---|---|---|---|---|---|---|
| (承認後に足す) | | | | | | | |

## 12. 実装の記録(骨組みの lib 側。実装担当 1e、2026-09-16)

**範囲(司令塔 e3 と確認)**: この計画の §2・§3 と、D4 計画(`7d6529d`)の §3「D3-COND への改訂」を lib 側だけ実装した。**入れていないもの**: D4 本体(`allPairsOf`・`gateTallyOf`・Gate。K-11 と G-F*)、§6 の出力の契約 `diagnosis-condition` v0.1 のスキーマと `diagnose.ts` の `--events-cond`・`--cond-summary`(B の D-SCREEN-2 のコミットの後に、その HEAD へ載せ替えてから足す)、条件式の中身(1 本も書いていない)。基点 `7d6529d`。**エンジンは使っていない。**

### 12.1 足したファイル(既存のファイルは 1 本も変えていない)

| ファイル | 中身 |
|---|---|
| `scripts/playtest/lib/condition.ts` | 行と定義の型(`ConditionRowKind` に `pair`、`PairRow` は型だけ)・`READABLE_FIELDS`・`checkCondition` / `loadCondition`・`judgeCondition` / `judgeConditionPvSide`・`conditionTallyOf` / `testSideTallyOf`・`userSideOf`・`lostByEndingOf` |
| `scripts/playtest/lib/condition.test.ts` | 固定例 35 件(K-1〜K-10、K-12a・K-12b・K-13・K-14、表の種類の列と印) |
| `scripts/playtest/lib/conditionFixtures/test_only_loadable.ts` | `loadCondition` を当てる試験だけの架空の定義(本番の置き場 `lib/conditions/` には置かない) |

### 12.2 計画に書いていなかった判断(計画と違えた点は無い)

- **J-1 定義のファイル**: TypeScript のモジュールの `export default`。`loadCondition(path)` はバイト列を読んでから動的 import し、確かめは純粋関数 `checkCondition(value, bytes)` に分けた(K-8 はバイト列で当てる)
- **J-2 読み込みの確かめ**: 形の崩れ(`malformed`: 欄の型・`evaluate` が関数か)を先に見て、崩れていればそれだけを出す。そうでなければ §2 の R-4 と D4 §3 の問題を**全部並べて**止める(最初の 1 つで止めない)。コードは `approvedWithoutApproval`・`draftWithApproval`・`labelWithoutProvisional`・`emptyAppliesTo`・`unknownPath`・`pathNotInKind`・`afterRowFieldWithPair`・`actualKeptFieldWithPair`
- **J-3 表の行**: 群(`*`)ではなく葉のパスを 1 本ずつ並べた(`uses` は表のパスと完全に一致するときだけ通る)。§2 の表の群に加え、**D4 §3 が表にあることを前提にしている欄**を足した: `action.*`・`branch.matedIfPassAfter`・`branch.evaluationAfter.*`・`branch.standingPair.{before,after}`・`evaluationAfter.*`・`standingPair.{before,after}`・`change.*`・`moves.*`・`userBestmoveAtBefore`・`counterfactual.state`・`counterfactual.{windowPlies,actualPlies,pvLength,pvUsablePlies}`。§2 の「null の意味 ―」の欄は `notNullable`(型が null を持たない。来たら例外)
- **J-4 途中の null**: パスの途中が null なら値は null とし、その欄の null の意味を当てる(`trigger.kingSurroundings.own` は値の null、`trigger.positionFacts.zonePieces.ownKingZone.bySente` は判定不能)
- **J-5 判定しない順**: `appliesTo` に無い種類を先に見て、次に最大の下がりの状態の行(`maxDropPair` を含まない定義では状態の行も `kindNotApplied`)
- **J-6 読み筋の側**: 当てられない理由は 2 つとも並べる(`noActualPath`・`pathNotReplaceable`)。そのまま読む欄は D4 §3 の列挙どおり(`trigger.*`・`standingPair.before`・`moves.*`・`userBestmoveAtBefore`・`counterfactual.state`・`counterfactual.comparedPlies`・`counterfactual.kingEscapesRoot.count`)。**`counterfactual` の外の欄(`branch.*`・`consequences.*` など)も置き換えの表に無いので当てられない**(pair を含む定義では読み込みで先に止まる)。門も読み筋の側のパスで見て、欠けた欄の名前は元のパスで出す
- **J-7 同じ組**: 局の中で Failure Event → 最大の下がりの組 → 上がりの順に見て、先に判定した組を数える。同じ組で判定が食い違えば例外(共通の欄は同じ関数の値なので食い違わないはず)
- **J-8 判定不能の内訳**: (欄, 理由) ごとの行の数。1 行が複数の欄で判定不能なら、それぞれに数える。理由の文は `門のパス=実際の値`・`null`・`undetermined:理由`
- **J-9 §7.2 の 5 手以内**: 王手か詰みが 1 つでもあれば、窓が足りなくても「あり」(起きたことは起きた)。無くて窓が足りなければ「窓が足りない」、無ければ「なし」
- **J-10 落としたか**: 入力は局ごとに `{ kifuId, userSide, ending, listedResult }` を呼び出し側が渡す(N-4。ファイルからの集め方は `diagnose.ts` 側)。`ending` のキーが無い・`null` はどちらも「記録に無い」、`unreadable` は「決まらない」。ply は固定棋譜 JSON の元の手数のまま読む(回した局でも `ending` は写すだけ)。README の列は `win` / `loss` / 載っていない、「食い違い」は両方が決まったときだけ
- **J-11 本人の側**: `userSideOf(meta)` は `mirrored` と `originalUserSide` が食い違えば例外。試す側の 2 列(`testSideTallyOf`)は、列と本人の側が食い違う局・両方の列にある kifuId で止める。後手の列は空でよい(g3 は開かない)

### 12.3 測った結果(予測は実装・実行の前に書いた。`scratchpad/d3cond/predict-impl.txt`)

- 型検査 `typecheck:scripts` rc 0。`condition.test.ts` 35/35。全体 49 本 699/699(基点は 664)
- 予測は、ファイルの本数だけ外れた(予測 47 本・実際 49 本。基点の本数の読み違え)。ほかは当たり
- 変異 32 本(計画 §7 の骨組みの変異・D4 §3 の 3 つ・実装担当が足した分): **予測どおり 32/32、鳴った 32/32**、戻り一致。予測の表は実行の 1 行目(`predictions sha1 af79c35e`)
- `loadCondition` を tsx でも当てた(試験の外の確認。既知の正解 = id とファイルの sha256 で校正して一致、形の崩れた定義は `ConditionLoadError`)

### 12.4 既知事項の候補(登録と番号は司令塔)

- 9. の N-2(`comparedPlies` が窓より短い)・N-3(`opponentIntent.classification` の undetermined に門が無い)は計画のまま残る
- 落ちる試験が 1 本だけの変異が多い(M-2・M-5・M-7a〜d・M-9〜M-13・M-14b・M-17・M-20・M-22・M-24〜M-27)
- `notNullable` の欄に null が来たときの例外は試験していない(型が null を持たないので、今の行では起きない)
- 実戦の側では `counterfactual.pv.*` を読めるが、読み筋の側では置き換えの表に無いので当てられない。読み筋を読む定義の読み筋の側の意味は計画に無い

### 12.5 監査 C の GO の条件 C-1・C-2 の取り込み(試験を足しただけ。`condition.ts` は変えていない)

- **C-1** `appliesTo` が 2 種類以上の定義の固定例を 2 つ足した: `["failureEvent","pair"]` + `branch.standingPair.before` → `pathNotInKind` は pair の分だけ / `["rise","pair"]` + `evaluationAfter.scoreCp` → `afterRowFieldWithPair`
- **C-2** `READABLE_FIELDS` の null の意味と門を、印の列挙の試験と同じ形で固定した(null の意味ごとのパスの一覧・門の並びごとのパスの一覧。期待は §2 の表と 12.2 の J-3 から手で書いた)
- 取り込みの確かめ: C の変異 C-01〜C-07(C の道具 `mutate_c.py` の、S と W の 2 行だけを替えた写し)が 7 本とも鳴った。落ちた試験は予測どおり(C-01・C-02 → C-1、C-03・C-04 → C-2 の null の意味、C-05〜C-07 → C-2 の門)。`condition.test.ts` 38 件・全体 702/702・型検査 rc 0
- **定義を起こすときに人間へ伝えること**: 実戦の側で `counterfactual.pv.*` を読む定義は、読み筋の側の判定(D4 の G-3)が常に当てられない(notEvaluable)
- 12.4 の候補のうち、`notNullable` の例外の経路は司令塔が P-60 に登録する(JSONL から読んだ行では型が効かず、古い版の Event で当たる)。「落ちる試験が 1 本だけの変異」は登録しない

### 12.6 実装の記録(diagnose.ts 側。実装担当 1e、2026-09-16)

**範囲**: §6 の出力の契約と `diagnose.ts` の口。基点は `ae74ec1`(lib 側のコミット。D-SCREEN-2 `90ea1f1` の後)。lib/condition.ts は変えていない。**エンジンは使っていない。**条件式の中身は 0 本(試験だけの架空の定義を 2 本足した)。

| ファイル | 中身 |
|---|---|
| `scripts/playtest/diagnose.ts`(足しただけ) | 旗 `--conditions <dir>`・`--person <p1 の形>`・`--events-cond <out.jsonl>`・`--cond-summary <out.json>`・`--kifu-dir <dir>`・`--listed-results <file.json>`。定義は表を書く前に読み、表の後に条件式の節を書く。main は非同期(末尾は `main().catch`) |
| `scripts/playtest/lib/conditionReport.ts`(新) | `--events-cond` の行(`conditionLinesOf`)・集計の JSON(`conditionSummaryOf`)・条件式の節(`renderConditionSection`)・定義のディレクトリ・§7.2 の材料・`--person` の確かめ・スキーマの読み込み |
| `scripts/playtest/schemas/diagnosis-condition.v0.1.schema.json`(新) | 契約 diagnosis-condition v0.1。`provenance` は Failure Event v0.6 のスキーマから値のまま写した(試験で一致を見る) |
| `scripts/playtest/lib/schemaVersions.ts`(足しただけ) | `DIAGNOSIS_CONDITION_SCHEMA_VERSION`・`KNOWN_DIAGNOSIS_CONDITION_SCHEMA_VERSIONS`・`DIAGNOSIS_CONDITION_SUMMARY_SCHEMA_VERSION` |
| `scripts/playtest/lib/conditionFixtures/test_only_always.ts`・`test_only_focus_stated.ts`(新) | 試験だけの架空の定義(いつも真 / ③の状態の門で判定不能になる) |
| `scripts/playtest/lib/conditionReport.test.ts`(新)・`scripts/playtest/diagnose.test.ts`(足しただけ) | 11 件 / 2 件(子プロセス: 旗をそろえた回・旗の組み合わせの誤り)とソース照合の 5 行 |

**計画に書いていなかった判断**(計画と違えた点は無い):
- **J-12 旗**: `--conditions` は `*.ts`(`*.test.ts`・`*.d.ts` を除く)をファイル名の順に読み、1 つも無い・同じ id が 2 つなら止める。`--person` は `--conditions` に必須で、**`p` と数字の記号だけ**を受ける(D4 の S-8。人の名前を出力に書かない)。ほかの条件式の旗は `--conditions` と一緒でなければ止め、値の無い旗も止める(どれも表を書く前)
- **J-13 §7.2 の材料**(N-4): `--kifu-dir` は固定棋譜 JSON の `id` → `ending` だけを読む(手は読まない)。`--listed-results` は README の表を人が写した `{ kifuId: "win" | "loss" }`(README の文は読まない)。渡さなければ「記録に無い」「載っていない」
- **J-14** `--conditions` を渡すと、`--events*` が無くても moment と出どころを組み立てる(記録の meta が出どころに写せない形なら、表の後に exit 1 ― K-3 と同じ)
- **J-15** 条件式の節は `--conditions` を渡したときだけ、表(と合計の節)の後に書く。渡さなければ標準出力と 3 つのファイルは変えない
- **J-16 行の並び**: 記録 → 入力(Failure Event → 上がり → 最大の下がり。ファイルの順)→ 定義(ファイル名の順)。判定しない行は書かない。種類をまたいで同じ組の行は、それぞれの入力の行として書く(1 回だけ数えるのは集計)
- **J-17 出どころの選び方**: 行と集計は `--events`・`--events-rise`・`--events-maxdrop` と同じ行に当てる(D-SCREEN-2 の組ごとの深い / 軽いの選び方のまま)。D4 の「軽い値だけ」は gate.ts の決まりで、ここには当てない
- **J-18 集計の JSON**: `contract`・`schemaVersion`・`person`・`inputs`(根からの相対のパス・sha256・kifuId・数えたか)・`sources`・`analysis`(gitHead・dirty)・`conditions`(条件ごとの集計)。**スキーマのファイルは置いていない**(欄の並びと契約の欄は試験で見る)。「数えた局」は error 行の記録・数えられなかった記録を入れない
- **J-19 スキーマ**: `condition.label` は「(仮)」を含む・`id` は `^[a-z][a-z0-9_]*$`・`definitionSha256` は 64 桁・`missing` は 1 件以上・理由は 3 つの形の oneOf・`usedValues` は object だけ(中身の形は定義ごとに違うので見ない)

**測った結果**(予測は実装・実行の前に書いた。`scratchpad/d3cond2/predict-diag.txt`): 基点 `ae74ec1` で型検査 rc 0・全体 53 本 771/771(lib 側のコミットは 758。足したのは conditionReport 11・diagnose 2)・check-docs rc 0。予測の外れは 2 つ: 基点 90ea1f1 に写した直後の「手で書いた行に型エラーが出る」(D-SCREEN-2 の欄は任意だったので 0)と、1 回目の全体で子プロセスの試験 1 件が落ちた(見出しを確かめる `new RegExp` の文字列が正規表現として例外。試験の書き方の誤りで、行の確かめに直して 771/771)。変異 18 本(conditionReport.ts 10・diagnose.ts 5・スキーマ 3。判定しない行を書く・並び・eventClass・終局を引かない・キーの無い ending・README の値・--person の記号・見出しの status・契約の欄の位置・同じ id・endings を渡さない・行を書かない・--person 無し・定義を表の後に読む・値の無い旗・label の(仮)・出どころ・missing の件数)は **予測どおり 18/18、鳴った 18/18**、戻り一致

**監査の観点 S-2(notNullable の例外が届く経路)への材料**: `diagnose.ts` は JSONL の Failure Event を読み直さず、同じプロセスで lib が組み立てた行(型どおり)に判定を当てる。JSONL の行を読んで判定する口は、この差分には無い。

**載せ替えと NUL の直し(監査 f2 の GO の後、司令塔 e3 の指示)**: 基点を `ae74ec1` から `1fc4f67`(D6 計画 `67fdd89` と D4 の実装)に替えた。`ae74ec1..1fc4f67` で重なったのは `lib/schemaVersions.ts` だけで、1e の 3 定数は D4 の 2 定数の後ろ(末尾)へ文をそのまま移した。ほかの 8 本は載せ替えの前とバイト一致(写しと照合してから checkout)。あわせて、f2 の気づきのとおり `lib/condition.ts` 573 行目(集計の判定不能の理由の表のキーの区切り)に**生の NUL が 1 バイト**入っていたので、エスケープの 6 文字に替えた(この 1 行だけ。値は同じ。原因は実装担当が書いたときにエスケープが実バイトになったこと。ほかの 11 本に制御文字は無い)。測った結果(予測は回す前に書いた): 型検査 rc 0・`condition.test` 38/38・全体 57 本 831/831(基点 818 + conditionReport 11 + diagnose 2)・check-docs rc 0。予測は 3 つとも当たり
