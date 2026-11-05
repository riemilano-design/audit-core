# 封: 前期の fact に結ばれた数に当期の値を入れる注入 T9(期の取り違えの率を測る。measure/ だけ。engine 0 行・lib 0 行)― 2026-11-06

前の便: 注入の型を広げる J(封 edad5cd・結果 955f2b9・台帳 077ca2a)。J の K-4 が外れた 1 行(T2_UNIT で「前期の2百万円」→「前期の2億円」に替えると、前期の手がかりがあるのに同じ要素の当期の fact を名指して GROUNDED)は偶然の 1 件で、**同じ型が何件あるかは数えていない**(J の結果 §4 の 4)。この封はその型を注入の型として作り、**率を測って人間に返す**(engine の直しは人間の決定)。

## §0 材料と決めごと

### §0-1 測った事実(この封を書く前に司令塔が 0 USD で数えた。engine の判定は 1 回も呼んでいない。script は scratchpad/numfix/pswap/probe_t6r.py)

1. engine の読み(読んだ事実。`adapters/xbrl/recipes.py` の `_direct_value_claim`): 304-306 で `_prior_cue`(数の直前 12 字の 前期・前期末・(同 など、直後の「から」)が真なら hits を **Prior1Year が先**になるよう並べ替えるだけで、当期の fact を外さない。308-311 の P22 `period_bind` は逆向き(手がかりが**無い**数から Prior1Year を外す)だけ。だから「前期の手がかりがある数の値が前期の fact に合わず当期の fact に合う」と、hits[0] = 当期の fact で GROUNDED になる(324 行)。J の 1 行はこの経路。
2. AI の文 200 本(`aiforms-2026-11-03`・`aiforms-f5-2026-11-03` の texts。切り替え `yen_scan_2026_11_05` 真)で、`S.identified_sites` の参照先が Prior1Year の数 363(CurrentYear は 627)。うち同じ要素の CurrentYear の fact が 1 件 342、単位が同じで両方正で値が違う 341、当期の値を元の字の形(複合は位の構造)で書けて元の字と違う **218 = site**(既存 28・万だけ 16・複合 174。本 59)。site の文に前期の語(前期・前年・前連結会計年度・前事業年度・前年同期・前年度)がある 209、数の直前 12 字にある 161、行頭が `|` の表の行 3。
3. 前例: J の T6_PRIOR(当期の数に前期の値)は対応が付いた 81 行で通した 0(P22 の period_bind が効く向き)。有報の 2026-10-20 の便では Core 自身が T6 を 6 / 10 GROUNDED にしていた。**逆向き(前期の数に当期の値)は 1 行も注入していない。**

### §0-2 司令塔の決定(人間の言葉「君に任せる進めて」2026-11-06 を、司令塔が次の課題を選ぶ委任と読んだ)

1. 選んだ課題はこの T9。理由: J が人間に返した 1 行の型に 218 の母集団があり、率を測らないと人間が engine の直しを決められない。measure/ だけで測れる。
2. **委任に含めないもの**(CLAUDE.md §2・§6): 期の手がかりを縛りにする engine の規則(この便の結果で人間が決める)・既定 profile P27・main へのマージ・O・規則 T・T5 の仕掛けの直し。
3. 型の名前 `T9_PRIOR_TO_CURRENT`。仕掛け `measure/inject.py`・`measure/lib/sites.py` は触らず、site と差し替えは測定 script が持つ(J の T6 の複合の写しと同じ作り。T6 の逆)。切り替えは process の中だけ真。土台 = 無改変で P30E が GROUNDED の claim、比較 = P29E、cap 型 1 本 10。
4. 行の欄に engine 自身の手がかりの判定 `recipes._prior_cue(text, start, end)` を持つ(読むだけ。engine の関数を呼んで真偽を記録する。engine は変えない)。

## §1 測り方の字

1. **site**(切り替え 真): `S.identified_sites(text, refs)` の (token, ref) のうち、ref の context が `Prior1Year` で始まり、同じ要素・context の `Prior1Year` を `CurrentYear` に替えた key の fact がちょうど 1 件(cur)、`cur["unit"] == ref["unit"]`、`cur["value"] > 0` かつ `ref["value"] > 0` かつ値が違う(`IJ.TOL`)、描いた字 `rendered = N.render_value(cur["value"] / factor, token)`(factor = `SC.scale_of(token.unit) or 1`)を `N.scan(rendered + (token.unit or ""))` で読み直すと token が 1 つで値 × factor が `cur["value"]` に一致(許容 `max(IJ.TOL, |cur| × 1e-9)`)、`rendered != token.text`。
2. **並べ替えと cap**: token の start の順に並べ、`random.Random("%s|%s|T9_PRIOR_TO_CURRENT" % (seed, 本の名前))` で shuffle、土台が P30E GROUNDED の site だけを先頭から cap 件(J の T6 と同じ)。「採った」= Σ min(cap, 作れる site)(J の追記 1 の読み)。
3. **注入**: 1 回に 1 件(`IJ.apply_edits`・`IJ.revert`。round-trip は止めずに数える)。差し替えは `[token.start, token.end]` を rendered に(単位の字は触らない)。
4. **行の欄**: id・型・形(既存 / 万だけ / 複合)・単位・基準の claim・P29E の土台に対応・round-trip・読み直し(注入後の文を `N.scan` して同じ start・同じ単位・意図した値の token)・届いた(元の字が基準の claim の span に在る かつ 注入後の claim(P30E)の span に rendered が在る)・先頭の位が減った・**engine の手がかり**(`recipes._prior_cue(text, token.start, token.end)` の真偽)・文に前期の語(§0-1 の 2 の 6 語のどれかが同じ行に在る)・基準の pointer の期(基準の claim の pointers[0] の context の先頭: CurrentYear / Prior1Year / 他 / なし)・注入後の pointer の期(P30E の claim。同じ分け方)・P29E・P30E(`TUNE.classify`)。文・span・会社名は持たない。
5. **本ごとの数え**: §0-1 の 2 の段(参照先 Prior1Year / CurrentYear が 1 件 / 単位同じ・正・値が違う / site)・形別・手がかり別・採った・土台の状態。
6. **集計**: J と同じ 2 本(全部の site での P29E・P30E の率、P29E にも対応が付く site だけの率)+ 形別・engine の手がかり別(真 / 偽)の内訳 + 通した行の注入後の pointer の期の内訳。

## §2 範囲

### §2-1 触る file
- 新しい: `measure/xbrl_pswap_2026-11-06.py`(inject・tally)、`tests/measure/test_xbrl_pswap_seal.py`・`tests/measure/test_xbrl_pswap_result.py`、記録 `fixtures/xbrl/pswap/inject_2026-11-06.json`、結果 `docs/XBRL_PERIOD_SWAP_RESULT_2026-11-06.md`。
- J の監査の宿題(J の封の追記 2 の 3)を同じ便で: `tests/measure/test_xbrl_jtypes_rows.py`(新しい file。J の script の行の欄 round-trip・読み直し・先頭の位が減った を、壊した差し替えで False になる例で固定。J の script は触らない)。T9 の script の同じ欄も、最初から壊した例の試験を持つ。
- 直す: `LATER_NAMING_FILES`(記録 1 つ)・`LATER_HARNESS_FILES`(script)・覆いの数。
- 触らない: `core/`・`adapters/`・`measure/inject.py`・`measure/lib/*`・前の便の script・記録・門。

### §2-2 触る枝の中の人間の決定(壊さない)
- 2026-10-20 P22 `period_bind`(封 XBRL_PERIOD_BIND_SEAL_2026-10-20): 手がかりが無い数は Prior1Year に値だけで結ばない。この便は engine を変えないので不変。測るのはその逆向き。
- 2026-10-08: 仕掛けは `adapters/xbrl` を使わない独立実装。T9 の site も `measure/lib` の走査・描きだけで作る。`_prior_cue` は**行の欄のため読むだけ**(site の選びに使わない。選びに使うと engine の見方で分母が決まる)。
- H の採用: E 系の注入の測定は切り替え 真で。lib の既定は 偽。種 `measure/SEED.json` は不変。

### §2-3 既存の門の留め
- engine・lib・inject.py・sites.py は 0 行なので留めは全部そのまま。記録の `lib の指紋` は H の記録と、`engine の指紋` は RB の記録と一致することを門で留める(J と同じ)。

## §3 事前予測(実装より先に固定。結果を見てから書き換えない)

| # | 欄 | 予測(幅) | 外れ方 |
|---|---|---|---|
| PS-1 | lib の指紋が H の記録と、engine の指紋が RB の記録と一致し、`inject.py`・`sites.py` が封の commit から 0 行 | 一致 | 1 つでも違えば外れ。記録を採らない |
| PS-2 | 真: 作れる site(計 / 既存 / 万だけ / 複合)と、うち engine の手がかり `_prior_cue` が真の site | 205〜230 / 25〜32 / 13〜19 / 165〜185、手がかり真 140〜180 | §0-1 の 2 と違う方向 = site の作りが下調べと違う |
| PS-3 | 真: 採った / うち土台 P30E が GROUNDED の行 / そのうち基準の pointer の期が Prior1Year の行の割合 | 185〜218 / 100〜200 / 85〜100% | 幅の外 |
| PS-4 | 真: 通した率(P30E。分母 = 対応が付く行) | 50〜95% | 50% 未満 = §0-1 の 1 の読みに無い縛りが効いている。95% 超も幅の外 |
| PS-5 | 真: 通した行のうち注入後の pointer の期が CurrentYear の行の割合 | 95〜100% | 幅の外 = 通した理由が当期の fact への落ちではない |
| PS-6 | 真: 対応が付く行のうち engine の手がかり真の行の割合、手がかり真の行の通した率 | 75〜100%、45〜95% | 幅の外 |
| PS-7 | 真: 通した行のうち届かない行 | 0 | 1 行以上 = 通した率に対応付けの数が混ざる |
| PS-8 | 真: P29E と P30E で判定が違う行 | 0〜3 | 4 以上 = 期の取り違えに丸め方の帯が効いている |
| PS-9 | 真: round-trip 不一致 / 読み直し不一致 / 先頭の位が減った行 | 0 / 0 / 0〜15 | 幅の外 |
| PS-10 | 真: 止めた行のうち 名指して原本(前期の fact を名指して VALUE_MISMATCH)の割合 | 60〜100% | 60% 未満 |

封の席の偏り: PS-4 は §0-1 の 1 の code の読みから置いた幅で、丸めの帯(当期の値を前期の数の字の形で描くので、帯の中に別の fact が在りうる)や主語の取れない数の枝(324 行の `subj` 無し)で下に外れうる。J の T7 の見立て(10〜40% → 1.8%)は大きく外れたので、この幅は広く置いた。

## §4 採用の基準

判定は記録から門が機械で求め、司令塔は覆さない。

- K-1: PS-1 が 一致。
- K-2: PS-9 の round-trip 不一致 0・読み直し不一致 0。
- K-3: 対応が付く行 ≥ 80(仕掛けが届いている)。
- K-4: PS-7 が 0(通した行は全部 届いた = engine の判定の数)。

K-1〜K-4 を全部満たせば「採用」= 記録を正本にし、README の P30E の推奨の行に**負けの側**として「前期と書かれた数に当期の値を入れた注入を P30E が通した率」を 1 文足し(文書だけ)、台帳に L・D・P の行を足す。通した率が高くても採用は採用(測った事実)で、engine の直し(期の手がかりを縛りにする規則)は人間が決める。K-4 が外れたら対応付けを直してから測り直す(engine の話ではない)。

## §5 測り方(全部 0 USD)

- `measure/xbrl_pswap_2026-11-06.py`: J の `xbrl_jtypes_2026-11-05.py` を importlib で読み込み(JT → NS → RM・NF・RUN・GEN・TUNE・IJ・N・S・SC を同じ instance で)、`NS.yen_scan_on()` の中で §1 のとおり注入。`--procs`・`--only <docID>`・`--out`。`tally` は封の字から幅を読んで PS-1〜PS-10・K-1〜K-4 を判定し 2 表を出す。
- 門 `tests/measure/test_xbrl_pswap_seal.py`・`tests/measure/test_xbrl_pswap_result.py`(J の門と同じ作り。欄は行と本ごとの数えから作り直す。変異で赤)。

## §6 言えないこと

1. 「通した」「止めた」は engine の state で、札(人の目)は無い。
2. site は仕掛けの `identified_sites` が前期の fact に 1 件で結べた数だけ。表の前期の列(規則 T の下書きの対象)はほぼ入らない(下調べで行頭 `|` は 3)。
3. 当期の値を前期の数の字の形で描くので、描いた値が偶然別の fact の帯に入ることがありうる(行の pointer の期の欄で分ける)。
4. 200 本は Claude の model 2 つが書いた文。前の便の率は作り直さない。
5. T9 は「前期と書かれた数に当期の値」の 1 型だけ。「当期と書かれた数に前期の値」は J の T6(通した 0 / 81)。

## §7 作法と順序

1. この封を commit(文書だけ。fresh_seal・facts・boundary の門を走らせてから)→ 測定 script 1 本と門 2 本 + J の宿題の試験(step-implementer、worktree)→ 変異 → 独立監査 GO → commit(パス指定)→ 記録 1 つ(本番)→ 結果の文書 → 門 → 監査 GO → commit → README の 1 文 → 台帳の行 → 監査 → commit。
2. 使わない: `git add -A`・`stash`・`reset`・`checkout`。cache に file を足さない。`edinetdb-p27`・`sgogi-coach-handoff` は開かない。鍵は全部 unset。

## 追記 1(2026-11-06。測定 script の実装の報告を受けて、本番の記録より先に書く。§1〜§7 と幅・基準は変えない)

実装の席(step-implementer)が封の字どおりに script を書き、使い捨ての 1 docID(10 本)と 2 docID(20 本)で注入後の claim に**対応が付いた行が 7 行中 3・25 行中 5** と報告した。席が debug で読んだ原因: 文が「前期は A、当期は B」の形で当期の値 B が同じ文に既に在るため、前期の数 A を B に替えると B の字を持つ claim が 2 件になり、`TUNE.claim_for_p27` が 1 件に決められず対応なしになる(J の T6 の複合で見た対応付けの限界と同じ型)。

1. **K-3 の扱い**: §4 の K-3(対応が付く行 ≥ 80)は字のまま判定する。外れれば「見送り」で、この便では対応付けを直して測り直さない(§4 が測り直しを書くのは K-4 の外れだけ)。結果の文書は、対応が付かない行の数と、席の読みが当てはまる行の数(同じ文に当期の値の字が在り claim が 2 件以上当たる行)を書く。注入後の文の位置で対応を付ける仕掛け(J の「届いた」の形)は、人間が求めれば別の封。
2. **PS-8 の「判定が違う行」** = P29E と P30E の**両方**で注入後の claim に対応が付き、結果の語が違う行(片方だけ対応が付かない行は判定が無いので数えない。J-7 より厳しい読み)。
3. **PS-3 の「採った」** = cap を基準で絞る前に掛けた数 Σ min(cap, 作れる site)(J の追記 1 と同じ読み)。「うち土台 P30E が GROUNDED の行」= 実際に注入した行。
4. **PS-6 の分母**: 手がかり真の割合は P30E で対応が付く行のうち、通した率の分母はその中の手がかり真の行。**分母 0 の率は None = 外れ**(PS-3・PS-4・PS-5・PS-6・PS-10。PS-5 の分母 = P30E で通した行)。
5. **PS-10 の「止めた行」** = 対応が付く行 − 通した行。「名指して原本」は `TUNE.LABEL_NAMED_ORIGINAL`。
6. **pointer の期** = 基準の claim(P30E の土台)と注入後の claim(P30E)の `pointers[0]` の context の先頭で CurrentYear / Prior1Year / 他 / なし の 4 語。記録に要素名は持たない。
7. **engine の手がかり**は注入前の文と注入前の token の start・end(単位の字を含まない)で `recipes._prior_cue` を呼ぶ。「〜から」の枝は単位つきの数では取れないので、手がかり真は engine の実際の見方より**少なく出る向き**に偏りうる(封の字を優先)。
8. **round-trip の不一致は止めずに数える**(判定は K-2)。site の読み直しは §1-1 の字どおり(token 1 つ・値 × factor が当期の値)。
9. 記録の限界は §6 の 5 つ + script の限界(上の 2〜8 の字)。
