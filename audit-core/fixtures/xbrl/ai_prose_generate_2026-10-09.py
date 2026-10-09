# -*- coding: utf-8 -*-
"""封 AI_PROSE_SEAL_2026-10-09 §2.2 の生成を **1 回だけ** 回す。

**司令塔が凍結時の 1 回目として回す。**各測定は 1 回だけ。

封じた規則(ここで変えない):
  - **1 社だけ回す。** 使える provider のうち**名前の辞書順で最初**
    (claude < gemini < gpt)。**結果を見てから選び直さない。良い方を採らない。**
  - **上限 1.00 USD。** 上限と単価を env から読み、**無ければ回さない**
    (既存器 runClaimDecomposer の「上限の無い実行はしない」と同じ姿勢)。
  - 鍵は env から読むだけ。**値を印字も記録も保存もしない**(例外の文も通さない)。

守り:
  - 指示文の sha が、生成の前にコミットした meta と一致しなければ止まる。
  - **再試行しない。** 1 回の失敗で止める ― 再試行は費用を倍にし、
    かつ「生成は 1 回」という封を破る。
  - **出力の file が既に在れば上書きしない。** 2 回目の生成を事故で作らない。
"""

import hashlib
import io
import json
import os
import sys
import urllib.error
import urllib.request

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)

PROMPT = os.path.join(HERE, "ai_prose_prompt_filled_2026-10-09.txt")
PROMPT_META = os.path.join(HERE, "ai_prose_prompt_meta_2026-10-09.json")
OUT_PROSE = os.path.join(HERE, "ai_prose_2026-10-09.txt")
OUT_META = os.path.join(HERE, "ai_prose_generation_meta_2026-10-09.json")

COST_CAP_USD = 1.00                 # 封 §2.2
MAX_OUTPUT_TOKENS = 6000            # 本文 5,000 字程度の依頼に対する構造的な上限

# **辞書順で最初**。封じた選び方。
PROVIDERS = (
    ("claude", "ANTHROPIC_API_KEY", "SEAT_CLAUDE_MODEL",
     ("PRICE_CLAUDE_INPUT", "PRICE_CLAUDE_OUTPUT"), "claude-sonnet-5"),
    ("gemini", "GEMINI_API_KEY", "SEAT_GEMINI_MODEL",
     ("PRICE_GEMINI_INPUT", "PRICE_GEMINI_OUTPUT"), "gemini-2.5-pro"),
    ("gpt", "OPENAI_API_KEY", "SEAT_GPT_MODEL",
     ("PRICE_GPT_INPUT", "PRICE_GPT_OUTPUT"), "gpt-5"),
)


def load_dotenv(path):
    """最小の .env 読み。**既に process.env に在る名前は上書きしない。**
    値は返さず、この関数の外へは dict として渡すだけで**印字しない。**"""
    vals = {}
    if not os.path.exists(path):
        return vals, []
    names = []
    with io.open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            names.append(k)
            if k not in os.environ:
                vals[k] = v
    return vals, names


def env_get(vals, name):
    return os.environ.get(name) or vals.get(name)


def redact(text, secret):
    return text.replace(secret, "***") if secret else text


def main():
    vals, names = load_dotenv(os.path.join(REPO, ".env"))
    print(".env から読んだ名前の数: %d(**値は印字しない**)" % len(names))

    # 封じた選び方 ― 辞書順で最初に「鍵が在る」もの
    chosen = None
    for label, keyname, modelname, pricenames, default_model in PROVIDERS:
        if env_get(vals, keyname):
            chosen = (label, keyname, modelname, pricenames, default_model)
            break
    if chosen is None:
        print("止まる: 3 社の鍵がどれも無い(%s)" % ", ".join(p[1] for p in PROVIDERS))
        return 2
    label, keyname, modelname, pricenames, default_model = chosen
    print("provider = %s(**辞書順で最初に鍵が在ったもの。結果を見て選んでいない**)" % label)

    key = env_get(vals, keyname)
    model = env_get(vals, modelname) or default_model
    print("model = %s%s" % (model, "" if env_get(vals, modelname) else "(既定値)"))

    # 上限と単価 ― 無ければ回さない
    pin, pout = env_get(vals, pricenames[0]), env_get(vals, pricenames[1])
    missing = [n for n, v in zip(pricenames, (pin, pout)) if not v]
    if missing:
        print("止まる: 単価が env に無い -> %s" % ", ".join(missing))
        print("  上限の無い実行はしない。1M トークンあたりの USD を置いてから回すこと。")
        return 2
    pin, pout = float(pin), float(pout)

    with io.open(PROMPT, encoding="utf-8") as fh:
        prompt = fh.read()
    meta = json.load(open(PROMPT_META, encoding="utf-8"))
    got = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    if got != meta["prompt_sha256"]:
        print("止まる: 指示文の sha が、生成の前にコミットした meta と違う")
        print("  いま %s / 封じた %s" % (got[:16], meta["prompt_sha256"][:16]))
        return 3
    print("指示文 %d 字 sha %s… ― コミット済みの meta と一致" % (len(prompt), got[:16]))

    if os.path.exists(OUT_PROSE):
        print("止まる: %s が既に在る。**生成は 1 回だけ**なので上書きしない。" % OUT_PROSE)
        return 3

    # 入力トークンは**文字数で過大に見積もる**(日本語はトークン ≤ 文字数)
    est_in = len(prompt)
    bound = est_in * pin / 1e6 + MAX_OUTPUT_TOKENS * pout / 1e6
    print("費用の上限の見積り: 入力 %d(文字数で過大に見積もり)+ 出力 %d トークン -> **%.4f USD**"
          % (est_in, MAX_OUTPUT_TOKENS, bound))
    if bound > COST_CAP_USD:
        print("止まる: 見積り %.4f USD が上限 %.2f USD を超える" % (bound, COST_CAP_USD))
        return 2

    if label != "claude":
        print("止まる: この道具は今 claude の端点だけを実装している(provider=%s)" % label)
        print("  封の選び方を変えずに実装を足すこと。**こちらで provider を選び直さない。**")
        return 2

    body = json.dumps({
        "model": model,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"}, method="POST")
    print("呼ぶ ― **1 回だけ。再試行しない。**")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            res = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = redact(e.read().decode("utf-8", "replace")[:400], key)
        print("止まる: HTTP %s ― %s" % (e.code, detail))
        return 2
    except Exception as e:                                  # noqa: BLE001
        print("止まる: %s" % redact(str(e), key))
        return 2

    text = "".join(b.get("text", "") for b in res.get("content", []))
    usage = res.get("usage", {})
    tin, tout = usage.get("input_tokens"), usage.get("output_tokens")
    cost = (tin or 0) * pin / 1e6 + (tout or 0) * pout / 1e6
    stop = res.get("stop_reason")

    with io.open(OUT_PROSE, "w", encoding="utf-8") as fh:
        fh.write(text)
    rec = {
        "seal": "docs/AI_PROSE_SEAL_2026-10-09.md",
        "gate3_respec": "docs/AI_PROSE_GATE3_RESPEC_2026-10-09.md",
        "provider": label, "model": model,
        "provider_choice_rule": "使える provider のうち名前の辞書順で最初(claude<gemini<gpt)。結果を見てから選び直さない",
        "calls": 1, "retries": 0,
        "prompt_sha256": got, "prompt_chars": len(prompt),
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "input_tokens": tin, "output_tokens": tout, "stop_reason": stop,
        "cost_usd": round(cost, 6), "cost_cap_usd": COST_CAP_USD,
        "prose_chars": len(text),
        "prose_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
    with io.open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1); fh.write(u"\n")
    print("本文 %d 字  sha %s…" % (len(text), rec["prose_sha256"][:16]))
    print("トークン 入力 %s / 出力 %s  stop=%s  **費用 %.4f USD**(上限 %.2f)"
          % (tin, tout, stop, cost, COST_CAP_USD))
    if stop == "max_tokens":
        print("  注意: 出力の上限で切れている。打ち切られた本文として扱う。")
    print("  -> %s" % OUT_PROSE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
