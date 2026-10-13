# 稼働の入口(1 書類を検証して Claim ごとの state・pointer・reason を返す)

作成: 2026-10-13。人間の決定(第 3 段階)「まず内部道具として、入力から判定までを一貫して動かす入口を 1 本作る。顧客向けの形・P17・規則の追加はやらない」。

## 0. なぜ要ったか

main には、**文と XBRL を入れて 4 状態と pointer を返す本番の入口が無かった。** `adapters/xbrl/run.py` は Claim の層(結果なし)を書くだけで、判定まで回す経路は試験の補助(`tests/golden/_instrument.py`)と日付つきの測定道具にしかなかった。P16 は測定の中では動いていたが、「システムとして稼働」には入口が欠けていた。

## 1. 何を作ったか

| file | 中身 |
|---|---|
| `adapters/xbrl/verify_document.py` | 入口。`load_instance → make_resolver → register_all → build_recipes → verify_all` を**試験の補助と同じ順**で呼ぶ。足したのは書類レベルの旗 1 つだけ |
| `adapters/xbrl/prose.py` | 経営分析の節を渡された文章で差し替える。日付つき道具 `fixtures/xbrl/ai_prose_claims_2026-10-09.py` の `prose_to_html`・`build_modified_zip` を**中身を変えずに**写した。**変えたのは止め方だけ**(`SystemExit` → `ProseReplacementError`)。日付つき道具は 1 行も触っていない |
| `fixtures/xbrl/build_entry_golden_2026-10-13.py` + `entry_golden_ai_prose_2026-10-13.json` | 入口の期待値。**入口の出力からは作っていない**(`tests/golden/_instrument.run_verification` で作った。入口の出力から作ると同語反復になる) |
| `tests/adapters/xbrl/test_verify_entry.py` | 23 本 |

**新しい判定規則は 1 つも入れていない。** 既定 profile は `vocabulary.DEFAULT_PROFILE`(= P16、第 2 段階で人間が決めた)。

### 1-1 書類レベルの旗(人間が承認した文面そのまま)

> Claim 件数が 0 件の場合、書類レベルを UNVERIFIABLE とする。Claim 件数が 1 件以上の場合、GROUNDED 件数が 0 件、かつ POINTER_NOT_FOUND 件数 ÷ 全 Claim 件数が 0.5 を超える場合、書類レベルを UNVERIFIABLE とする。それ以外は、この規則によって UNVERIFIABLE とは判定しない。Claim 個別の state は変更しない。

`verify_document.DOC_UNVERIFIABLE_RULE` に字で置き、試験が字そのものを留める。分母は**全 Claim 件数**(人間の決定)。

## 2. 完成条件に対する実測 [測定]

| # | 条件 | 実測 |
|---|---|---|
| 1 | 既存の測定との**意味の一致** | 開発書類の AI 文: P7 415 件・P13 412 件・P16 412 件の全行で (state, pointers, reason, subject) が golden と一致。P16 の内訳は記録どおり G 330 / VM 25 / PNF 16 / UV 41。未使用 2 書類: 限定確認の commit 済み dump と、行の鍵 → claim id の対応表を経由して全行一致(103・150 行)。14 書類の止めた件数は §2-3 の表と一致 |
| 2 | **入力**の再現性 | 文章を差し替えた ZIP の sha256 = 封じた値 `03521437…4799`(日付つき道具が作った値) |
| 3 | **出力**の再現性 | 同じ入力を 2 回処理して byte 一致。さらに 1 書類(S100Z4B6)の本体の sha256 を字で留めた(engine の指紋は adapters の .py が変わると動くので除く)。字下げを変える変異で赤くなる |
| 4 | 書類レベルの UNVERIFIABLE | S100Z3HP(PNF 57/62 = 0.92)・S100Z433(77/87 = 0.89)で真、未使用 2 書類と他で偽。ちょうど 0.5 は偽、GROUNDED 1 件で偽、PNF の無い停止では偽 |
| 5 | CLI から実際に JSON が出る | 原文 1 件と AI 文 + ZIP 1 件を回した。出力は §4 |
| 6 | 独立監査の GO | §6。GO、所見 2 件。ただし §5 の境界の直しは GO の後なので、別の監査席に独立に当てた(結果は §5 末尾) |

全試験(枝の木、境界の直しの後)[測定]: pytest **885 passed**(main 3e08f5c の 859 + 入口 23 + 境界の守り 3)、unittest discover **Ran 789 OK**。直す前は `1 failed, 881 passed` / `Ran 786, FAILED (failures=1)`(§5)。

### 2-1 変異(壊したら赤くなるか)[測定]

| 変異 | 予測 | 実測 |
|---|---|---|
| 閾値 0.5 → 0.9 | 旗の試験が赤 | 3 本赤(規則の字・合成・実書類) |
| Claim 0 件の枝を消す | 1 本赤 | 1 本赤 |
| 差し替え**前**の ZIP で recipes を作る | 意味の一致が赤 | 4 本赤 |
| 出力の字下げを変える | 字で留めた sha が赤 | 1 本赤 |
| 1 行 1 段落をやめる | 差し替えの試験が赤 | 3 本赤(封じた sha を含む) |

恒等(変異なし)と復元後はどちらも 23 本緑。pyc は変異ごとに新しい置き場で測った。

## 3. 使い方

```bash
# 原文の書類(既定 profile = P16)
python3 -m adapters.xbrl.verify_document --doc S100Z4N9 --out out.json
# 書類の ZIP を道で渡す
python3 -m adapters.xbrl.verify_document --zip ~/.cache/audit-core/edinet/S100Z4N9.zip --out out.json
# 文章を渡して経営分析の節を差し替えて検証する
python3 -m adapters.xbrl.verify_document --doc S100Z4Q1 --text fixtures/xbrl/ai_prose_2026-10-09.txt --out out.json
```

出力の頭に tool 名・engine の指紋(adapters/xbrl と Core の .py の sha256。git の commit は取れなければ `null`)・profile・入力の sha256・差し替えた要素名、`document` に件数の内訳と旗と規則の字、`claims` に Claim ごとの 12 欄。

## 4. 実際に回した 2 通り [測定]

| 入力 | Claim | 内訳 | 書類レベル |
|---|---|---|---|
| S100Z4N9(原文) | 186 | G 99 / VM 53 / UV 28 / PNF 6 | 偽 |
| S100Z4Q1 + AI 文(`ai_prose_2026-10-09.txt`) | 412 | G 330 / VM 25 / UV 41 / PNF 16 | 偽 |
| S100Z3HP(原文、参考) | 62 | PNF 57 / UV 5 | **真** |

## 5. 全試験で初めて赤くなった境界の試験(そのまま報告) [測定]

入口だけの試験 23 本は緑だったが、**全試験を回して 1 本赤くなった**。

```
FAILED tests/adapters/xbrl/test_boundary.py::CoreImportBoundaryTest::test_only_recipes_and_run_import_core_among_adapter_files
AssertionError: Lists differ: ['verify_document.py'] != []
1 failed, 881 passed in 1087.14s   (unittest discover: Ran 786, FAILED (failures=1) ― 同じ 1 本)
```

main が前から持っている保護条件で、**`adapters/xbrl` のどのファイルが Core を
import してよいか**を一覧で留めている(許可 = `recipes.py`・`run.py`・
`comparators.py`・`resolve.py`・`registry_setup.py`、禁止 = `edinet.py`・
`instance.py`・`extract.py`・`vocabulary.py`・`__init__.py`)。入口は
`core.Registry.default()` と `core.verify_all` を呼ぶので、この一覧に無い
6 本目として赤くなった。`prose.py` は Core に触らないので赤くない。

**判断(司令塔、2026-10-13)**: 許可の一覧に `verify_document.py` を足す。根拠は、
この規則が守っているのは「**データの層が Core に触らない**」ことであり、禁止の
5 本は 0 件のまま変わらないから。`run.py` は main の中で
「`audit_core.verify_all` の入口になる予定」と自分の字で書きながら(`# noqa: F401`
の注記)結果の層を書いていない。入口はその予定の 1 本であって、新しい層ではない。

**ただし「import してよい」が「Core を何にでも使ってよい」に広がらないよう、
同じ commit で守りを 3 本足した**(許可を 1 つ緩めた分の歯止め)。

| 足した試験 | 何を留めるか |
|---|---|
| `EntryCoreUsageTest::test_the_allow_list_is_pinned_literally` | 許可の一覧を字で留める。黙って増やせない |
| `EntryCoreUsageTest::test_the_entry_uses_only_the_two_pinned_core_names` | 入口が Core から使う名前は `Registry` と `verify_all` の **2 つだけ**(AST で `import audit_core as <別名>` の別名を追い、属性の読みを数える) |
| `EntryCoreUsageTest::test_the_data_layer_is_still_forbidden` | 禁止の 5 本が減っていない・許可と交わらない |

変異 3 本(ファイルごとに新しい bytecode の置き場、`-B -p no:cacheprovider`)[測定]

| 変異 | 予測 | 実測 |
|---|---|---|
| 入口に `core.Claim` を足す(3 つ目の名前) | 2 つ目の試験が赤 | 1 本赤(予測どおり) |
| `core.verify_all(...)` を `getattr(core, "verify_all")(...)` にする(走査の迂回) | 同じ試験が赤(集合が縮む) | 1 本赤(予測どおり。字面の走査は迂回できるが、**等号**で留めているので縮んでも赤くなる) |
| 許可の一覧に `instance.py` を足す | 1 本目と 3 本目が赤 | 2 本赤(予測どおり) |

変異のあと `shasum -a 256` で 2 ファイルが元に戻ったことを確かめ、12 本が緑。

**この直しは最初の独立監査の GO の範囲外**(監査は全試験が終わる前に GO を返しており、
この赤を見ていない)。そのため**別の監査席に独立に当てた → GO**(問題点なし)。
監査席が独立にやったこと: 禁止 5 件と Core→adapters 不可の試験が無傷であることを diff で確認 /
入口が Core から使う名前を自分で数えて 2 つ /
私の 3 本とは別の変異 2 本 ― `from audit_core import Claim` を足す(ImportFrom の経路)→ 1 本赤、
許可の一覧から既存の `recipes.py` を外す → 2 本赤(既存の試験と字で留めた試験) ―
ともに予測どおり、`shasum -a 256` で復元を確認、35 本緑 /
代替案(`run.py` に統合・Core を引数で注入)は独立に検討して「今回は優れていない」。
既知の限界として、静的な走査は `getattr(core, "<任意>")` の動的な迂回までは
見ない(既存の `_imports_audit_core` と同じ限界)。

## 6. 独立監査 [記録]

判定 **GO**。監査席が独立にやったこと。

- golden を自分で作り直し、commit 済みの `entry_golden_ai_prose_2026-10-13.json`
  と全行一致を確認(P7 415 / P13 412 / P16 412 行)。
- 私が使った 5 本とは**別の変異 2 本**: pointer の並びを反転 → 5 本赤、
  書類レベルの旗の呼び出しを外す → 1 本赤。
- CLI を別の書類で実行(S100Z4B6、123 件・停止 58 件)。堅牢性の表の行と一致。
- `recipes.py`・`vocabulary.py`・`core/py/audit_core` に対して差 0 行
  (入口は既存の判定に触っていない)。

**所見 2 件(GO を変えないが、将来のための注意)**

1. `document_level(counts, total)` は分母を引数で受けるので、呼び出し元が増えた
   ときに誤った分母を渡せる。いまの呼び出し元は 1 か所で `total = len(claims)`。
2. `engine_fingerprint()` の `core_py_sha256` はディレクトリ直下の `.py` だけを
   見る。Core は今 4 ファイルで平らなので一致するが、将来サブディレクトリが
   できたら指紋に入らない(件数 `core_py_files` にも出ない)。

**監査が見ていないもの**: §5 の境界の試験の赤と、その直し(許可の一覧 + 守り 3 本)。
監査の GO はそれより前の状態に対するもの。

## 7. していないこと

- 顧客向けの形(PDF・画面・レポートの文)。
- P16 の規則の変更、新しい profile、方向の主張の別扱い、千円のずれの許容。
- 運用の監視(定期に 100 件を抜いてラベルする仕組み)。
- 旗以外の書類レベルの判断。
