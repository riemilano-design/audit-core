# 封: 決算短信の概況の文を、同じ短信の添付の財務諸表で確かめる TSS ― 手元の 400 本(通期 250・中間 150)・0 USD・engine は 0 行 ― 2026-11-14

人間の決定(2026-11-14):「測った事実は増やして、あらゆる文書に対応していきたい」。これはスコープの拡大で、人間が決めた。司令塔はこれを「**数の出どころが機械で読める文書**から順に、1 便に 1 つの出どころで、封 → 実測 → 結果(負けた数も残す)」と読む。この封はその第 1 便。

これまで engine が測った組み合わせは「文 × 有価証券報告書の XBRL」だった(AI の文 200 本・決算短信の概況 17 社。どちらも出どころは有報)。この便は**出どころを決算短信そのものに替える**: 短信の添付資料の「経営成績等の概況」の文を、**同じ短信に付いている財務諸表(iXBRL)**で確かめる。有報が出る前の時点で、短信 1 本だけで閉じる形。

この便で言えるようになること(結果が出たあと): 「短信の概況の数のうち、同じ短信の財務諸表の値に結べた数・止まった数・『値が違う』と言った数」と、その『値が違う』の中身。**言えないこと**: 誤りを通す率(注入は次の便 1b)・文の正しさ・上場会社全体の率。

## §0 材料と決めごと

### §0-1 測った事実(この封を書く前に司令塔が 0 USD で数えた下調べ。script は scratchpad に在り、記録ではない。engine は共有の木の HEAD c1ba898b のまま・0 行)

1. **材料の在りか**: 英文短信の 3 つの便(50 本・200 本・中間 150 本。封は `sales/EN_TANSHIN_50_SEAL_2026-11-10.md`・`sales/EN_TANSHIN_EXPAND_SEAL_2026-11-13.md` ほか)で、人間の許可を得て取った日本語の短信の TDnet の XBRL パッケージ(ZIP)が、この席の scratchpad に 400 本在る。sha256 の重なりは 0。400 本とも `XBRLData/Attachment/qualitative.htm`(添付資料の全文)と、添付の財務諸表の iXBRL(`XBRLData/Attachment/` の下の、名前が `-ixbrl.htm` で終わる file)を持つ。**この便の新しいダウンロードは 0。**
2. **群**: 甲 = 通期の 50 本、乙 = 通期の 200 本、丙 = 中間の 150 本。**A = 甲 + 乙 = 通期 250 本、B = 丙 = 中間 150 本。** 3 つの群は英文短信を出している会社から引いた標本で、上場会社全体からの標本ではない。
3. **様式の種類**(サマリーの file 名 `XBRLData/Summary/tse-<8 字>-…` の 8 字): A は acedjpsm(日本基準・連結)203・acedifsm(IFRS・連結)43・anedjpsm(日本基準・非連結)4。B は scedjpsy 110・scedifsy 29・scedjpsm 7・snedjpsy 4。
4. **engine の入口の形**(読んだだけ。変えない): `adapters/xbrl/instance.py` の `load_instance` は ZIP の `XBRL/PublicDoc/` の下だけを読み、`.xbrl` が無ければ `.htm`(iXBRL)の `ix:nonFraction` を fact に、名前に `ManagementAnalysis` を含む `…TextBlock` の `ix:nonNumeric` を文にする。書類の表示名を読む `inline_labels` は、名前が `_ixbrl.htm`(下線)で終わる file だけを読む。TDnet の ZIP は置き場所も名前(`-ixbrl.htm`。ハイフン)も違うので、そのままでは engine に入らない。**`measure/` の側で ZIP を包み直せば、engine を 1 行も変えずに入る**(§0-2 の 4)。
5. **切り出しの下調べ**(§0-2 の 3 の規則そのもの): A 250 本のうち**切れた 239・切れない 11**、B 150 本のうち**切れた 133・切れない 17**。切れない 28 本は全部「始まりの見出しが規則に当たらない」(見出しの書き方が規則の 3 つと違う。下調べで粗く見た範囲では「当中間期決算に関する定性的情報」(「期」が入る)が 4 本、ほかはばらばら。規則はここで広げない)。B の切れた 133 本の見出しは「経営成績等の概況」91・「当中間決算に関する定性的情報」40・「当四半期決算に関する定性的情報」2。A の 239 本は全部「経営成績等の概況」。概況の字数の合計は A 1,204,375(最小 226・中央 4,515・最大 24,161)、B 445,473(最小 81・中央 2,905・最大 10,568)。
6. **判定の下調べ(profile P33E。数の claim)**:

   | 群 | 切れた本 | 数の claim | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND |
   |---|---|---|---|---|---|---|
   | 甲(通期 50) | 48 | 3,418 | 1,061 | 377 | 766 | 1,214 |
   | 乙(通期 200) | 191 | 14,279 | 4,344 | 1,521 | 3,214 | 5,200 |
   | **A(甲 + 乙)** | **239** | **17,697** | **5,405** | **1,898** | **3,980** | **6,414** |
   | **B(丙・中間 150)** | **133** | **6,834** | **1,229** | **0** | **855** | **4,750** |

   A の様式ごと: acedjpsm 198 本・claim 14,496・GROUNDED 4,765、acedifsm 37 本・2,906・612、anedjpsm 4 本・295・28。A で claim が 0 の本 2・GROUNDED が 0 の本 6・VALUE_MISMATCH が 1 以上の本 220。A の VALUE_MISMATCH 1,898 のうち span に `%` を含む 1,273・導出(pointer が `formula:` で始まる)425。
7. **B(中間)で VALUE_MISMATCH が 0 の理由(下調べで読んだ)**: 中間の短信の iXBRL は期の名前が `InterimInstant`・`InterimDuration`・`Prior1InterimDuration` などで、engine の期の読みは `CurrentYear…`・`Prior1Year…` だけ。engine は中間の期の fact を当期・前期として選べず、B の POINTER_NOT_FOUND 4,750 のうち reason `no_element` が 4,357。**B の「値が違う 0」は「違いが無い」ではなく、engine が中間の期を読めないこと**を指す。この便は B をそのまま測って限界として記録し、期の対応を `measure/` の側で付ける直しは別の封にする。
8. **時間**: 400 本の切り出し・包み直し・判定は、この機械の 4 並列で約 33 秒(下調べ。1 回)。
9. 包み直しの名前を `-ixbrl.htm` のまま(書類の表示名を読まない)にした場合も数えた: A は GROUNDED 5,399・VALUE_MISMATCH 1,909・UNVERIFIABLE 3,984・POINTER_NOT_FOUND 6,405、B は 1,191・0・860・4,783。差は小さい。この便は engine の約束どおり `_ixbrl.htm` に替える側だけを測る。

### §0-2 司令塔の決定(人間の言葉「任せる」「測った事実は増やして、あらゆる文書に対応していきたい」の下で)

1. **母集団は §1 の表の 400 本**(sha256 で留める)。足さない・引かない。切れない 28 本も母集団に残し、「切れない」と数える。
2. **本は ZIP の sha256 だけで呼ぶ。** 証券コード・会社名・TDnet の番号・docID は、追跡する file(封・記録・結果・門・script)に書かない。記録は件数・state・位置・番号だけで、文・span・値・pointer の字・要素名を持たない(これまでの記録と同じ)。
3. **切り出しの規則**(実装者が 1 通りに書ける字で):
   - ZIP の member がちょうど `XBRLData/Attachment/qualitative.htm` のものを utf-8(strict)で読む。無ければ「切れない(member なし)」、読めなければ「切れない(decode)」。
   - `measure/xbrl_tanshin_2026-11-09.py` の `html_to_lines` で行にし、各行に NFKC を掛けて前後の空白を落とし、空の行を捨てる。
   - 始まり = 正規表現 `^1\s*\.\s*(経営成績等の概況|当中間決算に関する定性的情報|当四半期決算に関する定性的情報)` に当たり、かつ行の中に `...` も `・・` も無い行のうち、**最後の行**(目次の行を外すため)。無ければ「切れない(始まりなし)」。
   - 終わり = 始まりより後で、正規表現 `^2\s*\.\s*[^\d\s]` に当たる**最初の行**。無ければ「切れない(終わりなし)」。
   - 文 = 始まりの行から終わりの行の手前までを `\n` でつないだもの。
   - 当たる例:「1.経営成績等の概況」「1. 当中間決算に関する定性的情報」。当たらない例:「1.経営成績・財政状態の概況」「1.当中間期決算に関する定性的情報」「(1)経営成績に関する説明」「1.経営成績等の概況 ......... 2」(目次)。終わりに当たらない例:「2.5%増加しました」(数字が続く)。
   - NFKC を掛けたことは記録に書く(全角の数字・括弧・％ が半角になる。engine の数の読みは半角を前提にする)。
4. **包み直しの規則**(`measure/` の側。engine は 0 行):
   - 元の ZIP の member のうち、`XBRLData/Attachment/` で始まり file 名が `-ixbrl.htm` で終わるものを、名前の順に、`XBRL/PublicDoc/<file 名の末尾の -ixbrl.htm を _ixbrl.htm に替えたもの>` として新しい ZIP に入れる(中身は 1 byte も変えない)。
   - サマリー(`XBRLData/Summary/`)の iXBRL は入れない。
   - 文は `XBRL/PublicDoc/zz_overview_ixbrl.htm` として入れる: `<html><body><ix:nonNumeric name="jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock" contextRef="FilingDateInstant" escape="true">` + `adapters/xbrl/prose.py` の `prose_to_html(文)` + `</ix:nonNumeric></body></html>`。
   - 包んだ ZIP を `adapters/xbrl/verify_document.py` の `verify_document(包んだ ZIP, "P33E")` に渡す(`text` は渡さない)。数の claim = `claims` のうち `kind == "num"`。
   - 包んだ ZIP は memory の中だけで作り、どこにも書かない。
5. **profile は P33E だけ**(README の推奨)。ほかの profile との比べはこの便ではしない。
6. **材料の置き場**: `~/.cache/audit-core/tanshin-self-2026-11-14/<sha256>.zip`(新しい folder。置く script だけが書く)。scratchpad の 3 つの folder から、sha256 が §1 の表に在る file だけを写す(表に無い file は写さない・400 本そろわなければ止める)。**ほかの cache folder には 1 file も足さない**(cache の一覧の sha256 は、この新しい folder を除いて前後で同じ)。ネットワークには出ない。
7. **「値が違う」の中身を読む標本**: A の VALUE_MISMATCH の行を(§1 の表の # の順・文の番号の順・位置の順)に並べ、Python 3.9 の `random.Random(20261114).sample(range(行の数), 120)` で 120 行を引き、番号の順に並べる。行の数が 120 に満たなければ全部。司令塔(**AI の席。人は読んでいない**)が 1 行ずつ文と結んだ先を読み、次の型のどれか 1 つを付ける。読むための紙(文・span・結んだ先・値)は repo の外(scratchpad)に置き、追跡しない。
   - (ア) セグメント・事業・地域・製品別の数を、全社の fact と比べた
   - (イ) 内訳・一部分・文の中で計算した率や差を、全体の fact と比べた
   - (ウ) 計画・予想・目標の数
   - (エ) キャッシュ・フローの向き・増減の書き方
   - (オ) 定義の違い(同じ名前でも文の言う範囲が fact と違う)
   - (カ) 丸め・単位
   - (キ) 損失・マイナスの符号
   - (ク) **本当の差の候補**(文が全社のその項目の当期の数を言っていて、同じ短信の財務諸表の値と違って見える)
   - (ケ) 読んでも分けられない
   (ク) は候補で、紙面(PDF)で確かめるまで「食い違い」と呼ばない。会社は名指さない。
8. **注入(誤りを通す率)はこの便では測らない。** 次の便 1b(別の封)で、同じ材料に T1・T5・T8 を掛ける。
9. 0 USD。LLM の席(API)は呼ばない。外へは何も出さない。

## §1 母集団(字で留める。400 行。置く script と記録はこの表と同じ 400 行を持ち、sha256 が違えば止める)

「下調べ」の 2 欄は §0-1 の下調べの値(切り出しの成否と、切れた本の数の claim)。

| # | 群 | 様式の種類 | ZIP の sha256 | 下調べ: 切り出し | 下調べ: 数の claim |
|---|---|---|---|---|---|
| 1 | 甲 | acedifsm | `014dc61c6aab0c4f28d15ed0694eb51053ce939b6d186dcb1e539d911c2f7127` | 切れた | 41 |
| 2 | 甲 | acedifsm | `0906918ad1c02608705b5a7445a46080550388f403c0354f754d17a17c0e8a39` | 切れない | - |
| 3 | 甲 | acedjpsm | `0a32341950633b1f6147c38c5891d55ea865946b5d778efce9c1a8b28119ce8a` | 切れた | 62 |
| 4 | 甲 | anedjpsm | `12e6f920f80a80e6c926d3c55638ff93e7e54c7bd5b919c51ca6256ab121c716` | 切れた | 77 |
| 5 | 甲 | acedifsm | `14e0570bc2783996379dd6df3379943bfec5fdc65f7b2900ff93af0d7330aa8b` | 切れた | 43 |
| 6 | 甲 | acedjpsm | `24f1971430bf00ab55589d6aa224fbc7c79a67cdbf479562212bcca10b46a696` | 切れた | 38 |
| 7 | 甲 | acedjpsm | `2a35779542206ce6604d5558f95d1ba362b118ba2efa76bdf1ad13e42f70cc16` | 切れた | 54 |
| 8 | 甲 | acedifsm | `2ba6f5006c858b5ec9be52f2d8165aaca59289534bdf0ddc035e9959d261e457` | 切れた | 68 |
| 9 | 甲 | acedjpsm | `2de323997f5697d49b2337325ab3f072c540913b10eca54cc955db6919ff4e65` | 切れた | 94 |
| 10 | 甲 | acedifsm | `2fbd804f8e0cf1476a7a78352ed770acde7f30850de3ee12c81bccce02a7040c` | 切れた | 135 |
| 11 | 甲 | acedifsm | `35288b535d48bebac273a5c60b05cb24443f9b4c30e463463233a51267636bba` | 切れた | 68 |
| 12 | 甲 | acedjpsm | `36847ba020be2ba52c0b2571384cff981729153830ad25393a294f68ac5b8e72` | 切れた | 75 |
| 13 | 甲 | acedjpsm | `3840182dd3e8617bde0e662a79d3cc802489f3dd9cc01d7a7738cfed225c7062` | 切れた | 92 |
| 14 | 甲 | acedjpsm | `39621a75c825e7b695f7a76ead147373c1971609107d8cb7e9001c3dfec2ff22` | 切れた | 112 |
| 15 | 甲 | acedifsm | `3dee5b0503faad1f250812fecc1b1ce3d2141845f34e65e993c80f0aae511847` | 切れた | 98 |
| 16 | 甲 | acedjpsm | `47da6c1cb2a12b1365569f03ad8334e9c77b9b25117e8298c2c231da864a6eca` | 切れない | - |
| 17 | 甲 | acedifsm | `4ac7f64558ac01a2b222a52eb2f058971847e63bfad1e9d2dca74f2c323263cd` | 切れた | 48 |
| 18 | 甲 | acedjpsm | `4deb5ac7c819c458dbb6d502617bf6537f58a4d5ebac8625993802d6d58951e8` | 切れた | 91 |
| 19 | 甲 | acedjpsm | `558afee395050574fa2574ebd2881baf95245cd4b355cb672726d5a9ac2845aa` | 切れた | 49 |
| 20 | 甲 | acedifsm | `58d40410b8f3c9ae23ed152e14fcce90224cb1ea5141b2e6b77ed879ec080dc3` | 切れた | 64 |
| 21 | 甲 | acedjpsm | `5d9eb9bdcc8285cf6b5a25eed4566ad5d948f374d23d7e9aa7e37856de0060b3` | 切れた | 12 |
| 22 | 甲 | acedjpsm | `67e111a5edf6640ed7e5f6ac88e577824d9f0c074f36b8eaad94d332ffd04251` | 切れた | 56 |
| 23 | 甲 | acedifsm | `6a7f3aaaadf9da74a270d3deee0422f1c306d3ad54f6e4d9f40ce3e03c821c35` | 切れた | 30 |
| 24 | 甲 | acedjpsm | `6cbda2be10b55d0981d5dbe4005f484624aa9b580335f070e0944aa7895a02f0` | 切れた | 62 |
| 25 | 甲 | acedjpsm | `70ce0fac704ef96a3e9c001077d676e811b4538cadf54841bc650c30200a29bf` | 切れた | 60 |
| 26 | 甲 | acedjpsm | `765d43b05b1acf8fffd2fe8d1d2990bbcacdd388d318dacd82bd2f6f580e18db` | 切れた | 90 |
| 27 | 甲 | acedjpsm | `7fce6d41fd29270d5b51c244b9ebb404ea44089222eaa24405380c5fa1c0da4f` | 切れた | 66 |
| 28 | 甲 | acedifsm | `8289e26169c77f8c4a0362ac6c5c81f4c28118182fccd95080d2546586535c6f` | 切れた | 59 |
| 29 | 甲 | acedjpsm | `842a7f2ecf189ab8d270c160a4a469128d77011ba1bc991e5d4e40b165d72b52` | 切れた | 88 |
| 30 | 甲 | acedifsm | `87509c40b8e645e2753c8e09936d75e1e606a7801f5d0af5bd4cfcb2546eb6d5` | 切れた | 0 |
| 31 | 甲 | acedjpsm | `87cac2e8a395e3426decc6b5f8f526c99c8eebb652e8e8ca76b2106dbc6270cd` | 切れた | 67 |
| 32 | 甲 | acedjpsm | `95963c254103066578a3721d5c5d6427eab25ac7f94b213cf35fb2c2773aefaf` | 切れた | 68 |
| 33 | 甲 | acedjpsm | `9ee94dec5c7161145e556d4183ac2e44d14cacefa72fe7ad2eff12035532ccff` | 切れた | 92 |
| 34 | 甲 | acedjpsm | `a395a61cb8624b2645217b19ea79f3fa714fbd6df86e9ccdd4d57eb3e378bcc0` | 切れた | 70 |
| 35 | 甲 | acedjpsm | `b3b4c773439a9717a4f5db35d5e08d8a9273bcab8edccc9302e038079142bbc1` | 切れた | 108 |
| 36 | 甲 | acedjpsm | `c967bd451fcb5b0d4ad1717644d9e0c15a09451d8e71d2d2e6e31a9847403b5b` | 切れた | 67 |
| 37 | 甲 | acedifsm | `cb5302192471a0202b5b008bb1fe80fe8b42d5b1a9786ed041d2903187c4afc1` | 切れた | 77 |
| 38 | 甲 | acedjpsm | `d1537403c020108a57351ae1832cd219c9afcab88fea359508c54a25aef601c5` | 切れた | 66 |
| 39 | 甲 | acedjpsm | `d436d08290b082298aed3af8a18f21224eaede9a8875c5ca9dd99a33a830adaa` | 切れた | 77 |
| 40 | 甲 | acedjpsm | `d4ec1d44cb2f429aac37d1ac1677282bf4bf6ef0dc766f0b2e2a3dadb7dd1dff` | 切れた | 58 |
| 41 | 甲 | acedjpsm | `d76af952b82d84f364ce1515f10392988ed6e26c1821adba51276f3fa8d10641` | 切れた | 43 |
| 42 | 甲 | acedjpsm | `da719d213a0b643c069393c6947a39f8828e29f5652e9339e08b429fc79ed2fe` | 切れた | 62 |
| 43 | 甲 | acedjpsm | `df921a6ac95ec0060de54857135431330837edf7a387ee1cec9d2c5d48240af8` | 切れた | 156 |
| 44 | 甲 | acedjpsm | `e0353e91b348ba5e9c242b4bfbb9eb6ef7ccd22c74cf28b426e4a0867c770963` | 切れた | 73 |
| 45 | 甲 | acedjpsm | `e0c59b5fcd093e7768534d17a8502cd012a3d72ecbd5e74b7e26bcd3fe276bad` | 切れた | 58 |
| 46 | 甲 | acedjpsm | `e688122e944b3cbd05facfb4e8c4b671c6d17675d06b09bf5a3afef74bcd5e02` | 切れた | 100 |
| 47 | 甲 | acedjpsm | `ed7d59e420f937a602403615c79892af59cc43e17be420865aa70aa50a4c4b40` | 切れた | 62 |
| 48 | 甲 | acedjpsm | `ede42df7f7c688b5839e6beae632af517f4441f55718c953c7bfdd56172280d9` | 切れた | 110 |
| 49 | 甲 | acedjpsm | `f9020ac26cd1edadf981a566cf95ef085583c62dd9841eceba8999299a9ad373` | 切れた | 102 |
| 50 | 甲 | acedjpsm | `fee3d518a5d3fac2ce7534b07ba604e4b67953d7902010ccfa4bd6cc36ab264a` | 切れた | 70 |
| 51 | 乙 | acedjpsm | `02967e840a838874f8a6b9009355d604bd2de0785cae1bd054d1bad691f03c5f` | 切れた | 15 |
| 52 | 乙 | acedjpsm | `02f2ad7a4324ce22d6c27e665c1ca469d1beb2e5e08ebafdc41a8b2df381f3f4` | 切れた | 68 |
| 53 | 乙 | acedjpsm | `039b53b1eeaa6277e558d26e23b8fa8168b07a8d3c26268c5dfac840accad008` | 切れた | 100 |
| 54 | 乙 | acedjpsm | `04d250e0c12572480c2df05cbf624391c4c6888cc206c0f69e20f6e2b404d623` | 切れた | 24 |
| 55 | 乙 | acedjpsm | `0a15fcb00f13a19a569594a004d853042c713bb1258c0f63f0d0df56e0c5a76c` | 切れた | 102 |
| 56 | 乙 | acedjpsm | `0ca13095b411e5bf44e1d1c0d8845ca536fd398d0bc0e63b63c0b6cfe1667a0f` | 切れた | 45 |
| 57 | 乙 | acedjpsm | `0d310707c451c388e7f6f4cddbbb85d8807172c6040e1158959a3b1e08ed9928` | 切れた | 30 |
| 58 | 乙 | acedjpsm | `0ff1f6851293c38a4723e1ee20ed786580c138fbe4f810fb529bde99cffce9b6` | 切れた | 67 |
| 59 | 乙 | anedjpsm | `106162580a40e7d3a76938cccf45f8c9e835663e2c8b6c43b3c729cb5d57d599` | 切れた | 64 |
| 60 | 乙 | acedjpsm | `1285b5d8cb22f76cd7f854541d6ad3b7c19ea4cd21354e7f540d562bec365c04` | 切れた | 54 |
| 61 | 乙 | acedjpsm | `12a42ab257ae3dbf7cf5e1fde2c52f9917e9bbcbecf275aa3748d6fe36958b32` | 切れた | 58 |
| 62 | 乙 | acedjpsm | `142c5c89f72d23e39071bcf00a38e2173a74294c523d6daa9c4838e70a5c8f7c` | 切れた | 77 |
| 63 | 乙 | acedjpsm | `161bdba43855621a712ca343175decc50230c2e409a7f9dab7aeb04fdf0874a3` | 切れた | 84 |
| 64 | 乙 | acedjpsm | `1817c3b83112c8c5bacbfee213103349d833fb199401f883ef40fc0066b1a37e` | 切れた | 38 |
| 65 | 乙 | acedjpsm | `18a5bfac162427e363f13fef8341952e6bf7982204bdd6e5246d5ec5bd6edf6a` | 切れた | 55 |
| 66 | 乙 | acedjpsm | `1ad26b4db0dc8648204470c01f65d5b17fcdeb357d79446993e4fe8520aaf137` | 切れた | 73 |
| 67 | 乙 | acedjpsm | `1b697acde06c8be0c65e1f2ff017b88f92cf617e41b31022455bde712750f91e` | 切れた | 63 |
| 68 | 乙 | acedjpsm | `1c9ba0ecfeaa80ba6927d5caa1413f176a28bdbd4517e5ee82333105a08b34ce` | 切れた | 102 |
| 69 | 乙 | anedjpsm | `1d217949ec0c79a4f2013083b877d64224698f6c072afb711719772d2f5972d6` | 切れた | 93 |
| 70 | 乙 | acedjpsm | `20e59abd647bb9abbd3327c3aae8cb1117eaf24a6129c401165e215046e0a548` | 切れた | 99 |
| 71 | 乙 | acedifsm | `2459a231dd1117f75e6d6ed2688974cd6b26577596fc8e9d0a0f40b968c89c53` | 切れない | - |
| 72 | 乙 | acedjpsm | `28d4edd7e1ebf903aab03384d852e2e256845683ac7351a3dbfc33b75279dc6b` | 切れた | 0 |
| 73 | 乙 | acedjpsm | `292d45351aa06d6005406b10fd8dc43c4aa9d0978b9889a3d8b92e523a532e7a` | 切れた | 78 |
| 74 | 乙 | acedjpsm | `2a685f23518f2c3b34370ea9996c435baeffb394f8530e63714715048bd36cd7` | 切れた | 47 |
| 75 | 乙 | acedjpsm | `2abb3ac266581841e4b050615a68b8da024bdb5de39c5204f7f18c079a39d7c0` | 切れた | 64 |
| 76 | 乙 | acedjpsm | `2bfcee07a5aa654deadcb0cce57e5c748f445eb1874138d28b1707f6a8143b8e` | 切れた | 77 |
| 77 | 乙 | acedifsm | `2dc2d72d67b4e1cbb2dd5a0f437ee1d6cd46194805bfbc0fe9831ca96b784b44` | 切れない | - |
| 78 | 乙 | acedjpsm | `3167dd8c887d6199b9bfa1c7a876fb0fdfcf7b7c5ec83023477f729a12054f74` | 切れた | 81 |
| 79 | 乙 | acedjpsm | `326913acc01acbf4ab4cc212ba89a5048b80ee0357bfacf0276925ae414dde03` | 切れた | 71 |
| 80 | 乙 | acedjpsm | `32919f138e15a91e539a38d2199dde93e01db6891f89b2db115b420d078a233e` | 切れた | 44 |
| 81 | 乙 | acedjpsm | `33b8434ca1f2b870e9720a5461bc23b51565bee029b43f2d60feeac9f3f533f6` | 切れた | 49 |
| 82 | 乙 | acedjpsm | `341ce5cdfae0ade5122da81a44f25aa359df53984b192a3aa62873694968b0ed` | 切れた | 59 |
| 83 | 乙 | acedifsm | `370c2fd78c22e9b5780ed71900d5ae12f79dce0a96c695dc07e56351262ef47b` | 切れた | 71 |
| 84 | 乙 | acedifsm | `378cdb33c2a3925419d57926a73a45c99a5f51321b76b852de37f00b80890c2f` | 切れた | 78 |
| 85 | 乙 | acedjpsm | `39aa77141ccedeae010fdc79cc39b4934a49ca0297a53c1207b238b9e6cf3fda` | 切れた | 41 |
| 86 | 乙 | acedjpsm | `3ad59df5d809e1d5fbef5e59c9b2c666fa15d11e09188ecc35c91517948d034a` | 切れた | 79 |
| 87 | 乙 | acedjpsm | `3b739526746dc8127f12487048dc10cc3b2fd9e3275e2b0f21765220475085f2` | 切れた | 7 |
| 88 | 乙 | acedjpsm | `3c38f3f6aca61563509360a4e68d7884b2da8bfbe8b9b8992e232df39da7f272` | 切れた | 72 |
| 89 | 乙 | acedifsm | `3cca9cc64a230c61fea66b08b2d73d1dda9cb46272e94b195a4b332c319f250a` | 切れた | 116 |
| 90 | 乙 | acedjpsm | `3d30194c81c5056989a53a7532d3a61d30dd5aae49ed89ed2328ead3b786e371` | 切れた | 150 |
| 91 | 乙 | acedjpsm | `3e1e2b326c744fc3fb88f78b6cd046cf905c418ce7837f2c9b1f07b322e7e1c8` | 切れた | 98 |
| 92 | 乙 | acedjpsm | `410885f5786a4f846b3a2f0d1fd47243135a87e9a80dff9c0b196e9bcef60c54` | 切れた | 88 |
| 93 | 乙 | acedjpsm | `410903ed76ed9e4c9c5164d9b8d1bf5f0e755a570ee173be204ad3c4b147213d` | 切れた | 77 |
| 94 | 乙 | acedjpsm | `410fb3a401a6d12823b3dd28f5a3d6a949f95781340983a335d2af6072d7e736` | 切れた | 82 |
| 95 | 乙 | acedjpsm | `415cdb236f84a22102122c1c8e94aee4275e53dcc9ab8e2ce3a799553c7cfc12` | 切れた | 89 |
| 96 | 乙 | acedjpsm | `4215901b5a28d72b2286f5af73f5c5e56bdf171e27283e2318f4eafd433ced6c` | 切れた | 62 |
| 97 | 乙 | acedjpsm | `4229a2df1a5dc09e0fea6ea247e90bbc6b51d52bff408954b97efd5454b16f86` | 切れた | 110 |
| 98 | 乙 | acedjpsm | `44e41c85374e6ccbbf864fde30550df3d8fe45df1768b87c17bdbd9b2305df26` | 切れた | 64 |
| 99 | 乙 | acedjpsm | `45774ac9052c39a8a60c8280a8a0e68e313c37d630cef476804829e3d90084c4` | 切れた | 72 |
| 100 | 乙 | acedjpsm | `46ce826c6fc6a3d131813d41680d24ecd8ba37165ee8874f3e931f642abb66d8` | 切れた | 177 |
| 101 | 乙 | acedjpsm | `4749794baa9e7ae80ff82bc7781a9b4477c665932cd37d809f5763ec008d6c64` | 切れた | 116 |
| 102 | 乙 | acedjpsm | `4823bc3f672be85bb0debc21f44eeed6f0356d5373a45a0a9ef069de5d0b432a` | 切れた | 97 |
| 103 | 乙 | acedjpsm | `4b4b34d822001e2267a734323210aefaf1a932cd471a23d4308ab4d2842830f5` | 切れた | 60 |
| 104 | 乙 | acedjpsm | `4d7d343e94ae19ce72e398f37f4deadf301bdc367e15b196e0d8048048084862` | 切れた | 58 |
| 105 | 乙 | acedjpsm | `4d8a0e08b1ab4b05f646e467026c589cb213037c9737d7b69a055686549580d6` | 切れた | 108 |
| 106 | 乙 | acedjpsm | `4f8c60871fdd7b24fa97c8ef438af34c8f14b3e1cb18c27baec51531d049482c` | 切れた | 82 |
| 107 | 乙 | acedjpsm | `4fcfdb816453afc3a477ab157cb353bf79a3ea4451ce671fa91cf26746093ce6` | 切れた | 88 |
| 108 | 乙 | acedjpsm | `51ec272183bcdd7d03634a09eef12a9298aa631235a3b8a957ccbec53b30b26c` | 切れた | 92 |
| 109 | 乙 | acedjpsm | `5314accd467494df6e716f48a7428b4e243c6c82e3d4092868fbf39a776ade31` | 切れた | 70 |
| 110 | 乙 | acedjpsm | `5350a9271806f0eccf69efd702c4f9e6fe874f7a6360cda9b9cf4b7517c4ba4e` | 切れた | 65 |
| 111 | 乙 | acedjpsm | `557efcf15df473b19fed6b2ac9b63821e9939f0e3191f83a61d02eb85ad481f5` | 切れた | 62 |
| 112 | 乙 | acedjpsm | `55ac9f12858116e5b3d780d159bf89819ad0b7bd14eca6d506c84d9f17a0b770` | 切れた | 90 |
| 113 | 乙 | acedjpsm | `57178ba6edb4c8e7311dcf395372bd17e1d7ab807ffc6b1a9bd0358ea2f9da10` | 切れた | 76 |
| 114 | 乙 | acedjpsm | `572754ae449ad92f0b9464653ba26d8a132f27c6b0bf348a43be3e33e4805514` | 切れた | 78 |
| 115 | 乙 | acedjpsm | `5a511bdc9501ccdd6f073c44b245151e7ea8a7bf58f70fac42ea0b72b32e1aca` | 切れた | 101 |
| 116 | 乙 | acedifsm | `5a8b20399d44ea275dc04c0c2a56fbc6df76e0d03e2c29db5bcf227005a78dce` | 切れた | 136 |
| 117 | 乙 | acedjpsm | `5dadb1145b0a32d93a9a6f66970af28fa1672d75eb4a98c01a281dac41bc9bde` | 切れた | 92 |
| 118 | 乙 | acedjpsm | `5e2f351e82053f972e323ccd13f99fa1c58941389823ccd9331266fe309d580a` | 切れた | 77 |
| 119 | 乙 | acedjpsm | `601dae1883ca015732d54cde05c599a87032e5b7fb44eb8831540f8d9f7d3909` | 切れた | 104 |
| 120 | 乙 | acedjpsm | `6122f4db2933cd79dc746152b17e5c447dfd01e68bc8752247f7777c65f5da82` | 切れた | 96 |
| 121 | 乙 | acedifsm | `6126e58945953bc106ff155822f4178404be02fb547f948fe3011a33072a400f` | 切れた | 155 |
| 122 | 乙 | acedjpsm | `614ab9acb74e252e1a688958bc1891d19a2f50ec62af0513d176220c71f2238c` | 切れた | 37 |
| 123 | 乙 | acedjpsm | `619e5f33d8f5c8a2b47d8545352d74c783b4852ed6faaae80d4b390ee824f161` | 切れた | 43 |
| 124 | 乙 | acedjpsm | `6394272e18a9de5b2cf309a0127e37ba76723d965a1a5c76a412765c2d5fa48b` | 切れた | 65 |
| 125 | 乙 | acedjpsm | `6418e71f0557e38d494937154c9dbc0f2ae9292a0afd4521f8eb3a9e127ae06d` | 切れた | 75 |
| 126 | 乙 | acedifsm | `64260acb6d09678b1d608e74bdbcc23486c9dacd6722dfa34adbb09729754b50` | 切れた | 96 |
| 127 | 乙 | acedjpsm | `6518cd685bdbf0fab438a582fe8ca87bf60ee7e9aec24e3242c96f7c1e7145c4` | 切れた | 117 |
| 128 | 乙 | acedjpsm | `69535f8a53ea1dd36a40a98801f27a71fec83e5b6416dd976ce2b93e08a8857d` | 切れた | 70 |
| 129 | 乙 | acedjpsm | `699b8e995d2246e0e47b6757faecf750bd1720124e684d3e7a52f3b247ef79ac` | 切れた | 94 |
| 130 | 乙 | acedjpsm | `6bbdc4e612f1e9d2639b3c1aaf60d45c9c734f5182af31140e1ae8d1b26e3f7a` | 切れた | 69 |
| 131 | 乙 | anedjpsm | `6e10634488d1e04598a52b3130b3d5290d5ceff5794095147c1de05266215130` | 切れた | 61 |
| 132 | 乙 | acedjpsm | `6ededc7f8dba73330b7b94c23f6adc1e13676e672b8a812dcfa26a676174b742` | 切れた | 21 |
| 133 | 乙 | acedjpsm | `6ef6a2b5c1ef49bbef4e5e942d0b53f404914fdca8d4e886933d976b7a20d83d` | 切れた | 83 |
| 134 | 乙 | acedjpsm | `7017d736ee00471228cba1a171b1b0d4b8fbad5ba855cf12faaa5d3fd230640b` | 切れた | 63 |
| 135 | 乙 | acedjpsm | `7064a89226afb23ccd878733f564a7899b5f8c9de0919de3e0115075c3d3d8ef` | 切れない | - |
| 136 | 乙 | acedjpsm | `71a8bf341ffd049619c55f0496d1da7bd51e583be36c8aac126126e5d1dc534a` | 切れた | 89 |
| 137 | 乙 | acedjpsm | `73bb55bdd1d663a1845d5114f08dbcd9f5758dacfab80620e8be93964f468e34` | 切れない | - |
| 138 | 乙 | acedjpsm | `74e4d4c28a5f1316d3ef2310ca07c1235929c22ae6d4b02d95b7f2a9a17e3b0f` | 切れた | 51 |
| 139 | 乙 | acedjpsm | `755bdfb324647c34063dad374a4d386779a002242c1b2ac44e9cc7b7a6290646` | 切れた | 94 |
| 140 | 乙 | acedjpsm | `769e89ccaf82c63d9fac7dec1b8ec14991764c3745e9dc8c9e9b3a3ae44d55d8` | 切れた | 70 |
| 141 | 乙 | acedjpsm | `779215a3c1e496ba09abe812f40f3cf08a147a000f016c0d21eac029e263c71d` | 切れた | 95 |
| 142 | 乙 | acedjpsm | `78ac4b26820a90ebbcd596b5604a57b274b5e13931650c2b93ad63d39a56369c` | 切れた | 60 |
| 143 | 乙 | acedjpsm | `795a667c58ab892c1532aff5200334c75d4bce55dd719a8f4a0e44552792d6fc` | 切れた | 83 |
| 144 | 乙 | acedjpsm | `79a4e87b5d789d55d9e2a91e47fb9a1bac8a5a5aef9844d86df2c5aa0ed78f40` | 切れた | 86 |
| 145 | 乙 | acedjpsm | `79adfdc6a1481bc3b6f790e7a5e8e91409e190ebd4ecf6f526ac0db33a65f797` | 切れた | 46 |
| 146 | 乙 | acedjpsm | `7a85f9e8ad14a157f67a8281ef6f44001247746cfe9579d50b929d27b0ae35b4` | 切れた | 72 |
| 147 | 乙 | acedjpsm | `7abd4f8810e8d2edb75dda11ab2307cdc05ca31c40e506418a89bd86eccd00b7` | 切れた | 87 |
| 148 | 乙 | acedifsm | `7b4eb3e48254b228073bd71c4abdd86d0836289fd61810c0013399d30744344e` | 切れた | 70 |
| 149 | 乙 | acedjpsm | `7bc5fb8fe024b7433ba7ae3db324f6c1150970ec7169f026790108d9e67a3c2e` | 切れた | 111 |
| 150 | 乙 | acedjpsm | `7e6f2049c24f0b631fccab2cae95b2e57a596241ce1900cdd76ca3cdce90c906` | 切れた | 80 |
| 151 | 乙 | acedjpsm | `7fbf274feabf6c53423c16e4d3aaa1bbfe5c3188c65b8b107ce564885d5498d1` | 切れた | 69 |
| 152 | 乙 | acedjpsm | `80de1140d6e1ec540b18c2f193a732ad8363984b1dd544f4e814e29bdd4215d9` | 切れた | 40 |
| 153 | 乙 | acedjpsm | `81471e4cc979d23c8ec62fff0ea20664211c288b105a99bed017a73e3e186223` | 切れた | 121 |
| 154 | 乙 | acedjpsm | `81a38cbbec78e9e5e700db1159162ebd7dad4e8350519223040b49bb2bdc7ef3` | 切れた | 81 |
| 155 | 乙 | acedjpsm | `86cb1ab8c8ebd1e8e499153cb514e3ee710e68a6ff7a4649e82f7b8da13e8ce9` | 切れた | 50 |
| 156 | 乙 | acedjpsm | `87dafd3f9a5e5eb9f6f5fb2d041b2521ccd84d471bd282419565bd0842d84911` | 切れた | 86 |
| 157 | 乙 | acedjpsm | `8a97ca43a8a856c1f04f7fb8e945afd1b4abc136531efa626da98c93e059966e` | 切れた | 32 |
| 158 | 乙 | acedifsm | `8b34bf58fdb62cb7d962d50b9aae7542bab2aa1d08a46c430caa7fbca88e4293` | 切れた | 82 |
| 159 | 乙 | acedjpsm | `8bb013d01e8a1c0ca9382baa1f47955d35fd78dc1e52cc8c8df9ba15e737d212` | 切れた | 103 |
| 160 | 乙 | acedjpsm | `8bf59351032b3b461a8ebd19358173ee01b9fcd29722f89f49f8c4baccafa4a6` | 切れた | 58 |
| 161 | 乙 | acedjpsm | `8dde3ed6936da3db24662856b63af791766aeba5a05aaa0ec807494521dc5ef4` | 切れた | 71 |
| 162 | 乙 | acedifsm | `8e115552c3087e1d036ef587597a3deb65dc69b222adc750a5b941fa437edde1` | 切れた | 145 |
| 163 | 乙 | acedjpsm | `8f54dce05031b7e53b2f9d26b82c040dc72008a0afc9d79b3f70c4ffc094c09c` | 切れた | 87 |
| 164 | 乙 | acedjpsm | `908f551211f6bed2047a3b98819ff79dbd8a45e5cc65c5d3b4644b03e799666c` | 切れた | 48 |
| 165 | 乙 | acedjpsm | `9295be1a0f78d68f7ec462c25fd8319e2b3677f64aeb4f877f9cae753153d839` | 切れた | 62 |
| 166 | 乙 | acedjpsm | `950e20879428f65746a9d0f86c7db16d9d65b2b27e4699ea121b1c77dbf471f3` | 切れた | 99 |
| 167 | 乙 | acedjpsm | `95e4d4c6b365c9bf41354e7a663efda5d0f5123aa6ea2a2b5e65f7c52a6802cf` | 切れた | 59 |
| 168 | 乙 | acedjpsm | `9800334cab43ca02afa77b2f491bf0280a678c2c6a293dd642a2cbb981b2a8ba` | 切れた | 103 |
| 169 | 乙 | acedifsm | `9a13843caec668cae3c62f1b229c63e8681fb7533fc33c6c6c10e63d153df344` | 切れた | 90 |
| 170 | 乙 | acedifsm | `9b6c7a57ee97be417506f70962fbd2f3d240a83fc618fe9243d26ec505e373db` | 切れた | 34 |
| 171 | 乙 | acedjpsm | `9ccb573b40312b70256092b2f229a7dcd650f7b7376fde5904af10778af826a7` | 切れた | 75 |
| 172 | 乙 | acedifsm | `9d0d9dc223ea1d55ef2525892c32b2f2643ef71c7fd44d13ed9699c801e1dd9b` | 切れた | 11 |
| 173 | 乙 | acedjpsm | `9db47afbc1670e1ba4f9c1dc74a87fd1093beafd20e7de70af4ec7cf82079032` | 切れた | 76 |
| 174 | 乙 | acedjpsm | `9e03135b11b34d6d00b028e588458dcef908659896a96a2d7ec48e63d810677b` | 切れた | 68 |
| 175 | 乙 | acedifsm | `9fc6282778bec31b8e56a690f31a2089172d39573184f0511b732b9c95e93955` | 切れた | 81 |
| 176 | 乙 | acedjpsm | `9fe719131b587f5fb3eed6603ec58e7d309e792a54d0464b053bcba06263d22c` | 切れた | 59 |
| 177 | 乙 | acedifsm | `a0226008011c584e16e0a9ff8de50b091935c96781f5c6b65f40a1ad20f03bd5` | 切れない | - |
| 178 | 乙 | acedjpsm | `a0a1bdfbd4cb18cde9cc24f342c9b6a198f48593913913c436a69948716c4b69` | 切れた | 8 |
| 179 | 乙 | acedjpsm | `a2439206b492546f6c4a5ef5cca7e0450b372eec2c352146616d85ab07f04c6c` | 切れた | 94 |
| 180 | 乙 | acedifsm | `a4428e5ca25ab23ad126ff32fbfd1724ca0a51325e65c7f14dd85488d046dfdd` | 切れない | - |
| 181 | 乙 | acedifsm | `a464cf513a9c766afa6d08adb21a9710e3a7a7f9f3581993ef09726804c9022a` | 切れない | - |
| 182 | 乙 | acedifsm | `a53916a786865d3b4871d73e045045e65d5ab24964cb71c530dc0a2f1834c22d` | 切れた | 207 |
| 183 | 乙 | acedjpsm | `a7a64d255be53eb573d60509c835fabc29907df65b9e8436c384b0f7b9e607aa` | 切れた | 227 |
| 184 | 乙 | acedifsm | `a8f37c81ec86d035219bc3ee71db134dff839dbd0415b88ab2de2d80fc97e7b8` | 切れた | 6 |
| 185 | 乙 | acedjpsm | `abce5d2e463d99fe39cab832ef37a51ff71b25ea75f142516ac49bdca42df66a` | 切れた | 55 |
| 186 | 乙 | acedjpsm | `abe44647c7268e9c6b91abd77ea5e335f1aebec750af1df3647a9bd148cc99f8` | 切れた | 60 |
| 187 | 乙 | acedjpsm | `ac8a8b096021754c1790a1daf84fa592f4214f2b3b8e5597d12877c81abaeb56` | 切れた | 84 |
| 188 | 乙 | acedjpsm | `ad0679ea434e2341e692f58099deecdabcb06cc3ef32531794f1e4fc5586e81b` | 切れた | 74 |
| 189 | 乙 | acedifsm | `ae3d60a83832cd36bd16052ebe92d7b2d4a3c4c9d48d4a62824ab98874a22562` | 切れた | 47 |
| 190 | 乙 | acedjpsm | `aeb0dd6f9e16c00b5908f52a5d01c0127496ed1ac002e64e249edd45f6ef7e7f` | 切れた | 77 |
| 191 | 乙 | acedjpsm | `aeb98129fd4b2a5fc701abe08b97c349df2ca82acbd30b956c4c5ce56b04d37a` | 切れた | 49 |
| 192 | 乙 | acedjpsm | `af69c3c6f6346727c601cb124a15bcf967fcca05e2349654a0e120ff75271793` | 切れた | 82 |
| 193 | 乙 | acedifsm | `b26b6b517fd8006595900242616381c659d8d75c218052ea0b44438fbcb3797d` | 切れた | 122 |
| 194 | 乙 | acedjpsm | `b304ca3bb1772ef7106ed755b327a4b0d97baf0c02102180e3efc9caa99b22d2` | 切れた | 55 |
| 195 | 乙 | acedifsm | `b3e257c63978441b513e5037368943dda50b7d7b551de6eb720c7c3a9381694e` | 切れた | 82 |
| 196 | 乙 | acedjpsm | `b7999494c028bf932116d13a24c535eff0b49702566db7e4e8d1dd20d5edf720` | 切れない | - |
| 197 | 乙 | acedjpsm | `b84d43d3bf6a5ab45f6ae7ef3a6dfae56a01dd502d923ce996ca61548bceba91` | 切れた | 109 |
| 198 | 乙 | acedjpsm | `b90416e43d8007478435ea2b02f84bdd17f5630226604ddb8d2eeadbefba52de` | 切れた | 73 |
| 199 | 乙 | acedifsm | `ba884795a20b2c316cb0e87a75d2530412b641c1a3e32eb1592c27d90522f9bb` | 切れた | 65 |
| 200 | 乙 | acedifsm | `badb517f8e5c4e7aed9284a34a558cd8246a58f44a956acdb795e2237a1fb6ba` | 切れた | 62 |
| 201 | 乙 | acedjpsm | `bb0229fd39fff053ee5f357b274ab7db9fbbf2ec98835d9435b8b20727f8aaac` | 切れた | 63 |
| 202 | 乙 | acedjpsm | `bb44e35cf8b9c72d7c3947511953342648503df3a91dbc7302f68d4fb8082346` | 切れた | 84 |
| 203 | 乙 | acedjpsm | `bbb363f2a54ad37a17a69cc85fd14d940c523014d28ed06b35af4038e324df51` | 切れた | 27 |
| 204 | 乙 | acedjpsm | `c204a977704c60ebd9d7a8cf0264d41e89291f966bcd18c3d5472d2af9f08bd2` | 切れた | 71 |
| 205 | 乙 | acedjpsm | `c26d4112dccd53a0b6e15718a4253355e05fb179c6f624677c0a49fff087f81e` | 切れた | 60 |
| 206 | 乙 | acedjpsm | `c2faca9800d9fde24e0198612244030bc86c627792f67710b30a8b2ecdf86ac0` | 切れた | 59 |
| 207 | 乙 | acedjpsm | `c35e620808badafd8c6684f414173a0ad43f099a93b2cbd110d88d9d25ea4bbe` | 切れた | 87 |
| 208 | 乙 | acedjpsm | `c45eddd972219049f2e9131b6b1fd5bb4602aa42a1d23fcaf3191865db7563f9` | 切れた | 73 |
| 209 | 乙 | acedjpsm | `c5526cbed6c2e8c743ae6b0516d37d9db42efd3aead08f1ebe8f074984ba6545` | 切れた | 27 |
| 210 | 乙 | acedjpsm | `c69f5b0626d82094795adf64b4aa771af3e1c109203648289c717c8104524540` | 切れた | 69 |
| 211 | 乙 | acedjpsm | `c7773be6cdc5aa4120092ad356676954f29b3ac4c72a609be254d37578f8329b` | 切れた | 32 |
| 212 | 乙 | acedjpsm | `c8b840177dc32a3f5d25613ac62b95b362072e35aeb58bf24027c2aa6b9dd0ac` | 切れた | 54 |
| 213 | 乙 | acedjpsm | `cc4158fd6bd220dfa6bcb513d6b723829f1f3ff38a8127e2bdfb8054e71c92ee` | 切れた | 76 |
| 214 | 乙 | acedjpsm | `cc5bb432005ac4b8c3b158e834acb0582c531b5a85fed00f6232fffeb3117611` | 切れた | 132 |
| 215 | 乙 | acedifsm | `ce5f9f15e14f11feb857df2c74175dbd264cbbf1f2c43b2c1c7f729a43a0c251` | 切れた | 55 |
| 216 | 乙 | acedjpsm | `cfa9946d16375e4e96cecd69c5fb8f30343e842b303e38a908b15de09a6fc8be` | 切れた | 81 |
| 217 | 乙 | acedjpsm | `cfd6907902d151e10be354a95f2612e86caf5a07eb51f8c841c129760e962a45` | 切れた | 59 |
| 218 | 乙 | acedjpsm | `d1dc921403602e85781c775f077a9473f9b17fee1a525058c91ea7f7b2a765a3` | 切れた | 77 |
| 219 | 乙 | acedjpsm | `d3cabc2d1d6fcc3b962fc62d8a1a75c2cfb9601d1762c8ab1a163e01c63aaca2` | 切れた | 83 |
| 220 | 乙 | acedjpsm | `d60e61e71f16944ec92f2f1b39424076d7de61d511c0f05088a0af4ad078547b` | 切れた | 76 |
| 221 | 乙 | acedjpsm | `d859aa1211f39b36bc45c1a8a3a6637b2b20a5d17181e4c0eff85ce2d367fcf5` | 切れた | 67 |
| 222 | 乙 | acedjpsm | `d8beac4fd8d1818841218a297ad06a5d830a73ce2812a920fd52ab1a91bd0f30` | 切れない | - |
| 223 | 乙 | acedjpsm | `d9a8860fb5a338679fdc1a2b6abdc7cf3004330550b160594ace85fd4875ada5` | 切れた | 61 |
| 224 | 乙 | acedjpsm | `db0567c1c84deca13ae5963edcca3c5bd8de10433da3032a9f3682950ecf927a` | 切れた | 42 |
| 225 | 乙 | acedjpsm | `db2b4f9c1795f4eca68186450020ffdc933144c5c8fe5d02f7dee45ff104fc8e` | 切れた | 130 |
| 226 | 乙 | acedjpsm | `dc95fe7c48f5253d6ff083100759d3e733b555e89ed60f26273e7e2d1c66bf50` | 切れた | 131 |
| 227 | 乙 | acedjpsm | `dd3772830eeb5269179d8f66727a5a67d2626e639f7c122e05b5eebb9d7f7363` | 切れた | 62 |
| 228 | 乙 | acedjpsm | `de370948dc59947cd9d64d3c881241c52f75d9e0421e2f2c5dda40d4225e2635` | 切れた | 65 |
| 229 | 乙 | acedjpsm | `e02aa817f24676fce046f423ef8afbc811b4ad922cf6a5e2bbdf6341f1bb2674` | 切れた | 9 |
| 230 | 乙 | acedjpsm | `e11c13f45d43ded615ed41fa2c8ede611a37fd803cfec62f4da94b758056791e` | 切れた | 90 |
| 231 | 乙 | acedjpsm | `e3618788160fb7b339c0220b6cdd3705ef1f19876ae3d372886b8b4372425f3e` | 切れた | 37 |
| 232 | 乙 | acedjpsm | `e42eb302d79a048b965da55c3d2bb7bde97b6f5800064caf321158cb94ba708b` | 切れた | 75 |
| 233 | 乙 | acedjpsm | `e47626f7c72d19a1b81e8b6bedadd22082aa5ab86cc486bd356f79bd15d9d08e` | 切れた | 81 |
| 234 | 乙 | acedjpsm | `e4a719853d13e291668a73b0d2a5805b9d141e7b3ff99bc7abba31f0d060a4e9` | 切れた | 61 |
| 235 | 乙 | acedifsm | `e5dfdafd0910c112fb95dc94cb2e5ddaf1e6f048ddb6ea78b9c7e7c10466ee44` | 切れた | 109 |
| 236 | 乙 | acedifsm | `e6805aebdee16fde3c6b3a37362a88508fd577788b476e67be40720ee32529b0` | 切れた | 58 |
| 237 | 乙 | acedifsm | `e80e2a9d7eb8de2a22aa3d682080f25376e21ba227be69694bfb3f37c00fe8b7` | 切れた | 113 |
| 238 | 乙 | acedjpsm | `e81c15847446b22f6f89efc126164f7a5b22442077cc8dbcac489ecabbbb5d04` | 切れた | 115 |
| 239 | 乙 | acedjpsm | `e8a8d2f0cb2328004fa03ec45a1081f8ed58491c293253b6f04e61eac26f4288` | 切れた | 55 |
| 240 | 乙 | acedjpsm | `ee0f2e329005ef30482953b0b57257a56d40253268793c55cc418f947e2f0ac1` | 切れた | 60 |
| 241 | 乙 | acedjpsm | `f11395bbbae287f2cb2dcb023fb386a6c3e97941ca55f84f8c99ef0088a0528b` | 切れた | 76 |
| 242 | 乙 | acedjpsm | `f2958e99deb4502102941f9d07652af9411d0e837e72f363e1cfe1e74dce6b51` | 切れた | 49 |
| 243 | 乙 | acedifsm | `f3dee0ef931eadf2d798c8f6472586af64bf5fbc71450d2a61d462a54ea15a0c` | 切れた | 84 |
| 244 | 乙 | acedjpsm | `f49b62a8bfab5845b45eee7c314d6ae0963df2f4fcccef9ca6a95af15464822e` | 切れた | 93 |
| 245 | 乙 | acedjpsm | `f8363219978982bda2252989dea7ff9c8c4220d49e2b628d57844d5ac436aa6f` | 切れた | 79 |
| 246 | 乙 | acedjpsm | `f8e0b36e724269dfb214f96ee35ae4c7c72c9308c897c319d4619be13735d2c1` | 切れた | 42 |
| 247 | 乙 | acedjpsm | `f8f65bc732b1f45b23a538020df96b363a92610424c0b78a6c3c4e1a19b01d9d` | 切れた | 47 |
| 248 | 乙 | acedjpsm | `f97e15668fa0ebce9cc6aa2287043a28b7325d03b9c91a5111a7006c97f47b32` | 切れた | 75 |
| 249 | 乙 | acedjpsm | `f9d3e662dc97eefa026df0e315f21dbb92a9aff564b09368c2e26afa842ff380` | 切れた | 83 |
| 250 | 乙 | acedjpsm | `ff5b94e5a0fb6c4b89dc1aa9545b097a50a9cbd3e97f049bac660c3466f00780` | 切れた | 52 |
| 251 | 丙 | scedifsy | `046135b47292ae4ddf0b4093f7f2b0badbf1b57c9708e818e0fc390f8a1ee845` | 切れない | - |
| 252 | 丙 | scedjpsm | `0564dd6669fb286b21916c8a61b30efdb2507fad0a09ee80b973aa33650c818a` | 切れた | 0 |
| 253 | 丙 | scedjpsm | `058567a1a3180aef89f0287c2893234d9d6de1842483cedd59f00732d062d9e3` | 切れた | 21 |
| 254 | 丙 | scedjpsy | `061ffb10788cfb3fab9f68a7a0ba9b27808ef31019d5873d62dd39e682249f85` | 切れた | 27 |
| 255 | 丙 | scedjpsy | `06564497515b858cd9d909fbb1e509229e1a892dcb6ba26b59c11f8dbc610b42` | 切れない | - |
| 256 | 丙 | scedjpsy | `0733f344547b57913278ce990f494377e0396f126ff32b5896752a552d68b807` | 切れた | 57 |
| 257 | 丙 | scedifsy | `0a07f336b24a5bb0038aff32f6649f39c8e3e243fdbc931797346bd0f9121dcb` | 切れない | - |
| 258 | 丙 | scedifsy | `0a91886acd64757cb55a7a1536d5d25a8d1398a0565324765553b7048d9d32c2` | 切れた | 149 |
| 259 | 丙 | scedjpsy | `0ae30d2d8c7b6817c72223b57803131250567a3fe68d5e3c443c0c074d3665b9` | 切れた | 31 |
| 260 | 丙 | scedjpsy | `0bea51c74a0723d693b6985468cd164f33ba36c75a7c7fc6fd345e3b6b143fdb` | 切れた | 55 |
| 261 | 丙 | scedjpsy | `0d10376b7e4c43ee243710bf356ea29944c40c04fda7fdf5a771bf5fa032294f` | 切れた | 42 |
| 262 | 丙 | snedjpsy | `0e413e396144627b168e2f052b6e2bb75f1811ff4f8efff29561169f2c09285f` | 切れた | 10 |
| 263 | 丙 | scedjpsy | `10e4bec7c30a1a2addfa6ba573f4434e6650c03a68c39398cd60dcc82918f0e3` | 切れた | 41 |
| 264 | 丙 | scedifsy | `12f73b59bfbedcb8050810b568c1e5aced607215a1b2e4e23327ec6224edaaa6` | 切れた | 62 |
| 265 | 丙 | scedjpsy | `13db80d5180fb34f565cd71e6cb755856d30857b9cbdbc383e27ee34d98ce78b` | 切れた | 39 |
| 266 | 丙 | scedjpsy | `1466f034c3cf9bfd67f5d73380e078b69166653da8247cc503c6f5325b6a7971` | 切れた | 33 |
| 267 | 丙 | scedjpsy | `151711980d9791be4995c50dfea7fdee8ff399a6b6f1578560e9925c1662ee4c` | 切れた | 63 |
| 268 | 丙 | scedjpsy | `155fad77653b2741a317848d48cc6a0e71666731cbb2d7885e62f2a417d8090c` | 切れた | 62 |
| 269 | 丙 | scedjpsy | `18d8aa5cb0dbcee0d6c4c5a2178641aa356d08952deb1645619d094a67a489be` | 切れた | 29 |
| 270 | 丙 | scedjpsy | `1ce903ec2704dc3f9dbb4749f58f11bae64e3198cc0a68b1e17a9fc96162c842` | 切れた | 50 |
| 271 | 丙 | scedjpsy | `1eaf28fbb5ef8687b5d95545a396060fcee23af5bea45723c86c6c67356017c3` | 切れた | 39 |
| 272 | 丙 | scedifsy | `1f4df457fdf06314e8d17cf6f7e3158499193fc1cf2cc43cb7553337199f7cd0` | 切れた | 93 |
| 273 | 丙 | scedjpsy | `2018dc548babeacfe695bc6d635581152bfa6dcd70cead578f243a0541c35714` | 切れた | 95 |
| 274 | 丙 | scedjpsy | `21a261368034a5c40357902ffea85170b5d6c1e4192ea31787bd2683ac55f567` | 切れた | 0 |
| 275 | 丙 | scedifsy | `23d4041b3616dd558e88520aab5f20f52c482109d5149ea26c71cb4d3b86b282` | 切れた | 62 |
| 276 | 丙 | scedjpsy | `25885c7049ceeda84b95a6b562760cc7f701714e2fa23dcc58061aa0beb44bc0` | 切れた | 78 |
| 277 | 丙 | scedifsy | `27e69805543b72720e081549ced9e997a4c7f8ee177940c66976d67d3e2e5fb4` | 切れた | 33 |
| 278 | 丙 | snedjpsy | `29be876f7e72610401673140ae386b5ba8757367cbc83a95725e5d246404c5d4` | 切れた | 6 |
| 279 | 丙 | scedjpsy | `2a8f70a681dc1c0393fc3b646fe2d0dec83dfd5852609936f1e06c8e88e45410` | 切れた | 58 |
| 280 | 丙 | scedjpsy | `2e293df27057ec1606b5006dbe3ff89d4fefa96b72540a98e1afd4ec082880a8` | 切れた | 39 |
| 281 | 丙 | scedjpsy | `2f09c3fcd0fa6413c0287055827213831cca154fb81a919d08f6296245c0ed10` | 切れた | 129 |
| 282 | 丙 | scedjpsy | `2f215be0297e48eafd0a63190b3c28b4836df95cff6670edceba3c331c04a9ba` | 切れた | 42 |
| 283 | 丙 | scedifsy | `2f8a94b7d640b7fb8fcb571a320931358dd3f6c2d0a8b873274983741e7a3449` | 切れない | - |
| 284 | 丙 | scedjpsm | `30dec59e67a8bb49460ee12ff101fed816c7955daf07e7e74d189ccc3a5dfcfd` | 切れない | - |
| 285 | 丙 | scedjpsy | `31e5a9693769e6a1603a882813c6bcb8abc0d08d792a35da674622758bbe29ea` | 切れた | 6 |
| 286 | 丙 | scedjpsy | `379dbded2b718a1e1e846e81fd6f88614c128efa86bed83a044176a2d507f33f` | 切れた | 60 |
| 287 | 丙 | scedifsy | `3d010eb3eb80832108df320ab374a1495a7078140a051dfb2090b532bd5f7dd9` | 切れた | 41 |
| 288 | 丙 | scedjpsy | `401bf9346958bd50ba5404e1719ebf915363d31a7e9d3a475ba114c616d70bb0` | 切れない | - |
| 289 | 丙 | scedjpsm | `421f7a3742e1b85b5fc5d2879a69a10028b972e1845b2ec6adb6c64befd74759` | 切れた | 36 |
| 290 | 丙 | scedjpsy | `426cbda16173e85b4d79d8be283ed46741dfa9a4873943c2cec333d6f9114578` | 切れた | 30 |
| 291 | 丙 | scedjpsy | `473474788df4065e8744933d3fd125b58acd7a0c7e3316fda43fd79849c9a8b4` | 切れた | 41 |
| 292 | 丙 | scedjpsy | `483101ae6894b51b20ef681f09cd6d81bea4f2bbab4749c9fa503721b0620607` | 切れた | 68 |
| 293 | 丙 | scedifsy | `4a592249d3a63b05e256d35a69592a2cd5090fcbee379c0653fc0a988f29c409` | 切れない | - |
| 294 | 丙 | scedjpsy | `4cbeb84ba6273dd7e7999f2d235b3cc0ea79de297a1e6bd407c6947fd971ade9` | 切れた | 54 |
| 295 | 丙 | scedjpsy | `4cdc71cb7e80e8f29adadee4ced386ca413b8bab0ae45dd7fb15709396709f51` | 切れた | 33 |
| 296 | 丙 | snedjpsy | `4e3affe92c18b11cf6820b3a01050f80612ddbfdec11d69c42f1f64b1195d72e` | 切れた | 60 |
| 297 | 丙 | snedjpsy | `4e9e9695864c44cc2e1b75091fcde22c73582ab1851e153eb7736c228fed06ec` | 切れた | 75 |
| 298 | 丙 | scedjpsy | `4f79d75a5eee218f6619085a42b9c0cb9b84192fd6acb21f34763683c9a89a44` | 切れた | 56 |
| 299 | 丙 | scedjpsy | `4fbb3ed765f682a54126471aee45ae52b887d86ee2239b6ceeda22309951f5e1` | 切れた | 25 |
| 300 | 丙 | scedjpsy | `50131b1b0a35bcc1d7fd5a123ccc42d66feb8d42d8a0239a7a5358af472f5c6c` | 切れた | 42 |
| 301 | 丙 | scedjpsy | `50ef02b9ca4cc56c3f6668227613e4a1d211fc89f2b802fea6a875cee60342e5` | 切れた | 0 |
| 302 | 丙 | scedjpsy | `5227de272b1183628c51a62e44ff484674ff4e64e71e93b72a1bd84e7818a107` | 切れた | 58 |
| 303 | 丙 | scedjpsy | `588ea4ba2a2e0f8208c91ed7768163770489fbb8dda1cdded3537beeabdb94f2` | 切れた | 77 |
| 304 | 丙 | scedjpsy | `59ef786935d2c9c52c71dd1ee868bbcaca7e7c6d1f207ca97e779a7e4f32605a` | 切れた | 34 |
| 305 | 丙 | scedjpsy | `5cdd301bb2f16c3e3595df8f46b76aed2bd982aa5b7bdb1f8a32292a47ff4b29` | 切れた | 58 |
| 306 | 丙 | scedjpsy | `5e6b6b2ff75401cd9fadb9f0dd3fb5b17c641039396524d9955371c1db0cf19f` | 切れた | 75 |
| 307 | 丙 | scedjpsy | `5e865499f1d7ed457ca8f29c81b59a8daa1c91e2ff0c8996f219c850f3a4a82a` | 切れた | 47 |
| 308 | 丙 | scedjpsy | `5eb3554de4872f5fd19db0eb67e01f9a673f5e411eb2a0df3e8026a3dfbf3e87` | 切れた | 56 |
| 309 | 丙 | scedjpsy | `61ae9ed0328c37a7068b3227c4da86ed8d42f689a225c312cdf2a6059c70906a` | 切れた | 70 |
| 310 | 丙 | scedjpsy | `6d1e8b9a2cb737cbaeb62f9d8722b17bcdd058b2473fad0c4cd363363e49aa9c` | 切れた | 64 |
| 311 | 丙 | scedjpsy | `6fd7d6992654a91ff3ac12fe87695436e28be5b839249d2f4ad33da5514fe0d2` | 切れた | 44 |
| 312 | 丙 | scedifsy | `70cc0f3683bd0c3cb33ea3004558c28d8c8112875f6071bae879080d6a15bf63` | 切れた | 50 |
| 313 | 丙 | scedjpsy | `7154b549fc3a3f321afab80b1bbea9c81b881265d6658a597d24258bd3697e98` | 切れた | 54 |
| 314 | 丙 | scedjpsy | `73fed16e88376147307d9653435d02d0c7a22382c306a75c0e1a8166bdca3867` | 切れた | 94 |
| 315 | 丙 | scedjpsy | `77fd5bb96afb8e420f68ba263d6e3c2f955cbec6a889d90cedd2b98b14095153` | 切れた | 11 |
| 316 | 丙 | scedjpsy | `7ab1a5147481534cf38264a597df345c0f4c56f4cabf29b3aa1bcab0ca630a29` | 切れた | 59 |
| 317 | 丙 | scedjpsy | `7b795d814a8b1bd777c9e58670dd39f05a8dfd44cc657ff67579def18287de20` | 切れた | 49 |
| 318 | 丙 | scedifsy | `7d202c61662448184c83b95854e4dd6a3ede6bda4575533bed95e05db230b56e` | 切れた | 12 |
| 319 | 丙 | scedifsy | `80a508767368d94cb7684400c4bd214702c70f5bfb156125dea6a2de76d5b962` | 切れた | 69 |
| 320 | 丙 | scedifsy | `8137d45f63be95c7b853d5e1449d98bab8a36d62381dcd63989b42f74a592c73` | 切れない | - |
| 321 | 丙 | scedifsy | `8171ac75ba0e232446e209ef9d47f3dbb89d5b572282eba86f147de4c4a2fec1` | 切れた | 29 |
| 322 | 丙 | scedjpsy | `83ef41c1ecfb1ab18cfdc6928d7f925f607cac1bfa4c96113905866a7ce4e834` | 切れない | - |
| 323 | 丙 | scedjpsy | `86742e13af9cf4befb52614e5947686e01577a29ea3ecd2ecbf45d16fd24ad94` | 切れた | 70 |
| 324 | 丙 | scedjpsy | `86f8815f166e384b22a84531b52039a67be2753dd7ce108aae6f92e445f3dfb9` | 切れない | - |
| 325 | 丙 | scedjpsy | `872201509e9535d74851514f4d77731ba2e023e0a363516f919fd7e81df052f2` | 切れた | 9 |
| 326 | 丙 | scedjpsy | `88533c5afc3ffa75ddff03edd69d636c75dcdd22b65a5a832ecb083b1b524386` | 切れた | 67 |
| 327 | 丙 | scedjpsy | `889d157fc860215992de3034d9067908995aead90ec57abc7178c83fd85bc591` | 切れた | 39 |
| 328 | 丙 | scedjpsy | `8d56fd295ff7face4208b448b07abccf6f77da4241a1ba34573771a0b5d42cbe` | 切れた | 72 |
| 329 | 丙 | scedifsy | `8dfe0feb08c9a94359a0a3df75cfac588f25ff943d3dbebbf089d6ec9d63a8b8` | 切れた | 0 |
| 330 | 丙 | scedifsy | `910ab16b22d466594a5ec8558e4cfbe028ff5ff7a5f9a56ffcb198cb5628a81d` | 切れた | 69 |
| 331 | 丙 | scedjpsy | `93294383e45107c4836a3c8aec2ed753e6c793963a6bf880a5e4e952b6d2888c` | 切れた | 54 |
| 332 | 丙 | scedjpsy | `9741623158d1f4d02fda6244912283ce6b5e8abd3ec1f47fd43945539c9121e0` | 切れた | 51 |
| 333 | 丙 | scedjpsm | `986249450a6a1edad3d259c0b20b9f2b699cf9625d3fc9d9f043b08ec43f872f` | 切れた | 21 |
| 334 | 丙 | scedjpsy | `99781a6fbcd0e767b44f2061505ec8d4f7e9aac8c3449f28faa613d1e69cfcd7` | 切れた | 31 |
| 335 | 丙 | scedjpsy | `99c69c689464c22364ea0fdb75a2f0aab873009ce59e028a0e298de3f262740a` | 切れた | 40 |
| 336 | 丙 | scedjpsy | `9af3341a3b993f87f4a949e196ee47f5a246ecef550a8c7e319f81e8b8e14f68` | 切れた | 35 |
| 337 | 丙 | scedjpsy | `9c6cdf66b8a1f56efb874a0f6d72aec16d0ab53782c143649a6ff57698212f03` | 切れた | 75 |
| 338 | 丙 | scedjpsm | `9dfd6bbb4dc5a17b19fc857a1c6b53779c93a90f4b2df74a41dab004827e5f7e` | 切れた | 15 |
| 339 | 丙 | scedjpsy | `a07da01fa6e620affe26cb39147254d226b3662074046ecf928cf8233ef69152` | 切れた | 80 |
| 340 | 丙 | scedjpsy | `a2d369e0d6615f3c86d95f439a74bac72d19ce0eb712ee4d4fb1ced06325a3f4` | 切れた | 62 |
| 341 | 丙 | scedjpsy | `a2dbf3762d464afe41da8534f327683322b2f8e9c4d2434664f62d5f95abe3e7` | 切れた | 72 |
| 342 | 丙 | scedjpsy | `a58a9c4cc902f9e7c2971e78b08a84c2fa46f52c287b610cb6916bcf6a33bff8` | 切れた | 57 |
| 343 | 丙 | scedjpsy | `a8ab96bec53bc7582e51309c6011b8d693d9787b7adf7c02d5803434cfa5bc8f` | 切れた | 91 |
| 344 | 丙 | scedjpsy | `a8b120f56eef480aa4c300b8f52888fd64af279fde64118bcf97737c6dbdf76a` | 切れた | 56 |
| 345 | 丙 | scedjpsy | `a92e24f15612444af2ccf0297f67ddfa28a385eb478e96211166967d92297db6` | 切れた | 96 |
| 346 | 丙 | scedifsy | `ab01183ea5a0f66c11f07fcc6c0d1b8d6fafc5fdcfa423a220f2da5a3bd876e8` | 切れた | 15 |
| 347 | 丙 | scedjpsy | `ac08041a1758d0c18fd3f77d27e35bb80e742e8e782f433c2f85892a874e1cc1` | 切れた | 85 |
| 348 | 丙 | scedjpsy | `adee37f1b70f362db1b0f34ea720676c84e775436fca90de5d6da43502ce61be` | 切れた | 43 |
| 349 | 丙 | scedjpsy | `adf13df40177e61f7397864f545ee8b27039f82051b53ccc09235fccd818ed18` | 切れた | 41 |
| 350 | 丙 | scedjpsy | `ae2b7fc10beb3dc3697cf37a62a664725ddee01c711d64dcb65e48918c342fc2` | 切れない | - |
| 351 | 丙 | scedjpsy | `aee2601c5bdd7c128ca4d513fba1d2a284fe6652e9ef5eaf51362b0b25d2ac84` | 切れた | 61 |
| 352 | 丙 | scedjpsy | `b22de798247bb774fae39f9ce543ebc863fc47545bed9bd1d6669d1badd659cd` | 切れた | 38 |
| 353 | 丙 | scedifsy | `b62b5276936e86b6947e9ae2a207910a6461cfd9919ac489e3438cbbaeefbd8d` | 切れた | 75 |
| 354 | 丙 | scedjpsy | `b89f1796641140b36a191990d48b1460bbddb37a2b1faad0afdf9758dbd047fa` | 切れた | 61 |
| 355 | 丙 | scedjpsy | `b9296fa9780cda1e6b1e3793f5dd6c6c20cf95ca3bb1b9aeccb7fe4695f36d90` | 切れた | 69 |
| 356 | 丙 | scedjpsy | `b9dc0f8a8b8eaa60b8779cd22eefcf370586fbb5e573dbdc619b828c0ef4db43` | 切れた | 84 |
| 357 | 丙 | scedifsy | `bb4c3fb64b21bcd11aff3b5319565ec8c4273024123df78780083dcd16176ae1` | 切れた | 103 |
| 358 | 丙 | scedifsy | `bc2b9bc98018b68146d0bd3e85f61c1018365937fade84c304dcb21ede7eeb0c` | 切れない | - |
| 359 | 丙 | scedjpsy | `bdcb3d004bc449372f624371aae42d7e19b8f36f25b7c439561860d02e45b70d` | 切れた | 71 |
| 360 | 丙 | scedjpsy | `bdead17f865241774c4a6cfb90570083b1c9fd4dd246d4979342647ae54cf9fa` | 切れた | 64 |
| 361 | 丙 | scedjpsy | `c1689daa19fa045ba6ffd61d32a6e11f6b98d90545ec444298816f940bbe0ad7` | 切れない | - |
| 362 | 丙 | scedjpsy | `c1fcac28c2e6b9f3931a1f19d7401ebbdcaf2ffccd7aac4976e3a9bae2952e88` | 切れた | 50 |
| 363 | 丙 | scedjpsy | `c20173ccb718973cf7b30c036b63c524da3c4430951d059f7d7de086cdf7a0b1` | 切れた | 64 |
| 364 | 丙 | scedjpsy | `c2638ea198fbaf58d96d0f7e8067dfdd6966ec3b7ce999f4436171c943e32c35` | 切れた | 75 |
| 365 | 丙 | scedjpsy | `c3f4f2c3cd50c1c42651bf053234ac0ad252c875fdddaca158e99c0892e5362d` | 切れた | 45 |
| 366 | 丙 | scedjpsy | `c4464690c09357b8f2278bdafc8c0deb8cc6f4d08bb189e9e7f4937272592a6e` | 切れた | 46 |
| 367 | 丙 | scedjpsy | `c5600b612b6ed96a95284ab40fc0a7dceba7a9b6305c88e654225cc262bfef25` | 切れた | 66 |
| 368 | 丙 | scedifsy | `c88e1cf8417ffb29e35142c3e4a3deeb5877131839e8724503a5f8a8e6c801ad` | 切れた | 87 |
| 369 | 丙 | scedjpsy | `cb84e7663ef1dfc9682bd02af43b52e63b18c8a97474e21ad28dee0fdbee8d86` | 切れた | 108 |
| 370 | 丙 | scedjpsy | `cbbe542d45610bdbfa35f42e6fc882ba0d20053fc12b07ef0d6dfc19d2c993e3` | 切れない | - |
| 371 | 丙 | scedifsy | `d231be3ed6b7d2817e3d7beb67f564fda8afd7f059c96d97d127a8598f95b1d5` | 切れた | 33 |
| 372 | 丙 | scedifsy | `d43c8acca8297f8ff439727c69e884c2ee188cd3be081984e4be712b3f1ff34b` | 切れた | 69 |
| 373 | 丙 | scedjpsy | `d5af1533582905ae376cb11fdb766efc88fc974f725c8ab750b875f7e204acf8` | 切れた | 79 |
| 374 | 丙 | scedifsy | `d5b172b0d8db4958336b9b6e4a043ed453e7b0004fa12f00368208c511f6348d` | 切れた | 63 |
| 375 | 丙 | scedjpsy | `d7121c75fa8815e15fb91a6d2ded266f63ee12ef57e94cfbdd979c2864b4da47` | 切れた | 42 |
| 376 | 丙 | scedjpsy | `d8a0b95f386d164e4b83be5007280bdeb75fc622efe50880aa468a97c5abb674` | 切れた | 44 |
| 377 | 丙 | scedjpsy | `d8ab3e91fa3e5611ee9e511d5395b21fc38d59d7e3897a58b8a0883dee974c6e` | 切れない | - |
| 378 | 丙 | scedjpsy | `da4b9b8f04e79577269e9409b1b102cd85ef52d084405e148b7209ec1fee9f26` | 切れた | 37 |
| 379 | 丙 | scedjpsy | `daa9f10283ceba54153e9f3bf2689993b9f616d93e25c8df976ed08ec04bbe85` | 切れた | 41 |
| 380 | 丙 | scedjpsy | `dd1f71f561ec6869040a9f8af8f8ddbcb1b044d58caecd02b80d48f8809aa26d` | 切れた | 0 |
| 381 | 丙 | scedjpsy | `df5dd2609e2a97009a6c8e4341fa42615011388a66b149ca13f31eb3087d2119` | 切れた | 49 |
| 382 | 丙 | scedjpsy | `dfad637babb196a7f5a1fde5bfb044fee9d7630b3aedcf906ec101cfdd629da5` | 切れた | 37 |
| 383 | 丙 | scedjpsy | `e112328ac2296818320cd3cdfb23d62bfd6cc23ec7768cb87b7a2c22e2e51177` | 切れた | 62 |
| 384 | 丙 | scedjpsy | `e4e068656475a746412fa35de39d363b83d1fdddbbb23d4e542dbe9d68f65e93` | 切れた | 59 |
| 385 | 丙 | scedifsy | `e9a2b23b9ceaf7bceb65c67b5e5f72851c671540f76b6edf536da3dee7ec62fa` | 切れた | 51 |
| 386 | 丙 | scedifsy | `eb374b40ff8a205d3d0339f11d676a11abf0655a746dfb901202aaf8048f3d35` | 切れた | 31 |
| 387 | 丙 | scedjpsy | `ec38c325b0bbed895d30196d3105945aebb56746b0c78d2e42ed519d70417cf6` | 切れた | 34 |
| 388 | 丙 | scedjpsy | `ed6caec3856539eb4b383c4f412d959d581a9e704ca9a5dc19a2c57efb15a824` | 切れた | 46 |
| 389 | 丙 | scedjpsy | `f1cde0d60ef728827730954608e16998bac4df9d63c8e14f02f53942abd693dd` | 切れた | 37 |
| 390 | 丙 | scedifsy | `f22d74a17cbcf88ea51d9a4c0968d9587e52141cc0867bca97e8839297b44c2e` | 切れた | 0 |
| 391 | 丙 | scedjpsy | `f41e304c37c2df67e72e9fe0ac8c5c018952d6f4a0bbd77845f5c0df197db398` | 切れない | - |
| 392 | 丙 | scedjpsy | `f5164a649ccb75395b83558963ac6ce96066d91d6fb67a63906fcc9f9cf77987` | 切れた | 44 |
| 393 | 丙 | scedjpsy | `f655641b9f7ac54d7095769c73260dc2841250f39e4b07a17f7a0cfc362fc61f` | 切れた | 62 |
| 394 | 丙 | scedjpsy | `f802bef5bf33ef5e22230e71e557b8c0b75f308f65e1ec2b7b2e06db7aabc5ce` | 切れた | 46 |
| 395 | 丙 | scedjpsy | `f879ae30762c37eb0b9a4362c20c60867317059708b646034977a0532f377442` | 切れた | 68 |
| 396 | 丙 | scedjpsy | `f9cafde05a0a8be5dba16753fe41f0e2ae0b7e792d89ca00bf20adce4e35871a` | 切れた | 68 |
| 397 | 丙 | scedifsy | `fac2d1f6fe1ecca1d6648e0fb46ca954922fd4d138d3157696e53ec177022484` | 切れない | - |
| 398 | 丙 | scedjpsy | `fba4d1d2da9cf75c5eeca7fff533f7c952fdc3cb05b3a7c54954c3798737be8c` | 切れた | 43 |
| 399 | 丙 | scedjpsy | `fcf6b56bc6771eaa26bd72f3f835423315747dcf774cc77f07e233c227d9c329` | 切れた | 76 |
| 400 | 丙 | scedjpsm | `ff6f7fe8e5e5092221083af136664f3de3fd5b615b201e88964fff5f6f26aa39` | 切れた | 18 |

## §2 測るもの(全部 0 USD。engine は 0 行)

1. **置く**: §0-2 の 6 のとおり 400 本を写し、`fixtures/xbrl/tanshin_self/population_2026-11-14.json` に 400 行(#・群・様式の種類・sha256・byte 数)。
2. **判定**: 400 本を §0-2 の 3・4 のとおり切り出し・包み直し・P33E で判定する。記録 `fixtures/xbrl/tanshin_self/states_2026-11-14.json`: 本ごとに(#・切り出しの結果(切れた / 切れない + 理由)・見出しの番号(0 = 経営成績等の概況、1 = 当中間決算に関する定性的情報、2 = 当四半期決算に関する定性的情報)・字数・入れた iXBRL の file の数・fact の数・行)。行の欄は 2026-11-09 の短信の便と同じ `[文の番号, 位置, state, reason, pointer の期, formula の有無, 単位の族, 両期の fact を引く a−b, span に % を含む]`。集計(群ごと・様式ごとの 4 state、reason の内訳、VALUE_MISMATCH の機械の内訳)は行から数える。かかった時間(秒)も記録する(予測は置かない)。
3. **2 回走らせて記録が byte で同じ**(時間の欄を除く)。
4. **「値が違う」の標本 120 行の型分け**(§0-2 の 7)。記録 `fixtures/xbrl/tanshin_self/vm_types_2026-11-14.json`: 120 行(標本の番号・本の #・文の番号・位置・型)と、付けたのが司令塔(AI の席)であること。
5. **結果の文書** `docs/XBRL_TANSHIN_SELF_RESULT_2026-11-14.md`: 表は記録から 1 つずつ読んで書く。予測の当たり・外れを欄ごとに。
6. **門** `tests/measure/test_xbrl_tanshin_self_seal.py`・`tests/measure/test_xbrl_tanshin_self_result.py`: §1 の表の 400 行と記録の一致・封の commit が script と記録より先(commit の順で)・engine(`core/`・`adapters/`)が封の時点から 0 行・集計を行から数え直す・標本の 120 行が規則どおりに引かれている・記録に文も会社名も証券コードも無い・結果の文書の数が記録と同じ。**門は変異で赤くなることを確かめてから門と呼ぶ。** 門は追跡されている記録だけを読む(cache の材料が無い機械でも動く)。材料から測り直す試験は環境変数でだけ走る別の試験にする。

## §3 事前予測(**測定の script より先に固定。結果を見てから書き換えない**)

S-1〜S-6 は下調べの数をそのまま置いた = 当たりは「下調べと本物が同じ」の確認で、外れるとすれば実装の違い。**S-7〜S-10 は測っていない本当の予測。**

| # | 欄 | 予測 | 外れ方 |
|---|---|---|---|
| S-1 | 置く: 400 本の sha256 が §1 の表と一致。ほかの cache の一覧の sha256 が前後で同じ | 400 / 400・同じ | 1 本でも違う = 止める |
| S-2 | 切り出し: A の 切れた / 切れない、B の 切れた / 切れない。切れない理由 | A 239 / 11、B 133 / 17。28 本とも「始まりなし」 | 1 でも違う |
| S-3 | 概況の字数の合計: A、B | 1,204,375、445,473 | 1 でも違う |
| S-4 | A の数の claim と 4 state(GROUNDED / VALUE_MISMATCH / UNVERIFIABLE / POINTER_NOT_FOUND) | 17,697 = 5,405 / 1,898 / 3,980 / 6,414 | 1 でも違う |
| S-5 | B の数の claim と 4 state | 6,834 = 1,229 / 0 / 855 / 4,750 | 1 でも違う。B の VALUE_MISMATCH が 1 以上 = 中間の期の読みについての §0-1 の 7 の説明が崩れる |
| S-6 | A の VALUE_MISMATCH のうち span に % を含む行 / 導出(formula)の行。A で VALUE_MISMATCH が 1 以上の本 | 1,273 / 425。220 本 | 1 でも違う |
| S-7 | 2 回走らせた記録(時間の欄を除く) | byte で同じ | 違う = 並列か辞書の順が結果を動かしている |
| S-8 | 標本 120 行の型: (ア) + (イ) の行の数 | 66〜102 行(55〜85%) | 幅の外。66 未満 = 「値が違う」の主な中身は部分と全体の取り違えではない |
| S-9 | 標本 120 行の型: (ク) 本当の差の候補 の行の数 | 0〜4 行 | 5 行以上 = 文と同じ短信の表の数の違いが、司令塔の見立てより多い(候補。紙面では確かめていない) |
| S-10 | 標本 120 行の型: (ケ) 読んでも分けられない の行の数 | 0〜12 行 | 13 行以上 = 読むための紙が足りない(型分けの数を弱く読む) |

封の席の偏り: S-8 は 2026-11-09 の短信の便(有報と比べた 110 行で セグメント 39 + 内訳・部分・派生 32 = 64.5%)から置いた。こんどは出どころが同じ短信の表なので、有報との時点の差・訂正の差は無いはずで、(ク) は前の便(110 行のうち 4)より少ないほうへ置いた。外れが (ク) の多いほうへ出たら、「同じ文書の中なら差は無いはず」という見立ての偏り。

## §4 結果の扱い

採用 / 不採用の判定は無い(engine を変えない便)。結果は全部そのまま台帳(FACTS)の行と README の「測った事実」にする。負けた数(GROUNDED が claim の約 3 割・切れない 28 本・中間で「値が違う」が 0)も同じ場所に書く。2026-11-09 の短信の便(17 社・出どころは有報)の数とは**並べて書き、足さない**(出どころが違う)。外に出す紙に写すのは、結果の文書が監査を通ったあと。

## §5 測り方と順序

1. この封を commit する(文書だけ)。
2. 実装の席(`step-implementer`)が worktree で script(`measure/xbrl_tanshin_self_stage_2026-11-14.py`・`measure/xbrl_tanshin_self_2026-11-14.py`)と門を書く。新しい file は NF・LB の封の門の `DECLARED_NEW_AFTER_SEAL` に日付つきで届ける。試験 file を足したら `measure/suite_coverage_2026-10-16.py --write` と台帳の試験の数。
3. 独立監査(`step-auditor`)の GO → script と門を commit。
4. 置く → 判定 2 回 → 記録。司令塔が標本 120 行を読んで型を付ける → 記録。
5. 結果の文書 → 独立監査の GO → commit。台帳・README はその後。

## §6 限界(先に書く)

- 母集団は英文短信を出している会社から引いた 400 本で、上場会社全体の標本ではない。率を一般化しない。
- 切れない 28 本は測れていない(見出しの書き方の違い)。規則を広げるのは別の封。
- 中間(B)は engine が期を読めないので、「値が違う」が出ない。B の数は限界の記録で、成績ではない。
- 文と表が同じ誤りを共有していれば、この照合では見えない(同じ文書の中の照合)。
- engine が見るのは添付の財務諸表の fact だけ。サマリーの数(予想・配当など)は入れていないので、文がそれを言うと止まるか「見つからない」になる。
- 型分けは司令塔(AI の席)が封の予測を知ったうえで付ける(盲検ではない)。人は読んでいない。(ク) は候補で、紙面で確かめていない。
- 注入をしていないので、「誤りを通す率」はこの便では言えない。
- NFKC を掛けた文を測っている(原文の全角・半角の違いは見ていない)。
