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

### 1.5 束の設計の穴(司令塔の観測、2026-09-29 昼。指示書 §13 冒頭)

束 §11 には戦型定義の**件数**(107・すべて draft)と局ごとの認識結果だけがあり、**定義の中身(`recognition_pattern`)を席に渡していなかった**。手順の列(§5)はあったが照合先が無いので、席は「draft だから判断できない」で止まるしかなかった。**これは席の弱さではなく束の設計の穴**。追加の問い H7(棋譜の流れから戦型を認識できるか)は実験 2 として §6 に別に記録する。

## 2. 手順 2・3 ― 3 席に掛け、回答を原文のまま保存した(2026-09-29)

| 席 | 掛け方 | 原本(`scripts/playtest/out/c5/experiment-llm-25/`) | sha256 | 保存先 |
|---|---|---|---|---|
| A(Claude) | 実験席が subagent(新規会話、claude-fable-5-1)を起こし `request.md` を Read で全行読ませた。他のファイルは読まない・コードを実行しないと指示 | `seat_A_claude_raw.md`(255 行・39,738 バイト) | `4c9a1e766556bc61a3789c3ff8698d53d8338d105272ee512abb40d2a9f5974e` | [SEAT_A](EXPERIMENT_LLM_DISCOVERY_25GAMES_SEAT_A.md) |
| B(GPT/ChatGPT) | 人間がブラウザの新規会話に本文貼り付け。回答を一字も変えず保存(司令塔が中継) | `seat_B_gpt_raw.md`(935 行・21,024 バイト) | `2beccf35bf786f3ca2a2cb14d742c21fd09195507e305c87ceae3edd826dea2e` | [SEAT_B](EXPERIMENT_LLM_DISCOVERY_25GAMES_SEAT_B.md) |
| C(Gemini) | 同上 | `seat_C_gemini_raw.md`(55 行・6,163 バイト) | `41659a37c4bdb030c8baa9e15ee679c82d9f1b767b839c150967411f55405785` | [SEAT_C](EXPERIMENT_LLM_DISCOVERY_25GAMES_SEAT_C.md) |

各席には他の席の結果を見せていない。

### 2.1 席の入力が末尾まで届いたか(比較の 6 項目とは別の欄。司令塔の指示)

| 席 | 席の申告 | 束の末尾(§11)を引用しているか(証拠) | 判定 |
|---|---|---|---|
| A | 「1 行目から 3021 行目『(束はここまで)』まで全部読んだ」 | §11.1 の `proposalSignatureClass(案)` を 25 局ぶん拾い、`nakabisha_self`・`shikenbisha_opponent` など §11 の中身を引いている | **届いた**(申告と引用が整合) |
| B | 「3021 行すべてを確認した」 | §11 の署名(douke_yagura・onikoroshi・yagura_37kei)と局の群を列挙している(核 18 局のうち g20 を落とし、それ以外 4 局のうち g13 を落としている。数は書いていない) | **届いた**(引用あり。列挙の抜けは 2 局) |
| C | §7・§10 で「戦型の機械認識データ(§11)が含まれていない」 | §11 の内容を一切引用していない。§1〜§6 の数だけを引いている | **届いていないか読めなかった**(request.md には §11 が 2980 行目から末尾まであることを実験席・司令塔がともに確認。入力の長さの上限で切れたか、読んだうえで見落としたかは束からは判別できない) |

### 2.2 「束に無い数」の照合(指示書 §11「数え直さない」)

| 席 | 印付きの「束に無い数」 | 印なしで束に無い数 | 印付きの数の正誤(実験席が元ファイルで確かめた) |
|---|---|---|---|
| A | 多数(§1.1 の勝ち 16、§1.2 の割合・和 944/79、§1.3 の 7 局、§1.4 の firstVisibleNodes の和 84/19/17/11/7/266・materialLook の和 107/23/11・応手一致 138/401、§1.6 の「同〜」37 行と sameBest 8、§1.7 の群別勝敗 13-5/1-3/2-1・rookMark own=false の 3 敗 1 勝、など約 25 か所) | 表の行数に当たる数(「負け 9 局」「7/7」「n = 4」「2 局」)。いずれも束の表の行数で、数え直しではない(軽微) | **2 か所が誤り**: 「同〜」37 行のうち `sameBest` = true は 8 → **実際は 10**。`pvEscEnd ≥ escEnd` は 6 行(例外 g01 75 だけ)→ **実際は 5 行**(例外は g01 75 と g11 62)。他(和・列挙・群別勝敗・rookMark・最終評価の符号・残り秒の一覧・局面の値)は一致 |
| B | 0(数はすべて束の値。§3 findings の 17%・4% も束にある文) | 0 | ― |
| C | 0 | 0(「崩れの過半数は中盤」は語だけで数を作っていない) | ― |

席 A の 2 つの誤りは、どちらも束の表の行を席が手で拾って数えたもので、**「席が数を作った場合は採用候補にしない」の規則(指示書 §11「数え直さない」)が実測で裏づけられた印**として残す。印の付け忘れは 3 席とも実質無し。

### 2.3 席の回答と原則(指示書 §2・§5)の関係(実験席の判定。司令塔は判定しない)

- **席 C の行動 2(H3)**「迷った局面では、盤上の駒を動かす前に、持ち駒を打つ手がないか確認する」: 根拠は §6 `counts` の打つ 54 vs 33 だけで、基準率(分かれ道でない局面の印の分布)が無い。行動の文そのものは手順であって診断ではないが、この根拠から行動に進むと「打つ候補を指さなかった = 打つ手を思いつかなかった」(原則 5 で禁止)を含意しやすい。**席 A と席 B は同じ数から「行動にしない」と判定している**(A: §6「駒を打つ手を優先する ― 基準率が無く §5 の解釈を含意」、B: §6「駒を打つ手を考える練習 ― 現時点では不可」)。実験席の判定: **採用候補にしない(証拠不足・原則との緊張)**。
- **席 C の行動 1(H2)**「長考した直後の手は一呼吸置く」: 根拠は `afterLongThinkAny` 44 のうち `quickAfterLongThink` 37(束 §0.2 の定義どおりの読み方で、鍵名の読み違いではない)。ただし全体でも 1 手 4 秒以下の手が大半(`bySpent[0]`+`[1]` = 818/944 手。束に無い数、実験席が確かめた)なので、37/44 が「長考後に固有の傾向」かは比べられていない。行動は現行の M5 と同じ(§3.2)。
- **席 B の行動**「10 秒以上考えた局面を後から確認し、分かれ道だったかだけを記録する」: 対局中の手順ではなく復習の手順。承認済みの表(M1〜M9)には無い型。診断を含意しない。
- **席 A**: 「行動にできる」0 件(原則 9・10 を明示して)。
- 禁止語・診断の言い切り: 3 席とも「苦手」「見落とし」「知らない」「時間の使い方が悪い」の型の診断は無し。手の目的・意図の記述も無し(席 A は幾何の印の組み合わせまで)。戦型名は 3 席とも束 §11 の下書き認識にあるものだけ(A: nakabisha_self・shikenbisha_opponent 等、B: douke_yagura・onikoroshi・yagura_37kei、C: 無し)。

## 3. 手順 4 ― 現行ルートとの突き合わせ(指示書 §8 の 6 項目)

現行ルート = `deliver1/direct/answer_menu.json` の M1〜M9(通ったのは **M4・M5・M6**、落ちたのは M1・M2・M3・M7・M8・M9)と、2 周目の本編(`deliver1/9_本編.md`): 観測 3 つ(①優勢 18 局のうち負け 6、②第 1 候補が打つ手だった分かれ道 54 局面のうち実戦は打つ手でない 32、③10 秒以上の手 7/41 と 0〜1 秒の手 22/531)、行動 2 つ(M6 捨て駒を候補に入れる 50/137、M4 攻めと自玉側の候補を 1 つずつ 65/107・76/132)。**席にはどれも見せていない。**

### 3.1 仮説の対応表(主題ごと。同じ数を根拠にしたものを同じ行に)

| # | 主題(根拠の数) | 席 A | 席 B | 席 C | 現行ルートでの扱い | 「拾えていない」か |
|---|---|---|---|---|---|---|
| T1 | 長考直後の手・長考と崩れ(§4 afterLongThink 11/44・9/37、bySpent 7/41 vs 22/531) | H4(直後の崩れ率が全体の約 3 倍〈束に無い数〉。quick で差なし) | H1・H2(長考局面の条件を結合して見る) | H1・H2(直後の早指しの傾向) | 本編観測③(shown)、**M5(通過・行動)**、M4 の条件「10 秒以上」 | 拾われている(観測・行動とも) |
| T2 | 分かれ道の印の分布(§6 counts 打つ 54/33・取る 19/32・引く 5/12) | H2(基準率なし・行動にしない) | H5(属性の組み合わせ・行動にしない) | H3(**行動にする**: 打つ手の確認) | 本編観測②(打つ手 54/22/32、shown)、行動は M6(捨て駒)のみ | 観測は拾われている。**「打つ手」の行動は表に無い**(A・B は行動にしないと判定、§2.3) |
| T3 | 優勢後の負け(§3 aheadLoss 6/18) | H1(c)(負け局の型の 1 つ) | H3・新規候補 C(優勢化後の最初の分かれ道を追う) | H4 | 本編観測①(shown)。行動は無し | 観測は拾われている。**「優勢後の時系列(到達→最初の fork→最初の崩れ)」は表に無い** |
| T4 | 崩れは中盤に多い(§3 overview 79 = 7/41/31) | 1.1 で数を引くのみ | 1-1(分母が無いと注記) | H5 | findings phase(shown)。M1・M9(中盤の時間)は落ちた | 拾われている(観測) |
| T5 | 分かれ道と探索の深さ(§6 103/404、§8 firstVisibleNodes) | H11(266 は 600 未満・84 は 2000 で見える〈束に無い数〉) | H4・新規候補 B(深度別に分類) | ― | **M7(否定型、落ちた)**が同じ内訳を根拠にしている | 拾われている(否定型)。道具側の論点 |
| T6 | 長考 × 分かれ道 × 側の逆(§9 forkFraction 30/56・oppositeSide 4/30) | H5(長考の分かれ道は 2 種〈手で突き合わせ〉) | H2・新規候補 A | ― | M4 は側の一致率(65/107・76/132)を根拠にするが、C7・C8 の分数は表に無い | **部分的に拾えていない**(C7・C8 の分数を根拠にした行動は無い) |
| T7 | 玉の逃げ道(§3.3 escapeScenes 7 行) | H12(7/7 で減る・行動候補だが証拠不足) | H6(補助変数) | ― | `escapeScenes` は現行の条件 C-1 の場面(道具にある)。M 表には無い | 材料は現行にある。行動は無い |
| T8 | 勝敗の記録と最終評価の符号の食い違い(§1.1、7 局〈束に無い数〉) | H6 | ― | ― | 無し(現行の分母は勝敗ラベルを使う) | **拾えていない**(1 席のみ) |
| T9 | 負け局の 3 型(残り秒・手数、§9.1 remainingSec) | H1 | ― | ― | 無し(timeUpLoss 1 局と aheadLoss を別々に見る) | **拾えていない**(1 席のみ) |
| T10 | 相手の応手と読み筋の一致(§8.2 の和 138/401〈束に無い数〉) | H7 | 指標⑥で言及 | ― | 無し | **拾えていない** |
| T11 | materialLook の反証(107/23/11〈束に無い数〉) | H3 | ― | ― | 無し | **拾えていない**(1 席のみ) |
| T12 | 取り返し「同〜」の連続で段階的に下がる(§2、37 行〈束に無い数〉) | H8 | ― | ― | 無し | **拾えていない**(1 席のみ) |
| T13 | 現行条件 moveCheck に差なし(§3.1 1/13 vs 1/17) | H10 | ― | ― | 現行条件そのものへの観測 | **拾えていない**(1 席のみ) |
| T14 | 戦型: 署名群(案)・rookMark(§11・§9.2 27/78.5) | H9(群別 1 勝 3 敗〈束に無い数〉・own=false 4 局。明確な差なし・盲検候補) | §7(群は見えるが未承認・判断材料不足) | §7(§11 が無い・判断材料不足) | 人間の決定: 3 群の再集計は可、顧客向け分類にはしない。表には無い | 現行の線と同じ結論(差は確認できない) |
| T15 | 時間の長短を処方にしない(0〜1 秒が最も崩れにくい 22/531) | H13 | §6(長考を減らす・早く指す は不可) | §6(H1 を行動にしない) | M3・M8(否定型、落ちた)、本編観測③ | 拾われている(否定型) |

### 3.2 6 項目の数

| 項目 | 数 | 中身 |
|---|---|---|
| 共通して出た仮説(3 席) | **3**(T1・T2・T3) | いずれも本編の観測 3 つと同じ数が根拠。T15(時間の長短を処方にしない)も 3 席が同じ向き |
| 2 席が出した仮説 | **3**(T4・T5・T6) | T7 も A・B |
| 1 席だけが出した仮説 | **6**(T8〜T13、すべて席 A) | 5 つは束に無い数(席が表を拾って数えた)を根拠にしている |
| 顧客の自己申告(普段指さない戦型)に関係する仮説 | **1 主題**(T14)、3 席とも「明確な差は確認できない/判断材料不足」 | A だけが群別の数を出した(束に無い数)。C は §11 が届いていない |
| 現行ルートで拾えていない仮説 | **7**(T6 の一部、T8・T9・T10・T11・T12・T13)+ 行動の型 2 つ(T2 の「打つ手」の行動、T3 の「優勢後の時系列」) | T8〜T13 は席 A のみ。新しい = 正しいではない |
| 後から機械検証できた仮説 | **6 本を契約に載せた**(§4)。検証(次の 25 局)はまだ | 今回の 25 局内の反証で 6 本とも `weakened` |
| 検証によって棄却された仮説 | **0**(測る前) | ― |

### 3.3 実験席の読み(結論ではない。Phase 2 ①④ の設計の入力)

- 3 席が共通して出したのは、**現行の本編が既に観測として出している 3 つの数**(優勢後の負け・打つ手・長考と崩れ)であり、現行ルートの観測の選び方は 3 つの LLM の独立の読みと一致した。行動まで一致したのは T1(C の行動 = M5)。
- **現行ルートに無い仮説は席 A に集中**し、その多くは席が束の表を横に拾って作った数(束に無い数)を根拠にしている。その数のうち 2 つは誤っていた。**「顧客固有の可能性」を LLM が見つけるには、席に数え直させるのではなく、道具側にその集計(最終評価の符号と結果の一致、残り秒の分布、応手一致の和、materialLook の和、「同〜」の率)を足す**のが筋(Phase 2 の入力)。
- 戦型は 3 席とも結論を出せなかった。束 §11 に定義の中身が無かったことが原因の一つ(§1.5)。実験 2(§6)で扱う。

## 4. 手順 5 ― 契約 hypothesis.v0.3 への載せ替え

`scripts/playtest/records/experiment-llm-25/` に 6 本(顧客 `p5`、組「3 分」、25 局、scope `this_user`、knowledge `discovered`/`draft`)。数は束(= 道具の出力)にあるものだけ。席の文は数の出どころにしていない(`provenance.excludedInputs` に SEAT_A/B/C と現行ルートの出力を明記)。予測は 2026-09-29 に書いた(測る前)。検査: `npx tsx scripts/playtest/hypothesisCheck.ts scripts/playtest/records/experiment-llm-25/*.json --today 2026-09-29` → **6 本とも schema・H-1〜H-8 すべて ok、exit 0**。

| ファイル | 主題 | 席 | 予測(次の 25 局・同じ持ち時間) | 反証の結果 |
|---|---|---|---|---|
| `E-001-time-afterLongThink.json` | T1 長考直後の手の崩れ 11/44 vs 1 秒以下 22/531 | A-H4・B-H1/H2・C-H2 | afterLongThinkAny の崩れ率 − bySpent[0] の崩れ率 > 0(n ≥ 30・≥ 300) | weakened(選択効果: 長考のうち分かれ道 30/56。分母 44) |
| `E-002-fork-tagCounts.json` | T2 分かれ道の印 打つ 54/33・取る 19/32・引く 5/12 | A-H2・B-H5・C-H3 | top1 drop − actual drop > 0、かつ capture の差 < 0(totalCount ≥ 50) | weakened(sacrifice 41/44・kingMove 7/8 は差なし。基準率なし。取り合いの局面の反映) |
| `E-003-time-rookMark.json` | T14(b) 飛車の印 own=false 4 局 27/78.5 vs 16.5/67.5 vs 14/49 | A-H9(b) | own=false の medianMidSec − own=true/opp=false の medianMidSec > 0(games ≥ 3・≥ 5) | weakened(4 局。相手の飛車の位置の効果と分けられない) |
| `E-004-prior-moveCheck.json` | T13 現行条件に差なし 1/13 vs 1/17 | A-H10 | 条件に当たる手の崩れ率 − 当たらない手の崩れ率 ≤ 0(n ≥ 10・≥ 10) | weakened(13・17 は小さい) |
| `E-006-fork-shallowVisible.json` | T5 浅い読みで見える分かれ道 103/404 | A-H11・B-H4 | totalCount/totalForkCount ≥ 20%(totalForkCount ≥ 200) | weakened(定義は候補 5 本に無ければ拾う) |
| `E-007-time-forkAmongLongThink.json` | T6 長考のうち分かれ道 30/56、側の逆 4/30 | A-H5・B-H2 | forkFraction ≥ 40%(分母 ≥ 30) | weakened(結合できた長考だけ。分母 30・3) |

**載せられない仮説と理由**(契約の H-1「引いた数が観測項目に実在すること」を満たせない = 道具がその数を出していない):

| 仮説 | 理由 | 道具側に要るもの(Phase 2 の入力) |
|---|---|---|
| A-H1 負け局の 3 型 | 型の境目(残り秒・手数)を席が置いた。道具の集計に無い | 負け局ごとの remainingSec・total・最終評価の符号の表と、境目の人間承認 |
| A-H3 materialLook の反証 107/23/11 | 25 局の和は席が足した(束に無い数) | read summary の全局合算 |
| A-H6 勝敗と最終評価の符号の食い違い 7 局 | 席が §1.1 を読んで数えた | 局ごとの「最終評価の符号 × result」の集計と、相手の時計(記録に無い) |
| A-H7 相手の応手一致 138/401 | 席が足した | read summary の全局合算 |
| A-H8 「同〜」37 行・段階的な下がり | 席が数えた(sameBest の数は誤り 8→10)。全手での基準率も無い | events の `played` が「同」で始まる行の集計と、全手での率 |
| A-H12 / B-H6 逃げ道 7/7 | 7 行の比較は席が数えた。急落候補でない手の逃げ道(基準率)が無い | 全手の escRoot/escEnd |
| A-H9(a) 署名群(案)ごとの勝敗 1 勝 3 敗 | 群は未承認の案(§11 `proposal`)で、同じ 25 局で作られた(循環)。数も席が拾った | 実験 2 と知識レーンの再走査(指示書 §13.4) |
| B-H3 の時系列(+300 到達 → 最初の fork → 最初の崩れ) | 道具に無い結合 | 局ごとの時系列の集計 |
| C-H2 の行動(一呼吸) | 数は載せられる(E-001 と同じ)が、行動は現行 M5 と同じで新規でない | ― |
| C-H3 の行動(打つ手の確認) | 数は E-002 に載せた。行動は原則 4・5 との緊張で採用候補にしない(§2.3) | 基準率 |

## 5. 手順 6 ― 司令塔への報告

報告 1(2026-09-29、手順 1 完了)→ 司令塔が実物と照合(sha256 一致・名前 0 件・混入 0)。報告 2(手順 2〜5 完了、この §2〜§4)を送付。採否は司令塔の承認系統。

## 6. 実験 2(H7)― 棋譜の流れから戦型を認識できるか(指示書 §13、2026-09-29 昼)

### 6.1 手順 1 ― `request2.md` を作った(抽出だけ)

| ファイル | sha256 | 大きさ | 中身 |
|---|---|---|---|
| `scripts/playtest/out/c5/experiment-llm-25/request2.md` | `ea0f55072ef6c1e0a888f46898223da1df7757dd074224ea2c0fcb148e091da9` | 34,570 バイト・184 行 | 問い(§13.1 の原文)+ 守ること + 出力の形(§13.3 の 6 欄 + 側の欄)+ 材料 1: 25 局の指し手列(`sfens.json` の `moves`、実験 1 の束 §5 と同じ。本人の側と、後手局は元の棋譜の手数のままの注)+ 材料 2: 戦型定義 114 件(`data/openings` 3 + `data/drafts/2026-09-25-knowledge/openings` 111 の `id`・`name`・`side`・`recognition_pattern`・`review_status` をそのまま。pattern 長の分布 0 手 7 / 1 手 34 / 2 手 37 / 3 手 28 / 4 手 6 / 5 手 2 = 指示書 §13.2 の実測と一致) |

**座標の注**(request2.md に明記): 定義の座標は「本人 = 先手」の向き(self は先手の絶対座標、opponent は後手の絶対座標。`docs/DATA_MODEL.md` の座標規約)。本人が後手の 13 局は盤を 180 度回してから照合するよう席に指示した(根拠の手数と USI は元の棋譜のまま)。`sfens.json` の `side` は sente/gote なので、表示は「本人 = 先手(sente)/後手(gote)」に写した。

**入れていないもの**: `opening_recognition.json` の `rows`・`proposal`(機械の認識結果と署名の案。席の読みを寄せないため)。突き合わせは実験席が後から。

### 6.2 席に掛け、回答を原文のまま保存した

| 席 | 掛け方 | 原本 | sha256 | 保存先 | 扱い |
|---|---|---|---|---|---|
| A2(Claude) | 実験席が subagent(新規会話)を起こし `request2.md` を全行読ませた。他のファイル・コード実行・ウェブ無し | `seat_A2_claude_raw.md`(74 行・51,025 バイト) | `eb1ecc7ee6189313e61db6152cea8bebfea01ed9a60674ccce13e1fb78a98570` | [SEAT2_A](EXPERIMENT_LLM_DISCOVERY_25GAMES_SEAT2_A.md) | 正式な席 |
| B2(GPT) | 人間がブラウザで本文貼り付け(司令塔が中継) | `seat_B2_gpt_raw.md`(141 行・13,971 バイト) | `f21ef9f4980021b5cf8350070f503d2987d5a38bca25cb19f88aa61b5c290cfb` | [SEAT2_B](EXPERIMENT_LLM_DISCOVERY_25GAMES_SEAT2_B.md) | **保留**(人間の決定 2026-09-29 昼: 回答自身が「本編・『数の出どころ』付録も確認した」と書き、request2.md にはそれが無い → 独立性に疑いあり。表と指摘は保存するが、比較の正式な 1 席にしない・3 席一致の数に入れない) |
| C2(Gemini) | 同上(新規会話) | `seat_C2_gemini_raw.md`(59 行・9,676 バイト) | `ef893090f388433ab755083bed362478294150d317e6da4a073b196ce8cd9693` | [SEAT2_C](EXPERIMENT_LLM_DISCOVERY_25GAMES_SEAT2_C.md) | 正式な席 |

**入力到達の欄**(実験 1 §2.1 と同じ形。C2 は前回 §11 が届かなかった席なので、材料 2 の定義を引用しているかで判定):

| 席 | 材料 2(定義)の id を引用しているか | 判定 |
|---|---|---|
| A2 | 50 行すべてで id を引き、114 件の内訳(相手側 29 件・pattern 無し 7 件)にも触れている | 届いた |
| B2 | 50 行で id を引き、pattern 長の分布(1 手 34・2 手 37)を引いている | 届いた(ただし独立性は保留) |
| C2 | 50 行で id を引いている(うち 5 行は side=self の定義を相手側に当て「(side=self)」と注記) | **届いた**(実験 1 と違い、末尾の材料まで読めている) |

### 6.3 突き合わせ ― 席の主張を機械で検査し、機械の rows と局ごとに比べた

**検査器**(scratchpad `exp2_check.py`、盤を再生する python): 定義の座標は「本人=先手」の向きとし、定義の side の色が実際と違う局は 180 度回して照合。判定 B = 「pattern の全駒(種類一致・未成)が**同時に**その側の駒として盤上の to に居る時点がある」。判定 A = 「その側の駒が to に**着いた手が 1 回以上ある**」(B より緩い)。**校正**: 判定 B は機械の rows(`opening_recognition.json` の completed、253 件)と **253/253 で一致、不一致 0**(機械の detector は order_hint を読まず「盤の占有 + 動いた証拠」で判定 ― `openingDetector.ts` の明記どおり)。判定 A は 88 件多い。

| 席 | 引用した手(手数と USI)の実在 | 「完全」と主張した id | うち判定 B(機械と同じ)で成立 | うち判定 A で成立 | 判定 A でも不成立 | 不成立の主因 |
|---|---|---|---|---|---|---|
| A2 | 384 / 384 | 160 | 134 | 159 | 0(部分 143 のうち判定 B で実は完全 7・何も無し 4) | 「着いた手が 1 回ある」を完全と読んだ(同時に盤上でない 25 件)。180 度回転は正しい |
| B2(保留) | 283 / 283 | 217 | 145 | 183 | 31 | **飛と角の取り違え**(USI に駒の文字が無い)が 31 件中 28 件。180 度回転は正しい |
| C2 | 98 / 98 | 50(1 行 1 id) | 30 | 48 | 1 | 5 行で side=self の定義を相手側に当てた(注記あり) |

**局ごとの表**(機械 = `rows` の completed。判定 = 席の「完全」の id と機械の completed の関係: 一致(共通の id がある)/ 席と機械が別の id / 席だけ / 機械だけ / どちらも未認識。**B2 は保留列**):

| 局 | 側 | 機械(completed) | 群(案) | 席 A2(完全) | 判定 A2 | 席 C2 | 判定 C2 | A2∩C2∩機械 | 席 B2(保留) | 判定 B2(保留) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 本人 | onikoroshi, douke_yagura, kakutoufu, migigyoku, ufo_gin, yagura_37gin | 多数の核 | douke_yagura, migigyoku, yagura_37kei | 一致 | chousoku_37gin | 席と機械が別の id | ― | chousoku_37gin, douke_yagura, kakutoufu, migigyoku, onikoroshi, ufo_gin, yagura_37gin | 一致 |
| 1 | 相手 | sansan_kaku_senpo, yokofudori_33kaku, rokusuji_kuraidori, yonyonfu_pacman, yokofudori_85hi |  | sansan_kaku_senpo, yokofudori_33kaku | 一致 | rokusuji_kuraidori | 一致 | ― | rokusuji_kuraidori, yokofudori_44kaku, yokofudori_45kaku, yonyonfu_pacman | 一致 |
| 2 | 本人 | douke_yagura, migigyoku, koshikakegin | 多数の核 | douke_yagura, koshikakegin, migigyoku, yagura_37kei | 一致 | douke_yagura | 一致 | douke_yagura | douke_yagura, kintachi, koshikakegin, migigyoku, ponpon_kei | 一致 |
| 2 | 相手 | gokigen_nakabisha, sansan_kaku_senpo, yokofudori_33kaku, rokusuji_kuraidori, yonyonfu_pacman |  | gokigen_nakabisha, sansan_kaku_senpo, yagura_ryu_nakabisha | 一致 | gokigen_nakabisha | 一致 | gokigen_nakabisha | rokusuji_kuraidori, yonyonfu_pacman | 一致 |
| 3 | 本人 | yagura_37kei, douke_yagura, migigyoku, koshikakegin | 多数の核 | douke_yagura, migigyoku, yagura_37kei | 一致 | koshikakegin | 一致 | ― | koshikakegin, migigyoku | 一致 |
| 3 | 相手 | sansan_kaku_senpo, yokofudori_33kaku, shikenbisha_opponent, rokusuji_kuraidori, yonyonfu_pacman, yokofudori_33kei |  | rokusuji_kuraidori, sansan_kaku_senpo, shikenbisha_opponent, yonyonfu_pacman | 一致 | ittezon_kakugawari | 席と機械が別の id | ― | direct_mukaibisha, mukaibisha_opponent, rokusuji_kuraidori, yokofudori_33kei, yokofudori_45kaku, yonyonfu_pacman | 一致 |
| 4 | 本人 | kakugawari_koshikakegin, gosuji_kuraidori_nakabisha, eichanryu_nakabisha, fuusha, nakabisha_self, koshikakegin, migigyoku, kakutoufu | それ以外 | eichanryu_nakabisha, fuusha, genshi_nakabisha, gosuji_kuraidori_nakabisha, migigyoku, nakabisha_self | 一致 | eichanryu_nakabisha | 一致 | eichanryu_nakabisha | kakutoufu, koshikakegin, migigyoku | 一致 |
| 4 | 相手 | (なし) |  | (なし) | どちらも未認識 | kakutoufu | 席だけ | ― | (なし) | どちらも未認識 |
| 5 | 本人 | yagura_37kei, douke_yagura, onikoroshi, kamereon_senpo, migigyoku, koshikakegin | 多数の核 | douke_yagura, kamereon_senpo, migigyoku, yagura_37kei | 一致 | kamereon_senpo | 一致 | kamereon_senpo | kamereon_senpo, koshikakegin, migigyoku, onikoroshi, ponpon_kei | 一致 |
| 5 | 相手 | yonenaga_kyusen_yagura, sansan_kaku_senpo, yokofudori_33kaku, rokusuji_kuraidori, yonyonfu_pacman, shikenbisha_opponent |  | rokusuji_kuraidori, sansan_kaku_senpo, shikenbisha_opponent, yonenaga_kyusen_yagura, yonyonfu_pacman | 一致 | yonenaga_kyusen_yagura | 一致 | yonenaga_kyusen_yagura | rokusuji_kuraidori, yonenaga_kyusen_yagura, yonyonfu_pacman | 一致 |
| 6 | 本人 | onikoroshi, kamereon_senpo, kanazawaryu, mukaibisha, migigyoku, koshikakegin | 多数の核 | kamereon_senpo, kanazawaryu, migigyoku, mukaibisha | 一致 | gangi_senpou | 席と機械が別の id | ― | gangi_senpou, kamereon_senpo, kintachi, koshikakegin, migigyoku, onikoroshi | 一致 |
| 6 | 相手 | sansan_kaku_senpo, yokofudori_33kaku, yokofudori_33kei |  | sansan_kaku_senpo | 一致 | ai_yokofudori | 席と機械が別の id | ― | ai_yokofudori, shikenbisha_opponent, yokofudori_33kei, yokofudori_85hi | 一致 |
| 7 | 本人 | henachoko_kyusen, onikoroshi, douke_yagura, kamereon_senpo, migigyoku | 多数の核 | douke_yagura, kamereon_senpo, migigyoku, yagura_37kei | 一致 | douke_yagura | 一致 | douke_yagura | douke_yagura, kamereon_senpo, migigyoku, onikoroshi | 一致 |
| 7 | 相手 | sansan_kaku_senpo, yokofudori_33kaku, rokusuji_kuraidori, yonyonfu_pacman, nitemme_32hi, sankenbisha_opponent, shikenbisha_opponent |  | nitemme_32hi, rokusuji_kuraidori, sankenbisha_opponent, sansan_kaku_senpo, yonyonfu_pacman | 一致 | yagura_35fu_hayajikake | 席と機械が別の id | ― | rokusuji_kuraidori, shikenbisha_opponent, yonyonfu_pacman | 一致 |
| 8 | 本人 | yagura_37kei, douke_yagura, onikoroshi, migigyoku, koshikakegin | 多数の核 | douke_yagura, kamereon_senpo, migigyoku, yagura_37kei | 一致 | onikoroshi | 一致 | ― | hikikaku, koshikakegin, migigyoku, onikoroshi, ponpon_kei, torisashi | 一致 |
| 8 | 相手 | sansan_kaku_senpo, yokofudori_33kaku, rokusuji_kuraidori, yonyonfu_pacman, shikenbisha_opponent |  | rokusuji_kuraidori, sansan_kaku_senpo, shikenbisha_opponent, yonenaga_kyusen_yagura, yonyonfu_pacman | 一致 | yonenaga_kyusen_yagura | 席と機械が別の id | ― | rokusuji_kuraidori, yonenaga_kyusen_yagura, yonyonfu_pacman | 一致 |
| 9 | 本人 | (なし) | 署名なし | hineribisha, kakugawari, tatefudori, yagura_senpo | 席だけ | yagura_senpo | 席だけ | ― | yagura_senpo | 席だけ |
| 9 | 相手 | yokofudori_44kaku, rokusuji_kuraidori, yonyonfu_pacman |  | (なし) | 機械だけ | rokusuji_kuraidori | 一致 | ― | rokusuji_kuraidori, yonyonfu_pacman | 一致 |
| 10 | 本人 | yokofudori | 署名なし | aigakari | 席と機械が別の id | aigakari | 席と機械が別の id | ― | mukaibisha | 席と機械が別の id |
| 10 | 相手 | rokusuji_kuraidori, yonyonfu_pacman, yokofudori_33kei |  | (なし) | 機械だけ | rokusuji_kuraidori | 一致 | ― | rokusuji_kuraidori, yokofudori_33kei, yonyonfu_pacman | 一致 |
| 11 | 本人 | yagura_37kei, douke_yagura, onikoroshi, migigyoku | 多数の核 | douke_yagura, migigyoku, yagura_37kei | 一致 | onikoroshi | 一致 | ― | migigyoku, onikoroshi | 一致 |
| 11 | 相手 | yonenaga_kyusen_yagura, rokusuji_kuraidori, yonyonfu_pacman, sansan_kaku_senpo, yokofudori_33kaku, shikenbisha_opponent |  | rokusuji_kuraidori, sansan_kaku_senpo, shikenbisha_opponent, yonenaga_kyusen_yagura, yonyonfu_pacman | 一致 | yonenaga_kyusen_yagura | 一致 | yonenaga_kyusen_yagura | direct_mukaibisha, mukaibisha_opponent, rokusuji_kuraidori, yokofudori_44kaku, yonenaga_kyusen_yagura, yonyonfu_pacman | 一致 |
| 12 | 本人 | yagura_37kei, douke_yagura, onikoroshi, kamereon_senpo, kakugawari_koshikakegin, migigyoku, koshikakegin | 多数の核 | douke_yagura, migigyoku, yagura_37kei | 一致 | kakugawari_koshikakegin | 一致 | ― | kamereon_senpo, koshikakegin, migigyoku, onikoroshi, youryuu_shikenbisha | 一致 |
| 12 | 相手 | yonenaga_kyusen_yagura, rokusuji_kuraidori, yonyonfu_pacman, sansan_kaku_senpo, yokofudori_33kaku, shikenbisha_opponent |  | rokusuji_kuraidori, sansan_kaku_senpo, shikenbisha_opponent, yonenaga_kyusen_yagura, yonyonfu_pacman | 一致 | yonenaga_kyusen_yagura | 一致 | yonenaga_kyusen_yagura | rokusuji_kuraidori, yonenaga_kyusen_yagura, yonyonfu_pacman | 一致 |
| 13 | 本人 | ninja_gin, yagura_37gin, wakisystem, kusarigamagin, migi_shikenbisha | それ以外 | yagura_37gin, yagura_bogin | 一致 | aigakari | 席と機械が別の id | ― | kusarigamagin, migi_shikenbisha, ponpon_kei, sujichigai_kaku, wakisystem, yagura_37gin, yagura_bogin | 一致 |
| 13 | 相手 | akutsu_kyusen_yagura, sansan_kaku_senpo, yokofudori_33kaku, yokofudori_33kei, yokofudori_44kaku |  | sansan_kaku_senpo | 一致 | sansan_kaku_senpo | 一致 | sansan_kaku_senpo | yokofudori_33kei, yokofudori_44kaku | 一致 |
| 14 | 本人 | yagura_37kei, douke_yagura, onikoroshi, migigyoku | 多数の核 | douke_yagura, migigyoku, yagura_37kei | 一致 | onikoroshi | 一致 | ― | migigyoku, onikoroshi, ponpon_kei | 一致 |
| 14 | 相手 | yonenaga_kyusen_yagura, sansan_kaku_senpo, yokofudori_33kaku, rokusuji_kuraidori, yonyonfu_pacman, shikenbisha_opponent |  | rokusuji_kuraidori, sansan_kaku_senpo, shikenbisha_opponent, yonenaga_kyusen_yagura, yonyonfu_pacman | 一致 | yonenaga_kyusen_yagura | 一致 | yonenaga_kyusen_yagura | rokusuji_kuraidori, yonenaga_kyusen_yagura, yonyonfu_pacman | 一致 |
| 15 | 本人 | douke_yagura, gangi_senpou, kamereon_senpo, migigyoku, kakutoufu, yagura_37gin | 多数の核 | douke_yagura, kamereon_senpo, migigyoku, yagura_37kei | 一致 | eishunryu | 席と機械が別の id | ― | douke_yagura, eishunryu, gangi_senpou, kakutoufu, kamereon_senpo, kanikanigin, migigyoku, mukaibisha, yagura_37gin | 一致 |
| 15 | 相手 | rokusuji_kuraidori, yonyonfu_pacman, sansan_kaku_senpo, yokofudori_33kaku, yokofudori_33kei |  | rokusuji_kuraidori, sansan_kaku_senpo, yonyonfu_pacman | 一致 | rokusuji_kuraidori | 一致 | rokusuji_kuraidori | rokusuji_kuraidori, shikenbisha_opponent, yokofudori_33kei, yonyonfu_pacman | 一致 |
| 16 | 本人 | onikoroshi, douke_yagura, migigyoku, kakutoufu, koshikakegin, wakisystem | 多数の核 | aigakari, douke_yagura, migigyoku, yagura_37kei | 一致 | aigakari | 席と機械が別の id | ― | douke_yagura, henachoko_kyusen, kakutoufu, koshikakegin, migigyoku, onikoroshi, ponpon_kei | 一致 |
| 16 | 相手 | yonenaga_kyusen_yagura, rokusuji_kuraidori, yonyonfu_pacman, yokofudori_33kei |  | yonenaga_kyusen_yagura | 一致 | yonenaga_kyusen_yagura | 一致 | yonenaga_kyusen_yagura | rokusuji_kuraidori, shikenbisha_opponent, yokofudori_33kei, yonenaga_kyusen_yagura, yonyonfu_pacman | 一致 |
| 17 | 本人 | kakugawari_koshikakegin, gosuji_kuraidori_nakabisha, eichanryu_nakabisha, fuusha, nakabisha_self, koshikakegin, migigyoku, yagura_37gin | それ以外 | eichanryu_nakabisha, fuusha, genshi_nakabisha, gosuji_kuraidori_nakabisha, migigyoku, nakabisha_self | 一致 | kanikanigin | 席と機械が別の id | ― | chousoku_37gin, kanikanigin, koshikakegin, migigyoku, yagura_37gin | 一致 |
| 17 | 相手 | yonenaga_kyusen_yagura, yokofudori_44kaku, rokusuji_kuraidori, yonyonfu_pacman |  | yonenaga_kyusen_yagura | 一致 | yonenaga_kyusen_yagura | 一致 | yonenaga_kyusen_yagura | rokusuji_kuraidori, yonenaga_kyusen_yagura, yonyonfu_pacman | 一致 |
| 18 | 本人 | kakutoufu, koshikakegin, yagura_37gin | 署名なし | aigakari, koshikakegin | 一致 | aigakari | 席と機械が別の id | ― | douke_yagura, kakutoufu, koshikakegin, onikoroshi, yagura_37gin | 一致 |
| 18 | 相手 | ai_yokofudori, yokofudori_85hi, yokofudori_33kei |  | ai_yokofudori, yokofudori_85hi | 一致 | ai_yokofudori | 一致 | ai_yokofudori | ittezon_kakugawari, shikenbisha_opponent, yokofudori_33kei | 一致 |
| 19 | 本人 | kakugawari_koshikakegin, yagura_37kei, douke_yagura, koshikakegin, migigyoku, kakutoufu, yagura_37gin | 多数の核 | douke_yagura, henachoko_kyusen, kakugawari_koshikakegin, kamereon_senpo, koshikakegin, migigyoku, yagura_37kei | 一致 | henachoko_kyusen | 席と機械が別の id | ― | henachoko_kyusen, kakutoufu, kamereon_senpo, koshikakegin, migigyoku, ponpon_kei, sujichigai_kaku, wakisystem, yagura_37gin | 一致 |
| 19 | 相手 | gokigen_nakabisha, sansan_kaku_senpo, yokofudori_33kaku, rokusuji_kuraidori, yonyonfu_pacman, shikenbisha_opponent, yokofudori_33kei |  | rokusuji_kuraidori, sansan_kaku_senpo, yonyonfu_pacman | 一致 | gokigen_nakabisha | 一致 | ― | rokusuji_kuraidori, shikenbisha_opponent, yokofudori_33kei, yonyonfu_pacman | 一致 |
| 20 | 本人 | onikoroshi, hidarimino_senpo, hayakurigin, naname_bogin_self, migigyoku, kakutoufu, mukaibisha, koshikakegin | 多数の核 | douke_yagura, koshikakegin, migigyoku, mukaibisha | 一致 | genshi_bogin | 席と機械が別の id | ― | aigakari_bogin, boh_gin_self, genshi_bogin, hayakurigin, kakutoufu, koshikakegin, migigyoku, naname_bogin_self, onikoroshi | 一致 |
| 20 | 相手 | yonenaga_kyusen_yagura, yokofudori_45kaku, yokofudori_85hi |  | yokofudori_45kaku | 一致 | kakugawari | 席と機械が別の id | ― | yokofudori_44kaku, yokofudori_45kaku | 一致 |
| 21 | 本人 | yagura_37kei, douke_yagura, migigyoku | 多数の核 | douke_yagura, migigyoku, yagura_37kei | 一致 | migigyoku | 一致 | migigyoku | migigyoku | 一致 |
| 21 | 相手 | sansan_kaku_senpo, yokofudori_33kaku, shikenbisha_opponent, direct_mukaibisha, mukaibisha_opponent, rokusuji_kuraidori, yonyonfu_pacman |  | direct_mukaibisha, mukaibisha_opponent, rokusuji_kuraidori, sansan_kaku_senpo, shikenbisha_opponent, yonyonfu_pacman | 一致 | direct_mukaibisha | 一致 | direct_mukaibisha | rokusuji_kuraidori, yonyonfu_pacman | 一致 |
| 22 | 本人 | onikoroshi, douke_yagura, kamereon_senpo, kakugawari_koshikakegin, kakutoufu, koshikakegin, migi_shikenbisha, hikikaku, torisashi | 多数の核 | douke_yagura, koshikakegin, yagura_37kei | 一致 | eishunryu | 席と機械が別の id | ― | douke_yagura, eishunryu, gangi_senpou, henachoko_kyusen, hidarigyoku, kakutoufu, kamereon_senpo, koshikakegin, mukaibisha, onikoroshi | 一致 |
| 22 | 相手 | rokusuji_kuraidori, yonyonfu_pacman, yokofudori_85hi |  | rokusuji_kuraidori, yonyonfu_pacman | 一致 | onikoroshi | 席と機械が別の id | ― | rokusuji_kuraidori, shikenbisha_opponent, yonyonfu_pacman | 一致 |
| 23 | 本人 | douke_yagura, hayaishida, sankenbisha | 多数の核 | douke_yagura, yagura_37kei | 一致 | douke_yagura | 一致 | douke_yagura | douke_yagura | 一致 |
| 23 | 相手 | sansan_kaku_senpo, yokofudori_33kaku, nitemme_32hi, sankenbisha_opponent, rokusuji_kuraidori, yonyonfu_pacman, shikenbisha_opponent, yokofudori_33kei |  | nitemme_32hi, rokusuji_kuraidori, sankenbisha_opponent, sansan_kaku_senpo, shikenbisha_opponent, yonyonfu_pacman | 一致 | nitemme_32hi | 一致 | nitemme_32hi | rokusuji_kuraidori, yokofudori_33kei, yonyonfu_pacman | 一致 |
| 24 | 本人 | hayakurigin, naname_bogin_self, kakutoufu, migigyoku, yagura_37gin | それ以外 | eishunryu, yagura_senpo | 席と機械が別の id | eishunryu | 席と機械が別の id | ― | chousoku_37gin, eishunryu, hayakurigin, henachoko_kyusen, kakutoufu, kanikanigin, migigyoku, naname_bogin_self, onikoroshi, yagura_37gin, yagura_senpo, yamada_joseki | 一致 |
| 24 | 相手 | yokofudori_33kei, rokusuji_kuraidori, yonyonfu_pacman |  | (なし) | 機械だけ | onikoroshi | 席と機械が別の id | ― | direct_mukaibisha, mukaibisha_opponent, rokusuji_kuraidori, sansan_kaku_senpo, yokofudori_33kaku, yokofudori_33kei, yonyonfu_pacman | 一致 |
| 25 | 本人 | yagura_37kei, douke_yagura, yagura_nakabisha, onikoroshi, migigyoku, kakutoufu, koshikakegin, yagura_37gin, wakisystem | 多数の核 | douke_yagura, eishunryu, kakutoufu, migigyoku, yagura_37kei | 一致 | eishunryu | 席と機械が別の id | ― | eishunryu, hikikaku, kakutoufu, kanikanigin, koshikakegin, migigyoku, onikoroshi, torisashi, ureshino, yagura_37gin | 一致 |
| 25 | 相手 | yonenaga_kyusen_yagura, rokusuji_kuraidori, yonyonfu_pacman, sansan_kaku_senpo, yokofudori_33kaku, shikenbisha_opponent, direct_mukaibisha, mukaibisha_opponent, yokofudori_44kaku |  | rokusuji_kuraidori, sansan_kaku_senpo, shikenbisha_opponent, yonyonfu_pacman | 一致 | direct_mukaibisha | 一致 | ― | rokusuji_kuraidori, yonyonfu_pacman | 一致 |

**数**(50 行 = 25 局 × 本人/相手):

| 判定 | A2 | C2 | B2(保留) |
|---|---|---|---|
| 一致(共通の id あり) | 43 | 28 | 47 |
| 席と機械が別の id | 2 | 20 | 1 |
| 席だけ | 1(局 9 本人) | 2(局 4 相手・局 9 本人) | 1(局 9 本人) |
| 機械だけ | 3(局 9 相手・局 10 相手・局 24 相手) | 0 | 0 |
| どちらも未認識 | 1(局 4 相手) | 0 | 1(局 4 相手) |

- A2 と C2(正式な 2 席)が同じ id を挙げ、機械にもある行: **18 / 50**。A2 と C2 が同じ id を挙げた行: 26 / 50。**2 席の一致は証拠ではない**(再検証の価値の印)。
- 機械が空(completed 無し)の行は 2(局 4 相手・局 9 本人)。局 4 相手は A2・B2 も「なし」(どちらも未認識)、C2 は side=self の kakutoufu を当てた。局 9 本人は 3 席とも yagura_senpo(A2 は hineribisha・tatefudori・kakugawari も)を挙げ、機械は無し(定義 yagura_senpo は 3 手で、機械の「同時に盤上」では 29 手目の銀→7g の時点で 7f の歩が動いている等で不成立 ― 検査器の判定 B も不成立、A は成立)。
- C2 の「別の id」20 行の多くは、C2 が 1 行 1 id で「浅い一致」を避けて手順の長い定義(eishunryu・aigakari・kanikanigin 等)を選び、機械は 1〜2 手の定義を complete にしているため。機械と席の**判定の基準の違い**であって、局面の読みの違いではない。
- 群(案)との関係: 「それ以外」4 局(4・13・17・24)のうち、局 4・17 は A2 が nakabisha_self・gosuji_kuraidori_nakabisha・eichanryu_nakabisha を機械と同じく完全にした(一致)。局 13 は A2 が yagura_37gin・yagura_bogin、機械は kusarigamagin・migi_shikenbisha・ninja_gin・wakisystem・yagura_37gin(一致は yagura_37gin のみ)。局 24 は A2 が eishunryu・yagura_senpo、機械は hayakurigin・naname_bogin_self 等で**別の id**。署名なし 3 局(9・10・18)は、局 9 本人が席だけ、局 10 本人が別の id(A2 aigakari vs 機械 yokofudori)。**群(案)を席の読みで裏づけたとは言えない**。

### 6.4 「定義の側で何が足りないか」― 3 席分を 1 本に(名前なし・条件の形)

[EXPERIMENT_LLM_DISCOVERY_25GAMES_EXP2_DEF_GAPS.md](EXPERIMENT_LLM_DISCOVERY_25GAMES_EXP2_DEF_GAPS.md)(G1〜G17、席の記号つき、実例つき)。3 席が独立に言ったのは G1(1 手 pattern の重なり)・G2(手数の窓が無い)。A2 だけが G4(取る手で一致)・G6(経由と停止の区別)・G7(前提の駒の位置)・G9〜G12・G15・G16 を実例つきで挙げた。**G1〜G4 は機械の判定にもそのまま当てはまる**(機械も同じ条件で completed にしている)。「定義に無い名前の候補」: A2・B2 は 50 行すべて名前なし、C2 は 50 行すべてに 5 種の名前(角換わり・矢倉・相掛かり・横歩取り・ゴキゲン中飛車)。分類・比較には使っていない。

### 6.5 実験席の読み(結論ではない。指示書 §13.4 の 2・3 への入力)

- 「棋譜の流れから戦型を認識できるか」への答え: **現行の 114 定義では、席も機械も「完全一致」を 1 局に多数出し、id を 1 つに絞れない**(A2 は 1 行あたり最大 7 id を完全、機械は最大 9)。原因は定義の側(G1〜G5)で、席の読みの弱さではない。席 A2 は 180 度回転・手数・USI の引用をすべて正しく行い(384/384)、機械と同じ判定でも 134/160 が成立した。
- 席が機械より多く見たもの: 「取る手での一致」「経由と停止」「角交換の経路」「飛先の歩交換の戻り」「本人=後手 9 局で繰り返す右側の順」「相手側の定義の薄さ」(G4・G6・G9〜G12)。これらは**定義を 3 手以上の流れへ深める条件の候補**として知識レーンへ(§13.4 の 2)。
- 席が機械より弱かったもの: 「同時に盤上」の条件を席は使わない(A2 の 25 件、C2 の 18 件、B2 の 38 件が判定 A のみ)。USI から駒の種類を取り違える(B2 28 件)。
- 顧客の関心(普段指さない戦型)への含意: 群(案)の 4 局のうち 2 局(4・17)は席と機械が同じ「中飛車系(下書き)」の id で一致、2 局(13・24)は別の id。**戦型別の再集計(§13.4 の 3)は、定義を深めた後の再走査を待つ**。顧客の文には出さない(§13.5)。


## 7. 3 席 LLM API ― 束 R1(render: packet + request → `seat_input.md`)の実装と実測(2026-09-30)

計画 [STEP_LLM_SEATS_R1_RENDER](STEP_LLM_SEATS_R1_RENDER_2026-09-30.md)(f2023c5、司令塔 GO)。上位 [PLAN_LLM_SEATS_API](PLAN_LLM_SEATS_API_2026-09-30.md)。**LLM は呼んでいない**(鍵は無い)。冊子・`deliver.ts`・packet を作る道具・schema・指示文には触っていない。

### 7.1 作ったもの

| 物 | 場所 | 中身 |
|---|---|---|
| lib | `scripts/playtest/lib/seatInput.ts` | `renderSeatInput`(抽出だけ。値は `JSON.stringify` の写し)、`numberInclusionProblems`(本文の data 行の数値トークンの多重集合 ⊆ packet + request の多重集合)、`dataLinesOf`(ファイルから data 行を抜く口)、`identifierProblems`(全部の文字列の値を歩き `@`・URL・絶対パス・`~`・禁止の語で止める。語はメッセージに出さない)、`INSTRUCTION_V1_SHA256`(3b09bec2…) |
| 試験 | `scripts/playtest/lib/seatInput.test.ts` | 24 本。最小の packet は隣の束(`observationPacket.test.ts`)と同じ形で、契約を通ることを先に見る |
| CLI | `scripts/playtest/seatInput.ts` | `--packet --request --instruction --run-id --out-dir [--forbid-file] [--instruction-sha]`。書いた後、ファイルから読み直して数の包含をもう一度(別の口)。止まれば書かず終了コード 1 |
| request | `scripts/playtest/out/c5/packet/observation-request.json`(gitignore) | 司令塔の指示どおり、記録に在る本人の言葉(人間が中継)を `customerQuestions[0].text` にそのまま、`via: relayed`、note に「人間が中継した本人の言葉。本人が書いた文字列そのものではない」。本人には聞いていない |

**計画からの変更**: 置き場は `scripts/playtest/llmSeats/` でなくリポジトリの慣例(lib / 隣の試験 / CLI)。`facts.moves` は局ごと 1 行(司令塔の指示。初回の実行で席が gameId + ply で手を引けるかを測ってから 1 手 1 行に切り替えるかを決める)。`lastKey` は先頭 60 字で切る(問いの全文が入っていたため)。「固定文に数字を含めない」の規則は成り立たなかった(欄名 `top1Side`・「第 1 候補」に数字が入る)ので、**固定文は data 行ではない(検査から除く)**に改め、試験は固定文の全行が data 行から除かれることを見る。

### 7.2 実装中に検査が捕まえたもの(直した)

- 持ち時間 180 を 1 行目と request の節の 2 か所に写していた → 数の包含が「180 が本文に 3 回、packet + request には 2 回」で赤。request の節は note だけにした。**同じ値を 2 か所に写すと写しではなくなる**(検査が設計どおりに働いた実例)。
- ファイルから読み直す口が「省いたもの」の固定文(`§0.3`・`v0.1` を含む)を data 行と数えていた → render の内側の検査(`e.data`)と食い違う。固定文の集合に `OMITTED`・`NOT_INCLUDED` を足して 2 つの口を同じ集合にした。
- 決定性の試験で runId の先頭 8 桁が同じ 2 つを比べていた(試験側の誤り)。

### 7.3 5 人目の 25 局での実測(packet は束 C の CLI で scratchpad に生成。packetId `22aee8fe696d0262` = 束 C の記録と一致。**実物は scratchpad、コミットしない**)

| 数 | 実測 |
|---|---|
| `seat_input.md` | **223,201 バイト・210,476 字・概算 70,159 トークン(chars/3。count-tokens は鍵が無いので未測)**。計画の見込み 300〜350 KB より小さい(表の行に組むと JSON の鍵名が消えるため) |
| sha256 | `93e45565c83fba73c4ad7949638a8028fa46cc6925fc4e89a927ce9cf833ad51`(runId `r1calib20260930a`) |
| 節と行数 | A 1 / 0.3 5 / 1 25 / 2 26 / 3 25 / 4 155 / 5 404 / 6 25 / 6.1 114 / 7 1242(局ごと 25 行)/ 8 1033 |
| 本文の数値トークン | 31,036 |
| 所要 | 1 秒未満 |

**校正(予測は計画 §4 に先に書いた)**: 1 数の包含 差 0(render の中とファイルからの 2 つの口)/ 2 行数 = packet の配列の長さ、全節一致 / 3 集計 26 行の `| aggregates.<id> | 名前 | 値 |` が §2 にそのまま 26/26 / 4 実名 0(`patient_report_data.person`・`opening_recognition.customer` の 3 通りの表記で照合。語は書かない)・`@` 0・`/Users` 0 / 5 同じ入力 2 回でバイト一致、runId を変えると差は末尾の 1 行だけ。**5 つとも予測どおり。**

**変異(予測は計画 §4)**:

| 変異 | 予測 | 実測 |
|---|---|---|
| M1 packet の `aggregates[0].numerator` 65→66 | 封で止まる・校正 3 も赤 | 止まる(`packetId が中身と合わない`、書かない)。校正 3 を当てると 25/26(`sideMatch.attack` だけ赤)。**両方赤** |
| M2 `seat_input.md` の −715 を −716 に | ファイルの口が 1 件挙げる | `数「-716」が本文に 1 回、packet + request には 0 回` の 1 件 |
| M3 request の `timeLimitSec` 600 | 止まる | `範囲: request の持ち時間が 600 秒(packet の局は 180 秒)` |
| M4 問いの文に `x@y` | 止まる(欄の型) | `request.customerQuestions[0].text にメールの記号を含む` |
| M5 指示文の 1 バイト | 止まる(sha) | `指示文の sha256 が固定値と違う` |
| M6 `provenance.thresholds` を `[]` | schema と render の両方で止まる | schema の `minItems` で止まる。**render 側の同じ検査には到達しない**(schema が先に走るので、内側の守りは生きていない = 予測の「両方」は半分外れ。害は無い。記録) |

### 7.4 門

- `npx vitest run --root scripts/playtest lib/seatInput.test.ts` 24/24。全体 102 files / **1955 passed**。
- `npm run typecheck:scripts` 赤 **11** = 既知の 10(`out/` 配下、P-84)+ **1 は他レーンの未コミット差分**(`scripts/playtest/observationPacket.ts` 107 行。作業ツリーに `observationAggregates*.ts`・`observationPacket.ts`・`dump_booklet_numbers.py` の差分があり、実験席は触っていない・コミットしない)。seatInput 由来の赤 0。
- 独立監査(step-auditor)1 回目: **REVISE 1 点**。監査が自分で render を回し直し(バイト数・行数・集計 26/26・決定性を独立に再現)、変異 3 本(pv を漏らす・`@` の検査行を消す・配列の再帰を消す)で試験が赤くなることを確かめたうえで、**`dataLinesOf`(ファイルから読み直す口)が `# (A)` から後ろだけを切り出していて 1 行目(符号・持ち時間・局数・線の組の値)が検査から落ちている**ことを実物で示した(1 行目の 180 を 999999 にしても緑)。線の組の値は本文で 1 行目にしか出ないので、読み直しの口はそれを一度も packet と突き合わせていなかった。render の内側の検査(`e.data`)とは食い違い。**私の試験・変異はどれも 1 行目を狙っていなかった**(校正の道具の穴は、その道具で作った緑からは見えない)。
- **直し**: `dataLinesOf` が 1 行目を含むようにし、試験を 1 本追加(1 行目の 180→999999・300→301 で読み直しの口が 2 件挙げる)→ 25/25。実物で校正 1(差 0)・校正 5(バイト一致、sha 変わらず `93e45565…`)を回し直し、変異 M7(実物の 1 行目 180→999999)を追加 → `数「999999」が本文に 1 回、packet + request には 0 回` で赤。M2 も引き続き赤。
- 監査の付記(自己申告): 監査中 `git add --intent-to-add` を一時使用し `git reset` で戻した、変異はバックアップから復元し差分 0。
- **差し替え(2026-09-30、R2 の中で。司令塔の決定)**: 自動化レーンが H-9 の実測で継ぎ目の衝突を見つけた ― §2 の集計を `aggregates.<id>` 単独で写すと、分子と分母のどちらを引いたかが決まらず H-9 で 26 行すべて引けない(数ごとの形なら 37/37)。**集計を数ごと 1 行**(分数は `.numerator` と `.denominator` の 2 行、単独の数は `.value`)に変え、`aggregateRef(id, part)` と文法(`lib/packetRef.ts`、1 か所)も同じ形にした。名前・母集団・出どころの局は分子の行にだけ書く(同じ値を 2 度写さない)。回し直しの実測: `seat_input.md` **224,907 バイト・211,946 字・概算 70,649 トークン**、sha256 **`19f2cca0da6fa131f3435c7d9afe838c9ffcbefd135d1d7ab1da5bac3f73a632`**、§2 は 37 行。校正 1(差 0)・2(行数一致、§2 = 37)・**3 = 37/37**(`| aggregates.<id>.<part> | 分子|分母|値 | 値 |` が全部そのまま)・4(実名 0・@ 0・/Users 0)・5(2 回でバイト一致、runId 違いは末尾 1 行)すべて予測どおり。
- 独立監査 2 回目: **GO**。監査が直しの部分だけを手で外して新設の試験が赤くなること(ダミーでないこと)を確かめ、実物で 1 行目の 999999 が検出されること、note の行・線の組の id 行・inputs の path 行が読み直しの口に含まれること、全体 1957 本緑・typecheck の赤は既知の 10 だけ(監査の手元では他レーンの差分が無い状態)を独立に確認。GO の対象は lib・試験・CLI・LOG・計画で、他レーンの未コミット差分は含まない。

## 8. 3 席 LLM API ― 束 R2(席の出力の契約: hypothesis.v0.4 + 封筒 seat-output.v0.1 + 席の出力側の契約検査)の実装と実測(2026-09-30)

計画 [STEP_LLM_SEATS_R2_CONTRACT](STEP_LLM_SEATS_R2_CONTRACT_2026-09-30.md)(57a6b31、司令塔 GO + 判断 4 点: H-2 は `packet.` を文法で / pattern を `[a-z][0-9]+` に / kind 無しは hypothesis / writtenAt は道具)。**LLM は呼んでいない・packet を読まない**(実在は H-9 = 自動化レーン)。

### 8.1 作ったもの

| 物 | 場所 | 中身 |
|---|---|---|
| 文法(1 か所) | `scripts/playtest/lib/packetRef.ts` | `AGGREGATE_REF_RE`(`aggregates.<id>.numerator|denominator|value`)・`FACTS_REF_RE`(`facts.<列>[添字].欄名…`、recognition は `rows|definitions[添字]`)・`aggregateRef(id, part)`・`packetRefPathProblems`・`PACKET_OBS_ID_PREFIX`。observationPacket* を import しない(試験が見る)。R1 の render・R2 の E-4・H-2 の分岐・レーンの H-9 が同じ定数を読む(司令塔の条件) |
| 契約 v0.4 | `schemas/hypothesis.v0.4.schema.json`(v0.3 から生成、足すだけ)、`lib/schemaVersions.ts` の KNOWN に `"0.4"`(既定は据え置き) | kind・factOrHypothesis・origin・requestRef・observations[].packetRef・actionCandidate・neededObservation・internal、prediction は任意、pattern は `[a-z][0-9]+` |
| 検査の版分岐 | `lib/hypothesis.ts` | v0.4 の行だけ: H-2(`packet.` は文法、obsId = `packet.` + path)・H-4(finding / action_candidate / unanswerable / needed_observation は予測が無くてよい)・H-5(fact / finding は読みの形を要らず、読みの語を混ぜたら落ちる)。v0.1〜v0.3 の判定は変えない |
| 封筒 | `schemas/seat-output.v0.1.schema.json`(道具が保存する形)・`schemas/seat-output.llm.v0.1.schema.json`(席が書く形。provenance・subject・knowledge・hypothesisId・status・obsId・writtenAt・run は無い) | ― |
| lib | `lib/seatOutput.ts` | `completeSeatOutput`(席の形 → 封筒。決定的。数を作らない。`structuredClone` で写してから組む)、`seatOutputProblems`(E-1 到達 / E-2 答え・missing 必須 / E-3 行 = schema v0.4 + H-1〜H-8 + kind の必須 / E-4 文法 / E-5 隔離 / E-6 内部 / E-7 run) |
| CLI | `scripts/playtest/seatOutputCheck.ts` | `--seat-output --meta --request --today [--obs-items]`。1 本でも落ちれば終了コード 1 |
| 試験 | `lib/seatOutput.test.ts`(19)・`lib/packetRef.test.ts`(4)・`lib/seatInput.test.ts`(+2 = 27)。`hypothesis.test.ts` は触っていない(v0.4 の分岐の試験は seatOutput.test.ts の中) | 全体 **104 files / 1981 passed**(私の hunk だけの worktree)、typecheck の非 out の赤 0 |

### 8.2 実装中に検査が捕まえたもの(直した)

- 事実の列の文法が緩く `facts.time.bySpent[3].collapsed`(v0.1 の packet に無い列の書き方)を通した → **列の直後に添字を必須**にした(`facts.time[3].midSpentSec` は通り、`facts.time.bySpent[3]` は落ちる)。実在の照合ではなく packet の形(配列)の文法。
- fixture の「第 1 候補」の 1 を H-1 が拾った(契約どおり)。fixture は「第一候補」に。**席への注意点**: statement の「第 1 候補」も数として H-1 に掛かる → 指示文 v1.1 に 1 句(または render の §0 の固定文)で伝える候補。
- fixture の packetRef を 3 か所で共有していて、変異の試験が互いに漏れた(8 本が連鎖で赤)。fixture は毎回新しい object に。**同じ危うさが道具側にもあった**(封筒に席の object を参照のまま入れていた)→ `structuredClone`。試験: 封筒を直しても入力が変わらない。
- 「内部の分岐 = 検査が 10 本」の赤 2 本は、共有ツリーに同居していた自動化レーンの未コミット H-9 によるもの(§8.4)。

### 8.3 校正・変異(予測は計画 §6)

| 校正 | 予測 | 実測 |
|---|---|---|
| 1 実験 1 の契約 6 本(v0.3)の schemaVersion を 0.4 にした写し | 6/6 で 9 検査 ok | **ok**(`hypothesisCheck.ts` 終了コード 0。元の v0.3 も 0)。試験にも固定 |
| 2 最小の封筒(finding / hypothesis / unanswerable・問い 1)が E-1〜E-7 を通る | ok | ok。**実物の meta(5 人目、37 行の §2)と request でも CLI が「問題なし」** |
| 3 `hypothesis.test.ts` の既存 31 本 | 変わらず緑 | 緑(worktree) |
| 4 packet を読まない | import の一覧に無い | 試験が `from "./observation…"` と `readFileSync(…packet…)` の不在を見る |

| 変異 | 予測 | 実測 |
|---|---|---|
| unanswerable の missing を空 | E-2 | E-2 の 1 件(CLI でも rc=1) |
| packetRef.path を `facts.time.bySpent[3].collapsed` | E-4(文法) | **E-4 + E-3(H-2)の 2 件**(同じ文法を 2 か所から読むので両方落ちる。文法は 1 か所) |
| 合言葉を 1 字 | E-1 | E-1 の 1 件 |
| 隔離欄の数を statement に | E-5(H-1 も) | E-5 + H-1 の 2 件 |
| fact の statement に「という読みです」 | E-3(H-5) | H-5 の分岐の 1 件 |
| hypothesis から prediction を外す | E-3(H-4) | H-4 の 1 件 |
| finding から prediction を外す・付ける | 通る | 通る(kind で必須が変わる) |
| answers の中に internal | E-6 | **封筒の schema が先に落とす**(`additionalProperties: false`)。E-6 は schema をすり抜けた形の備え(計画の予測は半分外れ。記録) |
| 席が書く形に provenance を入れる | 席が書く形で落ちる | 落ちる(`completeSeatOutput` も例外) |
| itemId の重複 | ― | `completeSeatOutput` が例外(追加) |
| 節を写さず omissions にも無い | E-1 | E-1 の 1 件(追加) |

### 8.4 独立監査(step-auditor): **GO**

監査が worktree で自分で回したもの: 全体 1981 本緑・typecheck 赤 0 / schema の差分(required から prediction を除いた 1 点以外は全部追加、additionalProperties false のまま)/ 校正 1(6 本 × v0.3・v0.4 とも exit 0)/ 校正 2(**監査が自分の script で封筒を組み直し**、実物の meta と request で「問題なし」)/ 変異 6 本(E-1・E-2・E-4+H-2・E-5+H-1・H-4・H-5)を自分のデータで再現、二重検出まで一致 / 実装を 3 か所消す変異(H-5 の fact 分岐・FACTS_REF_RE の添字必須・E-5 の塊)で対応する試験が赤くなること(11 本・1 本・1 本)を確かめ、バイト一致に復元。
GO を妨げない指摘 2 点(直した・記録した): (1) partial の空 missing の専用試験が無かった → 1 本追加(20 本)。(2) scratchpad の smoke script `r2/make_env.ts` は古い meta(26 行版)を指したまま ― 実際の校正 2 は sed で置き換えた写しで回した(§8.3 の env_ok.json は 37 行版)。**再現の手順を書くときはこの script を指さない**。監査は独立に別の script で同じ結果を得た。

### 8.5 共有ツリーの衝突とコミットの仕方

作業ツリーの `lib/hypothesis.ts`・`lib/schemaVersions.ts`・`lib/hypothesis.test.ts` に自動化レーンの未コミット H-9 が同居していた(検査が 9 → 10 本になり、レーンの側の試験 2 本が赤)。司令塔の決定: **R2 が先**(レーンの H-9 が `packetRef.ts` を読む側)。私の hunk だけを HEAD から script で作り直し(scratchpad `r2/apply_mine.py`)、別 worktree で全体の試験・型検査を通し(1981 本緑・非 out の赤 0)、監査 GO の後、**私の版の blob を index に置いて**(`git hash-object` + `update-index`)`git diff --cached --stat` に私のファイルだけが載っていることを見てから commit。コミット後の共有ツリーの残差はレーンの hunk だけになる(1 行で報告)。

## 9. 3 席 LLM API ― 束 R3(統合 = 整理役の入力と出力の契約と検査)の実装と実測(2026-09-30)

計画 [STEP_LLM_SEATS_R3_INTEGRATION](STEP_LLM_SEATS_R3_INTEGRATION_2026-09-30.md)(170322d、司令塔 GO + 判断 4 点。I-3 は「forVerification から外す束は**すべて** heldBack に理由つき。理由は seatCount を参照しない」に直して GO)。**LLM は呼んでいない・packet を読まない**(packetDigest は呼び出し側が渡す packet の JSON からの写し。検査は読まない)。実装は R2 と同じく私だけの worktree(HEAD 4119298)で行った(共有ツリーには自動化レーンの未コミット差分が残っているため)。

### 9.1 作ったもの(新規 6 ファイル。既存のファイルは触っていない)

| 物 | 場所 | 中身 |
|---|---|---|
| 器(入力) | `schemas/integration-input.v0.1.schema.json` | 席は `seatIndex` だけ(名前なし)、`internal` の欄が無い(`additionalProperties: false`)、席の行の写しは許した欄だけ、`packetDigest` = 線の組・集計 37 行・局の表、空席は `present: false` + 理由 |
| 器(出力) | `schemas/integration.v0.1.schema.json` | `clusters[]`(`clusterId`・`packetRefs`・`itemRefs`・`seatCount {value, evidence: const false}`・`representative` = v0.4 の行)・`contradictions`・`dropped`・`heldBack`(理由つき)・`forVerification`・`answersByQuestion`・`selfComputedNumbers`・`seatOrderRef`・`run` |
| 整理役が書く形 | `schemas/integration.llm.v0.1.schema.json` | clusters(representative は席が書く形と同じ欄)・contradictions・dropped・heldBack・forVerification・answerNotes。**seatCount・answersByQuestion・run・代表の道具の欄は書けない** |
| lib | `lib/integration.ts` | `seatPermutation`(runId → 決定的な置換、`lib/prng.ts`)、`copySeatItem`(許した欄だけ)、`packetDigestOf`、`buildIntegrationInput`(封筒 → 器。**席の hypothesisId も匿名 `I-<seatIndex>-<連番>` に写し替え**、対応表 `itemMap` は seatOrder と一緒に run のログへ)、`answersByQuestionOf`(機械で決まる内訳と summary。1 席でも違えば `mixed`)、`completeIntegration`(整理役の形 → 器。決定的。`seatCount.value` = 異なる席の数)、`integrationProblems`(I-1〜I-8)、`canonicalJson`(observationPacket.ts を import しないために同じ規則を持つ) |
| CLI | `scripts/playtest/integrationCheck.ts` | `--integration --input --today [--obs-items]` |
| 試験 | `lib/integration.test.ts`(19 本) | 全体 **105 files / 2001 passed**(worktree)、typecheck の非 out の赤 0 |

### 9.2 実装中に検査が捕まえたもの(直した)

- **席の hypothesisId(R2 の形 `H-c5-gptrun2-001`)が席名を埋め込んでいた** → 入力の器にそのまま写すと整理役に席名が漏れる(校正 1 の「席名が無い」が赤)。器では匿名 id に写し替え、`answers[].itemIds`・`derivedFrom` も同じ対応で置き換える。対応表はログ側(seatOrderRef)。R2 の id の形は変えていない(封筒の中では席名を持ってよい ― 封筒は整理役に渡らない)。
- **代表の行の `provenance.inputs` を `integration_input:<sha>` にすると H-6(盲検)の禁止語「integrat」に当たる**。代表は席の項目から作られるので、入力として正直なのは成員の列 → `seat_item:<seatIndex>:<匿名 id>` にし、**I-8 で束の itemRefs と一致すること**を見る(器の sha は `run.inputSha256`)。H-6 を避けるための言い換えではなく、出どころが成員そのものになった。
- 予測の外れ 2 点(記録): 同じ席の項目を別の束に足す変異は seatCount を変えない(I-3 は鳴らず I-1・I-2・I-8 の 3 件)。I-4 の変異に隔離欄と同じ数 0.61 を使うと I-6 も鳴る(試験側の誤り、数を変えた)。

### 9.3 校正・変異(予測は計画 §5)

| 校正 | 実測 |
|---|---|
| 1 封筒 3 つ(1 つは空席)から器を組む → schema を通る、`internal` 0、席名 0、itemMap 6、空席は理由つき | ok |
| 2 最小の出力(束 2・dropped 2・矛盾 1・heldBack 1)が I-1〜I-8 を通り、道具が seatCount `{2, false}`・answersByQuestion(summary `unanswerable`、bySeat 2)・run を埋める | ok。**実物**: R2 の smoke 封筒(5 人目の meta)× 2 席 + 空席 1 で器を組み(集計 37・局 25・12,181 バイト・`internal` 無し・席名無し)、CLI が「問題なし」。heldBack を空に → I-3 の 1 件、代表に `origin.seat: claude` → I-7 の 2 件 |
| 3 同じ runId で同じ順・同じ器、違う runId で順が変わる例あり | ok |
| 4 packet を読まない(`from "./observation…"` と `readFileSync(…packet…)` の不在) | ok |

| 変異 | 予測 | 実測 |
|---|---|---|
| 項目を clusters からも dropped からも落とす | I-1 | I-1 の 1 件 |
| 根拠の場所を共有しない項目を束に | I-2 | I-2 + I-1(2 回)+ I-8 の 3 件(I-3 は鳴らない ― 上) |
| `evidence: true` | schema | schema の 1 件 |
| `seatCount.value` +1 | I-3 | I-3 の 1 件 |
| 束を forVerification から外し heldBack に置かない / 理由が一致の数を参照 | I-3 | I-3 の 1 件ずつ |
| 代表の statement に成員に無い数 / 代表の観測に成員に無い場所 | I-4 | H-1 の 1 件 / I-4 の 1 件 |
| 1 席 unanswerable なのに summary を answered | I-5 | I-5 の 1 件 |
| 隔離欄の数を矛盾の text に | I-6 | I-6 の 1 件 |
| 代表に `origin.seat: gpt` | I-7 | I-7 の 2 件(origin + 席名の語) |
| `run.inputSha256` を変える | I-8 | I-8 の 1 件 |
| 入力に `internal` を入れる / 整理役が seatCount・answersByQuestion を書く | 器の schema で落ちる | 落ちる(構造で拒む) |

### 9.4 独立監査(step-auditor): **GO**

監査が worktree で自分で回したもの: 全体 2001 本緑・typecheck 赤 0 / CLI smoke 3 本(ok・heldBack 空 → I-3・origin.seat → I-7 の 2 件)/ 実物の器を走査して集計 37・局 25・線 6・`internal` 0・席名の語 0 / 実装を消す変異 3 本(I-1 の「どちらにも無い」・SEAT_COUNT_REFERENCE_RE・copySeatItem の白名簿に internal)で対応する試験が赤くなる(3 本目は入力 schema が先に落とし、copySeatItem の単体試験も独立に赤 = 二重の壁)ことを確かめ、バイト一致に復元 / H-6 の禁止語「integrat」に `integration_input:<sha>` が当たることを自分で実測し、`seat_item:` の形は言い換えでなく出どころが成員そのものになった、と判断。指摘 1 点(GO を妨げない): 計画 §3・§4 I-8 の文言が実装と食い違っていた → 正本を実装に合わせた(この commit)。

## 10. 3 席 LLM API ― 束 R4(callSeat: 実際の呼び出し・再試行・原文保存・1 回の実行の器)の実装と実測(2026-09-30)

計画 [STEP_LLM_SEATS_R4_CALLSEAT](STEP_LLM_SEATS_R4_CALLSEAT_2026-09-30.md)(f31982c、司令塔 GO + 6 点の答え)。**この束では LLM を 1 度も呼んでいない** ― 試験は fetch を差し替えて網に出ない。実装は R2・R3 と同じく私だけの worktree(HEAD f32e911)。実行は鍵・モデル名・単価・上限額が `.env` に入ってから(下見だけは実物の `.env` で回した。§10.4)。

**司令塔・人間の決定をこの束で規則にしたもの**: (1) `SEAT_COST_CAP_USD` を越える見込みなら**送る前に**止める。(2) 鍵は `.env` からだけ読み、保存物・run_summary・例外・ログに出さない。(3) 失敗した席は他の席で埋めない(空席のまま器に残る)。(4) **上限は実行の累計**に掛かる ― 揺れの床の 2 回目(同じ入力・runId だけ違う)は 1 回目の累計を引き継ぎ、越える見込みなら 1 通も送らない。(5) Gemini は入力 200k 超で単価が上がる段があり、**超える組では高い段で見積もる**(安い方に倒さない)。

### 10.1 作ったもの(新規 8 ファイル + 既存 1 ファイルの直し)

| 物 | 場所 | 中身 |
|---|---|---|
| 鍵と値の入口 | `lib/env.ts` | `.env` を読む**唯一の場所**(依存 0 の最小パーサ・既に在る名前は上書きしない・戻り値は名前だけ)、`ENV_NAMES`(鍵 3・モデル 3・整理役 2・単価 6・段 3・入力上限 3・上限額)、`redactSecrets` |
| 概算と上限 | `lib/tokenBudget.ts` | `estimateTokensByChars`(chars/3)・`pricesFor`(段。当たる段のうち**高い方**)・`costUsd`・`budgetDecision`(`cost_cap` / `input_limit`。**越えたら送らない**) |
| 呼び出し層 | `lib/llmClient.ts` | 3 社の REST を `fetch` で薄く(SDK 0)。`callStructured`・`countTokens`(OpenAI は入口が無く undefined)・`parseStructuredResponse`(3 社の応答から text/json/usage/finishReason/modelVersion)。再送は 429・5xx・接続で 1・4・16 秒の 3 回。**鍵はヘッダだけ**(Gemini も URL に載せない)、例外の文は `redactSecrets` を通す |
| 構造化の写し | `lib/schemaAdapters.ts` | 正本 → OpenAI strict(全欄 required + 任意は `anyOf [T, null]` + `additionalProperties false`)/ Gemini(`additionalProperties`・`pattern` 無し・`const` → `enum`・型配列 → `nullable`)/ Anthropic(正本のまま)。`dropNullsNotAllowed`(strict の `null` を「欄が無い」に戻す)・`forbiddenKeywords` |
| 1 席・1 回の実行 | `lib/seatRun.ts` | `runSlot`(送る前の数え → 上限 → 送る → 正本で検証 → 再試行)・`runSeat`(+ 合言葉 → `completeSeatOutput`)・`runAll`(render → 3 席を順に → 器 → 整理役 → R2・R3 の検査 → `run_summary`)。空席の理由 8 種(`no_key`・`no_model`・`cost_cap`・`input_limit`・`http_failed`・`schema_failed`・`reach_failed`・`no_json`) |
| 指示文の例の門 | `lib/instructionExamples.ts` | 指示文の**場所の例**を実物の packet に当てる(司令塔の F-2・F-3)。**書き方の誤り(表の名前・欄名・集計の id・文法・例が 3 本未満)は送らない / 材料の薄さ(表が空・行番号が表の外・値が空)は警告で続ける**。**packet を読むのはこの module と CLI だけ**(契約の検査は読まない ― 実在の照合は H-9) |
| CLI | `scripts/playtest/runSeats.ts` | `--packet --request --out-dir [--env --runs 2 --instruction --instruction-sha --integrator-instruction --forbid-file --dry-run]`。**単価が無ければ送らない**(費用が 0 に見えて上限が効かないため)。`--dry-run` は鍵を使わず束と概算と上限だけ見せる |
| 見本 | `.env.example` | 値は鍵だけ空。モデル名は人間・司令塔の決定(`gpt-5.5` / `gemini-3.1-pro-preview` / `claude-opus-5`、整理役 anthropic + `claude-opus-5`)。**別名を使わない**(周をまたいで席を比べるため) |
| 試験 | `lib/llmClient.test.ts`(20)・`lib/schemaAdapters.test.ts`(14)・`lib/seatRun.test.ts`(27)・`lib/env.test.ts`(9)・`lib/tokenBudget.test.ts`(12)・`lib/instructionExamples.test.ts`(19) | R4 の 6 本で **101 本**、全体 **112 files / 2120 passed**(worktree)、typecheck の赤 0 |
| 直し(既存) | `lib/hypothesis.ts` の H-2 | §10.2 の 1 点(私が R2 で作った抜け)。`lib/seatOutput.test.ts` に回帰 4 本 |
| 指示文の sha の門 | `lib/seatRun.ts` の `FIXED_INSTRUCTION_SHA256` + `fixedShaProblems` | 司令塔が固定した 3 本(v1・v1.1・整理役 v1)の sha。**表に無い指示文は配らない**・`--instruction-sha` を手で打っても固定値と照合する・**整理役の指示文はここだけが照合する**(render を通らないので、これまで誰も見ていなかった)。1 バイト変えれば試験が赤くなる = 版名を上げる合図 |
| 指示文の下書き | `docs/LLM_SEATS_INSTRUCTION_v1.1_2026-09-30.md`・`docs/LLM_SEATS_INTEGRATOR_INSTRUCTION_v1_2026-09-30.md` | 司令塔が読んで sha を固定する(初回の実行の直前に 1 回だけ) |

### 10.2 実装中に検査が捕まえたもの(直した)

1. **H-2 の歩く先が足りていなかった(私の R2 の抜け。R4 の通し試験で出た)**。封筒では反証(`counterEvidence.items[].observations[]`)と分数(`observations[].derived.numerator/denominator`)も `packet.` の obsId を持つのに、v0.4 の分岐は `observations[]` だけを歩いていた → **正しい席の行が「登録簿に無い」で落ちる**。3 か所を歩くようにし、封筒では反証の観測が `packetRef` でなく `path` を持つことに合わせた。**在来の試験で捕まらなかった理由**: fixture が反証・分数に `observations` と同じ path を使っていたので、先に集めた集合に入っていて登録簿の側へ回らなかった(集合の重なりで隠れる型 ― 記憶の「試験の正解は近くの数と同じにしない」と同型)。回帰は別の path で 4 本。
2. **Anthropic は tool の名前が強制した名前と一致しないと JSON を取り出さない** → 試験の fixture が別名だったため 3 席目が `no_json` で空席になった(試験側の誤り。仕様としては正しい振る舞いなので実装は変えず、fixture を直した)。
3. **整理役は器の行をそのまま代表に写せない** ― 器の観測は `obsId` を持ち、代表の観測は `packetRef` を持つ形(整理役向けの正本)。`obsId`・`writtenAt` を写すと「知らない欄」で 5 件落ちる。**整理役の指示文 v1 にこの写し替えを明記した**(実測で分かった落ち方)。
4. **単価の変数名が `.env` の実物と違っていた**(私の案 `PRICE_*_IN`/`_OUT`、置かれていたのは `PRICE_*_INPUT`/`_OUTPUT`)→ 下見で「単価が無い」警告が 3 本出て分かった。**実物に合わせた**(`.env` を書き替えるのでなく道具を合わせる)。あわせて**単価が無ければ実行を止める**門を足した(0 と見なすと上限が効かない)。
5. **指示文 v1 の場所の例(`facts.time.bySpent[3].collapsed`)が文法を通らない** ― 行番号は表の名前のすぐ後ろに付ける決まりなので、席がこの例をまねると E-4 / H-2 で落ちる。v1.1 で直し、**指示文の例を機械に当てる試験**(`lib/instructionExamples.test.ts`)を足した。
6. `LlmHttpError` が再送の回数を持っていなかったので `run_summary` の `httpAttempts` が 0 になった → 例外に回数を持たせた。
7. **指示文の例が実物の packet で引けなかった(3 本)**。司令塔が目で 1 本(`facts.recognition.rows[0].reviewStatus` ― 認識の行にこの欄が無い)、**機械で当てて残り 2 本**(`aggregates.side_match.attack.numerator` ― 実物の id は camelCase の `sideMatch.attack` / `facts.moves[10].spentSec` ― 手の表に時間の欄が無い)。席は例をまねるので、配った側の誤りが席の失敗に見える。差し替えた 5 本は実物で全部引けて値も入っている。**目で確かめる限界の実例**として司令塔が記録した。
8. **例の行番号を固定すると、材料の薄い組で正しい packet が送れなくなる**(司令塔の F-3)。`facts.time[3]` のような例と「例が引けなければ送らない」門を組み合わせると、局数の少ない組・10 切れの新しい顧客で止まる。例の行番号を `[0]` にし、**門を 2 段**(書き方の誤り = 止める / 材料の薄さ = 警告)に分けた。

### 10.3 校正・変異(予測は当てる前に scratchpad の `PREDICT.md` に書いた)

| 校正 | 実測 |
|---|---|
| 1 3 社の応答の形から text/json/usage/finishReason を取り出す(切れた応答は `length`、知らない終わり方は `other`) | ok |
| 2 3 社の入口・ヘッダ・本体(Gemini の鍵は URL でなくヘッダ、Anthropic は tool_choice で強制、temperature を渡さない席には送らない) | ok |
| 3 写しが正本の受理集合を狭めない ― 任意の欄を**全部 null で埋めて**返っても、`dropNullsNotAllowed` を通せば正本を通る(通す前は落ちることも見た) | ok(seat-output・integration の両方) |
| 4 3 席 + 整理役の通し(空席なし)→ 封筒 3・E-1〜E-7 が 0 件・器・統合・I-1〜I-8 が 0 件・保存物 10 種 | ok |
| 5 実物の `.env` と 5 人目の packet で**下見**(鍵は使うが送らない) | 束 226,313 B・212,678 字・概算 70,893 トークン(chars/3)。1 回の見込み(取り置き満額の最悪値)= gpt 1.2545 + gemini 0.5018 + claude 1.1045 + 整理役 0.8545 = **3.7152 ドル**、**2 回で約 7.43 ドル**(上限 10 ドル)。モデル名・上限額は `.env` から読めた。**段の 3 変数と入力上限は `.env` に無い**(§10.5) |
| 6 指示文の sha が固定値と違えば実行を始めない | ok(v1.1 に 0 埋めの sha を渡して停止) |
| 7 指示文 v1.1 の例 5 本を実物の packet に当てる | **5 本中 5 本が引けて値も入っている**(`aggregates.sideMatch.attack.numerator` 65・`aggregates.branches.total.value` 404・`facts.time[0].longThinkCount` 5・`facts.branches[0].topGapCp` -46・`facts.recognition.rows[0].names` 2 件)|
| 8 古い v1 を渡すと例の門が止める | ok(**3 件**: 文法に合わない例 2 本 + 例が 2 本しか無い)|
| 9 sha の門: 固定値で通る / 手で違う sha を渡すと止まる / 表に無い指示文は配れない | ok(3 通りとも)|

変異 **16 本すべてが狙った試験だけを赤くした**(素は 152 passed。門の 4 本 M11・M11b・M12・M13 は F-3 の直しの後に足した)。

| # | 変異 | 赤くなった試験 |
|---|---|---|
| M1 | 保存物から `redactSecrets` を外す | 鍵が保存物・run_summary に出ない(1) |
| M2 | 入力上限の判定を外す | input_limit(2) |
| M2b | 費用の上限の判定を外す | cost_cap 関係(7) |
| M3 | 空席を直前の席の封筒で埋める | 器には 3 席が残り、空席は項目 0 件(1) |
| M4 | 合言葉不一致でも再試行に回す | reach_failed は再試行しない(1) |
| M5 | 途中切れの倍率を 1.0 に | 取り置きを 1.5 倍にして 1 回(1) |
| M6 | `capReached` を立てない | 1 席目で越えたら残りの席も送らない(1) |
| M7 | 段を見ない(下の段を返す) | 段の判定(5) |
| M8 | H-2 の反証を歩かない | 反証の path(2)+ 通し(1) |
| M8b | H-2 の分数を歩かない | 分数の分子の path(1) |
| M11 | 値が空でも `ok` にする(薄さの判定を消す) | 値が空でも止めない・薄い材料では警告だけ(2) |
| M11b | 表が空を `error` にする | 表が空でも止めない・薄い材料では警告だけ(2) |
| M12 | 欄名の誤りを見ない | 欄名が実物と違う(1) |
| M13 | 例が足りないことを誤りにしない | 例が足りないのは誤り(1) |
| M9 | 例外の再送回数を 1 に固定 | http_failed の回数(1) |
| M10 | 再依頼の文に前回の返答を足す | 会話にしない(1) |

**雑音 1 件(記録)**: M10 のとき `lib/hypothesis.test.ts` の子プロセスの試験も落ちたが、その試験は `seatRun` を import していないので変異とは無関係で、単体で回すと 34/34 緑 ― 並行して回したときの時間切れ。**沈黙が 1 本出た(M6)。** 上限を 0.01 ドルにした試験では席ごとに落ちるだけで「残りも送らない」を測れていなかった(等価変異)。上限 0.6 ドル(**2 席目は単体なら収まる額**)に直して赤くなった ― 極端な値の試験は経路を測らないという型。

### 10.4 まだ測っていないこと(門)

- **実際の呼び出しは 0 回**。到達率・自分で数える率・発見の重なり・戦型の問いへの answers の内訳・費用と所要(計画 §6.0 の表)は初回の実行の後に書く。
- 費用の**実測**は無い。§10.3 の校正 5 は取り置き満額の最悪値で、実際の出力が 1 万トークンなら下がる。
- 各社の**本物の応答**は見ていない(fixture は公開 API の応答の形を手で写したもの)。形が違えば `no_json` か `schema_failed` の空席として残り、原文が保存される。

### 10.5 司令塔・人間に渡すこと

1. **指示文 2 本の実文**(v1.1 と整理役 v1)を読んで sha を固定。整理役 v1 は承認済み(直しなし)。席 v1.1 は司令塔の F-1(名前は認識の表の `names` に出たものだけ・定義の表にしか無い名前は使えない)・F-2(例を解決器で確かめる)・F-3(例の行番号は `[0]`・門は 2 段)を直した。**司令塔が 2026-09-30 に 2 本の sha を固定した**: 席 v1.1 = `11d1f533c74ec6dcecbd9010fb512546961bc753f57e45e88b34157b8cdb148b`(6,113 B)・整理役 v1 = `5118a6949862a104942f6975191dd3d16b00ca834f18b4bba5807aeaf2d7d94a`(4,403 B)。**1 バイトでも変えるなら版名を上げる(同じ版名で中身を差し替えない)** ― 周をまたいで席の答えを比べるとき、どの文で聞いたか分からなくなるため。道具は表の固定値で照合するので、CLI に sha を手で渡す必要は無い。
2. **段の 3 変数は司令塔が `.env` に足した**(`PRICE_GEMINI_TIER_ABOVE_TOKENS=200000`・`PRICE_GEMINI_INPUT_HIGH=4`・`PRICE_GEMINI_OUTPUT_HIGH=18`)。下見で 18 個の名前が読めて警告が消えたことを確かめた。`SEAT_*_INPUT_LIMIT` は空のまま(無ければ費用だけで見る)。
3. 単価の変数名は `.env` の実物(`PRICE_*_INPUT` / `PRICE_*_OUTPUT`)に合わせた ― 計画 §9 の表の名前(`_IN` / `_OUT`)は古い。

### 10.6 指示文の直しと、独立監査の 1 回目(REVISE)― 経緯と直し(2026-09-30)

**指示文の直しは司令塔の指示で 3 回入った。** 順に F-1・F-2・F-3。この 3 つと、そこから生まれた 2 つの門(例の門・sha の門)は**司令塔が承認している**(便: 整理役 v1 は直しなしで承認、席 v1.1 は F-1・F-2 の直し後に F-3 を追加指示、`instructionExamples` の門とコミットの段取りは「すべて承認済み」、最後に 2 本の sha を固定)。

| 印 | 司令塔の指示 | 直したこと |
|---|---|---|
| F-1 | 名前の出どころは**認識の表に出た名前だけ**(H-10 が通すのは `rows[].names`。定義の表 108 件のうち 92 件はこの顧客の局では認識されていない ― レーンの実測) | 指示文 14 行目を「局ごとの認識の表に出た名前だけ」に。定義の表にしか無い名前は使えないと明記 |
| F-2 | 例の path を**解決器で実物の packet に当てて機械で確かめる**(目で確かめない) | `lib/instructionExamples.ts` を作り、`runSeats` の送る前の門にした。実測で私の候補 3 本が引けなかった(司令塔が目で見つけたのは 1 本) |
| F-3 | 例の行番号は `[0]`・**門を 2 段に**(書き方の誤り = 止める / 材料の薄さ = 警告で続ける) | 例を `[0]` に。`error` と `warn` を分け、薄い packet で正しい実行が止まらないようにした |
| ― | **2 本の sha を固定。1 バイトでも変えるなら版名を上げる(同じ版名で中身を差し替えない)** | `FIXED_INSTRUCTION_SHA256` の表と `fixedShaProblems` を作り、**整理役の指示文にも sha の門**を付けた(render を通らないので、それまで誰も照合していなかった)。表と実物が違えば試験が赤くなる |

**独立監査の 1 回目は REVISE。理由は私の手順の誤りである** ― 監査が走っている最中に、司令塔の F-2・F-3 の指示を受けて**同じ worktree を編集した**。監査は「記録と実物の照合」を中心に見るので、対象が動くと前提が崩れる(試験の本数が監査の途中で 2099 → 2113 に動き、記録が追いついていない状態を監査が読んだ。`lib/seatRun.test.ts` が一度だけ `expected 1 to be 3` で落ちる揺れも観測された ― 書き込み中のファイルを読んだためと見られる)。**教訓: 凍結してから監査に出す。監査中に指示が来たら、指示の実装は監査の後に回すか、監査を止めてから入れる。**

監査が**測って見つけた穴 2 つ**(どちらも「緑だが何も守っていない」)を閉じた。

| 監査の変異 | 沈黙した理由 | 閉じ方 | 閉じた後の変異 |
|---|---|---|---|
| E: 鍵の**空の字**の判定を外す | `.env` 側で空文字は undefined に直しているので実運用では届かないが、`seatRun` 単体の守りを試験していなかった | 鍵に空の字を渡す試験を足した | M15 で赤 |
| F: 例の**文法**の判定を外す | 文法を外しても**別の理由**(欄が無い・集計の id が無い)で `error` になるので、`level` だけ見る試験は黙る | 文法の試験が**理由まで**見るようにした(4 本の path で「文法」を含むこと) | M14 で赤 |

監査が実物と合うことを確かめた範囲(指摘以外): H-2 の歩く先 3 か所・変異 12 本の狙いと本数・下見の概算額・単価の変数名の経緯・`package.json` に差分なし(SDK を足していない)・`.env.example` に鍵の値なし・指示文 2 本に禁止語 0 件。監査自身の変異 6 本のうち 4 本(合言葉・H-2・null の後始末・例外の redact)は赤で、守れていることが測られた。

あわせて `lib/hypothesis.ts` の H-2 のコメントを実装に合わせた(「observations の packetRef で裏づく」→ 歩いた 3 か所で裏づく)。**2 回目の監査は、凍結した状態で差分(指示文 2 本・`instructionExamples`・sha の門・穴 2 つの直し)を対象に依頼する。**

### 10.7 独立監査の 2 回目: **GO**(2026-09-30)

凍結して差分だけを対象に同じ監査席へ出した。監査は**凍結を機械で確かめた** ― 未追跡 16 ファイルの sha256 を開始時と終了時に取り、私が置いた `freeze/SHA256.txt` と 3 方向で比べて完全一致(監査中に対象が動いていない)。記録との照合も一致(112 files / 2118 passed・typecheck exit 0・個別の本数 99 本・`package.json` に差分なし・固定 sha 3 本は実物と一致)。

監査は**自動試験が `main()` を通らないことを補って、CLI を実行で裏取りした**: 表に無い指示文名は拒否・`--instruction-sha` の誤り値は拒否・正しい値は通過・**整理役の指示文を 1 バイト壊して渡すと sha の門が拒否**(「render を通らないのでこれまで誰も照合していなかった」経路を実行で確かめた)・実物に合わせた packet で例 5 本が「5 本中 5 本」で通過(`facts.recognition.rows` の 2 段の引き当てが実際に効くことも実行で確認)。

監査自身の変異 5 本のうち 3 本は赤(閉じた穴 2 つの再試 E・F、`facts.recognition` の 2 段判定 H)。**沈黙 2 本 = 境界の試験漏れ**を指摘された(ブロッカーではないが、次に触るときに足すこと)。**その場で閉じ、変異で赤を確かめた**(試験だけの追加で、動きを変えるコードは触っていない)。

| 監査の変異 | 沈黙した理由 | 閉じ方 | 閉じた後 |
|---|---|---|---|
| G: `isEmptyValue` が 0 も空にする | fixture に**値 0 の例が無かった** | `facts.time[0].remainingSec`(値 0)が `ok` であることを固定 | M16 で赤 |
| I: 例の本数の判定を `< min - 1` に(off-by-one) | ちょうど `min - 1` 本(2 本)を突く試験が無かった | 2 本 → 誤り 1 件 / 3 本 → 0 件の両側を固定 | M17 で赤 |

**型(記憶に残した)**: 「境界の値そのものを材料に持たない試験は、境界をずらす変異で黙る」 ― 0・ちょうどの本数・ちょうどの上限は、**その値を材料に置く**。

## 11. 初回の実行(2 回回し)の実測と、そこから出た直し(2026-09-30)

**送信は 2 回の実行(同じ入力・runId だけ違う)。上限 10 ドル(人間の決定)。原文は `scripts/playtest/out/c5/llm-seats/<runId>/`(gitignore)に全部残した。**
中身の評価(どの発見を採るか)は司令塔の工程で、ここには書かない ― 書くのは**数と到達**だけ。

### 11.1 1 回目の試み: 4 席とも入口で 400。実費 0 ドル

道具は設計どおり「席が 1 つも立たなかった」で止まり、理由を 4 本保存した。**3 社が 3 つの別の理由で断った**(どれも写しと本体の作りで、契約ではない)。

| 席 | 断られた理由(原文の要旨) | 直し |
|---|---|---|
| Claude・整理役 | `temperature is deprecated for this model` | Anthropic に温度を送らない |
| GPT | strict の写しで `value` の自由形の object の枝に `additionalProperties: false` が無い | 自由形の object の枝を落とす |
| Gemini | `value` の配列の枝に `items` が無い(`any_of[5].items: missing field`) | 自由形の配列に items(数・字・真偽・無し)を足す |

### 11.2 2 回目の試み: Claude 席と整理役が到達。実費 4.3941 ドル

| 席 | 周 1 | 周 2 |
|---|---|---|
| GPT | 1 回 → 400(`Unsupported parameter: 'temperature'` ― **gpt-5.5 も温度を受け付けない**)。0 ドル | 同じ。0 ドル |
| Gemini | 4 回(429 で再送 3)→ 失敗(`Quota exceeded … free_tier`。**鍵が無料枠**)。0 ドル | 同じ。0 ドル |
| Claude | **3 回**(形が合わず再依頼 2 回)→ 2.7963 ドル・309 秒・入力 42.6 万トークン | **1 回** → 0.929 ドル・93 秒・入力 14.2 万 |
| 整理役 | 1 回 → 0.3331 ドル(束 11 件) | 1 回 → 0.3356 ドル(束 11 件) |

**揺れの床(同じ入力・同じ写し・runId だけ違う)**

| 測り | 周 1 | 周 2 |
|---|---|---|
| 項目の数 | 11 | 11 |
| kind の内訳 | finding 8・hypothesis 1・unanswerable 1・needed_observation 1 | finding 7・hypothesis 1・unanswerable 1・needed_observation 1・action_candidate 1 |
| fact / hypothesis | 10 / 1 | 8 / 3 |
| 自分で作った数(隔離欄) | 5 | 5 |
| 読めなかった申告(omissions) | 4 | 4 |
| 整理役の束 | 11 | 11 |
| 契約の指摘(席) | 23(E-1 10・H-1 7・H-3 4・その他 2) | 25(E-1 12・H-1 10・H-5 1・その他 2) |
| 送信回数 | 3 | 1 |

**数はそろい、種類の内訳は動く。** 顧客の問い(q1)への答えは両周とも **partial**(根拠 6 件)で、`unanswerable` ではない。
束に無くて答えを狭めたものとして挙がったのは周 1 が 3 件・周 2 が 4 件で、**両周で重なるのは 3 件**:
(1) 局ごとの「普段指す・普段指さない」の印、(2) 群ごとの勝敗の内訳、(3) 群ごとに母数をそろえた分かれ道・崩れの割合。

**契約が効いた証拠**: 席の H-1 が 7〜10 件(文に出した数を observations に写していない)・H-3 が 4 件(反証を書いたのに `none_found`)、整理役も I-4 で 11 件。
**どれも数え直しや捏造ではなく「写し忘れ」** ― 指示文に書いてあっても守られないことの実測で、機械の層が要る根拠になる。

### 11.3 実測から出た直し(司令塔の決定つき)

| # | 直し | 理由 |
|---|---|---|
| 1 | **3 席とも temperature を送らない** | gpt-5.5 も claude-opus-5 も受け付けない。受け付ける Gemini だけに送ると**席の条件が非対称**になり、一致・不一致を実力差として読めない(司令塔の対称性の線)。送らなかったことは `run_summary.temperatureSent` に残す ― 「温度 0 で回した」と誤読させない |
| 2 | **`value` の有効な形を 3 社でそろえる**(数・字・真偽・無し・その配列) | 社ごとに写しの狭さが違うと席の間で「書ける形」が変わる。**いちばん狭い社にそろえる**(司令塔の条件)。`run_summary` に席ごとの `valueShape` と `totals.valueShapeSame` を残す |
| 3 | **render の meta に見出しだけの節(0・0.1)を載せ、E-1 は在ることだけ見る** | 席は束の見出しどおり読んだと書いたのに meta が持っておらず、**正直な席が落ちていた**。注記に格下げするだけでは**束にも無い節名の捏造も通る**ので、meta に載せて「meta にも束の見出しにも無い節名」は従来どおり落とす(司令塔の (iii))。見出しは本文から機械で拾う(字面を手で並べない) |
| 4 | **§0.3 の `lastKey` を本文の実際の最後の行から取る** | inputs の一覧が節の**外**に在り、席が見た最後の行と meta が食い違っていた。一覧を節の中に移した(行数も sources + inputs になる) |

**測り**: 全体 **112 files / 2154 passed**・typecheck の赤 0(R4 の 6 本 + 触った R1・R2 の試験を含む)。
変異 **6 本すべてが狙った試験だけを赤くした**(素は 222 本 = R4 の 6 本 + seatInput・seatOutput・integration・hypothesis)。**予測の外れ 2 件(記録)**: M25(見出しを拾う関数を空にする)は render 側の試験だけを赤くした ― 検査側の試験は meta の fixture を使うので独立に守られている(M26 が担当)。M27(§0.3 の行数だけを戻す)は行数の試験だけを赤くした ― 本文の中身は変えていないので lastKey は動かない。**どちらも「1 つの変異が 2 つの層を同時に測る」と思い込んでいた。**

### 11.4 人間の判断を待っていること

1. **Gemini の鍵が無料枠**(429)。有料枠にしない限り Gemini 席は立たない。
2. **測り直しの費用**(直した後に 3 席で測ると 3〜4 ドル)。**上限は実行 1 回の累計に掛かる作りなので、回し直すたびに枠が改めて効く** ― 今日の合計を縛るなら、次の実行の上限を残額で渡す。
3. 次の束の候補(司令塔の提案、いまはやらない): 再依頼が高いのは束を丸ごと再送するため。Anthropic の prompt caching なら再依頼の入力はほぼ消える。呼び方が変わるので独立監査つきの別束にする。

### 11.5 独立監査の 3 回目: **REVISE** → 直して 4 回目へ(2026-09-30)

監査は凍結を機械で確かめ(13 ファイルの sha256 を開始時・終了時・`freeze2/SHA256.txt` の 3 方向で一致)、記録の数を**実物の `run_summary.json`・`checks.json`・`seat_*_error.txt` と全部照合して一致**、`schemas/` に差分 0(正本を変えていない)、`effectiveValueShape` を 3 社ぶん実行して形が完全に一致すること(Anthropic は `oneOf` を保つので `normalizeFreeForm` が両方を見ていることも)を確認した。そのうえで **1 件の実装の欠陥**を見つけた。

**欠陥: 「0.2 線の組」はデータの行を持つのに「見出しだけの節」に分類されていた。** `headingSectionsOf` は「`section()` で正式に登録されたか」だけを見ており、`data()` を呼んでいるかは見ない。0.2 は見出し + `data()` の形で書かれていて登録されていなかったので、**この節だけ E-1 の `lastKey` の照合が外れていた**(緩めたのは 0・0.1 だけのはずだった)。

**いちばん痛いのは、私の試験がその誤りを「仕様」として固定していたこと** ― `{ section: "0.2", lastKey: "ahead_cp" }` で通ることを試験が主張しており、**実装と試験が同じ誤った前提を共有していたので、変異では出ない**(変異は実装と試験の食い違いを探す道具で、両方が同じ向きに間違っているときは黙る)。**外の目が要る理由がここに出た。**

**直し**: 0.2 を 0.3 と同じく `section()` で正式に登録した(コードの直しは 1 か所。`headingSectionsOf` は自動で除く)。試験は (1) 0.2 がデータの節として `lastKey` を持つこと、(2) `headingSections` に入らないこと、(3) **見出しに見えてもデータの行が在れば `lastKey` を厳しく照合すること**を固定した。`headingSectionsOf` のコメントに「見ているのは登録の有無だけ ― データの行を書く節は必ず登録する」を明記した。あわせて監査の変異 L(枝が全部自由形 object のときの受け皿)も試験で閉じた。

変異 **2 本**(M28 = 欠陥そのものに戻す・M29 = 受け皿を外す)を当て、**M28 は 3 本、M29 は 1 本**の試験を赤くした(素は 225 本)。直した後の測り: 全体 **112 files / 2157 passed**・typecheck の赤 0。

**4 回目の監査は GO**(2026-09-30)。監査は同じ変異を**自分でも当てて**(他の席の結果を鵜呑みにしない)3 本赤を独立に確かめ、さらに 2 本足した。
1 本は「0.2 の新しい試験が本当に前方一致の判定を測っているか(見出しの枝を通っただけで緑になっていないか)」― 前方一致を外すと新旧 2 本が赤。
もう 1 本は「**将来また見出し + `data()` を登録なしで書いたら捕まるか**」― 本文の末尾に未登録の見出しとデータの行を足したら、
`headingSections` を `toEqual(["0","0.1"])` で**完全一致**で比べている試験が捕まえた。**監査の所見(記録として残す)**:
この安全網は `toEqual` の完全一致に依っている ― 将来誰かが `toContain` に緩めると失われる。**緩めない。**
本文の `heading()` / `section()` / `data()` / `prose()` を全行走査して、**同型の未登録の節が他に無い**ことも確かめられた。
