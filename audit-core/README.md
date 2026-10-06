# audit-core

AI が出した文章の主張(Claim)を、証拠(Evidence)へのポインタと契約(Contract)で機械が照合し、GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND / UNVERIFIABLE の 4 状態で返す監査の Core。将棋の対局後診断(このリポジトリの `scripts/playtest/`)が最初の顧客、EDINET の XBRL が 2 番目。

- 設計の正本: [docs/CLAIM_CONTRACT_SPEC_v0.2.md](docs/CLAIM_CONTRACT_SPEC_v0.2.md)(4 層)。経緯と封じた予測は [docs/](docs/)(README の一覧は [../docs/README.md](../docs/README.md))。
- 接続の工程: [docs/CORE_CONNECTION_C0_2026-10-06.md](docs/CORE_CONNECTION_C0_2026-10-06.md)(封印)→ [docs/CORE_CONNECTION_C1_PLAN_2026-10-06.md](docs/CORE_CONNECTION_C1_PLAN_2026-10-06.md) → [docs/CORE_CONNECTION_C1C_PREDICTION_2026-10-06.md](docs/CORE_CONNECTION_C1C_PREDICTION_2026-10-06.md)(C-1c の予測、封印) → [docs/CORE_CONNECTION_C1C_RESULT_2026-10-06.md](docs/CORE_CONNECTION_C1C_RESULT_2026-10-06.md)(C-1c の結果、066eb13) → [docs/CORE_CONNECTION_C1D_PREDICTION_2026-10-06.md](docs/CORE_CONNECTION_C1D_PREDICTION_2026-10-06.md)(C-1d の予測、封印) → [docs/CORE_CONNECTION_C1D_RESULT_2026-10-06.md](docs/CORE_CONNECTION_C1D_RESULT_2026-10-06.md)(C-1d の結果、25f33e9) → [docs/CORE_CONNECTION_C1E_CLASSIFICATION_2026-10-06.md](docs/CORE_CONNECTION_C1E_CLASSIFICATION_2026-10-06.md)(C-1e 分類、C-1 の締め) → [docs/CORE_CONNECTION_C1F_PREDICTION_2026-10-06.md](docs/CORE_CONNECTION_C1F_PREDICTION_2026-10-06.md)(C-1f 癖の直しの予測、封印) → [docs/CORE_CONNECTION_C1F_RESULT_2026-10-06.md](docs/CORE_CONNECTION_C1F_RESULT_2026-10-06.md)(C-1f の結果、bd0e62b) → [docs/CORE_CONNECTION_THIRD_PREDICTION_2026-10-06.md](docs/CORE_CONNECTION_THIRD_PREDICTION_2026-10-06.md)(3 社目の予測、封印) → [docs/CORE_CONNECTION_THIRD_RESULT_2026-10-06.md](docs/CORE_CONNECTION_THIRD_RESULT_2026-10-06.md)(3 社目の結果) → [docs/CORE_CONNECTION_C1G_PREDICTION_2026-10-06.md](docs/CORE_CONNECTION_C1G_PREDICTION_2026-10-06.md)(C-1g の予測、封印) → [docs/CORE_CONNECTION_C1G_RESULT_2026-10-06.md](docs/CORE_CONNECTION_C1G_RESULT_2026-10-06.md)(C-1g の結果、3afd0ba) → [docs/CORE_CONNECTION_C2_PLAN_2026-10-06.md](docs/CORE_CONNECTION_C2_PLAN_2026-10-06.md)(C-2 の計画と予測、封印。実装は C-1g の後) → [docs/CORE_CONNECTION_C2_PLAN_2026-10-06_DECISIONS.md](docs/CORE_CONNECTION_C2_PLAN_2026-10-06_DECISIONS.md)(§8 への人間の決定)。
- いまの段: **C-1a(器と移動)まで。Core のコードはまだ無い。**

## 置き場所

| 場所 | 中身 |
|---|---|
| `core/py/audit_core/` | Core(C-1b で作る)。将棋も XBRL も知らない |
| `adapters/xbrl/` | XBRL Adapter(C-1c で作る)。語彙・member・母集団の印・抽出規則 P-1〜P-8 |
| `fixtures/xbrl/` | 探りの JSON・期待値(計器 3 の Golden)・探りの script の系譜・`manifest.json`。**ZIP は置かない** |
| `tests/` | 単体・境界・変異・Golden(C-1b 以降) |
| `docs/` | 設計・予測・結果の文書(`docs/` から 2026-10-06 に移動。履歴は `git log --follow`) |

## 材料と鍵

- 材料の ZIP は `~/.cache/audit-core/edinet/<docID>.zip`。sha256 は `fixtures/xbrl/manifest.json`。無ければ試験は**落ちる**(skip にしない)。
- EDINET API の鍵は環境変数 `EDINET_API_KEY`(`~/.config/edinet/env`)。repo・fixtures・ログに書かない。

## 出典

金融庁 EDINET の開示書類(有価証券報告書。docID と提出日は `fixtures/xbrl/manifest.json`)を、PDL1.0 に従って出典を明記したうえで、機械で抽出・照合して加工したもの。

## 門(C-1b から)

```
python3 -m unittest discover -s audit-core/tests -t audit-core
```
