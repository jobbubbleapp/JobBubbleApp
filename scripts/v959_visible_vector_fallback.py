#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=2:
    raise SystemExit('usage: v959_visible_vector_fallback.py <project_dir>')

root=Path(sys.argv[1])
java=root/'app/src/main/java/com/jobbubble/app/MainActivity.java'
version=root/'VERSION.txt'
s=java.read_text(encoding='utf-8')

marker='    private Bitmap makeJobMarkerBitmap(Job j){'
if marker not in s:
    raise SystemExit('makeJobMarkerBitmap target not found')

helpers=r'''    // A downloaded bitmap is not automatically a usable logo. Some lookup failures return
    // transparent/white placeholder images; accepting those is what caused apparently empty
    // job bubbles. Sample the bitmap and require visible, non-white artwork before using it.
    private boolean isUsableCompanyLogo(Bitmap b){
        if(b==null||b.isRecycled()||b.getWidth()<4||b.getHeight()<4)return false;
        int visible=0, meaningful=0;
        int minR=255,minG=255,minB=255,maxR=0,maxG=0,maxB=0;
        final int grid=12;
        for(int gy=0;gy<grid;gy++){
            int y=Math.min(b.getHeight()-1,(int)(((gy+0.5f)*b.getHeight())/grid));
            for(int gx=0;gx<grid;gx++){
                int x=Math.min(b.getWidth()-1,(int)(((gx+0.5f)*b.getWidth())/grid));
                int px=b.getPixel(x,y), a=Color.alpha(px);
                if(a<48)continue;
                int r=Color.red(px), g=Color.green(px), bl=Color.blue(px);
                visible++;
                minR=Math.min(minR,r); minG=Math.min(minG,g); minB=Math.min(minB,bl);
                maxR=Math.max(maxR,r); maxG=Math.max(maxG,g); maxB=Math.max(maxB,bl);
                // Near-white pixels disappear into the white marker center and do not count as artwork.
                if(!(r>242&&g>242&&bl>242))meaningful++;
            }
        }
        if(visible<4||meaningful<2)return false;
        int spread=Math.max(maxR-minR,Math.max(maxG-minG,maxB-minB));
        // A tiny accidental speck on an otherwise blank image is still a failed logo.
        return meaningful>=Math.max(2,visible/20)||spread>=28;
    }

    // Resolve the icon from the job itself, not only the provider's category string. This means
    // listings such as "Youth Housing Support Staff" still get a useful Community/Social icon
    // even when the provider categorizes them as Other.
    private String bubbleIconFamily(Job j){
        String category=j==null||j.category==null?"":j.category;
        String title=j==null||j.title==null?"":j.title;
        String x=(category+" "+title).toLowerCase(Locale.US);
        if(x.contains("truck")||x.contains("driver")||x.contains("transport")||x.contains("delivery")||x.contains("courier")||x.contains("cdl"))return "transportation";
        if(x.contains("security")||x.contains("guard")||x.contains("police")||x.contains("public safety")||x.contains("correction"))return "security";
        if(x.contains("nurs")||x.contains("medical")||x.contains("health")||x.contains("physician")||x.contains("doctor")||x.contains("clinic")||x.contains("caregiver")||x.contains("dental")||x.contains("pharmacy"))return "healthcare";
        if(x.contains("software")||x.contains("developer")||x.contains("programmer")||x.contains("technology")||x.contains("computer")||x.contains("cyber")||x.contains("data engineer")||x.contains("it support")||x.contains("network engineer"))return "technology";
        if(x.contains("warehouse")||x.contains("logistics")||x.contains("fulfillment")||x.contains("material handler")||x.contains("forklift")||x.contains("inventory"))return "warehouse";
        if(x.contains("construction")||x.contains("carpenter")||x.contains("electrician")||x.contains("plumber")||x.contains("mechanic")||x.contains("maintenance")||x.contains("skilled trade")||x.contains("operating engineer"))return "construction";
        if(x.contains("restaurant")||x.contains("server")||x.contains("cook")||x.contains("chef")||x.contains("food")||x.contains("hospitality")||x.contains("barista")||x.contains("dishwasher"))return "food";
        if(x.contains("retail")||x.contains("cashier")||x.contains("store associate")||x.contains("sales associate")||x.contains("merchandiser"))return "retail";
        if(x.contains("teacher")||x.contains("school")||x.contains("education")||x.contains("instructor")||x.contains("tutor"))return "education";
        if(x.contains("account")||x.contains("finance")||x.contains("bank")||x.contains("financial")||x.contains("bookkeep"))return "finance";
        if(x.contains("customer service")||x.contains("call center")||x.contains("customer support"))return "customer";
        if(x.contains("housing")||x.contains("youth")||x.contains("social service")||x.contains("social worker")||x.contains("community")||x.contains("case manager")||x.contains("counsel")||x.contains("outreach")||x.contains("human service")||x.contains("nonprofit"))return "community";
        if(x.contains("government")||x.contains("federal")||x.contains("state agency")||x.contains("city of ")||x.contains("county"))return "government";
        if(x.contains("manufactur")||x.contains("production")||x.contains("machine operator")||x.contains("assembler"))return "manufacturing";
        if(x.contains("clean")||x.contains("janitor")||x.contains("custodian")||x.contains("facilities"))return "cleaning";
        if(x.contains("office")||x.contains("administr")||x.contains("reception")||x.contains("clerical")||x.contains("assistant"))return "office";
        return "other";
    }

    // Draw category artwork directly on the marker canvas instead of relying on emoji-font
    // glyphs. Canvas text rendering can silently omit emoji on some Android builds; these vector
    // shapes are always available, so a job bubble can no longer have an empty center.
    private void drawCategoryBubbleIcon(Canvas c,Job j,float cx,float cy){
        String family=bubbleIconFamily(j);
        Paint q=new Paint(Paint.ANTI_ALIAS_FLAG);
        q.setColor(Color.parseColor(categoryHex(j==null?null:j.category)));
        q.setStyle(Paint.Style.STROKE);
        q.setStrokeWidth(dp(3));
        q.setStrokeCap(Paint.Cap.ROUND);
        q.setStrokeJoin(Paint.Join.ROUND);

        if("transportation".equals(family)){
            c.drawRoundRect(new android.graphics.RectF(cx-dp(14),cy-dp(7),cx+dp(3),cy+dp(6)),dp(2),dp(2),q);
            Path cab=new Path(); cab.moveTo(cx+dp(3),cy-dp(5)); cab.lineTo(cx+dp(9),cy-dp(5)); cab.lineTo(cx+dp(14),cy); cab.lineTo(cx+dp(14),cy+dp(6)); cab.lineTo(cx+dp(3),cy+dp(6)); c.drawPath(cab,q);
            c.drawCircle(cx-dp(8),cy+dp(8),dp(3),q); c.drawCircle(cx+dp(9),cy+dp(8),dp(3),q);
            return;
        }
        if("security".equals(family)){
            Path sh=new Path(); sh.moveTo(cx,cy-dp(15)); sh.lineTo(cx+dp(12),cy-dp(10)); sh.lineTo(cx+dp(10),cy+dp(4)); sh.quadTo(cx+dp(7),cy+dp(11),cx,cy+dp(15)); sh.quadTo(cx-dp(7),cy+dp(11),cx-dp(10),cy+dp(4)); sh.lineTo(cx-dp(12),cy-dp(10)); sh.close(); c.drawPath(sh,q); return;
        }
        if("healthcare".equals(family)){
            q.setStrokeWidth(dp(5)); c.drawLine(cx-dp(11),cy,cx+dp(11),cy,q); c.drawLine(cx,cy-dp(11),cx,cy+dp(11),q); return;
        }
        if("technology".equals(family)){
            c.drawRoundRect(new android.graphics.RectF(cx-dp(14),cy-dp(11),cx+dp(14),cy+dp(7)),dp(2),dp(2),q); c.drawLine(cx,cy+dp(7),cx,cy+dp(13),q); c.drawLine(cx-dp(7),cy+dp(13),cx+dp(7),cy+dp(13),q); return;
        }
        if("warehouse".equals(family)){
            android.graphics.RectF box=new android.graphics.RectF(cx-dp(13),cy-dp(12),cx+dp(13),cy+dp(13)); c.drawRect(box,q); c.drawLine(cx-dp(13),cy-dp(12),cx,cy-dp(4),q); c.drawLine(cx+dp(13),cy-dp(12),cx,cy-dp(4),q); c.drawLine(cx,cy-dp(4),cx,cy+dp(13),q); return;
        }
        if("construction".equals(family)){
            q.setStrokeWidth(dp(4)); c.drawLine(cx-dp(9),cy+dp(13),cx+dp(7),cy-dp(8),q); c.drawLine(cx+dp(1),cy-dp(12),cx+dp(13),cy-dp(3),q); c.drawLine(cx-dp(12),cy-dp(8),cx-dp(4),cy, q); return;
        }
        if("food".equals(family)){
            q.setStrokeWidth(dp(2)); c.drawLine(cx-dp(9),cy-dp(13),cx-dp(9),cy+dp(13),q); c.drawLine(cx-dp(14),cy-dp(13),cx-dp(14),cy-dp(3),q); c.drawLine(cx-dp(4),cy-dp(13),cx-dp(4),cy-dp(3),q); c.drawLine(cx-dp(14),cy-dp(3),cx-dp(4),cy-dp(3),q); c.drawLine(cx+dp(9),cy-dp(13),cx+dp(9),cy+dp(13),q); c.drawArc(new android.graphics.RectF(cx+dp(3),cy-dp(13),cx+dp(15),cy-dp(1)),180,180,false,q); return;
        }
        if("retail".equals(family)){
            c.drawRoundRect(new android.graphics.RectF(cx-dp(12),cy-dp(5),cx+dp(12),cy+dp(14)),dp(2),dp(2),q); c.drawArc(new android.graphics.RectF(cx-dp(7),cy-dp(13),cx+dp(7),cy+dp(2)),180,180,false,q); return;
        }
        if("community".equals(family)){
            c.drawCircle(cx-dp(7),cy-dp(7),dp(4),q); c.drawCircle(cx+dp(7),cy-dp(7),dp(4),q); c.drawArc(new android.graphics.RectF(cx-dp(15),cy-dp(1),cx+dp(1),cy+dp(15)),195,150,false,q); c.drawArc(new android.graphics.RectF(cx-dp(1),cy-dp(1),cx+dp(15),cy+dp(15)),195,150,false,q); return;
        }
        if("education".equals(family)){
            Path book=new Path(); book.moveTo(cx,cy-dp(9)); book.quadTo(cx-dp(7),cy-dp(13),cx-dp(14),cy-dp(9)); book.lineTo(cx-dp(14),cy+dp(11)); book.quadTo(cx-dp(7),cy+dp(7),cx,cy+dp(11)); book.quadTo(cx+dp(7),cy+dp(7),cx+dp(14),cy+dp(11)); book.lineTo(cx+dp(14),cy-dp(9)); book.quadTo(cx+dp(7),cy-dp(13),cx,cy-dp(9)); book.close(); c.drawPath(book,q); c.drawLine(cx,cy-dp(9),cx,cy+dp(11),q); return;
        }
        if("finance".equals(family)){
            q.setStyle(Paint.Style.FILL); q.setTypeface(Typeface.create(Typeface.DEFAULT,Typeface.BOLD)); q.setTextAlign(Paint.Align.CENTER); q.setTextSize(dp(27)); Paint.FontMetrics fm=q.getFontMetrics(); c.drawText("$",cx,cy-(fm.ascent+fm.descent)/2f,q); return;
        }
        if("customer".equals(family)){
            c.drawArc(new android.graphics.RectF(cx-dp(12),cy-dp(13),cx+dp(12),cy+dp(11)),190,160,false,q); c.drawLine(cx-dp(13),cy-dp(1),cx-dp(13),cy+dp(8),q); c.drawLine(cx+dp(13),cy-dp(1),cx+dp(13),cy+dp(8),q); c.drawLine(cx+dp(13),cy+dp(8),cx+dp(7),cy+dp(11),q); return;
        }
        if("government".equals(family)){
            Path roof=new Path(); roof.moveTo(cx-dp(14),cy-dp(7)); roof.lineTo(cx,cy-dp(15)); roof.lineTo(cx+dp(14),cy-dp(7)); roof.close(); c.drawPath(roof,q); c.drawLine(cx-dp(11),cy+dp(12),cx+dp(11),cy+dp(12),q); for(int off=-8;off<=8;off+=8)c.drawLine(cx+dp(off),cy-dp(5),cx+dp(off),cy+dp(10),q); return;
        }
        if("manufacturing".equals(family)){
            Path f=new Path(); f.moveTo(cx-dp(14),cy+dp(13)); f.lineTo(cx-dp(14),cy-dp(3)); f.lineTo(cx-dp(6),cy+dp(1)); f.lineTo(cx,cy-dp(4)); f.lineTo(cx+dp(7),cy); f.lineTo(cx+dp(7),cy-dp(12)); f.lineTo(cx+dp(13),cy-dp(12)); f.lineTo(cx+dp(13),cy+dp(13)); f.close(); c.drawPath(f,q); return;
        }
        if("cleaning".equals(family)){
            q.setStrokeWidth(dp(3)); c.drawLine(cx,cy-dp(14),cx,cy+dp(14),q); c.drawLine(cx-dp(14),cy,cx+dp(14),cy,q); c.drawLine(cx-dp(9),cy-dp(9),cx+dp(9),cy+dp(9),q); c.drawLine(cx+dp(9),cy-dp(9),cx-dp(9),cy+dp(9),q); return;
        }

        // Office/Other: a universally recognizable briefcase, guaranteeing a visible default.
        c.drawRoundRect(new android.graphics.RectF(cx-dp(14),cy-dp(7),cx+dp(14),cy+dp(12)),dp(2),dp(2),q); c.drawRoundRect(new android.graphics.RectF(cx-dp(6),cy-dp(13),cx+dp(6),cy-dp(6)),dp(2),dp(2),q); c.drawLine(cx-dp(14),cy+dp(1),cx+dp(14),cy+dp(1),q);
    }

'''

s=s.replace(marker,helpers+marker,1)

start=s.find('        Bitmap logo=getCompanyLogo(j.company);',s.find(marker))
end=s.find('\n\n        if(haveLocation){',start)
if start<0 or end<0:
    raise SystemExit('job marker logo/fallback block not found')
new_block=r'''        Bitmap logo=getCompanyLogo(j.company);
        if(isUsableCompanyLogo(logo)){
            Path clip=new Path(); clip.addCircle(cx,cy,r-dp(5),Path.Direction.CW);
            c.save(); c.clipPath(clip);
            android.graphics.RectF dest=new android.graphics.RectF(cx-r+dp(5),cy-r+dp(5),cx+r-dp(5),cy+r-dp(5));
            c.drawBitmap(logo,null,dest,new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG)); c.restore();
        }else{
            drawCategoryBubbleIcon(c,j,cx,cy);
        }'''
s=s[:start]+new_block+s[end:]

# Guard against accidentally retaining the emoji text fallback inside the map marker.
marker_body=s[s.find(marker):s.find('        return out;',s.find(marker))]
if 'c.drawText(categoryIcon' in marker_body:
    raise SystemExit('old emoji marker fallback still present')
if 'drawCategoryBubbleIcon(c,j,cx,cy);' not in marker_body:
    raise SystemExit('vector marker fallback was not installed')

java.write_text(s,encoding='utf-8')
version.write_text('9.4.58\n',encoding='utf-8')
print('Applied V9.4.58 blank-logo rejection and always-visible vector job bubble icons')
