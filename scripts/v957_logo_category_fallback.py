#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=2:
    raise SystemExit('usage: v957_logo_category_fallback.py <project_dir>')

root=Path(sys.argv[1])
java=root/'app/src/main/java/com/jobbubble/app/MainActivity.java'
version=root/'VERSION.txt'
s=java.read_text(encoding='utf-8')

old='''        Bitmap logo=getCompanyLogo(j.company);
        if(logo!=null){
            Path clip=new Path(); clip.addCircle(cx,cy,r-dp(5),Path.Direction.CW);
            c.save(); c.clipPath(clip);
            android.graphics.RectF dest=new android.graphics.RectF(cx-r+dp(5),cy-r+dp(5),cx+r-dp(5),cy+r-dp(5));
            c.drawBitmap(logo,null,dest,new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG)); c.restore();
        }else{
            String company=j.company==null?"":j.company.trim(); String initial=company.isEmpty()?"J":company.substring(0,1).toUpperCase(Locale.US);
            Paint ip=new Paint(Paint.ANTI_ALIAS_FLAG); ip.setTypeface(Typeface.DEFAULT_BOLD); ip.setTextSize(dp(18)); ip.setTextAlign(Paint.Align.CENTER); ip.setColor(Color.rgb(105,55,184));
            c.drawText(initial,cx,cy-(ip.ascent()+ip.descent())/2f,ip);
        }
'''

new='''        // Company artwork always has priority. Trigger/continue the asynchronous logo lookup
        // before reading the cache so a missing first-frame logo can upgrade itself as soon as
        // the real company artwork arrives.
        if(j.company!=null&&!j.company.trim().isEmpty())requestCompanyLogo(j.company);
        Bitmap logo=getCompanyLogo(j.company);
        if(logo!=null){
            Path clip=new Path(); clip.addCircle(cx,cy,r-dp(5),Path.Direction.CW);
            c.save(); c.clipPath(clip);
            android.graphics.RectF dest=new android.graphics.RectF(cx-r+dp(5),cy-r+dp(5),cx+r-dp(5),cy+r-dp(5));
            c.drawBitmap(logo,null,dest,new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG)); c.restore();
        }else{
            // No company logo yet/available: reuse the exact icon mapping shown in the Job
            // Category picker. Job.from() already refines each listing into one of these
            // categories from its title/provider category/description, so the fallback stays
            // relevant (truck -> Transportation, nurse -> Healthcare, security -> Shield, etc.).
            String categoryIcon=choiceIcon(j.category==null?"Other":j.category);
            if(categoryIcon==null||categoryIcon.trim().isEmpty()||"•".equals(categoryIcon))categoryIcon=choiceIcon("Other");
            Paint ip=new Paint(Paint.ANTI_ALIAS_FLAG);
            ip.setTypeface(Typeface.create(Typeface.DEFAULT,Typeface.BOLD));
            ip.setTextSize(dp(22));
            ip.setTextAlign(Paint.Align.CENTER);
            ip.setColor(Color.parseColor(categoryHex(j.category)));
            Paint.FontMetrics fm=ip.getFontMetrics();
            c.drawText(categoryIcon,cx,cy-(fm.ascent+fm.descent)/2f,ip);
        }
'''

if old not in s:
    raise SystemExit('compact marker company-logo fallback target not found')
s=s.replace(old,new,1)
java.write_text(s,encoding='utf-8')
version.write_text('9.4.56\n',encoding='utf-8')
print('Applied V9.4.56 company-logo-first category-icon fallback for job bubbles')
