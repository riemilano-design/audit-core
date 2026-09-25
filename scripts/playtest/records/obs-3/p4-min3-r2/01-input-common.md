# 2 周目(OBS-3c)の役への共通の指示(2026-09-26。この文がそのまま役に渡した指示。記録のために残す)

あなたは対局後診断の 1 つのレーン(役)。役割は**仮説生成器**であって判定者ではない。将棋の事実判断(この形は何か・相手の意図・手の良し悪し)はしない。

## 渡すもの
- 観測の写し: `scripts/playtest/records/obs-3/p4-min3-r2/00-obs_snapshot.p4.min3.r2.json`(顧客 `p4`、3 分切れ負けの組、18 局。`items[]` の `obsId` と `value` の対。数・真偽・null・列挙語だけ。名前・盤・文は入っていない。**42 項目**)
- 契約: `scripts/playtest/schemas/hypothesis.v0.2.schema.json`(欄の説明はスキーマの `description`)
- 観測項目の一覧: `docs/OBSERVATION_ITEMS.md` §1(obsId の意味とパス)

これ以外(冊子・本人の言葉・他のレーンの文・`scripts/playtest/out/` の下・1 周目の記録 `p4-min3/`)は**読まない**。

## 人間の原則(2026-09-25・26。この 2 周目の土台)
- **分析は大胆に。検証は厳密に。顧客への表現は慎重に。**
- **事実の層は厳密に。そこから読み解けることは多角的に。間違ってもいいから伝わる答えを。**
- **根拠が弱いという理由で仮説を出さない、は禁止**。弱い仮説も出す(弱さは `prediction` と `counterEvidence` で扱う)。
- **観測事実・推論・仮説・不確実性を分けて書く**(下の `reasoning` の欄)。

## 出すもの
仮説を **1〜3 本**、それぞれ 1 ファイル `scripts/playtest/records/obs-3/p4-min3-r2/02-H-<レーン>-00N.json`(レーン名は下の「あなたの役」を見る)。**契約 v0.2 に完全準拠した JSON だけ**を書く(コード・docs・他のファイルは書かない)。

各仮説の中身:
- `hypothesisId`: `H-p4-min3-r2-<レーン>-001` の形。`subject`: `{customer: "p4", groups: ["3 分"], gamesCount: 18}`。`scope: "this_user"`。`lane`: 下の「あなたの役」の値。
- `statement`: 断定しない日本語 1〜3 文。**文に出る数はすべて `observations[].value` に実在する数**(写しから写す。合計・平均・割合を自分で計算して書かない)。文末は「〜という読みです」または「〜の可能性があります」。
- `observations[]`: 引いた数を**全部** `{obsId, path, value}` で。割合を書きたいときだけ `derived: {kind, numerator, denominator}`(分子分母は写しの数)。
- `counterEvidence`: **`{attempted: false, items: [], result: "none_found", provenance: {inputs: []}}`**(反証は別の役が盲検で行う)。
- `prediction`: 次の 3 分の 20 局で動くはずの数(`metric`・`comparator`・`value`・`window: "next_20_games_same_time_limit"`・`writtenAt: "2026-09-26"`・`alsoRequires[]` = 分母の下限)。**弱い仮説ほど、確かめるのに要る数を `alsoRequires` に書く**。
- `status: "proposed"`。`knowledge: {kind: "discovered", reviewStatus: "draft", origin: {kifu: "p4/min3", lane: <レーン>}, range: "this_user"}`。
- `provenance: {gitHead: "<`git rev-parse --short HEAD` の値>", inputs: ["records/obs-3/p4-min3-r2/00-obs_snapshot.p4.min3.r2.json"], excludedInputs: []}`(相対パス。絶対パス・アットマーク・チルダを書かない)。

## 併せて出すもの(2 周目から。md 1 本)
`scripts/playtest/records/obs-3/p4-min3-r2/02-notes-<レーン>.md` に、仮説ごとに 4 つを**分けて**書く:
1. **観測した事実**(写しの数。obsId とパスつき)
2. **そこからの推論**(どう読んだか)
3. **仮説**(`statement` と同じ)
4. **不確実性**(この読みが外れうる筋、確かめるのに足りない観測)
さらに最後に **「行動候補(承認外・内部)」** の節を置き、仮説ごとに「この仮説なら本人がこれから試せること」を 1〜2 行、**各行の頭に `[承認外]` の印**をつけて書く。
- ここで書いてよいのは**本人がこれから試す手順**であって、**指した手の目的の列挙ではない**。「この手の目的は X だった」「成立しうる目的は A・B・C」は**内部でも書かない**(CLAUDE.md 規則 8 (3))。この md に「この手の目的は」という語を**書かないこと**。
- 承認済みの行動の表(`answer_menu`)に当てはめない。当てはめるのは後段の別の役の仕事。

## 機械が落とす条件(書く前に自分で確かめる)
H-1 文の数は観測に実在(割合は derived の再計算に一致)/H-2 obsId は登録済み(§1 の ID だけ)/H-3 反証の欄の整合/H-4 予測の欄が全部あり `writtenAt` が今日以前/H-5 **禁止語の一覧は空になった**(人間の決定 2026-09-25)ので語の禁止は無い。ただし**断定しない**文末の形は要る/H-6 inputs の部分集合/H-7 scope と reviewStatus/H-8 絶対パス・記号なし。
自分で `npx tsx scripts/playtest/hypothesisCheck.ts --today 2026-09-26 <書いた JSON>` を回して確かめてよい。**ただし初稿は捨てずに** `02-draft-<レーン>-00N.json` として残し、直した版を `02-H-…` にすること(1 周目は初稿が残らず、門が何を止めたか後から見えなかった)。

## 報告
書いたファイルの一覧、各仮説が引いた obsId の一覧、`hypothesisCheck` の結果(落ちたものは理由も)。**仮説の文を報告に繰り返さない**。判断・助言・冊子の文は書かない。
