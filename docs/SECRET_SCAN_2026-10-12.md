# 鍵型スキャン(全履歴)― 2026-10-12

買い手の DD は gitleaks / truffleHog 等で**全履歴**を走査する。先に同じことをして、出るものを説明しておく。

## コマンド(値は出力しない)

```
git log -p --all | grep -c -E "sk-ant-|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|EDINET_API_KEY=[A-Za-z0-9]"
```

結果 **3 件**(2026-10-12、HEAD `f10365e`)。`.env` の追跡 **0 件**(`git ls-files | grep -c -E "(^|/)\.env$"`)。

## 3 件の内訳(値は伏せる。形だけ)

| commit | ファイル | 何か | 長さ | 本物か |
|---|---|---|---|---|
| `2edf921`(2026-09-30) | `scripts/playtest/lib/env.test.ts` | `.env` 読み取りの試験が使う **作り物の行** `ANTHROPIC_API_KEY=sk-ant-…` | 24 字 | **否**(`test` の印つき) |
| `2edf921`(2026-09-30) | `scripts/playtest/lib/seatRun.test.ts` | 3 社分の **作り物の鍵の束** `KEYS = {openai: "sk-test-…", gemini: "AIza-test-…", anthropic: "sk-ant-…"}` | 15 字 | **否**(`test` の印つき) |
| `c6c350d`(2026-10-05) | `scripts/playtest/lib/fillTexts.test.ts` | 試験が器に渡す `apiKey:` の **置き字** | 21 字 | **否**(印は無いが長さで分かる) |

Anthropic の本物の鍵は約 108 字(`sk-ant-api03-…`)。**3 件とも 25 字未満で、鍵の形をしているだけの試験用の値**である。
3 件とも**試験ファイルの中**で、本番の経路(`scripts/playtest/lib/env.ts` 等)は環境変数からしか読まない。

## 方針

- **履歴は書き換えない。** 値は秘密ではなく、履歴を書き換えると封印・監査の証跡(commit sha による参照)が全部壊れる。
- 買い手の走査器が同じ 3 件を出したときは、この文書を示す。
- 以後、試験に鍵の形の値を置くときは `test` / `dummy` の印を値の中に入れる(`c6c350d` の 1 件はそれが無く、長さでしか判別できない)。
- 本物の鍵は `.env`(追跡しない)と `~/.config/edinet/env` にだけ在る。repo・fixtures・ログ・チャットに書かない(`audit-core/README.md`「材料と鍵」)。
