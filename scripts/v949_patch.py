from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
java = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
gradle = root / 'app/build.gradle'
version = root / 'VERSION.txt'

s = java.read_text(encoding='utf-8')

# Android can grant ACCESS_COARSE_LOCATION while denying ACCESS_FINE_LOCATION when
# the user disables Precise location. The old callback only checked grantResults[0]
# (FINE), so approximate-only users were treated as having denied location entirely.
old = '''    @Override public void onRequestPermissionsResult(int r,@NonNull String[] p,@NonNull int[] g){super.onRequestPermissionsResult(r,p,g);if(r==LOCATION_REQUEST&&g.length>0&&g[0]==PackageManager.PERMISSION_GRANTED)enableLocation();else{jobs.clear();applyFilters();status.setText("Location permission is required for nearby live jobs");centerOnUser();}}'''
new = '''    @Override public void onRequestPermissionsResult(int r,@NonNull String[] p,@NonNull int[] g){
        super.onRequestPermissionsResult(r,p,g);
        if(r!=LOCATION_REQUEST)return;
        boolean fine=ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED;
        boolean coarse=ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED;
        if(fine||coarse){
            enableLocation();
        }else{
            jobs.clear();
            applyFilters();
            status.setText("Location permission is required for nearby live jobs");
            centerOnUser();
        }
    }'''
if old not in s:
    raise SystemExit('Location permission callback target not found')
s = s.replace(old, new, 1)

# Keep visible/report/package metadata aligned.
s = s.replace('Version 9.4.48', 'Version 9.4.49')
s = s.replace('payload.put("app_version","9.4.48")', 'payload.put("app_version","9.4.49")')
s = s.replace('TextView version=label("v9.4.47",12,', 'TextView version=label("v9.4.49",12,')
s = s.replace('TextView version=label("v9.4.48",12,', 'TextView version=label("v9.4.49",12,')

if gradle.exists():
    g = gradle.read_text(encoding='utf-8')
    g = re.sub(r'versionCode\s+\d+', 'versionCode 83', g, count=1)
    g = re.sub(r"versionName\s+['\"][^'\"]+['\"]", "versionName '9.4.49'", g, count=1)
    gradle.write_text(g, encoding='utf-8')

if version.exists():
    version.write_text('9.4.49\n', encoding='utf-8')

java.write_text(s, encoding='utf-8')

checks = [
    'boolean fine=ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED;',
    'boolean coarse=ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED;',
    'if(fine||coarse)',
    'Version 9.4.49',
]
for check in checks:
    if check not in s:
        raise SystemExit(f'Missing V9.4.49 location fix: {check}')

print('Applied JobBubble V9.4.49 approximate-location permission fix')
