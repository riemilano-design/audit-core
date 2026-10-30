# 封: 語彙の登録で「結べない」を減らし、枠の取り直しで「違う」を「要確認」に弱める(engine の直し P24 = P23 + 旗 2 つ)― 2026-10-21

**この封は engine(`adapters/xbrl/vocabulary.py`・`recipes.py`・`registry_setup.py`)を変える。人間の承認(2026-10-21 深夜): 司令塔が朝に諮ると言った 3 点(語彙の封・丸めの帯・日本語の報告形)に対し、人間「engine に触るので承認が要る → 先に承認しておくので好きに進めて これをもって承認とする」。作法は変えない(封 → 実装 → 凍結 → 独立監査 GO → commit)。数を見てから封・予測を直さない。外れは外れとして残す。P23 段 1(7d530cc、宣言 8fc113f)の後に置く。**

## §0 根拠(封の前の試作 3 回、scratchpad の clone。正本でない。司令塔の席の手元の報告 `scratchpad/vocab/proto_report.md`・`scratchpad/vocab3/proto3_report.md`)

- 無改変の原文 67 書類 7,799 claim を P23 で: GROUNDED 4,234、VALUE_MISMATCH 1,418、UNVERIFIABLE 1,323、POINTER_NOT_FOUND 824(封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md の段 1 の記録 fixtures/xbrl/rounding_2026-10-21.json と同じ数)。
- **試作 v2(枠の取り直しで GROUNDED を作る形)は新 GROUNDED 345 のうち偽 16・準偽 11 を出した。** 偽の型: (イ) 同じ要素の別の枠の率が帯の中で偶然に合う(報告セグメント合計・調整額)、(ロ) 外部顧客への売上高の文をセグメント間を含む売上高の率に結ぶ(準偽 11)、(ハ) 1 千円の端数で素の枠を外れ内訳の列に結ぶ、(ニ) 連結の文を単体の枠に結ぶ、(ホ) 資金の句の括弧「(前年同期は…の減少)」を前期 − 前々期の差の符号で照合する(12。P22 でも既存 6 句で同じ枝を 6 行が通る)。**値が合う枠がちょうど 1 つでも同定ではない** → 枠の取り直しは GROUNDED を作らない設計に変えた。
- 試作 v3 は偽 5(CF 合計の文字の主張を、前期の手がかりが無いとき当期の値の符号で照合した枝)・注入 705 回で GROUNDED 1(新しい資金の句が Prior3Year に結んだ)。
- **試作 v3.1(この封 §1 の規則)**: 新 GROUNDED 148(資金の主語の句 117・手がかり語とポイント 13・CF 合計の符号 18)を全部人が読み**偽 0**。G → 非 G 0、G → G 4(全部改善)。VALUE_MISMATCH 1,418 → 1,203(−215 = 枠 −209・語彙 −6)。枠の VM → UNVERIFIABLE 209(other_frame 198・ambiguous(member) 11)を全部読み、正しい文 207・文が本当に違う 1・分からない 1。新しい VALUE_MISMATCH 6(全部正しい文)。穴 B 通した 0 / 485(P23 と同じ、違う行 0)、儀式 通した 2 / 247・止めた 245 / 247(素の書類の GROUNDED 329 → 340 で注入の対象が 240 → 247)。動いた 361 行への注入 695 回(1 回に 1 件、末尾の桁 ±3・10 倍・向きの語の反転)で P24 の GROUNDED 0・UNVERIFIABLE 1(P23 は同じ 695 回で GROUNDED 2)。既存試験の赤 33(登録の一覧 13・test_mutations 1・sha の留め 14・diff の門 5、数 / state の門 0、人間の決定の字の門 0)。engine recipes +224/−0・vocabulary +27/−1・registry_setup +2/−0。
- **試作は全部同じ 67 書類で測った。** 規則は 67 書類を読んで作ったので、67 書類での偽 0 は新しい標本での偽 0 を意味しない(凍結材料での増分は新しい標本で 0 になりうる)。手元の cache `~/.cache/audit-core/edinet/*.zip` は 281 書類、うち 67 の外が 214(司令塔の席で数えた。text と claim の有無は未測定)。

## §1 直しの中身(engine 3 file、core/ 0 行、recipes.py の既存の行は 1 行も書き換えない)

- `vocabulary.py`: `Profile` に `vocab_2026_10_21: bool = False`・`frame_rebind: bool = False`。`P24 = dataclasses.replace(P23, name="P24", vocab_2026_10_21=True, frame_rebind=True)`、`PROFILES` に登録。**段 1 では既定にしない(DEFAULT_PROFILE = "P22" のまま)。** 旗が偽なら 1 行も変わらない。
- 旗 `vocab_2026_10_21`:
  - (1) 同じ節(直前の読点・句点より後、閉じた括弧の中は除く)の前期の手がかり語に「前連結会計年度末残高」「前年は」「(前期␣」(␣ は空白)を足す。新しい関数が持ち、`def _prior_cue_clause(s, pos):` とその本体は字を変えない。**「前連結会計年度に」「前期同期」は足さない**(前者は得 ≤ 1・代価 2、後者は誤字に合わせない)。P22 の period_bind は、この語が節に在る数では Prior1Year の hit を外さない(period_bind の `if` 行の字は変えず、後ろに足す)。
  - (2) ポイントの前期の語(数の手前 25 字)に「(同」「前事業年度」「前事業年度末」を足す。**C-1g §1-3 の `_build_point_diff_claim` は字を変えず**(def 行・窓の `if` 行・呼び出しの行)、既存の語で reason が `no_element(point without prior phrase)` になった数だけ、本体を写した新しい関数で組み直す。
  - (3) 資金の主語の句 19 通り(67 書類で件数 2 以上)を、既存 6 句と同じ要素に結ぶ登録に足す。**この 19 句の主語の数は当期と Prior1Year の fact にだけ値で結ぶ(Prior2Year 以前に結ばない)。** 既存 6 句は変えない。
  - (4) 主語の要素が CF 合計(`NetCashProvidedByUsedIn(Operating|Investing|Investment|Financing)Activities`、末尾 `SummaryOfBusinessResults` を含む)の文字の主張(増加・減少・獲得・使用・支出)は、**前期の手がかり(既存の括弧の「前連結会計年度は」・節の手がかり・(1) の語)があるときだけ** Prior1Year の値そのものの符号で照合する(正 = 増加・獲得、負 = 減少・使用・支出)。前期・前々期の対には落とさない。**手がかりが無ければ P23 のまま。**
- 旗 `frame_rebind`:
  - 対象: 主語の要素が取れ、取った枠で値が合わず、前期の手がかりが無い数。同じ要素の別の枠(素か member 1 つ、当期)で (i) 直接の値 (ii) 当期・前期の率 (iii) 当期 − 前期 が合うとき。
  - 扱い: VALUE_MISMATCH をやめて UNVERIFIABLE。合う枠が 1 つなら理由 `other_frame`(登録簿の固定の名前。`registry_setup.py` に登録。合った当期の fact の context は provenance)、2 つ以上なら `ambiguous(member)`。**pointer を付けず、GROUNDED にしない。** 別の要素・前期の枠には広げない。
- **触る枝の中の人間の決定(列挙。字も振る舞いも 1 つも壊さない)**: 2026-10-08 案ア(no_subject)、§1b の止め、C2 `period_cue`、C-1g §1-3 `_build_point_diff_claim`、P21 の最後の枝(5eb80a2)、P22 の `period_bind`(3320c8c、`subj and`)、P23 の `_mag_trunc`(7d530cc)。これらの字を engine に探す既存の門(period_bind_seal test_8・rounding_seal test_7 ほか)は**直さずに緑**。P16/P20/P21/P22/P23 を明示した試験の数は 1 つも変えない。
- **過去の門の engine の留め**: ENGINE_LATER 6 本(branch_a・role_swap・axis3・p20_result・a_core_vs_grep・pnf_diag)、cd_seal FROZEN_LATER、point_prior_result・ritual_result・period_bind(seal/result)・rounding(seal/result)、frozen_bundle の世代、axis3 LATER_ENGINE_COMMITS(次の便)。registry_setup.py の sha を留める門があれば同じ型で宣言する。

## §2 事前予測(実装前に固定。段 1 = P24 を旗で。対照は P23)

| # | 予測 | 外れ方 |
|---|---|---|
| **W-1** | 67 書類の無改変で新しく GROUNDED になる行 **140〜156**、向きは全部 非 GROUNDED → GROUNDED。枠の取り直しが作る GROUNDED **0** | 幅の外 / 枠の GROUNDED 1 以上 |
| **W-2** | 67 書類で GROUNDED → 非 GROUNDED **0〜1**。G → G(参照先が動いた)**0〜6** | 2 以上 / 7 以上 |
| **W-3** | 67 書類の VALUE_MISMATCH は **1,195〜1,211**(P23 1,418)。VM → UNVERIFIABLE(other_frame・ambiguous(member))**200〜215** | 幅の外 |
| **W-4** | 穴 B の 485 件を P24 で通す **0**、止めた行の state は P23 と全行同じ | 1 以上 / 1 行でも違う |
| **W-5** | 儀式を P24 で: 通した **2〜3**、止めのうち VM → UNVERIFIABLE に移る **0〜1**(注入の対象の数は素の書類の GROUNDED で決まり 240 から動きうる。対象の数は予測しない) | 幅の外 |
| **W-6** | 67 書類で P23 → P24 に GROUNDED か UNVERIFIABLE へ動いた行(G → G を含む。試作で 361 = 148 + 4 + 209。非 G → 非 G の 8 は含めない)への注入(1 回に 1 件、末尾の桁 ±3・10 倍・向きの語の反転、試作と同じ作り方)で P24 が GROUNDED にする **0** 回、止まらず UNVERIFIABLE **0〜3** 回 | GROUNDED 1 回以上 / UNV 4 以上 |
| **W-7** | **新しい標本(手元の cache の 67 の外 214 書類のうち、67 と同じ抽出で claim が 1 以上の書類)**で P23 → P24 の新 GROUNDED を全部人が読み、**偽(間違った fact に結んだ)が新 GROUNDED の 3% 以下**、かつ VM → UNVERIFIABLE を全部読み「文が本当に違う」が **10% 以下**。claim が 1 以上の書類が 10 未満なら「測れない」と記録する(当たりにも外れにもしない) | 偽が 3% 超 / 違うが 10% 超 |
| **W-8** | engine の差分 `recipes.py` **+200〜+250 / −0**、`vocabulary.py` **≤ 35 行**、`registry_setup.py` **≤ 5 行**、`comparators.py`・`core/` 0 行。既存試験の赤は登録の一覧・旗の形・sha の留め・diff の門だけ(数 / state の門 0、人間の決定の字の門 0) | 超える / `recipes.py` の削除 1 行以上 / 種類の外の赤 |
| **W-9** | 段 2(既定 P22 → P24、P23 と P25 を含めてまとめて)は人間に 3 つの率(通す率・無改変で「違う」と言う率・結べない率)を見せてから | ― |

**W-1〜W-6 は試作の再現で、外れるなら実装が試作と違うことを示す。本当に外れうるのは W-7(新しい標本)である。** W-7 の分母と読みは結果文書に 1 行ずつ残す。

## §3 限界

- 枠の取り直しは、別の枠の率が帯の中で合うとき、注入した誤りを UNVERIFIABLE にする(試作で 695 回中 1 回、S100YWGX N020)。「違う」を「要確認」に弱める代価がある(67 書類で 209 行中 2)。
- 「前期同期」(誤字)の文は VALUE_MISMATCH のまま。増減の数・支出の減少率を当期の値や符号つきの率と照合する型の正しい文は VALUE_MISMATCH(試作で新しい VM 6)。
- 手がかりの無い CF 合計の文字の主張は P23 のまま(前期・前々期の対の符号で、偶然に合う行がある。試作で S100Z6XO の 3 行)。
- 登録する語は 67 書類の字。別の提出者の言い回しは W-7 で一部だけ見る。
- 段 2 の材料(192 行)にはこの規則の形の文が無い(試作で動いた行 0)= 段 2 の材料ではこの直しの安全を測れない。安全は W-6 と W-7 で見る。
- 「違う」1,418 のうち最後の枝の名指し(696)・率の再計算で対が無い・増減で対が無い・向きの語は、この封では直らない(P25 の封)。
- 単位 145(店舗・社・台・株・倍・件)は fact が無いので登録しない。

## §4 触る file と順序

段 1: `adapters/xbrl/vocabulary.py`・`adapters/xbrl/recipes.py`・`adapters/xbrl/registry_setup.py` → 登録の一覧の試験に P24 → `tests/adapters/xbrl/test_recipes_p24.py` → `measure/xbrl_vocab_2026-10-21.py`(W-1〜W-8) → `fixtures/xbrl/vocab_2026-10-21.json` → `docs/XBRL_VOCAB_RESULT_2026-10-21.md` → `tests/measure/test_xbrl_vocab_result.py` → pin の遷移 → 覆い。段 2(人間に見せてから): `DEFAULT_PROFILE` + 既定の字の試験 + 儀式の走らせ直し + README + pin。
順序: 人間の事前承認(2026-10-21)→ P23 段 1 の commit(7d530cc・8fc113f)→ **この封 + 封の門を commit** → 段 1 実装(別席)→ 凍結 → 独立監査 → commit → axis3 の宣言 → P25 の封 → 段 2 を人間に。
