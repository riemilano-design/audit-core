# Core 接続 C-1 の計画: `audit-core/` を切り、XBRL だけを Core に繋ぐ(2026-10-06、司令塔)

**前提**: [CORE_CONNECTION_C0_2026-10-06.md](CORE_CONNECTION_C0_2026-10-06.md)(コミット `6c6973b`、封印)。C-1 は C-0 の計器 3(224 件の再現)と計器 5(抽出の偶然一致 0)を通し、計器 4(分類)を集計して止まる。**将棋側(`scripts/playtest/`・`apps/`・`data/`)は 1 行も触らない。** 計器 1・2(将棋の Golden)は C-2。
**この文書は計画で、コードは含まない。** C-1b 以降は 3 役(司令塔・実装担当・監査担当)で回し、動きを変える変更は監査の GO を経てから承認する(CLAUDE.md 承認の委任・条件 1)。

## 1. 置き場所と言語

[AUDIT_CORE_EXTRACTION_PLAN.md](AUDIT_CORE_EXTRACTION_PLAN.md) §6.3 の段階 2 の案(`core/ts` + `core/py`、`adapters/`、`tests/`)を同一 repo の直下に **`audit-core/`** の名で切る(C-0 §6。抽出計画の仮名 `audit-platform/` は使わない ― 売るものは platform でなく core、という 2026-10-06 の整理に合わせる)。

- **C-1 は Python だけ。** 理由: XBRL の探りは Python、将棋側の Core 候補のうち T-5 で切り出した汎用部(`exit_verification.py`)も Python。TS の門(`hypothesis.ts` H-1〜H-11・`packetRef`・`observationPacket`)をどう繋ぐかは **C-2 の範囲の人間判断**(§7)。
- 依存は標準ライブラリだけ(探りと同じ)。新しいパッケージを入れない。

```
audit-core/
├── README.md                     目的・出典(EDINET、PDL1.0 の出典と加工の明記)・門の回し方・置かないもの
├── core/py/audit_core/           Core。将棋も XBRL も知らない
│   ├── model.py                  Claim / EvidencePointer / Contract / Result / Recipe(v0.2 の 4 層 + レシピ。データ型は 5 つまで = C-0 の予測)
│   ├── registry.py               scheme の表(信頼の段)・比較子の表・丸めの表・理由の表。登録は Adapter が呼ぶ
│   ├── verify.py                 レシピの実行器: pointer の解決(Adapter の resolver を受け取る)→ 比較子 → Result(state・recomputed・provenance)
│   └── __init__.py
├── adapters/xbrl/                XBRL Adapter(探り 1→3→4→5 の script を機能ごとに割る。語彙・member・印・P-1〜P-8 はここ)
│   ├── edinet.py                 取得(鍵は環境変数。repo に置かない)・ZIP の sha 照合・ローカルの置き場(§4)
│   ├── instance.py               load_instance(.xbrl / iXBRL)・context・label linkbase
│   ├── extract.py                文の切り方・数と語の抽出(P-1〜P-8。正規表現は探りのまま)
│   ├── vocabulary.py             主語 → 要素名(73 + 1。会社ごとに育つ登録簿として JSON で持つ)・member のラベル対応・母集団の印
│   ├── recipes.py                Claim + Contract + pointer の組み立て(direct / derived / threshold、母集団の解決、期間の対の作り方 ― **ずらしはここ**。C-0 §4)
│   └── run.py                    1 書類 → Claim ごとの Result の一覧(JSON)
├── fixtures/xbrl/                探りの JSON・期待値・script の系譜(`docs/probe_xbrl_2026-10-06/` を移す)。ZIP は置かない(manifest に sha だけ)
├── tests/
│   ├── core/                     Core 単体 + 境界の試験(§5 B-1)+ 変異(両向き)
│   ├── adapters/xbrl/            抽出・語彙・母集団の単体 + 変異
│   └── golden/                   計器 3(224 件)・計器 5
└── docs/                         `XBRL_*`・`CLAIM_CONTRACT_*`・`CORE_CONNECTION_*`・`AUDIT_CORE_*` を `docs/` から移す(リンクは同じコミットで直す)
```

## 2. 段(各 1 コミット。止まる場所を決めておく)

| 段 | 中身 | 誰が | 承認 | 止まる |
|---|---|---|---|---|
| **C-1a** 器 | `audit-core/` の骨組み・README・`.gitignore`(ZIP・ローカルの置き場)・文書と fixtures の移動・`docs/README.md` のリンク修正・manifest(ZIP の sha 2 本) | 司令塔 | 文書だけ → 司令塔が承認 | リンク切れ 0 を機械で確かめて停止 |
| **C-1b** Core | `model` / `registry` / `verify` と単体試験・境界の試験(B-1〜B-3)・変異 | 実装担当 | 監査 GO → 司令塔 | 試験緑 + 変異両向き赤で停止 |
| **C-1c** Adapter | 探りの script を `adapters/xbrl/` に割る。**探りの script 自体は fixtures に残して触らない**(系譜の証拠) | 実装担当 | 監査 GO → 司令塔 | 単体試験 + 計器の前段(Adapter 単体で `probe5F` と同じ Claim 列を出す: id・form・subject・value・pointer)で停止 |
| **C-1d** 計器 3・5 | Adapter + Core で 2 書類を回し、`core_expectation_1B/5F.json` の 224 件と(state・pointers・recomputed)で照合。差は全件を表に。`sign_token` 0 件が別の数 | 実装担当 → 監査 | 監査 GO | 結果を文書化して停止 |
| **C-1e** 分類 | 計器 4: C-1 で Core に入った変更を全部列挙し、C-0 §3 の予測と照合(登録追加 / インターフェース拡張 / 意味変更)。XBRL 固有の文字列が Core に 0 件(grep) | 司令塔 | 人間(C-2 に進むか) | **停止** |

## 3. Core の形(C-1b の実装担当への約束。関数名は実装担当が決める)

- **Claim**: id / form(direct_value・derived_value・aggregate・threshold)/ subject / value / unit / modifiers{population, time_range, normalization} / provenance{spans, sign_token, member_source, …}。
- **EvidencePointer**: scheme / locator / 結合の手順(派生は pointer の列 + 式)。Core は locator の中身を解釈しない。**解決は Adapter の resolver**(pointer → 値・単位・精度)に委ねる。
- **Contract**: comparator(登録簿の名前)/ tolerance / formula / reference(閾値は registry: のポインタ、構造の 0 は builtin:)。
- **Result**: state(GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND / UNVERIFIABLE)/ recomputed / achieved_depth / provenance(どの pointer をどう解決し、どの比較子で、どの理由か)。
- **Recipe**: Claim + Contract + pointer を作る側(Adapter)の出力。Core は Recipe を受けて Result を返すだけ。
- **time_range**: Core は Adapter が解決した鍵(文字列)の一致だけを見る。「前期 = 当期 − 1」の類の計算を Core に書かない(C-0 §4)。
- **登録簿は Adapter が起動時に登録する**(比較子 6・scheme 2・丸め・理由)。Core の既定の登録は `builtin:` と完全一致だけ。

## 4. 材料の置き場と鍵

- ZIP は repo に置かない。**ローカルの置き場は `~/.cache/audit-core/edinet/<docID>.zip`**(2026-10-06 に 2 本を scratchpad から写した: S100Z4Q1 sha `0731a291…`、S100Z4B6 sha `d617b6e1…`)。`fixtures/xbrl/manifest.json` に docID・sha・提出日・出典を書く。
- 試験は ZIP が無いとき **落ちる**(skip にしない。「測っていないものは緑にしない」)。鍵(`EDINET_API_KEY`)があれば取得して sha を照合してから使う。
- 鍵は `~/.config/edinet/env` のまま。repo・fixtures・ログに書かない(試験で grep)。
- 出典: EDINET(金融庁)の開示書類。PDL1.0 に従い、README と manifest に出典と加工(抽出・照合)を明記する。

## 5. 試験の約束(監査担当の点検表)

- **B-1 境界**: `core/py/audit_core/` の import を静的に走査し、`scripts/`・`apps/`・`adapters/` を import しない。`xbrl`・`jppfs`・`EDINET`・事業名・将棋語(`shogi`・`ply`・`sfen`・`usi`)が Core のソースに 0 件(禁止語の一覧は JSON 1 本)。
- **B-2 方向**: `adapters/xbrl/` は Core を import してよい。Core は Adapter を import しない。
- **B-3 鍵**: 全ファイルに `EDINET_API_KEY=` の値の形が 0 件。
- **変異は両向き**(TESTING_STRATEGY)。比較子を 1 つ無効にすると計器 3 が赤、丸めの表を緩めると赤、母集団の置き換えを「合わせる」に変えると赤(T025 型の証拠の層の false pass が復活する向き)、符号を `search` に戻すと計器 5 が赤。各変異の**予測を先に書く**([[predict-at-the-granularity-that-can-fail]])。
- **期待値は手で直さない**。計器 3 が赤なら、差を表にして Adapter か Core のどちらの意味が違うかを人が読む。期待値を変えるのは「探りの script の方が誤っていた」と人が判定したときだけ(そのときは探りの結果文書に追記)。
- 門の回し方: `python3 -m unittest discover -s audit-core/tests -t audit-core`(標準ライブラリだけ)。将棋側の 2 本の門(vitest・typecheck)には C-1 では入れない(C-2 で統合)。

## 6. C-1 の予測(C-0 §3 に加えて封じるもの)

| 項目 | 予測 |
|---|---|
| 計器 3 の初回の一致 | 224 件中 **210〜224**。差が出るなら「`value_only` の候補の順序(`hits[0]`)」「`ambiguous(N elements)` の N の数え方」「`diff phrase but value matched` の分岐」の 3 か所(探りの script の暗黙の順序に依存しているところ) |
| 期待値を直す必要 | **0 件**(差は Adapter の写し漏れとして Adapter 側で直す) |
| Core のデータ型 | 5 |
| Core の行数 | 300〜600 行(登録簿と実行器が主。比較子の実体は Adapter 登録) |
| Adapter の行数 | 探りの script 4 本の合計(約 1,300 行)の 70〜90%。重複(main の写し 3 回)が消える分だけ減る |
| 変異の本数 | Core 8〜12・Adapter 10〜16。黙る変異 0 |
| C-0 §3 の分類から外れる変更 | 0〜1(出るなら provenance の欄の形) |
| 意味変更 | 0 |

## 7. 人間に決めてもらうこと(C-1 に入る前・途中)

1. **フォルダ名 `audit-core/`** でよいか(抽出計画の仮名は `audit-platform/`)。
2. **文書と fixtures の移動**を C-1a でやってよいか(`docs/` の 15 本前後と `docs/probe_xbrl_2026-10-06/`。リンクは同じコミットで直す。git の履歴は `--follow` で追える)。
3. **C-2 の言語の範囲**: 将棋の門のうち Python(`exit_verification.py`・`check_answer.py` の汎用部)だけを Core 経由にするか、TS(`hypothesis.ts` 等)も含めるか。TS を含めるなら Core を 2 言語で持つか、JSON の契約で跨ぐかの設計が先に要る。**C-1 には影響しない**が、Core の形(§3)を TS に写せる範囲に留めるかに効く。
4. **出典の文言**(README・manifest に書く EDINET / PDL1.0 の表記)。
5. 新しい repo の名前と公開の可否は **C-2 の後**(いまは決めなくてよい)。
6. ブランチ: 現状どおり `feature/phase7-recognition-spec` 上で段ごとに 1 コミットとする(並行セッションとパス指定コミットの運用を変えない)。別ブランチにするなら指示を。

## 8. この文書がしないこと

- コードを書かない。`audit-core/` を作らない(C-1a は人間の 1〜2 の返答の後)。
- C-0 の予測と期待値を変えない。将棋側を触らない。
