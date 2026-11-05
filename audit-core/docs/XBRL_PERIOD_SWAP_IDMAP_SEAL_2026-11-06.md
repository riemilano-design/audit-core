# 封: 期の取り違えの注入 T9 の第 2 便 ― 注入後の claim を基準の claim の id で引く対応付けで 141 行を判定する(measure/ だけ。engine 0 行・lib 0 行)― 2026-11-06

前の便: T9(封 3a6aefa・追記 1 073adf9・script と門 e4ca583・記録と結果 d74f491・台帳 b984c47)。判定は「見送り」(K-3 外れ: 注入後の claim に対応が付く行 13 / 141)。対応が付かない 128 行は 128 / 128 が「注入後の値と同じ値の token が同じ行に既に在り、値で引くと claim が 2〜3 件当たって 1 件に決まらない」(d74f491 の結果 §3 の 4)。測れた 13 行は母集団に偏り、engine が期の取り違えを通す率は 13 行でしか言えない(10 / 13)。この封は**対応付けを位置(claim の id)で引いて 141 行全部を判定し、率を人間に返す**(engine の直しは人間の決定)。

## §0 材料と決めごと

### §0-1 測った事実(この封を書く前に司令塔が 0 USD で数えた。script は scratchpad/numfix/pswap2/probe_idmap.py。**注入後の claim の state・pointer は読んでいない**(予測を盲検に保つため、引けるかだけを数えた))

1. engine の claim の id は `N%03d` で文書の出現順(`adapters/xbrl/recipes.py` 818 行。`_direct_value_claim` が数ごとに番号を振る)。T9 の差し替えは数の字を同じ場所で替えるだけで数の個数を変えない。
2. T9 の記録(d74f491)の 141 行で、注入後の文を組み直して P29E・P30E の claim を作り、**基準の claim と同じ id の claim** を引くと: 141 / 141 行で id が在り、値が注入した値(円に直して `TUNE.same_number`)で、span に差し替えの字が在る(P29E も 141 / 141)。注入の前後で claim の数は 141 / 141 行で同じ。旧の対応付け(`TUNE.claim_for_p27`)が付いた 13 行は 13 / 13 で同じ claim。
3. 前の便の結果(読んでよい既知の数): 対応が付いた 13 行の P30E 通した 10・止めた 3(全部 名指して原本)、P29E 通した 9、両 profile で違う行 1、手がかり真 129 / 141、文に前期の語 137 / 141、round-trip 不一致 0・読み直し不一致 0・先頭の位が減った 1。

### §0-2 司令塔の決定(人間の言葉「君に任せる進めて」2026-11-06 を、司令塔が次の課題を選ぶ委任と読んだ)

1. 選んだ課題はこの第 2 便。理由: T9 の率 10 / 13 は分母が偏り、128 行が未測のままでは人間が engine の直しを決められない。仕掛け(`measure/inject.py`・`measure/lib`)も engine も触らず、測定 script の対応付けだけで測れる。
2. **委任に含めないもの**(CLAUDE.md §2・§6): 期の手がかりを縛りにする engine の規則(この便の結果で人間が決める)・既定 profile P27・main へのマージ・O・規則 T・T5 の仕掛けの直し・T7 の帯幅。`TUNE.claim_for_p27` そのものは変えない(前の便の記録と門が使う)。
3. site・並べ替え・cap・差し替え・行の欄は T9 の封 §1 のまま(同じ種・同じ cap なので行の id は T9 の記録と同じ 141 になるはず = Q-2 で留める)。変えるのは**注入後の claim の引き方**だけ。土台 = 無改変で P30E が GROUNDED の claim、比較 = P29E。

## §1 測り方の字

1. **注入後の claim の対応付け(id で引く)**: 注入後の文の claim のうち `id == 基準の claim の id` の claim を c とし、(ア) c が在る、(イ) `c["value"]` が在り円に直した値が注入した値と `TUNE.same_number` で一致、(ウ) `c["span"]` に差し替えの字 rendered が在る、の 3 つを全部満たすときだけ対応が付く(P29E・P30E それぞれ)。1 つでも欠ければ「対応が付かない」(行には残す。欠けた条件を欄に持つ)。
2. **旧の対応付けの欄**: 同じ行に `TUNE.claim_for_p27` の結果(付いた / 付かない。付いたら id が同じか)も持つ(前の便の 13 行との照らし。判定には使わない)。
3. **届いた**: 元の字が基準の claim の span に在る かつ 注入後の claim(P30E。id で引いたもの)の span に rendered が在る(= (ウ) と同じ字。欄は残す)。
4. **行の欄**: T9 の封 §1 の 4 の欄 + 対応の条件(ア)(イ)(ウ)の真偽(P29E・P30E)+ 旧の対応(付いた / 付かない / 同じ id)。engine の手がかりは T9 と同じく `recipes._prior_cue(text, token.start, token.end)` を読むだけ。文・span・会社名・pointer の字(要素名)は持たない。
5. **site・並べ替え・cap・注入・本ごとの数え・集計**: T9 の封 §1 の 1〜3・5・6 のまま(script は T9 の script を importlib で読み込み、site の関数・行の欄の関数をそのまま使う。T9 の script は触らない)。

## §2 範囲

### §2-1 触る file
- 新しい: `measure/xbrl_pswap_idmap_2026-11-06.py`(inject・tally)、`tests/measure/test_xbrl_pswap_idmap_seal.py`・`tests/measure/test_xbrl_pswap_idmap_result.py`、記録 `fixtures/xbrl/pswap/inject_idmap_2026-11-06.json`、結果 `docs/XBRL_PERIOD_SWAP_IDMAP_RESULT_2026-11-06.md`。
- 直す: `LATER_NAMING_FILES`(記録 1 つ)・`LATER_HARNESS_FILES`(script)・覆いの数。
- 触らない: `core/`・`adapters/`・`measure/inject.py`・`measure/lib/*`・`measure/xbrl_p27_tune_2026-10-27.py`・前の便(T9・J・H・RB・N)の script・記録・門。

### §2-2 触る枝の中の人間の決定(壊さない)
- T9 の封 §2-2 のとおり(P22 `period_bind` は不変・仕掛けは `adapters/xbrl` を使わない・`_prior_cue` は読むだけ・H の採用 = E 系は切り替え 真・種は不変)。
- 旧の対応付け `claim_for_p27` は前の便(RB・H・J・T9)の記録と門が使うので変えない。新しい引き方はこの script だけが持つ。

### §2-3 既存の門の留め
- engine・lib・inject.py・sites.py・T9 の script は 0 行。記録の `lib の指紋` は H の記録と、`engine の指紋` は RB の記録と一致することを門で留める(T9 と同じ)。

## §3 事前予測(実装より先に固定。結果を見てから書き換えない)

| # | 欄 | 予測(幅) | 外れ方 |
|---|---|---|---|
| Q-1 | lib の指紋が H の記録と、engine の指紋が RB の記録と一致し、`inject.py`・`sites.py`・T9 の script が封の commit から 0 行 | 一致 | 1 つでも違えば外れ。記録を採らない |
| Q-2 | 注入の行の数と、行の id の集合が T9 の記録(d74f491)と同じ | 141・同じ | 違えば site か種が違う |
| Q-3 | id で対応が付く行(P30E / P29E)と、注入の前後で claim の数が同じ行 | 141 / 141・141 | 1 行でも欠ければ §0-1 の 2 と違う |
| Q-4 | 旧の対応付けが付く行と、そのうち id で引いた claim と同じ claim の行 | 13・13 | 幅の外 = 前の便と同じ文を組めていない |
| Q-5 | 旧の対応付けが付いた 13 行の P30E・P29E の結果が T9 の記録と同じ行 | 13 / 13 | 1 行でも違えば engine の判定が決定的でない |
| Q-6 | 真: 通した率(P30E。分母 = id で対応が付く行 141)と、旧で付かなかった 128 行だけの通した率 | 55〜95%、50〜95% | 50% 未満 = 同じ行に当期の値が 2 つ在る文では engine が別の経路で止める。95% 超も幅の外 |
| Q-7 | 真: 通した行のうち注入後の pointer の期が CurrentYear の行の割合、engine の手がかり真の行の通した率 | 95〜100%、55〜95% | 幅の外 |
| Q-8 | 真: P29E と P30E で判定が違う行(両方に対応が付く行の中) | 0〜6 | 7 以上 = 丸め方の帯が効いている |
| Q-9 | 真: round-trip 不一致 / 読み直し不一致 / 先頭の位が減った行 / 届いた行 | 0 / 0 / 1 / 141 | 幅の外 |
| Q-10 | 真: 止めた行のうち 名指して原本(前期の fact を名指して VALUE_MISMATCH)の割合 | 60〜100% | 60% 未満 = 止め方が別(POINTER_NOT_FOUND など) |

封の席の偏り: Q-6 の 128 行の幅は、§0-1 の 1 の code の読み(前期の手がかりは順序にだけ効く)が「同じ行に同じ値の数が 2 つ在る文」でも同じに働くという見立てで置いた。engine に「同じ fact を 2 つの数に結ばない」規則があれば(読んでいない)下に外れる。T9 の 13 行の 76.9% は幅の中。

## §4 採用の基準

判定は記録から門が機械で求め、司令塔は覆さない。

- K-1: Q-1 が 一致。
- K-2: Q-9 の round-trip 不一致 0・読み直し不一致 0。
- K-3: id で対応が付く行(P30E)≥ 130。
- K-4: Q-5 が 13 / 13(旧で測れた行の判定が前の便と同じ = 対応付けを替えても engine の判定は不変)。

K-1〜K-4 を全部満たせば「採用」= 記録を正本にし、README の P30E の推奨の行に**負けの側**として「前期と書かれた数に同じ要素の当期の値を入れた注入を P30E が通した率(分母 141)」を 1 文足し(文書だけ)、台帳に L・D・P の行を足す。通した率が高くても採用は採用(測った事実)で、engine の直しは人間が決める。K-3 か K-4 が外れたら「見送り」で、対応付けの直しは別の封(この便では測り直さない)。

## §5 測り方(全部 0 USD)

- `measure/xbrl_pswap_idmap_2026-11-06.py`: T9 の `xbrl_pswap_2026-11-06.py` を importlib で読み込み(PS → JT → NS → RM・NF・RUN・GEN・TUNE・IJ・N・S・SC を同じ instance で)、`NS.yen_scan_on()` の中で T9 の site・並べ替え・cap・差し替えのまま注入し、§1 のとおり id で引く。`--procs`・`--only <docID>`・`--out`。`tally` は封の字から幅を読んで Q-1〜Q-10・K-1〜K-4 を判定し 2 表を出す(Q-2・Q-4・Q-5 は T9 の記録 `fixtures/xbrl/pswap/inject_2026-11-06.json` を読んで照らす)。
- 門 `tests/measure/test_xbrl_pswap_idmap_seal.py`・`tests/measure/test_xbrl_pswap_idmap_result.py`(T9 の門と同じ作り。欄は行と本ごとの数えから作り直す。対応の 3 条件と旧の対応の欄を壊した例で固定。変異で赤)。

## §6 言えないこと

1. 「通した」「止めた」は engine の state で、札(人の目)は無い。
2. id で引く対応付けは「数の個数が注入の前後で同じ」ことに頼る(Q-3 で留める)。個数が変わる注入(複合の字を別の形に替えるなど)には使えない。
3. site・cap・母集団は T9 のまま(表の前期の列はほぼ入らない。当期の値を前期の数の字の形で描く。200 本は Claude の model 2 つが書いた文)。前の便の率は作り直さない。
4. T9 は「前期と書かれた数に当期の値」の 1 型だけ。逆向きは J の T6(通した 0 / 81)。

## §7 作法と順序

1. この封を commit(文書だけ。fresh_seal・facts・boundary の門を走らせてから)→ 測定 script 1 本と門 2 本(step-implementer、worktree)→ 変異 → 独立監査 GO → commit(パス指定)→ 記録 1 つ(本番)→ 結果の文書 → 門 → 監査 GO → commit → README の 1 文(採用なら)→ 台帳の行 → 監査 → commit。
2. 使わない: `git add -A`・`stash`・`reset`・`checkout`。cache に file を足さない。`edinetdb-p27`・`sgogi-coach-handoff` は開かない。鍵は全部 unset。
