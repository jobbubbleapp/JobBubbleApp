#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v948_cleanup.py <project_dir>')

project = Path(sys.argv[1])
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
text = main.read_text(encoding='utf-8')

# These helpers are legacy code paths that are no longer referenced by the app.
# A method is removed only when its name occurs exactly once in MainActivity.java
# (the declaration itself). If a future patch starts using one again, it is kept.
DEAD_METHODS = [
    'addForeignCountryLabel',
    'bboxIntersects',
    'bestAddressText',
    'chooseCompanyLocation',
    'correctJobCoordinates',
    'followJob',
    'isGenericCompanyName',
    'ovalStrokeBg',
    'renderExpandedPile',
    'shortCompanyName',
    'tileYToLatitude',
    'violetGlassBg',
    'chooseBestListingLocation',
    'companyTokensMatch',
    'looksLikeStreetAddress',
]


def method_span(src: str, name: str):
    decl = re.compile(
        r'(?m)^[ \t]*(?:public|private|protected)?[ \t]*'
        r'(?:static[ \t]+)?(?:final[ \t]+)?(?:synchronized[ \t]+)?'
        r'(?:[\w<>\[\],.?]+[ \t]+)+' + re.escape(name) +
        r'[ \t]*\([^;{}]*\)[ \t]*\{'
    )
    match = decl.search(src)
    if not match:
        return None
    brace = src.find('{', match.start(), match.end())
    depth = 0
    i = brace
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    while i < len(src):
        c = src[i]
        n = src[i + 1] if i + 1 < len(src) else ''
        if line_comment:
            if c == '\n':
                line_comment = False
        elif block_comment:
            if c == '*' and n == '/':
                block_comment = False
                i += 1
        elif quote:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == quote:
                quote = None
        else:
            if c == '/' and n == '/':
                line_comment = True
                i += 1
            elif c == '/' and n == '*':
                block_comment = True
                i += 1
            elif c in ('\"', "'"):
                quote = c
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    while end < len(src) and src[end] in ' \t':
                        end += 1
                    if end < len(src) and src[end] == '\n':
                        end += 1
                    return match.start(), end
        i += 1
    raise RuntimeError(f'unbalanced method body for {name}')

removed = []
preserved = []
for name in DEAD_METHODS:
    calls = len(re.findall(r'\b' + re.escape(name) + r'\s*\(', text))
    if calls != 1:
        preserved.append((name, calls))
        continue
    span = method_span(text, name)
    if not span:
        preserved.append((name, calls))
        continue
    text = text[:span[0]] + text[span[1]:]
    removed.append(name)

# Keep formatting compact without changing executable code.
text = re.sub(r'\n{4,}', '\n\n\n', text)
main.write_text(text, encoding='utf-8')

print(f'Removed {len(removed)} dead MainActivity helpers: {", ".join(removed)}')
if preserved:
    print('Preserved methods that are referenced or no longer present: ' + ', '.join(f'{n}({c})' for n, c in preserved))
