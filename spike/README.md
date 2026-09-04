# Phase 0 技術スパイク: shogiops + やねうら王(USI) 最小疎通確認

このディレクトリは、「将棋コーチ」アプリ本体とは別の、技術検証専用のスパイクです。
[CLAUDE.md](../CLAUDE.md) の現段階でやらないことに従い、UI・サーバー・コーチングロジック・定跡データは一切含みません。

## 目的

次の経路が実際に動くことだけを確認する。

```
局面(初期局面) → shogiops(合法手生成・局面操作・SFEN生成)
              → やねうら王(USIハンドシェイク・position・go)
              → bestmove / 評価値(score cp)
```

## 構成

| ファイル | 役割 |
|---|---|
| `package.json` | Node.jsプロジェクト定義。依存は `shogiops` のみ |
| `engine/` | ビルドした やねうら王 の実行ファイルを配置する場所(Git管理対象外) |
| `usi-client.mjs` | やねうら王プロセスを起動し、USIプロトコル(`usi`/`isready`/`position`/`go`)で通信する最小クライアント |
| `smoke-test.mjs` | shogiopsで局面を数手進め、やねうら王に投げて `bestmove` と評価値を取得するだけのスクリプト |

## 事前準備: やねうら王のビルド

`engine/` にはバイナリを含めていません(Git管理対象外)。以下の手順でローカルビルドしてください。

```bash
git clone --depth 1 https://github.com/yaneurao/YaneuraOu.git
cd YaneuraOu/source
make -j$(sysctl -n hw.ncpu) normal \
  COMPILER=clang++ \
  TARGET_CPU=APPLEM1 \
  YANEURAOU_EDITION=YANEURAOU_ENGINE_MATERIAL
cp YaneuraOu-by-gcc <このリポジトリ>/spike/engine/
```

- `TARGET_CPU=APPLEM1`: Apple Silicon (arm64) ネイティブビルド向けターゲット
- `YANEURAOU_EDITION=YANEURAOU_ENGINE_MATERIAL`: 駒得のみの評価関数。外部の評価関数ファイル(`nn.bin`など)が不要で、疎通確認の目的には十分。指し手の強さは検証対象外

## 実行方法

```bash
cd spike
npm install
node smoke-test.mjs
```

## 期待される出力

- shogiopsが生成した初期局面のSFEN
- 数手分の合法手選択とSFENの変化
- `usi` → `usiok`、`isready` → `readyok` のハンドシェイク成功ログ
- `position` / `go` 送信後の `bestmove` と(取得できれば)`score cp`
- 取得したbestmoveをshogiops側に反映した後のSFEN(往復確認)

## 既知の制約

- MATERIAL版エンジンのため、指し手の強さ・評価値の意味は将棋として最善手を示すものではない(疎通確認が目的)
- `engine/`配下のバイナリはこの環境専用にビルドしたもので、Gitにcommitしない
- このスパイクの成果物・知見をPhase 0本実装(`apps/server/src/engine/`)に転用する際は、`.claude/agents/engine-integration.md` の責任範囲に従う
