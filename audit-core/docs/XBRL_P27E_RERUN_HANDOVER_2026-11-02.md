# 引き継ぎ: AI の文を P27E と P27 で再判定する便(封 `35f624c`)― cloud の席から、ラベル file のある席へ ― 2026-11-02

2026-11-02。人間の指示「きっちり全て引き継ぐように準備してね」。この便は cloud の席で封・script・門まで進め、**測定(engine を走らせる)だけが残っている**。理由は §0-2。この文書は、ラベル file のある席(desktop、またはその席の agent)がこの便を最後まで運ぶための手順と、守る字の一覧。**数は 1 つも書かない**(測っていない)。

## §0 状態

### §0-1 commit 済み(branch `feature/audit-core-final-eval-8-yzrflr`、HEAD `be3ed402`、木は clean)

| commit | 中身 | 監査 |
|---|---|---|
| `35f624c9` | 封 `docs/XBRL_P27E_RERUN_SEAL_2026-11-02.md`(材料 8 本の sha256・走らせ方・数えるもの・予測 M-1〜M-10) | 文書のみ |
| `d24a21e0` | script `measure/xbrl_rerun_p27e_2026-11-02.py`(走らせていない) | REVISE 1 回 → GO |
| `be3ed402` | 門 `tests/measure/test_xbrl_rerun_p27e.py`(30 本)、覆い(257 / 191)、台帳 A-06〜A-09、README | REVISE 1 回 → GO |

無いもの: 記録 3 つ(`fixtures/xbrl/rerun_p27e_2026-11-02.json`・`fixtures/xbrl/entry_output_ai_prose_p27e_2026-11-02.json`・`fixtures/xbrl/entry_output_ai_prose_p27_2026-11-02.json`)、結果の文書 `docs/XBRL_P27E_RERUN_2026-11-02.md`、台帳の L-54 / P-39。

### §0-2 cloud で測れなかった理由(確定)

標準タクソノミのラベル file 3 本(`fixtures/xbrl/taxonomy_labels_sha256.txt` の名簿)の配布元 `disclosure.edinet-fsa.go.jp` が、cloud の送信元(国外のデータセンター)からの要求を遮断する(HTTP 403、本文「Service unavailable. The request is blocked.」。環境の許可ドメインを正しく設定しても同じ。ラベル file の URL だけでなくトップページも同じ)。環境の設定では直らない。desktop の folder は cloud から使えない状態だった。

### §0-3 cloud の席の sha256(この字と照らす。違えば pull が済んでいない)

| file | sha256 |
|---|---|
| `measure/xbrl_rerun_p27e_2026-11-02.py` | `0a4f1a3ccccb060f3ef97f15096e3422d17fdb549b9e7a16405953d23c85b68d` |
| `tests/measure/test_xbrl_rerun_p27e.py` | `6b4b6696ed10b76dd580c959b8748b691114aa7e6741294aa5d1a96bcfffe2a1` |
| `docs/XBRL_P27E_RERUN_SEAL_2026-11-02.md` | `fb363453da065c9ca8bef87441f3f9dfb4b748db9998192be4e7e815e4059819` |

材料 8 本の sha256 は封 §0 の表のとおり(script が走る前に照らす)。

## §1 desktop で最初に確かめること(全部通ってから §2 へ)

```
cd audit-core
git fetch origin feature/audit-core-final-eval-8-yzrflr
git checkout feature/audit-core-final-eval-8-yzrflr      # 別の branch の作業が残っていれば先に片づける(stash・reset は使わない)
git pull origin feature/audit-core-final-eval-8-yzrflr
git status --short                                      # 何も出ないこと。特に core/・adapters/ に差分があると script は止まる
sha256sum measure/xbrl_rerun_p27e_2026-11-02.py tests/measure/test_xbrl_rerun_p27e.py docs/XBRL_P27E_RERUN_SEAL_2026-11-02.md   # §0-3 と一致
( cd ~/.cache/audit-core/edinet-taxonomy/2025-11-01 && sha256sum -c "$OLDPWD/fixtures/xbrl/taxonomy_labels_sha256.txt" )       # 3 本とも OK
python3 --version                                       # 3.8 以上(門が ast.get_source_segment を使う)
python3 -m pytest -q -p no:cacheprovider tests/measure/test_xbrl_rerun_p27e.py                                                  # 22 passed・8 skipped
```

ラベル file が別の場所にあるなら `EDINET_TAXONOMY_DIR` で指す(`adapters/xbrl/instance.py` の `taxonomy_dir()`)。desktop で `sh run_tests.sh` が緑なら 3 本は在る。

## §2 走らせる(engine は 1 行も変えない)

```
python3 measure/xbrl_rerun_p27e_2026-11-02.py
```

- 書くのは §0-1 の「無いもの」の記録 3 つだけ。走り切ると `written: …` と、配線の門・主な集計・予測の判定を出す。
- **止まる条件**(止まるときは何も書かない。理由を 1 行で出す): 出力が既に在る / 材料の sha256 が封と違う / ラベル file が無いか sha256 が名簿と違う / `core/`・`adapters/` に未 commit の変更 / 記録に docID が残った。直して走らせ直す。走らせ直したら結果の文書の追記に回数と理由を書く(「その他」の便の追記 1 の形)。
- 走らせる時間は測っていない(engine を 2 回。儀式の script と同じ道)。
- 記録の `配線の門` の `通った` が false なら、結果の文書を書く前に理由を記録の中で探す(53 / 12 / 8 の数、行の対応、engine の未 commit)。**配線が通らない結果で予測を判定しない。**
- M-1(P27 の分布が儀式の 340・25・33・14 と一致)が外れたら、環境か engine の違いの印。外れは外れとして残し、§4 で中身を書く。**封(`docs/XBRL_P27E_RERUN_SEAL_2026-11-02.md`)は 1 字も変えない**(門 `test_c_1` が封の commit の字と照らす。追記も封には書かず結果の文書に書く)。

## §3 走らせた直後の門の見え方(想定内の赤)

`python3 -m pytest -q -p no:cacheprovider tests/measure/test_xbrl_rerun_p27e.py` を走らせると:

- `RecordTest` 8 本: 結果の文書がまだ無いので **全部 error**(setUpClass で文書を読む)。文書を書くと走る。
- `test_c_3`(記録・文書・entry 2 つは揃って在るか揃って無い): 文書が無い間は赤。
- `test_c_2_order`: 記録 3 つが未 commit の間は赤。commit で緑。
- 他(封と script の確かめ・変異 11 本)は緑のまま。変異は記録が在ればそれを使うので、`MutationTest` は記録の形の確かめにもなる。

## §4 結果の文書 `docs/XBRL_P27E_RERUN_2026-11-02.md` の書き方(門が字で縛る)

### §4-1 字の形(門 `table_problems`・`expected_cells`・`expected_lines` が要る物。`in doc` で見るので、行は字どおり)

記録から要る行を **そのまま印字する**コマンド(先頭行の `当たり / 外れ` と、§1 の表の実測の欄に入れる句、字どおり要る表の行、括弧の中の id の列):

```
python3 - <<'EOF'
import importlib.util, collections
spec = importlib.util.spec_from_file_location("g", "tests/measure/test_xbrl_rerun_p27e.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
rec = g.jload(g.REC); e16 = g.jload("fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json")
p16 = collections.OrderedDict((s, sum(1 for c in e16["claims"] if c["state"] == s)) for s in g.STATES)
J = rec["予測の判定"]; print("見出し: **予測 当たり %d / 外れ %d(%s)**" % (J["当たり"], J["外れ"], "・".join(i for i in g.IDS if J.get(i) == "外れ")))
for i in g.IDS: print("| **%s** | 〈封の予測〉 | %s | %s |" % (i, "、".join(g.expected_cells(rec)[i]), "判定しない" if i == "M-10" else "**%s**" % J[i]))
print("\n".join(g.expected_lines(rec, p16)))
T = rec["集計"]
for k in ("53 行で P27E で GROUNDED の id", "249 行で P27E で GROUNDED でなくなった id", "P27E と P27 で state が違う id", "12 行で P27E で GROUNDED の id"): print(k, "(%s)" % "・".join(T[k]))
print("札 偽", list(T["札 偽 の行"].keys()))
EOF
```

- **1 行目(見出し)** に `**予測 当たり N / 外れ M(外れた id を・で)**` を含める(外れが 0 なら括弧は要らない)。
- **§1 の表**: `| **M-1** | 予測 | 実測 | **当たり** |` の形で M-1〜M-10 を順に。実測の欄に上のコマンドの句が入っていること。M-3〜M-7・M-9 の実測の欄は数で始める。M-10 は 3 列目が `判定しない`。
- **字どおり要る表の行**(上のコマンドが印字する): state の分布 3 行(`| **P16** | G | VM | UNV | PNF |` の順。P27E・P27 も)、動きの表 8 行(`| P27E | **GROUNDED** | … |` 4 行と P27 の 4 行。P16 の state の行 → 新しい state の列)、53 行の型ごと 6 行(`| **T1 指せず** | 行数 | P27E で GROUNDED | P27 で GROUNDED |`)、8 行の id ごと 8 行(`| N039 | state / 期 | state / 期 |`。P27E・P27 の順)、根拠の形の表 2 行(`| **P27E** | 根拠に無い数 | 同 | 数式 | 要素名 |`。state の分布の行と同じ形なので、どちらも在ること)、句 6 つ(`53 行で P27E で GROUNDED N` など)。
- **id**: 53 行で P27E で GROUNDED の id・249 行で GROUNDED でなくなった id・P27E と P27 で state が違う id・12 行で P27E で GROUNDED の id・札 偽 の id が全部文書に在り、前 3 つは `(N001・N002・…)` の形(記録の順)で 1 か所以上在ること(空なら要らない)。
- **散文の数**: 表と見出し以外の行にある 3 桁以上の数は、記録の字に在るか、その行に `【門なし】` が要る(2 桁以下は縛らない ― だからこそ、2 桁の数も記録から写す)。
- **禁止語**(門 `FORBIDDEN`): accurate・guarantee・正確・保証・世界初・出所として正しい証拠が得られた。docID(S100 + 英数 4 字)を書かない。
- 変異の門が使う最小の文書は `tests/measure/test_xbrl_rerun_p27e.py` の `MutationTest.synthetic_doc` にある(形の見本。中身はこれより厚く書く)。

### §4-2 中身(今日の 5 便の結論に答える形。数は記録から)

- §1 予測の表(当たり外れ。外れは**外れのまま**。原因は別の段で)。
- §2 配線(ラベル file の sha256・engine の bundle の sha256 と HEAD・行の対応・53 / 12 / 8 / 249 の数・M-1 の一致)。
- §3 動き(分布 3 行、動きの表、GROUNDED でなくなった行の id と中身を 1 行ずつ読む)。
- §4 53 行(型ごと。P27E で GROUNDED になった行は根拠と比べ、engine の要素が根拠に在るか ― 「止めた真の文」の便 `docs/XBRL_DERIVATION_STOPPED_2026-11-02.md` の型 T1〜T6 と突き合わせる)。
- §5 12 行(「その他」の便 `docs/XBRL_OTHER_RULE_2026-11-02.md` の R1 が決まった 8 行と、P27E の state)。
- §6 8 行(期の印の便 `docs/XBRL_PERIOD_MARK_2026-11-02.md` の 8 行。P27E / P27 で pointers の期が前期に変わったか)。
- §7 M-9 の読み方: 封の照らし(local name の部分文字列)は「同」で略した根拠と数式の根拠では当たらない。記録の「根拠の形(参考)」の内訳で、要素名を書きうる根拠の行に限った数を併記する(**判定は封の定義のまま**。参考の欄は予測の対象ではない、と書く)。
- §8 言えないこと(1 書類・1 model、照らしの限界、engine の変更はこの便にない、P27E を既定にするかは人間)。
- §9 作法(走らせた回数、監査の REVISE の中身、cloud で測れなかった理由 = この文書 §0-2)。

### §4-3 その後の門

```
python3 -m pytest -q -p no:cacheprovider tests/measure/test_xbrl_rerun_p27e.py     # 記録・文書が揃えば test_c_2_order(未 commit)以外 緑
```

## §5 台帳 `docs/FACTS_FOR_BUYERS_2026-10-20.md` と門 `tests/measure/test_facts_for_buyers.py`

- **L-54**(§1 の表の末尾、L-53 の次)と **P-39**(§3 の予測の表の末尾、P-38 の次)を足す。形は L-53・P-38 と同じ(列: ID / 何を / 数の欄 / 印 / 確かめ方 / 門)。
  - 数の欄に書く数は全部、印 `〔rec fixtures/xbrl/rerun_p27e_2026-11-02.json#集計 > <鍵> = <値>〕` で縛る。鍵の例: `53 行で P27E で GROUNDED`、`249 行で P27E で GROUNDED でなくなった`、`8 行で P27E で GROUNDED`、`12 行で P16 が VALUE_MISMATCH の 9 行のうち P27E で GROUNDED`、`P27E と P27 で state が違う行`、`P27E で GROUNDED の 札 真・num のうち要素が根拠に無い`、入れ子は `P27E の state の分布(全 claim) > GROUNDED`。P-39 は `#予測の判定 > 当たり`・`> 外れ`・`> M-3` など。
  - 何をの欄(散文)に 3 桁の数や「1 / 3」の形の比を書かない(門 test_12 が赤くなる。「53 行のうち N 行」は 2 桁なら可、3 桁は「数の欄」と書いて欄に送る)。
  - 禁止語(台帳): 精度・LLM より正確・世界で 1 社・金額・契約・税・USD(「税金等調整前」も 税 を含む)。
- 門の定数: `EXPECT_ROWS` の `"L": 53 → 54`・`"P": 38 → 39`。`EXPECT_CLAIMS` に足した印の本数を加える(コメントに `2026-11-02(11): L-54(n)・P-39(m)で +k` の形で残す)。封の hash の一覧(`u"5a3b2a0"` の次)に `u"35f624c"` を、コメント `# 2026-11-02(11): P-39(AI の文を P27E と P27 で再判定。封)` つきで足す。
- 確かめ: `python3 measure/facts_check_2026-10-20.py --check --row L-54`・`--row P-39`(OK)、`python3 -m pytest -q -p no:cacheprovider tests/measure/test_facts_for_buyers.py`。

## §6 覆い・README

試験 file を**足さない**なら何も変えない(門はもう数えてある: 257 / 191 / 5899 / 5803)。門に試験を足したら `python3 measure/suite_coverage_2026-10-16.py --write` → `docs/SUITE_COVERAGE_2026-10-16.md` の +1(11) の段の本数と台帳 A-08 / A-09 を直す(file 数が変わらなければ A-06 / A-07・README は不変)。

## §7 監査 → commit → push

1. 触る file の sha256 を控えて凍結(scratchpad)。独立監査(`step-auditor`)に、封・記録・文書・台帳・門を渡す。観点: 封の字どおりか、記録の数と文書の字、外れを外れのまま書いたか、参考の欄が判定を変えていないか、台帳の印と門、docID、禁止語。REVISE なら直して再監査。**GO の前に commit しない。監査中は木を触らない**(前後で sha256 を照らす)。
2. commit は**パス指定**(`git add -A`・stash・reset・checkout を使わない)。repo の根(`audit-core` の親)から:
   ```
   git add audit-core/fixtures/xbrl/rerun_p27e_2026-11-02.json audit-core/fixtures/xbrl/entry_output_ai_prose_p27e_2026-11-02.json audit-core/fixtures/xbrl/entry_output_ai_prose_p27_2026-11-02.json audit-core/docs/XBRL_P27E_RERUN_2026-11-02.md
   git commit -F <msgfile> -- audit-core/fixtures/xbrl/rerun_p27e_2026-11-02.json audit-core/fixtures/xbrl/entry_output_ai_prose_p27e_2026-11-02.json audit-core/fixtures/xbrl/entry_output_ai_prose_p27_2026-11-02.json audit-core/docs/XBRL_P27E_RERUN_2026-11-02.md audit-core/docs/FACTS_FOR_BUYERS_2026-10-20.md audit-core/tests/measure/test_facts_for_buyers.py
   git push -u origin feature/audit-core-final-eval-8-yzrflr
   ```
   message は 1 行目に結論(当たり / 外れ と主な数)、本文に記録・門・監査の経過。docID を書かない。
3. push 後に `python3 -m pytest -q -p no:cacheprovider tests/measure/test_xbrl_rerun_p27e.py tests/measure/test_facts_for_buyers.py` が全部緑であることを見る。desktop なら `sh run_tests.sh`(約 40 分)も。

## §8 測らないまま終えるなら

封は「結果の文書が無い封」として台帳 §4-2 に **Q-09** を足す(状態: **測らなかった**。理由は §0-2)。`EXPECT_ROWS` の `"Q": 7 → 8`。門 `tests/measure/test_xbrl_rerun_p27e.py` は記録が無い限り skip のまま緑で、消さない。

## §9 この便の外にある判断(人間が決める)

- 「その他」の規則 R1 を engine に入れるか(既定にしない profile で)。期の印の規則を engine に入れるか。P27E を外部の文の既定にするか。― いずれも今日の 5 便の結果の文書 `docs/XBRL_DERIVATION_FALSE_2026-11-02.md`・`docs/XBRL_DERIVATION_STOPPED_2026-11-02.md`・`docs/XBRL_OTHER_RULE_2026-11-02.md`・`docs/XBRL_PERIOD_MARK_2026-11-02.md` と、この便の結果が材料。
- engine の変更は `measure/` で測ってから、人間の承認、独立監査 GO、path 指定の commit の順。
