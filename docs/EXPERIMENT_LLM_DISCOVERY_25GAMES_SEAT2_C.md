# 席 C2(Gemini)の回答 ― 実験 2: 棋譜の流れから戦型を認識できるか(原文のまま)

**出どころ**: 人間が Gemini の新規会話に `scripts/playtest/out/c5/experiment-llm-25/request2.md`(sha256 `ea0f55072ef6c1e0a888f46898223da1df7757dd074224ea2c0fcb148e091da9`)を本文貼り付けで渡し、回答を一字も変えずに保存したもの(2026-09-29)。原本 `seat_C2_gemini_raw.md`、sha256 `ef893090f388433ab755083bed362478294150d317e6da4a073b196ce8cd9693`(59 行・9,676 バイト)。下の区切り線から先が原文で、語も書式も変えていない。

**注(司令塔の中継)**: 最終行「Gemini」は人間が貼るときに付けた席の印で、回答の本文ではない。表は Markdown の罫線つき。

**この文書の扱い**: 実験 2(指示書 §13、H7「棋譜の流れから戦型を認識できるか」)の席の回答。発見レイヤー(顧客向け文章ではない)。「一致した定義」の id は data/ の下書き定義(すべて draft)であり、顧客の文には出さない。「定義に無い名前の候補」の欄は分類・比較に使わず、知識レーン向けの材料として司令塔経由で別に渡す。突き合わせ(席 vs 機械の rows)は LOG §6 に書く。

---

指定された条件に従い、各局の棋譜の序盤〜中盤までの流れを読み解き、提供された定義とマッチングした結果を以下に報告します。
出力: 25 局の戦型分類
| 局 | 側(本人/相手) | 一致した定義(id) | 根拠となる手順(手数と USI) | 一致の程度(完全 / 部分 / なし) | 未認識部分(定義に無いが手順にある特徴。名前を付けず手順で) | 定義に無い名前の候補(別欄) |
|---|---|---|---|---|---|---|
| g01 | 本人 | chousoku_37gin | 83手目 4f3g・89手目 S*4f | 完全 | patternが浅いため一致。1手目 2g2f・3手目 2f2e の手順を含む。 | 角換わり |
| g01 | 相手 | rokusuji_kuraidori | 38手目 4c4d | 完全 | patternが浅いため一致。単一の歩突きのみで他の手順を含まない。 | 角換わり |
| g02 | 本人 | douke_yagura | 9手目 4h4g・13手目 2i3g | 完全 | patternが浅いため一致。1手目 2g2f・3手目 2f2e の手順を含む。 | 角換わり |
| g02 | 相手 | gokigen_nakabisha | 6手目 5c5d・14手目 8b5b | 完全 | patternが浅いため一致。後手から角道を開ける手を含まない。 | ゴキゲン中飛車 |
| g03 | 本人 | koshikakegin | 57手目 S*5f | 完全 | patternが浅いため一致。1手目 2g2f・3手目 2f2e の手順を含む。 | 角換わり |
| g03 | 相手 | ittezon_kakugawari | 46手目 3c8h+ | 完全 | patternが浅いため一致。角交換のみで他の特徴を含まない。 | 角換わり |
| g04 | 本人 | eichanryu_nakabisha | 11手目 2h5h・13手目 7i6h | 完全 | patternが浅いため一致。1手目 7g7f の手順を含む。 | 矢倉 |
| g04 | 相手 | kakutoufu (side=self) | 34手目 8e8f | 完全 | patternが浅いため一致。2手目 8c8d・4手目 8d8e の手順を含む。 | 矢倉 |
| g05 | 本人 | kamereon_senpo | 33手目 6h6g・45手目 6f6e | 完全 | patternが浅いため一致。1手目 2g2f・3手目 2f2e の手順を含む。 | 角換わり |
| g05 | 相手 | yonenaga_kyusen_yagura | 26手目 6c6d・36手目 8a7c | 完全 | patternが浅いため一致。2手目 3c3d・4手目 2b3c の手順を含む。 | 角換わり |
| g06 | 本人 | gangi_senpou | 8手目 4b4c・86手目 4b5c | 完全 | patternが浅いため一致。2手目 3c3d・4手目 4c4d の手順を含む。 | 矢倉 |
| g06 | 相手 | ai_yokofudori | 77手目 2e3d | 完全 | patternが浅いため一致。1手目 7g7f・3手目 6i7h の手順を含む。 | 矢倉 |
| g07 | 本人 | douke_yagura | 11手目 4h4g・17手目 2i3g | 完全 | patternが浅いため一致。1手目 2g2f・3手目 2f2e の手順を含む。 | 角換わり |
| g07 | 相手 | yagura_35fu_hayajikake (side=self) | 32手目 3d3e・66手目 4g3f+ | 完全 | patternが浅いため一致。2手目 3c3d・4手目 2b3c の手順を含む。 | 角換わり |
| g08 | 本人 | onikoroshi | 25手目 7g7f・29手目 8i7g | 完全 | patternが浅いため一致。1手目 2g2f・3手目 2f2e の手順を含む。 | 角換わり |
| g08 | 相手 | yonenaga_kyusen_yagura | 24手目 6c6d・56手目 8a7c | 完全 | patternが浅いため一致。2手目 3c3d・4手目 2b3c の手順を含む。 | 角換わり |
| g09 | 本人 | yagura_senpo | 9手目 7g7f・13手目 7i6h・29手目 6h7g | 完全 | 定義の手順のみで進行していない。 | 横歩取り |
| g09 | 相手 | rokusuji_kuraidori | 28手目 4c4d | 完全 | patternが浅いため一致。2手目 9c9d・4手目 4a3b の手順を含む。 | 横歩取り |
| g10 | 本人 | aigakari | 3手目 2f2e・27手目 6i7h・35手目 2h2d | 完全 | 定義の手順のみで進行していない。 | 相掛かり |
| g10 | 相手 | rokusuji_kuraidori | 38手目 4c4d | 完全 | patternが浅いため一致。2手目 8c8d・6手目 8d8e の手順を含む。 | 相掛かり |
| g11 | 本人 | onikoroshi | 26手目 3c3d・28手目 2a3c | 完全 | patternが浅いため一致。2手目 8c8d・4手目 8d8e の手順を含む。 | 矢倉 |
| g11 | 相手 | yonenaga_kyusen_yagura | 19手目 4g4f・27手目 2i3g | 完全 | patternが浅いため一致。1手目 7g7f・3手目 6g6f の手順を含む。 | 矢倉 |
| g12 | 本人 | kakugawari_koshikakegin | 58手目 2d3c・60手目 4c5d | 完全 | patternが浅いため一致。2手目 8c8d・4手目 8d8e の手順を含む。 | 矢倉 |
| g12 | 相手 | yonenaga_kyusen_yagura | 23手目 4g4f・33手目 2i3g | 完全 | patternが浅いため一致。1手目 7g7f・3手目 6g6f の手順を含む。 | 矢倉 |
| g13 | 本人 | aigakari | 4手目 8d8e・10手目 4a3b・44手目 8b8f | 完全 | 序盤に 2手目 8c8d の手順を含む。 | 相掛かり |
| g13 | 相手 | sansan_kaku_senpo | 5手目 8h7g | 完全 | patternが浅いため一致。1手目 7g7f・3手目 3i4h の手順を含む。 | 相掛かり |
| g14 | 本人 | onikoroshi | 26手目 3c3d・34手目 2a3c | 完全 | patternが浅いため一致。2手目 8c8d・4手目 8d8e の手順を含む。 | 矢倉 |
| g14 | 相手 | yonenaga_kyusen_yagura | 23手目 4g4f・27手目 2i3g | 完全 | patternが浅いため一致。1手目 7g7f・3手目 7i7h の手順を含む。 | 矢倉 |
| g15 | 本人 | eishunryu | 6手目 7a6b・72手目 5c5d・80手目 6d5c | 完全 | patternが浅いため一致。2手目 8c8d・4手目 8d8e の手順を含む。 | 矢倉 |
| g15 | 相手 | rokusuji_kuraidori | 3手目 6g6f | 完全 | patternが浅いため一致。1手目 7g7f・5手目 8h7g の手順を含む。 | 矢倉 |
| g16 | 本人 | aigakari | 3手目 2f2e・11手目 6i7h・31手目 2h2d | 完全 | 飛車先交換の前に 7手目 7g7f を含む。 | 相掛かり |
| g16 | 相手 | yonenaga_kyusen_yagura | 14手目 6c6d・20手目 8a7c | 完全 | patternが浅いため一致。2手目 1c1d・4手目 4a3b の手順を含む。 | 相掛かり |
| g17 | 本人 | kanikanigin | 6手目 5c5d・14手目 4b5c・42手目 7c6d | 完全 | patternが浅いため一致。2手目 3c3d・4手目 2b3c の手順を含む。 | 角換わり |
| g17 | 相手 | yonenaga_kyusen_yagura | 13手目 4g4f・27手目 2i3g | 完全 | patternが浅いため一致。1手目 2g2f・3手目 2f2e の手順を含む。 | 角換わり |
| g18 | 本人 | aigakari | 4手目 8d8e・12手目 4a3b・26手目 8b8f | 完全 | 2手目 8c8d・4手目 8d8e の手順を含む。 | 相掛かり |
| g18 | 相手 | ai_yokofudori | 17手目 2d3d | 完全 | patternが浅いため一致。1手目 7i6h・3手目 5g5f の手順を含む。 | 相掛かり |
| g19 | 本人 | henachoko_kyusen | 10手目 3a4b・30手目 8a7c・38手目 6d6e | 完全 | patternが浅いため一致。2手目 8c8d・4手目 8d8e の手順を含む。 | 相掛かり |
| g19 | 相手 | gokigen_nakabisha | 35手目 5g5f・51手目 6h5h | 完全 | patternが浅いため一致。1手目 2g2f・3手目 7g7f の手順を含む。 | 相掛かり |
| g20 | 本人 | genshi_bogin | 62手目 8b8c・64手目 8c8d・68手目 8d8e | 完全 | patternが浅いため一致。2手目 3c3d・4手目 2b3c の手順を含む。 | 矢倉 |
| g20 | 相手 | kakugawari (side=self) | 27手目 2d3c+・139手目 S*3c | 完全 | patternが浅いため一致。1手目 2g2f・3手目 2f2e の手順を含む。 | 矢倉 |
| g21 | 本人 | migigyoku | 21手目 5i4h | 完全 | patternが浅いため一致。1手目 2g2f・3手目 2f2e の手順を含む。 | 角換わり |
| g21 | 相手 | direct_mukaibisha | 12手目 4b2b | 完全 | patternが浅いため一致。2手目 3c3d・4手目 2b3c の手順を含む。 | 角換わり |
| g22 | 本人 | eishunryu | 6手目 7a6b・40手目 5c5d・118手目 5b5c | 完全 | patternが浅いため一致。2手目 8c8d・4手目 8d8e の手順を含む。 | 矢倉 |
| g22 | 相手 | onikoroshi (side=self) | 97手目 P3d・99手目 N3c | 完全 | patternが浅いため一致。1手目 7g7f・3手目 7i6h の手順を含む。 | 矢倉 |
| g23 | 本人 | douke_yagura | 9手目 4h4g・17手目 2i3g | 完全 | patternが浅いため一致。1手目 2g2f・3手目 2f2e の手順を含む。 | 角換わり |
| g23 | 相手 | nitemme_32hi | 6手目 8b3b | 完全 | patternが浅いため一致。2手目 3c3d・4手目 2b3c の手順を含む。 | 角換わり |
| g24 | 本人 | eishunryu | 8手目 7a6b・34手目 5c5d・36手目 6b5c | 完全 | patternが浅いため一致。2手目 8c8d・4手目 8d8e の手順を含む。 | 相掛かり |
| g24 | 相手 | onikoroshi (side=self) | 73手目 P*3d・79手目 4e3c+ | 完全 | patternが浅いため一致。1手目 2g2f・3手目 2f2e の手順を含む。 | 相掛かり |
| g25 | 本人 | eishunryu | 6手目 7a6b・28手目 5c5d・30手目 4b5c | 完全 | patternが浅いため一致。2手目 8c8d・4手目 8d8e の手順を含む。 | 矢倉 |
| g25 | 相手 | direct_mukaibisha | 59手目 6h8h | 完全 | patternが浅いため一致。1手目 7g7f・3手目 6g6f の手順を含む。 | 矢倉 |
定義の側で何が足りないか
 * recognition_pattern が1〜2手程度の最終的な駒の配置のみで指定されており、そこに至るまでの序盤の進行（例：飛車先を突く、角道を開けるなど）を指定する手順が不足している。これにより、終盤の手順や別の展開でたまたま駒が同じマスに動いただけで「完全一致」と認識されてしまう。
 * 同じ最終位置に駒を移動させる場合でも、特定の戦型に必須となる「経由するマス」の違い（例えば、銀が直進して上がるか、別のマスを経由して上がるか）を区別する条件が不足しているため、手順の流れを適切に識別できない。

Gemini
