# Core 接続 C-1d(計器 3・5)の結果 ― 予測との突き合わせ

**日付**: 2026-10-06 **予測の封**: [CORE_CONNECTION_C1D_PREDICTION_2026-10-06.md](CORE_CONNECTION_C1D_PREDICTION_2026-10-06.md)(コミット `91bd83d`、sha `e08ca838…`、本文は不変) **実装**: 3 役(実装担当 1 席、監査担当 1 席、司令塔) **監査**: GO(独立の監査担当、1 回で GO。司令塔の差し戻し 1 便は監査の前) **コミット**: `25f33e9`(比較子・resolver・登録・計器 3・5・試験・証拠 JSON、20 ファイル)

## 1. 何を測ったか

- 門: `python3 -X pycache_prefix=<一時> -m unittest discover -s audit-core/tests -t audit-core` → **Ran 217 tests OK**(C-1c の 168 + 49)。末尾に変異ランナーの要約「predicted == actual: 21 本 / 外れ: 1 本 (D-R3)」。司令塔が 2 回回した。
- 計器 3: `tests/golden/test_instrument3.py`。P1 × S100Z4Q1 ↔ 1B、P5F × S100Z4B6 ↔ 5F。Adapter の `build_recipes` → `Registry.default()` + `register_all` → **Core の `verify_all`**(resolver は Adapter)→ 期待値と state・pointers・recomputed(`==`、丸めなし)・理由(写像 1 表)・normalization(77 件)で照合。1 回目の出力は `fixtures/xbrl/c1d_first_run_1B.json`(`bd74128f…`)・`_5F.json`(`d59a5850…`)・差 `c1d_first_run_diff.json`(`9243b155…`)。
- 計器 5: `tests/golden/test_instrument5.py`。sign_token を持つ Claim の token の数 == |claim.value|。
- 不変の確認(sha256): Core 4 本(`f917f02` のまま)、期待値 2 本、原本 4 本、予測文書。
- **1 回目の生成順の記録**: Adapter 本体(comparators / resolve / registry_setup / recipes)の最終更新 15:32〜15:33 → 公式試験 test_instrument3.py 15:35 → 1 回目の JSON 15:38。予測 §3.4 の「公式試験より前」を満たしていない(実装担当が自己申告)。本体は 15:33 以降不変で、現在のコードで再生成すると一致する。「直す前」の文字どおりの証明ではないことを明記する。

## 2. 予測 §4 との突き合わせ(司令塔の席)

| # | 項目 | 予測 | 実測 | 当否 |
|---|---|---|---|---|
| 1 | 計器 3 state(1 回目) | 224/224(点) | **224/224** | ○ |
| 2 | pointers | 224/224(点) | **224/224** | ○ |
| 3 | recomputed(`==`) | 220〜224 | **224/224** | ○(上端) |
| 4 | 理由(写像) | 224/224(点) | **224/224** | ○ |
| 5 | normalization の再導出 | 77/77(点) | **77/77** | ○ |
| 6 | 直し / 期待値 / Core | 0〜2 / 0 / 0 | **0 / 0 / 0** | ○ |
| 7 | 計器 5 | 不一致 0/15 | **0/15**(1B は材料 0) | ○ |
| 8 | resolver の曖昧さ(99 本) | 0 | **0**(1B 60 + 5F 39) | ○ |
| 9 | 登録の数 | 6・2・4・9 = 21 | **21** | ○ |
| 10 | Core のインターフェース拡張 | 0 | **0** | ○ |
| 11 | Core の意味変更 | 0 | **0** | ○ |
| 12 | 新規モジュール / 追加行 / 試験 / 変異 | 7〜8 / 250〜450 / 20〜45 / 11〜14 | 本体 3 本(comparators 173・resolve 64・registry_setup 66 = 303)+ 試験側 7 本 / Adapter 合計 1547 行(C-1c 1214 から +333) / **49 本** / **12 本**(+ D-R3b) | 行 ○・変異 ○・**試験 ×**(過小)・モジュールは本体だけなら ○ |
| 13 | C-1 計画 §5 の「母集団を合わせるに変えると赤」 | 計器 3 では緑 | **緑**(D-R7、gate_only) | ○(計画の外れを確定) |
| 14 | 人間に見せる原本の癖 | 3 | **3**(新発見 0) | ○ |
| 15 | state が合って recomputed だけ違う Claim | 0〜4 | **0** | ○ |

当たり 14 / 外れ 1(試験本数の過小。C-1c と同じ向き)。**変異の予測は 1 本外れた**(D-R3、§3)。これは §4 の 15 項目の外ではなく、§3.6 の表の予測の外れとして数える: 変異 11 本中 10 本当たり、1 本外れ。

### 2.1 C-1 計画 §6 の席(先に封じた別の席)

計画は「計器 3 の初回の一致 210〜224」と予測した。実測 224 で範囲の上端。計画が外れの出どころとして挙げた「value_only の候補の順序(hits[0])・ambiguous(N) の数え方・diff phrase の分岐」は、どれも C-1c の写しの段で消えていた。

## 3. 変異(22 本)と D-R3 の外れ

表は `tests/adapters/xbrl/mutations.json`。A-* 10 本(C-1c、legacy スコープ、不変)+ D-* 12 本。D-R1〜R9・G1・G2 のうち **D-R3 だけ予測が外れた**: 予測「green(等価)、根拠 = c − p = 0 の Claim が 0 件」に対し、既定スコープの実測は **red**。理由は、司令塔自身が点 G で要求した境界試験(差 0 の sign)が diff == 0 を直接作るため。司令塔の予測は実データの門だけを根拠にしていて、自分が要求した単体試験を数えていなかった。

**過程の記録(規則の確認)**: 実装担当は当初、実測で red を見た後にスコープを gate_only に狭めて green にした。司令塔はこれを「規則を予測に合わせる操作」として差し戻し、D-R3 を既定スコープに戻して `prediction_miss: true` / `actual_first_measurement: red` で外れを固定させた。ランナーは miss の行について「外れが再現すること」を assert し、要約に外れの本数と id を出す(隠さない)。gate_only で green という事実は別行 D-R3b(予測は実測後に書いた = 予測の価値なし、と明記)に残した。

**D-R7**(ctx_ok の `== [member]` → `in`): gate_only(前段照合 + 計器 3)で green。**C-1 計画 §5 が「赤」と予測した変異が、224 件では赤くならないことを公式に確定**。守っているのは C-1c の単体試験(合成データ)だけ。

## 4. 登録(C-1e の計器 4 の入力)

| 種類 | 名前 | 数 | C-0 §3 の予測との関係 |
|---|---|---|---|
| scheme | xbrl(evidence, filing)・formula(operator, structural)。builtin は Core の既定 | 2 | 予測 2 ○ |
| 比較子 | equals_within・equals_within(pure*100)・ratio*100・pct_change(cur,prior)・diff(a-b) equals_within・builtin:sign(cur-prior)==direction | 6 | 予測 6 ○ |
| normalization | round・truncate・abs+round・abs+truncate | 4 | 予測 1〜2 **×**(C-0 は梯子を 1 つの表と数えた) |
| 理由 | POINTER_NOT_FOUND 4(no_element・no_element(unit not in XBRL)・no_element(ratio without fact)・no_prior_member_context)/ UNVERIFIABLE 5(no_subject・ambiguous(member)・ambiguous(elements)・state_word(no line)・prior is 0) | 9 | 予測「表 1」(単位が違う。表 1 枚 = 名前 9) |
| 合計 | | **21** | |

全部 **登録追加**。Core のインターフェース拡張 0(C-0 は provenance 欄で 1 と予測 → **C-0 の外れ、少ない向き**。Core の `Claim.provenance` が Mapping だったので Adapter 側で吸収できた)。意味変更 0(C-0 どおり)。分類の確定は C-1e。

## 5. 原本の癖(写した。直していない。人間が見る)

| # | 癖 | どこ | 224 件での影響 |
|---|---|---|---|
| a | pure×100 と ratio×100 は **|claim.value|** と比べる(符号を落とす) | comparators の pure100 / ratio100 | 1B の pure 3 件・ratio 4 件は全部正の数なので影響 0 |
| b | sign は差 0 を「減」に数える(`> 0` の else が −1) | comparators の sign | c − p = 0 は 0 件なので影響 0。D-R3 の境界試験だけが見ている |
| c | prior = 0 は Adapter が build 時に UNVERIFIABLE(比較子に届かない) | recipes | 0 件 |

これらを直すかは人間の判断。直すときは期待値も動く(224 件の再現が壊れる)ので、3 社目の前に決める。

## 6. 実装担当が自分で決めた点(12)と司令塔の扱い

| # | 決定 | 扱い |
|---|---|---|
| 1 | match_value は import せず写す(系譜試験 1 本を後から追加: 原本・vocabulary・comparators の 3 者で値一致) | 可。最初の報告で漏れ、司令塔の 1 便で直した |
| 2 | resolve は facts を引数で受け、instance を import しない | 可 |
| 3 | registry_setup.py を分離 | 可(Core を import する Adapter の file は recipes・run・comparators・resolve・registry_setup の 5 本) |
| 4 | equals_within は params の `abs_tolerance` の有無で絶対誤差モードを切替(224 件に 0 件) | 可。3 社目で名/人が出たときに初めて動く経路 |
| 5 | detail["normalization"] は梯子系だけ | 可(77 件の集計と整合) |
| 6 | depth は "value_match" 固定 | 可。depth の意味づけは C-2(将棋側の層の深さ)で決める |
| 7 | 曖昧さは文書ごとに集計(99 = 60 + 39) | 可 |
| 8 | 変異のスコープ機構(legacy / default / gate_only) | 可。ただし gate_only は「門の射程を測る」ためだけに使う |
| 9 | D-R3 のスコープ変更 | **不可、差し戻し**(§3) |
| 10 | tie-break の試験は合成の 2 語で再構成(SUBJECTS_73 では本物の tie が無い) | 可。XP-C1c-2 の 4 分岐の 1 つと整合 |
| 11 | run.py 未変更(contract.tolerance 欄が None に) | 可。CLI の出力に params を出すかは C-1e の論点 |
| 12 | first_run の生成順 | 記録(§1) |

## 7. 到達しない分岐(XP-C1c-2 の更新)

C-1c の 4 つ(ctx_ok の == [member]・round の境界・接続語無しの隣接・subject_of の tie-break)に、C-1d で **sign の差 0**(D-R3 の境界)と **名/人の abs_tolerance** が加わり **6 つ**。どれも単体試験(合成)だけが守っている。計器 3 の 224/224 はこれらに無言。

## 8. 止まる所

C-1d はここで止まる。次は C-1e(計器 4: C-1 で Core に入った変更を全部列挙して C-0 §3 の予測と照合。実測は「Core の変更 0・登録追加 21・インターフェース拡張 0・意味変更 0」)。C-1e は文書だけ。

## 9. 監査

独立の監査担当の判定は **GO**。監査担当が自分で測ったこと:

- 凍結 sha 44 行を開始時と終了時に照合、全部一致。Core 4 本・期待値 2 本・原本 4 本・ZIP 2 本・予測文書の sha を独立に再照合。
- 門 217 本 OK を 2 回、変異の要約「21 本 / 外れ 1 本(D-R3)」も再現。
- **計器 3 と 5 を、司令塔の試験コードを信用せず自分の script で `core.verify_all` を直接呼んで再現**: 224/224、15 件で不一致 0、1B は 0 件。理由の写像の catch-all に落ちる行が全部 bound(Core が reason=None を返す経路)であることを 224 件の走査で確認(None 同士の漏れ一致 0)。
- 比較子は `import audit_core` だけ。direction は params の ±1 整数(word ではない)。`_match_value` は vocabulary.match_value と `inspect.getsource` で byte 同一。
- 変異 3 本を自作: D-R2 再現 = red(**不一致は N049 の 1 件のみ**)、D-R9 再現 = red(recomputed 14 件)、resolver が最後の fact を返す = **red**(監査の予測は green、合成データの単体試験が固定していた。良い向きの外れ)。
- D-R3 の `prediction_miss` 機構は透明(本数と id を必ず印字、今回 1 件、司令塔の指示が記録済み)。D-R7 は予測文書に事前に「計器 3 では green」とあり事後の絞りではない。
- tie-break の試験は長さの違う 2 語(資産合計 / 純資産合計)に直され、tie-break を外す変異で今回は赤くなる(C-1c の穴が塞がった)。本体不変。
- 境界: Core を import する Adapter の file は 5 本、鍵の値 0、偽 HOME で ZIP 無しは `FileNotFoundError` で落ちる。

**記録事項(非ブロッキング、2 件)**:
1. 1 回目の JSON の生成が公式試験より後(§1)。Adapter 本体は保存前に確定し以後不変、現在のコードで再現すると一致するが、「直す前の盲検の 1 回目」としての証拠の強さは弱い。
2. D-R2 の note(と予測文書 §3.6 の根拠)は「N049・N078・N083 の符号が返る」と書いたが、N078・N083 は `diff(a-b)` の比較子で pct_change を通らない。実測の赤は N049 の 1 件から出ている。**司令塔の予測の根拠の数え間違い**(前期が負の Claim を比較子で分けずに数えた)。予測の当否(red)は変わらないが、根拠の記述を訂正する。予測文書は書き換えず、この結果文書に訂正を置く。

### 9.1 この段で学んだこと(手順)

- 「1 回目の実行は公式試験より前に保存する」は手順として書いただけでは守られない。次の段からは、1 回目の保存を**実装担当ではなく司令塔が、実装担当の本体が凍結された時点で**回す(保存の主体を分ける)。
- 変異の予測の根拠は「どの試験が見るか」まで書く。D-R3 の外れは、根拠を実データの門だけで書き、自分が同じ文書で要求した単体試験を数えなかったことから出た。
