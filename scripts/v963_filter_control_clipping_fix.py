#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v963_filter_control_clipping_fix.py <project_dir>')

project = Path(sys.argv[1]).resolve()
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
layout = project / 'app/src/main/res/layout/activity_main.xml'
version = project / 'VERSION.txt'

text = main.read_text(encoding='utf-8')
xml = layout.read_text(encoding='utf-8')

# Add a runtime normalization pass so the four primary search/filter controls
# remain readable even when Android font/display scaling differs from the
# device used to design the original XML.
helper = r'''
    private void normalizeTopFilterControls(){
        final int targetHeight=dp(56);
        final int verticalPad=dp(6);
        final int horizontalPad=dp(12);
        final int drawableGap=dp(8);
        final int[] ids={R.id.locationButton,R.id.distanceValue,R.id.categoryChip,R.id.sourceChip};
        for(int id:ids){
            android.view.View v=findViewById(id);
            if(v==null)continue;

            android.view.ViewGroup.LayoutParams lp=v.getLayoutParams();
            if(lp!=null){
                lp.height=targetHeight;
                v.setLayoutParams(lp);
            }
            v.setMinimumHeight(targetHeight);

            if(v instanceof android.widget.TextView){
                android.widget.TextView tv=(android.widget.TextView)v;
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
                if(parentLp!=null && parentLp.height>0 && parentLp.height<dp(60)){
                    parentLp.height=dp(60);
                    group.setLayoutParams(parentLp);
                }
            }
        }
    }
'''

if 'private void normalizeTopFilterControls()' not in text:
    anchor='    private int dp(float v)'
    pos=text.find(anchor)
    if pos < 0:
        anchor='    private int dp(int v)'
        pos=text.find(anchor)
    if pos < 0:
        raise SystemExit('dp helper anchor not found')
    text=text[:pos]+helper+'\n'+text[pos:]

call='normalizeTopFilterControls();'
if call not in text:
    needle='setContentView(R.layout.activity_main);'
    if needle not in text:
        raise SystemExit('setContentView target not found')
    text=text.replace(needle, needle+'\n        '+call, 1)

# Keep the XML itself roomy too. The runtime helper above is the final safety
# net; these attributes prevent clipping during the first layout pass.
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

for view_id in ('locationButton','distanceValue','categoryChip','sourceChip'):
    for attr,value in (
        ('layout_height','56dp'),
        ('minHeight','56dp'),
        ('paddingTop','6dp'),
        ('paddingBottom','6dp'),
        ('paddingLeft','12dp'),
        ('paddingRight','12dp'),
        ('gravity','center'),
    ):
        xml,ok=set_attr(xml,view_id,attr,value)
        if not ok:
            raise SystemExit(f'layout control not found: {view_id}')

main.write_text(text,encoding='utf-8')
layout.write_text(xml,encoding='utf-8')
version.write_text('9.4.62\n',encoding='utf-8')
print('Applied V9.4.62 top search/filter sizing and clipping fix')
