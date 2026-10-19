# 包装(pip で入る・CLI 2 本・英語の README 1 枚)の実測 ― **予測 当たり 5 / 外れ 1(G-1)**

2026-10-20。封 `docs/PACKAGING_SEAL_2026-10-20.md`(commit `f4d956b`。実装より先)。
**engine(`core/`・`adapters/`)は 0 行変更。0 USD・通信しない**(pip には常に
`--no-build-isolation` と `--no-index` を渡した。PyPI には触れていない)。
正本は `fixtures/packaging_2026-10-20.json`。

---

## §1 欄ごとの当たり/外れ

| | 予測 | 実測 | 判定 |
|---|---|---|---|
| **G-1** | 新しい venv で editable install が rc=0 かつ、repo の外の cwd からの combined import が rc=0 | install は rc=0。**combined import は rc=1**(`ModuleNotFoundError: No module named 'audit_core'`) | **外れ** |
| **G-2** | 2 本の console script が `--help` で rc=0 | 両方 rc=0(editable venv・非 editable venv の両方で確認) | 当たり |
| **G-3** | wheel が 1 本、中の `.py` が保護面の 36 本、他は metadata だけ | wheel 1 本(`audit_core-0.1.0-py3-none-any.whl`)、`.py` **36 本**、他 5 本は全部 `*.dist-info/*` | 当たり |
| **G-4** | `pytest --collect-only -q` の本数が pyproject を置く前後で同じ | 3363 → 3363(**試験 file を 1 本も足す前**に測った) | 当たり |
| **G-5** | 覆いの検査が試験 file +2、漏れは既存の 1 本のまま | `test_files_on_disk` 176 → **178**、`tests/measure` 118 → **120**、漏れは `measure/tests/test_inject.py` のまま 1 本 | 当たり |
| **G-6** | README の数が全部記録と一致、禁止語 0 件 | 数は §0-1 の記録の鍵からそのまま引いた(下記 §2)。禁止語 0 件 | 当たり |

## §2 G-1 の外れの原因 ― **1 件**

**原因**: この機械の setuptools(58.0.4)は PEP 660 を持たない。`pip install -e .` は
内部で `setup.py develop` を呼び、これが作る egg-link(`easy-install.pth`)は
**repo の根 1 つだけ**を `sys.path` に足す。`setup.cfg` の `package_dir` で
`core/py/audit_core` に写した `audit_core` パッケージは repo の根には実在しないので、
`import audit_core, adapters.xbrl.verify_external` のように **`audit_core` を先に**
評価する combined import では解決できない(`adapters` を先に import すれば、
`adapters/__init__.py` が元から持つ `sys.path.insert(0, core/py)` ―
engine 側の既存コードで今回 1 行も変えていない ― が効いて解決するが、それは封が
書いた import の順序ではない)。

**確認**: 同じ `--claims`・`--out` を要求しない `--help` は、`adapters.xbrl.verify_document`
モジュールの読み込み時点で `import audit_core as core` が走るため、**editable でも
rc=0 になる**(G-2 が当たった理由)。つまり外れているのは「`audit_core` という
名前を combined import で直接引く経路」だけで、CLI としての動作には影響しない。

**追加の実測(封 G-1 の判定には使わない)**: 非 editable(`pip install .`、PEP 517 の
通常ビルド)では、`audit_core` が venv の site-packages 直下に実体として配置されるので
install・combined import とも **rc=0**。

## §3 G-6 の数(全部 `fixtures/packaging_2026-10-20.json` 経由で記録から引いた)

| README の数 | 記録 | 鍵 |
|---|---|---|
| 24/24(一般 LLM、接続) | `fixtures/sheet/poc_ab_score_2026-10-17.json` | `arms/A1 一般 LLM(sonnet)/正解集合` |
| 12/24(Audit Core、接続。保留 12・誤接続 0) | 同上 | `arms/B Audit Core/正解集合` |
| 24/24・18/18・24/24(注入が通った) | `fixtures/xbrl/cd8/attr_inject_2026-10-17.json` | `**第 1 部 注入**/{単位,期間(注入),次元}/**誤って通した**` |
| 18/18・24/24・24/24(製品の経路での保留)・192/192(再現) | `fixtures/xbrl/cd8/holds_product_path_2026-10-19.json` | `**実測**/F-6`・`F-4` |
| 0/50(正解の参照先の保留) | `fixtures/xbrl/cd8/period_unit_hold_2026-10-19.json` | `**第 2 部 露出の帯(状態は変えない)**/D4 …/P` |
| 8/8(一般 LLM)・4/8(旧 C)・8/8(C′)・上書き 0 | `fixtures/sheet/errdet_cprime_2026-10-19.json` | `方式ごとの内訳/seat1`・`旧 C(2026-10-17)との突き合わせ/seat1` |
| 1/49(議事録の小さな誤りの通過) | `fixtures/kokkai/false_pass_round12_2026-10-15.json` | `passed`・`n` |
| 178(試験 file 本数) | `fixtures/suite_coverage_2026-10-16.json` | `test_files_on_disk` |
| 96(変異の本数) | `tests/adapters/xbrl/mutations.json` | 配列の要素数(`len()`) |
| 429(Core の行数) | `core/py/audit_core/*.py` | `wc -l` の合計(`__init__.py` 40・`model.py` 138・`registry.py` 112・`verify.py` 139) |

## §4 G-3 の sha256 について ― **測ったことだけ書く**

同じ木から `pip wheel` を 3 回回すと、**3 回とも違う sha256**(size は 115262 バイトで同じ)。

| 回 | sha256 |
|---|---|
| 1 | `fea99a13fc945ec2e3bce026080ef2c0c9cc2584f24471af32214795899d97af` |
| 2 | `21d0f25515c35cad98c50ea5915374ff6f232b0af9742cf5255090190f08f793` |
| 3 | `31821a789accb16816fb4d70597967918acc626eace8d7e85a4f120a457e47b5` |

内訳の `.py` 36 本・metadata 5 本は 3 回とも同じ。原因を断定しない(測っていない)。
**sha256 は同一性の証拠にせず、中身(`.py` の本数と一覧)で確かめた。**

## §5 言えないこと(封 §2 のまま)

- 包装は能力ではない。**数は 1 つも増えていない。**
- `pip install` できることは「動く」の証拠であって「正しい」の証拠ではない。
- 英語 README は日本語の正本の抜粋。正本は日本語の文書と記録のまま。
- この機械(setuptools 58.0.4・pip 21.2.4)で組めることは、新しい setuptools・pip
  (PEP 660 対応)で組めることの証拠ではない。**editable install は依然 rc=1。**

## §6 独立監査: REVISE 1 回(2026-10-20)

**独立監査: REVISE 1 回(README の領域名 2・分母 1・時系列 1)→ 直した。**
封 §1 の G-1〜G-6 の予測欄・当たり/外れの表(§1)は変えていない(REVISE は
README.en.md の字の正確さに対するもので、封の予測欄の対象ではない)。

直した 4 か所:

1. **領域名の取り違え(errdet)**: 「Error detection (national-parliament-minutes
   domain, …)」→「Error detection (spreadsheet domain, …)」。`errdet_cprime_2026-10-19.json`
   の入力は `fixtures/sheet/errdet_answers_seat1_2026-10-17.json` 等(表計算、
   R001〜R035、予算現額・支出済額)で、議事録ではない。
2. **「同じ領域」の誤用(false-pass)**: 「… in the same domain: 1/49」→
   「… in the national-parliament-minutes domain (a separate dataset): 1/49」。
   `false_pass_round12_2026-10-15.json` は議事録の別の材料で、直前の bullet
   (表計算)と同じ領域ではない。
3. **分母の出どころ(sheet 接続)**: 「On a 24-document spreadsheet-reconciliation
   benchmark」→「On a 24-claim gold-confirmed subset (of 35 claims checked against
   a single spreadsheet)」。`poc_ab_score_2026-10-17.json` の 24 は正解集合の
   **主張(claim)の数**で、書類(スプレッドシート)は 1 つ。
4. **時系列(attribute-injection probe)**: 「… and the production hold rule is
   bypassed」→「… (measured 2026-10-17, before the production hold rules described
   in the next bullet existed)」。製品の経路の hold 規則(`adapters/xbrl/holds.py`)
   は 2026-10-19 の commit `295e636` で新設されたもので、2026-10-17 の注入実測の
   時点ではまだ存在しなかった。**「迂回した」のではなく、まだ無かった。**

門: `tests/measure/test_packaging.py` の `ReadmeDomainPairTest`(4 本)が、
数の bullet・段落に領域名・分母の出どころ・時系列の字が**同じ場所**に在ることを縛る。
直す前の README(scratchpad に保存)をこの門に in-memory で通すと 4 本とも赤に
なることを確認した(木の file は書き換えていない)。

## §7 独立監査: REVISE 2 回目(2026-10-20)

**独立監査: REVISE 2 回目(覆いの再生成漏れ・README の旧 C の字)→ 直した。**
封 §1 の G-1〜G-6 の予測欄・当たり/外れの表(§1)は変えていない。

1. **覆いの再生成漏れ**: §6 の門を 4 本足した(`test_packaging.py` が
   25 → 29 試験 method)のに、`measure/suite_coverage_2026-10-16.py --write` を
   走らせていなかった。本 REVISE の 2 点目(下記)でさらに 1 本足した
   (29 → **30**)。両方を足した最終の本数で走らせ直すと
   **pytest 収集 3404 → 3409・discover 3308 → 3313**(試験 file 本数 178 は不変。
   `measure/tests/test_inject.py` の漏れ 1 本も不変)。`fixtures/suite_coverage_2026-10-16.json`
   を更新し、連動する `fixtures/packaging_2026-10-20.json`(`G-5.pytest_tests_after`・
   `G-6.numbers_cited.pytest_tests`)と `README.en.md`(「3404 collected test
   cases」)も 3409 に直した。**この結果文書 §1 の G-4(3363 → 3363)は
   測った時点のまま変えていない**(G-4 は試験 file を足す前の実測で、
   3409 とは別の時点・別の対象)。
2. **README の旧 C の字**: 「a prior rule-based detector detected 4/8」は誤り。
   旧 C は LLM の席 + 旧検証層(`docs/DOMAIN1_ERRDET_CPRIME_RESULT_2026-10-19.md`
   §3「行 1 が 4 件(seat1): 旧 C はこの 4 件を『確認済み』で上書きしていた」)で、
   rule-based ではない。「a prior design (the LLM's answers passed through an
   earlier verification layer that overwrote 4 of the LLM's correct findings)
   detected 4/8」に直した。`ReadmeDomainPairTest` に 1 本追加
   (`test_g6_4_of_8_bullet_names_the_overwrite_not_rule_based`。直す前の字
   (scratchpad に保存)を in-memory で通すと赤)。この追加分も上記 1 の
   最終の本数(25 → 30・3409・3313)に含めて数えてある。
