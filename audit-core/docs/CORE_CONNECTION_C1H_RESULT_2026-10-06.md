# Core 接続 C-1h(XBRL Adapter の直し 4 つ、profile P7)の結果

**日付**: 2026-10-06 **予測の封**: [CORE_CONNECTION_C1H_PREDICTION_2026-10-06.md](CORE_CONNECTION_C1H_PREDICTION_2026-10-06.md)(`201c081`、sha `bea332c9…`、不変) **監査**: **GO**(独立、2026-10-06。凍結 14 件の sha 一致・`_dispatch_num_claim` 切り出しの dedent diff 0・384 OK/39/39/6/6 を再測・自作変異 4 本(abs 落とし・目標の窓 10→5・理由 (a)/(b) 入替・差額の窓 25→20)全部赤・P6→P7 の 5 欄突き合わせを独自に再計算して一致。非ブロッキング 2 件は §5.4) **コミット**: `78d1a76`(Adapter + 試験 + 1 回目の計測 3 本)

## 1. 何を直したか(全部 `adapters/xbrl/`。Core 0 行)

| # | 直し | 実装 |
|---|---|---|
| 1 | 「支出」系 CF 項目の文章 Claim | `vocabulary.expenditure_convention`(`^(PurchaseOf|PaymentsFor|Payments|RepaymentsOf|RepaymentOf|RedemptionOf|DividendsPaid|IncomeTaxesPaid|InterestPaid)`、anchored)。**語彙のトークン**に当てる(C-1g の `flow_convention` と同じ場所)。文章 Claim は当期・前期の JPY の対 + 新比較子 `builtin:sign(\|cur\|-\|prior\|)==direction`、recomputed = \|cur\| − \|prior\|。数の Claim は変えていない |
| 2 | 目標値・計画値の数の Claim | `_TARGET_RE = 目標\|計画`、`_TARGET_WINDOW = 10`(手前だけ)→ UNVERIFIABLE `target_or_plan`。数の Claim の振り分けを `_dispatch_num_claim` に切り出し、その前に判定を置いた(本文は不変) |
| 3 | 文章の対が無い理由の分割 | `_text_unbound_reason`: (a) `no_element(text needs money fact)` (b) `no_element(no prior for text)` (c) `no_element`。plain の分岐と支出の分岐の両方から呼ぶ |
| 4 | 窓幅の字留め | `_flow_direction_word` の 4 字と `_build_point_diff_claim`・差額判定の 25 字を境界の両側の試験で留めた。変異 窓 4→10・25→30 が赤 |

Profile P7 = P6 + `expenditure_sign`・`target_word`・`text_reason_split`(既定 False)。P1・P5F・P6 の `Profile(...)` の行は不変。差分 10 ファイル +803/−116(recipes +170/−90 は切り出しの再構成を含む)。

## 2. 門(司令塔が凍結時点で測った。凍結 = 10 ファイルの sha 一覧)

| 門 | 結果 |
|---|---|
| Core 4 本・v1 2 本・v2・原本 4 本の sha | 不変 |
| `unittest discover` | **Ran 384 OK**(336 + 新規 48) |
| 変異 | XBRL **39/39** 予測どおり(33 + H-R1〜R5 red・H-G1 green)。将棋 6/6 不変 |
| P6 の門(3b: P6×1B == v2、P6×5F == v1) | 緑(P6 の挙動は不変) |
| P7 の門(3b に追加: P7×1B == v2、P7×5F == v1) | 緑 = 封じた「1 社目 0 件・2 社目 0 件」 |
| 登録 | **28**(Adapter 分: scheme 2・比較子 9・normalization 4・理由 13)。`register_all` 後の登録簿は builtin/equals を含めて 3/10/4/13 |

## 3. 1 回目の計測(司令塔が凍結の後 19:45 に P7 で 1 回ずつ)

出力: `fixtures/xbrl/c1h_first_run_{1B,5F,3rd}_P7.json`(sha `f2abebdd… / b12974cc… / 5b5d66e4…`)。基準: P6 の 1 回目 `c1g_first_run_*_P6.json`。照合は **5 欄**(state・pointers・recomputed・normalization・reason)、ID 単位。

### 3.1 1 社目 S100Z4Q1(91 件)― 予測 0、動いた **0**。v2 との `--gate` も差 0

### 3.2 2 社目 S100Z4B6(133 件)― 予測 0、動いた **0**。v1 との `--gate` も差 0

### 3.3 3 社目 S100YMFV(140 件)― 予測 5、動いた **6**

| ID | 予測 | 実測 | 判定 |
|---|---|---|---|
| T022 法人税等の支払額「等の減少」 | G → VM、recomputed +19,499,000、pointers の 3 本目が新トークン | そのとおり | 当たり(T021 型の証拠の層 false pass が消えた) |
| T025 投資有価証券の取得による支出「減少」 | VM → G、recomputed −75,990,000 | そのとおり | 当たり(取りこぼしが直った) |
| N087 目標値であった 8.6% | VM → UNV `target_or_plan`、pointers 1 → 0 | そのとおり | 当たり |
| T045 自己資本比率 / T052 ROE(文章) | reason → `no_element(text needs money fact)`、state PNF 不変 | そのとおり | 当たり(2) |
| **T028 配当金の支払額 63 百万円「等の減少」** | **書いていない**(不変と見なしていた) | **G → VM**、recomputed −11,822,000 → **+11,822,000**、pointers の 3 本目が新トークン | **予測に無い変化 1** |
| N088・T040・N013(1 社目) | 不変 | 不変 | 当たり |

state 集計: **G 72・VM 3(T021・T022・T028)・PNF 19・UNV 46**(予測 73 / 2 / 19 / 46)。`no_element(no prior for text)` は 3 書類とも **0**(予測どおり)。

**T028 の外れの原因**(司令塔の側): 予測は instance の **fact の要素名**を走査して「支出」系を数えた。`CashDividendsPaidFinCF` は `Cash` で始まるので anchored の正規表現に合わず、見落とした。実装は C-1g の `flow_convention` と同じく**語彙のトークン**(`配当金の支払額 → DividendsPaid`)に正規表現を当てる(封じた「要素の局所名」の読みは語彙側が前例どおりで、実装は正しい)。T028 の文は「…配当金の支払額 63 百万円等の**減少**によるもの」で、減少は資金のもの。当期 \|63,…\| > 前期 なので支払いは増えており、VM は安全側で正しい。**P6 の G は T021・T022 と同型の証拠の層 false pass で、P7 で 3 件とも消えた。**

### 3.4 その他の予測との照合

| # | 予測 | 実測 | 判定 |
|---|---|---|---|
| a | Core・v1・v2・原本 不変 | 不変 | 当たり |
| b | P1・P5F・P6 の門 緑 | 緑 | 当たり |
| c | 登録 28・Core 0・拡張 0 | 28・0・0 | 当たり |
| d | 試験 +10〜18 | **+48** | **外れ**(窓の境界試験と理由の分割、目標の窓の試験を細かく割った。過小見積もり 3 段連続: C-1g +41 は当たりの上限際、C-2 +73 と C-1h +48 は上に外れ) |
| e | 変異 +5〜7 | +6 | 当たり |
| f | 行数 +60〜140 | **+687 正味**(Adapter 4 本 +267/−106 = +161、試験 +536/−10) | **外れ**(Adapter だけでも 161 で上限 140 を超えた。切り出しの再構成分を見ていない) |
| g | 違う ID 0〜1 | **1**(T028) | 当たり |
| h | 手検査 3 件 false pass 0 | 動いた 4 件(T022・T025・T028・N087)を文と fact で読み、false pass 0。T022/T028 の VM は文の「減少」が資金の語であることを確かめた | 当たり |

**集計**: 1B 0/0、5F 0/0、3rd 予測 5 件は 5 当たり + 予測外 1、3.4 の 8 項目中 6 当たり・2 外れ(試験本数・行数)。**封じた予測は変えていない。実装を予測に寄せていない。**

## 4. 期待値(規則 §2 の適用)

- 1 社目: 差 0 なので **v2 がそのまま P7 の門**(新設なし)。2 社目: **v1 のまま**。
- **3 社目の期待値はこの段でも作らない。** 規則は「予測した差の集合と実測の差の集合が一致したときだけ」で、5 対 6。委任されていても規則は曲げない。
- **人間への申し送り**: 3 社目は C-1g(18 対 20)・C-1h(5 対 6)と 2 段続けて「全部説明がつき安全側だが集合は 1〜2 件ずれる」で止まっている。「一致」の定義を (i) 集合の完全一致のまま(次の段で予測外 0 を狙う)にするか、(ii) 「予測外の変化が全部説明され、安全側で、人間が表を読んで承認した」場合も新設可にするかは、**人間が決める**(規則の変更なので司令塔は決めない)。(ii) なら今回の 6 件で新設できる。

## 5. 手順との差・記録

1. 実装担当は作業木を書き換える git 操作を使わず、実書類で P7 を手で回していない(P7 の門 2 本は discover の中で走る形)。逸脱なし。
2. 実装担当が決めた点のうち記録に値するもの: (i) `comparators.builtin_sign_abs_diff_direction` の式を既存の `builtin_sign_direction` と**字面が重ならないように**言い換えた(既存の変異 F-R3・D-R4 が「old 文字列は 1 回だけ出現」を前提にしており、同じ字が 2 か所にあると変異の当て先がずれる。[記憶 `restore-by-replace-lands-elsewhere`] と同じ根)。変異の運用上の制約がコードの書き方に影響した例として記録。(ii) 支出の分岐では prior も JPY で絞ったが、既存の plain の分岐は絞っていない(原本の癖、触っていない)。非対称は次に揃える候補。
3. `_dispatch_num_claim` の切り出しは本文を変えない再構成(P6 の門と 1B/5F の差 0 で裏づけ)。
4. 監査の非ブロッキングの記録(REVISE の理由にしない): (i) C-1g 由来の `flow_convention` 分岐で対が無いときの理由は `no_element` のままで、3 分割は plain と支出の分岐にだけ掛かる(封じた規則は分岐別の適用を明示しておらず、ID 単位の予測もこの分岐の分割を求めていない)。(ii) `_direct_value_claim` のもう 1 つの 25 字窓(是認用の「比べて」句)は境界の試験は在るが、変異 H-R5 の対象は `_build_point_diff_claim` の窓だけ。

## 6. 次に直す物・決める物

1. 人間: §4 の「一致」の定義。
2. 1 社目 N013(目標の語が数の後ろ)は残る安全側の誤り。後ろの語を見る規則は別に封じてから。
3. plain の文章分岐の prior も JPY で絞るか(§5.2 の非対称)。
4. S-1(将棋側、[計画](CORE_CONNECTION_S1_PLAN_2026-10-06.md)、封 `fa827f7`)の実装へ。
5. `flow_convention` 分岐の理由の分割と、2 つ目の 25 字窓の変異(§5.4)。必要になったときに別に封じてから。

## 7. この文書がしないこと

Core の変更。P1・P5F・P6 の変更。「一致」の定義を司令塔が変えること。
