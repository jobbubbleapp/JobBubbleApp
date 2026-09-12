#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v951_location_fetch_fix.py <project_dir>')

project = Path(sys.argv[1])
main = project / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = project / 'VERSION.txt'
s = main.read_text(encoding='utf-8')

old = '''    @SuppressLint("MissingPermission") private void enableLocation(){
        locationClient.getLastLocation().addOnSuccessListener(loc->{ enableGoogleMyLocation(); if(loc!=null){userLat=loc.getLatitude();userLon=loc.getLongitude();haveLocation=true;centerOnUser();loadJobs();} else {jobs.clear();applyFilters();status.setText("Location unavailable — live jobs not loaded");}});
    }
'''
new = '''    @SuppressLint("MissingPermission") private void enableLocation(){
        enableGoogleMyLocation();
        // getLastLocation() is only a cache lookup and is allowed to return null on a fresh
        // install/device.  Falling straight to an empty map made live providers (including
        // The Muse) look broken even though the backend was healthy.  Use the cached fix when
        // available, otherwise explicitly request a current fused location.
        locationClient.getLastLocation()
            .addOnSuccessListener(loc->{
                if(loc!=null){
                    useResolvedLocation(loc);
                    return;
                }
                status.setText("Finding your current location…");
                com.google.android.gms.tasks.CancellationTokenSource cts=new com.google.android.gms.tasks.CancellationTokenSource();
                locationClient.getCurrentLocation(com.google.android.gms.location.Priority.PRIORITY_BALANCED_POWER_ACCURACY,cts.getToken())
                    .addOnSuccessListener(current->{
                        if(current!=null)useResolvedLocation(current);
                        else showLocationUnavailable();
                    })
                    .addOnFailureListener(e->{
                        android.util.Log.w("JobBubbleMuse","Current location request failed",e);
                        showLocationUnavailable();
                    });
            })
            .addOnFailureListener(e->{
                android.util.Log.w("JobBubbleMuse","Cached location lookup failed",e);
                status.setText("Finding your current location…");
                com.google.android.gms.tasks.CancellationTokenSource cts=new com.google.android.gms.tasks.CancellationTokenSource();
                locationClient.getCurrentLocation(com.google.android.gms.location.Priority.PRIORITY_BALANCED_POWER_ACCURACY,cts.getToken())
                    .addOnSuccessListener(current->{if(current!=null)useResolvedLocation(current);else showLocationUnavailable();})
                    .addOnFailureListener(currentError->{
                        android.util.Log.w("JobBubbleMuse","Current location fallback failed",currentError);
                        showLocationUnavailable();
                    });
            });
    }

    private void useResolvedLocation(android.location.Location loc){
        userLat=loc.getLatitude();
        userLon=loc.getLongitude();
        haveLocation=true;
        android.util.Log.d("JobBubbleMuse","location ready lat="+userLat+" lon="+userLon);
        centerOnUser();
        loadJobs();
    }

    private void showLocationUnavailable(){
        jobs.clear();
        applyFilters();
        status.setText("Location unavailable — choose a search location to load live jobs");
    }
'''

if old in s:
    s = s.replace(old, new, 1)
elif 'private void useResolvedLocation(android.location.Location loc)' not in s:
    raise SystemExit('enableLocation target not found')

# Add compact network diagnostics while Muse runtime verification is active. These contain
# no credentials and make a transport/JSON problem visible instead of looking like an empty map.
needle = '    private JSONObject fetchJobJson(String requestUrl)throws Exception{\n        HttpURLConnection c=(HttpURLConnection)new URL(requestUrl).openConnection();'
replacement = '    private JSONObject fetchJobJson(String requestUrl)throws Exception{\n        android.util.Log.d("JobBubbleMuse","job request="+requestUrl);\n        HttpURLConnection c=(HttpURLConnection)new URL(requestUrl).openConnection();'
if needle in s and '"job request="+requestUrl' not in s:
    s = s.replace(needle, replacement, 1)

needle2 = '        if(code<200||code>=300)throw new IOException("Job API HTTP "+code+": "+body);\n        return new JSONObject(body);'
replacement2 = '        if(code<200||code>=300)throw new IOException("Job API HTTP "+code+": "+body);\n        android.util.Log.d("JobBubbleMuse","job response HTTP="+code+" bytes="+body.length());\n        return new JSONObject(body);'
if needle2 in s and '"job response HTTP="+code' not in s:
    s = s.replace(needle2, replacement2, 1)

needle3 = '        if(arr!=null)for(int i=0;i<arr.length();i++)fresh.add(Job.from(arr.getJSONObject(i)));\n        return new JobResponse(fresh,parsedOriginLat,parsedOriginLon,validCoordinate(parsedOriginLat,parsedOriginLon));'
replacement3 = '        if(arr!=null)for(int i=0;i<arr.length();i++)fresh.add(Job.from(arr.getJSONObject(i)));\n        android.util.Log.d("JobBubbleMuse","parsed jobs="+fresh.size());\n        return new JobResponse(fresh,parsedOriginLat,parsedOriginLon,validCoordinate(parsedOriginLat,parsedOriginLon));'
if needle3 in s and '"parsed jobs="+fresh.size()' not in s:
    s = s.replace(needle3, replacement3, 1)

main.write_text(s, encoding='utf-8')
if version.exists():
    version.write_text('9.4.51\n', encoding='utf-8')
print('Applied JobBubble V9.4.51 current-location fallback and Muse diagnostics')
