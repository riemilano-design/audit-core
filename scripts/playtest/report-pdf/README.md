# report-pdf/ ― 対局後診断レポートの PDF を作る道具(STEP PIPE 作業 B、S7)

凍結した第 6 版テンプレート(`scripts/playtest/out/report-template-v6/`、gitignore・**読むだけ・変えない**)の python(reportlab)6 本を、
**中身を変えずに**ここへ移したもの。docs/STEP_PIPE_PLAN_2026-09-21.md §2.2 の S7。

## 変えたところ(この 1 点だけ)

`_head.py`・`_util.py`・`_mid.py` の 3 行だけ、`prose.json`・`sfens.json` の置き場を環境変数 `REPORT_DATA_DIR` で渡せるようにした
(既定はこれまでどおり、道具と同じフォルダ)。中身のレイアウト・文言・判定・照合の規則(`_mid.py` の `allowed_numbers`・`BANNED` 語)は
**1 バイトも変えていない**。

- `_head.py`: `_here` の後に `_data_dir = os.environ.get("REPORT_DATA_DIR", _here)` を足した
- `_util.py`: `SF = json.load(open(os.path.join(_here, "sfens.json"), …))` → `os.path.join(_data_dir, "sfens.json")`
- `_mid.py`: `PROSE = json.load(open(os.path.join(_here, "prose.json"), …))` → `os.path.join(_data_dir, "prose.json")`

フォント(`_here/fonts/…`)の探し方は変えていない(`_here` は道具のあるフォルダのまま)。

## 使い方

1. `./build.sh` で `render_main.py`(本編)・`render_appendix.py`(別冊)を作る(`_head.py`・`_util.py`・`_mid.py` / `_head.py`・`_util.py`・`_app_head.py`・`_app.py`・`_tail.py` を連結するだけ。コミット対象ではない ― `.gitignore` 参照)。
2. `patient_report_data.json`・`audit_metrics.json`(`scripts/playtest/reportData.ts` の出力)と、`prose.json`・`sfens.json`(`reportData.ts --out-sfens` と、`prose-request.md` から人が書いたもの)を 1 つのフォルダに置く。
3. 本編: `REPORT_DATA_DIR=<そのフォルダ> python3 -X utf8 render_main.py <patient_report_data.json> <出力 PDF>`
4. 別冊: `REPORT_DATA_DIR=<そのフォルダ> python3 -X utf8 render_appendix.py <audit_metrics.json> <出力 PDF>`
   (`REPORT_DATA_DIR` を渡さなければ、`patient_report_data.json`・`audit_metrics.json` と同じフォルダに `prose.json`・`sfens.json` を置く、これまでどおりの使い方でよい)

`prose.json` が無ければ `_mid.py` の `json.load` で例外になり、本編は作られない(「言い換えが要る」の判断は `reportData.ts` の `prose-request.md` 側。ここでは止まるだけで、止まり方自体は変えていない)。

## 依存

`reportlab`・(埋め込み確認をするなら)`pymupdf`(`fitz`)。どちらも利用者の Python の site-packages にあることを前提にする(この STEP では固定しない。docs/STEP_PIPE_PLAN_2026-09-21.md 4.)。
埋め込める日本語フォントが無ければ `_head.py` が止まる(`fonts/IPAexfont00401/ipaexg.ttf` か、いくつかの既定の場所を探す。この規則は変えていない)。

作った PDF の全書体が埋め込みかどうかの確認は、いまは人(司令塔)が pymupdf で確かめる手作業(docs/STEP_PIPE_PLAN_2026-09-21.md §2.2 の指示どおり)。

## 既知の欠落(2026-09-21 独立監査 REVISE で明記)

別冊(`render_appendix.py`)は、`audit_metrics.json` の `candidate.reps` の欄(`side`・`transitionJp`・`capUsJp` ほか)と
`engine`・`sideLabel`・`trajectories` などが `reportData.ts` で未実装のため、`reportData.ts` の出力からは作れず `KeyError` で止まる。
凍結した `audit_metrics.json`(`scripts/playtest/out/report-template-v6/audit_metrics.json`)からは作れる。
