# 封: QWED と同じ材料で測る ― **取り込まない。並べて測る。予測を先に固定する**

2026-10-19。人間の指示(2026-10-19、原文): 「**QWED という既存システムを見つけた。競合にも思えるが取り込めるかも**」「**問題ないなら入れて良い**」(Python 3.11 と QWED の導入)。
売却戦略(2026-10-19、第 1 版)は「**QWED は計算、こちらは出所**」と書いたが、それは公開ページとコードを読んだ見立てで、**同じ材料で測った数は 1 つも無い**。
この封は、Audit Core を測ったのと**同じ 2 つの材料**(XBRL 8 書類 192 行・表計算 35 件)に QWED の 0 USD の入口を通し、**誤りを通す率**を並べる。
**0 USD・LLM は呼ばない・engine(`core/`・`adapters/`)は変えない・QWED を依存に足さない。**
下見は `scratchpad/qwed/QWED_SURVEY_2026-10-19.md`(2026-10-19。合成の英文 3 件だけ。Audit Core の材料は通していない)。

---

## §0 何を何と比べるか(**実装者が 1 通りに書ける字で**)

**QWED の入口**(下見 §3-2。版は字で留める): qwed **7.3.0**(PyPI。GitHub `QWED-AI/qwed-verification`、Apache-2.0)、Python **3.11.17**(`/opt/homebrew/bin/python3.11`)、
venv は `scratchpad/qwed/venv`(**repo に入れない**)。

```python
from qwed_new.core.fact_verifier import FactVerifier
r = FactVerifier(use_llm_fallback=False).verify_fact(claim, context, provider=None)   # provider=None → LLM は呼ばれない
```

**読む欄**(1 行につき全部を記録に写す): `status`、`developer_fields` の `deterministic_verdict`・`deterministic_confidence`・
`scores.semantic_similarity`・`scores.keyword_overlap`・`scores.entity_match`・`scores.negation_conflict`・`len(citations)`・`constraint_id`。

**QWED の答えの 3 分類**(この封で決める。QWED の語彙ではない):

| 分類 | 定義 |
|---|---|
| **QWED が違うと言う** | `deterministic_verdict == "REFUTED"` **または** `status == "BLOCKED"` **または** `scores.entity_match < 1.0` |
| **QWED が通す** | `scores.entity_match == 1.0` **かつ** `deterministic_verdict == "SUPPORTED"` |
| **判定なし** | それ以外(`entity_match == 1.0` で `NEUTRAL` / `INSUFFICIENT_EVIDENCE`) |

**Audit Core 側は記録から写す。再実行しない。** XBRL は `fixtures/xbrl/cd8/period_unit_hold_2026-10-19.json` の `rows` の `**合成の後**`(engine の state)と `**最終判定(後)**`、
表計算は `fixtures/sheet/errdet_core_2026-10-17.json` の「検出 / 保留 / 見落とし(誤り 8 件)」。

**QWED のコードは変えない。QWED の答えを Audit Core の state に写さない。engine は触らない。**

## §1 材料と分母(**字で留める。全部いま測った**)

### 1-1 XBRL(③ の記録 `period_unit_hold_2026-10-19.json`、8 書類 × 24 行)

| | 数 |
|---|---|
| 行 | **192** |
| 注入(誤り) | **64**(型: T5_COINCIDENT **50**・T3_ABSENT **12**・T1_VALUE **2**。`material_2026-10-17.json` の 書類ごと) |
| 無改変 | **128** |
| 注入 64 行の engine の state(合成の後) | VALUE_MISMATCH **43**・参照先なし **21**・GROUNDED **0**・UNPROVABLE 0 |
| 無改変 128 行の engine の state(合成の後) | 参照先なし 86・UNPROVABLE 23・GROUNDED **18**・VALUE_MISMATCH 1 |
| 注入 64 行の最終判定(後。席 + engine) | 誤りが在る **51**・実証不能 13・**検査通過 0** |
| 無改変 128 行の最終判定(後) | 実証不能 107・検査通過 18・誤りが在る 2・不一致 1 |

**Audit Core が注入 64 件のうち検査通過(誤りを通す)にした行は 0。**これが並べる相手の数。

**下見(2026-10-19、いま測った。QWED は通していない)**: §2 の E の一覧の字数。instance の数の fact を 1 行 `Fact <局所名> in <context> equals <値>.` で並べると:

| 書類 | fact(全部が数) | 字数 |
|---|---|---|
| S100YWGX | 1,122 | 110,764 |
| S100YXF5 | 947 | 91,439 |
| S100YXMA | 1,223 | 116,712 |
| S100YYRG | 777 | 70,358 |
| S100YYRV | 943 | 88,326 |
| S100YZ7E | 502 | 52,041 |
| S100YZCT | 1,097 | 105,881 |
| S100YZEV | 397 | 41,062 |

QWED は context を **100,000 字で切る**(下見 §3-2)ので、E は **95,000 字以下の塊(chunk)に行の境で割る**(§2)。
**割れる数は S100YWGX・S100YXMA・S100YZCT が 2、他 5 書類が 1、合計 11**(字数から決まる。実装者の描き方が封と同じなら一致する)。

### 1-2 表計算(東京都 令和 6 年度決算、errdet の材料)

| | 数 |
|---|---|
| 主張(id) | **35**(`poc_gold_2026-10-17.json` の `rows`) |
| 文(重複なし。`rows[].文` の字) | **11** |
| 植えた誤り | **8**(I-1 2・I-2 2・II-1 2・II-2 2。`errdet_make_2026-10-17.json` の 植えた誤り)。**8 通りの文に 1 件ずつ**(元の表記はその文に 1 回だけ出る) |
| 誤りの無い文 | **3**(うち 1 文に罠 R035。文書は正しい) |
| 抜粋(context) | **4,194 字**(`measure/sheet_errdet_material_2026-10-17.py` の `extract_block()`。段 11 と 1 字も同じ) |
| Audit Core(errdet_core) | 検出 **4**(R004・R009・R010・R012)・保留 4(R001・R021・R024・R030)・見落とし 0・偽警報 0 |
| 群で見ると | 群 I(値が原資料に無い)4 件: 検出 2(R010・R012)・保留 2 / 群 II(値は原資料に在る)4 件: 検出 2(R004・R009)・保留 2 |

## §2 走らせ方 3 本(**1 本ごとに入力の作り方を 1 通りに**)

### W1 ― XBRL、日本語のまま、本文を読ませる(192 行)

- `claim` = その行の **抜粋**(改変後の本文から切った字。③ と同じ `MB.build_rows` の `抜粋`)。
- `context` = その書類の **改変後の本文**(`IJ.apply_edits` の後の `tampered`。③ と同じ組み立て。`measure/xbrl_holds_product_path_2026-10-19.py` の `_material_rows`)。
- 意味: **読み手に渡した文書と、その文書から切った主張**。QWED の Fact が「文書に書いてあるか」を見る道具なら、ここでは全部「書いてある」。

### E ― XBRL、英語の機械文、fact の一覧を読ませる(192 行。**QWED に有利な条件**)

- `context` = その書類の instance の **数の fact 全部**を instance の並びで 1 行ずつ
  `Fact <局所名> in <context id> equals <値の字>.`(局所名は `name` の `:` より後。値は instance の字そのまま。改行で結ぶ)。
  **95,000 字以下の chunk に行の境で割る**(前から詰める)。
- `claim` = 席が参照先を名指した行(85 行): 参照先を ③ と同じ `A1.norm_pointer` で fact に解き、`Fact <局所名> in <context id> equals <換算した値>.`。
  解けなければ `@` の前後をそのまま局所名・context id に置く。参照先なし(107 行): `Fact equals <換算した値>.`。
- **換算した値** = 行の `値` × `UNIT_SCALE[単位]`(`adapters/xbrl/vocabulary.py`。百万円 1e6・千円 1e3・億円 1e8・兆円 1e12・円 1)。
  `％`・`%`・単位なしは `値` のまま。整数なら桁区切りなしの整数の字、そうでなければ末尾の 0 を落とした十進の字(指数表記にしない)。
- 行の結果 = **その書類の chunk 全部に当て、`entity_match` が最大の chunk の結果**(同点は前の chunk)。chunk ごとの結果も記録に残す。
- 意味: **QWED に Audit Core の参照先の解決と単位の換算を渡したうえで**、数が一覧に在るかを見させる。
  残る違いは「**その数が別の fact に在るとき(T5)に通すか**」。

### S ― 表計算、日本語のまま(11 文)

- `claim` = `poc_gold_2026-10-17.json` の `rows[].文` の重複なしの 11 文。誤りの 8 文は `植えた誤り` の `元の表記` を `植えた表記` に **1 回だけ**置き換える(置き換えた回数が 1 でなければ止める)。
- `context` = `extract_block()` の抜粋(4,194 字)。
- 文の結果を id に写すとき: 文に属する id は全部その文の結果を持つ(**文と id は 1 対多**。誤り 8 件の比較は文の単位で行い、id の単位では書かない)。

**順序**: W1 → E → S → 対照(§3)。**途中で封を書き換えない。**

## §3 対照(**測る道具の故障を作って当てる。1 回に 1 件**)

| 対照 | 作り方 | 期待(外れたら測る道具を疑う) |
|---|---|---|
| **C-1 英文の再現** | 下見 §5 の (a)(b) をそのまま通す | (a) `entity_match` 1.0・SUPPORTED / (b) `entity_match` < 1.0・SUPPORTED(下見と同じ) |
| **C-2 E の +1** | GROUNDED の先頭行 S100YXMA R004(`ordinaryincome@currentyearduration`、12,497 百万円)の換算した値に +1 | `entity_match` < 1.0 **かつ verdict は SUPPORTED のまま**(名前が合えば数を見ない) |
| **C-3 \b の読み** | S の R010 の文(I-1、植えた表記 `32,385,483,000円`)から QWED の数の正規表現 `\b\d{1,20}(?:\.\d{1,10})?\b` で抜いた字 | **その数から抜けるのは `385`・`483` の 2 つだけ**(`32` は `額` に、`000` は `円` に挟まれて境界が無い) |

## §4 予測(**欄ごと・外れうる形で**。結果を見てから書き換えない)

QWED の Fact は tokenizer `[a-zA-Z]+`・文の切れ目 `[A-Z]` 始まり・重みつき合計 `0.3·semantic + 0.3·keyword + 0.2·entity + 0.2·(否定なし)`、
SUPPORTED は 0.7 以上・NEUTRAL は 0.4 以上(下見 §3-2、コード `fact_verifier.py`)。**日本語の文は語が 0 個**なので、残るのは数の一致(`entity_match`)と否定語だけ。

| | 予測 | **外れ方** |
|---|---|---|
| **Q-1** | W1: `status` は **192 / 192** が `UNVERIFIABLE`(VERIFIED 0・BLOCKED 0) | 1 行でも他の値 |
| **Q-2** | W1: `deterministic_verdict` は 192 / 192 が `NEUTRAL` か `INSUFFICIENT_EVIDENCE`(**SUPPORTED 0・REFUTED 0**) | SUPPORTED か REFUTED が 1 行でも |
| **Q-3** | W1: `len(citations)` **0** が 192 / 192、`keyword_overlap` **0.0** が 192 / 192 | 1 行でも非 0 |
| **Q-4** | W1: `entity_match` 1.0 は **注入 64 / 64**(植えた数は改変後の本文に在る)、全体 **185 以上** / 192 | 注入で 1 行でも < 1.0、または全体 184 以下 |
| **Q-5** | W1: **QWED が違うと言う: 注入 0 / 64。QWED が通す: 0 / 192**(verdict が SUPPORTED にならない)。判定なし 185 以上 | 違うと言う 1 件でも / 通す 1 件でも |
| **Q-6** | E: 一覧の字数は §1-1 の表と **8 / 8 一致**、chunk は **11** | 1 書類でも違う |
| **Q-7** | E: verdict `SUPPORTED` は **180 以上** / 192(語が合えば数が無くても 0.7 を超える) | 179 以下 |
| **Q-8** | E: 注入 64 行で、T5 50 行の `entity_match` 1.0 は **35 以上**、T3+T1 14 行の < 1.0 は **12 以上** | どちらかを下回る |
| **Q-9** | E: **QWED が通す: 注入 35 以上 / 64**。Audit Core の engine は GROUNDED **0 / 64**、最終判定の検査通過 **0 / 64** | 34 以下 |
| **Q-10** | E: 無改変 128 行の `entity_match` 1.0 は **60〜100** | 幅の外 |
| **Q-11** | E: Audit Core が GROUNDED にした 18 行の `entity_match` 1.0 は **14 以上** / 18(EDINET の値は丸めた桁で入っているので換算が合う) | 13 以下 |
| **Q-12** | C-2: `entity_match` < 1.0 **かつ** SUPPORTED のまま | 1.0 のまま、または SUPPORTED でなくなる(QWED が数で verdict を変える = 私の読みの外れ) |
| **Q-13** | S: `status` UNVERIFIABLE **11 / 11**、verdict NEUTRAL か INSUFFICIENT_EVIDENCE 11 / 11、citations 0 が 11 / 11 | 1 文でも他 |
| **Q-14** | S: 誤りの 8 文で `entity_match` 1.0 は **6 以上**(`,` で割れた 3 桁の組が 4,194 字のどこかに在る)。**QWED が違うと言う ≦ 2 / 8**。Audit Core は検出 4 / 8・保留 4・見落とし 0 | 違うと言う 3 件以上 |
| **Q-15** | C-3: 抜けた字は **`385`・`483` のちょうど 2 つ** | `32` か `000` が入る、または 2 つに足りない |
| **Q-16** | 費用と時間: API 鍵の環境変数 4 つ(`ANTHROPIC_API_KEY`・`OPENAI_API_KEY`・`GOOGLE_API_KEY`・`GEMINI_API_KEY`)は **0 件**、`provider=None`、3 本 + 対照の所要 **300 秒未満** | 鍵 1 つでも在る / 300 秒以上 |
| **Q-17** | 木: `core/`・`adapters/` の差分 **0 行**。足す file は封側 2 本・結果側 4 本(§5)。覆いの記録は封の commit で +1、結果の commit で +1。結果の commit の後 `python3 -m pytest -q tests/measure` は **赤 0** | 差分 1 行でも / 赤 1 本でも |

**本当に測っているのは Q-4・Q-5・Q-8〜Q-11・Q-14 である。**他は道具の読みの確認。
**「QWED は計算、こちらは出所」が当たりなら、Q-5(日本語では何も言えない)と Q-9(英語の一覧でも T5 を通す)が当たる。**

## §5 限界(先に書く)

- **QWED の LLM の経路は測らない**(0 USD)。QWED 自身が README で「Fact は advisory。VERIFIED を返さない」と書く。**この封が測るのは QWED の 0 USD の決定論の部分だけ**で、QWED 全体の優劣ではない。
- **入力の形はこちらが決めた。**W1・S は QWED に不利(日本語)、E は有利(参照先の解決と単位の換算を Audit Core から渡す)。**E が QWED の最良の条件で、それでも T5 を通すかを見る。**
- **Math engine(`verify_math`)は測らない。**Audit Core が抜いた 2 つの数を渡すだけで、QWED が照合しているのではない(`memory: shared-extractor-defect-flips-the-verdict`)。
- **GraphFact は測らない**(述語の表が英語の固定表。下見で三つ組 0 / 0)。
- **同じ 8 書類・同じ 35 件である。**新しい標本で同じ数になる保証は無い(`memory: diagnosis-does-not-transfer-to-a-new-sample`)。
- **qwed 7.3.0 の数である。**版が変われば測り直す。
- **誤りを通す率(偽陰性)だけを並べる。**偽警報の側は、QWED が W1・S で何も言わないので比べられない(E の無改変 128 行の `entity_match` < 1.0 は「丸め・単位・参照先の違い」が混ざるので偽警報と呼ばない)。

## §6 触る file と順序

**段 A(この封。文書 + 門。engine 不変)**: `docs/QWED_COMPARE_SEAL_2026-10-19.md`・`tests/measure/test_qwed_compare_seal.py`・覆いの記録(`fixtures/suite_coverage_2026-10-16.json`・`docs/SUITE_COVERAGE_2026-10-16.md` §2-1)。

**段 B(測定。別セッション。Python 3.11 の venv で走らせる。engine 不変)**:
- `measure/qwed_compare_2026-10-19.py` ― 3 本 + 対照。`qwed` が import できない(3.9)ときは理由を印字して止まる。記録に `qwed.__version__`・`sys.version`・`fact_verifier.py` の sha256 を書く
- `fixtures/xbrl/cd8/qwed_compare_2026-10-19.json` ― 全行(W1 192・E 192 と chunk ごと・S 11・対照 3)の読む欄と、Audit Core 側の写し、予測との照合
- `docs/QWED_COMPARE_RESULT_2026-10-19.md` ― 当たり / 外れを欄ごとに
- `tests/measure/test_qwed_compare_result.py` ― 文書の数を記録に縛る門。**変異 3 通り**(記録の「QWED が通す 注入」±1 → 赤、Audit Core 側の写し 0 → 1 → 赤、文書の数の改ざん → 赤)で赤を確かめてから門と呼ぶ

**これ以外に触らない。**`core/py/` は 0 行、`adapters/` は 0 行。過去の門の engine の留め(`test_xbrl_axis3_decision.py` test_9 の git log・`test_xbrl_cd_seal.py` の sha・`test_verify_external_v1.py`)は engine を触らないので**衝突しない**(予測 Q-17)。

**順序**: 段 A を commit → 段 B の実装と測定 → 独立監査(`step-auditor`)GO → commit(パス指定)。**測ってから封を直さない。**

## §7 やらないこと

- QWED を `audit-core` の依存に足さない(標準ライブラリのみ、を守る)。venv は scratchpad に置く。
- QWED の答えを Audit Core の 4 状態に写す表(下見 §6 の候補)は**作らない**。並べて数えるだけ。
- LLM の英訳・LLM fallback・`qwed verify`(CLI。LLM 必須)は呼ばない。

---

## 追記 2(2026-10-20、段 B の結果の後。**本文は書き換えない**)

段 B(`docs/QWED_COMPARE_RESULT_2026-10-19.md`、commit 0bb1301)で予測 17 欄のうち 10 欄が外れた。主因は 2 つとも**この封の入力の描き方**で、QWED の性質ではない。

1. §2 E の「値は instance の字そのまま」は float の字(`12497000000.0`)で、claim の「整数の字」(`12497000000`)と**字が違う**。QWED は数の**字**の集合を突き合わせるので E は 192 / 192 で `entity_match` < 1.0 になった(記録 `**外れの原因の読み**/E`: 値の字に `.0` を付けると 53 / 192 が在り、GROUNDED 18 行は 18 / 18、T3+T1 14 行は 2 / 14)。
2. §4 Q-8 の「T5 = その数が別の fact に在る」は、T5 の植えた値が**借りた ref の生の円の値を行の単位(千円・百万円)で読ませたもの**だという注入の定義を読まずに書いた。行の単位で換算すると一覧に無く(0 / 50)、換算しなければ 36 / 50 が在る。

**E′(2 本。描き方の違いは「値の字」と「換算」だけ。他は §2 E のまま。chunk・参照先の解決・一覧の並びも同じ)**:

| 走らせ方 | context の値の字 | claim の値 |
|---|---|---|
| **E′a** | 整数なら整数の字(`12497000000`)、そうでなければ末尾の 0 を落とした十進の字(claim 側 §2 と同じ規則を両側に掛ける) | §2 E のまま(`UNIT_SCALE` で換算) |
| **E′b** | E′a と同じ | **換算しない**(行の `値` を同じ規則で字にする。`12497.0` → `12497`) |

**実物から描いた 1 行**(S100YXMA R004。GROUNDED、12,497 百万円、`ordinaryincome@currentyearduration`。段 B の記録の `rows/E` から):
context の行 `Fact OrdinaryIncome in CurrentYearDuration equals 12497000000.`(段 B では `… equals 12497000000.0.`)/ claim(E′a)`Fact OrdinaryIncome in CurrentYearDuration equals 12497000000.`(段 B と同じ字)/ claim(E′b)`Fact OrdinaryIncome in CurrentYearDuration equals 12497.`

**対照 C-2 は E′a で当て直す**(換算した値 +1 で `entity_match` が 1.0 から下がることを見る。段 B では元から 0.857 で動かなかった)。
記録の版の欄は `importlib.metadata.version("qwed")` と `qwed_new.__version__`(§6 の `qwed.__version__` という module は無い。段 B の記録どおり)。

| | 予測 | **外れ方** |
|---|---|---|
| **Q-18** | E′a: GROUNDED 18 行の `entity_match` 1.0 は **18 / 18**(記録の `.0` の読みと同じ) | 17 以下 |
| **Q-19** | E′a: 注入 64 行の `entity_match` 1.0 は **0〜3**(T5 は行の単位で換算すると一覧に無い。T3+T1 は記録で 2 / 14 が在る) | 4 以上 |
| **Q-20** | E′b: T5 50 行の `entity_match` 1.0 は **34〜38**(記録の「換算しなければ 36 / 50」±2) | 幅の外 |
| **Q-21** | E′b: **「QWED が通す」(SUPPORTED かつ 1.0)注入は 0〜5 / 64**(否定語の部分列検出が一覧の行を refute に分類し、SUPPORTED の条件 `support ≥ refute` が通りにくい)。**`entity_match` 1.0 で数えれば 34 以上 / 64** | 通す 6 以上 / 1.0 が 33 以下 |
| **Q-22** | E′a・E′b とも `status == BLOCKED`(REFUTED)は **55〜70 / 192**(段 B の 62 と同じ機構。描き方は数の字しか変わらない) | 幅の外 |
| **Q-23** | C-2(E′a): `entity_match` 1.0 → **< 1.0** | 1.0 のまま |
| **Q-24** | E′b: GROUNDED 18 行の `entity_match` 1.0 は **0〜2**(換算しない値は一覧に無い。記録 0 / 18) | 3 以上 |

**読み方(先に書く)**: Q-20 と Q-24 が当たれば「同じ 18 行が、換算すれば在り(E′a)、換算しなければ無い(E′b)。T5 はその逆」― QWED の `entity_match` は**単位も参照先も見ない値検索**で、Audit Core は同じ 50 行の T5 を VALUE_MISMATCH / 参照先なし で 0 件通した(§1-1)。これが「QWED は計算、こちらは出所」を数で言う形。Q-21 の「通す」が 0〜5 なら、QWED の verdict は数の一致を映さない(段 B と同じ)。

**順序**: この追記を commit → E′ の測定(段 B の script に `--variant eprime-a|eprime-b` を足す。段 B の記録は書き換えず、新しい記録 `fixtures/xbrl/cd8/qwed_compare_eprime_2026-10-20.json`・結果 `docs/QWED_COMPARE_EPRIME_RESULT_2026-10-20.md`・門 `tests/measure/test_qwed_compare_eprime_result.py`)→ 独立監査 → commit。
