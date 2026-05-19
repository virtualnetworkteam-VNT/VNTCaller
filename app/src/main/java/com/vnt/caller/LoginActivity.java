package com.vnt.caller;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.widget.*;

public class LoginActivity extends Activity {
    private static final String[][] USERS = {
        {"kraheelw@vntworld.com", "App159earance.VnT", "Ryan", "admin"},
        {"admin", "116899", "Admin", "admin"},
        {"ryan", "116899", "Ryan", "admin"}
    };

    @Override
    protected void onCreate(Bundle s) {
        super.onCreate(s);
        // Auto-login if saved
        SharedPreferences p = getSharedPreferences("vnt_auth", MODE_PRIVATE);
        if (p.contains("user_name")) {
            startActivity(new Intent(this, MainActivity.class));
            finish(); return;
        }
        setContentView(R.layout.activity_login);
        updateStatusDot();

        EditText etPass = findViewById(R.id.etPass);
        TextView tvShow = findViewById(R.id.tvShowPass);
        tvShow.setOnClickListener(v -> {
            if (etPass.getInputType() == InputType.TYPE_CLASS_TEXT) {
                etPass.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
                tvShow.setText("👁");
            } else {
                etPass.setInputType(InputType.TYPE_CLASS_TEXT);
                tvShow.setText("🙈");
            }
            etPass.setSelection(etPass.getText().length());
        });

        findViewById(R.id.btnLogin).setOnClickListener(v -> {
            String user = ((EditText)findViewById(R.id.etUser)).getText().toString().trim().toLowerCase();
            String pass = ((EditText)findViewById(R.id.etPass)).getText().toString();
            TextView err = findViewById(R.id.tvError);
            for (String[] u : USERS) {
                if ((u[0].equals(user) || u[2].toLowerCase().equals(user)) && u[1].equals(pass)) {
                    p.edit().putString("user_name", u[2]).putString("user_role", u[3]).apply();
                    startActivity(new Intent(this, MainActivity.class));
                    finish(); return;
                }
            }
            err.setText("Invalid credentials");
            err.setVisibility(View.VISIBLE);
        });
    }

    private void updateStatusDot() {
        View dot = findViewById(R.id.statusDot);
        if (dot == null) return;
        new Thread(() -> {
            try {
                java.net.Socket s = new java.net.Socket();
                s.connect(new java.net.InetSocketAddress("192.168.10.96", 9999), 2000);
                s.close();
                runOnUiThread(() -> dot.setBackgroundResource(R.drawable.dot_green));
            } catch (Exception e) {
                try {
                    java.net.InetAddress.getByName("8.8.8.8");
                    runOnUiThread(() -> dot.setBackgroundResource(R.drawable.dot_orange));
                } catch (Exception e2) {
                    runOnUiThread(() -> dot.setBackgroundResource(R.drawable.dot_red));
                }
            }
        }).start();
    }
}
