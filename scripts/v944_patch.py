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

# V9.4.45: unknown salary must not be treated as $0 and filtered out.
old_filter = 'boolean ok=d<=maxDistanceMiles&&j.pay>=minPay&&(source.equals("All sources")||j.source.equalsIgnoreCase(source))&&(category.equals("All jobs")||j.category.equalsIgnoreCase(category))&&(!preciseLocationsOnly||hasPreciseLocation(j));'
new_filter = 'boolean ok=d<=maxDistanceMiles&&(j.pay<=0||j.pay>=minPay)&&(source.equals("All sources")||j.source.equalsIgnoreCase(source))&&(category.equals("All jobs")||j.category.equalsIgnoreCase(category))&&(!preciseLocationsOnly||hasPreciseLocation(j));'
if old_filter in s:
    s = s.replace(old_filter, new_filter, 1)
elif new_filter not in s:
    raise SystemExit('Salary filter patch target not found')

# V9.4.46: large clusters represent multiple jobs, especially Muse jobs that share
# an approximate city-level coordinate. Tapping a cluster of more than five jobs should
# always open the scrollable job list immediately instead of repeatedly zooming in first.
old_cluster = 'if(pile.jobIndexes.size()>5 && zoom>=16.8f){\n                    showClusterSideList(pile);'
new_cluster = 'if(pile.jobIndexes.size()>5){\n                    showClusterSideList(pile);'
if old_cluster in s:
    s = s.replace(old_cluster, new_cluster, 1)
elif new_cluster not in s:
    raise SystemExit('Large-cluster click patch target not found')

# Version bump.
if version.exists():
    version.write_text('9.4.46\n', encoding='utf-8')

java.write_text(s, encoding='utf-8')
print('Applied JobBubble V9.4.46 Muse cluster-list fix')
