# C-0: 探りの JSON を Core の 4 層へ写す(写す規則はこの file が唯一)。Core のコードではない。
import json, sys, re, hashlib
from collections import Counter
STATE = {  # 未束縛の理由 → Core の状態(2026-10-06 人間が C-0 で固定)
    'no_element': 'POINTER_NOT_FOUND', 'no_element(unit not in XBRL)': 'POINTER_NOT_FOUND', 'no_element(ratio without fact)': 'POINTER_NOT_FOUND',
    'no_prior_member_context': 'POINTER_NOT_FOUND',
    'no_subject': 'UNVERIFIABLE', 'ambiguous(member)': 'UNVERIFIABLE', 'state_word(no line)': 'UNVERIFIABLE', 'prior is 0': 'UNVERIFIABLE',
}
def state_of(c):
    if c['result'] in ('GROUNDED', 'VALUE_MISMATCH', 'UNVERIFIABLE'): return c['result']
    r = c.get('reason') or ''
    if r in STATE: return STATE[r]
    if r.startswith('ambiguous('): return 'UNVERIFIABLE'
    raise KeyError(r)
def ctx_of(ptr):  # 'xbrl:name@context' → (name, context)
    name, ctx = ptr[5:].split('@'); return name, ctx
def period(ctx):
    m = re.match(r'(CurrentYear|Prior1Year|Prior2Year)(Duration|Instant)', ctx); return (m.group(1), m.group(2)) if m else ('?', '?')
def member_of(ctx):
    parts = ctx.split('_', 1); return parts[1] if len(parts) > 1 and 'Member' in parts[1] else None
def map_claim(c, kind):
    ptrs = c['pointer'] if isinstance(c['pointer'], list) else ([c['pointer']] if c['pointer'] else [])
    xptrs = [p for p in ptrs if p.startswith('xbrl:')]; others = [p for p in ptrs if not p.startswith('xbrl:')]
    schemes = sorted({p.split(':')[0] for p in ptrs})
    form = {'direct_value': 'direct_value', 'derived_value': 'derived_value', 'threshold': 'threshold'}[c['form']]
    tr = [period(ctx_of(p)[1]) for p in xptrs]
    pop = None
    if xptrs:
        mems = {member_of(ctx_of(p)[1]) for p in xptrs}; pop = 'member:' + mems.pop() if len(mems) == 1 and None not in mems else ('consolidated' if mems == {None} else 'mixed')
    elif c.get('member'): pop = 'member:' + c['member'].split(':')[-1]
    # contract
    if kind == 'text':
        comparator = 'builtin:sign(cur-prior)==direction'; tol = None
    elif form == 'direct_value':
        comparator = 'equals_within' if c['unit'] not in ('%', '％', 'ポイント') else 'equals_within(pure*100)'; tol = 'max(decimals, claim_scale/2)' if c['unit'] not in ('%', '％', 'ポイント') else '0.15pt'
    else:
        f = others[0] if others else ''
        comparator = {'formula:cur/prior*100': 'ratio*100', 'formula:a-b': 'diff(a-b) equals_within'}.get(f, 'pct_change(cur,prior)'); tol = '0.15pt' if comparator != 'diff(a-b) equals_within' else 'max(decimals, claim_scale/2)'
    norm = c.get('match')  # round / truncate / abs+round / abs+truncate
    prov = []
    if (c.get('reason') or '').startswith('value_only'): prov.append('value_only')
    if c.get('reason') == 'diff phrase but value matched a fact': prov.append('diff_phrase_direct')
    if c.get('sign_token'): prov.append('sign_token')
    if c.get('member_source'): prov.append('member_source:' + c['member_source'])
    return {'id': c['id'], 'kind': kind, 'form': form, 'subject': c.get('subject'), 'value': c.get('value'), 'unit': c.get('unit'), 'word': c.get('word'),
            'modifiers': {'population': pop, 'time_range': tr or None, 'normalization': norm},
            'evidence': {'schemes': schemes, 'pointers': ptrs},
            'contract': {'comparator': comparator if ptrs else None, 'tolerance': tol if ptrs else None},
            'result': {'state': state_of(c), 'recomputed': c.get('recomputed'), 'script_reason': c.get('reason')}, 'provenance': prov}
out = {}
for tag, f in (('1B', 'probe1B_S100Z4Q1.json'), ('5F', 'probe5F_S100Z4B6.json')):
    d = json.load(open(f)); rows = [map_claim(c, 'num') for c in d['num_claims']] + [map_claim(c, 'text') for c in d['text_claims']]
    sha = hashlib.sha256(open(f, 'rb').read()).hexdigest()
    exp = {'source': f, 'source_sha256': sha, 'document': d['document']['docID'], 'claims': rows}
    json.dump(exp, open(f'core_expectation_{tag}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    out[tag] = rows
    print(f'=== {tag} ({f}) claims', len(rows))
    print(' form', dict(Counter(r['form'] for r in rows)))
    print(' state', dict(Counter(r['result']['state'] for r in rows)))
    print(' state by kind', dict(Counter((r['kind'], r['result']['state']) for r in rows)))
    print(' population', dict(Counter((r['modifiers']['population'] or 'none').split(':')[0] for r in rows)))
    print(' time_range', dict(Counter(json.dumps(r['modifiers']['time_range']) for r in rows if r['modifiers']['time_range'])))
    print(' normalization', dict(Counter(r['modifiers']['normalization'] for r in rows if r['modifiers']['normalization'])))
    print(' schemes', dict(Counter(json.dumps(r['evidence']['schemes']) for r in rows if r['evidence']['schemes'])))
    print(' comparator', dict(Counter(r['contract']['comparator'] for r in rows if r['contract']['comparator'])))
    print(' provenance', dict(Counter(p for r in rows for p in r['provenance'])))
    print(' script reasons mapped', dict(Counter((r['result']['script_reason'], r['result']['state']) for r in rows if r['result']['script_reason'])))
