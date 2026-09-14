#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v974_sync_android_version.py <project_dir>')

project = Path(sys.argv[1]).resolve()
gradle = project / 'app/build.gradle'
version_file = project / 'VERSION.txt'

if not gradle.is_file():
    raise SystemExit(f'missing Android app Gradle file: {gradle}')

text = gradle.read_text(encoding='utf-8')

code_match = re.search(r'(?m)^(?P<indent>[ \t]*)versionCode[ \t]+(?P<code>\d+)[ \t]*$', text)
name_match = re.search(r"(?m)^(?P<indent>[ \t]*)versionName[ \t]+(?P<quote>['\"])(?P<name>[^'\"]+)(?P=quote)[ \t]*$", text)
if not code_match or not name_match:
    raise SystemExit('could not find versionCode/versionName in app/build.gradle')

# The source seed is still 9.4.41 / code 80. Refuse to silently overwrite an
# unexpected package version; future releases should deliberately update this patch.
if code_match.group('code') != '80':
    raise SystemExit(f'unexpected seed versionCode {code_match.group("code")}; expected 80')
if name_match.group('name') != '9.4.41':
    raise SystemExit(f'unexpected seed versionName {name_match.group("name")}; expected 9.4.41')

text = (
    text[:code_match.start()]
    + f"{code_match.group('indent')}versionCode 81"
    + text[code_match.end():]
)
# Re-find after the first replacement so offsets cannot go stale.
name_match = re.search(r"(?m)^(?P<indent>[ \t]*)versionName[ \t]+(?P<quote>['\"])(?P<name>[^'\"]+)(?P=quote)[ \t]*$", text)
if not name_match:
    raise SystemExit('versionName disappeared after versionCode update')
text = (
    text[:name_match.start()]
    + f"{name_match.group('indent')}versionName '9.4.74'"
    + text[name_match.end():]
)

gradle.write_text(text, encoding='utf-8')
version_file.write_text('9.4.74\n', encoding='utf-8')

# Verify the final package declarations are unique and exactly synchronized.
final = gradle.read_text(encoding='utf-8')
if len(re.findall(r'(?m)^\s*versionCode\s+', final)) != 1:
    raise SystemExit('versionCode declaration is not unique after patch')
if len(re.findall(r'(?m)^\s*versionName\s+', final)) != 1:
    raise SystemExit('versionName declaration is not unique after patch')
if not re.search(r'(?m)^\s*versionCode\s+81\s*$', final):
    raise SystemExit('versionCode 81 was not materialized')
if not re.search(r"(?m)^\s*versionName\s+['\"]9\.4\.74['\"]\s*$", final):
    raise SystemExit('versionName 9.4.74 was not materialized')

print('Applied JobBubble V9.4.74 Android package version metadata sync (versionCode 81)')
