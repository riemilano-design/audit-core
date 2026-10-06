# Core 接続 C-1f(原本の癖 2 つの直し、Adapter だけ)の予測 ― 実装の前に封じる

**日付**: 2026-10-06 **段**: C-1f(C-1e §5 の 1 番、人間の決定 2026-10-06「それで進めて」) **前提**: C-1d `25f33e9`、C-1e `726cae0` **封の手順**: この文書をコミットしてから書く。後から書き換えない。予測は司令塔の席。

## 1. 直す物(2 つ)と直さない物(1 つ)

| # | 癖 | 今 | 直し後 | なぜ直すか |
|---|---|---|---|---|
| a | `equals_within(pure*100)` と `ratio*100` が **|claim.value|** と比べる | `abs(x − abs(claim.value)) ≤ 0.15` | `abs(x − claim.value) ≤ 0.15`(符号つき) | 「△5.8%」が 5.8 の fact に GROUNDED になる = 値の層の false pass |
| b | `builtin:sign(cur-prior)==direction` が差 0 を「減」に数える | `actual = 1 if diff > 0 else −1` | `actual = 0 if diff == 0 else (1 if diff > 0 else −1)`。0 は +1 にも −1 にも一致しない | 差 0 で「減少」と書いた文が GROUNDED になる = 同上 |
| c | prior = 0 は build 時に UNVERIFIABLE | そのまま | そのまま | 妥当 |

recomputed は変えない(pure は `round(fvp, 2)`、ratio は `round(ratio, 2)`、sign は `cur − prior`)。**Core・recipes・期待値・原本は触らない。** 変えるのは `adapters/xbrl/comparators.py` の 3 関数の一致条件と docstring、試験、変異の表だけ。

## 2. 既知(本日測ってある。予測の根拠)

224 件に該当する Claim は **0 件**: pure×100 は 1B の 3 件(N013 10.0 / N014 5.8 / N041 61.7)で全部正、ratio×100 は 1B の 4 件で全部正、文章の Claim で c − p = 0 は 0 件(C-1d の予測 §2)。したがって直しは 224 件の結果を動かさない **はず**。これを点で予測する。

既存の試験で癖を固定している物: `test_comparators.py::test_zero_difference_counts_as_decrease`(差 0 → −1 を assert)。これは **直しで赤くなる**ので、直しの仕様に合わせて書き換える(名前も「差 0 はどちらにも一致しない」に)。変異の表で癖 b の行 `old` を持つ物: D-R3(prediction_miss の記録行)と D-R3b。直しで `old` の行が消えるので差し替えが要る(§4)。

## 3. 予測

| # | 項目 | 予測 | 外れたら |
|---|---|---|---|
| 1 | 計器 3(state・pointers・recomputed・理由・normalization) | **224/224・77/77 不変**(点)。1 回目は **司令塔が凍結時点で回す**(C-1d の手順の直し) | 1 件でも動けば §2 の既知が誤り。期待値は変えず、動いた Claim を表にして止まる |
| 2 | 計器 5・前段照合(C-1c の 7 欄) | 不変(recipes を触らないので構造上) | ― |
| 3 | 変わる試験 | 既存の赤 **1 本**(test_zero_difference…)を書き換え、新規 **4〜6 本**(pure 負の claim、ratio 負の claim、sign 差 0 × 向き ±1、pure 正は従来どおり) | ― |
| 4 | 門 | 217 → **221〜225** | ― |
| 5 | Core 4 本の sha / 期待値 2 本 / recipes.py | 不変(門) | ― |
| 6 | 変異 | 癖を**戻す**変異 3 本(F-R1 pure を |claim| に戻す / F-R2 ratio を戻す / F-R3 差 0 を −1 に戻す)は **default で red・gate_only で green**(224 件は該当 0 なので門は無言 = 直しは実データでは測れていない、を数で残す)。D-R3・D-R3b は `old` が消えるので **F-R3 に置き換え**、D-R3 の prediction_miss の記録は行の note に移して消さない。D-R4(direction 反転)は不変で red | F-R* が gate_only で red なら §2 の既知が誤り |
| 7 | 変異の表の本数 | 22 − 2 + 3(default)+ 3(gate_only)= **26** | ― |
| 8 | 変更の分類(計器 4) | Core 0・登録追加 0・インターフェース拡張 0・意味変更 **Adapter 側 2**(比較子の意味。Core の意味変更は 0) | ― |
| 9 | 行数 | comparators.py ±10 行以内 | ― |

**この段で測れないこと(明記)**: 直しが「正しい」ことは実データでは測れない(該当 0 件)。測れるのは、直しが 224 件を壊さないことと、合成の単体試験で意図どおり VM になることだけ。正しさの実測は 3 社目以降で該当 Claim が出たとき。

## 4. 3 役と止まる所

実装担当(comparators.py・test_comparators.py・mutations.json だけ)→ 司令塔が凍結し **計器 3 を自分で 1 回回して数を記録** → 監査(変異 F-R1〜R3 を自分で当てる、224 不変、Core と recipes 不変)→ GO でコミット → 短い結果文書。REVISE は累積で。
