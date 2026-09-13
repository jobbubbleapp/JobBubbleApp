from pathlib import Path

patch = Path('scripts/v947_patch.py')
s = patch.read_text(encoding='utf-8')
marker = '# Refactor cleanup: remove private methods proven to have no callers.'
if marker in s:
    raise SystemExit('Refactor cleanup already present')

cleanup = r'''

# Refactor cleanup: remove private methods proven to have no callers.
def _remove_private_java_method(text, name):
    import re as _re
    pattern = _re.compile(
        r'(?m)^[ \t]*private\s+(?:static\s+)?(?:final\s+)?[\w<>\[\].?, ]+\s+' +
        _re.escape(name) + r'\s*\([^;{]*\)\s*\{'
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit(f'Dead-method cleanup target not found: {name}')
    start = match.start()
    brace = text.find('{', match.start(), match.end())
    if brace < 0:
        raise SystemExit(f'Opening brace not found for: {name}')

    depth = 0
    state = 'code'
    escaped = False
    i = brace
    end = None
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if state == 'code':
            if ch == '/' and nxt == '/':
                state = 'line'; i += 2; continue
            if ch == '/' and nxt == '*':
                state = 'block'; i += 2; continue
            if ch == '"':
                state = 'string'; escaped = False; i += 1; continue
            if ch == "'":
                state = 'char'; escaped = False; i += 1; continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        elif state == 'line':
            if ch == '\n': state = 'code'
        elif state == 'block':
            if ch == '*' and nxt == '/':
                state = 'code'; i += 2; continue
        elif state in ('string', 'char'):
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif (state == 'string' and ch == '"') or (state == 'char' and ch == "'"):
                state = 'code'
        i += 1

    if end is None:
        raise SystemExit(f'Closing brace not found for: {name}')
    while end < len(text) and text[end] in ' \t': end += 1
    if end < len(text) and text[end] == '\r': end += 1
    if end < len(text) and text[end] == '\n': end += 1
    if end < len(text) and text[end] == '\n': end += 1
    return text[:start] + text[end:]

_dead_methods = [
    'addForeignCountryLabel',
    'bboxIntersects',
    'bestAddressText',
    'chooseBestListingLocation',
    'chooseCompanyLocation',
    'companyTokensMatch',
    'correctJobCoordinates',
    'drawGeoCurtainPath',
    'followJob',
    'installForeignCountryCurtains',
    'isGenericCompanyName',
    'looksLikeStreetAddress',
    'ovalStrokeBg',
    'renderExpandedPile',
    'renderStrictRegionMaskTile',
    'selectedRegionOutline',
    'shortCompanyName',
    'tileYToLatitude',
    'violetGlassBg',
]
_refactored = java.read_text(encoding='utf-8')
for _method in _dead_methods:
    _refactored = _remove_private_java_method(_refactored, _method)
java.write_text(_refactored, encoding='utf-8')
print(f'Removed {len(_dead_methods)} dead MainActivity methods')
'''

patch.write_text(s.rstrip() + cleanup + '\n', encoding='utf-8')

for dead in [
    Path('scripts/v942_patch.py'),
    Path('JobBubble-V9.4.40-USA-ONLY-MAPS-debug.apk'),
]:
    if dead.exists():
        dead.unlink()

print('Applied JobBubble Android refactor cleanup')
