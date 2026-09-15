#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v979_google_play_services.py <project_dir>')
root=Path(sys.argv[1]).resolve(); gradle=root/'app/build.gradle'; manifest=root/'app/src/main/AndroidManifest.xml'; version=root/'VERSION.txt'
g=gradle.read_text(encoding='utf-8')
# Keep play-services-location at 21.3.0 for this audit. 21.4.0 resolves and builds,
# but its Kotlin 2.3 metadata produces incompatibility diagnostics with the current
# Android lint/toolchain. Defer that upgrade until the dedicated build-tooling test.
if 'com.google.android.gms:play-services-location:21.3.0' not in g:
    raise SystemExit('expected play-services-location 21.3.0 baseline')
old='com.google.android.gms:play-services-maps:19.0.0'; new='com.google.android.gms:play-services-maps:20.0.0'
if old not in g: raise SystemExit(f'missing dependency target: {old}')
g=g.replace(old,new,1)
# Do NOT upgrade play-services-auth 21.3.0 in this step. JobBubble still uses the
# legacy GoogleSignInClient/GoogleSignInOptions APIs removed from auth 22.0.0.
if "com.google.android.gms:play-services-auth:21.3.0" not in g:
    raise SystemExit('legacy Google Sign-In compatibility dependency unexpectedly changed')
if not re.search(r'(?m)^\s*targetSdk\s+35\s*$',g): raise SystemExit('Step 9 must keep targetSdk 35 unchanged')
g=re.sub(r'(?m)^\s*versionCode\s+85\s*$','        versionCode 86',g,count=1)
g=re.sub(r"(?m)^\s*versionName\s+['\"]9\.4\.78['\"]\s*$","        versionName '9.4.79'",g,count=1)
gradle.write_text(g,encoding='utf-8')

m=manifest.read_text(encoding='utf-8')
entry='<uses-library android:name="org.apache.http.legacy" android:required="false" />'
if entry not in m:
    app=re.search(r'<application\b[^>]*>',m,re.S)
    if not app: raise SystemExit('AndroidManifest application element missing')
    m=m[:app.end()]+'\n        '+entry+m[app.end():]
manifest.write_text(m,encoding='utf-8')
version.write_text('9.4.79\n',encoding='utf-8')
print('Applied JobBubble V9.4.79 Maps 20.0.0; kept location/auth 21.3.0 and added legacy HTTP compatibility declaration')
