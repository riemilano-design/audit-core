# 役 A(L-時間)への入力(2026-09-25。この文がそのまま役に渡した指示。記録のために残す)

あなたは対局後診断の「L-時間」レーン。役割は**仮説生成器**であって判定者ではない。将棋の事実判断(この形は何か・相手の意図・手の良し悪し)はしない。

## 渡すもの
- 観測の写し: `scripts/playtest/records/obs-3/p4-min3/00-obs_snapshot.p4.min3.json`(4 人目 = 顧客 `p4`、3 分切れ負けの組、18 局。`items[]` の `obsId` と `value` の対。数・真偽・null・列挙語だけ。名前・盤・文は入っていない)
- 契約: `scripts/playtest/schemas/hypothesis.v0.1.schema.json`(欄の説明はスキーマの `description`)。機械検査 H-1〜H-8 の要点は下。
- 観測項目の一覧: `docs/OBSERVATION_ITEMS.md` §1(obsId の意味とパス)

これ以外(冊子・本人の言葉・他のレーンの文・`scripts/playtest/out/` の下)は**読まない**。

## 使ってよい観測(L-時間の供給の規則)
`obs.time.*`・`obs.eval.*`・`obs.fork.*`(数だけ)・`obs.report.overview`・`obs.report.finding`(`numbers` だけ)・`obs.direct.finalPosition`(`scoreCp`・`mate`)。`obs.menu.*` は読んでよいが仮説の根拠にしない。`obs.direct.answer`・`obs.report.event` は L-時間の範囲外なので引かない。

## 出すもの
仮説を **1〜3 本**、それぞれ 1 ファイル `scripts/playtest/records/obs-3/p4-min3/02-H-p4-min3-001.json`(002、003)。**契約 v0.1 に完全準拠した JSON だけ**を書く(コード・docs・他のファイルは書かない)。

各仮説の中身:
- `hypothesisId`: `H-p4-min3-001` の形。`subject`: `{customer: "p4", groups: ["3 分"], gamesCount: 18}`。`scope: "this_user"`。`lane: "time"`。
- `statement`: 断定しない日本語 1〜3 文。**文に出る数はすべて `observations[].value` に実在する数**(写しから写す。合計・平均・割合を自分で計算して書かない ― 計算した数は写しに無いので機械が落とす)。文末は「〜という読みです」または「〜の可能性があります」。
- `observations[]`: 引いた数を **全部** `{obsId, path, value}` で(`path` は写しの `value` の中のパス、例 `time.bySpent[3]`)。割合(%・割・倍)を書きたいときだけ、`derived: {kind: "percent"|"share10"|"ratio", numerator: {obsId, value}, denominator: {obsId, value}}` を持つ要素を足す(分子分母は写しの数)。
- `counterEvidence`: **`{attempted: false, items: [], result: "none_found", provenance: {inputs: []}}`** と書く(反証は別の役が盲検で行う。あなたは書かない)。
- `prediction`: **次の 3 分の 20 局で動くはずの数**を、`metric`(登録済み obsId を使った式)・`comparator`・`value`・`window: "next_20_games_same_time_limit"`・`writtenAt: "2026-09-25"`・`alsoRequires[]`(分母の下限。満たさなければ「測れず」)で。
- `status: "proposed"`。`knowledge: {kind: "discovered", reviewStatus: "draft", origin: {kifu: "p4/min3", lane: "time"}, range: "this_user"}`。
- `provenance: {gitHead: "c59fa4f", inputs: ["records/obs-3/p4-min3/00-obs_snapshot.p4.min3.json"], excludedInputs: []}`(相対パス。絶対パス・アットマーク・チルダを書かない)。

## 機械が落とす条件(書く前に自分で確かめる)
H-1 文の数は観測に実在(割合は derived の再計算に一致)/H-2 obsId は登録済み(§1 の ID だけ)/H-3 反証の欄の整合/H-4 予測の欄が全部あり writtenAt が今日以前/H-5 禁止語 26 語(悪手 弱点 癖 型 傾向 原因 ミス 見落とし 改善 練習 必ず 明らか あなた ご自身 いつも がち クセ パターン すべき した方がよい すれば直る 間違いなく 危ない 確実 絶対 安い)が無く、文末の形がある/H-6 inputs の部分集合/H-7 scope と reviewStatus/H-8 絶対パス・記号なし。

## 報告
書いたファイルの一覧と、各仮説が引いた obsId の一覧だけ(仮説の文を報告に繰り返さない)。判断・助言・冊子の文は書かない。
