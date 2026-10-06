# 将棋側 S-1(H-9 に packet を渡す)の計画と予測 ― 直す前に封じる

> **封じた後は本文を変えない。** 訂正は日付つきの追記か結果文書に。予測を当てるために範囲・規則を動かさない。
>
> **前提**: 人間の決定(2026-10-06、[CORE_CONNECTION_C2_DECISIONS_AFTER_2026-10-06.md](CORE_CONNECTION_C2_DECISIONS_AFTER_2026-10-06.md)): 「H-9 に packet を渡していなかった穴を、いきなり修正するのではなく、**何が見えるようになるかを先に予測 → 計測 → 人間判断**」。順番は XBRL(C-1h)の後。この文書は C-1h の実装中に、ファイルが重ならないので先に封じる。**実装は C-1h のコミットの後。**
>
> **Base**: `201c081`。c5 Golden Master は rc=0(C-2 で確認)。

## 1. 何が穴か(読んで確かめた事実)

`validateHypothesisLine(line, {today, registry, packet?})` の呼び出しは将棋側に 5 か所。**packet を渡しているのは `lib/exitSelect.ts` の 1 か所だけ。** `hypothesisCheck.ts`(CLI)・`goldenMasterCheck.ts`(Golden の g9.hypothesisCheck)・`lib/seatOutput.ts`(E-3)・`lib/integration.ts`(I-4)は渡していない。渡さないと H-9・H-10・H-11 は `skipped: true` で緑にならないが**落ちもしない**。c5 の Golden Master では 58 件とも H-9/H-10/H-11 が「未照合」。

C-2([結果](CORE_CONNECTION_C2_RESULT_2026-10-06.md) §3.2)で packet を渡して初めて、観測 213 件のうち VALUE_MISMATCH 20(形の名前の配列を文字列に潰した写し 18・数そのものの差 2)と POINTER_NOT_FOUND 1 が見えた。

## 2. S-1 の範囲(狭く)

| 直す所 | 直し | 直さない所 |
|---|---|---|
| `scripts/playtest/goldenMasterCheck.ts` | g9.hypothesisCheck の `validateHypothesisLine` に **packet を渡す**(同じファイルで既に読んでいる `packet` を `opts.packet` に) | `seatOutputCheck`・`integrationCheck` の呼び方(E-3・I-4 は本番の門。渡すかは S-1 の結果を人間が読んでから = S-2) |
| `scripts/playtest/hypothesisCheck.ts` | `--packet <path>` を**任意引数**で足す(無ければ今のまま skip) | 既定の挙動 |
| ― | ― | `lib/hypothesis.ts`・`lib/packetRef.ts`・`lib/observationPacket.ts`・契約 schema・`docs/golden_master/c5_expectation.json`(**期待値は書き直さない**。書き直すかは人間) |

将棋側の差分は 2 ファイル、**+10〜25 行**。`audit-core/` は触らない。

## 3. 予測(封じる。C-2 の 1 回目 `c2_first_run_core.json` と Golden の現状から導いた)

### 3.1 Golden Master の動き

- `npx tsx scripts/playtest/goldenMasterCheck.ts --expect docs/golden_master/c5_expectation.json` は **rc=1** になり、差は **`g9.hypothesisCheck.*.items[*].lines` の中だけ**(H-9・H-10・H-11 の行の字が変わる)。`identity`・`packet`・`seat_runs`・`g8`・`g9.exit_gate / check_answer / check_structure / seatOutputCheck / integrationCheck` に差 **0**。
- 6 封筒の `status` は **6 つとも `fail` のまま**(H-1・H-3・H-5 の NG が元々あるので変わらない)、`return_code` も不変。
- 差の行数は `diff` の出力で **58 件 × 3 行 = 174 行以下**(H-9/H-10/H-11 の 3 行がそれぞれ変わる。174 を超えたら他の欄が動いている = 外れ)。

### 3.2 H-9(ID 単位。C-2 の観測ごとの結果から機械的に導いた)

packet を渡すと H-9 は観測ごとに照合し、**1 件でも落ちた観測がある仮説の行が NG** になる。

| 封筒 | items | H-9 NG になる行 |
|---|---|---|
| `0f1b019e-20261001-1/seat_gpt.json` | 7 | **1**: H-c5-gpt0f1b-005(reviewStatus の PNF) |
| `268dac98-20260930-1/seat_claude.json` | 11 | **2**: H-c5-claude268d-005(names 4 件)・-010(shallowVisibleGames 25/24) |
| `52ae3745-20261001-1/seat_claude.json` | 10 | **1**: H-c5-claude52ae-009(names 4 件) |
| `558b8a81-20261001-2/seat_claude.json` | 12 | **1**: H-c5-claude558b-004(names 4 件 + aheadThenLost 分母 2/4) |
| `558b8a81-20261001-2/seat_gpt.json` | 7 | **2**: H-c5-gpt558b-005・-006(names 各 1 件) |
| `f37561e1-20260930-2/seat_claude.json` | 11 | **1**: H-c5-claudef375-005(names 4 件) |
| 合計 | 58 | **8 NG・50 ok**(skip 0) |

H-9 の messages の合計は **21 行**(VM 20 + PNF 1)。数え直し(`数え直し:`)の行は **0**(C-2 の P-10 の未測部分がここで初めて測れる。1 行でも出れば C-2 の P-10 は外れに格上げ)。

### 3.3 H-10(名前が顧客の局の認識に在るか)

- 認識された名前は 16(`rows[].names` の和集合)、定義は 114(全部 `draft`)。H-10 は `statement`・反証の `text`・行動候補の `text` の中の名前を最長一致で拾い、16 に無ければ NG。
- 席の文は render された seat_input から書かれていて、形の名前は rows から写している。予測: **H-10 NG の行 0〜6 / 58**(出るなら、席が定義の表にある別の名前(例: 「中飛車」単独・「矢倉」単独)を文に使った行)。**0〜6 の幅は粗い**と先に書く(H-10 を回したことが無く、文を読まずに予測しているため)。

### 3.4 H-11(名前の段。落とさない)

- 全部 `draft` なので、文中の名前の言及は**全部**注記になる。`ok` は 58 件とも true のまま、`notes` が付く行は **20〜58 / 58**。

### 3.5 Core の経路との一致(計器 6 の再利用)

- 新しい Golden の H-9 の判定(行ごと NG/ok と messages の種類)は、C-2 の `c2_first_run_core.json` の state と観測 1 件ごとに **213/213 一致**するはず(同じ TS 関数を packet つきで呼ぶだけなので、C-2 の `h9_reference.ts` と同じ結果になる)。1 件でも違えば `h9_reference.ts` の写しが TS 本体と違っていたことになる(C-2 の結果の訂正)。

### 3.6 その他

| # | 項目 | 予測 |
|---|---|---|
| a | `audit-core/` の差分 | 0 |
| b | `npm run typecheck:scripts` | 既存の `out/` の赤以外に新しい赤 0 |
| c | vitest(`npx vitest run --root scripts/playtest`) | 既存と同じ本数が緑(`goldenMasterCheck` に試験は無い。`hypothesisCheck` の引数の試験があれば +1〜2) |
| d | 1 回目で予測と違う項目 | 0〜2(疑うのは 3.3 の H-10 の幅と 3.1 の 174 行の上限) |

## 4. 手順(3 役)

1. この文書を封(コミット)。C-1h のコミットを待つ。
2. 実装担当(将棋側 2 ファイルだけ。**作業木を書き換える git 操作は使わない。`goldenMasterCheck.ts` を実物 c5 で回さない**(1 回目は司令塔)。試験は合成材料で。コミットしない)。
3. 司令塔が凍結し、**1 回目を 1 回だけ**: (a) Golden Master を回し差の一覧を `docs/golden_master/s1_first_run_diff.txt` に保存(rc と行数)、(b) `goldenMasterCheck.ts --write` は**使わない**(期待値を書き直すかは人間)。代わりに一時ファイルへ測った値を書き出す手段が要るなら、`--write` を一時コピーの期待値に向ける(本物は触らない)。(c) 新しい g9.hypothesisCheck の H-9 行を C-2 の `c2_first_run_core.json` と観測単位で突き合わせる(scratchpad の照合 script)。
4. 独立監査 → GO でコミット(将棋側 2 ファイル + 差の一覧)→ 結果文書。
5. **人間の判断**: (i) Golden の期待値を書き直すか(新しい現状 = H-9 NG 8 件を「固定」するか、席の封筒を直させるか)、(ii) S-2 = E-3・I-4(本番の門)にも packet を渡すか、(iii) 20 件の元(席が names を潰す・数を 1 つずらす)を席の指示文で直すか。

## 5. この文書がしないこと

席の封筒の修正。期待値の書き直し。E-3・I-4 への packet の配線。`audit-core/` の変更。H-10/H-11 の規則の変更。
