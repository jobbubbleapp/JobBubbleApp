#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v967_options_legal_links.py <project_dir>')

project = Path(sys.argv[1]).resolve()
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = project / 'VERSION.txt'
s = main.read_text(encoding='utf-8')

# Put the Google Play-facing legal/support destinations directly on the main
# Options/Settings page while keeping the existing Help & Support page intact.
anchor = '''        Button help=settingsMenuButton("Help & Support",false); LinearLayout.LayoutParams hp2=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); hp2.topMargin=dp(8); box.addView(help,hp2); help.setOnClickListener(v->{dlg.dismiss();showHelpSupport();});\n'''
if anchor not in s:
    raise SystemExit('Options Help & Support anchor not found')

insert = anchor + '''        Button privacyPolicyOption=settingsMenuButton("Privacy Policy",false); LinearLayout.LayoutParams ppOpt=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); ppOpt.topMargin=dp(8); box.addView(privacyPolicyOption,ppOpt); privacyPolicyOption.setOnClickListener(v->openJobBubbleWebPage("https://jobbubble-support.onrender.com/privacy.html"));\n        Button supportOption=settingsMenuButton("Support",false); LinearLayout.LayoutParams supOpt=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); supOpt.topMargin=dp(8); box.addView(supportOption,supOpt); supportOption.setOnClickListener(v->openJobBubbleWebPage("https://jobbubble-support.onrender.com/support.html"));\n        Button deleteAccountOption=settingsMenuButton("Delete Account",true); LinearLayout.LayoutParams delOpt=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); delOpt.topMargin=dp(8); box.addView(deleteAccountOption,delOpt); deleteAccountOption.setOnClickListener(v->openJobBubbleWebPage("https://jobbubble-support.onrender.com/delete-account.html"));\n'''
s = s.replace(anchor, insert, 1)

required = [
    'settingsMenuButton("Privacy Policy",false)',
    'settingsMenuButton("Support",false)',
    'settingsMenuButton("Delete Account",true)',
    'privacyPolicyOption.setOnClickListener',
    'supportOption.setOnClickListener',
    'deleteAccountOption.setOnClickListener',
]
for token in required:
    if token not in s:
        raise SystemExit('missing Options legal link token: ' + token)

main.write_text(s, encoding='utf-8')
version.write_text('9.4.67\n', encoding='utf-8')
print('Applied V9.4.67 Privacy Policy, Support, and Delete Account to Options page')
