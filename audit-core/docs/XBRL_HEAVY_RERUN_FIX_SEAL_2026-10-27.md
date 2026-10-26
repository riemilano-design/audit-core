# 封: 環境変数つきの重い走らせ直し 3 本の赤を、宣言された遷移で直す ― 2026-10-27

**司令塔の依頼(2026-10-27)。直すのは試験のコードだけで、engine(`core/`・`adapters/`)・記録(`fixtures/**/*.json`)・過去の封と結果の文書は 1 字も変えない。** engine を触らないので人間の承認は要らない(CLAUDE.md の作法 2)。ただし試験のコードは動きを変える変更なので、独立監査(`step-auditor`)の GO を経てから commit する(作法 3)。0 USD・通信なし・鍵の環境変数は使わない・読まない。数を見てから封・予測を直さない。外れは外れとして残す。

**この封の commit 時点では、3 本の試験 file は HEAD `8372b5e` のまま(1 字も直していない)。**

## §0 根拠(棚卸し。この封のための診断で、記録ではない)

### §0-1 重い走らせ直しの全部(HEAD `8372b5e` の使い捨ての clone で、2026-10-27 に測った)

`grep -l "AUDIT_CORE_" tests/measure/*.py` で 18 file。環境変数で重い試験を走らせるのは下の 12 の環境変数で、走らせた file は表の 14 本。残りの 4 file(`test_packaging_result.py`・`test_packaging_seal.py`・`test_xbrl_default_p26_seal.py`・`test_xbrl_ritual_seal.py`)は環境変数の字を docstring か文書の検査に使うだけで、環境変数で走る試験を持たない(grep で読んだ)。1 つの環境変数ごとに、その変数を読む file を `python3 -m pytest -q -rfEs -p no:cacheprovider` で走らせた。clone は 6 本(`8372b5e` に checkout、走らせた後も `git status` は 6 本とも空)、TMPDIR は scratchpad の下。**儀式(`AUDIT_CORE_RITUAL`)以外の 11 本は 5 本ずつ並べて走らせた**ので、秒は負荷の下の数で、単独の所要ではない。儀式だけは他の走らせ直しが終わってから単独で走らせた(時間の門があるため)。

| 環境変数 | 走らせた file | 結果(pytest の最後の行) | 重い試験 | 赤の要点 | 秒 |
|---|---|---|---|---|---|
| `AUDIT_CORE_CUSTOMER_REPORT` | `test_xbrl_customer_report_result.py` | 1 failed, 34 passed | `RerunTest.test_heavy_everything_matches_the_record` **赤** | 最初に落ちたのは `C3`(登録簿の理由 16 → 19)。§0-2 | 151 |
| `AUDIT_CORE_CUSTOMER_REPORT_FIX` | `test_xbrl_customer_report_fix_result.py` | 1 failed, 32 passed | `RerunTest.test_heavy_everything_matches_the_record` **赤** | 最初に落ちたのは `R2-7`(vocabulary.py ほかの sha)。§0-2 | 185 |
| `AUDIT_CORE_PERIOD_BIND` | `test_xbrl_period_bind_result.py`・`test_xbrl_period_bind_seal.py` | 1 failed, 60 passed | `RerunTest.test_heavy_stage2_default_matches_the_record` **赤**。同じ file の `test_heavy_everything_matches_the_record` と seal の `LiveReproductionTest.test_g1_cost_26_is_reproduced` は緑 | `recipes.py の sha16` が `181b370420ab751b` ≠ 記録の `65a37869f053a60e`。§0-2 | 1,703 |
| `AUDIT_CORE_DEFAULT_P26` | `test_xbrl_default_p26_result.py` | 30 passed | 緑 | ― | 487 |
| `AUDIT_CORE_FRESH` | `test_xbrl_fresh_result.py` | 36 passed | 緑 | ― | 2,393 |
| `AUDIT_CORE_LASTBRANCH` | `test_xbrl_lastbranch_result.py` | 40 passed, 1 skipped | 緑(skip 1 は軽い試験の「engine が宣言された遷移の後」) | ― | 2,101 |
| `AUDIT_CORE_P26` | `test_xbrl_p26_result.py` | 44 passed, 1 skipped | 緑(skip は同上) | ― | 2,414 |
| `AUDIT_CORE_ROUNDING` | `test_xbrl_rounding_result.py`・`test_xbrl_rounding_seal.py` | 47 passed, 1 skipped | 緑(seal の `LiveReproductionTest` 3 本も緑。skip は同上) | ― | 1,220 |
| `AUDIT_CORE_VOCAB` | `test_xbrl_vocab_result.py` | 34 passed, 1 skipped | 緑(skip は同上) | ― | 3,292 |
| `AUDIT_CORE_POINT_PRIOR` | `test_xbrl_point_prior_result.py` | 23 passed | 緑(`HeavyRerunTest.test_11_full_rerun_equals_the_record`) | ― | 272 |
| `AUDIT_CORE_PACKAGING` | `test_packaging.py` | 30 passed | 緑(venv・wheel の 5 本。pip は `--no-index`) | ― | 20 |
| `AUDIT_CORE_RITUAL`(単独) | `test_xbrl_ritual_result.py` | 37 passed | 緑(`RerunHeavyTest` の test_4 は 22.8 秒、test_6 の時間の門も緑) | ― | 26 |

- **赤は 3 本だけで、司令塔の言う 3 本と同じ。** ほかの 9 つの環境変数の重い試験は全部緑。儀式の時間の門は単独で緑で、走らせ直しは要らなかった。
- 軽い門(同じ `8372b5e` の clone、`python3 -m pytest -q -p no:cacheprovider tests/measure`): **2964 passed, 34 skipped、赤 0**(1,129 秒。他の走らせ直しと並べた負荷の下)。
- 覆いの検査(`python3 -B measure/suite_coverage_2026-10-16.py`、読むだけ): 試験 file 222、pytest の収集 4599 本、discover の収集 4503 本で、記録 `fixtures/suite_coverage_2026-10-16.json` と同じ。
- 客 A の出力(`AUDIT_CORE_CUSTOMER_OUT`)は渡していない。報告形の直しの重い試験の `R2-6` の比べは、渡さないと試験の中で飛ばされる(skip でなく比べない)。**R2-6 は測っていない。**
- cache の件数(走らせる前 → 後): `~/.cache/audit-core/edinet/` **281 → 281**、`edinet-fresh-2026-10-21/` **40 → 40**(ほか `edinet-demo-cabocia` 3 → 3、`edinet-taxonomy` 3 → 3、`edinet-taxonomy-ifrs` 0 → 0、`sheet` 10 → 10)。

### §0-2 赤 3 本の出力の差(記録との欄ごとの差。時間の欄を除く)

試験が出力を捨てるので、同じ clone で試験の関数(`run_script`・`RerunTest._script().stage2_default`)を呼んで出力を JSON に書き、記録と葉の欄ごとに比べた(scratchpad の診断。正本でない)。**3 本とも、試験が比べる欄のうち測った値の欄は 1 字も違わない。** 違うのは下の欄だけ。

**T-1 報告形**(`fixtures/xbrl/customer_report_2026-10-21.json`。試験が比べるのは `書類別`・`集計`(P22・P25)・`抜粋`・`C3`・`C4`・`C5`):

- 一致: `書類別`(67 書類 × 2 profile、`verify 秒` を除く)・`集計`・`抜粋`・`C4`、`入力の sha256` も一致。
- `C3` の 5 欄が違う。原因は登録簿の理由が 16 → 19(P26 の段 1 `b778dd9` が `other_concept` を POINTER_NOT_FOUND に、`direction_on_cause_item`・`rounded_diff_within_double_band` を UNVERIFIABLE に足した)。重い走らせ直しは**測った当時の module(c13a746)の理由の表**を使うので、表は 16 のまま、登録簿だけが 19 になる: `登録簿の理由` の 2 つの一覧と `数`(16 → 19)・`登録簿 − 理由の表`([] → 3 つ)・`登録簿 − UNBOUND_REASON_STATE`・`実測に出なかった登録簿の理由`・`1 つ消したときの網羅の検査` の 16 の値(どれも 3 つが足される)。**got の C3 からその 3 つを除くと、記録の C3 と == で一致した。** 測った reason の欄(`実測に出た reason`・`実測に出た reason のうち表の外`・`profile 別の reason の件数`)と `UNBOUND_REASON_STATE の key の数`・`UNBOUND_REASON_STATE − 登録簿`・`理由の表の key の数`・`理由の表 − 登録簿` は一致。got の C3 を `json.dumps(…, ensure_ascii=False, sort_keys=True)` の UTF-8 にした sha256 は `9584cc05006c3b357298fa35cd83f295f726ec93c5be38b5e412681d6d6d1437`(記録の C3 は `2e3123c4eeb7fd98d5c7b1d8b12475586ca599bcf714629e79e9307338ba8413`)。
- `C5` の 6 欄が違う: `sha256` の `vocabulary.py`(`27e71e98…` → `e28733067b1f17f5…`)・`recipes.py`(`bff243f1…` → `181b370420ab751b…`)・`registry_setup.py`(`f42ffe23…` → `7f2cbded9c830211…`)、`engine の指紋` の `adapter_xbrl_py_sha256`(`c556de1c…` → `5aba7749259683563c37e62353717f64b4e4828931998a7c42518aca107f3504`)、`report_customer.py の sha256`(`d8248169…` → `141767d189b63733…`)、`report_customer.py の行数`(518 → 1025)。`report.py`・`verify_document.py` の sha256、`HEAD からの差分`(5 file とも「0 行」)、`engine の指紋` の `adapter_xbrl_py_files`・`core_py_sha256`・`core_py_files`、`adapters/xbrl の .py の数`、`core/ の HEAD からの差分` は一致。
- いまの試験は `C3` で止まるので `C5` の比べに届いていない。`C5` は、いまの試験の「動いた 3 欄」(`report_customer.py` の sha256・行数・`engine の指紋`)のほかに `sha256` の 3 欄が違うので、`C3` を直しても `C5` で赤のまま。
- 試験が比べない欄で違ったもの: `環境/HEAD`・`環境/DEFAULT_PROFILE`(P22 → P26)・`C1`(客 A の出力を渡していない)・`予測の判定` の C-1(判定しない)と C-3(外れ)・`所要秒`。

**T-2 報告形の直し**(`fixtures/xbrl/customer_report_fix_2026-10-21.json`。試験が比べるのは `書類別`・`集計`・`抜粋`・`R2-5`・`R2-7`・(客 A の出力があれば `R2-6`)・`予測の判定` の R2-1〜R2-7 の `判定`(R2-6 は客 A の出力があるときだけ)):

- 一致: `書類別`・`集計`・`抜粋`・`R2-5`、`予測の判定` の R2-1〜R2-5 の `判定`(どれも「当たり」)。
- `R2-7` の 12 欄が違う: `sha256` と `sha16` の `vocabulary.py`・`recipes.py`・`registry_setup.py`(6 欄。値は T-1 と同じ)、`封の commit 時点の sha16 と同じ` の同じ 3 file(true → false)、`engine の指紋` の `adapter_xbrl_py_sha256`(`11840a09…` → `5aba7749…`)、`report_customer.py の sha256`(`71546869…` → `141767d189b63733…`)、`report_customer.py の行数`(1020 → 1025)。`report.py`・`verify_document.py`・`comparators.py` の sha256・sha16・`封の commit 時点の sha16 と同じ`(true)、`HEAD からの差分`(6 file とも「0 行」)、`engine の指紋` の残り 3 欄、`core/ の HEAD からの差分`、`adapters/xbrl の .py の数` は一致。
- `予測の判定` の R2-7 の `判定` が「当たり」→「外れ」。`実測` の字は、記録の字の「sha16 が封の commit 時点と同じ True」(1 か所)を「sha16 が封の commit 時点と同じ False」に置き換えた字と == で一致した。R2-7 の判定は script が「いまの木の sha16 が封の commit 時点の sha16 と同じか」で求めるので、engine の遷移だけで「外れ」になる。
- 試験が比べない欄で違ったもの: `環境/HEAD`・`R2-6`(客 A の出力を渡していない)・`予測の判定` の R2-6(判定しない)・`所要秒`。

**T-3 期の縛りの段 2**(`fixtures/xbrl/period_bind_2026-10-20.json` の `stage2_default_2026-10-20`。試験が比べるのは `E1`・`E2`・`対照: 既定を P21 に戻す変異(比較器が差を拾えるか)`・`差 0 の行数`・`差のあった行の合計`・`DEFAULT_PROFILE`・`recipes.py の sha16`・`vocabulary.py の sha16`・`engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)`・`E5`(`所要秒` を除く)):

- 一致: `E1`・`E2`・`E5`・`対照…`・`差 0 の行数`・`差のあった行の合計`・`DEFAULT_PROFILE`(`"P22"`。段 2 の便で測定は測った当時の P22 に固定してある)。
- 違う 3 欄: `recipes.py の sha16`(`65a37869f053a60e` → `181b370420ab751b`)・`vocabulary.py の sha16`(`25a3c0992e10daaa` → `e28733067b1f17f5`)・`engine の束ねた sha256`(`a0c92547a59802172340fa73c1aa97eac4763b1adaac62e8ab57aa5ad6b24e34` → `4f417562d322caa7241199d8462783e6a260a275a4e2794d18396a3bc6dc6b39`)。
- 試験が比べない欄で違ったもの: `HEAD`・`engine の file 数`(36 → 37。`report_customer.py` が足された)・`既存試験`(試験は `run_tests=False` で呼ぶので false)・`所要秒`。

### §0-3 いつから赤か(静的な読み。走らせて確かめてはいない)

- T-1・T-2: 記録の `C5`・`R2-7` の vocabulary.py・recipes.py・registry_setup.py の sha は `9577eab`(P25 段 1)から `129ee9d` までの値で、`b778dd9`(P26 段 1)で動いた。`C3` の登録簿も `b778dd9` で動いた。= `b778dd9` から赤(司令塔の言うとおり)。
- T-3: 試験は `recipes.py の sha16` を記録の `65a37869f053a60e`(`d0b544c` の値)と == で比べ、その字は `d0b544c` から `8372b5e` まで同じ。recipes.py の sha16 は `7d530cc`(P23 段 1)で `d5308700eae78c10` に動いた。**= 静的には `7d530cc` から赤で、`b778dd9` からではない**(`git show <commit>:audit-core/adapters/xbrl/recipes.py` の sha256 と、各 commit の試験の比べの字から読んだ)。直し方は変わらない。
- P26 の既定の段 2 の結果(`fixtures/xbrl/default_p26_2026-10-23.json` の `試験の赤/S9/実装の後`)は、この 3 本を「段 2 の前から赤」と記録している。その記録は当時の事実として残し、この封は書き換えない。

## §1 対象・除外・触ってよい file

### §1-1 対象(直す試験 3 本)

- **T-1** `tests/measure/test_xbrl_customer_report_result.py` の `RerunTest.test_heavy_everything_matches_the_record`(`AUDIT_CORE_CUSTOMER_REPORT=1`)
- **T-2** `tests/measure/test_xbrl_customer_report_fix_result.py` の `RerunTest.test_heavy_everything_matches_the_record`(`AUDIT_CORE_CUSTOMER_REPORT_FIX=1`)
- **T-3** `tests/measure/test_xbrl_period_bind_result.py` の `RerunTest.test_heavy_stage2_default_matches_the_record`(`AUDIT_CORE_PERIOD_BIND=1`)

§0-2 のとおり、3 本とも測った値の欄は記録と一致したので、3 本とも遷移で直してよい(「測った値の欄が 1 つでも違えば遷移で直さない」に当たる試験は 0 本)。

### §1-2 除外

- 緑だった 9 つの環境変数の重い試験(§0-1)。T-3 と同じ file の `test_heavy_everything_matches_the_record`(緑)。
- `R2-6`・`C1`(客 A の出力。repo の外で、この封は渡していない・測っていない)。客 A の出力を渡したときの比べ方は変えない。
- engine(`core/`・`adapters/`)、記録(`fixtures/**/*.json`。`fixtures/suite_coverage_2026-10-16.json` の `--write` だけは §5 の条件で例外)、`measure/` の script、過去の封・結果の文書(`docs/XBRL_*_SEAL_*`・`docs/XBRL_*_RESULT_*`)。
- `adapters/xbrl/verify_document.py` の docstring の HUMAN の項目(封 `docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md` §1-3)、`docs/DECISION_LOG.md`、axis3 の `LATER_ENGINE_COMMITS`(engine の commit が無いので宣言は要らない)。
- 試験が今比べていない欄(T-1 の `環境`・`C1`・`予測の判定`、T-2 の `環境`、T-3 の `HEAD`・`engine の file 数`・`既存試験`)を新しく比べに足すこと。

### §1-3 触ってよい file(これだけ)

1. `tests/measure/test_xbrl_customer_report_result.py`
2. `tests/measure/test_xbrl_customer_report_fix_result.py`
3. `tests/measure/test_xbrl_period_bind_result.py`
4. `fixtures/suite_coverage_2026-10-16.json`(`python3 measure/suite_coverage_2026-10-16.py --write` の出力だけ。手で書かない)
5. `docs/FACTS_FOR_BUYERS_2026-10-20.md` の §6 の A-08・A-09 の 2 行(§5)
6. 結果の文書 `docs/XBRL_HEAVY_RERUN_FIX_RESULT_2026-10-27.md`(新しく。文書だけ)

**試験 file は足さない。** 新しい試験の method は 1 file に 1 本だけ足す(§4)。`docs/SUITE_COVERAGE_2026-10-16.md` §2-1・`README.en.md`・FACTS の A-06・A-07 は試験 file の数(222・157)なので動かない(動いたら H-4 の外れ)。

## §2 直し方の規則

### §2-1 共通の手順(3 本とも同じ形。実装者はこの順にだけ書く)

各 file に、門の側の関数 `heavy_rerun_check(got, rec, later)` を 1 つ足す(T-2 だけ引数 `cust` を足して `heavy_rerun_check(got, rec, later, cust)`)。`got` は走らせ直しの出力、`rec` は記録(T-3 は `rec[STAGE2]`)、`later` は §2-2〜§2-4 の宣言の dict。食い違えば `AssertionError`(`assert` で。既存の `check_record` と `MutationTest._red` の型と同じ)。重い試験の本体は、走らせ直しの後この関数を `later=HEAVY_RERUN_LATER` で 1 回呼ぶだけにする(いまの比べの行はこの関数に移し、比べる欄の集合は §1-2 のとおり今と同じ)。

1. `g`・`r` を `got`・`rec` から、試験が今比べている欄だけ取り出した deepcopy にする。時間の欄(T-1・T-2 の `書類別` の各行の `verify 秒`、T-3 の `E5` の `所要秒`)は今と同じく除く。
2. `later` の各行 `(path, (後の値, 封の path, 桁))` について、`g` の `path` の値を `v`、`r` の同じ path の値を `w` とする。`桁` が 16 なら `v[:16]` と `w[:16]` で比べ、`None` なら値そのもので比べる。
   - `v == w`(測った当時の値)なら何もしない。
   - そうでなければ、`git log --diff-filter=A --format=%H -- <封の path>`(cwd は audit-core)の出力が空でないこと、かつ `v`(または `v[:16]`)が `後の値` と == であることを `assert` する。通ったら `g` の `path` に `w` を入れ(記録の値に戻す)、`path` を「遷移として受け入れた」集合に足す。
3. §2-2・§2-3 の特別な規則(C3 の 3 つの理由・R2-7 の真偽と判定)を、書いた条件のとおりに当てる。通ったら同じく `g` の該当欄を `r` の値に戻す。
4. 最後に `assert g == r`。**`later` と特別な規則に名前の無い欄は、1 字でも違えば赤**(byte 一致のまま)。

`HEAVY_RERUN_LATER` の値は、既存の定数(`UNTOUCHED_LATER`・`MODULE_LATER`・`ENGINE_ADAPTER_SHA_LATER`・`ENGINE_FP_LATER`・`ENGINE_LATER`・`SEAL_P26`・`SEAL_DEFAULT_P26`)が既に持つ値は**その定数を参照して**作り(同じ sha を 2 か所に字で書かない)、既存の定数に無い値だけを字で書く。**既存の定数の値・key は変えない・足さない。**

### §2-2 T-1(報告形)

`HEAVY_RERUN_LATER`(path → (後の値, 封, 桁)):

| path | 後の値 | 封 | 桁 | 出どころ |
|---|---|---|---|---|
| `("C5", "sha256", "adapters/xbrl/vocabulary.py")` | `e28733067b1f17f5` | `SEAL_DEFAULT_P26` | 16 | `UNTOUCHED_LATER` を参照 |
| `("C5", "sha256", "adapters/xbrl/recipes.py")` | `181b370420ab751b` | `SEAL_P26` | 16 | `UNTOUCHED_LATER` を参照 |
| `("C5", "sha256", "adapters/xbrl/registry_setup.py")` | `7f2cbded9c830211` | `SEAL_P26` | 16 | `UNTOUCHED_LATER` を参照 |
| `("C5", "report_customer.py の sha256")` | `141767d189b63733` | `SEAL_P26` | 16 | `MODULE_LATER` を参照 |
| `("C5", "report_customer.py の行数")` | `1025` | `SEAL_P26` | None | **新しく字で**(§0-2 の実測) |
| `("C5", "engine の指紋", "adapter_xbrl_py_sha256")` | `5aba7749259683563c37e62353717f64b4e4828931998a7c42518aca107f3504` | `SEAL_DEFAULT_P26` | None | `ENGINE_ADAPTER_SHA_LATER` を参照 |

**C3 の特別な規則**: `g["C3"] != r["C3"]` のとき、`SEAL_P26` が履歴に在り(上の 2 と同じ `git log --diff-filter=A`)、`A = P26_REASONS`(既存の定数、3 つ)として次の全部が成り立つときだけ `g["C3"]` を `r["C3"]` に戻す:

- (i) `g["C3"]["登録簿の理由"]["POINTER_NOT_FOUND"] == r["C3"]["登録簿の理由"]["POINTER_NOT_FOUND"] + ["other_concept"]`
- (ii) `g["C3"]["登録簿の理由"]["UNVERIFIABLE"] == r["C3"]["登録簿の理由"]["UNVERIFIABLE"] + ["direction_on_cause_item", "rounded_diff_within_double_band"]`
- (iii) `g["C3"]["登録簿の理由"]["数"] == r["C3"]["登録簿の理由"]["数"] + 3`
- (iv) `g["C3"]["登録簿 − 理由の表"] == sorted(A)`
- (v) `"登録簿 − UNBOUND_REASON_STATE"` と `"実測に出なかった登録簿の理由"` のそれぞれで `g == sorted(set(r) | A)`
- (vi) `"1 つ消したときの網羅の検査(消した key → 表に無い登録簿の理由)"` の key の集合が g と r で同じで、各 key で `g[k] == sorted(set(r[k]) | A)`
- (vii) C3 の key の集合が g と r で同じで、上に名前の無い 7 欄(`UNBOUND_REASON_STATE の key の数`・`UNBOUND_REASON_STATE − 登録簿`・`理由の表の key の数`・`理由の表 − 登録簿`・`実測に出た reason`・`実測に出た reason のうち表の外`・`profile 別の reason の件数`)が ==

byte 一致のまま(`later` に無い): `書類別`(P22・P25)・`集計`(P22・P25)・`抜粋`・`C4`・C5 の `sha256` の `report.py`・`verify_document.py`・`HEAD からの差分(git diff --numstat)`・`engine の指紋` の `adapter_xbrl_py_files`・`core_py_sha256`・`core_py_files`・`adapters/xbrl の .py の数`・`core/ の HEAD からの差分`。

いまの試験の `MODULE_LATER` で分ける枝(`report_customer.py の sha256` が同じか違うか)と `moved` の 3 欄は、この関数に置き換えて消す(`report_customer.py の行数` を値を見ずに通していた所が、1025 を見るようになる)。

### §2-3 T-2(報告形の直し)

`HEAVY_RERUN_LATER`:

| path | 後の値 | 封 | 桁 | 出どころ |
|---|---|---|---|---|
| `("R2-7", "sha256", "adapters/xbrl/vocabulary.py")` と `("R2-7", "sha16", "adapters/xbrl/vocabulary.py")` | `e28733067b1f17f5` | `SEAL_DEFAULT_P26` | 16 | `UNTOUCHED_LATER` を参照 |
| `("R2-7", "sha256", "adapters/xbrl/recipes.py")` と `("R2-7", "sha16", "adapters/xbrl/recipes.py")` | `181b370420ab751b` | `SEAL_P26` | 16 | `UNTOUCHED_LATER` を参照 |
| `("R2-7", "sha256", "adapters/xbrl/registry_setup.py")` と `("R2-7", "sha16", "adapters/xbrl/registry_setup.py")` | `7f2cbded9c830211` | `SEAL_P26` | 16 | `UNTOUCHED_LATER` を参照 |
| `("R2-7", "report_customer.py の sha256")` | `141767d189b63733` | `SEAL_P26` | 16 | `MODULE_LATER` を参照 |
| `("R2-7", "report_customer.py の行数")` | `1025` | `SEAL_P26` | None | **新しく字で** |
| `("R2-7", "engine の指紋", "adapter_xbrl_py_sha256")` | `5aba7749259683563c37e62353717f64b4e4828931998a7c42518aca107f3504` | `SEAL_DEFAULT_P26` | None | `ENGINE_FP_LATER` を参照 |

**R2-7 の真偽の特別な規則**: `("R2-7", "封の commit 時点の sha16 と同じ", <file>)` が `false` で記録が `true` のとき、同じ `<file>` の `("R2-7", "sha16", <file>)` を手順 2 で遷移として受け入れていたときだけ `true` に戻す(受け入れていない file の `false` は赤)。

**R2-7 の判定の特別な規則**: `g["予測の判定"]["R2-7"]` が `r` と違うとき、上の真偽の規則で 1 つ以上の file を戻していて、かつ `g` の `判定` が `"外れ"`、`実測` が `r` の `実測` の `"sha16 が封の commit 時点と同じ True"`(ちょうど 1 か所)を `"sha16 が封の commit 時点と同じ False"` に置き換えた字と == のときだけ、`r` の値に戻す。比べるのは今と同じく `判定`(この規則のために `実測` も見る)。

byte 一致のまま: `書類別`・`集計`・`抜粋`・`R2-5`・(`cust` のとき)`R2-6`・`予測の判定` の R2-1〜R2-5(と `cust` のとき R2-6)の `判定`、R2-7 の `report.py`・`verify_document.py`・`comparators.py` の `sha256`・`sha16`・`封の commit 時点の sha16 と同じ`、`HEAD からの差分(git diff --numstat)`、`engine の指紋` の残り 3 欄、`core/ の HEAD からの差分`、`adapters/xbrl の .py の数`。

### §2-4 T-3(期の縛りの段 2)

`HEAVY_RERUN_LATER`:

| path | 後の値 | 封 | 桁 | 出どころ |
|---|---|---|---|---|
| `("recipes.py の sha16",)` | `181b370420ab751b` | `SEAL_P26` | None | 既存の `ENGINE_LATER["adapters/xbrl/recipes.py"]` を参照 |
| `("vocabulary.py の sha16",)` | `e28733067b1f17f5` | `SEAL_DEFAULT_P26` | None | 既存の `ENGINE_LATER["adapters/xbrl/vocabulary.py"]` を参照 |
| `("engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)",)` | `4f417562d322caa7241199d8462783e6a260a275a4e2794d18396a3bc6dc6b39` | `SEAL_DEFAULT_P26` | None | **新しく字で**(§0-2 の実測。他の門の定数を import しない) |

byte 一致のまま: `E1`・`E2`・`E5`(`所要秒` を除く)・`対照: 既定を P21 に戻す変異(比較器が差を拾えるか)`・`差 0 の行数`・`差のあった行の合計`・`DEFAULT_PROFILE`(`"P22"`)。

束ねた sha256 は `d0b544c` の後 7 つの engine の commit(`7d530cc`・`c7ad668`・`9577eab`・`c13a746`・`129ee9d`・`b778dd9`・`917157c`)で動いたが、宣言は既存の門と同じく**いまの値を作った最後の commit の封**(`SEAL_DEFAULT_P26`)1 つで行う。途中の commit は axis3 の `LATER_ENGINE_COMMITS` が既に全部を宣言している。

### §2-5 名前(既存の門が数える行頭の名前を新しく定義しない)

- 新しく足すのは、各 file の行頭の `HEAVY_RERUN_LATER = {` 1 つ・関数 `heavy_rerun_check`・`MutationTest` の method `test_mh_heavy_rerun_transitions` 1 本だけ。
- **行頭の `ENGINE_LATER`・`UNTOUCHED` を新しく定義しない。** P26 の封の門 `test_xbrl_p26_seal.py` の `PIN_DEF`(行頭の `ENGINE_LATER`・`ENGINE_AT_SEAL`・`UNTOUCHED`・`FROZEN_LATER`・`LATER_ENGINE_COMMITS`・`LATER_FINGERPRINT`・`FINGERPRINT_LATER`・`FINGERPRINT_AT_SEAL`・`LATER_TARGET`・`LATER_FROZEN`・`FROZEN_BUNDLE_AT_SEAL`・`TARGET_AT_SEAL` を単語の境で探す)と、P25 の封の門 `test_xbrl_lastbranch_seal.py` の test_10 ほか(行頭の `ENGINE_LATER = {` を数える)、行頭の `DEFAULT_PROFILE`・`FROZEN_COUNT`・`FROZEN_BUNDLE_GENERATIONS` を見る門がある。`HEAVY_RERUN_LATER` はどれにも当たらない(2026-10-27 に `grep -rn "HEAVY_RERUN\|heavy_rerun_check\|test_mh_heavy_rerun" tests measure docs fixtures` で 0 件)。
- 既存の行頭の定義(T-1・T-2 の `UNTOUCHED`・`UNTOUCHED_LATER`、T-3 の `ENGINE_LATER` など)の行は 1 字も変えない。
- 各 file の module docstring の末尾に、日付つき(2026-10-27)の追記を 1 段落だけ足す(前例: 報告形の門の 2026-10-21 追記)。既存の docstring の字は消さない。

## §3 事前予測(実装の前に固定。外れうる形で欄ごとに)

| # | 予測 | 外れ方 |
|---|---|---|
| **H-1** | 直した木の clone で 1 つの環境変数ずつ走らせると、T-1 の file は **36 passed・赤 0**(いま 1 failed, 34 passed)、T-2 の file は **34 passed・赤 0**(いま 1 failed, 32 passed)、`AUDIT_CORE_PERIOD_BIND=1` で T-3 の file と `test_xbrl_period_bind_seal.py` は **62 passed・赤 0**(いま 1 failed, 60 passed)。増えた 1 本は各 file の `test_mh_heavy_rerun_transitions` | 赤が 1 本でも残る / passed の数が違う / skip が出る |
| **H-2** | ほかの 9 つの環境変数の重い走らせ直しは §0-1 と同じ最後の行(DEFAULT_P26 30 passed、FRESH 36 passed、LASTBRANCH 40 passed・1 skipped、P26 44 passed・1 skipped、ROUNDING 47 passed・1 skipped、VOCAB 34 passed・1 skipped、POINT_PRIOR 23 passed、PACKAGING 30 passed、RITUAL 単独で 37 passed) | 1 つでも違う / 赤が出る |
| **H-3** | 軽い門 `python3 -m pytest -q tests/measure` は **2967 passed, 34 skipped、赤 0**(いま 2964 passed, 34 skipped) | passed が 2967 でない / skip が 34 でない / 赤が 1 本でも |
| **H-4** | 覆い: `--write` の後、試験 file **222** のまま・`tests/measure` **157** のまま、pytest の収集 **4602**(いま 4599)、discover の収集 **4506**(いま 4503)。`docs/SUITE_COVERAGE_2026-10-16.md` §2-1・`README.en.md`・FACTS の A-06・A-07 は 0 行の差分、A-08・A-09 の 2 行だけ動く | どれか 1 つでも違う |
| **H-5** | 直す commit の差分は §1-3 の file だけ。`core/`・`adapters/`・`measure/`・`fixtures/xbrl/`・`docs/XBRL_*`(この封と結果の文書を除く)は 0 行 | 1 行でも |
| **H-6** | 直した木で T-1 の重い走らせ直しの出力の `C3` を §0-2 と同じ作り(`json.dumps(…, ensure_ascii=False, sort_keys=True)` の UTF-8)にした sha256 は `9584cc05006c3b357298fa35cd83f295f726ec93c5be38b5e412681d6d6d1437`(測り方は §0-2 と同じく、試験の `run_script` を呼んで出力を書く使い捨ての script。scratchpad で) | 違う |
| **H-7** | §4 の変異 V-1〜V-7(各 file の `test_mh_heavy_rerun_transitions` の中)は全部赤、基準 V-0 は緑。手でかける変異 C-1〜C-3 は、どれも `test_mh_heavy_rerun_transitions` を 1 本だけ赤にする(他の試験は赤くならない)。手でかける重い変異 W-1 は 3 本の重い試験をそれぞれ赤にする | 黙る変異が 1 つでも / 他の試験まで赤 |
| **H-8** | 既存の名前を数える門(`test_xbrl_p26_seal.py` test_16、`test_xbrl_lastbranch_seal.py` test_10、`test_xbrl_period_bind_seal.py`・`test_xbrl_rounding_seal.py`・`test_xbrl_vocab_seal.py` の同じ型の試験、`test_xbrl_default_p26_seal.py` test_17)は緑のまま(H-3 に含まれるが、名指しで記録する) | 1 本でも赤 |

本当に外れうるのは H-1(遷移の規則が全部の欄を覆っているか)・H-3 と H-4(足す method が 1 本ずつか、他の門の数え方に当たらないか)・H-6(直した後も出力が同じか)・H-7(変異が黙らないか)。H-2 は対象の外の file なので、変わらないのが当然の確認。

## §4 変異の計画

### §4-1 毎回走る変異(各 file の `MutationTest.test_mh_heavy_rerun_transitions` の中。`subTest` で名を付ける)

基準の標本は記録から作る: `got0 = deepcopy(記録)` に、`HEAVY_RERUN_LATER` の各行の後の値を入れる(桁 16 の欄は `後の値 + 記録の値[16:]`)。T-1 は C3 に §2-2 (i)〜(vi) の形で `P26_REASONS` を足し、T-2 は `封の commit 時点の sha16 と同じ` の 3 file を false に、R2-7 の判定を「外れ」・実測を置き換えた字にする。

- **V-0**(緑): `heavy_rerun_check(got0, 記録, HEAVY_RERUN_LATER)` が通る。`got = deepcopy(記録)`(測った当時の値のまま)も通る。
- **V-1** 封の path を在らない file に: `later` の 1 行の封を `docs/XBRL_NO_SUCH_SEAL_2026-10-27.md` に → 赤。
- **V-2** 後の値を 1 字変える: `later` の 1 行の後の値の最後の 1 字を変える → 赤。
- **V-3** 測った値の欄を 1 つ変える: T-1 は `got0["集計"]["P22"]["節"]["違う"]` に 1 を足す、T-2 は `got0["集計"]["P25"]["節"]["一致"]` に 1 を足す、T-3 は `got0["差のあった行の合計"]` に 1 を足す → 赤。
- **V-4** byte 一致のままの留めを変える: T-1 は `got0["C5"]["engine の指紋"]["core_py_sha256"]` を `"0" * 64`、T-2 は `got0["R2-7"]["sha16"]["adapters/xbrl/report.py"]` を `"0" * 16`、T-3 は `got0["DEFAULT_PROFILE"]` を `"P26"` → 赤。
- **V-5** 宣言の無い欄に後の値を入れる: T-1 は `got0["C5"]["sha256"]["adapters/xbrl/report.py"]` を vocabulary.py の後の値の頭 16 字 + 残り、T-2 は `got0["R2-7"]["sha16"]["adapters/xbrl/comparators.py"]` を `"181b370420ab751b"`、T-3 は `got0["E5"]["通した"]["件"]` に 1 を足す → 赤。
- **V-6**(T-1)`P26_REASONS` に無い理由 `"zz_reason"` を `got0["C3"]["登録簿の理由"]["UNVERIFIABLE"]` の末尾に足し `数` も 1 足す → 赤。(T-2)真偽の 3 file を false のまま、`sha16` の 3 欄を記録の値に戻す(遷移が無いのに false)→ 赤。(T-3)束ねた sha256 を P22 の段 2 の値でも後の値でもない `"0" * 64` → 赤。
- **V-7**(T-1)`"other_concept"` を `POINTER_NOT_FOUND` から外して `UNVERIFIABLE` の末尾に → 赤。(T-2)R2-7 の `実測` の置き換えた字に 1 字足す → 赤。(T-3)`recipes.py の sha16` を P23 の段 1 の値 `d5308700eae78c10`(途中の値。宣言していない)に → 赤。

### §4-2 手でかける変異(凍結の前に、worktree で 1 回ずつ。結果の文書に記録。門ではない)

- **C-1** `heavy_rerun_check` の封の履歴の `assert` を消す → `test_mh_heavy_rerun_transitions` が赤(V-1 が黙らない)。
- **C-2** 後の値の比べを常に真にする → 赤(V-2・V-6(T-3)・V-7(T-3)が黙らない)。
- **C-3** 最後の `assert g == r` を消す → 赤(V-3・V-4・V-5 が黙らない)。
- **W-1** 重い経路: 3 file それぞれで `HEAVY_RERUN_LATER` の 1 行の封の path を在らない file にして、環境変数をつけて重い試験だけを走らせる → 3 本とも赤。戻した後に同じ試験が緑(戻しは置換でなく、凍結した file の写しで byte 一致に戻す)。

## §5 覆い(試験の method を足すので)

- 試験 file は足さない。method を 3 本(1 file に 1 本)足すので、収集の本数が動く。直した後に `python3 measure/suite_coverage_2026-10-16.py --write` を走らせ、`fixtures/suite_coverage_2026-10-16.json` を書き直す(忘れると `test_suite_coverage.py` test_37 が「記録が古い」で赤)。
- `docs/FACTS_FOR_BUYERS_2026-10-20.md` §6 の A-08(pytest の収集本数)・A-09(discover の収集本数)の 2 行の数と〔rec …〕の字を、書き直した記録の値に合わせる(`test_facts_for_buyers.py` test_21 が記録と突き合わせる)。A-06・A-07・`docs/SUITE_COVERAGE_2026-10-16.md` §2-1・`README.en.md` は試験 file の数なので触らない(H-4)。
- 試験 file を足すことになったら(この封の外)、それは封の外れで、§2-1 の 222・157 と README.en.md・FACTS の A-06〜A-09 を全部直す必要が出る。その前に止めて司令塔に戻す。

## §6 承認と順序

- engine を触らないので人間の承認は要らない。**独立監査(`step-auditor`)の GO を経てから commit する。** feature 上の commit の承認は司令塔に委任(`docs/AGENT_PROTOCOL.md` の「承認の委任」)。
- 順序: **この封を commit** → 実装(別席。worktree か clone で。重い走らせ直しは共有の木で走らせない)→ §4-2 の手の変異 → 凍結(触った file の sha256 の一覧)→ 独立監査 → GO → パス指定で commit → 結果の文書 `docs/XBRL_HEAVY_RERUN_FIX_RESULT_2026-10-27.md`(予測 H-1〜H-8 の当たり外れ、走らせた環境変数と最後の行、cache の件数の前後)。
- 走らせるたびに `~/.cache/audit-core/edinet/`(281)と `~/.cache/audit-core/edinet-fresh-2026-10-21/`(40)の件数を前後で数え、結果の文書に書く。cache に file を足さない。

## §7 限界(封の時点で分かっていること)

- 遷移で受け入れるのは「engine の commit が sha を動かした」ことだけで、**記録が測った当時の engine で同じ数が出ることは、この直しの後も重い走らせ直しでは確かめない**(確かめるのは、いまの engine で測った当時の profile を明示して同じ数が出ること)。測った当時の engine での再現は、その時点の記録と commit に頼る。
- T-1 の C3 は、測った当時の module(c13a746)の理由の表が P26 の 3 つの理由を持たないことを「宣言された遷移」として受け入れる。いまの module の表が 19 を覆うことは、既存の軽い試験(`test_6_c3_is_recomputed_from_the_module_and_the_registry_not_the_record` の `live_c3`)が別に縛る。
- T-2 の R2-7 の判定「外れ」を受け入れるのは、script が判定を「いまの木の sha16 が封の時点と同じか」で求めるため。記録の判定「当たり」は 1 字も変えない。
- 結果の文書の数(H-1〜H-8 の実測)は手の実測で、記録(fixtures)と門には縛らない(新しい試験 file を足さないため)。結果の門を足すかどうかは司令塔が決める。
- 客 A の出力を渡したときの T-2 の `R2-6` は測っていない。
- 秒(§0-1)は並べて走らせた負荷の下の数で、所要の予測には使わない。

## §8 司令塔の決定(2026-10-27、封の commit の前。封を書く席が挙げた 6 点)

1. **C3**: §2-2 の特別な規則のとおり、登録簿の字の遷移として受け入れる。C3 は測った当時の module の理由の表と登録簿の差で、材料を測った値ではない。いまの表が登録簿を覆うことは軽い試験 `test_6_c3_is_recomputed_from_the_module_and_the_registry_not_the_record` が別に縛る(§7)。
2. **R2-7 の判定**: §2-3 の特別な規則のとおり受け入れる。記録の判定「当たり」は 1 字も変えない。結果の文書に「いまの木で求め直すと外れになるが、それは宣言された engine の遷移による」と書く。
3. **T-3 の赤の始まり**: §0-3 の静的な読み(`7d530cc` から)を結果の文書にそのまま書き、「走らせて確かめてはいない」と添える。走らせての確認はしない。
4. **method の追加**: §4 のとおり 1 file に 1 本足す。遷移の規則を、環境変数なしの軽い門で毎回試せるようにするため。§5 の覆いの直しを行う。
5. **結果の門**: 新しい試験 file は足さない。結果の文書の数は手の実測で門に縛らないことを、文書の冒頭に書く(§7 の最後から 3 つ目)。
6. **H-2**: 測る。ほかの 9 つの重い走らせ直しを、直した木の clone で全部走らせ、最後の行を結果の文書に書く。
