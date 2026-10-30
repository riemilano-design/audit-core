# -*- coding: utf-8 -*-
"""条件2: 候補の選択が Claim の値に依存しないことを実行経路で確かめる。
match_value を「常に不一致」「常に一致」に差し替えて、選ばれた pointer が
変わらないことを 1 書類の全 Claim で照合する。変われば値依存が残っている。"""
import json, os, sys
HERE = sys.argv[1]
sys.path.insert(0, HERE)
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

ZIP = os.environ["AC_ZIP"]
with open(ZIP, "rb") as f:
    zb = f.read()

def ptrs(label):
    num, text = R.build_raw_claims(zb, V.P7)
    return {c["id"]: (c.get("form"), json.dumps(c.get("pointer"), ensure_ascii=False)) for c in num}

base = ptrs("base")
orig = V.match_value
V.match_value = lambda fv, t, unit: None
never = ptrs("never")
V.match_value = lambda fv, t, unit: "forced"
always = ptrs("always")
V.match_value = orig

def cmp(name, other):
    diff = [i for i in base if base[i] != other.get(i)]
    print("%-8s 全 %d 件中 pointer/form が変わった: %d 件" % (name, len(base), len(diff)))
    for i in diff[:40]:
        print("   %-6s base=%s  %s=%s" % (i, base[i], name, other.get(i)))
    return diff

d1 = cmp("never", never)
d2 = cmp("always", always)
json.dump({"never_diff": d1, "always_diff": d2}, open(os.environ["AC_OUT"], "w"), ensure_ascii=False, indent=1)
