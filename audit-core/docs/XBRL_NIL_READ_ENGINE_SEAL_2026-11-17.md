# 封: engine の inline XBRL の読み取りが「自己閉じの空の欄」を始まりの tag と読まないようにする直し(便 NRE。`adapters/xbrl/instance.py` の式 1 行。旗なし。既定 P27 の規則は不変)― 2026-11-17

便 NR(封 `docs/XBRL_NIL_READ_SEAL_2026-11-17.md` 720a473d・記録 44ba3e61・結果 `docs/XBRL_NIL_READ_RESULT_2026-11-17.md` f92adcdb)が効きを数えた engine の読み取りの欠陥を、engine の側で直す封。**engine(`adapters/`)を変える。** 実装・測定・記録はまだ無い(作業木は 68c0797e のまま 0 行)。取得 0・0 USD・LLM の席を呼ばない・新しい読み 0。`main` へはマージしない。外には書かない。

## §0 材料と決めごと

### §0-1 測った事実(この封を書く前に司令塔が 0 USD で見たもの)

1. 便 NR の記録(`fixtures/xbrl/nil_read/states_2026-11-17.json`): TSS の 400 本のうち切れた本 372・行 24,531。自己閉じ 9,166 個(184 本)。そのままの engine で作られた fact 128(18 本)・消えた fact 5,323(184 本)。「自己閉じを消した入力」に替えると state が変わる行 207(81 本)・直した入力でだけ値が合う行 86・そのままでだけ値が合う行 0。
2. **下調べ**(作業木とは別の detached の木。68c0797e に §1 の 1 行だけを当てた。script は scratchpad。どの枝にも載せない): 直した engine に**そのままの入力**を渡した本の記録が、便 NR の script の「直した入力」の本の記録と **372/372 本で同じ**。便 NR の独立の読みの fact の列 = 直した engine の fact の列も 372/372 本。
3. 同じ下調べの木で `tests/adapters tests/core tests/fixtures` は 1776 passed・1 skipped(赤 0)。`tests/measure` の全数は、1 行を未 commit のまま当てた木で 96 failed・21 errors・6086 passed・49 skipped。1 行を捨てる commit にして、赤だった 54 file だけを走らせ直すと **92 failed(48 file)**・2055 passed・27 skipped。理由を読んだ赤は全部 engine の留め(§2-3 の型)。**92 本の全部の理由を 1 本ずつ読んではいない**(読んだのは型ごとの代表)。
4. `instance.py` の今の sha16 `f2d9e040f19adebf` を字で持つ追跡 file は 11 本(試験 4 本・記録 7 本)。今の束ねた指紋 `adapter_xbrl_py_sha256` は `5221d3c9…`(16 file)。`fixtures/frozen_bundle_sha.py` の対象は 37 本。
5. `load_instance` の呼び出し元は `adapters/xbrl/` の 4 file(verify_external・prose・verify_document・recipes)。profile の引数は無い。`sales/` の code は `load_instance` を呼ばない(grep。英文短信の側の点検は別の読み取りを使う)。
6. 便 NR の棚卸し: 手元の EDINET の ZIP 418 本(`edinet` 281・`edinet-demo-cabocia` 3・`edinet-fresh-2026-10-21` 40・`edinet-prior-2026-11-02` 94)と便 2026-11-09 の短信 17 本は全部 `.xbrl` の経路。`.htm` の経路を通るのは便 TSS の包み方だけ。

下調べは本物ではない(1 行を手で当てた木・門は一部並行に走った)。この封の数は §3 の予測として置き、本物の実装で測り直す。

### §0-2 司令塔の決定(人間の言葉「任せる進めて」2026-11-17 = 便 NR の報告の「決めていただくこと (1) engine の読み取りの欠陥を直すか。直す場合は別の封を書き、直した engine で同じ数が出ることを予測に置いて、実装 → 監査 GO。`main` へのマージはしない」を受けた委任。engine の変更を含む)

- **旗(profile)の後ろに置かない。** 理由: (a) これは結ぶ規則でなく読み取りの欠陥で、「空の欄の context に次の欄の値を入れた fact」が正しい profile は無い。(b) `load_instance` は profile を受けない。旗にするには呼び出し元 4 file に引数を通すことになり、触る面が 1 行から 5 file に広がる。(c) `.xbrl` の経路(EDINET の便の全部・便 2026-11-09)は式が別で 1 行も通らない。
- **この決めで変わるもの(人間に報告する)**: `.htm` の経路で自己閉じを持つ入力は、**既定 P27 を含む全部の profile で** fact の列が変わる。既定の名前 `DEFAULT_PROFILE = "P27"` と P27 の規則は変えない。過去の記録(TSS・PS・NR・1b・第 2 便)は**作り直さない・書き換えない**。当時の数は当時の engine の commit で再現する、と門に宣言する。
- 人間の決定に残すもの: `main` へのマージ・外に書くか・TSS の系列の記録を直した engine で取り直すか。

## §1 直しの字(engine。1 行の置き換え)

`adapters/xbrl/instance.py` の `.htm` の経路の式:

```
前: r'<ix:nonFraction([^>]*)>(.*?)</ix:nonFraction>'
後: r'<ix:nonFraction([^>]*)(?<!/)>(.*?)</ix:nonFraction>'
```

意味: 属性の並びの直後の `>` の 1 字前が `/` である tag(自己閉じ)を、始まりの tag と読まない。

- 当たらなくなる例(fact を作らない): `<ix:nonFraction name="ex:A" contextRef="Prior" unitRef="JPY" scale="6" xsi:nil="true"/>`。この後ろに `<ix:nonFraction name="ex:A" contextRef="Current" unitRef="JPY" scale="6">120</ix:nonFraction>` が続くとき、直す前は「Prior の ex:A = 120 百万」が 1 つ、直した後は「Current の ex:A = 120 百万」が 1 つ。
- 変わらない例: `<ix:nonFraction name="ex:A" contextRef="Current" unitRef="JPY" scale="6">120</ix:nonFraction>` だけの入力(自己閉じが無い)は、前後で fact の列が同じ。
- 変わらない例: 属性の値の中に `/` が在る tag(`format="ixt:numdotdecimal"` や URL の形)。見るのは `>` の直前の 1 字だけ。

ほかの行(値の作り方・scale・sign・`.xbrl` の経路)は 1 字も変えない。

## §2 engine の範囲

### §2-1 触る file

`adapters/xbrl/instance.py` の 1 行だけ(numstat で 挿入 1・削除 1)。`core/`・ほかの `adapters/` は 0 行。`tests/adapters/xbrl/test_boundary.py` の import 一覧は広げない。

### §2-2 触る枝の中の人間の決定(字も振る舞いも壊さない)

- 既定 `DEFAULT_PROFILE = "P27"`(人間の決定)。名前も規則も変えない。
- profile の一覧と旗(P27〜P33E)。1 つも足さない・変えない。
- `.htm` の経路を通る入力は便 TSS の包み方だけ(§0-1 の 6)。EDINET の便の全部はこの直しの**後ろに居ない**(式が別)。

### §2-3 既存の門の engine の留め(実装の便で同じ便に宣言された遷移を足す。測った当時の値は消さない。前例 T・PB・RB)

下調べで赤だった 48 file(commit 後)の型。実装の席は本物の木で数え直し、型ごとに前例と同じ形で直す。

1. **sha16 を字で留める門**(`instance.py` の `f2d9e040f19adebf`): `test_xbrl_cd_seal.py`・`test_xbrl_customer_report_fix_seal.py`・`test_xbrl_default_p26_seal.py`・`test_xbrl_p26_seal.py`。宣言の行 `(新しい sha16, "docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md")` を足す。記録 7 本の中の sha16 は当時の値で、触らない。
2. **束ねた指紋・frozen bundle を「封の時の値か宣言された遷移」で留める門**(customer_report 系・default_p26・default_p27・p26_seal・p27_engine_result・p27_result・period_bind_result): 新しい指紋の値を宣言に足し、`fixtures/frozen_bundle_sha.py` の世代を +1(対象の本数は変えない)。
3. **「封(か engine の commit)から engine 0 行」で留める家族の門**(nscan・jtypes・pswap・pswap_idmap・rmix・pbind・t5y・tperiod と、その結果の門の「記録の頭が頭の検査を通る」): `test_xbrl_rmix_seal.py` の「宣言された遷移だけを許す部品」に NRE の遷移(触った file 1 本・行数 挿入 1 削除 1・sha16・指紋・封の path が履歴に在る・この封の後に `instance.py` を最初に触った commit ただ 1 つ)を足す。
4. **「封の後に engine・入力に変更が無い」を履歴で見る門**(attr_tally・kam・labelonly・nonfunc・nil_read・plan_source・point_prior・ritual・tanshin・tanshin_self・tanshin_self2・tanshin_self_inject・yuho_sections の封と結果の門): 各門の今の作りに合わせて、NRE の engine の commit ただ 1 つを宣言された遷移として許す。「記録の指紋 = 今の engine」を見る検査は「記録の指紋 = 記録を作った時の engine(NRE の前)で、今の engine はそこから宣言された遷移だけ離れている」に替える。**記録は作り直さない。**
5. **`test_xbrl_p27_seal.py` の「5 file は挿入だけ」**(test_7・m5): この直しは既存の行の置き換え。P27 の封の範囲(5 file)に `instance.py` が入っているなら NRE の 1 行を宣言された置き換えとして許す。入っていないなら門の読み方を報告して止まる。
6. **欠陥が在ることを作り物で確かめている試験**(NR の封の門 c_2・c_6・c_7・PS の封の門 c_8 と、それに連なる d_1・i_2): docstring に「engine が直ったら赤くなる」と書いてある。**直った後の形に書き直す**(同じ作り物で、そのままの engine が「作られた fact 0・消えた fact 0」を出し、独立の読みと同じ列になること)。直す前の欠陥の形は、試験の中の「直す前の式」の写しを使う参照の関数で残す(式は試験 file の中に置き、engine からは読まない)。
7. `test_xbrl_axis3_decision.py` の `LATER_ENGINE_COMMITS` は前例どおり次の便。
8. 新しい門で engine の留めを定義するときは `ENGINE_LATER`・`UNTOUCHED`・`PIN_DEF`・`LATER_ENGINE_COMMITS`・`FROZEN_LATER`・`ENGINE_TRANSITIONS` を行頭の名前に使わない。

上の型に入らない赤が本物の木で出たら、実装の席は直さずに理由を報告して止まる。

## §3 事前予測(実装より先に固定。結果を見てから書き換えない。外れは外れとして残す)

NRE-1〜NRE-3 は下調べ(§0-1 の 2)で値を見ている。外れうるのは「下調べの木と本物の実装が違う」ときだけで、当たっても司令塔の見立ての強さにはならない、と先に書く。NRE-4〜NRE-7 は見ていない。

| # | 予測 | 外れ方 |
|---|---|---|
| NRE-1 | 直した engine に**そのままの入力**を渡した行が、便 NR の記録の「直した入力」の行と、切れた本 **372 本の全部**で同じ(行 24,531。state と `safe_reason` の字) | 1 本でも違えば、engine の直しは便 NR の「直した入力」と同じでない。NR の数(207・86・0)を engine の直しの効きとして言えない |
| NRE-2 | 直した engine で「そのまま」と「自己閉じを消した入力」の fact の差は、作られた fact **0**・消えた fact **0**(372 本) | 1 つでも残れば、式がまだ自己閉じを拾うか、正しい tag を落としている |
| NRE-3 | 直した engine の「そのまま」を、TSS の記録(直す前)の行と比べると、state が変わった行は **207**(81 本)・直した engine でだけ値が合う行 **86**・直す前でだけ値が合う行 **0** | 数が 1 でも違えば NRE-1 と同じ意味で外れ |
| NRE-4 | `.xbrl` の経路の ZIP(EDINET 418 本・便 2026-11-09 の 17 本)で、直す前と後の `load_instance` の fact の列が**全部の本で同じ**(違う本 0) | 1 本でも違えば「`.xbrl` の経路は 1 行も通らない」という読みが誤り。旗なしの決めを人間に返す |
| NRE-5 | 包んだ 372 本の `.htm` に、自己閉じでないのに直した式が拾わなくなる `ix:nonFraction`(終わりの tag を持つのに落ちる fact)は **0**。数え方: 直す前の式が拾う始まりの位置のうち自己閉じでないものの数 = 直した式が拾う数 | 1 つでも在れば lookbehind が正しい tag を落としている |
| NRE-6 | 留めの連動で触る試験 file は **44 本以上 56 本以下**(新しく足す試験 file は数えない) | 43 以下なら下調べの赤の一部は別の理由だった。57 以上なら下調べが留めを数え漏らした |
| NRE-7 | 実装と留めの連動の後、`tests/measure` の全数と `tests/adapters tests/core tests/fixtures` は**赤 0**。§2-3 の型に入らない赤で実装の席が止まる回数は **0 回か 1 回** | 2 回以上止まれば、司令塔は留めの型を読み切れていなかった |

## §4 採用の基準

NRE-1・NRE-2・NRE-4・NRE-5 が全部当たりで、独立監査が GO のときだけ engine の 1 行を commit する。どれかが外れたら engine は commit せず、外れを結果の文書に書いて人間に返す。NRE-3・NRE-6・NRE-7 の外れは commit を止めない(外れとして書く)。

## §5 測り方(全部 0 USD)

- `measure/xbrl_nil_read_engine_2026-11-17.py`(入口 `states --out`・`--check`)。便 NR の script を sys.modules を汚さない形で読んで**呼ぶ**(包み方・行の付け方・消す式・独立の読み)。記録 `fixtures/xbrl/nil_read_engine/states_2026-11-17.json`。
- 「直す前」の値は engine を戻して作らない。TSS の記録(そのまま・直す前)と便 NR の記録(直した入力・直す前の engine)を字で読む。NRE-4 と NRE-5 の「直す前の式」は script の中に式の写しを置いて数える(engine の旧い blob を `git show` で読んで式の行が写しと同じことを門で確かめる)。
- 記録に持たないもの: 文・値・要素名・context の字・会社名・証券コード・docID。本は # で指す。時間以外は 2 回走らせて byte で同じ。
- 試験: `tests/adapters/xbrl/test_instance.py` に §1 の 3 つの例(作り物の ZIP)。封の門 `tests/measure/test_xbrl_nil_read_engine_seal.py`(順序は commit の順で: 封 → engine の commit。engine の差分が `instance.py` の挿入 1・削除 1 だけ・式の字が §1 と同じ・記録の集計が行からの数え直しと一致・つなぐ関数を作り物で本物のまま走らせる・非対称な例(作られた fact と消えた fact の数が違う作り物)・文や値や要素名が無い)。門は変異で赤を確かめる(式を戻す・lookbehind を `(?<!\s)` に・記録の数を 1 変える・fact の差の向きを逆に・NR の記録の代わりに TSS の記録と比べる、など。戻して byte 一致)。
- engine の commit と留めの連動・試験・script・記録は同じ便で、独立監査 GO の後に commit する(前例 T・PB)。結果の文書と台帳はその後の便。

## §6 言えないこと

1. 直すのは自己閉じの読み方だけ。`.htm` の経路のほかの読み取り(入れ子・`ix:continuation`・負の表記の format・属性の値の中の `>`)は見ていない。
2. 効きを数えたのは TSS の 400 本の states だけ。型の読み・注入(1b)・near・第 2 便・便 PS のサマリーの数は、直した engine で取り直さない。それらの記録は直す前の engine の数のまま残る。
3. NRE-1〜NRE-3 は下調べで見た値で、予測としては弱い。
4. 英文短信の側(`sales/`)は `load_instance` を呼ばないことを grep で見ただけで、数は測らない。
5. この直しで「短信の概況の文を engine が正しく結べる」とは言えない。便 NR の結果のとおり、変わるのは行の 1% に満たない。

## §7 作法と順序

封(この文書。文書だけ)→ 実装(step-implementer。git は触らない)→ sha256 で凍結 → 新しい step-auditor → GO で commit(パス指定)→ 全数の門 → 結果の文書・台帳 → 引き継ぎ。`main` へはマージしない。
