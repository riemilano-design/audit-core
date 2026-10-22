# 診断 ― `POINTER_NOT_FOUND` の 10 行で Core は**どの key も試していなかった**

2026-10-17。人間の指示(α より先に診断)の 1 番。
**Core の関数・正規化・探索挙動は 1 行も変えていない。費用 0 USD・席は呼んでいない。**

正本は `fixtures/xbrl/cd8/pnf_diag_2026-10-17.json`
(作ったのは `measure/xbrl_pnf_diag_2026-10-17.py`)。**この文の数はそこから引いている。**

---

## §1 既存の記録では足りなかった(先に確かめた)

`material_2026-10-17.json` が持つのは `verify_document` の **結果の** 参照先である。
`POINTER_NOT_FOUND` では結果が空なので、**試した key は記録に無い。**
だから**診断用の記録だけを足した**(engine には触っていない)。

**配線が Core と同じことを門で示した。**`verify_document` と同じ呼び出し・同じ順で
recipe を組み、`core.verify_all` の state と pointers が
**2 書類の全主張(89 件・80 件)で `verify_document` の出力と一致**した。
一致しなければ止める ― 私の配線が Core と違うなら、観測は Core の観測ではない。
材料も封の記録と **sha256 が一致**している。

---

## §2 観測(**機械が出した数だけ**)

| 書類 | 行 | Core が決めた subject | その subject に当たった要素 | 試した key | 正解の要素 | 正解の要素に次元なしの context |
|---|---|---|---|---|---|---|
| `S100YZ7E` | R017 | 営業収益 | `OperatingRevenue`, `NetSales`, `Revenue` | **0 本** | `operatingrevenue2summaryofbusinessresults` | **無い** |
| `S100YZ7E` | R018 | 営業収益 | `OperatingRevenue`, `NetSales`, `Revenue` | **0 本** | `ordinaryincomelosssummaryofbusinessresults` | **無い** |
| `S100YZ7E` | R019 | 営業収益 | `OperatingRevenue`, `NetSales`, `Revenue` | **0 本** | `cashandcashequivalentssummaryofbusinessresults` | **無い** |
| `S100YZ7E` | R020 | 営業収益 | `OperatingRevenue`, `NetSales`, `Revenue` | **0 本** | `netcashprovidedbyusedininvestingactivitiessummaryofbusinessresults` | **無い** |
| `S100YZ7E` | R023 | 資産合計 | `Assets`, `TotalAssets` | **0 本** | `totalassetssummaryofbusinessresults` | **無い** |
| `S100YZ7E` | R024 | 純資産合計 | `NetAssets` | **0 本** | `netassetssummaryofbusinessresults` | **無い** |
| `S100YZEV` | R011 | 営業利益 | `OperatingIncome`, `OperatingProfit` | **0 本** | `operatingincome` | **無い** |
| `S100YZEV` | R018 | 流動資産 | `CurrentAssets` | **0 本** | `currentassets` | **無い** |
| `S100YZEV` | R019 | 固定資産 | `NoncurrentAssets` | **0 本** | `noncurrentassets` | **無い** |
| `S100YZEV` | R020 | 営業利益 | `OperatingIncome`, `OperatingProfit` | **0 本** | `increasedecreaseinaccountspayableotheropecf` | **無い** |

**10 行すべてで、試した key は 0 本である。**`reason` はすべて `no_element`、
`state` は `POINTER_NOT_FOUND`。**結果の参照先も 0 本。**

| | |
|---|---|
| 正解の `(要素名, context)` が instance に在った行 | **10 / 10** |
| 正解の要素名に**次元なしの context が在った**行 | **10 / 10** |
| 正解の要素が Core の語彙のどこかに在った行 | **9 / 10** |
| subject に当たった要素に正解が無かった行 | **7** |
| 語彙も subject も正解の要素を持っていたのに key が 0 本だった行 | **3** |

書類の側の数。

| 書類 | 主張 | fact | **次元つきの context を持つ fact** | 語彙の行(うちラベル由来) |
|---|---|---|---|---|
| `S100YZ7E` | 89 | 502 | **497** | 170(89) |
| `S100YZEV` | 80 | 397 | **385** | 190(109) |

---

## §3 判定(**観測から機械的に言えること**)

1. **照合・正規化の問題ではない。**key を 1 本も作っていないので、
   解決器(`make_resolver`)も値の比較も**一度も呼ばれていない。**
2. **Core は正解の fact を読み込んでいる。**10 / 10 行で
   正解の `(要素名, context)` が instance に在った。**見えていないのではない。**
3. **正解の fact は、どの行でも次元つきの context にしか無い**
   (`NonConsolidatedMember`。10 / 10 行で「次元なしの context は無い」)。
4. **落ちた場所は 2 つに分かれる。**
   **3 行**は語彙も subject も正解の要素名そのものを持っていた
   (`CurrentAssets`・`NoncurrentAssets`・`OperatingIncome`)。
   それでも key が 0 本 ― **要素を選べても key にならなかった。**
   残る **7 行**は、subject に当たった要素の中に正解が無い
   (6 行は `...SummaryOfBusinessResults` 族、1 行は subject の取り違え)。

---

## §4 解釈(**仮説。測るまで断定しない**)

- **仮説 A(次元)**: Core は**次元つきの context を使う key を作らない**。
  §3 の 4 番の 3 行は、これだけで説明が付く(要素は選べていた)。
  **これは仮説である。**key を作る分岐のどこで次元が落ちるかは、この記録では見ていない。
- **仮説 B(語彙と主語)**: `...SummaryOfBusinessResults` 族(主要な経営指標等の推移)が
  subject の候補に入っておらず、同じ文に複数の数が並ぶ行では subject を取り違える。
  **7 行はこちらが先に効いている**ので、仮説 A を直しても動かない可能性が高い。
- **2 つは別の直しである。**片方を直して「10 行が直る」と書いてはいけない。

---

## §5 言えないこと

1. **10 行・2 書類の観測である。**Core 全体の振る舞いを断定しない。
2. **原因の特定ではなく、落ちた場所の特定である。**なぜ次元つきの key を作らないかは
   コードの分岐を読んでいない(次の便)。
3. **直していない。**この記録は観測であり、改善の提案ではない。
4. **他の 6 書類では起きていない。**書類差と注入箇所の差は分けていない。
5. **正規化は両側に同じ関数を掛けた。**一度これを片側だけに掛けて
   「正解の要素名が instance に無い」という**誤った記録を作り、作り直した**
   (記憶 `normalize-both-sides-of-a-comparison`)。**この記録は掛け直した後の 1 本である。**
6. **`word` ではなく `subject` で語彙を引いた。**最初は `word` で引いて
   「語が取れていない」と誤って分類した。**数の主張では `word` は `None` である。**

---

## §6 次に測ること(**改善の前に書く**)

1. 仮説 A の場所を特定する ― 次元つきの context が key になる分岐が在るか、
   在るなら何で落ちるか。**コードを読んで、落ちる入力を 1 つ作る。**
2. 仮説 B は別便にする ― `...SummaryOfBusinessResults` 族を subject の候補に入れるのは
   **語彙(判断的知識)の変更**であり、独立監査の GO が要る。
3. **どちらも直す前に、直したら何が動くはずかを数で書く**
   (この 10 行のうち何行・他の 6 書類で何行変わらないはず)。
4. **α はこの後である。**Core が key を作れない行では、α は測る前から 0 である。
