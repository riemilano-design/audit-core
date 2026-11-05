# 封: AI の文 200 本に注入の型を広げる J ― T2_UNIT・T6_PRIOR・T7_ROUND を切り替え 真で(measure/ だけ。engine 0 行・lib 0 行)― 2026-11-05

前の便: 読み取り N(封 48e7078・結果 dc2cfe7)・混ざる桁 RB(封 de23edc・結果 301d9f1)・注入の仕掛けの数の読み H(封 89afc79・結果 e93cf95)。AI の文への注入は F5 の便から 4 便続けて **T1_VALUE・T8_REL の 2 型だけ**で、記録の「限界」に「期・単位・主語の取り違えは注入しない」が残り、H の結果 §4 の 6 は「T2・T5 などの型に 万円 の token が入る影響は測っていない」を残した。この封は **P30E の推奨の根拠に、単位のずれ(T2)・前期の値(T6)・最後の桁 ±1(T7)を通した率を足す**。有報の原文では T2 が `fresh_2026-10-21.json`(T1・T2・T3・T5)、T6・T7 が `hybrid_s2_2026-10-20.json`(10 件ずつ)で測られているが、AI の文(E 系 profile)では 1 行も無い。

## §0 材料と決めごと

### §0-1 測った事実(この封を書く前に司令塔が 0 USD で数えた。engine の判定は 1 回も呼んでいない。script は scratchpad/numfix/jtypes/probe_sites.py・probe_sites2.py)

1. AI の文 200 本(`aiforms-2026-11-03`・`aiforms-f5-2026-11-03` の texts)で、仕掛けの site を token の種類別に数えた(切り替え `yen_scan_2026_11_05` を process の中で 偽 → 真)。token の種類: **既存**(`groups` が None)・**万だけ**(`groups` が 1 つ)・**複合**(`groups` が 2 つ以上 = 億+万・兆+億)・空白入り「5 万円」(`groups` None・unit 万円、200 本で 4。既存に含める)。

| 型 | 偽 | 真: 既存 | 真: 万だけ | 真: 複合 |
|---|---|---|---|---|
| T2_UNIT の site(`S.t2_sites`) | 8,028 | 8,032(円族 5,215・比率 2,810・時間 7) | 1,820(差し替え先は 円・千円・百万円・億円・兆円 の 5 つ) | 5,408(**site にしない**。差し替えは最後の位の単位だけを替えるので「12億3,456億円」になる) |
| T5_COINCIDENT の site(`S.t5_sites`) | **0** | 0 | 43 | 629 |
| T6_PRIOR の site(`IJ.t6_sites`) | 61 | 61 | 16 | 12(写しで数えると 272) |
| T7_ROUND の site(`IJ.t7_sites`) | 374 | 376 | 243 | 走らせると落ちる(写しで数えると 1,223) |

2. **T5 は注入しない**(数えて記録に持つだけ)。理由(読んだ事実): `S.t5_sites` の規模の篩 `lo <= o["value"] <= hi` は token の**書かれた単位の値**(1,234万円 → 1,234)と参照の**円の値**を比べ、`build_t5` は参照の円の値をそのまま token の単位で描く。円族の token には偶然一致の相手が作れず(偽で 200 本 0)、真の 672 は全部、相手の参照の単位が None か 円 の小さい値(万円 の token に対して)で、意味のある取り違えではない。直すには `measure/lib/sites.py` の篩と描きを円に直す仕掛けの変更が要る(別の封。この便では触らない)。
3. **複合 token の T6・T7 は仕掛けの外**: `IJ.t6_sites` は描いた字を `float()` に戻すので、先頭の位が落ちた 12 件(1億500万 → 9,700万 の形)だけが site になる。`IJ.t7_sites` の `_bump_last_digit` は `int("12億3,456")` で落ちる。どちらも測定 script の**写し**(複合だけ)で作る: T6 は描いた字を `N.scan(描いた字 + 単位)` で値に戻して前期の値と一致を見る。T7 は like の単位で値 ±1 を `N.render_value` で描き、位の数が減らない・元の字と違う・refs のどの値とも一致しない、を要る。**仕掛けができる token(既存・万だけ)は仕掛けの経路(`IJ.select`・`IJ.t6_sites`・`IJ.t7_sites`)のまま**、複合だけ写し(写しの乱数を仕掛けの乱数と混ぜない。混ぜると 200 本中 64 本で乱数の消費がずれた)。
4. 前例の率(比較の土台。母集団が違うので規則の効きの比較ではない): 有報 30 書類(`fresh_2026-10-21.json`、P26)T2 通した 5 / 263 = 全部「差し替えが基準の claim の文の外」(測定の対応付けの数。診断 `docs/XBRL_T2_PASS_DIAG_2026-10-28.md`)。有報(`hybrid_s2_2026-10-20.json`、2026-10-20 の Core)T6 を Core 自身が GROUNDED にした 6 / 10(前期の fact に値が実在する)・T7 0 / 10。AI の文 200 本の P30E(RB・H の記録)T1 0.4% / 0.0%・T8 2.7% / 0.1%。
5. T7 で期待する形(読んだ事実): 最後の桁 −1 は、切り捨てで書かれた数では「丸めた値の差の帯 2 倍(切り捨て側)」の中に入る(H の便で通した 1 件 10万円 → 9万円 と同じ形)。+1 は丸めの帯の外。符号は仕掛けの乱数が選ぶ。

### §0-2 司令塔の決定(人間の言葉「君に任せる進めて」2026-11-05 を、司令塔が次の課題を選ぶ委任と読んだ)

1. 選んだ課題はこの J。理由: H の結果 §4 の 6 と 4 便の「限界」に残った型を、engine も lib も触らずに measure/ だけで測れる。T7 は RB の「混ざる桁は両方の帯」の代価を T8 より鋭く当てる型(§0-1 の 5)。
2. **委任に含めないもの**(CLAUDE.md §6 の人間の決定): 既定 profile P27 の切り替え・main へのマージ・O を外す engine の変更・規則 T(engine。`docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-03.md` は下書きのまま)・T5 の仕掛けの直し(`sites.py`)・T7 の結果を受けた帯の変更(engine)。
3. 切り替え `yen_scan_2026_11_05` は H の採用のとおり**測定 script の process の中だけ 真**(lib の既定は 偽のまま。lib は 1 byte も変えない)。
4. 触るのは新しい測定 script 1 本・門 2 本・記録 1 つ・結果の文書 1 つ・台帳。`measure/inject.py`・`measure/lib/sites.py`・`measure/lib/numbers.py`・`measure/lib/scales.py`・`core/`・`adapters/`・前の便の script と記録は 0 行。
5. 土台と比較は H と同じ: 土台 = 無改変の文で **P30E** が GROUNDED の claim(`RM.base_status_rb`)、比較 = P29E((value, span, unit) が同じ claim があれば結ぶ)。cap は型ごと 1 本 10。

## §1 測り方の字(script が 1 通りに書ける形)

1. **T2_UNIT**: `IJ.select(text, refs, "xbrl", seed, 本の名前, cap, types=["T2_UNIT"])`。`S.t2_sites` は with の中だけ「`groups` が 2 つ以上の token を除く」版に差し替える(出るときは必ず戻す)。cap は採用に掛ける(基準で絞る前。T1 と同じ)。注入後の claim は `TUNE.claim_for_p27(claims, inj, 差し替え後の単位)`(`inj["detail"]["unit_after"]`。T2 は数の字が同じで単位が違うので、円に直す単位は後の単位)。
2. **T6_PRIOR**: `IJ.t6_sites(text, refs)` を、`S.identified_sites` を with の中だけ「複合を除く」版に差し替えて呼ぶ(既存・万だけ)+ 複合の写し(§0-1 の 3)。2 つを合わせ `random.Random("%s|%s|T6_PRIOR" % (seed, 本の名前))` で並べ替え(`IJ.select` の `erng` と同じ種)、土台が P30E GROUNDED の site だけを先頭から cap 件(T8 と同じく cap は基準で絞った後)。
3. **T7_ROUND**: `IJ.t7_sites(text, refs, random.Random("%s|%s|T7_ROUND" % (seed, 本の名前)))` を、`S.data_bearing_sites` を with の中だけ「複合を除く」版に差し替えて呼ぶ + 複合の写し(符号は `random.Random("%s|%s|T7_ROUND|複合" % (seed, 本の名前))` で [+1, −1] を並べ替えて先に選び、作れなければ逆側)。並べ替えと cap は T6 と同じ(種の字は T7_ROUND)。
4. 1 回に 1 件(`IJ.apply_edits`・`IJ.revert`。round-trip は止めずに数え、行の欄に持つ)。行の欄: id・型・形(既存 / 万だけ / 複合)・単位・単位の後(T2)・符号(T7)・基準の claim・P29E の土台に対応・round-trip・読み直し(注入後の文を `N.scan` して同じ start・意図した値の token が在る。T2 は同じ start・後の単位)・**届いた**(元の字が基準の claim の span に在る **かつ** 注入後の claim の span に差し替えの字が在る)・先頭の位が減った(T6・T7 の複合)・P29E・P30E(`TUNE.classify`)。
5. 本ごとの数え: token の種類別の数(既存・万だけ・複合・空白入り 万円)、型ごとの 作れる site(種類別)・採った・土台の状態(`RM.base_status_rb` の語)、site にしなかった複合の T2 の数、T5 の site(偽・真。真は相手の参照の単位の内訳)。文・span・会社名は持たない(禁止欄・key_leaks は前例の検査)。
6. 集計は H と同じ 2 本(全部の site での P29E・P30E の率、P29E にも対応が付く site だけの率)に、**型 × 形(既存 / 万だけ / 複合)** の内訳を足す。

## §2 範囲

### §2-1 触る file
- 新しい: `measure/xbrl_jtypes_2026-11-05.py`(inject・tally)、`tests/measure/test_xbrl_jtypes_seal.py`・`tests/measure/test_xbrl_jtypes_result.py`、記録 `fixtures/xbrl/jtypes/inject_2026-11-05.json`、結果 `docs/XBRL_INJECT_TYPES_RESULT_2026-11-05.md`。
- 直す: `tests/measure/test_xbrl_fresh_seal.py` の `LATER_NAMING_FILES`(記録 1 つ)・`tests/measure/test_xbrl_inject_harness_review.py` の `LATER_HARNESS_FILES`(script)・覆いの数(SUITE_COVERAGE §2-1・FACTS A-06〜A-09・SALES_SHEET・README.en)。
- 触らない: §0-2 の 4。

### §2-2 触る枝の中の人間の決定(壊さない)
- 2026-10-08(INJECTION_TOOL_AUDIT3): 仕掛けは `adapters/xbrl` を使わない独立実装。写しは `measure/lib/numbers.py` の描きと走査だけを使う。
- 2026-10-20(段 2): T6・T7 は `types` で名指したときだけ catalog に足す。`IJ.select` の既定の呼び出しの結果は 1 字も変えない(この便は `IJ.select` を T2 だけで呼び、T6・T7 は select の外で同じ種の乱数で並べる)。
- H の採用(e93cf95): E 系の注入の測定は切り替え 真で。lib の既定は 偽。
- 種 `measure/SEED.json` は不変。

### §2-3 既存の門の留め
- `measure/inject.py`・`measure/lib/*.py`・engine は触らないので、FROZEN・遷移・指紋の留めは全部そのまま。記録の `lib の指紋` は H の記録 `fixtures/xbrl/nscan/inject_2026-11-05.json` の `lib の指紋` と、`engine の指紋` は RB の記録 `fixtures/xbrl/rmix/inject_2026-11-04.json` の `engine の指紋` と一致することを門で留める。

## §3 事前予測(実装より先に固定。結果を見てから書き換えない)

| # | 欄 | 予測(幅) | 外れ方 |
|---|---|---|---|
| J-1 | lib の指紋が H の記録と、engine の指紋が RB の記録と一致し、`inject.py`・`sites.py` が封の commit から 0 行 | 一致 | 1 つでも違えば外れ = 測定の土台が変わっている。記録を採らない |
| J-2 | 真: 作れる site(種類別)T2 既存 / 万だけ / site にしない複合、T6 既存 / 万だけ / 複合、T7 既存 / 万だけ / 複合 | T2 7,900〜8,150 / 1,780〜1,860 / 5,300〜5,500、T6 55〜70 / 12〜20 / 250〜300、T7 360〜390 / 230〜260 / 1,150〜1,300 | §0-1 の 1 の数と違う方向に出れば、仕掛けの経路と写しの分け方が下調べと違う |
| J-3 | 真: 採った / うち土台 P30E が GROUNDED の行 | T2 1,700〜2,000 / 700〜1,300、T6 280〜349 / 150〜300、T7 1,500〜1,900 / 800〜1,400 | 幅の外 |
| J-4 | 真: 通した率(P30E。分母 = P30E が GROUNDED の site) | T2_UNIT 0.0〜1.0%・T6_PRIOR 0.0〜12.0%・T7_ROUND 10.0〜40.0% | 幅の外。T7 が上を超えれば「最後の桁の帯」を人間に返す材料。T6 が上を超えれば期の縛りが AI の文で効いていない |
| J-5 | 真: T7_ROUND の通した率は P30E が P29E より高い(P29E にも対応が付く site だけで) | 差 2.0 pt 以上 | 2.0 pt 未満 = RB の両方の帯は T7 では代価にならない |
| J-6 | 真: 名指して原本を返した率(P30E) | T2 55〜90%・T6 55〜95%・T7(止めた行の中で)50〜90% | 幅の外 |
| J-7 | 真: P29E と P30E で判定が違う行(P29E に対応が付く行)と、そのうち T7 の割合 | 10〜150 行・T7 が 80% 以上 | 幅の外 |
| J-8 | 真: T2 で通した行のうち「届いた」行 | 0 | 1 行以上 = engine が単位の誤りを通した(有報の便の T2 の 5 件は全部 届かない だった) |
| J-9 | 真: round-trip 不一致 / 読み直し不一致 / 先頭の位が減った行(T6・T7 の複合) | 0 / 0 / 0〜40 | 幅の外 |
| J-10 | T5 の site: 偽 / 真 / 真のうち相手の参照の単位が None か 円 でない site | 0 / 600〜750 / 0 | 幅の外 = §0-1 の 2 の読みが違う |

封の席の偏り: J-4 の T7 と J-5 は §0-1 の 5 の読み(−1 が 2 倍の帯に入る)から置いた幅で、切り捨てで書かれた数の割合と符号の乱数で大きく動く。J-3 の土台の率は T1・T8 の前例(採った → 土台 GROUNDED が 40〜71%)から置いた見立て。

## §4 採用の基準

判定は記録から門が機械で求め、司令塔は覆さない。

- K-1: J-1 が 一致(測定の土台が前の便と同じ)。
- K-2: J-9 の round-trip 不一致 0・読み直し不一致 0。
- K-3: 3 型の土台 P30E が GROUNDED の行の和 ≥ 1,800(仕掛けが届いている)。
- K-4: J-8 が 0(T2 で通した行は全部「届かない」= 測定の対応付けの数)。

K-1〜K-4 を全部満たせば「採用」= 記録を正本にし、README の P30E の推奨の行に T2・T6・T7 の通した率を 1 文足し(文書だけ)、台帳に L・D・P の行を足す。J-4 の T7 の上限を超えても採用はそのままで、「最後の桁 −1 は帯の中」を人間に返す(engine の帯の話)。K-4 が外れたら engine が単位の誤りを通した行を 1 件ずつ結果の文書に書き、人間に返す。

## §5 測り方(全部 0 USD)

- `measure/xbrl_jtypes_2026-11-05.py`: H の `xbrl_nscan_2026-11-05.py` を importlib で読み込み(RM・NF・RUN・GEN・TUNE・IJ・N・S を H と同じ instance で)、`NS.yen_scan_on()` の中で §1 のとおり注入。`--procs`・`--only`・`--out`。記録 `fixtures/xbrl/jtypes/inject_2026-11-05.json`。`tally` は記録から J-1〜J-10・K-1〜K-4 を封の字の幅で判定し、結果の文書の 2 表を出す。
- 門 `tests/measure/test_xbrl_jtypes_seal.py`(封の字と script の定数の一致・順序 封 ⊏ script・触らない file の不変・配線)・`tests/measure/test_xbrl_jtypes_result.py`(J と K を記録から機械で。結果の文書の 2 表を照らす。記録の検査(禁止欄・key_leaks・docID は LATER_NAMING_FILES の file だけ・cache の前後・lib と engine の指紋)。文書の検査(禁止語・【門なし】)。記録が無ければ skip)。**変異で赤になることを 1 本ずつ確かめる**。

## §6 言えないこと

1. 「通した」「止めた」は engine の state で、札(人の目)は無い。
2. T5 は注入しない(§0-1 の 2)。T3(原文に無い数の挿入)も注入しない(土台の claim が無く、H の集計の形に乗らない)。
3. 複合の T6・T7 は写しで作る(§0-1 の 3)。写しの site と仕掛けの site は母集団が違う。
4. T2 の「通した」は有報の便の診断のとおり測定の対応付けの数でありうる。行の「届いた」の欄で分け、K-4 で縛る。
5. 200 本は Claude の model 2 つが書いた文。
6. 前の便(RB・H)の率は作り直さない(記録は不変)。

## §7 作法と順序

1. この封を commit(文書だけ。fresh_seal・facts・boundary の門を走らせてから)→ 測定 script 1 本と門 2 本(step-implementer、worktree)→ 変異 → 独立監査 GO → commit(パス指定)→ 記録 1 つ(本番)→ 結果の文書 → 門 → 監査 GO → commit → README の 1 文 → 台帳の行 → 監査 → commit。
2. 使わない: `git add -A`・`stash`・`reset`・`checkout`。cache に file を足さない。`edinetdb-p27`・`sgogi-coach-handoff` は開かない。鍵は全部 unset。
