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
