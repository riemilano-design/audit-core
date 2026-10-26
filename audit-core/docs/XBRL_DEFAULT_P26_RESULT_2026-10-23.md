# 結果: 既定の profile を P22 から P26 に切り替えた(段 2)― 2026-10-23

封: `docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md`(commit `6a78b42`。本文は一字も直していない)。測定: `measure/xbrl_default_p26_2026-10-23.py`。記録: `fixtures/xbrl/default_p26_2026-10-23.json`。門: `tests/measure/test_xbrl_default_p26_result.py`。
**0 USD・通信なし・鍵の値は読まない・席は呼ばない。** 数のある表と文は記録から門が作る(散文の数は漢数字、識別子はコードの字)。**読みはエージェントの読みで人間の読みではない。**

## 0. 結論

- 予測 S-1〜S-12 の機械判定: 当たり 十・外れ 二。
- 外れた予測: S-8・S-9。外れは外れのまま残す(封と予測は直していない)。
- profile を省いた経路と P26 を明示した経路の出力は、手元の六十七書類で 零書類、新しい標本の三十書類で 零書類が違った(違った書類の数。零なら 1 byte も違わない)。
- 対照(既定を実行中だけ P22 に戻す)では、九十七書類のうち 九十七書類が違った。『差零』は自分の欠陥ではない。
- 測った書類は手元の 六十七・新しい標本の 三十、claim は 七千七百九十九 と 三千九百二十三。
- **判定は覆さない。** 既定にするかどうかは封 `docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md`(commit `14cdd21`)§3 の基準を記録の数から機械で求めた結果で、この段 2 はその実装である。判定の再計算(S-12)は別の関数が P26 と求め直した。K-3 の読み(正しい文かどうか)はエージェントの読みで、読みを変えれば既定は変わる(封 §3)。
- engine 全体の品質証明ではない。

## 1. 予測の当たり外れ

予測の欄は封の字そのまま。実測の欄と当たり外れは記録から門が作る。S-1〜S-6 の数の多くは P26 を明示した記録の写しで**当たって当然の再現**(profile を省いた経路が P26 明示と同じ出力を返すことの確認)。本当に外れうるのは S-1(配線)・S-2 の幅・S-8・S-9・S-11 である。

| # | 予測(封の字) | 実測 | 当たり外れ |
|---|---|---|---|
| **S-1** | profile を省いた `verify_document` の出力を `sort_keys` の JSON にした字が、`profile_name="P26"` 明示と 1 byte も違わない: 手元の 67 書類(claim 7,799)で違った書類 **0 / 67**、新しい標本 30 書類(claim 3,923)で **0 / 30**。対照(既定を実行中だけ P22 に戻す)で違う書類は **97 / 97**(出力の `profile` の欄が違う) | 違った書類 0 / 67・0 / 30。対照(既定を実行中だけ P22 に戻す)で違った書類 97 / 97 | **当たり** |
| **S-2** | 67 書類の既定の 4 state は P26 の記録のとおり GROUNDED **4,371**・VALUE_MISMATCH **433**・UNVERIFIABLE **1,579**・POINTER_NOT_FOUND **1,416**(合計 7,799)。いまの既定 P22(4,242 / 1,410 / 1,323 / 824)から、GROUNDED を離れる行 **15〜23**(うち VALUE_MISMATCH に **5〜9**)、新しい GROUNDED **140〜156** | GROUNDED 4,371・VALUE_MISMATCH 433・UNVERIFIABLE 1,579・POINTER_NOT_FOUND 1,416。GROUNDED を離れる行 19(うち VALUE_MISMATCH 7)・新しい GROUNDED 148 | **当たり** |
| **S-3** | 新しい標本 30 書類の既定の 4 state は GROUNDED **2,194**・VALUE_MISMATCH **250**・UNVERIFIABLE **774**・POINTER_NOT_FOUND **705**(合計 3,923)。P22 と state の違う行は **507**、向きは VALUE_MISMATCH → POINTER_NOT_FOUND **297**・VALUE_MISMATCH → UNVERIFIABLE **139**・UNVERIFIABLE → GROUNDED **54**・POINTER_NOT_FOUND → GROUNDED **5**・GROUNDED → VALUE_MISMATCH **5**・UNVERIFIABLE → VALUE_MISMATCH **4**・GROUNDED → UNVERIFIABLE **2**・POINTER_NOT_FOUND → UNVERIFIABLE **1** | GROUNDED 2,194・VALUE_MISMATCH 250・UNVERIFIABLE 774・POINTER_NOT_FOUND 705。P22 と state の違う行 507(VALUE_MISMATCH → POINTER_NOT_FOUND 297・VALUE_MISMATCH → UNVERIFIABLE 139・UNVERIFIABLE → GROUNDED 54・POINTER_NOT_FOUND → GROUNDED 5・GROUNDED → VALUE_MISMATCH 5・UNVERIFIABLE → VALUE_MISMATCH 4・GROUNDED → UNVERIFIABLE 2・POINTER_NOT_FOUND → UNVERIFIABLE 1) | **当たり** |
| **S-4** | 儀式(同梱の 1 書類、既定)は 通した **2 / 243 = 0.8%**・止めた(VALUE_MISMATCH)**210 / 243 = 86.4%**・結べない(POINTER_NOT_FOUND)**31**、素の書類(claim 412)は GROUNDED **340**・POINTER_NOT_FOUND **27**・UNVERIFIABLE **31**・VALUE_MISMATCH **14**。いまの P22 の記録(15 / 240 = 6.2%、素の書類 329 / 16 / 41 / 26)は byte 一致の写し `ritual_2026-10-20_p22.json` に残る。README の数は P26 の記録と 1 対 1 | 通した 2 / 243 = 0.8%・止めた 210 / 243 = 86.4%・POINTER_NOT_FOUND 31。素の書類(claim 412)GROUNDED 340・POINTER_NOT_FOUND 27・UNVERIFIABLE 31・VALUE_MISMATCH 14。記録 `ritual_2026-10-20.json` と違う欄 0 | **当たり** |
| **S-5** | 報告形(`report_customer`)の節の件数、67 書類(claim 7,799)の既定: 違う **433**・要確認 **1,775**・対象外 **151**・判断しない **1,069**・一致 **4,371**(合計 7,799)。「違う」の節 = VALUE_MISMATCH の行(P22 の節は 1,410 / 915 / 151 / 1,081 / 4,242) | 違う 433・要確認 1,775・対象外 151・判断しない 1,069・一致 4,371(合計 7,799)。「違う」の節と VALUE_MISMATCH の差 0 | **当たり** |
| **S-6** | 誤りを通す側(既定): 穴 B の注入 485 件で通した(GROUNDED のまま)**0 / 485**(いまの P22 は 1 / 485)・止めた **480**・その他 **5**、段 2 の材料の注入 64 件で Core 自身が GROUNDED にした **0 / 64**。P26 の記録の P26 の欄と 1 行ずつ比べて違う行 **0** | 穴 B で通した 0 / 485 = 0.0%・止めた 480・その他 5(P22 明示の対照は通した 1 / 485 = 0.2%)。段 2 の材料で Core 自身が GROUNDED 0 / 64 = 0.0%。P26 の記録の P26 の欄と違う行 0 | **当たり** |
| **S-7** | engine の差分は `vocabulary.py` の挿入 **≤ 8**・削除 **1**(`DEFAULT_PROFILE` の行)。adapters/xbrl の他の 15 file の sha16 と `core/` は 0 行(封の commit 時点と同じ)。束ねた指紋 `adapter_xbrl_py_sha256` と frozen_bundle の世代は動き、`adapter_xbrl_py_files` 16・`core_py_sha256`・frozen_bundle の本数 37 は動かない | `vocabulary.py` 挿入 4・削除 1。`core/` 0 行。ほかの engine の file で動いたもの 0 | **当たり** |
| **S-8** | `DEFAULT_PROFILE` の 1 行だけを P26 にした作業木(試作)で、`tests/measure` の赤 **66 本**(**24 file** = §4 (a) の 23 file + `test_xbrl_naming_fix_result.py`)・`tests/adapters/xbrl` の赤 **15 本**(10 file)。段 2 と無関係で既に赤の 1 本(`tests/core`。§1-4 の 4)は別に数える。幅は合計 **78〜84**。種類は 4 つだけ: (1) vocabulary.py の sha16・束ねた指紋・frozen_bundle・「engine を触っていない」を留める門、(2) 既定の字(`"P22"`)と「既定では旗が偽」を留める試験、(3) 既定を前提に走らせ直す門(報告形 2 本・期の縛りの段 2・儀式・点の前期・`test_verify_entry.py` の既定の数 4 本)、(4) 変異の baseline の連鎖。`tests/golden`・`tests/fixtures`・`measure/tests` の赤 **0**。**記録(fixtures)の数・state を書き換えないと緑にならない門 0**(儀式の記録だけは、買い手が今の既定で走らせるものなので採り直す = S-4)。人間の決定の字(recipes.py の決定の行)を見る門の赤 **0**。(3) は測定側を測った当時の profile(P22)に固定して直し、記録は 1 字も直さない | `tests/measure` の赤 68 本(25 file)・`tests/adapters/xbrl` の赤 15 本。合計 83。`golden`・`fixtures`・`measure/tests` の赤 0。記録を書き換えないと緑にならない門 0。人間の決定の字の門の赤 0。種類 1 が 40 本・2 が 13 本・3 が 18 本・4 が 12 本 | **外れ** |
| **S-9** | 重い走らせ直し(`AUDIT_CORE_*=1`。報告形 2 本・新しい標本・期の縛り・儀式・点の前期・最後の枝・丸め・語彙・P26 の 10 本)を試作の作業木で走らせると、軽い門の赤のほかに増えた赤は **6 本**(新しい標本 1・報告形 1・報告形の直し 1・期の縛り 1・儀式 2)。P26・最後の枝・丸め・語彙・点の前期の走らせ直しは増えない。段 2 の実装の後は、10 本の走らせ直しが全部緑 | 軽い門の赤のほかに増えた赤 6 本 | **外れ** |
| **S-10** | README.md と README.en.md の儀式の節の数は P26 の記録(S-4)と 1 対 1(門が節の全文を縛る)。`docs/FACTS_FOR_BUYERS_2026-10-20.md` の P22・P26 の字は 0 のまま(§6 の覆いの 4 行だけ動く) | README の儀式の節に 通した・止めた の字が在る: README.md 在る・README.en.md 在る。`FACTS_FOR_BUYERS` の P22 の字 0・P26 の字 0 | **当たり** |
| **S-11** | 覆い: 試験 file の数は、いま(`52289c4`)の 220 から、この封の commit で **221**(封の門 `tests/measure/test_xbrl_default_p26_seal.py`)、段 2 の commit で **222**(結果の門)。段 2 の実装で試験 file をほかに足さない | 試験 file 222 本(ディスク上)。覆われていない file 0 | **当たり** |
| **S-12** | 判定は 記録から門が別の関数で求め直しても **P26**(K-1・K-2・K-3 を候補ごとに数え、順に P26 → P25 → P24)。この封は判定を覆さない | 記録の判定: 既定 P26・候補の順 P26→P25→P24 | **当たり** |

## 2. 実測

### 2-1 S-1: profile を省いた経路と P26 明示

| 標本 | 書類 | claim | 既定と P26 明示で違った書類 | 既定を実行中だけ P22 に戻した対照で違った書類 |
|---|---|---|---|---|
| 手元の 67 | 67 | 7,799 | 0 | 67 |
| 新しい標本 30 | 30 | 3,923 | 0 | 30 |

九十七書類を `verify_document(zb, None, None)`(既定)と `verify_document(zb, "P26", None)` で検証し、`sort_keys` の JSON の字を比べた。対照は `vocabulary.DEFAULT_PROFILE` を実行中だけ P22 に戻した同じ比較で、`profile` の欄が変わるので全書類が違う。

### 2-2 S-2・S-3: 四 state と P22 からの動き

| 標本 | profile | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND |
|---|---|---|---|---|---|
| 手元の 67 | P22 | 4242 / 7799 = 54.4% | 1410 / 7799 = 18.1% | 1323 / 7799 = 17.0% | 824 / 7799 = 10.6% |
| 手元の 67 | 既定(P26) | 4371 / 7799 = 56.0% | 433 / 7799 = 5.6% | 1579 / 7799 = 20.2% | 1416 / 7799 = 18.2% |
| 新しい標本 30 | P22 | 2142 / 3923 = 54.6% | 677 / 3923 = 17.3% | 690 / 3923 = 17.6% | 414 / 3923 = 10.6% |
| 新しい標本 30 | 既定(P26) | 2194 / 3923 = 55.9% | 250 / 3923 = 6.4% | 774 / 3923 = 19.7% | 705 / 3923 = 18.0% |

既定(P26)と P22 で state の違う行は、手元の六十七書類で 千百四十九・新しい標本の三十書類で 五百七。 手元の六十七書類で P22 の GROUNDED を離れる行は 十九(うち VALUE_MISMATCH に移る行 七)、新しい GROUNDED になる行は 百四十八。

| 標本 | 向き(P22 → 既定) | 行 |
|---|---|---|
| 手元の 67 | GROUNDED → UNVERIFIABLE | 12 |
| 手元の 67 | GROUNDED → VALUE_MISMATCH | 7 |
| 手元の 67 | POINTER_NOT_FOUND → GROUNDED | 5 |
| 手元の 67 | POINTER_NOT_FOUND → UNVERIFIABLE | 2 |
| 手元の 67 | UNVERIFIABLE → GROUNDED | 131 |
| 手元の 67 | UNVERIFIABLE → VALUE_MISMATCH | 4 |
| 手元の 67 | VALUE_MISMATCH → GROUNDED | 12 |
| 手元の 67 | VALUE_MISMATCH → POINTER_NOT_FOUND | 599 |
| 手元の 67 | VALUE_MISMATCH → UNVERIFIABLE | 377 |
| 新しい標本 30 | GROUNDED → UNVERIFIABLE | 2 |
| 新しい標本 30 | GROUNDED → VALUE_MISMATCH | 5 |
| 新しい標本 30 | POINTER_NOT_FOUND → GROUNDED | 5 |
| 新しい標本 30 | POINTER_NOT_FOUND → UNVERIFIABLE | 1 |
| 新しい標本 30 | UNVERIFIABLE → GROUNDED | 54 |
| 新しい標本 30 | UNVERIFIABLE → VALUE_MISMATCH | 4 |
| 新しい標本 30 | VALUE_MISMATCH → POINTER_NOT_FOUND | 297 |
| 新しい標本 30 | VALUE_MISMATCH → UNVERIFIABLE | 139 |

### 2-3 S-4: 儀式(同梱の一書類)

| 儀式(同梱の 1 書類) | 通した | 止めた(VALUE_MISMATCH) | 止めた(POINTER_NOT_FOUND) | 注入の対象 |
|---|---|---|---|---|
| P22(`ritual_2026-10-20_p22.json`) | 15 / 240 = 6.2% | 225 / 240 = 93.8% | 0 | 240 |
| 既定(P26。`ritual_2026-10-20.json`) | 2 / 243 = 0.8% | 210 / 243 = 86.4% | 31 | 243 |

買い手が clone して走らせるのは今の既定である。`fixtures/xbrl/ritual_2026-10-20.json` と README の儀式の節は P26 で採り直し、P22 のときの記録は同じバイト列の写し `fixtures/xbrl/ritual_2026-10-20_p22.json` と履歴に残した(結果文書 `docs/XBRL_RITUAL_RESULT_2026-10-20.md` は末尾に日付つきの追記)。

### 2-4 S-5: 報告形

| 報告形の節(67 書類) | 件 |
|---|---|
| 違う | 433 |
| 要確認 | 1,775 |
| 対象外 | 151 |
| 判断しない | 1,069 |
| 一致 | 4,371 |
| 合計 | 7,799 |

「違う」の節は VALUE_MISMATCH の行と同じ数である。報告形の節の割り当ては変えていない。

### 2-5 S-6: 誤りを通す側

| 誤りを通す側 | 既定 | P22 明示(対照) |
|---|---|---|
| 穴 B の注入 485 件で通した | 0 / 485 = 0.0% | 1 / 485 = 0.2% |
| 穴 B の注入で止めた(VALUE_MISMATCH) | 480 | 482 |
| 段 2 の材料の注入 64 件で Core 自身が GROUNDED | 0 / 64 = 0.0% | (測っていない) |

誤りを通す側は、穴 B の注入四百八十五件で既定が通した数が 零・段 2 の材料の注入六十四件で Core 自身が GROUNDED にした数が 零。 P26 を明示して測った記録(`fixtures/xbrl/p26_2026-10-21.json`)の P26 の欄と一行ずつ比べて違った行は零だった。新しい標本の注入で通した五件(封 §0)は、この測定では測り直していない。

### 2-6 S-7: engine の差分

engine の差分は `vocabulary.py` の挿入 四 行・削除 一 行だけ。 `core/` と、`vocabulary.py` 以外の `adapters/xbrl` の file は封の commit から零行。束ねた指紋 `adapter_xbrl_py_sha256` と frozen_bundle の世代は動き、`adapter_xbrl_py_files`・`core_py_sha256`・frozen_bundle の本数は動かない(pin の遷移は封 §4 の一覧のとおり宣言した)。

覆い(S-11): 試験 file はディスク上で 二百二十二本。

## 3. 試験の赤(S-8・S-9)

S-8・S-9 の数は**試作の clone の実測**で、人が書いた表(記録は入力の file の sha256 を持つ)から写した。門が縛るのは表の内訳の足し算と封の幅との当たり外れだけで、赤の中身が本当にその種類かは門の外である。

| 試作の clone(`DEFAULT_PROFILE` の 1 行だけ P26)の赤 | 本 | file |
|---|---|---|
| `tests/measure` | 68 | 25 |
| `tests/adapters/xbrl` | 15 | 10 |
| 種類 1 | 40 |  |
| 種類 2 | 13 |  |
| 種類 3 | 18 |  |
| 種類 4 | 12 |  |

既定の一行だけを替えた clone の赤は、`tests/measure` が 六十八本(二十五 file)・`tests/adapters/xbrl` が 十五本。 封の予測は `tests/measure` が 六十六本(二十四 file)・`tests/adapters/xbrl` が 十五本。実測との差のうち、封の commit で足された `test_xbrl_default_p26_seal.py` の赤は 二本(封の試作の clone にはこの file が無かった)。`tests/core` の赤は 零本。 重い走らせ直しで軽い門の赤のほかに増えた赤は 六本。

実装の後(凍結した file を当てた clone)の重い走らせ直し:

| 実装の後の重い走らせ直し(環境変数) | 赤 | うち段 2 の前から赤 |
|---|---|---|
| `AUDIT_CORE_CUSTOMER_REPORT` | 1 | 1 |
| `AUDIT_CORE_CUSTOMER_REPORT_FIX` | 1 | 1 |
| `AUDIT_CORE_DEFAULT_P26` | 0 | 0 |
| `AUDIT_CORE_FRESH` | 0 | 0 |
| `AUDIT_CORE_LASTBRANCH` | 0 | 0 |
| `AUDIT_CORE_P26` | 0 | 0 |
| `AUDIT_CORE_PERIOD_BIND` | 1 | 1 |
| `AUDIT_CORE_POINT_PRIOR` | 0 | 0 |
| `AUDIT_CORE_RITUAL` | 0 | 0 |
| `AUDIT_CORE_ROUNDING` | 0 | 0 |
| `AUDIT_CORE_VOCAB` | 0 | 0 |

実装の後の重い走らせ直し 十一本の赤は 三本。うち、何も変えない clone(`6a78b42`)で同じ環境変数を付けて走らせても赤だった(段 2 の前から赤)が 三本、段 2 が原因の赤は 零本。封の S-9 の『実装の後は全部緑』は外れ。 何も変えない clone と段 2 の clone で、報告形の走らせ直しの出力は 四欄・報告形の直しの出力は 四欄・期の縛りの段 2 の出力は 三欄だけ違った。違った欄はどれも既定・HEAD・`vocabulary.py` の sha・束ねた指紋の欄だけで、測った値の欄は一字も違わない。

段 2 の実装の後は、赤になっていた門に宣言された遷移(測った当時の値は残し、後の値を足す)を入れ、既定の字を見る試験は P26 に直し、既定を前提に記録を再現する measure は測った当時の P22 を明示して固定した。記録(fixtures)の数・state を書き換えないと緑にならない門は零で、儀式の記録だけは買い手が今の既定で走らせるものなので採り直した(S-4)。

## 4. 代価と限界

- 封 §3 の代価と限界はそのまま。この測定は測り直していない: K-3 の読みの転び方、P22 で GROUNDED の行が P26 で VALUE_MISMATCH になる比率の主張、「違う」が「要確認」に移ること、注入で通した五件の原因を調べていないこと。
- この測定が確かめたのは**既定の配線**(profile を省いた経路が P26 明示と同じ出力を返すこと)と、その結果として既定の数が P26 明示の記録と同じであること。P26 の効き目は P26 を明示した記録(`p26_2026-10-21.json`・`fresh/fresh_2026-10-21.json`)が測った。
- 読み(正しい文かどうか)は測っていない。
- 席(LLM)は呼んでいない。通信はしていない。新しい標本の ZIP は `~/.cache/audit-core/edinet-fresh-2026-10-21/`、手元の六十七書類は `~/.cache/audit-core/edinet/` から読み、どちらにも 一 file も足していない(件数を測定の前後で数えて記録に残した)。
- 実装の後も赤が残る重い走らせ直し(報告形・報告形の直し・期の縛りの段 2)は、何も変えない clone でも同じ赤だった。P26 の段 1 が動かした登録簿の字・`recipes.py` の sha16・engine の指紋を、記録が測った時点の値と突き合わせているために赤い(これはエージェントの読み)。上の『出力の差』のとおり、段 2 の clone と何も変えない clone の出力は、既定・HEAD・`vocabulary.py` の sha・束ねた指紋の欄のほかは違わないので、段 2 はこの赤を増やしていない。直すか(測った当時の値を宣言された遷移として受け入れる)は封の範囲の外なので触っていない。人間か司令塔が別便で決める。
- **HUMAN の残り一点(変わらず)**: `adapters/xbrl/verify_document.py` の docstring「`--profile` を省くと `vocabulary.DEFAULT_PROFILE`(= P20)」は、既定 P26 と食い違う(P20・P21・P22 に続き四つめ)。engine の file なので触っていない(一行の承認と、`verify_document.py` の sha16 を留める門の遷移が要る)。

## 5. 再現

```
cd audit-core
python3 measure/xbrl_default_p26_2026-10-23.py --stage all --out <出力先> --reds <試験の赤の表>
python3 -m pytest -q tests/measure/test_xbrl_default_p26_result.py
AUDIT_CORE_DEFAULT_P26=1 python3 -m pytest -q tests/measure/test_xbrl_default_p26_result.py     # 全部の走らせ直し
```

軽い走らせ直し(手元の cache の二書類)は既定で走る。全部の走らせ直し(`AUDIT_CORE_DEFAULT_P26=1`)は九十七書類・注入・報告形を回す。
