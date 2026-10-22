# fix5 保護面 6 ファイルの提案 patch(2026-10-12)

**D-001(人間の決定、`e7dbf93` の `docs/DECISION_LOG.md`)への回答。merge しない。main には触っていない。**

> 手順0は A。main を製品線とする。fix5 の数(47.1→34.4)は台帳から外す。並行席は保護面6ファイルの提案patchをsha固定で用意し、mergeしない。①の原因内訳が fix5 の直す型と一致した場合のみ、手順3で最初の候補として封じて当てる

## 1. patch の本体

| | |
|---|---|
| ファイル | `audit-core/patches/fix5_protected_surface_2026-10-12.patch` |
| **sha256** | **`74e70074aa8d5f5b0f1c67d59c13f470186ececcac102fb00ff2aa8384ee2b50`** |
| バイト数 | 91,873 |
| 作り方 | `git diff main...feature/audit-core-xbrl-fix5 -- <6 ファイル>`(分岐点 `0d54c9a`) |
| 対象 6 ファイル | `comparators.py`(+48 行)・`extract.py`(+240)・`instance.py`(+247)・`recipes.py`(+473)・`registry_setup.py`(+11)・`vocabulary.py`(+381) |
| 測定 JSON | **含めていない**(`measure_xbrl_fix5_*.json` は対象外、50 万行) |

**main への当て込みを確かめた**(作業用の一時フォルダで。main・共有の木には触っていない):
`git apply --check` は `rc=0`(オフセットのみ、衝突 0)。**実際に当てて**、
main の `_direct_value_claim` に案ア(`5b0f356`、主語の無い数の主張を束縛しない)の
`if subj: ... else: claim["reason"] = "no_subject"` の形が**そのまま残る**ことを確認した
(`value_only(no subject)` の文字列は当てた後も 0 件 ― 案ア は壊れない)。

## 2. hunk ごとの分類と、4 書類での件数

**件数は「P7 からの累積の差」ではなく、各 flag を P11/P13 の**単独**(その flag だけ、他は乗せない)
で測った、**孤立した効果**である。開発 4 書類(`S100Z4Q1`・`S100Z4B6`・`S100YMFV`・`S100Z37J`)の
合計。出どころは `fixtures/xbrl/measure_xbrl_fix5_*.json`(枝に既存)の `rows` を比較して算出
(保存済みの `diff` フィールドは P7 からの累積比較なので使っていない)。

| flag / hunk の中身 | ファイル | **直す型** | 比較の形 | state が変わった件数 |
|---|---|---|---|---|
| `doc_rounding`(書類単位の丸め方を 1 つに決める) | recipes.py・vocabulary.py | **丸め** | P7 単独 vs base | 61 |
| `target_both`(照合の的を両方試す) | recipes.py・vocabulary.py | **丸め** | P7 単独 vs base | 4 |
| `label_statement_rows_only`(§7a 計算書の行のみ) | recipes.py・vocabulary.py | **束縛** | P11 単独 vs P11 | 9 |
| `label_overrides_dead_hand`(§7b 死んだ手書きの上書き) | recipes.py・vocabulary.py | **束縛** | P11 単独 vs P11 | 3 |
| 手書きの語彙の直し(§7c、`V.SUBJECTS_P12`) | vocabulary.py | **束縛** | P11 単独 vs P11 | 3 |
| **§7a+§7b+§7c 合計**(= P12 vs P11) | recipes.py・vocabulary.py | **束縛** | 組み合わせ | **12**(9+3+3 と一致しない ― 重なりが在る) |
| `taxonomy_labels`(標準タクソノミのラベル、§8) | instance.py・recipes.py・vocabulary.py | **束縛** | P13 vs P12 | 10 |
| `subject_skip_coordinated_cause`(S1、並列の原因の主語を跨がせない) | extract.py・vocabulary.py | **束縛** | P13 単独 vs P13 | 3 |
| `subject_direction_object`(S2、向きの目的語) | recipes.py・vocabulary.py | **束縛**(かつ `dropped`=2 件の主張を落とす) | P13 単独 vs P13 | 0(落ちた主張 2) |
| `subject_not_part_of_aggregate`(S3、合計の一部を主語にしない) | extract.py・vocabulary.py | **束縛** | P13 単独 vs P13 | 2 |
| `direction_word_lexicon`(S4、向きの語彙) | recipes.py・vocabulary.py | **その他**(語彙の拡張。`dropped`=9 件) | P13 単独 vs P13 | 2(落ちた主張 9) |
| `direction_amount_check`(A1、差の金額照合) | comparators.py・recipes.py・vocabulary.py | **丸め**(§0 の整数差の導出。2026-10-09 に **FAIL / 棄却**、下記 §3) | P13 単独 vs P13 | 5 |
| `_match_value` の符号を落とす枝(`abs` 2 周目) | comparators.py | **符号** | ― (未実装・測っていない) | ― |
| 主語の規則そのもの(`subject_of` の再設計) | extract.py | **束縛**(土台。上の S1/S3 が使う) | ― | ― |

**符号の型は、まだ実装していない `Sign semantics` 封の対象で、この patch の hunk には
「使われていない」防御コード(`comparators.py:289` の `abs(difference)`)としてのみ在る。
単独で動かした測定は無い。**

## 3. ①(AI 文実験・本線)との一致判定に使えること

2026-10-09 の記録(`XBRL_A1_TOLERANCE_RESULT_2026-10-09.md`・`XBRL_DECISIONS_2026-10-09.md`)で
確定している事実:

- **A1(差の金額照合、±0.5 単位)は `FAIL / 棄却`。** 未使用 2 書類で 1 単位超の誤停止 8 件、
  うち**丸め起因は 0 件**(全部束縛誤りか符号規約)。**この patch の A1 の実装は、
  いまの ±0.5 のままである**(A1-A は未実装、棄却のまま)。
- **`Binding` 7 件は 2 つの型に割れる**: (a) 正しい fact が在るのに別要素/期に結んだ 5 件、
  (b) 正しい fact が存在しない 2 件。**本線の `N275`/`N276` 型(区分・関係の誤り、偽の通過)とは
  向きが逆**なので、①の原因内訳が「偽の通過」側なら**この patch とは一致しない**可能性が高い。
  「偽の停止」側(誤った告発)なら §7a/§7b/§7c・S1/S3 の束縛系の hunk が候補になる。
- **391 件(AI 文)への効果は未測定。**この patch 自体も測っていない(§2 の数はすべて
  人間の MD&A・開発 4 書類のもの)。

## 4. 凍結

| | |
|---|---|
| 守る面(この枝) | `5873ac7803adfa9de22195943b552e5f9d829611e1404f247a2397e629734f3d`(不変) |
| 分岐点 | `0d54c9a` |
| main への当て込み | 確認済み(`rc=0`・案ア 健全) |
| main への merge | **していない。しない。** |
| 規則の変更 | **この commit で 0**(patch を切り出しただけ) |
