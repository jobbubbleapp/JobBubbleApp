from pathlib import Path
import sys, json

root=Path(sys.argv[1])
java=root/'app/src/main/java/com/jobbubble/app/MainActivity.java'
raw=root/'app/src/main/res/raw'
version=root/'VERSION.txt'
s=java.read_text(encoding='utf-8')

# V9.4.47: dark appearance must style the actual Google map; light stays default Google Maps.
old='''            // Keep the map itself on Google Maps default styling. UI theme still applies to JobBubble controls.\n            googleMap.setMapStyle(null);\n            removeForeignCountryCurtains();'''
new='''            // JobBubble dark mode styles the actual Google map. Light mode remains normal Google Maps.\n            if("dark".equals(mapTheme)) googleMap.setMapStyle(MapStyleOptions.loadRawResourceStyle(this,R.raw.google_map_dark_style));\n            else googleMap.setMapStyle(new MapStyleOptions("[]"));\n            removeForeignCountryCurtains();'''
if old in s:
    s=s.replace(old,new,1)
elif 'R.raw.google_map_dark_style' not in s:
    raise SystemExit('Map theme patch target not found')

# Match dark settings/support sheets to the same deep navy family as the app exterior.
s=s.replace('light?"#ECEDEF":"#0B1A29"','light?"#ECEDEF":"#071C2C"')
s=s.replace('light?"#E2E4E8":"#10283A"','light?"#E2E4E8":"#0D2A40"')
s=s.replace('light?"#C3C7CD":"#31546C"','light?"#C3C7CD":"#315D78"')

# Correct appearance copy now that dark mode also changes Google Maps.
s=s.replace('Choose the JobBubble interface theme. The map itself keeps the normal Google Maps appearance.',
            'Choose the JobBubble appearance. Dark mode also applies a dark Google Maps style.')

raw.mkdir(parents=True,exist_ok=True)
style=[
 {"elementType":"geometry","stylers":[{"color":"#0b1f2d"}]},
 {"elementType":"labels.text.fill","stylers":[{"color":"#d7e5ef"}]},
 {"elementType":"labels.text.stroke","stylers":[{"color":"#071723"}]},
 {"featureType":"administrative","elementType":"geometry.stroke","stylers":[{"color":"#36566b"}]},
 {"featureType":"poi","elementType":"geometry","stylers":[{"color":"#102b35"}]},
 {"featureType":"poi.park","elementType":"geometry","stylers":[{"color":"#12372f"}]},
 {"featureType":"road","elementType":"geometry","stylers":[{"color":"#1c3545"}]},
 {"featureType":"road","elementType":"geometry.stroke","stylers":[{"color":"#0d2534"}]},
 {"featureType":"road.highway","elementType":"geometry","stylers":[{"color":"#31566b"}]},
 {"featureType":"transit","elementType":"geometry","stylers":[{"color":"#173241"}]},
 {"featureType":"water","elementType":"geometry","stylers":[{"color":"#06131d"}]},
 {"featureType":"water","elementType":"labels.text.fill","stylers":[{"color":"#8bb8d0"}]}
]
(raw/'google_map_dark_style.json').write_text(json.dumps(style,separators=(',',':')),encoding='utf-8')

if version.exists(): version.write_text('9.4.47\n',encoding='utf-8')
java.write_text(s,encoding='utf-8')
print('Applied JobBubble V9.4.47 dark map/menu theme patch')
