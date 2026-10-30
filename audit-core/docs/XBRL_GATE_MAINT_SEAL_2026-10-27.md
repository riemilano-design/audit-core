# 封: 門の手入れ 2 点 ― 封の名指しで赤くなった引きの門と、試験 file を足すたびに赤くなる段 2 の門 ― 2026-10-27

人間(2026-10-27)「寝るから今の作業終えたら p27 進めて 君に任せる」。P27 段 1 の便(取得の script と封の門。試験 file 2 本を足す)の前に、2 本の門を直す。engine 0 行・記録(`fixtures/**/*.json`)0 行。試験 file は足さない。独立監査の GO を経て commit する。

## §0 赤の事実(P27 段 1 の実装の席の報告と、司令塔の読み。2026-10-27)

1. `tests/measure/test_xbrl_fresh_seal.py::DrawRecordTest::test_23_the_draw_is_recomputed_from_scratch_and_equals_the_record` は、commit `e37ae3b`(P27 段 1 の封)から赤。封 §11-0 が下見の docID 2 つを字で名指し、引きの再計算(追跡 file に名前が出る docID を飛ばす)がその 2 件を飛ばして 40 件が変わるため。**原因は司令塔が書いた封の字。** 前例: `fixtures/xbrl/p26_2026-10-21.json` ほかを同じ一覧に足した(2026-10-22・2026-10-23)。
2. `tests/measure/test_xbrl_default_p26_result.py::RecordTest::test_8_readme_facts_and_suite_count_are_live` は、ディスク上の試験 file の数を段 2 の記録の `S11."試験 file の数(ディスク上)"`(222)と == で比べる。**試験 file を 1 本でも足す便は、どれもこの門で赤になる**(P27 段 1 の作業木で 224 ≠ 222)。記録を採り直すのは誤り(段 2 の記録は段 2 の時点の事実)。いまの木の試験 file の数は、覆いの記録 `fixtures/suite_coverage_2026-10-16.json` の `test_files_on_disk` が持ち、同じ試験の 694 行が既にそれと比べている。一つの性質を 2 か所で縛っていたのが欠陥。

## §1 触ってよい file(これだけ)

1. `tests/measure/test_xbrl_fresh_seal.py` ― `LATER_NAMING_FILES` の tuple の末尾に `"docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md"` を 1 つ足す。ほかの行は 1 字も変えない。
2. `tests/measure/test_xbrl_default_p26_result.py` ― `test_8` の中の、ディスクを歩いて数えた `n` を記録の `S11` と比べる 1 つの `assertEqual` だけを、次に置き換える: 段 2 の commit `917157c` の木(`git ls-tree -r --name-only 917157c`、cwd は audit-core。path の最後の成分が `test_` で始まり `.py` で終わるもの。`.git`・`node_modules`・`__pycache__`・`.pytest_cache` を含む path は数えない)の数が、記録の `S11."試験 file の数(ディスク上)"` と == であること。`git ls-tree` が失敗する環境(履歴の無い写し)では、この比べだけを skip する(skip の行を出す)。**ディスクを歩いて数えた `n` と覆いの記録の比べ(いまの 694 行の `suite["test_files_on_disk"] == n`)と、`uncovered_files == []` はそのまま残す。** docstring に日付つきの追記を 1 文足す。
3. この封と、結果は commit のメッセージに書く(結果の文書は作らない。数は下の予測の当たり外れだけ)。

## §2 予測(外れうる形で)

| # | 予測 | 外れ方 |
|---|---|---|
| G-1 | 直した木(試験 file を足していない状態)で `python3 -m pytest -q tests/measure` は赤 0。`test_23` と `test_8` は緑 | 赤が 1 本でも |
| G-2 | `917157c` の木の試験 file の数は 222(記録と同じ) | 222 でない |
| G-3 | 変異: (a) `LATER_NAMING_FILES` から足した 1 つを外す → `test_23` が赤、(b) 記録の比べの相手を `917157c` でなく `HEAD` にする → P27 段 1 の便を足した木で赤(足していない木では緑のまま。この変異は試験 file を足す前の木では黙る、と予測する)、(c) 覆いの記録の比べを外す → 未追跡の `test_zz_probe.py` を 1 本置いた写しで、ほかの門(`test_suite_coverage.py`)だけが赤になり `test_8` は緑 | 黙る / 別の門が赤 |
| G-4 | P27 段 1 の作業木の file を足した木で、`test_8` は緑(224 は覆いの記録の 224 と比べられ、段 2 の 222 は `917157c` の木と比べられる) | 赤 |

## §3 限界

- `test_8` は、段 2 の後に足した試験 file の数を見なくなる。いまの木の数は覆いの記録と `test_suite_coverage.py` だけが縛る(それがその性質の持ち主)。
- (c) の変異は `test_8` の外の門で拾われる。`test_8` 単独では覆いの記録の古さを拾わない形を許す。
