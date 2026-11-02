# 封: engine が止めた真の文の中身 ― engine の指した fact と導出の候補を札の根拠で照らし、止めた理由を型に分ける ― 2026-11-02

2026-11-02。人間の指示「君に任せる進めて」(2026-11-02。課題は「AI が要約したレポートに engine が対応できるか」)。
ここまでの 5 便(全探索 `9c2437f`・主語の制約 `4278c41`・深さ 2 と型 2 つ `d5f2e76d`・偽の数 `a6835dd3`)で、導出(主語の制約つき・深さ 1・6 型)は **engine が止めた真の文 53 のうち手がかりあり 34 の 15 を 1 つに決め**、偽の数には桁ずらしを通す弱点があると分かった。まだ見ていないのは、**engine が真の文を止めた理由そのもの**である。engine は 53 件の各行で何を指し、何と比べて止めたのか。導出が 1 つに決めた fact と engine が指した fact は同じか別か。別なら、要素が別(主語の取り違え)か、期が別か、文の数が差や率(engine が計算しない量)か。
本便は engine を走らせず、**既にある記録だけ**を突き合わせて、53 行を型に分けて数える。課題に対して言えるのは「AI の文を engine が止めるとき、その多くは何の失敗か」で、直す場所(主語の結びつき / 期の結びつき / 導出の量 / 帯)を決める材料になる。
**engine(`core/`・`adapters/`)は 1 行も変えず、import もしない。** 通信しない。0 USD。LLM を呼ばない。

## §0 材料(全部 repo の中。sha256 で固定)

| 材料 | file | sha256 |
|---|---|---|
| AI の文の主張(id・文・数・単位) | `fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json` | `c886a9e69353c677297341436f9777b779895054804adce1805f3d546dd4b579` |
| 盲検の札(真 / 偽 / 判定不能、根拠の字) | `fixtures/xbrl/ai_prose_labels_2026-10-09.json` | `7eac1450c40c68e0a25bf7f56c32db4ee6dad226e55df7efdb8019764a71173b` |
| engine の判定(profile P16。state・pointers・recomputed・reason・form・subject) | `fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json` | `6c4c65d1d24ed46250d6bda41fc023d0624ec130f9c1fe791e840c6def7077da` |
| 主語の制約の便の記録(行ごとの手がかり S・K0 の判定・候補の fact) | `fixtures/xbrl/derivation_subject_2026-11-02.json` | `6703ae50e2fcee8bf6340fc96c89b7bd530b472b5b103efc83e2e40c0eb02de0` |

**母数**: 主語の制約の便の母数と同じ **53 件**(札が 真・kind が num・P16 の state が GROUNDED でない。封 `ab09aa6` の字では VALUE_MISMATCH 23・UNVERIFIABLE 18・POINTER_NOT_FOUND 12。手がかりあり 34・手がかりなし 19)。対照は置かない(GROUNDED の行は engine が止めていない)。
**既に記録に在る数(予測の対象にしない)**: 手がかりあり 34 の K0 の判定(導出一致 15・保留 5・不一致 14)、導出一致 15 の候補の型(D1 9・D2 4・D5 2)、導出一致 15 のうち候補の要素名が札の根拠に在る 14。

## §1 行ごとに引く字(字で固定)

engine の側(entry の claim から): `state`・`form`(direct_value / derived_value)・`pointers`(`xbrl:prefix:Local@context` の列。要素と context に分ける)・`recomputed`・`reason`・`subject`。
導出の側(主語の制約の便の記録から): K0 の判定・候補(型と fact の列。導出一致の行は候補 1)。
札の側: 根拠の字。**要素が根拠に在る** = その要素の local name(`:` の後)が根拠の字に部分文字列として在る(主語の制約の便の「根拠に要素名」と同じ決め方)。

## §2 型(1 行に 1 つ。上から順に当てて最初に当たった型)

| 型 | 条件 | 読み |
|---|---|---|
| **T1 指せず** | engine の pointers が空 | engine は主語を fact に結べなかった |
| **T2 同じ fact** | K0 導出一致、候補が D1、候補の fact(要素と context)が engine の pointers の 1 つと同じ | 同じ fact を見て engine は値が合わないと言い、導出の帯(g + u)は合うと言った ― 帯・丸めの違いだけ |
| **T3 導出の量** | K0 導出一致、候補の型が D2〜D6 | 文の数は差・増減率・和・比率・一株あたり(engine が計算しない量) |
| **T4 同じ要素・別の期** | K0 導出一致、候補が D1、候補の要素が engine の pointers の要素と同じで context が別 | 期の結びつきの取り違え(engine か文のどちらかが別の期を見た) |
| **T5 別の要素** | K0 導出一致、候補が D1、候補の要素が engine の pointers のどれとも別 | 主語の結びつきの取り違え |
| **T6 導出も決めない** | K0 が保留・不一致、または手がかりなし | 導出では理由が言えない行 |

T2 の行には参考として、engine の帯の形(round: |fact − t| ≤ u / 2、truncate: 0 ≤ fact − t < u。`adapters/xbrl/comparators.py` の `_match_value` の字。本便は読むだけ)で候補の値が入るかを書く(どちらの丸め方を engine が選んだかは entry に無いので、両方を書く。判定には使わない)。

## §3 数えるもの(字で固定)

- 53 行の型 T1〜T6 の件数。state(VALUE_MISMATCH / UNVERIFIABLE / POINTER_NOT_FOUND)× 型の表。
- VALUE_MISMATCH 23 のうち **engine の pointers の要素が札の根拠に 1 つも在らない**行(engine が主語を取り違えた向きの数)。
- VALUE_MISMATCH 23 のうち engine の `form` が derived_value の行(engine 自身が差などを計算して比べた行)。
- UNVERIFIABLE 18 の `reason` の分布と、pointers が空でない行の数。
- 53 行のうち「K0 が 1 つに決め、候補の要素が札の根拠に在り、engine の pointers の要素は根拠に無い」行(導出が engine の取り違えを正した形)。
- 手がかりあり 34 で、engine の pointers の要素が手がかり S に入っている行(A1 は engine の自分の pointer なので、state が VALUE_MISMATCH / UNVERIFIABLE で pointers が在れば必ず入る ― 配線の確かめ)。

## §4 事前予測(**実装より先に固定。結果を見てから書き換えない**。母数 53)

| | 予測 | **外れ方** |
|---|---|---|
| **J-1** | 配線: 53 行の P16 の state の分布が封 `ab09aa6` の字(VALUE_MISMATCH 23・UNVERIFIABLE 18・POINTER_NOT_FOUND 12)と一致し、手がかりあり 34 の K0 の判定が前の便の記録と **53 / 53** 行で一致 | 1 行でも違う(実装の欠陥を先に疑う) |
| **J-2** | VALUE_MISMATCH 23 のうち engine の pointers の要素が札の根拠に 1 つも在らない行 **10〜18**(止めた主因は値ではなく主語の結びつき) | 幅の外 |
| **J-3** | **T2 同じ fact** は **0〜2**(engine の帯は書かれた桁で厳しく、導出の帯 g + u が緩い。同じ fact で食い違う行は少ない) | 3 以上 |
| **J-4** | **T3 導出の量**(件数は前の便の記録から 6 と分かっている)のうち、engine の pointers の要素が候補の fact の要素の 1 つである行 **3〜6**(engine は主語を正しく結び、差や率を計算しなかっただけ) | 2 以下 |
| **J-5** | **T4 同じ要素・別の期** は **1〜4** | 幅の外 |
| **J-6** | **T5 別の要素** は **3〜8** | 幅の外 |
| **J-7** | UNVERIFIABLE 18 の `reason` は **1 種類に 10 以上**集まる | 最多の種類が 9 以下 |
| **J-8** | 「導出が engine の取り違えを正した形」(K0 が 1 つに決め、候補の要素が根拠に在り、engine の要素は根拠に無い)は 53 のうち **6〜12** | 幅の外 |
| **J-9** | VALUE_MISMATCH 23 のうち `form` が derived_value の行 **0〜5** | 6 以上 |
| **J-10** | 手がかりなし 19 は T1 か T6 に入る(数だけ)。T2 の engine の帯の参考は判定しない | ― |

## §5 言えないこと

- entry は P16 の判定(2026-10-13)。いまの既定 P27 で同じ 53 行がどう判定されるかは、行ごとの P27 の記録が repo に無く、engine を走らせるには標準ラベルの cache が要る(cloud に無い)。デスクトップの仕事。
- 型は engine の pointers と導出の候補の字の突き合わせで、どちらが正しいかは札の根拠の字との部分一致で見るだけ(目で読んだ分類は【門なし】)。
- 1 書類(1 社)・1 model の AI の文。導出は深さ 1・6 型。
- 直す場所を決めるのは人間。engine の変更はこの便にない。

## §6 作法

- 封を先に commit → script `measure/xbrl_derivation_stopped_2026-11-02.py`(標準ライブラリだけ。engine は import しない。前の便の script も読まない ― 候補は記録に在る)→ 記録 `fixtures/xbrl/derivation_stopped_2026-11-02.json`(claim id は書いてよい。docID は書かない)→ 結果 `docs/XBRL_DERIVATION_STOPPED_2026-11-02.md` → 門 `tests/measure/test_xbrl_derivation_stopped.py` → 独立監査 GO → path 指定で commit。
- 覆い・台帳・README の本数は同じ便で揃える。
- 本封と同じ commit で、偽の数の便の結果文書に追記 2(engine の帯についての見込みの訂正。文書だけ)を入れる。
