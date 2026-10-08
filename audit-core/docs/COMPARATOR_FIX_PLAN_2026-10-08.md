# 封 ③-1 ― 照合器を直す(最大マッチング・重なり最大の導出・claim の同一性・自己試験 3 本)

2026-10-08。**費用 0 円・LLM を 1 回も呼ばない。** 人間の承認は 2026-10-08 夜(1〜5 の順で連続して進める)。
**予測は封じた後に書き換えない。**

## 1. 司令塔の決定(実装担当は仕様を決めない)

**決-A: 既存の関数と出力を 1 つも変えない。新しい関数を足す。**
`compareClaimDecomposition` の返り値の既存の欄(`span` / `spanMatchedCount` / `valueMatchCount` /
`formMatchCount` / `formBreakdown` / `uncovered`)は**そのまま**。
理由: **「修正前」の数を repo のコードで再現できる状態を残す。** 直す前の数が消えると直した効果を示せない。

**決-B: `hostSentenceOf(sentences, span)` を足す(重なりが最大の文)。**
- 重なり = `min(span[1], s.end) - max(span[0], s.start)`。**最大のものを選ぶ。**
- **同点のときは `start` が小さい文**(規則で固定。実装担当に選ばせない)。
- 重なりが **0 以下しか無いときは `undefined`**。

**決-C: 文ごとの対の付け方は最大マッチング。**
- 辺の重み: **value と form の両方一致 = 2 / どちらか一方だけ一致 = 1 / どちらも不一致 = 0**。
- **片側の件数が 8 以下なら全探索**、**9 以上なら貪欲に落とし、その文の数を `greedyFallbackSentences` に入れる**
  (落ちたことを隠さない)。
- `value` の比べ方は既存と同じ(`===`)。**正規化を足さない**(足すなら別の封)。

**決-D: claim の同一性を返す。**
```
pairs: Array<{ goldIndex, actualIndex, sameSentence, valueMatch, formMatch }>
goldUnmatched: number[]   // 対応が付かなかった正解の添字
actualUnmatched: number[] // 対応が付かなかった実測の添字
sentenceCorrect: number   // 正解の導出文と実測の導出文が同一のものの件数
```
**`sentenceCorrect` は「別の正解の文に当たった」場合を一致に数えない。**

**決-E: 自己試験 3 本を同じ封で足す。**

| | 内容 |
|---|---|
| **S-A** | `gold_01..04` の `expected_claims` を**そのまま実測として**渡すと、4 本すべてで **1 対 1 完全対応・`sentenceCorrect` = 正解件数・`valueMatch` 全件・過剰 0** |
| **S-B** | 実測の `claims` 配列を固定の種(`20261008`)でシャッフルしても、**新しい関数の返り値が同一** |
| **S-C** | 実測の span を **−4 / −1 / +1 / +4** 字ずらしても、**span の長さが 8 字以上の claim について選ばれた文が変わらない** |

## 2. 範囲

- 触るのは **`scripts/playtest/lib/decompositionCompare.ts` と `decompositionCompare.test.ts` だけ。**
- **`claimDecomposition.ts` は触らない**(`splitIntoSentences` は import して使うだけ)。
- `runClaimDecomposer.ts` は**触らない**(新しい関数の配線は次の封)。

## 3. 触ってはいけないもの

`scripts/playtest/fixtures/decomposition/gold_0*.json`(1 バイトも) / `audit-core/core/py/` / `audit-core/adapters/` /
`docs/golden_master/` / 封じた予測の節(この §4 を含む) / `scripts/playtest/out/` への書き込み。

**実装担当・監査担当は鍵を使わない**(`.env` を読まない・表示しない・鍵の有無の `grep` もしない。
`runSeats.ts` と `runClaimDecomposer.ts` を本番でも `--dry-run` でも走らせない。
`deliver.ts` / `goldenMasterCheck.ts` / `seatOutputCheck.ts` / `hypothesisCheck.ts` / `exitSelect.ts` を
実物の `out/` に対して走らせない ― 門の出力を見たいときは関数を直接呼ぶ)。
**木を書き換える git は使わない**(変異は `git worktree add --detach`、`git worktree remove --force` で消す)。
根からの vitest は `--exclude '**/.claude/worktrees/**'`。

## 4. 封じる予測(T-1〜T-10)

| | 予測 | どうやったら外れるか / 外れ方は何通りか(**照合器が間違いを当たりと数える経路を 1 行入れる**) |
|---|---|---|
| **T-1** | 既存の 6 欄の値は **4 本すべてで 1 つも動かない** | **2 通り。** 動く = 既存の経路に手が入った(決-A 違反) / 新旧で同じ補助関数を共有して既存の挙動が変わる |
| **T-2** | 新しい関数で `sentenceCorrect` は **37 / 37** | **3 通り。** 36 以下 = 重なり最大でも外れる文がある / 38 以上は定義上ありえない(あれば同一性の数え方の欠陥) / **別の正解の文に当たったものを数えてしまって 37 に見える**(= `pairs` の `sameSentence` を見ずに件数だけ数えた) |
| **T-3** | 新しい関数で **value 一致 37 / 37・form 一致 33 / 37** | **3 通り。** value 36 以下 = 最大マッチングが貪欲より悪い(実装の誤り) / 38 以上 = 1 対 1 が壊れている / form 34 以上 = 重みの付け方が form を優先している |
| **T-4** | `actualUnmatched` は **19 件**(56 − 37) | **2 通り。** 20 以上 = 1 対 1 が付かない claim がある / 18 以下 = 1 つの実測を 2 つの正解に使い回している |
| **T-5** | `greedyFallbackSentences` は **0**(1 文に 9 件以上の claim がある文は無い) | **2 通り。** 1 以上 = `gold_03` のような密な本にある / 数えていない(欄が無い) |
| **T-6** | **壊した照合器で S-A が赤**(`hostSentenceOf` を「開始位置が入る文」に戻すと `gold_04` が自分自身と照合しても満点にならない) | **2 通り。** 赤くならない = S-A が実物の 4 本を見ていない / 別の理由で赤くなる(例外で落ちる) |
| **T-7** | **壊した照合器で S-B が赤**(対の付け方を配列の順に戻すとシャッフルで結果が変わる) | **2 通り。** 赤くならない = シャッフルが同じ文に 2 件以上ある場合を踏んでいない / 種が固定されていない |
| **T-8** | **壊した照合器で S-C が赤**(文の選択を `span[0]` が入る文で決めると −4 で前の文に移る) | **2 通り。** 赤くならない = ずらす幅が足りない / 8 字以上の条件で対象が 0 件になる |
| **T-9** | 既存の試験は **赤 0 本**(既存の欄を変えないので) | **2 通り。** 1 本以上赤 = 決-A 違反 / 0 本だが新しい関数を見る試験が無い(= 試験が弱い) |
| **T-10** | Core は **0 行**。`claimDecomposition.ts` は **0 行** | **2 通り。** どちらかに手が要る(そのときは止めて人間へ) |

## 5. 工程

実装担当 → 司令塔が sha 一覧で凍結 → **独立監査の GO** → パス指定でコミット → 既存 4 本を**新旧並べて**採点し、
`COMPARATOR_FIX_RESULT_2026-10-08.md` に T-1〜T-10 の採点と**壊した照合器の赤の出力**を貼る。
**監査が同じ封を 2 回差し戻したら止めて人間へ。**
**自己試験が、壊した照合器で赤くならなかったら止めて人間へ。**
