# STEP FILL 計画: 一本の流れの 4 つの穴を埋める(2026-09-22、司令塔 e3)

人間の指示(2026-09-22「穴埋めて」)。2 人目の 44 局を通して見つかった穴(STEP PIPE 計画 §5.5、STEP BASE 計画 §8.5)を埋める。

位置づけ: `scripts/playtest/` の開発補助(対局後診断の側)。**本番導線(`apps/`)・`data/`・Gate の値・承認済みの条件式・`records/` の既存の記録は変えない。**

## 1. 穴と、調べて分かったこと

| # | 穴 | 調べて分かったこと |
|---|---|---|
| H1 | 本人が王手を受けている局面に評価が付かない | `apps/server/src/analysis/engineReference.ts` の `measureEngineReference` が、王手中は `reference: null` を返す(パスが成立しないため。本番の③のための作り)。`lib/failureEvent.ts` の `evaluationOf` は `notMeasuredInCheck` にする。3 分の第 9 局は 82 手目の後が全部これで、+3000 前後から本人の玉の詰みへ変わった 1 手が、グラフ・組・場面から抜けた |
| H2 | 最後の手の後の局面に評価が付かない | **負けた局では、ほぼ H1 と同じ穴だった。** 投了・切れ負けの局面は本人の手番なので、ready の行としてすでに記録にある(例: 3 分の第 2 局は末尾 +1513)。空になるのは、その行が王手中のとき(3 分の第 4 局など)。勝った局(相手の手番で終わる)の最後の局面は、今回は対象にしない |
| H3 | `pipeline.ts` の `--work` を相対パスで渡すと pdf の段だけ失敗 | `render_main.py` を `report-pdf/` を作業フォルダにして起こすため |
| H4 | 凍結した第 6 版の PDF の道具が 20 局・1 冊を前提にしている | 「20 局」が固定の文、題に「優勢のまま投了で終わった」が無い |

## 2. 作業 X: 王手中の局面に、現局面だけの評価を付ける(H1・H2)

**本番の `measureEngineReference` は変えない。** ハーネスの側に、別の欄を足す。

- **記録(段 1、`lib/recorder.ts`)**: ready の行で `engineReference` が null、かつ終局でなく、本人(先手の側)が王手中のとき、**現局面だけ**を MultiPV 1・`referenceNodes` で読み、新しい欄 `checkBaseline: { scoreCp, mate, bestmove, nodes } | null` に書く(測れなかったら null。王手中でない行には欄を出さない)。`engineReference` 自体は null のまま(「パスの比べは測っていない」という意味を保つ)。測る関数はハーネスの側(`scripts/playtest/lib/`)に置く。`apps/` に足さない。
- **記録(段 2、`lib/rescreen.ts`)**: 深く読み直す行に選ばれた行が王手中なら、同じ形で `checkBaselineDeep` を書く。選び方(`DRAFT_SCREEN_RULE_1`)の値は変えない。王手中の行が選ばれるかどうかは、軽い値の読み取り(下)が変わる結果として決まる。
- **読み取り(`lib/failureEvent.ts` の `evaluationOf`、と深い値の側の同じ役の関数)**: `engineReference` が null・王手中・`checkBaseline` に値がある行は、`state: "measured"`(`afterPassScoreCp`・`afterPassMate`・`dropCp` は null)にする。`checkBaseline` が無い古い記録は、これまでどおり `notMeasuredInCheck`。**`records/` の 30 局の診断・判定・レポートの材料の出力は 1 バイトも変わらないこと**(試験か実測で確かめる)。
- `|scoreCp| ≥ NOT_EVALUATION_CP` の扱い(`notEvaluation`)は、`checkBaseline` にも同じに当てる。
- 下流(組・形勢の段・Failure Event・判定・基準値・レポートの材料)が、`measured` なのに afterPass の側が null の行で落ちないこと。落ちる所があれば、その行を「パスの比べは無い」として扱う最小の直しにとどめ、直した所を報告する。
- 試験: エンジンを起こさない(measure を差し替える)。王手中の行に欄が出る / 王手中でない行には出ない / 終局は測らない / 古い記録は前と同じ / 深い側 / `notEvaluation`。
- **完了の確かめ(実装担当はエンジン 1 本まで使ってよい)**: gitignore の `out/tatsunami3/kifu/` の第 9 局だけを、新しい作業フォルダで段 1 → 段 2 → 診断まで通し、82 手目の後の行に評価が入ること、形勢の段が 優勢 → 劣勢 へ変わる組が 1 つ以上できることを見る。**出力の中身(手・値)は報告に書かず、件数と有無だけを書く。**

## 3. 作業 Y: 相対パスと、PDF の道具の 20 局前提(H3・H4)

- **H3**: `pipeline.ts`(または `lib/pipeline.ts`)で、`--work`・`--kifu-dir`・`--compare-dir` を受け取った時点で絶対パスにする。相対パスで `--until pdf` まで通る試験(エンジンも python も起こさない形でよい。いまの試験の流儀に合わせる)。
- **H4**: `report-pdf/` の `_head.py`・`_mid.py`・`_tail.py`(と別冊の側)で、
  1. 固定の「20 局」を、データの局数(`summary.games`)から入れる。文の数の照合(`allowed_numbers`)の 20 も同じに。
  2. 題の決め方に 1 つ足す: 負け・切れ負けでない・最後の評価が +300 以上 → 「盤上は優勢のまま、投了で終わった将棋」。置く位置は「盤上は優勢のまま、持ち時間切れで負けた将棋」の次。
  3. そのほか、局数や比較対象の数が固定で入った文を洗い出す。データから取れるものは置き換え、取れないものは一覧にして報告する(直さない)。
- **縛り: 2 人目の前の 20 局(第 6 版)の入力では、出力が変わらないこと。** STEP PIPE の完了条件 (a)(`patient_report_data.json` の完全一致、本編 14 ページの本文の完全一致)を、直しの後にもう一度実測する(手順は STEP PIPE 計画 §5.2・§5.3、`report-pdf/README.md`)。
- 「凍結」の意味は「第 6 版の入力で同じものが出る」に改める。README を直す。

## 4. 体制

1. この計画をコミット(docs のみ、司令塔)。
2. 作業 X・作業 Y を、別々の使い捨ての実装担当(worktree)に並行で出す。触るファイルは重ならない(X: `lib/recorder.ts`・`lib/rescreen.ts`・`lib/failureEvent.ts` と下流の最小の直し・試験・README / Y: `pipeline.ts`・`lib/pipeline.ts`・`report-pdf/`・試験・README の別の節)。README は両方が触るので、節を分ける。
3. 独立の監査は、X・Y それぞれ 1 回。GO の後に司令塔がコミット。
4. ~~司令塔が、2 人目の 44 局を新しい作業フォルダで測り直し、まとめと付録を作り直す。~~ **(2026-09-22 人間の決定)今回の 44 局は測り直さない。** 大きな変化は見込まれないため(司令塔の見込み: 増えるのは王手中の場面の数件。主な発見 3 つは、終局の局面の別の評価と棋譜の消費時間から出しており、測り直しと関係がない)。今回の冊子は、王手中の穴を文で書き添えた下書きのまま使う。**直しは、次に通す棋譜から効く。** 次の人・次の 20 局を通すときに、王手中の行に評価が入っていること(`checkBaseline` の欄の数 > 0 の局があること)を、司令塔が 1 回確かめる。

## 5. やらないこと

- 本番の `measureEngineReference`・③の動きを変えること。
- 勝った局の最後の局面(相手の手番)の評価。要るとなれば別の STEP。
- `records/` の 30 局を測り直して置き換えること(4M と 2 段階の不ぞろいは、別の判断)。
- Gate の値・選び方の値・形勢の段の境を変えること。

## 6. 実装と監査の記録

### 6.1 作業 X(王手中の局面に現局面だけの評価、2026-09-22)

- **実装**(使い捨ての実装担当、worktree): 新規 `lib/checkBaseline.ts`(`measureCheckBaseline`。MultiPV 1・nodes 固定、先手視点。`apps/` の `sideFromMultiPv` と同じ読み方)と試験 4 本(25 件)。`lib/recorder.ts`(ready の行で `engineReference` が null・終局でない・王手中・`referenceNodes` > 0 のとき `checkBaseline` を書く)、`lib/rescreen.ts`・`rescreen.ts`(読み直す行が王手中なら `checkBaselineDeep`。`DeepRunInput` の任意項目 `checkMeasure` 経由)、`lib/failureEvent.ts` の `evaluationOf`(王手中で `checkBaseline` に値があれば `measured`、afterPass の側と `dropCp` は null。両方 null は `notMeasurable`、|scoreCp| ≥ `NOT_EVALUATION_CP` は `notEvaluation`、欄なし・null は従来どおり `notMeasuredInCheck`)、`lib/screenDiagnosis.ts` の `deepRowOf`(深い側は `checkBaselineDeep` に差し替えて同じ `evaluationOf` へ)、`invariants/types.ts`、README。**`apps/`・`data/`・`records/`・値(`DRAFT_SCREEN_RULE_1`・`STANDING_BOUNDS`・`NOT_EVALUATION_CP`・GATE_VALUES)は変えていない。**
- **実装側の実測**: 3 分の第 9 局 1 局をエンジン 1 本で診断まで通し、`checkBaseline` 8 行(全部 `measured`)、`checkBaselineDeep` 6 行、形勢の段が 優勢 → 劣勢 へ変わる組が 1 つできた(件数のみ)。`records/real-02`・`real-01` で diagnose・gate の Markdown の sha が直しの前後で一致。変異 4 本 red。
- **独立監査 1 回: GO。** 監査の実測: sha 一致、差分の範囲、符号の向き(`measureEngineReference` の baseline と同じ先手視点)、`records/` の 157 ファイルに `checkBaseline` の欄が 0 件、王手中の行を含む `real-03` の 15 局で diagnose の出力が本体と worktree で一致(出どころの gitHead・dirty を除く)、JSON Schema は afterPass の側の null をもともと許す、下流に非 null の決めつけなし、段 2 の S-19(measure の回数 = deepPlies の数)と矛盾しない、抜き取りの変異 2 本 red。
- **司令塔の確かめ**: 監査の後の sha の照合(監査が変異の復元で 1 度 `failureEvent.ts` を巻き戻し、sha で気づいて戻している。最終の sha は実装側の報告と一致)、feature の先頭へ載せ替えた後に 型検査 rc=0・vitest 69 ファイル 1071 件・check-docs rc=0。
- **既知事項(監査)**: `checkBaseline: null`(測ろうとして測れなかった)と欄なし(測っていない)が、`evaluationOf` ではどちらも `notMeasuredInCheck` に丸められる。偽の `measured` は出ないが、集計の列がわずかに不正確になりうる。同じ形の欄を足すときは踏襲しない。
- **測っていないもの**: `reportData.ts` の出力の不変(`records/` の入力で)。`real-01`・`02`・`03` 以外の `records/`。エンジン 5 本での所要の増え方。

### 6.2 作業 Y(相対パスと、PDF の道具の 20 局前提、2026-09-22)

- **実装**(使い捨ての実装担当、worktree): `lib/pipeline.ts` の `parsePipelineArgs` で `--work`・`--kifu-dir`・`--compare-dir` を絶対パスにする(新規 `lib/pipelineAbsolutePath.test.ts`)。`report-pdf/` の `_head.py`・`_mid.py`・`_app.py` で、固定の「20」をデータの局数から入れる。題に「盤上は優勢のまま、投了で終わった将棋」を足し、数え方 `n_la_resigned_ahead` を足した(該当 0 局のとき 1 ページ目の文は元と同じ)。README の「凍結」の説明を「第 6 版の入力で同じものが出る」に改めた。
- **独立監査 1 回: REVISE → 直し → 司令塔が確かめてコミット**(往復 1 回の規則)。
  - 監査の実測: 第 6 版の入力で本編・別冊の PDF がバイト数まで同じ。14 局の入力で rc=0・「20 局」0 件・新しい題 3 局。相対パスの変異は red。
  - **指摘(重大)**: 新しい題の条件が「切れ負けでない」だけで、詰み・反則負け・終局の記録なしの負けも「投了で終わった」と断定してしまう(手元の 74 局には該当が無く、表に出ていなかった)。→ 終局の語が「投了」の局だけに限った。それ以外は直しの前と同じ分岐へ流す。合成の局(詰み・反則負け・記録なしで +300 以上の負け)が新しい題にならないことを実装側が実測。
  - 司令塔の確かめ: 直しの差分の目視、sha の照合、feature の先頭(作業 X の後)へ載せ替えた後に、第 6 版の入力で本編の本文が直しの前の道具と完全一致(14 ページ・11225 字)、型検査 rc=0・vitest 70 ファイル 1076 件・check-docs rc=0。
- **既知の限界(監査が実証)**: python の道具は vitest の対象外で、守りは「第 6 版 20 局で本文が変わらない」の実測だけ。**該当が 0 件の分岐の誤りは、この確かめをすり抜ける**(分岐の順を入れ替える変異で、20 局の本文は 1 文字も変わらなかった)。分岐を足すときは、該当が 1 件以上出る入力でも本文を確かめる(`report-pdf/README.md` に書いた)。
- そのほかの既知の限界: 本編に「比較対象の 10 局」が固定で残った文が 4 か所ある(データに数が無い)。「次の n 局で」は今回の局数で書かれる。別冊は `reportData.ts` の出力からは作れないまま(STEP PIPE §5.2)。**古い記録(王手中の評価が無い)では、最後の評価が実際と違うことがあり、題が誤ることがある**(3 分の第 9 局。作業 X の後に通した記録では起きない)。
