# 封: 注入の仕掛けの T5(値が偶然一致して参照先が違う)を円族の数に作れるようにする T5Y ― 切り替え `t5_yen_2026_11_06`(measure/lib と measure/inject.py だけ。engine 0 行)― 2026-11-06

前の便: H(封 89afc79 → lib db41631 → 結果 e93cf95。仕掛けの数の読みに 万円・億+万 を足した)、J(封 edad5cd → 結果 955f2b9。T5 は注入せず: 偽 0 / 真 672 で真の 672 は全部相手の単位が None か 円 = 意味の無い偶然一致)。T5 は「値だけを探す照合は通り、参照先を解いてから比べる照合だけが止める」既知の一番の穴で、看板(出所に縛る)の裏づけに直結する型だが、**円族の数では 1 件も作れていない**。

## §0 材料と決めごと

### §0-1 測った事実(この封を書く前に司令塔が 0 USD で数えた。engine の判定は 1 回も呼んでいない。script は scratchpad/numfix/t5y/probe_t5y.py)

1. 欠陥は 2 か所。(ア) `measure/lib/sites.py` `t5_sites`: 規模の篩 `lo, hi = t.value / 10, t.value * 10` と「値が違う」`abs(o["value"] - t.value) > TOL` が**書かれた単位の値**(「12.3億円」なら 12.3)と**円の参照の値**を比べる。円族の token では [1.23, 123] に円の fact が無いので site 0(真の 672 は単位 None の数)。(イ) `measure/inject.py` `build_t5`: `cand = other["value"]` を倍率で割らずに `N.render_value(cand, t)` で描く(「12.3億円」に 1,433,000,000 を描くと「1433000000億円」)。
2. 切り替え `yen_scan_2026_11_05` 真の AI の文 200 本で、篩と値の比べを円に直す(`S._scaled(t.value, t.unit)` を使う。倍率・相手の単位の条件は現行のまま)と **site 1,007**(本 154。複合 629・万だけ 89・既存 289。単位 万円 719・億円 280・百万円 8)。相手の候補の和 286,550。相手の値を倍率で割って token の形で描き、読み直した円の値が相手の値と**書かれた桁の半分**(複合は最後の位の単位、少数は小数の桁、整数は 1 × 倍率)以内で、元の字と違い、元の値からも桁の半分より離れる site **979**(複合 629・万だけ 89・既存 261)。読み直せない 28(既存)。現行の `t5_sites` は同じ 200 本で 672(全部単位 None か 円 の相手)。
3. 前例の率: 有報の便(2026-10-20)で Core の T5 の通した率は低く、値検索は 0%(記憶 core-names-the-referent-value-search-cannot)。AI の文では未測。

### §0-2 司令塔の決定(人間の言葉「それで任せる進めて」2026-11-06 = 司令塔の意見 1〜7 の順で進める委任。4 = T5 の仕掛け)

1. 直しは **切り替え `t5_yen_2026_11_06 = False`**(`measure/lib/sites.py`。H の `yen_scan_2026_11_05` と同じ作り)の後ろだけ。偽なら `t5_sites`・`build_t5` は 1 byte も振る舞いを変えない(K-1)。真は測定 script の process の中だけ。
2. 真のとき: (ア) `t5_sites` は篩と「値が違う」を円で比べ、さらに**相手ごとに**「倍率で割って token の形で描き、`N.scan(描いた字 + 単位)` で読み直すと token 1 つで、円の値が相手の値と書かれた桁の半分以内、描いた字が元の字と違い、読み直した値が元の値から桁の半分より離れる」相手だけを `others` に残す(残らなければ site にしない)。(イ) `build_t5` は `cand = other["value"] / (SC.scale_of(t.unit) or 1)` を描き、`new_value` は描いた字を読み直した値(token の単位)、`detail` に `coincident_ref_key`・`replacement_value`(円)を持つ。相手の単位の優先(`pool`)と乱数は現行のまま。
3. 測定は土台 P30E・比較 P29E(J と同じ。P32E は別の便)。注入後の claim は**基準の claim の id で引く**(T9 の第 2 便の 3 条件)。cap 型 1 本 10。
4. 委任に含めないもの: engine・既定 P27・main・O・規則 T・T7 の帯幅。

## §1 測り方の字

1. **site**(切り替え 真): §0-2 の 2 の (ア)。並べ替えは T9 と同じ(start の順 → `random.Random("%s|%s|T5_COINCIDENT" % (seed, 本の名前))` → 土台 P30E GROUNDED を先頭から cap)。「採った」= Σ min(cap, 作れる site)。
2. **注入**: `IJ.apply_edits`・`IJ.revert`(round-trip は止めずに数える)。差し替えは `[token.start, token.end]`(単位の字は触らない)。
3. **行の欄**: id・型・形・単位・基準の claim・P29E の土台に対応・round-trip・読み直し・先頭の位が減った・届いた(id で引いた claim の span に描いた字)・相手の fact の期(coincident_ref_key の context の先頭: CurrentYear / Prior1Year / 他)・相手と同じ要素か(要素名は記録に持たず真偽だけ)・基準の pointer の期・注入後の pointer の期(P30E)・注入後の pointer が相手の fact と同じか(真偽)・P29E・P30E(`TUNE.classify`)。文・span・会社名・要素名は持たない。
4. **本ごとの数え**: 切り替え 偽の site 数・真の site 数(形別)・読み直せる site・採った・土台の状態。集計は J と同じ 2 本 + 形別 + 相手の期別の通した率 + 通した行の「相手の fact と同じ pointer」の内訳。

## §2 範囲

### §2-1 触る file
- `measure/lib/sites.py`(切り替え・`t5_sites` の真の枝。既存の行の書き換えは 0 行、挿入だけ)・`measure/inject.py`(`build_t5` の真の枝。挿入だけ)・`measure/tests/test_t5_yen.py`(新しい file。偽で不変・真の篩と描き・読み直し・変異)。
- 新しい: `measure/xbrl_t5y_2026-11-06.py`(inject・tally)、`tests/measure/test_xbrl_t5y_seal.py`・`tests/measure/test_xbrl_t5y_result.py`、記録 `fixtures/xbrl/t5y/inject_2026-11-06.json`、結果 `docs/XBRL_T5_YEN_RESULT_2026-11-06.md`。`LATER_NAMING_FILES`・`LATER_HARNESS_FILES`・覆いの数。
- 触らない: `core/`・`adapters/`・`measure/lib/numbers.py`・`scales.py`・前の便の script・記録・門。

### §2-2 触る枝の中の人間の決定
- 2026-10-08 の仕掛けの独立実装(`adapters/xbrl` を使わない)・`MAGNITUDE_RATIO = 10`・相手の label が違う条件・単位の優先: 字は変えない。
- H の採用(E 系の注入の測定は `yen_scan_2026_11_05` 真で。lib の既定は偽)・種 `measure/SEED.json` は不変。

### §2-3 既存の門の留め
- lib の指紋(`numbers.py`・`scales.py`)は変わらない(触らない)。`sites.py`・`inject.py` の指紋を留める門があれば、H の便(db41631)と同じ形で宣言された遷移を足す(測った当時の値は消さない)。`tests/measure/test_xbrl_inject_harness_review.py` の経路の表に T5Y の行。

## §3 事前予測(実装より先に固定。結果を見てから書き換えない)

| # | 欄 | 予測(幅) | 外れ方 |
|---|---|---|---|
| Y-1 | 切り替え 偽: 200 本の `t5_sites` の数と、J の記録(T5 偽 0 / 真 672)・H の記録の T1・T8 の site 数が一致 | 672・一致 | 1 つでも違えば偽の経路が変わった。記録を採らない |
| Y-2 | 真: 作れる site(計 / 複合 / 万だけ / 既存)と、うち読み直せる site | 950〜1,030 / 600〜660 / 80〜100 / 250〜300、読み直せる 940〜1,000 | §0-1 の 2 と違う方向 |
| Y-3 | 真: 採った / うち土台 P30E が GROUNDED の行(注入の行) | 500〜900 / 300〜700 | 幅の外(cap の効きは下調べで数えていない。幅は広い) |
| Y-4 | 真: id で対応が付く行の割合(P30E) | 90〜100% | 90% 未満 = 数の個数が変わる差し替えがある |
| Y-5 | 真: 通した率(P30E。分母 = 対応が付く行)と、止めた行のうち 名指して原本 の割合 | 3〜20%、60〜95% | 20% 超 = 値の偶然一致を engine が通す(看板の裏づけの負け)。幅の外 |
| Y-6 | 真: 通した行のうち注入後の pointer が相手の fact(coincident_ref_key)と同じ行の割合 | 70〜100% | 70% 未満 = 通した理由が偶然一致ではない |
| Y-7 | 真: round-trip 不一致 / 読み直し不一致 / 届かない行(対応が付く行の中) | 0 / 0 / 0 | 1 以上 |
| Y-8 | 真: P29E と P30E で判定が違う行(両方に対応が付く行) | 0〜10 | 11 以上 = 丸め方の帯が効く |
| Y-9 | 真: 相手の fact の期が CurrentYear の行の通した率 / Prior1Year の行の通した率 | 両方 3〜25% | 幅の外 |
| Y-10 | `measure/tests/test_inject.py` の既存の試験が偽のまま全部緑、足した試験が変異(切り替えを外す・篩を書かれた値に戻す・描きを倍率で割らない・読み直しを外す・相手の単位の優先を外す)で赤 | 失敗 0・赤 5 / 5 | 黙った変異 1 本以上 |

封の席の偏り: Y-5 の幅は有報の便の記憶(値検索 0%・Core は名指して止める)から置いたが、AI の文では相手の fact が同じ要素の別の期・別の枠(NonConsolidated)になりうる(§1 の 3 の「相手と同じ要素か」の欄で分ける)。同じ要素の別の期は engine が結びうるので上に外れうる。

## §4 採用の基準

判定は記録から門が機械で求め、司令塔は覆さない。

- K-1: Y-1 が一致(偽のときの不変)。
- K-2: Y-7 の round-trip 不一致 0・読み直し不一致 0。
- K-3: 注入の行 ≥ 300(仕掛けが円族の数に届いている)。
- K-4: Y-10 が 失敗 0・赤 5 / 5。

K-1〜K-4 を全部満たせば「採用」= 切り替えは既定 偽のまま仕掛けに残り、以後 E 系の注入の測定は真で T5 も注入する。README の P30E の推奨の行に T5 の通した率(負けなら負けの側)を 1 文足し(文書だけ)、台帳に L・D・P の行。Y-5 が 20% を超えても採用は採用(測った事実)。

## §5 測り方(全部 0 USD)

- `measure/xbrl_t5y_2026-11-06.py`: T9 の第 2 便の script(`xbrl_pswap_idmap_2026-11-06.py`)を importlib で読み込み(PI → PS → JT → NS → RM・NF・RUN・GEN・TUNE・IJ・N・S・SC を同じ instance で)、`NS.yen_scan_on()` と `t5_yen_on()`(新しい context manager。切り替えを with の中だけ真)の中で §1 のとおり注入。`--procs`・`--only <docID>`・`--out`。`tally` は封の字から幅を読んで Y-1〜Y-10・K-1〜K-4 を判定し 2 表。
- 門 `tests/measure/test_xbrl_t5y_seal.py`・`tests/measure/test_xbrl_t5y_result.py`(前例の作り。欄は行から数え直す。変異で赤。偽で不変の門は H の `offcheck` の形で J の記録と照らす)。

## §6 言えないこと

1. 「通した」「止めた」は engine の state で、札(人の目)は無い。
2. 相手の fact は label が違う参照から選ぶ(現行の条件)。同じ要素の別の期・別の枠も入りうる(欄で分けるが除かない)。
3. 200 本は Claude の model 2 つが書いた文。母集団は `identified_sites`(値が一致する参照がちょうど 1 件 + 単位か label の裏づけ)の数だけ。
4. 読み直せない 28 site(既存)の理由は読んでいない(site にしないだけ)。

## §7 作法と順序

1. この封を commit(文書だけ。fresh_seal・facts・boundary の門を走らせてから)→ lib と inject.py の切り替え + 試験 + 測定 script + 門(step-implementer、worktree。PB の engine の commit の後の HEAD から)→ 変異 → 独立監査 GO → commit(パス指定)→ 記録 1 つ(本番)→ 結果の文書 → 門 → 監査 GO → commit → README の 1 文 → 台帳 → 監査 → commit。
2. 使わない: `git add -A`・`stash`・`reset`・`checkout`。cache に file を足さない。`edinetdb-p27`・`sgogi-coach-handoff` は開かない。鍵は全部 unset。
