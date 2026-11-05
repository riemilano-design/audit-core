# 封: 注入の仕掛けの数の読みに「万円」と「億+万の複合」を足す H(measure/lib だけ。engine 0 行)― 2026-11-05

前の便: 読み取り N(封 48e7078・結果 dc2cfe7)と混ざる桁 RB(封 de23edc・結果 301d9f1)。どちらも「注入の仕掛け(`N.scan`)は万・億のコンマの数に届かない」を言えないことに残した。この封はその仕掛けを直し、**P30E の推奨の根拠(注入の 通した率・名指して原本の率)の分母に、万円で書かれた数を入れる**。

## §0 材料と決めごと

### §0-1 測った事実(この封を書く前に司令塔が 0 USD で数えた。script は scratchpad/numfix/nscan/)

1. AI の文 200 本(`aiforms-2026-11-03`・`aiforms-f5-2026-11-03` の texts)の円族の数の形(engine の読み `_MAN_COMMA_RE_2026_11_04` の当たりを位の組で分けた):

| 形 | 例 | 本数 | 注入の仕掛け `scan` の見え方 |
|---|---|---|---|
| 億+万の複合 | 12億3,456万円・1億500万円 | 5,472(コンマあり 4,921・なし 551) | 「12」「3,456」の 2 token。unit None・is_quantity 偽 → site にならない |
| 万だけ | 1,234万円・568万円 | 1,831(コンマあり 1,343・なし 488) | 1 token。unit None・is_quantity 真。値が 万 のまま円に直らず `find_base_claim` が付かない → 「基準に対応が付かない」 |
| 億だけ | 10億円・1,234億円 | 4,089 | 1 token。unit 億円(届く。変えない) |
| 兆+億 | 5兆1,234億円 | 6 | 2 token。届かない |

2. RB の便の記録 `fixtures/xbrl/rmix/inject_2026-11-04.json` の本ごとの数えの和: T1_VALUE は 作れる site 798・採った 696・基準に対応が付かない 188。T8_REL は 円族の token 5,211・作れる site 2,747・採った 1,107・基準に対応が付かない 1,152。
3. 原因: `measure/lib/numbers.py` の `UNIT_FAMILIES["money"]` と `measure/lib/scales.py` の `MONEY_SCALE` に 万円 が無い。複合の数は `is_quantity` が「位の記号の後ろに数字が続く = 複合の部品」として除く(2026-10-08 の決定。仕掛けは extractor の `AMOUNT_JP_RE` を再利用しない設計)。
4. 試作(scratchpad/numfix/nscan/proto。repo を触らない写しに規則 H を足して 200 本で数えた): 切り替え 偽 は 200 本の token 24,228 が元の `numbers.py` と全欄一致し、RB の記録の注入の行(id・型・基準の claim)と本ごとの数えも 200 / 200 本一致。真 では新しい token 7,305(億+万 5,472・万だけ 1,827・兆+億 6。is_quantity 真 7,228)、既存の token で複合に覆われて捨てたもの 10,956(is_quantity 真 0)。円族の token 5,211 → 12,443。T1 の作れる site(新しい token から)1,468・採った 761(うち P30E が GROUNDED 542)、T8 の作れる site 4,727・採った 1,217(対応 1,196)。基準に対応が付かない率は新しい token 9.4%(既存 22.1%)。新しい token の site だけへの注入(P30E): T1 通した 0 / 542・名指して原本 86.9%、T8 通した 1 / 1,196 = 0.1%・名指して原本 90.4%(P29E は T1 0 / 542、T8 0 / 1,196)。round-trip 不一致 0・読み直し不一致 0。通した 1 件は「+10万円」の差額が r = −0.1 で 9万円になり、formula の 98,000 円の切り捨て側の帯に入ったもの(桁の小さい万の数は丸めの帯が相対で広い)。所要は注入 約 20 分(procs 3)。試作の報告 scratchpad/numfix/nscan/proto_report.md に、案に無かった決め 12 点と設計の穴 6 点。

### §0-2 司令塔の決定(人間の言葉「君に任せる進めて」2026-11-05 を、司令塔が次の課題を選ぶ委任と読んだ)

1. 選んだ課題はこの H。理由: 2 便続けて「言えないこと」に残り、P30E の推奨の根拠の分母から約 7,300 の数が抜けている。engine を触らず measure/ だけで直せる。
2. **委任に含めないもの**(CLAUDE.md §6 の人間の決定): 既定 profile P27 の切り替え・main へのマージ・O を外す engine の変更・規則 T(engine)。
3. 直しは **切り替え付き**(`compound_yen_2026_11_05`、既定 偽)。偽のときの `scan`・`_unit_after`・`render_value` の出力は 1 byte も変えない。理由: `select` を記録と突き合わせて再計算する門(`test_xbrl_a_core_vs_grep_seal`・`test_xbrl_cd_seal`・`test_xbrl_hybrid_s2_material`・`test_xbrl_p27_tune`・`test_xbrl_p27_eval`・`test_xbrl_fresh_seal`・`test_xbrl_restated_prior`)と前の便の記録を壊さない。真にするのは H の測定 script の process の中だけ。
4. `measure/inject.py`(FROZEN と宣言された遷移の留めが 6 門)と `measure/lib/sites.py` は触らない。触るのは `measure/lib/numbers.py`・`measure/lib/scales.py` の挿入と、`measure/tests/test_inject.py` の試験の追加。
5. 仕掛けの独立: 規則は数詞の仕組み(兆・億・万)から書く。`adapters/xbrl/extract.py` を import しない・写さない(2026-10-08 の設計方針のまま)。

## §1 規則 H(字で固定)

切り替え `yen_scan_2026_11_05 = False`(`measure/lib/numbers.py` の module の変数。既定 偽)。偽のとき、`scan`・`_unit_after`・`unit_family`・`render_value`・`is_quantity` の出力は 1 byte も変えない。真のとき:

1. **複合の走査**: `(?<![0-9.,])(?=\d)(?:(X)兆)?(?:(X)億)?(?:(X)万)?円`(X = `\d{1,3}(?:,\d{3})+|\d+`)の当たりのうち、**万の group があるか、group が 2 つ以上**のものを 1 つの `NumberToken` にする(億だけ・兆だけの 1 group は作らない = 既存の token のまま)。`start` = 最初の group の先頭の数字、`end` = 最後の group の数字の次、`text` = その間の字(「12億3,456」)、`unit` = いちばん小さい書かれた位の単位(万 → 万円、億 → 億円)、`unit_end` = 円の次、`value` = 各 group の数 × 10^(その位の指数 − 最小の位の指数)の和(兆 12・億 8・万 4。整数で足して float)、`has_comma` = `text` に `,` があるか、`has_frac` 偽、`sentence_index` は既存と同じ引き方。新しい slot `groups` = `((位の字, その group にコンマがあるか), …)`(既存の token は None。`as_dict` は変えない)。既存の token のうち `start` が [新しい token の start, unit_end) にあるものは捨てる(「万だけ」は同じ span の置き換え)。位置順。
2. **万円 の単位**: `_unit_after` は 万円 も単位の候補に数える(元の集合 + 万円、長い順)。`unit_family("万円")` は "money"(真のときだけ。偽のとき None のまま)。`measure/lib/scales.py` の `MONEY_SCALE` に `"万円": 10000,` を字で足す(切り替えと無関係。偽のとき 万円 の unit を持つ token は無いので出力は変わらない)。
3. **描き**: `render_value(value, like)` は `like.groups` が None でなければ `render_groups` へ(None なら元の処理に 1 行も触れない)。`render_groups`: `value`(like の単位の数。`has_frac` 偽なので整数に丸める)を大きい位から divmod(位の比 = 10^(指数差))し、いちばん小さい group に余りを全部。先頭の 0 の group は落とす。先頭以外の 0 の group は「0」で描く(keep)。group ごとに like の group と同じコンマの有無(ありなら 3 桁区切り、なしなら区切らない)。描いた字は `start:end` を置き換えるだけで、単位の字は触らない。
4. **当たる例**(真のとき): 「売上高は12億3,456万円」→ token 1 つ(text 12億3,456・unit 万円・value 123456・groups ((億, 偽), (万, 真)))。「1,234万円」→ text 1,234・unit 万円・value 1234。「5兆1,234億円」→ text 5兆1,234・unit 億円・value 51234。描き: value 123458 → 「12億3,458」、value 9700(like 1億500)→ 「9,700」(先頭の 0 を落とす。like の 万 の group にコンマが無ければ「9700」)、value 10000(like 1億500)→ 「1億0」。
5. **当たらない例**: 「10億円」「1,234億円」(億だけ = 既存の token)、「1,234百万円」「105,873千円」(既存の単位)、「1,234万人」「3万株」(円が続かない。既存どおり部品として除く)、「2026年」。偽のとき全部が既存どおり。
6. `is_quantity` は複合 token にも既存の規則をそのまま掛ける(位の記号の規則は token の `end` の後ろが 円 なので除かれない)。`measure/inject.py`・`measure/lib/sites.py` は触らない。T8 の円族の filter(`TUNE.MONEY_FAMILY`)に 万円 を足すのは H の測定 script の側(`t8_candidates4` の写しを script が持ち、新しい token だけに絞る)。

## §2 範囲

### §2-1 触る file
- `measure/lib/numbers.py`: 挿入だけ(切り替え・複合 token の走査・`render_value` の位の構造の描き・`_unit_after` の 万円)。既存の行の書き換え 0。
- `measure/lib/scales.py`: `MONEY_SCALE` に `"万円": 10000,` の 1 行(字で。計算しない)。
- `measure/tests/test_inject.py`: 試験の追加(`TestMoneyScaleTable` に 万円 の行。切り替え 偽 の不変・真 の走査・描き・round-trip)。
- 新しい measure script 1 本と門 2 本(§5)。
- 触らない: `core/`・`adapters/`・`measure/inject.py`・`measure/lib/sites.py`・前の便の script・記録・門。

### §2-2 触る枝の中の人間の決定(壊さない)
- 2026-10-08(DETECTION_T2_PLAN 第 2 部 S-7): 倍率表は人が決めた数を字で留める(定数から計算しない。表の 1 行を壊すと試験が赤)。→ 万円 の行も字で足し、壊すと赤になる試験を足す。
- 2026-10-08(INJECTION_TOOL_AUDIT3_RESULT §2・`numbers.py` の注記): 仕掛けは `adapters/xbrl` を使わない独立実装。複合の部品は「推測しない」。→ H は独立に書き、推測でなく位の構造から値を決める。
- 2026-10-08 の `is_quantity` の除外規則(日付・範囲・見出し・識別子・表の 1 列目・節番号)は不変。複合 token にも同じ `is_quantity` を掛ける。
- 種 `measure/SEED.json` は不変。

### §2-3 既存の門の留め
- `measure/lib/numbers.py`・`scales.py` を sha で留める門は無い(`test_xbrl_a_core_vs_grep_seal` は `lib/sites.py` を None で持つだけ)。`measure/inject.py` は触らないので FROZEN・遷移の留めは全部そのまま。
- 切り替え 偽 の不変は、H の封の門で「RB の便の記録の注入の行(id・型・span)と `select`・T8 の候補が本ごとに一致」で留める(§3 H-1)。

## §3 事前予測(実装より先に固定。結果を見てから書き換えない)

| # | 欄 | 予測(幅) | 外れ方 |
|---|---|---|---|
| H-1 | 切り替え 偽: AI の文 200 本の token の全欄と、RB の便の記録 `inject_2026-11-04.json` の注入の行(id・型・基準の claim)・本ごとの数えが一致する本 | 200 / 200 | 1 本でも違えば外れ = 偽のときの不変が破れている。lib を commit しない |
| H-2 | 切り替え 真: 新しい token の数(億+万 / 万だけ / 兆+億)と is_quantity 真の数 | 7,250〜7,350(億+万 5,400〜5,550・万だけ 1,780〜1,880・兆+億 4〜8)、is_quantity 真 7,150〜7,300 | 試作 7,305 / 5,472 / 1,827 / 6 / 7,228 と違う方向に出れば規則の字の解釈が試作と違う |
| H-3 | 真: 円族の token(is_quantity 真) | 12,200〜12,600 | 試作 12,443 |
| H-4 | 真: T1 の作れる site(新しい token から)/ 採った / うち P30E が GROUNDED | 1,350〜1,550 / 700〜800 / 480〜600 | 試作 1,468 / 761 / 542 |
| H-5 | 真: T8 の作れる site / 採った / P29E に対応が付く行 | 4,500〜4,900 / 1,150〜1,280 / 1,130〜1,250 | 試作 4,727 / 1,217 / 1,196 |
| H-6 | 真: 新しい token の site で基準に対応が付かない率(T8) | 7〜12% | 試作 9.4%。既存の 22.1% より低い |
| H-7 | 真: 注入の通した率(P30E。分母 = P30E が GROUNDED の site) | T1_VALUE 0.0〜0.6%・T8_REL 0.0〜0.5% | 試作 0 / 542・1 / 1,196。上を超えれば「新しい数は穴」= 人間に返す材料 |
| H-8 | 真: 名指して原本を返した率(P30E) | T1 82〜90%・T8 86〜93% | 試作 86.9 / 90.4 |
| H-9 | 真: P29E と P30E で判定が違う行(新しい site) | 0〜5 | 試作 1(T8 の小さい万の数。RB の 2 帯の切り捨て側) |
| H-10 | 真: round-trip 不一致・読み直し不一致・注入後の値(円)が refs に在る行 | 0 / 0 / 0〜3 | 試作 0 / 0 / 0。refs の守り(`build_t1`)は円に直さず比べる既存の欠陥なので、円に直して数え直した値を記録に持つ |

## §4 採用の基準

判定は記録から門が機械で求め、司令塔は覆さない。

- K-1: H-1 が 200 / 200(偽のときの不変)。外れたら lib を commit しない。
- K-2: H-10 の round-trip 不一致 0・読み直し不一致 0。
- K-3: H-4 と H-5 の採った site の和 ≥ 1,500(仕掛けが新しい数に届いている)。
- K-4: `measure/tests/test_inject.py` の既存の試験が偽のまま全部緑、足した試験が変異(切り替えを外す・万円 の行を 1e3 に壊す・描きのコンマ・先頭の 0・複合の value の指数)で赤。

K-1〜K-4 を全部満たせば「採用」= 切り替えは既定 偽のまま lib に残し、外部の文(E 系 profile)の注入の測定は以後 真で行う(封にそう書く)。結果の文書に「既存の site の率(RB の記録)」と「新しい token の site の率」の 2 本を並べ、README の P30E の推奨の行に新しい site の率を 1 文足す(文書だけ)。H-7 の上限を超えたら、採用はそのままで「新しい数は穴」を人間に返す(engine の話)。

## §5 測り方(全部 0 USD)

- `measure/xbrl_nscan_2026-11-05.py`: RB の便の `xbrl_rmix_2026-11-04.py` を importlib で読み込み(NF と同じ作り)、`N.compound_yen_2026_11_05 = True` を process の中で立てて、土台 = P30E が GROUNDED、比較 = P29E で注入(T1_VALUE・T8_REL)。T8 の円族の filter は `MONEY_FAMILY + ("万円",)` を script が持つ(TUNE は触らない)。記録 `fixtures/xbrl/nscan/inject_2026-11-05.json`(新しい token の site と既存の site を分けて集計)と `fixtures/xbrl/nscan/offcheck_2026-11-05.json`(切り替え 偽 の不変)。
- 門 `tests/measure/test_xbrl_nscan_seal.py`(封の字・順序 封 ⊏ lib ⊏ script)・`tests/measure/test_xbrl_nscan_result.py`(H-1〜 と K を記録から機械で。結果の文書 `docs/XBRL_INJECT_SCAN_FIX_RESULT_2026-11-05.md` の 2 表を照らす。変異で赤)。`LATER_NAMING_FILES` に記録 2 つ、`LATER_HARNESS_FILES` に script。覆いの数を直す。

## §6 言えないこと

1. 新しい site の「通した」「止めた」は engine の state で、札(人の目)は無い。
2. T1 の置換は 1 万円の位(like の単位)で足す。万円で書かれた数に 1 円の位の誤りは入れない。
3. 複合の描き直しで先頭の位が 0 になる形(1億500万 → 9,700万)は位が減る。round-trip が合わないときは止める。
4. 200 本は Claude の model 2 つが書いた文。
5. 前の便(N・RB)の率は作り直さない(記録は不変)。H の記録に「既存の site」と「新しい site」の 2 本の率を並べる。

## §7 作法と順序

1. この封を commit(文書だけ)→ 実装(step-implementer、worktree。`measure/lib` 2 file + `measure/tests/test_inject.py`)→ 試験と変異 → 独立監査 GO → commit(パス指定)。
2. 測定 script 1 本と門 2 本 → 監査 GO → commit → 記録 2 つ → 結果の文書 → 監査 GO → commit → 台帳の行。
3. 使わない: `git add -A`・`stash`・`reset`・`checkout`。cache に file を足さない。`edinetdb-p27`・`sgogi-coach-handoff` は開かない。
