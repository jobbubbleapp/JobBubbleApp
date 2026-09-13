#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v966a_disable_logo_request.py <project_dir>')

project = Path(sys.argv[1]).resolve()
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
s = main.read_text(encoding='utf-8')

line = '        if(j.company!=null&&!j.company.trim().isEmpty())requestCompanyLogo(j.company);\n'
count = s.count(line)
if count < 1:
    raise SystemExit('expected active company-logo request line not found')

s = s.replace(line, '')
main.write_text(s, encoding='utf-8')
print(f'Removed {count} active company-logo request call(s) before V9.4.66 artwork patch')
