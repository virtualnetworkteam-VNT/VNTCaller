package com.vnt.caller;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.Looper;
import android.telecom.TelecomManager;
import android.telephony.TelephonyManager;

public class CallReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        String state = intent.getStringExtra(TelephonyManager.EXTRA_STATE);
        String number = intent.getStringExtra(TelephonyManager.EXTRA_INCOMING_NUMBER);
        if (!TelephonyManager.EXTRA_STATE_RINGING.equals(state) || number == null) return;

        int slot = intent.getIntExtra("slot", -1);
        if (slot == -1) slot = intent.getIntExtra("android.telephony.extra.SLOT_INDEX", -1);
        SharedPreferences prefs = ctx.getSharedPreferences("vnt_prefs", Context.MODE_PRIVATE);
        int selectedSlot = prefs.getInt("selected_sim_slot", 1);
        if (slot != -1 && slot != selectedSlot) return;

        String clean = number.replaceAll("[+\\s-]","");
        String room = clean.endsWith("568116899") ? "ryan-alias" : "vnt-general";
        
        // Start AI call service
        Intent si = new Intent(ctx, CallService.class);
        si.putExtra("room", room);
        si.putExtra("number", number);
        ctx.startForegroundService(si);
        
        // Auto-answer after 2 seconds using TelecomManager
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            try {
                TelecomManager tm = (TelecomManager) ctx.getSystemService(Context.TELECOM_SERVICE);
                if (tm != null) tm.acceptRingingCall();
            } catch (Exception e) {
                // Try accessibility service as fallback
                if (CallAnswerService.instance != null) {
                    CallAnswerService.instance.answerCall();
                }
            }
        }, 2000);
    }
}
