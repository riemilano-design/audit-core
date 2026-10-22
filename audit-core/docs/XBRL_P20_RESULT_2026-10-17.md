# P20 の実測 ― **原因仮説 A は支持された。ただし誤認定も予測どおり 7 行増えた**

2026-10-17。封 `docs/XBRL_P20_SEAL_2026-10-17.md`(commit `c3a9e0f`。実測より先)。
**profile を P16 → P20 にしただけ。engine のコードは 1 行も変えていない。0 USD・席は呼んでいない。**

正本は `fixtures/xbrl/cd8/p20_rerun_2026-10-17.json` と
`fixtures/xbrl/cd8/p20_pred_recheck_2026-10-17.json`。

---

## §1 判定

**封の 6 欄すべてで、事前に commit した予測(`cf4f5c9`)と実測が一致した。**

| 欄 | 予測 | 実測 | |
|---|---|---|---|
| M-1 10 行の POINTER_NOT_FOUND | 0 | 0 | **当たり** |
| M-2 特定(T5 全部の行) | 18/50 | 18/50 | **当たり** |
| M-2 特定(1 対 1 の行だけ) | 15/26 | 15/26 | **当たり** |
| M-3 名指して正解でない行(P16 より何行増えたか) | 7 行増える | 7 行増えた(25 → 32) | **当たり** |
| M-4 連結ありの 6 書類が不変 | 24 行すべて不変(1 行でも動けば外れ) | {"S100YYRG": 0, "S100YXMA": 0, "S100YWGX": 0, "S100YZCT": 0, "S100YYRV": 0, "S100YXF5": 0} | **当たり** |
| M-5 α の天井 | 0/7(変わらない) | 0/7 | **当たり** |

**当たり 6 / 外れ 0。**主張ごと(10 行)は **照合 1 で 9/10、
照合 2(字で書いた参照先で比べる)で 10/10**(§4 の照合器の欠陥)。

**止める条件(封 §4)はどれも起きていない。**
`P16` の再現は **8 書類 192 行すべてで材料の記録と一致**し、
profile の差は `name` と `nonconsolidated_fallback` の **2 欄だけ**だった。

---

## §2 数(P16 → P20)

| | P16 | **P20** |
|---|---|---|
| 10 行の `POINTER_NOT_FOUND` | 10 | **0** |
| Core 自身の特定(T5 全部の行) | 30.0%(15/50) | **36.0%(18/50)** |
| Core 自身の特定(1 対 1 の行だけ) | 50.0%(13/26) | **57.7%(15/26)** |
| Core が参照先を名指した行(T5) | 40 | **50** |
| **うち正解でなかった行** | 25 | **32** |
| **α の天井**(席が外した 7 行で Core が正解を持つ) | 0/7 | **0/7** |
| 連結ありの 6 書類で動いた主張 | ― | **0 件** |

**特定は 3 行増え、誤認定は 7 行増えた。**名指した行が 10 行増えたうち、
**正解だったのは 3 行**である。**これを「改善」と書かない。**

### §2-2 10 行の中身

| 書類 | 行 | P16 の state | P20 の state | P20 の参照先 | |
|---|---|---|---|---|---|
| `S100YZ7E` | R017 | `POINTER_NOT_FOUND` | VALUE_MISMATCH | `unearnedrevenue@currentyearinstant_nonconsolidatedme` | 正解でない |
| `S100YZ7E` | R018 | `POINTER_NOT_FOUND` | VALUE_MISMATCH | `unearnedrevenue@currentyearinstant_nonconsolidatedme` | 正解でない |
| `S100YZ7E` | R019 | `POINTER_NOT_FOUND` | VALUE_MISMATCH | `unearnedrevenue@currentyearinstant_nonconsolidatedme` | 正解でない |
| `S100YZ7E` | R020 | `POINTER_NOT_FOUND` | VALUE_MISMATCH | `unearnedrevenue@currentyearinstant_nonconsolidatedme` | 正解でない |
| `S100YZ7E` | R023 | `POINTER_NOT_FOUND` | VALUE_MISMATCH | `assets@currentyearinstant_nonconsolidatedmember` | 正解でない |
| `S100YZ7E` | R024 | `POINTER_NOT_FOUND` | VALUE_MISMATCH | `netassets@currentyearinstant_nonconsolidatedmember` | 正解でない |
| `S100YZEV` | R011 | `POINTER_NOT_FOUND` | VALUE_MISMATCH | `operatingincome@currentyearduration_nonconsolidatedm` | **正解** |
| `S100YZEV` | R018 | `POINTER_NOT_FOUND` | VALUE_MISMATCH | `currentassets@currentyearinstant_nonconsolidatedmemb` | **正解** |
| `S100YZEV` | R019 | `POINTER_NOT_FOUND` | VALUE_MISMATCH | `noncurrentassets@currentyearinstant_nonconsolidatedm` | **正解** |
| `S100YZEV` | R020 | `POINTER_NOT_FOUND` | VALUE_MISMATCH | `operatingincome@currentyearduration_nonconsolidatedm` | 正解でない |

`S100YZEV` の 3 行(`N014`・`N017`・`N007` の `R011`)は**正解を名指した。**
`S100YZ7E` の 4 行(`N022`)は **`unearnedrevenue@…` という、P16 では無かった誤った
参照先**を名指した。`R023`・`R024` は素の `assets` / `netassets` を名指した。
**どれも予測どおりである。**

---

## §3 仮説の切り分け

- **仮説 A(次元)は支持された。**`with_nonconsolidated_fallback` を有効にすると、
  **要素を選べていた 3 行は正解に届いた**(`fs` が 0 件でなくなった)。
- **仮説 B(語彙・主語)は残った。**`S100YZ7E` の 7 行は、
  **参照先が出るようになった分だけ誤認定が増えた。**
  subject が `営業収益` 1 つに潰れている行(`N022` に 4 行)は、
  **次元を直しても正解には届かない。**
- **α の天井は 0/7 のまま。**席が外した 7 行で Core が正解を持つ行は、
  **P20 でも 1 行も無い。****製品価値の側は、この設定変更では動かない。**

---

## §4 私の照合器の欠陥(**先の記録は書き換えない**)

主張ごとの照合は、予測の欄が**「正解」で始まるか**だけを見ていた。
`N007` の予測は**参照先を字で書いていた**ので、その字が正解と一致する行(`R011`)まで
「正解ではないと予測した」に分類され、**正しい予測が外れに数えられた。**

| 数え方 | 当たり |
|---|---|
| 照合 1(先の記録。そのまま残す) | **9/10** |
| **照合 2(字で書いた参照先で比べる)** | **10/10** |

**両方を残す。**片方だけ残せば「結果を見て照合器を緩めた」のと同じになる。
**実測の数(M-1〜M-6)は 1 つも変えていない。**変えたのは一致の数え方だけである。

---

## §5 言えないこと

1. **性能の証明ではない**(封 §0)。**特定 +3 と誤認定 +7 を同じ表に並べた。**
2. **A 対 C′(LLM + Core が LLM 単体より正確か)はこの封では測っていない。**
   席の答えは「席が外した行」を数えるためだけに読んだ。**製品価値の実証は別の封。**
3. **fallback の適用条件は変えていない。**変えるかどうかは人間が決める。
4. **器の欠陥は残っている。**行 → 主張 は 1 対 1 でないので、率は 2 つの分母で書いた。
5. **8 書類の標本である。**うち条件を満たすのは 2 書類(単体のみの書類)だけである。
6. **「P20 にすべき」とは書かない。**P20 は既定だが、**この標本では誤認定も増える。**
   既定に戻す/条件を狭める/語彙を直す、のどれが良いかは**測っていない。**

---

## §6 次に人間が決めること

1. **profile をどうするか** ― 既定(P20)に合わせるか、条件を狭めるか。
   **この便の数は「替えると誤認定も増える」ことを示している。**
2. **仮説 B(語彙・主語)を直すか** ― `S100YZ7E` の 7 行はそちらが先に効いている。
   語彙は判断的知識なので独立監査の GO が要る。
3. **製品価値の実証(A 対 C′)をいつやるか** ― α の天井は P20 でも 0/7 なので、
   **先に Core 側の特定を上げないと α は 0 のままである。**
