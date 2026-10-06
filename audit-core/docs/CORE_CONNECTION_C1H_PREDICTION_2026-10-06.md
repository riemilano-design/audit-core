# Core 接続 C-1h(XBRL Adapter の直し 4 つ、profile P7)の予測 ― 実装の前に封じる

> **封じた後は本文を変えない。** 訂正は日付つきの追記か結果文書に。予測を当てるために規則・窓・語を動かさない。外れは外れのまま記録する。
>
> **前提**: 人間の決定(2026-10-06、[CORE_CONNECTION_C2_DECISIONS_AFTER_2026-10-06.md](CORE_CONNECTION_C2_DECISIONS_AFTER_2026-10-06.md)): 「XBRL の次の直し 4 つは 1 本の予測として封じてから。直す前に、どの Claim がどう動くかを ID 単位で予測して封じる」。直す物は [C-1g の結果](CORE_CONNECTION_C1G_RESULT_2026-10-06.md) §7 の 1・2・3・5(4 の registry 欄は `2ecefa2` で済み)。
>
> **Base**: `b449458`。Core 4 本は `f917f02` から不変。P1・P5F・P6 と期待値 v1 2 本・1B v2 は凍結(1 byte も変えない)。直しは全部 **profile P7**(= P6 + 4 つ)に束ねる。

## 1. 直す物(全部 Adapter。Core は 1 行も触らない = 門)

| # | 直し | 規則(封) |
|---|---|---|
| 1 | **「支出」系 CF 項目の文章 Claim** | 要素の局所名が `^(PurchaseOf|PaymentsFor|Payments|RepaymentsOf|RepaymentOf|RedemptionOf|DividendsPaid|IncomeTaxesPaid|InterestPaid)` に合う(`ProceedsFrom…` は含めない。`IncreaseDecrease…`/`DecreaseIncrease…` は C-1g の規約 b が先に効く)。これらは**負で記録され、文の「増加/減少」は大きさの増減**。**文章の Claim だけ**: 当期・前期の JPY の対に束縛し、新比較子 `builtin:sign(|cur|-|prior|)==direction`(pointer の 3 本目のトークンも同名)。recomputed = \|cur\| − \|prior\|。**数の Claim は変えない**(「支出 143 百万円」の数は大きさで、abs の札が正しい) |
| 2 | **目標値・計画値の数の Claim** | 数の Claim で、**数の手前 10 字以内**に `目標|計画` があれば UNVERIFIABLE、新理由 `target_or_plan`。文章の Claim・数の後ろの語は見ない(1 社目 N014「5.8% となり、目標を達成」を落とさないため)。**1 社目 N013「ROE 10% 以上を安定的に達成…」は語が後ろにあるので直らない**(先に書く) |
| 3 | **文章 Claim の対が無いときの理由を 3 つに分ける** | 主語が束縛でき、(a) 要素の当期 fact はあるが JPY が 1 件も無い → `no_element(text needs money fact)`(pure 比率の文章)、(b) JPY の当期はあるが前期の対が無い → `no_element(no prior for text)`、(c) fact が無い → `no_element` のまま。state は全部 POINTER_NOT_FOUND のまま(動くのは reason だけ) |
| 4 | **窓幅を字で留める試験** | `_flow_direction_word` の「数の直後 4 字」と `_build_point_diff_claim`・差額の「手前 25 字」を、境界の両側(4 字目に語があれば拾い 5 字目なら拾わない、25 字目と 26 字目)の試験で留める。変異 窓 4→10・25→30 が赤になる(C-1g 監査の記録事項 3) |

実装の形: `vocabulary.expenditure_convention(element_name)`(新)、`comparators.builtin_sign_abs_diff_direction`(新、登録名 `builtin:sign(|cur|-|prior|)==direction`)、`recipes` の文章 Claim の分岐に 1 と 3、数の Claim の分岐に 2(`_TARGET_RE = 目標|計画`、窓 `s[max(0, a-10):a]`)、`Profile` に `expenditure_sign`・`target_word`・`text_reason_split` の 3 フラグ(既定 False、P7 だけ True)。P1・P5F・P6 の `Profile(...)` の行は不変。

## 2. 期待値の扱い(規則)

v1 2 本・1B v2 は不変。P6 の門(計器 3b)は v2/v1 のまま緑。P7 の結果は §3 の ID 単位の予測と照合する。**予測した差の集合と実測の差の集合が一致したときだけ**(人間の委任 2026-10-06 のもと司令塔が判断): 1B は差 0 なので **v2 がそのまま P7 の門**(新ファイルを作らない)、5F も **v1 のまま**、3 社目は `core_expectation_3rd_v1.json`(P7、140 件)を**別コミットで新設**し計器 3c とする。一致しなければ止まって差を表にする(3 社目の期待値はまた持ち越し)。

## 3. 予測(ID 単位。1 回目の JSON `c1g_first_run_{1B,5F,3rd}_P6.json` と instance の fact を読んで書いた。直す前に封じる)

### 3.1 1 社目 S100Z4Q1(P7 vs P6、91 件)― 動くのは **0 件**(state・pointers・recomputed・normalization・reason の 5 欄とも)

根拠: 「支出」系の要素に束縛された Claim は N052・N055・N056 の**数の Claim だけ**(文章は無い)で、数は変えない。`目標|計画` が数の手前 10 字に出る数の Claim は無い(N014 は後ろ、N013 も後ろ)。文章の PNF は T011(退職給付に係る資産)1 件で、`RetirementBenefitAsset` の fact は plain context に無い → (c) のまま `no_element`。

### 3.2 2 社目 S100Z4B6(P7 vs P6、133 件)― 動くのは **0 件**

根拠: 「支出」系に束縛されたのは N060〜N062 の数の Claim だけ。`目標|計画` の数の Claim 無し。文章の PNF 無し。

### 3.3 3 社目 S100YMFV(P7 vs P6、140 件)― 動くのは **5 件**(state 3 + reason だけ 2)

| ID | 文 | P6 | P7 の予測 | 根拠(fact) |
|---|---|---|---|---|
| **T022** | 法人税等の支払額 86 百万円**等の減少**(資金の減少要因) | G(偶然。sign(cur−prior) = −1 == 減少) | **VM**(\|−86,046\| − \|−66,547\| = **+19,499 千円** = 支払いは増えた ≠ 減少)。pointers の 3 本目が `builtin:sign(\|cur\|-\|prior\|)` に、recomputed +19,499,000 | T021 と同型の証拠の層の false pass が消える(安全側) |
| **T025** | 投資有価証券の取得による支出 143 百万円等の**減少** | VM | **G**(\|−143,940\| − \|−219,930\| = **−75,990 千円** = 支出は減った == 減少)。recomputed −75,990,000 | 取りこぼしが直る |
| **N087** | 目標値であった 8.6% | VM(ROE 7.3 と比べる) | **UNV `target_or_plan`**(「目標値であった」が手前 10 字以内)。pointers 1 → 0、recomputed None | 安全側の誤りが消える |
| N088 | 目標値であった 8.6% と比べて 1.3 ポイント | PNF `no_element(point without prior phrase)` | **不変**(「目標」は 1.3 の手前 15 字で窓の外) | ― |
| **T045** | 自己資本比率 … 増加 | PNF `no_element` | PNF **`no_element(text needs money fact)`**(CapitalAdequacyRatio は pure だけ) | reason だけ |
| **T052** | ROE … 下回 | PNF `no_element` | PNF **`no_element(text needs money fact)`**(RateOfReturnOnEquity… は pure だけ) | reason だけ |
| T040 | 退職給付に係る負債 増加 | PNF `no_element` | **不変**(`RetirementBenefitLiability` の fact が無い = (c)) | ― |
| N013(1 社目) | ROE 10% 以上を安定的に達成 | VM | **不変**(語が後ろ。直らないと先に書く) | ― |

state の集計: **G 73 → 73、VM 3 → 2(T021・T022)、PNF 19 → 19、UNV 45 → 46**。`no_element(no prior for text)` は **3 書類とも 0 件**(JPY の当期があって前期が無い主語は見当たらない。1 件でも出れば外れ)。

### 3.4 その他

| # | 項目 | 予測 |
|---|---|---|
| a | Core 4 本・v1 2 本・v2・原本 | 不変(門) |
| b | P1・P5F・P6 の門(224・計器 3・3b・5・系譜) | 緑のまま |
| c | 登録 | **28**(比較子 9・scheme 2・normalization 4・理由 13 = Adapter の登録だけ。C-1d/C-1g と同じ数え方)。Core 0・拡張 0 |
| d | 試験 | 新規 **+10〜18**(支出規約 3〜5、目標 2〜3、理由の分割 2〜3、窓の字留め 2、P7 の門 2〜3、登録 1) |
| e | 変異 | **+5〜7**(支出の符号を反転 → 3 社目 T022/T025 が入れ替わって red、目標の窓を外す → red、理由の分割を外す → red、窓 4→10 → red、25→30 → red、green 1〜2)。予測を先に書く |
| f | 行数 | Adapter **+60〜140** |
| g | 1 回目の計測で予測と違う ID | **0〜1 件**(疑うのは、`目標` の窓 10 字が別の数を拾うこと(3 社目 N086「中期経営計画にお」は 1.2 の後ろなので拾わないはず)と、`Payments` の接頭辞が想定外の要素(例 `PaymentsForRetirementBenefits`)の数の Claim の文脈で文章 Claim を 1 件増やすこと) |
| h | 手検査 | 動いた 3 件(T022・T025・N087)を文と fact で読み直し、false pass 0 |

## 4. 3 役と止まる所

実装担当(`adapters/xbrl/`・`tests/adapters/xbrl/`・`tests/golden/` の P7 の門だけ。**作業木を書き換える git 操作は使わない。実書類で P7 を回さない(合成材料だけ)。コミットしない**)→ 司令塔が凍結し **P7 で 3 書類を 1 回ずつ回して §3 と ID 単位で照合、結果を `fixtures/xbrl/c1h_first_run_{1B,5F,3rd}_P7.json` に保存** → 監査(変異を自作、v1/v2 不変、Core 不変)→ GO でコミット → 結果文書 → §2 のとおり一致したときだけ 3 社目の期待値を別コミットで新設。

止まる所: Core の変更が要ると分かったら HUMAN。P6 の門(3b)が赤になったら REVISE(P6 を変えてはいけない)。

## 5. この文書がしないこと

Core の変更。将棋側の変更。P1・P5F・P6 の変更。「支出」系の**数の Claim** の札を変えること。1 社目 N013 を無理に直す規則(後ろの語)を足すこと。
