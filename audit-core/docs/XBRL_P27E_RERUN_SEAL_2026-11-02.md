# 封: AI の文を P27E と P27 で再判定する ― claim ごとの記録を作り、P16 の記録で測った 53 行・12 行・8 行が、いまの既定 P27 と外部の文の profile P27E でどう動くかを数える ― 2026-11-02

2026-11-02。人間の指示「全て認めるから君に任せる進めて」(2026-11-02。標準タクソノミのラベル file の cloud への取得を含む)。
今日の 5 便(`a6835dd3`・`59f4d1ea`・`02394a77`・`2d776793` とその封)は、AI の文 1 書類の claim ごとの engine の判定として repo に在る唯一の記録 `entry_output_S100Z4Q1_ai_prose_2026-10-13.json`(**P16**)を材料にした。いまの既定は **P27**(2026-10-28)で、AI が書いた文(外部の数の文)には **P27E**(P27 + B。2026-10-27 に「外部の数の文に使う profile」として採用。既定にしない)がある。P16 → P27 では期の結びつき(P22 以降「期を留める」)と書かれた桁での照合が変わっており、今日の結論(engine が止めた真の文 53 の中身・「その他」の行 12・期の取り違え 8)が P27 / P27E でどうなるかは、各文書で「言えないこと」に置いてある。
本便は **engine を変えず、走らせる**。同梱の AI の文の書類(ZIP)を `verify_document` で P27E と P27 の 2 つの profile で判定し、claim ごとの記録を repo に残し、P16 の記録と行を対応させて、state の動きを数える。ラベル file は人間の許可で cloud の cache に置く(repo には sha256 だけ)。
**engine(`core/`・`adapters/`)は 1 行も変えない。** 走らせるときの engine の中身は `fixtures/frozen_bundle_sha.py` の bundle の sha256 と HEAD の commit で記録する。外へ出す通信はしない(ラベル file の取得は EDINET の公開 file の受け取りだけ)。0 USD。LLM を呼ばない。

## §0 材料(全部 repo の中。sha256 で固定。ラベル file は repo の外、sha256 の名簿で固定)

| 材料 | file | sha256 |
|---|---|---|
| 書類(inline XBRL。経営分析の節は 2026-10-09 の AI の文に差し替え済み) | `fixtures/xbrl/ai_prose_instance_2026-10-09.zip` | `03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799` |
| engine の判定 P16(2026-10-13。比べる元) | `fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json` | `6c4c65d1d24ed46250d6bda41fc023d0624ec130f9c1fe791e840c6def7077da` |
| AI の文の主張(id・文・数・単位) | `fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json` | `c886a9e69353c677297341436f9777b779895054804adce1805f3d546dd4b579` |
| 盲検の札(真 / 偽 / 判定不能、根拠の字) | `fixtures/xbrl/ai_prose_labels_2026-10-09.json` | `7eac1450c40c68e0a25bf7f56c32db4ee6dad226e55df7efdb8019764a71173b` |
| 止めた真の文 53 の記録(型 T1〜T6) | `fixtures/xbrl/derivation_stopped_2026-11-02.json` | `cacbdb62a958522f9284cfc026f057ddb8d7be4c8e648f5ad579faa7edd4775e` |
| 「その他」の行 12 の記録(R1 の判定) | `fixtures/xbrl/other_rule_2026-11-02.json` | `76ad667f53314e4548626dde1176329d951fd853382e9b8949a8fe5a7b962783` |
| 期の印の記録(engine の期の取り違え 9) | `fixtures/xbrl/period_mark_2026-11-02.json` | `7e026ac938f38e5e7f1dd09ba85466419e3831734eaa8f329cdb7d1f37a34901` |
| 標準ラベルの名簿(cache の file 名と sha256) | `fixtures/xbrl/taxonomy_labels_sha256.txt` | `92fe4bcad0d91fcc8256f7f3132494eafd231de9039fa99da3939af11298a13e` |

**封の時点で見た数**(材料の形の確認。予測の対象にしない): 儀式の記録(P27、同じ ZIP の素の書類)の state の分布は GROUNDED 340・POINTER_NOT_FOUND 25・UNVERIFIABLE 33・VALUE_MISMATCH 14(claim 412)。P16 の entry は GROUNDED 330・POINTER_NOT_FOUND 16・UNVERIFIABLE 41・VALUE_MISMATCH 25(claim 412)。札は 真 391・判定不能 23・偽 1(415 行。P16 の entry に無い id が 3)。

## §1 走らせ方(字で固定)

- `adapters.xbrl.verify_document.verify_document(zip_bytes, profile_name, None)` を `"P27E"` と `"P27"` で 1 回ずつ。text は渡さない(ZIP に AI の文が入っている。儀式の「素の書類」と同じ)。
- 出す記録は 2 つの entry(claim ごとの id・kind・form・subject・value・unit・span・state・pointers・reason・recomputed)を、それぞれ `fixtures/xbrl/entry_output_ai_prose_p27e_2026-11-02.json`・`fixtures/xbrl/entry_output_ai_prose_p27_2026-11-02.json` に書く(docID は書かない。P16 の entry の `input`・`document` に当たる欄は、docID を含む字を落として写す)。
- 突き合わせの記録 `fixtures/xbrl/rerun_p27e_2026-11-02.json` に、行の対応と動きの数を書く。
- ラベル file は `taxonomy_labels_sha256.txt` の 3 本が cache に在り sha256 が合うことを走らせる前に確かめる(合わなければ止める)。engine の bundle の sha256(`fixtures/frozen_bundle_sha.py` の `bundle()`)と HEAD を記録に書く。

## §2 行の対応と数えるもの(字で固定)

- **行の対応**: P16 の entry の claim と P27E / P27 の claim を、id の順で並べ、同じ位置の (span, value, unit) が一致すれば対応。一致しない行は (span, value, unit) で探し直す。対応しない行は数だけ。
- **動き**: 札 真・kind num の行について、P16 の state → P27E の state の表(4 × 4)。P27 も同じ。
- **53 行**(止めた真の文の記録の 53 行): P27E / P27 での state の分布。型 T1〜T6 ごとの GROUNDED になった数。
- **12 行**(「その他」の行): P27E / P27 での state。R1 で決まった 8 行のうち GROUNDED になった数。
- **8 行**(期の印の記録で「engine の期の取り違え」かつ 前期の文 × engine 当期 の 8 行): P27E / P27 での state と pointers の context の期。
- **P16 で GROUNDED の 札 真・num の行**(249)のうち P27E / P27 で GROUNDED でなくなった数と id。
- P27E と P27 で state が違う行の数と id。
- P27E で GROUNDED の 札 真・num の行のうち、pointers の要素の local name が札の根拠に無い数(engine が別の要素で GROUNDED にした向き。「止めた真の文」の便と同じ照らし方)。
- 札 偽 1 行の P27E / P27 の state。判定不能 23 行は数だけ。

## §3 事前予測(**実装より先に固定。結果を見てから書き換えない**)

| | 予測 | **外れ方** |
|---|---|---|
| **M-1** | 配線: P27 の 412 claim の state の分布が儀式の記録の素の書類(340・25・33・14)と**一致** | 1 つでも違う(環境・実装の欠陥を先に疑う) |
| **M-2** | 配線: P16・P27E・P27 の claim は id の順で (span, value, unit) が **412 / 412** 対応 | 1 行でも違う(探し直した数を書く) |
| **M-3** | P16 の 53 行のうち P27E で GROUNDED になるのは **5〜15** | 幅の外 |
| **M-4** | P16 で GROUNDED の 札 真・num 249 行のうち P27E で GROUNDED でなくなるのは **0〜12** | 13 以上 |
| **M-5** | 期の取り違え 8 行のうち P27E で GROUNDED になるのは **0〜3**(P27 は期を留めるので前期の値は当期と合わないまま) | 4 以上 |
| **M-6** | 「その他」の VALUE_MISMATCH 9 行のうち P27E で GROUNDED になるのは **0〜2**(P27 に「その他」の規則は無い) | 3 以上 |
| **M-7** | P27E と P27 で state が違う行は **0〜10** | 11 以上 |
| **M-8** | 札 偽 1 行は P27E・P27 とも **GROUNDED でない** | GROUNDED |
| **M-9** | P27E で GROUNDED の 札 真・num の行のうち pointers の要素が札の根拠に無いのは **0〜10** | 11 以上 |
| **M-10** | 判定不能 23 行、P16 の entry に無い 3 行、対応しない行の中身は判定しない。数だけ | ― |

## §4 言えないこと

- 1 書類(1 社)・1 model の AI の文。P27 / P27E の数はこの書類の数で、engine 全体の性質ではない。
- 札の根拠との照らしは local name の部分文字列で、根拠が略された行は照らせない。
- ラベル file の取得は cloud の環境のネットワーク方針に依る。取れなければこの封は結果の文書が無い封として残す(台帳 §4-2)。
- engine の変更はこの便にない。P27E を既定にするかは人間が決める。

## §5 作法

- 封を先に commit → ラベル file を cache に置き sha256 を照らす → script `measure/xbrl_rerun_p27e_2026-11-02.py`(engine を走らせる。`adapters.xbrl.verify_document` を import する ― 儀式の script と同じ。engine の字は変えない)→ 記録 3 つ → 結果 `docs/XBRL_P27E_RERUN_2026-11-02.md` → 門 `tests/measure/test_xbrl_rerun_p27e.py`(engine の走らせ直しはラベル file が在るときだけ。無ければ skip)→ 独立監査 GO → path 指定で commit。
- 覆い・台帳・README の本数は同じ便で揃える。cloud の 93 本の赤い門がラベル file で緑になるかも同じ便で確かめ、結果の文書に書く。
