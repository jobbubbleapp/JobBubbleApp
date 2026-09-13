from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
java = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
gradle = root / 'app/build.gradle'
version = root / 'VERSION.txt'

s = java.read_text(encoding='utf-8')

# Add ATS and the three direct ATS provider filters everywhere the main source picker is built.
s = s.replace(
    'final String[] src={"All sources","Adzuna","USAJOBS","The Muse"};',
    'final String[] src={"All sources","Adzuna","USAJOBS","The Muse","ATS","Greenhouse","Lever","Ashby"};'
)

# Source icons in the modern source chooser.
s = s.replace(
    '        if(item.equals("The Muse")) return "TM";\n        return "•";',
    '        if(item.equals("The Muse")) return "TM";\n'
    '        if(item.equals("ATS")) return "ATS";\n'
    '        if(item.equals("Greenhouse")) return "GH";\n'
    '        if(item.equals("Lever")) return "L";\n'
    '        if(item.equals("Ashby")) return "AS";\n'
    '        return "•";'
)

# Preserve ATS selections from local/cloud settings and also normalize raw backend names.
s = s.replace(
    '        if(value.equalsIgnoreCase("The Muse")||value.equalsIgnoreCase("Muse"))return "The Muse";\n'
    '        if(value.equalsIgnoreCase("CareerOneStop")||value.equalsIgnoreCase("CareerOneStop/NLx"))return "All sources";',
    '        if(value.equalsIgnoreCase("The Muse")||value.equalsIgnoreCase("Muse"))return "The Muse";\n'
    '        if(value.equalsIgnoreCase("ATS"))return "ATS";\n'
    '        if(value.equalsIgnoreCase("Greenhouse")||value.equalsIgnoreCase("ATS/Greenhouse"))return "Greenhouse";\n'
    '        if(value.equalsIgnoreCase("Lever")||value.equalsIgnoreCase("ATS/Lever"))return "Lever";\n'
    '        if(value.equalsIgnoreCase("Ashby")||value.equalsIgnoreCase("ATS/Ashby"))return "Ashby";\n'
    '        if(value.equalsIgnoreCase("CareerOneStop")||value.equalsIgnoreCase("CareerOneStop/NLx"))return "All sources";'
)

# Send the provider-specific source parameter to the backend when selected.
s = s.replace(
    '        if("The Muse".equalsIgnoreCase(source))return "themuse";\n        return "all";',
    '        if("The Muse".equalsIgnoreCase(source))return "themuse";\n'
    '        if("ATS".equalsIgnoreCase(source))return "ats";\n'
    '        if("Greenhouse".equalsIgnoreCase(source))return "greenhouse";\n'
    '        if("Lever".equalsIgnoreCase(source))return "lever";\n'
    '        if("Ashby".equalsIgnoreCase(source))return "ashby";\n'
    '        return "all";'
)

# Backend ATS jobs keep source names like ATS/Greenhouse. Match those correctly in local filtering.
old_filter = 'boolean ok=d<=maxDistanceMiles&&(j.pay<=0||j.pay>=minPay)&&(source.equals("All sources")||j.source.equalsIgnoreCase(source))&&(category.equals("All jobs")||j.category.equalsIgnoreCase(category))&&(!preciseLocationsOnly||hasPreciseLocation(j));'
new_filter = 'boolean ok=d<=maxDistanceMiles&&(j.pay<=0||j.pay>=minPay)&&jobMatchesSelectedSource(j)&&(category.equals("All jobs")||j.category.equalsIgnoreCase(category))&&(!preciseLocationsOnly||hasPreciseLocation(j));'
if old_filter not in s:
    raise SystemExit('Source filter target not found')
s = s.replace(old_filter, new_filter, 1)

apply_marker = '    private void applyFilters(){\n'
if apply_marker not in s:
    raise SystemExit('applyFilters marker not found')
match_helper = '''    private boolean jobMatchesSelectedSource(Job j){
        if("All sources".equalsIgnoreCase(source))return true;
        String js=j==null||j.source==null?"":j.source.trim();
        if("ATS".equalsIgnoreCase(source))return js.equalsIgnoreCase("ATS")||js.toLowerCase(Locale.US).startsWith("ats/");
        if("Greenhouse".equalsIgnoreCase(source))return js.equalsIgnoreCase("Greenhouse")||js.equalsIgnoreCase("ATS/Greenhouse");
        if("Lever".equalsIgnoreCase(source))return js.equalsIgnoreCase("Lever")||js.equalsIgnoreCase("ATS/Lever");
        if("Ashby".equalsIgnoreCase(source))return js.equalsIgnoreCase("Ashby")||js.equalsIgnoreCase("ATS/Ashby");
        return js.equalsIgnoreCase(source);
    }

'''
s = s.replace(apply_marker, match_helper + apply_marker, 1)

# Keep the source/data information accurate without making Help & Support verbose.
adzuna_card = '        box.addView(infoCard("Adzuna","Job listing search provider used as one of JobBubble\'s live job sources."),gap2);\n'
if adzuna_card in s and 'Greenhouse, Lever & Ashby' not in s:
    s = s.replace(
        adzuna_card,
        adzuna_card +
        '        LinearLayout.LayoutParams gap3=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); gap3.topMargin=dp(8);\n'
        '        box.addView(infoCard("Greenhouse, Lever & Ashby","Direct employer ATS feeds used for current employer-posted jobs."),gap3);\n',
        1
    )

# Replace the old job-sources/help block with the new source list, simple help menu,
# bug report form, app info, privacy, and secure backend submission.
start = s.find('    private void showJobSourcesMenu(){\n')
end = s.find('    private void showSettings(){\n', start)
if start < 0 or end < 0:
    raise SystemExit('Could not locate source/help methods')

methods = r'''    private void showJobSourcesMenu(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        ScrollView outer=new ScrollView(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(16),dp(22),dp(32)); box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));
        outer.addView(box);
        box.addView(label("Job Sources",24,light?"#22252B":"#F4F8FC",true));
        TextView sub=label("Choose a source for the map.",13,light?"#646B74":"#8FA7BA",false); sub.setPadding(0,dp(5),0,dp(14)); box.addView(sub);
        final String[] choices={"All sources","Adzuna","USAJOBS","The Muse","ATS","Greenhouse","Lever","Ashby"};
        for(String choice:choices){
            String detail;
            if(choice.equals("All sources"))detail="Every enabled source";
            else if(choice.equals("ATS"))detail="All direct employer ATS feeds";
            else if(choice.equals("Greenhouse")||choice.equals("Lever")||choice.equals("Ashby"))detail="Direct employer jobs";
            else detail=choice.equals("USAJOBS")?"Federal jobs":choice.equals("The Muse")?"The Muse jobs":"Adzuna jobs";
            Button b=settingsMenuButton((choice.equals(source)?"✓  ":"     ")+choice+"  —  "+detail,false);
            LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(58)); p.bottomMargin=dp(8); box.addView(b,p);
            b.setOnClickListener(v->{source=choice;if(sourceChip!=null)sourceChip.setText(choice);saveLocalSettings();saveCloudState();dlg.dismiss();loadJobs();});
        }
        dlg.setContentView(outer); dlg.show();
    }

    private void showHelpSupport(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(16),dp(22),dp(32)); box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));
        box.addView(label("Help & Support",24,light?"#22252B":"#F4F8FC",true));
        TextView sub=label("Support and app information.",13,light?"#646B74":"#8FA7BA",false); sub.setPadding(0,dp(5),0,dp(14)); box.addView(sub);

        Button report=settingsMenuButton("Report a bug",false); box.addView(report,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(54)));
        report.setOnClickListener(v->{dlg.dismiss();showBugReport();});
        Button appInfo=settingsMenuButton("App information",false); LinearLayout.LayoutParams a=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(54)); a.topMargin=dp(8); box.addView(appInfo,a);
        appInfo.setOnClickListener(v->{dlg.dismiss();showAppInformation();});
        Button privacy=settingsMenuButton("Privacy",false); LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(54)); p.topMargin=dp(8); box.addView(privacy,p);
        privacy.setOnClickListener(v->{dlg.dismiss();showPrivacyInformation();});

        Button done=settingsMenuButton("Done",false); done.setGravity(Gravity.CENTER); LinearLayout.LayoutParams d=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); d.topMargin=dp(14); box.addView(done,d); done.setOnClickListener(v->dlg.dismiss());
        dlg.setContentView(box); dlg.show();
    }

    private void showAppInformation(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(16),dp(22),dp(30)); box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));
        box.addView(label("App information",24,light?"#22252B":"#F4F8FC",true));
        TextView version=infoCard("JobBubble","Version 9.4.47"); LinearLayout.LayoutParams vp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); vp.topMargin=dp(14); box.addView(version,vp);
        LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); sp.topMargin=dp(8); box.addView(infoCard("Live job sources","Adzuna, USAJOBS, The Muse, Greenhouse, Lever and Ashby."),sp);
        Button done=settingsMenuButton("Done",false); done.setGravity(Gravity.CENTER); LinearLayout.LayoutParams dpv=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); dpv.topMargin=dp(14); box.addView(done,dpv); done.setOnClickListener(v->dlg.dismiss());
        dlg.setContentView(box); dlg.show();
    }

    private void showPrivacyInformation(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(16),dp(22),dp(30)); box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));
        box.addView(label("Privacy",24,light?"#22252B":"#F4F8FC",true));
        TextView text=label("Bug reports send the description you enter plus the JobBubble version, Android version, device model and the report screen. Passwords and GitHub credentials are never included in the app report.",14,light?"#3D434B":"#DCE8F2",false);
        text.setPadding(0,dp(12),0,dp(10)); box.addView(text);
        TextView sync=label("Account sign-in and profile sync use Firebase.",13,light?"#646B74":"#8FA7BA",false); box.addView(sync);
        Button done=settingsMenuButton("Done",false); done.setGravity(Gravity.CENTER); LinearLayout.LayoutParams dpv=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); dpv.topMargin=dp(16); box.addView(done,dpv); done.setOnClickListener(v->dlg.dismiss());
        dlg.setContentView(box); dlg.show();
    }

    private void showBugReport(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(16),dp(22),dp(30)); box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));
        box.addView(label("Report a bug",24,light?"#22252B":"#F4F8FC",true));
        TextView sub=label("Describe what went wrong.",13,light?"#646B74":"#8FA7BA",false); sub.setPadding(0,dp(5),0,dp(12)); box.addView(sub);

        EditText description=new EditText(this);
        description.setHint("What happened? Include what you were doing when the problem occurred.");
        description.setHintTextColor(Color.parseColor(light?"#7A8088":"#7893A6"));
        description.setTextColor(Color.parseColor(light?"#22252B":"#F4F8FC"));
        description.setTextSize(15); description.setGravity(Gravity.TOP|Gravity.START); description.setMinLines(6); description.setMaxLines(12);
        description.setPadding(dp(14),dp(12),dp(14),dp(12));
        description.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE|InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        description.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(5000)});
        description.setBackground(roundStrokeBg(light?"#F3F4F6":"#10283A",light?"#BFC3CA":"#31546C",14,1));
        box.addView(description,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(180)));

        TextView deviceNote=label("App and device details are attached automatically.",12,light?"#6B7280":"#8FA7BA",false); deviceNote.setPadding(0,dp(9),0,dp(12)); box.addView(deviceNote);

        LinearLayout actions=new LinearLayout(this); actions.setOrientation(LinearLayout.HORIZONTAL);
        Button cancel=settingsMenuButton("Cancel",false); cancel.setGravity(Gravity.CENTER); LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(0,dp(52),1); cp.rightMargin=dp(7); actions.addView(cancel,cp);
        Button submit=new Button(this); submit.setText("Submit Report"); submit.setAllCaps(false); submit.setTypeface(Typeface.DEFAULT,Typeface.BOLD); submit.setTextColor(Color.WHITE); submit.setBackground(roundBg("#7C3AED",14)); LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(0,dp(52),1); sp.leftMargin=dp(7); actions.addView(submit,sp); box.addView(actions);
        cancel.setOnClickListener(v->dlg.dismiss());
        submit.setOnClickListener(v->{
            String text=description.getText().toString().trim();
            if(text.length()<5){Toast.makeText(this,"Please describe the bug before submitting.",Toast.LENGTH_SHORT).show();return;}
            submitBugReport(text,submit,dlg);
        });

        dlg.setContentView(box); dlg.show(); description.requestFocus();
    }

    private String bugReportUrl(){
        String jobs=jobApiUrl();
        int q=jobs.indexOf('?'); if(q>=0)jobs=jobs.substring(0,q);
        while(jobs.endsWith("/"))jobs=jobs.substring(0,jobs.length()-1);
        if(jobs.endsWith("/jobs"))return jobs.substring(0,jobs.length()-5)+"/report-bug";
        return jobs+"/report-bug";
    }

    private void submitBugReport(String description,Button submit,BottomSheetDialog dlg){
        submit.setEnabled(false); submit.setText("Submitting…");
        jobExecutor.execute(()->{
            String message=null; int issueNumber=0;
            HttpURLConnection c=null;
            try{
                JSONObject payload=new JSONObject();
                payload.put("description",description);
                payload.put("app_version","9.4.47");
                payload.put("android_version",String.valueOf(Build.VERSION.RELEASE)+" (API "+Build.VERSION.SDK_INT+")");
                payload.put("device_model",(Build.MANUFACTURER+" "+Build.MODEL).trim());
                payload.put("screen","Help & Support > Report a bug");
                byte[] body=payload.toString().getBytes("UTF-8");
                c=(HttpURLConnection)new URL(bugReportUrl()).openConnection();
                c.setRequestMethod("POST"); c.setConnectTimeout(12000); c.setReadTimeout(15000); c.setDoOutput(true);
                c.setRequestProperty("Content-Type","application/json; charset=utf-8"); c.setRequestProperty("Accept","application/json");
                c.setFixedLengthStreamingMode(body.length);
                try(OutputStream out=c.getOutputStream()){out.write(body);}
                int code=c.getResponseCode(); InputStream in=code>=200&&code<300?c.getInputStream():c.getErrorStream();
                String response=in==null?"":read(in); JSONObject result=response.isEmpty()?new JSONObject():new JSONObject(response);
                if(code>=200&&code<300){issueNumber=result.optInt("issue_number",0);}
                else message=result.optString("error","Unable to submit the bug report right now.");
            }catch(Exception e){message="Unable to submit the bug report right now.";}
            finally{if(c!=null)c.disconnect();}
            final String error=message; final int number=issueNumber;
            runOnUiThread(()->{
                submit.setEnabled(true); submit.setText("Submit Report");
                if(error==null){
                    dlg.dismiss();
                    Toast.makeText(this,number>0?"Bug report submitted • Issue #"+number:"Bug report submitted",Toast.LENGTH_LONG).show();
                }else Toast.makeText(this,error,Toast.LENGTH_LONG).show();
            });
        });
    }

'''
s = s[:start] + methods + s[end:]

# Make the Settings version label accurate too.
s = s.replace('TextView version=label("v9.0",12,', 'TextView version=label("v9.4.47",12,')

java.write_text(s, encoding='utf-8')

# Keep Android package metadata aligned with the visible/app-reported version.
if gradle.exists():
    g = gradle.read_text(encoding='utf-8')
    g = re.sub(r'versionCode\s+\d+', 'versionCode 81', g, count=1)
    g = re.sub(r"versionName\s+['\"][^'\"]+['\"]", "versionName '9.4.47'", g, count=1)
    gradle.write_text(g, encoding='utf-8')

if version.exists():
    version.write_text('9.4.47\n', encoding='utf-8')

# Guardrails: fail the build patch loudly if any required feature was not installed.
checks = [
    '"ATS","Greenhouse","Lever","Ashby"',
    'return "greenhouse";',
    'jobMatchesSelectedSource(Job j)',
    'private void showBugReport()',
    'private void submitBugReport(',
    'Help & Support > Report a bug',
    'Version 9.4.47'
]
for check in checks:
    if check not in s:
        raise SystemExit(f'Missing V9.4.47 app feature: {check}')

print('Applied JobBubble V9.4.47 ATS source/help/bug-report patch')
