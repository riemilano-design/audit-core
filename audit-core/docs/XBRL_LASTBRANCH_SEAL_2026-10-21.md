# 封: 最後の枝の名指しは証拠があるときだけ「違う」と言う(engine の直し P25 = P24 + 旗 1 つ)― 2026-10-21

**この封は engine(`adapters/xbrl/vocabulary.py`・`recipes.py`・`registry_setup.py`)を変える。人間の承認(2026-10-21 深夜): 人間「engine に触るので承認が要る → 先に承認しておくので好きに進めて これをもって承認とする」、続けて「その先の展望まで全て進めといてね」(司令塔が示した展望: 丸めの帯 P23 → 語彙と枠 P24 → 最後の枝 P25 → 日本語の報告形 → 既定の切り替えは 1 回にまとめて人間に)。作法は変えない(封 → 実装 → 凍結 → 独立監査 GO → commit)。数を見てから封・予測を直さない。外れは外れとして残す。P24 段 1(c7ad668、宣言 92ae5e9)の後に置く。**

## §0 根拠(封の前の試作 3 回、scratchpad の clone。正本でない。司令塔の席の手元の報告 `scratchpad/lastbranch/proto_report.md`)

- 無改変の原文 67 書類 7,799 claim を P24 で: GROUNDED 4,382、VALUE_MISMATCH 1,203、UNVERIFIABLE 1,397、POINTER_NOT_FOUND 817(記録 fixtures/xbrl/vocab_2026-10-21.json と同じ数)。VALUE_MISMATCH 1,203 のうち **583 は最後の枝の名指し**(値が合う fact が無く導出も合わず、主語の当期の先頭 fact を名指す)。
- 試作 v1(証拠 = 同じ要素の別の期か別の枠で値が合う / 差 ≤ k 単位): k = 2 で VM 1,203 → 637。VM → PNF に動いた 566 行から書類ごとに上限 4 行の決め打ちの抽出で 228 行(64 書類)を読み、正しい文 227・文が本当に違う 0・分からない 1。**代価: 儀式の止め 82 / 245 が「違う」→「要確認」(10 倍の注入 71・±1 単位 11)、段 2 の注入 11 / 27(全部 単位の取り違え)。** k = 1 は k = 2 と同じ、k = 5 は残る「違う」6 行が全部偽。
- 試作 v2: 桁・単位の取り違え(10^n)を証拠に足したが、名指す fact の表示より下の端数も 10 倍になり帯から出て、10 倍は 71 → 64 しか戻らなかった。
- **試作 v3(この封 §1 の規則)**: VM 1,203 → 626(動いた 577 行は全部 VM → PNF `no_same_value`、GROUNDED と UNVERIFIABLE は 1 行も動かない)。最後の枝で VM に残る 6 行((i) 2・(ii) 2・(iii) 2)は全部読み正しい文(偶然の近さ 3 を含む)。動いた 577 行のうち読んだ 240 行(v1 の抽出 227 + 13)は正しい文 239・分からない 1・違う 0、**残り 337 行は読んでいない**。穴 B 通した 0 / 485・止め → 要確認 2。儀式 通した 2 / 247(N069・N096)・止め → 要確認 30(10 倍 19・±1 単位 11)。段 2 の材料 注入の GROUNDED 0 / 64・止め → 要確認 1 / 27。動いた行への注入 1,154 回(有効 1,118)で GROUNDED は P24 0・P25 0。n = ±9 の効き目は段 2 の注入 1 行だけ(無改変 0)。既存試験の赤 33(登録の一覧 13・test_mutations 1・sha 14・diff の門 5、数 / state の門 0、人間の決定の字の門 0)。engine recipes +72/−0・vocabulary +7/−0・registry_setup +2/−0。
- **試作は全部同じ 67 書類で測った。** 手元の cache の 67 の外 214 書類は全部 jpsps(経営分析の節なし、P24 の W-7 で確かめた)= 新しい標本は手元に無い。

## §1 直しの中身(engine 3 file、core/・comparators.py 0 行、既存の行は 1 行も書き換えない)

- `vocabulary.py`: `Profile` に `last_branch_names_only_if_evidence: bool = False`。`P25 = dataclasses.replace(P24, name="P25", last_branch_names_only_if_evidence=True)`、`PROFILES["P25"] = P25` を足す(`PROFILES = {...}` の行の字は変えない)。**段 1 では既定にしない(DEFAULT_PROFILE = "P22" のまま)。** 旗が偽なら 1 行も変わらない。
- `recipes.py` の最後の枝(主語があり、値が合う fact が無く、導出 a−b も合わず、§1b の止め・F2′・P24 frame_rebind・F1′・F3b のどれにも当たらず、主語の当期の先頭 fact = 「名指す fact」を名指して VALUE_MISMATCH にする直前)で、旗が真なら証拠を見る。照合の帯は `vocabulary.match_value` が当てるもの(主張の桁・書類の丸め方・P23 の `_mag_trunc`)。
  - (i) 名指す fact と**同じ要素名・同じ枠**(context から期の接頭辞を除いた字が同じ)で context が違う JPY の fact(単位の字が JPY で始まる)のどれかが、文の値と照合の帯で合う(期の取り違えの証拠)。別の枠・別の要素は証拠にしない。
  - (ii) `min(|名指す値 − 文の値|, ||名指す値| − |文の値||) ≤ 2 × 主張の桁`(桁の打ち間違いの証拠。`LAST_BRANCH_DIGIT_K = 2`)。
  - (iii) `n ∈ (1, −1, 2, −2, 3, −3, 6, −6, 9, −9)` のどれかで、名指す値が 文の値 × 10^−n と帯「書かれた数の精度 × 10^−n」で合う(桁・単位の取り違えの証拠)。書かれた数の精度 = 主張の桁 × 10^(round(|文の値| / 主張の桁) の末尾の 0 の数)、round は Python の `round`(偶数丸め)。n が負のとき帯は 精度 × 10^|n| に広がる(文の値を 10^|n| 倍して比べる側の精度)。符号は問わない。
  - どれかが真なら今までどおり名指して VALUE_MISMATCH。どれも偽なら pointer を付けず POINTER_NOT_FOUND、reason は登録簿の固定の名前 `no_same_value`(`registry_setup._POINTER_NOT_FOUND_REASONS` と `_state_of` の 2 か所に登録)。名指す fact の要素・context・値は `Claim.provenance["no_same_value"]` に残す(名指しは消さない)。
- **触る枝の中の人間の決定(列挙。字も振る舞いも 1 つも壊さない)**: 2026-10-08 案ア(no_subject)、§1b の止め、C2 `period_cue`、C-1g §1-3 `_build_point_diff_claim`、P21 の最後の枝(5eb80a2。この封は最後の枝の**後ろ**に証拠の判定を足すだけで、P21 の枝の字は変えない)、P22 `period_bind`(`subj and`)、P23 `_mag_trunc`、P24 の旗 2 つ(c7ad668)。これらの字を探す既存の門は直さずに緑。P16/P20/P21/P22/P23/P24 を明示した試験の数は 1 つも変えない。
- **過去の門の engine の留め**: ENGINE_LATER 系(branch_a・role_swap・axis3・p20_result・a_core_vs_grep・pnf_diag)、cd_seal FROZEN_LATER、point_prior_result・ritual_result・period_bind(seal/result)・rounding(seal/result)・vocab(seal/result)・registry_setup の sha を留める門、frozen_bundle の世代、axis3 LATER_ENGINE_COMMITS(次の便)。
- **P24 の監査の軽い指摘の手当て(同じ便)**: 率の枠の取り直し (ii) の旗が偽のとき効かないことを 1 件で直接見る unit 試験を `tests/adapters/xbrl/test_recipes_p24.py` に 1 本足す(engine は変えない)。

## §2 事前予測(実装前に固定。段 1 = P25 を旗で。対照は P24)

| # | 予測 | 外れ方 |
|---|---|---|
| **L-1** | 67 書類の無改変で VALUE_MISMATCH **620〜632**(P24 1,203)。動く行は全部 VM → POINTER_NOT_FOUND `no_same_value` で **570〜584**、GROUNDED と UNVERIFIABLE の数は P24 と同じ | 幅の外 / 他の向きが 1 行以上 |
| **L-2** | 最後の枝で VM に残る行 **4〜8**、全部読んで「文が本当に違う」**0〜1** | 幅の外 |
| **L-3** | **試作で読んでいない VM → PNF の行を全部読み、「文が本当に違う」が読んだ行の 2% 以下**。読んでいない行 = 段 1 で動いた行 − 試作で読んだ集合(試作 v1 の記録 `scratchpad/lastbranch/proto.json` の読み 228 行と v3 の 13 行の (doc, id)。実装席はこの (doc, id) の一覧を記録に写す)。試作では 337 行に当たる | 2% 超 |
| **L-4** | 穴 B の 485 件を P25 で通す **0**、止め(P24 で VALUE_MISMATCH の 483)のうち → 要確認 **0〜4** | 通す 1 以上 / 5 以上 |
| **L-5** | 儀式を P25 で: 通した **2〜3**、注入の止め → 要確認 **26〜34**(素の書類の VM の動きは含めない) | 幅の外 |
| **L-6** | 段 2 の材料: 注入の GROUNDED **0 / 64**、注入の止め → 要確認 **0〜2** | 幅の外 |
| **L-7** | 67 書類で P24 → P25 に動いた全行への注入(1 回に 1 件、末尾の桁 ±3・10 倍、試作と同じ作り方)で P25 が GROUNDED にする **0** 回 | 1 回以上 |
| **L-8** | engine の差分 `recipes.py` **+60〜+90 / −0**、`vocabulary.py` **≤ 10 行**、`registry_setup.py` **≤ 5 行**(行数は挿入 + 削除)、`comparators.py`・`core/` 0 行。既存試験の赤は登録の一覧・旗の形・sha の留め・diff の門だけ(数 / state の門 0、人間の決定の字の門 0) | 超える / `recipes.py` の削除 1 行以上 / 種類の外の赤 |
| **L-9** | 段 2(既定 P22 → P25 をまとめて 1 回)は人間に 3 つの率(誤りを通す率・無改変で「違う」と言う率・結べない率)と、「違う」が「要確認」に移る注入の数を見せてから | ― |

**L-1・L-2・L-4〜L-7 は試作の再現で、外れるなら実装が試作と違うことを示す。本当に外れうるのは L-3(試作で読んでいない 337 行)である。** 新しい標本は手元に無い(§0)。

## §3 限界

- **「違う」を「要確認」に弱める代価がある**: 増減の数・前期の数で、注入前に結んだ fact と名指す fact が別物の誤りは、どの証拠にも当たらず「要確認」になる(試作で儀式の ±1 単位 11・10 倍 19、段 2 の単位の取り違え 1)。誤りを**通す**数は変わらない(GROUNDED にはしない)が、顧客の報告では「違う」でなく「要確認」に出る。
- (iii) の帯は末尾の 0 が多い数で広がる(無改変の偶然の「違う」1: S100YYK8 N041)。(ii)・(iii) は偶然の近さでも立つ(残る 6 のうち 3)。
- 増減の数で、表示桁の fact の当期 − 前期と 1 単位違う正しい文(試作で 29 行)は「要確認」になる(丸めた値の差の帯の問題。この封では直さない)。
- 顧客の出力(verify_document)には provenance の欄が無い。「当期の値は X」を見せるのは日本語の報告形の封で決める。
- 試作も実装も同じ 67 書類。新しい標本での率は未測定(EDINET から取るのは人間の決定)。

## §4 触る file と順序

段 1: `adapters/xbrl/vocabulary.py`・`adapters/xbrl/recipes.py`・`adapters/xbrl/registry_setup.py` → 登録の一覧の試験に P25 → `tests/adapters/xbrl/test_recipes_p25.py`(+ `test_recipes_p24.py` に 1 本) → `measure/xbrl_lastbranch_2026-10-21.py`(L-1〜L-8) → `fixtures/xbrl/lastbranch_2026-10-21.json` → `docs/XBRL_LASTBRANCH_RESULT_2026-10-21.md` → `tests/measure/test_xbrl_lastbranch_result.py` → pin の遷移 → 覆い。段 2(人間に見せてから): `DEFAULT_PROFILE` + 既定の字の試験 + 儀式の走らせ直し + README + pin。
順序: 人間の事前承認(2026-10-21)→ P24 段 1 の commit(c7ad668・92ae5e9)→ **この封 + 封の門を commit** → 段 1 実装(別席)→ 凍結 → 独立監査 → commit → axis3 の宣言 → 日本語の報告形の封 → 段 2 を人間に。
