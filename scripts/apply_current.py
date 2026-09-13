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
    'v953_blank_unknown_bubble_pay.py',
    'v954_compact_map_ui.py',
    'v955_fix_compact_marker_compile.py',
    'v956_unknown_pay_detail_label.py',
    'v957_logo_category_fallback.py',
    'v958_meaningful_category_icons.py',
    'v959_visible_vector_fallback.py',
    'v960_unified_category_vectors.py',
    'v961_group_company_logos.py',
    'v962_top_safe_area.py',
    'v963_filter_control_clipping_fix.py',
    'v964_compact_top_controls.py',
]

for script in steps:
    path = root / script
    if not path.is_file():
        raise SystemExit(f'missing patch step: {path}')
    print(f'Applying {script}...')
    subprocess.run([sys.executable, str(path), str(project)], check=True)

print('Current JobBubble patch pipeline applied successfully.')
