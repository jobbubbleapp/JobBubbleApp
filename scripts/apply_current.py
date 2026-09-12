#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: apply_current.py <project_dir>')

project = Path(sys.argv[1]).resolve()
root = Path(__file__).resolve().parent
steps = [
    'v943_patch.py',
    'v944_patch.py',
    'v947_patch.py',
    'v948_cleanup.py',
    'v949_remove_careeronestop.py',
    'v950_muse_runtime_fix.py',
    'v951_location_fetch_fix.py',
    'v952_muse_location_query_fix.py',
]

for script in steps:
    path = root / script
    if not path.is_file():
        raise SystemExit(f'missing patch step: {path}')
    print(f'Applying {script}...')
    subprocess.run([sys.executable, str(path), str(project)], check=True)

print('Current JobBubble patch pipeline applied successfully.')
