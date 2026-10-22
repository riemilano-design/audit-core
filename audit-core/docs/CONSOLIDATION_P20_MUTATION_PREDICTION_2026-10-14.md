# P20 の変異の予測(**当てる前に書く**。2026-10-14)

既存の変異は 81 本(`tests/adapters/xbrl/mutations.json` を `python3 -c len` で数えた)。
足すのは 8 本 → 89 本。**赤くなる本数の見積もりは毎回低く出ると記録にあるので、
「全部赤」ではなく 1 本ずつ根拠の試験名を書く。**

| id | 変異 | 予測 | 赤にする試験(名前で書く) |
|---|---|---|---|
| P20-M1 | `FINANCIAL_PREFIXES` から `jpigp_cor:` を落とす | 赤 | `ClassificationTest.test_ifrs_elements_count_too` / `test_both_prefixes_are_named_in_the_constant` |
| P20-M2 | `_nonconsolidated_only` で局所名にせず生の member で比べる | 赤 | `FiresTest.test_the_member_value_carries_a_prefix` / `test_single_member_nonconsolidated_contexts_become_plain` / `BehaviourTest`(3 本) |
| P20-M3 | `_nonconsolidated_only` を「含む」に緩める(内訳も素にする) | 赤 | `DoesNotFireTest.test_breakdown_contexts_never_become_plain` |
| P20-M4 | `with_nonconsolidated_fallback` の連結の門(`!= 0`)を外す | 赤 | `DoesNotFireTest.test_consolidated_document_returns_the_same_object_even_with_the_flag_on` / `test_ifrs_document_...` / **`BehaviourTest.test_p20_does_not_take_the_matching_nonconsolidated_value_when_consolidated_exists`** |
| P20-M5 | `with_nonconsolidated_fallback` で `enabled` を無視する | 赤 | `DoesNotFireTest.test_flag_off_returns_the_same_object` / `BehaviourTest.test_nonconsolidated_only_stops_under_p16` |
| P20-M6 | `consolidated_element_count` の枠の絞り(`PLAIN_PERIOD_CONTEXTS`)を外す | 赤 | `ClassificationTest.test_member_contexts_do_not_count` / `BehaviourTest.test_nonconsolidated_only_grounds_under_p20` |
| P20-M7 | `recipes.py` で旗を読まず `False` を渡す(配線を切る) | 赤 | `WiringTest.test_the_flag_is_read_from_the_profile` / `BehaviourTest.test_nonconsolidated_only_grounds_under_p20` |
| P20-M8 | `plain_context` で落とし込みの枝を消す(素の判定だけに戻す) | 赤 | `FiresTest.test_single_member_nonconsolidated_contexts_become_plain` / `BehaviourTest.test_nonconsolidated_only_grounds_under_p20` |

**scope**: 既定(`default`)の scope に `test_p20` を足す。足さなければ**全部緑**になる
(2026-10-09 の記録「変異が赤くなっても本番で効いているとは限らない」の裏: scope に
無い試験は変異を捕まえられない)。**scope を足す変更そのものも、足す前に 1 本わざと
走らせて「緑のまま」を確かめる。**

**外れ方(どうやったら外れるか)**
- M1〜M8 のどれかが**緑**なら、その変異が覆う入力を留めている試験が無い ― 試験を足す。
- M4 が緑なら最も重い(連結の門が測られていない)。そのときは C-1 = 0 の意味も弱い。
- 予測を外したら**予測は直さず**、外れとして記録する。
