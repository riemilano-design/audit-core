# 将棋側 S-1(H-9 に packet を渡す)の結果

**日付**: 2026-10-06 **計画と予測の封**: [CORE_CONNECTION_S1_PLAN_2026-10-06.md](CORE_CONNECTION_S1_PLAN_2026-10-06.md)(`fa827f7`、不変) **監査**: **GO**(独立、2026-10-06。凍結 3 件の sha 一致・diff 全文読み・H-9/H-10/H-11 と 213/213 を自分で再集計して一致・178 件と flatten 201 件の整合を解明・自作変異 2 本(`--packet` 分岐を潰す → 試験 s1-2 赤、packet の受け渡しを外す → 別木で Golden が rc=0 差 0 に戻る)・期待値の sha 不変。非ブロッキング 1: 集計の数え方の揺れ → §3.6 の集計を欄 16 に直した) **コミット**: `c2708ed`(将棋側 2 ファイル + 試験 1 本 + 1 回目の差の一覧と照合の出力)

## 1. 何を直したか(将棋側 2 ファイル、+15/−5。`audit-core/` 0)

| ファイル | 直し |
|---|---|
| `scripts/playtest/goldenMasterCheck.ts` | g9.hypothesisCheck の `validateHypothesisLine(line, {today, registry})` に、同じファイルの G-2 で既に読んでいる `packet` を足した(**1 行**)。`seatOutputCheck`・`integrationCheck`(E-3・I-4)は不変 |
| `scripts/playtest/hypothesisCheck.ts` | 任意引数 `--packet <path>`。指定が無ければ `packet: undefined` を渡し、今までどおり H-9/H-10/H-11 は skip(`checkH9` 等は `undefined` で skip する作り)。壊れた JSON の扱いは既存の席ファイル読みと同じ(try/catch を足さない) |
| `scripts/playtest/hypothesisCheck.test.ts`(新規) | CLI を spawn で回す既存の流儀。s1-1 `--packet` 無し → `H-9 skip`、s1-2 有り → 値一致で `H-9 ok`・ずれで `H-9 NG`(「value が packet と違う」)。材料は合成(mkdtemp) |

触っていない物: `lib/hypothesis.ts`・`lib/packetRef.ts`・`lib/observationPacket.ts`・`lib/exitSelect.ts`・`lib/seatOutput.ts`・`lib/integration.ts`・契約 schema・`docs/golden_master/c5_expectation.json`(sha `3b29862443ac5a61…`、1 回目の前後で不変)。

## 2. 門(司令塔が凍結の時点で測った。凍結 = 3 ファイルの sha 一覧)

| 門 | 結果 |
|---|---|
| `audit-core/` の差分 | **0** |
| `npm run typecheck:scripts` | rc=1、`error TS` 10 件は全部既存の `scripts/playtest/out/**`、**新しい赤 0** |
| `npx vitest run --root scripts/playtest` | 118 ファイル **2327 本**緑(変更前 117 / 2325、+2 = 新規試験) |
| `git diff --check` | 空白エラー 0(実装担当) |

## 3. 1 回目の計測(司令塔が凍結の後 20:20 に 1 回)

(a) `npx tsx scripts/playtest/goldenMasterCheck.ts --expect docs/golden_master/c5_expectation.json` → **rc=1、差 178 件**。stderr の全文を [docs/golden_master/s1_first_run_diff.txt](../../docs/golden_master/s1_first_run_diff.txt) に保存。(b) `--write` は scratchpad の一時コピーに向け、本物は触っていない。(c) 新しい H-9 を C-2 の `fixtures/shogi/c2_first_run_core.json` と観測単位で照合 → [docs/golden_master/s1_first_run_compare.json](../../docs/golden_master/s1_first_run_compare.json)。

### 3.1 Golden Master の動き(予測 §3.1)

| 項目 | 予測 | 実測 | 判定 |
|---|---|---|---|
| rc | 1 | 1 | 当たり |
| 差の場所 | `g9.hypothesisCheck.*.items[*].lines` だけ。`identity`・`packet`・`seat_runs`・`g8`・他の g9 の門に差 0 | そのとおり(照合 script の flatten で `lines` の外の差 **0**) | 当たり |
| 6 封筒の `status` / `return_code` | 不変(fail のまま) | 不変 | 当たり |
| 差の件数 | **174 以下**(58 × 3 行)。「超えたら他の欄が動いている」 | **178** = lines[9]/[10]/[11] × 58 = 174 **+ `items[k].lines` の長さの差 4 件**(H-11 の `(報告)` 行が増えた 4 項目: 12 → 20・18・23・14 行) | **外れ**。数も外れ、「超えたら他の欄」の読みも外れ(増えた 4 件は同じ `lines` の中の長さの差で、他の欄は動いていない。配列の長さの差を 1 件と数える Golden の diff の流儀を見ていなかった) |

### 3.2 H-9(予測 §3.2。ID 単位)

| 封筒 | 予測 NG | 実測 NG | 判定 |
|---|---|---|---|
| `0f1b019e-20261001-1/seat_gpt.json` | gpt0f1b-005 | gpt0f1b-005 | 当たり |
| `268dac98-20260930-1/seat_claude.json` | claude268d-005・-010 | 同 | 当たり |
| `52ae3745-20261001-1/seat_claude.json` | claude52ae-009 | 同 | 当たり |
| `558b8a81-20261001-2/seat_claude.json` | claude558b-004 | 同 | 当たり |
| `558b8a81-20261001-2/seat_gpt.json` | gpt558b-005・-006 | 同 | 当たり |
| `f37561e1-20260930-2/seat_claude.json` | claudef375-005 | 同 | 当たり |
| 合計 | **8 NG・50 ok・skip 0** | **8・50・0** | 当たり |
| messages | 21(VM 20 + PNF 1) | **21**(`value が packet と違う` 20・`rows[3].reviewStatus が packet に無い` 1) | 当たり |
| 数え直し `数え直し:` の行 | 0 | **0** | 当たり。**C-2 の P-10 の未測部分がここで測れた → C-2 の「半分」は当たりに**(C-2 結果へ追記) |

### 3.3 H-10(予測 §3.3)― 予測 NG 0〜6、実測 **0**(58 件とも `H-10 ok`)。当たり(幅は粗いと先に書いたとおり)。

### 3.4 H-11(予測 §3.4)

| 項目 | 予測 | 実測 | 判定 |
|---|---|---|---|
| `ok` | 58 件 true | 58 件 true | 当たり |
| `(報告)` が付く行 | **20〜58** | **4**(claude268d-005 8 行・claude558b-004 6 行・claudef375-005 11 行・claudef375-010 2 行 = 注記 27 行。名前は「英ちゃん流中飛車」「5筋位取り中飛車」「早繰り銀」「4六銀左戦法」など) | **外れ**。原因: 「名前の言及は全部注記」は正しかったが、**席の `statement`・反証の `text` が名前を含む項目は 4 つしか無い**。私は VM 18 件(観測の値に名前の配列を潰した行)を「文に名前が出る行」と取り違えて 20 以上と読んだ。観測の値と文の字は別の欄 |

### 3.5 Core の経路との一致(予測 §3.5)― **213/213**(UNVERIFIABLE 108 は H-9 の対象外なので除外)。食い違い 0。当たり。`h9_reference.ts` の写しは TS 本体と同じだった(C-2 の結果の訂正は不要)。

### 3.6 その他

| # | 予測 | 実測 | 判定 |
|---|---|---|---|
| a | `audit-core/` 差分 0 | 0 | 当たり |
| b | typecheck 新しい赤 0 | 0 | 当たり |
| c | vitest 既存と同じ本数 + 引数の試験 1〜2 | +2 | 当たり |
| d | 1 回目で予測と違う項目 0〜2(疑うのは H-10 の幅と 174 の上限) | **2**(174 の上限・H-11 の注記数)。174 は疑っていたとおり、H-11 は疑っていなかった | 当たり(上限際) |
| §2 | 将棋側 +10〜25 行 | +15/−5 | 当たり |

**集計**: 欄 16(3.1 の 4・3.2 の 3 = NG の ID・messages・数え直し(封筒 6 行は ID の 1 欄に束ねる)・3.3 の 1・3.4 の 2・3.5 の 1・3.6 の 5)のうち **当たり 14・外れ 2**(差の件数 178、H-11 の注記 4)。ID 単位の H-9 は 8/8。**封じた予測は変えていない。**

## 4. 見えたもの(S-1 が証明した範囲)

- packet を渡すだけで、Golden Master に **C-2 で Core が見つけた 21 件(VM 20・PNF 1)が将棋側の道具でもそのまま見える**。両者は観測単位で 213/213 一致。
- 証明していないこと: E-3・I-4(本番の門)に渡したときの振る舞い(S-2)。H-10/H-11 の規則の妥当性。席の封筒の中身の正否(20 件の元を直す判断は人間)。

## 5. 手順との差・記録

1. 実装担当: 作業木を書き換える git 操作を使わず、実物 c5 で回していない。変更前の数は `git worktree add --detach` の別木で測り、片づけた(`git worktree list` で確認)。逸脱なし。
2. 1 回目は計画 §4.3 のとおり、(a) 本物の期待値に対する読み取りの 1 回と、(b) 一時コピーへの `--write` の 1 回(同じ測り方の 2 度目。(c) の照合のため)。本物の期待値は書き直していない。
3. 範囲外の申し送り(実装担当): `scripts/playtest/report-pdf/render_main.py`・`render_appendix.py` は gitignore 済みの生成物で、クリーンな checkout から vitest を回すと `lib/core_boundary.test.ts` が `build.sh` 無しでは落ちる(今回は別木で symlink して回避。既存事項)。

## 6. 人間の判断(計画 §4.5。司令塔の推しを添える。決めるのは人間)

| # | 問い | 推し |
|---|---|---|
| (i) | Golden の期待値 `c5_expectation.json` を新しい現状(H-9 NG 8)で書き直すか | **書き直す**。Golden Master は「現状の固定」で判定ではない(6 封筒は元々 fail)。1 回目の差の一覧が記録として残るので、新しい現状を固定して次の変更の差が見えるようにする。書き直しは人間の GO の後に司令塔が `--write` で 1 回 |
| (ii) | S-2 = E-3・I-4(本番の門)にも packet を渡すか | **渡す。ただし S-1 と同じく、顧客の出口で何が変わるかを ID 単位で予測して封じてから**(VM 20 件の席の文が本番の門で止まるなら顧客の冊子の中身が変わりうる) |
| (iii) | 20 件の元(席が `names` の配列を「A+B+C」に潰す 18・数の差 2)を席の指示文で直すか | **直す。先に席の指示文の 1 行で何件直るかを予測してから**。数の差 2(shallowVisibleGames 25/24、aheadThenLost 分母 2/4)は席の数え間違いか packet の定義の読み違いかを 1 件ずつ読んでから |

## 7. この文書がしないこと

期待値の書き直し。E-3・I-4 への配線。席の封筒の修正。H-10/H-11 の規則の変更。`audit-core/` の変更。
