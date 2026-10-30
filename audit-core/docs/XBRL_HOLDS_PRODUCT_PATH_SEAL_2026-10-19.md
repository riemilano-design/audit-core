# 封: (d)・P・U を製品の経路へ、軸の保持 (e) を engine へ ― **engine 変更。実装より先に封じる**

2026-10-19。人間の指示(2026-10-19、原文): 「**営業的戦略はこちらでやるから、技術的に特化して** /
**なんんでもやっていいから** / **本当に制約はない**」。
これを受けて、司令塔が **engine 変更の構造の決定**(境界の一覧に入口を 1 本足す)を自分で行う。
**作法は変えない**: 封を先に commit し、engine の差分は独立監査(`step-auditor`)の GO を経てから commit する。
`main` へのマージは人間。**0 USD・席は呼ばない。**

元になった測定(すべて `measure/` で engine 不変のまま済み):
- (d) `docs/XBRL_DIM_HOLD_RESULT_2026-10-17.md`(曖昧 6 行を保留、正解 50 件の保留 0)
- P・U `docs/XBRL_PERIOD_UNIT_HOLD_RESULT_2026-10-19.md`(注入の穴 18/18・24/24 を通さない、正解の保留 0)

---

## §0 何を測るか

**規則は 1 つも新しく作らない。**`measure/` で封じて測った 3 つの規則を **adapters/xbrl に写し**、
外から渡された主張を照合する入口を**製品の経路**に置く。足す engine の情報は **軸(dimension)だけ**。

測るのは **(i) 写しが測定と同じ結果を出すか**(192 行・対照)、**(ii) 既存の経路が 1 byte も動かないか**、
**(iii) 軸が 1:1 で保持されるか**、の 3 つ。**精度は測らない**(上がらない。元の封のとおり)。

---

## §1 変更する file(**これ以外に触らない**)

| # | file | 変更 | engine か |
|---|---|---|---|
| 1 | `adapters/xbrl/instance.py` | `load_instance` の各枠に **`"axes": [[軸, 枠の名], ...]`** を足す(`.xbrl` の経路は `explicitMember` の `dimension` 属性、iXBRL の経路は正規表現)。**既存の鍵(`instant`/`start`/`end`/`members`)は 1 文字も変えない。他の関数は触らない** | **engine** |
| 2 | `adapters/xbrl/holds.py`(**新規**) | 3 つの規則の写し: `dim_of`・`dimension_siblings`・`period_siblings`・`claim_class`・`fact_class`・`unit_mismatch`・`apply_holds(out, f, facts, tol, claim_unit, contexts=None)`。**`audit_core` を import しない**(データの層)。(d) の発火には **`hold_axes`**(`f` と兄弟の枠で違う軸の一覧)を足す | **engine** |
| 3 | `adapters/xbrl/verify_external.py`(**新規**) | `measure/xbrl_verify_external_v1_2026-10-17.py` の写し + `apply_holds`。`verify_external(spec, facts, contexts=None)`・`verify_claims(claims, inst)`・CLI `python3 -m adapters.xbrl.verify_external --zip|--doc --claims in.json --out out.json` | **engine** |
| 4 | `tests/adapters/xbrl/test_boundary.py` | `_ALLOWED_TO_IMPORT_CORE` に **`verify_external.py` を 1 本足す**(字で固定)。`holds.py` は Core を import しないことを足す。新しい入口が Core から使う名前を字で留める(`ExternalEntryCoreUsageTest`) | 試験 |
| 5 | `tests/adapters/xbrl/test_holds.py`・`test_verify_external.py`(**新規**) | 規則の単体(測定の試験の写し)・**写しと `measure/` の規則の同値**(合成の格子)・**192 行の再現**(記録 `period_unit_hold_2026-10-19.json` の `**合成の後**` と 1 行ずつ一致)・対照(注入 18/18・24/24)・CLI の byte 安定 | 試験 |
| 6 | `tests/adapters/xbrl/mutations.json` | **H- の行を 3 本足す**(予測 red): H-R1 保留が `GROUNDED` 以外も動かす / H-R2 P が次元違いも拾う / H-R3 軸を記録しない | 試験 |
| 7 | `fixtures/frozen_bundle_sha.py` | 世代の行を **1 本追記**(22 本 → **24 本**。古い値は消さない) | 記録 |

**触らない**: `core/py/`(0 行)・`recipes.py`・`verify_document.py`・`resolve.py`・`comparators.py`・`registry_setup.py`・`vocabulary.py`・`extract.py`・`edinet.py`・`prose.py`・`report.py`。
`measure/` の規則と記録は**そのまま残す**(履歴。写しの同値を試験が見る)。

### §1-1 入口の応答(字で固定)

| 欄 | 中身 |
|---|---|
| `state` | `GROUNDED` / `VALUE_MISMATCH` / `POINTER_NOT_FOUND` / `UNPROVABLE` |
| `held` / `hold_rules` / `hold_axes` | 保留なら `True` / 発火した規則の組(`("d","P","U")` の部分列)/ (d) の軸 |
| `checks` | **`("存在", "値", "同額の次元兄弟", "同額の期間兄弟", "単位の種類")`** |
| `unchecked` | **`("重複", "単位の倍率", "期間(同額の兄弟が無いとき)", "次元(同額の兄弟が無いとき)", "要素の取り違え")`** |

**`unchecked` を空にしない。**保留規則は「同額の兄弟」と「単位の種類」しか見ない。

---

## §2 分母(**字で留める**)

| | 数 | 出どころ |
|---|---|---|
| 既存の engine 側の試験(`tests/adapters` + `tests/golden` + `tests/core`) | **786 本** | `pytest --collect-only` 2026-10-19(commit `9776adf`) |
| 変異 | **89 件** | `tests/adapters/xbrl/mutations.json` |
| 再現する行 | **192 行** | `fixtures/xbrl/cd8/period_unit_hold_2026-10-19.json` の `rows` |
| 対照 | 期間(注入)作れた **18**・単位 **24**・次元 **24** | 同記録 |
| (d) の 6 行の軸 | 連結・個別 **2**・セグメント **2**・株主資本の内訳 **2** | `fixtures/xbrl/cd8/dim_diag_2026-10-17.json` |
| 既存の経路の基準 | `verify_document --doc S100YXMA` の出力(claims 119: G 60 / PNF 17 / UNV 18 / VM 24) | 実装前に scratchpad へ保存(sha256 `2c2af15a…`) |
| 保護面の file | **22 本**(束ねた sha `490888d4…`) | `fixtures/frozen_bundle_sha.py` |

---

## §3 事前予測(**実装前に固定。外れは外れとして残す**)

| | 予測 | **外れ方** |
|---|---|---|
| **F-1** | `core/py/` の差分 **0 行** | 1 行でも |
| **F-2** | `instance.py` の差分は**足すだけ**(消す行 0・変える行 0)。既存 786 本は**全部緑**のまま | 消した行 / 赤 |
| **F-3** | 8 書類すべてで、`members` を持つ枠は **`len(axes) == len(members)`**(1:1)。`members` が空の枠は `axes` も空 | 1 枠でも違う(iXBRL の正規表現の取りこぼし) |
| **F-4** | 新しい入口を 192 行に当てると、`state` は記録の `**合成の後**` と **192 / 192 一致**。`reason` も (d) の 6 行で字で一致 | 1 行でも違う(写しの誤り) |
| **F-5** | (d) の 6 行の `hold_axes` の分類は **連結・個別 2・セグメント 2・株主資本の内訳 2** | 分類が違う |
| **F-6** | 新しい入口での対照: 期間(注入)**18 / 18** 保留・単位 **24 / 24** 保留・次元 **24 / 24** 保留 | 1 件でも通す |
| **F-7** | `verify_document --doc S100YXMA` の出力は、**`engine` の欄以外 byte 同一**(`claims`・`document`・`input` が同じ) | 他の欄が動く(instance の変更が既存経路に漏れた) |
| **F-8** | 新しい CLI の出力は **2 回走らせて sha256 が同じ** | 違う |
| **F-9** | 変異 H-R1・H-R2・H-R3 は **3 本とも red**。既存 89 本の判定は変わらない | 1 本でも沈黙 |
| **F-10** | 保護面は **22 → 24 本**。`frozen_bundle_sha.py` に世代の行を追記(前の値は消さない) | 本数が違う |
| **F-11** | `sh run_tests.sh` **rc=0**(覆いの検査・pytest・unittest discover) | 赤 |
| **F-12** | 独立監査は **REVISE 1 回 → GO**(0 回でも 2 回以上でも外れ) | 0 回 / 2 回以上 / HUMAN |

**本当に測っているのは F-3・F-4・F-5・F-7・F-9 である。**

---

## §4 言えないこと

1. **精度は上がらない。**元の封の判定(危険な通過 0 → 0)のまま。
2. **`hold_axes` は「どの軸が違うか」を**記録する**だけで、「どの軸の違いなら不一致か」は決めない。**
   その規則((e) の本体)は別の封。
3. **要素の取り違え(T5)・率の主張の 2 本目の参照先・方向の主張は触らない。**
4. **同じ 8 書類での再現である。**新しい書類での挙動は測っていない。
5. **境界の一覧に入口を足したのは司令塔の決定**(人間の 2026-10-19 の指示を根拠にした)。
   `docs/DECISION_LOG.md` は人間の裁定の原文だけを置く場所なので、**この決定はそこには書かない**。

## §5 やること(順)

1. `holds.py` と単体試験・同値試験 → 2. `instance.py` の `axes` と 1:1 の試験 → 3. `verify_external.py` と 192 行の再現・対照・CLI の試験 →
4. 境界の試験の更新 → 5. 変異 3 本 → 6. `verify_document` の byte 比較 → 7. `run_tests.sh` → 8. 独立監査 → 9. commit(GO の後)。
