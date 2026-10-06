# Claim Contract Specification v0.2 ― 4 層への整理(2026-10-06、司令塔。Q-1〜Q-6・H-A の人間の決定を反映)

**この版の性格**: [v0.1](CLAIM_CONTRACT_SPEC_v0.1.md)(測った時点の記録。書き換えない)と [決定](CLAIM_CONTRACT_DECISIONS_2026-10-06.md)を受けて、主張・証拠ポインタ・契約・結果の **4 層**に組み直した仕様。設計書であって実装ではない。**Core のコード・データ・schema・試験は触らない。** XBRL を繋ぐ前の予測は別文書([XBRL_ADAPTER_PREDICTION_2026-10-06.md](XBRL_ADAPTER_PREDICTION_2026-10-06.md))で、この版と同じコミットで封じる。

---

## 0. v0.1 からの変更(要点)

| v0.1 | v0.2 | 由来 |
|---|---|---|
| 修飾 3 → 実測で 6 | **修飾は 3 のまま。** `source_kind` は Evidence Pointer の scheme、`join` は検証レシピの操作、`verification_depth` は契約が要求する深さと結果が到達した深さ | 決定 §2 |
| `approval_record` を契約の欄に | **欄にしない。** 線の登録簿に値・比較子・承認を束ね、Evidence Pointer(`registry:`)で解決する。解決しなければ POINTER_NOT_FOUND | Q-1・Q-2 |
| 比較子は契約の固定値 | **比較子は線と一緒に登録簿にある。** LLM は線の id だけを書く。構造上の 0 との比較(存在・空でない・等しい)だけは承認なし | Q-1 |
| `INCONCLUSIVE` を結果状態に足す提案 | **足さない。** 予測台帳の結果の主張が minN で落ちた UNVERIFIABLE。顧客向けは固定文(H-7 承認済み) | Q-5 |
| 主張どうしの整合の欄 | **足さない。** 両方を保持して個別に検証。人の確認の表で同じ subject を隣に並べる(表示の規則) | Q-6 |
| 顧客向けの予測の扱い | **PREDICTIVE は成立条件を満たすものだけ。** H-4 の欄 + 封じたコミットの時刻 + 事象時刻との順序検査。満たさなければ descriptive(測る数の登録) | Q-3 |
| c5 の線 0.7・2 倍 | 登録簿に載せない。線の記述は `code:` で GROUNDED、採用の主張は POINTER_NOT_FOUND(§8) | H-A |

---

## 1. 4 層

```
┌─ Claim ───────────────────────────────────────────────┐
│ form(4)+ modifiers(population / time_range / normalization) │
│ value・subject・span                                    │
└───────────────┬───────────────────────────────────────┘
                │ 1 つ以上
┌─ Evidence Pointer ────────────────────────────────────┐
│ scheme + locator(+ 結合の手順 = レシピがどう組み立てるか)   │
└───────────────┬───────────────────────────────────────┘
                │ 契約が検査する
┌─ Contract(form ごと)───────────────────────────────────┐
│ 必須欄・許す scheme・要求する深さ・許容幅・線の id(registry) │
└───────────────┬───────────────────────────────────────┘
                │ 検証が返す
┌─ Result ──────────────────────────────────────────────┐
│ 状態(4 語)+ 到達した深さ + 出所(何を・いつ・どこから取ったか) │
└───────────────────────────────────────────────────────┘
```

**LLM が書けるのは Claim と Evidence Pointer だけ。** 契約は人が登録し、結果は Core が付ける。UNVERIFIABLE は結果であって、Claim には書けない。

---

## 2. Claim(主張)

### 2.1 Form(4 つ。v0.1 §3.1 と同じ)

| form | 主張の形 | 値 |
|---|---|---|
| `direct_value` | X は v である | 1 つの値 |
| `derived_value` | X から式で計算すると v である | 式と入力 |
| `aggregate` | 母集団 P のうち条件 Q を満たすものが n(/ d) | 件数・分子分母・合計 |
| `threshold` | 値 v は線 t について成り立つ | 真偽。**比較子は書かない**(線の登録簿にある) |

### 2.2 Modifier(3 つ)

| modifier | 何を決めるか |
|---|---|
| `population` | 母集団の表と絞り込み(where)・分子の絞り込み(numeratorWhere) |
| `time_range` | 事象時刻の範囲・基準日(「当期」「前年同期」「今月」の解決に要る) |
| `normalization` | 正規化の規則 id の**並び**(順序つき。例: 鏡映 → USI → 漢字表記 → tags → 語。F-3) |

### 2.3 Claim の欄

| 欄 | 必須 | 意味 |
|---|---|---|
| `claim_id` | ✔ | 一意 |
| `form` | ✔ | 2.1 |
| `modifiers` | △ | 2.2 |
| `span` | ✔ | 顧客に見える文の区間(§6 の束縛) |
| `subject` | ✔ | 何について(顧客・局・局面・集計 id・会社・期) |
| `value` | ✔ | 主張している値(threshold は線の id と値の pointer) |
| `pointers` | ✔(1 つ以上) | §3 |

---

## 3. Evidence Pointer(証拠ポインタ)

### 3.1 形

```
<scheme>:<locator>
```

| scheme | locator の形 | 信頼の段 | 解決の先 |
|---|---|---|---|
| `packet:` | packet の path(文法は `lib/packetRef.ts`) | **正準データ**(顧客向けのデータの主張を根拠づけてよい) | `resolvePacketPath` |
| `aggregate:` | 集計行の id | 正準データ(宣言された集計行。深さは `value_match`) | packet.aggregates |
| `registry:` | 登録簿の id(線・行動の表・形の定義・固定文) | **承認状態を持つ唯一の scheme**。線の承認・比較子・値はここだけから取る | `ANSWER_MENU`・`provenance.thresholds`・`data/`(reviewStatus) |
| `code:` | module.定数.鍵 | **道具についての主張だけ**を根拠づける(「道具の仮置きの線は 0.7」は可。顧客向けのデータの主張は不可) | ソースの定数 |
| `files:` | 材料のファイル名・path | 材料の存在と名前だけ(対応表のファイル名。F-4) | ディレクトリ |
| `document:` | 文書自身の行・節 | 文書についての主張だけ(「数は 3 つ」「2 つです」) | 文書 |
| (XBRL 候補)`xbrl:` / `filing:` | 要素名 + contextRef / 提出書類の meta | 正準データ / meta | 予測文書で封じる |

**契約が form ごとに許す scheme を列挙する**(§4)。許されない scheme の pointer は Claim Validation で落ち、UNVERIFIABLE。

### 3.2 結合の手順(join は修飾ではなくここ)

`aggregate` と `derived_value` の pointer は、複数の表を鍵で結んで母集団を組み立ててよい。鍵には**鍵の約束の正規化**が付く(F-2: `engine.ply` = 表示の手数、`branches.ply` = 表示の手数 − 1、橋は `displayPly`)。結合の手順は pointer の一部として LLM が書くが、**鍵の約束の表は登録簿にある**(LLM が発明しない)。

---

## 4. Contract(契約。form ごとに人が登録する)

| 欄 | direct | derived | aggregate | threshold | 意味 |
|---|---|---|---|---|---|
| `allowed_schemes` | ✔ | ✔ | ✔ | ✔ | 許す scheme(§3.1)。顧客向けのデータの主張は `packet:`・`aggregate:`・`registry:` だけ |
| `required_depth` | `value_match` | `recount` | `recount`(packet が `recountable: false` なら `value_match` を許し、顧客にその区別を出す) | `value_match` | 要求する深さ |
| `formula` | ― | ✔ | ― | ― | 式(入力 id → 出力) |
| `tolerance` | △ | ✔ | ― | ― | 許容幅(人が承認した数を字で留める。`registry:` で解決) |
| `threshold_ref` | ― | ― | ― | ✔ | 線の id。**`registry:` で解決し、値・比較子・承認状態をそこから取る**。構造上の 0(存在・空でない・等しい)だけは `registry:` 無しで `builtin:exists` / `builtin:equals` を許す(Q-1) |
| `min_population` | ― | ― | △ | △ | 分母の下限(minN。`registry:ANSWER_MENU.*.minN`) |
| `unit` | △ | ✔ | ✔ | ✔ | 単位(packet の enum か登録簿) |

**Claim Validation**: 必須欄が 1 つでも欠ける・許されない scheme・`threshold_ref` が無い threshold → **UNVERIFIABLE**(LLM は選べない。Core が付ける)。
**pointer が解決しない**(登録簿に線が無い・packet の列が無い)→ **POINTER_NOT_FOUND**(Validation は通るが Fetch で止まる)。この区別が H-A の 2 行を作る(§8)。

---

## 5. Result(結果)

| 欄 | 値 |
|---|---|
| `state` | `GROUNDED` / `VALUE_MISMATCH` / `POINTER_NOT_FOUND` / `UNVERIFIABLE`(4 語。増やさない) |
| `achieved_depth` | `value_match` / `recount`。GROUNDED のときだけ。契約の `required_depth` に届かなければ GROUNDED にしない |
| `provenance` | 何を(pointer と取得した値)・いつ(検証の時刻)・どこから(packet id / registry の版 / code の commit) |
| `messages` | 現行の `CheckResult.messages` の字(G-9 の記録を壊さない) |

**INCONCLUSIVE は無い。** 予測台帳(§7)の結果の主張が `min_population` で落ちると UNVERIFIABLE になり、顧客向けには固定文「今回の数からは、明確な差は確認できませんでした。」(接続設計案 H-7、人間承認 2026-09-30)。
**CONTRADICTED は無い。** 両立しない主張は個別に検証する。人の確認の表(§6.4)で同じ `subject` を隣に並べる。

---

## 6. Claim Binding(束縛。Core の 10 番目)

### 6.1 生成側(将棋の冊子。在る)

検証済みの値から文を生成する。`<!-- agg: id -->`・`<!-- menu: Mx -->`・`<!-- pos: -->`・`<!-- ans: -->`・固定文(v0.1 §8.1)。印 = Claim ID。

### 6.2 監査側(他者の AI の出力。無い。製品になるのはこちら)

```
他者の文 → Claim Extraction(LLM: span → Claim + pointers。UNVERIFIABLE は書けない)
        → Claim Validation → Fetch → Verification → 札
        → 出力は止められない。束縛率と結果の分布を出す
```

抽出の失敗と本当の検証不能を機械は区別できない。区別は人の札(§6.4 の列 7)。

### 6.3 束縛率(v0.1 §8.3 と同じ)

| 数 | 定義 |
|---|---|
| 主張区間数 | 主張を持つ区間(固定文・人間の文・見出しは分母に入れない) |
| Binding Rate | 束縛数 / 主張区間数 |
| 検証通過率 | GROUNDED / 束縛数(分母は束縛数。束縛率と一緒にしか意味を持たない) |
| UNVERIFIABLE 率と内訳 | 札で分ける |
| 未束縛区間 | 一覧で出す |

### 6.4 人の確認の表(列の定義)

| 列 | 中身 |
|---|---|
| 1 原文の区間 | 行と文字列 |
| 2 Claim ID | 無ければ未束縛 |
| 3 Form + Modifiers | |
| 4 Evidence Pointers | scheme つき |
| 5 Contract | どの契約で検査したか |
| 6 Result | state + achieved_depth |
| 7 札(人) | UNVERIFIABLE: `extraction_failure` / `binding_failure` / `genuinely_unverifiable`。GROUNDED: `claim_matches_span` / `claim_narrower_than_span` |

**表示の規則**: 同じ `subject` の主張を隣に並べる(Q-6)。札は捨てずに溜める(抽出器を測る唯一のデータ)。

---

## 7. Prediction Ledger(予測台帳)

| 項目 | 定義 |
|---|---|
| 予測の Claim | H-4 の欄そのまま: `metric`(aggregate の id)・`comparator`・`value`・`window`・`writtenAt` |
| Registration Time | **予測を封じたコミットの時刻**(`git log --format=%ci`)。`writtenAt` の文字列は参考 |
| Event Time | **データ自身の時刻**(KIF の開始日時・XBRL の提出日)。mtime は使わない |
| PREDICTIVE の成立 | 上の欄が全部在り、かつ `registration_time < min(event_time of 照合データ)` |
| 満たさない表 | **descriptive**(測る数の登録)。c5 の答え合わせの表は比較子が無いのでこれ(C-32)。PREDICTIVE と呼ばない |
| 結果の主張 | 「次の N 局で metric が comparator value」= threshold 形の Claim。`min_population` を契約に持つ |
| 結果 | 結果の主張が GROUNDED → CONFIRMED、VALUE_MISMATCH → REFUTED、`min_population` で UNVERIFIABLE → 顧客向け固定文(§5)。台帳の語は 2 つ + UNVERIFIABLE で、新しい状態は作らない |

---

## 8. c5 を v0.2 の語で読み直す(新しい測定ではない。v0.1 §7 の 45 単位の再分類)

v0.1 の 3 値(A 表現可・充足 / B 表現可・不充足 / C 表現不能)を、v0.2 では**結果の状態**で読む。変わるのは次の 3 群だけ。

| 群 | v0.1 | v0.2 | 理由 |
|---|---|---|---|
| 構造上の 0 との比較(C-02・C-10「両方の側に残った」) | B | **A → GROUNDED**(`builtin:exists`) | Q-1 |
| 線が登録簿に無い threshold(C-03・C-09・C-13・C-26・C-30) | B | **A → POINTER_NOT_FOUND**(`threshold_ref = registry:thresholds.M4.line` が解決しない) | Q-2・H-A。Validation は通り、Fetch で止まる |
| 線の記述(C-26・C-30 の前半「仮置きの線は 0.7」「2 つぶん」) | (C-26・C-30 に含めていた) | **A → GROUNDED**(`code:check_answer.MENU_THRESHOLDS.M4.line`、道具についての主張) | H-A |
| 線の無い比較の語(C-05・C-16・C-29・C-36b・C-36c「多く・目立った・出やすかった」) | B | **B → UNVERIFIABLE**(`threshold_ref` が書けない) | 変わらず |
| 網羅・選別(C-01b・C-23b) | B | B → UNVERIFIABLE | 変わらず |
| 形の外(C-17・C-18・C-31b・C-31c・C-32・C-33) | C | C(C-32 は descriptive の登録として台帳に置ける) | 変わらず |

| 数 | v0.1 | v0.2 の読み直し |
|---|---|---|
| A | 25 | **32**(25 + 構造上の 0 の 2 + 線の threshold 5) |
| B | 14 | **7** |
| C | 6 | 6 |
| A のうち GROUNDED にならないもの | ― | **5**(POINTER_NOT_FOUND。線の承認が無い) |

**読み方**: 「表現できる」と「通る」は別で、v0.2 は後者を結果の状態で言う。線の 5 件が POINTER_NOT_FOUND で止まるのは、**人が選んだ線は承認の証拠が無ければ検証可能な線として扱わない**という契約を実データで確かめた例(H-A)。送付済みの冊子は変えない。

---

## 9. Core の 10 項目(v0.1 §2)との対応

| # | 構成要素 | v0.2 での層 |
|---|---|---|
| 1 | Claim Contract Registry | Contract(§4)+ 登録簿(線・行動の表・形・固定文・鍵の約束・正規化の規則) |
| 2 | Claim Validation | §4 の必須欄・scheme の検査 |
| 3 | Canonical Fetch | §3 の scheme ごとの解決 |
| 4 | Deterministic Verification | §4 のレシピ(式・再計算・比較)+ 許容幅 |
| 5 | Result State | §5(4 語) |
| 6 | Provenance | §5 の `provenance` |
| 7 | Prediction Ledger | §7 |
| 8 | Human Approval Gate | **`registry:` scheme の承認状態に畳まれた**(特別な門ではない) |
| 9 | Meta Audit | Golden Master・境界試験・変異(変わらず) |
| 10 | Claim Binding | §6 |

---

## 10. 将棋側で動くもの(確定監査 §3.2 との対応。実装の GO ではない)

| v0.2 の層 | 現行の機構 | 足りないもの |
|---|---|---|
| Claim | hypothesis v0.4 の行(statement・observations・prediction) | form と modifiers の欄(契約の版上げ = 人間の承認) |
| Evidence Pointer | `packetRef.path`(scheme 無し。`packet:` 固定) | scheme。I-6(文法の注入)がその入口 |
| Contract | H-1〜H-11・門 (i)〜(xi)・検査 1〜7 に散った欄 | 登録簿としての束ね(確定監査 §4「`PacketSpec` は今も存在しない」と同じ話) |
| Result | `CheckResult{check, ok, messages}` | 4 語と `achieved_depth`(G-9 の字は壊さない: `messages` に残す) |
| Prediction Ledger | H-4・`status` enum | 封じたコミット時刻と事象時刻の順序検査 |
| Binding | 印 4 種 + 固定文 + 型からの再構成 | 監査側(無い) |

---

## 11. この版がしないこと

- コード・schema・試験・data は触らない。契約の版上げ(form・modifiers・scheme の欄)は人間の承認。
- XBRL は調べていない。予測を同じコミットで封じ(別文書)、その後に実物を調べる。
- 監査側の抽出器(LLM)の設計はしない。
- H-B(2 冊目の答え合わせの表に比較子と向きを出すか)は 2 冊目の前に人間が決める。
