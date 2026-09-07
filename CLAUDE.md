# CLAUDE.md

このファイルは、このリポジトリで作業するすべてのセッション(人間・Claude Codeエージェント問わず)が最初に読む「憲法」です。**薄く・安定させておく**ことを原則とし、詳細は `docs/` 以下に置きます。CLAUDE.md自体を頻繁に書き換える必要が出てきたら、それは大抵「本当はdocs/に書くべき内容」です。判断基準は [docs/CHANGE_MANAGEMENT.md](docs/CHANGE_MANAGEMENT.md) を参照してください。

## プロジェクト

将棋初心者向けのAIコーチアプリ「将棋コーチ」。

## 最重要コンセプト

> このプロジェクトは、「定跡を覚えさせるアプリ」ではなく、
> **「将棋の考え方を対局中に身につけさせるAIコーチ」** である。
> 「最善手を教えるアプリ」ではない。

この一文と矛盾する実装・データ・UI文言は、たとえ技術的に正しくても採用しない。迷ったら「これは"覚えさせる"設計になっていないか?」を自問すること。

## 現在のスコープ(MVP)

- 対局: **四間飛車(自分) vs 居飛車(AI)**。これは**開発上のスコープ**であり、**ユーザーに前提知識として最初に提示する設定ではない**(下記「戦法の扱い」)
- 先後: **自分=先手固定**、相手=後手固定(先後選択・先後可変は将来拡張として別途判断する。詳細は [docs/DATA_MODEL.md](docs/DATA_MODEL.md) の座標表記の規約を参照)
- 戦法の扱い: 戦型・狙い・陣形は、対局開始前に固定された設定ではなく、**対局の経過から徐々に形成される認識(仮説)**として扱う。戦法の名前は、認識がその段階に達してから初めて出す(詳細は [docs/DATA_MODEL.md](docs/DATA_MODEL.md))
- 目標形: **美濃囲い系**(本美濃・高美濃・銀冠など)
- プラットフォーム: Webブラウザ
- 想定ユーザー: プログラミング経験・将棋経験ともに前提としない初心者
- 実験機能: **指す前にユーザーが「この手は何のため」を申告する仕組み**(MVPの中心機能ではなく、最小の実験機能として含める。詳細は [docs/LONG_TERM_VISION.md](docs/LONG_TERM_VISION.md))

このスコープを広げる変更(戦型追加・目標形追加など)は、必ず人間の承認を経ること。詳細は [docs/PHASES.md](docs/PHASES.md)。

## 教育用データパイプライン

このアプリの中核は、次の9段階のパイプラインである。単なる棋譜・定跡データの丸暗記ではなく、**各段階に「初心者向けの意味づけ」を持たせる**ことが目的。

```
局面 → 戦型・形 → 相手の意図 → 相手の次の狙い → 自分の目的
     → 目指せる形 → 代表的な候補手 → その手の目的 → 初心者向け説明
```

各段階の詳細な設計・対応するデータスキーマは [docs/DATA_MODEL.md](docs/DATA_MODEL.md) を参照。

## 絶対に守るルール

1. **目的→手→理由** の順で説明を構成する(手だけを提示しない)。
2. 将棋用語には必ず初心者向けの説明を添える(用語を知っている前提にしない)。
3. 将棋エンジンによる安全確認(悪手でないかのチェック)を経ていない候補手をユーザーに見せない。
4. 将棋の知識は3種(記述的・構造的・判断的)に分けて扱う([docs/DATA_MODEL.md](docs/DATA_MODEL.md))。既存スキーマに準拠した新しいレコード(記述的知識)は未レビューの下書きとして件数の制限なく追加してよいが、**未レビューの知識を、戦法・陣形・狙いの名前としてユーザーへ断定的に見せない**。スキーマの形式を変える知識(構造的)と、判定結果・優先度・閾値・安全性・ゲーム挙動を変える知識(判断的)は、**人間の承認なしに確定しない**。
5. LLMに将棋の事実判断(この形は何か、相手の意図は何か)をさせない。LLMを使う場合の役割は、確定した判断を自然な言い回しに整える「言い換え」に限定する。
6. 断定できないことは断定しない(「〜を狙っている可能性があります」のような控えめな表現を既定にする)。
7. `main` ブランチへのマージは人間の承認を経る。詳細は [docs/GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md)。

## 現段階でやらないこと

- 構造的知識・判断的知識の人間承認なしの追加・変更、および未レビューの知識を断定的な表示に使うこと(上記「絶対に守るルール」4番)
- 「対局シナリオ」のうち、**ユーザーが練習テーマとして相手の作戦を選ぶ仕組み**の本実装 ― 構造は [docs/SCENARIOS.md](docs/SCENARIOS.md) に設計済みだが、本実装は見送り中(判断の記録は [docs/PHASES.md](docs/PHASES.md))

なお「**相手AIが狙いを持って指す(選んだものはユーザーに開示しない)**」ことは、人間の判断により行う方針へ変更された。**MVPで相手AIが選択候補として使う範囲**は、STEP δ で司令塔が提案し人間が追認した解釈により `data/intents/` の居飛車系3件(棒銀・斜め棒銀・早仕掛け)に限定するが、この限定は相手AIの選択範囲についてのものであり、`data/` への記述的知識の追加や将来の戦法追加を禁じるものではない([docs/DATA_MODEL.md](docs/DATA_MODEL.md) の Kind 1)。上の見送りはこれには当たらない。実装は今後のSTEPで行い、現段階では未実装である([docs/SCENARIOS.md](docs/SCENARIOS.md)・[docs/PHASES.md](docs/PHASES.md))。

着手済み・完了済みの範囲は [docs/PHASES.md](docs/PHASES.md) の「現在地」を正とする。

## ドキュメント一覧

| ファイル | 内容 |
|---|---|
| [docs/README.md](docs/README.md) | ドキュメント全体の目次 |
| [docs/PROJECT_VISION.md](docs/PROJECT_VISION.md) | このアプリの完成像(核心的な強み・完成イメージ・完成の判定基準) |
| [docs/LONG_TERM_VISION.md](docs/LONG_TERM_VISION.md) | 長期構想(このアプリが最終的に何になろうとしているか)。MVPの完成条件ではない |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 全体構造とモジュール・Unitの責務境界 |
| [docs/AGENT_PROTOCOL.md](docs/AGENT_PROTOCOL.md) | 3役(司令塔・実装担当・承認/監査担当)と専門エージェントの協働ルール |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | 教育用データパイプラインとスキーマ設計の詳細 |
| [docs/SCENARIOS.md](docs/SCENARIOS.md) | 対局シナリオ(AI序盤制御)の将来設計 |
| [docs/PHASES.md](docs/PHASES.md) | Phase 0〜6 の開発計画と受け入れ基準 |
| [docs/GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md) | ブランチ戦略・コミット規約 |
| [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md) | 自動テスト戦略 |
| [docs/ROLES.md](docs/ROLES.md) | 人間とAIエージェントの役割分担 |
| [docs/CHANGE_MANAGEMENT.md](docs/CHANGE_MANAGEMENT.md) | 仕様変更時に何をどこで直すかのルール |

## ディレクトリ構成(予定・現状)

```
sgogi-coach/
├── CLAUDE.md
├── .claude/            # Claude Code設定(agents/commands/skills/hooks)
├── docs/               # 設計・運用ドキュメント
├── data/
│   ├── schemas/        # shapes/openings/intents/explanations のJSON Schema(確定)
│   └── examples/       # スキーマ検証用の最小サンプル(本番データではない)
├── apps/               # アプリ本体(Phase 0 で作成済み)
│   ├── web/
│   └── server/
├── spike/              # Phase 0着手前の技術検証(shogiops+やねうら王のUSI疎通確認)。apps/本実装ではない
├── prototypes/         # Phase 0着手前のプロトタイプ検証(shape-matcher等)。apps/本実装ではない
└── scripts/            # 開発補助スクリプト(データ検証など)
```

`apps/` は Phase 0 で作成済み(`apps/web`・`apps/server`)。`spike/`・`prototypes/` はPhase 0着手前の技術検証であり、`apps/` の本実装とは別物である。
