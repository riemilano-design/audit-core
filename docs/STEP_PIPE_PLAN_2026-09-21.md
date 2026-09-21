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
