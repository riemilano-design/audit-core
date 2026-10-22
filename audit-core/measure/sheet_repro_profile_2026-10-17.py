# -*- coding: utf-8 -*-
"""令和５年度のプロファイル(封 docs/DOMAIN1_REPRO_SEAL_2026-10-17.md §2)。

**差し替えるのは「どの年度の file を読むか」の 1 か所だけ。**
規則・閾値・語彙・表層形の表・採点器は 1 文字も変えない。

**凍結した module を汚さない** ― 差し替えたら必ず戻す
(段 11 で `M9.PREV` を戻したのと同じ型)。

  usage: import して `with year5(): ...`
"""
import contextlib
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
TOC_OUT = os.path.join(FX, "repro_toc_2026-10-17.json")
SEAL = "docs/DOMAIN1_REPRO_SEAL_2026-10-17.md"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


F = _mod("fetch5_for_profile", "sheet_repro_fetch_2026-10-17.py")
SE = _mod("se_for_profile", "sheet_sainyuu_engine_2026-10-16.py")
M2 = SE.M2
P2 = SE.P2
P1M = P2.P1M


def build_toc():
    """**令和５年度の明細 歳入の目次を、凍結した規則で作り直す。**(費用 0)

    `SE` は目次を記録(令和６年度の P-1)から読む。**年度をまたいで使えない**ので、
    **同じ関数**で作り直して別の記録に置く。
    """
    if os.path.exists(TOC_OUT):
        return json.load(io.open(TOC_OUT, encoding="utf-8"))
    old = P1M.MEISAI_SAINYUU
    P1M.MEISAI_SAINYUU = F.MEISAI_SAINYUU
    try:
        sheets, _ = P1M.read(P1M.MEISAI_SAINYUU)
        got = P1M.meisai_sainyuu(sheets)
    finally:
        P1M.MEISAI_SAINYUU = old
    rec = {"seal": SEAL,
           "source": F.MEISAI_SAINYUU,
           "rule": ("**`sheet_sainyuu_p1_2026-10-16.py` の `meisai_sainyuu()` を"
                    "そのまま呼んだ。規則は変えていない**"),
           "toc_entries": got["toc_entries"],
           "meisai_sainyuu": {"toc": got["toc"]}}
    json.dump(rec, io.open(TOC_OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return rec


@contextlib.contextmanager
def year5(*m2s):
    """**令和５年度の file を読むようにする。**終わったら必ず戻す。

    **`_mod()` は呼ぶたびに別の module 実体を作る。**だから
    **これから使う module が持っている `M2` の実体を全部渡さなければ効かない。**
    2026-10-17 にこれで一度失敗した(抜粋が令和６年度のまま出て、
    門 `test_11` が「指示文が段 11 と byte 一致」で捕まえた)。
    **既定は `SE.M2` だけ。使う側が自分の実体を渡す。**
    """
    build_toc()
    targets = list(m2s) + [M2]
    saved = [(m, m.SOUKATU, m.KESSAN, m.MEISAI) for m in targets]
    saved_rest = (P1M.SAINYUU, P1M.MEISAI_SAINYUU, SE.P1REC, dict(SE._CACHE))
    for m in targets:
        m.SOUKATU, m.KESSAN, m.MEISAI = F.SOUKATU, F.KESSAN, F.MEISAI
    P1M.SAINYUU, P1M.MEISAI_SAINYUU = F.SAINYUU, F.MEISAI_SAINYUU
    SE.P1REC = TOC_OUT
    SE._CACHE.clear()
    try:
        yield
    finally:
        for m, s, k, ms in saved:
            m.SOUKATU, m.KESSAN, m.MEISAI = s, k, ms
        (P1M.SAINYUU, P1M.MEISAI_SAINYUU, SE.P1REC, cache) = saved_rest
        SE._CACHE.clear()
        SE._CACHE.update(cache)


def is_year5(*m2s):
    """いま令和５年度を見ているか(門が確かめる)。**渡した実体も全部見る。**"""
    return all(m.KESSAN == F.KESSAN and m.MEISAI == F.MEISAI
               and m.SOUKATU == F.SOUKATU
               for m in (list(m2s) + [M2]))


if __name__ == "__main__":
    print("既定(令和６年度): %s" % M2.KESSAN)
    with year5():
        print("プロファイルの中: %s / is_year5=%s" % (M2.KESSAN, is_year5()))
        t = build_toc()
        print("目次 %d 件: %s" % (t["toc_entries"],
                               json.dumps(t["meisai_sainyuu"]["toc"][:3],
                                          ensure_ascii=False)))
    print("戻した: %s / is_year5=%s" % (M2.KESSAN, is_year5()))
