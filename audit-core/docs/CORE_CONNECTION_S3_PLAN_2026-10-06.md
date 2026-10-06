# 将棋側 S-3(死んでいた門を生かして実 run を 1 周)の計画と予測 ― 回す前に封じる

> **封じた後は本文を変えない。** 訂正は日付つきの追記か結果文書に。予測を当てるために範囲・規則・上限を動かさない。外れは外れのまま記録する。
>
> **前提**: 人間の決定(2026-10-06、[CORE_CONNECTION_S2_DECISIONS_AFTER_2026-10-06.md](CORE_CONNECTION_S2_DECISIONS_AFTER_2026-10-06.md)): S-3 = (a) `seal`・(b) 描画・(c) 埋め草禁止・(d) exit-select の draft 経路・(e) `seatRun.ts` の packet を**実 run 1 周に束ねる**。実験単位は「**本番の死んでいた門を生かした状態で、最初から最後まで 1 周する**」。予測は変更ごとに観測対象を分ける。費用は **$5 ハードキャップ**(越えて自動継続しない)。Core は触らない。文字列 Claim は保留。
>
> **Base**: `111253b`(Golden は S-2 の現状、rc=0)。`audit-core/` は触らない。

## 1. 読んで確かめた事実(読むだけの調査。予測ではなく材料)

| # | 事実 | 出典 |
|---|---|---|
| 1 | 席の実 run の入口は `scripts/playtest/runSeats.ts` 1 本。1 周 = 描画 → 席 3 つ(gpt / gemini / claude、順に)→ 器 → 整理役 → 検査 E/I → `run_summary`。deliver のパイプラインに席の段は無い | `lib/seatRun.ts:386-478`、`lib/deliver.ts:59-88` |
| 2 | **`seal` は 2026-10-01(`fc8f6e5`)に指示文 v1.2・描画(節末の「封印語: xxxxxx」)・封筒 schema(`reach.sections[].seal` 必須)・E-1(meta の seal と完全一致)として入ったが、実 run は 7 run とも v1.1 で、seal 入りのコードで席が回った記録は 0** | `lib/seatInput.ts:203, 254-256, 277-287`、`lib/seatOutput.ts:233, 253-255`、`run_summary.seatInput.instructionSha256` 7 run とも `11d1f533…` |
| 3 | 器(schemaAdapters)は `seal` を落とさない(openai strict は全欄 required、anthropic は注記を外すだけ)。落ちるのは席が `null` を入れた返答だけ | `lib/schemaAdapters.ts:92-141, 156-171` |
| 4 | 描画 `list()` が配列を `+` で潰す箇所 5 つ: §0.3 `definitionsDirs`(`;`)、§2 `derivedFrom`、§5 `top1Tags`/`actualTags`、§6 `selfSignature`/`opponentSignature`/`names`、§6.1 `leadsToShapeIds`。全部 packet 側は `string[]` | `lib/seatInput.ts:122-125, 366, 384, 411, 419, 427` |
| 5 | packet に鍵が 1 行も無いのに描いている列 6 つ: §0.3 `engineVersion`・`definitionsDirs`、§4 `bandBefore`・`bandAfter`、§6 `reviewStatus`、§7 `phase`。部分的に鍵が無い列も多数(§5 `actualGapCp` 15/404、§7 `spentSec` 161/1242 など)で、鍵が無い行は `null` と描かれ、§0 は「`null` は packet でも null」と言う(= 席が写すと PNF) | `lib/seatInput.ts:100-112, 404-442`、実物 packet |
| 6 | 指示文 v1.2 に「observations に余分を入れない」向きの文は 0。「文に出す数は observations に写した数だけ」はある | `docs/LLM_SEATS_INSTRUCTION_v1.2_2026-10-01.md:6-7` |
| 7 | `exit-select` 段は `action: "gate"` で子プロセスを起こさない。draft(`exitSelect.ts --draft`、`--packet --integration --request --out` 必須)を作る段は無い。draft は `items`/`rejected`/`questions` の一覧で `adoptedBy` は常に null、**組版は `answer_selection.json` しか読まず draft も rejected も見ない**(採用は人) | `lib/deliver.ts:1562-1569`、`scripts/playtest/exitSelect.ts:48-107`、`lib/exitSelect.ts:40-51, 116-140`、`exit_fill.py` に rejected 0 件 |
| 8 | `seatRun.ts` の E-3(`:436`)と I-4(`:464`)は `cfg.packet` を渡していない(`cfg.packet` は器の生成 `:426` にだけ使う) | `lib/seatRun.ts:426-464` |
| 9 | 費用: 上限は `SEAT_COST_CAP_USD`(`.env` は 10)1 本、**CLI 1 起動ごと**に「送る前に累計 + 見込みが上限を超えたら送らない」。`--max-cost` は無い。コマンドの環境変数で上書きできる(`loadDotEnv` は既存を上書きしない)。席を減らすのは `--hold-back-seat`。`--runs` 既定 2 | `lib/tokenBudget.ts:66-72`、`lib/seatRun.ts:409-415, 548-562`、`lib/env.ts:38`、`runSeats.ts:150, 209` |
| 10 | 実費(USD): 2 席 + 整理役が立った唯一の周 `558b8a81` = **2.9239**(gpt 1.542(2 試行)・claude 0.948(1 試行)・整理役 0.4339)。席 1 つの最大 2.7963(claude 3 試行)。1 周の最大 4.5438。gemini は実績 0(http_failed / held_back)。`--dry-run`(v1.2 + 封印語)の見込みは 2 周で 6.43 | 実物 `run_summary.json` 7 本 |
| 11 | 言い換え(fill_texts)は上限 1 ドル固定・1 回限り・既に回っている → S-3 では回らない。回答生成は無い。組版・門は Python で決定論 | `lib/fillTexts.ts:33-44, 220-223`、`fillTexts.ts:135-136` |
| 12 | Golden c5 は `llm-seats/` の下を全部拾う。新しい run をそこに置くと `seat_runs`・`identity`・`g9` の鍵が増えて Golden が動く。`--customer-dir` は顧客 dir 丸ごとの差し替え | `goldenMasterCheck.ts:131-133, 190-240` |

## 2. S-3 の範囲

### 2.1 直す所(将棋側だけ。`audit-core/` 0・Core 0)

| # | 直し | 直さない所 |
|---|---|---|
| (a) seal | **コードは直さない。** 既に入っている(事実 2・3)。S-3 の実 run が初の計測 | schema・E-1 |
| (b) 描画 `lib/seatInput.ts` | (b1) `list()` の **5 箇所とも配列を JSON の字面で描く**(`["同型矢倉","鬼殺し"]`。空は `[]`)。(b2) **packet に鍵が 1 行も無い列 6 つを描かない**(事実 5)。(b3) 部分的に鍵が無い列で、鍵が無い行は `null` でなく **`(無)`** と描く(`null` は packet の値が null のときだけ)。§0 読み方の 1 行目・2 行目をこれに合わせて直す(「列挙は JSON の配列の字面。`(無)` は packet にその欄が無い = 引けない」)。§6 の表題「すべて draft」は残す | 節の構成・`section()` の登録・seal・数の包含検査の規則 |
| (c) 指示文 **v1.3** `docs/LLM_SEATS_INSTRUCTION_v1.3_2026-10-06.md` | v1.2 の全文 + 版名の行 + 挿入 2 文: (c1) 「`observations[]` には、`statement`・`counterEvidence`・`answers` の根拠に実際に使う値だけを写す。**1 件以上という条件を満たすための埋め草を写さない**。根拠が束に無い項目は `kind` を `unanswerable` にして `neededObservation` を書く」、(c2) 「束の中で配列は JSON の配列の字面で描いてある。`observations[].value` には**配列をそのまま配列として**写す(文字列に連結しない)」。`lib/seatRun.ts` の `FIXED_INSTRUCTION_SHA256` に 1 行。例の検査(`minExamples 3`)は v1.2 の例をそのまま残して通す | v1.1・v1.2 の本文、整理役の指示文 |
| (d) `lib/deliver.ts` | 新しい段 **`exit-draft`**(`action: run`、`exit-select` 段の**直前**)= `npx tsx scripts/playtest/exitSelect.ts --draft --packet <packet> --integration <seatsDir>/<runId>/integration.json --request <request> --obs-registry docs/OBSERVATION_ITEMS.md --today <today> --out <exit>/answer_selection.draft.json`。`runId` は deliver の新しい任意引数 **`--seat-run <runId>`**(無ければ段は `skip`(理由「--seat-run 無し」)で、既存の顧客の流れは不変)。`exit-select` 段は不変 | `exitSelect.ts`・`lib/exitSelect.ts`(落とす規則)・`exit-select` 段・組版・`answer_selection.json`(採用は人) |
| (e) `lib/seatRun.ts` | `:436` の `seatOutputProblems` と `:464` の `integrationProblems` に `packet: cfg.packet`(2 行) | 器の生成、再試行、上限の規則 |
| 試験 | (b) の描画は字で留める(配列 1 件・複数・空、`(無)` と `null` の区別、消えた列)、(d) の段(`--seat-run` 有り/無し、引数の並び)、(e) は checks に H-9 の行が出る合成の試験。既存の試験で**段の数や段の一覧を字で留めている物だけ**は段の追加に合わせて書き換えてよい(他は書き換えない) | |

将棋側 **4 ファイル + 指示文 1 本 + 試験**。行数 **+120〜260**(試験を除く)。

### 2.2 実 run の条件(司令塔が凍結の後に 1 回だけ)

- 出力先: **`scripts/playtest/out/c5/llm-seats-s3/`**(新しい dir。`llm-seats/` に置かない → Golden c5 は動かない。⑦ で「`llm-seats/` に移して Golden を書き直すか」を人間が決める)。
- `--runs 1`、**gemini は `--hold-back-seat gemini --hold-back-reason "S-3: 費用上限 $5 と前回(558b8a81)と同条件"`**(前回も保留。事実 10)。送る席は **gpt と claude の 2 つ + 整理役**。
- **`SEAT_COST_CAP_USD=5`** をコマンドの環境変数で渡す(`.env` は書き換えない)。道具が送る前に止める(事実 9)。司令塔は実 run の前に `--dry-run` を 1 回(無料。見込みを記録)。
- 指示文 v1.3、packet / request は c5 のもの(不変、sha を記録)。`--today 2026-10-06`。
- 実 run の後に司令塔が 1 回ずつ: `seatOutputCheck.ts --packet`・`integrationCheck.ts --packet`(現行コードでの照合の再確認)、`exitSelect.ts --draft`(deliver の段を通さず単体で。deliver を c5 で回すと納品ログに触るため)、`run_core_path_shogi.py`(C-2 の道具。新しい席の H-9 を Core でも測る)。
- fill_texts・組版・納品は回さない(事実 11、採用は人)。

## 3. 予測(封じる。**0/1** = 当たり外れが二値、**幅** = LLM の出力に依るので粗い。幅の所は粗いと先に書く)

### 3.1 (a) seal → E-3 が走るか

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| a1 | 封筒 schema(`reach.sections[].seal` 必須)を**返ってきた封筒が通るか** | 返ってきた封筒は **全部通る**(器が required で強制。通らなければ再試行 → 3 回落ちて空席) | 0/1(席ごと) |
| a2 | E-1 の封印語の不一致 | 席ごと **0〜2 節**(語 6 桁の写し間違い。gpt strict は 0 と見る) | 幅・粗い |
| a3 | checks.json の E-3 の行が **H-1〜H-11 の行を含む**(= E-3 が実物で初めて走る) | **含む**(2 席とも) | 0/1 |
| a4 | 空席(3 試行とも落ちる) | **0 席**(前回 0f1b019e の claude の空席は H-1 の数の不一致が原因で、seal ではない。v1.3 で増える要因は無い) | 0/1 |

### 3.2 (b) 描画 → H-9 の内訳

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| b1 | H-9 の VM のうち「配列を文字列に潰した」型(value が string で packet が配列) | **0 件**(S-1 では 18) | 0/1 |
| b2 | H-9 の PNF のうち `reviewStatus` など**消した列**への参照 | **0 件**(S-1 では 1) | 0/1 |
| b3 | H-9 の PNF のうち `(無)` と描いた欄への参照 | **0 件**(席は `(無)` を数として写せない) | 0/1 |
| b4 | H-9 の VM・PNF の**残り**(席の書き間違い・分母の読み違いの型。S-1 では 2) | 2 席合計 **0〜4 件** | 幅・粗い |
| b5 | 配列の欄(`rows[n].names` 等)を根拠に引いた観測で value が**配列のまま**で GROUNDED | **1 件以上**(席が配列を写せることの実証。0 なら (c2) の指示が効いていない) | 0/1 |
| b6 | 描画の数の包含検査(送る前) | 通る(配列の字面は数を増やさない) | 0/1 |
| b7 | `seat_input.md` のバイト数 | v1.2 の 227,828 B から **−2%〜+6%**(列 6 つ消える・`(無)` と JSON の括弧と引用符が増える) | 幅 |

### 3.3 (c) 埋め草禁止

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| c1 | 項目あたりの observations の中央値 | **1〜3**(前回 558b8a81 claude は 12 項目に観測 … 中央値は結果で書く) | 幅・粗い |
| c2 | **H-9 で落ちた観測のうち statement にも counterEvidence にも answers にも値が出ない物**(埋め草の印) | **0 件**(S-1 の 25/24 がこの型) | 0/1 |
| c3 | `kind: unanswerable` の項目 | 2 席合計 **1〜6**(前回 0f1b019e gpt に 1) | 幅・粗い |

### 3.4 (e) seatRun の packet → checks.json

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| e1 | checks.json の席の problems に **`H-9` の行**が出る(skip でなく ok/NG の結果として。NG が 0 なら行は出ないので「H-9 skip の文が無い」で見る) | H-9 が照合されている(skip 0) | 0/1 |
| e2 | checks.json の `integration.problems` の I-4 H-9 行 | **0〜6**(b4 の残りが代表に写れば出る) | 幅 |
| e3 | 現行コードの CLI(`seatOutputCheck --packet`・`integrationCheck --packet`)の結果と checks.json の E-3/I-4 の行が**一致** | 一致(同じ関数) | 0/1 |
| e4 | Core の経路(`run_core_path_shogi.py`)の state と H-9 の結果が観測単位で一致 | **100%**(C-2/S-1 と同じ) | 0/1 |

### 3.5 (d) draft → rejected の束

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| d1 | `answer_selection.draft.json` が出る(単体実行) | 出る、`adoptedBy: null` | 0/1 |
| d2 | rejected になる束の割合 | **40〜80%**(前回の I-4 は束の半分前後に H-1/H-3/H-5 の NG。H-9 を足しても大半は H-1/H-3/H-5 で落ちる) | 幅・粗い |
| d3 | rejected の `failedChecks` に **H-9 だけ**で落ちた束 | **0〜2** | 幅 |
| d4 | deliver の段 `exit-draft` は `--seat-run` 無しで skip(既存の顧客の流れ不変) | skip | 0/1 |
| d5 | **冊子の変わるページ** | **0**(組版は draft を読まない。採用は人。S-3 は「拒否が draft に出る」までを見せ、冊子は変えない。これは設計の帰結で、S-3 の欠陥ではない) | 0/1 |

### 3.6 費用

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| f1 | 実費の合計(2 席 + 整理役) | **2.5〜4.8 USD**(前回 2.92 + v1.3 と描画の増分 + 再試行 0〜1 回) | 幅 |
| f2 | 上限で止まる(`cost_cap`) | **止まらない**(止まれば f1 の上側が外れ) | 0/1 |
| f3 | `--dry-run` の見込み(1 周・2 席) | **2.4〜3.4 USD** | 幅 |
| f4 | 5 USD を超える | **超えない**(道具が送る前に止める。超えたら手順の欠陥) | 0/1 |

### 3.7 その他

| # | 観測対象 | 予測 |
|---|---|---|
| g1 | Golden c5(`--expect`、新 run は `llm-seats-s3/`) | **rc=0 のまま** |
| g2 | `audit-core/` 差分 | 0 |
| g3 | typecheck 新しい赤 | 0 |
| g4 | vitest | 既存は落ちない(段の一覧を字で留めた試験の書き換えを除く)。新規 **+6〜14** |
| g5 | 違う項目(0/1 の欄) | **0〜3**(疑うのは a2(gpt の strict でも写し間違いは起きうる)・b5(席が配列を書かず文字列にする)・c2) |

## 4. 手順(3 役)

1. この文書を封(コミット)。
2. 実装担当(§2.1。**作業木を書き換える git 操作を使わない。API の鍵を使わない(`--dry-run` も禁止: countTokens は鍵を使う)。席を回さない。deliver を実物で回さない**。合成材料だけ。コミットしない)。
3. 司令塔が凍結 → 独立監査 → GO でコミット。
4. 司令塔が **実 run を 1 回**(§2.2): `--dry-run` 1 回 → 見込みを記録 → 実 run 1 回(`SEAT_COST_CAP_USD=5`)→ 席ごとの実費を `run_summary.json` から記録 → 事後の照合 4 本(§2.2)→ §3 と項目別に照合。
5. 結果文書 → 人間の判断(⑦ Golden に入れるか、席の封筒・draft をどう読むか、次)。

## 5. この文書がしないこと

Core の変更。`audit-core/` の変更。schema・E/I/H の規則の変更。採用(`adoptedBy`)を機械が付けること。組版・納品・fill_texts。Golden の書き直し(⑦ は人間)。gemini を回すこと。`.env` の書き換え。

## 6. 止まる所

`SEAT_COST_CAP_USD=5` で道具が止めたらそこまで(続きを回さない)。描画の数の包含検査が落ちたら送らず REVISE。Golden c5 が rc≠0 になったら HUMAN(新 run を `llm-seats/` に置いてしまった等、手順の欠陥)。
