#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v950_muse_runtime_fix.py <project_dir>')

project = Path(sys.argv[1])
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = project / 'VERSION.txt'
text = main.read_text(encoding='utf-8')

# The backend provider key is `themuse`, while the UI label is `The Muse`.
# Do not compare raw provider labels when applying the client-side source filter.
old_filter = 'boolean ok=d<=maxDistanceMiles&&(j.pay<=0||j.pay>=minPay)&&(source.equals("All sources")||j.source.equalsIgnoreCase(source))&&(category.equals("All jobs")||j.category.equalsIgnoreCase(category))&&(!preciseLocationsOnly||hasPreciseLocation(j));'
new_filter = 'boolean ok=d<=maxDistanceMiles&&(j.pay<=0||j.pay>=minPay)&&(source.equals("All sources")||sourcesMatch(j.source,source))&&(category.equals("All jobs")||j.category.equalsIgnoreCase(category))&&(!preciseLocationsOnly||hasPreciseLocation(j));'
if old_filter in text:
    text = text.replace(old_filter, new_filter, 1)
elif new_filter not in text:
    raise SystemExit('Muse source filter target not found')

# Canonicalize both server/provider values and UI labels. This also makes source
# filtering tolerant of harmless punctuation/spacing differences from providers.
if 'private boolean sourcesMatch(String jobSource,String selectedSource)' not in text:
    helper = '''    private String canonicalSourceKey(String value){
        if(value==null)return "";
        String key=value.trim().toLowerCase(java.util.Locale.US).replaceAll("[^a-z0-9]","");
        if(key.equals("muse")||key.equals("themuse"))return "themuse";
        if(key.equals("usajob")||key.equals("usajobs"))return "usajobs";
        if(key.equals("adzuna"))return "adzuna";
        if(key.equals("allsources")||key.equals("all"))return "allsources";
        return key;
    }

    private boolean sourcesMatch(String jobSource,String selectedSource){
        if(selectedSource==null||"All sources".equalsIgnoreCase(selectedSource))return true;
        return canonicalSourceKey(jobSource).equals(canonicalSourceKey(selectedSource));
    }

'''
    markers = [
        '    private void loadJobs(){\n',
        '    private void loadJobs() {\n',
        '    private String sourceApiValue(',
        '    private String sourceKey(',
    ]
    inserted = False
    for marker in markers:
        if marker in text:
            text = text.replace(marker, helper + marker, 1)
            inserted = True
            break
    if not inserted:
        # Fall back to inserting immediately before the final class brace.
        pos = text.rfind('\n}')
        if pos < 0:
            raise SystemExit('Could not find insertion point for Muse source helpers')
        text = text[:pos] + '\n' + helper + text[pos:]

# Add small, targeted diagnostics so the emulator verifier can distinguish
# transport/parsing/filter failures without dumping job descriptions or secrets.
if 'JobBubbleMuse"' not in text:
    # Log once per Muse candidate at the existing filter point. CI only tails these
    # lines, and release behavior is otherwise unchanged.
    logged_filter = new_filter + '\n                if("The Muse".equalsIgnoreCase(source)) android.util.Log.d("JobBubbleMuse","candidate source="+j.source+" title="+j.title+" pass="+ok);'
    if new_filter in text:
        text = text.replace(new_filter, logged_filter, 1)

main.write_text(text, encoding='utf-8')
if version.exists():
    version.write_text('9.4.50\n', encoding='utf-8')

print('Applied JobBubble V9.4.50 Muse runtime source-matching fix')
