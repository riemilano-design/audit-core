# Core 接続 C-2 の計画と予測(封印) ― 将棋の Golden Master(c5)を薄い Python Adapter で Core に繋ぐ

> **この文書は将棋 Adapter のコードを 1 行も書く前に封じる。** 封じた後は本文を変えない(訂正は日付つきの追記か、結果文書に書く)。予測を当てるために範囲・規則を動かさない ― 外れは外れのまま記録する。
>
> **前提**: [CORE_CONNECTION_C0_2026-10-06.md](CORE_CONNECTION_C0_2026-10-06.md)(封印 `6c6973b`)§5 の計器 1・2・4、[CORE_CONNECTION_C1_PLAN_2026-10-06.md](CORE_CONNECTION_C1_PLAN_2026-10-06.md) §7 の人間の決定 3(C-2 の言語の範囲)、人間の決定(2026-10-06): 「C-1g の後に C-2 を計画する。c5 の Golden Master(packet・identity・seat_runs・g8・g9)を Claim / Evidence Pointer / Contract / Result に対応づけ、**Core の変更 0 で Python の薄い将棋 Adapter が繋がる**という予測を封じる」。
>
> **Base**: `d0fe6e8`(C-1g の予測の封)。Core 4 本は `f917f02` から不変。c5 の Golden Master は Base で rc=0(封の前の門、2026-10-06 に司令塔が回した: 「期待値のとおり … packet 22aee8fe696d0262・門 6 種・冊子 4 冊・入力 47 ファイル」)。
>
> **C-1g との関係**: C-1g(XBRL の profile P6)は実装中で、この文書と触るファイルが重ならない(C-1g = `adapters/xbrl/`・`tests/adapters/xbrl/`、C-2 = `adapters/shogi/`・`tests/adapters/shogi/`・`fixtures/shogi/`)。**C-2 の実装は C-1g のコミットの後に始める**(Core 不変の証拠を 1 本の線で追えるようにする)。

## 1. 範囲(C-0 の C-2 の文言との差を先に言う)

C-0 §1 の表は C-2 を「将棋の門(exit_verification・check_answer・hypothesis の汎用部)を Core 経由にする」と書いた。**この C-2 はそれをしない。** 理由: 将棋の門は TS(`hypothesis.ts` H-1〜H-11・`packetRef`・`observationPacket`)と Python(`exit_verification.py`・`check_answer.py`)の 2 言語で、中身を Core 経由に置き換えるには C-1 計画 §7 の決定 3(Core を 2 言語で持つか、JSON の契約で跨ぐか)が先に要る。その決定の材料を作るのが、この C-2 である。

**この C-2 がすること**: 将棋の検証器のうち **H-9(packetRef の実在と値の一致)の判定**を、将棋側のコードを 1 行も触らずに、**Python の薄い Adapter + Core の `verify_all`** で再現し、TS の H-9 の結果と**観測 1 件ごとに**照合する。XBRL の C-1d(計器 3 = 224 件を Core 経由で同値)の将棋版。

**この C-2 がしないこと**: 将棋の門の置き換え(計器 1 の関数レベル Golden は**この段では動かさない** ― 将棋側の差分が 0 行なので同値は自明で、測っても意味が無い。正直に「未測」と書く)。`check_answer` の数の照合(検査 1)・`exit_gate` の p1 の数(数が材料に在るか)の再現 ― 数と材料を結ぶ束縛が要り、それは I-7(未着手)の仕事で薄くない。集計行の**数え直し**(`recountRowProblems`。§7)。

## 2. 対応表(将棋の何が Core の何か)

c5 の Golden Master(`docs/golden_master/c5_expectation.json`)の 5 節と Core の 4 層の対応。

| Golden の節 | 中身 | Core での位置 | C-2 で使うか |
|---|---|---|---|
| `inputs` | どの実物を測るか(人が書く) | Adapter の入力(packet・席の封筒の場所) | 使う(読むだけ) |
| `identity` | 入力 47 ファイルの sha256 | **証拠の同一性**。Result の provenance に packet の `file_sha256` を写す | 使う(packet と席の封筒 5 本の sha を 1 回目の出力に書く) |
| `packet` | packetId・canonical sha・problems 0 | **証拠の本体**。Pointer `packet:<path>` の解決先 | 使う |
| `seat_runs` | 7 run・席の封筒 5 本・統合 4 本 | **Claim の出どころ**。席の封筒の `items[].observations[]` が Claim | 使う(統合の封筒は packetRef を持たないので Claim にしない。§3) |
| `g9.hypothesisCheck` | 58 件 × 12 検査の判定。**H-9 は 58 件とも skip**(packet が渡されていない。参照 213 件) | **Result の層の参照値は Golden に無い**。TS の H-9 を packet つきで 1 回回して参照を作る(§6) | 使う(参照の作り方が C-2 の新しい道具) |
| `g9.exit_gate` / `check_answer` / `check_structure` | Python の門 3 本 | 門の判定。本編の集計の印は **0 件**(exit_gate の報告「本編に集計の印が 0 件(packet の集計は 26 行)」)なので (xi) の Claim は c5 に無い | 使わない(c5 に材料が無い) |
| `g9.seatOutputCheck` / `integrationCheck` | 封筒・統合の形の検査 | 封筒の検査で Claim ではない | 使わない |
| `g8` | PDF の 3 つの数 | 組版の封で Claim ではない | 使わない |

**4 層への写し**(観測 1 件 = Claim 1 件):

| 層 | 将棋の材料 | Core の欄 | 値の決め方 |
|---|---|---|---|
| Claim | `items[i].observations[j]`(`obsId`・`path`・`value`・`unit`・`packetRef.path`) | `id` = `<runId>/<seatFile>#<hypothesisId>/observations[j]`、`form` = path が `aggregates.` なら `AGGREGATE`、`facts.` なら `DIRECT_VALUE`、`subject` = `packetRef.path`、`value` = 数なら float、文字列なら **None**(文字列は `Contract.params["expected"]`。§7)、`unit` = `unit`、`modifiers` = **全部空**(population None・time_range ()・normalization None)、`provenance` = {`hypothesis_id`・`kind`・`obs_id`・`value_is_number`} | **文(`statement`)は Claim に入れない・出力にも書かない**(顧客の対局の記述。sha だけ) |
| Evidence Pointer | `packetRef.path` | `Pointer(scheme="packet", locator=path)`、1 件につき 1 本 | 文法は `lib/packetRef.ts` の 2 つの正規表現(`AGGREGATE_REF_RE`・`FACTS_REF_RE`)を **値で写し、系譜試験で TS の字面と比べる**(XBRL の系譜試験と同じ型) |
| Contract | H-9 の「`canonicalJson(value)` が一致」 | `comparator = "canonical_json_equals"`、`params = {"expected": <観測の value>}`、`formula` None、`reference` None | 比較子は 1 つ。数も文字列も canonical JSON の文字列比較(TS と同じ規則を Python に写す: 鍵の並びを揃えた `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=False)`。**TS の `canonicalJson` と同値かは系譜試験で 213 件の値で確かめる**) |
| Result | H-9 の 3 つの結果 | ok → **GROUNDED**、「value が packet と違う」→ **VALUE_MISMATCH**、`resolvePacketPath` が `ok:false` → **POINTER_NOT_FOUND**(理由は `resolvePacketPath` の 5 種を登録: `grammar`・`no_row`・`no_field`・`index_out_of_range`・`missing_key`)、packetRef を持たない観測 → **UNVERIFIABLE**(理由 `no_packet_ref(H-9 out of scope)`) | H-9 の「skip(packet 無し)」に Core の相当物は無い(Core は必ず決める)。C-2 は packet を必ず渡すので出ない。**数え直し**は再現しない(§7) |

束縛(path → 値)は **Adapter が Recipe を組む時点で解く**(XBRL の `no_element` と同じ型): 解けなければ `Recipe.not_found_reason` を立て、Core の resolver は呼ばれない。解けたときだけ resolver(`make_resolver(packet)`)が `Resolved(value=数なら float / 文字列なら None, meta={"raw": 値})` を返す。

## 3. 入力の構造(測った数。予測ではない)

2026-10-06 に司令塔が **packet に当てずに**(解かずに)数えた。席の封筒 5 本(`seat_gpt.json`・`seat_claude.json`。`*_attempt_*_raw.json` は Golden の対象外なので数えない)。

| 数えたもの | 数 |
|---|---|
| 席の run / 封筒 / 統合 | 7 / 5 / 4 |
| items(仮説の行) | 58 |
| `observations[]` で `packetRef.path` を持つもの(= H-9 の対象。Golden の「参照 N 件」の合計と一致) | **213** |
| ↑ のうち `aggregates.` / `facts.` | 176 / 37 |
| ↑ `facts.` の列の内訳 | recognition 24・time 9・games 4 |
| ↑ 値が数 / 文字列 | 190 / 23 |
| 参照された集計の path(distinct) | 31 |
| `counterEvidence.items[].observations[]`(反証の観測) | 108(aggregates 77・facts 30・`provenance.inputs[4].path` 1。**packetRef は 0 件** ― `path` 欄だけ。H-9 は集めない) |
| Golden の H-2(文法)の NG | 1(反証の `provenance.inputs[4].path`。H-9 の対象ではない)。**213 件は全部文法を通っている** |
| 統合の封筒 4 本の観測で packetRef を持つもの | 0 |

## 4. 予測(封じる。外れうる粒度で)

### 4.1 Core と分類(計器 4)

| # | 予測 | 外れたら |
|---|---|---|
| P-1 | **Core 4 本の diff は 0 バイト**(`f917f02` のまま) | C-2 を止めて HUMAN |
| P-2 | 登録追加 = **8**(scheme `packet` 1・比較子 `canonical_json_equals` 1・理由 6 = POINTER_NOT_FOUND 5 + UNVERIFIABLE 1)。normalization 0。`builtin`・`equals` は `Registry.default()` の既存で足さない | 数が違えば結果文書に内訳 |
| P-3 | インターフェース拡張 **0**、意味変更 **0** | 1 つでも出たら記録して人間の判断(C-0 §3 のまま) |
| P-4 | Core に入る将棋固有の文字列(`packet`・`aggregates`・`facts`・`gameId`・`hypothesis`)は **0 件**(grep) | 同上 |
| P-5 | **Claim.value の型(float)に文字列が入らない問題が出る**: 23 件は `value=None` + `params["expected"]` で**Core を変えずに通る**が、`Result.recomputed` が None になり「何と比べたか」が detail にしか残らない。これを**インターフェース拡張の候補 1 件**として結果文書に書く(入れるかは人間) | 候補が 0 なら予測の外れ(= 私が過大に見ている) |

### 4.2 Claim と Result の数(計器 6 = C-2 の本体)

| # | 予測 | 根拠 |
|---|---|---|
| P-6 | Claim の総数 = **321**(packetRef あり 213 + 反証の観測 108 を UNVERIFIABLE で立てる) | §3 |
| P-7 | form: AGGREGATE 176 + 77 = **253**、DIRECT_VALUE 37 + 30 = **67**、`provenance.inputs[4].path` の 1 件は文法外なので form は DIRECT_VALUE で UNVERIFIABLE(packetRef 無し)= 67 に含む → 253 + 68 = 321 | §3。**ここは数え方で割れる**(文法外の 1 件をどちらに入れるか)。割れたら外れ |
| P-8 | 213 件の state: **GROUNDED 200〜213・VALUE_MISMATCH 0〜8・POINTER_NOT_FOUND 0〜5**。POINTER_NOT_FOUND の理由に `grammar` は **0**(213 件が H-2 を通っているから)。出るなら `no_field`(`.value` と `.numerator/.denominator` の取り違え)か `index_out_of_range`(recognition.rows の添字) | 席は render された seat_input から値を写しているので大半は一致する。文字列 23 件は、席が単位や語尾を変えていれば VM |
| P-9 | **TS の H-9(packet つき)と Core の state の対応が 213/213 で一致**(ok ↔ GROUNDED、value 違い ↔ VM、resolve 失敗 ↔ PNF)。**1 件でも違えば、それは Adapter の写しの誤りか、canonical JSON の 2 言語差**(C-1 の「2 言語で規則が違う」の型)。どちらかを結果に書く | §2 の対応表 |
| P-10 | TS の H-9 の**数え直し**(`recountRowProblems`)の problems は 31 行とも **0**(Golden の G-2 で packet の recountProblems 0 を封じている) | 0 でなければ P-9 の一致が崩れる(Core 側は数え直さない) |
| P-11 | 修飾 3 つは **321 件とも空**。= Core の modifiers は XBRL の形で、将棋の観測には要らない。これは Core の欠陥ではなく「将棋の観測は場所 1 つを指す」ことの記録 | 1 件でも埋まれば、Adapter が勝手に意味を足している |
| P-12 | GROUNDED の手検査 10 件(seed 20261006): **証拠の層の false pass 0**(値が packet のその場所に在る)。ただし **値の層は H-9 も Core も見ていない**(その数が文の主張に合う数かは誰も確かめない)。これは限界で、C-2 では直さない | 1 件でも出たら Adapter の写しの誤り |

### 4.3 試験・変異・大きさ

| # | 予測 |
|---|---|
| P-13 | Adapter(`adapters/shogi/`)**250〜450 行**、試験 **+20〜35 本**、変異 **+4〜6 本**(両向き: 比較子を `==` に替える・文法の正規表現を緩める・理由の登録を 1 つ外す・resolver を 1 段浅くする)が全部赤 |
| P-14 | 門: 既存 219(C-1g の後の数を結果文書に書き直す)+ C-2 の本数。c5 の Golden Master **rc=0 のまま**(将棋側 0 行なので自明。それでも凍結時に 1 回回す) |
| P-15 | 1 回目の計測で予測と違う項目: **P-6〜P-12 のうち 1〜2 個** |

## 5. 計器(GO / NO-GO)

| # | 計器 | 合格 | 備考 |
|---|---|---|---|
| 1 | 関数レベル Golden | ― | **この段では測らない**(将棋側 0 行)。結果文書に「未測」と書く |
| 2 | c5 Golden Master | rc=0 | 凍結時に司令塔が 1 回 |
| 4 | Core 変更の分類 | 登録追加 8・拡張 0・意味変更 0(P-2〜P-5) | |
| **6** | **TS H-9 ↔ Core の観測 1 件ごとの一致** | **213/213**(P-9)。差は全件を表に | 新設。TS の参照は `fixtures/shogi/h9_reference.ts`(`validateHypothesisLine(line, {today, registry, packet})` を呼ぶだけ。将棋の lib を読むが書かない)。Core の側は `fixtures/shogi/run_core_path_shogi.py` |
| 7 | 手検査 | GROUNDED 10 件で証拠の層 false pass 0(P-12) | |

## 6. 手順(3 役。C-1g と同じ)

1. この文書を封(コミット)。**コードは書かない。**
2. C-1g のコミットの後、実装担当に §2 の対応表どおりに書かせる: `audit-core/adapters/shogi/{packet_ref,resolve,recipes,comparators,registry_setup}.py`、`audit-core/tests/adapters/shogi/`、`audit-core/fixtures/shogi/{run_core_path_shogi.py,h9_reference.ts}`。Core・XBRL Adapter・将棋側(`scripts/playtest/`・`apps/`・`data/`)・fixtures の期待値・文書は触らない。コミットしない。
3. 司令塔が凍結(sha の一覧)し、**凍結時点で 1 回だけ**回す: (a) `h9_reference.ts` → `fixtures/shogi/c2_first_run_h9_reference.json`(観測ごとに `ok`・messages の種別だけ。文は保存しない)、(b) `run_core_path_shogi.py` → `fixtures/shogi/c2_first_run_core.json`(§2 の Claim 欄 + state・reason・pointers。**`statement` は書かない**。入力の sha = Golden の identity の値を写す)、(c) Golden Master、(d) 門。
4. (a) と (b) を観測 1 件ごとに照合(`c2_compare.py`、scratchpad)。§4 と突き合わせ、当たり外れを数える。
5. 独立監査 → GO でコミット(パス指定)→ 結果文書 `CORE_CONNECTION_C2_RESULT_2026-10-06.md`。
6. 結果を人間が読み、**C-1 計画 §7 の決定 3**(将棋の門を Core 経由に置き換えるか・言語)と **repo の切り出し**(C-0 §6)を決める。

## 7. Core に入れない物と、この段の限界(先に書く)

- **数え直し(`recountRowProblems`)は再現しない。** 集計行を母集団のとおりに数え直すには `facts` の列名・`gameId`・`games` 単位の意味(境界監査 I-4、未着手)が要る。Python に写すと同じ規則が 2 言語に 2 本できる(C-1 の「2 言語で規則が違う」の再来)。C-2 では TS の数え直しの problems が 0 であること(P-10)を前提に、照合の対象から外す。**0 でなければ、その観測は TS が fail・Core が GROUNDED で割れる**(外れとして記録)。
- **文字列の値**(23 件)は `Claim.value` に入らない。`params["expected"]` で通すが、`recomputed` が None になる。拡張するかは人間(P-5)。
- **H-9 の「skip」**(packet が無いとき緑にしない印)に Core の相当物は無い。Core は 4 状態で必ず決める。C-2 では packet を必ず渡すので問題にならないが、将棋の門を置き換えるときは「packet が無い = 回さない」を呼ぶ側で守る必要がある(記録)。
- **GROUNDED は「値が packet のその場所に在る」までで、その数が文の主張に合う数かは見ない。** 席が render された seat_input から値を写しているので、ほぼ全部が一致するのは当然で、**213/213 の GROUNDED は Core の手柄ではない**。C-2 が測るのは「Core の 4 層が将棋の検証器の判定を同じ粒度で言えるか」であって、将棋の冊子の正しさではない。
- 反証の観測 108 件は `path` だけで `packetRef` が無く、TS の H-9 は見ていない。C-2 は UNVERIFIABLE(理由 `no_packet_ref`)で立てるが、これは**将棋側の仕様の記録であって判定ではない**。反証の観測も照合すべきかは将棋側の判断(C-2 では触らない)。
- 統合の封筒(4 本)の観測は packetRef を持たないので Claim にしない。

## 8. 人間に決めてもらうこと(封の後、実装の前)

1. **範囲**: §1 のとおり「H-9 の判定を Core 経由で再現する(並走)」でよいか。将棋の門の置き換えは C-2 の結果を見てから(C-1 計画 §7 の決定 3)。
2. **TS の参照の道具の置き場所**: `audit-core/fixtures/shogi/h9_reference.ts`(将棋の lib を import する TS が audit-core の中に 1 本できる。repo を切り出すときは将棋側に残す)でよいか。嫌なら `scripts/playtest/` に置くが、それは将棋側に 1 ファイル足すことになる。
3. **1 回目の出力に値を書くか**: `c2_first_run_core.json` は観測の `value`(数・群の名前・形の名前の文字列)を含む。文(statement)は含まない。顧客の対局の数そのものなので、**sha と state だけにするか、値も書くか**。この文書の既定は「値も書く」(ID 単位の照合に要る)。
4. 反証の観測 108 件を Claim に数えるか(P-6 は数える前提。数えないなら 213)。

## 9. この文書がしないこと

- Core のコードを変える提案。将棋側のコードを変える提案。Adapter のコードを書くこと。
- C-1g の予測・結果に触ること。
- repo の切り出しの名前・公開の可否(C-0 §6 のまま人間)。
