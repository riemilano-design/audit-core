# -*- coding: utf-8 -*-
"""XBRL 探り 4 本目(使い捨て)。予測 docs/XBRL_PROBE4_PREDICTION_2026-10-06.md(コミット 0736a71)§3・§4 の設計をそのまま機械にした。
- xbrl_probe.py(sha 896492a7…)と xbrl_probe3.py(sha 3d2092a9…)は変更しない。両方を import して使い、xbrl_probe3.main の写しに 3 か所だけ差し込む。
- 変更 A(PROBE4_A=1): 主語表の先頭に ("セグメント利益", ["OperatingIncome"]) を実行時に足す(凍結の 73 語のファイルは触らない)。
- 変更 B(PROBE4_B=1): 母集団の印を Claim 単位で直前方向に決める(§3.2)。いちばん右の印が「全社」→ 連結、事業名 → 列挙を集めて 1 語なら member・2 語以上なら ambiguous(member)、印が無ければ 3 本目の文単位の値。
- 2 段の門: PROBE4_A=0 PROBE4_B=0 で probe3L と byte 一致(Gate 1)、さらに PROBE_MEMBER=0 で probe2B と byte 一致(Gate 2)。
- 写しの作り方: xbrl_probe3.py の main を読み、置換を 1 か所ずつ assert しながら当てて生成した(生成の手順は結果文書に記す)。
"""
import os, sys, re, json, io, zipfile, hashlib, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("PROBE_RUN", "B")
import xbrl_probe as P
import xbrl_probe3 as P3
from xbrl_probe3 import (ctx_ok, facts_for, member_denominator, labels_from_zip, build_registry, resolve_members, paragraph_index,
                         AMBIG, ZIP_SHA, META_PATH, REGISTRY_PATH, MEMBER_ON, RUN3, ZIP_PATH, OUT_DIR)

A_ON = os.environ.get("PROBE4_A", "0") == "1"
B_ON = os.environ.get("PROBE4_B", "0") == "1"
VOCAB4 = ("セグメント利益", ["OperatingIncome"])      # 変更 A
MARK_CONSOL = "全社"                                   # 変更 B の連結の印(「連結」は印にしない)
CONN_RE = re.compile(r"^[、,及びおよびとや・\s]*$")    # 列挙の接続語だけか


def claim_member_B(s, pos, reg, fallback):
    """予測 §3.2。head = 文の Claim より前。いちばん右の印で決める。印が無ければ 3 本目の文単位の値(fallback)。"""
    head = s[:pos]
    marks = []
    for mem, name in reg.items():
        for mm in re.finditer(re.escape(name), head):
            marks.append((mm.start(), mm.end(), "seg", mem))
    for mm in re.finditer(MARK_CONSOL, head):
        marks.append((mm.start(), mm.end(), "all", None))
    if not marks:
        return fallback
    marks.sort()
    last = marks[-1]
    if last[2] == "all":
        return (None, "consolidated")
    group = [last]; cur = last
    for mk in reversed(marks[:-1]):
        if mk[2] != "seg":
            break
        if CONN_RE.match(head[mk[1]:cur[0]]):
            group.append(mk); cur = mk
        else:
            break
    if len({g[3] for g in group}) == 1:
        return (last[3], "claim")
    return (AMBIG, "ambiguous")


def main():
    if A_ON and P.SUBJECTS[0][0] != VOCAB4[0]:
        P.SUBJECTS.insert(0, VOCAB4)   # 変更 A: 4 本目専用の登録簿 1 行。凍結の 73 語のファイルは触らない
    zb = open(ZIP_PATH, "rb").read()
    sha = hashlib.sha256(zb).hexdigest()
    if sha != ZIP_SHA:
        print("ZIP sha mismatch:", sha); return 4
    meta = json.load(open(META_PATH, encoding="utf-8"))
    date, tried, chosen = meta["date_listed"], meta["tried"], meta["document"]
    inst = P.load_instance(zb)
    facts, contexts, tbs = inst["facts"], inst["contexts"], inst["textblocks"]
    mdna_name = next((n for n in tbs if "ManagementAnalysis" in n and n.endswith("TextBlock")), None)
    if mdna_name is None:
        mdna_name = next((n for n in tbs if "AnalysisOfFinancialPosition" in n or "OverviewOfBusinessResults" in n), None)
    text = P.strip_html(tbs[mdna_name]) if mdna_name else ""
    sentences = [unicodedata.normalize("NFKC", s.strip()) for s in re.split(r"(?<=。)|\n", text) if s and s.strip()]

    # ---- member の解決(ON のときだけ。OFF では一切触らない) ----
    sent_member = [(None, None)] * len(sentences)
    member_info = None
    if MEMBER_ON:
        z = zipfile.ZipFile(io.BytesIO(zb))
        members = member_denominator(contexts)
        id2label = labels_from_zip(z, inst["names"])
        ntext = unicodedata.normalize("NFKC", text)
        reg, rows, hand = build_registry(members, id2label, ntext, RUN3)
        paras = paragraph_index(text, sentences)
        sent_member = resolve_members(sentences, paras, reg)
        member_info = {"denominator": len(members), "members": rows, "registry": {m: n for m, n in reg.items()}, "hand_registry": hand,
                       "sentence_members": {str(i): [m, src] for i, (m, src) in enumerate(sent_member) if src},
                       "label_files": [n for n in inst["names"] if n.startswith("XBRL/PublicDoc/") and n.endswith("_lab.xml")]}

    reg_for_b = reg if MEMBER_ON else {}
    def claim_member(si, pos):
        """変更 B: Claim 単位。OFF なら 3 本目の文単位の値をそのまま返す。"""
        if not (MEMBER_ON and B_ON):
            return sent_member[si]
        return claim_member_B(sentences[si], pos, reg_for_b, sent_member[si])

    SUBJECTS, UNIT_SCALE = P.SUBJECTS, P.UNIT_SCALE
    EXCLUDE_AFTER, EXCLUDE_CONTEXT, PCT_DIR_RE, PCT_RATIO_RE, NUM_RE = P.EXCLUDE_AFTER, P.EXCLUDE_CONTEXT, P.PCT_DIR_RE, P.PCT_RATIO_RE, P.NUM_RE
    subject_of, match_value, iter_numbers = P.subject_of, P.match_value, P.iter_numbers
    DIRECTION_WORDS, STATE_WORDS = P.DIRECTION_WORDS, P.STATE_WORDS

    # ---------- 数の Claim ----------
    num_claims = []
    class _M:
        def __init__(self, a, b): self._a, self._b = a, b
        def start(self): return self._a
        def end(self): return self._b
    for si, s in enumerate(sentences):
        for (a, b, signed, unit, prec) in iter_numbers(s):
            m = _M(a, b)
            member, msrc = claim_member(si, m.start())
            after = s[m.end():m.end() + 3]
            around = s[max(0, m.start() - 12):m.end() + 4]
            if EXCLUDE_AFTER.match(after) or EXCLUDE_CONTEXT.search(around):
                continue
            sign = -1 if signed < 0 else 1
            num = abs(signed)
            subj, elems = subject_of(s, m.start())
            claim = {"id": f"N{len(num_claims)+1:03d}", "sentence": si, "span": s[max(0, m.start()-30):m.end()+10], "value": sign * num, "unit": unit,
                     "subject": subj, "form": None, "pointer": None, "bound": False, "reason": None, "result": None, "recomputed": None}
            pm = PCT_DIR_RE.search(s[max(0, m.start()-25):m.end()+6]) if unit in ("％", "%") else None
            pr = PCT_RATIO_RE.search(s[max(0, m.start()-12):m.end()+3]) if unit in ("％", "%") and not pm else None
            if unit in ("％", "%") and pr:
                claim["form"] = "derived_value"
                if subj:
                    cur = [f for f in facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear")]
                    pri = [f for f in facts_for(elems, facts, contexts, member) if f["context"].startswith("Prior1Year")]
                    pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
                    if pairs:
                        c, p = pairs[0]
                        claim["pointer"] = [f"xbrl:{c['name']}@{c['context']}", f"xbrl:{p['name']}@{p['context']}", "formula:cur/prior*100"]
                        claim["bound"] = True
                        if p["value"] != 0:
                            ratio = c["value"] / p["value"] * 100
                            claim["recomputed"] = round(ratio, 2)
                            claim["result"] = "GROUNDED" if abs(ratio - num) <= 0.15 else "VALUE_MISMATCH"
                        else:
                            claim["result"] = "UNVERIFIABLE"; claim["reason"] = "prior is 0"
                    else:
                        claim["reason"] = "no_prior_member_context" if (member and member != AMBIG and cur) else "no_element"
                else:
                    claim["reason"] = "no_subject"
            elif unit in ("％", "%") and pm and (pm.group(4) or pm.group(7)):
                claim["form"] = "derived_value"
                sgn = 1 if (pm.group(4) or pm.group(7)) in ("増", "増加") else -1
                claim["value"] = sgn * num
                if subj:
                    cur = [f for f in facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear")]
                    pri = [f for f in facts_for(elems, facts, contexts, member) if f["context"].startswith("Prior1Year")]
                    pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
                    if pairs:
                        c, p = pairs[0]
                        claim["pointer"] = [f"xbrl:{c['name']}@{c['context']}", f"xbrl:{p['name']}@{p['context']}"]
                        claim["bound"] = True
                        if p["value"] != 0:
                            pct = (c["value"] - p["value"]) / abs(p["value"]) * 100
                            claim["recomputed"] = round(pct, 2)
                            claim["result"] = "GROUNDED" if abs(pct - claim["value"]) <= 0.15 else "VALUE_MISMATCH"
                        else:
                            claim["result"] = "UNVERIFIABLE"; claim["reason"] = "prior is 0"
                    else:
                        claim["reason"] = "no_prior_member_context" if (member and member != AMBIG and cur) else "no_element"
                else:
                    claim["reason"] = "no_subject"
            elif unit in UNIT_SCALE:
                claim["form"] = "direct_value"
                scale = prec if unit == "円" else UNIT_SCALE[unit]
                target = sign * num * (1.0 if unit == "円" else UNIT_SCALE[unit])
                pool = facts_for(elems, facts, contexts, member) if subj else [f for f in facts if ctx_ok(f["context"], contexts, member)]
                pool = [f for f in pool if f["unit"] and f["unit"].upper().startswith("JPY")]
                is_diff = bool(re.search(r"(増加|減少|増|減)", s[m.end():m.end() + 4])) or bool(re.search(r"(増加額|減少額|比べて)", s[max(0, m.start() - 25):m.start()]))
                hits = [(f, match_value(f["value"], target, scale)) for f in pool]
                hits = [(f, how) for f, how in hits if how]
                if hits and not (is_diff and subj):
                    fams = sorted({f["name"] for f, _ in hits})
                    if subj or len(fams) == 1:
                        f, how = hits[0]
                        claim["pointer"] = f"xbrl:{f['name']}@{f['context']}"; claim["bound"] = True; claim["result"] = "GROUNDED"
                        claim["recomputed"] = f["value"]; claim["match"] = how
                        if not subj: claim["reason"] = "value_only(no subject)"
                    else:
                        claim["reason"] = f"ambiguous({len(fams)} elements)"
                elif subj:
                    fs = facts_for(elems, facts, contexts, member)
                    fs = [f for f in fs if f["unit"] and f["unit"].upper().startswith("JPY")]
                    by = {}
                    for f in fs:
                        by.setdefault(f["name"], {})[f["context"]] = f
                    found = None
                    prev_year_phrase = "前連結会計年度は" in s[max(0, m.start() - 15):m.start()]
                    for name, ctxs in by.items():
                        def ctx(prefix):
                            return next((v for k, v in ctxs.items() if k.startswith(prefix)), None)
                        pairs = [("Prior1Year", "Prior2Year")] if prev_year_phrase else [("CurrentYear", "Prior1Year")]
                        for a_, b_ in pairs:
                            fa, fb = ctx(a_), ctx(b_)
                            if fa and fb:
                                how = match_value(fa["value"] - fb["value"], target, scale)
                                if how:
                                    found = (fa, fb, how); break
                        if found: break
                    if found:
                        fa, fb, how = found
                        claim["form"] = "derived_value"; claim["pointer"] = [f"xbrl:{fa['name']}@{fa['context']}", f"xbrl:{fb['name']}@{fb['context']}", "formula:a-b"]
                        claim["bound"] = True; claim["result"] = "GROUNDED"; claim["recomputed"] = fa["value"] - fb["value"]; claim["match"] = how
                    elif hits:
                        f, how = hits[0]
                        claim["pointer"] = f"xbrl:{f['name']}@{f['context']}"; claim["bound"] = True; claim["result"] = "GROUNDED"
                        claim["recomputed"] = f["value"]; claim["match"] = how; claim["reason"] = "diff phrase but value matched a fact"
                    else:
                        cur = [f for f in fs if f["context"].startswith("CurrentYear")]
                        if cur:
                            claim["pointer"] = f"xbrl:{cur[0]['name']}@{cur[0]['context']}"; claim["bound"] = True
                            claim["result"] = "VALUE_MISMATCH"; claim["recomputed"] = cur[0]["value"]; claim["reason"] = "value differs(segment/other period?)"
                        else:
                            claim["reason"] = "no_element"
                else:
                    claim["reason"] = "no_element"
            elif unit in ("％", "%", "ポイント"):
                claim["form"] = "direct_value"
                if subj and any((f["unit"] or "").lower().startswith("pure") for f in facts_for(elems, facts, contexts, member)):
                    cur = [f for f in facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear") and (f["unit"] or "").lower().startswith("pure")]
                    if cur:
                        fv = cur[0]["value"]; fvp = fv * 100 if abs(fv) <= 1.5 else fv
                        claim["pointer"] = f"xbrl:{cur[0]['name']}@{cur[0]['context']}"; claim["bound"] = True; claim["recomputed"] = round(fvp, 2)
                        claim["result"] = "GROUNDED" if abs(fvp - num) <= 0.15 else "VALUE_MISMATCH"
                    else:
                        claim["reason"] = "no_element"
                else:
                    claim["reason"] = "no_element(ratio without fact)" if subj else "no_subject"
            elif unit in ("名", "人"):
                claim["form"] = "direct_value"
                cur = [f for f in facts_for(["NumberOfEmployees"], facts, contexts, member) if f["context"].startswith("CurrentYear")]
                if subj and elems == ["NumberOfEmployees"] and cur:
                    hit = [f for f in cur if abs(f["value"] - num) <= 0.5]
                    claim["pointer"] = f"xbrl:{(hit or cur)[0]['name']}@{(hit or cur)[0]['context']}"; claim["bound"] = True
                    claim["result"] = "GROUNDED" if hit else "VALUE_MISMATCH"; claim["recomputed"] = (hit or cur)[0]["value"]
                else:
                    claim["reason"] = "no_element"
            else:
                claim["form"] = "direct_value"; claim["reason"] = "no_element(unit not in XBRL)"
            if MEMBER_ON:
                if msrc == "ambiguous" and not claim["bound"]:
                    claim["reason"] = "ambiguous(member)"
                claim["member"] = None if member == AMBIG else member; claim["member_source"] = msrc
            num_claims.append(claim)
    # ---------- 文章の Claim ----------
    text_claims = []
    for si, s in enumerate(sentences):
        if NUM_RE.search(s): pass
        for w, sg in DIRECTION_WORDS.items():
            for m in re.finditer(w, s):
                member, msrc = claim_member(si, m.start())
                subj, elems = subject_of(s, m.start())
                claim = {"id": f"T{len(text_claims)+1:03d}", "sentence": si, "word": w, "span": s[max(0, m.start()-30):m.end()+5], "subject": subj,
                         "form": "threshold", "pointer": None, "bound": False, "result": None, "reason": None}
                if subj:
                    cur = [f for f in facts_for(elems, facts, contexts, member) if f["context"].startswith("CurrentYear") and f["unit"] and f["unit"].upper().startswith("JPY")]
                    pri = [f for f in facts_for(elems, facts, contexts, member) if f["context"].startswith("Prior1Year")]
                    pairs = [(c, p) for c in cur for p in pri if c["name"] == p["name"] and c["context"].replace("CurrentYear", "") == p["context"].replace("Prior1Year", "")]
                    if pairs:
                        c, p = pairs[0]
                        claim["pointer"] = [f"xbrl:{c['name']}@{c['context']}", f"xbrl:{p['name']}@{p['context']}", "builtin:sign(cur-prior)"]
                        claim["bound"] = True
                        actual = 1 if c["value"] - p["value"] > 0 else -1
                        claim["result"] = "GROUNDED" if actual == sg else "VALUE_MISMATCH"
                        claim["recomputed"] = c["value"] - p["value"]
                    else:
                        claim["reason"] = "no_prior_member_context" if (member and member != AMBIG and cur) else "no_element"
                else:
                    claim["reason"] = "no_subject"
                if MEMBER_ON:
                    if msrc == "ambiguous" and not claim["bound"]:
                        claim["reason"] = "ambiguous(member)"
                    claim["member"] = None if member == AMBIG else member; claim["member_source"] = msrc
                text_claims.append(claim)
        for w in STATE_WORDS:
            for m in re.finditer(w, s):
                text_claims.append({"id": f"T{len(text_claims)+1:03d}", "sentence": si, "word": w, "span": s[max(0, m.start()-30):m.end()+5],
                                    "subject": None, "form": "threshold", "pointer": None, "bound": False, "result": "UNVERIFIABLE", "reason": "state_word(no line)"})
    # ---------- 集計(写し) ----------
    def rate(a, b): return round(100.0 * a / b, 1) if b else None
    nb = [c for c in num_claims if c["bound"]]
    tb = [c for c in text_claims if c["bound"]]
    recomp = [c for c in nb if c["form"] == "derived_value"]
    direct = [c for c in nb if c["form"] == "direct_value"]
    from collections import Counter
    stats = {
        "num_claims": len(num_claims), "num_bound": len(nb), "num_binding_rate_pct": rate(len(nb), len(num_claims)),
        "text_claims": len(text_claims), "text_bound": len(tb), "text_binding_rate_pct": rate(len(tb), len(text_claims)),
        "recompute_targets": len(recomp), "recompute_grounded": sum(c["result"] == "GROUNDED" for c in recomp),
        "recompute_match_rate_pct": rate(sum(c["result"] == "GROUNDED" for c in recomp), len(recomp)),
        "direct_targets": len(direct), "direct_grounded": sum(c["result"] == "GROUNDED" for c in direct),
        "direct_match_rate_pct": rate(sum(c["result"] == "GROUNDED" for c in direct), len(direct)),
        "num_forms": dict(Counter(c["form"] for c in num_claims)),
        "unbound_reasons_num": dict(Counter(c["reason"] for c in num_claims if not c["bound"])),
        "unbound_reasons_text": dict(Counter(c["reason"] for c in text_claims if not c["bound"])),
        "mismatch_num": [c["id"] for c in num_claims if c["result"] == "VALUE_MISMATCH"],
        "schemes_used": sorted({(p if isinstance(p, str) else p[0]).split(":")[0] for c in num_claims + text_claims for p in ([c["pointer"]] if isinstance(c["pointer"], str) else (c["pointer"] or []))}),
    }
    out = {"probe": "xbrl-probe-1", "date_listed": date, "selection_rule": "docTypeCode 120, xbrlFlag 1, consolidated jppfs facts > 0, min docID", "tried": tried,
           "document": {k: chosen.get(k) for k in ("docID", "filerName", "docDescription", "submitDateTime", "periodStart", "periodEnd", "edinetCode", "secCode")},
           "instance_source": inst["source"], "facts_total": len(facts), "contexts_total": len(contexts), "textblocks_total": len(tbs),
           "mdna_textblock": mdna_name, "mdna_chars": len(text), "mdna_sentences": len(sentences),
           "stats": stats, "num_claims": num_claims, "text_claims": text_claims}
    out["run"] = P.RUN; out["subjects_count"] = len(P.SUBJECTS)
    if MEMBER_ON:
        out["probe"] = "xbrl-probe-3"; out["run3"] = RUN3; out["member_binding"] = member_info
        out["baseline"] = {"probe2_json": os.path.basename(META_PATH), "zip_sha256": sha, "prediction_commit": "9651eca"}
        path = os.path.join(OUT_DIR, f"probe3{RUN3}_{chosen['docID']}.json")
        if A_ON or B_ON:
            tag = ("A" if A_ON else "") + ("B" if B_ON else "")
            out["probe"] = "xbrl-probe-4"; out["run4"] = tag
            out["probe4"] = {"A_vocab": [list(VOCAB4)] if A_ON else [], "B_marker_consolidated": MARK_CONSOL if B_ON else None,
                             "claim_members": {c["id"]: [c.get("member"), c.get("member_source")] for c in num_claims + text_claims if c.get("member_source")},
                             "baseline": {"probe3L_sha256": "168edc63ed53807183b57e184ff26de512037f20a4224769e1a1c94ae1e992d3", "prediction_commit": "0736a71"}}
            path = os.path.join(OUT_DIR, f"probe4{tag}_{chosen['docID']}.json")
    else:
        path = os.path.join(OUT_DIR, f"probe3_off_{chosen['docID']}.json")
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"member_on": MEMBER_ON, "run3": RUN3 if MEMBER_ON else None, "A": A_ON, "B": B_ON, "stats": stats,
                      "member_denominator": member_info["denominator"] if member_info else None}, ensure_ascii=False, indent=1))
    print("written:", path)
    return 0



if __name__ == "__main__":
    sys.exit(main())
