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

## 本編(`render_front.py`。STEP TIME 作業 2・作業 3・作業 4・作業 4b、docs/STEP_TIME_PLAN_2026-09-22.md §6.4・§6.7・§6.10・§6.12)

`render_front.py` も、凍結した 6 本とは**別の、単体の新規ファイル**である(`render_whatif.py` と同じ位置づけ)。
`build.sh` では作らない。今の本編(凍結した第 6 版、局ごとのページ。`render_main.py`)は**触らず、資料 1 になる**
(2 回目以降の主役はこちらの本編)。

- 入力: `patient_report_data.json` の `findings`・`previous`・`time`・`overview`・`summary` だけ(`sfens.json`・`prose.json`
  は読まない。`REPORT_DATA_DIR` は渡さない)。第 3 引数に `finding_texts.json`(STEP TIME 作業 3。任意)を渡せる
- 発見の判定(何を出すか・前回との比較・「ひとことで」の選び方)は `lib/reportData.ts` の `buildFindings`・`buildPrevious`
  (TypeScript・試験できる側)がすでに決めている。この道具は結果(`shown`・`text`・`oneLine`・`numbers`)を PDF に
  描くだけ(判定はしない)。「考えられること」「次の 20 局で見分けがつくこと」「試せること」「§5.3 の 3 通りの文」
  「読み方」「試せることのまとめの見出し・末尾の文」「言葉の意味」も、`lib/findingTexts.ts`(TypeScript)が正本
  (docs §5.2・§5.3・§5.5 の写し。試験 `lib/findingTexts.test.ts` が一致を確かめる)で、この道具は `finding_texts.json`
  (`reportData.ts` の CLI が生成)を読んで描くだけ(新しい文言はここで作らない)
- 使い方: `python3 -X utf8 render_front.py <patient_report_data.json> <出力 PDF> [<finding_texts.json>]`
- ページ: 1 今回の n 局で分かったこと(冒頭に読み方の枠(`finding_texts.json` があるときだけ)。`findings` のうち
  `shown` のものを、発見の種類の固定順で並べる。発見ごとに 題 → **ひとことで**(`findings[].oneLine`。太字、
  数の文の上)→ 数の文 → `finding_texts.json` があれば「考えられること」(頭の 1 文 + (a)(b)(c))・「次の 20 局で
  見分けがつくこと」・「試せること」の 3 段(`phase` は数の文だけ ― §5.2 T5「考えられること・試せることは
  付けない」)。末尾に「次の 20 局までに試せること(まとめ)」(`finding_texts.json` があるときだけ。shown の
  発見の `tryable` を出た順に番号で再掲 + 末尾の 1 文。`tryable` が 1 つも無ければ何も出さない ― 実装担当の判断)。
  STEP TIME 作業 4b(§6.12): `phase` は数の文の下に `finding_texts.json` の `phaseNote`(考えられること・試せる
  ことを付けない理由の 1 文)を足す) /
  2 前回のことは、今回も起きたか(`previous` が無ければ「初回のため、前回との比較はありません」の
  1 文。`finding_texts.json` があれば、種類ごとの 3 通りの文の下に §5.3 の固定文を足す) / 3 次の n 局で見るもの
  (今回、数として出した名前と今回の値の表。表の名は「(崩れた手 / 手)」の形(§5.5「言い換え」)。**予測や助言は
  書かない**) / 4 数え方(頭に「言葉の意味」(`finding_texts.json` の `glossary`、5 項目 ― STEP TIME 作業 4b で
  「秒読み」を追加。あるときだけ)。固定文。`finding_texts.json` があれば評価の揺れの注記も足す)
- **`finding_texts.json` を渡さなければ、今の形(読み方の枠・ひとことで以外の 3 段・まとめ・言葉の意味・§5.3 の
  固定文・評価の揺れの注記が付かない形)のまま動く**。`findings[].oneLine`(数の文の上の太字)は `finding_texts.json`
  の有無に関わらずつねに描く(`patient_report_data.json` だけで決まる値のため)
- 発見の種類ごとの題(`TITLE_JP`)は、計画(§6.4)に文言の指定が無いため、この道具の実装で最小限の事実だけの題を決めた
  (実装担当の判断。判断・助言の言葉は含まない。`finding_texts.json` の `title` 欄は `TITLE_JP` と同じ文字列の写しで、
  見出しとしては使っていない)
- 機械の検査: 禁止語(`BANNED`。悪手・弱点・癖・型・傾向・原因・ミス・見落とし・改善・練習・必ず・明らか・あなた・ご自身・
  いつも・がち・クセ・パターンの 18 語)0(固定文も対象)、**お客さん向けの文に「組」が残っていれば rc=1**(STEP TIME
  作業 4。§5.5「言い換え」。`emit()` に組み込み、テンプレの文・`finding_texts.json` 経由の文の両方が対象)、
  文に出る数がすべて `findings[].numbers`・`time`・`overview`・`previous` の値にあること(`GLOBAL_ALLOWED_NUMBERS` は
  `TIME_VALUES`・`STANDING_BOUNDS` と同じ値を手で合わせたもの。STEP TIME 作業 3 で固定文の数(30・40)、作業 4 で
  「言葉の意味」の `600`(`lib/whatif.ts` の `WHATIF_VALUES.minLossCp` と同じ値)を追加。ずれたら emit() が
  「データに無い数」として rc=1 で止まる)、ページ数が 4〜6(3 段・読み方・まとめ・言葉の意味を足すと 1・4 ページ目が
  2 ページ以上になり得るため、STEP TIME 作業 2 の「4 ページ固定」から緩めた。4 節・節ごとに改ページは変えていない。
  pymupdf が使える環境でだけ確認。使えない環境では確認をスキップし、その旨を標準出力に書く)。**STEP TIME 作業 4b
  (§6.12)**: 「次の 20 局までに試せること(まとめ)」の各項目に `(a)`/`(b)`/`(c)` の裸の参照、または「同じ物差し」
  が残っていれば rc=1(`check_summary_item()`。まとめは発見の題を伴わずに再掲されるため、裸の参照は読者に伝わらない)
- 依存はこの README の「依存」節と同じ(`reportlab`・`pymupdf`)。新しい依存は足していない

## B(「どうしたら」の冊子)の検査と PDF(`check_answer.py`・`render_answer.py`。STEP ANSWER)

docs/STEP_ANSWER_PLAN_2026-09-23.md §2.1・§2.2 の道具。B(LLM が書いた「どうしたら」の markdown)を検査し、
通った文だけを PDF にする。CLAUDE.md ルール 5 の拡張((1) 数・手・読み筋の機械照合、(2) 行動は承認済みの表から、
(3) 断定しない)を機械で守らせる仕組み。**生成(B を書くこと)はしない ― 検査するだけ。**

### `check_answer.py`

```
python3 -X utf8 check_answer.py <B.md>
  [--patient <patient_report_data.json> --time-limit-sec <秒>]…(組ごとに 1 対。直後に --time-limit-sec を置く。
    180 秒 = 3 分の組、600 秒 = 10 分の組、他の秒数はタグ無し。同じタグが複数あれば分子・分母を別々に合算する
    ― 司令塔の指示 2026-09-23 REVISE 1。前回 20 局 + 今回 14 局 = 3 分の組、のように)
  [--whatif-data <whatif_report_data.json>]…(複数可。検査 1 の数の材料)
  [--whatif-v2-dir <whatif-v2 jsonl のフォルダ>]…(複数可。組をまたいで合算。M4「側の一致」の材料)
  [--read-dir <read.ts の jsonl のフォルダ>]…(複数可。組をまたいで合算。summary 行を合算する)
  [--type-summary <summary.json>]…(複数可。検査 1 の数の材料)
  [--whatif-pdf <whatif.pdf>]…(複数可。fitz で印字を読み、指し手の答え合わせに使う)
  [--direct <json>]…(複数可。付録 3(ANSWER-DIRECT)の `direct_answers.json`(`directAnswers.ts` の出力)・
    `final_positions.json`(`finalPositions.ts` の出力)のどちらも受け付ける ― 中身の `kind`
    (`"direct_answers"`/`"final_positions"`)で見分ける。検査 1 の材料に足す ― 単独の数(渡した JSON の
    再帰走査)と、下の「登録済みの組」)
  [--time-cause <json>]…(複数可。付録 4(STEP TIME-CAUSE)の `time_cause.json`(`scripts/playtest/timeCause.ts`
    の出力、`lib/timeCause.ts` の `TimeCauseFile`)。中身の `kind`(`"time_cause"`)で見分ける ― `--direct` と
    同じ流儀。検査 1 の材料に足す ― 単独の数(渡した JSON の再帰走査)と、下の「登録済みの組」)
  [--time-search <json>]…(複数可。付録 4 の探索(STEP TIME-CAUSE-2・STEP TIME-CAUSE-3)の
    `time_cause_search.json`(`scripts/playtest/timeSearch.ts` の出力、`lib/timeSearch.ts` の `SearchResult`)。
    中身の `kind`(`"time_cause_search"`)で見分ける ― `--direct`・`--time-cause` と同じ流儀。検査 1 の材料に
    足す ― 単独の数(渡した JSON の再帰走査)と、下の「登録済みの組」)
  --menu <answer_menu.json>(`scripts/playtest/answerMenu.ts` の出力)
```

rc=0 なら通過(「通過(落ちた文なし)」を標準出力へ)。rc=1 なら、落ちた文と理由の一覧を標準エラーへ(1 行 1 件、
`<行番号>: <理由>: <文の先頭 100 字>`)。「書いた側の記録(顧客には見せない)」の見出しから末尾までは、検査の対象
から外す(顧客向けの文ではないため)。

**検査(§2.1 のとおり。すべて機械)**:
1. **数の照合**: 単位つきの数は、下の「登録済みの組」または許す集合(渡した JSON の値の再帰的な走査 + 組ごとに
   合算した数 + 登録済みの組から計算した四捨五入の整数 %)に無ければ落とす。単位の無い小さな数(9 以下)は対象外
   (実装担当の判断: 「小さな数」を 9 以下で近似 ― §2.1 は「2 つ」「3 段」を例に挙げるだけで、しきい値までは
   決めていない)。日付(YYYY-MM-DD)は数の主張として扱わない(見出し・作成日の表記のため。実装担当の判断)。
   「〜倍」「〜割」は常に落とす。**「a / b」「n のうち m」「n 局のうち m 局」の形は、下の「登録済みの組」の
   どちらかの並びに一致しなければ落とす**(単独の数がどこかにあるだけでは通さない)。
2. **手の答え合わせ**: `▲`/`△` で始まる指し手の表記(`report-pdf/render_whatif.py` の `move_kanji` と同じ形)が、
   `--whatif-pdf` の印字(空白を取り除いた連結テキスト)に無ければ落とす。「第 1 候補は」の形は、同じ段落
   (空行区切り)に「n 局目 m 手目」の形が無ければ落とす。
3. **禁止語と断定**: 18 語(悪手・弱点・癖・型・傾向・原因・ミス・見落とし・改善・練習・必ず・明らか・あなた・
   ご自身・いつも・がち・クセ・パターン)+「すべき」「した方がよい」「すれば直る」「間違いなく」「危ない」
   「確実」「絶対」「安い」(司令塔の指示 2026-09-23 REVISE 5・2026-09-24 の再監査 1)。
4. **行動のメニュー**: `<!-- menu: Mx -->` の行は、id が `answer_menu.json` にあり、`menuConditionHoldsOf` が
   その材料で成り立たなければ落とす。**印の外で、行動・優先順位の表現(「してみては」「を目安に」「を選ぶ」
   「選ぶなら」「1つだけ」「先に」「で指す」「を混ぜる」「候補に入れ」の 9 語)を含む行は落とす**(司令塔の指示
   2026-09-23 REVISE 4・2026-09-24 の再監査 3。「を選ぶ」は実装の監査 REVISE で欠落が見つかり追加: 印の外の
   「いちばん評価の高い手を選ぶと良いでしょう」が通っていた)。例外は `<!-- priority: Mx -->` の印がある行(その id が成り立っていれば除外)。
   太字だけの見出し行(例: 「**こうしてみては**」)は対象外(実装担当の判断)。**ANSWER-MENU2(2026-09-24、
   docs §8)**: 条件・minN に加えて、`answer_menu.json` の該当項目に `verifyGate`(答え合わせの下限。§8.1)が
   あれば、それも満たさなければ落とす(理由「答え合わせの数が下限に届かない」。M1 だけが持つ:
   `midOver.overAndTimeUpLoss / midOver.over ≥ 1/2`)。`foundInSameData: true` の項目(M9 だけ)は、印の行に
   「今回の対局から見つけた読みです」の句が無ければ落とす(理由「今回の対局から見つけた読みの句が無い」)。
5. **数が足りなければ言わない**: `<!-- menu: Mx -->`(条件が成り立った)行は、`answerMenuDenominatorOf` が返す
   分母が `answer_menu.json` の `minN` 未満なら落とす。
6. **戦法・陣形の名前**: `data/shapes`・`data/openings`・`data/intents` の `review_status` が `human_reviewed` または
   `expert_verified`(「レビュー済み」。`reviewed` という値は無い ― 司令塔の指示 2026-09-23 REVISE 7)の `name` に
   無い、「〜戦法」「〜囲い」「〜飛車」「〜銀」の語(指し手の表記は先に除いてから探す)は、「〜のような形」の
   後ろに付いていなければ落とす。

**登録済みの組(検査 1 の「a / b」「n のうち m」。両方向を許す)**: `timeUpLosses` の `n`/`m`、`aheadGames`/
`aheadLossGames`、`bySpent` の各段の `n`/`collapsed`(組ごとの合算も)、`bySpentTotal` の `n`/`collapsed`、
`afterLongThink`(`quickAfterLongThink`・`afterLongThinkAny`)の `n`/`collapsed`、READ 合算の
`forkPositionsRead`/(`forkPositionsRead` − `firstVisibleNodesNoneCount`)、`tagCrossTable.sacrifice` の行合計/対角
(B v3(2026-09-24)の実例「57 のうち 17」で確認)、`opponentReplyMatchesPv` の `matched`/`measured`、M4 の側の一致
2 分数(`attack`/`defense` それぞれの `n`/`collapsed`)、**ANSWER-M1(2026-09-24、§7.2)**: `midOver` の
`over`/`games`、`overAndTimeUpLoss`/`over`(patient ごと・組ごとの合算の両方)、**ANSWER-MENU2(2026-09-24、
§8.2)**: 「時間負けのうち中央値超え(`timeUpLossMidSecs` のうち `otherGamesMidMedian` を超えた数)/ 時間負け
(`timeUpLosses.n`)」(組ごとの合算)、**ANSWER-DIRECT(2026-09-24、§9.2。`--direct` で渡した JSON から)**:
(i) 浅い読みで見えた分かれ道の総数(`counts.totalCount`)/ 分かれ道の総数(`counts.totalForkCount`)(例
30 / 152)、(ii) 第 1 候補の印(`counts.top1TagCounts` の取る・打つ・王手・捨て駒・引く・玉の動き・不成)
ごとの n / 総数(`counts.totalCount`。例「打つ」16 / 30)、(iii) 実戦の印(`counts.actualTagCounts`)ごとの
n / 総数、(iv) 第 1 候補の側(`counts.top1SideCounts` の攻め・守り・両方・なし)ごとの n / 総数、(v) 組
(`answers[].group`。「3 分」「10 分」等)ごとの局面数 / 総数(例「3 分」21 / 30)。**(vi) 組ごとの「局数」
(`counts.gamesCount` にあたる、組ごとに絞った局数)は登録しない**(`--patient` の `games`(対局の局数)と
混ざるため)。`--direct` を複数渡した場合は、これらの分子・分母をそれぞれ合算する。**付録 4(STEP TIME-CAUSE、
`--time-cause` で渡した `time_cause.json` から)**: 同じ `group`(「3 分」「10 分」等)の `groups[]` を、
ファイルをまたいでも(`--time-cause` は複数可)分子・分母を合算してまとめたうえで、(i) C7 = 長考のうち
分かれ道に当たった数 / 長考の総数(`timeUpLoss.forkFraction` + `other.forkFraction` の合算。実例「3 分」の組で
9 / 35)、(ii) C8 = 側が逆だった数 / 長考かつ分かれ道の総数(`timeUpLoss.oppositeSideFraction` +
`other.oppositeSideFraction` の合算。実例「3 分」の組で 1 / 9)、(iii) C9 の 2×2(`rookMarkBreakdown`。
本人/相手の飛車が初期の筋に居るかの 4 通り)の各局数 / 組の局数、(iv) 時間負けの局数(`timeUpLoss.games`)/
組の局数(`games`)(`--patient` の `timeUpLosses` と同じ値になるはずだが、別材料として独立に登録する)を
登録する。**(v) 局ごとの「時期ごとの長考の回数(`longThinkCountByPhase`)/ 長考の総数(`longThinkTotal`)」は
登録しない**(小さい数の偶然一致が増えるため)。**付録 4 の探索(STEP TIME-CAUSE-2、`--time-search` で渡した
`time_cause_search.json` から)**: (i) `reproduced[]`・`notReproduced[]` の各条件について discover.longThink /
discover.n、validate.longThink / validate.n(実例: ある条件で 7 / 75〈発見用〉と 14 / 70〈検証用〉)、
(ii) `depths[]` の深さごとの adopted / tried・reproduced / adopted・reproduced / tried(実データで深さ 3 は
508 / 6209 など)、(iii) 発見用・検証用それぞれの「長考の数 / 手の数」(長考の数は JSON に無いため
`round(moves × longThinkRate)` で作り、`moves × longThinkRate` 自身と 1e-6 以内で一致するときだけ登録する
〈実データで 33 / 744、35 / 604〉)を登録する。**STEP TIME-CAUSE-3(2026-09-25、§9.1)で足した崩れ
(collapse)の数**: (iv) `reproduced[]`・`notReproduced[]`(長考の探索)と `collapseSearch.reproduced[]`・
`collapseSearch.notReproduced[]`(崩れの探索)の各条件について discover.collapsed / discover.collapseCounted、
validate.collapsed / validate.collapseCounted、(v) 全体の崩れ discover.collapsed / discover.collapseCounted、
validate.collapsed / validate.collapseCounted、(vi) `factors[]`(共通因子)の各部品の `single` の分数
(discover.longThink / discover.n・validate.longThink / validate.n・discover.collapsed / discover.collapseCounted・
validate.collapsed / validate.collapseCounted の 4 つ)、(vii) `factors[]` の各部品の
`inReproduced.depth1`/`depth2`/`depth3` と、対応する `depths[0]`/`depths[1]`/`depths[2]` の `reproduced`
(長考の探索の再現の数)を登録する。**局ごとの時期別の分数のような小さい数は登録しない**(§8.5 と同じ判断)。
`--time-search` を複数渡した場合は、ファイルごと(1 回の探索の実行ごと)に別々の集計として登録する
(`--time-cause` の `group` のような合算先の鍵が無いため)。**CAUSE-SEARCH-1(2026-09-25、§11.1)で足した
`searches.*`(アウトカムごとの探索。JSON に `searches` が無い〈一般化の前に作った古い形式の〉ファイルは
スキップする)**: `searches` に入っている各アウトカム(`longThink`・`collapse`・`decisionGap`。`--outcomes`
で絞った場合は渡された分だけ)について、(viii) `searches.<outcome>.reproduced[]`・`notReproduced[]` の各条件の
分数(`longThink` は discover.longThink / discover.n・validate.longThink / validate.n、`collapse` は
discover.collapsed / discover.collapseCounted・validate.collapsed / validate.collapseCounted、`decisionGap` は
discover.matched / discover.n・validate.matched / validate.n)、(ix) `searches.<outcome>.depths[]` の深さごとの
adopted / tried・reproduced / adopted、(x) `searches.decisionGap` があるときだけ、`factors[]` の各部品の
`singleDecisionGap`(`byOutcome.decisionGap` の判定に使った部品単独の分数)の discover.matched / discover.n・
validate.matched / validate.n を登録する(`longThink`・`collapse` の単独の分数は既存の (vi)〈`factors[].single`〉
で登録済みのため重複させない)。

**既知の限界**: 検査 1 の単独の数(分数でない 1 つの数)は、渡された JSON のどこかに同じ値があれば通す(再帰的な
数値走査。`render_front.py` の `allowed_numbers_of` のようなフィールドごとの明示的な一覧ではない)。値の意味
(どのフィールド由来か)までは確認しないため、たとえば「16 秒・79 秒」のような、正規の集計と無関係な値が
偶然どこかの JSON 値と一致すれば通ってしまう(実測: B v2 の校正で 1 件確認。落とせていない。強い検証が要るなら
フィールドごとの明示的な許可リストへの置き換えが要る ― 測っていない・計画にない判断)。**付録 4 の探索の登録済みの
組も同じ限界を持つ(実測): `reproduced[]`・`notReproduced[]` を合わせて数百件の条件を登録するため、無関係な
条件どうしで同じ「a / b」が偶然一致することがある。立浪さんの実データで、上の実例の分子・分母(7 / 75)の分母
だけを 76 に変えた「7 / 76」を試したところ、別の(意味の異なる)条件が偶然 discover.n=76・discover.longThink=7
を持つため、これも登録済みの組として通ってしまった(落とせていない)。

### `render_answer.py`

```
python3 -X utf8 render_answer.py <B.md> <出力 PDF>  [check_answer.py と同じ引数…]
```

先に `check_answer.check_answer()` を呼び、落ちた文があれば描かずに理由を標準エラーへ出して exit 1。通れば、
markdown を見出し(`#`・`##`・`###`)・箇条書き(`-`・`1.`)・表(`|...|`)・太字(`**...**`)の A4 縦 PDF にする
(書体の埋め込みの確認は `check_fonts_embedded.py` の `unembedded_fonts` をそのまま呼ぶ)。`<!-- menu: … -->`・
`<!-- priority: … -->` の印は描かない。ページ数の上限 8(超えたら exit 1)。検査・markdown の中身(生成ロジック)は
変えていない ― 変わったのは組版(見た目)だけ。

**組版(発注者「今のレイアウトじゃ読みづらい」、2026-09-24 に読みやすく作り直した)**:

- 本文 11pt・行送り 1.65 倍・段落間 0.5 行前後、左右の余白 22mm(1 行 40 字台)。`#` は表紙代わりに大きく
  (直後の 1 行が見出し等でなければ「読み方の説明」として薄い色で載せる)、`##` の前後に空きと下線、`###` は太字。
- **太字の実装**: この環境には Bold の欠けた TrueType しか無い(`render_front.py` 等と同じ制約)。そこで、
  同じ物理フォントを 2 つの名前(`JPEmbedded`・`JPEmbeddedBold`)で登録し、`<b>` が後者に解決されるようにしたうえで、
  `Canvas.beginText()` を差し替えた自前の `PDFTextObject`(`_FauxBoldTextObject`)で「フォント名が `JPEmbeddedBold`
  になった瞬間だけ PDF の文字描画モードを 2(塗り+縁取り)にして細い線幅を乗せる」ことで太らせる(=書体そのもの
  ではなく描画の太さで太くする)。reportlab の内部 API(`_setFont`/`setFont`/`setTextRenderMode`)に依存するため、
  reportlab のバージョンが大きく変わると挙動が変わりうる(既知の限界)。
- 「こうしてみては」の番号つき項目(`N. **行動の文。** 根拠: …` の形)は、行動の文(太字・1 段大きい)と
  根拠(`根拠:` 以降・1 段小さい薄い色)の 2 つの段落に分けて描く。
- 単位つきの数(局・回・手・秒・%・ポイント が続く)と、符号つきの評価値(`+2407` のような形)は太字にして拾える
  ようにする(数そのものは変えない・増やさない。印字は markdown の文字列そのまま)。
- 箇条書きは reportlab の `bulletText`(•・番号)によるぶら下げインデント。表は `GRID` の罫線・ヘッダ行だけ薄い塗り・
  列幅は内容の見かけの文字数から比例配分(極端な差を抑えるため 0.6 乗で緩めている)。
- ページ下に「ページ n / N」、2 ページ目以降は上に小さく題を再掲(reportlab の定番手順どおり、`Canvas.save()` で
  総ページ数が分かってから描き直す `_ReportCanvas`)。

**この python の道具も vitest の対象外**(`report-pdf/` の他の道具と同じ理由)。守りは、実データ(立浪さんの
14 局・20 局・10 局)での実行時確認(B v2・B v3 の 2 本。組版の作り直しでは、さらに送付版・v4 の 2 本を
実データで PNG 確認した)と、変異 5 本(数を 1 つ変える・「すべき」を足す・付録 2 に無い手を足す・
`<!-- menu: -->` を消す・条件を満たさない id へ材料を絞る)。

## 付録 3「直接の答え」(`render_direct.py`。STEP ANSWER 追加作業 ANSWER-DIRECT、docs/STEP_ANSWER_PLAN_2026-09-23.md §9)

`render_direct.py` も、凍結した 6 本とは**別の、単体の新規ファイル**である(`render_whatif.py`・`render_front.py`
と同じ位置づけ。`build.sh` では作らない)。CLAUDE.md ルール 5 の拡張 (4)(2026-09-23 の人間の決定)― エンジンで
答え合わせした指し手を局面つきで示してよい ― の実物。**道具が局面と手を選ぶ**(LLM は使わない)。

- 入力: `direct_answers.json`(`scripts/playtest/directAnswers.ts` の出力)・`final_positions.json`
  (`scripts/playtest/finalPositions.ts` の出力)・`sfens.json`(`REPORT_DATA_DIR`。既存の `reportData.ts
  --out-sfens` の出力をそのまま使う)
- 使い方: `REPORT_DATA_DIR=<sfens.json のあるフォルダ>[,<フォルダ>…] python3 -X utf8 render_direct.py
  <direct_answers.json> <final_positions.json> <出力 PDF>`(`REPORT_DATA_DIR` はカンマ区切りで複数渡せる ―
  `direct_answers.json`・`final_positions.json` は組をまたいで作れるため、対応する `sfens.json` も複数の組に
  またがることがある〈実装担当の判断〉。同じ kifuId が複数の `sfens.json` に出た場合は最初に読んだものを使う)
- ページ: 1 ページ目(表〈組・局・手数・実戦の手・第 1 候補・第 1 候補の性質・実戦との差〉と印の数) / 「盤上は
  こう勝てた」(`final_positions.json` の局ごとに 1 ブロック。終局の局面 + 第 1 候補の読み筋。詰みなら
  「n 手で詰み」、詰みでなければ評価だけを中立に書く ― 判断的な「勝ちに届く」のような閾値は置いていない
  〈実装担当の判断。docs §9.1 の例文はこの版では使っていない〉) / 「浅い読みで見えた分かれ道」
  (`direct_answers.json` の `answers` の順〈実戦との差の大きい順〉に、局面ごとのブロック)
- **組・実戦との差(司令塔の仕様追記 2 点、2026-09-24)**: 「局」の番号が組(3 分の組・10 分の組)をまたいで
  重なる(1〜10 が両方にある)ため、表の先頭に「組」の列(`answers[].group`・`entries[].group`。「3 分」
  「10 分」等)を足し、盤面のページの見出し(「n 局目 m 手目」「n 局目 ・ m 手で時間切れ」)にも
  「{group} の n 局目 …」の形で組を前に付けた。「評価の差」の列は `topGapCp`(第 1 候補と第 2 候補の差)から、
  実戦の手が第 1 候補からどれだけ下がったか(`answers[].actualGapCp`。whatif-v2 の `loss`)に替え、列名も
  「実戦との差」にした。実戦の手が候補 5 つに無いとき(`loss.isLowerBound`)は下限の値であり実戦の手の正確な
  差ではないため「—」(`lib/directAnswers.ts` の `actualGapCpOf`)。`topGapCp` は `direct_answers.json` には
  残るが表には出さない。並び順も `actualGapCp` の大きい順(null は最後)に変えた。数の照合の固定の語彙
  (`GLOBAL_ALLOWED_NUMBERS`)に、組のラベルの数字(3 分・10 分の「10」)を足した。
- **盤面図・手の表記は `render_whatif.py` と同じ考え方**(`REPORT_DATA_DIR`・書体・`parse_sfen`・`move_kanji`・
  `mark` などのコードをこのファイルの中に持つ ― `render_whatif.py` も import せず同じ考え方をコードとして
  持つ書き方をしているため、同じ流儀)。**mirrored(本人が後手)の局は、`sfens.json` の `side`(`"gote"` なら
  mirrored。二重に判定ロジックを作らない)を見て、盤面は本人が指した実際の向き(`sfens.json`)、候補・実戦の
  手は `rotate_usi` で本人が指した向きへ戻してから当てる**(`render_whatif.py` と同じ考え方)
- **矢印・丸(このファイルの新規部分)**: `render_whatif.py` の `Board` は升の色づけだけで矢印は描いていなかった
  ため、`render_direct.py` の `Board` は実戦の手(茶の実線)・第 1 候補(青緑の破線)の矢印(線 + 三角の矢じるし)
  を描く機能を新しく足した。打つ手(元の升が無い)は行き先に丸(実線/破線は実戦・候補と同じ塗り分け)
- `check_answer.py` の `--whatif-pdf` にこの PDF のパスも渡せば、検査 2(手の答え合わせ)がこの PDF の印字でも
  通る(`move_kanji`・`mark` のコードは `render_whatif.py` と文字どおり同じ)。配線(`--direct` 等)は司令塔が
  別に行う(触らないもの)
- **第 1 候補の性質・side の出どころ**: `directAnswers.ts` が作る通り、`top1Tags`/`actualTags` は read.ts の印
  (取る/打つ/王手/捨て駒/引く 他)、`top1Side`/`actualSide` は whatif-v2 の側(攻め/守り/両方/なし)
- 数の照合・禁止語・書体の埋め込みの確認は `render_front.py`・`render_whatif.py` と同じ考え方
  (`emit`/`BANNED`/`check_fonts_embedded.py`)
- **既知の限界(実装担当が実データで確認)**: 持ち駒の種類が多い局面(4 種類以上)で、「本人の持ち駒」/
  「相手の持ち駒」のラベルと駒の数の表記が重なることがある。`render_whatif.py` の `Board`(升の色づけ・持ち駒の
  帯)をそのまま流用したコードで起きるため、この付録固有の新しい不具合ではなく、既存の描き方が抱える限界と
  見られる(今回は直さない ― 人間・司令塔の判断)
- 依存はこの README の「依存」節と同じ(`reportlab`・`pymupdf`)。新しい依存は足していない
- この python の道具も vitest の対象外(`report-pdf/` の他の道具と同じ理由)。守りは、合成データ(短い実戦の手数
  で分かれ道 3 つ・詰みの終局局面 1 つを含む)での rc=0・書体埋め込み確認と、実データ(`tatsunami3`・
  `tatsunami-long`・`tatsunami20` の 3 組)での実行時確認(rc=0・ページ数・fitz で PNG化した目視確認。mirrored
  〈本人が後手〉の局・mirrored でない局の両方を含む)

## 付録 4「時間の使い方」(`render_time_cause.py`。STEP TIME-CAUSE、docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §2・§3)

`render_direct.py`・`render_front.py` と同じ位置づけの**単体の新規ファイル**(`build.sh` では作らない)。
`scripts/playtest/timeCause.ts` が作る `time_cause.json` を描くだけで、判定・集計は TypeScript 側
(`lib/timeCause.ts`)がすでに済ませている。

- 入力: `time_cause.json` のみ(`REPORT_DATA_DIR`・`sfens.json` は使わない ― 盤面は描かない)
- 使い方: `python3 -X utf8 render_time_cause.py <time_cause.json> <出力 PDF>`
- ページ: 1 ページ目(局ごとの表 ― 組・局・`kifuId`・手数・序/中/終の秒・長考の回数・最長の 1 手・連続・
  中考の回数・本人/相手の飛車の筋の印・時間切れか) / 2 ページ目以降(組ごとに「要因の候補」― C1〜C6 の中央値の
  表〈時間切れの局・他の局〉・C7/C8 の分数・C9 の 2×2 の内訳・C10 の局ごとの表) / 最後(時間切れで負けた対局
  ごとに、中盤の手ごとの秒を縦棒で描く帯〈`MidBars` Flowable。手目を横軸、秒を棒の高さ、10 秒の参考線
  〈`TIME_VALUES.longThinkSec` と同じ値。新しい閾値ではない〉、分かれ道の手は棒の色を変えて丸い印を添える〉)
- **`kifuId` 列(実装担当の判断)**: `--time-limit-sec` が同じ複数の `--kifu-dir` を 1 つの組に合算すると
  (実データ: `tatsunami20`・`tatsunami3` はどちらも 180 秒 = 「3 分」)、局番号(`gameNo`)は元の `--patient`
  ごとに 1 から始まるため、同じ組・同じ局番号が別の対局を指すことがある(実データで実際に起きた)。1 ページ目の
  表と帯の見出しに `kifuId` を足して一意に見分けられるようにした。
- 数の照合・禁止語・書体の埋め込みの確認は `render_direct.py`(`emit()`)・`render_front.py` と同じ考え方。
  禁止語は `render_whatif.py` の `BANNED` と文字どおり同じ 15 語(「原因」「傾向」を含む ― 見出しは
  「時間の使い方」「要因の候補」にした)。中央値の小数(例: `11.5 秒`)は `[0-9]+` の正規表現で `11`・`5` に
  割れるため、表示に使う文字列そのものから許す数を作る(`digits_of`。実装担当の判断)
- この文書は「考えられること」「試せること」のような解釈・助言の文を持たない(B の役目ではなく、道具が確かめた
  数を並べる付録。`render_direct.py`・`render_whatif.py` と同じ位置づけ)
- 依存はこの README の「依存」節と同じ(`reportlab`・`pymupdf`)。新しい依存は足していない
- この python の道具も vitest の対象外(`report-pdf/` の他の道具と同じ理由)。守りは、合成データ(局 2 つ・
  長考の手が分かれ道に当たる/当たらない・fork が null の組を含む)での rc=0・書体埋め込み確認と、実データ
  (`tatsunami20`・`tatsunami3`・`tatsunami-long` の 3 組、局 44)での実行時確認(rc=0・全書体埋め込み・fitz で
  PNG 化した目視確認。時間切れで負けた 3 局の帯 ― `whatif-v2` あり/なしの両方を含む ― も確認した)

### 「探索の結果」のページ(STEP TIME-CAUSE-2・STEP TIME-CAUSE-3、docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §7.5・§9.4)

`scripts/playtest/timeSearch.ts` が作る `time_cause_search.json` を、任意の `--search` 引数で受け取って
最後に足す(渡さなければ従来どおり付録 4 は変わらない)。

- 使い方: `python3 -X utf8 render_time_cause.py <time_cause.json> <出力 PDF> [--search <time_cause_search.json>]`
- ページ(STEP TIME-CAUSE-3 で差し替え。226 組の一覧はやめた): 見出し「時間と一緒に起きている条件(探索)」。
  「崩れ」の定義のノートボックス → (i) 深さ(1〜3 条件)ごとの表を 2 つ(長考と一緒に起きている条件・崩れと
  一緒に起きている条件。どちらも試した組の数・採用候補の数・再現の数・偶然でも残る数の目安〈二項分布の裾 ×
  採用候補の数〉) → (ii) 共通因子の表(上位 15。部品〈単独の条件〉ごとに、長考・時間と崩れ・速く指して崩れの
  3 つのアウトカムを「単独で再現」「組で再現」「―」の 3 語で分類) → (iii) 時間と崩れの両方を説明する条件の
  一覧(長考の探索で再現し、かつ崩れの線も両組で越えた条件。0 件なら「0 件でした。」とだけ書く) →
  (iv) 速く指して崩れの条件の一覧(崩れを目的変数にした探索で再現し、時間の線は越えなかった条件。上位 10)。
  一覧の全量(226 組)は `time_cause_search.json` に残る(PDF には出さない)。
- 列名・値の日本語(`COLUMN_LABELS`・`VALUE_LABELS`)は、この段が測った量をそのまま名付けたもの(`phase` の
  早/中/終・`evalBand` の優勢/互角/劣勢〈`_head.py` の `RANK_JP` と同じ語〉・真偽値は既存の `yn()`)で、新しい
  将棋の判断ではない。
- A/B/C(`lib/timeSearch.ts` の `Kind`)は PDF では「時間だけ」「時間と崩れ」「速く指して崩れ」と書き、
  「A 型」のような語は使わない(「型」は禁止語 ― 2026-09-25 の指示)。`BANNED` に `render_front.py` と同じ
  「型」「クセ」「パターン」を足した(18 語)。`GLOBAL_ALLOWED_NUMBERS` に 300(崩れの境。`STANDING_BOUNDS.aheadCp`)
  を足した。
- 数の照合(`emit()`)は既存のページと同じ考え方。条件の文字列(`condition_text`・`factor_condition_text`)も
  `digits_of` で自分自身の数を許す集合にしてから `emit()` へ通す(`c10_table` 等、既存の数値セルの流儀と同じ)
- 禁止語チェックは既存と同じ(「原因」の語そのものを固定文に一切使わない ― 「原因ではなく」のような否定文でも
  `emit()` は語の有無だけを見るため書けない。実装担当の判断)
- 守りは、合成の `time_cause_search.json`(再現した組が有る場合・無い場合の両方。B/C 型の条件が有る場合・無い
  場合の両方)での rc=0 確認と、実データ(`tatsunami20` = 発見用・`tatsunami3` = 検証用)での実行時確認
  (rc=0・ページ数〈10 ページ〉・禁止語 0・テキスト抽出での目視確認)

## B の「分かっている事実」を機械で組む(`answer_facts.py`。STEP DELIVER-1、docs/STEP_DELIVER1_PLAN_2026-09-25.md §3 の 4)

```
python3 -X utf8 answer_facts.py --name <表示名> \
  --patient <patient_report_data.json> --time-limit-sec <秒> [--patient … --time-limit-sec … …] \
  [--whatif-v2-dir <dir>]… [--read-dir <dir>]… \
  --direct <direct_answers.json> --direct <final_positions.json> \
  --time-cause <time_cause.json> [--time-search <time_cause_search.json>] \
  --out <md>
```

**数を自分で計算しない。** `check_answer.py` を import して、その `PatientFile`・`combined_groups_of`
(`CombinedGroup`)・`read_combined_of`・`side_match_of`・`direct_materials_of`・`time_cause_materials_of`・
`tag_of_time_limit_sec` が既に作っている材料から数を**引くだけ**である。**`check_answer.py` は 1 バイトも
変えていない。** 新しい集計・新しい中央値・新しい分数はここに無い。

- 出力は基準版(v7)と**同じ見出し構造**の md。機械で組むのは「分かっている事実」の 4 ブロック(14 個の
  箇条書き)だけで、文の形は基準版のまま・差し替えるのは数だけ。それ以外は `<!-- TODO: 読み -->` で空ける
  (「この冊子の約束」だけは数を含まないので固定文)。
- 数が引けない箇条書きは、その 1 行だけ `<!-- TODO: 読み -->` に落とし、標準エラーへ
  「どの数が出せなかったか」を出す(黙って省かない)。
- **組の見分け**: 「3 分の組」は `check_answer.py` と同じ `min3`/`min10` のタグ。「今回の組」は、その
  タグの `--patient` のうち**最後に渡されたもの**(`deliver.ts` は組を前回 → 今回の順に渡す。実装担当の判断)。
- **中盤の長考の回数**は `longThinkCountByPhase.mid` を使う(局ぜんたいの `longThinkTotal` ではない。
  基準版の「中盤 N 秒の中身…長考が M 回ずつ」は中盤の回数と一致する)。
- **READ を回した局の数**は `--read-dir` の `*.jsonl` の**ファイル数**(局ごとに 1 本)。数の集計ではなく
  入力の数え上げ(実装担当の判断)。
- 実測(固定材料 44 局、基準版と同じ材料): 14 / 14 を生成。基準版の同じ 4 ブロックと数の一覧が
  **順序つきで完全一致(118 個)**、かつ**文字まで同一**。生成物は `check_answer.py` rc=0
  (校正: 1 つの数を故意に変えた版は rc=1 で「データに無い数」として落ちる)。

## 納品フォルダの伏せ字・個人情報の検査(`check_delivery.py`。STEP DELIVER-1、計画 §3 の 6)

```
python3 -X utf8 check_delivery.py <顧客フォルダ> [--forbid <語>]…
```

`<顧客フォルダ>` 直下の `*.pdf`(`fitz` でテキスト抽出)と `*.md` に、次が無いことを確かめる。あれば
**rc=1** で、どのファイルの何ページ・何行に何があったかを標準エラーへ出す。`direct/` の JSON は対象外。

- `--forbid <語>`(繰り返し可)、`@`、`/Users/`、「水匠」
- 禁止語 18 語(悪手・弱点・癖・型・傾向・原因・ミス・見落とし・改善・練習・必ず・明らか・あなた・
  ご自身・いつも・がち・クセ・パターン)。**この 18 語は書き写さず、`check_answer.py` の `BANNED_WORDS` の
  先頭 18 語を import して使う**(語のリストを二重に持たない。司令塔の指示)
- 実測(固定材料の納品フォルダ 7 本 = PDF 5 冊 + md 2 本): 禁止語 18 語・`@`・`/Users/`・「水匠」は
  **0 件**(rc=0)。校正: 「原因」と `@` を含む md を置くと 2 件を挙げて rc=1。
- **注意**: `--forbid` に**お客さま自身の表示名**を渡すと必ず落ちる(本人の冊子に本人の名前が出るのは
  正しい)。実測では 42 件(本編・付録 1・B の本文)。`--forbid` は「出てはいけない語」に使う。

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
- **`render_front.py`(STEP TIME 作業 2・作業 3・作業 4)も同じ理由で vitest の対象外。** 発見の判定そのもの
  (何を出すか)・固定文そのもの(§5.2・§5.3・§5.5)は `lib/reportData.ts`・`lib/findingTexts.ts`(どちらも vitest
  の対象)がすでに決めているため、この道具の責務は「描くだけ」に絞ってある。守りは、合成データ(5 種類の発見が
  すべて `shown: true` の組・すべて `shown: false`(none だけ)の組・`previous` の 3 通り(前回出た/今回も出た・
  今回は出ない・前回出ない/今回出た)・`time.available: false` の組)での rc=0・禁止語 0・数の照合・ページ数 4〜6
  の実行時確認と、実データ(14・10・20 局の 3 組)での実行時確認(§4・§6.10 の 3 の校正の表と一致すること)。
  作業 3 では、`finding_texts.json` を渡した場合(3 段・§5.3 の固定文が入る)と渡さない場合(今の形のまま)の
  両方を実データで確認し、第 6 版 20 局の `main.pdf` 本文の完全一致(既存の確かめ)も変わっていないことを確かめた。
  作業 4 では、実データ 3 組で「ひとことで」の文字列・試せることのまとめの項目数・表の名・「組」0 件を確認し
  (実測は `scripts/playtest/README.md` の「伝わる形」節を参照)、変異(禁止語チェックの「組」判定を外す)で
  合成データの「組」を含む文が rc=0 になってしまうこと(= 検査が無いと通ってしまうこと)を確かめたうえで戻した。
