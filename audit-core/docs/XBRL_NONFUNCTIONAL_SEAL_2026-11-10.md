# 封: engine の非機能の実測 NF ― 1 回の照合の時間とメモリ(97 書類の原文と AI の文 200 本、P27 と P33E。0 USD)― 2026-11-10

買い手の技術 DD の追及の 1 つは「非機能を測っていない」(1 書類・1 claim あたりの時間とメモリ)。この封は engine を変えずに、手元の材料で 1 回の照合(`adapters/xbrl/verify_document.py` の `verify_document` 1 回)の時間とメモリを測る便。engine の規則は足さない(人間の決定 2026-11-09 の戦略案「規則 T・O の後は engine の規則を足さない」)。規則 O の便は人間が保留にした(2026-11-10「rule O問題はまだいい」)。

## §0 材料と決めごと

### §0-1 測った事実(この封を書く前に司令塔が 0 USD で数えた。下見は scratchpad/nonfunc/probe.py。engine は HEAD `afc3cd6b`(規則 T の engine `2770ab23` の後)。cache の一覧の sha256 は前後で同じ)

1. **機械**: Apple M2・8 コア・メモリ 24 GiB・macOS 13.4・Python 3.9.6(Apple の python3)。他の機械では測らない。
2. **下見の作り**: 1 回の呼び出しを fork した子 process 1 つで行い(`multiprocessing` の Pool(1, maxtasksperchild=1)、並行なし)、呼び出しの前後で `time.perf_counter`・`time.process_time`・`resource.getrusage(RUSAGE_SELF).ru_maxrss`(macOS では byte)を読む。入力(ZIP の bytes と AI の文)を読むのは時計の外。
3. **下見の数(97 書類のうち先頭 5 書類・AI の文 200 本のうち先頭 5 本 × P27・P33E × 3 回 = 60 回)**: 書類 P27 の 1 回の時間の中央値 0.653 秒(最大 0.773)・P33E 0.679 秒(最大 0.796)・1 claim あたりの中央値 4.90 ms / 5.11 ms。AI の文 P27 0.584 秒(最大 0.828)・P33E 0.685 秒(最大 0.959)。呼び出しの後の ru_maxrss の中央値 99〜117 MB、呼び出しの前は 9〜10 MB。claim の数は 28〜179 で、時間は claim の数にほとんど比例しない(固定の部分が大きく見える。理由は測っていない)。【門なし】
4. **材料の大きさ**: 97 書類の P27 の claim の数は 51〜279(中央値 121、合計 11,722。記録 `fixtures/xbrl/pbind/regress97_2026-11-06.json`)。AI の文 200 本の P33E の数の claim は合計 16,588(記録 `fixtures/xbrl/tperiod/moves_200_2026-11-09.json`)。下見の 5 書類はこの幅の中ほど(101〜156)で、最大の書類は下見に入っていない。【門なし】

### §0-2 司令塔の決定(人間の言葉 2026-11-09「それで任せるから進めて」= 戦略案の「非機能の実測(1 claim・1 書類あたりの時間とメモリ。97 書類と 200 本。記録と門)」)

1. 測るのは `verify_document` 1 回(読み込み済みの入力に対する照合)。入力の読み込み・ZIP の展開の外側・report の組版は時計の外。engine の import の時間は別の欄で測る(§1 の 4)。
2. profile は P27(既定)と P33E(外部の数の文の推奨)の 2 つ。97 書類は原文(text なし)、AI の文 200 本は text つき。
3. 全部を 3 回ずつ、子 process 1 つずつ、並行なし(1 本の Pool(1))。順は (回, 材料, profile) の固定の順。測っている間は同じ機械で他の重い仕事を走らせない(門・監査・生成を止めて走らせる)。
4. 時間の数は機械と負荷で変わる。記録はこの機械のこの日の 1 回の走りで、門は「文書の数が記録と同じ」を縛るだけで、時間を測り直して照らすことはしない。
5. engine・既存の記録・cache は変えない。新しい記録は `fixtures/xbrl/nonfunc/timing_2026-11-10.json` の 1 つ(行は 材料の種類・本の id・profile・回・時間・CPU 時間・ru_maxrss の前後・claim の数・入力の byte 数。文・要素名・会社名を持たない。97 書類の docID を持つので fresh_seal の LATER_NAMING_FILES に宣言する)。

## §1 測るもの(字で留める)

1. **1 回の時間**: `time.perf_counter()` の差(秒)。CPU 時間は `time.process_time()` の差。
2. **1 claim あたりの時間**: 1 回の時間 ÷ その回の claim の数(数と文の claim の全部。`out["claims"]` の長さ)。
3. **メモリ**: 呼び出しの後の子 process の `ru_maxrss`(byte。macOS)。呼び出しの前の値も記録し、差も出す。
4. **import の時間**: 新しい python process で `import adapters.xbrl.verify_document` だけを 5 回(`python3 -X importtime` は使わず、子 process の起動から import の後までの `perf_counter` の差)。
5. **3 回の揺れ**: 同じ (材料, profile) の 3 回の (最大 − 最小) ÷ 中央値。

## §2 予測(**測定の script より先に固定。結果を見てから書き換えない**。N-1〜N-7 は下見の 5 書類・5 本の数から幅を置いた。最大の書類は下見に入っていないので N-3・N-5・N-6 の上限は本当の予測。N-8・N-9 は下見していない本当の予測)

| # | 欄 | 予測 | 外れ方 |
|---|---|---|---|
| N-1 | 97 書類 × P27: 1 回の時間の中央値(3 回 × 97 = 全部の回) | 0.4〜1.0 秒 | 幅の外 = 外れ |
| N-2 | 97 書類: P33E の中央値 ÷ P27 の中央値 | 0.90〜1.15 | 規則 T の分だけ遅くなる見込み。幅の外 = 外れ |
| N-3 | 97 書類 × P27: 1 回の時間の最大 | 2.0 秒以下 | 最大の書類が claim の数に比例して遅いなら超えうる |
| N-4 | 97 書類 × P27: 1 claim あたりの時間の中央値 | 3〜9 ms | 幅の外 = 外れ |
| N-5 | AI の文 200 本 × P33E: 1 回の時間の中央値 / 最大 | 0.4〜1.0 秒 / 2.5 秒以下 | どちらかが外 = 外れ |
| N-6 | 全部の回: 呼び出しの後の ru_maxrss の中央値 / 最大 | 70〜150 MB / 250 MB 以下 | どちらかが外 = 外れ |
| N-7 | 全部の (材料, profile): 3 回の揺れの中央値 | 10% 以下 | 超えたら「この機械の 1 回の数は揺れる」と書く |
| N-8 | import の時間(5 回の中央値) | 1.5 秒以下 | 超えたら外れ |
| N-9 | 97 書類 × P27 の claim の数の合計 / AI の文 200 本 × P33E の数の claim の合計 | 11,722 / 16,588(既存の記録と同じ) | 1 でも違えば材料か配線が違う(止めて原因を読む) 【門なし】 |

## §3 判定

採用 / 不採用の判定は無い便。結果の文書は §2 の当たり / 外れと、§1 の数の表(材料 × profile ごとの中央値・最大・1 claim あたり・メモリ)を記録から作る。台帳には L・D・P の行を足す。README に 1 文(この機械の数であること・測っていないことを先に)。

## §4 測り方(全部 0 USD)

- `measure/xbrl_nonfunc_2026-11-10.py`: `run`(§0-2 の 3 の順で全部の回を測り記録を書く)と `tally`(封の字から幅を読んで N-1〜N-9 を判定し表を出す)。97 書類の入力は前の便の作り(`measure/xbrl_p28_regress97_2026-11-02.py` の `make_jobs`)、AI の文は PB の便の `RM.load_jobs` を importlib で読んで使う(関数を写さない。前から在る sys.modules の名前は戻す)。記録の header に機械(CPU の名・コア数・メモリ・OS・python)・HEAD・engine の指紋・cache の前後を書く。
- 門 `tests/measure/test_xbrl_nonfunc_seal.py`・`tests/measure/test_xbrl_nonfunc_result.py`(封の字・順序・配線・記録の形・表 = 記録から作り直した表・判定の境界・変異で赤)。
- 結果 `docs/XBRL_NONFUNCTIONAL_RESULT_2026-11-10.md`。

## §5 言えないこと

1. 数はこの 1 台(Apple M2・macOS 13.4・Python 3.9.6)の、この日の 1 回の走り。他の機械・OS・python・負荷では測らない。
2. 並行の処理(何書類を同時に回せるか・throughput)は測らない。1 process ずつ直列で測る。
3. 材料は手元の 97 書類と AI の文 200 本だけ。これより大きい書類・PDF・他の形式は測らない。
4. ru_maxrss は子 process の最大の常駐の量で、fork の親と共有する頁の数え方は OS に依る。呼び出し 1 回だけのメモリを切り出した量ではない。
5. 有料の API・通信は使わない。LLM の席の時間・費用は含まない。

## §6 作法と順序

1. この封を commit(文書だけ。fresh_seal・facts・boundary の門を走らせてから)→ 測定 script と門(step-implementer、worktree)→ 変異 → 独立監査 GO → commit → 記録(本番。他の重い仕事を止めて)→ 結果の文書 → 門 → 監査 GO → commit → 台帳・README → 監査 → commit。
2. 使わない: `git add -A`・`stash`・`reset`・`checkout`。cache に file を足さない。`edinetdb-p27`・`sgogi-coach-handoff` は開かない。鍵は全部 unset。
