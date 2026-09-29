# 指示書 ― セッション「将棋コーチ｜次世代分析パイプライン設計」(2026-09-30。人間が開く。司令塔が書いた)

**目的**: 次回以降の冊子制作を「エンジン観測 → LLM 自由分析 → 機械検証 → 顧客の問いへの回答 → 固定された器への配置 → PDF 監査」まで自動化できる構造にする。**このセッションは実装しない。** 現在のコード・データ・Golden Master・既存の検証器を調べ、この構造を**どこに接続するか**だけを設計案として出す。

**上位の正本**(先に読む): [NEXTGEN_PIPELINE_BRIEF_2026-09-29.md](NEXTGEN_PIPELINE_BRIEF_2026-09-29.md)(原則「冊子を作りながら分析しない」・5 層・流れ・人間の 4 つの直し + 2 点・作るもの 5 つ・変えない線)。この指示書はそれに**読者フィードバックから固定した 10 項目**を足すもので、原則は変えない。

## 1. 読者フィードバックから固定する事項(人間の言葉、2026-09-30)

1. **「第 1 候補」は初出時に 1 行定義する。** この局面でエンジンが 1 番に挙げた手。正解を意味しない。実戦手との比較材料として使用する。(例: 「第 1 候補: この局面でエンジンが 1 番に挙げた手。正解と決めるものではなく、実戦の手と比べるために使っています。」「最善手」という語は使わない。この修正に読者テストはしない。)
2. **本編を先に読む導線を固定する。** ファイル名・並び順で本編を先頭にする(`01_本編.pdf`・`02_付録.pdf` のように、名前だけで「最初に読むもの」が分かる)。
3. **本編だけで価値が完結する。** 付録は根拠確認用。付録を読者が照合することを前提にしない。付録を読ませるために本編を薄くしない。
4. **顧客の問いを Observation/Analysis の入力に含める。** 今回は「普段と違う型の局が影響しているか」。(packet ではなく `request` 側 ― 上位正本 §2.5)
5. **LLM 分析レーンでは分析を自由にする。** GPT/Gemini 等に同じ Observation JSON を渡す。分析段階で過度な禁止事項を設けない。LLM に数値の再集計はさせない。
6. **LLM の仮説は後段で機械検証する。** 数値・分母・母集団・該当局面・戦型等の認識結果を再確認する。
7. **検証済み材料を固定された Golden Master の器に自動配置する。**
8. **本編は顧客の問いへの回答を優先する。**
9. **読者フィードバックを別ログとして保存し**、「届いた/届かなかった/読者がどう解釈したか」を次回以降比較可能にする。([READER_UNDERSTANDING_LOG.md](READER_UNDERSTANDING_LOG.md) に記録 1 あり)
10. **3 切れと 10 切れは別データセットとして扱う。** 特に時間指標は 3 切れの閾値(10 秒以上・4 秒以内・0〜1 秒)を 10 切れへそのまま流用しない。比較できるものとできないものを最初から分ける。

**答えを作らせない**: 顧客の問いに対して「明確な差は確認できない」も正式な結果(上位正本 §2 の 4)。

## 2. いま在るもの(調べる対象。動かさない)

| 層 | 在るもの | 場所 |
|---|---|---|
| 顧客向け出口(器) | `deliver.ts` の段 exit-candidates → exit-gate → exit-render → exit-check → check-delivery。器の正本 | `scripts/playtest/deliver.ts`、`scripts/playtest/report-pdf/exit_candidates.py`・`exit_gate.py`・`exit_body.py`・`exit_cover.py`・`exit_render.py`、[GOLDEN_MASTER_CUSTOMER_EXIT.md](GOLDEN_MASTER_CUSTOMER_EXIT.md)、[DELIVER_GATES.md](DELIVER_GATES.md) §3a |
| 本編の文(今は人が書く) | 書き手の script(数を候補 JSON から引いて本文を組む。次世代ではここが「スロット」になる) | `scripts/playtest/out/c5/_final_draft_2026-09-29/write_round7.py`(`out/` は gitignore。読むだけ) |
| 検証器 | 検査 1〜7(数の実在・手の実在・分母の対・語・盤の位置)、構造検査、封 | `report-pdf/check_answer.py`(`MENU_THRESHOLDS`・`SIDE_LABEL_JP`)、`exit_gate.py`、`check_structure`、`compare_render.py --seal/--verify`、`lib/hypothesisCheck.ts` |
| Observation Packet(進行中) | 契約 2 本(packet・request)+ 生成器の束 A(f46e2c0)。束 B(facts)・C(aggregates + provenance、試験 A〜E)は自動化レーンが実装中 | [PLAN_OBSERVATION_PACKET_2026-09-30.md](PLAN_OBSERVATION_PACKET_2026-09-30.md)、`scripts/playtest/schemas/observation-packet.v0.1.schema.json`・`observation-request.v0.1.schema.json`、`scripts/playtest/lib/observationPacket.ts` |
| 3 席 LLM API(計画のみ) | hypothesis v0.4・seat-output v0.1・integration_input(internal.* を持たない)・H-9/H-10・固定の指示文 v1 | [PLAN_LLM_SEATS_API_2026-09-30.md](PLAN_LLM_SEATS_API_2026-09-30.md)、[LLM_SEATS_INSTRUCTION_v1_2026-09-30.md](LLM_SEATS_INSTRUCTION_v1_2026-09-30.md)、`schemas/hypothesis.v0.3.schema.json` |
| 材料(5 人目) | 25 局の棋譜・エンジン出力・time_cause・whatif-v2/read・opening_recognition・封をした冊子 | `scripts/playtest/out/c5/`(gitignore。実名は読まない・動かさない) |
| 過去の実験 | 25 局 LLM 独立分析 実験 1・2(人間の中継) | `docs/EXP*`(実験席の記録)、[RUNBOOK_PHASE1_MEASUREMENT.md](RUNBOOK_PHASE1_MEASUREMENT.md) |
| 記録 | 5 人目の周回の振り返り・感想・読者理解ログ | [RETRO_C5_EXIT_2026-09-29.md](RETRO_C5_EXIT_2026-09-29.md)、[CUSTOMER5_FEEDBACK_2026-09-30.md](CUSTOMER5_FEEDBACK_2026-09-30.md)、[READER_UNDERSTANDING_LOG.md](READER_UNDERSTANDING_LOG.md) |

## 3. 出すもの(設計案 1 本)

`docs/NEXTGEN_CONNECTION_DESIGN_2026-09-30.md` に、上位正本 §1 の流れの各段について次の表を書く。

| 段 | いま在る部品 | 足りないもの | 接続点(どのファイル・どの段・どの schema) | §1 の 10 項目のうち関係するもの | 変えない線に触れないか |
|---|---|---|---|---|---|

特に決めてほしいこと:

- **スロット**: 書き手の script が今やっている「候補 JSON → 本文」を、検証済み材料 → 器への自動配置に置き換えるとき、器のどこが固定でどこが可変か(P1 の 3 本・顧客の問いの答えの位置・盤 2・行動 + 次回測るもの・数え方・対応表)。器の余裕 0(本人用 5 / 見本用 4)をどう直すか。
- **用語の 1 行定義の置き場所**(§1 の 1): 器の固定文か、スロットの前文か。初出が本編 1 ページ目の太字にある。
- **顧客の問い**(§1 の 4・8): `request` → 席 → 検証 → 「答えの場所」の門(exit_gate に足す検査)までの通り道。
- **母集団の分離**(§1 の 10): packet の population(from/where/unit)と `time_limit_sec` で 3 切れ / 10 切れを別データセットにする方法。時間の閾値をどこで持つか(`check_answer.MENU_THRESHOLDS` のような固定値を持ち時間ごとにするか)。
- **読者理解ログとの接続**(§1 の 9): 採用された解釈と本編の文の対応を、後で読者の言葉と突き合わせられる形で残す場所。

## 4. 線(このセッションで守る)

- 実装しない。schema・コード・データを変えない。進行中の束(packet B/C、実験席)の schema を変える提案は、設計案の中に「提案」として書き、司令塔へ回す。
- `out/` の材料は読むだけ。実名は読まない・書かない(顧客は「本人」、符号は c5)。
- LLM に数えさせない・将棋の判定をさせない。戦型の名前は `data/` の承認済み認識だけ。一致を証拠にしない。
- 冊子(最終版)はもう直さない。§1 の 1・2 は次回の冊子に効かせるもので、送った版には触れない。
- 報告先: このセッションを開いた人間と、司令塔セッション「指示システムの整理 [1d8eef]」(設計案のパスと、判断が要る点の一覧)。
