# 結果: 既定の profile を P26 から P27 に切り替えた(段 2)― 2026-10-28

封 `docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md`(commit `87f83fd`)の事前予測 S-1〜S-12 を、実装の後の作業木で測って判定する。**人間の決定**(2026-10-27「価値を上げるためにも君に任せる 進めよう」・2026-10-28「君に任せるよ」)を受けた司令塔の決定は封のとおり: 既定を P27 に替える(P27E ではない)。判定の出どころは評価用の結果 `docs/XBRL_P27_RESULT_2026-10-27.md`(commit `aeae608`)。この文書は判定は覆さない。
記録は `fixtures/xbrl/default_p27_2026-10-28.json`(`measure/xbrl_default_p27_2026-10-28.py` の出力)。結果の門 `tests/measure/test_xbrl_default_p27_result.py` が、この文書の表を記録から作り直した表と一行も違わないことと、予測の当たり外れを封の字の太字から別の関数で求め直した判定と一致することを縛る。封の門は `tests/measure/test_xbrl_default_p27_seal.py`。
**門の外の散文は数を持たない**(持つ行には【門なし】の印をつける。門は印の有無を字面で見る)。数は `<!-- 門:start 名前 -->` の表の中だけ。0 USD・通信なし・鍵の値は読まない・席(LLM)は呼ばない。この測定をした席は、評価用・調整用の AI の文・DB の応答を開いていない(docID と claim の id の字は、この文書にも門にも無い)。

## 1. 予測 S-1〜S-12 の当否(先頭。外れは外れのまま)

<!-- 門:start pred -->
| # | 予測の太字(封の字) | 外れ方(封の字) | 実測(記録から) | 当たり外れ |
|---|---|---|---|---|
| **S-1** | 0 / 67・0 / 30・97 / 97 | 1 書類でも違う / 対照が 97 / 97 でない | 違った書類 0 / 67・0 / 30。対照で違った書類 97 / 97 | **当たり** |
| **S-2** | 4,371・433・1,601・1,394・28・25・3・0・0・0・0・0・0 | 4 state のどれか 1 つでも違う / 行数か向きが違う / 集合が違う | GROUNDED 4,371・VALUE_MISMATCH 433・UNVERIFIABLE 1,601・POINTER_NOT_FOUND 1,394。state の違う行 28(POINTER_NOT_FOUND → UNVERIFIABLE 25・UNVERIFIABLE → POINTER_NOT_FOUND 3)。他の向き 0・離れる 0・VALUE_MISMATCH に入る 0・新しい GROUNDED 0・reason か pointer だけ違う 0 | **当たり** |
| **S-3** | 2,194・250・787・692・15・14・1・0・0・0・0・0 | 1 つでも違う | GROUNDED 2,194・VALUE_MISMATCH 250・UNVERIFIABLE 787・POINTER_NOT_FOUND 692。state の違う行 15(POINTER_NOT_FOUND → UNVERIFIABLE 14・UNVERIFIABLE → POINTER_NOT_FOUND 1)。他の向き 0・離れる 0・VALUE_MISMATCH に入る 0・新しい GROUNDED 0・reason か pointer だけ違う 0 | **当たり** |
| **S-4** | 2 / 243 = 0.8%・210 / 243 = 86.4%・31・340・25・33・14・2 行・1・1・0・0・`入力`・`注入`・`素の書類` の 3 つだけ | 1 つでも違う / 写しが byte 一致でない / 違う欄が増える | 通した 2 / 243 = 0.8%・止めた 210 / 243 = 86.4%・POINTER_NOT_FOUND 31。素の書類 GROUNDED 340・POINTER_NOT_FOUND 25・UNVERIFIABLE 33・VALUE_MISMATCH 14。P26 の記録と違う欄 入力・注入・素の書類 | **当たり** |
| **S-5** | 433・1,773・145・1,077・4,371 | 1 つでも違う / 「違う」の節と VALUE_MISMATCH が食い違う / 「違う」か「一致」が動く | 違う 433・要確認 1,773・対象外 145・判断しない 1,077・一致 4,371(合計 7,799) | **当たり** |
| **S-6** | 0 / 485・480・5・0 / 64・0・0 | 通した 1 以上 / 違う行の数が違う | 穴 B で通した 0 / 485 = 0.0%・止めた 480・その他 5。段 2 の材料で Core 自身が GROUNDED 0 / 64 = 0.0%。P26 の記録の P26 の欄と違う行 穴 B 0・段 2 0 | **当たり** |
| **S-7** | ≤ 8・1・1・1・16・37 | 超える / 他の file が動く / 本数が動く | `vocabulary.py` 挿入 5・削除 1。`verify_document.py` 挿入 1・削除 1。ほかで動いた file 0・`core/` 0 行。`adapter_xbrl_py_files` 16・frozen_bundle の本数 37 | **当たり** |
| **S-8** | 81 本・29 file・16 本・11 file・97・98〜105・37・17・9・18・0・記録(fixtures)の数・state を書き換えないと緑にならない門 0・0・2・7・3・0・0 | 幅の外 / 種類の外の赤 / 記録の数を書き換える門が出る / 人間の決定の字の門が赤 / P27 の門の赤の数が違う | `tests/measure` 87 本(31 file)・`tests/adapters/xbrl` 16 本(11 file)。合計 103。種類 1 が 43・2 が 33・3 が 9・4 が 18。P27 の門 5 本 result 2・seal 8・engine_result 3・eval 0・order 0。ほか 0・記録を書き換える門 0・人間の決定の字の門 0 | **外れ** |
| **S-9** | 7 本 | 増える赤が 7 でない / 実装の後に赤が残る | 実装の前の基準の木(封の commit + engine 2 file)で増えた赤 7 本。実装の後の 12 変数の赤 0 本 | **当たり** |
| **S-10** | 0 | 1 つでも違う | README の儀式の節に 通した・止めた の字: README.md 在る・README.en.md 在る。「いまの段」の P27 の行 1・P26 の行 1。`FACTS_FOR_BUYERS` の P26 の字 0・P27 の字 0 | **当たり** |
| **S-11** | 232・232・234・0 | 数が違う | 試験 file 234 本(ディスク上)・覆いの記録 234 本・覆われていない file 0 | **当たり** |
| **S-12** | 「P27 を既定の候補として記録する」 | 違う | 記録の判定の文: 判定(P27E): P27E を「外部の数の文に使う profile」として採用する。 / 判定(P27): P27 を「既定の候補」として記録する。 | **当たり** |
<!-- 門:end -->

外れた予測: S-8。外れは外れのまま残す(封も予測も直さない)。

S-8 は外れ。基準の木(封の commit の木 + engine 2 file。試験を直す前)の赤は、合計では封の幅の中に入り、種類も封の 4 つの中、記録を書き換えないと緑にならない門と人間の決定の字の門の赤は 0 で、`golden`・`fixtures`・`measure/tests`・`core` の赤も 0 だった。外れたのは P27 の門 5 本の赤の数 1 か所だけ: `test_xbrl_p27_seal.py` が封の予測の 7 本でなく 8 本だった。増えた 1 本は `test_8`(`verify_document.py` が封の commit と byte 一致であることを見る門)で、封の試作は docstring を直していない(封 §2 の S-8 の字が『docstring の分は試作で測っていない』と書いていた)ので、試作では赤にならなかった。封の予測のうち、試作の clone の件数(81 本・29 file・16 本・11 file・合計 97)は、docstring を直した作業木には当てはまらないので判定に使っていない(封の字『合計の幅 98〜105』の側で判定した)。 【門なし】

封の予測の多くは、記録(97 書類の regress97・儀式・P26 の記録)の写しと試作の写しで、**当たって当然の再現**(profile を省いた経路が P27 を明示した経路と同じ出力を返すことの確認)と封自身が書いていた。本当に外れうるのは S-1(配線)・S-4 の違う欄・S-7(docstring の 一行が他の行を動かさないか)・S-8・S-9・S-11 である。当たった数が多いことは、既定の切り替えが良かったことの証拠ではない(97 書類で GROUNDED・VALUE_MISMATCH の数は P26 と 一行も変わらない)。 【門なし】

## 2. 既定の配線(S-1〜S-3): profile を省いた経路と P27 を明示した経路

profile を省いて `verify_document` を呼んだ出力(`sort_keys` の JSON)を、P27 を明示した出力と、書類ごとに 一 byte まで比べた。**対照**として、既定を実行中だけ P26 に戻す(module の `DEFAULT_PROFILE` を書き換える)と、出力の `profile` の欄が違う書類が全部に出る(対照が差を拾えること = 『差零』が自分の欠陥でないこと)。

<!-- 門:start s1 -->
| 標本 | 書類 | claim | 既定と P27 明示で違った書類 | 対照(既定を実行中だけ P26 に戻す)で違った書類 |
|---|---|---|---|---|
| 手元の 67 | 67 | 7,799 | 0 | 67 |
| 新しい標本 30 | 30 | 3,923 | 0 | 30 |
<!-- 門:end -->

既定の 4 state を P26 の 4 state と並べる。動いた行の数は下の向きの表。regress97(P27 を明示して E の engine `b2c3f56` で測った記録)の P27 の欄とは、書類ごとの 4 state・出力の sha256(engine の欄を除く)・動いた行の集合を 一行ずつ比べ、違いは 0 だった(結果の門が記録の行から数え直す)。

<!-- 門:start s2 -->
| 標本 | profile | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND |
|---|---|---|---|---|---|
| 手元の 67 | P26 | 4371 / 7799 = 56.0% | 433 / 7799 = 5.6% | 1579 / 7799 = 20.2% | 1416 / 7799 = 18.2% |
| 手元の 67 | 既定(P27) | 4371 / 7799 = 56.0% | 433 / 7799 = 5.6% | 1601 / 7799 = 20.5% | 1394 / 7799 = 17.9% |
| 新しい標本 30 | P26 | 2194 / 3923 = 55.9% | 250 / 3923 = 6.4% | 774 / 3923 = 19.7% | 705 / 3923 = 18.0% |
| 新しい標本 30 | 既定(P27) | 2194 / 3923 = 55.9% | 250 / 3923 = 6.4% | 787 / 3923 = 20.1% | 692 / 3923 = 17.6% |
<!-- 門:end -->

<!-- 門:start s3 -->
| 標本 | 向き(P26 → 既定) | 行 |
|---|---|---|
| 手元の 67 | POINTER_NOT_FOUND → UNVERIFIABLE | 25 |
| 手元の 67 | UNVERIFIABLE → POINTER_NOT_FOUND | 3 |
| 新しい標本 30 | POINTER_NOT_FOUND → UNVERIFIABLE | 14 |
| 新しい標本 30 | UNVERIFIABLE → POINTER_NOT_FOUND | 1 |
<!-- 門:end -->

動いた行の state と reason の内訳:

<!-- 門:start s3reason -->
| 標本 | 動いた行の state と reason(P26 → 既定) | 行 |
|---|---|---|
| 手元の 67 | POINTER_NOT_FOUND / no_element → UNVERIFIABLE / per_unit_counter | 11 |
| 手元の 67 | POINTER_NOT_FOUND / no_element → UNVERIFIABLE / target_or_plan | 2 |
| 手元の 67 | POINTER_NOT_FOUND / no_element(ratio without fact) → UNVERIFIABLE / target_or_plan | 3 |
| 手元の 67 | POINTER_NOT_FOUND / no_element(unit not in XBRL) → UNVERIFIABLE / per_unit_counter | 6 |
| 手元の 67 | POINTER_NOT_FOUND / no_same_value → UNVERIFIABLE / target_or_plan | 3 |
| 手元の 67 | UNVERIFIABLE / ambiguous(elements) → POINTER_NOT_FOUND / no_element | 3 |
| 新しい標本 30 | POINTER_NOT_FOUND / no_element → UNVERIFIABLE / per_unit_counter | 1 |
| 新しい標本 30 | POINTER_NOT_FOUND / no_element → UNVERIFIABLE / target_or_plan | 1 |
| 新しい標本 30 | POINTER_NOT_FOUND / no_element(unit not in XBRL) → UNVERIFIABLE / per_unit_counter | 11 |
| 新しい標本 30 | POINTER_NOT_FOUND / no_same_value → UNVERIFIABLE / target_or_plan | 1 |
| 新しい標本 30 | UNVERIFIABLE / ambiguous(elements) → POINTER_NOT_FOUND / no_element | 1 |
<!-- 門:end -->

動いた行は全部 UNVERIFIABLE と POINTER_NOT_FOUND の間で、GROUNDED と VALUE_MISMATCH の数は動かない。**動いた行を 一行ずつ読んではいない**(読みの席は使っていない)。顧客向けの報告形では『要確認』の節の中の理由が替わる。 【門なし】

## 3. 儀式(S-4): 同梱の書類

買い手が今の既定で走らせる儀式(`measure/ritual_2026-10-20.py`)を P27(既定)で採り直した記録 `fixtures/xbrl/ritual_2026-10-20.json` と、P26 の記録の写し `fixtures/xbrl/ritual_2026-10-20_p26.json`(`aeae608` の `ritual_2026-10-20.json` と byte 一致)を並べる。採り直した記録が P26 の記録と違う欄(所要秒・実行環境を除く)は封の予測どおり 3 つだけ(`入力` の `profile`・`注入` と `素の書類` の `state の分布`)で、通した・止めた・通した行の (id, 型) の一覧は同じ。

<!-- 門:start s4 -->
| 儀式(同梱の 1 書類) | 通した | 止めた(VALUE_MISMATCH) | 止めた(POINTER_NOT_FOUND) | 注入の対象 |
|---|---|---|---|---|
| P26(`ritual_2026-10-20_p26.json`) | 2 / 243 = 0.8% | 210 / 243 = 86.4% | 31 | 243 |
| 既定(P27。`ritual_2026-10-20.json`) | 2 / 243 = 0.8% | 210 / 243 = 86.4% | 31 | 243 |
<!-- 門:end -->

<!-- 門:start s4base -->
| 素の書類(claim 412)の state | P26 | 既定(P27) |
|---|---|---|
| GROUNDED | 340 | 340 |
| VALUE_MISMATCH | 14 | 14 |
| UNVERIFIABLE | 31 | 33 |
| POINTER_NOT_FOUND | 27 | 25 |
<!-- 門:end -->

## 4. 報告形(S-5): 顧客向け報告の節

『違う』の節は VALUE_MISMATCH の行と差 0、『一致』は GROUNDED の行と同じ。要確認・対象外・判断しないの間だけが動く(封の字は −2・−6・+8)。UNVERIFIABLE が増えた分と『判断しない』が増えた分が揃わないのは、節の割り当てが state だけで決まらないため(`report_customer` の節の割り当ては変えていない)。

<!-- 門:start s5 -->
| 報告形の節(67 書類) | 件 |
|---|---|
| 違う | 433 |
| 要確認 | 1,773 |
| 対象外 | 145 |
| 判断しない | 1,077 |
| 一致 | 4,371 |
| 合計 | 7,799 |
<!-- 門:end -->

## 5. 誤りを通す側(S-6)

穴 B の注入 485 件と、段 2 の材料の注入 64 件(Core 自身)を、既定で。P26 の記録 `fixtures/xbrl/p26_2026-10-21.json` の Q3 の P26 の欄と 一行ずつ(結果・state・reason・pointers)比べて、違った行は 0。P27 は有報の原文の注入に対して P26 と同じ止め方だった。 【門なし】

<!-- 門:start s6 -->
| 誤りを通す側 | 既定(P27) | P26 明示(対照) |
|---|---|---|
| 穴 B の注入 485 件で通した | 0 / 485 = 0.0% | 0 / 485 = 0.0% |
| 穴 B の注入で止めた(VALUE_MISMATCH) | 480 | 480 |
| 段 2 の材料の注入 64 件で Core 自身が GROUNDED | 0 / 64 = 0.0% | (測っていない) |
<!-- 門:end -->

## 6. engine の差分(S-7)

封の commit からの `git diff --numstat`。engine は `vocabulary.py` の `DEFAULT_PROFILE` の 一行と注記、`verify_document.py` の docstring の 一行だけ。`DEFAULT_PROFILE` を P27 にした。実行の字(`profile_name or V.DEFAULT_PROFILE`・argparse の help)・P27E の定義・旗の既定値・P16〜P27E を明示した呼び出しは 一行も変えていない。`core/` は 零行。

<!-- 門:start s7 -->
| engine の file | 封の commit の sha16 | いまの sha16 | 挿入 | 削除 |
|---|---|---|---|---|
| `adapters/xbrl/vocabulary.py` | 85896a67913ce1e7 | 514ebb8104451c07 | 5 | 1 |
| `adapters/xbrl/verify_document.py` | 67e7639de3f5f2ad | c3791080ab5aef2f | 1 | 1 |
<!-- 門:end -->

<!-- 門:start s7fp -->
| 束ねた指紋・frozen_bundle | 値 |
|---|---|
| `adapter_xbrl_py_sha256`(16 file) | `92326a0f4dcefd21fae4393a611e4206ef174b19258ddadd0213117191e7b399` |
| `core_py_sha256`(4 file) | `34e836bb39762d5af831a9aa11d4ea095e73221beb5bd4510d3b234363a2a6e8` |
| frozen_bundle の束ねた sha(37 本) | `030455282c89661b4c0152498d76bc30314362b5896b15ab67a8886a6887b0f6` |
<!-- 門:end -->

## 7. 試験の赤(S-8・S-9)

S-8: **基準の木**(封の commit の木 + engine の 2 file だけを替えた木。試験・記録・文書は直す前)で `tests/measure` と `tests/adapters/xbrl`(`tests/core`・`tests/golden`・`tests/fixtures`・`measure/tests` を含む)を走らせた赤。種類 1 は engine の sha16・束ねた指紋・frozen_bundle・『engine が動いていない』を留める門、2 は既定の字(`"P26"`)と『既定は P26』を留める試験、3 は既定を前提に走らせ直す門、4 は変異の baseline の連鎖。この表の赤の一覧は人が走らせた pytest の出力から作った表で、記録に入力の file の sha256 を残した。この表そのものの再現は門が縛らない(足し算と封の幅との当たり外れだけを縛る)。 【門なし】

<!-- 門:start reds -->
| 実装の前の基準の木(封の commit + engine 2 file)で、試験を直す前の赤 | 本 | file |
|---|---|---|
| `tests/measure` | 87 | 31 |
| `tests/adapters/xbrl` | 16 | 11 |
| 合計 | 103 |  |
| 種類 1 | 43 |  |
| 種類 2 | 33 |  |
| 種類 3 | 9 |  |
| 種類 4 | 18 |  |
| P27 の門 `test_xbrl_p27_result.py` | 2 |  |
| P27 の門 `test_xbrl_p27_seal.py` | 8 |  |
| P27 の門 `test_xbrl_p27_engine_result.py` | 3 |  |
| P27 の門 `test_xbrl_p27_eval.py` | 0 |  |
| P27 の門 `test_xbrl_p27_order.py` | 0 |  |
<!-- 門:end -->

S-9: 同じ基準の木に `AUDIT_CORE_*=1` の 12 変数を付けて走らせ、軽い門の赤の一覧に無い赤を『増えた赤』と数えた(記録の `試験の赤/S9/増えた赤の id`)。実装の後の 12 変数は、実装の全ファイルを一度だけ commit した使い捨ての clone(本線の履歴に入れない)で走らせた。**未 commit の作業木で赤になるのは、『HEAD からの差分 零行』の欄を比べる試験だけ**で、commit 後は緑(E の commit の説明と同じ確かめ方)。 【門なし】

<!-- 門:start after -->
| 実装の後の重い走らせ直し(環境変数) | rc | 赤 |
|---|---|---|
| `AUDIT_CORE_PACKAGING` | 0 | 0 |
| `AUDIT_CORE_CUSTOMER_REPORT` | 0 | 0 |
| `AUDIT_CORE_CUSTOMER_REPORT_FIX` | 0 | 0 |
| `AUDIT_CORE_POINT_PRIOR` | 0 | 0 |
| `AUDIT_CORE_DEFAULT_P26` | 0 | 0 |
| `AUDIT_CORE_FRESH` | 0 | 0 |
| `AUDIT_CORE_ROUNDING` | 0 | 0 |
| `AUDIT_CORE_VOCAB` | 0 | 0 |
| `AUDIT_CORE_P26` | 0 | 0 |
| `AUDIT_CORE_PERIOD_BIND` | 0 | 0 |
| `AUDIT_CORE_LASTBRANCH` | 0 | 0 |
| `AUDIT_CORE_RITUAL` | 0 | 0 |
<!-- 門:end -->

## 8. 覆い・README・判定(S-10〜S-12)

README.md の『いまの段』に P27 の行が増え、P26 の行は残る。README の儀式の節の数は P27 の記録と 1 対 1(儀式の結果の門が節の全文を縛る)。`docs/FACTS_FOR_BUYERS_2026-10-20.md` の P26・P27 の字は 0 のまま。

<!-- 門:start s11 -->
| 覆い | 本 |
|---|---|
| 試験 file(ディスク上) | 234 |
| 覆いの記録の試験 file | 234 |
| 覆われていない file | 0 |
<!-- 門:end -->

S-12: 判定は、評価用の結果の門の別の関数が記録 4 つから D の 9 小項目を数え直しても次の 2 文のとおり。**既定を P27 にするのはこの判定と人間の言葉に基づき、この文書は判定は覆さない。**

判定(P27E): P27E を「外部の数の文に使う profile」として採用する。
判定(P27): P27 を「既定の候補」として記録する。

## 9. 限界・封にない判断・言わないこと

- **この測定が見たもの**は、既定の配線(profile を省いた経路が P27 を明示した経路と同じ出力を返すこと)と、97 書類・注入の数が P26 から動かないこと、試験の赤の数。**新しい標本での良し悪し・文を読んだ結果は測っていない。** 【門なし】
- 動いた行(UNVERIFIABLE と POINTER_NOT_FOUND の間)を 一行ずつ読んでいない。評価用の読み(読み手の席は同じ model の 2 席・読む行は 2 行で同じ 1 社)の限界は封 §3 と評価用の結果文書 `docs/XBRL_P27_RESULT_2026-10-27.md` の §5〜§6 のまま。読みはエージェントの読みで、人間の読みではない。 【門なし】
- 試験の赤の表(S-8・S-9)は人が走らせた pytest の出力を写した表で、script が測ったものではない。表の中身の再現は門が縛らない(内訳の足し算と封の幅との当たり外れだけ)。
- 既定を替えた代価(評価用で T8_REL の名指して原本の値を返した率 41.4% → 31.0%、T1_VALUE 7/7 → 5/7、GROUNDED を失った 一行、C1・C3 の当たってしまう例)は封 §0-2・§3 のとおりで、この文書は再掲しない。 【門なし】
- P27E は既定にしていない。外部の数の文を点検する客には P27E を明示して使う(評価用の結果の判定)。有報の原文で P27E は VALUE_MISMATCH に入る行を増やす(封 §0-3)。
- 既定の切り替えは人間の決定(2026-10-27・2026-10-28)に基づく。この文書は、顧客向けの文言を新しく書いていない。報告形の理由の表の `per_unit_counter` と `target_or_plan` の文言は、P27 の封で承認済みの字のまま。
- `DECISION_LOG` の D-025 と axis3 の `LATER_ENGINE_COMMITS` への宣言は、この便の範囲の外(次の便)。

記録・入力の sha256:

<!-- 門:start sha -->
| 記録・入力 | sha256 |
|---|---|
| `fixtures/xbrl/ritual_2026-10-20_p26.json` | 42ff63e27e43200fbbc2172482a9c8fefc687e78da65f152138639134f87e3b9 |
| `fixtures/xbrl/p27/regress97_2026-10-27.json` | 7c98ceea69a00841e6e9085f3ab802f634117a3e9d58243c1bb73feed02a2517 |
| `fixtures/xbrl/p26_2026-10-21.json` | 2c41062b3033bb2aca98b6d5b7588ba6d141ebb06847c3acadd222d5717d1ed0 |
<!-- 門:end -->
