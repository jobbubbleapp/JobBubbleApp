#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v965_half_height_top_controls.py <project_dir>')

project = Path(sys.argv[1]).resolve()
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
layout = project / 'app/src/main/res/layout/activity_main.xml'
version = project / 'VERSION.txt'

text = main.read_text(encoding='utf-8')
xml = layout.read_text(encoding='utf-8')


def replace_method(src, marker, replacement):
    idx = src.find(marker)
    if idx < 0:
        raise SystemExit(f'method not found: {marker}')
    start = src.rfind('\n', 0, idx) + 1
    brace = src.find('{', idx)
    if brace < 0:
        raise SystemExit(f'opening brace not found: {marker}')
    depth = 0
    i = brace
    state = 'code'
    while i < len(src):
        ch = src[i]
        nx = src[i+1] if i+1 < len(src) else ''
        if state == 'code':
            if ch == '"': state = 'string'
            elif ch == "'": state = 'char'
            elif ch == '/' and nx == '/': state = 'line'; i += 1
            elif ch == '/' and nx == '*': state = 'block'; i += 1
            elif ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return src[:start] + replacement + src[i+1:]
        elif state == 'string':
            if ch == '\\': i += 1
            elif ch == '"': state = 'code'
        elif state == 'char':
            if ch == '\\': i += 1
            elif ch == "'": state = 'code'
        elif state == 'line':
            if ch == '\n': state = 'code'
        elif state == 'block':
            if ch == '*' and nx == '/': state = 'code'; i += 1
        i += 1
    raise SystemExit(f'closing brace not found: {marker}')

# V9.4.65: make the visible filter controls roughly half the height of the
# older 56dp layout while preserving every existing text/icon size and style.
replacement = r'''    private void normalizeTopFilterControls(){
        final int targetHeight=dp(30);
        final int verticalPad=0;
        final int horizontalPad=dp(6);
        final int drawableGap=dp(7);
        final int parentRoom=dp(34);
        final int[] ids={R.id.locationButton,R.id.distanceValue,R.id.payValue,R.id.categoryChip,R.id.sourceChip};
        for(int id:ids){
            android.view.View v=findViewById(id);
            if(v==null)continue;

            android.view.ViewGroup.LayoutParams lp=v.getLayoutParams();
            if(lp!=null){
                lp.height=targetHeight;
                if(lp instanceof android.view.ViewGroup.MarginLayoutParams){
                    android.view.ViewGroup.MarginLayoutParams mlp=(android.view.ViewGroup.MarginLayoutParams)lp;
                    mlp.topMargin=dp(1);
                    mlp.bottomMargin=dp(1);
                }
                v.setLayoutParams(lp);
            }
            v.setMinimumHeight(targetHeight);

            if(v instanceof android.widget.TextView){
                android.widget.TextView tv=(android.widget.TextView)v;
                // Do not change text size, number size, typeface, or drawable size.
                tv.setIncludeFontPadding(true);
                tv.setGravity(android.view.Gravity.CENTER);
                tv.setSingleLine(true);
                tv.setEllipsize(null);
                tv.setMinHeight(targetHeight);
                tv.setPadding(horizontalPad,verticalPad,horizontalPad,verticalPad);
                tv.setCompoundDrawablePadding(drawableGap);
            }

            android.view.ViewParent parent=v.getParent();
            if(parent instanceof android.view.ViewGroup){
                android.view.ViewGroup group=(android.view.ViewGroup)parent;
                group.setClipChildren(false);
                group.setClipToPadding(false);
                android.view.ViewGroup.LayoutParams parentLp=group.getLayoutParams();
                if(parentLp!=null && parentLp.height>0){
                    parentLp.height=parentRoom;
                    if(parentLp instanceof android.view.ViewGroup.MarginLayoutParams){
                        android.view.ViewGroup.MarginLayoutParams pmlp=(android.view.ViewGroup.MarginLayoutParams)parentLp;
                        pmlp.topMargin=dp(1);
                        pmlp.bottomMargin=dp(1);
                    }
                    group.setLayoutParams(parentLp);
                }
            }
        }
    }
'''
text = replace_method(text, 'private void normalizeTopFilterControls()', replacement)


def set_attr(src, view_id, attr, value):
    token=f'android:id="@+id/{view_id}"'
    pos=src.find(token)
    if pos < 0:
        return src, False
    start=src.rfind('<',0,pos)
    end=src.find('>',pos)
    if start < 0 or end < 0:
        return src, False
    tag=src[start:end+1]
    pat=re.compile(rf'android:{re.escape(attr)}="[^"]*"')
    rep=f'android:{attr}="{value}"'
    if pat.search(tag):
        tag=pat.sub(rep,tag,1)
    else:
        tag=tag[:-2]+' '+rep+tag[-2:] if tag.endswith('/>') else tag[:-1]+' '+rep+'>'
    return src[:start]+tag+src[end+1:], True

for view_id in ('locationButton','distanceValue','payValue','categoryChip','sourceChip'):
    for attr,value in (
        ('layout_height','30dp'),
        ('minHeight','30dp'),
        ('paddingTop','0dp'),
        ('paddingBottom','0dp'),
        ('paddingLeft','6dp'),
        ('paddingRight','6dp'),
        ('layout_marginTop','1dp'),
        ('layout_marginBottom','1dp'),
        ('gravity','center'),
    ):
        xml,ok=set_attr(xml,view_id,attr,value)
        if not ok:
            raise SystemExit(f'layout control not found: {view_id}')

main.write_text(text,encoding='utf-8')
layout.write_text(xml,encoding='utf-8')
version.write_text('9.4.65\n',encoding='utf-8')
print('Applied V9.4.65 half-height top filter containers with unchanged text/icon sizing')
