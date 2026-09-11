# 5-0 観測記録(2026-09-11。**観測記録。正本ではない**)

> この文書は、既知事項 LP-1・LP-2([PHASES.md](PHASES.md) の「既知事項(対局回帰で検出。2026-09-11)」)を直すために、司令塔が読み取りと実行だけで集めた事実の記録である。「5-0」は STEP 番号ではなく、Unit 5 の前段として行った観測を指す呼び名である。仕様の決定・推奨は含まない。決定は人間が行い、その記録は [PHASES.md](PHASES.md) に置く。行番号は HEAD `d0633bf`(2026-09-11)時点。

対象: LP-1(I-1 沈黙。候補手が安全確認で全件除外されても、除外の事実が画面に出ず道のりだけが表示され続ける)、LP-2(I-2 矛盾。除外されて表示していない手を指しても「この手は、直前に表示していた候補手の一つです」と出る)。

---

## 1. LP-1(I-1)の機構

| # | 事実 | 場所 |
|---|---|---|
| 1-1 | 安全確認の結果は `candidateMove`(status / notReadyReason)にだけ入る。`routes`・`targetShapeProgress`・`candidateMoveLabels` は routePlanner の生の値のまま組み立てられ、除外の影響を受けない | `apps/server/src/api/stateResponse.ts` 1435〜1437 |
| 1-2 | `hasCandidateMoves` は除外**前**の件数で決まる。そのため全件除外でも「一手目をどれも指せません」(`no_playable_route_first_move`)が落とされる | 同 1369、1450(`filterContradictoryConsiderations`) |
| 1-3 | `computeReachablePlan` の戻り値は reachableShapes / candidateMove / targetShapeId の3つだけ。除外された手の一覧・理由は返らない。除外のデータ源は `excluded: boolean[]`(どの手が除外されたかのみ。評価値低下と詰みの区別は無い) | 同 1504〜1506、`analysis/candidateMoveReferenceFilter.ts` 55〜62 |
| 1-4 | `not_ready` のとき `explanations` と `sharedNotes` は常に空 | `analysis/candidateMoveExplanation.ts` 105〜107 |
| 1-5 | web は `candidateMoveState === "ready"` かつ `candidateMove.status === "not_ready"` のとき候補手セクションを DOM に出さない。`notReadyReason` は届いているが未参照 | `apps/web/src/main.ts` 673〜688 |
| 1-6 | 道のり(`renderRouteProgress`)と `nextConsiderations` は候補手セクションと独立に描画される | 同 668、671 |
| 1-7 | 記録の実例(探索 game-01 ply 20): routes 2件、candidateMoveLabels 2件(除外された手のラベルを含む)、nextConsiderations 空、directionNote null、[0] に当たり1件。除外は一言も出ない | `scripts/playtest/reports/explore-2026-09-10T23-01-21-685Z-report.md` の元記録 |

## 2. LP-2(I-2)の機構

| # | 事実 | 場所 |
|---|---|---|
| 2-1 | `played_candidate` は `before.candidateMoves` = 前局面の `routePlanResult.candidateMoves`(安全確認**前**)で判定する。コメントの「直前に表示していた」は、実際には「routePlanner が候補として挙げていた」を指す | `analysis/moveOutcomeDetector.ts` 227〜239、`stateResponse.ts` 649〜658 |
| 2-2 | `computeMoveOutcomeAfterMove` は前局面を再計算し、⑧(MultiPV 参考評価)には触れない設計。安全確認の結果は引数にも経路にも無い | `stateResponse.ts` 1655〜1673、`server.ts` 275〜283 |
| 2-3 | 前局面で実際に表示した candidateMove は `backgroundPlan` にあり、着手処理の時点(`server.ts` 275)ではまだ書き換わっていない。`backgroundPlan.sfen === stateBeforeMove.sfen` で「その局面で表示していたもの」を照合できる。解析未完了のまま着手した場合は sfen が一致せず、「表示していなかった」と扱える | `server.ts` 61、134〜166、293 |
| 2-4 | 文言生成は `played_candidate` / `played_non_candidate` とも残っている。STEP 4-6 の廃止は表示フィルタで行われた | `analysis/moveOutcomeExplanation.ts` 71〜77、`stateResponse.ts` 1036〜1049 |
| 2-5 | 記録の実例(game-01 ply 22): ２八玉を指した直後に「候補手の一つです」。前の ply 20 の candidateMove は not_ready(除外)だった | 同上 |

## 3. 直すときの制約(承認済みの記録から。決定ではなく引用)

- STEP 4-2 完了記録: 全件除外の副作用は Unit 5 の論点。閾値(300cp)と除外規則は変更しない
- Unit 5 の定義: 候補手はユーザーが望んだときに出る位置づけ
- STEP 4-6 承認記録: 新しいユーザー向け文言は作らない前提で削除・非表示で対応した。述べる形で直すなら文言は人間承認事項
- [PROJECT_VISION.md](PROJECT_VISION.md) 4.3: エンジンの評価値を根拠に良い/悪いと述べない。[ARCHITECTURE.md](ARCHITECTURE.md): 評価語を述べない
- [TESTING_STRATEGY.md](TESTING_STRATEGY.md) 6. の注記: 候補手の説明件数は実行ごとに揺れることがある(下記 5.)

## 4. 人間の決定(2026-09-11。記録の写し。決定そのものは PHASES.md の STEP 5-1 の記録が正)

1. 除外の事実はサーバー側の新 kind で API 応答に載せる(web だけで直すと JSONL に痕跡が残らず、ハーネスが「直った」を証明できない)。文言は事実のみ。具体の文は人間承認へ
2. 除外時は盤上の矢印と「次の一歩」を出さない。道のりは目標の説明としてだけ残す(「残り1手(３九→２八)」という指示形が事故の原因で、目標の名前が残ること自体は害が無い)
3. I-2 の判定は「実際に表示した候補」(`backgroundPlan` と SFEN の照合)にする
4. Unit 5 の最初の STEP(5-1)として扱う
5. 完了確認: 今日の10手の固定棋譜で I-1 4件・I-2 2件 → 0件。あわせて同棋譜を3回再生して全一致すること。5-1 の承認時に I-1・I-2 を最初の approved 不変条件にするかを併せて提示する。探索6局は登録規則が未承認のため使わない

## 5. 揺れの観測(固定棋譜10手の10回再生)

目的: [TESTING_STRATEGY.md](TESTING_STRATEGY.md) 6. の注記(ply 20 で候補手の説明が1件/2件と揺れた)の頻度と箇所を記録する。原因の断定はしない。

- 実行: 2026-09-11 09:31〜09:36、`scripts/playtest/replay.ts` で `scripts/playtest/kifu/2026-09-10-claude-10moves.json` を10回、順次(並列なし)再生。10回とも exit 0、所要23〜24秒。`meta.gitHead` は10回とも `d4a1b1c`(docs のみのコミット。apps/・scripts/ は無変更)
- 比較: `elapsedMs`・`startedAt`・`totalMs`・`gitHead`・`readyMsPerPly`・`enginePath` を除いた record 22行を正規化して比較
- 結果: **全22行(ply 0〜20 × immediate/ready)が10回とも1通り。差が出た行は0件**。ply 20 の ready 行は10回とも `status: ready`、explanations 2件(`4g4f`、`3g3f`。順序も同一)
- 2026-09-10 の記録 `out/run1.jsonl`(gitHead `df6ecea`)と比較しても差0件
- 事実として言えること: 揺れは間欠的であり、10回の連続再生では再現しなかった。先の3回の再生(T-3 成果監査時)で見えた1件/2件の揺れと矛盾はしない(どちらも観測)。原因は未確定のまま

## 6. 影響範囲(事実。実測は 5-1 で)

- server: `api/stateResponse.ts`、`analysis/nextConsideration*` または新 kind の置き場所、`analysis/moveOutcomeDetector.ts`、`server.ts`(backgroundPlan を渡す場合)。それぞれのテスト
- web: `main.ts`(除外時の矢印・次の一歩の非表示、道のりの出し方)、`gameApi.ts`(型のミラー)
- 変えないもの: `candidateMoveReferenceFilter.ts`(300cp・除外規則)、`routePlanner`、`data/`
