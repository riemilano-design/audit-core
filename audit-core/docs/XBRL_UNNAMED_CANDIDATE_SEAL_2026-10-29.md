# 封: P27 が「証拠が無く名指さない」で止めた行に、engine が内側に持つ「名指さなかった fact」を出力の候補の欄として添える ― engine の出力の形の変更の提案(**承認待ち**)― 2026-10-29

**この封は `adapters/`(engine)の出力の形を変える提案で、CLAUDE.md の作法 2 により実装は人間の承認の後。** 封は「承認を求める文書」で、承認の前に commit してよい(文書だけ)。承認はまだ無い(§5-3 に人間が決める点を列挙した)。人間 2026-10-29「次の戦略ある？」→ 司令塔「測定の測定を止め、商品の 1 点 = 名指しに戻る」→ 人間「君に任せる進めて」。この言葉は診断の便(`020ffc0`)までの範囲で、engine の出力の形を変える承認ではない。
作法は変えない(封 → **人間の承認** → 実装 → 測定 → 凍結 → 独立監査 GO → commit)。数を見てから封・予測を直さない。外れは外れとして残す(補足は日付つきの追記)。0 USD・通信なし・席(LLM)は呼ばない。評価用・調整用(`~/.cache/audit-core/edinetdb-p27/`)は開かない。

- 封の時点: branch `feature/audit-core-final-eval-8`、HEAD `020ffc0`、`vocabulary.DEFAULT_PROFILE = "P27"`。engine の sha16: `verify_document.py` `c3791080ab5aef2f`・`vocabulary.py` `514ebb8104451c07`・`report_customer.py` `6679138d350ec382`・`recipes.py` `52d645e713c53c1c`・`extract.py` `3cf55966f12919f0`・`registry_setup.py` `d6f25750bcd73c0a`・`resolve.py` `a41043763c1d4073`・`comparators.py` `d8706338325e725b`・`run.py` `e2192229bf2e4eff`・`report.py` `0d2854e659a5d8e0`。束ねた指紋 `adapter_xbrl_py_sha256` `92326a0f4dcefd21…`(16 file)・`core_py_sha256` `34e836bb39762d5a…`(4 file)。`fixtures/frozen_bundle_sha.py` の最新の世代 `030455282c89661b…`(37 本。作業木で測り直して同じ値)。
- この封は docID・claim の id・提出者別の接頭辞の要素名を書かない。書類と行は位置か集計で呼ぶ。診断の文書が避けた「元に戻す」系の語は使わず「P22 と同じ fact を候補として添える」と書く。
- 前例の型: `docs/XBRL_P27_SEAL_2026-10-27.md`(§0-5 の試作・§2-3 の留めの一覧)、`docs/XBRL_UNNAMED_FACT_DIAG_SEAL_2026-10-29.md`(§2 の配線の門・§3 の欄ごとの予測)、`tests/adapters/xbrl/test_report_customer.py` の「golden の遷移」。

## §0 根拠(記録の数。封を書く席が記録から数え直した)

### §0-1 看板との関係(司令塔の戦略、2026-10-29)

看板は「出所に縛る検証層」の 1 本。DB 側の相手(出所側のパートナー候補)に効くのは「止める」より「どの行かを指す」こと。P25 以降の engine は、証拠が無いとき名指さずに止める(`no_same_value`)が、その行で engine が内側に持つ「名指さなかった fact」(要素@期と値)は出力に出ない。診断 `020ffc0` は、その fact が P22 の名指した fact と同じかを字で数えた。この封は、その fact を **state・reason を変えずに**「候補」として出力に添える案を、承認を求める形で固定する。

### §0-2 診断の記録 `fixtures/xbrl/unnamed_fact_2026-10-29.json`(封 `d31371e` → 診断 `020ffc0`。文書 `docs/XBRL_UNNAMED_FACT_DIAG_2026-10-29.md`)

- 注入 741 行(新しい標本 30 書類。T1_VALUE 195・T2_UNIT 263・T5_COINCIDENT 103・T3_ABSENT 180)のうち P27 の reason が `no_same_value` の行は **156**(T1 2・T2 32・T5 92・T3 30)。その 156 行の全部に `named`(`xbrl:` で始まる字)と value(数。0 の行 0)が在る。
- **一致(基準)**: T1・T2・T5 の 126 行で `named` = 無改変の基準の claim の先頭の pointer が **126 / 126**(T1 2 / 2・T2 32 / 32・T5 92 / 92。(context だけ違う)・(要素だけ違う)・(両方違う)は 0)。T3 30 行は基準が無く、`named` = P22 の注入後の先頭が **30 / 30**。`named` の value = P22 の注入後の `recomputed` が **156 / 156**。
- **無改変の 30 書類**: P27 の `no_same_value` は **296 行**(書類ごと 1〜25)。全部に `named` が在り、その全部で P22 は VALUE_MISMATCH で同じ fact を名指していた(296 / 296)。fresh の P26 の dossier の名指した fact とも 296 / 296 で同じ字。比が(15% 以内)の行は 24 で、`regress97` の P27 → P27E で動いた 24 行と集合が同じ。**無改変の行は正解が無く、候補の正しさは測れない**(診断 §7 の 3)。
- 止めた理由の診断(`ed615b5`、記録 `fixtures/xbrl/stop_reason_2026-10-29.json`): 基準の在る型(T1・T2・T5)で止めた行は 553(T1 195・T2 255・T5 103。この封の席が記録の `結果` の 違う + 要確認 で数え直した)。そのうち原本の fact を名指した行は P22 497・P27 373(診断の文書の数。P27 の VALUE_MISMATCH 374 行のうち先頭が基準と別の fact の 1 行を除く)。差の大半は T5(P22 は 103 行の全部を名指し、P27 は 11 行)。

### §0-3 手元の 67 書類(有報の原文)の `no_same_value` の見込み(記録から積んだ。測るのは実装の後)

- P25 の `no_same_value` は 577(`fixtures/xbrl/lastbranch_2026-10-21.json` の L1。VALUE_MISMATCH → POINTER_NOT_FOUND `no_same_value` 577)。P25 → P26 で VALUE_MISMATCH → `no_same_value` に入った行 1(`fixtures/xbrl/p26_2026-10-21.json` Q1 の 向き)。P26 → P27 で `no_same_value` → `target_or_plan` に出た行 3(`fixtures/xbrl/p27/regress97_2026-10-27.json` の 動いた行)。**見込み 577 + 1 − 3 = 575**(§3 CA-4 は幅で書く)。P27 → P27E で動いた 82 行は全部 `no_same_value` から(VALUE_MISMATCH 81・`other_concept` 1)なので、P27 の `no_same_value` は 82 以上であることは記録から確か。
- 4 state の正本(`regress97` の 集計・`default_p27_2026-10-28.json` S2・S3): 67 書類 P27 GROUNDED 4,371・VALUE_MISMATCH 433・UNVERIFIABLE 1,601・POINTER_NOT_FOUND 1,394(claims 7,799)。30 書類 2,194・250・787・692(claims 3,923)。P22 は 67 書類 4,242・1,410・1,323・824、30 書類 2,142・677・690・414。

### §0-4 engine の事実(`adapters/xbrl/` を読んだ。封を書く前)

- `recipes.py`: 最後の枝の 3 か所(P27E の B `_last_branch_decide_2026_10_27`・P26 G2 `_last_branch_unname_2026_10_21`・P25 `_last_branch_unname`)が、名指さずに止めるとき `claim["reason"] = NO_SAME_VALUE` と `claim["no_same_value"] = {"named": "xbrl:<要素>@<context>", "value": <fact の値>}` を書く(3 か所とも同じ字)。`claim_to_recipe` が `raw["no_same_value"]` を `provenance["no_same_value"]` に写す(1 か所)。P27 の C2・C3 が束縛を消すときは `_P27_STALE_KEYS` で `no_same_value` も消す(その行の reason は `per_unit_counter`・`target_or_plan` になる)。
- `verify_document.py`: `CLAIM_FIELDS` は 12 欄(id・kind・form・subject・value・unit・word・span・state・pointers・reason・recomputed)で、行は `{k: row[k] for k in CLAIM_FIELDS}` で作る。`provenance` は出力に出ない。`dumps` は `indent=1, sort_keys=False`(欄の並びが byte を決める)。
- `report_customer.py`: `REASON_JA["no_same_value"]` = 「出典の当期の数と合わず、同じ数も桁違いの数もこの項目に無い。参照先を確かめる」。`no_same_value` の行は `section_of` で「要確認」(§2 の表。欄は # ・文の抜粋・文の値・理由)。pointer の字は `source_ja`(ラベル 期[区分: …])、値は `source_value_report`(`recomputed` を文の単位・桁に直す)が描く。`.provenance.json` は本文の sha256 と指紋だけで claim の欄を持たない。
- `run.py`(Claim の層。`recipe.pointers` を自分の欄で書く)・`report.py`(`c["pointers"]`・`c["recomputed"]` を読む)・`verify_external.py`(自分の `RESULT_FIELDS`)は `CLAIM_FIELDS` を読まない。候補の欄は `pointers`・`recomputed` に入れないので、この 3 つの出力は変わらない。
- `vocabulary.Profile` は `frozen=True` の dataclass。旗は末尾に足せる(P27 の旗 5 つの後ろ)。`DEFAULT_PROFILE = "P27"`(封 `docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md`、人間の委任 2026-10-28)。

## §1 規則(司令塔が決めた範囲。実装者が 1 通りに書ける字で)

**この節の例の字と数は全部作り物。**

### §1-1 state・reason は 1 行も変えない

止め方(P27 の規則・P25 の証拠 (i)〜(iii)・P26 G1〜G5・P27E の B)はそのまま。変えるのは「止めた行に何を添えるか」だけ。4 state の意味(Claim Contract v0.2 §5 の 4 語)は変えない。`pointers` にも `recomputed` にも入れない(GROUNDED / VALUE_MISMATCH の意味を汚さない)。

### §1-2 出力に欄を 1 つ足す(`verify_document.py`)

- **欄の名前**: `candidate`。`CLAIM_FIELDS` の**末尾**に足す(13 欄目。`recomputed` の後ろ)。並びを字で固定する作りは変えない。
- **形**: `reason == "no_same_value"` かつ `claim.provenance` に `no_same_value` の鍵が在る行だけ `{"pointer": <provenance["no_same_value"]["named"] の字そのまま>, "value": <provenance["no_same_value"]["value"] そのまま>, "basis": "no_same_value"}`。**他の行は `None`**(欄は常に在る)。鍵の並びは pointer・value・basis の順(`dumps` は `sort_keys=False`)。
- **旗で囲う**: `vocabulary.Profile` に旗 `unnamed_candidate_2026_10_29: bool = False` を 1 つ足す(P27 の旗 5 つの後ろ。注記つき)。`verify_document` の行の組み立てで、`profile.unnamed_candidate_2026_10_29` が偽なら `candidate` は**全行 `None`**(欄は在る)。真なら上の形。
- **値の出どころは `claim.provenance["no_same_value"]` だけ**。`verify_document` が recipes の関数を呼び直したり、fact を引き直したりしない(名指しの規則を 2 か所にしない)。
- **当たる例**: reason `no_same_value`・provenance に `{"named": "xbrl:jppfs_cor:NetSales@CurrentYearDuration", "value": 1234000000.0}` → `candidate = {"pointer": "xbrl:jppfs_cor:NetSales@CurrentYearDuration", "value": 1234000000.0, "basis": "no_same_value"}`。
- **当たらない例**: state VALUE_MISMATCH(reason None)→ `None`。reason `other_concept`・`other_frame`・`target_or_plan` → `None`(provenance に別の鍵が在っても読まない)。旗が偽の profile → 全行 `None`。
- **既定の P27 でこの旗をどうするかは人間が決める(§5-3 の 2)。** 封の字としては 2 通りを書く: **(ア)** `P27 = dataclasses.replace(P26, …, unnamed_candidate_2026_10_29=True)`(既定の出力の形が変わる。P27E も P27 から作るので真)。**(イ)** P27・P27E は触らず、`P27C = dataclasses.replace(P27, name="P27C", unnamed_candidate_2026_10_29=True)` と `PROFILES["P27C"] = P27C` を P27E の行の後ろに足す(明示したときだけ候補が付く。`DEFAULT_PROFILE` は P27 のまま)。どちらでも §1-2 の形・§3 の予測は同じ(予測は旗の真偽で書く)。

### §1-3 客向けの報告(`report_customer.py`)― 2 つの案(どちらを勧めるかは書かない)

- **案 A(足す)**: 「要確認」の表の「理由」の欄で、`c.get("candidate")` が辞書の行だけ、`REASON_JA` の一文の後ろに「。候補: <要素の日本語ラベル(無ければ要素名)>・<期の字>・<値>」を足す。表の 1 行は 1 欄で改行できないので、字の上では同じ欄の中の 1 節になる(「1 行足す」= 1 節)。要素のラベルは `element_ja`、期は `period_ja`(`CurrentYearDuration` → 当期 など。表に無ければ context の字のまま)、区分(member)が在れば `source_ja` と同じ「[区分: …]」を期の後ろに付ける。値は `source_value_report` に `recomputed` を候補の value に替えた写しを渡して得る(文の単位・桁に直す。engine の値を自分で割らない)。新しい関数は `candidate_ja(c, labels)` の 1 つ(候補が無ければ空の字)。**当たる例**: 理由「出典の当期の数と合わず、同じ数も桁違いの数もこの項目に無い。参照先を確かめる。候補: 売上高・当期・1,234 百万円」。**当たらない例**: `candidate` が `None` の行(今の字のまま)。「違う」「一致」の節の行(候補は付かない)。
- **案 B(足さない)**: `report_customer.py` は 0 行。候補は `verify_document` の JSON にだけ出る。
- **どちらの案でも**: `REASON_JA` の字・20 行・`section_of`・判定・節の割り当ては変えない。`golden` について: `test_report_customer.py` の `SMALL_GOLDEN`・`UNITS_GOLDEN`・`GOLDEN_SHA256`(実出力 2 件 × 2)の入力は `candidate` の欄を持たない(`_claim` の 9 欄・2026-10-13 の実出力)ので、案 A でも**今の golden は byte で変わらない**と見る(§3 CA-9)。案 A なら、候補を持つ行を 1 つ足した**新しい golden**(`SMALL_GOLDEN_CANDIDATE` のような別名の定数)を足し、`candidate` の鍵が無い入力 → 今の字、辞書の入力 → 候補つきの字、の両方を留める。既存の golden の値は消さない(「golden の遷移」の型 = 測った当時の値を残し、新しい値を別名で足す)。

### §1-4 P27E との関係

P27E の B は、相対の差が 15% 以内なら名指して VALUE_MISMATCH にする(既定にしない。封 `docs/XBRL_P27_SEAL_2026-10-27.md` §1-2・§8)。候補の欄は state を変えないので **B と直交する**: B が名指した行は `no_same_value` でなくなり候補は付かず(`pointers` に出る)、B が名指さなかった行には候補が付く。P27E に旗を立てるかは §1-2 の(ア)(イ)に従う((ア)なら P27E も真、(イ)なら `P27EC` は作らない)。

### §1-5 やらないこと

- `pointers`・`recomputed` に入れない。4 state の意味を変えない。Claim Contract v0.2(`docs/CLAIM_CONTRACT_SPEC_v0.2.md`)§5 の Result の欄は `state`・`achieved_depth`・`provenance`・`messages` で、`provenance` は「何を(pointer と取得した値)・いつ・どこから」。**候補の欄は、Result の `provenance` の一部(止めた行で道具が見ていた fact)を出力に写すもので、4 語を増やさず、GROUNDED / VALUE_MISMATCH の根拠にもしない。** v0.2 は `verify_document` の出力 JSON の欄を列挙していないので、欄を足すことを禁じる字は無い(契約の版上げではない)。ただし契約の文書に「候補」の語は無く、意味は「止めた行で道具が見ていた fact。正しさは測っていない」に限る、とこの封が決める。
- 候補の正しさを人の目で見る便はこの封に入れない(0 USD の範囲では無理。§5-3 の 4)。
- 台帳 `docs/FACTS_FOR_BUYERS_2026-10-20.md` の行は足さない(§5-3 の 5)。

## §2 engine の範囲

### §2-1 触る file と関数(`core/`・`recipes.py`・`extract.py`・`registry_setup.py`・`comparators.py`・`resolve.py`・`run.py`・`report.py`・`verify_external.py` は 0 行。既存の行の書き換えは `CLAIM_FIELDS` の 1 行(`"recomputed")` → `"recomputed", "candidate")`)と、案 A のときの「理由」の欄を描く 1 行だけ。他は挿入)

| file | 足すもの・変えるもの | 行数の見込み |
|---|---|---|
| `adapters/xbrl/vocabulary.py` | 旗 `unnamed_candidate_2026_10_29`(1 行 + 注記)。(ア)なら P27 の `replace` の引数に 1 つ(既存の行の書き換え 1)、(イ)なら `P27C` と `PROFILES["P27C"]` の 2 行 | 3〜6 |
| `adapters/xbrl/verify_document.py` | `CLAIM_FIELDS` に `"candidate"`(末尾)、行の組み立てに `candidate` の 3〜6 行(旗・reason・provenance の鍵を見る)。docstring に 1 段(「候補の欄。state は変えない。2026-10-29 の封」) | 6〜12 |
| `adapters/xbrl/report_customer.py` | 案 A: `candidate_ja` と「要確認」の理由の欄の 1 行。案 B: 0 行 | 案 A 10〜20 / 案 B 0 |

- `verify_document.py` の `DOC_UNVERIFIABLE_RULE`(人間が承認した文面 2026-10-13)・`document_level`・`dumps`・`engine_fingerprint` の字は変えない。
- 試験(`tests/adapters/xbrl`): `test_verify_entry.py` に候補の試験を足す(旗が偽なら `candidate` が全行 `None`・旗が真なら `no_same_value` の行だけ辞書で pointer が provenance の `named` と同じ・他の行は `None`・`CLAIM_FIELDS` が 13 欄で末尾が `candidate`・`pointers` と `recomputed` は旗の真偽で 1 字も変わらない。変異: 旗を見ない / reason を見ない / `pointers` に足す / 鍵の並びを変える、で赤)。`test_report_customer.py` に案 A の golden(§1-3)。`test_vocabulary.py`・`test_recipes_p27.py` の profile の一覧は(イ)なら `P27C` を足す((ア)なら `test_recipes_p27.py` の「P27 = P26 + 旗 4 つ」の等式の試験を「+ 旗 5 つ」に直す)。`tests/adapters/xbrl/test_boundary.py` の import の一覧は広げない。

### §2-2 触る枝の中の人間の決定(字も振る舞いも壊さない)

1. `verify_document.DOC_UNVERIFIABLE_RULE`(2026-10-13)・「新しい判定規則は入れない」の docstring: 字は変えない。候補は判定ではない(state・reason・pointers・recomputed は旗の真偽で 1 字も変わらない = §3 CA-1・CA-2)。
2. `CLAIM_FIELDS` の「並びを字で固定する」(byte の安定のため): 並びは固定のまま末尾に 1 欄。
3. P25 の最後の枝(証拠が無ければ名指さない)・P26 G2・P27E の B の字: 変えない(候補はその 3 か所が既に書く `no_same_value` の鍵を読むだけ)。
4. **既定 `DEFAULT_PROFILE = "P27"`**(2026-10-28 の人間の委任): 変えない。既定の P27 に旗を立てるか((ア)/(イ))は人間(§5-3 の 2)。
5. `report_customer.py` の「判定(state・reason・pointer・recomputed)は足さず変えず、並べ方と字だけを変える」(封 `docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md`): 案 A は「理由」の欄の字に 1 節を足すだけで、節の割り当て・判定は変えない。
6. `REASON_JA["no_same_value"]` の一文(P25 の封 §1 の字): 変えない(後ろに足す)。

### §2-3 既存の門の engine の留め(`git grep -l -F <sha16> 020ffc0 -- tests` で数えた全部。実装の便で同じ便に宣言された遷移を足す。測った当時の値は消さない)

いまの sha16 を留める試験 file の数: `verify_document.py` `c3791080ab5aef2f` **27 file**・`vocabulary.py` `514ebb8104451c07` **33**・`report_customer.py` `6679138d350ec382` **11**・束ねた指紋 `92326a0f4dcefd21` **9**。4 つの和集合は **37 file、全部 `tests/measure`**:

`test_xbrl_a_core_vs_grep_seal.py`・`test_xbrl_axis3_decision.py`・`test_xbrl_branch_a.py`・`test_xbrl_cd8_rowclaim_reach.py`・`test_xbrl_cd_seal.py`・`test_xbrl_customer_report_fix_result.py`・`test_xbrl_customer_report_fix_seal.py`・`test_xbrl_customer_report_result.py`・`test_xbrl_customer_report_seal.py`・`test_xbrl_default_p26_result.py`・`test_xbrl_default_p26_seal.py`・`test_xbrl_default_p27_result.py`・`test_xbrl_fresh_result.py`・`test_xbrl_inject_reach.py`・`test_xbrl_lastbranch_result.py`・`test_xbrl_lastbranch_seal.py`・`test_xbrl_p20_result.py`・`test_xbrl_p26_result.py`・`test_xbrl_p26_seal.py`・`test_xbrl_p27_engine_result.py`・`test_xbrl_p27_inject_reach.py`・`test_xbrl_p27_result.py`・`test_xbrl_p27_seal.py`・`test_xbrl_period_bind_result.py`・`test_xbrl_period_bind_seal.py`・`test_xbrl_pnf_diag.py`・`test_xbrl_point_prior_result.py`・`test_xbrl_ritual_result.py`・`test_xbrl_role_swap_result.py`・`test_xbrl_rounding_result.py`・`test_xbrl_rounding_seal.py`・`test_xbrl_stop_reason.py`・`test_xbrl_t2_pass_diag.py`・`test_xbrl_unnamed_fact.py`・`test_xbrl_verify_inventory.py`・`test_xbrl_vocab_result.py`・`test_xbrl_vocab_seal.py`

留めの型(行頭の変数名で数えた。1 つの file が複数の型を持つので和は 37 を超える):

| 型(行頭の変数名) | file 数 | file |
|---|---|---|
| `ENGINE_LATER` 系 | 16 | a_core_vs_grep_seal・axis3_decision・branch_a・lastbranch_result・lastbranch_seal・p20_result・period_bind_result・period_bind_seal・pnf_diag・point_prior_result・ritual_result・role_swap_result・rounding_result・rounding_seal・vocab_result・vocab_seal |
| `FROZEN_LATER` | 1 | cd_seal |
| `ENGINE_TRANSITIONS` | 3 | fresh_result・p26_result・p26_seal |
| `UNTOUCHED`(+ `UNTOUCHED_LATER`) | 6 | customer_report_fix_result・customer_report_fix_seal・customer_report_result・customer_report_seal・p26_result・p26_seal |
| `PIN_DEF` | 1 | p26_seal |
| `ENGINE_AT_MEASURE` / `ENGINE_DECLARED`(診断の門の型。`ENGINE_DECLARED` は今は空が 6) | 12 / 6 | AT_MEASURE: cd8_rowclaim_reach・fresh_result・inject_reach・lastbranch_result・p26_result・p27_inject_reach・period_bind_result・rounding_result・stop_reason・t2_pass_diag・unnamed_fact・vocab_result。DECLARED: cd8_rowclaim_reach・inject_reach・p27_inject_reach・stop_reason・t2_pass_diag・unnamed_fact |
| `LATER_ENGINE_COMMITS` | 1 | axis3_decision(実装の commit を宣言するのは次の便。前例と同じ) |
| 別名の宣言 | 11 | default_p26_result(`P27_LATER`)・default_p26_seal(`DECLARED`)・default_p27_result(`ENGINE_DECL`)・p27_seal(`P27_AFTER16` と既定 P27 の宣言)・p27_engine_result(`DEFAULT_P27_FP_TO`)・p27_result(`DEFAULT_P27_FP_TO`)・verify_inventory(`ENGINE_SHA`・`VD_DOCSTRING_DECLARED`)・customer_report_result(`ENGINE_ADAPTER_SHA_LATER`・`MODULE_LATER`)・customer_report_fix_result(`ENGINE_FP_LATER`・`MODULE_LATER`)・customer_report_seal(`FINGERPRINT_LATER`・`FROZEN_BUNDLE_DEFAULT_P27`)・customer_report_fix_seal(`LATER_FINGERPRINT`・`LATER_TARGET`) |

- `fixtures/frozen_bundle_sha.py` の `FROZEN_BUNDLE_GENERATIONS` に新しい世代を足す(いまの世代 `030455282c89661b…`、37 本。本数は変わらない見込み。(イ)でも file は増えない)。
- `tests/adapters/xbrl`: `test_verify_entry.py` の `CLAIM_FIELDS` の留め(`tuple(row.keys()) == VD.CLAIM_FIELDS` ― 定数から読むので緑のまま)と、**1 書類の出力の本体の sha256 を字で留めた 5 本**(`_PINNED_BODY_SHA256_<開発書類の docID>` の P20・P21・P22・P26・P27。開発書類は手元の cache の 1 書類)は、欄が 1 つ増えるので旗の真偽に関わらず赤になる → 測った当時の値を残し、新しい値を別名で足す(golden の遷移の型。`del out["engine"]` の後に `candidate` を消した本体の sha256 が旧の値と同じことも 1 本足す = §3 CA-1 の最小の門)。`test_report_customer.py` の golden(§1-3)。`test_vocabulary.py` の `PROFILES` の一覧 2 か所は(イ)なら `P27C` を足す。`test_recipes_p27.py` の `FLAGS`(5 つ)の順と「P27・P27E だけが旗を持つ」の試験は新しい旗を見ないので緑のまま((ア)なら「P27 = P26 + 旗 4 つ」の等式の 1 本が赤)。登録簿の理由の数(20)・`REASON_JA` の数(20)は変えない。
- 重い走らせ直し(`AUDIT_CORE_*` の 13 変数のうち、この 4 つの sha16 のどれかを留める file が読む 11: `CUSTOMER_REPORT`・`CUSTOMER_REPORT_FIX`・`DEFAULT_P26`・`FRESH`・`LASTBRANCH`・`P26`・`PERIOD_BIND`・`POINT_PRIOR`・`RITUAL`・`ROUNDING`・`VOCAB`。`PACKAGING`・`CUSTOMER_OUT` は留めない)のうち engine の sha・指紋を記録と比べるものは、測った値の欄が 1 字も違わないことを確かめてから宣言された遷移を足す(封 `docs/XBRL_HEAVY_RERUN_FIX_SEAL_2026-10-27.md` の型)。**`verify_document` の出力 JSON の sha256 を記録と比べる重い走らせ直し(`regress97`・`default_p26`・`default_p27`・`fresh` の記録の「出力の sha256(engine の欄を除く)」の型)は、欄が増えるぶん旗の真偽に関わらず赤になる** → 実装の便で、比べる前に `candidate` の欄を落とす写しで比べ直す(記録の値は消さない)か、宣言された遷移で新しい値を足すかを 1 本ずつ列挙して監査に回す(数は予測しない。前例 P27 封 §10 の 7)。
- 新しい門(封の門・結果の門)で engine の留めを定義するときは、`ENGINE_LATER`・`UNTOUCHED`・`PIN_DEF`・`LATER_ENGINE_COMMITS`・`FROZEN_LATER`・`ENGINE_TRANSITIONS` を行頭の名前にしない(`ENGINE_TRANSITIONS_CAND` などの別名)。
- 封の文書に「`no_same_value` の名指した当期の値は `verify_document` の出力に欄が無く出さない」の字を持つ過去の封 3 本(`customer_report_seal`・`customer_report_fix_seal`・`lastbranch_seal` の門が照らす字)は、**過去の封の字として正しいまま残す**(直さない。門は過去の封の字を見るので緑のまま)。この封が「今は欄が在る」と書く。

## §3 事前予測(実装の後に測る。外れうる形。§6 の試作より前に固定)

測り方は §7 の script。「今の出力」= HEAD `020ffc0` の engine を `git archive` で取り出して同じ入力で得た出力(前例 `measure/xbrl_p27_regress97_2026-10-27.py` の「比べる側」)。「欄を落とした出力」= 各 claim から `candidate` の鍵を消し、`engine` の欄を除いた `sort_keys` の JSON。

| # | 欄 | 予測 | 外れ方 |
|---|---|---|---|
| **CA-1** | 旗が偽の恒等(97 書類の原文。P22・P27 の 2 profile) | 欄を落とした出力の sha256 が今の出力と **97 / 97** 書類で一致(2 profile とも)。`candidate` は全行 `None`(claims 7,799 + 3,923 = 11,722 行で辞書の行 **0**) | 1 書類でも違う / 辞書の行 1 以上 |
| **CA-2** | 旗が真の 4 state(97 書類。P27 に旗を立てた profile) | 書類ごとの 4 state が `regress97` の P27 と **97 / 97** で同じ。行ごとの state・reason・pointers・recomputed が旗が偽の出力と **11,722 / 11,722** で同じ。欄を落とした出力の sha256 も **97 / 97** で今の出力と一致 | 1 行でも違う |
| **CA-3** | 候補が付く行 = `no_same_value` の行(旗が真。30 書類) | 辞書の行 **296**、`reason == "no_same_value"` の行 **296**、両方の集合が同じ。`no_same_value` で候補が `None` の行 **0**、`no_same_value` でなく候補が辞書の行 **0** | どれかが違う |
| **CA-4** | 候補が付く行(旗が真。67 書類) | 辞書の行 = `no_same_value` の行で **560 以上 590 以下**(見込み 575。§0-3)。食い違う行 **0** | 幅の外 / 食い違い 1 以上 |
| **CA-5** | 候補の中身(30 書類。無改変) | `candidate.pointer` が診断の記録 `unnamed_fact_2026-10-29.json` の `plain_rows` の同じ (書類, id) の `named` と **296 / 296** で同じ字、`candidate.value` が `named の value` と **296 / 296** で同じ。`basis` は全部 `no_same_value` | 1 行でも違う |
| **CA-6** | 注入 741 行(旗が真の P27 を、診断の便と同じ配線 `RE.work_doc` で観測) | state・reason・pointers が記録 `stop_reason_2026-10-29.json` と **741 / 741** 同じ。候補が辞書の行 **156**(T1 2・T2 32・T5 92・T3 30)で、その pointer が記録 `unnamed_fact` の `rows` の `named` と **156 / 156**、= 原本の基準の先頭(T1・T2・T5)**126 / 126**、= P22 の注入後の先頭(T3)**30 / 30**。候補が `None` の行 **585** | どれかが違う |
| **CA-7** | 旗が真の P27E(30 書類) | 候補が辞書の行 = P27E の `no_same_value` の行 = **296 − 24 = 272**(B が名指した 24 行に候補は付かず、その 24 行は VALUE_MISMATCH で `pointers` に出る)。候補が付く行と B が名指した行の積 **0** | 幅の外(± 0。字で 272)/ 積 1 以上 |
| **CA-8** | 客向けの報告(旗が偽。97 書類。既定と `--full`) | `render_markdown` の本文が今の出力からの本文と **97 / 97 × 2** で byte 一致(案 A でも B でも) | 1 本でも違う |
| **CA-9** | 既存の golden(`test_report_customer.py`) | `SMALL_GOLDEN`・`UNITS_GOLDEN`・`GOLDEN_SHA256` の 4 値は、案 A でも B でも**今の値のまま緑**(入力に `candidate` の欄が無い) | 1 本でも赤 |
| **CA-10** | 客向けの報告(旗が真・案 A。30 書類) | 今の本文と違う行は「要確認」の表の行だけで、その数 = 候補が辞書の行 **296**(書類ごとに同じ数)。違う行の全部が「。候補: 」の字を 1 回だけ持つ。既定と `--full` で違う行の数は同じ | 他の節に差 / 数が違う |
| **CA-11** | 既存の試験の赤(engine の留め以外) | `test_verify_entry.py` の本体の sha256 の **5 本**が赤((ア)(イ)とも。欄が増えるため)。`test_vocabulary.py` の `PROFILES` の一覧 **2 本**は(イ)なら赤・(ア)なら緑。`test_recipes_p27.py` の等式 **1 本**は(ア)なら赤・(イ)なら緑。`test_report_customer.py` は **0 本**(CA-9)。`tests/measure` の 37 file は §2-3 の型どおり赤(数は予測しない) | 数が違う / 別の file が赤 |

- 封の席の偏り: CA-3・CA-5・CA-6 は診断 `020ffc0` の記録の再現で、外れるなら実装が「provenance の鍵をそのまま写す」と違う。本当に外れうるのは CA-4(67 書類は P27 の `no_same_value` を直接は数えていない)・CA-7(P27E の候補を数えた記録は無い)・CA-10(案 A の描き方は試作で初めて動く)・CA-11(赤の数は字で留めた試験を読んで数えた)。
- CA-2 の「11,722 / 11,722」は claims の和(7,799 + 3,923)で、記録の数から書いた。

## §4 採用の基準(数で。判定は記録から門が機械で求め、司令塔は覆さない)

**候補の欄を engine に残す(旗が偽なら何も変わらない)**のは次を全部満たすとき:

- **K-1(4 state の後退 0 行)**: CA-2 の行ごとの state・reason・pointers・recomputed の一致 11,722 / 11,722。
- **K-2(741 行の state 不変)**: CA-6 の 741 / 741。
- **K-3(旗が偽で恒等)**: CA-1 の 97 / 97(2 profile)と CA-8 の 97 / 97 × 2。
- **K-4(候補は `no_same_value` の行にだけ、その行の全部に付く)**: CA-3 の食い違い 0・CA-4 の食い違い 0。

**基準にしないもの**: 候補が付く無改変の行(30 書類で 296・67 書類で 560〜590)の**正しさ**は測れない(正解が無い。診断 §7 の 3)ので、基準にしない。CA-5・CA-6 の「同じ」は字の一致で、人の目は入らない。CA-7・CA-10・CA-11 は記録するが採用の判定に使わない。

**満たさないとき**: 欄と旗は engine に残さず(実装の commit をしない)、結果文書に「採用しない」と書く。直すなら新しい封。

## §5 限界・除外・承認

### §5-1 限界

1. 候補の正しさは測れない。候補は「止めた行で道具が見ていた fact」で、文の言う数の出所として正しいかは誰も見ていない(人の目を入れる便は別。0 USD の範囲では無理)。出せば、正しい文にも候補が付く(無改変の 30 書類で 296 行。代価の側の数)。
2. 「同じ」は字の一致(診断 §4 の 1)。基準そのものの結び付きが正しいかも測っていない。
3. 候補が付くのは `no_same_value` の行だけ。`other_concept`・`other_frame`・`rounded_diff_hold`・`cause_item` の provenance も名指さなかった fact を持つが、この封では出さない(意味が違う。別の封)。
4. 欄が増えると、出力 JSON の sha256 を留めた門・記録は旗の真偽に関わらず動く(§2-3)。「旗が偽なら何も変わらない」は**欄 1 つ(全部 `None`)を除いて**の意味で、P23〜P27 の「旗が偽なら 1 byte も変わらない」より弱い。これを避けるには「旗が偽なら欄も無い」にする手があるが、欄の並びを profile で変えると byte の安定の約束(§0-4)が profile 依存になるので、この封は「欄は常に在る」を採る(人間が決める点 §5-3 の 1 に含む)。
5. 30 書類・741 行・67 書類の観測で、他の書類で同じ数になるとは言えない。
6. 試作(§6)は既存の試験を走らせない。§2-3 の赤の数は CA-11 の分だけ予測し、`tests/measure` の数は予測しない。
7. 案 A の「候補」の字が客に伝わるか(「候補」を「道具が結んだ」と読まれないか)は測れない。字の良し悪しは人間が見る。

### §5-2 除外

- P27E の B の規則・ρ は触らない。候補の欄は B と直交する(§1-4)。
- 台帳の行(L-40 の「約 7 割」の隣に候補を含めた率を並べるか)はこの便に入れない(§5-3 の 5)。
- 調整用・評価用の文・DB の応答は開かない。Cabocia への紙・束には候補の欄を載せない(載せるかは別の便で人間が決める)。

### §5-3 人間が決める点(承認待ち。この封の実装はどれも人間の決定の後)

1. **欄を足すこと自体**(`verify_document.py` の `CLAIM_FIELDS` に `candidate` を足す。= `adapters/` の変更)。足さないなら、候補は `provenance` を読む外側の道具(`measure/` の側)で出す(診断 §8 の候補 2)。
2. **既定の P27 で旗を真にするか**: (ア)真(既定の出力の形が変わる。P27E も真)/ (イ)偽のまま、`P27C` を登録して明示したときだけ。
3. **客向けの報告に「。候補: …」を足すか**(案 A / 案 B)。
4. **候補の正しさを人の目で見る便を別に立てるか**(0 USD では無理。見るなら席(subagent)か人。見るなら新しい封で、読む行の選び方・席の数・指示文を先に固定する)。
5. **台帳の行**(L-40 の隣に「候補を含めた率」を並べるか。並べるなら印の付け方(行ごとの欄が入れ子なので印の文法が届くかを先に確かめる)も)。

### §5-4 承認の記録

- 人間の承認はまだ無い。この封の commit は文書だけ(封の門 §7 の 2 は承認の前に足してよい)。
- 実装・測定の script・記録の commit の前に独立監査(`step-auditor`)の GO が要る。
- 通信なし・0 USD。席は呼ばない。

## §6 試作(予測の後。scratchpad の clone。正本でない。0 USD)

§3 を書いて file を保存した後に(予測を固定 2026-10-30 00:12:15 JST。直後の 00:12:52 JST に開発書類の docID 1 か所を試験の変数名の中で伏せ字に直し、その時点の file 全体の sha256 `c4240744a3f94c17246f775bec5215e922d9d2ce7de78d0fba5f5ebb89d0a87e` を `probe/mtime_seal_predictions.txt` に残した(写しは `probe/seal_at_prediction.md`)。予測の字は不変)、§1 を clone の `adapters/` の写しに当て、先頭の 5 書類(診断の記録の出てくる順)で旗の真偽の出力を比べた(clone `probe/clone`、HEAD `020ffc0`。差分 `probe/clone_adapters.patch`(sha256 `7d99c419c4beb647330e88ef43e32e0c051d3170dcad9d6cf03156e461a3204b`。`vocabulary.py` +4 行・`verify_document.py` +6 行・−1 行・`report_customer.py` +21 行・−1 行。(イ)の形で `P27C` を登録した)。走らせ 00:14:05〜00:14:09 JST(`probe/mtime_probe_start.txt`・`probe/mtime_probe_observed.txt`)。走らせる側 `probe/scripts/probe_cand_one.py`(sha256 `c3a8643c487b162721b6607cf65d7756744ea30bbb142c9701873c681013cca1`)と driver `probe/scripts/probe_cand_2026-10-29.py`(sha256 `82b42dd5d5124dce4231f03c35bf7620fa5d0fdb718defb8e0eb0a4bc3a8027e`)→ `probe/runs/`・`probe/probe5.json`・`probe/probe5_stdout.txt`)。**§0〜§5 と §7 の字は変えていない**(この節の前までの字と §7 は、予測を固定した写しと byte 一致。`probe/seal_prefix_check.txt`)。

ここの数は下調べの数で、正本は §7 の記録と門が出す。**CA-1〜CA-11 の当否は本番の記録から門が求める。**

### §6-1 配線・環境

- 比べる側(「今の出力」)は HEAD `020ffc0` の `adapters/`・`core/` を `git archive` で取り出した `probe/base`(main の木は読んでいない・書いていない)。clone の P27(旗が偽)と `P27C`(旗が真)、base の P27 を、書類ごと・profile ごとに別の process で走らせた(15 process、6 並行)。ZIP は `~/.cache/audit-core/edinet-fresh-2026-10-21/` の 5 file を読むだけで、sha256 を取得の記録と照らした(5 / 5 一致)。`~/.cache/audit-core/edinet/` は読んでいない。`edinetdb-p27/` は開いていない。鍵の値は読んでいない(環境変数 6 つを外して走らせた)。
- cache: 開始 `edinet/` 281・`edinet-fresh-2026-10-21/` 40 → 終了 281・40(`probe/cache_before.txt`・`probe/cache_after.txt`)。`/tmp` に file を足していない(TMPDIR と PYTHONPYCACHEPREFIX は probe の下。`probe/tmp` は終了時に空)。clone の `git status` は `adapters/xbrl/` の 3 file の変更だけ(未追跡 0)。
- 所要: 5 書類 × 3 走らせで 4.7 秒(無改変の 1 書類の `verify_document` は 1 秒ほど)。
- 既存の試験は走らせていない。

### §6-2 観測(5 書類・claims 823。位置と集計だけ)

- **CA-1(旗が偽の恒等)**: `candidate` を落とした出力の `sort_keys` の JSON(`engine` を除く)の sha256 が base と **5 / 5** で一致。`candidate` が辞書の行 **0**(欄は 13 欄目に在り、全行 `None`)。束ねた指紋の file 数は base・clone とも 16。
- **CA-2(旗が真の 4 state)**: 書類ごとの 4 state が旗が偽と **5 / 5** で同じ。行ごとの state・reason・pointers・recomputed が旗が偽(= base)と **823 / 823** で同じ。**ただし「欄を落とした出力の sha256 が今の出力と一致」は 0 / 5** ― (イ)の形では出力の `profile` の欄が `P27C` で base の `P27` と字が違うため(§6-4)。
- **CA-3(候補が付く行 = `no_same_value` の行)**: 辞書の行 **74** = reason が `no_same_value` の行 74(書類ごと 16・22・4・18・14)。食い違い 0・0。
- **CA-5(候補の中身)**: 74 行の全部で、`candidate.pointer` が診断の記録 `plain_rows` の同じ (書類, id) の `named` と同じ字 **74 / 74**、value が `named の value` と同じ **74 / 74**、`basis` は全部 `no_same_value`。記録に無い行 0。
- **CA-8(報告の恒等。旗が偽)**: `render_markdown`(ラベル無し。既定と `--full`)の本文が base と **5 / 5 × 2** で byte 一致。
- **CA-10(案 A。旗が真)**: 本文で base と違う行は既定・`--full` とも **74 行**(= 候補が辞書の行)で、全部が「要確認」の表の行(`| N` で始まる)、全部が「。候補: 」を 1 回だけ持つ。消えた行 74 は同じ行の置き換え(他の節に差は無い)。候補の字の形は「<要素名>・<期の字>・<値 文の単位>」で、ラベル無しなので要素名が出た(例の形: 「。候補: jppfs_cor:CashAndDeposits・当期末・37,006 百万円」。値は文の単位の桁に直っていた)。
- CA-4(67 書類)・CA-6(741 行)・CA-7(P27E)・CA-9(golden の試験)・CA-11(試験の赤)は試作で測っていない。

### §6-3 下調べの時点の当否の見立て(本番の門が 97 書類・741 行で求め直す)

| # | 見立て | 理由 |
|---|---|---|
| CA-1 | 当たりの側 | 5 / 5・辞書の行 0 |
| CA-2 | **第 1・第 2 節は当たりの側、第 3 節(欄を落とした sha256 の一致)は(イ)なら外れの側** | 5 / 5・823 / 823。sha256 は `profile` の字で違う(0 / 5)。(ア)なら `profile` は `P27` のまま変わらず一致の側 |
| CA-3 | 当たりの側 | 74 = 74、食い違い 0 |
| CA-4 | 測っていない | 67 書類は走らせていない |
| CA-5 | 当たりの側 | 74 / 74・74 / 74 |
| CA-6・CA-7 | 測っていない | 741 行・P27E は走らせていない |
| CA-8 | 当たりの側 | 5 / 5 × 2 |
| CA-9・CA-11 | 測っていない | 既存の試験を走らせていない |
| CA-10 | 当たりの側 | 74 行・全部「要確認」・「。候補: 」1 回 |

見立ての向き: 「候補は provenance の鍵をそのまま写す」の見立てどおりで、5 書類で食い違う行は 0。外れの側は CA-2 の第 3 節で、封を書く席が「欄を落とした出力」の定義に `profile` の欄を含めたまま、(イ)の形では profile の名前が変わることを見落とした(予測の字は変えない。外れたら外れのまま残す)。

### §6-4 追記(2026-10-30、試作の後。§7 の script の補い。§3 の字は変えない)

- **CA-2 の第 3 節の測り方の補い。** §3 の「欄を落とした出力」は `candidate` と `engine` を除いた JSON で、`profile` の欄を含む。(イ)の形(`P27C` を登録)では旗が真の出力の `profile` が `P27C` になり、base の `P27` と一致しえない。本番の script は、CA-2 の第 3 節を「`candidate`・`engine` に加えて `profile` も除いた JSON の sha256」で**並べて**記録し(§3 の字どおりの値も記録する)、当否は §3 の字で判定する((イ)なら第 3 節は外れとして残る。(ア)なら §3 の字のままで測れる)。
- 試作の 5 書類は診断の記録の `書類(出てくる順)` の先頭 5 件で、本番の 30 書類・97 書類に含まれる。本番の記録はこの 5 書類についても作り直す(試作の出力は使わない)。

## §7 file と順序

1. **この封**(文書だけ。承認の前に commit 可)。本線へは `docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md` として司令塔が写して commit する(scratchpad の file と byte 一致)。docID・claim の id・提出者別の接頭辞・禁止語・code fence を含まない。
2. 封の門 `tests/measure/test_xbrl_unnamed_candidate_seal.py`(承認の前に足してよい): 封の字に docID・claim の id が 0 件、§2-3 の数(sha16 ごとの file 数・和集合 37・型ごとの数)を実物の `git grep`(封の時点の commit `020ffc0`)から数え直す、§1-2 の欄の名前・旗の名前・`basis` の字が実装の後の engine と同じ(実装の前は「まだ無い」を留める。前例 `test_xbrl_lastbranch_seal.py` test_14 の型)、封の commit が engine を 1 行も触っていない。
3. **人間の承認**(§5-3 の 1〜3 が最低限。4・5 は後でよい)。
4. 実装(1 commit。独立監査 GO の後): 旗・欄・(案 A なら)報告の 1 節、`tests/adapters/xbrl` の試験(§2-1)、engine の留めの遷移の宣言(§2-3 の 37 file)、`frozen_bundle` の世代、golden の遷移(`test_verify_entry.py` の 5 本・案 A の新しい golden)、覆い(`measure/suite_coverage_2026-10-16.py --write`・`docs/SUITE_COVERAGE_2026-10-16.md` §2-1: 241 → 242 以上)。
5. 測定 script `measure/xbrl_unnamed_candidate_2026-10-29.py`(実装と同じ便でも次の便でもよい。監査 GO の後に commit): (a) 97 書類の原文(`doc_lists()` は `regress97` の script と同じ。ZIP の sha256 を記録と照らす)で P22・P27・旗が真の P27(`V.PROFILES` に候補つきの profile が在ればその名前、無ければ実行中だけ `dataclasses.replace(V.P27, unnamed_candidate_2026_10_29=True)` を `V.PROFILES` に差し込み `finally` で戻す。戻せていなければ止める)・旗が真の P27E(30 書類だけ)を走らせ、CA-1〜CA-5・CA-7 を数える。比べる側は HEAD(実装の commit の親)の engine を `git archive` で取り出して別の process で走らせる。(b) 741 行は診断の script `measure/xbrl_unnamed_fact_2026-10-29.py` と同じ配線(`SR` を `_mod` で読み、`RE.OBS = ("P27",)`、`RE.work_doc(a)`)で、旗が真の P27 を走らせて CA-6 を数える(出力の claim に `candidate` が付くので包みは要らない。配線の門 W-1〜W-3 は診断の便と同じ字で通す)。(c) 客向けの報告は `render_markdown` を旗の真偽の出力に当てて CA-8・CA-10(ラベルは `~/.cache/audit-core/edinet-taxonomy/` の名簿の file だけ。無ければラベル無しで測り、記録にそう書く)。記録 `fixtures/xbrl/unnamed_candidate_2026-10-29.json`(docID と claim の id を持つ。span・原文は持たない。候補の pointer・value は持つ)、結果の文書 `docs/XBRL_UNNAMED_CANDIDATE_RESULT_2026-10-29.md`、門 `tests/measure/test_xbrl_unnamed_candidate_result.py`(表を記録から作り直す・CA-1〜CA-11 の当否を封の字と記録から求める・K-1〜K-4 の判定・engine の留めは `ENGINE_AT_MEASURE_CAND` / `ENGINE_DECLARED_CAND` の別名)。`tests/measure/test_xbrl_fresh_seal.py` の `LATER_NAMING_FILES` に記録・script・門の 3 つ、`tests/measure/test_xbrl_inject_harness_review.py` の `LATER_HARNESS_FILES` に script 1 行(使う側・有・根拠の字 `r = RE.work_doc(a)`)。
6. 凍結(木の sha256 の一覧)→ 独立監査 → GO → commit(パス指定)。監査中は木を触らない。
7. axis3 の `LATER_ENGINE_COMMITS` に実装の commit を宣言(次の便)。台帳・Cabocia の紙は別の便で人間が決める。

各便の commit はパス指定。主の木を赤くしうる実測は worktree で。
