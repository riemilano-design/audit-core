# -*- coding: utf-8 -*-
"""抽選 341e079 のうち **A1 封に割り当てられた 2 件だけ**を取る。

**本線の truncate 封に割り当てられた 2 件は取らない** ―
取得は席ごとの承認が要る行為で、席の間で承認は渡せない
(本線の席が 2026-10-09 に明言。同意した)。この道具は
``seal`` が A1 封でない docID を**拒否する**。

鍵は環境変数 ``EDINET_API_KEY`` から読む。**値は印字も保存もしない。**
ZIP は ``~/.cache/audit-core/edinet/`` に置く(**リポジトリの外**)。
記録に残すのは docID・社名・バイト数・sha256・中身の印だけ。**中身は見ない。**
「取った」のか「すでに手元に在った」のかを**区別して印字し、記録にも残す**
(人間の指示、2026-10-09)。
"""

import json
import os
import sys
import urllib.request
import os as _os_gate
import sys as _sys_gate
_sys_gate.path.insert(0, _os_gate.path.dirname(_os_gate.path.abspath(__file__)))
from sealed_material import refuse_if_sealed  # noqa: E402  **取る直前に呼ぶ**

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from adapters.xbrl import edinet as E                      # noqa: E402
from fixtures.xbrl.zip_content_digest import content_digest  # noqa: E402

FETCHABLE_SEAL = "A1 封(① 差の許容幅)"

# ---------------------------------------------------------------------------
# **他の席が封じた材料。字で書いて拒否する。**
#
# 本線(司令塔)の依頼、2026-10-09。本線で「封じた時点で未取得」と書いた封が
# コミットの直前に測り直されておらず、実際には取得済みだった ― という事故が
# 起きた(本線が申告・追記 862ce7a)。原因は本線の手順だが、**再発条件は
# 「人が覚えていること」に頼っている限り消えない。**
#
# だから**人の記憶ではなく道具で閉じる。**この一覧の docID は、
# 抽選記録に何と書いてあっても、引数に何を渡しても**取らない。**
#
# 外すときは、**その封を持っている席からの依頼**と、外す理由を行に書くこと。
from sealed_material import SEALED_DOCS as OTHER_SEATS_SEALED  # 一覧は関門が持つ
# ---------------------------------------------------------------------------
API = "https://api.edinet-fsa.go.jp/api/v2/documents/%s?type=1&Subscription-Key=%s"


def main():
    key = os.environ.get("EDINET_API_KEY")
    if not key:
        print("環境変数 EDINET_API_KEY が無い。鍵の値はこの道具に書かない。")
        return 2
    rec = json.load(open(os.path.join(HERE, "new_draw_2026-10-09.json"), encoding="utf-8"))
    # **矛盾したときだけ止まる。**
    # 拒否の一覧に在る docID が「こちらの封の材料」と記録されていたら、
    # 割当と拒否が食い違っている = 記録が壊れている。
    # そのまま取ると「封じた材料を取ってしまう」側へ倒れるので、1 件も取らない。
    # (一覧に在るだけなら正常 ― こちらが引いて他の席に渡した材料がそうなる。)
    conflict = [r["docID"] for r in rec["picked"]
                if r["docID"] in OTHER_SEATS_SEALED and r.get("seal") == FETCHABLE_SEAL]
    if conflict:
        print("止まる: 割当と拒否の一覧が食い違っている -> %s" % ", ".join(conflict))
        print("  (記録の側を直してから回すこと。この道具は食い違ったまま取らない)")
        return 3
    out = []
    for row in rec["picked"]:
        doc, seal = row["docID"], row["seal"]
        if doc in OTHER_SEATS_SEALED:                      # 二重の錠(到達しない想定)
            print("  %-10s **取らない**(%s ― 席の間で承認は渡せない)"
                  % (doc, OTHER_SEATS_SEALED[doc]))
            continue
        if seal != FETCHABLE_SEAL:
            print("  %-10s **取らない**(%s ― 席の間で承認は渡せない)" % (doc, seal))
            continue
        path = E.cache_path(doc)
        had = os.path.exists(path)
        if not had:
            refuse_if_sealed(doc_id=doc, where="fetch_new_draw.main")   # **取る直前**
            with urllib.request.urlopen(API % (doc, key), timeout=120) as r:
                data = r.read()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "wb").write(data)
        import hashlib
        zb = open(path, "rb").read()
        digest, members = content_digest(zb)
        out.append({"docID": doc, "filerName": row.get("filerName"), "seal": seal,
                    "bytes": len(zb), "zip_sha256": hashlib.sha256(zb).hexdigest(),
                    "content_digest": [digest, members],
                    "how": "すでに手元に在った" if had else "取った"})
        print("  %-10s %-24s %8d bytes  zip=%s…  中身の印=%s…(目録 %d 本)  (%s)"
              % (doc, (row.get("filerName") or "")[:24], len(zb),
                 out[-1]["zip_sha256"][:12], digest[:12], members, out[-1]["how"]))
    # **既にある取得記録を上書きしない。**
    #
    # 2026-10-09 に実際に壊した: 動作を確かめるために回し直したら、
    # 「取った」で記録されていた 2 件が「すでに手元に在った」に**上書きされた**。
    # 2 つ目以降の実行は定義上いつでも「すでに手元に在った」なので、
    # **回し直すほど「取った」という事実が消えていく。**
    # 人間の指示(2026-10-09)は「取ったのか手元に在ったのかを記録上で区別する」
    # ― 上書きはその指示を静かに破る。だから**構造で閉じる。**
    p = os.path.join(HERE, "fetched_new_draw_2026-10-09.json")
    if os.path.exists(p):
        print("記録は既にある -> %s(**上書きしない**)" % p)
        print("  今回の実行で取った件数: %d(0 なら全部すでに手元に在った)"
              % sum(1 for r in out if r["how"] == "取った"))
        print("  記録を作り直すなら、先に古い記録を自分で退避すること。")
        return 0
    json.dump({"tool": "fetch_new_draw_2026-10-09.py", "fetched": out},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("記録 -> %s  **中身は読んでいない**(中身の印は ZIP の目録だけから作っている)" % p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
