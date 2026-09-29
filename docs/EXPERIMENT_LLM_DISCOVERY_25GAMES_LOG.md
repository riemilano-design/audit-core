# 25 局 LLM 独立分析実験 ― 実験席の記録(2026-09-29〜)

指示書: [EXPERIMENT_LLM_DISCOVERY_25GAMES_BRIEF_2026-09-29.md](EXPERIMENT_LLM_DISCOVERY_25GAMES_BRIEF_2026-09-29.md)。この記録は指示書 §10 の手順ごとに、実験席が何をどう作ったかを書く。**束・依頼文・席の生の回答の材料は `scripts/playtest/out/c5/experiment-llm-25/`(gitignore)に置き、コミットしない。** 席の回答の原文だけ `docs/EXPERIMENT_LLM_DISCOVERY_25GAMES_SEAT_{A,B,C}.md` に保存する(語を変えない)。

## 1. 手順 1 ― 材料の束(bundle)を作った(2026-09-29)

### 1.1 作ったもの(すべて `scripts/playtest/out/c5/experiment-llm-25/`)

| ファイル | sha256 | 大きさ | 何 |
|---|---|---|---|
| `bundle.md` | `bcf741dfb17d912bc4e8d0b1c0b524d02d9d9354b2523eae7e65901892d0d2f1` | 424,870 バイト・2,958 行(推定 約 12 万トークン) | 材料の束。Markdown の表(§0 読み方・対応表・鍵の意味、§1〜§11 が材料) |
| `bundle.md.extract.json` | ― | ― | 抽出の記録(束の sha256、元ファイルごとの sha256、行数) |
| `build_bundle.py` | `dca5bf186d7cfed77521260a8ced44ce7410a18310f76004c8428e6ff0036759` | ― | 束を作った python(`python3 -X utf8 build_bundle.py scripts/playtest/out/c5 <出力>`)。抽出だけ。再計算・丸め直し・補完はしない(数は json の表現をそのまま写す) |
| `request.md` | `bb1b3aca8235ab17867053bd9db633eefd5aaf118bea2fd1b1712ffee23e108b` | 431,963 バイト・3,021 行 | 依頼文 = 前置き(守ること 6 点)+ 指示書 §1〜§7 の原文(sha256 `dd28dc9ff4fa95717cd9f13fe18dec864f79d914bf390932e15a373e755b19ec`)+ 束。**3 席に同じ文** |

元ファイルは git HEAD `e0ecc9c` 時点の `scripts/playtest/out/c5/` の実物(sha256 は `bundle.md.extract.json` の `sources`)。

### 1.2 抽出の記録(どのファイルのどの鍵から。束の §0.1 と同じ)

| 束の節 | 元ファイル | 鍵 | 行数 |
|---|---|---|---|
| §1 | `pipe-3min/report/patient_report_data.json` | `games[]`(no・id・side・total・result・ending・events・scores・plies・marks) | 25 局 |
| §2 | 同 | `events[]` 全欄 | 155 |
| §3 | 同 | `overview`・`findings[]`・`escapeScenes[]` | 7 escape |
| §4 | 同 | `time.*` 全欄 | ― |
| §5 | `pipe-3min/report/sfens.json` | `{gid}.side`・`{gid}.moves` | 25 局 |
| §6 | `deliver1/direct/direct_answers.json` | `values`・`counts`・`answers[]`(sfen 含む) | 103 |
| §7 | `pipe-3min/p2/whatif-v2/g*.jsonl` | meta(values・mirrored・originalUserSide・plyOffset)・position 行・scene 行・summary 行 | fork 404 / 非 fork 629 / scene 500 / summary 25 |
| §8 | `pipe-3min/p2/read/g*.jsonl` | meta(values)・position 行・summary 行 | 404 / 25 |
| §9 | `deliver1/direct/time_cause.json` | `games[]` 全欄・`groups[0]` 全欄 | 25 |
| §10 | `deliver1/direct/final_positions.json` | `entries[]` | 1 |
| §11 | `pipe-3min/report/opening_recognition.json` | `definitions`・`useOfThisFile`・`proposal`・`silence`・`rows`(completed と evidence≥2 の forming) | 25 |

**省いたもの**(元ファイルにはあるが束に無い。束の §0 に明記): 各手の SFEN(`sfens.json` の `sfens`)、whatif-v2 の候補の読み筋 `pv`・scene 行の `pv`・position 行の `sfen`、分かれ道でない局面(§7.2)の候補 2〜5 番目(第 1 候補・`actualRank`・`loss` は残した)、opening_recognition の `reached` のうち forming で evidence 1 の項目。理由: 束を 3 席(Claude・GPT・Gemini)が 1 回の会話で読める大きさに収めるため(省く前は 45 万バイト・推定 13 万トークン)。**再計算は一切していない**。

**含めていないもの**(意図的、指示書 §9): 現行ルートの出力(`answer_menu.json`・`exit_candidates.json`・本編 PDF)。

**書き換えたもの**: 印(tags)の辞書は true の名前だけの列挙に(`-` = 全部 false)、ladder は `ノード数:第1/実戦/差` の並び、分数は `分子/分母`。いずれも情報を落とさない表記の変換で、数は元のまま。顧客の名前(`patient_report_data.json` の `person`)は束に書かず「〇〇さん」。棋譜のヘッダ(相手の名前)は開いていない(`pipe-3min/p2/kifu/` は読んでいない)。

### 1.3 校正(既知の正解で突き合わせ)

束の表の行を機械で読み戻し、元ファイルの値と突き合わせた(scratchpad の検査スクリプト、乱数 seed 20260929)。

| 対象 | 抜き取り | 結果 |
|---|---|---|
| §7.1 fork 404 行 | 40 行 × 全欄 + 候補 5 つ × 5 欄 | 一致 |
| §7.2 非 fork 629 行 | 30 行 | 一致 |
| §8.1 read 404 行 | 40 行 × 全欄 + ladder 5 段 × 4 欄 | 一致 |
| §6 direct 103 行 | 全行 × 8 欄 + 既知の正解(局 13 の 110 手目: actualGapCp 2945・実戦 3a1c+) | 一致 |
| §2 events 155 行 | 全行 × 7 欄 | 一致(5 件は検査側が Python の None を「None」と書いた表記差。束は正しく `null`) |
| §1.1 評価値の推移 | 25 局 × 全組 | 一致(同上) |
| §4.3 perGame | 既知の正解(局 12 = 6.2、局 1 = 4.380952380952381) | 一致 |
| §8.2 tagCrossTable | 既知の正解(g01 drop>drop:5・sacrifice>drop:4) | 一致 |
| §9.1・§11.1・§5 | 25 行すべて(時期別秒・残り秒・中盤の秒列/plies・群・自分側の件数/指し手列) | 一致 |

合計 5,926 点を確かめ、値の不一致 0。

### 1.4 鍵の意味の出どころ

束 §0.2 の定義は道具のコードから写した: `lib/reportData.ts`(TIME_VALUES・phaseOf・perMove)、`lib/gate.ts`(collapseOf)、`lib/failureEvent.ts`(STANDING_BOUNDS ±300)、`lib/whatif.ts`(WHATIF_VALUES・fork/narrowHeld/chanceHeld・side v2)、`lib/read.ts`(ladder・firstVisibleNodes・tagCrossTable・materialLook)、`lib/directAnswers.ts`(浅い読み ≤ 1 万ノードの絞り)、`lib/timeCause.ts`(C1〜C10)。**閾値は仮置きの値であり将棋一般の基準ではない**と束に明記した(`lib/whatif.ts` の申し送り)。

## 2. 手順 2・3 ― 席に掛ける(進行中)

- **席 A(Claude、文脈ゼロ)**: 実験席が subagent(新規会話)を起こし、`request.md` を全部読ませて分析させる。回答は原文のまま `docs/EXPERIMENT_LLM_DISCOVERY_25GAMES_SEAT_A.md` へ。
- **席 B(GPT/ChatGPT)・席 C(Gemini)**: 人間がブラウザで新規会話に `request.md` を渡す。回答は原文のまま SEAT_B / SEAT_C へ(実験席が保存する。人間はテキストを渡すだけでよい)。

(以降、手順 4〜6 は結果が出てから追記する)
