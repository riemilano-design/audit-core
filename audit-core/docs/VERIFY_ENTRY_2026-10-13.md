# 稼働の入口(1 書類を検証して Claim ごとの state・pointer・reason を返す)

作成: 2026-10-13。人間の決定(第 3 段階)「まず内部道具として、入力から判定までを一貫して動かす入口を 1 本作る。顧客向けの形・P17・規則の追加はやらない」。

## 0. なぜ要ったか

main には、**文と XBRL を入れて 4 状態と pointer を返す本番の入口が無かった。** `adapters/xbrl/run.py` は Claim の層(結果なし)を書くだけで、判定まで回す経路は試験の補助(`tests/golden/_instrument.py`)と日付つきの測定道具にしかなかった。P16 は測定の中では動いていたが、「システムとして稼働」には入口が欠けていた。

## 1. 何を作ったか

| file | 中身 |
|---|---|
| `adapters/xbrl/verify_document.py` | 入口。`load_instance → make_resolver → register_all → build_recipes → verify_all` を**試験の補助と同じ順**で呼ぶ。足したのは書類レベルの旗 1 つだけ |
| `adapters/xbrl/prose.py` | 経営分析の節を渡された文章で差し替える。日付つき道具 `fixtures/xbrl/ai_prose_claims_2026-10-09.py` の `prose_to_html`・`build_modified_zip` を**中身を変えずに**写した。**変えたのは止め方だけ**(`SystemExit` → `ProseReplacementError`)。日付つき道具は 1 行も触っていない |
| `fixtures/xbrl/build_entry_golden_2026-10-13.py` + `entry_golden_ai_prose_2026-10-13.json` | 入口の期待値。**入口の出力からは作っていない**(`tests/golden/_instrument.run_verification` で作った。入口の出力から作ると同語反復になる) |
| `tests/adapters/xbrl/test_verify_entry.py` | 23 本 |

**新しい判定規則は 1 つも入れていない。** 既定 profile は `vocabulary.DEFAULT_PROFILE`(= P16、第 2 段階で人間が決めた)。

### 1-1 書類レベルの旗(人間が承認した文面そのまま)

> Claim 件数が 0 件の場合、書類レベルを UNVERIFIABLE とする。Claim 件数が 1 件以上の場合、GROUNDED 件数が 0 件、かつ POINTER_NOT_FOUND 件数 ÷ 全 Claim 件数が 0.5 を超える場合、書類レベルを UNVERIFIABLE とする。それ以外は、この規則によって UNVERIFIABLE とは判定しない。Claim 個別の state は変更しない。

`verify_document.DOC_UNVERIFIABLE_RULE` に字で置き、試験が字そのものを留める。分母は**全 Claim 件数**(人間の決定)。

## 2. 完成条件に対する実測 [測定]

| # | 条件 | 実測 |
|---|---|---|
| 1 | 既存の測定との**意味の一致** | 開発書類の AI 文: P7 415 件・P13 412 件・P16 412 件の全行で (state, pointers, reason, subject) が golden と一致。P16 の内訳は記録どおり G 330 / VM 25 / PNF 16 / UV 41。未使用 2 書類: 限定確認の commit 済み dump と、行の鍵 → claim id の対応表を経由して全行一致(103・150 行)。14 書類の止めた件数は §2-3 の表と一致 |
| 2 | **入力**の再現性 | 文章を差し替えた ZIP の sha256 = 封じた値 `03521437…4799`(日付つき道具が作った値) |
| 3 | **出力**の再現性 | 同じ入力を 2 回処理して byte 一致。さらに 1 書類(S100Z4B6)の本体の sha256 を字で留めた(engine の指紋は adapters の .py が変わると動くので除く)。字下げを変える変異で赤くなる |
| 4 | 書類レベルの UNVERIFIABLE | S100Z3HP(PNF 57/62 = 0.92)・S100Z433(77/87 = 0.89)で真、未使用 2 書類と他で偽。ちょうど 0.5 は偽、GROUNDED 1 件で偽、PNF の無い停止では偽 |
| 5 | CLI から実際に JSON が出る | 原文 1 件と AI 文 + ZIP 1 件を回した。出力は §4 |

### 2-1 変異(壊したら赤くなるか)[測定]

| 変異 | 予測 | 実測 |
|---|---|---|
| 閾値 0.5 → 0.9 | 旗の試験が赤 | 3 本赤(規則の字・合成・実書類) |
| Claim 0 件の枝を消す | 1 本赤 | 1 本赤 |
| 差し替え**前**の ZIP で recipes を作る | 意味の一致が赤 | 4 本赤 |
| 出力の字下げを変える | 字で留めた sha が赤 | 1 本赤 |
| 1 行 1 段落をやめる | 差し替えの試験が赤 | 3 本赤(封じた sha を含む) |

恒等(変異なし)と復元後はどちらも 23 本緑。pyc は変異ごとに新しい置き場で測った。

## 3. 使い方

```bash
# 原文の書類(既定 profile = P16)
python3 -m adapters.xbrl.verify_document --doc S100Z4N9 --out out.json
# 書類の ZIP を道で渡す
python3 -m adapters.xbrl.verify_document --zip ~/.cache/audit-core/edinet/S100Z4N9.zip --out out.json
# 文章を渡して経営分析の節を差し替えて検証する
python3 -m adapters.xbrl.verify_document --doc S100Z4Q1 --text fixtures/xbrl/ai_prose_2026-10-09.txt --out out.json
```

出力の頭に tool 名・engine の指紋(adapters/xbrl と Core の .py の sha256。git の commit は取れなければ `null`)・profile・入力の sha256・差し替えた要素名、`document` に件数の内訳と旗と規則の字、`claims` に Claim ごとの 12 欄。

## 4. 実際に回した 2 通り [測定]

| 入力 | Claim | 内訳 | 書類レベル |
|---|---|---|---|
| S100Z4N9(原文) | 186 | G 99 / VM 53 / UV 28 / PNF 6 | 偽 |
| S100Z4Q1 + AI 文(`ai_prose_2026-10-09.txt`) | 412 | G 330 / VM 25 / UV 41 / PNF 16 | 偽 |
| S100Z3HP(原文、参考) | 62 | PNF 57 / UV 5 | **真** |

## 5. していないこと

- 顧客向けの形(PDF・画面・レポートの文)。
- P16 の規則の変更、新しい profile、方向の主張の別扱い、千円のずれの許容。
- 運用の監視(定期に 100 件を抜いてラベルする仕組み)。
- 旗以外の書類レベルの判断。
