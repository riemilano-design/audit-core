# 束縛の実装の記録 ― 封を書く**前**に、コード位置と実行経路で(2026-10-12)

人間の決定 `D-007`「束縛の実装を、**推測なしでコード位置と実行経路に紐付けて**記録。**文章での順序説明だけは不可**」。
**調査のみ。`audit-core/core`・`adapters`・`tests` の変更 0 行**(人間の禁止: 6 点の記録と封のコミットが終わる前の Adapter・Core 変更)。

**読んだ commit**: 開始時 HEAD `9c9fc62`、終了時 HEAD `93072bb`(並行して司令塔が docs 2 本を足した)。
**読み取り範囲は 2 つの sha で byte 単位で同一**(`git diff --stat 9c9fc62 93072bb -- audit-core/adapters/xbrl audit-core/core/py/audit_core audit-core/tests/golden audit-core/fixtures/xbrl/ai_prose_instance_2026-10-09.zip` が空)。行番号は両方で同じ。

## 【1】Claim の対象・属性・期間はどこで確定するか

**対象(主語)** は `extract.py:89`(`subject_of`)― `extract.py:98` の `i = head.rfind(word)` で数の左側を後方検索し、
`extract.py:102` が「**終わりの位置が最も右、同じなら長い語**」で決める(呼び出しは数の Claim が `recipes.py:406`、文章の Claim が `recipes.py:455`、語彙は P7 では `vocabulary.py:240` 経由の `vocabulary.py:111` `SUBJECTS_P6`)。
**属性(XBRL 要素)** は `instance.py:142`(`facts_for`)― `instance.py:154` の完全一致(+`SummaryOfBusinessResults` 変種)、外れたら `instance.py:156` の**部分一致**(`e.lower() in local.lower()`)、`instance.py:158` が `exact or loose` を**文書順**で返す。
**期間は文から確定していない** ― `facts_for` の期間フィルタ引数 `want_ctx`(`instance.py:152`)は**呼び出し元 0 件**(`grep -rn "want_ctx" adapters/ tests/` は定義行だけ)。
対の形(derived / threshold)は期間が**字で固定**(`recipes.py:249`・`311-312`・`335-336`・`181-184`・`481`・`496-497`・`512-513`。例外は `recipes.py:245` の `prev_year_phrase`「前連結会計年度は」が `recipes.py:249` で対を Prior1/Prior2 に替える 1 箇所)で、
**単一 fact の `direct_value` では期間の制約が一切なく、選ばれた fact の `context` がそのまま期間になる**(`recipes.py:219`)。
Claim の `modifiers.time_range` は `recipes.py:603`(`claim_to_recipe`)が `recipes.py:77`(`_period`)で **pointer の context から逆算**して作るため、**pointer と食い違いようがない(同語反復)**。population も `recipes.py:607-613` が pointer から作る。member だけは文から決まる(`extract.py:191` `claim_member_B` / `extract.py:167` `resolve_members`、呼び出しは `recipes.py:572-575`)。

## 【2】Pointer は値の比較より前に確定するか ― **形によって逆**

**単一 fact の `direct_value`(`N219`)では、pointer は値の比較の後に、値の比較によって決まる。**
`sys.settrace` の行順実測: `212`(全候補に `V.match_value`)→ `213`(一致しない候補を捨てる)→ `214`(分岐)→ `218`(`hits[0]`)→ **`219`(`claim["pointer"] = …`)**。
対の形(`T023`)では **pointer が先**: `511`→`512`→`513`→`514`→`515`→`516`(`pairs[0]`)→**`517`(pointer)**→`519`→`520`(符号の判定)。
**確定後に値によって pointer が変更される経路は 0 件** ― pointer 代入行 {`193`,`219`,`262`,`269`,`278`,`316`,`340`,`367`,`384`,`484`,`501`,`517`} の実行を claim id ごとに数え、
pointer を立てた Claim **217 件のうち 2 行以上実行した Claim は 0 件**(`N219`=[`219`]、`T023`=[`517`])。
`_apply_flow_sign`(`recipes.py:133`)は pointer を**読む**だけ(`recipes.py:142-145`)で書き替えない。Core 側 `verify.py:80-99` は渡された pointer を順に解決するだけで選び直しの分岐を持たない。

## 【3】複数の Fact が候補になったときの選択・棄却

候補集合は (a) `instance.py:150`(`ctx_ok` ― member か素の連結 context だけ)+ `instance.py:154/156`(完全一致 → 部分一致)で作られ **期間で絞らない**、
(b) `recipes.py:210` で単位 `JPY` に絞る、(c) `recipes.py:212-213` で **Claim の数に一致しない候補を全部捨てる**、
(d) 主語があれば `recipes.py:218` の **`hits[0]`**、主語が無ければ `recipes.py:215-216` で要素の家族が 1 つでも束縛せず `recipes.py:230` `no_subject`、家族が 2 つ以上なら `recipes.py:236` `ambiguous(elements)`。
**同点の切り方は「文書順の先頭」だけで、期間・`decimals`・一致の種類(round か truncate か)による優先度は実装されていない** ―
`hits[0]`(`recipes.py:218`・`268`)、`pairs[0]`(`recipes.py:190`・`315`・`339`・`500`・`516`)、`cur[0]`(`recipes.py:278`・`367`)、`(hit or cur)[0]`(`recipes.py:383`)。
`recipes.py:215` の `sorted` は家族の**数を数えるため**だけで順位付けに使っていない。文書順は `instance.py:96` の `facts.append` 順で `instance.py:158` が保つ。

## 【4】GROUNDED の直前に整合性を再検証しているか ― **していない。Core の契約も要求していない**

`verify.py:124` は `state = State.GROUNDED if comparison.match else State.VALUE_MISMATCH` の 1 行で、直前の `verify.py:118-119` は comparator を呼ぶだけ。
**Core の契約は pointer に概念・期の一致を要求していない(要求なし)**: `model.py:52-53`(`Pointer`)は `scheme` と `locator` の **2 欄のみ**で概念・期間の欄が無く、`model.py:83-86`(`Contract`)は `comparator`/`params`/`formula`/`reference` のみ。
`claim.subject` を読む場所は全体で `run.py:35`(JSON への書き出し)の **1 件だけ**で comparator は 0 件。`claim.modifiers` を読むのは `verify.py:23-26`(provenance へ写すだけ)と `run.py:39-42` のみ。
**実測の裏取り**: `N219`・`T023` の Claim を `dataclasses.replace` で `subject="まったく無関係な主語"`・`unit="トン"`・`population="member:WRONG"`・`time_range=("CurrentYear/Duration","XXX")` に差し替えて `core.verify` を呼び直しても、**両方とも GROUNDED のまま変わらない**。

## 【5】Claim の値を参照している箇所の全列挙

**選択・棄却(どの fact が pointer になるかを決める)で Claim の数を読む箇所は 6 件**:
`recipes.py:212`(全候補に `V.match_value`)/ `recipes.py:213`(一致しない候補を捨てる)/ `recipes.py:214`(一致 0 件なら対の形へ落ちる分岐)/
`recipes.py:253`(`V.match_value(fa["value"]-fb["value"], …)` と `recipes.py:254-256` の `if how: found=…; break` で**どの要素・どの期間の対**を pointer にするかを数で決める)/
`recipes.py:382`(単位 名・人 の `hit = [f for f in cur if abs(f["value"] - num) <= 0.5]` と `recipes.py:383` の `chosen = (hit or cur)[0]`)/
`extract.py:114`(`own_sign_match`、`abs(float(g) - num) < 1e-9` で窓の中の**どの正規表現一致**を採るかを数で決める。呼び出しは `recipes.py:305`。fact ではなく文側の選択)。
**pointer 確定後の比較だけで読む箇所は 17 件**: `recipes.py:155`・`197`・`321`・`345`・`370`、`comparators.py:84`・`92`・`93`・`98`・`99`・`123`・`144`・`163`・`181`・`182`・`275`、`core/py/audit_core/registry.py:108`(`_equals_comparator`。comparator 名 `"equals"` を使う recipe は **0 件**なので本番では走らない)。
**0 件と明記する範囲**: `instance.py`・`resolve.py`・`registry_setup.py`・`core/py/audit_core/verify.py` に Claim の値を読む行は **0 件**。
使った grep パターン 10 本は §末に記載。

## 【6】`N219`・`T023` の実際の実行経路と、誤った選択が起きた行

実行は `tests/golden/_instrument.run_verification("S100Z4Q1", V.P7, …)` + `fixtures/xbrl/ai_prose_instance_2026-10-09.zip`(fact 863・recipe 415)。

### `N219` ― 誤った選択が起きた行は **`recipes.py:212-213` と `recipes.py:219`**

文: 「有利子負債は1年内返済予定分234百万円と長期借入金275百万円の合計510百万円(前期末843百万円)まで減少しており…」

| 段 | 実測の戻り値 |
|---|---|
| `extract.iter_numbers`(`extract.py:54`) | `(35, 41, 510000000.0, '円', 1000000.0)`(漢数字経路 `extract.py:62-79`) |
| `extract.claim_member_B`(`extract.py:191`) | `(None, None)` |
| **`extract.subject_of`(`extract.py:89`)** | **`('長期借入金', ['LongTermLoansPayable','LongTermBorrowings'])`** ― 「有利子負債」は `vocabulary` に `('有利子負債', ['InterestBearing'])` として**在る**が、「長期借入金」の方が数の直前で右にあるため `extract.py:102` が後者を採る |
| **`instance.facts_for`(`instance.py:142`)** | **2 件を文書順: `LongTermLoansPayable@Prior1YearInstant`=510,637,000 と `@CurrentYearInstant`=275,773,000** ― **期間で絞らないため前期末の fact が候補に入る** |
| `recipes.py:211` | `is_diff=False` |
| `vocabulary.match_value`(`vocabulary.py:130`) ×2 | Prior1 が **`'truncate'`**(`vocabulary.py:137-138` の `0 <= 510,637,000 − 510,000,000 = 637,000 < 1e6`)、Current が `None` |
| `recipes.py:213` → `218` → **`219`** | pointer = `xbrl:jppfs_cor:LongTermLoansPayable@Prior1YearInstant` |
| Core | `verify.py:84` が 510,637,000 を得て `verify.py:119` → `comparators.py:98-101` → `'truncate'` → `verify.py:124` **GROUNDED** |

**原因は 3 つの積**: ① 候補集合に期間の制約が無い(`instance.py:152` の `want_ctx` 呼び出し元 0 件)
② **数の一致だけで pointer を決める**(`recipes.py:212-213`)③ 637,000 円の差を truncate の段が吸う(`vocabulary.py:138`)。

### `T023` ― 誤った選択が起きた行は **`extract.py:98`・`extract.py:102`(起点)と `recipes.py:511-517`**

文: 「…売上原価率は前期の67.5%から70.2%へと2.7ポイント上昇し、売上総利益率は32.5%から29.8%へと低下しております。」

| 段 | 実測 |
|---|---|
| **`extract.subject_of`** | **`('売上総利益', ['GrossProfit'])`** ― `SUBJECTS_P6` に「売上総利益**率**」が**無く**(実測 `False`。「売上総利益」を含む項目は 1 件のみ)、`extract.py:98` の `rfind` が「売上総利益率」の**部分文字列**に当たる |
| `instance.facts_for` ×2(`recipes.py:512-513`) | `GrossProfit@CurrentYearDuration`=11,334,658,000 と `@Prior1YearDuration`=12,018,937,000。**この要素の pure(比率)fact は 0 件。instance 全体の pure fact 114 件のうち 0.325/0.298/32.5/29.8 に近いものは 0 件 ― 率の fact は存在しない** |
| `recipes.py:514`→`516`→**`517`** | pointer = `[GrossProfit@CurrentYearDuration, GrossProfit@Prior1YearDuration, builtin:sign(cur-prior)]` |
| `recipes.py:519-520` | `actual=-1`(差 −684,279,000)が `direction=-1`(`extract.py:42` の `DIRECTION_WORDS["低下"]`)と一致 |
| Core | `comparators.py:187`・`204-207` → `verify.py:124` **GROUNDED** |

**この枝には主語の「属性」(率か額か)を見る条件が一つも無く、文の単位「%」も `_build_raw_text_claims` では一切読まれない。**
threshold の Claim は `claim.value` が `None`(実測)なので、**値による検査が率と額の取り違えを捕まえる経路は構造上存在しない。**

---

## 実行して確かめたこと / 静的に読んだだけのこと

**実行して確かめた**(scratchpad の読み取り専用スクリプト 7 本。**本体への print 挿入・変更は 0**):
最終 `Result`(state / pointers / comparator / recomputed / provenance / Contract)、`subject_of`・`claim_member_B`・`facts_for`・`match_value`・`hits`・`pairs` の実際の戻り値と候補の並び順、
`SUBJECTS_P6` に「売上総利益率」が無いこと、率の pure fact が 0 件、`sys.settrace` による関数の呼び出し順と**行の実行順**、pointer 代入行の実行回数(217 件中 2 回以上は 0 件)、
Claim の欄を壊しても GROUNDED が変わらないこと(【4】)。

**静的に読んだだけ**: `model.py:44-104` の欄の定義、`registry.py` の登録と既定 comparator、`registry_setup.py` の 28 登録、
P1/P5F/P6 向けの枝(`_build_point_diff_claim`・`_apply_flow_sign` の束縛側・`equals_within` の `abs_tolerance`/`flow_convention` 枝・`ratio*100`・`pct_change`・`diff(a-b)(pure*100)`)、`instance.py:97-122` の iXBRL 経路
― **P7 の `N219`/`T023` の経路では走らないため実測していない。**

## 確かめられなかったこと(席の申告。司令塔はこれを埋めない)

- **他の文書・他の profile(P1/P5F/P6)での挙動は測っていない**(材料 1 件・profile P7 の 1 run のみ)。
  したがって「同点の切り方が文書順しかない」ことが**実際に 2 件以上の候補で発火した件数は未測定** ―
  **`N219` では値のふるい(`recipes.py:213`)を通った候補が 1 件だけだったので、`hits[0]` は今回「同点の切り方」としては働いていない。**
  誤りの原因は候補集合の期間無制約と truncate の段である。
- 本番の出口(`deliver`・冊子)がこの Adapter をどう呼ぶかは、禁止指定のため実行・確認していない。
- `vocabulary.py:118` `tol_of` は `match_value` から呼ばれておらず**本番の呼び出し元 0 件**(試験 `test_vocabulary.py:53-65`・`test_lineage.py:168-174` のみ)。
  今回の束縛判定の許容幅は `tol_of` ではなく `vocabulary.py:135-138` の `unit/2` と `unit` で決まっている。

## 項目 5 で使った grep パターン(全部)

```
grep -rn "match_value" audit-core/adapters/xbrl/*.py audit-core/core/py/audit_core/*.py
grep -rn 'claim\.value\|claim\["value"\]' audit-core/adapters/xbrl/*.py audit-core/core/py/audit_core/*.py
grep -nE 'claim\["value"\]|claim\.value|\btarget\b *=|\bnum\b|\bsigned\b' audit-core/adapters/xbrl/*.py audit-core/core/py/audit_core/*.py
grep -nE '\["value"\]|\.value' audit-core/adapters/xbrl/recipes.py | grep -E 'abs\(|<=|==|>|<'
grep -n "num\b" audit-core/adapters/xbrl/recipes.py
grep -n 'claim\["pointer"\] *=\|"pointer":' audit-core/adapters/xbrl/recipes.py
grep -rn "want_ctx" audit-core/adapters audit-core/tests
grep -nE 'claim' audit-core/adapters/xbrl/instance.py audit-core/adapters/xbrl/resolve.py audit-core/adapters/xbrl/registry_setup.py
grep -rn "claim\.subject\|claim\.modifiers" audit-core/adapters/xbrl/*.py audit-core/core/py/audit_core/*.py
grep -n '"equals"' audit-core/adapters/xbrl/*.py        # 0 件
```

`git status --short` は終了時に**空**。repo 内への書き込み 0、`core`・`adapters`・`tests` の変更 0。
