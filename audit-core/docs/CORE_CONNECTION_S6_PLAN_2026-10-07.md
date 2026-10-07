# S-6 計画(封印) ― 実 run を Golden の土台に移す + 代表の版の統一 + 指示文 v1.5 + 端の境界の変異

- 日付: 2026-10-07
- 人間の合図: 「着手して」(2026-10-07)。直前の意見で挙げた 4 点 (a)(b)(c)(d) をこの 1 封にまとめる
- 前の封: `audit-core/docs/CORE_CONNECTION_S5_PLAN_2026-10-07.md`(結果は `..._S5_RESULT_2026-10-07.md`)
- 起点のコミット: `5f10d9f`(木は clean)
- **費用: 0 円**(この封に実 run は含まれない。API 鍵を使う道具は 1 つも走らせない)
- **Core(`audit-core/core/py`)は 1 バイトも変えない**

## 0. この文書の約束

1. **この文書の §2〜§5 の予測は、測る前に封じる。** コミットした後は書き換えない。訂正は日付つきの追記か結果文書に書く。
2. **予測を当てるために規則・範囲・上限を動かさない。** 外れは外れとして固定する。
3. 「全部当たった」は粒度が粗い証拠として扱う。欄は外れうる粒度で立てる(件数・内訳・行数まで書く)。
4. 役割: (a) は司令塔が行う(`scripts/playtest/out/` を触るため実装担当には渡せない)。(b)(c)(d) は実装担当が行い、独立した監査の GO を経てから司令塔がパス指定でコミットする。

## 1. 何をするか

### (a) 実 run `43f8b69c-20261007-1` を `llm-seats/` に移し、Golden を書き直す

- いま: `scripts/playtest/out/c5/llm-seats-s5/43f8b69c-20261007-1/`
- 移した後: `scripts/playtest/out/c5/llm-seats/43f8b69c-20261007-1/`
- `llm-seats-s5/` の直下の `pair_summary.json`・`seat_input.md`・`seat_input.meta.json` は**動かさない**(run の外側の証跡として残す)。run の中にも同名の `seat_input.meta.json` があり、Golden が読むのはそちら。
- `scripts/playtest/out/` は `.gitignore:8` で追跡外。よって移動は `mv` であり git の操作ではない。追跡されている記録は `docs/golden_master/c5_expectation.json` だけ。
- `llm-seats-s3/`・`llm-seats-s4/` の run は**移さない**。理由: S-3 の run は指示文 v1.3 の時代で契約が今と違い、S-4 の run は claude 席が HTTP 400(残高不足)で立たなかった不完全な run。Golden の土台にするのは、いまの契約で完走した 1 本だけにする。
- **順序を守る**: 移す → `goldenMasterCheck` を `--write` **なしで** 1 回回して rc と差の件数を記録する → それから `--write` する。差を見ないまま上書きしない。

### (b) 整理役が書く代表の `schemaVersion` を 1 つの定数にする

S-5 の結果 §10.4 の発見 (A)。S-4 で契約を直したのに、整理役が書く代表の行だけ版が `0.4` のまま据え置かれていて、観測 0 件の代表が schema で落ちる。

- 直す字: `scripts/playtest/lib/integration.ts:282` の `schemaVersion: "0.4"`
- 定数の置き場: `scripts/playtest/lib/schemaVersions.ts`(このファイルの冒頭に「版は**この 1 か所**に置く」と書いてある)。`scripts/playtest/lib/seatOutput.ts:18` の `SEAT_HYPOTHESIS_SCHEMA_VERSION` の定義をそこへ移し、`seatOutput.ts` は再輸出にする(既存の輸入を壊さない)
- **席と整理役が同じ 1 つの定数を読む**状態にする。ずれを試験で留める

### (c) 指示文 v1.5(局の符号を観測に引かせる)

S-5 の結果 §10.4 の発見 (B)。`g04` のような局の符号の数字が H-1 に数えられて安全側の誤りになる。直すのは門ではなく指示文。

- 新しいファイル `docs/LLM_SEATS_INSTRUCTION_v1.5_2026-10-07.md`。v1.4 からの差は**版名の行 + 1 ブロック**だけ
- 足す中身: 局を符号や番号で呼ぶときは、その局の `facts.recognition.rows[n].gameId` を観測に引く。**理由も書く**(文に出た数は観測の値に無ければ H-1 が落とす。符号そのものを観測に引けば、符号の中の数字はその文字列の内側として覆われる)
- v1.3 の埋め草禁止と矛盾しないことを 1 文で書く(引くのは束に実在する欄であり、埋め草ではない)
- `scripts/playtest/lib/seatRun.ts` の `FIXED_INSTRUCTION_SHA256` に v1.5 の行を足す

### (d) 端の境界の変異 1 組

S-5 で入れた `isFullyCoveredBySpan`(`scripts/playtest/lib/hypothesis.ts`)の境界が、試験で押さえられているかを測る。

```
return spans.some(([s, e]) => s <= start && end <= e);
```

- 変異 m1: `s <= start` → `s < start`
- 変異 m2: `end <= e` → `end < e`
- 変異は `git worktree add --detach` の中で回し、終わりに `git worktree remove --force` で消す。**共有の木に残さない**

## 2. 予測 ― (a) 移動と Golden(14 欄)

| 欄 | 予測 |
|---|---|
| a1 | 移した後・`--write` の前の `goldenMasterCheck` は **rc=1**、差は **25 件** |
| a2 | 差の節ごとの内訳: `identity` **5** / `seat_runs` **15** / `g9` **5** / `packet` **0** / `g8` **0** |
| a3 | `seat_runs` の 15 件の内訳: 「長さ 期待 7 / 実測 8」**1 件** + `[3]` **4 件** + `[4]` **3 件** + `[5]` **4 件** + `[6]` **3 件**。理由は新しい run の名前 `43f8b69c…` が並びの **index 3**(`268dac98` と `52ae3745` の間)に入り、以降が 1 つずつずれるため |
| a4 | `identity` の 5 件はすべて「期待に無い」。`llm-seats/43f8b69c-20261007-1/` の 5 ファイル(`seat_input.meta.json`・`seat_claude.json`・`seat_gpt.json`・`integration.json`・`integration_input.json`) |
| a5 | `g9` の 5 件は「期待に無い」。`hypothesisCheck` に 2 鍵・`seatOutputCheck` に 2 鍵・`integrationCheck` に 1 鍵。`exit_gate`・`check_answer`・`check_structure` は **0 件** |
| a6 | 書き直した後の件数: `identity` 47 → **52**、`seat_runs` 7 → **8**、`g9.hypothesisCheck` 6 → **8**、`g9.seatOutputCheck` 6 → **8**、`g9.integrationCheck` 4 → **5** |
| a7 | 新しい run の `hypothesisCheck` の 1 項目の `lines` は**基本 13 行**(schema + H-1〜H-12。skip も 1 行)。13 を超えるのは H-11 または H-9 の報告(notes)が付く項目だけ。点推定: 14 項目のうち **3〜7 項目**が 13 を超える(主な理由は H-11 の「承認済みの定義が無い名前」) |
| a8 | 新しい run の `hypothesisCheck` の `status` は gpt・claude **ともに fail** |
| a9 | 新しい run の `seatOutputCheck.problems` は gpt **4 行**・claude **8 行**(実 run の `checks.json` と同じ中身。E-3 がこの面で初めて実際に回る) |
| a10 | 新しい run の `integrationCheck` は **fail**。`problems` に **C-007 と C-008 の representative の schema NG が各 1 行以上**(代表の版が 0.4 で、`hypothesis.v0.4` が `observations` を 1 件以上求めるため) |
| a11 | 新しい run の `integrationCheck.problems` の総数: 点推定 **4 件**、帯 **2〜10 件** |
| a12 | 新しい run の `integrationCheck.problems` に **I-1 の行は 0 件**・**H-9 の行は 0 件**(実 run の計器 `r4_I1_lines`・`e2_I4_H9_lines` がともに空だった) |
| a13 | 新しい run の `hypothesisCheck` では H-12 の行が **すべて「H-12 ok」**(skip ではない。席の出力の `schemaVersion` は 0.5)。= 14 項目 × 1 行 |
| a14 | `--write` の後に回し直すと **rc=0** |

## 3. 予測 ― (b) 代表の版の統一(7 欄)

| 欄 | 予測 |
|---|---|
| b1 | 版を直書きしている字は `scripts/playtest/lib/integration.ts:282` の **1 か所だけ** |
| b2 | 定数の置き場は `scripts/playtest/lib/schemaVersions.ts`。`seatOutput.ts` は再輸出に変わる |
| b3 | 触るファイルは **3 本**(`schemaVersions.ts`・`seatOutput.ts`・`integration.ts`)+ 試験 1 本。他は触らない |
| b4 | 新しい試験は **3 本**: (i) 定数が**字で** `"0.5"`、(ii) `completeIntegration` の出力の `clusters[].schemaVersion` が**字で** `"0.5"`、(iii) 観測 0 件・`kind: needed_observation` の代表が `validateHypothesisLine` の schema を通る |
| b5 | (iii) は**直す前のコードでは落ちる**(0.4 の契約が `minItems: 1` を持つ)。= 直しの効き目を測る試験になっている |
| b6 | (b) は Golden を**変えない**。`integrationProblems` は保存済みの `integration.json` を読み、`completeIntegration` を呼ばない。(b) の後の Golden は **rc=0** |
| b7 | 既存の試験で赤になるものは **0 本**、typecheck は通る |

## 4. 予測 ― (c) 指示文 v1.5(7 欄)

| 欄 | 予測 |
|---|---|
| c1 | v1.4 からの差は **版名の行 + 1 ブロック**。他は 1 バイトも変えない |
| c2 | 足すブロックは、局を符号で呼ぶときに `facts.recognition.rows[n].gameId` を観測に引くこと **と その理由** の 2 文以上 |
| c3 | v1.3 の埋め草禁止と矛盾しない旨の 1 文を入れる |
| c4 | `FIXED_INSTRUCTION_SHA256` の鍵は 7 本 → **8 本** |
| c5 | v1.5 の sha は**字で**表に書く(実ファイルから測った値を実行時に当てはめる形にしない) |
| c6 | (c) は Golden を**変えない**。Golden は **rc=0** のまま |
| c7 | (c) の効き目(`g04` の数が H-1 に数えられなくなるか)は **次の実 run まで測れない**。この封では **未測定**として記録する |

## 5. 予測 ― (d) 端の境界の変異(4 欄)

| 欄 | 予測 |
|---|---|
| d1 | 変異 m1(`s <= start` → `s < start`)で**赤になる**。赤になる試験は **1 本以上**(点推定 2 本) |
| d2 | 変異 m2(`end <= e` → `end < e`)で**赤になる**。赤になる試験は **1 本以上**(点推定 2 本) |
| d3 | どちらかが**黙ったら**、試験が足りないという結果として記録し、その境界を押さえる試験を足す(変異を直すのではなく試験を足す) |
| d4 | 変異は worktree の中だけで回し、ジョブの終わりに木から消える。共有の木に残る変異は **0 本** |

**予測の欄は合計 32 欄**(a 14 + b 7 + c 7 + d 4)。

## 6. やらないこと(この封の外)

- 実 run(費用 0 円。次の実 run の上限は人間が別に決める)
- `heldBack` を下書きに読ませる直し(人間の決定で後回し)
- E-5 の字面一致の規則
- 名前のついた安全側の誤り「検証済みの文字列の内側の比の数」
- gemini 席
- `audit-core/core/py` の変更(必要になったら止めて人間へ)
- 販売・実証の範囲の書き換え(人間が (a)〜(c) を見てから)

## 7. 次の実 run に持っていく約束

人間の指摘(2026-10-07)により、費用と所要の予測は**二峰の帯**で書く。再試行が 0 回のとき / 1 回のとき / 3 回打ち切りのときを分けて書き、1 つの点推定にまとめない。S-5 では r11・t3 がこの理由で外れた(どちらも再試行が 0 回だったため低く出た)。
