#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v956_unknown_pay_detail_label.py <project_dir>')

root = Path(sys.argv[1])
java = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = root / 'VERSION.txt'
s = java.read_text(encoding='utf-8')
original = s

# When a provider does not publish compensation, the job-detail card must not
# present $0.0/hr as if it were a real wage. Keep real positive pay unchanged.
replacement = '(j.pay>0?("$"+j.pay+"/hr"):"See listing for pay")'
patterns = [
    r'"\$"\s*\+\s*j\.pay\s*\+\s*"/hr"',
    r'String\.format\(Locale\.US\s*,\s*"\$%\.1f/hr"\s*,\s*j\.pay\s*\)',
    r'String\.format\(java\.util\.Locale\.US\s*,\s*"\$%\.1f/hr"\s*,\s*j\.pay\s*\)',
]

changed = 0
for pattern in patterns:
    s, n = re.subn(pattern, replacement, s)
    changed += n

if changed == 0:
    candidates = [line.strip() for line in s.splitlines() if 'j.pay' in line and ('/hr' in line or '$' in line)]
    raise SystemExit('Unknown-pay detail target not found. Candidates: ' + ' | '.join(candidates[:12]))

java.write_text(s, encoding='utf-8')
version.write_text('9.4.55\n', encoding='utf-8')
print(f'Updated {changed} job-detail pay label(s): unknown pay now says See listing for pay')
