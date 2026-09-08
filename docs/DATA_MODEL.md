# 教育用データモデル設計

## 位置づけ

このドキュメントは、データの**意味**を定義する。データの**形式**(必須フィールド・型)は `data/schemas/*.schema.json` が正とする。両者が食い違ったら、まずどちらが正しいかを判断し、必ず両方を同時に直す(片方だけ直した状態を残さない)。ルールは [CHANGE_MANAGEMENT.md](CHANGE_MANAGEMENT.md) を参照。

## なぜこの設計か

[../CLAUDE.md](../CLAUDE.md) の最重要コンセプトのとおり、このアプリは「定跡を覚えさせる」のではなく「考え方を身につけさせる」ことが目的である。そのため、単純な「局面→次の一手」の棋譜データではなく、**各局面に「なぜその形なのか」「相手は何を狙っているのか」「自分はどこを目指せるのか」という意味づけを持たせたデータ構造**を中心に置く。

## 教育用データパイプライン(9段階)

```
① 局面
   │  (SFEN + 指し手履歴。データではなくエンジン/shogiopsから取得)
   ▼
② 戦型・形
   │  (openings + shapes で判定。自分の陣形・相手の陣形の両方に使う)
   ▼
③ 相手の意図
   │  (intents で判定。指し手の並びから「今何をしているか」を読む)
   ▼
④ 相手の次の狙い
   │  (intents の next_aim_explanation フィールド。③の延長線上の予測)
   ▼
⑤ 自分の目的
   │  (Phase1: システムが提案 / Phase2: ユーザーが選択)
   ▼
⑥ 目指せる形
   │  (shapes を shape graph でランキングし、上位2〜3個を提示)
   ▼
⑦ 代表的な候補手
   │  (⑥への道筋 + エンジンの安全確認を経た指し手)
   ▼
⑧ その手の目的
   │  (⑦の手が⑥のどの形にどう近づくかの理由づけ)
   ▼
⑨ 初心者向け説明
      (②〜⑧すべてを「目的→手→理由」の文章にまとめた最終出力。explanations として保存・生成)
```

②〜④、⑦〜⑨がデータスキーマ(shapes/openings/intents/explanations)に対応する。⑤⑥は主にロジック側(shape graph・path planner)が実行時に算出するため、それ自体は静的データとしては持たない。①はエンジン/ルール処理ライブラリ(shogiops)から得る実行時の情報であり、こちらもデータとしては持たない。

## ②〜④は確定値ではなく「認識(仮説)」

戦型(②)・陣形(②)・狙い(③④)は、対局開始前に固定された設定ではなく、**その時点までの指し手から観測できた範囲の仮説**である。いずれも同じ形で扱い、次の3つを持つ。

| 持つもの | 内容 |
|---|---|
| `status` | `none`(観測なし)/ `forming`(一部のシグネチャが観測された)/ `matched`(そのパターンのシグネチャがすべて観測された) |
| 内部スコア | 判定ロジックの内部でのみ使う。**ユーザーには見せない**(一致率などの数値を画面に出さない) |
| 根拠(`evidence`) | 何手目のどの指し手で観測されたか |

`matched` は「そのパターンの全シグネチャが観測された」という**観測事実**であって、「相手の戦法はこれである」という断定ではない。**確定値としては扱わない。**

**認識の対象は自分・相手の両方とする。** 現状は陣形が自分側、狙いが相手側だけを対象にしており、戦型はどちらも対象にしていない(`data/openings/*.json` は実行時に読み込まれていない)。この差を埋める実装の着手時期は [PHASES.md](PHASES.md) を参照。

### 初心者への提示のしかた

戦法の名前は、認識がその段階に達してから初めて出す。

| 認識の段階 | ユーザーに述べてよいこと |
|---|---|
| 認識前(`none`) | 戦法の名前を出さず、観測した事実だけを述べる |
| `forming` | 戦法の名前を出さず、駒がどちらへ向かっているかという**動きの向き**だけを述べる |
| `matched` の初出 | ここで初めて戦法の名前を導入する。**必ず初心者向けの説明を添える**([../CLAUDE.md](../CLAUDE.md) のルール2番) |
| 認識が変わったとき | 前の認識を否定せず、**観測が増えた**とだけ述べる |

いずれの段階でも断定しない言い回しを既定とし([../CLAUDE.md](../CLAUDE.md) のルール6番)、認識結果を根拠に「だからこう指すべき」とは述べない。表示ブロックとしての責務境界は [ARCHITECTURE.md](ARCHITECTURE.md) 5. を参照。

**適用範囲(STEP ζ-3 で人間が確定)**: この表は**相手の狙いと自分の形の両方**に適用する。対局経過ブロックだけに限定しない。したがって既存の Phase 1 コーチ説明も、`forming` の段階では戦法・陣形の名前を出さない。

**`forming` では説明文も出さない(同)**: `data/intents/*.json` の `current_aim_explanation` / `next_aim_explanation` には本文中に戦法名を含むものがある(`naname_bogin`・`hayajikake`)。名前のプレースホルダだけを伏せても説明文から名前が漏れるため、`forming` ではこれらの説明文を表示しない。これらは `matched` の初出で名前を導入するときに初めて使う。

**各段階の具体的な文言**は [PHASES.md](PHASES.md) Phase 7「初心者向け説明の段階化の文言仕様(STEP ζ-3 で確定・人間承認済み)」にある。段階の判定は `apps/server/src/analysis/intentDetector.ts` の既存判定をそのまま使い、**新しい閾値を設けない**。一致率(`matchScore`)は表示にも段階判定にも使わない。

## 座標表記の規約

座標に関する設計は、**「座標形式(表記のフォーマット)」**と**「盤面上の意味・視点(その座標がどちら側の絶対座標か)」**という、別々の2つの設計事項として扱う。この2つを混同しないこと。

### 確定事項: 座標形式

内部データ(`shapes.required_pieces.square` / `shapes.typical_build_order` / `intents.recognition_pattern.to` / `explanations.move` など、盤面上のマス目・指し手を表す全フィールド)は、**将棋エンジン(やねうら王)およびshogiopsとそのまま連携できるUSI形式を正規形式とする**。日本語の将棋表記(「３二」「３六」など)をデータの正規値として保存しない。

USI形式は「筋(1〜9の数字)+段(a〜iのアルファベット)」で1マスを表す。段の対応は以下の通り。

| 日本語 | 一 | 二 | 三 | 四 | 五 | 六 | 七 | 八 | 九 |
|---|---|---|---|---|---|---|---|---|---|
| USI | a | b | c | d | e | f | g | h | i |

例: 「3二」→ `3b`、「3八」→ `3h`、「3九から3八への移動」→ `3i3h`。

ユーザー向け画面には、この正規形式から日本語表記への変換関数を通してから表示する(変換ロジックは実装時に `apps/server` または `apps/web` 側に置く。データ側で日本語表記を重複して持たせない)。

### 確定事項(MVPスコープ): 盤面上の意味・視点

この節では2つの異なる概念を区別する。

- **role(役割)**: `self`(自分) / `opponent`(相手)。将棋知識としての役割を表す概念で、`shapes.side` / `openings.side` などスキーマの `side` フィールドに対応する。**戦法ではなく陣営を表す**(どちらの陣営の形・狙いかであって、「四間飛車側」「居飛車側」という戦法上の区別ではない)。
- **color(盤面上の色)**: `sente`(先手) / `gote`(後手)。座標がどちら側の陣地を基準にした絶対座標かを表す概念。

MVPでは、**role=self(自分)を color=sente(先手)に固定し、role=opponent(相手)を color=gote(後手)に固定する**([CLAUDE.md](../CLAUDE.md) の「現在のスコープ(MVP)」を参照)。したがって、self側の形は先手の絶対座標として記録する。**この固定は先後(color)にのみ依存し、戦法には依存しない。** 戦法を対局開始前の設定として扱わなくなっても、先後の固定は維持されるため、この規約は変わらない。**この role↔color の固定はMVPスコープ上の決定であり、将来的にroleとcolorを分離して先後選択・先後可変を導入することを禁止するものではない**(その場合の座標正規化・先後反転の設計は将来判断)。

**現在の状態**: `data/shapes/*.json` の既存3件(`mino_honmino` / `mino_takamino` / `mino_ginkanmuri`)は、上記のMVP確定仕様(self=先手固定)に合わせて180度回転による変換が完了しており、先手側絶対座標で記録されている(変換の経緯は各ファイルの `source` フィールドを参照)。

**現在の状態(intents)**: `data/intents/*.json` の `recognition_pattern.to` について、座標規約レビューセッションで一次資料を確認した。`hayajikake` / `naname_bogin` / `boh_gin` はいずれも、引用元資料(Wikipedia『4五歩早仕掛け』『4六銀左戦法』『棒銀』、将棋大図書館『四間飛車対棒銀の定跡』)本文で居飛車側が▲(先手)として記述されていることを直接確認できたため、上記のMVP確定仕様(opponent=後手固定)に合わせて180度回転し、後手側絶対座標に変換済み(変換の経緯は各ファイルの `source` フィールドを参照)。`boh_gin` は当初、ゼロから始める将棋研究所『四間飛車vs棒銀①②』の本文には3筋の手順が見当たらず判断を保留していたが、別の一次資料(将棋大図書館・Wikipedia『棒銀』)で▲3七銀・▲3五歩が居飛車側(先手)の絶対座標として記述されていることを確認できたため、180度回転(3g→3f→3e を 7c→7d→7e に変換)して座標を確定した。

**要レビュー事項(残)**: 現時点で `data/intents/*.json` の座標レビューに未解決項目はない。

## 4つのスキーマ

### shapes(形)

囲い・陣形そのもの。自分が「目指せる形」としても、相手の陣形判定としても、同じ型を使う。

主なフィールド:
- `id` / `name` / `name_kana`: 識別子と表記
- `side`: `self`(自分側の目標になり得る) / `opponent`(相手の陣形判定用) / `both`
- `family`: 形のグループ(例: `美濃系`)。同じ family 内で `parent_shape_id` により発展関係(本美濃→高美濃→銀冠)を表す
- `required_pieces`: 完成に必要な駒と位置の一覧(必須/任意の区別つき)
- `typical_build_order`: 典型的な組み方の順序(道筋提示に使う)
- `characteristics` / `beginner_friendliness` / `weak_against`: 初心者向けの特徴説明、初心者向き度(1〜5)とその理由、弱点
- `source`: 参考にした出典
- `confidence_level`: 内容にどれだけ自信があるか(`high`/`medium`/`low`)
- `review_status`: 追加してよいかと見せてよいかを分離する運用区分(`draft`/`human_reviewed`/`expert_verified`)。定義は下記「運用区分 `review_status`」節を参照

### openings(戦型)

四間飛車・居飛車などの戦型。「対局シナリオ」(→ [SCENARIOS.md](SCENARIOS.md)。**開発・検証専用の機構**)もここに拡張する前提の器を用意している。

主なフィールド:
- `id` / `name` / `side`(`self`/`opponent`)
- `family`: 振り飛車系・居飛車系などの分類
- `leads_to_shape_ids`: この戦型がどの shapes(形)につながりやすいか
- `recognition_pattern`: この戦型を指し手の並びから認識するための手がかり(任意フィールド)。値を持たない戦型は認識の候補にならない。「飛車を初期位置から動かさない」のような否定的な条件は現在の表現では書けない(その表現方法は未確定であり、必要になった時点で人間の承認を経て決める)
- `scenario`: 対局シナリオ(AI序盤制御)の制御用データ(任意フィールド)。制御方式は「序盤の数手を `moves` の手順で強制進行させ、以降はエンジンに任せる」(人間承認済み)。`variants` に相手AIが毎局1つを選ぶ候補を持ち、各 variant は `target_intent_id` / `moves` / `verification_method` / `verification_status` / `verification_record` を持つ。**実データへの値の投入は、[KIND3_VERIFICATION.md](KIND3_VERIFICATION.md) の検証と Phase F の人間による最終採用判断を経てから行う(現時点では `null`)。** 詳細は [SCENARIOS.md](SCENARIOS.md)・[KIND3_VERIFICATION.md](KIND3_VERIFICATION.md)
- `source` / `confidence_level`
- `review_status`: 追加してよいかと見せてよいかを分離する運用区分(`draft`/`human_reviewed`/`expert_verified`)。定義は下記「運用区分 `review_status`」節を参照

### intents(相手の意図)

指し手の並びから読み取れる、相手の「今の狙い」と「次の狙い」。

主なフィールド:
- `id` / `name`(例: 棒銀) / `opening_id`(どの戦型に属する意図か)
- `side`: この意図がどちらの陣営のものか(`self`/`opponent`)
- `recognition_pattern`: 指し手の並びから意図を判定するための手がかり(例: 銀が特定の順で動く)
- `current_aim_explanation`: 初心者向けの「今何をしているか」の説明
- `next_aim_explanation`: 「次に何をしてきそうか」の説明
- `affects_target_shapes`: この意図がある場合、自分が目指す形の優先度をどう調整すべきか(例: 急戦相手には軽い形を優先)
- `confidence_level`: 判定の確からしさ。UI側の言い回し(断定 or 「〜かもしれません」)を左右する
- `review_status`: 追加してよいかと見せてよいかを分離する運用区分(`draft`/`human_reviewed`/`expert_verified`)。定義は下記「運用区分 `review_status`」節を参照

### explanations(説明)

パイプラインの②〜⑧のうち、ユーザーに見せる文章として出力される部分すべてに使う共通の型。「目的→手→理由」を構造として強制する。

主なフィールド:
- `id` / `stage`: パイプラインのどの段階の説明か(`current_shape` / `opponent_intent` / `opponent_next_aim` / `reachable_shape` / `candidate_move` のいずれか)
- `purpose`: 目的(なぜこれをするのか、初心者向け文章)
- `move`: 手(USI形式の指し手記法)。`stage` が `candidate_move` の場合のみ使う
- `reason`: 理由(その目的のためになぜその手/形が良いのか)
- `refers_to_shape_id` / `refers_to_intent_id`: 参照する shapes / intents の id
- `confidence_level`: 断定を避けるべきかどうかの判断材料
- `glossary_terms`: このテキストに含まれる将棋用語のキー一覧(UI側でツールチップ表示するため)

**位置づけ**: shapes / openings / intents は人間が整備する将棋知識データである。これに対し explanations は、局面ごとに内容が変わる(どの手を勧めるか等)ため、**主として実行時にロジック側(coach-logic-dev)が組み立てるコーチ出力のデータ契約**という性格が強い。`data/examples/explanations.example.json` は、このスキーマの形が実際にどう使われるかを示す実装確認用の最小サンプルであり、shapes/openings/intentsのように書き溜めていく完成教材データではない。

Phase1では、explanationsは単発の候補手説明(1レコード=1手)のみを扱う。複数手にまたがる「道筋」(Phase2で扱う機能)をexplanationsでどう表現するか(`path_id`・`step_order`のようなフィールドが必要になる見込み)は、Phase2着手時に改めて設計する。現段階ではスキーマに追加しない。

## 将棋知識の3分類

将棋知識は、**何を変えるものか**によって3種に分け、必要な手続きを変える。分類は「どのファイルを触るか」ではなく「何が変わるか」で決める。

| 種別 | 内容 | 例 | 手続き |
|---|---|---|---|
| **Kind 1 記述的知識** | 既存スキーマに準拠した新しいレコード。ロジック・閾値・スキーマ・UI上の意味付けを一切変えない | 新しい shape / intent / opening の追加 | **件数の制限はない。** 下記の露出制御を必須とする |
| **Kind 2 構造的知識** | スキーマの形式・フィールドの意味・参照関係の変更 | `openings` への `recognition_pattern` の追加 | 緩和しない。[AGENT_PROTOCOL.md](AGENT_PROTOCOL.md) 10. の Tier A + 人間承認。`data/schemas/*.schema.json` と本文書を**必ず同時に**直す |
| **Kind 3 判断的知識** | 判定結果・優先度・閾値・安全性・ゲーム挙動を変えるもの | `intents.affects_target_shapes` の `adjustment`、相手AIの着手選択、エンジンの利用範囲 | 緩和しない。**人間承認必須** |

**Kind 1 と Kind 3 の境界の判定規則**: 新しいレコードが `affects_target_shapes` を持つ場合は Kind 3 として扱う。持たない場合のみ Kind 1 とする。

**Kind 3 の検証方法**: 相手AI制御データ(`openings.scenario`)については、有段者レビューが得られない場合、[KIND3_VERIFICATION.md](KIND3_VERIFICATION.md) の多段階検証プロトコル + 人間による最終採用判断で代替できる。**これは検証方法の拡張であって、Kind 3 の定義および人間承認要件の緩和ではない。** AI検証は有段者レビューと同等の知識的保証を持つものではない。

**`review_status` との関係**: `review_status` は**ユーザーへの知識露出**を制御する。Kind 3 制御データの**検証・採用状態**はこれと**完全に分離して管理**し、一方の値から他方を導出しない。**AI検証済みを `human_reviewed` として扱わない。** `review_status` の3値は変更・追加しない。

**独立監査の指摘(併記)**: 現行スキーマでは shapes / openings のレコードに `affects_target_shapes` フィールドが無いため、新規の shape / opening は機械的にすべて Kind 1 と判定される。したがって、実際の安全網は下記の露出制御が単独で担っている。

## 運用区分 `review_status`(「追加の自由」と「ユーザーへの露出」を分ける)

知識を**追加してよいか**と、その知識を**ユーザーへ見せてよいか**を分離する。値は3種で、この3値の構成は STEP δ で司令塔が提案し、人間が追認した解釈である。

| 値 | 意味 | 現時点で該当するもの | ユーザーへの露出 |
|---|---|---|---|
| `draft` | AIが追加した未レビューの知識 | openings 2件・shapes 1件(`mino_ginkanmuri`) | **戦法・陣形・狙いの名前を断定的に見せる経路では使わない**(断定しない言い回しに留めるか、表示対象から外す) |
| `human_reviewed` | 人間のレビューを経たもの | shapes 2件(`mino_honmino`・`mino_takamino`)・intents 3件(STEP δ の確定記録に基づく) | 従来どおり |
| `expert_verified` | 有段者・一次資料による確認を経たもの | **0件**(人間の判断により保留中) | 従来どおり |

`mino_ginkanmuri` は `confidence_level: "low"` で一次資料未検証のため `draft` とする(STEP ε-2)。

AI は Kind 1 の知識を `draft` として**件数の制限なく**追加してよい。ただし `draft` の知識は上記の露出制御に従う。

**`draft` の表示方法(STEP ζ-3 で人間が確定)**: 上記の2択のうち、**「断定しない言い回しに留める」を採る。** 表示対象から外すと `draft` の形を目標形として選べなくなり、Phase 6 の既存機能を壊すためである。`draft` の名前を出す場合は「内容を確認中」の注記を必ず添える。具体的な文言は [PHASES.md](PHASES.md) Phase 7「初心者向け説明の段階化の文言仕様」の「`draft` の表示」を参照。

**露出制御の実装要件(同)**: `review_status` を、戦法・陣形・狙いの名前をユーザーへ出してよいかの**唯一のゲート**とする。名前を出す経路はすべて1つの関数を通し、[ARCHITECTURE.md](ARCHITECTURE.md) 6. の `toPublicGameState()` と同じ許可リスト方式にする(経路を新設しても既定では名前が素通りしないようにするため)。**ζ-3 の時点では `review_status` は `apps/` から一切参照されておらず、`draft` の `mino_ginkanmuri`(銀冠)が5経路で断定表示されている。** その一覧と是正要件は [PHASES.md](PHASES.md) Phase 7「初心者向け説明の段階化の文言仕様」の「露出制御の実装要件」にある。

**このフィールドは `data/schemas/shapes.schema.json` / `openings.schema.json` / `intents.schema.json` に必須フィールドとして追加済み(STEP ε)。** 必須化により未指定のレコードは構造上存在しなくなったが、`draft` を実際にどう扱うか(認識処理での利用可否など)の判断は今回のSTEPでは行っていない。今後の実装STEPで判断する。

**人間の判断(保留)**: shape座標の一次資料確認は保留中である。**有段者による確認が取れるまで、既存データを `expert_verified` にしない。** 「shape座標の一次資料が未検証」という既知事項([PHASES.md](PHASES.md))は、この区分の導入によって解消していない。

**露出制御文言の同期(記録)**: ζ-1 以前は、露出制御の対象に「陣形」を含まない文書が `CLAUDE.md`・[ROLES.md](ROLES.md)・[AGENT_PROTOCOL.md](AGENT_PROTOCOL.md)・[PROJECT_VISION.md](PROJECT_VISION.md)・`.claude/agents/shogi-content-curator.md` の5件あった。STEP ζ-1 でこの5件すべてを本文書・スキーマと同じ「戦法・陣形・狙い」に同期済みであり、露出制御上の文言差は現在解消している。Phase 7 の実装は、この同期済みの状態を前提としてよい。

## 検証・採用状態 `verification_*`(Kind 3 制御データ用)

Kind 3 の相手AI制御データ(`openings.scenario.variants[]`)が、検証を経て実運用に採用してよい状態かを管理する。手順は [KIND3_VERIFICATION.md](KIND3_VERIFICATION.md)。

| フィールド | 値 | 意味 |
|---|---|---|
| `verification_method` | `expert_review` / `ai_multi_stage` / `null` | どの方法で検証したか。`expert_review` は有段者レビューを実施した場合のみ |
| `verification_status` | `unverified` / `ai_verified` / `human_approved` | 検証・採用状態。**`human_approved` は人間のみが設定できる** |
| `verification_record` | object / `null` | 検証の記録(使用エンジン名・バージョン・探索条件・各Phaseの結果・不一致の有無・最終判断者・日付など) |

**`review_status` との関係**: `review_status` は**ユーザーへの知識露出**を制御し、`verification_*` は**制御データを実運用に使ってよいか**を制御する。**両者は完全に分離しており、一方の値から他方を導出しない。AI検証済みを `human_reviewed` として扱わない。**

**保持単位**: variant 単位で持つ。[KIND3_VERIFICATION.md](KIND3_VERIFICATION.md) が「検証単位は1つの狙い = 1本の手順列」と定めているため。

**`verification_record` の中身を固定しない理由**: 記録項目が運用の中で変わりうるため、`additionalProperties: true` とする(他のスキーマが `additionalProperties: false` を採っているのに対する例外であり、人間の承認を経ている)。

**運用規則**:

- AI検証で問題が確認された場合、`verification_status` を `unverified` へ戻す(`review_status` は触らない)
- 有段者レビューが後日可能になった場合、`ai_multi_stage` から `expert_review` への追認・格上げができる
- **未承認の Kind 3 制御データが実運用に入らないゲートを実装要件とする**(実装方式は今後のSTEP)

## 用語集データについて

初心者向けの用語説明(用語集)は、上記4スキーマとは別に既存の `glossary.json`(v0.1設計時に構想)を継続利用する想定で、今回は新規にスキーマ化しない。`explanations.glossary_terms` はこの用語集のキーを参照する形にする。

## IDの参照関係

`intents.opening_id` → `openings.id`、`explanations.refers_to_shape_id` → `shapes.id`、`explanations.refers_to_intent_id` → `intents.id`、`openings.leads_to_shape_ids` → `shapes.id[]`、`shapes.parent_shape_id` → `shapes.id`、`openings.scenario.variants[].target_intent_id` → `intents.id`(**この参照は検証時のテスト・オラクルとしてのみ使い、実行時のAI制御手順の生成・選択には使わない**)。参照先が存在しないIDを書かないこと(将来 `scripts/validate-data.mjs` で機械チェックする。[TESTING_STRATEGY.md](TESTING_STRATEGY.md) 参照)。
