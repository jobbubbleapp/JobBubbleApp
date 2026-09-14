#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v972_cluster_split_animation.py <project_dir>')

root = Path(sys.argv[1])
main = root / 'app/src/main/java/com/jobbubble/app/MainActivity.java'
version = root / 'VERSION.txt'
s = main.read_text(encoding='utf-8')

# Step 4: clusters should start separating earlier as the user zooms in. Smaller
# screen-distance thresholds mean jobs stop being treated as one pile sooner.
old_thresholds = '''    private int jobPileThresholdDp(float zoom){
        // V9.4.29: separate noticeably sooner. These values are intentionally smaller than
        // V9.4.28 so street-level clusters break apart before the map becomes extremely close.
        if(zoom<11.5f)return 158;
        if(zoom<13.5f)return 136;
        if(zoom<14.8f)return 112;
        if(zoom<15.8f)return 88;
        if(zoom<16.8f)return 66;
        if(zoom<17.8f)return 48;
        if(zoom<18.8f)return 34;
        if(zoom<19.7f)return 25;
        return 18;
    }
'''
new_thresholds = '''    private int jobPileThresholdDp(float zoom){
        // V9.4.72: begin separating earlier so nearby jobs become readable before the
        // user reaches extreme street-level zoom. Thresholds taper smoothly to avoid
        // a sudden cluster explosion at one zoom boundary.
        if(zoom<11.5f)return 150;
        if(zoom<13.5f)return 126;
        if(zoom<14.8f)return 98;
        if(zoom<15.8f)return 72;
        if(zoom<16.8f)return 52;
        if(zoom<17.8f)return 38;
        if(zoom<18.8f)return 28;
        if(zoom<19.7f)return 20;
        return 14;
    }
'''
if old_thresholds in s:
    s = s.replace(old_thresholds, new_thresholds, 1)
elif new_thresholds not in s:
    raise SystemExit('cluster threshold target not found')

# Exact/same-coordinate jobs cannot naturally separate by map projection. Start the
# progressive fan-out one full zoom level sooner.
old_exact = 'if(zoom>=17.2f && pile.size()<=5 && pileMaxSeparationMeters(pile)<=45.0){'
new_exact = 'if(zoom>=16.2f && pile.size()<=5 && pileMaxSeparationMeters(pile)<=45.0){'
if old_exact in s:
    s = s.replace(old_exact, new_exact, 1)
elif new_exact not in s:
    raise SystemExit('same-location pile threshold target not found')

# When one old pile becomes two smaller piles, animate the new pile marker outward
# from the old shared center instead of letting it pop into place. The existing
# splitAnimationStarts map already records each member's previous pile center.
old_cluster_marker = '''            LatLng center=pileRepresentativePoint(pile);
            Marker m=googleMap.addMarker(new MarkerOptions()
                .position(center)
                .icon(BitmapDescriptorFactory.fromBitmap(makeJobPileBitmap(pile)))
                .anchor(0.50f,0.73f)
                .zIndex(7f));
            if(m!=null){
                m.setTag(new ClusterTag(new ArrayList<>(pile),center));
                jobMarkers.add(m);
            }
'''
new_cluster_marker = '''            LatLng center=pileRepresentativePoint(pile);
            LatLng clusterStart=clusterSplitAnimationStart(pile,center);
            boolean animateCluster=clusterStart!=null;
            Marker m=googleMap.addMarker(new MarkerOptions()
                .position(animateCluster?clusterStart:center)
                .icon(BitmapDescriptorFactory.fromBitmap(makeJobPileBitmap(pile)))
                .anchor(0.50f,0.73f)
                .zIndex(7f));
            if(m!=null){
                m.setTag(new ClusterTag(new ArrayList<>(pile),center));
                jobMarkers.add(m);
                if(animateCluster)animateMarkerTo(m,clusterStart,center,pile.get(0)%5);
            }
'''
if old_cluster_marker in s:
    s = s.replace(old_cluster_marker, new_cluster_marker, 1)
elif 'clusterSplitAnimationStart(pile,center)' not in s:
    raise SystemExit('cluster marker animation target not found')

# Find a previous common pile center for any member of the new cluster. Require a
# meaningful movement so ordinary redraws do not animate unnecessarily.
if 'private LatLng clusterSplitAnimationStart(' not in s:
    marker = '    private void renderSingleJobMarker(int index,LatLng position,float zoom){\n'
    helper = '''    private LatLng clusterSplitAnimationStart(ArrayList<Integer> pile,LatLng target){
        if(pile==null||target==null)return null;
        for(Integer idx:pile){
            if(idx==null)continue;
            LatLng start=splitAnimationStarts.get(idx);
            if(start!=null && distanceMiles(start.latitude,start.longitude,target.latitude,target.longitude)>0.0008)return start;
        }
        return null;
    }

'''
    if marker not in s:
        raise SystemExit('cluster animation helper insertion point not found')
    s = s.replace(marker, helper + marker, 1)

# Same-coordinate fan-out now begins with two bubbles, then progressively reveals
# more as zoom increases. This keeps large visual cards readable while still showing
# obvious movement earlier.
old_reveal = 'final int reveal=zoom>=18.8f?Math.min(5,pile.size()):zoom>=17.9f?Math.min(4,pile.size()):Math.min(3,pile.size());\n        final float radiusDp=zoom>=18.8f?196f:zoom>=17.9f?172f:148f;'
new_reveal = 'final int reveal=zoom>=18.8f?Math.min(5,pile.size()):zoom>=17.6f?Math.min(4,pile.size()):zoom>=16.8f?Math.min(3,pile.size()):Math.min(2,pile.size());\n        final float radiusDp=zoom>=18.8f?196f:zoom>=17.6f?172f:zoom>=16.8f?148f:126f;'
if old_reveal in s:
    s = s.replace(old_reveal, new_reveal, 1)
elif new_reveal not in s:
    raise SystemExit('progressive fan-out target not found')

# Keep the already-correct Step 4 rule: clusters larger than five open the job list
# instead of becoming an unreadable bubble explosion.
if 'if(pile.jobIndexes.size()>5){' not in s:
    raise SystemExit('large-cluster list behavior missing')

main.write_text(s, encoding='utf-8')
if version.exists():
    version.write_text('9.4.72\n', encoding='utf-8')
print('Applied JobBubble V9.4.72 earlier animated cluster separation')
