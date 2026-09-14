#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v968_legal_links_help_only.py <project_dir>')

project = Path(sys.argv[1]).resolve()
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = project / 'VERSION.txt'
s = main.read_text(encoding='utf-8')

# V9.4.67 temporarily exposed Privacy Policy / Support / Delete Account directly
# on the main Options page. The desired UX is a single Help & Support entry on
# Options, with those three destinations nested inside Help & Support.
block = '''        Button privacyPolicyOption=settingsMenuButton("Privacy Policy",false); LinearLayout.LayoutParams ppOpt=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); ppOpt.topMargin=dp(8); box.addView(privacyPolicyOption,ppOpt); privacyPolicyOption.setOnClickListener(v->openJobBubbleWebPage("https://jobbubble-support.onrender.com/privacy.html"));\n        Button supportOption=settingsMenuButton("Support",false); LinearLayout.LayoutParams supOpt=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); supOpt.topMargin=dp(8); box.addView(supportOption,supOpt); supportOption.setOnClickListener(v->openJobBubbleWebPage("https://jobbubble-support.onrender.com/support.html"));\n        Button deleteAccountOption=settingsMenuButton("Delete Account",true); LinearLayout.LayoutParams delOpt=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); delOpt.topMargin=dp(8); box.addView(deleteAccountOption,delOpt); deleteAccountOption.setOnClickListener(v->openJobBubbleWebPage("https://jobbubble-support.onrender.com/delete-account.html"));\n'''
if block not in s:
    raise SystemExit('V9.4.67 direct Options legal-link block not found')
s = s.replace(block, '', 1)

# Verify Help & Support still owns all three destinations.
required = [
    'private void showHelpSupport()',
    'settingsMenuButton("Privacy Policy",false)',
    'settingsMenuButton("Support",false)',
    'settingsMenuButton("Delete Account & Data",true)',
    'https://jobbubble-support.onrender.com/privacy.html',
    'https://jobbubble-support.onrender.com/support.html',
    'https://jobbubble-support.onrender.com/delete-account.html',
]
for token in required:
    if token not in s:
        raise SystemExit('missing Help & Support legal-link token: ' + token)

# Ensure the temporary direct-Options controls are gone.
for token in ('privacyPolicyOption','supportOption','deleteAccountOption','settingsMenuButton("Delete Account",true)'):
    if token in s:
        raise SystemExit('direct Options legal-link token still present: ' + token)

main.write_text(s, encoding='utf-8')
version.write_text('9.4.68\n', encoding='utf-8')
print('Applied V9.4.68 legal/support links nested inside Help & Support only')
