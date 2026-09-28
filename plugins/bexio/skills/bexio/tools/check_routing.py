#!/usr/bin/env python3
"""check_routing.py: structure check of the core router (SKILL.md §8) and routing-cases.json.

Checks structure only, not routing semantics:
1. every expected skill exists (skills/<name>/SKILL.md) or is an outcome: lookup, ask, not covered;
2. every deciding row text occurs in exactly one line of §8, and that line names the expected skill;
3. §8.2 owns each of the 34 tools in op-map.json exactly once, no unknown tool.
Stdlib only. Exit 1 on any failure. Run: python3 check_routing.py
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILLS = HERE.parent.parent
core = (HERE.parent / 'SKILL.md').read_text()
sec8 = core[core.index('## 8. Router'):core.index('## 9.')]
sec82 = sec8[sec8.index('### 8.2'):]
lines8 = sec8.splitlines()
OUTCOMES = {'lookup', 'ask', 'not covered'}
errors = []

# 1 + 2: cases
cases = json.load(open(HERE / 'routing-cases.json'))['cases']
ids = [c['id'] for c in cases]
if len(ids) != len(set(ids)):
    errors.append('duplicate case ids')
for c in cases:
    exp, rows = c['expected'], c['row']
    if not exp or len(exp) != len(rows):
        errors.append(f"{c['id']}: expected / row count differ")
        continue
    for skill, row in zip(exp, rows):
        if skill not in OUTCOMES and not (SKILLS / skill / 'SKILL.md').is_file():
            errors.append(f"{c['id']}: unknown skill {skill}")
        hits = [l for l in lines8 if row in l]
        if len(hits) != 1:
            errors.append(f"{c['id']}: row found {len(hits)}x in §8: {row!r}")
        elif skill not in OUTCOMES and f'`{skill}`' not in hits[0]:
            errors.append(f"{c['id']}: row does not name {skill}: {row!r}")

# 3: ownership
tools = set(json.load(open(HERE / 'op-map.json'))['tools'])
owned = []
for l in sec82.splitlines():
    cells = [x.strip() for x in l.strip().strip('|').split('|')]
    if len(cells) == 3 and re.fullmatch(r'`bexio-[a-z]+`', cells[1]):
        if not (SKILLS / cells[1].strip('`') / 'SKILL.md').is_file():
            errors.append(f'§8.2 unknown skill {cells[1]}')
        owned += re.findall(r'`(bexio_[a-z_]+)`', cells[2])
dups = sorted({t for t in owned if owned.count(t) > 1})
missing, unknown = sorted(tools - set(owned)), sorted(set(owned) - tools)
if len(tools) != 34 or dups or missing or unknown:
    errors.append(f'§8.2 ownership: tools={len(tools)} dups={dups} missing={missing} unknown={unknown}')

by_set = {}
for c in cases:
    by_set[c['set']] = by_set.get(c['set'], 0) + 1
print(f"cases {len(cases)} {by_set} · §8.2 owns {len(set(owned))}/34 tools once")
if errors:
    print('\n'.join(errors))
    sys.exit(1)
print('OK')
