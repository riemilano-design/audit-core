# 封: 期間を縛る ― 当期の文に書かれた数を前期の fact に値だけで結ばない(engine の直し P22)― 2026-10-20

**この封は engine(`adapters/xbrl/recipes.py`・`vocabulary.py`)を変える。人間の承認(2026-10-20): 司令塔が穴 B の数(458 / 485 = 94.4%)と直しの案・代価 26 行を示し「承認するなら…進める」と聞き、人間「君に任せる」。段 2(既定 P21 → P22)は段 1 の結果を見せてから別に諮る。数を見てから封・予測を直さない。外れは外れとして残す。**

## §0 根拠(測った事。封 74d15e3 の結果と、司令塔の手元の数)

- 穴 B の結果(`fixtures/xbrl/point_prior_2026-10-20.json`): 経営分析の文を持つ 67 書類で、当期の数を同じ要素の前期の値に置き換えた注入 485 件のうち、製品の文書経路(`verify_document`、既定 P21)が **GROUNDED のまま通した 458 / 485 = 94.4%**(金額 458 / 460 = 99.6%)。通した 458 は参照先が当期 → 前期の fact へ移っている。段 2 の Core 自身 T6 6 / 10、儀式の N125・N199 も同じ形。
- 原因(コード): `recipes._direct_value_claim` の最初の枝は、主語の要素の fact を **期間を問わず**値で突き合わせ(`hits`)、一致した先頭を pointer にする。前期の手がかり(「前期」「(同」等、`_prior_cue`)があるときだけ Prior1Year を先に並べる(C2)。手がかりが無くても Prior1Year の fact に値が合えば GROUNDED にする。
- 直しが届く範囲(2026-10-20、穴 B の独立監査席の概算。正規表現、正本ではない): 通した 459 件の文に「前期」「前年」等の語が在るのは 336(「前期比」等の比較形を除くと 186)。**engine 自身の `_prior_cue`(数の直前 12 字)は 459 件すべてで偽**。この封の直しは `_prior_cue` と `_prior_cue_clause`(同じ節の「前期は」等)で判定するので、E-1 の外れ方は「`_prior_cue_clause` が真になる文で前期の fact が候補に残る数」。
- 代価の見積もり(2026-10-20、司令塔の手元。67 書類、既定 P21): GROUNDED の claim で pointer が 1 本のもの 1,942 のうち、**Prior1Year に結び、文に前期の手がかりが無いもの 26**(手がかりありは 190、当期 1,726)。26 件は「短期借入金が 2 億円減少」(前期残高 2 億 → 当期 0)のように、減少額が前期の残高と偶然一致して前期の fact に結んだ行で、直せば GROUNDED から外れる(= 直しの代価。全 GROUNDED 4,267 の 0.6%)。

## §1 直しの中身(案。engine 2 file、core/ 0 行)

- `vocabulary.py`: `Profile` に `period_bind: bool = False` を足し、`P22 = replace(P21, name="P22", period_bind=True)`。**段 1 では既定にしない**(`DEFAULT_PROFILE = "P21"` のまま)。
- `recipes.py` `_direct_value_claim` の最初の枝、C2 の並べ替えの直後・`if hits and not (is_diff and subj)` の前に: `period_bind` かつ `_prior_cue(s, a, b)` でない(かつ `_prior_cue_clause` でもない)とき、`hits` から `Prior1Year…` の fact を外す。当期の hit が残ればそれで今までどおり。当期の hit が無く Prior1Year の hit しか無かった行は **値の一致なし**として後続の枝(導出 a−b → 最後の枝 = P21 の F1′/F2′/F3b と `no_element` 等)に落とす(= 結果は VALUE_MISMATCH か POINTER_NOT_FOUND。実装席が最後の枝の挙動で確かめ、記録に state の内訳を書く)。
- **触る枝の中の人間の決定(列挙。この後ろに置き、1 つも壊さない)**: 2026-10-08 案ア(主語が取れない数は束縛しない `no_subject`)、2026-10-08 §1b の止め、C2 `period_cue`(前期の手がかりがあれば Prior1Year を先に = そのまま効く)、P21 の最後の枝(5eb80a2)。P16/P20/P21 を明示した試験の数は 1 つも変えない(旗は P22 だけ)。
- **既存試験の直し 3 か所**(封の門の実装席が発見、commit 前に足した): `tests/adapters/xbrl/test_vocabulary.py` の `sorted(V.PROFILES)` の一覧 2 か所(322 行・573 行)に `"P22"` を足す、`tests/adapters/xbrl/test_p20.py` の `test_every_other_profile_keeps_the_flag_off`(394 行)の除外に P22 を足す(P21 の段 1 と同じ前例)。これは登録の一覧の試験で、P16/P20/P21 の数の試験ではない。E-7 の「全部緑のまま」はこの 3 か所を直した後の緑。
- **過去の門の engine の留めを先に列挙**(段 1 の commit で遷移を宣言): axis3 `LATER_ENGINE_COMMITS`、`ENGINE_LATER` の pin 6 本(vocabulary.py・recipes.py の sha16)、`fixtures/frozen_bundle_sha.py` の世代、`test_xbrl_cd_seal.py` FROZEN_LATER、`test_xbrl_a_core_vs_grep_seal.py` ENGINE_LATER、`test_xbrl_hybrid_trust_seal.py`(順序のみ)。

## §2 事前予測(実装前に固定。段 1 = P22 を旗で、既定は P21 のまま)

| # | 予測 | 外れ方 |
|---|---|---|
| **E-1** | 穴 B の 485 件を P22 で再検証: 通した(GROUNDED のまま) **0〜10 / 485**(458 から)、止めた(VALUE_MISMATCH)**420〜485**、残りは POINTER_NOT_FOUND 等 | 通した 11 以上 |
| **E-2** | 67 書類の無改変で P21 → P22 で動く GROUNDED の行は **22〜30**(§0 の 26 とその周辺)、動く向きは全部 GROUNDED → 非 GROUNDED(新しく GROUNDED になる行 0)。手がかりありの Prior1Year 190 行と当期の 1,726 行は **1 行も動かない** | 幅の外 / 新 GROUNDED 1 以上 / 190・1,726 が動く |
| **E-3** | 名指しの直しの無改変 40 書類 4,665 本(`fixtures/xbrl/naming_fix/p21_2026-10-20.json` の集合)で動く行 **≤ 40**、全部 GROUNDED → 非 GROUNDED | 41 以上 / 向きが逆 |
| **E-4** | 段 2 の材料で Core 自身の T6 は **0〜1 / 10** GROUNDED(6 から)。α 型(`verify_external`、席の参照先)の 3 群の数は **1 つも変わらない**(別の経路) | T6 2 以上 / α 型が動く |
| **E-5** | 儀式(E36539、241 件)を P22 で: 通した **15**(N125・N199 が VALUE_MISMATCH に)、止めた **226**、他の 239 件は同じ結果 | 15・226 でない / 他が動く |
| **E-6** | 動いた無改変の行(E-2 の 22〜30)を 1 件ずつ読むと、**過半は「減少額が前期の残高と一致」型**で、当期の文として正しい数(= 直しの代価は「正しい文を保留に落とす」)。これを隠さず結果に書く | 過半が別の型 |
| **E-7** | engine の差分 `recipes.py` **≤ 15 行**、`vocabulary.py` **≤ 6 行**、`core/` 0 行。P16/P20/P21 明示の既存試験 **全部緑のまま** | 超える / 赤 |
| **E-8** | 段 2(既定 P21 → P22、E-1〜E-7 が当たったときだけ、人間の承認の後): 既定の字の試験・pin 6 本・frozen_bundle・axis3 の遷移を宣言して全緑。`DEFAULT_PROFILE` の字の決定の注記を日付つきで | 赤が残る |

**本当に測っているのは E-1・E-2・E-6 である**(直しが効くか、代価はいくつか、代価の中身は何か)。

## §3 限界

- 代価 26 行は 67 書類の数。別の書類では増えうる。
- 「前期の手がかり」は `_prior_cue`(直前 12 字)と `_prior_cue_clause`(同じ節)の字の規則。「前期比」は当期扱い。手がかりの字の一覧を広げる直しはこの封に含めない。
- 率の主張(％)は穴 B で 23 / 24 止めていたので対象外(金額だけが問題)。
- 穴 A(ポイント)はこの封で直さない(原因が別: `no_element`・`no_subject`)。
- 代価 26 は span の語の正規表現で数えた(封の門の実装席が再現、commit 前に注記)。うち N049「現金及び預金が 50,369 千円から 50,751 千円」の 50,369 は数の直後が「から」なので engine の `_prior_cue` では真になり、P22 でも前期の fact に結んだまま残りうる = 段 1 の実測の代価は 25 か 26(E-2 の幅 22〜30 の中。どちらになるかは段 1 が数える)。

## §4 触る file と順序

段 1: `adapters/xbrl/vocabulary.py`(P22)・`adapters/xbrl/recipes.py`(最初の枝) → `tests/adapters/xbrl/test_recipes_p22.py` → 既存試験 3 か所(`tests/adapters/xbrl/test_vocabulary.py` の一覧 2 か所・`tests/adapters/xbrl/test_p20.py` の除外 1 か所)に P22 を足す → `measure/xbrl_period_bind_2026-10-20.py`(E-1〜E-6 を測る。穴 B の記録・儀式・段 2 の材料・naming_fix の集合を再利用)→ `fixtures/xbrl/period_bind_2026-10-20.json` → `docs/XBRL_PERIOD_BIND_RESULT_2026-10-20.md` → `tests/measure/test_xbrl_period_bind_result.py` → pin の遷移の宣言 → 覆い。段 2(承認後): `vocabulary.py` の `DEFAULT_PROFILE = "P22"` + 既定の字の試験 + pin。
順序: 人間の承認(済み、2026-10-20「君に任せる」)→ この封 + 封の門を commit → 段 1 実装(別席)→ 凍結 → 独立監査 → commit → 結果を人間に見せる → 段 2 の承認 → 段 2 → 監査 → commit。

## 追記(2026-10-20、段 1 の実測の後。本文と予測は不変)

- 既存試験の直しは 3 か所でなく 4 か所だった: `tests/adapters/xbrl/test_recipes_p21.py` の `test_only_p21_has_the_flag_on`(P22 は P21 から作るので `last_branch_cues` を引き継ぐ)。1 行直した。E-7 の判定は外れのまま。
- 段 1 の実装席が封の pin 一覧に無い 2 本を同じ型で宣言した: `tests/measure/test_xbrl_point_prior_result.py` の `engine_untouched()` と `tests/measure/test_xbrl_ritual_result.py` の R-8(生の `git diff` で engine 0 行を見ていた)。測った当時の事実は消していない。
- E-2 の外れ: 「手がかりあり 190」は span の正規表現の数で、engine の `_prior_cue`・`_prior_cue_clause` より広かった。11 行(「前年は…」「前連結会計年度末残高…」等)が正しい前期の文のまま VALUE_MISMATCH になった。§3 の「手がかりの字の一覧を広げる直しはこの封に含めない」がそのまま代価に出た。段 2 の判断材料。
- 独立監査(2026-10-20)の指摘: 主語の無い数 5 行で案ア(UNVERIFIABLE)の state が POINTER_NOT_FOUND に動いた。司令塔の判断で P22 の条件に「主語あり」を足し、主語なしは P21 と同一のまま(案アを字のとおり残す)。主語ありの行は 1 つも変わらない。人間が「主語なしも POINTER_NOT_FOUND でよい」と決めるなら別の便。

## 追記(2026-10-20、段 2。本文と予測は不変)

- 段 2(2026-10-20): 人間「任せる」(段 1 3320c8c の結果と客の席 A の回し直し ― 同じ書類で誤り 5 / 5 止め・正しい 39 行の空振り 0(開発側でない客の席の日記。repo の外 = scratchpad、記録なし。司令塔が読んで諮った数) ― を見てから)。`DEFAULT_PROFILE = "P22"`。儀式の記録と README の数は P22 の既定で走らせ直した(P21 の 17 / 241 は履歴と結果文書の本文に残す)。既定で測った記録を持つ measure・門は測った当時の P21 を字で留めた。
- 司令塔が段 1 の結果(通した 458 → 1 / 485、代価 25 行、うち正しい前期の文 11 行が『不一致』になる副作用)と客の席 A の回し直しを並べて『既定を P22 にするか』と諮り、人間(2026-10-20)『任せる』。
