# 封: 評価用・調整用 P27 の注入で「差し替えが基準の claim に届いたか」を数える診断 ― 2026-10-29

**人間(2026-10-29)「確かめていいよ 君に任せる」。** 総点検の封 `docs/XBRL_INJECT_HARNESS_REVIEW_SEAL_2026-10-29.md`(`365b468`)の §6-4 の 4・§6-5 の 5 が残した便。**診断だけ。engine(`core/`・`adapters/`)は 0 行。既存の記録 `fixtures/xbrl/p27/eval_inject_2026-10-27.json`・`tune_inject_2026-10-27.json`・`tune_p27_inject_2026-10-27.json` は書き換えない(別の記録を足す)。直すなら別の封。** 0 USD・通信なし・席(LLM)は呼ばない。人間は、評価用 10 社と調整用 10 社の文を script に読ませて注入を走らせ直すことを許した(席も司令塔も文を開かない。§2-5)。
作法は変えない(封 → 測定 → 凍結 → 独立監査 GO → commit)。数を見てから封・予測を直さない。外れは外れとして残す(補足は日付つきの追記)。

- 封の時点: branch `feature/audit-core-final-eval-8`、HEAD `365b468`、`vocabulary.DEFAULT_PROFILE = "P27"`(`6a34db5`)。
- この封は docID・claim の id を書かない。書類は「評価用の n 番目」「調整用の n 番目」(記録 `fixtures/xbrl/p27/reports_2026-10-27.json` の `会社` の区分ごとの並び)か集計で呼ぶ。理由は前の便と同じ(引きの門 `tests/measure/test_xbrl_fresh_seal.py` は `LATER_NAMING_FILES` の外の追跡 file に docID が出ると赤になる。評価用・調整用の docID も外に出さない)。
- 前例の型: 封 `docs/XBRL_INJECT_REACH_DIAG_SEAL_2026-10-28.md`(`df5c215`。§0 の問い・§2 の配線の門と観測の欄・§2-3 の分類 6 語・§3 の欄ごとの予測・§6 の下調べ)と、その script `measure/xbrl_inject_reach_2026-10-28.py`・門 `tests/measure/test_xbrl_inject_reach.py`。

## §0 根拠(この封は新しく測らない。数は既存の記録と code から引く)

### §0-1 問い

評価用 96 行(T1_VALUE 7・T8_REL 89)と調整用 101 行(T1_VALUE 11・T8_REL 90。`tune_inject` の P22・P26 と、同じ 101 行を 4 profile で測り直した `tune_p27_inject` の P27・P27E)で、profile ごと(P22・P26・P27・P27E)に:

1. **注入後に数えた claim の id が、基準の claim の id と同じ行は何行か**(違う行・対応が付かない行)。
2. 前の便と同じ定義(engine の文の一覧の差で token の文を決め、基準の claim の文と比べる)で、**届いた(文)・届いた(数)は何行か。** 分類 6 語(前の便の封 §2-3。この封の §2-3)で。
3. 記録の「通した」(評価用 P22 27・P26 27、調整用 P22 28・P26 28)と「名指したが別の値」(評価用 P22 7・P26 5・P27 5・P27E 7、調整用 4・4・7・9)のうち、**届いていない行は何行か。**
4. **読み直した率**(届いた行だけを分母に)を、元の率と並べて 2 本。とくに評価用 T8_REL の通した率・名指して原本の値を返した率(P26・P27・P27E)。

評価用の帯の数(T8_REL の通した P26 27 / 87 = 31.0% → P27 0、名指して原本の値を返した P26 41.4% → P27 31.0%、P27E 89.7%)は台帳 `docs/FACTS_FOR_BUYERS_2026-10-20.md` の D-22・D-23 にあり、人間が外に出した紙(Cabocia への技術概要。repo には無い。依頼文の字)にも載った。この仕掛けの数で、確かめの対象である。**紙と台帳の字を直すかは、診断の後で人間が決める(この便では直さない)。**

### §0-2 記録の数(封を書く席が記録から数え直した。結果文書の字と一致)

- 評価用 `eval_inject`: 行 96(T1_VALUE 7・T8_REL 89)、10 書類のうち行を持つ書類 10(行の数 1〜19)。文体 A 47・B 26・C 23。4 profile の全部で対応が付く行 T1_VALUE 7・T8_REL 87。対応が付かない行は T8_REL の 2 行で、**4 profile で同じ 2 行**。round-trip を確かめた注入 113(採った T1_VALUE 24・T8_REL 89)。
- 調整用 `tune_inject`(P22・P26)と `tune_p27_inject`(P22・P26・P27・P27E): 同じ 101 行(T1_VALUE 11・T8_REL 90)、10 書類のうち行を持つ書類 9(調整用の 7 番目は 0 行)。文体 B 55・A 27・C 19。対応が付かない行は T1_VALUE 1・T8_REL 2 で、**4 profile で同じ 3 行**。`tune_p27_inject` の U-1: `tune_inject` と P22・P26 の分類(対応・結果・state・reason)が違う行 0 / 101。採った T1_VALUE 32・T8_REL 90(round-trip を確かめた注入は 122 になるはず。記録に round-trip の欄は無い)。
- 書類別の数えの合計(評価用): T1_VALUE 作れる site 24・採った 24・両方 GROUNDED 7・どちらも GROUNDED でない 10・基準に対応が付かない 7。T8_REL 円族の token 186・両方 GROUNDED 90・どちらも GROUNDED でない 91・基準に対応が付かない 5・r が決まらず site にしない 1・作れる site 89・採った 89。調整用: T1_VALUE 32・32・11・16・5。T8_REL 198・94・103・1・4・90・90。
- 結果の語の数(評価用。全部の行):

| 型 | P22 | P26 | P27 | P27E |
|---|---|---|---|---|
| T1_VALUE 7 | 名指して原本の値を返した 7 | 名指して原本 7 | 名指して原本 5・止めたが名指さない(POINTER_NOT_FOUND)2 | 名指して原本 5・PNF 2 |
| T8_REL 89 | 名指して原本 53・通した 27・名指したが別の値 7・対応が付かない 2 | 名指して原本 36・通した 27・PNF 19・名指したが別の値 5・対応が付かない 2 | PNF 55・名指して原本 27・名指したが別の値 5・対応が付かない 2 | 名指して原本 78・名指したが別の値 7・PNF 2・対応が付かない 2 |

- 結果の語の数(調整用。`tune_p27_inject`):

| 型 | P22 | P26 | P27 | P27E |
|---|---|---|---|---|
| T1_VALUE 11 | 名指して原本 10・対応が付かない 1 | 名指して原本 8・PNF 1・UNVERIFIABLE 1・対応が付かない 1 | 名指して原本 5・PNF 4・UNVERIFIABLE 1・対応が付かない 1 | 名指して原本 7・PNF 2・UNVERIFIABLE 1・対応が付かない 1 |
| T8_REL 90 | 名指して原本 56・通した 28・名指したが別の値 4・対応が付かない 2 | PNF 34・通した 28・名指して原本 19・名指したが別の値 4・UNVERIFIABLE 3・対応が付かない 2 | PNF 60・名指して原本 19・名指したが別の値 7・UNVERIFIABLE 2・対応が付かない 2 | 名指して原本 75・名指したが別の値 9・PNF 2・UNVERIFIABLE 2・対応が付かない 2 |

- 元の率(T8_REL。分母 = 4 profile の全部で対応が付く行。評価用 87・調整用 88。記録の対応が付かない行は 4 profile で同じなので、profile ごとの分母とも同じ): 評価用 通した P22 27(31.0%)・P26 27(31.0%)・P27 0・P27E 0、名指して原本の値を返した P22 53(60.9%)・P26 36(41.4%)・P27 27(31.0%)・P27E 78(89.7%)、名指したが別の値 7・5・5・7。調整用 通した 28(31.8%)・28(31.8%)・0・0、名指して原本 56(63.6%)・19(21.6%)・19(21.6%)・75(85.2%)、名指したが別の値 4・4・7・9。T1_VALUE は通した 0(両方の組・4 profile)、名指して原本 評価用 7・7・5・5 / 7、調整用 10・8・5・7 / 10。
- 「通した」の行は P22 と P26 で同じ行(評価用 27 行・調整用 28 行)。P27 ではその行が、評価用 POINTER_NOT_FOUND(no_same_value)18・VALUE_MISMATCH 9、調整用 POINTER_NOT_FOUND(no_same_value)15・VALUE_MISMATCH 11・UNVERIFIABLE(target_or_plan)2 に移る。
- 「名指したが別の値」の行の重なり(4 profile の結果の組): 評価用 4 profile とも 5 行・P22 と P27E だけ 1 行・P22 だけ 1 行・P27E だけ 1 行。調整用 4 profile とも 4 行・P27 と P27E だけ 3 行(うち P22・P26 で通した 2 行)・P27E だけ 2 行。
- 基準の claim(判定の記録 `eval_2026-10-27.json`・`tune_p27_2026-10-27.json` の `claim` と docID・id で引いた): 評価用 相異なる 93(2 行以上が同じ claim を基準にする claim 3・その行 6、3 つとも T1_VALUE と T8_REL の両方の基準)、kind・form は num・direct_value 93 行・num・derived_value 3 行。調整用 相異なる 94(同 7・14、7 つとも両方の型)、direct_value 100・derived_value 1。**無改変の基準の state は、P22・P26 は全行 GROUNDED(土台の条件)。P27・P27E では評価用 1 行・調整用 2 行が UNVERIFIABLE**(その 3 行は全部、P22・P26 で通した行)。調整用の 2 行は注入後の P27・P27E も UNVERIFIABLE(無改変と同じ state)、評価用の 1 行は注入後の P27・P27E が POINTER_NOT_FOUND(無改変と違う state)。
- 無改変の判定の記録での profile の移り: 評価用 P26 → P27 で GROUNDED を離れた claim 1 / 523、調整用 2 / 534。新しい GROUNDED は両方 0。4 profile で claim の id の並びは同じ(調整用は `tune_p27` の測定が確かめて止める作り)、値・span・単位が P22 と違う id は両方 0。

### §0-3 対応の付け方(`measure/xbrl_p27_tune_2026-10-27.py` を読んで確かめた)

- **土台 `base_status` は code の字のとおり「無改変で P22 と P26 の両方が GROUNDED」。** `find_base_claim(base_claims["P22"], tok.value, digits, tok.unit)` が 1 件に決めた claim について、P26 の同じ id の claim の (value・span・unit) が同じで、P22・P26 の state が両方 GROUNDED のときだけ土台にする(片方だけなら `P22 のみ GROUNDED`・`P26 のみ GROUNDED`、どちらも違えば `どちらも GROUNDED でない`、id が無いか値・span・単位が違えば `profile 間で claim が合わない`)。**P27・P27E の無改変の state は土台の条件に入らない**(§0-2 の 3 行がその例)。
- `find_base_claim`(基準): 値 = token の値を `SC.scaled_value` で円に直した数、字 = 本文の token の字(`text[tok.start:tok.end]`)。「値が `same_number` で一致し、span に字を含む claim」が 1 件ならそれ(**値と字**)、1 件でなければ「値が一致する claim」が 1 件ならそれ(**値だけ**)、それ以外は None(行にしない。`基準に対応が付かない`)。
- `claim_for_p27`(注入後): 値 = `inj["new_value"]` を token の単位で円に直した数、字 = `inj["replacement"]`。同じ順(値と字 → 値だけ → None)。**返した claim の id が基準の claim の id と同じかは見ない。** 前の便の `claim_for`(`a_core_vs_grep`)と違い、値は円に直して比べる(前の便の script の `after_match` は円に直さないので、この便では使えない)。
- `classify(res, base)`: res が None なら `対応が付かない`。state が GROUNDED なら `通した`、VALUE_MISMATCH なら、pointers の先頭が土台(同じ profile の無改変の、**基準の claim の id** の claim)の先頭と同じで recomputed が土台と同じとき `名指して原本の値を返した`、そうでなければ `名指したが別の値`。POINTER_NOT_FOUND・UNVERIFIABLE は「止めたが名指さない」。**res の id は見ない。**
- 新しい値の選び方: T1_VALUE は `inject.build_t1`(元の値 ± 差の小さい候補のうち refs の値に無いもの)。T8_REL は `pick_r`(r ∈ ±0.03・±0.10、書かれた桁に丸め、元の値と同じか refs のどれかの値と同じなら 4 回まで引き直す)。**どちらも「新しい値は refs に無い」で、注入後の対応付けは新しい値で claim を引く**ので、差し替えた token を読んでいない claim が引かれるのは、別の claim が偶然その新しい値を持つときに限られる(と code からは読める。測ってはいない)。前の便の T2_UNIT(数を変えない差し替え)は値が同じなので、値だけに落ちると別の claim を引いた。この便の 2 型はそこが違う。

### §0-4 走らせ直しの経路(code を読んで確かめた)

- 評価用の script の `run_inject` は `preflight` を通る。`preflight` は **`V.DEFAULT_PROFILE == "P26"` と、E(`b2c3f56`)と HEAD の間で `adapters`・`core` に差が無いこと**を求める。HEAD では `DEFAULT_PROFILE = "P27"` で、`6a34db5` が `adapters/xbrl/vocabulary.py`(既定の profile の 1 行と注記)と `adapters/xbrl/verify_document.py`(docstring の 1 行)を変えたので、**`run_inject` はいまは走る前に止まる。** だからこの便の script は `run_inject` を呼ばず、評価用の script の `EvalCtx`(評価用だけを通す guard と sha256 の照合)と段 1 の script の `inject_doc` を直接呼ぶ(§2-1)。`6a34db5` の engine の差は、profile を明示した呼び出しの振る舞いを変えない字の差である(`git show 6a34db5 -- audit-core/adapters` の字で確かめた。測ってはいない ― 配線の門が測る)。
- `RealBackend`(段 1 の script)は手元の engine: `adapters.xbrl.verify_document.verify_document`・`adapters.xbrl.instance.load_instance`・`measure/prepare_material.prepare_xbrl`。この 3 つの経路に通信は無い(`adapters/xbrl/` で通信の字を持つのは `edinet.py` の `fetch` だけで、`verify_document`・`instance` は `edinet` の取得を呼ばない。`prepare_material.py` は `urllib` を import しない)。鍵は読まない。
- 材料の置き場(code と記録から): ZIP は `~/.cache/audit-core/edinet-fresh-2026-10-21/<docID>.zip` を**読むだけ**(sha256 を取得の記録 `fixtures/xbrl/fresh/fetched_2026-10-21.json` と照らす)。文は `~/.cache/audit-core/edinetdb-p27/reports/<docID>.txt`(sha256 を W の記録 `reports_2026-10-27.json` の `文の sha256` と照らす)。**注入の経路は DB の応答を開かない**(`inject_doc` は `read_db` を呼ばない)。refs は `prepare_xbrl` が作業 folder(TMPDIR の下)に書く `<docID>.reference_numbers.json` から。
- 文の番号の求め方: 前の便の `xbrl_lastbranch_2026-10-21.py` の `_RawTap` + `verify_raw(tap, zb, prof, text)` は `VD.verify_document(zb, prof, text)` をそのまま呼び、`recipes._member_material` に渡る文の一覧と、`_build_raw_num_claims`・`_build_raw_text_claims` の出力(claim ごとの `sentence`・`pos`)を取る。`verify_document` は text を渡されると `build_modified_zip` で文を ZIP の本文の block に入れ、`build_raw_claims` がその block から文の一覧を作る。**だから外から渡した文でも同じ求め方が使える**(code で確かめた。動くかは §6 の下調べで見る)。`diff_sentence`・`claims_in_sentence`(`xbrl_t2_pass_diag_2026-10-28.py`)と `num_span`(`xbrl_inject_reach_2026-10-28.py`)はそのまま使える。

### §0-5 封を書く前に見たもの(予測の偏りの出どころ)

- 記録: `eval_inject`・`tune_inject`・`tune_p27_inject`(行・書類別の数え・U-1・round-trip・engine の指紋)、`eval_2026-10-27.json`・`tune_p27_2026-10-27.json`(`claim` の 4 profile の state・`集計`・`会社` の id の差)、`reports_2026-10-27.json`(区分・型・並び)、`fetched_2026-10-21.json`(書類の bytes)。§0-2 の数はここから。
- code: `xbrl_p27_tune_2026-10-27.py` の全部、`xbrl_p27_eval_2026-10-27.py` の全部、`xbrl_p27_tune_rerun_2026-10-27.py` の全部、`xbrl_inject_reach_2026-10-28.py` の全部、`xbrl_t2_pass_diag_2026-10-28.py` の `after_match`・`number_text`・`diff_sentence`・`claims_in_sentence`、`xbrl_lastbranch_2026-10-21.py` の `_RawTap`・`verify_raw`、`inject.py` の `build_t1`、`lib/sites.py` の `_value_index`・`_matches`、`xbrl_p27_dbfetch_2026-10-27.py` の置き場の関数、`adapters/xbrl/verify_document.py` の `verify_document` の頭、`adapters/xbrl/recipes.py` の `build_raw_claims`(文の一覧と claim の `sentence`・`pos` の出どころだけ)。比べる側の分岐(`resolve.py`・`comparators.py`)は読んでいない。
- 文書: 前の便の封と診断の字(§0-1 の引用の範囲)、総点検の封 §6-4・§6-5、`XBRL_P27_RESULT_2026-10-27.md` の「通した」の行(T8_REL の通した行が P27・P27E で無くなったのは「A(書かれた桁で照合)の効きと見るが、行を 1 つずつ読んでおらず」)、台帳 D-22・D-23。
- **評価用・調整用の文・DB の応答・指示文は開いていない。** 注入の token の位置・文の番号・注入後の claim の id は、予測を固定する前には見ていない(下調べは §3 を書いた後。§6)。

## §1 既存の記録で足りないこと(先に確かめた)

記録 `eval_inject`・`tune_inject`・`tune_p27_inject` の 1 行が持つ欄は `docID`・`id`・`型`・`文体`・`基準の claim`・(T8_REL は)`r`・`r を決めた回`と、profile ごとの `対応`・`結果`・`state`・`reason` だけ。**無い欄**:

1. **注入後に数えた claim の id**(`claim_for_p27` が返した claim の id)と、それが基準の claim の id と同じか。
2. 差し替えた token がある**文の番号**(engine の文の一覧の中の番号)と、文の中で最初に違う位置。
3. **基準の claim の文の番号と文の中の位置**(`_RawTap` が返す `sentence`・`pos`)と、数の字の始まり・終わり(整数)。
4. **対応の付け方**(無改変の `find_base_claim` が値と字で決めたか値だけに落ちたか。注入後の `claim_for_p27` も同じ)。
5. 注入後の claim の state が、無改変の同じ id の claim の state と同じか。注入後の pointers の有無と、先頭が基準(同じ profile の無改変)の先頭と同じか。
6. 書類ごとの文の数(profile ごと)。

だから、診断用の記録を 1 本足す。engine には触らない。既存の記録は書き換えない。

## §2 測り方(script `measure/xbrl_p27_inject_reach_2026-10-29.py` の仕様)

### §2-1 配線は測定の script と同じ(門で示す)

- **関数は写さず import する。** 評価用の script `xbrl_p27_eval_2026-10-27.py` を importlib で 1 回読み(module E)、**E が読んだ段 1 の module(`E.T`)を、評価用と調整用の両方の唯一の T とする**(module の差し替えは使う側の実体に届かないと黙って効かない ― 別に読んだ T に当てた差し替えは `E.T.inject_doc` に届かない)。`E.T.PROFILES = ("P22", "P26", "P27", "P27E")`(評価用の script と調整用 P27 の script と同じ形)。調整用 P27 の script `xbrl_p27_tune_rerun_2026-10-27.py` は定数(`PROFILES4`・記録の path)のために読み、`PROFILES4 == E.PROFILES` と、その script が読んだ段 1 の file の sha256 が `E.T` の file と同じことを確かめる(違えば止める)。
- 評価用: `E.EvalCtx`(評価用の 10 件だけを通す guard。調整用・区分の外の docID はどの file も開く前に止める)で、`load_materials(db=False)` を 10 書類の全部に当て、文と ZIP の sha256 を全部照らしてから注入に入る(評価用の script の `run_inject` と同じ順)。`E.preflight` は呼ばない(§0-4。代わりに §2-5 の engine の確かめ)。
- 調整用: `E.T.Ctx`(調整用の 10 件だけを通す guard)。
- 注入: `E.T.inject_doc(ctx, backend, doc, seed, work, E.T.INJECT_CAP)` を書類ごとに呼ぶ。**注入の規則・site・土台・対応付け・分類を自分で書かない。** 種は `measure/SEED.json`(`IJ.verify_seed_sealed`)。`inject_doc` が返す外に置く行(元の字・後の字・新しい値)は**捨てる**(書かない・印字しない。この便は外の置き場にも何も足さない)。
- **包む 2 か所**(観測のため。返り値は変えない):
  1. backend: `E.T.RealBackend` を継ぎ、`verify(zb, profile, text)` だけを `LB.verify_raw(tap, zb, profile, text)`(`_RawTap` の中)に替える。返すのは `verify_raw` が `VD.verify_document` から受け取った出力の object そのもの。claim の一覧の object の `id()` を鍵に、その呼び出しの profile・文の一覧・claim ごとの `sentence`・`pos` を process の中に持つ(記録には文を書かない)。
  2. `E.T.claim_for_p27`: module の属性を包みに替える。包みは本物を呼び、返り値の object をそのまま返し(`is` で確かめる)、(注入の id・claim の一覧の `id()`・返した claim の id)を残す。終わったら属性を戻し、戻ったことを `is` で確かめる。
  - **包みの門**: (i) 作り物の backend(段 1 の `StubBackend`)と試験の材料で、包んだときと包まないときの `inject_doc` の返り値(行・外の行・数え)が JSON の byte で同じ(門 (g) の 1 本)。(ii) 本番では、包みの呼ばれた回数 = 対応を数えた行 × 4 profile、claim の一覧の `id()` が全部 backend の控えに在る(無ければ止める)。
- **配線の門**: 走らせ直した行が、既存の記録の同じ (docID, id) の行と、`型`・`文体`・`基準の claim`・(T8_REL は)`r`・`r を決めた回`・profile ごとの `対応`・`結果`・`state`・`reason` で**全行**一致すること。照らす記録は、評価用は `eval_inject`(4 profile)、調整用は `tune_p27_inject`(4 profile)と `tune_inject`(P22・P26)の両方。(docID, id) の集合が記録と同じこと。`書類別の数え` が書類 × 型(評価用 10 × 2・調整用 10 × 2)で記録と辞書ごと同じこと(調整用は 2 本の記録の両方と)。round-trip を確かめた注入の数(採った数の合計)が評価用 113・調整用 122 で、評価用は記録の `round-trip` の数と同じこと。**1 つでも違えば記録を書かずに止める。** 調整用を先に走らせて門を当て、通ってから評価用を開く(調整用で止まれば評価用の文は開かない)。
- 書類ごとに別の process で走らせてよい(段 1 の `run_parallel` と同じ fork)。出力が既に在れば測り直さない。`--set tune` と `--docs n`(調整用の先頭 n 書類。scratchpad の出力へ)は試し。**評価用は `--docs` を受け付けない**(評価用は全 10 書類を本番の 1 回だけ走らせる。下調べでも走らせない)。

### §2-2 観測する欄(行ごと・profile ごと。全部 engine の出力から機械で取る)

| 欄 | 出どころ |
|---|---|
| 注入後の claim の id | 包み 2 が残した、本物の `claim_for_p27` の返り値の `id`(None なら対応が付かない) |
| 注入後の id が基準の claim の id と同じ | 上の id と記録の `基準の claim` の字の比較 |
| 基準の対応の付け方(P22 の無改変。値と字 / 値だけ) | `find_base_claim` と同じ順で、どの枝で 1 件に決まったかだけを返す関数(値は `E.T.scaled`・`E.T.claim_scaled`・`E.T.same_number` を使う)。**指す claim の id が行の `基準の claim` と同じでなければ止める** |
| 注入後の対応の付け方(値と字 / 値だけ) | `claim_for_p27` と同じ順で枝だけを返す関数。**指す claim の id が本物の返り値と同じでなければ止める** |
| 基準の claim の文の番号・文の中の位置 | その profile の無改変の控えから、記録の `基準の claim` の id で引いた `sentence`・`pos` |
| 基準の claim の数の始まり・終わり(文の中の整数) | `num_span`(前の便の script)。字は持たない |
| token の文の番号・文の中で最初に違う位置 | `diff_sentence(無改変の文の一覧, 注入後の文の一覧)`(同じ profile)。None = **文が 1 つに決まらない** |
| 文の数(無改変, 注入後) | 控えの文の一覧の長さ |
| 注入後の claim の文の番号 | 注入後の控えから、注入後の claim の id で引いた `sentence` |
| **届いた(文)** | token の文の番号 = 基準の claim の文の番号 |
| **届いた(数)** | 届いた(文)かつ、最初に違う位置が数の始まりから「終わり + 2」の中(前の便と同じ) |
| state・reason・結果 | `inject_doc` の行の profile の欄(本物の `classify`)をそのまま |
| 注入後の state が無改変の同じ id の state と同じ | 無改変の控えの claim 一覧から注入後の id で引く |
| 注入後の pointers の有無・先頭が基準(同じ profile の無改変)の先頭と同じ | 旗だけ(pointers の字は持たない) |
| 分類・細目 | §2-3 |

書類ごと: 文の sha256(W の記録と一致)・ZIP の sha256(取得の記録と一致)の旗、`書類別の数え`、配線の門の旗、claim の数と文の数(4 profile)、秒。記録の頭: HEAD、`DEFAULT_PROFILE`、engine の sha16(前の便と同じ 6 本)と `VD.engine_fingerprint()`、種、読んだ入力の sha256(`eval_inject`・`tune_inject`・`tune_p27_inject`・`eval_2026-10-27.json`・`tune_p27_2026-10-27.json`・`reports_2026-10-27.json`・`fetched_2026-10-21.json`・`dbfetch_2026-10-27.json`)、cache の件数(開始時・終了時。`edinet/` と `edinet-fresh-2026-10-21/` だけ)と段 1 の `cache_snapshot`(同じ 2 つの folder の件数と名前の一覧の sha256)。

### §2-3 分類(機械で 1 か所。§3 の予測はこの語で書く)

行ごと・profile ごとに、上の欄から次の順で 1 つに決める(先に当たったものを取る。前の便の封 §2-3 と同じ語):

1. **(対応が付かない)**: 注入後の claim が None。
2. **(文が 1 つに決まらない)**: token の文が None。
3. 届いた(文)なら、state が GROUNDED のとき **(届いた・通した)**、それ以外は **(届いた・止めた)**。
4. 届いていないなら、state が GROUNDED のとき **(届かない・通した)**、それ以外は **(届かない・止めた)**。

細目(記録に持つが順には入れない): 届いた(文)の行を「数の位置が合う」と「同じ文・別の数」に分ける。届かない行を「注入後の claim が基準と別の id」「同じ id・state が無改変と違う」「同じ id・state も無改変と同じ」に分ける。

「名指して原本の値を返した」「名指したが別の値」などの結果の語(本物の `classify`)は分類とは別の欄に並べ、問い 3 は「結果の語 × 分類」の表で答える。**型の意味(なぜそうなるか)は診断の文書の仮説の節に書き、記録には書かない。**

### §2-4 読み直し(診断の文書に日付つきで書く表。既存の記録は不変)

組(評価用・調整用)× 型 × profile ごとに: 行・対応が付く・id が同じ・届いた(文)・届いた(数)・届かない・決まらない、分類 6 語の数、結果の語 × 分類。率は**分母を書いて** 2 本並べる:

- **元の率**: 分母 = 4 profile の全部で対応が付く行(評価用 T8_REL 87・T1_VALUE 7、調整用 88・10。§0-2)。記録の数のまま。
- **読み直した率**: 分母 = 元の分母の行のうち、**4 profile の全部で (届いた・止めた) か (届いた・通した) の行**(profile の間で同じ行を比べるため)。分子は同じ行の中の結果の語。

外に出した紙の 5 つの数(評価用 T8_REL の通した率 P26・P27、名指して原本の値を返した率 P26・P27・P27E)は、表の行として名指して並べる。

### §2-5 盲検と記録の欄(依頼文の規約のとおり)

- **文・DB の応答・指示文は、script が読んで engine に渡すだけ。** 席・司令塔・監査は開かない・印字しない・抜粋しない。標準出力は件数・旗・秒・path だけ。止める文言にも文・値を入れない(段 1 の `Stop` の作法)。
- **記録に持てる欄**: docID・注入の id・型・文体・r・r を決めた回・基準の claim の id・注入後に数えた claim の id・2 つが同じか・対応の付け方(値と字 / 値だけ)・engine の文の一覧の番号(token の文・基準の claim の文・注入後の claim の文)・文の中の位置と数の始まり・終わり(整数)・文の数・届いた(文)/(数) の旗・state・reason・結果の語・pointers の有無と先頭が同じかの旗・state が無改変と同じかの旗・分類と細目の語・文の sha256(W の記録の文全体の sha256 だけ。文ごとの sha256 は持たない)・ZIP の sha256。
- **持てない欄**: 文の抜粋・周りの字・数の字・span・subject・value・recomputed・pointers の字そのもの・新しい値・元の字・後の字(前例 `eval_inject` が repo に入れなかった欄と同じ。迷ったら持たない)。script は記録の全部の鍵を「持てる欄」の一覧と照らし、一覧に無い鍵が 1 つでも在れば書かずに止める。さらに段 1 の `assert_record_clean`(禁止の鍵・`record_key_leaks`)を書く前と書いた後に通す(commit の 40 桁を持つ欄は評価用の script と同じく `COMMIT_KEYS` に足す)。
- `~/.cache/audit-core/edinet/`(281)は読まず書かない(段 1 の `cache_snapshot` が件数と名前の一覧の sha256 を取るだけ)。`edinet-fresh-2026-10-21/`(40)は ZIP を読むだけで、1 file も足さない・変えない。`edinetdb-p27/` の下は `read_report`(文)だけが開き、件数も数えない。`~/Desktop/sgogi-coach-handoff/` は読まない。作業 folder(`prepare_xbrl` の refs)は TMPDIR の下に作り、終わりに消す。
- engine の確かめ(`E.preflight` の代わり): `git diff --quiet HEAD -- audit-core/adapters audit-core/core`(未 commit の差が無い)、`V.DEFAULT_PROFILE` を記録に書く、6 本の sha16 と `engine_fingerprint` を記録に書く(門 (f) が留める)。

## §3 事前予測(欄ごと・外れうる形・外れ方つき。§6 の下調べより前に固定)

予測の土台(§0-5 の範囲で見たもの): 2 型とも新しい値は refs に無く、注入後の対応付けは新しい値で claim を引くので、差し替えた token を読んでいない claim が引かれるのは別の claim が偶然その値を持つときだけだと見る(§0-3)。対応が付かない行は 4 profile で同じ 5 行で、引けないときは「別の claim」ではなく None に落ちていると見る。「通した」行は P27 で全部 GROUNDED を離れたが、無改変で P26 → P27 に GROUNDED を離れた claim は評価用 1 / 523・調整用 2 / 534 しか無い。通した行の注入後の claim が差し替えと無関係の claim なら、その claim は P27 でも無改変のまま GROUNDED に残るはずなので、通した行の大半は差し替えを読んだ claim だと見る。**この見立ては「届いた」の向きに寄っている**(前の便の R-3〜R-6 と同じ向き)。外れが同じ向きに揃ったら見立ての偏りとして診断の文書に書く。

| # | 欄 | 予測 | 外れ方 |
|---|---|---|---|
| **IR-1** | 配線の門(§2-1) | 評価用 96 / 96 行・調整用 101 / 101 行が記録の欄と全部一致(調整用は 2 本の記録の両方と)。(docID, id) の集合が同じ。書類別の数え 40 組(10 × 2 × 2 組)が一致。round-trip 評価用 113・調整用 122 | 1 つでも違う(止める。観測を書かない) |
| **IR-2** | 注入後の id が基準の claim の id と違う行(対応が付く行のうち。profile ごと) | 評価用 **0 以上 1 以下**、調整用 **0 以上 2 以下**(4 profile とも) | どれかの profile で 評価用 2 以上、調整用 3 以上 |
| **IR-3** | 文が 1 つに決まらない(対応が付く行。profile ごと) | 両方の組で **0 以上 2 以下** | どれかで 3 以上 |
| **IR-4** | 届かない(文)(対応が付き、文が決まる行で、token の文 ≠ 基準の claim の文。profile ごと) | 評価用 **0 以上 1 以下**、調整用 **0 以上 2 以下** | どれかで幅の上 |
| **IR-5** | 「id が同じ」と「届いた(文)」が食い違う行(対応が付き、文が決まる行) | 両方の組・4 profile とも **0** | 1 以上 |
| **IR-6** | 同じ文・別の数(届いた(文)だが届いた(数)でない。P22) | 両方の組で **0 以上 3 以下** | どちらかで 4 以上 |
| **IR-7** | 「通した」のうち (届いた・通した) でない行 | 評価用 P22・P26、調整用 P22・P26 の各々で **0 以上 1 以下**(P27・P27E は通した行が 0 なので 0) | どれかで 2 以上 |
| **IR-8** | 「名指したが別の値」のうち (届いた・止めた) でない行 | 評価用 P22・P26・P27・P27E、調整用 同の各々で **0 以上 1 以下** | どれかで 2 以上 |
| **IR-9** | 対応が付かない 5 行(評価用 T8_REL 2・調整用 T1_VALUE 1・T8_REL 2)の P22 での「token の文 = 基準の claim の文」 | **4 行以上 / 5**(引けないのは注入後の側で、基準は差し替えた token の文の claim) | 3 行以下 |
| **IR-10** | 評価用 T8_REL の読み直した率(§2-4) | 分母 **85 以上 87 以下**。通した率 P22・P26 は **31.0% ± 1.5 pt の内**、P27・P27E は **0.0%**。名指して原本の値を返した率 P26 **41.4%**・P27 **31.0%**・P27E **89.7%** の各々が **± 1.5 pt の内** | 1 つでも幅の外 |
| **IR-11** | 調整用 T8_REL の読み直した率 | 分母 **86 以上 88 以下**。通した率 P22・P26 **31.8% ± 1.5 pt**、P27・P27E **0.0%**。名指して原本 P22 63.6%・P26 21.6%・P27 21.6%・P27E 85.2% の各々が **± 1.5 pt の内** | 1 つでも幅の外 |
| **IR-12** | T1_VALUE の対応が付く行(評価用 7・調整用 10) | 4 profile とも全部 **(届いた・止めた)** | 1 行でも別の分類 |
| **IR-13** | 文の一覧の数の profile の間の一致(書類ごと、無改変) | 20 書類とも **4 profile で同じ数** | 1 書類でも違う |
| **IR-14** | §0-2 の「無改変の P27・P27E で基準が UNVERIFIABLE」の 3 行 | P27 で 3 行とも **届いた(文)** | 1 行でも 届かない か 決まらない |

- IR-2・IR-4・IR-7・IR-8 は「届かない行はほぼ無い」の向きに寄せた予測。新しい値が別の claim と偶然一致する行が多ければ、IR-2 と IR-4 が上に外れ、通した行がそこに在れば IR-7 も外れる(その数は対応付けの数で、engine の数ではない)。
- IR-7 を 0 側に予測したことは「T8_REL の通した行は engine の見逃し」の主張ではない。届いた(文)は engine の文の一覧の番号の一致で、claim がどの fact で GROUNDED になったかは見ない(§4 の 2)。
- IR-10・IR-11 の幅は「読み直しても率は動かない」の予測。外れたら、外に出した紙の数が対応付けの数を含んでいたことになる(直すかは人間が決める)。
- 各型の「engine の直し方」はこの封に書かない(診断だけ)。

## §4 言えないこと・限界(封の時点で分かっているもの)

1. **文を誰も読まない。** 「届いた」の意味は engine の文の一覧の番号の一致(と数の位置の整数)だけで、差し替えた字を claim が読んだことを字で見た人はいない。数の位置が合うことは、claim がその数を使ったことの必要条件で十分条件ではない(1 文に数が複数在る。差の主張・率の主張)。
2. **「届いた・通した」は engine が差し替えた claim を通した行だが、なぜ通したか(どの fact に GROUNDED したか)はこの便では読まない。** pointers の字は記録に持たない(旗だけ)。比べる側の分岐(`resolve.py`・`comparators.py`)も読まない。
3. **評価用は「使い切った」材料である。** この便も評価(数え直し)だけで、規則の調整には使わない。評価用は本番の 1 回だけ走らせる(下調べでは走らせない)。走らせ直しで評価用の文を engine にもう一度通すことは人間が許した(2026-10-29)が、その 1 回で配線の門が通らなければ、もう 1 回走らせるかは人間が決める。
4. **外に出した紙・台帳 D-22・D-23・結果文書 `XBRL_P27_RESULT_2026-10-27.md` の字は直さない。** 診断の文書に日付つきで読み直しを書く。直すかは診断の後で人間が決める。
5. **基準は「無改変で P22 と P26 の両方が GROUNDED」**(§0-3)。P27・P27E で無改変から GROUNDED でない基準の行(3 行)は、その profile では「止めた」が差し替えと無関係でありうる(細目で数える)。
6. **文の番号は engine の文の一覧の中の番号で、文の本文の位置ではない。** `diff_sentence` は同じ長さ・1 文だけ違うときに限る。差し替えが文の切り方を変えると「決まらない」になる。
7. **評価用 10 社・調整用 10 社・1 書類あたり型ごと 40 件までの観測である。** 土台で絞られた site(どちらも GROUNDED でない・基準に対応が付かない)の側はこの便でも見ない。Core 全体の振る舞いを断定しない。
8. **E(`b2c3f56`)から HEAD の engine の差(`6a34db5`)は字で見ただけで、振る舞いが同じことは配線の門が示す**(門が通らなければ止める)。調整用の P22・P26 の記録(`tune_inject`)は E より前の engine の数で、U-1 が E で 0 行の差を確かめた。
9. 読みは無い(席は呼ばない。人の目も入らない)。観測は全部 engine の出力からの機械の値。
10. 所要時間は前の便(1 行あたり 4〜5 秒・6 profile)から、注入 235(調整用 122・評価用 113)× 4 profile で 1 process なら 15〜25 分の見込み。**時間は症状で、目標ではない**。途中で止まったら記録を書かない。

## §5 file と順序

1. **この封**(文書だけ)。本線へは `docs/XBRL_P27_INJECT_REACH_SEAL_2026-10-29.md` として司令塔が写して commit する(scratchpad の file と byte 一致)。封の commit が script・記録・診断の文書・門のどの commit よりも前であること(順序の門は commit の順で見る)。docID・claim の id を含まない。
2. 診断の便(1 commit。独立監査 GO の後):
   - script `measure/xbrl_p27_inject_reach_2026-10-29.py`(§2)。出力が既に在れば測り直さない。`--set`・`--docs`(調整用だけ)・`--procs`・`--out`・`--work-dir` を持つ。
   - 記録 `fixtures/xbrl/p27/inject_reach_2026-10-29.json`(docID と claim の id を持つ。文・値は持たない。§2-5)。行は 1 行 1 件の compact JSON(前の便と同じ)。
   - 文書 `docs/XBRL_P27_INJECT_REACH_DIAG_2026-10-29.md`(前の便の節立て: 予測の当否(先頭)→ 既存の記録で足りなかった → 配線 → 観測(集計の表。行ごとの表は書かない。例は位置で数行まで)→ 判定(§2-4 の読み直しの表を日付つきで)→ 仮説 → 言えないこと → 次に測ること。表は `<!-- 門:start 名前 -->`〜`<!-- 門:end -->` の内側。門の外の散文は数を持たない(持つ行は【門なし】)。docID・claim の id を書かない)。
   - 門 `tests/measure/test_xbrl_p27_inject_reach.py`: (a) 記録の行の (docID, id) が `eval_inject`・`tune_p27_inject`・`tune_inject` の行と集合で同じ(字で留めない)、型別の数が記録と同じ (b) 配線の門(全行一致・書類別の数え 40 組・round-trip 113 / 122)が記録されている (c) 文書の表を記録から作り直して一致 (d) IR-1〜IR-14 の当否を記録から求め、封の字(予測・外れ方)と文書の当否の字が一致 (e) 分類(§2-3)を記録の欄から別実装で求め直して一致(届いた(文)・届いた(数)・id が同じ、の 3 つとも) (f) engine の sha16 を `ENGINE_AT_MEASURE` に字で留め、遷移は `ENGINE_DECLARED` で宣言する(前の便と同じ型。6 本) (g) 偽物で赤: 記録の写しの分類・文の番号・id の旗・配線の旗・対応の付け方を 1 か所変えると (b)(c)(e) が赤、文書の表の 1 字で (c) が赤、封の予測の 1 字で (d) が赤、包みが返り値を変える偽の包み(作り物の backend)で包みの門が赤 (h) 封と文書に評価用・調整用 20 書類の docID と claim の id の字が無い、記録に持てない欄の鍵が 0(§2-5 の一覧と照らす。`span`・`subject`・`value`・`recomputed`・`pointers`・元の字・後の字・新しい値・数の字・周り) (i) 封の commit が script・記録・文書・門の commit より前(前の便の `test_i_*` の型) (j) 記録が持つ入力の sha256(§2-2 の 8 本)がいまの file と一致(読み直しの元が不変)。
   - `tests/measure/test_xbrl_fresh_seal.py` の `LATER_NAMING_FILES` に記録・script・門の 3 つを足す(日付つきの注記。既存の並びは変えない)。
   - 覆い: `python3 measure/suite_coverage_2026-10-16.py --write` と `docs/SUITE_COVERAGE_2026-10-16.md` §2-1 の数。
3. 凍結(木の sha256 の一覧)→ 独立監査(`step-auditor`。調整用を自分で走らせ直して記録の調整用の行と byte 一致を見る。評価用は走らせ直さない(§4 の 3。走らせ直すかは司令塔が人間に聞く)。分類を別実装で求め直す。変異 (g))→ GO → commit(パス指定)。監査中は木を触らない。
4. engine の直しはこの便に入れない。(届かない・通した)の行が出たら、その数は対応付けの数として診断の文書に書き、台帳・紙の字の直しは別の便(人間の決定)。

## §6 下調べの観測(予測の後。scratchpad の clone。正本でない。0 USD)

§3 を書いて file を保存した後に、`<S>/evalreach_seal/probe/clone`(HEAD `365b468`)で §2 の配線を**調整用の先頭 2 書類だけ**で試した(`probe/reach_probe.py` → `probe/reach_probe_out.json`・`probe/reach_probe_stdout.txt`・`probe/summary.txt`)。**評価用は走らせていない**(本番の 1 回だけ)。本番は調整用 10・評価用 10 の全部(§5)。**§0〜§5 の字は変えていない**(§3 を固定した時点の封の sha256 `58368631…842f5c`・41,763 bytes = この節を足す前の file の先頭と byte 一致。`probe/mtime_seal_predictions.txt`)。時刻: 予測を固定 2026-10-29 11:53:43 JST、下調べの開始 11:55:43 JST、出力 11:56:37 JST(`probe/probe_start.txt`・`probe/mtime_probe_observed.txt`)、この節はその後に足した。
ここの数は下調べの数で、正本は §5 の記録と門が出す。**IR-1〜IR-14 の当否は本番の記録から門が求める。** ここに書く見立ては 2 書類の時点のもので、本番で変わりうる。

### §6-1 配線・環境

- 配線の門(2 書類): 作り直した行 4・14 = **18 / 18** が `tune_p27_inject`(4 profile)と `tune_inject`(P22・P26)の両方と、型・文体・基準の claim・r・r を決めた回・profile ごとの対応・結果・state・reason で一致。(docID, id) の集合が同じ。書類別の数えは 2 書類 × 2 型とも 2 本の記録の両方と辞書ごと同じ。round-trip 23(採った数の合計)。
- 包み: `claim_for_p27` の包みが呼ばれた回数 72 = 行 18 × 4 profile。claim の一覧の `id()` は全部 backend の控えに在った。無改変の控えは 4 profile に 1 つずつ。基準の枝・注入後の枝の判定は 18 行 × 4 profile で本物と同じ claim を指した(違えば止まる作り)。**作り物の backend での「包んでも返り値が byte 同じ」の門は、下調べでは試していない**(§5 の門 (g) で本番の便が作る)。
- 文の sha256 は W の記録と 2 / 2 一致(段 1 の `read_report` が照らす)。ZIP の sha256 も段 1 の `read_zip` が照らした。
- cache: 開始 `edinet/` 281・`edinet-fresh-2026-10-21/` 40 → 終了 281・40。段 1 の `cache_snapshot`(2 つの folder の件数と名前の一覧の sha256)も前後で同じ。作業 folder は `probe/tmp` の下に作り、終わりに消した(残り 0)。`PYTHONPYCACHEPREFIX` も probe の下。`edinetdb-p27/` は script の `read_report` が文を 2 本開いただけ(席は ls・cat・件数の数えをしていない)。外の置き場には何も書いていない(`inject_doc` の外に置く行は捨てた)。
- `DEFAULT_PROFILE` = P27。engine の sha16: extract `3cf55966f12919f0`・vocabulary `514ebb8104451c07`・recipes `52d645e713c53c1c`・resolve `a41043763c1d4073`・comparators `d8706338325e725b`・verify_document `c3791080ab5aef2f`(前の便の記録と同じ 6 本)。
- 所要: 2 書類を 1 process で 53 秒(書類ごと 15・38 秒。行 4・14)。1 行あたり 3 秒前後(4 profile)。本番の 197 行なら 1 process で 10 分前後の見込み(§4 の 10 のとおり症状で、目標ではない)。
- 文の数(4 profile で同じ): 26・19。claim の数(4 profile で同じ): 34・69。

### §6-2 観測の集計(2 書類・18 行。位置と集計だけ)

| profile | 型 | 行 | 対応が付く | id が同じ | 届いた(文) | 届いた(数) | 決まらない | (届いた・止めた) | (届いた・通した) | (届かない・止めた) | (届かない・通した) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P22 | T1_VALUE | 3 | 3 | 3 | 3 | 3 | 0 | 3 | 0 | 0 | 0 |
| P22 | T8_REL | 15 | 15 | 15 | 15 | 15 | 0 | 6 | 9 | 0 | 0 |
| P26 | T1_VALUE | 3 | 3 | 3 | 3 | 3 | 0 | 3 | 0 | 0 | 0 |
| P26 | T8_REL | 15 | 15 | 15 | 15 | 15 | 0 | 6 | 9 | 0 | 0 |
| P27 | T1_VALUE | 3 | 3 | 3 | 3 | 3 | 0 | 3 | 0 | 0 | 0 |
| P27 | T8_REL | 15 | 15 | 15 | 15 | 15 | 0 | 15 | 0 | 0 | 0 |
| P27E | T1_VALUE | 3 | 3 | 3 | 3 | 3 | 0 | 3 | 0 | 0 | 0 |
| P27E | T8_REL | 15 | 15 | 15 | 15 | 15 | 0 | 15 | 0 | 0 | 0 |

- 基準の対応の付け方は 18 行とも「値と字」。注入後の対応の付け方も 18 行 × 4 profile とも「値と字」。注入後の claim の文の番号 = token の文の番号(18 行 × 4 profile)。「id が同じ」と「届いた(文)」の食い違い 0。同じ文・別の数 0(細目は 72 / 72 が「数の位置が合う」)。
- 結果の語 × 分類: P22 通した 9 は 9 とも (届いた・通した)、名指して原本の値を返した 9 は (届いた・止めた)。P26 通した 9・名指して原本 5・POINTER_NOT_FOUND 4。P27 名指して原本 6・POINTER_NOT_FOUND 12。P27E 名指して原本 17・POINTER_NOT_FOUND 1。この 2 書類に「名指したが別の値」と「対応が付かない」の行は無い。
- 注入後の state が無改変の同じ id の state と同じ行: P22・P26 は 9(= 通した 9 行。無改変も GROUNDED)、P27・P27E は 0。通した 9 行の注入後の claim は基準と同じ id で、差し替えた token の文の、数の位置の claim だった。
- VALUE_MISMATCH の行の pointers の先頭は全部、基準(同じ profile の無改変)の先頭と同じ(P22 9・P26 5・P27 6・P27E 17。全部「名指して原本の値を返した」)。

### §6-3 下調べの時点の当否の見立て(2 書類だけ。本番の門が 20 書類で求め直す)

| # | 見立て(2 書類の範囲) | 理由 |
|---|---|---|
| IR-1 | 当たりの側 | 18 / 18、数え 4 組一致、round-trip 23(本番は 96 + 101 行・40 組・113 / 122) |
| IR-2 | 当たりの側 | id が違う行 0 / 18(4 profile) |
| IR-3 | 当たりの側 | 決まらない 0 |
| IR-4 | 当たりの側 | 届かない 0 |
| IR-5 | 当たりの側 | 食い違い 0 |
| IR-6 | 当たりの側 | 同じ文・別の数 0 |
| IR-7 | 当たりの側 | 通した 9 は全部 (届いた・通した) |
| IR-8 | 未観測 | 2 書類に「名指したが別の値」の行が無い |
| IR-9 | 未観測 | 2 書類に対応が付かない行が無い |
| IR-10 | 未観測 | 評価用は走らせていない |
| IR-11 | 当たりの側(2 書類の分母では) | 2 書類の T8_REL 15 行は全部 4 profile で届いた(読み直しても率は動かない)。分母の幅は 88 行の本番で見る |
| IR-12 | 当たりの側 | T1_VALUE 3 行 × 4 profile が (届いた・止めた) |
| IR-13 | 当たりの側 | 2 書類とも 4 profile で文の数が同じ |
| IR-14 | 未観測 | その 3 行は先頭 2 書類に無い |

見立ての向き: §3 の「届かない行はほぼ無い」は 2 書類では当たりの側。2 書類は対応が付かない行と「名指したが別の値」の行を持たないので、届かない行が出るとすれば残りの書類のその種の行だと見る(本番で外れれば外れのまま残す)。

### §6-4 下調べで分かったこと(診断の文書の判定・仮説の節に書く材料。記録は書き換えない)

1. **外から渡した文でも、`_RawTap` + `verify_raw` で文の一覧と claim の `sentence`・`pos` が取れた**(§0-4 の code の読みのとおり)。前の便と同じ求め方が使える。
2. **2 書類では、T1_VALUE・T8_REL の全部で、注入後に数えた claim は基準の claim と同じ id で、差し替えた token の文の、数の位置の claim だった。** P22・P26 の通した 9 行は、差し替えた claim を engine が GROUNDED にした行(state も無改変と同じ)で、対応付けの数ではない。P27・P27E ではその 9 行が全部止まった(この 2 書類の範囲。なぜ通したか・なぜ止めたかはこの便では読まない ― §4 の 2)。
3. 評価用の script の `preflight` はいまの HEAD では止まる(§0-4)ので、下調べも `run_inject` を通さず `inject_doc` を直接呼んだ。`E.T` の 1 つの module の `claim_for_p27` を包み、`E.T.inject_doc` に届いた(包みの回数 72 = 18 × 4)。

### §6-5 追記(2026-10-29、下調べの後。§2 の仕様の補い。§3 の字は変えない)

- 記録の頭の HEAD の欄の名は `HEAD の commit` にする(段 1 の `COMMIT_KEYS` が 40 桁の小文字 16 進を鍵の検査から外す欄の名。`HEAD` という名だと `record_key_leaks` の「32 字以上の英数字」に当たる)。E・W の commit を持つなら、評価用の script と同じく `COMMIT_KEYS` に足した名にする。
- §2-5 の「持てる欄」の一覧は、`書類別の数え` の中の鍵(`作れる site`・`採った`・`両方 GROUNDED`・`どちらも GROUNDED でない`・`基準に対応が付かない`・`P22 のみ GROUNDED`・`P26 のみ GROUNDED`・`profile 間で claim が合わない`・`円族の token`・`r が決まらず site にしない`)と、engine の file の path(sha16 の鍵)と、cache の folder の名を含める(下調べの script の一覧の形)。
- 細目の「届かない行」の分け方(別の id / 同じ id・state が違う / 同じ id・state も同じ)は、(届かない・止めた)と(届かない・通した)の両方に当てる(前の便の script の `detail_of` は (届かない・通した) には None を返すので、新しい script は自分の細目の関数を持つ。分類の順(§2-3)は変えない)。
- 前の便の script(`xbrl_inject_reach_2026-10-28.py`)を `num_span`・`classify_row` と分類の語のために import すると、`xbrl_fresh_2026-10-21.py` から `xbrl_lastbranch_2026-10-21.py` までの import の鎖を読む。下調べでは cache の件数・名前の一覧は前後で同じだった。**import の鎖が `edinet/`(281)の file を開かないことは、件数では確かめられない**(code の上では、鎖の中で `edinet/` を開くのは関数の中だけで、import の時には呼ばれない、と読んだ。測ってはいない)。
- 下調べの 2 書類は調整用の先頭 2 件で、本番の調整用 10 書類に含まれる。本番の記録はこの 2 書類についても作り直す(下調べの出力は使わない)。
