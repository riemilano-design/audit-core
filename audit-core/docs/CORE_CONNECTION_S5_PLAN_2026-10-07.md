# 将棋側 S-5(規則を kind と値の形に噛み合わせる + 所要の上限 + 工程の穴)の計画と予測 ― 直す前に封じる

> **封じた後は本文を変えない。** 訂正は日付つきの追記か結果文書に。予測を当てるために規則・窓・上限を動かさない。外れは外れのまま記録する。
>
> **前提**: 人間の決定(2026-10-07、S-4 の結果への「進めて」= 司令塔の意見の提案どおり): **S-5 = (b) Golden の書き直し + (c) H-1 + (d) H-3 + (f) HTTP の所要の上限を 1 つの封に、実 run は 1 回。** 入金してすぐやり直すのではなく、先に直してから同じ金額で多く測る。claude 席の v1.4 の効き目は 1 回では断定しない(次の run の目的は draft の経路)。
>
> **Base**: `3ee4d00`。Core 4 本は `f917f02` から不変。
>
> **① は済んでいる**: Golden c5 の期待値は S-4 の現状(H-12 の skip 行 58 件)で書き直し済み(`3ee4d00`、sha `26edee80…`、base_commit `e5d319f`、再照合 rc=0)。**この封から先の Golden の差は (c)(d) だけに帰属する。**

## 1. 読んで確かめた事実(予測の根拠。全部読むだけで測った)

| # | 事実 | どこで |
|---|---|---|
| 1 | H-1 の `collectValueNumbers` は number・配列・object を辿るが、**文字列の中の数字を集めない**。だから観測の値が `"5筋位取り中飛車"` でも、文に出た `5` は「observations の値に無い」になる | `lib/hypothesis.ts:319-344` |
| 2 | H-1 は `statement` と `counterEvidence.items[].text` の両方を見る。比(`%`・`割`・`倍`)は `derived` の再計算と突き合わせる別の枝 | `lib/hypothesis.ts` の `checkH1` |
| 3 | S-4 の gpt の封筒で H-1 が落ちた 3 件は全部、配列の名前の中の数字(`5筋位取り中飛車` の 5 が 2 回・`4六銀左戦法` の 4)。**その名前は H-9 で GROUNDED 済み**(観測の値そのもの) | S-4 結果 §3.3 |
| 4 | H-3 は kind を見ず、`counterEvidence.attempted !== true` を全部落とす。`items` と `result` の整合は別の 2 つの文 | `lib/hypothesis.ts:521-527` |
| 5 | H-4 は既に同じ問題を kind で解いている(`KINDS_WITHOUT_PREDICTION` = finding・action_candidate・unanswerable・needed_observation、`isV04OrLater` の下で) | `lib/hypothesis.ts:306,540` |
| 6 | 契約は `counterEvidence` を **required** にしている(kind によらず)。S-4 の gpt の `needed_observation` は `{attempted: false, items: [], result: "none_found"}` を入れてきた = **欄は出すが試みていない**と正直に書いた | `seat-output.llm.v0.2` の required、S-4 の封筒 |
| 7 | 既存 6 封筒(版 0.4)の kind: finding 35・unanswerable 6・**needed_observation 7**・answer_candidate 3・action_candidate 3・hypothesis 4 | 6 封筒を読んだ |
| 8 | 既存の期待値の H-1 の行 58 本中 **NG 15 本**(メッセージ 33 件、全部「数 N が observations の値に無い」型。他の型 0) | `c5_expectation.json` |
| 9 | 既存の期待値の H-3 の NG は **16 本**。内訳は `attempted` 型 **4 本**(needed_observation 3 + **action_candidate 1**)と `items`/`result` の整合型 12 本 | 同上 + 6 封筒 |
| 10 | `fetchWithRetry` は `AbortSignal`・timeout を渡していない。再送は 429 / 5xx / 接続の失敗で 1・4・16 秒の後に最大 3 回。S-4 で 1 試行が **50.8 分** | `lib/llmClient.ts:71-106`、S-4 結果 §2 |
| 11 | 1 回の HTTP が普通にかかる時間: gpt 71,834 ms(S-4、1 試行)・123,984 ms(S-3、2 試行)、claude 295,787 ms(S-3、3 試行)= 1 試行あたり **60〜150 秒** | `run_summary.json` 2 本 |
| 12 | 監査は実物の `out/` を持たない別木で測るので **Golden を回せない**。S-3 の a3・S-4 の b2 で「落ちない」と「記録が変わらない」を混同し、**監査も独立に同じ混同をした** | S-3・S-4 の結果、私(司令塔)の指示 |

## 2. S-5 の範囲

### 2.1 直す物(3 つ + 工程。予測は別々に立てる)

**(c) H-1: 検証済みの文字列の中の数字を、文の中の数として数えない**

- 新しい helper `collectValueStrings(value, out: Set<string>)`: 観測の値(`observations[].value` と `counterEvidence.items[].observations[].value`)を辿り、**文字数 2 以上**で、かつ `0-9 . , - + %` **以外の文字を 1 つ以上含む**文字列を集める(数字だけの文字列 `"25"` は集めない = 数の偽装を許さない)。配列・object は中を辿る。
- 新しい helper `maskVerifiedStrings(text, strings)`: `strings` を**長い順**に並べ、`text` の中の出現を全部 `□`(数字を含まない 1 文字)に置き換える。置き換えで数字がつながらないよう、空文字ではなく `□` にする。
- `checkH1` は、数を取り出す前に `statement` と各 `counterEvidence.items[].text` に `maskVerifiedStrings` を掛ける。**比(`%`・`割`・`倍`)の枝・メッセージの字・`allowed` の作り方は変えない。**
- **緩むのは「検証済みの文字列が文にそのまま出ている所の内側」だけ。** 観測に無い数を文に書く道は閉じたまま。

**(d) H-3: `counterEvidence.attempted` を kind で免除する**

- `KINDS_WITHOUT_COUNTER_EVIDENCE = new Set(["unanswerable", "needed_observation"])`(H-4 の隣に置く)。この kind のときだけ `attempted !== true` の文を出さない。**`items` と `result` の整合の 2 文は出し続ける。**
- **`action_candidate` は免除しない**(観測を持ち主張の形の文を書くので、反証の試みを求めるのは筋が通る)。既存の `attempted` 型 4 本のうち **1 本(`H-c5-gpt558b-007`)は NG のまま残る**。緑を増やすために範囲を広げない。
- 版で区切らない(H-12 と違い、これは kind と規則の噛み合わせの直しで、古い記録にも同じ規則が正しい)。

**(f) HTTP の 1 試行に所要の上限**

- `lib/llmClient.ts` に `HTTP_ATTEMPT_TIMEOUT_MS = 300_000`(= 5 分)を字で置く。`fetchWithRetry` の各 `fetch` に `AbortSignal.timeout(…)` を渡し、**時間切れは今までの「接続の失敗」と同じ扱い**(1・4・16 秒の後に再送、最大 3 回)。`ClientDeps` に試験用の任意の上書き(`attemptTimeoutMs`)を足す。
- 最悪の所要は 1 席 4 試行 × 5 分 + 待ち 21 秒 ≒ **20.4 分**(今は上限なし)。数は字で留めて試験で見る。

**(工程) 記録が変わるかを凍結の時点で測る**

`docs/AGENT_PROTOCOL.md` の「監査の確認項目」の直後に 1 段落を足す: **検査・行・欄を足す(または消す)変更では、凍結の時点で司令塔が Golden Master を 1 回回し、差の件数を監査に渡す。** 監査は実物の `out/` を持たない別木で測るので Golden を回せない。**「規則が掛からない」と「記録が変わらない」は別**(skip でも 1 行出る。S-3 の a3・S-4 の b2 で 2 回踏み、監査も独立に同じ混同をした)。

### 2.2 試験

(c): 文字列の覆いの単位試験(名前の中の数字が許される / 数字だけの文字列 `"25"` は覆わない / 配列の要素の文字列 / 覆いで数字がつながらない / 観測に無い数は今までどおり落ちる / 比の枝は不変)。(d): kind 4 通り × `attempted` true/false × `items`/`result` の整合(`action_candidate` が免除されないことを字で留める)。(f): 上限の数を字で、時間切れが再送され最大 3 回で諦めること(差し替えた `fetch` と `sleep` で)。既存試験で字で留めた件数の書き換えは可。

### 2.3 直さない物

Core。`audit-core/`。schema(新版も旧版も)。H-12 の規則。`additionalProperties`。E/I の規則。Golden の期待値(**①で書き直し済み。S-5 の中では触らない** ― (c)(d) で出る差は人間が ⑦ で決める)。`.env`。整理役の指示文。席の指示文(v1.4 のまま。**v1.5 は作らない**)。(S-4 の) draft が `heldBack` を読むか。E-5 の字面。gemini。組版・納品。

### 2.4 測り方(**0 円の計測を先に、実 run は最後**)

**先に 0 円で測る**(S-4 の gpt の封筒が残っているので、(c)(d) の効き目は金を使わずに測れる):

1. `seatOutputCheck.ts --packet` を **S-4 の gpt の封筒**(`llm-seats-s4/effffa3e-20261006-1/seat_gpt.json`)に当てる。
2. Golden c5 `--expect`(書き直さない。差の一覧を保存するだけ)。
3. `run_core_path_shogi.py --seats-dir llm-seats-s4`(H-9 は変えていないので不変のはず)。
4. `hypothesisCheck.ts --packet` を既存 6 封筒に当てて、H-1・H-3 の行が変わる項目を数える。

**実 run は 1 回**(`llm-seats-s5/`、`--runs 1`、gemini 保留、v1.4、c5 の packet/request、整理役 v1)。**2 つの前提が揃ってから**: (i) 人間が Anthropic API に入金する(claude 席と整理役が送れない状態では S-4 と同じ結果になる)、(ii) 人間が費用上限を承認する(S-4 の承認は S-4 の 1 回に対するもの。推し: 同じ 5 USD)。**揃わなければ実 run は回さず、0 円の計測と結果文書で止める。**

## 3. 予測(封じる。0/1 = 二値、幅 = 席の出力に依るので粗い)

### 3.1 (c)(d) の効き目 ― 0 円で測れる分

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| p1 | S-4 の gpt の封筒に `seatOutputCheck --packet` を当てた指摘の数 | **4 → 0**(H-1 の 3 件は覆いで消え、H-3 の 1 件は kind の免除で消える) | 0/1 |
| p2 | Golden c5 の rc | **1**(差が出る) | 0/1 |
| p3 | Golden の差の件数 | **5 件**(H-1 の行が変わる項目 2 = `H-c5-claude268d-005`・`H-c5-claude558b-004`、H-3 の行が変わる項目 3 = `H-c5-gpt0f1b-006`・`H-c5-claude52ae-010`・`H-c5-gpt558b-006`)。**機械的に導いた**(私の写しの数の取り出しは本物の `extractNumbers` と違う ― 全角・比の扱いが別なので、ここが外れる余地) | 0/1 |
| p4 | 差の中身 | **全部 `lines` の中身の差で、長さの差 0**(行は増えも減りもしない。NG → ok に変わるだけ) | 0/1 |
| p5 | `status` / `return_code` | **6 封筒とも不変**(`fail` / 1。どの封筒にも他に NG の項目が残る) | 0/1 |
| p6 | 他の欄(`identity`・`packet`・`seat_runs`・`g8`・`g9.exit_gate`・`check_answer`・`check_structure`・`seatOutputCheck`・`integrationCheck`) | 差 **0** | 0/1 |
| p7 | `H-c5-gpt558b-007`(action_candidate)の H-3 | **NG のまま**(免除しない) | 0/1 |
| p8 | 既存 6 封筒の H-1 のメッセージの合計 | **33 → 31**(2 件消える) | 0/1 |
| p9 | 既存 6 封筒の H-3 の NG の本数 | **16 → 13**(3 本消える) | 0/1 |
| p10 | Core の経路(`--seats-dir llm-seats-s4`)の Claim 33 と state | **不変**(H-9 を触らない) | 0/1 |
| p11 | `audit-core/` 差分 | 0 | 0/1 |

### 3.2 (f) 所要の上限

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| t1 | 上限の数が字で在り、試験が留める | 在る | 0/1 |
| t2 | 時間切れが再送され、4 回目で諦める(差し替えた `fetch`) | そうなる | 0/1 |
| t3 | 実 run の 1 席の所要 | **60〜400 秒**(S-4 の 50.8 分のような伸びは起きない。起きたら上限が効いていない) | 幅 |

### 3.3 実 run(前提が揃ったときだけ。S-4 で測れなかった分)

| # | 観測対象 | 予測 | 種別 |
|---|---|---|---|
| r1 | claude 席が封筒を返す | **返る**(残高が入れば。**返っても v1.4 の効き目とは断定しない** ― 1 回では揺れと区別できない) | 0/1 |
| r2 | claude の試行の理由に `items2` / `items` の文字列化 | **無い** | 0/1 |
| r3 | 連続する試行で同じ理由の繰り返し | **0**(再試行が無ければ測れない、と先に書く) | 0/1・粗い |
| r4 | 整理役が走り、観測 0 の項目が I-1(全項目ちょうど 1 回)を通る | 通る | 0/1 |
| r5 | 整理役の代表に観測 0 の束が出たときの H-12 | **NG 0** | 0/1(束が出なければ測れない) |
| r6 | `exitSelect --draft` が出る | 出る、`adoptedBy: null` | 0/1 |
| r7 | draft の `items` のうち `aggregateIds` が空の候補 | **観測 0 の項目が束になって H を通った数と同じ**(0〜3) | 幅 |
| r8 | draft の rejected の割合 | **0〜50%** | 幅・粗い |
| r9 | 2 席の H-9 の VM + PNF | **0〜4** | 幅 |
| r10 | 配列のまま GROUNDED | **1 件以上**(S-4 で gpt が 4 件出した) | 0/1 |
| r11 | 実費の合計 | **2.3〜4.8 USD**(claude が試行 1 で通れば 2.8 前後) | 幅 |
| r12 | 上限で止まる / 上限を超える | 止まらない / 超えない | 0/1 |

### 3.4 その他

| # | 観測対象 | 予測 |
|---|---|---|
| g1 | typecheck 新しい赤 | 0 |
| g2 | vitest | 既存は落ちない(字で留めた件数の書き換えを除く)。新規 **+10〜26** |
| g3 | 行数(本体、試験を除く) | +40〜110 |
| g4 | 冊子の変わるページ | 0(設計の帰結) |
| g5 | 違う 0/1 の欄 | **0〜3**(疑うのは p3(写しと本物の数の取り出しの差)・p8・r1) |

## 4. 手順(3 役)

1. ① Golden の書き直しは**済み**(`3ee4d00`)。この文書を封(コミット)。
2. 実装担当(§2.1〜2.2。**作業木を書き換える git 操作を使わない。API の鍵を使わない(`--dry-run` も禁止)。席を回さない。deliver・Golden を実物で回さない**。合成材料だけ。コミットしない)。
3. **司令塔が凍結し、§2.4 の 0 円の計測 4 本を凍結の時点で回して、差の件数を監査に渡す**(工程の直しの初回適用)。
4. 独立監査(別木の変異: 覆いを外す・数字だけの文字列を覆う・`action_candidate` を免除に入れる・H-3 の整合の 2 文を消す・上限の数を変える)→ GO でコミット。
5. **前提 2 つ(入金・上限の承認)が揃えば**実 run 1 回(§2.4)→ 項目別に §3 と照合。揃わなければ 0 円の分だけで結果文書を書き、実 run は次の決定へ回す。
6. 結果文書 → 人間の判断(⑦ Golden を (c)(d) の後の状態で書き直すか、次)。

## 5. 止まる所

Golden の差が **5 件でない**ときは止めて表にする(直しが思ったより広い・狭い)。`status`/`return_code` が動いたら HUMAN(封筒の判定が変わる = 緩め過ぎ)。実 run で上限に当たったらそこまで。Core の変更が要ると分かったら HUMAN。

## 6. この文書がしないこと

Core の変更。schema の変更。Golden の書き直し(① は済み、(c)(d) の後は人間)。席の指示文の版上げ。入金の判断。費用上限を司令塔が決めること。`action_candidate` を H-3 の免除に入れること。claude 席の v1.4 の効き目を主張すること。
