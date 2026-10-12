# 代表の選び方の patch ― 独立監査の対象と判定基準(**実行の前に固定**)

人間の判定 D-015「代表選択の patch は独立監査へ進める候補。**main 採用はまだ承認しない**」。
この文書は監査席に渡す。**監査席は実装しない・直さない・封の予測を評価し直さない。** 判定は GO / REVISE / HUMAN のどれか。

## 1. 対象(sha で固定)

| | |
|---|---|
| 土台 | main `e283feb`(`git worktree add --detach <道> e283feb`) |
| patch | `audit-core/docs/patches/representative_selection_2026-10-12.patch`(sha256 `f759cef30ba40e1a2b26cbb6d1bd933518f663eb0cd13628630783a1ec5f7a94`・10,922 B)。**設計 Y の patch を含む累積**。触る所は `audit-core/adapters/xbrl/recipes.py` の 1 ファイルだけ |
| 当て方 | worktree の根(リポジトリの根)で `git apply <patch>`。**作業木では当てない** |
| 封 | `REPRESENTATIVE_SELECTION_SEAL_2026-10-12.md`(規約・予測・合否)、`CANDIDATE_DEFINITION_SEAL_2026-10-12.md` と `_ADDENDUM_`(設計 Y と追加の封 h〜m) |
| 結果 | `REPRESENTATIVE_SELECTION_RESULT_2026-10-12.md`、`fixtures/xbrl/seals_*_R_*`(司令塔が測った生の出力) |
| 独立判定 | `fixtures/xbrl/independent_truth_2026-10-12.json`(73 行。**正解として使うのはこれだけ。Golden 期待値は正解ではない**)、`INDEPENDENT_JUDGEMENT_51_2026-10-12.md` |
| 採点 | `fixtures/xbrl/score_blind51_2026-10-12.py`・`score_round2_2026-10-12.py`(定義を変えない)。エンジン出力は `fixtures/xbrl/dump_engine_populations_2026-10-12.py <audit-core の道> <出力>` |

## 2. 監査席がやること(番号順)

1. **再現**: patch の sha を確かめ、`git apply --check` → 当てる。`dump_engine_populations` の出力が司令塔の
   `seals_engine_R_2026-10-12.json` と**一致するか**(司令塔は一致を確認済み。席は自分で確かめる)。
   試験: `audit-core/` で `python3 -m unittest discover -s tests -t .`(493 中 12 落ち)・`python3 -m pytest -q`(589 中 12 落ち)。
   落ちる 12 本の**名前**を司令塔の記録(結果文書 §表の最終行)と照らす。名前が違えば HUMAN。
   保護面の束ね sha(`git ls-files audit-core/core/py audit-core/adapters | sort | xargs shasum -a 256 | shasum -a 256`、**リポジトリの根で**)が
   **patch を当てた木で変わるのは `recipes.py` の分だけ**であること、**main の木では `490888d4…` のまま**であることを確かめる。
2. **コードを読む**: `_representative` と 3 つの呼び出し(対の a 側・b 側、単一)を読み、次を**入力を作って**確かめる。
   - `jppfs_cor` が 0 種 / 1 種 / 2 種以上の群での返り値(2 種以上で `None`)。
   - `None` が返ったとき、**3 つの呼び出しすべて**が `ambiguous(elements)` で停止し、`ambiguous_count` を立てるか(取りこぼしなら REVISE)。
   - 群の中で同じ `jppfs_cor` 要素名が複数 fact に在る場合(文書順で最初の fact を返すか)。
   - **値(`claim["value"]`・`target`・`match_value`)を参照していないこと。** 参照があれば REVISE。
3. **司令塔が見落とした・予測を外した点を重点的に**(人間の指定):
   - **`N053` の誤通過**: 残る 1 件が綴り違い(`InvestmentActivities`/`InvestingActivities`)であることを、材料から自分で確かめる。規約の欠陥か、別の問題か。
   - **`N069` の変化**(2 巡目、対象、誤った束縛 → 正答): 何が起きたか。規約が**対の各側**に効く経路(a 側・b 側それぞれ)を、`N069` の pointer で確かめる。
     封 §4 は「対の形は影響を受けない」と予測して外れた。**対の各側に規約が効くことが、封 §1 の字(『畳んだ群』)の範囲に入るか**を席の読みで答える。
   - **対の両側への適用**: a 側と b 側で**代表の種類が食い違う**ことは起きうるか(例: a 側は `jppfs`、b 側は 5 年表)。1B/5F の全 Claim で数える。起きれば、その対の意味を書く。
   - **別概念を畳むケース**: `elems` に複数の概念が入っている Claim(`Income`→`IncomeLoss` の変種、`e` と `e+SummaryOfBusinessResults`、
     `ProfitLoss` と `ProfitLossAttributableToOwnersOfParent` など)で、**別の概念の fact が 1 つの群に畳まれていないか**。
     `N248` 型(`jppfs` が 2 種 → 停止の予測)が実際に停止しているか。
4. **席自身の予測と変異**(**先に予測を書き、それから変異する**。記憶: 変異と同じ逐次コマンドで書く):
   次の変異を**使い捨て worktree**で作り、(a) 司令塔の 98 行採点(`score_blind51`)と (b) 試験が、**どう動くか予測してから**測る。
   `startswith("jppfs_cor:")` を `"jpcrp_cor:"` に / `len(names) == 1` を `>= 1` に / `None` を `group[0]` に / 代表を `group[-1]` に /
   選択に `claim["value"]` を混ぜる。**試験が黙る変異は報告する**(この patch は `_representative` の試験を持たない。採用の前に要る試験の一覧が欲しい)。
5. **範囲の外を言わない**: 未使用 2 書類 `S100Z39P`・`S100Z4N9` は**開かない**。別文書での振る舞いは**測れないので未証明のまま**と書く。

## 3. 判定の基準(**先に固定**)

| 判定 | 条件 |
|---|---|
| **GO** | 1 が全部再現し、2 の入力で**欠陥が見つからず**、3 の 4 点に**証拠つきで答え**、`None` の取りこぼし・値の参照が 0 件 |
| **REVISE** | patch のコードに、**封の字に反する**欠陥(取りこぼし・値の参照・片側だけの適用など)。**封の予測・合否は直さない。**直しは patch の新版で、再測定は別に封じる |
| **HUMAN** | 規約の**意味**(`jppfs_cor` 優先)に関わる問い、封の字が 2 通りに読める点、試験の名前の不一致、再現不能。席は選ばない |

**GO が意味しないこと**: main 採用の承認ではない。「独立 3 席の規約と一致する代表を選べる」を超えて、**根拠の意味的な正しさ・別文書での振る舞いは証明しない**。
main 採用の前には、少なくとも (i) `_representative` の試験の追加、(ii) 恒久の門 `test_comparator_independence` の期待値の更新、
(iii) Golden の差 48 件の扱い(**期待値の変更は人間の承認**)が別に要る。席はこの 3 つに**手を付けず**、要る内容の一覧だけ書く。

## 4. 席の規約(AGENT_PROTOCOL に従う。席の書き出しにも入れる)

- 作業は `git worktree add --detach` の使い捨て木だけ。**共有の作業木を書き換える git(stash/reset/checkout --/clean/restore/add/commit/merge)を使わない。**終わったら `git worktree remove --force`。
- API キーを使わない・`.env` を読まない・EDINET の API を呼ばない(`fetch_material.py` を実行しない)。`scripts/playtest/out/` に書かない。
- 材料の zip(`ai_prose_instance_2026-10-09.zip`)は作業木の `audit-core/fixtures/xbrl/` に在る(git 管理外)。worktree では環境変数 `AC_ZIP` に絶対の道を渡す。
- 報告に**測った木と入口**を数の横に書く。0 件を報告するときは、その 0 を作りうる自分の絞り込みを同じ文に書く。
- 報告の形: 判定(GO/REVISE/HUMAN)→ 1〜5 の結果を番号順に(数・入力・出力を示す)→ 席が見つけたが封の範囲外の問題(別行で)→ 採用の前に要る試験の一覧。
