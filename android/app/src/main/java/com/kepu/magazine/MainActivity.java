package com.kepu.magazine;

import android.os.Bundle;
import android.webkit.WebView;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // 启用 WebView 调试（仅在开发时有用）
        WebView.setWebContentsDebuggingEnabled(true);
    }

    @Override
    public void onBackPressed() {
        // Capacitor BridgeActivity 默认处理：
        // WebView 可后退时后退，否则退出 App
        // 保持默认行为即可
        super.onBackPressed();
    }
}
