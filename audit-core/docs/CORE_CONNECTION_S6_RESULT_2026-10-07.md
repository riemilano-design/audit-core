# S-6 結果 ― 実 run を Golden の土台に移す + 代表の版の統一 + 指示文 v1.5 + 端の境界の変異

- 日付: 2026-10-07
- 封じた計画: `audit-core/docs/CORE_CONNECTION_S6_PLAN_2026-10-07.md`(コミット `d8c9ae5`、sha256 `73619916…`)
- **費用: 0 円**(実 run なし。API 鍵を使う道具は 1 つも走らせていない)
- **Core(`audit-core/core/py`)は 1 バイトも変えていない**

## 1. (a) 実 run を `llm-seats/` に移し、Golden を書き直した

### 1.1 移した手順と確かめ方

```
scripts/playtest/out/c5/llm-seats-s5/43f8b69c-20261007-1/
  → scripts/playtest/out/c5/llm-seats/43f8b69c-20261007-1/
```

- 移す前に行き先が空いていることを確かめた(空いていた)。
- 移す前に run の中の **15 ファイルの sha256** を控え(`docs/golden_master/s6_move_files.sha`)、移した後に `shasum -a 256 -c` で照合した。**OK でない行は 0 行**。
- `llm-seats-s5/` の直下の `pair_summary.json`・`seat_input.md`・`seat_input.meta.json` は動かしていない(run の外側の証跡として残した)。
- `llm-seats-s3/`・`llm-seats-s4/` の run は移していない(S-3 は指示文 v1.3 の時代、S-4 は claude 席が立たなかった不完全な run)。
- `scripts/playtest/out/` は `.gitignore:8` で追跡外のため、移動は `mv` であり git の操作ではない。追跡されている記録は `docs/golden_master/c5_expectation.json` だけ。

### 1.2 **`--write` の前に 1 回測った**(これが今回いちばん大事な手順)

移した直後、`--write` を付けずに `goldenMasterCheck` を 1 回回した。

```
npx tsx scripts/playtest/goldenMasterCheck.ts --expect docs/golden_master/c5_expectation.json
→ rc=1 / ★期待値と違う(25 件)
```

差の 25 行はそのまま `docs/golden_master/s6_move_golden_diff.txt` に残した。そのうえで `--write` し、もう 1 回回して `rc=0`(入力 52 ファイル)を確かめた。

### 1.3 予測との突き合わせ(14 欄 → 当たり 12 / 外れ 2)

| 欄 | 予測 | 実測 | 判定 |
|---|---|---|---|
| a1 | rc=1、差 25 件 | rc=1、差 25 件 | 当たり |
| a2 | identity 5 / seat_runs 15 / g9 5 / packet 0 / g8 0 | 同じ | 当たり |
| a3 | 長さ 1 + [3] 4 + [4] 3 + [5] 4 + [6] 3 | 同じ | 当たり |
| a4 | identity の 5 件は名前を挙げた 5 ファイルで、すべて「期待に無い」 | 同じ | 当たり |
| a5 | g9 は hypothesisCheck 2 + seatOutputCheck 2 + integrationCheck 1、Python の門 3 つは 0 | 同じ | 当たり |
| a6 | identity 52 / seat_runs 8 / hypothesisCheck 8 / seatOutputCheck 8 / integrationCheck 5 | 同じ | 当たり |
| a7 | 基本 13 行。13 を超えるのは 14 項目のうち **3〜7 項目** | 基本 13 行。超えたのは **2 項目**(gpt の 4 番目・claude の 5 番目がともに 22 行) | **外れ** |
| a8 | gpt・claude ともに fail | 同じ | 当たり |
| a9 | seatOutputCheck.problems は gpt 4 行・claude 8 行 | 同じ | 当たり |
| a10 | C-007・C-008 の representative の schema NG が各 1 行以上 | 各 1 行(`$.observations: 要素が 0 個で、1 個に足りない`) | 当たり |
| a11 | integrationCheck.problems は点推定 4 件・帯 2〜10 件 | **15 件**(I-4 10 / I-2 4 / I-6 1) | **外れ** |
| a12 | I-1 の行 0 件・H-9 の行 0 件 | ともに 0 件 | 当たり |
| a13 | H-12 はすべて「ok」(14 項目 × 1 行) | `{ok: 14}` | 当たり |
| a14 | `--write` の後は rc=0 | rc=0 | 当たり |

### 1.4 外れた 2 欄の根は 1 つ ― 「面の中の検査を数え落とした」

a11 の外れ方が重要である。予測は「I-4 の schema 2 行 + H-1 の数行」しか立てていなかった。実測の 15 行のうち **5 行は I-2 と I-6 で、予測にはその検査の名前が 1 つも出ていない**。

```
I-2: C-007 の packetRefs: packetRef.path「facts.recognition.rows」が文法(…)に合わない
I-2: C-007 の成員「1:I-1-007」が束の根(facts.recognition.rows)を根拠に持たない
I-2: C-007 の成員「2:I-2-006」が束の根(facts.recognition.rows)を根拠に持たない
I-2: C-008 の成員「1:I-1-008」が束の根(…)を根拠に持たない
I-6: selfComputedNumbers[5] の値「0」が代表の文・矛盾・注に出ている
```

これは S-5 で外れた p3/p4/p6 と**同じ型を 1 段下に降ろしたもの**である。S-5 では「門を呼んでいる 5 か所のうち I-4 を数え落とした」。今回は「I-4 を数えたが、**同じ記録面に I-1〜I-6 が並んでいることを数え落とした**」。`docs/AGENT_PROTOCOL.md` の工程 v2 は「呼び出し元 × 記録面 × 生きているか」を数えよと定めているが、**記録面の中にいくつ検査が並んでいるかは数えよと書いていない**。

a7 も同じ方向の誤りで、符号は逆である。報告(notes)が付く項目を 3〜7 と広く見積もったが実測は 2 項目だった。H-11 の報告が出る条件(承認済みの定義が無い名前が文に出ること)を、席の文の実態より多く見込んでいた。

**工程の直し(v3)として次を `docs/AGENT_PROTOCOL.md` に足す**: 記録面の差を予測するときは、その面に並ぶ**検査の識別子を列挙して**、それぞれ 0 件か何件かを書く。列挙に出てこない識別子があれば、その面はまだ数えられていない。

### 1.5 分かったこと(予測の当たり外れとは別に)

- **E-3 がこの面で初めて実際に回った。** 既存の 6 通の封筒は `seal` の欄が無くて schema で早く返っていたため、`g9.seatOutputCheck` は 6 件すべて「`seal` が無い」の羅列だった。新しい run は封が 12/12 揃っているので、E-3 の中身の検査が初めて記録に載った(gpt 4 行・claude 8 行)。
- **S-5 §10.4 の発見 (A) が Golden の記録に固定された。** C-007・C-008 の代表は観測 0 件だが版が `0.4` なので `$.observations: 要素が 0 個で、1 個に足りない` で落ちる。これは (b) で直す。
- **整理役が束に無い根を作った**(I-2 の 4 行)。`facts.recognition.rows` は行の配列の根であり、観測の道の文法(`facts.<列>[添字].欄名`)に合わない。S-5 §10 で見たものと同じで、今回は門の記録として残った。
- **I-6 が 1 行出た。** 隔離した欄の数(`selfComputedNumbers[5]` の値 0)が代表の文に出ている。E-5 が席の側で同じことを言っており、整理役の側でも同じ誤りが通っていた。
