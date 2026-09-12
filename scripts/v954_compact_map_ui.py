#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv)!=2:
    raise SystemExit('usage: v954_compact_map_ui.py <project_dir>')
root=Path(sys.argv[1])
java=root/'app/src/main/java/com/jobbubble/app/MainActivity.java'
layout=root/'app/src/main/res/layout/activity_main.xml'
version=root/'VERSION.txt'
s=java.read_text(encoding='utf-8')

def replace_method(src, marker, replacement):
    idx=src.find(marker)
    if idx<0: raise SystemExit(f'method target not found: {marker}')
    start=src.rfind('\n',0,idx)+1
    brace=src.find('{',idx)
    if brace<0: raise SystemExit(f'opening brace not found: {marker}')
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
                    end=i+1
                    return src[:start]+replacement+src[end:]
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

new_marker=r'''    private Bitmap makeJobMarkerBitmap(Job j){
        final boolean light=isLightUi();
        final int w=dp(176), h=dp(126);
        Bitmap out=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);
        Canvas c=new Canvas(out);
        Paint p=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);

        String title=j.title==null||j.title.trim().isEmpty()?"Job":j.title.trim();
        String pay=j.pay>0?("$"+Math.round(j.pay)+"/hr"):"";
        String approx=shouldShowApproxLocation(j)?"Approx.":"";

        // Compact title card: attached to the logo bubble, two lines max, no giant gray banner.
        RectF card=new RectF(dp(15),dp(4),w-dp(9),dp(pay.isEmpty()?61:68));
        p.setStyle(Paint.Style.FILL);
        p.setColor(light?Color.argb(244,250,250,252):Color.argb(242,17,29,43));
        p.setShadowLayer(dp(3),0,dp(1),Color.argb(55,0,0,0));
        c.drawRoundRect(card,dp(15),dp(15),p);
        p.clearShadowLayer();
        p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(dp(1));
        p.setColor(light?Color.rgb(202,205,213):Color.rgb(61,79,99));
        c.drawRoundRect(card,dp(15),dp(15),p);

        Paint text=new Paint(Paint.ANTI_ALIAS_FLAG);
        text.setTypeface(Typeface.create(Typeface.DEFAULT,Typeface.BOLD));
        text.setTextSize(dp(13));
        text.setColor(light?Color.rgb(36,39,46):Color.rgb(241,245,249));
        float maxText=w-dp(46);
        int first=text.breakText(title,true,maxText,null);
        if(first<title.length()){
            int sp=title.lastIndexOf(' ',Math.max(1,first-1));
            if(sp>4)first=sp;
        }
        String line1=title.substring(0,Math.min(first,title.length())).trim();
        String rest=title.substring(Math.min(first,title.length())).trim();
        String line2="";
        if(!rest.isEmpty()){
            int second=text.breakText(rest,true,maxText,null);
            line2=rest.substring(0,Math.min(second,rest.length())).trim();
            if(second<rest.length()){
                while(text.measureText(line2+"…")>maxText && line2.length()>1)line2=line2.substring(0,line2.length()-1).trim();
                line2+="…";
            }
        }
        float ty=dp(25);
        c.drawText(line1,dp(27),ty,text);
        if(!line2.isEmpty())c.drawText(line2,dp(27),ty+dp(17),text);

        if(!approx.isEmpty()){
            Paint ap=new Paint(Paint.ANTI_ALIAS_FLAG); ap.setTextSize(dp(9)); ap.setTypeface(Typeface.DEFAULT_BOLD);
            ap.setColor(Color.rgb(68,142,208)); c.drawText(approx,w-dp(49),dp(15),ap);
        }
        if(!pay.isEmpty()){
            Paint pp=new Paint(Paint.ANTI_ALIAS_FLAG); pp.setTextSize(dp(10)); pp.setTypeface(Typeface.DEFAULT_BOLD);
            pp.setColor(light?Color.rgb(20,137,105):Color.rgb(116,222,184));
            c.drawText(pay,dp(27),dp(60),pp);
        }

        // Logo bubble overlaps the card so the marker reads as one object.
        final float cx=dp(48), cy=dp(91), r=dp(27);
        p.setStyle(Paint.Style.FILL); p.setColor(light?Color.WHITE:Color.rgb(246,248,251));
        p.setShadowLayer(dp(3),0,dp(2),Color.argb(65,0,0,0)); c.drawCircle(cx,cy,r,p); p.clearShadowLayer();
        p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(dp(3)); p.setColor(Color.rgb(139,78,230)); c.drawCircle(cx,cy,r,p);
        Bitmap logo=getCompanyLogo(j.company);
        if(logo!=null){
            Path clip=new Path(); clip.addCircle(cx,cy,r-dp(5),Path.Direction.CW);
            c.save(); c.clipPath(clip);
            RectF dest=new RectF(cx-r+dp(5),cy-r+dp(5),cx+r-dp(5),cy+r-dp(5));
            c.drawBitmap(logo,null,dest,new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG)); c.restore();
        }else{
            String company=j.company==null?"":j.company.trim(); String initial=company.isEmpty()?"J":company.substring(0,1).toUpperCase(Locale.US);
            Paint ip=new Paint(Paint.ANTI_ALIAS_FLAG); ip.setTypeface(Typeface.DEFAULT_BOLD); ip.setTextSize(dp(18)); ip.setTextAlign(Paint.Align.CENTER); ip.setColor(Color.rgb(105,55,184));
            c.drawText(initial,cx,cy-(ip.ascent()+ip.descent())/2f,ip);
        }

        if(haveLocation){
            double mi=distanceMiles(userLat,userLon,j.lat,j.lon);
            String dist=mi<10?String.format(Locale.US,"%.1f mi",mi):String.format(Locale.US,"%.0f mi",mi);
            Paint dt=new Paint(Paint.ANTI_ALIAS_FLAG); dt.setTextSize(dp(10)); dt.setTypeface(Typeface.DEFAULT_BOLD);
            float tw=dt.measureText(dist); float left=w-dp(12)-tw-dp(18);
            RectF db=new RectF(left,dp(79),w-dp(10),dp(105));
            p.setStyle(Paint.Style.FILL); p.setColor(light?Color.argb(238,245,246,249):Color.argb(238,28,42,57)); c.drawRoundRect(db,dp(13),dp(13),p);
            p.setStyle(Paint.Style.STROKE); p.setStrokeWidth(dp(1)); p.setColor(light?Color.rgb(194,198,207):Color.rgb(73,94,115)); c.drawRoundRect(db,dp(13),dp(13),p);
            dt.setColor(light?Color.rgb(70,75,84):Color.rgb(225,233,240)); c.drawText(dist,left+dp(9),dp(96),dt);
        }
        return out;
    }
'''
s=replace_method(s,'makeJobMarkerBitmap(Job j)',new_marker)

# Anchor the new composite marker on the center of the logo bubble.
s=s.replace('float markerAnchorY=shouldShowApproxLocation(j)?0.734f:0.705f;','float markerAnchorY=0.722f;')
s=s.replace('.anchor(0.293f,markerAnchorY)','.anchor(0.273f,markerAnchorY)')
# Give the map more breathing room around the overlays.
s=s.replace('googleMap.setPadding(0,dp(126),0,dp(96));','googleMap.setPadding(0,dp(108),0,dp(78));')
java.write_text(s,encoding='utf-8')

# Tighten the visible chrome without changing behavior.
x=layout.read_text(encoding='utf-8')
def set_attr(xml, vid, attr, value):
    token=f'android:id="@+id/{vid}"'; pos=xml.find(token)
    if pos<0: return xml,False
    a=xml.rfind('<',0,pos); b=xml.find('>',pos)
    if a<0 or b<0: return xml,False
    tag=xml[a:b+1]
    pat=re.compile(rf'android:{re.escape(attr)}="[^"]*"')
    rep=f'android:{attr}="{value}"'
    if pat.search(tag): tag=pat.sub(rep,tag,1)
    else: tag=tag[:-2]+' '+rep+tag[-2:] if tag.endswith('/>') else tag[:-1]+' '+rep+'>'
    return xml[:a]+tag+xml[b+1:],True

for vid in ['locationButton','distanceValue','payValue','categoryChip','sourceChip']:
    x,_=set_attr(x,vid,'layout_height','48dp')
for vid in ['searchButton','refreshButton']:
    x,_=set_attr(x,vid,'layout_width','48dp'); x,_=set_attr(x,vid,'layout_height','48dp')
for vid in ['navMap','navList','navSaved','navProfile']:
    x,_=set_attr(x,vid,'layout_height','58dp')
for vid,val in [('logoTitle','27sp'),('logoSubtitle','11sp')]:
    x,_=set_attr(x,vid,'textSize',val)
for vid in ['bottomNav','bottomBar','navContainer','navigationBar']:
    x,_=set_attr(x,vid,'layout_height','72dp')
layout.write_text(x,encoding='utf-8')
version.write_text('9.4.54\n',encoding='utf-8')
print('Applied JobBubble V9.4.54 compact marker and map chrome cleanup')
