# 代表選択 patch の独立監査 結果(2026-10-12)

監査席の最終報告を記録する。司令塔は結果を予測せず、報告を要約して残す。**GO は main 採用の承認ではない。** 人間の承認が要る。

対象: `docs/patches/representative_selection`(sha `f759cef3…a94`・10,922 B・設計 Y の上に累積・`recipes.py` のみ)。
測った木: 使い捨て worktree(e283feb + patch)。未使用 2 書類は開いていない。共有木・コミットは触っていない。

## 判定: GO(条件つきの注記あり)。REVISE に当たる欠陥なし。HUMAN に回す論点は 1 点。

## 1 再現(司令塔の数と全部一致)

- patch sha・大きさ一致。`git apply --check` OK。保護面は patch 後に `recipes.py` の 1 行だけ変化。main の木は `490888d4…` のまま。
- 1 巡目 98 行: 正答 24 / 誤った束縛 1 / 誤停止 21 / 形が違う 11 / 判定不能 41。2 巡目: 正答 6 / 誤 1 / 形違い 9。
- unittest 493 中 12 落ち、pytest 589 中 12 落ち。名前は Golden 10 + 恒久の門 2 で、設計 Y と同名。

## 2 コード

- jppfs の群が 0 / 1 / 2 種以上 → 先頭 / その fact / None。2 種以上は単一・対 a 側・対 b 側の 3 呼び出しすべてで `ambiguous(elements)` で停止。
- `claim["value"]`・target の参照は `_representative`・`_collapse_candidates` に 0。
- 注記: 停止時の `ambiguous_count` が固定値 2(provenance だけ)。`not subj` 枝は patch 前から同じ。

## 3 重点 4 点

- **N053**: 独立判定は `…InvestmentActivities`、語彙は `InvestingActivities`。語彙の欠落で、規約は何も決められないまま GROUNDED に通る。対象外の行。
- **N069(5F)**: 対の両側が畳まれ、誤った束縛から正答へ。封 §1 の字の範囲内と読むが、封 §4 の予測行「対は影響を受けない」と封内で食い違っていた。
- **対の両側の食い違い**: 1B/5F の対 15 件中 1 件(5F N084。a=jppfs の Prior1、b=jpcrp 5 年表の Prior2)。Prior2 に jppfs の fact が無いため構造的にこの形になる。結果は VALUE_MISMATCH。概念の食い違う対は 0。P7 の対 23 件は食い違い 0。
- **別概念の畳み**: 1B/5F は 0。P7 は `N114`・`N115`・`N116`・`N248` が停止(予測どおり)。**jppfs が片方だけの文書は未測定。**

## 4 変異(監査席が先に予測を記してから測定)

5 本のうち 4 本は予測どおり。外れ 1 本: 単一経路に claim 値で群を選ぶ処理を混ぜても 98 行採点は不変(P7 の 4 件は変化)。**98 行の採点は値依存の混入を検出できず、valindep の照合に頼る。** unittest は 5 本とも黙る(12 落ち・同名のまま)。

## 5 採用の前に要る試験(監査席の指定)

1. `_representative` の単体試験(0・1・2 種、同名複数、None)。
2. 単一・対 a・対 b で jppfs 2 種なら `ambiguous(elements)` になる試験。
3. 対の a=jppfs/b=5 年表、a=5 年表/b=jppfs を固定する試験(N084 型)。
4. 群が複数ある入力で値だけ変えても同じ選択になる試験。
5. `test_comparator_independence` の期待値更新(人間承認)と Golden 差 48 件の扱い(人間承認)。
6. 代表の最終順序(`group[-1]`・名前の接頭辞の取り違え)を赤くする変異試験。

## 6 人間に回す点・封の範囲外

- **HUMAN**: 対の a/b で代表の種類が食い違うことを許すか(N084 型)。規約の意味に触れる。
- 範囲外: N053 型の語彙欠落 / N084 型の意味づけ / `ambiguous_count` 固定値 / jppfs が片方だけの文書での振る舞い。

## 7 司令塔の扱い

- この結果で patch を main へ入れない。D-015 の順序どおり、次は抽出の v2 の実装と再測定(`EXTRACTION_SEAL_V2_2026-10-12.md`)。統合測定は両方が決着してから予測を先に封じて行う。
- 採用の判断材料として、人間には上の HUMAN 論点・Golden 48 件・`test_comparator_independence` の期待値更新を並べて渡す。
