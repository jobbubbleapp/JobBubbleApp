from pathlib import Path
import sys

root = Path(sys.argv[1])
java = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = root / 'VERSION.txt'
s = java.read_text(encoding='utf-8')

# Replace the temporary CareerOneStop-facing source with The Muse.
s = s.replace('final String[] src={"All sources","Adzuna","USAJOBS","CareerOneStop"};', 'final String[] src={"All sources","Adzuna","USAJOBS","The Muse"};')
s = s.replace('if(item.equals("CareerOneStop")) return "CS";', 'if(item.equals("The Muse")) return "TM";')
s = s.replace('if(value.equalsIgnoreCase("CareerOneStop")||value.equalsIgnoreCase("CareerOneStop/NLx"))return "CareerOneStop";', 'if(value.equalsIgnoreCase("The Muse")||value.equalsIgnoreCase("Muse"))return "The Muse";\n        if(value.equalsIgnoreCase("CareerOneStop")||value.equalsIgnoreCase("CareerOneStop/NLx"))return "All sources";')
s = s.replace('if("CareerOneStop".equalsIgnoreCase(source))return "careeronestop";', 'if("The Muse".equalsIgnoreCase(source))return "themuse";')

# Hide CareerOneStop from all visible source information, but keep backend/provider code intact.
s = s.replace('        box.addView(infoCard("CareerOneStop / NLx","U.S. Department of Labor job-search data. CareerOneStop attribution is shown here instead of covering the map."));\n        LinearLayout.LayoutParams gap=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); gap.topMargin=dp(8);\n        box.addView(infoCard("USAJOBS","Official U.S. federal government job listings."),gap);',
'''        box.addView(infoCard("The Muse","Private-sector job listings supplied through The Muse API."));
        LinearLayout.LayoutParams gap=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); gap.topMargin=dp(8);
        box.addView(infoCard("USAJOBS","Official U.S. federal government job listings."),gap);''')
s = s.replace('final String[] choices={"All sources","Adzuna","USAJOBS","CareerOneStop"};', 'final String[] choices={"All sources","Adzuna","USAJOBS","The Muse"};')
s = s.replace('choice.equals("USAJOBS")?"Federal government jobs":"CareerOneStop / NLx listings";', 'choice.equals("USAJOBS")?"Federal government jobs":"Private-sector jobs from The Muse";')

# Version bump.
if version.exists():
    version.write_text('9.4.44\n', encoding='utf-8')

java.write_text(s, encoding='utf-8')
print('Applied JobBubble V9.4.44 The Muse source patch')
