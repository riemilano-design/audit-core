# (d)・P・U を製品の経路へ + 軸の保持 (e) の実測 ― **192 / 192 を再現し、既存の経路は `engine` の欄以外 byte 同一。予測 当たり 8 / 外れ 4**

2026-10-19。封 `docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md`(commit `ae528a4`。実装より先)。
**engine を変えた**(`adapters/xbrl/holds.py`・`verify_external.py` 新規、`instance.py` に `axes` を追加。`core/py/` は 0 行)。
独立監査(`step-auditor`)**GO**(REVISE 0 回)の後に commit。0 USD・席は呼んでいない。
正本は `fixtures/xbrl/cd8/holds_product_path_2026-10-19.json`
(`python3 measure/xbrl_holds_product_path_2026-10-19.py --baseline … --run-tests-log … --audit-verdict GO --audit-revise 0 --write` で再現)。

---

## §1 判定 ― **写しは測定と同じ結果を出し、既存の経路は動かない**

| 欄 | 対象 | **実測** |
|---|---|---|
| F-1 `core/py/` | 封の commit との diff | **0 行** |
| F-3 軸の 1:1 | 8 書類・1203 枠(members あり 1128)| **違反 0** |
| F-4 192 行の再現 | 記録 `period_unit_hold_2026-10-19.json` の「合成の後」| **192 / 192** 一致・(d) の理由 6 / 6 |
| F-5 (d) の 6 行の `hold_axes` | 軸の分類 | 連結・個別 2・セグメント 2・株主資本の内訳 2 |
| F-6 対照 | 注入 1 件ずつ(GROUNDED の 24 行)| 期間(注入)**18 / 18**・単位 **24 / 24**・次元 **24 / 24** |
| F-7 既存の経路 | `verify_document --doc S100YXMA`(基準 sha256 `2c2af15a…`)| 動いた欄は **`engine` だけ**(中は `adapter_xbrl_py_files`・`adapter_xbrl_py_sha256`・`git_commit`)。claims 119: G 60 / PNF 17 / UNV 18 / VM 24 で同じ |
| F-8 新しい CLI | 2 回走らせた sha256 | 同じ(`f1a40428…`) |
| F-9 変異 | HOLD-R1・R2・R3 | **3 本とも red**。既存 89 本の行は封の commit と字が同じ |

**入口の状態の分布(192 行)**: GROUNDED 18 / VALUE_MISMATCH 44 / UNPROVABLE 23 / 参照先なし 107 ― 10-19 の測定(`measure/`)と同じ。

### §1-1 何が製品の経路に入ったか

- `adapters/xbrl/holds.py`: (d)・P・U の写し。`audit_core` を import しない(データの層)。`checks` 5 つ・`unchecked` 5 つを応答に毎回入れる。
- `adapters/xbrl/verify_external.py`: 外から渡された主張を照合する入口(library + CLI)。比較の算術は新しく書いていない。
- `adapters/xbrl/instance.py`: 各枠に `axes`(`[[軸, 枠の名], ...]`、`members` と 1:1)。既存の鍵は変えていない。
- 境界: `test_boundary.py` の `_ALLOWED_TO_IMPORT_CORE` に `verify_external.py` を 1 本足し、Core から使う名前 8 つを字で留めた。

---

## §2 代価 ― **測ったのは同値と不変だけ。精度は測っていない**

- 既存の engine 側の試験(変異を除く)は全部緑(記録 F-2 の `engine 側の試験(変異を除く)`)。
- `sh run_tests.sh` は **1 回目はログに `rc=` の行が無い**(pytest が 3 failed で止まった。赤 3 本は全部 10-17 の封の門で、
  「入口は measure/ に在る」「engine は動かない」を字で留めていた)。その 3 本に **2026-10-19 の遷移を宣言する追記**
  (封が履歴に在るときだけ後の形を受け入れる。10-17 の値は消さない)を足して **2 回目 rc=0**。§3 F-11 のとおり外れ。
- 保護面は 34 → 36 本(束ねた sha `2617c963…`。`fixtures/frozen_bundle_sha.py` に世代の行を 1 本追記、前の値は消していない)。

---

## §3 予測との照合(**封は書き換えない**)

| | 予測 | 実測 | |
|---|---|---|---|
| F-1 | `core/py/` の差分 0 行 | 0 行 | **当たり** |
| **F-2** | `instance.py` は**足すだけ**(消す行 0・変える行 0)・既存 786 本が全部緑 | numstat 足した 18・**消した 1**(消したコード行 0)・試験は全部緑 | **外れ** |
| F-3 | 8 書類で `axes` と `members` が 1:1 | 違反 0 / 1203 枠 | **当たり** |
| F-4 | 192 / 192 一致・(d) の 6 行は理由も一致 | 192 / 192・6 / 6 | **当たり** |
| F-5 | 連結・個別 2・セグメント 2・株主資本の内訳 2 | 2・2・2 | **当たり** |
| F-6 | 期間 18 / 18・単位 24 / 24・次元 24 / 24 | 18 / 18・24 / 24・24 / 24 | **当たり** |
| F-7 | `engine` の欄以外 byte 同一 | 動いた欄は `engine` だけ | **当たり** |
| F-8 | 2 回の sha256 が同じ | 同じ | **当たり** |
| F-9 | HOLD-R1〜R3 が 3 本とも red・既存 89 本は変わらない | 3 本 red・89 本同じ | **当たり** |
| **F-10** | 保護面 22 → 24 本 | **34 → 36 本** | **外れ** |
| **F-11** | `run_tests.sh` rc=0 | **1 回目はログに `rc=` の行が無い**(pytest 3 failed・赤 3 本)→ 追記の後 2 回目 rc=0 | **外れ** |
| **F-12** | 独立監査 REVISE 1 回 → GO | **REVISE 0 回 → GO** | **外れ** |

**当たり 8 / 外れ 4。**

- **F-2 外れ**: 「消す行 0」と書いたが、numstat は足した 18・消した 1。消えた 1 行は `load_instance` の
  **1 行 docstring の閉じ**(同じ文を複数行 docstring の 1 行目に残し、追記の注を足した)で、**消したコード行は 0**。
  字で「消す行 0」と封じた以上、docstring でも外れは外れ。**封は直さない。**
- **F-10 外れ**: 「22 → 24」と書いたが、実測は 34 → 36。字で留めた `FROZEN_COUNT = 22` は 2026-10-09 の数で、
  その後 `adapters/shogi`(7 本、10-06)と `adapters/kokkai`(9 本、10-14)が足されても定数を直した人がいなかった。
  封の分母を**定数から写して実測しなかった**のが原因(`memory: pinned-count-rots-without-an-owner`)。
  `FROZEN_COUNT` は 36 に直し、世代の行を 1 本足した。
- **F-11 外れ**: 「rc=0」と書いたが 1 回目のログには `rc=` の行が無い(pytest が 3 failed で止まった。
  `run_tests.sh` は `set -e` で、pytest が失敗すると `--- 3/3 ---` にも最後の `rc=` の echo にも進まない)。
  赤 3 本は `tests/measure/test_verify_external_v1.py` の
  test_25・test_26(10-17: 「境界の一覧は触らない」「入口は adapters/ に無い」)と `test_xbrl_cd_seal.py` の test_12
  (10-17: `instance.py` の sha)。**engine を変えないと封じた過去の門が、engine を変える封と衝突する**ことを
  封の分母に入れていなかった(封 §2 は engine 側の試験 786 本しか数えず、`tests/measure` の門を数えていない)。
  直しは 3 本への**日付つきの追記**(10-17 の値・字は消さず、10-19 の封が履歴に在るときだけ後の形を通す)。
  追記の後の 2 回目は rc=0。
- **F-12 外れ**: 「REVISE 1 回」と書いたが、監査は REVISE 0 回で GO(必要な修正なし)。監査の観察事項 1 件
  ― 封 §1 の「これ以外に触らない」一覧に、`test_mutations.py`(scope の登録)・coverage の記録 2 本が
  載っていなかった ― は次の封で一覧に入れる。

**外れ 4 のうち 3(F-2・F-10・F-11)は同じ向き**: 封の分母・条件を**実測せずに字から写した**(docstring の行・保護面の本数・
過去の門)。次の封では、分母の欄は全部その場で測った値にする。

---

## §4 言えないこと

1. **精度は上がらない。**危険な通過は前も後も 0。示せたのは「写しが同じ答えを出す」「既存の経路が動かない」だけ。
2. **`hold_axes` は「どの軸が違うか」を記録するだけ**で、「どの軸の違いなら不一致か」は決めない。その規則は別の封。
3. **同じ 8 書類である。**新しい書類での挙動は測っていない。
4. 要素の取り違え(T5)・率の主張の 2 本目の参照先・方向の主張は触っていない。
5. F-12 は機械の測定ではなく、監査の席の報告を司令塔が写した値である。

## §5 次

- 包装(pip/CLI/JSON/英語 README)の封 `docs/PACKAGING_SEAL_2026-10-19.md`(別便)。
- `main` へのマージは人間の決定。
