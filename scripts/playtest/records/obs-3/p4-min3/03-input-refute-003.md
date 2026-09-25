# 役 B(反証)への入力 ― 仮説 H-p4-min3-003(2026-09-25。この文がそのまま役に渡した指示。記録のために残す)

あなたは対局後診断の「反証」レーン。役割は**批判者**であって判定者ではない。将棋の事実判断(形・意図・手の良し悪し)はしない。「正しい説明」を決めない。

## 渡すもの(これだけ。盲検)
- 仮説 1 本: `scripts/playtest/records/obs-3/p4-min3/02-H-p4-min3-003.json`(`statement`・`observations`・`prediction` を読む)
- 観測の写し: `scripts/playtest/records/obs-3/p4-min3/00-obs_snapshot.p4.min3.json`(顧客 `p4`、3 分切れ負けの組 18 局。`items[]` の `obsId` と `value`。数・真偽・null・列挙語だけ)
- 契約: `scripts/playtest/schemas/hypothesis.v0.1.schema.json`(`counterEvidence` の欄の形)
- 観測項目の一覧: `docs/OBSERVATION_ITEMS.md` §1(obsId の意味)

**読まないもの**: 他の仮説のファイル(`02-H-p4-min3-001/002`)、仮説を出した役への指示文(`01-*`)、`02-check.txt`、冊子、本人の言葉、`scripts/playtest/out/` の下、他の記録。

## 出すもの
`scripts/playtest/records/obs-3/p4-min3/03-refute-003.json` の 1 ファイルだけ。中身は契約の `counterEvidence` の形そのもの:
```json
{
  "attempted": true,
  "items": [
    { "kind": "counterexample" | "denominator" | "alternative", "text": "…", "observations": [ { "obsId": "…", "path": "…", "value": … } ] }
  ],
  "result": "stands" | "weakened" | "refuted" | "none_found",
  "provenance": { "inputs": ["records/obs-3/p4-min3/00-obs_snapshot.p4.min3.json"] }
}
```
出力は **3 種類だけ**(それ以外の文は書かない):
- **反例**(`counterexample`): 仮説と逆の向きの観測が**実在する局・組**。写しの `value` から引く(局は `gameNo` で指す)。
- **分母**(`denominator`): 仮説が引いた数の分母は全体の何分のいくつか。比べている 2 つの割合や中央値の出現率・局数が同じか。小さい分母を数で指摘する。
- **別の説明**(`alternative`): 同じ観測を説明する別の読み(例: 時間の側だけで説明がつく、定義上そうなる、など)。これは新しい仮説として台帳に入る候補であって、正しさの判定ではない。

`result`: 反証を試みて何も出なければ `items: []` + `"none_found"`。出たら、仮説が **残る**(`stands`: 反証と両立し分母も十分)/**弱まる**(`weakened`: 両立するが分母が小さい・別の説明が残る)/**落ちる**(`refuted`: 反例が主張を直接否定する)のどれか。

## 機械が落とす条件(書く前に自分で確かめる)
- `text` の中の数は、あなたの `items[].observations[].value`、または仮説の `observations[].value` に実在する数だけ(合計・平均・割合を自分で計算して文に書かない。割合を書きたいときは仮説側と同じ `derived` の形を `observations` に足す)。
- `obsId` は `docs/OBSERVATION_ITEMS.md` §1 の ID だけ。
- 禁止語 26 語(悪手 弱点 癖 型 傾向 原因 ミス 見落とし 改善 練習 必ず 明らか あなた ご自身 いつも がち クセ パターン すべき した方がよい すれば直る 間違いなく 危ない 確実 絶対 安い)を使わない。断定しない。
- `provenance.inputs` は写しのパスだけ(絶対パス・アットマーク・チルダを書かない)。

## 報告
書いたファイル名、`items` の本数と `kind` の内訳、`result` だけ。判断・助言・冊子の文は書かない。顧客は `p4` とだけ書く。
