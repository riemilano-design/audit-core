# 封: 包装(pip で入る・CLI 2 本・英語の README 1 枚)― **新しい能力は足さない**

2026-10-20(下書きは 2026-10-19)。売却戦略(`~/Desktop/sgogi-coach-handoff/AUDIT_CORE_EXIT_STRATEGY_2026-10-19.md` §5 線 3 の 4)。
人間の指示(2026-10-19): 技術に特化・制約なし。**engine のコードは 1 行も変えない**(包装だけ)。
**0 USD。通信しない**(pip は `--no-build-isolation` で、この機械に在る setuptools だけで組む)。

この機械の道具(封の時点で実測): Python 3.9.6・pip 21.2.4・setuptools 58.0.4・wheel 0.37.0。
**PEP 621(`[project]` 表)は setuptools ≥ 61、PEP 660(`setup.py` 無しの editable)は pip ≥ 21.3 が要る**ので、
metadata は `setup.cfg` に書き、`pyproject.toml` は `[build-system]` だけ、`setup.py` は 2 行の shim にする。

---

## §0 何をするか

買い手が「製品の形」と認める最低線を揃える。**判定の規則・比較の算術・Adapter の中身は触らない。**

| # | 足す物 | 中身 |
|---|---|---|
| 1 | `pyproject.toml`・`setup.cfg`・`setup.py`(audit-core 直下) | setuptools。package は `audit_core`(`core/py/audit_core`)と `adapters`(+ `adapters.xbrl`・`adapters.kokkai`・`adapters.shogi`)。**依存 0**(標準ライブラリのみ)。Python ≥ 3.9。License は専有(repo の根の `LICENSE`: Yushi Yamanaka。`setup.cfg` は `license = Proprietary`、classifier は `License :: Other/Proprietary License` だけ。OSS の classifier を付けない) |
| 2 | console script 2 本 | `audit-core-verify-document` = `adapters.xbrl.verify_document:main` / `audit-core-verify-external` = `adapters.xbrl.verify_external:main` |
| 3 | `README.en.md`(audit-core 直下) | 英語 1 枚。**数は全部 `fixtures/**/*.json` の記録から引き、門で縛る**(§0-1 の記録だけを使う)。負けの数(表計算で LLM 単体 24/24・Core 12/24)を先頭に置く |
| 4 | `tests/measure/test_packaging.py` | 下の予測 G-1〜G-6 を門にする(venv を作る試験は **`AUDIT_CORE_PACKAGING=1` のときだけ**走る。普段の `pytest` は遅くしない)。README の数と禁止語の門は常に走る |

**触る file は上の 4 行 + この封の門 `tests/measure/test_packaging_seal.py` + 結果の文書 `docs/PACKAGING_RESULT_2026-10-20.md` と門 `tests/measure/test_packaging_result.py` + 記録 `fixtures/packaging_2026-10-20.json` + 覆いの記録 2 本(`fixtures/suite_coverage_2026-10-16.json`・`docs/SUITE_COVERAGE_2026-10-16.md`)。**これ以外に触らない**(10-19 の監査の観察: 付随 file も一覧に入れる)。
**触らない**: `core/`・`adapters/` のコード・`run_tests.sh`・既存の試験・`README.md`(日本語の正本)。

### §0-1 README が引いてよい記録(字で固定)

| 数 | 記録 | 鍵 |
|---|---|---|
| 注入した穴が通った 24/24・18/18・24/24 | `fixtures/xbrl/cd8/attr_inject_2026-10-17.json` | `**第 1 部 注入**/{単位,期間(注入),次元}/**誤って通した**` |
| 製品の経路での保留 18/18・24/24・24/24、再現 192/192 | `fixtures/xbrl/cd8/holds_product_path_2026-10-19.json` | `**実測**/F-6`・`F-4` |
| 正解の参照先の保留 0/50 | `fixtures/xbrl/cd8/period_unit_hold_2026-10-19.json` | `**第 2 部 露出の帯(状態は変えない)**/D4 …/{P,U}` |
| 表計算の接続 LLM 24/24・Core 12/24(誤接続 0・保留 12) | `fixtures/sheet/poc_ab_score_2026-10-17.json` | `arms/*/正解集合` |
| 誤り検出 LLM 8/8・旧 C 4/8・C′ 8/8(上書き 0) | `fixtures/sheet/errdet_cprime_2026-10-19.json` | `方式ごとの内訳/seat1`・`旧 C(2026-10-17)との突き合わせ/seat1` |
| 議事録の小さな誤りの通過 1/49 | `fixtures/kokkai/false_pass_round12_2026-10-15.json` | `passed`・`n` |
| 試験 file 本数・収集本数 | `fixtures/suite_coverage_2026-10-16.json` | `test_files_on_disk`・`commands/pytest/tests` |
| 変異の本数 | `tests/adapters/xbrl/mutations.json` | 行数 |
| Core の行数 | `core/py/audit_core/*.py` | `wc -l`(門がその場で数える) |

## §1 事前予測(**実装前に固定**)

| | 予測 | **外れ方** |
|---|---|---|
| **G-1** | 新しい venv で `pip install -e . --no-build-isolation` が **rc=0**。repo の外の cwd から `python -c "import audit_core, adapters.xbrl.verify_external"` が **rc=0** | 失敗(package-dir の写像の誤り) |
| **G-2** | `audit-core-verify-external --help` と `audit-core-verify-document --help` が **rc=0** | どちらか失敗 |
| **G-3** | `pip wheel . --no-deps --no-build-isolation` で wheel が 1 本でき、中の `.py` の本数 = **保護面の 36 本**(`fixtures/frozen_bundle_sha.py` の `FROZEN_COUNT`)。`.py` 以外の file は metadata だけ | 本数が違う(package の列挙漏れ・余計な file) |
| **G-4** | `pytest --collect-only -q` の本数は pyproject を置く**前後で同じ**(pytest の設定を書かないので rootdir も変わらない) | 変わる |
| **G-5** | 覆いの検査(`suite_coverage`)は試験 file **+2**(`test_packaging.py`・`test_packaging_result.py`)で、漏れは既存の 1 本(`measure/tests/test_inject.py`)のまま | 漏れが増える |
| **G-6** | `README.en.md` の数はすべて §0-1 の記録と一致(門)。禁止語(`accurate`, `world's first`, `only`, `unique`, `guarantee`)**0 件** | 1 つでも |

## §2 言えないこと

- 包装は能力ではない。**数は 1 つも増えない。**
- `pip install` できることは「動く」の証拠であって「正しい」の証拠ではない。
- 英語 README は日本語の正本の**抜粋**で、正本は日本語の文書と記録のまま。
- この機械で組めることは、新しい setuptools・pip で組めることの証拠ではない(測っていない)。
