#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_DIR:?PROJECT_DIR is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"

EXPECTED_FILE="$RUNNER_TEMP/expected-muse-titles.txt"

python3 - <<'PY'
import json, os, time, urllib.request
url='https://jobbubble-backend-1.onrender.com/jobs?where=Everett%2C+WA&lat=47.9780&lon=-122.2021&radius=100&source=themuse'
last=None
for attempt in range(3):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'JobBubble-Verification/9.4.49'})
        with urllib.request.urlopen(req, timeout=90) as r:
            data=json.load(r)
        break
    except Exception as e:
        last=e
        print(f'Backend attempt {attempt+1} failed: {e}')
        if attempt < 2:
            time.sleep(8)
else:
    raise last
jobs=data.get('jobs') or []
titles=[]
for j in jobs:
    title=str(j.get('title') or '').strip()
    src=str(j.get('source') or '').lower()
    if title and ('muse' in src or not src):
        titles.append(title)
titles=list(dict.fromkeys(titles))
print('LIVE_MUSE_JOB_COUNT=',len(titles))
print('LIVE_MUSE_TITLES=',titles[:20])
if len(titles) < 2:
    raise SystemExit('Backend did not provide at least two Muse jobs')
open(os.environ['RUNNER_TEMP']+'/expected-muse-titles.txt','w').write('\n'.join(titles))
PY

dump_ui() {
  local name="$1"
  adb shell uiautomator dump --compressed "/sdcard/$name.xml" >/dev/null 2>&1 || true
  adb pull "/sdcard/$name.xml" "$RUNNER_TEMP/$name.xml" >/dev/null 2>&1 || true
}

tap_text() {
  local text="$1" file="$2"
  python3 - "$text" "$file" <<'PY'
import html,re,subprocess,sys
needle,path=sys.argv[1:]
s=open(path).read()
for node in re.findall(r'<node[^>]*>',s):
    mt=re.search(r'text="([^"]*)"',node)
    mb=re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',node)
    if mt and mb and needle.casefold() in html.unescape(mt.group(1)).casefold():
        x=(int(mb[1])+int(mb[3]))//2
        y=(int(mb[2])+int(mb[4]))//2
        subprocess.run(['adb','shell','input','tap',str(x),str(y)],check=True)
        raise SystemExit(0)
raise SystemExit('missing text '+needle)
PY
}

tap_resource() {
  local id="$1" file="$2"
  python3 - "$id" "$file" <<'PY'
import re,subprocess,sys
wanted,path=sys.argv[1:]
s=open(path).read()
for node in re.findall(r'<node[^>]*>',s):
    mr=re.search(r'resource-id="([^"]*)"',node)
    mb=re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',node)
    if mr and mb and (mr.group(1)==wanted or mr.group(1).endswith('/'+wanted)):
        x=(int(mb[1])+int(mb[3]))//2
        y=(int(mb[2])+int(mb[4]))//2
        print(f'Tapping {mr.group(1)} at {x},{y}')
        subprocess.run(['adb','shell','input','tap',str(x),str(y)],check=True)
        raise SystemExit(0)
raise SystemExit('missing resource-id '+wanted)
PY
}

set_text_by_desc() {
  local desc="$1" value="$2" file="$3"
  python3 - "$desc" "$value" "$file" <<'PY'
import html,re,subprocess,sys
desc,value,path=sys.argv[1:]
s=open(path).read()
for node in re.findall(r'<node[^>]*>',s):
    md=re.search(r'content-desc="([^"]*)"',node)
    mb=re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',node)
    if md and mb and html.unescape(md.group(1)).casefold()==desc.casefold():
        x=(int(mb[1])+int(mb[3]))//2
        y=(int(mb[2])+int(mb[4]))//2
        subprocess.run(['adb','shell','input','tap',str(x),str(y)],check=True)
        subprocess.run(['adb','shell','input','keyevent','KEYCODE_MOVE_END'],check=True)
        for _ in range(8):
            subprocess.run(['adb','shell','input','keyevent','KEYCODE_DEL'],check=True)
        subprocess.run(['adb','shell','input','text',value],check=True)
        subprocess.run(['adb','shell','input','keyevent','KEYCODE_BACK'],check=True)
        raise SystemExit(0)
raise SystemExit('missing content-desc '+desc)
PY
}

dismiss_system_overlays() {
  for n in 1 2 3 4 5; do
    dump_ui "overlay-$n"
    local f="$RUNNER_TEMP/overlay-$n.xml"
    if grep -q 'Got it' "$f" 2>/dev/null; then tap_text 'Got it' "$f"; sleep 2; continue; fi
    if grep -q "isn't responding" "$f" 2>/dev/null; then
      if grep -q 'Close app' "$f"; then tap_text 'Close app' "$f"; else tap_text 'Wait' "$f" || true; fi
      sleep 2; continue
    fi
    if grep -q 'System UI has stopped' "$f" 2>/dev/null; then tap_text 'Close app' "$f" || true; sleep 2; continue; fi
    break
  done
}

reach_main_screen() {
  for n in $(seq 1 10); do
    dismiss_system_overlays
    dump_ui "entry-$n"
    local f="$RUNNER_TEMP/entry-$n.xml"
    if grep -qi 'All sources' "$f" 2>/dev/null; then
      echo "Reached JobBubble main screen on attempt $n"
      return 0
    fi
    if grep -qi 'Continue as Guest' "$f" 2>/dev/null; then
      tap_text 'Continue as Guest' "$f"
      sleep 4
      continue
    fi
    if grep -qi 'Guest' "$f" 2>/dev/null; then
      tap_text 'Guest' "$f"
      sleep 4
      continue
    fi
    sleep 2
  done
  echo 'Could not reach JobBubble main screen after retries'
  return 1
}

visible_expected_count() {
  local xml="$1"
  python3 - "$xml" "$EXPECTED_FILE" <<'PY'
import html,re,sys
xml_path,expected_path=sys.argv[1:]
xml=open(xml_path).read()
texts=[html.unescape(x) for x in re.findall(r'text="([^"]+)"',xml) if x.strip()]
def norm(s): return ' '.join(s.casefold().split())
visible='\n'.join(norm(x) for x in texts)
expected=[x.strip() for x in open(expected_path) if x.strip()]
matches=[t for t in expected if norm(t) in visible]
print('VISIBLE_LIST_TEXTS=',texts)
print('VISIBLE_EXPECTED_MUSE_MATCHES=',matches)
print(len(set(matches)))
PY
}

adb wait-for-device
adb shell 'while [[ -z $(getprop sys.boot_completed) ]]; do sleep 1; done'
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0
adb emu geo fix -122.2021 47.9780 || true

APK=$(find "$PROJECT_DIR" -type f -path '*/build/outputs/apk/debug/*.apk' -print -quit)
test -n "$APK"
adb install -r -g "$APK"
BUILD_TOOLS=$(find "$ANDROID_HOME/build-tools" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -V | tail -n1)
AAPT="$ANDROID_HOME/build-tools/$BUILD_TOOLS/aapt"
PKG=$("$AAPT" dump badging "$APK" | sed -n "s/package: name='\([^']*\)'.*/\1/p")
ACT=$("$AAPT" dump badging "$APK" | sed -n "s/launchable-activity: name='\([^']*\)'.*/\1/p")

adb shell am force-stop com.google.android.apps.nexuslauncher || true
adb logcat -c
adb shell am force-stop "$PKG"
adb shell am start -W -n "$PKG/$ACT"
sleep 3
dismiss_system_overlays
reach_main_screen

dump_ui main
grep -q 'package="com.jobbubble.app"' "$RUNNER_TEMP/main.xml"
grep -qi 'All sources' "$RUNNER_TEMP/main.xml"

# Select The Muse.
tap_text 'All sources' "$RUNNER_TEMP/main.xml"
sleep 1
dump_ui source-menu
tap_text 'The Muse' "$RUNNER_TEMP/source-menu.xml"
sleep 1
dump_ui source-selected
if grep -q 'Apply' "$RUNNER_TEMP/source-selected.xml"; then tap_text 'Apply' "$RUNNER_TEMP/source-selected.xml"; fi
sleep 3
dismiss_system_overlays
dump_ui after-source
grep -q 'The Muse' "$RUNNER_TEMP/after-source.xml"

# Set 100 miles.
if grep -Eqi '25 ?mi' "$RUNNER_TEMP/after-source.xml"; then
  tap_text '25' "$RUNNER_TEMP/after-source.xml"
else
  tap_text 'Distance' "$RUNNER_TEMP/after-source.xml"
fi
sleep 1
dump_ui distance-menu
set_text_by_desc 'miles' '100' "$RUNNER_TEMP/distance-menu.xml"
sleep 1
dump_ui distance-selected
grep -q 'text="100"' "$RUNNER_TEMP/distance-selected.xml"
if grep -q 'Apply' "$RUNNER_TEMP/distance-selected.xml"; then tap_text 'Apply' "$RUNNER_TEMP/distance-selected.xml"; fi
sleep 3
dismiss_system_overlays
dump_ui selected-filters
grep -q 'The Muse' "$RUNNER_TEMP/selected-filters.xml"
grep -q '100' "$RUNNER_TEMP/selected-filters.xml"

# Give live jobs time to load, preserving map evidence.
sleep 20
dismiss_system_overlays
dump_ui loaded-map
adb exec-out screencap -p > "$RUNNER_TEMP/loaded-map.png"

# Tap the clickable navigation container, not its non-clickable TextView label.
tap_resource 'navList' "$RUNNER_TEMP/loaded-map.xml"
sleep 3

# Poll the actual list for live Muse titles. This tolerates normal backend/render latency.
passed=0
for n in $(seq 1 8); do
  dismiss_system_overlays
  dump_ui "list-$n"
  adb exec-out screencap -p > "$RUNNER_TEMP/list.png"
  count=$(visible_expected_count "$RUNNER_TEMP/list-$n.xml" | tail -n1)
  echo "Visible expected Muse title count on list poll $n: $count"
  cp "$RUNNER_TEMP/list-$n.xml" "$RUNNER_TEMP/list.xml"
  if [ "$count" -ge 2 ]; then
    passed=1
    break
  fi
  sleep 5
done

echo '=== APP LOGS / MUSE ==='
adb logcat -d -v brief | grep -i -E 'JobBubble|Muse|/jobs|http|error|exception' | tail -n 800 || true

if [ "$passed" -ne 1 ]; then
  echo 'FAIL: running JobBubble app did not visibly display at least two distinct live Muse job titles'
  visible_expected_count "$RUNNER_TEMP/list.xml" || true
  exit 1
fi

echo 'PASS: running JobBubble app visibly displays multiple distinct live Muse jobs'
