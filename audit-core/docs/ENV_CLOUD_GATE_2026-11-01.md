# cloud の機での門の実測 ― 履歴の欠けと cache の欠けを分けて数える(2026-11-01)

desktop の席から cloud の機(claude.ai の container)へ移った直後に、`tests/measure` の門を走らせた記録である。**engine(`core/`・`adapters/`)は 0 行、記録(`fixtures/**/*.json`)は 0 行、封は立てていない。0 USD。EDINET・東京都の open data・LLM の席(API)は呼んでいない。** 変えたのは門 1 file(`tests/measure/test_xbrl_axis3_decision.py`。§4)と、この文書と、`docs/Q2_OPTIONS_DRAFT_2026-10-14.md`(§6)だけ。

この文書の数は pytest の出力をそのまま字で留めたもので、記録 JSON は作っていない(**全行【門なし】**)。走らせ直せば同じ数になるはずだが、cache の有無で変わる(§2)。

## §1. 機の違い(実測)

| 項目 | desktop(10-30 まで) | cloud(11-01) |
|---|---|---|
| git の履歴 | 全部 | 届いた時点は **shallow**(境界 `a3ad04a`、49 commit)→ `git fetch --unshallow origin` で全部(1,767 commit)。HEAD `a18d57f` は不変 |
| `~/.cache/audit-core/` | `edinet/` 281 件・`edinet-fresh-2026-10-21/` 40 件・`sheet/` 5 本・`edinetdb-p27/`・taxonomy | **無い**(作っていない。取りに行っていない) |
| pytest | 入っている | 入っていなかった → `pip install pytest`(repo の外) |
| `git log --format=%h` の短縮 | 7 字 | **8 字**(object の数が違うため。§4) |

## §2. 門の数(3 回。同じ HEAD `a18d57f`、同じ機)

| 回 | 条件 | failed | passed | skipped | errors |
|---|---|---|---|---|---|
| 1 | shallow・cache 無し | 181 | 3,623 | 97 | 30 |
| 2 | 全履歴・cache 無し | 80 | 3,744 | 93 | 14 |
| 3 | 全履歴・cache 無し・§4 の直しの後 | 79 | 3,745 | 93 | 14 |

1 → 2 で消えた赤(約 101 + 16)は、全部「封や記録が名指す commit が履歴に無い」型だった(`128 != 0`・`<sha> の木に … が無い`・`fromisoformat('')`・`git log --diff-filter=A` が境界の commit に潰れて「同じ commit に在る」「両向きが真」)。shallow の機では、**順序の門(封 → 材料 → 結果)が「全部同じ commit」と読んで赤になる**。履歴を全部取れば消える。

2 の残り 80 + 14 のうち、**93 件は cache が無いことによる**(`FileNotFoundError: ~/.cache/audit-core/sheet/op20251218_06kessan_01_soukatu.xlsx` 52・`…02_sainyuu.xlsx` 29・`材料が無い` 4・`edinet` 1・taxonomy の label 1、ほか setUp で落ちた分)。残りの **1 件が §4** で、cache とも履歴とも関係が無い。

## §3. 分類の読み方(数ではなく型)

- **履歴の欠け**は clone の仕方の問題で、`--unshallow` 1 回で消える。門が壊れていたのではない。ただし §4 の門だけは、shallow の機で**空で通っていた**(起点の commit が無いと `git log` が失敗し、commit の一覧が空になり、「宣言されていない commit は無い」が真になる)。
- **cache の欠け**は、この repo の作法(材料の ZIP・xlsx は repo の外)の裏返しで、cache の無い機では `test_domain1_*`(表計算)と `test_xbrl_*` の一部が必ず赤になる。門は「cache が無い」で skip する枝を持つものと、持たないものが混ざっている(skip 93 件の中に「cache が無い」「封がまだ commit されていない」が含まれる)。
- どちらも**退行ではない**。cloud の機で緑を言えるのは、cache も履歴も要らない範囲だけで、その範囲は試験 file 179 本のうち cache の道を書いていない 157 本の中に在る(間接に cache を読む file があるので、157 は上限)。

## §4. 門の直し: `test_xbrl_axis3_decision.py` の `test_9_the_engine_was_not_touched`

- **何が起きたか。** 門は `git log --format=%h 2745dd5..HEAD -- adapters core` の出力を、7 字の鍵の辞書 `LATER_ENGINE_COMMITS`(engine を変えた commit と、それを宣言した封の対)に当てていた。`%h` の長さは git が object の数から自動で決める。desktop では 7 字、この機では 8 字になり、**16 commit 全部が「宣言されていない」として赤**になった。16 個を 7 字で切ると辞書と 1 対 1 で合う(衝突なし)。
- **直し。** `--format=%H` を取って `c[:7]` で切る(他の門 `test_xbrl_period_pair_result.py`・`test_domain1_errdet_cprime_result.py`・`test_xbrl_holds_product_path_result.py`・`test_xbrl_period_unit_hold_result.py` が既に使っている `out[-1][:7]` と同じ型)。あわせて `returncode == 0` の assert を足し、**起点が履歴に無い機(shallow)では空で通らず赤になる**ようにした。差分は +6/−2。
- **歯の確認(変異)。** (MA) 鍵 `cb8612f` を 1 つ消す → 赤(`宣言されていない commit: ['cb8612f']`)。(MB) `BASE = "deadbee"` → 赤(`128 != 0 : 起点 deadbee が履歴に無い`)。直した門は 11 passed。
- **独立監査。** step-auditor の判定と気づきは §7 に写す。

## §5. やらなかったこと

- cache を作る・取りに行く(東京都 open data・EDINET)。`sheet/` 5 本は `fixtures/sheet/opened_2026-10-15.json`・`opened_sainyuu_2026-10-16.json` に file 名・sha256・bytes・URL が在るので、持ってくれば照合できる。`edinet/` 281 件の sha256 は便ごとの `fetched_*.json` に分散しており、1 か所にそろっているかは確かめていない。
- 新しい封・測定。直近の結果 `docs/XBRL_DELTA_NAMING_DIAG_2026-10-30.md` §7 の候補は、順位を付けずにそのまま残っている。
- 門の赤 79 + 14 を消すこと(cache の無い機で消すには skip の枝を足すことになり、それは門の動きを変えるので別の便)。

## §6. 移ってきた未追跡 file の扱い

desktop の `scratchpad/` から 6 file が未追跡で届いた(cloud の harness が作った WIP commit `05f55d8` にも同じ blob が在る。HEAD には含めていない)。

- JSON 5 本(`blind51_answer_1〜3.json`・`blind_round2_answer_1〜2.json`)は `fixtures/xbrl/*_2026-10-12.json` と **sha256 が一致**(byte 単位で同じ)。重複なので作業ツリーから除いた。原本は fixtures に在る。
- `final8/q2_options_2026-10-14.md`(sha256 `851c0711…`)は、Q2 の案 A / 案 B を比べた司令塔の下書きで、決定は `docs/Q2_NONCONSOLIDATED_SEAL_2026-10-14.md` に「案 B を採用」として commit 済み。どこにも commit されていなかったので、`docs/Q2_OPTIONS_DRAFT_2026-10-14.md` として末尾に日付つきの追記を付けて残した(本文は 1 字も変えていない)。

## §7. 追記(日付つき)

### 追記 1(2026-11-01。独立監査)

- 判定 **GO**(step-auditor。木は読むだけ、変異は scratchpad のコピーで)。確かめたこと: 差分が 2 点 + コメント 2 行だけ・engine 0 行、直した門 11 passed、自分で考えた変異 2 本で赤(`[:7]` → `[:8]`、`BASE = "0123456"`)、`core.abbrev=7` の 16 行が全部 7 字で衝突なし、`%H` の先頭 7 字と鍵 16 個が 1 対 1、残りの `--format=%h` 4 file は `[:7]` で切っている、凍結 sha256 `814967069b2d4b1a…` が監査の前後で一致。
- 監査の気づき 1: 監査の途中で `fixtures/suite_coverage_2026-10-16.json` が一時的に変わって見えた(`tests` が −1)。原因は並行して走っていた全門の走らせ直し(§2 の 3 回目)で、`tests/measure/test_suite_coverage*.py` の「歯」の試験が記録を 1 か所壊して `--write` で直す型(自分で戻す)。数秒後に木から消えた。**門を走らせている間に `git status` を信じない**、commit はパス指定で、という作法の裏付け。
- 監査の気づき 2: `returncode` の assert は shallow の機ではこの門を赤にする。意図どおり(空で通るより、「起点が無い」と明示される方がよい)。
- §2 の 3 回目の行は、走らせ直しが終わる前に見込みの数を書いてしまい、終わってから実測(79 / 3,745 / 93 / 14)と一致することを確かめた。2 回目との赤の差は `Axis3Test.test_9` の 1 本だけ(FAILED/ERROR の一覧の diff)。
