from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
java = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
gradle = root / 'app/build.gradle'
version = root / 'VERSION.txt'

s = java.read_text(encoding='utf-8')

# Maps SDK 19.0.0 has a native dark/light color scheme. V9.4.43 intentionally
# forced googleMap.setMapStyle(null), which left the base map light even when
# JobBubble's dark appearance was selected. Restore a real map theme here.
if 'import com.google.android.gms.maps.MapColorScheme;' not in s:
    anchor = 'import com.google.android.gms.maps.GoogleMap;\n'
    if anchor not in s:
        raise SystemExit('GoogleMap import target not found')
    s = s.replace(anchor, anchor + 'import com.google.android.gms.maps.MapColorScheme;\n', 1)

old_theme = '''    private void applyMapTheme(){
        if(!mapReady || googleMap==null)return;
        try{
            // Keep the map itself on Google Maps default styling. UI theme still applies to JobBubble controls.
            googleMap.setMapStyle(null);
            removeForeignCountryCurtains();
        }catch(Exception ignored){}
    }
'''
new_theme = '''    private void applyMapTheme(){
        if(!mapReady || googleMap==null)return;
        try{
            // Use the Maps SDK native color scheme. Clear legacy JSON styling first because
            // MapColorScheme only affects maps that are not using local JSON styling.
            googleMap.setMapStyle(null);
            googleMap.setMapColorScheme("dark".equals(mapTheme)?MapColorScheme.DARK:MapColorScheme.LIGHT);
            removeForeignCountryCurtains();
        }catch(Exception e){
            android.util.Log.e("JobBubbleMap","Failed to apply map color scheme: "+mapTheme,e);
        }
    }
'''
if old_theme in s:
    s = s.replace(old_theme, new_theme, 1)
elif 'googleMap.setMapColorScheme("dark".equals(mapTheme)?MapColorScheme.DARK:MapColorScheme.LIGHT);' not in s:
    raise SystemExit('applyMapTheme target not found')

# Restore the settings copy so the control accurately describes what it now changes.
s = s.replace(
    'TextView section=label("App appearance",16,lightUi?"#25282E":"#DCE8F2",true);',
    'TextView section=label("Map appearance",16,lightUi?"#25282E":"#DCE8F2",true);'
)
s = s.replace(
    'TextView mapSub=label("Choose the JobBubble interface theme. The map itself keeps the normal Google Maps appearance.",13,lightUi?"#646B74":"#8FA7BA",false);',
    'TextView mapSub=label("Choose the map style. The rest of the app follows it.",13,lightUi?"#646B74":"#8FA7BA",false);'
)
s = s.replace('light.setText("Light interface")', 'light.setText("Light map\\nLight gray interface")')
s = s.replace('dark.setText("Dark interface")', 'dark.setText("Dark map\\nDark violet interface")')

# Keep visible/report metadata aligned with this release.
s = s.replace('Version 9.4.47', 'Version 9.4.48')
s = s.replace('payload.put("app_version","9.4.47")', 'payload.put("app_version","9.4.48")')

if gradle.exists():
    g = gradle.read_text(encoding='utf-8')
    g = re.sub(r'versionCode\s+\d+', 'versionCode 82', g, count=1)
    g = re.sub(r"versionName\s+['\"][^'\"]+['\"]", "versionName '9.4.48'", g, count=1)
    gradle.write_text(g, encoding='utf-8')

if version.exists():
    version.write_text('9.4.48\n', encoding='utf-8')

java.write_text(s, encoding='utf-8')
print('Applied JobBubble V9.4.48 native dark/light Google Map fix')
