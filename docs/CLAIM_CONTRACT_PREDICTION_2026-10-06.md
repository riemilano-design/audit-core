# Claim Contract 仕様 v0.1 ― 表現可能性の事前予測(封印。2026-10-06)

**この文書は、実在の Claim を形と修飾に分解する前に書き、コミットで封じる。** 分解の結果は [CLAIM_CONTRACT_SPEC_v0.1.md](CLAIM_CONTRACT_SPEC_v0.1.md) §7 に書き、この予測との一致・不一致を同 §11 に書く。**この文書は封じた後に書き換えない**(訂正は §11 に書く)。

| 項目 | 値 |
|---|---|
| 対象 | `scripts/playtest/out/c5/deliver1/9_本編.md`(sha256 `eb4c0b1e231e040f57db56cbe6fcca63145484cee560e6dad3af48f1eb9d7cbc`、9240 bytes。Golden Master `docs/golden_master/c5_expectation.json` の identity と同じ) |
| Claim の一覧 | 仕様書 §5 の C-01〜C-38(分解していない。原文の区間と行番号だけ) |
| 形の案 | 4 つ: `direct_value` / `derived_value` / `aggregate` / `threshold` |
| 修飾の案 | 3 つ: `time_range` / `population` / `normalization`(雑談で合意した案。足りるかをここで予測する) |
| 予測を書いた席 | 司令塔(設計した席と同じ。独立性は無い ― 仕様書 §13 に明記) |
| 予測を書く前に見たもの | 門 6 種のコード(`exit_verification.py`・`check_answer.py`・`check_structure.py`・`hypothesis.ts`・`seatOutput.ts`・`integration.ts`)、packet の集計 26 行と閾値 6 本、`exit_candidates.json`、`answer_selection.json`。**C-01〜C-38 を形に当てる作業はしていない** |

## 0. 判定の 3 値(分解の結果をこの 3 つで数える)

| 記号 | 意味 |
|---|---|
| **A** | 表現可・契約充足。形と修飾で書け、契約の必須欄が全部埋まり、検証レシピが packet か登録簿に届く(結果は GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND のどれか) |
| **B** | 表現可・契約不充足。形には当たるが必須欄が埋まらない(閾値の承認記録が無い・比べる相手の数が無い等)→ Core の判定は UNVERIFIABLE |
| **C** | 表現不能。4 つの形のどれにも当たらない(定義・不在・約束・工程の状態など) |

## 1. 単位ごとの予測(C-01〜C-38。a/b は仕様書 §5 の分け方に従う)

| Claim | 予測 | 根拠(予測時点の読み) |
|---|---|---|
| C-01a 25 局・3 分切れ負け・日付 | A | `facts.games` の件数・`timeLimitSec`・`provenance.generatedAt` |
| C-01b 「1 手ずつ」 | B | 網羅性の主張。契約に「網羅」の欄が無い |
| C-02 両方の側に残り | B | 「>0」は閾値だが、0 を閾値として承認した記録は無い(存在の比較子を承認なしで許すかの設計論点になる) |
| C-03 長考の直後の 1 手は崩れやすく | B | 比べる線「2 つぶん」は道具の仮置きで承認記録が無い |
| C-04 一度良くなった局を落としていた | A | `aheadThenLost` 6 / 18 |
| C-05 普段と違う型の 4 局で目立った | B | 「目立った」に閾値が無い |
| C-06 数は 3 つ | A | 文書自身への集計(門 (ii) が数えている)。**出どころが packet ではなく文書**なので修飾 `source_kind` が要る |
| C-07 107 のうち 65 | A | `sideMatch.attack` |
| C-08 132 のうち 76 | A | `sideMatch.defense` |
| C-09 どちらの一致率も線(0.7)を下回った | B | 0.7 は `provenance.thresholds` に無い。承認記録も無い、と読む |
| C-10 偏りではなく両方の側で | B | 比較の語に閾値が無い |
| C-11 37 手のうち 9 | A | `time.quickAfterLongThink`。10 秒・4 秒は `provenance.thresholds` に在る |
| C-12 531 手で 22 | A | `time.bySpent0to1` |
| C-13 それより崩れる割合が高かった | B | 比較は再計算できる(9/37 と 22/531)が「高い」の線が承認されていない |
| C-14 優勢(+300 以上)が 18 局 | A | `aheadThenLost` の分母。300 は `ahead_cp` |
| C-15 そのうち負け 6 局 | A | 同上の分子 |
| C-16 負けた局の多くは一度は良くなってから | B | 6 / 負け局数(集計行が無く再計算は要る)。「多く」に線が無い |
| C-17 分けて数えた材料がまだ無い | C | 不在の主張(登録簿に無いことを言う形が無い) |
| C-18 次の 25 局で分けて数えます | C | 約束。Prediction Ledger の登録であって 4 形の主張ではない |
| C-19 25 局で 51 局面 | A | `sideMatch.oppositeAll` の分子 |
| C-20 攻めと自玉側を 1 つずつ | A | 盤 2 枚の `top1Side` |
| C-21 11 局目 48 手目の手と性質 | A | `facts.engine[354]`・`facts.branches` の tags/side。語への写しは `normalization`(語彙表) |
| C-22 12 局目 70 手目 | A | 同上 |
| C-23a 2 つです | A | 文書自身への集計(`source_kind` = 文書) |
| C-23b 差が確認でき測り直せるものだけ | B | 選別の基準。`menuPassed` には届くが「測り直せる」の欄が無い |
| C-24 行動 1 の文と根拠 | A | 承認済みの表 `ANSWER_MENU` との一致(`source_kind` = 登録簿)+ 分数 |
| C-25 行動 2 の文と根拠 | A | 同上 |
| C-26 線 0.7・下回ったので行動に | B | C-09 と同じ |
| C-27 61 手のうち分かれ道 33、逆は 5 | A | `longThink.total/fork/opposite` |
| C-28 239 のうち逆は 51 | A | `sideMatch.oppositeAll` |
| C-29 逆の多くは 10 秒未満 | B | 51 − 5 = 46 は再計算できるが「多く」に線が無い |
| C-30 線は 2 つぶん・上回ったので行動に | B | C-03 と同じ |
| C-31a 駒を打つ手 54 局面 | A | `repro.top1Drop.positions` |
| C-31b 比べる線がまだ無く | C | 不在の主張 |
| C-31c 分母の数え方を確かめ直している | C | 工程の状態(データでも登録簿でもない) |
| C-32 答え合わせの表 | C | 予測の登録だが比較子と値が無い(H-4 の形を満たさない)。4 形の主張としては表現不能 |
| C-33 「崩れ」の定義 | C | 定義の主張。比べる相手は定義の正本(文書)で、4 形に無い |
| C-34a 18 局・4 局・3 局 | A | `groups.*.games` |
| C-34b 定義が下書きなので名前を付けていない | A | `recognition.definitions[].reviewStatus` が全部 draft(集計)+ 本文に名前が無い(H-10/H-11 の機構) |
| C-35 群の表 9 セル | A | games・collapses・aheadThenLost は集計行に在る。**側の一致 6 セルは集計行に無い** → `facts.branches` と `recognition.rows` を gameId で結んで再計算すれば出る、と読む(修飾 `join` が要る) |
| C-36a 4 局とも優勢・3 局落とした | A | `groups.other.aheadThenLost` 3 / 4 と `groups.other.games` 4 |
| C-36b 1 局あたり多く | B | 18/4 と 56/18 は再計算できるが線が無い |
| C-36c 優勢になってからの崩れが出やすかった | B | 数が無い比較。C-17 が「材料が無い」と言う同じものを言っている(両立しない 2 文) |
| C-37 分母の表 10 行 | A | 0.7 の行だけ B |
| C-38 対応表 25 行 × 4 列 | A | `facts.games[]` の src・side・totalPlyCount・result |

## 2. 数の予測

| 数 | 予測 |
|---|---|
| 単位の数(a/b を分けた後) | 45 |
| A | **25** |
| B | **14** |
| C | **6** |
| 4 つの形で足りるか | **足りる**(A と B は 4 形のどれかに当たる。C は全部、数でない主張) |
| 形の使われ方 | `aggregate` が最多。`threshold` は B に集中する(線の承認記録が無いため) |
| 修飾 3 つで足りるか | **足りない**。少なくとも 2 つ足す: `source_kind`(packet / 登録簿 / 文書自身 / 承認済みの固定文 / 人間の文)と `join`(gameId で表を結ぶ)。`unit` と `threshold_ref` は修飾でなく契約の欄として要る |
| `time_range` の出番 | **0〜1 回**(C-01a の日付だけ。将棋の 25 局には時間の範囲の主張が無い) |
| C-35 の側の一致 6 セル | 再計算で **6 / 6** 一致する |
| 0.7 と「2 つぶん」の承認記録 | packet に無い(確認済み)。docs にも「承認」の記録は無い、と読む → B |
| 門に無い契約欄 | `approval_record`・`tolerance`・`source_kind`・`registration_time` の 4 つは門のどれも持っていない |
| 両立しない 2 文 | C-17 と C-36c の 1 組。契約には「主張どうしの整合」の欄が無い(集計の整合関係 (5) は集計行の話) |

## 3. 外れたときの読み方

- A が予測より少なければ、契約の必須欄を厳しく置きすぎている(承認記録の要求が実物を落とす)。
- C が予測より多ければ、4 形では将棋の冊子すら書けない ― 形を足す前に「数でない主張を Core が扱うか」を設計論点に戻す。
- `time_range` が 2 回以上使われたら、将棋にも時間の主張が隠れていた(XBRL を待たずに修飾の契約が試せる)。
