#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=2:
    raise SystemExit('usage: v958_meaningful_category_icons.py <project_dir>')

root=Path(sys.argv[1])
java=root/'app/src/main/java/com/jobbubble/app/MainActivity.java'
version=root/'VERSION.txt'
s=java.read_text(encoding='utf-8')

def replace_method(src, marker, replacement):
    idx=src.find(marker)
    if idx<0:
        raise SystemExit(f'method target not found: {marker}')
    start=src.rfind('\n',0,idx)+1
    brace=src.find('{',idx)
    if brace<0:
        raise SystemExit(f'opening brace not found: {marker}')
    depth=0; i=brace; state='code'
    while i<len(src):
        ch=src[i]; nx=src[i+1] if i+1<len(src) else ''
        if state=='code':
            if ch=='"': state='string'
            elif ch=="'": state='char'
            elif ch=='/' and nx=='/': state='line'; i+=1
            elif ch=='/' and nx=='*': state='block'; i+=1
            elif ch=='{': depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:
                    return src[:start]+replacement+src[i+1:]
        elif state=='string':
            if ch=='\\': i+=1
            elif ch=='"': state='code'
        elif state=='char':
            if ch=='\\': i+=1
            elif ch=="'": state='code'
        elif state=='line':
            if ch=='\n': state='code'
        elif state=='block':
            if ch=='*' and nx=='/': state='code'; i+=1
        i+=1
    raise SystemExit(f'closing brace not found: {marker}')

# One shared category-icon function is used by BOTH the Job Category picker and
# the map-bubble fallback. Matching by category family rather than exact text
# prevents provider/category wording variations from falling through to a dot.
new_choice='''    private String choiceIcon(String item){
        if(item==null)return "💼";
        String x=item.trim().toLowerCase(Locale.US);
        if(x.equals("all jobs")||x.equals("all sources"))return "▦";
        if(x.contains("transport")||x.contains("delivery")||x.contains("driver")||x.contains("truck"))return "🚚";
        if(x.contains("security")||x.contains("public safety")||x.contains("police")||x.contains("guard"))return "🛡";
        if(x.contains("health")||x.contains("medical")||x.contains("nurs"))return "✚";
        if(x.contains("technology")||x.contains("engineering")||x.contains("software")||x.contains("computer"))return "💻";
        if(x.contains("construction")||x.contains("skilled trade")||x.contains("maintenance"))return "🛠";
        if(x.contains("food")||x.contains("hospitality")||x.contains("restaurant"))return "🍴";
        if(x.contains("retail")||x.contains("sales"))return "🛍";
        if(x.contains("warehouse")||x.contains("logistics")||x.contains("fulfillment"))return "📦";
        if(x.contains("office")||x.contains("administration"))return "▥";
        if(x.contains("customer service"))return "☎";
        if(x.contains("government"))return "★";
        if(x.contains("education"))return "▤";
        if(x.contains("finance")||x.contains("accounting"))return "$";
        if(x.contains("manufacturing")||x.contains("production"))return "⚙";
        if(x.contains("cleaning")||x.contains("facilities"))return "✦";
        if(x.equals("adzuna"))return "A";
        if(x.equals("usajobs"))return "US";
        if(x.equals("the muse")||x.equals("muse"))return "TM";
        return "💼";
    }
'''
s=replace_method(s,'private String choiceIcon(String item)',new_choice)

# Transportation previously fell through to the generic green category color.
# Give it its own clear map/category accent while leaving the other existing
# category colors unchanged.
old_cat='private String categoryHex(String cat){if(cat==null)return "#38D89A";String c=cat.toLowerCase(Locale.US);'
new_cat='private String categoryHex(String cat){if(cat==null)return "#38D89A";String c=cat.toLowerCase(Locale.US);if(c.contains("transport")||c.contains("delivery"))return "#2563EB";'
if old_cat in s:
    s=s.replace(old_cat,new_cat,1)
elif 'c.contains("transport")||c.contains("delivery")' not in s:
    raise SystemExit('categoryHex patch target not found')

java.write_text(s,encoding='utf-8')
version.write_text('9.4.57\n',encoding='utf-8')
print('Applied V9.4.57 meaningful shared job-category icons for bubble fallbacks')
