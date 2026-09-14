#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v977_remove_unused_resources.py <project_dir>')

root = Path(sys.argv[1]).resolve()
app = root / 'app'
res = app / 'src/main/res'
gradle = app / 'build.gradle'
version = root / 'VERSION.txt'

candidates = [
    ('drawable', 'chip_bg', res / 'drawable/chip_bg.xml'),
    ('drawable', 'dropdown_bg', res / 'drawable/dropdown_bg.xml'),
    ('raw', 'google_map_light_style', res / 'raw/google_map_light_style.json'),
    ('drawable', 'ic_filter', res / 'drawable/ic_filter.xml'),
    ('drawable', 'ic_launcher_foreground', res / 'drawable/ic_launcher_foreground.xml'),
    ('drawable', 'ic_logo_pin', res / 'drawable/ic_logo_pin.xml'),
    ('drawable', 'ic_search', res / 'drawable/ic_search.xml'),
    ('drawable', 'outline_button', res / 'drawable/outline_button.xml'),
    ('drawable', 'panel', res / 'drawable/panel.xml'),
    ('drawable', 'welcome_bubble_blue', res / 'drawable/welcome_bubble_blue.xml'),
    ('drawable', 'welcome_bubble_green', res / 'drawable/welcome_bubble_green.xml'),
    ('drawable', 'welcome_bubble_purple', res / 'drawable/welcome_bubble_purple.xml'),
]

text_suffixes = {'.java','.kt','.xml','.json','.gradle','.kts','.properties','.pro','.txt'}
all_files = [p for p in app.rglob('*') if p.is_file() and 'build' not in p.parts and p.suffix.lower() in text_suffixes]
removed=[]
for kind,name,path in candidates:
    if not path.is_file():
        raise SystemExit(f'expected lint candidate is missing before cleanup: {path}')
    patterns = [
        re.compile(r'@' + re.escape(kind) + r'/' + re.escape(name) + r'\b'),
        re.compile(r'R\.' + re.escape(kind) + r'\.' + re.escape(name) + r'\b'),
        re.compile(r'getIdentifier\s*\(\s*["\']' + re.escape(name) + r'["\']'),
    ]
    refs=[]
    for other in all_files:
        if other.resolve() == path.resolve() or not other.is_file():
            continue
        try: text=other.read_text(encoding='utf-8')
        except UnicodeDecodeError: continue
        if any(p.search(text) for p in patterns): refs.append(str(other.relative_to(root)))
    if refs:
        raise SystemExit(f'refusing to delete referenced resource {kind}/{name}: {refs}')
    path.unlink()
    removed.append(f'{kind}/{name}')

if len(removed) != len(candidates):
    raise SystemExit(f'expected to remove {len(candidates)} resources, removed {len(removed)}')

g = gradle.read_text(encoding='utf-8')
if not re.search(r'(?m)^\s*targetSdk\s+35\s*$', g):
    raise SystemExit('Step 9 must keep targetSdk 35 unchanged')
g = re.sub(r'(?m)^\s*versionCode\s+83\s*$', '        versionCode 84', g, count=1)
g = re.sub(r"(?m)^\s*versionName\s+['\"]9\.4\.76['\"]\s*$", "        versionName '9.4.77'", g, count=1)
gradle.write_text(g, encoding='utf-8')
version.write_text('9.4.77\n', encoding='utf-8')

print('Applied JobBubble V9.4.77 unused-resource cleanup: ' + ', '.join(removed))
