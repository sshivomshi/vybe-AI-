package com.mnemos.mobile;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.graphics.Color;
import android.net.Uri;
import android.view.View;
import android.webkit.*;
import android.widget.*;

/** Lightweight PC-connected Android client. No AI models run on the phone. */
public final class PcActivity extends Activity {
    private String home = "http://127.0.0.1:8000/";
    private boolean development;
    private WebView web;
    private LinearLayout offline;
    private ProgressBar progress;
    private boolean failed;
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private TextView text(String content, int size) {
        TextView v = new TextView(this); v.setText(content); v.setTextSize(size);
        v.setTextColor(Color.rgb(38,74,61)); v.setPadding(dp(12),dp(8),dp(12),dp(8)); return v;
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        development = (getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE) != 0;
        if (development) home = "http://127.0.0.1:5173/";
        WebView.setWebContentsDebuggingEnabled(development);
        LinearLayout root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(250,251,248));
        LinearLayout bar = new LinearLayout(this); bar.setGravity(android.view.Gravity.CENTER_VERTICAL);
        bar.addView(text(development ? "Mnemos Dev · Live UI" : "Mnemos · AI & data on your PC",12),new LinearLayout.LayoutParams(0,dp(48),1));
        Button help = new Button(this); help.setText("Connect"); help.setTextSize(12);
        help.setOnClickListener(v -> showHelp()); bar.addView(help);
        root.addView(bar);
        progress = new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);
        root.addView(progress,new LinearLayout.LayoutParams(-1,dp(3)));
        FrameLayout body = new FrameLayout(this); root.addView(body,new LinearLayout.LayoutParams(-1,0,1));
        web = new WebView(this); body.addView(web,new FrameLayout.LayoutParams(-1,-1));
        WebSettings settings=web.getSettings(); settings.setJavaScriptEnabled(true);
        if (development) settings.setCacheMode(WebSettings.LOAD_NO_CACHE);
        settings.setDomStorageEnabled(true); settings.setAllowFileAccess(false); settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setUserAgentString(settings.getUserAgentString()+" MnemosAndroid/1.0");
        CookieManager.getInstance().setAcceptThirdPartyCookies(web,false);
        web.setWebChromeClient(new WebChromeClient() {
            @Override public void onProgressChanged(WebView view,int value) { progress.setProgress(value); }
            @Override public boolean onJsConfirm(WebView view,String url,String message,JsResult result) {
                new AlertDialog.Builder(PcActivity.this).setMessage(message)
                    .setPositiveButton("Confirm",(d,w)->result.confirm()).setNegativeButton("Cancel",(d,w)->result.cancel())
                    .setOnCancelListener(d->result.cancel()).show(); return true;
            }
        });
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request) {
                Uri u=request.getUrl();
                return !("http".equals(u.getScheme()) && "127.0.0.1".equals(u.getHost()) && u.getPort()==Uri.parse(home).getPort());
            }
            @Override public void onPageStarted(WebView view,String url,android.graphics.Bitmap icon) { progress.setVisibility(View.VISIBLE); }
            @Override public void onPageFinished(WebView view,String url) { progress.setVisibility(View.GONE); if(!failed) web.setVisibility(View.VISIBLE); }
            @Override public void onReceivedError(WebView view,WebResourceRequest request,WebResourceError error) { if(request.isForMainFrame()) showOffline(); }
            @Override public void onReceivedHttpError(WebView view,WebResourceRequest request,WebResourceResponse response) { if(request.isForMainFrame()) showOffline(); }
        });
        offline = new LinearLayout(this); offline.setOrientation(LinearLayout.VERTICAL); offline.setGravity(android.view.Gravity.CENTER);
        offline.setPadding(dp(20),dp(20),dp(20),dp(20)); offline.setBackgroundColor(Color.rgb(250,251,248));
        offline.addView(text("Connect to your PC",26));
        offline.addView(text("Your assistant runs on your computer. Keep it running and connect this phone with a USB data cable.\n\nEnable USB debugging, approve this PC, then run on the PC:\n\nscripts\\test_android.ps1\n\nChats and memories are stored on the PC. The USB connection must stay active.",16));
        Button retry=new Button(this); retry.setText("Try again"); retry.setOnClickListener(v->load()); offline.addView(retry);
        body.addView(offline,new FrameLayout.LayoutParams(-1,-1));
        if (development) offline.addView(text("Development mode: run scripts/start_android_dev.ps1 on your PC. Vite uses port 5173; the backend uses port 8000.",14));
        setContentView(root); load();
    }
    private void load() { failed=false; offline.setVisibility(View.GONE); web.setVisibility(View.VISIBLE); progress.setVisibility(View.VISIBLE); web.loadUrl(home); }
    private void showOffline() { failed=true; web.setVisibility(View.GONE); progress.setVisibility(View.GONE); offline.setVisibility(View.VISIBLE); }
    private void showHelp() {
        new AlertDialog.Builder(this).setTitle("PC connection")
            .setMessage((development ? "LIVE DEVELOPMENT: Run scripts/start_android_dev.ps1 on your PC. Save React/CSS files to update this app. Java changes need Android Studio Run or Apply Changes.\n\n" : "") + "1. Run the Mnemos server on your PC.\n2. Connect USB and enable USB debugging.\n3. On the PC run scripts\\test_android.ps1.\n4. Tap Reload below.\n\nKeep USB connected. AI and saved data stay on the PC. Reloading clears an unsent draft.")
            .setPositiveButton("Reload",(d,w)->load()).setNegativeButton("Close",null).show();
    }
    @Override public void onBackPressed() { if(!failed && web.canGoBack()) web.goBack(); else super.onBackPressed(); }
    @Override protected void onPause() { web.onPause(); super.onPause(); }
    @Override protected void onResume() { super.onResume(); if(web!=null)web.onResume(); }
    @Override protected void onDestroy() { web.destroy(); super.onDestroy(); }
}
