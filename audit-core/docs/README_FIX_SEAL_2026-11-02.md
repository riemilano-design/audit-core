# 封: `README.en.md` の入口の字を 2 か所直す(2026-11-02 の実測に合わせる。engine は触らない)― 2026-11-02

2026-11-02。人間の指示(2026-11-02)「まかせるから進めて」= 司令塔が示した次の戦略の 1(README の入口の直し)。
出どころは同日の実測 `docs/README_CACHELESS_RESULT_2026-11-02.md`(記録 `fixtures/readme_cacheless_2026-11-02.json`。当たり 3 / 外れ 4):
「Check your own filing's text」の節はラベル無しでは最初のコマンドで落ち(R-3)、「Install」の節は Ubuntu の setuptools では非 editable が落ちて editable が通った(R-5。2026-10-20 の結果と向きが逆)。
**engine(`core/`・`adapters/`)・包装の file(`setup.cfg`・`pyproject.toml`・`setup.py`)・儀式の節(「10-minute reproduction」。儀式の門が全文を縛る)・数(G-6 の門が記録に縛る)は 1 字も変えない。**
新しい測定はしない(数は 11-02 の記録から引く)。0 USD。通信しない。

---

## §0 何を直すか(字を先に固定する。直した後の字はこれと同じでなければならない)

### 0-1 「Check your own filing's text and get a Japanese report (0 USD, no network)」の節

見出しは変えない。段落の末尾の 1 文

> Without the standard-taxonomy labels (step 0 above) the source column shows element names.

を、次の 3 文に置き換える:

> Step 0 above (the standard-taxonomy labels) is a prerequisite for this section as well: without them the first command stops with `FileNotFoundError` before writing anything (measured 2026-11-02 on a clone without the labels; `docs/README_CACHELESS_RESULT_2026-11-02.md`). In the report step, an element that has no standard label is printed by its element name. Whether the report step still runs when the label directory itself is missing was not measured in that run.

根拠: R-3(`verify_document` が `FileNotFoundError` で rc=1、`out.json` は書かれない)。「要素名で出る」は 10-21 の結果(`docs/XBRL_CUSTOMER_REPORT_RESULT_2026-10-21.md` §: 標準ラベルの無い要素は要素名のまま出る)。ラベル dir が無いときの報告は R-4 で未測。

### 0-2 「Install」の節

段落

> Editable install (`pip install -e .`) on an older toolchain without PEP 660 support (setuptools < 61, as measured on this machine: 58.0.4) installs successfully but the combined import `import audit_core, adapters.xbrl.verify_external` from outside the project directory fails with `ModuleNotFoundError`; the console scripts and a normal (non-editable) install both work. See the Japanese result document for the measured detail.

の「both work.」を「both worked on that machine.」に直し、その段落の直後に 1 段落を足す:

> The reverse was measured on 2026-11-02 on Ubuntu 24.04 with the distribution's `python3-setuptools` 68.1.2 and Python 3.13.18: the normal `pip install .` failed while building the wheel (`AttributeError: install_layout`), and the editable install plus the combined import both worked. Whether this comes from this repository's packaging files or from that toolchain has not been isolated (`docs/README_CACHELESS_RESULT_2026-11-02.md`).

根拠: R-5(非 editable install rc=1・例外の行 `AttributeError: install_layout`、editable install rc=0・combined import rc=0)。環境の欄(OS・setuptools・python)。

### 0-3 触る file

| file | 何を |
|---|---|
| `README.en.md` | 0-1・0-2 の字。ほかに試験 file の本数の行(覆いの門が要求する数)だけ |
| `tests/measure/test_readme_fix.py`(新規) | 0-1・0-2 の字が在ること・その中の事実(例外の名・版・rc)が 11-02 の記録と合うこと・儀式の節が封の commit から変わっていないこと・差分が 2 節 + 本数の行に限ること・禁止語 0・変異 |
| `tests/measure/test_readme_cacheless.py` | `test_e_1`(封 `443a078` と木の README の差を「test files」の行に限る)を、**封 `443a078` と結果 `a6a1ea0` の commit 同士の差**に変える(その便で README を変えなかったことは git の 2 点で永く言える。木と比べる形だと本便の直しで赤くなる)。それ以外は変えない |
| `fixtures/suite_coverage_2026-10-16.json`・`docs/SUITE_COVERAGE_2026-10-16.md`・台帳 A-06〜A-09 | 門 +1 の覆い |
| `docs/FACTS_FOR_BUYERS_2026-10-20.md` | L-45(README の入口の直し。印は 11-02 の記録)。`tests/measure/test_facts_for_buyers.py` の EXPECT_ROWS・EXPECT_CLAIMS |

**触らない**: `core/`・`adapters/`・`setup.cfg`・`pyproject.toml`・`setup.py`・`README.md`(日本語の正本。英語の抜粋だけ直す。日本語側に同じ節は無い)・README の数・儀式の節。

## §1 事前予測(**実装より先に固定**)

| | 予測 | **外れ方** |
|---|---|---|
| **F-1** | 直した後も `tests/measure/test_packaging.py` の常に走る門(G-4・G-6・`ReadmeDomainPairTest`)は**全部緑**。禁止語(`accurate`・`world's first`・`only`・`unique`・`guarantee`)は **0**。英語だけ | 1 本でも赤 / 禁止語が入る(特に `only`) |
| **F-2** | 封の commit の README と直した README の差分(行単位)は、**0-1 の 1 文(−1 行)・0-2 の 2 段落(±2〜4 行)・試験 file の本数の 1 行**だけ。儀式の節(`## 10-minute reproduction` から次の `## ` の前まで)は**同じ**。数の bullet は 1 つも変わらない | 他の行が変わる / 儀式の節が変わる |
| **F-3** | 新しい門が、0-1 の `FileNotFoundError`・0-2 の `AttributeError: install_layout`・`24.04`・`68.1.2`・`3.13.18`・「editable … both worked」を 11-02 の記録の欄(例外の行・環境・rc)と照らして**全部一致** | 1 つでも記録に無い字 |
| **F-4** | `README.en.md` の行数は **+2 以上 +4 以下**(段落 1 つと 1 文の置き換え) | 幅の外 |
| **F-5** | 台帳: L-45 で印 **3 本**(非 editable install rc 1・editable install rc 0・verify_document の rc 1)、`facts_check --check` は **OK 650 / NG 0**。覆いは試験 file **248**・`tests/measure` **182** | 数が違う / NG が出る |

## §2 言えないこと

- 直すのは字で、挙動は変わらない。「ラベル dir が無いときの報告」「他の toolchain での `pip install .`」は未測のまま(README もそう書く)。
- 英語 README は抜粋。正本は日本語の文書と記録のまま。
- 日本語の `README.md` に同じ節が在れば直す対象だが、今回は英語側だけを封の対象にする(日本語側は触らない)。

## §3 作法

- 封を先に commit → README・門・覆い・台帳を直す → 独立監査 GO → path 指定で commit。
- 結果の文書は作らない(字の直しで数は増えない。当たり / 外れは本封の末尾に**日付つきの追記**として足し、予測欄は変えない)。

## §4 追記(2026-11-02、実装の後): 当たり 4 / 外れ 1(F-4)

予測欄(§1)は変えていない。直した後の字は §0-1・§0-2 のとおり(門 `tests/measure/test_readme_fix.py` が封の引用を読んで README と照らす)。

| | 実測 | 判定 |
|---|---|---|
| **F-1** | `test_packaging.py` の常に走る門は全部緑。禁止語 0。英語だけ | 当たり |
| **F-2** | 差分は「Check your own filing's text」「Install」「Test suite」(本数の行)の 3 節の中だけ。儀式の節は同じ。数の bullet は変わらない | 当たり |
| **F-3** | `FileNotFoundError`・`AttributeError: install_layout`・Ubuntu 24.04・68.1.2・3.13.18・editable の rc 0 は全部 11-02 の記録の欄と一致(門 `test_a_2`) | 当たり |
| **F-4** | 行数は **+6**(足した段落が折り返しで 5 行 + 空行 1。幅 +2〜+4 の外)。見立てが折り返しを数え落とした。門は実測の +6 を縛る(見立てに合わせて折り返しは変えない) | **外れ** |
| **F-5** | L-45 の印 3 本、`facts_check --check` OK 650 / NG 0。覆い 248・`tests/measure` 182 | 当たり |

`tests/measure/test_readme_cacheless.py` の `test_e_1` は、封 `443a078` と結果 `a6a1ea0` の commit 同士の README の差を見る形に変えた(§0-3 のとおり。他は変えていない)。
