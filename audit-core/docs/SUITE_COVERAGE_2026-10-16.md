# 試験の走らせ方の統一 ― **「全体 1,065 OK」は全体ではなかった**

2026-10-16。人間の指示(優先順位 ③ → ① → ②)の ③。

> 重要なのはコマンドの数ではなく、**新しい門を追加したのに標準の検証から漏れる事故**を
> 防ぐことです。
> `tests/measure/__init__.py` を置けば解決すると決めつけず、**実測してから変更します。**

---

## §1 私の誤り

段 6〜段 9 の報告で私は「全体 `unittest discover` 1,065 OK」と書いた。
**これは全体ではなかった。**

| 漏れていた場所 | file | 本数 | なぜ |
|---|---|---|---|
| `tests/measure` | 50 | 1,022 | `tests` は package なのに `tests/measure` に `__init__.py` が無い。**unittest の探索は package でない下位ディレクトリを飛ばす** |
| `measure/tests` | 1 | 96 | `measure/` が package でないので**丸ごと飛ぶ** |

`tests/measure` は `-s tests/measure` で毎回別に走らせていたので**測り落としは無かった**。
しかし **`measure/tests/test_inject.py` の 96 本は、私の 2 つの標準手順の
どちらにも入っていなかった。**

**同じ誤りは 2026-10-14 に一度見つかって文書化されていた**
(`docs/CONSOLIDATION_P20_RESULT_2026-10-14.md` §5-2 の 2 番:
「報告していた pytest 1,039 / discover 1,030 → 実は 1,141 / 1,036。
`tests/` だけの数で `measure/tests/` の 96 本が入っていなかった」)。
**私はその記録を読まずに同じ型を繰り返した。**

---

## §2 測った事実 ― **変更前**(試験は走らせず、収集だけ数えた)

### §2-1 ディスク上の試験 file: **224 本**(**いまの数**。門を足すと増える)

| ディレクトリ | file |
|---|---|
| `measure/tests` | 1 |
| `tests/adapters/kokkai` | 11 |
| `tests/adapters/shogi` | 8 |
| `tests/adapters/xbrl` | 32 |
| `tests/core` | 5 |
| `tests/fixtures/xbrl` | 4 |
| `tests/golden` | 4 |
| `tests/measure` | 159 |

**2026-10-20 に +2**(`tests/measure/test_packaging.py`・`tests/measure/test_packaging_result.py`。
包装の封 `docs/PACKAGING_SEAL_2026-10-20.md` の G-5)。176 → 178、`tests/measure` 118 → 120。

**2026-10-20 に +2**(`tests/measure/test_xbrl_generality_seal.py`・`tests/measure/test_xbrl_generality_result.py`。
汎化 C の封 `docs/XBRL_GENERALITY_SEAL_2026-10-20.md` の G-14)。封の門で 180 → 181(`tests/measure` 122 → 123)、結果の門で 181 → 182(123 → 124)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_generality_c1_result.py`。
汎化 C の封 追記 1 `docs/XBRL_GENERALITY_SEAL_2026-10-20.md` の K-12)。C1 の結果の門で 182 → 183(`tests/measure` 124 → 125)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_generality_p20_result.py`。
汎化 C の封 追記 2 `docs/XBRL_GENERALITY_SEAL_2026-10-20.md` の R-11)。P20 の結果の門で 183 → 184(`tests/measure` 125 → 126)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_generality_alpha_result.py`。
汎化 C の封 追記 3 `docs/XBRL_GENERALITY_SEAL_2026-10-20.md` の S-9)。α の結果の門で 184 → 185(`tests/measure` 126 → 127)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_naming_fix_seal.py`。
名指しの直しの封 `docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md` の N-11)。封の門で 185 → 186(`tests/measure` 127 → 128)。

**2026-10-20 に +2**(`tests/adapters/xbrl/test_recipes_p21.py`・`tests/measure/test_xbrl_naming_fix_result.py`。
名指しの直しの封 `docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md` の段 1)。実装の試験で 186 → 187(`tests/adapters/xbrl` 25 → 26)、結果の門で 187 → 188(`tests/measure` 128 → 129)。

**2026-10-20 に +1**(`tests/measure/test_facts_for_buyers.py`。
「測った事実」1 冊 `docs/FACTS_FOR_BUYERS_2026-10-20.md` の門)。188 → 189(`tests/measure` 129 → 130)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_hybrid_trust_seal.py`。
席と Core の一致の信頼(3 群)の封 `docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md` の門)。189 → 190(`tests/measure` 130 → 131)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_hybrid_trust_result.py`。
席と Core の一致の信頼(3 群)の封 `docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md` の段 1)。段 1 の結果の門で 190 → 191(`tests/measure` 131 → 132)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_hybrid_s2_material.py`。
席と Core の一致の信頼(3 群)の封 `docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md` の段 2 の前半 = 下見と材料)。191 → 192(`tests/measure` 132 → 133)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_hybrid_s2_result.py`。
席と Core の一致の信頼(3 群)の封 `docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md` の段 2 の採点)。192 → 193(`tests/measure` 133 → 134)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_ritual_seal.py`。
10 分の再現の儀式の封 `docs/XBRL_RITUAL_SEAL_2026-10-20.md` の封の門)。193 → 194(`tests/measure` 134 → 135)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_ritual_result.py`。
10 分の再現の儀式の結果と README の節を記録に縛る門)。194 → 195(`tests/measure` 135 → 136)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_point_prior_seal.py`。
穴 2 つ(単位語「ポイント」/ 前期の値を通す)の広さを測る封 `docs/XBRL_POINT_PRIOR_SEAL_2026-10-20.md` の封の門)。195 → 196(`tests/measure` 136 → 137)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_point_prior_result.py`。
穴 2 つの広さの結果(記録 `fixtures/xbrl/point_prior_2026-10-20.json`・文書 `docs/XBRL_POINT_PRIOR_RESULT_2026-10-20.md`)を縛る門)。196 → 197(`tests/measure` 137 → 138)。

**2026-10-20 に +1**(`tests/measure/test_xbrl_period_bind_seal.py`。
期間を縛る直し(P22)の封 `docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md` の封の門)。197 → 198(`tests/measure` 138 → 139)。

**2026-10-20 に +2**(`tests/adapters/xbrl/test_recipes_p22.py`・`tests/measure/test_xbrl_period_bind_result.py`。
期を縛る直し(P22)の段 1 の engine の試験 27 本と、結果(記録 `fixtures/xbrl/period_bind_2026-10-20.json`・文書 `docs/XBRL_PERIOD_BIND_RESULT_2026-10-20.md`)を縛る門)。198 → 200(`tests/adapters/xbrl` 26 → 27・`tests/measure` 139 → 140)。

**2026-10-21 に +1**(`tests/measure/test_xbrl_rounding_seal.py`。
丸めの帯を直す(P23)の封 `docs/XBRL_ROUNDING_SEAL_2026-10-21.md` の封の門)。200 → 201(`tests/measure` 140 → 141)。

**2026-10-21 に +2**(`tests/adapters/xbrl/test_recipes_p23.py`・`tests/measure/test_xbrl_rounding_result.py`。
丸めの帯を直す(P23)の段 1 の engine の試験 29 本と、結果(記録 `fixtures/xbrl/rounding_2026-10-21.json`・文書 `docs/XBRL_ROUNDING_RESULT_2026-10-21.md`)を縛る門)。201 → 203(`tests/adapters/xbrl` 27 → 28・`tests/measure` 141 → 142)。

**2026-10-21 に +1**(`tests/measure/test_xbrl_vocab_seal.py`。
語彙の登録と枠の取り直しの直し(P24)の封 `docs/XBRL_VOCAB_SEAL_2026-10-21.md` の封の門)。203 → 204(`tests/measure` 142 → 143)。

**2026-10-21 に +2**(`tests/adapters/xbrl/test_recipes_p24.py`・`tests/measure/test_xbrl_vocab_result.py`。
語彙の登録と枠の取り直しの直し(P24)の段 1 の engine の試験 68 本と、結果(記録 `fixtures/xbrl/vocab_2026-10-21.json`・文書 `docs/XBRL_VOCAB_RESULT_2026-10-21.md`)を縛る門)。204 → 206(`tests/adapters/xbrl` 28 → 29・`tests/measure` 143 → 144)。

**2026-10-21 に +1**(`tests/measure/test_xbrl_lastbranch_seal.py`。
最後の枝の名指しは証拠があるときだけ「違う」と言う直し(P25)の封 `docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md` の封の門)。206 → 207(`tests/measure` 144 → 145)。

**2026-10-21 に +2**(`tests/adapters/xbrl/test_recipes_p25.py`・`tests/measure/test_xbrl_lastbranch_result.py`。
最後の枝の名指しは証拠があるときだけ「違う」と言う直し(P25)の段 1 の engine の試験 63 本と、結果(記録 `fixtures/xbrl/lastbranch_2026-10-21.json`・文書 `docs/XBRL_LASTBRANCH_RESULT_2026-10-21.md`)を縛る門)。207 → 209(`tests/adapters/xbrl` 29 → 30・`tests/measure` 145 → 146)。

**2026-10-21 に +1**(`tests/measure/test_xbrl_customer_report_seal.py`。
顧客向けの報告形(新しい module `adapters/xbrl/report_customer.py`)の封 `docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md` の封の門)。209 → 210(`tests/measure` 146 → 147)。

**2026-10-21 に +2**(`tests/adapters/xbrl/test_report_customer.py`・`tests/measure/test_xbrl_customer_report_result.py`。
顧客向けの報告形(新しい module `adapters/xbrl/report_customer.py`)の module の試験と、結果(記録 `fixtures/xbrl/customer_report_2026-10-21.json`・文書 `docs/XBRL_CUSTOMER_REPORT_RESULT_2026-10-21.md`)を縛る門)。210 → 212(`tests/adapters/xbrl` 30 → 31・`tests/measure` 147 → 148)。

**2026-10-21 に +1**(`tests/measure/test_xbrl_fresh_seal.py`。
新しい標本 30 書類で P22・P24・P25 を並べ既定を決める封 `docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md` の封の門)。212 → 213(`tests/measure` 148 → 149)。

**2026-10-21 に +1**(`tests/measure/test_xbrl_customer_report_fix_seal.py`。
顧客向けの報告形の直し(単位・英字・但し書き・指紋・表題・桁)の封 `docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md` の封の門)。213 → 214(`tests/measure` 149 → 150)。

**2026-10-21 に +1**(`tests/measure/test_xbrl_customer_report_fix_result.py`。
顧客向けの報告形の直しの結果(記録 `fixtures/xbrl/customer_report_fix_2026-10-21.json`・文書 `docs/XBRL_CUSTOMER_REPORT_FIX_RESULT_2026-10-21.md`)を縛る門)。214 → 215(`tests/measure` 150 → 151)。

**2026-10-22 に +1**(`tests/measure/test_xbrl_p26_seal.py`。
「違う」に出る正しい文の主因を減らす engine の直し P26 の封 `docs/XBRL_P26_SEAL_2026-10-21.md` の封の門)。215 → 216(`tests/measure` 151 → 152)。

**2026-10-22 に +2**(`tests/adapters/xbrl/test_recipes_p26.py`・`tests/measure/test_xbrl_p26_result.py`。
「違う」に出る正しい文の主因を減らす engine の直し P26 の段 1 の engine の試験と、結果(記録 `fixtures/xbrl/p26_2026-10-21.json`・文書 `docs/XBRL_P26_RESULT_2026-10-21.md`)を縛る門)。216 → 218(`tests/adapters/xbrl` 31 → 32・`tests/measure` 152 → 153)。

**2026-10-22 に +1**(`tests/measure/test_xbrl_fresh_fetch.py`。
新しい標本 40 件の取得 script `measure/xbrl_fresh_fetch_2026-10-21.py`(封 `docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md` §1-3・§1-4)の試験。通信を差し替え、鍵は偽の字)。218 → 219(`tests/measure` 153 → 154)。

**2026-10-23 に +1**(`tests/measure/test_xbrl_fresh_result.py`。
新しい標本 30 書類で P22・P23・P24・P25・P26 を並べ既定を決めた結果(記録 `fixtures/xbrl/fresh/fresh_2026-10-21.json`・文書 `docs/XBRL_FRESH_SAMPLE_RESULT_2026-10-21.md`)を縛る門)。219 → 220(`tests/measure` 154 → 155)。

**2026-10-23 に +1**(`tests/measure/test_xbrl_default_p26_seal.py`。
既定の profile を P22 から P26 に切り替える(段 2)の封 `docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md` の封の門)。220 → 221(`tests/measure` 155 → 156)。

**2026-10-23 に +1**(`tests/measure/test_xbrl_default_p26_result.py`。
既定の profile を P22 から P26 に切り替えた(段 2)結果(記録 `fixtures/xbrl/default_p26_2026-10-23.json`・文書 `docs/XBRL_DEFAULT_P26_RESULT_2026-10-23.md`)を縛る門)。221 → 222(`tests/measure` 156 → 157)。

**2026-10-27 に +2**(`tests/measure/test_xbrl_p27_sample_seal.py`・`tests/measure/test_xbrl_p27_dbfetch.py`。
P27 段 1 の封 `docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md` の封の門と、外部の DB の応答の取得 script `measure/xbrl_p27_dbfetch_2026-10-27.py` の試験)。222 → 224(`tests/measure` 157 → 159)。

**この節だけは「いま」の数である**(門 `DocTest` が記録と突き合わせる)。
下の §2-2 は**変更前の実測**で、後の記録と結び付けない。

### §2-2 コマンドごとの収集(**この節は変更前の実測で、後の記録と結び付けない**)

| 走らせ方 | 本数 | モジュール | 読み込み失敗 | 覆う file |
|---|---|---|---|---|
| `pytest -q`(path 指定なし) | **2,214** | ― | 0 | **100 / 100** |
| `unittest discover`(ルートから) | 1,065 | 55 | 0 | 55 / 100 |
| `unittest discover -s tests -t .` | 1,065 | 55 | 0 | 55 / 100 |
| **`unittest discover -s tests`(`-t` 無し)** | **219** | 14 | **42** | ― |
| `unittest discover -s tests/measure` | 1,053 | 44 | 0 | 44 / 100 |

**既知の影は健在である。**`-s tests` に `-t .` を付けないと、
`tests/adapters/xbrl` が実体の `adapters.xbrl` を隠して **42 件の読み込み失敗**になる。
`-t .` を付ければ 0 件に戻る。

**2 つの unittest の集合は互いに素**(重なり 0 モジュール)で、合わせても
`measure/tests/test_inject.py`(96 本)は入らない。**全部を覆うのは `pytest` だけ**である。

---

## §3 統合案を隔離して試した(worktree。共有ツリーを触らずに)

### 案 A `tests/measure/__init__.py` を足す → **採用**

| | 前 | 後 |
|---|---|---|
| `discover`(ルートから) | 1,065 本 / 55 モジュール | **2,087 本 / 98 モジュール** |
| 読み込み失敗 | 0 | **0** |

### 案 B `measure/__init__.py` も足す → **却下**

| | 後 |
|---|---|
| `discover`(ルートから) | **101 本 / 2 モジュール** |
| 読み込み失敗 | **5 件**(`tests.adapters` / `tests.core` / `tests.fixtures` / `tests.golden` / `tests.measure`) |

**理由は測って特定した。**`measure/` が package になると、探索は
`measure.tests.test_inject` を `tests.*` より先に読み込む。その **39 行目の
`sys.path.insert(0, MEASURE)`** が `sys.path` の先頭に `measure/` を入れるので、
以後の **`import tests` が `measure/tests/` に解決される**。
本物の `tests.core` などが `ModuleNotFoundError` になる。
**影の問題と同じ型である。だから `measure/__init__.py` は足さない。**

### §3-1 **一度測り間違えた(自分の後片付け漏れ)**

案 B を試したあと `measure/__init__.py` だけを消し、**`measure/tests/__init__.py` を
消し忘れた**まま案 A の確認に進んだ。その状態で `pytest` を走らせたら
**98 件の収集エラー**(`ModuleNotFoundError: No module named 'tests.adapters'`)が出た。

原因は案 A ではない。`measure/tests` が package のままだったので、
`measure/tests/test_inject.py:39` の `sys.path.insert(0, MEASURE)` のあと
**`import tests` が `measure/tests/` に解決された**。案 B の残骸である。

消して測り直したら、**案 A 単独では両方とも健全**だった。

| 案 A 単独(worktree で確かめた) | 実測 |
|---|---|
| `pytest --collect-only` | **2,183 本・エラー 0** |
| **`pytest -q` の完走** | **2,182 passed / 1 skipped**(rc=0・21 分 00 秒) |
| `unittest discover`(ルートから)の収集 | **2,087 本 / 98 モジュール** |
| **`unittest discover` の完走** | **2,087 OK**(skip 1・20 分 56 秒) |

記憶 `injected-errors-contaminate-each-other`(**1 回の検証で 1 件だけ変える**)の型を
踏んだ。**却下した案の残骸が次の測定を汚した。**

---

## §3-2 共有ツリーに入れた後の覆い

| 走らせ方 | 覆い |
|---|---|
| `pytest -q`(path 指定なし) | **全部**(漏れ 0 本) |
| `unittest discover`(ルートから) | **1 本だけ漏れる**(`measure/tests/test_inject.py`) |

**本数はこの文書に書かない。**正本は `fixtures/suite_coverage_2026-10-16.json` で、
**覆いの検査が記録と現実の食い違いで落ちる**(`--write` で更新する)。
**文に書いた数は古くなる** ― 2026-10-16 に実際それで共有ツリーの完走が落ちた(§3-3)。

**残る 1 本は `measure/tests/test_inject.py`(96 本)で、`pytest` でしか走らない。**
`measure/__init__.py` を足せば discover にも入るが、**それは案 B で崩れる**(§3)。


---

## §4 採った方式

**1 コマンドにはしない。**`pytest` が全部を覆うが、
**「漏れていないこと」自体を機械で確かめる**層を足した。

1. **`measure/suite_coverage_2026-10-16.py`** ― **試験を走らせず**、
   ディスク上の `test_*.py` を数え上げ、各標準コマンドが収集するかを調べ、
   **どのコマンドにも収集されない file が在れば落ちる。**
   標準コマンドの字は**この file 1 か所**に書く(`COMMANDS`)。
2. **`run_tests.sh`** ― 覆いの検査 → `pytest`(全数)→ `unittest discover` の順に走らせ、
   1 つでも落ちたら全体を落とす。`COMMANDS` の字が runner に在ることを門で確かめる。
3. **`tests/measure/test_suite_coverage.py`** ― 門(**本数はここに書かない**)。
   記録と突き合わせるだけでなく、**その場で測り直して漏れ 0 を要求する**
   (`LiveCoverageTest`)。記録を更新し忘れても漏れを見逃さない。
   判定は `judge()` に切り出し、**壊した入力を食わせて赤になることを確かめた。**

**試験 file を 1 本足すと覆いの記録が古くなって門が赤くなる ― それが狙いである。**

---

## §5 言えないこと

- **「収集された」と「緑だった」は別である。**§3-2 は**覆い**の話で、
  完走したかは §6 の 1 本の run だけが示す。
- **1 つのコマンドで全部走るわけではない。**`run_tests.sh` が 2 つの runner を順に走らせる。
- **`unittest discover` は案 A を入れても全部は覆わない。**
  残る 1 本(`measure/tests/test_inject.py`)は `pytest` でしか走らない。
- この整備は**試験の数を増やしていない。**漏れを検出できるようにしただけである。

---

## §6 共有ツリーでの完走(**2026-10-16 の 1 本。これが唯一の証跡**)

commit `e9b2165` の木で `sh run_tests.sh` を 1 本通した。**rc=0。**

| 段 | 結果 | 所要 |
|---|---|---|
| 1/3 覆いの検査 | **漏れ 0 本**(どの試験 file も標準のコマンドに収集されている) | 約 1 分 |
| 2/3 `pytest -q`(全数) | **2,257 passed / 3 skipped** | **20 分 16 秒** |
| 3/3 `unittest discover` | **Ran 2,164 / OK (skipped=3)** | **20 分 18 秒** |
| 合計 | **全部通った(rc=0)** | **18:59:35 → 19:40:11(約 40 分 36 秒)** |

**この数は 1 本の run の記録であり、更新しない。**次に測ったら別の節に書く
(記憶 `evidence-file-must-be-the-completed-run`)。

**所要の大半は `tests/adapters/xbrl/test_mutations.py` である。**
変異 **89 件**がそれぞれ**隔離した一時の木**で `unittest discover -s tests -t .` を
走らせる(写すのは `tests/adapters/xbrl` と `tests/golden` だけで、
`tests/measure` は写さない)。**この整備で増えた負荷ではない。**

---

## §6-2 2 本目の完走(**2026-10-16・段 11 の門を足したあと**)

commit `a4fe2af` の木で `sh run_tests.sh` を 1 本通した。**rc=0。**
**§6 の数は書き換えていない**(1 本の run は 1 本の記録として残す)。

| 段 | 結果 | 所要 |
|---|---|---|
| 1/3 覆いの検査 | **漏れ 0 本** | 約 1 分 |
| 2/3 `pytest -q`(全数) | **2,479 passed / 3 skipped** | **20 分 58 秒** |
| 3/3 `unittest discover` | **Ran 2,386 / OK (skipped=3)** | **20 分 55 秒** |
| 合計 | **全部通った(rc=0)** | **約 42 分** |

段 11(本実験)の門 **86 本**を足した分だけ増えている
(2,257 → 2,479 passed。**赤は 0 本**)。
**所要の大半は変わらず `tests/adapters/xbrl/test_mutations.py` の 89 変異である。**
