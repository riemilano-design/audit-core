# 将棋側 S-3(死んでいた門を生かして実 run を 1 周)の結果

**日付**: 2026-10-06 **計画と予測の封**: [CORE_CONNECTION_S3_PLAN_2026-10-06.md](CORE_CONNECTION_S3_PLAN_2026-10-06.md)(`ca6fe0d`、sha `6016f00c…`、不変) **監査**: **GO**(独立、2026-10-06。凍結 8 件の sha 一致(前後)、範囲 §2.1 内(`audit-core/`・schema・Golden・`.env`・`exitSelect.ts`・`hypothesis.ts` 差 0)、v1.3 の diff は 3 ブロックだけ、`exitSelect.ts --draft` の必須旗と `exitDraftCommand` 一致、実物 c5 packet で消した 6 列が鍵 0 行、別木の変異 5 本が全部予測どおり赤。非ブロッキング 3 件は §6.3) **コミット**: `5df660b`(将棋側 7 ファイル + 指示文 v1.3)、本文書と証跡は次のコミット **実 run**: `ae40ec51-20261006-1`(`scripts/playtest/out/c5/llm-seats-s3/`、gitignore。司令塔が 23:13〜23:19 に 1 回だけ)

> 人間の決定(111253b)の S-3: 「本番の死んでいた門を生かした状態で、最初から最後まで 1 周する」が実験単位、費用 $5 ハードキャップ、Core 変更なし、予測は先に封。順序 ① Golden 更新 → ② 封 → ③ 実装 → ④ 監査 → ⑤ 実 run 1 回 → ⑥ 照合 → ⑦ 人間。この文書は ⑥ まで。

## 1. 何を直したか(将棋側 7 ファイル +170/−27、本体 4 ファイル +72/−17、`audit-core/` 0)

| 計画 | 直し | 実装 |
|---|---|---|
| (a) seal | コード不要(fc8f6e5 で入っていて実 run が無かっただけ) | 実 run 自体が初の計測(§3.1) |
| (b) 描画 | `lib/seatInput.ts`: `list()` を JSON の配列の字面に(5 箇所、空は `[]`)、packet に鍵が 1 行も無い列 6 つ(§0.3 `engineVersion`・`definitionsDirs`、§4 `bandBefore`・`bandAfter`、§6 `reviewStatus`、§7 `phase`)を消す、鍵の無い行は `(無)`(`null` は packet の値が null のときだけ)、§0 読み方 1・2 行目 | +21/−15 |
| (c) 指示文 | `docs/LLM_SEATS_INSTRUCTION_v1.3_2026-10-06.md` = v1.2 + 版名の行 + 20 行目の後に 2 文(埋め草を写さない・根拠が無ければ `unanswerable` と `neededObservation`、配列はそのまま配列で写す)。sha `284f24a9…` を `FIXED_INSTRUCTION_SHA256` に | 新規 31 行 |
| (d) draft の段 | `lib/deliver.ts`: 段 `exit-draft`(`exit-select` の直前)。`--seat-run <runId>` 無しで skip(`args: []`、既存 24 段の順・action 不変)、有りで `exitSelect.ts --draft --packet … --integration <seatsDir>/<runId>/integration.json --request … --obs-registry docs/OBSERVATION_ITEMS.md --today … --out <answer_selection.draft.json>`。採用の印は付けない | +32/−1(+ CLI の表 1 行) |
| (e) packet | `lib/seatRun.ts` の E-3(`seatOutputProblems`)と I-4(`integrationProblems`)の呼び出しに `packet: cfg.packet` | 2 行 |

試験 +4(2329 → 2333)。書き換えた既存試験は計画が許した「段の一覧・件数・sha 表の件数・描画の literal」と、**fixture 2 箇所**(`minimalAggregates` の numerator 行に `numeratorWhere: []`、`seatLlm` の観測値 65 → 1)。後者は packet が H-9 に初めて渡って露出した fixture 側の不整合(実物 c5 の numerator 行 11 件は全部 `numeratorWhere` を持つ。監査が実物で確かめた)。

## 2. 門(監査が別木で自分で測った)

| 門 | 結果 |
|---|---|
| `npm run typecheck:scripts` | 新しい赤 0 |
| `npx vitest run --root scripts/playtest` | 118 ファイル・**2333** 緑(+4) |
| `git diff --check` | 0 |
| 変異(別木) | E-3 側の packet を外す → 新規 1 本 赤、I-4 側 → 新規 1 本 赤、`list()` を `+` 結合に戻す → seatInput 1 本 赤、skip 条件の反転 → deliver 2 本 赤、v1.3 の 1 文を消す → sha 表の試験 赤 |
| 描画の数の包含検査(送る前) | 指示文の例 5 本中 5 本が引けて値も入っている(dry-run・実 run とも) |

## 3. 実 run の記録(司令塔、1 回だけ)

### 3.1 下見と実費

| | gpt(gpt-5.5) | gemini | claude(claude-opus-5) | 整理役(claude-opus-5) | 合計 |
|---|---|---|---|---|---|
| `--dry-run` の見込み(23:12) | 1.2464 | 保留 | 1.0964 | 0.8464 | **3.19**(上限 5) |
| 実費(USD) | **1.5597**(2 試行) | 0(保留) | **2.8448**(3 試行、空席) | **0.1307** | **4.5351**(上限 5・`capReached: false`) |
| 所要 | 123,984 ms | ― | 295,787 ms | ― | 23:13 → 23:19:59 |

束 226,568 B・207,827 字・概算 69,276 トークン(chars/3、鍵を使わない)。`SEAT_COST_CAP_USD=5` はコマンドの環境変数で渡し、`.env` は不変(`loadDotEnv` は既にある名前を上書きしない ― コードで確認し、dry-run の「上限 5 ドル」で実測)。stdout の写し: [docs/golden_master/s3_first_run_stdout.txt](../../docs/golden_master/s3_first_run_stdout.txt)。

### 3.2 席ごとの顛末

**gpt**: 試行 1 は schema で落ちた(`itemId` が `f1`/`f2`/`f3`/`h1`/`n1` で `^S-[0-9]{3}$` に合わない 5 件 + **`n1`(kind `needed_observation`)の observations が 0 個で minItems 1 に足りない**)。試行 2 で通過: 項目 **3**(finding 3、`answer_candidate` と `needed_observation` は消えた)、観測 **12**(全部 `aggregates.groups.*`)、answers q1 = `partial`(「普段指すかどうかの印が束に無い」)、`selfComputedNumbers` 3 件(比の計算、根拠には使っていないと注記)。封印語 **12/12 一致**、E-3 の指摘 **1**: `E-5: selfComputedNumbers[2] の値「0」が statement / answers の文に出ている`。

**claude**: 3 試行とも schema で落ちて**空席**(`schema_failed`)。理由は試行 1「$: 知らない欄 `items2`」、試行 2「$.items: 型が array ではない(string)」、試行 3「$: 知らない欄 `items2`」。中身を読むと、**試行 1・3 は `items` に 7 項目(finding 6 + needed_observation 1、観測 31 件)を正しく持ち、余計な `items2: []` が 1 つ付いていただけ**。試行 2 は `items2` を消す代わりに `items` 全体を JSON の文字列にした。3 試行とも封印語は **12/12 一致**。失われた 7 項目には **配列のままの観測が 6 件**(`facts.recognition.rows[3].names = ["英ちゃん流中飛車","5筋位取り中飛車","角換わり腰掛け銀"]`、`rows[12].names = ["忍者銀"]`、`rows[23].names`、空配列 `rows[8]/[9]/[17].names`)が入っていた = **席は配列を配列のまま写していた**が、器に届かなかった。再試行の指摘は累積して渡しているが、席は 2 つの誤りの間を往復した(1 → 2 で直し、2 → 3 で元に戻る)。

**整理役**: 束 3(gpt の 3 項目が 1 つずつ)、`forVerification` 2(C-002・C-003)、`heldBack` 1(C-001「局数の内訳は根拠の場所をそのまま写しただけで、検証で新たに確かめる差が無い」)、指摘 **1**: `I-6: selfComputedNumbers[2] の値「0」が代表の文・矛盾・注に出ている`。

### 3.3 事後の照合 4 本

| 照合 | 結果 |
|---|---|
| `seatOutputCheck.ts --packet`(gpt) | 問題 1(E-5)。**packet 無しでも同じ 1 件** = H-9 の NG 0 |
| `integrationCheck.ts --packet` | 問題 1(I-6)。packet 無しでも同じ = I-4 の H-9 行 0 |
| `exitSelect.ts --draft`(単体、`--out` は scratchpad → 写し [docs/golden_master/s3_answer_selection.draft.json](../../docs/golden_master/s3_answer_selection.draft.json)) | 通った候補 **3**・落ちた候補 **0**・問い 1・行動の表 9・`adoptedBy: null`。**整理役が `heldBack` にした C-001 も `items` に入っている**(`buildSelectionDraft` は `clusters` を全部回し、`heldBack`・`forVerification` を読まない ― 読んで確かめた事実。S-3 の欠陥ではなく道具の作り) |
| `run_core_path_shogi.py --seats-dir llm-seats-s3` → [fixtures/shogi/s3_first_run_core.json](../fixtures/shogi/s3_first_run_core.json) | Claim **17** = 観測 12 **GROUNDED 12** + counterEvidence の観測 5 UNVERIFIABLE(`no_packet_ref(H-9 out of scope)`、C-2 と同じ規則)。H-9 の自前の再導出と **12/12 一致** |

H-9 の内訳(gpt の観測 12 件、[s3_first_run_compare.json](../../docs/golden_master/s3_first_run_compare.json)): `+` 型 VM **0**・消した列への PNF **0**・`(無)` への PNF **0**・残り **0**・埋め草の印 **0**。Golden c5 `--expect` は実 run の後も **rc=0**(新 run は `llm-seats-s3/` で Golden は拾わない)。

## 4. 予測との照合(封 §3 の 32 欄。計画の題は「30 欄」と書いたが表の行は 32)

| # | 予測 | 実測 | 判定 |
|---|---|---|---|
| a1 | 返ってきた封筒は schema を全部通る | gpt の封筒は通った。claude は通る封筒が返らず空席 | 当たり(gpt)。claude は測る物が無い |
| a2 | E-1 不一致 席ごと 0〜2 | gpt 0。失われた claude の 3 封筒も 0 | 当たり |
| a3 | checks.json の E-3 行が H-1〜H-11 の行を含む(2 席とも) | gpt の E-3 は走った(E-5 の行が証拠)が **H-\* の行は 0**(NG が無ければ行は出ない)。claude は無し | **外れ**(字面。「走る」と「行が出る」を混同した予測の書き方の誤り) |
| a4 | 空席 0 | **claude が空席**(seal ではなく `items2`/文字列) | **外れ** |
| b1 | `+` 型 VM 0 | 0 | 当たり |
| b2 | 消した列の PNF 0 | 0 | 当たり |
| b3 | `(無)` の PNF 0 | 0 | 当たり |
| b4 | 残りの VM/PNF 0〜4 | 0 | 当たり |
| b5 | 配列のまま GROUNDED 1 件以上 | **gpt 0**(aggregates しか引かなかった)。claude の失われた封筒には 6 件 | **外れ**(測れた席では 0。「席が配列を写せる」は届かなかった封筒で見えただけで、当たりにしない) |
| b6 | 包含検査 通る | 5/5 | 当たり |
| b7 | 束 −2%〜+6%(227,828 基準) | 226,568(**−0.55%**) | 当たり |
| c1 | 観測/項目 中央値 1〜3 | 3 | 当たり |
| c2 | 埋め草の印 0 | 0 | 当たり |
| c3 | `unanswerable` 1〜6 | **0** | **外れ**(§5.1: 指示文の逃げ道を schema が塞ぐ) |
| e1 | H-9 が照合されている(skip 0) | skip の文 0、新規試験で配線を固定 | 当たり |
| e2 | I-4 H-9 行 0〜6 | 0 | 当たり |
| e3 | CLI と checks.json 一致 | E-5 / I-6 とも一致(packet の有無でも同じ) | 当たり |
| e4 | Core の経路と 100% | 12/12 | 当たり |
| d1 | draft が出る、`adoptedBy: null` | 出た、null | 当たり |
| d2 | rejected 40〜80% | **0%**(3/3 通過) | **外れ**(前回の束は H-1/H-3/H-5 で半分落ちたが、今回の gpt 3 項目は数の写しだけで全部通った) |
| d3 | H-9 だけで落ちた束 0〜2 | 0 | 当たり |
| d4 | `exit-draft` は `--seat-run` 無しで skip | skip(試験・監査の変異) | 当たり |
| d5 | 冊子の変わるページ 0 | 0(組版は回さず、Golden の g8 不変) | 当たり(設計の帰結) |
| f1 | 実費 2.5〜4.8 | 4.5351 | 当たり(上側。claude の 3 試行 2.84 が押し上げた) |
| f2 | 上限で止まらない | 止まらず | 当たり |
| f3 | dry-run 2.4〜3.4 | 3.19 | 当たり |
| f4 | 5 を超えない | 超えず | 当たり |
| g1 | Golden rc=0 のまま | rc=0 | 当たり |
| g2 | `audit-core/` 差分 0 | 0 | 当たり |
| g3 | typecheck 新しい赤 0 | 0 | 当たり |
| g4 | vitest +6〜14 | **+4** | **外れ** |
| g5 | 違う 0/1 の欄 0〜3 | a3・a4・b5 = **3** | 当たり(上端) |

**集計: 32 欄 当たり 26・外れ 6**(a3・a4・b5・c3・d2・g4)。封じた予測は変えていない。実装を予測に寄せていない。外れの向き: 席の出力に依る欄(a4・b5・c3・d2)が全部「席はこちらが見込んだより少なく・保守的に出した」側、残り 2 つは私の書き方(a3)と見積もり(g4)。

## 5. S-3 が見せた物(予測の表に無かった事実)

### 5.1 指示文 v1.3 の逃げ道を schema が塞いでいる

v1.3 の 21 行目は「根拠が束に無い項目は `kind` を `unanswerable` にして `neededObservation` を書く」と言うが、`hypothesis.v0.4.schema.json` は `observations` に **minItems 1 を kind によらず**要求する(`kind` の enum に `unanswerable`・`needed_observation` は在る)。gpt の試行 1 の `n1`(needed_observation、観測 0)はまさにこれで落ち、試行 2 で席は **その項目を捨てた**。埋め草を禁じた(c1)うえで観測 0 も禁じると、席に残る合法手は「捨てる」だけ ― c3 の 0 はこの構造の帰結で、席の怠慢ではない。schema は契約なので直すのは人間の判断(§6)。

### 5.2 封印語は効く

seal 入りの実 run は今回が初めて。4 封筒(gpt 1・claude 3)とも 12 節 12/12 一致で、E-1 は 1 件も落とさなかった。「席が節の終わりまで読んだ」の到達の証拠は取れる。

### 5.3 claude 席の失い方

落ちたのは中身ではなく器の外側(`items2: []` という空の余計な鍵、次に `items` の文字列化)。schema の additionalProperties を緩めるのは正しくない(緩めると「写さない」が崩れる)。2.84 USD で 7 項目・配列の観測 6 件が届かなかった。再試行の指摘は累積して渡していたが、席は 2 種類の誤りを往復した。

### 5.4 draft は整理役の「外した束」を読まない

`buildSelectionDraft` は `clusters` を全部回し、代表が H 検査に通れば `items` に入れる。整理役が `heldBack` にした C-001(「検証で新たに確かめる差が無い」)も候補として並んだ。採用は人なので冊子には出ないが、「整理役の判断が draft に見えない」のは道具の作りとして記録する。

### 5.5 E-5 の「0」

gpt の statement「署名なし で 0/2」の 0 は packet の `aggregates.groups.noSignature.aheadThenLost.numerator = 0`(観測に写してあり H-9 で GROUNDED)で、`selfComputedNumbers[2]` の 0(= 0/2)と字面が同じなだけ。E-5 は隔離欄の数が文に出たと見なして落とした。[記憶 `gate-counts-non-claims-as-numbers`] と同じ根(字面の一致で数を数える)。直すなら規則の変更なので先に封じる。

### 5.6 配線の事実(S-1 → S-2 → S-3 で揃った)

packet つきの H-9 は Golden(S-1)→ I-4 の記録(S-2)→ **実 run の E-3/I-4(S-3)** まで同じ関数で届き、CLI と checks.json と Core の経路が一致する。描画の `+` 潰しが消えた今回、gpt の観測 12 件は VM 0・PNF 0 で、S-1 の 21 件の原因が描画 18 + 席 2 + 列 1 だったという S-2 の読みと矛盾しない(ただし gpt は配列の欄を引かなかったので、配列の写しは今回の実物では未実証)。

## 6. 人間の判断(⑦)

| # | 問い | 司令塔の推し |
|---|---|---|
| (a) | `ae40ec51` を `llm-seats/` に移して Golden を書き直すか | **まだ移さない。** 1 席が空席の run を「現状」として固定すると、次の比較の基準が片肺になる。`llm-seats-s3/` に置いたまま結果文書で参照する |
| (b) | §5.1 の schema(`unanswerable`/`needed_observation` の観測 0 を許すか、代わりに `neededObservation` を必須にするか) | 契約の変更なので人間。推しは「kind がこの 2 つのときだけ minItems 0 + `neededObservation` 必須」を**別に封じてから**(H-4 と同じ形で kind が必須を決める) |
| (c) | claude 席の `items2` | 器は緩めない。次の実 run の前に、再試行の指摘に「前回通った欄の形はそのまま」を足すかは席の指示文の版上げ(v1.4)として別に封じる。費用は人間 |
| (d) | draft が `heldBack` を読むか(外した束を `rejected` に理由つきで並べる) | 道具の作りの変更。推しは読む(整理役の判断を draft に見せる)。先に封じる |
| (e) | E-5 の字面一致(§5.5) | 規則の変更なので先に封じる。今回は記録のみ |
| (f) | もう 1 回実 run を回すか(金銭) | 人間。回すなら (b)(c) の後に、同じ `llm-seats-s3/` へ、上限は改めて決める |

## 7. 手順との差・記録

1. 実装担当は鍵を使わず、dry-run も席も deliver も実物で回していない。作業木を書き換える git 操作なし。逸脱なし。
2. 司令塔の実 run は 1 回(dry-run 1 回の後)。上限は環境変数で渡し `.env` は不変。実 run 中にコードは触っていない(`gitHead` = `5df660b`、木はきれい)。
3. draft の `--out` は scratchpad に向け、`out/c5/exit/` には書いていない。Core の経路の出力も scratchpad から fixtures へ写した。
4. 監査の非ブロッキング 3 件(直していない): `list()` の複数要素・空配列を直接見る試験が無い(fixture が全部 1 要素)、`v(null)` の分岐は実物 c5 に null 値 0 件で未到達、`deliver.test.ts` の古い題名「23 段」。
5. 計画の題「予測 30 欄」は表の行で数えると 32。数え方の誤りで、予測の中身は変えていない。

## 8. この文書がしないこと

Golden の書き直し(⑦ は人間)。schema・E/I/H の規則の変更。採用(`adoptedBy`)。claude 席の再実行。gemini。Core の変更。
