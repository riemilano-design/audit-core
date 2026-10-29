# 封: P27 が「証拠が無く名指さない」で止めた行で、engine が内側に持つ「名指さなかった fact」は原本の fact か ― 2026-10-29

**人間(2026-10-29)「君に任せる進めて」。司令塔の戦略: 測定の測定はいったん止め、商品の 1 点 = 名指しに戻る。** 看板は「出所に縛る検証層」で、DB 側の相手に売れる価値は「止める」より「どの行かを指す」こと。止めた理由の診断(封 `docs/XBRL_STOP_REASON_DIAG_SEAL_2026-10-29.md` = `6bea94b`、記録 `fixtures/xbrl/stop_reason_2026-10-29.json`・文書 `docs/XBRL_STOP_REASON_DIAG_2026-10-29.md`・script `measure/xbrl_stop_reason_2026-10-29.py`・門 `tests/measure/test_xbrl_stop_reason.py` = `ed615b5`)が残した「P26・P27 は T5 の多くを `no_same_value` にした」と「比の分布」の宿題(同 文書 §8)を、同じ 741 行と無改変の 30 書類で測る便。
**この封は診断だけ。engine(`core/`・`adapters/`)は 0 行・出力の形(`verify_document.py` の `CLAIM_FIELDS`・`report_customer.py`)は 0 行。** 既存の記録(`stop_reason_2026-10-29.json`・`inject_reach_2026-10-28.json`・`fresh/fresh_2026-10-21.json`・`p27/regress97_2026-10-27.json`・`default_p27_2026-10-28.json`)は書き換えない(別の記録を足す)。「名指さなかった fact」を出力に出す変更(`adapters/` の変更 = 人間の承認が要る)は、この診断の結果を見てから別の封で決める(§7)。0 USD・通信なし・席(LLM)は呼ばない。評価用・調整用(`~/.cache/audit-core/edinetdb-p27/`)は開かない・使わない。
作法は変えない(封 → 測定 → 凍結 → 独立監査 GO → commit)。数を見てから封・予測を直さない。外れは外れとして残す(補足は日付つきの追記)。

- 封の時点: branch `feature/audit-core-final-eval-8`、HEAD `14771a6`、`vocabulary.DEFAULT_PROFILE = "P27"`。engine の sha16 6 本(extract `3cf55966f12919f0`・vocabulary `514ebb8104451c07`・recipes `52d645e713c53c1c`・resolve `a41043763c1d4073`・comparators `d8706338325e725b`・verify_document `c3791080ab5aef2f`)は止めた理由の記録 `stop_reason_2026-10-29.json` の `engine sha16` と同じ 6 本(封を書く席が HEAD で計算して照らした)。
- この封は docID・claim の id・タクソノミのラベル(日本語名)を書かない。書類と行は**位置か集計**で呼ぶ。要素名(`接頭辞:名前`)は書いてよいが、提出者別の接頭辞の要素名は書かない(前の便 §2-5 と同じ)。
- 前例の型: 止めた理由の便(封 §2 の配線の門・§2-3 の機械の分類・§3 の欄ごとの予測・§6 の下調べ)。

## §0 根拠(封を書く席が、記録と engine の code から自分で数え直した。司令塔の下見の数と違えば、この節の数が正本)

### §0-1 問い

1. **P27 が `no_same_value`(証拠が無く名指さない)で止めた行(741 行の内側)で、engine が内側に持つ `no_same_value.named` は、無改変の基準の claim の先頭の pointer と同じか。** 型別(T1・T2・T5。T3 は基準が無いので別に: `named` が在るか、P22 の注入後の先頭の pointer と同じか)。同じなら、出力に出すだけで「P22 の名指し」を「P27 の止め」のまま取り戻せる行の数がそれ。違うなら、何が違うか(要素だけ・context だけ・両方)。
2. **無改変の新しい標本 30 書類で P27 が `no_same_value` にした claim は何行で、その全部に `named` が在るか。** これは「出力に出したら、無改変の文にも候補が付く行の数」= 代価の側の数。正解が無いので正しさは測れない。P22 がその同じ claim を何にしたか(VALUE_MISMATCH で同じ fact を名指したか)を並べる。
3. **`named` の `value` と、注入後の文の値(claim の `value` × 単位の倍率)との比(大きさ)の分布**を、型別に幅で(止めた理由の診断 §8 の宿題。判定には使わない)。無改変の `no_same_value` の行でも同じ比を数える(P27E の B の規則 `LAST_BRANCH_REL_RHO = 0.15` が名指しに移した 24 行との突き合わせになる)。

### §0-2 記録の数(封を書く席が記録から数え直した)

**741 行(記録 `stop_reason_2026-10-29.json` の `rows`。型別 T1_VALUE 195・T2_UNIT 263・T5_COINCIDENT 103・T3_ABSENT 180)の P27 の注入後の claim の (state, reason)**:

| 型 | P27 の (state / reason) の行数 |
|---|---|
| T1 195 | VALUE_MISMATCH 192・`no_same_value` 2・`no_element(no prior2 for prior-year diff)` 1 |
| T2 263 | VALUE_MISMATCH 171・`no_element` 41・`no_same_value` 32・`no_element(point without prior phrase)` 9・`no_element(no prior2 for prior-year diff)` 2・GROUNDED 5・対応が付かない 3 |
| T5 103 | `no_same_value` 92・VALUE_MISMATCH 11 |
| T3 180 | `no_element` 70・`no_same_value` 30・`no_subject` 59・`ambiguous(elements)` 20・対応が付かない 1 |

- **P27 の `no_same_value` は T1 2・T2 32・T5 92(計 126)・T3 30(計 156)。** 司令塔の下見の数(T1 2・T2 32・T5 92・T3 30)と同じ。
- **126 行(T1・T2・T5)の全部で**: P22 の注入後の claim は VALUE_MISMATCH で語は(名指した・原本)126 / 126。基準の claim(P27 の無改変の一覧から id で引いたもの。P22 の無改変も同じ)は state が GROUNDED で pointers が空でない 126 / 126。**P22 の注入後の先頭の pointer = P27 の基準の先頭の pointer が 126 / 126**、P22 の基準の先頭 = P27 の基準の先頭も 126 / 126。P22 の注入後の claim の form は `direct_value`・pointers は 1 本・`recomputed` は None でない 126 / 126。
- 基準の claim の form: T1 `derived_value` 2(pointers 3 本)、T2 `direct_value` 21(1 本)・`derived_value` 11(3 本)、T5 `direct_value` 90(1 本)・`derived_value` 2(3 本)。P22 の「recomputed が同じ」(記録の `名指し`): T1 0 / 2・T2 21 / 32・T5 90 / 92(違う 15 行 = 基準が `derived_value` の 15 行)。
- 単位(基準の claim の `unit` → P27 の注入後の claim の `unit`): T1 千円 → 千円 2。T2 千円 → 億円 24・千円 → 兆円 4・千円 → 百万円 2・千円 → 円 1・円 → 百万円 1。T5 千円 → 千円 74・百万円 → 百万円 18(T5 は単位を変えない)。T3 の注入後の claim の `unit` は 円 30。
- **T3 30 行の全部で**: P22 の注入後の claim は VALUE_MISMATCH・(名指した・基準なし)・`direct_value`・pointers 1 本・`recomputed` は None でない 30 / 30。
- 741 行の `後の字` / `元の字` の比は**数えていない**(§0-4)。

**無改変の 30 書類(記録 `fresh/fresh_2026-10-21.json` の `claims`(書類ごと・claim ごとの P22〜P26 の state と reason)と `p27/regress97_2026-10-27.json`)**:

- claims 3,923。4 state: P22 GROUNDED 2,142・VALUE_MISMATCH 677・UNVERIFIABLE 690・POINTER_NOT_FOUND 414。P27 2,194・250・787・692。P27E 2,194・274・787・668(`regress97` の `集計 > 新しい標本 30`。`default_p27_2026-10-28.json` の S3 の `既定の 4 state` も 30 書類・claims 3,923)。
- **P26 の `no_same_value` は 297 行**(書類ごと 1〜25)。その 297 行の P22 は全部 VALUE_MISMATCH(reason None)。P25 の `no_same_value` も 297。
- `regress97` の `動いた行 > 新しい標本 30 > P26 → P27` は 15 行: `no_element(unit not in XBRL)` → `per_unit_counter` 11・`no_element` → `per_unit_counter` 1・`ambiguous(elements)` → `no_element` 1・**`no_same_value` → `target_or_plan` 1**・`no_element` → `target_or_plan` 1。`no_same_value` に入る行は 0。だから **P27 の `no_same_value` は 296 と見込む**(測って確かめる。§3 UF-9)。
- `P27 → P27E` は 24 行(全部 `no_same_value` → VALUE_MISMATCH。`規則ごとに当たった claim の数` の P27E `B relative_within_rho` 24)。

### §0-3 engine の事実(封を書く前に `adapters/xbrl/recipes.py`・`verify_document.py`・`report_customer.py` と、読む経路の script を読んだ)

- `recipes.py` の最後の枝(`_last_branch_decide_2026_10_27`(P27E の B)→ `_last_branch_unname_2026_10_21`(P26 G2)→ `_last_branch_unname`(P25)の順。どれも `named = cur[0]` = その主語の当期の fact)は、名指さずに止めるとき `claim["no_same_value"] = {"named": "xbrl:<要素>@<context>", "value": <fact の値>}` を書く(3 か所とも同じ字。`NO_SAME_VALUE = "no_same_value"`)。証拠があれば何も書かず、下の P21 の 5 行が `pointer = "xbrl:<要素>@<context>"`(同じ `cur[0]`)・`recomputed = cur[0]["value"]` で VALUE_MISMATCH にする。**だから P22 が名指した fact と、P26・P27 が名指さなかった fact は、同じ場所の同じ `cur[0]` である**(ただし `cur` を選ぶ手前の規則は profile で違いうる)。
- `_raw_to_provenance` 相当の箇所(同 file、`claim_to_recipe` の中の `provenance["no_same_value"] = raw["no_same_value"]`)で Recipe の `claim.provenance` に写る。P27 の C2・C3 が束縛を消すときは `_P27_STALE_KEYS` で `no_same_value` も消す。
- `verify_document.py` の `CLAIM_FIELDS` は id・kind・form・subject・value・unit・word・span・state・pointers・reason・recomputed の 12 欄で、**出力 JSON に `no_same_value` は出ない。** `report_customer.py` は reason の字 `no_same_value` を客向けの一文に替えるだけで、名指さなかった fact は読まない(file の中に `provenance` の語は `.provenance.json` の指紋の話だけ)。
- 読む経路: `measure/xbrl_lastbranch_2026-10-21.py` の `_RawTap`(`R._build_raw_num_claims`・`_build_raw_text_claims`・`_member_material` を実行中だけ差し替え、raw の claim を拾う)と `verify_raw(tap, zb, prof, text)`(`VD.verify_document` を呼び、`(出力, {id: raw の claim}, 文の一覧)` を返す。raw の claim に `no_same_value` の鍵が在る)。`provenance_doc` は Recipe の `claim.provenance.get("no_same_value")` を数える(この便では使わない。raw で足りる)。
- 比の土台: `vocabulary.UNIT_SCALE = {"百万円": 1e6, "千円": 1e3, "億円": 1e8, "兆円": 1e12, "円": 1}`。fact の `value` は円の数(XBRL の生の値)、claim の `value` は書かれた単位の数(前の便の `dossier` が `value * unit_scale` で円に直している)。
- 注入の規則(`measure/inject.py`・`measure/lib/sites.py`): T1 は元の値 ± (1〜13) × (2〜11)(参照の数に無い値)、T2 は数字そのまま単位を同じ族の別の単位に、T5 は別の fact の値(`MAGNITUDE_RATIO = 10.0` で元の値の 1/10〜10 倍、単位は互換)、T3 は 37 から 7 刻み(400 未満)の、参照の数に無い値を円で書いた文。

### §0-4 封を書く前に見たもの(予測の偏りの出どころ)・見ていないもの

- 見たもの: 止めた理由の封・文書・script・門の全文(§2・§3・§6 の型)。`inject_reach` の script の `work_doc`・`observe_main`・`observe_t3`・`view`・`CLAIM_KEYS`。`lastbranch` の `_RawTap`・`verify_raw`・`dossier` の冒頭・`provenance_doc`。`recipes.py` の最後の枝(F3b・B・G2・P25 の 30 行ほど)と `_last_branch_unname`・`_last_branch_decide_2026_10_27`・`claim_to_recipe` の provenance の写し。`verify_document.py` の `verify_document`。`inject.py` の `build_t1`・`build_t2`・`build_t5`・`build_t3`、`sites.py` の `t5_sites`。記録: `stop_reason` の欄の名前と、§0-2 の集計(state・reason・語・基準の form・pointers の本数・unit・先頭の一致の旗)。`fresh` の `claims` の集計と `動いた行` の欄の名前・dossier の `型` の集計(§1)。`regress97` の `集計` と `動いた行` の 15 行・24 行の前と後。
- **見ていないもの**: 741 行のどの行の `named` の字も値も(記録に無い)。`後の字` と `元の字` の比(記録に在るが数えていない。比の予測が記録から決まってしまうのを避けた)。無改変の `fresh` の dossier の `名指した fact` の字・`名指した値`(集計の `型` だけ見た)。engine を走らせた結果は何も見ていない。
- **§0-2 の単位の対(T2)は見た**ので、§3 の比の帯の T2 の予測は単位の対からほぼ決まる(当たって当然の欄。良さの証拠にしない)。

## §1 既存の記録に無い欄(先に確かめた)

1. **741 行の `no_same_value.named`・`value` はどの記録にも無い。** `stop_reason_2026-10-29.json`・`inject_reach_2026-10-28.json` の claim の欄は `CLAIM_KEYS` の 10 欄(id・kind・form・value・unit・span・state・reason・pointers・recomputed)だけで、file の中に `"no_same_value": {` の形は 0 回(`no_same_value` の字は reason の値として 1,109 回・781 回)。`regress97`・`default_p27` にも 0 回。
2. **無改変の行では、別の profile の `named` が一部の記録に在る。** `fresh/fresh_2026-10-21.json` の `動いた行`(507 行 = P23 → P26 で動いた行)の `dossier` に、P24・P25(`名指した fact`・`名指した値`・`文の値`・`主張の桁`・差・`型` など 13 欄)と P26(`名指した fact`・`型` の 2 欄)の値が在り、P26 で `名指した fact` が `xbrl:` で始まる行は 352(dossier の `型` A 51・B 193・C 5・D 103。`名指しなし` 111・None 44)。`lastbranch_2026-10-21.json`(手元の 67 書類・P25)にも `名指した fact` の字が 343 回在る。**しかし P27 の `named` はどの記録にも無く、P26 の dossier は `名指した値` を持たない。** この便は P27 で測り、fresh の P26 の `名指した fact` は照らす相手(§2-2)にする。
3. **一致の旗**(`named` = 基準の先頭 / 要素 / context、`named` = P22 の注入後の先頭)と**比**(`文の値 / |named.value|`)の欄が無い。

だから、診断用の記録を 1 本足す。engine には触らない。既存の記録は書き換えない。

## §2 測り方(script `measure/xbrl_unnamed_fact_2026-10-29.py` の仕様)

### §2-1 配線(止めた理由の script → 前の便の script の関数を import し、観測する profile を P27 だけにする)

- script は `measure/xbrl_stop_reason_2026-10-29.py` を `_mod(...)` で読み込み(以下 SR)、SR が読み込んだ前の便の module `SR.RE`(= `measure/xbrl_inject_reach_2026-10-28.py`。以下 RE)を使う。SR の import の時点で `RE.OBS` は 4 つ・`RE.CLAIM_KEYS` は `recomputed` つきになっているので、この script は `RE.OBS = ("P27",)` だけを替える(`RE.ALLP` は `tuple(sorted(set(RE.PROFILES5) | set(RE.OBS)))` で P22〜P27 の 6 つ = 前の便の 2026-10-28 の走らせ方と同じ)。**観測するのは P27 だけ**。P22〜P26 は `RE.work_doc` の中の前の便の配線の門(`結果(P22〜P26)` の 4 欄の旗)のために走り、その出力は観測しない・記録に写さない(「走らせるのは P27 だけ」の依頼文に対し、P22〜P26 の engine の走らせを省くには `RE.work_doc` の配線の門を自分で書き直すことになり、「自分で注入の規則・対応付けを書かない」に反するので、走らせは省かず観測を省く)。前の便の script・止めた理由の script の file は触らない。
- 書類ごとに `RE.work_doc(a)` を呼ぶ(引数は止めた理由の script の `main` と同じ 6 つ組: 書類・取得の行・種・作業 dir・記録の `注入の行` の id 引き・`注入の件数(書類別)`)。材料・注入・対応付けは RE の中で `xbrl_fresh_2026-10-21.py` の関数が使われる(`IJ.select` の引数・`INJECT_CAP = 40`・種の照合も同じ)。
- **raw の拾い方**: `RE.LB.verify_raw`(RE が `LB.verify_raw(tap, zb, p, tampered)` と module の属性で呼ぶ。`RE.LB` は `FR.LB` と同じ module の実体)を、**返り値を変えない包み**に実行中だけ替える。包みは `prof == "P27"` のとき、呼び出しごとに `{id: raw の claim の no_same_value}`(`text` が None なら無改変、None でなければ注入後)と `出力の claims`(無改変のときだけ。P22 も無改変のときだけ出力の claims を拾い、P22 の無改変の pointers の先頭を得る)を、書類ごとの一覧に順に積む。`RE.work_doc` は注入の行 1 件につき `verify_raw` を P27 で 1 回だけ呼び、行を `out_rows` に同じ順で積むので、**積んだ順 = 行の順**で対応付ける。対応の確かめは W-3(行の claim の id が、その回の raw に在り、raw の `reason` が出力の `reason` と同じ)。
- 走らせるのは 30 書類(`fetched_2026-10-21.json` の「使う」30 件。生 ZIP は `~/.cache/audit-core/edinet-fresh-2026-10-21/`(40)から読み sha256 を照らす。`~/.cache/audit-core/edinet/`(281)は読まず書かない、`edinetdb-p27/` は開かない。件数は開始時と終了時に数えて記録に書く)。書類ごとに別の process(fork の pool。`--procs`)。出力が既に在れば測り直さない。`--docs` で先頭の n 書類だけの試し(scratchpad の出力へ)。
- 基準の claim の先頭の pointer・P22 の注入後の claim(先頭の pointer・`recomputed`)・P27 の注入後の claim の 10 欄は、**記録 `stop_reason_2026-10-29.json` から id で読む**(走らせ直さない。読んだ記録の sha256 を記録に持つ)。
- engine の sha16 6 本が `stop_reason_2026-10-29.json` の `engine sha16` と違えば、走らせる前に止める。

**配線の門(1 つでも違えば記録を書かずに止める)**:

- **W-1(前の便・止めた理由の便と同じ観測か)**: (i) `RE.work_doc` が返す配線の旗で、前の便の門と同じく 741 / 741 の 4 欄一致・id の集合が記録 `fresh` の `注入の行` と同じ・`注入の件数` 120 組の一致。(ii) 741 行の P27 の注入後の claim(10 欄 + `recomputed`。`json.dumps(sort_keys=True)` の字)が、記録 `stop_reason_2026-10-29.json` の同じ id の `profile.P27.注入後.claim`(T3 は `profile.P27.claim`)と 741 / 741 一致。state・reason・pointers は欄ごとにも数える。
- **W-2(無改変が台帳の記録と同じか)**: 30 書類の無改変の P27 の 4 state の数が `regress97` の `書類` の同じ docID の行の `4 state.P27` と 30 / 30 で一致し、30 書類の和が `default_p27_2026-10-28.json` の S3 の `既定の 4 state` と 4 つとも一致。P22 の 4 state も `regress97` と 30 / 30。
- **W-3(差し替えが使う側に届いたか)**: (i) P27 の注入後の `verify_raw` の捕捉の回数 = 書類ごとの行数(30 書類で 741)、無改変の捕捉 = 30。(ii) 741 行の全部で、行の claim の id がその回の raw に在り、raw の `reason` が出力の `reason` と同じ(claim が None の行 4 は raw を見ない)。(iii) **raw に `no_same_value` の鍵が None でない値で在る行の数 = P27 の reason が `no_same_value` の行の数**(注入後 156、無改変は P27 の `no_same_value` の行数)。鍵が在って reason が違う行、reason が `no_same_value` で鍵が無い行は 0。

### §2-2 観測する欄(行ごと。全部 engine の出力と記録から機械で取る)

注入の 156 行(P27 の reason が `no_same_value` の行。741 行の全部を記録に持ち、`no_same_value` でない行は `named` を None にする):

| 欄 | 出どころ |
|---|---|
| 型・P27 の state・reason | 今回の出力(W-1 で記録と一致) |
| `named`・`named` の value | raw の claim の `no_same_value` |
| 基準の先頭の pointer(T1・T2・T5) | 記録 `stop_reason` の `profile.P27.無改変.claim.pointers[0]` |
| P22 の注入後の先頭の pointer・`recomputed` | 記録 `stop_reason` の `profile.P22.注入後.claim`(T3 は `profile.P22.claim`) |
| 一致(基準)・一致(P22) | §2-3 の語(機械で 1 か所) |
| `named` の value = P22 の `recomputed` | `==`(どちらも None なら数えない) |
| 文の値(円) | P27 の注入後の claim の `value` × `UNIT_SCALE[unit]`(`unit` が表に無ければ None) |
| 比・帯・10 の冪 | §2-4(機械で 1 か所) |

無改変の 30 書類(P27 の `no_same_value` の行だけ。行ごと):

| 欄 | 出どころ |
|---|---|
| 書類・id・P27 の state・reason | 今回の無改変の出力 |
| `named`・value | raw の claim の `no_same_value`(無改変の捕捉) |
| P22 の state・reason・先頭の pointer・`recomputed` | 今回の無改変の P22 の出力(`RE.work_doc` の中で走る P22 を包みが拾う) |
| 一致(P22 の先頭) | §2-3 の語 |
| fresh の P26 の `名指した fact` | 記録 `fresh` の `動いた行` の同じ (書類, id) の `dossier.P26.名指した fact`(無ければ None) |
| 一致(fresh の P26) | `named` と字で同じか |
| 文の値・比・帯 | claim の `value` × 倍率、§2-4 |

書類ごと: 無改変の P27・P22 の 4 state(W-2)、P27 の `no_same_value` の行数、捕捉の回数。記録の全体: 材料の sha256(取得の記録と一致)、配線の門 W-1〜W-3 の数、engine の sha16 6 本、`DEFAULT_PROFILE`、HEAD、封の commit、cache の件数(開始時・終了時)、所要秒、読んだ入力の sha256(`stop_reason_2026-10-29.json`・`fresh/fresh_2026-10-21.json`・`fresh/fetched_2026-10-21.json`・`p27/regress97_2026-10-27.json`・`default_p27_2026-10-28.json`)、`key_leaks`。

**記録に書ける欄は id・型・state・reason・pointer の字・値・比だけ(span・原文・文の字は書かない)。** `named` は pointer の字と同じ形(`xbrl:<接頭辞>:<名前>@<context>`)で、提出者別の接頭辞を含みうる(記録にだけ持ち、文書には書かない)。

### §2-3 一致の語(機械で 1 か所。§3 の予測はこの語で書く)

`named`(字)と照らす先頭の pointer `h`(基準の先頭、または P22 の注入後の先頭)から、次の順で 1 つに決める:

| # | 条件 | 語 |
|---|---|---|
| 1 | `named` が None(raw に鍵が無い・reason が `no_same_value` でない) | **(named なし)** |
| 2 | `h` が None(基準が無い(T3)・pointers が空) | **(照らす先なし)** |
| 3 | `named == h`(字の完全一致) | **(同じ)** |
| 4 | 要素(`xbrl:` の後ろを最初の `@` で切った前)が同じで context が違う | **(context だけ違う)** |
| 5 | context が同じで要素が違う | **(要素だけ違う)** |
| 6 | 両方違う(`h` が `xbrl:` で始まらない場合を含む) | **(両方違う)** |

要素と context の切り方は止めた理由の script の `split_pointer`(`SR.split_pointer`)をそのまま使う(自分で書かない)。

### §2-4 比(機械で 1 か所。判定には使わない)

- 比 `r` = |文の値(円)| / |`named` の value|。`named` の value が None か 0、または文の値が None なら `r` は None(「比なし」)。
- 帯(`r` から 1 つ): **(15% 以内)** 0.85 ≤ r ≤ 1.15 / **(2 倍以内)** 0.5 ≤ r < 0.85 または 1.15 < r ≤ 2 / **(10 倍以内)** 0.1 ≤ r < 0.5 または 2 < r ≤ 10 / **(10,000 倍以内)** 0.0001 ≤ r < 0.1 または 10 < r ≤ 10,000 / **(10,000 倍超)** それ以外(0 < r < 0.0001 または r > 10,000)。帯の端を 10 の 3 乗に置かないのは、T2 の単位の差し替え(千円 ↔ 百万円・円)がちょうど 10 の 3 乗に落ちて、書かれた数の丸めで端の両側に割れるため。
- 10 の冪に近い: `k = round(log10 r)` として |log10 r − k| ≤ 0.01 なら真(`k` も記録)。
- 文の値は P27 の注入後(無改変は P27)の claim の `value` × `UNIT_SCALE[unit]`。engine の `target` と同じ数かは確かめない(P27E の B が名指しに移した行数との突き合わせ UF-13 が、同じ数かの間接の確かめになる)。

### §2-5 集計の表(診断の文書の `<!-- 門:start 名前 -->` の中。門が記録から作り直す)

1. `pred`(先頭): §3 の予測の当否。
2. `wiring`: W-1(i)(ii)・W-2・W-3 の数。`engine`: sha16・DEFAULT_PROFILE・HEAD・封の commit・cache・key_leaks。
3. `agree`: 型(T1・T2・T5・計)× 一致(基準)の 6 語の行数。T3 × 一致(P22)。T1・T2・T5 × 一致(P22)。
4. `value`: 型 × 「`named` の value = P22 の `recomputed`」の真・偽・数えない。
5. `plain`: 無改変 30 書類の P27 の `no_same_value` の行数(書類ごとの最小・最大・計)、`named` 在り、P22 の state・reason の分布、一致(P22 の先頭)の語の分布、fresh の P26 の `名指した fact` との一致・不一致・fresh に無い、fresh の P26 の `no_same_value` の集合との差(足りない・余り)。
6. `ratio`: 型(T1・T2・T5・T3・無改変)× 帯の行数と、10 の冪に近い行数(T2 は `k` の分布も)。比なしの行数。
7. `elements`: (同じ)の行の `named` の要素名の上位 10(提出者別の接頭辞は「(提出者別の要素)」の 1 行)、接頭辞の種類、期 × member の有無(止めた理由の便 §2-5・§6-5 の切り方。`SR.split_pointer`)。(context だけ違う)・(要素だけ違う)・(両方違う)の行は、`named` と `h` の期・member の有無の対を並べる(字は書かない)。
8. `examples`: 語ごとに先頭 3 行まで(位置で呼ぶ。`書類 n・型の k 番目`、型・語・帯)。

## §3 事前予測(欄ごと・外れうる形・外れ方つき。§6 の下調べより前に固定)

予測の土台(§0 の範囲で見たもの): P22 が名指した fact と P26・P27 が名指さなかった fact は、`recipes.py` の最後の枝の同じ `cur[0]` である(§0-3)。記録では P22 の注入後の先頭 = P27 の基準の先頭が 126 / 126 なので、P27 の `cur[0]` が P22 の `cur[0]` と同じなら、`named` = 基準の先頭も 126 / 126 になる。違いうるのは、`cur` を選ぶ手前の規則(P24 の枠の読み直し `other_frame`、P26 の G1・G3・G4、P27 の C1〜C3)が P27 で別の fact を `cur[0]` にする行で、その場合は要素が同じで context(枠・member)だけ違う形になると見る(要素が違う形は、主語の読みが変わる行で、少ないと見る)。T3 は主語が作り物で、P22 が名指した fact(= `cur[0]`)と同じ fact を P27 も名指さなかったと見る。無改変は P26 の `no_same_value` 297 行から 1 行が C2・C3 系の `target_or_plan` に移って 296 と見る。比は、T1 は元の値 ± 小さい数、T2 は 10 の冪、T5 は 1/10〜10 倍で、P27E の B が T5 の 4 行(`ed615b5`)・無改変の 24 行を 15% 以内で名指しに移したことから、15% 以内の行数はその数に近いと見る。T3 は 37〜400 円で、fact は円の数なので比は極端に小さいと見る。

| # | 欄 | 予測 | 外れ方 |
|---|---|---|---|
| **UF-1** | 配線の門 W-1(§2-1) | (i) 前の便の門 **741 / 741**・id の集合が同じ・`注入の件数` **120 / 120**、(ii) P27 の注入後の claim が記録 `stop_reason` と **741 / 741**(state・reason・pointers の欄ごとも 741 / 741) | 1 つでも違う(止める。観測を書かない) |
| **UF-2** | 配線の門 W-2(§2-1) | 無改変の P27 の 4 state が `regress97` と **30 / 30**、和が `default_p27` S3 の `既定の 4 state`(2,194・250・787・692)と一致、P22 の 4 state も **30 / 30** | 1 つでも違う(止める) |
| **UF-3** | 配線の門 W-3(§2-1) | 捕捉 注入後 **741**・無改変 **30**、id と reason の照合 **737 / 737**(claim が None の 4 行を除く)、raw に `no_same_value` の鍵が在る行 = reason が `no_same_value` の行 = 注入後 **156**(T1 2・T2 32・T5 92・T3 30)、鍵と reason が食い違う行 **0** | 1 つでも違う(止める) |
| **UF-4** | `named` の在り方(注入後 156 行) | `named` が `xbrl:` で始まる字 **156 / 156**、value が None でない数 **156 / 156**、value が 0 の行 **0** | どれかが違う |
| **UF-5** | 一致(基準)=(同じ)(型別) | T1 **2 / 2**・T2 **29 以上 32 以下**・T5 **85 以上 92 以下** | どれかが幅の外(下に外れたら、P27 が `cur[0]` に別の fact を選ぶ行が見立てより多い) |
| **UF-6** | 一致(基準)が(同じ)でない行(T1・T2・T5 の計)とその中身 | 計 **0 以上 10 以下**。そのうち(context だけ違う)が(要素だけ違う)+(両方違う)以上。(named なし)・(照らす先なし)は **0**(違う行が 0 なら中身は判定しない) | 11 以上、または要素の違いが context の違いより多い、または(named なし)・(照らす先なし)が 1 以上 |
| **UF-7** | T3 30 行 | `named` 在り **30 / 30**、一致(P22 の注入後の先頭)=(同じ)**27 以上 30 以下** | どちらかが幅の外 |
| **UF-8** | `named` の value = P22 の注入後の `recomputed`(一致が(同じ)の行。T1・T2・T5・T3 の計) | **100%**(数えない行 0) | 1 行でも違う |
| **UF-9** | 無改変 30 書類の P27 の `no_same_value` | 行数 **290 以上 300 以下**(見立て 296)、`named` 在り **100%**、その行の P22 は VALUE_MISMATCH・pointers 空でない **100%** | どれかが幅の外 |
| **UF-10** | 無改変: P27 の `no_same_value` の (書類, id) の集合 と fresh の P26 の `no_same_value` の集合の差 | fresh に在って P27 に無い **1**(`regress97` の `no_same_value` → `target_or_plan` の 1 行)、P27 に在って fresh に無い **0** | どちらかが違う |
| **UF-11** | 無改変: 一致(fresh の P26 の `名指した fact`)と 一致(P22 の無改変の先頭) | fresh と(同じ)が **97% 以上**(fresh に無い行は分母から除く)、P22 の先頭と(同じ)が **95% 以上** | どちらかが未満 |
| **UF-12** | 比の帯(注入後 156 行。型別) | T1: (15% 以内)+(2 倍以内)**2 / 2**。T2: 10 の冪に近い **32 / 32**、(10,000 倍超)**27 以上 29 以下**、(10,000 倍以内)**3 以上 5 以下**、(10 倍以内)以下の 3 帯 **0**。T5: (15% 以内)**3 以上 5 以下**、(2 倍以内)+(10 倍以内)**85 以上 89 以下**、(10,000 倍以内)+(10,000 倍超)**0 以上 3 以下**。T3: (10,000 倍超)**24 以上 30 以下**。比なし **0** | どれかが幅の外 |
| **UF-13** | 比の帯(無改変の P27 の `no_same_value` の行) | (15% 以内)**23 以上 26 以下**(P27E の B が名指しに移した 24 と突き合わせ)、比なし **0 以上 3 以下** | どちらかが幅の外(15% 以内が 24 から離れたら、私の「文の値」が engine の `target` と違う) |
| **UF-14** | (同じ)の行の `named` の接頭辞・context(注入後 T1・T2・T5) | 標準の接頭辞 **85% 以上**、期が CurrentYear(Duration・Instant)**90% 以上**、member ありのうち単体の member が **全部**(member ありが 0 なら判定しない) | どれかが外れる |

- UF-5〜UF-8 が問い 1、UF-9〜UF-11 が問い 2、UF-12〜UF-13 が問い 3 への予測。UF-1〜UF-3 は配線で、外れたら観測を書かない。
- UF-5 と UF-7 と UF-11 が同じ向き(P27 の `cur[0]` が P22 と別)に外れたら、見立ての偏り(「最後の枝の手前は profile で変わらない」)として診断の文書に書く。
- UF-12 の T2 は §0-2 の単位の対からほぼ決まる(当たって当然の欄)。UF-12 の T5 の (15% 以内) と UF-13 は、engine の `target` の数の作り方(`claim_scale`・丸め)を見ていないので外れうる。
- 予測を 0 と書いた欄は「engine がその形を持たない」の主張ではない。この 741 行と 30 書類の観測に限る。
- 各型の engine の直し方・出力に出す是非はこの封に書かない(診断だけ)。

## §4 言えないこと・限界(封の時点で分かっているもの)

1. **「同じ」は字の一致であり、人の目は入らない。** `named` が基準の先頭と同じでも、その fact が文の言う数の出所として正しいかは測っていない(基準は「無改変の P22 で GROUNDED」の claim で、基準そのものの結び付きが正しいかも測っていない。止めた理由の便 §4 の 1 と同じ)。
2. **出力に `named` を出す変更の是非は、この便で決めない。** 出すと「止めたが候補はこれ」という形になり、客向けの報告の字も変わる(`adapters/` の変更 = 人間の承認)。この便はその判断の材料(取り戻せる行数と代価の側の行数)を数えるだけ。
3. **無改変の候補の正しさは測れない。** 無改変の `no_same_value` の行は正解が無い(前の便の読みでは「正しい文 335 / 337」= 文は正しく、engine が名指さなかっただけ)。`named` を出せば、正しい文にも「候補」が付く。その数(UF-9)は代価の側の数で、良し悪しの数ではない。
4. **P27E は測らない。** 741 行で P27 と語が変わるのは T5 の 4 行だけ(`ed615b5`)。無改変の 24 行は `regress97` の記録で足りる。
5. 比は「文の値 / |named の value|」で、engine の `target`(`claim_scale`・丸め・符号の扱い)と同じ数とは限らない。UF-13 で間接に確かめるだけ。比は判定に使わない(B の幅 0.15 が適切かは測らない)。
6. 30 書類・741 行・1 書類あたり型ごとに 40 件までの `IJ.select` の順の観測である。他の書類・他の site で同じ分布になるとは言えない。Core 全体の振る舞いを断定しない。
7. `cur[0]` が P22 と P27 で同じかを、engine の中の変数で直接は見ない(`_RawTap` は raw の claim を拾うだけ)。`named` と P22 の先頭の字の一致から間接に読む。
8. 仮説は測るまで断定しない。読みは無い(席は呼ばない。人の目も入らない)。観測は全部 engine の出力と記録からの機械の値。
9. 所要時間は前の便(6 profile・30 書類・`--procs 6` で 960 秒)と同じ程度の見込み(P27 の捕捉は engine を増やさない)。時間は症状で、目標ではない。途中で止まったら記録を書かない。

## §5 file と順序

1. **この封**(文書だけ)。本線へは `docs/XBRL_UNNAMED_FACT_DIAG_SEAL_2026-10-29.md` として司令塔が写して commit する(scratchpad の file と byte 一致)。封の commit が script・記録・文書・門のどの commit よりも前であること(順序の門は commit の順で見る)。docID・claim の id・ラベルを含まない。
2. 診断の便(1 commit。独立監査 GO の後):
   - script `measure/xbrl_unnamed_fact_2026-10-29.py`(§2)。出力が既に在れば測り直さない。`--docs`・`--procs`・`--out` を持つ。一致の語(§2-3)・比と帯(§2-4)はそれぞれ 1 つの関数に置く。`verify_raw` の包みは返り値を変えず、`RE.work_doc` の後で元に戻す(戻せていなければ止める)。
   - 記録 `fixtures/xbrl/unnamed_fact_2026-10-29.json`(docID と claim の id を持つ。行は 1 行 1 件の compact JSON(前の便の `dump_record` と同じ形))。§2-2 の欄、配線の門 W-1〜W-3、engine の sha16 6 本、HEAD、封の commit、cache の前後、所要秒、読んだ入力 5 つの sha256、`key_leaks`(`FR.key_leaks` を通す)。
   - 文書 `docs/XBRL_UNNAMED_FACT_DIAG_2026-10-29.md`(節立て: 予測の当否(先頭)→ 既存の記録で足りなかった → 配線 → 観測(§2-5 の表。行ごとの表は書かない。位置で呼ぶ例は語ごとに 3 行まで)→ 判定(§0-1 の 3 つの問いへ)→ 仮説 → 言えないこと → 次に測ること(§7 の 2 つの候補を並べ、どちらを勧めるかは書かない)。表は `<!-- 門:start 名前 -->`〜`<!-- 門:end -->` の内側。門の外の散文は数を持たない(持つ行は【門なし】)。docID・claim の id・ラベル・提出者別の要素名・禁止語(止めた理由の門の `FORBIDDEN` の 5 語)・code fence を書かない)。
   - 門 `tests/measure/test_xbrl_unnamed_fact.py`((a)〜(j) の型は `tests/measure/test_xbrl_stop_reason.py` と同じ): (a) 記録の 741 行の id が `fresh_2026-10-21.json` の `注入の行` の id と順も集合も同じ(字で留めない)、型別の数が同じ (b) 配線の門 W-1〜W-3 が記録の数で通っていて、P27 の注入後の claim を `stop_reason_2026-10-29.json` と門が自分で比べ直して 741 / 741、W-2 を `regress97` と `default_p27` で門が自分で比べ直す、W-3 の「鍵が在る行 = reason の行」を門が数え直す (c) 文書の表を記録から作り直して 1 行も違わない (d) UF-1〜UF-14 の当否を記録から求め(幅は封の表の字から読む。字で留めない)、封の字(欄・予測・外れ方)と文書の当否の字が一致 (e) 一致の語(6 語)・帯・10 の冪・要素名の切り出しを、記録の欄(`named`・pointer の字・value・比)から別の書き方で求め直して一致 (f) engine の sha16 を `ENGINE_AT_MEASURE`(字で留める)と `ENGINE_DECLARED`(宣言された遷移。今は空)で留める。**行頭に `ENGINE_LATER`・`UNTOUCHED`・`PIN_DEF`・`LATER_ENGINE_COMMITS`・`FROZEN_LATER` を定義しない** (g) 偽物で赤: 記録の `named`・value・比・一致の語・配線の旗を 1 か所変えると (b)(c)(e) が赤、文書の表の 1 字で (c) が赤、封の予測の 1 字で (d)(c) が赤、文書に提出者別の接頭辞の字を 1 つ足すと (h) が赤 (h) 封と文書に 30 書類の docID・記録の claim の id・提出者別の接頭辞の字が無い (i) 封の commit が script・記録・文書・門の commit より前 (j) 記録が持つ読んだ入力 5 つの sha256 がいまの file と一致。
   - `tests/measure/test_xbrl_fresh_seal.py` の `LATER_NAMING_FILES` に記録・script・門の 3 つを足す(日付つきの注記。既存の並びは変えない。文書と封は docID を持たないので足さない)。
   - `tests/measure/test_xbrl_inject_harness_review.py` の `LATER_HARNESS_FILES` に script 1 行: path `measure/xbrl_unnamed_fact_2026-10-29.py`・役「使う側」・届いたことの確かめ「有」・根拠の関数 `run_doc`・根拠の字 `r = RE.work_doc(a)`・日付 `2026-10-29`(script の `run_doc` の中にその 1 行を置く。check「有」の中身は W-1(ii) = 741 行の id と claim を記録 `stop_reason` と読み合わせること)。
   - 覆い: `python3 measure/suite_coverage_2026-10-16.py --write` と `docs/SUITE_COVERAGE_2026-10-16.md` §2-1 の数(240 → 241)。
3. 凍結(木の sha256 の一覧)→ 独立監査(`step-auditor`。配線の門を自分で走らせ直す(`--docs` で一部でもよいが、走らせた行は記録と byte 一致を見る)・一致の語と帯を別実装で求め直す・変異 (g))→ GO → commit(パス指定)。監査中は木を触らない。
4. engine の直し・出力の形の変更・台帳 `FACTS_FOR_BUYERS` への行はこの便に入れない(診断の後、別の封で決める)。

## §6 下調べの観測(予測の後。scratchpad の clone。正本でない。0 USD)

§3 を書いて file を保存した後に(予測を固定 2026-10-29 21:48:42 JST。その時点の file 全体の sha256 `d0811c47aa1a531890508a5903ad4f77f46668c9ca5c2c57eb5bc7cb46040540` は `probe/mtime_seal_predictions.txt`、写しは `probe/seal_at_prediction.md`)、§2-1 の配線を先頭の 5 書類で試した(clone `probe/clone`、HEAD `14771a6`。下調べの script `probe/scripts/probe_unnamed_fact_2026-10-29.py`(sha256 `1015a80fad8d424a34cbe712a3fa9fe12ed3faf1f3553b90ede69e993d0ab1a8`。clone の `audit-core/measure/` に置いて走らせた写し)→ `probe/probe5.json`・`probe/probe5_stdout.txt`。走らせ 21:51:12〜21:55:01 JST は集計の書き出しで止まり(集計の辞書の鍵が tuple。engine の走らせは終わっていた)、鍵を字に直して 21:55:17〜21:59:11 JST に走らせ直した。`probe/mtime_probe_start.txt`・`probe/mtime_probe_observed.txt`)。**§0〜§5 と §7 の字は変えていない**(この節の前までの字と §7 は、予測を固定した写しと byte 一致。`probe/seal_prefix_check.txt`)。

ここの数は下調べの数で、正本は §5 の記録と門が出す。**UF-1〜UF-14 の当否は本番の記録から門が求める。** ここに書く見立ては、この時点のもので、本番で変わりうる。

### §6-1 配線・環境

- 下調べの script は §2-1 のとおり、止めた理由の script を `_mod` で読み込み(SR)、`SR.RE.OBS = ("P27",)` だけ替え、`RE.LB.verify_raw` を返り値を変えない包みに実行中だけ替えて `RE.work_doc` を書類ごとに呼んだ。clone の中の既存の script は触っていない(clone の `git status` は下調べの script 1 つだけが未追跡)。engine の sha16 6 本は記録 `stop_reason` と同じ(script の先頭の照合で止まらなかった)。
- W-1(5 書類・131 行): 前の便の門の 4 欄 **131 / 131**、`注入の件数` 20 / 20 組。P27 の注入後の claim が記録 `stop_reason` と全欄 **131 / 131**(state・reason・pointers の欄ごとも 131 / 131)。
- W-2(5 書類): 無改変の P27 の 4 state が `regress97` と **5 / 5**、P22 も 5 / 5(`default_p27` S3 の和は 30 書類でだけ照らす)。
- W-3: P27 の注入後の捕捉 **131** = 行 131、無改変の捕捉 5。id と reason の照合 129 / 129(claim が None の 2 行を除く)。raw に `no_same_value` の鍵が在る行 **28** = reason が `no_same_value` の行 28、食い違い 0。無改変も鍵 74 = reason 74、食い違い 0。
- cache: 開始 `edinet/` 281・`edinet-fresh-2026-10-21/` 40 → 終了 281・40(この封を書く前(21:4x JST)と、全部の後にも同じ数を数えた)。`/tmp` に file を足していない(TMPDIR と PYTHONPYCACHEPREFIX は probe の下)。`edinetdb-p27/` は開いていない。鍵の値は読んでいない。
- 所要: 5 書類を 5 process で 233 秒(書類ごと 180・58・233・88・175 秒)。止めた理由の便の下調べ(4 profile の観測で 207 秒)と同じ程度。

### §6-2 観測(5 書類・131 行のうち P27 が `no_same_value` の 28 行と、無改変の 74 行。位置と集計だけ)

- 28 行の型: T1 **0**・T2 5・T5 18・T3 5(T1 の `no_same_value` 2 行は後ろの書類に在る)。
- `named` 在り **28 / 28**(全部 `xbrl:` で始まる字、value は数で 0 の行 0)。
- **一致(基準)は(同じ)が T2 5 / 5・T5 18 / 18。T3 の 一致(P22 の注入後の先頭)も(同じ)5 / 5。** 一致(P22)は T2・T5 でも 23 / 23。(context だけ違う)・(要素だけ違う)・(両方違う)・(named なし)・(照らす先なし)は 0。
- **`named` の value = P22 の注入後の `recomputed` が 28 / 28**(T3 の 5 行を含む)。
- 比の帯: T5 (15% 以内)1・(2 倍以内)4・(10 倍以内)13(比は 0.112〜9.57)。T2 (10,000 倍超)4・(10,000 倍以内)1。T3 **(10,000 倍以内)5**(比 0.00018〜0.0100)。比なし 0。
- T2 の 10 の冪: 近い 3(`k` = 5。千円 → 億円、基準が `direct_value`)、**近くない 2**(`k` = 2 と 8。基準が `derived_value` の行で、文の値は当期と前期の差、`named` の value は当期の残高(§0-3 の F3b の `cur[0]`)。比は 10 の冪 × (差 / 残高)になる)。
- T3 の比が 10,000 倍以内に収まった理由: 作り物の文の template は値を「百万円」で書く(`measure/lib/sites.py` の T3 の template 4 つの字は `%s百万円`)。engine の claim の `value` は 51,000,000 など(unit 円)で、§0-3 に書いた「円で書いた文」は読み違い(§6-4)。`named` は 5 行とも `jppfs_cor:NetSales` の当期(4 行は連結、1 行は単体の member)。
- 無改変(5 書類): P27 の `no_same_value` **74 行**(書類ごと 16・22・4・18・14 = fresh の P26 の `no_same_value` の書類ごとの数と同じ)。`named` 在り 74 / 74。P22 は VALUE_MISMATCH(reason None)74 / 74・pointers 空でない 74。一致(P22 の無改変の先頭)=(同じ)**74 / 74**。fresh の P26 の `名指した fact` と(同じ)**74 / 74**(fresh に無い行 0)。fresh の P26 の `no_same_value` の集合との差 0(`target_or_plan` に移った 1 行はこの 5 書類の外)。`named` の value = P22 の `recomputed` 74 / 74。
- 無改変の比の帯: (15% 以内)**4**・(2 倍以内)15・(10 倍以内)26・(10,000 倍以内)26・(10,000 倍超)3。**(15% 以内)の 4 行は、`regress97` の `P27 → P27E` で動いた行のうちこの 5 書類の 4 行と、(書類, id) の集合で同じ**(私の「文の値」と engine の `target` が、この 4 行と残り 70 行の境で同じ側に落ちた)。
- (同じ)の `named`(T2・T5 の 23 行): 接頭辞は標準が 23 / 23(`jppfs_cor` 23)。上位の要素名は `jppfs_cor:Liabilities` 3(上位 1 つ 3 / 23)。期は CurrentYear が 23 / 23(Duration 11・Instant 12)。member ありは 11 で、11 とも単体の member。

### §6-3 下調べの時点の当否の見立て(本番の門が 30 書類で求め直す)

| # | 見立て | 理由 |
|---|---|---|
| UF-1〜UF-3 | 当たりの側 | 131 / 131・5 / 5・捕捉と鍵の数が一致 |
| UF-4 | 当たりの側 | 28 / 28 |
| UF-5 | 当たりの側 | T2 5 / 5・T5 18 / 18(T1 は 5 書類に無い) |
| UF-6 | 当たりの側(違う行 0 なら中身は判定しない) | 違う行 0 |
| UF-7 | 当たりの側 | 5 / 5・5 / 5 |
| UF-8 | 当たりの側 | 28 / 28 |
| UF-9 | 当たりの側 | 5 書類で 74 = fresh の P26 と同じ。30 書類で 296 の見立て |
| UF-10 | 当たりの側 | 差 0(1 行は別の書類の見立て) |
| UF-11 | 当たりの側 | 74 / 74・74 / 74 |
| UF-12 | **T2 の「10 の冪に近い 32 / 32」と T3 の「(10,000 倍超)24 以上」は外れの側** | 基準が `derived_value` の T2 11 行は 10 の冪にならない(5 書類で 2 / 5)。T3 の文の値は百万円の桁で、5 書類の 5 行は全部 (10,000 倍以内)。T2 の (10,000 倍超) 27〜29 と (10,000 倍以内) 3〜5 は、derived の行の比が 10 の冪 × (差 / 残高)になるので、幅の内か外かは本番で決まる(5 書類では 4・1)。T5 の (15% 以内) は 1 / 18 で、92 行なら 5 前後(幅 3〜5 の上側) |
| UF-13 | 当たりの側 | 5 書類で 4 = `regress97` の 4 |
| UF-14 | 当たりの側 | 標準 23 / 23・CurrentYear 23 / 23・member あり 11 は全部単体 |

見立ての向き: 問い 1・2(UF-5〜UF-11)は見立てどおり「全部同じ」の側に寄っていた(5 書類で違う行 0)。問い 3(UF-12)は、注入の値の形(T3 の百万円、T2 の derived)を見立てが取り違えていた。外れたら外れのまま残す。

### §6-4 追記(2026-10-29、下調べの後。§2・§0-3 の補い。§3 の字は変えない)

- **W-3(ii) の字の補い。** §2-1 の「raw の `reason` が出力の `reason` と同じ」は、VALUE_MISMATCH の行では成り立たない(raw の claim は原本形式の `value differs(segment/other period?)` を持ち、`verify_document` は reason を None にする。止めた理由の封 §0-3)。本番の script の W-3(ii) は「行の claim の id が raw に在り、**(出力の reason が `no_same_value`)と(raw の reason が `no_same_value`)が同じ真偽**」で照らす(下調べはこの形で 129 / 129)。
- **§0-3 の T3 の値の形の訂正。** 作り物の文の値は 37〜400 を**百万円**で書く(円ではない)。UF-12 の T3 の予測はこの読み違いの上に立っていて、§3 の字のまま判定する。
- **T2 の基準が `derived_value` の行(11 / 32)の比。** 文の値は差(当期 − 前期)、`named` の value は当期の残高で、比は 10 の冪にならない。`ratio` の表に T2 を基準の form(記録 `stop_reason` の `profile.P27.無改変.claim.form`)で 2 列に分けて数える(UF-12 の判定は §3 の字のとおり 32 行の全部で行う)。
- 下調べの 5 書類は記録の `書類(出てくる順)` の先頭 5 件で、本番の 30 書類に含まれる。本番の記録はこの 5 書類についても作り直す(下調べの出力は使わない)。

## §7 この診断の結果で分かれる次の封の候補(2 つだけ。どちらを勧めるかは書かない)

1. **出力に `candidate` の欄を足す**(`adapters/xbrl/verify_document.py` の `CLAIM_FIELDS` に 1 欄。`no_same_value` の行だけ `named` と value を持ち、state・reason は変えない。`report_customer.py` の字も変わる。`adapters/` の変更 = 人間の承認。既存の golden・門の留めが動く)。材料: UF-5・UF-7(取り戻せる行数)と UF-9(無改変で候補が付く行数)。
2. **足さない**(名指しは P22 の形を profile で選ぶか、別の経路(`provenance` を読む外側の道具)で出す。engine 0 行)。材料: UF-9・UF-11(無改変の候補が正しい文にも付く数)と、§4 の 3(候補の正しさは測れない)。
