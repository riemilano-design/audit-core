# report-pdf/ ― 対局後診断レポートの PDF を作る道具(STEP PIPE 作業 B、S7)

凍結した第 6 版テンプレート(`scripts/playtest/out/report-template-v6/`、gitignore・読むだけ)の python(reportlab)6 本を、
docs/STEP_PIPE_PLAN_2026-09-21.md §2.2 の S7 としてここへ移したもの。

**「凍結」の意味(STEP FILL 作業 Y、docs/STEP_FILL_PLAN_2026-09-22.md §3 で改めた)**: ソースの文字列を今後も一切変えない、という
意味ではない。**2 人目の前の 20 局(第 6 版)の入力で通したとき、出力(`patient_report_data.json`・本編 PDF の本文)が
変わらない**ことを指す。以前は局数などが「20」のように直接書かれていた箇所があり、ほかの局数の入力(14 局等)では
1・2 ページ目や最後のページの文が実際の局数と食い違っていた(docs/STEP_PIPE_PLAN_2026-09-21.md §5.5 の 4)。この STEP で、
局数が固定で入っていた文をデータ(`summary.games` 等)から出すように直した。20 局の入力なら直す前と同じ「20」が出るため、
第 6 版の出力そのものは変わらない(直しの前後で `patient_report_data.json`・本編 PDF の本文の完全一致を確かめた)。

## 変えたところ

- `_head.py`・`_util.py`・`_mid.py` の 3 行だけ、`prose.json`・`sfens.json` の置き場を環境変数 `REPORT_DATA_DIR` で渡せるようにした
  (既定はこれまでどおり、道具と同じフォルダ)。
  - `_head.py`: `_here` の後に `_data_dir = os.environ.get("REPORT_DATA_DIR", _here)` を足した
  - `_util.py`: `SF = json.load(open(os.path.join(_here, "sfens.json"), …))` → `os.path.join(_data_dir, "sfens.json")`
  - `_mid.py`: `PROSE = json.load(open(os.path.join(_here, "prose.json"), …))` → `os.path.join(_data_dir, "prose.json")`
- STEP FILL 作業 Y(H4、docs/STEP_FILL_PLAN_2026-09-22.md §3)。`_head.py`・`_mid.py`・`_app.py` の固定の「20 局」を、
  データの局数(`m["summary"]["games"]`)から出すようにした(`_mid.py` の `allowed_numbers` の照合が許す数のリストも同じ)。
  題の決め方に 1 つ足した(`_head.py` の `game_facts`): **負け・終局の語(`ending`)が「投了」・最後の評価が +300 以上** →
  「盤上は優勢のまま、投了で終わった将棋」(「盤上は優勢のまま、持ち時間切れで負けた将棋」の次)。
  - **独立監査 REVISE(2026-09-22)で直した点**: 当初は「切れ負けでない」だけで判定しており、詰み・反則負け・終局の記録なしの
    負けまで「投了で終わった」と誤って断定していた。`g.get("ending")`(`lib/kifuImport.ts` の `ENDING_KIF_WORDS` の日本語語。
    `reportData.ts` の `endingTextOf` がそのまま `patient_report_data.json` の `ending` に書く)が実際に「投了」であることを
    見て判定するように直した。投了でない「終局の記録あり・切れ負けでない・+300 以上」の負け(詰み・反則負け等)と、
    終局の記録が無い負けは、この分岐に入れず、直しの前と同じ `ever_ahead` の分岐(「一度は良くなったが…に崩れた将棋」)へ流す。
  - これに伴い、1 ページ目・まとめの「n 局は優勢になった後に形勢が崩れ、n 局は優勢のまま持ち時間が切れています」を、該当局が
    1 局以上あるときだけ「、n 局は優勢のまま投了しています」を足す形にし(`_mid.py` の `n_la_resigned_ahead`。`_head.py` の
    `game_facts` が返す `resigned_ahead` と同じ条件)、
    `assert n_la_collapsed + n_time_ahead + n_la_resigned_ahead == len(la)` に直した(該当局が 0 局のとき ― 第 6 版の
    20 局を含む ― は元の文・assert と結果が変わらない)。
  - **レイアウト・文言・照合の規則そのもの(`_mid.py` の `allowed_numbers` の作り・`BANNED` 語のリスト)は変えていない。**
  - **データから取れない固定の数は変えていない(直さない)**: `_mid.py`(本編)の「比較対象は…対局 10 局です」等 ―
    本人向けの `patient_report_data.json` には比較対象側(試す側)の局数が入っていないため、本編の側からは出せない
    (`_app.py`(別冊)は `audit_metrics.json` に `candidate.test.games` があるので、そちらは直した)。`_app.py` の
    判定のしきい値(「2 倍以上かつ 10 ポイント以上」等)も、局数ではなく判断的な基準値なので変えていない。
  - **「次の {局数} 局で確かめます」の 2 か所も `summary.games`(今回と同じ局数)に置き換えたまま**(司令塔の判断、
    2026-09-22。第 6 版の不変を優先。下の「既知の限界」参照)。

フォント(`_here/fonts/…`)の探し方は変えていない(`_here` は道具のあるフォルダのまま)。

## 使い方

1. `./build.sh` で `render_main.py`(本編)・`render_appendix.py`(別冊)を作る(`_head.py`・`_util.py`・`_mid.py` / `_head.py`・`_util.py`・`_app_head.py`・`_app.py`・`_tail.py` を連結するだけ。コミット対象ではない ― `.gitignore` 参照)。
2. `patient_report_data.json`・`audit_metrics.json`(`scripts/playtest/reportData.ts` の出力)と、`prose.json`・`sfens.json`(`reportData.ts --out-sfens` と、`prose-request.md` から人が書いたもの)を 1 つのフォルダに置く。
3. 本編: `REPORT_DATA_DIR=<そのフォルダ> python3 -X utf8 render_main.py <patient_report_data.json> <出力 PDF>`
4. 別冊: `REPORT_DATA_DIR=<そのフォルダ> python3 -X utf8 render_appendix.py <audit_metrics.json> <出力 PDF>`
   (`REPORT_DATA_DIR` を渡さなければ、`patient_report_data.json`・`audit_metrics.json` と同じフォルダに `prose.json`・`sfens.json` を置く、これまでどおりの使い方でよい)

`prose.json` が無ければ `_mid.py` の `json.load` で例外になり、本編は作られない(「言い換えが要る」の判断は `reportData.ts` の `prose-request.md` 側。ここでは止まるだけで、止まり方自体は変えていない)。

## 依存

`reportlab`・(埋め込み確認をするなら)`pymupdf`(`fitz`)。どちらも利用者の Python の site-packages にあることを前提にする(この STEP では固定しない。docs/STEP_PIPE_PLAN_2026-09-21.md 4.)。
埋め込める日本語フォントが無ければ `_head.py` が止まる(`fonts/IPAexfont00401/ipaexg.ttf` か、いくつかの既定の場所を探す。この規則は変えていない)。

作った PDF の全書体が埋め込みかどうかの確認は、いまは人(司令塔)が pymupdf で確かめる手作業(docs/STEP_PIPE_PLAN_2026-09-21.md §2.2 の指示どおり)。

## 付録 2「分かれ道」(`render_whatif.py`。STEP WHATIF 作業 2、docs/STEP_WHATIF_PLAN_2026-09-22.md §2.3・§7.3)

`render_whatif.py` は、上記の凍結した 6 本(`_head.py`・`_util.py`・`_mid.py`・`_app_head.py`・`_app.py`・`_tail.py`)とは**別の、単体の新規ファイル**である。`build.sh` では作らない(`_head.py`・`_util.py` を `cat` で連結する対象に含めていない ― これらは断片ファイルで import を前提にしていないため、書体・`REPORT_DATA_DIR`・盤面図(`Board`)の考え方だけを再利用し、コードはこのファイルの中に新しく書いた)。

- 入力: `whatif_report_data.json`(`scripts/playtest/whatifReport.ts` の出力)と `sfens.json`(`REPORT_DATA_DIR`。既存の `reportData.ts --out-sfens` の出力をそのまま使う)
- 使い方: `REPORT_DATA_DIR=<sfens.json のあるフォルダ> python3 -X utf8 render_whatif.py <whatif_report_data.json> <出力 PDF>`
- 依存はこの README の「依存」節と同じ(`reportlab`・`pymupdf`)。新しい依存は足していない
- 数の照合・禁止語(`BANNED`)の確かめは、この道具の中で完結する(`_mid.py` の `allowed_numbers`・`BANNED` とは別の実装だが、同じ考え方)
- 詳しい設計は `scripts/playtest/README.md` の「重要な局面の分かれ道を見せる」節を参照

## 本編(`render_front.py`。STEP TIME 作業 2・作業 3、docs/STEP_TIME_PLAN_2026-09-22.md §6.4・§6.7)

`render_front.py` も、凍結した 6 本とは**別の、単体の新規ファイル**である(`render_whatif.py` と同じ位置づけ)。
`build.sh` では作らない。今の本編(凍結した第 6 版、局ごとのページ。`render_main.py`)は**触らず、資料 1 になる**
(2 回目以降の主役はこちらの本編)。

- 入力: `patient_report_data.json` の `findings`・`previous`・`time`・`overview`・`summary` だけ(`sfens.json`・`prose.json`
  は読まない。`REPORT_DATA_DIR` は渡さない)。第 3 引数に `finding_texts.json`(STEP TIME 作業 3。任意)を渡せる
- 発見の判定(何を出すか・前回との比較)は `lib/reportData.ts` の `buildFindings`・`buildPrevious`(TypeScript・試験できる側)が
  すでに決めている。この道具は結果(`shown`・`text`・`numbers`)を PDF に描くだけ(判定はしない)。「考えられること」
  「次の 20 局で見分けがつくこと」「試せること」「§5.3 の 3 通りの文」も、`lib/findingTexts.ts`(TypeScript)が正本
  (docs §5.2・§5.3 の写し。試験 `lib/findingTexts.test.ts` が一致を確かめる)で、この道具は `finding_texts.json`
  (`reportData.ts` の CLI が生成)を読んで描くだけ(新しい文言はここで作らない)
- 使い方: `python3 -X utf8 render_front.py <patient_report_data.json> <出力 PDF> [<finding_texts.json>]`
- ページ: 1 今回の n 局で分かったこと(`findings` のうち `shown` のものを、発見の種類の固定順で並べる。
  `finding_texts.json` があれば、発見ごとに数の文の下へ「考えられること」(頭の 1 文 + (a)(b)(c))・「次の 20 局で
  見分けがつくこと」・「試せること」の 3 段を足す。`phase` は数の文だけ ― §5.2 T5「考えられること・試せることは
  付けない」) / 2 前回のことは、今回も起きたか(`previous` が無ければ「初回のため、前回との比較はありません」の
  1 文。`finding_texts.json` があれば、種類ごとの 3 通りの文の下に §5.3 の固定文を足す) / 3 次の n 局で見るもの
  (今回、数として出した名前と今回の値の表。**予測や助言は書かない**) / 4 数え方(固定文。`finding_texts.json` が
  あれば評価の揺れの注記を足す)
- **`finding_texts.json` を渡さなければ、今の形(数の文だけ)のまま動く**(STEP TIME 作業 2 の挙動と変わらない)
- 発見の種類ごとの題(`TITLE_JP`)は、計画(§6.4)に文言の指定が無いため、この道具の実装で最小限の事実だけの題を決めた
  (実装担当の判断。判断・助言の言葉は含まない。`finding_texts.json` の `title` 欄は `TITLE_JP` と同じ文字列の写しで、
  見出しとしては使っていない)
- 機械の検査: 禁止語(`BANNED`。悪手・弱点・癖・型・傾向・原因・ミス・見落とし・改善・練習・必ず・明らか・あなた・ご自身・
  いつも・がち・クセ・パターンの 18 語)0(固定文も対象)、文に出る数がすべて `findings[].numbers`・`time`・`overview`・
  `previous` の値にあること(`GLOBAL_ALLOWED_NUMBERS` は `TIME_VALUES`・`STANDING_BOUNDS` と同じ値を手で合わせたもの。
  STEP TIME 作業 3 で固定文の数(30・40)を追加。ずれたら emit() が「データに無い数」として rc=1 で止まる)、
  ページ数が 4〜6(3 段を足すと 1 ページ目が 2 ページ以上になり得るため、STEP TIME 作業 2 の「4 ページ固定」から
  緩めた。4 節・節ごとに改ページは変えていない。pymupdf が使える環境でだけ確認。使えない環境では確認をスキップし、
  その旨を標準出力に書く)
- 依存はこの README の「依存」節と同じ(`reportlab`・`pymupdf`)。新しい依存は足していない

## 既知の欠落(2026-09-21 独立監査 REVISE で明記)

別冊(`render_appendix.py`)は、`audit_metrics.json` の `candidate.reps` の欄(`side`・`transitionJp`・`capUsJp` ほか)と
`engine`・`sideLabel`・`trajectories` などが `reportData.ts` で未実装のため、`reportData.ts` の出力からは作れず `KeyError` で止まる。
凍結した `audit_metrics.json`(`scripts/playtest/out/report-template-v6/audit_metrics.json`)からは作れる。

## 既知の限界(STEP FILL 作業 Y、独立監査 REVISE 2026-09-22 で明記)

- **この `report-pdf/` の python の道具は vitest の対象外(このリポジトリに python の自動試験の基盤が無い)。**
  この STEP での守りは「第 6 版 20 局の入力で、直しの前後で本文が変わらない」という実測だけである。
  **該当が 0 件の分岐は、この確かめをすり抜ける** ― 独立監査が変異(新しい分岐の順序を入れ替える)で実証済み:
  第 6 版の 20 局には新しい分岐(投了で終わった将棋)に当てはまる局が 0 局のため、分岐の中身をどう間違えても
  20 局の本文は 1 文字も変わらなかった。**`_head.py`・`_mid.py`・`_app.py` に新しい分岐・新しい数を足す STEP では、
  第 6 版 20 局の不変を見るだけでなく、その分岐に該当する局が 1 件以上出る入力(合成データでよい)でも本文を確かめること。**
- 「次の {局数} 局で確かめます」(`_mid.py`・`_app.py` に計 2 か所)は、次の回の局数を今回と同じ数(`summary.games`)で
  書く(次の回の局数を予測しているのではなく、今回と同じ規模を仮に置いているだけ)。
- **`render_whatif.py`(STEP WHATIF 作業 2)も同じ理由で vitest の対象外。** 守りは、合成データ(先手の負け・後手の勝ち・
  代表の場面が無い局の 3 局程度)での rc=0・禁止語 0・数の照合の実行時確認と、実データ(24 局)での実行時確認
  (1 ページ目の集計の件数が事前に測った値と一致すること)。「代表の場面が無い局」のような該当 0 件の分岐は、
  実データだけでは確かめられないため、合成データ側に必ず 1 件以上含める。
- **`render_front.py`(STEP TIME 作業 2・作業 3)も同じ理由で vitest の対象外。** 発見の判定そのもの(何を出すか)・
  固定文そのもの(§5.2・§5.3)は `lib/reportData.ts`・`lib/findingTexts.ts`(どちらも vitest の対象)がすでに
  決めているため、この道具の責務は「描くだけ」に絞ってある。守りは、合成データ(5 種類の発見がすべて `shown: true`
  の組・すべて `shown: false`(none だけ)の組・`previous` の 3 通り(前回出た/今回も出た・今回は出ない・前回出ない/
  今回出た)・`time.available: false` の組)での rc=0・禁止語 0・数の照合・ページ数 4〜6 の実行時確認と、実データ
  (14・10・20 局の 3 組)での実行時確認(§4 の校正の表と一致すること)。作業 3 では、`finding_texts.json` を渡した
  場合(3 段・§5.3 の固定文が入る)と渡さない場合(今の形のまま)の両方を実データで確認し、第 6 版 20 局の
  `main.pdf` 本文の完全一致(既存の確かめ)も変わっていないことを確かめた。
