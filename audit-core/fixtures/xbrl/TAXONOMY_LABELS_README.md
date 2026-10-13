# 標準タクソノミの日本語ラベル(リポジトリの外に置く)

人間の許可(2026-10-08): 「標準タクソノミの日本語ラベル(jppfs・jpcrp の 2025-11-01 版)の
取得を許可します。書類が参照する版と一致させ、**取得したファイルはリポジトリの外に置いて
sha256 だけを残す**。」

**このリポジトリにはラベルの本体を 1 バイトも置かない。** 置くのは
`taxonomy_labels_sha256.txt`(照合用の sha256)とこの説明だけ。

## 置き場

    ~/.cache/audit-core/edinet-taxonomy/2025-11-01/

(既存の書類 ZIP の置き場 `~/.cache/audit-core/edinet/` と同じ流儀。
環境変数 `EDINET_TAXONOMY_DIR` で上書きできる。)

## 取り方

    mkdir -p ~/.cache/audit-core/edinet-taxonomy/2025-11-01
    cd ~/.cache/audit-core/edinet-taxonomy/2025-11-01
    curl -sS -O http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/label/jppfs_2025-11-01_lab.xml
    curl -sS -O http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/label/jpcrp_2025-11-01_lab.xml

## 照合

    shasum -a 256 -c <このリポジトリ>/audit-core/fixtures/xbrl/taxonomy_labels_sha256.txt

| ファイル | バイト | sha256 |
|---|---|---|
| `jppfs_2025-11-01_lab.xml` | 5,053,378 | `bf56ea1585afe426b398a9053ec4de4dbeafc211a53675b5d6d19453e4e04bf4` |
| `jpcrp_2025-11-01_lab.xml` | 3,309,364 | `df9c23764ec9a63cb65b5ef62e79a2907c590523797421442ea2a60e334cd684` |

## 版が書類と一致していることの確認

3 書類(`S100Z4Q1`・`S100Z4B6`・`S100YMFV`)の `.xsd` は `linkbaseRef` で
`taxonomy/jppfs/2025-11-01/label/jppfs_2025-11-01_lab.xml` と
`taxonomy/jpcrp/2025-11-01/label/jpcrp_2025-11-01_lab.xml` を指している(機械で確認済み)。
**別の版の書類を測るときは、その書類の `linkbaseRef` の版を取り直すこと。**

## 著作権

ファイルの先頭に金融庁の表示がある(`(c) Financial Services Agency, The Japanese Government.`)。
**本文は引用せず、リポジトリにも複製しない。** 使うのは「要素名 → 日本語の標準ラベル」の
対応を実行時に読むことだけ。
