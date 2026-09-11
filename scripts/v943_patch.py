from pathlib import Path
import sys

root = Path(sys.argv[1])
java = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
layout = root / 'app/src/main/res/layout/activity_main.xml'
version = root / 'VERSION.txt'

s = java.read_text(encoding='utf-8')

# CareerOneStop source support from V9.4.42.
s = s.replace('final String[] src={"All sources","Adzuna","USAJOBS"};', 'final String[] src={"All sources","Adzuna","USAJOBS","CareerOneStop"};')
s = s.replace('if(item.equals("USAJOBS")) return "US";', 'if(item.equals("USAJOBS")) return "US";\n        if(item.equals("CareerOneStop")) return "CS";')
s = s.replace('if(value.equalsIgnoreCase("USAJOBS"))return "USAJOBS";', 'if(value.equalsIgnoreCase("USAJOBS"))return "USAJOBS";\n        if(value.equalsIgnoreCase("CareerOneStop")||value.equalsIgnoreCase("CareerOneStop/NLx"))return "CareerOneStop";')
s = s.replace('if("USAJOBS".equalsIgnoreCase(source))return "usajobs";', 'if("USAJOBS".equalsIgnoreCase(source))return "usajobs";\n        if("CareerOneStop".equalsIgnoreCase(source))return "careeronestop";')

# V9.4.43 map: restore the normal Google world-map appearance. Keep camera constraints only.
s = s.replace('        installForeignCountryCurtains();\n        if(moveCamera){', '        removeForeignCountryCurtains();\n        if(moveCamera){')
s = s.replace('            if("dark".equals(mapTheme)) googleMap.setMapStyle(MapStyleOptions.loadRawResourceStyle(this,R.raw.google_map_dark_style));\n            else googleMap.setMapStyle(MapStyleOptions.loadRawResourceStyle(this,R.raw.google_map_light_style));\n            installForeignCountryCurtains();', '            // Keep the map itself on Google Maps default styling. UI theme still applies to JobBubble controls.\n            googleMap.setMapStyle(null);\n            removeForeignCountryCurtains();')

old_bounds = '''            }else{\n                googleMap.setMinZoomPreference(4.1f);\n                googleMap.setLatLngBoundsForCameraTarget(new LatLngBounds(\n                    new LatLng(23.5,-126.0),new LatLng(50.5,-65.0)));\n            }'''
new_bounds = '''            }else{\n                googleMap.setMinZoomPreference(3.35f);\n                // Default Google map, but camera targets remain in the United States region.\n                // The bounds leave a little visual context at the edges without allowing world-wide panning.\n                googleMap.setLatLngBoundsForCameraTarget(new LatLngBounds(\n                    new LatLng(18.0,-130.0),new LatLng(52.5,-62.0)));\n            }'''
s = s.replace(old_bounds, new_bounds)

needle = '    private void installForeignCountryCurtains(){\n'
if 'private void removeForeignCountryCurtains()' not in s and needle in s:
    helper = '''    private void removeForeignCountryCurtains(){\n        if(foreignCountryTileOverlay!=null){\n            try{foreignCountryTileOverlay.remove();}catch(Exception ignored){}\n            foreignCountryTileOverlay=null;\n        }\n        for(Marker m:foreignCountryLabels)try{m.remove();}catch(Exception ignored){}\n        foreignCountryLabels.clear();\n        foreignTileCache.clear();\n    }\n\n'''
    s = s.replace(needle, helper + needle, 1)

insert_before = '    private void showSettings(){\n'
if 'private Button settingsMenuButton(' not in s and insert_before in s:
    methods = r'''    private Button settingsMenuButton(String text, boolean danger){
        final boolean light=isLightUi();
        Button b=new Button(this);
        b.setText(text); b.setAllCaps(false); b.setGravity(Gravity.START|Gravity.CENTER_VERTICAL);
        b.setPadding(dp(18),0,dp(18),0); b.setTextSize(15); b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        b.setTextColor(danger?Color.parseColor(light?"#9A374A":"#FF9F9F"):Color.parseColor(light?"#22252B":"#F4F8FC"));
        b.setBackground(roundStrokeBg(danger?(light?"#F2E4E7":"#281A23"):(light?"#E2E4E8":"#10283A"),danger?(light?"#D7AEB7":"#5B3442"):(light?"#C3C7CD":"#31546C"),14,1));
        return b;
    }

    private TextView infoCard(String title,String body){
        final boolean light=isLightUi();
        TextView v=label(title+"\n"+body,14,light?"#2B3037":"#E8F1F8",false);
        SpannableString sp=new SpannableString(v.getText());
        sp.setSpan(new android.text.style.StyleSpan(Typeface.BOLD),0,title.length(),Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        v.setText(sp); v.setPadding(dp(14),dp(12),dp(14),dp(12));
        v.setBackground(roundStrokeBg(light?"#E2E4E8":"#10283A",light?"#C3C7CD":"#31546C",14,1));
        return v;
    }

    private void showLicensesAndSources(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        ScrollView scroll=new ScrollView(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(16),dp(22),dp(34)); box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));
        scroll.addView(box);
        TextView title=label("Licenses & Data Sources",24,light?"#22252B":"#F4F8FC",true); box.addView(title);
        TextView intro=label("See your saved licenses and certifications, plus the services JobBubble uses to find and place job listings.",13,light?"#646B74":"#8FA7BA",false); intro.setPadding(0,dp(5),0,dp(16)); box.addView(intro);

        TextView your=label("Your Licenses & Certifications",16,light?"#25282E":"#DCE8F2",true); box.addView(your);
        String certText=profileCertifications().trim();
        TextView certs=infoCard(certText.isEmpty()?"No licenses or certifications saved":"Saved credentials",certText.isEmpty()?"Add them from Edit profile to improve requirement matching.":certText);
        LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); cp.topMargin=dp(8); box.addView(certs,cp);

        Button edit=settingsMenuButton("Edit licenses & certifications",false); LinearLayout.LayoutParams ep=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); ep.topMargin=dp(8); box.addView(edit,ep); edit.setOnClickListener(v->{dlg.dismiss();showEditProfile();});

        TextView data=label("Job Data Sources",16,light?"#25282E":"#DCE8F2",true); data.setPadding(0,dp(20),0,dp(8)); box.addView(data);
        box.addView(infoCard("CareerOneStop / NLx","U.S. Department of Labor job-search data. CareerOneStop attribution is shown here instead of covering the map."));
        LinearLayout.LayoutParams gap=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); gap.topMargin=dp(8);
        box.addView(infoCard("USAJOBS","Official U.S. federal government job listings."),gap);
        LinearLayout.LayoutParams gap2=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); gap2.topMargin=dp(8);
        box.addView(infoCard("Adzuna","Job listing search provider used as one of JobBubble's live job sources."),gap2);
        TextView map=label("Map data: Google Maps. Location refinement: Geoapify. Authentication/profile sync: Firebase.",12,light?"#6B7280":"#8FA7BA",false); map.setPadding(0,dp(14),0,dp(10)); box.addView(map);

        Button done=settingsMenuButton("Done",false); done.setGravity(Gravity.CENTER); LinearLayout.LayoutParams dpv=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); dpv.topMargin=dp(10); box.addView(done,dpv); done.setOnClickListener(v->dlg.dismiss());
        dlg.setContentView(scroll); dlg.show();
    }

    private void showJobSourcesMenu(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(16),dp(22),dp(32)); box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));
        box.addView(label("Job Sources",24,light?"#22252B":"#F4F8FC",true));
        TextView sub=label("Choose which live source the map should use. You can always return to All sources.",13,light?"#646B74":"#8FA7BA",false); sub.setPadding(0,dp(5),0,dp(14)); box.addView(sub);
        final String[] choices={"All sources","Adzuna","USAJOBS","CareerOneStop"};
        for(String choice:choices){
            String detail=choice.equals("All sources")?"Combine every enabled source":choice.equals("Adzuna")?"General job listings":choice.equals("USAJOBS")?"Federal government jobs":"CareerOneStop / NLx listings";
            Button b=settingsMenuButton((choice.equals(source)?"✓  ":"     ")+choice+"  —  "+detail,false);
            LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(58)); p.bottomMargin=dp(8); box.addView(b,p);
            b.setOnClickListener(v->{source=choice;if(sourceChip!=null)sourceChip.setText(choice);saveLocalSettings();saveCloudState();dlg.dismiss();loadJobs();});
        }
        dlg.setContentView(box); dlg.show();
    }

    private void showHelpSupport(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(16),dp(22),dp(32)); box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));
        box.addView(label("Help & Support",24,light?"#22252B":"#F4F8FC",true));
        TextView sub=label("Quick help for the most common JobBubble questions.",13,light?"#646B74":"#8FA7BA",false); sub.setPadding(0,dp(5),0,dp(14)); box.addView(sub);
        box.addView(infoCard("No jobs showing","Try All sources, increase distance, lower the pay filter, or use Reset. Some providers may temporarily be unavailable."));
        LinearLayout.LayoutParams g1=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); g1.topMargin=dp(8); box.addView(infoCard("Job location looks approximate","JobBubble shows the best available area when an exact worksite address is unavailable, then refines it when better information is found."),g1);
        LinearLayout.LayoutParams g2=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); g2.topMargin=dp(8); box.addView(infoCard("Profile matching","Add degrees, licenses and certifications in your profile. Matching requirements appear green; missing requirements appear red."),g2);
        LinearLayout.LayoutParams g3=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); g3.topMargin=dp(8); box.addView(infoCard("Privacy & account","Signing out removes the active Firebase session on this device. Saved local profile data is kept unless you edit or clear it."),g3);
        Button done=settingsMenuButton("Done",false); done.setGravity(Gravity.CENTER); LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); p.topMargin=dp(12); box.addView(done,p); done.setOnClickListener(v->dlg.dismiss());
        dlg.setContentView(box); dlg.show();
    }

'''
    s = s.replace(insert_before, methods + insert_before, 1)

s = s.replace('TextView regionSub=label("Show one U.S. map at a time. Foreign countries stay outside the usable map.",13,lightUi?"#646B74":"#8FA7BA",false);', 'TextView regionSub=label("The normal Google map stays visible, while panning is limited to the selected U.S. region.",13,lightUi?"#646B74":"#8FA7BA",false);')
s = s.replace('TextView section=label("Map appearance",16,lightUi?"#25282E":"#DCE8F2",true);', 'TextView section=label("App appearance",16,lightUi?"#25282E":"#DCE8F2",true);')
s = s.replace('TextView mapSub=label("Choose the map style. The rest of the app follows it.",13,lightUi?"#646B74":"#8FA7BA",false);', 'TextView mapSub=label("Choose the JobBubble interface theme. The map itself keeps the normal Google Maps appearance.",13,lightUi?"#646B74":"#8FA7BA",false);')
s = s.replace('light.setText("Light map\\nLight gray interface")', 'light.setText("Light interface")')
s = s.replace('dark.setText("Dark map\\nDark violet interface")', 'dark.setText("Dark interface")')

marker = '        TextView accountSection=label("Account",16,lightUi?"#25282E":"#DCE8F2",true);\n'
if 'Licenses & Data Sources' in s and 'settingsMenuButton("Licenses & Data Sources"' not in s and marker in s:
    menu = '''        TextView toolsSection=label("Information & Support",16,lightUi?"#25282E":"#DCE8F2",true);\n        toolsSection.setPadding(0,dp(4),0,dp(8)); box.addView(toolsSection);\n        Button licenses=settingsMenuButton("Licenses & Data Sources",false); box.addView(licenses,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52))); licenses.setOnClickListener(v->{dlg.dismiss();showLicensesAndSources();});\n        Button jobSources=settingsMenuButton("Job Sources",false); LinearLayout.LayoutParams jsp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); jsp.topMargin=dp(8); box.addView(jobSources,jsp); jobSources.setOnClickListener(v->{dlg.dismiss();showJobSourcesMenu();});\n        Button help=settingsMenuButton("Help & Support",false); LinearLayout.LayoutParams hp2=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); hp2.topMargin=dp(8); box.addView(help,hp2); help.setOnClickListener(v->{dlg.dismiss();showHelpSupport();});\n\n'''
    s = s.replace(marker, menu + marker, 1)

s = s.replace('sign.setText(guest?"Sign out of guest mode":"Sign out")', 'sign.setText(guest?"Exit guest mode":"Log Out")')

java.write_text(s, encoding='utf-8')

x = layout.read_text(encoding='utf-8')
if '@+id/careerOneStopAttribution' in x:
    start = x.find('    <TextView\n        android:id="@+id/careerOneStopAttribution"')
    if start >= 0:
        end = x.find('/>', start)
        if end >= 0:
            x = x[:start] + x[end+2:]
layout.write_text(x, encoding='utf-8')

if version.exists():
    version.write_text('9.4.43\n', encoding='utf-8')

for rel in ['backend/providers/indeed.js','backend/providers/glassdoor.js','backend/providers/ziprecruiter.js']:
    p = root / rel
    if p.exists(): p.unlink()

print('Applied JobBubble V9.4.43 default-map/settings patch')
