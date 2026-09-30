# STEP R1 ― render: packet + request → `seat_input.md`(3 席 LLM API の最初の束。2026-09-30、実験席)

**位置づけ**: [PLAN_LLM_SEATS_API](PLAN_LLM_SEATS_API_2026-09-30.md) §1・§8 の「render(S-2)」。packet 束 C(532e320、packetId `22aee8fe696d0262`)が閉じたので着手。順は render → seat-output v0.1 と hypothesis v0.4 の契約検査 → integration(司令塔 2026-09-30)。**この束は LLM を呼ばない**(鍵はまだ無い)。
**独立監査つき・コミットはパス指定・鍵をログ・out・記録に書かない。**

## 0. 顧客の PDF にどう出るか(先に書く)

**今は何も変わらない。** 冊子は今のままの数で出る。この束が作るのは、3 席の LLM に渡す**同一バイトの入力 1 本**と、その入力の目次・sha・省いたものの一覧(`seat_input.meta.json`)。将来、席の発見が検証を通り人が採用したとき、本編の文から packet まで戻る道の**最初の輪**(席が見た入力 = packet の写し)が固定される。

## 1. 作るもの

| 物 | 場所 | 中身 |
|---|---|---|
| lib | `scripts/playtest/lib/seatInput.ts` | `renderSeatInput({packet, request, instructionBytes, runId, omit?})` → `{text, meta}`。**抽出だけ**(値は `JSON.stringify` の写し。再計算・丸め直し・補完をしない)。止まる条件(§3)は例外で返す |
| 試験 | `scripts/playtest/lib/seatInput.test.ts` | §5 |
| CLI | `scripts/playtest/seatInput.ts` | `npx tsx scripts/playtest/seatInput.ts --packet <packet.json> --request <request.json> --instruction docs/LLM_SEATS_INSTRUCTION_v1_2026-09-30.md --run-id <id> --out-dir <dir>` → `seat_input.md` + `seat_input.meta.json`。問題があれば終了コード 1 |
| 記録 | [LOG](EXPERIMENT_LLM_DISCOVERY_25GAMES_LOG.md) §7(新設) | 5 人目の packet での実測(§4)。sha と数だけ。顧客の材料はコミットしない |

計画 §3.5 は `scripts/playtest/llmSeats/` を挙げたが、**リポジトリの慣例(CLI は `scripts/playtest/*.ts`、lib は `lib/*.ts`、試験は隣)に合わせる**。

## 2. `seat_input.md` の形(節の順は計画 §1.1。小さい節を先、大きい表を後)

**差し替え(2026-09-30、R2 の中。司令塔の決定)**: §2 の集計は **数ごとに 1 行**(分数は `aggregates.<id>.numerator` と `.denominator` の 2 行、単独の数は `.value`。26 集計 → 37 行)。名前・母集団・出どころの局は分子の行にだけ書く。理由と実測は LOG §7 の差し替えの行。以下の図の「集計(aggregates、26 行)」「aggregates.<id>」はこの差し替えで読み替える。

```
<1 行目>  対象: 〇〇さん(符号 c5)。持ち時間 180 秒の組・25 局。線の組: ahead_cp=300 centipawns; long_think_sec=10 seconds; …   ← S-2(request と provenance.thresholds から。無ければ止まる)
<指示文>  docs/LLM_SEATS_INSTRUCTION_v1 のバイト列そのまま(sha256 が固定値 3b09bec2… と違えば止まる)
# (A) 依頼主の問いと範囲(request)
  q1: <原文の写し>(via: relayed = 人が中継した伝聞)  /  requestedScope: games 25・timeLimitSec 180・note
  固定文: この問いに合わせて事実の作り方を変えていない(packet は request を参照しない)。
# (B) 材料の束(packet の写し。packetId・schemaVersion・pipelineVersion・generatedAt)
## 0. 読み方
  0.1 数はすべて packet からそのまま写した / 省いたもの(§2.1)/ 含めていないもの(現行ルートの出力)
  0.2 鍵の意味(packet の schema の description と、線の組の値。閾値は仮置き)
  0.3 provenance.sources(5 本: 種類・エンジン設定・入力の本数)と inputs の path の一覧(符号 c5 を含む。sha は省く)
## 1. 局(facts.games、25 行)              gameId no side result ending ownPlyCount totalPlyCount timeLimitSec mirrored aheadAtAnyPoint
## 2. 集計(aggregates、26 行)              id name 値(numerator/denominator または value)unit population(from・where・unit)numeratorWhere timeDependent recountable recountNote derivedFrom
## 3. 時間(facts.time、25 行)               局ごと
## 4. 崩れ(facts.collapse、155 行)          gameId ply beforeCp afterCp bandBefore bandAfter kind
## 5. 分かれ道(facts.branches、404 行)      gameId ply displayPly top1Usi actualUsi top1Side actualSide top1Tags actualTags oppositeSide topGapCp actualGapCp firstVisibleNodes shallowVisible
## 6. 戦型の機械認識(facts.recognition: rows 25 行 + definitions 114 本)  すべて draft。definitions は id name side family reviewStatus recognitionPattern を写す
## 7. 本人の手(facts.moves、1242 行)        局ごとに 1 行: `ply:usi piece [drop] spentSec scoreCp [F] [C] [phase]` を空白区切り(F = isFork、C = collapsed)
## 8. 候補 5 つ(facts.engine、1033 局面)    局面ごとに 1 行: `ply top1Usi actualUsi scoreCp | usi scoreCp; usi scoreCp; …`(candidates の順のまま)。**pv と sfen は省く**(§2.1)
(束はここまで。合言葉: <runId の先頭 8 桁>)
```

- **同じ値は同じ字で**: 数は `JSON.stringify` の写し(小数の桁も元のまま)。列挙(tags・where)は `+` または `;` 区切りで、空は `-`。`null` は `null` のまま。
- **packetRef の文法**(計画 §8.1 (ii)): 各節の見出しに、その節の行が packet のどこか(`facts.branches[]`・`aggregates.<id>`)を書き、集計の行には `aggregates.<id>` をそのまま id 列に置く。席はこれを `observations[].packetRef.path` に写す。
- 節の目次(`meta.sections[]`: 節番号・見出し・行数・最後の行の鍵)を `seat_input.meta.json` に書く。到達検査(次の束)がこれと席の `reach.sections` を照合する。

### 2.1 省くもの(packet にはある。`meta.omitted[]` に列挙し、束の §0.1 にも書く)

| 省く | 大きさ(実測、詰めた JSON) | 理由 |
|---|---|---|
| `facts.engine[].candidates[].pv` | 約 255 KB(31,107 手) | 実験 1 も省いた。席は読み筋を根拠にしない(数は引くだけ) |
| `facts.engine[].sfen` | 約 88 KB | 実験 1 も省いた。局面は `gameId + ply` で packet に戻れる |
| `provenance.inputs[].sha256`・`bytes` | 169 本 | path だけ写す(符号 c5 は載せてよい ― 計画 §1.1 の監査の条件) |
| `facts.*[].src`・`src*` | ― | 出どころの符号。`provenance.sources` を §0.3 に写すので行ごとには要らない |
| `aggregates[].derivedFrom` の局の列 | ― | **省かない**(席が「どの局から」を引けるように)。ただし 25 局全部なら `all` と書かず列挙する(写しの規則) |

省いた後の見込み: 詰めた packet 1,000 KB − 255 − 88 ≈ 650 KB の JSON を md の行に組むと **300〜350 KB(概算 10〜12 万トークン)**。実験 1 の束 405 KB と同程度。**実測は §4 で。** count-tokens は鍵が無いので、この束では **字数 ÷ 3 の概算だけ**を meta に書き、`tokenEstimate.method: "chars/3"` と明記する。

### 2.2 実験 1 の束に在って packet v0.1 に無いもの(この束では作らない。**「実験 1 の再現」の比較の注記**として記録)

Failure Event の詳細(§2)・escapeScenes・`time.bySpent` の 4 段全部と `byLeft`・read の ladder(5 段)・scene 行・`tagCrossTable`・summary 行・final_positions。packet が唯一の事実入力なので、**render は packet に無いものを他のファイルから足さない**(人間の直し 1)。初回の実行の比較(計画 §6.0)では「入力が実験 1 より狭い」を差の説明の候補として先に書く。

## 3. 止まる条件(黙って送らない。例外の文に何が無いかを書く)

| 条件 | どう見るか |
|---|---|
| packet が schema を通らない | `validateObservationPacket` + `observationPacketProblems`(既存。重ねて作らない) |
| request が schema を通らない / `customerRef` が packet と違う / `requestedScope.timeLimitSec` が `facts.games[].timeLimitSec` の共通値と違う | `validateObservationRequest` + `requestAgreementProblems`(既存) |
| `provenance.thresholds` が空 | schema の `minItems: 1` で既に落ちるが、render も 1 行目を組む前に見る |
| 指示文の sha256 が固定値と違う | `instructionSha256` を引数で受け、違えば止まる(周をまたいで席の答えを比べるため。変えるときは版を上げる) |
| 符号以外の識別子 | **欄の型で見る**(司令塔 2026-09-30、H-8 の一覧の家族): packet と request の**すべての文字列の値**を歩き、(a) `@` を含む、(b) `http://`・`https://`、(c) 人名の一覧(`check_answer.py` の `BANNED_WORDS` と H-8 が読む一覧を同じ口から読む)のいずれかに当たれば止まる。**enum の欄(side・result・unit …)と USI・SFEN・id の欄は型で除く**(字面の一覧を本文に当てない ― 字面の試験は自分の説明文に当たる) |
| `runId` が無い・8 桁未満 | 合言葉が作れない |

## 4. 校正と変異(予測を先に書く。5 人目の packet は scratchpad に生成済み: packetId が束 C の記録と一致 `22aee8fe696d0262`)

**校正(既知の正解)**:
1. **数の包含**: `seat_input.md` の (B) に出る数値トークンの多重集合 ⊆ packet の値の多重集合(`JSON.stringify` の写しなので、字面で一致するはず)。予測: 差 0。差が出たら render の書き方(区切り・桁)を直し、packet は触らない。
2. **行数**: 各節の行数 = packet の配列の長さ(25 / 26 / 25 / 155 / 404 / 25+114 / 1242 局面は局ごと 1 行なので 25 行・1033 局面は 1 行ずつ)。予測: 全部一致。
3. **26 の集計の値**が束 §2 に 1 つ残らず出る(65/107 … 0/2)。予測: 26/26。
4. 実名 0・`@` 0・絶対パス 0(`/Users`)。予測: 0・0・0。
5. 同じ packet・同じ runId で 2 回 render して **バイト一致**(決定性)。予測: 一致。runId を変えると末尾の 1 行だけ変わる。

**変異(先に予測、`-X pycache_prefix` の教訓は TS なので不要。校正の道具を「わざとずらした写し」で校正する)**:
| 変異 | 予測 |
|---|---|
| packet の `aggregates[0].numerator` を 65 → 66 に | 校正 3 が 65 を見つけず赤。packet 自体は `packetIdProblems` で先に落ちる(封) ― **両方が赤いこと**を見る |
| `seat_input.md` の 1 つの数を手で +1 | 校正 1 が「packet に無い数」を 1 つ挙げて赤 |
| request の `timeLimitSec` を 600 に | 止まる(既存の `requestAgreementProblems`) |
| request の `customerQuestions[0].text` に `x@y` を混ぜる | 止まる(欄の型の検査) |
| 指示文の 1 バイトを変えた写し | 止まる(sha) |
| `provenance.thresholds` を `[]` に | 止まる(schema と render の両方) |

## 5. 試験(vitest、`npx vitest run --root scripts/playtest`)

- 最小の packet を**試験の中で組み**、`validateObservationPacket` を通す(通らない fixture で試験しない)。局 1・moves 2・engine 1・branches 1・collapse 1・time 1・recognition rows 1 + definitions 1・aggregates 1・thresholds 1。
- 見るもの: 節の順と行数 / 数の包含(校正 1 を関数にして試験からも呼ぶ)/ 省いたもの(`pv`・`sfen` が本文に出ない)/ 止まる条件 6 つが**それぞれ**止まる / 決定性 / 合言葉が末尾の 1 行にだけ出る / `meta.sections[].lastKey` が本文の最後の行と一致。
- **字面の試験を書いたら、消す変異で赤くなるか確かめる**(2026-09-29 の教訓)。

## 6. 触らないもの

`deliver.ts`・`report-pdf/`・`out/c5/deliver1/`・packet を作る道具(`observationPacket*.ts`)・schema 2 本・`answer_menu.json`・指示文 v1(sha 固定)・CLAUDE.md。**`out/` に書かない**(実測の出力は scratchpad。記録は sha と数だけ)。

## 7. 受け入れ基準

1. 校正 1〜5 が予測どおり(差 0・行数一致・26/26・0/0/0・バイト一致)。
2. 変異 6 本が予測どおり赤・止まる。
3. `npx vitest run --root scripts/playtest` 緑、`npm run typecheck:scripts` は既知の赤 10(P-84)のまま増えない。
4. 5 人目の packet での `seat_input.md` の大きさ(バイト・字数・概算トークン)と sha256 を LOG §7 に記録。**実物は scratchpad に置き、コミットしない。**
5. 独立監査 GO → パス指定でコミット(lib・試験・CLI・LOG・この計画)。

## 8. 決めていない点(司令塔へ)

1. **5 人目の request.json の原文**: 顧客の問いの原文はどこにも写されていない(設計セッションの指示書は「普段と違う型の局が影響しているか」と要約)。校正の実行では scratchpad に `via: "relayed"`・`note: "原文ではない(正本の要約)"` の request を置く。**正式な request.json(原文)は人が置く**(このセッションは本人に聞かない・原文を作らない)。
2. §2 の節の順(小さい節 → 大きい表)と、集計(§2)を局(§1)の直後に置くこと。実験 1 は集計相当を §3 に置いていた。席が数を引くときに最初に見る場所なので前に出した。
3. `facts.moves` を局ごと 1 行に畳む書き方(1242 行を 25 行に)。読みにくければ 1 手 1 行(1242 行、約 60 KB 増)。
