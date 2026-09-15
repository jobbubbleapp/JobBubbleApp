#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v980_firebase_dependencies.py <project_dir>')

root=Path(sys.argv[1]).resolve(); gradle=root/'app/build.gradle'; version=root/'VERSION.txt'
g=gradle.read_text(encoding='utf-8')
# Firestore 26.6.0 is compatible with the current build toolchain. Firebase Auth
# 24.2.0 currently ships Kotlin 2.3 metadata, which AGP 8.7.3/R8 8.7 cannot
# cleanly process. Preserve Auth 23.2.1 until a dedicated build-tooling upgrade.
old='com.google.firebase:firebase-firestore:25.1.4'; new='com.google.firebase:firebase-firestore:26.6.0'
if old not in g: raise SystemExit(f'missing Firebase dependency target: {old}')
g=g.replace(old,new,1)
required=(
    'androidx.appcompat:appcompat:1.8.0',
    'com.google.android.material:material:1.14.0',
    'com.google.android.gms:play-services-location:21.3.0',
    'com.google.android.gms:play-services-maps:20.0.0',
    'com.google.android.gms:play-services-auth:21.3.0',
    'com.google.firebase:firebase-auth:23.2.1',
)
for dep in required:
    if dep not in g: raise SystemExit(f'validated dependency unexpectedly changed: {dep}')
if 'com.google.firebase:firebase-auth:24.2.0' in g:
    raise SystemExit('Firebase Auth 24.2.0 must remain deferred in Step 9')
if not re.search(r'(?m)^\s*targetSdk\s+35\s*$',g):
    raise SystemExit('Step 9 must keep targetSdk 35 unchanged')
g=re.sub(r'(?m)^\s*versionCode\s+86\s*$','        versionCode 87',g,count=1)
g=re.sub(r"(?m)^\s*versionName\s+['\"]9\.4\.79['\"]\s*$","        versionName '9.4.80'",g,count=1)
gradle.write_text(g,encoding='utf-8')
version.write_text('9.4.80\n',encoding='utf-8')
print('Applied JobBubble V9.4.80 Firestore 26.6.0; kept Firebase Auth 23.2.1 for current-toolchain compatibility')
