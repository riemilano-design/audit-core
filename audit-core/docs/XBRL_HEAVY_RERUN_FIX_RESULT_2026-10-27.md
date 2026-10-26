# 結果: 環境変数つきの重い走らせ直し 3 本の赤を、宣言された遷移で直した ― 2026-10-27

封: `docs/XBRL_HEAVY_RERUN_FIX_SEAL_2026-10-27.md`(commit `c8fadf2`。本文は 1 字も直していない)。

**この文書の数は手の実測で、記録(`fixtures/`)にも門にも縛っていない(新しい試験 file を足さないため。封 §7・§8 の 5)。** 数を読む人は、下の clone での走らせ直しを同じ手順で再現できる。**0 USD・通信なし・鍵の環境変数は外して走らせた(`env -u`)。** 読みはエージェント(実装の席)の読みで、人間の読みではない。独立監査の GO の前の報告で、commit はしていない。

## 0. 結論

- 直したのは試験のコード 3 file だけ(engine・記録・過去の封と結果は 0 行)。重い走らせ直しの赤 3 本は、直した木の clone で全部緑になった(H-1 当たり)。
- 緑だった他の 9 つの環境変数の重い走らせ直しは、直した木の clone でも封 §0-1 と同じ最後の行だった(H-2 当たり)。
- 予測 H-1〜H-8: 当たり 8・外れ 0。ただし変異の予測(`mut_predictions.txt`)の数え間違いが 1 か所ある(§4)。
- 遷移の規則は各 file の `MutationTest.test_mh_heavy_rerun_transitions` が環境変数なしで毎回試す。手の変異 C-1〜C-3・W-1 は、予測どおり、規則の側の assert を消すと赤くなった。
- 測っていないもの: 客 A の出力を渡したときの T-2 の `R2-6`(渡していない)。測った当時の engine での再現(封 §7)。

## 1. 変えた file(主の木。`git diff HEAD --numstat`)

| file | 追加 | 削除 | 中身 |
|---|---|---|---|
| `tests/measure/test_xbrl_customer_report_result.py`(T-1) | 128 | 16 | `HEAVY_RERUN_LATER`・`heavy_rerun_check`・`test_mh_heavy_rerun_transitions`・docstring の追記・重い試験の比べを関数の呼び出しに |
| `tests/measure/test_xbrl_customer_report_fix_result.py`(T-2) | 120 | 10 | 同上(`heavy_rerun_check(got, rec, later, cust)`) |
| `tests/measure/test_xbrl_period_bind_result.py`(T-3) | 90 | 7 | 同上(`rec` は `rec[STAGE2]`) |
| `fixtures/suite_coverage_2026-10-16.json` | 2 | 2 | `--write` の出力だけ(pytest 4599 → 4602、discover 4503 → 4506) |
| `docs/FACTS_FOR_BUYERS_2026-10-20.md` | 2 | 2 | §6 の A-08(4599 → 4602)・A-09(4503 → 4506)の 2 行だけ |
| `docs/XBRL_HEAVY_RERUN_FIX_RESULT_2026-10-27.md` | 新規 | ― | この文書 |

- 新しく足した名前は、各 file の行頭の `HEAVY_RERUN_LATER = ...` 1 つ・関数 `heavy_rerun_check` 1 つ・method `test_mh_heavy_rerun_transitions` 1 本だけ(封 §2-5)。補助の関数・定数は `heavy_rerun_check` の中の入れ子と method の中の局所にした。行頭の `ENGINE_LATER`・`UNTOUCHED` などは新しく定義していない。既存の定数の値・key は変えていない。
- 比べる欄の集合は今と同じ(`pick` が取る欄は旧い比べの欄と一致)。`HEAVY_RERUN_LATER` の値は既存の定数(`UNTOUCHED_LATER`・`MODULE_LATER`・`ENGINE_ADAPTER_SHA_LATER`・`ENGINE_FP_LATER`・`ENGINE_LATER`・`SEAL_P26`)を参照し、新しく字で書いたのは行数 1025(T-1・T-2)と T-3 の束ねた sha256 `4f417562…6dc6b39` だけ。
- 責務境界: engine(`core/`・`adapters/`)・`measure/`・`fixtures/xbrl/`・過去の封と結果の文書は 0 行。既存の試験は変えていない(重い試験の本体の比べの行だけが関数の呼び出しに移った)。

## 2. 予測 H-1〜H-8 の当たり外れ

| # | 予測 | 実測 | 当たり外れ |
|---|---|---|---|
| H-1 | T-1 の file 36 passed・赤 0 / T-2 の file 34 passed・赤 0 / `AUDIT_CORE_PERIOD_BIND=1` で T-3 の file と period_bind の seal 62 passed・赤 0。skip なし | T-1 **36 passed**(いま 1 failed, 34 passed だったもの)/ T-2 **34 passed** / T-3 + seal **62 passed**。skip 0・赤 0 | **当たり** |
| H-2 | 他の 9 つの環境変数は封 §0-1 と同じ最後の行 | §3 の表のとおり 9 つとも同じ | **当たり** |
| H-3 | `tests/measure` は 2967 passed, 34 skipped、赤 0 | 直した木の clone(`c8fadf2` に直した file を写したもの)で **2967 passed, 34 skipped**、赤 0 | **当たり**(この文書を足した後の再走も 2967 passed, 34 skipped。§2-1) |
| H-4 | 試験 file 222・`tests/measure` 157 のまま、pytest 4602・discover 4506。`SUITE_COVERAGE` §2-1・`README.en.md`・FACTS の A-06・A-07 は 0 行、A-08・A-09 の 2 行だけ | `--write` の出力は 222 file・`tests/measure` 157・pytest **4602**・discover **4506**(漏れ 1 本は `measure/tests/test_inject.py` で従来どおり)。FACTS は A-08・A-09 の 2 行だけ(`facts_check` の A-08・A-09 は OK 1 / NG 0)。`README.en.md`・`SUITE_COVERAGE` は触っていない | **当たり** |
| H-5 | 差分は §1-3 の file だけ。`core/`・`adapters/`・`measure/`・`fixtures/xbrl/`・`docs/XBRL_*`(封とこの文書を除く)は 0 行 | §5 | **当たり**(数え方は §5) |
| H-6 | 直した木で T-1 の重い走らせ直しの出力の `C3`(`json.dumps(…, ensure_ascii=False, sort_keys=True)` の UTF-8)の sha256 は `9584cc05…d6d1437` | `run_script` を呼んで書いた出力の C3 で **`9584cc05006c3b357298fa35cd83f295f726ec93c5be38b5e412681d6d6d1437`**(§0-2 と 1 字も違わない) | **当たり** |
| H-7 | V-1〜V-7 は全部赤・V-0 は緑。C-1〜C-3 は `test_mh_heavy_rerun_transitions` を 1 本だけ赤にする。W-1 は 3 本の重い試験を赤にする | 3 file の軽い門で `test_mh…` は 113 passed の中で緑(V-0 緑・V-1〜V-7 赤が毎回確かめられる)。手の変異は §4 | **当たり** |
| H-8 | 既存の名前を数える門は緑のまま | `tests/measure` 全体が緑(H-3)。名指しの確認は §2-2 | **当たり** |

### 2-1 この文書を足した後の再走

この文書を clone に写した後で `tests/measure` をもう一度走らせた: **2967 passed, 34 skipped**、赤 0(753 秒)。文書を足しても、結果の文書を走査する門・`test_facts_for_buyers.py` の `test_19`(`docs/<stem>*RESULT*` が無いことを見る)は赤にならなかった。

### 2-2 名指しの門(`-v` で緑を確かめた)

- `test_xbrl_p26_seal.py` の `test_16_every_engine_pin_gate_of_the_past_is_listed`: PASSED
- `test_xbrl_lastbranch_seal.py` の `test_10_engine_pins_list_is_written_and_exists`: PASSED
- `test_xbrl_period_bind_seal.py` の `test_9_engine_pins_list_is_written_and_exists`・`test_xbrl_rounding_seal.py` の `test_8_…`・`test_xbrl_vocab_seal.py` の `test_10_…`: 3 本とも PASSED
- `test_xbrl_default_p26_seal.py` の `test_17_live_pin_set_only_grows_by_the_named_new_gates`: PASSED
- 上の 6 file と `test_facts_for_buyers.py`・`test_suite_coverage.py` をまとめて走らせて **171 passed, 6 skipped**(skip 6 は従来どおり)。

## 3. 走らせた環境変数ごとの最後の行(直した木の clone。5 本並べて走らせたので秒は負荷の下の数)

| 環境変数 | 最後の行 | 封 §0-1 の行 | 同じか |
|---|---|---|---|
| `AUDIT_CORE_CUSTOMER_REPORT` | 36 passed in 145.52s | 1 failed, 34 passed | 赤が緑に(H-1) |
| `AUDIT_CORE_CUSTOMER_REPORT_FIX` | 34 passed in 179.50s | 1 failed, 32 passed | 赤が緑に(H-1) |
| `AUDIT_CORE_PERIOD_BIND`(result + seal) | 62 passed in 1892.90s | 1 failed, 60 passed | 赤が緑に(H-1) |
| `AUDIT_CORE_DEFAULT_P26` | 30 passed in 529.55s | 30 passed | 同じ |
| `AUDIT_CORE_FRESH` | 36 passed in 2689.93s | 36 passed | 同じ |
| `AUDIT_CORE_LASTBRANCH` | 40 passed, 1 skipped in 2398.18s | 40 passed, 1 skipped | 同じ |
| `AUDIT_CORE_P26` | 44 passed, 1 skipped in 2810.33s | 44 passed, 1 skipped | 同じ |
| `AUDIT_CORE_ROUNDING`(result + seal) | 47 passed, 1 skipped in 1383.75s | 47 passed, 1 skipped | 同じ |
| `AUDIT_CORE_VOCAB` | 34 passed, 1 skipped in 3732.01s | 34 passed, 1 skipped | 同じ |
| `AUDIT_CORE_POINT_PRIOR` | 23 passed in 338.19s | 23 passed | 同じ |
| `AUDIT_CORE_PACKAGING` | 30 passed in 23.40s | 30 passed | 同じ |
| `AUDIT_CORE_RITUAL` | 37 passed in 31.96s | 37 passed | 同じ |

- 儀式(`AUDIT_CORE_RITUAL`)は他の走らせ直しが終わった後に、この席の走らせとしては単独で走らせた。ただし同じ機械で別の席(P27 の封の下書き)の pytest が同じ時間に走っていた(`pgrep` で見えた)ので、**「機械で単独」ではない**。時間の門は緑だった。
- 客 A の出力(`AUDIT_CORE_CUSTOMER_OUT`)は渡していない。**T-2 の `R2-6` は測っていない。**
- 全体: `tests/measure` 2967 passed, 34 skipped(1,775 秒)。`tests/adapters/xbrl tests/core` **1211 passed, 1 skipped**(1,752 秒)。赤の一覧は空。
- cache の件数(走らせる前 → 後): `~/.cache/audit-core/edinet/` **281 → 281**、`edinet-fresh-2026-10-21/` **40 → 40**(ほか `edinet-demo-cabocia` 3 → 3、`edinet-taxonomy` 1 folder・3 file → 同じ、`edinet-taxonomy-ifrs` 1 folder・0 file → 同じ、`sheet` 10 → 10)。file を足していない。

## 4. 手の変異(予測は走らせる前に書いた。`scratchpad/heavy_fix/impl/mut_predictions.txt`)

かけ先は使い捨ての clone。戻しは凍結した写し(主の木の直した file)を `cp` して `cmp` で byte 一致を確かめた(置換で戻していない)。

| 変異 | 予測 | 実測(`unittest` で `test_mh…` の subTest ごとに) | 当たり外れ |
|---|---|---|---|
| C-1 封の履歴の assert を消す | 3 file とも `test_mh…` だけ赤。割れるのは V-1 の全行(T-1 は 6、T-2 は **12**、T-3 は 3) | pytest では 3 failed・110 passed(赤は 3 file の `test_mh…` だけ)。subTest は T-1 の V-1 が 6 行・T-2 の V-1 が **9 行**・T-3 の V-1 が 3 行、V-2 以降は割れず | 割れる subTest は **当たり**。**T-2 の行数 12 は予測の数え間違い(外れ)**。封 §0-2 の「12 欄」は R2-7 の違った欄の数で、`HEAVY_RERUN_LATER` の行は 9(sha256・sha16 の 3 file ずつ 6 + module の sha256・行数・指紋 3)。真偽の 3 欄は特別な規則の側 |
| C-2 後の値の比べを常に真に | 3 file とも `test_mh…` だけ赤。V-2 の全行。T-3 はさらに V-6・V-7。T-1・T-2 の V-5 は割れない | T-1 は V-2 の 6 行、T-2 は V-2 の 9 行、T-3 は V-2 の 3 行 + V-6 + V-7。pytest で 3 failed・110 passed | **当たり** |
| C-3 `assert g == r` を消す | 3 file とも `test_mh…` だけ赤。割れるのは V-3・V-4・V-5。V-6・V-7・V-1・V-2 は割れない | 3 file とも V-3・V-4・V-5 の 3 つだけ。pytest で 3 failed・110 passed | **当たり** |
| W-1 重い経路: `HEAVY_RERUN_LATER` の 1 行の封を在らない file に | 3 本の重い試験が赤、戻した後(byte 一致)に同じ 3 本が緑 | T-1(`C5/sha256/…/vocabulary.py` の行)**1 failed**(「…遷移を宣言した封 docs/XBRL_NO_SUCH_SEAL_2026-10-27.md が履歴に無い」)→ 戻した後 **1 passed**。T-2(`R2-7/sha16/…/vocabulary.py` の行)**1 failed** → 戻した後 **1 passed**。T-3(`recipes.py の sha16` の行)**1 failed** → 戻した後 **1 passed** | **当たり** |

- 毎回走る V-0〜V-7 は、上の C-1〜C-3 で割れる subTest が予測どおりだったことで、それぞれの assert が別々に効いていることを示す(V-1 は封の履歴、V-2・V-6・V-7 は後の値、V-3・V-4・V-5 は最後の `g == r`)。
- 毎回走る変異は T-1 の C3(V-6: P26_REASONS に無い理由、V-7: `other_concept` を別の群へ)、T-2 の真偽(V-6)と判定の実測の字(V-7)、T-3 の束ねた sha256(V-6)と途中の recipes.py の値(V-7)を、遷移の規則の側の assert で赤にする。

## 5. H-5 の数え方(司令塔の連絡: 作業中に主の木の HEAD が `c8fadf2` → `e37ae3b` に進んだ)

- 足されたのは文書 1 本 `docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md`(P27 段 1 の封。文書だけ)で、この席の対象の file には触れていない。
- **数え方: 作業木の `git diff HEAD`(HEAD = `e37ae3b`)で数えた。** 差分は §1 の 5 file(と、この文書が未追跡)と、**この席が触っていない `docs/DECISION_LOG.md` の既存の変更 17 行(作業の開始時点から M)**だけ。`core/`・`adapters/`・`measure/`・`fixtures/xbrl/`・`docs/XBRL_*`(封とこの文書を除く)の差分は 0 行。
- clone は `c8fadf2` のまま使った(違いは上の文書 1 本だけ)。
- `fixtures/suite_coverage_2026-10-16.json` は HEAD の commit を記録する欄を持たない(`grep -i "head\|commit"` で 0 件)。

## 6. 赤の始まり(封 §0-3。静的な読み)

- T-1・T-2: 記録の `C5`・`R2-7` の sha と `C3` の登録簿は `b778dd9`(P26 の段 1)で動いた。**静的な読みでは `b778dd9` から赤。走らせて確かめてはいない。**
- **T-3: 静的な読みでは `7d530cc`(P23 の段 1)から赤で、`b778dd9` からではない**(試験は `recipes.py の sha16` を記録の `65a37869f053a60e` と == で比べ、その字は `d0b544c` から `8372b5e` まで同じ。`recipes.py` の sha16 は `7d530cc` で `d5308700eae78c10` に動いた。`git show <commit>:audit-core/adapters/xbrl/recipes.py` の sha256 と各 commit の試験の比べの字から読んだ)。**走らせて確かめてはいない。**
- P26 の既定の段 2 の結果(`fixtures/xbrl/default_p26_2026-10-23.json` の `試験の赤/S9/実装の後`)は、この 3 本を「段 2 の前から赤」と記録している。その記録は当時の事実として残し、書き換えていない。

## 7. R2-7(封 §8 の 2)

T-2 の `予測の判定` の R2-7 は、記録では「当たり」だが、**いまの木で求め直すと外れになる。それは宣言された engine の遷移(`vocabulary.py`・`recipes.py`・`registry_setup.py` の sha16 が封の commit 時点から動いた)による**。記録の判定「当たり」は 1 字も変えていない。`heavy_rerun_check` は、同じ file の sha16 の遷移を受け入れて真偽を戻していて、実測の字が「sha16 が封の commit 時点と同じ True」(ちょうど 1 か所)を「… False」に置き換えた字と == のときだけ、この判定の違いを受け入れる。

## 8. 封との食い違い・判断が要ること

- **封との食い違いは無い。** 封の字(§2 の規則・§4 の変異・§5 の覆い)のとおりに実装した。次は実装上の判断で、封の字を越える点を 3 つ書く。
  1. T-1 の C3 の規則で、封の (i)〜(vii) に加えて `登録簿の理由` の key の集合が g と r で同じであることも見る(封は 3 つの key だけを名指しするので、余分な key を黙って通さないための厳しい側の判断)。
  2. T-2 の真偽の規則は「g が false・r が true」のときだけ受け入れる。それ以外の違い(g が true で r が false など)は最後の `g == r` で赤になる。
  3. V-1・V-2 は封の「1 行」でなく `HEAVY_RERUN_LATER` の全行で試す(厳しい側)。
- 補助の関数・定数は封 §2-5 の「新しく足す名前」に合わせて、入れ子と局所にした。
- 変異の予測の数え間違い(T-2 の V-1 が 12 行でなく 9 行)は §4 に外れとして残した。直したのは数え方で、封には影響しない。
- 結果の門を足すかどうかは司令塔の決定(封 §7)。この文書の数は門に縛っていない。
