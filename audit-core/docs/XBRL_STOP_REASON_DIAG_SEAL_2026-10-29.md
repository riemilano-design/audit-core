# 封: 注入 741 行で「道具が止めた理由」と「名指し」を分類し、P27E を同じ 741 行で測る診断 ― 2026-10-29

**人間(2026-10-29)「阻止理由(判定ログ)の精査 ― 止めた際、Audit Core が『どの要素名・どの理由で止めたのか』のログを分類し、P27E の『名指し返却』を支えるエビデンスとして整理しておくこと。君に任せる」。** 前の便(封 `docs/XBRL_INJECT_REACH_DIAG_SEAL_2026-10-28.md` = `df5c215`、診断 `docs/XBRL_INJECT_REACH_DIAG_2026-10-28.md`・記録 `fixtures/xbrl/inject_reach_2026-10-28.json`・script `measure/xbrl_inject_reach_2026-10-28.py`・門 `tests/measure/test_xbrl_inject_reach.py` = `a7ceb29`)の封 §4 の 3 が「どの枝で止めたか(reason)の意味はこの便では読まない」と残した便。加えて、**P27E(外部の数の文のための profile。既定にしない)を、同じ 741 行で初めて測る**(前の便は P22・P26・P27 だけ)。
**診断だけ。engine(`core/`・`adapters/`)は 0 行。既存の記録(`fresh_2026-10-21.json`・`inject_reach_2026-10-28.json`・`p27/regress97_2026-10-27.json`)は書き換えない(別の記録を足す)。直すなら別の封。** 0 USD・通信なし・席(LLM)は呼ばない。
作法は変えない(封 → 測定 → 凍結 → 独立監査 GO → commit)。数を見てから封・予測を直さない。外れは外れとして残す(補足は日付つきの追記)。

- 封の時点: branch `feature/audit-core-final-eval-8`、HEAD `cb4283d`、`vocabulary.DEFAULT_PROFILE = "P27"`(`6a34db5`)。
- この封は docID・claim の id・タクソノミのラベル(日本語名)を書かない。書類と行は**位置か集計**で呼ぶ(引きの門 `tests/measure/test_xbrl_fresh_seal.py` は `LATER_NAMING_FILES` の外の追跡 file に新しい標本の docID が出ると赤になる)。要素名(`接頭辞:名前`)は書いてよいが、**提出者別の接頭辞の要素名は書かない**(§2-5。接頭辞に提出者の符号が入るため)。
- 前例の型: 前の便(封 §2 の配線の門・§2-3 の機械の分類・§3 の欄ごとの予測・§6 の下調べ)と、`measure/xbrl_p27_tune_2026-10-27.py` の `named_original`(名指しの定義)。

## §0 根拠(この封は新しく測らない。数は記録と、それを縛った文書から引く)

### §0-1 問い

1. 注入の 741 行(T1_VALUE 195・T2_UNIT 263・T5_COINCIDENT 103・T3_ABSENT 180)で、注入後の claim を、engine はどの理由(state と reason の組)で止めたか。profile ごと(P22・P26・P27・P27E)・型別に。T3 は基準の claim が無いので分けて書く。
2. そのうち**名指した**行は何行か。名指し = 注入後の claim の state が VALUE_MISMATCH で、pointers が空でなく、pointers の先頭が、**同じ profile の無改変の基準の claim の pointers の先頭と同じ**(原本の fact を名指して「違う」と言った)。前例の `named_original` は `recomputed` の一致も見るが、記録 `inject_reach_2026-10-28.json` には `recomputed` が無い。だから 4 profile を走らせ直して `recomputed` も採り、**名指し(pointers)と名指し(pointers + recomputed)の 2 本**を書く。名指したが先頭が違う行(別の fact)も数える。
3. 名指した pointer の**要素名**の分布(上位の要素名・接頭辞・context の種類)。
4. P27E を 741 行で測ると、通した・名指した・名指さずに止めた・理由の分布はどうなるか。
5. 名指しの率を P22・P26・P27・P27E で並べる。分母は「止めた」行と「届いた(文)の行(T1・T2・T5)」の 2 本。評価用 10 社の T8_REL・T1_VALUE の名指しの率とは**材料も型も違う**ので、並べるときは別の表にし、同じ表に入れない。

### §0-2 記録の数(封を書く席が、既に門が縛った文書から引いた。新しく集計していない)

前の便の封 §0-2(記録 `fresh_2026-10-21.json` から、P22 と P26 の型別の `結果`):

> T1_VALUE 195 | VALUE_MISMATCH 194・POINTER_NOT_FOUND 1 | VALUE_MISMATCH 192・POINTER_NOT_FOUND 3(うち no_same_value 2)

> T2_UNIT 263 | VALUE_MISMATCH 200・POINTER_NOT_FOUND 55(no_element 38・point without prior phrase 15・no prior2 2)・GROUNDED 5・対応が付かない 3 | VALUE_MISMATCH 171・POINTER_NOT_FOUND 84(no_element 41・no_same_value 32・point without prior phrase 9・no prior2 2)・GROUNDED 5・対応が付かない 3

> T5_COINCIDENT 103 | VALUE_MISMATCH 103 | POINTER_NOT_FOUND(no_same_value)92・VALUE_MISMATCH 11

> T3_ABSENT 180 | POINTER_NOT_FOUND(no_element)69・UNVERIFIABLE(no_subject 59・ambiguous(elements) 21)・VALUE_MISMATCH 30・対応が付かない 1 | POINTER_NOT_FOUND 100(no_element 70・no_same_value 30)・UNVERIFIABLE 79(no_subject 59・ambiguous 20)・対応が付かない 1

前の便の診断の文書 §4(表 `stops`。記録 `inject_reach_2026-10-28.json` から門が作り直す表):

> P22 計: 届いた・違う 497・届いた・要確認 56・届かない・通した 5。P26 計: 374・179・5。P27 計: 374・179・5(T1・T2・T5)。

> P27 T1: 192・3、T2: 171・84・通した 5、T5: 11・92(届いた・違う・届いた・要確認)

同 表 `t3`: P22 は届いた 179(違う 30・要確認 149)・対応が付かない 1、P26・P27 は届いた 179(違う 0・要確認 179)・対応が付かない 1。同 表 `reread` の全 741 行: P22 は通した 5・止めのうち違う 527 / 732、P26・P27 は 5・374 / 732、対応が付かない 4。

記録 `p27/regress97_2026-10-27.json` の `集計 > 新しい標本 30`(無改変の 30 書類。台帳 L-35・D-24 の出どころ):

> claims 3923。4 state: P22 GROUNDED 2142・VALUE_MISMATCH 677・UNVERIFIABLE 690・POINTER_NOT_FOUND 414、P26 2194・250・774・705、P27 2194・250・787・692、P27E 2194・274・787・668。

> P27 → P27E: 動いた行 24、VALUE_MISMATCH に入る行(no_same_value → VALUE_MISMATCH)24、他の向きの行 0、GROUNDED が P27 と違う行 0。規則ごとに当たった claim の数 P27E の B relative_within_rho 24。

同 `動いた行 > 新しい標本 30 > P27 → P27E` は 24 行で、行ごとに docID・claim の id・前(state・reason)・後(state・reason)を持つ。書類ごとの 4 state は `書類`(97 件)の各行に在る。

台帳 `docs/FACTS_FOR_BUYERS_2026-10-20.md` L-34(評価用 10 社。材料も型も違う):

> P26 の T8_REL: 名指して原本の値を返した行 36 / 87 = 41.4%; P27 の T8_REL: 名指して原本の値を返した行 27 / 87 = 31.0%; P26 の T1_VALUE: 名指して原本の値を返した行 7 / 7 = 100.0%; P27 の T1_VALUE: 名指して原本の値を返した行 5 / 7 = 71.4%

結果文書 `docs/XBRL_P27_RESULT_2026-10-27.md` の P27E(同じ評価用 10 社):

> T8_REL | P27E | 全体 | 87 | 0 | 78 | 7 | 2 | 0 | 89.7% | 0.0%

> T1_VALUE | P27E | 全体 | 7 | 0 | 5 | 0 | 2 | 0 | 71.4% | 0.0%

### §0-3 engine が出しうる state と reason の字(封を書く前に `core/` と `adapters/xbrl/` を読んで列挙した)

出力の claim の `state`・`reason`・`pointers`・`recomputed` は `adapters/xbrl/verify_document.py` の `verify_document` が `core.verify_all` の `Result` から写す(`CLAIM_FIELDS` に `recomputed` が在る)。`core/py/audit_core/verify.py` の `verify` は次の 4 通りでしか `Result` を作らない:

- recipe に `unverifiable_reason` がある → UNVERIFIABLE、reason = その字(登録簿で UNVERIFIABLE の字でなければ engine が例外)、`recomputed` = None。
- recipe に `not_found_reason` がある → POINTER_NOT_FOUND、reason = その字、`recomputed` = None。
- evidence の pointer が解けない → POINTER_NOT_FOUND、reason = `unresolved:` + pointer の字。evidence が 0 本 → POINTER_NOT_FOUND、reason = `no_pointer`。
- 比較した → GROUNDED か VALUE_MISMATCH。**reason は必ず None**(recipes の原本形式の claim が持つ `value differs(segment/other period?)` は Result に写らない)。`recomputed` は比較器が fact から求めた値(`comparators.py`: equals_within は fact の生の値、ratio・pct・diff は fact から計算した値)。

登録簿 `adapters/xbrl/registry_setup.py` の reason(全部):

- POINTER_NOT_FOUND 10: `no_element`・`no_element(unit not in XBRL)`・`no_element(ratio without fact)`・`no_prior_member_context`・`no_element(point without prior phrase)`・`no_element(text needs money fact)`・`no_element(no prior for text)`・`no_element(no prior2 for prior-year diff)`・`no_same_value`(P25 以降。最後の枝で証拠が無く名指さなかった数)・`other_concept`(P26 G1。当てた fact が文の項目と別の概念)。
- UNVERIFIABLE 10: `no_subject`・`ambiguous(member)`・`ambiguous(elements)`・`state_word(no line)`・`prior is 0`・`target_or_plan`・`other_frame`(P24。原本形式の `other_frame(<context>)` は `claim_to_recipe` が `other_frame` に替える)・`direction_on_cause_item`(P26 G4)・`rounded_diff_within_double_band`(P26 G3)・`per_unit_counter`(P27 C2)。
- core が自分で作る POINTER_NOT_FOUND 2: `no_pointer`・`unresolved:<pointer>`。

P27E は `vocabulary.py` で `P27E = dataclasses.replace(P27, name="P27E", last_branch_relative_2026_10_27=True)`。`recipes.py` の最後の枝で、B(`_last_branch_decide_2026_10_27`)は P26 G2・P25 の行より前に走り、証拠が無く、名指す値が 0 でなく、`||名指す値| − |文の値|| <= LAST_BRANCH_REL_RHO × |名指す値|`(`LAST_BRANCH_REL_RHO = 0.15`)なら `cur[0]`(その主語の当期の fact)を名指して VALUE_MISMATCH にし、そうでなければ G2 と同じ `no_same_value` にする。**B は GROUNDED を作らない。**

pointer の字の形(記録 `inject_reach_2026-10-28.json` の T1_VALUE の 1 行目の、P22 の無改変の基準の claim の `pointers` の実物の 1 行):

> xbrl:jppfs_cor:IncreaseDecreaseInAdvancesReceivedOpeCF@CurrentYearDuration

形は `<scheme>:<locator>`(`core.Pointer.parse` は最初の `:` で切る)。scheme が `xbrl` のとき locator は `<接頭辞>:<名前>@<context>`(`recipes._ctx_of` は `xbrl:` の後ろを `@` で 2 つに切る)。derived の claim は `formula:...` の pointer を後ろに持ち、text の claim は `builtin:...` を持ちうる。context の member は `recipes._member_of_ctx` と同じく、最初の `_` の後ろに `Member` を含むとき在る。

### §0-4 封を書く前に見たもの(予測の偏りの出どころ)

- 前の便の封・診断の文書・script・門の全文。`measure/xbrl_p27_tune_2026-10-27.py` の `named_original`・`classify`・`safe_reason`・`SAFE_REASON`・`SAFE_POINTER`・ラベル 6 語。
- engine: `core/py/audit_core/verify.py`・`registry.py`(全文)、`adapters/xbrl/registry_setup.py`(全文)、`verify_document.py` の `CLAIM_FIELDS`・`verify_document`、`recipes.py` の `UNBOUND_REASON_STATE`・`_state_of`・`claim_to_recipe` の reason の写し方・`reason` を書く行の grep・最後の枝(F3b・B・G2・P25 の順の 30 行ほど)・`_last_branch_decide_2026_10_27`、`comparators.py` の `recomputed` の行。`vocabulary.py` の P27E の 3 行。
- 注入: `measure/inject.py` の `build_t1`(差し替えは元の値 ± 小さい数)・`build_t3`(37 から 7 刻みの、参照の数に無い値)・`build_t5`(別の fact の値。`lib/sites.py` の `MAGNITUDE_RATIO = 10.0` で大きさを揃えた候補)。
- 記録: `inject_reach_2026-10-28.json` は**欄の名前と、T1_VALUE の 1 行目の P22 の基準の claim の `pointers`・`kind`・`form` だけ**を見た(§0-3 の実物の 1 行)。`regress97_2026-10-27.json` は `集計 > 新しい標本 30` の全部と、`動いた行 > 新しい標本 30 > P27 → P27E` の行数・欄の名前・1 行目の前と後の state・reason、`書類` の 1 行目(手元の 67 の書類)の欄の名前を見た。
- **見ていないもの**: `inject_reach` の P27 の reason の分布、741 行の注入後の pointers の先頭と基準の pointers の先頭の一致、`recomputed`、要素名・context の分布、P27E の注入後の全部。P22・P26 の reason の分布は §0-2 の引用(前の便の封の字)だけを知っていて、`inject_reach` の記録から集計していない。**`inject_reach` の reason の分布の集計は、§3 を固定した後に §6 で行う**(時刻を mtime で残す)。

## §1 既存の記録に無い欄(先に確かめた)

1. **`recomputed`**: 前の便の script の `CLAIM_KEYS` は `id`・`kind`・`form`・`value`・`unit`・`span`・`state`・`reason`・`pointers` の 9 つで、`recomputed` を記録に写していない。`fresh_2026-10-21.json` の `結果` は state と reason だけ。
2. **P27E の全欄**: 741 行の注入後も、無改変の基準も、P27E では測っていない(`regress97` は無改変の 30 書類の claim だけ)。
3. **要素名の分け方**: pointers は字のまま在るが、先頭の pointer を接頭辞・名前・context(期と member の有無)に切った欄が無い。
4. **名指しの旗**: 「先頭が基準の先頭と同じか」「recomputed が基準と同じか」の欄が無い。分類の語(§2-3)も無い。

だから、診断用の記録を 1 本足す。engine には触らない。既存の記録は書き換えない。

## §2 測り方(script `measure/xbrl_stop_reason_2026-10-29.py` の仕様)

### §2-1 配線(前の便の script を import し、観測する profile を 4 つにする)

- script は前の便の script を `_mod("measure/xbrl_inject_reach_2026-10-28.py", ...)` で読み込み(以下 RE)、その module の値を 3 つだけ替えてから、`RE.work_doc`(`observe_main`・`observe_t3`・`base_match_typed`・`classify_row`・`detail_of` を中で使う)を書類ごとに呼ぶ:
  - `RE.OBS = ("P22", "P26", "P27", "P27E")`
  - `RE.ALLP = tuple(sorted(set(RE.PROFILES5) | set(RE.OBS)))`(P22〜P27 と P27E の 7 つ。注入後は 7 つとも `verify_raw` で走る)
  - `RE.CLAIM_KEYS = RE.CLAIM_KEYS + ("recomputed",)`(`view` が `recomputed` も写す)
  前の便の script の file は触らない。**自分で注入の規則・対応付けを書かない**(注入・材料・`_find_base_claim`・`claim_for` は前の便と同じく `xbrl_fresh_2026-10-21.py` から、RE の中で使われる)。
- 書類・材料・cache は前の便と同じ(取得の記録の「使う」30 件、生 ZIP は `~/.cache/audit-core/edinet-fresh-2026-10-21/`(40)から読み sha256 を照らす、`~/.cache/audit-core/edinet/`(281)は読まず書かない、`edinetdb-p27/` は開かない。件数は開始時と終了時に数えて記録に書く)。書類ごとに別の process(fork の pool。`--procs`)。出力が既に在れば測り直さない。`--docs` で先頭の n 書類だけの試し(scratchpad の出力へ。正本の記録は 30 書類)。
- 無改変の 4 state: 書類ごとに、同じ process の中で `VD.verify_document(zb, p, None)` を P22・P26・P27・P27E で呼び、claim ごとの `id`・`state`・`reason` を取る(`RE.work_doc` の無改変の一覧とは別の呼び出し。engine は同じ入力に同じ出力を返す)。

**配線の門(1 つでも違えば記録を書かずに止める)**:

- **W-1(前の便と同じ観測か)**: (i) `RE.work_doc` が返す配線の旗で、前の便の門と同じく 741 / 741 の 4 欄(`元の字`・`後の字`・`基準の claim`・`結果` P22〜P26)一致・id の集合が同じ・`注入の件数` 120 組の一致。(ii) 741 行の P22・P26・P27 の欄が、記録 `inject_reach_2026-10-28.json` の同じ id の行の同じ profile の欄と一致すること: 注入後の claim の state・reason・pointers と分類(6 語)は**欄ごとに** 741 / 741、さらに profile の欄の全部(`recomputed` の鍵を除いて、`json.dumps(..., sort_keys=True, ensure_ascii=False)` の字で)741 / 741。
- **W-2(P27E の無改変が台帳 L-35 の記録と同じか)**: 30 書類の無改変の 4 state の数が、`regress97` の `書類` の同じ docID の行の `4 state`(P22・P26・P27・P27E)と 30 書類 × 4 profile で一致。P27 と P27E で state か reason が違う claim の (docID, claim の id) の集合が、`regress97` の `動いた行 > 新しい標本 30 > P27 → P27E` の 24 行の集合と同じで、24 行とも前 = POINTER_NOT_FOUND・`no_same_value`、後 = VALUE_MISMATCH・None であること(= L-35 の 24)。
- **W-3(module の値の差し替えが届いたか)**: 741 行の全部で `profile` の鍵の並びが `["P22", "P26", "P27", "P27E"]`、`結果(P22〜P27)` の鍵に P27E が在り、claim の欄が None でない行の全部で `claim` に `recomputed` の鍵が在ること(差し替えが使う側に届かず黙って効かない形を、記録を書く前に止める)。

### §2-2 観測する欄(行ごと・profile ごと。全部 engine の出力から機械で取る)

`RE.work_doc` が返す行(前の便の欄の全部 + P27E + `recomputed`)に、script が次の欄を足す(同じ profile の欄の中に `名指し` として):

| 欄 | 出どころ |
|---|---|
| 注入後の claim の state・reason | RE の行の `注入後.claim`(T3 は `claim`) |
| 基準の claim(T1・T2・T5) | RE の行の `無改変.claim`(記録の P22 の基準の id を、その profile の無改変の一覧から id で引いた claim。前の便の封 §6-5) |
| 先頭が同じ | 注入後の pointers が空でなく、基準の pointers が空でなく、両方の先頭の字が同じ |
| recomputed が同じ | 先頭が同じ、かつ注入後の `recomputed` と基準の `recomputed` が `==` で同じ(どちらも None なら同じと数えない) |
| 分類(止めの語) | §2-3 の 13 語(機械で 1 か所) |
| 先頭の pointer の切り方 | scheme・接頭辞・名前・context・期・member の有無・標準の接頭辞か(§2-5) |
| 基準の claim の state がその profile で GROUNDED か | 基準の claim の state(前の便の 1 行(T2)が P26・P27 で GROUNDED でない。P27E も見る) |

書類ごと: 無改変の 4 state の数と、W-2 の行(P27 → P27E で動いた claim の id と前・後)。記録の全体: 材料の sha256(取得の記録と一致)、配線の門 W-1〜W-3 の数、engine の sha256 先頭 16 桁(前の便と同じ 6 本)、`DEFAULT_PROFILE`、HEAD、封の commit、cache の件数(開始時・終了時)、所要秒、読んだ入力の sha256(`fresh_2026-10-21.json`・`fetched_2026-10-21.json`・`inject_reach_2026-10-28.json`・`p27/regress97_2026-10-27.json`)、`key_leaks`。

記録に `recomputed` を持つ。値は有報の XBRL の fact の値(またはそれから計算した値)で、前の便の記録が既に持つ `value`・`span` と同じ種類の字である(前例 `p27/tune` の記録が `recomputed` を repo に入れなかったのは、文が外部 DB の応答の写しになるためで、この便の材料には当たらない)。

### §2-3 分類(止めの語。機械で 1 か所。§3 の予測はこの語で書く)

行ごと・profile ごとに、注入後の claim から次の順で 1 つに決める(先に当たったものを取る)。「基準」は §2-2 の基準の claim(T3 は無い)。

| # | 条件 | 語 |
|---|---|---|
| 1 | 注入後の claim が None | **(対応が付かない)** |
| 2 | state = GROUNDED | **(通した)** |
| 3 | state = VALUE_MISMATCH、pointers が空でない、T1・T2・T5、基準が在り基準の pointers が空でなく、先頭が同じ | **(名指した・原本)** |
| 4 | state = VALUE_MISMATCH、pointers が空でない、T1・T2・T5、3 に当たらない(先頭が違う・基準が無い・基準の pointers が空) | **(名指した・別の fact)** |
| 5 | state = VALUE_MISMATCH、pointers が空でない、T3_ABSENT | **(名指した・基準なし)** |
| 6 | state = POINTER_NOT_FOUND、reason = `no_same_value` | **(要確認・証拠が無く名指さない)** |
| 7 | state = POINTER_NOT_FOUND、reason = `other_concept` | **(要確認・別の概念)** |
| 8 | state = POINTER_NOT_FOUND、reason = `no_element` か `no_element(` で始まる字か `no_prior_member_context` | **(要確認・要素が無い)** |
| 9 | state = POINTER_NOT_FOUND、reason = `no_pointer` か `unresolved:` で始まる字 | **(要確認・pointer が引けない)** |
| 10 | state = UNVERIFIABLE、reason = `no_subject` | **(要確認・主語が無い)** |
| 11 | state = UNVERIFIABLE、reason が `ambiguous(` で始まる字 | **(要確認・候補が複数)** |
| 12 | state = UNVERIFIABLE、reason が `other_frame`・`rounded_diff_within_double_band`・`per_unit_counter`・`target_or_plan`・`state_word(no line)`・`direction_on_cause_item`・`prior is 0` のどれか | **(要確認・主張の形で保留)** |
| 13 | 上のどれにも当たらない(VALUE_MISMATCH で pointers が空、§0-3 に無い reason の字、POINTER_NOT_FOUND・UNVERIFIABLE で reason が None など) | **(形の外)** |

- 「止めた」= 語 3〜13(state が GROUNDED でなく、対応が付く)。`outcome_of` の「違う」= 語 3・4・5 と、13 のうち VALUE_MISMATCH。「要確認」= 語 6〜12 と、13 のうち POINTER_NOT_FOUND・UNVERIFIABLE。
- **名指し(pointers)** = 語 3。**名指し(pointers + recomputed)** = 語 3 のうち「recomputed が同じ」の行(細目。分類の順には入れない)。**名指したが別の fact** = 語 4。
- (形の外)は止めない(記録に残し、§3 の予測で 0 と見る)。§0-3 に無い reason の字が出たら、記録の `reason` の字の分布にそのまま出る。
- 語 6〜12 は engine の reason の字から決まり、reason の字そのものも記録と文書の表(§2-4 の `reasons`)に出す。語は字の束ね方で、**意味(なぜその枝に落ちたか)は診断の文書の仮説の節に書き、記録には書かない**。

### §2-4 集計の表(診断の文書の `<!-- 門:start 名前 -->` の中。門が記録から作り直す)

1. `pred`(先頭): §3 の予測の当否。
2. `wiring`: W-1(i)(ii)・W-2・W-3 の数。`engine`: sha16・DEFAULT_PROFILE・HEAD・封の commit・cache・key_leaks。
3. `reasons`: profile × 型 × (state, reason の字) の行数(741 行の全部。通した・対応が付かないを含む)。
4. `cls`: profile × 型(T1・T2・T5・計・T3)× 13 語の行数。
5. `named`: profile × 型(T1・T2・T5・計・T3)で、止めた・届いた(文)(T1・T2・T5 のみ)・名指した・原本・うち recomputed も同じ・名指した・別の fact・名指した・基準なし、名指しの率 2 本(分母 = 止めた、分母 = 届いた(文))を `n / d = x.x%` の字で。T3 の行は名指しの率を書かない(基準が無い)。
6. `p27e`: P27 → P27E で語が変わった行(型 × 前の語 × 後の語 × 行数)と、変わらなかった行数。
7. `elements`: 語 3 の行の先頭の pointer の要素名の上位 10(profile ごとに P22・P27・P27E。同数は要素名の字の順)。提出者別の接頭辞の要素は 1 行にまとめ「(提出者別の要素)」とする(§2-5)。`prefix`: 接頭辞の種類 × profile の行数。`context`: 期(CurrentYear・Prior1Year・Prior2Year × Duration・Instant・その他)× member の有無 × profile の行数。語 4 の行の先頭も同じ 3 表に別の列で数える。
8. `basestate`: 基準の claim がその profile の無改変で GROUNDED でない行(profile × 型)と、その行の語。
9. `eval`(別の表。材料も型も違う): 評価用 10 社の T8_REL・T1_VALUE の「名指して原本の値を返した」の率(P26・P27・P27E)を `fixtures/xbrl/p27/eval_inject_2026-10-27.json` の `集計(4 profile の全部で対応が付く行が分母。V-1〜V-3)` から門が読んで写す。この表は他の表と行を混ぜない。
10. `examples`: 語ごとに先頭 3 行まで(位置で呼ぶ。`書類 n・型の k 番目`、元の字 → 後の字、P27 と P27E の語)。

### §2-5 要素名の切り出し方

先頭の pointer の字 `p` について:

- `p` が `xbrl:` で始まらない → scheme の欄にその scheme、要素名は「(xbrl でない)」。
- `xbrl:` で始まる → `p[5:]` を最初の `@` で 2 つに切り、前を要素名、後ろを context とする。要素名を最初の `:` で切り、前を接頭辞、後ろを名前とする。
- 接頭辞が `jp[a-z]+_cor` の字(正規表現で全体一致)なら**標準の接頭辞**(例 `jppfs_cor`・`jpcrp_cor`・`jpigp_cor`)。それ以外は**提出者別の接頭辞**。提出者別の要素名・接頭辞の字は記録にだけ持ち、文書には書かない(「(提出者別の要素)」の 1 行に数だけ)。
- context の期: `^(CurrentYear|Prior1Year|Prior2Year)(Duration|Instant)` に当たればその 2 つの字、当たらなければ「その他」。member: context を最初の `_` で切った後ろに `Member` を含めば「member あり」、そうでなければ「なし」。context の字そのもの(member の字は提出者の符号を含みうる)は文書に書かない。
- 例(§0-3 の実物): 接頭辞 `jppfs_cor`・名前 `IncreaseDecreaseInAdvancesReceivedOpeCF`・期 `CurrentYear`・`Duration`・member なし・標準の接頭辞。

## §3 事前予測(欄ごと・外れうる形・外れ方つき。§6 の下調べより前に固定)

予測の土台(§0-4 の範囲で見たもの): T1 の差し替えは元の値 ± 小さい数で、主語と要素は変わらないので、engine は無改変で GROUNDED にした fact と同じ fact を名指して「違う」と言うと見る(無改変は一致の梯子で fact を選び、注入後は最後の枝が `cur[0]`(当期)を名指すので、無改変が当期でない fact で一致していた行だけ先頭が違うと見る)。T2 の単位の差し替えは値が 10 の冪で動き、G2 の証拠(iii)(桁・単位の取り違え)が効くので、P26・P27 でも名指す行が多いと見る。T5 は P22 では最後の枝が主語の fact を名指し(103 が全部 VALUE_MISMATCH)、P26・P27 は 92 が `no_same_value`。P27E の B は `||名指す値| − |文の値|| <= 0.15 × |名指す値|` のときだけ名指すので、T5 の差し替え(大きさを 10 倍以内に揃えた別の fact の値)のうち 15% 以内のものだけが名指しに移り、T2(10 の冪)と T3(37〜400 の小さい値)はほとんど移らないと見る。B は GROUNDED を作らないので、P27E の通した行は P27 と同じと見る。

| # | 欄 | 予測 | 外れ方 |
|---|---|---|---|
| **SR-1** | 配線の門 W-1(§2-1) | 前の便の門 **741 / 741**・`注入の件数` 120 組の一致、P22・P26・P27 の欄が `inject_reach` の記録と欄ごとも全欄でも **741 / 741** | 1 つでも違う(止める。観測を書かない) |
| **SR-2** | 配線の門 W-2(§2-1) | 無改変の 4 state が `regress97` と **30 / 30** 書類 × 4 profile で一致、P27 → P27E で動いた claim の集合が `regress97` の **24** 行と同じ | 1 つでも違う(止める) |
| **SR-3** | P27 の(名指した・原本)(型別) | T1 **170 以上 192 以下**・T2 **130 以上 171 以下**・T5 **0 以上 11 以下** | どれかが幅の外(下に外れたら、注入後の名指しが無改変と別の fact に向く行が見立てより多い) |
| **SR-4** | P27 の(名指した・別の fact)(T1・T2・T5 の計) | **0 以上 40 以下** | 41 以上 |
| **SR-5** | P22 の(名指した・原本)(T5)と、P22 − P27 の(名指した・原本)(T1・T2・T5 の計) | P22 の T5 **80 以上 103 以下**、差 **60 以上 160 以下**(P22 が多い) | どちらかが幅の外(差が負なら向きの外れ) |
| **SR-6** | 名指し(pointers) − 名指し(pointers + recomputed)(T1・T2・T5、4 profile それぞれ) | 4 つとも **0 以上 5 以下** | どれかが 6 以上 |
| **SR-7** | P27E の通した・対応が付かない(741 行) | 通した **5**(5 行とも P27 で通した行と同じ id)、対応が付かない **4** | 数が違う、または通した行の id が P27 と違う |
| **SR-8** | P27 → P27E で語が変わった行(741 行) | 計 **3 以上 35 以下**。型別に T5 **3 以上 25 以下**・T1 **0 以上 2 以下**・T2 **0 以上 3 以下**・T3 **0 以上 3 以下**。変わった行は全部、前が(要確認・証拠が無く名指さない)で、後が語 3・4・5 のどれか | どれかが幅の外、または前か後が別の語の行が 1 行でも在る |
| **SR-9** | P27E の(名指した・原本)と P27 の差、変わった行のうち(名指した・原本)の割合 | P27E が P27 より **1 以上 35 以下** 多い。変わった行(T1・T2・T5)のうち(名指した・原本)が **70% 以上** | 差が幅の外、または 70% 未満(変わった T1・T2・T5 の行が 0 なら割合は判定しない) |
| **SR-10** | P27E の「要確認」(語 6〜12 と 13 のうち POINTER_NOT_FOUND・UNVERIFIABLE、741 行) | **323 以上 355 以下** | 幅の外 |
| **SR-11** | P27 の(名指した・原本)の先頭の要素名の上位 1 つが占める割合 | **3% 以上 25% 以下** | 幅の外 |
| **SR-12** | P27 の(名指した・原本)の先頭の接頭辞 | 標準の接頭辞が **85% 以上**、`jppfs_cor` が **40% 以上 90% 以下** | どちらかが外れる |
| **SR-13** | P27 の(名指した・原本)の先頭の context | 期が CurrentYear(Duration・Instant)の行が **80% 以上**、member ありが **0% 以上 30% 以下** | どちらかが外れる |
| **SR-14** | P27 の T3_ABSENT 180 行の語 | (要確認・要素が無い)**60 以上 80 以下**・(要確認・証拠が無く名指さない)**20 以上 35 以下**・(要確認・主語が無い)**50 以上 65 以下**・(要確認・候補が複数)**15 以上 25 以下**。(対応が付かない)**1**、(通した)と(名指した・基準なし)は **0** | どれかが外れる |
| **SR-15** | (形の外)と(要確認・pointer が引けない)(741 行、4 profile) | 両方とも 4 profile で **0** | どれかで 1 以上 |
| **SR-16** | P22 の(要確認・証拠が無く名指さない)・(要確認・別の概念)(741 行)と、P22 の T3 の(名指した・基準なし) | 前の 2 つは **0**、T3 の(名指した・基準なし)は **30**(§0-2 の再現) | どれかが違う |
| **SR-17** | P26 と P27 で語が同じ行(T1・T2・T5 の 561 行) | **98% 以上** | 未満 |

- SR-3〜SR-5・SR-11〜SR-13 は engine の名指しへの予測。SR-7〜SR-10 は B の規則への予測。SR-16 と SR-14 の一部は §0-2 の記録の数の再現に近く、当たって当然の欄を含む(当たりの数を良さの証拠にしない)。
- SR-3 の下限は「無改変が当期の fact で一致した行がほとんど」という見立てに依る。SR-3 と SR-4 と SR-5 が同じ向き(名指しが別の fact に向く)に外れたら、見立ての偏りとして診断の文書に書く。
- SR-8・SR-9 は「B は主語の当期の fact を名指す」の見立てに依る。T5 の差し替えの値の分布は見ていない(15% 以内に入る割合は推測)。
- 予測を 0 と書いた欄(SR-15・SR-16)は「engine がその枝を持たない」の主張ではない。この 741 行の観測に限る。
- 各型の engine の直し方はこの封に書かない(診断だけ)。

## §4 言えないこと・限界(封の時点で分かっているもの)

1. **「名指した」は、注入後の claim の pointers の先頭が無改変の基準の先頭と同じ、という字の一致である。** その名指しが人の目に正しい(文の数が本当にその fact のことを言っている)かは測っていない。基準は「無改変の P22 で GROUNDED」の claim を各 profile の一覧から id で引いたもので、基準そのものの結び付きが正しいかも測っていない。
2. **P27E を有報の原文に当てる使い方は想定しない。** P27E は無改変の 30 書類で 24 行を VALUE_MISMATCH に入れる(L-35。偽の「違う」かは確かめていない)。この便で P27E を測るのは、外部の数の文のための名指しの規則が、注入の 741 行でどう働くかを見るためで、有報に P27E を勧める材料ではない。
3. **評価用 10 社の名指しの率(L-34・P27 の結果文書)とは別物。** 材料(評価用 10 社 vs 新しい標本 30 書類)も型(T8_REL・T1_VALUE vs T1・T2・T5・T3)も分母の作り方も違う。文書では別の表にし、差を「良くなった・悪くなった」と読まない。
4. **要素名の分布は、この 30 書類の文の書き方と `IJ.select` の site の取り方に依る。** 他の書類で同じ分布になるとは言えない。
5. 30 書類・741 行・1 書類あたり型ごとに 40 件までの `IJ.select` の順の観測である。通さなかった site に同じ形が無いとは言えない。Core 全体の振る舞いを断定しない。
6. 語 6〜12 は reason の字の束ね方で、どの枝のどの条件で落ちたか(recipes の中の行)は記録に無い。reason の字が同じでも、落ちた枝が違うことがある(`no_element` は recipes の複数の行が書く)。
7. 前の便と同じく、「届いた(文)」は engine の文の一覧の番号の一致で、claim が読む数そのものの一致ではない。
8. 仮説は測るまで断定しない。読みは無い(席は呼ばない。人の目も入らない)。観測は全部 engine の出力からの機械の値。
9. 所要時間は前の便(6 profile で 960 秒、`--procs 6`)から、注入後 7 profile と無改変の 4 回で 1,100〜1,300 秒前後の見込み。**時間は症状で、目標ではない**。途中で止まったら記録を書かない。

## §5 file と順序

1. **この封**(文書だけ)。本線へは `docs/XBRL_STOP_REASON_DIAG_SEAL_2026-10-29.md` として司令塔が写して commit する(scratchpad の file と byte 一致)。封の commit が script・記録・文書・門のどの commit よりも前であること(順序の門は commit の順で見る)。docID・claim の id・ラベルを含まない。
2. 診断の便(1 commit。独立監査 GO の後):
   - script `measure/xbrl_stop_reason_2026-10-29.py`(§2)。出力が既に在れば測り直さない。`--docs`・`--procs`・`--out` を持つ。分類(§2-3)と要素名の切り出し(§2-5)はそれぞれ 1 つの関数に置く。
   - 記録 `fixtures/xbrl/stop_reason_2026-10-29.json`(docID と claim の id を持つ。行は 1 行 1 件の compact JSON(前の便の `dump_record` と同じ形))。材料と読んだ入力の sha256(§2-2 の 4 つ)、配線の門 W-1〜W-3、engine の sha16 6 本、HEAD、封の commit、cache の前後、所要秒、`key_leaks`(`FR.key_leaks` を通す)。
   - 文書 `docs/XBRL_STOP_REASON_DIAG_2026-10-29.md`(前の便の節立て: 予測の当否(先頭)→ 既存の記録で足りなかった → 配線 → 観測(§2-4 の表。行ごとの表は書かない。位置で呼ぶ例は語ごとに 3 行まで)→ 判定 → 仮説 → 言えないこと → 次に測ること。表は `<!-- 門:start 名前 -->`〜`<!-- 門:end -->` の内側。門の外の散文は数を持たない(持つ行は【門なし】)。docID・claim の id・ラベル・提出者別の要素名・禁止語(前の便の門の `FORBIDDEN` の 5 語)・code fence を書かない)。
   - 門 `tests/measure/test_xbrl_stop_reason.py`: (a) 記録の 741 行の id が `fresh_2026-10-21.json` の `注入の行` の id と順も集合も同じ(字で留めない)、型別の数が同じ (b) 配線の門 W-1〜W-3 が記録の数で通っていて、P22・P26・P27 の欄を `inject_reach_2026-10-28.json` と門が自分で比べ直して 741 / 741、W-2 を `regress97` と門が自分で比べ直して 30 書類 × 4 profile と 24 行 (c) 文書の表を記録から作り直して 1 行も違わない(`eval` の表は `eval_inject_2026-10-27.json` から) (d) SR-1〜SR-17 の当否を記録から求め(幅は封の表の字から読む。字で留めない)、封の字(欄・予測・外れ方)と文書の当否の字が一致 (e) 分類(13 語)・名指しの 2 本・要素名の切り出しを、記録の欄から別の書き方で求め直して一致 (f) engine の sha16 を `ENGINE_AT_MEASURE`(字で留める)と `ENGINE_DECLARED`(宣言された遷移。今は空)で留める (g) 偽物で赤: 記録の写しの語・先頭の pointer・recomputed・配線の旗を 1 か所変えると (b)(c)(e) が赤、文書の表の 1 字で (c) が赤、封の予測の 1 字で (d)(c) が赤、文書に提出者別の接頭辞の字を 1 つ足すと (h) が赤 (h) 封と文書に 30 書類の docID・記録の claim の id・提出者別の接頭辞の字が無い (i) 封の commit が script・記録・文書・門の commit より前 (j) 記録が持つ読んだ入力 4 つの sha256 がいまの file と一致。
   - `tests/measure/test_xbrl_fresh_seal.py` の `LATER_NAMING_FILES` に記録・script・門の 3 つを足す(日付つきの注記。既存の並びは変えない)。
   - 覆い: `python3 measure/suite_coverage_2026-10-16.py --write` と `docs/SUITE_COVERAGE_2026-10-16.md` §2-1 の数。
3. 凍結(木の sha256 の一覧)→ 独立監査(`step-auditor`。配線の門を自分で走らせ直す(`--docs` で一部でもよいが、走らせた行は記録と byte 一致を見る)・分類と名指しを別実装で求め直す・変異 (g))→ GO → commit(パス指定)。監査中は木を触らない。
4. engine の直しはこの便に入れない。台帳 `FACTS_FOR_BUYERS` に行を足すかも別の便(診断の後、台帳の便で決める)。

## §6 下調べの観測(予測の後。scratchpad の clone。正本でない。0 USD)

§3 を書いて file を保存した後に(予測を固定 2026-10-29 11:18:22 JST。§0〜§5 の sha256 は `probe/mtime_seal_predictions.txt`、その時点の写しは `probe/seal_at_prediction.md`)、次の 2 つを行った。**§0〜§5 の字は変えていない**(この節の前までの字は、予測を固定した写しと byte 一致。`probe/seal_prefix_check.txt`)。

1. 記録 `inject_reach_2026-10-28.json`(clone の写し)の P22・P26・P27 の state・reason と名指し(pointers の先頭)の集計(`probe/scripts/agg_reach.py` → `probe/agg_reach_out.json`。11:18:48 JST。`probe/mtime_agg_reach.txt`)。
2. §2-1 の配線を先頭の 5 書類・4 profile で試した(clone `probe/clone`、HEAD `cb4283d`。`probe/clone/audit-core/measure/probe_stop_reason_2026-10-29.py` → `probe/probe5.json`・`probe/probe5_stdout.txt`・`probe/summary.txt`。11:22:01〜11:25:29 JST。`probe/mtime_probe_observed.txt`)。先に 1 書類で配線を見た(`probe/probe1.json`)。

ここの数は下調べの数で、正本は §5 の記録と門が出す。**SR-1〜SR-17 の当否は本番の記録から門が求める。** ここに書く見立ては、この時点のもので、本番で変わりうる。

### §6-1 配線・環境

- 下調べの script は、依頼文の「前の便の script の写しを作り `OBS` を 4 つにする」の代わりに、§2-1 のとおり前の便の script を import して `OBS`・`ALLP`・`CLAIM_KEYS` の 3 つを替える形で書いた(§2-1 の差し替えが使う側に届くかを、本番と同じ形で試すため)。clone の中の前の便の script は触っていない(clone の `git status` は下調べの script 1 つだけが未追跡)。下調べの script の sha256 は `fb7476c81aa7acb38bc335fe1f1079e3876869babc4b36d2ce603f61b2ca574b`。前の便の script との差分は無い(写していない)。足したのは、無改変の 4 state の `verify_document` の呼び出し、W-1〜W-3 の比べ方、§2-3 の 13 語の関数、§2-5 の切り出しの関数。
- W-1(5 書類): 前の便の 4 欄の一致 **131 / 131**、`注入の件数` 20 / 20 組。P22・P26・P27 の欄が `inject_reach` の記録と、state・reason・pointers・分類とも 131 / 131、`recomputed` を除いた全欄でも 131 / 131。
- W-2(5 書類): 無改変の 4 state が `regress97` と 5 / 5 書類 × 4 profile で一致。P27 → P27E で動いた claim は 4 で、`regress97` の 24 行のうちこの 5 書類の 4 行と、(docID, id, 前, 後)の集合で同じ。
- W-3: 131 行の全部で `profile` の鍵が 4 つの順、`結果(P22〜P27)` に P27E が在り、None でない claim の全部に `recomputed` の鍵が在った。
- cache: 開始 `edinet/` 281・`edinet-fresh-2026-10-21/` 40 → 終了 281・40(この封を書く前と、全部の後にも同じ数を数えた)。`/tmp` に file を足していない(TMPDIR と PYTHONPYCACHEPREFIX は probe の下)。`edinetdb-p27/` は開いていない。鍵の値は読んでいない。
- engine の sha16(clone): extract `3cf55966f12919f0`・vocabulary `514ebb8104451c07`・recipes `52d645e713c53c1c`・resolve `a41043763c1d4073`・comparators `d8706338325e725b`・verify_document `c3791080ab5aef2f`(前の便の記録と同じ 6 本)。
- 所要: 5 書類を 5 process で 207 秒(書類ごと 157・48・205・73・148 秒)。前の便の下調べ(6 profile、254 秒)と同じ程度。

### §6-2 記録 `inject_reach` の P22・P26・P27 の集計(予測の後。741 行の全部。記録は前の便のまま)

| profile | 型 | (state / reason)の行数 | 名指し(pointers の先頭が基準と同じ) | 先頭が違う |
|---|---|---|---|---|
| P22 | T1 | VALUE_MISMATCH 194・POINTER_NOT_FOUND / no_element(no prior2 for prior-year diff) 1 | 194 | 0 |
| P22 | T2 | VALUE_MISMATCH 200・no_element 38・no_element(point without prior phrase) 15・no_element(no prior2 for prior-year diff) 2・GROUNDED 5・対応が付かない 3 | 200 | 0 |
| P22 | T5 | VALUE_MISMATCH 103 | 103 | 0 |
| P22 | T3 | no_element 69・no_subject 59・ambiguous(elements) 21・VALUE_MISMATCH 30・対応が付かない 1 | 基準なし 30 | ― |
| P26 | T1 | VALUE_MISMATCH 192・no_same_value 2・no_element(no prior2 for prior-year diff) 1 | 192 | 0 |
| P26 | T2 | VALUE_MISMATCH 171・no_element 41・no_same_value 32・no_element(point without prior phrase) 9・no_element(no prior2 for prior-year diff) 2・GROUNDED 5・対応が付かない 3 | 170 | 1 |
| P26 | T5 | no_same_value 92・VALUE_MISMATCH 11 | 11 | 0 |
| P26 | T3 | no_element 70・no_same_value 30・no_subject 59・ambiguous(elements) 20・対応が付かない 1 | 0 | ― |
| P27 | T1〜T3 | P26 と同じ数(型ごとに同じ) | T1 192・T2 170・T5 11・T3 0 | T2 1 |

- VALUE_MISMATCH の行で pointers が空の行は 0。reason の字は全部 §0-3 の列挙の中に在った(`no_pointer`・`unresolved:` は 0)。
- P26・P27 の「先頭が違う」1 行(書類 9・T2 の 2 番目)は、基準が無改変で前期末の残高(context `Prior1YearInstant`、member あり)の fact と GROUNDED で、注入後は form が direct_value から derived_value(当期末と前期末の残高の差。最後の枝の F3b)に変わり、先頭が当期末の fact になった行である。
- この集計から、SR-3(T1 192・T2 170・T5 11)・SR-4(1)・SR-5(P22 の T5 103、差 497 − 373 = 124)・SR-14(no_element 70・no_same_value 30・no_subject 59・ambiguous(elements) 20・対応が付かない 1・通した 0・名指し 0)・SR-16(0・0・30)・SR-17 は、W-1 が通れば(P22・P26・P27 の欄が記録と同じなら)本番でもこの数になる見立てで、どれも幅の内に見える。**SR-3 の T5 は幅の上限ちょうど(11)、T1 も上限ちょうど(192)**。これは予測の後に見た数で、§3 は変えない。

### §6-3 下調べの観測(5 書類・131 行。4 profile。位置と集計だけ)

| profile | T1 27 | T2 55 | T5 19 | T3 30 |
|---|---|---|---|---|
| P22 | 名指した・原本 27 | 名指した・原本 32・要素が無い 20・対応が付かない 2・通した 1 | 名指した・原本 19 | 要素が無い 9・名指した・基準なし 5・主語が無い 11・候補が複数 5 |
| P26 | 名指した・原本 27 | 名指した・原本 28・要素が無い 19・証拠が無く名指さない 5・対応が付かない 2・通した 1 | 証拠が無く名指さない 18・名指した・原本 1 | 要素が無い 10・証拠が無く名指さない 5・主語が無い 11・候補が複数 4 |
| P27 | P26 と同じ | P26 と同じ | P26 と同じ | P26 と同じ |
| P27E | 名指した・原本 27 | P26 と同じ | 証拠が無く名指さない 17・名指した・原本 2 | P26 と同じ |

- 止めた 128(4 profile とも)。名指した・原本(T1・T2・T5): P22 78・P26 56・P27 56・P27E 57。うち recomputed も同じ: 76・55・55・56。届いた(文)100(4 profile とも)。(形の外)・(要確認・pointer が引けない)・(名指した・別の fact)は 0。
- P27 → P27E で語が変わった行は 1(T5。(要確認・証拠が無く名指さない)→(名指した・原本))。T3 の(要確認・証拠が無く名指さない)5 は P27E でも変わらなかった。
- P26 と P27 で語が同じ行 101 / 101。
- recomputed が基準と違う(先頭は同じ)行は、P22 で 2(T2: 千円 → 百万円、千円 → 兆円)、P27 で 1(T2: % → ポイント)。どれも単位の差し替えで、claim の比べ方(form か比較器)が変わった行に見える(form は下調べの記録に取っていない。§6-5)。
- 名指した・原本の先頭(P27、56 行): 接頭辞は `jppfs_cor` 52・`jpcrp_cor` 4(標準の接頭辞 56 / 56)。上位の要素名は `jppfs_cor:Liabilities` 5・`jppfs_cor:CashAndCashEquivalents` 4・`jppfs_cor:Assets` 4・`jppfs_cor:NoncurrentLiabilities` 4(上位 1 つ 5 / 56)。期は CurrentYearDuration 24・CurrentYearInstant 32(CurrentYear が 56 / 56)。member ありは 10 で、**10 とも `NonConsolidatedMember`(単体)**だった。

### §6-4 下調べの時点の当否の見立て(本番の門が 30 書類で求め直す)

| # | 見立て | 理由 |
|---|---|---|
| SR-1 | 当たりの側 | 131 / 131(全欄も) |
| SR-2 | 当たりの側 | 5 / 5 書類、動いた 4 が `regress97` と同じ |
| SR-3 | 当たりの側(T1・T5 は上限ちょうど) | §6-2 の記録の数 |
| SR-4 | 当たりの側 | 記録で 1 |
| SR-5 | 当たりの側 | 記録で T5 103、差 124 |
| SR-6 | **外れうる** | 5 書類で P22 の差が 2。30 書類で同じ割合なら 6 を超えうる(上に外れる) |
| SR-7 | 当たりの側 | 5 書類で P27E の通した 1・対応が付かない 2 は P27 と同じ行 |
| SR-8 | **下限が危うい** | 5 書類で変わった行 1(T5 の 18 行のうち 1)。同じ割合なら 30 書類で T5 5 前後で、下限 3 に近い |
| SR-9 | 当たりの側 | 差 1、変わった行は原本 1 / 1 |
| SR-10 | 当たりの側(変わった行が 3 未満なら上に外れる) | P27 の要確認 358 から変わった行を引いた数 |
| SR-11 | 当たりの側 | 5 / 56 = 8.9% |
| SR-12 | **上に外れうる** | 5 書類で `jppfs_cor` が 52 / 56 = 92.9%(上限 90% を超えている) |
| SR-13 | 当たりの側 | CurrentYear 100%、member あり 10 / 56 = 17.9% |
| SR-14 | 当たりの側 | §6-2 の記録の数 |
| SR-15 | 当たりの側 | 0 |
| SR-16 | 当たりの側 | §6-2 の記録の数 |
| SR-17 | 当たりの側 | 5 書類で 101 / 101、記録の型ごとの数も同じ |

見立ての向き: 名指しの数(SR-3〜SR-5)は見立てより「原本を名指す」側に寄っていた(VALUE_MISMATCH のほぼ全部が原本の先頭)。B で名指しに移る行(SR-8)は見立ての下限に寄っている。接頭辞(SR-12)は見立てより `jppfs_cor` に寄っている。外れたら外れのまま残す。

### §6-5 追記(2026-10-29、下調べの後。§2 の仕様の補い。§3 の字は変えない)

- **member ありは単体を含む。** 5 書類の member ありの先頭は全部 `NonConsolidatedMember` だった。§2-4 の `context` の表は、member ありを「`NonConsolidatedMember`」と「それ以外の member」の 2 列に分けて数える(`NonConsolidatedMember` は標準の member の名で、提出者の符号を含まないので文書に書いてよい。それ以外の member の字は書かない)。文書は member ありを「セグメント」と読まない。SR-13 の判定は §3 の字のとおり member ありの全部で行う。
- **recomputed が違う行の形。** 記録に、注入後の claim と基準の claim の `form` と、比較器を引ける欄が在れば並べる(`verify_document` の出力に比較器の名は無いので、`form` と `unit` だけを並べる)。`named` の表に「先頭は同じで recomputed が違う」の行数を列として出し、§2-4 の `examples` にその行を位置で 3 行まで出す。
- **(名指した・別の fact)の行の形。** 記録の P26・P27 で 1 行(§6-2)。`examples` にその行を位置で出し、基準と注入後の context の期・form を並べる(context の member の字は §2-5 のとおり書かない)。
- 下調べの 5 書類は記録の `docs` の先頭 5 件で、本番の 30 書類に含まれる。本番の記録はこの 5 書類についても作り直す(下調べの出力は使わない)。
