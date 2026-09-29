# 席 B2(GPT/ChatGPT)の回答 ― 実験 2: 棋譜の流れから戦型を認識できるか(原文のまま)

**出どころ**: 人間が ChatGPT の会話に `scripts/playtest/out/c5/experiment-llm-25/request2.md`(sha256 `ea0f55072ef6c1e0a888f46898223da1df7757dd074224ea2c0fcb148e091da9`)を本文貼り付けで渡し、回答を一字も変えずに保存したもの(2026-09-29)。原本 `seat_B2_gpt_raw.md`、sha256 `f21ef9f4980021b5cf8350070f503d2987d5a38bca25cb19f88aa61b5c290cfb`(141 行・13,971 バイト)。下の区切り線から先が原文で、語も書式も変えていない。

**注(司令塔の中継)**: 1 行目「2m 38s考えました」は ChatGPT の画面の思考時間の表示、最終行「gpt」は人間が貼るときに付けた席の印で、回答の本文ではない。表はタブ区切りで貼られた(Markdown の罫線なし)。**独立性に疑いあり**: 2 段落目に「本編・『数の出どころ』付録も確認しましたが」とあり、request2.md には本編も付録も無いため、席 B2 の会話には現行ルートの出力(2 周目の冊子)が見えていた可能性がある(新規会話だったか・PDF を添付していたかを人間に確認中)。**人間の決定(2026-09-29 昼)**: 独立性に疑いありの扱いを確定。表と定義構造への指摘は保存するが、独立実験の比較対象としての GPT は**保留**(突き合わせの表では B2 の列を「保留」と印し、3 席一致の数には入れない)。本人が「新規会話・添付なし」と確認しても、なぜその文が出たかは別途の確認対象。

**この文書の扱い**: 実験 2(指示書 §13、H7「棋譜の流れから戦型を認識できるか」)の席の回答。発見レイヤー(顧客向け文章ではない)。「一致した定義」の id は data/ の下書き定義(すべて draft)であり、顧客の文には出さない。「定義に無い名前の候補」の欄は分類・比較に使わず、知識レーン向けの材料として司令塔経由で別に渡す。突き合わせ(席 vs 機械の rows)は LOG §6 に書く。

---

2m 38s考えました

読みました。request2.md の指示を基準に、25局×本人/相手＝50行として照合しました。
本編・「数の出どころ」付録も確認しましたが、今回のH7の分類材料そのものは request2.md にある25局の指し手列と114件の戦型定義です。本編・付録は、25局の形勢や分かれ道を扱う別レイヤーで、エンジン候補を「正解」とは扱わない構成になっています。 

また、request の指定どおり、

後手の本人は180度回転して定義と照合

表に書く手数・USIは元棋譜のまま

recognition_pattern の駒→toを順番どおり照合

pattern全部なら「完全」、一部なら「部分」

定義にない名前は分類に使わない


としました。定義114件はすべて draft です。

重要な結果

この照合をそのまま行うと、かなり強い「一意分類不能」が出ます。

特に1手だけの pattern が34件、2手が37件で、例えば「歩→4d」のような1手patternは、別の戦型の途中にも普通に現れます。したがって、「完全一致＝その戦型だった」とは扱えません。
request自身が「patternが浅いために一致してしまう場合」を認めているのも、この問題に対応するためです。

以下では、完全一致したIDをすべて出し、根拠となった手順も併記します。
「定義に無い名前の候補」は、この段階では勝手に命名せず — としています。

局	側	一致した定義(id)	根拠となる手順(手数とUSI)	一致	未認識部分	定義に無い名前の候補

1	本人	chousoku_37gin, douke_yagura, kakutoufu, migigyoku, onikoroshi, ufo_gin, yagura_37gin	chousoku_37gin: 83手4f3g・89手S*4f / douke_yagura: 19手4h4g・35手2i3g / kakutoufu: 25手8g8f / migigyoku: 39手5i4h / onikoroshi: 7手7g7f・69手8i7g / ufo_gin: 53手4g3f / yagura_37gin: 83手4f3g	完全	後半で成立するpatternを含む	—
1	相手	rokusuji_kuraidori, yokofudori_44kaku, yokofudori_45kaku, yonyonfu_pacman	rokusuji_kuraidori/yonyonfu_pacman: 38手4c4d / yokofudori_44kaku: 76手8d4d / yokofudori_45kaku: 78手4d4e	完全	1手patternによる重複	—
2	本人	douke_yagura, kintachi, koshikakegin, migigyoku, ponpon_kei	9手4h4g・13手2i3g / 19手6i5h・75手5h5g / 23手4g5f / 17手5i4h / 13手2i3g・49手3g4e	完全	kintachi等はpatternの一部がかなり後半	—
2	相手	rokusuji_kuraidori, yonyonfu_pacman	32手4c4d	完全	同一1手pattern	—
3	本人	koshikakegin, migigyoku	57手S*5f / 19手5i4h	完全	57手目の一致は序盤から離れる	—
3	相手	direct_mukaibisha, mukaibisha_opponent, rokusuji_kuraidori, yokofudori_33kei, yokofudori_45kaku, yonyonfu_pacman	26手3c2b / 16手4c4d / 32手2a3c / 54手4b4e	完全	1手patternが複数成立	—
4	本人	kakutoufu, koshikakegin, migigyoku	35手8g8f / 17手5g5f / 19手5i4h	完全	—	—
4	相手	—	該当patternなし	なし	手順にあるが定義patternとして拾えない	—
5	本人	kamereon_senpo, koshikakegin, migigyoku, onikoroshi, ponpon_kei	33手6h6g・45手6f6e / 47手6g5f / 21手5i4h / 25手7g7f・31手8i7g / 11手2i3g・51手3g4e	完全	—	—
5	相手	rokusuji_kuraidori, yonenaga_kyusen_yagura, yonyonfu_pacman	8手4c4d / 26手6c6d・36手8a7c	完全	1手patternと2手patternが併存	—
6	本人	gangi_senpou, kamereon_senpo, kintachi, koshikakegin, migigyoku, onikoroshi	8手4b4c・86手4b5c / 8手4b4c・30手4d4e / 20手4a5b・74手5d5c / 36手4c5d / 14手5a6b / 2手3c3d・34手2a3c	完全	複数patternが同時成立	—
6	相手	ai_yokofudori, shikenbisha_opponent, yokofudori_33kei, yokofudori_85hi	77手2e3d / 29手7g6h / 41手8i7g / 71手1d2e	完全	いずれも1手pattern	—
7	本人	douke_yagura, kamereon_senpo, migigyoku, onikoroshi	11手4h4g・17手2i3g / 37手7h6g・43手6f6e / 21手5i4h / 5手7g7f・31手8i7g	完全	—	—
7	相手	rokusuji_kuraidori, shikenbisha_opponent, yonyonfu_pacman	6手4c4d / 30手3c4b	完全	1手patternの重複	—
8	本人	hikikaku, koshikakegin, migigyoku, onikoroshi, ponpon_kei, torisashi	43手2i7i / 97手6e5f / 21手5i4h / 25手7g7f・29手8i7g / 11手2i3g・67手3g4e	完全	hikikaku/torisashiは同一1手pattern	—
8	相手	rokusuji_kuraidori, yonenaga_kyusen_yagura, yonyonfu_pacman	6手4c4d / 24手6c6d・56手8a7c	完全	—	—
9	本人	yagura_senpo	9手7g7f・13手7i6h・29手6h7g	完全	—	—
9	相手	rokusuji_kuraidori, yonyonfu_pacman	28手4c4d	完全	同一1手pattern	—
10	本人	mukaibisha	45手7g8h	完全	45手目のみで成立	—
10	相手	rokusuji_kuraidori, yokofudori_33kei, yonyonfu_pacman	38手4c4d / 52手2a3c	完全	—	—
11	本人	migigyoku, onikoroshi	20手5a6b / 26手3c3d・28手2a3c	完全	—	—
11	相手	direct_mukaibisha, mukaibisha_opponent, rokusuji_kuraidori, yokofudori_44kaku, yonenaga_kyusen_yagura, yonyonfu_pacman	45手5e8h / 3手6g6f / 69手6h6f / 19手4g4f・27手2i3g	完全	同じ1手patternが複数	—
12	本人	kamereon_senpo, koshikakegin, migigyoku, onikoroshi, youryuu_shikenbisha	34手3b4c・44手4d4e / 60手4c5d / 20手5a6b / 24手3c3d・28手2a3c / 64手3c4b・108手6b7b	完全	youryuu_shikenbishaはかなり離れた2手	—
12	相手	rokusuji_kuraidori, yonenaga_kyusen_yagura, yonyonfu_pacman	3手6g6f / 23手4g4f・33手2i3g	完全	—	—
13	本人	kusarigamagin, migi_shikenbisha, ponpon_kei, sujichigai_kaku, wakisystem, yagura_37gin, yagura_bogin	96手7f8g / 124手R6b / 34手8a7c・52手7c6e / 118手7f6e / 48手B6d / 22手6b7c / 8手7a6b・22手6b7c・26手7c8d	完全	後半の1手pattern多数	—
13	相手	yokofudori_33kei, yokofudori_44kaku	65手8i7g / 69手5e6f	完全	—	—
14	本人	migigyoku, onikoroshi, ponpon_kei	22手5a6b / 26手3c3d・34手2a3c / 12手8a7c・52手7c6e	完全	—	—
14	相手	rokusuji_kuraidori, yonenaga_kyusen_yagura, yonyonfu_pacman	7手6g6f / 23手4g4f・27手2i3g	完全	—	—
15	本人	douke_yagura, eishunryu, gangi_senpou, kakutoufu, kamereon_senpo, kanikanigin, migigyoku, mukaibisha, yagura_37gin	10手6b6c・14手8a7c / 6手7a6b・72手5c5d・80手6d5c / 28手4b4c・80手6d5c / 56手2c2d / 28手4b4c・36手4d4e / 72手5c5d・80手6d5c・88手5c6d / 34手5a6b / 66手4d2b / 90手6d7c	完全	複数のpatternが後半までつながって成立	—
15	相手	rokusuji_kuraidori, shikenbisha_opponent, yokofudori_33kei, yonyonfu_pacman	3手6g6f / 33手7g6h / 61手8i7g	完全	—	—
16	本人	douke_yagura, henachoko_kyusen, kakutoufu, koshikakegin, migigyoku, onikoroshi, ponpon_kei	25手4h4g・35手2i3g / 15手7i6h・35手2i3g・65手4f4e / 51手8g8f / 59手6g5f / 37手5i4h / 7手7g7f・47手8i7g / 35手2i3g・67手3g4e	完全	—	—
16	相手	rokusuji_kuraidori, shikenbisha_opponent, yokofudori_33kei, yonenaga_kyusen_yagura, yonyonfu_pacman	40手4c4d / 64手3a4b / 44手2a3c / 14手6c6d・20手8a7c	完全	—	—
17	本人	chousoku_37gin, kanikanigin, koshikakegin, migigyoku, yagura_37gin	40手7b7c・42手7c6d / 6手5c5d・14手4b5c・42手7c6d / 16手5c5d / 18手5a6b / 40手7b7c	完全	chousoku_37ginとyagura_37ginが同一1手を共有	—
17	相手	rokusuji_kuraidori, yonenaga_kyusen_yagura, yonyonfu_pacman	77手6g6f / 13手4g4f・27手2i3g	完全	—	—
18	本人	douke_yagura, kakutoufu, koshikakegin, onikoroshi, yagura_37gin	16手6b6c・60手8a7c / 14手2c2d / 20手6c5d / 10手3c3d・34手2a3c / 58手S*7c	完全	—	—
18	相手	ittezon_kakugawari, shikenbisha_opponent, yokofudori_33kei	101手2d2b+ / 71手7i6h / 63手8i7g	完全	ittezon_kakugawariは終盤の1手	—
19	本人	henachoko_kyusen, kakutoufu, kamereon_senpo, koshikakegin, migigyoku, ponpon_kei, sujichigai_kaku, wakisystem, yagura_37gin	10手3a4b・30手8a7c・38手6d6e / 60手2c2d / 14手4b4c・24手4d4e / 16手4c5d / 36手5a6b / 30手8a7c・42手7c6e / 74手6d6e / 54手8f6d / 82手S*7c	完全	後半成立のpattern多数	—
19	相手	rokusuji_kuraidori, shikenbisha_opponent, yokofudori_33kei, yonyonfu_pacman	19手6g6f / 23手7g6h / 93手8i7g	完全	—	—
20	本人	aigakari_bogin, boh_gin_self, genshi_bogin, hayakurigin, kakutoufu, koshikakegin, migigyoku, naname_bogin_self, onikoroshi	62手8b8c・64手8c8d / 同じ＋68手8d8e / 90手S6d・94手P7e / 22手2c2d / 30手4c5d / 20手5a6b / 90手S6d・94手P7e / 2手3c3d・28手2a3c	完全	aigakari_boginとboh_gin_selfは同一pattern	—
20	相手	yokofudori_44kaku, yokofudori_45kaku	35手8d6f / 29手B*6e	完全	1手pattern	—
21	本人	migigyoku	21手5i4h	完全	1手のみ	—
21	相手	rokusuji_kuraidori, yonyonfu_pacman	14手4c4d	完全	同一1手pattern	—
22	本人	douke_yagura, eishunryu, gangi_senpou, henachoko_kyusen, hidarigyoku, kakutoufu, kamereon_senpo, koshikakegin, mukaibisha, onikoroshi	14手6b6c・38手8a7c / 6手7a6b・40手5c5d・118手5b5c / 18手4b4c・118手5b5c / 12手3a4b・38手8a7c・48手6d6e / 28手1c2b・116手3a3b / 34手2c2d / 18手4b4c・72手4d4e / 42手6c5d / 28手1c2b / 10手3c3d・76手2a3c	完全	後半で成立するもの多数	—
22	相手	rokusuji_kuraidori, shikenbisha_opponent, yonyonfu_pacman	13手6g6f / 63手7i6h	完全	—	—
23	本人	douke_yagura	9手4h4g・17手2i3g	完全	—	—
23	相手	rokusuji_kuraidori, yokofudori_33kei, yonyonfu_pacman	10手4c4d / 32手2a3c	完全	—	—
24	本人	chousoku_37gin, eishunryu, hayakurigin, henachoko_kyusen, kakutoufu, kanikanigin, migigyoku, naname_bogin_self, onikoroshi, yagura_37gin, yagura_senpo, yamada_joseki	86手6d7c・100手5e6d / 8手7a6b・34手5c5d・36手6b5c / 68手5c6d・84手7d7e / 20手3a4b・54手8a7c・64手6d6e / 10手2c2d / 34手5c5d・36手6b5c・68手5c6d / 62手5b6b / 68手5c6d・84手7d7e / 16手3c3d・80手2a3c / 86手6d7c / 16手3c3d・20手3a4b・22手4b3c / 36手6b5c・46手7d7e・68手5c6d	完全	非常に多くのpatternが同時成立	—
24	相手	direct_mukaibisha, mukaibisha_opponent, rokusuji_kuraidori, sansan_kaku_senpo, yokofudori_33kaku, yokofudori_33kei, yonyonfu_pacman	59手9g8h / 75手6g6f / 103手7f7g / 49手8i7g	完全	後半のpatternあり	—
25	本人	eishunryu, hikikaku, kakutoufu, kanikanigin, koshikakegin, migigyoku, onikoroshi, torisashi, ureshino, yagura_37gin	6手7a6b・28手5c5d・30手4b5c / 94手9a3a / 38手2c2d / 28手5c5d・30手4b5c・92手5c6d / 62手6c5d / 22手5a6b / 34手3c3d・46手2a3c / 94手9a3a / 26手3a4b・94手9a3a・128手3a3b / 102手6d7c	完全	後半patternが多い	—
25	相手	rokusuji_kuraidori, yonyonfu_pacman	3手6g6f	完全	同一1手pattern	—


この表から読み取れること

ここが今回かなり重要です。

「棋譜の流れから戦型を認識できるか」という実験としては、現状の114定義では、かなり厳しいです。

たとえば、

第20局・本人は aigakari_bogin、boh_gin_self、genshi_bogin が同じ 8b8c → 8c8d を共有して完全一致します。

第8局・本人は hikikaku と torisashi が、どちらも「角→7i」という1手だけのpatternなので完全一致します。

第3局・相手では direct_mukaibisha と mukaibisha_opponent が、どちらも「飛→2b」だけなので完全一致します。

第1局・相手では rokusuji_kuraidori と yonyonfu_pacman が、どちらも「歩→4d」だけで完全一致します。

第24局・本人では12個もの定義が完全一致します。


つまり、「完全一致した」という機械的事実と、「その局の戦型を認識できた」という意味がまだ分離されていません。

これはrequestにある「patternが浅いために一致してしまう場合はそう書いてよい」という注意そのものに該当します。

さらに、第1局の chousoku_37gin が 83手目・89手目で初めて成立、第18局の ittezon_kakugawari が 101手目、第25局の ureshino が 26・94・128手目で成立しているように、序盤の戦型認識用patternなのに、終盤の手で「完全一致」になってしまうケースがあります。

これはかなり重要な発見です。

「定義の側で何が足りないか」

名前を付けず、条件の形だけで書くと、

patternが1手だけの定義が多く、別の戦型の途中の1手でも完全一致してしまう。

2手以上のpatternでも、1手目と2手目の間隔に上限がないため、数十手離れた手で完全一致できる。

序盤に現れるべきpatternかどうかを判定する手数条件がない。

patternの各手が「同じ駒の連続した動き」なのか、「局面形成の中で現れる複数の手」なのかを区別していない。

他の戦型でも普通に現れる手をpatternにしている定義がある。

複数定義が同じpatternを共有しているため、完全一致してもIDを一つに絞れない。

「その後に何が続いたら成立なのか」という否定条件・追加条件がない。

戦型を構成する前段階の手順と、戦型そのものを区別する条件がない。

ibisha、nakabisha、shikenbisha など7件のpatternなし定義は、この資料のpattern照合だけでは機械的に認識できない。


そして、今回の結果で一番大きいのは、**「戦型定義を増やせば解決する問題ではなく、recognition_patternの表現方法そのものを改める必要がある」**という点です。

なお、本編・付録側では25局について形勢推移や103局面の分かれ道を扱っていますが、そこでもエンジン第1候補は「正解」ではなく比較材料と明記されています。したがって、今回の戦型分類にそれらの評価を混ぜてはいません。 

結論として、このH7の実験結果は「25局を戦型定義へ分類できた」よりも、現行114定義の recognition_pattern が浅すぎて、文脈ゼロでは大量の偽陽性・重複分類を生むことをかなり明確に示しています。

gpt
