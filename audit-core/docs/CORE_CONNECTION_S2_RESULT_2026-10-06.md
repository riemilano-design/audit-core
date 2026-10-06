# 将棋側 S-2(E-3・I-4 にも packet を渡す)の結果

**日付**: 2026-10-06 **計画と予測の封**: [CORE_CONNECTION_S2_PLAN_2026-10-06.md](CORE_CONNECTION_S2_PLAN_2026-10-06.md)(`667eeac`、sha `d05b559f…`、不変) **監査**: **GO**(独立、2026-10-06。凍結 7 件の sha 一致・diff 全文読み・Golden を自分で再実行して 35 件一致・H-9 を packet と integration.json から独自実装で再導出して 17 行/6 束一致・別木の変異 2 本(integration 側の中継を外す → 新規試験 赤かつ Golden 差 0 に戻る、seatOutput 側 → 新規試験 赤)・E-3 の未到達を実測確認・粒度は束・添字・種類の単位で外れうる形と評価。非ブロッキング 2 件は §5.3 と同じ) **コミット**: `c3da8de`(将棋側 7 ファイル + 1 回目の差の一覧と照合の出力)

## 1. 何を直したか(将棋側 7 ファイル、+51/−9。本体 18 行、`audit-core/` 0)

| ファイル | 直し |
|---|---|
| `scripts/playtest/lib/seatOutput.ts` | `SeatOutputCheckOptions.packet?: unknown`、E-3 の `validateHypothesisLine` に `packet: opts.packet`。先頭コメントに「呼び出し側から渡された packet を中継するだけで自分では読まない」の注記。import・`readFileSync` は増やしていない(源の正規表現の試験 2 本 緑) |
| `scripts/playtest/lib/integration.ts` | `IntegrationCheckOptions.packet?: unknown`、I-4 の呼び出しに渡す(2 行) |
| `scripts/playtest/goldenMasterCheck.ts` | `seatOutputProblems(…, {meta, request, today, packet})`・`integrationProblems(…, {today, packet})`(G-2 の `packet`。S-1 と同じ形、2 行) |
| `scripts/playtest/seatOutputCheck.ts`・`integrationCheck.ts` | 任意引数 `--packet <path>`(無ければ今のまま)。USAGE と先頭コメント |
| `lib/seatOutput.test.ts`・`lib/integration.test.ts` | +1 本ずつ(packet 無し → H-9 の行無し、有り・一致 → 無し、有り・不一致 → `E-3: items[0] H-9: …` / `I-4: C-001 の representative H-9: …`)。E-3 側は数え直しの要らない `facts.recognition.rows[0].reviewStatus` 参照だけの封筒を組んだ。I-4 側は既存の `packet()` fixture(`facts` 無し)なので `toContain` で対象の 1 行だけを見る |

触っていない物: 早期 return、E-1〜E-7・I-1〜I-6 の規則、`forVerification`/`heldBack`、`lib/seatRun.ts`(S-3)、`lib/exitSelect.ts`・`lib/deliver.ts`・`exit_fill.py`、契約 schema、`c5_expectation.json`(sha `07b36a4b1a23a8eb…`、前後で不変)。

## 2. 門(司令塔が凍結の時点で測った。凍結 = 7 ファイルの sha 一覧)

| 門 | 結果 |
|---|---|
| `audit-core/` 差分 | **0** |
| `npm run typecheck:scripts` | rc=1、`error TS` 10 件は全部既存の `scripts/playtest/out/**`、新しい赤 **0** |
| `npx vitest run --root scripts/playtest` | 118 ファイル **2329 本**緑(変更前 2327、+2) |
| 源の正規表現の試験(`seatOutput.test.ts:193`・`integration.test.ts:267`) | 緑 |
| `git diff --check` | 0 |

## 3. 1 回目の計測(司令塔が凍結の後 21:14 に 1 回)

(a) `goldenMasterCheck.ts --expect docs/golden_master/c5_expectation.json` → **rc=1、差 35 件**。stderr の全文は [docs/golden_master/s2_first_run_diff.txt](../../docs/golden_master/s2_first_run_diff.txt)。(b) `--write` は scratchpad の一時コピーに向け、本物は触っていない。(c) 新しい `g9.integrationCheck` の H-9 行を §3.2 の束・観測単位の予測と突き合わせ → [docs/golden_master/s2_first_run_compare.json](../../docs/golden_master/s2_first_run_compare.json)。

### 3.1 Golden Master(予測 §3.1)

| 項目 | 予測 | 実測 | 判定 |
|---|---|---|---|
| rc | 1 | 1 | 当たり |
| 差の場所 | `g9.integrationCheck.<周>.problems` だけ。`seatOutputCheck`・`hypothesisCheck`・`exit_gate`・`check_answer`・`check_structure`・`g8`・`identity`・`packet`・`seat_runs` は 0 | そのとおり(`seatOutputCheck` 差 **0**、integrationCheck の problems の外 **0**) | 当たり |
| 4 周の status / return_code | fail / 1 のまま | 不変 | 当たり |
| 差の件数 | **35**(3・10・15・7) | **35**(3・10・15・7) | 当たり(S-1 の外れから学んだ数え方で導いた。Golden の diff の長さ 1 件 + 添字のずれ) |
| problems の長さ | 2→3・12→17・15→22・11→15 | そのとおり | 当たり |

### 3.2 I-4 の H-9(予測 §3.2。束・観測単位)

| 周 | 束 | 予測 | 実測 | 判定 |
|---|---|---|---|---|
| 0f1b019e-20261001-1 | C-005 | obs[2] PNF | obs[2] PNF(`rows[3].reviewStatus が packet に無い`) | 当たり |
| 268dac98-20260930-1 | C-005 | obs[1..4] VM | そのとおり | 当たり |
| 268dac98-20260930-1 | C-010 | obs[0] VM(25/24) | そのとおり | 当たり |
| 558b8a81-20261001-2 | C-005 | obs[1] VM | そのとおり | 当たり |
| 558b8a81-20261001-2 | C-006 | obs[0] VM | そのとおり | 当たり |
| 558b8a81-20261001-2 | C-008 | obs[0..3] VM + obs[5] VM(2/4) | そのとおり | 当たり |
| f37561e1-20260930-2 | C-005 | obs[0..3] VM | そのとおり | 当たり |
| 合計 | | **17**(VM 16・PNF 1)/ 6 束 | **17**(16・1)/ 6 束 | 当たり |
| 数え直しの行 | 0 | **0** | 当たり |
| H-10 NG / H-11 の行 | 0 / 0(H-10 は粗いと先に書いた) | **0 / 0** | 当たり |
| 他の束の H-9 | 0 | 0 | 当たり |

### 3.3 E-3 ― 予測 0 行、実測 **0 行**(6 封筒とも `schema: … seal` の行のまま)。当たり。**E-3 への伝播はこの材料では測れない**(封じたとおり)。

### 3.4 顧客の出口 ― 予測「伝播しない」、実測 **g8 差 0・exit_gate / check_answer / check_structure 差 0**。当たり。

### 3.5 その他

| # | 予測 | 実測 | 判定 |
|---|---|---|---|
| a | `audit-core/` 0 | 0 | 当たり |
| b | typecheck 新しい赤 0 | 0 | 当たり |
| c | vitest 既存 0 本落ちる・新規 +2〜4 → 2329〜2331 | 0 本落ち・**2329** | 当たり(下限) |
| d | 源の正規表現の試験 2 本 緑 | 緑 | 当たり |
| e | 違う項目 0〜2 | **0** | 当たり |
| §2 | 本体 +15〜40 行 | +18 | 当たり |

**集計**: 欄 22(3.1 の 5・3.2 の 11・3.3 の 1・3.4 の 1・3.5 の 6)、**当たり 22・外れ 0**。

**「全部当たった = 粒度が粗い」への答え**(先に自分で書く): 当たりの大半は、代表の観測 156 件が席の写しだと**読んで確かめた**うえで C-2 の 1 回目から機械的に導いたもので、外れうる形(束と観測の ID、差の件数 35 の厳密な数、長さの 4 組)で書いた。実際に外れうる危うさがあったのは 35 件(Golden の diff の数え方と `normalize` の掛かり方)と、整理役が書き直した代表の文に対する H-10 で、どちらも当たった。粗かったのは H-10 の「0」で、これは S-1 と同じく「文を読まずに予測した」ので、当たっても H-10 の規則の妥当性を言う材料にはならない。**S-2 で新しく学んだことは少ない**(予測が材料から全部決まる段だった)。学びは §1 の調査(E-3 が走っていない・伝播が無い・21 件の原因)の側にある。

## 4. S-2 が見せたもの

- Core 化した検証の結果(21 件)は、将棋側の **Golden(S-1)→ 統合の検査 I-4 の記録(S-2)** まで同じ観測単位で届く。代表の観測が席の写しなので、席の 21 件のうち統合に入った 17 件がそのまま I-4 に現れた。
- **届かない所**: E-3(封筒の schema で返る)、出口の選別(packet の経路がパイプラインで走っていない)、組版(I-4 を読まない)。**顧客の冊子は 1 byte も変わらない。** これは S-2 の欠陥ではなく、いまの配線の事実。届かせるかは規則の変更(計画 §6 (d))。

## 5. 手順との差・記録

1. 実装担当: 作業木を書き換える git 操作なし、実物 c5 で回していない、別木も不要だった。逸脱なし。
2. 1 回目は (a) 本物への `--expect` 1 回と (b) 一時コピーへの `--write` 1 回(照合のため)。本物は不変。
3. 実装担当の申し送り(直していない): CLI 2 本の固定文言「packet の実在は見ていない = H-9」が `--packet` 指定時に不正確、`integration.ts` 先頭と I-4 の見出しの「packet を読まない」の字面、`integration.test.ts` の `packet()` fixture に `facts` が無く aggregates 系の H-9 は「数え直し: … population が無い」の副産物を伴う(実物の packet は population を持つので 1 回目には出なかった)。
4. 差の一覧ファイルで `H-9` を含む行は 16(17 行のうち 268dac98 の C-010 の 1 行は新しい添字 12 で旧の長さ 12 の外にあり、Golden の diff には長さの差としてしか出ない)。照合の出力(新しい計測の全文から数えた)は 17。

## 6. 人間の判断(計画 §6 のとおり。司令塔の推しを添える)

| # | 問い | 推し |
|---|---|---|
| (a) | E-3 が実物で一度も走っていない(`reach.sections[].seal` 欠落で schema 止まり) | **席の出力に `seal` を書かせる方向で、次の席の指示文の版(v1.3)に入れる。** schema を緩めない。測るのは次の実 run |
| (b) | 18 件の元 = `seat_input` の描画 `list()` の `+` 連結、PNF 1 件 = 実在しない `reviewStatus` 列 | **描画を直す(配列は JSON の字面で描く・無い欄は描かない)。H-9 側は緩めない。** c5 では測れないので、席の再実行 1 周と抱き合わせで予測を封じてから |
| (c) | 数の差 2 件 | 直す物なし。H-9 の成果として記録 |
| (d) | I-4/E-3 の H-9 NG を選別・組版に届かせるか | **(b) を直してから。** 先に届かせると正しく写した 18 件が落ちる。届かせるなら「`forVerification` の束の代表が H-9 NG なら heldBack へ」の規則を別に封じる |
| (e) | S-3 = `lib/seatRun.ts` の checks.json にも packet | **(a)(b) と同じ次の実 run にまとめる**(Golden では測れない) |
| (f) | Golden の期待値を S-2 の現状(I-4 の H-9 行 17)で書き直すか | S-1 と同じ扱いなら書き直す(`--write` 1 回、`note` に 1 行)。**今回は人間の GO を待つ** |

## 7. この文書がしないこと

期待値の書き直し。描画・席の指示文・schema の修正。選別・組版への配線。`audit-core/` の変更。
