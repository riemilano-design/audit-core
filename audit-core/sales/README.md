# sales/ ― 売り方の側の入口(英文の決算短信の点検・営業の紙・送る文の下書き)

この folder は、Audit Core の engine(`core/`・`adapters/`)とは別の仕事を置く場所。engine の測定の正本は [../README.md](../README.md) と台帳 [../docs/FACTS_FOR_BUYERS_2026-10-20.md](../docs/FACTS_FOR_BUYERS_2026-10-20.md)。

**数はここに書かない。** 数は各便の結果の文書(`_RESULT_`)に在る。この file は「どこに何が在るか」だけを書く。

## 守ること(毎回効く)

1. **会社の名・証券コード・食い違いの値を、追跡する file に書かない**(repo は公開)。どの会社かは repo の外に置く。
2. **送る・公開する・フォームに入れる・契約する は人間がやる。** ここに在るのは下書きと控えだけ。
3. **便の数は並べて読み、足さない。** 表の便 3 つ(50 本・200 本・中間)は足さない。文章の便の「件」は表の便の「欄」と足さない。
4. **道具が「違う」と出しただけでは食い違いと書かない。** 誰が紙面を読んだか(人間か AI の席か)を、便ごとに結果の文書の字のとおりに書く。
5. 外に出す紙に金額を書かない。「精度」「証明」「保証」「唯一」は使わない。調べた範囲の言い方は「当方が調べた範囲(年月)では確認できませんでした」。
6. お客さまの文章は AI の席に読ませない。人間が `run_diagnosis.sh` を走らせ、数だけを受け取る([REPLY_KIT_2026-11-12.md](REPLY_KIT_2026-11-12.md))。
7. 英文の決算短信の便は engine の測定ではない(短い script とブラウザのページ。門も記録も無い)。engine の数と混ぜない。

## 英文の決算短信の点検(封 → 結果の対)

| 便 | 封 | 結果 |
|---|---|---|
| 下調べ | ― | [EN_TANSHIN_PROBE_2026-11-10.md](EN_TANSHIN_PROBE_2026-11-10.md) |
| 表の便(50 本) | [EN_TANSHIN_50_SEAL_2026-11-10.md](EN_TANSHIN_50_SEAL_2026-11-10.md) | [EN_TANSHIN_50_RESULT_2026-11-10.md](EN_TANSHIN_50_RESULT_2026-11-10.md) |
| 表の便(200 本にふやした) | [EN_TANSHIN_EXPAND_SEAL_2026-11-13.md](EN_TANSHIN_EXPAND_SEAL_2026-11-13.md) | [EN_TANSHIN_EXPAND_RESULT_2026-11-13.md](EN_TANSHIN_EXPAND_RESULT_2026-11-13.md) |
| 表の便(中間の決算短信) | [EN_TANSHIN_INTERIM_SEAL_2026-11-13.md](EN_TANSHIN_INTERIM_SEAL_2026-11-13.md) | [EN_TANSHIN_INTERIM_RESULT_2026-11-13.md](EN_TANSHIN_INTERIM_RESULT_2026-11-13.md) |
| 文章の中の数の便 | [EN_TANSHIN_PROSE_SEAL_2026-11-14.md](EN_TANSHIN_PROSE_SEAL_2026-11-14.md) | [EN_TANSHIN_PROSE_RESULT_2026-11-14.md](EN_TANSHIN_PROSE_RESULT_2026-11-14.md) |
| 点検ページ S1(表) | [S1_CHECK_PAGE_SEAL_2026-11-11.md](S1_CHECK_PAGE_SEAL_2026-11-11.md) | [S1_CHECK_PAGE_RESULT_2026-11-11.md](S1_CHECK_PAGE_RESULT_2026-11-11.md) |
| 点検ページ S2(文章の中の数。試作) | [S2_CHECK_PAGE_PROSE_SEAL_2026-11-14.md](S2_CHECK_PAGE_PROSE_SEAL_2026-11-14.md) | [S2_CHECK_PAGE_PROSE_RESULT_2026-11-14.md](S2_CHECK_PAGE_PROSE_RESULT_2026-11-14.md) |

- 点検ページ: `en_check/index.html`(公開している版と同じもの。変えたら公開し直すのは人間)・`en_check/index_prose.html`(文章の中の数を足した試作。公開していない)。
- 文章の便を「出す前の点検」に足す案: [PRECHECK_PROSE_PROPOSAL_2026-11-14.md](PRECHECK_PROSE_PROPOSAL_2026-11-14.md)。

## 計画と売り方

- 計画: [REVENUE_PLAN_2026-11-10.md](REVENUE_PLAN_2026-11-10.md)。売り方の形: [MONETIZE_FORMS_2026-11-10.md](MONETIZE_FORMS_2026-11-10.md)・別の形: [MONETIZE_ALTERNATIVES_2026-11-10.md](MONETIZE_ALTERNATIVES_2026-11-10.md)。
- 返事が来たときの一式と決めごと: [REPLY_KIT_2026-11-12.md](REPLY_KIT_2026-11-12.md)(§6 が人間の決定)。無償診断の受け方: [FREE_DIAGNOSIS_INTAKE_2026-11-10.md](FREE_DIAGNOSIS_INTAKE_2026-11-10.md)。

## 当たる先と下書き(送ったかどうかは各 file の控えの節)

- 最初の当たる先と下書き: [TARGETS_2026-11-10.md](TARGETS_2026-11-10.md)・[OUTREACH_DRAFTS_2026-11-10.md](OUTREACH_DRAFTS_2026-11-10.md)
- 「出す前の点検」の当たる先: [EN_CHECK_TARGETS_2026-11-11.md](EN_CHECK_TARGETS_2026-11-11.md)
- 資料を添えて送る相手: [DIRECT_MAIL_TARGETS_2026-11-12.md](DIRECT_MAIL_TARGETS_2026-11-12.md)・開示の文書を作る / 訳す / 点検する会社: [TIER2_TARGETS_2026-11-12.md](TIER2_TARGETS_2026-11-12.md)・大手: [MAJOR_TARGETS_2026-11-12.md](MAJOR_TARGETS_2026-11-12.md)
- 読み手を持っている所への持ち込み: [PITCH_TARGETS_2026-11-13.md](PITCH_TARGETS_2026-11-13.md)(返事の控えは §10)
- 2 通目の下書き: [FOLLOWUP_DRAFTS_2026-11-13.md](FOLLOWUP_DRAFTS_2026-11-13.md)(送った控えは §7)

## 記事

- 1 本目の下書き: [ARTICLE_DRAFT_EN_TANSHIN_2026-11-13.md](ARTICLE_DRAFT_EN_TANSHIN_2026-11-13.md)(公開は人間が済ませた)。図は `article_figs/`。
- 2 本目の下書き: [ARTICLE2_DRAFT_PERCENT_PARENS_2026-11-13.md](ARTICLE2_DRAFT_PERCENT_PARENS_2026-11-13.md)(出すかは人間が決める)。

## 紙と道具

| file | 何か |
|---|---|
| `deck.html` → `AuditCore_ご紹介資料_2026-11-12.pdf` | 営業資料。`sh sales/build.sh` で組む(はみ出しが在れば止まる) |
| `en50_summary.html` → `AuditCore_英文決算短信50本_結果の要約_2026-11-12.pdf` | 50 本の便の要約 |
| `sample_report.html`・`sample_report_build.py` → `AuditCore_見本の診断レポート_2026-11-10.pdf` | 見本の診断レポート |
| `run_diagnosis.sh`・`customer_report_build.py`・`customer_report_selfcheck.py` | 無償診断の 1 本分を人間が走らせる道具(0 USD。文章と出力は repo の外) |
| [YOMITOKA_PROBE_2026-11-10.md](YOMITOKA_PROBE_2026-11-10.md) | 下調べの控え(外に出す紙には使わない) |
