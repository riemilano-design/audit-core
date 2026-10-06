# 将棋側 S-4(unanswerable を契約で言えるようにする + claude 席の封筒を器に届かせる)の結果 ― 実 run は途中で止まった

**日付**: 2026-10-07 **計画と予測の封**: [CORE_CONNECTION_S4_PLAN_2026-10-06.md](CORE_CONNECTION_S4_PLAN_2026-10-06.md)(`66052e1`、sha `fee52400…`、不変) **監査**: **GO**(独立、2026-10-06。凍結 16 件の sha 一致(前後)、範囲 §2.1〜2.2 内、新版 4 本は生テキスト diff で 1〜2 行差、v1.4 の diff は 4 ブロックと字まで一致、別木の変異 **7 本が全部予測どおりの試験だけ赤**。非ブロッキング 2 件は §7.4) **コミット**: `e5d319f`(将棋側 11 ファイル + 新規 5) **実 run**: `effffa3e-20261006-1`(`scripts/playtest/out/c5/llm-seats-s4/`、gitignore。司令塔が 03:31:14 → 04:23:16 に 1 回。人間が費用上限 5 USD を承認済み)

> **この文書の要点を先に書く。** (1) **実 run は 1 席(gpt)だけで終わった。** claude 席と整理役は Anthropic API の **残高不足(HTTP 400)**で送れず、実費は 0.847 USD(上限 5 の 17%)。**コードの欠陥ではなく、外部の口座の状態。** (2) それでも **S-3 で未検証だった 2 点が解けた**: 観測 0 の `needed_observation` が契約を通り、**配列のままの観測 4 件が GROUNDED** で Core まで届いた。(3) **Golden c5 が rc=1 になった**(差 58 件は全部「行数 +1」)。封じた §5 の「止まる所」なので、**Golden の扱いは人間が決める**。(4) 予測 33 欄: 当たり 23・外れ 4・**測れない 6**。

## 1. 何を直したか(コミット `e5d319f`。将棋側 11 ファイル +403/−19、本体 5 ファイル +66/−10、`audit-core/` 0)

| 計画 | 直し |
|---|---|
| (b) 契約 | `hypothesis.v0.5`・`seat-output.llm.v0.2`・`integration-input.v0.2`・`integration.llm.v0.2` を新設(旧版の複製で `observations` の `minItems` を外しただけ。hypothesis は版の const を 0.5。旧版は残す)。読み込み先 4 か所を新版に。`KNOWN_HYPOTHESIS_SCHEMA_VERSIONS` に 0.5、`SEAT_HYPOTHESIS_SCHEMA_VERSION`(`seatOutput.ts:17`)を 0.4 → 0.5。新検査 **H-12**(版 0.5 以上だけ。`unanswerable`/`needed_observation` は `neededObservation` の 3 欄が必須で観測 0 可、他の kind は観測 1 件以上) |
| (c1) 指示文 | `docs/LLM_SEATS_INSTRUCTION_v1.4_2026-10-06.md` = v1.3 + 4 ブロック(版名・21 行目の置き換え・`itemId` は `S-001` の形・最上位の鍵 5 つで `items` は 1 つ、配列を文字列にしない)。sha `8bd603ef…` |
| (c2) 再試行 | `retryUserText` に「落ちた欄以外は形が合っていました…」の 1 文(字で固定)を理由の一覧の前に |

門: typecheck 新しい赤 0、vitest **2333 → 2352**(+19)、`git diff --check` 0。

## 2. 実 run の記録(1 回。途中で止まった)

| | gpt(gpt-5.5) | gemini | claude(claude-opus-5) | 整理役(claude-opus-5) | 合計 |
|---|---|---|---|---|---|
| `--dry-run` の見込み | 1.2470 | 保留 | 1.0970 | 0.8470 | **3.19**(上限 5) |
| 実測 | **通過(試行 1)**・項目 6・指摘 4 | 送っていない | **空席 `http_failed`** | **無し `http_failed`** | ― |
| 実費(USD) | **0.847** | 0 | **0**(送れていない) | **0** | **0.847**(`capReached: false`) |
| 所要 | 71,834 ms | ― | 3,049,829 ms(= 50.8 分) | ― | 03:31 → 04:23 |

**claude 席と整理役が落ちた理由(記録のまま)**: `HTTP 400: {"type":"error","error":{"type":"invalid_request_error","message":"Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits."}}`。整理役は `count_tokens` の段でも同じ 400。**schema も封印語も検査も、この 2 つについては測れていない**(送れていないので)。

**付随して分かった運用上の事実**: claude 席の 1 回の試行に **50.8 分**かかった(`httpAttempts: 4`、最後の status が 400)。`lib/llmClient.ts` の `fetchWithRetry` は `AbortSignal`・timeout を渡していないので、**つながったまま返らない接続があると 1 試行が何十分でも伸びる**。再送の待ちは 1・4・16 秒なので、50 分の大半は接続の待ち。費用は増えないが、1 回の実 run の所要が読めなくなる。直すなら別に封じる(§6 の (f))。

## 3. 測れた物(gpt の 1 封筒)

### 3.1 S-3 で未検証だった 2 点が解けた

**(i) 観測 0 の `needed_observation` が契約を通った**(予測 b3。S-3 では契約が塞いで 0 件だった)。

```
kind: needed_observation / observations: [] / schemaVersion: 0.5
statement: 本人が普段指さない戦型として採用した局の一覧は束に無い。
neededObservation.what: 本人が普段指さない戦型として採用した局の一覧
neededObservation.whyNotInPacket: 束には戦型の機械認識と機械分類はあるが、本人の通常採用戦型や意図的な採用の印は無い。
neededObservation.howToMeasure: 対局ごとに本人申告または事前の通常採用戦型リストと照合して、普段外として採用した局に印を付ける。
```

H-12 の NG は **0 件**(他の kind で観測 0 の濫用も 0 件)。**「束からは答えられない」が初めて構造として出力に残った。**

**(ii) 配列のままの観測が GROUNDED で Core まで届いた**(予測 c6。S-3 では claude の失われた封筒にしか無く未検証だった)。

| 観測 | 値(配列のまま) | H-9 |
|---|---|---|
| `facts.recognition.rows[3].names` | `["英ちゃん流中飛車","5筋位取り中飛車","角換わり腰掛け銀"]` | GROUNDED |
| `facts.recognition.rows[12].names` | `["忍者銀"]` | GROUNDED |
| `facts.recognition.rows[16].names` | `["英ちゃん流中飛車","5筋位取り中飛車","角換わり腰掛け銀"]` | GROUNDED |
| `facts.recognition.rows[23].names` | `["早繰り銀","4六銀左戦法"]` | GROUNDED |

**配列の写しは S-3 の描画の直し((b1) JSON の字面)と v1.4 の「配列はそのまま配列で」が揃って初めて成立した。** 席 → packetRef → H-9 → Core の経路を、数でない値が通った初めての記録。

### 3.2 検査と Core

| 照合 | 結果 |
|---|---|
| H-9(自前の再導出、観測 20 件) | **GROUNDED 20・VM 0・PNF 0** |
| Core の経路(`run_core_path_shogi.py --seats-dir llm-seats-s4` → [s4_first_run_core.json](../fixtures/shogi/s4_first_run_core.json)) | Claim **33** = 観測 20 GROUNDED + counterEvidence の観測 13 UNVERIFIABLE(`no_packet_ref(H-9 out of scope)`)。自前の再導出と **20/20 一致・不一致 0** |
| `seatOutputCheck.ts --packet`(gpt) | 指摘 **4**。checks.json と一致 |
| 封印語(E-1) | **12/12 一致** |
| H-12 の行(E-3) | 0 |
| 埋め草の印 | 0 |
| `integrationCheck.ts --packet` / `exitSelect.ts --draft` | **回していない**(`integration.json` が無い。整理役が送れなかった) |

### 3.3 E-3 が初めて中身のある H-\* の行を出した ― 新しい構造の穴が 2 つ

S-3 では E-3 の H-\* の行は 0 だった(NG が無かった)。S-4 の 4 件は全部、**規則が kind や値の形と噛み合っていない**型:

```
E-3: items[3] H-1: statement: 数「5」が observations の値に無い   ← 「5筋位取り中飛車」の 5
E-3: items[3] H-1: statement: 数「5」が observations の値に無い   ← 同じ名前が 2 回出る
E-3: items[3] H-1: statement: 数「4」が observations の値に無い   ← 「4六銀左戦法」の 4
E-3: items[4] H-3: counterEvidence.attempted が true でない        ← needed_observation の項目
```

**(iii) H-1 は形の名前に含まれる数字を「文の中の数」として数える。** 席は配列の名前を忠実に写した(= S-4 で通したかったこと)のに、その名前に数字が入っているせいで H-1 が落ちる。**(ii) の成功と同じ項目が、別の検査で落ちている。** [記憶 `gate-counts-non-claims-as-numbers`] と同じ根だが、今回は**配列の名前の写しという、まさに通したい道で起きた**。

**(iv) H-3 は `needed_observation` の項目にも `counterEvidence.attempted` を要求する。** 根拠が束に無いから観測 0 にした項目に、反証の試みを求めている。**c3(S-3)で見つけた「規則が kind と噛み合わない」構造が、観測の側を直したら反証の側に出た。** H-4 は `KINDS_WITHOUT_PREDICTION` で同じ問題を既に解いており、H-1・H-3 にも kind の扱いが要る。

## 4. Golden c5 が rc=1 になった(封じた「止まる所」)

| 事実 | 値 |
|---|---|
| `--expect` の rc | **1**(S-3 までは 0) |
| 差の件数 | **58**(= 既存 6 封筒の全項目数とちょうど同じ) |
| 差の中身 | **全部 `g9.hypothesisCheck.<run>/<seat>.items[*].lines` の「長さ 期待 N / 実測 N+1」** |
| 他の欄 | `identity`・`packet`・`seat_runs`・`g8`・`g9.exit_gate`・`check_answer`・`check_structure`・`seatOutputCheck`・`integrationCheck` 差 **0** |
| `status` / `return_code` | 差 **0**(6 封筒とも `fail` / 1 のまま) |

**原因**: Golden は項目ごとに `validateHypothesisLine` の結果を `checkResultLines` で 1 行ずつ字にして `lines` に積む。`checkResultLines` は **skip でも 1 行書く**(`"H-12 skip …"`)。H-12 は既存 6 封筒(全部版 0.4)では落ちないが、**行としては必ず現れる**。だから 58 項目すべてで行数が 1 増えた。

**予測 b2「rc=0 のまま」は外れ。** 外れの理由は私(司令塔)の推論の誤りで、**「落ちない」と「現れない」を混同した**。S-3 の a3 の外れ(「E-3 が走る」と「H-\* の行が出る」の混同)と**同じ型を 2 回続けた**。監査も「期待値に H-12 の文字列が 0 件・既存封筒は全部 0.4」から「Golden への影響は無い」と結論しており、**同じ混同を独立に 2 人がした**。

**この差は顧客の冊子には届かない**(g8・出口の門・組版はいずれも差 0)。

## 5. 予測との照合(封 §3 の 33 欄)

| 判定 | 数 | 欄 |
|---|---|---|
| 当たり | **23** | b1・b3・b4・b5・b8・b9 / c1・c5・c6・c7・c8・c9 / r1 / f1・f4・f5 / g1・g2・g4・g5・g6・g7・g8 |
| 外れ | **4** | **b2**(Golden rc=0 → rc=1)・**c4**(空席 0 → claude が空席。理由は残高で schema ではない)・**f2**(実費 2.3〜4.8 → 0.847)・**f3**(claude の実費 0.9〜2.0 → 0) |
| 測れない | **6** | b6(観測 0 の項目が整理役の入力を通るか)・b7(draft の `aggregateIds` 空の候補)・c2(claude の試行が schema を通るか)・c3(`items2`/文字列が消えたか)・r2(再試行の往復。gpt は再試行なし)・g3(draft の rejected の割合) |

当たりの内訳で記録に値するもの: **c1**(gpt が試行 1 で通った。v1.4 で `itemId` の形を書いたため)、**c6**(配列のまま GROUNDED 4 件)、**b3**(観測 0 の項目 1 件)、**b8**(Core と 20/20)、**g6**(vitest +19 で幅の中。4 段続けて下に外していたので上を広げたのが当たった)。

外れの向き: **b2 は私の推論の誤り**、**c4・f2・f3 は外部の口座の状態**で、席の挙動でも実装でもない。

## 6. 人間の判断

| # | 問い | 司令塔の推し |
|---|---|---|
| (a) | **Anthropic API の残高**。claude 席と整理役が送れないまま。入金して S-4 の実 run をやり直すか | **やり直す価値はある**(c2・c3・b6・b7・g3・r2 の 6 欄がそこでしか測れない。gpt の分は測り終わっているので、次は claude が立つかだけを見る)。費用は人間。**入金は人間しかできない** |
| (b) | **Golden c5 の 58 件**。(i) 現状(H-12 の skip 行入り)で書き直す、(ii) H-12 を Golden の `lines` から外す(`checkResultLines` が skip を書かない、または Golden 側で skip を落とす)、(iii) 既存封筒を 0.5 に上げ直す | **(i) を推す**(次の比較の基準として記録する。S-1・S-2 と同じ扱い)。(ii) は「黙る検査」を作る方向なので避ける。ただし**書き直すかは人間**(⑦ の規則) |
| (c) | **H-1 が形の名前の数字を数える**(§3.3 の (iii))。配列の名前の写しが落ちる | 直す価値が高い(S-4 で通したかった道をふさいでいる)。規則の変更なので**先に封じてから**。案: 観測の値が配列で、その要素の文字列が statement にそのまま出ているときは、その文字列の中の数字を数えない |
| (d) | **H-3 が `needed_observation` に反証を要求する**(§3.3 の (iv)) | H-4 の `KINDS_WITHOUT_PREDICTION` と同じ形で kind を分ける。(c) と同じ封に入れてよい |
| (e) | **claude 席の v1.4 の効き目は未測定**。(c1) の `items2` 対策が効いたかは次の run まで分からない | 次の run で測る。**1 回通っても「効いた」とは書かない**(揺れと区別できない。封のとおり) |
| (f) | **HTTP の timeout 無し**(§2 の付随)。1 試行で 50 分 | 直す価値がある(実 run の所要が読めない)。`fetchWithRetry` に timeout を足すのは Core でなく将棋側の道具。別に封じる |

## 7. 手順との差・記録

1. 司令塔は `--dry-run` 1 回の後に実 run 1 回。上限は環境変数(`.env` は不変)。実 run 中にコードは触っていない(`gitHead` = `e5d319f`、木はきれい)。
2. **止まる所を守った**: Golden c5 が rc≠0 になったので、**Golden は書き直していない**(人間へ)。残高で席が落ちた後、**上限を上げる・席を足す・やり直すことはしていない**(1 回の承認は 1 回)。
3. `exitSelect --draft` と `integrationCheck` は材料(`integration.json`)が無いので**回していない**。「測れない」として記録した(回したふりをしない)。
4. 監査の非ブロッキング 2 件(直していない): 新版 4 本の `$id`/`title`/`description` が旧版の字のまま(計画の「それ以外は 1 字も変えない」の最も厳密な読み。検証器は注記を見ない)、`lib/reportData.test.ts` の実データ回帰が環境負荷で 120 秒の timeout を超えることがある。
5. 証跡: [docs/golden_master/s4_first_run_stdout.txt](../../docs/golden_master/s4_first_run_stdout.txt)(dry-run・実 run・HTTP の失敗の全文・CLI・照合・Golden)、[s4_first_run_compare.json](../../docs/golden_master/s4_first_run_compare.json)、[s4_first_run_golden_diff.txt](../../docs/golden_master/s4_first_run_golden_diff.txt)(58 件の全文)、[fixtures/shogi/s4_first_run_core.json](../fixtures/shogi/s4_first_run_core.json)(Claim 33)。

## 8. この文書がしないこと

Golden の書き直し。入金・やり直しの判断。H-1・H-3 の規則の変更。claude 席の効き目の主張。`additionalProperties` を緩めること。Core の変更。営業の実証範囲の更新(§6 の (a) の後)。
