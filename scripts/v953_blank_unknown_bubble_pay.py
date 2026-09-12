#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v953_blank_unknown_bubble_pay.py <project_dir>')

project = Path(sys.argv[1])
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
s = main.read_text(encoding='utf-8')

# Unknown compensation should not add a placeholder line to map bubbles. Keep real
# pay values unchanged; only remove the user-facing "not listed" fallback text.
patterns = [
    r'"Pay\s+not\s+listed"',
    r'"Pay:\s*not\s+listed"',
    r'"Salary\s+not\s+listed"',
    r'"Compensation\s+not\s+listed"',
]

changed = 0
for pattern in patterns:
    s, n = re.subn(pattern, '""', s, flags=re.IGNORECASE)
    changed += n

if changed == 0:
    raise SystemExit('No unknown-pay placeholder text was found to blank')

main.write_text(s, encoding='utf-8')
print(f'Blanked {changed} unknown-pay bubble placeholder(s); real pay text is unchanged')
