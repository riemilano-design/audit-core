# STEP PIPE 計画: 棋譜のフォルダからレポートまでを一本の流れにする(2026-09-21、司令塔 e3)

人間の決定(2026-09-21): 立浪さんへ第 6 版を渡した。**「一本の流れはやらないとね。効率的かつ早くやれるように整えて」。** 以前の規則「一括自動化は 20 局版の後」(2026-09-15 の効率化の規則)の「後」が今である。

位置づけ: `scripts/playtest/` の開発補助。本番導線(`apps/`)・`data/`・判定の値(GATE_VALUES)・条件式の定義は**変えない**。既にある道具を**呼ぶ順に並べるだけ**で、将棋の判断・閾値・文言を新しく書かない。

## 1. いまの手作業(実物。2026-09-21 の Lishogi 90 局の評価と、第 4〜6 版の作成から)

| 段 | 道具(すでにある) | いまの回し方 |
|---|---|---|
| S1 読み込み | `kifu-import-check.ts <kif> --fixed <out> --id <id> --source <text> --as sente\|gote` | 1 局ずつ手で。後手の局は回して固定棋譜にする(D0-SIDE) |
| S2 評価 | `replay.ts <fixed.json> --nodes 400000 --reference-nodes 400000 --threads 1 --direction-rule current --out <段1>` → `rescreen.ts <段1> --out <段2> --deep-nodes 4000000` | シェルで 5 本並行。実測 1 局あたり段 1 が約 5 分・段 2 が約 8 分、5 本並行で 1 局あたり約 3 分(90 局中 26 局の時点) |
| S3 診断 | `diagnose.ts <段2 …> --events … --events-rise … --events-maxdrop … --evaluator …` | 1 人ぶんまとめて手で |
| S4 判定 | `gate.ts --person … --test-person … --material … --test-sente … --test-gote … --conditions lib/conditions --out … [--records-append]` | 入力 30 本を手で並べる |
| S5 レポートの材料 | **無い**(司令塔の使い捨てスクリプトは /tmp の掃除で失われた) | 記録 → レポート用 JSON |
| S6 言い換え | 司令塔が会話の中で書く(`prose.json`)。数と指し手は機械で照合 | 手作業(LLM は言い換えのみ。CLAUDE.md ルール 5) |
| S7 PDF | 凍結した第 6 版テンプレート(python・reportlab。gitignore の `scripts/playtest/out/report-template-v6/`) | 手で 3 コマンド |

## 2. 作るもの

### 2.1 作業 A: `scripts/playtest/pipeline.ts`(S1〜S4 を順に呼ぶ)

```
npx tsx scripts/playtest/pipeline.ts --person <id> --kifu-dir <dir> --work <dir> [--me <名前> | 規約のファイル名] [--parallel 5] [--compare-dir <段 2 の記録のフォルダ …>] [--until import|evaluate|diagnose|gate] [--dry-run]
```

- **既存の道具を子プロセスで呼ぶだけ**(import して中身を複製しない)。引数は §1 の表のとおりに固定し、表と違う値を渡せる旗は作らない(ノード数は 2 段階評価の採用値)。
- **途中から再開できる**: 段ごと・局ごとに、出力があって完結している(段 1 は最後の行が summary、段 2 は空でない、等。判定は Lishogi の `run-game.sh` と同じ)なら飛ばす。
- **並行はジョブの列で上限つき**(既定 5 = エンジンの上限。engine-parallel-rule)。始めに本数を標準出力へ宣言する。
- **所要の記録**: 局ごとの開始・終了・rc を `work/timing.jsonl` に書く(原価を測るため)。
- **失敗は止めずに集める**: 1 局が失敗しても他は進め、最後に失敗の一覧と rc ≠ 0 で終わる。成功はログでなく成果物で確かめる(symptom-not-yet-verified)。
- 先後: `--me <名前>` をそのまま `kifu-import-check.ts` へ渡すか、ファイル名の末尾 `-sente` / `-gote` を `--as` に渡す。どちらも無ければ止まる(推測しない)。
- S4 は `--compare-dir` があるときだけ。`--records-append` は**付けない**(棄却の記録へ書くのは、予測を先にコミットした正式な実行だけ。司令塔が手で回す)。
- 出力先は `--work`(既定は gitignore の `scripts/playtest/out/`)。`records/` へは書かない。
- **試験はエンジンを起こさない**: 子プロセスの起動を差し替えられる形にし、順序・飛ばし・並行の上限・失敗の集め方・引数の固定を試験で見張る。

### 2.2 作業 B: `scripts/playtest/reportData.ts`(S5)と、S6 の材料、S7 の置き場

- **S5** `reportData.ts --person <id> --name <表示名> --records <段 2 …> --kifu <fixed.json …> --gate <gate.jsonl> --out-patient <patient_report_data.json> --out-audit <audit_metrics.json>`。記録から**事実だけ**を組む純粋関数を `lib/reportData.ts` に置く。
  - **受け入れの基準(金の標本)**: 2 人目 20 局の記録(`records/real-02`・`real-03`)から作った `patient_report_data.json` が、凍結した第 6 版のもの(`scripts/playtest/out/report-template-v6/patient_report_data.json`)と**欄の順を除いて一致**する。食い違う欄は、直す前に**どちらが正しいかを記録から確かめて**報告する(凍結した側が誤りなら、それは第 6 版の不備として司令塔へ)。
  - 本人向けの側に開発用の語(G-1〜G-4・sha・nodes・gitHead・definition)が入ったら止まる(いまの `split_data.py` と同じ見張り)。
  - 各手の局面(SFEN)も同じ道具で出す(いまの `sfens.ts`)。
- **S6 の材料**: 1 局ずつ載せる局(優勢から負けた局の全部 + 劣勢から勝った局のうち下がり幅の大きい 3 局まで)について、事実の一覧(形勢の段の変化・場面・数)を `prose-request.md` に出す。`prose.json` が無ければここで止まり、「言い換えが要る」と出す。ある場合は照合(文の数がその局の事実に無ければ止まる・使わない語・優勢から負けた局に「優勢」がある)を通してから S7 へ。**照合の規則は凍結した `_mid.py` のものを変えない。**
- **S7 の置き場**: 凍結したテンプレートの道具(python)を `scripts/playtest/report-pdf/` へ**そのまま**移してコミットする(個人のデータ・PDF・`prose.json` は入れない。gitignore のまま)。呼び出しは `pipeline.ts` の最後の段として足す(`--until` に `report-data|prose|pdf` を足す。作業 A の後に司令塔がつなぐ)。埋め込める書体が無ければ作らずに止まる・作った後に全書体が埋め込みかを確かめる、は残す。
- 第 6 版の PDF を**同じ入力から作り直して、本文の文字が一致**することを確かめる(見た目の 1 ページずつの比べは司令塔)。

### 2.3 順序と体制(1 作業 1 セッション)

1. この計画をコミット(docs のみ、司令塔)。
2. 作業 A と作業 B を**別々の使い捨ての実装担当で並行**(ファイルは重ならない: A = `pipeline.ts`・`lib/pipeline*.ts`・その試験、B = `reportData.ts`・`lib/reportData*.ts`・`report-pdf/`・その試験)。
3. 監査は**まとめて 1 回**(独立の監査担当)。計画の事前読みは省く(2026-09-21 の方針)。
4. 司令塔がつなぎ(S5〜S7 を `pipeline.ts` へ)、Lishogi の 1 人ぶん(30 局)で**通しの実測**(所要と、手が入った箇所を数える)。エンジンを使うのはここだけで、Lishogi の評価が終わってから。

## 3. 完了の条件

- (a) 2 人目 20 局について、`pipeline.ts` 1 コマンド + `prose.json` で、第 6 版と本文の一致する PDF が出る(評価済みの記録があるので S2 は全部飛ばされる = 再開の確かめも兼ねる)。
- (b) Lishogi の 1 人ぶんで、棋譜のフォルダから `prose-request.md` まで人の手が入らない。所要を `timing.jsonl` から報告する。
- (c) typecheck・vitest・check-docs が通る。試験はエンジンを起こさない。

## 4. やらないこと・限界

- 言い換え(S6)の自動化はしない。API の課金と外部送信は人間の判断(2026-09-21: いまは会話の形で足りる)。
- レイアウトは変えない(第 6 版で凍結)。
- 判定の値・条件式・文言の規則を変えない。新しい物差しを足さない。
- 同意のない棋譜(Lishogi)から本人向けのレポートを外へ出さない(物差しと流れの検証だけ)。
- python(reportlab)に依存したままである。別の環境で動かすときの手当て(依存の固定)は、この STEP では書き残すだけにする。

## 5. 実装と監査の記録

### 5.1 作業 A(`pipeline.ts`、2026-09-21)

- 実装: 使い捨ての実装担当(worktree)。`scripts/playtest/lib/pipeline.ts`(sha256 `cb8ebffac415…`)・`scripts/playtest/pipeline.ts`(`2b9b7bcf7b77…`)・`scripts/playtest/lib/pipeline.test.ts`(`c9ba23415d8e…`、51 件)・`scripts/playtest/README.md`(`c9f887d44d79…`)。
- 途中の直し 1 回: 判定の役割の向きが逆だった(原因はこの計画 §2.1 の書き方の曖昧さ)。**材料 = お客さん(`--person`)、試す側 = `--compare-dir`** に直した。D3-COND 計画 §14・§15.2 の正式な実行と同じ向き。
- **計画に無かった追加**: `--compare-person <id>`(`gate.ts` が求める「試す側の人」のラベルを渡す手段が計画に欠けていた)。`--work` は必須の引数として実装した(§2.1 の「既定は out/」は採らない。置き場を毎回はっきり書かせる)。
- 独立監査(使い捨ての監査担当、A と B をまとめて 1 回): **作業 A は GO**。監査側の実測: typecheck:scripts rc 0、vitest 62 ファイル 969/969、check-docs rc 0。抜き取りの変異 2 本(段 2 のノード数を変える・`--records-append` を足す)はどちらも検出、sha256 で戻りを確認。引数は `replay.ts`・`rescreen.ts`・`kifu-import-check.ts`・`gate.ts` の使い方と 1 つずつ照合。`--records-append` は構造的に付かない。`records/` へ書かない。GATE_VALUES・`apps/`・`data/` に触れていない。
- 司令塔の承認の根拠: 上の監査の GO、実装側の報告と監査側の実測の数の一致(969)、コミット前の sha256 の照合(実装側の報告と同じ)。エンジンを通した実測(§3 (b))は**まだ測っていない**。Lishogi の評価が終わった後に測る。

### 5.2 作業 B(`reportData.ts`・`report-pdf/`、2026-09-21)

- 実装: 使い捨ての実装担当(worktree)。`scripts/playtest/lib/reportData.ts`(sha256 `f7dadd29d088…`)・`lib/reportData.test.ts`(`42b8741699e8…`)・`scripts/playtest/reportData.ts`・`scripts/playtest/report-pdf/`(凍結した第 6 版の道具 6 本 + `build.sh`・`check_fonts_embedded.py`・`README.md`・`.gitignore`)。
- **金の標本との一致**: 2 人目 20 局の記録から作った `patient_report_data.json` と `sfens.json` は、凍結した第 6 版のものと**完全一致**。本編の PDF は本文が完全一致(14 ページ)。凍結した側の不備は見つからなかった。
- 凍結した道具から変えた行は 3 か所だけ(`REPORT_DATA_DIR` で材料の置き場を渡せるようにした。`_head.py`・`_util.py`・`_mid.py`)。照合の規則(使わない語・文に出る数)は変えていない。監査側が diff で確認。
- **計画に無かった判断**: `--title`・`--today` の追加(本人向けデータの必須の欄)、勝敗の導出 `resultOf`、駒名の短い表(竜・全・圭・杏。D0-KIFU2 の慣行)、条件式 ID の既定値(`king_escapes_decrease_v1`・`ahead_move_into_own_king_zone_v1`。上書きできる)。
- 独立監査: **REVISE 1 点 → 直し → GO**(往復 1 回)。指摘は「`resultOf` が終局の種類を見ず、手数の偶奇だけで勝敗を決めている」(反則・千日手・持将棋・中断・不戦では、確かめていない勝敗を断定しうる。ルール 6)。直し: 投了・詰み・切れ負けは従来の規則、反則勝ち・反則負けは終局の語の意味から、それ以外と終局の記載が無い局は**決めずに例外で止まる**。監査側の実測: typecheck rc 0、vitest 952/952、check-docs rc 0、sha256 の照合、差分が `resultOf` まわり・試験・README だけであること、反則の勝敗の向きを `kifuImport.ts`(`endingPly = moves.length + 1`)から独立に導き直して一致。
- 司令塔の承認の根拠: 上の GO、A を取り込んだ状態で司令塔が回した実測(typecheck rc 0、vitest 63 ファイル **1003/1003** = 予測 969 + 34 と一致)、コミット前の sha256 の照合。
- **既知の限界(持ち越し)**:
  - 別冊(`render_appendix.py`)は、`reportData.ts` の出す `audit_metrics.json` からは作れない(`candidate.reps` の `side`・`transitionJp`・`capUsJp` ほか、`engine`・`sideLabel`・`trajectories` などが未実装。`KeyError` ではっきり止まる。静かに誤らない)。凍結した `audit_metrics.json` からは作れる。`report-pdf/README.md` に明記。
  - 反則勝ち・反則負けの実例は手元の棋譜に無く、単体の試験でしか確かめていない。
  - 詰みの表示用の値(±3000)の負の側は、実データに例が無い。
  - 場面の時期(早い・中・遅い)の割り方が 2 つの欄で基準が違う(回す前の手数 ÷ 総手数 と、表示の手数 ÷ 総手数)。元の使い捨てスクリプトの癖をそのまま再現した。第 6 版との一致を優先し、いまは変えない。
  - python(reportlab・pymupdf)と、埋め込める書体(Arial Unicode)に依存する。

### 5.3 作業 C(S5〜S7 を `pipeline.ts` につなぐ、2026-09-21〜22)

- 実装: 使い捨ての実装担当(worktree。1 回目は利用制限で何も残さず中断、出し直し)。`lib/pipeline.ts`(sha256 `118b89205bbe…`)・`pipeline.ts`(`bcf005a48229…`)・`README.md`(`4ec6b5c7843e…`)・新規 `lib/pipelineReport.test.ts`(`f230c2859de4…`、20 件)。
- `--until` に `report-data`・`prose`・`pdf` を足した(**既定の終点は `gate` のまま**)。`--name`・`--title`・`--today` は report-data 以降で必須。判定の出力が無ければ `reportData.ts` を呼ばずに失敗。`prose.json` が無ければ `prose-request.md` の場所を示して rc ≠ 0(言い換えは自動化しない。LLM を呼ばない)。pdf 段は本編だけ(`build.sh` → `render_main.py` → `check_fonts_embedded.py`)。済みの判定は、PDF が `prose.json`・`patient_report_data.json` より新しいこと。出力は `<work>/report/`(PDF は `main.pdf`)。
- **完了条件 (a) を満たした**: 2 人目 20 局を work フォルダの形に写し、`pipeline.ts --until pdf` の 1 コマンドで、`patient_report_data.json` は第 6 版と完全一致、本編 PDF(14 ページ)の本文は第 6 版と完全一致。再実行では何も作り直さない。**監査側も独立に再現した**(名前を変えて回し、差は名前の行だけ)。
- 独立監査: **GO**(直す点なし)。監査側の実測: typecheck rc 0、vitest 64 ファイル 1023/1023、check-docs rc 0、抜き取りの変異 2 本を検出、既存の `lib/pipeline.test.ts` は 1 文字も変わっていない、`reportData.ts` への引数を `parseArgs` と 1 つずつ照合。
- 司令塔の承認の根拠: 上の GO、sha256 の照合、docs だけの 3 コミットを取り込んだ後の typecheck と pipeline の試験 2 ファイルの再実行。
- **既知の限界(持ち越し)**: `--dry-run` は S1〜S4 だけを出す(S5〜S7 のプレビューは無い)。pdf の済み判定は `sfens.json` の時刻を見ない(いまは `reportData.ts` が同時に書くので実害なし)。別冊は作らない(§5.2)。
- **完了条件 (b)(人の手が入らない通しと所要)は、2 人目の新しい棋譜 24 局で実測中。** 結果は §5.4 に足す。
