# -*- coding: utf-8 -*-
"""冊子の道具(python)が数える数を JSON で出すだけの読み取り。**判定も編集もしない。**

【なぜ要るか】Observation Packet の試験 A(冊子の数との一致。計画
`docs/PLAN_OBSERVATION_PACKET_2026-09-30.md` §5b)で、**2 つの数だけ突き合わせ相手が無かった** ―
「第 1 候補と実戦の側が逆だった分かれ道の**分子**」(冊子の本文の 51)と
「10 秒以上考えた分かれ道のうち側が逆だった手」(本文の 5)は、
既存の python の関数がその場で数えているだけで **JSON に残っていない**。
そこで**冊子が実際に使っている実装をそのまま呼ぶ**。TS 側の packet と**別の言語の別の実装**なので、
期待値を書き写すより強い相手になる(書き写しは材料が変わったときに古くなる)。

【出さないもの】`side_match_of` が返す `rows`(局面ごとの側の印)は**出さない** ―
この道具が要るのは合計だけで、局面ごとの印を通す必要が無い(通す口を作らない)。

【静かに空を返さない】材料が読めない・関数が None を返すときは **終了コード 1 で理由を書く。**
呼ぶ側(`scripts/playtest/observationPacket.ts`)はそれを問題として並べる。

使い方:
  python3 -X utf8 dump_booklet_numbers.py --time-cause <time_cause.json> --group "3 分" \
      --whatif <whatif-v2 のフォルダ> [<フォルダ> …]
"""
import argparse
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_answer as CA  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--time-cause", required=True)
    parser.add_argument("--group", required=True)
    parser.add_argument("--whatif", required=True, nargs="+")
    args = parser.parse_args()

    with io.open(args.time_cause, encoding="utf-8") as f:
        time_cause = {"raw": [json.load(f)]}

    long_think = CA.long_think_fork_of(time_cause, args.group)
    if long_think is None:
        print(f"長考の数が取れない(組「{args.group}」の局が time_cause に無い)", file=sys.stderr)
        return 1

    side_match = CA.side_match_of(args.whatif)
    if side_match is None:
        print(f"側の数が取れない(分かれ道の行が無い): {args.whatif}", file=sys.stderr)
        return 1

    out = {
        "longThink": long_think,
        "sideMatch": {
            "attack": side_match["attack"],
            "defense": side_match["defense"],
            "forkTotal": side_match["forkTotal"],
            "opposite": side_match["opposite"],
        },
    }
    print(json.dumps(out, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
