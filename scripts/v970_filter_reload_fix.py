#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v970_filter_reload_fix.py <project_dir>')

root = Path(sys.argv[1])
main = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = root / 'VERSION.txt'
s = main.read_text(encoding='utf-8')

# Category changes must run a real backend search, not only re-filter the small
# result set from the previous category.
old_category = 'categoryChip.setOnClickListener(v->showChoiceMenu("Job category",cats,category,(choice)->{category=choice;categoryChip.setText(choice);saveLocalSettings();saveCloudState();applyFiltersWithLoading();}));'
new_category = 'categoryChip.setOnClickListener(v->showChoiceMenu("Job category",cats,category,(choice)->{boolean changed=!choice.equals(category);category=choice;categoryChip.setText(choice);saveLocalSettings();saveCloudState();if(changed)loadJobs();else applyFiltersWithLoading();}));'
if old_category in s:
    s = s.replace(old_category, new_category, 1)
elif new_category not in s:
    raise SystemExit('category refresh target not found')

# Pay changes also go through the normal refresh path. This preserves the current
# client-side salary semantics (unknown salary is not incorrectly treated as $0)
# while ensuring the map/list refreshes from a current backend response.
old_pay = 'payBar.setMax(100);payBar.setProgress(minPay);payBar.setOnSeekBarChangeListener(new SimpleSeek(){public void onProgressChanged(SeekBar s,int p,boolean f){minPay=Math.max(0,p);payValue.setText("$"+minPay+"+");scheduleMapRender(90);} @Override public void onStopTrackingTouch(SeekBar s){saveLocalSettings();saveCloudState();applyFiltersWithLoading();}});'
new_pay = 'payBar.setMax(100);payBar.setProgress(minPay);payBar.setOnSeekBarChangeListener(new SimpleSeek(){public void onProgressChanged(SeekBar s,int p,boolean f){minPay=Math.max(0,p);payValue.setText("$"+minPay+"+");scheduleMapRender(90);} @Override public void onStopTrackingTouch(SeekBar s){saveLocalSettings();saveCloudState();refreshForRangeChange();}});'
if old_pay in s:
    s = s.replace(old_pay, new_pay, 1)
elif new_pay not in s:
    raise SystemExit('pay refresh target not found')

# Convert the user-facing category into a provider-friendly keyword. The backend
# already supports the `what` parameter and includes it in its search-cache key, so
# changing job type now requests a different provider search instead of filtering
# only whatever happened to be returned for All jobs.
if 'private String backendCategoryQuery()' not in s:
    marker = '    private String backendSourceParam(){\n'
    helper = '''    private String backendCategoryQuery(){
        if(category==null)return "";
        switch(category){
            case "Retail & Sales": return "retail";
            case "Warehouse & Logistics": return "warehouse";
            case "Food & Hospitality": return "restaurant";
            case "Construction & Skilled Trades": return "construction";
            case "Office & Administration": return "administrative";
            case "Customer Service": return "customer service";
            case "Healthcare": return "healthcare";
            case "Transportation & Delivery": return "driver";
            case "Security & Public Safety": return "security";
            case "Technology & Engineering": return "technology";
            case "Government": return "government";
            case "Education": return "education";
            case "Finance & Accounting": return "accounting";
            case "Manufacturing": return "manufacturing";
            case "Cleaning & Facilities": return "janitorial";
            default: return "";
        }
    }

'''
    if marker not in s:
        raise SystemExit('backendSourceParam insertion point not found')
    s = s.replace(marker, helper + marker, 1)

old_request = '''        StringBuilder url=new StringBuilder(endpoint)
            .append("?where=").append(URLEncoder.encode(normalizeBackendWhere(where),"UTF-8"))
            .append("&radius=").append(maxDistanceMiles)
            .append("&source=").append(URLEncoder.encode(backendSourceParam(),"UTF-8"));
'''
new_request = '''        StringBuilder url=new StringBuilder(endpoint)
            .append("?where=").append(URLEncoder.encode(normalizeBackendWhere(where),"UTF-8"))
            .append("&radius=").append(maxDistanceMiles)
            .append("&source=").append(URLEncoder.encode(backendSourceParam(),"UTF-8"));
        String categoryQuery=backendCategoryQuery();
        if(!categoryQuery.isEmpty())url.append("&what=").append(URLEncoder.encode(categoryQuery,"UTF-8"));
'''
if old_request in s:
    s = s.replace(old_request, new_request, 1)
elif 'String categoryQuery=backendCategoryQuery();' not in s:
    raise SystemExit('job request URL target not found')

main.write_text(s, encoding='utf-8')
if version.exists():
    version.write_text('9.4.70\n', encoding='utf-8')
print('Applied JobBubble V9.4.70 filter reload and category-search fix')
