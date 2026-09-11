from pathlib import Path
import sys

root = Path(sys.argv[1])
java = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
layout = root / 'app/src/main/res/layout/activity_main.xml'
version = root / 'VERSION.txt'

s = java.read_text()
s = s.replace('final String[] src={"All sources","Adzuna","USAJOBS"};', 'final String[] src={"All sources","Adzuna","USAJOBS","CareerOneStop"};')
s = s.replace('if(item.equals("USAJOBS")) return "US";', 'if(item.equals("USAJOBS")) return "US";\n        if(item.equals("CareerOneStop")) return "CS";')
s = s.replace('if(value.equalsIgnoreCase("USAJOBS"))return "USAJOBS";', 'if(value.equalsIgnoreCase("USAJOBS"))return "USAJOBS";\n        if(value.equalsIgnoreCase("CareerOneStop")||value.equalsIgnoreCase("CareerOneStop/NLx"))return "CareerOneStop";')
s = s.replace('if("USAJOBS".equalsIgnoreCase(source))return "usajobs";', 'if("USAJOBS".equalsIgnoreCase(source))return "usajobs";\n        if("CareerOneStop".equalsIgnoreCase(source))return "careeronestop";')
s = s.replace('final int fill=Color.parseColor(isLightUi()?"#E7E8EB":"#111820");', 'final int fill=Color.parseColor(isLightUi()?"#A9D8F2":"#12384F");')
s = s.replace('// region is covered by a solid curtain above the Google base map.', '// region is covered by an ocean-colored curtain above the Google base map.')
s = s.replace('// foreign roads, cities, labels, terrain and country names from showing at all.', '// foreign roads, cities, labels, terrain and country names from showing at all while making non-U.S. land visually read as ocean.')
java.write_text(s)

x = layout.read_text()
if '@+id/careerOneStopAttribution' not in x:
    marker = '''\n    <LinearLayout\n        android:id="@+id/bottomNav"'''
    attr = '''\n    <TextView\n        android:id="@+id/careerOneStopAttribution"\n        android:layout_width="wrap_content"\n        android:layout_height="26dp"\n        android:layout_gravity="bottom|center_horizontal"\n        android:layout_marginBottom="84dp"\n        android:paddingLeft="10dp"\n        android:paddingRight="10dp"\n        android:gravity="center"\n        android:background="#CC0B2232"\n        android:text="CareerOneStop • U.S. Department of Labor"\n        android:textColor="#EAF6FF"\n        android:textSize="10sp"\n        android:textStyle="bold"\n        android:elevation="8dp" />\n\n    <LinearLayout\n        android:id="@+id/bottomNav"'''
    if marker not in x:
        raise SystemExit('bottomNav insertion point not found')
    x = x.replace(marker, attr, 1)
layout.write_text(x)

if version.exists():
    version.write_text('9.4.42\n')

# Remove archived provider experiments from the packaged project. They are not used by the Android client.
for rel in ['backend/providers/indeed.js','backend/providers/glassdoor.js','backend/providers/ziprecruiter.js']:
    p = root / rel
    if p.exists():
        p.unlink()

print('Applied JobBubble V9.4.42 Android patch')
