# 封: 既定の profile を P22 から P26 に切り替える(段 2)― 2026-10-23

**人間(2026-10-21 朝)「新しい標本取り、テストしてP25にするか判断したらどう?」「取って良い あとは全て任せる」。engine の事前承認(2026-10-21)「engine に触るので承認が要る 先に承認しておくので好きに進めて これをもって承認とする」。** 既定にするかどうかは封 `docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md`(commit `14cdd21`)§3 の基準で決め、判定は記録の数から機械で求め司令塔は覆さないと封じてある。判定は結果 `docs/XBRL_FRESH_SAMPLE_RESULT_2026-10-21.md`(commit `52289c4`)で **P26**。この封は §3 が名指した段 2(`DEFAULT_PROFILE`・既定の字の試験・儀式の走らせ直し・README・pin)を、作法(封 → 実装 → 凍結 → 独立監査 GO → commit)のまま行うための封で、予測・pin の一覧・代価を実装の前に固定する。数を見てから封・予測を直さない。外れは外れとして残す。**この封の commit 時点では `DEFAULT_PROFILE = "P22"` のまま。** 0 USD・通信なし・鍵の値は読まない。人間の確認が要りうる点は §1-4 に列挙した(この封は勝手に直さない)。

## §0 根拠(この封は新しく測らない。数は commit `52289c4` の木の記録。試作の数は正本でない)

- 判定(記録 `fixtures/xbrl/fresh/fresh_2026-10-21.json` の `判定`): 候補の順は P26 → P25 → P24、既定は **P26**。P26 は K-1(通した 5 対 P22 の 5)・K-2(偽 0 / 新 GROUNDED 59)・K-3(文が本当に違う 0・分からない 0 / 「違う」が弱まった行 436)を全部満たし、P25(K-3 は 0 / 361)・P24(0 / 64)も全部満たす。先頭の候補が P26。
- 封 `docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md` §3 の字: 「**P26(…)の段 1 が取得より前に commit されていれば、候補は P26 → P25 → P24 の順**。P26 も K-1〜K-3(P22 → P26 で同じ定義)で判定し、満たせば P26 を既定にする。」「判定は記録の数から機械で(門で縛る)。司令塔は判定を覆さない。」P26 の段 1 `b778dd9` は取得の最初の ZIP(2026-10-22T15:15:15Z)より前(記録の `順序`)。
- 無改変の 4 state、67 書類(claim 7,799)、いまの既定 P22 → P26: GROUNDED 4,242 → 4,371・VALUE_MISMATCH 1,410 → 433・UNVERIFIABLE 1,323 → 1,579・POINTER_NOT_FOUND 824 → 1,416(P22 は `fixtures/xbrl/customer_report_2026-10-21.json`、P26 は `fixtures/xbrl/p26_2026-10-21.json`)。
- 無改変の 4 state、新しい標本 30 書類(claim 3,923)、P22 → P26: GROUNDED 2,142 → 2,194・VALUE_MISMATCH 677 → 250・UNVERIFIABLE 690 → 774・POINTER_NOT_FOUND 414 → 705(記録の `A`)。state の違う行は 507(記録の `動いた行`)。
- 誤りを通す側(P26 明示の記録): 穴 B の注入 0 / 485、儀式 2 / 243、段 2 の材料の注入 0 / 64(`p26_2026-10-21.json`)。新しい標本の注入 741 回で通したのは P22 から P26 まで同じ 5 件。
- **読みはエージェントの読みで、人間の読みではない**(K-2・K-3 は読みに依る)。監査が示した K-3 の転び方は §3。
- **試作(scratchpad の clone。正本でない。`scratchpad/default_p26/`)**: `DEFAULT_PROFILE` の 1 行だけを P26 にした clone で、(1) 67 書類と新しい標本 30 書類を profile 省略で検証 → P26 明示と byte 一致(違った書類 0 / 97)・4 state は上の記録の P26 と同じ、(2) 儀式を走らせ 通した 2 / 243、(3) 試験を走らせて赤を数えた(§2 の S-8)。試作の数は §2 の幅に写したもので、記録(fixtures)に無い。実装席が同じ測定を記録に残す。

## §1 変えるもの(engine 1 file の 1 行。残りは試験・記録・文書)

### §1-1 engine

- `adapters/xbrl/vocabulary.py`: `DEFAULT_PROFILE = "P22"` を `DEFAULT_PROFILE = "P26"` に(1 行)。日付つきの決定の注記を足す(P16・P20・P21・P22 の注記は消さない。前例は a516288・d0b544c とも +5/−1)。**他の engine の行は 1 字も変えない。** `recipes.py`・`extract.py`・`registry_setup.py`・`report_customer.py`・`comparators.py` ほか adapters/xbrl の 15 file と `core/` は 0 行(sha16 が封の commit 時点と同じ)。`run.py` と `verify_document.py` は既定の名前を `V.DEFAULT_PROFILE` から引くので、実行の字は変えない。
- P22 以前の profile の字、`PROFILES` の行、P26 の定義は変えない。P16〜P25 を明示した呼び出しと試験の数は 1 つも変えない。

### §1-2 既定を名指す字の区分(`git grep -c DEFAULT_PROFILE 52289c4` で 94 file・303 か所を数えた。直す / 残す)

| 区分 | file | 字 | 直す / 残す |
|---|---|---|---|
| engine | 3 file | 8 | `vocabulary.py` の 1 行と注記を**直す**。`run.py`(3)は `V.DEFAULT_PROFILE` を引く字で名前を書かない = 残す。`verify_document.py`(3)の実行の字 2 は残す、docstring の 1 つは §1-3 の HUMAN で**残す** |
| frozen_bundle | `fixtures/frozen_bundle_sha.py` 1 file | 8 | 世代の一覧に新しい世代を**足す**(過去の世代は消さない) |
| tests/adapters/xbrl | 10 file | 22 | 既定の字(`"P22"`)と「既定では旗が偽」の字を見る試験を**直す**(`test_p17.py`・`test_p20.py`・`test_recipes_p21.py`〜`test_recipes_p26.py`・`test_run.py`・`test_verify_entry.py` の 10 file。試作で 15 本が赤)。P16〜P25 を明示した試験は触らない |
| tests/measure | 30 file | 159 | 封・結果の門が既定を字で留めている所を**直す**(試作で 24 file・66 本が赤。§4 の一覧)。測った当時の既定を字で留めている所(過去の値)は**残す** |
| measure | 14 file | 42 | 既定を前提にして記録を再現する script を**直す**(`ritual_2026-10-20.py` の guard、`xbrl_customer_report_2026-10-21.py` と `xbrl_customer_report_fix_2026-10-21.py` の「`None if profile == "P22"`」を P22 の明示に、`xbrl_period_bind_2026-10-20.py` の段 2 の測定を測った当時の既定 P22 に固定。記録の字は直さない)。記録に `DEFAULT_PROFILE` の欄を書くだけの script は残す |
| fixtures/xbrl | 13 file | 23 | 測った記録の中の `DEFAULT_PROFILE` の欄。**残す**(記録は 1 字も直さない) |
| docs | 23 file | 41 | 過去の封・結果・文書。**残す**(本文は直さない。足すのは日付つきの追記だけ) |

- 上の表に `DEFAULT_PROFILE` の字が無いが既定を名指す file: `README.md`(「いまの段」と「10 分の再現」の節)・`README.en.md`(同じ節)= **直す**(P26 の行を足し、儀式の数を P26 の記録に。P22 のときの数は日付つきで残す)。`docs/FACTS_FOR_BUYERS_2026-10-20.md` は P22・P26 の字が 0 = **触らない**(§6 の覆いの 4 行だけ直す)。`docs/SUITE_COVERAGE_2026-10-16.md` は覆いの数。
- 儀式(`measure/ritual_2026-10-20.py`): 買い手が今の既定で走らせるもの。guard「既定が P22」を P26 に直し、記録 `fixtures/xbrl/ritual_2026-10-20.json` を P26(既定)で採り直す。P22 の記録は byte 一致の写し `fixtures/xbrl/ritual_2026-10-20_p22.json` と履歴に残す(前例: `ritual_2026-10-20_p21.json`)。結果文書 `docs/XBRL_RITUAL_RESULT_2026-10-20.md` は本文を直さず末尾に日付つきの追記。
- 新しい測定: `measure/xbrl_default_p26_2026-10-23.py` → `fixtures/xbrl/default_p26_2026-10-23.json` → `docs/XBRL_DEFAULT_P26_RESULT_2026-10-23.md` → `tests/measure/test_xbrl_default_p26_result.py`(profile 省略 = 既定で §2 の測定をして、P26 明示の記録と 1 行ずつ比べる。対照: 既定を実行中だけ P22 に戻すと差が出る)。

### §1-3 HUMAN の残り項目(この封は直さない)

- `adapters/xbrl/verify_document.py` の docstring「`--profile` を省くと `vocabulary.DEFAULT_PROFILE`(= P20。2026-10-14 の人間の決定)」は、P21 の段 2 から食い違ったまま(儀式の封・d0b544c が「HUMAN: 1 行の docstring の直しの承認」として残した)。engine の file で、`verify_document.py` の sha16 を留める門が複数ある。**この封も直さない。** 段 2 で既定が P26 になると食い違いは 4 つめ(P20・P21・P22 に続く)になる。直すには 1 行の承認と、sha16 の留めの遷移が要る。

### §1-4 人間の確認が要りうる点(列挙。封は先に進む前提で書いたが、止めるなら実装の前に)

1. **engine の承認の範囲**: 事前承認の言葉(2026-10-21)は P26 の engine の直し(段 1)に向けて言われた。段 2 の engine の行は `vocabulary.py` の 1 行だけで、人間の「あとは全て任せる」と封 14cdd21 §3 の「全部満たす → 既定にする」「司令塔は判定を覆さない」に基づいて進む。及ばないと読むなら実装の前に止める。
2. **DECISION_LOG**: `vocabulary.py` の既定の注記(2026-10-13)は「変えるときは人間の決定と DECISION_LOG の項目が要る」と書く。P20・P21・P22 の切り替えは `docs/DECISION_LOG.md` に項目を足さず(最後の更新は 2026-10-13)、封・結果文書と人間の言葉で残した。今回も同じ扱い。足すべきなら人間が決める。
3. **verify_document.py の docstring**(§1-3)。
4. **段 2 と無関係の赤が 1 本、既に在る**: `tests/core/test_boundary.py::SecretKeyBoundaryTest::test_no_edinet_api_key_value_anywhere_under_audit_core`(鍵の値が無いことを字の型 `EDINET_API_KEY` の後ろに 8 字以上、で検査する門)が、新しい標本の取得 script の使い方の字と、その試験の偽の字の 2 file に当たって赤(`52289c4` の木で赤。鍵の値ではない。段 2 の前から)。この封は直さない(指定外)。段 2 の「全緑」の前に、人間か司令塔が別便で決める。
5. **K-3 の読み**(§3): 読みを変えれば既定は P25 か P24 になる。封は封の語義で P26。

## §2 事前予測(段 2 の実装の前に固定。既定 = profile 省略)

| # | 予測 | 外れ方 |
|---|---|---|
| **S-1** | profile を省いた `verify_document` の出力を `sort_keys` の JSON にした字が、`profile_name="P26"` 明示と 1 byte も違わない: 手元の 67 書類(claim 7,799)で違った書類 **0 / 67**、新しい標本 30 書類(claim 3,923)で **0 / 30**。対照(既定を実行中だけ P22 に戻す)で違う書類は **97 / 97**(出力の `profile` の欄が違う) | 1 書類でも違う / 対照が 97 / 97 でない |
| **S-2** | 67 書類の既定の 4 state は P26 の記録のとおり GROUNDED **4,371**・VALUE_MISMATCH **433**・UNVERIFIABLE **1,579**・POINTER_NOT_FOUND **1,416**(合計 7,799)。いまの既定 P22(4,242 / 1,410 / 1,323 / 824)から、GROUNDED を離れる行 **15〜23**(うち VALUE_MISMATCH に **5〜9**)、新しい GROUNDED **140〜156** | 4 state のどれか 1 つでも違う / 幅の外 |
| **S-3** | 新しい標本 30 書類の既定の 4 state は GROUNDED **2,194**・VALUE_MISMATCH **250**・UNVERIFIABLE **774**・POINTER_NOT_FOUND **705**(合計 3,923)。P22 と state の違う行は **507**、向きは VALUE_MISMATCH → POINTER_NOT_FOUND **297**・VALUE_MISMATCH → UNVERIFIABLE **139**・UNVERIFIABLE → GROUNDED **54**・POINTER_NOT_FOUND → GROUNDED **5**・GROUNDED → VALUE_MISMATCH **5**・UNVERIFIABLE → VALUE_MISMATCH **4**・GROUNDED → UNVERIFIABLE **2**・POINTER_NOT_FOUND → UNVERIFIABLE **1** | 1 つでも違う |
| **S-4** | 儀式(同梱の 1 書類、既定)は 通した **2 / 243 = 0.8%**・止めた(VALUE_MISMATCH)**210 / 243 = 86.4%**・結べない(POINTER_NOT_FOUND)**31**、素の書類(claim 412)は GROUNDED **340**・POINTER_NOT_FOUND **27**・UNVERIFIABLE **31**・VALUE_MISMATCH **14**。いまの P22 の記録(15 / 240 = 6.2%、素の書類 329 / 16 / 41 / 26)は byte 一致の写し `ritual_2026-10-20_p22.json` に残る。README の数は P26 の記録と 1 対 1 | 1 つでも違う / 写しが byte 一致でない |
| **S-5** | 報告形(`report_customer`)の節の件数、67 書類(claim 7,799)の既定: 違う **433**・要確認 **1,775**・対象外 **151**・判断しない **1,069**・一致 **4,371**(合計 7,799)。「違う」の節 = VALUE_MISMATCH の行(P22 の節は 1,410 / 915 / 151 / 1,081 / 4,242) | 1 つでも違う / 「違う」の節と VALUE_MISMATCH が食い違う |
| **S-6** | 誤りを通す側(既定): 穴 B の注入 485 件で通した(GROUNDED のまま)**0 / 485**(いまの P22 は 1 / 485)・止めた **480**・その他 **5**、段 2 の材料の注入 64 件で Core 自身が GROUNDED にした **0 / 64**。P26 の記録の P26 の欄と 1 行ずつ比べて違う行 **0** | 通した 1 以上 / 違う行がある |
| **S-7** | engine の差分は `vocabulary.py` の挿入 **≤ 8**・削除 **1**(`DEFAULT_PROFILE` の行)。adapters/xbrl の他の 15 file の sha16 と `core/` は 0 行(封の commit 時点と同じ)。束ねた指紋 `adapter_xbrl_py_sha256` と frozen_bundle の世代は動き、`adapter_xbrl_py_files` 16・`core_py_sha256`・frozen_bundle の本数 37 は動かない | 超える / 他の file が動く |
| **S-8** | `DEFAULT_PROFILE` の 1 行だけを P26 にした作業木(試作)で、`tests/measure` の赤 **66 本**(**24 file** = §4 (a) の 23 file + `test_xbrl_naming_fix_result.py`)・`tests/adapters/xbrl` の赤 **15 本**(10 file)。段 2 と無関係で既に赤の 1 本(`tests/core`。§1-4 の 4)は別に数える。幅は合計 **78〜84**。種類は 4 つだけ: (1) vocabulary.py の sha16・束ねた指紋・frozen_bundle・「engine を触っていない」を留める門、(2) 既定の字(`"P22"`)と「既定では旗が偽」を留める試験、(3) 既定を前提に走らせ直す門(報告形 2 本・期の縛りの段 2・儀式・点の前期・`test_verify_entry.py` の既定の数 4 本)、(4) 変異の baseline の連鎖。`tests/golden`・`tests/fixtures`・`measure/tests` の赤 **0**。**記録(fixtures)の数・state を書き換えないと緑にならない門 0**(儀式の記録だけは、買い手が今の既定で走らせるものなので採り直す = S-4)。人間の決定の字(recipes.py の決定の行)を見る門の赤 **0**。(3) は測定側を測った当時の profile(P22)に固定して直し、記録は 1 字も直さない | 幅の外 / 種類の外の赤 / 記録の数を書き換える門が出る / 人間の決定の字の門が赤 |
| **S-9** | 重い走らせ直し(`AUDIT_CORE_*=1`。報告形 2 本・新しい標本・期の縛り・儀式・点の前期・最後の枝・丸め・語彙・P26 の 10 本)を試作の作業木で走らせると、軽い門の赤のほかに増えた赤は **6 本**(新しい標本 1・報告形 1・報告形の直し 1・期の縛り 1・儀式 2)。P26・最後の枝・丸め・語彙・点の前期の走らせ直しは増えない。段 2 の実装の後は、10 本の走らせ直しが全部緑 | 増える赤が 6 でない / 実装の後に赤が残る |
| **S-10** | README.md と README.en.md の儀式の節の数は P26 の記録(S-4)と 1 対 1(門が節の全文を縛る)。`docs/FACTS_FOR_BUYERS_2026-10-20.md` の P22・P26 の字は 0 のまま(§6 の覆いの 4 行だけ動く) | 1 つでも違う |
| **S-11** | 覆い: 試験 file の数は、いま(`52289c4`)の 220 から、この封の commit で **221**(封の門 `tests/measure/test_xbrl_default_p26_seal.py`)、段 2 の commit で **222**(結果の門)。段 2 の実装で試験 file をほかに足さない | 数が違う |
| **S-12** | 判定は 記録から門が別の関数で求め直しても **P26**(K-1・K-2・K-3 を候補ごとに数え、順に P26 → P25 → P24)。この封は判定を覆さない | 違う |

予測 S-1・S-2・S-3・S-4・S-5・S-6 の数の多くは P26 明示の記録の写しで、**当たって当然の再現**(profile 省略が P26 明示と同じ出力を返すことの確認)。本当に外れうるのは S-1(配線)・S-2 の幅(P22 から動く行)・S-8(赤の数と種類)・S-9(重い走らせ直し)・S-11(覆い)である。

## §3 既定を替えたときの代価と限界(外れうる予測ではなく、封の時点で分かっている限界。読みはエージェントの読み)

- **K-3 の読みの転び方**(監査が示した。数は `52289c4` の commit の説明に在り、測定の記録ではない): P26 だけの丸めの 74 行(名指した前期と当期の差 a−b が文の数より 1 単位大きい。192 件のうち 1 単位小さい行 0・1 単位大きい行 74 で、切り捨て表示の形)を「分からない」と読むと P26 は K-3 を満たさず、既定は P25 になる。文の数に合う fact が書類に無い 59 行(部門・区分・予想・合計)を「分からない」と読むと P26・P25 とも満たさず、既定は P24 になる。封と前例の語義ではどちらも採らない(「正しい文」は『P22 の「違う」が偽だった』ことで、文の正しさを確かめたことではない)。**判定は覆さない**が、この読みを人間が採るなら既定は変わる。
- P22 で GROUNDED の行が P26 で VALUE_MISMATCH になる比率の主張 **5 行**(新しい標本。`docs` の 0 起点の位置と claim id で 5・N008、5・N056、10・N056、18・N050、20・N016)。原因は P23 の `pct_tolerance_from_decimals`(率の帯を書かれた桁から)。監査の読み: 4 行は文が正しい(率の切り捨て・外部顧客への売上)、10・N056 は丸めで説明できず決められない。K-1〜K-3 には数えていない。
- P22 で UNVERIFIABLE(`no_subject`)の行が VALUE_MISMATCH になる **4 行**(3・T018、9・N042、26・T076、26・T092)。原因は P24 の資金の語彙(`vocab_2026_10_21`)。読んでいない(文が正しいかは未確認)。
- P26 だけ GROUNDED → UNVERIFIABLE(`direction_on_cause_item`)になる **2 行**(4・T001、23・T020)。増減の語が原因の項目にかかる文。P25 までは GROUNDED。
- 67 書類では、P22 で GROUNDED の行のうち **GROUNDED でなくなる行**が試作で 19(VALUE_MISMATCH 7・UNVERIFIABLE 12)。S-2 の幅。段 2 の測定が全部を記録に出す。
- **丸めの差の 1 単位の書き誤りは「違う」でなく「要確認」に出る**(P26 の封 §3 の G3 の代価)。報告形の節で 67 書類の「違う」は 1,410 → 433、「要確認」は 915 → 1,775。新しい標本の注入 741 回では、止めのうち「違う」が 72.0% → 51.1%、「要確認」が 28.0% → 48.9%(値が偶然別の fact と一致する T5 は、P22 は 103 回とも「違う」、P26 は 11 回を「違う」・92 回を「要確認」)。**通した数は 5 のまま**。
- **注入で通した 5 件は 5 つの profile で同じ一覧**(全部 T2 の単位の差し替え)で、**原因は調べていない**。P26 を既定にしてもこの 5 件は止まらない。
- 区分の取り違えの疑い・向きの語の残りなど、「違う」に残る正しい文の主因は P26 では直っていない(P26 の封 §3)。新しい標本の「違う」250 行は全部が本当の誤りではない。
- 30 書類は 1 つの母集団(封 `431f436` の 256 件)からの引き。注入は 4 型だけ。読みはエージェントで人間ではない。席は 1 回も呼んでいない。
- 試作の赤の数(S-8)と重い走らせ直し(S-9)は試作の clone の実測で、記録に無い。実装席が同じ測定を記録に出す。

## §4 pin の遷移の一覧(段 2 の同じ便で。数は `git grep` で 52289c4 の木から数えた。封の門の test_16 が実物から数え直す)

**(a) `adapters/xbrl/vocabulary.py` の sha16 `83025e9c0525d08b` を字で留める門 23 本**(`git grep -l -F 83025e9c0525d08b 52289c4 -- tests` で数えた全部。どれも `tests/measure`)。段 2 で vocabulary.py が動くので、この 23 本それぞれに後の sha16 を宣言された遷移として足す(測った当時の値は消さない)。試作ではこの 23 本が全部赤になった:

  - `tests/measure/test_xbrl_a_core_vs_grep_seal.py`
  - `tests/measure/test_xbrl_axis3_decision.py`
  - `tests/measure/test_xbrl_branch_a.py`
  - `tests/measure/test_xbrl_cd_seal.py`
  - `tests/measure/test_xbrl_customer_report_fix_result.py`
  - `tests/measure/test_xbrl_customer_report_fix_seal.py`
  - `tests/measure/test_xbrl_customer_report_result.py`
  - `tests/measure/test_xbrl_customer_report_seal.py`
  - `tests/measure/test_xbrl_fresh_result.py`
  - `tests/measure/test_xbrl_lastbranch_result.py`
  - `tests/measure/test_xbrl_lastbranch_seal.py`
  - `tests/measure/test_xbrl_p20_result.py`
  - `tests/measure/test_xbrl_p26_result.py`
  - `tests/measure/test_xbrl_p26_seal.py`
  - `tests/measure/test_xbrl_period_bind_result.py`
  - `tests/measure/test_xbrl_period_bind_seal.py`
  - `tests/measure/test_xbrl_pnf_diag.py`
  - `tests/measure/test_xbrl_point_prior_result.py`
  - `tests/measure/test_xbrl_ritual_result.py`
  - `tests/measure/test_xbrl_rounding_result.py`
  - `tests/measure/test_xbrl_rounding_seal.py`
  - `tests/measure/test_xbrl_vocab_result.py`
  - `tests/measure/test_xbrl_vocab_seal.py`

**(b) 束ねた指紋 `adapter_xbrl_py_sha256` の `498993e29055472a…` を字で留める門 5 本**(`git grep -l -F 498993e29055472a 52289c4 -- .`)。(a) と重なる(段 2 の遷移を同じ便で宣言する):

  - `tests/measure/test_xbrl_customer_report_fix_result.py`
  - `tests/measure/test_xbrl_customer_report_fix_seal.py`
  - `tests/measure/test_xbrl_customer_report_result.py`
  - `tests/measure/test_xbrl_customer_report_seal.py`
  - `tests/measure/test_xbrl_p26_seal.py`

**(c) frozen_bundle の世代 `a97ecf7c44e60c45…` を字で留める所**(`git grep -l -F a97ecf7c44e60c45 52289c4 -- .`): `fixtures/frozen_bundle_sha.py` の世代の一覧に新しい世代を足す。字で留める門は次の 3 本(どれも (a) と重なる):

  - `tests/measure/test_xbrl_customer_report_fix_seal.py`
  - `tests/measure/test_xbrl_customer_report_seal.py`
  - `tests/measure/test_xbrl_p26_seal.py`

**(d) 既定の字だけで赤になる `tests/measure`**: `tests/measure/test_xbrl_naming_fix_result.py`(sha16 の字を持たず、`DEFAULT_PROFILE` が `"P22"` であることと古い注記の字が残ることを見る。注記の字は残し、既定の字だけ P26 に)。(a) と合わせて試作の赤の 24 file。

**(e) 既定の字を見る `tests/adapters/xbrl` 10 file**(`git grep -l DEFAULT_PROFILE 52289c4 -- tests/adapters/xbrl` で数えた全部。試作で 15 本が赤):

  - `tests/adapters/xbrl/test_p17.py`
  - `tests/adapters/xbrl/test_p20.py`
  - `tests/adapters/xbrl/test_recipes_p21.py`
  - `tests/adapters/xbrl/test_recipes_p22.py`
  - `tests/adapters/xbrl/test_recipes_p23.py`
  - `tests/adapters/xbrl/test_recipes_p24.py`
  - `tests/adapters/xbrl/test_recipes_p25.py`
  - `tests/adapters/xbrl/test_recipes_p26.py`
  - `tests/adapters/xbrl/test_run.py`
  - `tests/adapters/xbrl/test_verify_entry.py`

`test_recipes_p23.py` から `test_recipes_p26.py` の「既定ではその旗が偽(段 1 では既定にしない)」は、既定が P26 になるので「既定は P26」「P23〜P26 の旗が真」に直す(P23・P24・P25・P26 を明示した試験の数は変えない)。`test_verify_entry.py` の既定の数(未使用 2 書類の旗・14 書類の止めた件数・保留の照合・出力の sha256)は、前例 d0b544c と同じく、P22 を明示した試験に名前を変えて数を 1 つも変えず残し、既定(P26)の試験を足す。

**(f) 重い走らせ直しだけで赤になる 6 本**(試作。環境変数つき): `test_xbrl_fresh_result.py` の `RerunTest.test_heavy_everything_matches_the_record`(`AUDIT_CORE_FRESH=1`)、`test_xbrl_customer_report_result.py` の同名(`AUDIT_CORE_CUSTOMER_REPORT=1`)、`test_xbrl_customer_report_fix_result.py` の同名(`AUDIT_CORE_CUSTOMER_REPORT_FIX=1`)、`test_xbrl_period_bind_result.py` の `RerunTest.test_heavy_stage2_default_matches_the_record`(`AUDIT_CORE_PERIOD_BIND=1`)、`test_xbrl_ritual_result.py` の `RerunHeavyTest.test_4`・`test_6`(`AUDIT_CORE_RITUAL=1`)。

**(g) 軽い門で赤になる「既定を前提に走らせ直す」所**(試作): 報告形 2 本の `RerunTest.test_light_two_documents_match_the_record`、期の縛りの `RerunTest.test_light_stage2_default_e2_matches_the_stage1_moved_rows` と `test_light_stage2_the_comparator_sees_a_wrong_default`、儀式の `LabelTest.test_13`・`test_14`・`test_17`(guard が P22 でないと rc 1 で止まる)と `PredictionTest.test_8`、点の前期の `test_3`・`test_6`・`test_m0`(engine の差分 0 行を作業木の `git diff` で数える)。直し方は測定側を測った当時の profile に固定する(前例 `PROFILE_AT_MEASURE`)か、engine の留めを sha16 の遷移に移す。

**(h) 新しい門の名前**: 新しい門(この封の門と結果の門)で engine の留めを定義するときは `ENGINE_LATER`・`UNTOUCHED` ほか既存の門が行頭の名前を数える変数名を使わない(`ENGINE_LATER = {` を P25 の封の門 test_10 が、PIN_DEF の名前を P26 の封の門 test_16 が数える)。

**(i) axis3** の `LATER_ENGINE_COMMITS` に段 2 の commit を宣言するのは次の便(この commit の直後は axis3 の test_9 が赤。P22 の段 2 の前例と同じ)。

## §5 触る file と順序

段 2: `adapters/xbrl/vocabulary.py`(`DEFAULT_PROFILE` の 1 行と注記)→ 既定の字を見る試験と pin の遷移(§4)→ 儀式 `measure/ritual_2026-10-20.py` の guard・記録 `fixtures/xbrl/ritual_2026-10-20.json`・写し `fixtures/xbrl/ritual_2026-10-20_p22.json`・`README.md`・`README.en.md`・`docs/XBRL_RITUAL_RESULT_2026-10-20.md`(追記)→ `measure/xbrl_default_p26_2026-10-23.py` → `fixtures/xbrl/default_p26_2026-10-23.json` → `docs/XBRL_DEFAULT_P26_RESULT_2026-10-23.md` → `tests/measure/test_xbrl_default_p26_result.py` → 覆い(`measure/suite_coverage_2026-10-16.py --write`・`docs/SUITE_COVERAGE_2026-10-16.md` §2-1・`README.en.md`・`docs/FACTS_FOR_BUYERS_2026-10-20.md` §6 の A-06〜A-09)→ pin の遷移の宣言(`fixtures/frozen_bundle_sha.py` の新しい世代)。

順序: 人間の方針(2026-10-21 朝)→ 新しい標本の判定の commit(`52289c4`)→ **この封 + 封の門を commit** → 段 2 実装(別席)→ 凍結 → 独立監査 → commit → axis3 の `LATER_ENGINE_COMMITS` に段 2 の commit を宣言(次の便。段 1 の前例と同じ。この commit の直後は axis3 の test_9 が赤)。
