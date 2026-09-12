#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: probe_runtime_flow.py <project_dir>')

project = Path(sys.argv[1])
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
lines = main.read_text(encoding='utf-8').splitlines()

needles = [
    'jobbubble-backend',
    '/jobs?',
    'HttpURLConnection',
    'new URL(',
    'loadJobs(',
    'refreshJobs(',
    'fetchJobs(',
    'refineJobs(',
    'sourceApiValue(',
    'themuse',
    'getJSONArray("jobs")',
    'optJSONArray("jobs")',
    'new JSONObject',
    'navList.setOnClickListener',
    'showClusterSideList(',
    'sourceChip.setOnClickListener',
    'distanceValue.setOnClickListener',
    'makeJobBubble',
    'renderSingleJobMarker',
    'payText',
    'payLabel',
    'Pay not listed',
    'pay not listed',
    'Not listed',
    'Apply',
]

seen = set()
print('=== JobBubble runtime-flow probe ===')
for needle in needles:
    hits = [i for i, line in enumerate(lines) if needle in line]
    if not hits:
        continue
    print(f'\n--- {needle!r}: {len(hits)} hit(s) ---')
    for i in hits[:8]:
        start = max(0, i - 12)
        end = min(len(lines), i + 18)
        key = (start, end)
        if key in seen:
            continue
        seen.add(key)
        for n in range(start, end):
            print(f'{n+1:05d}: {lines[n]}')
        print('---')

print('=== end runtime-flow probe ===')
