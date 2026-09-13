#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v966_legal_help_no_company_logos.py <project_dir>')

project = Path(sys.argv[1]).resolve()
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = project / 'VERSION.txt'
s = main.read_text(encoding='utf-8')


def replace_method(src, marker, replacement):
    idx = src.find(marker)
    if idx < 0:
        raise SystemExit(f'method target not found: {marker}')
    start = src.rfind('\n', 0, idx) + 1
    brace = src.find('{', idx)
    if brace < 0:
        raise SystemExit(f'opening brace not found: {marker}')
    depth = 0
    i = brace
    state = 'code'
    while i < len(src):
        ch = src[i]
        nx = src[i + 1] if i + 1 < len(src) else ''
        if state == 'code':
            if ch == '"':
                state = 'string'
            elif ch == "'":
                state = 'char'
            elif ch == '/' and nx == '/':
                state = 'line'; i += 1
            elif ch == '/' and nx == '*':
                state = 'block'; i += 1
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return src[:start] + replacement + src[i + 1:]
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


def balanced_end(src, brace):
    depth = 0
    i = brace
    state = 'code'
    while i < len(src):
        ch = src[i]
        nx = src[i + 1] if i + 1 < len(src) else ''
        if state == 'code':
            if ch == '"': state = 'string'
            elif ch == "'": state = 'char'
            elif ch == '/' and nx == '/': state = 'line'; i += 1
            elif ch == '/' and nx == '*': state = 'block'; i += 1
            elif ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0: return i + 1
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
    raise SystemExit('unclosed block')

# ---------------------------------------------------------------------------
# Help & Support: keep the existing JobBubble settings visual language and add
# the public pages Google Play reviewers/users need to be able to reach.
# ---------------------------------------------------------------------------
help_marker = '    private void showHelpSupport(){'
if help_marker not in s:
    raise SystemExit('Help & Support method not found')

if 'private void openJobBubbleWebPage(String url)' not in s:
    web_helper = r'''    private void openJobBubbleWebPage(String url){
        try{
            Intent intent=new Intent(Intent.ACTION_VIEW,android.net.Uri.parse(url));
            startActivity(intent);
        }catch(Exception e){
            Toast.makeText(this,"Unable to open this page",Toast.LENGTH_SHORT).show();
        }
    }

'''
    s = s.replace(help_marker, web_helper + help_marker, 1)

new_help = r'''    private void showHelpSupport(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        ScrollView scroll=new ScrollView(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(16),dp(22),dp(32)); box.setBackground(roundBg(light?"#ECEDEF":"#071C2C",28));
        scroll.addView(box);
        box.addView(label("Help & Support",24,light?"#22252B":"#F4F8FC",true));
        TextView sub=label("Quick help, privacy information, support, and account controls.",13,light?"#646B74":"#8FA7BA",false); sub.setPadding(0,dp(5),0,dp(14)); box.addView(sub);

        box.addView(infoCard("No jobs showing","Try All sources, increase distance, lower the pay filter, or use Reset. Some providers may temporarily be unavailable."));
        LinearLayout.LayoutParams g1=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); g1.topMargin=dp(8); box.addView(infoCard("Job location looks approximate","JobBubble shows the best available area when an exact worksite address is unavailable, then refines it when better information is found."),g1);
        LinearLayout.LayoutParams g2=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); g2.topMargin=dp(8); box.addView(infoCard("Profile matching","Add degrees, licenses and certifications in your profile. Matching requirements appear green; missing requirements appear red."),g2);

        TextView legal=label("Privacy & Support",16,light?"#25282E":"#DCE8F2",true); legal.setPadding(0,dp(20),0,dp(8)); box.addView(legal);

        Button privacy=settingsMenuButton("Privacy Policy",false);
        box.addView(privacy,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)));
        privacy.setOnClickListener(v->openJobBubbleWebPage("https://jobbubble-support.onrender.com/privacy.html"));

        Button support=settingsMenuButton("Support",false);
        LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); sp.topMargin=dp(8); box.addView(support,sp);
        support.setOnClickListener(v->openJobBubbleWebPage("https://jobbubble-support.onrender.com/support.html"));

        Button deleteAccount=settingsMenuButton("Delete Account & Data",true);
        LinearLayout.LayoutParams dap=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); dap.topMargin=dp(8); box.addView(deleteAccount,dap);
        deleteAccount.setOnClickListener(v->openJobBubbleWebPage("https://jobbubble-support.onrender.com/delete-account.html"));

        TextView supportEmail=label("Support email: jobbubbleapp@gmail.com",12,light?"#6B7280":"#8FA7BA",false); supportEmail.setPadding(dp(4),dp(12),dp(4),0); box.addView(supportEmail);

        Button done=settingsMenuButton("Done",false); done.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); p.topMargin=dp(14); box.addView(done,p); done.setOnClickListener(v->dlg.dismiss());
        dlg.setContentView(scroll); dlg.show();
    }
'''
s = replace_method(s, 'private void showHelpSupport()', new_help)

# ---------------------------------------------------------------------------
# Company logos are deliberately disabled everywhere JobBubble renders map job
# artwork. Only JobBubble-owned job/category icons are displayed from now on.
# Company names remain ordinary listing text.
# ---------------------------------------------------------------------------
job_marker = s.find('private Bitmap makeJobMarkerBitmap(Job j)')
if job_marker < 0:
    raise SystemExit('makeJobMarkerBitmap not found')
logo_start = s.find('        Bitmap logo=getCompanyLogo(j.company);', job_marker)
location_start = s.find('\n\n        if(haveLocation){', logo_start)
if logo_start < 0 or location_start < 0:
    raise SystemExit('individual company-logo render block not found')
s = s[:logo_start] + '''        // JobBubble-owned category artwork only; employer logos are never rendered.\n        drawCategoryBubbleIcon(c,j,cx,cy);''' + s[location_start:]

# Replace the company-logo-first grouped marker loop added in V9.4.60.
group_comment = '        // Grouped markers use the same company-logo-first artwork as individual job bubbles.'
group_start = s.find(group_comment)
if group_start < 0:
    raise SystemExit('grouped company-logo marker block not found')
loop_start = s.find('        for(int k=show-1;k>=0;k--){', group_start)
if loop_start < 0:
    raise SystemExit('grouped marker loop not found')
loop_brace = s.find('{', loop_start)
loop_end = balanced_end(s, loop_brace)
new_group = r'''        // Grouped markers also use JobBubble-owned category artwork only.
        float cy=dp(72),r=dp(18);
        int show=Math.min(3,pile.size());
        for(int k=show-1;k>=0;k--){
            Job j=filtered.get(pile.get(k));
            float cx=dp(48+k*25);
            android.graphics.Paint disk=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            disk.setColor(Color.parseColor(companyColor(j.company,j.category)));
            c.drawCircle(cx,cy,r,disk);
            android.graphics.Paint rim=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            rim.setStyle(android.graphics.Paint.Style.STROKE); rim.setStrokeWidth(dp(2)); rim.setColor(Color.parseColor("#D5DADF"));
            c.drawCircle(cx,cy,r-dp(1),rim);
            android.graphics.Paint white=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG); white.setColor(Color.WHITE);
            c.drawCircle(cx,cy,dp(13),white);
            drawUnifiedCategoryIcon(c,bubbleIconFamily(j),cx,cy,getResources().getDisplayMetrics().density*0.72f,Color.parseColor("#7B3FC1"));
        }'''
s = s[:group_start] + new_group + s[loop_end:]

# Safety guards: helper functions can remain as dead compatibility code, but no
# runtime code may request or read employer logos after this patch.
active_request = [line.strip() for line in s.splitlines() if 'requestCompanyLogo(' in line and 'void requestCompanyLogo(' not in line]
active_get = [line.strip() for line in s.splitlines() if 'getCompanyLogo(' in line and 'Bitmap getCompanyLogo(' not in line]
if active_request:
    raise SystemExit('active company-logo request remains: ' + ' | '.join(active_request[:5]))
if active_get:
    raise SystemExit('active company-logo read remains: ' + ' | '.join(active_get[:5]))

required = [
    'Privacy Policy',
    'Support',
    'Delete Account & Data',
    'https://jobbubble-support.onrender.com/privacy.html',
    'https://jobbubble-support.onrender.com/support.html',
    'https://jobbubble-support.onrender.com/delete-account.html',
    'drawCategoryBubbleIcon(c,j,cx,cy);',
    'drawUnifiedCategoryIcon(c,bubbleIconFamily(j),cx,cy',
]
for token in required:
    if token not in s:
        raise SystemExit('required V9.4.66 token missing: ' + token)

main.write_text(s, encoding='utf-8')
version.write_text('9.4.66\n', encoding='utf-8')
print('Applied V9.4.66 Help/Privacy/Delete links and category-only job artwork')
