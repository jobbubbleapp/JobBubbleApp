package com.jobbubble.app;

import android.Manifest;
import android.animation.ValueAnimator;
import android.annotation.SuppressLint;
import android.content.Intent;
import android.location.Address;
import android.location.Geocoder;
import android.location.Location;
import android.app.Dialog;
import android.graphics.drawable.ColorDrawable;
import android.text.SpannableString;
import android.text.InputType;
import android.text.Spanned;
import android.text.style.ForegroundColorSpan;
import android.content.pm.PackageManager;
import android.graphics.Typeface;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.Window;
import android.view.WindowManager;
import android.view.inputmethod.InputMethodManager;
import com.google.android.material.bottomsheet.BottomSheetDialog;
import android.net.Uri;
import android.os.Bundle;
import android.os.Build;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import com.google.android.gms.maps.CameraUpdateFactory;
import com.google.android.gms.maps.GoogleMap;
import com.google.android.gms.maps.OnMapReadyCallback;
import com.google.android.gms.maps.SupportMapFragment;
import com.google.android.gms.maps.model.BitmapDescriptorFactory;
import com.google.android.gms.maps.model.LatLng;
import com.google.android.gms.maps.model.MapStyleOptions;
import com.google.android.gms.maps.model.Marker;
import com.google.android.gms.maps.model.MarkerOptions;
import com.google.android.gms.maps.model.Polyline;
import com.google.android.gms.maps.model.PolylineOptions;
import com.google.android.gms.maps.model.Polygon;
import com.google.android.gms.maps.model.PolygonOptions;
import com.google.android.gms.maps.model.Tile;
import com.google.android.gms.maps.model.TileOverlay;
import com.google.android.gms.maps.model.TileOverlayOptions;
import com.google.android.gms.maps.model.TileProvider;
import com.google.android.gms.maps.model.LatLngBounds;
import android.view.View;
import android.view.MotionEvent;
import android.view.ViewGroup;
import android.os.Handler;
import android.os.Looper;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffXfermode;
import android.widget.FrameLayout;
import android.widget.*;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;
import com.google.android.gms.location.FusedLocationProviderClient;
import com.google.android.gms.location.LocationServices;
import com.google.android.gms.auth.api.signin.GoogleSignIn;
import com.google.android.gms.auth.api.signin.GoogleSignInAccount;
import com.google.android.gms.auth.api.signin.GoogleSignInClient;
import com.google.android.gms.auth.api.signin.GoogleSignInOptions;
import com.google.android.gms.common.api.ApiException;
import com.google.firebase.auth.AuthCredential;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.auth.GoogleAuthProvider;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.SetOptions;
import com.google.android.gms.maps.model.Circle;
import com.google.android.gms.maps.model.CircleOptions;
import org.json.*;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {
    private static final int LOCATION_REQUEST = 42;
    private static final int PROFILE_GALLERY_REQUEST = 201;
    private static final int PROFILE_CAMERA_REQUEST = 202;
    private static final int GOOGLE_SIGN_IN_REQUEST = 203;
    private FirebaseAuth firebaseAuth;
    private FirebaseFirestore firestore;
    private GoogleSignInClient googleSignInClient;
    private final ArrayList<Circle> approxCircles = new ArrayList<>();
    private String jobApiUrl(){ return getString(R.string.job_api_url).trim(); }
    private FusedLocationProviderClient locationClient;
    private GoogleMap googleMap;
    private SupportMapFragment mapFragment;
    private final ArrayList<Marker> jobMarkers = new ArrayList<>();
    private final ArrayList<Polyline> pileSpokes = new ArrayList<>();
    // V9.4.37: tile-level country curtains render ABOVE Google base-map labels,
    // so non-U.S. roads/cities/province labels are truly hidden instead of bleeding through.
    private TileOverlay foreignCountryTileOverlay;
    private final ArrayList<Marker> foreignCountryLabels = new ArrayList<>();
    // V9.4.29: remembers where a job was while it was inside a pile so the newly
    // separated bubble can visibly glide out from the old pile instead of popping in.
    private final Map<Integer,LatLng> splitAnimationStarts = new HashMap<>();
    private double userLat = 47.979, userLon = -122.202;
    private boolean haveLocation = false, mapReady = false;
    private final ArrayList<Job> jobs = new ArrayList<>();
    private final ArrayList<Job> filtered = new ArrayList<>();

    // V9.4.25: adaptive pile spreading + reliable hold/slide map location gesture.
    // Nearby jobs stay piled at wide zooms, then progressively separate at their true coordinates as zoom increases.
    private static final class ClusterTag {
        final ArrayList<Integer> jobIndexes;
        final LatLng center;
        ClusterTag(ArrayList<Integer> jobIndexes, LatLng center){ this.jobIndexes=jobIndexes; this.center=center; }
    }
    private Spinner categorySpinner, sourceSpinner;
    private TextView categoryChip, sourceChip, mapRegionBadge;
    private SeekBar distanceBar, payBar;
    private TextView distanceValue, payValue, resultCount, status;
    private int maxDistanceMiles = 25, minPay = 15;
    private boolean extendedDistance = false;
    // V9.4.35: optional precision filter. "Precise" includes exact addresses and
    // high-confidence likely workplaces; area-only estimates stay separate.
    private boolean preciseLocationsOnly = false;
    private String category = "All jobs", source = "All sources";
    private String mapTheme = "light";
    // V9.4.40: three U.S.-only map regions. The default map is the Lower 48;
    // Alaska and Hawaii can be selected independently from Settings.
    private String mapRegion = "lower48";
    private Dialog jobsLoadingDialog;
    private final Map<String,Bitmap> companyLogoCache = Collections.synchronizedMap(new HashMap<>());
    private final Set<String> companyLogoLoading = Collections.synchronizedSet(new HashSet<>());
    private final java.util.concurrent.ExecutorService logoExecutor = Executors.newFixedThreadPool(4);
    private final java.util.concurrent.ExecutorService jobExecutor = Executors.newFixedThreadPool(2);
    private volatile int jobLoadGeneration = 0;
    private final Handler mapHoldHandler = new Handler(Looper.getMainLooper());
    private MapHoldOverlay mapHoldOverlay;
    private boolean mapHoldActive = false;
    private float mapHoldX, mapHoldY;
    private LatLng mapHoldLatLng;
    private final Map<String,Bitmap> markerBitmapCache = Collections.synchronizedMap(new LinkedHashMap<String,Bitmap>(160,0.75f,true){
        @Override protected boolean removeEldestEntry(Map.Entry<String,Bitmap> e){ return size()>180; }
    });
    // V9.4.38 performance: cache rendered country-curtain PNG tiles so pan/zoom does
    // not repeatedly allocate a 256x256 bitmap and recompress identical tiles.
    private final Map<String,byte[]> foreignTileCache = Collections.synchronizedMap(new LinkedHashMap<String,byte[]>(192,0.75f,true){
        @Override protected boolean removeEldestEntry(Map.Entry<String,byte[]> e){ return size()>192; }
    });
    // Coalesce bursts of map rebuilds (logo arrivals / slider drags) into one render.
    private final Handler renderHandler = new Handler(Looper.getMainLooper());
    private final Runnable deferredMapRender = this::applyFilters;
    private void scheduleMapRender(long delayMs){
        renderHandler.removeCallbacks(deferredMapRender);
        renderHandler.postDelayed(deferredMapRender,Math.max(0,delayMs));
    }

    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        enableImmersiveFullscreen();
        firebaseAuth=FirebaseAuth.getInstance();
        firestore=FirebaseFirestore.getInstance();
        GoogleSignInOptions gso=new GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN).requestIdToken(getString(R.string.default_web_client_id)).requestEmail().build();
        googleSignInClient=GoogleSignIn.getClient(this,gso);
        int seenVersion=getPreferences(MODE_PRIVATE).getInt("seenVersion",0);
        if(firebaseAuth.getCurrentUser()!=null){ getPreferences(MODE_PRIVATE).edit().putBoolean("onboarded",true).putBoolean("guestMode",false).putInt("seenVersion",10).apply(); startMap(); }
        else if (!getPreferences(MODE_PRIVATE).getBoolean("onboarded", false) || seenVersion<10) showWelcome(); else startMap();
    }

    // V9.0.9: use AndroidX's compatibility controller for immersive fullscreen.
    // This avoids device/API-specific startup crashes while still hiding both system bars.
    private void enableImmersiveFullscreen(){
        try {
            Window window=getWindow();
            View decor=window.getDecorView();
            WindowCompat.setDecorFitsSystemWindows(window, false);
            WindowInsetsControllerCompat controller=WindowCompat.getInsetsController(window, decor);
            if(controller!=null){
                controller.hide(WindowInsetsCompat.Type.statusBars() | WindowInsetsCompat.Type.navigationBars());
                controller.setSystemBarsBehavior(WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
            }
        } catch (Throwable ignored) {
            // Last-resort legacy fallback. Fullscreen should never be able to crash app launch.
            try {
                getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                    View.SYSTEM_UI_FLAG_FULLSCREEN |
                    View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                    View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                    View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                    View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                );
            } catch (Throwable ignoredAgain) { }
        }
    }

    @Override public void onWindowFocusChanged(boolean hasFocus){
        super.onWindowFocusChanged(hasFocus);
        if(hasFocus) enableImmersiveFullscreen();
    }

    @Override protected void onResume(){
        super.onResume();
        enableImmersiveFullscreen();
    }

    private void showWelcome() {
        setContentView(R.layout.activity_welcome);
        findViewById(R.id.createAccountButton).setOnClickListener(v -> showAuth(true));
        findViewById(R.id.loginButton).setOnClickListener(v -> showAuth(false));
        findViewById(R.id.googleWelcomeButton).setOnClickListener(v -> startActivityForResult(googleSignInClient.getSignInIntent(),GOOGLE_SIGN_IN_REQUEST));
        findViewById(R.id.guestButton).setOnClickListener(v -> finishOnboarding(true));
    }
    private void showAuth(boolean create) {
        setContentView(R.layout.activity_auth);
        TextView title=findViewById(R.id.authTitle); EditText name=findViewById(R.id.nameInput); EditText email=findViewById(R.id.emailInput); EditText password=findViewById(R.id.passwordInput); Button action=findViewById(R.id.authAction);
        title.setText(create?"Create Account":"Log In"); name.setVisibility(create?View.VISIBLE:View.GONE); action.setText(create?"Create Account":"Log In");
        action.setOnClickListener(v -> { String e=email.getText().toString().trim(), pw=password.getText().toString(); if(e.isEmpty()||pw.length()<6){Toast.makeText(this,"Enter a valid email and a password with at least 6 characters.",Toast.LENGTH_LONG).show();return;} action.setEnabled(false); if(create) firebaseAuth.createUserWithEmailAndPassword(e,pw).addOnCompleteListener(t->{action.setEnabled(true);if(t.isSuccessful()){String n=name.getText().toString().trim();if(!n.isEmpty())getSharedPreferences("profile",MODE_PRIVATE).edit().putString("name",n).apply();finishOnboarding(false);saveCloudState();}else Toast.makeText(this,authError(t.getException()),Toast.LENGTH_LONG).show();}); else firebaseAuth.signInWithEmailAndPassword(e,pw).addOnCompleteListener(t->{action.setEnabled(true);if(t.isSuccessful())finishOnboarding(false);else Toast.makeText(this,authError(t.getException()),Toast.LENGTH_LONG).show();}); });
        findViewById(R.id.authBack).setOnClickListener(v -> showWelcome());
        findViewById(R.id.googleButton).setOnClickListener(v -> startActivityForResult(googleSignInClient.getSignInIntent(),GOOGLE_SIGN_IN_REQUEST));
    }
    private String authError(Exception e){return e==null?"Sign-in failed. Please try again.":e.getLocalizedMessage();}
    private void firebaseAuthWithGoogle(GoogleSignInAccount account){AuthCredential credential=GoogleAuthProvider.getCredential(account.getIdToken(),null);firebaseAuth.signInWithCredential(credential).addOnCompleteListener(t->{if(t.isSuccessful()){FirebaseUser u=firebaseAuth.getCurrentUser();if(u!=null&&u.getDisplayName()!=null&&!u.getDisplayName().trim().isEmpty())getSharedPreferences("profile",MODE_PRIVATE).edit().putString("name",u.getDisplayName()).apply();finishOnboarding(false);saveCloudState();}else Toast.makeText(this,authError(t.getException()),Toast.LENGTH_LONG).show();});}

    private void finishOnboarding(boolean guest) {
        getPreferences(MODE_PRIVATE).edit().putBoolean("onboarded",true).putBoolean("guestMode",guest).putInt("seenVersion",10).apply();
        if(guest) Toast.makeText(this,"Browsing as guest",Toast.LENGTH_SHORT).show(); startMap();
    }

    private void startMap() {
        setContentView(R.layout.activity_main);
        locationClient=LocationServices.getFusedLocationProviderClient(this);
        android.content.SharedPreferences mapPrefs=getSharedPreferences("settings",MODE_PRIVATE);
        if(!mapPrefs.getBoolean("v816LightDefault",false)){mapPrefs.edit().putString("mapTheme","light").putBoolean("v816LightDefault",true).apply();}
        mapTheme=mapPrefs.getString("mapTheme","light");
        mapRegion=mapPrefs.getString("mapRegion","lower48");
        extendedDistance=mapPrefs.getBoolean("extendedDistance",false);
        preciseLocationsOnly=mapPrefs.getBoolean("preciseLocationsOnly",false);
        maxDistanceMiles=mapPrefs.getInt("maxDistanceMiles",25);
        minPay=mapPrefs.getInt("minPay",15);
        category=mapPrefs.getString("category","All jobs");
        source=mapPrefs.getString("source","All sources");
        bindFilters();
        applyUiTheme();

        mapFragment=(SupportMapFragment)getSupportFragmentManager().findFragmentById(R.id.googleMap);
        if(mapFragment!=null){
            mapFragment.getMapAsync(map -> {
                googleMap=map;
                mapReady=true;
                configureGoogleMap();
                applyMapTheme();
                centerOnUser();
                applyFilters();
            });
        } else {
            Toast.makeText(this,"Google Maps could not start.",Toast.LENGTH_LONG).show();
        }
        if(!profileLocation().isEmpty()){
            if(hasSavedProfileCoordinates()){
                userLat=profileLocationLat();userLon=profileLocationLon();haveLocation=true;
                centerOnUser();
            }
            loadJobs();
        } else requestLocation();
        if(firebaseAuth.getCurrentUser()!=null) syncCloudState();
    }

    @SuppressLint("MissingPermission")
    private void configureGoogleMap(){
        if(googleMap==null)return;
        googleMap.getUiSettings().setZoomControlsEnabled(false);
        googleMap.getUiSettings().setMapToolbarEnabled(false);
        googleMap.getUiSettings().setCompassEnabled(false);
        googleMap.getUiSettings().setMyLocationButtonEnabled(false);
        googleMap.getUiSettings().setIndoorLevelPickerEnabled(false);
        googleMap.setPadding(0,dp(126),0,dp(96));
        // V9.4.40: the map is intentionally split into three U.S.-only views.
        // This avoids loading/rendering an entire world map just to reach Alaska/Hawaii.
        applyMapRegionBounds(false);
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED || ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED){
            try{googleMap.setMyLocationEnabled(true);}catch(Exception ignored){}
        }
        // V9.4.24: do no marker rebuilding/focus work during camera movement.
        // Google Maps moves the existing marker textures itself; we cluster once when motion stops.
        googleMap.setOnCameraMoveListener(null);
        googleMap.setOnCameraIdleListener(() -> { applyFilters(); updateZoomFocusTransparency(); updateForeignCountryLabels(); });
        installMapHoldGesture();
        googleMap.setOnMarkerClickListener(marker -> {
            Object tag=marker.getTag();
            if(tag instanceof Integer){
                int i=(Integer)tag;
                if(i>=0 && i<filtered.size()) showJob(filtered.get(i));
                return true;
            }
            if(tag instanceof ClusterTag){
                ClusterTag pile=(ClusterTag)tag;
                float zoom=googleMap.getCameraPosition().zoom;
                // Large piles become much easier to understand as a scrollable side list once
                // the user is close enough to inspect the area. Smaller piles still zoom in.
                if(pile.jobIndexes.size()>5){
                    showClusterSideList(pile);
                }else{
                    float nextZoom=Math.min(20.5f,Math.max(zoom+2.0f,15.8f));
                    googleMap.animateCamera(CameraUpdateFactory.newLatLngZoom(pile.center,nextZoom));
                }
                return true;
            }
            return false;
        });
    }

    private void installMapHoldGesture(){
        if(mapFragment==null||mapFragment.getView()==null)return;
        final View mapView=mapFragment.getView();
        if(!(mapView.getParent() instanceof ViewGroup))return;
        final ViewGroup parent=(ViewGroup)mapView.getParent();

        // V9.4.25: the old listener sat on the SupportMapFragment root, but Google Maps' inner
        // renderer consumes the gesture stream. A transparent sibling overlay now receives the
        // complete DOWN/MOVE/UP sequence and forwards ordinary gestures to the map underneath.
        if(mapHoldOverlay!=null){
            try{((ViewGroup)mapHoldOverlay.getParent()).removeView(mapHoldOverlay);}catch(Exception ignored){}
        }
        mapHoldOverlay=new MapHoldOverlay(this,mapView);
        int mapIndex=parent.indexOfChild(mapView);
        parent.addView(mapHoldOverlay,Math.max(0,mapIndex+1),new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.MATCH_PARENT));
        mapHoldOverlay.setElevation(0f);
    }

    private void setPinnedSearchLocation(LatLng point){
        if(point==null)return;
        if(!isInsideSelectedMapRegion(point)){
            Toast.makeText(this,"Choose a location inside the selected U.S. map.",Toast.LENGTH_SHORT).show();
            return;
        }
        userLat=point.latitude; userLon=point.longitude; haveLocation=true;
        // Persist the exact map coordinate immediately so the camera and distance math use
        // the point the user actually selected. Resolve a human-readable city/state label in
        // the background for provider searches; never send the literal text "Pinned map location"
        // to the backend because providers may geocode that to an unrelated city.
        profilePrefs().edit()
            .putLong("location_lat_bits",Double.doubleToRawLongBits(userLat))
            .putLong("location_lon_bits",Double.doubleToRawLongBits(userLon))
            .putBoolean("map_location_pinned",true)
            .apply();
        if(mapReady&&googleMap!=null){
            googleMap.animateCamera(CameraUpdateFactory.newLatLngZoom(point,Math.max(15.5f,googleMap.getCameraPosition().zoom)));
        }
        status.setText("Setting search location…");
        final double pinnedLat=userLat,pinnedLon=userLon;
        jobExecutor.execute(()->{
            String label=String.format(Locale.US,"%.5f,%.5f",pinnedLat,pinnedLon);
            try{
                Geocoder g=new Geocoder(MainActivity.this,Locale.US);
                List<Address> a=g.getFromLocation(pinnedLat,pinnedLon,1);
                if(a!=null&&!a.isEmpty()){
                    Address x=a.get(0);
                    String city=x.getLocality();
                    if(city==null||city.trim().isEmpty())city=x.getSubAdminArea();
                    String state=x.getAdminArea();
                    if(city!=null&&!city.trim().isEmpty())label=(state==null||state.trim().isEmpty())?city:city+", "+state;
                }
            }catch(Exception ignored){}
            final String resolvedLabel=label;
            runOnUiThread(()->{
                // Ignore a stale reverse-geocode result if the user has already pinned elsewhere.
                if(Math.abs(userLat-pinnedLat)>0.000001||Math.abs(userLon-pinnedLon)>0.000001)return;
                profilePrefs().edit().putString("location",resolvedLabel).apply();
                saveCloudState();
                Toast.makeText(MainActivity.this,"Search location set to "+resolvedLabel,Toast.LENGTH_SHORT).show();
                loadJobs();
            });
        });
    }

    private final class MapHoldOverlay extends View{
        private final Paint ring=new Paint(Paint.ANTI_ALIAS_FLAG),fill=new Paint(Paint.ANTI_ALIAS_FLAG),text=new Paint(Paint.ANTI_ALIAS_FLAG);
        private final View mapTarget;
        private final float density;
        private float cx,cy,fx,fy,downX,downY;
        private boolean visible,selected,tracking,movedTooFar,multiTouch;
        private final Runnable activateHold;

        MapHoldOverlay(android.content.Context c,View mapTarget){
            super(c);
            this.mapTarget=mapTarget;
            density=getResources().getDisplayMetrics().density;
            activateHold=()->{
                if(!tracking||movedTooFar||multiTouch||googleMap==null)return;
                mapHoldActive=true;visible=true;selected=false;cx=downX;cy=downY;fx=downX;fy=downY;
                try{mapHoldLatLng=googleMap.getProjection().fromScreenLocation(new android.graphics.Point(Math.round(cx),Math.round(cy)));}catch(Exception e){mapHoldLatLng=null;}
                // Cancel the map's own pan/zoom recognizer once the radial gesture wins.
                try{
                    long now=android.os.SystemClock.uptimeMillis();
                    MotionEvent cancel=MotionEvent.obtain(now,now,MotionEvent.ACTION_CANCEL,cx,cy,0);
                    this.mapTarget.dispatchTouchEvent(cancel);cancel.recycle();
                }catch(Exception ignored){}
                try{performHapticFeedback(android.view.HapticFeedbackConstants.LONG_PRESS);}catch(Exception ignored){}
                invalidate();
            };
            setWillNotDraw(false);setClickable(true);setFocusable(false);
        }
        private float d(float v){return v*density;}
        private void forwardToMap(MotionEvent event){
            try{MotionEvent copy=MotionEvent.obtain(event);mapTarget.dispatchTouchEvent(copy);copy.recycle();}catch(Exception ignored){}
        }
        boolean isOnSetTarget(float x,float y){
            float tx=cx,ty=Math.max(d(68),cy-d(118));float dx=x-tx,dy=y-ty;
            return dx*dx+dy*dy<=d(58)*d(58);
        }
        private void reset(){
            mapHoldHandler.removeCallbacks(activateHold);tracking=false;movedTooFar=false;multiTouch=false;
            visible=false;selected=false;mapHoldActive=false;mapHoldLatLng=null;invalidate();
        }
        @Override public boolean onTouchEvent(MotionEvent event){
            final int action=event.getActionMasked();
            if(action==MotionEvent.ACTION_DOWN){
                reset();tracking=true;downX=event.getX();downY=event.getY();cx=downX;cy=downY;
                mapHoldX=downX;mapHoldY=downY;
                mapHoldHandler.postDelayed(activateHold,430);
                forwardToMap(event);
                return true;
            }
            if(event.getPointerCount()>1){
                multiTouch=true;mapHoldHandler.removeCallbacks(activateHold);
            }
            if(action==MotionEvent.ACTION_MOVE){
                if(mapHoldActive){
                    fx=event.getX();fy=event.getY();selected=isOnSetTarget(fx,fy);invalidate();
                    return true;
                }
                float dx=event.getX()-downX,dy=event.getY()-downY;
                if(dx*dx+dy*dy>d(16)*d(16)){
                    movedTooFar=true;mapHoldHandler.removeCallbacks(activateHold);
                }
                forwardToMap(event);
                return true;
            }
            if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_CANCEL){
                mapHoldHandler.removeCallbacks(activateHold);
                if(mapHoldActive){
                    boolean choose=action==MotionEvent.ACTION_UP&&isOnSetTarget(event.getX(),event.getY());
                    LatLng chosen=mapHoldLatLng;
                    reset();
                    if(choose&&chosen!=null)setPinnedSearchLocation(chosen);
                    return true;
                }
                forwardToMap(event);reset();return true;
            }
            if(!mapHoldActive)forwardToMap(event);
            return true;
        }
        @Override protected void onDraw(Canvas c){super.onDraw(c);if(!visible)return;
            ring.setStyle(Paint.Style.STROKE);ring.setStrokeWidth(d(3));ring.setColor(Color.argb(230,142,72,255));
            fill.setStyle(Paint.Style.FILL);fill.setColor(Color.argb(50,142,72,255));
            c.drawCircle(cx,cy,d(45),fill);c.drawCircle(cx,cy,d(45),ring);
            float tx=cx,ty=Math.max(d(68),cy-d(118));
            fill.setColor(selected?Color.argb(250,139,69,255):Color.argb(240,20,29,39));c.drawCircle(tx,ty,d(54),fill);
            ring.setColor(Color.argb(245,180,120,255));ring.setStrokeWidth(d(2));c.drawCircle(tx,ty,d(54),ring);
            text.setColor(Color.WHITE);text.setTextAlign(Paint.Align.CENTER);text.setTypeface(Typeface.DEFAULT_BOLD);text.setTextSize(d(12));
            c.drawText("Set as",tx,ty-d(3),text);c.drawText("location",tx,ty+d(13),text);
            if(selected){ring.setColor(Color.WHITE);ring.setStrokeWidth(d(4));c.drawCircle(tx,ty,d(49),ring);}
        }
    }

    @SuppressLint("MissingPermission")
    private void enableGoogleMyLocation(){
        if(googleMap==null)return;
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED || ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED){
            try{googleMap.setMyLocationEnabled(true);}catch(Exception ignored){}
        }
    }

    private Bitmap makeJobMarkerBitmap(Job j){
        boolean showApprox=shouldShowApproxLocation(j);
        String markerKey=jobKey(j)+"|"+mapTheme+"|"+(isTracked(j)?"1":"0")+"|"+(showApprox?"a":"e")+"|"+(getCompanyLogo(j.company)!=null?"L":"N");
        Bitmap cachedMarker=markerBitmapCache.get(markerKey);
        if(cachedMarker!=null&&!cachedMarker.isRecycled())return cachedMarker;
        // V9.4.16 marker layout:
        // dark unified text card ABOVE a round company-logo bubble,
        // with a compact distance badge just outside the lower-right edge.
        final int w=dp(188);
        final int h=showApprox?dp(124):dp(112);
        Bitmap bitmap=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);
        android.graphics.Canvas c=new android.graphics.Canvas(bitmap);

        final float density=getResources().getDisplayMetrics().density;
        final float bubbleCx=dp(55);
        final float bubbleCy=showApprox?dp(91):dp(79);
        final float bubbleR=dp(28);

        // Text box follows the selected map theme: light card on light map, dark card on dark map.
        float cardLeft=dp(4), cardTop=dp(1), cardRight=dp(168);
        float cardBottom=showApprox?dp(64):dp(52);
        android.graphics.Paint shadow=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        shadow.setColor(Color.argb(62,0,0,0));
        c.drawRoundRect(new android.graphics.RectF(cardLeft+dp(1),cardTop+dp(3),cardRight+dp(1),cardBottom+dp(3)),dp(14),dp(14),shadow);

        boolean lightMarkerUi=isLightUi();
        android.graphics.Paint cardPaint=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        cardPaint.setColor(Color.parseColor(lightMarkerUi?"#E9EAED":"#0A1B29"));
        c.drawRoundRect(new android.graphics.RectF(cardLeft,cardTop,cardRight,cardBottom),dp(14),dp(14),cardPaint);
        android.graphics.Paint cardStroke=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        cardStroke.setStyle(android.graphics.Paint.Style.STROKE);
        cardStroke.setStrokeWidth(density);
        cardStroke.setColor(Color.parseColor(lightMarkerUi?"#AEB4BC":"#64727D"));
        c.drawRoundRect(new android.graphics.RectF(cardLeft+.5f*density,cardTop+.5f*density,cardRight-.5f*density,cardBottom-.5f*density),dp(14),dp(14),cardStroke);

        float tx=dp(15);
        float y=dp(15);
        android.graphics.Paint text=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        text.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);

        if(showApprox){
            text.setTextSize(dp(8));
            text.setColor(Color.parseColor(lightMarkerUi?"#69737D":"#9FB5C7"));
            c.drawText("approx. location",tx,y,text);
            y+=dp(17);
        }else{
            y+=dp(4);
        }

        text.setTextSize(dp(14));
        text.setColor(Color.parseColor("#35E0A1"));
        c.drawText(markerPayText(j.pay),tx,y,text);
        y+=dp(18);

        text.setTextSize(dp(10));
        text.setColor(Color.parseColor(lightMarkerUi?"#202329":"#F7FAFC"));
        String title=shortMarkerTitle(j.title);
        c.drawText(title,tx,y,text);

        // Round bubble with a light-gray border, as requested.
        android.graphics.Paint bubbleShadow=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        bubbleShadow.setColor(Color.argb(65,0,0,0));
        c.drawCircle(bubbleCx+dp(1),bubbleCy+dp(3),bubbleR,bubbleShadow);

        android.graphics.Paint bubbleFill=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        bubbleFill.setColor(Color.parseColor(companyColor(j.company,j.category)));
        c.drawCircle(bubbleCx,bubbleCy,bubbleR,bubbleFill);

        android.graphics.Paint bubbleBorder=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        bubbleBorder.setStyle(android.graphics.Paint.Style.STROKE);
        bubbleBorder.setStrokeWidth(dp(3));
        bubbleBorder.setColor(Color.parseColor("#D5DADF"));
        c.drawCircle(bubbleCx,bubbleCy,bubbleR-(density*1.5f),bubbleBorder);

        // White inset keeps light/dark company logos readable while preserving bubble color.
        android.graphics.Paint logoDisk=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        logoDisk.setColor(Color.WHITE);
        c.drawCircle(bubbleCx,bubbleCy,dp(22),logoDisk);

        Bitmap logo=getCompanyLogo(j.company);
        if(logo!=null){
            drawLogoCentered(c,logo,bubbleCx,bubbleCy,dp(18));
        }else{
            android.graphics.Paint fallback=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            fallback.setTextAlign(android.graphics.Paint.Align.CENTER);
            fallback.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
            fallback.setTextSize(dp(Math.min(15,companyLogoTextSize(j.company))));
            fallback.setColor(Color.parseColor(companyColor(j.company,j.category)));
            String badge=companyBadge(j.company).replace("\n"," ");
            if(badge.length()>4)badge=badge.substring(0,4);
            android.graphics.Paint.FontMetrics fm=fallback.getFontMetrics();
            c.drawText(badge,bubbleCx,bubbleCy-(fm.ascent+fm.descent)/2f,fallback);
            requestCompanyLogo(j.company);
        }

        // Small distance text outside the lower-right of the round bubble.
        String distance=markerDistanceText(j);
        android.graphics.Paint distanceText=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        distanceText.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        distanceText.setTextSize(dp(8));
        distanceText.setColor(Color.parseColor(lightMarkerUi?"#333A42":"#D9E1E8"));
        float distW=distanceText.measureText(distance)+dp(12);
        float distLeft=bubbleCx+bubbleR-dp(4);
        float distTop=bubbleCy+dp(10);
        android.graphics.Paint distBg=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        distBg.setColor(Color.parseColor(lightMarkerUi?"#E9EAED":"#182A38"));
        c.drawRoundRect(new android.graphics.RectF(distLeft,distTop,distLeft+distW,distTop+dp(20)),dp(10),dp(10),distBg);
        android.graphics.Paint distStroke=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        distStroke.setStyle(android.graphics.Paint.Style.STROKE);
        distStroke.setStrokeWidth(density);
        distStroke.setColor(Color.parseColor(lightMarkerUi?"#AEB4BC":"#8996A0"));
        c.drawRoundRect(new android.graphics.RectF(distLeft+.5f*density,distTop+.5f*density,distLeft+distW-.5f*density,distTop+dp(20)-.5f*density),dp(10),dp(10),distStroke);
        android.graphics.Paint.FontMetrics dfm=distanceText.getFontMetrics();
        float db=distTop+dp(10)-(dfm.ascent+dfm.descent)/2f;
        c.drawText(distance,distLeft+dp(6),db,distanceText);

        markerBitmapCache.put(markerKey,bitmap);
        return bitmap;
    }

    private void drawLogoCentered(android.graphics.Canvas canvas,Bitmap logo,float cx,float cy,float maxRadius){
        if(logo==null||logo.getWidth()<=0||logo.getHeight()<=0)return;
        float maxSize=maxRadius*2f;
        float scale=Math.min(maxSize/logo.getWidth(),maxSize/logo.getHeight());
        float drawW=logo.getWidth()*scale;
        float drawH=logo.getHeight()*scale;
        android.graphics.RectF dest=new android.graphics.RectF(cx-drawW/2f,cy-drawH/2f,cx+drawW/2f,cy+drawH/2f);
        android.graphics.Paint paint=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG|android.graphics.Paint.FILTER_BITMAP_FLAG);
        canvas.drawBitmap(logo,null,dest,paint);
    }

    private Bitmap getCompanyLogo(String company){ return companyLogoCache.get(normalizeCompany(company)); }

    private Bitmap downloadLogoBitmap(String urlText){
        HttpURLConnection con=null;
        try{
            URL u=new URL(urlText);
            con=(HttpURLConnection)u.openConnection();
            con.setConnectTimeout(5000);
            con.setReadTimeout(5000);
            con.setInstanceFollowRedirects(true);
            con.setRequestProperty("User-Agent","Mozilla/5.0 JobBubble/1.0");
            con.setRequestProperty("Accept","image/*,*/*;q=0.8");
            int code=con.getResponseCode();
            if(code>=200&&code<300){
                try(InputStream in=con.getInputStream()){
                    Bitmap bm=BitmapFactory.decodeStream(in);
                    if(bm!=null&&bm.getWidth()>8&&bm.getHeight()>8)return bm;
                }
            }
        }catch(Exception ignored){} finally { if(con!=null)con.disconnect(); }
        return null;
    }

    private void requestCompanyLogo(String company){
        final String key=normalizeCompany(company);
        if(key.isEmpty()||companyLogoCache.containsKey(key)||!companyLogoLoading.add(key))return;
        logoExecutor.execute(()->{
            Bitmap bm=null;
            try{
                java.util.List<String> domains=companyLogoDomains(company);
                for(String domain:domains){
                    if(domain==null||domain.trim().isEmpty())continue;
                    // Google favicon endpoint is the primary source because it works without
                    // a paid API key and returns official site artwork for most employers.
                    String encoded=java.net.URLEncoder.encode("https://"+domain,"UTF-8");
                    bm=downloadLogoBitmap("https://www.google.com/s2/favicons?sz=256&domain_url="+encoded);
                    if(bm==null)bm=downloadLogoBitmap("https://icons.duckduckgo.com/ip3/"+domain+".ico");
                    if(bm==null)bm=downloadLogoBitmap("https://logo.clearbit.com/"+domain+"?size=256");
                    if(bm!=null)break;
                }
                if(bm!=null)companyLogoCache.put(key,bm);
            }catch(Exception ignored){} finally { companyLogoLoading.remove(key); }
            if(bm!=null)runOnUiThread(()->scheduleMapRender(140));
        });
    }

    private java.util.List<String> companyLogoDomains(String company){
        java.util.LinkedHashSet<String> out=new java.util.LinkedHashSet<>();
        String mapped=companyLogoDomain(company);
        if(mapped!=null)out.add(mapped);
        String x=normalizeCompany(company);
        if(!x.isEmpty()){
            String compact=x.replaceAll("\\b(inc|llc|corp|corporation|company|co|ltd|holdings|group|services|service|healthcare|health|medical|systems|system|partners|partner|staffing|solutions|solution|the)\\b"," ").replaceAll("[^a-z0-9]","");
            if(compact.length()>=3){out.add(compact+".com");out.add(compact+".org");}
            String first=x.split("\\s+")[0].replaceAll("[^a-z0-9]","");
            if(first.length()>=4){out.add(first+".com");out.add(first+".org");}
        }
        return new java.util.ArrayList<>(out);
    }

    private String companyLogoDomain(String company){
        String x=normalizeCompany(company);
        if(x.contains("amazon"))return "amazon.com"; if(x.contains("starbucks"))return "starbucks.com"; if(x.contains("walmart"))return "walmart.com";
        if(x.contains("target"))return "target.com"; if(x.contains("home depot"))return "homedepot.com"; if(x.contains("lowe"))return "lowes.com";
        if(x.contains("costco"))return "costco.com"; if(x.contains("boeing"))return "boeing.com"; if(x.contains("microsoft"))return "microsoft.com";
        if(x.contains("apple"))return "apple.com"; if(x.contains("tesla"))return "tesla.com"; if(x.contains("fedex"))return "fedex.com"; if(x.contains("ups"))return "ups.com";
        if(x.contains("instacart"))return "instacart.com"; if(x.contains("providence"))return "providence.org"; if(x.contains("st david"))return "stdavids.com";
        if(x.contains("ascension"))return "ascension.org"; if(x.contains("mattress firm"))return "mattressfirm.com"; if(x.contains("jackson therapy"))return "jacksontherapy.com";
        if(x.contains("stability healthcare"))return "stabilityhealthcare.com"; if(x.contains("healthcare support"))return "healthcaresupport.com";
        if(x.contains("cross country"))return "crosscountry.com"; if(x.contains("trustaff"))return "trustaff.com"; if(x.contains("aya healthcare"))return "ayahealthcare.com";
        if(x.contains("medical solutions"))return "medicalsolutions.com"; if(x.contains("host healthcare"))return "hosthealthcare.com"; if(x.contains("totalmed"))return "totalmed.com";
        if(x.contains("gifted healthcare"))return "giftedhealthcare.com"; if(x.contains("fusion medical"))return "fusionmedstaff.com"; if(x.contains("coremedical"))return "coremedicalgroup.com";
        if(x.contains("mcdonald"))return "mcdonalds.com"; if(x.contains("chipotle"))return "chipotle.com"; if(x.contains("cvs"))return "cvs.com"; if(x.contains("walgreens"))return "walgreens.com";
        if(x.contains("kaiser"))return "kaiserpermanente.org"; if(x.contains("swedish"))return "swedish.org"; if(x.contains("evergreenhealth"))return "evergreenhealth.com";
        if(x.contains("life stance")||x.contains("lifestance"))return "lifestance.com"; if(x.contains("seattle children's")||x.contains("seattle childrens"))return "seattlechildrens.org";
        if(x.contains("virginia mason"))return "vmfh.org"; if(x.contains("multicare"))return "multicare.org"; if(x.contains("fred meyer"))return "fredmeyer.com";
        if(x.contains("kroger"))return "kroger.com"; if(x.contains("safeway"))return "safeway.com"; if(x.contains("whole foods"))return "wholefoodsmarket.com";
        if(x.contains("best buy"))return "bestbuy.com"; if(x.contains("t mobile")||x.contains("tmobile"))return "t-mobile.com"; if(x.contains("comcast")||x.contains("xfinity"))return "xfinity.com";
        if(x.contains("at and t")||x.equals("att"))return "att.com"; if(x.contains("verizon"))return "verizon.com"; if(x.contains("amazon web services")||x.equals("aws"))return "aws.amazon.com";
        if(x.contains("uber"))return "uber.com"; if(x.contains("lyft"))return "lyft.com"; if(x.contains("doordash"))return "doordash.com";
        if(x.contains("google"))return "google.com"; if(x.contains("meta"))return "meta.com"; if(x.contains("salesforce"))return "salesforce.com";
        if(x.contains("nordstrom"))return "nordstrom.com"; if(x.contains("rei"))return "rei.com"; if(x.contains("alaska airlines"))return "alaskaair.com";
        return null;
    }

    private String shortCompanyName(String c){if(c==null||c.trim().isEmpty())return "Employer";String x=c.trim();return x.length()>20?x.substring(0,19)+"…":x;}
    private String markerDistanceText(Job j){double d=distanceMiles(userLat,userLon,j.lat,j.lon);return String.format(Locale.US,"%.1f mi",d);}

    private String markerPayText(double p){
        if(p<=0)return "Pay not listed";
        if(Math.abs(p-Math.rint(p))<0.001)return "$"+((int)Math.rint(p))+"/hr";
        return "$"+String.format(Locale.US,"%.2f",p)+"/hr";
    }

    private String shortMarkerTitle(String t){
        if(t==null||t.trim().isEmpty())return "Job";
        String x=t.toLowerCase(Locale.US);
        if(x.contains("customer service/sales"))return "Retail";
        if(x.contains("retail sales"))return "Sales";
        if(x.contains("online order filling"))return "Order Filling";
        if(x.contains("fulfillment center"))return "Warehouse";
        if(x.contains("package handler"))return "Package Handler";
        if(x.contains("guest advocate"))return "Guest Advocate";
        if(x.contains("medical assistant"))return "Medical Asst.";
        if(x.contains("crew team"))return "Crew Member";
        if(x.contains("administrative assistant"))return "Admin Assistant";
        return t.length()>22?t.substring(0,21)+"…":t;
    }

    // V9.4.37: JobBubble is U.S.-only. A TileOverlay is used instead of ordinary
    // GoogleMap polygons because Google can render its own text labels above polygons.
    // The tile overlay sits above the base map, so Canada/Mexico become clean gray
    // country shapes with only the JobBubble-owned country name visible.
    private static final LatLng[] CANADA_CURTAIN = new LatLng[]{
        new LatLng(48.99,-123.32), new LatLng(49.00,-117.03), new LatLng(49.00,-110.00),
        new LatLng(49.00,-101.50), new LatLng(49.00,-95.15), new LatLng(48.15,-89.70),
        new LatLng(47.00,-88.00), new LatLng(46.45,-84.75), new LatLng(45.95,-83.00),
        new LatLng(43.65,-82.40), new LatLng(42.05,-83.10), new LatLng(42.85,-78.90),
        new LatLng(44.80,-74.80), new LatLng(45.00,-71.50), new LatLng(45.00,-67.00),
        new LatLng(47.00,-60.00), new LatLng(52.00,-55.00), new LatLng(60.00,-61.00),
        new LatLng(68.00,-64.00), new LatLng(76.00,-78.00), new LatLng(82.00,-100.00),
        new LatLng(78.00,-125.00), new LatLng(70.00,-141.00), new LatLng(60.00,-141.00),
        new LatLng(58.50,-136.50), new LatLng(55.00,-130.00), new LatLng(51.00,-128.00),
        new LatLng(48.99,-123.32)
    };

    private static final LatLng[] MEXICO_CURTAIN = new LatLng[]{
        new LatLng(32.54,-117.12), new LatLng(32.72,-114.72), new LatLng(31.33,-111.05),
        new LatLng(31.78,-108.21), new LatLng(31.78,-106.50), new LatLng(29.45,-104.45),
        new LatLng(28.70,-103.10), new LatLng(29.75,-101.30), new LatLng(27.50,-99.50),
        new LatLng(25.84,-97.15), new LatLng(23.75,-97.50), new LatLng(23.75,-60.00),
        new LatLng(0.00,-60.00), new LatLng(0.00,-125.00), new LatLng(23.00,-125.00),
        new LatLng(23.00,-110.00), new LatLng(28.00,-114.00), new LatLng(32.54,-117.12)
    };

    // Canada immediately east/southeast of Alaska. At Alaska zoom levels this curtain
    // is enough to keep Canadian roads/cities/labels from appearing beside the state.
    private static final LatLng[] ALASKA_CANADA_CURTAIN = new LatLng[]{
        new LatLng(69.8,-141.0), new LatLng(60.0,-141.0), new LatLng(59.4,-139.4),
        new LatLng(58.8,-137.6), new LatLng(58.2,-136.4), new LatLng(57.3,-135.0),
        new LatLng(56.3,-133.7), new LatLng(55.2,-132.0), new LatLng(54.4,-130.0),
        new LatLng(50.0,-130.0), new LatLng(50.0,-105.0), new LatLng(76.0,-105.0),
        new LatLng(76.0,-141.0), new LatLng(69.8,-141.0)
    };

    // V9.4.40: strict selected-region mask. Everything outside the active U.S.
    // region is covered by a solid curtain above the Google base map. This prevents
    // foreign roads, cities, labels, terrain and country names from showing at all.
    private static final LatLng[] LOWER48_OUTLINE = new LatLng[]{
        new LatLng(49.0,-124.8),new LatLng(49.0,-95.0),new LatLng(48.0,-89.5),
        new LatLng(46.5,-84.5),new LatLng(45.0,-83.0),new LatLng(42.0,-83.0),
        new LatLng(43.0,-79.0),new LatLng(45.0,-74.8),new LatLng(45.0,-71.5),
        new LatLng(47.2,-67.0),new LatLng(44.5,-67.0),new LatLng(41.0,-70.0),
        new LatLng(39.0,-74.0),new LatLng(35.0,-75.5),new LatLng(30.0,-81.2),
        new LatLng(25.0,-80.0),new LatLng(24.4,-82.0),new LatLng(29.0,-83.0),
        new LatLng(29.0,-89.0),new LatLng(29.0,-94.0),new LatLng(25.8,-97.2),
        new LatLng(28.8,-100.0),new LatLng(29.0,-103.0),new LatLng(31.8,-106.5),
        new LatLng(31.3,-111.0),new LatLng(32.5,-117.1),new LatLng(34.0,-120.0),
        new LatLng(38.0,-123.0),new LatLng(42.0,-124.0),new LatLng(46.0,-124.8),
        new LatLng(49.0,-124.8)
    };

    private static final LatLng[] ALASKA_OUTLINE = new LatLng[]{
        new LatLng(71.5,-156.0),new LatLng(70.0,-141.0),new LatLng(60.0,-141.0),
        new LatLng(59.0,-139.0),new LatLng(58.0,-136.5),new LatLng(55.0,-130.0),
        new LatLng(54.4,-132.0),new LatLng(56.0,-135.0),new LatLng(57.5,-138.5),
        new LatLng(59.0,-143.0),new LatLng(60.0,-147.0),new LatLng(59.0,-152.0),
        new LatLng(57.0,-157.0),new LatLng(55.0,-162.0),new LatLng(54.0,-166.0),
        new LatLng(52.0,-170.0),new LatLng(52.5,-176.0),new LatLng(54.5,-179.5),
        new LatLng(58.0,-170.0),new LatLng(61.0,-166.0),new LatLng(64.0,-166.0),
        new LatLng(67.0,-164.0),new LatLng(69.0,-162.0),new LatLng(71.5,-156.0)
    };

    private static final LatLng[] HAWAII_OUTLINE = new LatLng[]{
        new LatLng(22.35,-160.35),new LatLng(22.25,-159.15),new LatLng(21.75,-158.0),
        new LatLng(21.25,-156.7),new LatLng(20.45,-155.2),new LatLng(18.75,-154.7),
        new LatLng(18.7,-156.0),new LatLng(19.6,-157.4),new LatLng(20.5,-158.7),
        new LatLng(21.4,-160.4),new LatLng(22.35,-160.35)
    };

    private void removeForeignCountryCurtains(){
        if(foreignCountryTileOverlay!=null){
            try{foreignCountryTileOverlay.remove();}catch(Exception ignored){}
            foreignCountryTileOverlay=null;
        }
        for(Marker m:foreignCountryLabels)try{m.remove();}catch(Exception ignored){}
        foreignCountryLabels.clear();
        foreignTileCache.clear();
    }

    private void installForeignCountryCurtains(){
        if(googleMap==null)return;
        if(foreignCountryTileOverlay!=null){
            try{foreignCountryTileOverlay.remove();}catch(Exception ignored){}
            foreignCountryTileOverlay=null;
        }
        for(Marker m:foreignCountryLabels)try{m.remove();}catch(Exception ignored){}
        foreignCountryLabels.clear();
        foreignTileCache.clear();

        final int fill=Color.parseColor(isLightUi()?"#E7E8EB":"#111820");
        TileProvider provider=(x,y,zoom)->renderStrictRegionMaskTile(x,y,zoom,fill);
        foreignCountryTileOverlay=googleMap.addTileOverlay(new TileOverlayOptions()
            .tileProvider(provider).zIndex(90f).fadeIn(false));
    }

    private LatLng[] selectedRegionOutline(){
        if("alaska".equals(mapRegion))return ALASKA_OUTLINE;
        if("hawaii".equals(mapRegion))return HAWAII_OUTLINE;
        return LOWER48_OUTLINE;
    }

    private Tile renderStrictRegionMaskTile(int tileX,int tileY,int zoom,int fill){
        final int size=256;
        final String key=mapRegion+":"+zoom+":"+tileX+":"+tileY+":"+fill;
        byte[] cached=foreignTileCache.get(key);
        if(cached!=null)return new Tile(size,size,cached);

        Bitmap b=Bitmap.createBitmap(size,size,Bitmap.Config.ARGB_8888);
        Canvas c=new Canvas(b);
        c.drawColor(fill);

        Paint clearPaint=new Paint(Paint.ANTI_ALIAS_FLAG);
        clearPaint.setStyle(Paint.Style.FILL);
        clearPaint.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.CLEAR));
        drawGeoCurtainPath(c,selectedRegionOutline(),tileX,tileY,zoom,clearPaint,null);
        clearPaint.setXfermode(null);

        ByteArrayOutputStream out=new ByteArrayOutputStream(3072);
        b.compress(Bitmap.CompressFormat.PNG,100,out);
        b.recycle();
        byte[] bytes=out.toByteArray();
        foreignTileCache.put(key,bytes);
        return new Tile(size,size,bytes);
    }

    private double tileYToLatitude(double y,double n){
        double merc=Math.PI*(1.0-2.0*y/n);
        return Math.toDegrees(Math.atan(Math.sinh(merc)));
    }

    private boolean bboxIntersects(double left,double right,double bottom,double top,
                                   double minLon,double maxLon,double minLat,double maxLat){
        return right>=minLon && left<=maxLon && top>=minLat && bottom<=maxLat;
    }

    private void drawGeoCurtainPath(Canvas canvas,LatLng[] polygon,int tileX,int tileY,int zoom,Paint fillPaint,Paint edgePaint){
        if(polygon==null||polygon.length<3)return;
        Path path=new Path();
        double world=256.0*Math.pow(2.0,zoom);
        boolean first=true;
        for(LatLng ll:polygon){
            double px=((ll.longitude+180.0)/360.0)*world-(tileX*256.0);
            double sin=Math.sin(Math.toRadians(Math.max(-85.05112878,Math.min(85.05112878,ll.latitude))));
            double py=(0.5-Math.log((1.0+sin)/(1.0-sin))/(4.0*Math.PI))*world-(tileY*256.0);
            if(first){path.moveTo((float)px,(float)py);first=false;}else path.lineTo((float)px,(float)py);
        }
        path.close();
        if(fillPaint!=null)canvas.drawPath(path,fillPaint);
        if(edgePaint!=null)canvas.drawPath(path,edgePaint);
    }

    private void addForeignCountryLabel(String name,LatLng position){
        if(googleMap==null)return;
        Bitmap b=Bitmap.createBitmap(dp(150),dp(42),Bitmap.Config.ARGB_8888);
        Canvas c=new Canvas(b);
        Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setTextAlign(Paint.Align.CENTER);
        p.setTypeface(Typeface.create(Typeface.DEFAULT,Typeface.BOLD));
        p.setTextSize(dp(18));
        p.setColor(Color.parseColor(isLightUi()?"#4C5158":"#E2E5E8"));
        Paint.FontMetrics fm=p.getFontMetrics();
        float y=b.getHeight()/2f-(fm.ascent+fm.descent)/2f;
        c.drawText(name,b.getWidth()/2f,y,p);
        Marker m=googleMap.addMarker(new MarkerOptions().position(position)
            .icon(BitmapDescriptorFactory.fromBitmap(b)).anchor(.5f,.5f).zIndex(100f));
        if(m!=null)foreignCountryLabels.add(m);
    }

    private void updateForeignCountryLabels(){
        // V9.4.40: foreign country names are intentionally never shown.
        for(Marker m:foreignCountryLabels)try{m.setVisible(false);}catch(Exception ignored){}
    }

    private void requestLocation(){
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_FINE_LOCATION)!=PackageManager.PERMISSION_GRANTED && ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_COARSE_LOCATION)!=PackageManager.PERMISSION_GRANTED)
            ActivityCompat.requestPermissions(this,new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION},LOCATION_REQUEST);
        else enableLocation();
    }
    @SuppressLint("MissingPermission") private void enableLocation(){
        locationClient.getLastLocation().addOnSuccessListener(loc->{ enableGoogleMyLocation(); if(loc!=null){userLat=loc.getLatitude();userLon=loc.getLongitude();haveLocation=true;centerOnUser();loadJobs();} else {jobs.clear();applyFilters();status.setText("Location unavailable — live jobs not loaded");}});
    }
    private void centerOnUser(){
        if(mapReady && googleMap!=null){
            LatLng target=new LatLng(userLat,userLon);
            boolean inside=isInsideSelectedMapRegion(target);
            if(!inside) target=selectedMapRegionCenter();
            googleMap.animateCamera(CameraUpdateFactory.newLatLngZoom(
                target,inside?13f:selectedMapRegionDefaultZoom()));
        }
    }

    private LatLng selectedMapRegionCenter(){
        if("alaska".equals(mapRegion))return new LatLng(64.2,-152.5);
        if("hawaii".equals(mapRegion))return new LatLng(20.7,-157.4);
        return new LatLng(38.7,-96.5);
    }

    private float selectedMapRegionDefaultZoom(){
        if("alaska".equals(mapRegion))return 5.0f;
        if("hawaii".equals(mapRegion))return 7.35f;
        return 4.35f;
    }

    private boolean isInsideSelectedMapRegion(LatLng p){
        if(p==null)return false;
        if("alaska".equals(mapRegion)){
            // Includes the mainland, panhandle, and most Aleutians without treating Canada as Alaska.
            return p.latitude>=51.0 && p.latitude<=72.5 &&
                ((p.longitude>=-180.0 && p.longitude<=-129.0) || p.longitude>=169.0);
        }
        if("hawaii".equals(mapRegion))
            return p.latitude>=18.0 && p.latitude<=23.0 && p.longitude>=-161.5 && p.longitude<=-154.0;
        return p.latitude>=24.0 && p.latitude<=50.0 && p.longitude>=-125.5 && p.longitude<=-66.0;
    }

    private void applyMapRegionBounds(boolean moveCamera){
        if(googleMap==null)return;
        try{
            if("alaska".equals(mapRegion)){
                googleMap.setMinZoomPreference(4.65f);
                // Keep the camera on Alaska itself; the mainland/panhandle fill the useful view.
                googleMap.setLatLngBoundsForCameraTarget(new LatLngBounds(
                    new LatLng(51.0,-179.8),new LatLng(72.5,-129.0)));
            }else if("hawaii".equals(mapRegion)){
                googleMap.setMinZoomPreference(6.85f);
                googleMap.setLatLngBoundsForCameraTarget(new LatLngBounds(
                    new LatLng(18.0,-161.5),new LatLng(23.0,-154.0)));
            }else{
                googleMap.setMinZoomPreference(3.35f);
                // Default Google map, but camera targets remain in the United States region.
                // The bounds leave a little visual context at the edges without allowing world-wide panning.
                googleMap.setLatLngBoundsForCameraTarget(new LatLngBounds(
                    new LatLng(18.0,-130.0),new LatLng(52.5,-62.0)));
            }
        }catch(Exception ignored){}
        removeForeignCountryCurtains();
        if(moveCamera){
            googleMap.animateCamera(CameraUpdateFactory.newLatLngZoom(
                selectedMapRegionCenter(),selectedMapRegionDefaultZoom()));
            scheduleMapRender(180);
        }
    }

    private void updateMapRegionBadge(){
        if(mapRegionBadge==null)return;
        if("alaska".equals(mapRegion))mapRegionBadge.setText("ALASKA MAP");
        else if("hawaii".equals(mapRegion))mapRegionBadge.setText("HAWAII MAP");
        else mapRegionBadge.setText("USA MAP");
    }

    private void setMapRegion(String region){
        if(region==null||region.trim().isEmpty())return;
        mapRegion=region;
        updateMapRegionBadge();
        getSharedPreferences("settings",MODE_PRIVATE).edit().putString("mapRegion",region).apply();
        saveLocalSettings();
        saveCloudState();
        applyMapRegionBounds(true);
    }
    private void applyMapTheme(){
        if(!mapReady || googleMap==null)return;
        try{
            // Keep the map itself on Google Maps default styling. UI theme still applies to JobBubble controls.
            googleMap.setMapStyle(null);
            removeForeignCountryCurtains();
        }catch(Exception ignored){}
    }
    private void setMapTheme(String theme){mapTheme=theme;getSharedPreferences("settings",MODE_PRIVATE).edit().putString("mapTheme",theme).apply();saveCloudState();applyMapTheme();applyUiTheme();applyFilters();updateZoomFocusTransparency();}

    private boolean isLightUi(){return !"dark".equals(mapTheme);}

    private void tintCompound(TextView v,int color){
        if(v==null)return;
        try{v.setCompoundDrawableTintList(android.content.res.ColorStateList.valueOf(color));}catch(Exception ignored){}
    }

    private void tintImage(ImageView v,int color){
        if(v==null)return;
        try{v.setImageTintList(android.content.res.ColorStateList.valueOf(color));}catch(Exception ignored){}
    }

    private void applyUiTheme(){
        if(findViewById(R.id.topPanel)==null)return;
        boolean light=isLightUi();
        int text=Color.parseColor(light?"#202329":"#F2F6FA");
        int muted=Color.parseColor(light?"#646A73":"#91A9BC");
        int border=Color.parseColor(light?"#C8CBD1":"#31546C");
        int chip=Color.parseColor(light?"#E2E4E8":"#0D2030");
        int panel=Color.parseColor(light?"#E9EAED":"#071725");
        int bottom=Color.parseColor(light?"#E5E7EA":"#081A28");
        int violet=Color.parseColor(light?"#6F32C9":"#A46BFF");

        View top=findViewById(R.id.topPanel); top.setBackground(roundStrokeBg(light?"#E9EAED":"#071725",light?"#D1D3D8":"#173247",0,0));
        View bottomNav=findViewById(R.id.bottomNav); bottomNav.setBackground(roundStrokeBg(light?"#E5E7EA":"#081A28",light?"#C9CCD2":"#173247",24,1));
        TextView logo=findViewById(R.id.logoTitle); if(logo!=null){
            SpannableString title=new SpannableString("JobBubble");
            title.setSpan(new ForegroundColorSpan(text),0,3,Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
            title.setSpan(new ForegroundColorSpan(violet),3,9,Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
            logo.setText(title);
        }
        TextView tag=findViewById(R.id.tagline); if(tag!=null)tag.setTextColor(muted);

        TextView dist=findViewById(R.id.distanceValue), pay=findViewById(R.id.payValue), cat=findViewById(R.id.categoryChip), src=findViewById(R.id.sourceChip);
        Button near=findViewById(R.id.locationButton);
        TextView[] neutral={dist,cat,src};
        for(TextView v:neutral)if(v!=null){v.setTextColor(text);v.setBackground(roundStrokeBg(light?"#E2E4E8":"#0D2030",light?"#BFC3CA":"#31546C",18,1));tintCompound(v,light?Color.parseColor("#553187"):Color.parseColor("#D9E9F7"));}
        if(pay!=null){pay.setBackground(roundStrokeBg(light?"#E2E4E8":"#0B2A26",light?"#AEB6B2":"#1D8E69",18,1));pay.setTextColor(Color.parseColor(light?"#12835F":"#35E0A1"));tintCompound(pay,Color.parseColor(light?"#12835F":"#35E0A1"));}
        if(near!=null){near.setBackground(roundStrokeBg(light?"#E2E4E8":"#5D27A8",light?"#B8A2D7":"#8F4AE5",18,1));near.setTextColor(text);tintCompound(near,violet);}

        ImageButton search=findViewById(R.id.searchButton), filters=findViewById(R.id.refreshButton);
        if(search!=null){search.setBackground(roundStrokeBg(light?"#E2E4E8":"#0C2030",light?"#BFC3CA":"#31546C",20,1));tintImage(search,light?Color.parseColor("#343841"):Color.parseColor("#D9E9F7"));}
        if(filters!=null){filters.setBackground(roundStrokeBg(light?"#DDDDE2":"#261044",light?"#B9A4D5":"#7442AA",20,1));tintImage(filters,light?Color.parseColor("#5D2B97"):Color.parseColor("#D9C2FF"));}
        if(mapRegionBadge!=null){mapRegionBadge.setTextColor(light?Color.parseColor("#252932"):Color.WHITE);mapRegionBadge.setBackground(roundStrokeBg(light?"#F2F3F5":"#132638",light?"#B9BEC6":"#3F566A",16,1));}

        int navMuted=Color.parseColor(light?"#646A73":"#9BB0C1");
        int navActive=Color.parseColor(light?"#252932":"#FFFFFF");
        View[] navs={findViewById(R.id.navMap),findViewById(R.id.navList),findViewById(R.id.navSaved),findViewById(R.id.navProfile)};
        for(int i=0;i<navs.length;i++) if(navs[i] instanceof android.view.ViewGroup){
            android.view.ViewGroup g=(android.view.ViewGroup)navs[i];
            for(int j=0;j<g.getChildCount();j++)if(g.getChildAt(j) instanceof TextView){
                TextView tv=(TextView)g.getChildAt(j);
                if(i==0 && j==0)tv.setTextColor(violet); else tv.setTextColor(i==0?navActive:navMuted);
            }
        }
        getWindow().setStatusBarColor(light?Color.parseColor("#ECEDEF"):Color.parseColor("#061421"));
        getWindow().setNavigationBarColor(light?Color.parseColor("#ECEDEF"):Color.parseColor("#061421"));
        if(android.os.Build.VERSION.SDK_INT>=23){
            int flags=getWindow().getDecorView().getSystemUiVisibility();
            if(light)flags|=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;else flags&=~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
            getWindow().getDecorView().setSystemUiVisibility(flags);
        }
        // Theme changes can make Android reconsider system-bar visibility. Re-hide them.
        enableImmersiveFullscreen();
    }

    private void bindFilters(){
        categorySpinner=findViewById(R.id.categorySpinner); sourceSpinner=findViewById(R.id.sourceSpinner); distanceBar=findViewById(R.id.distanceBar); payBar=findViewById(R.id.payBar);
        categoryChip=findViewById(R.id.categoryChip); sourceChip=findViewById(R.id.sourceChip);
        distanceValue=findViewById(R.id.distanceValue); payValue=findViewById(R.id.payValue); resultCount=findViewById(R.id.resultCount); status=findViewById(R.id.status); mapRegionBadge=findViewById(R.id.mapRegionBadge);
        updateMapRegionBadge();
        TextView logoTitle=findViewById(R.id.logoTitle);
        SpannableString logoText=new SpannableString("JobBubble");
        logoText.setSpan(new ForegroundColorSpan(Color.parseColor("#9B4DFF")),3,9, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        logoTitle.setText(logoText);
        final String[] cats={"All jobs","Retail & Sales","Warehouse & Logistics","Food & Hospitality","Construction & Skilled Trades","Office & Administration","Customer Service","Healthcare","Transportation & Delivery","Security & Public Safety","Technology & Engineering","Government","Education","Finance & Accounting","Manufacturing","Cleaning & Facilities","Other"};
        final String[] src={"All sources","Adzuna","USAJOBS","The Muse"};
        category=normalizeSavedCategory(category);
        source=normalizeSavedSource(source);
        categoryChip.setText(category);
        sourceChip.setText(source);
        categorySpinner.setAdapter(modernSpinnerAdapter(cats));
        sourceSpinner.setAdapter(modernSpinnerAdapter(src));
        categoryChip.setOnClickListener(v->showChoiceMenu("Job category",cats,category,(choice)->{category=choice;categoryChip.setText(choice);saveLocalSettings();saveCloudState();applyFilters();}));
        sourceChip.setOnClickListener(v->showChoiceMenu("Job source",src,source,(choice)->{boolean changed=!choice.equals(source);source=choice;sourceChip.setText(choice);saveLocalSettings();saveCloudState();if(changed)loadJobs();else applyFilters();}));
        distanceBar.setMax(extendedDistance?10000:100);distanceBar.setProgress(Math.min(maxDistanceMiles,distanceBar.getMax()));distanceBar.setOnSeekBarChangeListener(new SimpleSeek(){
            public void onProgressChanged(SeekBar s,int p,boolean fromUser){
                maxDistanceMiles=Math.max(1,p);
                distanceValue.setText(maxDistanceMiles+" mi");
                if(!fromUser) applyFilters();
            }
            @Override public void onStopTrackingTouch(SeekBar s){ saveLocalSettings();saveCloudState();refreshForRangeChange(); }
        });
        payBar.setMax(100);payBar.setProgress(minPay);payBar.setOnSeekBarChangeListener(new SimpleSeek(){public void onProgressChanged(SeekBar s,int p,boolean f){minPay=Math.max(0,p);payValue.setText("$"+minPay+"+");scheduleMapRender(90);} @Override public void onStopTrackingTouch(SeekBar s){saveLocalSettings();saveCloudState();scheduleMapRender(0);}});
        distanceValue.setOnClickListener(v->showNumericFilterDialog(true));
        payValue.setOnClickListener(v->showNumericFilterDialog(false));
        findViewById(R.id.refreshButton).setOnClickListener(v->showFilterSettings()); findViewById(R.id.locationButton).setOnClickListener(v->centerOnUser());
        findViewById(R.id.searchButton).setOnClickListener(v->showSearchDialog());
        findViewById(R.id.navMap).setOnClickListener(v->centerOnUser()); findViewById(R.id.navList).setOnClickListener(v->showJobList(false)); findViewById(R.id.navSaved).setOnClickListener(v->showJobList(true)); findViewById(R.id.navProfile).setOnClickListener(v->showProfile());
    }
    abstract class SimpleSeek implements SeekBar.OnSeekBarChangeListener{public void onStartTrackingTouch(SeekBar s){} public void onStopTrackingTouch(SeekBar s){}}

    private ArrayAdapter<String> modernSpinnerAdapter(String[] items){
        return new ArrayAdapter<String>(this,R.layout.spinner_item,items){
            @Override public View getDropDownView(int position,View convertView,android.view.ViewGroup parent){
                View v=super.getDropDownView(position,convertView,parent);
                TextView t=(TextView)v; t.setTextColor(Color.parseColor("#EAF3FA")); t.setTextSize(15); t.setPadding(dp(16),dp(14),dp(16),dp(14));
                t.setBackgroundColor(position%2==0?Color.parseColor("#102335"):Color.parseColor("#0C1D2C"));
                return t;
            }
        };
    }
    private interface ChoiceCallback{void picked(String value);}

    private String choiceIcon(String item){
        if(item.equals("All jobs")||item.equals("All sources")) return "▦";
        if(item.equals("Retail & Sales")) return "▰";
        if(item.equals("Warehouse & Logistics")) return "◇";
        if(item.equals("Food & Hospitality")) return "♨";
        if(item.equals("Construction & Skilled Trades")) return "⌂";
        if(item.equals("Office & Administration")) return "▥";
        if(item.equals("Customer Service")) return "☎";
        if(item.equals("Healthcare")) return "✚";
        if(item.equals("Transportation & Delivery")) return "▰";
        if(item.equals("Security & Public Safety")) return "⛨";
        if(item.equals("Technology & Engineering")) return "▱";
        if(item.equals("Government")) return "★";
        if(item.equals("Education")) return "▤";
        if(item.equals("Finance & Accounting")) return "$";
        if(item.equals("Manufacturing")) return "⚙";
        if(item.equals("Cleaning & Facilities")) return "◆";
        if(item.equals("Adzuna")) return "A";
        if(item.equals("USAJOBS")) return "US";
        if(item.equals("The Muse")) return "TM";
        return "•";
    }

    private String normalizeSavedSource(String value){
        if(value==null)return "All sources";
        if(value.equalsIgnoreCase("Adzuna"))return "Adzuna";
        if(value.equalsIgnoreCase("USAJOBS"))return "USAJOBS";
        if(value.equalsIgnoreCase("The Muse")||value.equalsIgnoreCase("Muse"))return "The Muse";
        if(value.equalsIgnoreCase("CareerOneStop")||value.equalsIgnoreCase("CareerOneStop/NLx"))return "All sources";
        return "All sources";
    }

    private String normalizeSavedCategory(String value){
        if(value==null||value.trim().isEmpty()||value.equalsIgnoreCase("All jobs"))return "All jobs";
        String v=value.trim();
        if(v.equalsIgnoreCase("Retail"))return "Retail & Sales";
        if(v.equalsIgnoreCase("Warehouse"))return "Warehouse & Logistics";
        if(v.equalsIgnoreCase("Restaurant"))return "Food & Hospitality";
        if(v.equalsIgnoreCase("Construction"))return "Construction & Skilled Trades";
        if(v.equalsIgnoreCase("Office"))return "Office & Administration";
        if(v.equalsIgnoreCase("Transportation"))return "Transportation & Delivery";
        if(v.equalsIgnoreCase("Security"))return "Security & Public Safety";
        if(v.equalsIgnoreCase("Technology"))return "Technology & Engineering";
        String[] valid={"Retail & Sales","Warehouse & Logistics","Food & Hospitality","Construction & Skilled Trades","Office & Administration","Customer Service","Healthcare","Transportation & Delivery","Security & Public Safety","Technology & Engineering","Government","Education","Finance & Accounting","Manufacturing","Cleaning & Facilities","Other"};
        for(String x:valid)if(x.equalsIgnoreCase(v))return x;
        return "All jobs";
    }

    private static String refinedJobCategory(String title,String providerCategory,String description,String company,String source){
        String x=((title==null?"":title)+" "+(providerCategory==null?"":providerCategory)+" "+(description==null?"":description)+" "+(company==null?"":company)).toLowerCase(Locale.US);
        String src=source==null?"":source.toLowerCase(Locale.US);
        if(src.contains("usajobs")||x.contains("federal government")||x.contains("government administration"))return "Government";
        if(x.matches(".*\b(nurse|rn|lpn|cna|medical|health|hospital|clinic|pharmacy|pharmacist|therapist|dental|dentist|physician|doctor|caregiver|surgical|radiology|respiratory|patient)\b.*"))return "Healthcare";
        if(x.matches(".*\b(software|developer|engineer|engineering|information technology|\bit\b|cyber|network|systems|data scientist|data analyst|programmer|cloud|devops|technical support)\b.*"))return "Technology & Engineering";
        if(x.matches(".*\b(teacher|teaching|school|education|educator|instructor|professor|tutor|academic|training specialist)\b.*"))return "Education";
        if(x.matches(".*\b(accountant|accounting|finance|financial|bookkeeper|payroll|auditor|banking|credit|tax preparer)\b.*"))return "Finance & Accounting";
        if(x.matches(".*\b(manufactur|production|machinist|assembler|fabricator|welder|cnc|machine operator|plant operator)\b.*"))return "Manufacturing";
        if(x.matches(".*\b(construction|carpenter|electrician|plumber|hvac|roofer|mechanic|maintenance technician|skilled trade|journeyman|apprentice)\b.*"))return "Construction & Skilled Trades";
        if(x.matches(".*\b(warehouse|fulfillment|picker|packer|inventory|material handler|forklift|distribution|shipping|receiving|logistics)\b.*"))return "Warehouse & Logistics";
        if(x.matches(".*\b(driver|delivery|courier|cdl|truck|transportation|transit|bus driver|air traffic|dispatcher|fleet)\b.*"))return "Transportation & Delivery";
        if(x.matches(".*\b(security|police|officer|guard|public safety|firefighter|correction|law enforcement|emergency management)\b.*"))return "Security & Public Safety";
        if(x.matches(".*\b(restaurant|server|cook|chef|barista|bartender|food service|dishwasher|host|hotel|hospitality|catering)\b.*"))return "Food & Hospitality";
        if(x.matches(".*\b(retail|sales associate|cashier|store manager|merchandis|sales representative|salesperson|customer advisor|shop|grocery)\b.*"))return "Retail & Sales";
        if(x.matches(".*\b(customer service|call center|customer support|member service|client service|contact center|customer care)\b.*"))return "Customer Service";
        if(x.matches(".*\b(cleaner|janitor|custodian|housekeeper|housekeeping|facilities|groundskeeper|sanitation|building maintenance)\b.*"))return "Cleaning & Facilities";
        if(x.matches(".*\b(administrative|office|receptionist|secretary|coordinator|executive assistant|data entry|human resources|recruiter|clerical|office manager)\b.*"))return "Office & Administration";
        return "Other";
    }

    private GradientDrawable violetGlassBg(int alpha, int radius, int strokeWidth){
        GradientDrawable g=new GradientDrawable();
        if(isLightUi()) g.setColor(Color.argb(Math.min(alpha,246),229,230,234));
        else g.setColor(Color.argb(alpha,12,5,31));
        g.setCornerRadius(dp(radius));
        if(strokeWidth>0) g.setStroke(dp(strokeWidth),Color.parseColor(isLightUi()?"#9A79C2":"#6C249B"));
        return g;
    }

    private void lightenDialogTree(View v){
        if(!isLightUi()||v==null)return;
        final int text=Color.parseColor("#23262C");
        final int muted=Color.parseColor("#686E77");
        final int violet=Color.parseColor("#63339A");
        final int border=Color.parseColor("#C3C6CC");
        final int surface=Color.parseColor("#E4E6E9");

        if(v instanceof EditText){
            EditText e=(EditText)v;
            e.setTextColor(text); e.setHintTextColor(Color.parseColor("#7B818A"));
            e.setBackground(roundStrokeBg("#E6E8EB","#BFC3C9",14,1));
        }else if(v instanceof RadioButton){
            RadioButton rb=(RadioButton)v;
            rb.setTextColor(text);
            rb.setButtonTintList(new android.content.res.ColorStateList(
                new int[][]{new int[]{android.R.attr.state_checked},new int[]{}},
                new int[]{violet,Color.parseColor("#8B9199")}));
            rb.setBackground(roundStrokeBg("#E4E6E9","#C3C6CC",14,1));
        }else if(v instanceof CheckBox){
            CheckBox cb=(CheckBox)v;
            cb.setTextColor(text);
            cb.setButtonTintList(new android.content.res.ColorStateList(
                new int[][]{new int[]{android.R.attr.state_checked},new int[]{}},
                new int[]{violet,Color.parseColor("#8B9199")}));
            cb.setBackground(roundStrokeBg("#E4E6E9","#C3C6CC",14,1));
        }else if(v instanceof Button){
            Button b=(Button)v;
            String t=b.getText()==null?"":b.getText().toString().toLowerCase(Locale.US);
            if(t.contains("sign out")){
                b.setTextColor(Color.parseColor("#913949"));
                b.setBackground(roundStrokeBg("#EFE1E4","#D3AEB6",14,1));
            }else if(t.contains("apply")||t.contains("done")||t.equals("close")){
                b.setTextColor(violet);
                b.setBackground(roundStrokeBg("#DDDDE3","#B8A8CB",14,1));
            }else{
                b.setTextColor(text);
                b.setBackground(roundStrokeBg("#E2E4E8","#C1C5CB",14,1));
            }
        }else if(v instanceof TextView){
            TextView tv=(TextView)v;
            int current=tv.getCurrentTextColor();
            String t=tv.getText()==null?"":tv.getText().toString().trim().toLowerCase(Locale.US);
            if(current!=Color.parseColor("#35E0A1")&&current!=Color.parseColor("#12835F")){
                if(t.startsWith("●")) tv.setTextColor(Color.parseColor("#267A5C"));
                else tv.setTextColor(text);
            }
            if(tv.getBackground()!=null){
                if(t.startsWith("●")) tv.setBackground(roundStrokeBg("#DEE6E2","#B7C8C0",18,1));
                else if(t.equals("×")) tv.setBackground(roundStrokeBg("#DDDDE3","#B8A8CB",24,1));
            }
        }
        if(v instanceof android.view.ViewGroup){
            android.view.ViewGroup g=(android.view.ViewGroup)v;
            if(v.getBackground()!=null && !(v instanceof Button) && !(v instanceof EditText) && !(v instanceof RadioButton) && !(v instanceof CheckBox)){
                v.setBackground(roundStrokeBg("#E8E9EC","#CACDD2",14,1));
            }
            for(int i=0;i<g.getChildCount();i++)lightenDialogTree(g.getChildAt(i));
        }
    }

    private void showChoiceMenu(String title,String[] items,String current,ChoiceCallback cb){
        final Dialog dialog=new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        final boolean light=isLightUi();
        final String panel=light?"#ECEEF1":"#0C051F";
        final String rowNormal=light?"#E6E8EC":"#100921";
        final String rowSelected=light?"#E4DCF0":"#24103D";
        final String borderNormal=light?"#C9CDD3":"#2B1B45";
        final String borderSelected=light?"#8A63B7":"#7336B5";
        final int primary=Color.parseColor(light?"#20242A":"#F6F2FF");
        final int secondary=Color.parseColor(light?"#676D76":"#BBA9E5");
        final int violet=Color.parseColor(light?"#6B3AA1":"#B56DFF");

        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18),dp(18),dp(18),dp(16));
        root.setBackground(roundStrokeBg(panel,light?"#B8A2CE":"#6E2FA4",24,1));

        LinearLayout head=new LinearLayout(this);
        head.setGravity(Gravity.CENTER_VERTICAL);
        TextView hero=new TextView(this);
        hero.setText(title.equals("Job category")?"▣":"▦");
        hero.setTextColor(violet); hero.setTextSize(28); hero.setGravity(Gravity.CENTER);
        hero.setBackground(roundStrokeBg(light?"#E7E1EF":"#1B0D31",light?"#B69CCE":"#663399",16,1));
        head.addView(hero,new LinearLayout.LayoutParams(dp(52),dp(52)));

        LinearLayout titles=new LinearLayout(this); titles.setOrientation(LinearLayout.VERTICAL); titles.setPadding(dp(14),0,0,0);
        TextView h=new TextView(this); h.setText(title); h.setTextColor(primary); h.setTextSize(23); h.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        TextView sub=new TextView(this); sub.setText(title.equals("Job category")?"Choose a category to filter jobs.":"Choose which job source to show."); sub.setTextColor(secondary); sub.setTextSize(13);
        titles.addView(h); titles.addView(sub);
        head.addView(titles,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1f));
        TextView close=new TextView(this); close.setText("×"); close.setTextColor(primary); close.setTextSize(34); close.setGravity(Gravity.CENTER);
        close.setBackground(roundStrokeBg(light?"#E4E6EA":"#1A0D2C",light?"#C1B3D0":"#4B2A70",25,1)); close.setOnClickListener(v->dialog.dismiss());
        head.addView(close,new LinearLayout.LayoutParams(dp(50),dp(50)));
        root.addView(head);

        final int[] selected={0}; for(int i=0;i<items.length;i++) if(items[i].equals(current)){selected[0]=i;break;}
        ScrollView scroll=new ScrollView(this); scroll.setFillViewport(false); scroll.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
        LinearLayout list=new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL); list.setPadding(0,dp(10),0,dp(6));
        final ArrayList<RadioButton> radios=new ArrayList<>();
        final ArrayList<LinearLayout> rows=new ArrayList<>();
        for(int i=0;i<items.length;i++){
            final int idx=i; final String item=items[i];
            LinearLayout row=new LinearLayout(this); row.setGravity(Gravity.CENTER_VERTICAL); row.setPadding(dp(12),dp(4),dp(12),dp(4));
            row.setBackground(roundStrokeBg(i==selected[0]?rowSelected:rowNormal,i==selected[0]?borderSelected:borderNormal,14,1)); rows.add(row);
            int rowHeight=(i==0)?dp(58):dp(46);
            LinearLayout.LayoutParams rlp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,rowHeight); rlp.setMargins(0,dp(4),0,0);

            RadioButton rb=new RadioButton(this); rb.setChecked(i==selected[0]); rb.setClickable(false); rb.setFocusable(false);
            rb.setButtonTintList(new android.content.res.ColorStateList(new int[][]{new int[]{android.R.attr.state_checked},new int[]{}},new int[]{violet,Color.parseColor(light?"#8F969E":"#B7A8DD")}));
            rb.setBackgroundColor(Color.TRANSPARENT); radios.add(rb);
            row.addView(rb,new LinearLayout.LayoutParams(dp(38),dp(38)));

            String ci=choiceIcon(item);
            if(!"•".equals(ci)){
                TextView icon=new TextView(this); icon.setText(ci); icon.setTextColor(violet); icon.setTextSize(20); icon.setGravity(Gravity.CENTER);
                row.addView(icon,new LinearLayout.LayoutParams(dp(38),dp(38)));
            } else {
                TextView spacer=new TextView(this); spacer.setText(""); row.addView(spacer,new LinearLayout.LayoutParams(dp(10),dp(1)));
            }

            LinearLayout textBox=new LinearLayout(this); textBox.setOrientation(LinearLayout.VERTICAL); textBox.setGravity(Gravity.CENTER_VERTICAL);
            TextView label=new TextView(this); label.setText(item); label.setTextColor(primary); label.setTextSize(16); label.setTypeface(Typeface.DEFAULT,Typeface.BOLD); textBox.addView(label);
            if(i==0){ TextView desc=new TextView(this); desc.setText(title.equals("Job category")?"Show jobs from every category":"Show jobs from every source"); desc.setTextColor(secondary); desc.setTextSize(11); desc.setSingleLine(true); textBox.addView(desc); }
            row.addView(textBox,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1f));
            row.setOnClickListener(v->{ selected[0]=idx; for(int k=0;k<radios.size();k++) radios.get(k).setChecked(k==idx); for(int k=0;k<rows.size();k++) rows.get(k).setBackground(roundStrokeBg(k==idx?rowSelected:rowNormal,k==idx?borderSelected:borderNormal,14,1)); });
            list.addView(row,rlp);
        }
        scroll.addView(list);
        LinearLayout.LayoutParams slp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,0,1f); root.addView(scroll,slp);

        LinearLayout actions=new LinearLayout(this); actions.setPadding(0,dp(10),0,0);
        TextView cancel=new TextView(this); cancel.setText("Cancel"); cancel.setTextSize(16); cancel.setTypeface(Typeface.DEFAULT,Typeface.BOLD); cancel.setGravity(Gravity.CENTER); cancel.setIncludeFontPadding(false);
        // Force a true light-mode secondary action instead of inheriting any dark Material button tint.
        cancel.setTextColor(android.content.res.ColorStateList.valueOf(Color.parseColor(light?"#25282D":"#E9DFFF")));
        cancel.setBackground(roundStrokeBg(light?"#F3F4F6":"#160B28",light?"#B8BCC3":"#6B3BA0",16,1));
        cancel.setOnClickListener(v->dialog.dismiss());
        TextView apply=new TextView(this); apply.setText("Apply"); apply.setTextSize(16); apply.setTypeface(Typeface.DEFAULT,Typeface.BOLD); apply.setGravity(Gravity.CENTER); apply.setIncludeFontPadding(false);
        // Explicit state list prevents theme/ripple tint from turning the label dark on the violet button.
        apply.setTextColor(android.content.res.ColorStateList.valueOf(Color.WHITE));
        GradientDrawable abg=new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,new int[]{Color.parseColor(light?"#7434C8":"#5A169A"),Color.parseColor(light?"#9D35E8":"#7A1CC7")}); abg.setCornerRadius(dp(16)); apply.setBackground(abg);
        apply.setOnClickListener(v->{cb.picked(items[selected[0]]);dialog.dismiss();});
        LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(0,dp(52),1f); bp.setMargins(0,0,dp(7),0); actions.addView(cancel,bp);
        LinearLayout.LayoutParams ap=new LinearLayout.LayoutParams(0,dp(52),1f); ap.setMargins(dp(7),0,0,0); actions.addView(apply,ap); root.addView(actions);

        dialog.setContentView(root);
        dialog.setOnShowListener(x->{ Window ww=dialog.getWindow(); if(ww!=null){ww.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT)); ww.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND); WindowManager.LayoutParams lp=ww.getAttributes(); lp.dimAmount=.55f; ww.setAttributes(lp); ww.setGravity(Gravity.CENTER); ww.setLayout((int)(getResources().getDisplayMetrics().widthPixels*.88f),(int)(getResources().getDisplayMetrics().heightPixels*.82f)); }});
        dialog.show();
    }

    private EditText numericField(String value,String suffix){
        EditText e=new EditText(this);
        e.setText(value);
        e.setSelectAllOnFocus(true);
        e.setSingleLine(true);
        e.setInputType(InputType.TYPE_CLASS_NUMBER);
        e.setTextColor(Color.parseColor("#F4F8FC"));
        e.setHintTextColor(Color.parseColor("#6F879A"));
        e.setTextSize(17);
        e.setGravity(Gravity.CENTER_VERTICAL);
        e.setPadding(dp(14),0,dp(14),0);
        e.setBackground(roundStrokeBg("#0E2132","#31546C",14,1));
        e.setContentDescription(suffix);
        return e;
    }

    private void refreshForRangeChange(){
        String savedWhere=profileLocation();
        if(!jobApiUrl().contains("YOUR_BACKEND_URL") && (haveLocation || !savedWhere.isEmpty())){
            loadJobs();
        }else{
            applyFilters();
        }
    }

    private int safeInt(EditText e,int fallback,int min,int max){
        try{
            String raw=e.getText().toString().trim();
            if(raw.isEmpty())return fallback;
            int v=Integer.parseInt(raw);
            return Math.max(min,Math.min(max,v));
        }catch(Exception ex){return fallback;}
    }

    private void showNumericFilterDialog(boolean distance){
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(14),dp(22),dp(24)); box.setBackground(roundBg("#0B1A29",28));
        TextView handle=new TextView(this); LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(dp(42),dp(5)); hp.gravity=Gravity.CENTER_HORIZONTAL; hp.bottomMargin=dp(16); handle.setLayoutParams(hp); handle.setBackground(roundBg("#526A7E",10)); box.addView(handle);
        String titleText=distance?"Distance":"Minimum hourly pay";
        TextView title=label(titleText,22,"#F4F8FC",true); box.addView(title);
        TextView sub=label(distance?(extendedDistance?"Extended distance is on — drag the slider or type up to 10,000 miles.":"Drag the slider or type up to 100 miles. Enable Extended distance in Settings for long-range searches."):"Drag the slider or type your minimum hourly rate.",13,"#8FA7BA",false); sub.setPadding(0,dp(4),0,dp(16)); box.addView(sub);

        int current=distance?maxDistanceMiles:minPay;
        int max=distance?(extendedDistance?10000:100):100;
        int min=distance?1:0;
        SeekBar slider=new SeekBar(this); slider.setMax(max); slider.setProgress(current); box.addView(slider,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(48)));
        LinearLayout row=new LinearLayout(this); row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER_VERTICAL); row.setPadding(0,dp(6),0,0);
        TextView prefix=label(distance?"Miles":"$",16,"#A9BED0",true); row.addView(prefix,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT,dp(48)));
        EditText input=numericField(String.valueOf(current),distance?"miles":"dollars per hour"); LinearLayout.LayoutParams ip=new LinearLayout.LayoutParams(0,dp(48),1); ip.leftMargin=dp(10); row.addView(input,ip);
        TextView suffix=label(distance?"mi":"/ hr +",15,"#8FA7BA",false); suffix.setPadding(dp(10),0,0,0); row.addView(suffix,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT,dp(48))); box.addView(row);
        slider.setOnSeekBarChangeListener(new SimpleSeek(){public void onProgressChanged(SeekBar s,int val,boolean f){int v=Math.max(min,val);if(f)input.setText(String.valueOf(v));}});

        LinearLayout actions=new LinearLayout(this); actions.setOrientation(LinearLayout.HORIZONTAL); actions.setPadding(0,dp(18),0,0);
        Button cancel=new Button(this); cancel.setText("Cancel"); cancel.setAllCaps(false); cancel.setTextColor(Color.WHITE); cancel.setBackground(roundStrokeBg("#10283A","#31546C",14,1)); LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(0,dp(52),1); cp.rightMargin=dp(8); actions.addView(cancel,cp);
        Button apply=new Button(this); apply.setText("Apply"); apply.setAllCaps(false); apply.setTypeface(Typeface.DEFAULT,Typeface.BOLD); apply.setTextColor(Color.WHITE); apply.setBackground(roundBg("#2196F3",14)); LinearLayout.LayoutParams ap=new LinearLayout.LayoutParams(0,dp(52),1); ap.leftMargin=dp(8); actions.addView(apply,ap); box.addView(actions);
        cancel.setOnClickListener(v->dlg.dismiss());
        apply.setOnClickListener(v->{
            int chosen=safeInt(input,current,min,max);
            if(distance){maxDistanceMiles=chosen;distanceBar.setProgress(chosen);distanceValue.setText(chosen+" mi");}
            else{minPay=chosen;payBar.setProgress(chosen);payValue.setText("$"+chosen+"+");}
            saveLocalSettings();saveCloudState();refreshForRangeChange(); dlg.dismiss();
        });
        if(isLightUi())lightenDialogTree(box);dlg.setContentView(box); dlg.show();
    }

    private void showFilterSettings(){
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(14),dp(22),dp(24)); box.setBackground(roundBg("#0B1A29",28));
        TextView handle=new TextView(this); LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(dp(42),dp(5)); hp.gravity=Gravity.CENTER_HORIZONTAL; hp.bottomMargin=dp(16); handle.setLayoutParams(hp); handle.setBackground(roundBg("#526A7E",10)); box.addView(handle);
        TextView title=label("Filter jobs",22,"#F4F8FC",true); title.setPadding(0,0,0,dp(4)); box.addView(title);
        TextView sub=label("Use the sliders or type exact values.",13,"#8FA7BA",false); sub.setPadding(0,0,0,dp(18)); box.addView(sub);

        TextView dLabel=label("Distance",15,"#DCE8F2",true); box.addView(dLabel);
        SeekBar d=new SeekBar(this); int distanceMax=extendedDistance?10000:100; d.setMax(distanceMax); d.setProgress(Math.min(maxDistanceMiles,distanceMax)); box.addView(d,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(44)));
        LinearLayout dRow=new LinearLayout(this); dRow.setOrientation(LinearLayout.HORIZONTAL); dRow.setGravity(Gravity.CENTER_VERTICAL);
        EditText dInput=numericField(String.valueOf(maxDistanceMiles),"distance in miles"); dRow.addView(dInput,new LinearLayout.LayoutParams(0,dp(46),1));
        TextView dSuffix=label(" miles",14,"#8FA7BA",false); dRow.addView(dSuffix,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT,dp(46))); box.addView(dRow);

        TextView pLabel=label("Minimum hourly pay",15,"#DCE8F2",true); pLabel.setPadding(0,dp(14),0,0); box.addView(pLabel);
        SeekBar p=new SeekBar(this); p.setMax(100); p.setProgress(minPay); box.addView(p,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(44)));
        LinearLayout pRow=new LinearLayout(this); pRow.setOrientation(LinearLayout.HORIZONTAL); pRow.setGravity(Gravity.CENTER_VERTICAL);
        TextView dollar=label("$",17,"#35E0A1",true); pRow.addView(dollar,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT,dp(46)));
        EditText pInput=numericField(String.valueOf(minPay),"minimum hourly pay"); LinearLayout.LayoutParams pip=new LinearLayout.LayoutParams(0,dp(46),1); pip.leftMargin=dp(8); pRow.addView(pInput,pip);
        TextView pSuffix=label(" / hr +",14,"#8FA7BA",false); pRow.addView(pSuffix,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT,dp(46))); box.addView(pRow);

        // V9.4.35: location-confidence filter. Includes exact employer addresses and
        // high-confidence likely-workplace matches, but hides area-only estimates.
        CheckBox preciseOnly=new CheckBox(this);
        preciseOnly.setText("Exact / likely locations only");
        preciseOnly.setChecked(preciseLocationsOnly);
        preciseOnly.setTextColor(Color.parseColor("#DCE8F2"));
        preciseOnly.setTextSize(15);
        preciseOnly.setPadding(0,dp(14),0,0);
        box.addView(preciseOnly,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)));
        TextView preciseHint=label("Hide jobs that only have a city, ZIP, or broad area estimate.",12,"#8FA7BA",false);
        preciseHint.setPadding(dp(34),0,0,dp(4));
        box.addView(preciseHint);

        d.setOnSeekBarChangeListener(new SimpleSeek(){public void onProgressChanged(SeekBar s,int val,boolean f){int n=Math.max(1,val);if(f)dInput.setText(String.valueOf(n));}});
        p.setOnSeekBarChangeListener(new SimpleSeek(){public void onProgressChanged(SeekBar s,int val,boolean f){if(f)pInput.setText(String.valueOf(Math.max(0,val)));}});

        LinearLayout actions=new LinearLayout(this); actions.setOrientation(LinearLayout.HORIZONTAL); actions.setPadding(0,dp(18),0,0);
        Button reset=new Button(this); reset.setText("Reset"); reset.setAllCaps(false); reset.setTextColor(Color.WHITE); reset.setBackground(roundStrokeBg("#10283A","#31546C",14,1)); LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(0,dp(52),1); rp.rightMargin=dp(8); actions.addView(reset,rp);
        Button apply=new Button(this); apply.setText("Apply filters"); apply.setAllCaps(false); apply.setTypeface(Typeface.DEFAULT,Typeface.BOLD); apply.setTextColor(Color.WHITE); apply.setBackground(roundBg("#2196F3",14)); LinearLayout.LayoutParams ap=new LinearLayout.LayoutParams(0,dp(52),1); ap.leftMargin=dp(8); actions.addView(apply,ap); box.addView(actions);
        reset.setOnClickListener(v->{d.setProgress(25);p.setProgress(15);dInput.setText("25");pInput.setText("15");preciseOnly.setChecked(false);});
        apply.setOnClickListener(v->{
            maxDistanceMiles=safeInt(dInput,Math.max(1,d.getProgress()),1,distanceMax);
            minPay=safeInt(pInput,Math.max(0,p.getProgress()),0,100);
            preciseLocationsOnly=preciseOnly.isChecked();
            distanceBar.setProgress(maxDistanceMiles);payBar.setProgress(minPay);
            distanceValue.setText(maxDistanceMiles+" mi");payValue.setText("$"+minPay+"+");
            saveLocalSettings();saveCloudState();refreshForRangeChange();dlg.dismiss();
        });
        if(isLightUi())lightenDialogTree(box);dlg.setContentView(box); dlg.show();
    }

    private void showJobsLoading(){
        runOnUiThread(() -> {
            if(isFinishing() || isDestroyed()) return;
            if(jobsLoadingDialog!=null && jobsLoadingDialog.isShowing()) return;
            Dialog dlg=new Dialog(this);
            dlg.requestWindowFeature(Window.FEATURE_NO_TITLE);
            dlg.setCancelable(false);

            LinearLayout outer=new LinearLayout(this);
            outer.setGravity(Gravity.CENTER);
            outer.setPadding(dp(28),dp(28),dp(28),dp(28));
            outer.setBackgroundColor(Color.argb(185,4,12,20));

            LinearLayout card=new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setGravity(Gravity.CENTER);
            card.setPadding(dp(34),dp(32),dp(34),dp(32));
            card.setBackground(roundBg("#101D29",22));

            ProgressBar spinner=new ProgressBar(this);
            card.addView(spinner,new LinearLayout.LayoutParams(dp(48),dp(48)));

            TextView title=label("Loading your jobs list",20,"#FFFFFF",true);
            title.setGravity(Gravity.CENTER);
            LinearLayout.LayoutParams tp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT,LinearLayout.LayoutParams.WRAP_CONTENT);
            tp.topMargin=dp(20);
            card.addView(title,tp);

            TextView sub=label("Finding live jobs near your saved location…",14,"#9FB3C3",false);
            sub.setGravity(Gravity.CENTER);
            LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT,LinearLayout.LayoutParams.WRAP_CONTENT);
            sp.topMargin=dp(8);
            card.addView(sub,sp);

            outer.addView(card,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT,LinearLayout.LayoutParams.WRAP_CONTENT));
            dlg.setContentView(outer);
            Window w=dlg.getWindow();
            if(w!=null){
                w.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
                w.setLayout(WindowManager.LayoutParams.MATCH_PARENT,WindowManager.LayoutParams.MATCH_PARENT);
                w.setDimAmount(0f);
            }
            jobsLoadingDialog=dlg;
            dlg.show();
            if(w!=null)w.setLayout(WindowManager.LayoutParams.MATCH_PARENT,WindowManager.LayoutParams.MATCH_PARENT);
        });
    }

    private void hideJobsLoading(){
        runOnUiThread(() -> {
            if(jobsLoadingDialog!=null){
                try{ if(jobsLoadingDialog.isShowing())jobsLoadingDialog.dismiss(); }catch(Exception ignored){}
                jobsLoadingDialog=null;
            }
        });
    }

    private void loadJobs(){
        final String savedWhere=profileLocation();
        if(!haveLocation && savedWhere.isEmpty()){
            if(jobs.isEmpty())applyFilters();
            status.setText("Finding your location…");
            return;
        }

        final String endpoint=jobApiUrl();
        if(endpoint.contains("YOUR_BACKEND_URL")){
            if(jobs.isEmpty())applyFilters();
            status.setText("Job service is not configured");
            return;
        }

        final int generation=++jobLoadGeneration;
        final boolean hadJobs=!jobs.isEmpty();
        status.setText(hadJobs?"Refreshing jobs…":"Loading live jobs…");
        if(!hadJobs)showJobsLoading();

        jobExecutor.execute(()->{
            try{
                String where=!savedWhere.isEmpty()?savedWhere:locationSearchName();
                String requestUrl=buildJobRequestUrl(endpoint,where,savedWhere,false);
                JSONObject root=fetchJobJson(requestUrl);
                JobResponse parsed=parseJobResponse(root);

                if(generation!=jobLoadGeneration)return;
                runOnUiThread(()->{
                    if(generation!=jobLoadGeneration)return;
                    hideJobsLoading();
                    applyJobResponse(parsed,savedWhere,true);
                    boolean refining=root.optBoolean("location_refining",false);
                    String cache=root.optString("cache","");
                    if(refining){
                        status.setText(filtered.isEmpty()?"Jobs loaded • refining locations…":"Jobs loaded • "+filtered.size()+" • refining locations…");
                        requestRefinedJobs(endpoint,where,savedWhere,generation);
                    }else{
                        status.setText(filtered.isEmpty()?"No live jobs found within "+maxDistanceMiles+" miles.":"Live jobs updated • "+filtered.size()+(cache.equals("hit")?" • cached":""));
                    }
                });
            }catch(Exception e){
                if(generation!=jobLoadGeneration)return;
                runOnUiThread(()->{
                    if(generation!=jobLoadGeneration)return;
                    hideJobsLoading();
                    // Keep the last usable map instead of blanking it during a refresh failure.
                    if(jobs.isEmpty()){
                        applyFilters();
                        status.setText("Live jobs temporarily unavailable — no demo listings shown");
                    }else{
                        status.setText("Refresh failed • showing previous live jobs");
                    }
                });
            }
        });
    }

    private String backendSourceParam(){
        if("Adzuna".equalsIgnoreCase(source))return "adzuna";
        if("USAJOBS".equalsIgnoreCase(source))return "usajobs";
        if("The Muse".equalsIgnoreCase(source))return "themuse";
        return "all";
    }

    private String buildJobRequestUrl(String endpoint,String where,String savedWhere,boolean refined)throws Exception{
        StringBuilder url=new StringBuilder(endpoint)
            .append("?where=").append(URLEncoder.encode(where,"UTF-8"))
            .append("&radius=").append(maxDistanceMiles)
            .append("&source=").append(URLEncoder.encode(backendSourceParam(),"UTF-8"));
        if(refined)url.append("&refined=1");
        // Always send the exact saved/search coordinates when we have them. The backend uses
        // these as the authoritative search origin while `where` remains the city/state text
        // that Adzuna and USAJOBS understand. This prevents a pinned point from jumping to an
        // unrelated geocoded city such as Boston.
        if(haveLocation){
            url.append("&lat=").append(userLat).append("&lon=").append(userLon);
        }
        return url.toString();
    }

    private JSONObject fetchJobJson(String requestUrl)throws Exception{
        HttpURLConnection c=(HttpURLConnection)new URL(requestUrl).openConnection();
        c.setConnectTimeout(15000);
        c.setReadTimeout(20000);
        c.setRequestProperty("Accept","application/json");
        int code=c.getResponseCode();
        InputStream in=code>=200&&code<300?c.getInputStream():c.getErrorStream();
        String body=read(in);
        if(code<200||code>=300)throw new IOException("Job API HTTP "+code+": "+body);
        return new JSONObject(body);
    }

    private static final class JobResponse{
        final ArrayList<Job> jobs;
        final double originLat,originLon;
        final boolean gotOrigin;
        JobResponse(ArrayList<Job> jobs,double originLat,double originLon,boolean gotOrigin){
            this.jobs=jobs;this.originLat=originLat;this.originLon=originLon;this.gotOrigin=gotOrigin;
        }
    }

    private JobResponse parseJobResponse(JSONObject root)throws Exception{
        JSONObject origin=root.optJSONObject("search_origin");
        double parsedOriginLat=userLat,parsedOriginLon=userLon;
        if(origin!=null){
            parsedOriginLat=origin.optDouble("latitude",userLat);
            parsedOriginLon=origin.optDouble("longitude",userLon);
        }else{
            parsedOriginLat=root.optDouble("search_latitude",userLat);
            parsedOriginLon=root.optDouble("search_longitude",userLon);
        }
        ArrayList<Job> fresh=new ArrayList<>();
        JSONArray arr=root.optJSONArray("jobs");
        if(arr!=null)for(int i=0;i<arr.length();i++)fresh.add(Job.from(arr.getJSONObject(i)));
        return new JobResponse(fresh,parsedOriginLat,parsedOriginLon,validCoordinate(parsedOriginLat,parsedOriginLon));
    }

    private void applyJobResponse(JobResponse parsed,String savedWhere,boolean recenter){
        if(parsed.gotOrigin){
            userLat=parsed.originLat;userLon=parsed.originLon;haveLocation=true;
            if(!savedWhere.isEmpty())profilePrefs().edit()
                .putLong("location_lat_bits",Double.doubleToRawLongBits(parsed.originLat))
                .putLong("location_lon_bits",Double.doubleToRawLongBits(parsed.originLon)).apply();
            if(recenter)centerOnUser();
        }
        jobs.clear();
        jobs.addAll(parsed.jobs);
        applyFilters();
    }

    private void requestRefinedJobs(String endpoint,String where,String savedWhere,int generation){
        jobExecutor.execute(()->{
            try{
                // The V9.4.23 backend waits on its existing in-flight refinement; it does not
                // start another provider search for this request.
                String refinedUrl=buildJobRequestUrl(endpoint,where,savedWhere,true);
                JSONObject root=fetchJobJson(refinedUrl);
                JobResponse parsed=parseJobResponse(root);
                if(generation!=jobLoadGeneration)return;
                runOnUiThread(()->{
                    if(generation!=jobLoadGeneration)return;
                    applyJobResponse(parsed,savedWhere,false);
                    boolean stillRefining=root.optBoolean("location_refining",false);
                    status.setText(filtered.isEmpty()?"No live jobs found within "+maxDistanceMiles+" miles.":
                        (stillRefining?"Live jobs • "+filtered.size()+" • locations still refining":"Live jobs updated • "+filtered.size()+" • locations refined"));
                });
            }catch(Exception ignored){
                // Quick results are already usable. A failed refinement should never erase them.
            }
        });
    }
    private String read(InputStream in)throws Exception{BufferedReader r=new BufferedReader(new InputStreamReader(in));StringBuilder s=new StringBuilder();String x;while((x=r.readLine())!=null)s.append(x);return s.toString();}
    private String locationSearchName(){
        if(!profileLocation().isEmpty())return profileLocation();
        try{
            Geocoder g=new Geocoder(this,Locale.US);
            List<Address> a=g.getFromLocation(userLat,userLon,1);
            if(a!=null&&!a.isEmpty()){
                Address x=a.get(0);
                String city=x.getLocality(); if(city==null||city.trim().isEmpty()) city=x.getSubAdminArea();
                String state=x.getAdminArea();
                if(city!=null&&!city.trim().isEmpty()) return state==null||state.trim().isEmpty()?city:city+", "+state;
            }
        }catch(Exception ignored){}
        return String.format(Locale.US,"%.5f,%.5f",userLat,userLon);
    }
    private void correctJobCoordinates(List<Job> list){
        // V9.4.6: server-side Geoapify is authoritative for likely-workplace matches.
        // Exact and likely coordinates returned by the backend are preserved unchanged.
        // If Geoapify could not confidently match a workplace, only geocode the broad
        // provider location as a fallback; do not invent another company match on-device.
        HashMap<String,Address> listingCache=new HashMap<>();
        Geocoder geocoder=new Geocoder(this,Locale.US);
        for(Job j:list){
            if(j==null)continue;
            if(("exact".equals(j.locationPrecision) || "likely".equals(j.locationPrecision)) && validCoordinate(j.lat,j.lon))continue;
            String place=j.location==null?"":j.location.trim();
            if(place.isEmpty())continue;
            try{
                Address listing=listingCache.get(place.toLowerCase(Locale.US));
                if(listing==null){
                    List<Address> matches=geocoder.getFromLocationName(place,5);
                    if(matches!=null&&!matches.isEmpty()){
                        listing=chooseBestListingLocation(matches,place);
                        if(listing!=null)listingCache.put(place.toLowerCase(Locale.US),listing);
                    }
                }
                if(listing!=null){
                    j.lat=listing.getLatitude();
                    j.lon=listing.getLongitude();
                    if(looksLikeStreetAddress(place)){
                        j.locationApproximate=false;
                        j.locationPrecision="exact";
                    }else{
                        j.locationApproximate=true;
                        j.locationPrecision="area";
                    }
                }else{
                    j.locationApproximate=!looksLikeStreetAddress(place);
                    j.locationPrecision=j.locationApproximate?"area":"exact";
                }
            }catch(Exception ignored){
                j.locationApproximate=!looksLikeStreetAddress(place);
                j.locationPrecision=j.locationApproximate?"area":"exact";
            }
        }
    }
    private Address chooseBestListingLocation(List<Address> matches,String listingLocation){
        if(matches==null||matches.isEmpty())return null;
        String want=listingLocation==null?"":listingLocation.toLowerCase(Locale.US);
        Address best=matches.get(0);int bestScore=-1;
        for(Address a:matches){
            if(a==null)continue;int score=0;
            String locality=low(a.getLocality()),subAdmin=low(a.getSubAdminArea()),admin=low(a.getAdminArea()),postal=low(a.getPostalCode()),feature=low(a.getFeatureName());
            if(!locality.isEmpty()&&want.contains(locality))score+=8;
            if(!subAdmin.isEmpty()&&want.contains(subAdmin))score+=5;
            if(!admin.isEmpty()&&want.contains(admin))score+=4;
            if(!postal.isEmpty()&&want.contains(postal))score+=8;
            if(!feature.isEmpty()&&want.contains(feature))score+=3;
            if(score>bestScore){bestScore=score;best=a;}
        }
        return best;
    }
    private Address chooseCompanyLocation(List<Address> matches,String company,String place,Address area,double providerLat,double providerLon){
        if(matches==null||matches.isEmpty())return null;
        String companyNorm=normalizeCompany(company);Address best=null;int bestScore=Integer.MIN_VALUE;
        for(Address a:matches){
            if(a==null)continue;
            double anchorLat=area!=null?area.getLatitude():providerLat,anchorLon=area!=null?area.getLongitude():providerLon;
            if(validCoordinate(anchorLat,anchorLon)){
                float[] d=new float[1];Location.distanceBetween(anchorLat,anchorLon,a.getLatitude(),a.getLongitude(),d);
                if(d[0]>32186)continue; // reject results more than 20 miles from provider/listing area
            }
            String hay=(low(a.getFeatureName())+" "+low(a.getPremises())+" "+low(a.getAddressLine(0))).trim();
            int score=0;
            if(companyTokensMatch(hay,companyNorm))score+=14;
            if(a.getThoroughfare()!=null)score+=5;
            if(a.getPremises()!=null)score+=3;
            String locality=low(a.getLocality()),admin=low(a.getAdminArea()),postal=low(a.getPostalCode()),want=low(place);
            if(!locality.isEmpty()&&want.contains(locality))score+=7;
            if(!admin.isEmpty()&&want.contains(admin))score+=3;
            if(!postal.isEmpty()&&want.contains(postal))score+=5;
            if(score>bestScore){bestScore=score;best=a;}
        }
        return bestScore>=12?best:null;
    }
    private String low(String x){return x==null?"":x.toLowerCase(Locale.US);}
    private String normalizeCompany(String x){return low(x).replaceAll("[^a-z0-9 ]"," ").replaceAll("\\b(inc|llc|corp|corporation|company|co|ltd|the)\\b"," ").replaceAll("\\s+"," ").trim();}
    private boolean companyTokensMatch(String hay,String companyNorm){
        if(companyNorm.isEmpty())return false;int hits=0,total=0;
        for(String t:companyNorm.split("\\s+")){if(t.length()<3)continue;total++;if(hay.contains(t))hits++;}
        return total>0 && hits>=Math.min(2,total);
    }
    private boolean isGenericCompanyName(String c){String x=normalizeCompany(c);return x.isEmpty()||x.equals("employer")||x.equals("unknown")||x.equals("confidential")||x.equals("staffing");}
    private String bestAddressText(Address a,String fallback){
        if(a==null)return fallback;String line=a.getAddressLine(0);
        if(line!=null&&!line.trim().isEmpty())return line.trim();
        StringBuilder b=new StringBuilder();if(a.getSubThoroughfare()!=null)b.append(a.getSubThoroughfare()).append(' ');if(a.getThoroughfare()!=null)b.append(a.getThoroughfare());
        if(a.getLocality()!=null){if(b.length()>0)b.append(", ");b.append(a.getLocality());}if(a.getAdminArea()!=null){if(b.length()>0)b.append(", ");b.append(a.getAdminArea());}
        return b.length()>0?b.toString():fallback;
    }
    private boolean looksLikeStreetAddress(String place){
        if(place==null)return false;String x=place.trim().toLowerCase(Locale.US);if(!x.matches(".*\\d+.*"))return false;
        return x.matches(".*\\b(st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|ln|lane|way|ct|court|pl|place|pkwy|parkway|hwy|highway|suite|ste)\\b.*");
    }
    private boolean validCoordinate(double lat,double lon){return lat>=-90&&lat<=90&&lon>=-180&&lon<=180&&!(Math.abs(lat)<0.0001&&Math.abs(lon)<0.0001);}
    private boolean hasPreciseLocation(Job j){
        if(j==null)return false;
        String p=j.locationPrecision==null?"":j.locationPrecision.trim().toLowerCase(Locale.US);
        return "exact".equals(p)||"likely".equals(p)||(!j.locationApproximate&&validCoordinate(j.lat,j.lon));
    }

    // V9.4.40: a likely/high-confidence workplace is presented as a resolved job pin.
    // Only broad area-level estimates carry the "approx. location" label/halo.
    private boolean shouldShowApproxLocation(Job j){ return j==null || !hasPreciseLocation(j); }

    private boolean pileHasPreciseLocation(ArrayList<Integer> pile){
        if(pile==null||pile.isEmpty())return false;
        for(Integer idx:pile){
            if(idx!=null&&idx>=0&&idx<filtered.size()&&hasPreciseLocation(filtered.get(idx)))return true;
        }
        return false;
    }

    private String displayLocation(Job j){
        if(j.location!=null&&!j.location.trim().isEmpty()){
            if("likely".equals(j.locationPrecision))return j.location.trim()+" (likely workplace)";
            if(j.locationApproximate)return j.location.trim()+" (approx. area)";
            return j.location.trim();
        }
        try{Geocoder g=new Geocoder(this,Locale.US);List<Address>a=g.getFromLocation(j.lat,j.lon,1);if(a!=null&&!a.isEmpty()){Address x=a.get(0);String city=x.getLocality();if(city==null||city.trim().isEmpty())city=x.getSubAdminArea();String state=x.getAdminArea();if(city!=null&&!city.trim().isEmpty())return state==null||state.trim().isEmpty()?city:city+", "+state;}}catch(Exception ignored){}
        return "Location provided by employer";
    }
    private void applyFilters(){
        filtered.clear();
        for(Job j:jobs){
            double d=distanceMiles(userLat,userLon,j.lat,j.lon);
            boolean ok=d<=maxDistanceMiles&&(j.pay<=0||j.pay>=minPay)&&(source.equals("All sources")||j.source.equalsIgnoreCase(source))&&(category.equals("All jobs")||j.category.equalsIgnoreCase(category))&&(!preciseLocationsOnly||hasPreciseLocation(j));
            if(ok)filtered.add(j);
        }
        resultCount.setText(filtered.size()+" jobs");
        if(!mapReady || googleMap==null)return;

        // Capture the old pile position before removing markers. If one of those jobs becomes
        // an individual bubble at the new zoom, render it at this old center first and animate
        // it outward to its true/display position.
        splitAnimationStarts.clear();
        for(Marker oldMarker:jobMarkers){
            try{
                Object oldTag=oldMarker.getTag();
                if(oldTag instanceof ClusterTag){
                    ClusterTag oldPile=(ClusterTag)oldTag;
                    for(Integer idx:oldPile.jobIndexes){
                        if(idx!=null) splitAnimationStarts.put(idx,oldPile.center);
                    }
                }
            }catch(Exception ignored){}
        }
        for(Marker m:jobMarkers){try{m.remove();}catch(Exception ignored){}}
        jobMarkers.clear();
        for(Polyline p:pileSpokes){try{p.remove();}catch(Exception ignored){}}
        pileSpokes.clear();
        for(Circle c:approxCircles){try{c.remove();}catch(Exception ignored){}} approxCircles.clear();

        final float zoom=googleMap.getCameraPosition().zoom;
        final ArrayList<ArrayList<Integer>> piles=buildJobPiles(zoom);

        for(ArrayList<Integer> pile:piles){
            if(pile.isEmpty())continue;

            if(pile.size()==1){
                int i=pile.get(0);
                renderSingleJobMarker(i,new LatLng(filtered.get(i).lat,filtered.get(i).lon),zoom);
                continue;
            }

            // At close zoom, provider feeds often still give several jobs the exact same
            // coordinate. Screen-distance clustering can never separate those naturally, so
            // progressively fan a limited number out around the true anchor as a UI treatment.
            // The center pile remains for the undisclosed remainder and no fake coordinate is
            // persisted back into the job data.
            if(zoom>=17.2f && pile.size()<=5 && pileMaxSeparationMeters(pile)<=45.0){
                renderProgressivelyExpandedPile(pile,zoom);
                continue;
            }

            LatLng center=pileRepresentativePoint(pile);
            Marker m=googleMap.addMarker(new MarkerOptions()
                .position(center)
                .icon(BitmapDescriptorFactory.fromBitmap(makeJobPileBitmap(pile)))
                .anchor(0.50f,0.73f)
                .zIndex(7f));
            if(m!=null){
                m.setTag(new ClusterTag(new ArrayList<>(pile),center));
                jobMarkers.add(m);
            }
        }
    }

    private ArrayList<ArrayList<Integer>> buildJobPiles(float zoom){
        ArrayList<ArrayList<Integer>> groups=new ArrayList<>();
        if(googleMap==null||filtered.isEmpty())return groups;

        // V9.4.38 performance: spatial buckets replace the old all-pairs scan. We keep
        // the same connected-component behavior, but each job only checks jobs in its
        // own screen-space cell and the eight neighboring cells. This scales much better
        // when a search returns a large number of jobs.
        final int n=filtered.size();
        final android.graphics.Point[] pts=new android.graphics.Point[n];
        final int xThresholdPx=dp(jobPileThresholdDp(zoom));
        final int yThresholdPx=dp(Math.max(26,Math.round(jobPileThresholdDp(zoom)*0.68f)));
        final HashMap<String,ArrayList<Integer>> buckets=new HashMap<>();
        try{
            for(int i=0;i<n;i++){
                Job j=filtered.get(i);
                pts[i]=googleMap.getProjection().toScreenLocation(new LatLng(j.lat,j.lon));
                int cx=Math.floorDiv(pts[i].x,Math.max(1,xThresholdPx));
                int cy=Math.floorDiv(pts[i].y,Math.max(1,yThresholdPx));
                String key=(hasPreciseLocation(j)?"p":"a")+":"+cx+":"+cy;
                ArrayList<Integer> bucket=buckets.get(key);
                if(bucket==null){bucket=new ArrayList<>();buckets.put(key,bucket);}
                bucket.add(i);
            }

            boolean[] seen=new boolean[n];
            for(int i=0;i<n;i++){
                if(seen[i])continue;
                ArrayList<Integer> group=new ArrayList<>();
                ArrayList<Integer> queue=new ArrayList<>();
                queue.add(i);seen[i]=true;
                for(int q=0;q<queue.size();q++){
                    int a=queue.get(q);group.add(a);
                    android.graphics.Point pa=pts[a];
                    boolean precise=hasPreciseLocation(filtered.get(a));
                    int acx=Math.floorDiv(pa.x,Math.max(1,xThresholdPx));
                    int acy=Math.floorDiv(pa.y,Math.max(1,yThresholdPx));
                    String prefix=precise?"p:":"a:";
                    for(int ox=-1;ox<=1;ox++){
                        for(int oy=-1;oy<=1;oy++){
                            ArrayList<Integer> bucket=buckets.get(prefix+(acx+ox)+":"+(acy+oy));
                            if(bucket==null)continue;
                            for(Integer b:bucket){
                                if(b==null||seen[b])continue;
                                android.graphics.Point pb=pts[b];
                                if(Math.abs(pa.x-pb.x)<=xThresholdPx && Math.abs(pa.y-pb.y)<=yThresholdPx){
                                    seen[b]=true;queue.add(b);
                                }
                            }
                        }
                    }
                }
                groups.add(group);
            }
        }catch(Exception ignored){
            groups.clear();
            for(int i=0;i<n;i++){ArrayList<Integer> one=new ArrayList<>();one.add(i);groups.add(one);}
        }
        return groups;
    }

    private int jobPileThresholdDp(float zoom){
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

    private LatLng pileCenter(ArrayList<Integer> pile){
        if(pile==null||pile.isEmpty())return googleMap!=null?googleMap.getCameraPosition().target:new LatLng(userLat,userLon);
        double lat=0,lon=0;int n=0;
        for(Integer idx:pile){
            if(idx==null||idx<0||idx>=filtered.size())continue;
            Job j=filtered.get(idx);lat+=j.lat;lon+=j.lon;n++;
        }
        if(n==0)return new LatLng(userLat,userLon);
        return new LatLng(lat/n,lon/n);
    }

    private LatLng pileRepresentativePoint(ArrayList<Integer> pile){
        LatLng mean=pileCenter(pile);
        double best=Double.MAX_VALUE;LatLng result=mean;
        for(Integer idx:pile){
            if(idx==null||idx<0||idx>=filtered.size())continue;
            Job j=filtered.get(idx);
            double d=distanceMiles(mean.latitude,mean.longitude,j.lat,j.lon);
            if(d<best){best=d;result=new LatLng(j.lat,j.lon);}
        }
        return result;
    }

    private double pileMaxSeparationMeters(ArrayList<Integer> pile){
        double max=0;
        for(int a=0;a<pile.size();a++){
            Integer ia=pile.get(a);if(ia==null||ia<0||ia>=filtered.size())continue;
            Job ja=filtered.get(ia);
            for(int b=a+1;b<pile.size();b++){
                Integer ib=pile.get(b);if(ib==null||ib<0||ib>=filtered.size())continue;
                Job jb=filtered.get(ib);
                max=Math.max(max,distanceMiles(ja.lat,ja.lon,jb.lat,jb.lon)*1609.344);
            }
        }
        return max;
    }

    private void renderSingleJobMarker(int index,LatLng position,float zoom){
        if(index<0||index>=filtered.size())return;
        Job j=filtered.get(index);
        addApproxHalo(j,zoom);
        float markerAnchorY=shouldShowApproxLocation(j)?0.734f:0.705f;
        LatLng start=splitAnimationStarts.get(index);
        boolean animate=start!=null && distanceMiles(start.latitude,start.longitude,position.latitude,position.longitude)>0.0008;
        Marker m=googleMap.addMarker(new MarkerOptions()
            .position(animate?start:position)
            .icon(BitmapDescriptorFactory.fromBitmap(makeJobMarkerBitmap(j)))
            .anchor(0.293f,markerAnchorY)
            .zIndex(isTracked(j)?10f:5f));
        if(m!=null){
            m.setTag(index);jobMarkers.add(m);
            if(animate) animateMarkerTo(m,start,position,index%5);
        }
    }

    private void animateMarkerTo(final Marker marker,final LatLng from,final LatLng to,int stagger){
        if(marker==null||from==null||to==null)return;
        final ValueAnimator animator=ValueAnimator.ofFloat(0f,1f);
        animator.setStartDelay(Math.max(0,stagger)*28L);
        animator.setDuration(320L);
        animator.setInterpolator(new android.view.animation.DecelerateInterpolator());
        animator.addUpdateListener(a -> {
            try{
                float t=(Float)a.getAnimatedValue();
                // A small ease-out arc keeps the separation readable without feeling bouncy.
                double lat=from.latitude+(to.latitude-from.latitude)*t;
                double lon=from.longitude+(to.longitude-from.longitude)*t;
                marker.setPosition(new LatLng(lat,lon));
                marker.setAlpha(Math.min(1f,0.72f+0.28f*t));
            }catch(Exception ignored){}
        });
        animator.start();
    }

    private void renderProgressivelyExpandedPile(ArrayList<Integer> pile,float zoom){
        if(pile==null||pile.isEmpty())return;
        LatLng center=pileRepresentativePoint(pile);
        android.graphics.Point base;
        try{base=googleMap.getProjection().toScreenLocation(center);}catch(Exception e){
            Marker m=googleMap.addMarker(new MarkerOptions().position(center)
                .icon(BitmapDescriptorFactory.fromBitmap(makeJobPileBitmap(pile))).anchor(0.50f,0.73f).zIndex(7f));
            if(m!=null){m.setTag(new ClusterTag(new ArrayList<>(pile),center));jobMarkers.add(m);}return;
        }

        final int reveal=zoom>=18.8f?Math.min(5,pile.size()):zoom>=17.9f?Math.min(4,pile.size()):Math.min(3,pile.size());
        final float radiusDp=zoom>=18.8f?196f:zoom>=17.9f?172f:148f;
        final float radius=radiusDp*getResources().getDisplayMetrics().density;
        final ArrayList<Integer> remainder=new ArrayList<>();

        for(int k=0;k<pile.size();k++){
            if(k>=reveal){remainder.add(pile.get(k));continue;}
            int idx=pile.get(k);
            // Rotate the first bubble upward and distribute the rest evenly. A larger radius than
            // the old fan-out accounts for the full 188dp marker card, not just the logo circle.
            double angle=(-Math.PI/2.0)+(2.0*Math.PI*k/Math.max(1,reveal));
            int x=Math.round(base.x+(float)Math.cos(angle)*radius);
            int y=Math.round(base.y+(float)Math.sin(angle)*radius*0.78f);
            LatLng display;
            try{display=googleMap.getProjection().fromScreenLocation(new android.graphics.Point(x,y));}
            catch(Exception e){display=center;}
            renderSingleJobMarker(idx,display,zoom);
        }

        if(!remainder.isEmpty()){
            Marker m=googleMap.addMarker(new MarkerOptions().position(center)
                .icon(BitmapDescriptorFactory.fromBitmap(makeJobPileBitmap(remainder)))
                .anchor(0.50f,0.73f).zIndex(8f));
            if(m!=null){m.setTag(new ClusterTag(new ArrayList<>(remainder),center));jobMarkers.add(m);}
        }
    }

    private void renderExpandedPile(ArrayList<Integer> pile,float zoom){
        LatLng center=pileRepresentativePoint(pile);
        android.graphics.Point base;
        try{base=googleMap.getProjection().toScreenLocation(center);}catch(Exception e){
            for(Integer idx:pile){Job j=filtered.get(idx);renderSingleJobMarker(idx,new LatLng(j.lat,j.lon),zoom);}return;
        }

        int n=pile.size();
        float radius=dp(n<=4?48:n<=8?62:76);
        for(int k=0;k<n;k++){
            int idx=pile.get(k);
            double angle=(-Math.PI/2.0)+(2.0*Math.PI*k/Math.max(1,n));
            float ring=(k>=10?1.28f:1f);
            int x=Math.round(base.x+(float)Math.cos(angle)*radius*ring);
            int y=Math.round(base.y+(float)Math.sin(angle)*radius*0.76f*ring);
            LatLng display;
            try{display=googleMap.getProjection().fromScreenLocation(new android.graphics.Point(x,y));}
            catch(Exception e){display=center;}
            try{
                Polyline spoke=googleMap.addPolyline(new PolylineOptions().add(center,display).width(dp(1)).color(Color.argb(105,170,190,205)).zIndex(3f));
                pileSpokes.add(spoke);
            }catch(Exception ignored){}
            renderSingleJobMarker(idx,display,zoom);
        }
    }


    private void showClusterSideList(ClusterTag cluster){
        if(cluster==null||cluster.jobIndexes==null||cluster.jobIndexes.isEmpty())return;
        final Dialog d=new Dialog(this);
        d.requestWindowFeature(Window.FEATURE_NO_TITLE);

        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(14),dp(16),dp(14),dp(14));
        GradientDrawable bg=new GradientDrawable();
        bg.setColor(mapTheme.equals("dark")?Color.rgb(28,35,48):Color.rgb(247,248,251));
        bg.setCornerRadii(new float[]{dp(22),dp(22),0,0,0,0,dp(22),dp(22)});
        root.setBackground(bg);

        TextView title=new TextView(this);
        title.setText(cluster.jobIndexes.size()+" jobs here");
        title.setTextSize(20);
        title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        title.setTextColor(mapTheme.equals("dark")?Color.WHITE:Color.rgb(31,34,43));
        root.addView(title,new LinearLayout.LayoutParams(-1,-2));

        TextView hint=new TextView(this);
        hint.setText("Tap a job to open it");
        hint.setTextSize(13);
        hint.setTextColor(mapTheme.equals("dark")?Color.LTGRAY:Color.DKGRAY);
        LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(-1,-2);hp.bottomMargin=dp(10);root.addView(hint,hp);

        ScrollView scroll=new ScrollView(this);
        LinearLayout list=new LinearLayout(this);list.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(list,new ScrollView.LayoutParams(-1,-2));

        for(Integer idx:cluster.jobIndexes){
            if(idx==null||idx<0||idx>=filtered.size())continue;
            Job j=filtered.get(idx);
            LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.VERTICAL);
            row.setPadding(dp(12),dp(11),dp(12),dp(11));
            GradientDrawable rb=new GradientDrawable();
            rb.setColor(mapTheme.equals("dark")?Color.rgb(39,48,64):Color.WHITE);
            rb.setCornerRadius(dp(14));
            rb.setStroke(dp(1),mapTheme.equals("dark")?Color.rgb(70,81,99):Color.rgb(220,223,230));
            row.setBackground(rb);

            TextView pay=new TextView(this);
            pay.setText(j.pay>0?String.format(Locale.US,"$%.2f/hr",j.pay):"Pay not listed");
            pay.setTextSize(17);pay.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
            pay.setTextColor(j.pay>0?Color.rgb(25,181,131):(mapTheme.equals("dark")?Color.LTGRAY:Color.DKGRAY));
            row.addView(pay);

            TextView jt=new TextView(this);jt.setText(j.title);jt.setTextSize(15);jt.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
            jt.setMaxLines(2);jt.setTextColor(mapTheme.equals("dark")?Color.WHITE:Color.rgb(35,38,47));row.addView(jt);

            TextView meta=new TextView(this);
            String comp=(j.company==null||j.company.trim().isEmpty())?j.source:j.company;
            double dist=distanceMiles(userLat,userLon,j.lat,j.lon);
            meta.setText(comp+"  •  "+String.format(Locale.US,"%.1f mi",dist));
            meta.setTextSize(12);meta.setTextColor(mapTheme.equals("dark")?Color.LTGRAY:Color.GRAY);row.addView(meta);

            row.setOnClickListener(v -> {d.dismiss();showJob(j);});
            LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(-1,-2);rp.bottomMargin=dp(9);list.addView(row,rp);
        }
        root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1f));
        d.setContentView(root);
        Window w=d.getWindow();
        if(w!=null){
            w.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
            w.setGravity(Gravity.RIGHT|Gravity.CENTER_VERTICAL);
            WindowManager.LayoutParams lp=new WindowManager.LayoutParams();
            lp.copyFrom(w.getAttributes());
            lp.width=(int)(getResources().getDisplayMetrics().widthPixels*0.72f);
            lp.height=(int)(getResources().getDisplayMetrics().heightPixels*0.70f);
            lp.dimAmount=0.18f;
            w.setAttributes(lp);
            w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
        }
        d.show();
    }

    private void addApproxHalo(Job j,float zoom){
        if(!shouldShowApproxLocation(j) || zoom<13.5f)return;
        double precision=approxRadiusMeters(j);
        double visual=Math.min(precision, visualApproxRadiusMeters(zoom));
        LatLng center=new LatLng(j.lat,j.lon);
        Circle outer=googleMap.addCircle(new CircleOptions().center(center).radius(visual).fillColor(Color.argb(18,78,190,240)).strokeColor(Color.argb(105,103,204,247)).strokeWidth(dp(1))); approxCircles.add(outer);
        Circle mid=googleMap.addCircle(new CircleOptions().center(center).radius(visual*0.72).fillColor(Color.argb(18,102,210,250)).strokeColor(Color.argb(55,125,218,252)).strokeWidth(dp(1))); approxCircles.add(mid);
        Circle inner=googleMap.addCircle(new CircleOptions().center(center).radius(visual*0.42).fillColor(Color.argb(22,143,226,255)).strokeColor(Color.TRANSPARENT).strokeWidth(0)); approxCircles.add(inner);
    }

    private Bitmap makeJobPileBitmap(ArrayList<Integer> pile){
        final int w=dp(156),h=dp(94);
        Bitmap bitmap=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);
        android.graphics.Canvas c=new android.graphics.Canvas(bitmap);
        boolean light=isLightUi();

        android.graphics.Paint shadow=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        shadow.setColor(Color.argb(72,0,0,0));
        c.drawRoundRect(new android.graphics.RectF(dp(12),dp(7),dp(146),dp(62)),dp(16),dp(16),shadow);

        android.graphics.Paint bg=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        bg.setColor(Color.parseColor(light?"#ECEEF1":"#091B29"));
        c.drawRoundRect(new android.graphics.RectF(dp(10),dp(4),dp(144),dp(59)),dp(16),dp(16),bg);
        android.graphics.Paint stroke=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        stroke.setStyle(android.graphics.Paint.Style.STROKE);stroke.setStrokeWidth(dp(1));
        stroke.setColor(Color.parseColor(light?"#AEB4BC":"#667985"));
        c.drawRoundRect(new android.graphics.RectF(dp(10),dp(4),dp(144),dp(59)),dp(16),dp(16),stroke);

        android.graphics.Paint text=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        text.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        text.setTextSize(dp(14));text.setColor(Color.parseColor("#35E0A1"));
        c.drawText(pilePayText(pile),dp(23),dp(27),text);
        text.setTextSize(dp(10));
        boolean precisePile=pileHasPreciseLocation(pile);
        text.setColor(Color.parseColor(precisePile?(light?"#252A30":"#F4F8FB"):"#4AAED8"));
        c.drawText(pile.size()+(precisePile?" jobs here":" approx. jobs"),dp(23),dp(46),text);

        // Three overlapping discs make the marker read as a physical pile rather than a generic pin.
        float cy=dp(72),r=dp(18);
        int show=Math.min(3,pile.size());
        for(int k=show-1;k>=0;k--){
            Job j=filtered.get(pile.get(k));
            float cx=dp(48+k*25);
            android.graphics.Paint disk=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            disk.setColor(Color.parseColor(companyColor(j.company,j.category)));
            c.drawCircle(cx,cy,r,disk);
            android.graphics.Paint rim=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            rim.setStyle(android.graphics.Paint.Style.STROKE);rim.setStrokeWidth(dp(2));rim.setColor(Color.parseColor("#D5DADF"));
            c.drawCircle(cx,cy,r-dp(1),rim);
            android.graphics.Paint white=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);white.setColor(Color.WHITE);
            c.drawCircle(cx,cy,dp(13),white);
            android.graphics.Paint badge=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            badge.setTextAlign(android.graphics.Paint.Align.CENTER);badge.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);badge.setTextSize(dp(8));
            badge.setColor(Color.parseColor(companyColor(j.company,j.category)));
            String b=companyBadge(j.company).replace("\n"," ");if(b.length()>3)b=b.substring(0,3);
            android.graphics.Paint.FontMetrics fm=badge.getFontMetrics();c.drawText(b,cx,cy-(fm.ascent+fm.descent)/2f,badge);
        }
        if(pile.size()>3){
            float cx=dp(124),cy2=dp(72);
            android.graphics.Paint countBg=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);countBg.setColor(Color.parseColor(light?"#303943":"#183549"));c.drawCircle(cx,cy2,dp(17),countBg);
            android.graphics.Paint count=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);count.setTextAlign(android.graphics.Paint.Align.CENTER);count.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);count.setTextSize(dp(9));count.setColor(Color.WHITE);
            android.graphics.Paint.FontMetrics fm=count.getFontMetrics();c.drawText("+"+(pile.size()-3),cx,cy2-(fm.ascent+fm.descent)/2f,count);
        }
        return bitmap;
    }

    private String pilePayText(ArrayList<Integer> pile){
        double min=Double.MAX_VALUE,max=0;
        for(Integer idx:pile){if(idx==null||idx<0||idx>=filtered.size())continue;double p=filtered.get(idx).pay;if(p>0){min=Math.min(min,p);max=Math.max(max,p);}}
        if(min==Double.MAX_VALUE)return pile.size()+" jobs";
        if(Math.abs(max-min)<0.01)return "$"+money(min)+"/hr";
        return "$"+money(min)+"–$"+money(max)+"/hr";
    }

    private double approxRadiusMeters(Job j){if("likely".equals(j.locationPrecision))return 220;String l=j.location==null?"":j.location.toLowerCase(Locale.US);if(l.matches(".*\\b\\d{1,6}\\s+.*"))return 180;if(l.contains("county"))return 5000;if(l.contains(","))return 1200;return 2500;}
    private double visualApproxRadiusMeters(float zoom){
        // Screen-friendly cap: shrinks in geographic size as the user zooms in.
        if(zoom>=17f)return 90;
        if(zoom>=16f)return 140;
        if(zoom>=15f)return 220;
        if(zoom>=14f)return 340;
        return 480;
    }

    private void updateZoomFocusTransparency(){
        if(!mapReady || googleMap==null || jobMarkers.isEmpty())return;
        float zoom=googleMap.getCameraPosition().zoom;

        // Keep everything fully visible until the user starts zooming into an individual job.
        if(zoom<13.75f){
            for(Marker marker:jobMarkers){ try{ marker.setAlpha(1f); }catch(Exception ignored){} }
            return;
        }

        try{
            android.graphics.Point targetPoint=googleMap.getProjection().toScreenLocation(googleMap.getCameraPosition().target);
            Marker focused=null;
            double nearest=Double.MAX_VALUE;
            for(Marker marker:jobMarkers){
                android.graphics.Point point=googleMap.getProjection().toScreenLocation(marker.getPosition());
                double dx=point.x-targetPoint.x;
                double dy=point.y-targetPoint.y;
                double distance=Math.sqrt(dx*dx+dy*dy);
                if(distance<nearest){ nearest=distance; focused=marker; }
            }

            // A job only becomes the focus when the camera is actually centered close to it.
            if(focused==null || nearest>dp(145)){
                for(Marker marker:jobMarkers){ try{ marker.setAlpha(1f); }catch(Exception ignored){} }
                return;
            }

            // Other jobs fade progressively as zoom increases. The focused job stays crisp.
            float otherAlpha=1f-((zoom-13.75f)*0.19f);
            otherAlpha=Math.max(0.18f,Math.min(1f,otherAlpha));
            for(Marker marker:jobMarkers){
                try{ marker.setAlpha(marker==focused?1f:otherAlpha); }catch(Exception ignored){}
            }
        }catch(Exception ignored){
            for(Marker marker:jobMarkers){ try{ marker.setAlpha(1f); }catch(Exception ignored2){} }
        }
    }
    private String money(double x){return String.format(Locale.US,"%.1f",x);} private double distanceMiles(double a,double b,double c,double d){double R=3958.761,p=Math.toRadians(c-a),q=Math.toRadians(d-b),x=Math.sin(p/2)*Math.sin(p/2)+Math.cos(Math.toRadians(a))*Math.cos(Math.toRadians(c))*Math.sin(q/2)*Math.sin(q/2);return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));}

    private void showJob(Job j){
        Dialog dlg=new Dialog(this);
        dlg.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(20),dp(10),dp(20),dp(8)); box.setBackgroundColor(Color.TRANSPARENT);

        TextView handle=new TextView(this); LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(dp(42),dp(5)); hp.gravity=Gravity.CENTER_HORIZONTAL; hp.bottomMargin=dp(14); handle.setLayoutParams(hp); handle.setBackground(roundBg("#657D90",10)); box.addView(handle);

        LinearLayout head=new LinearLayout(this); head.setOrientation(LinearLayout.HORIZONTAL); head.setGravity(Gravity.CENTER_VERTICAL);
        TextView logo=label(companyBadge(j.company),companyLogoTextSize(j.company),companyLogoTextColor(j.company),true); logo.setGravity(Gravity.CENTER); logo.setBackground(roundBg(companyColor(j.company,j.category),16)); head.addView(logo,new LinearLayout.LayoutParams(dp(56),dp(56)));
        LinearLayout titleBlock=new LinearLayout(this); titleBlock.setOrientation(LinearLayout.VERTICAL); titleBlock.setPadding(dp(14),0,dp(6),0);
        TextView title=label(j.title,20,"#F7FAFC",true); title.setMaxLines(2); title.setEllipsize(android.text.TextUtils.TruncateAt.END); titleBlock.addView(title);
        TextView company=label(j.company,14,"#A7BAC9",true); company.setMaxLines(1); company.setEllipsize(android.text.TextUtils.TruncateAt.END); titleBlock.addView(company);
        head.addView(titleBlock,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1));
        TextView close=label("×",28,"#9EB1C0",false); close.setGravity(Gravity.CENTER); close.setBackground(roundBg("#13283A",30)); close.setOnClickListener(v->dlg.dismiss()); head.addView(close,new LinearLayout.LayoutParams(dp(42),dp(42))); box.addView(head);

        double miles=distanceMiles(userLat,userLon,j.lat,j.lon);
        LinearLayout meta=new LinearLayout(this); meta.setOrientation(LinearLayout.HORIZONTAL); meta.setGravity(Gravity.CENTER_VERTICAL); meta.setPadding(dp(70),dp(2),0,dp(10));
        TextView source=label((j.source==null||j.source.trim().isEmpty()?"Job listing":j.source)+"  •  "+money(miles)+" mi away",12,"#8199AA",false); meta.addView(source); box.addView(meta);

        LinearLayout payRow=new LinearLayout(this); payRow.setOrientation(LinearLayout.HORIZONTAL); payRow.setGravity(Gravity.CENTER_VERTICAL); payRow.setPadding(0,dp(4),0,dp(12));
        TextView pay=label("$"+money(j.pay)+"/hr",23,"#35E0A1",true); payRow.addView(pay); Space gap=new Space(this); payRow.addView(gap,new LinearLayout.LayoutParams(0,1,1));
        TextView type=label(jobType(j),12,isLightUi()?"#6B3500":"#FFD19A",true); type.setPadding(dp(14),dp(7),dp(14),dp(7)); type.setBackground(roundStrokeBg(isLightUi()?"#FFE4C4":"#3A2B18",isLightUi()?"#D79A58":"#72502A",20,1)); type.setMaxLines(1); type.setSingleLine(true); payRow.addView(type); box.addView(payRow);

        TextView desc=label(jobDescription(j),14,"#B8C9D6",false); desc.setLineSpacing(0,1.14f); desc.setPadding(0,0,0,dp(14)); box.addView(desc);

        LinearLayout reqs=new LinearLayout(this); reqs.setOrientation(LinearLayout.HORIZONTAL); reqs.setPadding(dp(4),dp(8),dp(4),dp(8));
        LinearLayout leftReq=new LinearLayout(this); leftReq.setOrientation(LinearLayout.VERTICAL); leftReq.setPadding(0,0,dp(12),0);
        leftReq.addView(requirementRow("▣", "Job type", jobType(j)));
        leftReq.addView(requirementRow("⌖", "Location", displayLocation(j)));
        leftReq.addView(requirementRow("◷", "Schedule", scheduleText(j)));
        LinearLayout rightReq=new LinearLayout(this); rightReq.setOrientation(LinearLayout.VERTICAL); rightReq.setPadding(dp(12),0,0,0);
        LinearLayout degreeReqRow=requirementMatchRow("◇", "Degree required", degreeRequirement(j), profileHasDegree(degreeRequirement(j)));
        LinearLayout certReqRow=requirementMatchRow("▤", "Certification required", certificationRequirement(j), profileHasCertification(certificationRequirement(j)));
        rightReq.addView(degreeReqRow);
        rightReq.addView(certReqRow);
        rightReq.addView(requirementRow("◎", "Experience", experienceText(j)));
        View divider=new View(this); divider.setBackgroundColor(Color.parseColor("#294255"));
        reqs.addView(leftReq,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1));
        reqs.addView(divider,new LinearLayout.LayoutParams(dp(1),LinearLayout.LayoutParams.MATCH_PARENT));
        reqs.addView(rightReq,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1));
        box.addView(reqs);

        boolean tracked=isTracked(j); boolean saved=isSaved(j);
        LinearLayout actions=new LinearLayout(this); actions.setOrientation(LinearLayout.HORIZONTAL); actions.setGravity(Gravity.CENTER_VERTICAL); LinearLayout.LayoutParams ap=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(54)); ap.topMargin=dp(2); ap.leftMargin=dp(16); ap.rightMargin=dp(16); ap.bottomMargin=dp(16);
        Button save=new Button(this); save.setText(saved?"♥":"♡"); save.setTextColor(Color.WHITE); save.setTextSize(22); save.setAllCaps(false); save.setBackground(roundStrokeBg("#10283A","#31546C",15,1)); LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(dp(56),dp(52)); sp.rightMargin=dp(8); actions.addView(save,sp);
        Button follow=new Button(this); follow.setText(tracked?"Following":"Follow"); follow.setTextColor(Color.parseColor(tracked?"#B9CAD8":"#8DE7B5")); follow.setTextSize(15); follow.setTypeface(Typeface.DEFAULT,Typeface.BOLD); follow.setAllCaps(false); follow.setBackground(roundStrokeBg("#102A25","#2F7656",15,1)); LinearLayout.LayoutParams fp=new LinearLayout.LayoutParams(0,dp(52),1); fp.rightMargin=dp(8); actions.addView(follow,fp);
        Button apply=new Button(this); apply.setText("Apply  ↗"); apply.setTextColor(Color.WHITE); apply.setTextSize(16); apply.setTypeface(Typeface.DEFAULT,Typeface.BOLD); apply.setAllCaps(false); apply.setBackground(roundBg("#168CF0",15)); actions.addView(apply,new LinearLayout.LayoutParams(0,dp(52),2));

        save.setOnClickListener(v->{toggleSaved(j); save.setText(isSaved(j)?"♥":"♡");});
        follow.setOnClickListener(v->{setTracked(j,!isTracked(j)); dlg.dismiss(); showJob(j);});
        apply.setOnClickListener(v->{try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(j.url)));}catch(Exception e){Toast.makeText(this,"No application link available",Toast.LENGTH_SHORT).show();}});

        // V8.12: dark translucent violet glass job card; action row stays outside scrolling content, so Save/Follow/Apply
        // can never be clipped by a tall description or the Android navigation bar.
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackground(roundStrokeBg(isLightUi()?"#F2E4E6EA":"#E60B051F",isLightUi()?"#A786C9":"#6C249B",28,1));
        android.widget.ScrollView scroll=new android.widget.ScrollView(this);
        scroll.setFillViewport(false);
        scroll.setClipToPadding(false);
        scroll.addView(box,new android.widget.ScrollView.LayoutParams(android.widget.ScrollView.LayoutParams.MATCH_PARENT,android.widget.ScrollView.LayoutParams.WRAP_CONTENT));
        root.addView(scroll,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,0,1));
        root.addView(actions,ap);
        if(isLightUi())lightenDialogTree(root);
        // V9.0.7: light-theme recoloring must not erase semantic job-status colors.
        styleJobTypeChip(type);
        styleRequirementMatchRow(degreeReqRow,degreeRequirement(j),profileHasDegree(degreeRequirement(j)));
        styleRequirementMatchRow(certReqRow,certificationRequirement(j),profileHasCertification(certificationRequirement(j)));
        dlg.setContentView(root);
        dlg.setOnShowListener(x->{
            Window w=dlg.getWindow();
            if(w!=null){
                int screenH=getResources().getDisplayMetrics().heightPixels;
                int screenW=getResources().getDisplayMetrics().widthPixels;
                int wantedH=Math.min(dp(720),(int)(screenH*0.68f));
                int wantedW=Math.min(screenW-dp(28),dp(520));
                w.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
                w.setDimAmount(.10f); w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
                w.setLayout(wantedW,wantedH);
                WindowManager.LayoutParams attrs=w.getAttributes();
                attrs.gravity=Gravity.CENTER;
                attrs.y=dp(34);
                w.setAttributes(attrs);
            }
        });
        dlg.show();
    }

    private LinearLayout requirementRow(String icon,String name,String value){LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(0,dp(5),0,dp(5));TextView ic=label(icon,16,"#B8CAD8",true);ic.setGravity(Gravity.CENTER);row.addView(ic,new LinearLayout.LayoutParams(dp(30),dp(28)));LinearLayout words=new LinearLayout(this);words.setOrientation(LinearLayout.VERTICAL);TextView n=label(name,11,"#7893A6",false);TextView v=label(value,13,"#EAF2F8",false);words.addView(n);words.addView(v);row.addView(words,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1));return row;}
    private LinearLayout requirementMatchRow(String icon,String name,String value,boolean matched){
        LinearLayout row=requirementRow(icon,name,value);
        styleRequirementMatchRow(row,value,matched);
        return row;
    }
    private boolean isNoRequirementValue(String value){
        if(value==null)return true;
        String x=value.trim().toLowerCase(Locale.US);
        return x.isEmpty()||x.equals("no")||x.equals("none")||x.contains("not stated")||
            x.startsWith("no degree")||x.startsWith("no certification")||
            x.contains("not required")||x.contains("no requirement");
    }
    private void styleRequirementMatchRow(LinearLayout row,String value,boolean matched){
        if(row==null||value==null)return;
        LinearLayout words=(LinearLayout)row.getChildAt(1);
        TextView valueView=(TextView)words.getChildAt(1);
        if(isNoRequirementValue(value)){
            // V9.4.35: "No ... stated/required" is informational, not a failed match.
            // Leave it neutral and do not append the red "Required" status.
            valueView.setTextColor(Color.parseColor(isLightUi()?"#4F5963":"#EAF2F8"));
            valueView.setTypeface(Typeface.DEFAULT,Typeface.NORMAL);
            valueView.setText(value);
            return;
        }
        String color;
        if(isLightUi()) color=matched?"#087A4F":"#C6283D";
        else color=matched?"#35E0A1":"#FF6678";
        valueView.setTextColor(Color.parseColor(color));
        valueView.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        valueView.setText(value+(matched?"  ✓":"  Required"));
    }
    private void styleJobTypeChip(TextView type){
        if(type==null)return;
        type.setTextColor(Color.parseColor(isLightUi()?"#5A2D00":"#FFD19A"));
        type.setBackground(roundStrokeBg(isLightUi()?"#FFE4C4":"#3A2B18",isLightUi()?"#D79A58":"#72502A",20,1));
        type.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        type.setSingleLine(true);
    }
    private void saveLocalSettings(){
        getSharedPreferences("settings",MODE_PRIVATE).edit()
            .putInt("maxDistanceMiles",maxDistanceMiles)
            .putInt("minPay",minPay)
            .putString("category",category)
            .putString("source",source)
            .putString("mapTheme",mapTheme)
            .putString("mapRegion",mapRegion)
            .putBoolean("extendedDistance",extendedDistance)
            .putBoolean("preciseLocationsOnly",preciseLocationsOnly)
            .apply();
    }

    private void saveCloudState(){
        FirebaseUser user=firebaseAuth==null?null:firebaseAuth.getCurrentUser();
        if(user==null||firestore==null)return;
        HashMap<String,Object> data=new HashMap<>();
        android.content.SharedPreferences p=profilePrefs();
        data.put("name",p.getString("name",""));
        data.put("age",p.getInt("age",0));
        data.put("location",p.getString("location",""));
        data.put("degrees",p.getString("degrees",""));
        data.put("certifications",p.getString("certifications",""));
        if(hasSavedProfileCoordinates()){data.put("locationLat",profileLocationLat());data.put("locationLon",profileLocationLon());}
        data.put("maxDistanceMiles",maxDistanceMiles);
        data.put("minPay",minPay);
        data.put("category",category);
        data.put("source",source);
        data.put("mapTheme",mapTheme);
        data.put("mapRegion",mapRegion);
        data.put("extendedDistance",extendedDistance);
        data.put("preciseLocationsOnly",preciseLocationsOnly);
        data.put("updatedAt",com.google.firebase.firestore.FieldValue.serverTimestamp());
        firestore.collection("users").document(user.getUid()).set(data,SetOptions.merge());
    }

    private void syncCloudState(){
        FirebaseUser user=firebaseAuth==null?null:firebaseAuth.getCurrentUser();
        if(user==null||firestore==null)return;
        firestore.collection("users").document(user.getUid()).get().addOnSuccessListener(doc->{
            if(!doc.exists()){saveCloudState();return;}
            android.content.SharedPreferences.Editor pe=profilePrefs().edit();
            if(doc.contains("name"))pe.putString("name",String.valueOf(doc.get("name")));
            Long age=doc.getLong("age");if(age!=null)pe.putInt("age",age.intValue());
            if(doc.contains("location"))pe.putString("location",String.valueOf(doc.get("location")));
            if(doc.contains("degrees"))pe.putString("degrees",String.valueOf(doc.get("degrees")));
            if(doc.contains("certifications"))pe.putString("certifications",String.valueOf(doc.get("certifications")));
            Double lat=doc.getDouble("locationLat"),lon=doc.getDouble("locationLon");
            if(lat!=null&&lon!=null&&validCoordinate(lat,lon)){pe.putLong("location_lat_bits",Double.doubleToLongBits(lat));pe.putLong("location_lon_bits",Double.doubleToLongBits(lon));}
            pe.apply();
            Long dist=doc.getLong("maxDistanceMiles"),pay=doc.getLong("minPay");
            if(dist!=null)maxDistanceMiles=Math.max(1,dist.intValue());
            if(pay!=null)minPay=Math.max(0,pay.intValue());
            String c=doc.getString("category"),src=doc.getString("source"),theme=doc.getString("mapTheme"),region=doc.getString("mapRegion");
            if(c!=null&&!c.isEmpty())category=c;if(src!=null&&!src.isEmpty())source=src;if(theme!=null&&!theme.isEmpty())mapTheme=theme;
            if(region!=null&&("lower48".equals(region)||"alaska".equals(region)||"hawaii".equals(region)))mapRegion=region;
            Boolean ext=doc.getBoolean("extendedDistance");if(ext!=null)extendedDistance=ext;
            Boolean precise=doc.getBoolean("preciseLocationsOnly");if(precise!=null)preciseLocationsOnly=precise;
            saveLocalSettings();
            runOnUiThread(()->{
                if(distanceBar!=null){distanceBar.setMax(extendedDistance?10000:100);distanceBar.setProgress(Math.min(maxDistanceMiles,distanceBar.getMax()));}
                if(payBar!=null)payBar.setProgress(Math.min(minPay,100));
                if(distanceValue!=null)distanceValue.setText(maxDistanceMiles+" mi");
                if(payValue!=null)payValue.setText("$"+minPay+"+");
                if(categoryChip!=null)categoryChip.setText(category);
                if(sourceChip!=null)sourceChip.setText(source);
                applyMapTheme();applyMapRegionBounds(false);applyUiTheme();
                if(!profileLocation().isEmpty()&&hasSavedProfileCoordinates()){userLat=profileLocationLat();userLon=profileLocationLon();haveLocation=true;centerOnUser();loadJobs();}
                else applyFilters();
            });
        }).addOnFailureListener(e->{ /* Free cloud sync unavailable: keep the local copy without blocking the app. */ });
    }

    private android.content.SharedPreferences profilePrefs(){return getSharedPreferences("profile",MODE_PRIVATE);}
    private String profileName(){return profilePrefs().getString("name","");}
    private String profileLocation(){return profilePrefs().getString("location","").trim();}
    private double profileLocationLat(){return Double.longBitsToDouble(profilePrefs().getLong("location_lat_bits",Double.doubleToLongBits(0)));}
    private double profileLocationLon(){return Double.longBitsToDouble(profilePrefs().getLong("location_lon_bits",Double.doubleToLongBits(0)));}
    private boolean hasSavedProfileCoordinates(){return validCoordinate(profileLocationLat(),profileLocationLon());}
    private int profileAge(){return profilePrefs().getInt("age",0);}
    private String profileDegrees(){return profilePrefs().getString("degrees","");}
    private String profileCertifications(){return profilePrefs().getString("certifications","");}
    private boolean containsProfileItem(String stored,String required){
        if(required==null||required.trim().isEmpty()||required.equalsIgnoreCase("No")||required.toLowerCase(Locale.US).contains("not stated"))return true;
        String r=required.toLowerCase(Locale.US).replace("'","").replace("degree","").replace("diploma","").replace("certification","").replace("license","").trim();
        String all=(stored==null?"":stored).toLowerCase(Locale.US).replace("'","");
        if(all.contains(required.toLowerCase(Locale.US).replace("'","")))return true;
        for(String token:r.split("\\s+")){if(token.length()>4&&!all.contains(token))return false;}
        return r.length()>0;
    }
    private boolean profileHasDegree(String required){return containsProfileItem(profileDegrees(),required);}
    private boolean profileHasCertification(String required){return containsProfileItem(profileCertifications(),required);}
    private File profilePhotoFile(){return new File(getFilesDir(),"profile_photo.jpg");}
    private Bitmap loadProfilePhoto(){try{File f=profilePhotoFile();return f.exists()?BitmapFactory.decodeFile(f.getAbsolutePath()):null;}catch(Exception e){return null;}}
    private void saveProfileBitmap(Bitmap b){if(b==null)return;try{FileOutputStream out=new FileOutputStream(profilePhotoFile());b.compress(Bitmap.CompressFormat.JPEG,90,out);out.close();}catch(Exception e){Toast.makeText(this,"Couldn't save photo",Toast.LENGTH_SHORT).show();}}
    private void chooseProfilePhoto(){
        final String[] opts=profilePhotoFile().exists()?new String[]{"Choose from gallery","Take a photo","Remove photo"}:new String[]{"Choose from gallery","Take a photo"};
        new AlertDialog.Builder(this).setTitle("Profile picture").setItems(opts,(d,which)->{
            if(which==0){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("image/*");startActivityForResult(i,PROFILE_GALLERY_REQUEST);}
            else if(which==1){Intent i=new Intent("android.media.action.IMAGE_CAPTURE");startActivityForResult(i,PROFILE_CAMERA_REQUEST);}
            else {profilePhotoFile().delete();showProfile();}
        }).show();
    }
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode==GOOGLE_SIGN_IN_REQUEST){try{GoogleSignInAccount account=GoogleSignIn.getSignedInAccountFromIntent(data).getResult(ApiException.class);firebaseAuthWithGoogle(account);}catch(Exception e){Toast.makeText(this,"Google sign-in was not completed.",Toast.LENGTH_SHORT).show();}return;}
        if(resultCode!=RESULT_OK)return;
        try{
            if(requestCode==PROFILE_GALLERY_REQUEST&&data!=null&&data.getData()!=null){InputStream in=getContentResolver().openInputStream(data.getData());Bitmap b=BitmapFactory.decodeStream(in);if(in!=null)in.close();saveProfileBitmap(b);showProfile();}
            else if(requestCode==PROFILE_CAMERA_REQUEST&&data!=null&&data.getExtras()!=null){Object o=data.getExtras().get("data");if(o instanceof Bitmap){saveProfileBitmap((Bitmap)o);showProfile();}}
        }catch(Exception e){Toast.makeText(this,"Couldn't load profile picture",Toast.LENGTH_SHORT).show();}
    }
    private EditText profileEditField(String hint,String value,boolean numeric,boolean multiline){
        final boolean light=isLightUi();
        EditText e=new EditText(this);
        e.setHint(hint);
        e.setText(value==null?"":value);
        e.setTextSize(16);
        e.setTextColor(Color.parseColor(light?"#202329":"#F4F8FC"));
        e.setHintTextColor(Color.parseColor(light?"#7A8089":"#71889B"));
        e.setPadding(dp(16),multiline?dp(12):0,dp(16),multiline?dp(12):0);
        e.setGravity(multiline?(Gravity.TOP|Gravity.START):Gravity.CENTER_VERTICAL);
        e.setBackground(roundStrokeBg(light?"#F7F8FA":"#0E2132",light?"#C8CCD2":"#31546C",16,1));
        e.setEnabled(true);e.setClickable(true);e.setFocusable(true);e.setFocusableInTouchMode(true);
        e.setCursorVisible(true);e.setShowSoftInputOnFocus(true);
        if(numeric){e.setSingleLine(true);e.setInputType(InputType.TYPE_CLASS_NUMBER);}
        else if(multiline){e.setSingleLine(false);e.setMinLines(2);e.setMaxLines(4);e.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_CAP_SENTENCES|InputType.TYPE_TEXT_FLAG_MULTI_LINE);}
        else {e.setSingleLine(true);e.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_CAP_WORDS);}
        return e;
    }

    private TextView profileFieldLabel(String text){
        TextView t=label(text,13,isLightUi()?"#4B525B":"#A9BED0",true);
        t.setPadding(dp(2),0,0,dp(6));
        return t;
    }

    private void showEditProfile(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        ScrollView outer=new ScrollView(this);outer.setFillViewport(false);outer.setClipToPadding(false);
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(22),dp(14),dp(22),dp(28));box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));outer.addView(box);

        TextView handle=new TextView(this);LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(dp(42),dp(5));hp.gravity=Gravity.CENTER_HORIZONTAL;hp.bottomMargin=dp(16);handle.setLayoutParams(hp);handle.setBackground(roundBg(light?"#7D8790":"#526A7E",10));box.addView(handle);
        TextView title=label("Edit profile",24,light?"#22252B":"#F4F8FC",true);box.addView(title);
        TextView sub=label("Add details that JobBubble can use to match you with job requirements.",13,light?"#646B74":"#8FA7BA",false);sub.setPadding(0,dp(4),0,dp(18));box.addView(sub);

        box.addView(profileFieldLabel("Name"));
        EditText name=profileEditField("Your name",profileName(),false,false);box.addView(name,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(54)));

        TextView ageLabel=profileFieldLabel("Age");ageLabel.setPadding(dp(2),dp(14),0,dp(6));box.addView(ageLabel);
        EditText age=profileEditField("Your age",profileAge()>0?String.valueOf(profileAge()):"",true,false);box.addView(age,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(54)));

        TextView locationLabel=profileFieldLabel("Job search location");locationLabel.setPadding(dp(2),dp(14),0,dp(6));box.addView(locationLabel);
        EditText location=profileEditField("City, state or ZIP code",profileLocation(),false,false);box.addView(location,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(54)));
        TextView locationHint=label("Job distance is measured from this saved location. Leave blank to use your device location.",11,light?"#6B7280":"#8FA7BA",false);locationHint.setPadding(dp(2),dp(5),dp(2),0);box.addView(locationHint);

        TextView degreeLabel=profileFieldLabel("Degrees");degreeLabel.setPadding(dp(2),dp(14),0,dp(6));box.addView(degreeLabel);
        EditText degrees=profileEditField("One per line or separated by commas",profileDegrees(),false,true);box.addView(degrees,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(88)));

        TextView certLabel=profileFieldLabel("Certifications & licenses");certLabel.setPadding(dp(2),dp(14),0,dp(6));box.addView(certLabel);
        EditText certs=profileEditField("One per line or separated by commas",profileCertifications(),false,true);box.addView(certs,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(88)));

        LinearLayout actions=new LinearLayout(this);actions.setOrientation(LinearLayout.HORIZONTAL);actions.setPadding(0,dp(20),0,0);
        TextView cancel=label("Cancel",16,light?"#25282D":"#E9DFFF",true);cancel.setGravity(Gravity.CENTER);cancel.setBackground(roundStrokeBg(light?"#F3F4F6":"#160B28",light?"#B8BCC3":"#6B3BA0",16,1));
        TextView save=label("Save",16,"#FFFFFF",true);save.setGravity(Gravity.CENTER);GradientDrawable saveBg=new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,new int[]{Color.parseColor(light?"#7434C8":"#5A169A"),Color.parseColor(light?"#9D35E8":"#7A1CC7")});saveBg.setCornerRadius(dp(16));save.setBackground(saveBg);
        LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(0,dp(52),1f);cp.rightMargin=dp(7);actions.addView(cancel,cp);LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(0,dp(52),1f);sp.leftMargin=dp(7);actions.addView(save,sp);box.addView(actions);

        cancel.setOnClickListener(v->dlg.dismiss());
        save.setOnClickListener(v->{
            int a=0;try{a=Integer.parseInt(age.getText().toString().trim());}catch(Exception ignored){}
            String oldLocation=profileLocation();String newLocation=location.getText().toString().trim();
            android.content.SharedPreferences.Editor pe=profilePrefs().edit().putString("name",name.getText().toString().trim()).putInt("age",a).putString("location",newLocation).putString("degrees",degrees.getText().toString().trim()).putString("certifications",certs.getText().toString().trim());
            if(!newLocation.equalsIgnoreCase(oldLocation)){pe.remove("location_lat_bits").remove("location_lon_bits");haveLocation=false;}
            pe.apply();
            saveCloudState();
            dlg.dismiss();showProfile();
            if(!newLocation.isEmpty())loadJobs();else requestLocation();
        });

        dlg.setContentView(outer);
        dlg.setOnShowListener(x->{
            Window w=dlg.getWindow();if(w!=null){w.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE|WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE);w.setDimAmount(.30f);w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);}
        });
        dlg.show();
        name.postDelayed(()->{name.requestFocus();InputMethodManager imm=(InputMethodManager)getSystemService(INPUT_METHOD_SERVICE);if(imm!=null)imm.showSoftInput(name,InputMethodManager.SHOW_IMPLICIT);},180);
    }
    private String jobDescription(Job j){
        if(j.description!=null&&!j.description.trim().isEmpty())return cleanDescription(j.description);
        String t=(j.title==null?"":j.title).toLowerCase(Locale.US), c=(j.company==null?"":j.company).toLowerCase(Locale.US);
        if(c.contains("home depot"))return "Help customers find products, answer questions, and support sales and merchandising across the store.";
        if(c.contains("lowe"))return "Assist customers with products and projects, keep the sales floor organized, and support stocking and checkout needs.";
        if(c.contains("costco"))return "Stock merchandise, keep aisles organized, and help maintain a clean, safe warehouse environment.";
        if(c.contains("target"))return "Create a welcoming guest experience, help with checkout and pickup services, and support the sales floor as needed.";
        if(c.contains("starbucks"))return "Prepare beverages, serve customers, and help keep the store clean, stocked, and welcoming.";
        if(c.contains("amazon"))return "Receive, sort, pick, pack, and move customer orders in a fulfillment center while following safety procedures.";
        return "See the employer listing for full responsibilities and requirements.";
    }
    private String cleanDescription(String d){String x=d.replaceAll("<[^>]+>"," ").replace("&amp;","&").replace("&quot;","\"").replace("&#39;","'").replaceAll("\\s+"," ").trim();return x.length()>520?x.substring(0,517)+"...":x;}
    private String requirementText(Job j){return ((j.title==null?"":j.title)+" "+(j.description==null?"":j.description)+" "+(j.category==null?"":j.category)).toLowerCase(Locale.US);}
    private String degreeRequirement(Job j){
        String x=requirementText(j);
        if(x.matches(".*\\b(master'?s|masters degree|m\\.?s\\.?|mba)\\b.*"))return "Master's degree";
        if(x.matches(".*\\b(bachelor'?s|bachelors degree|b\\.?s\\.?|b\\.?a\\.?)\\b.*"))return "Bachelor's degree";
        if(x.matches(".*\\b(associate'?s|associates degree|a\\.?a\\.?|a\\.?s\\.?)\\b.*"))return "Associate degree";
        if(x.contains("high school diploma")||x.contains("ged"))return "High school diploma / GED";
        if(x.contains("medical assistant diploma"))return "Medical Assistant diploma";
        return "No degree stated";
    }
    private String certificationRequirement(Job j){
        String x=requirementText(j);
        if(x.contains("cdl a or b")||x.contains("class a or b")||x.contains("class a/b"))return "CDL Class A or B";
        if(x.matches(".*\\bcdl\\s*(class\\s*)?a\\b.*")||x.contains("class a cdl"))return "CDL Class A";
        if(x.matches(".*\\bcdl\\s*(class\\s*)?b\\b.*")||x.contains("class b cdl"))return "CDL Class B";
        if(x.contains("commercial driver's license")||x.contains("commercial driver’s license")||x.matches(".*\\bcdl\\b.*"))return "Commercial Driver's License (CDL)";
        if(x.contains("registered nurse")||x.matches(".*\\brn license\\b.*"))return "RN license";
        if(x.contains("licensed practical nurse")||x.matches(".*\\blpn license\\b.*"))return "LPN license";
        if(x.contains("cna")||x.contains("certified nursing assistant"))return "CNA certification";
        if(x.contains("security guard license")||x.contains("guard card"))return "Security Guard License";
        if(x.contains("medical assistant certification")||x.contains("certified medical assistant"))return "Medical Assistant Certification";
        if(x.contains("driver's license")||x.contains("driver’s license")||x.contains("valid driver license")||x.contains("valid driver's license"))return "Driver's License";
        if(x.contains("delivery driver")||x.contains("driver"))return "Driver's License";
        return "No certification stated";
    }
    private String scheduleText(Job j){String x=requirementText(j);if(x.contains("part-time")||x.contains("part time"))return "Part-time";if(x.contains("full-time")||x.contains("full time"))return "Full-time";if(x.contains("overnight")||x.contains("night shift"))return "Includes night/overnight shifts";return "See employer listing";}
    private String experienceText(Job j){String x=requirementText(j);java.util.regex.Matcher m=java.util.regex.Pattern.compile("(\\d+\\+?)\\s+(?:years?|yrs?)\\s+(?:of\\s+)?experience").matcher(x);if(m.find())return m.group(1)+" years experience";if(x.contains("entry level")||x.contains("no experience"))return "Entry level";return "See employer listing";}
    private String jobType(Job j){String x=requirementText(j);boolean ft=x.contains("full-time")||x.contains("full time");boolean pt=x.contains("part-time")||x.contains("part time");if(ft&&pt)return "Full-time / Part-time";if(pt)return "Part-time";if(ft)return "Full-time";return "See listing";}
    private String companyBadge(String n){String x=n==null?"":n.toLowerCase(Locale.US);if(x.contains("home depot"))return "THE\nHOME\nDEPOT";if(x.contains("lowe"))return "L";if(x.contains("costco"))return "COSTCO";if(x.contains("target"))return "◎";if(x.contains("starbucks"))return "S";if(x.contains("amazon"))return "a";if(x.contains("walmart"))return "✱";if(x.contains("fedex"))return "FedEx";if(x.contains("ups"))return "UPS";String[] a=(n==null?"Job":n).trim().split("\\s+");return (a[0].substring(0,1)+(a.length>1?a[a.length-1].substring(0,1):"")).toUpperCase(Locale.US);}
    private int companyLogoTextSize(String n){String x=n==null?"":n.toLowerCase(Locale.US);if(x.contains("home depot"))return 9;if(x.contains("costco")||x.contains("fedex")||x.contains("lowe"))return 10;if(x.contains("walmart")||x.contains("target")||x.contains("starbucks")||x.contains("amazon"))return 24;return 13;}
    private String companyLogoTextColor(String n){String x=n==null?"":n.toLowerCase(Locale.US);if(x.contains("walmart"))return "#FFC220";if(x.contains("costco"))return "#E31837";if(x.contains("mcdonald"))return "#FFC72C";return "#FFFFFF";}
    private String companyColor(String n,String cat){String x=n==null?"":n.toLowerCase(Locale.US);if(x.contains("home depot"))return "#F96302";if(x.contains("lowe"))return "#1D4E9E";if(x.contains("costco"))return "#E31837";if(x.contains("target"))return "#CC0000";if(x.contains("starbucks"))return "#00754A";if(x.contains("amazon"))return "#111111";if(x.contains("walmart"))return "#0878CE";if(x.contains("fedex"))return "#4D148C";if(x.contains("ups"))return "#351C15";return categoryHex(cat);}

    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    private TextView label(String text,int size,String color,boolean bold){TextView v=new TextView(this);v.setText(text);v.setTextSize(size);v.setTextColor(Color.parseColor(color));if(bold)v.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return v;}
    private GradientDrawable roundBg(String color,int radius){GradientDrawable g=new GradientDrawable();g.setColor(Color.parseColor(color));g.setCornerRadius(dp(radius));return g;}
    private GradientDrawable roundStrokeBg(String fill,String stroke,int radius,int width){GradientDrawable g=roundBg(fill,radius);g.setStroke(dp(width),Color.parseColor(stroke));return g;}
    private String categoryHex(String cat){if(cat==null)return "#38D89A";String c=cat.toLowerCase(Locale.US);if(c.contains("retail"))return "#F59E0B";if(c.contains("security"))return "#A855F7";if(c.contains("customer"))return "#3B82F6";if(c.contains("warehouse"))return "#10B981";if(c.contains("food")||c.contains("hospitality"))return "#EF4444";if(c.contains("health"))return "#EC4899";if(c.contains("technology")||c.contains("engineering"))return "#06B6D4";if(c.contains("government"))return "#2563EB";if(c.contains("education"))return "#8B5CF6";if(c.contains("finance"))return "#059669";if(c.contains("manufacturing"))return "#64748B";if(c.contains("construction"))return "#D97706";if(c.contains("cleaning")||c.contains("facilities"))return "#14B8A6";return "#38D89A";}
    private String jobKey(Job j){return Integer.toHexString((j.title+"|"+j.company+"|"+j.lat+"|"+j.lon).hashCode());} private boolean isSaved(Job j){return getSharedPreferences("saved",MODE_PRIVATE).getBoolean(jobKey(j),false);} private void toggleSaved(Job j){boolean n=!isSaved(j);getSharedPreferences("saved",MODE_PRIVATE).edit().putBoolean(jobKey(j),n).apply();Toast.makeText(this,n?"Job saved":"Job removed",Toast.LENGTH_SHORT).show();}
    private boolean isTracked(Job j){return getSharedPreferences("tracked",MODE_PRIVATE).getBoolean(jobKey(j),false);}
    private void setTracked(Job j,boolean tracked){getSharedPreferences("tracked",MODE_PRIVATE).edit().putBoolean(jobKey(j),tracked).apply();Toast.makeText(this,tracked?"Following "+j.title:"Stopped following "+j.title,Toast.LENGTH_SHORT).show();applyFilters();}
    private void followJob(Job j){if(!isTracked(j))setTracked(j,true);else Toast.makeText(this,"Already following "+j.title,Toast.LENGTH_SHORT).show();showJob(j);}
    private void addModernJobRow(LinearLayout list,Job j,Dialog dlg){
        boolean light=isLightUi();
        LinearLayout row=new LinearLayout(this); row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER_VERTICAL); row.setPadding(dp(14),dp(12),dp(12),dp(12));
        row.setBackground(roundStrokeBg(light?"#E3E5E8":"#110B25",light?"#C8CBD1":"#3B275B",16,1));
        TextView logo=label(j.company.length()>0?j.company.substring(0,1).toUpperCase(Locale.US):"J",18,light?"#FFFFFF":"#FFFFFF",true); logo.setGravity(Gravity.CENTER); logo.setBackground(roundBg(categoryHex(j.category),14));
        row.addView(logo,new LinearLayout.LayoutParams(dp(50),dp(50)));
        LinearLayout text=new LinearLayout(this); text.setOrientation(LinearLayout.VERTICAL); text.setPadding(dp(12),0,dp(6),0);
        TextView title=label(j.title,16,light?"#202329":"#F5F7FB",true);
        TextView company=label(j.company+"  •  "+money(distanceMiles(userLat,userLon,j.lat,j.lon))+" mi",12,light?"#656B75":"#A99CC9",false);
        TextView pay=label("$"+money(j.pay)+"/hr",14,light?"#12835F":"#35E0A1",true);
        text.addView(title); text.addView(company); text.addView(pay);
        row.addView(text,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1f));
        TextView arrow=label("›",28,light?"#6B3AA5":"#B98CFF",false); arrow.setGravity(Gravity.CENTER); row.addView(arrow,new LinearLayout.LayoutParams(dp(32),dp(50)));
        row.setOnClickListener(v->{dlg.dismiss();showJob(j);});
        LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); rp.bottomMargin=dp(9); list.addView(row,rp);
    }

    private LinearLayout modernListShell(String titleText,String subtitle){
        boolean light=isLightUi();
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(18),dp(12),dp(18),dp(22));
        box.setBackground(roundStrokeBg(light?"#E9EAED":"#0B0717",light?"#C9CCD2":"#3F2463",28,1));
        TextView handle=new TextView(this); LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(dp(42),dp(5)); hp.gravity=Gravity.CENTER_HORIZONTAL; hp.bottomMargin=dp(14); handle.setLayoutParams(hp); handle.setBackground(roundBg(light?"#A9ADB4":"#73519C",10)); box.addView(handle);
        TextView title=label(titleText,23,light?"#202329":"#F8F6FF",true); box.addView(title);
        TextView sub=label(subtitle,13,light?"#676D76":"#A99CC9",false); sub.setPadding(0,dp(3),0,dp(14)); box.addView(sub);
        return box;
    }

    private void showJobList(boolean savedOnly){
        ArrayList<Job> list=new ArrayList<>();for(Job j:filtered)if(!savedOnly||isSaved(j))list.add(j);
        if(list.isEmpty()){Toast.makeText(this,savedOnly?"No saved jobs yet":"No jobs match your filters",Toast.LENGTH_SHORT).show();return;}
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        LinearLayout box=modernListShell(savedOnly?"Saved jobs":"Jobs","Showing "+list.size()+" matching jobs");
        ScrollView scroll=new ScrollView(this); LinearLayout rows=new LinearLayout(this); rows.setOrientation(LinearLayout.VERTICAL);
        for(Job j:list)addModernJobRow(rows,j,dlg);
        scroll.addView(rows); box.addView(scroll,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,0,1f));
        Button close=new Button(this); close.setText("Close");close.setAllCaps(false);close.setTypeface(Typeface.DEFAULT,Typeface.BOLD);close.setTextColor(isLightUi()?Color.parseColor("#2A2D34"):Color.WHITE);close.setBackground(roundStrokeBg(isLightUi()?"#DFE1E5":"#17102C",isLightUi()?"#BFC3CA":"#6E3DA8",14,1));LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(50));cp.topMargin=dp(8);box.addView(close,cp);close.setOnClickListener(v->dlg.dismiss());
        if(isLightUi())lightenDialogTree(box);dlg.setContentView(box);dlg.show();
    }

    private void rebuildSearchRows(LinearLayout rows,String query,Dialog dlg){
        rows.removeAllViews();String q=query==null?"":query.trim().toLowerCase(Locale.US);int count=0;
        for(Job j:filtered){
            String hay=(j.title+" "+j.company+" "+j.category+" "+j.source).toLowerCase(Locale.US);
            if(q.isEmpty()||hay.contains(q)){addModernJobRow(rows,j,dlg);count++;}
        }
        if(count==0){TextView none=label("No jobs match that search.",15,isLightUi()?"#5D636C":"#A99CC9",false);none.setGravity(Gravity.CENTER);none.setPadding(0,dp(28),0,dp(28));rows.addView(none);}
    }

    private void showSearchDialog(){
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        LinearLayout box=modernListShell("Search jobs","Search job titles, companies, categories, or sources.");
        EditText search=new EditText(this);search.setSingleLine(true);search.setTextSize(16);search.setHint("Search jobs, companies, or keywords…");search.setHintTextColor(Color.parseColor(isLightUi()?"#858B94":"#80739A"));search.setTextColor(Color.parseColor(isLightUi()?"#202329":"#F5F2FB"));search.setPadding(dp(16),0,dp(16),0);search.setBackground(roundStrokeBg(isLightUi()?"#DFE1E5":"#100A20",isLightUi()?"#BFC3CA":"#55327B",18,1));box.addView(search,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)));
        LinearLayout chips=new LinearLayout(this);chips.setOrientation(LinearLayout.HORIZONTAL);chips.setPadding(0,dp(10),0,dp(8));
        TextView nearby=label(maxDistanceMiles+" mi",13,isLightUi()?"#4C2E72":"#CCB4F5",true);nearby.setGravity(Gravity.CENTER);nearby.setBackground(roundStrokeBg(isLightUi()?"#E4E5E8":"#17102C",isLightUi()?"#C7BDD3":"#6D3FC3",15,1));chips.addView(nearby,new LinearLayout.LayoutParams(dp(78),dp(38)));
        TextView payChip=label("$"+minPay+"+",13,"#12835F",true);payChip.setGravity(Gravity.CENTER);payChip.setBackground(roundStrokeBg(isLightUi()?"#E4E5E8":"#102821",isLightUi()?"#BCC9C3":"#237C61",15,1));LinearLayout.LayoutParams pcp=new LinearLayout.LayoutParams(dp(78),dp(38));pcp.leftMargin=dp(8);chips.addView(payChip,pcp);box.addView(chips);
        ScrollView scroll=new ScrollView(this);LinearLayout rows=new LinearLayout(this);rows.setOrientation(LinearLayout.VERTICAL);scroll.addView(rows);box.addView(scroll,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,0,1f));
        rebuildSearchRows(rows,"",dlg);
        search.addTextChangedListener(new android.text.TextWatcher(){public void beforeTextChanged(CharSequence c,int st,int count,int after){}public void onTextChanged(CharSequence c,int st,int before,int count){rebuildSearchRows(rows,c.toString(),dlg);}public void afterTextChanged(android.text.Editable e){}});
        if(isLightUi())lightenDialogTree(box);dlg.setContentView(box);dlg.show();search.requestFocus();
    }
    private void showProfile(){
        boolean guest=getPreferences(MODE_PRIVATE).getBoolean("guestMode",false);
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(false);scroll.setClipToPadding(false);
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(22),dp(14),dp(22),dp(30));box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));scroll.addView(box);
        TextView handle=new TextView(this);LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(dp(42),dp(5));hp.gravity=Gravity.CENTER_HORIZONTAL;hp.bottomMargin=dp(16);handle.setLayoutParams(hp);handle.setBackground(roundBg(light?"#7D8790":"#526A7E",10));box.addView(handle);
        LinearLayout top=new LinearLayout(this);top.setOrientation(LinearLayout.HORIZONTAL);top.setGravity(Gravity.CENTER_VERTICAL);
        FrameLayout avatarWrap=new FrameLayout(this);
        ImageView photo=new ImageView(this);photo.setScaleType(ImageView.ScaleType.CENTER_CROP);photo.setBackground(roundBg("#7C3AED",50));photo.setClipToOutline(true);Bitmap pb=loadProfilePhoto();if(pb!=null)photo.setImageBitmap(pb);
        TextView fallback=label((profileName().isEmpty()?(guest?"G":"J"):profileName().substring(0,1).toUpperCase(Locale.US)),22,"#FFFFFF",true);fallback.setGravity(Gravity.CENTER);fallback.setBackground(roundBg("#7C3AED",50));if(pb!=null)fallback.setVisibility(View.GONE);
        avatarWrap.addView(photo,new FrameLayout.LayoutParams(dp(70),dp(70)));avatarWrap.addView(fallback,new FrameLayout.LayoutParams(dp(70),dp(70)));avatarWrap.setOnClickListener(v->{dlg.dismiss();chooseProfilePhoto();});top.addView(avatarWrap,new LinearLayout.LayoutParams(dp(70),dp(70)));
        LinearLayout who=new LinearLayout(this);who.setOrientation(LinearLayout.VERTICAL);who.setPadding(dp(14),0,0,0);String display=profileName().isEmpty()?(guest?"Guest profile":"JobBubble profile"):profileName();who.addView(label(display,21,light?"#22252B":"#F4F8FC",true));String subtitle=profileAge()>0?"Age "+profileAge():(guest?"Browsing without an account":"Profile details");who.addView(label(subtitle,13,light?"#646B74":"#8FA7BA",false));top.addView(who,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1));box.addView(top);
        TextView photoHint=label("Tap your picture to choose from Gallery or Camera",12,light?"#6B7280":"#8FA7BA",false);photoHint.setPadding(0,dp(8),0,dp(16));box.addView(photoHint);
        Button edit=new Button(this);edit.setText("Edit profile");edit.setAllCaps(false);edit.setTextColor(light?Color.parseColor("#FFFFFF"):Color.WHITE);edit.setBackground(roundBg("#6F35A8",14));box.addView(edit,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)));edit.setOnClickListener(v->{dlg.dismiss();showEditProfile();});
        TextView lHead=label("Job search location",15,light?"#25282E":"#DCE8F2",true);lHead.setPadding(0,dp(18),0,dp(6));box.addView(lHead);TextView lVal=label(profileLocation().isEmpty()?"Using device location":profileLocation(),13,light?"#4B5563":"#B8CAD8",false);lVal.setPadding(dp(14),dp(10),dp(14),dp(10));lVal.setBackground(roundStrokeBg(light?"#E2E4E8":"#10283A",light?"#C3C7CD":"#31546C",14,1));box.addView(lVal);
        TextView dHead=label("Degrees",15,light?"#25282E":"#DCE8F2",true);dHead.setPadding(0,dp(18),0,dp(6));box.addView(dHead);TextView dVal=label(profileDegrees().isEmpty()?"No degrees added":profileDegrees(),13,light?"#4B5563":"#B8CAD8",false);dVal.setPadding(dp(14),dp(10),dp(14),dp(10));dVal.setBackground(roundStrokeBg(light?"#E2E4E8":"#10283A",light?"#C3C7CD":"#31546C",14,1));box.addView(dVal);
        TextView cHead=label("Certifications & licenses",15,light?"#25282E":"#DCE8F2",true);cHead.setPadding(0,dp(14),0,dp(6));box.addView(cHead);TextView cVal=label(profileCertifications().isEmpty()?"No certifications added":profileCertifications(),13,light?"#4B5563":"#B8CAD8",false);cVal.setPadding(dp(14),dp(10),dp(14),dp(10));cVal.setBackground(roundStrokeBg(light?"#E2E4E8":"#10283A",light?"#C3C7CD":"#31546C",14,1));box.addView(cVal);
        TextView matchNote=label("Job requirements turn green when your profile matches. Missing required degrees or certifications appear red.",12,light?"#5F6670":"#91A6B6",false);matchNote.setPadding(0,dp(14),0,dp(16));box.addView(matchNote);
        Button settings=new Button(this);settings.setText("⚙   Settings");settings.setAllCaps(false);settings.setGravity(Gravity.START|Gravity.CENTER_VERTICAL);settings.setPadding(dp(18),0,dp(18),0);settings.setTextColor(light?Color.parseColor("#22252B"):Color.WHITE);settings.setBackground(roundStrokeBg(light?"#E2E4E8":"#10283A",light?"#C3C7CD":"#31546C",14,1));box.addView(settings,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(54)));
        Button close=new Button(this);close.setText("Close");close.setAllCaps(false);close.setTypeface(Typeface.DEFAULT,Typeface.BOLD);close.setTextColor(Color.WHITE);close.setBackground(roundBg("#2196F3",14));LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52));cp.topMargin=dp(12);box.addView(close,cp);
        settings.setOnClickListener(v->{dlg.dismiss();showSettings();});close.setOnClickListener(v->dlg.dismiss());
        dlg.setContentView(scroll);dlg.setOnShowListener(x->{Window w=dlg.getWindow();if(w!=null){w.setDimAmount(.30f);w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);}});dlg.show();
    }

    private Button settingsMenuButton(String text, boolean danger){
        final boolean light=isLightUi();
        Button b=new Button(this);
        b.setText(text); b.setAllCaps(false); b.setGravity(Gravity.START|Gravity.CENTER_VERTICAL);
        b.setPadding(dp(18),0,dp(18),0); b.setTextSize(15); b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        b.setTextColor(danger?Color.parseColor(light?"#9A374A":"#FF9F9F"):Color.parseColor(light?"#22252B":"#F4F8FC"));
        b.setBackground(roundStrokeBg(danger?(light?"#F2E4E7":"#281A23"):(light?"#E2E4E8":"#10283A"),danger?(light?"#D7AEB7":"#5B3442"):(light?"#C3C7CD":"#31546C"),14,1));
        return b;
    }

    private TextView infoCard(String title,String body){
        final boolean light=isLightUi();
        TextView v=label(title+"\n"+body,14,light?"#2B3037":"#E8F1F8",false);
        SpannableString sp=new SpannableString(v.getText());
        sp.setSpan(new android.text.style.StyleSpan(Typeface.BOLD),0,title.length(),Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        v.setText(sp); v.setPadding(dp(14),dp(12),dp(14),dp(12));
        v.setBackground(roundStrokeBg(light?"#E2E4E8":"#10283A",light?"#C3C7CD":"#31546C",14,1));
        return v;
    }

    private void showLicensesAndSources(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        ScrollView scroll=new ScrollView(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(16),dp(22),dp(34)); box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));
        scroll.addView(box);
        TextView title=label("Licenses & Data Sources",24,light?"#22252B":"#F4F8FC",true); box.addView(title);
        TextView intro=label("See your saved licenses and certifications, plus the services JobBubble uses to find and place job listings.",13,light?"#646B74":"#8FA7BA",false); intro.setPadding(0,dp(5),0,dp(16)); box.addView(intro);

        TextView your=label("Your Licenses & Certifications",16,light?"#25282E":"#DCE8F2",true); box.addView(your);
        String certText=profileCertifications().trim();
        TextView certs=infoCard(certText.isEmpty()?"No licenses or certifications saved":"Saved credentials",certText.isEmpty()?"Add them from Edit profile to improve requirement matching.":certText);
        LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); cp.topMargin=dp(8); box.addView(certs,cp);

        Button edit=settingsMenuButton("Edit licenses & certifications",false); LinearLayout.LayoutParams ep=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); ep.topMargin=dp(8); box.addView(edit,ep); edit.setOnClickListener(v->{dlg.dismiss();showEditProfile();});

        TextView data=label("Job Data Sources",16,light?"#25282E":"#DCE8F2",true); data.setPadding(0,dp(20),0,dp(8)); box.addView(data);
        box.addView(infoCard("The Muse","Private-sector job listings supplied through The Muse API."));
        LinearLayout.LayoutParams gap=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); gap.topMargin=dp(8);
        box.addView(infoCard("USAJOBS","Official U.S. federal government job listings."),gap);
        LinearLayout.LayoutParams gap2=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); gap2.topMargin=dp(8);
        box.addView(infoCard("Adzuna","Job listing search provider used as one of JobBubble's live job sources."),gap2);
        TextView map=label("Map data: Google Maps. Location refinement: Geoapify. Authentication/profile sync: Firebase.",12,light?"#6B7280":"#8FA7BA",false); map.setPadding(0,dp(14),0,dp(10)); box.addView(map);

        Button done=settingsMenuButton("Done",false); done.setGravity(Gravity.CENTER); LinearLayout.LayoutParams dpv=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); dpv.topMargin=dp(10); box.addView(done,dpv); done.setOnClickListener(v->dlg.dismiss());
        dlg.setContentView(scroll); dlg.show();
    }

    private void showJobSourcesMenu(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(16),dp(22),dp(32)); box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));
        box.addView(label("Job Sources",24,light?"#22252B":"#F4F8FC",true));
        TextView sub=label("Choose which live source the map should use. You can always return to All sources.",13,light?"#646B74":"#8FA7BA",false); sub.setPadding(0,dp(5),0,dp(14)); box.addView(sub);
        final String[] choices={"All sources","Adzuna","USAJOBS","The Muse"};
        for(String choice:choices){
            String detail=choice.equals("All sources")?"Combine every enabled source":choice.equals("Adzuna")?"General job listings":choice.equals("USAJOBS")?"Federal government jobs":"Private-sector jobs from The Muse";
            Button b=settingsMenuButton((choice.equals(source)?"✓  ":"     ")+choice+"  —  "+detail,false);
            LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(58)); p.bottomMargin=dp(8); box.addView(b,p);
            b.setOnClickListener(v->{source=choice;if(sourceChip!=null)sourceChip.setText(choice);saveLocalSettings();saveCloudState();dlg.dismiss();loadJobs();});
        }
        dlg.setContentView(box); dlg.show();
    }

    private void showHelpSupport(){
        final boolean light=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(22),dp(16),dp(22),dp(32)); box.setBackground(roundBg(light?"#ECEDEF":"#0B1A29",28));
        box.addView(label("Help & Support",24,light?"#22252B":"#F4F8FC",true));
        TextView sub=label("Quick help for the most common JobBubble questions.",13,light?"#646B74":"#8FA7BA",false); sub.setPadding(0,dp(5),0,dp(14)); box.addView(sub);
        box.addView(infoCard("No jobs showing","Try All sources, increase distance, lower the pay filter, or use Reset. Some providers may temporarily be unavailable."));
        LinearLayout.LayoutParams g1=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); g1.topMargin=dp(8); box.addView(infoCard("Job location looks approximate","JobBubble shows the best available area when an exact worksite address is unavailable, then refines it when better information is found."),g1);
        LinearLayout.LayoutParams g2=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); g2.topMargin=dp(8); box.addView(infoCard("Profile matching","Add degrees, licenses and certifications in your profile. Matching requirements appear green; missing requirements appear red."),g2);
        LinearLayout.LayoutParams g3=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); g3.topMargin=dp(8); box.addView(infoCard("Privacy & account","Signing out removes the active Firebase session on this device. Saved local profile data is kept unless you edit or clear it."),g3);
        Button done=settingsMenuButton("Done",false); done.setGravity(Gravity.CENTER); LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); p.topMargin=dp(12); box.addView(done,p); done.setOnClickListener(v->dlg.dismiss());
        dlg.setContentView(box); dlg.show();
    }

    private void showSettings(){
        boolean guest=getPreferences(MODE_PRIVATE).getBoolean("guestMode",false);
        final boolean lightUi=isLightUi();
        BottomSheetDialog dlg=new BottomSheetDialog(this);

        ScrollView outer=new ScrollView(this);
        outer.setFillViewport(true);
        outer.setClipToPadding(false);
        outer.setPadding(0,0,0,dp(34));

        LinearLayout box=new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(22),dp(14),dp(22),dp(34));
        box.setBackground(roundBg(lightUi?"#ECEDEF":"#0B1A29",28));
        outer.addView(box,new ScrollView.LayoutParams(ScrollView.LayoutParams.MATCH_PARENT,ScrollView.LayoutParams.WRAP_CONTENT));

        TextView handle=new TextView(this);
        LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(dp(42),dp(5));
        hp.gravity=Gravity.CENTER_HORIZONTAL; hp.bottomMargin=dp(14);
        handle.setLayoutParams(hp);
        handle.setBackground(roundBg(lightUi?"#7D8790":"#526A7E",10));
        box.addView(handle);

        int primary=Color.parseColor(lightUi?"#22252B":"#F4F8FC");
        int secondary=Color.parseColor(lightUi?"#646B74":"#8FA7BA");
        int violet=Color.parseColor(lightUi?"#6F35A8":"#B989FF");
        String rowFill=lightUi?"#E2E4E8":"#10283A";
        String rowStroke=lightUi?"#C3C7CD":"#31546C";

        LinearLayout titleRow=new LinearLayout(this);
        titleRow.setOrientation(LinearLayout.HORIZONTAL); titleRow.setGravity(Gravity.CENTER_VERTICAL);
        TextView title=label("Settings",24,lightUi?"#22252B":"#F4F8FC",true);
        titleRow.addView(title,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1));
        TextView version=label("v9.0",12,lightUi?"#6C727B":"#7893A6",true);
        titleRow.addView(version); box.addView(titleRow);

        LinearLayout account=new LinearLayout(this);
        account.setOrientation(LinearLayout.HORIZONTAL); account.setGravity(Gravity.CENTER_VERTICAL);
        account.setPadding(dp(14),dp(12),dp(14),dp(12));
        account.setBackground(roundStrokeBg(rowFill,rowStroke,16,1));
        TextView avatar=label(guest?"G":"J",18,"#FFFFFF",true);
        avatar.setGravity(Gravity.CENTER); avatar.setBackground(roundBg("#168CF0",50));
        account.addView(avatar,new LinearLayout.LayoutParams(dp(48),dp(48)));
        LinearLayout who=new LinearLayout(this); who.setOrientation(LinearLayout.VERTICAL); who.setPadding(dp(12),0,0,0);
        TextView name=label(guest?"Guest mode":"JobBubble account",16,lightUi?"#22252B":"#F4F8FC",true);
        FirebaseUser accountUser=firebaseAuth.getCurrentUser(); String accountSub=accountUser!=null&&accountUser.getEmail()!=null?accountUser.getEmail():"JobBubble account"; TextView sub=label(guest?"Saved jobs stay on this device":accountSub,12,lightUi?"#646B74":"#8FA7BA",false);
        who.addView(name); who.addView(sub); account.addView(who,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1));
        TextView state=label("●",16,"#2D9A73",true); account.addView(state);
        LinearLayout.LayoutParams ap=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT); ap.topMargin=dp(14); box.addView(account,ap);

        TextView searchSection=label("Search range",16,lightUi?"#25282E":"#DCE8F2",true);
        searchSection.setPadding(0,dp(20),0,dp(3)); box.addView(searchSection);
        TextView searchSub=label("Allow searches far beyond your local area.",13,lightUi?"#646B74":"#8FA7BA",false);
        searchSub.setPadding(0,0,0,dp(10)); box.addView(searchSub);

        LinearLayout extendedRow=new LinearLayout(this);
        extendedRow.setOrientation(LinearLayout.HORIZONTAL); extendedRow.setGravity(Gravity.CENTER_VERTICAL);
        extendedRow.setPadding(dp(14),dp(7),dp(10),dp(7));
        extendedRow.setBackground(roundStrokeBg(rowFill,lightUi?"#BDA9D3":"#6D3FC3",15,1));
        LinearLayout extText=new LinearLayout(this); extText.setOrientation(LinearLayout.VERTICAL);
        TextView extTitle=label("Extended distance",15,lightUi?"#22252B":"#F4F8FC",true);
        TextView extSub=label("Search up to 10,000 miles",12,lightUi?"#646B74":"#A894C4",false);
        extText.addView(extTitle); extText.addView(extSub); extendedRow.addView(extText,new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1));
        Switch extendedToggle=new Switch(this); extendedToggle.setShowText(false); extendedToggle.setChecked(extendedDistance);
        int[][] switchStates=new int[][]{new int[]{android.R.attr.state_checked},new int[]{}};
        extendedToggle.setThumbTintList(new android.content.res.ColorStateList(switchStates,new int[]{Color.WHITE,Color.parseColor(lightUi?"#F7F7F8":"#D7DDE4")}));
        extendedToggle.setTrackTintList(new android.content.res.ColorStateList(switchStates,new int[]{violet,Color.parseColor(lightUi?"#B9BEC5":"#526577")}));
        extendedRow.addView(extendedToggle,new LinearLayout.LayoutParams(dp(58),dp(42)));
        box.addView(extendedRow,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(68)));
        extendedRow.setOnClickListener(v->extendedToggle.setChecked(!extendedToggle.isChecked()));
        TextView extendedNote=label("Off: 1–100 mi  •  On: 1–10,000 mi",12,lightUi?"#727983":"#8F7DBB",false);
        extendedNote.setPadding(dp(4),dp(7),dp(4),0); box.addView(extendedNote);
        extendedToggle.setOnCheckedChangeListener((buttonView,isChecked)->{
            extendedDistance=isChecked;
            getSharedPreferences("settings",MODE_PRIVATE).edit().putBoolean("extendedDistance",isChecked).apply();saveLocalSettings();saveCloudState();
            int newMax=isChecked?10000:100;
            if(!isChecked && maxDistanceMiles>100) maxDistanceMiles=100;
            if(distanceBar!=null){distanceBar.setMax(newMax);distanceBar.setProgress(Math.min(maxDistanceMiles,newMax));}
            if(distanceValue!=null) distanceValue.setText(maxDistanceMiles+" mi");
            applyFilters();
            Toast.makeText(this,isChecked?"Extended distance enabled":"Extended distance disabled",Toast.LENGTH_SHORT).show();
        });

        TextView regionSection=label("Map region",16,lightUi?"#25282E":"#DCE8F2",true);
        regionSection.setPadding(0,dp(20),0,dp(3)); box.addView(regionSection);
        TextView regionSub=label("The normal Google map stays visible, while panning is limited to the selected U.S. region.",13,lightUi?"#646B74":"#8FA7BA",false);
        regionSub.setPadding(0,0,0,dp(10)); box.addView(regionSub);

        RadioGroup regionGroup=new RadioGroup(this); regionGroup.setOrientation(RadioGroup.VERTICAL);
        RadioButton lower48=new RadioButton(this); lower48.setId(View.generateViewId());
        lower48.setText("United States\nLower 48 states"); lower48.setTextColor(primary); lower48.setTextSize(15); lower48.setGravity(Gravity.CENTER_VERTICAL);
        lower48.setPadding(dp(14),dp(7),dp(14),dp(7)); lower48.setButtonTintList(new android.content.res.ColorStateList(new int[][]{new int[]{android.R.attr.state_checked},new int[]{}},new int[]{violet,Color.parseColor(lightUi?"#9AA1A9":"#AAB6C1")}));
        lower48.setBackground(roundStrokeBg(rowFill,rowStroke,15,1));
        RadioButton alaska=new RadioButton(this); alaska.setId(View.generateViewId());
        alaska.setText("Alaska\nAlaska-only map"); alaska.setTextColor(primary); alaska.setTextSize(15); alaska.setGravity(Gravity.CENTER_VERTICAL);
        alaska.setPadding(dp(14),dp(7),dp(14),dp(7)); alaska.setButtonTintList(lower48.getButtonTintList());
        alaska.setBackground(roundStrokeBg(rowFill,rowStroke,15,1));
        RadioButton hawaii=new RadioButton(this); hawaii.setId(View.generateViewId());
        hawaii.setText("Hawaii\nHawaii-only map"); hawaii.setTextColor(primary); hawaii.setTextSize(15); hawaii.setGravity(Gravity.CENTER_VERTICAL);
        hawaii.setPadding(dp(14),dp(7),dp(14),dp(7)); hawaii.setButtonTintList(lower48.getButtonTintList());
        hawaii.setBackground(roundStrokeBg(rowFill,rowStroke,15,1));
        LinearLayout.LayoutParams regionRbp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(64)); regionRbp.bottomMargin=dp(8);
        regionGroup.addView(lower48,regionRbp);
        LinearLayout.LayoutParams regionRbp2=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(64)); regionRbp2.bottomMargin=dp(8);
        regionGroup.addView(alaska,regionRbp2);
        regionGroup.addView(hawaii,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(64)));
        box.addView(regionGroup);

        if("alaska".equals(mapRegion))alaska.setChecked(true);
        else if("hawaii".equals(mapRegion))hawaii.setChecked(true);
        else lower48.setChecked(true);

        regionGroup.setOnCheckedChangeListener((g,id)->{
            String next=id==alaska.getId()?"alaska":id==hawaii.getId()?"hawaii":"lower48";
            if(!next.equals(mapRegion))setMapRegion(next);
        });

        TextView section=label("App appearance",16,lightUi?"#25282E":"#DCE8F2",true);
        section.setPadding(0,dp(20),0,dp(3)); box.addView(section);
        TextView mapSub=label("Choose the JobBubble interface theme. The map itself keeps the normal Google Maps appearance.",13,lightUi?"#646B74":"#8FA7BA",false);
        mapSub.setPadding(0,0,0,dp(10)); box.addView(mapSub);

        RadioGroup group=new RadioGroup(this); group.setOrientation(RadioGroup.VERTICAL);
        RadioButton light=new RadioButton(this); light.setId(View.generateViewId());
        light.setText("Light interface"); light.setTextColor(primary); light.setTextSize(15); light.setGravity(Gravity.CENTER_VERTICAL);
        light.setPadding(dp(14),dp(7),dp(14),dp(7)); light.setButtonTintList(new android.content.res.ColorStateList(new int[][]{new int[]{android.R.attr.state_checked},new int[]{}},new int[]{violet,Color.parseColor(lightUi?"#9AA1A9":"#AAB6C1")}));
        light.setBackground(roundStrokeBg(rowFill,rowStroke,15,1));
        RadioButton dark=new RadioButton(this); dark.setId(View.generateViewId());
        dark.setText("Dark interface"); dark.setTextColor(primary); dark.setTextSize(15); dark.setGravity(Gravity.CENTER_VERTICAL);
        dark.setPadding(dp(14),dp(7),dp(14),dp(7)); dark.setButtonTintList(new android.content.res.ColorStateList(new int[][]{new int[]{android.R.attr.state_checked},new int[]{}},new int[]{violet,Color.parseColor(lightUi?"#9AA1A9":"#AAB6C1")}));
        dark.setBackground(roundStrokeBg(rowFill,rowStroke,15,1));
        LinearLayout.LayoutParams rbp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(64)); rbp.bottomMargin=dp(8);
        group.addView(light,rbp); group.addView(dark,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(64))); box.addView(group);
        if("dark".equals(mapTheme)){
            dark.setChecked(true);
            dark.setBackground(roundStrokeBg(lightUi?"#E8DDF2":"#25113D",lightUi?"#8B58B8":"#8E4BD1",15,1));
        }else{
            light.setChecked(true);
            light.setBackground(roundStrokeBg(lightUi?"#E8DDF2":"#25113D",lightUi?"#8B58B8":"#8E4BD1",15,1));
        }
        group.setOnCheckedChangeListener((g,id)->{
            String next=id==dark.getId()?"dark":"light";
            if(!next.equals(mapTheme)){setMapTheme(next);dlg.dismiss();showSettings();}
        });

        TextView mapNote=label("Powered by Google Maps.",12,lightUi?"#737982":"#7893A6",false);
        mapNote.setPadding(0,dp(9),0,dp(16)); box.addView(mapNote);

        TextView toolsSection=label("Information & Support",16,lightUi?"#25282E":"#DCE8F2",true);
        toolsSection.setPadding(0,dp(4),0,dp(8)); box.addView(toolsSection);
        Button licenses=settingsMenuButton("Licenses & Data Sources",false); box.addView(licenses,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52))); licenses.setOnClickListener(v->{dlg.dismiss();showLicensesAndSources();});
        Button jobSources=settingsMenuButton("Job Sources",false); LinearLayout.LayoutParams jsp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); jsp.topMargin=dp(8); box.addView(jobSources,jsp); jobSources.setOnClickListener(v->{dlg.dismiss();showJobSourcesMenu();});
        Button help=settingsMenuButton("Help & Support",false); LinearLayout.LayoutParams hp2=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); hp2.topMargin=dp(8); box.addView(help,hp2); help.setOnClickListener(v->{dlg.dismiss();showHelpSupport();});

        TextView accountSection=label("Account",16,lightUi?"#25282E":"#DCE8F2",true);
        accountSection.setPadding(0,dp(2),0,dp(8)); box.addView(accountSection);
        Button sign=new Button(this); sign.setText(guest?"Exit guest mode":"Log Out"); sign.setGravity(Gravity.CENTER_VERTICAL); sign.setPadding(dp(18),0,dp(18),0);
        sign.setTextColor(Color.parseColor(lightUi?"#9A374A":"#FF9F9F")); sign.setTextSize(15); sign.setTypeface(Typeface.DEFAULT,Typeface.BOLD); sign.setAllCaps(false);
        sign.setBackground(roundStrokeBg(lightUi?"#F2E4E7":"#281A23",lightUi?"#D7AEB7":"#5B3442",14,1));
        box.addView(sign,new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)));
        sign.setOnClickListener(v->{dlg.dismiss();firebaseAuth.signOut();if(googleSignInClient!=null)googleSignInClient.signOut();getPreferences(MODE_PRIVATE).edit().clear().apply();showWelcome();});

        Button done=new Button(this); done.setText("Done"); done.setAllCaps(false); done.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        done.setTextColor(Color.WHITE); done.setBackground(roundBg(lightUi?"#6F35A8":"#6E2FA4",14));
        LinearLayout.LayoutParams dbp=new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,dp(52)); dbp.topMargin=dp(14); box.addView(done,dbp);
        done.setOnClickListener(v->dlg.dismiss());

        dlg.setContentView(outer);
        dlg.setOnShowListener(x->{
            Window w=dlg.getWindow();
            if(w!=null){w.setDimAmount(.28f);w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);}
            View sheet=dlg.findViewById(com.google.android.material.R.id.design_bottom_sheet);
            if(sheet!=null){
                com.google.android.material.bottomsheet.BottomSheetBehavior<View> behavior=com.google.android.material.bottomsheet.BottomSheetBehavior.from(sheet);
                behavior.setState(com.google.android.material.bottomsheet.BottomSheetBehavior.STATE_EXPANDED);
                behavior.setSkipCollapsed(true);
            }
        });
        dlg.show();
    }

    @Override public void onRequestPermissionsResult(int r,@NonNull String[] p,@NonNull int[] g){super.onRequestPermissionsResult(r,p,g);if(r==LOCATION_REQUEST&&g.length>0&&g[0]==PackageManager.PERMISSION_GRANTED)enableLocation();else{jobs.clear();applyFilters();status.setText("Location permission is required for nearby live jobs");centerOnUser();}}

    private GradientDrawable ovalStrokeBg(String fill,String stroke,int strokeDp){
        GradientDrawable g=new GradientDrawable();
        g.setShape(GradientDrawable.OVAL);
        g.setColor(Color.parseColor(fill));
        g.setStroke(dp(strokeDp),Color.parseColor(stroke));
        return g;
    }

    static class Job{String title,company,category,url,source,description,location;double lat,lon,pay;boolean locationApproximate=false;String locationPrecision="area";Job(String t,String c,double a,double o,double p,String cat,String u){this(t,c,a,o,p,cat,u,inferSource(u),"","");}Job(String t,String c,double a,double o,double p,String cat,String u,String src){this(t,c,a,o,p,cat,u,src,"","");}Job(String t,String c,double a,double o,double p,String cat,String u,String src,String desc,String loc){title=t;company=c;lat=a;lon=o;pay=p;category=cat;url=u;source=src;description=desc;location=loc;}static String inferSource(String u){String x=u==null?"":u.toLowerCase(Locale.US);if(x.contains("usajobs.gov"))return"USAJOBS";if(x.contains("adzuna"))return"Adzuna";return"Adzuna";}static Job from(JSONObject o){JSONObject co=o.optJSONObject("company");double pay=o.optDouble("salary_min",0);String period=o.optString("salary_period","");if(pay>0&&period.equalsIgnoreCase("year"))pay=pay/2080.0;else if(pay>0&&period.equalsIgnoreCase("month"))pay=pay*12.0/2080.0;else if(pay>0&&period.equalsIgnoreCase("week"))pay=pay*52.0/2080.0;String title=o.optString("title","Job");String company=co==null?o.optString("company","Employer"):co.optString("display_name","Employer");String src=o.optString("source",inferSource(o.optString("apply_url","")));String desc=o.optString("description","");String providerCat=o.optString("category","Other");String refined=refinedJobCategory(title,providerCat,desc,company,src);Job j=new Job(title,company,o.optDouble("latitude",0),o.optDouble("longitude",0),pay,refined,o.optString("apply_url",""),src,desc,o.optString("location",""));String precision=o.optString("location_precision","");if(!precision.isEmpty()){j.locationPrecision=precision;j.locationApproximate=o.optBoolean("location_approximate",!"exact".equals(precision));}return j;}}
}
