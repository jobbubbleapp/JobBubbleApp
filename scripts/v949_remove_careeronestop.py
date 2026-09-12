#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v949_remove_careeronestop.py <project_dir>')

project = Path(sys.argv[1])
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
layout = project / 'app/src/main/res/layout/activity_main.xml'
version = project / 'VERSION.txt'

text = main.read_text(encoding='utf-8')

# CareerOneStop/NLx is no longer a JobBubble source. Earlier patches kept one
# compatibility mapping so old saved preferences would silently fall back to
# All sources; remove that legacy provider name entirely from the compiled app.
text = re.sub(r'(?m)^.*(?:CareerOneStop|NLx).*(?:\n|$)', '', text)
main.write_text(text, encoding='utf-8')

# The old attribution view was already removed by v943. Guard against any old
# ZIP variant reintroducing the provider name in the main layout.
if layout.exists():
    x = layout.read_text(encoding='utf-8')
    if 'CareerOneStop' in x or 'NLx' in x:
        raise SystemExit('CareerOneStop/NLx still present in activity_main.xml')

# Remove unused bundled provider source if an older project ZIP still contains it.
for rel in [
    'backend/providers/careeronestop.js',
    'app/src/main/assets/careeronestop.js',
]:
    p = project / rel
    if p.exists():
        p.unlink()

if 'CareerOneStop' in main.read_text(encoding='utf-8') or 'NLx' in main.read_text(encoding='utf-8'):
    raise SystemExit('CareerOneStop/NLx still present in MainActivity.java')

if version.exists():
    version.write_text('9.4.49\n', encoding='utf-8')

print('Removed CareerOneStop/NLx from the Android app')
