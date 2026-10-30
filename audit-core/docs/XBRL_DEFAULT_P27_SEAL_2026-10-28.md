# 封: 既定の profile を P26 から P27 に切り替える(段 2)― 2026-10-28

**人間(2026-10-27)「価値を上げるためにも君に任せる 進めよう」(P27 段 2 の進行)。人間(2026-10-28)「君に任せるよ」** ― 司令塔が「既定を P26 から P27 に替えるか・DECISION_LOG の D-024・Cabocia の第 2 の評価用」を人間の決定として挙げた直後の言葉。司令塔の決定(2026-10-28): **既定を P27 に替える(P27E ではない)。** 根拠は、評価用の結果 `docs/XBRL_P27_RESULT_2026-10-27.md`(commit `aeae608`)が封 `docs/XBRL_P27_SEAL_2026-10-27.md` §4 の条件を記録の数から門で求め、**「P27 を既定の候補として記録する」と判定済み**であること(§0-1)。P27E を既定にしないのは、同じ封の §0-3 の 3・§1-2・§8 のとおり、B(相対の近さの名指し)は有報の原文で偽の「違う」を増やすため(§0-2)。`verify_document.py` の docstring「既定 P20」の食い違い(P26 の段 2 の封 §1-3 の HUMAN)も、この便で直す ― 人間の委任(2026-10-28)の範囲として司令塔が決めた(§1-4 の 1)。

この封は、前例 `docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md`(P22 → P26 の段 2、commit `6a78b42` → 実装 `917157c`)と同じ構成で、作法(封 → 実装 → 凍結 → 独立監査 GO → commit)のまま段 2 を行うために、予測・pin の遷移の一覧・代価を実装の前に固定する。数を見てから封・予測を直さない。外れは外れとして残す(補足は日付つきの追記)。**この封の commit 時点では `DEFAULT_PROFILE = "P26"` のまま、`verify_document.py` の docstring も「= P20」のまま。** 0 USD・通信なし・鍵の値は読まない・席(LLM)は呼ばない。この封を書いた席は、評価用・調整用の AI の文・DB の応答(`~/.cache/audit-core/edinetdb-p27/` の下)を開いていない(読んだのは HEAD の記録・文書と、手元の有報の原文の ZIP だけ)。封の本文に評価用・調整用の docID と claim の id は書かない。

- 封の時点: branch `feature/audit-core-final-eval-8`、HEAD `aeae608`(R = 評価用の結果の commit)。`adapters/xbrl/vocabulary.py` の sha16 `85896a67913ce1e7`・`adapters/xbrl/verify_document.py` の sha16 `67e7639de3f5f2ad`・束ねた指紋 `adapter_xbrl_py_sha256` `0e51211a8aed2151…`(16 file)・`core_py_sha256` `34e836bb39762d5a…`(4 file)・frozen_bundle の最新の世代 `29fd733c8988164a…`(37 本)。
- 作業木には commit されていない差分が 1 つ在る: `../docs/DECISION_LOG.md` の D-024(+17 行・−0 行。P26 の段 2 の項目。`aeae608` の木に D-024 は無い)。この封は触らない(§1-4 の 2)。

## §0 根拠(この封は新しく測らない。数は HEAD `aeae608` の記録と文書。試作の数は正本でない)

### §0-1 判定(結果 `docs/XBRL_P27_RESULT_2026-10-27.md` §1。門 `tests/measure/test_xbrl_p27_result.py` が記録から求めた字)

- 封 `docs/XBRL_P27_SEAL_2026-10-27.md` §4: 「**P27 を『既定の候補』として記録する**(既定に替えるのは別の便で人間が決める)のは、K-1・K-4・K-5 を P27 で満たし、K-3 の代わりに『評価用の無改変で P27 の VALUE_MISMATCH の行 ≤ P26 の行』と §5 の N-2 の 4 つの数を満たすとき。」同 §9-5「既定を替えるかは、R の後に人間が決める」。
- 判定(結果 §1 の表 `判定`): 「P27 を『既定の候補』として 記録する」。D の 9 小項目は全部当たり: D-1a T8_REL の通した率 P27 **0.0%**(≤ 2%)・D-1b T1_VALUE の通した行 P27 **0**・D-3 無改変の VALUE_MISMATCH の行 P27 − P26 **−4**(≤ 0)・D-4 P26 で GROUNDED かつ P27 で GROUNDED でない行のうち合わせた側が道具の行 **1**(≤ 3)・D-5 旗が偽の P22・P26 の byte 一致 **97 / 97**・D-N2a〜d 手元の 67 の P27 の GROUNDED **4,371**・VALUE_MISMATCH **433**、新しい標本 30 の **2,194**・**250**(P26 と同じ)。
- 同じ結果で P27E は K-1〜K-5 の 8 小項目が全部当たりで「外部の数の文に使う profile として採用する」。**P27E は既定の候補にしない**(封 §1-2・§10-1)。

### §0-2 評価用 10 社(claim 523)の P26 → P27(結果 §4 の表。負けた数も書く)

| 評価用(無改変・注入) | P22 | P26 | **P27** | P27E |
|---|---|---|---|---|
| GROUNDED / VALUE_MISMATCH / UNVERIFIABLE / POINTER_NOT_FOUND | 254 / 41 / 100 / 128 | 255 / 26 / 100 / 142 | **254 / 22 / 106 / 141** | 254 / 24 / 106 / 139 |
| VALUE_MISMATCH の率 | 7.8% | 5.0% | **4.2%** | 4.6% |
| T8_REL(4 profile で対応が付く 87): 通した | 27(31.0%) | 27(31.0%) | **0(0.0%)** | 0 |
| T8_REL: 名指して原本の値を返した | 53(60.9%) | 36(41.4%) | **27(31.0%)** | 78(89.7%) |
| T8_REL: 名指したが別の値 / 止めたが名指さない | 7 / 0 | 5 / 19 | **5 / 55** | 7 / 2 |
| T1_VALUE(対応 7): 通した / 名指して原本の値 | 0 / 7(100%) | 0 / 7(100%) | **0 / 5(71.4%)** | 0 / 5 |

- **P27 で良くなった数**: T8_REL(相対 ±3%・±10% の値の差し替え)を通した 27 行が 0 になった(封 §1-1 の A の効き。行は 1 つずつ読んでいない)。無改変の VALUE_MISMATCH が 26 → 22。
- **P27 で負けた数(既定にしたときの代価。§3)**: T8_REL で名指して原本の値を返した行が 36 → 27(P26 で「通した」27 のうち 9 は P27 で名指し、18 は止めたが名指さない。「名指して原本の値を返した」36 のうち 18 は P27 で名指さなくなった ― 結果 §4 の表 `注入-交差`)。T1_VALUE で名指して原本の値を返した行が 7 → 5(封 §1-1 の A の代価: 照合の桁が細かくなり証拠 (ii) の桁が細かくなり効かなくなる)。P26 で GROUNDED だった 1 行が P27 で UNVERIFIABLE(`other_frame`)になり、読み手 2 席とも `道具`(= 正しい文の一致を失った。原因は記録に無く読んでいない)。
- P26 → P27 で無改変の判定が動いた行(結果 §4 の表 `動いた行`): GROUNDED → UNVERIFIABLE / other_frame **1**・GROUNDED のまま pointer だけ **2**・POINTER_NOT_FOUND / no_element → UNVERIFIABLE / per_unit_counter **7**・UNVERIFIABLE / ambiguous(elements) → POINTER_NOT_FOUND / no_element **4**・UNVERIFIABLE / ambiguous(elements) → UNVERIFIABLE / no_subject **7**・VALUE_MISMATCH → POINTER_NOT_FOUND / no_same_value **1**・VALUE_MISMATCH → POINTER_NOT_FOUND / other_concept **1**・VALUE_MISMATCH → UNVERIFIABLE / per_unit_counter **2**。VALUE_MISMATCH を離れた 4 行は**読んでいない**(結果 §1 の読み)。
- **読みはエージェントの読み**(同じ model の 2 席)で、人間の読みではない。読む行は 2 行で同じ 1 社(結果 §5)。

### §0-3 手元の 97 書類の有報の原文(記録 `fixtures/xbrl/p27/regress97_2026-10-27.json`。E の engine `b2c3f56` で測った)

- N-1: 旗が偽の P22・P26 は封の時点の engine(`29e6d0a`)と byte 一致 **97 / 97**(どちらも)。
- 手元の 67 書類(claim 7,799)の 4 state、P26 → **P27**: GROUNDED 4,371 → **4,371**・VALUE_MISMATCH 433 → **433**・UNVERIFIABLE 1,579 → **1,601**・POINTER_NOT_FOUND 1,416 → **1,394**。動いた行 **28**(state か reason か pointer が違う行 = state が違う行 = 28。reason だけ違う行 0・GROUNDED のまま pointer が替わる行 0)。向きは POINTER_NOT_FOUND → UNVERIFIABLE **25**・UNVERIFIABLE → POINTER_NOT_FOUND **3**、他の向き 0。VALUE_MISMATCH に入る行 0・新しい GROUNDED 0・GROUNDED を離れる行 0。
- 新しい標本 30 書類(claim 3,923)、P26 → **P27**: GROUNDED 2,194 → **2,194**・VALUE_MISMATCH 250 → **250**・UNVERIFIABLE 774 → **787**・POINTER_NOT_FOUND 705 → **692**。動いた行 **15**(POINTER_NOT_FOUND → UNVERIFIABLE **14**・UNVERIFIABLE → POINTER_NOT_FOUND **1**)。他は 0。
- 動いた行の reason(記録の `動いた行` を数えた): 67 書類は `no_element` → `per_unit_counter` 11・`no_element(unit not in XBRL)` → `per_unit_counter` 6・`no_same_value` → `target_or_plan` 3・`no_element(ratio without fact)` → `target_or_plan` 3・`no_element` → `target_or_plan` 2・`ambiguous(elements)` → `no_element` 3(書類は 12)。30 書類は `no_element(unit not in XBRL)` → `per_unit_counter` 11・`no_element` → `per_unit_counter` 1・`ambiguous(elements)` → `no_element` 1・`no_same_value` → `target_or_plan` 1・`no_element` → `target_or_plan` 1(書類は 10)。
- 規則ごとに当たった claim(記録の `規則ごとに当たった claim の数`): P27 で C2 `per_unit_counter` **17**(67)・**12**(30)、C3 `future_period` **8**・**2**、C1 の窓に入った claim **5**・**7**(うち `other_concept` になった 0・0)。B は 0(P27 には無い)。
- **P27E を既定にしない数**: 同じ 97 書類で P27 → P27E は VALUE_MISMATCH に入る行(`no_same_value` → VALUE_MISMATCH)が 67 書類で **81**・30 書類で **24**(P25 の結果は有報の原文で名指さなくなった行のほぼ全部を正しい文と読んだ。この 81 + 24 行は読んでいない)。
- 動いた行はどれも UNVERIFIABLE と POINTER_NOT_FOUND の間で、顧客向け報告形では「要確認」の節の中の理由が替わる(`per_unit_counter` の理由は報告形の理由の表に 1 行、`target_or_plan` は「目標・計画の数(実績ではない)」)。「違う」「一致」の節は動かない(§2 の S-5 で確かめる)。

### §0-4 試作(scratchpad の clone。正本でない。`<S>/d27_seal/probe/`。記録に無い。実装席が同じ測定を記録に出す)

`aeae608` を clone し、`adapters/xbrl/vocabulary.py` の `DEFAULT_PROFILE` の 1 行だけを `"P27"` にした(`git diff --numstat` 1/1。vocabulary.py の sha16 `d1d5d37c07ee3094`・束ねた指紋 `4e7536bc569197b1…`・frozen_bundle `22a720df2d8d33e2…` 37 本。verify_document.py は `67e7639de3f5f2ad` のまま)。TMPDIR と pycache は scratchpad の下。鍵の環境変数は `env -u` で外して走らせた(`ANTHROPIC_BASE_URL` の名前だけは環境に在ったが、値は読まない・鍵ではない)。cache(`~/.cache/audit-core/edinet/` 281・`edinet-fresh-2026-10-21/` 40)には 1 file も足していない(§5 の末尾)。

1. **S-1〜S-3**(97 書類を profile 省略・P27 明示・既定を実行中だけ P26 に戻した対照の 3 通りで `verify_document`): 省略と P27 明示の `sort_keys` の JSON が違った書類 **0 / 67・0 / 30**。対照で違った書類 **67 / 67・30 / 30**。既定の 4 state は §0-3 の P27 の数と**全部同じ**(67: 4,371 / 433 / 1,601 / 1,394、30: 2,194 / 250 / 787 / 692)。対照(P26)と state の違う行 **28・15**、向きと reason の内訳は §0-3 と同じ集合(docID・id・前・後の組が regress97 の `動いた行` と**集合として一致**、過不足 0)。state が同じで reason か pointer が違う行 **0・0**。
2. **S-4** 儀式(同梱の 1 書類、既定 = P27): 通した **2 / 243 = 0.8%**・止めた(VALUE_MISMATCH)**210 / 243 = 86.4%**・POINTER_NOT_FOUND **31**。素の書類(claim 412)GROUNDED **340**・POINTER_NOT_FOUND **25**・UNVERIFIABLE **33**・VALUE_MISMATCH **14**(P26 の記録は 340 / 27 / 31 / 14。2 行が POINTER_NOT_FOUND → UNVERIFIABLE)。通した 2 の中身(帯の中 1 = 率 1・退化値 1・帯の外 0)と通した行の (id, 型) の一覧は P26 の記録と同じ。参照先が前期へ移って通した行 0。型別は V1 対象 119・通した 1・止めた 99、V2 対象 124・通した 1・止めた 111。P26 の記録 `fixtures/xbrl/ritual_2026-10-20.json` と違う欄(所要秒・実行環境を除く)は **3 つ**: `入力`(`profile` が P26 → P27)・`注入`(`土台(経営分析の文のまま)の state の分布` の POINTER_NOT_FOUND 27 → 25・UNVERIFIABLE 31 → 33)・`素の書類`(同じ `state の分布`)。`通した`・`止めた`・`止めた でも 通した でもない結果`・`通した の分け方`・`型別`・`通した の一覧`・`注入の一覧` は同じ。
3. **S-5** 報告形(67 書類、既定): 違う **433**・要確認 **1,773**・対象外 **145**・判断しない **1,077**・一致 **4,371**(合計 7,799。P26 の記録は 433 / 1,775 / 151 / 1,069 / 4,371)。「違う」= VALUE_MISMATCH の行(差 0)。
4. **S-6** 誤りを通す側(既定): 穴 B の注入 485 件で通した **0 / 485**・止めた **480**・その他 **5**。P26 の記録(`fixtures/xbrl/p26_2026-10-21.json` の Q3)の P26 の欄と 1 行ずつ(結果・state・reason・pointers)比べて違った行 **0**(P26 明示の対照と違った行も 0)。段 2 の材料の注入 64 件で Core 自身が GROUNDED にした **0 / 64**、P26 の記録の P26 の欄と違った行 **0**。
5. **S-8** 試験の赤(§2 の S-8 の幅の出どころ): `python3 -m pytest -q -rfEs -p no:cacheprovider` で `tests/measure` は **81 failed, 3228 passed, 34 skipped**(赤 81 本・**29 file**)、`tests/adapters/xbrl tests/core tests/golden tests/fixtures measure/tests` は **16 failed, 1487 passed, 1 skipped**(赤 16 本は全部 `tests/adapters/xbrl` の **11 file**。`tests/core`・`tests/golden`・`tests/fixtures`・`measure/tests` の赤 0)。合計 **97**。種類(赤の assertion を 1 本ずつ読んで分けた): (1) engine の sha16・束ねた指紋・frozen_bundle・「engine が動いていない」を留める門 **37**(29 file のうち §4 (a) の 26 file 全部 + `test_xbrl_p27_engine_result.py`・`test_xbrl_p27_result.py` の test_61)、(2) 既定の字(`"P26"`)と「既定は P26」を見る試験 **17 + 16**(`tests/measure` 17: `test_xbrl_branch_a.py` test_3・`test_xbrl_fresh_result.py` test_6・`test_xbrl_lastbranch_result.py` test_8・`test_xbrl_lastbranch_seal.py` test_9・test_14・`test_xbrl_naming_fix_result.py` test_14・`test_xbrl_p26_result.py` test_8・`test_xbrl_p27_result.py` test_65・`test_xbrl_p27_seal.py` test_2・test_6・`test_xbrl_period_bind_result.py` test_9・test_13・`test_xbrl_period_bind_seal.py` test_13・`test_xbrl_rounding_result.py` test_8・`test_xbrl_rounding_seal.py` test_12・`test_xbrl_vocab_result.py` test_8・`test_xbrl_vocab_seal.py` test_14。`tests/adapters/xbrl` 16: `test_p17.py` 1・`test_p20.py` 1・`test_recipes_p21.py`〜`test_recipes_p27.py` 各 1(7)・`test_run.py` 2・`test_verify_entry.py` 5。どれも assertion は `'P27' != 'P26'` の形)、(3) 既定を前提に走らせ直す門 **9**(`test_xbrl_default_p26_result.py` の `test_light_two_documents_match_the_record`・`test_xbrl_period_bind_result.py` の `test_light_stage2_the_comparator_sees_a_wrong_default`・`test_xbrl_ritual_result.py` の `LabelTest` test_13・test_14・test_17(guard が P26 でないと rc 1)と `PredictionTest` test_8(判定の字が「外れ」になる)・`test_xbrl_point_prior_result.py` の test_3・test_6・test_m0(B-5 の判定を作業木の `git diff` で求め直す))、(4) 変異の baseline の連鎖 **18**(`test_baseline_is_green` 8 本と「誤った engine の sha が赤」の変異 7 本(`m14`・`m21`・`m20`・`m17`・`m16` ×2・`m10`)・`test_xbrl_p27_seal.py` の `m2`・`m5`・`test_xbrl_period_bind_result.py` の `ms6`)。37 + 17 + 9 + 18 = 81。記録(fixtures)の数・state を書き換えないと緑にならない門 **0**、人間の決定の字の門の赤 **0**。P27 の門 5 本の赤: `test_xbrl_p27_result.py` **2**(test_61・test_65)・`test_xbrl_p27_seal.py` **7**(test_2・test_5・test_6・test_7・test_9・m2・m5)・`test_xbrl_p27_engine_result.py` **3**(test_5・test_7・m10 ― 記録が測った engine の指紋といまの指紋の比べ)・`test_xbrl_p27_eval.py` **0**(作り物の vocab で走る)・`test_xbrl_p27_order.py` **0**。試作は docstring の 1 行を直していないので、§4 (a′) の 14 file のうち試作で赤でなかった `test_xbrl_role_swap_result.py`・`test_xbrl_verify_inventory.py` と `test_xbrl_default_p26_seal.py` の test_7 は数に入っていない。
6. **S-9** 重い走らせ直し(`AUDIT_CORE_*` 12 変数): 12 変数を試作の clone の写し 4 つで走らせた(`PACKAGING`〜`DEFAULT_P26`・`VOCAB`・`PERIOD_BIND`・`FRESH`・`ROUNDING`・`P26`・`LASTBRANCH` は 5 本までを並べて、`RITUAL` は最後に単独)。pytest の最後の行: `PACKAGING` 30 passed・`CUSTOMER_REPORT` 3 failed / 33 passed・`CUSTOMER_REPORT_FIX` 3 failed / 31 passed・`POINT_PRIOR` 4 failed / 19 passed・`DEFAULT_P26` 5 failed / 25 passed・`FRESH` 5 failed / 31 passed・`ROUNDING` 6 failed / 41 passed / 1 skipped・`VOCAB` 4 failed / 30 passed / 1 skipped・`P26` 4 failed / 40 passed / 1 skipped・`PERIOD_BIND`(result + seal)9 failed / 53 passed・`LASTBRANCH` 4 failed / 36 passed / 1 skipped・`RITUAL` 6 failed / 31 passed。軽い門(S-8)の赤を除いて**増えた赤は 7 本**: `test_xbrl_customer_report_result.py` の `RerunTest.test_heavy_everything_matches_the_record`(最初に落ちた欄は `C5/engine の指紋/adapter_xbrl_py_sha256`)・`test_xbrl_customer_report_fix_result.py` の同名(`R2-7/engine の指紋/adapter_xbrl_py_sha256`)・`test_xbrl_default_p26_result.py` の同名(script が「既定 profile が P26 でない」で止まる)・`test_xbrl_fresh_result.py` の同名(vocabulary.py の sha16 の組)・`test_xbrl_period_bind_result.py` の `RerunTest.test_heavy_stage2_default_matches_the_record`(`engine の束ねた sha256`)・`test_xbrl_ritual_result.py` の `RerunHeavyTest.test_4`(guard「既定 profile が P26 でない」で rc 1)と `test_6`(同じ理由で時間の門も落ちる)。`PACKAGING`・`POINT_PRIOR`・`ROUNDING`・`VOCAB`・`P26`・`LASTBRANCH` の 6 変数は増えた赤 0(重い試験は緑)。増えた 7 本はどれも最初に engine の sha・指紋・既定の欄で落ちており、**測った値の欄まで比べには届いていない**(試験は最初の assertion で止まる。測った値の欄が 1 字も違わないかは実装席が封 `docs/XBRL_HEAVY_RERUN_FIX_SEAL_2026-10-27.md` §0-2 の型で欄ごとに比べる)。秒は並べた負荷の下の数で単独の所要ではない。

## §1 変えるもの(engine 2 file の 2 行。残りは試験・記録・文書)

### §1-1 engine

- `adapters/xbrl/vocabulary.py`: `DEFAULT_PROFILE = "P26"` を `DEFAULT_PROFILE = "P27"` に(1 行)。その直前の決定の注記の末尾に、日付つきの注記を足す(前例 `917157c` は +4/−1。今回は **+≤ 8/−1**)。注記の字は次の要素を含む(字は実装席が書く): `# 2026-10-28 に P26 -> P27(P27 の段 2)。`・人間の言葉 2026-10-27「価値を上げるためにも君に任せる 進めよう」と 2026-10-28「君に任せるよ」・判定の出どころ `docs/XBRL_P27_RESULT_2026-10-27.md`(aeae608)が封 `docs/XBRL_P27_SEAL_2026-10-27.md` §4 の条件で「既定の候補」と判定したこと・段 2 の封 `docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md`・結果 `docs/XBRL_DEFAULT_P27_RESULT_2026-10-28.md`・「**P26 の字は消さず**」と P26 を明示した呼び出しは変えないこと・P27E は既定にしないこと。**P16・P20・P21・P22・P26 の注記は 1 字も消さない。** `PROFILES` の行・P27・P27E の定義の行は変えない。
- `adapters/xbrl/verify_document.py`: docstring の 1 行(いまの字: `` ``--profile`` を省くと ``vocabulary.DEFAULT_PROFILE``(= P20。2026-10-14 の人間の決定)。 ``)を、次の 1 行に(**+1/−1**。他の行は 0): `` ``--profile`` を省くと ``vocabulary.DEFAULT_PROFILE``(いまは P27。P20 → P21 → P22 → P26 → P27 の履歴と根拠は vocabulary.py の注記。この行は 2026-10-28 の人間の委任「君に任せるよ」で直した)。 ``。**実行の字(`profile_name or V.DEFAULT_PROFILE`・argparse の help)は変えない**(既定の名前を `V.DEFAULT_PROFILE` から引く)。
- **他の engine の行は 0。** `recipes.py`・`extract.py`・`registry_setup.py`・`report_customer.py`・`comparators.py`・`report.py`・`run.py` ほか adapters/xbrl の残り 14 file と `core/` は 0 行(sha16 が封の commit 時点と同じ)。`run.py` は `V.DEFAULT_PROFILE` を引くので変えない。
- P27E の定義・旗の既定値(全部 `False`)・P16〜P27E を明示した呼び出しと試験の数は 1 つも変えない。

### §1-2 既定を名指す字の区分(`git grep -c DEFAULT_PROFILE aeae608 -- .` で **111 file・424 か所**を数えた。直す / 残す)

| 区分 | file | 字 | 直す / 残す |
|---|---|---|---|
| engine | 3 file | 9 | `vocabulary.py`(3)の 1 行と注記を**直す**。`verify_document.py`(3)の docstring の 1 行を**直す**、実行の字 2 は残す。`run.py`(3)は `V.DEFAULT_PROFILE` を引く字で名前を書かない = 残す |
| frozen_bundle | `fixtures/frozen_bundle_sha.py` 1 file | 10 | 世代の一覧に新しい世代を**足す**(過去の世代は消さない。`FROZEN_COUNT` 37 のまま) |
| tests/adapters/xbrl | 11 file | 27 | 既定の字(`"P26"`)と「既定は P26」を見る試験を**直す**(§4 (e)。試作で赤になった本数は §2 の S-8)。P16〜P27E を明示した試験は触らない |
| tests/measure | 38 file | 232 | 封・結果の門が既定を字で留めている所を**直す**(試作で赤になった file は §4 の一覧)。測った当時の既定を字で留めている所(過去の値)は**残す** |
| measure | 16 file | 49 | 既定を前提にして記録を再現する script を**直す**(§4 (g): `ritual_2026-10-20.py` の guard「既定が P26」を P27 に、`xbrl_default_p26_2026-10-23.py` の「既定 = P26」の前提を測った当時の P26 の明示に固定。記録の字は直さない)。記録に `DEFAULT_PROFILE` の欄を書くだけの script は残す。`xbrl_p27_eval_2026-10-27.py` の走る前の確かめ「既定が P26」は**残す**(script の sha256 は記録と結果の門 test_60 が留める。評価用は使い切ったので走らせ直さない。既定が P27 のときは (b) で止まる = 意図どおり) |
| fixtures/xbrl | 14 file | 26 | 測った記録の中の `DEFAULT_PROFILE` の欄。**残す**(記録は 1 字も直さない) |
| docs | 28 file | 71 | 過去の封・結果・文書。**残す**(本文は直さない。足すのは日付つきの追記だけ) |

- 上の表に `DEFAULT_PROFILE` の字が無いが既定を名指す file: `README.md`(「いまの段」の節に P27 の行を足す。P26 の行は「この直前の既定」として残す。「10 分の再現」の節の数を P27 の記録に。P26 のときの数は日付つきで残す)・`README.en.md`(「10-minute reproduction」の節。同じ扱い)= **直す**。`docs/FACTS_FOR_BUYERS_2026-10-20.md` は P26・P27 の字が 0 = **触らない**(§6 の覆いの A-06〜A-09 の 4 行だけ直す)。`docs/SUITE_COVERAGE_2026-10-16.md` §2-1 は覆いの数。
- 儀式(`measure/ritual_2026-10-20.py`): 買い手が今の既定で走らせるもの。guard「既定が P26」を P27 に直し、記録 `fixtures/xbrl/ritual_2026-10-20.json` を P27(既定)で採り直す。P26 の記録は byte 一致の写し `fixtures/xbrl/ritual_2026-10-20_p26.json` と履歴に残す(前例 `_p22.json`・`_p21.json`)。結果文書 `docs/XBRL_RITUAL_RESULT_2026-10-20.md` は本文を直さず末尾に日付つきの追記(§8)。
- 新しい測定: `measure/xbrl_default_p27_2026-10-28.py` → `fixtures/xbrl/default_p27_2026-10-28.json` → `docs/XBRL_DEFAULT_P27_RESULT_2026-10-28.md` → `tests/measure/test_xbrl_default_p27_result.py`(profile 省略 = 既定で §2 の測定をして、P27 明示(`regress97_2026-10-27.json` の P27 の欄)と 1 行ずつ比べる。対照: 既定を実行中だけ P26 に戻すと 97 / 97 違う)。
- 封の門 `tests/measure/test_xbrl_default_p27_seal.py` は**実装の便で足す**(P27 の段 2 の前例: 封の commit は文書だけ)。門が見るもの: この封の冒頭の人間の言葉・§0 の数が記録と同じ・§1-2 の表が `git grep` と同じ・§2 の 12 行に外れ方がある・§4 の一覧が `git grep -l -F <sha16> aeae608 -- tests` と同じ・順序(この封の commit が `aeae608` より後で段 2 の file より前)・評価用・調整用の docID と claim の id(`N\d{3}`・`T\d{3}`)が封の字に 0 件。

### §1-3 HUMAN の残り項目

- **無い。** 前例の §1-3(`verify_document.py` の docstring「既定 P20」)は、この便で直す(§1-1。司令塔が人間の委任 2026-10-28「君に任せるよ」の範囲として決めた。止めるなら §1-4 の 1)。

### §1-4 人間の確認が要りうる点(列挙。封は先に進む前提で書いたが、止めるなら実装の前に)

1. **承認の範囲(「君に任せるよ」の読み)**: 司令塔が「既定を P26 から P27 に替えるか」を人間の決定として挙げた直後の言葉を、既定の切り替えと docstring の 1 行の直しの委任と読んだ。engine の行は `vocabulary.py` の 1 行 + 注記と `verify_document.py` の docstring の 1 行(振る舞いを変える行は `DEFAULT_PROFILE` の 1 行だけ)。P27 の封 §8 は「既定の切り替え・`verify_document.py` の docstring・`DECISION_LOG` は範囲の外(人間が決める)」と書いていた。その「人間が決める」を 2026-10-28 の言葉で満たしたと読む。及ばないと読むなら実装の前に止める。
2. **DECISION_LOG**: `../docs/DECISION_LOG.md` の D-024(P26 の段 2)は作業木に在るが commit されていない(+17 行)。この便では **D-025**(P26 → P27。人間の言葉 2 つ・判定の出どころ・engine の行・P27E を既定にしない理由・言わないこと)を足し、D-024 と同じ便(文書だけ。§5 の末尾)で commit する。D-024 の字は変えない。
3. **`verify_document.py` の docstring**(§1-1)。engine の file なので、sha16 を留める門 14 本 + measure 1 本(§4 (a′))に宣言された遷移が要る。
4. **P27E を既定にしない理由**: 封 `docs/XBRL_P27_SEAL_2026-10-27.md` §0-3 の 3・§1-2 の代価・§10-1(司令塔の決定「P27E は既定の候補にしない」)。有報の原文で VALUE_MISMATCH に入る行が 67 書類で 81・30 書類で 24(§0-3。読んでいない)。外部の数の文を点検する客には P27E を明示して使う(結果 §1「P27E を『外部の数の文に使う profile』として採用する」)。既定を P27E にするなら、別の封と新しい標本。
5. **読み手の限界**: K-4(= D-4)の「正しい文の一致を失った行 1」は同じ model の 2 席の読みで、人の目は入っていない。読む行は 2 行・1 社。P26 → P27 で VALUE_MISMATCH を離れた 4 行は読んでいない(偽の「違う」が減ったとは言えない)。評価用は使い切った。D-3 の「P27 の VALUE_MISMATCH が P26 以下」は行数だけの判定。

## §2 事前予測(段 2 の実装の前に固定。既定 = profile 省略)

| # | 予測 | 外れ方 |
|---|---|---|
| **S-1** | profile を省いた `verify_document` の出力を `sort_keys` の JSON にした字が、`profile_name="P27"` 明示と 1 byte も違わない: 手元の 67 書類(claim 7,799)で違った書類 **0 / 67**、新しい標本 30 書類(claim 3,923)で **0 / 30**。対照(既定を実行中だけ P26 に戻す)で違う書類は **97 / 97**(出力の `profile` の欄が違う) | 1 書類でも違う / 対照が 97 / 97 でない |
| **S-2** | 67 書類の既定の 4 state は regress97 の P27 の欄のとおり GROUNDED **4,371**・VALUE_MISMATCH **433**・UNVERIFIABLE **1,601**・POINTER_NOT_FOUND **1,394**(合計 7,799)。いまの既定 P26(4,371 / 433 / 1,579 / 1,416)から state の違う行 **28**、向きは POINTER_NOT_FOUND → UNVERIFIABLE **25**・UNVERIFIABLE → POINTER_NOT_FOUND **3**、他の向き **0**。GROUNDED を離れる行 **0**・VALUE_MISMATCH に入る行 **0**・新しい GROUNDED **0**。state が同じで reason か pointer が違う行 **0**。動いた 28 行の (docID, id, 前の state と reason, 後の state と reason) は regress97 の `動いた行` と集合として同じ(過不足 **0**) | 4 state のどれか 1 つでも違う / 行数か向きが違う / 集合が違う |
| **S-3** | 新しい標本 30 書類の既定の 4 state は GROUNDED **2,194**・VALUE_MISMATCH **250**・UNVERIFIABLE **787**・POINTER_NOT_FOUND **692**(合計 3,923)。P26 と state の違う行 **15**、向きは POINTER_NOT_FOUND → UNVERIFIABLE **14**・UNVERIFIABLE → POINTER_NOT_FOUND **1**、他の向き **0**。GROUNDED を離れる行 **0**・VALUE_MISMATCH に入る行 **0**・新しい GROUNDED **0**。動いた 15 行は regress97 の `動いた行` と集合として同じ(過不足 **0**) | 1 つでも違う |
| **S-4** | 儀式(同梱の 1 書類、既定 = P27)は 通した **2 / 243 = 0.8%**・止めた(VALUE_MISMATCH)**210 / 243 = 86.4%**・結べない(POINTER_NOT_FOUND)**31**、素の書類(claim 412)は GROUNDED **340**・POINTER_NOT_FOUND **25**・UNVERIFIABLE **33**・VALUE_MISMATCH **14**(P26 の記録 340 / 27 / 31 / 14 から **2 行**が POINTER_NOT_FOUND → UNVERIFIABLE。GROUNDED・VALUE_MISMATCH は動かない)。通した 2 の中身は 帯の中 **1**(率 1・金額ほか 0)・退化値 **1**・帯の外 **0**、通した行の (id, 型) の一覧は P26 の記録と同じ、参照先が前期へ移って通した行 **0**。採り直した記録が P26 の記録 `ritual_2026-10-20.json` と違う欄(所要秒・実行環境を除く)は **`入力`・`注入`・`素の書類` の 3 つだけ**(`入力` は `profile` の字、`注入` と `素の書類` は `state の分布` の POINTER_NOT_FOUND 27 → 25・UNVERIFIABLE 31 → 33。`通した`・`止めた`・`止めた でも 通した でもない結果`・`通した の分け方`・`型別`・`通した の一覧`・`注入の一覧` は同じ)。いまの P26 の記録は byte 一致の写し `ritual_2026-10-20_p26.json` に残る(sha256 が HEAD `aeae608` の `ritual_2026-10-20.json` と同じ)。README 2 本の数は P27 の記録と 1 対 1 | 1 つでも違う / 写しが byte 一致でない / 違う欄が増える |
| **S-5** | 報告形(`report_customer`)の節の件数、67 書類(claim 7,799)の既定: 違う **433**・要確認 **1,773**・対象外 **145**・判断しない **1,077**・一致 **4,371**(合計 7,799)。「違う」の節 = VALUE_MISMATCH の行(P26 の節は 433 / 1,775 / 151 / 1,069 / 4,371。動くのは 要確認・対象外・判断しない の間だけ(−2・−6・+8)で、「違う」と「一致」は動かない。UNVERIFIABLE が 22 増えて「判断しない」が 8 しか増えないのは、節の割り当てが state だけで決まらないため ― `report_customer` の節の割り当ては変えない) | 1 つでも違う / 「違う」の節と VALUE_MISMATCH が食い違う / 「違う」か「一致」が動く |
| **S-6** | 誤りを通す側(既定): 穴 B の注入 485 件で通した(GROUNDED のまま)**0 / 485**(P26 も 0 / 485)・止めた **480**・その他 **5**、段 2 の材料の注入 64 件で Core 自身が GROUNDED にした **0 / 64**。P26 の記録(`p26_2026-10-21.json` の Q3)の P26 の欄と 1 行ずつ(結果・state・reason・pointers)比べて違う行 穴 B **0**・段 2 **0**(注入の判定は P26 と 1 行も変わらない) | 通した 1 以上 / 違う行の数が違う |
| **S-7** | engine の差分は `vocabulary.py` の挿入 **≤ 8**・削除 **1**(`DEFAULT_PROFILE` の行)と、`verify_document.py` の挿入 **1**・削除 **1**(docstring の 1 行)。adapters/xbrl の他の 14 file と `core/` は 0 行(封の commit 時点と同じ)。束ねた指紋 `adapter_xbrl_py_sha256` と frozen_bundle の世代は動き、`adapter_xbrl_py_files` **16**・`core_py_sha256` `34e836bb39762d5a…`・frozen_bundle の本数 **37** は動かない | 超える / 他の file が動く / 本数が動く |
| **S-8** | `DEFAULT_PROFILE` の 1 行だけを P27 にした作業木(試作。docstring は直していない)で、`tests/measure` の赤 **81 本**(**29 file** = §4 (a) の 26 file + `test_xbrl_naming_fix_result.py`・`test_xbrl_p27_engine_result.py`・`test_xbrl_p27_result.py`)・`tests/adapters/xbrl` の赤 **16 本**(**11 file** = §4 (e) の全部)。合計 **97**。docstring の 1 行も直した作業木では、§4 (a′) の 14 file のうち試作で赤でなかった `test_xbrl_role_swap_result.py`・`test_xbrl_verify_inventory.py` と `test_xbrl_default_p26_seal.py` の test_7 の分が増えて、合計の幅 **98〜105**(増える赤は種類 (1) だけ)。種類は 4 つだけ(試作の内訳: `tests/measure` で (1) **37**・(2) **17**・(3) **9**・(4) **18**、`tests/adapters/xbrl` は 16 本とも (2)): (1) vocabulary.py の sha16・束ねた指紋・frozen_bundle・「engine が E から動いていない」を留める門、(2) 既定の字(`"P26"`)と「既定は P26」を留める試験、(3) 既定を前提に走らせ直す門(儀式の guard と判定・既定 P26 の測定の軽い走らせ直し・期の縛りの対照・点の前期の `git diff`)、(4) 変異の baseline の連鎖。`tests/core`・`tests/golden`・`tests/fixtures`・`measure/tests` の赤 **0**。**記録(fixtures)の数・state を書き換えないと緑にならない門 0**(儀式の記録だけは、買い手が今の既定で走らせるものなので採り直す = S-4)。人間の決定の字(recipes.py の決定の行・P27 の封 §2-2 の 10 項目)を見る門の赤 **0**。P27 の門 5 本の赤: `test_xbrl_p27_result.py` **2**(test_61・test_65)・`test_xbrl_p27_seal.py` **7**・`test_xbrl_p27_engine_result.py` **3**・`test_xbrl_p27_eval.py` **0**・`test_xbrl_p27_order.py` **0** | 幅の外 / 種類の外の赤 / 記録の数を書き換える門が出る / 人間の決定の字の門が赤 / P27 の門の赤の数が違う |
| **S-9** | 重い走らせ直し(`AUDIT_CORE_*=1` の 12 変数。封 `docs/XBRL_HEAVY_RERUN_FIX_SEAL_2026-10-27.md` §0-1 の一覧)を試作の作業木で走らせると、軽い門の赤のほかに増えた赤は **7 本**(報告形 1・報告形の直し 1・既定 P26 の測定 1・新しい標本 1・期の縛りの段 2 の 1・儀式 2)。`PACKAGING`・`POINT_PRIOR`・`ROUNDING`・`VOCAB`・`P26`・`LASTBRANCH` の走らせ直しは増えない。docstring の 1 行を直した作業木では、`verify_document.py` の sha16 を記録と比べる走らせ直し(報告形・報告形の直し)の落ちる欄が増えるが、本数は増えない。段 2 の実装の後は、12 変数の走らせ直しが全部緑(E の commit `b2c3f56` の説明は「重い走らせ直し 12 変数は commit 後に全部緑」。`8372b5e` で赤だった 3 本は封 `c8fadf2` → `40cdd93` で宣言された遷移に直した。この封は HEAD で走らせ直していない) | 増える赤が 7 でない / 実装の後に赤が残る |
| **S-10** | README.md と README.en.md の儀式の節の数は P27 の記録(S-4)と 1 対 1(門が節の全文を縛る)。README.md の「いまの段」に P27 の行が 1 行増え、P26 の行は残る。`docs/FACTS_FOR_BUYERS_2026-10-20.md` の P26・P27 の字は **0** のまま(§6 の覆いの 4 行だけ動く) | 1 つでも違う |
| **S-11** | 覆い: 試験 file の数は、いま(`aeae608`)の **232** から、この封の commit では変わらず **232**(文書だけ)、段 2 の実装の commit で **234**(封の門 `tests/measure/test_xbrl_default_p27_seal.py` と結果の門 `tests/measure/test_xbrl_default_p27_result.py`)。段 2 の実装で試験 file をほかに足さない。`fixtures/suite_coverage_2026-10-16.json` の `uncovered_files` は **0** のまま | 数が違う |
| **S-12** | 判定は、記録(`eval_2026-10-27.json`・`eval_inject_2026-10-27.json`・`eval_readings_2026-10-27.json`・`regress97_2026-10-27.json`)から結果の門が別の関数で D-1・D-3・D-4・D-5・D-N2 を求め直しても **「P27 を既定の候補として記録する」**(9 小項目が全部当たり)。既定を P27 にするのはこの判定と人間の言葉(冒頭)に基づき、この封は判定を覆さない | 違う |

予測 S-1・S-2・S-3・S-4・S-5・S-6 の数の多くは記録(regress97・ritual・p26)の写しと試作の写しで、**当たって当然の再現**(profile 省略が P27 明示と同じ出力を返すことの確認)。本当に外れうるのは S-1(配線)・S-4 の違う欄・S-7(docstring の 1 行が他の行を動かさないか)・S-8(赤の数と種類。docstring の分は試作で測っていない)・S-9・S-11 である。

## §3 既定を替えたときの代価と限界(外れうる予測ではなく、封の時点で分かっている限界。読みはエージェントの読み)

- **C1(1 株当たりの窓)の当たってしまう例**(P27 の封 §1-3): 「1株当たり配当は30円、配当金の総額は5.1億円」の 5.1 億円が VALUE_MISMATCH なら、数の前 20 字に「株当たり」が入るので `other_concept` に止まる(本当の「違う」を「要確認」に弱める)。97 書類では C1 の窓に入った claim 12 のうち `other_concept` になった行は 0(§0-3)。
- **C3(先の決算期)の当たってしまう例**(同 §1-4): 「2027年5月期の予想は…で、当期の営業利益は5.9億円」のように、先の期の字の後ろに同じ文で当期の実績が続くと、実績の数も UNVERIFIABLE(`target_or_plan`)になる。「来期」など年月期の字の無い言い方は拾わない(限界)。
- **A(書かれた桁で照合する)の代価**(同 §1-1): 書き手が書類と違う丸め方で小数を書いた正しい文は一致から外れうる(97 書類の実測では GROUNDED を離れた行 0、評価用で 1 行 = §0-2)。照合の桁が細かくなるので証拠 (ii) も細かくなり、小数つきの数の整数の位を変えた誤りは名指されにくくなる(評価用の T1_VALUE で名指して原本の値を返した行 7 → 5、T8_REL で 36 → 27。**通した行は 27 → 0**。既定を P27 にすると、顧客向け報告で「違う」として原本の値を返す行が減り、「要確認」(`no_same_value`)で止める行が増える)。
- **評価用で P26 → P27 で GROUNDED を離れた 1 行**は、読み手 2 席(同じ model)とも `道具`(正しい文の一致を失った)。原因は記録に無く、行を 1 つずつ読んでいない。
- **読む行は 2 行・1 社**(結果 §5・§6)。K-3・K-4 の閾値(2 行・3 行)はこの標本では満たしやすい。「偽の『違う』が増えなかった」証拠ではない。
- **P27 で UNVERIFIABLE に動く行**(97 書類で 25 + 14)は顧客向け報告形で「要確認」の節に出る。その理由は `per_unit_counter`(「1人当たり」「1株当たり」の「1」。数の主張ではない)と `target_or_plan`(先の決算期の数)。P26 では同じ行が POINTER_NOT_FOUND(`no_element`・`no_same_value`・`no_element(ratio without fact)`・`no_element(unit not in XBRL)`)で、同じく「要確認」の節だった(節の間の移動は S-5 で数える)。逆に UNVERIFIABLE → POINTER_NOT_FOUND の 3 + 1 行(`ambiguous(elements)` → `no_element`)は、§0-2 の評価用でも同じ向きが 4 行ある。原因は読んでいない。
- **注入で通した件数は変わらない**(試作: 穴 B 0 / 485・止めた 480・その他 5、段 2 の材料 0 / 64。P26 の記録と 1 行も違わない)。P27 は有報の原文の注入(前期の値への置き換え・桁・単位)に対して P26 と同じ止め方で、良くなるのは外部の数の文の T8_REL(相対の小さな差)だけ。
- **97 書類では GROUNDED・VALUE_MISMATCH の数が P26 と 1 行も変わらない**ので、有報の原文を点検する使い方で P27 が P26 より良くなる数は、この標本では無い(動いた行は全部 UNVERIFIABLE と POINTER_NOT_FOUND の間)。既定を替える益は、外部の数の文(億円の小数)を既定のまま通す客に対して A が効くこと(評価用で通した 27 → 0)。
- **文2(DB の値 = 翌期の有報の前期の欄)はこの標本で起きえない**(P27 の封の追記)。P27 はこの型を測っていない。
- 書き手も読み手も同じ model。評価用の XBRL は見たことのある書類で、新しいのは AI の文の側だけ(P27 の封 §8)。
- 試作の赤の数(S-8)と重い走らせ直し(S-9)は試作の clone の実測で、記録に無い。実装席が同じ測定を記録に出す。試作は docstring の 1 行を直していないので、S-8 の幅はその分を §4 (a′) の数から見込んだ。

## §4 pin の遷移の一覧(段 2 の同じ便で。数は `git grep` で `aeae608` の木から数えた。封の門(実装の便)が実物から数え直す)

**(a) `adapters/xbrl/vocabulary.py` の sha16 `85896a67913ce1e7` を字で留める門 26 本**(`git grep -l -F 85896a67913ce1e7 aeae608 -- tests` で数えた全部。どれも `tests/measure`)。段 2 で vocabulary.py が動くので、この 26 本それぞれに後の sha16 を宣言された遷移として足す(測った当時の値 `85896a67913ce1e7`(P27 の段 2)・`e28733067b1f17f5`(P26 の段 2)ほかは消さない。受け入れるのは、この封が履歴に在り、値が段 2 の後の値のときだけ ― 前例 `917157c` と同じ形)。試作で赤になった本数は S-8:

  - `tests/measure/test_xbrl_a_core_vs_grep_seal.py`
  - `tests/measure/test_xbrl_axis3_decision.py`
  - `tests/measure/test_xbrl_branch_a.py`
  - `tests/measure/test_xbrl_cd_seal.py`
  - `tests/measure/test_xbrl_customer_report_fix_result.py`
  - `tests/measure/test_xbrl_customer_report_fix_seal.py`
  - `tests/measure/test_xbrl_customer_report_result.py`
  - `tests/measure/test_xbrl_customer_report_seal.py`
  - `tests/measure/test_xbrl_default_p26_result.py`
  - `tests/measure/test_xbrl_default_p26_seal.py`
  - `tests/measure/test_xbrl_fresh_result.py`
  - `tests/measure/test_xbrl_lastbranch_result.py`
  - `tests/measure/test_xbrl_lastbranch_seal.py`
  - `tests/measure/test_xbrl_p20_result.py`
  - `tests/measure/test_xbrl_p26_result.py`
  - `tests/measure/test_xbrl_p26_seal.py`
  - `tests/measure/test_xbrl_p27_seal.py`
  - `tests/measure/test_xbrl_period_bind_result.py`
  - `tests/measure/test_xbrl_period_bind_seal.py`
  - `tests/measure/test_xbrl_pnf_diag.py`
  - `tests/measure/test_xbrl_point_prior_result.py`
  - `tests/measure/test_xbrl_ritual_result.py`
  - `tests/measure/test_xbrl_rounding_result.py`
  - `tests/measure/test_xbrl_rounding_seal.py`
  - `tests/measure/test_xbrl_vocab_result.py`
  - `tests/measure/test_xbrl_vocab_seal.py`

**(a′) `adapters/xbrl/verify_document.py` の sha16 `67e7639de3f5f2ad` を字で留める門 14 本**(`git grep -l -F 67e7639de3f5f2ad aeae608 -- tests` で数えた全部。どれも `tests/measure`。`verify_document.py` は `d27a390`(2026-10-14)から動いていない)と measure 1 本。docstring の 1 行で sha16 が動くので、14 本それぞれに宣言された遷移を足す(`UNTOUCHED` の表に在る file は、`verify_document.py` だけを「封が履歴に在り、値が段 2 の後の値のときだけ受け入れる」行へ移す。測った当時の値は残す)。(a) と重なるのは 12 本、重ならないのは `test_xbrl_role_swap_result.py`・`test_xbrl_verify_inventory.py` の 2 本:

  - `tests/measure/test_xbrl_a_core_vs_grep_seal.py`
  - `tests/measure/test_xbrl_axis3_decision.py`
  - `tests/measure/test_xbrl_branch_a.py`
  - `tests/measure/test_xbrl_cd_seal.py`
  - `tests/measure/test_xbrl_customer_report_fix_result.py`
  - `tests/measure/test_xbrl_customer_report_fix_seal.py`
  - `tests/measure/test_xbrl_customer_report_result.py`
  - `tests/measure/test_xbrl_customer_report_seal.py`
  - `tests/measure/test_xbrl_default_p26_seal.py`
  - `tests/measure/test_xbrl_p20_result.py`
  - `tests/measure/test_xbrl_p26_seal.py`
  - `tests/measure/test_xbrl_pnf_diag.py`
  - `tests/measure/test_xbrl_role_swap_result.py`
  - `tests/measure/test_xbrl_verify_inventory.py`

  measure: `measure/xbrl_customer_report_fix_2026-10-21.py` の `UNTOUCHED_SHA16`(記録を再現する script の中の留め。重い走らせ直し `AUDIT_CORE_CUSTOMER_REPORT_FIX` が読む)。記録 `fixtures/xbrl/customer_report_2026-10-21.json`・`customer_report_fix_2026-10-21.json`・`naming_fix/p21_2026-10-20.json`・`p27/regress97_2026-10-27.json` の中の同じ字は**残す**(記録は直さない)。`test_xbrl_default_p26_seal.py` の test_7(docstring が「= P20」のままであることを実物の字で見る)は、直った後は「別便で人間が直した」として赤になる門なので、この封の遷移(docstring の後の字・sha16)を宣言して緑にする(前提が変わったことを門の字で残す)。

**(b) 束ねた指紋 `adapter_xbrl_py_sha256` の `0e51211a8aed2151…` を字で留める門 6 本**(`git grep -l -F 0e51211a8aed2151 aeae608 -- tests`)。(a) と重なる(段 2 の遷移を同じ便で宣言する)。記録 4 つ・結果文書 1 つの同じ字は残す:

  - `tests/measure/test_xbrl_customer_report_fix_result.py`
  - `tests/measure/test_xbrl_customer_report_fix_seal.py`
  - `tests/measure/test_xbrl_customer_report_result.py`
  - `tests/measure/test_xbrl_customer_report_seal.py`
  - `tests/measure/test_xbrl_default_p26_seal.py`
  - `tests/measure/test_xbrl_p26_seal.py`

**(c) frozen_bundle の世代 `29fd733c8988164a…` を字で留める所**(`git grep -l -F 29fd733c8988164a aeae608 -- .`): `fixtures/frozen_bundle_sha.py` の世代の一覧に新しい世代を足す(`FROZEN_COUNT` 37 のまま)。字で留める門は次の 4 本(どれも (a) と重なる):

  - `tests/measure/test_xbrl_customer_report_fix_seal.py`
  - `tests/measure/test_xbrl_customer_report_seal.py`
  - `tests/measure/test_xbrl_default_p26_seal.py`
  - `tests/measure/test_xbrl_p26_seal.py`

**(d) 既定の字だけで赤になる `tests/measure`**(sha16 の字でなく `"P26"` の既定を見る。試作の赤の内訳は S-8): `test_xbrl_naming_fix_result.py`(`DEFAULT_PROFILE == "P26"`・注記の字。注記は残し既定の字だけ P27 に)、`test_xbrl_period_bind_result.py`(vocabulary.py の字の検査 `found == ["P26"]`)、`test_xbrl_rounding_result.py`(同じ)、`test_xbrl_default_p26_result.py`(`engine_ok` の `DEFAULT_PROFILE == "P26"`)、`test_xbrl_default_p26_seal.py`(test_20 の `DEFAULT_PROFILE == "P26"`)、`test_xbrl_p27_result.py`(test_65 の `DEFAULT_PROFILE == "P26"`)、`test_xbrl_p27_seal.py`(test_6 の `DEFAULT_PROFILE = "P26"` の行が 1 つ)。どれも「測った当時の既定」の字は残し、「いまの既定」の字を P27 にする(この封を根拠に)。

**(e) 既定の字を見る `tests/adapters/xbrl` 11 file**(`git grep -l DEFAULT_PROFILE aeae608 -- tests/adapters/xbrl` で数えた全部。試作で赤になった本数は S-8):

  - `tests/adapters/xbrl/test_p17.py`
  - `tests/adapters/xbrl/test_p20.py`
  - `tests/adapters/xbrl/test_recipes_p21.py`
  - `tests/adapters/xbrl/test_recipes_p22.py`
  - `tests/adapters/xbrl/test_recipes_p23.py`
  - `tests/adapters/xbrl/test_recipes_p24.py`
  - `tests/adapters/xbrl/test_recipes_p25.py`
  - `tests/adapters/xbrl/test_recipes_p26.py`
  - `tests/adapters/xbrl/test_recipes_p27.py`
  - `tests/adapters/xbrl/test_run.py`
  - `tests/adapters/xbrl/test_verify_entry.py`

`test_recipes_p27.py` の「既定は P26 のまま」「`PROFILES[DEFAULT_PROFILE] is P26`」は「既定は P27」「P27 の旗 4 つが真・B の旗は偽」に直す(P27・P27E を明示した試験の数は変えない)。`test_recipes_p23.py`〜`test_recipes_p26.py` の「既定は P26」の字は P27 に。`test_verify_entry.py` の既定の数(未使用 2 書類の旗・14 書類の止めた件数・保留の照合・出力の sha256)は、前例 `917157c`・`d0b544c` と同じく、P26 を明示した試験に名前を変えて数を 1 つも変えず残し、既定(P27)の試験を足す(P27 の数が P26 と同じでも、P27 を既定として測った字で留める)。

**(f) 重い走らせ直しだけで赤になる 7 本**(試作。環境変数つき。S-9 の一覧): `test_xbrl_customer_report_result.py` の `RerunTest.test_heavy_everything_matches_the_record`(`AUDIT_CORE_CUSTOMER_REPORT=1`)、`test_xbrl_customer_report_fix_result.py` の同名(`AUDIT_CORE_CUSTOMER_REPORT_FIX=1`)、`test_xbrl_default_p26_result.py` の同名(`AUDIT_CORE_DEFAULT_P26=1`)、`test_xbrl_fresh_result.py` の同名(`AUDIT_CORE_FRESH=1`)、`test_xbrl_period_bind_result.py` の `RerunTest.test_heavy_stage2_default_matches_the_record`(`AUDIT_CORE_PERIOD_BIND=1`)、`test_xbrl_ritual_result.py` の `RerunHeavyTest.test_4`・`test_6`(`AUDIT_CORE_RITUAL=1`)。直し方は、測った値の欄が 1 字も違わないことを確かめてから、engine の sha・既定の欄に宣言された遷移を足す(封 `docs/XBRL_HEAVY_RERUN_FIX_SEAL_2026-10-27.md` の型)。既定を前提に記録を再現する script(`xbrl_default_p26_2026-10-23.py`)は、測った当時の既定 P26 を明示して固定する(前例 `PROFILE_AT_MEASURE`。記録 `default_p26_2026-10-23.json` は 1 字も直さない)。

**(g) 軽い門で赤になる「既定を前提に走らせ直す」所**(試作。S-8 の種類 (3) の 9 本): `test_xbrl_default_p26_result.py` の `RerunTest.test_light_two_documents_match_the_record`(script が「既定が P26 でない」で止まる)、`test_xbrl_period_bind_result.py` の `RerunTest.test_light_stage2_the_comparator_sees_a_wrong_default`(対照の既定の字)、`test_xbrl_ritual_result.py` の `LabelTest.test_13`・`test_14`・`test_17`(guard が P26 でないと rc 1 で止まる)と `PredictionTest.test_8`、`test_xbrl_point_prior_result.py` の `test_3`・`test_6`・`test_m0`(B-5 の判定を作業木の `git diff` で数える)。直し方は測定側を測った当時の profile に固定するか、engine の留めを sha16 の遷移に移す。`xbrl_default_p26_2026-10-23.py` を P26 の明示に固定したら、その字を見る `test_xbrl_default_p26_result.py` の `test_light_the_script_stops_when_the_default_is_not_p26` も同じ便で直す(記録 `default_p26_2026-10-23.json` の `環境/DEFAULT_PROFILE` の欄 P26 は測った当時の値として残し、走らせ直しは P26 を明示した出力と比べる ― 前例: 期の縛りの段 2 の `stage2_default`)。儀式の guard は P27 に(記録を採り直す = S-4)。`test_xbrl_ritual_result.py` の README の節の字(P26 の行)は P27 の記録から作る形に直し、P26 のときの数の 1 行を足す(P22・P21 の行は残す)。

**(h) 新しい門の名前**: 新しい門(封の門・結果の門)で engine の留めを定義するときは、`ENGINE_LATER`・`UNTOUCHED`・`PIN_DEF`・`LATER_ENGINE_COMMITS`・`FROZEN_LATER`・`ENGINE_TRANSITIONS`・`LATER_FINGERPRINT`・`FINGERPRINT_`・`LATER_TARGET`・`LATER_FROZEN`・`FROZEN_BUNDLE_AT_SEAL`・`TARGET_AT_SEAL`・`ENGINE_AT_SEAL` を行頭で定義しない(P27 の封の門 test_11 の `RESERVED_PREFIXES`、P25 の封の門 test_10、P26 の封の門 test_16 が行頭の名前を数える)。新しい門は P26 の段 2 の封の時点の sha16 `83025e9c0525d08b` の字を持たない(`test_xbrl_default_p26_seal.py` の test_17 が作業木でその字を持つ file を数える)。

**(i) axis3** の `LATER_ENGINE_COMMITS` に段 2 の commit を宣言するのは次の便(この commit の直後は `test_xbrl_axis3_decision.py` の test_9 が赤。前例 `917157c` → `afd2d15`、`b2c3f56` → `76d557f` と同じ)。

**(j) P27 の段 2 の門 5 本**(監査の所見: `test_xbrl_p27_result.py` の test_61「engine が E から動いていない」と test_65「既定が P26」が赤になる): test_61 は「E から HEAD まで engine の diff が 0」と「作業木の指紋が E の指紋」を見るので、既定の切り替え(この封)を宣言された遷移として受け入れる形に直す(E の指紋・記録の指紋の字は残す。受け入れるのは、この封が履歴に在り、作業木の指紋が段 2 の後の値で、E から動いた file が `vocabulary.py`・`verify_document.py` の 2 つだけのとき)。test_65 は「既定は P27」に(P26 の字は測った当時の値として注記に残す)。`test_xbrl_p27_seal.py` の test_6(`DEFAULT_PROFILE = "P26"` の行が 1 つ)・test_8(`verify_document.py` が封の commit と byte 一致)・test_9(sha16 が封の時点の値か `P27_AFTER16`)は同じ形で遷移を足す。`test_xbrl_p27_engine_result.py`・`test_xbrl_p27_eval.py`・`test_xbrl_p27_order.py` の赤は試作で数えた(S-8)。順序の門は R より後に P27 の封を変えた commit の削除の行が 0 であることを見るので、P27 の封には日付つきの追記以外を足さない。

## §5 触る file と順序

段 2: `adapters/xbrl/vocabulary.py`(`DEFAULT_PROFILE` の 1 行と注記)・`adapters/xbrl/verify_document.py`(docstring の 1 行)→ 既定の字を見る試験と pin の遷移(§4 (a)〜(e)・(j))→ 儀式 `measure/ritual_2026-10-20.py` の guard・記録 `fixtures/xbrl/ritual_2026-10-20.json`(P27 で採り直す)・写し `fixtures/xbrl/ritual_2026-10-20_p26.json`・`README.md`・`README.en.md`・`docs/XBRL_RITUAL_RESULT_2026-10-20.md`(追記)→ `measure/xbrl_default_p26_2026-10-23.py`(測った当時の P26 に固定)→ `measure/xbrl_default_p27_2026-10-28.py` → `fixtures/xbrl/default_p27_2026-10-28.json` → `docs/XBRL_DEFAULT_P27_RESULT_2026-10-28.md` → `tests/measure/test_xbrl_default_p27_seal.py`(封の門)・`tests/measure/test_xbrl_default_p27_result.py`(結果の門)→ `tests/measure/test_xbrl_fresh_seal.py` の `LATER_NAMING_FILES`(docID を名指す新しい記録・script・門。前例 `917157c` の 3 file と同じ型)→ 覆い(`measure/suite_coverage_2026-10-16.py --write`・`docs/SUITE_COVERAGE_2026-10-16.md` §2-1・`README.en.md`・`docs/FACTS_FOR_BUYERS_2026-10-20.md` §6 の A-06〜A-09)→ pin の遷移の宣言(`fixtures/frozen_bundle_sha.py` の新しい世代)。

順序: 人間の言葉(2026-10-27・2026-10-28)→ 評価用の結果の commit(`aeae608` = R)→ **この封を commit(文書だけ。封の門は実装の便)** → 段 2 実装(別席。`measure/` と試験と記録と文書)→ 凍結(sha256 の一覧)→ 独立監査(`step-auditor`)GO → commit → axis3 の `LATER_ENGINE_COMMITS` に段 2 の commit を宣言(次の便)→ `../docs/DECISION_LOG.md` の D-024・D-025(文書だけ。別の便)。各便の commit はパス指定。主の木を赤くしうる実測は worktree で。

- 試作の clone の cache の件数(走らせる前 → 後): `~/.cache/audit-core/edinet/` **281 → 281**・`edinet-fresh-2026-10-21/` **40 → 40**(試作の script の記録 `probe_default_p27.json` の `cache の件数`)。評価用・調整用の AI の文・DB の応答は開いていない(試作の script は `edinetdb-p27/` の下を読まない。会話の記録でも開いていない)。
