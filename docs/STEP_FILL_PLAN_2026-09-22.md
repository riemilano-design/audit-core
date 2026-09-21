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
4. 司令塔が、2 人目の 44 局を新しい作業フォルダで測り直し(エンジン 5 本、約 1.5 時間)、まとめと付録を作り直す。**前後で変わった数を、表にして人間に報告する**(崩れの数・分母・場面の数・終局の評価)。

## 5. やらないこと

- 本番の `measureEngineReference`・③の動きを変えること。
- 勝った局の最後の局面(相手の手番)の評価。要るとなれば別の STEP。
- `records/` の 30 局を測り直して置き換えること(4M と 2 段階の不ぞろいは、別の判断)。
- Gate の値・選び方の値・形勢の段の境を変えること。
