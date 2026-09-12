#!/usr/bin/env python3
from pathlib import Path
import re,sys

if len(sys.argv)!=2:
    raise SystemExit('usage: inspect_category_icons.py <project_dir>')
root=Path(sys.argv[1])
java=root/'app/src/main/java/com/jobbubble/app/MainActivity.java'
s=java.read_text(encoding='utf-8')
lines=s.splitlines()
terms=('category','transport','truck','security','health','medical','technology','computer','construction','restaurant','food','retail','warehouse','logistics','icon')
print('=== CATEGORY/ICON CANDIDATES ===')
seen=set()
for i,line in enumerate(lines):
    low=line.lower()
    if any(t in low for t in terms):
        if i in seen: continue
        start=max(0,i-2); end=min(len(lines),i+3)
        block='\n'.join(f'{j+1}: {lines[j]}' for j in range(start,end))
        if len(block)>1800: block=block[:1800]
        print(block); print('---')
        seen.update(range(start,end))
print('=== END CATEGORY/ICON CANDIDATES ===')
