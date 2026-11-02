# 封: cache の無い clone で `README.en.md` の手順が字どおりに動くか(買い手の最初の 10 分)― 2026-11-02

2026-11-02。人間の指示(2026-11-02)「B」= 司令塔が 2026-11-01 に示した選択肢 B(デスクトップに戻るまでにできること:
cache の無い clone で README の 10 分再現が成り立つかの点検)。
**engine(`core/`・`adapters/`)は 1 行も変えない。README の字も、この便では変えない**(外れが出たら結果の文書に書き、
直すかどうかは別の便で人間が決める)。**0 USD。通信しない**(pip には `--no-index`、EDINET には触れない。
ラベルの取得(README の Step 0)は**この便では測らない**)。

この機械(封の時点で実測した道具だけ): Python 3.13.18・pip 24.0・setuptools 68.1.2・`venv`(ensurepip 26.2.2)。
`~/.cache/audit-core/` は**無い**。環境変数 `EDINET_TAXONOMY_DIR` は未設定。HEAD `23030cc`。
買い手が `git clone` した直後の機械にいちばん近い条件なので、この機会に測る(デスクトップには cache が在って測れない)。

---

## §0 何を測るか

`README.en.md` の 3 節(「10-minute reproduction」「Check your own filing's text」「Install」)に書いてある
コマンドを、**README の字のまま**(置き場・option を変えない)この clone で走らせ、rc・書き出された file・案内の字を記録する。
数の正本は `fixtures/readme_cacheless_2026-11-02.json`。script は `measure/readme_cacheless_2026-11-02.py`
(標準ライブラリだけ。engine を import しない。子 process で CLI を呼ぶだけ)。結果は `docs/README_CACHELESS_RESULT_2026-11-02.md`、
門は `tests/measure/test_readme_cacheless.py`。

| # | 走らせる物(README の字) | 記録する物 |
|---|---|---|
| 1 | `python3 measure/ritual_2026-10-20.py --out <空の dir>`(ラベル無し) | rc・stdout+stderr の字・`<空の dir>` に書かれた file の数 |
| 2 | (走らせない。字の照合)README Step 0 の「two … label files … about 8 MB」と、`fixtures/xbrl/TAXONOMY_LABELS_README.md`・`fixtures/xbrl/taxonomy_labels_sha256.txt`・`adapters/xbrl/instance.py` の `TAXONOMY_LABEL_FILES`(読むだけ) | 儀式が要求する file の数・名簿の file の数・sha256 の一致・バイト数の合計 |
| 3 | `python3 -m adapters.xbrl.verify_document --zip fixtures/xbrl/ai_prose_instance_2026-10-09.zip --text <1 文の file> --out out.json`。1 文は封で固定: 「当連結会計年度の売上高は 1,234 百万円となりました。」。別に `--text` 無し(ZIP 自身の本文)でも 1 回 | rc・`out.json` の有無・`document.claims`・`document.states` |
| 4 | `python3 -m adapters.xbrl.report_customer --in out.json --out report.md --labels ~/.cache/audit-core/edinet-taxonomy/2025-11-01 --zip <同じ ZIP> --full`(ラベルの dir は**存在しない**。入力は 3 の `--text` 無しの出力) | rc・`report.md`・`report.provenance.json` の有無・出所の欄に要素名(`<接頭辞>:<要素名>` の形)が出る行の数 |
| 5 | 新しい venv(`--system-site-packages`)で `pip install . --no-build-isolation --no-index` → repo の外の cwd から `python -c "import audit_core, adapters.xbrl.verify_external"` → `audit-core-verify-document --help`・`audit-core-verify-external --help`。別の venv で `pip install -e . --no-build-isolation --no-index` → 同じ combined import | それぞれの rc |
| 6 | 1・3・4・5 の壁時計の合計(2 は読むだけなので除く) | 秒 |
| 7 | (読むだけ)README の字 4 か所: 「exit code 2」「Python >= 3.9」「zero runtime dependencies」「Two console scripts」を、1・5 の実測と `setup.cfg`(`python_requires`・`install_requires`・`console_scripts`)に照らす | 一致した数 |

## §1 事前予測(**実装・実測より先に固定。結果を見てから書き換えない**)

| | 予測 | **外れ方** |
|---|---|---|
| **R-1** | ラベル無しの儀式は **rc=2**。案内の字に `TAXONOMY_LABELS_README.md` と `EDINET_TAXONOMY_DIR` の両方が在る。`--out` の dir に書かれた file は **0** | rc が 2 でない / どちらかの字が無い / file が 1 つでも書かれる(止まる前に書く) |
| **R-2** | 儀式が要求するラベルは **2 本**(jppfs・jpcrp)で、README の「two」と合う。名簿 `taxonomy_labels_sha256.txt` は **3 本**(jpigp を含む。報告だけが使う)。2 本の sha256 は 3 か所(`TAXONOMY_LABELS_README.md`・名簿・`instance.py`)で**全部同じ**。2 本のバイト数の合計は **8,000,000 以上 9,000,000 未満**(「about 8 MB」) | 本数が違う / sha256 が 1 つでも食い違う / 合計が幅の外 |
| **R-3** | 1 文の `--text` で **rc=0**、`out.json` が書かれ、`document.claims` は **1**。`--text` 無しでも **rc=0** で `document.claims` は **200 以上** | rc≠0 / claims が 1 でない / `--text` 無しが 200 未満 |
| **R-4** | 存在しないラベル dir を `--labels` に渡しても **rc=0**(README「Without the standard-taxonomy labels … the source column shows element names」)。`report.md`・`report.provenance.json` の両方が書かれる。出所の欄に要素名の形が出る行は **1 行以上** | rc≠0(dir が無くて落ちる) / file が欠ける / 要素名の行が 0 |
| **R-5** | 非 editable: install **rc=0**・combined import **rc=0**・`--help` 2 本とも **rc=0**。editable(setuptools 68.1.2 は PEP 660 を持つ): install **rc=0**・combined import **rc=0**(README の「on an older toolchain … fails」はこの機械には当たらない方向) | どれか 1 つでも rc≠0。特に editable の import が rc=1 なら README の但し書きは「古い toolchain」に限らない |
| **R-6** | 壁時計の合計は **600 秒以下**(venv 2 本と pip を含めて) | 600 秒を超える |
| **R-7** | README の字 4 か所は **4 つとも**実測・`setup.cfg` と一致 | 1 つでも食い違う |

予測の数え方: 当たり / 外れ は欄ごと。欄の中の 1 つでも外れ方に当たれば、その欄は外れ。

## §2 言えないこと(測らないこと)

- **Step 0(ラベルの取得)と Step 1 のラベル有りの実行は測らない**(通信しない)。README の「Passed 2 / 243」「22.8 seconds」が
  この機械で再現するかは、この便では言えない。
- README の「10-minute」は Step 0 を除いた字ではない。この便で測る R-6 は **Step 0 を除いた**時間で、README の字の検証ではない。
- 1 文の `--text` の判定(GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND のどれか)は記録するが、**正しさの判定には使わない**
  (封で作った文で、書類の事実との関係は見ていない)。
- 動くことは「正しい」の証拠ではない(包装の封 §2 と同じ)。
- venv の中の pip は ensurepip が同梱する版(26.2.2 系)で、`--system-site-packages` 経由で機械の setuptools 68.1.2 を使う。
  他の版の pip・setuptools で同じになるかは言えない。

## §3 作法

- 封(この file)を先に commit し、その後に script・記録・結果・門を足す(順序の門が git で見る)。
- `core/`・`adapters/`・`README.en.md`・`measure/ritual_2026-10-20.py`・既存の試験は触らない。
- 記録・結果・門に docID を書かない(`fixtures/xbrl/` の名簿の門が見る)。
- 書き出しは scratchpad(repo の外)に置き、木には記録 1 本だけを足す。
- 独立監査(step-auditor)の GO の後に commit する。
