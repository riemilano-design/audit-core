# -*- coding: utf-8 -*-
"""A / C の問い(封 docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md §5-2)。

**段 11 の問いを 1 文字も変えずに接頭とし、「不一致の種類」の 1 欄だけを足す。**
足す字はこの file が持ち、**`startswith` を機械で確かめる。**

**この欄を足すことは席に「誤りが在る」と示唆しうる**(封 §5-2・§7 の 5)。
**だから偽警報は同じ文書の無改変の主張で測る。**
**測れるのは「誤りを示唆する問いの下での検出性能」であり、
通常の報告文を自然に読む場面での検出性能とは区別する**(人間の指示 2026-10-17)。

    python3 measure/sheet_errdet_question_2026-10-17.py
"""
import hashlib
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEAL = "docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md"
# 封 §3-2 の固定語彙(**6 語。字で留める**)
VOCAB = ("値が原資料に無い", "列の取り違え", "別の科目の値", "親階層の取り違え",
         "単位・符号の表記", "不明")

ADDED = u"""
さらに、各要素に次の欄を 1 つ足してください。

  不一致の種類 … 下の 6 語のどれか 1 つだけを書いてください。
      %s
    表のどこの数かを決められて、特に言うことが無ければ「不明」と書いてください。

  例: {"id": "R001", "会計": "一般会計", "階層": "款", "親": "", "科目名": "福祉費", "列": "支出済額", "値": 1066495914576, "不一致の種類": "不明"}
  例: {"id": "R002", "verdict": "根拠なし", "不一致の種類": "値が原資料に無い"}
  例: {"id": "R003", "verdict": "判定不能", "不一致の種類": "不明"}
""" % " / ".join(VOCAB)


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


L9 = _mod("spec9_for_errdet", "sheet_label_spec_m9_2026-10-16.py")


def base_question():
    """**段 11 の問い**(生成器から作る。手で写さない)。"""
    q = L9.question_text()
    L9.check_question(q)
    return q


def question_text():
    return base_question() + ADDED


def check(text=None):
    """**段 11 の問いが接頭**で、**6 語が全部在る**ことを確かめる。"""
    t = text or question_text()
    base = base_question()
    if not t.startswith(base):
        raise AssertionError("**段 11 の問いが接頭になっていない**")
    tail = t[len(base):]
    for w in VOCAB:
        if w not in tail:
            raise AssertionError("固定語彙が足りない: %s" % w)
    if "不一致の種類" not in tail:
        raise AssertionError("足した欄の名前が無い")
    return True


if __name__ == "__main__":
    q = question_text()
    check(q)
    print("段 11 の問い: %d 字 / sha256 %s"
          % (len(base_question()),
             hashlib.sha256(base_question().encode("utf-8")).hexdigest()[:16]))
    print("足した字: %d 字" % (len(q) - len(base_question())))
    print("A / C の問い: %d 字 / sha256 %s"
          % (len(q), hashlib.sha256(q.encode("utf-8")).hexdigest()[:16]))
    print("固定語彙: %s" % json.dumps(list(VOCAB), ensure_ascii=False))
