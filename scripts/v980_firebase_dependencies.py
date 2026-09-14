#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v980_firebase_dependencies.py <project_dir>')
root=Path(sys.argv[1]).resolve(); gradle=root/'app/build.gradle'; version=root/'VERSION.txt'
g=gradle.read_text(encoding='utf-8')
for old,new in {
    'com.google.firebase:firebase-auth:23.2.1':'com.google.firebase:firebase-auth:24.2.0',
    'com.google.firebase:firebase-firestore:25.1.4':'com.google.firebase:firebase-firestore:26.6.0',
}.items():
    if old not in g: raise SystemExit(f'missing dependency target: {old}')
    g=g.replace(old,new,1)
if not re.search(r'(?m)^\s*targetSdk\s+35\s*$',g): raise SystemExit('Step 9 must keep targetSdk 35 unchanged')
g=re.sub(r'(?m)^\s*versionCode\s+86\s*$','        versionCode 87',g,count=1)
g=re.sub(r"(?m)^\s*versionName\s+['\"]9\.4\.79['\"]\s*$","        versionName '9.4.80'",g,count=1)
gradle.write_text(g,encoding='utf-8'); version.write_text('9.4.80\n',encoding='utf-8')
print('Applied JobBubble V9.4.80 Firebase Auth 24.2.0 + Firestore 26.6.0 dependency upgrade')
