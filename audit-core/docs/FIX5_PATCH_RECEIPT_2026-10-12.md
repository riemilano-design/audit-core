# fix5 提案 patch の受領記録(2026-10-12、司令塔)

D-001(`docs/DECISION_LOG.md`)に基づき、並行席(セッション「Audit Core XBRL抽出器の修正」)が用意した
**保護面 6 ファイルの提案 patch** を受け取り、**司令塔が自分の木で検証した**。merge していない。main の保護面は不変。

## 相手の申告 と 司令塔の実測(すべて一致)

| 項目 | 申告 | 実測(コマンド) |
|---|---|---|
| commit | `a18612a`(fix5 枝のみ) | `git branch --contains a18612a` → `feature/audit-core-xbrl-fix5` のみ |
| patch の sha256 | `74e70074aa8d5f5b0f1c67d59c13f470186ececcac102fb00ff2aa8384ee2b50` | `git show a18612a:audit-core/patches/fix5_protected_surface_2026-10-12.patch \| shasum -a 256` → 同じ |
| 大きさ | 91,873 B・41 hunk・6 ファイル | 91,873 B・`grep -c '^@@'` 41・`diff --git` 6 本 |
| 対象 | `comparators.py` `extract.py` `instance.py` `recipes.py` `registry_setup.py` `vocabulary.py` | 同じ(すべて `audit-core/adapters/xbrl/`。**Core は 0 ファイル**) |
| main に当たるか | `git apply --check` rc=0 | 使い捨ての detached worktree(main)で rc=0、`--stat` 6 files, +1,338 / −62。worktree は `remove --force` 済み |
| 測定 JSON | 含めない | 含まれていない |

## この patch の扱い(D-001 の原文どおり)

- **merge しない。** 保護面の sha `490888d4…`(22 ファイル)は変わらない。
- 手順 ① の原因内訳が、この patch が直す型(相手の申告: 丸め `doc_rounding` 61 / `target_both` 4、束縛 §7a-c・§8・S1・S3 計 27、語彙 S4 2 ― **いずれも相手の 4 書類での孤立した件数**で、391 件への効果は**未測定**)と一致した場合にのみ、手順 3 で**最初の候補**として main 上で封じ、391 件を未見の標本として当てる。
- A1(差の金額照合)は相手側で 2026-10-09 に FAIL/棄却済みで**この patch にも入っていない**。`comparators.py:289` の `abs(difference)`(符号を落とす)は**未実装のまま残っている**と相手が申告 ― 封B の観点から、取り込むときは成功条件に入れる。
- 相手の件数は台帳に載せない(4 書類の測定記録として fix5 枝に残る)。

## 注入道具の席(`feature/audit-core-injection-roleless`)

生きたセッションは見つからない(相手の `ListAgents` でも、司令塔の `ListAgents` でも)。
`S100Z39P`・`S100Z4N9` の確保(D-002)は、その枝の記録と矛盾しない(同枝 `fetch_material.py` の「未開封は S100Z39P・S100Z4N9 の 2 件」)。
