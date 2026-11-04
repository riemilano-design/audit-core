# 封: 丸め方の根拠が混ざる桁は両方の帯で照らす RB ― P30E = P29E + RB(旗 `rounding_mixed_2026_11_04`。既定は P27 のまま)― 2026-11-04

根拠は読み取り N の結果 [XBRL_NUMBER_READER_ENGINE_RESULT_2026-11-04.md](XBRL_NUMBER_READER_ENGINE_RESULT_2026-11-04.md)(`dc2cfe7`)§3 の K-2 の外れと §5 の 1 の (イ)。engine(`adapters/`)を変える。この便は全部 0 USD(API の呼び出しなし。材料は既にある AI の文 200 本・前の便の盲検の札・手元の有報の原文 97 書類)。

## §0 材料と決めごと

### §0-1 測った事実(この封を書く前に司令塔が 0 USD で数えた。script は scratchpad/numfix/。記録にはしない)

1. **動いた既存の行 21 に前の便の札を当てた**(`ai200_2026-11-04.json` の `変わった行の中身` と `labels_2026-11-03.json`・`f5_labels_2026-11-03.json` を、P27 の claim の並びで id に結んだ): 21 行のうち札 **真 20・偽 1**。真の行のうち GROUNDED を失った行 15(K-2 の 8 行では 7)、GROUNDED になった行 4。つまり読み取り N の便で動いた既存の行は、ほぼ全部が人の目では正しい数で、engine は正しい数を「値が違う」に変えた。
2. **原因は書類単位の丸め方の決定**(`V.decide_rounding`: 書類の全 claim の根拠で round / truncate を 1 つに決め、2 周目はその 1 つの帯だけで照らす。XBRL 直し §2、人間の決定 2026-10-08): 200 本のうち、P28E → P29E で決定が truncate → round に切り替わった本 11。切り替わった本では、万円で書いた新しい claim の多くが round でしか説明できず、既存の万円の行(札 真)が truncate でしか説明できない = **AI の書き手は 1 つの文書の中で四捨五入と切り捨てを混ぜる**。根拠を桁(`claim_scale`)ごとに分けても、動いた 21 行の桁(10^4 が 19・10^8 が 2)の決定は round のままで、桁ごとの決定では戻らない(両方の根拠が同じ桁に在る)。
3. **試作 1: `doc_rounding=False`(1 周目だけ = 両方の帯)**: 200 本で GROUNDED を失う行 0・得る行 125、だが手元の 97 書類で UNVERIFIABLE → VALUE_MISMATCH が **232 行**(65 書類)。1 周目だけでは P26 G3 の保留(`rounded_diff_hold`。`rounding is not None` の 2 周目だけ)が消えるため。**採らない。**
4. **試作 2(この封の規則。scratchpad の clone の adapters に §1 を当て、measure の側から呼んだ。repo の file・cache には何も書いていない)**: 200 本で P29E → P30E の GROUNDED 11,137 → 11,260(+123)、**GROUNDED を失う行 0**。既存の行で GROUNDED になった行 110 = 札 真 102(VALUE_MISMATCH → 88・POINTER_NOT_FOUND → 13・UNVERIFIABLE → 1)・札 偽 8(VALUE_MISMATCH → 7・POINTER_NOT_FOUND → 1)。新しい行(札なし)で GROUNDED になった行 13。K-2 の 8 行のうち GROUNDED を失っていた 7 行は全部 GROUNDED に戻る。手元の 97 書類で動いた行 **2**(POINTER_NOT_FOUND → GROUNDED 1・VALUE_MISMATCH → GROUNDED 1。2 書類)、失う行 0。注入(土台 = P30E が GROUNDED の claim。N の便の仕掛け)は T1_VALUE 通した 1 / 263 = 0.4%(P29E と同じ)、**T8_REL 通した 28 / 1,053 = 2.7%(P29E 8 / 1,053 = 0.8%)**、T8_REL で名指して原本 854 / 1,053 = 81.1%(P29E 82.2%)。増えた 20 のうち 12 は P29E が名指して原本を返していた行。r 別: −0.03 が 12・−0.10 が 9・+0.10 が 6・+0.03 が 1。
5. **engine の留め**(HEAD `cf4a187` で `git grep -l -F <sha16> HEAD -- tests`): `vocabulary.py` `ca0367520f04cf87` 38 file・`recipes.py` `f1f344a9e2bb364a` 37 file・`comparators.py` `d8706338325e725b` 22 file。

### §0-2 司令塔の決定(人間の問い §5 の 1 への返事「君に任せる課題解決に向けて進めて」(2026-11-04)= 司令塔が (イ) を選ぶ)

1. **規則 RB(旗 `rounding_mixed_2026_11_04`)**: 1 周目の根拠(`_rounding_evidence`: (差, 桁) の列)を桁 `claim_scale` ごとに分け、**round しか説明できない件(差 < 0)と truncate しか説明できない件(差 > 桁 / 2)の両方が 1 件以上ある桁**を「混ざる桁」とする。混ざる桁の数の claim は、2 周目の結果でなく、**両方の帯(mode `"both"` = 1 周目の梯子と同じ −桁/2 .. +桁)で照らした結果**に差し替える。他の桁の claim・文字の claim・書類の決定(`decide_rounding`)・G3 の保留は 2 周目のまま。
2. **mode `"both"`**: 梯子(`vocabulary.py` と `comparators.py` の正規化の関数)の先頭に「`mode == "both"` なら `None` として扱う」1 行を挿す。`recipes._mag_trunc` は `"both"` で偽(P23 の切り捨ての絶対値の帯は混ざる桁に掛からない)。G3 `rounded_diff_hold` の `rounding is not None` は `"both"` で真(保留は残る。§0-1 の 3 と 4 の 97 書類の差がその証拠)。claim の `rounding` の欄には `"both"` が入る(出所の記録)。
3. **profile**: `P30E = dataclasses.replace(P29E, name="P30E", rounding_mixed_2026_11_04=True)`。外部の文の E 系だけ(P30 は作らない。B と同じ)。`DEFAULT_PROFILE` は "P27" のまま。旗の欄は `numbers_man_comma_2026_11_04` の直後。**既存の profile(P27〜P29E)の出力は 1 byte も変えない**(旗の既定は偽。`"both"` を渡す既存の呼び出しは無い)。
4. **外部の文の推奨**: §4 を満たせば README の推奨を P28E → **P30E** に替える(N の便の §5 の 1 の (イ) の決着。P29E は推奨にしない)。
5. 規則 T の下書きは P31 = P29 + T・P31E = P30E + T に番号を替える(未 commit)。
6. 札は付けない(前の便の札を既存の行に当てるだけ。新しい行の 13 は札なし)。
7. 含めない(人間が起きてから決める): `main` へのマージ・既定の切り替え・O の除去・札付けの便・注入の仕掛け(N.scan)の数の読みの直し。

## §1 規則 RB(engine の直し。字で固定)

- `recipes.build_raw_claims`: `if profile.doc_rounding:` の中で、`rounding, r_only, t_only = V.decide_rounding(...)` の**前**に `_first_2026_11_04 = num_claims`(1 周目の claim)を挿し、2 周目の `num_claims = _build_raw_num_claims(..., rounding, ...)` の**後**に次を挿す:
  1. 旗が偽なら何もしない。
  2. `_rounding_evidence(_first_2026_11_04)` を桁 `u` ごとに分け、各桁で `V.decide_rounding(その桁の列)` の R > 0 かつ T > 0 なら混ざる桁。
  3. 混ざる桁が 1 つ以上なら `_third = _build_raw_num_claims(sentences, facts, contexts, profile, claim_member, "both", flow_base=flow_base)`(長さは 2 周目と同じ。違えば止める)。`num_claims` の各 claim について、`claim.get("claim_scale")` が混ざる桁なら `_third` の同じ位置の claim に差し替える。
  4. `info` があれば `info["rounding_mixed_scales_2026_11_04"]` に混ざる桁の列(昇順)。
- `vocabulary.py` の正規化の梯子の関数と `comparators.py` の同じ関数: 先頭に `if mode == "both": mode = None` を挿す(それぞれ 1〜2 行)。既存の行は書き換えない。
- `vocabulary.py`: 旗 `rounding_mixed_2026_11_04: bool = False`(注記つき)、`P30E`、`PROFILES["P30E"]`。
- **当たる例**: 1 つの文書に「売上高は1,234万円(fact 12,345,678 円: 切り捨て)」と「営業利益は568万円(fact 5,675,432 円: 四捨五入)」が在り桁 10^4 の根拠が R ≥ 1・T ≥ 1 → 2 周目が round なら前者は VALUE_MISMATCH だったが、RB で両方の帯 → GROUNDED。
- **当たらない例**: 桁 10^4 の根拠が round だけの文書(R ≥ 1・T = 0)→ 混ざらない → 2 周目のまま。桁 10^6 の claim は、10^4 が混ざっていても 10^6 が混ざらなければ 2 周目のまま。根拠が 0 件の桁(束縛できた claim が無い桁)は混ざらない。文字の claim(向きの主張)は変えない。
- **当たってしまう例(代価)**: 混ざる桁では、書き手の数が fact から +0 .. +1 桁(truncate の帯)と −桁/2 .. 0(round の帯)のどちらでも GROUNDED になるので、桁の半分を超えて 1 桁未満の誤りは止まらない(§0-1 の 4: 札 偽 8 行が GROUNDED、T8_REL の通した率 0.8 → 2.7%)。

## §2 engine の範囲

### §2-1 触る file(`core/`・`extract.py`・`verify_document.py`・`registry_setup.py`・`report_customer.py` は 0 行。既存の行の書き換えは 0 行。挿入だけ)

| file | 足すもの | 行数の見込み(挿入) |
|---|---|---|
| `adapters/xbrl/recipes.py` | `build_raw_claims` に `_first_2026_11_04` の 1 行と混ざる桁の block | 12〜20 |
| `adapters/xbrl/vocabulary.py` | 旗 1 つ(注記つき)・梯子の `"both"` の 1〜2 行・P30E・`PROFILES` | 6〜10 |
| `adapters/xbrl/comparators.py` | 梯子の `"both"` の 1〜2 行 | 1〜2 |

- 試験: `tests/adapters/xbrl/test_recipes_p30e.py`(新しい file)。§1 の当たる例・当たらない例を小さい文と fact で(`test_recipes_p24` の `num_claims` の土台)。旗が偽の P29E と P30E が「当たらない」の例で同じ出力。`V.P30E` の旗・`PROFILES`・`DEFAULT_PROFILE == "P27"`・旗の欄の位置。梯子の `"both"` が `None` と同じ結果(vocabulary と comparators の両方)。G3 の保留が `"both"` でも残る例 1 本。変異で赤: 混ざる判定を R > 0 **または** T > 0 にする・差し替えを `_third` でなく 2 周目のままにする・`"both"` を `"round"` として扱う・`"both"` を梯子に通さない(全部外れる)・桁の分け方を無くす(全部まとめる)・旗の 2 行を外す・P30E の旗を偽にする。
- `verify_document.py`・`run.py` は 0 行。

### §2-2 触る枝の中の人間の決定(字も振る舞いも壊さない。新しい行は旗が真のときだけ通る block か、既存の呼び出しが渡さない `"both"` の分岐)

1. XBRL 直し §2 `doc_rounding`・`decide_rounding`(2026-10-08): 字は変えない。書類の決定と 2 周目はそのまま行い、RB は 2 周目の**後ろ**で混ざる桁だけ差し替える。
2. P23 `truncate_abs_band`(2026-10-21): `_mag_trunc` の字は変えない(`"both"` では偽)。
3. P26 G3 `rounded_diff_hold`(2026-10-21): 字は変えない(`"both"` は `None` でないので保留は残る)。
4. P27 A `written_precision_2026_10_27`: `claim_scale` の決め方は変えない(混ざる桁の鍵にそのまま使う)。
5. 梯子の関数(vocabulary・comparators。写し元 P1/P5F/P6/P7 の系譜): 既存の行は変えず、先頭に `"both"` の 1 行を挿す。`test_lineage` が梯子の字を留めていれば宣言された遷移で。
6. 読み取り N(c43517d)・O(6ac3911)・P27E の B・P22〜P28 の規則と旗: 字は変えない。
7. **既定 `DEFAULT_PROFILE = "P27"`**(人間 2026-11-03): 変えない。
8. P16〜P29 を明示した試験の数は 1 つも変えない。

### §2-3 既存の門の engine の留め(§0-1 の 5。実装の便で同じ便に宣言された遷移を足す。測った当時の値は消さない)

- `vocabulary.py`(38 file)・`recipes.py`(37)・`comparators.py`(22)の sha16 を留める門に、宣言の行 `(新しい sha16, "docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md")` を前例(N の便 c43517d)と同じ形で足す。`test_xbrl_default_p27_result.py` の `ENGINE_DECL` の numstat の上限は挿入分だけ上げ、`comparators.py` を足す(削除 0 は変えない)。
- 束ねた指紋 `adapter_xbrl_py_sha256`(前の値 `f1d97a2a…`)の新しい値と、`fixtures/frozen_bundle_sha.py` の世代 +1。profile の名前の一覧に P30E。`test_xbrl_axis3_decision.py` の `LATER_ENGINE_COMMITS` は次の便。
- 新しい門で engine の留めを定義するときは `ENGINE_LATER`・`UNTOUCHED`・`PIN_DEF`・`LATER_ENGINE_COMMITS`・`FROZEN_LATER`・`ENGINE_TRANSITIONS` を行頭の名前に使わない。
- 見込み: 直す試験 file 45〜75。

## §3 事前予測(**実装より先に固定。結果を見てから書き換えない**。外れは外れとして残す)

測り方は §5。数の正本は `fixtures/xbrl/rmix/*.json`。試作(§0-1 の 4)の再現が基本で、外れるなら実装が試作と違う。

| # | 欄 | 予測 | 外れ方 |
|---|---|---|---|
| D-1 | 旗が偽: AI の文 200 本の P27〜P29E の claims が N の便の記録(`ai200`・`claims`・`f5_claims`)と byte 一致、97 書類の P22〜P29E の出力が N の便の記録 `regress97_2026-11-04.json` の sha256 と一致 | 200 / 200・97 / 97 × 8 | 1 つでも違う(commit しない) |
| D-2 | AI の文 200 本: P29E → P30E の GROUNDED の数の差 | +110〜+135(試作 +123) | 範囲の外 |
| D-3 | AI の文 200 本: P29E で GROUNDED・P30E で GROUNDED でない行 | 0 | ≥ 1 |
| D-4 | 既存の行(P28E にもある行)で P30E で GROUNDED になった行の札: 真 / 偽 | 真 90〜110・偽 0〜12(試作 102 / 8) | 範囲の外 |
| D-5 | N の便の K-2 の 8 行のうち、P29E で GROUNDED を失っていた 7 行が P30E で GROUNDED | 7 / 7 | < 7 |
| D-6 | 混ざる桁がある本(記録の `rounding_mixed_scales_2026_11_04` が空でない本) | 60〜120(§0-1 の 2 の「書類の根拠が混ざる本 76」から見た) | 範囲の外 |
| D-7 | 手元の 97 書類: P29E → P30E で動いた行 / 失う行 | 0〜5 / 0(試作 2 / 0) | 動いた ≥ 6 または失う ≥ 1 |
| D-8 | 注入(土台 = P30E が GROUNDED): T1_VALUE 通した率・T8_REL 通した率(P30E) | T1 0.0〜1.0%・T8 2.0〜3.5%(試作 0.4 / 2.7) | 範囲の外 |
| D-9 | 注入 T8_REL で名指して原本を返した率(P30E) | 78〜84%(試作 81.1) | 範囲の外 |
| D-10 | engine の留めの連動で直す試験 file の数 | 45〜75 | 範囲の外 |

## §4 採用の基準(数で。判定は記録から門が機械で求め、司令塔は覆さない)

- **K-1** D-1 が全部一致。外れたら engine を commit しない。
- **K-2** D-3 = 0(札 真の行を落とさないだけでなく、GROUNDED を 1 行も失わない)。
- **K-3** D-4 の札 偽 ≤ 12 かつ札 真 ≥ 80。
- **K-4** D-8 の T1_VALUE ≤ 1.0% かつ T8_REL ≤ 3.5%。
- **K-5** D-7 の失う行 = 0 かつ動いた行 ≤ 5。
- **判定**: K-1〜K-5 を全部満たす → **採用**: README の「外部の数の文に使う profile」の推奨を P28E → **P30E**(既定は P27 のまま)。1 つでも外れ → engine には残しても推奨は替えず、人間に返す。

## §5 測り方(全部 0 USD)

- `measure/xbrl_rmix_2026-11-04.py`: N の便の script(`xbrl_numfix_2026-11-04.py`)を同じ instance で読み込み、profile の組を (P29E, P30E) に差し替える(judge: 鍵は (文の番号, 位置)。既存の行は N の便の `claims`・`f5_claims` の P27 の並びで id に結び、`labels`・`f5_labels` の札を当てる。inject: `INJECT_PROFILES = ("P29E", "P30E")`。D-1 の byte 一致は N の便の記録と比べる)。記録 `fixtures/xbrl/rmix/ai200_2026-11-04.json`・`inject_2026-11-04.json`。
- `measure/xbrl_rmix_regress97_2026-11-04.py`: N の便の regress97 の作りで P22〜P30E(byte 一致は N の便の記録の sha256 と)。記録 `fixtures/xbrl/rmix/regress97_2026-11-04.json`。
- 門 `tests/measure/test_xbrl_rmix_seal.py`(封の字・順序 封 ⊏ engine ⊏ script)・`tests/measure/test_xbrl_rmix_result.py`(D-1〜D-10・K-1〜K-5 を記録から機械で。結果の文書 `docs/XBRL_ROUNDING_MIXED_ENGINE_RESULT_2026-11-04.md` の 2 表を照らす。変異で赤)。`LATER_NAMING_FILES` に記録 3 つ。覆いの数を直す。

## §6 言えないこと

1. 注入の仕掛け(`N.scan`)は万・億のコンマの数を断片に切るので、D-8・D-9 は新しく読めた数に注入した誤りを測っていない(N の便と同じ)。
2. 新しい行 13 に札は無い。D-4 は既存の行だけ。
3. 代価(§1)の「桁の半分を超えて 1 桁未満の誤り」は、有報の原文では混ざる桁がほぼ無いので(D-7)掛からないが、AI の文では掛かる(D-8 の T8_REL)。どちらを重く見るかは人間の判断で、§4 の K-4 の上限 3.5% は司令塔が置いた数。
4. 200 本は Claude の model 2 つが書いた文。他の書き手が丸め方を混ぜるかは測っていない。

## §7 作法と順序

1. この封を commit(文書だけ)→ 実装(step-implementer、worktree。engine の差分は §2-1 だけ)→ 試験と変異 → 留めの連動 → 独立監査 GO → engine の commit(パス指定)。
2. 測定 script 2 本と門 2 本 → 監査 GO → commit → 記録 3 つ → 結果の文書 → 監査 GO → commit。採用なら README の推奨の字を替える(文書だけ)。
3. 使わない: `git add -A`・`stash`・`reset`・`checkout`。cache に file を足さない。`edinetdb-p27`・`sgogi-coach-handoff` は開かない。
