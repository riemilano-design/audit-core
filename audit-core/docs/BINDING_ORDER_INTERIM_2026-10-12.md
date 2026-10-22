# 束縛の順序の封 ― 実装は**止まっている**。1 回目の実測(2026-10-12)

封 `1500958` の規則を Adapter に実装した patch(`recipes.py` **1 ファイル・+73 / −72**)を、
**使い捨ての worktree で司令塔が自分で当てて測った。patch はコミットしていない。**
**止めた理由は Golden 期待値が落ちること**(封 §4・人間の禁止「Golden 期待値の変更」)。**期待値は 1 行も触っていない。**

| | |
|---|---|
| patch | `scratchpad/binding_order.patch`(8,588 B)。`git apply --check` rc=0 |
| 変更 | `audit-core/adapters/xbrl/recipes.py` のみ。**`core`・`extract.py`・`vocabulary.py`・`core_expectation_*.json`・`tests/golden` は 0 行** |
| 材料 | `ai_prose_instance_2026-10-09.zip`(`03521437be23c8e2…` 一致)・P7 |
| 理由名 | 既存の `no_element`・`ambiguous(elements)` のみ。**新規登録 0** |

## 1. 封の対象 60 件 ― **司令塔が自分で回した値**(実装席の報告と一致)

| | 変更前 | 変更後 |
|---|---|---|
| GROUNDED | 60 | **38** |
| UNVERIFIABLE(`ambiguous(elements)`) | 0 | **12** |
| VALUE_MISMATCH | 0 | **10** |
| **停止の合計** | 0 | **22**(封の予測は **14**) |

停止した 22 件: `N009`・`N014`・`N021`・`N026`・`N063`・`N066`・`N089`・`N105`・`N130`・`N138`・`N172`・`N175`・`N179`・`N181`・`N191`・`N214`・**`N219`**・`N264`・`N267`・`N278`・`N282`・**`N289`**

## 2. 対象 2 件 ― **予測どおり停止した**

| id | 変更後 | pointer |
|---|---|---|
| **`N219`** | **`VALUE_MISMATCH`** | `LongTermLoansPayable@CurrentYearInstant`(誤っていた `@Prior1YearInstant` が候補から外れた) |
| **`N289`** | **`VALUE_MISMATCH`** | `PurchaseOfIntangibleAssetsInvCF@CurrentYearDuration` の**単一 fact**(対の形へ落ちていない) |

**`N289` の封の予測との差**: 封 §2-B は「候補 0 件・**値の比較は行われない**」と予測した。
実測は**候補 1 件に絞られ、値の比較が行われて `VALUE_MISMATCH`** になった。
**仕組みの予測は外れ、向き(停止する)は当たり。** 実装席は `sys.settrace` で
「対の形の分岐に一切入らない」ことを確かめたと報告しており、**人間の指示「別経路へ落ちる挙動そのものが止まったか」は満たされている**
(ただし**独立席の確認はまだ**)。

`T023`・`T038`・`T086` は **3 件とも GROUNDED のまま**(封の予測どおり。今回の対象外)。`T087` は **`POINTER_NOT_FOUND` で停止維持**。

## 3. **止めた理由** ― 規則 4 を字どおり当てると Golden が 51 件落ちる

試験: `unittest` 490 → **480 通過 / 10 落ち**、`pytest` 586 → **576 通過 / 10 落ち**。落ちた 10 本は全部 Golden 期待値との不一致
(`test_claim_layer.test_p1_against_1B`・`test_p5f_against_5F`、`test_mutations.test_all_mutations_match_their_prediction`、
`test_instrument3` の 3 本、`test_instrument3b` の 4 本)。
実装席の測定では **1B 側 32 id・5F 側 19 id = 51 id**(P1/P5F/P6/P7 で同じ)が GROUNDED → UNVERIFIABLE / VALUE_MISMATCH に変わる。

### 原因(**司令塔が自分で測って確かめた**)

**同じ (context, 値, 単位) を、2 つ以上の異なる要素名が持っている組が 80 組ある。**

```
ctx=CurrentYearDuration  値=38,064,274,000  要素=['jpcrp_cor:NetSalesSummaryOfBusinessResults', 'jppfs_cor:NetSales']
ctx=CurrentYearDuration  値= 1,457,848,000  要素=['jpcrp_cor:OrdinaryIncomeLossSummaryOfBusinessResults', 'jppfs_cor:OrdinaryIncome']
ctx=Prior1YearDuration   値= 1,922,581,000  要素=['jpcrp_cor:ProfitLoss…SummaryOfBusinessResults', 'jppfs_cor:ProfitLoss', 'jppfs_cor:ProfitLossAttributableToOwnersOfParent']
```

`instance.py:154` は `local == e` と `local == e + "SummaryOfBusinessResults"` を**同じ主張の証拠として意図的に両方拾う**。
したがって**規則 4「候補が複数なら停止」を字どおり当てると、この形に広く発火する。**

**ここで分かったこと(記録しておく)**: **旧コードは `hits[0]`(`recipes.py:218`)で黙って 1 つ選んでいた** ―
**規則 4 の違反そのものが、開発書類でも日常的に起きていた。** 誰も数えていなかった。

## 4. **診断できていないこと**(実装席の説明と司令塔の測定が食い違う)

実装席は「`N137`・`N143`・`N192` が停止しなかったのは `is_diff` が **True** だから(封 §2-A-2 の記載と矛盾する)」と報告した。
**司令塔が `recipes.py` の正規表現を import して測り直すと、3 件とも `is_diff` は `False`** である
(`N137` の数の直後 4 字は `百万円の`、手前 25 字は `預金:2,605百万円(前期末2,899百万円)、` でどちらも当たらない)。
**したがって 3 件が停止しなかった理由は未解明。** 封 §2-A-2 の記載(`is_diff=False` 8 件)は司令塔の測定と一致しており、**封は書き換えない。**
**この patch を採るかを決める前に、3 件の経路を診断する必要がある。**

## 5. 封の予測との差(**予測は書き換えない**)

| 封の予測 | 実測 | 判定 |
|---|---|---|
| 停止 **14** 件 | **22** 件 | **外れ** |
| GROUNDED **46** | **38** | **外れ** |
| 規則 4 で停止 **0** 件 | **12 件**(`ambiguous(elements)`) | **外れ**(`N021`・`N138`・`N264` の 3 件は `D-009` で事前に MISS と記録済み。**残り 9 件は封が想定していなかった**) |
| 規則 3 の巻き込み 7 件 | **`N137`・`N143`・`N192` が停止せず**(理由未解明) | **外れ** |
| `N219` 停止 | 停止 | 当たり |
| `N289` 停止・**値の比較は行われない** | 停止・**値の比較が行われた** | 向きは当たり / 仕組みは外れ |
| `T023`・`T038`・`T086` は GROUNDED のまま | GROUNDED のまま | 当たり |
| 53 件のうち停止 **12** 件 | **20 件**(実装席の測定。司令塔は未検算) | **外れ** |
| 台帳 L-001 **32.4%** | **算出していない**(60 件の状態が予測と大きく違い、意味のある比較にならない) | **未測定** |

## 6. 未測定・未着手

- 独立席による 53 件の停止の妥当性確認(条件 c)。
- **`D-009` が指す「固定した偽 Claim 注入試験」の特定**(実装席が名指しで特定できなかった。既存の `test_tamper_*`・`test_boundary` 52 本は通過)。
- 未使用 2 書類(`S100Z39P`・`S100Z4N9`)― **開いていない**(条件 f。規則のコミット後に行う)。
- 営業資料との照合(封 §8)。
- `N137`・`N143`・`N192` の経路の診断(§4)。
