# Core 接続 C-0: 探りの JSON を Core の 4 層に写す対応表と、変更の分類の予測(封印。2026-10-06)

> **この文書は Core のコードを 1 行も書く前に封じる。C-1(XBRL だけを Core に繋ぐ)・C-2(将棋の門を Core 経由にする)の結果を見て、ここに書いた分類と予測を変えない。**

**位置づけ**: XBRL の探り 5 本([XBRL_PROBE_RESULT](XBRL_PROBE_RESULT_2026-10-06.md) → [5 本目](XBRL_PROBE5_RESULT_2026-10-06.md)、2 社)で、層・form・modifier・scheme の増分は 5 回とも 0、誤りは止まる側、見つかった欠陥 2 つ(母集団・符号)は予測を封じて直した。これ以上 script で探っても測れるのは script なので、Core を繋いで「意味変更 0」を初めて測る工程に入る。C-0 はその最初の 1 便で、**文書と期待値だけ**。人間の決定(2026-10-06): 方針採用、未束縛の意味の表、C-1 → C-2 → 切り出しの順序、フォルダは C-1 で `audit-core/` を切り C-2 の後に別 repo。

## 0. 工程と止まる場所

| 段 | 中身 | 触るもの | 止まる場所 |
|---|---|---|---|
| **C-0**(この文書) | 対応表・未束縛の意味・分類の予測・計器 | 文書・期待値 JSON・README・2 本目/4 本目の結果への追記 | コミットして停止 |
| **C-1** | Core の最小モジュール(4 層のデータ型・比較子と scheme の登録簿・レシピの実行器)+ XBRL Adapter(語彙・member・印・P-1〜P-8)。計器 3 を通す | `audit-core/` を新設。**将棋側は 1 行も触らない** | 計器 3 の結果で停止。3 役(実装・監査)で回す |
| **C-2** | 将棋の門(exit_verification・check_answer・hypothesis の汎用部)を Core 経由にする。計器 1・2・4・5 | `scripts/playtest/` | GO / NO-GO は人間 |
| 切り出し | `audit-core/` を履歴ごと別 repo へ(subtree split)。将棋は版を固定して使う側 | repo の構造 | 人間の決定(公開の可否も) |

## 1. 未束縛の意味(人間が C-0 で固定)

script の「未束縛」を Core の 2 つの状態に落とす規則。**この境界は C-0 で固定し、C-1 の実装で動かさない。**

| script 側の理由 | Core の状態 | 読み方 |
|---|---|---|
| `no_element`・`no_element(unit not in XBRL)`・`no_element(ratio without fact)` | **POINTER_NOT_FOUND** | 指すべき要素が材料に無い |
| `no_prior_member_context` | **POINTER_NOT_FOUND** | 前期の context が無い |
| `no_subject` | **UNVERIFIABLE** | 主語が無く、何を指すか決められない |
| `ambiguous(N elements)`・`ambiguous(member)` | **UNVERIFIABLE** | 候補が複数で決められない |
| `state_word(no line)`・`prior is 0` | **UNVERIFIABLE** | 意味の判断か定義不能 |
| `value_only(no subject)` で GROUNDED | GROUNDED(provenance に `value_only`) | 通すが、経路の札を残す |
| `diff phrase but value matched a fact` で GROUNDED | GROUNDED(provenance に `diff_phrase_direct`) | 同上 |

## 2. 対応表(写す規則は 1 か所、期待値は 2 本)

写す規則は [probe_xbrl_2026-10-06/make_core_expectation.py](probe_xbrl_2026-10-06/make_core_expectation.py)(Core のコードではない。探りの JSON を読んで 4 層に落とすだけ)。出力が C-1 の計器 3 の期待値:

| 期待値 | 元 | Claim 数 | sha256 |
|---|---|---:|---|
| [core_expectation_1B.json](probe_xbrl_2026-10-06/core_expectation_1B.json) | `probe1B_S100Z4Q1.json`(sha `cd0d4596…`、ＤＮホールディングス、百万円・漢数字・比の式の会社) | 91(数 60・文章 31) | `f8a45ecce18a3d98181061a6943449c75a0fbb850e09ec0b71808a45a70fd820` |
| [core_expectation_5F.json](probe_xbrl_2026-10-06/core_expectation_5F.json) | `probe5F_S100Z4B6.json`(sha `3f140d5a…`、エム・エイチ・グループ、千円・増減%・セグメントの会社) | 133(数 91・文章 42) | `a19f3419e1a6e1a0cc87df92ae7717c48049b2fcca89d7e8d7ae0161b994adc4` |

Claim 1 件の写し方(期待値の 1 行の形):

```
Claim      id / kind(num|text) / form(direct_value|derived_value|threshold) / subject / value / unit / word
modifiers  population(consolidated | member:<name> | none) / time_range([(CurrentYear|Prior1Year|Prior2Year, Duration|Instant)…]) / normalization(round|truncate|abs+round|abs+truncate)
evidence   schemes({xbrl, formula, builtin} の部分集合) / pointers(script の pointer をそのまま)
contract   comparator / tolerance
result     state(4 つのどれか) / recomputed / script_reason(照合用。Core には渡さない)
provenance value_only / diff_phrase_direct / sign_token / member_source:(sentence|claim|carried|consolidated|ambiguous)
```

### 2.1 集計(2 本の期待値から。C-1 はこれを Claim 単位で再現する)

| 層 | 値 | 1B | 5F |
|---|---|---:|---:|
| form | direct_value / derived_value / threshold | 39 / 21 / 31 | 72 / 19 / 42 |
| result | GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND / UNVERIFIABLE | 71 / 6 / 7 / 7 | 55 / 14 / 22 / 42 |
| population | consolidated / member / none(未束縛) | 77 / 0 / 14 | 47 / **29** / 57 |
| time_range | 当期 Duration のみ | 22 | 35 |
| | 当期・前期 Duration の対 | 9 | 30 |
| | 当期・前期 **Instant** の対(貸借対照表の項目) | **33** | 0 |
| | 当期 Instant / 前期 Instant / 前期 Duration | 6 / 3 / 3 | 0 / 0 / 4 |
| | **前期・前々期** Instant の対(P-6) | **1** | 0 |
| normalization | round / truncate / abs+round / abs+truncate | 12 / **13** / 13 / **6** | 20 / 0 / 13 / 0 |
| scheme | xbrl のみ / xbrl+formula / xbrl+builtin | 34 / 19 / 24 | 53 / 4 / 12 |
| comparator | equals_within(許容幅つき一致) | 31 | 39 |
| | equals_within(pure×100)(比率の fact) | 3 | 0 |
| | ratio×100(比の式。P-2) | 4 | 0 |
| | pct_change(cur, prior)(増減%。P-8 で符号) | 0 | 14 |
| | diff(a−b) equals_within(差額。P-6) | 15 | 4 |
| | builtin:sign(cur−prior)==direction(文章) | 24 | 12 |
| provenance | value_only / diff_phrase_direct / sign_token / member_source | 1 / 4 / 0 / 0 | 5 / 2 / 15 / 36 |

読み: 2 社で **form 3・modifier 3・scheme 3・比較子 6・状態 4** に全部落ちた。1 社目にしか無いもの(Instant・前々期・truncate・比の式・pure 比率)と 2 社目にしか無いもの(member・増減%・sign_token)があり、**合わせて初めて XBRL Adapter の形が見える**。どちらか 1 社だけで Core を切ると、無い方が「増分」として後から出る。

## 3. 変更の分類の予測(封じる)

分類は [CLAIM_CONTRACT_SPEC_v0.2.md](CLAIM_CONTRACT_SPEC_v0.2.md) の 4 種(0 / 登録追加 / インターフェース拡張 / 意味変更)。**C-1・C-2 でこの表に無い変更が出たら、分類して記録し、Core に入れる前に人間の判断。**

| 変更 | 予測の分類 | 根拠 |
|---|---|---|
| 比較子 6 種(equals_within / pure×100 / ratio×100 / pct_change / diff / sign) | **登録追加 6** | 将棋側に在るのは完全一致・閾値・存在。6 種は全部 Adapter が登録簿に足す |
| scheme `xbrl:`・`formula:` | **登録追加 2**(`builtin:` は将棋の 0 との比較で既存) | 信頼の段つきの scheme 表に 2 行 |
| `population` の値(member・consolidated) | **0**(登録簿は Adapter のデータ) | Core は値を比べるだけ |
| `normalization` の 4 値(round / truncate / abs の組) | **登録追加 1〜2**(将棋に truncate・abs は無い) | 丸めの種類の表 |
| **`time_range`** | **意味変更の候補(予測は 0。1 が出るならここ)** | §4 |
| 派生 Claim の 2 pointer + 式 | **0** | 将棋の再計算(F-1)で既に在る形 |
| UNVERIFIABLE の下位理由(no_subject / ambiguous / state_word)・POINTER_NOT_FOUND の下位理由 | **登録追加 1**(理由の表) | 状態は 4 のまま |
| **`sign_token`・`member_source`・`value_only` の provenance 欄** | **インターフェース拡張 1**(Claim / Result の provenance の欄) | 4 本目 XP5-2。欄が増えるが意味は変えない |
| Core のデータ型の数 | **5**(Claim / EvidencePointer / Contract / Result / Recipe)。6 つ目は出ない | v0.2 の 4 層 + レシピ |
| Core に入る XBRL 固有の文字列 | **0**(`xbrl`・`jppfs`・`EDINET`・事業名・語彙は全部 `audit-core/adapters/xbrl/` 側) | 測り方: Core のモジュールを grep して 0 件 |
| **意味変更の合計** | **0** | 1 本でも出たら NO-GO ではなく「記録して人間の判断」(2 本目の予測 §4 のまま) |

## 4. time_range を意味変更の候補に置く理由(C-1 の前の予測)

将棋の F-2([CLAIM_CONTRACT_SPEC_v0.1.md](CLAIM_CONTRACT_SPEC_v0.1.md) §7): `engine.ply` = `displayPly`、`branches.ply` = `displayPly − 1`。同じ「手数」が材料ごとに 1 ずれ、橋は `displayPly`。XBRL の time_range は contextRef の期間の対(CurrentYear ↔ Prior1Year、P-6 では Prior1Year ↔ Prior2Year)で、対は context 名の接頭辞を置き換えて作っている(`c.context.replace("CurrentYear","") == p.context.replace("Prior1Year","")`)。

どちらも「証拠を取る時間の切片を、主張の側の時間からずらして決める」操作。**危ないのは、Core が「前期 = 当期 − 1」のようなずらしを自分で計算する設計にすること。** そうすると将棋の `−1` と XBRL の `Prior1Year` が同じ規則に見えて、どちらかの既存の挙動が動く(= 意味変更)。

封じる設計の意図と予測:
- Core の `time_range` は **Adapter が解決した鍵(文字列)を比べるだけ**。ずらしの計算(`displayPly − 1`・`CurrentYear → Prior1Year`)は Adapter のレシピに置く。
- この形なら C-2 の関数レベル Golden で将棋側は同値のまま(**意味変更 0**)。
- もし C-1 で「Core に期間の対を作らせないと XBRL の派生が書けない」となったら、それは time_range の意味変更の兆候。**Core を変えずに記録し、人間の判断**。

## 5. 計器(GO / NO-GO はこれで。2 本目の予測 §4 の 4 つ + 5 本目で足した 1 つ)

| # | 計器 | 合格 | 測る段 |
|---|---|---|---|
| 1 | 関数レベルの Golden(T-5 と同じ方法) | 将棋側の呼び出しの結果が接続前後で同値 | C-2 |
| 2 | c5 の Golden Master(`docs/golden_master/c5_expectation.json`) | 不変(rc = 0) | C-2 |
| 3 | 探りの JSON の再現 | `core_expectation_1B.json`・`core_expectation_5F.json` の **224 件**を、Core のレシピ経由で Claim ごとに(state・pointers・recomputed)同値で出す。差が出たら差の全件を表にする | C-1 |
| 4 | Core 変更の分類 | §3 の表に収まる。インターフェース拡張 1 まで。意味変更 0 | C-1・C-2 |
| 5 | 抽出の層の偶然一致 | 0(5 本目 §4。`sign_token` が自分の数でない派生 Claim 0) | C-1 |

## 6. フォルダと repo

- C-0: 置き場所は `docs/` のまま(移動を 2 回しない)。
- C-1: `audit-core/` を repo 直下に新設。`core/`(4 層・登録簿・実行器)、`adapters/xbrl/`(語彙 73 + 1・member の対応・印・P-1〜P-8・EDINET 取得)、`fixtures/`(探りの JSON と期待値)、`docs/`(`XBRL_*`・`CLAIM_CONTRACT_*`・`CORE_CONNECTION_*` をここへ移し、`docs/README.md` のリンクを同じコミットで直す)。
- C-2 が通ったら `audit-core/` を履歴ごと別 repo へ。将棋は版を固定して使う側。新 repo の作成と公開の可否は人間。

## 7. この文書がしないこと

- Core のコードを書かない。`scripts/playtest/` を触らない。`audit-core/` を作らない。
- 探りの script・JSON・予測・結果を変えない(2 本目・4 本目の結果への**日付つき追記**だけ、このコミットで入れる)。
- C-1 の実装の設計(関数名・ファイル構成)を決めない。それは C-1 の計画で、3 役で回す。
