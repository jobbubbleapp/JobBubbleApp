#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v961_group_company_logos.py <project_dir>')

project = Path(sys.argv[1]).resolve()
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = project / 'VERSION.txt'
text = main.read_text(encoding='utf-8')

old = '''        // Three overlapping discs make the marker read as a physical pile rather than a generic pin.
        float cy=dp(72),r=dp(18);
        int show=Math.min(3,pile.size());
        for(int k=show-1;k>=0;k--){
            Job j=filtered.get(pile.get(k));
            float cx=dp(48+k*25);
            android.graphics.Paint disk=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            disk.setColor(Color.parseColor(companyColor(j.company,j.category)));
            c.drawCircle(cx,cy,r,disk);
            android.graphics.Paint rim=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            rim.setStyle(android.graphics.Paint.Style.STROKE);rim.setStrokeWidth(dp(2));rim.setColor(Color.parseColor("#D5DADF"));
            c.drawCircle(cx,cy,r-dp(1),rim);
            android.graphics.Paint white=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);white.setColor(Color.WHITE);
            c.drawCircle(cx,cy,dp(13),white);
            android.graphics.Paint badge=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            badge.setTextAlign(android.graphics.Paint.Align.CENTER);badge.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);badge.setTextSize(dp(8));
            badge.setColor(Color.parseColor(companyColor(j.company,j.category)));
            String b=companyBadge(j.company).replace("\\n"," ");if(b.length()>3)b=b.substring(0,3);
            android.graphics.Paint.FontMetrics fm=badge.getFontMetrics();c.drawText(b,cx,cy-(fm.ascent+fm.descent)/2f,badge);
        }
'''

new = '''        // Grouped markers use the same company-logo-first artwork as individual job bubbles.
        // Logo requests are asynchronous; requestCompanyLogo schedules a map rerender when ready.
        float cy=dp(72),r=dp(18);
        int show=Math.min(3,pile.size());
        for(int k=show-1;k>=0;k--){
            Job j=filtered.get(pile.get(k));
            float cx=dp(48+k*25);
            if(j.company!=null&&!j.company.trim().isEmpty())requestCompanyLogo(j.company);
            Bitmap logo=getCompanyLogo(j.company);

            android.graphics.Paint disk=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            disk.setColor(Color.parseColor(companyColor(j.company,j.category)));
            c.drawCircle(cx,cy,r,disk);
            android.graphics.Paint rim=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            rim.setStyle(android.graphics.Paint.Style.STROKE);rim.setStrokeWidth(dp(2));rim.setColor(Color.parseColor("#D5DADF"));
            c.drawCircle(cx,cy,r-dp(1),rim);
            android.graphics.Paint white=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);white.setColor(Color.WHITE);
            c.drawCircle(cx,cy,dp(13),white);

            if(isUsableCompanyLogo(logo)){
                Path clip=new Path();clip.addCircle(cx,cy,dp(12),Path.Direction.CW);
                c.save();c.clipPath(clip);
                android.graphics.RectF dest=new android.graphics.RectF(cx-dp(12),cy-dp(12),cx+dp(12),cy+dp(12));
                c.drawBitmap(logo,null,dest,new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG));
                c.restore();
            }else{
                drawUnifiedCategoryIcon(c,bubbleIconFamily(j),cx,cy,getResources().getDisplayMetrics().density*0.72f,Color.parseColor("#7B3FC1"));
            }
        }
'''

if old not in text:
    raise SystemExit('grouped job badge block not found')
text = text.replace(old, new, 1)
main.write_text(text, encoding='utf-8')
version.write_text('9.4.60\n', encoding='utf-8')
print('Applied V9.4.60 company-logo-first grouped job markers')
