# Core 接続 C-2(将棋の c5 Golden Master を薄い Python Adapter で Core に繋ぐ、H-9 の並走再現)の結果

**日付**: 2026-10-06 **封**: [CORE_CONNECTION_C2_PLAN_2026-10-06.md](CORE_CONNECTION_C2_PLAN_2026-10-06.md)(`82a1ab0`、不変)+ 人間の決定 [DECISIONS](CORE_CONNECTION_C2_PLAN_2026-10-06_DECISIONS.md)(`f1baa15`) **監査**: GO(独立の監査。Core/将棋側の不変を sha と grep で確認、canonical を自分で 15 値 TS と突き合わせ、213 件を独立に突き合わせて 0 不一致、別 seed の手検査 10/10、自作変異 2 本が赤。問題点なし) **コミット**: `922126b`(Adapter + 試験 + 計測の道具 2 本 + 1 回目の出力 2 本)

## 1. 何を作ったか(全部 `audit-core/` の中。Core 0 行、将棋側 0 行)

| 置き場所 | 中身 |
|---|---|
| `adapters/shogi/` 7 本 **601 行** | `packet_ref.py`(TS `packetRef.ts` の正規表現 2 本を値で写す)、`canonical.py`(TS `canonicalJson` と同値の Python 版。数の書式は ECMA-262 の `Number::toString` を実装)、`resolve.py`(TS `resolvePacketPath` と同じ順で引き、失敗を 5 種に分類)、`comparators.py`(`canonical_json_equals`)、`recipes.py`(観測 1 件 = Claim 1 件)、`registry_setup.py`(登録 8) |
| `fixtures/shogi/` 2 本 | `run_core_path_shogi.py`(Core の経路の計測の道具。registry 欄は登録簿から数える)、`h9_reference.ts`(**監査専用・参照専用の独立オラクル**。TS の `validateHypothesisLine` を packet つきで呼び H-9 の結果を観測ごとに `ok / value_mismatch / recount / not_found` に分ける。将棋の lib は import するだけ) |
| `tests/adapters/shogi/` 11 本 | 試験 **73 本**(系譜 = packetRef.ts をファイルとして読み正規表現を字で比較、canonical は TS の実出力を字で書いた期待値、resolve の 5 種、recipes、registry、Core 経由の end-to-end)+ 変異 6 本(S-R1〜R5 red・S-G1 green、全部予測どおり) |

## 2. 門(司令塔が凍結時点で測った。凍結 = 20 ファイルの sha 一覧)

| 門 | 結果 |
|---|---|
| Core 4 本の sha | `f917f02` から不変 |
| XBRL Adapter・`scripts/playtest/`・`apps/`・`data/`・`docs/` | 差分 0 |
| Core に将棋固有の文字列(packet / aggregates / facts / gameId / hypothesis) | **0 件**(grep) |
| `tests/adapters/shogi` | 73 OK、変異 6/6 |
| 全体 `unittest discover` | **336 OK**(260 + 73 + 同時に作業中の v2 の束 3) |
| `h9_reference.ts` の型検査 | `scripts/playtest/tsconfig.json` を extends した一時 tsconfig(gitignore の `out/` に置く)で `tsc --noEmit` **rc=0** |
| c5 Golden Master(計器 2) | **rc=0**(将棋側 0 行なので自明。それでも回した) |
| 登録(計器 4) | Adapter 分 **8**(scheme `packet` 1・比較子 1・理由 6)。`register_all` 後の登録簿は builtin/equals を含めて 2/2/0/6 |

## 3. 1 回目の計測(司令塔が凍結の後 18:43 に 1 回ずつ)

出力: `fixtures/shogi/c2_first_run_h9_reference.json`(TS、sha `c0932f3d…`)と `fixtures/shogi/c2_first_run_core.json`(Core の経路、sha `9b922ef3…`。入力の sha = packet `1c43582b…` と席の封筒 5 本を記録。**文(statement)は書いていない**)。

### 3.1 数(計器 6 の本体)

| 項目 | 実測 |
|---|---|
| Claim | **321**(packetRef あり 213 + 反証の観測 108) |
| form | AGGREGATE **253** / DIRECT_VALUE **68** |
| 213 件の state | **GROUNDED 192・VALUE_MISMATCH 20・POINTER_NOT_FOUND 1** |
| 108 件 | 全部 UNVERIFIABLE `no_packet_ref(H-9 out of scope)` |
| TS の H-9(packet つき)の kind | ok 192・value_mismatch 20・not_found 1・recount 0 |
| **観測 1 件ごとの対応** | **213 / 213 一致**(ok ↔ G、value_mismatch ↔ VM、not_found ↔ PNF) |
| 修飾(population / time_range / normalization) | **321 件とも空** |
| 手検査 GROUNDED 10 件(seed 20261006、Adapter を使わず packet を直接たどる) | **10 / 10** 一致(証拠の層の false pass 0) |

### 3.2 VALUE_MISMATCH 20 件と POINTER_NOT_FOUND 1 件の中身(packet を直接読んで確かめた)

| 件数 | 場所 | 何が違うか |
|---|---|---|
| **18** | `facts.recognition.rows[n].names`(n = 0・3・12・16・23。席の封筒 5 本すべてに出る) | packet の `names` は**配列**(例: `["英ちゃん流中飛車","5筋位取り中飛車","角換わり腰掛け銀"]`)。席は `"英ちゃん流中飛車+5筋位取り中飛車+角換わり腰掛け銀"` と **1 本の文字列に潰して写した**。canonical JSON では配列と文字列は一致しない。**表現の差**(値の層の誤りではないが、「packet のその場所の値」ではない) |
| **2** | `aggregates.branches.shallowVisibleGames.value`(席 25 / packet **24**)、`aggregates.groups.other.aheadThenLost.denominator`(席 2 / packet **4**) | **数そのものが違う。** 席が packet に無い数を書いた。TS の H-9 も同じ判定 |
| 1(PNF) | `facts.recognition.rows[3].reviewStatus` | `reviewStatus` は `rows` に無く `definitions` 側の欄(`hypothesis.ts` の H-10 の注のとおり)。`missing_key` |

**この 2 + 18 件は c5 の Golden Master では見えていなかった。** Golden の `hypothesisCheck` は packet を渡さずに回っていて H-9 が 58 件とも skip(「未照合」)だったから。TS の検証器自体は正しく判定する(今回 packet を渡したら捕まえた)。**H-9 を packet つきで回していなかったことが、顧客の冊子の工程の穴**として記録に残る(直すのは将棋側の判断。C-2 では触らない)。

### 3.3 予測との照合

| # | 予測 | 実測 | 判定 |
|---|---|---|---|
| P-1 | Core diff 0 | 0 | 当たり |
| P-2 | 登録 8 | 8 | 当たり |
| P-3 | 拡張 0・意味変更 0 | 0・0 | 当たり |
| P-4 | Core に将棋固有の文字列 0 | 0 | 当たり |
| P-5 | 文字列の値は `params["expected"]` で Core を変えずに通るが `recomputed` が None になり、拡張の候補 1 件 | そのとおり。**VM 20 件のうち 18 件は文字列(配列)で、Result の `recomputed` は None、何と何を比べたかは `detail` にしか無い** | 当たり(候補が実物で見えた) |
| P-6 | Claim 321 | 321 | 当たり |
| P-7 | form 253 / 68 | 253 / 68 | 当たり |
| P-8 | 213 件: G 200〜213・VM 0〜8・PNF 0〜5、grammar 0、出るなら no_field か index | **G 192・VM 20**・PNF 1、grammar 0、理由は **missing_key** | **外れ 2 欄**(G が下、VM が上)。原因: 「席は写すので一致する」を文字列 23 件にも当てはめた。実際は 23 件中 18 件が配列→文字列の潰しで VM。方向(「文字列が危ない」)は書いていたが大きさを外した。PNF の理由の種類も外した(欄としては当たりの範囲内) |
| P-9 | TS と 213/213 一致 | 213/213 | 当たり |
| P-10 | 数え直しの problems 0 | ok 192 件では 0(= 数え直しの苦情も無い)。**VM 20 件では未観測**(参照の道具が value_mismatch を recount より優先して kind を 1 つにする) | 半分当たり(192 件)・半分未測(20 件)。次に参照の道具に messages を残す |
| P-11 | 修飾 321 件とも空 | 空 | 当たり(**H-9 の断面では空だった、まで。** 「将棋では不要」と一般化しない = 人間の注意) |
| P-12 | 手検査 10 件 false pass 0 | 10/10 | 当たり |
| P-13 | Adapter 250〜450 行・試験 +20〜35・変異 +4〜6 | **601 行・+73**・+6 | **外れ 2 欄**(canonical の数値書式 134 行と resolve の分類 153 行を見積もりに入れていなかった。試験は canonical の値ごとの試験が多い) |
| P-14 | Golden Master rc=0 | rc=0 | 当たり |
| P-15 | 違う項目 1〜2 | 2(P-8・P-13) | 当たり(ぎりぎり) |

**集計**: 15 項目中 当たり 12・外れ 2(P-8・P-13、各 2 欄)・半分 1(P-10)。**封じた予測は変えていない。実装を予測に寄せていない。**

## 4. C-2 が証明したこと・しないこと(人間の決定の範囲で読む)

証明した(人間が認めた 3 点):

1. 将棋側の既存 H-9 の意味(観測 → packetRef → canonical 一致 → 3 結果)を Adapter で取り出せた。
2. Core の既存 `verify_all` で同じ結果が出た(213/213)。
3. Core を将棋固有に変えなくてよかった(diff 0、登録追加 8 だけ)。

証明していない: Core の汎用性(213/213 は「席が写した値が packet に在る」ことの再確認で、Core の手柄ではない。§7 のとおり)。修飾が将棋で不要なこと(H-9 の断面では空だった、まで)。将棋の門を Core 経由に置き換えられること(今回は並走で、置き換えはしていない。計器 1 の関数レベル Golden は未測)。

**C-1 と並べて言えること**: XBRL(3 社、修飾 3 つが実際に出る)と将棋(修飾が全部空)という意味の濃さの違う 2 つの Adapter が、同じ Core の 4 層・4 状態・同じ `verify_all` で動き、Core の変更は C-1b 以降 **0**。「XBRL 専用の抽象だった」という反証には耐えた。耐えたのは**この 2 つに対して**であり、3 つ目(会議データなど)で同じことが言えるかは測っていない。

## 5. 手順との差・道具の記録

1. **実装担当が作業中に `git stash -u` → `pop` を実行**(18:29。目的: きれいな HEAD での試験本数の確認)。共有の作業木から、並行して監査中だった別の束(v2、5 ファイル)と自分の未追跡ファイルが数分間消え、監査が「対象が無い」で HUMAN 判定になった。pop 後に司令塔が凍結 sha 一覧で全件一致を確かめ、変異の項目だけ再依頼した。**次からは実装担当・監査担当への指示に「作業木を書き換える git 操作(stash / reset / checkout -- / clean / restore / add)を使わない」を毎回書く**(記憶に残した)。実装担当は指摘後やっていない。
2. `h9_reference.ts` の型検査は `npm run typecheck:scripts` の対象外(audit-core 配下)。gitignore の `out/` に一時 tsconfig を置いて単体で通した(rc=0)。恒久の門にするなら tsconfig の include の判断が要る(将棋側の設定なので C-2 では触らない)。
3. `h9_reference.ts` は kind を 1 つに潰す(value_mismatch > recount > not_found)。VM の観測に数え直しの苦情が併発していても見えない。次は messages をそのまま残す欄を足す(P-10 の半分未測の原因)。
4. 今回の計測で席の封筒 5 本(個人の対局の数・形の名前)の sha と、観測の値(数・名前の文字列)が `c2_first_run_core.json` に入る。文は入れていない(人間の決定 8.3 のとおり)。

## 6. 次に直す物・決める物(この段では触っていない)

1. **将棋側**: `hypothesisCheck` に packet を渡して H-9 を本当に回す(Golden Master の H-9 skip 58 件を無くす)。今回の 20 件(数の誤り 2・表現の差 18)が最初の材料。将棋側の判断。
2. **参照の道具**: messages を残す(§5.3)。
3. **Core の判断材料(人間)**: 文字列の値を Claim/Result がどう持つか(P-5 の候補)。`Claim.value: Optional[float]` のままにして `params`/`detail` で持つか、型を広げるか(インターフェース拡張 1)。C-2 では変えていない。
4. **C-1 計画 §7 の決定 3**(将棋の門を Core 経由に置き換えるか・言語)と **repo の切り出し**(C-0 §6)は、この結果を読んで人間が決める。

## 7. この文書がしないこと

Core の変更。将棋側の変更。213/213 を汎用性の証明と読むこと。
