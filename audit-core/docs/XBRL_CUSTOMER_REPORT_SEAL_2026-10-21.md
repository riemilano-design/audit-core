# 封: 顧客向けの報告形(新しい module。既存の報告は触らない)― 2026-10-21

**engine 側(`adapters/xbrl/` に module を足す)の変更。人間の承認(2026-10-21 深夜)「先に承認しておくので好きに進めて これをもって承認とする」。既存の `adapters/xbrl/report.py` は人間の決定(2026-10-13「判定に手を加えない・golden」)のまま 1 字も触らない。判定(state・reason・pointer)は足さず変えず、並べ方と字だけを変える。**

## §0 根拠(客の 1 回 2026-10-20 と封の前の下調べ 2026-10-21)

- 客 A(開示担当者): 「値が違う」の表はそのまま上司に見せられる。pointer の英字と `formula:a-b`、根拠の値が円で文が百万円、理由の字(no_element 等)は読めない。「一致」に前期の数が混ざる印が無い(P22 で解消)。
- 客 B(政策担当): sha256・engine の指紋・英語の state・`unresolved:…` が混じり会員には出せない。止まった理由の列が「―」。
- 下調べ: GROUNDED でない 3,557 のうち、出典に fact が無い (a) = `no_element(unit not in XBRL)` 145・`no_prior_member_context` 6、判断しないが正しい (c) = `no_subject` 1,001・`target_or_plan` 42・`ambiguous(member)` 38。合わせて 1,232 / 3,557 = 34.6% は「人が読み直す警告」ではない。
- 試作(2026-10-21、clone の中、司令塔の席の手元の数。scratchpad/report/proto_report.md): 客 A の P22 の出力(39 claim)で answer_key の 5 件は 5 / 5 が先頭の節「違う」に在り、出典の値は文と同じ単位(N001 40,480 百万円、N015 53,812,000 千円 = 文が千円、N010 36.22%、語の主張 T009 は単位が無いので円)。67 書類(既定 P22、7,799 claim): 違う 1,410 / 要確認 915 / 対象外 151 / 判断しない 1,081 / 一致 4,242(当期 1,736・前期 180・計算 2,326)。理由の表 14 key = `UNBOUND_REASON_STATE` 14 key。同じ JSON から同じバイト列(CLI 2 回、67 書類 2 回)。`report.py` の golden 13 本は緑のまま。**adapters/xbrl に module を足すだけで engine の指紋(adapter_xbrl_py_sha256、15 file → 16 file)が動き、frozen_bundle の本数 36 → 37、「engine 不動」を見る門(point_prior の B-5・ritual の R-8)が赤になる = commit で遷移の宣言が要る。**

## §1 中身

- 新 module `adapters/xbrl/report_customer.py`(`python3 -m adapters.xbrl.report_customer --in out.json --out report.md [--labels <dir>]`)。純粋関数、同じ JSON から同じバイト列(golden)。LLM なし。
- 節の順と字(state・reason から決定論で引く。表は字で留める):
  1. **違う** = VALUE_MISMATCH。列: 文の抜粋 / 文の値 / 出典の値(**文と同じ単位に直す**。直接の値は claim の単位の倍率で割る。率・差は engine の値のまま)/ 出典(**日本語**: 要素の標準ラベル(ラベル file があれば。無ければ要素名)+ 期の字「当期」「前期」「当期末」「前期末」。計算なら「当期 − 前期」等)。
  2. **要確認** = POINTER_NOT_FOUND と UNVERIFIABLE のうち (a)(c) 以外。列: 文の抜粋 / 文の値 / **理由(日本語の 1 行。reason の字から表で引く。表に無い reason は字のまま出して赤にしない)**。
  3. **対象外**(出典に無い) = (a) の reason。**判断しない** = (c) の reason。件数と抜粋だけ。
  4. **一致** = GROUNDED。件数と、出典の内訳(当期 / 前期 / 計算)の件数。行は省略可(`--full` で出す)。
  5. 末尾に小さく: 書類・入力の sha256・engine の指紋・profile(1 行ずつ)。
- 理由の日本語表(reason → 1 行)は登録簿の理由の全部を網羅する(`registry_setup._POINTER_NOT_FOUND_REASONS` 9 + `_UNVERIFIABLE_REASONS` 7 = 16。`recipes.UNBOUND_REASON_STATE` の 14 key + `other_frame` + `no_same_value` と同じ集合。網羅を門で縛る。新しい reason が増えたら赤)。P24 の `other_frame` と P25 の `no_same_value` は「要確認」に置く: `other_frame` =「同じ項目の別の区分(セグメント・単体等)の数と合う。どの区分の数かを確かめる」、`no_same_value` =「出典の当期の数と合わず、同じ数も桁違いの数もこの項目に無い。参照先を確かめる」。
- profile は入力の JSON に書かれた profile をそのまま出す(報告は判定をしない)。測定は既定(P22)と P25 明示の 2 通り。
- 議事録(`adapters/kokkai/report_meeting.py`)は別の封(この封は有報だけ)。

## §2 事前予測

| # | 予測 | 外れ方 |
|---|---|---|
| **C-1** | 客 A の P22 の出力(誤り入り 39 claim)を新しい報告にすると、答え合わせの 5 件が先頭の節「違う」に **5 / 5** 在り、出典の値は文と同じ単位(百万円の文は百万円、千円の文は千円。語の主張は円) | 5 件が先頭に無い / 単位が文と違う |
| **C-2** | 67 書類の無改変(既定 P22)で、「違う」**1,410**、「要確認」**880〜950**、「対象外 + 判断しない」**1,200〜1,260**、「一致」4,242。足して 7,799 | 幅の外 / 和が合わない |
| **C-2b** | 同じ 67 書類を P25 明示で: 「違う」**626**、「一致」**4,382**(P25 段 1 の記録 fixtures/xbrl/lastbranch_2026-10-21.json の VALUE_MISMATCH・GROUNDED)、「対象外 + 判断しない」**1,190〜1,250**、「要確認」**1,540〜1,600**。足して 7,799 | 幅の外 / 和が合わない |
| **C-3** | 理由の日本語表は登録簿の理由の全部(**16** = `UNBOUND_REASON_STATE` の 14 key + `other_frame` + `no_same_value`)を網羅し、網羅の門が理由を 1 つ消すと赤 | 赤にならない / key の数が違う |
| **C-4** | 同じ JSON から 2 回で同じバイト列。`report.py` の golden は不変 | 違う / golden が動く |
| **C-5** | 既存の `report.py`・`verify_document.py` は 0 行。engine の指紋は module を足した分だけ動く(宣言された遷移) | 1 行でも / 宣言なしに赤が残る |

## §3 限界

- 「対象外」「判断しない」の線は reason 単位で、混在の reason(no_element 等)は全部「要確認」に入る(安全側)。
- 標準ラベルは repo の外(2026-10-08 の人間の決定)。無ければ要素名のまま。IFRS(`jpigp_cor`)と会社ごとのセグメント member はラベル file に無く要素名のまま(67 書類で 48 行 + member の字)。
- 語の主張(「増加した」等)の出典の値は単位が無いので円で出る。`report.py` 末尾の「率・差は文と同じ単位」は差については実物と違う(差も円)― `report.py` は触らないので、この封の文書に 1 行書く。
- 「違う」が正しい文に出る率は報告の形では減らない(既定 P22 で 1,410 / 7,799 = 18.1%。P25 明示で減るのは P24・P25 の engine の直しの効き目で、この封の効き目ではない)。
- `no_same_value` の名指した当期の値は `Claim.provenance` に在るが、`verify_document` の出力 JSON には provenance の欄が無い。この封は `verify_document.py` を触らないので、報告に「当期の値は X」は出さない(理由の 1 行だけ)。出すなら別の封。

## §4 触る file と順序

試作の module は scratchpad の clone(`scratchpad/report/clone/audit-core/adapters/xbrl/report_customer.py`、513 行、試験 18 本)。流用してよいが、P24 の `other_frame`・P25 の `no_same_value` の行と C-2b はこの封で足す。同じ便で P25 の監査の軽い指摘(`_written_precision` の丸めを切り捨てにする変異が黙る)に、桁の倍数でない値の unit 試験を `tests/adapters/xbrl/test_recipes_p25.py` に 1 本足す(engine は変えない)。


`adapters/xbrl/report_customer.py` → `tests/adapters/xbrl/test_report_customer.py`(golden・網羅・単位・C-4)→ `measure/xbrl_customer_report_2026-10-21.py`(C-1・C-2)→ `fixtures/xbrl/customer_report_2026-10-21.json` → `docs/XBRL_CUSTOMER_REPORT_RESULT_2026-10-21.md` → `tests/measure/test_xbrl_customer_report_result.py` → README の入口(有報: 自分の zip + 文 + 報告の 3 行)→ pin の遷移の宣言(engine の束ねた sha・frozen_bundle 36 → 37・point_prior の B-5・ritual の R-8・ENGINE_LATER は vocabulary/recipes が不変なら不要、axis3 の LATER_ENGINE_COMMITS は次の便)→ 覆い。
順序: 人間の事前承認(2026-10-21)→ P25 段 1 の commit(9577eab・宣言 0db03a4)→ この封 + 門を commit → 実装 → 凍結 → 独立監査 → commit → axis3 の宣言 → 段 2(既定の切り替え)を人間に。
