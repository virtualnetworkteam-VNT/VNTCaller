package com.vnt.caller;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.*;
import android.view.*;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        // Start service
        startForegroundService(new Intent(this, CallService.class));
        TextView status = findViewById(R.id.status);
        status.setText("VNT Caller Active\nAlias: ryan-alias room\nMia: vnt-general room\nWaiting for calls...");
        Switch sw = findViewById(R.id.enableSwitch);
        sw.setChecked(true);
        sw.setOnCheckedChangeListener((b, checked) -> {
            if (checked) startForegroundService(new Intent(this, CallService.class));
            else stopService(new Intent(this, CallService.class));
        });
    }
}
