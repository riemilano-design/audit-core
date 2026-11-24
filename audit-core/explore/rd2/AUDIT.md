# 監査 ― 便 RD2(2026-11-24)

独立監査(step-auditor)を結果の前に 1 回。判定 **GO**。監査は木を読むだけで、集計の再現は repo の外(scratchpad)に書いた。

## 凍結(sha256。監査の始めと終わりで 6 file とも一致)

```
f91ef95222d71d566f53206953bf383fcb034c79060c6900f5cadc930a0da20c  build_rd2.py
3067635c4aeb65077048e11b0cb1cf5dd7dd8f8afb540d73f7a5528de93afb7e  tally_rd2.py
7d5f7fdb08d3b1d729ba0574aaa084e30637d12f0a50b5beee5b9e7bd2fe6f25  record.json
17bebf6feaaaf2fc7ced36d847c5ea0c4ac1a81237cb076ebdaefe323b923f70  RESULT.md
11e3ae7fc2121f2c65aaf5329e9de0122dd96f8b6fe34da3239d7bc80b25eba4  SEAL.md
e878ebd30feca823ef78829b0ebdbbeba2b77a2cb8de544fbee2ad638a7aad59  BRIEF_DECIDE_RD2.md
```

## 報告の写し(要約せず、要点の順のまま)

1. 封の不変: `git diff 59a6fbe2 -- SEAL.md BRIEF_DECIDE_RD2.md` は空。
2. build_rd2.py は封 §1 のとおり(RD0 の作り方・`#` 7〜17・番号 31〜41・足したのは減価償却費の代わりの要素 1 つだけ)。tally_rd2.py は tally_rd0 の会社の番号を 31〜41 に替えて走らせるだけ。engine(core/・adapters/)の変更は 0 行。
3. 数の一致: 監査が tally_rd2.py を走らせ直した出力は record.json と完全一致。RESULT.md §1 の表は record.json と、RD1 の列は rd1 の record.json・RESULT.md と一致。予測 RD2-1〜5 の判定は封の字のとおり。
4. 秘匿: RESULT.md・record.json に docID・EDINET コード・会社の名・file の名・金額・日付は無い(文書の日付だけ)。
5. §3 の読み: 司令塔の確かめの script で、止めた 13 行の内訳と社・項目の割り当てが記述と一致。第 31 社の席の値が事業収益の要素の値と一致することも確かめた。
6. 軽い指摘(GO を妨げない):
   - 第 31 社の席の値は、事業収益の要素のほか、別の 2 つの要素とも同じ値。「事業収益の要素と一致」は唯一の一致ではない。
   - 第 34 社の S2 を変換の欠陥とする読みと、第 38 社の同じずれは、監査の script では再現していない(S2 が出た事実までは確認)。司令塔の読みと分かる書き方なので言い過ぎではない。
   - RESULT.md の冒頭が参照する AUDIT.md を置くこと。

## GO の後の直し(文書だけ)

- 指摘 1: RESULT.md §3 に、同じ値が別の 2 つの要素にも在ることを書き足した。
- 指摘 2: 第 34 社の読みに「司令塔が貯めた行の列の見出しを見た読み」「変換の直しはこの便ではしない」と書き足した。
- 指摘 3: この file を置いた。
- 直しの後の RESULT.md の sha256: `1c57839d162683ec86264b5a5aa3d9d16f1426977a65c6d7db17f80456e12905`(ほかの 5 file は上の凍結のまま)。
