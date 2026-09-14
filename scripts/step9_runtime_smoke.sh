#!/usr/bin/env bash
set -euo pipefail
API="${STEP9_API:?STEP9_API is required}"
APK=$(find "$RUNNER_TEMP/apk" -name '*.apk' -print -quit)
test -n "$APK"
LAST_UI=""

dump_ui(){
  local n="$1"
  adb shell uiautomator dump --compressed "/sdcard/$n.xml" >/dev/null 2>&1 || true
  adb pull "/sdcard/$n.xml" "$RUNNER_TEMP/$n.xml" >/dev/null 2>&1 || true
  if [ -s "$RUNNER_TEMP/$n.xml" ]; then LAST_UI="$RUNNER_TEMP/$n.xml"; fi
}

tap_text(){
  python3 - "$1" "$2" <<'PY'
import html,re,subprocess,sys
needle,path=sys.argv[1:]
try:
    data=open(path,encoding='utf-8').read()
except Exception:
    raise SystemExit(1)
for node in re.findall(r'<node[^>]*>',data):
    mt=re.search(r'text="([^"]*)"',node)
    mb=re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',node)
    if mt and mb and needle.casefold() in html.unescape(mt.group(1)).casefold():
        x=(int(mb[1])+int(mb[3]))//2
        y=(int(mb[2])+int(mb[4]))//2
        subprocess.run(['adb','shell','input','tap',str(x),str(y)],check=True)
        raise SystemExit(0)
raise SystemExit(1)
PY
}

capture_evidence(){
  set +e
  dump_ui "api${API}-last"
  if [ -n "${LAST_UI:-}" ] && [ -s "$LAST_UI" ]; then
    cp "$LAST_UI" "$RUNNER_TEMP/api${API}-last.xml" 2>/dev/null || true
  fi
  adb shell dumpsys activity activities > "$RUNNER_TEMP/api${API}-activity.txt" 2>&1 || true
  adb logcat -d -v time > "$RUNNER_TEMP/api${API}-logcat.txt" 2>&1 || true
  adb exec-out screencap -p > "$RUNNER_TEMP/api${API}-final.png" 2>/dev/null || true
}
trap capture_evidence EXIT

dismiss_overlays(){
  dump_ui "api${API}-overlay"
  local f="$RUNNER_TEMP/api${API}-overlay.xml"
  [ -s "$f" ] || return 0
  local t
  for t in 'Got it' 'While using the app' 'Only this time' 'Allow' 'ALLOW' 'OK'; do
    if grep -Fqi "$t" "$f" 2>/dev/null; then
      tap_text "$t" "$f" || true
      sleep 1
      dump_ui "api${API}-overlay-after"
      f="$RUNNER_TEMP/api${API}-overlay-after.xml"
    fi
  done
}

enter_guest(){
  local n f
  for n in $(seq 1 25); do
    dismiss_overlays
    dump_ui "api${API}-entry-$n"
    f="$RUNNER_TEMP/api${API}-entry-$n.xml"
    [ -s "$f" ] || { sleep 2; continue; }
    if grep -q 'package="com.jobbubble.app"' "$f" && grep -Fqi 'text="List"' "$f"; then return 0; fi
    if grep -Fqi 'Continue as Guest' "$f"; then tap_text 'Continue as Guest' "$f" || true; sleep 3; continue; fi
    if grep -q 'package="com.jobbubble.app"' "$f" && grep -Fqi 'Guest' "$f"; then tap_text 'Guest' "$f" || true; sleep 3; continue; fi
    sleep 2
  done
  echo "Failed to enter JobBubble guest/map state on API $API"
  return 1
}

wait_map(){
  local n f
  for n in $(seq 1 60); do
    dismiss_overlays
    dump_ui "api${API}-map-$n"
    f="$RUNNER_TEMP/api${API}-map-$n.xml"
    [ -s "$f" ] || { sleep 2; continue; }
    if grep -q 'package="com.jobbubble.app"' "$f" && grep -Fqi 'text="List"' "$f" && ! grep -Fq 'Loading your jobs list' "$f"; then
      cp "$f" "$RUNNER_TEMP/api${API}-final.xml"
      return 0
    fi
    sleep 2
  done
  echo "JobBubble map/list did not settle on API $API"
  return 1
}

adb wait-for-device
adb shell 'while [[ -z $(getprop sys.boot_completed) ]]; do sleep 1; done'
adb emu geo fix -122.2021 47.9780 || true
adb install -r -g "$APK"

BT=$(find "$ANDROID_HOME/build-tools" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -V | tail -n1)
AAPT="$ANDROID_HOME/build-tools/$BT/aapt"
PKG=$("$AAPT" dump badging "$APK" | sed -n "s/package: name='\([^']*\)'.*/\1/p")
ACT=$("$AAPT" dump badging "$APK" | sed -n "s/launchable-activity: name='\([^']*\)'.*/\1/p")
test -n "$PKG"
test -n "$ACT"

adb logcat -c
adb shell am start -W -n "$PKG/$ACT" >/dev/null
sleep 3
enter_guest
wait_map
capture_evidence

grep -q 'package="com.jobbubble.app"' "$RUNNER_TEMP/api${API}-final.xml"
grep -Fqi 'text="List"' "$RUNNER_TEMP/api${API}-final.xml"
if grep -Eiq 'FATAL EXCEPTION|Process: com\.jobbubble\.app.*FATAL|NoClassDefFoundError|VerifyError|FirebaseApp initialization unsuccessful|Default FirebaseApp failed to initialize' "$RUNNER_TEMP/api${API}-logcat.txt"; then
  echo "Runtime/Firebase failure detected on API $API"
  exit 1
fi

echo "PASS: JobBubble V9.4.80 startup/guest/map/Firebase smoke on API $API"
