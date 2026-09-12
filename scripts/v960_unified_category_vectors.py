#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=2:
    raise SystemExit('usage: v960_unified_category_vectors.py <project_dir>')

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

# The category picker and job bubbles now share one geometry renderer. This removes
# platform emoji from the category menu and guarantees a consistent, density-aware
# outline icon at every Android display density.
helpers=r'''    private String categoryIconFamily(String item){
        if(item==null)return "other";
        String x=item.trim().toLowerCase(Locale.US);
        if(x.equals("all jobs"))return "all";
        if(x.contains("retail")||x.contains("sales"))return "retail";
        if(x.contains("warehouse")||x.contains("logistics")||x.contains("fulfillment"))return "warehouse";
        if(x.contains("food")||x.contains("hospitality")||x.contains("restaurant"))return "food";
        if(x.contains("construction")||x.contains("skilled trade")||x.contains("maintenance"))return "construction";
        if(x.contains("office")||x.contains("administration"))return "office";
        if(x.contains("customer service")||x.contains("customer support"))return "customer";
        if(x.contains("health")||x.contains("medical")||x.contains("nurs"))return "healthcare";
        if(x.contains("transport")||x.contains("delivery")||x.contains("driver")||x.contains("truck"))return "transportation";
        if(x.contains("security")||x.contains("public safety")||x.contains("police")||x.contains("guard"))return "security";
        if(x.contains("technology")||x.contains("engineering")||x.contains("software")||x.contains("computer"))return "technology";
        if(x.contains("government"))return "government";
        if(x.contains("education"))return "education";
        if(x.contains("finance")||x.contains("accounting"))return "finance";
        if(x.contains("manufacturing")||x.contains("production"))return "manufacturing";
        if(x.contains("cleaning")||x.contains("facilities"))return "cleaning";
        if(x.contains("community")||x.contains("social service"))return "community";
        return "other";
    }

    private Bitmap categoryIconBitmap(String item,int sizeDp,int color){
        int px=Math.max(dp(24),dp(sizeDp));
        Bitmap out=Bitmap.createBitmap(px,px,Bitmap.Config.ARGB_8888);
        Canvas canvas=new Canvas(out);
        float u=px/38f;
        drawUnifiedCategoryIcon(canvas,categoryIconFamily(item),px/2f,px/2f,u,color);
        return out;
    }

    private void drawUnifiedCategoryIcon(Canvas c,String family,float cx,float cy,float u,int color){
        if(family==null||family.trim().isEmpty())family="other";
        Paint q=new Paint(Paint.ANTI_ALIAS_FLAG);
        q.setColor(color);
        q.setStyle(Paint.Style.STROKE);
        q.setStrokeWidth(2.6f*u);
        q.setStrokeCap(Paint.Cap.ROUND);
        q.setStrokeJoin(Paint.Join.ROUND);

        if("all".equals(family)){
            float a=11*u,b=3*u,r=1.5f*u;
            c.drawRoundRect(new android.graphics.RectF(cx-a,cy-a,cx-b,cy-b),r,r,q);
            c.drawRoundRect(new android.graphics.RectF(cx+b,cy-a,cx+a,cy-b),r,r,q);
            c.drawRoundRect(new android.graphics.RectF(cx-a,cy+b,cx-b,cy+a),r,r,q);
            c.drawRoundRect(new android.graphics.RectF(cx+b,cy+b,cx+a,cy+a),r,r,q);
            return;
        }
        if("transportation".equals(family)){
            c.drawRoundRect(new android.graphics.RectF(cx-14*u,cy-7*u,cx+3*u,cy+6*u),2*u,2*u,q);
            Path cab=new Path(); cab.moveTo(cx+3*u,cy-5*u); cab.lineTo(cx+9*u,cy-5*u); cab.lineTo(cx+14*u,cy); cab.lineTo(cx+14*u,cy+6*u); cab.lineTo(cx+3*u,cy+6*u); c.drawPath(cab,q);
            c.drawCircle(cx-8*u,cy+8*u,3*u,q); c.drawCircle(cx+9*u,cy+8*u,3*u,q); return;
        }
        if("security".equals(family)){
            Path sh=new Path(); sh.moveTo(cx,cy-15*u); sh.lineTo(cx+12*u,cy-10*u); sh.lineTo(cx+10*u,cy+4*u); sh.quadTo(cx+7*u,cy+11*u,cx,cy+15*u); sh.quadTo(cx-7*u,cy+11*u,cx-10*u,cy+4*u); sh.lineTo(cx-12*u,cy-10*u); sh.close(); c.drawPath(sh,q); return;
        }
        if("healthcare".equals(family)){
            q.setStrokeWidth(4.3f*u); c.drawLine(cx-10*u,cy,cx+10*u,cy,q); c.drawLine(cx,cy-10*u,cx,cy+10*u,q); return;
        }
        if("technology".equals(family)){
            c.drawRoundRect(new android.graphics.RectF(cx-14*u,cy-11*u,cx+14*u,cy+7*u),2*u,2*u,q); c.drawLine(cx,cy+7*u,cx,cy+13*u,q); c.drawLine(cx-7*u,cy+13*u,cx+7*u,cy+13*u,q); return;
        }
        if("warehouse".equals(family)){
            android.graphics.RectF box=new android.graphics.RectF(cx-13*u,cy-12*u,cx+13*u,cy+13*u); c.drawRect(box,q); c.drawLine(cx-13*u,cy-12*u,cx,cy-4*u,q); c.drawLine(cx+13*u,cy-12*u,cx,cy-4*u,q); c.drawLine(cx,cy-4*u,cx,cy+13*u,q); return;
        }
        if("construction".equals(family)){
            q.setStrokeWidth(3.2f*u); c.drawLine(cx-10*u,cy+13*u,cx+6*u,cy-8*u,q);
            Path hammer=new Path(); hammer.moveTo(cx-1*u,cy-13*u); hammer.lineTo(cx+12*u,cy-4*u); hammer.lineTo(cx+8*u,cy+1*u); hammer.lineTo(cx-5*u,cy-8*u); c.drawPath(hammer,q); return;
        }
        if("food".equals(family)){
            q.setStrokeWidth(2.2f*u); c.drawLine(cx-9*u,cy-13*u,cx-9*u,cy+13*u,q); c.drawLine(cx-14*u,cy-13*u,cx-14*u,cy-3*u,q); c.drawLine(cx-4*u,cy-13*u,cx-4*u,cy-3*u,q); c.drawLine(cx-14*u,cy-3*u,cx-4*u,cy-3*u,q); c.drawLine(cx+9*u,cy-13*u,cx+9*u,cy+13*u,q); c.drawArc(new android.graphics.RectF(cx+3*u,cy-13*u,cx+15*u,cy-1*u),180,180,false,q); return;
        }
        if("retail".equals(family)){
            c.drawRoundRect(new android.graphics.RectF(cx-12*u,cy-5*u,cx+12*u,cy+14*u),2*u,2*u,q); c.drawArc(new android.graphics.RectF(cx-7*u,cy-13*u,cx+7*u,cy+2*u),180,180,false,q); return;
        }
        if("office".equals(family)){
            c.drawRoundRect(new android.graphics.RectF(cx-14*u,cy-7*u,cx+14*u,cy+12*u),2*u,2*u,q); c.drawRoundRect(new android.graphics.RectF(cx-6*u,cy-13*u,cx+6*u,cy-6*u),2*u,2*u,q); c.drawLine(cx-14*u,cy+1*u,cx+14*u,cy+1*u,q); return;
        }
        if("customer".equals(family)){
            c.drawArc(new android.graphics.RectF(cx-12*u,cy-13*u,cx+12*u,cy+11*u),190,160,false,q); c.drawLine(cx-13*u,cy-1*u,cx-13*u,cy+8*u,q); c.drawLine(cx+13*u,cy-1*u,cx+13*u,cy+8*u,q); c.drawLine(cx+13*u,cy+8*u,cx+7*u,cy+11*u,q); return;
        }
        if("government".equals(family)){
            Path roof=new Path(); roof.moveTo(cx-14*u,cy-7*u); roof.lineTo(cx,cy-15*u); roof.lineTo(cx+14*u,cy-7*u); roof.close(); c.drawPath(roof,q); c.drawLine(cx-12*u,cy+13*u,cx+12*u,cy+13*u,q); for(int off=-8;off<=8;off+=8)c.drawLine(cx+off*u,cy-5*u,cx+off*u,cy+10*u,q); return;
        }
        if("education".equals(family)){
            Path book=new Path(); book.moveTo(cx,cy-9*u); book.quadTo(cx-7*u,cy-13*u,cx-14*u,cy-9*u); book.lineTo(cx-14*u,cy+11*u); book.quadTo(cx-7*u,cy+7*u,cx,cy+11*u); book.quadTo(cx+7*u,cy+7*u,cx+14*u,cy+11*u); book.lineTo(cx+14*u,cy-9*u); book.quadTo(cx+7*u,cy-13*u,cx,cy-9*u); book.close(); c.drawPath(book,q); c.drawLine(cx,cy-9*u,cx,cy+11*u,q); return;
        }
        if("finance".equals(family)){
            c.drawRoundRect(new android.graphics.RectF(cx-12*u,cy-14*u,cx+12*u,cy+14*u),2*u,2*u,q);
            c.drawRect(new android.graphics.RectF(cx-7*u,cy-9*u,cx+7*u,cy-4*u),q);
            for(int yy=2;yy<=9;yy+=7)for(int xx=-6;xx<=6;xx+=6)c.drawCircle(cx+xx*u,cy+yy*u,1.5f*u,q);
            return;
        }
        if("manufacturing".equals(family)){
            Path f=new Path(); f.moveTo(cx-14*u,cy+13*u); f.lineTo(cx-14*u,cy-3*u); f.lineTo(cx-6*u,cy+1*u); f.lineTo(cx,cy-4*u); f.lineTo(cx+7*u,cy); f.lineTo(cx+7*u,cy-12*u); f.lineTo(cx+13*u,cy-12*u); f.lineTo(cx+13*u,cy+13*u); f.close(); c.drawPath(f,q); return;
        }
        if("cleaning".equals(family)){
            q.setStrokeWidth(2.8f*u); c.drawLine(cx,cy-14*u,cx,cy+14*u,q); c.drawLine(cx-14*u,cy,cx+14*u,cy,q); c.drawLine(cx-8*u,cy-8*u,cx+8*u,cy+8*u,q); c.drawLine(cx+8*u,cy-8*u,cx-8*u,cy+8*u,q); return;
        }
        if("community".equals(family)){
            c.drawCircle(cx-7*u,cy-7*u,4*u,q); c.drawCircle(cx+7*u,cy-7*u,4*u,q); c.drawArc(new android.graphics.RectF(cx-15*u,cy-1*u,cx+1*u,cy+15*u),195,150,false,q); c.drawArc(new android.graphics.RectF(cx-1*u,cy-1*u,cx+15*u,cy+15*u),195,150,false,q); return;
        }

        // Other: simple ellipsis inside a circle, using the same stroke language as the set.
        c.drawCircle(cx,cy,13*u,q); q.setStyle(Paint.Style.FILL); c.drawCircle(cx-6*u,cy,1.7f*u,q); c.drawCircle(cx,cy,1.7f*u,q); c.drawCircle(cx+6*u,cy,1.7f*u,q);
    }

'''

choice_marker='    private String choiceIcon(String item){'
if choice_marker not in s:
    raise SystemExit('choiceIcon insertion point not found')
s=s.replace(choice_marker,helpers+choice_marker,1)

# Source picker can keep compact text marks; category rows no longer use text/emoji glyphs.
new_choice='''    private String choiceIcon(String item){
        if(item==null)return "";
        String x=item.trim().toLowerCase(Locale.US);
        if(x.equals("all sources"))return "▦";
        if(x.equals("adzuna"))return "A";
        if(x.equals("usajobs"))return "US";
        if(x.equals("the muse")||x.equals("muse"))return "TM";
        return "";
    }
'''
s=replace_method(s,'private String choiceIcon(String item)',new_choice)

# Job bubbles use exactly the same vector geometry as the picker. Company logos still
# win before this method is called; this only handles the logo-missing fallback.
new_bubble='''    private void drawCategoryBubbleIcon(Canvas c,Job j,float cx,float cy){
        String family=bubbleIconFamily(j);
        drawUnifiedCategoryIcon(c,family,cx,cy,getResources().getDisplayMetrics().density,Color.parseColor("#7B3FC1"));
    }
'''
s=replace_method(s,'private void drawCategoryBubbleIcon(Canvas c,Job j,float cx,float cy)',new_bubble)

old_menu='''            String ci=choiceIcon(item);
            if(!"•".equals(ci)){
                TextView icon=new TextView(this); icon.setText(ci); icon.setTextColor(violet); icon.setTextSize(20); icon.setGravity(Gravity.CENTER);
                row.addView(icon,new LinearLayout.LayoutParams(dp(38),dp(38)));
            } else {
                TextView spacer=new TextView(this); spacer.setText(""); row.addView(spacer,new LinearLayout.LayoutParams(dp(10),dp(1)));
            }
'''
new_menu='''            if(title.equals("Job category")){
                android.widget.ImageView icon=new android.widget.ImageView(this);
                icon.setScaleType(android.widget.ImageView.ScaleType.CENTER);
                icon.setImageBitmap(categoryIconBitmap(item,38,violet));
                icon.setContentDescription(item+" category icon");
                row.addView(icon,new LinearLayout.LayoutParams(dp(38),dp(38)));
            }else{
                String ci=choiceIcon(item);
                if(ci!=null&&!ci.trim().isEmpty()){
                    TextView icon=new TextView(this); icon.setText(ci); icon.setTextColor(violet); icon.setTextSize(18); icon.setTypeface(Typeface.DEFAULT,Typeface.BOLD); icon.setGravity(Gravity.CENTER);
                    row.addView(icon,new LinearLayout.LayoutParams(dp(38),dp(38)));
                }else{
                    TextView spacer=new TextView(this); spacer.setText(""); row.addView(spacer,new LinearLayout.LayoutParams(dp(10),dp(1)));
                }
            }
'''
if old_menu not in s:
    raise SystemExit('showChoiceMenu icon block not found')
s=s.replace(old_menu,new_menu,1)

# Ensure the old emoji category art cannot leak back into the generated app.
for bad in ('🚚','🛡','💻','🛠','🍴','🛍','📦','💼'):
    if bad in s:
        raise SystemExit('legacy category emoji still present: '+bad)

java.write_text(s,encoding='utf-8')
version.write_text('9.4.59\n',encoding='utf-8')
print('Applied V9.4.59 unified clean vector category icon system')
