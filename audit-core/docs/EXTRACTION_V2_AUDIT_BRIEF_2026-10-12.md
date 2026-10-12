# 抽出 v2 の patch ― 独立監査の対象と判定基準(**実行の前に固定**)

人間の判断(2026-10-13): 抽出 v2 は封の合否条件を満たしたが main 採用は保留。次は独立監査。
この文書は監査席に渡す。**監査席は実装しない・直さない・封(`EXTRACTION_SEAL_V2_2026-10-12.md`)の予測と合否を評価し直さない。** 判定は GO / REVISE / HUMAN のどれか。
**結果文書 `EXTRACTION_V2_RESULT_2026-10-12.md` の §3(司令塔の疑い)は、§2 の 4 の判定を終えるまで読まない**(先入観を避けるため。封・本書・材料は読んでよい)。

## 1. 対象(sha で固定)

| | |
|---|---|
| 土台 | main の本書をコミットした commit(`git worktree add --detach <道> <commit>`)。保護面の束ね sha は `490888d4…`(main の木で変わっていないこと) |
| patch (a) | `audit-core/docs/patches/design_Y_2026-10-12.patch`(sha256 `518f7d40a0f7b7c5673cb84da8ca9d5126ec82352e73af05d094e4978faabe04`) ― 基準線 |
| patch (b) | `audit-core/docs/patches/extraction_v2_over_Y_2026-10-12.patch`(sha256 `91d9440460101e01107bf11375fe741c6404f698462a4de74b7ce76b20824fa1`・`recipes.py` +65/−9・新規試験 `test_extraction_v2.py` 6 本)。**(a) の上に載る差分** |
| 当て方 | worktree の根(リポジトリの根)で `git apply (a)` → `git apply (b)`。**作業木では当てない。** 当てた後の `recipes.py` sha256 は `e57171e64afd2dad…eaf48a3f`、試験ファイルは `1c024f0dfa653f1f…8da964` |
| 比べる木 | 基準線 = (a) だけを当てた木(別の worktree)。**代表選択の patch は載せない** |
| 封 | `EXTRACTION_SEAL_V2_2026-10-12.md`(規則 R-1〜R-4・§2.1 の表・§5 の既知の未解決・§6 の合否・禁止)。割当の正本は `fixtures/xbrl/premeasure_assign_2026-10-12.py` の `v2_rule` |
| 独立判定 | `fixtures/xbrl/independent_truth_2026-10-12.json`(正解として使うのはこれと `grounded_binding_check_2026-10-12.json` だけ。**Golden 期待値は正解ではない**)。回答は `blind51_answer_*`・`blind_round2_answer_*` と各 `*_key_*`、採点は `score_blind51_2026-10-12.py`・`score_round2_2026-10-12.py`(定義を変えない) |
| 司令塔の参照出力 | `fixtures/xbrl/extv2_engine_ref_2026-10-12.json`(1B・5F の全 Claim の状態・pointer・reason)、`extv2_60_ref_2026-10-12.json`(P7 の 60 件)。**席は自分で出し直して突き合わせる** |

## 2. 監査席がやること(番号順)

1. **再現**(司令塔は一致を確認済み。席は自分で確かめる)
   - patch 2 本の sha → `git apply --check` → 当てる。`recipes.py`・試験ファイルの sha が上の値と一致。
   - `python3 fixtures/xbrl/dump_engine_populations_2026-10-12.py . <出力>`(`audit-core/` で) が `extv2_engine_ref` と一致。`AC_ZIP=<ai_prose_instance_2026-10-09.zip の絶対の道> AC_LABELS=<grounded_binding_check_2026-10-12.json の絶対の道> AC_OUT=<出力> python3 fixtures/xbrl/measure_v2_2026-10-12.py .` の 60 件が `extv2_60_ref` と一致(G55 / VM2 / UV3)。
   - 採点: `score_blind51`(全 98 行: 正答 21・誤った束縛 18・誤停止 17)と `score_round2`(2 巡目 16 行中 13 正答)。引数は各スクリプトの `--help`/先頭を読む。
   - 試験: `audit-core/` で `python3 -m unittest discover -s tests -t .`(**499 中 13 落ち**)・`python3 -m pytest -q`(**595 中 13 落ち**)。落ちる 13 本の**名前**は次のとおり。違えば HUMAN。
     12 本は代表選択の木と同じ(Golden 10 + 比較器の門 2)+ 新規 1 本(`test_recipes.py::WindowBoundaryTest::test_direct_value_diff_phrase_caught_at_window_edge`)。
     ```
     tests/adapters/xbrl/test_claim_layer.py::ClaimLayerGateTest::test_p1_against_1B
     tests/adapters/xbrl/test_claim_layer.py::ClaimLayerGateTest::test_p5f_against_5F
     tests/adapters/xbrl/test_comparator_independence.py::ComparatorIndependenceTest::test_1B_comparator_forcing
     tests/adapters/xbrl/test_comparator_independence.py::ComparatorIndependenceTest::test_5F_comparator_forcing
     tests/adapters/xbrl/test_mutations.py::MutationTwoWayTest::test_all_mutations_match_their_prediction
     tests/adapters/xbrl/test_recipes.py::WindowBoundaryTest::test_direct_value_diff_phrase_caught_at_window_edge
     tests/golden/test_instrument3.py::Instrument3GateTest::test_normalization_total_77
     tests/golden/test_instrument3.py::Instrument3GateTest::test_p1_against_1B
     tests/golden/test_instrument3.py::Instrument3GateTest::test_p5f_against_5F
     tests/golden/test_instrument3b.py::Instrument3bTest::test_p6_against_1B_v2
     tests/golden/test_instrument3b.py::Instrument3bTest::test_p6_against_5F_v1_unchanged
     tests/golden/test_instrument3b.py::Instrument3bTest::test_p7_against_1B_v2
     tests/golden/test_instrument3b.py::Instrument3bTest::test_p7_against_5F_v1_unchanged
     ```
   - **割当の突き合わせ**: 金額の数 374 行で、実装の `_assign_period_form(s, a, b)` が `premeasure_assign` の `v2_rule` と 1 行も違わないこと(`fixtures/xbrl/dump_numbers_2026-10-12.py` の出力を使う)。**自分で突き合わせ、司令塔の「差 0」を写さない。**
2. **コードを読む** ― `_assign_period_form`・`_inside_prior_paren` と、それを呼ぶ `_direct_value_claim` の分岐(対の探索・単一の探索)を読み、**入力を作って**確かめる。
   - **値の参照**: `claim["value"]`・`target`・`match_value`・fact の値が、期間と形の**割当**に入っていないこと(入っていれば REVISE)。**割当の後に候補を選ぶ段**(対の探索・単一の探索)が、v2 が足した行で値によって候補を選んでいないこと。設計 Y から在る挙動は v2 の欠陥ではないので、**(a) 由来か (b) 由来かを分けて**書く。
   - **封 §2.1 の表の 22 行**: 表の各行の文(1B/5F は材料の文、P7 は `ai_prose_*` の文)と数の位置を実際に作り、`_assign_period_form` の返り値(期間・対かどうか)が表と一致するか。1 行ずつ「一致/不一致」で。
   - **境界を自分で作る**(封の字が決めている入力だけ。字が決めていない所は『封が決めていない』と書く): 手がかり `前期` が数の 15 字前ちょうどの位置 / 16 字前 / 手がかりと数の間に別の数がある / `前期比`・`前期に比べ`・`前期末と比べ` / 全角括弧と半角括弧 / 括弧が閉じない / 括弧の中に `同` / `増加額`・`減少額` / `減価償却費` / `増減なし` / F1 と F2 が同時 / F3 の括弧の中に `%` / F5 の `大幅` / 前期の数が F2 に当たる(C-1)。**封の規則どおりに動くか。** 規則から外れる入力があれば入力と出力を書く。
3. **範囲外だが人間が指定した重点**(**§2 の 4 を先に済ませてから**結果文書の §3 を読んでよい):
   - **(i) 期間の誤停止**: P7 全 415 主張・1B・5F で、基準線 (a) → (b) で状態が変わった行のうち、**期間が文と合っていない束縛**はないか。
   - **(ii) 前年の変化を述べた文**(封 §5-2)で、新たに VALUE_MISMATCH になった行の一覧(1B `N016`・`N025`・`N034`、P7 `N210` ほか)。真の文を咎めているものを数える。
   - **(iii) 代表選択との境界**: 誤った束縛 h の 18 のうち、(m)(期間は合うが要素名が `jpcrp_cor:*SummaryOfBusinessResults`)の 6 行が封の予測どおりか、それ以外に(m) でない行が混じっていないか。
4. **概念の判定(盲検に近い形・席が 1 行ずつ決める)**:
   - 基準線 (a) の木と (b) の木で P7 の全 415 主張を走らせ(`measure_v2` の `INS.run_verification("S100Z4Q1", V.P7, zb)`)、**状態または pointer が変わった全行**を列挙する。
   - 各行について、**文が指す項目(概念・期間・単一か差か)を材料の fact と context から席が自分で決め**、(b) の pointer がそれと一致するか(一致 / 概念が違う / 期間が違う / 形が違う / 判定不能)を書く。**値が偶然一致していても概念が違えば『概念が違う』**。判定不能は判定不能と書く。
   - 結果は『司令塔が疑っている行』を名指しされない形で出す。**そのうえで** 封 §5-1 の監視行 6 行(`N267`・`N268`〜`N272`)を別表に抜き出す。
   - 文を貸借対照表の差と読むか CF の項目と読むかは、**文の前後・材料の fact のうち文に出る語**から席が根拠を書いて決める。決められなければ判定不能。
5. **新規に落ちた試験の扱いの材料**(決めない・材料だけ出す): `test_direct_value_diff_phrase_caught_at_window_edge` が固定している入力と期待、(b) でその期待が崩れる理由(旧 25 字窓 vs F1 の直前)、1B・5F・P7 の全金額の数のうち **旧規則(窓 25 字・`比べて`)と v2 で『対にするか』が食い違う数の件数と id**、食い違いの向き(旧: 対 → v2: 単一 / 旧: 単一 → v2: 対)、その中で独立判定がある行は旧・v2 のどちらが合っているか。
6. **席自身の予測と変異**(**先に予測を書き、それから変異する**。変異と同じ逐次コマンドで書く):
   使い捨て worktree で、次のような変異を作り、(a) 98 行採点 (b) P7 の 60 件 (c) 試験(新規 6 本と既存)が**どう動くか予測してから**測る。
   `(?!額)` を外す / `[増減](?![一-龥])` の漢字除外を外す / 手がかりの窓 15 → 25 / C-1 の `period == "Current"` を外す / `前期比`・`に比べ` の基準の除外を外す / `_inside_prior_paren` を常に False / F5 を外す / F3 の `%` 除外を外す / R-2f(`増加額` 直前を単一)を外す / 割当に `claim["value"]` を混ぜる。
   **試験が黙る変異は報告する**。採用の前に要る試験の一覧が欲しい。
7. **範囲の外を言わない**: 未使用 2 書類 `S100Z39P`・`S100Z4N9` は**開かない**。代表選択との組み合わせ・別文書での振る舞いは**測れないので未証明のまま**と書く。

## 3. 判定の基準(**先に固定**)

| 判定 | 条件 |
|---|---|
| **GO** | 1 が全部再現(試験名も一致)し、2 の入力で**封の字に反する欠陥が見つからず**(値の参照 0・§2.1 の 22 行が一致・境界の入力が封の規則どおり)、4 の判定が全行に証拠つきで出ていて、6 の変異の結果が報告されている |
| **REVISE** | patch のコードに**封の字に反する**欠陥(値の参照・§2.1 の表との不一致・封の規則と食い違う境界・割当の取りこぼしなど)。**封の予測・合否は直さない。**直しは patch の新版で、再測定は別に封じる |
| **HUMAN** | 封の字が 2 通りに読める点 / **封 §5 が既知の限界として宣言した現象の範囲を超えた概念違いの束縛**(4 で見つかった『概念が違う』のうち §5-1 で説明がつかないもの)/ 新規に落ちた試験の契約の選択 / 試験の名前の不一致 / 再現不能。席は選ばない |

**『概念が違う』が見つかったこと自体は REVISE の理由にしない**(封 §5-1 が文字で区別できないと宣言済みで、封の字に反する欠陥ではない)。件数と行を出し、採用の判断(人間)の材料にする。
**GO が意味しないこと**: main 採用の承認ではない。「封の字どおりに実装されている」を超えて、**根拠の意味的な正しさ・別文書での振る舞い・代表選択との組み合わせは証明しない**。
main 採用の前に要るもの(席は手を付けず、**要る内容の一覧**だけ書く): (i) 割当の純粋関数の試験の追加(現状 6 本)、(ii) `test_direct_value_diff_phrase_caught_at_window_edge` の契約の更新(人間の承認)、(iii) Golden の扱い(期待値の変更は人間の承認)、(iv) 貸借対照表と CF を区別できない件の扱い(人間)。

## 4. 席の規約(AGENT_PROTOCOL に従う。席の書き出しにも入れる)

- 作業は `git worktree add --detach` の使い捨て木だけ。**共有の作業木を書き換える git(stash/reset/checkout --/clean/restore/add/commit/merge)を使わない。**終わったら `git worktree remove --force`。**リポジトリの docs/ やコードを編集しない**(報告は返答として返す。ファイルに書くのは司令塔)。
- API キーを使わない・`.env` を読まない・EDINET の API を呼ばない(`fetch_material.py` を実行しない)。`scripts/playtest/out/` に書かない。
- 材料の zip(`ai_prose_instance_2026-10-09.zip`)は main の `audit-core/fixtures/xbrl/` に在る(git 管理外)。worktree では環境変数 `AC_ZIP` に絶対の道を渡す。
- 報告に**測った木と入口**を数の横に書く。0 件を報告するときは、その 0 を作りうる自分の絞り込みを同じ文に書く。
- 報告の形: 判定(GO/REVISE/HUMAN)→ 1〜7 の結果を番号順に(数・入力・出力を示す)→ 席が見つけたが封の範囲外の問題(別行で)→ 採用の前に要る試験の一覧。
