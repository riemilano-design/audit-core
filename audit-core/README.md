# audit-core

AI が出した文章の主張(Claim)を、証拠(Evidence)へのポインタと契約(Contract)で機械が照合し、GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND / UNVERIFIABLE の 4 状態で返す監査の Core。将棋の対局後診断(このリポジトリの `scripts/playtest/`)が最初の顧客、EDINET の XBRL が 2 番目。

- 設計の正本: [docs/CLAIM_CONTRACT_SPEC_v0.2.md](docs/CLAIM_CONTRACT_SPEC_v0.2.md)(4 層)。経緯と封じた予測は [docs/](docs/)(README の一覧は [../docs/README.md](../docs/README.md))。
- **いま使う profile**: 既定は `P27`。外部の数の文(AI の文など)を点検するときの推奨は `P33E`(明示して使う)。推奨の負けの側・判定の出どころ・速さとメモリは [docs/README_HISTORY_2026-11-14.md](docs/README_HISTORY_2026-11-14.md) の 2026-11-10 の行に在る。既定の切り替えは人間が決める。
- **測った事実の正本**: 台帳 [docs/FACTS_FOR_BUYERS_2026-10-20.md](docs/FACTS_FOR_BUYERS_2026-10-20.md)。数の正本は `fixtures/**/*.json`。README には数を積まない。
- **経緯**(接続の工程・既定と推奨の profile の移り変わり): [docs/README_HISTORY_2026-11-14.md](docs/README_HISTORY_2026-11-14.md)。2026-11-14 に README から字のまま移した。
- **英文の決算短信の点検**(売り方の側。engine は使わない別の道具): 入口は [sales/README.md](sales/README.md)。
- 買い手向けの英語の入口: [README.en.md](README.en.md)。

**証明済みの範囲(2026-10-06、人間の決定)**: XBRL 3 社(S100Z4Q1・S100Z4B6・S100YMFV)と将棋 c5 の 2 つの Adapter が、Core の変更 0(`f917f02` 以降)で同じ `verify_all` により動いた。修飾が実際に出る場合(XBRL)と全部空の場合(将棋 H-9 の断面)の双方を処理できた。**これは「XBRL 専用の抽象ではない」という反証であって、Core の汎用性の証明ではない。** 以後の文書はこの行を参照し、範囲が広がったときだけこの行を書き換える([docs/CORE_CONNECTION_C2_DECISIONS_AFTER_2026-10-06.md](docs/CORE_CONNECTION_C2_DECISIONS_AFTER_2026-10-06.md))。

## 10 分の再現(API 鍵なし・0 USD。初回のラベル取得を除き通信なし)

clone した直後に、`audit-core/` の中で、誤りを入れたとき何を通し何を止めるかを自分の手で見る入口(記録 `fixtures/xbrl/ritual_2026-10-20.json`、結果 `docs/XBRL_RITUAL_RESULT_2026-10-20.md`)。

**手順 0(初回に 1 回だけ)**: EDINET から標準タクソノミのラベル 2 file を取る(curl 2 本 + sha256 照合、約 8 MB)。手順と sha256 は `fixtures/xbrl/TAXONOMY_LABELS_README.md`。置き場は `~/.cache/audit-core/edinet-taxonomy/2025-11-01/` で、環境変数 `EDINET_TAXONOMY_DIR` で変えられる。ラベルには金融庁の著作権表示があるので repo には入れていない。無いまま走らせると、案内を出して止まる(rc=2)。

**手順 1**:

```
python3 measure/ritual_2026-10-20.py --out <出力先>
```

- **通した 2 / 243 = 0.8%**: 経営分析の文の数を 1 つずつわざと変え(最小の桁の 1 字 / ±1 最小単位)、書類が GROUNDED のまま通した数。
- 止めた 210 / 243 = 86.4%(VALUE_MISMATCH)。ほかに、参照先が結べず止めた(POINTER_NOT_FOUND)31。
- 通した 2 の中身: 丸めの帯の中(±1 最小単位)1(率 1・金額ほか 0)・退化値(`0百万円 → 00百万円`。字は変わるが値が変わらない)1・帯の外 0。これが欠陥でないかは読む人が決める。
- 既定は P27(2026-10-28。P26 に P27 の旗 4 つ(書かれた桁での照合・1 株当たりの窓・「1人当たり」の「1」・先の決算期)を積んだもの)。前期の値を当期の数として書くと止まるのは、P22(期を縛る。2026-10-20)から変わらない: P21 で注入後の値が前期の fact に合い、参照先が当期から前期へ移ったまま GROUNDED で通した N125・N199 は、P27 では止める(N125 は POINTER_NOT_FOUND・N199 は VALUE_MISMATCH)。通した行のうち参照先が前期へ移った行は 0。
- P26 のとき(2026-10-23 の P26 の段 2 から、2026-10-28 の P27 の段 2 の前まで)は 通した 2 / 243、止めた 210 / 243(記録 `fixtures/xbrl/ritual_2026-10-20_p26.json`)。
- P22 のとき(2026-10-20 の `d0b544c` から、2026-10-23 の P26 の段 2 の前まで)は 通した 15 / 240、止めた 225 / 240(記録 `fixtures/xbrl/ritual_2026-10-20_p22.json`)。
- P21 のとき(2026-10-20、`cb4b497` まで)は 通した 17 / 241、止めた 224 / 241(記録 `fixtures/xbrl/ritual_2026-10-20_p21.json`)。
- 所要 22.8 秒(記録を採った機械の値)。
- 入力 `fixtures/xbrl/ai_prose_instance_2026-10-09.zip`(sha256 `03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799`、580,260 bytes)は EDINET の公開の開示書類(書類 ID S100Z4Q1、提出者コード E36539 ＤＮホールディングス株式会社、提出日 2026-09-30)。**経営分析の節は 2026-10-09 の AI 文の実験で AI の文に差し替えてあり、原文ではない。**
- 鍵は使わない。読むのは同梱の書類と `~/.cache` のラベル 2 file だけ。自分の書類で回すには、EDINET の鍵と書類の取得が要る。

## 自分の有報の文を照合して、日本語の報告にする(0 USD・通信なし)

自分の書類の ZIP(EDINET の有価証券報告書)と、照合したい文章(経営分析の節の代わりに差し替える文)を渡す。判定は engine が出したまま、報告は並べ方と字だけを日本語にする(違う → 要確認 → 対象外・判断しない → 一致。封 [docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md](docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md)・結果 [docs/XBRL_CUSTOMER_REPORT_RESULT_2026-10-21.md](docs/XBRL_CUSTOMER_REPORT_RESULT_2026-10-21.md))。標準ラベル(手順 0 の 2 file)が無ければ出典は要素名のまま出る。

```
python3 -m adapters.xbrl.verify_document --zip <自分の書類.zip> --text <自分の文.txt> --out out.json
python3 -m adapters.xbrl.report_customer --in out.json --out report.md --labels ~/.cache/audit-core/edinet-taxonomy/2025-11-01 --zip <自分の書類.zip>
python3 -m adapters.xbrl.report_customer --in out.json --out report_full.md --labels ~/.cache/audit-core/edinet-taxonomy/2025-11-01 --zip <自分の書類.zip> --full   # 一致の行も出す
```

`--zip` を渡すと、会社ごとの要素・区分が書類自身のラベルで日本語になり、表題が提出者名になる。指紋は本文に出さず、隣の `report.provenance.json`(機械用)に出る。ラベルは `fixtures/xbrl/taxonomy_labels_sha256.txt`(名簿)に在る file だけを読む。

## 置き場所

| 場所 | 中身 |
|---|---|
| `core/py/audit_core/` | Core。将棋も XBRL も知らない |
| `adapters/xbrl/` | XBRL Adapter。語彙・member・母集団の印・抽出規則 P-1〜P-8。入口は `verify_document`・`report_customer` |
| `measure/` | 実験の入口(測る script)。engine は変えない |
| `fixtures/` | 記録(数の正本)。`fixtures/xbrl/` に探りの JSON・期待値(計器 3 の Golden)・探りの script の系譜・`manifest.json`。**ZIP は置かない** |
| `tests/` | 単体・境界・変異・Golden。門は `tests/measure/` |
| `docs/` | 設計・封(`_SEAL_`)・結果(`_RESULT_`)・台帳(`docs/` から 2026-10-06 に移動。履歴は `git log --follow`) |
| `sales/` | 売り方の側(英文の決算短信の点検・営業の紙・送る文の下書き)。入口は [sales/README.md](sales/README.md) |

## 材料と鍵

- 材料の ZIP は `~/.cache/audit-core/edinet/<docID>.zip`。sha256 は `fixtures/xbrl/manifest.json`。無ければ試験は**落ちる**(skip にしない)。
- EDINET API の鍵は環境変数 `EDINET_API_KEY`(`~/.config/edinet/env`)。repo・fixtures・ログに書かない。

## 出典

金融庁 EDINET の開示書類(有価証券報告書。docID と提出日は `fixtures/xbrl/manifest.json`)を、PDL1.0 に従って出典を明記したうえで、機械で抽出・照合して加工したもの。

## 門

`audit-core/` の中で:

```
python3 -m pytest -q tests/measure   # 門だけ
sh run_tests.sh                      # 全部(覆いの検査 → pytest → unittest)
```

repo の根からは(C-1b から):

```
python3 -m unittest discover -s audit-core/tests -t audit-core
```
