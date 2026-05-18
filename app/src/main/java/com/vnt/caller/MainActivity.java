package com.vnt.caller;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.*;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        SharedPreferences prefs = getSharedPreferences("vnt_prefs", MODE_PRIVATE);
        
        // SIM slot selector
        RadioGroup simGroup = findViewById(R.id.simGroup);
        int savedSlot = prefs.getInt("selected_sim_slot", 1);
        ((RadioButton)simGroup.getChildAt(savedSlot)).setChecked(true);
        
        simGroup.setOnCheckedChangeListener((group, checkedId) -> {
            int slot = checkedId == R.id.sim1 ? 0 : 1;
            prefs.edit().putInt("selected_sim_slot", slot).apply();
            updateStatus();
        });
        
        Switch sw = findViewById(R.id.enableSwitch);
        sw.setChecked(true);
        sw.setOnCheckedChangeListener((b, checked) -> {
            if (checked) startForegroundService(new Intent(this, CallService.class));
            else stopService(new Intent(this, CallService.class));
        });
        
        startForegroundService(new Intent(this, CallService.class));
        updateStatus();
    }
    
    private void updateStatus() {
        SharedPreferences prefs = getSharedPreferences("vnt_prefs", MODE_PRIVATE);
        int slot = prefs.getInt("selected_sim_slot", 1);
        TextView status = findViewById(R.id.status);
        status.setText("VNT Caller Active\nMonitoring: SIM " + (slot+1) + " (" + (slot==0?"Physical SIM":"eSIM") + ")\n\nRyan (+966568116899) -> Alias\nOthers -> Mia");
    }
}
