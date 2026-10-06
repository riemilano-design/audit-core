# Core 接続 C-1d(計器 3・5: Adapter + Core で 224 件)の予測 ― 実装の前に封じる

**日付**: 2026-10-06 **段**: C-1d(C-1 計画 §4) **前提**: C-1b `f917f02`(Core)、C-1c `066eb13`(Adapter、前段照合 224/224)、C-1c の結果 `e4c9ebd`(XP-C1c-2: 2 社で到達しない分岐 4 つ) **封の手順**: この文書をコミットしてから書く。後から書き換えない。予測は司令塔の席(人間の欄は空欄。C-1 計画 §6 の「計器 3 初回 210〜224」は先に封じた別の席として残す)。

## 1. 範囲

**作る**: 比較子 6 の実体、`register_all(registry)`(scheme・比較子・normalization・理由)、Adapter の resolver(`xbrl:` pointer → `Resolved`)、計器 3(Core の `verify_all` を通した 224 件の照合)、計器 5(sign_token の数の一致)、1 回目の実行の保存、変異(両向き)。
**作らない**: Core の変更(必要になったら止めて HUMAN。C-0 の予測は意味変更 0・インターフェース拡張 1)、期待値の変更、3 社目、C-1e の分類文書(ただし C-1e の入力になる登録の数は C-1d の報告に表で出す)。

## 2. 材料(sha256、不変であること)

Core 4 本 = `f917f02`(`__init__` 9aea7f9e… / model a65e285c… / registry 38ac65a5… / verify d29b21dc…)。期待値 1B `f8a45ecc…`(91)・5F `a19f3419…`(133)。原本 4 本(896492a7… / 3d2092a9… / f25652f0… / 275ae50e…)。Adapter は `066eb13` の状態から始める(C-1d で変えてよいのは Adapter と試験。ただし C-1c の前段照合 224/224 は門として残す)。ZIP 2 本(0731a291… / d617b6e1…)。

**本日測った既知(予測の根拠、結果を見て書いたものではない)**: 原本の main は `tol_of` を呼んでいない(許容幅は `match_value` の梯子 round / truncate / abs+round / abs+truncate だけ)。期待値で使われる `xbrl:` pointer 60 + 39 本は全部 facts に在り、同じ(要素名, context)で値が違う重複は 0(重複自体は 1 社目 38 組・2 社目 46 組あるが値は同じ)。pct_change の前期が負の Claim は 5F に 3 件(N049・N078・N083)、文章の Claim で前期が負は T040・T041。c − p = 0 の Claim は 0。pure×100 は 1B に 3 件(N013 VM 10.0 vs 5.8、N014・N041 GROUNDED)、5F に 0。sign_token を持つ Claim は 5F 15 件・1B 0 件。

## 3. いま固定する設計(C-1d で実装担当が選ばない所)

### 3.1 比較子(`adapters/xbrl/comparators.py` を新設。語彙・instance を import しない。読むのは evidence の値・`claim.value`・`contract.params` だけ)

| 名前(C-0 のまま) | params(Adapter が recipes で入れる) | 一致 | recomputed |
|---|---|---|---|
| `equals_within` | `unit_scale`(千円 → 1000 等)、`claim_scale`(精度の単位。円の漢数字は書かれた最小の位)、任意 `abs_tolerance`(名/人の 0.5。224 件に 0 件) | `match_value(fact, claim.value × unit_scale, claim_scale)` の梯子が None でない | fact の値(生) |
| `equals_within(pure*100)` | `tolerance 0.15`、`pure_threshold 1.5` | fv×100(|fv| ≤ 1.5 のとき)と **|claim.value|** の差 ≤ 0.15 | `round(fvp, 2)` |
| `ratio*100` | `tolerance 0.15` | cur/prior×100 と **|claim.value|** の差 ≤ 0.15 | `round(ratio, 2)` |
| `pct_change(cur,prior)` | `tolerance 0.15` | (cur − prior)/**|prior|**×100 と claim.value(符号つき)の差 ≤ 0.15 | `round(pct, 2)` |
| `diff(a-b) equals_within` | `unit_scale`、`claim_scale` | `match_value(a − b, claim.value × unit_scale, claim_scale)` | a − b(生) |
| `builtin:sign(cur-prior)==direction` | `direction` ±1(Adapter が DIRECTION_WORDS から解決。**Core は word を読まない**) | (cur − prior > 0 ? +1 : −1) == direction | cur − prior |

原本の癖は **そのまま写し、直さない**(直すと 224 件の再現が壊れる。直すかは人間の判断): (a) pure×100 と ratio×100 は |claim.value| と比べる、(b) sign は差 0 を「減」と数える、(c) prior = 0 は Adapter が build 時に `unverifiable_reason="prior is 0"` を立てる(224 件に 0 件)。これらは結果文書で「人間に見せる癖」として列挙する。

normalization: 比較子は梯子の `how` を `Comparison.detail["normalization"]` に入れる。Adapter が bind 時に Claim に書いた `modifiers.normalization` と一致することを計器 3 の中で確かめる(77 件 = 1B 44 + 5F 33)。

### 3.2 resolver(`adapters/xbrl/resolve.py` または instance.py 内)

`xbrl:<name>@<context>` → その (name, context) を持つ fact のうち **instance の順で最初**の値。`Resolved(value, unit, precision = 10^(−decimals)(数値のとき)、meta = {decimals, duplicates: 同じ鍵の fact 数, distinct_values: 値の異なり})`。計器 3 の中で、使われた pointer 全部について `distinct_values == 1` を assert(本日 0 件の曖昧さ、を門にする)。`formula:` と `builtin:` は operator なので Core が resolver に渡さない(Core の既存の挙動)。無い pointer は None(Core が POINTER_NOT_FOUND にする)。

### 3.3 登録(`register_all(registry)`。`Registry.default()` の上に)

| 種類 | 登録する名前 | 数 |
|---|---|---|
| scheme | `xbrl`(evidence、trust は "filing")、`formula`(operator、"structural")。`builtin` は Core の既定(再登録すると ValueError。試験で確かめる) | 2 |
| 比較子 | §3.1 の 6 | 6 |
| normalization | round / truncate / abs+round / abs+truncate | 4 |
| 理由 | POINTER_NOT_FOUND: `no_element`・`no_element(unit not in XBRL)`・`no_element(ratio without fact)`・`no_prior_member_context` / UNVERIFIABLE: `no_subject`・`ambiguous(member)`・`ambiguous(elements)`・`state_word(no line)`・`prior is 0` | 9 |

`ambiguous(N elements)` は **名前を `ambiguous(elements)` に正規化し、N は `Claim.provenance["ambiguous_count"]`** に入れる(3 社目で N が増えても登録が落ちないため)。計器 3 の理由の照合は、期待値の `script_reason` → 登録名の写像(1 本の表)を通す。登録の合計 **21** が C-1e の計器 4 の入力。

### 3.4 計器 3(`tests/golden/test_instrument3.py`)と 1 回目の保存

P1 × S100Z4Q1 と P5F × S100Z4B6 で `build_recipes` → `Registry.default()` + `register_all` → `verify_all(recipes, resolver, registry)` → 期待値と比べる欄: **state・pointers(文字列の列)・recomputed(None 含め `==`。float は丸めなし)・理由(写像を通して)・normalization(detail と期待値)**。1 回目の出力を `fixtures/xbrl/c1d_first_run_{1B,5F,diff}.json` に保存(直す前の証拠。recipes/comparators の更新時刻より後で、公式試験より前)。期待値は変えない。差は全件を表に。

### 3.5 計器 5(`tests/golden/test_instrument5.py`)

sign_token を持つ Claim(5F 15 件)について、token の中の数 == |claim.value|。不一致 **0** が門。1B は 0 件であることも数える(0 件は「通った」ではなく「材料に無い」と書く)。

### 3.6 変異(予測を先に書く。期待値の数から予測を導いてよい。少なくとも次の 9 本 + green 2 本)

| id | 変異 | 予測 | 根拠 |
|---|---|---|---|
| D-R1 | 比較子の梯子から truncate を外す | red | 1B に truncate 13 + abs+truncate 6 |
| D-R2 | pct_change の分母を |prior| → prior | red | 5F N049・N078・N083 の符号が返る |
| D-R3 | sign の `> 0` を `>= 0` | **green**(等価) | c − p = 0 が 0 件 |
| D-R4 | direction の符号を反転 | red | 文章の GROUNDED 21 + 9 が VM に |
| D-R5 | resolver が context を無視して名前だけで最初の fact | red | 当期と前期が同じ値になる |
| D-R6 | `formula` を evidence で登録 | red | 派生 Claim の pointer が解決できず PNF |
| D-R7 | `ctx_ok` の `== [member]` → `in`(C-1 計画 §5 が「赤」と予測した変異) | **green(計器 3 では)**。C-1c の監査が実測済み | **C-1 計画 §5 の予測の外れを、ここで公式に記録する**。守っているのは C-1c の単体試験だけ |
| D-R8 | pure×100 の `|fv| ≤ 1.5` を外す | red | 1B N014・N041 が ×100 されず VM |
| D-R9 | recomputed の `round(x, 2)` を外す | red | ratio 4 + pct 14 の recomputed が期待値と `==` でなくなる |
| D-G1/G2 | コメント・docstring の変更 | green | 対照 |

変異は一時コピーに当て、`-X pycache_prefix` で回し、Adapter・Core・原本の sha が実行前後で不変であることを確認する(C-1c の方式)。

## 4. 予測(司令塔の席。写しの所は点、書き直しの所は幅)

| # | 項目 | 予測 | 外れたら何を疑うか |
|---|---|---|---|
| 1 | 計器 3 の state(1 回目) | **224 / 224**(点) | 比較子の params の入れ忘れ、理由の写像、prior is 0 の経路 |
| 2 | 同 pointers | **224 / 224**(点。C-1c で一致済み) | Core の pointer 文字列化 |
| 3 | 同 recomputed(`==`、None 含む) | **220〜224** | `round(x, 2)` の場所、a − b の float、pure の fvp |
| 4 | 同 理由(写像経由) | **224 / 224**(点) | 写像の表の漏れ |
| 5 | normalization の再導出 == 期待値 | **77 / 77**(点) | 梯子の順(round を先に試す) |
| 6 | 1 回目の後の直し / 期待値の変更 / Core の変更 | **0〜2 / 0 / 0**(Core は門。1 行でも必要なら止めて HUMAN) | 2 を超えれば比較子を「書き直した」証拠 |
| 7 | 計器 5 | 不一致 **0 / 15**(5F)、1B は材料 0 | P-8 の写しが壊れた(C-1c の R5 と同じ) |
| 8 | resolver の曖昧さ(使われた pointer 99 本で distinct_values > 1) | **0**(門) | ― |
| 9 | 登録の数 | 比較子 **6**・scheme **2**・normalization **4**・理由 **9** = **21** | C-0 は normalization 1〜2 と予測した → **外れる見込み(4)**。理由は C-0 が「表 1」と数えたので単位が違う。C-1e で記録 |
| 10 | Core のインターフェース拡張 | **0**(C-0 の予測は 1。provenance が Mapping だったので Adapter 側で吸収) | 1 以上なら C-0 どおり |
| 11 | Core の意味変更 | **0**(門) | ― |
| 12 | 新規モジュール / 行数 / 試験 / 変異 | comparators.py(+ resolve.py なら 2)で **7〜8**、追加 **250〜450 行**、試験 **20〜45 本**、変異 **11〜14 本** | C-1c は量を過小に予測した(1214 行・111 本)。今回は幅を上に広げた |
| 13 | C-1 計画 §5 の「母集団の置き換えを合わせるに変えると赤」 | **計器 3 では緑**(計画の外れ 1 件、確定) | ― |
| 14 | 人間に見せる原本の癖 | **3**(pure と ratio の |claim|、sign の 0 → 減、prior is 0 の経路は 4 つ目として 0 件と添える) | 実装中に 4 つ目以上が見つかれば足す(直さない) |
| 15 | 1 回目の計器 3 で、state が合うのに recomputed だけ違う Claim | **0〜4** | 3 と同じ根 |

**書かない予測**: 所要時間。費用 0。

### 4.1 この段の false pass の定義

(1) state が合っているが比較子が **別の理由**で同じ答えを出している(例: 許容幅が広すぎて VM が GROUNDED に、または逆に GROUNDED が偶然)― 変異 D-R1〜R9 で捕まえる。(2) 224/224 が **到達しない 4 分岐**(XP-C1c-2)について無言であること ― これは false pass ではなく材料の限界で、D-R7 がその証拠。(3) 計器 5 の 0 は P-8 の構造の帰結であり、「符号の偶然一致が無い」を言うのは 5F の 15 件に限る。

## 5. 止まる所と 3 役

計器 3 が 224/224(state・pointers・理由)+ recomputed の差 0 + normalization 77/77 + 計器 5 の 0 + 変異 11/11 + Core 4 本不変 → 監査 → GO でコミット(パス指定) → 結果文書(予測との表、C-1 計画 §6 の「210〜224」の当否、癖の一覧、登録の表)。その後 C-1e(分類)。実装担当は `adapters/`・`tests/`・`fixtures/xbrl/c1d_*` だけ触り、コミットしない。監査は変異 2〜3 本を自作し、1 回目の JSON の時刻を見る。C-1c の監査が記録した `test_extract.py` の tie-break の試験の名前と中身のずれは、この段の実装担当が直す(試験だけ、1 件、報告に書く)。
