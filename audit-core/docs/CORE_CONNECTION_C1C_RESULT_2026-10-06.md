# Core 接続 C-1c(XBRL Adapter)の結果 ― 予測との突き合わせ

**日付**: 2026-10-06 **予測の封**: [CORE_CONNECTION_C1C_PREDICTION_2026-10-06.md](CORE_CONNECTION_C1C_PREDICTION_2026-10-06.md)(コミット `88a64c6`、sha `ad1f5646…`、本文は不変) **実装**: 3 役(実装担当 1 席、監査担当 1 席、司令塔) **監査**: GO(独立の監査担当、1 回で GO、REVISE 0) **コミット**: `066eb13`(Adapter・試験・証拠 JSON、27 ファイル)

## 1. 何を測ったか

- 門: `python3 -X pycache_prefix=<一時> -m unittest discover -s audit-core/tests -t audit-core` → **Ran 168 tests OK**(Core 57 本は不変 + Adapter 111 本)。司令塔が自分で 2 回回した。
- 前段照合(予測 §4): 期待値 JSON の Claim の層を 9 欄(id・form・subject・value・unit・population・time_range・normalization・pointers = 予測の 7 欄で modifiers を 3 つに割ったもの)で比べた。1 回目の出力は `fixtures/xbrl/c1c_first_run_1B.json`(sha `6a78bce9…`)・`_5F.json`(`1a3546f9…`)・差の表 `c1c_first_run_diff.json`(`da3baceb…`)。
- 不変の確認(sha256): Core 4 本(`f917f02` のまま)、期待値 2 本(`f8a45ecc…` / `a19f3419…`)、原本 4 本(`896492a7…` / `3d2092a9…` / `f25652f0…` / `275ae50e…`)、予測文書。
- 「直す前」の裏付け: `recipes.py` の最終更新 14:32:02 < 1 回目の JSON 14:34:30。1 回目の後に Adapter 本体は変更されていない(移植差の直し 0 と整合)。

## 2. 予測 §6 との突き合わせ(司令塔の席)

| # | 項目 | 予測 | 実測 | 当否 |
|---|---|---|---|---|
| 1 | 1 回目 1B 全欄一致 | 91/91 | **91/91** | ○ |
| 2 | 1 回目 5F id・form・value・unit | 133/133 | **133/133** | ○ |
| 3 | 同 subject | 133/133 | **133/133** | ○ |
| 4 | 同 pointers・modifiers | 130〜133 | **133/133**(上端) | ○ |
| 5 | 224 件の全欄一致(1 回目) | 221〜224 | **224**(上端) | ○ |
| 6 | 移植差の直し / 期待値の修正 | 0〜3 / 0 | **0 / 0** | ○ |
| 7 | Core 4 本の sha | 不変 | **不変** | ○(門) |
| 8 | Core への変更要求 | 0〜1 | **0** | ○ |
| 9 | Adapter 行数(試験除く) | 700〜1100 | **1214**(edinet 71・instance 212・extract 221・vocabulary 151・recipes 454・run 81・__init__ 24) | **×**(+10%) |
| 10 | モジュール数 | 6 | **6** | ○ |
| 11 | 試験 / 変異 | 25〜60 / 8〜14 | **111 / 10** | **×** / ○ |
| 12 | 通信 / 鍵の値 | 0 / 0 | **0 / 0** | ○(門) |
| 13 | 追加計測 X(P5F × S100Z4Q1 と 1B) | 差 0〜4 | **0/91**(`c1c_x_P5F_S100Z4Q1.json` `43bea75c…`) | ○ |
| 14 | 系譜の試験 | 全部一致 | **25 本 OK**(定数 15 項目、関数 Golden 13 関数 × 1 社目 119 文・2 社目 136 文) | ○(門) |

当たり 12 / 外れ 2。外れは両方とも「量」(行数と試験本数)で、向きは同じ(過小)。数の予測(#1〜#5・#13)は全部**範囲の上端**に落ちた。

### 2.1 上端に揃ったことの読み

「全部当たった = 粒度が粗い」(探り 1 本目の教訓)に照らすと、#4・#5・#6・#13 が揃って最良に落ちたのは、予測の範囲が広すぎた印でもある。ただし今回は「写し」であり、系譜の試験(関数レベル Golden)が全部通っている以上、224/224 は偶然ではなく構造の帰結。**次に同種の予測を書くときは、写しの段では「差 0」を点で予測し、外れたら写しの失敗と読む**方が粒度に合う。範囲を持たせるのは「書き直し」の段(C-1d の比較子の実体など)。

### 2.2 行数と試験本数の外れ

- 行数 1214: recipes.py が 454 行。原本 main の分岐(直接・比・増減%・差額・diff phrase・value_only・名/人・pure・no_element 系)を 1 つも落とさず写し、さらに Core の Recipe への変換と C-0 の理由の表を持つため。予測は「main の写し 3 回分が重複」を差し引きすぎた。
- 試験 111: 系譜 25 + 単体 67 + 前段 3 + 境界 8 + 変異 5 + run 3。予測 25〜60 は系譜と前段と変異だけを数えていて、単体試験の量を見積もっていなかった。

## 3. 変異(両向き、予測を先に)

10 本(red 8・green 2)、予測 = 実測 10/10。表は `tests/adapters/xbrl/mutations.json`。

**記録すべき途中経過**: authoring 中に 2 本が等価変異だった。(a) `match_value` の round の境界 `<=` → `<`、(b) `claim_member_B` の接続語の判定を常に真。どちらも 2 社の実データでは **その分岐に到達する入力が無い**(境界値ぴったりの差・接続語を介さない事業名の隣接)。実装担当は凍結前に変異を強化(round を丸ごと外す・群の異なり数の検査を外す)して red にし、`note` に経緯を残した。これは規則(予測を書いてから回す・結果に合わせて予測を書き換えない)の範囲内だが、**XP-C1c-1**: 2 社では到達しない分岐が少なくとも 2 つある。3 社目でその分岐が初めて動く可能性があり、動いたときの正しさはまだ測られていない。

## 4. 実装担当が自分で決めた点(11)と司令塔の扱い

| # | 決定 | 扱い |
|---|---|---|
| 1 | P-8(own_sign_match)は P1 でも常時適用 | 可。X(P5F × 1 社目)でも差 0、1 社目に増/減% の束縛 Claim が 0 という既知と整合 |
| 2 | run.py に未使用の `audit_core` import(C-1d の入口の印) | 可。C-1d で使われなければ外す |
| 3 | `is_consolidated`(原本の未使用関数)を写さず | 可。系譜の試験の対象外として明記 |
| 4 | run.py の出力の最上位 `{document, profile, claims}` | 可(前段照合は recipes を直接呼ぶので依存しない) |
| 5 | `Claim.provenance` の鍵名 sentence/span/word/value_only/diff_phrase_direct/sign_token/member_source/kind/schemes | 可。**C-1e の分類の材料**(C-0 の「インターフェース拡張 1」= provenance 欄、の実体がこれ) |
| 6 | prior is 0 は pointers を残しつつ unverifiable_reason も立てる(224 件中 0 件) | 可。Core の verify は unverifiable_reason を先に見るので矛盾しない。C-1d で 0 件のままか見る |
| 7 | 系譜の P5F 語彙は `[VOCAB4] + SUBJECTS(B)` を手で組んで比較 | 可(原本の main は API 時代の経路) |
| 8 | 変異の対象から test_lineage を外し test_claim_layer を入れた | 可。期待値 JSON は原本の出力から独立に C-0 で封じた物なので、同じ表の照合ではない |
| 9 | 等価変異 2 本の強化 | 可(§3) |
| 10 | `adapters/__init__.py` に sys.path 追加 | 可 |
| 11 | 境界試験の重複(鍵の値) | 可。重複は害が無い |

Core への変更要求 0。provenance の形(決定 5)と `Modifiers.time_range` の文字列の形(`"CurrentYear/Duration"`)は、Core を変えずに Adapter 側で吸収できた。**C-0 の予測「意味変更 0」は C-1c でも保たれている。**

## 5. 境界(人間の固定 5 点の照合)

| 固定 | 確認 |
|---|---|
| 1 原本不変 | 原本 4 本の sha 不変。Adapter は原本を import しない(系譜の試験だけが importlib で読む) |
| 2 向き | `audit_core` を import するのは recipes.py・run.py のみ。edinet/instance/extract/vocabulary は標準ライブラリと互いの import だけ。Core に `adapters` の文字列 0 |
| 3 XBRL 知識は Adapter | 語彙 73/74・member・ラベル linkbase・P-1〜P-8・context の鍵・Current/Prior の対はすべて adapters/ 内。Core の禁止語の試験は 57 本の中で不変 |
| 4 期待値不変 | 2 本の sha 不変、1 回目で 224/224 なので「直して緑」は起きていない |
| 5 計器 3 は最終判定しない | 比較子の実体・verify_all への接続・state の照合は未着手(C-1d) |

## 6. C-1d への引き継ぎ

- 入口: `adapters.xbrl.recipes.build_recipes(doc, profile)` → Recipe の列、`run.py` の CLI。
- C-1d で書く物: 比較子 6 の実体と `register_all(registry)`(scheme・normalization・理由)、Adapter の resolver(pointer → Resolved)、224 件の state・recomputed の照合(計器 3)、`sign_token` 0 件の別計器(計器 5)。
- C-1d の予測を書く前に見ておく物: XP-C1c-1(到達しない分岐 2 つ)、決定 6(prior is 0 の経路)、provenance の鍵名(C-1e)。

## 7. 監査

独立の監査担当の判定は **GO**(REVISE 0)。監査担当が自分で測ったこと:

- 凍結 sha 36 行を開始時と終了時に照合、全部一致。Core 4 本・原本 4 本・期待値 2 本・ZIP 2 本・予測文書の sha を独立に再照合。
- 門 168 本 OK を 2 回。前段照合は `recipes.build_recipes` を直接呼んで 224 件を独立に再現(差 0)。追加計測 X も再現(差 0)。
- 1 回目の JSON: Adapter 本体 5 本の最終更新より後、公式試験より前の時刻で、現在のコードで `run.py` を再実行すると完全一致。「直す前」の文字どおりの証明は transcript が無いので不可、と明記したうえで主張と整合。
- 系譜の試験: `_material.py` が importlib で原本を `PROBE_RUN=B` で読み(73 語の根拠)、定数は `.pattern`/`flags` の値比較、関数 Golden は 119/136 文の全件を回している。
- 変異 3 本を自分で当てた(一時コピー、本体の sha 不変): R3 再現 = red(**ただし 224 件の門は赤くならず、単体試験だけが捕まえた**)、R5 再現 = red(5F の N020/N043/N047 の符号反転。探り 5 本目 Run F の記録と同じ ID)、subject_of の tie-break 削除 = green(等価変異)。
- 境界: AST 走査で向きを確認、Core に `adapters` 0、鍵の値 0、偽の HOME で ZIP が無いとき skip でなく `FileNotFoundError` で落ちる。
- 決定 11 点は全部受け入れ。`is_consolidated` は原本でも呼び出し 0 のデッドコード。prior is 0 の経路は Core の verify が pointers を先に文字列化してから短絡する設計と整合。

**非ブロッキングの記録事項(監査)**: `test_extract.py` の tie-break の試験は名前(長い語を優先)と中身(同じ語の重複同士の競合)がずれている。本体は原本の写しで欠陥ではない。

### 7.1 XP-C1c-2: 224 件の門が見えない分岐

監査の MY-1 と MY-3、実装担当の等価変異 2 本を合わせると、**2 社の実データでは到達しない分岐が 4 つ**ある。

| 分岐 | 何が到達しないか | 今それを守っている物 |
|---|---|---|
| `ctx_ok` の `== [member]`(置き換え、合わせない) | member を 2 つ以上持つ context を区別する実例 | 単体試験(合成データ)だけ。224 件の門は黙る |
| `match_value` の round の境界 `<=` | 差がちょうど単位/2 の数 | 無し(変異を強化して回避) |
| `claim_member_B` の接続語の判定 | 接続語を介さず隣接する事業名 | 無し(同上) |
| `subject_of` の tie-break(同じ終わりなら長い語) | 終わりが同じで長さの違う語の競合 | 無し(等価変異) |

これは C-1c の欠陥ではなく **224 件という材料の限界**。3 社目でこれらの分岐が初めて動く可能性があり、動いたときの正しさは単体試験(合成)でしか測られていない。C-1d の予測を書くとき、計器 3 の「224/224」がこの 4 分岐について何も言わないことを前提に書く。

## 8. 止まる所

C-1c はここで止まる。計器 3(state・recomputed の 224 件照合)・比較子の実体・`register_all`・resolver は C-1d。C-1d の予測は別の文書で封じてから書く。
