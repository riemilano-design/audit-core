# 結果 ― 便 XC5: 道具の出力の文から読んだ原因を直し、組んだ包みの誤りの符号を減らす(2026-11-26)

封: [SEAL.md](SEAL.md)(commit 84af78de)。監査: [AUDIT.md](AUDIT.md)(組んだ形は [AUDIT.html](AUDIT.html)。GO)。記録: [record.json](record.json)(組ごとの数は `out/dev.json`・`out/held.json`)。script: [xc5.py](xc5.py)・[tally_xc5.py](tally_xc5.py)(封で commit した。封の後の変更 0 行)。軽い型。engine 0 行・`measure/` と便 XC0〜XC4 の file 0 行・費用 0 USD・LLM の席 0。素材は受理済みの本物の有報。記録には会社の名・コード・file の名を書いていない(道具の符号は書いた)。

## 1. 出た数(記録の写し。判定の 40 組)

**今年の答えを見ずに組んだ包みで、組んだ側だけで EDINET の E の符号が鳴らなかった組は 29 / 40(便 XC4 は 0 / 40)。誤りの符号が 1 つも鳴らなかった組は 25 / 40。** 提出できる形ではない(置いていない fact が多く、W の符号 EC8029W は 40 組とも鳴る)。

| 組んだ包み(道具 P) | 数 |
|---|---|
| 組んだ側だけで EDINET の E の符号が鳴らなかった組 | **29 / 40** |
| 組んだ側だけで誤りの符号が 1 つも鳴らなかった組 | **25 / 40** |
| 道具が最後まで読んだ組 | 36 / 40(便 XC4 は 34) |
| 道具が読んだ数の fact で元と同じ行 | 32251(元の 40741 の 79.2%。便 XC4 は 32124) |

| 文の fact(答え 10335) | 数 |
|---|---|
| 置いた | 3544 |
| 置き場と属性が答えと同じ | 3270(答えの 31.64%) |
| 置いた中の答えと違う | 274(7.73%) |

| 直しが働いた数 | 数 |
|---|---|
| F1 で置かなかった文の fact | 52 |
| F2 で直した roleRef | 260 |
| F3 で除いた文脈 | 1119 |
| F5 で置かなかった数の fact・文の fact | 2・1 |
| F7 で提出日を本文から入れた文脈 | 123 |

組んだ側だけで鳴った符号の組の数(全部): `EDINET.EC8029W` 40・`EDINET.EC8075W` 28・`EDINET.EC8030W` 13・`arelle:nonIxdsDocument` 8・`EDINET.EC8069W` 7・`EDINET.EC8076W` 6・`EDINET.EC3005E` 5・`EDINET.EC5700W` 5・`EDINET.EC8024E` 5・`EDINET.EC8050W` 4・`EDINET.EC8055W` 4・`xbrldie:PrimaryItemDimensionallyInvalidError` 4・`EDINET.EC3002E` 3・`exception:AttributeError` 3・`EDINET.EC1001E` 2・`EDINET.EC1057E` 2・`EDINET.EC8070W` 2・`xbrldie:ExplicitMemberUndefinedQNameError` 2・`AttributeError` 1・`EDINET.EC1004E` 1・`EDINET.EC5602R` 1・`EDINET.EC8015W` 1・`EDINET.EC8039W` 1・`EDINET.EC8041W` 1・`EDINET.EC8043W` 1・`EDINET.EC8044W` 1・`EDINET.EC8048W` 1・`EDINET.EC8049W` 1・`ix10.11.1.2:missingReferences` 1・`ix10.9.1.2:contextReference` 1・`xbrl.4.6.1:itemContextRef` 1。`xbrl.3.5.2.4.5:roleRefMismatch`・`xmlSchema:syntax` は 0。

## 2. 予測の当たり外れ

| 番号 | 予測 | 出た数 | 判定 |
|---|---|---|---|
| XC5-1 | EDINET の E の符号が鳴らなかった組は 30 以上 | 29 | **外れ**(1 足りない) |
| XC5-2 | 誤りの符号が 1 つも鳴らなかった組は 20〜36 | 25 | 当たり |
| XC5-3 | roleRefMismatch は 1 以下 | 0 | 当たり |
| XC5-4 | xmlSchema:syntax は 1 以下 | 0 | 当たり |
| XC5-5 | EC1001E は 6 以下 | 2 | 当たり |
| XC5-6 | 数の fact の元と同じ行は 32000 以上 | 32251 | 当たり |
| XC5-7 | 文の fact の違いは 10% 以下・一致は 25〜40% | 7.73%・31.64% | 当たり |
| XC5-8 | 道具が止まった組は 4 以下 | 4 | 当たり |

## 3. 読み(結果の後に司令塔が見た。記録の外の読み)

- **XC5-1 の外れ(29 と 30)は、判定の組で残る E の符号が作りの組より多かったため。** 残る E の符号は EC3005E・EC8024E(5 組ずつ)・EC3002E(3 組)・EC1001E・EC1057E(2 組ずつ)・EC1004E(1 組)。EC3002E・EC3005E は便 XC4 で `nonIxdsDocument` と同じ組で減った符号で、文の fact を 1 つも置けなかった `.htm` の在る組と読む(確かめていない)。
- **便 XC4 から減った誤りの符号**(組の数): roleRefMismatch 35 → 0・xmlSchema:syntax 15 → 0・EC1001E 35 → 2・EC1004E 35 → 1。訓練の 3 組で道具の文から読んだ原因の直しが、判定の組でも効いた。
- **数の fact の元と同じ行が 127 ふえた**(32124 → 32251)。F3(使う文脈だけ)か F7(提出日)で道具の読み方が変わった分と読む。内訳は数えていない。
- 残る誤りの符号のうち `xbrldie:`(4・2 組)と `exception:AttributeError`(3 組)の原因は読んでいない。

## 4. 言えないこと

- **E の符号が鳴らないことは、提出できる XBRL であることではない。** 数の fact の 2 割・文の fact の 7 割を置いておらず、それは W の符号でしか出ない。置いた文の fact の 7.7% は違う置き場。
- 「軸のメンバーの在る文脈の文の fact は置かない」(便 XC4・F6)は、実装では文脈の id に `_` が在るかで代用している。文脈の中身(scenario)は見ていない。
- 提出者別タクソノミは今年の物の持ち込み。道具は 1 行を直した版で、EDINET の本物の検査とは照らしていない。
- 便 XC0〜XC4 の限界を全部継ぐ(素の本文は原稿ではない・前の年の在る会社だけ・63 組は無作為でない・判定の 40 組は 6 度目)。

## 5. 次の候補

(i) 置かなかった fact と置いた文の fact を人が確かめる画面(前の年と今年を並べる。提出できる形への残りの道)。(ii) 提出者別タクソノミを前の年から作る(持ち込みをやめる)。(iii) 残る誤りの符号(`xbrldie:`・EC8024E・道具の例外)の原因を読む。(iv) やめる。
