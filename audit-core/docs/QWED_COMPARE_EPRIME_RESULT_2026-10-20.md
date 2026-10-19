# QWED と同じ材料で測った ― E′(値の字を揃えた)。**同じ 18 行が、換算すれば在り(E′a 18 / 18)、換算しなければ無い(E′b 0 / 18)。T5 はその逆(E′a 0 / 50・E′b 36 / 50)。E′b で QWED が通した注入は 14 / 64、Audit Core は 0 / 64。予測 当たり 6 / 外れ 1**

2026-10-20。封 `docs/QWED_COMPARE_SEAL_2026-10-19.md` の **追記 2**(commit `db8816f`。測定より先)。段 B の結果は `docs/QWED_COMPARE_RESULT_2026-10-19.md`(commit `0bb1301`)。
**取り込んでいない。並べて測った。**engine(`core/`・`adapters/`)は 0 行、QWED のコードも 0 行。LLM は呼んでいない。通信していない。0 USD(API 鍵の環境変数 4 つは 0 件・`provider=None`)。
正本は `fixtures/xbrl/cd8/qwed_compare_eprime_2026-10-20.json`
(`<venv>/bin/python measure/qwed_compare_2026-10-19.py --variant eprime-a --variant eprime-b --write` で再現。段 B の記録 `qwed_compare_2026-10-19.json` は書き換えていない。`--variant` なしの挙動は段 B のまま)。
入口: 配布名 `qwed` 7.3.0(`importlib.metadata`)・`qwed_new.__version__` 7.3.0・Python 3.11.17・`fact_verifier.py` の sha256 `e59520b0…6afaa`(段 B と同じ)。
**W1・S は走らせていない**(追記 2 は E′ だけ)。**封は直さない。**外れ 1 欄(Q-21)は外れとして §3 に残す。

---

## §1 判定 ― **QWED の `entity_match` は単位も参照先も見ない値検索。verdict は数の一致を半分しか映さない**

E′ の描き方は段 B の E と「値の字」と「換算」だけが違う(追記 2 の表)。context の値の字は claim 側と同じ関数(`scaled_value_str`、換算なし)を両側に掛けた。
追記 2 の「実物から描いた 1 行」(S100YXMA R004)は記録でそのとおりの字になっている:
context の行 `Fact OrdinaryIncome in CurrentYearDuration equals 12497000000.`(E′a・E′b とも一致 True)/ claim(E′a)`… equals 12497000000.`(一致 True)/ claim(E′b)`… equals 12497.`(一致 True)。

| 走らせ方 | 欄 | **実測** |
|---|---|---|
| E′a | Audit Core が GROUNDED にした 18 行の `entity_match` 1.0 | **18 / 18** |
| E′a | 注入 64 行の `entity_match` 1.0 | 2 / 64(T5 0 / 50・T3 2 / 12・T1 0 / 2)|
| E′a | QWED が通す(注入)| **0 / 64**(全体 12 / 192。12 は全部 無改変)|
| E′b | T5 50 行の `entity_match` 1.0 | **36 / 50** |
| E′b | 注入 64 行の `entity_match` 1.0 | 36 / 64 |
| E′b | QWED が通す(注入)| **14 / 64**(全体 16 / 192)|
| E′b | QWED が違うと言う(注入)| 39 / 64(判定なし 11)|
| E′b | GROUNDED 18 行の `entity_match` 1.0 | **0 / 18** |
| E′a・E′b | `status` BLOCKED(= REFUTED)| 62 / 192・62 / 192(段 B の E も 62)|
| Audit Core | 注入で検査通過(誤りを通す)| **0 / 64**(engine の GROUNDED 0 / 64。段 B の記録から写した)|

**値の字が一覧に在ることと `entity_match` 1.0 は両方向で一致した**(E′a 53 行・E′b 65 行。在るのに < 1.0 は 0・1.0 なのに無い 0)。
段 B で 0 / 192 だった 1.0 は、値の字を揃えただけで E′a 53・E′b 65 になった ― **段 B の E の 0 は `.0` の字の違いだった**(段 B の §3 Q-8 の原因 (1) のとおり)。

**E′a → E′b で動いたのは「換算」だけ**で、同じ 192 行の 1.0 が **GROUNDED 18 → 0・T5 0 → 36** と入れ替わった。
GROUNDED 18 行は Audit Core が参照先の fact と値を単位つきで突き合わせて通した行で、T5 50 行は**別の fact の生の円の値を行の単位で読ませた注入**(段 B の §3 Q-8 の原因 (2))。
QWED の `entity_match` は、どちらも「数の字が一覧のどこかに在るか」でしか見ていない。

**verdict(SUPPORTED)は数の一致を半分しか映さない。**E′b の SUPPORTED 34 行のうち `entity_match` 1.0 は 16・< 1.0 は 18。E′a の SUPPORTED 33 行のうち 1.0 は 12・< 1.0 は 21。
E′b で注入 64 行のうち 1.0 は 36 で、その verdict は SUPPORTED 14・NEUTRAL 11・REFUTED 11 に割れた(§3 Q-21)。

### §1-1 一覧(E′ の描き方での字数と chunk。段 B の描き方 `str(float)` の一覧は封 §1-1 と 8 / 8 一致することを先に確かめた)

| 書類 | fact | E′ の字数 | 段 B の字数 | chunk |
|---|---|---|---|---|
| S100YWGX | 1,122 | 108,719 | 110,764 | 2 |
| S100YXF5 | 947 | 89,781 | 91,439 | 1 |
| S100YXMA | 1,223 | 114,448 | 116,712 | 2 |
| S100YYRG | 777 | 68,976 | 70,358 | 1 |
| S100YYRV | 943 | 86,633 | 88,326 | 1 |
| S100YZ7E | 502 | 51,153 | 52,041 | 1 |
| S100YZCT | 1,097 | 103,905 | 105,881 | 2 |
| S100YZEV | 397 | 40,362 | 41,062 | 1 |

chunk は E′a・E′b とも **11**(段 B の E と同じ割れ方)。字数が減ったのは、整数の値の `.0` が落ちた 6,285 行と、`-0.0` が `0` になった 12 行の分(8 書類 7,008 fact。`fact_lines` と `fact_lines_eprime` を同じ instance に掛けて行ごとに比べた。整数でない値 711 行は 1 書類 47〜119 行で、十進の字はそのまま)。

### §1-2 対照 C-2(E′a で当て直した)

| 対照 | 期待 | 実測 | |
|---|---|---|---|
| C-2 E′a の +1 | `entity_match` 1.0 → < 1.0 | **1.0 → 0.857**・NEUTRAL → NEUTRAL | 期待どおり |

段 B で動かなかった +1(0.857 → 0.857)が、値の字を揃えると **1.0 → 0.857** と動いた。道具がこの数を見ている証拠。verdict は +1 の前後とも NEUTRAL(数が合っても SUPPORTED にならない行)。

---

## §2 追記 2 の「読み方」の 2 文 ― **1 文目は当たり、2 文目は外れ**

- **「Q-20 と Q-24 が当たれば…」― 当たり。**Q-20 は 36(予測 34〜38)、Q-24 は 0(予測 0〜2)。同じ 18 行が、換算すれば在り(E′a 18 / 18)、換算しなければ無い(E′b 0 / 18)。T5 はその逆(E′a 0 / 50・E′b 36 / 50)。**QWED の `entity_match` は単位も参照先も見ない値検索**で、Audit Core は同じ 50 行の T5 を VALUE_MISMATCH / 参照先なし で 0 件通した(封 §1-1)。これが「QWED は計算、こちらは出所」を数で言う形 ― ただし、この数で言えるのは **0 USD の決定論の部分の `entity_match`** についてだけ(§4)。
- **「Q-21 の『通す』が 0〜5 なら、QWED の verdict は数の一致を映さない」― 外れ。**通すは 14 / 64。verdict は数の一致を**半分だけ**映す: 注入で 1.0 の 36 行の verdict は SUPPORTED 14・NEUTRAL 11・REFUTED 11。SUPPORTED 34 行のうち 1.0 は 16・< 1.0 は 18(§1)。

---

## §3 予測との照合(**封は書き換えない**)

**当たり 6 / 外れ 1。**

| | 予測 | 実測 | |
|---|---|---|---|
| Q-18 | E′a: GROUNDED 18 行の 1.0 は 18 / 18 | 18 / 18 | **当たり** |
| Q-19 | E′a: 注入 64 行の 1.0 は 0〜3 | 2(T5 0・T3 2・T1 0) | **当たり** |
| Q-20 | E′b: T5 50 行の 1.0 は 34〜38 | 36 | **当たり** |
| **Q-21** | E′b: 通す 注入 0〜5 / 64・1.0 で数えれば 34 以上 / 64 | 通す **14** / 64・1.0 は 36 / 64 | **外れ** |
| Q-22 | E′a・E′b とも BLOCKED 55〜70 / 192 | 62・62 | **当たり** |
| Q-23 | C-2(E′a): 1.0 → < 1.0 | 1.0 → 0.857 | **当たり** |
| Q-24 | E′b: GROUNDED 18 行の 1.0 は 0〜2 | 0 | **当たり** |

### 外れの原因(1 件ずつ読んだ。数は記録の「外れの原因の読み」)

- **Q-21 外れ**: 通す 14(予測 0〜5)。後半の「1.0 で数えれば 34 以上」は 36 で当たっていた。外れたのは**追記 2 の読み**「否定語の部分列検出が一覧の行を refute に分類し、SUPPORTED の条件 `support ≥ refute` が通りにくい」で、これは claim の側に否定語の部分列が無い行にしか当たらない。
  QWED の支持 / 反証の分類は「claim と文の否定語の有無が同じか」で決まり(`_determine_support_type`: 違えば refutes・同じで語の重なり > 0.5 なら supports)、REFUTED は上位 3 引用に食い違いが在りかつ refute > support のとき、SUPPORTED は重みつき合計 ≥ 0.7 かつ support ≥ refute のとき(`_calculate_verdict`。`fact_verifier.py` の sha256 は記録に留めた)。
  通す 14 のうち **10 は claim に `no` の部分列が在る行**(context id `…_NonConsolidatedMember` の `No`。S100YZ7E 6・S100YZEV 4)で、同じ context id を持つ一覧の行も `no` を含むので「否定の有無が同じ」になり supports が refutes を上回った。残る **4 は claim に否定語の無い行**(S100YXMA R021 `Fact equals 1000000.`・S100YWGX R010・S100YYRV R017・R018)。
  追記 2 の読みが当たったのは残る 22 行(NEUTRAL 11・REFUTED 11。S100YYRG 8・S100YZCT 8・S100YYRV 6)で、**書類の context id の字(`NonConsolidatedMember` が在るか)が verdict を分けた**。主張の中身ではない。
  **0 件を先に疑った**: 値の字の規則(在る ⇔ 1.0 が両方向で 0 のずれ)・chunk(11、段 B と同じ割れ方)・換算(E′a と E′b の違いは claim の値の字だけ)に欠陥は見つからなかった。14 は道具の数。

**外れの向き**: 1 欄。段 B と同じく、QWED の字句の扱い(否定語の部分列が claim の側にも在る)を軽く見た向き。

### 木・所要

- `core/`・`adapters/` の差分: 0 行(`git diff --numstat HEAD`)。status も 0 行。
- 足した file: 記録 `fixtures/xbrl/cd8/qwed_compare_eprime_2026-10-20.json`・この文書・門 `tests/measure/test_qwed_compare_eprime_result.py`。変えた file: `measure/qwed_compare_2026-10-19.py`(`--variant`・`--out` を足した。`--variant` なしの出力は段 B の記録と、読む欄 9 つ + 分類が 395 / 395 行で一致。違うのは QWED の `evidence` の語の並び(集合の順)・所要秒・pytest の欄だけ)。覆いの記録は 179 → 180 本(`tests/measure` 121 → 122)。
- 所要: 材料の組み立て 1.73 秒、E′a 3.21 秒、E′b 3.19 秒、対照 0.02 秒。**E′ + 対照 6.42 秒**(同じ測定を 3 回走らせ、読む欄 9 つ + 分類は 3 回とも 192 / 192 行で一致。記録は最後の 1 回)。

---

## §4 限界(封 §5・段 B §4 のとおり。測って分かった分を足す)

- **QWED の 0 USD の決定論の部分だけ**を測った。LLM の経路・Math engine・GraphFact は測っていない。QWED 全体の優劣ではない。
- **入力の形はこちらが決めた。**E′ は値の字を claim 側と同じ関数で揃え、参照先の解決は Audit Core から渡した。QWED に有利な条件の数である。
- **「QWED は計算、こちらは出所」の数は `entity_match` の数である。**verdict(SUPPORTED)は数の一致を半分しか映さず(§1)、否定語の部分列が context id に在るかで割れた(§3 Q-21)。verdict で率を作らない。
- **W1・S は走らせていない。**日本語の本文・表計算の数は段 B のまま。
- **同じ 8 書類である。**新しい標本で同じ数になる保証は無い。
- **qwed 7.3.0 の数である**(`fact_verifier.py` の sha256 を記録に留めた)。
- **誤りを通す率(偽陰性)だけを並べた。**E′b の「通す 14 / 64」は `entity_match` 1.0 かつ SUPPORTED の行で、Audit Core の 0 / 64 と同じ注入 64 行に対する数。無改変 128 行で QWED が通したのは E′a 12・E′b 2 で、正しい行の側でも通す数は少ない(偽警報の側は比べない)。
