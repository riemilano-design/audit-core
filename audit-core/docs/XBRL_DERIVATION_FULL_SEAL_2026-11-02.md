# 封: 導出の検証の診断(後半)― AI の文の数字を instance の全 fact と計算リンクから導出できるか ― 2026-11-02

2026-11-02。人間の指示「君に任せるから、課題解決して」(2026-11-02)の続き。前半(`docs/XBRL_DERIVATION_DIAG_SEAL_2026-11-02.md` → 結果 `docs/XBRL_DERIVATION_DIAG_2026-11-02.md`)は、候補の要素の 2 期の値からは帯の外の行を 1 行も導出できなかった。
後半は起点を変える: **AI が書いた文の数字**(2026-10-09 の実験の 415 件。盲検の札つき)を、**その書類の instance の全 fact と計算リンク**に当て、固定した導出の集合で説明が付く行を数える。
**engine(`core/`・`adapters/`)は 1 行も変えず、import もしない。** instance は repo に同梱の ZIP を標準ライブラリ(zipfile・xml/正規表現)で読む。通信しない。0 USD。LLM を呼ばない。

## §0 材料(全部 repo の中。sha256 で固定)

| 材料 | file | sha256 |
|---|---|---|
| AI の文の主張(id・文・数・単位) | `fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json` | `c886a9e69353c677297341436f9777b779895054804adce1805f3d546dd4b579` |
| 盲検の札(真 / 偽 / 判定不能、根拠) | `fixtures/xbrl/ai_prose_labels_2026-10-09.json` | `7eac1450c40c68e0a25bf7f56c32db4ee6dad226e55df7efdb8019764a71173b` |
| engine の判定(profile P16、2026-10-13。claim ごとの state・pointers・recomputed) | `fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json` | `6c4c65d1d24ed46250d6bda41fc023d0624ec130f9c1fe791e840c6def7077da` |
| 書類(経営分析の節を AI の文に差し替えた ZIP。inline XBRL と計算リンクを含む) | `fixtures/xbrl/ai_prose_instance_2026-10-09.zip` | `03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799` |

**母数(封の時点で記録から数えた)**: 札が 真・kind が num・P16 の state が GROUNDED でない主張 = **53 件**(VALUE_MISMATCH 23・UNVERIFIABLE 18・POINTER_NOT_FOUND 12。単位は 円 28・百万円 14・% 5・ポイント 3・名 3)。
**対照**: 札が 真・kind が num・GROUNDED = **249 件**(全部に engine の `recomputed` の値が在る)。D1 がこの 249 件の値を fact から見つけられるかで、読み取りの配線を確かめる。
台帳 P-29 の「真の主張 391 のうち止めた 214」は profile P7(2026-10-09)の数で、claim ごとの state は記録に無い。本便は P16 の記録(claim ごとに在る)で母数を取る。P7 の 214 は本便では使わない。

## §1 fact の読み方(標準ライブラリ)

- `XBRL/PublicDoc/*_ixbrl.htm` の `ix:nonFraction` を全部読む: name・contextRef・unitRef・decimals・scale・sign・format・本文。値 = 本文の数(桁区切りを除く)× 10^scale、sign="-" なら負。`xsi:nil="true"` と空の本文は捨てる。同じ (name, contextRef, unitRef, 値) の重複は 1 つにする(表紙と本文に同じ fact が出る)。
- g(fact) = 10^(−decimals) 円(decimals が INF なら 0)。
- 単位: unitRef が JPY の fact を「金額」、shares を「株数」、pure(それ以外の無次元)を「比率・個数」とする。
- 文の数の円換算の倍率 s(単位): 円 1・千円 10³・百万円 10⁶。% と ポイント は比率(fact の pure の値 × 100 と比べる)。名 は個数(pure)。
- 計算リンク `*_cal.xml` の `calculationArc`(from = 親, to = 子, weight)を全部読む。

## §2 導出の集合(字で固定。文を見て足さない)

文の数 t、単位 unit。候補 = 帯の中に入った (導出の型, fact の組) の 1 つ 1 つ。

| 型 | 対象の単位 | 候補の作り方 | v | G(切り捨ての帯。H = G/2) |
|---|---|---|---|---|
| **D1** 単一 | 金額 / 名 / % | 金額の fact 1 つ(金額の文)/ pure の fact 1 つ(名: ×1、%: ×100) | fact の値 | g + u(u = 文の最下位の桁 × s。%・名は文の桁から) |
| **D2** 差 | 金額 / ポイント | 同じ name・同じ unit の fact 2 つ(context が違う) | a − b(ポイントは ×100) | g_a + g_b + u |
| **D3** 増減率 | % | 同じ name・同じ unit の金額 fact 2 つ | (a − b) / |b| × 100 | u + 100 (g_a / |b| + g_b |a| / b²) |
| **D4** 合算 | 金額 | 計算リンクの 1 つの親と、同じ context に在るその子 2 つ以上。**親の fact がその context に無いときだけ** | Σ weight × 子 | Σ g_子 + u |
| **D5** 比率 | % | 同じ context の金額 fact 2 つ(順序あり) | a / |b| × 100 | u + 100 (g_a / |b| + g_b |a| / b²) |
| **D6** 一株あたり | 円 | 金額 fact ÷ 株数 fact(context は問わない) | a / b | u + (g_a / |b| + g_b |a| / b²) |

e = | |v| − t' |(t' は t を円または比率の尺に合わせた値)。段: 完全一致(e = 0)/ 丸めの帯 H(e ≤ H)/ 丸めの帯 F(H < e ≤ G)/ 不一致。帯の中 = 完全一致・H・F。
**行の判定**: 帯の中の候補の数 n で、n = 1 → 導出一致(型と fact を名指す)、n ≥ 2 → 保留、n = 0 → 不一致。候補は (型, fact の組) で数える(同じ値の fact が 2 つ在れば 2 つ)。
**根拠との照合(参考。判定には使わない)**: 導出一致の行で、候補の fact の要素の local name が札の「根拠」の字に含まれるか。

## §3 事前予測(**実装より先に固定。結果を見てから書き換えない**。母数 53)

| | 予測 | **外れ方** |
|---|---|---|
| **C-1** | 対照 249 件のうち D1 が engine の `recomputed` の値を帯の中で見つける割合 **95% 以上**(読み取りの配線。下回れば読み取りの欠陥を先に疑う) | 95% 未満 |
| **C-2** | 母数 53 のうち D1(単一の fact)だけで帯の中に入る行 **10〜25**(engine は主語・期の結びつきで止めたが、数そのものは instance に在る) | 幅の外 |
| **C-3** | 導出一致(候補ちょうど 1) **15〜35** | 幅の外 |
| **C-4** | 不一致(候補 0) **8〜25** | 幅の外 |
| **C-5** | 保留(候補 2 以上) **5〜20** | 幅の外 |
| **C-6** | 導出一致の行の型のうち、D1 以外で最多は **D2(差)** | D2 でない |
| **C-7** | % の 5 件のうち D3 か D5 が帯の中 **3〜5** | 2 以下 |
| **C-8** | 導出一致の行で、候補の要素の local name が札の根拠に含まれる割合 **60% 以上** | 60% 未満 |
| **C-9** | 円 28 件のうち D6(一株あたり)が帯の中 **5〜20** | 幅の外 |
| **C-10** | 判定不能の num 2 件・偽の 1 件(text なので母数外)は判定しない。数だけ記録 | ― |

## §4 言えないこと

- 帯の中に入っても「出所として正しい」とは言えない(instance 全体を探すので偶然の一致が増える。保留の数と、根拠との照合の割合がその目安)。
- 1 書類(1 社)の AI の文で、書き手は 1 つの model。他の書類・他の書き手には広げられない。
- P16 の判定であって、いまの既定 P27 の判定ではない(P27 で止める数は測っていない)。
- 導出一致の行を engine に入れるか(導出の profile)は、この診断の後に人間が決める。

## §5 作法

- 封を先に commit → script `measure/xbrl_derivation_full_2026-11-02.py`(標準ライブラリだけ)→ 記録 `fixtures/xbrl/derivation_full_2026-11-02.json`(claim id は書いてよい ― この実験の記録は既に id を持つ。docID は書かない)→ 結果 `docs/XBRL_DERIVATION_FULL_2026-11-02.md` → 門 `tests/measure/test_xbrl_derivation_full.py` → 独立監査 GO → path 指定で commit。
- 覆い・台帳・README の本数は同じ便で揃える。
