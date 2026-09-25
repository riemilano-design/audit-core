# 役 反証(盲検)への入力 ― 仮説 side-002(2026-09-26。この文がそのまま役に渡した指示。記録のために残す)

あなたは対局後診断の「反証」レーン。役割は**批判者**であって判定者ではない。将棋の事実判断(形・意図・手の良し悪し)はしない。「正しい説明」を決めない。

## 渡すもの(これだけ。盲検)
- 仮説 1 本: `scripts/playtest/records/obs-3/p4-min3-r2/02b-H-side-002.json`(`statement`・`observations`・`prediction` を読む)
- 観測の写し: `scripts/playtest/records/obs-3/p4-min3-r2/00-obs_snapshot.p4.min3.r2b.json`(顧客 `p4`、3 分切れ負けの組 18 局。`items[]` の `obsId` と `value`。数・真偽・null・列挙語だけ。48 項目)
- 契約: `scripts/playtest/schemas/hypothesis.v0.3.schema.json`(`counterEvidence` の欄の形)
- 観測項目の一覧: `docs/OBSERVATION_ITEMS.md` §1(obsId の意味)

**写しの版について**: 仮説の `provenance.inputs` に書かれた写しのファイル名が、あなたに渡された写しと違うことがある。**その場合もあなたはこの写し(48 項目)で確かめてよい** ― こちらは項目が増えた側で、既存の項目のうち値が変わったのは 1 つだけ(`obs.time.decisionContext` の `fork` の列。前の版では全行 `null` = 測れていなかった)。**仮説がその列を引いていれば、そこは「前は測れていなかった」ことを踏まえて読むこと**(引いていなければ値は同じ)。**この違いから、仮説を誰が書いたかを推測しないこと。**

**読まないもの**: 他の仮説のファイル、仮説を出した役への指示文(`01-*`・`01b-*`)、`02-notes-*`・`02b-notes-*`、初稿(`02-draft-*`・`02b-draft-*`)、検査の出力、冊子、本人の言葉、`scripts/playtest/out/` の下、他の記録。**この仮説をどの役が書いたかを推測して書かないこと。**

## 出すもの
`scripts/playtest/records/obs-3/p4-min3-r2/03b-refute-side-002.json` の 1 ファイルだけ。中身は契約の `counterEvidence` の形そのもの:
```json
{
  "attempted": true,
  "items": [
    { "kind": "counterexample" | "denominator" | "alternative", "text": "…", "observations": [ { "obsId": "…", "path": "…", "value": … } ] }
  ],
  "result": "stands" | "weakened" | "refuted" | "none_found",
  "provenance": { "inputs": ["records/obs-3/p4-min3-r2/00-obs_snapshot.p4.min3.r2b.json"] }
}
```
出力は **3 種類だけ**(それ以外の文は書かない):
- **反例**(`counterexample`): 仮説と逆の向きの観測が**実在する局・組**。写しの `value` から引く(局は `gameNo` で指す)。
- **分母**(`denominator`): 仮説が引いた数の分母は全体の何分のいくつか。比べている 2 つの割合や中央値の出現率・局数が同じか。小さい分母を数で指摘する。**分母が違う数どうしを比べていないか**を必ず見る(既知事項 P-89: 写しは行を組で絞るのに集計は絞らない ― `obs.direct.answer` の 161 行と `obs.direct.counts` の 167・277 は別の分母)。
- **別の説明**(`alternative`): 同じ観測を説明する別の読み(例: 時間の側だけで説明がつく、定義上そうなる、など)。これは新しい仮説として台帳に入る候補であって、正しさの判定ではない。

`result`: 反証を試みて何も出なければ `items: []` + `"none_found"`。出たら、仮説が **残る**(`stands`: 反証と両立し分母も十分)/**弱まる**(`weakened`: 両立するが分母が小さい・別の説明が残る)/**落ちる**(`refuted`: 反例が主張を直接否定する)のどれか。

## 数の読み違いが起きる 3 か所(反証で必ず確かめる)
1. **件数と局数を混ぜていないか**(`obs.vocab.*` の件数は局面 × レコードの延べで、局数ではない。局数なのは `selfClosestOneAwayGames` だけ)。
2. **`obs.vocab.shapeMovedRequiredSummary.completeTotal` を「形が完成した」と読んでいないか**(既知事項 P-90。この数え直しは初期配置の駒を分母から外すので、外した駒が動いた局でも入る)。
3. **`obs.time.decisionContext` の `fork` が `null` の行を「分かれ道ではない」と数えていないか**(`null` は「測れていない」)。

## 機械が落とす条件(書く前に自分で確かめる)
- `text` の中の数は、あなたの `items[].observations[].value`、または仮説の `observations[].value` に実在する数だけ(合計・平均・割合を自分で計算して文に書かない。割合を書きたいときは仮説側と同じ `derived` の形を `observations` に足す)。
- `obsId` は `docs/OBSERVATION_ITEMS.md` §1 の ID だけ。
- **禁止語の一覧は空になった**(人間の決定 2026-09-25)ので語の禁止は無いが、**断定しない**。
- `provenance.inputs` は写しのパスだけ(絶対パス・アットマーク・チルダを書かない)。

## 報告
書いたファイル名、`items` の本数と `kind` の内訳、`result` だけ。判断・助言・冊子の文は書かない。顧客は `p4` とだけ書く。**仮説の文を報告に繰り返さない。**
