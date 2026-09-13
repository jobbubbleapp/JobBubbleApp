#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v962_top_safe_area.py <project_dir>')

project = Path(sys.argv[1]).resolve()
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = project / 'VERSION.txt'
text = main.read_text(encoding='utf-8')

needle = 'setContentView(R.layout.activity_main);'
if needle not in text:
    raise SystemExit('setContentView target not found')

insertion = '''setContentView(R.layout.activity_main);\n\n        // Keep the top header clear of camera cutouts while preserving fullscreen chrome.\n        // We intentionally leave the bottom edge alone so the floating navigation keeps its current position.\n        final android.view.View appContent=findViewById(android.R.id.content);\n        if(appContent!=null){\n            final int baseLeft=appContent.getPaddingLeft();\n            final int baseTop=appContent.getPaddingTop();\n            final int baseRight=appContent.getPaddingRight();\n            final int baseBottom=appContent.getPaddingBottom();\n            appContent.setOnApplyWindowInsetsListener((v,insets)->{\n                int cutoutTop=0;\n                if(android.os.Build.VERSION.SDK_INT>=28 && insets.getDisplayCutout()!=null){\n                    cutoutTop=insets.getDisplayCutout().getSafeInsetTop();\n                }\n                int topRoom=Math.max(dp(12),cutoutTop+dp(4));\n                v.setPadding(baseLeft,baseTop+topRoom,baseRight,baseBottom);\n                return insets;\n            });\n            appContent.requestApplyInsets();\n        }'''

if 'getDisplayCutout().getSafeInsetTop()' not in text:
    text = text.replace(needle, insertion, 1)

main.write_text(text, encoding='utf-8')
version.write_text('9.4.61\n', encoding='utf-8')
print('Applied V9.4.61 top safe-area padding for display cutouts')
