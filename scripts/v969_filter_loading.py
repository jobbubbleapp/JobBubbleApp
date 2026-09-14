#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v969_filter_loading.py <project_dir>')

root = Path(sys.argv[1])
main = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = root / 'VERSION.txt'
s = main.read_text(encoding='utf-8')

replacements = {
    'categoryChip.setOnClickListener(v->showChoiceMenu("Job category",cats,category,(choice)->{category=choice;categoryChip.setText(choice);saveLocalSettings();saveCloudState();applyFilters();}));':
    'categoryChip.setOnClickListener(v->showChoiceMenu("Job category",cats,category,(choice)->{category=choice;categoryChip.setText(choice);saveLocalSettings();saveCloudState();applyFiltersWithLoading();}));',

    'sourceChip.setOnClickListener(v->showChoiceMenu("Job source",src,source,(choice)->{boolean changed=!choice.equals(source);source=choice;sourceChip.setText(choice);saveLocalSettings();saveCloudState();if(changed)loadJobs();else applyFilters();}));':
    'sourceChip.setOnClickListener(v->showChoiceMenu("Job source",src,source,(choice)->{boolean changed=!choice.equals(source);source=choice;sourceChip.setText(choice);saveLocalSettings();saveCloudState();if(changed)loadJobs();else applyFiltersWithLoading();}));',

    'payBar.setMax(100);payBar.setProgress(minPay);payBar.setOnSeekBarChangeListener(new SimpleSeek(){public void onProgressChanged(SeekBar s,int p,boolean f){minPay=Math.max(0,p);payValue.setText("$"+minPay+"+");scheduleMapRender(90);} @Override public void onStopTrackingTouch(SeekBar s){saveLocalSettings();saveCloudState();scheduleMapRender(0);}});':
    'payBar.setMax(100);payBar.setProgress(minPay);payBar.setOnSeekBarChangeListener(new SimpleSeek(){public void onProgressChanged(SeekBar s,int p,boolean f){minPay=Math.max(0,p);payValue.setText("$"+minPay+"+");scheduleMapRender(90);} @Override public void onStopTrackingTouch(SeekBar s){saveLocalSettings();saveCloudState();applyFiltersWithLoading();}});',

    'if(!hadJobs)showJobsLoading();':
    'showJobsLoading();'
}

for old, new in replacements.items():
    if old in s:
        s = s.replace(old, new, 1)
    elif new not in s:
        raise SystemExit('filter loading patch target not found: ' + old[:90])

old_refresh = '''    private void refreshForRangeChange(){
        String savedWhere=profileLocation();
        if(!jobApiUrl().contains("YOUR_BACKEND_URL") && (haveLocation || !savedWhere.isEmpty())){
            loadJobs();
        }else{
            applyFilters();
        }
    }
'''
new_refresh = '''    private void applyFiltersWithLoading(){
        showJobsLoading();
        final View root=findViewById(android.R.id.content);
        final Runnable work=()->{
            try{
                applyFilters();
            }finally{
                hideJobsLoading();
            }
        };
        if(root!=null)root.post(work);else runOnUiThread(work);
    }

    private void refreshForRangeChange(){
        String savedWhere=profileLocation();
        if(!jobApiUrl().contains("YOUR_BACKEND_URL") && (haveLocation || !savedWhere.isEmpty())){
            loadJobs();
        }else{
            applyFiltersWithLoading();
        }
    }
'''
if old_refresh in s:
    s = s.replace(old_refresh, new_refresh, 1)
elif 'private void applyFiltersWithLoading()' not in s:
    raise SystemExit('refreshForRangeChange target not found')

main.write_text(s, encoding='utf-8')
if version.exists():
    version.write_text('9.4.69\n', encoding='utf-8')
print('Applied JobBubble V9.4.69 filter-change loading screen behavior')
