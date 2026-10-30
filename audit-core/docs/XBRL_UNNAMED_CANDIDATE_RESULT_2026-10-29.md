# 測定: 候補の欄(`candidate`)を足した engine は、他を壊さず、止めた行にだけ候補を付けるか ― 2026-10-30

封: [docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md](XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md)(commit `0df5222`)の §3(CA-1〜CA-11)・§4(K-1〜K-4)・§7-5 と、その承認の追記(commit `db68a2c`。人間 2026-10-30 の決定: 欄を足す・(イ)で `P27C` を登録し明示したときだけ・客向けの報告は案 A)。前の診断は [docs/XBRL_UNNAMED_FACT_DIAG_2026-10-29.md](XBRL_UNNAMED_FACT_DIAG_2026-10-29.md)(記録 `fixtures/xbrl/unnamed_fact_2026-10-29.json`)。
記録は `fixtures/xbrl/unnamed_candidate_2026-10-29.json`(`measure/xbrl_unnamed_candidate_2026-10-29.py` の出力。docID と claim の id はここにだけ在る)。門 `tests/measure/test_xbrl_unnamed_candidate_result.py` が、この文書の表を記録から作り直した表と一行も違わないこと、CA-1〜CA-11 の当否と K-1〜K-4 の判定を封の字と記録から求め直した結果と一致させること、を縛る。
**この便の測定は engine(`core/`・`adapters/`)を 0 行も変えていない(engine は 0 行)。** 測ったのは段 1 の席が実装した engine(未 commit の変更。旗 `unnamed_candidate_2026_10_29`・登録した `P27C`・Claim の欄 `candidate`・客向けの報告の `candidate_ja`)で、比べる側は `020ffc0` の engine を `git archive` で取り出した写し(別の process)。既存の記録は書き換えていない。0 USD・通信なし・鍵は読まない・席(LLM)は呼ばない。評価用・調整用(`edinetdb-p27`)は開いていない。【門なし】
**門の外の散文は数を持たない**(持つ行には【門なし】の印をつける。門は印の有無を字面で見る)。数は `<!-- 門:start 名前 -->` の表の中だけ。
**候補の正しさは測っていない**(封 §4)。候補は「止めた行で道具が見ていた fact」で、文の言う数の出所として正しいかは誰も見ていない。この文書の「同じ」は字の一致で、人の目は入っていない。候補を出す是非はすでに人間が決めた(承認の追記)。この便で決めるのは「旗が偽なら何も変わらず、旗が真なら止めた行にだけ付くか」だけ。

## 1. 予測 CA-1〜CA-11 の当否(先頭。外れは外れのまま)

<!-- 門:start pred -->
| # | 欄 | 予測(封の字) | 外れ方(封の字) | 実測(記録から) | 当たり外れ |
|---|---|---|---|---|---|
| **CA-1** | 旗が偽の恒等(97 書類の原文。P22・P27 の 2 profile) | 欄を落とした出力の sha256 が今の出力と **97 / 97** 書類で一致(2 profile とも)。`candidate` は全行 `None`(claims 7,799 + 3,923 = 11,722 行で辞書の行 **0**) | 1 書類でも違う / 辞書の行 1 以上 | 欄を落とした出力の sha256 が比べる側と一致: P22 97 / 97・P27 97 / 97。旗が偽の profile(P22・P27・30 書類は P27E も)の辞書の行 0。P27 の claims 11722 | **当たり** |
| **CA-2** | 旗が真の 4 state(97 書類。P27 に旗を立てた profile) | 書類ごとの 4 state が `regress97` の P27 と **97 / 97** で同じ。行ごとの state・reason・pointers・recomputed が旗が偽の出力と **11,722 / 11,722** で同じ。欄を落とした出力の sha256 も **97 / 97** で今の出力と一致 | 1 行でも違う | 4 state が regress97 の P27 と 97 / 97。行ごと(5 欄)が旗が偽の P27 と 11722 / 11722・比べる側の P27 と 11722 / 11722。欄を落とした出力の sha256(§3 の字)が比べる側の P27 と 0 / 97(`profile` も除くと 97 / 97。封 §6-4 の補い。判定は §3 の字) | **外れ** |
| **CA-3** | 候補が付く行 = `no_same_value` の行(旗が真。30 書類) | 辞書の行 **296**、`reason == "no_same_value"` の行 **296**、両方の集合が同じ。`no_same_value` で候補が `None` の行 **0**、`no_same_value` でなく候補が辞書の行 **0** | どれかが違う | 新しい標本 30: 辞書の行 296・no_same_value の行 296・両方 296。no_same_value で候補が None の行 0・no_same_value でなく辞書の行 0 | **当たり** |
| **CA-4** | 候補が付く行(旗が真。67 書類) | 辞書の行 = `no_same_value` の行で **560 以上 590 以下**(見込み 575。§0-3)。食い違う行 **0** | 幅の外 / 食い違い 1 以上 | 手元の 67: 辞書の行 575・no_same_value の行 575・両方 575。食い違う行 0 | **当たり** |
| **CA-5** | 候補の中身(30 書類。無改変) | `candidate.pointer` が診断の記録 `unnamed_fact_2026-10-29.json` の `plain_rows` の同じ (書類, id) の `named` と **296 / 296** で同じ字、`candidate.value` が `named の value` と **296 / 296** で同じ。`basis` は全部 `no_same_value` | 1 行でも違う | pointer が診断の named と 296 / 296・value が named の value と 296 / 296・basis が no_same_value 296 / 296 | **当たり** |
| **CA-6** | 注入 741 行(旗が真の P27 を、診断の便と同じ配線 `RE.work_doc` で観測) | state・reason・pointers が記録 `stop_reason_2026-10-29.json` と **741 / 741** 同じ。候補が辞書の行 **156**(T1 2・T2 32・T5 92・T3 30)で、その pointer が記録 `unnamed_fact` の `rows` の `named` と **156 / 156**、= 原本の基準の先頭(T1・T2・T5)**126 / 126**、= P22 の注入後の先頭(T3)**30 / 30**。候補が `None` の行 **585** | どれかが違う | state・reason・pointers が stop_reason の P27 と 741 / 741。候補が辞書の行 156(T1 2・T2 32・T5 92・T3 30)で、pointer が診断の named と 156 / 156・原本の基準の先頭と 126 / 126(T1・T2・T5)・P22 の注入後の先頭と 30 / 30(T3)。候補が None の行 585 | **当たり** |
| **CA-7** | 旗が真の P27E(30 書類) | 候補が辞書の行 = P27E の `no_same_value` の行 = **296 − 24 = 272**(B が名指した 24 行に候補は付かず、その 24 行は VALUE_MISMATCH で `pointers` に出る)。候補が付く行と B が名指した行の積 **0** | 幅の外(± 0。字で 272)/ 積 1 以上 | P27EC(30 書類): 候補が辞書の行 272・no_same_value の行 272(P27 の no_same_value は 296)。B が動かした行 24(うち VALUE_MISMATCH 24)。候補が付く行と B が動かした行の積 0 | **当たり** |
| **CA-8** | 客向けの報告(旗が偽。97 書類。既定と `--full`) | `render_markdown` の本文が今の出力からの本文と **97 / 97 × 2** で byte 一致(案 A でも B でも) | 1 本でも違う | 旗が偽の本文が比べる側と byte 一致: 既定 97 / 97・--full 97 / 97 | **当たり** |
| **CA-9** | 既存の golden(`test_report_customer.py`) | `SMALL_GOLDEN`・`UNITS_GOLDEN`・`GOLDEN_SHA256` の 4 値は、案 A でも B でも**今の値のまま緑**(入力に `candidate` の欄が無い) | 1 本でも赤 | 既存の golden の試験(db68a2c の test_report_customer.py に段 1 の engine を当てた)は赤 0 本。SMALL_GOLDEN・UNITS_GOLDEN・GOLDEN_SHA256 の 4 値は今の値のまま緑(段 1 の席と、使い捨て clone での測り直し)。golden の 3 定数の字が比べる側の commit と同じ: はい | **当たり** |
| **CA-10** | 客向けの報告(旗が真・案 A。30 書類) | 今の本文と違う行は「要確認」の表の行だけで、その数 = 候補が辞書の行 **296**(書類ごとに同じ数)。違う行の全部が「。候補: 」の字を 1 回だけ持つ。既定と `--full` で違う行の数は同じ | 他の節に差 / 数が違う | 違う行: 既定 296・--full 296(「。候補: 」を 1 回だけ持つ行 296・296、候補の節を除くと比べる側の行と同じ行 296・296、「要確認」の見出しの下の表の行 296・296)。書類ごとに 候補が辞書の行と同じ数: 30 / 30 | **当たり** |
| **CA-11** | 既存の試験の赤(engine の留め以外) | `test_verify_entry.py` の本体の sha256 の **5 本**が赤((ア)(イ)とも。欄が増えるため)。`test_vocabulary.py` の `PROFILES` の一覧 **2 本**は(イ)なら赤・(ア)なら緑。`test_recipes_p27.py` の等式 **1 本**は(ア)なら赤・(イ)なら緑。`test_report_customer.py` は **0 本**(CA-9)。`tests/measure` の 37 file は §2-3 の型どおり赤(数は予測しない) | 数が違う / 別の file が赤 | tests/adapters/xbrl(db68a2c の試験に段 1 の engine を当てた。test_mutations は別に走らせた)の赤は 21 本: test_verify_entry の本体の sha256 が 5 本(予測どおり)・test_vocabulary が 3 本(予測は 2 本)・test_recipes_p27 が 2 本(予測は 0 本)・旗の継承の一覧を字で持つ別の file の試験が 11 本(test_p17 1・test_p20 1・test_recipes_p21 1・p22 2・p23 2・p24 1・p25 2・p26 1。予測に無い file)。test_report_customer は 0 本(予測どおり)。tests/measure(同じ条件。使い捨て clone で全部走らせた)の赤は 37 file・91 本で、file の集合は封 §2-3 の和集合と同じ(予測どおり。本数は予測しなかった) | **外れ** |
<!-- 門:end -->

外れた予測: CA-2・CA-11。外れは外れのまま残す(封も予測も直さない)。【門なし】

11 本のうち 9 本が当たり、2 本(CA-2・CA-11)が外れた。当たりのうち CA-3・CA-5・CA-6 は診断の記録の再現で、封が先に「外れるなら実装が provenance の鍵をそのまま写すのと違う」と書いた欄である。本当に外れうると封が書いた CA-4・CA-7・CA-10 は当たり、CA-11 は外れた。当たりの数を予測の良さの証拠にしない。【門なし】
CA-2 は三つの節のうち第 3 節(欄を落とした出力の sha256 が比べる側と一致)が外れた。(イ)の形(`P27C` を登録)では出力の `profile` の字が `P27C` になり、比べる側の `P27` と字が違うため一致しない。封 §6-4 が試作の時点で先に外れの側と書いた分で、`profile` の欄も除いた sha256 は並べて記録し、全書類で一致している(表 pred の CA-2 の実測)。第 1 節(4 state)・第 2 節(行ごとの一致)は当たった。当否は §3 の字で判定したので CA-2 は外れのまま残す。【門なし】
CA-11 は、段 1 の試験の結果を測り直した事実で外れた(`tests/adapters/xbrl` の赤は 21 本で、封が数えた 7 本(test_verify_entry の 5 本と test_vocabulary の 2 本)より多く、別の file も赤になった)。外れた中身は、`test_vocabulary` の登録簿の一覧の赤が 2 本でなく 3 本、`test_recipes_p27` が緑でなく 2 本赤、旗の継承の一覧を字で持つ別の file(`test_p17`・`test_p20`・`test_recipes_p21`〜`p26`)が赤、の三つ。封は「旗が偽の profile だけが旗を持つ」の形の試験が新しい旗を見ないと読んだが、一部は profile の一覧と旗の一覧を総なめしていた。外れの向きは一方向(予測より赤が多い)。`tests/measure` の赤は封 §2-3 の和集合の 37 file とちょうど同じ file(予測どおり。本数は予測しなかった)で、この part は外れていない。【門なし】
CA-9 は段 1 の席の結果と、使い捨て clone で db68a2c の `test_report_customer.py` に段 1 の engine を当てた測り直しで、赤 0 本・golden の 3 定数の字は比べる側の commit と同じ(門はこの字の同一だけ見る)。【門なし】

## 2. 採用の判定(K-1〜K-4。記録から門が機械で求め、司令塔は覆さない)

<!-- 門:start adopt -->
| # | 基準(封 §4 の見出し) | 基準(封 §4 の字) | 実測(記録から) | 満たすか |
|---|---|---|---|---|
| **K-1** | 4 state の後退 0 行 | CA-2 の行ごとの state・reason・pointers・recomputed の一致 11,722 / 11,722。 | 行ごとの一致 11722 / 11722(旗が偽の P27 と)・11722 / 11722(比べる側の P27 と)。4 state が regress97 の P27 と 97 / 97 | はい |
| **K-2** | 741 行の state 不変 | CA-6 の 741 / 741。 | 741 行の state・reason・pointers が stop_reason の P27 と 741 / 741 | はい |
| **K-3** | 旗が偽で恒等 | CA-1 の 97 / 97(2 profile)と CA-8 の 97 / 97 × 2。 | 欄を落とした出力の sha256 が比べる側と一致: P22 97 / 97・P27 97 / 97。旗が偽の辞書の行 0。報告の本文が byte 一致: 既定 97 / 97・--full 97 / 97 | はい |
| **K-4** | 候補は `no_same_value` の行にだけ、その行の全部に付く | CA-3 の食い違い 0・CA-4 の食い違い 0。 | 食い違う行: 新しい標本 30 で 0(no_same_value で候補が None 0・no_same_value でなく辞書 0)、手元の 67 で 0(0・0) | はい |
| **採用** | K-1〜K-4 の全部 | 全部を満たすとき(封 §4) |  | はい |
<!-- 門:end -->

採用する。K-1〜K-4 が全部満たされた(候補の欄を engine に残す。旗が偽なら何も変わらない。実装の commit は独立監査の GO の後)。【門なし】

「旗が偽なら何も変わらない」は、封 §5-1 の 4 のとおり**欄 1 つ(全部 `None`)を除いて**の意味である。欄は常に在る(13 欄目、末尾)ので、出力 JSON の sha256 をそのまま留めた門・記録は旗の真偽に関わらず動く。この測定の K-3 は「`candidate` と `engine` を除いた JSON の sha256」で比べた。【門なし】
CA-4・CA-7・CA-10・CA-11 は採用の判定に使わない(封 §4)。【門なし】

## 3. 配線

比べる側は `020ffc0` の `adapters`・`core` を `git archive` で取り出し、`adapters/xbrl` の `.py` が commit の blob と byte 一致かを確かめてから、同じ script を `CAND_ENGINE_ROOT` を替えた別の process で走らせた。97 書類(手元の 67 と新しい標本 30)の原文で、いまの engine は P22・P27(旗が偽)・P27C(旗が真)を、30 書類だけ P27E と P27EC(`replace(P27E, name="P27EC", 旗=True)` を実行中だけ `V.PROFILES` に差し込み、`finally` で戻した)も走らせた。【門なし】
注入の 741 行は、診断の便と同じ配線(止めた理由の script を読み込み、`RE.work_doc` を書類ごとに呼ぶ。自分では注入の規則・対応付けを書かない)で、観測する profile を P22・P27・P27C にした。入力の記録は `stop_reason_2026-10-29.json`(P27 の注入後の claim)と `unnamed_fact_2026-10-29.json`(候補の中身の照らし先)。配線の数は次の表(門が `regress97`・`stop_reason`・`fetched` から自分で数え直して一致を見る)。【門なし】

<!-- 門:start wiring -->
| 配線の門 | 値 |
|---|---|
| ZIP の sha256 が p26・fetched・regress97 と一致(97 書類) | はい |
| 比べる側の P22・P27 の 4 state が regress97 と一致した書類 | 97 / 97 |
| いまの engine の P22・P27(旗が偽)の 4 state が regress97 と一致した書類 | 97 / 97 |
| いまの engine の P27E(旗が偽。30 書類)の 4 state が regress97 と一致した書類 | 30 / 30 |
| 標準ラベルを名簿どおりに読んだ file | 3 / 3 |
| 741 行: 前の便の門(4 欄とも一致) | 741 / 741 |
| 741 行: 注入の件数の組 | 120 / 120 |
| 741 行: P27(旗が偽)の claim が stop_reason と一致した行 | 741 / 741 |
| 741 行: P27C の claim が stop_reason の P27 と一致した行(10 欄) | 741 / 741 |
| 741 行: P27C の state・reason・pointers が stop_reason の P27 と一致した行 | 741 / 741 |
| 741 行: id の集合が記録と同じ | はい |
| 全書類の記録 | はい |
| 配線の門が通った | はい |
<!-- 門:end -->

## 4. engine の sha16(測った時点)

段 1 の席の実装で動いたのは `vocabulary.py`(旗 1 つと `P27C` の登録)・`verify_document.py`(Claim の欄 `candidate`)・`report_customer.py`(`candidate_ja`)の 3 file で、他の 4 file と `core/` は `020ffc0` と同じ字である。比べる側の値は門が `git show` で引き直す。DEFAULT_PROFILE は P27 のまま。【門なし】

<!-- 門:start engine -->
| 項目 | 値 |
|---|---|
| `adapters/xbrl/extract.py` の sha16(いまの engine) | `3cf55966f12919f0` |
| `adapters/xbrl/extract.py` の sha16(比べる側 020ffc0) | `3cf55966f12919f0` |
| `adapters/xbrl/vocabulary.py` の sha16(いまの engine) | `7fbcfbf0e472f366` |
| `adapters/xbrl/vocabulary.py` の sha16(比べる側 020ffc0) | `514ebb8104451c07` |
| `adapters/xbrl/recipes.py` の sha16(いまの engine) | `52d645e713c53c1c` |
| `adapters/xbrl/recipes.py` の sha16(比べる側 020ffc0) | `52d645e713c53c1c` |
| `adapters/xbrl/resolve.py` の sha16(いまの engine) | `a41043763c1d4073` |
| `adapters/xbrl/resolve.py` の sha16(比べる側 020ffc0) | `a41043763c1d4073` |
| `adapters/xbrl/comparators.py` の sha16(いまの engine) | `d8706338325e725b` |
| `adapters/xbrl/comparators.py` の sha16(比べる側 020ffc0) | `d8706338325e725b` |
| `adapters/xbrl/verify_document.py` の sha16(いまの engine) | `6c76c8ade6c7b1c8` |
| `adapters/xbrl/verify_document.py` の sha16(比べる側 020ffc0) | `c3791080ab5aef2f` |
| `adapters/xbrl/report_customer.py` の sha16(いまの engine) | `bdbaa00a419219fe` |
| `adapters/xbrl/report_customer.py` の sha16(比べる側 020ffc0) | `6679138d350ec382` |
| DEFAULT_PROFILE | P27 |
<!-- 門:end -->

## 5. 数(CA の内訳)

候補の行の数は、書類ごとの数でなく行の一覧(`候補の行`)から門が数え直す。候補は `reason` が `no_same_value` の行だけに付き、その行の全部に付いた(食い違い 0 は表)。【門なし】

<!-- 門:start counts -->
| 項目 | 値 |
|---|---|
| 新しい標本 30 の候補が辞書の行 | 296 |
| 新しい標本 30 の reason が no_same_value の行 | 296 |
| 新しい標本 30 の no_same_value で候補が None の行 | 0 |
| 新しい標本 30 の no_same_value でなく候補が辞書の行 | 0 |
| 手元の 67 の候補が辞書の行 | 575 |
| 手元の 67 の reason が no_same_value の行 | 575 |
| 手元の 67 の no_same_value で候補が None の行 | 0 |
| 手元の 67 の no_same_value でなく候補が辞書の行 | 0 |
| 97 書類の P27 の claims(7,799 + 3,923) | 11722 |
| 4 state の和 P22(GROUNDED・VALUE_MISMATCH・UNVERIFIABLE・POINTER_NOT_FOUND) | 6384・2087・2013・1238 |
| 4 state の和 P27(GROUNDED・VALUE_MISMATCH・UNVERIFIABLE・POINTER_NOT_FOUND) | 6565・683・2388・2086 |
| 4 state の和 P27C(GROUNDED・VALUE_MISMATCH・UNVERIFIABLE・POINTER_NOT_FOUND) | 6565・683・2388・2086 |
| P27C の出力の profile の字が P27C の書類 | 97 / 97 |
| P27C の欄の並びが 13 欄で末尾が candidate の書類 | 97 / 97 |
| 注入 741 行で候補が辞書の行(型別 T1・T2・T5・T3) | 156(2・32・92・30) |
| 注入 741 行で候補が None の行 | 585 |
<!-- 門:end -->

## 6. 客向けの報告(案 A)

標準ラベルは `~/.cache/audit-core/edinet-taxonomy/2025-11-01` の 3 file を名簿の sha256 で照合して渡した(書類自身のラベルは渡していない)。旗が偽の本文は比べる側と byte 一致し、旗が真(`P27C`)の本文は、新しい標本 30 では「要確認」の表の行の理由の欄の末尾に「。候補: …」の 1 節が足されただけである(候補の節を除くと比べる側の行と同じ)。他の節に差は無い。【門なし】

<!-- 門:start report -->
| 項目 | 値 |
|---|---|
| 旗が偽の本文が比べる側と byte 一致(97 書類)・既定 | 97 / 97 |
| 旗が真(案 A)で本文の違う行(新しい標本 30 の和)・既定 | 296 |
| うち「。候補: 」を 1 回だけ持つ行・既定 | 296 |
| うち候補の節を除くと比べる側の行と同じ行・既定 | 296 |
| うち「要確認」の見出しの下の行・既定 | 296 |
| 行数が同じ書類・既定 | 30 / 30 |
| 旗が偽の本文が比べる側と byte 一致(97 書類)・--full | 97 / 97 |
| 旗が真(案 A)で本文の違う行(新しい標本 30 の和)・--full | 296 |
| うち「。候補: 」を 1 回だけ持つ行・--full | 296 |
| うち候補の節を除くと比べる側の行と同じ行・--full | 296 |
| うち「要確認」の見出しの下の行・--full | 296 |
| 行数が同じ書類・--full | 30 / 30 |
| 手元の 67(参考。判定に使わない)で本文の違う行・既定 | 575 |
| 標準ラベルを渡したか | 標準ラベル 3 file(名簿の sha256 で照合。書類自身のラベルは渡していない) |
<!-- 門:end -->

字の形は「。候補: <要素のラベル(無ければ要素名)>・<期>[区分: …]・<値(文の単位・桁)>」である(封 §1-3)。この文書は候補の字の良し悪し(「候補」が「道具が結んだ」と読まれないか)を判断しない。人間が見る。【門なし】

## 7. 限界・測っていないこと

1. 候補の正しさは測っていない。無改変の行に正解は無く、出せば正しい文にも候補が付く(表 counts の新しい標本 30 の和)。人の目で見る便は別の封で 1 回だけ立てる(承認の追記)。この便で決めない。【門なし】
2. CA-9・CA-11 は engine を走らせる測定でなく、既存の試験の赤の数である。CA-11 は段 1 の席の数を、使い捨て clone(db68a2c の試験に段 1 の engine を当てた)で測り直した事実を門に字で留めた。`tests/measure` の遷移は段 1 の席が宣言した(数は予測しなかった)。【門なし】
3. 報告は標準ラベルだけで描いた。書類自身のラベルを渡すと候補の要素名・区分の字が変わりうるが、違う行の数は変わらない見込みで、測っていない。【門なし】
4. 97 書類・741 行の観測で、他の書類で同じ数になるとは言えない。【門なし】
5. 重い走らせ直し(`AUDIT_CORE_*`)と `run_tests.sh` の結果は、この文書に入れない(段 1・段 2 の報告に別に書く)。【門なし】
6. 台帳(`FACTS_FOR_BUYERS_2026-10-20.md`)の行・Cabocia の紙・束には候補の欄を載せない(承認の追記の 5)。【門なし】

## 8. 次

採用の判定は第 2 節。実装(段 1)と測定(この便)の commit は独立監査の GO の後(CLAUDE.md の作法 3)。`LATER_ENGINE_COMMITS`(axis3 の門)に実装の commit を宣言するのは次の便(封 §7 の 7)。「正しさを人の目で見る便」は別の封(承認の追記の 4)、台帳 L-40 の隣の率は別の便(同 5)。【門なし】
