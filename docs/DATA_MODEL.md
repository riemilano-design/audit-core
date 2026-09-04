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
   │  (intents の next_aim フィールド。③の延長線上の予測)
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

### openings(戦型)

四間飛車・居飛車などの戦型。将来の「対局シナリオ」(→ [SCENARIOS.md](SCENARIOS.md))もここに拡張する前提の器を用意している。

主なフィールド:
- `id` / `name` / `side`(`self`/`opponent`)
- `family`: 振り飛車系・居飛車系などの分類
- `leads_to_shape_ids`: この戦型がどの shapes(形)につながりやすいか
- `scenario`: 将来の対局シナリオ拡張用の任意フィールド。**現段階では値を入れない。** 詳細は [SCENARIOS.md](SCENARIOS.md)
- `source` / `confidence_level`

### intents(相手の意図)

指し手の並びから読み取れる、相手の「今の狙い」と「次の狙い」。

主なフィールド:
- `id` / `name`(例: 棒銀) / `opening_id`(どの戦型に属する意図か)
- `recognition_pattern`: 指し手の並びから意図を判定するための手がかり(例: 銀が特定の順で動く)
- `current_aim_explanation`: 初心者向けの「今何をしているか」の説明
- `next_aim_explanation`: 「次に何をしてきそうか」の説明
- `affects_target_shapes`: この意図がある場合、自分が目指す形の優先度をどう調整すべきか(例: 急戦相手には軽い形を優先)
- `confidence_level`: 判定の確からしさ。UI側の言い回し(断定 or 「〜かもしれません」)を左右する

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

## 用語集データについて

初心者向けの用語説明(用語集)は、上記4スキーマとは別に既存の `glossary.json`(v0.1設計時に構想)を継続利用する想定で、今回は新規にスキーマ化しない。`explanations.glossary_terms` はこの用語集のキーを参照する形にする。

## IDの参照関係

`intents.opening_id` → `openings.id`、`explanations.refers_to_shape_id` → `shapes.id`、`explanations.refers_to_intent_id` → `intents.id`、`openings.leads_to_shape_ids` → `shapes.id[]`、`shapes.parent_shape_id` → `shapes.id`。参照先が存在しないIDを書かないこと(将来 `scripts/validate-data.mjs` で機械チェックする。[TESTING_STRATEGY.md](TESTING_STRATEGY.md) 参照)。
