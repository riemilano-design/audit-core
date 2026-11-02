# 封: 「その他」の主語の結び直し O を engine に入れる(P28 = P27 + O。既定にしない)― 2026-11-02

2026-11-02。人間の指示「君に任せる課題解決に向けて進めて」(2026-11-02 夜。引き継ぎ `docs/XBRL_P27E_RERUN_HANDOVER_2026-11-02.md` §9 の「人間が決める」3 点と、出所のずれの名指しの便の結果からの 1 点を司令塔が決めてよい、の承認として引く。前例: 2026-10-20「君に任せる」= P22 段 1、2026-10-27「君に任せる」= P27 段 2 E の承認)。
**この承認の範囲は、旗 1 つ・profile 1 つ(P28。既定にしない)・`recipes.py` と `vocabulary.py` への挿入・試験と測定の script と記録・門の留めの遷移まで。** 既定の切り替え(`DEFAULT_PROFILE`)・既存の行の書き換え・人間の決定の行の字の変更は範囲の外(人間が決める)。

## §0 根拠と司令塔の決定

### §0-1 測った事実(commit 済みの記録と結果の文書から。新しい測定なし)

- AI の文 1 書類(`fixtures/xbrl/ai_prose_instance_2026-10-09.zip`、claim 412、札つき)の「その他 N 百万円」「その他の○○ N 百万円」の行は 12(`docs/XBRL_OTHER_RULE_2026-11-02.md` §2-2。封 `8d4cf3b`、記録 `fixtures/xbrl/other_rule_2026-11-02.json`)。measure 側の規則 R1(engine が結んだ要素の計算リンクの近傍の `Other…` 要素で、同じ期・engine の帯の中の fact がちょうど 1 つ)は 8 行を 1 つに決め、**8 / 8 が札の根拠の要素と合う**。制約なしの R0(書類の全部の `Other…` 要素)も **12 行とも R1 と同じ判定**(候補の数も同じ)。残り 4 行は候補 0(要素名が `Other` で始まらない項目: 投資その他の資産 2・その他の包括利益累計額 2)。
- 同じ 12 行の、いまの既定 **P27** での判定(`fixtures/xbrl/entry_output_ai_prose_p27_2026-11-02.json`。封 `35f624c` の再判定の記録): GROUNDED 3(N118 = `OtherComprehensiveIncome` で R1 と同じ fact、N162・N163 = `InvestmentsAndOtherAssets`)、VALUE_MISMATCH 3(N081・N145・N239。別の要素の前期の fact を指す)、POINTER_NOT_FOUND `no_same_value` 6(N080・N144・N213・N238・N290・N299。pointers は空)。P27 でも「その他」の VALUE_MISMATCH 9 行(P16 基準)で GROUNDED になった行は 0(`docs/XBRL_P27E_RERUN_2026-11-02.md` M-6)。
- 期の印の便(`docs/XBRL_PERIOD_MARK_2026-11-02.md`)の「engine の期の取り違え」8 行のうち、P27 では 5 行が既に前期の fact を指し、残り 3 行(従業員数 2・借入金の和 1)は期を直しても値が合わない(同 §6)。R1 は N081・N145 を期も含めて正す。
- 出所のずれの名指しの段 1(`fixtures/xbrl/prior_pairs_2026-11-02.json`)で、前年と翌年の有報で値が違う要素の名の上位は `OtherNetOpeCF` 16・`OtherNOI` 10・`OtherNOE` 8 = 有報の文で `Other` 系の要素は頻出(「その他」の数は書き手が書く)。
- engine は要素の近傍(計算リンクの親・子・兄弟)を持たない(`instance.load_instance` は facts・contexts・textblocks・names だけ。`_cal.xml` は読んでいない)。R1 を engine に入れるには `instance.py` に linkbase の読みを足す必要がある。

### §0-2 司令塔の決定(2026-11-02 夜。根拠は §0-1 の数だけ)

1. **「その他」の規則を engine に入れる → 本便。** 規則は **R0 の形**(書類の全部の `Other…` 要素から、同じ期・member なし・円・engine の帯の中の fact がちょうど 1 つ)で入れる。R1 の近傍は engine に無く、AI の文では R0 = R1 だった。近傍が要るかは、本便の 97 書類の測定で「R0 で決まった行のうち R1(measure 側で計算リンクを読む)でも同じ fact が 1 つ」の割合を測って判断する(§3 N-6)。
2. **期の印(「(同」「前期末」)の規則 → 今は入れない。** P27 で動く見込みが 0〜3 行(§0-1 の 3 つ目)で、有報の原文での後退の測定の代価に見合わない。
3. **P27E を外部の文の既定にする → 今は変えない。** AI の文 412 claim で P27E と P27 の差は 1 行(N213)。P27E は既に「外部の数の文に使う profile」として採用済み(`docs/XBRL_P27_RESULT_2026-10-27.md` K-1〜K-5)で、呼ぶ側が明示する。`verify_document` の text の経路で自動に P27E にする配線は、自書類の文を渡す経路(儀式・measure)と衝突する。
4. **規則 R(翌期の前期欄の名指し)を engine に → 今は入れない。** site 23 件・2 書類(F-6 外れ)。engine は 1 書類の ZIP しか受けず、R には翌期の instance が要る(入力の形の変更)。measure 側の規則のまま、DB 事業者の第 2 の評価用が届いたときに測る。

## §1 規則 O(engine の直し。字で固定)

**この節の例の字と数は全部作り物。**

profile は 1 つ足す。**P28 = P27 + O**(旗 `other_subject_2026_11_02`)。旗が偽(既定値)なら、P1〜P27・P27E・P27C の振る舞いは 1 行も変わらない。

### §1-1 形(どの数に当てるか)

- `recipes.py` に定数を字で留める(measure の script `measure/xbrl_other_rule_2026-11-02.py` の字と同じ):
  - `OTHER_SUBJECT_TRAIL_2026_11_02 = u":" + u":" + u"、はがをでに 　"`(measure の字のまま。コロン 2 つはどちらも ASCII の `:`、読点・助詞 4 字・半角空白・全角空白 U+3000)
  - `OTHER_SUBJECT_RE_2026_11_02 = re.compile(u"その他(の[^、。::()()\\s]{0,8})?$")`(measure の字のまま。字の集合のコロン 2 つと括弧 4 つは全部 ASCII。全角の「（」は拾わない ― 文は NFKC 済みなので全角の括弧は無い)
  - `OTHER_SUBJECT_HOPS_2026_11_02 = 5`
- 新しい関数 `_other_subject_shape_2026_11_02(profile, s, a, hops=0)` → `(形, 前期)`:
  1. `w = s[:a].rstrip(OTHER_SUBJECT_TRAIL_2026_11_02)`。
  2. `w` が `"(同"` で終わる(文は NFKC 済みなので括弧は半角)なら、`_numbers_of(profile, s)` の数のうち `b <= a` の**最後の 1 つ**の開始位置 `a′` で同じ関数を `hops + 1` で呼び、返り値の 形 をそのまま、前期 = 真 で返す。前の数が無いか `hops >= OTHER_SUBJECT_HOPS_2026_11_02` なら `(偽, 真)`。
  3. それ以外は `(bool(OTHER_SUBJECT_RE_2026_11_02.search(w)), 偽)`。
- **当たる例**: 「受取配当金 12 百万円、その他 3 百万円」の 3(形 真・前期 偽)。「その他の流動資産 45 百万円(同 41 百万円)」の 45(形 真・前期 偽)と 41(形 真・前期 真。「(同」から 45 の手前を辿る)。「- その他の包括利益 7 百万円」の 7(形 真)。
- **当たらない例**: 「売上高 123 百万円」(形 偽)。「その他有価証券評価差額金 9 百万円」(「その他」の後に「の」が無く 9 字以上 → 形 偽。限界、measure と同じ)。「『その他』の販管費 5 百万円」(直前が鉤括弧 → 形 偽)。「(前期 3 百万円)」の 3(「(同」でなく「(前期」→ 2 を通らず、`w` の末尾は「(前期」で 形 偽。限界)。

### §1-2 候補と決まり方

- 新しい関数 `_other_subject_2026_11_02(claim, s, a, b, sign, num, unit, facts, contexts, profile, rounding)`。呼ぶ所は `_dispatch_num_claim` の中、`_direct_value_claim` を呼んだ**直後**(旗が真のときだけ通る 2 行)。`_direct_value_claim` の字は変えない。
- 当てる条件(1 つでも外れたら何もしない): 旗が真。`unit` が `V.UNIT_SCALE` の key(円族)。`claim.get("result") != "GROUNDED"`(engine 自身の経路で一致した行は触らない = **GROUNDED は作りから動かない**)。形 が真。
- 候補: `facts` のうち、(a) 要素の local name(`name` の `:` の後ろ)が `"Other"` で始まり、(b) `unit` が `JPY` で始まり、(c) context の id が 前期 なら `"Prior1Year"`、でなければ `"CurrentYear"` で始まり、かつ `"_"` を含まず(member なし。measure の `period_ok` と同じ字)、(d) `V.match_value(f["value"], target, scale, rounding, mag_trunc)` が真。`target = sign * num * claim["unit_scale"]`・`scale = claim["claim_scale"]`・`mag_trunc = bool(claim.get("magnitude_truncate"))`(どれも `_direct_value_claim` が置いた欄。帯は engine の既存の帯そのもの)。
- 候補が**ちょうど 1 つ**なら決まる: `_P27_STALE_KEYS` の欄と `reason` を消し、`pointer = "xbrl:%s@%s"`・`bound = True`・`result = "GROUNDED"`・`recomputed = f["value"]`・`match = how` を `_direct_value_claim` の GROUNDED の 5 行と同じ字で置く。候補 0 か 2 以上なら claim を変えない。
- どの場合も(形が真の claim 全部に)`claim["other_subject_2026_11_02"] = {"前期": 真/偽, "候補": n, "決まった": 真/偽}` を置き、`claim_to_recipe` で `provenance["other_subject_2026_11_02"]` に写す(P27 の `p27_gate` と同じ形。測定はこの欄で数える)。形が偽の claim には欄を置かない。
- **当たる例**: 「受取配当金 12 百万円、その他 3 百万円」で engine が主語「受取配当金」の fact と 3 を比べて止めた行。`OtherNOI@CurrentYearDuration = 3,200,000` が帯の中で、他の `Other…` に帯の中の fact が無い → `OtherNOI` の当期に結び GROUNDED。
- **当たらない例**: 同じ文で `OtherNOI` と `OtherNOE` の両方に 3 百万円の fact が在る → 候補 2 で保留(claim は engine の判定のまま)。engine が既に `OtherComprehensiveIncome` で GROUNDED にした「その他の包括利益 7 百万円」→ `result == "GROUNDED"` で触らない。「投資その他の資産 88 百万円」で `Other…` に 88 百万円の fact が無い → 候補 0。
- **当たってしまう例(代価)**: 「その他の包括利益累計額 15 百万円」(正しい要素は `ValuationAndTranslationAdjustments`)の値が偶然 `OtherCA@CurrentYearInstant` と帯の中で一致し、他に無い → `OtherCA` に結んで GROUNDED(偽の一致)。「その他」の数が偶然どれか 1 つの `Other…` の fact と一致する率は、97 書類の測定(§3 N-5・N-7)で見る。
- 規則にしないもの: 要素の近傍の制約(R1。§0-2 の 1)。「その他」の後ろ 9 字以上・鉤括弧・「(前期 N)」(§1-1 の限界)。主語の取り方そのもの(`extract.subject_of` の字は変えない)。

### §1-3 profile

- `vocabulary.Profile` に旗 `other_subject_2026_11_02: bool = False` を **P27 の旗 5 つの後ろ・`unnamed_candidate_2026_10_29` の前**に足す(P27C の封の門 `tests/measure/test_xbrl_unnamed_candidate_seal.py` が `unnamed_candidate_2026_10_29` を Profile の末尾と字で縛っているため。末尾に足すとその門が赤になる)。
- `P28 = dataclasses.replace(P27, name="P28", other_subject_2026_11_02=True)`、`PROFILES["P28"] = P28`。P27C の行の後に足す。`PROFILES = {...}` の行・P27C までの定義の字は変えない。**`DEFAULT_PROFILE = "P27"` は変えない。** 旗が真の profile は P28 だけ。
- `verify_document.py`・`run.py`・`registry_setup.py`・`report_customer.py`・`extract.py`・`instance.py`・`core/`・`comparators.py` は **0 行**(新しい理由の名前は足さない。GROUNDED に結ぶだけ)。

## §2 engine の範囲

### §2-1 触る file(既存の行の書き換えは 0 行。挿入だけ)

| file | 足すもの | 行数の見込み(挿入) |
|---|---|---|
| `adapters/xbrl/vocabulary.py` | 旗 1 つ・P28・`PROFILES["P28"]` | 4〜8 |
| `adapters/xbrl/recipes.py` | 定数 3 つ・`_other_subject_shape_2026_11_02`・`_other_subject_2026_11_02`・`_dispatch_num_claim` の呼び出し 2 行・`claim_to_recipe` の provenance の 2 行 | 40〜80 |

- 試験: `tests/adapters/xbrl/test_recipes_p28.py`(新しい file。§1 の当たる例・当たらない例・当たってしまう例を作り物の facts で 1 本ずつ。旗が偽なら P27 と同じ出力(同じ入力で claim の欄が全部同じ)。変異で赤: 正規表現の `{0,8}` を `{0,9}` に・`TRAIL` から読点を消す・hops を 4 に・候補の条件 (a)〜(d) を 1 つずつ外す・「ちょうど 1 つ」を「1 つ以上」に・`result == "GROUNDED"` の条件を外す・旗の既定を真に)。
- `tests/adapters/xbrl` の profile 名の一覧(`test_p17.py`・`test_p20.py`・`test_recipes_p21.py`〜`test_recipes_p26.py`・`test_vocabulary.py` の `sorted(V.PROFILES)`・`test_recipes_p27.py` の「P27 の旗を持つ profile」の一覧)に P28 を足す(cb8612f が P27C で足したのと同じ所)。P16〜P27 を明示した試験の数は 1 つも変えない。

### §2-2 触る枝の中の人間の決定(字も振る舞いも壊さない。新しい行はどれもその**後ろ**か、旗が真のときだけ通る別の関数)

1. 案ア `no_subject`(2026-10-08): `_direct_value_claim` の字は変えない。O は `result != "GROUNDED"` の行に当たるので、主語なしの行(`no_subject`)にも当たりうる ― 形が真(直前が「その他」)なら主語は「その他」の項目であり、案アの「主語が取れていない数を束縛しない」の趣旨(どの項目か分からない数)の外。**この点は監査に判断を回す**(当たらないようにするなら `subj` が空の行は条件から外す。実装の席は両方の数を測って報告する)。
2. §1b `prior2_required`・P21 の最後の枝・P22 `period_bind`・P23 `_mag_trunc`・P24 の旗・P25 の証拠・P26 G1〜G5・P27 A・B・C1〜C3: 字は変えない。O は `_direct_value_claim` の**後ろ**(全部の枝が決めた後)。
3. C2 `period_cue`(2026-10-13): 字は変えない。O の 前期 の判定は `_prior_cue` を使わず §1-1 の「(同」だけ(measure と同じ字。「前期末」の印は辿らない)。
4. XBRL 直し §2 `doc_rounding`・`decide_rounding`: 字は変えない(帯は `rounding` をそのまま受ける)。
5. P26 G1 概念の門・P27 C1〜C3 は全部の claim を作った後に当たる(O で GROUNDED になった行は G1 の対象外 = GROUNDED でない束縛だけに当たる)。
6. **既定 `DEFAULT_PROFILE = "P27"`**(封 `docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md`・6a34db5)。この封は**この後ろ**に profile を足すだけ。
7. P27C の候補の欄 `candidate`(cb8612f。人間の承認 db68a2c): 字は変えない。P28 は P27 から作るので `unnamed_candidate_2026_10_29` は偽のまま。
8. `extract.subject_of`・`iter_numbers*`(写し元との照合 `test_lineage`): 字は変えない。

### §2-3 既存の門の engine の留め(HEAD `c4b8221` で `git grep -l` した数。実装の便で同じ便に宣言された遷移を足す。測った当時の値は消さない)

いまの sha16(file の sha256 の頭 16 字)と留める file 数(全部 `tests/measure`): `vocabulary.py` `7fbcfbf0e472f366`(36)・`recipes.py` `52d645e713c53c1c`(33)・`verify_document.py` `6c76c8ade6c7b1c8`(30。本便 0 行)・`comparators.py` `d8706338325e725b`(21。0 行)・`extract.py` `3cf55966f12919f0`(19。0 行)・`resolve.py` `a41043763c1d4073`(17。0 行)・`registry_setup.py` `d6f25750bcd73c0a`(16。0 行)・`report_customer.py` `bdbaa00a419219fe`(15。0 行)。adapter の指紋 `dc7e35fbfb0f56ca…` 11 file。束ねた sha `864b1f96292f1615…`(37 本)を字で持つ 4 file(`test_xbrl_customer_report_fix_seal.py`・`test_xbrl_customer_report_seal.py`・`test_xbrl_default_p26_seal.py`・`test_xbrl_p26_seal.py`)。

- 留めの型: `ENGINE_LATER` 系・`FROZEN_LATER`・`ENGINE_TRANSITIONS`(`test_xbrl_p26_result.py`・`test_xbrl_p26_seal.py`・`test_xbrl_fresh_result.py`)・`UNTOUCHED_LATER`・`P27_LATER`・`DECLARED`・`LATER_FROZEN`・`LATER_FINGERPRINT`・`MODULE_LATER`。どの file がどの型かは実装の席が `git grep` で数え直し、宣言の行(`(新しい sha16, "docs/XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02.md")`)を b2c3f56・cb8612f と同じ形で足す。
- `fixtures/frozen_bundle_sha.py` の `FROZEN_BUNDLE_GENERATIONS` に新しい世代を足す(いまの束ねた sha `864b1f96…`、37 本。本数は変わらない見込み)。
- `tests/measure/test_xbrl_axis3_decision.py` の `LATER_ENGINE_COMMITS` に実装の commit を宣言するのは次の便(commit の直後は test_9 が赤。前例 76d557f・f71a9a3 と同じ)。
- 新しい門で engine の留めを定義するときは、`ENGINE_LATER`・`UNTOUCHED`・`PIN_DEF`・`LATER_ENGINE_COMMITS`・`FROZEN_LATER`・`ENGINE_TRANSITIONS` を行頭の名前に使わない(`ENGINE_PIN_P28` などの別名)。
- 儀式の記録 `fixtures/xbrl/ritual_2026-10-20.json` は既定 P27 の記録で、既定は変えないので採り直さない(門 `test_xbrl_ritual_result.py` が engine の sha を留めていれば宣言された遷移で)。
- 重い走らせ直し(`AUDIT_CORE_*` の変数)のうち engine の sha を比べるものは、測った値の欄が 1 字も違わないことを確かめてから遷移を足す(同じ封の型)。

## §3 事前予測(**実装より先に固定。結果を見てから書き換えない**)

### §3-1 AI の文 1 書類(同梱の ZIP。P27 → P28。`verify_document(zip, profile, None)`)

| # | 予測 | **外れ方** |
|---|---|---|
| **O-1** | 配線: 旗が偽の P27 の出力(`sort_keys` の JSON。`engine` の欄を除く)が HEAD `c4b8221` の engine と **byte 一致**。P27 の 4 state は 340・14・33・25 | 1 byte でも違う / 数が違う |
| **O-2** | 形が真の行(provenance の欄で数える)は **10〜16** | 幅の外 |
| **O-3** | 決まって GROUNDED になった行は **6〜8**(§0-1 の 7 行 N080・N081・N144・N145・N213・N290・N299 の見込み) | 5 以下 / 9 以上 |
| **O-4** | 決まった行の要素と期は `docs/XBRL_OTHER_RULE_2026-11-02.md` §2-2 の表と**全部同じ**(N080 `OtherNOI` 当期・N081 `OtherNOI` 前期・N144 `OtherCA` 当期末・N145 `OtherCA` 前期末・N213 `OtherNCL` 当期末・N290 `OtherNetInvCF` 当期・N299 `OtherNetFinCF` 当期) | 1 行でも違う要素か期 |
| **O-5** | 候補 2 以上で保留の行は **0〜2**。候補 0 の行は **3〜6**(N162・N163・N238・N239 の見込み) | 幅の外 |
| **O-6** | 形が偽の行で P27 と state・pointer・reason が違う行は **0**。GROUNDED 340 は P28 でも全部 GROUNDED(作りから。配線の確認) | 1 行でも違う |
| **O-7** | P28 の 4 state: GROUNDED **346〜348**・VALUE_MISMATCH **11〜13**・UNVERIFIABLE 33・POINTER_NOT_FOUND **19〜22** | 幅の外 |

### §3-2 手元の 97 書類の原文(P22・P26・P27 → P28。前例 `measure/xbrl_p27_regress97_2026-10-27.py` の 97 書類)

| # | 予測 | **外れ方** |
|---|---|---|
| **N-1** | 旗が偽の profile(P22・P26・P27)で、97 書類の出力が HEAD `c4b8221` の engine と byte 一致 **97 / 97**(3 profile とも) | 1 書類でも違う |
| **N-2** | 形が真の行は 97 書類で **40〜300**(67 書類と 30 書類の内訳は判定しない) | 幅の外 |
| **N-3** | 決まって GROUNDED になった行は **10〜120** | 幅の外 |
| **N-4** | 動いた行の向きは (VALUE_MISMATCH / UNVERIFIABLE / POINTER_NOT_FOUND)→ GROUNDED **だけ**。他の向き **0**。GROUNDED のまま pointer が替わる行 **0**。形が偽の行で動いた行 **0** | 1 行でも |
| **N-5** | 候補 2 以上で保留の行は、決まった行**以下** | 保留 > 決まった |
| **N-6** | 決まった行のうち、measure 側で計算リンクの近傍(R1。`measure/xbrl_other_rule_2026-11-02.py` の `neighbourhood` を import)を当てても同じ fact が候補 1 つである割合は **85% 以上** | 85% 未満 |
| **N-7** | 読み(§5-3。決まった行から種で引いた最大 30 行を 2 席が読む): 2 席とも「文の数はその要素の値」と読んだ行が読んだ行の **90% 以上**、2 席とも「違う項目」と読んだ行 **0〜1** | 幅の外 |
| **N-8** | 判定しない: 要素名の分布、書類ごとの内訳、主語なし(`no_subject`)の行で決まった数(§2-2 の 1。数は記録に書く) | ― |

封の席の偏り: O-3・O-4 は measure の R0/R1 の結果の写しで当たりやすい(帯の形が engine の帯と同じ `V.match_value` になる分だけ違いうる。measure は round と truncate の両方を試した)。N-2・N-3 の幅は AI の文の率(12 / 412)を有報の原文に当てた見立てで、根拠の数は無い。N-7 の読みは同じ model の 2 席(§6 の限界)。

## §4 採用の基準(数で。判定は記録から門が機械で求め、司令塔は覆さない)

**P28 を「既定の候補」として記録する**(既定に替えるのは別の便で人間が決める)のは、次を全部満たすとき:

- **K-1(壊さない)**: N-1 が 97 / 97(3 profile とも)、O-1 の byte 一致、N-4 の他の向き 0・形が偽の行で動いた行 0。
- **K-2(決める)**: O-3 が 6 以上、O-4 が全部同じ。
- **K-3(偽の一致を作らない)**: N-7 で 2 席とも「違う項目」と読んだ行が **1 以下**、かつ「文の数はその要素の値」が **85% 以上**。
- **K-4(近傍なしで足りる)**: N-6 が **80% 以上**(80% 未満なら「R1 の近傍を engine に入れる封」を次の候補に書く。P28 自体は残す)。

**採用しない**とき(K-1〜K-3 のどれか 1 つでも外れたら): P28 は engine に残す(旗が偽なら何も変わらない。P23〜P25 の前例)が、結果文書に「採用しない」と書き、既定の候補にしない。規則を直すなら新しい封で。

## §5 測り方

### §5-1 AI の文(`measure/xbrl_p28_ai_prose_2026-11-02.py`)

- `fixtures/xbrl/ai_prose_instance_2026-10-09.zip`(sha256 `03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799`)を P27 と P28 で `verify_document(zip, profile, None)`。標準ラベルは `fixtures/xbrl/taxonomy_labels_sha256.txt` の 3 本が cache に在り sha256 が合うことを先に確かめる(無ければ止める)。
- 記録 `fixtures/xbrl/p28/ai_prose_2026-11-02.json`: P27 と P28 の 4 state、行の対応(id の順で (span, value, unit) が同じ)、形が真の行の一覧(id・前期・候補の数・決まった・P27 の state と要素・P28 の state と要素・期)、動いた行、O-1〜O-7 の判定。P28 の entry は `fixtures/xbrl/p28/entry_output_ai_prose_p28_2026-11-02.json`(封 `35f624c` §1 と同じ欄・docID を落とす)。
- 配線の門: P27 の出力の sha256 が `fixtures/xbrl/entry_output_ai_prose_p27_2026-11-02.json` の claims と欄ごとに一致(engine の欄を除く)。

### §5-2 97 書類(`measure/xbrl_p28_regress97_2026-11-02.py`)

- 前例の script `measure/xbrl_p27_regress97_2026-10-27.py` の関数(`doc_lists`・`zip_path`・`names_sha`・`dump_no_engine`・`moved_rows`・`state_counts`・`direction`)を **import して**使う(写さない。前例の script は 1 行も変えない)。profile は `("P22", "P26", "P27", "P28")`、比べる engine は HEAD `c4b8221`(`git archive` で TMPDIR に取り出し、別の process)。
- 形が真の行と候補の数は provenance の欄で数える。R1 の近傍(N-6)は measure 側で `_cal.xml` を読む(`measure/xbrl_derivation_full_2026-11-02.py` の `parse_cal`・`to_qname` と `measure/xbrl_other_rule_2026-11-02.py` の `neighbourhood` を import)。
- 記録 `fixtures/xbrl/p28/regress97_2026-11-02.json`: 書類ごと・profile ごとの 4 state、動いた行の (docID, id, 前の state と reason, 後の state, 結んだ要素の local name と期, 候補の数, R1 でも同じ fact か, `no_subject` だったか)。**span・value・recomputed・文は入れない**(前例と同じ)。cache の前後(`edinet/` 281・`edinet-fresh-2026-10-21/` 40・`edinet-prior-2026-11-02/` 94 が変わらない)。評価用の AI の文・DB の応答は開かない(`edinetdb-p27/` の下を読まない)。

### §5-3 読み(2 席の subagent。0 USD)

- 決まった行(N-3)から、種 `measure/SEED.json`(`inject.verify_seed_sealed`)で**最大 30 行**を引く(30 以下なら全部)。行ごとに、文(NFKC 済みの engine の文)・数・結んだ要素の名と標準ラベル・その fact の値と期・engine が P27 で指していた要素(あれば)を束にして、2 席に同じ指示文で渡す(1 行 1 subagent × 2 席)。問い: 「文のこの数は、この要素(ラベル)のこの期の値か」。答えは 3 値(`合う` / `違う項目` / `判定不能`)と理由 1 文。
- 束と理由は repo の外(scratchpad)。記録 `fixtures/xbrl/p28/readings_2026-11-02.json` には行ごとの (docID, id, 席 1 の答え, 席 2 の答え) と集計だけ(文・値・理由は入れない)。
- 席の指示文は script の定数で字を固定し、結果の門が script と照らす。席は `~/Desktop/sgogi-coach-handoff/` と `~/.cache/audit-core/edinetdb-p27/` を開かない。

## §6 限界・除外

- 97 書類は 2026 年提出の有報に偏る(P27 の封 §8 と同じ標本)。札が無いので、決まった行の正しさは読み(同じ model の 2 席)でしか見られない。2 席の一致は独立した証拠に数えない(H-08・H-13)。
- 規則 O は R0(近傍なし)。`Other…` 要素が多い書類で候補 2 以上(保留)が増えるかは本便で初めて測る。近傍が要ると分かっても本便では入れない(別の封)。
- 形の規則は measure の字そのまま(§1-1 の限界: 9 字以上・鉤括弧・「(前期 N)」を拾わない)。
- 帯は engine の既存の帯(書かれた精度 A・丸め方 P23)。measure の便は round と truncate の両方を試していたので、measure で決まった行が engine で決まらないことはありうる(O-3 の外れ方)。
- 既定は P27 のまま。P28 を既定にするかは、本便の結果と採用の基準を見て人間が決める(別の封)。
- 通信なし・0 USD・LLM の API を呼ばない(読み手は subagent)。

## §7 門

- 封の門 `tests/measure/test_xbrl_p28_seal.py`: §1-1 の定数 3 つ(正規表現の字・TRAIL・hops)が engine の字と同じ。P28 の作り方(`dataclasses.replace(P27, name="P28", other_subject_2026_11_02=True)`)と旗が真の profile が P28 だけ。旗の位置(P27 の旗 5 つの後ろ・`unnamed_candidate_2026_10_29` の前)。`DEFAULT_PROFILE == "P27"`。§2-3 の留めの一覧を実物の `git grep` から数え直す。
- 結果の門 `tests/measure/test_xbrl_p28_result.py`: 記録 3 つの中身(禁止欄 span・value・recomputed・文が無い、cache の前後が同じ、docID が 97 の一覧の中)、O-1〜O-7・N-1〜N-7 の判定を記録から計算して結果文書の表と一致、K-1〜K-4 の判定を記録から求める、読みの指示文の字が script の定数と同じ、順序(封 S ⊏ 実装 E ⊑ 記録 R ⊑ HEAD を commit の祖先で。同じ commit は赤にしない。S の commit が engine を触っていない)。変異で赤くなることを確かめてから門と呼ぶ(各判定の条件を 1 つずつ緩める・記録の数を 1 つ変える・順序を逆にする)。
- 新しい測定の script 2 本は `tests/measure/test_xbrl_inject_harness_review.py` の `LATER_HARNESS_FILES` に宣言(仕掛けなし。注入はしない)。記録に docID が入るので `tests/measure/test_xbrl_fresh_seal.py` の `LATER_NAMING_FILES` に記録 2 つ・結果の文書を宣言。
- 覆い: `python3 measure/suite_coverage_2026-10-16.py --write`・`docs/SUITE_COVERAGE_2026-10-16.md` §2-1。台帳 `docs/FACTS_FOR_BUYERS_2026-10-20.md` に L・P の行(印つき)。

## §8 file と順序

1. **この封(S)を commit**(文書だけ。engine 0 行)。
2. 実装(§1・§2)・`tests/adapters/xbrl/test_recipes_p28.py`・profile 名の一覧・留めの遷移・`FROZEN_BUNDLE_GENERATIONS` → script 2 本(§5-1・§5-2)を書いて走らせる → 読み(§5-3)→ 記録 3 つ → 結果 `docs/XBRL_OTHER_SUBJECT_ENGINE_RESULT_2026-11-02.md` → 門 2 本(§7)→ 凍結(sha256 の一覧)→ 独立監査 GO → path 指定で commit(**E**。engine・試験・script・記録・結果・門・覆いを 1 commit に束ねる。順序の門は同じ commit を赤にしない)。
3. axis3 の `LATER_ENGINE_COMMITS` に E を宣言、台帳の L・P の行、README の本数(次の便)。
4. 既定を替えるかは人間が決める(この封の範囲の外)。

各便の commit はパス指定。主の木を赤くしうる実測は worktree で。cache の 3 folder(281・40・94)には 1 file も書かない。
