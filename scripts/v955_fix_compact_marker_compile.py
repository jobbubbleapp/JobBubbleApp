#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=2:
    raise SystemExit('usage: v955_fix_compact_marker_compile.py <project_dir>')
root=Path(sys.argv[1])
java=root/'app/src/main/java/com/jobbubble/app/MainActivity.java'
s=java.read_text(encoding='utf-8')
old=s
s=s.replace('RectF card=new RectF(', 'android.graphics.RectF card=new android.graphics.RectF(')
s=s.replace('RectF dest=new RectF(', 'android.graphics.RectF dest=new android.graphics.RectF(')
s=s.replace('RectF db=new RectF(', 'android.graphics.RectF db=new android.graphics.RectF(')
if s==old:
    raise SystemExit('compact marker RectF targets not found')
java.write_text(s,encoding='utf-8')
print('Fixed compact marker RectF references')
