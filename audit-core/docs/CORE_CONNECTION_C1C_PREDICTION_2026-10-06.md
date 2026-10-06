# Core 接続 C-1c(XBRL Adapter)の予測 ― 実装の前に封じる

**日付**: 2026-10-06 **段**: C-1c(C-1 計画 [CORE_CONNECTION_C1_PLAN_2026-10-06.md](CORE_CONNECTION_C1_PLAN_2026-10-06.md) §4) **前提**: C-1b 完了 `f917f02`(Core 本体 4 本、監査 GO)
**封の手順**: この文書をコミットしてから `adapters/xbrl/` を書き始める。文書は後から書き換えない(訂正は結果の文書に書く)。予測は司令塔の席だけ(人間の予測の欄は空欄。人間は 5 点の固定条件を出した)。

## 1. 固定する 5 点(人間の指示、2026-10-06)

1. **探りの script の原本は変更しない。** `fixtures/xbrl/xbrl_probe*.py` は系譜として残す。Adapter は原本を import しない(写す)。
2. **Adapter から Core を呼ぶ。Core から Adapter を import しない。**
3. **XBRL 固有の知識は Adapter 側。** 語彙(主語 → 要素名)・member・EDINET・P-1〜P-8・XBRL の context・Current/Prior 等の期間の解決を Core に入れない。
4. **C-0 の期待値 224 件(`core_expectation_1B.json` / `_5F.json`)は変更しない。** 差が出たら Adapter の移植差として扱う。期待値を書き換えて緑にすることは禁止。
5. **C-1c の終わりでは計器 3 を最終判定しない。** Adapter 単体で期待値と同じ Claim の列(id・form・subject・value・pointer)が出る所で止まる。Core と繋いだ 224 件の照合(state・recomputed)は C-1d。

司令塔が足した締め(人間が「進めて」で採用): 前段照合の相手は probe の生 JSON ではなく **期待値 JSON の Claim の層**。**1B(91)も入れて 224 件**。Adapter は原本を **写す**(import しない)+ **系譜の試験**で漂いを機械で捕まえる。**通信 0**。

## 2. 材料(sha256)

| 物 | sha256 |
|---|---|
| `fixtures/xbrl/xbrl_probe.py`(1 本目、516 行) | `896492a7…` 系譜の根。import 時の `SUBJECTS` は 39 語、`PROBE_RUN=B` で 73 語 |
| `fixtures/xbrl/xbrl_probe3.py`(399 行)/ `_probe4.py`(326)/ `_probe5.py`(312) | `3d2092a9…`(3) / `f25652f0…`(4) / `275ae50e…`(5) |
| `fixtures/xbrl/core_expectation_1B.json`(91 件) | `f8a45ecce18a3d98181061a6943449c75a0fbb850e09ec0b71808a45a70fd820` |
| `fixtures/xbrl/core_expectation_5F.json`(133 件) | `a19f3419e1a6e1a0cc87df92ae7717c48049b2fcca89d7e8d7ae0161b994adc4` |
| `fixtures/xbrl/probe1B_S100Z4Q1.json` / `probe5F_S100Z4B6.json` | `cd0d4596…` / `3f140d5a…` |
| `~/.cache/audit-core/edinet/S100Z4Q1.zip` / `S100Z4B6.zip` | `0731a291f10af5dd…` / `d617b6e1807c8aa6…`(manifest.json と同じ) |
| Core 本体 4 本(`f917f02`) | `__init__` `9aea7f9e…` / `model` `a65e285c…` / `registry` `38ac65a5…` / `verify` `d29b21dc…` |

既知(C-1c の前に測ってある): `probe5R1_S100Z4Q1.json`(5 本目の写しを member OFF・P-8 ON で 1 社目に当てたもの)は `probe1B` と Claim の全欄で一致(差 0 件、本日 14 時台に照合)。つまり **1 本目の設定(member OFF・語彙 73・印 OFF)で 1 社目を回せば 1B が出る**ことは機械で分かっている。**最終設定(member ON・語彙 74・印 ON・P-8 ON)で 1 社目を回したことは無い**(§6 の追加計測 X)。

## 3. 割り方

```
audit-core/adapters/__init__.py
audit-core/adapters/xbrl/
├── __init__.py
├── edinet.py       ZIP の置き場(~/.cache/audit-core/edinet/<docID>.zip)・sha256 の照合・取得(鍵は環境変数 EDINET_API_KEY の名前だけ。C-1c の試験は取得を呼ばない)
├── instance.py     ZIP → facts / contexts / textblocks / names(load_instance)、strip_html、plain_context・ctx_ok、facts_for(member 対応版)、
│                   member_denominator、labels_from_zip、MD&A textBlock の選び方
├── extract.py      NFKC・文の切り方(re.split(r"(?<=。)|\n"))・paragraph_index、iter_numbers(NUM_RE・AMOUNT_JP_RE・EXCLUDE_AFTER・EXCLUDE_CONTEXT)、
│                   PCT_DIR_RE・PCT_RATIO_RE・own_sign_match(P-8)、subject_of(P-3)、DIRECTION_WORDS・STATE_WORDS、
│                   build_registry(ラベル → 事業名)・resolve_members(文単位、CARRY_BACK 5、AMBIG)・claim_member_B(Claim 単位、MARK_CONSOL「全社」・CONN_RE)
├── vocabulary.py   SUBJECTS(1 本目の 39 + Run B の 34 = 73、先頭に 4 本目の 1 行「セグメント利益 → OperatingIncome」= 74)、PROFIT_SUBJECTS、UNIT_SCALE、
│                   tol_of、match_value(round / truncate / abs。P-4・P-5)、profile(§3.2)
├── recipes.py      1 文書の Claim の列を作り、Core の Recipe(Claim・Pointer・Contract・unverifiable_reason / not_found_reason)へ写す。
│                   候補の選び方(hits[0]・pairs[0]・cur[0]・差額 a−b・diff phrase・value_only・名/人・pure)は原本の main の分岐のまま。
│                   未束縛の理由 → Core の状態は C-0 §2 の表(make_core_expectation.py の STATE)
└── run.py          docID と ZIP から Claim の層の JSON(期待値と同じ鍵の形)を書く CLI。C-1d で Core の verify_all に繋ぐ入口にもなる
```

**Core を import するのは `recipes.py` と `run.py` だけ。** `edinet` / `instance` / `extract` / `vocabulary` は Core を知らない(境界試験 B-2 を Adapter 側にも置く)。

### 3.2 profile(設定の束)

Adapter は設定を 2 つの名前で持つ。両方とも Adapter の知識(Core には無い)。

| profile | member 束縛 | 語彙 | Claim 単位の印(B) | P-8 | 元の探り |
|---|---|---|---|---|---|
| `P1` | OFF | 73 | OFF | ON でも OFF でも同じ(1 社目に増/減% の束縛 Claim は 0。既知) | 1 本目 Run B = `probe1B` |
| `P5F` | ON(ラベルだけ、手書き 0) | 74 | ON | ON | 5 本目 Run F = `probe5F` |

前段照合は `P1` × S100Z4Q1 ↔ 期待値 1B、`P5F` × S100Z4B6 ↔ 期待値 5F。探りの門(Gate 2・3)と同じ対応。

## 4. 前段照合の定義(C-1c の止まる所)

- **比べる欄(7)**: `id`・`form`・`subject`・`value`・`unit`・`modifiers`(population / time_range / normalization)・`evidence.pointers`(文字列の列、順序込み)。
- **比べない欄**: `contract`(名前は作るが C-1d で)・`result`・`provenance`(C-1d)。`kind`・`word` は id で決まるので比べる欄に含めてよい(含めても数は変わらない見込み)。
- **鍵の形**: Core の `Modifiers.time_range` は文字列の組なので、Adapter は `("CurrentYear/Duration", "Prior1Year/Duration")` の形で持ち、照合では期待値の `[["CurrentYear","Duration"],…]` と同じ物として比べる(写し方は照合 script の 1 行、両側に同じ正規化)。population は `consolidated` / `member:<local name>` / `None` の文字列。
- **1 回目の実行を保存する。** Adapter が初めて 224 件を出した時の JSON と差の表(Claim ごと・欄ごと)を `fixtures/xbrl/c1c_first_run_{1B,5F}.json` と結果文書に残す。その後の移植差の直しは「何を・なぜ・何件動いたか」を表にする。**期待値は 1 byte も変えない**(sha で確認)。
- **門**: 直し終わりで 224/224 の 7 欄一致。これが C-1d へ進む条件。達しなければ差の表を人が読む(期待値の方が誤っていると人が裁定した時だけ別の段で扱う)。

## 5. 系譜の試験(原本を import しない代わりに置くもの)

`tests/adapters/xbrl/test_lineage.py`。原本は `importlib` で `fixtures/xbrl/` から読み(原本の `main` は `__main__` 判定の内側なので import は安全)、Adapter の物と **値で**比べる(字面ではない)。

1. **定数**: NUM_RE・AMOUNT_JP_RE・EXCLUDE_AFTER・EXCLUDE_CONTEXT・PCT_DIR_RE・PCT_RATIO_RE・CONN_RE の `.pattern` と flags、SUBJECTS(P1 = `PROBE_RUN=B` の 73、P5F = 先頭に VOCAB4 の 74)、DIRECTION_WORDS、STATE_WORDS、PROFIT_SUBJECTS、UNIT_SCALE、MARK_CONSOL、CARRY_BACK、AMBIG。
2. **関数レベル Golden**(2 書類の MD&A の全文、1 社目 119 文・2 社目 136 文): `iter_numbers`・`subject_of`(両 profile)・`match_value`(全 fact × 全数の組は多いので、原本 main と同じ呼び方で現れる組だけ)・`tol_of`・`own_sign_match`・`claim_member_B`・`resolve_members`・`paragraph_index`・`strip_html`・`load_instance`(facts の件数・contexts・textblocks の名前)・`member_denominator`・`labels_from_zip`・`build_registry` が、原本と同じ入力で同じ出力。
3. **ZIP が無ければ落ちる**(skip にしない)。

これが C-1c の「false pass」の定義でもある: 前段照合が 224/224 でも、関数レベルで原本と違う出力をする物があれば、それは偶然の一致(将来の書類で割れる)として記録し、直す。

## 6. 予測(司令塔の席。人間の欄は空欄)

| # | 項目 | 予測 | 外れたら何を疑うか |
|---|---|---|---|
| 1 | 前段照合 1 回目、1B(91 件)7 欄全部一致 | **91 / 91** | 文の切り方・NFKC・Run B の語彙の順(先頭に足す) |
| 2 | 前段照合 1 回目、5F(133 件)id・form・value・unit | **133 / 133** | 数の抽出(P-1)・P-8 の窓 |
| 3 | 同、subject | **133 / 133** | 語彙 74 の順(「セグメント利益」を先頭に) |
| 4 | 同、pointers と modifiers | **130〜133 / 133** | 候補の順序(facts の走査順・`hits[0]`・`pairs[0]`・`cur[0]`)、member の候補(ctx_ok の `== [member]`)、Claim 単位の印の群の作り方 |
| 5 | 224 件のうち 7 欄全部一致(1 回目) | **221〜224** | 上の 4 |
| 6 | 移植差の直し(1 回目 → 門まで) | **0〜3 件**、期待値の修正 **0** | 3 件を超えれば「写し」ではなく「書き直し」になっている |
| 7 | Core 本体 4 本の sha | **不変**(門) | ― |
| 8 | 実装担当が出す Core への変更要求 | **0〜1 件**(候補: `Claim.provenance` に入れる欄の形、`Modifiers.time_range` の文字列の形) | 2 件以上なら C-0 の予測(インターフェース拡張 1)が崩れる兆し。C-1e で分類 |
| 9 | Adapter の行数(試験を除く) | **700〜1100** | 原本 4 本 1553 行には main の写し 3 回分が含まれる |
| 10 | モジュール数 | **6**(+ `__init__` 2) | ― |
| 11 | Adapter の試験 | **25〜60 本**、変異 **8〜14 本**(両向き、予測を先に) | ― |
| 12 | 通信 / 鍵の値 | **0 / 0**(門) | ― |
| 13 | **追加計測 X(記述)**: `P5F` × S100Z4Q1 を 1B の Claim の層と比べる | 差 **0〜4 件**。出れば出どころは member 束縛(1 社目の文に事業名が現れるか)か語彙の 1 行 | 期待値は変えない。C-1d で「1B は P1 で比べる」ことの根拠になる |
| 14 | 系譜の試験 | 関数レベル Golden は **全部一致**(門)。一致しない関数が出れば、それが「原本を書き直した」場所 | ― |

**書かない予測**: 所要時間。費用は 0(LLM・API を使わない)。

## 7. 止まる所と C-1d への引き継ぎ

- C-1c で止まる: 前段照合 224/224 + 系譜の試験 + Adapter 単体試験 + 変異 → 監査 GO → コミット(パス指定)。
- C-1d に渡す物: `run.py` の Claim の層 JSON、`recipes.py` の Recipe の列、比較子 6 と scheme・normalization・理由の登録(`register_all(registry)` は C-1d で書く。C-1c では Contract の名前だけ)。
- C-1c で **やらない**: 比較子の実体、Core の `verify_all` に繋ぐ、state の照合、Core の変更(要求は文書に書くだけ)。

## 8. 3 役

実装担当(新規セッション、`adapters/` と `tests/adapters/` と `fixtures/xbrl/c1c_first_run_*.json` だけ触る、コミットしない)→ 凍結(sha 一覧)→ 監査担当(独立。系譜の試験を自分で回す、1 回目の JSON が「直す前」の物か、期待値の sha 不変、原本 4 本の sha 不変)→ GO で司令塔がコミット。REVISE の指摘は累積で渡す。
