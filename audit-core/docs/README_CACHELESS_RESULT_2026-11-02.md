# cache の無い clone で `README.en.md` の手順は字どおりに動いたか ― **予測 当たり 3 / 外れ 4(R-3・R-4・R-5・R-7)**

2026-11-02。封 `docs/README_CACHELESS_SEAL_2026-11-02.md`(commit `443a078`。実装・実測より先)。
記録 `fixtures/readme_cacheless_2026-11-02.json`(数の正本。script `measure/readme_cacheless_2026-11-02.py`、標準ライブラリだけ)。
**engine(`core/`・`adapters/`)・`README.en.md` の 3 節・儀式の script は 1 行も変えていない。通信していない。0 USD。**
この文書の数は門 `tests/measure/test_readme_cacheless.py` が記録に縛る(【門なし】の印が無い数は全部、門が記録と照らす)。

この機械: Ubuntu 24.04.5 LTS・Python 3.13.18・pip 24.0・setuptools 68.1.2(Ubuntu の `python3-setuptools`。`/usr/lib/python3/dist-packages`)・
`~/.cache/audit-core/` 無し・`EDINET_TAXONOMY_DIR` 未設定。**買い手が `git clone` した直後の機械にいちばん近い条件**で測った。

---

## 1. 欄ごとの当たり / 外れ(封 §1 の字をそのまま。結果を見てから書き換えていない)

| | 予測(封 §1) | 実測(記録) | 判定 |
|---|---|---|---|
| **R-1** | ラベル無しの儀式は rc=2。案内に `TAXONOMY_LABELS_README.md` と `EDINET_TAXONOMY_DIR` の両方。`--out` の dir に書かれた file は 0 | rc=2。案内に両方の字が在る。書かれた file 0 | **当たり** |
| **R-2** | 儀式が要求するラベルは 2 本で README の「two」と合う。名簿は 3 本。2 本の sha256 は 3 か所で同じ。合計は 8,000,000 以上 9,000,000 未満 | 要求 2 本・README の語「two」・名簿 3 本・sha256 が 3 か所で同じ本数 2・合計 8,362,742 バイト | **当たり** |
| **R-3** | 1 文の `--text` で rc=0・`document.claims` 1。`--text` 無しでも rc=0・claims 200 以上 | `--text` あり rc=1、`--text` 無し rc=1。どちらも `out.json` は書かれず、`FileNotFoundError: no taxonomy label file at …/jppfs_2025-11-01_lab.xml` で落ちた | **外れ** |
| **R-4** | 存在しないラベル dir を `--labels` に渡しても rc=0。`report.md`・`report.provenance.json` が書かれ、要素名の行 1 以上 | rc=1。入力(R-3 の `out.json`)が無いので `FileNotFoundError` で落ちた。**ラベル dir が無いときの挙動そのものは測れていない**(入口の R-3 で止まった) | **外れ** |
| **R-5** | 非 editable: install rc=0・combined import rc=0・`--help` 2 本 rc=0。editable: install rc=0・combined import rc=0 | 非 editable: install **rc=1**(wheel の build が `AttributeError: install_layout` で落ちる)・import rc=1・`--help` 2 本とも rc=127(console script が無い)。editable: install rc=0・import **rc=0** | **外れ** |
| **R-6** | 壁時計の合計 600 秒以下 | 9.6 秒(落ちた物は速く落ちる。venv 2 本と pip を含む) | **当たり** |
| **R-7** | README の字 4 か所が 4 つとも実測・`setup.cfg` と一致 | 一致 3(「exit code 2」「Python >= 3.9」「zero runtime dependencies」)。「Two console scripts」は `setup.cfg` には 2 本在るが、非 editable の venv では 1 本も入らなかった(R-5 の帰結) | **外れ** |

外れの向き: 4 本とも「README が書いた手順が、この機械ではそのまま通らない」側。見立ては「ラベルが無くても verify と report は動き、pip は入る」側に寄っていた。

## 2. 外れの中身 ― 読み手(買い手)に効く順

### 2-1 R-3: 「Check your own filing's text」の節は、ラベル無しでは入口で落ちる

README の節の見出しは「(0 USD, no network)」で、本文は「Without the standard-taxonomy labels (step 0 above) the source column shows element names」と書く。
実測では **`verify_document` 自身が標準タクソノミのラベル(jppfs)を要求し、無いと `FileNotFoundError` で落ちた**(`--text` あり・無しの両方)。
落ちた場所は `adapters/xbrl/recipes.py` の `_label_tables` → `adapters/xbrl/instance.py` の `taxonomy_labels`(既定 profile の `taxonomy_labels` が真)。
つまり README の「ラベル無しでも要素名で出る」は報告(`report_customer`)の話で、**その前段の verify はラベル無しでは走らない。Step 0 はこの節にも前提。**
README の字は正しい部分(報告は要素名で出る)と足りない部分(verify にもラベルが要る)が混ざっている。**この便では README を直していない**(別の便で人間が決める)。

### 2-2 R-5: 「Install」の節の `pip install .` は、この機械では wheel の build で落ちる

`pip install . --no-build-isolation`(通信しないため `--no-index` を足した)は、setuptools の `bdist_wheel` → `install` → `install_lib.finalize_options` で
`AttributeError: install_layout. Did you mean: 'install_platlib'?` を出して落ちた。`install_layout` は Ubuntu/Debian が `python3-setuptools` に当てている patch の option(一般知識。記録に在るのは置き場 `/usr/lib/python3/dist-packages` と例外の行)で、
この機械の setuptools(68.1.2)と Python 3.13 の組み合わせで起きた。【門なし】**repo の `setup.cfg`・`pyproject.toml` の字の問題かどうかは、この便では断定しない**
(別の toolchain では測っていない。2026-10-20 の包装の便は Python 3.9.6・setuptools 58.0.4 で rc=0 だった)。【門なし】
一方 **editable(`pip install -e .`)は install rc=0・combined import rc=0**で、2026-10-20 の結果(editable で import rc=1)と**向きが逆**。
README の「Editable install … on an older toolchain without PEP 660 support … fails」はこの機械(PEP 660 あり)では当たらず、代わりに非 editable が落ちた。【門なし】
console script 2 本は editable の venv では `--help` が rc=0 で動いた(追加の実測。判定には使わない)。

### 2-3 R-4・R-7 は R-3・R-5 の帰結

R-4 は入力が無いので測れず(「ラベル dir が無いときに要素名で出るか」は未測のまま)、R-7 の「Two console scripts」は非 editable の venv に console script が入らなかったことの写し。
外れの独立な原因は 2 つ(R-3 と R-5)。

## 3. 当たった 3 本

- **R-1**: 儀式の入口(`measure/ritual_2026-10-20.py`)はラベル無しで **rc=2** で止まり、案内に取り方・置き場・`TAXONOMY_LABELS_README.md`・`EDINET_TAXONOMY_DIR` を出し、`--out` には何も書かない。README の「Without them the entry point prints instructions and stops (exit code 2)」は字どおり。
- **R-2**: 儀式が要求するラベルは jppfs・jpcrp の 2 本で README の「two」と合う。名簿(`taxonomy_labels_sha256.txt`)は jpigp を含む 3 本。2 本の sha256 は `TAXONOMY_LABELS_README.md`・名簿・`instance.py` の 3 か所で同じ。2 本の合計 8,362,742 バイトは「about 8 MB」の幅の中。
- **R-6**: 全部で 9.6 秒。ただし落ちた経路が速く終わっただけで、README の「10-minute」の検証ではない(封 §2)。

## 4. 言えること / 言えないこと

言えること(記録で裏づく):
- cache の無い clone で、README の 3 節のうち**字どおりに通ったのは「10-minute reproduction」の Step 0 の案内まで**(rc=2 と案内)。
- 「Check your own filing's text」は、ラベル無しでは最初のコマンドで落ちる。
- 「Install」は、この機械では非 editable が落ち、editable が通る。README の但し書きと向きが逆。
- README の字 4 か所のうち 3 か所(「exit code 2」「Python >= 3.9」「zero runtime dependencies」)は実測・`setup.cfg` と合う。

言えないこと(測っていない):
- Step 0(ラベルの取得)と、ラベル有りの儀式・verify・report。README の「Passed 2 / 243」「22.8 seconds」の再現。【門なし】
- ラベル dir が無いときに `report_customer` が要素名で出るか(R-4 の設計は入口で止まった)。
- 非 editable の失敗が他の toolchain(Ubuntu 以外・setuptools の他の版・Python 3.9〜3.12)でも起きるか。【門なし】
- README を直すべきか、どう直すか(人間が決める。この便は字を変えていない)。

## 5. 限界

- 1 文の `--text` は封で固定した文で、書類の事実との関係は見ていない。判定の中身は得られなかった(落ちたため)。
- venv の pip は ensurepip 同梱の 26.2.2 で、`--system-site-packages` 経由で機械の setuptools 68.1.2 を使った。pip 24.0(機械の pip)で直接入れる経路は測っていない。
- 壁時計は 1 機械・1 回。

## 6. 追記 1(2026-11-02、commit 前): script の欠陥 1 つと記録の走らせ直し 2 回

最初の走らせ(記録は scratchpad に保存、木には無い)で、R-7 の「zero runtime dependencies」が不一致になった。原因は **script の `setup.cfg` の読み取りの欠陥**
(正規表現の `\s*` が改行を跨ぎ、空の `install_requires =` の次の行 `package_dir =` と、その下の字下げの行を `install_requires` の値として読んだ)。
`[ \t]*` に直し、記録を消して走らせ直した。2 回目の記録には `--work` の絶対パス(scratchpad)が R-4 の例外の字に残っていたので、`<work>` に置き換える 1 関数を足して 3 回目を走らせた。
3 回の判定(R-1〜R-7 の当たり / 外れ)は**全部同じ**。変わったのは R-7 の一致した数(1 回目 2 → 2・3 回目 3)と、2 回目 → 3 回目の例外の字のパスだけ。
3 回とも封の条件(コマンド・置き場・option)は変えていない。

## 6-2. 追記 2(2026-11-02、commit 前): README の 1 行だけ変えた

封 §0 は「README の字も、この便では変えない」と書いた。3 節(10 分再現・自分の書類の点検・Install)の字は 1 字も変えていないが、門を 1 本足したので覆いの門(`tests/measure/test_packaging.py` の G-6)が要求する「Test suite」の節の試験 file の本数を 246 → 247 に直した(1 行)。結果に基づく直しではなく、覆いの記録に縛られた数の更新である。門 `test_e_1` が、封の commit と木の README の差を「test files」を含む行だけに限る。【門なし】

## 7. 次の封の候補(人間が決める)

- README「Check your own filing's text」に Step 0 を前提として書き足す(字の直しだけ。engine は触らない)。
- `setup.cfg`/`pyproject.toml` が Ubuntu の setuptools patch と Python 3.13 で `bdist_wheel` を通るか、原因を切り分ける(別 toolchain での実測を含む)。
- デスクトップ(cache あり)に戻ったら、Step 0 を済ませた状態で同じ script を走らせ、R-3・R-4 の本来の設計(ラベル dir 無しの報告)を測る。
