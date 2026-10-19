# 封: 汎化 C ― **未使用 8 書類で、いまの engine(③ + PP)の数が出るかを 0 USD で測る(C0)。席つきの比較(C1)は C0 の後に「まだ要る論点」だけ**

2026-10-20。人間の言葉(2026-10-20、原文): 「**有料のLLMはいつでも好きな時に使っていい** / claudeのAPIを使って / **決めるのは全て君でいい**」、
「既存8書類と重複しない候補書類を一覧化する。取得方法と、対象にできる数値主張の件数を確認する。検証対象・評価指標・予測・除外条件を封印する。
**0 USDで汎化Cを実行し、結果を監査する。**その後、測った事実を1冊にまとめる。**LLM単体とLLM＋Coreの比較がまだ必要な論点に限って、有料試験を行う。**」
司令塔の決定: この流れのとおり。いまの数は全部「同じ 8 書類(cd8)」の数で、新しい標本で増分が 0 になった前例がある(記憶 `diagnosis-does-not-transfer-to-a-new-sample`)。
**engine(`core/`・`adapters/`)は 1 行も変えない。測ってから直さない。**C0 は席を呼ばない。QWED は使わない。

---

## §0 何を測るか(**新しい腕は作らない。cd8 で測った経路をそのまま新しい書類に当てる**)

| 段 | 経路 | 出どころ(定義をそのまま) | 費用 |
|---|---|---|---|
| **C0-1 製品の経路(無改変)** | `adapters/xbrl/verify_document.py --doc <id>`(Core が主張を切り出し、名指し、検算する ①)。claims の本数と state の分布 | `docs/XBRL_HOLDS_PRODUCT_PATH_RESULT_2026-10-19.md` F-7 | 0 USD |
| **C0-2 注入(Core の名指し)** | (ア)の pipeline `measure/xbrl_a_core_vs_grep_2026-10-17.py`(`--docs` に 8 件、profile P16、種 `measure/SEED.json`)。腕は Core(厳しい読み方)・**Core-P**(止めても pointers を読む)・D′・D″ | `docs/XBRL_A_CORE_VS_GREP_RESULT_2026-10-17.md` | 0 USD |
| **C0-3 engine を Core-P の参照先に当てる** | C0-2 で Core-P が名指した参照先を `verify_external(spec, period_pair=True)` の `pointers` に渡し、③ の保留と PP を**同じ行に**当てる(席の参照先の代わりに Core の参照先。**新しい規則ではない。入口は measure/**) | `adapters/xbrl/verify_external.py`(ac8c3ff) | 0 USD |
| **C1 席つき(条件つき)** | cd8 と同じ 24 行 × 8 の材料・同じ問い(sha256 `4c63022014736bb25de0c3808d227c06bbfcd72856aaf3a2e2dfdf31cb85c0fb`、411 字)・1 席 × 8 便 `model=sonnet`・腕 A / C′(席を上書きしない)/ D′ / D″ | `docs/XBRL_CD_SEAL_2026-10-17.md`・`XBRL_CD_SEAL_V2_2026-10-17.md`・`XBRL_CD_MATERIAL_SPEC_2026-10-17.md` | 席 8 便 |

**C1 をやる条件(先に書く)**: C0 の結果で **G-5(Core-P の特定率)か G-8(注入を通す 0)が外れたとき**、または **G-10・G-11(実証できた行・保留)が cd8 から 15 pt 以上落ちたとき**だけ、「席が名指せば engine は持ち直すか」を A / C′ で測る。
どれも当たりなら **C1 はやらない**(cd8 で Z-1・Z-2 とも「上回らない」が出ており、同じ比較を繰り返す論点が無い)。C1 をやるときは**別の追記で予測を先に書く**。

## §1 材料と分母(**字で留める。全部いま測った**)

| | 数 | 出どころ |
|---|---|---|
| 母集団 | **256** | `fixtures/xbrl/holdout_p17/pool2_clean_2026-10-14.json`(ordinanceCode 010 / formCode 030000) |
| 並び | seed `6a24d72` の shuffle(`docs/HOLDOUT_SPLIT_SEAL_2026-10-14.md`) | 同 |
| 使った位置 | `order[0:22]`(分割の封)・`order[24:26]`(Q2)・`order[26:34]`(欠陥 A)・`order` の 34・37・41・42・43・46・56・58(cd8) | 各 draw の記録 |
| **引く規則** | cd8 の規則(`fixtures/xbrl/cd8/draw_2026-10-17.json` の `rule`)を **位置 59 から**続ける: `docs/`・`fixtures/`(母集団の名簿 3 file を除く)に docID が 1 度も出ていない先頭 8 件 | draw の記録 `fixtures/xbrl/gen_c/draw_2026-10-20.json`(位置・飛ばした件・キャッシュに無いこと) |
| **引いた 8 件**(位置 59〜66。飛ばした件 0) | `S100Z0OS` `S100YYN7` `S100YYT8` `S100Z42X` `S100YYT4` `S100Z4GF` `S100Z4J8` `S100YYUD` | 2026-10-20 に上の規則で計算 |
| キャッシュに在るか | **8 件とも無い**(= 一度も取っていない) | `~/.cache/audit-core/edinet/` を見た |
| 取得 | EDINET API(無料)。**`EDINET_API_KEY` は人間が環境変数で渡し、値は記録しない**。`measure/xbrl_cd_fetch_2026-10-17.py` と同じ作りの `measure/xbrl_gen_c_fetch_2026-10-20.py`。取る前にキャッシュに無いことを確かめ、在れば止める。取った後は使用済み(1 度しか開かない) | `fixtures/xbrl/cd8/fetched_2026-10-17.json` の形 |
| 対象にできる数値主張の件数 | **取得後に数える**(C0-1 の claims の本数。cd8 の S100YXMA は 119 本)。予測は §4 G-2 | F-7 |
| 注入(C0-2) | (ア)と同じ: 型 T5・T1・T3、書類ごとに作れる site から種で引く(cd8 の 8 書類で合計 142。T5 64・T1 38・T3 40) | `fixtures/xbrl/cd8/a_core_vs_grep_2026-10-17.json` |

**除外**: 母集団の外の書類・既に開いた書類・取得できなかった書類(取得できなければ次の位置から規則で補い、draw の記録に書く)。

## §2 cd8 で測った数(並べる相手。**ここから予測を作る**)

| | cd8 | 出どころ |
|---|---|---|
| C0-1: S100YXMA の claims 119 本、state GROUNDED 60 / VALUE_MISMATCH 24 / UNVERIFIABLE 18 / POINTER_NOT_FOUND 17 | 1 書類だけ記録 | `holds_product_path_2026-10-19.json` F-7 |
| C0-2: Core-P の特定率(T5) | 46 / 64 = 71.9% | `a_core_vs_grep_2026-10-17.json` 採点/Core-P |
| C0-2: Core-P の誤認定率(参照先を出した件) | 18 / 76 = 23.7% | 同 |
| C0-2: Core-P の T1 の通し / T3 の名指し | 0 / 38 = 0.0% / 6 / 40 = 15.0% | 同 |
| C0-2: D′ の特定率 / 誤認定率 | 0.0% / 100.0% | 同 |
| engine(席の参照先で): 注入 64 行の検査通過(GROUNDED) | **0** | `period_unit_hold_2026-10-19.json` rows(合成の後) |
| engine: 名指した行の U 保留 / 正解 50 件の P・U 保留 | 17 / 85 = 20.0% / 0・0 | 同 D2・D4 |
| engine: 実証できた行(PP の後) | 77 / 192 = 40.1% | `period_pair_stage2_2026-10-19.json` |
| PP: 率の主張で参照先 1 本 → 検算 | 17 行中 GROUNDED 15・UNPROVABLE((d))2 | 同 |

## §3 対照(**測る道具の故障を作って当てる。1 回に 1 件**)

| 対照 | 中身 | 期待 |
|---|---|---|
| **C-1 cd8 の再現** | C0-2 の script を cd8 の 8 書類(使用済み)で `--out` を一時 file に向けて回し、`a_core_vs_grep_2026-10-17.json` の採点と一致 | 全欄一致(道具が変わっていない) |
| **C-2 注入の他行への影響** | C0-1 を改変前の instance で、C0-2 を改変後で回し、無改変の主張の state が動かない | 判定が動いた 0 |
| **C-3 engine の留め** | C0-3 の `verify_external` が ac8c3ff の `adapters/` と byte 同一(sha256)。`period_pair=False` で回すと PP の行だけ変わる | 一致 / PP の行以外 0 |

## §4 予測(**欄ごと・外れうる形で**。cd8 の数と「新標本で落ちる」前例から。合格線は作らない)

| | 予測 | **外れ方** |
|---|---|---|
| **G-1** | 取得: 8 件とも取れる(byte > 0・zip が開く・instance の fact ≥ 300) | 1 件でも取れない / fact 299 以下 |
| **G-2** | C0-1: claims の本数は書類ごとに **60〜250**、8 書類の合計 **600〜1,600** | 1 書類でも幅の外 / 合計が幅の外 |
| **G-3** | C0-1: 8 書類の合計で GROUNDED の割合 **35〜60%**、VALUE_MISMATCH **10〜30%** | どちらか幅の外 |
| **G-4** | C0-2: 注入の合計 **100〜180**、T5 が **1 件以上作れる書類 6 以上 / 8** | 幅の外 / 5 以下 |
| **G-5** | C0-2: Core-P の特定率(T5)**55〜80%**(cd8 71.9%) | 幅の外 |
| **G-6** | C0-2: Core-P の誤認定率 **15〜35%**、T1 の通し **0%**、T3 の名指し **25% 以下** | どれか幅の外 / T1 1 件でも |
| **G-7** | C0-2: D′ の特定率 **0%**、誤認定率 **90% 以上**(値検索は新しい書類でも有害) | 特定 1 件でも / 誤認定 89% 以下 |
| **G-8** | C0-3: Core-P が名指した**注入の行**で engine が GROUNDED にする件数 **0**(誤りを通す 0。**この封の最重要の数**) | 1 件でも |
| **G-9** | C0-3: Core-P が名指した注入の行の state は VALUE_MISMATCH **60% 以上**、UNPROVABLE(保留)**40% 以下** | 幅の外 |
| **G-10** | C0-3: Core-P が名指した行の U 保留 **5〜35%**、(d) 保留 **0〜10%** | 幅の外 |
| **G-11** | C0-1: 実証できた行(GROUNDED + VALUE_MISMATCH)の割合は cd8 の 40.1%(席の参照先)と**同じ桁(25〜65%)**。分母が違う(Core の切り出し全部)ので並べ方を記録に書く | 幅の外 |
| **G-12** | C0-1: 率の主張で PP が発火(derived_pointers 非空)する行 **8 書類で 10 以上**、そのうち GROUNDED **半分以上** | 9 以下 / 半分未満 |
| **G-13** | 対照 C-1〜C-3 が全部期待どおり | 1 つでも外れ(道具を疑う) |
| **G-14** | 木: `core/`・`adapters/` 差分 0 行。過去の門の engine の留めは衝突しない。覆い +2(封の門・結果の門) | 差分 1 行でも / 赤 1 本でも |

**本当に測っているのは G-5〜G-12 である。G-8 が外れたら、直さずに 1 件ずつ読んで記録し、直しは別の封で。**

## §5 限界(先に書く)

- **8 書類 1 回である。**合格線は作らない(cd8 と並べて「落ちたか・同じか」を書くだけ)。
- **C0 の engine の数は Core 自身の名指しに依る**(席の名指しではない)。cd8 の engine の数(席の名指し)と並べるときは分母の違いを書く。席が名指せばどうなるかは C1 でしか分からない。
- C0-1 の claims は Core の切り出しで、席の 24 行の材料とは単位が違う。
- 「測った事実」1 冊はこの後。**この封の数が落ちても落ちたまま 1 冊に載せる。**

## §6 触る file と順序

**段 A(この封 + draw。engine 不変)**: `docs/XBRL_GENERALITY_SEAL_2026-10-20.md`・`tests/measure/test_xbrl_generality_seal.py`・`measure/xbrl_gen_c_draw_2026-10-20.py` → `fixtures/xbrl/gen_c/draw_2026-10-20.json`・覆いの記録。
**段 B(取得。人間が鍵を渡す)**: `measure/xbrl_gen_c_fetch_2026-10-20.py` → `fixtures/xbrl/gen_c/fetched_2026-10-20.json`(sha256・バイト数・時刻。鍵の値は書かない)。
**段 C0(0 USD。別セッション)**: `measure/xbrl_gen_c_2026-10-20.py`(C0-1〜C0-3 と対照。(ア)の script と `verify_document` を import して使う)→ `fixtures/xbrl/gen_c/c0_2026-10-20.json`・結果 `docs/XBRL_GENERALITY_RESULT_2026-10-20.md`・門 `tests/measure/test_xbrl_generality_result.py`(変異 3 通り)・覆いの記録。
**段 C1(条件つき。別の追記で予測を先に)**: cd8 の材料・席・採点の script を import して `fixtures/xbrl/gen_c/` に記録。
**これ以外に触らない。**`core/py/` は 0 行、`adapters/` は 0 行。

**順序**: 段 A を commit → 段 B(人間)→ 段 C0 → 独立監査 GO → commit → (条件を満たすときだけ)C1 の追記 → C1 → 監査 → commit → 「測った事実」1 冊。**数を見てから封・材料・採点を直さない。**
