# audit-core

AI が出した文章の主張(Claim)を、証拠(Evidence)へのポインタと契約(Contract)で機械が照合し、GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND / UNVERIFIABLE の 4 状態で返す監査の Core。将棋の対局後診断(このリポジトリの `scripts/playtest/`)が最初の顧客、EDINET の XBRL が 2 番目。

- 設計の正本: [docs/CLAIM_CONTRACT_SPEC_v0.2.md](docs/CLAIM_CONTRACT_SPEC_v0.2.md)(4 層)。経緯と封じた予測は [docs/](docs/)(README の一覧は [../docs/README.md](../docs/README.md))。
- 接続の工程: [docs/CORE_CONNECTION_C0_2026-10-06.md](docs/CORE_CONNECTION_C0_2026-10-06.md)(封印)→ [docs/CORE_CONNECTION_C1_PLAN_2026-10-06.md](docs/CORE_CONNECTION_C1_PLAN_2026-10-06.md) → [docs/CORE_CONNECTION_C1C_PREDICTION_2026-10-06.md](docs/CORE_CONNECTION_C1C_PREDICTION_2026-10-06.md)(C-1c の予測、封印) → [docs/CORE_CONNECTION_C1C_RESULT_2026-10-06.md](docs/CORE_CONNECTION_C1C_RESULT_2026-10-06.md)(C-1c の結果、066eb13) → [docs/CORE_CONNECTION_C1D_PREDICTION_2026-10-06.md](docs/CORE_CONNECTION_C1D_PREDICTION_2026-10-06.md)(C-1d の予測、封印) → [docs/CORE_CONNECTION_C1D_RESULT_2026-10-06.md](docs/CORE_CONNECTION_C1D_RESULT_2026-10-06.md)(C-1d の結果、25f33e9) → [docs/CORE_CONNECTION_C1E_CLASSIFICATION_2026-10-06.md](docs/CORE_CONNECTION_C1E_CLASSIFICATION_2026-10-06.md)(C-1e 分類、C-1 の締め) → [docs/CORE_CONNECTION_C1F_PREDICTION_2026-10-06.md](docs/CORE_CONNECTION_C1F_PREDICTION_2026-10-06.md)(C-1f 癖の直しの予測、封印) → [docs/CORE_CONNECTION_C1F_RESULT_2026-10-06.md](docs/CORE_CONNECTION_C1F_RESULT_2026-10-06.md)(C-1f の結果、bd0e62b) → [docs/CORE_CONNECTION_THIRD_PREDICTION_2026-10-06.md](docs/CORE_CONNECTION_THIRD_PREDICTION_2026-10-06.md)(3 社目の予測、封印) → [docs/CORE_CONNECTION_THIRD_RESULT_2026-10-06.md](docs/CORE_CONNECTION_THIRD_RESULT_2026-10-06.md)(3 社目の結果) → [docs/CORE_CONNECTION_C1G_PREDICTION_2026-10-06.md](docs/CORE_CONNECTION_C1G_PREDICTION_2026-10-06.md)(C-1g の予測、封印) → [docs/CORE_CONNECTION_C1G_RESULT_2026-10-06.md](docs/CORE_CONNECTION_C1G_RESULT_2026-10-06.md)(C-1g の結果、3afd0ba) → [docs/CORE_CONNECTION_C2_PLAN_2026-10-06.md](docs/CORE_CONNECTION_C2_PLAN_2026-10-06.md)(C-2 の計画と予測、封印。実装は C-1g の後) → [docs/CORE_CONNECTION_C2_PLAN_2026-10-06_DECISIONS.md](docs/CORE_CONNECTION_C2_PLAN_2026-10-06_DECISIONS.md)(§8 への人間の決定) → [docs/CORE_CONNECTION_C2_RESULT_2026-10-06.md](docs/CORE_CONNECTION_C2_RESULT_2026-10-06.md)(C-2 の結果、922126b。期待値 1B v2 は 2ecefa2) → [docs/CORE_CONNECTION_C2_DECISIONS_AFTER_2026-10-06.md](docs/CORE_CONNECTION_C2_DECISIONS_AFTER_2026-10-06.md)(C-2 の後の人間の決定) → [docs/CORE_CONNECTION_C1H_PREDICTION_2026-10-06.md](docs/CORE_CONNECTION_C1H_PREDICTION_2026-10-06.md)(C-1h の予測、封印) → [docs/CORE_CONNECTION_S1_PLAN_2026-10-06.md](docs/CORE_CONNECTION_S1_PLAN_2026-10-06.md)(将棋側 S-1 の計画と予測、封印。実装は C-1h の後) → [docs/CORE_CONNECTION_C1H_RESULT_2026-10-06.md](docs/CORE_CONNECTION_C1H_RESULT_2026-10-06.md)(C-1h の結果、`78d1a76`、監査 GO。1 社目 0・2 社目 0・3 社目 予測 5 当たり + 予測外 1(T028、安全側)、3 社目の期待値は規則どおり未作成、「一致」の定義は人間へ) → [docs/CORE_CONNECTION_S1_RESULT_2026-10-06.md](docs/CORE_CONNECTION_S1_RESULT_2026-10-06.md)(将棋側 S-1 の結果、`c2708ed`、監査 GO。Golden rc=1・H-9 NG 8/8 予測どおり・213/213、外れ 2(178 件・H-11 注記 4)。期待値の書き直し・S-2・席の修正は人間へ) → [docs/CORE_CONNECTION_S1_DECISIONS_AFTER_2026-10-06.md](docs/CORE_CONNECTION_S1_DECISIONS_AFTER_2026-10-06.md)(S-1 の後の人間の決定: Golden 書き直し GO・S-2 GO(予測が先)・20 件の元の修正 GO(原因を先に読む)・「一致」は (i) 完全一致を維持) → [docs/CORE_CONNECTION_S2_PLAN_2026-10-06.md](docs/CORE_CONNECTION_S2_PLAN_2026-10-06.md)(将棋側 S-2 の計画と予測、封印。E-3 は実物で走っていない・I-4 に H-9 行 17/6 束・出口へは伝播しない、の予測) → [docs/CORE_CONNECTION_S2_RESULT_2026-10-06.md](docs/CORE_CONNECTION_S2_RESULT_2026-10-06.md)(S-2 の結果、`c3da8de`、監査 GO。差 35・I-4 H-9 行 17/6 束・E-3 0・g8 0、22 欄全部当たり。期待値の書き直し・描画の直し・届かせるかは人間へ) → [docs/CORE_CONNECTION_S2_DECISIONS_AFTER_2026-10-06.md](docs/CORE_CONNECTION_S2_DECISIONS_AFTER_2026-10-06.md)(S-2 の後の人間の決定: Golden 書き直し GO・S-3 は実 run 1 周に束ねる GO・費用 $5 上限・Core 変更なし・予測の封印は必須) → [docs/CORE_CONNECTION_S3_PLAN_2026-10-06.md](docs/CORE_CONNECTION_S3_PLAN_2026-10-06.md)(S-3 の計画と予測、封印。実 run 1 周、0/1 と幅の予測 30 欄)→ [docs/CORE_CONNECTION_S3_RESULT_2026-10-06.md](docs/CORE_CONNECTION_S3_RESULT_2026-10-06.md)(S-3 の結果、`5df660b`、監査 GO。実 run 1 回 4.5351 USD・封印語 12/12・gpt の H-9 全部 G・Core と 12/12・claude 席は schema で空席・draft rejected 0、32 欄 当たり 26 外れ 6。期待値に入れるか・schema の minItems・draft と heldBack は人間へ) → [docs/CORE_CONNECTION_S4_PLAN_2026-10-06.md](docs/CORE_CONNECTION_S4_PLAN_2026-10-06.md)(S-4 の計画と予測、封印。契約 4 本の新版 + H-12・指示文 v1.4・再試行の 1 文)→ [docs/CORE_CONNECTION_S4_RESULT_2026-10-07.md](docs/CORE_CONNECTION_S4_RESULT_2026-10-07.md)(S-4 の結果、`e5d319f`、監査 GO。実 run は gpt だけ通過 0.847 USD・claude と整理役は Anthropic の残高不足で送れず。観測 0 の needed_observation と**配列のままの観測 4 件 GROUNDED** が解けた・Core 20/20・Golden c5 は rc=1(skip でも 1 行出る)・H-1 が名前の数字を数える/H-3 が needed_observation に反証を要求する の 2 穴。33 欄 当たり 23 外れ 4 測れない 6。入金してやり直すか・Golden・H-1/H-3 は人間へ) → **Golden c5 を S-4 の現状で書き直し `3ee4d00`**(58 項目に H-12 の skip 行。skip の行は落とさない ― S-1 の穴はこの行で見える)→ [docs/CORE_CONNECTION_S5_PLAN_2026-10-07.md](docs/CORE_CONNECTION_S5_PLAN_2026-10-07.md)(S-5 の計画と予測、封印 + 追記 §7 = 設計の訂正)→ [docs/CORE_CONNECTION_S5_RESULT_2026-10-07.md](docs/CORE_CONNECTION_S5_RESULT_2026-10-07.md)(S-5 の結果、`3a766cc`、監査 GO。**監査が REVISE 2 回**= 実物では発火しない潜在欠陥を変異と probe だけが捕まえた。0 円の計測は 3 便を通じてバイト一致、Golden 差 38(予測 5 を外した = 記録の面の数え落ち、同じ型 4 回目)。実 run は入金と上限の承認が揃ってから)→ **S-5 の実 run 1 回 完了**(`43f8b69c-20261007-1`、2026-10-07、3 分 6 秒・2.0050 USD。両席が試行 1 で通過・整理役も走り・H-9 46/46 で Core と一致・配列のまま GROUNDED 8 件・draft 7/7・Golden rc=0。上限が効いて S-4 の 52 分 → 3 分 6 秒。予測の外: 整理役の代表の schemaVersion が 0.4 で契約の直しが届いていない・gameId の数字が H-1 に数えられる)。
- いまの段(2026-10-12 訂正): **Core は `core/py/audit_core/` に在る。** 保護面(`core/py` + `adapters/`)は 22 ファイル、束ねた sha `490888d46d034ca9eaae8e4b4d01f494919abf21a8b057e87c835d25256d7116`(repo の根で `git ls-files audit-core/core/py audit-core/adapters | sort | xargs shasum -a 256 | shasum -a 256`)。試験は `python3 -m unittest discover -s tests -t .` で 490、`python3 -m pytest -q` で 586(2026-10-12)。**製品線は `main`**(`../docs/DECISION_LOG.md` D-001)。最新の段は AI 文実験(真 391 Claim)の停止原因の分類 ― [docs/STOP_CAUSE_CRITERIA_2026-10-09.md](docs/STOP_CAUSE_CRITERIA_2026-10-09.md)。旧記述「C-1a まで。Core のコードはまだ無い」は 2026-10-06 時点の字で、2026-10-12 まで直されていなかった(履歴は `git log -p -- audit-core/README.md`)。

- **外部の数の文に使う profile(2026-11-06、推奨を P30E から P32E に。既定は P27 のまま)**: 外部の数の文(AI の文など)を点検する客には `P32E`(= P30E + 数の直前 12 字に「前期」などの手がかりがある数を当期の fact に結ばず、前期の fact を名指して照らす PB。旗 `prior_cue_bind_2026_11_06`。`P32E` を明示して使う)を推奨する。判定は結果 [docs/XBRL_PRIOR_CUE_BIND_ENGINE_RESULT_2026-11-06.md](docs/XBRL_PRIOR_CUE_BIND_ENGINE_RESULT_2026-11-06.md) が封 [docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md](docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md) §4 の基準 K-1〜K-5 を記録の数から機械で求めた「採用」(「前期」と書かれた数に同じ要素の当期の値を入れた注入 141 行を通した率は P30E 97.9% から P32E 8.5% に下がる。手がかりのある 129 行で当期の fact に GROUNDED は 0。手元の 97 書類の原文で GROUNDED を失う行 0・状態が動いた行 19。AI の文 200 本で GROUNDED を失う行 1)。**負けの側**: P32E が通した 12 / 141 = 8.5% は、数の直前 12 字に前期の語が無い書き方の 11 行(規則の範囲の外。表の列の見出しも手がかりにしない)と、入れた値が前期の別の fact の値と偶然合った 1 行。人間の言葉 2026-11-06「それで任せる進めて」(封 §0-2)。 **P30E の字(下の 2026-11-04 の行)は消さない。** 既定の切り替えは人間が決める。 人が書いた文でも測った(2026-11-10。推奨は変えない): 会社が書いた決算短信の「経営成績等の概況」17 社に P32E を当てると、数の claim の GROUNDED は 4 割台にとどまり、engine が「値が違う」と返した行を 1 人の目で読んで、短信と有報の数が本当に違う候補は 4 行で、残りの大半はセグメント・内訳・計画などの数を全社の fact や別の fact と比べた行だった。注入した誤りを通したのは 1 行、期の取り違えの注入は 2 行しか作れず通した率は言えない。結果 [docs/XBRL_TANSHIN_HUMAN_TEXT_RESULT_2026-11-09.md](docs/XBRL_TANSHIN_HUMAN_TEXT_RESULT_2026-11-09.md)。【門なし】
- **外部の数の文に使う profile(2026-11-04、推奨を P28E から P30E に。既定は P27 のまま)**: 外部の数の文(AI の文など)を点検する客には `P30E`(= P28E + 万・億の数のコンマを 1 つの数に読む N + 丸め方の根拠が混ざる桁は両方の帯で照らす RB。旗 `numbers_man_comma_2026_11_04`・`rounding_mixed_2026_11_04`。`P30E` を明示して使う)を推奨する。判定は結果 [docs/XBRL_ROUNDING_MIXED_ENGINE_RESULT_2026-11-04.md](docs/XBRL_ROUNDING_MIXED_ENGINE_RESULT_2026-11-04.md) が封 [docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md](docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md) §4 の基準 K-1〜K-5 を記録の数から機械で求めた「採用」(AI の文 200 本で P29E の GROUNDED を失う行 0・GROUNDED になった既存の行の札は 真 102 / 偽 8・手元の 97 書類の原文で動いた行 2 / 失う行 0・注入の相対のずれを通した率は 0.8% から 2.7% に上がる = 代価)。N 単独(P29E)は前の便 [docs/XBRL_NUMBER_READER_ENGINE_RESULT_2026-11-04.md](docs/XBRL_NUMBER_READER_ENGINE_RESULT_2026-11-04.md) で「採用しない(人間に返す)」だった(既存の行 8 が動いた K-2 の外れ。原因は書類単位の丸め方の決定で、RB がその行を戻した)。人間の言葉 2026-11-04「君に任せる課題解決に向けて進めて」(封 §0-2)。注入の仕掛けの数の読みを直した便 [docs/XBRL_INJECT_SCAN_FIX_RESULT_2026-11-05.md](docs/XBRL_INJECT_SCAN_FIX_RESULT_2026-11-05.md)(2026-11-05。万円・億+万の複合の数 7,305 が注入の分母に入った)では、新しく届いた site で P30E が通した誤りは 値の置換 0 / 542・相対のずれ 1 / 1,196 = 0.1%(名指して原本 86.9% / 90.4%。既存の site の率とは母集団が違う)。期の取り違えの注入の便 [docs/XBRL_PERIOD_SWAP_IDMAP_RESULT_2026-11-06.md](docs/XBRL_PERIOD_SWAP_IDMAP_RESULT_2026-11-06.md)(2026-11-06。前の便 [docs/XBRL_PERIOD_SWAP_RESULT_2026-11-06.md](docs/XBRL_PERIOD_SWAP_RESULT_2026-11-06.md) は対応付けの限界で 13 行だけ)では、**「前期」と書かれた数に同じ要素の当期の値を入れた注入を P30E が通した率は 138 / 141 = 97.9%(P29E 137 / 141)= 負けの側**(engine の直接値の枝は「前期」の手がかりで前期の fact を先に見るだけで縛らない。縛る規則は人間の決定)。値が偶然一致して参照先が違う誤り(T5)を円族の数に注入した便 [docs/XBRL_T5_YEN_RESULT_2026-11-06.md](docs/XBRL_T5_YEN_RESULT_2026-11-06.md)(2026-11-06。注入の仕掛けが「12億3,456万円」などの円族の数に T5 を作れるようにした)では、**P30E が通した率は 12 / 535 = 2.2%**(P29E 11 / 535。止めた 523 行のうち原本を名指したのは 182 行で、300 行は名指さずに止めた。通した 12 行は全部が既存の書き方の数)。 **P28E の字(下の 2026-11-03 の行)と P27E の字は消さない。** 既定の切り替えは人間が決める。engine 全体の品質証明ではない。
- **外部の数の文に使う profile(2026-11-03、推奨を P27E から P28E に。既定は P27 のまま)**: 外部の数の文(AI の文など)を点検する客には `P28E`(= P27E + 「その他」の主語の結び直し O。新しい旗は無く、`P28E` を明示して使う)を推奨する。判定は結果 [docs/XBRL_P28E_RESULT_2026-11-03.md](docs/XBRL_P28E_RESULT_2026-11-03.md) が封 [docs/XBRL_P28E_SEAL_2026-11-03.md](docs/XBRL_P28E_SEAL_2026-11-03.md) §4 の基準 R-1〜R-3 を記録の数から機械で求めた「採用」(同梱の AI の文 1 書類で P27E の止めた 7 行が GROUNDED・P27E の GROUNDED は 1 行も動かず・注入の通した 2 件は同じ。手元の 97 書類の原文で動いた行は 1)。人間の言葉 2026-11-03「君に任せる進めて」。**P27E の字(下の 2026-10-28 の行)は消さない。** 既定の切り替えは人間が決める。engine 全体の品質証明ではない。
- **いまの段(2026-10-28、既定を P27)**: 既定は `P27`(P26 に P27 の旗 4 つ(書かれた桁での照合(封 §1-1 の A)・1 株当たりの窓・「1人当たり」の「1」・先の決算期)を積んだもの。判定は評価用の結果 [docs/XBRL_P27_RESULT_2026-10-27.md](docs/XBRL_P27_RESULT_2026-10-27.md)(`aeae608`)が封 [docs/XBRL_P27_SEAL_2026-10-27.md](docs/XBRL_P27_SEAL_2026-10-27.md) §4 の条件を記録の数から機械で求めた「P27 を既定の候補として記録する」。人間の言葉 2026-10-27「価値を上げるためにも君に任せる 進めよう」・2026-10-28「君に任せるよ」、封 [docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md](docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)・結果 [docs/XBRL_DEFAULT_P27_RESULT_2026-10-28.md](docs/XBRL_DEFAULT_P27_RESULT_2026-10-28.md)。P27E(相対の近さの名指しを足した profile)は既定にしない。engine 全体の品質証明ではない。下の行の P26 は、この直前の既定)。
- **いまの段(2026-10-23、既定を P26)**: 既定は `P26`(P22 に P23〜P26 の直しを積んだもの。判定は新しい標本 30 書類の結果 [docs/XBRL_FRESH_SAMPLE_RESULT_2026-10-21.md](docs/XBRL_FRESH_SAMPLE_RESULT_2026-10-21.md)(`52289c4`)の記録の数から、封 [docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md](docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md) §3 の基準で機械で求めた。人間の決定 2026-10-21「あとは全て任せる」、封 [docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md](docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)・結果 [docs/XBRL_DEFAULT_P26_RESULT_2026-10-23.md](docs/XBRL_DEFAULT_P26_RESULT_2026-10-23.md)。engine 全体の品質証明ではない。下の行の P22 は、この直前の既定)。
- **いまの段(2026-10-20、期を縛る P22)**: 既定は `P22`(P21 + 前期の手がかりが無い数を前期の fact に値だけで結ばない。人間の決定 2026-10-20「任せる」、封 [docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md](docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md)・結果 [docs/XBRL_PERIOD_BIND_RESULT_2026-10-20.md](docs/XBRL_PERIOD_BIND_RESULT_2026-10-20.md)。engine 全体の品質証明ではない。下の行の P21 は、この直前の既定)。
- **いまの段(2026-10-20)**: 既定は `P21`(P20 + 値が一致しないときの最後の枝に期の手がかり・セグメント枠・増減の語。人間の委任 2026-10-20、封 [docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md](docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md)・結果 [docs/XBRL_NAMING_FIX_RESULT_2026-10-20.md](docs/XBRL_NAMING_FIX_RESULT_2026-10-20.md)。engine 全体の品質証明ではない)。
- **いまの段(2026-10-15)**: 既定は `P20`(2026-10-14 の人間の決定。engine 全体の品質証明ではない)。
  **欠陥 A の修正は未採用で止めた** ― 封じた 8 書類では 4 条件合格だったが、
  使用済み 16 書類で既存の根拠を 2 件奪った([docs/DEFECT_A_ADOPTION_STOP_2026-10-14.md](docs/DEFECT_A_ADOPTION_STOP_2026-10-14.md))。
  XBRL 側の未解決事項は台帳 [docs/XBRL_OPEN_ISSUES_2026-10-15.md](docs/XBRL_OPEN_ISSUES_2026-10-15.md)(8 件)。
  次の領域は表計算・会計データの照合([docs/DOMAIN1_SHEET_DESIGN_2026-10-15.md](docs/DOMAIN1_SHEET_DESIGN_2026-10-15.md)、設計案。まだ 1 件も測っていない)。

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
| `core/py/audit_core/` | Core(C-1b で作る)。将棋も XBRL も知らない |
| `adapters/xbrl/` | XBRL Adapter(C-1c で作る)。語彙・member・母集団の印・抽出規則 P-1〜P-8 |
| `fixtures/xbrl/` | 探りの JSON・期待値(計器 3 の Golden)・探りの script の系譜・`manifest.json`。**ZIP は置かない** |
| `tests/` | 単体・境界・変異・Golden(C-1b 以降) |
| `docs/` | 設計・予測・結果の文書(`docs/` から 2026-10-06 に移動。履歴は `git log --follow`) |

## 材料と鍵

- 材料の ZIP は `~/.cache/audit-core/edinet/<docID>.zip`。sha256 は `fixtures/xbrl/manifest.json`。無ければ試験は**落ちる**(skip にしない)。
- EDINET API の鍵は環境変数 `EDINET_API_KEY`(`~/.config/edinet/env`)。repo・fixtures・ログに書かない。

## 出典

金融庁 EDINET の開示書類(有価証券報告書。docID と提出日は `fixtures/xbrl/manifest.json`)を、PDL1.0 に従って出典を明記したうえで、機械で抽出・照合して加工したもの。

## 門(C-1b から)

```
python3 -m unittest discover -s audit-core/tests -t audit-core
```
