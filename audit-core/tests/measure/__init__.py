# -*- coding: utf-8 -*-
"""`tests/measure` を package にする(人間の指示 2026-10-16 の ③)。

**これが無いと `audit-core/` からの `unittest discover` がこのディレクトリに降りない。**
`tests` は package なので、unittest の探索は**package でない下位ディレクトリを飛ばす**。
段 6〜段 9 で私が「全体 1,065 OK」と報告していたとき、**ここの 1,000 本以上は
その数に入っていなかった。**

実測(`docs/SUITE_COVERAGE_2026-10-16.md`):

  * これを置く前  `discover` 1,065 本 / 55 モジュール
  * これを置いた後 `discover` **2,087 本 / 98 モジュール**(読み込み失敗 0。完走 OK)
  * `pytest` は置く前 2,183 収集、置いた後も **2,182 passed / 1 skipped**(rc=0)

**`measure/__init__.py` は置かない。**置くと `measure/tests/test_inject.py` の
`sys.path.insert(0, MEASURE)` が `import tests` を `measure/tests/` に解決させ、
収集が 2,087 本から 101 本に崩れる(読み込み失敗 5 件)。
"""
