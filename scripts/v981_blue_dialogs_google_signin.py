from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
main = root / "app/src/main/java/com/jobbubble/app/MainActivity.java"
build = root / "app/build.gradle"
version = root / "VERSION.txt"
google_bg = root / "app/src/main/res/drawable/welcome_google_button.xml"

for path in (main, build, version, google_bg):
    if not path.exists():
        raise SystemExit(f"missing required file: {path}")

text = main.read_text(encoding="utf-8")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return source.replace(old, new, 1)


# Job category / source chooser: dark mode only. Layout, dimensions, text, icons,
# callbacks and light-mode styling are intentionally untouched.
choice_changes = [
    ('final String panel=light?"#ECEEF1":"#0C051F";', 'final String panel=light?"#ECEEF1":"#0B1A29";'),
    ('final String rowNormal=light?"#E6E8EC":"#100921";', 'final String rowNormal=light?"#E6E8EC":"#0E2132";'),
    ('final String rowSelected=light?"#E4DCF0":"#24103D";', 'final String rowSelected=light?"#E4DCF0":"#10283A";'),
    ('final String borderNormal=light?"#C9CDD3":"#2B1B45";', 'final String borderNormal=light?"#C9CDD3":"#31546C";'),
    ('final String borderSelected=light?"#8A63B7":"#7336B5";', 'final String borderSelected=light?"#8A63B7":"#2196F3";'),
    ('final int primary=Color.parseColor(light?"#20242A":"#F6F2FF");', 'final int primary=Color.parseColor(light?"#20242A":"#F4F8FC");'),
    ('final int secondary=Color.parseColor(light?"#676D76":"#BBA9E5");', 'final int secondary=Color.parseColor(light?"#676D76":"#8FA7BA");'),
    ('final int violet=Color.parseColor(light?"#6B3AA1":"#B56DFF");', 'final int violet=Color.parseColor(light?"#6B3AA1":"#2196F3");'),
    ('root.setBackground(roundStrokeBg(panel,light?"#B8A2CE":"#6E2FA4",24,1));', 'root.setBackground(roundStrokeBg(panel,light?"#B8A2CE":"#31546C",24,1));'),
    ('hero.setBackground(roundStrokeBg(light?"#E7E1EF":"#1B0D31",light?"#B69CCE":"#663399",16,1));', 'hero.setBackground(roundStrokeBg(light?"#E7E1EF":"#10283A",light?"#B69CCE":"#31546C",16,1));'),
    ('close.setBackground(roundStrokeBg(light?"#E4E6EA":"#1A0D2C",light?"#C1B3D0":"#4B2A70",25,1)); close.setOnClickListener(v->dialog.dismiss());', 'close.setBackground(roundStrokeBg(light?"#E4E6EA":"#10283A",light?"#C1B3D0":"#31546C",25,1)); close.setOnClickListener(v->dialog.dismiss());'),
    ('new int[]{violet,Color.parseColor(light?"#8F969E":"#B7A8DD")}', 'new int[]{violet,Color.parseColor(light?"#8F969E":"#8FA7BA")}'),
    ('Color.parseColor(light?"#25282D":"#E9DFFF")', 'Color.parseColor(light?"#25282D":"#F4F8FC")'),
    ('roundStrokeBg(light?"#F3F4F6":"#160B28",light?"#B8BCC3":"#6B3BA0",16,1)', 'roundStrokeBg(light?"#F3F4F6":"#10283A",light?"#B8BCC3":"#31546C",16,1)'),
    ('new int[]{Color.parseColor(light?"#7434C8":"#5A169A"),Color.parseColor(light?"#9D35E8":"#7A1CC7")}', 'new int[]{Color.parseColor(light?"#7434C8":"#168CF0"),Color.parseColor(light?"#9D35E8":"#2196F3")}'),
]
for old, new in choice_changes:
    text = replace_once(text, old, new, "choice menu color")

# Search and List sheets: dark-mode colors only. No structure or behavior changes.
list_search_changes = [
    ('row.setBackground(roundStrokeBg(light?"#E3E5E8":"#110B25",light?"#C8CBD1":"#3B275B",16,1));', 'row.setBackground(roundStrokeBg(light?"#E3E5E8":"#0E2132",light?"#C8CBD1":"#31546C",16,1));'),
    ('TextView title=label(j.title,16,light?"#202329":"#F5F7FB",true);', 'TextView title=label(j.title,16,light?"#202329":"#F4F8FC",true);'),
    ('TextView company=label(j.company+"  •  "+money(distanceMiles(userLat,userLon,j.lat,j.lon))+" mi",12,light?"#656B75":"#A99CC9",false);', 'TextView company=label(j.company+"  •  "+money(distanceMiles(userLat,userLon,j.lat,j.lon))+" mi",12,light?"#656B75":"#8FA7BA",false);'),
    ('TextView arrow=label("›",28,light?"#6B3AA5":"#B98CFF",false);', 'TextView arrow=label("›",28,light?"#6B3AA5":"#2196F3",false);'),
    ('box.setBackground(roundStrokeBg(light?"#E9EAED":"#0B0717",light?"#C9CCD2":"#3F2463",28,1));', 'box.setBackground(roundStrokeBg(light?"#E9EAED":"#0B1A29",light?"#C9CCD2":"#31546C",28,1));'),
    ('handle.setBackground(roundBg(light?"#A9ADB4":"#73519C",10));', 'handle.setBackground(roundBg(light?"#A9ADB4":"#526A7E",10));'),
    ('TextView title=label(titleText,23,light?"#202329":"#F8F6FF",true);', 'TextView title=label(titleText,23,light?"#202329":"#F4F8FC",true);'),
    ('TextView sub=label(subtitle,13,light?"#676D76":"#A99CC9",false);', 'TextView sub=label(subtitle,13,light?"#676D76":"#8FA7BA",false);'),
    ('close.setBackground(roundStrokeBg(isLightUi()?"#DFE1E5":"#17102C",isLightUi()?"#BFC3CA":"#6E3DA8",14,1));', 'close.setBackground(roundStrokeBg(isLightUi()?"#DFE1E5":"#10283A",isLightUi()?"#BFC3CA":"#31546C",14,1));'),
    ('isLightUi()?"#5D636C":"#A99CC9"', 'isLightUi()?"#5D636C":"#8FA7BA"'),
    ('search.setHintTextColor(Color.parseColor(isLightUi()?"#858B94":"#80739A"));', 'search.setHintTextColor(Color.parseColor(isLightUi()?"#858B94":"#6F879A"));'),
    ('search.setTextColor(Color.parseColor(isLightUi()?"#202329":"#F5F2FB"));', 'search.setTextColor(Color.parseColor(isLightUi()?"#202329":"#F4F8FC"));'),
    ('search.setBackground(roundStrokeBg(isLightUi()?"#DFE1E5":"#100A20",isLightUi()?"#BFC3CA":"#55327B",18,1));', 'search.setBackground(roundStrokeBg(isLightUi()?"#DFE1E5":"#0E2132",isLightUi()?"#BFC3CA":"#31546C",18,1));'),
    ('TextView nearby=label(maxDistanceMiles+" mi",13,isLightUi()?"#4C2E72":"#CCB4F5",true);', 'TextView nearby=label(maxDistanceMiles+" mi",13,isLightUi()?"#4C2E72":"#F4F8FC",true);'),
    ('nearby.setBackground(roundStrokeBg(isLightUi()?"#E4E5E8":"#17102C",isLightUi()?"#C7BDD3":"#6D3FC3",15,1));', 'nearby.setBackground(roundStrokeBg(isLightUi()?"#E4E5E8":"#10283A",isLightUi()?"#C7BDD3":"#31546C",15,1));'),
]
for old, new in list_search_changes:
    text = replace_once(text, old, new, "search/list color")

main.write_text(text, encoding="utf-8")

# Keep the existing Google sign-in UI and behavior; only make its existing button
# use the same visible blue/navy visual family. Both auth screens already reference
# this drawable, so no layout, spacing, text or click-handler change is required.
g = google_bg.read_text(encoding="utf-8")
g = replace_once(g, '<solid android:color="#102333" />', '<solid android:color="#10283A" />', "Google button fill")
g = replace_once(g, '<stroke android:width="1dp" android:color="#3B566A" />', '<stroke android:width="1dp" android:color="#2196F3" />', "Google button stroke")
google_bg.write_text(g, encoding="utf-8")

# Release metadata for the color/visibility fix only.
b = build.read_text(encoding="utf-8")
b = replace_once(b, "versionCode 87", "versionCode 88", "versionCode")
b = replace_once(b, "versionName '9.4.80'", "versionName '9.4.81'", "versionName")
if not re.search(r"targetSdk(?:Version)?\s+35\b", b):
    raise SystemExit("targetSdk 35 invariant missing")
build.write_text(b, encoding="utf-8")

if version.read_text(encoding="utf-8").strip() != "9.4.80":
    raise SystemExit("unexpected VERSION.txt baseline")
version.write_text("9.4.81\n", encoding="utf-8")

# Guard the Google sign-in behavior from accidental removal.
final_main = main.read_text(encoding="utf-8")
for required in (
    "googleWelcomeButton",
    "googleButton",
    "googleSignInClient.getSignInIntent()",
    "firebaseAuthWithGoogle(account)",
):
    if required not in final_main:
        raise SystemExit(f"Google sign-in invariant missing: {required}")

print("Applied JobBubble V9.4.81 blue dialog palette and Google sign-in visibility styling")
