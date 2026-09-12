from pathlib import Path
import sys, json, re

root=Path(sys.argv[1])
java=root/'app/src/main/java/com/jobbubble/app/MainActivity.java'
raw=root/'app/src/main/res/raw'
version=root/'VERSION.txt'
s=java.read_text(encoding='utf-8')

# V9.4.47: dark appearance must style the actual Google map; light stays default Google Maps.
old='''            // Keep the map itself on Google Maps default styling. UI theme still applies to JobBubble controls.\n            googleMap.setMapStyle(null);\n            removeForeignCountryCurtains();'''
new='''            // JobBubble dark mode styles the actual Google map. Light mode remains normal Google Maps.\n            if("dark".equals(mapTheme)) googleMap.setMapStyle(MapStyleOptions.loadRawResourceStyle(this,R.raw.google_map_dark_style));\n            else googleMap.setMapStyle(new MapStyleOptions("[]"));\n            removeForeignCountryCurtains();'''
if old in s:
    s=s.replace(old,new,1)
elif 'R.raw.google_map_dark_style' not in s:
    raise SystemExit('Map theme patch target not found')

# Match dark settings/support sheets to the same deep navy family as the app exterior.
s=s.replace('light?"#ECEDEF":"#0B1A29"','light?"#ECEDEF":"#071C2C"')
s=s.replace('light?"#E2E4E8":"#10283A"','light?"#E2E4E8":"#0D2A40"')
s=s.replace('light?"#C3C7CD":"#31546C"','light?"#C3C7CD":"#315D78"')

# The main Job category and Job source filter sheets predate the theme work and still
# contain fixed violet/purple literals. Retheme only the methods that own those two
# controls so brand purple elsewhere in JobBubble is left alone.
def _method_span(marker):
    idx=s.find(marker)
    if idx < 0:
        return None
    starts=[s.rfind('\n    private ',0,idx),s.rfind('\n    public ',0,idx),s.rfind('\n    protected ',0,idx)]
    start=max(starts)
    if start < 0:
        return None
    start += 1
    ends=[p for p in (s.find('\n    private ',idx+1),s.find('\n    public ',idx+1),s.find('\n    protected ',idx+1)) if p >= 0]
    end=min(ends) if ends else len(s)
    return start,end

def _navy_token(token):
    original=token
    if token.startswith('#'):
        digits=token[1:]
        kind='#'
    elif token.lower().startswith('0x'):
        digits=token[2:]
        kind='0x'
    else:
        return original
    if len(digits)==8:
        alpha=digits[:2]
        rgb=digits[2:]
    elif len(digits)==6:
        alpha=''
        rgb=digits
    else:
        return original
    try:
        r,g,b=(int(rgb[i:i+2],16) for i in (0,2,4))
    except ValueError:
        return original

    # Purple/violet has both red and blue above green. This deliberately does not
    # match the new navy colors (their red channel is below green) or semantic
    # red/green status colors used by the filters.
    purple=(b > g*1.20 and r > g*1.15 and max(r,b)-g >= 4 and max(r,b) >= 25)
    if not purple:
        return original

    lum=0.2126*r+0.7152*g+0.0722*b
    mx=max(r,g,b)
    if mx < 55 and lum < 32:
        mapped='071C2C'      # sheet/exterior
    elif mx < 105 and lum < 52:
        mapped='0D2A40'      # cards/buttons
    else:
        mapped='315D78'      # borders, selected controls, icons, CTA
    out=alpha+mapped
    return ('#'+out) if kind=='#' else ('0x'+out)

def _retheme_filter(marker,label):
    global s
    span=_method_span(marker)
    if span is None:
        return 0
    start,end=span
    block=s[start:end]
    changed=0
    def repl(m):
        nonlocal changed
        before=m.group(0)
        after=_navy_token(before)
        if after != before:
            changed += 1
        return after
    block=re.sub(r'#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?|0x[0-9A-Fa-f]{8}',repl,block)
    if changed:
        s=s[:start]+block+s[end:]
        print(f'Rethemed {label}: {changed} purple color literal(s)')
    return changed

category_changes=_retheme_filter('Retail & Sales','Job category filter')
if category_changes==0:
    category_changes=_retheme_filter('Job category','Job category filter')
source_changes=_retheme_filter('final String[] src={','Job source filter')
if source_changes==0:
    source_changes=_retheme_filter('Job source','Job source filter')
if category_changes==0:
    raise SystemExit('Job category filter theme target not found or already had no purple literals')
if source_changes==0:
    raise SystemExit('Job source filter theme target not found or already had no purple literals')

# Correct appearance copy now that dark mode also changes Google Maps.
s=s.replace('Choose the JobBubble interface theme. The map itself keeps the normal Google Maps appearance.',
            'Choose the JobBubble appearance. Dark mode also applies a dark Google Maps style.')

raw.mkdir(parents=True,exist_ok=True)
style=[
 {"elementType":"geometry","stylers":[{"color":"#0b1f2d"}]},
 {"elementType":"labels.text.fill","stylers":[{"color":"#d7e5ef"}]},
 {"elementType":"labels.text.stroke","stylers":[{"color":"#071723"}]},
 {"featureType":"administrative","elementType":"geometry.stroke","stylers":[{"color":"#36566b"}]},
 {"featureType":"poi","elementType":"geometry","stylers":[{"color":"#102b35"}]},
 {"featureType":"poi.park","elementType":"geometry","stylers":[{"color":"#12372f"}]},
 {"featureType":"road","elementType":"geometry","stylers":[{"color":"#1c3545"}]},
 {"featureType":"road","elementType":"geometry.stroke","stylers":[{"color":"#0d2534"}]},
 {"featureType":"road.highway","elementType":"geometry","stylers":[{"color":"#31566b"}]},
 {"featureType":"transit","elementType":"geometry","stylers":[{"color":"#173241"}]},
 {"featureType":"water","elementType":"geometry","stylers":[{"color":"#06131d"}]},
 {"featureType":"water","elementType":"labels.text.fill","stylers":[{"color":"#8bb8d0"}]}
]
(raw/'google_map_dark_style.json').write_text(json.dumps(style,separators=(',',':')),encoding='utf-8')

if version.exists(): version.write_text('9.4.47\n',encoding='utf-8')
java.write_text(s,encoding='utf-8')
print('Applied JobBubble V9.4.47 dark map/menu theme patch')
