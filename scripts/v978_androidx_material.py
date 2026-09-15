#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v978_androidx_material.py <project_dir>')
root=Path(sys.argv[1]).resolve(); gradle=root/'app/build.gradle'; version=root/'VERSION.txt'
g=gradle.read_text(encoding='utf-8')
expected={
    "androidx.appcompat:appcompat:1.7.0":"androidx.appcompat:appcompat:1.8.0",
    "com.google.android.material:material:1.12.0":"com.google.android.material:material:1.14.0",
}
for old,new in expected.items():
    if old not in g: raise SystemExit(f'missing dependency target: {old}')
    g=g.replace(old,new,1)
if not re.search(r'(?m)^\s*targetSdk\s+35\s*$',g): raise SystemExit('Step 9 must keep targetSdk 35 unchanged')
g=re.sub(r'(?m)^\s*versionCode\s+84\s*$','        versionCode 85',g,count=1)
g=re.sub(r"(?m)^\s*versionName\s+['\"]9\.4\.77['\"]\s*$","        versionName '9.4.78'",g,count=1)
gradle.write_text(g,encoding='utf-8'); version.write_text('9.4.78\n',encoding='utf-8')
print('Applied JobBubble V9.4.78 AndroidX AppCompat 1.8.0 + Material 1.14.0 dependency upgrade')
