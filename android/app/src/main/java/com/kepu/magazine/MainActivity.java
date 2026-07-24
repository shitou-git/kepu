package com.kepu.magazine;

import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    private WebView webView;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        WebView.setWebContentsDebuggingEnabled(true);
        
        webView = bridge.getWebView();
        if (webView != null) {
            webView.setWebViewClient(new WebViewClient());
        }
    }

    @Override
    public void onBackPressed() {
        if (webView == null) {
            webView = bridge.getWebView();
        }
        
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
