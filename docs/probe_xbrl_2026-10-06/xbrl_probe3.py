# -*- coding: utf-8 -*-
"""XBRL 探り 3 本目(使い捨て)。予測 docs/XBRL_PROBE3_PREDICTION_2026-10-06.md(コミット 9651eca)§3 の設計をそのまま機械にした。
- 2 本目の script(xbrl_probe.py、sha 896492a7…)は変更しない。この file が import して、語彙 73・正規表現・P-1〜P-7 の関数をそのまま使う。
- 変えるのは §5 の範囲だけ: (1) context の選別(member 付き context を population の値として読む)、(2) member 対応表の読み込み(Run L = label linkbase、Run R = 手書きの登録簿)、(3) 切替の配管。
- PROBE_MEMBER=0 のとき member の解決を一切行わず、2 本目の JSON を byte 一致で再現する(byte freeze gate。§5)。
- 材料は API を叩かず、保管済みの ZIP(sha256 を照合)と 2 本目の JSON の書類メタデータ(date_listed / tried / document)を使う。鍵は要らない。
"""
import os, sys, re, json, zipfile, io, hashlib, unicodedata
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("PROBE_RUN", "B")          # 語彙 73(凍結)
import xbrl_probe as P                            # 2 本目の script。変更しない

MEMBER_ON = os.environ.get("PROBE_MEMBER", "1") != "0"
RUN3 = os.environ.get("PROBE_RUN3", "L")          # L = ラベルだけ(主)/ R = ラベル + 手書きの登録簿(探索)
ZIP_PATH = os.environ.get("PROBE_ZIP")            # 保管済み ZIP
ZIP_SHA = "d617b6e1807c8aa6d2b1269f6b25ff57a6a71dbf683020f1859d2d4a04c02d26"   # 予測 §2
META_PATH = os.environ.get("PROBE_META", os.path.join(HERE, "probe2B_S100Z4B6.json"))
REGISTRY_PATH = os.environ.get("PROBE_REGISTRY", os.path.join(HERE, "probe3_registry_S100Z4B6.json"))
OUT_DIR = os.environ.get("PROBE_OUT", HERE)
CARRY_BACK = 5                                     # §3.1-2: 同じ段落で 5 文以内
AMBIG = "<ambiguous>"                              # 1 文に 2 つ以上の事業名

XLINK = "{http://www.w3.org/1999/xlink}"
XML = "{http://www.w3.org/XML/1998/namespace}"


# ---------- (1) context の選別 ----------
def ctx_ok(cid, contexts, member):
    """member が None なら 2 本目と同じ plain_context。member が決まっていれば、その member だけを持つ連結の context(置き換え。合わせない。§3.1-3)。"""
    if member is None:
        return P.plain_context(cid, contexts)
    c = contexts.get(cid) or {}
    return c.get("members") == [member] and "NonConsolidated" not in cid


def facts_for(elems, facts, contexts, member=None, want_ctx=None):
    """P.facts_for の写し。違いは plain_context → ctx_ok(member) だけ。要素の選び方(完全一致 → 部分一致)は凍結のまま。"""
    exact, loose = [], []
    for f in facts:
        local = f["name"].split(":")[-1]
        if not ctx_ok(f["context"], contexts, member): continue
        if want_ctx and not f["context"].startswith(want_ctx): continue
        if any(local == e or local == e + "SummaryOfBusinessResults" or local == e.replace("Income", "IncomeLoss") + "SummaryOfBusinessResults" for e in elems):
            exact.append(f)
        elif any(e.lower() in local.lower() for e in elems):
            loose.append(f)
    return exact or loose


# ---------- (2) member 対応表 ----------
def member_denominator(contexts):
    """分母(§3.2): 当期または前期の連結の Duration context に現れる explicitMember の異なり。結果を見て変えない。"""
    ms = set()
    for cid, c in contexts.items():
        if not (c.get("start") and c.get("end")): continue
        if "NonConsolidated" in cid: continue
        if not (cid.startswith("CurrentYear") or cid.startswith("Prior1Year")): continue
        for m in c.get("members") or []:
            ms.add(m)
    return sorted(ms)


def labels_from_zip(z, names):
    """会社拡張の label linkbase(XBRL/PublicDoc/*_lab.xml、日本語)から 要素 id → 標準ラベル を引く。標準タクソノミのラベルは ZIP に無い。"""
    out = {}
    for n in names:
        if not (n.startswith("XBRL/PublicDoc/") and n.endswith("_lab.xml")): continue
        root = ET.fromstring(z.read(n))
        loc_id, lab_text, arcs = {}, {}, []
        for el in root.iter():
            tag = el.tag.split("}")[-1]
            if tag == "loc":
                href = el.get(XLINK + "href") or ""
                loc_id[el.get(XLINK + "label")] = href.split("#")[-1]
            elif tag == "label":
                role = el.get(XLINK + "role") or ""
                lang = el.get(XML + "lang") or ""
                if role.endswith("/label") and lang.startswith("ja"):
                    lab_text[el.get(XLINK + "label")] = el.text or ""
            elif tag == "labelArc":
                arcs.append((el.get(XLINK + "from"), el.get(XLINK + "to")))
        for a, b in arcs:
            if a in loc_id and b in lab_text:
                out[loc_id[a]] = unicodedata.normalize("NFKC", lab_text[b].strip())
    return out


def build_registry(members, id2label, text, run3):
    """Run L: ラベルが MD&A の本文に現れる member だけ(人は書かない)。Run R: 手書きの登録簿 {事業名: member} を足す。"""
    reg = {}   # member → 事業名(文に当てる語)
    rows = []
    for m in members:
        mid = m.replace(":", "_")
        lab = id2label.get(mid)
        in_text = bool(lab) and lab in text
        rows.append({"member": m, "label": lab, "label_in_mdna": in_text, "source": "label" if in_text else None})
        if in_text:
            reg[m] = lab
    hand = {}
    if run3 == "R" and os.path.exists(REGISTRY_PATH):
        hand = json.load(open(REGISTRY_PATH, encoding="utf-8"))
        for name, m in hand.items():
            if m in reg: continue
            reg[m] = unicodedata.normalize("NFKC", name)
            for r in rows:
                if r["member"] == m: r["source"] = "hand"
    return reg, rows, hand


def resolve_members(sentences, paras, reg):
    """§3.1-2。文ごとに (member, source)。source は sentence / carried / ambiguous / None。"""
    res = []
    for si, s in enumerate(sentences):
        hits = sorted({m for m, name in reg.items() if name and name in s})
        if len(hits) == 1:
            res.append((hits[0], "sentence"))
        elif len(hits) >= 2:
            res.append((AMBIG, "ambiguous"))
        else:
            found = None
            for sj in range(si - 1, max(-1, si - 1 - CARRY_BACK), -1):
                if paras[sj] != paras[si]: break
                if res[sj][1] == "sentence":
                    found = res[sj][0]; break
            res.append((found, "carried" if found else None))
    return res


def paragraph_index(text, sentences):
    """凍結の文の切り方(re.split(r"(?<=。)|\\n"))と同じ列になることを確かめながら、文ごとの段落番号を作る。"""
    paras, check = [], []
    for pi, para in enumerate(text.split("\n")):
        for s in re.split(r"(?<=。)", para):
            if s and s.strip():
                paras.append(pi); check.append(unicodedata.normalize("NFKC", s.strip()))
    assert check == sentences, "paragraph split diverged from frozen sentence split"
    return paras


# ---------- main(2 本目の main の写し。差分は member の差し込みだけ) ----------
def main():
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
        member, msrc = sent_member[si]
        for (a, b, signed, unit, prec) in iter_numbers(s):
            m = _M(a, b)
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
        member, msrc = sent_member[si]
        if NUM_RE.search(s): pass
        for w, sg in DIRECTION_WORDS.items():
            for m in re.finditer(w, s):
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
    else:
        path = os.path.join(OUT_DIR, f"probe3_off_{chosen['docID']}.json")
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"member_on": MEMBER_ON, "run3": RUN3 if MEMBER_ON else None, "stats": stats,
                      "member_denominator": member_info["denominator"] if member_info else None}, ensure_ascii=False, indent=1))
    print("written:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
