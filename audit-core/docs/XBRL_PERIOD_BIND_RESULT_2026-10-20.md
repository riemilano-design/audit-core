# 結果: 期を縛る直し P22 の段 1(2026-10-20)

封: `docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md`(commit `4953a4f`。本文 §0〜§4 と予測 E-1〜E-8 は一字も直していない。末尾に日付つきの追記だけ足した)。測定: `measure/xbrl_period_bind_2026-10-20.py`。記録: `fixtures/xbrl/period_bind_2026-10-20.json`。門: `tests/measure/test_xbrl_period_bind_result.py`。engine の直し: `adapters/xbrl/recipes.py` 挿入 4・削除 0、`adapters/xbrl/vocabulary.py` 挿入 4・削除 1、`core/` 0 行。 **人間の承認(2026-10-20「君に任せる」)の範囲は段 1(旗 P22 だけ、既定は P21 のまま)。段 2(既定 P21 → P22)は、この結果を人間に見せてから別に諮る。** API 鍵は使っていない・通信なし・0 USD。独立監査(2026-10-20)の REVISE を受けて、engine の条件に「主語あり」を足し(§3 の注)、測定を全部やり直した。この文書の数のある文はすべて記録から門が作り直す(§12)。

## 0. 結論

**予測 機械判定 当たり 3 / 外れ 3**(E-1〜E-5・E-7。E-6 は人の読み、E-8 は段 2 なので判定しない)。 判定は §1。

- **E-1(当たり)**: 穴 B の注入 485 件を P22 で検証し直すと、通した(GROUNDED のまま)のは **1 / 485 = 0.2%**(P21 の再計算は 459 / 485 = 94.6%)。止めた(VALUE_MISMATCH)は 482 / 485 = 99.4%。前期へ移って通した件数は P21 458 → P22 0。P21 の再計算は穴 B の記録の 485 行と 1 行ずつ比べて、違った行 0(道具の再現)。
- **E-2(外れ)**: 経営分析の文を持つ 67 書類の無改変(7799 claim)で、P21 で GROUNDED の 4267 行のうち動いたのは 36 行(GROUNDED を離れた 25・GROUNDED のまま参照先だけ動いた 11)、P21 で GROUNDED でない行で動いたのは 0、新 GROUNDED 0。
- 群別(P21 で GROUNDED): 手がかり無し 26 行のうち動いた 25(離れた 14)・手がかりあり 190 行のうち動いた 11(離れた 11)・当期 1726 行のうち動いた 0・pointer が 1 本でない 2325 行のうち動いた 0。
- **E-6(人の読み)**: A「減少額が前期の残高と一致」の率は分母の選び方で変わる。GROUNDED を離れた行 25 を分母にすると 13 / 25 = 52.0%、動いた GROUNDED の行 36 を分母にすると 13 / 36 = 36.1%、動いた全 state の行 36 を分母にすると 13 / 36 = 36.1%。封の予測『過半』は『動いた無改変の行(E-2 の幅の GROUNDED を離れた行)』の読みでは 届いた、ほかの分母では 届かない。
- **C は封 §3 の限界(手がかりの字の一覧を広げる直しはこの封に含めない)が実測に出たもの**。「前年は…」「前期 親会社株主に…」「前連結会計年度に使用した資金は…」「前連結会計年度末残高…」の形は、engine の字の規則(`_prior_cue`・`_prior_cue_clause`)に載らない。字の一覧を広げるのは別の直し(人間の承認)。
- **E-3(当たり)**: 名指しの直しの無改変 40 書類(4665 claim、cache に無い書類 0、67 書類の中に入る書類 40)で、動いた行 23(P21 で GROUNDED の行 23 = 離れた 16 + 参照先だけ動いた 7)、新 GROUNDED 0。
- **E-4(当たり)**: 段 2 の材料(192 行・注入 64)で Core 自身の T6 は P22 で 0 / 10 = 0.0%(段 2 の記録は 6 / 10 = 60.0%、P21 の再計算は 6 / 10 = 60.0%)。全注入では P22 で GROUNDED 0 / 64 = 0.0%。Core 自身が動いた行 6(型を問わず)、対照の違い 0。α 型を当てた 128 行を再計算して記録との差 0。
- **E-5(外れ)**: 儀式(同梱の 1 書類)で 通した 15 / 240 = 6.2%・止めた 225 / 240 = 93.8%(P21 の再計算 通した 17 / 241 = 7.1%・止めた 224 / 241 = 92.9%、儀式の記録と違った行 0)。動いた行 N125 V2・N199 V2。注入の対象から外れた行 1・対象に増えた行 0・両方に在る行で結果が同じ 238。
- **E-7(外れ)**: engine の差分は `adapters/xbrl/recipes.py` 挿入 4・削除 0、`adapters/xbrl/vocabulary.py` 挿入 4・削除 1、`core/` 0 行。 既存試験(封の 3 か所を直した後): `python3 -m pytest -q tests/adapters/xbrl` → 827 passed, 1 skipped in 1101.00s (0:18:21)。封の 3 か所のほかに直した既存試験: 1 件。
- 次の一手は人間の決定(段 2 = 既定を P22 にするか、C の字の一覧を広げる別の封にするか)。**この文書は段 2 を実行しない。**

## 1. 予測 E-1〜E-8(封の字。実装の前に固定。判定は記録・封から門が求め直す)

幅は封 §2 の字(門が封の字から読む)。**本当に測っているのは E-1・E-2・E-6**(封の字)。

| # | 実測 | 判定 |
|---|---|---|
| **E-1** | 通した 1 / 485・止めた(VALUE_MISMATCH)482・その他 2 | **当たり** |
| **E-2** | P21 で GROUNDED の行のうち動いた 36(GROUNDED を離れた 25・GROUNDED のまま参照先だけ動いた 11)、新 GROUNDED 0。群別(動いた GROUNDED): 手がかり無し 25 / 26・手がかりあり 11 / 190・当期 0 / 1726 | **外れ** |
| **E-3** | 動いた行(全 state)23・うち P21 で GROUNDED だった行 23(GROUNDED を離れた 16・参照先だけ動いた 7)・新 GROUNDED 0。キャッシュに無い書類 0 | **当たり** |
| **E-4** | T6 の Core 自身 P22 が GROUNDED 0 / 10(段 2 の記録 6)。α 型を当てた 128 行のうち記録と違った 0 | **当たり** |
| **E-5** | 通した 15 / 240・止めた 225 / 240・動いた行 2(N125・N199)・対象から外れた行 1・他で結果が同じ 238 | **外れ** |
| **E-6** | GROUNDED を離れた行 25 のうち、機械の印(文に 減少・減)13・(増加・増 だけ)8・印なし 4。動いた行の分母は 3 通り(GROUNDED を離れた行 25・動いた GROUNDED の行 36・動いた全 state の行 36)で、過半かどうかは分母の選び方に依る。型の読みは人の読み(結果文書) | **判定は文書で(人の読み)** |
| **E-7** | recipes.py 挿入 4・削除 0、vocabulary.py 挿入 4・削除 1、core/ 0 行。既存試験 python3 -m pytest -q tests/adapters/xbrl → 827 passed, 1 skipped in 1101.00s (0:18:21) | **外れ** |
| **E-8** | 段 2(既定 P21 → P22)は人間の承認の後。この実行では何も変えていない(DEFAULT_PROFILE = P21) | **判定しない(段 2)** |

- E-2 の部分の判定: 幅 22〜30(GROUNDED を離れた行): はい・動いた GROUNDED の行の総数(離れた + 参照先だけ動いた)も 22〜30: いいえ・新 GROUNDED 0: はい・向きが全部 GROUNDED → 非 GROUNDED(参照先だけ動いた行 0): いいえ・手がかりあり 190 行が不動: いいえ・当期 1726 行が不動: はい
- E-3 の部分の判定: 動いた GROUNDED の行 ≤ 40: はい・新 GROUNDED 0(向きが逆でない): はい・全部 GROUNDED → 非 GROUNDED(参照先だけ動いた行 0): いいえ
- E-5 の部分の判定: 通した 15: はい・止めた 226: いいえ・N125・N199 が VALUE_MISMATCH に(動いた行はこの 2 つだけ): はい・他の 239 件は同じ結果(対象 241 のまま): いいえ

**封も予測も直していない。** 外れた E-2 は『代価が割れた』向き(動く GROUNDED の行が幅の外 + 手がかりありの群が動いた)、E-5 は『分母が減った』向き、E-7 は『封が数えた既存試験の直しが足りなかった』向き。

## 2. E-1: 穴 B の注入を P22 で再検証

入力 = 穴 B の記録(`fixtures/xbrl/point_prior_2026-10-20.json`)と同じ書類・同じ site・同じ注入の字(既定 P21 の土台で選んだ site、一文一件・束で再検証)。**profile だけを P21 / P22 にして検証し直した**。

| 単位 | 注入 | P21 通した | P22 通した | P22 止めた | P22 その他 |
|---|---:|---:|---:|---:|---:|
| % | 24 | 1 | 1 | 23 | 0 |
| 円 | 20 | 20 | 0 | 20 | 0 |
| 千円 | 392 | 390 | 0 | 390 | 2 |
| 名 | 1 | 0 | 0 | 1 | 0 |
| 百万円 | 48 | 48 | 0 | 48 | 0 |
| **合計** | **485** | **459** | **1** | **482** | **2** |

P21(対照) 通した 459 / 485 = 94.6%・P22 通した 1 / 485 = 0.2%・P22 止めた 482 / 485 = 99.4%・P22 その他 2 / 485 = 0.4%

- P22 で通した 1 件: S100YXLE N081(89.4% → 89.5%、%)。
- 止めた 482 件の state は VALUE_MISMATCH 482。
- P21 → P22 の遷移: その他 → その他 2、止めた → 止めた 24、通した(参照先が前期へ移った) → 止めた 458、通した(参照先が当期の同じ参照先のまま) → 通した(参照先が当期の同じ参照先のまま) 1。
- その他 2 件の内訳: id_shift | None 1・sentence_not_found | None 1(穴 B の記録でも『その他』。注入の道具側の事情で P21 でも同じ)。
- 通した行の注入後の文で `_prior_cue` か `_prior_cue_clause` が真のもの: 0(封 §0 の外れ方の数)。
- 注入は「前期の値を当期の数の位置に書いた」文なので、構造上すべて手がかり無しの文になる。**手がかりを付けた文は測れていない**(§11)。

## 3. E-2: 無改変を P21 と P22 で比べる

入力 = 経営分析の文を持つ書類(穴 B・封 §0 と同じ集合)の書類自身の本文(製品の経路。`verify_document(zb, "P21")` と `(zb, "P22")`)。claim の id・span の並びが両者で一致することを確かめてから、`(state, pointers, reason, recomputed, form)` の組が違った claim を数えた。

**注(独立監査の指摘で直した点)**: 最初の実装は主語なしの数にも期の絞りを掛けたため、P21 では `no_subject` / `ambiguous(elements)`(UNVERIFIABLE)だった主語なしの数が、前期の fact にだけ合うとき `no_element`(POINTER_NOT_FOUND)に動いた。案ア(2026-10-08 の人間の決定: 主語が取れない数は束縛せず UNVERIFIABLE)の出力が動いたので、条件に「主語あり」(`subj and`)を足し、主語なしは P21 と同一のままにした。主語ありの行の結果は変わらない。人間が「主語なしも POINTER_NOT_FOUND でよい」と決めるなら別の便。

動いた 36(P21 で GROUNDED の行 36 = GROUNDED を離れた 25 + GROUNDED のまま参照先だけ動いた 11、P21 で GROUNDED でない行 0)、新 GROUNDED 0

| 群(P21 で GROUNDED) | 件数 | 動いた | うち GROUNDED を離れた |
|---|---:|---:|---:|
| Prior1Year・手がかり無し | 26 | 25 | 14 |
| Prior1Year・手がかりあり | 190 | 11 | 11 |
| 当期 | 1726 | 0 | 0 |
| pointer が 1 本でない | 2325 | 0 | 0 |

- 封 §0 の数 26 / 190 / 1,726 / 4,267 は P21 側の数え直しで再現した: 手がかり無し 26・手がかりあり 190・当期 1726・全 GROUNDED 4267。
- 手がかり無しの群で動かなかった行は、数の直後が「から」などで engine の `_prior_cue` が真になるもの(封 §3 の予想の型)。
- 動いた 36 行の型(人の読み): A 13・B 1・C 11・D 10・E 1。
- GROUNDED を離れた 25 行の行き先: GROUNDED → POINTER_NOT_FOUND 13・GROUNDED → VALUE_MISMATCH 12。
- 手がかりありの群で GROUNDED を離れた行(C)は、span に前期の語が在るのに engine の `_prior_cue`・`_prior_cue_clause` が偽の形(数の直前十二字の外、または語の一覧の外)。

### 3-1. 動いた行の全部(型は人の読み)

型の読みは一件ずつ文脈を読んだ人の読みで、機械の印ではない。門は記録の行と過不足なく対応することだけ縛る。

| 型(人の読み) | 件数 |
|---|---:|
| A 減少額が前期の残高と一致 | 13 |
| B 別の要素の前期の値との偶然一致 | 1 |
| C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | 11 |
| D 両期が同額で当期の fact に結び直った | 10 |
| E 増減額の導出(当期 − 前期)に結び直った | 1 |

| doc | id | P21 → P22 | P21 の群 | 型(人の読み) | 文の抜粋 |
|---|---|---|---|---|---|
| S100YUHC | N076 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | これは主に短期借入金が2億円減少したものの、買掛 |
| S100YUHC | N104 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | これは主に、短期借入金の減少額2億円、長期借入金の返済に |
| S100YXGH | N040 | GROUNDED → GROUNDED | Prior1Year・手がかり無し | D 両期が同額で当期の fact に結び直った | これは主に、長期借入れによる収入30,000千円があったものの、長期 |
| S100YYRV | N071 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | 主な要因は、弔慰金が5,000千円増加し、為替差損が12,667千円減少 |
| S100YYRV | N072 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | 投資有価証券売却益が14,457千円減少しております。 |
| S100YYRV | N076 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | 要因は投資有価証券評価損が21,598千円増加し、減損損失が18,146 |
| S100YYS4 | N008 | GROUNDED → VALUE_MISMATCH | Prior1Year・手がかりあり | C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | 、親会社株主に帰属する当期純利益は137,498千円(前年は68,147 |
| S100YYS4 | N057 | GROUNDED → VALUE_MISMATCH | Prior1Year・手がかりあり | C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | 、親会社株主に帰属する当期純利益は137,498千円(前年は68,147 |
| S100YYVN | N010 | GROUNDED → VALUE_MISMATCH | Prior1Year・手がかりあり | C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | 期純損失3億40百万円(前期 親会社株主に帰属する当期純利益6億69百万 |
| S100YYVN | N029 | GROUNDED → VALUE_MISMATCH | Prior1Year・手がかりあり | C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | どが奏功し、セグメント利益は54百万円(前期 セグメント損失1億24百万 |
| S100YYVN | N057 | GROUNDED → VALUE_MISMATCH | Prior1Year・手がかりあり | C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | 円悪化し3億40百万円(前期 親会社株主に帰属する当期純利益6億69百万 |
| S100YZ31 | N031 | GROUNDED → GROUNDED | Prior1Year・手がかり無し | D 両期が同額で当期の fact に結び直った | 資産の取得による支出77百万円、無形固定資産の取得による支出34百万円が |
| S100YZ4E | N021 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | 増加した一方で、現金及び預金が281,806千円、有価証券が205,67 |
| S100YZ7E | N028 | GROUNDED → GROUNDED | Prior1Year・手がかり無し | D 両期が同額で当期の fact に結び直った | 用益の合計3,105百万円、ならびにテナントからの受取賃貸料106百万円 |
| S100YZ7E | N058 | GROUNDED → GROUNDED | Prior1Year・手がかり無し | D 両期が同額で当期の fact に結び直った | 証券の償還による収入240百万円、投資不動産の賃貸による収入106百万円 |
| S100Z39P | N038 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | これは、買掛金が291百万円、1年内返済予定の長期借入金が100百万円減 |
| S100Z3CI | N038 | GROUNDED → GROUNDED | Prior1Year・手がかり無し | D 両期が同額で当期の fact に結び直った | 入金の返済による支出△3,400,000千円、配当金の支払額△62,65 |
| S100Z3CO | N043 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | 資産のその他が36,149千円増加した一方で、投資有価証券が152,20 |
| S100Z3HP | N039 | GROUNDED → GROUNDED | Prior1Year・手がかり無し | D 両期が同額で当期の fact に結び直った | これは主に投資不動産の賃貸による収入が1億24百万円となったのに対し、有 |
| S100Z3HP | N044 | GROUNDED → GROUNDED | Prior1Year・手がかり無し | D 両期が同額で当期の fact に結び直った | 主に短期借入金の純減額が3億円、長期借入金の返済による支出が5億99百万 |
| S100Z3JY | N084 | GROUNDED → VALUE_MISMATCH | Prior1Year・手がかりあり | C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | 使用した資金は、139百万円(前連結会計年度に使用した資金は0百万円)と |
| S100Z3LJ | N056 | GROUNDED → GROUNDED | Prior1Year・手がかり無し | D 両期が同額で当期の fact に結び直った | 当事業年度において特別利益は2百万円、特別損失は3百万円 |
| S100Z433 | N009 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | この主たる要因は、短期借入金が55,000千円、契約負債が39,0 |
| S100Z4DE | N030 | GROUNDED → VALUE_MISMATCH | Prior1Year・手がかりあり | C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | ける流動資産の残高は118億93百万円(前連結会計年度末残高78億51百 |
| S100Z4DE | N035 | GROUNDED → VALUE_MISMATCH | Prior1Year・手がかりあり | C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | おける固定資産の残高は99億93百万円(前連結会計年度末残高91億19百 |
| S100Z4DE | N040 | GROUNDED → VALUE_MISMATCH | Prior1Year・手がかりあり | C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | ける流動負債の残高は108億59百万円(前連結会計年度末残高67億78百 |
| S100Z4DE | N045 | GROUNDED → VALUE_MISMATCH | Prior1Year・手がかりあり | C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | における固定負債の残高は51億7百万円(前連結会計年度末残高48億12百 |
| S100Z4DE | N050 | GROUNDED → VALUE_MISMATCH | Prior1Year・手がかりあり | C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | ける純資産の部の残高は59億19百万円(前連結会計年度末残高53億79百 |
| S100Z4J8 | N026 | GROUNDED → GROUNDED | Prior1Year・手がかり無し | E 増減額の導出(当期 − 前期)に結び直った | これは主に買掛金が257百万円、短期借入金が500百万円、未払金が358 |
| S100Z4N9 | N056 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | 一方、主な減少要因は、1年内償還予定の社債の減少300,000千円であり |
| S100Z4PA | N046 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | 内訳は、現金及び預金が298,750千円増加し、営業貸付金が223,89 |
| S100Z4PA | N050 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | その主な内訳は、長期貸付金が58,060千円減少したことによるも |
| S100Z4PA | N083 | GROUNDED → GROUNDED | Prior1Year・手がかり無し | D 両期が同額で当期の fact に結び直った | その内訳は、金融機関からの短期借入金100,000千円及びリース債務8, |
| S100Z4PA | N084 | GROUNDED → VALUE_MISMATCH | Prior1Year・手がかり無し | B 別の要素の前期の値との偶然一致 | は、金融機関からの短期借入金100,000千円及びリース債務8,066千 |
| S100Z5DN | N014 | GROUNDED → POINTER_NOT_FOUND | Prior1Year・手がかり無し | A 減少額が前期の残高と一致 | 20,097千円増加した一方で、1年内返済予定の長期借入金が201,72 |
| S100Z5DN | N081 | GROUNDED → GROUNDED | Prior1Year・手がかり無し | D 両期が同額で当期の fact に結び直った | これは主に支払利息3,825千円、支払保証料4,718千円及び上場関連費 |

## 4. E-3: 名指しの直しの無改変の書類(`naming_fix/p21_2026-10-20.json` の集合)

- **E-3(当たり)**: 名指しの直しの無改変 40 書類(4665 claim、cache に無い書類 0、67 書類の中に入る書類 40)で、動いた行 23(P21 で GROUNDED の行 23 = 離れた 16 + 参照先だけ動いた 7)、新 GROUNDED 0。

E-3 の動いた行は E-2 の動いた行の部分集合で、P21 / P22 の見えが一行ずつ一致する(門が縛る)。新 GROUNDED は無い。『全部 GROUNDED → 非 GROUNDED』は、参照先だけ動いた GROUNDED の行が在るので厳密には当たらないが、封の外れ方(幅の外 / 向きが逆)には当たらない。

## 5. E-4: 段 2 の材料の Core 自身(T6)と α 型

入力 = 段 2 の材料(`fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json`)を、`measure/xbrl_hybrid_s2_2026-10-20.py` の `rebuild` で組み直し、cd8 の材料 script と同じ claim の対の付け方で Core 自身を当て直した。**対照: P21 で当て直すと、Core 自身が段 2 の記録に全行一致する**(違った行は下の文の『対照の違い』)。

- **E-4(当たり)**: 段 2 の材料(192 行・注入 64)で Core 自身の T6 は P22 で 0 / 10 = 0.0%(段 2 の記録は 6 / 10 = 60.0%、P21 の再計算は 6 / 10 = 60.0%)。全注入では P22 で GROUNDED 0 / 64 = 0.0%。Core 自身が動いた行 6(型を問わず)、対照の違い 0。α 型を当てた 128 行を再計算して記録との差 0。
- T6 の Core 自身 P22 の state: POINTER_NOT_FOUND 1・UNVERIFIABLE 1・VALUE_MISMATCH 7・対応なし 1。
- Core 自身が動いた行はすべて T6 で、ほかの型は動いていない(門が縛る数は上の文の『動いた行』)。
- α 型の経路(`verify_external`)は引数に profile が無く、`_direct_value_claim` を呼ばない(構造の事実を記録に残した)。席が参照先を名指した行を `engine_item` で再計算して、記録の state・reason・held・参照先の fact の値と全部一致した。

## 6. E-5: 儀式(同梱の一書類)

- **E-5(外れ)**: 儀式(同梱の 1 書類)で 通した 15 / 240 = 6.2%・止めた 225 / 240 = 93.8%(P21 の再計算 通した 17 / 241 = 7.1%・止めた 224 / 241 = 92.9%、儀式の記録と違った行 0)。動いた行 N125 V2・N199 V2。注入の対象から外れた行 1・対象に増えた行 0・両方に在る行で結果が同じ 238。
- 素の書類(注入なし)の claim 412 の state: P21 {"GROUNDED": 330, "POINTER_NOT_FOUND": 16, "UNVERIFIABLE": 41, "VALUE_MISMATCH": 25}、P22 {"GROUNDED": 329, "POINTER_NOT_FOUND": 16, "UNVERIFIABLE": 41, "VALUE_MISMATCH": 26}。素の書類で動いた claim 4。
- 通した行は P21 の通した行から N125・N199 を除いたもの。N125・N199 は参照先が当期 → 前期へ移っていた注入で、P22 では VALUE_MISMATCH。
- 素の書類で GROUNDED だった一行が P22 で VALUE_MISMATCH になり、「GROUNDED の site だけが注入の対象」の規則で注入の対象から外れた。封の『止めた・他の件は同じ結果』が外れたのはこの分母の移りによる。

## 7. E-6: 動いた GROUNDED の行の型(人の読み)

GROUNDED を離れた 25 行の型: A 13・B 1・C 11。参照先だけ動いた 11 行の型: D 10・E 1。

| 型(人の読み) | 件数 |
|---|---:|
| A 減少額が前期の残高と一致 | 13 |
| B 別の要素の前期の値との偶然一致 | 1 |
| C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外) | 11 |
| D 両期が同額で当期の fact に結び直った | 10 |
| E 増減額の導出(当期 − 前期)に結び直った | 1 |

- **E-6(人の読み)**: A「減少額が前期の残高と一致」の率は分母の選び方で変わる。GROUNDED を離れた行 25 を分母にすると 13 / 25 = 52.0%、動いた GROUNDED の行 36 を分母にすると 13 / 36 = 36.1%、動いた全 state の行 36 を分母にすると 13 / 36 = 36.1%。封の予測『過半』は『動いた無改変の行(E-2 の幅の GROUNDED を離れた行)』の読みでは 届いた、ほかの分母では 届かない。
- 機械の印(span 前後に『減少』『減』): 離れた 25 行のうち 13、A の 13 行と一致 = はい。
- **判定が分母の選び方に依る**。封は『動いた無改変の行(E-2 の幅の行)を一件ずつ読むと、過半は A』と書いた。E-2 の幅は『GROUNDED を離れた行』を数えた幅なので、その読みでは過半に届くが、動いた GROUNDED の行や動いた全 state の行を分母にすれば届かない。ぎりぎりの当たりで、分母を変えれば外れる。
- A の例: `短期借入金が2億円減少したものの`(S100YUHC N076。前期残高が文の数と偶然一致し、当期は fact 無し)。文は当期の文として正しい数だが、P21 は前期の fact で GROUNDED にしていた。P22 は『前期の fact に結ばない』ので保留(POINTER_NOT_FOUND `no_element`)にする = **正しい文を保留に落とす代価**。
- C の例: `前年は68,147千円の…当期純損失`・`前期 …当期純利益6億69百万円`・`前連結会計年度末残高78億51百万円`。**前期の値を正しく言う文を、P21 は前期の fact に正しく結んでいたが、P22 は当期の fact を名指して VALUE_MISMATCH にする**。保留でなく不一致に落ちる分だけ、A より代価が重い(誤警報)。
- B の例: S100Z4PA N084 `リース債務8,066千円(1年内返済予定のリース債務を含む)`。P21 は別の要素(`LeaseObligationsNCL` の前期)に結んでいた = 偶然一致。P22 は VALUE_MISMATCH(当期の `LeaseObligationsCL` を名指す)。
- D・E(GROUNDED のまま参照先だけ動いた行): 両期が同額の項目(賃貸収入・短期借入金など)は P21 では先頭の Prior1Year に結ばれていたが、P22 は当期に結ぶ。E は `短期借入金が500百万円増加` が当期 − 前期の導出に結び直った。これらは P21 の結びが当期でなかっただけで、GROUNDED は保たれている(改善)。

## 8. E-7: engine の差分と既存試験

- **E-7(外れ)**: engine の差分は `adapters/xbrl/recipes.py` 挿入 4・削除 0、`adapters/xbrl/vocabulary.py` 挿入 4・削除 1、`core/` 0 行。 既存試験(封の 3 か所を直した後): `python3 -m pytest -q tests/adapters/xbrl` → 827 passed, 1 skipped in 1101.00s (0:18:21)。封の 3 か所のほかに直した既存試験: 1 件。
- 封は既存試験の直しを三か所(`test_vocabulary.py` の一覧二か所・`test_p20.py` の除外一か所)と書いた。**四か所目**として `tests/adapters/xbrl/test_recipes_p21.py::FlagShapeTest::test_only_p21_has_the_flag_on` が要った(`P22 = replace(P21, …)` が P21 の旗 `last_branch_cues` を引き継ぐので、旗の一覧が `["P21", "P22"]` になる)。実装席は指定外の file として最初は直さず、司令塔の判断で期待を一行直した(登録の一覧の試験で、P16/P20/P21 の数の試験ではない)。予測『全部緑のまま』は『封の三か所を直した後の緑』なので、四か所目が要ったことは**予測の外れ**として E-7 を外れのまま残す。
- 上の既存試験の結果は、四か所目を直した後の全体の走りで、緑。

## 9. 代価の要約(段 2 を諮るための数)

- P21 で GROUNDED の 4267 行のうち **GROUNDED を離れたのは 25 行 = 0.6%**(A 13・B 1・C 11)。参照先だけ動いた 11 行は GROUNDED のまま。
- 当期の文として正しい数を落とす行は A + C = 24 行 = 0.6%(A は保留へ、C は不一致へ)。B は怪しかった GROUNDED を止めた行。
- 封 §0 の見積もり(手がかり無し 26 行 = 0.6%)に対し、実測で手がかり無しの群から GROUNDED を離れたのは 14 行。見積もりに無かった C は手がかりありの 190 行のうち 11 行(5.8%)。
- 見返り: 穴 B の金額で前期へ移って通した件数 458 → 0。段 2 の Core 自身 T6 の GROUNDED 6 → 0。儀式で参照先が前期へ移って通した N125・N199 は VALUE_MISMATCH。

## 10. 変異と pin の遷移

### 10-1. engine への変異(手で走らせた。予測は走らせる前に固定し、一つずつ `cp` で戻して sha256 の一致を確かめた)

一回限りの手の実測で、門が毎回再現するものではない(記録に写しを残し、文書の表を記録に縛った)。

| # | 変異 | 予測(赤の本数) | 実測(26 本版) | 判定 | 実測(27 本版・参考) |
|---|---|---|---|---|---|
| M-1 | `vocabulary.py`: `P22 = replace(P21, …, period_bind=True)` の True を False に(旗を恒等) | 7〜9 本 | 9 本 | 当たり | 10 本(予測の幅の外 = 外れ側) |
| M-2 | `recipes.py`: 新しい行から `and not _prior_cue_clause(s, a)` を落とす | ちょうど 1 本(`test_cue_in_the_same_clause`) | 1 本 | 当たり | 1 本 |
| M-3 | `recipes.py`: 新しい行から `not _prior_cue(s, a, b) and` を落とす | ちょうど 1 本(`test_paren_dou_cue`) | 1 本 | 当たり | 1 本 |
| M-4 | `recipes.py`: 外す向きを反転(Prior1Year だけ残す) | 8 本以上 | 9 本 | 当たり | 10 本 |
| M-5 | `recipes.py`: 外す相手を Prior2Year に | 7〜9 本 | 8 本 | 当たり | 9 本 |
| M-6 | `vocabulary.py`: `DEFAULT_PROFILE = "P22"` | ちょうど 1 本(既定は P21 のままの試験) | 1 本 | 当たり | 1 本 |
| M-8 | `recipes.py`: 新しい条件から `subj and` を落とす | ちょうど 1 本(主語なしの reason・state が P21 と同一の試験) | 1 本 | 当たり | 1 本 |
| M-9 | `recipes.py`: `startswith("Prior1Year")` を `startswith("Prior")` に(前々期も外す) | ちょうど 2 本(`PriorTwoYearsTest`) | 2 本 | 当たり | 2 本 |
| M-7 | `vocabulary.py`: `period_bind: bool = False` を True に(既定で旗が真) | 6〜9 本 | 7 本 | 当たり | 8 本 |

一回限りの手の実測(`mutate.py`。予測は走らせる前に固定した)。第 1 版の予測では M-7 を 3〜5 本と見積もり実測 7 本で外れた(旗が既定で真になると P21 以前を引く側の標本も赤になるのを数え漏らした)ので、第 2 版(独立監査の後)は 6〜9 本に広げて予測した。M-8・M-9 は第 2 版で足した変異。『最終版・参考』は、挙動の試験(`CommaAfterPriorYearPhraseTest`)を足した後に同じ変異を再走させた値で、予測の幅は 26 本版のもの(M-1 は 10 本で幅の外)。各変異のあとに `cp` で戻し、recipes.py・vocabulary.py の sha256 が変異の前と一致した。第 1 版(22 本)の表は記録に残していない(M-1 8 本・M-4 8 本・M-5 6 本・M-7 7 本で M-7 だけ外れ)。

### 10-2. 門への変異(`tests/measure/test_xbrl_period_bind_result.py` の `MutationTest`。毎回走る)

m1 E-1 の P22 の一行を GROUNDED に書き換える・m2 E-2 の動いた行を一行落とす・m3 判定の語を入れ替える・m4 文書の E-1 の表の数を変える・m4b 文書の E-2 の表の向きを変える・m5 E-2 の行の群を付け替える・m6 P22 で新 GROUNDED の行を作る・m7 人の読み(`READ`)を一行抜く・m8 **engine の旗 `period_bind` を恒等(偽)にして E-1 を再計算する**(軽い走らせ直しと同じ道。通した数が増えて記録と食い違う)・m9 入力の sha256 を壊す・m10 追記を壊す・m11 文書の散文の数を変える・m12 散文に記録に無い数を足す・m13 結論の散文の数を変える。どれも赤になる。

### 10-3. pin の遷移の宣言(封 §1 の一覧 + 封の一覧に無かった二本)

測った当時の sha は消さず、遷移の値(この封が履歴に在るときだけ受け入れる)を足した。

- 測った時点の engine: `recipes.py` sha16 `65a37869f053a60e`・`vocabulary.py` sha16 `1fdb48e7e3ba58ce`。
- 独立監査の後に recipes.py の sha16 が変わった(足す前の中間値は commit していない)。vocabulary.py は変わっていない。
- `ENGINE_LATER`: `test_xbrl_branch_a.py`(recipes・vocabulary)・`test_xbrl_role_swap_result.py`(recipes)・`test_xbrl_axis3_decision.py`(vocabulary)・`test_xbrl_p20_result.py`(recipes・vocabulary)・`test_xbrl_a_core_vs_grep_seal.py`(vocabulary)・`test_xbrl_pnf_diag.py`(recipes・vocabulary)。
- `FROZEN_LATER`: `test_xbrl_cd_seal.py`(vocabulary)。
- `fixtures/frozen_bundle_sha.py`: 新しい世代を足した(対象の本数は変わらない)。
- 封の門 `test_xbrl_period_bind_seal.py`: `ENGINE_LATER` に二 file を宣言。`test_13` を『P22 は PROFILES に在り旗 `period_bind` が真(P22 だけ)、`DEFAULT_PROFILE` は P21 のまま』に直した。測った当時の値(`ENGINE_AT_SEAL`)は残した。
- **封の一覧に無かった二本**: `test_xbrl_point_prior_result.py` の `engine_untouched()` と `test_xbrl_ritual_result.py` の R-8 は、『封の commit から engine が零行』を生の `git diff` で数えていて、sha16 の表を持たない型だった。同じ型の『宣言された遷移』(動いた file が recipes.py・vocabulary.py の二つだけ、封が履歴に在る、sha16 が宣言どおり)を足した。測った当時の事実は消していない。
- **axis3 の `LATER_ENGINE_COMMITS` は commit 後でないと sha が分からないので、次の便で宣言する**。いま(commit 前)は遷移の試験は緑で、**commit した瞬間に赤になる**(宣言が無いため)。名指しの直し 段 1 と同じ扱い。

## 11. 限界

- 手元の cache の書類(無作為でない)と、その部分集合での数。別の書類では動く行が増減しうる(封 §3)。
- E-1 の注入は『前期の値がそのまま書かれる』誤りだけで、構造上すべて手がかり無しの文。**手がかりを付けた文は測れていない**。作れなかった注入(穴 B の記録に件数)は測っていない。千円の提出者に寄る。
- **前々期(Prior2Year)の値への置き換えは P22 でも通る**(P22 が外すのは Prior1Year だけ。未測定。挙動の試験は `test_recipes_p22.py`)。
- **今回の直しは §1b の止めへ新しい行を送る**: `前連結会計年度は、9,709千円`(語と数の間に読点)は手がかりの規則の外で、P21 では前期の fact に GROUNDED、P22 では前期の fact を外して §1b の止め `no_element(no prior2 for prior-year diff)` に落ちる(独立監査が合成で確認、挙動の試験は `test_recipes_p22.py`)。実書類での件数は未測定。
- 型の読み(A〜E)は一件ずつ文脈を読んだ人の読みで、取り違えがありうる。機械の印は span 前後の『減少』『減』の字だけ。
- E-6 の『過半』は分母の選び方に依る(§7)。
- C は『前期の語は在るが engine の字の規則の外』の形。字の一覧を広げる直しはこの封の外(封 §3)。広げた場合の効果は測っていない。
- E-4 の Core 自身は材料 script と同じ対の付け方の再現(対照 P21 で記録に全行一致)。α 型は profile を取らない経路で、P22 では動かないことを再計算した。
- E-8(段 2)は判定していない。既定は P21 のまま(`DEFAULT_PROFILE`)。
- 縛っていないもの(門の docstring にも書いた): 型の読みの正しさ・A の例などの引用文・限界の文・変異の手の実測そのもの(表は記録の写しを縛る)。

## 12. 再現

```
cd audit-core
python3 measure/xbrl_period_bind_2026-10-20.py --stage all                      # 記録を書く(測定は数分 + 既存試験は数十分)
python3 measure/xbrl_period_bind_2026-10-20.py --stage e1 --docs S100YMFV --out <file>    # 軽い走らせ直し
python3 -m pytest -q tests/measure/test_xbrl_period_bind_result.py              # 門(既定は軽い走らせ直しまで)
AUDIT_CORE_PERIOD_BIND=1 python3 -m pytest -q tests/measure/test_xbrl_period_bind_result.py   # 全部の走らせ直し
```

記録の所要秒: {"E1": 178.2, "E2": 64.3, "E3": 38.9, "E4": 11.2, "E5": 48.3, "E7": 1101.3, "全体": 1451.1}。

## 13. 追記(2026-10-20、司令塔の判断の後)

- 四か所目の直し: tests/adapters/xbrl/test_recipes_p21.py::FlagShapeTest::test_only_p21_has_the_flag_on の期待を ["P21"] から ["P21", "P22"] に一行直した(P22 = P21 + period_bind は last_branch_cues を引き継ぐ。封 XBRL_PERIOD_BIND_SEAL_2026-10-20 の追記)
- E-7 の判定: 外れ(封は既存試験の直しを三か所と書き、四か所目が要った = 予測の外れ。四か所目を直した後の tests/adapters/xbrl 全体の結果は E7 欄)

- 四か所目の file は、封の三か所と同じ『登録の一覧の試験』で、P16/P20/P21 の数の試験ではない。
- **E-7 は外れのまま残す**(予測は封の三か所を直した後の緑、四か所目が要った = 予測の外れ)。
- 封の末尾に、日付つきの追記を足した(本文 §0〜§4 と予測は一字も変えていない。内容: 既存試験の直しは四か所・封の pin 一覧に無かった二本の宣言・E-2 の外れの意味・独立監査の指摘と主語なしの扱い)。門は封の commit の本文が先頭に残っていることを縛る。

## 14. 段 2(2026-10-20、既定 P21 → P22)

人間の承認は 2026-10-20「任せる」(段 1 `3320c8c` の結果と、客の席 A の回し直し(誤り五件中五件を止め、正しい三十九行の空振りは零。開発側でない客の席の日記。repo の外 = scratchpad、記録なし。司令塔が読んで諮った数)を見てから)。封 `docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md` の E-8 と §4 の段 2。この節は段 1 の本文(§0〜§13)を 一字も直さない追記で、予測 E-1〜E-7 の判定も直していない。

### 14-1. 既定の字と engine の差分

- `adapters/xbrl/vocabulary.py` の `DEFAULT_PROFILE = "P22"`。字の決定の注記を日付つきで足した(P21 の注記・P20 の注記・P16 の注記は消していない)。
- engine の差分はこれだけ: `recipes.py` は段 1 の値のまま、`core/` は零行。`vocabulary.py` の sha16 は段 1 の `1fdb48e7e3ba58ce` から `25a3c0992e10daaa` へ(宣言された遷移。段 1 の値は測った当時の値として門に残る)。
- P21 の字は消していない。P16・P20・P21 を明示した呼び出しと、それを明示した既存試験の数は一つも変えていない。

### 14-2. 動かした試験と測定の一覧

既定の字を見ていた試験(『既定は P22』に直した):

- `tests/adapters/xbrl/test_p17.py`・`test_p20.py`・`test_recipes_p21.py`・`test_recipes_p22.py`・`test_run.py`
- `tests/adapters/xbrl/test_verify_entry.py`: 既定で P21 の数を見ていた四つの試験(未使用二書類の P16 の記録との差・十四書類の止めた件数・二書類の書類ごとの旗・出力の sha256)は、P21 を明示した試験に名前を変えて数を一つも変えずに残し、既定(P22)の試験を足した。既定の P22 は未使用二書類の P16 の記録の中で P21 の五行のほかに一行(`H-042`)の GROUNDED を離れ、十四書類のうち五書類の止めた件数が増える(型 A の行。数は試験の中に字で留めた)。
- `tests/measure/test_xbrl_branch_a.py`(Core の既定の事実)・`test_xbrl_naming_fix_result.py`(名指しの直し 段 2 の注記の門)・`test_xbrl_period_bind_seal.py`(封の門)・`test_xbrl_period_bind_result.py`(この節の門)

既定で測った記録を持つ measure と門(測った当時の P21 を明示して字で留めた。記録は一字も変えていない):

- `measure/xbrl_point_prior_2026-10-20.py`・`measure/xbrl_hybrid_s2_2026-10-20.py`・`measure/xbrl_hybrid_trust_2026-10-20.py`(定数 `PROFILE_AT_MEASURE`)
- `tests/measure/test_xbrl_ritual_seal.py`(封 §0-1 の数は P21 の数)・`tests/measure/test_xbrl_point_prior_seal.py`・`tests/measure/test_xbrl_period_bind_seal.py` の実走の門
- 段 1 の測定 `measure/xbrl_period_bind_2026-10-20.py` は P21・P22 を明示して比べるので既定がどちらでも同じ数が出る。儀式の対照だけ、P22 で採り直した `ritual_2026-10-20.json` ではなく、同じバイト列の写し `fixtures/xbrl/ritual_2026-10-20_p21.json` を読む。
- 儀式は買い手が今の既定で走らせるもの: `measure/ritual_2026-10-20.py` の guard を『既定は P22』に直し、記録・README・結果文書の追記を P22 で採り直した(`docs/XBRL_RITUAL_RESULT_2026-10-20.md` の追記)。

pin の遷移の宣言(`vocabulary.py` の新しい sha16 を、この封を根拠に): `test_xbrl_a_core_vs_grep_seal.py`・`test_xbrl_axis3_decision.py`・`test_xbrl_branch_a.py`・`test_xbrl_cd_seal.py`(`FROZEN_LATER`)・`test_xbrl_p20_result.py`・`test_xbrl_pnf_diag.py`・`test_xbrl_point_prior_result.py`・`test_xbrl_ritual_result.py`・`test_xbrl_period_bind_seal.py`(封の門 `test_12`)・この節の門(`ENGINE_LATER`)と、`fixtures/frozen_bundle_sha.py` の新しい世代。**この世代の宣言は、これまでどの門も作業木の束ねた sha と突き合わせていなかった**(変異で新しい世代を消しても全部緑だった = 世代を足し忘れても黙る)ので、この節の門に `test_16`(最新の世代 = いまの作業木の束ねた sha、説明が段 2 の宣言)を足した。**`test_xbrl_axis3_decision.py` の `LATER_ENGINE_COMMITS` は commit の sha が要るので次の便で宣言する**(commit した瞬間に `test_9` が赤になる。名指しの直し 段 2 と同じ扱い)。

### 14-3. 製品の経路(profile 省略)で測り直した数

- **E-1(profile 省略)**: 穴 B の注入 485 件を、profile を省いた `verify_document`(= 既定)で検証し直すと、通した(GROUNDED のまま)は 1 / 485 = 0.2%・止めた(VALUE_MISMATCH)は 482 / 485 = 99.4%・その他は 2 / 485 = 0.4%。段 1 の P22 の欄と 1 行ずつ比べて違った行 0、記録に無い行 0。
- **E-2(profile 省略)**: 経営分析の文を持つ 67 書類(7799 claim)の無改変を P21 と既定で比べると、動いた行は 36(GROUNDED を離れた 25・新 GROUNDED 0)。段 1 の記録の動いた行 36 と過不足なく同じで、P21・P22 の欄が違った行 0、記録に無い動いた行 0。
- **E-5(儀式、既定)**: 通した 15 / 240 = 6.2%・止めた 225 / 240 = 93.8%。P21 の記録に段 1 の動いた行・外れた行を当てて作った期待 240 行と 1 行ずつ比べて違った行 0、採り直した儀式の記録と違う欄 0。素の書類 412 claim のうち、既定と P22 明示で違った claim 0。素の書類の state(既定): {"GROUNDED": 329, "POINTER_NOT_FOUND": 16, "UNVERIFIABLE": 41, "VALUE_MISMATCH": 26}。
- 差のあった行の合計 0(差 0 の行: E-1 485・E-2 36・E-5 240)。
- 『差 0』が自分の欠陥でないことの対照: `vocabulary.DEFAULT_PROFILE` を実行中だけ P21 に戻して S100YMFV の注入 4 件を同じ比較器に当てると、段 1 の P22 の欄と違った行は 2。
- 比較は段 1 の記録の P22 の欄(E-1)・動いた行の P21・P22 の欄(E-2)・P21 の儀式の記録に段 1 の E-5 の動いた行・外れた行を当てた期待(E-5)に対して一行ずつ。『差が零』は先に自分の欠陥を疑い、上の対照(既定を P21 に戻す変異)で比較器が差を拾えることを確かめた。
- 既存試験 `python3 -m pytest -q tests/adapters/xbrl` → rc 0・831 passed, 1 skipped in 1118.43s (0:18:38)。

### 14-4. 儀式の P21 → P22

- 儀式(同梱の 1 書類)の記録: P21 のとき 通した 17 / 241 = 7.1%・止めた 224 / 241 = 92.9% → P22(既定)で 通した 15 / 240 = 6.2%・止めた 225 / 240 = 93.8%。注入の対象 241 → 240。素の書類の GROUNDED 330 → 329・VALUE_MISMATCH 25 → 26。
- 結果文書 `docs/XBRL_RITUAL_RESULT_2026-10-20.md` の本文は P21 のときの数のまま、末尾に日付つきの追記を足した。README の数は P22 の記録と一対一(P21 の数は一行、日付つきで残した)。

### 14-5. 代価(製品の経路で再掲)

- 代価(製品の経路で再掲): P21 で GROUNDED の 4267 行のうち GROUNDED を離れたのは 25 行(A 13・B 1・C 11)。C は正しい前期の文が不一致になる行(下の表)。参照先だけ動いた 11 行(D 10・E 1)は GROUNDED のまま。

| doc | id | P21 → P22 | 文の抜粋 |
|---|---|---|---|
| S100YYS4 | N008 | GROUNDED → VALUE_MISMATCH | 、親会社株主に帰属する当期純利益は137,498千円(前年は68,147 |
| S100YYS4 | N057 | GROUNDED → VALUE_MISMATCH | 、親会社株主に帰属する当期純利益は137,498千円(前年は68,147 |
| S100YYVN | N010 | GROUNDED → VALUE_MISMATCH | 期純損失3億40百万円(前期 親会社株主に帰属する当期純利益6億69百万 |
| S100YYVN | N029 | GROUNDED → VALUE_MISMATCH | どが奏功し、セグメント利益は54百万円(前期 セグメント損失1億24百万 |
| S100YYVN | N057 | GROUNDED → VALUE_MISMATCH | 円悪化し3億40百万円(前期 親会社株主に帰属する当期純利益6億69百万 |
| S100Z3JY | N084 | GROUNDED → VALUE_MISMATCH | 使用した資金は、139百万円(前連結会計年度に使用した資金は0百万円)と |
| S100Z4DE | N030 | GROUNDED → VALUE_MISMATCH | ける流動資産の残高は118億93百万円(前連結会計年度末残高78億51百 |
| S100Z4DE | N035 | GROUNDED → VALUE_MISMATCH | おける固定資産の残高は99億93百万円(前連結会計年度末残高91億19百 |
| S100Z4DE | N040 | GROUNDED → VALUE_MISMATCH | ける流動負債の残高は108億59百万円(前連結会計年度末残高67億78百 |
| S100Z4DE | N045 | GROUNDED → VALUE_MISMATCH | における固定負債の残高は51億7百万円(前連結会計年度末残高48億12百 |
| S100Z4DE | N050 | GROUNDED → VALUE_MISMATCH | ける純資産の部の残高は59億19百万円(前連結会計年度末残高53億79百 |

- 上の行は段 1 §3-1 の動いた行の C と同じ(製品の経路で一行ずつ一致を確かめた)。正しい前期の文を『不一致』と言う副作用は、既定にした以上、製品の経路に出る。手がかりの字の規則を広げる直しは別の封(封 §3)。

### 14-6. E-8 の判定と限界

- **E-8 の判定**: E-8 の条件(E-1〜E-7 が当たる)は満たされていない(当たり 3 / 外れ 3)。人間の承認(2026-10-20「任せる」)で段 2 に進んだ。全緑の部分だけ成立(tests/measure・tests/adapters/xbrl 緑。axis3 の LATER_ENGINE_COMMITS は commit の直後に赤 1 本 → 次の便で宣言、段 1 と同じ扱い)。記録の 予測の判定.E-8 は『判定しない(段 2)』のまま。
- `tests/measure` の本数と秒は commit の説明に書く(門の本数は門自身の中に入るので記録に取らない)。
- 限界(段 1 から変わらない): 手元の cache の書類(無作為でない)での数。前々期の値への置き換えは P22 でも通る。主語の無い数は案ア(2026-10-08)のまま P21 と同一。手がかりの字の規則の外の正しい前期の文は不一致になる。『ポイント』の穴 A は直していない。
- `adapters/xbrl/verify_document.py` の docstring『既定 P20』は engine の file なので触っていない。HUMAN の残り一点(承認待ち)。
