package com.vnt.caller;
import android.app.Activity;
import android.content.*;
import android.net.Uri;
import android.os.*;
import android.provider.MediaStore;
import android.telecom.TelecomManager;
import android.view.View;
import android.widget.*;
import java.io.*;

public class MainActivity extends Activity {
    private StringBuilder dialNumber = new StringBuilder();
    private int ringCount = 3;
    private static final int PICK_IMAGE = 1;

    @Override
    protected void onCreate(Bundle s) {
        super.onCreate(s);
        SharedPreferences auth = getSharedPreferences("vnt_auth", MODE_PRIVATE);
        if (!auth.contains("user_name")) {
            startActivity(new Intent(this, LoginActivity.class)); finish(); return;
        }
        setContentView(R.layout.activity_main);

        SharedPreferences prefs = getSharedPreferences("vnt_prefs", MODE_PRIVATE);
        
        // User info
        String userName = auth.getString("user_name","User");
        String userRole = auth.getString("user_role","user");
        ((TextView)findViewById(R.id.tvUser)).setText(userName);
        ((TextView)findViewById(R.id.tvAgentName)).setText(userName);
        ((TextView)findViewById(R.id.tvAgentRole)).setText(userRole.toUpperCase() + " — VNT");

        // Status dot
        updateStatusDot();
        new Handler().postDelayed(this::updateStatusDot, 5000);

        // SIM selection
        RadioGroup rg = findViewById(R.id.rgSim);
        int sim = prefs.getInt("sim_slot", 1);
        ((RadioButton)rg.getChildAt(sim)).setChecked(true);
        rg.setOnCheckedChangeListener((g, id) -> {
            int slot = id==R.id.rbSim1 ? 0 : id==R.id.rbSim2 ? 1 : 2;
            prefs.edit().putInt("sim_slot", slot).apply();
        });

        // Ring count
        ringCount = prefs.getInt("ring_count", 3);
        ((TextView)findViewById(R.id.tvRings)).setText(String.valueOf(ringCount));
        findViewById(R.id.btnRingPlus).setOnClickListener(v -> {
            if (ringCount < 9) { ringCount++;
                ((TextView)findViewById(R.id.tvRings)).setText(String.valueOf(ringCount));
                prefs.edit().putInt("ring_count", ringCount).apply(); }
        });
        findViewById(R.id.btnRingMinus).setOnClickListener(v -> {
            if (ringCount > 1) { ringCount--;
                ((TextView)findViewById(R.id.tvRings)).setText(String.valueOf(ringCount));
                prefs.edit().putInt("ring_count", ringCount).apply(); }
        });

        // AI switch
        Switch sw = findViewById(R.id.swAI);
        sw.setChecked(prefs.getBoolean("ai_enabled", true));
        sw.setOnCheckedChangeListener((b, checked) -> prefs.edit().putBoolean("ai_enabled", checked).apply());

        // Upload agent pic
        findViewById(R.id.tvUploadPic).setOnClickListener(v -> {
            Intent i = new Intent(Intent.ACTION_PICK, MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
            startActivityForResult(i, PICK_IMAGE);
        });

        // Load saved agent pic
        String picPath = prefs.getString("agent_pic", null);
        if (picPath != null) ((ImageView)findViewById(R.id.ivAgent)).setImageURI(Uri.parse(picPath));

        // Dialpad
        int[] keys = {R.id.k1,R.id.k2,R.id.k3,R.id.k4,R.id.k5,R.id.k6,R.id.k7,R.id.k8,R.id.k9,R.id.kStar,R.id.k0,R.id.kHash};
        String[] vals = {"1","2","3","4","5","6","7","8","9","*","0","#"};
        for (int i=0;i<keys.length;i++) {
            final String v = vals[i];
            findViewById(keys[i]).setOnClickListener(btn -> {
                dialNumber.append(v);
                ((TextView)findViewById(R.id.tvDialNumber)).setText(dialNumber.toString());
            });
        }
        findViewById(R.id.btnBackspace).setOnClickListener(v -> {
            if (dialNumber.length()>0) dialNumber.deleteCharAt(dialNumber.length()-1);
            ((TextView)findViewById(R.id.tvDialNumber)).setText(dialNumber.toString());
        });
        findViewById(R.id.btnClear).setOnClickListener(v -> {
            dialNumber.setLength(0);
            ((TextView)findViewById(R.id.tvDialNumber)).setText("");
        });

        // Call button - select SIM
        findViewById(R.id.btnCall).setOnClickListener(v -> {
            String num = dialNumber.toString().trim();
            if (num.isEmpty()) return;
            // Show SIM selection dialog
            String[] sims = {"SIM 1 (Physical)", "SIM 2 (eSIM)"};
            new android.app.AlertDialog.Builder(this)
                .setTitle("Select SIM to call")
                .setItems(sims, (d, which) -> makeCall(num, which))
                .show();
        });

        // Logout
        findViewById(R.id.tvLogout).setOnClickListener(v -> {
            getSharedPreferences("vnt_auth", MODE_PRIVATE).edit().clear().apply();
            startActivity(new Intent(this, LoginActivity.class)); finish();
        });

        // Start service
        startForegroundService(new Intent(this, CallService.class));
        PhoneAccountSetup.register(this);
    }

    private void makeCall(String number, int simSlot) {
        try {
            Uri uri = Uri.fromParts("tel", number, null);
            Intent intent = new Intent(Intent.ACTION_CALL, uri);
            // Try to select SIM slot
            intent.putExtra("com.android.phone.extra.slot", simSlot);
            intent.putExtra("slot", simSlot);
            startActivity(intent);
        } catch (Exception e) {
            Toast.makeText(this, "Call failed: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        if (req==PICK_IMAGE && res==RESULT_OK && data!=null) {
            Uri uri = data.getData();
            ((ImageView)findViewById(R.id.ivAgent)).setImageURI(uri);
            getSharedPreferences("vnt_prefs", MODE_PRIVATE).edit()
                .putString("agent_pic", uri.toString()).apply();
        }
    }

    private void updateStatusDot() {
        View dot = findViewById(R.id.statusDot);
        new Thread(() -> {
            int res;
            try {
                java.net.Socket s = new java.net.Socket();
                s.connect(new java.net.InetSocketAddress("192.168.10.96", 9999), 2000);
                s.close(); res = R.drawable.dot_green;
            } catch (Exception e) {
                try { java.net.InetAddress.getByName("8.8.8.8"); res = R.drawable.dot_orange; }
                catch (Exception e2) { res = R.drawable.dot_red; }
            }
            final int r = res;
            runOnUiThread(() -> { if(dot!=null) dot.setBackgroundResource(r); });
        }).start();
    }
}
