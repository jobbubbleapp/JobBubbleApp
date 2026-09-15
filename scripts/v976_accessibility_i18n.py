#!/usr/bin/env python3
from pathlib import Path
from xml.sax.saxutils import escape
import html
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v976_accessibility_i18n.py <project_dir>')

root = Path(sys.argv[1]).resolve()
res = root / 'app/src/main/res'
main = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
gradle = root / 'app/build.gradle'
version = root / 'VERSION.txt'

values = {}
value_to_key = {}
used_keys = set()

def slug(value, fallback):
    decoded = html.unescape(value).strip()
    words = re.findall(r'[A-Za-z0-9]+', decoded.lower())
    base = '_'.join(words[:7])
    if not base or base[0].isdigit():
        base = fallback + ('_' + base if base else '')
    base = ('step9_' + base)[:70].rstrip('_')
    key = base
    n = 2
    while key in used_keys and values.get(key) != decoded:
        key = f'{base}_{n}'; n += 1
    used_keys.add(key)
    return key, decoded

attr_re = re.compile(r'android:(text|hint|contentDescription)="([^"]*)"')
externalized = 0
decorative = 0
for layout in sorted((res / 'layout').glob('*.xml')):
    text = layout.read_text(encoding='utf-8')
    def repl(m):
        global externalized, decorative
        attr, raw = m.group(1), m.group(2)
        if raw.startswith('@') or raw.startswith('?'):
            return m.group(0)
        if attr == 'contentDescription' and raw == '':
            decorative += 1
            return 'android:contentDescription="@null"'
        if raw == '':
            return m.group(0)
        decoded = html.unescape(raw).strip()
        if decoded in value_to_key:
            key = value_to_key[decoded]
        else:
            fallback = f'{layout.stem}_{attr.lower()}_{len(values)+1}'
            key, decoded = slug(raw, fallback)
            value_to_key[decoded] = key
            values[key] = decoded
        externalized += 1
        return f'android:{attr}="@string/{key}"'
    text = attr_re.sub(repl, text)

    # Relative layout attributes preserve current LTR placement and support RTL.
    text = text.replace('android:layout_marginLeft=', 'android:layout_marginStart=')
    text = text.replace('android:layout_marginRight=', 'android:layout_marginEnd=')
    text = text.replace('android:paddingLeft=', 'android:paddingStart=')
    text = text.replace('android:paddingRight=', 'android:paddingEnd=')
    text = text.replace('android:layout_gravity="top|left"', 'android:layout_gravity="top|start"')
    text = text.replace('android:layout_gravity="top|right"', 'android:layout_gravity="top|end"')
    text = re.sub(r'android:gravity="left([|\"]?)', lambda m: 'android:gravity="start' + m.group(1), text)
    text = re.sub(r'android:gravity="right([|\"]?)', lambda m: 'android:gravity="end' + m.group(1), text)

    # The main toolbar logo had one-sided 5dp padding on a multiline ImageView tag.
    # Match across line breaks and add the corresponding relative end padding.
    if layout.name == 'activity_main.xml':
        text = re.sub(
            r'(<[^>]*android:paddingStart="5dp")(?![^>]*android:paddingEnd=)',
            r'\1 android:paddingEnd="5dp"', text, count=1, flags=re.S)
    layout.write_text(text, encoding='utf-8')

s = main.read_text(encoding='utf-8')
s = s.replace('Gravity.RIGHT', 'Gravity.END')
main.write_text(s, encoding='utf-8')

out = res / 'values/step9_strings.xml'
def android_string(v):
    return escape(v, {'"': '&quot;'}).replace("'", "\\'")
lines = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
for key in sorted(values):
    lines.append(f'    <string name="{key}">{android_string(values[key])}</string>')
lines.append('</resources>')
out.write_text('\n'.join(lines) + '\n', encoding='utf-8')

if externalized < 50:
    raise SystemExit(f'expected at least 50 XML literals to externalize, got {externalized}')
if decorative != 3:
    raise SystemExit(f'expected 3 decorative empty image descriptions, got {decorative}')

g = gradle.read_text(encoding='utf-8')
if not re.search(r'(?m)^\s*targetSdk\s+35\s*$', g):
    raise SystemExit('Step 9 must keep targetSdk 35 unchanged')
g = re.sub(r'(?m)^\s*versionCode\s+82\s*$', '        versionCode 83', g, count=1)
g = re.sub(r"(?m)^\s*versionName\s+['\"]9\.4\.75['\"]\s*$", "        versionName '9.4.76'", g, count=1)
gradle.write_text(g, encoding='utf-8')
version.write_text('9.4.76\n', encoding='utf-8')

print(f'Applied JobBubble V9.4.76 accessibility/i18n cleanup: {externalized} XML literals externalized, {decorative} decorative images marked @null')
