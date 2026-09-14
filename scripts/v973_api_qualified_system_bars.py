#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v973_api_qualified_system_bars.py <project_dir>')

project = Path(sys.argv[1]).resolve()
res = project / 'app/src/main/res'
base_path = res / 'values/styles.xml'
version_path = project / 'VERSION.txt'

if not base_path.is_file():
    raise SystemExit(f'missing styles file: {base_path}')

base = base_path.read_text(encoding='utf-8')
required = {
    'android:windowLightNavigationBar': 'false',
    'android:enforceNavigationBarContrast': 'false',
    'android:enforceStatusBarContrast': 'false',
}

# Remove API-specific framework attributes from the API-23 base resource. Use only
# horizontal whitespace here: \s would also consume newlines/indentation belonging
# to the following XML tag.
for name, value in required.items():
    pattern = re.compile(
        rf'^[ \t]*<item[ \t]+name=["\']{re.escape(name)}["\']>{re.escape(value)}</item>[ \t]*(?:\r?\n)?',
        re.MULTILINE,
    )
    base, count = pattern.subn('', base, count=1)
    if count != 1:
        raise SystemExit(f'expected exactly one {name}={value} item in base styles.xml; found {count}')

if '<style name="AppTheme"' not in base or '</style>' not in base:
    raise SystemExit('AppTheme style not found after API-specific cleanup')

base_path.write_text(base, encoding='utf-8')


def with_items(source: str, items: list[tuple[str, str]]) -> str:
    lines = ''.join(f'        <item name="{name}">{value}</item>\n' for name, value in items)
    match = re.search(r'(?m)^[ \t]*</style>[ \t]*$', source)
    if not match:
        raise SystemExit('could not locate AppTheme closing tag')
    return source[:match.start()] + lines + source[match.start():]

# API 27 gained light navigation bar control.
v27 = with_items(base, [
    ('android:windowLightNavigationBar', 'false'),
])

# API 29 gained status/navigation contrast enforcement controls. Because values-v29
# replaces the whole style definition, include the API-27 navigation flag here too.
v29 = with_items(base, [
    ('android:windowLightNavigationBar', 'false'),
    ('android:enforceNavigationBarContrast', 'false'),
    ('android:enforceStatusBarContrast', 'false'),
])

for qualifier, text in [('values-v27', v27), ('values-v29', v29)]:
    directory = res / qualifier
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / 'styles.xml'
    if target.exists():
        existing = target.read_text(encoding='utf-8')
        if existing != text:
            raise SystemExit(f'refusing to overwrite unexpected existing resource: {target}')
    target.write_text(text, encoding='utf-8')

version_path.write_text('9.4.73\n', encoding='utf-8')
print('Applied JobBubble V9.4.73 API-qualified system-bar theme compatibility fix')
