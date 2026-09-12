from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

root = Path(sys.argv[1]).resolve()
version = root / 'VERSION.txt'
main = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'

if not main.exists():
    raise SystemExit(f'Missing MainActivity.java under {root}')

TEXT_EXTENSIONS = {
    '.java', '.kt', '.kts', '.xml', '.gradle', '.properties', '.json', '.js', '.mjs',
    '.cjs', '.md', '.txt', '.yml', '.yaml', '.html', '.css', '.pro', '.cfg'
}
SKIP_PARTS = {'.gradle', 'build', '.idea', '.git', 'node_modules'}


def is_text_source(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS and not any(part in SKIP_PARTS for part in path.parts)


def normalize_text(path: Path) -> bool:
    raw = path.read_text(encoding='utf-8')
    text = raw.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    # Keep source readable without creating giant vertical gaps.
    out = []
    blank_run = 0
    for line in lines:
        if line:
            blank_run = 0
            out.append(line)
        else:
            blank_run += 1
            if blank_run <= 2:
                out.append(line)
    text = '\n'.join(out).rstrip() + '\n'
    if text != raw:
        path.write_text(text, encoding='utf-8')
        return True
    return False


# Remove obsolete experiments and generated artifacts from the packaged source tree.
removed = []
for rel in (
    'backend/providers/indeed.js',
    'backend/providers/glassdoor.js',
    'backend/providers/ziprecruiter.js',
):
    p = root / rel
    if p.exists():
        p.unlink()
        removed.append(rel)

for p in list(root.rglob('*')):
    if not p.is_file() or any(part in SKIP_PARTS for part in p.parts):
        continue
    if p.name in {'.DS_Store', 'Thumbs.db'} or p.suffix.lower() in {'.apk', '.aab'}:
        try:
            p.unlink()
            removed.append(str(p.relative_to(root)))
        except OSError:
            pass

# Normalize source text and collect files for validation.
normalized = []
source_files = []
for p in root.rglob('*'):
    if p.is_file() and is_text_source(p):
        source_files.append(p)
        try:
            if normalize_text(p):
                normalized.append(str(p.relative_to(root)))
        except UnicodeDecodeError:
            raise SystemExit(f'Non-UTF8 text source: {p.relative_to(root)}')

# Catch bad merges and accidental placeholders before they ever become an APK.
conflict_re = re.compile(r'^(<{7}|={7}|>{7})(?:\s|$)', re.MULTILINE)
conflicts = []
for p in source_files:
    text = p.read_text(encoding='utf-8')
    if conflict_re.search(text):
        conflicts.append(str(p.relative_to(root)))
if conflicts:
    raise SystemExit('Unresolved merge conflict markers: ' + ', '.join(conflicts))

# Validate every XML and JSON source file. Broken resources/config should fail early.
validated_xml = 0
validated_json = 0
for p in source_files:
    if p.suffix.lower() == '.xml':
        ET.parse(p)
        validated_xml += 1
    elif p.suffix.lower() == '.json':
        json.loads(p.read_text(encoding='utf-8'))
        validated_json += 1

# Retheme the actual category/source filter dialogs without stripping JobBubble's
# intentional brand purple elsewhere. These dialogs are identified by their own copy.
s = main.read_text(encoding='utf-8')


def method_span(text: str, marker: str):
    idx = text.find(marker)
    if idx < 0:
        return None
    candidates = [
        text.rfind('\n    private ', 0, idx),
        text.rfind('\n    public ', 0, idx),
        text.rfind('\n    protected ', 0, idx),
    ]
    start = max(candidates)
    if start < 0:
        return None
    start += 1
    ends = [
        p for p in (
            text.find('\n    private ', idx + 1),
            text.find('\n    public ', idx + 1),
            text.find('\n    protected ', idx + 1),
        ) if p >= 0
    ]
    return start, min(ends) if ends else len(text)


def navy_token(token: str) -> str:
    prefix = '#' if token.startswith('#') else '0x'
    digits = token[1:] if prefix == '#' else token[2:]
    if len(digits) == 8:
        alpha, rgb = digits[:2], digits[2:]
    elif len(digits) == 6:
        alpha, rgb = '', digits
    else:
        return token
    try:
        r, g, b = (int(rgb[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return token
    # Purple/violet: both red and blue materially exceed green.
    if not (b > g * 1.16 and r > g * 1.12 and max(r, b) - g >= 4 and max(r, b) >= 25):
        return token
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mx = max(r, g, b)
    if mx < 55 and lum < 32:
        mapped = '071C2C'
    elif mx < 110 and lum < 58:
        mapped = '0D2A40'
    else:
        mapped = '315D78'
    return prefix + alpha + mapped


def retheme_dialog(text: str, markers, label: str):
    total = 0
    touched_spans = set()
    for marker in markers:
        span = method_span(text, marker)
        if span is None or span in touched_spans:
            continue
        touched_spans.add(span)
        start, end = span
        block = text[start:end]
        changed = 0
        def repl(m):
            nonlocal changed
            before = m.group(0)
            after = navy_token(before)
            if after != before:
                changed += 1
            return after
        new_block = re.sub(r'#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?|0x[0-9A-Fa-f]{8}', repl, block)
        if changed:
            text = text[:start] + new_block + text[end:]
            total += changed
            print(f'{label}: replaced {changed} legacy purple literal(s) near {marker!r}')
    return text, total


s, category_theme_changes = retheme_dialog(
    s,
    ('Choose a category to filter jobs.', 'Retail & Sales', 'Job category'),
    'Job category dialog',
)
s, source_theme_changes = retheme_dialog(
    s,
    ('Choose which job source to show.', 'All sources', 'Job source'),
    'Job source dialog',
)

# Keep migration support for old CareerOneStop saved values, but eliminate stale
# user-facing provider copy if any survived earlier patches.
s = s.replace('CareerOneStop / NLx listings', 'All enabled job sources')
s = s.replace('CareerOneStop attribution is shown here instead of covering the map.',
              'Legacy provider settings are migrated automatically.')

# Normalize the Java file one last time after edits.
main.write_text(s, encoding='utf-8')
normalize_text(main)

# Structural sanity checks for the current feature set.
final_main = main.read_text(encoding='utf-8')
required = {
    'The Muse source': 'The Muse',
    'salary unknown handling': '(j.pay<=0||j.pay>=minPay)',
    'large cluster list behavior': 'if(pile.jobIndexes.size()>5)',
    'dark map style': 'R.raw.google_map_dark_style',
    'category control': 'categoryChip',
    'source control': 'sourceChip',
}
missing = [name for name, needle in required.items() if needle not in final_main]
if missing:
    raise SystemExit('Missing required JobBubble behavior after cleanup: ' + ', '.join(missing))

# Report complexity hotspots instead of blindly rewriting working code.
java_lines = final_main.count('\n')
method_count = len(re.findall(r'^\s+(?:private|public|protected)\s+[^;=]+\([^;]*\)\s*\{', final_main, re.MULTILINE))
if java_lines > 5000:
    print(f'NOTICE: MainActivity.java is {java_lines} lines; future refactor should split UI/network/map responsibilities into separate classes.')
print(f'MainActivity methods detected: {method_count}')

if version.exists():
    version.write_text('9.4.48\n', encoding='utf-8')

print('JobBubble V9.4.48 cleanup complete')
print(f'Normalized text files: {len(normalized)}')
print(f'Removed obsolete/generated files: {len(removed)}')
print(f'Validated XML files: {validated_xml}')
print(f'Validated JSON files: {validated_json}')
print(f'Category theme replacements: {category_theme_changes}')
print(f'Source theme replacements: {source_theme_changes}')
