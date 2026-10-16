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
| `tests/measure` | 43 | 1,022 | `tests` は package なのに `tests/measure` に `__init__.py` が無い。**unittest の探索は package でない下位ディレクトリを飛ばす** |
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

### §2-1 ディスク上の試験 file: **101 本**(**いまの数**。門を足すと増える)

| ディレクトリ | file |
|---|---|
| `tests/measure` | 45 |
| `tests/adapters/xbrl` | 23 |
| `tests/adapters/kokkai` | 11 |
| `tests/adapters/shogi` | 8 |
| `tests/core` | 5 |
| `tests/fixtures/xbrl` | 4 |
| `tests/golden` | 4 |
| `measure/tests` | 1 |

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

## §3-2 共有ツリーに入れた後の実測

| 走らせ方 | 本数 | 収集する file |
|---|---|---|
| `pytest -q`(path 指定なし) | **2,260** | **101 / 101** |
| `unittest discover`(ルートから) | **2,164** | **100 / 101** |

**残る 1 本は `measure/tests/test_inject.py`(96 本)で、`pytest` でしか走らない。**
`measure/__init__.py` を足せば discover にも入るが、**それは案 B で崩れる**(§3)。

### §3-3 **共有ツリーでの初回の完走は落ちた ― 検証が自分の記録を書き換えていた**

この整備を commit したあと `run_tests.sh` を共有ツリーで通したら、**落ちた**。

```
1 failed, 2215 passed, 1 skipped in 1204.69s (0:20:04)
FAILED tests/measure/test_suite_coverage.py::DocTest::test_27_counts_match_the_record
```

**原因は私の設計である。**1 段目の覆いの検査が記録 file を**書き換え**、
その新しい数(2,217 / 2,121)が文書の数(2,215 / 2,119)と合わなくなり、
2 段目の `pytest` が赤くなった。`set -e` なので 3 段目は走っていない。

**つまり「標準の検証を走らせた事自体で、緑の木が赤くなる」。**
記録の数が古かったのも事実である ― commit した記録は門を 2 本足す前に作ったもので、
**file 数(100/100)を見る門は通り、本数のずれは誰も見ていなかった。**

**直した。**覆いの検査は**既定では記録を読むだけ**にし、
**食い違いが在れば落ちる**(`--write` を付けたときだけ更新する)。
門 `RecordIsStableAndReadOnlyTest`(37〜39)で、
**既定の実行が記録を書き換えないこと**・**記録を 1 か所壊すと落ちること**・
**`run_tests.sh` が `--write` を渡さないこと**を固定した。
あわせて `_by_dir` が鍵を並べて返すようにした(鍵の順が実行ごとに変わり、
**中身が同じでも git の差分が出ていた**)。

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
3. **`tests/measure/test_suite_coverage.py`** ― **39 本**の門。
   記録と突き合わせるだけでなく、**その場で測り直して漏れ 0 を要求する**
   (`LiveCoverageTest`)。記録を更新し忘れても漏れを見逃さない。
   判定は `judge()` に切り出し、**壊した入力を食わせて赤になることを確かめた。**

**試験 file を 1 本足すと覆いの記録が古くなって門が赤くなる ― それが狙いである。**

---

## §5 言えないこと

- **「収集された」と「緑だった」は別である。**§3-2 の 2,260 / 2,164 は**収集の数**である。
  共有ツリーでの完走は §6 に書く。
- **1 つのコマンドで全部走るわけではない。**`run_tests.sh` が 2 つの runner を順に走らせる。
- **`unittest discover` は案 A を入れても 99 / 100 file である。**
  残る 1 本は `pytest` でしか走らない。
- この整備は**試験の数を増やしていない。**漏れを検出できるようにしただけである。
